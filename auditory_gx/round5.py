"""Round-5: continuous late-cluster weight, its reliability and confounds, template models, latency alignment,
graded repetition suppression, full-band vs 30-45 Hz trial-level independence, joint structure."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .round2 import shared_scores, since_last_deviant
from .round3 import HA_CHANNELS, _child_auc, _fold_models
from .round4 import _override, _partial_spearman, _spearman
from .runtime import ROOT, cfg, done, open_run, private_dir, read_json, results_dir, write_json_overwrite as write_json

PTA_TABLE = ROOT / "private/auditory_repair/pta_007/candidate_covariates.csv"
LEFT = ["Fp1", "F3", "F7", "C3", "T3", "P3", "T5", "O1"]
RIGHT = ["Fp2", "F4", "F8", "C4", "T4", "P4", "T6", "O2"]


def _windows(config, T):
    rate = float(cfg(config, "epoch.rate_hz")); pre_s = float(cfg(config, "epoch.pre_seconds"))
    win, step = int(0.08 * rate), int(0.04 * rate)
    starts = list(range(0, T - win + 1, step))
    return rate, pre_s, win, starts, np.array([(s + win / 2) / rate - pre_s for s in starts])


def _auc_subsets(lane, idx, logits, y, subsets):
    """AUC per (child, subset) from one set of logits over idx; subsets: dict name -> boolean mask over idx."""
    from sklearn.metrics import roc_auc_score
    score = logits[:, 1] - logits[:, 0]; out = {}
    for c in np.unique(lane.child[idx]):
        cm = lane.child[idx] == c
        for name, mask in subsets.items():
            sel = cm & mask; yy = y[idx][sel]
            if (yy == 1).sum() >= 10 and (yy == 0).sum() >= 20:
                out[(int(c), name)] = float(roc_auc_score(yy, score[sel]))
    return out


# ----------------------------------------------------------------------------- r5-curves (inference)

def cmd_r5_curves(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r5_curves", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy(); T = lane.x.shape[2]
    rate, pre_s, win, starts, centres = _windows(config, T)
    names = list(HA_CHANNELS) if lane.x.shape[1] == 20 else None
    # per-trial order within record for first-N and odd/even
    order_in_record = np.zeros(len(y), dtype=int)
    for r in np.unique(lane.record):
        idx = np.flatnonzero(lane.record == r); idx = idx[np.argsort(lane.onset_s[idx])]
        order_in_record[idx] = np.arange(len(idx))
    multi_children = {c for c in range(lane.n_children) if len(np.unique(lane.record[lane.child == c])) >= 2}
    rows, hemi = [], []
    x_backup = lane.x
    for seed, k, test_children, model in _fold_models(config, args.base_run, lane, device, torch):
        idx = gxd.idx_of_children(lane, test_children)
        subsets = {"all": np.ones(len(idx), bool), "odd": order_in_record[idx] % 2 == 1, "even": order_in_record[idx] % 2 == 0,
                   "first200": order_in_record[idx] < 200, "first400": order_in_record[idx] < 400, "first800": order_in_record[idx] < 800}
        for c in test_children:
            if c in multi_children:
                for r in np.unique(lane.record[lane.child == c]):
                    subsets[f"rec:{lane.record_ids[int(r)]}"] = lane.record[idx] == r
        base = _auc_subsets(lane, idx, gxt.predict(model, lane, idx), y, subsets)
        for s, centre in zip(starts, centres):
            lane.x = x_backup.clone(); lane.x[:, :, s:s + win] = 0
            occ = _auc_subsets(lane, idx, gxt.predict(model, lane, idx), y, subsets)
            for key, b in base.items():
                if key in occ:
                    rows.append({"seed": seed, "child": key[0], "subset": key[1], "centre_s": float(centre), "auc_base": b, "drop": b - occ[key]})
        if names:
            for side, chans in (("left", [names.index(n) for n in LEFT]), ("right", [names.index(n) for n in RIGHT])):
                lane.x = x_backup.clone(); lane.x[:, chans, :] = 0
                occ = _auc_subsets(lane, idx, gxt.predict(model, lane, idx), y, {"all": subsets["all"]})
                for key, b in base.items():
                    if key[1] == "all" and key in occ:
                        hemi.append({"seed": seed, "child": key[0], "side": side, "auc_base": b, "drop": b - occ[key]})
        lane.x = x_backup
    f = pd.DataFrame(rows); f.to_csv(run["public"] / f"curves_{args.lane}.csv", index=False)
    h = pd.DataFrame(hemi); h.to_csv(run["public"] / f"hemisphere_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "children": int(f.child.nunique()), "subsets": sorted(f.subset.unique().tolist())[:12], "windows": len(starts)}
    write_json(run["public"] / f"summary_r5_curves_{args.lane}.json", summary, private=False)
    done(run["private"], "r5_curves", summary)
    return summary


# ----------------------------------------------------------------------------- r5-wlate (CPU)

def _nnls2(curve, e, l):
    from scipy.optimize import nnls
    A = np.column_stack([e, l]); w, _ = nnls(A, curve)
    return w


def cmd_r5_wlate(args, config) -> dict:
    run = open_run("r5_wlate", args.run, config, args=vars(args))
    lane = "bdf_puretone"
    cv = pd.read_csv(results_dir(config, args.curves_run) / f"curves_{lane}.csv")
    cv = cv[cv.centre_s >= 0.04]
    mean = cv.groupby(["child", "subset", "centre_s"]).agg(drop=("drop", "mean"), auc=("auc_base", "mean")).reset_index()
    centres = np.sort(mean.centre_s.unique())
    def curve_of(child, subset):
        d = mean[(mean.child == child) & (mean.subset == subset)].sort_values("centre_s")
        return d["drop"].to_numpy() if len(d) == len(centres) else None
    # child covariates
    from .round4 import _child_table_ha
    t = _child_table_ha(config)
    rec = pd.read_csv(results_dir(config, "GX8_bdf_puretone") / "record_auc_bdf_puretone.csv")
    scale = rec.groupby("child").agg(record_scale=("record_scale", "mean"), n_trials=("n", "sum")).reset_index()
    t = t.merge(scale, on="child", how="left")
    if PTA_TABLE.exists():
        pta = pd.read_csv(PTA_TABLE)[["recording_id", "better_unaided_pta", "better_aided_pta"]].rename(columns={"recording_id": "record"})
        rp = rec[["record", "child"]].merge(pta, on="record", how="inner").groupby("child").agg(pta_unaided=("better_unaided_pta", "mean"), pta_aided=("better_aided_pta", "mean")).reset_index()
        t = t.merge(rp, on="child", how="left"); t["aided_gain"] = t.pta_unaided - t.pta_aided
    t["fitting_age"] = t.age - t.duration
    t["dur_bin"] = pd.cut(t.duration, [-1, 2, 12, 36, 400], labels=["0-2", "3-12", "13-36", ">36"]).astype(str)
    t.loc[t.source == "NH", "dur_bin"] = "NH"
    # 1a. bin-mean curves: shape description without clustering
    early_w = (centres >= 0.10) & (centres <= 0.18); late_w = (centres >= 0.22) & (centres <= 0.30)
    bins = {}
    for b, g in t.groupby("dur_bin"):
        cs = [curve_of(c, "all") for c in g.child]; cs = [c for c in cs if c is not None]
        if not cs:
            continue
        m = np.mean(cs, 0)
        bins[b] = {"children": len(cs), "peak_centre_s": float(centres[np.argmax(m)]), "early_window_drop": float(m[early_w].mean()), "late_window_drop": float(m[late_w].mean()),
                   "late_over_early": float(m[late_w].mean() / max(m[early_w].mean(), 1e-6)), "curve": [float(v) for v in m]}
    # 1b. two templates from R3 consistent clusters, NNLS weights
    pk = pd.read_csv(results_dir(config, "R3_peaks_bdf_puretone") / "child_peaks_bdf_puretone.csv").groupby("child").agg(peak=("peak_time_s", "mean"), rng=("peak_time_s", lambda v: v.max() - v.min())).reset_index()
    early_children = pk[(pk.rng <= 0.08) & (pk.peak < 0.2)].child.tolist(); late_children = pk[(pk.rng <= 0.08) & (pk.peak >= 0.2)].child.tolist()
    E = np.mean([curve_of(c, "all") for c in early_children if curve_of(c, "all") is not None], 0); L = np.mean([curve_of(c, "all") for c in late_children if curve_of(c, "all") is not None], 0)
    E = np.clip(E, 0, None); L = np.clip(L, 0, None)
    wl = {}
    for (c, s), g in mean.groupby(["child", "subset"]):
        cur = curve_of(c, s)
        if cur is None:
            continue
        w = _nnls2(np.clip(cur, 0, None), E, L); tot = w.sum()
        wl[(c, s)] = float(w[1] / tot) if tot > 1e-9 else np.nan
    W = pd.Series(wl).unstack(); W.index.name = "child"; W.to_csv(run["public"] / "w_late_by_subset.csv")
    t["w_late"] = t.child.map(W["all"] if "all" in W else {})
    t["w_late_odd"] = t.child.map(W["odd"]); t["w_late_even"] = t.child.map(W["even"])
    aucs = mean.groupby(["child", "subset"]).auc.first().unstack()
    t["auc_odd"] = t.child.map(aucs["odd"]); t["auc_even"] = t.child.map(aucs["even"])
    t.to_csv(run["public"] / "child_table_r5.csv", index=False)
    ha = t[t.source == "HA"]; nh = t[t.source == "NH"]
    out = {"run": args.run, "children": int(len(t)), "templates": {"early_children": len(early_children), "late_children": len(late_children), "centres_s": [float(c) for c in centres],
                                                               "early_template": [float(v) for v in E], "late_template": [float(v) for v in L]},
           "bin_mean_curves": bins,
           "w_late": {"mean_ha": float(ha.w_late.mean()), "mean_nh": float(nh.w_late.mean()), "by_dur_bin": {b: {"n": int(g.w_late.notna().sum()), "mean": float(g.w_late.mean()), "median": float(g.w_late.median())} for b, g in t.groupby("dur_bin")}},
           "reliability": {"w_late_odd_vs_even": _spearman(t.w_late_odd, t.w_late_even), "auc_odd_vs_even": _spearman(t.auc_odd, t.auc_even),
                           "w_late_odd_even_abs_diff_median": float((t.w_late_odd - t.w_late_even).abs().median())}}
    # two-visit record-level w_late
    recs = [s for s in W.columns if s.startswith("rec:")]
    two = []
    for c in W.index:
        vals = [W.loc[c, s] for s in recs if not np.isnan(W.loc[c, s])] if recs else []
        if len(vals) >= 2:
            two.append({"child": int(c), "w1": float(vals[0]), "w2": float(vals[1])})
    two = pd.DataFrame(two)
    out["reliability"]["two_visit_w_late"] = _spearman(two.w1, two.w2) if len(two) else {"n": 0}
    out["reliability"]["two_visit_abs_diff_median"] = float((two.w1 - two.w2).abs().median()) if len(two) else None
    # first-N stability
    out["first_n_abs_error_median"] = {s: float((W[s] - W["all"]).abs().median()) for s in ("first200", "first400", "first800") if s in W}
    # 3. confound table (HA only)
    covs = {"log_duration": np.log1p(ha.duration), "fitting_age": ha.fitting_age, "age": ha.age, "pta_unaided": ha.get("pta_unaided"), "pta_aided": ha.get("pta_aided"),
            "aided_gain": ha.get("aided_gain"), "record_scale": ha.record_scale, "n_trials": ha.n_trials, "auc": ha.auc}
    out["w_late_confounds_ha"] = {k: {"spearman": _spearman(ha.w_late, v), "partial_given_age": _partial_spearman(ha.w_late, v, ha.age)} for k, v in covs.items() if v is not None}
    # within-duration-bin fitting-age split
    split = {}
    for b, g in ha.groupby("dur_bin"):
        g = g[g.fitting_age.notna() & g.w_late.notna()]
        if len(g) >= 6:
            med = g.fitting_age.median(); lo = g[g.fitting_age <= med]; hi = g[g.fitting_age > med]
            split[b] = {"n_early_fit": int(len(lo)), "n_late_fit": int(len(hi)), "w_late_early_fit": float(lo.w_late.mean()), "w_late_late_fit": float(hi.w_late.mean()), "fitting_age_median": float(med)}
    out["fitting_age_within_duration_bin"] = split
    # convergence with memory slope; adequate subset
    out["w_late_vs_memory_slope"] = _spearman(ha.w_late, ha.slope_sd_per_step)
    adequate = ha[ha.n_trials >= 800]
    out["adequate_subset"] = {"n": int(len(adequate)), "w_late_vs_log_duration_partial_age": _partial_spearman(adequate.w_late, np.log1p(adequate.duration), adequate.age)}
    # 4a. spatial fingerprint by cluster (R3 channel-group occlusion)
    occ = pd.read_csv(results_dir(config, "R3_artefact_bdf_puretone") / "channel_occlusion_bdf_puretone.csv")
    occ = occ[occ.group.str.contains(r"\+")].groupby(["child", "group"])["drop"].mean().unstack()
    occ["cluster"] = np.where(occ.index.isin(early_children), "early", np.where(occ.index.isin(late_children), "late", "other"))
    occ["auc_tertile"] = pd.qcut(t.set_index("child").auc.reindex(occ.index), 3, labels=["low", "mid", "high"]).astype(str)
    fp = {cl: {g: float(v) for g, v in d.drop(columns=["cluster", "auc_tertile"]).mean().items()} for cl, d in occ.groupby("cluster")}
    fp_t = {f"{cl}/{tt}": {g: float(v) for g, v in d.drop(columns=["cluster", "auc_tertile"]).mean().items()} for (cl, tt), d in occ.groupby(["cluster", "auc_tertile"]) if len(d) >= 4}
    out["spatial_fingerprint_by_cluster"] = {"mean": fp, "by_auc_tertile": fp_t}
    # 8. hemisphere asymmetry
    hp = results_dir(config, args.curves_run) / f"hemisphere_{lane}.csv"
    if hp.exists():
        hm = pd.read_csv(hp).groupby(["child", "side"])["drop"].mean().unstack(); hm["asym_left_minus_right"] = hm.left - hm.right
        t = t.merge(hm[["asym_left_minus_right", "left", "right"]].reset_index(), on="child", how="left"); ha = t[t.source == "HA"]; nh = t[t.source == "NH"]
        out["hemisphere"] = {"mean_left_drop_ha": float(ha.left.mean()), "mean_right_drop_ha": float(ha.right.mean()), "children_left_larger_ha": int((ha.left > ha.right).sum()), "n_ha": int(ha.left.notna().sum()),
                             "nh_asym_mean": float(nh.asym_left_minus_right.mean()), "ha_asym_mean": float(ha.asym_left_minus_right.mean()),
                             "asym_vs_log_duration_partial_age": _partial_spearman(ha.asym_left_minus_right, np.log1p(ha.duration), ha.age), "asym_vs_age": _spearman(ha.asym_left_minus_right, ha.age),
                             "asym_vs_w_late": _spearman(ha.asym_left_minus_right, ha.w_late), "asym_by_dur_bin": {b: float(g.asym_left_minus_right.mean()) for b, g in t.groupby("dur_bin")}}
        t.to_csv(run["public"] / "child_table_r5.csv", index=False)
    write_json(run["public"] / "summary_r5_wlate.json", out, private=False)
    done(run["private"], "r5_wlate", out)
    return out


# ----------------------------------------------------------------------------- r5-templates (GPU)

def cmd_r5_templates(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r5_templates", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), "bdf_puretone", device)
    y = lane.y.cpu().numpy()
    pk = pd.read_csv(results_dir(config, "R3_peaks_bdf_puretone") / "child_peaks_bdf_puretone.csv").groupby("child").agg(peak=("peak_time_s", "mean"), rng=("peak_time_s", lambda v: v.max() - v.min())).reset_index()
    groups = {"early": np.array(sorted(pk[(pk.rng <= 0.08) & (pk.peak < 0.2)].child)), "late": np.array(sorted(pk[(pk.rng <= 0.08) & (pk.peak >= 0.2)].child))}
    src = {m["child"]: m["source_cohort_evidence"] for m in lane.record_meta}
    dur = {m["child"]: m["device_duration_months"] for m in lane.record_meta}
    ov = _override().set_index("record_id")
    for m in lane.record_meta:
        if m["record_id"] in ov.index:
            dur[m["child"]] = float(ov.loc[m["record_id"], "device_duration_months"])
    tags = {c: ("NH" if src.get(c) == "NH" else ("new" if (dur.get(c) is not None and np.isfinite(dur.get(c)) and dur.get(c) <= 2) else "HA")) for c in range(lane.n_children)}
    seeds = [int(s) for s in cfg(config, "folds.seeds")]; val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rows = []
    for gname, members in groups.items():
        other = groups["late" if gname == "early" else "early"]
        for seed in seeds:
            folds = gxd.child_folds(len(members), 5, seed)
            for k, f in enumerate(folds):
                test_in = members[f]; train_c = np.setdiff1d(members, test_in)
                tr, va = gxd.split_inner(train_c, val_frac, seed + k)
                gxt.seed_all(seed * 100 + k + (0 if gname == "early" else 50))
                model = gxt.build_model(config, lane)
                gxt.fit(model, lane, gxd.idx_of_children(lane, tr), gxd.idx_of_children(lane, va), config, seed=seed * 100 + k + (0 if gname == "early" else 50))
                eval_children = np.setdiff1d(np.arange(lane.n_children), train_c)   # everyone not used for training (incl. held-out same-cluster)
                idx = gxd.idx_of_children(lane, eval_children)
                aucs = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
                for c, a in aucs.items():
                    kind = "within" if c in test_in else ("cross" if c in other else "other")
                    rows.append({"template": gname, "seed": seed, "fold": k, "child": int(c), "kind": kind, "tag": tags.get(c, "HA"), "auc": a})
    f = pd.DataFrame(rows); f.to_csv(run["public"] / "templates.csv", index=False)
    pc = f.groupby(["template", "kind", "child"]).auc.mean().reset_index()
    summary = {"run": args.run, "early_children": int(len(groups["early"])), "late_children": int(len(groups["late"])),
               "auc_by_template_and_kind": {f"{tp}/{kd}": {"children": int(len(d)), "auc_mean": float(d.auc.mean())} for (tp, kd), d in pc.groupby(["template", "kind"])}}
    ft = f.groupby(["template", "tag", "child"]).auc.mean().reset_index()
    summary["auc_by_template_and_tag(not_in_training)"] = {f"{tp}/{tg}": {"children": int(len(d)), "auc_mean": float(d.auc.mean())} for (tp, tg), d in ft.groupby(["template", "tag"])}
    write_json(run["public"] / "summary_r5_templates.json", summary, private=False)
    done(run["private"], "r5_templates", summary)
    return summary


# ----------------------------------------------------------------------------- r5-align (GPU)

def _shift_time(x, s):
    """Shift along time by s samples with zero fill (positive s = move content earlier)."""
    import torch
    out = torch.zeros_like(x)
    if s > 0:
        out[..., :-s] = x[..., s:]
    elif s < 0:
        out[..., -s:] = x[..., :s]
    else:
        out.copy_(x)
    return out


def cmd_r5_align(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r5_align", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), "bdf_puretone", device)
    y = lane.y.cpu().numpy(); rate = float(cfg(config, "epoch.rate_hz"))
    cv = pd.read_csv(results_dir(config, args.curves_run) / "curves_bdf_puretone.csv"); cv = cv[cv.centre_s >= 0.04]
    mean = cv.groupby(["child", "subset", "centre_s"])["drop"].mean().reset_index()
    peaks = mean.loc[mean.groupby(["child", "subset"])["drop"].idxmax()][["child", "subset", "centre_s"]]
    pk = peaks.pivot(index="child", columns="subset", values="centre_s")
    median_peak = float(pk["all"].median())
    shift_samples = lambda p: int(round((p - median_peak) * rate)) if np.isfinite(p) else 0
    order_in_record = np.zeros(len(y), dtype=int)
    for r in np.unique(lane.record):
        idx = np.flatnonzero(lane.record == r); idx = idx[np.argsort(lane.onset_s[idx])]; order_in_record[idx] = np.arange(len(idx))
    seeds = [int(s) for s in cfg(config, "folds.seeds")]; n_folds = int(cfg(config, "folds.n_child_folds")); val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    rng = np.random.default_rng(11)
    x_orig = lane.x
    rows = []
    for mode in ("aligned", "random_control"):
        # child -> shift (train uses full-data peak; control permutes the shifts across children)
        full_shift = {c: shift_samples(pk["all"].get(c, np.nan)) for c in range(lane.n_children)}
        if mode == "random_control":
            vals = np.array(list(full_shift.values())); rng.shuffle(vals); full_shift = {c: int(v) for c, v in zip(full_shift, vals)}
        for seed in seeds:
            folds = gxd.child_folds(lane.n_children, n_folds, seed)
            for k, test_children in enumerate(folds):
                train_children = np.setdiff1d(np.arange(lane.n_children), test_children)
                lane.x = x_orig.clone()
                for c in train_children:
                    sel = torch.as_tensor(np.flatnonzero(lane.child == c), device=device)
                    lane.x[sel] = _shift_time(x_orig[sel], full_shift[c])
                tr_c, va_c = gxd.split_inner(train_children, val_frac, seed)
                gxt.seed_all(seed * 10 + k + (0 if mode == "aligned" else 500))
                model = gxt.build_model(config, lane)
                gxt.fit(model, lane, gxd.idx_of_children(lane, tr_c), gxd.idx_of_children(lane, va_c), config, seed=seed * 10 + k + (0 if mode == "aligned" else 500))
                from sklearn.metrics import roc_auc_score
                for c in test_children:
                    cidx = np.flatnonzero(lane.child == c)
                    for est_half, eval_par in (("odd", 0), ("even", 1)):       # shift from one half, evaluate on the other half
                        p = pk[est_half].get(c, np.nan) if est_half in pk else np.nan
                        s = shift_samples(p) if mode == "aligned" else full_shift[c]
                        ev = cidx[order_in_record[cidx] % 2 == eval_par]
                        if (y[ev] == 1).sum() < 10:
                            continue
                        lane.x[torch.as_tensor(ev, device=device)] = _shift_time(x_orig[torch.as_tensor(ev, device=device)], s)
                        a_shift = float(roc_auc_score(y[ev], (lambda l: l[:, 1] - l[:, 0])(gxt.predict(model, lane, ev))))
                        lane.x[torch.as_tensor(ev, device=device)] = x_orig[torch.as_tensor(ev, device=device)]
                        a_plain = float(roc_auc_score(y[ev], (lambda l: l[:, 1] - l[:, 0])(gxt.predict(model, lane, ev))))
                        rows.append({"mode": mode, "seed": seed, "fold": k, "child": int(c), "eval_half": "even" if eval_par == 0 else "odd", "shift_samples": s, "auc_shifted": a_shift, "auc_unshifted_input": a_plain})
    lane.x = x_orig
    f = pd.DataFrame(rows); f.to_csv(run["public"] / "align.csv", index=False)
    summary = {"run": args.run, "median_peak_s": median_peak, "shift_abs_samples_median": float(f[f["mode"] == "aligned"].shift_samples.abs().median())}
    for mode, g in f.groupby("mode"):
        pc = g.groupby("child")[["auc_shifted", "auc_unshifted_input"]].mean()
        summary[mode] = {"children": int(len(pc)), "auc_test_shifted_by_own_half_peak": float(pc.auc_shifted.mean()), "auc_test_unshifted": float(pc.auc_unshifted_input.mean()),
                         "seed_range_shifted": [float(v) for v in g.groupby("seed").apply(lambda q: q.groupby("child").auc_shifted.mean().mean(), include_groups=False)]}
    write_json(run["public"] / "summary_r5_align.json", summary, private=False)
    done(run["private"], "r5_align", summary)
    return summary


# ----------------------------------------------------------------------------- r5-memory (GPU-light)

def cmd_r5_memory(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r5_memory", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    score, _ = shared_scores(config, args.lane, args.base_run, len(y), lane.n_classes)
    n_since, _ = since_last_deviant(lane)
    order_in_record = np.zeros(len(y), dtype=int)
    for r in np.unique(lane.record):
        idx = np.flatnonzero(lane.record == r); idx = idx[np.argsort(lane.onset_s[idx])]; order_in_record[idx] = np.arange(len(idx))
    src = {}
    for m in lane.record_meta:
        s = m["source_cohort_evidence"]; src[m["child"]] = "CI" if s in ("CI", "CIHA_label") or src.get(m["child"]) == "CI" else src.get(m["child"], s)
    ov = _override().set_index("record_id")
    rows = []
    for c in np.unique(lane.child):
        cm = (lane.child == c) & np.isfinite(score) & (y >= 1)
        sd = np.nanstd(score[(lane.child == c) & np.isfinite(score)]) + 1e-9
        def supp(mask, k):
            a = cm & mask & (n_since == k); b = cm & mask & (n_since >= 3)
            return float((score[a].mean() - score[b].mean()) / sd) if a.sum() >= 8 and b.sum() >= 20 else np.nan
        row = {"child": int(c), "source": src.get(int(c), ""), "n_dev_after_dev": int((cm & (n_since == 0)).sum()), "n_dev_after_1std": int((cm & (n_since == 1)).sum()), "n_dev_after_std3": int((cm & (n_since >= 3)).sum())}
        for k in (0, 1):
            for name, mask in (("all", np.ones(len(y), bool)), ("odd", order_in_record % 2 == 1), ("even", order_in_record % 2 == 0), ("first200", order_in_record < 200), ("first400", order_in_record < 400), ("first800", order_in_record < 800)):
                row[f"supp{k}_{name}"] = supp(mask, k)
        rows.append(row)
    f = pd.DataFrame(rows); f.to_csv(run["public"] / f"memory_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "n_dev_after_dev_median": float(f.n_dev_after_dev.median()), "n_dev_after_1std_median": float(f.n_dev_after_1std.median())}
    for k, label in ((0, "dev_after_dev_minus_after_3std"), (1, "dev_after_1std_minus_after_3std")):
        col = f"supp{k}_all"
        summary[label] = {"children": int(f[col].notna().sum()),
                          "by_source": {s: {"n": int(g[col].notna().sum()), "mean": float(g[col].mean()), "median": float(g[col].median()), "children_negative": int((g[col] < 0).sum())} for s, g in f.groupby("source")},
                          "reliability_odd_vs_even": _spearman(f[f"supp{k}_odd"], f[f"supp{k}_even"]), "odd_even_abs_diff_median": float((f[f"supp{k}_odd"] - f[f"supp{k}_even"]).abs().median()),
                          "first_n_abs_error_median": {n: float((f[f"supp{k}_first{n}"] - f[col]).abs().median()) for n in (200, 400, 800)}}
    write_json(run["public"] / f"summary_r5_memory_{args.lane}.json", summary, private=False)
    done(run["private"], "r5_memory", summary)
    return summary


# ----------------------------------------------------------------------------- r5-hf (CPU): trial-level independence of full-band vs 30-45 Hz scores

def cmd_r5_hf(args, config) -> dict:
    run = open_run("r5_hf", args.run, config, args=vars(args))
    meta = read_json(private_dir(config, args.base_run) / "record_meta.json")
    # rebuild trial -> child / y from the staged epochs of the unknown lane (all trials, as in the allqc runs)
    stage = private_dir(config, args.stage_run) / "epochs"
    child_of, y_all = [], []
    for m in meta:
        d = np.load(stage / f"{m['record_id']}.npz", allow_pickle=False)
        child_of.append(np.full(len(d["y"]), m["child"])); y_all.append(d["y"])
    child_of = np.concatenate(child_of); y_all = np.concatenate(y_all)
    s_full, _ = shared_scores(config, args.lane, args.base_run, len(y_all), 2)
    s_hf, _ = shared_scores(config, args.lane, args.hf_run, len(y_all), 2)
    src = {}
    for m in meta:
        s = m["source_cohort_evidence"]; src[m["child"]] = "CI" if s in ("CI", "CIHA_label") or src.get(m["child"]) == "CI" else "non-CI"
    rows = []
    for c in np.unique(child_of):
        for cls in (0, 1):
            sel = (child_of == c) & (y_all == cls) & np.isfinite(s_full) & np.isfinite(s_hf)
            if sel.sum() >= 30:
                r = _spearman(s_full[sel], s_hf[sel]); rows.append({"child": int(c), "source": src.get(int(c)), "class": cls, "n": int(sel.sum()), "rho": r["rho"]})
        sel = (child_of == c) & np.isfinite(s_full) & np.isfinite(s_hf)
        if sel.sum() >= 30:
            rows.append({"child": int(c), "source": src.get(int(c)), "class": -1, "n": int(sel.sum()), "rho": _spearman(s_full[sel], s_hf[sel])["rho"]})
    f = pd.DataFrame(rows); f.to_csv(run["public"] / "hf_trial_correlation.csv", index=False)
    summary = {"run": args.run, "rho_within_class_by_source": {f"{s}/class{k}": {"children": int(len(g)), "rho_mean": float(g.rho.mean()), "rho_median": float(g.rho.median())} for (s, k), g in f.groupby(["source", "class"])}}
    write_json(run["public"] / "summary_r5_hf.json", summary, private=False)
    done(run["private"], "r5_hf", summary)
    return summary


# ----------------------------------------------------------------------------- r5-joint (CPU)

def cmd_r5_joint(args, config) -> dict:
    run = open_run("r5_joint", args.run, config, args=vars(args))
    t = pd.read_csv(results_dir(config, args.wlate_run) / "child_table_r5.csv")
    mem = pd.read_csv(results_dir(config, args.memory_run) / "memory_bdf_puretone.csv")[["child", "supp1_all"]].rename(columns={"supp1_all": "suppression1"})
    t = t.merge(mem, on="child", how="left")
    cols = ["auc", "w_late", "suppression1", "calibration_slope", "asym_left_minus_right"]
    cols = [c for c in cols if c in t and t[c].notna().mean() >= 0.5]     # drop sparse quantities (e.g. suppression in the HA paradigm)
    X = t[cols].copy(); m = X.notna().all(1); X = X[m]; grp = np.where(t.source[m] == "NH", "NH", np.where(t.duration[m] <= 2, "new", np.where(t.duration[m] > 36, "long", "mid")))
    corr = X.corr(method="spearman").round(3)
    Z = (X - X.mean()) / X.std(); U, S, Vt = np.linalg.svd(Z.to_numpy(), full_matrices=False); pcs = U[:, :2] * S[:2]
    proj = pd.DataFrame({"child": t.child[m].to_numpy(), "group": grp, "pc1": pcs[:, 0], "pc2": pcs[:, 1]}); proj.to_csv(run["public"] / "joint_projection.csv", index=False)
    summary = {"run": args.run, "n": int(m.sum()), "variables": cols, "spearman_matrix": {a: {b: float(corr.loc[a, b]) for b in cols} for a in cols},
               "explained_variance_ratio_pc1_pc2": [float(v) for v in (S[:2] ** 2 / (S ** 2).sum())],
               "loadings_pc1": {c: float(v) for c, v in zip(cols, Vt[0])}, "loadings_pc2": {c: float(v) for c, v in zip(cols, Vt[1])},
               "group_centroids": {g: {"n": int((proj.group == g).sum()), "pc1": float(proj[proj.group == g].pc1.mean()), "pc2": float(proj[proj.group == g].pc2.mean())} for g in np.unique(grp)}}
    write_json(run["public"] / "summary_r5_joint.json", summary, private=False)
    done(run["private"], "r5_joint", summary)
    return summary
