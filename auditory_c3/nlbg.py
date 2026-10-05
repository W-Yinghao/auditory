"""Non-linear acoustic background (NLBG; POST_G1_CHANGELOG 2026-10-05 ~14:40), stimulus side only, no EEG.

For each of the 32 unique FAU/TUD speech streams, L_BG = m0(Ac) + MLP([m0, Ac]) is fitted on the other 31 streams
(leave-one-stream-out; 3 of the 31 held out for early stopping) and applied to the held-out stream, for two targets:
the frozen L27 PCA-5 and Lz (z-scored-coordinate L27 PCA-5). Ac = Whisper shallow PCA-5. Everything 1-8 Hz.

Usage: python -m auditory_c3.nlbg
Output: <FEAT>/pca_k8_128hz_bg_crossfit.h5 ({code}/{stream}/bg_l27, bg_z27; 5 x n, 128 Hz) + .done.json (summary)
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import torch
import torch.nn as nn

from .c3dl import pl

FEAT = pl.FEAT
OUT = os.path.join(FEAT, "pca_k8_128hz_bg_crossfit.h5")
TARGETS = {"bg_l27": ("pca_k8_128hz_whisper.h5", "layer_27"), "bg_z27": ("pca_k8_128hz_whisper_z27.h5", "layer_27")}
MAX_EP, PATIENCE, BS = 300, 30, 8192


def load_all_streams(target_file, target_key):
    import h5py
    out = {}
    with h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r") as fa, h5py.File(os.path.join(FEAT, target_file), "r") as fl:
        for c in sorted(k for k in fl.keys() if not k.startswith("_")):
            for s in sorted(fl[c].keys()):
                Ac = pl._bp(fa[f"{c}/{s}/shallow_01_02"][()][:pl.D]); L = pl._bp(fl[f"{c}/{s}/{target_key}"][()][:pl.D])
                n = min(Ac.shape[1], L.shape[1])
                out[f"{c}/{s}"] = {"Ac": Ac[:, :n].astype(np.float32), "L": L[:, :n].astype(np.float32), "story": c[1], "part": c[2], "n": n}
    return out


class BGNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2 * pl.D, 64), nn.GELU(), nn.Linear(64, pl.D))
        nn.init.zeros_(self.net[2].weight); nn.init.zeros_(self.net[2].bias)

    def forward(self, x):
        return self.net(x)


def _rows(streams, m0, keys, norm):
    """Valid time points of the given streams: inputs [m0, Ac] standardised, m0, L."""
    Xs, M, Y = [], [], []
    for k in keys:
        s = streams[k]; a, b = pl.GUARD, s["n"] - pl.GUARD
        mz = (m0[k][:, a:b] - norm["m0"][0][:, None]) / norm["m0"][1][:, None]
        az = (s["Ac"][:, a:b] - norm["Ac"][0][:, None]) / norm["Ac"][1][:, None]
        Xs.append(np.r_[mz, az].T); M.append(m0[k][:, a:b].T); Y.append(s["L"][:, a:b].T)
    return [torch.tensor(np.concatenate(v), dtype=torch.float32) for v in (Xs, M, Y)]


def fit_predict(streams, held, seed=20261010):
    dev = pl.device()
    train = [k for k in streams if k != held]
    rng = np.random.default_rng(seed)
    es_keys = [train[i] for i in rng.permutation(len(train))[:3]]
    fit_keys = [k for k in train if k not in es_keys]
    m0, W, info, norm = pl.fit_m0(streams, train)
    Wt = torch.tensor(W, device=dev)
    Xf, Mf, Yf = (t.to(dev) for t in _rows(streams, m0, fit_keys, norm))
    Xe, Me, Ye = (t.to(dev) for t in _rows(streams, m0, es_keys, norm))
    torch.manual_seed(seed)
    net = BGNet().to(dev); opt = torch.optim.AdamW(net.parameters(), lr=1e-3, weight_decay=1e-4)
    loss = lambda X, M, Y: ((Y - M - net(X)) @ Wt.T).pow(2).sum(1).mean() / 2
    best, bad, ep_best = np.inf, 0, -1
    g = torch.Generator(device="cpu").manual_seed(seed)
    for ep in range(MAX_EP):
        net.train()
        for idx in torch.randperm(len(Xf), generator=g).split(BS):
            idx = idx.to(dev); opt.zero_grad(); l = loss(Xf[idx], Mf[idx], Yf[idx]); l.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            le = float(loss(Xe, Me, Ye))
        if le < best - 1e-6:
            best, bad, ep_best, state = le, 0, ep, {k: v.clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(state); net.eval()
    s = streams[held]
    full = np.zeros_like(s["L"])
    lo, hi = 128, s["n"] - 128
    mz = (m0[held][:, lo:hi] - norm["m0"][0][:, None]) / norm["m0"][1][:, None]
    az = (s["Ac"][:, lo:hi] - norm["Ac"][0][:, None]) / norm["Ac"][1][:, None]
    with torch.no_grad():
        full[:, lo:hi] = m0[held][:, lo:hi] + net(torch.tensor(np.r_[mz, az].T, dtype=torch.float32, device=dev)).cpu().numpy().T
    a, b = pl.GUARD, s["n"] - pl.GUARD
    r0 = s["L"][:, a:b] - m0[held][:, a:b]; r1 = s["L"][:, a:b] - full[:, a:b]
    e = float(((W @ r0) ** 2).sum(0).mean() - ((W @ r1) ** 2).sum(0).mean()) / (2 * np.log(2))
    r2 = 1 - (r1 ** 2).sum(1) / ((s["L"][:, a:b] - s["L"][:, a:b].mean(1, keepdims=True)) ** 2).sum(1)
    r2_m0 = 1 - (r0 ** 2).sum(1) / ((s["L"][:, a:b] - s["L"][:, a:b].mean(1, keepdims=True)) ** 2).sum(1)
    return full, {"held": held, "best_epoch": ep_best, "es_loss": best, "gain_bits_per_sample_vs_m0": e,
                  "r2_bg": r2.tolist(), "r2_m0": r2_m0.tolist(), "m0_alpha": info["alpha"]}


def fit_part(target_name, i0, i1, max_ep=3000, patience=100):
    """NLBG-conv: fit streams [i0, i1) (sorted order) of one target with a larger budget; writes npz per stream."""
    global MAX_EP, PATIENCE
    MAX_EP, PATIENCE = max_ep, patience
    d = os.path.join(FEAT, "bg_crossfit_conv_parts"); os.makedirs(d, exist_ok=True)
    tf, tk = TARGETS[target_name]
    streams = load_all_streams(tf, tk)
    for k in sorted(streams)[i0:i1]:
        p = os.path.join(d, f"{target_name}__{k.replace('/', '_')}.npz")
        if os.path.exists(p):
            continue
        full, info = fit_predict(streams, k)
        np.savez(p + ".tmp.npz", full=full.astype(np.float32), info=json.dumps(info, default=float))
        os.replace(p + ".tmp.npz", p)
        print(target_name, k, info["best_epoch"], round(info["gain_bits_per_sample_vs_m0"], 4), flush=True)


def merge_conv():
    import h5py
    d = os.path.join(FEAT, "bg_crossfit_conv_parts"); out = os.path.join(FEAT, "pca_k8_128hz_bg_crossfit_conv.h5")
    files = sorted(os.listdir(d)); assert len(files) == 64, len(files)
    summ = {}
    with h5py.File(out + ".tmp", "w") as o:
        for f in files:
            name, key = f[:-4].split("__"); code, stream = key.split("_", 1)
            z = np.load(os.path.join(d, f))
            o.create_dataset(f"{code}/{stream}/{name}", data=z["full"])
            summ.setdefault(name, []).append(json.loads(str(z["info"])))
        o.attrs["design"] = "as pca_k8_128hz_bg_crossfit.h5 but max 3000 epochs, patience 100"
    os.replace(out + ".tmp", out)
    meta = {"summary": {n: {"mean_gain_bits_per_sample": float(np.mean([x["gain_bits_per_sample_vs_m0"] for x in v])),
                            "min_gain": float(np.min([x["gain_bits_per_sample_vs_m0"] for x in v])),
                            "best_epoch_max": int(max(x["best_epoch"] for x in v)), "per_stream": v} for n, v in summ.items()},
            "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest()}
    json.dump(meta, open(out + ".done.json", "w"), indent=1)
    print("done", out, {n: (m["mean_gain_bits_per_sample"], m["best_epoch_max"]) for n, m in meta["summary"].items()})


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "fit_part":
        fit_part(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])); return
    if len(sys.argv) > 1 and sys.argv[1] == "merge_conv":
        merge_conv(); return
    import h5py
    if os.path.exists(OUT + ".done.json"):
        print("skip", OUT); return
    tmp = OUT + ".tmp"
    summ = {}
    with h5py.File(tmp, "w") as o:
        for name, (tf, tk) in TARGETS.items():
            streams = load_all_streams(tf, tk)
            summ[name] = []
            for k in sorted(streams):
                full, info = fit_predict(streams, k)
                o.create_dataset(f"{k}/{name}", data=full.astype(np.float32))
                summ[name].append(info)
                print(name, k, {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in info.items() if kk in ("best_epoch", "gain_bits_per_sample_vs_m0")}, flush=True)
        o.attrs["design"] = "leave-one-stream-out over 32 unique streams; m0 ridge (Ac lags +-1 s) + MLP([m0, Ac]) 10-64-5; ES on 3 training streams"
    os.replace(tmp, OUT)
    meta = {"summary": {n: {"mean_gain_bits_per_sample": float(np.mean([x["gain_bits_per_sample_vs_m0"] for x in v])),
                            "min_gain": float(np.min([x["gain_bits_per_sample_vs_m0"] for x in v])),
                            "per_stream": v} for n, v in summ.items()},
            "sha256": hashlib.sha256(open(OUT, "rb").read()).hexdigest()}
    json.dump(meta, open(OUT + ".done.json", "w"), indent=1)
    print("done", OUT, {n: m["mean_gain_bits_per_sample"] for n, m in meta["summary"].items()})


if __name__ == "__main__":
    main()
