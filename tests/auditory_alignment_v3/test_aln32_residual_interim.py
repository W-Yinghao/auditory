"""ADDENDUM_10 §5 synthetic check of aln32_residual_interim: known effects, wording, epoch-0 fractions."""
import numpy as np

from auditory_alignment_v3 import aln32_residual_interim as RS
from auditory_alignment_v3 import bc_interim as BI


def _m(ll):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": 40, "n_queries": 20}


def _ev(effect, fold):
    rng = np.random.default_rng(int(1000 * effect) % 997 + fold)
    pp = {}
    for j in range(8):
        reg = 4.0 + 0.1 * j - effect + 0.005 * rng.standard_normal()
        pp[f"P{fold}{j}"] = {"group": "ha", "n_segments": 20, **{f"{rd}/{k}": _m(reg + (1.0 if k == "mismatched_eeg" else 0) if k != "hard" else 2.5)
                                                                  for rd in ("unified", "native") for k in ("regular", "mismatched_eeg", "hard")}}
    return {"per_participant": pp}


def test_residual_families():
    eff = {"residual_aligned_pretrained": 0.3, "residual_aligned_random": 0.1, "residual_small_capacity": 0.05}
    rows, recs = [], {}
    for fold in (0, 1):
        for o in RS.OBJS:
            e = f"L{fold}{o}"
            rows.append({"experiment_id": e, "family_id": "A_LOCAL", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                         "spec": {"objective": o, "target": "local", "architecture": "lag_local_tokens", "window": "full", "projection_dim": 32}})
            recs[e] = {"status": "complete", "eval": _ev(0.0, fold)}
            for v, a in RS.CONF:
                e = f"R{fold}{o}{v}{a}"
                rows.append({"experiment_id": e, "family_id": "ALN32_RESIDUAL", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                             "spec": {"objective": o, "target": "local", "architecture": a, "variant": v}})
                recs[e] = {"status": "complete", "eval": _ev(eff[v], fold), "epoch0_selected": v == "residual_small_capacity"}
    orig = BI.cfg_of
    try:
        BI.cfg_of = RS.cfg
        out = RS.aggregate(BI.load_continuous(rows, recs.get, {}), rows, recs.get)
    finally:
        BI.cfg_of = orig
    f = out["families"]
    assert abs(f["RS-VALUE|dtu|NCE"]["members"]["reve/residual_aligned_pretrained"]["est"] - 0.3) < 0.02
    assert abs(f["RS-ATTRIB|dtu|CS_SINGLE|reve"]["members"]["pretrained_vs_small"]["est"] - 0.25) < 0.02
    assert out["wording"]["dtu|NCE|reve"]["wording"] == "complement from the pretrained representation"
    assert out["epoch0"]["RS|dtu|NCE|small_capacity_branch|residual_small_capacity"]["fraction_epoch0"] == 1.0
