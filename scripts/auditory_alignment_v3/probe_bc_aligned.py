"""BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014 P6 (one GPU): frozen backbone tokens of a query-aligned patch
[t - 0.4 s, t + 0.6 s) vs the raw EEG of the same window vs the unaligned full-context tokens B_DENSE uses. Training
participants only; FAU + DTU, subject fold 0, content fold 0, target local. Writes probe_bc/probe_aligned.json (aggregates)."""
import json, math, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
import torch.nn.functional as F
from auditory_alignment_v3 import run as R3, core, fm_dense
from auditory_alignment_v3.fm_probe import LayerTap
from auditory_alignment_v2.foundation_adapter import Backbone, FS_FM

OUTD = os.path.join(core.OUT, "probe_bc"); dev = torch.device("cuda")
rows = R3.all_rows(); core.load_rows = lambda: rows
RNG = 20261014
res = {"started": time.strftime("%F %T"), "datasets": {}}


def save():
    json.dump(res, open(os.path.join(OUTD, "probe_aligned.json"), "w"), indent=1)


def corr(P, Y):
    P = P - P.mean(0); Y = Y - Y.mean(0)
    return float(torch.mean((P * Y).sum(0) / (torch.sqrt((P ** 2).sum(0) * (Y ** 2).sum(0)) + 1e-12)))


def kridge(Xf, Yf, Xe, Ye, hA, hB, segB):
    """linear kernel ridge on standardised features; lambda on half A, r on half B; floor = targets of the next segment."""
    mx, sx = Xf.mean(0), Xf.std(0) + 1e-6
    Zf = ((Xf - mx) / sx).float(); Ze = ((Xe - mx) / sx).float(); p = Zf.shape[1]
    my, sy = Yf.mean(0), Yf.std(0) + 1e-6
    Yf_, Ye_ = ((Yf - my) / sy).double(), ((Ye - my) / sy).double()
    K = (Zf @ Zf.T).double() / p; Ke = (Ze @ Zf.T).double() / p
    lam, Q = torch.linalg.eigh(K); QtY = Q.T @ Yf_; tr = float(lam.sum()) / len(lam)
    best = None
    for a in np.logspace(-4, 2, 7):
        alpha = Q @ (QtY / (lam + a * tr)[:, None])
        P = Ke @ alpha
        rA = corr(P[hA], Ye_[hA])
        if best is None or rA > best[0]:
            best = (rA, float(a), P)
    P = best[2]
    rB = corr(P[hB], Ye_[hB])
    pr, yr = [], []
    segs = sorted(segB)
    for k, s in enumerate(segs):
        a_, b_ = segB[s], segB[segs[(k + 1) % len(segs)]]; n = min(len(a_), len(b_))
        pr.append(P[a_[:n]]); yr.append(Ye_[b_[:n]])
    return {"r": rB, "alpha": best[1], "floor": corr(torch.cat(pr), torch.cat(yr)), "dims": int(p)}


