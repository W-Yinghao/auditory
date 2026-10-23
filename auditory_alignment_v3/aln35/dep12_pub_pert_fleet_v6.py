"""Read-only fleet readiness shim (v6) for the DEP12 public 400 ms perturbation panel (Agent M; auditory_alignment_v3/dep12/perturb_v4.py, encoders_v4 registry
incl. ext3 ssl_continue (M21); DTU / FAU), lane s35_dep12_pub_perturb (c3_s35dMpert), submit slurm/aln35_dep12_pub_perturb_v4.sbatch. Providers byte-checked, then
reloaded (panels -> federici -> public_features_v5 -> measure_v5 -> perturb_v4 -> public_fleet_v5). Replaces aln35/dep12_pub_pert_fleet_v5.py.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'panels': '570e8be0f0900472308617fcff93a75bd7b1b11b5de4230438c24d459ebc50be', 'federici': '365c2b03575c088932ff8c47c63b03e9072b5812e674b64a2ca4bfae2e1845bd', 'public_features_v5': '8ba4118d69e62670742ff706fa49f1ac113a277c0aafb3c8efefb271864b6a19', 'measure_v5': '26644e61d538cec15a1dc0334922bb45c5a893694aa591c9c5fe63d0c32f72c3', 'perturb_v4': 'f4f18976e405a8379565f934feb449d84ea1c6c95d8a3cf1c32c44f68cefab41', 'public_fleet_v5': '5a5610e550a62267aa1489874bee032e201be35dba1a11aaa57a3c1235b0051e'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 public provider changed: {name}'
    for name in ('panels', 'federici', 'public_features_v5', 'measure_v5', 'perturb_v4'):
        importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_fleet_v5'))
    assert B.sha(module.__file__) == FROZEN['public_fleet_v5']
    st = module.fleet_status('P')
    assert st['lane'] == 's35_dep12_pub_perturb' and (not st['submit'] or st['submit'][0].startswith('slurm/aln35_')), st
    return st
