"""Read-only fleet readiness shim for the DEP12 public feature exporter (Agent M; auditory_alignment_v3/dep12/public_features.py),
lane P (c3_s35dMpert). Providers byte-checked, then reloaded (panels -> public_features -> perturb -> public_fleet).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'panels': '570e8be0f0900472308617fcff93a75bd7b1b11b5de4230438c24d459ebc50be', 'public_features': '156b78b07076fc58cacd1e62b3a6d10df3b4e28da51c70ab8a395e53e40f7edd', 'measure': '5ec2a87d83b12051ad59a97374f9ae79e5cd26d21fb7734584a80c8e6f8b810a', 'perturb': '1ae3925166f2386cfdfb8e1de6385217dd4a399be6c7e896c5780286afe6c978', 'public_fleet': 'ac6a60a6dab5f7463207f8ccd85ebcefed4de2ede6ade3950bf5c3c980f9025b'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 public provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.panels'))
    importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_features'))
    importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.measure'))
    importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.perturb'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.dep12.public_fleet'))
    assert B.sha(module.__file__) == FROZEN['public_fleet']
    return module.fleet_status('P')
