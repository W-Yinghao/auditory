"""Stimulus-side word table for the word-level analysis (docs/auditory_c3/WORDLEVEL_REG_v1.md). No EEG.

Words = single-speaker attended streams (codes 1xx) of FAU/TUD, word boundaries from the frozen Whisper ASR (as in the
GPT-2 surprisal file). A word is kept when its EEG epoch (-200..800 ms around onset) lies inside the analysis-valid
range [GUARD, n - GUARD] of the trial.

Background features C (stimulus side, no context model):
  duration, log duration, gap since previous word offset; Whisper shallow PCA-5 (Ac) means over the word's three
  equal thirds (15); attended envelope mean/max and onset-envelope mean/max over the word (4); characters, GPT-2
  token count, log corpus frequency of the lower-cased form over all 32 streams; sentence-final, clause-final,
  sentence-initial flags and position in sentence (/30, capped); previous word's duration, Ac mean (5), characters,
  token count, log frequency, sentence-final flag.
Targets: Y_L = PCA-16 of the GPT-2 layer-l word states (PCA fitted on all kept words, stimulus side); Y_S = surprisal.
"""
from __future__ import annotations

import collections
import json
import os
import re

import numpy as np

FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
ENV = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/fau_tud/stimulus_env_128.h5"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATES = os.path.join(REPO, "private", "auditory_c3", "wordlevel", "gpt2_word_states.h5")
FS, PRE, POST, GUARD = 128, 26, 102, 314  # epoch = onset-26 .. onset+101 (128 samples, -203..789 ms)
K_L = 16


def _norm_word(w):
    return re.sub(r"[^\wäöüßÄÖÜ]", "", w).lower()


def build(layer, k=K_L, states_path=STATES):
    import h5py
    sur = json.load(open(os.path.join(FEAT, "gpt2_german_word_surprisal.json")))["streams"]
    freq = collections.Counter(_norm_word(w["w"]) for ws in sur.values() for w in ws)
    total = sum(freq.values())
    rows = []
    with h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r") as fa, h5py.File(ENV, "r") as fe, \
            h5py.File(states_path, "r") as fs_:
        for code in sorted(c for c in fa.keys() if c.startswith("1")):
            key = f"{code}/attended"
            words = sur[key]
            Ac = fa[f"{key}/shallow_01_02"][()][:5].astype(np.float64)
            env = np.nan_to_num(fe[f"{code}/attended_env/raw"][()].astype(np.float64))
            onv = np.nan_to_num(fe[f"{code}/attended_onset_env/raw"][()].astype(np.float64))
            H = fs_[f"{key}/layer_{layer:02d}"][()].astype(np.float32); ntok = fs_[f"{key}/n_tokens"][()]
            n = Ac.shape[1]
            sent_start = True; pos = 0
            prev = None
            for i, w in enumerate(words):
                o = int(round(w["t0"] * FS)); e = max(o + 3, int(round(w["t1"] * FS)))
                e = min(e, n - 1)
                txt = w["w"]; sf = bool(re.search(r"[.!?]\W*$", txt)); cf = bool(re.search(r"[,;:]\W*$", txt))
                thirds = np.array_split(np.arange(o, max(e, o + 3)), 3)
                acm = [Ac[:, t].mean(1) for t in thirds]
                nw = _norm_word(txt)
                feat = {"dur": w["t1"] - w["t0"], "gap": (w["t0"] - words[i - 1]["t1"]) if i else 0.0,
                        "ac": np.concatenate(acm), "acmean": Ac[:, o:max(e, o + 1)].mean(1),
                        "env": [env[o:e + 1].mean(), env[o:e + 1].max(), onv[o:e + 1].mean(), onv[o:e + 1].max()],
                        "nchar": len(nw), "ntok": int(ntok[i]), "logf": np.log(freq[nw] / total + 1e-9),
                        "sf": float(sf), "cf": float(cf), "si": float(sent_start), "pos": min(pos, 30) / 30.0}
                pv = prev or {"dur": 0.0, "acmean": np.zeros(5), "nchar": 0, "ntok": 0, "logf": np.log(1e-9), "sf": 1.0}
                C = np.r_[feat["dur"], np.log(max(feat["dur"], 0.01)), feat["gap"], feat["ac"], feat["env"], feat["nchar"], feat["ntok"],
                          feat["logf"], feat["sf"], feat["cf"], feat["si"], feat["pos"],
                          pv["dur"], pv["acmean"], pv["nchar"], pv["ntok"], pv["logf"], pv["sf"]]
                valid = (o - PRE >= GUARD) and (o + POST <= n - GUARD)
                rows.append({"code": code, "story": code[1], "part": code[2], "i": i, "w": txt, "t0": w["t0"], "onset": o,
                             "C": C, "H": H[i], "sur": w["surprisal_bits"], "valid": valid})
                prev = feat
                pos = 0 if sf else pos + 1
                sent_start = sf
    rows = [r for r in rows if r["valid"]]
    H = np.stack([r["H"] for r in rows]).astype(np.float64)
    mu = H.mean(0); U, S, Vt = np.linalg.svd(H - mu, full_matrices=False)
    YL = (H - mu) @ Vt[:k].T
    evr = float((S[:k] ** 2).sum() / (S ** 2).sum())
    tab = {"C": np.stack([r["C"] for r in rows]).astype(np.float32), "YL": YL.astype(np.float32),
           "YS": np.array([[r["sur"]] for r in rows], np.float32)}
    for f_ in ("code", "story", "part", "w"):
        tab[f_] = np.array([r[f_] for r in rows])
    for f_ in ("i", "onset"):
        tab[f_] = np.array([r[f_] for r in rows], int)
    tab["t0"] = np.array([r["t0"] for r in rows], float)
    tab["meta"] = {"layer": layer, "k": k, "pca_evr": evr, "n_words": len(rows), "n_features": int(tab["C"].shape[1])}
    return tab
