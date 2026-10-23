"""Read-only fleet readiness shim for paper line W7 §2.7 D (auditory_alignment_v3/paper/w7_adapt.py): per-child input spatial-filter adaptation (D_CE / D_CS + cal) on the
selected core CE checkpoints, B0 and TCS x 3 seeds x 5 outer folds (APPENDUM_RAD_02).
New lane appended at the end of the registry. Provider byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'w7_adapt': '1193963e8fd12008f485d0cb9e586dd8e5b08329441802b2763861c467af1ec0'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
