"""Read-only fleet readiness shim for paper line W5, the MindMix alignment recipe on the common CBraMod backbone
(auditory_alignment_v3/paper/calra_cbramod.py; manuscript Table 6 row 'MindMix alignment recipe (common backbone)').
Provider byte-checked, then importlib.reload()ed. Lane c3_s35calra (smoke first, then one work item per worker job).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'calra_cbramod': 'dee050de3927f6adc3c1869e926b4fe4a2953c9030c70113630722119a21f31e'}


def fleet_status():
    name, digest = next(iter(FROZEN.items()))
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
    assert B.sha(module.__file__) == digest
    return module.fleet_status()
