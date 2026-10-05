"""P0 per-layer PCA of the cached speech-model representations (03 §3.3: k = 5, sensitivity 3 and 8; fitted on the
stimulus side only, never on EEG).

For each model and layer: PCA (centred covariance eigendecomposition) is fitted on all non-silent stimulus frames,
each distinct waveform counted once (deduplicated by wav sha256, so audio reused across codes is not weighted twice).
The leading 8 components are stored (k = 3 and 5 are their nested prefixes), projected per code x stream and resampled
from 50 Hz to the 128 Hz EEG grid (resample_poly 64/25) so that sample k is time k/128 s from stimulus onset, the same
origin as the EEG trial. No band-pass is applied here (the stimulus-side filter is a G1 decision).

Usage: python -m auditory_c3.pca <whisper|xlsr>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

SRC = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
FILES = {"whisper": "whisper_large_v3_hidden.h5", "xlsr": "xlsr300m_hidden.h5"}
K = 8
FS_OUT = 128


def run(model):
    import h5py
    from scipy.signal import resample_poly
    shallow = model == "whisper_shallow"  # MEASUREMENT_AMENDMENT_001 §4: Ac = PCA of mean(layer_01, layer_02)
    mel = model == "mel"  # DECISION_001 §6 control: log-mel (Whisper input, 128 bins, 100 Hz) replaces Ac
    z27 = model == "whisper_z27"  # POST_G1_CHANGELOG 2026-10-05 L27 diagnostic: coordinates z-scored before PCA (sensitivity)
    src = os.path.join(SRC, "whisper_logmel128.h5" if mel else FILES["whisper" if (shallow or z27) else model])
    if not os.path.exists(src + ".done.json"):
        raise SystemExit(f"{src} not done")
    out = os.path.join(SRC, f"pca_k{K}_128hz_{model}.h5")
    if os.path.exists(out + ".done.json"):
        print("skip", out); return
    tmp = out + ".tmp"
    with h5py.File(src, "r") as f, h5py.File(tmp, "w") as o:
        streams = [(c, s) for c in sorted(f.keys()) for s in sorted(f[c].keys()) if not f[c][s].attrs["silent"]]
        if mel:  # the log-mel file only holds non-silent streams' data; silence flags are on the groups
            streams = [(c, s) for c, s in streams if "logmel" in f[c][s]]
        seen, uniq = set(), []
        for c, s in streams:
            h = f[c][s].attrs["wav_sha256"]
            if h not in seen:
                seen.add(h); uniq.append((c, s))
        layers = sorted(k for k in f[streams[0][0]][streams[0][1]].keys() if k.startswith("layer_"))
        get = (lambda c, s_, layer: f[c][s_][layer][()].astype(np.float64))
        if mel:
            layers = ["logmel"]
            get = (lambda c, s_, layer: f[c][s_]["logmel"][()].T.astype(np.float64))
        if z27:
            layers = ["layer_27"]
        if shallow:
            layers = ["shallow_01_02"]
            get = (lambda c, s_, layer: 0.5 * (f[c][s_]["layer_01"][()].astype(np.float64) + f[c][s_]["layer_02"][()].astype(np.float64)))
        o.attrs.update(model=f.attrs["model"], revision=f.attrs["revision"], k=K, fs=FS_OUT, n_streams=len(streams),
                       n_unique_waveforms=len(uniq), fit="centred covariance eigendecomposition on unique non-silent waveforms",
                       resample="scipy.signal.resample_poly(up=64, down=25) from 50 Hz", source_sha256=json.load(open(src + ".done.json"))["sha256"])
        summary = {}
        for li, layer in enumerate(layers):
            X = np.concatenate([get(c, s, layer) for c, s in uniq], axis=0)
            mu = X.mean(0)
            sd = X.std(0) if z27 else np.ones(X.shape[1])
            sd[sd == 0] = 1.0
            C = np.cov((X - mu) / sd, rowvar=False)
            w, V = np.linalg.eigh(C)
            order = np.argsort(w)[::-1]
            w, V = w[order], V[:, order]
            # fix the sign of each component deterministically (largest-|loading| coordinate positive)
            sgn = np.sign(V[np.argmax(np.abs(V), axis=0), np.arange(V.shape[1])]); V = V * sgn
            evr = w / w.sum()
            g = o.create_group(f"_pca/{layer}")
            g.create_dataset("mean", data=mu.astype(np.float32)); g.create_dataset("components", data=V[:, :K].T.astype(np.float32))
            g.create_dataset("scale", data=sd.astype(np.float32))
            g.create_dataset("explained_variance_ratio", data=evr[:K])
            for c, s in streams:
                Z = ((get(c, s, layer) - mu) / sd) @ V[:, :K]
                Z128 = resample_poly(Z, 32, 25, axis=0) if mel else resample_poly(Z, 64, 25, axis=0)  # 100 Hz or 50 Hz -> 128 Hz
                o.create_dataset(f"{c}/{s}/{layer}", data=Z128.T.astype(np.float32))
            summary[layer] = {"n_frames_fit": int(X.shape[0]), "evr_k3": float(evr[:3].sum()), "evr_k5": float(evr[:5].sum()), "evr_k8": float(evr[:8].sum())}
            print(model, layer, summary[layer], flush=True)
        o.attrs["summary"] = json.dumps(summary)
    os.replace(tmp, out)
    meta = {"model": model, "summary": summary, "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}
    json.dump(meta, open(out + ".done.json", "w"), indent=1)
    print("done", out, meta["sha256"][:16])


if __name__ == "__main__":
    run(sys.argv[1])
