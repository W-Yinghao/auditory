"""Read-only fleet readiness shim for ALN4.1 lanes, v3 (researcher: ALN4.1 takes priority over ALN3.6 where they compete).

v2 handled one item per provider; v3 also accepts a provider that returns a list of items (per-arm private CE lanes in
aln41.private_ft_lane; private_ft.py itself stays frozen). Providers are byte-checked, then importlib.reload()ed.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'source': 'b7ebc04fec3476b7901b9de107505df6c508668b464cb4419442d2c091ff25d7',
    'private_ft_lane': '6ac54eddb7107e3737c98a82d20db54cf2ccfaa7ef71a054dc0fff83fce17bd5',
    'frozen': '48c46fe88d04e36d396f765eb9b72f5fb3c822d7671bcf4fd61a12ee164be1cb',
}


def fleet_status():
    out = []
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln41' / f'{name}.py') == digest, f'aln41 provider changed: {name}'
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln41.{name}'))
        assert B.sha(module.__file__) == digest
        value = module.fleet_status()
        out.extend(value if isinstance(value, list) else [value])
    return out
