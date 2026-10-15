"""ALN3 ADDENDUM_09 ALN32_SIMPLE_COMPLEMENT: low-complexity complement of a frozen local base in the common prediction space.

Per unit (fold cell x base {L0, L1} x backbone): frozen base model (A_LOCAL lag_local_tokens full, or ALN32_LOCAL_SUPPORT
local_aligned1000), frozen query-aligned backbone (pretrained and random initialisation, last layer), raw aligned window.
Every variant predicts the raw 8-frame target A(t); the scored representation is u = FixedFeatureHead(Ahat) (the local / B
space). Residual ridges are fitted on out-of-fold base predictions over 5 fixed groups of training participants; every ridge
alpha by grouped cross-validation (participants). No training, no test participant in any fit. Evaluation: the unchanged
ev2.evaluate_continuous with representations from cached per-query features (one evaluation per variant)."""
from __future__ import annotations

import os
import time
import traceback

import numpy as np
import torch

from . import core

K_PCA, N_GROUPS, GROUP_SEED = 64, 5, 20261014
ALPHAS = np.logspace(-5, 3, 9)
N_PCA_ROWS = 8000  # PCA fitted on a fixed random subsample of training rows (memory: DTU REVE tokens are 32,768-d)
VARIANTS = ("local_only", "local_refit_capacity", "aligned_pretrained", "aligned_random", "small_context", "concat")
PRE_S = 0.4


