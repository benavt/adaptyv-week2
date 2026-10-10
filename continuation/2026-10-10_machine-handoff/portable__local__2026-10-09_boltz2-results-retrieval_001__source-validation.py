import hashlib, json
from pathlib import Path
AA = dict(zip('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL'.split(), 'ARNDCQEGHILKMFPSTWYV'))

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def finite_json(value):
    import math
    if isinstance(value, float):
        assert math.isfinite(value)
    elif isinstance(value, dict):
        for child in value.values():
            finite_json(child)
    elif isinstance(value, list):
        for child in value:
            finite_json(child)

def validate_outputs(output, tasks, native=False, staging=None):
    import numpy as np
    import gemmi
    predictions = output / 'predictions'
    index = []
    for task in tasks:
        directory = staging if staging else (output / 'by_seed' / task['task_id'] / 's0' if native else predictions / task['task_id'])
        models = list(directory.glob('*_model_*.cif'))
        confidences = list(directory.glob('confidence_*.json'))
        paes = list(directory.glob('pae_*.npz'))
        pdes = list(directory.glob('pde_*.npz'))
        assert len(models) == len(confidences) == len(paes) == len(pdes) == 1, task['task_id']
        plddts = list(directory.glob('plddt_*.npz'))
        assert len(plddts) == 1
        with np.load(plddts[0]) as data:
            assert 'plddt' in data and np.isfinite(data['plddt']).all()
        block = gemmi.cif.read_file(str(models[0])).sole_block()
        columns = {name: list(block.find_values('_atom_site.'+name)) for name in
                   ['label_atom_id', 'label_comp_id', 'label_asym_id', 'label_seq_id', 'Cartn_x', 'Cartn_y', 'Cartn_z']}
        assert len({len(values) for values in columns.values()}) == 1 and columns['label_atom_id']
        coords = np.array([[float(columns[name][i]) for name in ['Cartn_x', 'Cartn_y', 'Cartn_z']]
                           for i in range(len(columns['label_atom_id']))])
        assert np.isfinite(coords).all()
        residues = {chain: [] for chain in ['A', 'B', 'C', 'D']}
        for i, atom in enumerate(columns['label_atom_id']):
            if atom == 'CA':
                residues[columns['label_asym_id'][i]].append((int(columns['label_seq_id'][i]), columns['label_comp_id'][i]))
        assert all(residues.values())
        assert all([n for n, _ in values] == list(range(1, len(values)+1)) for values in residues.values())
        sequences = {chain: ''.join(AA[name] for _, name in values) for chain, values in residues.items()}
        assert sequences == {'A': task['target_sequence'], 'B': task['target_sequence'], 'C': task['target_sequence'], 'D': task['binder_sequence']}
        confidence = json.loads(confidences[0].read_text())
        assert confidence
        finite_json(confidence)
        residues = 3*len(task['target_sequence'])+len(task['binder_sequence'])
        for path, key in [(paes[0], 'pae'), (pdes[0], 'pde')]:
            with np.load(path) as data:
                assert key in data and data[key].shape == (residues, residues) and np.isfinite(data[key]).all()
        index.append({'task_id': task['task_id'], 'candidate_id': task['candidate_id'], 'target_species': task['target_species'],
                      'source_cohort': task['source_cohort'], 'binder_sequence_sha256': task['binder_sequence_sha256'],
                      'target_sequence_sha256': task['target_sequence_sha256'], 'native_input_sha256': task['native_input_sha256'],
                      'files_sha256': {str(p.relative_to(RUN)): sha(p) for p in directory.rglob('*') if p.is_file()},
                      'confidence_source': str(confidences[0].relative_to(RUN)),
                      'validation': 'exact four-chain sequence identities; finite coordinates/confidence/PAE/PDE; one predicted model'})
    return index
