#!/usr/bin/env python3
"""Parent-linked human DD1 session with documented per-chain blue cartoons."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pymol2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(cmd, obj):
    model = cmd.get_model(obj)
    return ([tuple((a.chain, a.resi, a.resn, a.name, a.symbol, tuple(a.coord))) for a in model.atom],
            [(tuple(b.index), b.order) for b in model.bond])


def atom_colors(cmd, obj):
    values = []
    cmd.iterate(obj, 'values.append(color)', space={'values': values})
    return [cmd.get_color_tuple(x) for x in values]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parent', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    records = json.loads((root/'local/current_empire_dd1_deployment.json').read_text())['records']
    human = next(r for r in records if r['species'] == 'human')
    parent = args.parent.resolve()
    palette = {'A': '#174A78', 'B': '#397FB7', 'C': '#8BC6E8'}
    now = datetime.now(ZoneInfo('America/New_York'))
    out = root/'drafts/04_analysis'/ (now.strftime('%Y-%m-%d_%H%M%S%z')+'_human-tnfa-chain-blues_001')
    out.mkdir(exist_ok=False)
    path = out/(now.strftime('%Y-%m-%d')+'_human_TNFa_DD1_chain_blues_hotspots.pse')
    with pymol2.PyMOL() as pm:
        c = pm.cmd
        c.load(str(parent))
        objects = c.get_names('objects')
        before = {obj: identity(c, obj) for obj in objects}
        scenes = list(c.get_scene_list())
        original_colors = {}
        original_sticks = {}
        for scene in scenes:
            c.scene(scene, 'recall', animate=0)
            original_colors[scene] = {obj: atom_colors(c, obj) for obj in objects}
            original_sticks[scene] = {obj: c.count_atoms(f'{obj} and rep sticks') for obj in objects}
            for chain, hexcolor in palette.items():
                c.set_color('human_blue_'+chain, [int(hexcolor[i:i+2],16)/255 for i in (1,3,5)])
            for obj in objects:
                for chain in 'ABC':
                    c.set('cartoon_color', 'human_blue_'+chain, f'{obj} and chain {chain}')
            c.set('animation', 0)
            c.set('scene_animation_duration', 0)
            c.scene(scene, 'store')
        c.scene('DD1_Charge_context', 'recall', animate=0)
        c.save(str(path))
        c.reinitialize()
        c.load(str(path))
        for scene in scenes:
            c.scene(scene, 'recall', animate=0)
            for obj in objects:
                assert identity(c, obj) == before[obj], obj
                assert atom_colors(c, obj) == original_colors[scene][obj], (scene, obj)
                assert c.count_atoms(f'{obj} and rep sticks') == original_sticks[scene][obj]
                colors = []
                c.iterate(obj, 'colors.append((chain,s.cartoon_color))', space={'colors': colors})
                assert all(c.get_color_tuple(x) == c.get_color_tuple('human_blue_'+chain) for chain,x in colors), (scene, obj)
            assert c.count_atoms('DD1_Hotspots and rep sticks') == 43
        c.scene('DD1_Charge_context', 'recall', animate=0)
        view = c.get_view()
        c.orient('Human_TNFa_1TNF')
        c.zoom('Human_TNFa_1TNF', 2)
        assert c.get_view() == view
        c.png(str(out/'human_skyblue_preview.png'), 1000, 800, ray=1)
    shutil.copy2(__file__, out/'generator.py')
    receipt = {
        'created_at': now.isoformat(), 'parent_run': human['run_id'],
        'parent_PSE': str(parent), 'parent_PSE_sha256': sha(parent),
        'PSE': str(path), 'PSE_sha256': sha(path),
        'cartoon_palette': palette,
        'hotspots_author': human['hotspots_author'], 'hotspots': 'green sticks',
        'all_atom_colors_stick_visibility_identities_coordinates_and_bonds_preserved': True,
        'all_scenes_reopened_verified': scenes,
        'request': 'Restore documented distinct human blue chain shades; mouse retains copper/amber/sand.',
        'compute_inputs_changed': False, 'generator_sha256': sha(out/'generator.py'),
    }
    (out/'validation.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (out/'README.md').write_text(
        '# Human TNFa DD1 — distinct blue chain cartoons\n\n'
        f'Created {now.isoformat()}. Parent: `{human["run_id"]}`.\n\n'
        f'Open `{path.name}`. Human A navy `#174A78`, B blue `#397FB7`, C light blue `#8BC6E8`. '
        'The five current whole-residue green hotspot sticks, positive red, negative blue, '
        'histidine magenta, atom colors and scene-specific stick visibility are preserved. '
        'The default scene is `DD1_Charge_context`; hotspot, labeled and close-up scenes remain available.\n\n'
        'Each scene was verified after reopening: cartoon colors, atom colors, stick visibility, '
        'atom identities, coordinates and bonds. Parent PSEs and frozen Foundry bundles are unchanged. '
        'This snapshot follows the October 7 clarification that chain colors must remain distinct. '
        'The uniform sky-blue snapshot is superseded and preserved. Mouse copper/amber/sand is unchanged.\n'
    )
    for file in out.iterdir():
        file.chmod(0o444)
    out.chmod(0o555)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
