"""Insert the DEP12 source-learning shims (E0 lane c3_s35dSe0, production lane c3_s35dSprd) into the coordinator registry right
AFTER the batch-1 REVE lanes (c3_s35pereveB), i.e. ahead of W7 and DEP12 public lanes: source training is the critical path of
the researcher's latest direction (DEP12 package v1.2, "坚持推动项目"). Backup + receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MODS = ['auditory_alignment_v3.aln35.dep12_src_e0_fleet', 'auditory_alignment_v3.aln35.dep12_src_prod_fleet']
value = json.loads(REG.read_text()); order_before = [p['name'] for p in value['plugins']]
entries, states = [], {}
for mod in MODS:
    m = importlib.import_module(mod); st = m.fleet_status(); states[st['name']] = st
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st.get('initial', []) == []
    if st.get('submit'):
        assert st['submit'][0].startswith('slurm/aln35_') and f'#SBATCH --job-name={st["name"]}' in (ROOT / st['submit'][0]).read_text().splitlines()
    assert not any(p['module'] == mod or p['name'] == st['name'] for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']))
i = next(k for k, p in enumerate(value['plugins']) if p['name'] == 'c3_s35pereveB')
backup = REG.with_name(f'fleet_plugins_before_dep12_src_{os.environ["SLURM_JOB_ID"]}_20261023.json'); shutil.copy2(REG, backup)
value['plugins'][i + 1:i + 1] = entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'inserted_after': 'c3_s35pereveB', 'position': i + 1,
       'order_before': order_before, 'order_after': [p['name'] for p in value['plugins']], 'backup': str(backup),
       'readiness': {k: {x: v.get(x) for x in ('state', 'ready', 'remaining', 'slots', 'submit')} for k, v in states.items()},
       'priority_reason': 'DEP12 source training is the critical path of the latest research direction; W7 and DEP12 public lanes follow',
       'authorisation': 'researcher 2026-10-23: DEP12 "完成所有规划的实验 … 你都自己下判断"; "继续监控和之前的工作，坚持推动项目"'}
out = Path(__file__).with_name(f'register_dep12_src_{os.environ["SLURM_JOB_ID"]}_20261023.json'); out.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'position': i + 1, 'readiness': {k: (v['state'], v.get('ready'), v.get('remaining'), v['slots'], v.get('submit')) for k, v in states.items()}}))
