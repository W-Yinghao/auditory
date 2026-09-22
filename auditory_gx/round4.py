"""Round-4: device experience, deviant direction, high-frequency topography, trait reliability, hidden literals."""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .round3 import MFF_FRONTAL_POLAR, MFF_PERIOCULAR, _channel_names, _child_auc, _fold_models
from .runtime import ROOT, cfg, done, open_run, private_dir, read_json, results_dir, write_json_overwrite as write_json

OVERRIDE = ROOT / "private/auditory_gx/clinical_override.csv"


def _override() -> pd.DataFrame:
    return pd.read_csv(OVERRIDE) if OVERRIDE.exists() else pd.DataFrame(columns=["record_id", "age_months", "device_duration_months"])


def _spearman(a, b):
    from scipy.stats import spearmanr
    a, b = np.asarray(a, float), np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 6:
        return {"n": int(m.sum()), "rho": None, "p": None}
    r, p = spearmanr(a[m], b[m]); return {"n": int(m.sum()), "rho": float(r), "p": float(p)}


def _partial_spearman(y, x, z):
    """Spearman of y and x after residualising both on z (linear)."""
    y, x, z = (np.asarray(v, float) for v in (y, x, z)); m = np.isfinite(y) & np.isfinite(x) & np.isfinite(z)
    if m.sum() < 8:
        return {"n": int(m.sum()), "rho": None, "p": None}
    Z = np.column_stack([np.ones(m.sum()), z[m]])
    ry = y[m] - Z @ np.linalg.lstsq(Z, y[m], rcond=None)[0]; rx = x[m] - Z @ np.linalg.lstsq(Z, x[m], rcond=None)[0]
    return _spearman(ry, rx)


def _child_table_ha(config) -> pd.DataFrame:
    """One row per HA-lane child: AUC, age, duration (NH -> 0), peak, memory slope, calibration."""
    rec = pd.read_csv(results_dir(config, "GX8_bdf_puretone") / "record_auc_bdf_puretone.csv")
    ov = _override().set_index("record_id")
    for i, r in rec.iterrows():
        if r.record in ov.index:
            rec.loc[i, "age"] = ov.loc[r.record, "age_months"]; rec.loc[i, "duration"] = ov.loc[r.record, "device_duration_months"]
    rec.loc[(rec.source == "NH") & rec.duration.isna(), "duration"] = 0.0
    child = rec.groupby("child").agg(auc=("auc", "mean"), n_rec=("record", "count"), age=("age", "mean"), duration=("duration", "mean"),
                                     source=("source", "first"), n=("n", "mean")).reset_index()
    peaks = pd.read_csv(results_dir(config, "R3_peaks_bdf_puretone") / "child_peaks_bdf_puretone.csv")
    pk = peaks.groupby("child").agg(peak=("peak_time_s", "mean"), peak_range=("peak_time_s", lambda v: v.max() - v.min()), peak_drop=("peak_drop", "mean")).reset_index()
    pk["late_cluster"] = (pk.peak >= 0.2).astype(float); pk.loc[pk.peak_range > 0.08, "late_cluster"] = np.nan
    mem = pd.read_csv(results_dir(config, "R3_memory_bdf_puretone") / "memory_bdf_puretone.csv")[["child", "slope_sd_per_step", "slope_shrunk"]]
    cal = pd.read_csv(results_dir(config, "R2_instrument_bdf_puretone") / "calibration_bdf_puretone.csv")[["child", "calibration_slope", "balanced_brier"]]
    return child.merge(pk, on="child", how="left").merge(mem, on="child", how="left").merge(cal, on="child", how="left")


QUANTITIES = ["auc", "peak", "late_cluster", "peak_drop", "slope_sd_per_step", "calibration_slope", "balanced_brier"]


