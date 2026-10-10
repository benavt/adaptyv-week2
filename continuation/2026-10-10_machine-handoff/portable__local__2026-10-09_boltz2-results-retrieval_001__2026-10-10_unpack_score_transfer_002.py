from pathlib import Path
import gzip,hashlib,shutil,json
B=Path('campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs');PACK=B/'2026-10-10_boltz2-score-transfer_002/04_analysis/2026-10-10_score-transfer_002';OUT=B/'2026-10-10_boltz2-completed-pose-metrics_003/04_analysis/2026-10-10_completed-pose-metrics_003'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
r=json.loads((PACK/'transfer-validation.json').read_text());assert r['status']=='validated_lossless_transport';completion=json.loads((PACK/'source-completion.json').read_text());assert completion['status']=='validated' and completion['pair_count']==32488;OUT.mkdir(exist_ok=True,parents=True)
if not (OUT/'completion.json').exists():(OUT/'completion.json').write_text(json.dumps(completion,indent=2)+'\n')
assert json.loads((OUT/'completion.json').read_text())==completion
for name,e in r['files'].items():
 source=PACK/name;assert sha(source)==e['compressed_sha256'];dest=OUT/name[:-3]
 if not dest.exists():
  with gzip.open(source,'rb') as f,dest.open('xb') as g:shutil.copyfileobj(f,g)
 assert sha(dest)==e['uncompressed_sha256']
print('Validated lossless collection of original metric and runtime hashes')
