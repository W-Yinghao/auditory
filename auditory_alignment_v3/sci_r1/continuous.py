"""FAU / DTU / Federici analyses for one job = (dataset, content fold, subject fold) (SCI_R1_PREREG §4-§7).

The cohort is loaded once with auditory_alignment_v2.run.load_cohort (as the units) into a CPU bank holding the fp16 EEG (as
Batcher.E) and the targets. Per unit the evaluation sets are rebuilt exactly as auditory_alignment.evaluate.evaluate_continuous
draws them from default_rng(seed + 1000): first the Readouts' 400 training-participant fit+es segments, then <= 300
training-participant es queries against the es pool; test pool, hard candidates (K = 8) and the held-out participants' test
queries in recording order; anchors on the dense grid (arange(0, seg_len, grid)). Only the representation changes:
  frozen   h_k = token_k - pos_k of the unit's encoder (TokenEncoder.forward_tokens)
  random   the same for the untrained encoder built right after torch.manual_seed(row seed) (the unit's initialisation)
  raw      the identical EEG samples of token k (fp16 bank), flattened [C * w]; rawpca: training-side z-score + PCA-32;
           rawneg: same width/step before the anchor (NEG_OFFS)
Per lag: RelRidge to the training-side standardised 8-frame target, es temperature, test metrics (readout.participant_metrics).
TG: the readout fitted at tau applied to the features at tau' (temperature recalibrated at tau' on the training-side es queries;
the fixed-temperature version and the temperature-free rank_gain are stored too). MD / SB: token occlusion with the training-row
mean token through the unit's own LN + projection, readout fixed (MD) or refitted (SB); channel occlusion (z-scored channel set
to 0 at test) with the pooled readout fixed. S3: Haufe patterns of the raw maps; first-layer spatial filter patterns.
Outputs (per-participant, private): private/auditory_alignment_v3/sci_r1/continuous/<key>.npz + .json; skip-if-done.
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

from auditory_alignment.data import AUDIO_FRAMES
from auditory_alignment_v2 import temporal as T2
from auditory_alignment_v2.train import TARGET
from auditory_alignment_v3 import core
from . import lags as L
from .readout import RelRidge, calibrate_tau, cand_matrix, channel_summary, cov, filter_energy, haufe, participant_metrics, unified_scores

OUT = os.path.join(core.OUT, "sci_r1")
V2_PLAN = os.path.join(core.REPO, "AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006", "plans", "planned_comparisons.jsonl")
METRICS = ("gain_bits", "rank_gain", "hard_gain_bits", "regular_logloss_bits", "mismatched_logloss_bits", "top1", "rank_pct", "top5", "mrr")
TG_CELLS = ("gain_bits", "gain_bits_tau_fixed", "rank_gain", "regular_logloss_bits")
CHUNK = 4096


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------------------------------------ data bank / evaluation sets
class Bank:
    """CPU copy of a loaded cohort: fp16 EEG (as Batcher.E), float32 targets; patches / audio exactly as Batcher."""

    def __init__(self, coh, targets):
        self.fs, self.seg_len, self.n_ch = coh.fs, coh.meta["seg_len"], coh.n_ch
        self.dataset = coh.meta["dataset"]
        self.segments, self.participants = coh.segments, coh.participants
        self.E = torch.tensor(coh.eeg, dtype=torch.float16)
        self.S = {t: torch.tensor(coh.stim[TARGET[t]]) for t in targets}
        self.zero_ch = None

    def patches(self, e_idx, W):
        e = torch.as_tensor(np.asarray(e_idx))
        out = [self.E[:, (e[:, None] + torch.arange(a, b)[None])].permute(1, 0, 2).float() for a, b in W]
        if self.zero_ch is not None:
            for p in out:
                p[:, self.zero_ch, :] = 0.0
        return out

    def raw(self, e_idx, start, w):
        e = torch.as_tensor(np.asarray(e_idx))
        return self.E[:, (e[:, None] + start + torch.arange(w)[None])].permute(1, 0, 2).float().flatten(1).numpy()

    def audio(self, s_idx, target):
        s = torch.as_tensor(np.asarray(s_idx))
        return self.S[target][:, (s[:, None] + torch.arange(AUDIO_FRAMES)[None])].permute(1, 0, 2).flatten(1).numpy()


def eval_sets(bank, sf, seed, K=8):
    """evaluate_continuous's sets and rng order (Readouts draw, then es queries) for subject fold sf and unit seed."""
    segs, parts = bank.segments, bank.participants
    train_p = {i for i, p in enumerate(parts) if not p.get("test_only") and (p.get("dev") or p["fold"] != sf)}
    train_segs = [s for s in segs if s["p"] in train_p and s["role"] in ("fit", "es") and s["kind"] == "ss"]
    rng = np.random.default_rng(seed + 1000)
    tr = [train_segs[i] for i in rng.choice(len(train_segs), size=min(400, len(train_segs)), replace=False)]

    def pool_of(role):
        uids, rows = {}, []
        for s in segs:
            if s["role"] == role and s["kind"] == "ss" and s["uid"] not in uids:
                uids[s["uid"]] = len(rows); rows.append(s)
        return uids, rows
    es_uid, es_rows = pool_of("es")
    q_es = [s for s in segs if s["p"] in train_p and s["role"] == "es" and s["kind"] == "ss"]
    q_es = [q_es[i] for i in rng.choice(len(q_es), size=min(300, len(q_es)), replace=False)] if q_es else []
    te_uid, te_rows = pool_of("test")
    feat = np.array([r["feat"] for r in te_rows]); feat = (feat - feat.mean(0)) / (feat.std(0) + 1e-12)
    hard = {}
    for j, r in enumerate(te_rows):
        el = [i for i, q in enumerate(te_rows) if q["hard_key"] == r["hard_key"] and q["part"] != r["part"]]
        if len(el) < K:
            el = [i for i in range(len(te_rows)) if i != j and te_rows[i]["part"] != r["part"]]
        dd = np.sqrt(((feat[el] - feat[j]) ** 2).sum(1))
        hard[j] = [el[i] for i in np.argsort(dd)[:K]]
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and (parts[s["p"]]["fold"] == sf or parts[s["p"]].get("test_only"))})
    queries, own, slices, ids, groups = [], [], [], [], []
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == "ss"]
        if not q:
            continue
        q = [q[i] for i in np.argsort([s["e0"] for s in q])]
        slices.append(slice(len(queries), len(queries) + len(q))); queries += q; own += [te_uid[s["uid"]] for s in q]
        ids.append(parts[p]["id"]); groups.append(parts[p]["group"])
    return {"train_p": train_p, "tr": tr, "roles": np.array([s["role"] for s in tr]), "q_es": q_es,
            "own_es": np.array([es_uid[s["uid"]] for s in q_es], int), "es_rows": es_rows, "te_rows": te_rows, "hard": hard,
            "queries": queries, "own": np.array(own, int), "slices": slices, "ids": ids, "groups": groups}