def cmd_r4_experience(args, config) -> dict:
    run = open_run("r4_experience", args.run, config, args=vars(args))
    t = _child_table_ha(config)
    t.to_csv(run["public"] / "child_table_bdf_puretone.csv", index=False)
    ha = t[t.source == "HA"].copy(); nh = t[t.source == "NH"].copy()
    out = {"run": args.run, "children": int(len(t)), "ha": int(len(ha)), "nh": int(len(nh)),
           "ha_with_age_and_duration": int((ha.age.notna() & ha.duration.notna()).sum()), "nh_with_age": int(nh.age.notna().sum())}
    # 1. newly fitted vs age-matched experienced (greedy nearest-age, unique, |dAge| <= 12 months)
    new = ha[(ha.duration <= 2) & ha.age.notna()].sort_values("age"); exp_ = ha[(ha.duration >= 12) & ha.age.notna()].copy()
    pairs = []; used = set()
    for _, a in new.iterrows():
        cand = exp_[~exp_.child.isin(used)].copy(); cand["d"] = (cand.age - a.age).abs()
        cand = cand[cand.d <= 12]
        if len(cand):
            b = cand.sort_values("d").iloc[0]; used.add(b.child)
            pairs.append({"new_child": int(a.child), "exp_child": int(b.child), "age_new": a.age, "age_exp": b.age, "duration_exp": b.duration,
                          **{f"d_{q}": (a[q] - b[q]) for q in QUANTITIES}})
    pr = pd.DataFrame(pairs); pr.to_csv(run["public"] / "matched_pairs.csv", index=False)
    out["matched_new_vs_experienced"] = {"pairs": int(len(pr)), "new_candidates": int(len(new)), "experienced_pool": int(len(exp_)),
                                         "mean_diff_new_minus_exp": {q: float(pr[f"d_{q}"].mean()) for q in QUANTITIES} if len(pr) else {},
                                         "pairs_new_higher": {q: int((pr[f"d_{q}"] > 0).sum()) for q in QUANTITIES} if len(pr) else {},
                                         "duration_exp_median": float(pr.duration_exp.median()) if len(pr) else None}
    # 2. unified experience axis: NH -> age, HA -> duration
    t["E"] = np.where(t.source == "NH", t.age, t.duration)
    out["experience_axis"] = {"auc_vs_E_pooled": _spearman(t.auc, t.E), "auc_vs_E_ha": _spearman(ha.auc, ha.duration), "auc_vs_E_nh(age)": _spearman(nh.auc, nh.age),
                              "auc_vs_age_ha": _spearman(ha.auc, ha.age), "auc_vs_age_nh": _spearman(nh.auc, nh.age)}
    m = ha.auc.notna() & ha.duration.notna()
    if m.sum() >= 10 and nh.auc.notna().sum() >= 3:
        X = np.column_stack([np.ones(m.sum()), np.log1p(ha.duration[m])]); beta = np.linalg.lstsq(X, ha.auc[m], rcond=None)[0]
        pred_nh = beta[0] + beta[1] * np.log1p(nh.age.fillna(nh.age.median()))
        out["experience_axis"]["nh_residual_vs_ha_fit"] = {"beta_log1p_duration": float(beta[1]), "nh_mean_residual": float((nh.auc - pred_nh).mean()),
                                                           "nh_mean_auc": float(nh.auc.mean()), "ha_mean_auc": float(ha.auc.mean()),
                                                           "ha_top_duration_quartile_auc": float(ha[ha.duration >= ha.duration.quantile(.75)].auc.mean())}
    # 3. partial Spearman vs log1p(duration) | age, HA only
    out["partial_vs_log_duration_given_age"] = {q: _partial_spearman(ha[q], np.log1p(ha.duration), ha.age) for q in QUANTITIES}
    out["spearman_vs_age_ha"] = {q: _spearman(ha[q], ha.age) for q in QUANTITIES}
    # 4. two-visit children (record-level AUC change; order as in the record table)
    rec = pd.read_csv(results_dir(config, "GX8_bdf_puretone") / "record_auc_bdf_puretone.csv")
    multi = rec.groupby("child").filter(lambda g: len(g) >= 2)
    rows = [{"child": int(c), "auc_first": float(g.auc.iloc[0]), "auc_second": float(g.auc.iloc[1]), "delta": float(g.auc.iloc[1] - g.auc.iloc[0])} for c, g in multi.groupby("child")]
    lv = pd.DataFrame(rows); lv.to_csv(run["public"] / "two_visit.csv", index=False)
    out["two_visit"] = {"children": int(len(lv)), "delta_mean": float(lv.delta.mean()) if len(lv) else None, "delta_abs_median": float(lv.delta.abs().median()) if len(lv) else None,
                        "spearman_first_second": _spearman(lv.auc_first, lv.auc_second) if len(lv) else None}
    write_json(run["public"] / "summary_r4_experience.json", out, private=False)
    done(run["private"], "r4_experience", out)
    return out


