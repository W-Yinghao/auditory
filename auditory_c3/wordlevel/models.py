"""Word-level conditional decoding (docs/auditory_c3/WORDLEVEL_REG_v1.md).

Per word: EEG epoch X (31 x 128, -203..789 ms), background C (stimulus side), target Y (GPT-2 state PCA-16, or
surprisal). Scores are Gaussian evidence relative to the linear background B0 with a shared, training-side Sigma
(bits per word), as in auditory_c3.c3dl.pl:  e = (||Y - y0||^2_S^-1 - ||Y - Yhat||^2_S^-1) / (2 ln 2).

Arms: B0 (ridge C -> Y), BG (B0 + MLP(C); no EEG; trained to convergence on unique words), D2s (frozen BG +
zero-initialised correction head g([z(X), C])), D2s_twin (same, EEG of a background-matched other word of the same
participant), D4s (D2s + conditional InfoNCE: negatives BG_i + (Y_j - BG_j), j background-matched), D4s_twin,
B1 (ridge from binned EEG to the whitened residual Y - y0).
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..c3dl.core import Encoder, grad_param_norms, nonfinite, set_seed

LN2 = math.log(2.0)
ALPHAS_B0 = np.logspace(-2, 4, 7)
ALPHAS_B1 = np.logspace(0, 6, 7)
B1_BINS = (26, 128, 6)  # 0..789 ms, 17 bins of 6 samples (~47 ms)


# ------------------------------------------------------------------------------------------------ pools and matching
def pools(tab, fit_parts, es_parts, test_parts):
    return {"fit": np.flatnonzero(np.isin(tab["part"], fit_parts)), "es": np.flatnonzero(np.isin(tab["part"], es_parts)),
            "test": np.flatnonzero(np.isin(tab["part"], test_parts))}


def matched(tab, Cz, pool, K, min_sep_s=5.0):
    """For each word of pool: K nearest words of the same pool by standardised background distance, excluding words of
    the same stream within min_sep_s (no shared EEG epoch)."""
    pool = np.asarray(pool); P = Cz[pool]
    out = {}
    for a, i in enumerate(pool):
        d = ((P - P[a]) ** 2).sum(1)
        bad = (tab["code"][pool] == tab["code"][i]) & (np.abs(tab["t0"][pool] - tab["t0"][i]) < min_sep_s)
        d[bad] = np.inf
        out[int(i)] = [int(pool[j]) for j in np.argsort(d)[:K]]
    return out


# ------------------------------------------------------------------------------------------------ B0 and Sigma
def fit_b0(tab, Y, Cz, fit, es):
    """Ridge C -> Y on unique fit words; alpha by the ES pool; returns y0 for every word, W = Sigma^-1/2 of the fit
    residual."""
    X = np.c_[np.ones(len(Cz)), Cz].astype(np.float64)
    best = None
    for a in ALPHAS_B0:
        I = np.eye(X.shape[1]); I[0, 0] = 0
        B = np.linalg.solve(X[fit].T @ X[fit] + a * I, X[fit].T @ Y[fit])
        sse = float(((Y[es] - X[es] @ B) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, a, B)
    y0 = (X @ best[2]).astype(np.float32)
    R = (Y[fit] - y0[fit]).astype(np.float64)
    Sig = np.atleast_2d(np.cov(R.T)) + 1e-9 * np.eye(Y.shape[1])
    w, V = np.linalg.eigh(Sig)
    W = (V @ np.diag(w ** -0.5) @ V.T).astype(np.float32)
    return y0, W, float(best[1])


def evidence(Y, y0, Yhat, W):
    """bits per word, shape [N]."""
    r0 = (Y - y0) @ W.T; r1 = (Y - Yhat) @ W.T
    return (r0.pow(2).sum(-1) - r1.pow(2).sum(-1)) / (2 * LN2)


# ------------------------------------------------------------------------------------------------ models
class BGNet(nn.Module):
    def __init__(self, p, d):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(p, 64), nn.GELU(), nn.Linear(64, d))
        nn.init.zeros_(self.net[2].weight); nn.init.zeros_(self.net[2].bias)

    def forward(self, C, y0):
        return y0 + self.net(C)


class WordNet(nn.Module):
    """Frozen background prediction (input) + correction g([z(X), C]); last layer zero-initialised."""

    def __init__(self, n_ch, p, d):
        super().__init__()
        self.enc = Encoder(n_ch)
        self.pool = nn.AdaptiveAvgPool1d(8)
        self.fc = nn.Linear(self.enc.d_z * 8, 64)
        self.l1 = nn.Linear(64 + p, 64); self.l2 = nn.Linear(64, d)
        nn.init.zeros_(self.l2.weight); nn.init.zeros_(self.l2.bias)

    def forward(self, X, C, base):
        z = F.gelu(self.fc(self.pool(self.enc(X)).flatten(1)))
        return base + self.l2(F.gelu(self.l1(torch.cat([z, C], 1))))


class Bundle:
    """Tensors on device. subj: {s: (rows (np.int), X (torch float16 [n, 31, 128]))}; loc: {s: {row: local index}}."""

    def __init__(self, tab, Y, Cz, y0, W, subj, dev):
        self.dev = dev
        self.Y = torch.tensor(Y, device=dev); self.C = torch.tensor(Cz, device=dev); self.y0 = torch.tensor(y0, device=dev)
        self.W = torch.tensor(W, device=dev); self.tab = tab
        self.subj = {s: (r, torch.tensor(X, dtype=torch.float16, device=dev)) for s, (r, X) in subj.items()}
        self.loc = {s: {int(i): k for k, i in enumerate(r)} for s, (r, _) in subj.items()}
        self.bgY = None


def train_bg(B, fit, es, seed, max_epochs=3000, patience=200, bs=128, lr=1e-3):
    set_seed(seed); rng = np.random.default_rng(seed)
    net = BGNet(B.C.shape[1], B.Y.shape[1]).to(B.dev)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-4)
    es_t = torch.tensor(es, device=B.dev); best, bad, hist = (np.inf, -1, None), 0, []
    loss = lambda ii: ((B.Y[ii] - net(B.C[ii], B.y0[ii])) @ B.W.T).pow(2).sum(1).mean() / 2
    for ep in range(max_epochs):
        net.train()
        perm = rng.permutation(fit)
        for k in range(0, len(perm), bs):
            ii = torch.tensor(perm[k:k + bs], device=B.dev); opt.zero_grad(); l = loss(ii); l.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            v = float(loss(es_t))
        hist.append(v)
        if v < best[0] - 1e-7:
            best, bad = (v, ep, {k: t.detach().clone() for k, t in net.state_dict().items()}), 0
        else:
            bad += 1
            if bad >= patience:
                break
    net.load_state_dict(best[2]); net.eval(); net.best_epoch = best[1]; net.n_epochs = len(hist)
    with torch.no_grad():
        B.bgY = net(B.C, B.y0)
    return net


def _items(B, subjects, pool):
    pool = set(int(i) for i in pool)
    return [(s, B.loc[s][int(i)], int(i)) for s in subjects for i in B.subj[s][0] if int(i) in pool]


def _swap_local(B, s, i, cand):
    """Local index of the participant's EEG for the first candidate word the participant has."""
    for j in cand:
        if j in B.loc[s]:
            return B.loc[s][j]
    return None


