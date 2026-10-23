"""Append the paper-line W5 shim (aln35.paper_calra_fleet: MindMix alignment recipe on the common CBraMod backbone, manuscript
Table 6) to the coordinator registry, last, with a backup and a receipt."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
NEW = 'auditory_alignment_v3.aln35.paper_calra_fleet'
SB = 'slurm/aln35_paper_calra.sbatch'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
m = importlib.import_module(NEW); st = m.fleet_status()
assert st['name'] == 'c3_s35calra' and st['lane'].startswith('s35_') and st['slots'] in (1, 2) and st['initial'] == []
assert st['state'] == 'ready' and st['submit'][0] == SB and (ROOT / SB).exists()
assert '#SBATCH --job-name=c3_s35calra' in (ROOT / SB).read_text().splitlines()
value = json.loads(REG.read_text())
assert not any(p['module'] == NEW or p['name'] == st['name'] for p in value['plugins'])
backup = REG.with_name(f'fleet_plugins_before_paper_calra_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
entry = dict(module=NEW, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'readiness': st,
           'authorisation': 'researcher 2026-10-22: W5 approved; manuscript v2 Table 6 row "MindMix alignment recipe"',
           'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/paper/calra_cbramod.py', 'auditory_alignment_v3/aln35/paper_calra_fleet.py', SB,
                                              'private/auditory_alignment_v3/paper/calra_v1/plan.json')}}
out = Path(__file__).with_name(f'register_paper_calra_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps(receipt, indent=1))
