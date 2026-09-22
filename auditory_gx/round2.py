"""Round-2 analyses that treat the trained cross-child readout as a single-trial instrument.

All commands reuse the saved shared-model predictions (private/auditory_gx/GX1_<lane>_shared/predictions_shared.npz)
and the staged epochs; a few need one forward pass through the saved fold models (GPU).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as gxd
from . import train as gxt
from .runtime import ROOT, cfg, done, open_run, private_dir, read_json, results_dir, write_json_overwrite as write_json


# ----------------------------------------------------------------------------- helpers

def shared_scores(config: dict, lane_name: str, run: str, n_trials: int, n_classes: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-trial score (logit1 - logit0, or class logits for K>2) averaged over the seeds that held the trial out."""
    acc = np.zeros((n_trials, n_classes), dtype=np.float64)
    cnt = np.zeros(n_trials, dtype=np.int64)
    with np.load(private_dir(config, run) / "predictions_shared.npz", allow_pickle=False) as store:
        for key in store.files:
            arr = store[key]
            idx = arr[:, 0].astype(int)
            acc[idx] += arr[:, 1:]
            cnt[idx] += 1
    ok = cnt > 0
    logits = np.full((n_trials, n_classes), np.nan)
    logits[ok] = acc[ok] / cnt[ok, None]
    score = logits[:, 1] - logits[:, 0] if n_classes == 2 else logits[:, 1:].max(1) - logits[:, 0]
    return score, logits


def since_last_deviant(lane: gxd.Lane) -> tuple[np.ndarray, np.ndarray]:
    """For every trial: number of sounds since the last deviant and elapsed seconds (nan if none before in the record)."""
    n_since = np.full(len(lane.y), -1, dtype=np.int64)
    t_since = np.full(len(lane.y), np.nan)
    y = lane.y.cpu().numpy()
    for r in np.unique(lane.record):
        idx = np.flatnonzero(lane.record == r)
        idx = idx[np.argsort(lane.onset_s[idx])]
        last_t, count = np.nan, -1
        for i in idx:
            if count >= 0:
                n_since[i] = count
                t_since[i] = lane.onset_s[i] - last_t
            if y[i] >= 1:
                last_t, count = lane.onset_s[i], 0
            elif count >= 0:
                count += 1
    return n_since, t_since


def _lane_and_scores(config, args, device):
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    score, logits = shared_scores(config, args.lane, args.base_run, len(lane.y), lane.n_classes)
    return lane, score, logits


def _zscore_within_child(score: np.ndarray, child: np.ndarray, mask: np.ndarray) -> np.ndarray:
    z = np.full(len(score), np.nan)
    for c in np.unique(child):
        sel = (child == c) & mask & np.isfinite(score)
        if sel.sum() > 20:
            z[sel] = (score[sel] - score[sel].mean()) / (score[sel].std() + 1e-9)
    return z


# ----------------------------------------------------------------------------- r2-expectation

