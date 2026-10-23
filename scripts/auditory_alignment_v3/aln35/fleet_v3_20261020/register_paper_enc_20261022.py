"""Append the paper-line encoder shims (aln35.paper_enc_fleet_{z,r,m}; REVE + MindMix aligned EEG branch, manuscript v2
Tables 3-5) to the coordinator registry, last, with a backup and a receipt."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil

assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory')
REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
SB = {'z': 'slurm/aln35_paper_enc_frozen.sbatch', 'r': 'slurm/aln35_paper_enc_reve.sbatch', 'm': 'slurm/aln35_paper_enc_mmix.sbatch'}
value = json.loads(REG.read_text()); entries, states = [], {}
for lane in 'zrm':
    mod = f'auditory_alignment_v3.aln35.paper_enc_fleet_{lane}'
    m = importlib.import_module(mod); st = m.fleet_status(); states[lane] = st
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and st['slots'] in (1, 2, 3) and st['initial'] == []
    assert f'#SBATCH --job-name={st["name"]}' in (ROOT / SB[lane]).read_text().splitlines()
    if st['state'] == 'ready' and st['ready']:
        assert st['submit'][0] == SB[lane]
    assert not any(p['module'] == mod or p['name'] == st['name'] for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']))
backup = REG.with_name(f'fleet_plugins_before_paper_enc_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup), 'readiness': states,
           'authorisation': 'researcher 2026-10-22: manuscript v2 "补全所有差的实验" (Tables 3-5 rows REVE, MindMix aligned EEG branch)',
           'shas': {p: sha(ROOT / p) for p in ['auditory_alignment_v3/paper/encoders.py', 'auditory_alignment_v3/paper/enc_models.py',
                                              'private/auditory_alignment_v3/paper/encoders_v1/plan.json', *SB.values()]}}
out = Path(__file__).with_name(f'register_paper_enc_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps({'entries': entries, 'states': {k: (v['state'], v['ready'], v['slots']) for k, v in states.items()}}, indent=1))
