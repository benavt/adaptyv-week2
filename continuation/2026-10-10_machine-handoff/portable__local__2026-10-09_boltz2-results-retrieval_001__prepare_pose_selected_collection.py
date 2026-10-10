from pathlib import Path
import collections, hashlib, json
ROOT=Path.cwd();BASE=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs'
RUN=BASE/'2026-10-09_boltz2-pose-conservation_007';RANK=RUN/'04_analysis/2026-10-09_local-pose-ranking_001'
rows=json.loads((RANK/'selected-before-collection.json').read_text());files=collections.defaultdict(dict);missing=collections.defaultdict(set)
for r in rows:
 for sp in ['human','mouse']:
  o=r[sp]
  for kind,v in dict(structure=o['native_structure'],**o['artifact_sources']).items():
   key=(v['source_run'],v['relative_path']);assert key not in files or files[key]['sha256']==v['sha256']
   path=BASE/v['source_run']/v['relative_path'];entry=dict(v,kind=kind,candidate_id=r['candidate_id'],species=sp,path=str(path))
   entry['copy_relative_path']='04_analysis/2026-10-09_selected-pose-native-copies_001/'+r['candidate_id']+'/'+sp+'/'+Path(v['relative_path']).name
   files[key]=entry
   if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==v['sha256'],str(path)
   else:missing[v['source_run']].add(v['relative_path'])
for run,values in missing.items():(RANK/(run+'_missing-selected-files.txt')).write_text('\n'.join(sorted(values))+'\n')
(RANK/'selected-native-file-plan.json').write_text(json.dumps({'files':list(files.values()),'missing_by_run':{k:len(v) for k,v in missing.items()}},indent=2)+'\n')
(RANK/'selected-copy-files.txt').write_text('\n'.join(sorted([v['copy_relative_path'] for v in files.values()]+['04_analysis/2026-10-09_selected-pose-native-copies_001/manifest.json']))+'\n')
print(json.dumps({'files':len(files),'missing_by_run':{k:len(v) for k,v in missing.items()}},indent=2))
