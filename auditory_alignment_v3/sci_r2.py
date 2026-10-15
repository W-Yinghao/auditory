"""docs/13 science round 2 (SCI_R2_PREREG.md): one task per dataset x subject fold x content fold, CPU only.
Q1 nested forward models (stimulus features at t - lag -> EEG(t), lags -200..600 ms) and Q2/Q3 the common-ms-grid strict-local raw
readability of the envelope (2-8 Hz band-matched sensitivity for FAU/DTU). Everything from per-group sufficient statistics:
grouped CV (5 participant groups) chooses alpha; per test identity Pearson r from its own statistics. Outputs per-identity values
(private). Usage: python -m auditory_alignment_v3.sci_r2 --dataset fau --subject-fold 0 --content-fold 0"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

from auditory_alignment_v3 import core

OUT = os.path.join(core.OUT, "sci_r2")
GROUP_SEED, N_GROUPS = 20261014, 5
ALPHAS = np.logspace(-3, 4, 8)
FAMS = ("env", "onset", "spec", "flux", "Ac", "Lz")
MODELS = {"M1": ("env",), "M2": ("env", "onset"), "M3": ("env", "onset", "spec"), "M4": ("env", "onset", "spec", "flux"),
          "M5": ("env", "onset", "spec", "flux", "Ac"), "M6": ("env", "onset", "spec", "flux", "Ac", "Lz")}
LAG_GRID_MS = list(range(-200, 561, 20))


def feature_bank(coh, ds):
    """family -> [dims, N] arrays on the stimulus bank (aligned to the EEG via the segments' s0)."""
    st = coh.stim
    if ds == "federici":
        return {"env": np.asarray(st["envelope"], np.float64)[:1]}
    L = np.asarray(st["Local"], np.float64)
    env, spec = L[5:6], L[0:5]
    onset = np.maximum(np.diff(env, axis=1, prepend=env[:, :1]), 0.0)
    flux = np.linalg.norm(np.diff(spec, axis=1, prepend=spec[:, :1]), axis=0, keepdims=True)
    return {"env": env, "onset": onset, "spec": spec, "flux": flux, "Ac": np.asarray(st["Ac"], np.float64), "Lz": np.asarray(st["Lz"], np.float64)}


class Stats:
    """sufficient statistics of (X, Y) rows: n, Sx, Sy, Sxx, Sxy, Syy (per output column)."""

    def __init__(self, p, q):
        self.n = 0; self.Sx = np.zeros(p); self.Sy = np.zeros(q); self.Sxx = np.zeros((p, p)); self.Sxy = np.zeros((p, q)); self.Syy = np.zeros(q)

    def add(self, X, Y):
        self.n += len(X); self.Sx += X.sum(0); self.Sy += Y.sum(0); self.Sxx += X.T @ X; self.Sxy += X.T @ Y; self.Syy += (Y ** 2).sum(0)

    def __iadd__(self, o):
        self.n += o.n; self.Sx += o.Sx; self.Sy += o.Sy; self.Sxx += o.Sxx; self.Sxy += o.Sxy; self.Syy += o.Syy
        return self

    def sub(self, idx):
        s = Stats(len(idx), len(self.Sy)); s.n = self.n; s.Sx = self.Sx[idx]; s.Sy = self.Sy; s.Sxx = self.Sxx[np.ix_(idx, idx)]; s.Sxy = self.Sxy[idx]; s.Syy = self.Syy
        return s


def fit(S, a):
    mx, my = S.Sx / S.n, S.Sy / S.n
    C = S.Sxx / S.n - np.outer(mx, mx); Cxy = S.Sxy / S.n - np.outer(mx, my)
    tr = np.trace(C) / C.shape[0]
    B = np.linalg.solve(C + a * tr * np.eye(C.shape[0]), Cxy)
    return B, my - mx @ B


def r_of(S, B, b0):
    """mean over outputs of Pearson(X B + b0, Y) from statistics."""
    n = S.n; sp = S.Sx @ B + n * b0; spp = np.einsum("ij,ik,kj->j", B, S.Sxx, B) + 2 * b0 * (S.Sx @ B) + n * b0 ** 2
    spy = np.einsum("ij,ij->j", B, S.Sxy) + b0 * S.Sy
    cov = spy / n - (sp / n) * (S.Sy / n); vp = spp / n - (sp / n) ** 2; vy = S.Syy / n - (S.Sy / n) ** 2
    return float(np.mean(cov / np.sqrt(np.maximum(vp * vy, 1e-24))))


def choose(group_stats, idx=None):
    best = None; curve = []
    for a in ALPHAS:
        rs = []
        for k in range(len(group_stats)):
            tr = Stats(len(group_stats[0].Sx), len(group_stats[0].Sy))
            for j, g in enumerate(group_stats):
                if j != k:
                    tr += g
            te = group_stats[k]
            if idx is not None:
                tr, te = tr.sub(idx), te.sub(idx)
            B, b0 = fit(tr, a); rs.append(r_of(te, B, b0))
        r = float(np.mean(rs)); curve.append({"alpha_rel": float(a), "grouped_cv_r": r})
        if best is None or r > best[0]:
            best = (r, float(a))
    return best[1], curve


def lagged(F, s, t, lags):
    """F [d, N]; s scalar segment s0; t [n] times; lags [m] -> [n, d*m] rows F[:, s + t - lag]."""
    idx = s + t[:, None] - lags[None]
    return F[:, idx].transpose(1, 0, 2).reshape(len(t), -1)


def bandpass_2_8(x, fs):
    from scipy.signal import filtfilt, firwin
    b = firwin(129 if fs == 128 else 101, [2.0, 8.0], pass_zero=False, fs=fs)
    return filtfilt(b, [1.0], x, axis=-1, padtype="odd")


def run_task(ds, sf, cf):
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.train import train_participants
    t0 = time.time()
    coh = load_cohort({"dataset": ds, "content_fold": cf}); fs = coh.fs; seg_len = coh.meta["seg_len"]
    E = np.asarray(coh.eeg, np.float32); C = E.shape[0]  # float32 bank (DTU ~17M samples x 64 ch); slices are cast to float64
    tp = train_participants(coh, {}, sf)
    test_p = sorted({s["p"] for s in coh.segments if s["role"] == "test" and (coh.participants[s["p"]]["fold"] == sf or coh.participants[s["p"]].get("test_only"))})
    assert not set(test_p) & tp
    segs = [s for s in coh.segments if s["kind"] == "ss"]
    train_segs = [s for s in segs if s["p"] in tp and s["role"] in ("fit", "es")]
    test_segs = [s for s in segs if s["p"] in test_p and s["role"] == "test"]
    parts = sorted(tp); perm = np.random.default_rng(GROUP_SEED).permutation(len(parts)); grp = {p: int(perm[i]) % N_GROUPS for i, p in enumerate(parts)}
    res = {"dataset": ds, "subject_fold": sf, "content_fold": cf, "fs": fs, "n_train_participants": len(tp), "n_test_participants": len(test_p),
           "test_ids": [coh.participants[p]["id"] for p in test_p], "test_groups": [coh.participants[p]["group"] for p in test_p], "q1": {}, "q2": {}, "q3": {}}
    # ---------------------------------------------------------------- Q1 nested forward models
    Fb = feature_bank(coh, ds); fams = [f for f in FAMS if f in Fb]
    lmin, lmax = int(round(-0.2 * fs)), int(round(0.6 * fs)); lags = np.arange(lmin, lmax + 1)
    t_all = np.arange(lmax, seg_len + lmin)
    mu = {f: np.concatenate([Fb[f][:, s["s0"] + t_all] for s in train_segs[::5]], 1).mean(1, keepdims=True) for f in fams}
    sd = {f: np.concatenate([Fb[f][:, s["s0"] + t_all] for s in train_segs[::5]], 1).std(1, keepdims=True) + 1e-8 for f in fams}
    Fz = {f: (Fb[f] - mu[f]) / sd[f] for f in fams}
    cols = {}; off = 0
    for f in fams:
        cols[f] = np.arange(off, off + Fz[f].shape[0] * len(lags)); off += Fz[f].shape[0] * len(lags)
    G = [Stats(off, C) for _ in range(N_GROUPS)]; T = {p: Stats(off, C) for p in test_p}
    for s in train_segs:
        t = t_all[::2]; X = np.concatenate([lagged(Fz[f], s["s0"], t, lags) for f in fams], 1); G[grp[s["p"]]].add(X, E[:, s["e0"] + t].T.astype(np.float64))
    for s in test_segs:
        X = np.concatenate([lagged(Fz[f], s["s0"], t_all, lags) for f in fams], 1); T[s["p"]].add(X, E[:, s["e0"] + t_all].T.astype(np.float64))
    full = Stats(off, C)
    for g in G:
        full += g
    for m, fs_ in MODELS.items():
        if not all(f in fams for f in fs_):
            continue
        idx = np.concatenate([cols[f] for f in fs_])
        a, curve = choose(G, idx); B, b0 = fit(full.sub(idx), a)
        res["q1"][m] = {"alpha_rel": a, "cv_curve": curve, "r": [r_of(T[p].sub(idx), B, b0) for p in test_p], "n_regressors": int(len(idx))}
    res["q1_meta"] = {"lags_samples": [int(lmin), int(lmax)], "families": fams, "time_points_per_segment": int(len(t_all))}
    # ---------------------------------------------------------------- Q2 / Q3 common-ms-grid raw readability of the envelope
    env = Fz["env"][0]; w = 5 if fs == 128 else 4
    variants = [("q2", E)]
    if ds != "federici":
        variants.append(("q3", None))
    filt = {}
    for key, Ebank in variants:
        if key == "q3" and not filt:
            filt = {s["e0"]: bandpass_2_8(E[:, s["e0"]:s["e0"] + seg_len].astype(np.float64), fs) for s in train_segs + test_segs}
        for L in LAG_GRID_MS:
            a0 = int(round(L * fs / 1000.0)); lo, hi = max(0, -a0), seg_len - max(0, a0 + w)
            t = np.arange(lo, hi)
            Gs = [Stats(C * w, 1) for _ in range(N_GROUPS)]; Ts = {p: Stats(C * w, 1) for p in test_p}
            for s, is_test in [(s, False) for s in train_segs] + [(s, True) for s in test_segs]:
                tt = t if is_test else t[::2]
                seg = E[:, s["e0"]:s["e0"] + seg_len].astype(np.float64) if key == "q2" else filt[s["e0"]]
                idx = tt[:, None] + a0 + np.arange(w)[None]
                X = seg[:, idx].transpose(1, 0, 2).reshape(len(tt), -1); y = env[s["s0"] + tt][:, None]
                (Ts[s["p"]] if is_test else Gs[grp[s["p"]]]).add(X, y)
            fl = Stats(C * w, 1)
            for g in Gs:
                fl += g
            a, _ = choose(Gs); B, b0 = fit(fl, a)
            res[key][str(L)] = {"alpha_rel": a, "r": [r_of(Ts[p], B, b0) for p in test_p]}
    res["q2_meta"] = {"lag_grid_ms": LAG_GRID_MS, "window_samples": w, "window_ms": 1000.0 * w / fs, "target": "envelope (z-scored)"}
    res["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.join(OUT, "tasks"), mode=0o700, exist_ok=True)
    p = os.path.join(OUT, "tasks", f"{ds}_sf{sf}_cf{cf}.json"); json.dump(res, open(p + ".tmp", "w")); os.replace(p + ".tmp", p); os.chmod(p, 0o600)
    print("done", ds, sf, cf, res["seconds"], "s")


def main():
    a = argparse.ArgumentParser(); a.add_argument("--dataset"); a.add_argument("--subject-fold", type=int); a.add_argument("--content-fold", type=int, default=0)
    a.add_argument("--tasks", help="comma list ds:sf:cf, run in sequence; completed tasks are skipped"); args = a.parse_args()
    todo = [t.split(":") for t in args.tasks.split(",")] if args.tasks else [(args.dataset, args.subject_fold, args.content_fold)]
    for ds, sf, cf in todo:
        if os.path.exists(os.path.join(OUT, "tasks", f"{ds}_sf{int(sf)}_cf{int(cf)}.json")):
            print("skip", ds, sf, cf); continue
        run_task(ds, int(sf), int(cf))


if __name__ == "__main__":
    main()
