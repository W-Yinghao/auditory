"""Synthetic tests for the private per-lag pipeline and the TG block summaries of auditory_alignment_v3.sci_r1 (no data)."""
import sys

import numpy as np

sys.dont_write_bytecode = True

from auditory_alignment_v3.sci_r1 import aggregate as A  # noqa: E402
from auditory_alignment_v3.sci_r1 import private_task as P  # noqa: E402


def fake_kids(n=15, trials=300, K=6, p=5, seed=0):
    rng = np.random.default_rng(seed); kids, X = [], {}
    for c in range(n):
        y = (rng.random(trials) < 0.2).astype(np.int64)
        block = np.repeat(np.arange(10), trials // 10)
        es = block >= 8
        swap = np.array([rng.choice(np.flatnonzero((block != block[i]))) for i in range(trials)])
        kids.append({"id": f"child{c}", "group": "HA" if c % 4 else "NH", "fold": c % 5, "y": y, "bin": rng.integers(0, 6, trials),
                     "block": block, "es_mask": es, "swap": swap})
        x = rng.normal(size=(trials, K, p))
        x[:, 2, 0] += 1.5 * y  # planted signal at lag 2 only
        X[c] = x
    return kids, X


def test_s1_lags_signal_tg_diag_and_twin():
    kids, X = fake_kids()
    fd = P.Fold(kids, 0)
    res, probes = P.s1_lags(fd, X, 6, True)
    auc = res["s1"][:, :, 0]
    assert np.nanmean(auc[:, 2]) > 0.75 and abs(np.nanmean(auc[:, [0, 1, 3, 4, 5]]) - 0.5) < 0.08
    assert res["tg_diag_maxdiff"] == 0.0
    hg, tw = res["s1"][:, 2, P.S1_METRICS.index("hist_gain_bits")], res["s1"][:, 2, P.S1_METRICS.index("hist_gain_twin_bits")]
    assert np.nanmean(hg) > np.nanmean(tw)  # the swapped (other-block) EEG carries no trial-specific signal
    assert res["tg"].shape == (len(fd.te), 6, 6, 2)


def test_tg_blocks():
    ds = "private_bdf"
    M = np.zeros((29, 29)); M[6:9, 6:9] = 1.0; M[12:15, 12:15] = 2.0; M[6:9, 12:15] = 0.5
    b = A.blocks(M[None], ds)
    assert np.isclose(b["D_E"][0], 1.0) and np.isclose(b["D_L"][0], 2.0) and np.isclose(b["G_EL"][0], 0.5) and np.isclose(b["G_LE"][0], 0.0)
