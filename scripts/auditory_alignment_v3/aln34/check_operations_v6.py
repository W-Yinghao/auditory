import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('maintain_fleet_v6.py','milestone_monitor_v3.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_maintain_fleet_v6.sbatch','aln34_milestones_v3.sbatch','aln34_private_episode.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('fleet6',base/'maintain_fleet_v6.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.CONFIG.update({k:tuple(v) for k,v in json.loads((base/'fleet_runtime.json').read_text())['extra_lanes'].items()})
overrides=json.loads((base/'fleet_smoke_jobs.json').read_text())
for key in m.CONFIG:
    r=m.lane(key,overrides);print(key,r['state'],r['ready'],r['remaining'])
    if key=='private_episode':assert r['remaining']==50 and r['state']=='waiting_engineering_receipt'
subprocess.run([sys.executable,'-B','-m','pytest','-p','no:cacheprovider','-q',
    'tests/auditory_alignment_v3/aln34/test_fusion_function_aggregate.py'],check=True)
for module in ('private_episode_aggregate','fusion_function_aggregate','new_lane_aggregate','breadth_aggregate'):
    subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.'+module],check=True)
print('PASS: private episode readiness, monitor syntax, new functional risk parser, frozen plans and aggregate refresh',flush=True)
