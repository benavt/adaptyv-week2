import subprocess,json
from pathlib import Path
b=Path('local/2026-10-09_boltz2-results-retrieval_001')
code=r'''
from pathlib import Path
import json,hashlib,datetime,subprocess,re
RUN=Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-missing-prediction-recovery_001');P=RUN/'01_staging/payload';out=RUN/'04_analysis/2026-10-10_partial-output-audit_001';out.mkdir(exist_ok=False)
ns={'RUN':RUN};exec(compile((P/'validation.py').read_text(),str(P/'validation.py'),'exec'),ns)
tasks={t['task_id']:t for t in json.loads((P/'tasks.json').read_text())};groups=json.loads((P/'array-group-ids.json').read_text());valid=[];missing=[];partial=[];telemetry=[]
for n in range(428,582):
 gid=groups[n];native=RUN/'03_filtering/2026-10-09_predictions_001'/gid/'native'
 group=next(g for g in json.loads((P/'groups.json').read_text()) if g['group_id']==gid)
 for tid in group['task_ids']:
  d=native/'by_seed'/tid/'s0'
  if not list(d.glob('*_model_*.cif')):missing.append(tid);continue
  try:valid.extend(ns['validate_outputs'](native,[tasks[tid]],native=True))
  except Exception as e:partial.append({'task_id':tid,'exception':str(e)});missing.append(tid)
 f=next((RUN/'receipts/2026-10-09_bulk-submission_001/resources').glob(f'resource-9698_{n}-*.log'));p=subprocess.run(['/usr/bin/python3','MACHINE_CONFIGURED_PATH/scripts/slurm_monitor/2026-10-06_v1/check_log.py',str(f),'--gpu','--finished'],capture_output=True,text=True);telemetry.append({'task':n,'result':json.loads(p.stdout)})
(out/'result-index.json').write_text(json.dumps({'predictions':valid,'scope':'Scientifically valid native files salvaged from failed executions; native execution failure remains explicit','recovery_run':RUN.name},indent=2)+'\n');(out/'remaining-tasks.json').write_text(json.dumps([tasks[x] for x in missing],indent=2)+'\n');(out/'completion.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'validated_partial_models':len(valid),'remaining_tasks':len(missing),'invalid_partial':partial,'failed_jobs_final_telemetry':telemetry},indent=2)+'\n');print(json.dumps({'validated_partial_models':len(valid),'remaining_tasks':len(missing),'invalid_partial':len(partial)}))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','mimas','MACHINE_CONFIGURED_PATH/software/2026-10-08_boltz2-anthropic_001/env/bin/python -B -'],input=code,text=True,capture_output=True);(b/'2026-10-10_partial-audit_0218.log').write_text(p.stdout+p.stderr);print(p.stdout);print(p.stderr);raise SystemExit(p.returncode)
