#!/usr/bin/env python3
"""Run pinned native BC2 until N completed gradient trajectories, without MPNN.

Native accepted-design counters remain untouched. This single-process adapter
adds an independently inspectable completed-sequence ledger and stopping rule.
Paths and runtime identities come from frozen run inputs, never this module.
"""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


class CompletedBudget:
    def __init__(self, folder, requested, min_length=60, max_length=100):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.requested = int(requested)
        if self.requested < 1:
            raise ValueError('Completed-trajectory budget must be positive')
        self.min_length, self.max_length = min_length, max_length
        self.ledger = self.folder / 'completed_sequences.jsonl'
        self.records = [json.loads(line) for line in self.ledger.read_text().splitlines()] if self.ledger.exists() else []
        self.designs = {r['design'] for r in self.records}
        if len(self.designs) != len(self.records) or len(self.records) > self.requested:
            raise ValueError('Duplicate designs or excess completed records in ledger')

    @property
    def done(self):
        return len(self.records) >= self.requested

    def record(self, row, structure):
        if row.get('terminated'):
            return False
        if self.done:
            raise ValueError('Refusing a completed output beyond the requested budget')
        design, sequence = row['design'], row.get('Binder_Sequence', '')
        if design in self.designs:
            raise ValueError(f'Duplicate completed trajectory: {design}')
        if not re.fullmatch('[ACDEFGHIKLMNPQRSTVWY]+', sequence):
            raise ValueError(f'Completed trajectory has no exact standard-amino-acid sequence: {design}')
        if not self.min_length <= len(sequence) <= self.max_length:
            raise ValueError(f'Unexpected binder length: {design}, {len(sequence)}')
        structure = Path(structure)
        if not structure.is_file() or not structure.stat().st_size:
            raise ValueError(f'Completed trajectory structure is missing: {structure}')
        record = {'completed_index': len(self.records) + 1, 'design': design,
                  'trajectory': row['trajectory'], 'design_hash': row['hash'],
                  'sequence': sequence, 'sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
                  'structure': str(structure.resolve()), 'structure_sha256': sha256(structure),
                  'terminated': '', 'recorded_at': datetime.now(timezone.utc).isoformat(),
                  'scope': 'native gradient trajectory cleared all stage checks; no MPNN or independent validation'}
        with self.ledger.open('a') as stream:
            stream.write(json.dumps(record, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.records.append(record)
        self.designs.add(design)
        self.export()
        print(f'completed-trajectory budget: {len(self.records)}/{self.requested}; raw attempt {row["trajectory"]}', flush=True)
        return True

    def export(self):
        fasta = ''.join(f'>{r["design"]} completed={r["completed_index"]} trajectory={r["trajectory"]}\n{r["sequence"]}\n' for r in self.records)
        summary = {'requested_completed_trajectories': self.requested,
                   'completed_trajectories': len(self.records),
                   'unique_sequences': len({r['sequence_sha256'] for r in self.records}),
                   'budget_reached': self.done, 'accepted_designs': 0,
                   'mpnn': False, 'independent_validation': False,
                   'scope': 'completed native gradient trajectories; early failures do not count',
                   'updated_at': datetime.now(timezone.utc).isoformat()}
        for filename, content in [('completed.fasta', fasta), ('completed_budget.json', json.dumps(summary, indent=2) + '\n')]:
            temporary = self.folder / (filename + '.partial')
            temporary.write_text(content)
            temporary.replace(self.folder / filename)


def verify_runtime(lock):
    import bindcraft
    import importlib.metadata
    import subprocess
    root = Path(bindcraft.__file__).resolve().parent.parent
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != lock['commit']:
        raise ValueError(f'BC2 revision changed: {commit}')
    for relative, expected in lock['source_sha256'].items():
        if sha256(root / relative) != expected:
            raise ValueError(f'Pinned BC2 file changed: {relative}')
    for package, expected in lock['packages'].items():
        if importlib.metadata.version(package) != expected:
            raise ValueError(f'Runtime package changed: {package}')
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--budget', type=Path, required=True)
    parser.add_argument('--runtime-lock', type=Path, required=True)
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    lock = json.loads(args.runtime_lock.read_text())
    verify_runtime(lock)
    from bindcraft import campaign as native
    from bindcraft.settings import read_settings, build_design_settings
    from bindcraft.model_weights import model_weights
    from bindcraft.preflight import preflight_campaign
    from bindcraft.protein_preparation import prepare_targets, receptor_chain_layouts
    from bindcraft.protein import ResidueFlags, has_residue_flag
    import jax
    settings = read_settings(str(args.settings.resolve()))
    budget_spec = json.loads(args.budget.read_text())
    if not settings.get('trajectory_only') or settings.get('forced_targeting'):
        raise ValueError('This adapter requires trajectory-only and ordinary targeting')
    if settings.get('parameter_sweep') or settings.get('copies', 1) != 1:
        raise ValueError('This adapter supports one native campaign and one binder copy')
    af2, _mpnn = model_weights(download=False)
    checkpoints = preflight_campaign(settings, settings['project_folder'], af2, None)
    prepared = build_design_settings(settings)
    target_audit = {}
    for name, protein in prepare_targets(prepared).items():
        target_audit[name] = {'residues': len(protein), 'hotspots': int(has_residue_flag(protein.flags, ResidueFlags.HOTSPOT).sum())}
    checkpoint_audit = {p: {'bytes': Path(p).stat().st_size, 'sha256': sha256(p)} for p in checkpoints}
    audit = {'runtime_commit': lock['commit'], 'jax_devices': [str(d) for d in jax.devices()],
             'targets': target_audit, 'receptor_layouts': receptor_chain_layouts(prepared),
             'checkpoints': checkpoint_audit, 'resolved_settings': settings,
             'count_control': budget_spec, 'adapter_sha256': sha256(__file__)}
    for target in budget_spec['target_audit']:
        if target_audit[target['name']] != {'residues': target['residues'], 'hotspots': target['hotspots']}:
            raise ValueError(f'Native target/hotspot count changed: {target["name"]}')
    if args.preflight_only:
        print(json.dumps(audit, indent=2, default=str))
        return
    if not any(d.platform == 'gpu' for d in jax.devices()):
        raise ValueError('Scientific trajectory generation requires the allocated GPU')
    output = Path(settings['project_folder'])
    output.mkdir(parents=True, exist_ok=True)
    (output / 'native_preflight.json').write_text(json.dumps(audit, indent=2, default=str) + '\n')
    native.write_campaign_metadata(str(output), settings, str(args.settings.resolve()), checkpoints,
                                   {'count_method': 'completed_native_trajectory_v1', 'accepted_count_unused': True})
    counter = CompletedBudget(output / 'generated_sequences', budget_spec['requested_completed_trajectories'],
                              *settings['binder_lengths'])
    counter.export()
    original_progress, original_append = native.CampaignProgress, native.append_campaign_metrics
    trajectory_table = native.stage_table(str(output), native.TRAJECTORY_STAGE)

    class CompletedProgress(original_progress):
        def claim_trajectory(self):
            if counter.done:
                return None
            return super().claim_trajectory()

    def append_with_completed_sequence(path, row):
        original_append(path, row)
        if os.path.abspath(path) == os.path.abspath(trajectory_table):
            directory = Path(native.stage_folder(str(output), native.TRAJECTORY_STAGE)) / row['design']
            counter.record(row, native.trajectory_output_path(str(directory), 'trajectory.cif'))

    native.CampaignProgress, native.append_campaign_metrics = CompletedProgress, append_with_completed_sequence
    try:
        native.run_campaign(settings, str(output), af2_weights=af2, mpnn_weights=None)
    finally:
        native.CampaignProgress, native.append_campaign_metrics = original_progress, original_append
        counter.export()
    if not counter.done:
        raise RuntimeError('Run ended before the completed-trajectory budget was reached')


if __name__ == '__main__':
    main()
