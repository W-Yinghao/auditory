"""Readout: history design, partitions, LOGO leakage guard, metric algebra and a synthetic recovery."""
from __future__ import annotations

import math

import numpy as np
import pytest

from auditory_st import readout as rd
from auditory_st.runtime import load_config

CONFIG = load_config()


def test_history_design_is_explicit_about_unknowns():
    H, names, first = rd.history_design(np.array([-1, 0, 1]), np.array([-1.0, 0.9, 0.9]), np.array([-1, 1, 5]),
                                        np.array(["no_previous_sound", "complete", "complete"]))
    assert H.shape == (3, len(names))
    row = dict(zip(names, H[0]))
    assert row["prev_unknown"] == 1 and row["log1p_gap"] == 0 and row["prev_run_unknown"] == 1 and row["first_in_chain"] == 1
    row = dict(zip(names, H[1]))
    assert row["prev_code_0"] == 1 and math.isclose(row["log1p_gap"], math.log1p(0.9)) and row["prev_run_1"] == 1
    row = dict(zip(names, H[2]))
    assert row["prev_code_1"] == 1 and row["prev_run_5plus"] == 1
    assert first.tolist() == [True, False, False]


def test_partitions_respect_embargo():
    onset = np.arange(0.0, 600.0, 1.0)
    half, parity = rd.partitions(onset, pre_s=0.2, post_s=0.8, block_s=60.0, embargo_s=10.0)
    mid = (onset.min() + onset.max()) / 2
    assert (half[onset < mid - 15] == 0).all() and (half[onset > mid + 15] == 1).all()
    assert (half[(onset > mid - 5) & (onset < mid + 5)] == -1).all()
    assert parity[30] == 0 and parity[90] == 1 and parity[5] == -1 and parity[55] == -1


def test_metric_algebra():
    y = np.array([0, 0, 1, 1])
    assert math.isclose(rd.balanced_accuracy(np.array([0, 0, 1, 0]), y), 0.75)
    assert math.isclose(rd.safe_auc(np.array([0.1, 0.2, 0.8, 0.9]), y), 1.0)
    assert math.isnan(rd.safe_auc(np.array([0.1, 0.2]), np.array([0, 0])))
    loss = rd.bits_loss(np.array([0.5, 0.5]), np.array([0, 1]))
    assert np.allclose(loss, 1.0)


def _synthetic(seed=0, n_children=14, trials=160, W=12, C=6, signal_window=7):
    rng = np.random.default_rng(seed)
    Xs, ys, gs, rs, ts, ons, pcs, pgs, prs, sts = [], [], [], [], [], [], [], [], [], []
    for c in range(n_children):
        y = (rng.random(trials) < 0.2).astype(int)
        X = rng.standard_normal((trials, W, C)).astype(np.float32)
        pattern = rng.standard_normal(C) * 0 + np.array([1.5, -1.0, 0.5, 0, 0, 0][:C])
        X[y == 1, signal_window, :] += pattern.astype(np.float32)
        Xs.append(X); ys.append(y); gs.append(np.full(trials, f"G{c:02d}")); rs.append(np.full(trials, f"R{c:02d}"))
        ts.append(np.array([f"R{c:02d}:{k}" for k in range(trials)])); ons.append(np.arange(trials) * 0.9 + 5.0)
        prev = np.r_[-1, y[:-1]]
        pcs.append(prev); pgs.append(np.where(prev >= 0, 0.9, -1.0)); prs.append(np.where(prev >= 0, 1, -1))
        sts.append(np.where(prev >= 0, "complete", "no_previous_sound"))
    H, names, first = rd.history_design(np.concatenate(pcs), np.concatenate(pgs), np.concatenate(prs), np.concatenate(sts))
    halves, parities = [], []
    for o in ons:
        h, p = rd.partitions(o, pre_s=0.2, post_s=0.8, block_s=60.0, embargo_s=10.0)
        halves.append(h); parities.append(p)
    return rd.LaneData(X=np.concatenate(Xs), y=np.concatenate(ys), group=np.concatenate(gs), record=np.concatenate(rs),
                       trial=np.concatenate(ts), onset_s=np.concatenate(ons), H=H, h_names=names, first_in_chain=first,
                       half=np.concatenate(halves), parity=np.concatenate(parities),
                       centres_s=np.linspace(-0.16, 0.28, W), records_meta=[])


def test_logo_folds_have_no_identity_leakage_and_fold_is_deterministic():
    data = _synthetic()
    folds = rd.lane_folds(data, CONFIG)
    assert len(folds) == 14
    for g, train, test in folds:
        assert set(data.group[test]) == {g} and g not in set(data.group[train])
    g, train, test = folds[0]
    a = rd.run_fold(data, train, test, CONFIG, temporal_generalisation=True)
    b = rd.run_fold(data, train, test, CONFIG, temporal_generalisation=True)
    assert np.array_equal(a["dec"], b["dec"]) and np.array_equal(a["p_stack"], b["p_stack"])
    assert a["tg"].shape == (len(test), 12, 12)


def test_synthetic_signal_is_recovered_only_in_its_window():
    data = _synthetic()
    folds = rd.lane_folds(data, CONFIG)
    rows = []
    for g, train, test in folds[:6]:
        res = rd.run_fold(data, train, test, CONFIG, temporal_generalisation=True)
        rows.append(rd.child_metrics(data.y[test], res["dec"], res["p_stack"], res["p_hist"], res["prior_p1"],
                                     res["prior_logit"], p_cal=res["p_cal"]))
        assert res["p_cal"].shape == res["dec"].shape and np.isfinite(res["p_cal"]).all()
        tg = rd.tg_auc(data.y[test], res["tg"])
        # signal window generalises to itself; the signal model on a noise window is at chance.
        # (a noise-trained model applied to the signal window may deviate from 0.5 by chance direction)
        assert tg[7, 7] > 0.8 and 0.35 < tg[7, 0] < 0.65
    auc = np.stack([r["auc"] for r in rows]).mean(0)
    assert auc[7] > 0.85
    assert np.all(np.delete(auc, 7) < 0.65)
    g_hist = np.stack([r["g_hist"] for r in rows]).mean(0)
    g_prior = np.stack([r["g_prior"] for r in rows]).mean(0)
    assert g_hist[7] > 0.1 and g_prior[7] > 0.1
    assert abs(np.delete(g_prior, 7)).max() < 0.08
    # calibrated loss is never much worse than the prior on noise windows; raw may be
    g_raw = np.stack([r["g_prior_raw"] for r in rows]).mean(0)
    assert np.delete(g_prior, 7).min() > -0.03 and g_raw[7] > 0.05
    # history carries real information in this synthetic oddball (no two deviants in a row is not enforced),
    # so its loss must be at most the prior loss up to noise
    assert np.mean([r["ll_hist"] for r in rows]) <= np.mean([r["ll_prior"] for r in rows]) + 0.05


def test_bootstrap_and_spearman_shapes():
    curves = np.random.default_rng(1).standard_normal((20, 5))
    mean, lo, hi = rd.bootstrap_mean(curves, n=200, seed=3)
    assert mean.shape == (5,) and np.all(lo <= mean) and np.all(mean <= hi)
    assert math.isclose(rd.spearman(np.arange(10.0), np.arange(10.0) ** 2), 1.0)
