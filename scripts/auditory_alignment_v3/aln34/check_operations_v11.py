import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('maintain_fleet_v11.py','milestone_monitor_v8.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_maintain_fleet_v11.sbatch','aln34_milestones_v8.sbatch','aln34_prior_private_loo.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('fleet11',base/'maintain_fleet_v11.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.seconds_left('1-02:03:04')==93784 and m.seconds_left('02:03')==123
assert m.seconds_left('UNLIMITED') is None
m.CONFIG.update({k:tuple(v) for k,v in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items()})
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for key in m.CONFIG:
    r=m.lane(key,overrides);print(key,r['state'],r['ready'],r['remaining'])
    if key in ('prior_loo','prior_science'):
        assert r['total']>0 and r['state'] in ('waiting_engineering_receipt','engineering_running','ready')
        if r['state']=='ready':assert ('slurm/aln34_prior_private_loo.sbatch' if key=='prior_loo' else 'slurm/aln34_prior_science.sbatch') in r['submit']
subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.prior_private_loo','--aggregate'],check=True)
subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.prior_science_aggregate'],check=True)
print('PASS:20 operating lanes and both prior follow-up aggregates',flush=True)
