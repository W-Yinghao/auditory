"""ALN3.6 R2 in-process runner v2 (engineering fix, 2026-10-21): the R1 mains under r2.seeded() with argv passed verbatim.

r2.py parses its own options with parse_known_args before handing the rest to the R1 mains. It defines `--smoke`, so
`r2 private --smoke` consumed the flag and private_features.main ran its worker branch with smoke_job None
(FileNotFoundError probes/None/receipt.json; 127 c3_s35r2a36priv jobs from 15:22, none wrote a unit or a FAILED marker).
r2.py stays byte-identical (its sha is bound into the private plan as r2_sources); this runner re-enters the same seeded()
context and plan check and forwards every argument unchanged.
Usage: `python -m auditory_alignment_v3.aln36.r2_inproc <private|public_readout|private_readout|analysis> [R1 main args]`.
"""
from __future__ import annotations

import os
import sys

from . import common as C, r2 as R2

MODULES = {'private': R2.PFE, 'public_readout': R2.R, 'private_readout': R2.PR, 'analysis': R2.A}


def main():
    assert os.environ.get('SLURM_JOB_ID') and len(sys.argv) >= 2 and sys.argv[1] in MODULES, __doc__
    os.umask(0o077)
    stage, rest = sys.argv[1], sys.argv[2:]
    with R2.seeded():
        if stage == 'private':
            plan = C.read(R2.PFE.PLAN); assert plan['r2_sources'] == R2.r2_sources(), 'r2 runner drift'
        module = MODULES[stage]
        sys.argv = [module.__name__, *rest]
        module.main()


if __name__ == '__main__':
    main()
