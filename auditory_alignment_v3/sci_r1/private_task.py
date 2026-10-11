"""Private current-class analyses for one outer fold (SCI_R1_PREREG §4.2, §5.2, §6, §7). Everything here is private.

Trials, labels, folds and early-stopping blocks: auditory_alignment.data.load_private() (the E_LOCAL / D_TASK_LOCAL sets).
Readouts are fitted on the training children's early-stopping blocks only (their fit trials received gradient steps) and
evaluated on all trials of the fold's test children; EEG-free parts (q0 history table, base rate) use all training trials.
Per lag k (features standardised on the training es rows):
  frozen  h_k = token_k - pos_k of the unit's encoder; random: untrained encoder built after torch.manual_seed(row seed)
  raw     fp16-rounded epoch samples [50 + 5k, 60 + 5k) (20 ch x 10 samples), k = -10..28 (negative = pre-stimulus control)
  readout L2 logistic C = 1; AUC of the score; positive-affine calibration on training es -> NLL / Brier / gain vs base
  history sigmoid(logit q0[bin] + [1, x] w) (auditory_c3 _fit_offset_logistic on training es) -> gain over q0 (all trials and
          common support 0.01 < q0 < 0.99); twin = same fit on the swapped trials (same record, same bin, other block)
TG: readout (scaler + weights) at tau applied to tau' features: AUC; NLL after positive-affine recalibration at tau' on training es.
MD: native score (NCE prototype cosine difference / CS class-kernel log-odds at the unit's training bandwidth, reference set from
training es) with test tokens occluded by the training-es mean token, calibration fixed. SB: probe on u (scaler + LR, training
es) with the tokens deleted in training and test and refitted. Channel occlusion: z-scored test channel set to 0, native score
and calibration fixed. Haufe patterns of the raw maps (input space); first-layer spatial filter patterns.
Outputs: private/auditory_alignment_v3/sci_r1/private/<key>.npz + .json (0700); skip-if-done.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

import numpy as np
import torch
import torch.nn.functional as F
from scipy.special import expit

from auditory_alignment_v3 import core
from . import lags as L
from .readout import cov, filter_energy, haufe

OUT = os.path.join(core.OUT, "sci_r1")
LL = lambda q, y: np.where(y == 1, np.log2(np.clip(q, 1e-12, 1)), np.log2(np.clip(1 - q, 1e-12, 1)))
S1_METRICS = ("auc", "nll_bits", "brier", "gain_vs_base_bits", "hist_gain_bits", "hist_gain_cs_bits", "hist_gain_twin_bits",
              "hist_gain_twin_cs_bits", "auc_fit_all", "nll_bits_fit_all")
RAW_LAGS = list(range(-10, 29))


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def _auc(s, y):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


class Fold:
    def __init__(self, kids, sf):
        from auditory_c3.c3dl.hc import q0_table, _logit
        self.kids, self.sf = kids, sf
        self.tr = [i for i, k in enumerate(kids) if k["fold"] != sf]
        self.te = [i for i, k in enumerate(kids) if k["fold"] == sf]
        self.q0 = q0_table([kids[i] for i in self.tr]); self.logit = _logit
        self.base = float(np.concatenate([kids[i]["y"] for i in self.tr]).mean())
        self.es = {i: kids[i]["es_mask"] for i in self.tr}
        self.y_es = np.concatenate([kids[i]["y"][self.es[i]] for i in self.tr])
        self.y_all = np.concatenate([kids[i]["y"] for i in self.tr])
        self.off_es = _logit(self.q0[np.concatenate([kids[i]["bin"][self.es[i]] for i in self.tr])])

    def es_rows(self, X):
        return np.concatenate([X[i][self.es[i]] for i in self.tr])

    def all_rows(self, X):
        return np.concatenate([X[i] for i in self.tr])


class Probe:
    """Standardise on the given training rows, L2 logistic C = 1; positive-affine calibrator on training-es scores."""

    def __init__(self, Xtr, ytr, Xcal=None, ycal=None):
        from sklearn.linear_model import LogisticRegression
        from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator
        self.mu, self.sd = Xtr.mean(0), Xtr.std(0) + 1e-8
        self.lr = LogisticRegression(C=1.0, max_iter=2000).fit((Xtr - self.mu) / self.sd, ytr)
        Xc, yc = (Xtr, ytr) if Xcal is None else (Xcal, ycal)
        self.cal = AffineLogitCalibrator.fit(self.score(Xc), yc)

    def score(self, X):
        return self.lr.decision_function((X - self.mu) / self.sd)

    def w_input(self):  # weights in the original input space
        return self.lr.coef_[0] / self.sd


def child_metrics(s, p, y, base):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return _auc(s, y), float(-LL(p, y).mean()), float(((p - y) ** 2).mean()), float((LL(p, y) - LL(np.full(len(y), base), y)).mean())


def s1_lags(fd, X, n_lags, do_tg, history=True, fit_all=False):
    """X[i] [n_i, n_lags, p] per child -> S1 metrics [n_te, n_lags, len(S1_METRICS)], probes, optional TG [n_te, K, K, 2]."""
    from auditory_c3.c3dl_stage0 import _fit_offset_logistic
    kids = fd.kids
    s1 = np.full((len(fd.te), n_lags, len(S1_METRICS)), np.nan); probes = []
    for k in range(n_lags):
        Xk = {i: X[i][:, k] for i in X}
        Xe = fd.es_rows(Xk)
        pr = Probe(Xe, fd.y_es); probes.append(pr)
        if history:
            Z = (Xe - pr.mu) / pr.sd
            w = _fit_offset_logistic(Z, fd.y_es, fd.off_es)
            Xtw = {i: Xk[i][kids[i]["swap"]] for i in Xk}
            Ztw = (fd.es_rows(Xtw) - pr.mu) / pr.sd
            w_tw = _fit_offset_logistic(Ztw, fd.y_es, fd.off_es)
        if fit_all:
            pa = Probe(fd.all_rows(Xk), fd.y_all, Xe, fd.y_es)
        for j, i in enumerate(fd.te):
            y = kids[i]["y"]; s = pr.score(Xk[i]); p = pr.cal.predict(s)
            row = list(child_metrics(s, p, y, fd.base))
            if history:
                p0 = fd.q0[kids[i]["bin"]]; lg0 = fd.logit(p0); cs = (p0 > 0.01) & (p0 < 0.99)
                pw = expit(lg0 + np.c_[np.ones(len(y)), (Xk[i] - pr.mu) / pr.sd] @ w)
                pt = expit(lg0 + np.c_[np.ones(len(y)), (Xtw[i] - pr.mu) / pr.sd] @ w_tw)
                g, gt = LL(pw, y) - LL(p0, y), LL(pt, y) - LL(p0, y)
                row += [float(g.mean()), float(g[cs].mean()) if cs.any() else np.nan, float(gt.mean()), float(gt[cs].mean()) if cs.any() else np.nan]
            else:
                row += [np.nan] * 4
            if fit_all:
                sa = pa.score(Xk[i]); row += [_auc(sa, y), float(-LL(np.clip(pa.cal.predict(sa), 1e-6, 1 - 1e-6), y).mean())]
            else:
                row += [np.nan, np.nan]
            s1[j, k] = row
    out = {"s1": s1}
    if do_tg:
        from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator
        tg = np.full((len(fd.te), n_lags, n_lags, 2), np.nan)
        for k2 in range(n_lags):
            Xk2 = {i: X[i][:, k2] for i in X}; Xe2 = fd.es_rows(Xk2)
            for k1 in range(n_lags):
                pr = probes[k1]
                cal = pr.cal if k1 == k2 else AffineLogitCalibrator.fit(pr.score(Xe2), fd.y_es)
                for j, i in enumerate(fd.te):
                    y = kids[i]["y"]; s = pr.score(Xk2[i]); p = np.clip(cal.predict(s), 1e-6, 1 - 1e-6)
                    tg[j, k1, k2] = [_auc(s, y), float(-LL(p, y).mean())]
        out["tg"] = tg
        out["tg_diag_maxdiff"] = float(np.nanmax(np.abs(np.diagonal(tg[..., 0], axis1=1, axis2=2) - s1[:, :, 0])))
    return out, probes


# ------------------------------------------------------------------------------------------------ models
def model_for(task, kids, trained=True):
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v3 import private_stage
    enc, protos, rec, bt = private_stage.rebuild(task["eid"], kids, torch.device("cpu"))
    if trained and rec.get("status") != "complete":
        raise RuntimeError(f"unit record status {rec.get('status')}")
    if not trained:  # P2: same architecture built right after torch.manual_seed(task seed)
        row = rec["row"]; b = core.bind(row) if row["family_id"] == "E_LOCAL" else row
        d = 32 if row["family_id"] == "E_LOCAL" else 16
        torch.manual_seed(task.get("seed", row["seed"]))
        enc = build_encoder(b["spec"]["architecture"], 20, d, bt.W, 250); enc.eval(); protos = None
    return enc, protos, rec, bt


@torch.no_grad()
def child_tokens(enc, bt, i, zero_ch=None):
    n = len(bt.kids[i]["y"]); out = []
    for a in range(0, n, 2048):
        ps = bt.patches(i, torch.arange(a, min(n, a + 2048)))
        if zero_ch is not None:
            for p in ps:
                p[:, zero_ch, :] = 0.0
        out.append(enc.forward_tokens(ps).numpy())
    return np.concatenate(out)


@torch.no_grad()
def pooled(enc, Z):
    return F.normalize(enc.proj(torch.as_tensor(Z).flatten(1)), dim=1).numpy()


class Native:
    """Unit's native score on pooled u (private_stage.native_scores rule) with a reference set fixed from unoccluded u."""

    def __init__(self, rec, protos, fd, U):
        self.obj = rec["row"]["spec"]["objective"]
        if self.obj == "NCE":
            self.P = F.normalize(protos.float().cpu(), dim=1).numpy()
        else:
            Xr = fd.es_rows(U); yr = fd.y_es
            sel = np.random.default_rng(rec["row"]["seed"] + 77).choice(len(Xr), size=min(6000, len(Xr)), replace=False)
            self.Xs, self.ys = torch.tensor(Xr[sel], dtype=torch.float64), torch.tensor(yr[sel], dtype=torch.float64)
            self.s2 = 2 * rec["objective_calibration"]["sigma_u"] ** 2; self.base = fd.base

    def __call__(self, Ux):
        if self.obj == "NCE":
            return ((Ux / np.linalg.norm(Ux, axis=1, keepdims=True)) @ self.P.T) @ np.array([-1.0, 1.0])
        K = torch.exp(-torch.cdist(torch.tensor(Ux, dtype=torch.float64), self.Xs).pow(2) / self.s2)
        q = np.clip(((K @ self.ys + self.base) / (K.sum(1) + 1.0)).numpy(), 1e-6, 1 - 1e-6)
        return np.log(q) - np.log1p(-q)


