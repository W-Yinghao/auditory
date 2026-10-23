"""Append the W7 audit-A shim (aln35.paper_w7_audit_fleet; frozen W7 design + APPENDUM_RAD_03/04) to the coordinator registry,
last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, SB, NAME, LANE = 'auditory_alignment_v3.aln35.paper_w7_audit_fleet', 'slurm/aln35_paper_w7_audit.sbatch', 'c3_s35pw7audit', 's35_paper_w7_audit'
W = 'private/auditory_alignment_v3/paper/w7_v1/'
EXPECT = {'auditory_alignment_v3/paper/w7_audit.py': 'e14c76469929bfccfd9b84611f064e159adc37dc64c32e244fa6c90b5b6544af',
          'auditory_alignment_v3/aln35/paper_w7_audit_fleet.py': '49d85e14219dcd7be04c9375ba529cd37d5aab1dd07aff879afb2299ee7c205b',
          SB: '33dbce397a762022373acb8d24ff88728eaa50eef17bad7b84749a86cff4839d',
          W + 'audit/plan.json': 'a5e03fc77fa5f21ff2b1ee525eb7f83a2130783541201457e40993d3ec87e29c',
          W + 'APPENDUM_RAD_03.md': '17ad09670d231da01b32cc0f2f4c7ddece98d281dd56db8338d0e4a091620175',
          W + 'APPENDUM_RAD_04.md': 'd8ee2fac45ee11b185491403937f9f883b1e662f30d8c54ae788a467a3506901',
          'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md': 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == NAME and st['lane'] == LANE and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and f'#SBATCH --job-name={NAME}' in (ROOT / SB).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == NAME for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=NAME, lane=LANE)
backup = REG.with_name(f'fleet_plugins_before_paper_w7_audit_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'position': len(value['plugins']) - 1,
           'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
           'authorisation': 'researcher 2026-10-22: W7 approved ("你建议的都做，你自己拿主意"; "必须CCS，其余的按你推荐的来"); frozen W7 design 19:48',
           'smoke_receipt_sha256': sha(ROOT / W / 'audit/probes/1057962/receipt.json'), 'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_w7_audit_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entry': NAME, 'position': receipt['position'], 'readiness': receipt['readiness']}))
