"""Engineering checks E1-E6 (SCI_R1_PREREG §10). Stores and prints QC numbers only (differences, counts, flags, null-control
means); no real per-participant score or aggregate is printed. Output: private/auditory_alignment_v3/sci_r1/checks/.
  E1a  unchanged core.evaluate_grid on CPU vs the stored per-participant unified / native gain; readout alpha / tau vs record
       (P1: one ALN2 A_TIME unit with the unchanged ALN2 evaluation at stride 4); private: calib.private_variants vs stored
  E1b  this module's evaluation sets + scoring on pooled u with the ORIGINAL ridge (absolute grid, float32) vs E1a (CPU, tight)
       and vs the record; private: probe code on unstandardised u, LogisticRegression(C=1) -> head_auc / hist_gain_bits vs record
  E2   token starts / window token sets / straddlers vs lags tables; record windows; untrained build reproducible; negative-lag
       slices inside their trial / block / epoch; channel-name attributes vs foundation_adapter.CHANNELS (E2b)
  E3   TG diagonal == S1a (gain and risk; max |diff| must be 0)
  E4   training targets shuffled across segments / training labels permuted: null-control mean
  E5   S1a recomputed twice: bit-identical
  E6   share of lags whose lam sits on the extended-grid edge (expected, harmless under the correlation criterion)
Usage: python -m auditory_alignment_v3.sci_r1.probe --dataset federici --eids P0a P0b [--aln2 P1eid]
       python -m auditory_alignment_v3.sci_r1.probe --dataset private_bdf --fold 0 --eids P0a P0b
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import re
import time

import numpy as np
import torch

from auditory_alignment_v3 import core
from . import continuous as C
from . import lags as L

QC = os.path.join(C.OUT, "checks")


class RidgeEv1:
    """auditory_alignment.evaluate Readouts' unified ridge (absolute grid logspace(-4, 8, 13), float32 inputs)."""

    def __init__(self, X, Y, fit, es, alpha=None):
        from auditory_alignment.evaluate import _ridge
        X = np.asarray(X, np.float32); Y = np.asarray(Y, np.float32)
        a = alpha if alpha is not None else _ridge(X[fit], Y[fit], np.logspace(-4, 8, 13), X[es], Y[es], crit="corr")[1]
        self.B = _ridge(X, Y, [a])[0]; self.alpha = self.lam = float(a); self.on_edge = a in (1e-4, 1e8); self.curve = {}

    def predict(self, X):
        from auditory_alignment.evaluate import _apply
        return _apply(self.B, np.asarray(X, np.float32))


class Ev1Scorer(C.Scorer):
    alpha = None
    tau_forced = None

    def fit(self, Xtr):
        return RidgeEv1(Xtr, self.tg.Az32, self.tg.fit, self.tg.es, alpha=self.alpha)

    def tau(self, rr, Xes):
        from auditory_alignment.evaluate import _zt
        if self.tau_forced is not None:
            return self.tau_forced
        if self.tg.Zes is None or Xes is None:
            return 1.0
        P = rr.predict(Xes).reshape(len(self.ev["q_es"]), self.T, -1)
        S = np.einsum("qtd,ctd->qc", _zt(P), self.tg.C32_es) / (P.shape[1] * P.shape[2])
        return C.calibrate_tau(S, self.ev["own_es"])

    def test_scores(self, rr, Xte):
        from auditory_alignment.evaluate import _zt
        P = rr.predict(Xte).reshape(len(self.ev["queries"]), self.T, -1)
        return np.einsum("qtd,ctd->qc", _zt(P), self.tg.C32_te) / (P.shape[1] * P.shape[2])


def ev1_targets(bank, ev, target, offs):
    """Targets plus the float32 versions used by the original Readouts (a_mu / a_sd from float32 A, C = (Ac - mu) / sd)."""
    from auditory_alignment.evaluate import _zt
    tg = C.Targets(bank, ev, target, offs)
    T = len(offs)
    A = bank.audio((np.array([s["s0"] for s in ev["tr"]])[:, None] + offs).ravel(), target)
    mu, sd = A.mean(0), A.std(0) + 1e-8
    tg.Az32 = (A - mu) / sd

    def c32(rows):
        Ac = bank.audio((np.array([s["s0"] for s in rows])[:, None] + offs).ravel(), target).reshape(len(rows), T, -1)
        return _zt((Ac - mu) / sd)
    tg.C32_es = c32(ev["es_rows"]) if tg.Zes is not None else None
    tg.C32_te = c32(ev["te_rows"])
    return tg