def md_sb_private(enc, protos, rec, fd, Z):
    from auditory_alignment_v3.aln3_reference.calibration import AffineLogitCalibrator
    kids = fd.kids; K = next(iter(Z.values())).shape[1]
    U = {i: pooled(enc, Z[i]) for i in Z}
    nat = Native(rec, protos, fd, U)
    S = {i: nat(U[i]) for i in U}
    cal = AffineLogitCalibrator.fit(fd.es_rows(S), fd.y_es)
    probe = Probe(fd.es_rows(U), fd.y_es)
    mean_tok = np.concatenate([Z[i][fd.es[i]] for i in fd.tr]).mean(0)
    W, WI = L.WINDOW_TOKENS["private_bdf"], L.WINDOW_TOKENS_INTERSECT["private_bdf"]
    sets = [[k] for k in range(K)] + [W["early"], W["late"], WI["early"], WI["late"]]  # + straddler sensitivity
    md = np.full((len(fd.te), len(sets), 2), np.nan); sb = md.copy(); full = np.full((len(fd.te), 2, 2), np.nan)
    for j, i in enumerate(fd.te):
        y = kids[i]["y"]
        a, n, _, _ = child_metrics(S[i], cal.predict(S[i]), y, fd.base)
        ps = probe.score(U[i]); a2, n2, _, _ = child_metrics(ps, probe.cal.predict(ps), y, fd.base)
        full[j] = [[a, n], [a2, n2]]

    def occ(z, ks):
        z = z.copy(); z[:, ks, :] = mean_tok[ks]; return z
    for c, ks in enumerate(sets):
        Uo = {i: pooled(enc, occ(Z[i], ks)) for i in Z}
        p2 = Probe(fd.es_rows(Uo), fd.y_es)
        for j, i in enumerate(fd.te):
            y = kids[i]["y"]; so = nat(Uo[i])
            a, n, _, _ = child_metrics(so, cal.predict(so), y, fd.base)
            md[j, c] = [full[j, 0, 0] - a, n - full[j, 0, 1]]  # AUC loss, NLL increase
            s2 = p2.score(Uo[i]); a2, n2, _, _ = child_metrics(s2, p2.cal.predict(s2), y, fd.base)
            sb[j, c] = [full[j, 1, 0] - a2, n2 - full[j, 1, 1]]
    return {"md": md, "sb": sb, "pooled_full": full}, nat, cal, U


