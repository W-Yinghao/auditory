"""B2 (docs/auditory_c3/CI_EDG_REG_v1.md): simulated CI electrodogram envelopes, stimulus side only (no EEG).

The low-frequency part of a CI stimulation artefact follows the pulse-amplitude envelope that the sound processor
derives from the audio. For every FAU/TUD speech stream we simulate, per strategy family,
  filterbank (log-spaced Butterworth band-passes, causal) -> full-wave rectification -> 200 Hz low-pass (causal)
  -> 1 kHz frames -> n-of-m maxima selection (ACE only) -> loudness-growth map (40 dB input range, rho = 416)
  -> resample_poly 1000 -> 128 Hz,
then fit PCA-5 per family on the unique streams (centred covariance; band-pass is applied later at analysis, as for
the other cached features). Families (from Table 4 coding strategies):
  ace   : Cochlear ACE, 22 channels 188-7938 Hz, 8 maxima
  ab    : Advanced Bionics HiRes Optima-S / HiRes-S (Fidelity 120), 16 channels 250-7900 Hz, all channels (CIS-like)
  medel : MED-EL FS4 / FSP / HDCIS, 12 channels 100-8500 Hz, all channels (CIS-like envelope; fine-structure timing
          of the apical channels is not modelled, it is above the EEG band)

Usage: python -m auditory_c3.ci_edg build
Output: <FEAT>/ci_edg_<family>_pca5_128hz.h5 ({code}/{stream}/edg, 5 x n; _pca/{mean,components,evr}) + .done.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
SR, FRAME_SR, FS = 16000, 1000, 128
FAMILIES = {"ace": {"n_ch": 22, "lo": 188.0, "hi": 7938.0, "n_max": 8},
            "ab": {"n_ch": 16, "lo": 250.0, "hi": 7900.0, "n_max": None},  # 8000 Hz = Nyquist at 16 kHz
            "medel": {"n_ch": 12, "lo": 100.0, "hi": 7900.0, "n_max": None}}
STRATEGY_FAMILY = {"ACE": "ace", "HiRes Optima-S": "ab", "HiRes-S incl. Fidelity 120": "ab", "FS4": "medel", "FSP": "medel", "HDCIS": "medel"}
IDR_DB, RHO, K = 40.0, 416.0, 5


def _filterbank(fam):
    from scipy.signal import butter
    p = FAMILIES[fam]
    edges = np.geomspace(p["lo"], p["hi"], p["n_ch"] + 1)
    return [butter(4, [edges[i], edges[i + 1]], btype="band", fs=SR, output="sos") for i in range(p["n_ch"])], edges


def envelopes(x16, fam):
    """(n_ch, n_frames) channel envelopes at 1 kHz (before n-of-m and mapping)."""
    from scipy.signal import butter, sosfilt
    bank, _ = _filterbank(fam)
    lp = butter(2, 200.0, btype="low", fs=SR, output="sos")
    pre = sosfilt(butter(1, 1200.0, btype="high", fs=SR, output="sos"), x16) * 0.75 + x16 * 0.25  # mild pre-emphasis
    step = SR // FRAME_SR
    return np.stack([sosfilt(lp, np.abs(sosfilt(sos, pre)))[::step] for sos in bank]).astype(np.float32)


def electrodogram(env, ref, fam):
    """n-of-m selection (ACE) and loudness-growth map -> per-channel stimulation level in [0, 1] at 1 kHz."""
    E = env.copy()
    nmax = FAMILIES[fam]["n_max"]
    if nmax is not None:
        thr = -np.sort(-E, axis=0)[nmax - 1]
        E[E < thr[None, :]] = 0.0
    b = 10 ** (-IDR_DB / 20)
    xn = np.clip(E / ref, 0, 1)
    return (np.log1p(RHO * np.clip((xn - b) / (1 - b), 0, 1)) / np.log1p(RHO)).astype(np.float32)


def build():
    import h5py
    from scipy.signal import resample_poly
    from .features import _streams
    lengths = {}
    with h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r") as fa:
        for c in fa.keys():
            if c.startswith("_"):
                continue
            for s in fa[c].keys():
                lengths[(c, s)] = fa[f"{c}/{s}/shallow_01_02"].shape[1]
    streams = [(c, s, x, sha) for c, s, x, silent, sha in _streams() if not silent]
    summary = {}
    for fam in FAMILIES:
        out = os.path.join(FEAT, f"ci_edg_{fam}_pca5_128hz.h5")
        if os.path.exists(out + ".done.json"):
            print("skip", out); continue
        env = {(c, s): envelopes(x, fam) for c, s, x, _ in streams}
        ref = float(np.percentile(np.concatenate([e.ravel() for e in env.values()]), 99.9))
        edg = {}
        for (c, s), e in env.items():
            v = resample_poly(electrodogram(e, ref, fam), 16, 125, axis=1)  # 1000 -> 128 Hz
            n = lengths[(c, s)]
            v = v[:, :n] if v.shape[1] >= n else np.pad(v, ((0, 0), (0, n - v.shape[1])))
            edg[(c, s)] = v.astype(np.float64)
        seen, uniq = set(), []
        for c, s, _, sha in streams:
            if sha not in seen:
                seen.add(sha); uniq.append((c, s))
        X = np.concatenate([edg[k].T for k in uniq])
        mu = X.mean(0); w, V = np.linalg.eigh(np.cov(X - mu, rowvar=False))
        o_ = np.argsort(w)[::-1]; w, V = w[o_], V[:, o_]
        V = V * np.sign(V[np.argmax(np.abs(V), axis=0), np.arange(V.shape[1])])
        evr = w / w.sum()
        tmp = out + ".tmp"
        with h5py.File(tmp, "w") as o:
            o.attrs.update(family=fam, params=json.dumps(FAMILIES[fam]), idr_db=IDR_DB, rho=RHO, ref_99_9pct=ref, fs=FS,
                           note="simulated electrodogram envelope PCA-5 (unfiltered 128 Hz; band-pass at analysis)")
            g = o.create_group("_pca"); g.create_dataset("mean", data=mu); g.create_dataset("components", data=V[:, :K].T)
            g.create_dataset("evr", data=evr[:K])
            for (c, s), v in edg.items():
                o.create_dataset(f"{c}/{s}/edg", data=((v.T - mu) @ V[:, :K]).T.astype(np.float32))
        os.replace(tmp, out)
        summary[fam] = {"n_channels": FAMILIES[fam]["n_ch"], "evr_k5": float(evr[:K].sum()), "evr_each": evr[:K].tolist(),
                        "n_streams": len(edg), "n_unique": len(uniq)}
        meta = {"summary": summary[fam], "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}
        json.dump(meta, open(out + ".done.json", "w"), indent=1)
        print(fam, summary[fam], flush=True)


def sanity():
    """Band-passed EDG PCs vs band-passed Ac PCA-5: same-time R^2 of each EDG PC on Ac, and canonical correlations."""
    import h5py
    from .public_mi import _bp
    res = {}
    with h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r") as fa:
        for fam in FAMILIES:
            with h5py.File(os.path.join(FEAT, f"ci_edg_{fam}_pca5_128hz.h5"), "r") as fe:
                E, A = [], []
                for c in sorted(k for k in fe.keys() if not k.startswith("_")):
                    for s in fe[c].keys():
                        e = _bp(fe[f"{c}/{s}/edg"][()]); a = _bp(fa[f"{c}/{s}/shallow_01_02"][()][:5])
                        n = min(e.shape[1], a.shape[1]); E.append(e[:, 300:n - 300].T); A.append(a[:, 300:n - 300].T)
                E, A = np.concatenate(E), np.concatenate(A)
                E = (E - E.mean(0)) / E.std(0); A = (A - A.mean(0)) / A.std(0)
                A1 = np.column_stack([np.ones(len(A)), A])
                r2 = [float(1 - np.var(E[:, i] - A1 @ np.linalg.lstsq(A1, E[:, i], rcond=None)[0]) / np.var(E[:, i])) for i in range(E.shape[1])]
                Qe, _ = np.linalg.qr(E); Qa, _ = np.linalg.qr(A)
                cc = np.linalg.svd(Qe.T @ Qa, compute_uv=False)
                res[fam] = {"r2_edg_pc_on_ac_same_time": r2, "canonical_corr": cc.tolist(), "evr_k5": json.load(open(os.path.join(FEAT, f"ci_edg_{fam}_pca5_128hz.h5.done.json")))["summary"]["evr_k5"]}
    os.makedirs("private/auditory_c3/ci_edg", exist_ok=True)
    json.dump(res, open("private/auditory_c3/ci_edg/stimulus_sanity.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"build": build, "sanity": sanity}[sys.argv[1]]()
