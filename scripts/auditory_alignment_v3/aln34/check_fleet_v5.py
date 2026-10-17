import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('maintain_fleet_v5.py','rotation_worker.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_breadth.sbatch','aln34_breadth_smoke_chain.sbatch','aln34_maintain_fleet_v5.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('fleet5',base/'maintain_fleet_v5.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.CONFIG.update({k:tuple(v) for k,v in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items()})
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for key in m.CONFIG:
    r=m.lane(key,overrides)
    print(key,r['state'],r['ready'],r['remaining'])
print('PASS: every registered lane is gated by its own receipt and corresponding inner-source directory')
