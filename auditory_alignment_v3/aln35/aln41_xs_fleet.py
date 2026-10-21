"""Read-only fleet readiness shim for the ALN4.1 R2 cross-stimulus frozen extractions (7 units; researcher 2026-10-21:
"开始两个R2，跨刺激问题你来提方案"; decision docs/auditory_alignment_v3/aln41/R2_CROSS_STIM_DECISION.md).

Providers are byte-checked, then importlib.reload()ed (aln41.r2 first, which cross_stim imports). Lane c3_s35a41xs.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'r2': '62aad8c615136e817024b637654ae2a33589f38e4eb350a4835a7da80fd7a01d',
    'cross_stim': '92fd422389c8e999b4ae726fca2b8ad7ee1ea9e21328661ec69915ed4ae61d7e',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln41' / f'{name}.py') == digest, f'aln41 provider changed: {name}'
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln41.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
