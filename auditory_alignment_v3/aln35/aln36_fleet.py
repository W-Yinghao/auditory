"""Read-only fleet readiness shim for ALN3.6 lanes.

The ALN3.5 coordinator imports providers only from auditory_alignment_v3.aln35; the ALN3.6 science code lives in
auditory_alignment_v3/aln36 and is byte-checked here before its readiness functions are called.
Lanes: FAU whole-group source training (local, CB), public frozen feature banks, private window features.
"""
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'auditory_alignment_v3/aln36/fau_group.py': '562a98aa9f81c801b6645bd9026500236790bcc9742a767d56e8b430349f95d1',
    'auditory_alignment_v3/aln36/public_features.py': '0f9dd5970e7c9cf9e8d3aa16612b7dec09c67c3d2c89b9ff2c3e5182e7a77660',
    'auditory_alignment_v3/aln36/private_features.py': '4f69be86a5887bdba6e3dc0eddc51544681e52b055a9290ebfafbd29a22ce675',
}


def fleet_status():
    for rel, digest in FROZEN.items():
        assert B.sha(ROOT / rel) == digest, f'aln36 provider changed: {rel}'
    from ..aln36 import fau_group, private_features, public_features
    return fau_group.fleet_status() + [public_features.fleet_status(), private_features.fleet_status()]
