from pathlib import Path
import datetime,hashlib,json,runpy,subprocess
import numpy as np
ROOT=Path.cwd();BASE=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs';RUN=BASE/'2026-10-09_boltz2-pose-conservation_007';RANK=RUN/'04_analysis/2026-10-09_local-pose-ranking_001'
rows=json.loads((RANK/'selected-before-collection.json').read_text());ip=runpy.run_path(str(ROOT/'scripts/tnfa_boltz2_rank.py'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
copies=json.loads((RANK/'selected-native-file-plan.json').read_text());manifest=json.loads((RUN/'04_analysis/2026-10-09_selected-pose-native-copies_001/manifest.json').read_text());assert manifest['status']=='all160_native_and_copy_hashes_verified'
assert {(v['source_run'],v['relative_path'],v['sha256'],v['copy_relative_path']) for v in manifest['files']}=={(v['source_run'],v['relative_path'],v['sha256'],v['copy_relative_path']) for v in copies['files']}
copylookup={(v['source_run'],v['relative_path']):v['copy_relative_path'] for v in copies['files']}
comparisons=[];obsdir=RANK/'observation-inputs';obsdir.mkdir(exist_ok=False)
for r in rows:
 cid=r['candidate_id']
 for sp in ['human','mouse']:
  o=r[sp]
  for v in [o['native_structure'],*o['artifact_sources'].values()]:
   path=BASE/v['source_run']/v['relative_path']
   if not path.is_file():path=RUN/copylookup[v['source_run'],v['relative_path']]
   assert path.is_file() and sha(path)==v['sha256'],str(path);v['path']=str(path)
  with np.load(o['artifact_sources']['pae']['path'],allow_pickle=False) as x:values=ip['binder_pair_scores'](x['pae'],152 if sp=='human' else 148,len(r['sequence']))
  assert all(abs(values[ch]-o['ipsae_by_protomer'][ch])<1e-12 for ch in 'ABC')
  conf=json.loads(Path(o['artifact_sources']['confidence']['path']).read_text());assert conf['confidence_score']==o['confidence_score'] and conf['ptm']==o['ptm'] and conf['iptm']==o['complex_iptm']
  comparisons.append({'candidate_id':cid,'species':sp,'ipsae_difference':max(abs(values[ch]-o['ipsae_by_protomer'][ch]) for ch in 'ABC'),'structure_sha256':o['native_structure']['sha256']})
 record={'observation_id':'2026-10-09_paired-ipsae-pose-tm_001','candidate_id':cid,'method':'mean best-protomer Dunbrack v4 IPSAE times target-aligned identical-binder TM','version':'2026-10-09_v6','scope':{'evidence_type':'computational prediction comparison','species':['human','mouse'],'construct':'frozen human152/mouse148 aa soluble TNF-alpha, identical exact binder sequence','assembly':'target trimer and binder','pH':'not modeled','reference':'mutual Boltz2 predictions','pose_definition':'target-only homologous proper fit, equivalent-copy mapping within0.1A target minimum, max binder pose TM, full binder length d0 normalization'},'artifact':{'campaign_id':'2026-10-07_tnfa-foundry-boltz2-migration','run_id':RUN.name,'path':str((RANK/'scores.json').relative_to(RUN)),'sha256':sha(RANK/'scores.json')},'locator':{'format':'json','pointer':'/'+cid+'/ipsae_times_binder_pose_tm'},'value':r['ipsae_times_binder_pose_tm'],'candidate_binding':{'kind':'sequence_sha256','locator':{'format':'json','pointer':'/'+cid+'/sequence_sha256'}}}
 op=obsdir/(cid+'.json');op.write_text(json.dumps(record,indent=2)+'\n');subprocess.run(['python3','scripts/workspace.py','candidate','observe','--record',str(op)],check=True,capture_output=True)
 trace=subprocess.run(['python3','scripts/workspace.py','candidate','trace','--id',cid],check=True,capture_output=True,text=True);tp=RANK/(cid+'_trace.json');tp.write_text(trace.stdout);r['candidate_trace']={'path':str(tp),'sha256':sha(tp)}
(RANK/'selected.json').write_text(json.dumps(rows,indent=2)+'\n')
(RANK/'local-score-validation.json').write_text(json.dumps({'all_selected_native_hashes_verified':True,'comparisons':comparisons,'registered_observations':len(rows),'fresh_traces_verified':len(rows)},indent=2)+'\n')
print(json.dumps({'selected':len(rows),'models':len(comparisons),'max_ipsae_difference':max(c['ipsae_difference'] for c in comparisons)},indent=2))
