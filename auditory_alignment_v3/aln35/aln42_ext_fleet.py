"""Read-only fleet readiness shim for the ALN4.2 R3 external seat (MindMix released full architecture, common-protocol task
adaptation; 10 DTU44 units, seed 3401; binding frozen before any test score). Researcher 2026-10-21: "需要执行的就执行".
Provider byte-checked, then importlib.reload()ed. Lane c3_s35a42ext (smoke first, then <= 2 workers).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'external_mindmix': '564d4d1903915af0660ac6bdad963648aa0a2bb8cfff36496ef22056f71937d4'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln42' / f'{name}.py') == digest, f'aln42 provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln42.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