class Targets:
    """Training-side standardised 8-frame targets (Readouts.a_mu / a_sd) and candidate matrices of the es / test pools."""

    def __init__(self, bank, ev, target, offs):
        T = len(offs)
        A = bank.audio((np.array([s["s0"] for s in ev["tr"]])[:, None] + offs).ravel(), target).astype(np.float64)
        self.a_mu, self.a_sd = A.mean(0), A.std(0) + 1e-8
        self.Az = (A - self.a_mu) / self.a_sd
        self.D = A.shape[1]
        r = np.repeat(ev["roles"], T)
        self.fit, self.es = r == "fit", r == "es"

        def cm(rows):
            return cand_matrix(bank.audio((np.array([s["s0"] for s in rows])[:, None] + offs).ravel(), target).reshape(len(rows), T, -1), self.a_mu, self.a_sd)
        self.Zes = cm(ev["es_rows"]) if len(ev["es_rows"]) > 1 and len(ev["q_es"]) else None
        self.Zte = cm(ev["te_rows"])


def e_index(rows, offs):
    return (np.array([s["e0"] for s in rows])[:, None] + offs).ravel()


# ------------------------------------------------------------------------------------------------ scoring
class Scorer:
    """Unified-score evaluation of any per-anchor feature set given the evaluation sets and targets of one unit."""

    def __init__(self, ev, tg, T):
        self.ev, self.tg, self.T = ev, tg, T

    def fit(self, Xtr):
        return RelRidge(Xtr, self.tg.Az, self.tg.fit, self.tg.es)

    def tau(self, rr, Xes):
        if self.tg.Zes is None or Xes is None:
            return 1.0
        S = unified_scores(rr.predict(Xes).reshape(len(self.ev["q_es"]), self.T, -1), self.tg.Zes)
        return calibrate_tau(S, self.ev["own_es"])

    def test_scores(self, rr, Xte):
        return unified_scores(rr.predict(Xte).reshape(len(self.ev["queries"]), self.T, -1), self.tg.Zte)

    def per_participant(self, S, tau):
        ev = self.ev
        out = np.full((len(ev["slices"]), len(METRICS)), np.nan)
        for j, sl in enumerate(ev["slices"]):
            m = participant_metrics(S[sl], ev["own"][sl], ev["hard"], tau)
            out[j] = [m[k] for k in METRICS]
        return out


