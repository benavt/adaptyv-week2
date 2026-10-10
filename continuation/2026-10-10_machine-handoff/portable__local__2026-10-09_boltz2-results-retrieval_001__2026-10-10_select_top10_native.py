from pathlib import Path
import json,collections,hashlib
B=Path('campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs');R=B/'2026-10-10_boltz2-completed-pose-metrics_003';S=R/'04_analysis/2026-10-10_completed-pose-metrics_003';O=R/'04_analysis/2026-10-10_top10-selection_001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((S/'completion.json').read_text());assert c['status']=='validated' and c['pair_count']==32488 and sha(S/'metrics.jsonl')==c['metrics_sha256'];cohorts=collections.defaultdict(list)
for i,line in enumerate((S/'metrics.jsonl').open(),1):
 r=json.loads(line);r['score_source']={'path':str(S/'metrics.jsonl'),'sha256':c['metrics_sha256'],'line':i};cohorts[r['cohort']].append(r)
assert {k:len(v) for k,v in cohorts.items()}=={'original-human':8552,'original-mouse':8688,'revised-human':7672,'revised-mouse':7576};O.mkdir(exist_ok=False);rows=[];missing=collections.defaultdict(set)
for cohort in ['original-human','original-mouse','revised-human','revised-mouse']:
 for rank,r in enumerate(sorted(cohorts[cohort],key=lambda r:(-r['ipsae_times_binder_pose_tm'],r['candidate_id']))[:10],1):
  r['rank_within_cohort']=rank;rows.append(r)
  for sp in ['human','mouse']:
   e=r[sp]['native_structure'];p=B/e['source_run']/e['relative_path'];e['path']=str(p)
   if p.exists():assert sha(p)==e['sha256']
   else:missing[e['source_run']].add(e['relative_path'])
(O/'selected-before-collection.json').write_text(json.dumps(rows,indent=2)+'\n')
for run,names in missing.items():(O/(run+'_missing-selected-CIFs.txt')).write_text('\n'.join(sorted(names))+'\n')
(O/'selection-evidence.json').write_text(json.dumps({'selected_designs':40,'models':80,'full_pairs':32488,'method':'mean IPSAE times target-aligned binder pose TM; descending full precision, candidateID ties','metrics_sha256':c['metrics_sha256'],'missing_models_by_source_run':{k:len(v) for k,v in missing.items()}},indent=2)+'\n');print(O)
