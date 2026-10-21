"""Read-only fleet readiness shim for the ALN4.1 R2 replication (researcher 2026-10-21: "开始两个R2"; ALN4.1 keeps priority).

Providers (aln41.r2_lanes and the runner aln41.r2 it imports) are byte-checked, then importlib.reload()ed, so a changed
provider is refused instead of silently cached. Lanes c3_s35r2a41src / pb0 / ptcs / ptnc / frz.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'r2': '62aad8c615136e817024b637654ae2a33589f38e4eb350a4835a7da80fd7a01d',
    'r2_lanes': '64813eeddd24798fdccb775dfc45a7bdb90c6c0529f4db40a00cb808f8bdf732',
}


def fleet_status():
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln41' / f'{name}.py') == digest, f'aln41 R2 provider changed: {name}'
    importlib.reload(importlib.import_module('auditory_alignment_v3.aln41.r2'))
    module = importlib.reload(importlib.import_module('auditory_alignment_v3.aln41.r2_lanes'))
    assert B.sha(module.__file__) == FROZEN['r2_lanes']
    return module.fleet_status()
