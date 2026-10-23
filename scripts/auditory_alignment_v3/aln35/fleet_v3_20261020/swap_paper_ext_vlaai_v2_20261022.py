"""Swap the VLAAI lane provider shim v1 -> v2 (dependency-scoped swap-check correction; ext_vlaai_v2), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
OLD, NEW, SB = 'auditory_alignment_v3.aln35.paper_ext_vlaai_fleet', 'auditory_alignment_v3.aln35.paper_ext_vlaai_fleet_v2', 'slurm/aln35_paper_ext_vlaai_v2.sbatch'
value = json.loads(REG.read_text()); i = next(k for k, p in enumerate(value['plugins']) if p['module'] == OLD)
m = importlib.import_module(NEW); st = m.fleet_status()
assert st['name'] == value['plugins'][i]['name'] == 'c3_s35pxvla' and st['lane'] == value['plugins'][i]['lane'] and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and '#SBATCH --job-name=c3_s35pxvla' in (ROOT / SB).read_text().splitlines()
corr = ROOT / 'private/auditory_alignment_v3/paper/external_decoders/vlaai_v2/CORRECTION_RECEIPT.json'; assert corr.exists()
backup = REG.with_name(f'fleet_plugins_before_vlaai_v2_swap_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
replaced = value['plugins'][i]; value['plugins'][i] = dict(module=NEW, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'replaced': replaced, 'new': value['plugins'][i], 'backup': str(backup),
       'reason': 'v1 swap-antisymmetry check compared float32 recomputation with float64 margins (false check_failed on PXVLA_b71adaac1426b919); v2 checks the same float64 arrays; see CORRECTION_RECEIPT.json',
       'correction_receipt_sha256': sha(corr), 'readiness': {k: st[k] for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
       'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/paper/ext_vlaai_v2.py', 'auditory_alignment_v3/aln35/paper_ext_vlaai_fleet_v2.py', SB)}}
out = Path(__file__).with_name(f'swap_paper_ext_vlaai_v2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(rec, indent=1) + '\n')
print(json.dumps({k: rec[k] for k in ('status', 'new', 'readiness')}, indent=1))
