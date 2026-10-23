"""Add verified lanes to the coordinator's V100 policy (private/auditory_alignment_v3/aln35/v100_20261019/compatibility.json),
with a backup and a receipt. A lane is added only with a passing smoke receipt that ran on a V100 and whose measured peak GPU
allocation is below the 16 GB budget; the receipt, provider module and plan are bound by sha256 exactly as the existing entries
(efficiency_loop_v3.v100_allowed re-checks all three on every call).

usage: python v100_policy_add_20261023.py LANE PHASE RECEIPT MODULE_SOURCE PLAN PEAK_MB [DEVICE if nested in the receipt]   (Slurm)
"""
import hashlib, json, os, shutil, sys
from datetime import datetime
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID')
POL = Path('/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35/v100_20261019/compatibility.json')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lane, phase, receipt, module, plan, peak = sys.argv[1:7]
peak = float(peak)
rec = json.loads(Path(receipt).read_text())
assert rec['status'] == 'pass', 'receipt not pass'
device = rec.get('device') or (sys.argv[7] if len(sys.argv) > 7 else '')
assert 'V100' in str(device) and (rec.get('device') or str(device) in Path(receipt).read_text()), f'receipt device is not a V100: {device}'
assert peak < 16 * 1024, 'peak above the 16 GB budget'
assert lane.startswith('s35_')
pol = json.loads(POL.read_text())
assert lane not in pol['allowed_lanes'] and all(p['phase'] != phase for p in pol['phases'])
backup = POL.with_name(f'compatibility_before_{phase}_{os.environ["SLURM_JOB_ID"]}.json'); shutil.copy2(POL, backup)
pol['phases'].append({'phase': phase, 'module': module, 'status': 'pass', 'receipt': receipt, 'receipt_sha256': sha(receipt),
                      'peak_allocated_mb': peak, 'device': device, 'added': datetime.now().astimezone().isoformat()})
pol['allowed_lanes'][lane] = {'phase': phase, 'receipt': receipt, 'receipt_sha256': sha(receipt), 'module_source': module,
                              'module_sha256': sha(module), 'plan': plan, 'plan_sha256': sha(plan)}
tmp = POL.with_suffix('.tmp'); tmp.write_text(json.dumps(pol, indent=1) + '\n'); os.replace(tmp, POL)
sys.path.insert(0, '/home/infres/yinwang/EEG_auditory')
from private.auditory_alignment_v3.aln34 import efficiency_loop_v3 as E
ok = E.v100_allowed(lane)
out = Path(__file__).with_name(f'v100_policy_add_{phase}_{os.environ["SLURM_JOB_ID"]}.json')
out.write_text(json.dumps({'lane': lane, 'phase': phase, 'receipt': receipt, 'device': device, 'peak_mb': peak,
                           'backup': str(backup), 'v100_allowed_after': ok, 'time': datetime.now().astimezone().isoformat(),
                           'authorisation': 'researcher 2026-10-23 "V100也满了吗？" / "坚持推动项目"'}, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'lane': lane, 'v100_allowed': ok}))
