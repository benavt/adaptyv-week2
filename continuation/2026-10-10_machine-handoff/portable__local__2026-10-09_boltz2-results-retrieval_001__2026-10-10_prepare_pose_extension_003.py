from pathlib import Path
import json,gzip,hashlib,collections,shutil,datetime
ROOT=Path.cwd();B=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs';OLD=B/'2026-10-10_boltz2-completed-pose-metrics_002';P=OLD/'01_staging/payload';D=ROOT/'drafts/04_analysis/2026-10-10_boltz2-completed-pose-metrics_003';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tasks={};records={}
for r in sorted(B.iterdir()):
 p=r/'01_staging/payload/tasks.json'
 if p.exists() and 'boltz2' in r.name:
  for t in json.loads(p.read_text()):tasks[t['task_id']]=t
 indices=list(r.glob('03_filtering/**/result-index.json'))
 if r.name=='2026-10-09_boltz2-missing-prediction-recovery_001':indices+=list(r.glob('04_analysis/2026-10-10_partial-output-audit_001/result-index.json'))
 for f in sorted(indices):
  for row in json.loads(f.read_text()).get('predictions',[]):
   tid=row['task_id'];e=(r,f,row)
   if tid in records:assert records[tid][2]['files_sha256']==row['files_sha256'],tid
   else:records[tid]=e
pairs=[]
for cid in sorted({t['candidate_id'] for t in tasks.values()}):
 if not all(cid+'__'+s in records for s in ['human','mouse']):continue
 t=tasks[cid+'__human'];cohort=t['source_cohort'];cohort='revised-'+cohort if cohort in ['human','mouse'] else cohort
 pair={'candidate_id':cid,'cohort':cohort,'sequence':t['binder_sequence'],'sequence_sha256':t['binder_sequence_sha256']}
 for sp in ['human','mouse']:
  tid=cid+'__'+sp;r,f,row=records[tid];fs=row['files_sha256'];native=[n for n in fs if n.endswith('.cif')];assert len(native)==1
  art={}
  for k in ['pae','confidence','plddt']:
   names=[n for n in fs if Path(n).name.startswith(k+'_')];assert len(names)==1;art[k]={'relative_path':names[0],'sha256':fs[names[0]]}
  pair[sp]={'task_id':tid,'source_run':r.name,'index_path':str(f.relative_to(r)),'index_sha256':sha(f),'native_structure':{'relative_path':native[0],'sha256':fs[native[0]]},'artifact_sources':art,'target_sequence':tasks[tid]['target_sequence'],'binder_sequence_sha256':t['binder_sequence_sha256']}
 pairs.append(pair)
(D/'pairs.json.gz').write_bytes(gzip.compress(json.dumps(pairs).encode(),mtime=0))
assert len(pairs)==32488
resume_count=30028
parent_sha='fa3213e6a7d75f8038354cb5d7de74d9df00a8ef9a55ef48badfe9e7bc4c3e3c'
(D/'reuse-ipsae.jsonl').write_text('')
shutil.copytree(P/'vendor',D/'vendor');shutil.copy2(P/'pinned-ipsae.py',D/'pinned-ipsae.py');shutil.copy2(B/'2026-10-09_whole-tm-adapter-repair_001/01_staging/payload/canonical_tm.py',D/'canonical_tm.py')
s=json.loads((P/'settings.json').read_text());s.update(version='2026-10-10_v1',scope='All completed hash-indexed paired predictions at frozen snapshot; incremental missing pose metrics with corrected canonical whole-complex TM',available_pairs=dict(collections.Counter(r['cohort'] for r in pairs)),pair_count=len(pairs),ranking='Mean IPSAE times target-aligned binder pose TM; top10 per parent design run for updated report',predecessor=OLD.name,execution_resume={'source_run':OLD.name,'path':'04_analysis/2026-10-10_completed-pose-metrics_002/metrics.jsonl','sha256':parent_sha,'pair_count':resume_count,'reason':'Reuse validated primary metrics and corrected canonical whole TM for exact matching native hashes'},reuse_ipsae={'path':'payload/reuse-ipsae.jsonl','sha256':sha(D/'reuse-ipsae.jsonl')})
(D/'settings.json').write_text(json.dumps(s,indent=2)+'\n')
code=(P/'score_pose.py').read_text().replace('2026-10-10_completed-pose-metrics_002','2026-10-10_completed-pose-metrics_003').replace('2026-10-10_pose-pilot_002','2026-10-10_pose-pilot_003')
(D/'score_pose.py').write_text(code)
for n in ['all.sbatch','pilot.sbatch']:shutil.copy2(P/n,D/n)
(D/'snapshot-evidence.json').write_text(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':len(pairs),'reuse_pairs':resume_count,'new_pairs':len(pairs)-resume_count,'cohorts':s['available_pairs'],'parent_metrics_sha256':parent_sha,'canonical_score_source_sha256':parent_sha,'salvaged_models_included':True,'partial_cohorts_explicit':True},indent=2)+'\n')
compile(code,str(D/'score_pose.py'),'exec');print((D/'snapshot-evidence.json').read_text())