def W_of(sp, bank):
    return C.T2.window_ranges(sp["architecture"], bank.dataset, sp["window"], bank.fs)


def channel_names_check(ds):
    """E2b: per-file channel attributes identical across participants and equal to foundation_adapter.CHANNELS."""
    import h5py
    from auditory_alignment import data as D
    from auditory_alignment_v2.foundation_adapter import CHANNELS
    files = {"fau": sorted(glob.glob(os.path.join(D.STAGEB, "*", "*.h5"))), "dtu": sorted(glob.glob(os.path.join(D.DTU_PRE, "*.h5"))),
             "federici": sorted(glob.glob(os.path.join(D.FED_PRE, "*", "*.h5")))}.get(ds, [])
    seen, missing = set(), 0
    for p in files:
        with h5py.File(p, "r") as f:
            ch = f.attrs.get("channels")
            if ch is None and "channels" in f:
                ch = f["channels"][()]
            if ch is None:
                missing += 1; continue
            seen.add(tuple(str(c.decode() if isinstance(c, bytes) else c) for c in ch))
    n = len(CHANNELS[ds])
    return {"files": len(files), "files_without_channel_names": missing, "distinct_channel_lists": len(seen),
            "equal_to_table": [list(s)[:n] == list(CHANNELS[ds]) for s in seen]}


def neg_lag_check(bank):
    """negative-lag slices stay inside their trial / block: segment start offset (from the uid) + min offset >= 0."""
    st = [int(s["uid"].rsplit("@", 1)[1]) for s in bank.segments]
    return {"min_segment_start": int(min(st)), "min_neg_offset": int(min(L.NEG_OFFS[bank.dataset])),
            "ok": bool(min(st) + min(L.NEG_OFFS[bank.dataset]) >= 0), "touches_start": bool(min(st) + min(L.NEG_OFFS[bank.dataset]) == 0)}


