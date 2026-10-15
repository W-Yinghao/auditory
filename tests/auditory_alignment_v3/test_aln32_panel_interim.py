"""ADDENDUM_11 synthetic check of aln32_panel_interim: per-seed and three-seed role contrasts recovered; incomplete seeds reported."""
import numpy as np

from auditory_alignment_v3 import aln32_panel_interim as PN
from auditory_alignment_v3 import bc_interim as BI


def _m(ll):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": 40, "n_queries": 20}


def _rec(effect, fold, sd):
    rng = np.random.default_rng((int(1000 * effect) % 997 + fold) * 7 + sd % 13)
    pp = {}
    for j in range(8):
        reg = 4.0 + 0.1 * j - effect + 0.005 * rng.standard_normal()
        pp[f"P{fold}{j}"] = {"group": "ha", "n_segments": 20, **{f"{rd}/{k}": _m(reg + (1.0 if k == "mismatched_eeg" else 0) if k != "hard" else 2.5)
                                                                  for rd in ("unified", "native") for k in ("regular", "mismatched_eeg", "hard")}}
    return {"status": "complete", "eval": {"per_participant": pp}}


def test_panel_roles():
    rows, recs = [], {}

    def add(fam, spec, eff, seeds=PN.SEEDS):
        for sd in seeds:
            for fold in (0, 1):
                e = f"{fam}{len(rows)}"
                rows.append({"experiment_id": e, "family_id": fam, "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": sd, "spec": {**spec, "objective": "NCE", "target": "local"}})
                recs[e] = _rec(eff, fold, sd)
    add("ALN32_LOCAL_SUPPORT", {"variant": "local_aligned1000"}, 0.0)
    for a in BI.ARCH:
        add("B_ALIGNED", {"architecture": a, "adaptation": "pretrained_frozen"}, 0.2)
        add("B_ALIGNED", {"architecture": a, "adaptation": "pretrained_peft"}, 0.25, seeds=(3401, 3407))  # 3413 missing
    orig = BI.cfg_of
    try:
        BI.cfg_of = PN.cfg
        out = PN.aggregate(BI.load_continuous(rows, recs.get, {}))
    finally:
        BI.cfg_of = orig
    m = out["per_seed"]["aligned_access_matched|dtu|3407"]["members"]["reve"]
    assert abs(m["est"] - 0.2) < 0.02
    assert abs(out["three_seed"]["aligned_access_matched|dtu"]["members"]["reve"]["est"] - 0.2) < 0.02
    assert out["availability"]["dtu|3seed|adaptation|reve"] is False and "adaptation|dtu" not in out["three_seed"]
