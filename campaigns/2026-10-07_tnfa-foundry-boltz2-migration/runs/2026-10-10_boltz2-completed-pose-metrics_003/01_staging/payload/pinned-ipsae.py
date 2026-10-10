#!/usr/bin/env python3
"""Full-cohort paired Boltz2 ipSAE ranking; native coordinates are never modified."""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
VERSION='2026-10-09_v2'
EXPECTED={'original-human':8552,'original-mouse':8688,'revised-human':7672,'revised-mouse':7576}
COHORTS=('original-human','original-mouse','revised-human','revised-mouse')

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def asymmetric_ipsae(pae,cutoff=10.0):
 """Dunbrack v4 residue-specific d0, vectorized without changing the formula."""
 pae=np.asarray(pae,dtype=np.float64);mask=pae<cutoff;n=mask.sum(axis=1)
 d0=np.maximum(1.0,1.24*np.cbrt(np.maximum(26,n)-15)-1.8)
 transformed=1.0/(1.0+(pae/d0[:,None])**2)
 means=np.divide((transformed*mask).sum(axis=1),n,out=np.zeros(len(n)),where=n>0)
 return float(means.max(initial=0.0))

def binder_pair_scores(pae,target_length,binder_length):
 assert pae.shape==(3*target_length+binder_length,)*2 and np.isfinite(pae).all()
 b=np.arange(3*target_length,3*target_length+binder_length);scores={}
 for i,ch in enumerate('ABC'):
  t=np.arange(i*target_length,(i+1)*target_length)
  scores[ch]=max(asymmetric_ipsae(pae[np.ix_(t,b)]),asymmetric_ipsae(pae[np.ix_(b,t)]))
 return scores

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);p.add_argument('--traces',type=Path);args=p.parse_args()
 base=args.project/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs';tasks={};cohorts=defaultdict(dict);records={};source_indices={}
 for r in sorted(base.iterdir()):
  manifest=r/'01_staging/payload/tasks.json'
  if not manifest.is_file() or 'boltz2' not in r.name:continue
  for t in json.loads(manifest.read_text()):
   if t['task_id'] in tasks:
    assert tasks[t['task_id']]['binder_sequence_sha256']==t['binder_sequence_sha256']
   tasks[t['task_id']]=t
   cohort=t['source_cohort'];cohort=('revised-'+cohort) if cohort in ('human','mouse') else cohort
   if cohort in COHORTS:cohorts[cohort][t['candidate_id']]=t['binder_sequence_sha256']
  for f in sorted(r.glob('03_filtering/**/result-index.json')):
   source_indices[str(f)]=sha(f)
   for row in json.loads(f.read_text())['predictions']:
    tid=row['task_id'];entry={'run':r,'row':row,'index':f}
    if tid in records:
     assert records[tid]['row']['files_sha256']==row['files_sha256'],'Conflicting predictions: '+tid
    else:records[tid]=entry
 actual={c:len(cohorts[c]) for c in COHORTS}
 if actual!=EXPECTED:raise SystemExit('Full source cohort manifests required: '+json.dumps(actual))
 coverage={c:{'expected':len(v),'complete_pairs':sum(all(tid+'__'+s in records for s in ('human','mouse')) for tid in v)} for c,v in cohorts.items()}
 if any(v['complete_pairs']!=v['expected'] for v in coverage.values()):raise SystemExit('Full-cohort ranking refused: '+json.dumps(coverage))
 trace_dir=args.traces or args.project/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001'
 completion=trace_dir/'completion.json';trace_index=trace_dir/'trace-index.json'
 if not completion.is_file() or not trace_index.is_file():raise SystemExit('Complete candidate trace verification required before ranking')
 trace_receipt=json.loads(completion.read_text())
 assert trace_receipt['status']=='validated' and sha(trace_index)==trace_receipt['trace_index_sha256'],'Candidate trace verification failed or changed'
 traces={v['candidate_id']:v for v in json.loads(trace_index.read_text())}
 expected_candidates={candidate:sequence_hash for cohort in cohorts.values() for candidate,sequence_hash in cohort.items()}
 assert set(traces)==set(expected_candidates),'Candidate trace coverage differs'
 for candidate,h in expected_candidates.items():
  t=traces[candidate];assert t['status']=='verified' and t['sequence_sha256']==h
  assert sha(trace_dir/t['trace_path'])==t['trace_sha256'],'Candidate trace artifact changed: '+candidate
 observations={};missing_local=[]
 for tid,entry in records.items():
  t=tasks[tid];files=entry['row']['files_sha256'];r=entry['run'];selected={}
  for kind,prefix in [('pae','pae_'),('confidence','confidence_'),('plddt','plddt_')]:
   names=[n for n in files if Path(n).name.startswith(prefix)];assert len(names)==1
   n=names[0];path=r/n
   if not path.is_file():missing_local.append(str(path));continue
   assert sha(path)==files[n],'Hash differs: '+str(path)
   selected[kind]={'path':path,'sha256':files[n]}
  structures=[n for n in files if Path(n).suffix=='.cif'];assert len(structures)==1
  structure=r/structures[0]
  if not structure.is_file():missing_local.append(str(structure));continue
  assert sha(structure)==files[structures[0]],'Native structure hash differs: '+str(structure)
  if len(selected)!=3:continue
  with np.load(selected['pae']['path'],allow_pickle=False) as x:pair=binder_pair_scores(x['pae'],len(t['target_sequence']),len(t['binder_sequence']))
  c=json.loads(selected['confidence']['path'].read_text())
  with np.load(selected['plddt']['path'],allow_pickle=False) as x:values=np.asarray(x['plddt']);assert len(values)==3*len(t['target_sequence'])+len(t['binder_sequence']);binder=float(values[-len(t['binder_sequence']):].mean());binder*=100 if values.max()<=1 else 1
  iptm=c.get('pair_chains_iptm',{});bestiptm=max([float(iptm[str(i)]['3']) for i in range(3)]+[float(iptm['3'][str(i)]) for i in range(3)]) if iptm else None
  observations[tid]={'task_id':tid,'candidate_id':t['candidate_id'],'species':t['target_species'],'ipsae':max(pair.values()),'ipsae_by_protomer':pair,'best_protomer':max(pair,key=lambda k:(pair[k],-ord(k))),'confidence_score':c.get('confidence_score'),'ptm':c.get('ptm'),'complex_iptm':c.get('iptm'),'best_binder_pair_iptm':bestiptm,'binder_plddt_0_to_100':binder,'run_id':r.name,'source_index':str(entry['index']),'source_index_sha256':source_indices[str(entry['index'])],'artifact_sources':{k:{'path':str(v['path']),'sha256':v['sha256']} for k,v in selected.items()},'native_structure':{'path':str(structure),'sha256':files[structures[0]]}}
 if missing_local:raise SystemExit('Score sidecars not collected: '+str(len(missing_local))+' files; outputs not ranked')
 args.output.mkdir(parents=True,exist_ok=False)
 selected=[];ranked=[]
 for cohort in COHORTS:
  rows=[]
  for candidate,sequence_hash in cohorts[cohort].items():
   h=observations[candidate+'__human'];m=observations[candidate+'__mouse'];task=tasks[candidate+'__human']
   rows.append({'cohort':cohort,'candidate_id':candidate,'sequence':task['binder_sequence'],'sequence_sha256':sequence_hash,'mean_ipsae':(h['ipsae']+m['ipsae'])/2,'human_ipsae':h['ipsae'],'mouse_ipsae':m['ipsae'],'human':h,'mouse':m})
  rows.sort(key=lambda v:(-v['mean_ipsae'],v['candidate_id']));keep=math.ceil(len(rows)*.01)
  for rank,row in enumerate(rows,1):row.update(rank=rank,cohort_size=len(rows),selected=rank<=keep)
  ranked.extend(rows);selected.extend(rows[:keep])
 (args.output/'ranked.json').write_text(json.dumps(ranked,indent=2)+'\n');(args.output/'selected.json').write_text(json.dumps(selected,indent=2)+'\n')
 columns=['cohort','rank','candidate_id','sequence','sequence_sha256','mean_ipsae','human_ipsae','mouse_ipsae','cohort_size','selected']
 with (args.output/'ranked.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(ranked)
 method={'version':VERSION,'formula':'symmetric residue-specific-d0 ipSAE, maximum D vs A/B/C; mean of human/mouse','implementation':'vectorized DunbrackLab/IPSAE v4 formula','upstream_commit':'6174cf9e71cb1bd660cc805856a18c4871a6dec3','pae_cutoff_angstrom':10,'contact_distance_cutoff_angstrom':15,'distance_scope':'Distance cutoff applies to contact diagnostics in upstream IPSAE, not the PAE-only ipSAE formula. No distance mask is added to ipSAE.','selection':'ceil(1% of full unique sequences per cohort); descending full-precision mean; candidate_id ascending resolves ties','coverage':coverage,'candidate_traces':{'completion':str(completion),'completion_sha256':sha(completion),'trace_index':str(trace_index),'trace_index_sha256':sha(trace_index)},'script_sha256':sha(Path(__file__)),'predictions_are_not_binding_evidence':True}
 (args.output/'ranking-method.json').write_text(json.dumps(method,indent=2)+'\n');print(json.dumps({'selected':len(selected),'coverage':coverage}))
if __name__=='__main__':main()
