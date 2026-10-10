"""Diagnostic probe (2026-10-07): why are foundation-model alignment results near chance?

Same dev cell, segments, 200 Hz resampling and patch-level audio targets as the B_FM units (fold 0, content fold 0, seed 3401);
only the feature -> linear readout step differs. Ridge (alpha chosen on training-side es segments) maps per-patch features to
the standardised audio patch window; a test query segment scores each test candidate by the sum over patches of the
correlation between predicted and candidate audio. Reported per test participant: rank_pct of the true candidate (0.5 =
chance, lower is better) for true EEG and for rolled (mismatched) EEG.
Features: raw_ch (resampled EEG, every channel, 20 bins of 50 ms per 1 s patch), raw_mean (same, averaged over channels),
cb_mean (frozen CBraMod tokens averaged over channels = the units' PatchHead input), cb_ch (frozen CBraMod tokens of every
channel, PCA 512 fitted on training patches).
Usage: python fm_head_probe.py <dataset>
"""
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v2.foundation_adapter import Backbone, resample_fft  # noqa: E402
from auditory_alignment_v2.run import PLAN, load_cohort  # noqa: E402
from auditory_alignment_v2.train_fm import SegmentBatcher  # noqa: E402

DS = sys.argv[1]
OUT = f"/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v2/probes/fm_head_probe_{DS}.json"
torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "8")))
t0 = time.time()
row = next(json.loads(l) for l in open(PLAN) if (lambda r: r["family_id"] == "B_FM" and r["dataset"] == DS and r["subject_fold"] == 0
           and r["content_fold"] == 0 and r["seed"] == 3401 and r["spec"]["architecture"] == "cbramod"
           and r["spec"]["adaptation"] == "pretrained_frozen" and r["spec"]["objective"] == "NCE")(json.loads(l)))
coh = load_cohort(row)
segs, parts = coh.segments, coh.participants
bb = Backbone("cbramod", DS, "pretrained_frozen", coh.fs).eval()
bt = SegmentBatcher(coh, row["spec"], row, "cpu", bb.patch_starts(int(round(coh.meta["seg_len"] * 200 / coh.fs))))
rng = np.random.default_rng(0)
fit = list(rng.choice(bt.fit, size=min(1500, len(bt.fit)), replace=False))
es = list(rng.choice(bt.es, size=min(400, len(bt.es)), replace=False))
test_p = sorted({s["p"] for s in segs if s["role"] == "test" and (parts[s["p"]]["fold"] == row["subject_fold"] or parts[s["p"]].get("test_only"))})
test = [i for i, s in enumerate(segs) if s["role"] == "test" and s["kind"] == "ss" and s["p"] in test_p]
cand, seen = [], set()
for i in test:
    if segs[i]["uid"] not in seen:
        seen.add(segs[i]["uid"]); cand.append(i)
P = len(bt.starts)


@torch.no_grad()
def feats(idx):
    out = {"raw_ch": [], "raw_mean": [], "cb_mean": [], "cb_ch": []}
    for k in range(0, len(idx), 32):
        e0 = torch.tensor([segs[i]["e0"] for i in idx[k:k + 32]])
        x = bt.segments(e0)  # [n, C, T_native]
        z = resample_fft(x, int(round(x.shape[-1] * 200 / coh.fs)))
        n, C, _ = z.shape
        zz = z[..., :P * 200].reshape(n, C, P, 20, 10).mean(-1)  # [n, C, P, 20] 50 ms bins
        out["raw_ch"].append(zz.permute(0, 2, 1, 3).reshape(n, P, C * 20).numpy())
        out["raw_mean"].append(zz.mean(1).numpy())
        tok = bb(x)  # [n, C, P, 200]
        out["cb_mean"].append(tok.mean(1).numpy())
        out["cb_ch"].append(tok.permute(0, 2, 1, 3).reshape(n, P, -1).numpy().astype(np.float32))
    return {k: np.concatenate(v) for k, v in out.items()}


def audio(idx):
    return bt.audio_patches(torch.tensor([segs[i]["s0"] for i in idx])).float().numpy()  # [n, P, nbin*D]


