"""Read-only fleet readiness shim for the ALN3.6 R2 replication, seed 3407, v2 (replaces aln36_r2_fleet in the registry).

Same providers as v1 plus aln36.r2_inproc (runner of the private item) and aln36.r2_lanes_v2, byte-checked, then
importlib.reload()ed in dependency order. Only the private item changes (job name c3_s35r2a36priv2; see r2_lanes_v2).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'r2_apwrong': '5125cdfc5f079ba871a8d89300b4a06781bc403d4ad62383ac9297b1a419d961',
    'r2': '4a70305b0fb11bd2570682a63c4c84fb77a5bb8a5b7ff1b8269bc18af55895f7',
    'r2_inproc': '8ea41c8bd2cccb009055942e185d0558bc96e4900138bb7cb8eaaa1c2553aa80',
    'r2_lanes': '33632e4166b49d789aa7feffc8d5cb5a2db63215e78f48829c518082b387836d',
    'r2_lanes_v2': '3e4aa7dab69de89f312df30d2813ed819391bd12f89ce5111fbe02fb7d1d987b',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln36' / f'{name}.py') == digest, f'aln36 R2 provider changed: {name}'
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln36.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
