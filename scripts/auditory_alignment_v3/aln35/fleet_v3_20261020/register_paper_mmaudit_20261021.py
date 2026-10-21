"""Append the paper-line W2 MindMix audit shim (aln35.paper_mmaudit_fleet) to the coordinator registry, last, with a receipt."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
NEW = 'auditory_alignment_v3.aln35.paper_mmaudit_fleet'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

m = importlib.import_module(NEW); st = m.fleet_status()
assert isinstance(st, dict) and st['name'] == 'c3_s35mmaudit' and st['lane'].startswith('s35_') and st['slots'] == 1 and st['initial'] == []
if st['state'] == 'ready' and st['ready']:
    assert st['submit'][0] == 'slurm/aln35_paper_mmaudit.sbatch' and (ROOT / st['submit'][0]).exists()
assert '#SBATCH --job-name=c3_s35mmaudit' in (ROOT / 'slurm/aln35_paper_mmaudit.sbatch').read_text().splitlines()
value = json.loads(REG.read_text())
assert not any(p['module'] == NEW or p['name'] == st['name'] for p in value['plugins'])
backup = REG.with_name(f'fleet_plugins_before_paper_mmaudit_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(REG, backup)
entry = dict(module=NEW, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'readiness': st,
           'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/paper/mindmix_audit.py', 'auditory_alignment_v3/aln35/paper_mmaudit_fleet.py',
                                              'slurm/aln35_paper_mmaudit.sbatch')}}
out = Path(__file__).with_name(f'register_paper_mmaudit_{os.environ["SLURM_JOB_ID"]}.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps(receipt, indent=1))
