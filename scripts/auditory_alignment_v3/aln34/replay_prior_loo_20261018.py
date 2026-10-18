"""One matched-device replay; preserves original failure and frozen tolerances."""
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import torch

from auditory_alignment_v3.aln34 import prior_private_loo as P

assert os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available()
os.umask(0o077)
eid = 'ALN3X_5e2403355822478f'
base, store = P.BASE, P.STORE
plan = P.read(P.PLAN)
P.verify(plan)
row = next(r for r in plan['rows'] if r['experiment_id'] == eid)
source = P.read(P.SOURCE/'units'/f'{eid}.json')
assert torch.cuda.get_device_name(0) == source['device'] == 'Tesla V100-PCIE-16GB'
attempt = base/'device_replay_20261018'/os.environ['SLURM_JOB_ID']
attempt.mkdir(parents=True, exist_ok=False)
receipt = {'status': 'started', 'time': datetime.now().astimezone().isoformat(),
           'job': os.environ['SLURM_JOB_ID'], 'unit': eid, 'plan_sha256': P.sha(P.PLAN),
           'driver_sha256': P.sha(__file__), 'recorded_device': source['device'],
           'tolerances_unchanged': P.L.REPRO_TOL}
P.write(attempt/'receipt.json', receipt)
with (base/'claims'/f'{eid}.lock').open('a+') as handle:
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    original = base/'units'/f'{eid}.json'
    marker = base/'units'/f'{eid}.FAILED.json'
    assert P.read(original)['status'] == 'reproduction_failed' and marker.is_file()
    archived = attempt/'original_failure'
    archived.mkdir()
    for path in (original, marker):
        shutil.copy2(path, archived/path.name)
        assert P.sha(path) == P.sha(archived/path.name)
    receipt['preserved_failure'] = {str(p): P.sha(p) for p in archived.iterdir()}
    P.BASE = attempt/'evaluation'
    P.STORE = store/'device_replay_20261018'/os.environ['SLURM_JOB_ID']
    try:
        P.evaluate(row, plan)
        out = P.BASE/'units'/f'{eid}.json'
        result = P.read(out)
        assert result['status'] == 'complete' and result['reproduction']['pass']
        assert result['same_recorded_device'] and result['plan_sha256'] == P.sha(P.PLAN)
        result['device_replay'] = {'receipt': str(attempt/'receipt.json'),
                                   'preserved_failure': receipt['preserved_failure']}
        P.write(out, result)
        receipt.update(status='pass', result_sha256=P.sha(out), reproduction=result['reproduction'])
        P.write(attempt/'receipt.json', receipt)
        assert P.sha(original) == P.sha(archived/original.name)
        assert P.sha(marker) == P.sha(archived/marker.name)
        P.write(original, result)
        # The active stop marker is relocated only after a passing matched replay.
        marker.rename(archived/(marker.name+'.resolved_active_marker'))
        with (P.SOURCE/'logs/operations.log').open('a') as log:
            log.write(f"{datetime.now().astimezone().isoformat()} prior LOO {eid} matched V100 replay passed job={os.environ['SLURM_JOB_ID']}; original failure preserved at {archived}; unchanged plan and tolerances; lane eligible again\n")
        print(json.dumps(receipt), flush=True)
    except BaseException:
        receipt['status'] = 'failed'
        P.write(attempt/'receipt.json', receipt)
        raise
