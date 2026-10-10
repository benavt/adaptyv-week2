from pathlib import Path
import argparse,json,hashlib,subprocess
p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();root=Path.cwd();campaign='2026-10-07_tnfa-foundry-boltz2-migration';r=root/'campaigns'/campaign/'runs'/a.run;out=root/'local/2026-10-09_boltz2-results-retrieval_001'
records={}
for f in sorted(r.glob('03_filtering/**/result-index.json')):
 for row in json.loads(f.read_text())['predictions']:
  task=row['task_id']
  if task in records and records[task]['files_sha256']!=row['files_sha256']:raise RuntimeError('Conflicting result indexes: '+task)
  records[task]=row
files={}
for row in records.values():
 for name,h in row['files_sha256'].items():
  path=Path(name)
  if path.suffix=='.cif' or path.name.startswith(('confidence_','pae_','plddt_')):
   if (r/name).exists():
    assert hashlib.sha256((r/name).read_bytes()).hexdigest()==h
   else:files[name]=h
all_list=out/(a.run+'_models_all.txt');all_list.write_text('\n'.join(sorted(files))+'\n')
args=['python3','scripts/workspace.py','collect',campaign,a.run,'--files-from']
subprocess.run(args+[str(all_list)],check=True)
print('Planned collection',len(records),'predictions',len(files),'files',flush=True)
names=sorted(files)
for start in range(0,len(names),180):
 dest=out/(a.run+f'_models_{start:06d}.txt');dest.write_text('\n'.join(names[start:start+180])+'\n')
 subprocess.run(args+[str(dest),'--apply'],check=True,stdout=subprocess.DEVNULL)
 print('Verified files',min(start+180,len(names)),'/',len(names),flush=True)
print('COLLECTION COMPLETE',a.run,flush=True)
