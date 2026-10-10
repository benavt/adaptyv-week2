"""Paired TNFA pose agreement on read-only native Boltz2 predictions."""
from pathlib import Path
import argparse, copy, gzip, datetime, hashlib, itertools, json, os, re, runpy, subprocess, sys, tempfile, time
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
from canonical_tm import calculate as canonical_whole_tm
from Bio import Align
from Bio.PDB.Chain import Chain
from Bio.PDB.Model import Model
from Bio.SeqUtils import seq1

P = Path(__file__).resolve().parent
RUN = P.parents[1]
BASE = RUN.parent
SETTINGS = json.loads((P / 'settings.json').read_text())
PAIRS = json.loads(gzip.decompress((P / 'pairs.json.gz').read_bytes()))
IPSAE = runpy.run_path(str(P / 'pinned-ipsae.py'))

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def initialize(library):
    global DQ
    sys.path.insert(0, str(library/"DockQ"))
    sys.path.insert(0, str(library))
    from DockQ import DockQ
    DQ = DockQ

def proper_fit(x, y):
    xc, yc = x.mean(0), y.mean(0)
    u, _, v = np.linalg.svd((x-xc).T @ (y-yc))
    d = np.eye(3); d[2,2] = np.sign(np.linalg.det(u @ v))
    rot = u @ d @ v; trans = yc-xc @ rot
    rms = float(np.sqrt(np.mean(np.sum((x @ rot + trans-y)**2, axis=1))))
    return rot, trans, rms

def residue_mapping(hseq, mseq):
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'; aligner.match_score = 5; aligner.mismatch_score = 0
    aligner.open_gap_score = -4; aligner.extend_gap_score = -0.5
    aln = aligner.align(hseq, mseq)[0]
    hi, mi = [], []; hn, mn = {}, {}
    for col, (h, m) in enumerate(aln.indices.T, 1):
        if h >= 0: hn[int(h)] = col
        if m >= 0: mn[int(m)] = col
        if h >= 0 and m >= 0: hi.append(int(h)); mi.append(int(m))
    assert len(hn)==len(hseq) and len(mn)==len(mseq)
    return np.array(hi), np.array(mi), hn, mn, str(aln)

def ca(chain):
    return np.asarray([r['CA'].coord for r in chain], dtype=float)

def sequence(chain):
    return ''.join(seq1(r.resname) for r in chain)

def collapse(model, order, numbering):
    receptor = Chain('R'); receptor.is_het = False
    for slot, ch in enumerate(order):
        for index, residue in enumerate(model[ch]):
            r = copy.deepcopy(residue, {id(residue.parent): None}); r.detach_parent()
            r.id = (' ', slot*1000 + numbering[index], ' '); receptor.add(r)
    receptor.sequence = sequence(receptor)
    binder = copy.deepcopy(model['D'], {id(model['D'].parent): None}); binder.detach_parent(); binder.id='D'
    binder.is_het = False; binder.sequence = sequence(binder)
    container = Model(str(model.id)+"_collapsed")
    container.add(receptor); container.add(binder)
    assert receptor.get_full_id()!=binder.get_full_id()
    return receptor, binder

def clean_dockq(info):
    if info is None: return None
    return {k: float(info[k]) if isinstance(info[k], (float, np.floating)) else int(info[k])
            for k in ['DockQ','iRMSD','LRMSD','fnat','fnonnat','nat_correct','nat_total','nonnat_count','model_total'] if k in info}

