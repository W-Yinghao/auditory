"""Read-only fleet readiness shim for ALN4.1 lanes (researcher: ALN4.1 takes priority over ALN3.6 where they compete).

The ALN3.5 coordinator imports providers only from auditory_alignment_v3.aln35; the ALN4.1 code lives in
auditory_alignment_v3/aln41 and is byte-checked here before its readiness functions are called.
"""
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'auditory_alignment_v3/aln41/source.py': 'b7ebc04fec3476b7901b9de107505df6c508668b464cb4419442d2c091ff25d7',
    'auditory_alignment_v3/aln41/private_ft.py': 'c62b9c0694f179cbd033786a4db7d7f10687d29475476569eb593bedbde36ecd',
    'auditory_alignment_v3/aln41/frozen.py': '48c46fe88d04e36d396f765eb9b72f5fb3c822d7671bcf4fd61a12ee164be1cb',
}


def fleet_status():
    for rel, digest in FROZEN.items():
        assert B.sha(ROOT / rel) == digest, f'aln41 provider changed: {rel}'
    from ..aln41 import frozen, private_ft, source
    return [source.fleet_status(), private_ft.fleet_status(), frozen.fleet_status()]
