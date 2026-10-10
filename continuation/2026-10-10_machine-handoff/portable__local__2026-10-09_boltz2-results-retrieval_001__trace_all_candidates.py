from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import hashlib,json,subprocess,datetime,shutil
from zoneinfo import ZoneInfo
ROOT=Path.cwd();PREP=ROOT/'drafts/04_analysis/2026-10-09_boltz2-top-one-percent-preparation_001/paired-candidate-index.json'
OUT=ROOT/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(ZoneInfo('America/New_York')).isoformat()
data=json.loads(PREP.read_text());rows=[{'cohort':cohort,**r} for cohort,group in data.items() for r in group]
assert len(rows)==32488 and len({r['candidate_id'] for r in rows})==32488
OUT.mkdir(parents=True,exist_ok=False);(OUT/'traces').mkdir();(OUT/'failures').mkdir()
shutil.copyfile(Path(__file__),OUT/'generator.py')
manifest={'started_at':now(),'status':'running','candidate_count':len(rows),'source_index':str(PREP),'source_index_sha256':sha(PREP),'workspace_frontdoor_sha256':sha(ROOT/'scripts/workspace.py'),'workflow_lock_sha256':sha(ROOT/'workflow.lock.json'),'generator_sha256':sha(Path(__file__)),'command':['python3','scripts/workspace.py','candidate','trace','--id','CANDIDATE'],'concurrency':4,'scope':'Existing candidate lineage verification before full-cohort ranking; no registry mutations, no score generation or eligibility certification.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def trace(row):
 candidate=row['candidate_id'];run=subprocess.run(['python3','scripts/workspace.py','candidate','trace','--id',candidate],cwd=ROOT,text=True,capture_output=True)
 if run.returncode:
  failure={'candidate_id':candidate,'cohort':row['cohort'],'returncode':run.returncode,'stderr':run.stderr,'stdout':run.stdout};(OUT/'failures'/(candidate+'.json')).write_text(json.dumps(failure,indent=2)+'\n');return {'candidate_id':candidate,'cohort':row['cohort'],'status':'failed','failure_path':'failures/'+candidate+'.json'}
 result=json.loads(run.stdout);assert result['candidate']['candidate_id']==candidate and result['candidate']['sequence_sha256']==row['sequence_sha256'] and result['candidate']['sequence']==row['sequence']
 path=OUT/'traces'/(candidate+'.json')
 with path.open('x') as f:f.write(run.stdout)
 return {'candidate_id':candidate,'cohort':row['cohort'],'sequence_sha256':row['sequence_sha256'],'status':'verified','trace_path':'traces/'+path.name,'trace_sha256':sha(path),'generation_unknowns':result['candidate']['generation_unknowns']}
results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(trace,row):row for row in rows}
 for future in as_completed(futures):
  row=futures[future]
  try:result=future.result()
  except Exception as error:
   result={'candidate_id':row['candidate_id'],'cohort':row['cohort'],'status':'failed','error':repr(error)}
  results.append(result)
  if len(results)%100==0:
   progress={'updated_at':now(),'processed':len(results),'expected':len(rows),'statuses':dict(Counter(r['status'] for r in results))};(OUT/'progress.json').write_text(json.dumps(progress,indent=2)+'\n');print(json.dumps(progress),flush=True)
results.sort(key=lambda r:(r['cohort'],r['candidate_id']));(OUT/'trace-index.json').write_text(json.dumps(results,indent=2)+'\n')
manifest.update(completed_at=now(),status='validated' if all(r['status']=='verified' for r in results) else 'failed',statuses=dict(Counter(r['status'] for r in results)),trace_index_sha256=sha(OUT/'trace-index.json'))
(OUT/'completion.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
if manifest['status']!='validated':raise SystemExit(1)
