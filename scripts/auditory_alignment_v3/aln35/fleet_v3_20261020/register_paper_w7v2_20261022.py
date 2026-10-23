"""Append the W7 v2 GPU-arm shims (aln35.paper_w7v2_fleet_{a,b,z}; frozen W7 design + APPENDUM_01..04; v2 smoke 1058102 pass;
PRES beta selected by calibration job 1058200) to the coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
W = 'private/auditory_alignment_v3/paper/w7_v1/'
LANES = {'a': ('c3_s35pw7v2A', 's35_paper_w7v2_src_a', 'slurm/aln35_paper_w7v2_src_a.sbatch'),
         'b': ('c3_s35pw7v2B', 's35_paper_w7v2_src_b', 'slurm/aln35_paper_w7v2_src_b.sbatch'),
         'z': ('c3_s35pw7v2Z', 's35_paper_w7v2_frozen', 'slurm/aln35_paper_w7v2_frozen.sbatch')}
EXPECT = {'auditory_alignment_v3/paper/w7_objectives.py': 'ae209695c4382070090ca89a7c9e18b717b3acae4917f26023565524a8782cb3',
          'auditory_alignment_v3/paper/w7_arms_v2.py': 'c382c8a3ef5aae47226bbc556a278758b5363c7e16126c2188029e7933c00783',
          'auditory_alignment_v3/aln35/paper_w7v2_fleet_a.py': '4756fd3824274856a269d6ba2d13218700d0844e5e3c3f65742f6546482e1104',
          'auditory_alignment_v3/aln35/paper_w7v2_fleet_b.py': '5ad570d91b83cf4a328f3118c96ffc0f7835863006adcc5a9cfe0a5bff6709ab',
          'auditory_alignment_v3/aln35/paper_w7v2_fleet_z.py': 'c19e76eb30cd88b758c665fae9b7015f3785cfb4b3c49ad84feaf6792a2000e0',
          'slurm/aln35_paper_w7v2_src_a.sbatch': 'b136b60afd544e767e4719d6754092a12fb7f037f64fdd547453a317656f5393',
          'slurm/aln35_paper_w7v2_src_b.sbatch': '40b1f124312303af64d8ad0197e9d7d55df7391069228e491bd711edeb4cd239',
          'slurm/aln35_paper_w7v2_frozen.sbatch': '5836fd86636bb5c09570f1883c228e095cd9d38977468792d14ef460055bca30',
          W + 'APPENDUM_01.md': '3a0793ff660415cdd1376c366e8951856bfc294078042502771eed7f9097b44b',
          W + 'APPENDUM_02.md': '945cf00410a82898aac925748d7f62a2c5cc7aa431ca4943442b2a234731dae7',
          W + 'APPENDUM_03.md': 'd3db5a7402530ee61ab8697e629bdd4f5b8486e38ca60db5cce0b44e571634f7',
          W + 'APPENDUM_04.md': '32eae5256f12a3d8caf526c1843d22a86f902f8488ad5be517018434d37121e3',
          'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md': 'c4b461b0a6754af0ba04720320b0acc3f8c907a37f90369a4a250a612a92746c'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
smoke = json.loads((ROOT / W / 'arms_v2/probes/1058102/receipt.json').read_text()); assert smoke['status'] == 'pass'
sel = json.loads((ROOT / W / 'arms_v2/TCS_PRES/seed3401/source_v1/selection.json').read_text()); assert sel['choice']['TCS_PRES']['status'] == 'selected'
value = json.loads(REG.read_text()); entries, states = [], {}
for k, (name, lane, sb) in LANES.items():
    mod = f'auditory_alignment_v3.aln35.paper_w7v2_fleet_{k}'
    m = importlib.import_module(mod); st = m.fleet_status(); states[k] = st
    assert st['name'] == name and st['lane'] == lane and 1 <= st['slots'] <= 2 and st['submit'][0] == sb
    assert f'#SBATCH --job-name={name}' in (ROOT / sb).read_text().splitlines()
    assert not any(p['module'] == mod or p['name'] == name for p in value['plugins'])
    entries.append(dict(module=mod, sha256=sha(m.__file__), name=name, lane=lane))
backup = REG.with_name(f'fleet_plugins_before_paper_w7v2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'] += entries
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entries': entries, 'backup': str(backup),
           'readiness': {k: {x: v.get(x) for x in ('state', 'ready', 'remaining', 'slots', 'submit')} for k, v in states.items()},
           'pres_beta': sel['choice']['TCS_PRES']['beta'], 'pres_beta_note': 'selected beta is the upper end of the frozen grid {0.1, 0.3, 1.0}; grid not extended (frozen rule)',
           'smoke_receipt_sha256': sha(ROOT / W / 'arms_v2/probes/1058102/receipt.json'),
           'selection_sha256': sha(ROOT / W / 'arms_v2/TCS_PRES/seed3401/source_v1/selection.json'),
           'authorisation': 'researcher 2026-10-22: W7 approved ("你建议的都做，你自己拿主意"; "必须CCS，其余的按你推荐的来"); frozen W7 design 19:48',
           'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_w7v2_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entries': [e['name'] for e in entries], 'readiness': {k: (v['state'], v['ready'], v['remaining'], v['slots']) for k, v in states.items()}, 'beta': receipt['pres_beta']}))
