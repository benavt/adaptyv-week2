import subprocess,json,datetime
from pathlib import Path
code='''from pathlib import Path
import subprocess,json,hashlib
r=Path("MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2/campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-10_boltz2-cache-loss-recovery_001")
groups=json.loads((r/"01_staging/payload/array-group-ids.json").read_text());tasks={t["task_id"]:t for t in json.loads((r/"01_staging/payload/tasks.json").read_text())};out=[]
for f in sorted((r/"receipts/2026-10-10_bulk-submission_001/resources").glob("*.log")):
 events=[json.loads(x[len("[resource] "):]) for x in f.read_text().splitlines() if x.startswith("[resource] ")]
 end=[e for e in events if e.get("event")=="command_exit"]
 if not end:continue
 idx=int(f.name.split("_")[1].split("-")[0]);gid=groups[idx]
 c=subprocess.run(["/usr/bin/python3","MACHINE_CONFIGURED_PATH/scripts/slurm_monitor/2026-10-06_v1/check_log.py",str(f),"--gpu","--finished"],capture_output=True,text=True);check=json.loads(c.stdout)
 index=r/"03_filtering/2026-10-09_predictions_001"/gid/"result-index.json";rows=json.loads(index.read_text())["predictions"] if index.exists() else []
 expected=[t for t in tasks.values() if t["group_id"]==gid]
 good=end[-1]["exit_code"]==0 and check["status"]=="pass" and len(rows)==len(expected)
 for row in rows:
  t=tasks[row["task_id"]];assert row["binder_sequence_sha256"]==t["binder_sequence_sha256"] and row["target_sequence_sha256"]==t["target_sequence_sha256"]
 out.append({"array_index":idx,"group":gid,"native_exit":end[-1]["exit_code"],"telemetry":check,"expected":len(expected),"indexed":len(rows),"status":"validated_execution_index_metadata" if good else "requires_investigation","index_sha256":hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None})
print(json.dumps({"finished_task_count":len(out),"issues":[o for o in out if o["status"]!="validated_execution_index_metadata"],"indexed_predictions_in_finished_groups":sum(o["indexed"] for o in out),"tasks":out}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','mimas','/usr/bin/python3 -'],input=code,text=True,capture_output=True);print(r.stderr);r.check_returncode();d=json.loads(r.stdout);d['checked_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=Path('local/2026-10-09_boltz2-results-retrieval_001/2026-10-10_cache-recovery-audit_1220.json');assert not p.exists();p.write_text(json.dumps(d,indent=2)+'\n');print({k:v for k,v in d.items() if k!='tasks'})
