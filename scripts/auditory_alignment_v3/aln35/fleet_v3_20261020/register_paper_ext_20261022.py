"""Append the paper-line Table 2 external-decoder shims (aln35.paper_ext_{vlaai,mmfau,clip}_fleet; manuscript v2 Table 2) to the
coordinator registry, last, with a backup and a receipt. CLIP production stays gated on the researcher's route approval file."""
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
SB = {'vlaai': 'slurm/aln35_paper_ext_vlaai.sbatch', 'mmfau': 'slurm/aln35_paper_ext_mmfau.sbatch', 'clip': 'slurm/aln35_paper_ext_clip.sbatch'}
assert not (ROOT / 'private/auditory_alignment_v3/paper/external_decoders/clip/ROUTE_APPROVED.json').exists()
value = json.loads(REG.read_text()); entries, states = [], {}
for lane in ('vlaai', 'mmfau', 'clip'):
    mod = f'auditory_alignment_v3.aln35.paper_ext_{lane}_fleet'
    m = importlib.import_module(mod); st = m.fleet_status(); states[lane] = st
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and 1 <= st['slots'] <= 2 and st['initial'] == []
    assert f'#SBATCH --job-name={st["name"]}' in (ROOT / SB[lane]).read_text().splitlines()
    if st['state'] == 'ready' and st['ready']:
        assert st['submit'][0] == SB[lane]
    assert not any(p['module'] == mod or p['name'] == st['name'] for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']))
backup = REG.with_name(f'fleet_plugins_before_paper_ext_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
files = ['ext_common', 'ext_fleet', 'vlaai_torch', 'ext_mtrf', 'ext_vlaai', 'ext_clip', 'mindmix_fau', 'external_decoders']
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup),
           'readiness': {k: {x: v[x] for x in ('state', 'ready', 'slots', 'submit')} for k, v in states.items()},
           'authorisation': 'researcher 2026-10-22: manuscript v2 "补全所有差的实验" (Table 2 rows VLAAI, MindMix FAU, Transformer-CLIP; CLIP production gated on researcher route approval)',
           'shas': {**{f'auditory_alignment_v3/paper/{f}.py': sha(ROOT / f'auditory_alignment_v3/paper/{f}.py') for f in files}, **{v: sha(ROOT / v) for v in SB.values()}}}
out = Path(__file__).with_name(f'register_paper_ext_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps({'entries': [e['name'] for e in entries], 'readiness': receipt['readiness']}, indent=1))