def species_observation(pair, sp, model):
    e = pair[sp]; native = e['native_structure']; path = BASE/e['source_run']/native['relative_path']
    src = {kind:{**v, 'source_run':e['source_run']} for kind,v in e['artifact_sources'].items()}
    old = REUSED.get(pair['candidate_id'], {}).get(sp)
    if old:
        assert old['native_structure']['sha256'] == native['sha256']
        assert all(old['artifact_sources'][k]['sha256']==v['sha256'] for k,v in src.items())
        out = copy.deepcopy(old)
    else:
        for v in src.values(): assert sha(BASE/e['source_run']/v['relative_path'])==v['sha256']
        with np.load(BASE/e['source_run']/src['pae']['relative_path'], allow_pickle=False) as n:
            protomer = IPSAE['binder_pair_scores'](n['pae'],len(e['target_sequence']),len(pair['sequence']))
        conf = json.loads((BASE/e['source_run']/src['confidence']['relative_path']).read_text())
        with np.load(BASE/e['source_run']/src['plddt']['relative_path'], allow_pickle=False) as n:
            a=np.asarray(n['plddt']); assert len(a)==3*len(e['target_sequence'])+len(pair['sequence'])
            bp=float(a[-len(pair['sequence']):].mean())*(100 if a.max()<=1 else 1)
        iptm=conf.get('pair_chains_iptm',{})
        out={'task_id':e['task_id'],'candidate_id':pair['candidate_id'],'species':sp,
             'ipsae':max(protomer.values()),'ipsae_by_protomer':protomer,
             'best_protomer':max(protomer,key=lambda k:(protomer[k],-ord(k))),
             'confidence_score':conf.get('confidence_score'),'ptm':conf.get('ptm'),'complex_iptm':conf.get('iptm'),
             'best_binder_pair_iptm':max([float(iptm[str(i)]['3']) for i in range(3)]+[float(iptm['3'][str(i)]) for i in range(3)]) if iptm else None,
             'binder_plddt_0_to_100':bp}
    out.update(source_run=e['source_run'],source_index=e['index_path'],source_index_sha256=e['index_sha256'],
               native_structure={**native,'source_run':e['source_run']},artifact_sources=src)
    return out

