"""Read-only fleet readiness shim for the DEP12 private MFF extension (Agent P; auditory_alignment_v3/dep12/private_mff.py;
DECISIONS P21/P22): MFF pure tone / bapa as a second private cohort and cross-stimulus transfer for the DEP12 representations.
Lane c3_s35dPmff: --smoke (the complete B0 unit), then --worker (one unit = one encoder, all 15 fits; ends with the CPU
analysis), --post when only CPU stages remain. Providers are byte-checked, then importlib.reload()ed in dependency order.
"""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    'private_features': '37e392c745dc4708f247922787c50fcd740ddbaff36a6e74e2a7b8339b2881ba',
    'private_fleet': '081fbaafa5911158868279c7449e875965d9c6e79c69808adf3dfbdddd0eb70b',
    'private_use': '6ea1c223e895c7ff02e45f48e23b6f5f51a9a91ff0f30a5742f490e7cf1b47fb',
    'private_mff': '4070ee41a5ee424dfe9cb62aef59d9a8cf44e14a3592514650a7a3ccdd95a56f',
}


def fleet_status():
    module = None
    for name, digest in FROZEN.items():
        assert B.sha(ROOT / 'auditory_alignment_v3' / 'dep12' / f'{name}.py') == digest, f'dep12 private provider changed: {name}'
    for name, digest in FROZEN.items():
        module = importlib.reload(importlib.import_module(f'auditory_alignment_v3.dep12.{name}'))
        assert B.sha(module.__file__) == digest
    return module.fleet_status()
