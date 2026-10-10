#!/usr/bin/env python3
"""Render paired Boltz2 models in a recorded, shared PyMOL camera.

Native files are read-only. Equivalent trimer copies are assigned display slots
by a proper rigid fit, then the intended pocket breaks near-symmetry ambiguity.
Every fit, copy assignment, source hash and annotation is retained for review.
"""
import argparse,datetime,hashlib,itertools,json
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pymol2

VERSION='2026-10-09_v1'
PALETTES={'human':['#174A78','#397FB7','#8BC6E8'],'mouse':['#85451F','#C67B35','#EAC18B']}
BINDER='#555C64'
AA=dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(),'ARNDCQEGHILKMFPSTWYV'))

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def ca_atoms(c,sel):
 m=c.get_model(sel+' and name CA');coords=c.get_coords(sel+' and name CA')
 assert m.atom and len(m.atom)==len(coords)
 return m.atom,np.asarray(coords,dtype=float)

def fit(x,y):
 a=x.mean(0);b=y.mean(0);u,_,v=np.linalg.svd((x-a).T@(y-b))
 d=np.eye(3);d[2,2]=np.sign(np.linalg.det(u@v));rotation=u@d@v
 translation=b-a@rotation;rmsd=float(np.sqrt(np.mean(np.sum((x@rotation+translation-y)**2,axis=1))))
 matrix=np.eye(4);matrix[:3,:3]=rotation.T;matrix[:3,3]=translation
 assert np.linalg.det(rotation)>0.999999 and np.allclose(rotation.T@rotation,np.eye(3),atol=1e-7)
 return rotation,translation,matrix,rmsd

