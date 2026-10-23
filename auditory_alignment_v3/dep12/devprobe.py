"""DEP12 fixed source-dev readout (package 02 §4): the only input to the E0 mode choice.

Per checkpoint, on that checkpoint's own common representation U (source_common.tokens_to_U of the final CBraMod layer;
the B0 PCA is never reused):
  1. PCA16: centre U on the source-fit panel mean, top-16 right singular vectors of the centred fit matrix (float64).
  2. Ridge on the 16 scores -> the 125 ms envelope (8 samples at 64 Hz, the raw normalised env of the fixed source-fit
     panel), with intercept: per envelope sample, minimise mean_i (y_i - b - z_i w)^2 + 0.1 * ||w||^2 (mean squared error
     over panel anchors + 0.1 x squared norm; intercept unpenalised): w = (Z'Z/n + 0.1 I)^-1 Z'y/n on centred Z, y.
  3. Read out on the dev panel (dev listeners AND dev content families, both disjoint from fit): per dev listener, Pearson r
     between the predicted and the true envelope over all of that listener's anchors x 8 samples; report the per-listener
     vector and its equal-weight mean.
No dev information enters any fit; no hyper-parameter is chosen.
"""
from __future__ import annotations

import math

import numpy as np

PCA_DIM, RIDGE = 16, 0.1


def fit(U_fit, Y_fit, k=PCA_DIM, lam=RIDGE):
    import torch
    U = torch.as_tensor(U_fit).double(); Y = torch.as_tensor(Y_fit).double().to(U.device)
    mu = U.mean(0); Z0 = U - mu
    _, S, Vh = torch.linalg.svd(Z0, full_matrices=False)
    V = Vh[:k].T                                            # [D, k]
    Z = Z0 @ V; zm = Z.mean(0); Zc = Z - zm
    ym = Y.mean(0); Yc = Y - ym; n = len(Z)
    W = torch.linalg.solve(Zc.T @ Zc / n + lam * torch.eye(k, dtype=Z.dtype, device=Z.device), Zc.T @ Yc / n)
    ev = (S ** 2) / max(n - 1, 1)
    return {'mu': mu, 'V': V, 'zm': zm, 'W': W, 'ym': ym,
            'explained_fraction_top16': float(ev[:k].sum() / ev.sum()) if float(ev.sum()) > 0 else float('nan'),
            'fit_mse': float(((Zc @ W - Yc) ** 2).mean()), 'n_fit': n}


def predict(model, U):
    import torch
    U = torch.as_tensor(U).double().to(model['mu'].device)
    return ((U - model['mu']) @ model['V'] - model['zm']) @ model['W'] + model['ym']


def pearson(a, b):
    a = np.asarray(a, np.float64).ravel(); b = np.asarray(b, np.float64).ravel()
    a = a - a.mean(); b = b - b.mean()
    den = math.sqrt(float((a * a).sum()) * float((b * b).sum()))
    return float((a * b).sum() / den) if den > 0 else float('nan')


def score(U_fit, Y_fit, U_dev, Y_dev, who_dev, people_dev):
    m = fit(U_fit, Y_fit)
    P = predict(m, U_dev).cpu().numpy(); Y = np.asarray(Y_dev, np.float64); who = np.asarray(who_dev)
    per = {str(people_dev[i]): pearson(P[who == i], Y[who == i]) for i in sorted(set(who.tolist()))}
    vals = [v for v in per.values()]
    return {'rule': 'PCA16 (per-checkpoint refit on source-fit panel) + ridge mean-MSE + 0.1*||w||^2 -> 125 ms envelope',
            'pca_dim': PCA_DIM, 'ridge': RIDGE, 'per_dev_listener_r': per,
            'dev_listener_mean_r': float(np.mean(vals)) if all(np.isfinite(vals)) else float('nan'),
            'n_dev_listeners': len(per), 'n_dev_rows': int(len(Y)), 'n_fit_rows': m['n_fit'],
            'fit_mse': m['fit_mse'], 'explained_fraction_top16': m['explained_fraction_top16'],
            'finite': bool(all(np.isfinite(vals)))}
