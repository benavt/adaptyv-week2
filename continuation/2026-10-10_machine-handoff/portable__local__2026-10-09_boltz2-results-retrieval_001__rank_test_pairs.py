from pathlib import Path
from collections import defaultdict
import json,hashlib,datetime
from zoneinfo import ZoneInfo
root=Path.cwd();run=root/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-four-cohort-test-deck_001';features=run/'03_filtering/2026-10-09_available-pair-features_001';trace=root/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
completion=json.loads((features/'completion.json').read_text());assert completion['status']=='validated' and sha(features/'features.jsonl')==completion['features_sha256']
tc=json.loads((trace/'completion.json').read_text());assert tc['status']=='validated' and sha(trace/'trace-index.json')==tc['trace_index_sha256'];traces={t['candidate_id']:t for t in json.loads((trace/'trace-index.json').read_text())}
cohorts=defaultdict(list);scores={};full={'original-human':8552,'original-mouse':8688,'revised-human':7672,'revised-mouse':7576}
for line_no,line in enumerate((features/'features.jsonl').read_text().splitlines(),1):
 row=json.loads(line);cid=row['candidate_id'];t=traces[cid];assert t['status']=='verified' and t['sequence_sha256']==row['sequence_sha256'];assert sha(trace/t['trace_path'])==t['trace_sha256'];assert cid not in scores
 row['mean_ipsae']=(row['human']['ipsae']+row['mouse']['ipsae'])/2;row['feature_source']={'path':str(features/'features.jsonl'),'sha256':completion['features_sha256'],'line':line_no};row['candidate_trace']={'path':str(trace/t['trace_path']),'sha256':t['trace_sha256']}
 scores[cid]=row;cohorts[row['cohort']].append(row)
assert len(scores)==13890 and {c:len(v) for c,v in cohorts.items()}==completion['cohort_counts']
selected=[]
for cohort in ['original-human','original-mouse','revised-human','revised-mouse']:
 rows=sorted(cohorts[cohort],key=lambda v:(-v['mean_ipsae'],v['candidate_id']));r=rows[0];r.update(available_pair_count=len(rows),full_cohort_size=full[cohort],rank=1);selected.append(r)
out=run/'03_filtering/2026-10-09_local-available-pair-ranking_001';out.mkdir(exist_ok=False)
(out/'scores.json').write_text(json.dumps(scores,sort_keys=True,indent=2)+'\n')
(out/'winners-before-collection.json').write_text(json.dumps(selected,indent=2)+'\n')
(out/'selection-method.json').write_text(json.dumps({'timestamp':datetime.datetime.now(ZoneInfo('America/New_York')).isoformat(),'method':'Arithmetic mean of matched human/mouse best binder-protomer symmetric IPSAE','version':'Dunbrack v4; 6174cf9e71cb1bd660cc805856a18c4871a6dec3; project 2026-10-09_v2','rationale':'Four requested test slides. Highest full-precision mean among all complete validated indexed pairs in each source cohort at frozen snapshot. Ascending candidate ID resolves ties. Incomplete pairs excluded explicitly. Final full-cohort top 1% deck remains pending.','available_pairs':completion['cohort_counts'],'full_cohort_sizes':full,'source_features':completion,'candidate_trace_completion_sha256':sha(trace/'completion.json'),'scores_sha256':sha(out/'scores.json')},indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['cohort','candidate_id','mean_ipsae','available_pair_count']} for r in selected],indent=2))