def cmd_r2_expectation(args, config) -> dict:
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run = open_run("r2_expectation", args.run, config, args=vars(args))
    lane, score, _ = _lane_and_scores(config, args, device)
    y = lane.y.cpu().numpy()
    n_since, t_since = since_last_deviant(lane)
    std = (y == 0) & (n_since >= 0) & np.isfinite(score)
    dev = (y >= 1) & (n_since >= 0) & np.isfinite(score)
    z = _zscore_within_child(score, lane.child, y == 0)      # standards standardised within child
    bins = np.clip(n_since, 0, 4)
    rows = []
    for c in np.unique(lane.child):
        for kind, m in (("standard", std), ("deviant", dev)):
            sel = m & (lane.child == c)
            if sel.sum() < 50:
                continue
            per_bin = {int(b): float(np.mean(score[sel & (bins == b)])) for b in range(5) if np.sum(sel & (bins == b)) >= 10}
            x = bins[sel].astype(float)
            s = score[sel]
            slope = float(np.polyfit(x, s, 1)[0]) if len(np.unique(x)) > 1 else np.nan
            tt = t_since[sel]
            ok = np.isfinite(tt)
            slope_time = float(np.polyfit(tt[ok], s[ok], 1)[0]) if ok.sum() > 20 and np.std(tt[ok]) > 0 else np.nan
            # joint model: score ~ position + elapsed time (collinear at fixed SOA; reported with its condition number)
            joint = np.nan
            if ok.sum() > 50:
                X = np.column_stack([np.ones(ok.sum()), x[ok], tt[ok]])
                beta, *_ = np.linalg.lstsq(X, s[ok], rcond=None)
                joint = float(beta[1])
            rows.append({"child": int(c), "kind": kind, "n": int(sel.sum()), "slope_per_position": slope,
                         "slope_per_second": slope_time, "position_coef_given_time": joint,
                         "age_months": float(lane.age_child[c]), **{f"bin{b}": v for b, v in per_bin.items()}})
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"expectation_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "children": int(f.child.nunique()) if len(f) else 0}
    for kind, sub in f.groupby("kind"):
        binmeans = {b: float(sub[f"bin{b}"].mean()) for b in range(5) if f"bin{b}" in sub and sub[f"bin{b}"].notna().sum() >= 5}
        summary[kind] = {"children": int(len(sub)), "score_by_sounds_since_deviant": binmeans,
                         "slope_per_position_mean": float(sub.slope_per_position.mean()),
                         "slope_per_position_children_positive": int((sub.slope_per_position > 0).sum()),
                         "slope_per_position_sd": float(sub.slope_per_position.std()),
                         "position_coef_given_time_mean": float(sub.position_coef_given_time.mean())}
        m = np.isfinite(sub.age_months) & np.isfinite(sub.slope_per_position)
        if m.sum() >= 10:
            from scipy.stats import spearmanr
            r, p = spearmanr(sub.slope_per_position[m], sub.age_months[m])
            summary[kind]["slope_vs_age_spearman"] = {"n": int(m.sum()), "rho": float(r), "p": float(p)}
    # group split by source label (per-record meta -> child majority)
    src = {}
    for m in lane.record_meta:
        src.setdefault(m["child"], m["source_cohort_evidence"])
    f["source"] = f.child.map(src)
    summary["standard_slope_by_source"] = {s: {"children": int(len(d)), "slope_mean": float(d.slope_per_position.mean())}
                                            for s, d in f[f.kind == "standard"].groupby("source")}
    write_json(run["public"] / f"summary_r2_expectation_{args.lane}.json", summary, private=False)
    done(run["private"], "r2_expectation", summary)
    return summary


# ----------------------------------------------------------------------------- r2-repetition

def cmd_r2_repetition(args, config) -> dict:
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run = open_run("r2_repetition", args.run, config, args=vars(args))
    lane, score, _ = _lane_and_scores(config, args, device)
    y = lane.y.cpu().numpy()
    prev = lane.hist[:, 1] == 1          # prev_code_1 column of history_design
    prev_std = lane.hist[:, 0] == 1
    run3 = (lane.hist[:, 6] == 1) | (lane.hist[:, 7] == 1) | (lane.hist[:, 8] == 1)   # prev_run 3,4,5+
    pre_score = None
    pre_run = args.preonly_run
    if pre_run:
        pre_score, _ = shared_scores(config, args.lane, pre_run, len(y), lane.n_classes)
    rows = []
    for c in np.unique(lane.child):
        mine = lane.child == c
        d_after_d = mine & (y >= 1) & prev & np.isfinite(score)
        d_after_s = mine & (y >= 1) & prev_std & run3 & np.isfinite(score)
        s_after_d = mine & (y == 0) & prev & np.isfinite(score)
        s_after_s = mine & (y == 0) & prev_std & run3 & np.isfinite(score)
        if d_after_d.sum() < 10 or d_after_s.sum() < 20:
            continue
        sd = score[mine & np.isfinite(score)].std() + 1e-9
        row = {"child": int(c), "n_dev_after_dev": int(d_after_d.sum()), "n_dev_after_std3": int(d_after_s.sum()),
               "dev_after_dev": float(score[d_after_d].mean() / sd), "dev_after_std3": float(score[d_after_s].mean() / sd),
               "std_after_dev": float(score[s_after_d].mean() / sd), "std_after_std3": float(score[s_after_s].mean() / sd)}
        row["repetition_effect"] = row["dev_after_dev"] - row["dev_after_std3"]
        row["carryover_on_standards"] = row["std_after_dev"] - row["std_after_std3"]
        if pre_score is not None:
            psd = pre_score[mine & np.isfinite(pre_score)].std() + 1e-9
            row["pre_only_dev_after_dev"] = float(pre_score[d_after_d].mean() / psd)
            row["pre_only_dev_after_std3"] = float(pre_score[d_after_s].mean() / psd)
            row["pre_only_repetition_effect"] = row["pre_only_dev_after_dev"] - row["pre_only_dev_after_std3"]
        rows.append(row)
    f = pd.DataFrame(rows)
    f.to_csv(run["public"] / f"repetition_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane, "children": int(len(f)),
               "repetition_effect_mean_sd_units": float(f.repetition_effect.mean()) if len(f) else None,
               "repetition_effect_children_negative": int((f.repetition_effect < 0).sum()) if len(f) else 0,
               "carryover_on_standards_mean": float(f.carryover_on_standards.mean()) if len(f) else None,
               "dev_after_dev_mean": float(f.dev_after_dev.mean()) if len(f) else None,
               "dev_after_std3_mean": float(f.dev_after_std3.mean()) if len(f) else None}
    if pre_score is not None and len(f):
        summary["pre_only_repetition_effect_mean"] = float(f.pre_only_repetition_effect.mean())
    write_json(run["public"] / f"summary_r2_repetition_{args.lane}.json", summary, private=False)
    done(run["private"], "r2_repetition", summary)
    return summary