def continuous_probe(ds, eids, aln2=None):
    from auditory_alignment.aggregate import unit_rows
    from auditory_alignment_v2.audio_targets import build_head
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v3 import run as r3
    from auditory_alignment_v3.local_train import GridBatcher
    rows = {r["experiment_id"]: r for r in r3.all_rows() if r["experiment_id"] in eids}
    cf = rows[eids[0]]["content_fold"] or 0
    t0 = time.time(); coh = load_cohort({"dataset": ds, "content_fold": cf})
    eeg, stim = coh.eeg, coh.stim
    print("cohort", ds, f"{time.time() - t0:.0f}s", flush=True)
    qc = {"dataset": ds, "content_fold": cf, "units": {}, "E2b_channels": channel_names_check(ds)}
    bank = C.Bank(coh, sorted({core.bind(rows[e])["spec"]["target"] for e in eids}))
    coh.eeg, coh.stim = eeg, stim
    qc["E2_negative_lags"] = neg_lag_check(bank)
    g = core.grid_samples(coh.fs); offs = np.arange(0, bank.seg_len, g); T = len(offs)
    for eid in eids:
        row = rows[eid]; b = core.bind(row); sp = b["spec"]; d = int(row["spec"].get("projection_dim", 32))
        rec = json.load(open(os.path.join(core.OUT, "units", f"{eid}.json")))
        stored = unit_rows(rec); q = {}
        # E1a: unchanged evaluation on CPU
        coh.eeg, coh.stim = eeg, stim
        bt = GridBatcher(coh, sp, b, torch.device("cpu"), g)
        enc = C.T2.build_encoder(sp["architecture"], coh.n_ch, d, bt.W, coh.fs)
        sd = torch.load(os.path.join(core.OUT, "ckpt", f"{eid}_best.pt"), map_location="cpu", weights_only=False)
        enc.load_state_dict(sd["enc"]); enc.eval()
        head = build_head("fixed_features", bt.audio_dim, d, ds, (torch.zeros(bt.audio_dim), torch.ones(bt.audio_dim)))
        head.load_state_dict(sd["head"]); head.eval()
        t1 = time.time()
        with torch.no_grad():
            ev_new = core.evaluate_grid(b, enc, head, bt, coh, rec["objective_calibration"], g)
        new = unit_rows({"eval": ev_new})
        for m in ("unified/gain_bits", "native/gain_bits", "unified/regular/logloss_bits"):
            q[f"E1a_maxabs_{m}"] = max(abs(new[p][m] - stored[p][m]) for p in stored)
        q["E1a_same_participants"] = sorted(stored) == sorted(new)
        ro_new, ro_old = ev_new["readout"], rec["eval"]["readout"]
        q["E1a_alpha_match"] = ro_new["alpha_unified"] == ro_old["alpha_unified"]
        q["E1a_tau_unified_reldiff"] = abs(ro_new["tau"]["unified"] - ro_old["tau"]["unified"]) / ro_old["tau"]["unified"]
        q["E1a_seconds"] = round(time.time() - t1)
        del bt
        coh.eeg, coh.stim = eeg, stim
        # E1b: this module's sets + original ridge on pooled u
        ev = C.eval_sets(bank, row["subject_fold"], row["seed"])
        tg = ev1_targets(bank, ev, sp["target"], offs)
        W = W_of(sp, bank)
        Z = {"tr": C.tokens(enc, bank, W, C.e_index(ev["tr"], offs)), "es": C.tokens(enc, bank, W, C.e_index(ev["q_es"], offs)),
             "te": C.tokens(enc, bank, W, C.e_index(ev["queries"], offs))}
        U = {s: C.pooled(enc, v) for s, v in Z.items()}
        sc = Ev1Scorer(ev, tg, T)
        rr = sc.fit(U["tr"]); tau = sc.tau(rr, U["es"])
        mine = sc.per_participant(sc.test_scores(rr, U["te"]), tau)
        ix = {m: C.METRICS.index(m) for m in C.METRICS}
        def cmp(ref):
            d1 = max(abs(mine[j, ix["regular_logloss_bits"]] - ref[p]["unified/regular/logloss_bits"]) for j, p in enumerate(ev["ids"]))
            d2 = max(abs(mine[j, ix["mismatched_logloss_bits"]] - ref[p]["unified/mismatched_eeg/logloss_bits"]) for j, p in enumerate(ev["ids"]))
            d3 = max(abs((np.log2(9) - mine[j, ix["hard_gain_bits"]]) - ref[p]["unified/hard/logloss_bits"]) for j, p in enumerate(ev["ids"]))
            d4 = max(abs(mine[j, ix["rank_pct"]] - ref[p]["unified/regular/rank_pct"]) for j, p in enumerate(ev["ids"]))
            return {"regular": d1, "mismatched": d2, "hard": d3, "rank_pct": d4}
        q["E1b_vs_E1a_cpu_maxabs"] = cmp(new)
        q["E1b_vs_record_maxabs"] = cmp(stored)
        q["E1b_alpha_matches_cpu_eval"] = rr.alpha == ro_new["alpha_unified"]
        q["E1b_tau_reldiff_cpu_eval"] = abs(tau - ro_new["tau"]["unified"]) / ro_new["tau"]["unified"]
        q["E1b_participants_match"] = sorted(ev["ids"]) == sorted(stored)
        if not q["E1a_alpha_match"] or q["E1a_tau_unified_reldiff"] > 1e-6:  # discrete flip GPU -> CPU: rerun with the record's alpha / tau
            sc.alpha, sc.tau_forced = ro_old["alpha_unified"], ro_old["tau"]["unified"]
            rr = sc.fit(U["tr"]); mine = sc.per_participant(sc.test_scores(rr, U["te"]), sc.tau(rr, U["es"]))
            q["E1b_forced_record_alpha_tau_vs_record_maxabs"] = cmp(stored)
        # E2
        starts, w = L.branch_starts(enc, W)[0]
        q["E2_window_tokens_ok"] = all(L.tokens_in_window(starts, w, ds, wn) == L.WINDOW_TOKENS[ds][wn] for wn in ("early", "late"))
        q["E2_straddler_sets_ok"] = all(L.tokens_touching_window(starts, w, ds, wn) == L.WINDOW_TOKENS_INTERSECT[ds][wn] for wn in ("early", "late"))
        q["E2_record_windows_match"] = [list(x) for x in rec.get("windows_samples", W)] == [list(x) for x in W]
        torch.manual_seed(row["seed"]); e1 = C.T2.build_encoder(sp["architecture"], coh.n_ch, d, W, coh.fs)
        torch.manual_seed(row["seed"]); e2 = C.T2.build_encoder(sp["architecture"], coh.n_ch, d, W, coh.fs)
        q["E2_untrained_build_reproducible"] = all(torch.equal(x, y) for x, y in zip(e1.state_dict().values(), e2.state_dict().values()))
        # E3 / E5 / E6 on frozen tokens (relative ridge)
        tgr = C.Targets(bank, ev, sp["target"], offs); scr = C.Scorer(ev, tgr, T)
        pos = torch.cat([br.pos.detach() for br in enc.branches]).numpy()
        feats = lambda s, k: Z[s][:, k, :] - pos[k]
        r1, _, _ = C.s1_tg(scr, feats, pos.shape[0], True, eid)
        r2, _, _ = C.s1_tg(scr, feats, pos.shape[0], False, eid)
        q["E3_tg_diag_maxdiff"] = r1["tg_diag_maxdiff"]
        q["E5_bit_identical"] = bool(np.array_equal(r1["s1"], r2["s1"], equal_nan=True))
        q["E6_edge_share"] = float(np.mean([i["on_edge"] for i in r1["info"]]))
        q["E6_lams"] = sorted({float(i["lam"]) for i in r1["info"]})
        # E4: shuffled training targets (segment-level permutation)
        tgs = copy.copy(tgr)
        perm = np.random.default_rng(0).permutation(len(ev["tr"]))
        tgs.Az = tgr.Az.reshape(len(ev["tr"]), T, -1)[perm].reshape(-1, tgr.D)
        rs, _, _ = C.s1_tg(C.Scorer(ev, tgs, T), feats, pos.shape[0], False, eid + " shuffled")
        q["E4_shuffled_mean_gain_per_lag_maxabs"] = float(np.abs(np.nanmean(rs["s1"][:, :, 0], axis=0)).max())
        q["E4_shuffled_mean_gain_overall"] = float(np.nanmean(rs["s1"][:, :, 0]))
        qc["units"][eid] = q
        print(eid, json.dumps(q, default=float), flush=True)
    if aln2:
        qc["aln2"] = aln2_probe(aln2, coh, eeg, stim)
    return qc


