"""Read-only fleet readiness shim for paper line W6 (MindMix official code + released checkpoint on KUL AAD v2.0 with the
shortcut audit; auditory_alignment_v3/paper/kul_mindmix.py, revision 01 / plan_v2), lane A = P1 paper split, 80 units.
Provider byte-checked against the frozen sha256, then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'kul_mindmix': 'e948526b230c3811cea28253739536b2b37e475d84701f237a7d8db9c3e5dc6c'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.kul_mindmix'))
    assert B.sha(module.__file__) == FROZEN['kul_mindmix']
    st = module.fleet_status('A')
    assert 1 <= st['slots'] <= 2, st
    return st
