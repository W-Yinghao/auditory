"""Read-only fleet readiness shim for paper line W2, the post-hoc MindMix audit (auditory_alignment_v3/paper/mindmix_audit.py;
blueprint docs/auditory_alignment_v3/paper/PR_STORY_BLUEPRINT.md). Registered last (lowest priority).
Provider byte-checked, then importlib.reload()ed. Lane c3_s35mmaudit (smoke first, then one unit per worker job).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'mindmix_audit': 'be597320c300c4ceea7254fcad875aa1cb98cfb4cdb321752901e199c560015a'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
