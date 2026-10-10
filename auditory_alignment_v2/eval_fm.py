"""ALN2 module B evaluation: identical protocol to auditory_alignment.evaluate.evaluate_continuous (same Readouts, metrics,
candidate pools, hard candidates, mismatched-EEG control, temperature calibration, attention 2AFC, test-side kernel
dependence, split-half), with patch-level representations (T = backbone patches per 5 s segment) instead of anchors."""
from __future__ import annotations

import numpy as np
import torch

from auditory_alignment import evaluate as ev1

READOUT_OBJ = {"NCE": "NCE", "CS_SINGLE": "CS_SINGLE", "FMCA": "FMCA", "SELECTION_CE": "NCE"}


class SegmentReps:
    def __init__(self, enc, head, bt, chunk=64):
        self.enc, self.head, self.bt, self.chunk = enc, head, bt, chunk

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []
        for k in range(0, len(e0s), self.chunk):
            out.append(self.enc(self.bt.segments(torch.tensor(e0s[k:k + self.chunk], device=self.bt.dev))).float().cpu().numpy())
        return np.concatenate(out)

    @torch.no_grad()
    def va(self, s0s):
        s0s = np.asarray(s0s); v, a = [], []
        for k in range(0, len(s0s), self.chunk):
            A = self.bt.audio_patches(torch.tensor(s0s[k:k + self.chunk], device=self.bt.dev))
            a.append(A.cpu().numpy()); v.append(self.head(A).cpu().numpy())
        return np.concatenate(v), np.concatenate(a)


def evaluate_segments(row, enc, head, bt, coh, calib, K=8, reps=None, readouts=("unified", "native"), dependence=True):
    objective = READOUT_OBJ[row["spec"]["objective"]]
    rng = np.random.default_rng(row["seed"] + 1000)
    segs = coh.segments; kind = "ss"
    reps = reps if reps is not None else SegmentReps(enc, head, bt)
    train_segs = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == bt.kind]
    ro = ev1.Readouts(objective, reps, train_segs, rng)

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
        ro.calibrate({kr: ro.scores(Uq, Vc, Ac, kr) for kr in readouts}, own)
    te_uid, te_rows = pool_of("test", kind)
    Vc, Ac = reps.va([r["s0"] for r in te_rows])
    feat = np.array([r["feat"] for r in te_rows]); feat = (feat - feat.mean(0)) / (feat.std(0) + 1e-12)
    hard = {}
    for j, r in enumerate(te_rows):
        el = [i for i, q in enumerate(te_rows) if q["hard_key"] == r["hard_key"] and q["part"] != r["part"]]
        if len(el) < K:
            el = [i for i in range(len(te_rows)) if i != j and te_rows[i]["part"] != r["part"]]
        dd = np.sqrt(((feat[el] - feat[j]) ** 2).sum(1)); hard[j] = [el[i] for i in np.argsort(dd)[:K]]
    per = {}
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and (coh.participants[s["p"]]["fold"] == row["subject_fold"] or coh.participants[s["p"]].get("test_only"))})
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == kind]
        if not q:
            continue
        order = np.argsort([s["e0"] for s in q]); q = [q[i] for i in order]
        Uq = reps.u([s["e0"] for s in q]); own = np.array([te_uid[s["uid"]] for s in q])
        Umm = np.roll(Uq, 1, axis=0)
        rec = {"group": coh.participants[p]["group"], "n_segments": len(q)}; h = len(q) // 2
        for kr in readouts:
            S = ro.scores(Uq, Vc, Ac, kr)
            rec[f"{kr}/regular"] = ev1._metrics(S, own, ro.tau[kr])
            if h >= 2:
                rec[f"{kr}/regular_half0"] = ev1._metrics(S[:h], own[:h], ro.tau[kr]); rec[f"{kr}/regular_half1"] = ev1._metrics(S[h:], own[h:], ro.tau[kr])
            rec[f"{kr}/mismatched_eeg"] = ev1._metrics(ro.scores(Umm, Vc, Ac, kr), own, ro.tau[kr])
            Sh = np.stack([S[i, [own[i]] + hard[own[i]]] for i in range(len(q))])
            rec[f"{kr}/hard"] = ev1._metrics(Sh, np.zeros(len(q), int), ro.tau[kr])
        dep = ev1.test_cs_dependence(Uq, Vc[own], calib, np.random.default_rng(p), anchors=Uq.shape[1]) if dependence else None
        if dep:
            rec["kernel_dependence"] = dep
        per[coh.participants[p]["id"]] = rec
    out = {"per_participant": per, "readout": {"alpha_unified": ro.alpha_uni, "tau": ro.tau, "n_test_candidates": len(te_rows), "T_per_segment": int(Vc.shape[1])}}
    cs = [s for s in segs if s["kind"] == "cs" and s["role"] == "test" and s.get("s0_ign") is not None]
    if cs:
        att = {}
        for p in test_p:
            q = [s for s in cs if s["p"] == p]
            if not q:
                continue
            Uq = reps.u([s["e0"] for s in q]); Va, Aa = reps.va([s["s0"] for s in q]); Vi, Ai = reps.va([s["s0_ign"] for s in q])
            r = {}
            for kr in readouts:
                sa = np.array([ro.scores(Uq[i:i + 1], Va[i:i + 1], Aa[i:i + 1], kr)[0, 0] for i in range(len(q))])
                si = np.array([ro.scores(Uq[i:i + 1], Vi[i:i + 1], Ai[i:i + 1], kr)[0, 0] for i in range(len(q))])
                r[kr] = {"accuracy": float((sa > si).mean()), "mean_margin": float((sa - si).mean()), "n": len(q)}
            att[coh.participants[p]["id"]] = r
        out["attention_2afc"] = att
    return out


@torch.no_grad()
def trained_selection_2afc_segments(enc, head, bt, coh, row, sel):
    """2AFC with the trained selection score on test competing-speech segments (patch scores averaged per segment)."""
    segs = coh.segments
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == row["subject_fold"]})
    res = {}
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["kind"] == "cs" and s["role"] == "test" and s.get("s0_ign") is not None]
        if not q:
            continue
        U = enc(bt.segments(torch.tensor([s["e0"] for s in q], device=bt.dev)))
        Va = head(bt.audio_patches(torch.tensor([s["s0"] for s in q], device=bt.dev)))
        Vi = head(bt.audio_patches(torch.tensor([s["s0_ign"] for s in q], device=bt.dev)))
        B, Pn, d = U.shape
        sa = sel(U.reshape(-1, d), Va.reshape(-1, d)).reshape(B, Pn).mean(1); si = sel(U.reshape(-1, d), Vi.reshape(-1, d)).reshape(B, Pn).mean(1)
        res[coh.participants[p]["id"]] = {"accuracy": float((sa > si).float().mean()), "mean_margin": float((sa - si).mean()), "n": len(q)}
    return res
