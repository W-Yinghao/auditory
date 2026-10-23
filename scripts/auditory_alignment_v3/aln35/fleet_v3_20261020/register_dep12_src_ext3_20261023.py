"""Append the DEP12 source extension-3 shim (ssl_continue @3401/3407/3413; plan_ext3_amend1.json) to the registry, after the
DEP12 production lane (ahead of W7 / public / private lanes), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD = 'auditory_alignment_v3.aln35.dep12_src_ext3_fleet'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == 'c3_s35dSx3' and st['lane'] == 's35_dep12_src_ext3' and 1 <= st['slots'] <= 2 and st.get('initial', []) == []
assert st['submit'][0] == 'slurm/aln35_dep12_src_ext3.sbatch' and '#SBATCH --job-name=c3_s35dSx3' in (ROOT / st['submit'][0]).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == st['name'] for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
i = next(k for k, p in enumerate(value['plugins']) if p['name'] == 'c3_s35dSx2')
backup = REG.with_name(f'fleet_plugins_before_dep12_src_ext3_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
value['plugins'].insert(i + 1, entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'register_dep12_src_ext3_{os.environ["SLURM_JOB_ID"]}_20261023.json')
out.write_text(json.dumps({'status': 'pass', 'entry': entry, 'position': i + 1, 'backup': str(backup),
    'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
    'plan_ext3_amend1_sha256': sha(ROOT / 'private/auditory_alignment_v3/dep12/source/plan_ext3_amend1.json'),
    'authorisation': 'DECISIONS 2026-10-23 11:55 + 12:20 follow-up ext3 (researcher autonomy grant)'}, indent=1) + '\n')
print(json.dumps({'entry': entry['name'], 'position': i + 1, 'state': st['state'], 'ready': st['ready']}))
