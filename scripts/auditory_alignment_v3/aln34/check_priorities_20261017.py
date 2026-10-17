"""Validate operational reordering on Slurm CPU without touching training identities."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for p in (base/'maintain_fleet_v14.py',base/'priority_rotation_worker.py',base/'priority_schedule.py'):
    ast.parse(p.read_text())
subprocess.run([sys.executable,'-B','-m','pytest','-p','no:cacheprovider','-q',
               'tests/auditory_alignment_v3/aln34/test_priority_schedule.py'],check=True)
from private.auditory_alignment_v3.aln34 import maintain_fleet_v13 as Old, maintain_fleet_v14 as New
runtime=json.loads((base/'fleet_runtime.json').read_text())
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for k,v in runtime['extra_lanes'].items():Old.CONFIG[k]=tuple(v);New.CONFIG[k]=tuple(v)
for k in Old.CONFIG:
    a=Old.lane(k,overrides);b=New.lane(k,overrides)
    assert all(a.get(x)==b.get(x) for x in ('state','ready','remaining','failed','total')),k
    if b['state']=='ready' and 'submit' in b:
        assert 'scontrol' not in str(b['submit'])
print('PASS same eligible units, engineering gates and failed markers; only priority, ordering, budget concurrency and short evaluation batch size changed',flush=True)
subprocess.run([sys.executable,'-B',str(base/'priority_cost_breakdown_20261017.py')],check=True)
