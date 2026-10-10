from pathlib import Path
import json,hashlib,shutil,datetime
BASE=Path('MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs')
RUN=BASE/'2026-10-09_boltz2-pose-conservation_007'
ids=["2026-10-08_dd1-original-human-rfd3-b1082-m0","2026-10-08_dd1-original-human-rfd3-b833-m0","2026-10-08_dd1-original-human-rfd3-b4141-m2","2026-10-08_dd1-original-human-rfd3-b565-m6","2026-10-08_dd1-original-human-rfd3-b690-m6","2026-10-08_dd1-original-mouse-rfd3-b1451-m2","2026-10-08_dd1-original-mouse-rfd3-b1438-m5","2026-10-08_dd1-original-mouse-rfd3-b1162-m5","2026-10-08_dd1-original-mouse-rfd3-b1393-m6","2026-10-08_dd1-original-mouse-rfd3-b1032-m2","2026-10-07_dd1-human-rfd3-b789-m5","2026-10-07_dd1-human-rfd3-b1205-m4","2026-10-07_dd1-human-rfd3-b5696-m6","2026-10-07_dd1-human-rfd3-b700-m1","2026-10-07_dd1-human-rfd3-b2271-m7","2026-10-07_dd1-mouse-rfd3-b5908-m1","2026-10-07_dd1-mouse-rfd3-b3364-m4","2026-10-07_dd1-mouse-rfd3-b1226-m4","2026-10-07_dd1-mouse-rfd3-b3962-m3","2026-10-07_dd1-mouse-rfd3-b449-m3"]
source=RUN/'04_analysis/2026-10-09_all-available-pose-metrics_001/metrics.jsonl'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='bdbb1e8060f5619e50188a563d99aeeb30d7d3e6dce3a450aae1ab5357185d90'
out=RUN/'04_analysis/2026-10-09_selected-pose-native-copies_001';out.mkdir(exist_ok=False)
rows={}
with source.open() as f:
 for line in f:
  r=json.loads(line)
  if r['candidate_id'] in ids:rows[r['candidate_id']]=r
assert set(rows)==set(ids)
files=[]
for cid in ids:
 for sp in ['human','mouse']:
  o=rows[cid][sp]
  for kind,v in dict(structure=o['native_structure'],**o['artifact_sources']).items():
   src=BASE/v['source_run']/v['relative_path'];relative=str(out.relative_to(RUN)/cid/sp/src.name);dst=RUN/relative
   assert hashlib.sha256(src.read_bytes()).hexdigest()==v['sha256'],str(src)
   dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copy2(src,dst)
   assert hashlib.sha256(dst.read_bytes()).hexdigest()==v['sha256']
   files.append(dict(v,kind=kind,candidate_id=cid,species=sp,copy_relative_path=relative))
manifest={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_ids':ids,'score_source_sha256':'bdbb1e8060f5619e50188a563d99aeeb30d7d3e6dce3a450aae1ab5357185d90','status':'all160_native_and_copy_hashes_verified','files':files,'native_coordinates_preserved':True}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'copied':len(files),'status':manifest['status']}))

