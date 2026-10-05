"""C3-DL implementation checks (docs/auditory_c3/C3DL_PILOT_SPEC.md §1). Any failure stops the pilot.

1 zero correction -> q1 == q0 per sample (P-L Gaussian and H-Cur logistic)
2 synthetic worlds through the real P-L code path (fit_m0, build_stim, train_arm, evaluate):
  W1 background only, W2 known conditional increment, W3 pure interaction
3 candidate permutation equivariance
4 train() restored after every validation pass (from the training logs)
5 P-L input channels: 31 stage-B EEG channels, no auxiliary/audio channel
"""
from __future__ import annotations

import numpy as np
import torch

from . import hc, pl
from .core import candidate_scores, device, gaussian_evidence_bits, set_seed

TH_EPS = 1e-6


def _smooth(rng, d, n):
    return pl._bp(rng.standard_normal((d, n))).astype(np.float32)


def make_world(kind, n_subj=12, seconds=160, seed=0):
    rng = np.random.default_rng(seed)
    n = seconds * pl.FS
    M = [rng.standard_normal((pl.D, pl.D)) * 0.5 for _ in range(3)]
    G_ac = rng.standard_normal((16, pl.D)); G_r = rng.standard_normal((16, pl.D)); g_u = rng.standard_normal((16, 1))
    c = rng.standard_normal((pl.D, 1))
    streams, latent = {}, {}
    for story in "12":
        for part in "1234":
            code = "1" + story + part
            Ac = _smooth(rng, pl.D, n); Ac /= Ac.std(1, keepdims=True)
            bg = sum(Mo @ np.roll(Ac, o, axis=1) for Mo, o in zip(M, (-4, 0, 4)))
            R = _smooth(rng, pl.D, n); R /= R.std(1, keepdims=True)
            u = _smooth(rng, 1, n); u /= u.std()
            if kind == "W3":
                res = c @ (u * Ac[:1]) + 0.3 * R
            else:
                res = R
            streams[code] = {"Ac": Ac.astype(np.float32), "L": (bg + res).astype(np.float32), "story": story, "part": part, "n": n}
            latent[code] = {"Ac": Ac, "R": R, "u": u}
    eeg = {}
    for s in range(n_subj):
        e = {}
        for code, lt in latent.items():
            src = G_ac @ lt["Ac"]
            if kind == "W2":
                src = src + 1.5 * (G_r @ lt["R"])
            if kind == "W3":
                src = src + 1.5 * (g_u @ lt["u"])
            src = np.concatenate([np.zeros((16, 13)), src, np.zeros((16, 100))], axis=1)  # EEG lags the stimulus by ~100 ms
            x = src + rng.standard_normal(src.shape) * 1.0
            e[code] = ((x - x.mean(1, keepdims=True)) / x.std(1, keepdims=True)).astype(np.float32)
        eeg[f"s{s:02d}"] = e
    return streams, eeg


def run_world(kind, arms, epochs=40, seed=0, twins=(), head="additive"):
    """Same path as the real pilot: m0 on parts 1-2, fit on part 1, early stop on part 2 (training subjects),
    score held-out subjects on unseen content (parts 3-4; primary) and on seen content (parts 1-2)."""
    dev = device()
    streams, eeg = make_world(kind, seed=seed)
    codes = sorted(streams)
    m0, W, info, norm = pl.fit_m0(streams, [c for c in codes if c[2] in "12"])
    rf = 77
    stim = pl.build_stim(streams, m0, codes, rf)
    subj = {s: pl.subject_segments(stim, e, rf) for s, e in eeg.items()}
    B = pl.Bundle(stim, subj, W, dev)
    subjects = sorted(subj)
    tr_s, te_s = subjects[:8], subjects[8:]
    pools = pl.pools(stim)
    cfg = pl.default_cfg(stim, pools, norm, epochs=epochs); cfg["head"] = head
    out, logs = {}, []
    for arm in arms:
        for tw in ([False, True] if arm in twins else [False]):
            model = pl.train_arm(arm, B, tr_s, pools["fit"], pools["es"], cfg, logs, twin=tw)
            r = {nm: pl.evaluate(model, B, te_s, pools[nm], 8, twin=tw)["mean_over_subjects"]["e_bits_per_sample"] for nm in ("unseen", "seen")}
            out[arm + ("_twin" if tw else "")] = dict(r, best_epoch=model.best_epoch)
    return out, logs


