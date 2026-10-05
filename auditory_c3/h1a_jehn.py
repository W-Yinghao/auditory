"""H1a positive control (04 §4.1; MEASUREMENT_AMENDMENT_001 §7): attention-decoding accuracy with Jehn's published
linear backward pipeline (Constantin-Jehn/aad-neuroimage @ cbf9bd8). The Ridge class is used verbatim (private copy,
private/auditory_c3/vendor_jehn/ridge.py; the repository carries no licence, so it is never published). Preprocessing
re-implements utils.preprocess_eeg_array / concatenate_eeg / concatenate_stimulus exactly (no spyeeg dependency).

Folds: each competing-speaker trial (HDF5 keys 9-20) is the test trial once; validation = next competing trial
(cyclic); training = the other 18 trials (single- and competing-speaker), as in the repository's full-data split.
The test trial is cut at the distractor onset (Jehn utils.find_start_distractor on the 1 kHz distractor envelope) and
split into non-overlapping 60 s windows; a window is correct when r(reconstruction, attended) > r(reconstruction,
ignored). Per-subject accuracy = correct windows / windows; the group statistic is the mean over subjects.

Usage: python -m auditory_c3.h1a_jehn <ha|ci|th> <subject>   (group summary: auditory_c3.aggregate p2)
"""
from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout

import numpy as np
from scipy.ndimage import binary_erosion
from scipy.stats import pearsonr, zscore

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "private", "auditory_c3", "vendor_jehn"))
from ridge import Ridge  # noqa: E402

ROOT = "/projects/EEG-foundation-model/auditory_public"
H5 = {"ha": "fau_tud/zenodo_17927767_ha/hi_dataset_1kHz.hdf5", "ci": "fau_tud/zenodo_17952844_ci/ci_dataset_1kHz.hdf5",
      "th": "fau_tud/zenodo_17952231_th/nh_dataset_1kHz.hdf5"}
FS_IN, FS = 1000, 64
DOWN = FS_IN / FS
LAG0, LAG1 = int(-500 / 1000 * FS), int(500 / 1000 * FS)
ALPHA = np.logspace(-7, 7, 15)
WIN = 60 * FS
PAPER = {"th": 87.8, "ha": 88.5, "ci": 63.1}
OUT = os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud", "h1a")


def prep_eeg(x):
    import mne
    x = mne.filter.filter_data(x, FS_IN, l_freq=1, h_freq=None, verbose=False)
    x = mne.filter.resample(x, down=DOWN, axis=1, verbose=False)
    x = mne.filter.filter_data(x, sfreq=FS, l_freq=None, h_freq=8, verbose=False)
    return zscore(x, axis=1)[:31]


def prep_env(e):
    import mne
    return zscore(mne.filter.resample(e, down=DOWN, verbose=False))


def find_start_distractor(distr_arr, thres_window=10):
    m = distr_arr > distr_arr.mean()
    k = np.ones(thres_window, dtype=bool)
    return binary_erosion(m, k, origin=-(thres_window // 2)).argmax()


def subject(f, s, zero_removed=False, from_trial_start=False):
    """zero_removed / from_trial_start: DECISION_001 §5 audit variants (reported beside the primary, never replacing it)."""
    keys = sorted([k for k in f[f"eeg/{s}"].keys() if k.isdigit()], key=int)
    removed = [int(i) for i in np.atleast_1d(f[f"eeg/{s}/taken_out_indices"][()])] if (zero_removed and "taken_out_indices" in f[f"eeg/{s}"]) else []
    X, Ya, Yd, onset = {}, {}, {}, {}
    for k in keys:
        code = f[f"eeg/{s}/{k}"].attrs["stimulus"]
        code = code.decode() if isinstance(code, bytes) else str(code)
        X[k] = prep_eeg(f[f"eeg/{s}/{k}"][()].astype(np.float64))
        if removed:
            X[k][removed] = 0.0  # disconnected electrodes treated as absent channels
        ea = f[f"stimulus_files/{code}/attended_env"][()].astype(np.float64)
        ed = f[f"stimulus_files/{code}/distractor_env"][()].astype(np.float64)
        Ya[k] = prep_env(ea)
        if int(k) >= 9:
            Yd[k] = prep_env(ed)
            onset[k] = int(round(find_start_distractor(ed) / DOWN))
        n = min(X[k].shape[1], len(Ya[k]))
        X[k], Ya[k] = X[k][:, :n], Ya[k][:n]
        if k in Yd:
            Yd[k] = Yd[k][:n]
    cs = [k for k in keys if int(k) >= 9]
    windows = []
    for i, test in enumerate(cs):
        val = cs[(i + 1) % len(cs)]
        train = [k for k in keys if k not in (test, val)]
        mdl = Ridge(start_lag=LAG0, end_lag=LAG1, alpha=ALPHA, verbose=False)
        with redirect_stdout(io.StringIO()):
            mdl.fit(np.hstack([X[k] for k in train]).T, np.hstack([Ya[k] for k in train])[:, None])
            mdl.model_selection(X[val].T, Ya[val][:, None])
            pred = mdl.predict(X[test].T, best_alpha=True)[0]
        a = 0 if from_trial_start else onset[test]
        for w0 in range(a, len(pred) - WIN + 1, WIN):
            sl = slice(w0, w0 + WIN)
            ra, rd = pearsonr(pred[sl], Ya[test][sl])[0], pearsonr(pred[sl], Yd[test][sl])[0]
            windows.append({"test": test, "start": w0, "r_att": float(ra), "r_ign": float(rd), "correct": bool(ra > rd),
                            "alpha": float(ALPHA[mdl.best_alpha_idx])})
    acc = float(np.mean([w["correct"] for w in windows])) if windows else float("nan")
    return {"accuracy": acc, "n_windows": len(windows), "windows": windows}


def main(grp, subj, variant="primary"):
    """One subject per call (pool unit): private/auditory_c3/public/fau_tud/h1a[_<variant>]/<grp>/<subj>.json."""
    import h5py
    d = os.path.join(OUT if variant == "primary" else OUT + "_" + variant, grp); os.makedirs(d, exist_ok=True)
    with h5py.File(os.path.join(ROOT, H5[grp]), "r") as f:
        r = subject(f, subj, zero_removed=(variant == "zero_removed"), from_trial_start=(variant == "trial_start"))
    r["variant"] = variant
    json.dump(r, open(os.path.join(d, f"{subj}.json"), "w"), indent=1)
    print(grp, subj, variant, "acc %.3f windows %d" % (r["accuracy"], r["n_windows"]), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "primary")
