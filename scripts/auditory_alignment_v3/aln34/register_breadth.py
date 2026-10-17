import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import difflib
from auditory_alignment_v3.aln34 import learning_budget as B

assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
base=Path('auditory_alignment_v3/aln34');out=Path('private/auditory_alignment_v3/aln34/breadth_registration')
out.mkdir(parents=True,exist_ok=True)
for original,new in (('learning_budget_v2','breadth_budget'),('data_inner','breadth_inner'),('adaptation_policy','breadth_policy'),('strong_fusion','breadth_fusion'),('episode_training','breadth_episode')):
    patch=''.join(difflib.unified_diff((base/(original+'.py')).read_text().splitlines(True),(base/(new+'.py')).read_text().splitlines(True),fromfile=original+'.py',tofile=new+'.py'))
    (out/(new+'.patch')).write_text(patch)
    subprocess.run([sys.executable,'-B','-m','auditory_alignment_v3.aln34.'+new,'--make-plan'],check=True)
B.write(out/'receipt.json',{'job':os.environ['SLURM_JOB_ID'],'time':datetime.now().astimezone().isoformat(),
    'source_sha256':{p.name:B.sha(p) for p in base.glob('breadth_*.py')},'units':{'budget':75,'data_inner':375,'policy':40,'fusion':15,'episode':40}})