def rank_gain_only(S, ev):
    """temperature-free rank_gain per participant from a score matrix (for TG cells)."""
    out = np.empty(len(ev["slices"]))
    for j, sl in enumerate(ev["slices"]):
        s, own = S[sl], ev["own"][sl]
        n = s.shape[1]
        def rp(x):
            so = x[np.arange(len(x)), own]
            return ((x > so[:, None]).sum(1) / max(1, n - 1)).mean()
        out[j] = rp(np.roll(s, 1, axis=0)) - rp(s)
    return out


def gain_only(S, ev, tau, with_risk=False):
    """per-participant gain (mismatched - true logloss) and, optionally, the true-EEG logloss (risk R)."""
    out = np.empty(len(ev["slices"])); risk = np.empty(len(ev["slices"]))
    for j, sl in enumerate(ev["slices"]):
        s, own = S[sl], ev["own"][sl]
        def ll(x):
            z = x / tau; z = z - z.max(1, keepdims=True)
            return ((np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]) / np.log(2)).mean()
        r = ll(s); out[j] = ll(np.roll(s, 1, axis=0)) - r; risk[j] = r
    return (out, risk) if with_risk else out


# ------------------------------------------------------------------------------------------------ models
def load_row(task):
    if task["source"] == "aln3":
        from auditory_alignment_v3 import run as r3
        row = next(r for r in r3.all_rows() if r["experiment_id"] == task["eid"])
        return row, core.bind(row), int(row["spec"].get("projection_dim", 32)), core.OUT
    row = next(json.loads(l) for l in open(V2_PLAN) if json.loads(l)["experiment_id"] == task["eid"])
    return row, row, 16, core.V2_OUT


def build_model(task, bank, trained=True):
    """trained: the unit's encoder from its checkpoint. Untrained (P2): the same architecture built right after
    torch.manual_seed(task seed) - identical to the initialisation of every unit with that seed (fold / objective free)."""
    row, b, d, out = load_row(task)
    row = dict(row, seed=task.get("seed", row["seed"]), subject_fold=task.get("sf", row["subject_fold"]))
    sp = b["spec"]
    W = T2.window_ranges(sp["architecture"], bank.dataset, sp["window"], bank.fs)
    rec = json.load(open(os.path.join(out, "units", f"{task['eid']}.json")))
    if trained and rec.get("status") != "complete":
        raise RuntimeError(f"unit record status {rec.get('status')}")
    if "windows_samples" in rec and [list(w) for w in rec["windows_samples"]] != [list(w) for w in W]:
        raise RuntimeError(f"window mismatch {rec['windows_samples']} vs {W}")
    torch.manual_seed(row["seed"])
    enc = T2.build_encoder(sp["architecture"], bank.n_ch, d, W, bank.fs)
    if trained:
        sd = torch.load(os.path.join(out, "ckpt", f"{task['eid']}_best.pt"), map_location="cpu", weights_only=False)
        enc.load_state_dict(sd["enc"], strict=True)
    enc.eval()
    return row, b, enc, W


