"""ADDENDUM_06 §5 synthetic check of aligned_interim: known paired effects and signs are recovered in every family."""
import numpy as np

from auditory_alignment_v3 import aligned_interim as AI
from auditory_alignment_v3 import bc_interim as BI


def _m(ll, nc=40):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": nc, "n_queries": 20}


def _rec(effect, fold):
    rng = np.random.default_rng(int(1000 * effect) % 997 + fold)
    pp = {}
    for j in range(8):
        reg = 4.0 + 0.1 * j - effect + 0.005 * rng.standard_normal()
        pp[f"P{fold}{j}"] = {"group": "ha", "n_segments": 20, **{f"{rd}/{k}": _m(reg + (1.0 if k == "mismatched_eeg" else 0) if k != "hard" else 2.5)
                                                                  for rd in ("unified", "native") for k in ("regular", "mismatched_eeg", "hard")}}
    return {"status": "complete", "eval": {"per_participant": pp}}


def test_aligned_families_recover_effects():
    rows, recs = [], {}
    eff = {("A", "dtu", "NCE", "reve", ad): 0.3 for ad in BI.ADAPT}
    eff[("A", "dtu", "NCE", "reve", "pretrained_full")] = 0.5

    def add(fam, spec, c):
        for fold in (0, 1):
            e = f"{fam}_{len(rows)}"
            rows.append({"experiment_id": e, "family_id": fam, "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401, "spec": {**spec, "objective": "NCE", "target": "local"}})
            recs[e] = _rec(eff.get(c, 0.0), fold)
    add("A_LOCAL", {"architecture": "lag_local_tokens", "window": "full", "projection_dim": 32}, ("L", "dtu", "NCE"))
    for a in BI.ARCH:
        for ad in BI.ADAPT:
            add("B_DENSE", {"architecture": a, "adaptation": ad, "readout": "channel_phase_linear"}, ("B", "dtu", "NCE", a, ad, "channel_phase_linear"))
            add("B_ALIGNED", {"architecture": a, "adaptation": ad, "readout": "aligned_patch_linear"}, ("A", "dtu", "NCE", a, ad))
    orig = BI.cfg_of
    try:
        BI.cfg_of = AI.cfg
        out = AI.aggregate(BI.load_continuous(rows, recs.get, {}))
    finally:
        BI.cfg_of = orig
    f = out["families"]
    assert abs(f["AL-INTERFACE|dtu|NCE|reve"]["members"]["pretrained_peft"]["est"] - 0.3) < 0.02
    assert abs(f["AL-LOCAL|dtu|NCE|reve"]["members"]["pretrained_full"]["est"] - 0.5) < 0.02 and f["AL-LOCAL|dtu|NCE|reve"]["members"]["pretrained_full"]["class"] == "I>0"
    m = f["AL-INIT|dtu|NCE|reve"]["members"]["pretrained_full"]
    assert abs(m["est"] - 0.2) < 0.02 and m["tag"].startswith("initialization")
    assert abs(f["AL-ADAPT|dtu|NCE|reve"]["members"]["pretrained_full"]["est"] - 0.2) < 0.02
    assert not [x for x in out["excluded_pairs"] if "|dtu|" in x]
