"""DTU envelope-level attention analysis (04 §4.3-4.4; MEASUREMENT_AMENDMENT_001 §7-8: no raw audio, so only the
envelope layer). Stage A 1-8 Hz EEG, average reference over the 64 scalp channels, T = ROI first 3 PCs (ROIs as close
as the Biosemi-64 montage allows to the FAU/TUD definition). Envelopes = the presented sound (CamEQ-amplified for HI
listeners, as heard; NH have only the unequalised version), band-passed 1-8 Hz like the EEG. Two-talker trials start
the valid range 1.7 s (FIR transient of the zero-filled pre-onset masker envelope) + 0.61 s after the masker onset. 200 circular-shift surrogates within trials (>= 5 s).

Usage: python -m auditory_c3.dtu_mi <sub-XXX>
Output (per participant, private): private/auditory_c3/public/dtu/<sub>.json
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

from .engine import Subject
from .public_mi import FS, LAGS, WINDOWS, win_mask

PRE = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/dtu_snhl"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "private", "auditory_c3", "public", "dtu")
ROIS = {"frontocentral": ["Fz", "FC1", "FCz", "Cz", "C3", "C4", "CP1", "CP2"],
        "left_temporal": ["F7", "FC5", "T7", "CP5", "TP7"],
        "right_temporal": ["F8", "FC6", "T8", "CP6", "TP8"]}


def _bp(x):
    import mne
    return mne.filter.filter_data(np.atleast_2d(np.nan_to_num(x)).astype(np.float64), FS, 1.0, 8.0, method="fir",
                                  phase="zero", fir_design="firwin", pad="reflect_limited", verbose=False)


def run(sub):
    import h5py
    trials = []
    for p in sorted(glob.glob(os.path.join(PRE, f"{sub}*.h5"))):
        with h5py.File(p, "r") as f:
            ch = [str(c) for c in f.attrs["channels"]][:64]
            for k in sorted(f.keys()):
                g = f[k]
                X = g["eeg_1_8"][()][:64].astype(np.float64)
                X = X - X.mean(0, keepdims=True)  # average reference over the 64 scalp channels
                n = X.shape[1]
                two = str(g.attrs["talkers"]) == "twotalker"
                a = int(LAGS.max()) + 1
                if two:
                    mo = float(g.attrs["masker_onset_rel_s"])
                    # masker envelope is NaN before its onset (zero-filled before filtering): skip the 1.7 s FIR transient
                    a = max(a, int(np.ceil((mo + 1.7) * FS)) + int(LAGS.max()) + 1)
                stim = {"Env_att": _bp(g["env_target"][()])}
                if two and "env_masker" in g:
                    stim["Env_ign"] = _bp(g["env_masker"][()])
                trials.append({"X": X, "valid": (a, n + int(LAGS.min())), "stim": stim, "two": two})
    res = {"subject": sub, "n_trials": len(trials), "n_two": sum(t["two"] for t in trials)}
    for roi, chs in ROIS.items():
        idx = [ch.index(c) for c in chs]
        V = np.concatenate([t["X"][idx][:, slice(*t["valid"])] for t in trials], axis=1)
        mu = V.mean(1, keepdims=True)
        w, U = np.linalg.eigh((V - mu) @ (V - mu).T)
        U = U[:, np.argsort(w)[::-1][:3]]
        Ts = [U.T @ (t["X"][idx] - mu) for t in trials]
        S = Subject([{"T": T, "valid": t["valid"], "stim": {"Env_att": t["stim"]["Env_att"]}} for T, t in zip(Ts, trials)],
                    FS, LAGS, n_sur=200, seed=int(sub[-3:]))
        Sc = Subject([{"T": T, "valid": t["valid"], "stim": t["stim"]} for T, t in zip(Ts, trials) if t["two"] and "Env_ign" in t["stim"]],
                     FS, LAGS, n_sur=200, seed=int(sub[-3:]) + 1)
        for name, arr in (("TMIF_Env_att", S.mi("Env_att")), ("CS_TMIF_Env_att", Sc.mi("Env_att")), ("CS_TMIF_Env_ign", Sc.mi("Env_ign"))):
            res[f"{roi}/{name}/per_lag_obs"] = arr[0].tolist(); res[f"{roi}/{name}/per_lag_sur_mean"] = arr[1:].mean(0).tolist()
            for wname in WINDOWS:
                v = arr[:, win_mask(wname)].mean(1)
                res[f"{roi}/{name}/{wname}"] = {"obs": float(v[0]), "sur_mean": float(v[1:].mean()), "corr": float(v[0] - v[1:].mean())}
        res[f"{roi}/N"] = {"all": S.N, "two": Sc.N}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"{sub}.json"), "w"))
    print(sub, "done", res["n_trials"], res["n_two"])



def run_main(sub):
    """DTU with audio (D1): the FAU/TUD main quantities (MEASUREMENT_AMENDMENT_001 §1, frozen L27) on the original speech
    features (features_dtu.py). Output: private/auditory_c3/public/dtu_v2/<sub>.json."""
    import h5py
    from .engine import ridge_loto
    from .public_mi import ALPHAS, K_STIM, _mediated, _z, window_summary
    FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
    inv = json.load(open(os.path.join(FEAT, "inventory.json")))
    sha = {(r["file"], r["trial"], r["kind"]): (r.get("sha"), r["offset_s"]) for r in inv}
    pca = h5py.File(os.path.join(FEAT, "pca_k8_128hz_dtu.h5"), "r")

    def place(key, name, n):
        h, off = sha.get(key, (None, 0.0))
        if h is None:
            return None
        z = pca[f"{h}/{name}"][()][:K_STIM]
        out = np.zeros((K_STIM, n)); a = int(round(off * FS)); m = min(z.shape[1], n - a)
        out[:, a:a + m] = z[:, :m]
        return _bp(out)
    trials = []
    for p in sorted(glob.glob(os.path.join(PRE, f"{sub}*.h5"))):
        tag = os.path.basename(p)[:-3]
        with h5py.File(p, "r") as f:
            ch = [str(c) for c in f.attrs["channels"]][:64]
            for k in sorted(f.keys()):
                g = f[k]
                X = g["eeg_1_8"][()][:64].astype(np.float64); X = X - X.mean(0, keepdims=True)
                n = X.shape[1]; two = str(g.attrs["talkers"]) == "twotalker"
                a = int(LAGS.max()) + 1
                if two:
                    a = max(a, int(np.ceil((float(g.attrs["masker_onset_rel_s"]) + 1.7) * FS)) + int(LAGS.max()) + 1)
                st = {"Env_att": _bp(g["env_target"][()]), "Ac_att": place((tag, k, "target"), "shallow_01_02", n),
                      "L27_att": place((tag, k, "target"), "layer_27", n)}
                if two:
                    st.update(Env_ign=_bp(g["env_masker"][()]), Ac_ign=place((tag, k, "masker"), "shallow_01_02", n),
                              L27_ign=place((tag, k, "masker"), "layer_27", n))
                if any(v is None for v in st.values()):
                    continue
                trials.append({"X": X, "valid": (a, n + int(LAGS.min())), "stim": st, "two": two, "n": n})
    res = {"subject": sub, "n_trials": len(trials), "n_two": sum(t["two"] for t in trials), "mode": "dtu_v2_main"}
    for roi, chs in ROIS.items():
        idx = [ch.index(c) for c in chs]
        V = np.concatenate([t["X"][idx][:, slice(*t["valid"])] for t in trials], axis=1)
        mu = V.mean(1, keepdims=True)
        w, U = np.linalg.eigh((V - mu) @ (V - mu).T); U = U[:, np.argsort(w)[::-1][:3]]
        Ts = [U.T @ (t["X"][idx] - mu) for t in trials]
        tz = [_z(T) for T in Ts]

        def feats(kind):
            return [_z(np.vstack([t["stim"][f"{kind}_att"], t["stim"].get(f"{kind}_ign", np.zeros((K_STIM, t["n"])))])) for t in trials]
        yAc, aA, rA = ridge_loto(feats("Ac"), tz, LAGS, ALPHAS)
        yL, aL, rL = ridge_loto(feats("L27"), tz, LAGS, ALPHAS)
        S = Subject([{"T": T, "valid": t["valid"], "stim": {k: t["stim"][k] for k in ("Ac_att", "L27_att", "Env_att")}} for T, t in zip(Ts, trials)],
                    FS, LAGS, n_sur=200, seed=int(sub[-3:]))
        S.add_mediator("yAc", yAc); S.add_mediator("yL", yL)
        two = [i for i, t in enumerate(trials) if t["two"]]
        Sc = Subject([{"T": Ts[i], "valid": trials[i]["valid"], "stim": trials[i]["stim"]} for i in two], FS, LAGS, n_sur=200, seed=int(sub[-3:]) + 1)
        Sc.add_mediator("yAc", [yAc[i] for i in two])
        q = {"TMIF_Ac_att": S.mi("Ac_att"), "TMIF_Env_att": S.mi("Env_att"),
             "CMI_L_att_given_yAc": S.cmi("L27_att", cond_meds=("yAc",)), "CMI_Ac_att_given_yL": S.cmi("Ac_att", cond_meds=("yL",)),
             "CS_CMI_L_att_given_yAc": Sc.cmi("L27_att", cond_meds=("yAc",)), "CS_CMI_L_ign_given_yAc": Sc.cmi("L27_ign", cond_meds=("yAc",)),
             "CS_TMIF_Ac_att": Sc.mi("Ac_att"), "CS_TMIF_Ac_ign": Sc.mi("Ac_ign"),
             "CS_TMIF_Env_att": Sc.mi("Env_att"), "CS_TMIF_Env_ign": Sc.mi("Env_ign")}
        for k, arr in q.items():
            res[f"{roi}/{k}/per_lag_obs"] = arr[0].tolist(); res[f"{roi}/{k}/per_lag_sur_mean"] = arr[1:].mean(0).tolist()
            for wname, v in window_summary(arr).items():
                res[f"{roi}/{k}/{wname}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        for k, arr in _mediated(S, ("yAc", "yL")).items():
            res[f"{roi}/MED/{k}"] = {"obs": float(arr[0]), "sur_mean": float(arr[1:].mean()), "corr": float(arr[0] - arr[1:].mean())}
        res[f"{roi}/ridge"] = {"Ac": {"alpha": aA, "r": rA}, "L": {"alpha": aL, "r": rL}}
        res[f"{roi}/tie_fraction"] = {"all": S.tie_fraction, "cs": Sc.tie_fraction}
        print(sub, roi, "TMIF_Ac %.5f CMI_L %.5f" % (res[f"{roi}/TMIF_Ac_att/all"]["corr"], res[f"{roi}/CMI_L_att_given_yAc/all"]["corr"]), flush=True)
    d = os.path.join(REPO, "private", "auditory_c3", "public", "dtu_v2"); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{sub}.json"), "w"), default=float)


def run_sur(sub):
    """C3_EXTENSIONS_REG_v1 B1 (DTU): Danish mGPT word surprisal beyond yAc and word onsets.
    Output: private/auditory_c3/public/dtu_sur/<sub>.json."""
    import h5py
    from .engine import ridge_loto
    from .public_mi import ALPHAS, K_STIM, _z, window_summary
    FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
    inv = json.load(open(os.path.join(FEAT, "inventory.json")))
    sha = {(r["file"], r["trial"], r["kind"]): (r.get("sha"), r["offset_s"]) for r in inv}
    pca = h5py.File(os.path.join(FEAT, "pca_k8_128hz_dtu.h5"), "r")
    words = json.load(open(os.path.join(FEAT, "mgpt_word_surprisal_da.json")))["streams"]

    def place(key, name, n):
        h, off = sha.get(key, (None, 0.0))
        if h is None:
            return None
        z = pca[f"{h}/{name}"][()][:K_STIM]
        out = np.zeros((K_STIM, n)); a = int(round(off * FS)); m = min(z.shape[1], n - a)
        out[:, a:a + m] = z[:, :m]
        return _bp(out)

    def trains(key, n):
        h, _ = sha.get(key, (None, 0.0))
        if h is None or h not in words:
            return None, None
        su, on = np.zeros(n), np.zeros(n)
        for w in words[h]:
            if w["t0"] is None:
                continue
            i = int(round(w["t0"] * FS))
            if 0 <= i < n:
                su[i] += w["surprisal_bits"]; on[i] += 1.0
        return _bp(su[None])[0], _bp(on[None])[0]
    trials = []
    for p in sorted(glob.glob(os.path.join(PRE, f"{sub}*.h5"))):
        tag = os.path.basename(p)[:-3]
        with h5py.File(p, "r") as f:
            ch = [str(c) for c in f.attrs["channels"]][:64]
            for k in sorted(f.keys()):
                g = f[k]
                X = g["eeg_1_8"][()][:64].astype(np.float64); X = X - X.mean(0, keepdims=True)
                n = X.shape[1]; two = str(g.attrs["talkers"]) == "twotalker"
                a = int(LAGS.max()) + 1
                if two:
                    a = max(a, int(np.ceil((float(g.attrs["masker_onset_rel_s"]) + 1.7) * FS)) + int(LAGS.max()) + 1)
                su, on = trains((tag, k, "target"), n)
                st = {"Ac_att": place((tag, k, "target"), "shallow_01_02", n), "Sur_att": su, "Ons_att": on}
                if two:
                    st["Ac_ign"] = place((tag, k, "masker"), "shallow_01_02", n)
                if any(v is None for v in st.values()):
                    continue
                trials.append({"X": X, "valid": (a, n + int(LAGS.min())), "stim": st, "two": two, "n": n})
    res = {"subject": sub, "n_trials": len(trials), "mode": "dtu_sur"}
    for roi, chs in ROIS.items():
        idx = [ch.index(c) for c in chs]
        V = np.concatenate([t["X"][idx][:, slice(*t["valid"])] for t in trials], axis=1)
        mu = V.mean(1, keepdims=True)
        w, U = np.linalg.eigh((V - mu) @ (V - mu).T); U = U[:, np.argsort(w)[::-1][:3]]
        Ts = [U.T @ (t["X"][idx] - mu) for t in trials]
        tz = [_z(T) for T in Ts]
        yAc, _, _ = ridge_loto([_z(np.vstack([t["stim"]["Ac_att"], t["stim"].get("Ac_ign", np.zeros((K_STIM, t["n"])))])) for t in trials], tz, LAGS, ALPHAS)
        yOns, _, _ = ridge_loto([_z(t["stim"]["Ons_att"][None]) for t in trials], tz, LAGS, ALPHAS)
        S = Subject([{"T": T, "valid": t["valid"], "stim": {"Sur_att": t["stim"]["Sur_att"][None], "Ons_att": t["stim"]["Ons_att"][None]}} for T, t in zip(Ts, trials)],
                    FS, LAGS, n_sur=200, seed=int(sub[-3:]) + 21)
        S.add_mediator("yAc", yAc); S.add_mediator("yOns", yOns)
        q = {"CMI_Sur_given_yAc_yOns": S.cmi("Sur_att", cond_meds=("yAc", "yOns")), "CMI_Sur_given_yAc": S.cmi("Sur_att", cond_meds=("yAc",)),
             "CMI_Ons_given_yAc": S.cmi("Ons_att", cond_meds=("yAc",))}
        for kq, arr in q.items():
            for wname, v in window_summary(arr).items():
                res[f"{roi}/{kq}/{wname}"] = {kk: (vv if kk != "sur" else None) for kk, vv in v.items()}
        print(sub, roi, "Sur|Ac,Ons %.5f" % res[f"{roi}/CMI_Sur_given_yAc_yOns/all"]["corr"], flush=True)
    d = os.path.join(REPO, "private", "auditory_c3", "public", "dtu_sur"); os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, f"{sub}.json"), "w"), default=float)


if __name__ == "__main__":
    {"main": lambda: run_main(sys.argv[2]), "sur": lambda: run_sur(sys.argv[2])}.get(sys.argv[1], lambda: run(sys.argv[1]))()