@torch.no_grad()
def tokens(enc, bank, W, e_idx):
    out = []
    for k in range(0, len(e_idx), CHUNK):
        out.append(enc.forward_tokens(bank.patches(e_idx[k:k + CHUNK], W)).numpy())
    return np.concatenate(out)


@torch.no_grad()
def pooled(enc, Z):
    out = []
    for k in range(0, len(Z), CHUNK):
        z = torch.as_tensor(Z[k:k + CHUNK])
        out.append(F.normalize(enc.proj(z.flatten(1)), dim=1).numpy())
    return np.concatenate(out)


# ------------------------------------------------------------------------------------------------ analyses
def s1_tg(sc, feats, n_lags, do_tg, label):
    """feats(set, k) -> [N, p] features of lag k for set in ('tr', 'es', 'te'). Returns S1a metrics [P, K, M], readout info,
    and (optionally) TG arrays [P, K, K] x (gain recal, gain fixed tau, rank_gain)."""
    ev = sc.ev; P = len(ev["slices"])
    s1 = np.full((P, n_lags, len(METRICS)), np.nan); info = []
    rr_all, tau_all = [], []
    for k in range(n_lags):
        rr = sc.fit(feats("tr", k)); tau = sc.tau(rr, feats("es", k))
        S = sc.test_scores(rr, feats("te", k))
        s1[:, k] = sc.per_participant(S, tau)
        info.append({"lam": rr.lam, "alpha": rr.alpha, "on_edge": rr.on_edge, "tau": tau, "es_r_curve": rr.curve})
        rr_all.append(rr); tau_all.append(tau)
    out = {"s1": s1, "info": info}
    if do_tg:
        tg = np.full((P, n_lags, n_lags, len(TG_CELLS)), np.nan)
        for k2 in range(n_lags):  # tau' outer: one lag's features in memory at a time
            Xes, Xte = feats("es", k2), feats("te", k2)
            for k1 in range(n_lags):
                rr = rr_all[k1]
                S = sc.test_scores(rr, Xte)
                tau2 = sc.tau(rr, Xes) if k1 != k2 else tau_all[k1]
                tg[:, k1, k2, 0], tg[:, k1, k2, 3] = gain_only(S, ev, tau2, with_risk=True)
                tg[:, k1, k2, 1] = gain_only(S, ev, tau_all[k1])
                tg[:, k1, k2, 2] = rank_gain_only(S, ev)
        out["tg"] = tg
        out["tg_diag_maxdiff"] = float(max(np.nanmax(np.abs(np.diagonal(tg[..., 0], axis1=1, axis2=2) - s1[:, :, 0])),
                                           np.nanmax(np.abs(np.diagonal(tg[..., 3], axis1=1, axis2=2) - s1[:, :, METRICS.index("regular_logloss_bits")]))))
    log(label, "S1" + ("+TG" if do_tg else ""), "edges", sum(i["on_edge"] for i in info), "/", n_lags)
    return out, rr_all, tau_all


