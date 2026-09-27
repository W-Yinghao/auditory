"""B1 analyses (protocol sections 4, 6): models (a1) (a2) (b) (c), baselines, H1-H6, H9, H11-H15.

All scores are out-of-fold per partition seed; statistics average the 3 seeds. Per-child tables
stay under private/; results/ receives aggregates only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

from . import stats as st
from .cohort import Cohort
from .e2e import permuted_labels
from .runtime import ROOT, cfg, private_dir, results_dir


def centres_of(config) -> np.ndarray:
    rate, pre = 250.0, 0.2
    win = int(round(float(cfg(config, "windows.width_s")) * rate))
    step = int(round(float(cfg(config, "windows.step_s")) * rate))
    return np.array([round((s + win / 2) / rate - pre, 4) for s in range(0, 200 - win + 1, step)])


class B1:
    def __init__(self, config, *, prepare_run="prepare_001", stim_run="stim_001", e2e_run="e2e_001", features_run="features_001",
                 embed_source: str = "xfit"):
        self.config = config
        self.embed_source = embed_source
        self.co = Cohort(config, prepare_run)
        self.stim_dir = private_dir(config, stim_run)
        self.e2e_dir = private_dir(config, e2e_run)
        self.feat_dir = private_dir(config, features_run)
        self.n_outer = int(cfg(config, "folds.n_outer"))
        self.seeds = self.co.seeds
        self.centres = centres_of(config)
        self.n_time = len(self.centres)
        rec, ch = self.co.rec, self.co.ch
        self.ch = ch.set_index("child")
        self.E = sorted(ch[(ch.group == "labelled") & (ch.eligible == True)].child.astype(int))          # noqa: E712
        self.NH = sorted(ch[(ch.group == "nh") & (ch.nh_eligible == True)].child.astype(int))           # noqa: E712
        self.primary = {int(c): int(r) for c, r in zip(ch.child, ch.primary_rec)}
        self.stage = {c: float(self.ch.loc[c, "stage"]) for c in self.E}
        self.units = {}
        for s in self.seeds:
            for k in range(self.n_outer):
                p = self.stim_dir / f"unit_s{s}_k{k}" / "exports.npz"
                if p.exists():
                    with np.load(p, allow_pickle=False) as z:
                        self.units[(s, k)] = {n: z[n] for n in z.files}
                    if embed_source == "mo":        # correction: every child embedded by the fold's M_o
                        with np.load(p.parent / "exports_mo.npz", allow_pickle=False) as z:
                            self.units[(s, k)]["agg_base"] = z["agg_base"]
                            self.units[(s, k)]["agg_occ"] = z["agg_occ"]
                    elif embed_source not in ("xfit", "native"):   # native: agg_base as exported (stim2 = single encoder)
                        raise ValueError(embed_source)
        self.K = self.co.draw_dev.shape[2]
        self.D = self.co.draw_dev.shape[1]
        self._curve_cache = {}

    # ------------------------------------------------------------------ helpers
    def fold_of(self, s: int) -> dict[int, int]:
        return self.co.outer(s)

    def test_children(self, s, k, pool):
        f = self.fold_of(s)
        return [c for c in pool if f[c] == k]

    def train_children(self, s, k, pool):
        f = self.fold_of(s)
        return [c for c in pool if f[c] != k]

    def budget(self, rec: int, d: int):
        std_i = self.co.budget_idx(rec, d, 0)
        dev_i = self.co.budget_idx(rec, d, 1)
        idx = np.concatenate([std_i, dev_i])
        y = np.concatenate([np.zeros(len(std_i), int), np.ones(len(dev_i), int)])
        return idx, y

    def curve(self, s, k, child, strict=False) -> np.ndarray | None:
        """D-averaged (or draw-0) time-occlusion drop curve of the child's primary record [19].

        strict="all" uses every accepted trial of the primary record instead of the fixed budget (PF2 R2-D).
        """
        key = (s, k, child, strict)
        if key in self._curve_cache:
            return self._curve_cache[key]
        r = self.primary[child]
        if strict == "all":
            u = self.units[(s, k)]
            idx = np.flatnonzero(self.co.t_record == r)
            y = self.co.t_y[idx]
            base = st.auc(y, u["diff_base"][idx])
            c = np.array([base - st.auc(y, u["diff_occ"][w, idx]) for w in range(self.n_time)])
            self._curve_cache[key] = c
            return c
        if r not in self.co.draw_row:
            self._curve_cache[key] = None
            return None
        u = self.units[(s, k)]
        draws = [0] if strict else range(self.D)
        out = np.zeros((len(list(draws)), self.n_time))
        for i, d in enumerate(draws):
            idx, y = self.budget(r, d)
            base = st.auc(y, u["diff_base"][idx])
            for w in range(self.n_time):
                out[i, w] = base - st.auc(y, u["diff_occ"][w, idx])
        c = out.mean(0)
        self._curve_cache[key] = c
        return c

    def features(self, s, k, child, kind="both", strict=False, occl: int | None = None) -> np.ndarray | None:
        r = self.primary[child]
        u = self.units[(s, k)]
        if occl is None:
            a = u["agg_base"][r]                                    # [D, 2, 192]
            if not np.isfinite(a).all():
                return None
            a = a[0] if strict else a.mean(0)
        else:
            a = u["agg_occ"][occl, r]                               # [2, 192] D-averaged
            if not np.isfinite(a).all():
                return None
        dev, std = a[1], a[0]
        return {"both": np.concatenate([dev, std]), "dev": dev, "std": std}[kind]

    # ------------------------------------------------------------------ model (a1): fold-internal templates
    def templates(self, s, k, strict=False):
        mask = self.centres >= float(cfg(self.config, "windows.template_min_centre_s"))
        cen = self.centres[mask]
        pool = self.co.ch.child.astype(int).tolist()
        early, late = [], []
        for c in self.train_children(s, k, pool):
            cv = self.curve(s, k, c, strict)
            if cv is None:
                continue
            cv = cv[mask]
            (early if cen[int(np.argmax(cv))] < 0.2 else late).append(cv)
        E = np.clip(np.mean(early, 0), 0, None) if early else np.zeros(mask.sum())
        L = np.clip(np.mean(late, 0), 0, None) if late else np.zeros(mask.sum())
        return mask, E, L, len(early), len(late)

    def w_late(self, s, k, children, strict=False) -> dict[int, float]:
        mask, E, L, _, _ = self.templates(s, k, strict)
        out = {}
        for c in children:
            cv = self.curve(s, k, c, strict)
            if cv is None:
                continue
            w, _ = nnls(np.column_stack([E, L]), np.clip(cv[mask], 0, None))
            out[c] = float(w[1] / w.sum()) if w.sum() > 1e-12 else float("nan")
        return out

    def a1_scores(self, strict=False) -> dict:
        """{seed: {child: w_late}} for eligible labelled + NH test children; plus training-side values."""
        oof, train_side = {}, {}
        for s in self.seeds:
            oof[s] = {}
            for k in range(self.n_outer):
                test = self.test_children(s, k, self.E + self.NH)
                oof[s].update(self.w_late(s, k, test, strict))
                train_side[(s, k)] = self.w_late(s, k, self.train_children(s, k, self.E), strict)
        return {"oof": oof, "train": train_side}

    # ------------------------------------------------------------------ model (a2): label-informed template
    def a2_scores(self, labels: dict[int, float]) -> dict:
        mask = self.centres >= float(cfg(self.config, "windows.template_min_centre_s"))
        oof = {}
        for s in self.seeds:
            oof[s] = {}
            for k in range(self.n_outer):
                tr = self.train_children(s, k, self.E)
                c1 = [self.curve(s, k, c)[mask] for c in tr if labels[c] == 1]
                c0 = [self.curve(s, k, c)[mask] for c in tr if labels[c] == 0]
                T = np.mean(c1, 0) - np.mean(c0, 0)
                for c in self.test_children(s, k, self.E + self.NH):
                    cv = self.curve(s, k, c)
                    if cv is not None:
                        oof[s][c] = float(cv[mask] @ T)
        return oof

    # ------------------------------------------------------------------ model (b)
    def b_scores(self, labels: dict[int, float], kind="both", strict=False, occl=None, target="stage") -> dict:
        grid = cfg(self.config, "stats.logistic_C")
        oof, info = {}, {}
        for s in self.seeds:
            oof[s] = {}
            for k in range(self.n_outer):
                tr = [c for c in self.train_children(s, k, self.E) if self.features(s, k, c, kind, strict, occl) is not None]
                te = [c for c in self.test_children(s, k, self.E + self.NH) if self.features(s, k, c, kind, strict, occl) is not None]
                X = np.stack([self.features(s, k, c, kind, strict, occl) for c in tr])
                y = np.array([labels[c] for c in tr]).astype(int)
                f, inf = st.logistic_cv(X, y, grid, seed=s * 10 + k)
                sc = f(np.stack([self.features(s, k, c, kind, strict, occl) for c in te]))
                oof[s].update(dict(zip(te, sc.tolist())))
                info[(s, k)] = inf
        return {"oof": oof, "info": info}

    def b_train_crossfit(self, s, k, labels, kind="both") -> dict[int, float]:
        """Nested inner cross-fitted (b) stage scores for the outer-training eligible children."""
        grid = cfg(self.config, "stats.logistic_C")
        inner = self.co.inner(s, k)
        tr = self.train_children(s, k, self.E)
        out = {}
        for i in range(int(cfg(self.config, "folds.n_inner"))):
            fit_c = [c for c in tr if inner[c] != i]
            pred_c = [c for c in tr if inner[c] == i]
            if not pred_c:
                continue
            X = np.stack([self.features(s, k, c, kind) for c in fit_c])
            y = np.array([labels[c] for c in fit_c]).astype(int)
            f, _ = st.logistic_cv(X, y, grid, seed=s * 100 + k * 10 + i)
            out.update(dict(zip(pred_c, f(np.stack([self.features(s, k, c, kind) for c in pred_c])).tolist())))
        return out

    # ------------------------------------------------------------------ model (c)
    def c_scores(self, variant: str, p: int = 0, strict=False) -> dict | None:
        oof, prior = {}, {}
        for s in self.seeds:
            oof[s] = {}
            for k in range(self.n_outer):
                path = self.e2e_dir / variant / f"p{p:03d}_s{s}_k{k}.npz"
                if not path.exists():
                    return None
                with np.load(path, allow_pickle=False) as z:
                    recs, sc = z["recs"], z["scores"]
                    prior[(s, k)] = float(z["prior_log_odds"])
                child_of = self.co.rec.child.to_numpy()
                vals = sc[:, 0] if strict else sc.mean(1)
                for r, v in zip(recs, vals):
                    oof[s][int(child_of[int(r)])] = float(v)
        return {"oof": oof, "prior": prior}

    # ------------------------------------------------------------------ evaluation helpers
    def auc_seeds(self, oof: dict, labels: dict[int, float], children=None) -> dict:
        children = self.E if children is None else children
        per = []
        for s in self.seeds:
            cs = [c for c in children if c in oof[s] and np.isfinite(oof[s][c])]
            per.append(st.auc([labels[c] for c in cs], [oof[s][c] for c in cs]))
        return {"mean": float(np.nanmean(per)), "per_seed": [float(v) for v in per], "min": float(np.nanmin(per)),
                "max": float(np.nanmax(per))}

    def boot_auc(self, oof: dict, labels: dict[int, float], children=None, B=None, seed=0) -> list:
        children = np.array(self.E if children is None else children)
        B = int(B or cfg(self.config, "stats.bootstrap"))
        rng = np.random.default_rng(seed)
        y = np.array([labels[c] for c in children])
        S = np.array([[oof[s].get(int(c), np.nan) for c in children] for s in self.seeds])
        vals = []
        for _ in range(B):
            i = rng.integers(0, len(children), len(children))
            vals.append(np.nanmean([st.auc(y[i], S[j, i]) for j in range(len(self.seeds))]))
        return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]

    def boot_diff(self, oof1, oof2, labels, children=None, B=None, seed=0) -> list:
        children = np.array(self.E if children is None else children)
        B = int(B or cfg(self.config, "stats.bootstrap"))
        rng = np.random.default_rng(seed)
        y = np.array([labels[c] for c in children])
        S1 = np.array([[oof1[s].get(int(c), np.nan) for c in children] for s in self.seeds])
        S2 = np.array([[oof2[s].get(int(c), np.nan) for c in children] for s in self.seeds])
        vals = []
        for _ in range(B):
            i = rng.integers(0, len(children), len(children))
            a = np.nanmean([st.auc(y[i], S1[j, i]) for j in range(len(self.seeds))])
            b = np.nanmean([st.auc(y[i], S2[j, i]) for j in range(len(self.seeds))])
            vals.append(a - b)
        return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]

    def child_mean(self, oof: dict, children) -> dict[int, float]:
        return {c: float(np.nanmean([oof[s].get(c, np.nan) for s in self.seeds])) for c in children}


# ============================================================================ SI helpers

def sir_labels(b: B1) -> dict[int, float]:
    return {c: float(b.ch.loc[c, "sir"]) for c in b.E}


def b_ord_scores(b: B1, sir: dict[int, float], *, crossfit_train=False, kind="both") -> dict:
    """Full-EEG ordinal SIR decoder (b-ord). Returns OOF latent and E[SIR] (+ nested training latents)."""
    grid = cfg(b.config, "stats.ordinal_lambda")
    lat, exp_, train_lat = {}, {}, {}
    for s in b.seeds:
        lat[s], exp_[s] = {}, {}
        for k in range(b.n_outer):
            tr = b.train_children(s, k, b.E)
            te = b.test_children(s, k, b.E)
            X = np.stack([b.features(s, k, c, kind) for c in tr])
            y = np.array([sir[c] for c in tr]).astype(int)
            f_lat, f_exp, inf = st.ordinal_cv(X, y, grid, seed=s * 10 + k)
            Xt = np.stack([b.features(s, k, c, kind) for c in te])
            lat[s].update(dict(zip(te, f_lat(Xt).tolist())))
            exp_[s].update(dict(zip(te, f_exp(Xt).tolist())))
            if crossfit_train:
                inner = b.co.inner(s, k)
                out = {}
                for i in range(int(cfg(b.config, "folds.n_inner"))):
                    fit_c = [c for c in tr if inner[c] != i]
                    pred_c = [c for c in tr if inner[c] == i]
                    if not pred_c:
                        continue
                    Xi = np.stack([b.features(s, k, c, kind) for c in fit_c])
                    yi = np.array([sir[c] for c in fit_c]).astype(int)
                    fl, _, _ = st.ordinal_cv(Xi, yi, [inf["lambda"]], seed=0)
                    out.update(dict(zip(pred_c, fl(np.stack([b.features(s, k, c, kind) for c in pred_c])).tolist())))
                train_lat[(s, k)] = out
    return {"latent": lat, "expected": exp_, "train_latent": train_lat}


def si_eval(b: B1, lat: dict, exp_: dict, sir: dict[int, float], children=None) -> dict:
    children = b.E if children is None else children
    high = {c: float(sir[c] > float(cfg(b.config, "labels.sir_threshold"))) for c in children}
    a = b.auc_seeds(lat, high, children)
    mae = [float(np.mean([abs(exp_[s][c] - sir[c]) for c in children if c in exp_[s]])) for s in b.seeds]
    return {"auc_sir_gt3": a, "mae": {"mean": float(np.mean(mae)), "per_seed": mae}}


def one_d_ordinal(b: B1, train_side: dict, oof_test: dict, sir: dict[int, float]) -> dict:
    """Second layer: ordinal SIR ~ 1-D score (score of training children cross-fitted)."""
    grid = cfg(b.config, "stats.ordinal_lambda")
    lat, exp_ = {}, {}
    for s in b.seeds:
        lat[s], exp_[s] = {}, {}
        for k in range(b.n_outer):
            trs = train_side[(s, k)]
            tr = [c for c in b.train_children(s, k, b.E) if c in trs and np.isfinite(trs[c])]
            te = [c for c in b.test_children(s, k, b.E) if c in oof_test[s] and np.isfinite(oof_test[s][c])]
            X = np.array([[trs[c]] for c in tr])
            y = np.array([sir[c] for c in tr]).astype(int)
            f_lat, f_exp, _ = st.ordinal_cv(X, y, grid, seed=s * 10 + k)
            Xt = np.array([[oof_test[s][c]] for c in te])
            lat[s].update(dict(zip(te, f_lat(Xt).tolist())))
            exp_[s].update(dict(zip(te, f_exp(Xt).tolist())))
    return {"latent": lat, "expected": exp_}


def clinical_design(b: B1, train_c, test_c):
    age_tr = np.array([b.ch.loc[c, "age_months"] for c in train_c], float)
    dur_tr = np.log1p(np.array([b.ch.loc[c, "duration_months"] for c in train_c], float))
    fa = _spline(age_tr)
    fd = _spline(dur_tr)

    def design(cs):
        a = np.array([b.ch.loc[c, "age_months"] for c in cs], float)
        d = np.log1p(np.array([b.ch.loc[c, "duration_months"] for c in cs], float))
        return np.column_stack([fa(a), fd(d)])
    return design(train_c), design(test_c)


def _spline(values):
    try:
        return st.spline_basis(values)
    except ValueError:
        from sklearn.preprocessing import SplineTransformer
        t = SplineTransformer(n_knots=5, degree=3, knots="uniform", include_bias=False, extrapolation="linear")
        t.fit(np.asarray(values, float).reshape(-1, 1))
        return lambda v: t.transform(np.asarray(v, float).reshape(-1, 1))


def h14_models(b: B1, sir, z_train: dict, z_test: dict) -> dict:
    grid = cfg(b.config, "stats.ordinal_lambda")
    out = {"C": ({}, {}), "CZ": ({}, {})}
    for s in b.seeds:
        for key in out:
            out[key][0][s], out[key][1][s] = {}, {}
        for k in range(b.n_outer):
            tr = [c for c in b.train_children(s, k, b.E) if c in z_train[(s, k)]]
            te = b.test_children(s, k, b.E)
            Xtr, Xte = clinical_design(b, tr, te)
            y = np.array([sir[c] for c in tr]).astype(int)
            f_lat, f_exp, _ = st.ordinal_cv(Xtr, y, grid, seed=s * 10 + k)
            out["C"][0][s].update(dict(zip(te, f_lat(Xte).tolist())))
            out["C"][1][s].update(dict(zip(te, f_exp(Xte).tolist())))
            ztr = np.array([[z_train[(s, k)][c]] for c in tr])
            zte = np.array([[z_test[s][c]] for c in te])
            f_lat, f_exp, _ = st.ordinal_cv(np.column_stack([Xtr, ztr]), y, grid, seed=s * 10 + k)
            out["CZ"][0][s].update(dict(zip(te, f_lat(np.column_stack([Xte, zte])).tolist())))
            out["CZ"][1][s].update(dict(zip(te, f_exp(np.column_stack([Xte, zte])).tolist())))
    return out


# ============================================================================ per-child support/query report

def blocks_of(onset: np.ndarray, config) -> tuple[np.ndarray, np.ndarray]:
    """Block index and keep-mask (5 s guard, epoch -0.2..0.6 s) relative to the record's first trial."""
    bs, gs = float(cfg(config, "blocks.block_seconds")), float(cfg(config, "blocks.guard_seconds"))
    t = onset - onset.min()
    blk = np.floor(t / bs).astype(int)
    start = blk * bs
    keep = ((t - 0.2) - start >= gs) & ((start + bs) - (t + 0.6) >= gs)
    return blk, keep