def frozen_private(task, kids, fd):
    enc, protos, rec, bt = model_for(task, kids, trained=task.get("trained", True))
    idx = fd.tr + fd.te
    t0 = time.time()
    Z = {i: child_tokens(enc, bt, i) for i in idx}
    pos = torch.cat([br.pos.detach() for br in enc.branches]).numpy()
    X = {i: Z[i] - pos for i in Z}
    K = pos.shape[0]
    lag_rows = []
    for bi, (st, w) in enumerate(L.branch_starts(enc, [(a + bt.lo, b + bt.lo) for a, b in bt.W], rebase=L.PRE["private_bdf"])):
        for r in L.lag_table(st, w, 250, target_frames=1):
            r["branch"] = bi; lag_rows.append(r)
    log(task["key"], "tokens", len(Z), f"{time.time() - t0:.0f}s")
    res, _ = s1_lags(fd, X, K, task.get("tg", False))
    arrays = {"s1": res["s1"]}; meta = {"lags": lag_rows, "n_tokens": K, "windows_epoch": [(a + bt.lo, b + bt.lo) for a, b in bt.W]}
    if "tg" in res:
        arrays["tg"] = res["tg"]; meta["tg_diag_maxdiff"] = res["tg_diag_maxdiff"]
    if task.get("mdsb"):
        r2, nat, cal, U = md_sb_private(enc, protos, rec, fd, Z)
        arrays.update(r2)
        if task.get("chan"):
            ch = np.full((len(fd.te), 20, 2), np.nan)
            for c in range(20):
                for j, i in enumerate(fd.te):
                    y = kids[i]["y"]; so = nat(pooled(enc, child_tokens(enc, bt, i, zero_ch=c)))
                    a, n, _, _ = child_metrics(so, cal.predict(so), y, fd.base)
                    ch[j, c] = [r2["pooled_full"][j, 0, 0] - a, n - r2["pooled_full"][j, 0, 1]]
            arrays["chan_md"] = ch
    if task.get("filt"):
        W1 = enc.branches[0].local[0].weight.detach()[:, :, 0].numpy()
        Xs = np.concatenate([bt.Xall[bt.off[i]:bt.off[i + 1]].float().numpy()[fd.es[i]].transpose(0, 2, 1).reshape(-1, 20) for i in fd.tr])
        A1, en = filter_energy(W1, cov(Xs))
        arrays["filt_patterns"] = A1; arrays["filt_energy"] = en
    return arrays, meta


