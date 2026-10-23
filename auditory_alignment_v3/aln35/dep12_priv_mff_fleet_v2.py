"""Read-only fleet readiness shim, VERSION 2, for the DEP12 private MFF extension (Agent P; auditory_alignment_v3/dep12/
private_mff_v2.py; DECISIONS P21-P23): v1 plus the extension-1 mechanism controls served by encoders_v2.py. Same lane identity
c3_s35dPmff / s35_dep12_private_mff; sbatch slurm/aln35_dep12_priv_mff_v2.sbatch. Providers byte-checked, then reloaded.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'encoders': '0201f97504d15b92abb161900deb826ec10667baac69afa6e0fbb72459cf26f1',
    'encoders_v2': '6e4d3b5928826f0f27da2a9b026469c9f03a0ce0000fcab8edeaaeb9a55183c7',
    'private_features': '37e392c745dc4708f247922787c50fcd740ddbaff36a6e74e2a7b8339b2881ba',
    'private_use': '6ea1c223e895c7ff02e45f48e23b6f5f51a9a91ff0f30a5742f490e7cf1b47fb',
    'private_mechanism': 'bad50f61f0291f866a2357846505e81aa99d896b5684bf7a7196bc38f12e7d83',
    'private_fleet_v2': 'd83680d2aa84c4c7d81835bc9af88363672aff56c4d74555bac659b32a46450c',
    'private_mff_v2': '7bdd3322cc37a4ae0bd863cbeecaa1dd7e3bab7e089e40c61193fd8390ec71f5',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 private provider changed: {name}'
    for name, digest in FROZEN.items():
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
