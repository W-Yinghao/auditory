"""Stimulus-side targets for the kernel-CS alignment round (IMPLEMENTATION_NOTES §1). No EEG is read.

For every content fold, Ac (PCA-5 of mean Whisper layers 1-2), Lz (PCA-5 of z-scored Whisper layer 27) and Local
(PCA-5 of the Whisper log-mel input + broadband envelope) are fitted on the training-side unique waveforms only,
resampled to 128 Hz and band-passed 1-8 Hz (zero phase), for every stream of the cohort.

Usage: python -m auditory_alignment.prep_targets fau
       python -m auditory_alignment.prep_targets dtu_content     (content groups from SHA + Danish transcripts)
       python -m auditory_alignment.prep_targets dtu_audio       (log-mel + envelope from the original audio)
       python -m auditory_alignment.prep_targets dtu
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

import numpy as np

FAU_FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
FAU_ENV = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud/stimulus_env_128.h5"
DTU_FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
OUT_FAU = os.path.join(FAU_FEAT, "kcs_targets_v1")
OUT_DTU = os.path.join(DTU_FEAT, "kcs_targets_v1")
K = 5
FS = 128
# FAU content folds (plan content_fold 0/1): training parts (fit + early stop) of single- and competing-speaker codes
FAU_CF = {0: {"ss_fit": "1", "ss_es": "2", "ss_test": "34", "cs_fit": "05", "cs_es": "6", "cs_test": "789"},
          1: {"ss_fit": "3", "ss_es": "4", "ss_test": "12", "cs_fit": "78", "cs_es": "9", "cs_test": "056"}}


def _bp(x):
    import mne
    return mne.filter.filter_data(np.atleast_2d(x).astype(np.float64), FS, 1.0, 8.0, method="fir", phase="zero",
                                  fir_design="firwin", pad="reflect_limited", verbose=False)


def _rs(x, up, down):
    from scipy.signal import resample_poly
    return resample_poly(x, up, down, axis=-1)


def _pca(X, k=K, zscore=False):
    mu = X.mean(0); sd = X.std(0) if zscore else np.ones(X.shape[1]); sd[sd == 0] = 1
    w, V = np.linalg.eigh(np.cov((X - mu) / sd, rowvar=False))
    o = np.argsort(w)[::-1]; w, V = w[o], V[:, o]
    V = V * np.sign(V[np.argmax(np.abs(V), axis=0), np.arange(V.shape[1])])
    return {"mu": mu, "sd": sd, "V": V[:, :k], "evr": float(w[:k].sum() / w.sum())}


def _apply(p, X):
    return ((X - p["mu"]) / p["sd"]) @ p["V"]


def fau_training(code, cf):
    c = FAU_CF[cf]
    if code[0] == "1":
        return code[2] in c["ss_fit"] + c["ss_es"]
    return code[2] in c["cs_fit"] + c["cs_es"]


def run_fau():
    import h5py
    os.makedirs(OUT_FAU, exist_ok=True)
    fh = h5py.File(os.path.join(FAU_FEAT, "whisper_large_v3_hidden.h5"), "r")
    fm = h5py.File(os.path.join(FAU_FEAT, "whisper_logmel128.h5"), "r")
    fe = h5py.File(FAU_ENV, "r")
    streams = [(c, s) for c in sorted(fh.keys()) for s in sorted(fh[c].keys()) if not fh[c][s].attrs["silent"]]
    for cf in (0, 1):
        out = os.path.join(OUT_FAU, f"fau_cf{cf}.h5")
        if os.path.exists(out + ".done.json"):
            print("skip", out); continue
        seen, uniq = set(), []
        for c, s in streams:
            h = fh[c][s].attrs["wav_sha256"]
            if fau_training(c, cf) and h not in seen:
                seen.add(h); uniq.append((c, s))
        ac = np.concatenate([0.5 * (fh[c][s]["layer_01"][()].astype(np.float64) + fh[c][s]["layer_02"][()].astype(np.float64)) for c, s in uniq])
        lz = np.concatenate([fh[c][s]["layer_27"][()].astype(np.float64) for c, s in uniq])
        mel = np.concatenate([fm[c][s]["logmel"][()].T.astype(np.float64) for c, s in uniq])
        P = {"Ac": _pca(ac), "Lz": _pca(lz, zscore=True), "Mel": _pca(mel)}
        del ac, lz, mel
        meta = {"cf": cf, "fit_streams": [f"{c}/{s}" for c, s in uniq], "evr": {k: v["evr"] for k, v in P.items()}}
        with h5py.File(out + ".tmp", "w") as o:
            for c, s in streams:
                g = fh[c][s]
                ac = _apply(P["Ac"], 0.5 * (g["layer_01"][()].astype(np.float64) + g["layer_02"][()].astype(np.float64))).T
                lz = _apply(P["Lz"], g["layer_27"][()].astype(np.float64)).T
                mel = _apply(P["Mel"], fm[c][s]["logmel"][()].T.astype(np.float64)).T
                ac128, lz128, mel128 = _rs(ac, 64, 25), _rs(lz, 64, 25), _rs(mel, 32, 25)
                env = np.nan_to_num(fe[f"{c}/{'attended' if s == 'attended' else 'distractor'}_env/raw"][()].astype(np.float64))
                n = min(ac128.shape[1], lz128.shape[1], mel128.shape[1], len(env))
                local = np.vstack([mel128[:, :n], env[None, :n]])
                for name, arr in (("Ac", ac128[:, :n]), ("Lz", lz128[:, :n]), ("Local", local)):
                    o.create_dataset(f"{c}/{s}/{name}", data=_bp(arr).astype(np.float32))
            o.attrs["meta"] = json.dumps(meta)
        os.replace(out + ".tmp", out)
        json.dump({**meta, "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}, open(out + ".done.json", "w"), indent=1)
        print("done", out, meta["evr"], flush=True)


# ------------------------------------------------------------------------------------------------ DTU
def _norm_text(t):
    return re.sub(r"[^a-zæøå0-9 ]", " ", t.lower()).split()


def run_dtu_content():
    """Content groups: one group per distinct passage. Target waveforms are merged when their Danish transcripts are
    near-identical (word-set Jaccard >= 0.8), which joins e.g. the original and the 'woa' copy of the same passage."""
    asr = json.load(open(os.path.join(DTU_FEAT, "asr_words_whisper_large_v3_da.json")))["streams"]
    shas = sorted(asr)
    words = {h: set(_norm_text(asr[h]["text"])) for h in shas}
    parent = {h: h for h in shas}

    def find(h):
        while parent[h] != h:
            parent[h] = parent[parent[h]]; h = parent[h]
        return h
    for i, a in enumerate(shas):
        for b in shas[i + 1:]:
            wa, wb = words[a], words[b]
            if wa and wb and len(wa & wb) / len(wa | wb) >= 0.8:
                parent[find(a)] = find(b)
    groups = {}
    for h in shas:
        groups.setdefault(find(h), []).append(h)
    gl = sorted(groups.values(), key=lambda g: sorted(g)[0])
    rng = np.random.default_rng(20261005)
    order = rng.permutation(len(gl))
    half = {int(i): (0 if k < len(gl) / 2 else 1) for k, i in enumerate(order)}
    content = {}
    for gi, g in enumerate(gl):
        es = (gi % 5 == 0)  # every fifth group of a half is the early-stopping part of that half
        for h in g:
            content[h] = {"group": gi, "half": half[gi], "early_stop": bool(es)}
    os.makedirs(OUT_DTU, exist_ok=True)
    meta = {"n_target_waveforms": len(shas), "n_groups": len(gl), "group_sizes": sorted([len(g) for g in gl], reverse=True)[:10],
            "rule": "Jaccard(word sets) >= 0.8 merged; halves by seeded permutation of groups; every 5th group = early stop",
            "content": content}
    json.dump(meta, open(os.path.join(OUT_DTU, "content_groups.json"), "w"), indent=1)
    print({k: v for k, v in meta.items() if k != "content"})


def run_dtu_audio():
    """Whisper-extractor log-mel (128 bins, 100 Hz) and broadband Hilbert envelope (128 Hz) of every unique waveform."""
    import h5py
    from scipy.signal import hilbert
    from transformers import WhisperFeatureExtractor
    from auditory_c3.features import MODELS, _snapshot, _windows
    from auditory_c3.features_dtu import _mono16k
    out = os.path.join(OUT_DTU, "audio_local.h5")
    if os.path.exists(out + ".done.json"):
        print("skip", out); return
    inv = json.load(open(os.path.join(DTU_FEAT, "inventory.json")))
    paths = {}
    for r in inv:
        if r.get("sha") and r["path"] and r["sha"] not in paths:
            paths[r["sha"]] = r["path"]
    fe = WhisperFeatureExtractor.from_pretrained(_snapshot(MODELS["whisper"])[0])
    os.makedirs(OUT_DTU, exist_ok=True)
    with h5py.File(out + ".tmp", "w") as o:
        for h, p in sorted(paths.items()):
            x, h2 = _mono16k(p)
            assert h2 == h
            n100 = int(np.ceil(len(x) / 16000 * 100))
            mel = np.zeros((128, n100), np.float32)
            for s, e, lo, hi in _windows(len(x)):
                f = fe(x[s:e], sampling_rate=16000, return_tensors="np").input_features[0]
                a, b, A = int(round((lo - s) / 160)), int(round((hi - s) / 160)), int(round(lo / 160))
                b = min(b, a + n100 - A); mel[:, A:A + (b - a)] = f[:, a:b]
            env = np.abs(hilbert(x.astype(np.float64)))
            env128 = _rs(env, 1, 125)  # 16000 -> 128 Hz (anti-aliased)
            o.create_dataset(f"{h}/logmel", data=mel); o.create_dataset(f"{h}/env", data=env128.astype(np.float32))
    os.replace(out + ".tmp", out)
    json.dump({"n": len(paths), "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}, open(out + ".done.json", "w"))
    print("done", out, len(paths))


def run_dtu():
    import h5py
    cg = json.load(open(os.path.join(OUT_DTU, "content_groups.json")))["content"]
    inv = json.load(open(os.path.join(DTU_FEAT, "inventory.json")))
    # training-side waveforms of a fold = targets of the training half (+ maskers presented with them)
    trial_target = {}
    for r in inv:
        if r["kind"] == "target" and r.get("sha"):
            trial_target[(r["file"], r["trial"])] = r["sha"]
    fh = h5py.File(os.path.join(DTU_FEAT, "whisper_L01_L02_L27.h5"), "r")
    fa = h5py.File(os.path.join(OUT_DTU, "audio_local.h5"), "r")
    all_sha = sorted(set(fh.keys()) & set(fa.keys()))
    for cf in (0, 1):
        out = os.path.join(OUT_DTU, f"dtu_cf{cf}.h5")
        if os.path.exists(out + ".done.json"):
            print("skip", out); continue
        train = set()
        for r in inv:
            if not r.get("sha"):
                continue
            t = trial_target.get((r["file"], r["trial"]))
            if t is not None and t in cg and cg[t]["half"] != cf:  # content_fold cf tests half cf, trains on the other half
                train.add(r["sha"])
        tr = sorted(train & set(all_sha))
        ac = np.concatenate([0.5 * (fh[h]["layer_01"][()].astype(np.float64) + fh[h]["layer_02"][()].astype(np.float64)) for h in tr])
        lz = np.concatenate([fh[h]["layer_27"][()].astype(np.float64) for h in tr])
        mel = np.concatenate([fa[h]["logmel"][()].T.astype(np.float64) for h in tr])
        P = {"Ac": _pca(ac), "Lz": _pca(lz, zscore=True), "Mel": _pca(mel)}
        del ac, lz, mel
        meta = {"cf": cf, "n_fit_waveforms": len(tr), "evr": {k: v["evr"] for k, v in P.items()}}
        with h5py.File(out + ".tmp", "w") as o:
            for h in all_sha:
                g = fh[h]
                ac = _rs(_apply(P["Ac"], 0.5 * (g["layer_01"][()].astype(np.float64) + g["layer_02"][()].astype(np.float64))).T, 64, 25)
                lz = _rs(_apply(P["Lz"], g["layer_27"][()].astype(np.float64)).T, 64, 25)
                mel = _rs(_apply(P["Mel"], fa[h]["logmel"][()].T.astype(np.float64)).T, 32, 25)
                env = fa[h]["env"][()].astype(np.float64)
                n = min(ac.shape[1], lz.shape[1], mel.shape[1], len(env))
                for name, arr in (("Ac", ac[:, :n]), ("Lz", lz[:, :n]), ("Local", np.vstack([mel[:, :n], env[None, :n]]))):
                    o.create_dataset(f"{h}/{name}", data=_bp(arr).astype(np.float32))
            o.attrs["meta"] = json.dumps(meta)
        os.replace(out + ".tmp", out)
        json.dump({**meta, "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}, open(out + ".done.json", "w"), indent=1)
        print("done", out, meta, flush=True)


if __name__ == "__main__":
    {"fau": run_fau, "dtu_content": run_dtu_content, "dtu_audio": run_dtu_audio, "dtu": run_dtu}[sys.argv[1]]()
