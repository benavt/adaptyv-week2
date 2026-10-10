import json,pathlib,hashlib
r=pathlib.Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-08_boltz2-fast-resume-8708_001')
paths={n:r/n for n in ['run.json','preparation.json','resume.py','validation.py']}
paths['workflow-manifest.json']=pathlib.Path('MACHINE_CONFIGURED_PATH/folding/boltz2/workflows/2026-10-08_v1/manifest.json')
paths['resource-logging-SKILL.md']=pathlib.Path('MACHINE_CONFIGURED_PATH/skills/slurm-resource-logging/SKILL.md')
out={n:{'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'text':p.read_text()} for n,p in paths.items()}
original=r.parent/'2026-10-08_boltz2-four-cohort-increment_001';tasks=json.loads((original/'01_staging/payload/tasks.json').read_text())
missing=[];present=[];incomplete=[]
for t in tasks:
 d=original/'03_filtering/2026-10-08_predictions_001'/t['group_id']/('boltz_results_'+t['group_id'])/'predictions'/t['task_id'];tid=t['task_id']
 if not any(d.glob('*_model_*.cif')):missing.append(tid)
 else:
  files=[d/(tid+'_model_0.cif'),d/('confidence_'+tid+'_model_0.json'),d/('pae_'+tid+'_model_0.npz'),d/('pde_'+tid+'_model_0.npz'),d/('plddt_'+tid+'_model_0.npz')]
  present.append(tid)
  if not all(f.is_file() and f.stat().st_size for f in files):incomplete.append(tid)
out['coverage']={'missing':missing,'present':present,'incomplete':incomplete}
p=pathlib.Path('MACHINE_CONFIGURED_PATH/software/2026-10-08_boltz2-anthropic_001/weights/mols.tar');h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
out['mols_tar']={'path':str(p),'sha256':h.hexdigest(),'bytes':p.stat().st_size}
print(json.dumps(out))
