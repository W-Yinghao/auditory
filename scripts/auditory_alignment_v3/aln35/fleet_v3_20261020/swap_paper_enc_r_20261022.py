"""Swap the REVE lane shim v1 -> v2 (slots clamp) and append the second REVE lane, with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
value = json.loads(REG.read_text())
old = 'auditory_alignment_v3.aln35.paper_enc_fleet_r'
i = next(k for k, p in enumerate(value['plugins']) if p['module'] == old)
v2 = importlib.import_module('auditory_alignment_v3.aln35.paper_enc_fleet_r_v2'); st2 = v2.fleet_status()
rb = importlib.import_module('auditory_alignment_v3.aln35.paper_enc_fleet_r_b'); stb = rb.fleet_status()
assert st2['name'] == value['plugins'][i]['name'] == 'c3_s35pereve' and st2['slots'] <= 2 and stb['slots'] <= 2
assert '#SBATCH --job-name=c3_s35pereveB' in (ROOT / 'slurm/aln35_paper_enc_reve_b.sbatch').read_text().splitlines()
assert not any(p['name'] == 'c3_s35pereveB' for p in value['plugins'])
backup = REG.with_name(f'fleet_plugins_before_paper_enc_r_swap_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
replaced = value['plugins'][i]
value['plugins'][i] = dict(module='auditory_alignment_v3.aln35.paper_enc_fleet_r_v2', sha256=sha(v2.__file__), name=st2['name'], lane=st2['lane'])
value['plugins'].append(dict(module='auditory_alignment_v3.aln35.paper_enc_fleet_r_b', sha256=sha(rb.__file__), name=stb['name'], lane=stb['lane']))
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'replaced': replaced, 'new': value['plugins'][i], 'appended': value['plugins'][-1],
       'reason': 'v1 shim passed slots=3 through; coordinator asserts 1 <= slots <= 2 (maintain_fleet_v2.py:182)', 'backup': str(backup),
       'states': {'R': [st2['state'], st2['ready'], st2['slots']], 'R_b': [stb['state'], stb['ready'], stb['slots']]}}
out = Path(__file__).with_name(f'swap_paper_enc_r_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(rec, indent=1) + '\n'); print(json.dumps(rec, indent=1))
