"""Read-only Slurm diagnosis of old S0 hash exceptions; no fitting."""
import hashlib
import json
import os
from pathlib import Path
import shutil
if not os.environ.get('SLURM_JOB_ID'):
    raise RuntimeError('SLURM_REQUIRED')
os.umask(0o077)
root=Path('/home/infres/yinwang/EEG_auditory')
private=root/'private/auditory_v21/hash_diagnosis_001'
private.mkdir(mode=0o700)
shutil.copyfile(__file__,private/'source.py')
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
old=root/'private/auditory_next_v2/S0_001'
files=json.loads((old/'legacy_input_hashes.json').read_text())
files += [dict(path=str(old/'source'/key),sha256=value) for key,value in json.loads((old/'start.json').read_text())['source_hashes'].items()]
exceptions=[]
for row in files:
    path=Path(row['path'])
    actual=digest(path) if path.is_file() else None
    if actual!=row['sha256']:exceptions.append(dict(path=str(path),expected=row['sha256'],actual=actual))
(private/'exceptions.json').write_text(json.dumps(exceptions,indent=2)+'\n')
receipt=dict(status='HASH_DIAGNOSIS_COMPLETE',checked=len(files),exceptions=len(exceptions),new_head_fits=0,
             job_id=os.environ['SLURM_JOB_ID'],source_sha256=digest(private/'source.py'))
(private/'completion.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