def base_row(row, rows):
    b = row["spec"]["base"]
    for r in rows:
        if all(r[k] == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed")) and r["spec"].get("objective") == row["spec"]["objective"]:
            s = r["spec"]
            if b == "L0" and r["family_id"] == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
                return r
            if b == "L1" and r["family_id"] == "ALN32_LOCAL_SUPPORT" and s.get("variant") == "local_aligned1000":
                return r
    return None


def base_ready(row, rows, out=core.OUT):
    import json
    b = base_row(row, rows)
    if b is None:
        return None
    p = os.path.join(out, "units", f"{b['experiment_id']}.json"); ck = os.path.join(out, "ckpt", f"{b['experiment_id']}_best.pt")
    return (b, p, ck) if os.path.exists(p) and os.path.exists(ck) and json.load(open(p)).get("status") == "complete" else None


# ------------------------------------------------------------------------------------------------ ridge helpers (float64, GPU)
def _std(X):
    mu = X.mean(0); sd = X.std(0) + 1e-6
    return mu, sd


def ridge_fit(X, Y, a):
    mu, sd = _std(X); my = Y.mean(0); Z = (X - mu) / sd
    G = Z.T @ Z; tr = float(torch.trace(G)) / G.shape[0]
    B = torch.linalg.solve(G + a * tr * torch.eye(G.shape[0], dtype=G.dtype, device=G.device), Z.T @ (Y - my))
    return lambda X_: ((X_ - mu) / sd) @ B + my


def corr(P, Y):
    P = P - P.mean(0); Y = Y - Y.mean(0)
    return float(((P * Y).sum(0) / (torch.sqrt((P ** 2).sum(0) * (Y ** 2).sum(0)) + 1e-12)).mean())


def grouped_alpha(X, Y, g):
    best = None; curve = []
    for a in ALPHAS:
        P = torch.empty_like(Y)
        for k in range(N_GROUPS):
            m = g == k
            P[m] = ridge_fit(X[~m], Y[~m], float(a))(X[m])
        r = corr(P, Y); curve.append({"alpha_rel": float(a), "grouped_cv_r": r})
        if best is None or r > best[0]:
            best = (r, float(a))
    return best[1], curve


def oof(X, Y, g, a):
    P = torch.empty_like(Y)
    for k in range(N_GROUPS):
        m = g == k
        P[m] = ridge_fit(X[~m], Y[~m], a)(X[m])
    return P


# ------------------------------------------------------------------------------------------------ features
class Featurizer:
    """per-query features: base u, base tokens, raw aligned window, aligned backbone tokens (pretrained / random); PCA-reduced."""

    def __init__(self, enc, bt, bbs, pre, post):
        self.enc, self.bt, self.bbs, self.pre, self.post = enc, bt, bbs, pre, post
        self.starts = torch.tensor(sorted({s["e0"] for s in bt.coh_segments}), device=bt.dev)
        self.pca = {}

    @torch.no_grad()
    def raw(self, e):
        from .local_support import masked_windows
        return masked_windows(self.bt.E, e, -self.pre, self.post, self.starts)

    @torch.no_grad()
    def blocks(self, e, chunk=512):
        out = {"u": [], "tok": [], "raw": [], **{f"fm_{k}": [] for k in self.bbs}}
        for i in range(0, len(e), chunk):
            ee = e[i:i + chunk]; P = self.bt.patches(ee)
            out["u"].append(self.enc(P).float()); out["tok"].append(self.enc.forward_tokens(P).flatten(1).float())
            W = self.raw(ee); out["raw"].append(W.flatten(1).float())
            for k, bb in self.bbs.items():
                h = bb(W); out[f"fm_{k}"].append(h[:, :, 0].flatten(1).float())
        return {k: torch.cat(v) for k, v in out.items()}

    def fit_pca(self, F):
        for k, X in F.items():
            if k == "u":
                continue
            mu = X.mean(0); U, S, V = torch.pca_lowrank(X - mu, q=min(K_PCA + 8, X.shape[1]), center=False, niter=4)
            self.pca[k] = (mu, V[:, :K_PCA])

    def reduce(self, F):
        return {k: (X if k == "u" else (X - self.pca[k][0]) @ self.pca[k][1]).double() for k, X in F.items()}


def fit_variants(Fr, A, g):
    """Fr: reduced training features; A raw targets; g participant groups -> {variant: predictor(Fr_test) -> Ahat}, log."""
    log = {}
    a0, c0 = grouped_alpha(Fr["u"], A, g); base_full = ridge_fit(Fr["u"], A, a0); base_oof = oof(Fr["u"], A, g, a0)
    log["local_only"] = {"alpha_rel": a0, "curve": c0}
    preds = {"local_only": lambda F: base_full(F["u"])}
    R = A - base_oof
    for v, key in (("local_refit_capacity", "tok"), ("aligned_pretrained", "fm_pretrained"), ("aligned_random", "fm_random"), ("small_context", "raw")):
        a, c = grouped_alpha(Fr[key], R, g); res = ridge_fit(Fr[key], R, a)
        log[v] = {"alpha_rel": a, "curve": c}
        preds[v] = (lambda F, res=res, key=key: base_full(F["u"]) + res(F[key]))
    Xc = torch.cat([Fr["u"], Fr["fm_pretrained"]], 1)
    a, c = grouped_alpha(Xc, A, g); cj = ridge_fit(Xc, A, a); log["concat"] = {"alpha_rel": a, "curve": c}
    preds["concat"] = lambda F: cj(torch.cat([F["u"], F["fm_pretrained"]], 1))
    return preds, log


class VariantReps:
    """ev1.Reps interface: u = FixedFeatureHead(Ahat) at every grid query, from cached reduced features."""

    def __init__(self, fz, pred, head, bt, stride, cache, reps_cls):
        self.fz, self.pred, self.aud, self.bt, self.cache = fz, pred, head, bt, cache
        self.offs = np.arange(0, bt.seg_len, stride); self._va = reps_cls(None, head, bt, stride=stride)  # the unpatched ev1.Reps (audio side)

    @torch.no_grad()
    def u(self, e0s):
        out = []
        for e0 in np.asarray(e0s):
            k = int(e0)
            if k not in self.cache:
                F = self.fz.reduce(self.fz.blocks(torch.tensor(k + self.offs, device=self.bt.dev)))
                self.cache[k] = {n: X.float().cpu() for n, X in F.items()}
            F = {n: X.to(self.bt.dev).double() for n, X in self.cache[k].items()}
            out.append(self.aud(self.pred(F).float()).cpu().numpy())
        return np.stack(out)

    def va(self, s0s):
        return self._va.va(s0s)


# ------------------------------------------------------------------------------------------------ runner
def run(row, out, epochs=None):
    import json
    from auditory_alignment import evaluate as ev1
    from auditory_alignment.train import Objective
    from auditory_alignment_v2 import evaluate as ev2
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    from . import local_support, local_train
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    s = row["spec"]; rows = core.load_rows(); br = base_ready(row, rows, out)
    if br is None:
        print("technical_pending (base not complete)", row["experiment_id"]); return
    b = core.bind(row); dev = torch.device("cuda"); t0 = time.time(); rec = core.new_record(row, b, out)
    rec["dependency"] = {"base": br[0]["experiment_id"], "base_code_hash": json.load(open(br[1]))["code_hash"], "base_checkpoint": os.path.relpath(br[2], core.REPO)}
    try:
        coh = load_cohort(b); g = core.grid_samples(coh.fs); d = int(s.get("projection_dim", 32))
        bcls = local_support.batcher_for("aligned1000") if s["base"] == "L1" else local_train.GridBatcher
        bt = bcls(coh, {**b["spec"], "architecture": "lag_local_tokens", "window": "full"}, b, dev, g)  # the base encoder's batcher (lag window)
        enc = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
        sd = torch.load(br[2], map_location=dev); enc.load_state_dict(sd["enc"], strict=True); enc.eval()
        head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
        head.load_state_dict(sd["head"], strict=True); head.eval()
        bbs = {}
        for init, ad in (("pretrained", "pretrained_frozen"), ("random", "random_full")):
            torch.manual_seed(row["seed"]); bb = Backbone(s["architecture"], coh.meta["dataset"], ad, coh.fs).to(dev).eval()
            for p in bb.parameters():
                p.requires_grad_(False)
            bbs[init] = bb
        pre, post = int(round(PRE_S * coh.fs)), int(bt.W[0][1])  # post = the lag_local_tokens full window end (77 samples at 128 Hz, 60 at 100 Hz)
        fz = Featurizer(enc, bt, bbs, pre, post)
        # training rows: 8 grid anchors per fit and early-stopping segment of the training participants
        rng = np.random.default_rng(row["seed"]); units = list(bt.fit) + list(bt.es)
        E, Sx, P = [], [], []
        for k in range(0, len(units), 64):
            r = bt.rows(units[k:k + 64], rng, anchors=8); E.append(r[0]); Sx.append(r[1])
            P += [bt.coh_segments[i]["p"] for i in units[k:k + 64] for _ in range(8)]
        e = torch.cat(E); sx = torch.cat(Sx)
        parts = sorted(set(P)); perm = np.random.default_rng(GROUP_SEED).permutation(len(parts)); grp = {p: int(perm[i]) % N_GROUPS for i, p in enumerate(parts)}
        gt = torch.tensor([grp[p] for p in P], device=dev)
        assert set(P) <= set(bt.train_p), "a non-training participant in the fit rows"
        sub = torch.tensor(np.sort(np.random.default_rng(GROUP_SEED + 2).choice(len(e), size=min(N_PCA_ROWS, len(e)), replace=False)), device=dev)
        Fs = fz.blocks(e[sub]); fz.fit_pca(Fs); del Fs; torch.cuda.empty_cache()
        chunks = [fz.reduce(fz.blocks(e[k:k + 4096])) for k in range(0, len(e), 4096)]
        Fr = {n: torch.cat([q[n] for q in chunks]) for n in chunks[0]}; del chunks
        with torch.no_grad():
            A = bt.audio(sx).double()
        preds, flog = fit_variants(Fr, A, gt)
        rec.update({"fit": flog, "n_fit_rows": int(len(e)), "n_train_participants": len(parts), "groups": N_GROUPS, "k_pca": K_PCA,
                    "base_trained_on_all_groups": True, "window_samples": [-pre, post], "variants": list(VARIANTS), "n_pca_rows": int(len(sub)), "alpha_grid": [float(a) for a in ALPHAS]})
        torch.save({"pca": {k: (m.cpu(), V.cpu()) for k, (m, V) in fz.pca.items()}}, os.path.join(out, "ckpt", row["experiment_id"] + "_best.pt"))
        cache, evs = {}, {}
        obj_job = {"objective": s["objective"], "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
        calib_batch = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), 32))
        r0 = bt.rows(calib_batch, np.random.default_rng(row["seed"] + 98), anchors=8)
        for v in VARIANTS:
            with torch.no_grad():
                F0 = fz.reduce(fz.blocks(r0[0])); u0 = head(preds[v](F0).float())
            calib = Objective(obj_job, u0, head(bt.audio(r0[1]))).record()
            orig = ev1.Reps
            ev1.Reps = lambda enc_, aud, bt_, **kw: VariantReps(fz, preds[v], head, bt_, g, cache, orig)
            try:
                evs[v] = ev2.evaluate_continuous(b, enc, head, bt, coh, calib, None)
            finally:
                ev1.Reps = orig
        rec["eval_variants"] = evs; rec["eval"] = evs["local_only"]
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