def frozen_analysis(task, bank, ev_cache, tg_cache):
    row, b, enc, W = build_model(task, bank, trained=task.get("trained", True))
    sp = b["spec"]; seed = row["seed"]; sf = row["subject_fold"]
    g = core.grid_samples(bank.fs); offs = np.arange(0, bank.seg_len, g); T = len(offs)
    ev = ev_cache.get((sf, seed)) or ev_cache.setdefault((sf, seed), eval_sets(bank, sf, seed))
    tkey = (sf, seed, sp["target"])
    tg = tg_cache.get(tkey) or tg_cache.setdefault(tkey, Targets(bank, ev, sp["target"], offs))
    sc = Scorer(ev, tg, T)
    t0 = time.time()
    Z = {"tr": tokens(enc, bank, W, e_index(ev["tr"], offs)), "es": tokens(enc, bank, W, e_index(ev["q_es"], offs)) if ev["q_es"] else None,
         "te": tokens(enc, bank, W, e_index(ev["queries"], offs))}
    pos = torch.cat([br.pos.detach() for br in enc.branches]).numpy()
    starts = L.branch_starts(enc, W)
    K = pos.shape[0]
    lag_rows = []
    for bi, (st, w) in enumerate(starts):
        for r in L.lag_table(st, w, bank.fs):
            r["branch"] = bi; lag_rows.append(r)
    feats = lambda s, k: None if Z[s] is None else Z[s][:, k, :] - pos[k]
    log(task["key"], "tokens", {s: None if v is None else v.shape for s, v in Z.items()}, f"{time.time() - t0:.0f}s")
    res, rr_all, tau_all = s1_tg(sc, feats, K, task.get("tg", False), task["key"])
    arrays = {"s1": res["s1"]}
    meta = {"lags": lag_rows, "readout": res["info"], "windows": W, "n_tokens": K}
    if "tg" in res:
        arrays["tg"] = res["tg"]; meta["tg_diag_maxdiff"] = res["tg_diag_maxdiff"]
    if task.get("mdsb"):
        assert sp["window"] == "full", "MD/SB windows are defined on full-window token indices"
        arrays.update(md_sb(enc, Z, sc, bank, K, task["key"]))
    if task.get("chan"):
        arrays["chan_md"] = channel_occlusion(enc, Z, sc, bank, W, offs, task["key"])
    if task.get("filt"):
        W1 = enc.branches[0].local[0].weight.detach()[:, :, 0].numpy()
        Sch = channel_cov(bank, ev, W)
        A1, en = filter_energy(W1, Sch)
        arrays["filt_patterns"] = A1; arrays["filt_energy"] = en
    return arrays, meta, ev


def channel_cov(bank, ev, W):
    """Channel covariance of the training rows' EEG, each sample once (the 400 readout segments, [e0, e0 + seg_len))."""
    idx = np.unique((np.array([s["e0"] for s in ev["tr"]])[:, None] + np.arange(bank.seg_len)[None]).ravel())
    X = bank.E[:, torch.as_tensor(idx)].float().numpy().T
    return cov(X)


def md_sb(enc, Z, sc, bank, K, key):
    """MD (readout fixed, test tokens occluded) and SB (all sets occluded, readout and temperature refitted) for each lag and
    for the protocol windows; columns 0..K-1 lags, K / K+1 tokens fully inside early / late, K+2 / K+3 tokens touching early /
    late (straddlers included; sensitivity); last axis (gain loss, risk increase). Also the full pooled-u per-participant metrics."""
    ev = sc.ev
    mean_tok = Z["tr"].mean(0)  # [K, 32] training-row mean token (incl. pos)
    U = {s: pooled(enc, v) if v is not None else None for s, v in Z.items()}
    rr = sc.fit(U["tr"]); tau = sc.tau(rr, U["es"]) if U["es"] is not None else 1.0
    full = sc.per_participant(sc.test_scores(rr, U["te"]), tau)
    sets = [[k] for k in range(K)] + [L.WINDOW_TOKENS[bank.dataset]["early"], L.WINDOW_TOKENS[bank.dataset]["late"],
                                      L.WINDOW_TOKENS_INTERSECT[bank.dataset]["early"], L.WINDOW_TOKENS_INTERSECT[bank.dataset]["late"]]
    md = np.full((len(ev["slices"]), len(sets), 2), np.nan); sb = md.copy()  # [..., 0] gain loss, [..., 1] risk increase

    def occ(v, ks):
        z = v.copy(); z[:, ks, :] = mean_tok[ks]; return pooled(enc, z)
    for j, ks in enumerate(sets):
        Ute = occ(Z["te"], ks)
        g, r = gain_only(sc.test_scores(rr, Ute), ev, tau, with_risk=True)
        md[:, j, 0] = full[:, 0] - g; md[:, j, 1] = r - full[:, METRICS.index("regular_logloss_bits")]
        Utr = occ(Z["tr"], ks); Ues = occ(Z["es"], ks) if Z["es"] is not None else None
        r2 = sc.fit(Utr); t2 = sc.tau(r2, Ues) if Ues is not None else 1.0
        g, r = gain_only(sc.test_scores(r2, Ute), ev, t2, with_risk=True)
        sb[:, j, 0] = full[:, 0] - g; sb[:, j, 1] = r - full[:, METRICS.index("regular_logloss_bits")]
    log(key, "MD/SB done")
    return {"pooled_full": full, "md": md, "sb": sb, "pooled_lam": np.array([rr.lam, float(rr.on_edge), tau])}


