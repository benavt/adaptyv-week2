from pathlib import Path
import json,hashlib,zipfile,datetime
import numpy as np
import pymol2
root=Path.cwd();report=root/'campaigns/2026-10-07_tnfa-foundry-boltz2-migration/runs/2026-10-09_boltz2-pose-conservation_007/04_analysis/2026-10-09_pose-conservation-slides_001'
src=report/'renders_002';out=report/'2026-10-09_paired-pymol-deliverable_002';out.mkdir(exist_ok=False)
paired=out/'paired_sessions';paired.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
with pymol2.PyMOL() as pm:
 c=pm.cmd
 for hf in sorted(src.glob('*__human.pse')):
  cid=hf.name.removesuffix('__human.pse');mf=src/(cid+'__mouse.pse')
  c.reinitialize();c.load(str(hf));view=c.get_view();c.set_name('prediction','Human_complex')
  for name in c.get_names('objects'):
   if name!='Human_complex':c.delete(name)
  human=c.get_model('Human_complex');colors_h=[];c.iterate('Human_complex','colors_h.append(color)',space={'colors_h':colors_h});hc=c.get_coords('Human_complex').copy()
  c.load(str(mf),partial=1);c.set_name('prediction','Mouse_complex')
  for name in c.get_names('objects'):
   if name not in ['Human_complex','Mouse_complex']:c.delete(name)
  mouse=c.get_model('Mouse_complex');mc=c.get_coords('Mouse_complex').copy()
  assert np.allclose(hc,c.get_coords('Human_complex'))
  check_h=[];c.iterate('Human_complex','check_h.append(color)',space={'check_h':check_h});assert colors_h==check_h
  c.set('grid_mode',0);c.set_view(view);c.disable('all');c.enable('Human_complex');c.scene('Human','store')
  c.disable('all');c.enable('Mouse_complex');c.scene('Mouse','store')
  c.enable('Human_complex');c.scene('Overlay','store')
  c.scene('Human','recall');dest=paired/(cid+'__paired.pse');c.save(str(dest))
  c.reinitialize();c.load(str(dest));assert set(c.get_names('objects'))=={'Human_complex','Mouse_complex'}
  assert np.allclose(hc,c.get_coords('Human_complex')) and np.allclose(mc,c.get_coords('Mouse_complex'))
  assert np.allclose(view,c.get_view())
  for name,model in [('Human_complex',human),('Mouse_complex',mouse)]:
   loaded=c.get_model(name);assert len(loaded.atom)==len(model.atom)
   assert [(a.chain,a.resi,a.resn,a.name) for a in loaded.atom]==[(a.chain,a.resi,a.resn,a.name) for a in model.atom]
  rows.append({'candidate_id':cid,'paired_pse':dest.name,'paired_sha256':sha(dest),'human_source_sha256':sha(hf),'mouse_source_sha256':sha(mf),'atoms_human':len(human.atom),'atoms_mouse':len(mouse.atom),'reload_validation':'passed_coordinates_identities_colors_camera'})
  print(cid,flush=True)
manifest={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'design_count':len(rows),'original_session_count':40,'paired_session_count':20,'image_count':40,'objects':['Human_complex','Mouse_complex'],'scenes':['Human','Mouse','Overlay'],'default_scene':'Human','camera':'Exact final slide rendering camera; no additional alignment or atom changes','records':rows}
assert len(rows)==20
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'README.txt').write_text('TNF-alpha V2 PowerPoint accompanying PyMOL sessions\n\npaired_sessions/: one PSE per design, with Human_complex and Mouse_complex as separate objects. Both retain the exact display transforms, colors, cartoon/stick representations and camera used for the V2 slide images. Human is initially visible; choose the Human, Mouse or Overlay scene in PyMOL, or toggle objects directly. Overlay shows both aligned complexes superposed.\n\noriginal_sessions/: all 40 original per-species PSE files used to create slide images.\nimages/: all 40 exact PyMOL PNG panels embedded in the deck.\nrender_evidence/: source hashes, transforms, color and numbering records. Scatter plots are native editable PowerPoint charts, so they have no PSE source.\n\nRanking is provisional for three incomplete cohorts. Scores and selection are unchanged.\n')
archive=out/'2026-10-09_TNFA_V2_PyMOL_sessions_and_images.zip'
files=[]
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(paired.glob('*.pse')):z.write(p,'paired_sessions/'+p.name);files.append(p)
 for pattern,folder in [('*.pse','original_sessions'),('*.png','images'),('*.json','render_evidence')]:
  for p in sorted(src.glob(pattern)):z.write(p,folder+'/'+p.name);files.append(p)
 for p in [out/'manifest.json',out/'README.txt',report/'2026-10-09_shared-camera_002.json',report/'2026-10-09_METHODS_v2.md']:
  z.write(p,p.name);files.append(p)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
(out/'archive-receipt.json').write_text(json.dumps({'path':str(archive),'sha256':sha(archive),'file_count':len(files),'crc_validation':'passed','size_bytes':archive.stat().st_size},indent=2)+'\n')
print(archive)
