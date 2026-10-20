"""Validate and extract the supplied ALN3.5 package on a Slurm CPU node."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
OUT = ROOT/'private/auditory_alignment_v3/aln35'
OUT.mkdir(parents=True, exist_ok=True)
OUT.chmod(0o700)
PKG = ROOT/'AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018'
archive = PKG.with_suffix('.zip')
sha = lambda data: hashlib.sha256(data).hexdigest()
members = []
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        p = Path(info.filename)
        assert not p.is_absolute() and '..' not in p.parts
        assert p.parts[0] == PKG.name
        assert not stat.S_ISLNK(info.external_attr >> 16)
        if info.is_dir():
            continue
        data = z.read(info)
        target = ROOT/p
        if target.exists():
            assert target.is_file() and target.read_bytes() == data, str(target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        members.append({'path':str(p), 'bytes':len(data), 'sha256':sha(data)})
record = {'job':os.environ['SLURM_JOB_ID'], 'time_utc':datetime.now(timezone.utc).isoformat(),
          'zip_sha256':sha(archive.read_bytes()), 'members':members,
          'standalone_aln34_sha256':sha((ROOT/'AUDITORY_ALN3_FULL_EXPERIMENTS_SERVER_v3_4_20261016.md').read_bytes()),
          'inherited_aln34_sha256':sha((PKG/'inherited/ALN34_FULL_EXPERIMENTS_SERVER.md').read_bytes())}
(OUT/'package_extraction.json').write_text(json.dumps(record,indent=2)+'\n')
subprocess.run([sys.executable,'-B',str(PKG/'scripts/validate_package.py'),'--package',str(PKG)],check=True)
env = {**os.environ,'PYTHONPATH':str(PKG/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],cwd=PKG,env=env,check=True)
checkout = ROOT/'private/github_publish_032/checkout'
remote = subprocess.check_output(['git','-C',str(checkout),'rev-parse','origin/main'],text=True).strip()
subprocess.run([sys.executable,'-B',str(PKG/'scripts/intake_snapshot.py'),'--repo',str(checkout),
                '--package',str(PKG),'--out',str(OUT/'publication_baseline_intake_20261019.json'),
                '--remote-head',remote],check=True)
record.update(status='PASS', reference_tests_only=True, production_training_performed=False,
              observed_remote_main=remote)
(OUT/'bootstrap_receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='members'}),flush=True)
