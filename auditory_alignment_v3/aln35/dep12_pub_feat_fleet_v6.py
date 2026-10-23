"""Read-only fleet readiness shim (v6) for the DEP12 public feature exporter (Agent M; auditory_alignment_v3/dep12/public_features_v4.py:
DTU / FAU incl. ext2 cs_pair_noise, plus Federici as a third public cohort (DECISIONS M20)), lane s35_dep12_pub_features (c3_s35dMfeat),
submit slurm/aln35_dep12_pub_features_v4.sbatch. Providers byte-checked, then reloaded (panels -> federici -> public_features_v4 ->
measure_v4 -> public_fleet_v4). Replaces aln35/dep12_pub_feat_fleet_v5.py; the perturbation lane stays on dep12_pub_pert_fleet_v5.py.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'panels': '570e8be0f0900472308617fcff93a75bd7b1b11b5de4230438c24d459ebc50be', 'federici': '365c2b03575c088932ff8c47c63b03e9072b5812e674b64a2ca4bfae2e1845bd', 'public_features_v4': 'f1db073784371be6b7cd51c682a82504ea158705d85269bb3f75025b348a0506', 'measure_v4': '09c4cfdb3ed408802319253dbe752d4e8a948cec6df1b0cb896156141f9fec53', 'public_fleet_v4': 'faabd8bcd95bc148fac52ab3259a8ab7b03a8222187eb1af5659a468b43be227'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 public provider changed: {name}'
    for name in ('panels', 'federici', 'public_features_v4', 'measure_v4'):
        importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_fleet_v4'))
    assert B.sha(module.__file__) == FROZEN['public_fleet_v4']
    st = module.fleet_status('F')
    assert st['lane'] == 's35_dep12_pub_features' and (not st['submit'] or st['submit'][0].startswith('slurm/aln35_')), st
    return st