def score_pair(pair):
    started=time.monotonic(); models={}; paths={}
    for sp in ['human','mouse']:
        e=pair[sp]; path=BASE/e['source_run']/e['native_structure']['relative_path']
        assert sha(path)==e['native_structure']['sha256'], str(path)
        model=DQ.load_PDB(str(path)); assert set(c.id for c in model)==set('ABCD')
        assert all(sequence(model[ch])==e['target_sequence'] for ch in 'ABC')
        assert sequence(model['D'])==pair['sequence']
        assert [r.id[1] for r in model['D']]==list(range(1,len(pair['sequence'])+1))
        models[sp]=model; paths[sp]=path
    h,m=models['human'],models['mouse']; n=len(pair['sequence'])
    hi,mi,hn,mn,alignment=residue_mapping(pair['human']['target_sequence'],pair['mouse']['target_sequence'])
    y=np.vstack([ca(h[ch])[hi] for ch in 'ABC']); hb=ca(h['D']); mb=ca(m['D'])
    d0=max(.5,1.24*(n-15)**(1/3)-1.8) if n>15 else .5
    options=[]
    for order in itertools.permutations('ABC'):
        x=np.vstack([ca(m[ch])[mi] for ch in order]); rot,trans,rms=proper_fit(x,y)
        dist=np.linalg.norm(mb@rot+trans-hb,axis=1)
        options.append({'human_to_mouse_copy':dict(zip('ABC',order)),'target_ca_rmsd_angstrom':rms,
                        'binder_pose_tm':float(np.mean(1/(1+(dist/d0)**2))),
                        'binder_pose_ca_rmsd_angstrom':float(np.sqrt(np.mean(dist**2))),
                        'rotation_mouse_to_human':rot.tolist(),'translation_mouse_to_human':trans.tolist()})
    minimum=min(o['target_ca_rmsd_angstrom'] for o in options)
    eligible=[o for o in options if o['target_ca_rmsd_angstrom']<=minimum+.1]
    chosen=min(eligible,key=lambda o:(-o['binder_pose_tm'],o['target_ca_rmsd_angstrom'],''.join(o['human_to_mouse_copy'].values())))
    hc=collapse(h,'ABC',hn); mc=collapse(m,''.join(chosen['human_to_mouse_copy'].values()),mn)
    dh=clean_dockq(DQ.run_on_chains(mc,hc,no_align=True,small_molecule=False)); dm=clean_dockq(DQ.run_on_chains(hc,mc,no_align=True,small_molecule=False))
    dockq=(dh['DockQ']+dm['DockQ'])/2 if dh is not None and dm is not None else None
    scores=[0.0,0.0];rms=None
    proc=type("CanonicalPending",(),{"stdout":""})()
    out={k:pair[k] for k in ['candidate_id','cohort','sequence','sequence_sha256']}
    for sp in ['human','mouse']: out[sp]=species_observation(pair,sp,models[sp])
    out['mean_ipsae']=(out['human']['ipsae']+out['mouse']['ipsae'])/2
    out['pose']={'binder_pose_tm_target_aligned':chosen['binder_pose_tm'],'binder_tm_normalization_length':n,'binder_tm_d0_angstrom':d0,
                 'binder_pose_ca_rmsd_angstrom':chosen['binder_pose_ca_rmsd_angstrom'],
                 'whole_complex_tm_human_normalized':scores[1],'whole_complex_tm_mouse_normalized':scores[0],
                 'whole_complex_usalign_rmsd_angstrom':float(rms.group(1)) if rms else None,
                 'dockq_symmetric':dockq,'dockq_human_reference':dh,'dockq_mouse_reference':dm,
                 'dockq_missing_reason':None if dockq is not None else 'At least one species has no binder-trimer native contacts within 5 A.',
                 'chosen_copy_mapping':chosen,'copy_fit_options':options,'homolog_alignment':alignment,
                 'target_matched_ca_per_protomer':len(hi),'human_construct_to_common_number':hn,'mouse_construct_to_common_number':mn,
                 'usalign_stdout':proc.stdout,'elapsed_seconds':time.monotonic()-started}
    out['ipsae_times_binder_pose_tm']=out['mean_ipsae']*chosen['binder_pose_tm']
    correction=canonical_whole_tm(out,paths['human'],paths['mouse'],SETTINGS['usalign'])
    for key in ['whole_complex_tm_human_normalized','whole_complex_tm_mouse_normalized','whole_complex_usalign_rmsd_angstrom','usalign_stdout','whole_complex_usalign_aligned_length','canonical_adapter_records']:
        out['pose'][key]=correction[key]
    out['pose']['whole_complex_method']=correction['method']
    out['ipsae_times_whole_complex_tm']=out['mean_ipsae']*correction['whole_complex_tm_human_normalized']
    assert all(0<=out['pose'][k]<=1 for k in ['binder_pose_tm_target_aligned','whole_complex_tm_human_normalized'])
    return out

