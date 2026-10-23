"""Swap the completed CALRA lane entry (paper_calra_fleet, state complete) for the W5 audit v2 shim (train-mode scoring added after
the dropout-key shortcut diagnosis), same job name c3_s35calra, with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
OLD, NEW, SB = 'auditory_alignment_v3.aln35.paper_calra_fleet', 'auditory_alignment_v3.aln35.paper_calra_audit2_fleet', 'slurm/aln35_paper_calra_audit2.sbatch'
value = json.loads(REG.read_text()); i = next(k for k, p in enumerate(value['plugins']) if p['module'] == OLD)
old_st = importlib.import_module(OLD).fleet_status(); assert old_st['state'] == 'complete', old_st
m = importlib.import_module(NEW); st = m.fleet_status()
assert st['name'] == value['plugins'][i]['name'] == 'c3_s35calra' and st['lane'] == 's35_paper_calra_audit2' and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and '#SBATCH --job-name=c3_s35calra' in (ROOT / SB).read_text().splitlines()
corr = ROOT / 'private/auditory_alignment_v3/paper/calra_v1/audit_v2/CORRECTION_RECEIPT.json'; assert corr.exists()
backup = REG.with_name(f'fleet_plugins_before_calra_audit2_swap_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
replaced = value['plugins'][i]; value['plugins'][i] = dict(module=NEW, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'replaced': replaced, 'replaced_state': 'complete', 'new': value['plugins'][i], 'backup': str(backup),
       'reason': 'W5 audit v2: eval-mode CALRA representations are constant (v1 correct); train-mode scoring added to expose the dropout-key shortcut (training ClipLoss ~0.001 with identical/noise inputs)',
       'correction_receipt_sha256': sha(corr), 'readiness': {k: st[k] for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
       'shas': {p: sha(ROOT / p) for p in ('auditory_alignment_v3/paper/calra_audit_v2.py', 'auditory_alignment_v3/aln35/paper_calra_audit2_fleet.py', SB,
                                          'private/auditory_alignment_v3/paper/calra_v1/audit_v2/plan.json')}}
out = Path(__file__).with_name(f'swap_paper_calra_audit2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(rec, indent=1) + '\n')
print(json.dumps({k: rec[k] for k in ('status', 'new', 'readiness')}))
