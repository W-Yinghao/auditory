"""Read-only fleet readiness shim for paper line W5 audit v2 (auditory_alignment_v3/paper/calra_audit_v2.py), the
dependency-scoped eval- and train-mode audit of the completed calra_cbramod production units. Replaces the completed
c3_s35calra entry (paper_calra_fleet) in the registry. Provider byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'calra_audit_v2': '427a7e477d9c68b8c119cc54d02db99613e87b71d20dae406aedde78552d803f'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