@torch.no_grad()
def channel_occlusion(enc, Z, sc, bank, W, offs, key):
    """per channel: test queries with the z-scored channel set to 0 (its training-side mean) over the whole input window;
    pooled-u readout and temperature fixed; value = gain(full) - gain(channel occluded)."""
    ev = sc.ev
    U = {s: pooled(enc, v) if v is not None else None for s, v in Z.items()}
    rr = sc.fit(U["tr"]); tau = sc.tau(rr, U["es"]) if U["es"] is not None else 1.0
    g_full = gain_only(sc.test_scores(rr, U["te"]), ev, tau)
    out = np.full((len(ev["slices"]), bank.n_ch), np.nan)
    e = e_index(ev["queries"], offs)
    for c in range(bank.n_ch):
        bank.zero_ch = c
        try:
            Uc = pooled(enc, tokens(enc, bank, W, e))
        finally:
            bank.zero_ch = None
        out[:, c] = g_full - gain_only(sc.test_scores(rr, Uc), ev, tau)
    log(key, "channel occlusion done")
    return out


def raw_analysis(task, bank, ev_cache, tg_cache):
    """Raw strict-local linear reference for (sf, seed, target): positive lags with the full-window token supports
    (+ TG, Haufe), negative-lag controls, PCA-32 capacity-matched variant."""
    sf, seed, target = task["sf"], task["seed"], task["target"]
    g = core.grid_samples(bank.fs); offs = np.arange(0, bank.seg_len, g); T = len(offs)
    ev = ev_cache.get((sf, seed)) or ev_cache.setdefault((sf, seed), eval_sets(bank, sf, seed))
    tkey = (sf, seed, target)
    tg = tg_cache.get(tkey) or tg_cache.setdefault(tkey, Targets(bank, ev, target, offs))
    sc = Scorer(ev, tg, T)
    W = T2.window_ranges("lag_local_tokens", bank.dataset, "full", bank.fs)
    torch.manual_seed(0)
    (starts, w), = L.branch_starts(T2.build_encoder("lag_local_tokens", bank.n_ch, 32, W, bank.fs), W)
    E = {"tr": e_index(ev["tr"], offs), "es": e_index(ev["q_es"], offs) if ev["q_es"] else None, "te": e_index(ev["queries"], offs)}
    arrays, meta = {}, {"lags": L.lag_table(starts, w, bank.fs), "neg_lags": L.lag_table(L.NEG_OFFS[bank.dataset], w, bank.fs), "w": w}
    feats = lambda s, k: None if E[s] is None else bank.raw(E[s], starts[k], w)
    res, rr_all, _ = s1_tg(sc, feats, len(starts), task.get("tg", False), task["key"] + " raw")
    arrays["s1"] = res["s1"]; meta["readout"] = res["info"]
    if "tg" in res:
        arrays["tg"] = res["tg"]; meta["tg_diag_maxdiff"] = res["tg_diag_maxdiff"]
    if task.get("haufe"):
        H, chan = [], []
        for k, rr in enumerate(rr_all):
            A = haufe(cov(feats("tr", k)), rr.B[:-1]); H.append(A.astype(np.float32)); chan.append(channel_summary(A, bank.n_ch))
        arrays["haufe"] = np.stack(H); arrays["haufe_chan"] = np.stack(chan)
    if task.get("neg"):
        negf = lambda s, k: None if E[s] is None else bank.raw(E[s], L.NEG_OFFS[bank.dataset][k], w)
        rn, _, _ = s1_tg(sc, negf, len(L.NEG_OFFS[bank.dataset]), False, task["key"] + " rawneg")
        arrays["s1_neg"] = rn["s1"]; meta["readout_neg"] = rn["info"]
    if task.get("pca"):
        pcs = {}
        def pcaf(s, k):
            if k not in pcs:
                X = feats("tr", k).astype(np.float64); mu, sd = X.mean(0), X.std(0) + 1e-8
                ev_, V = np.linalg.eigh(np.cov(((X - mu) / sd).T)); pcs.clear(); pcs[k] = (mu, sd, V[:, ::-1][:, :32])
            mu, sd, V = pcs[k]
            X = feats(s, k)
            return None if X is None else ((X - mu) / sd) @ V
        rp, _, _ = s1_tg(sc, pcaf, len(starts), False, task["key"] + " rawpca")
        arrays["s1_pca"] = rp["s1"]; meta["readout_pca"] = rp["info"]
    return arrays, meta, ev


