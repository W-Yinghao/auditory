"""Evaluation of one fitted unit (IMPLEMENTATION_NOTES §4). Readouts are fitted on training participants only; the
candidate pools are defined by stimulus identity, never by test EEG.

Continuous: per test participant, retrieval of each 5 s test segment among (i) all test segments of the same kind
(regular), (ii) the K = 8 stimulus-nearest segments of the same hard_key and another part (hard), with (iii) the query
EEG replaced by another segment of the same participant (mismatched). Readouts: unified ridge bridge into the
standardised target space (all methods) and the method's native score. Attention: attended vs ignored stream (2AFC).
Private: calibrated logistic head on the frozen representation; history gain with a mismatched-EEG twin.
"""
from __future__ import annotations

import numpy as np
import torch

from .data import AUDIO_FRAMES

LN2 = np.log(2.0)


def _cs(u, v=None, labels=None, sigma_u=None, sigma_v=None):
    from .losses import cs_qmi
    _, st = cs_qmi(torch.as_tensor(u, dtype=torch.float64), None if v is None else torch.as_tensor(v, dtype=torch.float64),
                   sigma_u=sigma_u, sigma_v=sigma_v, labels=None if labels is None else torch.as_tensor(labels))
    return st["cs_qmi_nats"]


def test_cs_dependence(Uq, Vown, calib, rng, n_seg=32, anchors=8, draws=4):
    """CS-QMI on test anchors at the unit's training bandwidths: true pairing vs the audio of another test segment of the
    same participant (legal mismatch). Uq / Vown [n, T, d]."""
    n, T = Uq.shape[:2]
    if n < 2:
        return None
    ti = np.linspace(0, T - 1, anchors).round().astype(int)
    m, x = [], []
    for _ in range(draws):
        sel = rng.choice(n, size=min(n_seg, n), replace=False)
        u = Uq[sel][:, ti].reshape(-1, Uq.shape[-1])
        m.append(_cs(u, Vown[sel][:, ti].reshape(-1, Vown.shape[-1]), sigma_u=calib["sigma_u"], sigma_v=calib["sigma_v"]))
        x.append(_cs(u, Vown[np.roll(sel, 1)][:, ti].reshape(-1, Vown.shape[-1]), sigma_u=calib["sigma_u"], sigma_v=calib["sigma_v"]))
    return {"cs_true_nats": float(np.mean(m)), "cs_mismatched_nats": float(np.mean(x)), "cs_true_minus_mismatched": float(np.mean(m) - np.mean(x)),
            "n_rows": int(min(n_seg, n) * anchors), "draws": draws}


def _ridge(X, Y, alphas, Xv=None, Yv=None, crit="mse"):
    """Ridge with intercept; alpha chosen on (Xv, Yv) by mean squared error or by mean per-dimension Pearson r."""
    X1 = np.c_[X, np.ones(len(X))]
    best = None
    for a in alphas:
        R = a * np.eye(X1.shape[1]); R[-1, -1] = 0
        B = np.linalg.solve(X1.T @ X1 + R, X1.T @ Y)
        if Xv is None:
            return B, a
        P = np.c_[Xv, np.ones(len(Xv))] @ B
        if crit == "corr":
            Pc, Yc = P - P.mean(0), Yv - Yv.mean(0)
            err = -float(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)).mean())
        else:
            err = float(((P - Yv) ** 2).mean())
        if best is None or err < best[0]:
            best = (err, a, B)
    return best[2], best[1]


def _zt(X):
    """z-score each (segment, dimension) time course over the anchor axis: [n, T, D]."""
    return (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)


def _apply(B, X):
    return np.c_[X, np.ones(len(X))] @ B


