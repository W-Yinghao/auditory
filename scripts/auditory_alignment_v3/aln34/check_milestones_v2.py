"""Slurm-only validation before the operational monitor handover."""
import ast
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base = Path('private/auditory_alignment_v3/aln34')
ast.parse((base/'milestone_monitor_v2.py').read_text())
subprocess.run(['bash', '-n', 'slurm/aln34_milestones_v2.sbatch'], check=True)
subprocess.run([sys.executable, '-B', '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
 'tests/auditory_alignment_v3/aln34/test_new_lane_aggregate.py',
 'tests/auditory_alignment_v3/aln34/test_science_aggregate.py',
 'tests/auditory_alignment_v3/aln34/test_breadth.py'], check=True)
subprocess.run([sys.executable, '-B', '-m', 'auditory_alignment_v3.aln34.breadth_aggregate'], check=True)
print('PASS: v2 monitor syntax, aggregation pairing, breadth plan provenance and initial aggregate', flush=True)
