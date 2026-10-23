"""Read-only fleet readiness shim for paper line W7 §2.1 audit A (auditory_alignment_v3/paper/w7_audit.py): noise-EEG / identical-row forwards of B0, TCS, TNCE (seed 3401) on the
DTU cs test anchors and the CS-QMI permutation audit (APPENDUM_RAD_03 / 04).
New lane appended at the end of the registry. Provider byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'w7_audit': 'e14c76469929bfccfd9b84611f064e159adc37dc64c32e244fa6c90b5b6544af'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
