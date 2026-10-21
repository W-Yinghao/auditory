"""Replace the aln41_r2_fleet registry entry with aln41_r2_fleet_v2 (resumable private CE runner), with validation and receipt.

Reason: runfill preemption restarts the non-resumable R2 private CE fits from epoch 0 (ptcs / ptnc / pb0 requeued repeatedly on
2026-10-21; seed 3407 13/15 and seed 3413 0/15 fits complete at the swap). The v2 shim keeps the source and frozen items
byte-for-byte; the private items get new names / sbatch files and wait for the resume validation smoke. Old-path jobs already
running keep their claims and finish or requeue under the old code; both paths share the claims/<id>.lock files.
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
OLD, NEW = 'auditory_alignment_v3.aln35.aln41_r2_fleet', 'auditory_alignment_v3.aln35.aln41_r2_fleet_v2'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
OLD_PRIV = {'c3_s35r2a41pb0': 'c3_s35r2a41qb0', 'c3_s35r2a41ptcs': 'c3_s35r2a41qtcs', 'c3_s35r2a41ptnc': 'c3_s35r2a41qtnc'}

old = importlib.import_module(OLD).fleet_status()
new_mod = importlib.import_module(NEW); new = new_mod.fleet_status()
oth_old = [i for i in old if i['name'] not in OLD_PRIV]; oth_new = [i for i in new if i['name'] not in OLD_PRIV.values()]
assert oth_old == oth_new, (oth_old, oth_new)
pv_old = {i['name']: i for i in old if i['name'] in OLD_PRIV}; pv_new = {i['name']: i for i in new if i['name'] in OLD_PRIV.values()}
assert set(pv_new) == set(OLD_PRIV.values())
for o, n in OLD_PRIV.items():
    assert pv_old[o]['lane'] == pv_new[n]['lane'] and pv_old[o]['remaining'] == pv_new[n]['remaining'], (pv_old[o], pv_new[n])
for item in new:
    assert item['name'].startswith('c3_s35') and item['lane'].startswith('s35_') and 1 <= item['slots'] <= 2 and item.get('initial', []) == []
    if item['state'] == 'ready' and item['ready']:
        assert item['submit'][0].startswith('slurm/aln35_') and item['submit'][0].endswith('.sbatch') and (ROOT / item['submit'][0]).exists()
for n in OLD_PRIV.values():
    tag = n[len('c3_s35r2a41q'):]
    lines = (ROOT / f'slurm/aln35_r2a41_private_resume_{tag}.sbatch').read_text().splitlines()
    assert f'#SBATCH --job-name={n}' in lines and any('aln41.r2_private_resume' in l for l in lines)

value = json.loads(REG.read_text())
idx = [k for k, p in enumerate(value['plugins']) if p['module'] == OLD]; assert len(idx) == 1
backup = REG.with_name(f'fleet_plugins_before_aln41_r2_v2_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(REG, backup)
entry = dict(module=NEW, sha256=sha(new_mod.__file__), name=value['plugins'][idx[0]]['name'], lane=value['plugins'][idx[0]]['lane'])
replaced = value['plugins'][idx[0]]; value['plugins'][idx[0]] = entry
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'replaced': replaced, 'entry': entry, 'backup': str(backup),
           'private_items_v1': list(pv_old.values()), 'private_items_v2': list(pv_new.values()),
           'shas': {p: sha(ROOT / p) for p in ['auditory_alignment_v3/aln41/' + f + '.py' for f in
                                              ('private_ft', 'r2', 'r2_lanes', 'private_ft_resume', 'r2_private_resume', 'r2_lanes_v2')]
                    + ['auditory_alignment_v3/aln35/aln41_r2_fleet_v2.py']
                    + [f'slurm/aln35_r2a41_private_resume_{t}.sbatch' for t in ('b0', 'tcs', 'tnc')]}}
out = Path(__file__).with_name(f'swap_aln41_r2_private_resume_{os.environ["SLURM_JOB_ID"]}.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps({'private_items_v1': receipt['private_items_v1'], 'private_items_v2': receipt['private_items_v2']}, indent=1))
