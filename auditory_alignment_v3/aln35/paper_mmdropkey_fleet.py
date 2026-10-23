"""Read-only fleet readiness shim for the paper-line shortcut audit of the complete released MindMix system
(auditory_alignment_v3/paper/mindmix_dropkey_audit.py; frozen protocol private/auditory_alignment_v3/paper/mindmix_dropkey_v1/
PROTOCOL.md). Lane c3_s35pmmdk / s35_paper_mmdropkey: smoke first, then one unit per worker job (20 units, slots 2).
Provider byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'mindmix_dropkey_audit': 'c6b7587a8366edfa9fe6aac4fdd613141831f092ad1bab401fda17d315e079a0'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
