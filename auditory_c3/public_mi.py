"""Public FAU/TUD information analysis (04 §4.1-4.4 as amended by docs/auditory_c3/MEASUREMENT_AMENDMENT_001.md).

Per subject and ROI: T = first 3 principal components of the ROI channels (stage B, average reference, interpolated,
ICA-cleaned by default), PCA fitted on the subject's own valid samples (EEG only). Stimulus variables (128 Hz, same
1-8 Hz FIR as the EEG): Ac = Whisper shallow (mean of layers 1-2) PCA k=5, L = Whisper layer PCA k=5, published
envelopes. Mediators: leave-one-trial-out ridge predictions of T from [Ac_att, Ac_ign] (y_Ac) and [L_att, L_ign]
(y_L) over lags -200..600 ms. All information values via auditory_c3.engine with 200 circular-shift surrogates.

Usage:
  python -m auditory_c3.public_mi select <subject_id>          # TH selection half, all candidate layers
  python -m auditory_c3.public_mi main <grp> <subject_id> <layer> [--noica] [--pub]
Outputs (per-participant, private): private/auditory_c3/public/fau_tud/<mode>/<grp>/<subject>.npz
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from .engine import Subject, ent_from_cov, ridge_loto

PRE = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1"
FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud")
FS = 128
LAGS = np.arange(-26, 78)  # -203 .. 602 ms
WINDOWS = {"diag": (-200, 0), "w1": (0, 80), "w2": (90, 300), "w3": (300, 601), "all": (0, 601)}
ROIS = {"frontocentral": ["Fz", "FC1", "Cz", "C3", "C4", "CP1", "CP2"],
        "left_temporal": ["F7", "FC5", "T7", "CP5", "TP9"],
        "right_temporal": ["F8", "FC6", "T8", "CP6", "TP10"]}
K_STIM, K_T = 5, 3
ALPHAS = list(np.logspace(-2, 6, 9))
N_SUR = 200
GROUP_OF = {"1": "ci", "2": "ha", "3": "th"}


def win_mask(name):
    lo, hi = WINDOWS[name]
    ms = LAGS * 1000.0 / FS
    return (ms >= lo) & (ms < hi)


def _bp(x):
    import mne
    return mne.filter.filter_data(np.atleast_2d(x).astype(np.float64), FS, 1.0, 8.0, method="fir", phase="zero",
                                  fir_design="firwin", pad="reflect_limited", verbose=False)


class Stimuli:
    """1-8 Hz band-passed stimulus variables per code, cached."""

    def __init__(self):
        import h5py
        self.pw = h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper.h5"), "r")
        self.ps = h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r")
        self.px = h5py.File(os.path.join(FEAT, "pca_k8_128hz_xlsr.h5"), "r")
        self.env = h5py.File(os.path.join(PRE, "fau_tud", "stimulus_env_128.h5"), "r")
        self.cache = {}

    def get(self, code, stream, kind, n):
        """kind: 'Ac', 'L<ll>' (Whisper layer), 'X<ll>' (XLS-R layer), 'Env'. None if the stream is silent."""
        key = (code, stream, kind, n)
        if key in self.cache:
            return self.cache[key]
        if kind == "Env":
            e = self.env[f"{code}/{stream}_env/raw"][()]
            if np.isnan(e).all():
                v = None
            else:
                v = _bp(np.nan_to_num(e))[:, :n]
        else:
            if kind == "Ac":
                src, layer = self.ps, "shallow_01_02"
            elif kind[0] == "L":
                src, layer = self.pw, f"layer_{kind[1:]}"
            else:
                src, layer = self.px, f"layer_{kind[1:]}"
            path = f"{code}/{stream}/{layer}"
            v = None if path not in src else _bp(src[path][()][:K_STIM])[:, :n]
        if v is not None and v.shape[1] < n:
            v = np.pad(v, ((0, 0), (0, n - v.shape[1])))
        self.cache[key] = v
        return v


def distractor_onset(stim, code, n):
    """First sample of 10 consecutive raw distractor-envelope samples above its mean (Jehn utils.find_start_distractor)."""
    e = stim.env[f"{code}/distractor_env/raw"][()][:n]
    if np.isnan(e).all():
        return None
    above = np.nan_to_num(e) > np.nanmean(e)
    run = np.convolve(above.astype(int), np.ones(10, int), "valid")
    return int(np.flatnonzero(run == 10)[0])


STAGE = "fau_tud_stageB"  # "--stagec" on the command line switches to stage C (B + EOG removal) and mode "*_eog"


def load_subject(grp, subj, ica=True, pub=False):
    import h5py
    p = os.path.join(PRE, STAGE, grp, f"{subj}.h5")
    with h5py.File(p, "r") as f:
        ch = list(f.attrs["channels"])
        trials = []
        for t in sorted(f.keys()):
            g = f[t]
            name = f"eeg_1_8_{'ica' if ica else 'noica'}" + ("_pub" if pub and f"eeg_1_8_noica_pub" in g else "")
            trials.append({"key": t, "code": str(g.attrs["stimulus"]), "X": g[name][()].astype(np.float64),
                           "valid": (int(g.attrs["valid_start"]), int(g.attrs["valid_stop"]))})
    return ch, trials


def roi_T(ch, trials, roi):
    idx = [ch.index(c) for c in ROIS[roi]]
    V = np.concatenate([t["X"][idx][:, slice(*t["valid"])] for t in trials], axis=1)
    mu = V.mean(1, keepdims=True)
    w, U = np.linalg.eigh((V - mu) @ (V - mu).T)
    U = U[:, np.argsort(w)[::-1][:K_T]]
    return [U.T @ (t["X"][idx] - mu) for t in trials]


def _z(x):
    s = x.std(1, keepdims=True); s[s == 0] = 1
    return (x - x.mean(1, keepdims=True)) / s


def build(grp, subj, layers, ica=True, pub=False, l_streams=("attended", "distractor")):
    """Returns per-ROI dict with Subject objects (all trials and CS trials) and ridge diagnostics."""
    stim = Stimuli()
    ch, trials = load_subject(grp, subj, ica, pub)
    out = {}
    for roi in ROIS:
        Ts = roi_T(ch, trials, roi)
        recs = []
        for t, T in zip(trials, Ts):
            n = T.shape[1]
            S = {}
            for stream, tag in (("attended", "att"), ("distractor", "ign")):
                for kind in ["Ac", "Env"] + ([f"L{l:02d}" for l in layers] if stream in l_streams else []):
                    v = stim.get(t["code"], stream, kind, n)
                    if v is not None:
                        S[f"{kind}_{tag}"] = v
            cs = int(t["key"].split("_")[1]) >= 9
            a, b = t["valid"]
            a_cs = a
            if cs:
                d0 = distractor_onset(stim, t["code"], n)
                a_cs = max(a, (d0 or 0) + int(LAGS.max()) + 1)
            recs.append({"T": T, "valid": (a, b), "valid_cs": (a_cs, b), "stim": S, "cs": cs, "n": n, "code": t["code"]})
        # mediators: ridge LOTO from both streams (absent stream = zeros)
        def feats(kind):
            return [_z(np.vstack([r["stim"].get(f"{kind}_att", np.zeros((K_STIM, r["n"]))),
                                  r["stim"].get(f"{kind}_ign", np.zeros((K_STIM, r["n"])))])) for r in recs]
        tz = [_z(r["T"]) for r in recs]
        yAc, aAc, rAc = ridge_loto(feats("Ac"), tz, LAGS, ALPHAS)
        res = {"ridge": {"Ac": {"alpha": aAc, "r": rAc}}, "recs": recs, "yAc": yAc}
        out[roi] = res
    return out, stim


def window_summary(arr):
    """arr (n_sur+1, n_lags) -> dict window -> (obs, surrogate mean, corrected, surrogate distribution)."""
    out = {}
    for w in WINDOWS:
        m = win_mask(w)
        v = arr[:, m].mean(1)
        out[w] = {"obs": float(v[0]), "sur_mean": float(v[1:].mean()), "corr": float(v[0] - v[1:].mean()), "sur": v[1:]}
    return out


def _subject_obj(recs, keys, meds, seed, cs=False):
    tr = []
    for r in recs:
        if cs and not r["cs"]:
            continue
        tr.append({"T": r["T"], "valid": r["valid_cs"] if cs else r["valid"], "stim": {k: r["stim"][k] for k in keys if k in r["stim"]}})
    S = Subject(tr, FS, LAGS, n_sur=N_SUR, seed=seed)
    for name, Ys in meds.items():
        S.add_mediator(name, [y for y, r in zip(Ys, recs) if (r["cs"] or not cs)])
    return S


def cmd_select(subj):
    grp = GROUP_OF[subj[0]]
    layers = list(range(3, 33))
    built, _ = build(grp, subj, layers, l_streams=("attended",))
    res = {}
    for roi, b in built.items():
        keys = [f"L{l:02d}_att" for l in layers]
        S = _subject_obj(b["recs"], keys, {"yAc": b["yAc"]}, seed=int(subj))
        for l in layers:
            E = S.cmi(f"L{l:02d}_att", cond_meds=("yAc",))
            ws = window_summary(E)["all"]
            res[f"{roi}/L{l:02d}"] = ws["corr"]
        res[f"{roi}/ridge_Ac"] = b["ridge"]["Ac"]
        print(subj, roi, "best", max(layers, key=lambda l: res[f"{roi}/L{l:02d}"]), flush=True)
    os.makedirs(os.path.join(OUT, "select"), exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "select", f"{subj}.json"), "w"), indent=1, default=float)


def _mediated(S, meds):
    """Lag-free mediated quantities on (y_Ac, y_L, T): MIs, CMI, MMI-PID, I_ccs-PID; obs + surrogates."""
    from .pid_ccs import iccs_redundancy
    C, off = S.med_cov(meds)
    N = S.N
    dA = off[1] - off[0]; dL = off[2] - off[1]
    iA = np.arange(0, dA); iL = np.arange(dA, dA + dL); iT = np.arange(dA + dL, C.shape[-1])

    def H(idx):
        return ent_from_cov(C[:, idx[:, None], idx[None, :]], N)
    I_A = H(iA) + H(iT) - H(np.r_[iA, iT]); I_L = H(iL) + H(iT) - H(np.r_[iL, iT])
    I_AL = H(np.r_[iA, iL]) + H(iT) - H(np.r_[iA, iL, iT])
    out = {"I_T_yAc": I_A, "I_T_yL": I_L, "I_T_yAcyL": I_AL, "CMI_T_yL_given_yAc": I_AL - I_A}
    R_mmi = np.minimum(I_A, I_L)
    out.update(MMI_R=R_mmi, MMI_UAc=I_A - R_mmi, MMI_UL=I_L - R_mmi, MMI_S=I_AL - I_A - I_L + R_mmi)
    # I_ccs on the raw (non-bias-corrected) Gaussian covariance; bias handled by the surrogate subtraction
    R_ccs = np.array([iccs_redundancy(C[b], dA, dL, len(iT), n_mc=50_000, rng=1000 + b) for b in range(C.shape[0])])
    out.update(CCS_R=R_ccs, CCS_UAc=I_A - R_ccs, CCS_UL=I_L - R_ccs, CCS_S=I_AL - I_A - I_L + R_ccs)
    return out


def cmd_main(grp, subj, layer, ica=True, pub=False):
    lname = f"L{int(layer):02d}"
    mode = "main_v2" + ("_noica" if not ica else "") + ("_pub" if pub else "") + ("_eog" if STAGE.endswith("stageC") else "")  # v2: tie-aware copula
    built, stim = build(grp, subj, [int(layer)], ica=ica, pub=pub)
    res = {"subject": subj, "group": grp, "layer": lname, "mode": mode, "lags_ms": (LAGS * 1000.0 / FS).tolist()}
    for roi, b in built.items():
        recs = b["recs"]
        featsL = [_z(np.vstack([r["stim"].get(f"{lname}_att", np.zeros((K_STIM, r["n"]))),
                                r["stim"].get(f"{lname}_ign", np.zeros((K_STIM, r["n"])))])) for r in recs]
        yL, aL, rL = ridge_loto(featsL, [_z(r["T"]) for r in recs], LAGS, ALPHAS)
        meds = {"yAc": b["yAc"], "yL": yL}
        # all 20 trials, attended stream
        S = _subject_obj(recs, ["Ac_att", f"{lname}_att", "Env_att"], meds, seed=int(subj))
        q = {"TMIF_Ac_att": S.mi("Ac_att"), "TMIF_Env_att": S.mi("Env_att"),
             "CMI_L_att_given_yAc": S.cmi(f"{lname}_att", cond_meds=("yAc",)),
             "CMI_Ac_att_given_yL": S.cmi("Ac_att", cond_meds=("yL",)),
             "CMI_L_att_given_Ac_samelag": S.cmi(f"{lname}_att", cond_stims=("Ac_att",))}
        med = _mediated(S, ("yAc", "yL"))
        # competing-speaker trials, attended and ignored streams (from the distractor onset)
        Sc = _subject_obj(recs, ["Ac_att", "Ac_ign", f"{lname}_att", f"{lname}_ign", "Env_att", "Env_ign"], meds,
                          seed=int(subj) + 1, cs=True)
        q.update({"CS_TMIF_Env_att": Sc.mi("Env_att"), "CS_TMIF_Env_ign": Sc.mi("Env_ign"),
                  "CS_TMIF_Ac_att": Sc.mi("Ac_att"), "CS_TMIF_Ac_ign": Sc.mi("Ac_ign"),
                  "CS_CMI_L_att_given_yAc": Sc.cmi(f"{lname}_att", cond_meds=("yAc",)),
                  "CS_CMI_L_ign_given_yAc": Sc.cmi(f"{lname}_ign", cond_meds=("yAc",))})
        for k, arr in q.items():
            res[f"{roi}/{k}/per_lag_obs"] = arr[0].tolist()
            res[f"{roi}/{k}/per_lag_sur_mean"] = arr[1:].mean(0).tolist()
            for w, v in window_summary(arr).items():
                res[f"{roi}/{k}/{w}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        for k, arr in med.items():
            res[f"{roi}/MED/{k}"] = {"obs": float(arr[0]), "sur_mean": float(arr[1:].mean()), "corr": float(arr[0] - arr[1:].mean())}
        res[f"{roi}/ridge"] = {"Ac": b["ridge"]["Ac"], "L": {"alpha": aL, "r": rL}}
        res[f"{roi}/N"] = {"all": S.N, "cs": Sc.N}
        res[f"{roi}/tie_fraction"] = {"all": S.tie_fraction, "cs": Sc.tie_fraction}
        res["analysis_version"] = "v2_tie_aware_copnorm"
        print(subj, roi, "w2 TMIF_Ac %.4f CMI_L %.4f" % (res[f"{roi}/TMIF_Ac_att/w2"]["corr"], res[f"{roi}/CMI_L_att_given_yAc/w2"]["corr"]), flush=True)
    d = os.path.join(OUT, mode, grp); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{subj}.json"), "w"), default=float)


def _raw_stim(stim, code, stream, src_name, layer, k, n):
    """k leading PCA components of a cached representation, band-passed 1-8 Hz, cropped/padded to n; None if absent."""
    import h5py
    files = {"whisper": "pca_k8_128hz_whisper.h5", "shallow": "pca_k8_128hz_whisper_shallow.h5",
             "xlsr": "pca_k8_128hz_xlsr.h5", "mel": "pca_k8_128hz_mel.h5", "whisper_z27": "pca_k8_128hz_whisper_z27.h5",
             "bg": "pca_k8_128hz_bg_crossfit.h5", "bgc": "pca_k8_128hz_bg_crossfit_conv.h5"}
    key = (src_name, code, stream, layer, k, n)
    if key in stim.cache:
        return stim.cache[key]
    if not hasattr(stim, "extra"):
        stim.extra = {}
    if src_name not in stim.extra:
        stim.extra[src_name] = h5py.File(os.path.join(FEAT, files[src_name]), "r")
    f = stim.extra[src_name]
    path = f"{code}/{stream}/{layer}"
    v = None if path not in f else _bp(f[path][()][:k])[:, :n]
    if v is not None and v.shape[1] < n:
        v = np.pad(v, ((0, 0), (0, n - v.shape[1])))
    stim.cache[key] = v
    return v


def _word_trains(words_json, code, stream, n):
    """GPT-2 surprisal and word-onset impulse trains at word onsets (128 Hz), band-passed 1-8 Hz; None if silent."""
    w = words_json["streams"].get(f"{code}/{stream}")
    if not w:
        return None, None
    sur, ons = np.zeros(n), np.zeros(n)
    for x in w:
        i = int(round(x["t0"] * FS))
        if 0 <= i < n:
            sur[i] += x["surprisal_bits"]; ons[i] += 1.0
    return _bp(sur), _bp(ons)


def cmd_controls(grp, subj, layer=27, xlsr_layer=20):
    """04 §4.2 control checks (DECISION_001 §6): replace L by XLS-R / GPT-2 surprisal / word onsets, replace Ac by
    log-mel, and k = 3 / 8 for both Ac and L. All CMI conditioned on the matching cross-validated acoustic prediction."""
    words = json.load(open(os.path.join(FEAT, "gpt2_german_word_surprisal.json")))
    built, stim = build(grp, subj, [layer])
    lname = f"L{layer:02d}"
    res = {"subject": subj, "group": grp, "mode": "controls"}
    for roi, b in built.items():
        recs = b["recs"]
        for r in recs:
            n, code = r["n"], r["code"]
            for stream, tag in (("attended", "att"), ("distractor", "ign")):
                for name, (src_name, lay, k) in {"X20": ("xlsr", f"layer_{xlsr_layer:02d}", 5), "Mel": ("mel", "logmel", 5),
                                                 "Ac3": ("shallow", "shallow_01_02", 3), "Ac8": ("shallow", "shallow_01_02", 8),
                                                 "L3": ("whisper", f"layer_{layer:02d}", 3), "L8": ("whisper", f"layer_{layer:02d}", 8)}.items():
                    v = _raw_stim(stim, code, stream, src_name, lay, k, n)
                    if v is not None:
                        r["stim"][f"{name}_{tag}"] = v
                su, on = _word_trains(words, code, stream, n)
                if su is not None:
                    r["stim"][f"Sur_{tag}"] = su; r["stim"][f"Ons_{tag}"] = on
        tz = [_z(r["T"]) for r in recs]

        def med(kind, k):
            X = [_z(np.vstack([r["stim"].get(f"{kind}_att", np.zeros((k, r["n"]))), r["stim"].get(f"{kind}_ign", np.zeros((k, r["n"])))])) for r in recs]
            return ridge_loto(X, tz, LAGS, ALPHAS)
        yMel, aM, rM = med("Mel", 5); yAc3, a3, r3 = med("Ac3", 3); yAc8, a8, r8 = med("Ac8", 8); yOns, aO, rO = med("Ons", 1)
        keys = ["X20_att", "Sur_att", "Ons_att", f"{lname}_att", "L3_att", "L8_att", "Mel_att"]
        S = _subject_obj(recs, keys, {"yAc": b["yAc"], "yMel": yMel, "yAc3": yAc3, "yAc8": yAc8, "yOns": yOns}, seed=int(subj) + 7)
        q = {"CMI_X20_given_yAc": S.cmi("X20_att", cond_meds=("yAc",)),
             "CMI_Sur_given_yAc": S.cmi("Sur_att", cond_meds=("yAc",)),
             "CMI_Ons_given_yAc": S.cmi("Ons_att", cond_meds=("yAc",)),
             "CMI_Sur_given_yAc_yOns": S.cmi("Sur_att", cond_meds=("yAc", "yOns")),
             "CMI_L_given_yMel": S.cmi(f"{lname}_att", cond_meds=("yMel",)),
             "CMI_Lk3_given_yAc3": S.cmi("L3_att", cond_meds=("yAc3",)),
             "CMI_Lk8_given_yAc8": S.cmi("L8_att", cond_meds=("yAc8",)),
             "TMIF_Mel": S.mi("Mel_att")}
        for k, arr in q.items():
            for w, v in window_summary(arr).items():
                if w in ("all", "w2", "diag"):
                    res[f"{roi}/{k}/{w}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        res[f"{roi}/tie_fraction"] = S.tie_fraction
        res["analysis_version"] = "v2_tie_aware_copnorm"
        res[f"{roi}/ridge"] = {"Mel": {"alpha": aM, "r": rM}, "Ac3": {"alpha": a3, "r": r3}, "Ac8": {"alpha": a8, "r": r8}, "Ons": {"alpha": aO, "r": rO}}
        print(subj, roi, "X20 %.5f Sur %.5f L|Mel %.5f" % (res[f"{roi}/CMI_X20_given_yAc/all"]["corr"], res[f"{roi}/CMI_Sur_given_yAc/all"]["corr"], res[f"{roi}/CMI_L_given_yMel/all"]["corr"]), flush=True)
    d = os.path.join(OUT, "controls", grp); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{subj}.json"), "w"), default=float)


def cmd_l27z(grp, subj, layer=27):
    """POST_G1_CHANGELOG 2026-10-05 (registered before results): the frozen L27 PCA-5 is 99.85 % PC1, carried by four
    high-magnitude coordinates. Sensitivity: L27 PCA-5 on z-scored coordinates (Lz) given yAc. Exploratory decomposition:
    each frozen L27 PC alone given yAc, and frozen PCs 2-5 given yAc. Same estimator, mediators and surrogates as main."""
    built, stim = build(grp, subj, [layer])
    lname = f"L{layer:02d}"
    res = {"subject": subj, "group": grp, "mode": "l27z"}
    for roi, b in built.items():
        recs = b["recs"]
        for r in recs:
            n, code = r["n"], r["code"]
            v = _raw_stim(stim, code, "attended", "whisper_z27", f"layer_{layer:02d}", 5, n)
            if v is not None:
                r["stim"]["Lz_att"] = v
            L = r["stim"][f"{lname}_att"]
            for i in range(5):
                r["stim"][f"P{i + 1}_att"] = L[i:i + 1]
            r["stim"]["P25_att"] = L[1:5]
        keys = ["Lz_att", f"{lname}_att", "P25_att"] + [f"P{i + 1}_att" for i in range(5)]
        S = _subject_obj(recs, keys, {"yAc": b["yAc"]}, seed=int(subj) + 7)
        q = {"CMI_Lz_given_yAc": S.cmi("Lz_att", cond_meds=("yAc",)),
             "CMI_L_given_yAc": S.cmi(f"{lname}_att", cond_meds=("yAc",)),
             "CMI_P25_given_yAc": S.cmi("P25_att", cond_meds=("yAc",))}
        for i in range(5):
            q[f"CMI_P{i + 1}_given_yAc"] = S.cmi(f"P{i + 1}_att", cond_meds=("yAc",))
        for k, arr in q.items():
            for w, v in window_summary(arr).items():
                if w in ("all", "w2", "diag"):
                    res[f"{roi}/{k}/{w}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        res[f"{roi}/tie_fraction"] = S.tie_fraction
        res["analysis_version"] = "v2_tie_aware_copnorm"
        print(subj, roi, "Lz %.5f L %.5f P1 %.5f P25 %.5f" % tuple(res[f"{roi}/{k}/all"]["corr"] for k in ("CMI_Lz_given_yAc", "CMI_L_given_yAc", "CMI_P1_given_yAc", "CMI_P25_given_yAc")), flush=True)
    d = os.path.join(OUT, "l27z", grp); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{subj}.json"), "w"), default=float)


def cmd_nlbg(grp, subj, layer=27, src="bg", mode="nlbg"):
    """POST_G1_CHANGELOG 2026-10-05 ~14:40 (registered before computation): deep increment beyond a cross-fitted
    non-linear acoustic background. yBG / yBGz = ridge LOTO predictions of T from L_BG (attended + distractor streams),
    conditioned together with yAc; same estimator, surrogates and ROIs as main."""
    words = json.load(open(os.path.join(FEAT, "gpt2_german_word_surprisal.json")))
    built, stim = build(grp, subj, [layer])
    lname = f"L{layer:02d}"
    res = {"subject": subj, "group": grp, "mode": mode}
    for roi, b in built.items():
        recs = b["recs"]
        for r in recs:
            n, code = r["n"], r["code"]
            for stream, tag in (("attended", "att"), ("distractor", "ign")):
                for name, (src_name, lay) in {"BGl": (src, "bg_l27"), "BGz": (src, "bg_z27"), "Lz": ("whisper_z27", f"layer_{layer:02d}")}.items():
                    v = _raw_stim(stim, code, stream, src_name, lay, 5, n)
                    if v is not None:
                        r["stim"][f"{name}_{tag}"] = v
                su, on = _word_trains(words, code, stream, n)
                if su is not None:
                    r["stim"][f"Sur_{tag}"] = su; r["stim"][f"Ons_{tag}"] = on
        tz = [_z(r["T"]) for r in recs]

        def med(kind, k):
            X = [_z(np.vstack([r["stim"].get(f"{kind}_att", np.zeros((k, r["n"]))), r["stim"].get(f"{kind}_ign", np.zeros((k, r["n"])))])) for r in recs]
            return ridge_loto(X, tz, LAGS, ALPHAS)
        yBG, aB, rB = med("BGl", 5); yBGz, aZ, rZ = med("BGz", 5); yOns, aO, rO = med("Ons", 1)
        keys = [f"{lname}_att", "Lz_att", "BGl_att", "Sur_att"]
        S = _subject_obj(recs, keys, {"yAc": b["yAc"], "yBG": yBG, "yBGz": yBGz, "yOns": yOns}, seed=int(subj) + 11)
        q = {"CMI_L_given_yAc": S.cmi(f"{lname}_att", cond_meds=("yAc",)),
             "CMI_L_given_yAc_yBG": S.cmi(f"{lname}_att", cond_meds=("yAc", "yBG")),
             "CMI_L_given_yBG": S.cmi(f"{lname}_att", cond_meds=("yBG",)),
             "CMI_Lz_given_yAc": S.cmi("Lz_att", cond_meds=("yAc",)),
             "CMI_Lz_given_yAc_yBGz": S.cmi("Lz_att", cond_meds=("yAc", "yBGz")),
             "CMI_BG_given_yAc": S.cmi("BGl_att", cond_meds=("yAc",)),
             "CMI_Sur_given_yAc_yOns": S.cmi("Sur_att", cond_meds=("yAc", "yOns")),
             "CMI_Sur_given_yAc_yOns_yBG": S.cmi("Sur_att", cond_meds=("yAc", "yOns", "yBG"))}
        for k, arr in q.items():
            for w, v in window_summary(arr).items():
                if w in ("all", "w2", "diag"):
                    res[f"{roi}/{k}/{w}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        res[f"{roi}/tie_fraction"] = S.tie_fraction
        res[f"{roi}/ridge"] = {"BG": {"alpha": aB, "r": rB}, "BGz": {"alpha": aZ, "r": rZ}, "Ons": {"alpha": aO, "r": rO}}
        res["analysis_version"] = "v2_tie_aware_copnorm"
        print(subj, roi, "L|Ac %.5f L|Ac,BG %.5f BG|Ac %.5f" % tuple(res[f"{roi}/{k}/all"]["corr"] for k in ("CMI_L_given_yAc", "CMI_L_given_yAc_yBG", "CMI_BG_given_yAc")), flush=True)
    d = os.path.join(OUT, mode, grp); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{subj}.json"), "w"), default=float)


def main(argv=None):
    global STAGE
    a = argv or sys.argv[1:]
    if "--stagec" in a:
        STAGE = "fau_tud_stageC"; a = [x for x in a if x != "--stagec"]
    if a[0] == "select":
        cmd_select(a[1])
    elif a[0] == "controls":
        cmd_controls(a[1], a[2])
    elif a[0] == "l27z":
        cmd_l27z(a[1], a[2])
    elif a[0] == "nlbg":
        cmd_nlbg(a[1], a[2])
    elif a[0] == "nlbg_conv":
        cmd_nlbg(a[1], a[2], src="bgc", mode="nlbg_conv")
    elif a[0] == "main":
        cmd_main(a[1], a[2], a[3], ica="--noica" not in a, pub="--pub" in a)


if __name__ == "__main__":
    main()