def main():
    global REUSED
    p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--workers',type=int,default=8)
    p.add_argument('--pilot',action='store_true');a=p.parse_args()
    manifest=json.loads((RUN/'run.json').read_text())
    for name,h in manifest['files_sha256'].items(): assert sha(RUN/'01_staging'/name)==h
    reuse=SETTINGS['reuse_ipsae'];rp=P/'reuse-ipsae.jsonl';assert sha(rp)==reuse['sha256']
    REUSED={row['candidate_id']:row for row in map(json.loads,rp.read_text().splitlines())}
    for (r,index),h in {(e['source_run'],e['index_path']):e['index_sha256'] for pair in PAIRS for e in [pair['human'],pair['mouse']]}.items():
        assert sha(BASE/r/index)==h
    initialize(a.library)
    out=RUN/'04_analysis'/('2026-10-10_pose-pilot_003' if a.pilot else '2026-10-10_completed-pose-metrics_003');out.mkdir(exist_ok=False,parents=True)
    pairs=PAIRS
    resumed=[]
    if not a.pilot:
        resume=SETTINGS['execution_resume']; source=BASE/resume['source_run']/resume['path']
        assert sha(source)==resume['sha256']
        resumed=[json.loads(line) for line in source.read_text().splitlines()]
        expected={pair['candidate_id']:pair for pair in PAIRS}; seen=set()
        for row in resumed:
            cid=row['candidate_id']; assert cid in expected and cid not in seen; seen.add(cid)
            assert row['sequence_sha256']==expected[cid]['sequence_sha256']
            for sp in ['human','mouse']:
                e=expected[cid][sp]; assert row[sp]['native_structure']['sha256']==e['native_structure']['sha256']
                assert all(row[sp]['artifact_sources'][k]['sha256']==v['sha256'] for k,v in e['artifact_sources'].items())
            assert row['mean_ipsae']==(row['human']['ipsae']+row['mouse']['ipsae'])/2
            assert row['ipsae_times_binder_pose_tm']==row['mean_ipsae']*row['pose']['binder_pose_tm_target_aligned']
            row['execution_source']={**resume,'line':len(seen)}
        pairs=[pair for pair in PAIRS if pair['candidate_id'] not in seen]
    if a.pilot:
        cohorts=sorted(SETTINGS['available_pairs']);pairs=[]
        for cohort in cohorts:
            choices=[r for r in PAIRS if r['cohort']==cohort]
            choices.sort(key=lambda r:-(REUSED.get(r['candidate_id'],{}).get('human',{}).get('ipsae',0)+REUSED.get(r['candidate_id'],{}).get('mouse',{}).get('ipsae',0)))
            pairs.extend([choices[0],choices[len(choices)//2],choices[-1]])
    versions={}
    import importlib.metadata
    for name in ['numpy','scipy','biopython']:
        versions[name]=importlib.metadata.version(name)
    versions['DockQ']='2.1.4 source snapshot, pure Python operations fallback'
    versions['parallelbar']='2.5 source snapshot'
    runtime={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'execution_resume':SETTINGS.get('execution_resume'),'scientific_method_unchanged_from':'2026-10-09_v6','workers':a.workers,'python':sys.executable,'versions':versions,
             'usalign_path':SETTINGS['usalign'],'usalign_sha256':sha(SETTINGS['usalign']),
             'usalign_version':subprocess.run([SETTINGS['usalign'],'-v'],capture_output=True,text=True).stdout,
             'score_script_sha256':sha(Path(__file__)),'pairs_sha256':sha(P/'pairs.json.gz'),'settings_sha256':sha(P/'settings.json'),
             'library_hashes':{str(f.relative_to(a.library)):sha(f) for f in a.library.rglob('*') if f.is_file() and f.suffix in ['.py','.so']}}
    (out/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    count=len(resumed)
    with (out/'metrics.jsonl').open('x') as stream,ProcessPoolExecutor(max_workers=a.workers) as pool:
        for row in resumed: stream.write(json.dumps(row,allow_nan=False)+'\n')
        stream.flush()
        futures=[pool.submit(score_pair,pair) for pair in pairs]
        for f in as_completed(futures):
            row=f.result();row['execution_source']={'source_run':RUN.name,'score_script_sha256':sha(Path(__file__))};stream.write(json.dumps(row,allow_nan=False)+'\n');count+=1
            if count%100==0 or a.pilot:stream.flush();print('Completed paired pose scores',count,'/',len(pairs)+len(resumed),row['candidate_id'],round(row['pose']['elapsed_seconds'],3),flush=True)
    assert count==len(pairs)+len(resumed)
    completion={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'validated','pair_count':count,
                'cohort_counts':SETTINGS['available_pairs'] if not a.pilot else {c:3 for c in SETTINGS['available_pairs']},
                'metrics_sha256':sha(out/'metrics.jsonl'),'runtime_sha256':sha(out/'runtime.json'),'source_pairs_sha256':sha(P/'pairs.json.gz')}
    (out/'completion.json').write_text(json.dumps(completion,indent=2)+'\n');print(json.dumps(completion),flush=True)
if __name__=='__main__': main()
