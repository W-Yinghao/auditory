"""Read-only fleet readiness shim for paper line W7 §2.7 D v2 (auditory_alignment_v3/paper/w7_adapt_v2.py): primary 5-step
(APPENDUM_RAD_02) and converged (APPENDUM_RAD_05) per-child input spatial-filter adaptation on the selected core CE checkpoints,
B0 and TCS x 3 seeds x 5 outer folds. Replaces the never-registered v1 D lane. Provider byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'w7_adapt_v2': 'c66bc3818f35243bf675dd858b13cb369650cc53403319464bd45e1e55379df6', 'w7_adapt': '1193963e8fd12008f485d0cb9e586dd8e5b08329441802b2763861c467af1ec0'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_adapt'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_adapt_v2'))
    assert B.sha(module.__file__) == FROZEN['w7_adapt_v2']
    return module.fleet_status()
