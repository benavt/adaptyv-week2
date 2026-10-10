#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, datetime as dt
import pymol2

ROOT = Path('CONFIGURED_ROOT/Code/projects/adaptyv-week2')
OUT = ROOT / 'drafts/04_analysis/2026-10-07_tnfa-heimdall-hotspot-picking_001'
HUMAN = ROOT / 'campaigns/2026-10-06_dd1-human-tnfa-pocket/Designs/2026-10-06_162135-0400-dd1-human-1tnf-ac-pocket-rfd3-50000-empire_001/1TNF_target.pdb'
MOUSE = ROOT / 'campaigns/2026-10-06_dd1-mouse-tnfa-pocket/Designs/2026-10-06_162135-0400-dd1-mouse-2tnf-ac-pocket-rfd3-50000-empire_001/2TNF_target.pdb'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

OUT.mkdir(parents=True, exist_ok=False)
metadata = {
    'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'purpose': 'Interactive selection of additional TNFa DD1 hotspots before an EmpireAI_Beta run',
    'sources': [
        {'species': 'human', 'pdb_id': '1TNF', 'path': str(HUMAN), 'sha256': sha(HUMAN)},
        {'species': 'mouse', 'pdb_id': '2TNF', 'path': str(MOUSE), 'sha256': sha(MOUSE)},
    ],
    'interaction': 'Click atoms/residues in PyMOL and record selected author chain/residue IDs; candidate selections are intentionally empty.',
    'color_conventions': {'ARG/LYS': 'red', 'ASP/GLU': 'blue', 'HIS': 'magenta', 'candidate_hotspots': 'green'},
    'numbering': 'Deposited author residue IDs; chains A/B/C; mouse author numbering skips 73.',
    'downstream': 'Selected hotspots must be reviewed and then frozen into a new Empire upload snapshot; no job is submitted by this session.',
}
(OUT/'inputs.json').write_text(json.dumps(metadata, indent=2) + '\n')

session = OUT / '2026-10-07_TNFa_hotspot_picking.pse'
with pymol2.PyMOL() as pm:
    cmd = pm.cmd
    cmd.reinitialize()
    cmd.set('opaque_background', 'on')
    cmd.set('bg_rgb', '[1,1,1]')
    for species, path, obj, base in [
        ('Human', HUMAN, 'Human_TNFa_1TNF', 'slate'),
        ('Mouse', MOUSE, 'Mouse_TNFa_2TNF', 'sand'),
    ]:
        cmd.load(str(path), obj)
        cmd.color(base, obj)
        cmd.show('cartoon', obj)
        cmd.hide('lines', obj)
        for chain, color in zip('ABC', ['marine', 'skyblue', 'blue'] if species == 'Human' else ['wheat', 'orange', 'sandybrown']):
            chain_obj = f'{obj}_{chain}'
            cmd.create(chain_obj, f'{obj} and chain {chain}')
            cmd.color(color, chain_obj)
            cmd.show('cartoon', chain_obj)
            cmd.disable(obj)
            cmd.select(f'{species}_candidate_hotspots', 'none')
            cmd.select(f'{species}_selected_hotspots', 'none')
        # Charge/HIS sticks are visible context for residue picking.
        charged = f'{obj} and (resn ARG+LYS+ASP+GLU+HIS)'
        cmd.show('sticks', charged)
        cmd.color('red', f'{obj} and resn ARG+LYS')
        cmd.color('blue', f'{obj} and resn ASP+GLU')
        cmd.color('magenta', f'{obj} and resn HIS')
    cmd.group('Human_TNFa_1TNF_chains', 'Human_TNFa_1TNF_A Human_TNFa_1TNF_B Human_TNFa_1TNF_C')
    cmd.group('Mouse_TNFa_2TNF_chains', 'Mouse_TNFa_2TNF_A Mouse_TNFa_2TNF_B Mouse_TNFa_2TNF_C')
    cmd.disable('Human_TNFa_1TNF'); cmd.disable('Mouse_TNFa_2TNF')
    cmd.enable('Human_TNFa_1TNF_chains'); cmd.enable('Mouse_TNFa_2TNF_chains')
    cmd.orient('Human_TNFa_1TNF_chains or Mouse_TNFa_2TNF_chains')
    cmd.zoom('Human_TNFa_1TNF_chains or Mouse_TNFa_2TNF_chains', 2)
    cmd.set('label_color', 'black')
    cmd.set('label_size', 16)
    cmd.label('Human_selected_hotspots or Mouse_selected_hotspots', 'chain + ":" + resn + resi')
    cmd.scene('Both_trim ers', 'store') if False else None
    cmd.scene('Human_only', 'store')
    cmd.disable('Mouse_TNFa_2TNF_chains')
    cmd.scene('Mouse_only', 'store')
    cmd.disable('Human_TNFa_1TNF_chains'); cmd.enable('Mouse_TNFa_2TNF_chains')
    cmd.scene('Both_trim ers', 'store') if False else None
    cmd.enable('Human_TNFa_1TNF_chains')
    cmd.scene('Both_trim ers', 'store') if False else None
    cmd.save(str(session))

(OUT/'README.md').write_text(f'''# TNFa hotspot-picking session

Open `{session.name}` in PyMOL. This is the interactive hotspot-picking session for the next EmpireAI_Beta DD1 input revision.

The session contains both complete trimers with chain-specific objects:

- `Human_TNFa_1TNF_A/B/C`
- `Mouse_TNFa_2TNF_A/B/C`

Existing conventions are visible: ARG/LYS red, ASP/GLU blue, HIS magenta. The selections `Human_candidate_hotspots`, `Mouse_candidate_hotspots`, `Human_selected_hotspots`, and `Mouse_selected_hotspots` start empty so new choices can be added interactively. Candidate hotspot coloring should be green after selection.

Use PyMOL clicks or commands such as `select Human_candidate_hotspots, Human_TNFa_1TNF_A and resi 65` and then inspect the object. Record selected residues using deposited author chain and residue numbering. Mouse author numbering skips residue 73.

This session is for review only. It does not modify an Empire upload folder or submit a job.
''')
print(session)
