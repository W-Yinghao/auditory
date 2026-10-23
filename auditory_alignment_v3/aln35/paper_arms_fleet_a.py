"""Read-only fleet readiness shim for the paper-line common-backbone arms (auditory_alignment_v3/paper/arms.py; manuscript v2
Table 6 temporal HSIC + approved W4 single-view TCS), lane A. Provider (and its objective module) byte-checked, then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'temporal_hsic_torch': 'cbf70cfe545aeb205182d1916910ed4378a6ec70997828c3c42edfe1a5d90c41', 'arms': '540d6e968b45bfe98622cb282205ff2aa275cdad3a202788352425d7de839106'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.temporal_hsic_torch'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.arms'))
    assert B.sha(module.__file__) == FROZEN['arms']
    return module.fleet_status('A')
