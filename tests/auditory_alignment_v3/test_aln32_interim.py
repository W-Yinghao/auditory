"""ADDENDUM_07 §5 synthetic check of aln32_interim: known effects and signs recovered in AI-* and TF-* families."""
import numpy as np

from auditory_alignment_v3 import aln32_interim as AI
from auditory_alignment_v3 import bc_interim as BI


def _m(ll):
    return {"top1": 0.3, "top5": 0.6, "mrr": 0.4, "rank_pct": 0.2, "logloss_bits": ll, "n_candidates": 40, "n_queries": 20}


def _rec(effect, fold):
    rng = np.random.default_rng(int(1000 * effect) % 997 + fold)
    pp = {}
    for j in range(8):
        reg = 4.0 + 0.1 * j - effect + 0.005 * rng.standard_normal()
        pp[f"P{fold}{j}"] = {"group": "ha", "n_segments": 20, **{f"{rd}/{k}": _m(reg + (1.0 if k == "mismatched_eeg" else 0) if k != "hard" else 2.5)
                                                                  for rd in ("unified", "native") for k in ("regular", "mismatched_eeg", "hard")}}
    return {"status": "complete", "eval": {"per_participant": pp}}


def test_families_recover_effects():
    rows, recs = [], {}
    eff = {("L1", "dtu", "NCE"): 0.1, ("A", "dtu", "NCE", "reve", "pretrained_frozen"): 0.3, ("F2", "dtu", "NCE", "reve", "pretrained_frozen"): 0.25,
           ("T", "dtu", "NCE", "reve", "pretrained_full", "warmup_then_all_v1", 3e-4): 0.4}

    def add(fam, spec, c):
        for fold in (0, 1):
            e = f"{fam}_{len(rows)}"
            rows.append({"experiment_id": e, "family_id": fam, "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                         "spec": {**spec, "objective": "NCE", "target": "local"}})
            recs[e] = _rec(eff.get(c, 0.0), fold)
    add("A_LOCAL", {"architecture": "lag_local_tokens", "window": "full", "projection_dim": 32}, ("L0", "dtu", "NCE"))
    for v, k in (("local_aligned1000", "L1"), ("raw_aligned1000_ridge", "R1"), ("raw_post600_ridge", "R0")):
        add("ALN32_LOCAL_SUPPORT", {"architecture": "lag_local_tokens", "window": "full", "variant": v}, (k, "dtu", "NCE"))
    for a in BI.ARCH:
        for ad in BI.ADAPT:
            add("B_ALIGNED", {"architecture": a, "adaptation": ad}, ("A", "dtu", "NCE", a, ad))
        for ad in ("pretrained_frozen", "pretrained_peft"):
            add("ALN32_POSTONLY_FM", {"architecture": a, "adaptation": ad}, ("F2", "dtu", "NCE", a, ad))
        for ad in AI.TINIT:
            for rc in AI.RECIPES:
                for lr in AI.LRS:
                    add("ALN32_TRUE_FULL", {"architecture": a, "adaptation": ad, "recipe": rc, "lr_backbone": lr}, ("T", "dtu", "NCE", a, ad, rc, lr))
    orig = BI.cfg_of
    try:
        BI.cfg_of = AI.cfg
        out = AI.aggregate(BI.load_continuous(rows, recs.get, {}))
    finally:
        BI.cfg_of = orig
    f = out["families"]
    assert abs(f["AI-PASTEEG|dtu"]["members"]["L0->L1"]["est"] - 0.1) < 0.02
    assert abs(f["AI-ACCESS|dtu|reve"]["members"]["pretrained_frozen"]["est"] - 0.2) < 0.02
    assert abs(f["AI-POSTONLY|dtu|reve"]["members"]["pretrained_frozen"]["est"] - 0.25) < 0.02
    assert abs(f["AI-CONTEXT|dtu|reve"]["members"]["pretrained_frozen"]["est"] - 0.05) < 0.02
    m = f["TF-INIT|dtu|reve"]["members"]["warmup_then_all_v1/lr0.0003"]
    assert abs(m["est"] - 0.4) < 0.02 and m["class"] == "I>0"
    assert abs(f["TF-VS-LEGACY|dtu|reve"]["members"]["pretrained_full/warmup_then_all_v1/lr0.0003"]["est"] - 0.4) < 0.02
    assert abs(f["TF-LOCAL|dtu|reve"]["members"]["L1->pretrained_full/warmup_then_all_v1/lr0.0003"]["est"] - 0.3) < 0.02
    assert not [x for x in out["excluded_pairs"] if "|dtu" in x]