def cmd_r4_pitch_attr(args, config) -> dict:
    run = open_run("r4_pitch_attr", args.run, config, args=vars(args))
    pa = pd.read_csv(results_dir(config, "R3_pitch") / "pitch_asymmetry.csv")
    meta = pd.DataFrame(read_json(private_dir(config, "GX1_mff_unknown_hdev_ldev_shared") / "record_meta.json"))
    ch = meta.groupby("child").agg(age=("age_months", "mean"), source=("source_cohort_evidence", lambda s: "/".join(sorted(set(s)))), n_rec=("record_id", "count")).reset_index()
    t = pa.merge(ch, on="child", how="left"); t["low_minus_high"] = t.auc_std_vs_low - t.auc_std_vs_high
    t.drop(columns=[]).to_csv(run["public"] / "pitch_attr.csv", index=False)
    out = {"run": args.run, "children": int(len(t)), "records": int(meta.shape[0]), "source_mix_children": {k: int(v) for k, v in t.source.value_counts().items()},
           "records_per_child": {int(k): int(v) for k, v in t.n_rec.value_counts().sort_index().items()}, "age_known": int(t.age.notna().sum()),
           "low_minus_high_mean": float(t.low_minus_high.mean()), "low_minus_high_vs_age": _spearman(t.low_minus_high, t.age),
           "low_minus_high_by_source": {k: {"n": int(len(g)), "mean": float(g.low_minus_high.mean())} for k, g in t.groupby("source")}}
    write_json(run["public"] / "summary_r4_pitch_attr.json", out, private=False)
    done(run["private"], "r4_pitch_attr", out)
    return out


def cmd_r4_ci_memory(args, config) -> dict:
    run = open_run("r4_ci_memory", args.run, config, args=vars(args))
    rep = pd.read_csv(results_dir(config, "R2_repetition_mff_unknown_event") / "repetition_mff_unknown_event.csv")
    meta = pd.DataFrame(read_json(private_dir(config, "GX1_mff_unknown_event_shared") / "record_meta.json"))
    ch = meta.groupby("child").agg(source=("source_cohort_evidence", lambda s: "CI" if s.isin(["CI", "CIHA_label"]).any() else s.iloc[0]),
                                   label=("source_cohort_evidence", lambda s: "/".join(sorted(set(s)))), age=("age_months", "mean")).reset_index()
    t = rep.merge(ch, on="child", how="left"); t.to_csv(run["public"] / "ci_memory.csv", index=False)
    out = {"run": args.run, "children": int(len(t)),
           "repetition_effect_by_label": {k: {"n": int(len(g)), "mean": float(g.repetition_effect.mean()), "median": float(g.repetition_effect.median()),
                                              "children_negative": int((g.repetition_effect < 0).sum())} for k, g in t.groupby("label")},
           "repetition_effect_ci_vs_rest": {k: {"n": int(len(g)), "mean": float(g.repetition_effect.mean()), "children_negative": int((g.repetition_effect < 0).sum())} for k, g in t.groupby("source")},
           "repetition_vs_age": _spearman(t.repetition_effect, t.age)}
    write_json(run["public"] / "summary_r4_ci_memory.json", out, private=False)
    done(run["private"], "r4_ci_memory", out)
    return out