class Reps:
    """Dense-grid representations: u for EEG segments, v (learned audio) and A (standardised target frames)."""

    def __init__(self, enc, aud, bt, stride=4, chunk=2048):
        self.enc, self.aud, self.bt, self.stride, self.chunk = enc, aud, bt, stride, chunk
        self.offs = np.arange(0, bt.seg_len, stride)

    @torch.no_grad()
    def u(self, e0s):
        idx = (np.asarray(e0s)[:, None] + self.offs[None]).reshape(-1)
        out = [self.enc(self.bt.patches(torch.tensor(idx[k:k + self.chunk], device=self.bt.dev))).cpu().numpy() for k in range(0, len(idx), self.chunk)]
        return np.concatenate(out).reshape(len(e0s), len(self.offs), -1)

    @torch.no_grad()
    def va(self, s0s):
        idx = (np.asarray(s0s)[:, None] + self.offs[None]).reshape(-1)
        v, a = [], []
        for k in range(0, len(idx), self.chunk):
            t = torch.tensor(idx[k:k + self.chunk], device=self.bt.dev)
            A = self.bt.audio(t); a.append(A.cpu().numpy()); v.append(self.aud(A).cpu().numpy())
        shp = (len(s0s), len(self.offs), -1)
        return np.concatenate(v).reshape(shp), np.concatenate(a).reshape(shp)


def _cca(U, V, eps=1e-3):
    U = U - U.mean(0); V = V - V.mean(0); n = len(U)
    Ru = U.T @ U / n + eps * np.eye(U.shape[1]); Rv = V.T @ V / n + eps * np.eye(V.shape[1]); P = U.T @ V / n
    iu = np.linalg.inv(np.linalg.cholesky(Ru)).T; iv = np.linalg.inv(np.linalg.cholesky(Rv)).T
    M = iu.T @ P @ iv
    a, s, bT = np.linalg.svd(M, full_matrices=False)
    return iu @ a, iv @ bT.T, s


class Readouts:
    """Fitted on training participants' fit+es segments (subsampled anchors)."""

    def __init__(self, objective, reps, train_segs, rng, n_seg=400, alphas=np.logspace(-3, 3, 7)):
        sel = rng.choice(len(train_segs), size=min(n_seg, len(train_segs)), replace=False)
        segs = [train_segs[i] for i in sel]
        U = reps.u([s["e0"] for s in segs]); V, A = reps.va([s["s0"] for s in segs])
        roles = np.array([s["role"] for s in segs])
        U2, V2, A2 = (x.reshape(-1, x.shape[-1]) for x in (U, V, A))
        r2 = np.repeat(roles, U.shape[1])
        self.a_mu, self.a_sd = A2.mean(0), A2.std(0) + 1e-8
        Az = (A2 - self.a_mu) / self.a_sd
        fit, es = r2 == "fit", r2 == "es"
        has_es = es.sum() > 0
        ua = np.logspace(-4, 8, 13)
        self.B_uni, self.alpha_uni = _ridge(U2[fit], Az[fit], ua, U2[es] if has_es else None, Az[es] if has_es else None, crit="corr")
        self.B_uni = _ridge(U2, Az, [self.alpha_uni])[0]
        self.objective = objective
        if objective == "FMCA":
            self.Wu, self.Wv, self.rho = _cca(U2, V2)
            self.mu_u, self.mu_v = U2.mean(0), V2.mean(0)
        elif objective in ("CS_SINGLE", "CS_MULTI"):
            self.B_nat, self.alpha_nat = _ridge(U2[fit], V2[fit], alphas, U2[es] if has_es else None, V2[es] if has_es else None)
            self.B_nat = _ridge(U2, V2, [self.alpha_nat])[0]
        self.tau = {"unified": 1.0, "native": 1.0}

    def scores(self, Uq, Vc, Ac, kind):
        """Uq [nq, T, d], Vc / Ac [nc, T, .] -> [nq, nc] mean per-anchor scores."""
        if kind == "unified":  # reconstruction correlation: per target dimension over the segment's anchors, averaged
            P = _apply(self.B_uni, Uq.reshape(-1, Uq.shape[-1])).reshape(Uq.shape[0], Uq.shape[1], -1)
            C = (Ac - self.a_mu) / self.a_sd
            return np.einsum("qtd,ctd->qc", _zt(P), _zt(C)) / (P.shape[1] * P.shape[2])
        if self.objective == "NCE":
            return np.einsum("qtd,ctd->qc", Uq, Vc) / Uq.shape[1]
        if self.objective == "FMCA":
            a = (Uq - self.mu_u) @ self.Wu; b = (Vc - self.mu_v) @ self.Wv
            return np.einsum("qtk,ctk->qc", a * self.rho, b) / Uq.shape[1]
        P = _apply(self.B_nat, Uq.reshape(-1, Uq.shape[-1])).reshape(Uq.shape[0], Uq.shape[1], -1)
        return -(np.einsum("qtd,qtd->qt", P, P).mean(1)[:, None] - 2 * np.einsum("qtd,ctd->qc", P, Vc) / P.shape[1]
                 + np.einsum("ctd,ctd->ct", Vc, Vc).mean(1)[None]) / Vc.shape[-1]

    def calibrate(self, S, own):
        """Scalar temperature minimising the candidate cross-entropy on training-side queries (own = true column)."""
        out = {}
        for kind, s in S.items():
            best = None
            sd = s.std() + 1e-12
            for tau in np.logspace(-3, 2, 41) * sd:
                z = s / tau; z = z - z.max(1, keepdims=True)
                ce = float((np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]).mean())
                if best is None or ce < best[0]:
                    best = (ce, tau)
            out[kind] = float(best[1])
        self.tau = out


