"""Versioned device-reproduction attempts; unchanged v1 evaluator and tolerance.

The first v1 production unit differed on V100 from its original A40 evaluation.
Do not overwrite that failed record or loosen its registered numerical tolerance.
Each device attempt has separate outputs and reuses the immutable v1 source plan.
"""
import argparse
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import torch

from . import private_calibration_loo as L

ORIGINAL = L.BASE
BASE = ORIGINAL / 'device_attempts_v1'
PROTOCOL = BASE / 'protocol.json'


def register():
    plan = L.load_plan()
    value = {'version': 'S34_PRIVATE_DEVICE_REPRODUCTION_v1', 'source_plan_sha256': L.sha(L.PLAN),
             'driver_sha256': L.sha(__file__), 'evaluator_sha256': L.sha(L.__file__),
             'unchanged_reproduction_tolerance': L.REPRO_TOL,
             'reason': '1043961: REVE random_full seed3401 fold0 V100 differs from original A40; preserve and test original device first',
             'device_counts': {}, 'created': datetime.now().astimezone().isoformat()}
    for unit in plan['units']:
        device = unit['recorded_device']
        value['device_counts'][device] = value['device_counts'].get(device, 0)+1
    if PROTOCOL.exists():
        old = json.loads(PROTOCOL.read_text())
        assert all(old[k] == v for k, v in value.items() if k != 'created')
    else:
        L.D.write(PROTOCOL, value)
        PROTOCOL.chmod(0o444)
    print(json.dumps(value, indent=2), flush=True)


def successes(eid):
    paths = [ORIGINAL/'units'/f'{eid}.json', *BASE.glob(f'*/units/{eid}.json')]
    return [p for p in paths if p.is_file() and json.loads(p.read_text())['status'] == 'complete']


def evaluate(eid, plan, protocol):
    unit = next(u for u in plan['units'] if u['row']['experiment_id'] == eid)
    device = torch.cuda.get_device_name(0)
    name = ''.join(c if c.isalnum() else '_' for c in device)
    L.BASE = BASE / name
    store = L.STORE / 'device_attempts_v1' / name
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    L.BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    link = L.BASE/'scores'
    if not link.exists():
        link.symlink_to(store, target_is_directory=True)
    assert link.is_symlink() and link.resolve() == store
    out = L.BASE/'units'/f'{eid}.json'
    if out.exists():
        raise FileExistsError(f'Never overwrite an earlier device attempt: {out}')
    try:
        L.evaluate(unit, plan)
    finally:
        if out.exists():
            record = json.loads(out.read_text())
            record['device_attempt'] = {'protocol_sha256': L.sha(PROTOCOL), 'driver_sha256': protocol['driver_sha256'],
                                        'historical_v1_path': str(ORIGINAL/'units'/f'{eid}.json')}
            L.D.write(out, record)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', action='store_true')
    ap.add_argument('--unit')
    ap.add_argument('--matched-only', action='store_true')
    args = ap.parse_args()
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
    os.umask(0o077)
    if args.register:
        register()
        return
    plan = L.load_plan()
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol['source_plan_sha256'] == L.sha(L.PLAN)
    assert protocol['driver_sha256'] == L.sha(__file__) and protocol['evaluator_sha256'] == L.sha(L.__file__)
    assert torch.cuda.is_available()
    if args.unit:
        evaluate(args.unit, plan, protocol)
        return
    device = torch.cuda.get_device_name(0)
    counts = {'reused': 0, 'attempted': 0, 'failed': 0, 'wrong_device_skipped': 0}
    for unit in plan['units']:
        eid = unit['row']['experiment_id']
        if successes(eid):
            counts['reused'] += 1
            continue
        if args.matched_only and device != unit['recorded_device']:
            counts['wrong_device_skipped'] += 1
            continue
        lock = BASE/'claims'/f'{eid}.lock'
        lock.parent.mkdir(exist_ok=True)
        with lock.open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if successes(eid):
                continue
            result = subprocess.run([sys.executable, '-B', '-u', '-m', 'auditory_alignment_v3.aln34.private_calibration_device',
                                     '--unit', eid], check=False)
            counts['attempted'] += 1
            counts['failed'] += int(result.returncode != 0)
    L.D.write(BASE/f'worker_{os.environ["SLURM_JOB_ID"]}.json', {'device': device, 'counts': counts,
                'complete_units': sum(bool(successes(u['row']['experiment_id'])) for u in plan['units']),
                'protocol_sha256': L.sha(PROTOCOL)})
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
