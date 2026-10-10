#!/usr/bin/env python3
"""Save a parent-linked mouse DD1 view with consistent colors in every scene."""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pymol2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def molecular_identity(cmd, name):
    model = cmd.get_model(name)
    return {
        "atoms": [(a.chain, a.resi, a.resn, a.name, a.symbol, tuple(a.coord)) for a in model.atom],
        "bonds": [(tuple(b.index), b.order) for b in model.bond],
    }


def main():
    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / 'local/current_empire_dd1_deployment.json').read_text())
    mouse = next(r for r in record['records'] if r['species'] == 'mouse')
    parent = Path(mouse['PSE'])
    now = datetime.now(ZoneInfo('America/New_York'))
    label = now.strftime('%Y-%m-%d_%H%M%S%z') + '_mouse-tnfa-hotspot-colors_001'
    out = root / 'drafts/04_analysis' / label
    out.mkdir(exist_ok=False)
    session = out / (now.strftime('%Y-%m-%d') + '_mouse_TNFa_DD1_hotspots.pse')
    palette = {'A': '#85451F', 'B': '#C67B35', 'C': '#EAC18B'}
    obj = 'Mouse_TNFa_2TNF'
    hot = ' or '.join(f'(chain {ch} and resi {n})' for ch, n, _ in mouse['hotspots_author'])
    with pymol2.PyMOL() as pm:
        cmd = pm.cmd
        cmd.load(str(parent))
        names = cmd.get_names('objects')
        identities = {name: molecular_identity(cmd, name) for name in names}
        scenes = list(cmd.get_scene_list())

        def apply_colors():
            cmd.set('animation', 0)
            cmd.set('scene_animation_duration', 0)
            for name in names:
                if name == 'DD1_Hotspots':
                    cmd.color('green', name)
                    cmd.hide('everything', name)
                    cmd.show('sticks', name)
                    cmd.enable(name)
                    continue
                for chain, hexcolor in palette.items():
                    cname = 'mouse_copy_' + str('ABC'.index(chain) + 1)
                    cmd.set_color(cname, [int(hexcolor[i:i+2], 16)/255 for i in (1, 3, 5)])
                    selection = f'{name} and chain {chain}'
                    cmd.color(cname, selection)
                    cmd.set('cartoon_color', cname, selection)
                for residues, color in [('ARG+LYS', 'red'), ('ASP+GLU', 'blue'), ('HIS', 'magenta')]:
                    selection = f'{name} and resn {residues}'
                    cmd.color(color, selection)
                    cmd.show('sticks', selection)
                selection = f'{name} and ({hot})'
                cmd.color('green', selection)
                # One annotation object supplies hotspot sticks without overlap.
                cmd.hide('sticks', selection)
            cmd.show('cartoon', obj)
            cmd.enable(obj)
            cmd.disable('DD1_Pocket')
            cmd.deselect()

        def verify():
            for name in names:
                assert molecular_identity(cmd, name) == identities[name], name
                rows = []
                cmd.iterate(name, 'rows.append((chain,resi,resn,color,s.cartoon_color))', space={'rows': rows})
                for chain, resi, resn, color, cartoon in rows:
                    if name == 'DD1_Hotspots' or (chain, int(resi)) in hotspot_keys:
                        expected = cmd.get_color_tuple('green')
                    elif resn in ('ARG', 'LYS'):
                        expected = cmd.get_color_tuple('red')
                    elif resn in ('ASP', 'GLU'):
                        expected = cmd.get_color_tuple('blue')
                    elif resn == 'HIS':
                        expected = cmd.get_color_tuple('magenta')
                    else:
                        expected = cmd.get_color_tuple('mouse_copy_' + str('ABC'.index(chain)+1))
                    assert cmd.get_color_tuple(color) == expected, (name, chain, resi, resn)
                    if name != 'DD1_Hotspots':
                        assert cmd.get_color_tuple(cartoon) == cmd.get_color_tuple('mouse_copy_' + str('ABC'.index(chain)+1))
            charged = f'{obj} and resn ARG+LYS+ASP+GLU+HIS and not ({hot})'
            assert cmd.count_atoms(charged) == cmd.count_atoms(f'({charged}) and rep sticks')
            assert cmd.count_atoms('DD1_Hotspots') == cmd.count_atoms('DD1_Hotspots and rep sticks') == 43
            return cmd.count_atoms(charged)

        hotspot_keys = {(ch, n) for ch, n, _ in mouse['hotspots_author']}
        for scene in scenes:
            cmd.scene(scene, 'recall', animate=0)
            apply_colors()
            verify()
            cmd.scene(scene, 'store')
        cmd.scene('DD1_Charge_context', 'recall', animate=0)
        cmd.save(str(session))
        cmd.reinitialize()
        cmd.load(str(session))
        counts = {}
        for scene in scenes:
            cmd.scene(scene, 'recall', animate=0)
            counts[scene] = verify()
        cmd.scene('DD1_Charge_context', 'recall', animate=0)
        # Materialize the camera for headless rendering after session restore.
        # These commands reproduce the saved overview without changing it.
        overview = cmd.get_view()
        cmd.orient(obj)
        cmd.zoom(obj, 2)
        assert cmd.get_view() == overview
        cmd.png(str(out / 'mouse_hotspots_preview.png'), 1000, 800, ray=1)
    shutil.copy2(__file__, out / 'generator.py')
    report = {
        'created_at': now.isoformat(), 'parent_run': mouse['run_id'],
        'parent_PSE': str(parent), 'parent_PSE_sha256': digest(parent),
        'PSE': str(session), 'PSE_sha256': digest(session),
        'generator_sha256': digest(out / 'generator.py'),
        'hotspots_author': mouse['hotspots_author'], 'palette': palette,
        'whole_residue_colors': {'ARG/LYS': 'red', 'ASP/GLU': 'blue', 'HIS': 'magenta', 'hotspots': 'green'},
        'green_stick_atoms': 43, 'nonhotspot_charge_stick_atoms_by_scene': counts,
        'all_scenes_reopened_verified': True, 'atom_identities_coordinates_and_bonds_unchanged': True,
        'change': 'Restore full charged/HIS sticks and reapply colors in every stored scene.',
        'compute_inputs_changed': False,
    }
    (out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'README.md').write_text(
        '# Mouse TNFa DD1 hotspot color correction\n\n'
        f"Created {now.isoformat()}; parent run `{mouse['run_id']}`.\n\n"
        f'Open `{session.name}`. All four stored scenes use A copper, B amber, C sand cartoons; '
        'whole-residue ARG/LYS red, ASP/GLU blue, HIS magenta sticks, and the five selected hotspots green. '
        'Green overrides residue-class colors. Hotspots: A Asp71/Asp104; B Glu107/Glu110/Lys112. '
        'The default scene is `DD1_Charge_context`. The labeled and close-up scenes retain full charge context.\n\n'
        'Every saved scene was recalled after reopening and checked for atom colors, per-chain cartoon colors, '
        'stick visibility and unchanged atom identities, coordinates and bonds. '
        'The prior PSE and immutable Foundry upload bundles remain preserved. '
        'This display-only correction does not change scientific inputs.\n'
    )
    for file in out.iterdir():
        if file.is_file():
            file.chmod(0o444)
    out.chmod(0o555)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
