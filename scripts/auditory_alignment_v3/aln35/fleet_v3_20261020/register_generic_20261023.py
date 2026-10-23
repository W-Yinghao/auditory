"""Generic append of a NEW lane shim to the end of the registry, verifying sha256 and coordinator conventions, with a backup and a
receipt.  usage: python register_generic_20261023.py TAG MODULE=SHA256 [MODULE=SHA256 ...] --note TEXT   (Slurm)"""
import hashlib, importlib, json, os, shutil, sys
from datetime import datetime
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
args = sys.argv[1:]; note = args[args.index('--note') + 1] if '--note' in args else ''
args = args[:args.index('--note')] if '--note' in args else args
tag, specs = args[0], [a.split('=') for a in args[1:]]
value = json.loads(REG.read_text()); entries = []
for mod, digest in specs:
    m = importlib.import_module('auditory_alignment_v3.aln35.' + mod); assert sha(m.__file__) == digest, mod
    st = m.fleet_status()
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st.get('initial', []) == []
    if st.get('submit'):
        sb = st['submit'][0]; assert sb.startswith('slurm/aln35_') and f'#SBATCH --job-name={st["name"]}' in (ROOT / sb).read_text().splitlines()
    assert not any(p['module'].endswith('.' + mod) or p['name'] == st['name'] for p in value['plugins'])
    entries.append({'entry': dict(module='auditory_alignment_v3.aln35.' + mod, sha256=digest, name=st['name'], lane=st['lane']),
                    'state': st['state'], 'submit': st.get('submit')})
backup = REG.with_name(f'fleet_plugins_before_{tag}_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(REG, backup)
value['plugins'] += [e['entry'] for e in entries]
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'register_{tag}_{os.environ["SLURM_JOB_ID"]}.json')
out.write_text(json.dumps({'status': 'pass', 'tag': tag, 'time': datetime.now().astimezone().isoformat(), 'entries': entries,
                           'backup': str(backup), 'note': note}, indent=1, ensure_ascii=False) + '\n')
print(json.dumps([(e['entry']['name'], e['state']) for e in entries]))
