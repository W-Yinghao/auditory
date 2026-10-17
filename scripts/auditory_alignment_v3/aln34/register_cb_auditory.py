import os
import subprocess
import sys

assert os.environ.get('SLURM_JOB_ID')
subprocess.run(['bash','-n','slurm/aln34_cb_auditory.sbatch'],check=True)
subprocess.run([sys.executable,'-B','-m','pytest','-p','no:cacheprovider','-q',
    'tests/auditory_alignment_v3/aln34/test_cb_auditory.py','-k','paired_donor_accounting'],check=True)
for args in (['-m','auditory_alignment_v3.aln34.cb_auditory','--make-plan'],
             ['-m','auditory_alignment_v3.aln34.cb_auditory_aggregate']):
    subprocess.run([sys.executable,'-B',*args],check=True)
print('PASS: CB auditory registration and empty complete-identity aggregate',flush=True)
