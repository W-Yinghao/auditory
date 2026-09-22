"""Child-held-out, time-resolved sound-condition readout with references and repeatability.

Primary readout: shrinkage LDA on the per-window multichannel means, one model per
window, trained on all trials of the training children, evaluated on every trial of
the held-out identity group (leave-one-identity-group-out). References: class prior
and a stimulus-history logistic model. The conditional gain follows section 5.3 of the
plan: G = mean log2 q1(s|x,h) - log2 q0(s|h) with q1 a cross-fitted stacker over the
LDA log-odds and the history features. Temporal generalisation reuses the fitted
per-window models. Children are the unit of every aggregate.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from .runtime import ProvenanceError, cfg

EPS = 1e-7
LN2 = math.log(2.0)


@dataclass
class LaneData:
    X: np.ndarray            # [N, W, C] float32
    y: np.ndarray            # [N] int {0,1}
    group: np.ndarray        # [N] str identity group
    record: np.ndarray       # [N] str
    trial: np.ndarray        # [N] str
    onset_s: np.ndarray      # [N] float
    H: np.ndarray            # [N, F] history design
    h_names: list
    first_in_chain: np.ndarray
    half: np.ndarray         # [N] {0,1,-1} early/late with embargo
    parity: np.ndarray       # [N] {0,1,-1} odd/even 60 s block with embargo
    centres_s: np.ndarray    # [W]
    records_meta: list       # per record dicts


def history_design(prev_code: np.ndarray, prev_gap: np.ndarray, prev_run: np.ndarray,
                   status: np.ndarray) -> tuple[np.ndarray, list, np.ndarray]:
    """One-hot history features. Unknown values are explicit categories, never zeros in disguise."""
    n = len(prev_code)
    first = np.asarray([s == "no_previous_sound" for s in status], dtype=bool)
    known = np.asarray(prev_code, dtype=np.int64) >= 0
    gap = np.where(known, np.log1p(np.where(known, np.asarray(prev_gap, dtype=float), 0.0)), 0.0)
    run = np.asarray(prev_run, dtype=np.int64)
    cols = [np.where(known & (prev_code == 0), 1.0, 0.0), np.where(known & (prev_code == 1), 1.0, 0.0),
            np.where(~known, 1.0, 0.0), gap]
    names = ["prev_code_0", "prev_code_1", "prev_unknown", "log1p_gap"]
    for k in (1, 2, 3, 4):
        cols.append(np.where(run == k, 1.0, 0.0))
        names.append(f"prev_run_{k}")
    cols.append(np.where(run >= 5, 1.0, 0.0))
    names.append("prev_run_5plus")
    cols.append(np.where(run < 0, 1.0, 0.0))
    names.append("prev_run_unknown")
    cols.append(first.astype(float))
    names.append("first_in_chain")
    return np.column_stack(cols).astype(np.float64), names, first


def partitions(onset_s: np.ndarray, *, pre_s: float, post_s: float, block_s: float,
               embargo_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Early/late halves and odd/even blocks for ONE record, with embargoes (-1 = excluded)."""
    mid = (onset_s.min() + onset_s.max()) / 2.0
    half = np.full(len(onset_s), -1, dtype=np.int64)
    half[onset_s + post_s <= mid - embargo_s] = 0
    half[onset_s - pre_s >= mid + embargo_s] = 1
    block = np.floor(onset_s / block_s).astype(np.int64)
    within = onset_s - block * block_s
    parity = np.where((within - pre_s >= embargo_s) & (block_s - (within + post_s) >= embargo_s),
                      block % 2, -1).astype(np.int64)
    return half, parity


