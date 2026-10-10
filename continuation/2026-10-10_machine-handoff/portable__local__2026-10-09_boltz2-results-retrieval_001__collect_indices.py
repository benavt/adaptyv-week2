from pathlib import Path
import json,subprocess
root=Path.cwd();out=root/'local/2026-10-09_boltz2-results-retrieval_001';campaign='2026-10-07_tnfa-foundry-boltz2-migration'
for line in (out/'inventory.jsonl').read_text().splitlines():
 x=json.loads(line);r=root/'campaigns'/campaign/'runs'/x['run'];names=[n for n in x['indices'] if not (r/n).exists()]
 for start in range(0,len(names),160):
  dest=out/(x['run']+f'_indices_{start:04d}.txt');dest.write_text('\n'.join(names[start:start+160])+'\n')
  args=['python3','scripts/workspace.py','collect',campaign,x['run'],'--files-from',str(dest)]
  subprocess.run(args,check=True);subprocess.run(args+['--apply'],check=True)
  print('Collected index batch',x['run'],start,flush=True)
