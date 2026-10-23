"""Append the paper-line common-backbone arm shims (aln35.paper_arms_fleet_{a,b,z}) to the coordinator registry, last, with a receipt."""
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
value = json.loads(REG.read_text()); entries = []
for lane in 'abz':
    mod = f'auditory_alignment_v3.aln35.paper_arms_fleet_{lane}'
    m = importlib.import_module(mod); st = m.fleet_status()
    assert st['name'].startswith('c3_s35') and st['lane'].startswith('s35_') and st['slots'] in (1, 2) and st['initial'] == []
    sb = {'a': 'slurm/aln35_paper_arms_src_a.sbatch', 'b': 'slurm/aln35_paper_arms_src_b.sbatch', 'z': 'slurm/aln35_paper_arms_frozen.sbatch'}[lane]
    assert f'#SBATCH --job-name={st["name"]}' in (ROOT / sb).read_text().splitlines()
    if st['state'] == 'ready' and st['ready']:
        assert st['submit'][0] == sb
    assert not any(p['module'] == mod or p['name'] == st['name'] for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=st['name'], lane=st['lane']))
backup = REG.with_name(f'fleet_plugins_before_paper_arms_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup),
           'authorisation': 'researcher 2026-10-22: W4 approved; manuscript v2 "补全所有差的实验"',
           'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/paper/arms.py', 'auditory_alignment_v3/paper/temporal_hsic_torch.py',
                                              'slurm/aln35_paper_arms_src_a.sbatch', 'slurm/aln35_paper_arms_src_b.sbatch',
                                              'slurm/aln35_paper_arms_frozen.sbatch')}}
out = Path(__file__).with_name(f'register_paper_arms_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1) + '\n')
print(json.dumps(receipt, indent=1))
