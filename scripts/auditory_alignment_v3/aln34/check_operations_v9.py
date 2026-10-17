import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('maintain_fleet_v9.py','milestone_monitor_v6.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_maintain_fleet_v9.sbatch','aln34_milestones_v6.sbatch','aln34_private_cb_factorial.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('fleet9',base/'maintain_fleet_v9.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.seconds_left('1-02:03:04')==93784 and m.seconds_left('02:03')==123
assert m.seconds_left('UNLIMITED') is None
m.CONFIG.update({k:tuple(v) for k,v in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items()})
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for key in m.CONFIG:
    r=m.lane(key,overrides);print(key,r['state'],r['ready'],r['remaining'])
    if key=='private_factorial':assert r['remaining']==60 and r['state']=='waiting_engineering_receipt'
subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.private_cb_factorial_aggregate'],check=True)
print('PASS:18 operating lanes and private CB factorial aggregate',flush=True)
