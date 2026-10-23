"""Read-only fleet readiness shim for the W7 GPU arms TCS_RES / TCS_CCS / TCS_PRES / TCS_RES_PRES
(auditory_alignment_v3/paper/w7_arms_v2.py; frozen design W7_CS_DEPENDENCE_PREREG_FROZEN.md + w7_v1/APPENDUM_01..04), lane A.
Providers byte-checked against their frozen sha256, then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'w7_objectives': 'ae209695c4382070090ca89a7c9e18b717b3acae4917f26023565524a8782cb3', 'w7_arms_v2': 'c382c8a3ef5aae47226bbc556a278758b5363c7e16126c2188029e7933c00783'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'W7 provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_objectives'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.w7_arms_v2'))
    assert B.sha(module.__file__) == FROZEN['w7_arms_v2']
    return module.fleet_status('A')
