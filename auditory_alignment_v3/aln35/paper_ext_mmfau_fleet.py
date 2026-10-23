"""Read-only fleet readiness shim for the paper-line Table 2 external decoders, lane mmfau: MindMix complete system on FAU
(auditory_alignment_v3/paper/external_decoders.py; manuscript v2 section 4.1 / App. B.3). Every provider module of the fleet path
is byte-checked against its frozen sha256, then reloaded in dependency order; returns external_decoders.fleet_status('mmfau').
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
LANE = 'mmfau'
FROZEN = {'ext_common': '33de3374f0d0718f8d1ee6a02e39622d940504b59c319414e036aa95b1e3526b',
          'ext_fleet': '766fc3b02323352265e3a2988621187018f168c9ed355b8c708147316859187a',
          'vlaai_torch': '48181327fcea4ef1c9f3764297a80e702c203917857683ad1ac0b92668baa794',
          'ext_mtrf': '7da3718914ff49eb9c7547c60d6e81b7dccdb5c9270a26928a6c009bcf46cc05',
          'ext_vlaai': '91950309731c83cbc6a1eec541c2109257a9322e2f8b1c50bc2e315900dff270',
          'ext_clip': 'aa5254fabd6f051d5a2ca644630f54bcb55f450dee0545c3b494ebcb91132857',
          'mindmix_fau': '94b3e88738f0d19ab9db06363260bcc6bc0cd72d6a387e5fcc4b4bb88d2221ed',
          'external_decoders': '1abe17dc2bc312189e5199cf00645bad971e2e70433afbbe37d0230f92fa2f9f'}
DEPENDS = {'aln42/external_mindmix': '564d4d1903915af0660ac6bdad963648aa0a2bb8cfff36496ef22056f71937d4'}      # byte-checked only (imported by mindmix_fau; owned by the ALN4.2 lane)


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'paper' / f'{name}.py') == digest, f'paper provider changed: {name}'
    for name, digest in DEPENDS.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / f'{name}.py') == digest, f'dependency changed: {name}'
    for name in FROZEN:
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.paper.{name}'))
        assert B.sha(module.__file__) == FROZEN[name]
    return module.fleet_status(LANE)
