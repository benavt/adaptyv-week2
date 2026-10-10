from pathlib import Path
import json,csv,hashlib,collections,datetime
ROOT=Path.cwd();RUN=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-10_boltz2-completed-pose-metrics_001';SRC=RUN/'04_analysis/2026-10-10_completed-pose-metrics_001';OUT=RUN/'04_analysis/2026-10-10_completed-pose-score-table_001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((SRC/'completion.json').read_text());assert c['status']=='validated' and c['pair_count']==27980;assert sha(SRC/'metrics.jsonl')==c['metrics_sha256'];assert sha(SRC/'runtime.json')==c['runtime_sha256']
TRACE=ROOT/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001';tc=json.loads((TRACE/'completion.json').read_text());assert tc['status']=='validated' and sha(TRACE/'trace-index.json')==tc['trace_index_sha256'];traces={r['candidate_id']:r for r in json.loads((TRACE/'trace-index.json').read_text())}
oldsrc=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-pose-conservation_007/04_analysis/2026-10-09_all-available-pose-metrics_001';oc=json.loads((oldsrc/'completion.json').read_text());assert sha(oldsrc/'metrics.jsonl')==oc['metrics_sha256'];old={r['candidate_id']:r for r in map(json.loads,(oldsrc/'metrics.jsonl').read_text().splitlines())}
cohorts=collections.defaultdict(list);seen=set();overlap=0;missingdockq=0
for line,raw in enumerate((SRC/'metrics.jsonl').open(),1):
 r=json.loads(raw);cid=r['candidate_id'];assert cid not in seen;seen.add(cid);t=traces[cid];assert t['status']=='verified' and t['sequence_sha256']==r['sequence_sha256'];assert sha(TRACE/t['trace_path'])==t['trace_sha256']
 assert r['mean_ipsae']==(r['human']['ipsae']+r['mouse']['ipsae'])/2;assert r['ipsae_times_binder_pose_tm']==r['mean_ipsae']*r['pose']['binder_pose_tm_target_aligned']
 assert all(v['all_atom_site_values_except_chain_names_preserved'] for v in r['pose']['canonical_adapter_records'].values())
 if cid in old:
  o=old[cid];overlap+=1;assert r['mean_ipsae']==o['mean_ipsae']
  for key in ['binder_pose_tm_target_aligned','dockq_symmetric']:assert r['pose'][key]==o['pose'][key]
  for sp in ['human','mouse']:assert r[sp]['native_structure']['sha256']==o[sp]['native_structure']['sha256']
 if r['pose']['dockq_symmetric'] is None:missingdockq+=1
 r['score_source']={'path':str(SRC/'metrics.jsonl'),'sha256':c['metrics_sha256'],'line':line};r['candidate_trace']={'path':str(TRACE/t['trace_path']),'sha256':t['trace_sha256']};cohorts[r['cohort']].append(r)
assert overlap==13937 and len(seen)==27980 and {k:len(v) for k,v in cohorts.items()}==c['cohort_counts']
full={'original-human':8552,'original-mouse':8688,'revised-human':7672,'revised-mouse':7576};OUT.mkdir(exist_ok=False)
cols=['cohort','rank_within_completed_snapshot','candidate_id','sequence','human_ipsae','mouse_ipsae','mean_ipsae','binder_pose_tm','whole_complex_tm_human_normalized','dockq_symmetric','ipsae_times_binder_pose_tm','human_confidence','mouse_confidence','human_ptm','mouse_ptm','human_iptm','mouse_iptm','human_binder_plddt','mouse_binder_plddt','complete_pairs','full_cohort_size','cohort_complete','score_source_line','score_source_sha256']
with (OUT/'2026-10-10_TNFA_completed_pairs_all_metrics.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for cohort in full:
  rows=sorted(cohorts[cohort],key=lambda r:(-r['ipsae_times_binder_pose_tm'],r['candidate_id']))
  for rank,r in enumerate(rows,1):
   flat={'cohort':cohort,'rank_within_completed_snapshot':rank,'candidate_id':r['candidate_id'],'sequence':r['sequence'],'human_ipsae':r['human']['ipsae'],'mouse_ipsae':r['mouse']['ipsae'],'mean_ipsae':r['mean_ipsae'],'binder_pose_tm':r['pose']['binder_pose_tm_target_aligned'],'whole_complex_tm_human_normalized':r['pose']['whole_complex_tm_human_normalized'],'dockq_symmetric':r['pose']['dockq_symmetric'],'ipsae_times_binder_pose_tm':r['ipsae_times_binder_pose_tm'],'complete_pairs':len(rows),'full_cohort_size':full[cohort],'cohort_complete':len(rows)==full[cohort],'score_source_line':r['score_source']['line'],'score_source_sha256':c['metrics_sha256']}
   for sp in ['human','mouse']:
    for short,key in [('confidence','confidence_score'),('ptm','ptm'),('iptm','complex_iptm'),('binder_plddt','binder_plddt_0_to_100')]:flat[sp+'_'+short]=r[sp].get(key)
   w.writerow(flat)
(OUT/'validation.json').write_text(json.dumps({'status':'validated','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':len(seen),'reused_primary_metrics_exact_matches':overlap,'cohorts':c['cohort_counts'],'full_cohorts':full,'dockq_missing_no_contacts':missingdockq,'metrics_sha256':c['metrics_sha256'],'csv_sha256':sha(OUT/'2026-10-10_TNFA_completed_pairs_all_metrics.csv'),'scope':'Completed-pair snapshot, three full cohorts; revised-mouse incomplete. Predicted structures are mutual references.'},indent=2)+'\n');print(OUT)
