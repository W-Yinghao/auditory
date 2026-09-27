"""PF2 analyses (docs/auditory_pf/PF2_PROTOCOL_FROZEN.md): R2-A replication of H1, R2-B w_late beyond age,
R2-C condition-specific aggregates, R2-D all-trial curves, R2-E stability. Same children as round 1."""
from __future__ import annotations

import numpy as np

from . import stats as st
from .analysis_b1 import B1
from .e2e import permuted_labels
from .runtime import cfg, open_run, private_dir, read_json, stable_int, write_json_atomic


def _nested_auc(X, y, splits) -> float:
    """Mean OOF AUC over repeated stratified 5-fold splits; standardised, balanced logistic with fixed C = 1."""
    aucs = []
    for rep in splits:
        pred = np.full(len(y), np.nan)
        for tr, te in rep:
            z = st.Standardizer().fit(X[tr])
            m = st.logistic_fit(z.transform(X[tr]), y[tr], C=1.0)
            pred[te] = m.decision_function(z.transform(X[te]))
        aucs.append(st.auc(y, pred))
    return float(np.mean(aucs))


def r2b(config, b: B1, w: dict[int, float], stage: dict[int, float]) -> dict:
    from sklearn.model_selection import StratifiedKFold
    kids = [c for c in b.E if np.isfinite(w.get(c, np.nan))]
    y = np.array([stage[c] for c in kids]).astype(int)
    age = np.array([b.ch.loc[c, "age_months"] for c in kids], float)
    wv = np.array([w[c] for c in kids], float)
    R = int(cfg(config, "round2.cv_repeats"))
    splits = [list(StratifiedKFold(5, shuffle=True, random_state=1000 + r).split(np.zeros(len(y)), y)) for r in range(R)]
    a_age = _nested_auc(age[:, None], y, splits)
    a_both = _nested_auc(np.column_stack([age, wv]), y, splits)
    G = a_both - a_age
    q = int(cfg(config, "round2.age_bins"))
    bins = np.digitize(age, np.quantile(age, np.linspace(0, 1, q + 1)[1:-1]))
    null = []
    for p in range(1, int(cfg(config, "round2.perm_r2b")) + 1):
        rng = np.random.default_rng(stable_int("pf2_r2b", p))
        wp = wv.copy()
        for g in np.unique(bins):
            m = np.flatnonzero(bins == g)
            wp[m] = wv[m][rng.permutation(len(m))]
        null.append(_nested_auc(np.column_stack([age, wp]), y, splits) - a_age)
    # descriptive: rank partial association of w_late with stage given age
    from scipy.stats import rankdata
    ra, rw, ry = rankdata(age), rankdata(wv), rankdata(y)
    res = lambda v: v - np.polyval(np.polyfit(ra, v, 1), ra)  # noqa: E731
    partial = float(np.corrcoef(res(rw), res(ry))[0, 1])
    return {"n": len(kids), "auc_age": a_age, "auc_age_plus_w": a_both, "gain": G, "perm_p": st.perm_p(G, null),
            "null_mean": float(np.mean(null)), "partial_rank_corr_w_stage_given_age": partial,
            "age_bin_sizes": np.bincount(bins).tolist()}


def icc1(M: np.ndarray) -> float:
    """One-way random-effects ICC(1) for an [n_children, k_partitions] matrix."""
    M = M[np.isfinite(M).all(1)]
    n, k = M.shape
    grand = M.mean()
    msb = k * np.sum((M.mean(1) - grand) ** 2) / (n - 1)
    msw = np.sum((M - M.mean(1, keepdims=True)) ** 2) / (n * (k - 1))
    return float((msb - msw) / (msb + (k - 1) * msw))


