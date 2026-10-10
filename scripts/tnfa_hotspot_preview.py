#!/usr/bin/env python3
"""Render and verify one species' native-author-numbered DD1 hotspot PSE."""
import argparse,hashlib,json
from pathlib import Path
import pymol2

def identity(cmd,obj):
    return [(a.chain,a.resi,a.resn,a.name,tuple(a.coord)) for a in cmd.get_model(obj).atom]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('bundle',type=Path);args=parser.parse_args()
    root=args.bundle.resolve();s=json.loads((root/'settings.json').read_text());pdb=root/(s['source_pdb_id']+'_target.pdb')
    prefix='Human' if s['source_pdb_id']=='1TNF' else 'Mouse';obj=prefix+'_TNFa_'+s['source_pdb_id']
    colors=['#174A78','#397FB7','#8BC6E8'] if prefix=='Human' else ['#85451F','#C67B35','#EAC18B']
    out=root/'preview';out.mkdir(exist_ok=True);session=out/(s['run_id']+'_hotspots.pse')
    with pymol2.PyMOL() as pm:
        cmd=pm.cmd;cmd.load(str(pdb),obj);before=identity(cmd,obj)
        cmd.hide('everything','all');cmd.show('cartoon',obj);cmd.bg_color('white')
        for chain,color in zip('ABC',colors):
            name=prefix.lower()+'_copy_'+str(ord(chain)-ord('A')+1)
            cmd.set_color(name,[int(color[i:i+2],16)/255 for i in (1,3,5)])
            cmd.color(name,f'{obj} and chain {chain}');cmd.set('cartoon_color',name,f'{obj} and chain {chain}')
        for residues,color in [('ARG+LYS','red'),('ASP+GLU','blue'),('HIS','magenta')]:
            sel=f'{obj} and resn {residues}';cmd.show('sticks',sel);cmd.color(color,sel)
        hotspot_sel=' or '.join(f'(chain {ch} and resi {resi})' for ch,resi,_ in s['hotspots_author'])
        selection=f'{obj} and ({hotspot_sel})';cmd.create('DD1_Hotspots',selection)
        cmd.hide('everything','DD1_Hotspots');cmd.show('sticks','DD1_Hotspots');cmd.color('green','DD1_Hotspots')
        cmd.hide('sticks',selection);cmd.color('green',selection)
        cmd.create('DD1_Pocket',f'byres ({obj} within 6 of DD1_Hotspots)')
        cmd.disable('DD1_Pocket');cmd.set('stick_radius',0.22);cmd.set('label_color','black');cmd.set('label_size',16)
        cmd.orient(obj);cmd.zoom(obj,2);cmd.deselect();cmd.scene('DD1_Charge_context','store')
        cmd.hide('sticks',obj);cmd.scene('DD1_Hotspots','store')
        cmd.label('DD1_Hotspots and name CA','chain + ":" + resn + resi');cmd.scene('DD1_Labeled','store')
        cmd.zoom('DD1_Hotspots',8);cmd.scene('DD1_Pocket_closeup','store');cmd.scene('DD1_Charge_context','recall')
        assert identity(cmd,obj)==before
        expected=[(ch,str(n),rn) for ch,n,rn in s['hotspots_author']]
        actual=[(a.chain,a.resi,a.resn) for a in cmd.get_model('DD1_Hotspots and name CA').atom]
        assert sorted(actual)==sorted(expected),(actual,expected)
        assert cmd.count_atoms('DD1_Hotspots')==43
        assert cmd.count_atoms('DD1_Hotspots and rep sticks')==43
        indices=[];cmd.iterate('DD1_Hotspots','indices.append(color)',space={'indices':indices})
        assert all(cmd.get_color_tuple(i)==cmd.get_color_tuple('green') for i in indices)
        hotspot_atoms=identity(cmd,'DD1_Hotspots');cmd.save(str(session))
        cmd.reinitialize();cmd.load(str(session));assert identity(cmd,obj)==before;assert identity(cmd,'DD1_Hotspots')==hotspot_atoms
        report={'species':prefix.lower(),'run_id':s['run_id'],'hotspots_author':s['hotspots_author'],'hotspot_residues':5,'green_stick_atoms':43,'PSE_sha256':hashlib.sha256(session.read_bytes()).hexdigest(),'target_atoms':len(before),'target_coordinates_and_atom_identities_unchanged':True,'reopened_verified':True,'objects':cmd.get_names('objects'),'scenes':list(cmd.get_scene_list()),'numbering':'deposited author IDs','PSE':session.name}
        (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))

if __name__=='__main__':main()
