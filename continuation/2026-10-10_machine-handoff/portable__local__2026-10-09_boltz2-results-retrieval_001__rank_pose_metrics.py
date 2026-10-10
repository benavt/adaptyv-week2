from pathlib import Path
import collections, csv, datetime, hashlib, json, subprocess

ROOT=Path.cwd()
RUN=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-pose-conservation_007'
SOURCE=RUN/'04_analysis/2026-10-09_all-available-pose-metrics_001'
TRACE=ROOT/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001'
COHORTS=['original-human','original-mouse','revised-human','revised-mouse']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

completion=json.loads((SOURCE/'completion.json').read_text())
assert completion['status']=='validated' and sha(SOURCE/'metrics.jsonl')==completion['metrics_sha256']
tc=json.loads((TRACE/'completion.json').read_text())
assert tc['status']=='validated' and sha(TRACE/'trace-index.json')==tc['trace_index_sha256']
traces={r['candidate_id']:r for r in json.loads((TRACE/'trace-index.json').read_text())}
scores={};cohorts=collections.defaultdict(list)
for line,raw in enumerate((SOURCE/'metrics.jsonl').read_text().splitlines(),1):
    r=json.loads(raw);cid=r['candidate_id'];t=traces[cid]
    assert t['status']=='verified' and t['sequence_sha256']==r['sequence_sha256']
    assert sha(TRACE/t['trace_path'])==t['trace_sha256'];assert cid not in scores
    assert r['mean_ipsae']==(r['human']['ipsae']+r['mouse']['ipsae'])/2
    assert r['ipsae_times_binder_pose_tm']==r['mean_ipsae']*r['pose']['binder_pose_tm_target_aligned']
    r['score_source']={'path':str(SOURCE/'metrics.jsonl'),'sha256':completion['metrics_sha256'],'line':line}
    r['candidate_trace']={'path':str(TRACE/t['trace_path']),'sha256':t['trace_sha256']}
    scores[cid]=r;cohorts[r['cohort']].append(r)
assert len(scores)==completion['pair_count']==13937
assert dict((c,len(v)) for c,v in cohorts.items())==completion['cohort_counts']
out=RUN/'04_analysis/2026-10-09_local-pose-ranking_001';out.mkdir(exist_ok=False)
full={'original-human':8552,'original-mouse':8688,'revised-human':7672,'revised-mouse':7576}
selected=[];ranked=[]
for c in COHORTS:
    rows=sorted(cohorts[c],key=lambda r:(-r['ipsae_times_binder_pose_tm'],r['candidate_id']))
    for rank,r in enumerate(rows,1):r.update(rank=rank,available_pair_count=len(rows),full_cohort_size=full[c],selected=rank<=5)
    ranked.extend(rows);selected.extend(rows[:5])
(out/'scores.json').write_text(json.dumps(scores,sort_keys=True,indent=2)+'\n')
(out/'selected-before-collection.json').write_text(json.dumps(selected,indent=2)+'\n')
columns=['cohort','rank','candidate_id','sequence','sequence_sha256','human_ipsae','mouse_ipsae','mean_ipsae','binder_pose_tm','whole_complex_tm_human_normalized','dockq_symmetric','ipsae_times_binder_pose_tm','available_pair_count','full_cohort_size','selected']
with (out/'ranked.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
    for r in ranked:
        flat={k:r[k] for k in columns if k in r}
        flat.update(human_ipsae=r['human']['ipsae'],mouse_ipsae=r['mouse']['ipsae'],binder_pose_tm=r['pose']['binder_pose_tm_target_aligned'],whole_complex_tm_human_normalized=r['pose']['whole_complex_tm_human_normalized'],dockq_symmetric=r['pose']['dockq_symmetric'])
        w.writerow(flat)
method={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'mean human/mouse best-protomer IPSAE times target-aligned identical binder pose TM','version':'2026-10-09_v6; DockQ2.1.4; runtime record pins USalign','rationale':'Top five complete paired designs per cohort for the requested test/report. Pose similarity penalizes different predicted binding sites and conformations. Whole-complex TM and symmetric DockQ remain comparison diagnostics.','scope':'Frozen all-available complete paired snapshot. Incomplete cohorts do not constitute final full-cohort selection. Computational predictions are mutual references.','available_pairs':completion['cohort_counts'],'full_cohort_sizes':full,'tie_break':'full precision product descending, candidate ID ascending','source_metrics':{'path':str(SOURCE/'metrics.jsonl'),'sha256':completion['metrics_sha256']},'runtime':json.loads((SOURCE/'runtime.json').read_text()),'settings':json.loads((RUN/'01_staging/payload/settings.json').read_text()),'candidate_trace_completion_sha256':sha(TRACE/'completion.json'),'scores_sha256':sha(out/'scores.json'),'historical_sources':json.loads((RUN/'01_staging/payload/historical-source-manifest.json').read_text()),'evidence':[{'candidate_id':r['candidate_id'],'observation_id':'2026-10-09_paired-ipsae-pose-tm_001'} for r in selected]}
(out/'selection-method.json').write_text(json.dumps(method,indent=2)+'\n')
byrun=collections.defaultdict(set)
for r in selected:
    for sp in ['human','mouse']:
        o=r[sp];e=o['native_structure'];byrun[e['source_run']].add(e['relative_path'])
        for v in o['artifact_sources'].values():byrun[v['source_run']].add(v['relative_path'])
for name,files in byrun.items():
    p=out/(name+'_selected-files.txt');p.write_text('\n'.join(sorted(files))+'\n')
print(json.dumps({'selected':len(selected),'pairs':len(scores),'files_by_source_run':{k:len(v) for k,v in byrun.items()},'output':str(out),'winners':[{k:r[k] for k in ['cohort','candidate_id','rank','mean_ipsae','ipsae_times_binder_pose_tm']} for r in selected]},indent=2))
