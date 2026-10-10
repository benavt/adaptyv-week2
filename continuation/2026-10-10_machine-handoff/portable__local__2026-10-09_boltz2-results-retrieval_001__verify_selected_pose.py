from pathlib import Path
import importlib.util,itertools,json,numpy as np
from DockQ import DockQ as DQ
ROOT=Path.cwd();RUN=ROOT/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-pose-conservation_007';RANK=RUN/'04_analysis/2026-10-09_local-pose-ranking_001'
p=RUN/'01_staging/payload/score_pose.py';spec=importlib.util.spec_from_file_location('pose_method',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rows=json.loads((RANK/'selected.json').read_text());results=[]
for r in rows:
 h=DQ.load_PDB(r['human']['native_structure']['path']);m=DQ.load_PDB(r['mouse']['native_structure']['path']);hi,mi,hn,mn,_=mod.residue_mapping(mod.sequence(h['A']),mod.sequence(m['A']));n=len(r['sequence']);d0=max(.5,1.24*(n-15)**(1/3)-1.8) if n>15 else .5
 y=np.vstack([mod.ca(h[c])[hi] for c in 'ABC']);hb=mod.ca(h['D']);mb=mod.ca(m['D']);options=[]
 for order in itertools.permutations('ABC'):
  rot,trans,rms=mod.proper_fit(np.vstack([mod.ca(m[c])[mi] for c in order]),y);distance=np.linalg.norm(mb@rot+trans-hb,axis=1);options.append((float(np.mean(1/(1+(distance/d0)**2))),rms,order))
 minimum=min(o[1] for o in options);tm,rms,order=min([o for o in options if o[1]<=minimum+.1],key=lambda o:(-o[0],o[1],''.join(o[2])))
 hc=mod.collapse(h,'ABC',hn);mc=mod.collapse(m,''.join(order),mn);dh=DQ.run_on_chains(mc,hc,no_align=True,small_molecule=False);dm=DQ.run_on_chains(hc,mc,no_align=True,small_molecule=False);q=(dh['DockQ']+dm['DockQ'])/2 if dh is not None and dm is not None else None
 dt=abs(tm-r['pose']['binder_pose_tm_target_aligned']);dq=float(abs(q-r['pose']['dockq_symmetric'])) if q is not None else None;assert dt<2e-7;assert (q is None)==(r['pose']['dockq_symmetric'] is None);assert dq is None or dq<2e-6
 results.append({'candidate_id':r['candidate_id'],'binder_pose_tm_difference':dt,'compiled_local_vs_source_remote_DockQ_difference':dq})
(RANK/'local-pose-validation.json').write_text(json.dumps({'status':'passed','model_pairs':len(results),'comparisons':results},indent=2)+'\n');print(json.dumps({'pairs':len(results),'maximum_TM_difference':max(r['binder_pose_tm_difference'] for r in results),'maximum_DockQ_difference':max((r['compiled_local_vs_source_remote_DockQ_difference'] or 0) for r in results)},indent=2))
