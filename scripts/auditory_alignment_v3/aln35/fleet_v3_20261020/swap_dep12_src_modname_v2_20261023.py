"""Re-register the DEP12 source shims under NEW module names (byte-identical copies *_v2.py). The coordinator imports a shim
module once and never reloads it (it only re-checks the file sha), so the same-name swap at 02:52 left the stale v1 shim code
running in the coordinator: it evaluated v1 smoke receipts and reported 'engineering_probe_failed'. New names force a fresh import."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
value = json.loads(REG.read_text()); swaps = []
for x in ('e0', 'prod'):
    old_mod = f'auditory_alignment_v3.aln35.dep12_src_{x}_fleet'; new_mod = old_mod + '_v2'
    i = next(k for k, p in enumerate(value['plugins']) if p['module'] == old_mod)
    assert sha(ROOT / f'auditory_alignment_v3/aln35/dep12_src_{x}_fleet.py') == sha(ROOT / f'auditory_alignment_v3/aln35/dep12_src_{x}_fleet_v2.py')
    m = importlib.import_module(new_mod); st = m.fleet_status()
    assert st['name'] == value['plugins'][i]['name'] and st['lane'] == value['plugins'][i]['lane']
    swaps.append({'replaced': dict(value['plugins'][i]), 'new_module': new_mod, 'state': st['state'], 'submit': st.get('submit')})
    value['plugins'][i] = dict(module=new_mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
backup = REG.with_name(f'fleet_plugins_before_dep12_src_modname_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'swap_dep12_src_modname_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json')
out.write_text(json.dumps({'status': 'pass', 'swaps': swaps, 'backup': str(backup)}, indent=1) + '\n')
print(json.dumps([(s['new_module'].split('.')[-1], s['state'], s['submit']) for s in swaps]))