def raw_private(task, kids, fd):
    X = {}
    for i in fd.tr + fd.te:
        x = kids[i]["x"].astype(np.float16).astype(np.float32)  # same rounding as the fp16 batcher bank
        X[i] = np.stack([x[:, :, 50 + 5 * k: 60 + 5 * k].reshape(len(x), -1) for k in RAW_LAGS], 1)
    pos_idx = [j for j, k in enumerate(RAW_LAGS) if k >= 0]
    res, probes = s1_lags(fd, X, len(RAW_LAGS), False, fit_all=True)
    arrays = {"s1": res["s1"]}
    meta = {"lags": L.lag_table([5 * k for k in RAW_LAGS], 10, 250, target_frames=1), "raw_lag_index": RAW_LAGS}
    if task.get("tg"):
        Xp = {i: X[i][:, pos_idx] for i in X}
        rt, _ = s1_lags(fd, Xp, len(pos_idx), True, history=False)
        arrays["tg"] = rt["tg"]; meta["tg_diag_maxdiff"] = rt["tg_diag_maxdiff"]
    if task.get("haufe"):
        H = []
        for j in pos_idx:
            Xe = fd.es_rows({i: X[i][:, j] for i in X})
            H.append(haufe(cov(Xe), probes[j].w_input()).reshape(20, 10).astype(np.float32))
        arrays["haufe"] = np.stack(H)
    return arrays, meta


