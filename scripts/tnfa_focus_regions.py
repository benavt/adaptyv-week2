#!/usr/bin/env python3
"""Create independently toggleable TNFA focus regions from an existing palette PSE."""
import argparse,csv,hashlib,json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROFILES={
 'human':{'object':'Human_TNFa_1TNF','ranges':[(65,75),(99,114)]},
 'mouse':{'object':'Mouse_TNFa_2TNF','ranges':[(62,74),(99,116)]},
}
CLASSES={'positive':('ARG+LYS','red'),'negative':('ASP+GLU','blue'),'histidine':('HIS','magenta')}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atoms(model):return [(a.chain,a.resi,a.resn,a.name,a.symbol,a.alt,a.hetatm,tuple(round(v,4) for v in a.coord)) for a in model.atom]
def apply(cmd,species):
 """Modify the loaded reference object; return source/region identities and scene names."""
 profile=PROFILES[species];parent=profile['object']
 assert parent in cmd.get_names('objects'),parent
 assert cmd.count_states(parent)==1
 assert sorted(cmd.get_chains(f'{parent} and polymer.protein'))==['A','B','C']
 cmd.scene('*','clear');cmd.deselect()
 # Project convention supersedes the common HIS-purple default; focus sticks override elements.
 cmd.color('magenta',f'{parent} and resn HIS and elem C')
 cmd.hide('sticks',f'{parent} and polymer.protein')
 originals=atoms(cmd.get_model(parent));view=cmd.get_view();regions=[]
 prefix='Human' if species=='human' else 'Mouse'
 for chain in 'ABC':
  members=[]
  for lo,hi in profile['ranges']:
   selection=f'{parent} and polymer.protein and chain {chain} and resi {lo}-{hi}'
   model=cmd.get_model(selection);assert model.atom,selection
   name=f'{prefix}_TNFa_{chain}_{lo}_{hi}';assert name not in cmd.get_names('all')
   cmd.load_model(model,name)
   copy_color=f"{species}_copy_{ord(chain)-ord('A')+1}"
   cmd.color(copy_color,name);cmd.set('cartoon_color',copy_color,name)
   assert atoms(cmd.get_model(name))==atoms(model),name
   cmd.hide('everything',name);cmd.set('stick_radius',0.22,name)
   inventory=[]
   for kind,(resnames,color) in CLASSES.items():
    selected=f'{name} and resn {resnames}'
    cmd.show('sticks',selected);cmd.color(color,selected)
    ca=cmd.get_model(selected+' and name CA')
    inventory.extend({'residue':a.resi,'resname':a.resn,'class':kind,'color':color} for a in ca.atom)
   residues=sorted({a.resi for a in model.atom},key=lambda x:int(x.rstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ')))
   regions.append({'name':name,'chain':chain,'range':[lo,hi],'atoms':len(model.atom),'residues':residues,'absent_author_numbers':[n for n in range(lo,hi+1) if str(n) not in residues],'highlighted_residues':inventory})
   members.append(name)
  cmd.group(f'{prefix}_focus_chain_{chain}',' '.join(members))
 cmd.set('label_color','black');cmd.set('label_size',14)
 cmd.set_view(view);cmd.deselect();cmd.scene('Overview','store')
 cmd.disable(parent)
 for r in regions:cmd.show('cartoon',r['name'])
 cmd.scene('Regions_only','store')
 cmd.scene('Overview','recall')
 for chain in 'ABC':
  for r in regions:
   (cmd.enable if r['chain']==chain else cmd.disable)(r['name'])
  cmd.hide('cartoon',parent);cmd.show('cartoon',f'{parent} and chain {chain}')
  cmd.scene(f'Chain_{chain}','store')
 cmd.scene('Overview','recall')
 for r in regions:
  cmd.label(f"{r['name']} and resn ARG+LYS+ASP+GLU+HIS and name CA",'resn + resi')
 cmd.scene('Residue_labels','store');cmd.hide('labels','all');cmd.scene('Overview','recall');cmd.deselect()
 assert atoms(cmd.get_model(parent))==originals
 return {'source_object':parent,'source_atoms':len(originals),'regions':regions,'scenes':list(cmd.get_scene_list()),'camera':list(view)}
def verify(cmd,record):
 assert cmd.count_atoms(record['source_object'])==record['source_atoms']
 for r in record['regions']:
  name=r['name'];assert cmd.count_states(name)==1;assert cmd.count_atoms(name)==r['atoms']
  lo,hi=r['range'];source=f"{record['source_object']} and polymer.protein and chain {r['chain']} and resi {lo}-{hi}"
  assert atoms(cmd.get_model(name))==atoms(cmd.get_model(source))
  for kind,(resnames,color) in CLASSES.items():
   selected=f'{name} and resn {resnames}';model=cmd.get_model(selected)
   indices=[];cmd.iterate(selected,'indices.append(color)',space={'indices':indices})
   assert all(cmd.get_color_tuple(i)==cmd.get_color_tuple(color) for i in indices)
   assert cmd.count_atoms(f'({selected}) and rep sticks')==len(model.atom),f'Sticks absent in {name}: {kind}'
 assert cmd.get_scene_list()==record['scenes']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--human',type=Path,required=True);p.add_argument('--mouse',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--prior-attempt',type=Path)
 a=p.parse_args();out=a.output_dir.resolve();assert not out.exists(),'Create a new immutable snapshot directory.'
 for f in [a.human,a.mouse]:assert f.is_file(),f
 out.mkdir(parents=True)
 date=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
 inputs={'created_at':datetime.now(ZoneInfo('America/New_York')).isoformat(),'predecessor':'2026-10-06_tnfa-species-colors_001','sources':[{'species':s,'path':str(f.resolve()),'sha256':sha(f)} for s,f in [('human',a.human),('mouse',a.mouse)]],'generator_sha256':sha(Path(__file__)),'settings':{'ranges':{k:v['ranges'] for k,v in PROFILES.items()},'chains':['A','B','C'],'numbering':'Deposited author residue IDs; inclusive endpoints; no renumbering.','charged_residue_colors':{'ARG/LYS':'red','ASP/GLU':'blue','HIS':'magenta'},'scope':'Stick representation for entire ARG/LYS/ASP/GLU/HIS residues within focus regions only; uniform residue colors override standard element colors in these focus objects.','cartoons':'Retain species/copy cartoon colors, independently of atom colors.','histidine':'Separate visualization class; not a protonation assignment.','hotspots':'Inspection regions, not validated binder-design hotspot selections.'}}
 if a.prior_attempt:
  inputs['prior_attempt']={'path':str(a.prior_attempt.resolve()),'inputs_sha256':sha(a.prior_attempt/'inputs.json')}
 (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
 import pymol2
 records=[];rows=[]
 with pymol2.PyMOL() as pymol:
  cmd=pymol.cmd
  for species,source in [('human',a.human),('mouse',a.mouse)]:
   cmd.reinitialize();cmd.load(str(source.resolve()));record=apply(cmd,species);verify(cmd,record)
   record['species']=species;record['pymol_version']=cmd.get_version()
   session=out/f'{date}_{species}_TNFa_focus_regions.pse';cmd.save(str(session))
   cmd.set('ray_opaque_background',1);cmd.png(str(out/f'{date}_{species}_TNFa_focus_regions.png'),width=1200,height=900,ray=1,quiet=1)
   cmd.reinitialize();cmd.load(str(session));verify(cmd,record)
   record['output']={'path':session.name,'sha256':sha(session),'reopened_verified':True};records.append(record)
   rows.append(f'| {species.capitalize()} | [Open session]({session.name}) | 6 |')
   print(species,'six region objects verified and saved',flush=True)
 (out/'generation.json').write_text(json.dumps({'completed_at':datetime.now(ZoneInfo('America/New_York')).isoformat(),'records':records},indent=2)+'\n')
 with (out/'highlighted-residues.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['species','chain','object','author_residue','resname','class','color'])
  for rec in records:
   for r in rec['regions']:
    for item in r['highlighted_residues']:w.writerow([rec['species'],r['chain'],r['name'],item['residue'],item['resname'],item['class'],item['color']])
 (out/'README.md').write_text('# TNFA focus regions — '+date+'\n\nSuccessor to the species-color preview. Original sessions and coordinates remain intact.\n\n| Species | Session | Region objects |\n| --- | --- | --- |\n'+'\n'.join(rows)+'\n\nHuman ranges: **65–75** and **99–114**. Mouse ranges: **62–74** and **99–116**, inclusive, using deposited author numbering in chains A/B/C. Each chain has its own two objects, grouped in the PyMOL object panel.\n\nARG/LYS are red sticks; ASP/GLU are blue sticks; HIS is magenta sticks. Entire highlighted residues are uniformly colored. Neutral focus residues remain in the region objects and inherit their species/copy cartoon colors. The complete trimer supplies cartoon context.\n\nScenes: Overview (default), Regions_only, Chain_A, Chain_B, Chain_C, Residue_labels. Toggle individual region objects using their names; use Residue_labels to see residue identities. Mouse author numbering jumps from 72 to 74; no author residue 73 is invented. Mouse focus ranges contain no HIS, so no magenta histidine sticks appear.\n\ninputs.json and generation.json record source hashes, settings, object inventories, coordinates and reopening checks. highlighted-residues.csv lists every highlighted residue. These are visual inspection regions, not a binder hotspot or protonation assignment.\n')
if __name__=='__main__':main()
