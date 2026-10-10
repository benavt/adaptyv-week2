from pathlib import Path
import subprocess,json
b=Path('local/2026-10-09_boltz2-results-retrieval_001')
remote=r"""
import pathlib,json,subprocess,hashlib,datetime,re
r=pathlib.Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-missing-prediction-recovery_001');d=r/'04_analysis/2026-10-09_recovery-execution-evidence_009';d.mkdir(exist_ok=False);rows=[];files=[]
for f in sorted((r/'receipts/2026-10-09_bulk-submission_001/resources').glob('resource-9698_*.log')):
 n=int(re.search(r'resource-9698_(\d+)-',f.name).group(1))
 if n<203:continue
 s=f.read_text();finished='"event": "command_exit"' in s;p=subprocess.run(['/usr/bin/python3','MACHINE_CONFIGURED_PATH/scripts/slurm_monitor/2026-10-06_v1/check_log.py',str(f),'--gpu']+(['--finished'] if finished else []),capture_output=True,text=True);check=json.loads(p.stdout);cf=d/(f.name+'.check.json');cf.write_text(p.stdout);files.append(str(cf.relative_to(r)));row={'task':n,'finished':finished,'telemetry':check}
 if finished:
  exits=[json.loads(x.split('[resource] ',1)[1]) for x in s.splitlines() if '"event": "command_exit"' in x];assert exits[-1]['exit_code']==0;idx=r/f'03_filtering/2026-10-09_predictions_001/batch-{295+n}/result-index.json';data=json.loads(idx.read_text());row['predictions']=len(data['predictions']);row['index_sha256']=hashlib.sha256(idx.read_bytes()).hexdigest();files.append(str(idx.relative_to(r)))
  for source in [f,r/f'slurm-9698_{n}.out']:
   dest=d/source.name;dest.write_bytes(source.read_bytes());files.append(str(dest.relative_to(r)))
 assert check['status']=='pass';rows.append(row)
validation={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows};(d/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');files.append(str((d/'validation.json').relative_to(r)));print(json.dumps({'validation':validation,'files':files}))
"""
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','mimas','/usr/bin/python3 -'],input=remote,text=True,capture_output=True)
if p.returncode:print(p.stderr,flush=True);raise SystemExit(p.returncode)
data=json.loads(p.stdout);(b/'2026-10-09_remote-recovery-audit_2113.json').write_text(json.dumps(data,indent=2)+'\n');plan=b/'2026-10-09_collect-recovery-indices_009.txt';plan.write_text('\n'.join(data['files'])+'\n');print('Validated',sum(x.get('predictions',0) for x in data['validation']['rows']),'new predictions',flush=True)
subprocess.run(['python3','scripts/workspace.py','collect','2026-10-07_tnfa-foundry-boltz2-migration','2026-10-09_boltz2-missing-prediction-recovery_001','--files-from',str(plan),'--apply'],check=True)
