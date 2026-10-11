"""ALN3 private calibration variants (package docs/08 §5; R_PRIVATE_CALIBRATION interface).

The native score s of each trial is calibrated on the training children's early-stopping blocks only (the same blocks
the ALN2 heads use) and evaluated on the test children:
  NCE  s = cos(u, p1) - cos(u, p0)           temperature sigmoid(s / tau) (ALN2 rule) | positive affine sigmoid(a s + b), a > 0
  CS   s = logit of the ALN2 class-kernel posterior   class kernel (ALN2 native)      | positive affine on s
  GX   s = logit difference of the GX network          unconstrained affine (ALN2)     | positive affine
Positive affine = package reference AffineLogitCalibrator (a > 0 cannot change the ranking: AUC is that of s). Reported per
test child: AUC of s, natural-distribution log loss (bits), Brier, gain over the training base rate (bits per trial).
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.special import expit

from .aln3_reference.calibration import AffineLogitCalibrator

LL = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))


def _summ(p, s, y, base):
    from auditory_alignment.evaluate import _auc
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"auc_score": _auc(s, y), "nll_bits": float(-LL(p, y).mean()), "brier": float(((p - y) ** 2).mean()),
            "gain_vs_base_bits": float((LL(p, y) - LL(np.full(len(y), base), y)).mean()), "n": int(len(y))}


def _report(kids, tr, te, S, methods, base):
    out = {"per_participant": {}, "methods": {}}
    for name, (fit_desc, f) in methods.items():
        out["methods"][name] = fit_desc
    for i in te:
        y = kids[i]["y"]; s = S[i]
        out["per_participant"][kids[i]["id"]] = {name: _summ(f(s), s, y, base) for name, (_, f) in methods.items()}
    return out


@torch.no_grad()
def private_variants(row, enc, bt, protos, calib):
    from auditory_alignment.evaluate import _private_reps
    kids = bt.kids; tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
    U = {i: _private_reps(enc, bt, i) for i in tr + te}
    es = {i: kids[i]["es_mask"] for i in tr}
    yr = np.concatenate([kids[i]["y"][es[i]] for i in tr]); base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    obj = row["spec"]["objective"]; methods = {}
    if obj == "NCE":
        P = torch.nn.functional.normalize(protos.detach().float().cpu(), dim=1).numpy()
        score = lambda Ux: ((Ux / np.linalg.norm(Ux, axis=1, keepdims=True)) @ P.T) @ np.array([-1.0, 1.0])
        S = {i: score(U[i]) for i in tr + te}; sr = np.concatenate([S[i][es[i]] for i in tr])
        best = None
        for tau in np.logspace(-3, 1, 41):
            c = float(-LL(expit(sr / tau), yr).mean())
            if best is None or c < best[0]:
                best = (c, tau)
        tau = best[1]
        methods["temperature"] = ({"tau": float(tau)}, lambda s, t=tau: expit(s / t))
    elif obj == "CS_SINGLE":
        r = np.random.default_rng(row["seed"] + 77)
        Xr = np.concatenate([U[i][es[i]] for i in tr]); sel = r.choice(len(Xr), size=min(6000, len(Xr)), replace=False)
        Xs, ys = torch.tensor(Xr[sel], dtype=torch.float64), torch.tensor(yr[sel], dtype=torch.float64); s2 = 2 * calib["sigma_u"] ** 2
        def post(Ux):
            K = torch.exp(-torch.cdist(torch.tensor(Ux, dtype=torch.float64), Xs).pow(2) / s2)
            return np.clip(((K @ ys + base) / (K.sum(1) + 1.0)).numpy(), 1e-6, 1 - 1e-6)
        S = {i: np.log(post(U[i])) - np.log1p(-post(U[i])) for i in tr + te}; sr = np.concatenate([S[i][es[i]] for i in tr])
        methods["class_kernel"] = ({"n_reference": int(len(sel)), "sigma_u": calib["sigma_u"]}, lambda s: expit(s))
    else:
        return {"note": f"no native score for objective {obj}"}
    cal = AffineLogitCalibrator.fit(sr, yr)
    methods["positive_affine"] = (cal.to_dict(), cal.predict)
    out = _report(kids, tr, te, S, methods, base)
    out["calibration_set"] = "training children's early-stopping blocks"; out["n_calibration_trials"] = int(len(yr)); out["base_rate"] = base
    return out


@torch.no_grad()
def gx_variants(row, enc, bt):
    kids = bt.kids; tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == row["subject_fold"]]
    def z_of(i):
        x = bt.Xall[torch.as_tensor(bt.off[i], device=bt.dev) + torch.arange(len(kids[i]["y"]), device=bt.dev)].float()
        lg = enc.logits([x[:, :, a:b] for a, b in bt.W]).float().cpu().numpy(); return lg[:, 1] - lg[:, 0]
    S = {i: z_of(i) for i in tr + te}
    es = {i: kids[i]["es_mask"] for i in tr}
    sr = np.concatenate([S[i][es[i]] for i in tr]); yr = np.concatenate([kids[i]["y"][es[i]] for i in tr])
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    from sklearn.linear_model import LogisticRegression
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(sr[:, None], yr)
    cal = AffineLogitCalibrator.fit(sr, yr)
    methods = {"unconstrained_affine_ALN2": ({"slope": float(lr.coef_[0, 0]), "intercept": float(lr.intercept_[0])}, lambda s: lr.predict_proba(s[:, None])[:, 1]),
               "positive_affine": (cal.to_dict(), cal.predict)}
    out = _report(kids, tr, te, S, methods, base)
    out["calibration_set"] = "training children's early-stopping blocks"; out["n_calibration_trials"] = int(len(yr)); out["base_rate"] = base
    return out
