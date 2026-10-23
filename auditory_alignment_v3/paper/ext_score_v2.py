"""Score an external system whose plan covers only some of ext_common.DATASETS (2026-10-22).

external_decoders.score iterates every cohort in XC.DATASETS; for MindMix-FAU (plan = FAU only; DTU is aln42/external_eval_v2)
the empty DTU cohort fails at summary_by_window_s['20']. This wrapper re-points XC.DATASETS to the cohorts present in the
system's plan for the duration of the call; scoring, integration and the output file (results/.../external_decoders/<system>/
TABLE2_<SYSTEM>.json) are external_decoders.score unchanged. external_decoders.py itself is not edited (fleet shims byte-check
the paper providers).

Extension 2026-10-22 20:15 (Transformer-CLIP): plans whose rows include non-scored stages (clip: one stage='source' re-training
row without a 'dataset') are read with those rows removed for the scoring call only, after asserting their units are complete;
the plan file and its recorded sha256 are unchanged. For mmfau (no such rows) the behaviour is identical to the first version.

python -m auditory_alignment_v3.paper.ext_score_v2 --system mmfau | clip   (CPU, Slurm)
"""
from __future__ import annotations

import argparse
import contextlib
import os
from pathlib import Path

from . import ext_common as XC, external_decoders as XD


@contextlib.contextmanager
def plan_cohorts(system):
    S = XD.module(system); path = S.OUT / 'plan.json'; plan = XC.read(path)
    other = [r for r in plan['rows'] if 'dataset' not in r]
    assert all((S.OUT / 'units' / f'{r["id"]}.json').exists() for r in other), 'non-scored stage incomplete'
    present = tuple(d for d in XC.DATASETS if any(r.get('dataset') == d for r in plan['rows']))
    assert present, system
    old, old_read = XC.DATASETS, XD.read

    def read_scored(p):
        v = old_read(p)
        return {**v, 'rows': [r for r in v['rows'] if 'dataset' in r]} if Path(p) == path else v
    try:
        XC.DATASETS = present; XD.read = read_scored; yield present
    finally:
        XC.DATASETS, XD.read = old, old_read


def main():
    assert os.environ.get('SLURM_JOB_ID')
    ap = argparse.ArgumentParser(); ap.add_argument('--system', required=True, choices=tuple(XD.MODULES)); a = ap.parse_args()
    with plan_cohorts(a.system) as present:
        print('cohorts', present, flush=True)
        XD.score(a.system)


if __name__ == '__main__':
    main()
