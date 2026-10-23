"""Read-only fleet readiness shim for the paper-line transferred encoders (REVE, MindMix aligned EEG branch; manuscript v2
Tables 3-5; auditory_alignment_v3/paper/encoders.py), lane Z. Providers byte-checked, then reloaded (enc_models first).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'enc_models': '26e25df76e582bbe4a3e147df403282aaed512e4f7b32cfb3729370fd113bbd1',
          'encoders': '39d7e51e71571cbe44029487775d54ab2757697971aab081b0cf925f8dee9061'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.enc_models'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.encoders'))
    assert B.sha(module.__file__) == FROZEN['encoders']
    return module.fleet_status('Z')
