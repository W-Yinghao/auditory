"""H1c positive control and Federici envelope TMIF (04 §4.1, §4.4; MEASUREMENT_AMENDMENT_001 §7).

Authors' preprocessed EEG (2-8 Hz, 100 Hz, ICA; 12 x 50 s segments x 32 channels) and published envelopes
(AudioEnvSp). T = first 3 principal components of Federici's own frontocentral cluster (FC1, FC2, Fz, Cz), fitted on
each participant's valid samples. Lags -200..600 ms (100 Hz); valid response samples [60, n-20) so every lagged
envelope sample lies inside the 50 s segment; 200 circular-shift surrogates within segments (>= 5 s).
Windows: diag [-200, 0), w1 [0, 150), w2 [150, 600]. Also the onset envelope (half-wave rectified first difference).

Usage: python -m auditory_c3.federici_mi
Output (per participant, private): private/auditory_c3/public/federici/tmif.json
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

from .engine import Subject

PRE = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/federici_ci_children"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "private", "auditory_c3", "public", "federici")
FS = 100
LAGS = np.arange(-20, 61)
ROI = ["FC1", "FC2", "Fz", "Cz"]
WINDOWS = {"diag": (-200, 0), "w1": (0, 150), "w2": (150, 601)}


def run():
    import h5py
    res = {}
    for grp in ("HC", "CI", "HC-v", "Artifact"):
        for p in sorted(glob.glob(os.path.join(PRE, grp, "*.h5"))):
            pid = os.path.basename(p)[:-3]
            with h5py.File(p, "r") as f:
                E = f["eeg"][()].astype(np.float64); env = f["env"][()].astype(np.float64)
                ch = [str(c) for c in f.attrs["channels"]]
            idx = [ch.index(c) for c in ROI if c in ch]
            V = np.concatenate([seg[idx][:, 60:seg.shape[1] - 20] for seg in E], axis=1)
            mu = V.mean(1, keepdims=True)
            w, U = np.linalg.eigh((V - mu) @ (V - mu).T)
            U = U[:, np.argsort(w)[::-1][:min(3, len(idx))]]
            trials = []
            for seg, e in zip(E, env):
                n = seg.shape[1]
                onset = np.maximum(np.diff(e, prepend=e[0]), 0)
                trials.append({"T": U.T @ (seg[idx] - mu), "valid": (60, n - 20), "stim": {"Env": e[None], "Onset": onset[None]}})
            S = Subject(trials, FS, LAGS, n_sur=200, seed=int(pid.split("_")[0]) if pid.split("_")[0].isdigit() else 7)
            r = {"group": grp, "roi_channels_used": [ROI[i] for i in range(len(ROI)) if ROI[i] in ch], "N": S.N}
            for name in ("Env", "Onset"):
                arr = S.mi(name)
                ms = LAGS * 1000.0 / FS
                r[f"{name}/per_lag_obs"] = arr[0].tolist(); r[f"{name}/per_lag_sur_mean"] = arr[1:].mean(0).tolist()
                for wn, (lo, hi) in WINDOWS.items():
                    m = (ms >= lo) & (ms < hi)
                    v = arr[:, m].mean(1)
                    r[f"{name}/{wn}"] = {"obs": float(v[0]), "sur_mean": float(v[1:].mean()), "corr": float(v[0] - v[1:].mean())}
            res[f"{grp}/{pid}"] = r
            print(grp, pid, "Env w1 %.4f w2 %.4f" % (r["Env/w1"]["corr"], r["Env/w2"]["corr"]), flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"lags_ms": (LAGS * 1000.0 / FS).tolist(), "subjects": res}, open(os.path.join(OUT, "tmif.json"), "w"))


if __name__ == "__main__":
    run()
