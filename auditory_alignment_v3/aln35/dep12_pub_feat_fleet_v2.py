"""Coordinator-convention wrapper (2026-10-23) around the DEP12 public shim `dep12_pub_feat_fleet` (sha256 134a1bb70f6fa868792e363b5531e241579d202f04067b4d8813cbe3b9ff942a).
The coordinator (maintain_fleet_v2/v3) requires lane names starting with 's35_' and submit scripts 'slurm/aln35_*.sbatch'; the v1
shim reported lane 'dep12_pub_features' and 'slurm/dep12_pub_features.sbatch' and was rejected (AssertionError -> technical_error).
This wrapper byte-checks the v1 shim and the byte-identical sbatch copy, then renames only those two fields."""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
V1, V1_SHA = 'dep12_pub_feat_fleet', '134a1bb70f6fa868792e363b5531e241579d202f04067b4d8813cbe3b9ff942a'
SB_OLD, SB_NEW = 'slurm/dep12_pub_features.sbatch', 'slurm/aln35_dep12_pub_features.sbatch'


def fleet_status():
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln35' / f'{V1}.py') == V1_SHA, 'v1 public shim changed'
    assert (ROOT / SB_OLD).read_bytes() == (ROOT / SB_NEW).read_bytes(), 'sbatch copy differs'
    st = dict(importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln35.{V1}')).fleet_status())
    st['lane'] = 's35_' + st['lane']
    if st.get('submit'):
        assert st['submit'][0] == SB_OLD, st['submit']
        st['submit'] = [SB_NEW] + list(st['submit'][1:])
    return st
