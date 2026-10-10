from pathlib import Path
import json,hashlib,shutil,collections
root=Path.cwd();work=root/'drafts/03_filtering/2026-10-09_boltz2-missing-prediction-recovery_001';work.mkdir(parents=True,exist_ok=False)
evidence=json.loads((root/'local/2026-10-09_boltz2-results-retrieval_001/recovery-sources.json').read_text())
prior=root/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-08_boltz2-four-cohort-increment_001';old=json.loads((prior/'01_staging/payload/tasks.json').read_text());missing=set(evidence['coverage']['missing']);tasks=[t for t in old if t['task_id'] in missing]
assert len(tasks)==37194 and not evidence['coverage']['incomplete']
pilot_ids=set();bycandidate=collections.defaultdict(list)
for t in tasks:bycandidate[t['candidate_id']].append(t)
for cohort in sorted({t['source_cohort'] for t in tasks}):
 cand=next((v for v in bycandidate.values() if v[0]['source_cohort']==cohort and {t['target_species'] for t in v}=={'human','mouse'}),None)
 if cand:pilot_ids.update(t['task_id'] for t in cand)
groups=collections.defaultdict(list)
for t in tasks:
 source=prior/'01_staging/payload'/t['native_input_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==t['native_input_sha256']
 original_group=t['group_id'];t['predecessor_group_id']=original_group;t['group_id']='pilot' if t['task_id'] in pilot_ids else original_group
 t['native_input_path']='native-inputs/'+t['group_id']+'/'+t['task_id']+'.yaml'
 dest=work/t['native_input_path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 groups[t['group_id']].append(t['task_id'])
(work/'tasks.json').write_text(json.dumps(tasks,indent=2)+'\n');(work/'groups.json').write_text(json.dumps([{'group_id':g,'task_ids':v} for g,v in sorted(groups.items())],indent=2)+'\n');(work/'validation.py').write_text(evidence['validation.py']['text'])
plan=json.loads(evidence['preparation.json']['text'])
settings={'method':'Boltz2_missing_prediction_recovery','predecessor_campaign':prior.parent.parent.name,'predecessor_run':prior.name,'recovery_predecessor':evidence['preparation.json']['source'],'task_count':len(tasks),'pilot_prediction_count':len(pilot_ids),'scientific_options':plan['prediction_options'],'native_entrypoint':plan['native_entrypoint'],'mode':plan['mode'],'checkpoint_sha256':'090e82ac8c92f5e943fa1b39e7410a44027bea7243c0bbb3caa67a77fc1428e1','preservation':'New outputs only in new run. Every existing original model is preserved. No inference for tasks with any historical CIF.','seed_scope':'Seed 0 per recovery invocation; original group membership retained except completed models and six pilot tasks. RNG replay of a partially completed native batch is not claimed.','missing_task_audit':{'source':'2026-10-09 remote canonical output scan','source_sha256':hashlib.sha256((root/'local/2026-10-09_boltz2-results-retrieval_001/recovery-sources.json').read_bytes()).hexdigest()},'cache_repair':evidence['mols_tar'],'runtime_pins':plan['external_sha256'],'ranking':{'scope':'all four source cohorts separately; full completed human/mouse pairs required','IPSAE':'best binder-protomer symmetric ipSAE (D vs A/B/C); PAE cutoff 10; distance diagnostics cutoff 15','species_aggregation':'arithmetic mean of human and mouse'}}
(work/'recovery-plan.json').write_text(json.dumps(settings,indent=2)+'\n');(work/'settings.json').write_text(json.dumps(settings,indent=2)+'\n');(work/'source-resource-logging-SKILL.md').write_text(evidence['resource-logging-SKILL.md']['text']);(work/'source-workflow-manifest.json').write_text(evidence['workflow-manifest.json']['text'])
(work/'array-group-ids.json').write_text(json.dumps([g for g in sorted(groups) if g!='pilot'])+'\n')
print(work);print({'missing':len(tasks),'pilot':len(pilot_ids),'bulk_groups':len(groups)-1,'missing_by_cohort':dict(collections.Counter(t['source_cohort'] for t in tasks))})