def load_lane(feature_paths: list[Path], config: dict) -> LaneData:
    Xs, ys, groups, records, trials, onsets, halves, parities = [], [], [], [], [], [], [], []
    pcs, pgs, prs, sts, metas = [], [], [], [], []
    centres = None
    pre_s = float(cfg(config, "epoch.pre_seconds"))
    block_s = float(cfg(config, "readout.time_blocks.block_seconds"))
    embargo_s = float(cfg(config, "readout.time_blocks.embargo_seconds"))
    for path in feature_paths:
        with np.load(path, allow_pickle=False) as store:
            acc = store["accepted"]
            if not acc.any():
                continue
            X = store["features"][acc]
            c = store["window_centres_s"]
            if centres is None:
                centres = c
            elif c.shape != centres.shape or not np.allclose(c, centres):
                raise ProvenanceError(f"WINDOW_GRID_MISMATCH:{path.name}")
            onset = store["onset_seconds"][acc]
            half, parity = partitions(onset, pre_s=pre_s, post_s=float(store["post_seconds"]),
                                      block_s=block_s, embargo_s=embargo_s)
            n = int(acc.sum())
            Xs.append(X); ys.append(store["y"][acc]); onsets.append(onset)
            groups.append(np.full(n, str(store["identity_group"]))); records.append(np.full(n, str(store["record_id"])))
            trials.append(store["trial_id"][acc]); halves.append(half); parities.append(parity)
            pcs.append(store["previous_code"][acc]); pgs.append(store["previous_gap_s"][acc])
            prs.append(store["previous_run_length"][acc]); sts.append(store["history_status"][acc])
            metas.append({"record_id": str(store["record_id"]), "identity_group": str(store["identity_group"]),
                          "n_accepted": n, "record_scale": float(store["record_scale"]),
                          "class_counts": {int(k): int(v) for k, v in zip(*np.unique(store["y"][acc], return_counts=True))}})
    if not Xs:
        raise ProvenanceError("LANE_EMPTY")
    H, names, first = history_design(np.concatenate(pcs), np.concatenate(pgs), np.concatenate(prs), np.concatenate(sts))
    return LaneData(X=np.concatenate(Xs), y=np.concatenate(ys).astype(np.int64), group=np.concatenate(groups),
                    record=np.concatenate(records), trial=np.concatenate(trials), onset_s=np.concatenate(onsets),
                    H=H, h_names=names, first_in_chain=first, half=np.concatenate(halves),
                    parity=np.concatenate(parities), centres_s=centres, records_meta=metas)


# ----------------------------------------------------------------------------- models

def fit_lda(X: np.ndarray, y: np.ndarray, config: dict) -> LinearDiscriminantAnalysis:
    p1 = float(np.mean(y == 1))
    model = LinearDiscriminantAnalysis(solver=str(cfg(config, "readout.lda_solver")),
                                       shrinkage=str(cfg(config, "readout.lda_shrinkage")),
                                       priors=np.array([1.0 - p1, p1]))
    model.fit(X, y)
    return model


def fit_history(H: np.ndarray, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(C=1.0, max_iter=2000)
    model.fit(H, y)
    return model


def fit_calibrator(dec: np.ndarray, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(C=1.0, max_iter=2000)
    model.fit(np.asarray(dec, dtype=np.float64).reshape(-1, 1), y)
    return model


def fit_stacker(dec: np.ndarray, H: np.ndarray, y: np.ndarray) -> LogisticRegression:
    model = LogisticRegression(C=1.0, max_iter=2000)
    model.fit(np.column_stack([dec, H]), y)
    return model


def bits_loss(p1: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(np.where(y == 1, p1, 1.0 - p1), EPS, 1.0)
    return -np.log(p) / LN2


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60, 60)))


def balanced_accuracy(pred: np.ndarray, y: np.ndarray) -> float:
    out = []
    for k in (0, 1):
        m = y == k
        if m.any():
            out.append(float(np.mean(pred[m] == k)))
    return float(np.mean(out)) if len(out) == 2 else float("nan")


def safe_auc(score: np.ndarray, y: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, score))


# ----------------------------------------------------------------------------- one fold