def _metrics(s, own, tau):
    order = np.argsort(-s, axis=1)
    rank = np.array([int(np.flatnonzero(order[i] == own[i])[0]) for i in range(len(s))])
    z = s / tau; z = z - z.max(1, keepdims=True)
    ll = (np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]) / LN2
    n = s.shape[1]
    return {"top1": float((rank == 0).mean()), "top5": float((rank < 5).mean()), "mrr": float((1 / (rank + 1)).mean()),
            "rank_pct": float((rank / max(1, n - 1)).mean()), "logloss_bits": float(ll.mean()), "n_candidates": int(n), "n_queries": int(len(s))}


def evaluate_continuous(objective, enc, aud, bt, coh, job, rng, calib, K=8):
    segs = coh.segments
    kind = "ss"
    reps = Reps(enc, aud, bt)
    train_segs = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == bt.kind]
    ro = Readouts(objective, reps, train_segs, rng)
    # calibration queries: training participants' early-stop segments against the early-stop pool
    def pool_of(role, k):
        uids, rows = {}, []
        for s in segs:
            if s["role"] == role and s["kind"] == k and s["uid"] not in uids:
                uids[s["uid"]] = len(rows); rows.append(s)
        return uids, rows
    es_uid, es_rows = pool_of("es", kind)
    q_es = [s for s in segs if s["p"] in bt.train_p and s["role"] == "es" and s["kind"] == kind]
    q_es = [q_es[i] for i in rng.choice(len(q_es), size=min(300, len(q_es)), replace=False)] if q_es else []
    if q_es and len(es_rows) > 1:
        Vc, Ac = reps.va([r["s0"] for r in es_rows]); Uq = reps.u([s["e0"] for s in q_es])
        own = np.array([es_uid[s["uid"]] for s in q_es])
        ro.calibrate({"unified": ro.scores(Uq, Vc, Ac, "unified"), "native": ro.scores(Uq, Vc, Ac, "native")}, own)
    te_uid, te_rows = pool_of("test", kind)
    Vc, Ac = reps.va([r["s0"] for r in te_rows])
    feat = np.array([r["feat"] for r in te_rows]); feat = (feat - feat.mean(0)) / (feat.std(0) + 1e-12)
    hard = {}
    for j, r in enumerate(te_rows):
        el = [i for i, q in enumerate(te_rows) if q["hard_key"] == r["hard_key"] and q["part"] != r["part"]]
        if len(el) < K:
            el = [i for i in range(len(te_rows)) if i != j and te_rows[i]["part"] != r["part"]]
        dd = np.sqrt(((feat[el] - feat[j]) ** 2).sum(1))
        hard[j] = [el[i] for i in np.argsort(dd)[:K]]
    per = {}
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and (coh.participants[s["p"]]["fold"] == job["subject_fold"] or coh.participants[s["p"]].get("test_only"))})
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == kind]
        if not q:
            continue
        order = np.argsort([s["e0"] for s in q]); q = [q[i] for i in order]  # physical (recording) order
        Uq = reps.u([s["e0"] for s in q]); own = np.array([te_uid[s["uid"]] for s in q])
        Umm = np.roll(Uq, 1, axis=0)  # mismatched EEG: another segment of the same participant
        rec = {"group": coh.participants[p]["group"], "n_segments": len(q)}
        h = len(q) // 2
        for kind_r in ("unified", "native"):
            S = ro.scores(Uq, Vc, Ac, kind_r)
            rec[f"{kind_r}/regular"] = _metrics(S, own, ro.tau[kind_r])
            if h >= 2:  # split-half reliability on the first / second half of the recording (independent physical blocks)
                rec[f"{kind_r}/regular_half0"] = _metrics(S[:h], own[:h], ro.tau[kind_r])
                rec[f"{kind_r}/regular_half1"] = _metrics(S[h:], own[h:], ro.tau[kind_r])
            Smm = ro.scores(Umm, Vc, Ac, kind_r)
            rec[f"{kind_r}/mismatched_eeg"] = _metrics(Smm, own, ro.tau[kind_r])
            Sh = np.stack([S[i, [own[i]] + hard[own[i]]] for i in range(len(q))])
            rec[f"{kind_r}/hard"] = _metrics(Sh, np.zeros(len(q), int), ro.tau[kind_r])
        dep = test_cs_dependence(Uq, Vc[own], calib, np.random.default_rng(p))
        if dep:
            rec["kernel_dependence"] = dep
        per[coh.participants[p]["id"]] = rec
    out = {"per_participant": per, "readout": {"alpha_unified": ro.alpha_uni, "tau": ro.tau, "n_test_candidates": len(te_rows)}}
    if objective == "FMCA":
        out["readout"]["fmca_train_canonical_correlations"] = [float(x) for x in ro.rho]
    # attention 2AFC on competing-speech test segments (zero-shot for single-speaker-trained models)
    cs = [s for s in segs if s["kind"] == "cs" and s["role"] == "test" and s["s0_ign"] is not None]
    if cs:
        att = {}
        for p in test_p:
            q = [s for s in cs if s["p"] == p]
            if not q:
                continue
            Uq = reps.u([s["e0"] for s in q])
            Va, Aa = reps.va([s["s0"] for s in q]); Vi, Ai = reps.va([s["s0_ign"] for s in q])
            r = {}
            for kind_r in ("unified", "native"):
                sa = np.array([ro.scores(Uq[i:i + 1], Va[i:i + 1], Aa[i:i + 1], kind_r)[0, 0] for i in range(len(q))])
                si = np.array([ro.scores(Uq[i:i + 1], Vi[i:i + 1], Ai[i:i + 1], kind_r)[0, 0] for i in range(len(q))])
                r[kind_r] = {"accuracy": float((sa > si).mean()), "mean_margin": float((sa - si).mean()), "n": len(q)}
            att[coh.participants[p]["id"]] = r
        out["attention_2afc"] = att
    return out


