"""Fleet shim v2 for the REVE fine-tuning lane (paper/encoders.py lane R). v1 passed through slots=3, which the coordinator
rejects (assert 1 <= slots <= 2); v2 clamps to 2. A second lane (paper_enc_fleet_r_b) takes REVE work beyond these 2 slots.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'enc_models': '26e25df76e582bbe4a3e147df403282aaed512e4f7b32cfb3729370fd113bbd1',
          'encoders': '39d7e51e71571cbe44029487775d54ab2757697971aab081b0cf925f8dee9061'}


def status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.paper.enc_models'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.paper.encoders'))
    assert B.sha(module.__file__) == FROZEN['encoders']
    return module.fleet_status('R')


def fleet_status():
    st = status()
    return {**st, 'slots': min(int(st['slots']), 2)}