def cmd_r4_trait(args, config) -> dict:
    run = open_run("r4_trait", args.run, config, args=vars(args))
    out = {"run": args.run}
    for lane in ("bdf_puretone", "mff_unknown_event", "mff_puretone"):
        rec = pd.read_csv(results_dir(config, f"GX8_{lane}") / f"record_auc_{lane}.csv")
        if "day" in rec and rec.day.notna().any():
            rec = rec.sort_values(["child", "day"])
        multi = rec.groupby("child").filter(lambda g: len(g) >= 2)
        rows = [{"child": int(c), "auc_1": float(g.auc.iloc[0]), "auc_2": float(g.auc.iloc[1]), "n_records": int(len(g)), "auc_all_sd": float(g.auc.std())} for c, g in multi.groupby("child")]
        f = pd.DataFrame(rows); f.to_csv(run["public"] / f"trait_{lane}.csv", index=False)
        between_sd = float(rec.groupby("child").auc.mean().std())
        out[lane] = {"children_with_2plus": int(len(f)), "spearman_visit1_visit2": _spearman(f.auc_1, f.auc_2) if len(f) else None,
                     "within_child_abs_diff_median": float((f.auc_1 - f.auc_2).abs().median()) if len(f) else None, "between_child_sd": between_sd,
                     "pearson_visit1_visit2": float(np.corrcoef(f.auc_1, f.auc_2)[0, 1]) if len(f) >= 3 else None}
    write_json(run["public"] / "summary_r4_trait.json", out, private=False)
    done(run["private"], "r4_trait", out)
    return out


def cmd_r4_inverted(args, config) -> dict:
    run = open_run("r4_inverted", args.run, config, args=vars(args))
    out = {"run": args.run}
    for lane in ("bdf_puretone", "mff_unknown_event", "mff_puretone"):
        s = pd.read_csv(results_dir(config, f"R3_records_{lane}") / f"record_seed_auc_{lane}.csv")
        seeds = [c for c in s.columns if c.startswith("auc_seed")]; s["auc_mean"] = s[seeds].mean(1)
        inv = s[s.all_seeds_below_half]
        rows = []
        for _, r in inv.iterrows():
            others = s[(s.child == r.child) & (s.record != r.record)]
            rows.append({"child": int(r.child), "auc_inverted": float(r.auc_mean), "n_other_records": int(len(others)),
                         "other_auc_mean": float(others.auc_mean.mean()) if len(others) else np.nan, "other_all_below_half": bool(len(others) and (others.auc_mean < 0.5).all())})
        f = pd.DataFrame(rows); f.to_csv(run["public"] / f"inverted_{lane}.csv", index=False)
        out[lane] = {"inverted_records": int(len(f)), "with_other_visit": int((f.n_other_records > 0).sum()) if len(f) else 0,
                     "other_visit_also_below_half": int(f.other_all_below_half.sum()) if len(f) else 0,
                     "other_visit_auc_mean": float(f.other_auc_mean.mean()) if len(f) and f.other_auc_mean.notna().any() else None}
    write_json(run["public"] / "summary_r4_inverted.json", out, private=False)
    done(run["private"], "r4_inverted", out)
    return out


def cmd_r4_literals(args, config) -> dict:
    """Which event literals exist beyond the frozen target codes, per branch (staged ST1 event tables)."""
    run = open_run("r4_literals", args.run, config, args=vars(args))
    ev_dir = ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "events"
    out = {"run": args.run}
    for branch, pattern in (("bdf", "B*.parquet"), ("mff", "M*.parquet")):
        files = sorted(glob.glob(str(ev_dir / pattern)))
        lit_records, per_record, cells = {}, [], {}
        for f in files:
            e = pd.read_parquet(f, columns=["event_literal", "onset_seconds", "event_kind"])
            vc = e.event_literal.astype(str).value_counts()
            for lit, n in vc.items():
                lit_records.setdefault(lit, []).append(int(n))
            extra = vc[~vc.index.isin(["1", "2", "stad", "devt", "hdev", "ldev"])]
            per_record.append({"n_extra_literals": int(len(extra)), "n_extra_events": int(extra.sum())})
            for lit in extra.index:
                digits = "".join(ch for ch in lit if ch.isdigit())
                if digits:
                    cells.setdefault(digits, 0); cells[digits] += 1
        out[branch] = {"records": int(len(files)),
                       "literals": {lit: {"records": len(v), "events_per_record_median": float(np.median(v))} for lit, v in sorted(lit_records.items(), key=lambda kv: -len(kv[1]))[:20]},
                       "records_with_extra_literals": int(sum(1 for p in per_record if p["n_extra_events"] > 0)),
                       "numeric_tokens_in_extra_literals": dict(sorted(cells.items(), key=lambda kv: -kv[1])[:20])}
    write_json(run["public"] / "summary_r4_literals.json", out, private=False)
    done(run["private"], "r4_literals", out)
    return out


