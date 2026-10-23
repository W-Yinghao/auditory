"""Append the complete-MindMix shortcut audit shim (aln35.paper_mmdropkey_fleet; frozen PROTOCOL.md / plan.json in
paper/mindmix_dropkey_v1) to the coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, SB = 'auditory_alignment_v3.aln35.paper_mmdropkey_fleet', 'slurm/aln35_paper_mmdropkey.sbatch'
D = 'private/auditory_alignment_v3/paper/mindmix_dropkey_v1/'
EXPECT = {'auditory_alignment_v3/paper/mindmix_dropkey_audit.py': 'c6b7587a8366edfa9fe6aac4fdd613141831f092ad1bab401fda17d315e079a0',
          'auditory_alignment_v3/aln35/paper_mmdropkey_fleet.py': 'a33164dcce112bc0f1cd442d3e8dad9ed50f49205602d6fc96919bb651ccebab',
          SB: '5344195a366bc6d9b6908d7fa862f551ce15064be2d9be1710e35835d5af66ad',
          D + 'PROTOCOL.md': 'be2d1e9c6835bc4c35832483445e27cad8d97b2f5fd867a7100ad06d1b59a6b8',
          D + 'plan.json': '23769dbc01588f05aa7495976fe42bd4ffc99a0820c7de6e73939024e0ea6dde'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == 'c3_s35pmmdk' and st['lane'] == 's35_paper_mmdropkey' and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and f'#SBATCH --job-name={st["name"]}' in (ROOT / SB).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == st['name'] for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
backup = REG.with_name(f'fleet_plugins_before_paper_mmdropkey_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'position': len(value['plugins']) - 1,
           'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
           'authorisation': 'researcher 2026-10-22 ~18:40: "两个都做吧，优先级放在现有实验之后" (complete-MindMix shortcut audit; lowest registry position)',
           'smoke_receipt_sha256': sha(ROOT / D / 'probes/1057860/receipt.json'), 'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_mmdropkey_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entry': entry['name'], 'position': receipt['position'], 'readiness': receipt['readiness']}))
