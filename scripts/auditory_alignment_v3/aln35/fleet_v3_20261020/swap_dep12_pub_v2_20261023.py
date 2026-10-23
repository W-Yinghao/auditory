"""Swap the two DEP12 public registry entries v1 -> v2 (coordinator naming convention: lane 's35_*', submit 'slurm/aln35_*'),
with a backup and a receipt. The v1 entries were in technical_error since registration (01:25) because of that convention."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
value = json.loads(REG.read_text()); out_entries = []
for short in ('feat', 'pert'):
    old_mod = f'auditory_alignment_v3.aln35.dep12_pub_{short}_fleet'; new_mod = old_mod + '_v2'
    i = next(k for k, p in enumerate(value['plugins']) if p['module'] == old_mod)
    m = importlib.import_module(new_mod); st = m.fleet_status()
    assert st['name'] == value['plugins'][i]['name'] and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2
    assert st['submit'][0].startswith('slurm/aln35_') and f'#SBATCH --job-name={st["name"]}' in (ROOT / st['submit'][0]).read_text().splitlines()
    out_entries.append({'replaced': dict(value['plugins'][i]), 'new': dict(module=new_mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']),
                        'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')}})
    value['plugins'][i] = out_entries[-1]['new']
backup = REG.with_name(f'fleet_plugins_before_dep12_pub_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'swaps': out_entries, 'backup': str(backup),
       'reason': 'coordinator asserts lane.startswith("s35_") and submit[0].startswith("slurm/aln35_"); v1 reported dep12_* names -> technical_error'}
out = Path(__file__).with_name(f'swap_dep12_pub_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json'); out.write_text(json.dumps(rec, indent=1) + '\n')
print(json.dumps([(e['new']['name'], e['new']['lane'], e['readiness']['state'], e['readiness']['submit']) for e in out_entries]))
