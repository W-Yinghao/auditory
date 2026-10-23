"""Read-only fleet readiness shim (v5) for the DEP12 public feature exporter (Agent M; auditory_alignment_v3/dep12/public_features_v3.py, encoders_v3
registry incl. ext2 cs_pair_noise), lane s35_dep12_pub_features (c3_s35dMfeat), submit slurm/aln35_dep12_pub_features_v3.sbatch. Providers byte-checked, then
reloaded (panels -> public_features_v3 -> measure_v3 -> perturb_v3 -> public_fleet_v3). Replaces the v4 wrappers.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'panels': '570e8be0f0900472308617fcff93a75bd7b1b11b5de4230438c24d459ebc50be', 'public_features_v3': 'd6db62e4973a1cb0233ba964f69532b87768569bba464ae1e455aefa4f0faf70', 'measure_v3': 'b9e7a3173df8d3565bb8e904ba8b7fd0029c2e224a965b35dd7f5f03dd76a7dd', 'perturb_v3': 'a2f393a9969bb9dbb2a89ab20846312aa2ad4f3e7c8c5dd6bf188c9ebbf72ac7', 'public_fleet_v3': 'c38f83cb2217d67bfbea0551ed2685ee53f30bdf188feae4120c50d37be9282d'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 public provider changed: {name}'
    for name in ('panels', 'public_features_v3', 'measure_v3', 'perturb_v3'):
        importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_fleet_v3'))
    assert B.sha(module.__file__) == FROZEN['public_fleet_v3']
    st = module.fleet_status('F')
    assert st['lane'] == 's35_dep12_pub_features' and (not st['submit'] or st['submit'][0].startswith('slurm/aln35_')), st
    return st
