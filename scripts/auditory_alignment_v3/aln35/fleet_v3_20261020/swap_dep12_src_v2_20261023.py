"""Re-bind the DEP12 source shims after Agent S's v2 fix (trainer_v2 / source_tests_v2 / source_fleet_v2: tolerance-based inert
temporal-attention check, TF32 off; the first V100 smoke 1058746 failed on an exact-zero assertion). Same module names, new sha256.
Backup + receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
value = json.loads(REG.read_text()); swaps = []
for mod in ('auditory_alignment_v3.aln35.dep12_src_e0_fleet', 'auditory_alignment_v3.aln35.dep12_src_prod_fleet'):
    i = next(k for k, p in enumerate(value['plugins']) if p['module'] == mod)
    m = importlib.import_module(mod); st = m.fleet_status()
    assert st['name'] == value['plugins'][i]['name'] and st['lane'] == value['plugins'][i]['lane'] and st['lane'].startswith('s35_')
    old = dict(value['plugins'][i]); value['plugins'][i]['sha256'] = sha(m.__file__)
    swaps.append({'module': mod, 'old_sha256': old['sha256'], 'new_sha256': value['plugins'][i]['sha256'],
                  'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')}})
backup = REG.with_name(f'fleet_plugins_before_dep12_src_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'swap_dep12_src_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json')
out.write_text(json.dumps({'status': 'pass', 'swaps': swaps, 'backup': str(backup), 'reason': 'v2 fix after V100 smoke 1058746 failure'}, indent=1) + '\n')
print(json.dumps([(s['module'].split('.')[-1], s['readiness']['state'], s['readiness']['submit']) for s in swaps]))
