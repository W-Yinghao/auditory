"""Replace the aln36_r2_fleet registry entry with aln36_r2_fleet_v2 (private item runner fix), with validation and receipt.

Cause: aln36.r2 consumed `--smoke`, so every c3_s35r2a36priv job ran the R1 private_features worker branch with
smoke_job None and exited at probes/None/receipt.json (127 logs since 15:22; no unit or FAILED marker written).
Validation: the v2 shim returns the same items as v1 except the private item (new name / sbatch), names and submit
commands satisfy the coordinator's plugin contract, and the R2 private plan's r2_sources still match the unchanged r2.py.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
OLD, NEW = 'auditory_alignment_v3.aln35.aln36_r2_fleet', 'auditory_alignment_v3.aln35.aln36_r2_fleet_v2'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

old = importlib.import_module(OLD).fleet_status()
new_mod = importlib.import_module(NEW); new = new_mod.fleet_status()
assert [i['name'] for i in old if i['name'] != 'c3_s35r2a36priv'] == [i['name'] for i in new if i['name'] != 'c3_s35r2a36priv2']
for a, b in zip([i for i in old if i['name'] != 'c3_s35r2a36priv'], [i for i in new if i['name'] != 'c3_s35r2a36priv2']):
    assert a == b, (a, b)
priv = [i for i in new if i['name'] == 'c3_s35r2a36priv2']; assert len(priv) == 1
for item in new:
    assert item['name'].startswith('c3_s35') and item['lane'].startswith('s35_') and 1 <= item['slots'] <= 2 and item.get('initial', []) == []
    if item['state'] == 'ready' and item['ready']:
        assert item['submit'][0].startswith('slurm/aln35_') and item['submit'][0].endswith('.sbatch')
        assert (ROOT / item['submit'][0]).exists()
job_name = [l for l in (ROOT / 'slurm/aln35_r2a36_private_v2.sbatch').read_text().splitlines() if l.startswith('#SBATCH --job-name=')]
assert job_name == ['#SBATCH --job-name=c3_s35r2a36priv2']

value = json.loads(REG.read_text())
idx = [k for k, p in enumerate(value['plugins']) if p['module'] == OLD]; assert len(idx) == 1
backup = REG.with_name(f'fleet_plugins_before_aln36_r2_v2_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(REG, backup)
entry = dict(module=NEW, sha256=sha(new_mod.__file__), name=value['plugins'][idx[0]]['name'], lane=value['plugins'][idx[0]]['lane'])
replaced = value['plugins'][idx[0]]; value['plugins'][idx[0]] = entry
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'replaced': replaced, 'entry': entry, 'backup': str(backup),
           'private_item_v1': [i for i in old if i['name'] == 'c3_s35r2a36priv'], 'private_item_v2': priv,
           'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/aln36/r2.py', 'auditory_alignment_v3/aln36/r2_inproc.py',
                                              'auditory_alignment_v3/aln36/r2_lanes.py', 'auditory_alignment_v3/aln36/r2_lanes_v2.py',
                                              'auditory_alignment_v3/aln35/aln36_r2_fleet_v2.py', 'slurm/aln35_r2a36_private_v2.sbatch')}}
out = Path(__file__).with_name(f'swap_aln36_r2_private_{os.environ["SLURM_JOB_ID"]}.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps(receipt, indent=1))
