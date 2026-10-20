"""Slurm-only operational preflight; no GPU submissions or scientific outputs."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
root = Path('/home/infres/yinwang/EEG_auditory')
os.chdir(root)
out = root / 'private/auditory_alignment_v3/aln35/v100_20261019'
out.mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

sources = [root / p for p in (
    'private/auditory_alignment_v3/aln34/efficiency_loop_v2.py',
    'private/auditory_alignment_v3/aln35/maintain_fleet.py',
    'private/auditory_alignment_v3/aln34/efficiency_loop_v3.py',
    'private/auditory_alignment_v3/aln35/maintain_fleet_v2.py',
    'slurm/aln35_maintain_fleet_v2.sbatch')]
before = {str(p): sha(p) for p in sources}
subprocess.run([sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                'tests/auditory_alignment_v3/aln35/test_v100_routing.py'], check=True)
from private.auditory_alignment_v3.aln35 import maintain_fleet_v2 as F
overrides = F.read(F.BASE / 'fleet_smoke_jobs.json')
runtime = F.read(F.BASE / 'fleet_runtime.json')
for key, value in runtime['extra_lanes'].items():
    F.CONFIG[key] = F.Previous.CONFIG[key] = tuple(value)
lanes = [F.lane(key, overrides) for key in F.CONFIG] + F.plugin_lanes()
assert not any(x['state'].startswith(('technical', 'engineering_')) for x in lanes), lanes
assert all(sha(p) == value for p, value in before.items())
receipt = {'status': 'pass', 'time': datetime.now().astimezone().isoformat(),
           'job': os.environ['SLURM_JOB_ID'], 'step': os.environ.get('SLURM_STEP_ID'),
           'source_sha256': before, 'live_readiness': 'pass',
           'gpu_probe_is_separate': True, 'lanes': lanes}
(out / 'routing_check.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('V100 routing preflight PASS', receipt['job'], receipt['step'], flush=True)
