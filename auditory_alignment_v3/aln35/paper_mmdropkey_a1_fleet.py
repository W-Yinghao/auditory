"""Read-only fleet readiness shim for appendum 01 of the complete-MindMix shortcut audit (per-encoder split of the train-mode
coupling; auditory_alignment_v3/paper/mindmix_dropkey_audit_a1.py, which imports the v1 module mindmix_dropkey_audit.py without
editing it; frozen private/auditory_alignment_v3/paper/mindmix_dropkey_v1/APPENDUM_01.md and plan_v2_appendum.json).
Lane c3_s35pmmda1 / s35_paper_mmdropkey_a1: smoke first, then one unit per worker job (20 units, slots 2).
Both the appendum provider and the v1 provider it imports are byte-checked; the appendum provider is importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'mindmix_dropkey_audit_a1': '3b8e0676a5d8b50f71a0b93ae9709d74c85fe822faa104729eb974edfb304637'}
V1 = {'mindmix_dropkey_audit': 'c6b7587a8366edfa9fe6aac4fdd613141831f092ad1bab401fda17d315e079a0'}


def fleet_status():
    for name, digest in {**V1, **FROZEN}.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    name, digest = next(iter(FROZEN.items()))
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
