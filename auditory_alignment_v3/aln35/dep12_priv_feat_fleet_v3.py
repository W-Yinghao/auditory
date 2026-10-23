"""Read-only fleet readiness shim, VERSION 3, for the DEP12 private-children lane (Agent P; auditory_alignment_v3/dep12/
private_fleet_v3.py; DECISIONS P24): v2 plus the ext2 follow-up arm cs_pair_noise@{3401,3407,3413} served by encoders_v3.py.
Same lane identity c3_s35dPfeat / s35_dep12_private_features; sbatch slurm/aln35_dep12_priv_feat_v3.sbatch.
Providers (including the three encoder registries) are byte-checked, then importlib.reload()ed in dependency order.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'encoders': '0201f97504d15b92abb161900deb826ec10667baac69afa6e0fbb72459cf26f1',
    'encoders_v2': '6e4d3b5928826f0f27da2a9b026469c9f03a0ce0000fcab8edeaaeb9a55183c7',
    'encoders_v3': 'cc50ee4f95aaccd6bc88e88ec4156df7c9f0378c29385253f27128ac4bcd489e',
    'private_features': '37e392c745dc4708f247922787c50fcd740ddbaff36a6e74e2a7b8339b2881ba',
    'private_features_v3': '9f00e14322c89f1931d39e5be9e9c6fb74a4326c8774f729b988e48d45b80602',
    'private_use': '6ea1c223e895c7ff02e45f48e23b6f5f51a9a91ff0f30a5742f490e7cf1b47fb',
    'selection': '40e9f4a47b0adc231f26ee7125b867f9c018db9257f7554ec33c9e3c1929c496',
    'private_mechanism': 'bad50f61f0291f866a2357846505e81aa99d896b5684bf7a7196bc38f12e7d83',
    'private_mechanism_v2': 'da0c1635ed6e512dee85bc349f3670625cfc1d6dac813023fba44e4f16ace4ad',
    'private_fleet_v3': 'dcd09afc9ee0ec8be041ed4d5efad9fa8b286d8cc40ace04c9c4f2f5fe3620a7',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 private provider changed: {name}'
    for name, digest in FROZEN.items():
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
