"""Read-only fleet readiness shim for the ALN4.1 R2 replication, v2 (replaces aln41_r2_fleet in the registry; ALN4.1 keeps
priority). The private CE items run the resumable runner (aln41.r2_private_resume; see aln41.r2_lanes_v2).

Providers are byte-checked, then importlib.reload()ed in dependency order; private_ft is byte-checked only (r2.seeded
re-points its globals, so it must stay the module object r2 already holds).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'private_ft': 'c62b9c0694f179cbd033786a4db7d7f10687d29475476569eb593bedbde36ecd',
    'r2': '62aad8c615136e817024b637654ae2a33589f38e4eb350a4835a7da80fd7a01d',
    'r2_lanes': '64813eeddd24798fdccb775dfc45a7bdb90c6c0529f4db40a00cb808f8bdf732',
    'private_ft_resume': '334a51502096fc629b5c10ba36797fd1e333fcb7cb12f3b779af7a270f4c0e3b',
    'r2_private_resume': '1521b453321068ed1858645038076288e224b8a3a4d90cad8f96c4cac16fc04e',
    'r2_lanes_v2': '340443e2248091b71e5f06ae18160fa145551675742e3ad78d479d0109e5545f',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln41' / f'{name}.py') == digest, f'aln41 R2 provider changed: {name}'
        if name == 'private_ft':
            continue
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln41.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
