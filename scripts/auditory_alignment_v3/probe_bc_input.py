"""BC_PROBE_PLAN_02_INPUT_PATH_20261014 P5 (one GPU): is the stimulus-locked information of the local lag window still in
the tensor the foundation models receive? Training participants only; FAU + DTU, subject fold 0, content fold 0, target
local. Writes private/auditory_alignment_v3/probe_bc/probe_input.json (aggregates only)."""
import glob, json, math, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
import torch.nn.functional as F
from auditory_alignment_v3 import run as R3, core, fm_dense
from auditory_alignment_v2.foundation_adapter import CHANNELS, FS_FM, resample_fft

OUTD = os.path.join(core.OUT, "probe_bc"); dev = torch.device("cuda")
rows = R3.all_rows(); core.load_rows = lambda: rows
RNG = 20261014
res = {"started": time.strftime("%F %T"), "datasets": {}}


def save():
    json.dump(res, open(os.path.join(OUTD, "probe_input.json"), "w"), indent=1)


def corr(P, Y):
    P = P - P.mean(0); Y = Y - Y.mean(0)
    return float(torch.mean((P * Y).sum(0) / (torch.sqrt((P ** 2).sum(0) * (Y ** 2).sum(0)) + 1e-12)))


def ridge(Xf, Yf, Xa, Ya):
    mx, sx = Xf.mean(0), Xf.std(0) + 1e-6; my, sy = Yf.mean(0), Yf.std(0) + 1e-6
    z = lambda X: (X - mx) / sx
    Xf_, Yf_ = z(Xf), (Yf - my) / sy
    G = Xf_.T @ Xf_; H = Xf_.T @ Yf_; tr = torch.trace(G) / G.shape[0]
    best = None
    for a in np.logspace(-4, 2, 7):
        B = torch.linalg.solve(G + float(a) * tr * torch.eye(G.shape[0], device=G.device, dtype=G.dtype), H)
        r = corr(z(Xa) @ B, (Ya - my) / sy)
        if best is None or r > best[0]:
            best = (r, float(a), B)
    return best[2], best[1], (lambda X: z(X) @ best[2]), (lambda Y: (Y - my) / sy)


