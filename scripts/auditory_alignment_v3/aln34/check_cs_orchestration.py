"""Slurm-only CPU integration of new CS plan, aggregate and service versions."""
import ast
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
assert os.environ.get('SLURM_JOB_ID')
subprocess.run([sys.executable,'-B','-m','pytest','-p','no:cacheprovider','-q',
               'tests/auditory_alignment_v3/aln34/test_cs_episode.py'],check=True)
from auditory_alignment_v3.aln34 import cs_episode as C
plan=json.loads(C.PLAN.read_text());C.verify(plan)
assert len(plan['rows'])==40
fleet=importlib.import_module('private.auditory_alignment_v3.aln34.maintain_fleet_v12')
item=fleet.lane('cs_episode',{})
assert item['total']==40 and item['state']=='waiting_engineering_receipt'
monitor=importlib.import_module('private.auditory_alignment_v3.aln34.milestone_monitor_v9')
assert 'cs_episode_v1' in monitor.LANES and len(monitor.LANES)==len(set(monitor.LANES))
for script in ('slurm/aln34_cs_episode.sbatch','slurm/aln34_maintain_fleet_v12.sbatch','slurm/aln34_milestones_v9.sbatch'):
    subprocess.run(['bash','-n',script],check=True)
subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.cs_episode_aggregate'],check=True)
print('CS and fleet/evidence integration PASS',flush=True)
