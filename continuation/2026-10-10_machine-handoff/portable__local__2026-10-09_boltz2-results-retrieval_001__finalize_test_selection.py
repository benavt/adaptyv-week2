from pathlib import Path
import json,hashlib,runpy
import numpy as np
root=Path.cwd();run=root/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-four-cohort-test-deck_001';rank=run/'03_filtering/2026-10-09_local-available-pair-ranking_001';copy=run/'03_filtering/2026-10-09_selected-native-copies_001';rows=json.loads((rank/'winners-before-collection.json').read_text());manifest=json.loads((copy/'manifest-validated.json').read_text());method=runpy.run_path(str(root/'scripts/tnfa_boltz2_rank.py'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lookup={};comparisons=[]
for entry in manifest['files']:
 p=run/entry['copy'];assert p.is_file() and sha(p)==entry['sha256']
 if entry['kind']!='execution_evidence':lookup[(entry['candidate_id'],entry['species'],entry['kind'])]=p
for row in rows:
 cid=row['candidate_id'];trace=rank/(cid+'_trace.json');row['candidate_trace']={'path':str(trace),'sha256':sha(trace)}
 for species in ['human','mouse']:
  o=row[species];model=lookup[cid,species,'structure'];o['native_structure']['path']=str(model)
  for kind in ['pae','confidence','plddt']:o['artifact_sources'][kind]['path']=str(lookup[cid,species,kind])
  with np.load(lookup[cid,species,'pae'],allow_pickle=False) as x:
   target=152 if species=='human' else 148;values=method['binder_pair_scores'](x['pae'],target,len(row['sequence']))
  assert all(abs(values[ch]-o['ipsae_by_protomer'][ch])<1e-12 for ch in 'ABC')
  c=json.loads(lookup[cid,species,'confidence'].read_text());assert c['confidence_score']==o['confidence_score'] and c['ptm']==o['ptm'] and c['iptm']==o['complex_iptm']
  comparisons.append({'candidate_id':cid,'species':species,'ipsae_difference_local_vs_remote':max(abs(values[ch]-o['ipsae_by_protomer'][ch]) for ch in 'ABC'),'native_structure_sha256':sha(model)})
with (rank/'selected.json').open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
(rank/'local-score-validation.json').write_text(json.dumps({'comparisons':comparisons,'all_selected_native_files_hash_verified':True},indent=2)+'\n')
print(json.dumps({'selected':len(rows),'models':len(comparisons),'max_score_difference':max(c['ipsae_difference_local_vs_remote'] for c in comparisons),'binder_lengths':[len(r['sequence']) for r in rows]},indent=2))
