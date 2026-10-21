"""Read-only fleet readiness shim for the ALN4.2 bounded source-learning diagnosis (4 units, zero optimizer updates;
researcher 2026-10-21: "看看这个包，需要执行的就执行"). Provider byte-checked, then importlib.reload()ed. Lane c3_s35a42diag.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'source_diag': '06c396a43e5c6c332b4e28f2b5ec813883b5979412a5073e2c131cec88a6ead3'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln42' / f'{name}.py') == digest, f'aln42 provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln42.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
