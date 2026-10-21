"""Shared ALN3.6 paths, package binding and small I/O helpers (no data loading)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .. import core
from ..aln34 import learning_budget as B

REPO = Path(core.REPO)
OUT = Path(core.OUT) / 'aln36'
STORE = Path('<private checkpoint storage>/auditory_alignment_v3/aln36')
PACKAGE = REPO / 'AUDITORY_ALN3_SERVER_PACKAGE_v3_6_20261020'
PACKAGE_ZIP_SHA256 = '34f1162c2c04b553473346ae46f683332571a62c4167b691795440996a53d108'
BASELINE_COMMIT = '3da8cf5758214c0cf87a1f1c8d67fb84b574000e'
ORIGIN = 'prospective_protocol_after_2026_10_20_result_informed_design'
SEED = 3401
GROUPS = ('ci', 'ha', 'th')
CONTENT_FOLDS = (0, 1)
PERSON_FOLDS = (0, 1, 2, 3, 4)
TOOLS = ('local_L1', 'CBpre_true_full')

sha, write, dumps = B.sha, B.write, B.dumps


def read(path):
    return json.loads(Path(path).read_text())


def digest(value, n=16):
    return hashlib.sha256(dumps(value).encode()).hexdigest()[:n]


def package_binding():
    """Byte-check the package files this round relies on (manifest hashes, not the zip itself)."""
    manifest = read(PACKAGE / 'MANIFEST.json')
    out = {}
    for rec in manifest['files']:
        path = PACKAGE / rec['path']
        assert sha(path) == rec['sha256'], f'package file changed: {rec["path"]}'
        out[rec['path']] = rec['sha256']
    plan = read(PACKAGE / 'plans/round1.json')
    assert plan['baseline_commit'] == BASELINE_COMMIT and plan['seed'] == SEED
    nested = Path(__file__).with_name('nested.py')
    assert sha(nested) == out['src/aln36_readout/nested.py'], 'aln36/nested.py must stay byte-identical to the package reference'
    return {'package': PACKAGE.name, 'zip_sha256': PACKAGE_ZIP_SHA256, 'files': out, 'round1_plan': plan}