def three_category(y, score, onset, config, rng) -> dict:
    blk, keep = blocks_of(onset, config)
    sup = keep & (blk % 2 == 0)
    qry = keep & (blk % 2 == 1)
    a_s = st.auc(y[sup], score[sup])
    if not np.isfinite(a_s) or a_s == 0.5:
        return {"auc_support": a_s, "auc_query": float("nan"), "p_query": float("nan"), "direction": 0, "category": "undetermined"}
    direction = 1 if a_s > 0.5 else -1
    a_q, p = st.query_block_test(y[qry], score[qry], direction, int(cfg(config, "stats.query_perm")), rng)
    cat = "undetermined"
    if np.isfinite(p) and p < 0.05:
        cat = "consistent" if direction == 1 else "opposite"
    return {"auc_support": a_s, "auc_query": a_q, "p_query": p, "direction": direction, "category": cat,
            "n_support": int(sup.sum()), "n_query": int(qry.sum())}


def ensemble_trial_scores(b: B1, key: str = "diff_base") -> np.ndarray:
    """Mean over seeds of the held-out outer-model score for every trial (each child is test once per seed)."""
    N = b.co.n_trials
    child_of_trial = b.co.rec.child.to_numpy()[b.co.t_record]
    acc = np.zeros(N)
    cnt = np.zeros(N)
    for s in b.seeds:
        for k in range(b.n_outer):
            u = b.units[(s, k)]
            m = np.isin(child_of_trial, u["test_children"])
            v = u[key][m]
            ok = np.isfinite(v)
            idx = np.flatnonzero(m)[ok]
            acc[idx] += v[ok]
            cnt[idx] += 1
    out = np.full(N, np.nan)
    out[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0]
    return out


def ensemble_occ_scores(b: B1, w: int) -> np.ndarray:
    N = b.co.n_trials
    child_of_trial = b.co.rec.child.to_numpy()[b.co.t_record]
    acc, cnt = np.zeros(N), np.zeros(N)
    for s in b.seeds:
        for k in range(b.n_outer):
            u = b.units[(s, k)]
            m = np.isin(child_of_trial, u["test_children"])
            idx = np.flatnonzero(m)
            acc[idx] += u["diff_occ"][w, idx]
            cnt[idx] += 1
    out = np.full(N, np.nan)
    out[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0]
    return out
