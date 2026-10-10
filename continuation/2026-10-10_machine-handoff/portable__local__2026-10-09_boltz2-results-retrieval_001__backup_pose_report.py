from pathlib import Path
import datetime,hashlib,json,zipfile
ROOT=Path.cwd();BASE=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs'
RUN=BASE/'2026-10-09_boltz2-pose-conservation_007';REPAIR=BASE/'2026-10-09_whole-tm-adapter-repair_001'
RANK=RUN/'04_analysis/2026-10-09_local-pose-ranking_001';REPORT=RUN/'04_analysis/2026-10-09_pose-conservation-slides_001'
OUT=ROOT/'local/2026-10-09_boltz2-results-retrieval_001/backups';OUT.mkdir(exist_ok=True)
files=set()
def add(p):
    if p.is_file():files.add(p)
    elif p.is_dir():files.update(f for f in p.rglob('*') if f.is_file() and '__pycache__' not in str(f))
    else:raise FileNotFoundError(p)
for p in [ROOT/'registry',RUN/'run.json',RUN/'01_staging',RANK,RUN/'04_analysis/2026-10-09_selected-pose-native-copies_001',RUN/'04_analysis/2026-10-09_pose-execution-evidence_001',REPAIR/'run.json',REPAIR/'01_staging',REPAIR/'04_analysis/2026-10-09_canonical-whole-tm-pilot_001',REPAIR/'04_analysis/2026-10-09_corrected-report-pilot_001',REPAIR/'04_analysis/2026-10-09_canonical-execution-evidence_001',REPORT/'renders_002',REPORT/'build-v4',REPORT/'manifest-v4.json',REPORT/'2026-10-09_review_v4.json',REPORT/'2026-10-09_METHODS_v2.md',REPORT/'outputs/2026-10-09_TNFA_Boltz2_top5_IPSAE_pose_TM_available_pairs_v2.pptx',ROOT/'docs/2026-10-06_TNFA_COLORS.md',ROOT/'workflow.lock.json',ROOT/'scripts/tnfa_boltz2_rank.py',ROOT/'scripts/tnfa_boltz2_render.py']:add(p)
for p in REPORT.glob('*camera*.json'):add(p)
for n in ['metrics.jsonl.gz','runtime.json','completion.json','whole-complex-diagnostic-warning.json']:add(RUN/'04_analysis/2026-10-09_all-available-pose-metrics_001'/n)
add(ROOT/'drafts/04_analysis/2026-10-08_tnfa-four-hotspot-views_001')
add(ROOT/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001/trace-index.json')
add(ROOT/'drafts/04_analysis/2026-10-09_boltz2-candidate-traces_001/completion.json')
for p in (REPAIR/'04_analysis/2026-10-09_corrected-report-pilot_001/observation-inputs').glob('*_trace.json'):
    c=json.loads(p.read_text())['candidate'];origin=c['origin'];base=ROOT/'campaigns'/origin['campaign_id']/'runs'/origin['run_id'];add(base/'run.json')
    def source(v):
        p=base/v['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'];add(p)
    source(origin);g=c['generation'];source(g['parameters']['native_specification_artifact']);source(g['sequence_extraction']['coordinate_artifact']);source(g['execution_receipt'])
    for v in g['input_artifacts']:source(v)
manifest=[]
for p in sorted(files):manifest.append({'path':str(p.relative_to(ROOT)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();zp=OUT/'2026-10-09_pose-report-evidence_001.zip'
with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for entry in manifest:
        p=ROOT/entry['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'];z.write(p,entry['path'])
    z.writestr('2026-10-09_backup-manifest.json',json.dumps({'created_at':stamp,'files':manifest},indent=2)+'\n')
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
receipt={'created_at':stamp,'path':str(zp),'sha256':hashlib.sha256(zp.read_bytes()).hexdigest(),'file_count':len(files),'zip_crc_validation':'passed','scope':'Validated primary available-pair metrics, twenty corrected diagnostic observations, native source models, source generation artifacts, registry, camera/renders, final24slide report; full diagnostic13937supplement collected separately when complete.'}
(OUT/'2026-10-09_pose-report-evidence_001.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
