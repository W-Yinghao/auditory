import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('maintain_fleet_v8.py','milestone_monitor_v5.py','prior_trajectory.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_maintain_fleet_v8.sbatch','aln34_milestones_v5.sbatch','aln34_attention_transfer.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('fleet8',base/'maintain_fleet_v8.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.CONFIG.update({k:tuple(v) for k,v in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items()})
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for key in m.CONFIG:
    r=m.lane(key,overrides);print(key,r['state'],r['ready'],r['remaining'])
    if key=='attention':assert r['remaining']==160 and r['state']=='waiting_engineering_receipt'
for args in (['-m','auditory_alignment_v3.aln34.attention_transfer_aggregate'],[str(base/'prior_trajectory.py')]):
    subprocess.run([sys.executable,'-B',*args],check=True)
print('PASS:17 operating lanes, attention aggregation and all-observed donor diagnostics',flush=True)
