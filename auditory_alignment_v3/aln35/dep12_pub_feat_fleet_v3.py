"""Read-only fleet readiness shim (v3) for the DEP12 public feature exporter (Agent M; auditory_alignment_v3/dep12/public_features_v2.py,
encoders_v2 registry incl. the mechanism-seed extension), lane F (c3_s35dMfeat). Providers byte-checked, then reloaded
(panels -> public_features_v2 -> measure_v2 -> perturb_v2 -> public_fleet_v2). Replaces aln35/dep12_pub_feat_fleet.py.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'panels': '570e8be0f0900472308617fcff93a75bd7b1b11b5de4230438c24d459ebc50be', 'public_features_v2': '7f1ecca3d230e3ef4ce737db8126c3deaf35864b2a1898ed42bfb7974e382792', 'measure_v2': 'e13ec77bf55888f78dc0cb566f2e570706c0dfe0d26c26946bb198936c62d127', 'perturb_v2': 'bf21a9264a2ea620e49e125982eab0f4cc82d16f0c9114224b2d24f99b837db5', 'public_fleet_v2': '3a64758ba9d6cedeea46903157a60028ec323fb6f211d65fb2224008205b6e3f'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 public provider changed: {name}'
    for name in ('panels', 'public_features_v2', 'measure_v2', 'perturb_v2'):
        importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_fleet_v2'))
    assert B.sha(module.__file__) == FROZEN['public_fleet_v2']
    return module.fleet_status('F')
