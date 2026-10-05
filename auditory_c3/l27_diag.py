"""Diagnostic (post-hoc, disclosed in POST_G1_CHANGELOG.md): what do the leading PCs of Whisper layer 27 track?

The frozen L27 PCA-5 explains 99.9 % of the layer's variance (FAU/TUD and DTU alike), against 16-29 % in early layers.
This script describes, on the FAU/TUD stimulus side only (no EEG):
  - per-dimension variance share (are a few high-magnitude coordinates carrying the variance?),
  - each stored L27 PC's R^2 on: position inside the 30 s encoder window, log-mel energy, the Ac PCA-5 (shallow),
    and all three jointly (frame-level OLS on unique waveforms),
  - the PCA explained-variance profile after z-scoring every coordinate, and after dropping the top-variance coordinates,
  - the size of PC jumps at encoder-window seams relative to ordinary frame-to-frame steps.

Usage: python -m auditory_c3.l27_diag  ->  results/auditory_c3/L27_diagnostic.json
"""
from __future__ import annotations

import json
import os

import numpy as np

from .features import HOP_S, WIN_S, _windows

SRC = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "auditory_c3", "L27_diagnostic.json")
SR = 16000
N_POS_BINS = 60  # 0.5 s bins over the 30 s window


def _frame_window_position(n_samples, n_frames):
    """Seconds from the start of the encoder window that supplied each kept 50 Hz frame, and a seam flag."""
    pos = np.full(n_frames, np.nan)
    seam = np.zeros(n_frames, bool)
    for s, e, lo, hi in _windows(n_samples):
        A, B = int(round(lo / SR * 50)), min(int(round(hi / SR * 50)), n_frames)
        pos[A:B] = (np.arange(A, B) / 50.0) - s / SR
        if A > 0:
            seam[A] = True
    return pos, seam


def _r2(y, X):
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    res = y - X1 @ beta
    return float(1 - res.var() / y.var())


def main():
    import h5py
    fh = h5py.File(os.path.join(SRC, "whisper_large_v3_hidden.h5"), "r")
    fm = h5py.File(os.path.join(SRC, "whisper_logmel128.h5"), "r")
    fp = h5py.File(os.path.join(SRC, "pca_k8_128hz_whisper.h5"), "r")
    fs = h5py.File(os.path.join(SRC, "pca_k8_128hz_whisper_shallow.h5"), "r")
    mu27, V27 = fp["_pca/layer_27/mean"][()].astype(np.float64), fp["_pca/layer_27/components"][()].astype(np.float64)[:5]
    muA, VA = fs["_pca/shallow_01_02/mean"][()].astype(np.float64), fs["_pca/shallow_01_02/components"][()].astype(np.float64)[:5]

    seen, X, Z, P, E, AC, SEAM, STEP_OK = set(), [], [], [], [], [], [], []
    for c in sorted(fh.keys()):
        for s in sorted(fh[c].keys()):
            g = fh[c][s]
            if g.attrs["silent"] or g.attrs["wav_sha256"] in seen:
                continue
            seen.add(g.attrs["wav_sha256"])
            x27 = g["layer_27"][()].astype(np.float64)
            n = len(x27)
            pos, seam = _frame_window_position(int(g.attrs["n_samples_16k"]), n)
            mel = fm[c][s]["logmel"][()].astype(np.float64)  # (128, 100 Hz)
            m = mel.mean(0)
            m50 = np.array([m[2 * i:2 * i + 2].mean() if 2 * i < len(m) else m[-1] for i in range(n)])
            sh = 0.5 * (g["layer_01"][()].astype(np.float64) + g["layer_02"][()].astype(np.float64))
            X.append(x27); Z.append((x27 - mu27) @ V27.T); P.append(pos); E.append(m50); AC.append((sh - muA) @ VA.T)
            SEAM.append(seam)
    X, Z, P, E, AC, SEAM = (np.concatenate(a) for a in (X, Z, P, E, AC, SEAM))
    ok = np.isfinite(P)
    X, Z, P, E, AC, SEAM = X[ok], Z[ok], P[ok], E[ok], AC[ok], SEAM[ok]
    out = {"n_unique_waveforms": len(seen), "n_frames": int(len(X)), "windows": f"{WIN_S}s/{HOP_S}s centre-kept"}

    var = X.var(0)
    order = np.argsort(var)[::-1]
    tot = var.sum()
    out["coord_variance_share"] = {f"top{k}": float(var[order[:k]].sum() / tot) for k in (1, 2, 3, 5, 10, 20)}
    out["top_coords"] = [{"dim": int(d), "var_share": float(var[d] / tot), "mean": float(X[:, d].mean()),
                          "sd": float(np.sqrt(var[d]))} for d in order[:8]]
    out["median_coord_sd"] = float(np.median(np.sqrt(var)))
    out["pc_loading_on_top3_coords"] = [float(np.sum(V27[i, order[:3]] ** 2)) for i in range(5)]

    pos_oh = np.eye(N_POS_BINS)[np.clip((P / (WIN_S / N_POS_BINS)).astype(int), 0, N_POS_BINS - 1)][:, 1:]
    out["pc_r2"] = {}
    for i in range(5):
        y = Z[:, i]
        out["pc_r2"][f"PC{i + 1}"] = {
            "window_position_60bins": _r2(y, pos_oh),
            "logmel_energy": _r2(y, np.column_stack([E, E ** 2])),
            "Ac_pca5": _r2(y, AC),
            "all_three": _r2(y, np.column_stack([pos_oh, E, E ** 2, AC])),
            "var_share_of_layer": float(Z[:, i].var() / tot),
        }
        d = np.abs(np.diff(y))
        seam_steps = d[SEAM[1:]]
        out["pc_r2"][f"PC{i + 1}"]["seam_step_over_median_step"] = float(np.median(seam_steps) / np.median(d)) if len(seam_steps) else None

    def evr(M, k=(3, 5, 8)):
        w = np.linalg.eigvalsh(np.cov(M - M.mean(0), rowvar=False))[::-1]
        return {f"evr_k{j}": float(w[:j].sum() / w.sum()) for j in k}
    sd = X.std(0); sd[sd == 0] = 1
    out["evr_zscored_coords"] = evr(X / sd)
    for k in (1, 3, 10):
        keep = np.setdiff1d(np.arange(X.shape[1]), order[:k])
        out[f"evr_drop_top{k}_coords"] = evr(X[:, keep])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