# ------------------------------------------------------------------------------------------------ private
def _auc(p, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan")


@torch.no_grad()
def _private_reps(enc, bt, i, swap=False):
    k = bt.kids[i]
    idx = np.arange(len(k["y"]))
    if swap:
        idx = k["swap"]
    out = []
    for a in range(0, len(idx), 1024):
        t = torch.tensor(idx[a:a + 1024], device=bt.dev)
        out.append(enc(bt.patches(i, t)).cpu().numpy())
    return np.concatenate(out)


def evaluate_private(enc, bt, job, calib):
    from sklearn.linear_model import LogisticRegression
    from auditory_c3.c3dl.hc import q0_table, _logit
    from auditory_c3.c3dl_stage0 import _fit_offset_logistic
    kids = bt.kids
    tr = bt.train; te = [i for i, k in enumerate(kids) if k["fold"] == job["subject_fold"]]
    q0 = q0_table([kids[i] for i in tr])
    U = {i: _private_reps(enc, bt, i) for i in tr + te}
    Utw = {i: _private_reps(enc, bt, i, swap=True) for i in tr + te}
    # EEG readouts are fitted on the training children's early-stopping blocks only: their fit trials received gradient
    # steps and the encoders overfit them (probe: head AUC 0.60-0.73 on fit trials vs 0.52-0.55 on es blocks), which made
    # heads fitted on all trials over-confident on new children. EEG-free parts (q0, base rate) use all training trials.
    es = {i: kids[i]["es_mask"] for i in tr}
    Xtr = np.concatenate([U[i][es[i]] for i in tr]); ytr = np.concatenate([kids[i]["y"][es[i]] for i in tr])
    head = LogisticRegression(C=1.0, max_iter=2000).fit(Xtr, ytr)
    base = float(np.concatenate([kids[i]["y"] for i in tr]).mean())
    off_tr = _logit(q0[np.concatenate([kids[i]["bin"][es[i]] for i in tr])])
    w = _fit_offset_logistic(Xtr, ytr, off_tr)
    w_tw = _fit_offset_logistic(np.concatenate([Utw[i][es[i]] for i in tr]), ytr, off_tr)
    per = {}
    for i in te:
        k = kids[i]; y = k["y"]
        p = head.predict_proba(U[i])[:, 1]
        p0 = q0[k["bin"]]
        lg0 = _logit(p0)
        pw = 1 / (1 + np.exp(-(lg0 + np.c_[np.ones(len(y)), U[i]] @ w)))
        pt = 1 / (1 + np.exp(-(lg0 + np.c_[np.ones(len(y)), Utw[i]] @ w_tw)))
        ll = lambda q: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
        cs = (p0 > 0.01) & (p0 < 0.99)
        g, gt = ll(pw) - ll(p0), ll(pt) - ll(p0)
        hg = ll(np.clip(p, 1e-6, 1 - 1e-6)) - ll(np.full(len(y), base))
        hh = len(y) // 2
        r = np.random.default_rng(i); m, x = [], []
        for _ in range(4):  # label-kernel CS at the training bandwidth: true vs within-child permuted labels
            sel = r.choice(len(y), size=min(256, len(y)), replace=False)
            m.append(_cs(U[i][sel], labels=y[sel], sigma_u=calib["sigma_u"])); x.append(_cs(U[i][sel], labels=r.permutation(y[sel]), sigma_u=calib["sigma_u"]))
        per[k["id"]] = {"group": k["group"], "age_months": k["age_months"], "duration_months": k["duration_months"], "n": int(len(y)),
                        "head_auc": _auc(p, y), "head_brier": float(((p - y) ** 2).mean()),
                        "head_logloss_bits": float(-ll(np.clip(p, 1e-6, 1 - 1e-6)).mean()), "head_gain_vs_base_bits": float(hg.mean()),
                        "head_gain_vs_base_half0": float(hg[:hh].mean()), "head_gain_vs_base_half1": float(hg[hh:].mean()),
                        "qW_auc": _auc(pw, y), "qW_brier": float(((pw - y) ** 2).mean()), "q0_auc": _auc(p0, y), "q0_brier": float(((p0 - y) ** 2).mean()),
                        "qW_twin_auc": _auc(pt, y), "hist_gain_half0": float(g[:hh].mean()), "hist_gain_half1": float(g[hh:].mean()),
                        "common_support_fraction": float(cs.mean()),
                        "kernel_dependence": {"cs_true_nats": float(np.mean(m)), "cs_mismatched_nats": float(np.mean(x)),
                                              "cs_true_minus_mismatched": float(np.mean(m) - np.mean(x))},
                        "hist_gain_bits": float(g.mean()), "hist_gain_twin_bits": float(gt.mean()),
                        "hist_gain_common_support": float(g[cs].mean()) if cs.any() else None,
                        "hist_gain_twin_common_support": float(gt[cs].mean()) if cs.any() else None}
    return {"per_participant": per, "readout": {"head_fit": "training children, early-stopping blocks only", "n_head_fit_trials": int(len(ytr))}}
