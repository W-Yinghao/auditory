"""Round-3: artefact-source battery, per-child evidence peaks, component parameters, record-level checks, age matrix."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .round2 import shared_scores, since_last_deviant
from .runtime import ROOT, cfg, done, open_run, private_dir, read_json, results_dir, write_json_overwrite as write_json

HA_CHANNELS = ["Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4", "T3", "T4", "Pz", "P3", "P4", "T5", "T6", "Oz", "O1", "O2"]
# HydroCel GSN 128: EGI's designated EOG electrodes (VEOG 8/126 right, 25/127 left; HEOG 125/128) and the frontal-polar ring
MFF_PERIOCULAR = {"E8", "E25", "E125", "E126", "E127", "E128"}
MFF_FRONTAL_POLAR = {"E1", "E9", "E14", "E15", "E17", "E21", "E22", "E32"}


def _torch():
    import torch
    return torch, torch.device("cuda")


def _channel_names(config: dict, lane: gxd.Lane) -> list[str]:
    if lane.x.shape[1] == 20:
        return list(HA_CHANNELS)
    meta = read_json(ROOT / "private/auditory_d1" / cfg(config, "sources.d1_mff_run") / "arrays" / f"{lane.record_ids[0]}.json")
    return [str(c) for c in meta["channels"]]


def _fold_models(config: dict, base_run: str, lane: gxd.Lane, device, torch):
    base = private_dir(config, base_run)
    folds = read_json(base / "folds.json")
    for seed_str, fold_list in folds.items():
        if seed_str == "model":
            continue
        for k, test_children in enumerate(fold_list):
            model = gxt.build_model(config, lane)
            model.load_state_dict(torch.load(base / "models" / f"shared_s{seed_str}_f{k}.pt", map_location=device))
            model.to(device).eval()
            yield int(seed_str), k, np.asarray(test_children), model


def _child_auc(lane, idx, logits, y) -> dict:
    out = {}
    for c in np.unique(lane.child[idx]):
        sel = lane.child[idx] == c
        m = gxt.child_metrics(logits[sel], y[idx[sel]], lane.n_classes)
        out[int(c)] = m["auc"]
    return out


# ----------------------------------------------------------------------------- r3-artefact

def cmd_r3_artefact(args, config) -> dict:
    torch, device = _torch()
    from sklearn.metrics import roc_auc_score
    run = open_run("r3_artefact", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    names = _channel_names(config, lane)
    y = lane.y.cpu().numpy()
    rate = float(cfg(config, "epoch.rate_hz"))
    pre = int(round(float(cfg(config, "epoch.pre_seconds")) * rate))
    w0, w1 = pre + int(0.12 * rate), pre + int(0.32 * rate)
    is_ha = lane.x.shape[1] == 20
    groups = {n: [i] for i, n in enumerate(names)} if is_ha else {}
    if is_ha:
        for gname, members in (("Fp1+Fp2", ["Fp1", "Fp2"]), ("F7+F8+T3+T4", ["F7", "F8", "T3", "T4"]), ("Fz+Cz+F3+F4", ["Fz", "Cz", "F3", "F4"]),
                               ("T5+T6+P3+P4", ["T5", "T6", "P3", "P4"]), ("O1+O2+Oz+Pz", ["O1", "O2", "Oz", "Pz"])):
            groups[gname] = [names.index(m) for m in members]
    if not is_ha:
        peri = [i for i, n in enumerate(names) if n in MFF_PERIOCULAR]
        polar = [i for i, n in enumerate(names) if n in MFF_FRONTAL_POLAR]
        rest = [i for i in range(len(names)) if i not in peri and i not in polar]
        groups = {"periocular_eog": peri, "frontal_polar": polar, "non_periocular": rest,
                  "vertex_ring": [i for i, n in enumerate(names) if n in {"E6", "E7", "E31", "E55", "E80", "E106", "E129"}],
                  "left_temporal": [i for i, n in enumerate(names) if n in {"E39", "E40", "E44", "E45", "E46", "E50", "E57", "E58"}],
                  "right_temporal": [i for i, n in enumerate(names) if n in {"E96", "E101", "E102", "E108", "E109", "E114", "E115", "E100"}],
                  "occipital": [i for i, n in enumerate(names) if n in {"E70", "E71", "E74", "E75", "E76", "E82", "E83", "E69", "E89"}]}
        edges = np.linspace(0, len(names), 9).astype(int)
        for g in range(8):
            groups[f"band_{g}"] = list(range(edges[g], edges[g + 1]))
    # (a) inference-time occlusion per channel / group
    rows = []
    x_backup = lane.x
    for seed, k, test_children, model in _fold_models(config, args.base_run, lane, device, torch):
        idx = gxd.idx_of_children(lane, test_children)
        base = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
        for name, chans in groups.items():
            lane.x = x_backup.clone()
            lane.x[:, chans, :] = 0
            occ = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
            for c in base:
                rows.append({"seed": seed, "fold": k, "child": c, "group": name, "n_channels": len(chans),
                             "auc_base": base[c], "auc_occluded": occ[c], "drop": base[c] - occ[c]})
        lane.x = x_backup
    occ = pd.DataFrame(rows)
    occ.to_csv(run["public"] / f"channel_occlusion_{args.lane}.csv", index=False)
    topo = occ.groupby("group").drop.mean().sort_values(ascending=False)
    # (b) single-trial frontal amplitude distributions in the evidence window
    front = [0, 1] if is_ha else groups["periocular_eog"]
    xw = lane.x[:, front, w0:w1].float().mean(dim=(1, 2)).cpu().numpy()           # signed mean over frontal group and window
    score, _ = shared_scores(config, args.lane, args.base_run, len(y), lane.n_classes)
    dist_rows = []
    from scipy.stats import kurtosis
    for c in np.unique(lane.child):
        sel = (lane.child == c) & np.isfinite(score)
        s_std, s_dev = xw[sel & (y == 0)], xw[sel & (y >= 1)]
        if len(s_dev) < 30 or len(s_std) < 100:
            continue
        sd0 = s_std.std() + 1e-9
        extreme = float(np.mean(np.abs(s_dev - s_std.mean()) > 3 * sd0))
        extreme_std = float(np.mean(np.abs(s_std - s_std.mean()) > 3 * sd0))
        # bimodality proxy: BIC of 1 vs 2 gaussian components on deviant amplitudes
        from sklearn.mixture import GaussianMixture
        a = s_dev.reshape(-1, 1)
        bic1 = GaussianMixture(1, random_state=0).fit(a).bic(a)
        bic2 = GaussianMixture(2, random_state=0).fit(a).bic(a)
        b = np.random.default_rng(int(c)).choice(s_std, size=len(s_dev), replace=False).reshape(-1, 1)
        bic_std = GaussianMixture(2, random_state=0).fit(b).bic(b) - GaussianMixture(1, random_state=0).fit(b).bic(b)
        hi = sel & (score > np.nanquantile(score[sel], 0.9))
        lo = sel & (score < np.nanquantile(score[sel], 0.1))
        dist_rows.append({"child": int(c), "n_dev": int(len(s_dev)), "frontal_shift_sd": float((s_dev.mean() - s_std.mean()) / sd0),
                          "kurtosis_dev": float(kurtosis(s_dev)), "kurtosis_std": float(kurtosis(s_std)),
                          "bic2_minus_bic1_dev": float(bic2 - bic1), "bic2_minus_bic1_std_matched": float(bic_std), "frac_dev_beyond_3sd": extreme, "frac_std_beyond_3sd": extreme_std,
                          "frontal_mean_top10pct_logit": float(xw[hi].mean() if hi.any() else np.nan),
                          "frontal_mean_bottom10pct_logit": float(xw[lo].mean() if lo.any() else np.nan),
                          "frontal_auc_std_vs_dev": float(roc_auc_score(y[sel] >= 1, xw[sel]))})
    dist = pd.DataFrame(dist_rows)
    dist.to_csv(run["public"] / f"frontal_amplitude_{args.lane}.csv", index=False)
    # (d) diffuse amplitude control: RMS over all channels in the window
    rms = torch.sqrt((lane.x[:, :, w0:w1].float() ** 2).mean(dim=(1, 2))).cpu().numpy()
    rms_auc = []
    for c in np.unique(lane.child):
        sel = lane.child == c
        if len(np.unique(y[sel])) == 2 and (y[sel] >= 1).sum() >= 20:
            rms_auc.append(roc_auc_score(y[sel] >= 1, rms[sel]))
    # (e) QC flag rate by class (needs rejected trials)
    full = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device, accepted_only=False)
    yf = full.y.cpu().numpy()
    rej = full.qc_over > float(cfg(config, "qc.ptp_channel_fraction_max"))
    qc_rows = []
    for c in np.unique(full.child):
        sel = full.child == c
        if (yf[sel] >= 1).sum() >= 20:
            qc_rows.append({"child": int(c), "reject_rate_std": float(rej[sel & (yf == 0)].mean()), "reject_rate_dev": float(rej[sel & (yf >= 1)].mean())})
    qc = pd.DataFrame(qc_rows)
    summary = {"run": args.run, "lane": args.lane, "channel_names_available": True,
               "occlusion_topography_drop": {k: float(v) for k, v in topo.items()},
               "frontal_amplitude": {"children": int(len(dist)), "frontal_shift_sd_mean": float(dist.frontal_shift_sd.mean()),
                                     "frontal_auc_mean": float(dist.frontal_auc_std_vs_dev.mean()),
                                     "children_bimodal_dev(bic2<bic1-10)": int((dist.bic2_minus_bic1_dev < -10).sum()),
                                     "children_bimodal_std_matched(bic2<bic1-10)": int((dist.bic2_minus_bic1_std_matched < -10).sum()),
                                     "frac_dev_beyond_3sd_mean": float(dist.frac_dev_beyond_3sd.mean()),
                                     "frac_std_beyond_3sd_mean": float(dist.frac_std_beyond_3sd.mean()),
                                     "kurtosis_dev_median": float(dist.kurtosis_dev.median()), "kurtosis_std_median": float(dist.kurtosis_std.median())} if len(dist) else {},
               "diffuse_rms_auc_child_mean": float(np.mean(rms_auc)) if rms_auc else None,
               "qc_flag_rate": {"children": int(len(qc)), "reject_rate_std_mean": float(qc.reject_rate_std.mean()), "reject_rate_dev_mean": float(qc.reject_rate_dev.mean()),
                                "children_dev_flagged_more": int((qc.reject_rate_dev > qc.reject_rate_std).sum())} if len(qc) else {}}
    if is_ha:
        summary["frontal_polar_vs_frontocentral_drop"] = {"Fp1+Fp2": float(topo[["Fp1", "Fp2"]].mean()), "Fz+Cz": float(topo[["Fz", "Cz"]].mean()),
                                                          "T3+T4": float(topo[["T3", "T4"]].mean()), "O1+O2+Oz": float(topo[["O1", "O2", "Oz"]].mean())}
    write_json(run["public"] / f"summary_r3_artefact_{args.lane}.json", summary, private=False)
    done(run["private"], "r3_artefact", summary)
    return summary


# ----------------------------------------------------------------------------- r3-peaks

def cmd_r3_peaks(args, config) -> dict:
    torch, device = _torch()
    run = open_run("r3_peaks", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    rate = float(cfg(config, "epoch.rate_hz")); pre_s = float(cfg(config, "epoch.pre_seconds"))
    T = lane.x.shape[2]; win, step = int(0.08 * rate), int(0.04 * rate)
    starts = list(range(0, T - win + 1, step))
    centres = np.array([(s + win / 2) / rate - pre_s for s in starts])
    rows = []
    x_backup = lane.x
    for seed, k, test_children, model in _fold_models(config, args.base_run, lane, device, torch):
        idx = gxd.idx_of_children(lane, test_children)
        base = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
        drops = {c: [] for c in base}
        for s in starts:
            lane.x = x_backup.clone(); lane.x[:, :, s:s + win] = 0
            occ = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
            for c in base:
                drops[c].append(base[c] - occ[c])
        lane.x = x_backup
        for c, d in drops.items():
            d = np.asarray(d); post = centres >= 0.04
            rows.append({"seed": seed, "child": int(c), "n": int(np.sum(lane.child == c)), "auc_base": base[c],
                         "peak_time_s": float(centres[post][np.argmax(d[post])]), "peak_drop": float(d[post].max()),
                         "pre_drop_mean": float(d[~post].mean())})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"child_peaks_{args.lane}.csv", index=False)
    per = f.groupby("child").agg(peak_mean=("peak_time_s", "mean"), peak_range=("peak_time_s", lambda v: v.max() - v.min()),
                                 peak_drop_mean=("peak_drop", "mean"), n=("n", "mean")).reset_index()
    per["age"] = per.child.map(lambda c: lane.age_child[int(c)])
    consistent = per[per.peak_range <= 0.08]
    from scipy.stats import spearmanr
    summary = {"run": args.run, "lane": args.lane, "children": int(len(per)), "seed_consistent_children": int(len(consistent)),
               "peak_time_median_consistent": float(consistent.peak_mean.median()) if len(consistent) else None,
               "fraction_peak_after_120ms": float((consistent.peak_mean > 0.12).mean()) if len(consistent) else None,
               "peak_time_quartiles": [float(q) for q in consistent.peak_mean.quantile([.25, .5, .75])] if len(consistent) else None}
    m = np.isfinite(consistent.age) if len(consistent) else np.array([])
    if len(consistent) and m.sum() >= 12:
        r, p = spearmanr(consistent.peak_mean[m], consistent.age[m])
        # partial: residualise on n trials and drop magnitude
        X = np.column_stack([np.ones(m.sum()), consistent.n[m], consistent.peak_drop_mean[m]])
        rp = consistent.peak_mean[m].to_numpy() - X @ np.linalg.lstsq(X, consistent.peak_mean[m].to_numpy(), rcond=None)[0]
        ra = consistent.age[m].to_numpy() - X @ np.linalg.lstsq(X, consistent.age[m].to_numpy(), rcond=None)[0]
        r2, p2 = spearmanr(rp, ra)
        summary["peak_vs_age"] = {"n": int(m.sum()), "rho": float(r), "p": float(p), "rho_partial_n_drop": float(r2), "p_partial": float(p2)}
    write_json(run["public"] / f"summary_r3_peaks_{args.lane}.json", summary, private=False)
    done(run["private"], "r3_peaks", summary)
    return summary


# ----------------------------------------------------------------------------- r3-memory

def cmd_r3_memory(args, config) -> dict:
    torch, device = _torch()
    run = open_run("r3_memory", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    score, _ = shared_scores(config, args.lane, args.base_run, len(y), lane.n_classes)
    n_since, _ = since_last_deviant(lane)
    dev = (y >= 1) & (n_since >= 0) & np.isfinite(score)
    k = np.clip(n_since, 0, 5)
    # population curve and per-child slopes with empirical-Bayes shrinkage
    pop = {int(b): float(score[dev & (k == b)].mean()) for b in range(6) if np.sum(dev & (k == b)) >= 30}
    rows = []
    for c in np.unique(lane.child):
        sel = dev & (lane.child == c)
        if sel.sum() < 40 or len(np.unique(k[sel])) < 3:
            continue
        sd = score[(lane.child == c) & np.isfinite(score)].std() + 1e-9
        X = np.column_stack([np.ones(sel.sum()), k[sel].astype(float)]); yy = score[sel] / sd
        beta, res, *_ = np.linalg.lstsq(X, yy, rcond=None)
        resid = yy - X @ beta; s2 = float(resid @ resid) / max(1, sel.sum() - 2)
        se = float(np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1]))
        rows.append({"child": int(c), "n_dev": int(sel.sum()), "slope_sd_per_step": float(beta[1]), "slope_se": se, "age": float(lane.age_child[c])})
    f = pd.DataFrame(rows)
    if len(f):
        w = 1.0 / (f.slope_se ** 2)
        mu = float(np.average(f.slope_sd_per_step, weights=w))
        tau2 = max(float(f.slope_sd_per_step.var() - (f.slope_se ** 2).mean()), 1e-6)
        f["slope_shrunk"] = mu + (f.slope_sd_per_step - mu) * (tau2 / (tau2 + f.slope_se ** 2))
        f["shrinkage_factor"] = tau2 / (tau2 + f.slope_se ** 2)
    f.to_csv(run["public"] / f"memory_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "population_deviant_score_by_preceding_standards": pop,
               "children": int(len(f)), "slope_mean_sd_per_step": float(f.slope_sd_per_step.mean()) if len(f) else None,
               "slope_pooled_mu": float(mu) if len(f) else None, "between_child_tau": float(np.sqrt(tau2)) if len(f) else None,
               "median_se": float(f.slope_se.median()) if len(f) else None, "shrinkage_factor_median": float(f.shrinkage_factor.median()) if len(f) else None,
               "children_positive": int((f.slope_sd_per_step > 0).sum()) if len(f) else 0}
    if len(f):
        m = np.isfinite(f.age)
        if m.sum() >= 12:
            from scipy.stats import spearmanr
            r, p = spearmanr(f.slope_shrunk[m], f.age[m])
            X = np.column_stack([np.ones(m.sum()), f.n_dev[m]])
            rs = f.slope_shrunk[m].to_numpy() - X @ np.linalg.lstsq(X, f.slope_shrunk[m].to_numpy(), rcond=None)[0]
            ra = f.age[m].to_numpy() - X @ np.linalg.lstsq(X, f.age[m].to_numpy(), rcond=None)[0]
            r2, p2 = spearmanr(rs, ra)
            summary["slope_vs_age"] = {"n": int(m.sum()), "rho": float(r), "p": float(p), "rho_partial_ntrials": float(r2), "p_partial": float(p2)}
    write_json(run["public"] / f"summary_r3_memory_{args.lane}.json", summary, private=False)
    done(run["private"], "r3_memory", summary)
    return summary


# ----------------------------------------------------------------------------- r3-pitch

def cmd_r3_pitch(args, config) -> dict:
    torch, device = _torch()
    from sklearn.metrics import roc_auc_score
    run = open_run("r3_pitch", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), "mff_unknown_hdev_ldev", device)
    y = lane.y.cpu().numpy()
    _, logits = shared_scores(config, lane.name, args.base_run, len(y), lane.n_classes)
    ok = np.isfinite(logits[:, 0])
    n_since, _ = since_last_deviant(lane)
    prev_dev = np.full(len(y), -1)
    for r in np.unique(lane.record):
        idx = np.flatnonzero(lane.record == r); idx = idx[np.argsort(lane.onset_s[idx])]
        last = -1
        for i in idx:
            prev_dev[i] = last
            if y[i] >= 1:
                last = int(y[i])
    rows = []
    for c in np.unique(lane.child):
        sel = ok & (lane.child == c)
        yy = y[sel]
        if (yy == 1).sum() < 20 or (yy == 2).sum() < 20:
            continue
        s_h = logits[sel, 1] - logits[sel, 0]; s_l = logits[sel, 2] - logits[sel, 0]
        m_h = yy != 2; m_l = yy != 1
        rows.append({"child": int(c), "auc_std_vs_high": float(roc_auc_score(yy[m_h] == 1, s_h[m_h])),
                     "auc_std_vs_low": float(roc_auc_score(yy[m_l] == 2, s_l[m_l])),
                     "auc_high_vs_low": float(roc_auc_score(yy[yy > 0] == 2, (logits[sel, 2] - logits[sel, 1])[yy > 0]))})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / "pitch_asymmetry.csv", index=False)
    # order effect: deviant readability by the class of the previous deviant, within strata of preceding standards
    order_rows = []
    dev_score = np.where(y == 1, logits[:, 1] - logits[:, 0], logits[:, 2] - logits[:, 0])
    for c in np.unique(lane.child):
        base = ok & (lane.child == c) & (y >= 1) & (prev_dev > 0) & (n_since >= 0)
        sd = np.nanstd(dev_score[ok & (lane.child == c)]) + 1e-9
        for stratum, mask in (("0-1_std", n_since <= 1), ("2-3_std", (n_since >= 2) & (n_since <= 3)), ("4+_std", n_since >= 4)):
            for cls in (1, 2):
                same = base & mask & (y == cls) & (prev_dev == cls); diff = base & mask & (y == cls) & (prev_dev != cls)
                if same.sum() >= 5 and diff.sum() >= 5:
                    order_rows.append({"child": int(c), "stratum": stratum, "deviant_class": cls, "n_same": int(same.sum()), "n_diff": int(diff.sum()),
                                       "same_minus_diff_sd": float((dev_score[same].mean() - dev_score[diff].mean()) / sd)})
    o = pd.DataFrame(order_rows)
    o.to_csv(run["public"] / "pitch_order.csv", index=False)
    summary = {"run": args.run, "children": int(len(f)),
               "order_effect_same_minus_diff_sd": {f"{s}/class{k}": {"mean": float(d.same_minus_diff_sd.mean()), "children": int(len(d)),
                                                                     "children_negative": int((d.same_minus_diff_sd < 0).sum())}
                                                   for (s, k), d in o.groupby(["stratum", "deviant_class"])} if len(o) else {},
               "auc_std_vs_high_mean": float(f.auc_std_vs_high.mean()), "auc_std_vs_low_mean": float(f.auc_std_vs_low.mean()),
               "children_high_more_readable": int((f.auc_std_vs_high > f.auc_std_vs_low).sum()),
               "auc_high_vs_low_mean": float(f.auc_high_vs_low.mean()),
               "note": "acoustic step sizes of the two deviants are not recorded in the archive; asymmetry is descriptive"}
    write_json(run["public"] / "summary_r3_pitch.json", summary, private=False)
    done(run["private"], "r3_pitch", summary)
    return summary


# ----------------------------------------------------------------------------- r3-records (swap check, drift source, first-N)

def cmd_r3_records(args, config) -> dict:
    torch, device = _torch()
    from sklearn.metrics import roc_auc_score
    run = open_run("r3_records", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    seg_s = float(cfg(config, "blocks.segment_seconds"))
    rate = float(cfg(config, "epoch.rate_hz")); pre = int(round(float(cfg(config, "epoch.pre_seconds")) * rate))
    rms = torch.sqrt((lane.x[:, :, pre:].float() ** 2).mean(dim=(1, 2))).cpu().numpy()
    per_seed = {}
    with np.load(private_dir(config, args.base_run) / "predictions_shared.npz", allow_pickle=False) as store:
        for key in store.files:
            arr = store[key]; seed = int(key.split("_s")[1].split("_")[0])
            per_seed.setdefault(seed, np.full(len(y), np.nan))
            per_seed[seed][arr[:, 0].astype(int)] = arr[:, 2] - arr[:, 1]
    score = np.nanmean(np.stack(list(per_seed.values())), 0)
    swap_rows, drift_rows, firstn_rows = [], [], []
    rng = np.random.default_rng(11)
    for r, meta in enumerate(lane.record_meta):
        idx = np.flatnonzero((lane.record == r) & np.isfinite(score))
        yy = y[idx]
        if len(np.unique(yy)) < 2:
            continue
        aucs = {s: float(roc_auc_score(yy, v[idx])) for s, v in per_seed.items() if np.isfinite(v[idx]).all()}
        swap_rows.append({"record": meta["record_id"], "child": meta["child"], **{f"auc_seed{s}": a for s, a in aucs.items()},
                          "all_seeds_below_half": bool(aucs and all(a < 0.5 for a in aucs.values())),
                          "all_seeds_above_half": bool(aucs and all(a > 0.5 for a in aucs.values()))})
        # drift source: per segment, standard score vs qc_over and rms
        order = idx[np.argsort(lane.onset_s[idx])]
        t0 = lane.onset_s[order].min()
        seg = np.floor((lane.onset_s[order] - t0) / seg_s).astype(int)
        for s_ in np.unique(seg):
            q = order[seg == s_]; qs = q[y[q] == 0]
            if len(qs) >= 20:
                drift_rows.append({"record": meta["record_id"], "segment": int(s_), "std_score": float(score[qs].mean()),
                                   "qc_over": float(lane.qc_over[q].mean()), "rms": float(rms[q].mean()), "n": int(len(q))})
        for n in (100, 200, 400, 800):
            if len(order) >= n:
                first = order[:n]
                rand = rng.choice(order, size=n, replace=False)
                if len(np.unique(y[first])) == 2 and len(np.unique(y[rand])) == 2:
                    firstn_rows.append({"record": meta["record_id"], "n": n, "auc_first_n": float(roc_auc_score(y[first], score[first])),
                                        "auc_random_n": float(roc_auc_score(y[rand], score[rand])), "auc_full": float(roc_auc_score(yy, score[idx]))})
    swap, drift, firstn = pd.DataFrame(swap_rows), pd.DataFrame(drift_rows), pd.DataFrame(firstn_rows)
    swap.to_csv(run["public"] / f"record_seed_auc_{args.lane}.csv", index=False)
    drift.to_csv(run["public"] / f"drift_source_{args.lane}.csv", index=False)
    firstn.to_csv(run["public"] / f"first_n_{args.lane}.csv", index=False)
    from scipy.stats import spearmanr
    summary = {"run": args.run, "lane": args.lane, "records": int(len(swap)),
               "records_all_seeds_below_half": int(swap.all_seeds_below_half.sum()), "records_all_seeds_above_half": int(swap.all_seeds_above_half.sum())}
    if len(drift):
        d = drift.copy()
        d["std_score_c"] = d.std_score - d.groupby("record").std_score.transform("mean")
        d["qc_c"] = d.qc_over - d.groupby("record").qc_over.transform("mean")
        d["rms_c"] = d.rms - d.groupby("record").rms.transform("mean")
        d["seg_c"] = d.segment - d.groupby("record").segment.transform("mean")
        summary["drift_within_record_spearman"] = {"score_vs_segment": float(spearmanr(d.std_score_c, d.seg_c).correlation),
                                                    "score_vs_qc": float(spearmanr(d.std_score_c, d.qc_c).correlation),
                                                    "score_vs_rms": float(spearmanr(d.std_score_c, d.rms_c).correlation),
                                                    "qc_vs_segment": float(spearmanr(d.qc_c, d.seg_c).correlation),
                                                    "rms_vs_segment": float(spearmanr(d.rms_c, d.seg_c).correlation), "segments": int(len(d))}
    if len(firstn):
        summary["first_n"] = {int(n): {"records": int(len(g)), "auc_first_n_mean": float(g.auc_first_n.mean()), "auc_random_n_mean": float(g.auc_random_n.mean()),
                                       "abs_err_first_vs_full": float((g.auc_first_n - g.auc_full).abs().mean()),
                                       "abs_err_random_vs_full": float((g.auc_random_n - g.auc_full).abs().mean())} for n, g in firstn.groupby("n")}
    write_json(run["public"] / f"summary_r3_records_{args.lane}.json", summary, private=False)
    done(run["private"], "r3_records", summary)
    return summary


# ----------------------------------------------------------------------------- r3-agematrix (GPU)

def cmd_r3_agematrix(args, config) -> dict:
    torch, device = _torch()
    run = open_run("r3_agematrix", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    with_age = np.flatnonzero(np.isfinite(lane.age_child))
    order = with_age[np.argsort(lane.age_child[with_age])]
    tertiles = [order[i::3] for i in range(3)]        # interleaved -> equal N, but we want contiguous age groups:
    n = len(order) // 3
    tertiles = [order[:n], order[n:2 * n], order[2 * n:3 * n]]
    src = {}
    for m in lane.record_meta:
        src.setdefault(m["child"], m["source_cohort_evidence"])
    seeds = [int(s) for s in cfg(config, "folds.seeds")]
    val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rows = []
    for seed in seeds:
        for a, train_t in enumerate(tertiles):
            tr, va = gxd.split_inner(train_t, val_frac, seed + a)
            gxt.seed_all(seed * 10 + a)
            model = gxt.build_model(config, lane)
            gxt.fit(model, lane, gxd.idx_of_children(lane, tr), gxd.idx_of_children(lane, va), config, seed=seed * 10 + a)
            for b, test_t in enumerate(tertiles):
                if a == b:
                    continue
                idx = gxd.idx_of_children(lane, test_t)
                aucs = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
                rows.append({"seed": seed, "train_tertile": a, "test_tertile": b, "auc_child_mean": float(np.nanmean(list(aucs.values()))), "children": len(aucs)})
            # within-tertile child-held-out via 3 folds
            folds = gxd.child_folds(len(train_t), 3, seed)
            within = []
            for k, f in enumerate(folds):
                test_c = train_t[f]; train_c = np.setdiff1d(train_t, test_c)
                tr2, va2 = gxd.split_inner(train_c, val_frac, seed * 7 + k)
                gxt.seed_all(seed * 100 + a * 10 + k)
                m2 = gxt.build_model(config, lane)
                gxt.fit(m2, lane, gxd.idx_of_children(lane, tr2), gxd.idx_of_children(lane, va2), config, seed=seed * 100 + a * 10 + k)
                idx = gxd.idx_of_children(lane, test_c)
                within += list(_child_auc(lane, idx, gxt.predict(m2, lane, idx), y).values())
            rows.append({"seed": seed, "train_tertile": a, "test_tertile": a, "auc_child_mean": float(np.nanmean(within)), "children": len(within)})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"age_matrix_{args.lane}.csv", index=False)
    mat = f.groupby(["train_tertile", "test_tertile"]).auc_child_mean.mean().unstack()
    summary = {"run": args.run, "lane": args.lane, "children_with_age": int(len(with_age)),
               "tertile_age_ranges": [[float(lane.age_child[t].min()), float(lane.age_child[t].max())] for t in tertiles],
               "tertile_source_mix": [dict(pd.Series([src.get(int(c), "") for c in t]).value_counts()) for t in tertiles],
               "matrix_train_rows_test_cols": mat.round(4).to_dict()}
    summary["tertile_source_mix"] = [{k: int(v) for k, v in d.items()} for d in summary["tertile_source_mix"]]
    write_json(run["public"] / f"summary_r3_agematrix_{args.lane}.json", summary, private=False)
    done(run["private"], "r3_agematrix", summary)
    return summary


# ----------------------------------------------------------------------------- r3-nh classification (CPU-light)

def cmd_r3_nh_classify(args, config) -> dict:
    run = open_run("r3_nh_classify", args.run, config, args=vars(args))
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler
    import csv
    labels = {r["container_id"]: r["source_label_expanded"] for r in csv.DictReader(open(ROOT / "results/phase3_metadata_addendum_001/source_metadata.csv"))}
    out = {"run": args.run}
    for lane, gx8, inst in (("bdf_puretone", "GX8_bdf_puretone", "R2_instrument_bdf_puretone"), ("mff_bapa", "GX8_mff_bapa", "R2_instrument_mff_bapa")):
        rec = pd.read_csv(results_dir(config, gx8) / f"record_auc_{lane}.csv")
        cal = pd.read_csv(results_dir(config, inst) / f"calibration_{lane}.csv")
        blocks = pd.read_csv(results_dir(config, inst) / f"record_auc_blocks_{lane}.csv")
        rec["nh"] = (rec.source == "NH") if lane == "bdf_puretone" else rec.record.map(labels).eq("normal_literal")
        per_child = rec.groupby("child").agg(auc=("auc", "mean"), nh=("nh", "max"), n=("n", "mean")).reset_index()
        per_child = per_child.merge(cal[["child", "calibration_slope", "balanced_brier"]], on="child", how="left")
        if "auc_block0" in blocks:
            bd = blocks.assign(block_diff=(blocks.auc_block0 - blocks.auc_block1).abs()).groupby("child").block_diff.mean().reset_index()
            per_child = per_child.merge(bd, on="child", how="left")
        feats = [c for c in ("auc", "calibration_slope", "balanced_brier", "block_diff") if c in per_child]
        X = per_child[feats].fillna(per_child[feats].median()).to_numpy(); yv = per_child.nh.astype(int).to_numpy()
        if yv.sum() < 4:
            out[lane] = {"nh": int(yv.sum()), "note": "too few NH"}
            continue
        # leave-one-out logistic
        scores = np.zeros(len(yv))
        for i in range(len(yv)):
            m = np.ones(len(yv), bool); m[i] = False
            sc = StandardScaler().fit(X[m])
            clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=1000).fit(sc.transform(X[m]), yv[m])
            scores[i] = clf.decision_function(sc.transform(X[i:i + 1]))[0]
        auc = float(roc_auc_score(yv, scores))
        rng = np.random.default_rng(0); null = []
        for _ in range(500):
            yp = rng.permutation(yv); s2 = np.zeros(len(yv))
            for i in range(len(yv)):
                m = np.ones(len(yv), bool); m[i] = False
                sc = StandardScaler().fit(X[m]); clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=1000).fit(sc.transform(X[m]), yp[m])
                s2[i] = clf.decision_function(sc.transform(X[i:i + 1]))[0]
            null.append(roc_auc_score(yp, s2))
        out[lane] = {"children": int(len(yv)), "nh": int(yv.sum()), "features": feats, "loo_auc": auc,
                     "permutation_p": float((np.sum(np.asarray(null) >= auc) + 1) / (len(null) + 1)), "null_auc_mean": float(np.mean(null)),
                     "univariate_auc": {f: float(roc_auc_score(yv, per_child[f].fillna(per_child[f].median()))) for f in feats}}
    write_json(run["public"] / "summary_r3_nh_classify.json", out, private=False)
    done(run["private"], "r3_nh_classify", out)
    return out
