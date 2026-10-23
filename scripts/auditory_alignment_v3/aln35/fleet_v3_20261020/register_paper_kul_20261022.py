"""Append the paper-line W6 KUL MindMix shims (aln35.paper_kul_fleet_{a,b}; revision 01: P1 x 5 folds + P2 folds 0-1) to the
coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
SB = {'a': 'slurm/aln35_paper_kul_a.sbatch', 'b': 'slurm/aln35_paper_kul_b.sbatch'}
value = json.loads(REG.read_text()); entries, states = [], {}
for lane in 'ab':
    mod = f'auditory_alignment_v3.aln35.paper_kul_fleet_{lane}'
    m = importlib.import_module(mod); st = m.fleet_status(); states[lane] = st
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st['initial'] == []
    assert st['state'] == 'ready' and st['submit'][0] == SB[lane]
    assert f'#SBATCH --job-name={st["name"]}' in (ROOT / SB[lane]).read_text().splitlines()
    assert not any(p['module'] == mod or p['name'] == st['name'] for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']))
backup = REG.with_name(f'fleet_plugins_before_paper_kul_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
K = 'private/auditory_alignment_v3/paper/kul_v1/'
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup),
           'readiness': {k: {x: v[x] for x in ('state', 'ready', 'remaining', 'slots', 'submit')} for k, v in states.items()},
           'authorisation': 'researcher 2026-10-22: W6 "KUL download + attack" approved (~20 GPU-h); revision 01 keeps P2 at folds 0-1 (21.3 GPU-h projected)',
           'shas': {p: sha(ROOT / p) for p in ['auditory_alignment_v3/paper/kul_mindmix.py', *SB.values(), K + 'KUL_MINDMIX_BINDING.json',
                                              K + 'KUL_MINDMIX_REVISION_01.json', K + 'plan_v2.json', K + 'probes/1056232/receipt.json']}}
out = Path(__file__).with_name(f'register_paper_kul_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps({'entries': [e['name'] for e in entries], 'readiness': {k: (v['state'], v['ready'], v['slots']) for k, v in states.items()}}))
