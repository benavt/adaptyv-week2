#!/usr/bin/env python3
"""Frozen continuation: exclude existing structures; publish validated native outputs atomically."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent

def stamp():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')

def has_structure(directory):
    # Even an incomplete historical CIF must never trigger silent recomputation.
    return any(directory.glob('*_model_*.cif'))

def publish(native, canonical, tasks, published, validator):
    for task in tasks:
        tid = task['task_id']
        if tid in published:
            continue
        source = native/'by_seed'/tid/'s0'
        if not source.exists():
            continue
        try:
            validator(native, [task], native=True)
        except (AssertionError, ValueError, OSError, KeyError, RuntimeError, EOFError):
            continue  # The writer may still be publishing the sidecars.
        dest = canonical/'predictions'/tid
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise RuntimeError('Refusing to overwrite historical output: '+str(dest))
        staging = dest.parent/('.publishing-'+tid)
        shutil.copytree(source, staging)
        validator(canonical, [task], staging=staging)
        os.rename(staging, dest)
        published.add(tid)
        print(f'{stamp()} streamed {tid} -> {dest}', flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--audit', action='store_true')
    p.add_argument('--group')
    args=p.parse_args()
    plan=json.loads((HERE/'run.json').read_text())
    for name, expected in plan['files_sha256'].items():
        assert sha(HERE/name)==expected, name
    for name, expected in plan['external_sha256'].items():
        assert sha(name)==expected, name
    ns={}
    exec(compile((HERE/'validation.py').read_text(), str(HERE/'validation.py'), 'exec'), ns)
    ns['RUN']=Path(plan['predecessor']).parent
    validate=ns['validate_outputs']
    tasks=json.loads((HERE/'tasks.json').read_text())
    by_id={t['task_id']:t for t in tasks}
    groups=json.loads((HERE/'groups.json').read_text())
    output=Path(plan['canonical_output_root'])
    if args.audit:
        count=missing=incomplete=0
        remaining=[]
        for group in groups:
            if group['group_id']=='pilot':
                continue
            todo=0
            for tid in group['task_ids']:
                d=output/group['group_id']/('boltz_results_'+group['group_id'])/'predictions'/tid
                if has_structure(d):
                    count+=1
                    if not all((d/f).is_file() and (d/f).stat().st_size for f in [f'{tid}_model_0.cif', f'confidence_{tid}_model_0.json', f'pae_{tid}_model_0.npz',f'pde_{tid}_model_0.npz',f'plddt_{tid}_model_0.npz']):
                        incomplete+=1
                else:
                    todo+=1; missing+=1
            if todo:
                remaining.append(int(group['group_id'].split('-')[1]))
        print(json.dumps(dict(at=stamp(), existing_structures=count, remaining_structures=missing, incomplete_existing=incomplete, remaining_groups=remaining)))
        return
    gid=args.group or f'batch-{int(os.environ["SLURM_ARRAY_TASK_ID"]):03d}'
    group=next(g for g in groups if g['group_id']==gid)
    selected=[by_id[tid] for tid in group['task_ids']]
    result=output/gid
    result.mkdir(parents=True, exist_ok=True)
    with (result/'.boltz2-continuation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        todo=[t for t in selected if not has_structure(result/('boltz_results_'+gid)/'predictions'/t['task_id'])]
        canonical=result/('boltz_results_'+gid)
        attempt=result/('.'+HERE.name)
        attempt.mkdir()
        save(attempt/'continuation.json', dict(at=stamp(), run=str(HERE/'run.json'), mode=plan['mode'], todo=[t['task_id'] for t in todo], preserved=[t['task_id'] for t in selected if t not in todo]))
        # Historical directories without a structure are preserved before publication.
        for task in todo:
            old=canonical/'predictions'/task['task_id']
            if old.exists():
                dest=attempt/'predecessor-partial'/task['task_id']
                dest.parent.mkdir(parents=True, exist_ok=True)
                os.rename(old, dest)
        if not todo:
            print(gid+': all structures already exist; no inference', flush=True)
            return
        import torch
        assert torch.cuda.is_available(), 'GPU inference requires CUDA'
        assert torch.cuda.device_count()==1, 'Expected exactly one allocated visible GPU'
        save(attempt/'gpu.json',dict(at=stamp(),name=torch.cuda.get_device_name(0),visible_devices=1,cuda=torch.version.cuda,torch_version=torch.__version__))
        inputs=attempt/'inputs'
        inputs.mkdir()
        for task in todo:
            source=HERE/'native-inputs'/gid/(task['task_id']+'.yaml')
            assert sha(source)==plan['files_sha256'][str(source.relative_to(HERE))]
            (inputs/source.name).write_bytes(source.read_bytes())
        native=attempt/'native'
        command=['bash',plan['native_entrypoint'],plan['mode'],str(inputs),str(native),*plan['prediction_options']]
        tmp=tempfile.TemporaryDirectory(prefix='tnfa-resume-', dir='/tmp')
        env=dict(os.environ, TMPDIR=tmp.name, OMP_NUM_THREADS='8',MKL_NUM_THREADS='8')
        save(attempt/'execution-intent.json', dict(at=stamp(), command=command, job_id=os.environ.get('SLURM_JOB_ID'), array_id=os.environ.get('SLURM_ARRAY_JOB_ID'), task_id=os.environ.get('SLURM_ARRAY_TASK_ID'), canonical=str(canonical), monitor_logs=str(HERE/'resources')))
        published=set()
        with (attempt/'boltz2.log').open('x') as log:
            child=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                while child.poll() is None:
                    publish(native,canonical,todo,published,validate)
                    time.sleep(5)
                publish(native,canonical,todo,published,validate)
            except BaseException:
                child.terminate()
                child.wait()
                raise
            finally:
                save(attempt/'execution-exit.json',dict(at=stamp(),native_returncode=child.poll(),published=sorted(published)))
                tmp.cleanup()
        assert child.returncode==0, f'Native inference failed ({child.returncode}): {attempt}/boltz2.log'
        assert published=={t['task_id'] for t in todo}, 'Native run omitted or failed validation for some structures'
        index=validate(canonical,selected)
        # Native gates inspect their own output set at process exit. Remove only
        # verified duplicate files after those gates and canonical validation pass.
        for task in todo:
            source=native/'by_seed'/task['task_id']/'s0'
            dest=canonical/'predictions'/task['task_id']
            for file in source.iterdir():
                assert file.is_file() and sha(file)==sha(dest/file.name)
            shutil.rmtree(source)
        record=dict(completed_at=stamp(),group_id=gid,count=len(index),predictions=index,continuation_run=str(HERE/'run.json'),boltz2_mode=plan['mode'],preserved_count=len(selected)-len(todo))
        save(attempt/'result-index.json',record)
        if not (result/'result-index.json').exists():
            save(result/'result-index.json',record)
        print(f'{gid}: {len(index)} validated; {len(published)} new, {len(selected)-len(todo)} preserved',flush=True)

if __name__=='__main__':
    main()
