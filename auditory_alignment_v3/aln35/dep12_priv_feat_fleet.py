"""Read-only fleet readiness shim for the DEP12 private-children lane (Agent P; auditory_alignment_v3/dep12/private_fleet.py;
package v1.2 03 §1, §4.4, §5). Lane c3_s35dPfeat: --smoke first (probe exports + the complete B0 unit), then --worker (one unit =
one encoder x 5 outer folds; each worker job ends with the CPU post-processing: U0 / strict twin / δ profile, U10 selection,
aggregation), and --post when only CPU stages remain. Providers are byte-checked, then importlib.reload()ed in dependency order.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'private_features': '37e392c745dc4708f247922787c50fcd740ddbaff36a6e74e2a7b8339b2881ba',
    'private_use': '6ea1c223e895c7ff02e45f48e23b6f5f51a9a91ff0f30a5742f490e7cf1b47fb',
    'selection': '40e9f4a47b0adc231f26ee7125b867f9c018db9257f7554ec33c9e3c1929c496',
    'private_fleet': '081fbaafa5911158868279c7449e875965d9c6e79c69808adf3dfbdddd0eb70b',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 private provider changed: {name}'
    for name, digest in FROZEN.items():
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
