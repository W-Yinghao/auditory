"""ADDENDUM_12 synthetic check of d_lag_interim: attention level vs chance, integrator and task contrasts, adaptation gain, coverage."""
import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import d_lag_interim as DL


def _m(ll):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": 40, "n_queries": 20}


def test_d_lag_families():
    rows, recs = [], {}
    rng = np.random.default_rng(0)
    for fold in (0, 1):
        for t, o in DL.TASKS:
            e = f"A{fold}{t}{o}"
            rows.append({"experiment_id": e, "family_id": "D_ATTENTION", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                         "spec": {"architecture": "lag_local_tokens", "integrator": "mean_score", "training_task": t, "objective": o}})
            acc = 0.7 if t == "alignment_plus_selection" else 0.6
            pp = {f"P{fold}{j}": {"group": "nh", **{f"{w}s|{rd}": {"mean_score_accuracy": acc + 0.01 * j * 0 + 0.002 * rng.standard_normal(), "learned_temporal_accuracy": acc + 0.05,
                                                                   "mean_margin": 0.1, "n_windows": 10} for w in DL.WINS for rd in ("unified", "native")}} for j in range(8)}
            recs[e] = {"status": "complete", "eval": {"attention_windows": {"per_participant": pp}}}
        for o in ("NCE", "CS_SINGLE"):
            for a in DL.ADAPTERS:
                e = f"D{fold}{o}{a}"
                rows.append({"experiment_id": e, "family_id": "D_ADAPT", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                             "spec": {"architecture": "lag_local_tokens", "objective": o, "adapter": a}})
                g = 0.5 + (0.2 if a == "input_spatial" else 0.0)
                pp = {f"P{fold}{j}": {"group": "nh", **{f"support_{sf}": {"unified": {"gain_bits": g + (0.05 if sf == "0.3" and a != "none" else 0) + 0.001 * rng.standard_normal() * (a != "none"),
                                                                                      "rank_pct": 0.2, "top1": 0.1, "n_query": 10}, "native": {"gain_bits": g, "rank_pct": 0.2, "top1": 0.1, "n_query": 10}, "n_support": 3}
                                                        for sf in DL.SUPPORTS}} for j in range(8)}
                recs[e] = {"status": "complete", "eval": {"per_participant": pp}}
    load = recs.get
    vals, grp, status, cv_rows, cv_load = DL.collect(rows, load)
    BI.PDIR.update(DL.NEW_DIR)
    att = DL.run_fams(DL.att_families(), vals, grp, ("acc",), "acc", [])
    m = att["families"]["AT-LEVEL|dtu|attended_alignment|NCE"]["members"]["5s"]
    assert abs(m["est"] - 0.1) < 0.01 and m["class"] == "I>0"
    assert abs(att["families"]["AT-INTEGRATOR|dtu|attended_alignment|NCE"]["members"]["10s"]["est"] - 0.05) < 0.01
    assert abs(att["families"]["AT-TASK|dtu|5s"]["members"]["align->align+sel NCE"]["est"] - 0.1) < 0.01
    ad = DL.run_fams(DL.ad_families(), vals, grp, ("gain_bits",), "gain_bits", [])
    assert abs(ad["families"]["AD-GAIN|dtu|NCE|0.1"]["members"]["input_spatial"]["est"] - 0.2) < 0.01
    assert abs(ad["families"]["AD-SUPPORT|dtu|NCE"]["members"]["input_spatial"]["est"] - 0.05) < 0.01
