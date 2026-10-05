"""Stage B preprocessing for FAU/TUD (docs/auditory_c3/MEASUREMENT_AMENDMENT_001.md §5-§6), identical for all groups.

Per subject, from stage A (c3_preproc_v1/fau_tud/<grp>/<subj>.h5):
  * primary alignment = aux-realigned copy where it exists, else as published; trials with a realigned copy also keep
    the published alignment ("_pub") for the sensitivity analysis;
  * drop IO2 (EOG), add Cz (online reference) as a zero channel, average reference over the 31 EEG channels,
    spherical-spline interpolation (standard_1005 positions) of removed CI electrodes, re-average;
  * FastICA (rank components, random_state 97) on the 1-20 Hz data (guards excluded); a component is removed when its
    1-8 Hz cross-correlation with the presented-sound envelope (attended + distractor, 1-8 Hz) peaks within +-3 samples
    (+-23 ms) AND 20*log10(|peak| / std(r at 0.5-1 s lags)) > 15 dB; the same rule for every group;
  * both versions are stored: eeg_<band>_ica and eeg_<band>_noica, bands 1_8 and 1_20.
No stimulus-EEG information quantity is computed; the envelope correlation is used only for the artefact rule.

Usage: python -m auditory_c3.stageb <ha|ci|th> [n_workers]
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.signal import correlate

from .preproc import FAU_CH, OUT as PRE

OUTB = os.path.join(PRE, "fau_tud_stageB")
OUTC = os.path.join(PRE, "fau_tud_stageC")  # POST_G1_CHANGELOG 2026-10-05 ~15:30: stage B + EOG (IO2) component removal
EOG_Z, EOG_MAX = 3.0, 3
EEG30 = [c for c in FAU_CH if c != "IO2"]
ALL = EEG30 + ["Cz"]
ROWS30 = [FAU_CH.index(c) for c in EEG30]
SNR_DB, PEAK_MAX_LAG, MAXLAG = 15.0, 3, 128


def _spatial(X, bads):
    """Average reference (Cz added as zeros), interpolate bads, re-average. X: (30, n) recorded-reference EEG."""
    import mne
    Y = np.vstack([np.nan_to_num(X), np.zeros((1, X.shape[1]))])
    info = mne.create_info(ALL, 128.0, "eeg")
    info.set_montage(mne.channels.make_standard_montage("standard_1005"))
    raw = mne.io.RawArray(Y, info, verbose=False)
    raw.info["bads"] = list(bads)
    raw.set_eeg_reference("average", projection=False, verbose=False)
    if bads:
        raw.interpolate_bads(reset_bads=True, mode="accurate", verbose=False)
        raw.set_eeg_reference("average", projection=False, verbose=False)
    return raw.get_data()


def _eog_components(sources, eog, segs):
    """|r| of each IC with the EOG channel over valid samples; iterative z-scoring (threshold EOG_Z), at most EOG_MAX."""
    S = np.concatenate([s[:, a:b] for s, (a, b) in zip(sources, segs)], axis=1)
    e = np.concatenate([x[a:b] for x, (a, b) in zip(eog, segs)])
    r = np.array([abs(np.corrcoef(S[i], e)[0, 1]) for i in range(S.shape[0])])
    pool, bad = list(range(len(r))), []
    for _ in range(EOG_MAX):
        z = (r[pool] - r[pool].mean()) / (r[pool].std() + 1e-12)
        k = int(np.argmax(z))
        if z[k] <= EOG_Z:
            break
        bad.append(pool.pop(k))
    return bad, r


def subject(grp, subj, eog_rule=False):
    import h5py
    import mne
    src = os.path.join(PRE, "fau_tud", grp, f"{subj}.h5")
    out = os.path.join(OUTC if eog_rule else OUTB, grp, f"{subj}.h5")
    if os.path.exists(out):
        return subj, "present"
    stim = h5py.File(os.path.join(PRE, "fau_tud", "stimulus_env_128.h5"), "r")
    with h5py.File(src, "r") as f:
        removed = [int(i) for i in np.atleast_1d(f.attrs["removed_rows"])]
        bads = [FAU_CH[i] for i in removed if FAU_CH[i] != "IO2"]
        guard = int(f.attrs["guard_samples"])
        trials = sorted(f.keys())
        data = {}  # (trial, band, align) -> (31, n)
        segs, envs, lens, eogs = [], [], [], []
        for t in trials:
            g = f[t]
            code = g.attrs["stimulus"]
            for band in ("1_8", "1_20"):
                prim = f"eeg_{band}_realigned" if f"eeg_{band}_realigned" in g else f"eeg_{band}"
                data[(t, band, "prim")] = g[prim][()][ROWS30].astype(np.float64)
                if band == "1_20":
                    eogs.append(g[prim][()][FAU_CH.index("IO2")].astype(np.float64))
                if prim.endswith("_realigned"):
                    data[(t, band, "pub")] = g[f"eeg_{band}"][()][ROWS30].astype(np.float64)
            n = data[(t, "1_8", "prim")].shape[1]
            # presented sound = attended + distractor; a single-speaker trial's distractor envelope is NaN in the
            # published file (no distractor), i.e. silence
            e = np.nan_to_num(stim[f"{code}/attended_env/bp_1_8"][()]) + np.nan_to_num(stim[f"{code}/distractor_env/bp_1_8"][()])
            m = min(n, len(e))
            extra = int(g["eeg_1_8_realigned"].attrs.get("extra_guard_samples", 0)) if "eeg_1_8_realigned" in g else 0
            lens.append(n); envs.append(np.pad(e[:m], (0, n - m))); segs.append((guard + extra, m - guard - extra))
    stim.close()
    # spatial operations on the concatenation of all trials (instantaneous, so concatenation is harmless)
    keys = list(data.keys())
    cat = np.concatenate([data[k] for k in keys], axis=1)
    sp = _spatial(cat, bads)
    pos = 0
    for k in keys:
        n = data[k].shape[1]; data[k] = sp[:, pos:pos + n]; pos += n
    # ICA on 1-20 Hz primary, valid samples only
    fit = np.concatenate([data[(t, "1_20", "prim")][:, a:b] for t, (a, b) in zip(trials, segs)], axis=1)
    rank = len(ALL) - 1 - len(bads)
    info = mne.create_info(ALL, 128.0, "eeg"); info.set_montage(mne.channels.make_standard_montage("standard_1005"))
    with info._unlock():
        info["highpass"], info["lowpass"] = 1.0, 20.0  # stage A band-pass (1-20 Hz copy is the ICA fitting data)
    ica = mne.preprocessing.ICA(n_components=rank, method="fastica", random_state=97, max_iter="auto", verbose=False)
    ica.fit(mne.io.RawArray(fit, info, verbose=False), verbose=False)
    # artefact rule on 1-8 Hz sources
    src18 = [ica.get_sources(mne.io.RawArray(data[(t, "1_8", "prim")], info, verbose=False)).get_data() for t in trials]
    comp = []
    for ci in range(rank):
        ic = [s[ci] for s in src18]
        # r(k) = corr(ic(t), env(t-k)), k = -MAXLAG..MAXLAG, pooled over the valid segments of all trials
        num = np.zeros(2 * MAXLAG + 1); n_s = 0; sx = sxx = se = see = 0.0
        for x_full, e, (a, b) in zip(ic, envs, segs):
            x = x_full[a:b]; ee = e[a - MAXLAG:b + MAXLAG]
            num += correlate(ee, x, mode="valid", method="fft")[::-1]
            n_s += len(x); sx += x.sum(); sxx += (x**2).sum(); se += e[a:b].sum(); see += (e[a:b]**2).sum()
        r = num / n_s / (np.sqrt(sxx / n_s - (sx / n_s) ** 2) * np.sqrt(see / n_s - (se / n_s) ** 2))
        lags = np.arange(-MAXLAG, MAXLAG + 1)
        kpk = int(np.argmax(np.abs(r)))
        noise = np.std(r[(np.abs(lags) >= 64)])
        snr = 20 * np.log10(np.abs(r[kpk]) / noise)
        comp.append({"ic": ci, "peak_lag_samples": int(lags[kpk]), "peak_r": float(r[kpk]), "snr_db": float(snr),
                     "removed": bool(abs(lags[kpk]) <= PEAK_MAX_LAG and snr > SNR_DB)})
    excl = [c["ic"] for c in comp if c["removed"]]
    eog_info = None
    if eog_rule:
        if all(np.isfinite(x).all() for x in eogs):
            src20 = [ica.get_sources(mne.io.RawArray(data[(t, "1_20", "prim")], info, verbose=False)).get_data() for t in trials]
            eog_bad, eog_r = _eog_components(src20, eogs, segs)
            eog_info = {"eog_removed": eog_bad, "eog_abs_r": [float(x) for x in eog_r]}
            excl = sorted(set(excl) | set(eog_bad))
        else:
            eog_info = {"eog_removed": [], "note": "IO2 missing; no EOG removal"}
    ica.exclude = excl
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    with h5py.File(tmp, "w") as o, h5py.File(src, "r") as f:
        o.attrs.update(subject=subj, group=grp, fs=128, channels=ALL, bads_interpolated=bads, guard_samples=guard,
                       reference="average over 30 EEG + reconstructed Cz", ica_rank=rank, ica_removed=excl,
                       ica_rule=f"peak |lag|<={PEAK_MAX_LAG} samples and SNR>{SNR_DB} dB vs presented envelope (1-8 Hz)",
                       ica_components=json.dumps(comp), stage="c3_preproc_v1 stage C (B + EOG)" if eog_rule else "c3_preproc_v1 stage B")
        if eog_rule:
            o.attrs["eog_rule"] = f"iterative z of |r(IC, IO2)| > {EOG_Z}, at most {EOG_MAX}"
            o.attrs["eog_info"] = json.dumps(eog_info)
        for t, (a, b) in zip(trials, segs):
            g = o.create_group(t)
            g.attrs.update({k: f[t].attrs[k] for k in f[t].attrs})
            g.attrs["valid_start"], g.attrs["valid_stop"] = a, b
            for (tt, band, al), X in data.items():
                if tt != t:
                    continue
                suf = "" if al == "prim" else "_pub"
                Xc = mne.io.RawArray(X, info, verbose=False)
                g.create_dataset(f"eeg_{band}_noica{suf}", data=X.astype(np.float32), compression="lzf")
                g.create_dataset(f"eeg_{band}_ica{suf}", data=ica.apply(Xc.copy(), verbose=False).get_data().astype(np.float32), compression="lzf")
    os.replace(tmp, out)
    return subj, {"bads": bads, "rank": rank, "n_removed": len(excl), "eog": eog_info,
                  "max_snr_db": max(c["snr_db"] for c in comp), "removed_detail": [c for c in comp if c["removed"]]}


def _one(args):
    os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    try:
        return subject(*args)
    except Exception as ex:  # recorded per subject, never silently dropped
        return args[1], {"error": f"{type(ex).__name__}: {ex}"[:400]}


def main(argv=None):
    import glob
    a = argv or sys.argv[1:]
    if a[0] == "one":  # python -m auditory_c3.stageb one <grp> <subj> [--eog]
        s, r = subject(a[1], a[2], eog_rule="--eog" in a)
        print(a[1], s, json.dumps(r if isinstance(r, str) else {k: v for k, v in r.items() if k != "removed_detail"}), flush=True)
        return
    grp = a[0]; workers = int(a[1]) if len(a) > 1 else 4
    subs = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(PRE, "fau_tud", grp, "*.h5")))
    log = {}
    with ProcessPoolExecutor(workers) as ex:
        for s, r in ex.map(_one, [(grp, s) for s in subs]):
            log[s] = r
            print(grp, s, json.dumps(r if isinstance(r, str) else {k: v for k, v in r.items() if k != "removed_detail"}), flush=True)
    os.makedirs(os.path.join(PRE, "_logs"), exist_ok=True)
    json.dump(log, open(os.path.join(PRE, "_logs", f"stageB_{grp}.json"), "w"), indent=1)
    errs = [s for s, r in log.items() if isinstance(r, dict) and "error" in r]
    print("stageB", grp, "subjects", len(log), "errors", len(errs))


if __name__ == "__main__":
    main()
