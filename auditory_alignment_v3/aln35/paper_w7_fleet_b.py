"""Read-only fleet readiness shim for the W7 GPU arms TCS_RES / TCS_CCS / TCS_PRES / TCS_RES_PRES
(auditory_alignment_v3/paper/w7_arms.py; frozen design W7_CS_DEPENDENCE_PREREG_FROZEN.md + w7_v1/APPENDUM_01..03), lane B.
Providers byte-checked against their frozen sha256, then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'w7_objectives': 'ae209695c4382070090ca89a7c9e18b717b3acae4917f26023565524a8782cb3', 'w7_arms': '78e6fa7f57cae3910574c23d529d0e1571cf2c380d4cda53fe8299eb74da4ab8'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'W7 provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_objectives'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_arms'))
    assert B.sha(module.__file__) == FROZEN['w7_arms']
    return module.fleet_status('B')
