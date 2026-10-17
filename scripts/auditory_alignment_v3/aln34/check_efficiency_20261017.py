"""Slurm-only operational preflight: tests, preserved identities and live audit."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
assert os.environ.get('SLURM_JOB_ID')
base = Path('private/auditory_alignment_v3/aln34')
for name in ('efficiency_loop.py', 'maintain_fleet_v15.py'):
    ast.parse((base/name).read_text())
for name in ('private/auditory_alignment_v3/keeper_prior_v2.sh', 'slurm/aln34_prior_keeper_v2.sbatch', 'slurm/aln34_maintain_fleet_v15.sbatch'):
    subprocess.run(['bash', '-n', name], check=True)
subprocess.run([sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
               'tests/auditory_alignment_v3/aln34/test_efficiency_loop.py',
               'tests/auditory_alignment_v3/aln34/test_priority_schedule.py'], check=True)
expected = {
    'private/auditory_alignment_v3/keeper_prior.sh': 'd360065f6aec4f3d2e83e5401cd2d30f705cd1bdbcddf0d73f4e4e20fc993f10',
    'slurm/aln33_prior_pool.sbatch': '0d026b8490037a08c43ddc9e9129cac0c2f10cb8e065696c5586611ca807d723',
    'private/auditory_alignment_v3/aln34/private_episode_v2/plan.json': 'ea1f6884b500d6d723dc1d2f56f2c1d1a17c5cef3ed619561676589bb389f208',
}
for name, digest in expected.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
from private.auditory_alignment_v3.aln34 import efficiency_loop as E
from private.auditory_alignment_v3.aln34 import maintain_fleet_v14 as F
for key, value in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items():
    F.CONFIG[key] = tuple(value)
overrides = json.loads((base/'fleet_smoke_jobs.json').read_text())
lanes = [F.lane(key, overrides) for key in F.CONFIG]
jobs = E.query_jobs()
value = {'time': E.stamp(), 'job': os.environ['SLURM_JOB_ID'], 'status': 'pass',
         'gpu_count': E.gpu_count(jobs), 'hardware': E.hardware(), 'timing': E.collect_timings({}),
         'lanes': [{k: item.get(k) for k in ('lane','state','remaining','ready','failed')} for item in lanes]}
E.write(base/'efficiency_preflight.json', value)
print('PASS', json.dumps({k:value[k] for k in ('time','job','status','gpu_count')}), flush=True)
print(json.dumps(value['timing'], indent=2), flush=True)
