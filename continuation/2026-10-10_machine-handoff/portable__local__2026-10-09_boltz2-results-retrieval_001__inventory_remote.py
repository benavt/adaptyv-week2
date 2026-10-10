import pathlib,json,collections,hashlib,sys
base=pathlib.Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs')
for name in ['2026-10-07_boltz2-paired-foundry-trimers_001','2026-10-08_boltz2-four-cohort-increment_001']:
 r=base/name;tasks=json.loads((r/'01_staging/payload/tasks.json').read_text());indices=sorted((r/'03_filtering').glob('**/result-index.json'));completed=[];sizes=collections.Counter();missing=[];scorefiles=[]
 for f in indices:
  x=json.loads(f.read_text())
  for p in x['predictions']:
   completed.append(p['task_id'])
   for path in p['files_sha256']:
    actual=r/path
    if actual.is_file():sizes[actual.suffix]+=actual.stat().st_size
    else:missing.append(path)
 for f in (r/'03_filtering').rglob('*'):
  if f.is_file() and ('ipsae' in f.name.lower() or f.suffix=='.csv'):scorefiles.append(str(f.relative_to(r)))
 print(json.dumps({'run':name,'expected':len(tasks),'completed':len(completed),'unique_completed':len(set(completed)),'missing_tasks':sorted(set(t['task_id'] for t in tasks)-set(completed)),'index_count':len(indices),'indices':[str(f.relative_to(r)) for f in indices],'size_bytes_by_extension':dict(sizes),'absent_indexed_files':missing,'existing_score_files':scorefiles,'tasks_sha256':hashlib.sha256((r/'01_staging/payload/tasks.json').read_bytes()).hexdigest()}),flush=True)
