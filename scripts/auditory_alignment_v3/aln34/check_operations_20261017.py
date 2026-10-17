import ast
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
base=Path('private/auditory_alignment_v3/aln34')
for name in ('continue_prior.py','milestone_monitor.py','maintain_fleet_v4.py','rotation_worker.py'):
    ast.parse((base/name).read_text())
for name in ('aln34_milestones.sbatch','aln34_maintain_fleet_v4.sbatch'):
    subprocess.run(['bash','-n','slurm/'+name],check=True)
spec=importlib.util.spec_from_file_location('milestone_verify',base/'milestone_monitor.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.verify_add11()
subprocess.run([sys.executable,'-B',str(base/'continue_prior.py')],check=True)
print('PASS: operations AST/shell; unchanged ADDENDUM_11 source and original plan prefix; tracked continuation guard and dry run')
