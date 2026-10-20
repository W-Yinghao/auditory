import json
import os
import subprocess
from private.auditory_alignment_v3.aln35 import maintain_fleet as F
assert os.environ.get('SLURM_JOB_ID')
subprocess.run(['/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python','-B','-m','pytest','-q',
    '-p','no:cacheprovider','tests/auditory_alignment_v3/aln35/test_fleet.py',
    'tests/auditory_alignment_v3/aln34/test_efficiency_loop.py'],check=True)
old=F.read(F.NEWBASE/'live_inventory_1047281.json')['source_hashes']
assert all(F.sha(F.ROOT/p)==h for p,h in old.items()),'old training source changed'
overrides=F.read(F.BASE/'fleet_smoke_jobs.json')
lanes=[F.lane(key,overrides) for key in F.CONFIG]
assert not any(item['state'].startswith(('technical','engineering_')) for item in lanes),lanes
record={'status':'pass','job':os.environ['SLURM_JOB_ID'],'source_sha256':F.sha(F.__file__),
    'priority_sha256':F.sha(F.Priority.__file__),'old_training_sources_unchanged':True,'lanes':lanes}
F.E.write(F.NEWBASE/'fleet_check_receipt.json',record)
print(json.dumps(record,indent=2))
