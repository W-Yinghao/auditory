"""Validated scheduler handoff inside an existing project CPU allocation."""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

assert os.environ.get('SLURM_JOB_ID') == '1047358'
root = Path('/home/infres/yinwang/EEG_auditory')
os.chdir(root)
os.umask(0o077)
base = root / 'private/auditory_alignment_v3/aln35'
receipt = json.loads((base / 'v100_20261019/routing_check.json').read_text())
assert receipt['status'] == 'pass'
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in receipt['source_sha256'].items())
print(datetime.now().astimezone().isoformat(), 'HANDOFF_READY', os.environ['SLURM_JOB_ID'], os.environ.get('SLURM_STEP_ID'), flush=True)
deadline = time.time() + 600
while time.time() < deadline:
    if (base / 'STOP_fleet_maintenance').exists():
        with (base.parent / 'aln34/.fleet_maintenance.lock').open('a+') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                break
    time.sleep(2)
else:
    raise RuntimeError('Old scheduler did not release the handoff lock')
from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as fleet
print(datetime.now().astimezone().isoformat(), 'HANDOFF_START_V2', flush=True)
fleet.main()
