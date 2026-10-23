"""Append the W7 audit-A shim (aln35.paper_w7_adapt_v2_fleet; frozen W7 design + APPENDUM_RAD_03/04) to the coordinator registry,
last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, SB, NAME, LANE = 'auditory_alignment_v3.aln35.paper_w7_adapt_v2_fleet', 'slurm/aln35_paper_w7_adapt_v2.sbatch', 'c3_s35pw7adapt2', 's35_paper_w7_adapt_v2'
W = 'private/auditory_alignment_v3/paper/w7_v1/'
EXPECT = {'auditory_alignment_v3/paper/w7_adapt_v2.py': 'c66bc3818f35243bf675dd858b13cb369650cc53403319464bd45e1e55379df6',
          'auditory_alignment_v3/paper/w7_adapt.py': '1193963e8fd12008f485d0cb9e586dd8e5b08329441802b2763861c467af1ec0',
          'auditory_alignment_v3/aln35/paper_w7_adapt_v2_fleet.py': '00be3017e72034ec2b2b968e7228f63d318cd25f4f15effe1127270f2abaeab4',
          SB: '33b0bd1b4874b485bfbcf8b112b1364d4c8408e5e19a08b4a158749e925065d9',
          W + 'adapt_v2/plan.json': 'e4344748c69885f261dd1e438a0509a94b576adb649298d909030eb1be741f96',
          W + 'APPENDUM_RAD_02.md': '0fbd150f21a629c972ea624bc7b124ca89517a7c2211568d441151d5ddc3167b',
          W + 'APPENDUM_RAD_05.md': 'e2b794626b5770ac5f7b38ed53fc74531601bbb92bc463a067e9014bf5561beb',
          'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md': 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == NAME and st['lane'] == LANE and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and f'#SBATCH --job-name={NAME}' in (ROOT / SB).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == NAME for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=NAME, lane=LANE)
backup = REG.with_name(f'fleet_plugins_before_paper_w7_adapt_v2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'position': len(value['plugins']) - 1,
           'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')},
           'authorisation': 'researcher 2026-10-22: W7 approved ("你建议的都做，你自己拿主意"; "必须CCS，其余的按你推荐的来"); frozen W7 design 19:48',
           'smoke_receipt_sha256': sha(ROOT / W / 'audit/probes/1057962/receipt.json'), 'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_w7_adapt_v2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entry': NAME, 'position': receipt['position'], 'readiness': receipt['readiness']}))
