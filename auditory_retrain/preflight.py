"""Slurm-only audit checks against completed tasks; no model fitting."""
import argparse
import ast
import copy
import json
import os
import shutil
import sys
from pathlib import Path

import pandas as pd

from auditory5.provenance import ROOT, digest, require_slurm, write_json


def main():
    require_slurm()
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', default='audit_preflight_001')
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    base = ROOT / 'private/auditory_retrain_v1'
    plan_path = base / 'jobs/plan_001/plan.json'
    plan = json.loads(plan_path.read_text())
    destination = base / args.run
    snapshot = destination / 'source'
    if not args.frozen:
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copytree(Path(plan['source_snapshot']) / 'auditory5', snapshot / 'auditory5')
        (snapshot / 'auditory_retrain').mkdir()
        for name in ['__init__.py', 'verify.py', 'report.py', 'audit.py', 'preflight.py']:
            shutil.copyfile(ROOT / 'auditory_retrain' / name, snapshot / 'auditory_retrain' / name)
        write_json(destination / 'source_receipt.json', {str(p.relative_to(snapshot)): digest(p) for p in snapshot.rglob('*.py')})
        env = dict(os.environ, AUDITORY5_ROOT=str(ROOT), PYTHONPATH=str(snapshot))
        os.chdir(snapshot)
        os.execve(sys.executable, [sys.executable, '-m', 'auditory_retrain.preflight', '--run', args.run, '--frozen'], env)
    for file in snapshot.rglob('*.py'):
        ast.parse(file.read_text(), filename=str(file))
    from auditory_retrain.verify import _validate_task, _expected_tasks, _allowed_gpu
    from auditory_retrain import report
    assert report.ROOT == ROOT
    _expected_tasks(plan)
    spec = plan['config']['corrected_retraining']
    support = pd.read_parquet(base / 'splits/splits_001/support.parquet')
    folds = json.loads((base / 'splits/splits_001/folds.json').read_text())
    universe = set(folds['outer_fold_by_group'])
    general = set(support.loc[support.general, 'split_group_id'])
    completed = [t for t in plan['tasks'] if (plan_path.parent / 'outputs' / t['name'] / 'completion.json').exists()]
    assert len(completed) >= 7
    details = []
    for task in completed:
        details.append(_validate_task(task, plan_path.parent / 'outputs' / task['name'], digest(plan_path),
                                     plan['config_hash'], universe, general, spec['allowed_GPU_names']))
    task = next(t for t in completed if t['mode'] == 'R_SUP')
    bad = copy.deepcopy(task)
    bad['effective_fit_groups'].append(bad['test_groups'][0])
    rejected = False
    try:
        _validate_task(bad, plan_path.parent / 'outputs' / task['name'], digest(plan_path),
                       plan['config_hash'], universe, general, spec['allowed_GPU_names'])
    except ValueError:
        rejected = True
    assert rejected, 'Auditor accepted a held-out identity in fitting'
    assert not _allowed_gpu('Tesla P100', spec['allowed_GPU_names'])
    assert _allowed_gpu('NVIDIA L40S', spec['allowed_GPU_names'])
    write_json(destination / 'task_checks.json', details)
    result = dict(status='PASS', completed_task_receipts_checked=len(completed),
                  held_out_identity_mutation_rejected=rejected, no_P100=True,
                  model_refits=0, job_id=os.environ['SLURM_JOB_ID'])
    write_json(ROOT / spec['aggregates_relative'] / args.run / 'validation.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