# ------------------------------------------------------------------------------------------------ job driver
def save(key, arrays, meta, ev, task):
    os.makedirs(os.path.join(OUT, "continuous"), mode=0o700, exist_ok=True)
    base = os.path.join(OUT, "continuous", key)
    np.savez_compressed(base + ".tmp.npz", **arrays)
    os.replace(base + ".tmp.npz", base + ".npz")
    meta.update({"key": key, "task": task, "status": "complete", "participants": ev["ids"], "groups": ev["groups"], "tg_cells": list(TG_CELLS),
                 "n_queries": [sl.stop - sl.start for sl in ev["slices"]], "query_parts": [[str(s["part"]) for s in ev["queries"][sl]] for sl in ev["slices"]],
                 "metrics": list(METRICS), "host": os.uname().nodename,
                 "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    json.dump(meta, open(base + ".json.tmp", "w"), default=float); os.replace(base + ".json.tmp", base + ".json")


def run_job(job):
    from auditory_alignment_v2.run import load_cohort
    todo = [t for t in job["tasks"] if not os.path.exists(os.path.join(OUT, "continuous", t["key"] + ".json"))]
    log("job", job["name"], "tasks", len(job["tasks"]), "todo", len(todo))
    if not todo:
        return 0
    t0 = time.time()
    if job.get("loader") == "fau_noica":
        from .fau_noica import load_fau
        coh = load_fau(job["content_fold"], kinds=("ss", "cs"), key="eeg_1_20_noica")
    else:
        coh = load_cohort({"dataset": job["dataset"], "content_fold": job["content_fold"]})
    targets = sorted({t["target"] for t in todo})
    bank = Bank(coh, targets); del coh
    log("cohort loaded", f"{time.time() - t0:.0f}s", "E", tuple(bank.E.shape))
    ev_cache, tg_cache = {}, {}
    nfail = 0
    for t in todo:
        t1 = time.time()
        try:
            arrays, meta, ev = (raw_analysis if t["kind"] == "raw" else frozen_analysis)(t, bank, ev_cache, tg_cache)
            meta["seconds"] = round(time.time() - t1, 1)
            save(t["key"], arrays, meta, ev, t)
            log("saved", t["key"], f"{time.time() - t1:.0f}s")
        except Exception as ex:  # noqa: BLE001 - recorded with a reason, never silently dropped
            nfail += 1
            os.makedirs(os.path.join(OUT, "continuous"), mode=0o700, exist_ok=True)
            json.dump({"key": t["key"], "task": t, "status": "failed", "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-4000:]},
                      open(os.path.join(OUT, "continuous", t["key"] + ".FAILED.json"), "w"))
            log("FAILED", t["key"], repr(ex))
    return nfail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(OUT, "plan.json"))
    ap.add_argument("--job", required=True)
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    plan = json.load(open(a.plan))
    job = next(j for j in plan["jobs"] if j["name"] == a.job)
    sys.exit(1 if run_job(job) else 0)


if __name__ == "__main__":
    main()
