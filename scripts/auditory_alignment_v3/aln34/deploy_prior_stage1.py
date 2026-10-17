"""Checked, resumable registry -> dispatch -> offload integration, before plan apply."""
import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT / 'private/auditory_alignment_v3'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def deploy(key, relative):
    patch = (OUT / f'aln34/prior33_patches/{key}.prior33.patch').read_text()
    old = re.search(r'# live-sha256:\s+([0-9a-f]{64})', patch)[1]
    new = re.search(r'# patched-sha256:\s+([0-9a-f]{64})', patch)[1]
    live = ROOT / relative
    if sha(live) == new:
        print(f'already deployed {relative} {new}', flush=True)
        return
    assert sha(live) == old, f'live drift: {live}'
    candidate = Path(str(live)+'.tmp_prior33')
    assert sha(candidate) == new, f'candidate drift: {candidate}'
    if key in ('registry', 'run'):
        subprocess.run([sys.executable, '-B', '-m', 'auditory_alignment_v3.prior33.registry_patch',
                        'check-registry' if key == 'registry' else 'check-run', str(candidate)], check=True)
    else:
        loader = importlib.machinery.SourceFileLoader('prior_offload_candidate', str(candidate))
        module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
        loader.exec_module(module)
        assert module.P33_FAMILIES == {'ALN32_PUBLIC_AUDIO_PRIOR_'+x for x in
                                      ('DONOR','CSX_DONOR','RICH_DONOR','BRIDGE','TARGET','ZEROSHOT')}
        assert module.P33_FAMILIES <= module.NO_DEPS | module.HANDLED
    backup = OUT / 'aln34/deploy_backup_20261017' / relative
    backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if backup.exists():
        assert sha(backup) == old
    else:
        shutil.copy2(live, backup)
    assert sha(live) == old and sha(candidate) == new
    os.replace(candidate, live)
    assert sha(live) == new
    with (OUT/'logs/operations.log').open('a') as log:
        log.write(f'{datetime.now().astimezone().isoformat()} prior deployment job={os.environ["SLURM_JOB_ID"]}: {relative} {old} -> {new}; checked backup={backup}\n')
    print(f'deployed {relative} {new}', flush=True)


if __name__ == '__main__':
    assert os.environ.get('SLURM_JOB_ID'), 'Slurm required'
    os.umask(0o077)
    assert sha(OUT/'aln34/E34_PUBLIC_PRIOR_EXECUTION_RECORD.md') == '07466ebce053d1886baf093510aa8e4990818067d1193f5628152fc46b28af03'
    deploy('registry', 'auditory_alignment_v3/registry.py')
    deploy('run', 'auditory_alignment_v3/run.py')
    deploy('ckpt_offload', 'private/auditory_alignment_v3/ckpt_offload.py')
    print('STAGE1 PASS; old offload daemon must stop and be replaced before plan apply', flush=True)