# ----------------------------------------------------------------------------- GPU

def cmd_r4_direction(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r4_direction", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), "mff_unknown_hdev_ldev", device)
    y3 = lane.y.cpu().numpy().copy()
    seeds = [int(s) for s in cfg(config, "folds.seeds")]; n_folds = int(cfg(config, "folds.n_child_folds")); val_frac = float(cfg(config, "folds.inner_validation_fraction"))
    from sklearn.metrics import roc_auc_score
    rows = []
    for target, other in ((1, 2), (2, 1)):
        lane.y = torch.as_tensor((y3 == target).astype(np.int64), device=device); lane.n_classes = 2
        for seed in seeds:
            folds = gxd.child_folds(lane.n_children, n_folds, seed)
            for k, test_children in enumerate(folds):
                train_children = np.setdiff1d(np.arange(lane.n_children), test_children)
                tr_c, va_c = gxd.split_inner(train_children, val_frac, seed)
                tr = gxd.idx_of_children(lane, tr_c); va = gxd.idx_of_children(lane, va_c)
                tr = tr[y3[tr] != other]; va = va[y3[va] != other]
                gxt.seed_all(seed * 100 + target * 10 + k)
                model = gxt.build_model(config, lane)
                gxt.fit(model, lane, tr, va, config, seed=seed * 100 + target * 10 + k)
                te = gxd.idx_of_children(lane, test_children)
                logits = gxt.predict(model, lane, te); score = logits[:, 1] - logits[:, 0]
                for c in test_children:
                    sel = lane.child[te] == c; yy = y3[te][sel]; ss = score[sel]
                    if (yy == 0).sum() < 20 or (yy == target).sum() < 10 or (yy == other).sum() < 10:
                        continue
                    own = roc_auc_score((yy[yy != other] == target), ss[yy != other]); cross = roc_auc_score((yy[yy != target] == other), ss[yy != target])
                    rows.append({"trained_on": "high" if target == 1 else "low", "seed": seed, "fold": k, "child": int(c), "auc_own": float(own), "auc_cross": float(cross),
                                 "auc_high_vs_low_by_score": float(roc_auc_score((yy[yy > 0] == target), ss[yy > 0]))})
    f = pd.DataFrame(rows); f.to_csv(run["public"] / "direction_transfer.csv", index=False)
    summary = {"run": args.run, "children": int(f.child.nunique()) if len(f) else 0}
    for t_, g in f.groupby("trained_on"):
        pc = g.groupby("child")[["auc_own", "auc_cross", "auc_high_vs_low_by_score"]].mean()
        summary[f"trained_on_{t_}"] = {"auc_own_mean": float(pc.auc_own.mean()), "auc_cross_mean": float(pc.auc_cross.mean()),
                                       "children_cross_gt_half": int((pc.auc_cross > 0.5).sum()), "children": int(len(pc)),
                                       "seed_range_cross": [float(v) for v in g.groupby("seed").apply(lambda q: q.groupby("child").auc_cross.mean().mean(), include_groups=False)],
                                       "auc_deviant_vs_other_deviant_mean": float(pc.auc_high_vs_low_by_score.mean())}
    write_json(run["public"] / "summary_r4_direction.json", summary, private=False)
    done(run["private"], "r4_direction", summary)
    return summary


def cmd_r4_hf_topo(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r4_hf_topo", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device, accepted_only=not args.include_rejected)
    names = _channel_names(config, lane); y = lane.y.cpu().numpy()
    groups = {"periocular_eog": [i for i, n in enumerate(names) if n in MFF_PERIOCULAR], "frontal_polar": [i for i, n in enumerate(names) if n in MFF_FRONTAL_POLAR],
              "left_temporal": [i for i, n in enumerate(names) if n in {"E39", "E40", "E44", "E45", "E46", "E50", "E57", "E58"}],
              "right_temporal": [i for i, n in enumerate(names) if n in {"E96", "E101", "E102", "E108", "E109", "E114", "E115", "E100"}],
              "vertex_ring": [i for i, n in enumerate(names) if n in {"E6", "E7", "E31", "E55", "E80", "E106"}],
              "frontocentral": [i for i, n in enumerate(names) if n in {"E4", "E5", "E10", "E11", "E12", "E16", "E18", "E19", "E20", "E23", "E24"}],
              "occipital": [i for i, n in enumerate(names) if n in {"E70", "E71", "E74", "E75", "E76", "E82", "E83", "E69", "E89"}]}
    half = len(names) // 2
    groups["left_half"] = [i for i, n in enumerate(names) if n in {f"E{k}" for k in (22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59, 60, 61, 63, 64, 65, 66, 67, 68, 69, 70, 71, 73, 74)}]
    groups["right_half"] = [i for i, n in enumerate(names) if n in {f"E{k}" for k in (1, 2, 3, 8, 9, 14, 76, 77, 78, 79, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 120, 121, 122, 123, 124)}]
    src = {m["child"]: m["source_cohort_evidence"] for m in lane.record_meta}
    for m in lane.record_meta:
        if m["source_cohort_evidence"] in ("CI", "CIHA_label"):
            src[m["child"]] = "CI"
    rows = []; x_backup = lane.x
    for seed, k, test_children, model in _fold_models(config, args.base_run, lane, device, torch):
        idx = gxd.idx_of_children(lane, test_children); base = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
        for name, chans in groups.items():
            if not chans:
                continue
            lane.x = x_backup.clone(); lane.x[:, chans, :] = 0
            occ = _child_auc(lane, idx, gxt.predict(model, lane, idx), y)
            for c in base:
                rows.append({"seed": seed, "child": c, "group": name, "n_channels": len(chans), "source": "CI" if src.get(c) == "CI" else "non-CI", "auc_base": base[c], "auc_drop": base[c] - occ[c]})
        lane.x = x_backup
    f = pd.DataFrame(rows); f.to_csv(run["public"] / f"hf_topo_{args.lane}.csv", index=False)
    pc = f.groupby(["source", "group", "child"]).auc_drop.mean().reset_index()
    summary = {"run": args.run, "lane": args.lane, "stage_run": args.stage_run, "base_run": args.base_run,
               "children_by_source": {k: int(v) for k, v in pc.groupby("source").child.nunique().items()},
               "base_auc_by_source": {k: float(v) for k, v in f.groupby("source").auc_base.mean().items()},
               "drop_by_source_and_group": {s: {g: float(d.auc_drop.mean()) for g, d in q.groupby("group")} for s, q in pc.groupby("source")}}
    for s, q in pc.groupby("source"):
        piv = q.pivot(index="child", columns="group", values="auc_drop")
        if "left_temporal" in piv and "right_temporal" in piv:
            summary.setdefault("temporal_asymmetry_right_minus_left", {})[s] = {"mean": float((piv.right_temporal - piv.left_temporal).mean()), "children_right_larger": int((piv.right_temporal > piv.left_temporal).sum()), "n": int(len(piv))}
    write_json(run["public"] / f"summary_r4_hf_topo_{args.lane}.json", summary, private=False)
    done(run["private"], "r4_hf_topo", summary)
    return summary