F_fit, F_es, F_te = feats(fit), feats(es), feats(test)
A_fit, A_es, A_cand = audio(fit), audio(es), audio(cand)
mu, sd = A_fit.reshape(-1, A_fit.shape[-1]).mean(0), A_fit.reshape(-1, A_fit.shape[-1]).std(0) + 1e-6
Y_fit, Y_es, Y_cand = (A_fit - mu) / sd, (A_es - mu) / sd, (A_cand - mu) / sd
cand_pos = {segs[i]["uid"]: j for j, i in enumerate(cand)}
print(f"data ready {time.time() - t0:.0f}s fit {len(fit)} es {len(es)} test {len(test)} cand {len(cand)} P {P} C {bt.E.shape[0]}", flush=True)


def zrows(M):
    M = M - M.mean(-1, keepdims=True)
    return M / (np.linalg.norm(M, axis=-1, keepdims=True) + 1e-9)


def score(pred, Yc):  # pred [q, P, D], Yc [c, P, D] -> [q, c] sum over patches of correlations
    return np.einsum("qpd,cpd->qc", zrows(pred), zrows(Yc))


def ridge_fit(X, Y, a):
    XtX = X.T @ X
    return np.linalg.solve(XtX + a * np.trace(XtX) / XtX.shape[0] * np.eye(XtX.shape[0]), X.T @ Y)


res = {"dataset": DS, "n_fit": len(fit), "n_es": len(es), "n_test_queries": len(test), "n_candidates": len(cand), "P": P, "features": {}}
for name in ("raw_ch", "raw_mean", "cb_mean", "cb_ch"):
    Xf, Xe, Xt = F_fit[name], F_es[name], F_te[name]
    if name == "cb_ch":  # PCA 512 on training patches
        flat = Xf.reshape(-1, Xf.shape[-1]); m = flat.mean(0)
        U, S, Vt = np.linalg.svd(flat[rng.choice(len(flat), size=min(4000, len(flat)), replace=False)] - m, full_matrices=False)
        W = Vt[:512].T
        Xf, Xe, Xt = [(x - m) @ W for x in (Xf, Xe, Xt)]
    m, s = Xf.reshape(-1, Xf.shape[-1]).mean(0), Xf.reshape(-1, Xf.shape[-1]).std(0) + 1e-6
    Xf, Xe, Xt = [np.concatenate([(x - m) / s, np.ones(x.shape[:-1] + (1,))], -1) for x in (Xf, Xe, Xt)]
    best = None
    for a in (1e-3, 1e-2, 1e-1, 1, 10, 100):
        B = ridge_fit(Xf.reshape(-1, Xf.shape[-1]), Y_fit.reshape(-1, Y_fit.shape[-1]), a)
        pe = (Xe @ B)
        r = float(np.mean(np.sum(zrows(pe) * zrows(Y_es), -1)))  # mean per-patch correlation on es
        if best is None or r > best[1]:
            best = (a, r, B)
    a, r_es, B = best
    per = {}
    for p in test_p:
        q = [k for k, i in enumerate(test) if segs[i]["p"] == p]
        if len(q) < 3:
            continue
        pred = Xt[q] @ B
        S = score(pred, Y_cand)
        own = np.array([cand_pos[segs[test[k]]["uid"]] for k in q])
        def rank(Sm):
            return float(np.mean([(Sm[i] > Sm[i, own[i]]).mean() for i in range(len(own))]))
        per[str(p)] = {"rank_true": rank(S), "rank_mismatched": rank(np.roll(S, 1, axis=0)), "n": len(q), "group": parts[p]["group"]}
    rt = np.array([v["rank_true"] for v in per.values()]); rm = np.array([v["rank_mismatched"] for v in per.values()])
    b = np.random.default_rng(1).integers(0, len(rt), (2000, len(rt)))
    res["features"][name] = {"alpha": a, "es_patch_corr": r_es, "n_participants": len(rt),
                             "rank_true_mean": float(rt.mean()), "rank_mismatched_mean": float(rm.mean()),
                             "rank_gain_mean": float((rm - rt).mean()),
                             "rank_gain_ci": [float(np.percentile((rm - rt)[b].mean(1), 2.5)), float(np.percentile((rm - rt)[b].mean(1), 97.5))]}
    print(name, json.dumps(res["features"][name]), f"{time.time() - t0:.0f}s", flush=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(res, open(OUT, "w"), indent=1)
print("done", time.time() - t0)
