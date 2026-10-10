from pathlib import Path
import tarfile,io,subprocess,shlex,json
root=Path.cwd();base=root/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-10_boltz2-cache-loss-recovery_001/01_staging';buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w:gz') as tar:
 for p in base.rglob('*'):
  if p.is_file() and 'native-inputs' not in p.parts:tar.add(p,arcname=str(p.relative_to(base)))
code=r'''
from pathlib import Path
import sys,tarfile,io,hashlib,json,shutil,datetime
run=Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-10_boltz2-cache-loss-recovery_001');stage=run/'01_staging';stage.mkdir(parents=True,exist_ok=True)
assert not (run/'receipts').exists() or not any((run/'receipts').glob('*/submission-result.json'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as tar:
 for m in tar.getmembers():
  p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and m.isfile()
  data=tar.extractfile(m).read();dest=stage/p
  if dest.exists():assert dest.read_bytes()==data,'Interrupted/conflicting metadata: '+str(dest)
  else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
manifest=json.loads((stage/'snapshot.json').read_text());tasks=json.loads((stage/'payload/tasks.json').read_text());parent=run.parent/'2026-10-09_boltz2-missing-prediction-recovery_001/01_staging/payload'
for t in tasks:
 dest=stage/'payload'/t['native_input_path'];source=parent/'native-inputs'/t['parent_recovery_group_id']/(t['task_id']+'.yaml');assert sha(source)==t['native_input_sha256']
 if dest.exists():assert sha(dest)==t['native_input_sha256']
 else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
for name,h in manifest['files_sha256'].items():assert sha(stage/name)==h,name
for d in ['receipts','02_design','03_filtering','04_analysis']:(run/d).mkdir(exist_ok=True)
if (run/'run.json').exists():assert (run/'run.json').read_bytes()==(stage/'snapshot.json').read_bytes()
else:shutil.copyfile(stage/'snapshot.json',run/'run.json')
(run/'receipts/2026-10-10_reconstructed-upload_001.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'all_frozen_hashes_verified','native_inputs':len(tasks),'parent_native_inputs_preserved':True},indent=2)+'\n')
print('All frozen hashes verified: '+str(len(tasks))+' native inputs')
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','mimas','/usr/bin/python3 -c '+shlex.quote(code)],input=buf.getvalue(),capture_output=True);print(p.stdout.decode());print(p.stderr.decode());raise SystemExit(p.returncode)
