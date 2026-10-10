from pathlib import Path
import gzip,json,hashlib,shutil,datetime
P=Path(__file__).resolve().parent;RUN=P.parents[1];S=json.loads((P/'settings.json').read_text());source=RUN.parent/S['source_run']/S['source_path'];out=RUN/'04_analysis/2026-10-10_score-transfer_002';out.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
completion=json.loads((source/'completion.json').read_text());assert completion['status']=='validated' and completion['pair_count']==32488
files={}
for name in ['metrics.jsonl','runtime.json']:
 expected=S['metrics_sha256' if name=='metrics.jsonl' else 'runtime_sha256'];assert sha(source/name)==expected
 target=out/(name+'.gz')
 with (source/name).open('rb') as src,target.open('xb') as dst,gzip.GzipFile(filename='',mode='wb',fileobj=dst,compresslevel=3,mtime=0) as gz:shutil.copyfileobj(src,gz)
 files[target.name]={'compressed_sha256':sha(target),'uncompressed_sha256':expected,'source':str(source/name),'size_bytes':target.stat().st_size}
shutil.copy2(source/'completion.json',out/'source-completion.json')
record={'status':'validated_lossless_transport','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files};(out/'transfer-validation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