for ds in ("fau", "dtu"):
    lrow = next(r for r in rows if r["family_id"] == "A_LOCAL" and r["dataset"] == ds and r["subject_fold"] == 0 and r["content_fold"] == 0 and r["seed"] == 3401
                and r["spec"]["objective"] == "NCE" and r["spec"].get("architecture") == "lag_local_tokens" and r["spec"].get("window") == "full")
    from auditory_alignment_v2.run import load_cohort
    b = core.bind(lrow); coh = load_cohort(b); g = core.grid_samples(coh.fs); fs = coh.fs
    bt = fm_dense.DenseBatcher(coh, b["spec"], b, dev, g)
    lo, hi = min(a for a, _ in bt.W), max(c for _, c in bt.W)
    ctx = bt.ctx_len; n200 = int(math.ceil(ctx * FS_FM / fs / 200.0) * 200); pad = int(round(n200 * fs / FS_FM)) - ctx
    n_reve = int(round(ctx * FS_FM / fs)); w200 = int(round((hi - lo) * FS_FM / fs))
    offs = np.arange(0, bt.seg_len, g)
    rng = np.random.default_rng(RNG)
    fit = rng.choice(bt.fit, size=min(300, len(bt.fit)), replace=False); es = rng.choice(bt.es, size=min(160, len(bt.es)), replace=False)
    D = {"native_window_samples": [int(lo), int(hi)], "fs": fs, "grid": int(g), "ctx_len": int(ctx), "cbramod_pad_native": int(pad), "cbramod_n200": n200,
         "reve_n200": n_reve, "window_200hz_samples": w200, "n_fit_segments": int(len(fit)), "n_es_segments": int(len(es))}

    def views(idx, every, lags=range(-3, 4)):
        q = offs[::every]; out = {k: [] for k in ("F0", "F1", "F2")}; tg = {L: [] for L in lags}; pos = []; seg = []
        st = {"sd": [], "clip": [], "rms_fft_vs_lin": {"first": [], "middle": [], "last": []}}
        for j, i in enumerate(idx):
            e0 = torch.tensor([bt.coh_segments[i]["e0"]], device=dev); s0 = int(bt.s0_true[i])
            x = bt.context(e0)[0]  # [C, ctx] native, as DenseFM receives it
            z1 = resample_fft(F.pad(x[None], (0, pad)), n200)[0] * 0.15
            z2 = resample_fft(x[None], n_reve)[0]
            st["sd"].append(x.std(1).cpu().numpy()); st["clip"].append(float((z2.abs() > 15).float().mean()))
            tn = torch.arange(n_reve, device=dev).float() * fs / FS_FM  # native sample positions of the 200 Hz grid
            i0 = tn.floor().long().clamp(max=ctx - 2); fr = (tn - i0).clamp(0, 1)
            lin = x[:, i0] * (1 - fr) + x[:, i0 + 1] * fr
            dif = ((z2 - lin) ** 2).mean(0) / ((lin ** 2).mean() + 1e-12)
            tsec = torch.arange(n_reve, device=dev).float() / FS_FM
            for name, m in (("first", tsec < 0.5), ("middle", (tsec >= 0.5) & (tsec < ctx / fs - 0.5)), ("last", tsec >= ctx / fs - 0.5)):
                st["rms_fft_vs_lin"][name].append(float(torch.sqrt(dif[m].mean())))
            qt = torch.tensor(q, device=dev)
            out["F0"].append(torch.stack([x[:, t + lo:t + hi].reshape(-1) for t in q]))
            k200 = torch.round(qt.float() * FS_FM / fs).long()
            out["F1"].append(torch.stack([(z1[:, k:k + w200]).reshape(-1) for k in k200]))
            out["F2"].append(torch.stack([(z2.clamp(-15, 15)[:, k:k + w200]).reshape(-1) for k in k200]))
            for L in lags:
                tg[L].append(bt.audio(torch.tensor(s0 + q + L * g, device=dev)).float())
            pos += list(q / fs); seg += [j] * len(q)
        return ({k: torch.cat(v).double() for k, v in out.items()}, {L: torch.cat(v).double() for L, v in tg.items()}, np.array(pos), np.array(seg), st)

    Vf, Tf, _, _, stf = views(fit, 4)
    Ve, Te, pe, se, ste = views(es, 2)
    h = se < len(es) // 2; hb = ~h
    D["input_stats"] = {"native_sd_mean": float(np.mean(stf["sd"])), "native_sd_min": float(np.min(stf["sd"])), "native_sd_max": float(np.max(stf["sd"])),
                        "reve_clip_fraction": float(np.mean(stf["clip"])),
                        "rms_fft_vs_linear_rel": {k: float(np.mean(v)) for k, v in stf["rms_fft_vs_lin"].items()}}
    seg_len_s = bt.seg_len / fs
    regions = {"first_0.5s": pe < 0.5, "middle": (pe >= 0.5) & (pe < seg_len_s - 0.5), "last_0.5s": pe >= seg_len_s - 0.5}
    D["P5a"] = {}
    for name in ("F0", "F1", "F2"):
        r = {"dims": int(Vf[name].shape[1]), "lag_r": {}}
        for L in Tf:
            B, a, pred, ys = ridge(Vf[name], Tf[L], Ve[name][h], Te[L][h])
            r["lag_r"][L] = corr(pred(Ve[name][hb]), ys(Te[L][hb]))
            if L == 0:
                r["alpha"] = a
                P = pred(Ve[name]); Y = ys(Te[0])
                r["by_position"] = {k: corr(P[torch.tensor(hb & m, device=dev)], Y[torch.tensor(hb & m, device=dev)]) for k, m in regions.items()}
                # floor: targets from another segment (roll by one segment within half B)
                idxB = np.flatnonzero(hb); segsB = np.unique(se[hb]); roll = {s: segsB[(k + 1) % len(segsB)] for k, s in enumerate(segsB)}
                rows_by = {s: np.flatnonzero(se == s) for s in segsB}
                pr, yr = [], []
                for s in segsB:
                    a_, b_ = rows_by[s], rows_by[roll[s]]; n = min(len(a_), len(b_))
                    pr.append(P[torch.tensor(a_[:n], device=dev)]); yr.append(Y[torch.tensor(b_[:n], device=dev)])
                r["floor"] = corr(torch.cat(pr), torch.cat(yr))
        r["peak_lag"] = int(max(r["lag_r"], key=r["lag_r"].get))
        D["P5a"][name] = r
        print(ds, name, {k: v for k, v in r.items() if k != "lag_r"}, "lag_r", {k: round(v, 4) for k, v in r["lag_r"].items()}, flush=True)
    # P5c channel order
    if ds == "fau":
        from auditory_alignment import data
        import h5py
        same, diff_order, diff_set = 0, 0, 0
        for p in coh.participants:
            with h5py.File(os.path.join(data.STAGEB, p["group"], f"{p['id']}.h5"), "r") as f:
                ch = [str(c) for c in f.attrs["channels"]]
            if ch == CHANNELS["fau"]:
                same += 1
            elif sorted(ch) == sorted(CHANNELS["fau"]):
                diff_order += 1
            else:
                diff_set += 1
        D["P5c"] = {"files": len(coh.participants), "same_order": same, "same_set_different_order": diff_order, "different_set": diff_set}
    else:
        from auditory_alignment import data
        import h5py
        p = coh.participants[0]
        with h5py.File(os.path.join(data.DTU_PRE, f"{p['id']}.h5"), "r") as f:
            attrs = sorted(f.attrs.keys()); k0 = sorted(f.keys())[0]; gattrs = sorted(f[k0].attrs.keys())
            names = [str(c) for c in f.attrs["channels"]][:64] if "channels" in f.attrs else None
        D["P5c"] = {"file_attrs": attrs, "trial_attrs": gattrs, "channel_names_stored": names is not None,
                    "same_order_as_adapter": (names == CHANNELS["dtu"]) if names is not None else None}
    print(ds, "P5b", D["input_stats"], "P5c", D["P5c"], flush=True)
    res["datasets"][ds] = D; save()
    bt = coh = Vf = Ve = Tf = Te = None; torch.cuda.empty_cache()
res["finished"] = time.strftime("%F %T"); save(); print("done")
