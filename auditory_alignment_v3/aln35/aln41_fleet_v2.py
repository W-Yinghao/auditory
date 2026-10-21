"""Read-only fleet readiness shim for ALN4.1 lanes, v2 (researcher: ALN4.1 takes priority over ALN3.6 where they compete).

v1 (aln41_fleet) was imported once by the long-running coordinator, so later provider hashes could not be picked up.
v2 byte-checks each provider and then importlib.reload()s it, so the coordinator always evaluates exactly the registered
bytes; a provider change still requires a new shim hash in fleet_plugins.json (and a new module name if this file changes).
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'source': 'b7ebc04fec3476b7901b9de107505df6c508668b464cb4419442d2c091ff25d7',
    'private_ft': 'c62b9c0694f179cbd033786a4db7d7f10687d29475476569eb593bedbde36ecd',
    'frozen': '48c46fe88d04e36d396f765eb9b72f5fb3c822d7671bcf4fd61a12ee164be1cb',
}


def fleet_status():
    out = []
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln41' / f'{name}.py') == digest, f'aln41 provider changed: {name}'
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln41.{name}'))
        assert B.sha(module.__file__) == digest
        out.append(module.fleet_status())
    return out
