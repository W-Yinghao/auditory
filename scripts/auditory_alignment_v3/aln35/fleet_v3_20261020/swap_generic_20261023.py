"""Generic registry swap (2026-10-23): replace registry entries OLD_MODULE -> NEW_MODULE (NEW must be a new module name; the
coordinator never reloads shims), verifying the new shim's sha256, name/lane identity and the coordinator conventions, with a backup
and a receipt.

usage: python swap_generic_20261023.py TAG OLD_MODULE=NEW_MODULE=NEW_SHA256 [OLD=NEW=SHA ...]   (Slurm)
"""
import hashlib, importlib, json, os, shutil, sys
from datetime import datetime
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
tag, specs = sys.argv[1], [a.split('=') for a in sys.argv[2:]]
value = json.loads(REG.read_text()); swaps = []
for old, new, digest in specs:
    old_mod, new_mod = 'auditory_alignment_v3.aln35.' + old, 'auditory_alignment_v3.aln35.' + new
    assert old_mod != new_mod and not any(p['module'] == new_mod for p in value['plugins'])
    i = next(k for k, p in enumerate(value['plugins']) if p['module'] == old_mod)
    m = importlib.import_module(new_mod); assert sha(m.__file__) == digest, f'{new}: sha mismatch'
    st = m.fleet_status()
    assert st['name'] == value['plugins'][i]['name'] and st['lane'] == value['plugins'][i]['lane'], (st['name'], st['lane'])
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st.get('initial', []) == []
    if st.get('submit'):
        sb = st['submit'][0]
        assert sb.startswith('slurm/aln35_') and sb.endswith('.sbatch') and f'#SBATCH --job-name={st["name"]}' in (ROOT / sb).read_text().splitlines()
    swaps.append({'replaced': dict(value['plugins'][i]), 'new': dict(module=new_mod, sha256=digest, name=st['name'], lane=st['lane']),
                  'state': st['state'], 'submit': st.get('submit')})
    value['plugins'][i] = swaps[-1]['new']
backup = REG.with_name(f'fleet_plugins_before_{tag}_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(REG, backup)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'swap_{tag}_{os.environ["SLURM_JOB_ID"]}.json')
out.write_text(json.dumps({'status': 'pass', 'tag': tag, 'time': datetime.now().astimezone().isoformat(), 'swaps': swaps, 'backup': str(backup)}, indent=1) + '\n')
print(json.dumps([(s['new']['module'].split('.')[-1], s['state']) for s in swaps]))
