"""After plan apply, install checked queue/watcher copies and refresh once."""
import ast
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT/'private/auditory_alignment_v3'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert os.environ.get('SLURM_JOB_ID')
os.umask(0o077)
assert sum('ALN32_PUBLIC_AUDIO_PRIOR_' in x for x in (OUT/'plan_ext.jsonl').read_text().splitlines()) == 1154
for key in ('make_queue', 'watch_anyhost'):
    patch = (OUT/f'aln34/prior33_patches/{key}.prior33.patch').read_text()
    old = re.search(r'# live-sha256:\s+([0-9a-f]{64})', patch)[1]
    new = re.search(r'# patched-sha256:\s+([0-9a-f]{64})', patch)[1]
    name = key + ('.py' if key == 'make_queue' else '.sh')
    live = OUT/name
    if sha(live) == new:
        continue
    candidate = Path(str(live)+'.tmp_prior33')
    assert sha(live) == old and sha(candidate) == new
    if key == 'make_queue':
        ast.parse(candidate.read_text())
    else:
        subprocess.run(['bash', '-n', str(candidate)], check=True)
    backup = OUT/f'aln34/deploy_backup_20261017/private/auditory_alignment_v3/{name}'
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(live, backup)
    os.replace(candidate, live)
    with (OUT/'logs/operations.log').open('a') as log:
        log.write(f'{datetime.now().astimezone().isoformat()} prior stage2 job={os.environ["SLURM_JOB_ID"]}: {name} {old} -> {new}\n')
subprocess.run([sys.executable, '-B', str(OUT/'make_queue.py')], check=True)
assert (OUT/'queue_v3_prior.remaining').read_text().strip().isdigit()
print('STAGE2 PASS; queue refreshed; prior keeper may start', flush=True)
