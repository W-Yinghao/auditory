"""Append the complete-MindMix audit APPENDUM 01 shim (per-encoder splitAll; aln35.paper_mmdropkey_a1_fleet; frozen APPENDUM_01.md / plan_v2_appendum.json in
paper/mindmix_dropkey_v1) to the coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, SB = 'auditory_alignment_v3.aln35.paper_mmdropkey_a1_fleet', 'slurm/aln35_paper_mmdropkey_a1.sbatch'
D = 'private/auditory_alignment_v3/paper/mindmix_dropkey_v1/'
EXPECT = {'auditory_alignment_v3/paper/mindmix_dropkey_audit_a1.py': '3b8e0676a5d8b50f71a0b93ae9709d74c85fe822faa104729eb974edfb304637',
          'auditory_alignment_v3/paper/mindmix_dropkey_audit.py': 'c6b7587a8366edfa9fe6aac4fdd613141831f092ad1bab401fda17d315e079a0',
          'auditory_alignment_v3/aln35/paper_mmdropkey_a1_fleet.py': '485620262d41d73dd1488dae5edae98d0f2d083b39572c424ae5ae7da72be8bb',
          SB: '03aea3430737867be389d32c24bcc72bea55ed83d70306943920d582798f5076',
          D + 'APPENDUM_01.md': 'eb1442929cf3ff928cbba08a8510c27716b3611275f2bb05867c3c721e858851',
          D + 'plan_v2_appendum.json': '04c70364bd7e3c297d4078fe52f8f0d631fcdcbaa59ab995639bfed95813537e'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == 'c3_s35pmmda1' and st['lane'] == 's35_paper_mmdropkey_a1' and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and f'#SBATCH --job-name={st["name"]}' in (ROOT / SB).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == st['name'] for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
backup = REG.with_name(f'fleet_plugins_before_paper_mmdropkey_a1_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'position': len(value['plugins']) - 1,
           'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
           'authorisation': 'researcher 2026-10-22 ~18:40: "两个都做吧，优先级放在现有实验之后" (complete-MindMix shortcut audit) + 19:50 "你建议的都做" (appendum 01 per-encoder split; lowest registry position)',
           'smoke_receipt_sha256': sha(ROOT / D / 'appendum_01/probes/1057905/receipt.json'), 'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_mmdropkey_a1_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entry': entry['name'], 'position': receipt['position'], 'readiness': receipt['readiness']}))
