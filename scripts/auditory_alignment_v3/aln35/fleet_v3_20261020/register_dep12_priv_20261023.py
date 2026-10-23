"""Append the DEP12 private shims (aln35.dep12_priv_feat_fleet = BDF feature units + CPU stages; aln35.dep12_priv_mff_fleet =
MFF second private cohort) to the coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
LANES = [('auditory_alignment_v3.aln35.dep12_priv_feat_fleet', 'd0700b85510cfbc2c1d8ade6351e2ca9b092b2cb462dca0276a3f7dc9c308138', 'c3_s35dPfeat', 's35_dep12_private_features', 'slurm/aln35_dep12_priv_feat.sbatch'),
         ('auditory_alignment_v3.aln35.dep12_priv_mff_fleet', 'e53b48dae5a0f4e3b36eefb27e80af5c81d6d7a564b1685cfe653a29ae3524f0', 'c3_s35dPmff', 's35_dep12_private_mff', 'slurm/aln35_dep12_priv_mff.sbatch')]
value = json.loads(REG.read_text()); entries, states = [], {}
for mod, digest, name, lane, sb in LANES:
    m = importlib.import_module(mod); assert sha(m.__file__) == digest, mod
    st = m.fleet_status(); states[name] = st
    assert st['name'] == name and st['lane'] == lane and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st.get('initial', []) == [] and st['submit'][0] == sb and sb.startswith('slurm/aln35_')
    assert f'#SBATCH --job-name={name}' in (ROOT / sb).read_text().splitlines()
    assert not any(p['module'] == mod or p['name'] == name for p in value['plugins'])
    entries.append(dict(module=mod, sha256=digest, name=name, lane=lane))
backup = REG.with_name(f'fleet_plugins_before_dep12_priv_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup),
           'readiness': {k: {x: v.get(x) for x in ('state', 'ready', 'remaining', 'slots', 'submit')} for k, v in states.items()},
           'authorisation': 'researcher 2026-10-23: DEP12 package v1.2 "完成所有规划的实验 … 你都自己下判断"; lowest registry position',
           'sbatch_sha256': {sb: sha(ROOT / sb) for *_, sb in LANES}}
out = Path(__file__).with_name(f'register_dep12_priv_{os.environ["SLURM_JOB_ID"]}_20261023.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entries': [e['name'] for e in entries], 'readiness': {k: (v['state'], v.get('ready'), v.get('remaining'), v['slots']) for k, v in states.items()}}))