def render(c,row,species,camera,reference_models,out,width,height):
 source=row[species]['native_structure'];path=Path(source['path'])
 assert sha(path)==source['sha256']
 c.reinitialize();reference=reference_models[species]
 refname=species.title()+'_TNFa_Original_hotspots';c.load_model(reference,refname)
 c.load(str(path),'prediction');assert set(c.get_chains('prediction'))==set('ABCD')
 native={};ref={};maps={}
 for ch in 'ABC':
  aa,coords=ca_atoms(c,'prediction and chain '+ch);ra,rc=ca_atoms(c,refname+' and chain '+ch)
  assert ''.join(AA[a.resn] for a in aa)==''.join(AA[a.resn] for a in ra)
  assert [a.resi for a in aa]==[str(n) for n in range(1,len(aa)+1)]
  native[ch]=coords;ref[ch]=rc;maps[ch]={a.resi:ra[i].resi for i,a in enumerate(aa)}
 ba,bc=ca_atoms(c,'prediction and chain D');assert ''.join(AA[a.resn] for a in ba)==row['sequence']
 origin_species=row['cohort'].split('-')[-1];revision=row['cohort'].split('-')[0]
 origin_source=next(s for s in camera['sources'] if s['species']==origin_species and s['revision']==revision)
 origin_ref=reference_models[origin_species];origin_name='origin_reference';c.load_model(origin_ref,origin_name)
 hot=origin_name+' and name CA and ('+' or '.join('(chain '+ch+' and resi '+str(n)+')' for ch,n,_ in origin_source['hotspots'])+')'
 hc=c.get_coords(hot);assert hc is not None and len(hc)==len(origin_source['hotspots']);pocket=hc.mean(0)
 x=np.vstack([native[ch] for ch in 'ABC']);options=[]
 for perm in itertools.permutations('ABC'):
  y=np.vstack([ref[ch] for ch in perm]);rotation,translation,matrix,rmsd=fit(x,y)
  distance=float(np.linalg.norm((bc@rotation+translation).mean(0)-pocket))
  options.append({'native_to_display':dict(zip('ABC',perm)),'target_ca_rmsd_angstrom':rmsd,'binder_center_to_origin_hotspot_center_angstrom':distance,'rotation':rotation,'translation':translation,'matrix':matrix})
 minimum=min(o['target_ca_rmsd_angstrom'] for o in options)
 # Only near-equivalent target fits compete on pocket proximity. This changes
 # display assignment, never coordinates relative to the binder or any score.
 eligible=[o for o in options if o['target_ca_rmsd_angstrom']<=minimum+0.1]
 chosen=min(eligible,key=lambda o:(o['binder_center_to_origin_hotspot_center_angstrom'],o['target_ca_rmsd_angstrom'],''.join(o['native_to_display'].values())))
 before=c.get_coords('prediction').copy();c.transform_object('prediction',chosen['matrix'].ravel().tolist())
 assert np.allclose(c.get_coords('prediction'),before@chosen['rotation']+chosen['translation'],atol=2e-5)
 c.hide('everything','all');c.disable(refname);c.disable(origin_name);c.enable('prediction');c.show('cartoon','prediction')
 for native_chain,slot in chosen['native_to_display'].items():
  color=species+'_'+slot;value=PALETTES[species]['ABC'.index(slot)]
  c.set_color(color,[int(value[i:i+2],16)/255 for i in (1,3,5)])
  sel='prediction and chain '+native_chain;c.color(color,sel);c.set('cartoon_color',color,sel)
 c.set_color('binder',[int(BINDER[i:i+2],16)/255 for i in (1,3,5)])
 c.color('binder','prediction and chain D');c.set('cartoon_color','binder','prediction and chain D')
 for resn,color in [('ARG+LYS','red'),('ASP+GLU','blue'),('HIS','magenta')]:
  sel='prediction and chain A+B+C and resn '+resn;c.show('sticks',sel);c.color(color,sel)
 annotations=next(s for s in camera['sources'] if s['species']==species and s['revision']==revision)
 inverse={slot:ch for ch,slot in chosen['native_to_display'].items()};hotspot_records=[]
 for slot,author,resn in annotations['hotspots']:
  ch=inverse[slot];position=next(n for n,a in maps[ch].items() if a==str(author))
  sel='prediction and chain '+ch+' and resi '+position
  assert {(a.resn,a.resi) for a in c.get_model(sel+' and name CA').atom}=={(resn,position)}
  c.show('sticks',sel);c.color('green',sel)
  hotspot_records.append({'native_chain':ch,'display_copy':slot,'construct_residue':int(position),'reference_author_residue':author,'resn':resn})
 c.bg_color('white');c.set('grid_mode',0);c.set('orthoscopic',1);c.set('ray_opaque_background',1)
 c.set('antialias',2);c.set('depth_cue',0);c.set('specular',0.2);c.set('stick_radius',0.16)
 c.set('ray_shadows',0);c.deselect();c.set_view(camera['view'])
 stem=row['candidate_id']+'__'+species
 c.save(str(out/(stem+'.pse')))
 c.png(str(out/(stem+'.png')),width=width,height=height,dpi=200,ray=1,quiet=1)
 candidates=[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in o.items()} for o in options]
 result={'candidate_id':row['candidate_id'],'species':species,'cohort':row['cohort'],'source':source,'sequence_sha256':hashlib.sha256(row['sequence'].encode()).hexdigest(),'reference_object':refname,'alignment_method':'Proper Kabsch fit using all ordered CA atoms of each exact-sequence target chain. Enumerate six equivalent homotrimer copy assignments. Among fits within 0.1 A of minimum target RMSD, choose binder center closest to recorded origin hotspot center; deterministic RMSD/lexical ties.','symmetry_fit_tolerance_angstrom':0.1,'chosen':{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in chosen.items()},'fit_candidates':candidates,'native_to_reference_author_numbering':maps,'hotspots':hotspot_records,'hotspot_scope':'Corresponding species/revision reference pocket; annotations are display-only, not Boltz restraints.','colors':{'target_display_copies':dict(zip('ABC',PALETTES[species])),'binder_D':BINDER,'ARG_LYS':'red','ASP_GLU':'blue','HIS':'magenta','reference_hotspots':'green'},'cartoon_and_atom_colors_independent':True,'omitted_display_components':'Reference objects disabled; native four-chain model complete; hydrogens not added.','camera':list(c.get_view()),'render_width':width,'render_height':height,'pymol_version':c.get_version()[0],'png_sha256':sha(out/(stem+'.png')),'pse_sha256':sha(out/(stem+'.pse'))}
 (out/(stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--records',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--camera',type=Path,default=Path(__file__).resolve().parents[1]/'drafts/04_analysis/2026-10-08_tnfa-four-hotspot-views_001/initial-view.json')
 p.add_argument('--reference-pse',type=Path);p.add_argument('--width',type=int,default=1600);p.add_argument('--height',type=int,default=1200);a=p.parse_args()
 camera=json.loads(a.camera.read_text());pse=a.reference_pse or a.camera.parent/'2026-10-08_TNFa_four_hotspot_selections.pse'
 rows=json.loads(a.records.read_text());assert isinstance(rows,list) and rows
 a.output.mkdir(parents=True,exist_ok=False)
 results=[]
 with pymol2.PyMOL() as pm:
  c=pm.cmd;c.load(str(pse));refs={}
  # get_model does not fold in an object transform consistently across PyMOL
  # versions; explicitly store get_coords (transformed display coordinates).
  for species in ['human','mouse']:
   name=species.title()+'_TNFa_Original_hotspots';m=c.get_model(name);coords=c.get_coords(name);assert len(m.atom)==len(coords)
   for atom,coord in zip(m.atom,coords):atom.coord=coord.tolist()
   refs[species]=m
  for row in rows:
   for species in ['human','mouse']:
    results.append(render(c,row,species,camera,refs,a.output,a.width,a.height));print(row['candidate_id'],species,results[-1]['chosen']['target_ca_rmsd_angstrom'],flush=True)
 manifest={'created_at':datetime.datetime.now(ZoneInfo('America/New_York')).isoformat(),'version':VERSION,'script_sha256':sha(Path(__file__)),'source_records':{'path':str(a.records.resolve()),'sha256':sha(a.records)},'camera_source':{'path':str(a.camera.resolve()),'sha256':sha(a.camera)},'reference_pse':{'path':str(pse.resolve()),'sha256':sha(pse)},'render_count':len(results),'shared_camera':camera['view'],'render_records':[r['candidate_id']+'__'+r['species']+'.json' for r in results],'scientific_coordinates_preserved':True,'rank_claim':'Input records determine selection; this renderer does not rank or establish binding.'}
 (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