def cmd_analyze2(args, config) -> dict:
    run = open_run("analyze2", args.run, config, args=vars(args))
    b = B1(config, prepare_run=args.prepare_run, stim_run=args.stim_run, embed_source="native")
    stage = {c: b.stage[c] for c in b.E}
    out = {"n_eligible": len(b.E), "partitions": b.seeds, "units_loaded": len(b.units)}
    # R2-A
    a1 = b.a1_scores()
    A = b.auc_seeds(a1["oof"], stage)
    P = int(cfg(config, "round2.perm_r2a"))
    null = [b.auc_seeds(a1["oof"], permuted_labels(b.co, p, "stage"))["mean"] for p in range(1, P + 1)]
    sens = [c for c in b.E if b.ch.loc[c, "new02"] == 1 or b.ch.loc[c, "stage"] == 1]
    out["R2A"] = {"auc": A, "perm_p": st.perm_p(A["mean"], null), "ci": b.boot_auc(a1["oof"], stage),
                  "partitions_ge_065": int(sum(v >= 0.65 for v in A["per_seed"])),
                  "sens_0_2_vs_13": b.auc_seeds(a1["oof"], stage, sens),
                  "strict_single_draw": b.auc_seeds(b.a1_scores(strict=True)["oof"], stage)}
    # R2-B (per-child w_late = mean over partitions of the out-of-fold value)
    w = b.child_mean(a1["oof"], b.E)
    out["R2B"] = r2b(config, b, w, stage)
    # R2-C
    dev, std_ = b.b_scores(stage, kind="dev"), b.b_scores(stage, kind="std")
    Ad, As = b.auc_seeds(dev["oof"], stage), b.auc_seeds(std_["oof"], stage)
    rows = [read_json(p) for p in sorted(private_dir(config, args.perm_run).glob("p*.json"))]
    dv = np.array([r["auc_dev"] for r in rows]) if rows else np.array([])
    sv = np.array([r["auc_std"] for r in rows]) if rows else np.array([])
    out["R2C"] = {"auc_dev": Ad, "auc_std": As, "diff": Ad["mean"] - As["mean"],
                  "diff_ci": b.boot_diff(dev["oof"], std_["oof"], stage), "n_perm": len(rows),
                  "p_diff": st.perm_p(Ad["mean"] - As["mean"], dv - sv) if rows else None,
                  "p_dev": st.perm_p(Ad["mean"], dv) if rows else None,
                  "auc_both": b.auc_seeds(b.b_scores(stage)["oof"], stage)}
    # R2-D (secondary): every accepted trial instead of the fixed budget
    oof_all = {}
    for s in b.seeds:
        oof_all[s] = {}
        for k in range(b.n_outer):
            oof_all[s].update(b.w_late(s, k, b.test_children(s, k, b.E), strict="all"))
    out["R2D"] = {"auc_all_trials": b.auc_seeds(oof_all, stage), "auc_budget": A}
    # R2-E: stability of per-child w_late across partitions and against round 1
    M = np.array([[a1["oof"][s].get(c, np.nan) for s in b.seeds] for c in b.E])
    r1 = read_json(private_dir(config, "analyze_001") / "private_real.json")["a1_oof"]
    w1 = {int(c): np.nanmean([r1[s].get(str(c), np.nan) for s in r1]) for c in b.E}
    out["R2E"] = {"icc1_across_partitions": icc1(M),
                  "spearman_round2_vs_round1": st.spearman([w[c] for c in b.E], [w1[c] for c in b.E])}
    C = claims2(out)
    write_json_atomic(run["public"] / "summary_pf2.json", {"results": out, "claims": C}, private=False)
    write_json_atomic(run["private"] / "w_late_round2.json", {str(c): v for c, v in w.items()}, private=True)
    return {"claims": {k: v["status"] for k, v in C.items()}}


def claims2(o: dict) -> dict:
    from .analyze import status
    C = {}
    a, p = o["R2A"]["auc"]["mean"], o["R2A"]["perm_p"]
    C["R2-A"] = {"auc": a, "perm_p": p, "status": status(supported=a >= 0.65 and p < 0.05, refuted=p > 0.05 and a < 0.60,
                                                          partial=(a >= 0.65) != (p < 0.05), direction=a > 0.5)}
    g, pb = o["R2B"]["gain"], o["R2B"]["perm_p"]
    C["R2-B"] = {"gain": g, "perm_p": pb, "status": status(supported=g >= 0.03 and pb < 0.05, refuted=g <= 0 or pb > 0.20,
                                                           partial=(g >= 0.03) != (pb < 0.05), direction=g > 0)}
    d, pc = o["R2C"]["diff"], o["R2C"]["p_diff"]
    if pc is None:
        C["R2-C"] = {"diff": d, "status": status(not_evaluable="permutations_missing")}
    else:
        C["R2-C"] = {"diff": d, "p_diff": pc, "status": status(supported=d >= 0.10 and pc < 0.05, refuted=d <= 0 or pc > 0.20,
                                                               partial=(d >= 0.10) != (pc < 0.05), direction=d > 0)}
    return C
