"""ADDENDUM_09 §5 synthetic check of aln32_complement_interim: pseudo-unit expansion, known effects, mechanical wording."""
import numpy as np

from auditory_alignment_v3 import aln32_complement_interim as SC
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


def test_expand_effects_wording():
    eff = {"local_only": 0.0, "local_refit_capacity": 0.0, "aligned_pretrained": 0.3, "aligned_random": 0.1, "small_context": 0.05, "concat": 0.2}
    rows, recs = [], {}
    for fold in (0, 1):
        for a in BI.ARCH:
            for base in ("L0", "L1"):
                e = f"U{fold}{a}{base}"
                rows.append({"experiment_id": e, "family_id": "ALN32_SIMPLE_COMPLEMENT", "dataset": "dtu", "subject_fold": fold, "content_fold": 0, "seed": 3401,
                             "spec": {"objective": "NCE", "target": "local", "architecture": a, "base": base}})
                recs[e] = {"status": "complete", "eval_variants": {v: _ev(x, fold) for v, x in eff.items()}}
    prow, pload = SC.expand(rows, recs.get)
    assert len(prow) == 8 * 6 and pload(prow[0]["experiment_id"])["eval"] is not None
    orig = BI.cfg_of
    try:
        BI.cfg_of = SC.cfg
        out = SC.aggregate(BI.load_continuous(prow, pload, {}))
    finally:
        BI.cfg_of = orig
    f = out["families"]
    assert abs(f["SC-VALUE|dtu|reve|L1"]["members"]["aligned_pretrained"]["est"] - 0.3) < 0.02
    assert abs(f["SC-ATTRIB|dtu|reve|L1"]["members"]["pretrained_vs_random"]["est"] - 0.2) < 0.02
    assert out["wording"]["dtu|reve|L1"]["wording"] == "complement from the pretrained representation"
    assert "context-assisted" in out["wording"]["dtu|reve|L0"]["wording"]
