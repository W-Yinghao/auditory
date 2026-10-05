"""DTU ds-eeg-snhl stimulus features (D1 audio received 2026-10-05). Same frozen extractors as FAU/TUD
(FEATURE_MANIFEST.md): Whisper large-v3 encoder (revision 06f233fe), 30 s windows / 20 s hop, centre-kept.
Only the layers the frozen measurement needs are stored: layer_01, layer_02 (Ac = PCA of their mean) and layer_27
(L, frozen at G1 on FAU/TUD TH; never re-selected here).

Audio = the ORIGINAL (unequalised) speech for every participant, as for FAU/TUD where device users heard their own
devices but features come from the original stimuli: HI listeners -> the 'woa' files, NH listeners -> their files
(NH heard unequalised audio). Stereo (binaural) files are averaged to mono. Identical waveforms (sha256 of the mono
int16 signal) are encoded once. Time base: target wav sample 0 = trial onset; masker wav sample 0 = masker onset,
so masker features are placed at round(masker_onset_rel_s * 128) on the 128 Hz trial grid.
PCA (k = 8; Ac and L27) is fitted on the unique DTU waveforms only, then resampled 50 -> 128 Hz.

Usage: python -m auditory_c3.features_dtu <encode|pca>
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys

import numpy as np

ROOT = "/projects/EEG-foundation-model/auditory_public"
AUD = os.path.join(ROOT, "dtu_snhl", "audio_drcmr")
PRE = os.path.join(ROOT, "derived", "c3_preproc_v1", "dtu_snhl")
OUT = os.path.join(ROOT, "derived", "c3_features_v1", "dtu")
LAYERS = (1, 2, 27)
SR = 16000


def _audio_path(sub, stim_rel, kind, hi):
    """stim_rel like 'sub001/target/t001.wav'."""
    rel = stim_rel if kind == "target" else stim_rel.replace("/target/t", "/masker/m")
    if hi:
        cand = glob.glob(os.path.join(AUD, "stimuli-woa", "*", rel.replace(".wav", "woa.wav")))
    else:
        cand = glob.glob(os.path.join(AUD, "stimuli", "*", rel))
    return cand[0] if cand else None


def inventory():
    import h5py
    import pandas as pd
    part = pd.read_csv(os.path.join(ROOT, "dtu_snhl", "ds-eeg-snhl", "ds-eeg-snhl", "participants.tsv"), sep="\t")
    hi = dict(zip(part.participant_id, part.hearing_status == "hi"))
    rows = []
    for p in sorted(glob.glob(os.path.join(PRE, "*.h5"))):
        tag = os.path.basename(p)[:-3]; sub = tag.split("_")[0]
        with h5py.File(p, "r") as f:
            for k in sorted(f.keys()):
                g = f[k]
                for kind in ("target", "masker"):
                    if kind == "masker" and str(g.attrs["talkers"]) != "twotalker":
                        continue
                    path = _audio_path(sub, str(g.attrs["stim_file"]), kind, hi[sub])
                    off = 0.0 if kind == "target" else float(g.attrs["masker_onset_rel_s"])
                    rows.append({"file": tag, "trial": k, "kind": kind, "path": path, "offset_s": off, "hi": bool(hi[sub])})
    return rows


def _mono16k(path):
    import soundfile as sf
    from scipy.signal import resample_poly
    x, sr = sf.read(path, dtype="float64", always_2d=True)
    m = x.mean(1)
    h = hashlib.sha256(np.round(m * 32767).astype(np.int16).tobytes()).hexdigest()
    assert sr == 44100, sr
    return resample_poly(m, 160, 441).astype(np.float32), h


def run_encode():
    import h5py
    import torch
    from transformers import WhisperFeatureExtractor, WhisperModel
    from .features import MODELS, _snapshot, _windows
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "whisper_L01_L02_L27.h5")
    if os.path.exists(out + ".done.json"):
        print("skip", out); return
    rows = inventory()
    missing = [r for r in rows if r["path"] is None]
    snap, rev = _snapshot(MODELS["whisper"])
    fe = WhisperFeatureExtractor.from_pretrained(snap)
    enc = WhisperModel.from_pretrained(snap, dtype=torch.float16).encoder.cuda().eval()
    tmp = out + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    seen = {}
    with h5py.File(tmp, "w") as f:
        for r in rows:
            if r["path"] is None:
                continue
            x, h = _mono16k(r["path"])
            r["sha"] = h
            if h in seen:
                continue
            seen[h] = r["path"]
            n_frames = int(np.ceil(len(x) / SR * 50))
            hs = np.zeros((len(LAYERS), n_frames, 1280), np.float16)
            for s, e, lo, hi_ in _windows(len(x)):
                feats = fe(x[s:e], sampling_rate=SR, return_tensors="pt").input_features
                with torch.no_grad():
                    H = enc(feats.half().cuda(), output_hidden_states=True).hidden_states
                a, b = int(round((lo - s) / SR * 50)), int(round((hi_ - s) / SR * 50)); A = int(round(lo / SR * 50))
                b = min(b, a + n_frames - A)
                for li, L in enumerate(LAYERS):
                    hs[li, A:A + (b - a)] = H[L][0, a:b].float().cpu().numpy()
            g = f.create_group(h)
            for li, L in enumerate(LAYERS):
                g.create_dataset(f"layer_{L:02d}", data=hs[li], compression="lzf")
            g.attrs.update(source=os.path.relpath(r["path"], ROOT), seconds=len(x) / SR)
        f.attrs.update(model=MODELS["whisper"], revision=rev, layers=list(LAYERS), windows="30s/20s centre-kept", audio="original speech, stereo->mono")
    os.replace(tmp, out)
    json.dump([{k: v for k, v in r.items()} for r in rows], open(os.path.join(OUT, "inventory.json"), "w"), indent=1)
    meta = {"model": MODELS["whisper"], "revision": rev, "n_rows": len(rows), "n_unique": len(seen), "n_missing_audio": len(missing),
            "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}
    json.dump(meta, open(out + ".done.json", "w"), indent=1)
    print(json.dumps(meta))


def run_pca():
    import h5py
    from scipy.signal import resample_poly
    src = os.path.join(OUT, "whisper_L01_L02_L27.h5")
    out = os.path.join(OUT, "pca_k8_128hz_dtu.h5")
    tmp = out + ".tmp"
    with h5py.File(src, "r") as f, h5py.File(tmp, "w") as o:
        keys = sorted(f.keys())
        summ = {}
        for name, get in (("shallow_01_02", lambda g: 0.5 * (g["layer_01"][()].astype(np.float64) + g["layer_02"][()].astype(np.float64))),
                          ("layer_27", lambda g: g["layer_27"][()].astype(np.float64))):
            X = np.concatenate([get(f[k]) for k in keys]); mu = X.mean(0)
            w, V = np.linalg.eigh(np.cov(X - mu, rowvar=False)); order = np.argsort(w)[::-1]; w, V = w[order], V[:, order]
            V = V * np.sign(V[np.argmax(np.abs(V), axis=0), np.arange(V.shape[1])])
            summ[name] = {"evr_k5": float(w[:5].sum() / w.sum()), "evr_k8": float(w[:8].sum() / w.sum()), "n_frames": int(len(X))}
            for k in keys:
                Z = (get(f[k]) - mu) @ V[:, :8]
                o.create_dataset(f"{k}/{name}", data=resample_poly(Z, 64, 25, axis=0).T.astype(np.float32))
        o.attrs["summary"] = json.dumps(summ)
    os.replace(tmp, out)
    json.dump({"summary": summ, "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}, open(out + ".done.json", "w"), indent=1)
    print(json.dumps(summ))


if __name__ == "__main__":
    {"encode": run_encode, "pca": run_pca}[sys.argv[1]]()