def main(out_path, head="additive"):
    import json
    import os
    res, ok = {}, True
    dev = device(); set_seed(0)
    # 1 zero correction
    norm = {"Ac": (np.zeros(pl.D), np.ones(pl.D)), "m0": (np.zeros(pl.D), np.ones(pl.D))}
    m = pl.PLModel("D2", 31, norm, head=head).to(dev)
    for p in m.parameters():
        torch.nn.init.normal_(p)
    torch.nn.init.zeros_(m.head.l2.weight); torch.nn.init.zeros_(m.head.l2.bias)
    if head == "bilinear":
        torch.nn.init.zeros_(m.bw.weight)
    X = torch.randn(4, 31, pl.T + 76, device=dev); m0 = torch.randn(4, pl.D, pl.T, device=dev); Ac = torch.randn(4, pl.D, pl.T, device=dev)
    with torch.no_grad():
        Lh = m(X, m0, Ac)
        e = gaussian_evidence_bits(torch.randn_like(m0), m0, Lh, torch.eye(pl.D, device=dev))
    hm = hc.HCModel("D2", 20).to(dev)
    torch.nn.init.zeros_(hm.l2.weight); torch.nn.init.zeros_(hm.l2.bias)
    off = torch.randn(8, device=dev)
    with torch.no_grad():
        lg, _ = hm(torch.randn(8, 20, 200, device=dev), torch.randint(0, 6, (8,), device=dev), off)
    d1, d2, d3 = float((Lh - m0).abs().max()), float(e.abs().max()), float((lg - off).abs().max())
    res["1_zero_correction"] = {"pl_max_abs": d1, "pl_evidence_max_abs": d2, "hc_max_abs": d3, "pass": max(d1, d2, d3) <= TH_EPS}
    # 3 candidate permutation
    Lc = torch.randn(3, 9, pl.D, 50, device=dev); Lhat = torch.randn(3, pl.D, 50, device=dev); W = torch.eye(pl.D, device=dev)
    perm = torch.randperm(9)
    s0 = candidate_scores(Lc, Lhat, W); s1 = candidate_scores(Lc[:, perm], Lhat, W)
    res["3_candidate_permutation"] = {"max_abs": float((s0[:, perm] - s1).abs().max()), "pass": bool(torch.allclose(s0[:, perm], s1, atol=1e-5))}
    # 5 channels
    _, ch = pl.load_eeg("th", "301")
    res["5_channels"] = {"n": len(ch), "pass": len(ch) == 31 and not any(a in c.lower() for c in ch for a in pl.AUX_NAMES)}
    # 2 worlds (+ 4 from their logs)
    modes = []
    w1, l1 = run_world("W1", ["D2", "D4"], twins=("D2", "D4"), head=head); w2, l2 = run_world("W2", ["D2"], twins=("D2",), head=head)
    w3, l3 = run_world("W3", ["D0", "D1", "D2"], head=head)
    for lg_ in (l1, l2, l3):
        modes += [r["mode_after_val"] for r in lg_]
    G = lambda w, a: w[a]["unseen"]
    res["2_worlds"] = {"W1": w1, "W2": w2, "W3": w3,
                       "design": "12 synthetic subjects (8 train / 4 test), 8 codes x 160 s; fit part 1, early stop part 2 (<= 40 epochs); primary score = test subjects x unseen content (parts 3-4)",
                       "pass_W1": all(G(w1, a) <= 0.02 and G(w1, a) - G(w1, a + "_twin") <= 0.02 for a in ("D2", "D4")),
                       "pass_W2": G(w2, "D2") > 0.05 and G(w2, "D2") - G(w2, "D2_twin") > 0.05,
                       "pass_W3": G(w3, "D1") > 0.05 and G(w3, "D2") > 0.05 and G(w3, "D0") <= 0.02,
                       "nonfinite_max": max(r["nonfinite"] for r in l1 + l2 + l3)}
    res["2_worlds"]["pass"] = res["2_worlds"]["pass_W1"] and res["2_worlds"]["pass_W2"] and res["2_worlds"]["pass_W3"] and res["2_worlds"]["nonfinite_max"] == 0
    res["4_train_mode_restored"] = {"n_validation_passes": len(modes), "pass": all(m_ == "train" for m_ in modes)}
    ok = all(v["pass"] for v in res.values())
    res["ALL_PASS"] = ok
    res["head"] = head
    res["correctness_pass"] = all(res[k]["pass"] for k in ("1_zero_correction", "3_candidate_permutation", "4_train_mode_restored", "5_channels"))
    res["capability_label"] = ("additive_and_interaction" if res["2_worlds"]["pass"] else
                               "additive_only" if res["2_worlds"]["pass_W1"] and res["2_worlds"]["pass_W2"] else "fails_additive")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(res, open(out_path, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    return ok
