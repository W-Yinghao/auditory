"""Swap the DEP12 private registry entries to Agent P's v2 shims (encoders_v2 extension arms; new module names), with a backup
and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {'dep12_priv_feat_fleet_v2': ('9579b2a9eddad18527077ec9c129d29107443ad8673e1a874f1114adbd288791', 'slurm/aln35_dep12_priv_feat_v2.sbatch'),
          'dep12_priv_mff_fleet_v2': ('281ffdde2f76c0e15192e07d76cbe6ffd0e1fd88ce2b3fe3acf4e71cb9fab723', 'slurm/aln35_dep12_priv_mff_v2.sbatch')}
value = json.loads(REG.read_text()); swaps = []
for new, (digest, sb) in EXPECT.items():
    old_mod = 'auditory_alignment_v3.aln35.' + new.replace('_v2', ''); new_mod = 'auditory_alignment_v3.aln35.' + new
    i = next(k for k, p in enumerate(value['plugins']) if p['module'] == old_mod)
    m = importlib.import_module(new_mod); assert sha(m.__file__) == digest
    st = m.fleet_status()
    assert st['name'] == value['plugins'][i]['name'] and st['lane'] == value['plugins'][i]['lane'] and st['lane'].startswith('s35_')
    assert 1 <= st['slots'] <= 2 and st.get('initial', []) == [] and sb.startswith('slurm/aln35_')
    assert f'#SBATCH --job-name={st["name"]}' in (ROOT / sb).read_text().splitlines()
    if st.get('submit'):
        assert st['submit'][0] == sb
    swaps.append({'replaced': dict(value['plugins'][i]), 'new_module': new_mod, 'state': st['state']})
    value['plugins'][i] = dict(module=new_mod, sha256=digest, name=st['name'], lane=st['lane'])
backup = REG.with_name(f'fleet_plugins_before_dep12_priv_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
out = Path(__file__).with_name(f'swap_dep12_priv_v2_{os.environ["SLURM_JOB_ID"]}_20261023.json')
out.write_text(json.dumps({'status': 'pass', 'swaps': swaps, 'backup': str(backup), 'reason': 'extension arms via encoders_v2 (Agent P v2 modules)'}, indent=1) + '\n')
print(json.dumps([(s['new_module'].split('.')[-1], s['state']) for s in swaps]))