# ----------------------------------------------------------------------------- r2-embed-age

def cmd_r2_embed_age(args, config) -> dict:
    import torch
    device = torch.device("cuda")
    run = open_run("r2_embed_age", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    base = private_dir(config, args.base_run)
    folds = read_json(base / "folds.json")
    emb_sum = None
    emb_cnt = np.zeros(len(lane.y))
    for seed_str, fold_list in folds.items():
        if seed_str == "model":
            continue
        for k, test_children in enumerate(fold_list):
            model = gxt.build_model(config, lane)
            model.load_state_dict(torch.load(base / "models" / f"shared_s{seed_str}_f{k}.pt", map_location=device))
            model.to(device).eval()
            idx = gxd.idx_of_children(lane, np.asarray(test_children))
            out = []
            with torch.no_grad():
                for b in range(0, len(idx), 1024):
                    xb = lane.x[torch.as_tensor(idx[b:b + 1024], device=device)].float()
                    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                        out.append(model.embed(xb).float().cpu().numpy())
            z = np.concatenate(out)
            if emb_sum is None:
                emb_sum = np.zeros((len(lane.y), z.shape[1]))
            emb_sum[idx] += z
            emb_cnt[idx] += 1
    ok = emb_cnt > 0
    emb = emb_sum[ok] / emb_cnt[ok, None]
    child = lane.child[ok]
    y = lane.y.cpu().numpy()[ok]
    children = np.unique(child)
    feats = np.stack([np.concatenate([emb[child == c].mean(0), emb[(child == c) & (y == 0)].mean(0) - emb[(child == c) & (y >= 1)].mean(0)])
                      for c in children])
    ages = lane.age_child[children]
    m = np.isfinite(ages)
    from .ssl import ridge_probe
    res = {"run": args.run, "lane": args.lane, "children_with_age": int(m.sum()), "embedding_dim": int(feats.shape[1])}
    if m.sum() >= 15:
        res["ridge_child_heldout"] = ridge_probe(feats[m], ages[m], np.array(lane.child_ids)[children[m]],
                                                 n_folds=int(cfg(config, "folds.n_child_folds")), seeds=[int(s) for s in cfg(config, "folds.seeds")])
        res["ridge_mean_embedding_only"] = ridge_probe(feats[m][:, :emb.shape[1]], ages[m], np.array(lane.child_ids)[children[m]],
                                                       n_folds=int(cfg(config, "folds.n_child_folds")), seeds=[int(s) for s in cfg(config, "folds.seeds")])
    np.savez_compressed(run["private"] / f"child_embeddings_{args.lane}.npz", feats=feats, children=children, ages=ages)
    write_json(run["public"] / f"summary_r2_embed_age_{args.lane}.json", res, private=False)
    done(run["private"], "r2_embed_age", res)
    return res


# ----------------------------------------------------------------------------- r2-fingerprint

def _train_children_by_model(config, base_run: str) -> tuple[list, dict]:
    """identity groups (names) used for training in each fold model of a shared run."""
    base = private_dir(config, base_run)
    meta = json.loads((base / "record_meta.json").read_text())
    idx_to_gid = {}
    for m in meta:
        idx_to_gid[m["child"]] = m["identity_group"]
    folds = read_json(base / "folds.json")
    models = []
    all_children = set(idx_to_gid.values())
    for seed_str, fold_list in folds.items():
        if seed_str == "model":
            continue
        for k, test_children in enumerate(fold_list):
            test_g = {idx_to_gid[c] for c in test_children}
            models.append({"path": base / "models" / f"shared_s{seed_str}_f{k}.pt", "train_groups": all_children - test_g})
    return models, idx_to_gid


def cmd_r2_fingerprint(args, config) -> dict:
    import torch
    from sklearn.metrics import roc_auc_score
    device = torch.device("cuda")
    run = open_run("r2_fingerprint", args.run, config, args=vars(args))
    lane = gxd.load_lane(config, private_dir(config, args.stage_run), args.lane, device)
    y = lane.y.cpu().numpy()
    groups = np.array(lane.child_ids)[lane.child]
    out_scores = {}
    for name, base_run in (("bapa", args.bapa_run), ("puretone", args.puretone_run)):
        models, _ = _train_children_by_model(config, base_run)
        acc = np.zeros(len(y)); cnt = np.zeros(len(y))
        for m in models:
            model = gxt.build_model(config, lane)
            model.load_state_dict(torch.load(m["path"], map_location=device))
            model.to(device).eval()
            admissible = ~np.isin(groups, list(m["train_groups"]))
            idx = np.flatnonzero(admissible)
            if len(idx) == 0:
                continue
            logits = gxt.predict(model, lane, idx)
            acc[idx] += logits[:, 1] - logits[:, 0]
            cnt[idx] += 1
        out_scores[name] = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    stage_sum = {}
    for p in (private_dir(config, args.stage_run) / "summaries").glob("*.json"):
        d = read_json(p)
        if d.get("status") == "OK":
            stage_sum[d["record_id"]] = d
    rows = []
    for r, meta in enumerate(lane.record_meta):
        sel = np.flatnonzero(lane.record == r)
        yy = y[sel]
        if len(np.unique(yy)) < 2:
            continue
        row = {"record": meta["record_id"], "child": meta["identity_group"][:6], "source": meta["source_cohort_evidence"],
               "condition": meta["condition_clue"], "n": int(len(sel)), "age_months": meta["age_months"],
               "record_scale": meta["record_scale"], "soa_family": "", "qc_reject_fraction": np.nan}
        ss = stage_sum.get(meta["record_id"])
        if ss:
            row["qc_reject_fraction"] = 1.0 - ss["n_accepted"] / max(1, ss["n_epochs"])
        for name, sc in out_scores.items():
            ok = np.isfinite(sc[sel])
            row[f"auc_{name}_model"] = float(roc_auc_score(yy[ok], sc[sel][ok])) if ok.sum() > 20 and len(np.unique(yy[ok])) == 2 else np.nan
            row[f"n_models_{name}"] = int(ok.sum() > 0)
        rows.append(row)
    f = pd.DataFrame(rows)
    # SOA family from onset gaps
    for r, meta in enumerate(lane.record_meta):
        sel = np.flatnonzero(lane.record == r)
        gaps = np.diff(np.sort(lane.onset_s[sel]))
        med = float(np.median(gaps[gaps < 3])) if (gaps < 3).any() else np.nan
        f.loc[f.record == meta["record_id"], "soa_family"] = "~0.87" if med < 0.95 else ("~1.07" if med < 1.2 else f"{med:.2f}")
    f["bapa_minus_puretone"] = f.auc_bapa_model - f.auc_puretone_model
    f.to_csv(run["public"] / f"fingerprint_{args.lane}.csv", index=False)
    from scipy.stats import spearmanr
    summary = {"run": args.run, "lane": args.lane, "records": int(len(f)),
               "auc_bapa_model_mean": float(f.auc_bapa_model.mean()), "auc_puretone_model_mean": float(f.auc_puretone_model.mean()),
               "bapa_minus_puretone_mean": float(f.bapa_minus_puretone.mean()),
               "records_bapa_better": int((f.bapa_minus_puretone > 0).sum()),
               "by_soa_family": {k: {"records": int(len(d)), "bapa": float(d.auc_bapa_model.mean()), "puretone": float(d.auc_puretone_model.mean())}
                                 for k, d in f.groupby("soa_family")},
               "by_source": {k: {"records": int(len(d)), "children": int(d.child.nunique()), "bapa": float(d.auc_bapa_model.mean()),
                                 "puretone": float(d.auc_puretone_model.mean())} for k, d in f.groupby("source")}}
    for var in ("qc_reject_fraction", "record_scale", "n"):
        m = np.isfinite(f[var].astype(float)) & np.isfinite(f.auc_bapa_model)
        if m.sum() >= 10:
            r_, p_ = spearmanr(f.auc_bapa_model[m], f[var][m].astype(float))
            summary[f"spearman_auc_bapa_vs_{var}"] = {"n": int(m.sum()), "rho": float(r_), "p": float(p_)}
    write_json(run["public"] / f"summary_r2_fingerprint_{args.lane}.json", summary, private=False)
    done(run["private"], "r2_fingerprint", summary)
    return summary


# ----------------------------------------------------------------------------- r2-calibration / drift / usability (one command)

def cmd_r2_instrument(args, config) -> dict:
    """Calibration (balanced Brier, slope), within-record drift of standard scores, and signal-usability ranking."""
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run = open_run("r2_instrument", args.run, config, args=vars(args))
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    lane, score, logits = _lane_and_scores(config, args, device)
    y = lane.y.cpu().numpy()
    binary = lane.n_classes == 2
    seg_s = float(cfg(config, "blocks.segment_seconds"))
    cal_rows, drift_rows, rec_rows = [], [], []
    for c in np.unique(lane.child):
        sel = np.flatnonzero((lane.child == c) & np.isfinite(score))
        yy = y[sel]
        if binary and len(np.unique(yy)) == 2 and len(sel) > 50:
            p = 1 / (1 + np.exp(-score[sel]))
            w = np.where(yy == 1, 0.5 / max(1, (yy == 1).sum()), 0.5 / max(1, (yy == 0).sum()))
            brier = float(np.sum(w * (p - yy) ** 2) / w.sum())
            lr = LogisticRegression(C=1e6, max_iter=1000).fit(score[sel].reshape(-1, 1), yy)
            cal_rows.append({"child": int(c), "n": int(len(sel)), "balanced_brier": brier, "calibration_slope": float(lr.coef_[0, 0]),
                             "calibration_intercept": float(lr.intercept_[0]), "auc": float(roc_auc_score(yy, score[sel])),
                             "age_months": float(lane.age_child[c])})
        # drift of standard-trial scores by 2-minute segment (z within child)
        std = sel[yy == 0]
        if len(std) > 100:
            z = (score[std] - score[std].mean()) / (score[std].std() + 1e-9)
            for r in np.unique(lane.record[std]):
                m = lane.record[std] == r
                seg = np.floor((lane.onset_s[std][m] - lane.onset_s[std][m].min()) / seg_s).astype(int)
                for s_ in np.unique(seg):
                    q = seg == s_
                    if q.sum() >= 20:
                        drift_rows.append({"child": int(c), "record": lane.record_ids[r], "segment": int(s_), "n": int(q.sum()),
                                           "std_score_mean_z": float(z[m][q].mean()), "std_score_sd_z": float(z[m][q].std())})
    for r, meta in enumerate(lane.record_meta):
        sel = np.flatnonzero((lane.record == r) & np.isfinite(score))
        yy = y[sel]
        if len(np.unique(yy)) < 2:
            continue
        m_all = gxt.child_metrics(logits[sel], yy, lane.n_classes)
        row = {"record": meta["record_id"], "child": meta["child"], "auc": m_all["auc"], "n": int(len(sel))}
        for blk in (0, 1):
            q = lane.parity[sel] == blk
            if q.sum() > 30 and len(np.unique(yy[q])) == 2:
                row[f"auc_block{blk}"] = gxt.child_metrics(logits[sel][q], yy[q], lane.n_classes)["auc"]
        rec_rows.append(row)
    cal, drift, rec = pd.DataFrame(cal_rows), pd.DataFrame(drift_rows), pd.DataFrame(rec_rows)
    cal.to_csv(run["public"] / f"calibration_{args.lane}.csv", index=False)
    drift.to_csv(run["public"] / f"drift_{args.lane}.csv", index=False)
    rec.to_csv(run["public"] / f"record_auc_blocks_{args.lane}.csv", index=False)
    summary = {"run": args.run, "lane": args.lane}
    if len(cal):
        from scipy.stats import spearmanr
        summary["calibration"] = {"children": int(len(cal)), "balanced_brier_mean": float(cal.balanced_brier.mean()),
                                  "calibration_slope_median": float(cal.calibration_slope.median()),
                                  "slope_iqr": [float(cal.calibration_slope.quantile(.25)), float(cal.calibration_slope.quantile(.75))]}
        m = np.isfinite(cal.age_months)
        if m.sum() >= 10:
            r_, p_ = spearmanr(cal.calibration_slope[m], cal.age_months[m])
            summary["calibration"]["slope_vs_age"] = {"n": int(m.sum()), "rho": float(r_), "p": float(p_)}
    if len(drift):
        per_child_slope = drift.groupby("child").apply(lambda d: np.polyfit(d.segment, d.std_score_mean_z, 1)[0] if d.segment.nunique() > 2 else np.nan, include_groups=False)
        per_child_sd_slope = drift.groupby("child").apply(lambda d: np.polyfit(d.segment, d.std_score_sd_z, 1)[0] if d.segment.nunique() > 2 else np.nan, include_groups=False)
        summary["drift"] = {"children": int(per_child_slope.notna().sum()),
                            "std_score_mean_slope_per_segment_mean": float(np.nanmean(per_child_slope)),
                            "children_positive_slope": int((per_child_slope > 0).sum()),
                            "std_score_sd_slope_per_segment_mean": float(np.nanmean(per_child_sd_slope)),
                            "segment_means": {int(s): float(d.std_score_mean_z.mean()) for s, d in drift.groupby("segment") if len(d) >= 10}}
    if len(rec):
        per_child = rec.groupby("child").auc.mean()
        multi = rec.groupby("child").filter(lambda d: len(d) >= 2)
        within_rec = float((rec.auc_block0 - rec.auc_block1).abs().mean()) if "auc_block0" in rec else None
        across = float(multi.groupby("child").auc.agg(lambda v: np.abs(np.diff(v)).mean() if len(v) > 1 else np.nan).mean()) if len(multi) else None
        summary["usability"] = {"records": int(len(rec)), "children": int(len(per_child)),
                                "between_child_sd_of_record_auc": float(per_child.std()),
                                "within_record_block_abs_diff_mean": within_rec,
                                "within_child_across_record_abs_diff_mean": across,
                                "children_with_multiple_records": int(multi.child.nunique()) if len(multi) else 0,
                                "usability_ratio_between_sd_over_block_diff": (float(per_child.std() / within_rec) if within_rec else None)}
    write_json(run["public"] / f"summary_r2_instrument_{args.lane}.json", summary, private=False)
    done(run["private"], "r2_instrument", summary)
    return summary


# ----------------------------------------------------------------------------- r2-nh

def cmd_r2_nh(args, config) -> dict:
    """NH-vs-HA replication: normal-literal MFF records versus the rest of the same lane under the shared model."""
    run = open_run("r2_nh", args.run, config, args=vars(args))
    import csv
    labels = {r["container_id"]: r["source_label_expanded"] for r in csv.DictReader(open(ROOT / "results/phase3_metadata_addendum_001/source_metadata.csv"))}
    rows = []
    for lane in ("mff_unknown_event", "mff_puretone", "mff_bapa"):
        path = results_dir(config, f"GX8_{lane}") / f"record_auc_{lane}.csv"
        if not path.is_file():
            continue
        f = pd.read_csv(path)
        f["label_expanded"] = f.record.map(labels)
        f["lane"] = lane
        rows.append(f)
    if not rows:
        raise RuntimeError("NO_GX8_TABLES")
    allf = pd.concat(rows, ignore_index=True)
    normal = allf[allf.label_expanded == "normal_literal"]
    others = allf[allf.label_expanded != "normal_literal"]
    summary = {"run": args.run, "normal_literal_records": int(len(normal)), "normal_children": int(normal.child.nunique()) if len(normal) else 0,
               "normal_auc_mean": float(normal.auc.mean()) if len(normal) else None,
               "other_auc_mean_same_lanes": float(others[others.lane.isin(normal.lane.unique())].auc.mean()) if len(normal) else None,
               "normal_records": normal[["lane", "record", "auc", "n", "age"]].to_dict("records") if len(normal) else [],
               "by_label": {k: {"records": int(len(d)), "auc_mean": float(d.auc.mean())} for k, d in allf.groupby("label_expanded")}}
    # age-matched comparison where ages exist
    if len(normal) and normal.age.notna().any():
        matched = []
        for r in normal.itertuples():
            if np.isfinite(r.age):
                pool = others[(others.lane == r.lane) & np.isfinite(others.age) & ((others.age - r.age).abs() <= 12)]
                if len(pool):
                    matched.append({"record": r.record, "auc": r.auc, "matched_n": int(len(pool)), "matched_auc_mean": float(pool.auc.mean())})
        summary["age_matched"] = matched
    write_json(run["public"] / "summary_r2_nh.json", summary, private=False)
    done(run["private"], "r2_nh", summary)
    return summary