def aln2_probe(eid, coh, eeg, stim):
    """E1a for one ALN2 A_TIME unit: unchanged ALN2 batcher + evaluation (stride 4) on CPU vs the stored ALN2 record."""
    from auditory_alignment.aggregate import unit_rows
    from auditory_alignment_v2 import evaluate as ev2
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.train import Batcher
    row = next(json.loads(l) for l in open(C.V2_PLAN) if json.loads(l)["experiment_id"] == eid)
    rec = json.load(open(os.path.join(core.V2_OUT, "units", f"{eid}.json")))
    sp = row["spec"]
    coh.eeg, coh.stim = eeg, stim
    bt = Batcher(coh, sp, row, torch.device("cpu"))
    enc = C.T2.build_encoder(sp["architecture"], coh.n_ch, 16, bt.W, coh.fs)
    sd = torch.load(os.path.join(core.V2_OUT, "ckpt", f"{eid}_best.pt"), map_location="cpu", weights_only=False)
    enc.load_state_dict(sd["enc"]); enc.eval()
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head(sp.get("audio_head", "trainable_head"), bt.audio_dim, 16, coh.meta["dataset"], stats)
    head.load_state_dict(sd["head"]); head.eval()
    with torch.no_grad():
        new = unit_rows({"eval": ev2.evaluate_continuous(row, enc, head, bt, coh, rec["objective_calibration"], None)})
    old = unit_rows(rec)
    coh.eeg, coh.stim = eeg, stim
    out = {"eid": eid, "E1a_maxabs_unified_gain": max(abs(new[p]["unified/gain_bits"] - old[p]["unified/gain_bits"]) for p in old),
           "same_participants": sorted(new) == sorted(old), "audio_head": sp.get("audio_head", "trainable_head")}
    print("ALN2", json.dumps(out, default=float), flush=True)
    return out


