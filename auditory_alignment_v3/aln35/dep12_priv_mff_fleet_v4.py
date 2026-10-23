"""Read-only fleet readiness shim, VERSION 4, for the DEP12 private MFF extension (Agent P; auditory_alignment_v3/dep12/
private_mff_v4.py; DECISIONS P21-P25): v3 plus the ext3 follow-up arm ssl_continue served by encoders_v4.py. Same lane identity
c3_s35dPmff / s35_dep12_private_mff; sbatch slurm/aln35_dep12_priv_mff_v4.sbatch.
Providers (the four encoder registries and every module the lane or its CPU stages import) are byte-checked, then
importlib.reload()ed in dependency order.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'encoders': '0201f97504d15b92abb161900deb826ec10667baac69afa6e0fbb72459cf26f1',
    'encoders_v2': '6e4d3b5928826f0f27da2a9b026469c9f03a0ce0000fcab8edeaaeb9a55183c7',
    'encoders_v3': 'cc50ee4f95aaccd6bc88e88ec4156df7c9f0378c29385253f27128ac4bcd489e',
    'encoders_v4': 'b26d300b3aabcba5acb621a69a2e18542876b3a42d344378e3fc6585cf74518b',
    'private_features': '37e392c745dc4708f247922787c50fcd740ddbaff36a6e74e2a7b8339b2881ba',
    'private_use': '6ea1c223e895c7ff02e45f48e23b6f5f51a9a91ff0f30a5742f490e7cf1b47fb',
    'private_analysis': 'c2ddc15cf6b69aa9977b64f755170540d182766aad4f6c22969f327fe672515b',
    'selection': '40e9f4a47b0adc231f26ee7125b867f9c018db9257f7554ec33c9e3c1929c496',
    'private_fleet_v2': 'd83680d2aa84c4c7d81835bc9af88363672aff56c4d74555bac659b32a46450c',
    'private_fleet_v3': 'dcd09afc9ee0ec8be041ed4d5efad9fa8b286d8cc40ace04c9c4f2f5fe3620a7',
    'private_mff_v2': '7bdd3322cc37a4ae0bd863cbeecaa1dd7e3bab7e089e40c61193fd8390ec71f5',
    'private_mff_v3': '1fdb7410c32de6fb17d14c149495c11d2305bbaf069171a06a08e2c1c02ec338',
    'private_mechanism': 'bad50f61f0291f866a2357846505e81aa99d896b5684bf7a7196bc38f12e7d83',
    'private_mechanism_v2': 'da0c1635ed6e512dee85bc349f3670625cfc1d6dac813023fba44e4f16ace4ad',
    'private_mechanism_v3': '3cc68c8f148b433c39fe6a7c0ea7edb18e83b75de00f4c421f1178244b3a2f7e',
    'private_features_v4': '3e657bff055600012ad836d2e411af02c9142c96356eb274fe4f05dc5f40ffa4',
    'private_fleet_v4': '21bb3437655c0fd29202d09cc6eab3841b098785c0b84feb041b910dcddfe0a8',
    'private_mff_v4': '4f696881561b67200488e11c65c790a121e05ca9e47e8474e29ea4f6258ab71e',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 private provider changed: {name}'
    for name, digest in FROZEN.items():
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
