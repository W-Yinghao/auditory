"""Coordinator-convention wrapper (2026-10-23 07:50) around Agent M's v3 public shim `dep12_pub_pert_fleet_v3` (sha256 9445a6e0537635d356145f6546db07902605a920a4a9f5453dbe755ed49900c3;
encoders_v2 / plan_ext1). The coordinator requires lane 's35_*' and submit 'slurm/aln35_*.sbatch'; v3 reports 'dep12_pub_perturb' and
'slurm/dep12_pub_perturb_v2.sbatch'. This wrapper byte-checks v3 and the byte-identical sbatch copy, then renames only those two fields."""
import importlib
from pathlib import Path

from ..aln34 import learning_budget as B

ROOT = Path(__file__).resolve().parents[2]
V3, V3_SHA = 'dep12_pub_pert_fleet_v3', '9445a6e0537635d356145f6546db07902605a920a4a9f5453dbe755ed49900c3'
SB_OLD, SB_NEW = 'slurm/dep12_pub_perturb_v2.sbatch', 'slurm/aln35_dep12_pub_perturb_v2.sbatch'


def fleet_status():
    assert B.sha(ROOT / 'auditory_alignment_v3' / 'aln35' / f'{V3}.py') == V3_SHA, 'v3 public shim changed'
    assert (ROOT / SB_OLD).read_bytes() == (ROOT / SB_NEW).read_bytes(), 'sbatch copy differs'
    st = dict(importlib.reload(importlib.import_module(f'auditory_alignment_v3.aln35.{V3}')).fleet_status())
    st['lane'] = 's35_' + st['lane']
    if st.get('submit'):
        assert st['submit'][0] == SB_OLD, st['submit']
        st['submit'] = [SB_NEW] + list(st['submit'][1:])
    return st