def private_probe(sf, eids):
    from sklearn.linear_model import LogisticRegression
    from auditory_alignment import data
    from auditory_alignment_v3 import calib, private_stage
    from auditory_c3.c3dl_stage0 import _fit_offset_logistic
    from . import private_task as P
    kids = data.load_private(); fd = P.Fold(kids, sf)
    qc = {"dataset": "private_bdf", "fold": sf, "units": {}}
    for eid in eids:
        q = {}
        enc, protos, rec, bt = private_stage.rebuild(eid, kids, torch.device("cpu"))
        row = rec["row"]; b = core.bind(row)
        new = calib.private_variants(b, enc, bt, protos, rec["objective_calibration"])
        old = rec["eval"]["native_calibration"]["per_participant"]
        for m in ("auc_score", "nll_bits"):
            q[f"E1a_maxabs_positive_affine_{m}"] = max(abs(new["per_participant"][c]["positive_affine"][m] - old[c]["positive_affine"][m]) for c in old)
        Z = {i: P.child_tokens(enc, bt, i) for i in fd.tr + fd.te}
        U = {i: P.pooled(enc, Z[i]) for i in Z}
        # E1b: head on unstandardised u (es rows), q_hist + EEG offset logistic, twin = swapped u
        Xtr = fd.es_rows(U); head = LogisticRegression(C=1.0, max_iter=2000).fit(Xtr, fd.y_es)
        w = _fit_offset_logistic(Xtr, fd.y_es, fd.off_es)
        dauc, dhg = [], []
        for i in fd.te:
            k = kids[i]; y = k["y"]; cid = k["id"]
            p = head.predict_proba(U[i])[:, 1]
            p0 = fd.q0[k["bin"]]; pw = 1 / (1 + np.exp(-(fd.logit(p0) + np.c_[np.ones(len(y)), U[i]] @ w)))
            ll = lambda qq: np.where(y == 1, np.log2(np.clip(qq, 1e-12, 1)), np.log2(np.clip(1 - qq, 1e-12, 1)))
            dauc.append(abs(P._auc(p, y) - rec["eval"]["per_participant"][cid]["head_auc"]))
            dhg.append(abs(float((ll(pw) - ll(p0)).mean()) - rec["eval"]["per_participant"][cid]["hist_gain_bits"]))
        q["E1b_maxabs_head_auc"] = float(max(dauc)); q["E1b_maxabs_hist_gain_bits"] = float(max(dhg))
        W_ep = [(a + bt.lo, b_ + bt.lo) for a, b_ in bt.W]
        starts, w_ = L.branch_starts(enc, W_ep, rebase=L.PRE["private_bdf"])[0]
        q["E2_record_windows_match"] = [list(x) for x in rec.get("windows_samples_from_epoch_start", W_ep)] == [list(x) for x in W_ep]
        q["E2_window_tokens_ok"] = all(L.tokens_in_window(starts, w_, "private_bdf", wn) == L.WINDOW_TOKENS["private_bdf"][wn] for wn in ("early", "late"))
        q["E2_straddler_sets_ok"] = all(L.tokens_touching_window(starts, w_, "private_bdf", wn) == L.WINDOW_TOKENS_INTERSECT["private_bdf"][wn] for wn in ("early", "late"))
        q["E2_negative_lag_first_sample"] = 50 + 5 * min(P.RAW_LAGS)
        pos = torch.cat([br.pos.detach() for br in enc.branches]).numpy()
        X = {i: Z[i] - pos for i in Z}
        r1, _ = P.s1_lags(fd, X, pos.shape[0], True)
        r2, _ = P.s1_lags(fd, X, pos.shape[0], False)
        q["E3_tg_diag_maxdiff"] = r1["tg_diag_maxdiff"]
        q["E5_bit_identical"] = bool(np.array_equal(r1["s1"], r2["s1"], equal_nan=True))
        fs = copy.copy(fd); fs.y_es = np.random.default_rng(0).permutation(fd.y_es)
        rs, _ = P.s1_lags(fs, X, pos.shape[0], False, history=False)
        q["E4_permuted_mean_auc_minus_half_maxabs"] = float(np.abs(np.nanmean(rs["s1"][:, :, 0], axis=0) - 0.5).max())
        qc["units"][eid] = q
        print(eid, json.dumps(q, default=float), flush=True)
    return qc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--eids", nargs="+", required=True)
    ap.add_argument("--aln2", default=None)
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--e4b", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    if a.e4b:
        return e4b(a.dataset, a.eids)
    qc = private_probe(a.fold, a.eids) if a.dataset == "private_bdf" else continuous_probe(a.dataset, a.eids, a.aln2)
    os.makedirs(QC, mode=0o700, exist_ok=True)
    json.dump(qc, open(os.path.join(QC, f"probe_{a.dataset}_{time.strftime('%Y%m%dT%H%M%S')}.json"), "w"), indent=1, default=float)