for ds in ("fau", "dtu"):
    lrow = next(r for r in rows if r["family_id"] == "A_LOCAL" and r["dataset"] == ds and r["subject_fold"] == 0 and r["content_fold"] == 0 and r["seed"] == 3401
                and r["spec"]["objective"] == "NCE" and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("window") == "full")
    from auditory_alignment_v2.run import load_cohort
    b = core.bind(lrow); coh = load_cohort(b); g = core.grid_samples(coh.fs); fs = coh.fs
    bt = fm_dense.DenseBatcher(coh, b["spec"], b, dev, g)
    ctx = bt.ctx_len; pre = int(round(0.4 * fs)); post = int(round(0.6 * fs)); offs = np.arange(0, bt.seg_len, g)
    rng = np.random.default_rng(RNG)
    fit = rng.choice(bt.fit, size=min(300, len(bt.fit)), replace=False); es = rng.choice(bt.es, size=min(160, len(bt.es)), replace=False)
    D = {"fs": fs, "grid": int(g), "pre_samples": pre, "post_samples": post, "n_fit_segments": int(len(fit)), "n_es_segments": int(len(es)), "views": {}}

    def collect(idx, every):
        q = offs[::every]; X06, X10, Y, seg, ctxs, qs = [], [], [], [], [], []
        for j, i in enumerate(idx):
            e0 = torch.tensor([bt.coh_segments[i]["e0"]], device=dev); s0 = int(bt.s0_true[i])
            x = bt.context(e0)[0]; xp = F.pad(x, (pre, 0))  # zeros before the segment start
            X06.append(torch.stack([x[:, t:t + post] for t in q]).reshape(len(q), -1))
            X10.append(torch.stack([xp[:, t:t + pre + post] for t in q]))  # [Q, C, pre+post] window [t-0.4, t+0.6)
            Y.append(bt.audio(torch.tensor(s0 + q, device=dev)).float()); seg += [j] * len(q); ctxs.append(x); qs.append(q)
        return torch.cat(X06), torch.cat(X10), torch.cat(Y), np.array(seg), ctxs, qs

    f06, f10, fY, fseg, fctx, fq = collect(fit, 8)
    e06, e10, eY, eseg, ectx, eq = collect(es, 4)
    hA = torch.tensor(eseg < len(es) // 2, device=dev); hBn = eseg >= len(es) // 2; hB = torch.tensor(hBn, device=dev)
    segB = {s: torch.tensor(np.flatnonzero(eseg == s), device=dev) for s in np.unique(eseg[hBn])}

    def run_view(name, Xf, Xe):
        r = kridge(Xf.float(), fY.double(), Xe.float(), eY.double(), hA, hB, segB); D["views"][name] = r
        print(ds, name, r, flush=True); save()

    run_view("R06", f06, e06)
    run_view("R10", f10.reshape(len(f10), -1), e10.reshape(len(e10), -1))
    for arch in ("cbramod", "reve"):
        for init in ("pretrained", "random"):
            for layer in ("patch_embedding", "last"):
                torch.manual_seed(RNG)  # random-init backbones reproducible
                bb = Backbone(arch, ds, "pretrained_frozen" if init == "pretrained" else "random_full", fs).to(dev).eval()
                for p_ in bb.parameters():
                    p_.requires_grad_(False)
                tap = LayerTap(bb, layer)

                @torch.no_grad()
                def aligned(W):  # W [N, C, pre+post] native -> [N, C*E] tokens of the single aligned patch
                    out = []
                    for k in range(0, len(W), 64):
                        o = bb(W[k:k + 64]); h = tap.tokens(o)  # [n, C, 1, E]
                        out.append(h[:, :, 0].reshape(h.shape[0], -1).float())
                    return torch.cat(out)
                run_view(f"ALIGNED|{arch}|{init}|{layer}", aligned(f10), aligned(e10))
                if init == "pretrained":
                    dfm = fm_dense.DenseFM(bb, "channel_phase_linear", 32, fs, bt.seg_len, ctx).to(dev).eval()
                    pt = dfm.patch_times.cpu().numpy() - 0.5  # patch starts (s)
                    plen = 1.0

                    @torch.no_grad()
                    def unaligned(ctxs, qs):
                        out = []
                        for x, q in zip(ctxs, qs):
                            h = tap.tokens(dfm.tokens(x[None]))[0]  # [C, P, E]
                            c = (q / fs) + 0.3
                            k = np.array([int(np.flatnonzero((pt <= v) & (v < pt + plen))[0]) if ((pt <= v) & (v < pt + plen)).any() else len(pt) - 1 for v in c])
                            out.append(h[:, torch.tensor(k, device=dev)].permute(1, 0, 2).reshape(len(q), -1).float())
                        return torch.cat(out)
                    run_view(f"UNALIGNED|{arch}|pretrained|{layer}", unaligned(fctx, fq), unaligned(ectx, eq))
                    dfm = None
                bb = tap = None; torch.cuda.empty_cache()
    res["datasets"][ds] = D; save()
    bt = coh = f10 = e10 = fctx = ectx = None; torch.cuda.empty_cache()
res["finished"] = time.strftime("%F %T"); save(); print("done")
