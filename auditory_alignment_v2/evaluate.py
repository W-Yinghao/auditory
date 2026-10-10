"""ALN2 evaluation. Reuses the validated previous-round evaluation unchanged (auditory_alignment.evaluate: native and
unified readouts, regular / hard / mismatched-EEG real-candidate retrieval, attention 2AFC, test-side kernel dependence,
split-half; private heads fitted on early-stopping blocks, history gain with mismatched-EEG twin) and adds:
  - for selection-trained models, the 2AFC with the trained selection score on test competing-speech segments;
  - private task-native heads (package docs/06 §6.5): NCE prototype softmax with a temperature calibrated on the training
    children's early-stopping blocks; CS label-kernel posterior (Nadaraya-Watson with the unit's training bandwidth over
    the training children's early-stopping trials).
"""
from __future__ import annotations

import numpy as np
import torch

from auditory_alignment import evaluate as ev1

READOUT_OBJ = {"NCE": "NCE", "CS_SINGLE": "CS_SINGLE", "CS_MULTI": "CS_MULTI", "FMCA": "FMCA", "SELECTION_CE": "NCE"}


def evaluate_continuous(row, enc, head, bt, coh, calib, sel=None):
    job = {"subject_fold": row["subject_fold"]}
    out = ev1.evaluate_continuous(READOUT_OBJ[row["spec"]["objective"]], enc, head, bt, coh, job, np.random.default_rng(row["seed"] + 1000), calib)
    if sel is not None:
        out["attention_2afc_trained_score"] = trained_selection_2afc(enc, head, bt, coh, row, sel)
    return out


@torch.no_grad()
def trained_selection_2afc(enc, head, bt, coh, row, sel, stride=4):
    segs = coh.segments
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == row["subject_fold"]})
    offs = np.arange(0, bt.seg_len, stride)
    res = {}
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["kind"] == "cs" and s["role"] == "test" and s.get("s0_ign") is not None]
        if not q:
            continue
        acc, marg = [], []
        for s in q:
            e = torch.tensor(s["e0"] + offs, device=bt.dev)
            u = enc(bt.patches(e))
            va = head(bt.audio(torch.tensor(s["s0"] + offs, device=bt.dev))); vi = head(bt.audio(torch.tensor(s["s0_ign"] + offs, device=bt.dev)))
            sa, si = float(sel(u, va).mean()), float(sel(u, vi).mean())
            acc.append(sa > si); marg.append(sa - si)
        res[coh.participants[p]["id"]] = {"accuracy": float(np.mean(acc)), "mean_margin": float(np.mean(marg)), "n": len(q)}
    return res


@torch.no_grad()
def evaluate_private(row, enc, bt, calib, protos=None):
    job = {"subject_fold": row["subject_fold"]}
    out = ev1.evaluate_private(enc, bt, job, calib)
    kids = bt.kids
    tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
    U = {i: ev1._private_reps(enc, bt, i) for i in tr + te}
    Xr = np.concatenate([U[i][kids[i]["es_mask"]] for i in tr]); yr = np.concatenate([kids[i]["y"][kids[i]["es_mask"]] for i in tr])
    obj = row["spec"]["objective"]
    ll = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    if obj == "NCE" and protos is not None:
        P = torch.nn.functional.normalize(protos.detach().float().cpu(), dim=1).numpy()
        def logit(Ux):
            z = (Ux / np.linalg.norm(Ux, axis=1, keepdims=True)) @ P.T
            return z[:, 1] - z[:, 0]
        zr = logit(Xr); best = None
        for tau in np.logspace(-3, 1, 41):  # temperature on training children's early-stopping blocks (natural distribution)
            q = 1 / (1 + np.exp(-zr / tau)); c = float(-ll(q, yr).mean())
            if best is None or c < best[0]:
                best = (c, tau)
        native = lambda Ux: 1 / (1 + np.exp(-logit(Ux) / best[1])); nat_info = {"kind": "prototype_softmax", "tau": float(best[1])}
    elif obj == "CS_SINGLE":
        r = np.random.default_rng(row["seed"] + 77); sel = r.choice(len(Xr), size=min(6000, len(Xr)), replace=False)
        Xs, ys = torch.tensor(Xr[sel], dtype=torch.float64), torch.tensor(yr[sel], dtype=torch.float64)
        s2 = 2 * calib["sigma_u"] ** 2
        def native(Ux):
            K = torch.exp(-torch.cdist(torch.tensor(Ux, dtype=torch.float64), Xs).pow(2) / s2)
            return ((K @ ys + base) / (K.sum(1) + 1.0)).numpy()  # kernel posterior, one pseudo-trial at the base rate
        nat_info = {"kind": "label_kernel_posterior", "n_reference": int(len(sel)), "sigma_u": calib["sigma_u"]}
    else:
        native, nat_info = None, None
    if native is not None:
        for i in te:
            k = kids[i]; y = k["y"]; p = np.clip(native(U[i]), 1e-6, 1 - 1e-6)
            hg = ll(p, y) - ll(np.full(len(y), base), y); hh = len(y) // 2
            out["per_participant"][k["id"]].update({"native_auc": ev1._auc(p, y), "native_brier": float(((p - y) ** 2).mean()),
                                                    "native_gain_vs_base_bits": float(hg.mean()), "native_gain_half0": float(hg[:hh].mean()),
                                                    "native_gain_half1": float(hg[hh:].mean())})
        out["native_head"] = nat_info
    return out