def e4b(ds, eids):
    """E4 follow-up: share of segment-shuffled training pairs that kept the same stimulus uid, and the null-control mean
    under a uid-derangement (no training segment receives a target of its own stimulus). QC numbers only."""
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v3 import run as r3
    rows = {r["experiment_id"]: r for r in r3.all_rows() if r["experiment_id"] in eids}
    coh = load_cohort({"dataset": ds, "content_fold": rows[eids[0]]["content_fold"] or 0})
    bank = C.Bank(coh, sorted({core.bind(rows[e])["spec"]["target"] for e in eids}))
    g = core.grid_samples(bank.fs); offs = np.arange(0, bank.seg_len, g); T = len(offs)
    out = {"dataset": ds, "units": {}}
    for eid in eids:
        row = rows[eid]; b = core.bind(row); sp = b["spec"]
        _, _, enc, W = C.build_model({"eid": eid, "source": "aln3"}, bank)
        ev = C.eval_sets(bank, row["subject_fold"], row["seed"])
        uid = np.array([s["uid"] for s in ev["tr"]])
        perm0 = np.random.default_rng(0).permutation(len(uid))
        rng = np.random.default_rng(1); perm = rng.permutation(len(uid))
        for _ in range(100):  # repair collisions by swapping with random positions
            bad = np.flatnonzero(uid[perm] == uid)
            if not len(bad):
                break
            for i in bad:
                j = rng.integers(len(uid)); perm[i], perm[j] = perm[j], perm[i]
        tgr = C.Targets(bank, ev, sp["target"], offs)
        Z = {"tr": C.tokens(enc, bank, W, C.e_index(ev["tr"], offs)), "es": C.tokens(enc, bank, W, C.e_index(ev["q_es"], offs)),
             "te": C.tokens(enc, bank, W, C.e_index(ev["queries"], offs))}
        pos = torch.cat([br.pos.detach() for br in enc.branches]).numpy()
        feats = lambda s, k: Z[s][:, k, :] - pos[k]
        q = {"naive_shuffle_same_uid_share": float((uid[perm0] == uid).mean()), "derangement_collisions": int((uid[perm] == uid).sum()),
             "n_unique_uid_in_400": int(len(set(uid)))}
        for name, pm in (("naive", perm0), ("derange", perm)):
            tgs = copy.copy(tgr); tgs.Az = tgr.Az.reshape(len(uid), T, -1)[pm].reshape(-1, tgr.D)
            rs, _, _ = C.s1_tg(C.Scorer(ev, tgs, T), feats, pos.shape[0], False, f"{eid} {name}")
            m = np.nanmean(rs["s1"][:, :, 0], axis=0)
            q[f"{name}_mean_gain_overall"] = float(np.nanmean(rs["s1"][:, :, 0])); q[f"{name}_per_lag_maxabs"] = float(np.abs(m).max())
            q[f"{name}_lags_positive"] = int((m > 0).sum()); q["n_lags"] = int(len(m))
        out["units"][eid] = q
        print(eid, json.dumps(q, default=float), flush=True)
    os.makedirs(QC, mode=0o700, exist_ok=True)
    json.dump(out, open(os.path.join(QC, f"probe_e4b_{ds}_{time.strftime('%Y%m%dT%H%M%S')}.json"), "w"), indent=1, default=float)



if __name__ == "__main__":
    main()
