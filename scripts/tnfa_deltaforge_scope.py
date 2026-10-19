#!/usr/bin/env python3
"""Audit saved DeltaForge results against the selected sequences; no API calls."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def check(candidate, species, receipt):
    response = receipt['raw_response']
    chains = response['interface_chain_summary']
    expected_target_length = {'human': 152, 'mouse': 148}[species]
    assert receipt['species'] == species
    assert receipt['status'] == 'completed' and response['success'] is True
    assert chains['n_chains'] == chains['n_protein_chains'] == 4
    assert chains['scored_receptor_chains'] == list('ABC')
    assert chains['scored_peptide_chain'] == 'D'
    assert chains['chain_lengths'] == dict.fromkeys('ABC', expected_target_length) | {'D': len(candidate['sequence'])}
    assert response['source_pdb_sha256'] == receipt['pdb_sha256']
    assert response['kd_nm'] == candidate[f'archived_{species}_KD_nM']
    assert response['kd_nm'] > 0
    assert response['structure_source_detected'] == 'boltz2'
    assert response['model_load_degraded'] is False
    if 'sequence' in receipt:
        assert receipt['sequence'] == candidate['sequence']
    if 'sequence_sha256' in receipt:
        assert receipt['sequence_sha256'] == hashlib.sha256(candidate['sequence'].encode()).hexdigest()
    if 'candidate_id' in receipt:
        assert receipt['candidate_id'] == candidate['candidate_id']
    if 'candidate_ids' in receipt:
        assert candidate['candidate_id'] in receipt['candidate_ids']
    return {
        'rank': candidate['submission_rank'],
        'candidate': candidate['name'].replace('-BenS', ''),
        'species': species,
        'candidate_copies': 1,
        'TNF_alpha_protomers': 3,
        'candidate_chain': 'D',
        'target_chains': 'A/B/C',
        'candidate_length': len(candidate['sequence']),
        'target_protomer_length': expected_target_length,
        'DeltaForge_KD_nM': response['kd_nm'],
        'scorer_version': response['scorer_version'],
        'calibration_version': response['affinity_scorer_version'],
        'scope_check': 'PASS',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    selected = json.loads(args.selection.read_text())['selected']
    results, sources = [], []
    for candidate in sorted(selected, key=lambda x: x['submission_rank']):
        for species in ['human', 'mouse']:
            path = Path(candidate['KD_source'][species])
            result = check(candidate, species, json.loads(path.read_text()))
            results.append(result)
            sources.append(dict(candidate=result['candidate'], species=species, source=str(path), receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    assert len(results) == 2 * len(selected)
    assert len({(r['candidate'], r['species']) for r in results}) == len(results)
    assert len({(r['scorer_version'], r['calibration_version']) for r in results}) == 1
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output/'deltaforge-scope.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(results)
    (args.output/'internal-deltaforge-scope.json').write_text(json.dumps(dict(status='passed', candidates=len(selected), observations=len(results), new_paid_calls=0, results=results, sources=sources), indent=2)+'\n')
    print(f'PASS: {len(selected)} candidates, {len(results)} species results; all one complete candidate chain versus TNF-alpha trimer; same scorer/calibration.')


if __name__ == '__main__':
    main()