def save(key, arrays, meta, fd, task):
    os.makedirs(os.path.join(OUT, "private"), mode=0o700, exist_ok=True)
    base = os.path.join(OUT, "private", key)
    np.savez_compressed(base + ".tmp.npz", **arrays); os.replace(base + ".tmp.npz", base + ".npz")
    kids = fd.kids
    meta.update({"key": key, "task": task, "status": "complete", "children": [kids[i]["id"] for i in fd.te],
                 "groups": [kids[i]["group"] for i in fd.te], "n_trials": [int(len(kids[i]["y"])) for i in fd.te],
                 "common_support_fraction": [float(((fd.q0[kids[i]["bin"]] > 0.01) & (fd.q0[kids[i]["bin"]] < 0.99)).mean()) for i in fd.te],
                 "swap_strict_fraction": [float(kids[i].get("swap_strict_fraction", np.nan)) for i in fd.te],
                 "metrics": list(S1_METRICS), "host": os.uname().nodename, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    json.dump(meta, open(base + ".json.tmp", "w"), default=float); os.replace(base + ".json.tmp", base + ".json")


def run_job(job):
    from auditory_alignment import data
    todo = [t for t in job["tasks"] if not os.path.exists(os.path.join(OUT, "private", t["key"] + ".json"))]
    log("job", job["name"], "tasks", len(job["tasks"]), "todo", len(todo))
    if not todo:
        return 0
    t0 = time.time(); kids = data.load_private(); fd = Fold(kids, job["subject_fold"])
    log("private loaded", f"{time.time() - t0:.0f}s", "children", len(kids), "test", len(fd.te))
    nfail = 0
    for t in todo:
        t1 = time.time()
        try:
            arrays, meta = (raw_private if t["kind"] == "raw" else frozen_private)(t, kids, fd)
            meta["seconds"] = round(time.time() - t1, 1); save(t["key"], arrays, meta, fd, t)
            log("saved", t["key"], f"{time.time() - t1:.0f}s")
        except Exception as ex:  # noqa: BLE001
            nfail += 1
            os.makedirs(os.path.join(OUT, "private"), mode=0o700, exist_ok=True)
            json.dump({"key": t["key"], "task": t, "status": "failed", "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-4000:]},
                      open(os.path.join(OUT, "private", t["key"] + ".FAILED.json"), "w"))
            log("FAILED", t["key"], repr(ex))
    return nfail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(OUT, "plan.json"))
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    plan = json.load(open(a.plan))
    sys.exit(1 if run_job(next(j for j in plan["jobs"] if j["name"] == a.job)) else 0)


if __name__ == "__main__":
    main()