def _x(B, batch, swap=None):
    out = []
    for s, r, i in batch:
        if swap is not None:
            r = _swap_local(B, s, i, swap[i])
        out.append(B.subj[s][1][r])
    return torch.stack(out).float()


def train_arm(arm, B, train_subj, fit, es, cfg, log, twin=False):
    """arm in {D2s, D4s}; early stopping on train_subj x es (natural loss); best epoch restored."""
    set_seed(cfg["seed"]); rng = np.random.default_rng(cfg["seed"])
    net = WordNet(next(iter(B.subj.values()))[1].shape[1], B.C.shape[1], B.Y.shape[1]).to(B.dev)
    opt = torch.optim.AdamW(net.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"])
    tr = _items(B, train_subj, fit); ev = _items(B, train_subj, es)
    mf, me = cfg["matched_fit"], cfg["matched_es"]
    if twin:
        tr = [(s, r2, i) for s, r, i in tr if (r2 := _swap_local(B, s, i, mf[i])) is not None]
    best, bad = (np.inf, -1, None), 0
    for ep in range(cfg["epochs"]):
        net.train(); st = {"nat": [], "con": [], "gn": []}
        perm = rng.permutation(len(tr))
        for k in range(0, len(perm), cfg["bs"]):
            bt = [tr[j] for j in perm[k:k + cfg["bs"]]]
            X = torch.stack([B.subj[s][1][r] for s, r, _ in bt]).float(); ii = torch.tensor([i for _, _, i in bt], device=B.dev)
            Yh = net(X, B.C[ii], B.bgY[ii])
            nat = ((B.Y[ii] - Yh) @ B.W.T).pow(2).sum(1).mean() / 2
            loss = nat
            if arm == "D4s":
                ng = torch.tensor([mf[i][:cfg["K"]] for _, _, i in bt], device=B.dev)
                cand = torch.cat([B.Y[ii][:, None], B.bgY[ii][:, None] + (B.Y[ng] - B.bgY[ng])], 1)  # [b, K+1, d]
                sc = -((cand - Yh[:, None]) @ B.W.T).pow(2).sum(-1) / 2 / cfg["tau"]
                con = F.cross_entropy(sc, torch.zeros(len(bt), dtype=torch.long, device=B.dev))
                loss = nat + cfg["eta"] * con; st["con"].append(float(con))
            opt.zero_grad(); loss.backward(); gn, _ = grad_param_norms(net)
            torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0); opt.step()
            st["nat"].append(float(nat)); st["gn"].append(gn)
        net.eval()
        with torch.no_grad():
            v = []
            for k in range(0, len(ev), 512):
                bt = ev[k:k + 512]; ii = torch.tensor([i for _, _, i in bt], device=B.dev)
                Yh = net(_x(B, bt, me if twin else None), B.C[ii], B.bgY[ii])
                v.append(((B.Y[ii] - Yh) @ B.W.T).pow(2).sum(1) / 2)
            vnat = float(torch.cat(v).mean())
        if vnat < best[0]:
            best, bad = (vnat, ep, {k: t.detach().clone() for k, t in net.state_dict().items()}), 0
        else:
            bad += 1
        net.train(); assert net.training
        log.append({"arm": arm + ("_twin" if twin else ""), "epoch": ep, "train_nat": float(np.mean(st["nat"])),
                    "train_con": float(np.mean(st["con"])) if st["con"] else None, "es_nat": vnat,
                    "grad_norm_mean": float(np.mean(st["gn"])), "param_norm": grad_param_norms(net)[1],
                    "nonfinite": nonfinite(net), "mode_after_val": "train" if net.training else "eval"})
        if bad >= cfg["patience"]:
            break
    net.load_state_dict(best[2]); net.eval(); net.best_epoch = best[1]
    return net


