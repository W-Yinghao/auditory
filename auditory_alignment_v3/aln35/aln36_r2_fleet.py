"""Read-only fleet readiness shim for the ALN3.6 R2 replication, seed 3407 (researcher 2026-10-21: "开始两个R2").

Providers (aln36.r2_apwrong, aln36.r2 and aln36.r2_lanes) are byte-checked, then importlib.reload()ed in dependency order.
Lanes c3_s35r2a36loc / cb / feat / apw / priv; registered after the ALN4.1 R2 shim, which keeps priority.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'r2_apwrong': '5125cdfc5f079ba871a8d89300b4a06781bc403d4ad62383ac9297b1a419d961',
    'r2': '4a70305b0fb11bd2570682a63c4c84fb77a5bb8a5b7ff1b8269bc18af55895f7',
    'r2_lanes': '33632e4166b49d789aa7feffc8d5cb5a2db63215e78f48829c518082b387836d',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln36' / f'{name}.py') == digest, f'aln36 R2 provider changed: {name}'
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln36.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