def run_fold(data: LaneData, train: np.ndarray, test: np.ndarray, config: dict, *,
             temporal_generalisation: bool) -> dict:
    """Fit per-window LDAs, history model and cross-fitted stackers on `train`; predict `test`."""
    Xtr, ytr, Htr, gtr = data.X[train], data.y[train], data.H[train], data.group[train]
    Xte, Hte = data.X[test], data.H[test]
    W = Xtr.shape[1]
    p1 = float(np.mean(ytr == 1))
    prior_logit = math.log(p1 / (1.0 - p1))
    hist = fit_history(Htr, ytr)
    p_hist = hist.predict_proba(Hte)[:, 1]
    inner = int(cfg(config, "readout.inner_folds_for_stacking"))
    n_inner_groups = len(np.unique(gtr))
    splitter = GroupKFold(n_splits=min(inner, n_inner_groups))
    inner_splits = list(splitter.split(Xtr[:, 0, :], ytr, gtr))
    dec = np.empty((len(test), W), dtype=np.float32)
    p_cal = np.empty((len(test), W), dtype=np.float32)
    p_stack = np.empty((len(test), W), dtype=np.float32)
    tg = np.empty((len(test), W, W), dtype=np.float32) if temporal_generalisation else None
    for w in range(W):
        model = fit_lda(Xtr[:, w, :], ytr, config)
        dec[:, w] = model.decision_function(Xte[:, w, :])
        oof = np.empty(len(train), dtype=np.float64)
        for itr, ival in inner_splits:
            m = fit_lda(Xtr[itr, w, :], ytr[itr], config)
            oof[ival] = m.decision_function(Xtr[ival, w, :])
        # 1-D calibration (slope + bias) of the LDA log-odds, fitted on inner out-of-fold values only
        calibrator = fit_calibrator(oof, ytr)
        p_cal[:, w] = calibrator.predict_proba(dec[:, w].astype(np.float64).reshape(-1, 1))[:, 1]
        stacker = fit_stacker(oof, Htr, ytr)
        p_stack[:, w] = stacker.predict_proba(np.column_stack([dec[:, w].astype(np.float64), Hte]))[:, 1]
        if temporal_generalisation:
            for w2 in range(W):
                tg[:, w, w2] = model.decision_function(Xte[:, w2, :])
    return {"test": test, "dec": dec, "p_cal": p_cal, "p_stack": p_stack, "p_hist": p_hist.astype(np.float32),
            "prior_p1": p1, "prior_logit": prior_logit, "tg": tg,
            "n_train_groups": n_inner_groups, "n_train_trials": int(len(train))}


def child_metrics(y: np.ndarray, dec: np.ndarray, p_stack: np.ndarray, p_hist: np.ndarray,
                  prior_p1: float, prior_logit: float, p_cal: np.ndarray | None = None) -> dict:
    """Per-window metrics for one child's trials. dec/p_cal/p_stack are [n, W].

    ll_eeg_raw uses the LDA posterior as is; ll_eeg (and g_prior) use the inner-OOF calibrated
    posterior p_cal, which is the quantity comparable with earlier rounds' calibrated CE.
    """
    W = dec.shape[1]
    out = {k: np.full(W, np.nan) for k in ("bacc", "auc", "ll_eeg_raw", "ll_eeg", "ll_stack",
                                          "g_prior_raw", "g_prior", "g_hist")}
    ll_prior = float(np.mean(bits_loss(np.full(len(y), prior_p1), y)))
    ll_hist = float(np.mean(bits_loss(p_hist, y)))
    bacc_hist = balanced_accuracy((p_hist > prior_p1).astype(int), y)
    auc_hist = safe_auc(p_hist, y)
    for w in range(W):
        p_raw = sigmoid(dec[:, w].astype(np.float64))
        p_eeg = p_raw if p_cal is None else p_cal[:, w].astype(np.float64)
        out["bacc"][w] = balanced_accuracy((dec[:, w] > prior_logit).astype(int), y)
        out["auc"][w] = safe_auc(dec[:, w], y)
        out["ll_eeg_raw"][w] = float(np.mean(bits_loss(p_raw, y)))
        out["ll_eeg"][w] = float(np.mean(bits_loss(p_eeg, y)))
        out["ll_stack"][w] = float(np.mean(bits_loss(p_stack[:, w].astype(np.float64), y)))
        out["g_prior_raw"][w] = ll_prior - out["ll_eeg_raw"][w]
        out["g_prior"][w] = ll_prior - out["ll_eeg"][w]
        out["g_hist"][w] = ll_hist - out["ll_stack"][w]
    out.update(ll_prior=ll_prior, ll_hist=ll_hist, bacc_hist=bacc_hist, auc_hist=auc_hist,
               n_trials=int(len(y)), n_deviant=int(np.sum(y == 1)))
    return out


