"""Read-only fleet readiness shim for the DEP12 source extension-3 lane (auditory_alignment_v3/dep12/source_fleet_ext3.py:
ssl_continue x seeds 3401 / 3407 / 3413, DECISIONS 2026-10-23 11:55, S23-S25). Providers byte-checked (dependency order), then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {'source_common': '7987abffccc64f3d7bdae01c417d344679dad03ba221696173c16fa629fc94e9',
          'training_objectives_torch': 'd5116dec303aa6dba4a2f5493540ce2372d92cc0d7792a540fb62c1c96cf7f91',
          'dependence_measure': '22cf63e144b76c97c4dd69b78dac507580d7a5187e2add87cd5916f83fb31005',
          'objectives': 'b3e6163a27a5121a940c7533779aa10ada71ad5955f156c5bb4477ccd6d5ca33',
          'source_sampler': '8158e0127ff468495a72349875e67233cb5e429320b7a1ea741a2bb3e1d33651',
          'devprobe': '450041acd5c97f7d436343128001a220933c2d5ffe5fd2ef785bc6ea26f84f89',
          'trainer_v2': '3b69db9b4d5621a3bda3abca639d7500842b608d84d7c367134e993e2e010ff5',
          'source_fleet_v2': 'f338a6ac53db7a5faf1c37e52510785b533debb63017787a319dfe92c592f891',
          'trainer_ext3': '76e4325405394c1a53efeeed71a7e89f20f7dcc3a7ca02dc9156038cb4202dd3',
          'source_fleet_ext3': '22f22b4baab267a2a31ff47526042fd3076542fcd2f231bd3094cf4746c38281'}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'DEP12 source ext3 provider changed: {name}'
    module = None
    for name in FROZEN:
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
    assert B.sha(module.__file__) == FROZEN['source_fleet_ext3']
    return module.fleet_status()