# ------------------------------------------------------------------------------------------------ B1 (linear EEG)
def _feats(X):
    a, b, w = B1_BINS
    return X[:, :, a:b].reshape(X.shape[0], X.shape[1], -1, w).mean(-1).flatten(1)


def fit_b1(B, train_subj, fit):
    acc = {}
    for s in train_subj:
        bt = _items(B, [s], fit)
        if not bt:
            continue
        ii = torch.tensor([i for _, _, i in bt], device=B.dev)
        Fx = torch.cat([torch.ones(len(bt), 1, device=B.dev), _feats(torch.stack([B.subj[s][1][r] for _, r, _ in bt]).float())], 1).double()
        R = ((B.Y[ii] - B.y0[ii]) @ B.W.T).double()
        acc[s] = (Fx.T @ Fx, Fx.T @ R, (R * R).sum())
    tot = [sum(a[k] for a in acc.values()) for k in range(3)]
    I = torch.eye(tot[0].shape[0], device=B.dev, dtype=torch.float64); I[0, 0] = 0
    best = None
    for a in ALPHAS_B1:
        sse = 0.0
        for s, (xx, xy, yy) in acc.items():
            Bs = torch.linalg.solve(tot[0] - xx + a * I, tot[1] - xy)
            sse += float(yy - 2 * (Bs * xy).sum() + (Bs * (xx @ Bs)).sum())
        if best is None or sse < best[0]:
            best = (sse, a)
    Bw = torch.linalg.solve(tot[0] + best[1] * I, tot[1]).float()
    return (Bw, torch.linalg.inv(B.W)), float(best[1])


# ------------------------------------------------------------------------------------------------ evaluation
def predict(B, s, rows_global, kind, model=None, b1=None, swap=None):
    """Predictions for participant s at global word indices rows_global; kind in B0, BG, net, B1."""
    ii = torch.tensor(rows_global, device=B.dev)
    if kind == "B0":
        return B.y0[ii]
    if kind == "BG":
        return B.bgY[ii]
    out = []
    with torch.no_grad():
        for k in range(0, len(rows_global), 512):
            bt = [(s, B.loc[s].get(int(i)), int(i)) for i in rows_global[k:k + 512]]
            X = _x(B, bt, swap); jj = ii[k:k + 512]
            if kind == "B1":
                Bw, Winv = b1
                Fx = torch.cat([torch.ones(len(bt), 1, device=B.dev), _feats(X)], 1)
                out.append(B.y0[jj] + (Fx @ Bw) @ Winv.T)
            else:
                out.append(model(X, B.C[jj], B.bgY[jj]))
    return torch.cat(out)


def evaluate(B, subjects, test, matched_test, kind, model=None, b1=None, twin=False, K=8):
    """Per participant: e (bits/word) on the test pool, e_mismatch (EEG of the top background-matched word), and for
    EEG arms the conditional retrieval top-1 among K background-relative candidates."""
    per = {}
    for s in subjects:
        rows = [int(i) for i in test if int(i) in B.loc[s]]
        if not rows:
            continue
        ii = torch.tensor(rows, device=B.dev)
        sw = matched_test if twin else None
        Yh = predict(B, s, rows, kind, model, b1, swap=sw)
        e = evidence(B.Y[ii], B.y0[ii], Yh, B.W)
        r = {"e_bits_per_word": float(e.mean()), "n_words": len(rows)}
        if kind in ("net", "B1"):
            Ym = predict(B, s, rows, kind, model, b1, swap=matched_test)
            r["e_mismatch"] = float(evidence(B.Y[ii], B.y0[ii], Ym, B.W).mean())
            ng = torch.tensor([matched_test[i][:K] for i in rows], device=B.dev)
            cand = torch.cat([B.Y[ii][:, None], B.bgY[ii][:, None] + (B.Y[ng] - B.bgY[ng])], 1)
            sc = -((cand - Yh[:, None]) @ B.W.T).pow(2).sum(-1)
            r["cond_top1"] = float((sc.argmax(1) == 0).float().mean())
        per[s] = r
    return per