def tg_auc(y: np.ndarray, tg: np.ndarray) -> np.ndarray:
    """[n, Wtrain, Wtest] decision values -> [Wtrain, Wtest] AUC."""
    W = tg.shape[1]
    out = np.full((W, W), np.nan)
    if len(np.unique(y)) < 2:
        return out
    for a in range(W):
        for b in range(W):
            out[a, b] = roc_auc_score(y, tg[:, a, b])
    return out


# ----------------------------------------------------------------------------- lane driver

def lane_folds(data: LaneData, config: dict) -> list[tuple[str, np.ndarray, np.ndarray]]:
    groups = np.unique(data.group)
    if len(groups) - 1 < int(cfg(config, "readout.min_train_groups")):
        raise ProvenanceError(f"LANE_TOO_FEW_GROUPS:{len(groups)}")
    folds = []
    for g in groups:
        test = np.flatnonzero(data.group == g)
        train = np.flatnonzero(data.group != g)
        assert not np.intersect1d(data.group[train], data.group[test]).size, "identity leakage"
        folds.append((str(g), train, test))
    return folds


def within_child(data: LaneData, idx: np.ndarray, part: np.ndarray, config: dict) -> list[dict]:
    """Secondary: train on one block of a child, test on the other; both directions."""
    minimum = int(cfg(config, "readout.within_child_min_trials_per_class_per_block"))
    rows = []
    for a, b in ((0, 1), (1, 0)):
        tr = idx[part[idx] == a]
        te = idx[part[idx] == b]
        ok = all(np.sum(data.y[tr] == k) >= minimum and np.sum(data.y[te] == k) >= minimum for k in (0, 1))
        if not ok:
            rows.append({"train_block": a, "test_block": b, "supported": False})
            continue
        W = data.X.shape[1]
        auc = np.full(W, np.nan)
        bacc = np.full(W, np.nan)
        p1 = float(np.mean(data.y[tr] == 1))
        thr = math.log(p1 / (1 - p1))
        for w in range(W):
            m = fit_lda(data.X[tr, w, :], data.y[tr], config)
            d = m.decision_function(data.X[te, w, :])
            auc[w] = safe_auc(d, data.y[te])
            bacc[w] = balanced_accuracy((d > thr).astype(int), data.y[te])
        rows.append({"train_block": a, "test_block": b, "supported": True, "auc": auc, "bacc": bacc,
                     "n_train": int(len(tr)), "n_test": int(len(te))})
    return rows


def bootstrap_mean(curves: np.ndarray, *, n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """curves [children, W] -> mean, lo, hi (percentile 2.5/97.5) resampling children."""
    rng = np.random.default_rng(seed)
    k = curves.shape[0]
    mean = np.nanmean(curves, axis=0)
    draws = np.empty((n, curves.shape[1]))
    for i in range(n):
        pick = rng.integers(0, k, size=k)
        draws[i] = np.nanmean(curves[pick], axis=0)
    return mean, np.nanpercentile(draws, 2.5, axis=0), np.nanpercentile(draws, 97.5, axis=0)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 4:
        return float("nan")
    from scipy.stats import spearmanr
    return float(spearmanr(a[m], b[m]).correlation)
