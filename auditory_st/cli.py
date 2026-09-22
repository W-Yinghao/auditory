"""auditory_st runner. Slurm only. Per-record artefacts stay under private/.

Commands (in order):
  sources  --run R                 record table (metadata only)
  events   --run R                 [array] per-record event tables on the D1 axis
  scope    --run R                 public scope / task-event / support tables
  features --run F --scope-run R   [array] per-record window features (lanes with frozen post_seconds)
  support  --run F                 outcome-blind record support for every lane
  probe    --run P --scope-run R --record ID   one-record determinism and sanity gate
  readout  --run L --features-run F --lane NAME   child-held-out time-resolved readout
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from . import events as ev
from . import features as ft
from . import readout as rd
from . import report as rp
from . import scope as sc
from . import sources as src
from .runtime import (ROOT, ProvenanceError, array_slice, cfg, create_run, digest, finish,
                      load_config, private_dir, read_json, results_dir, write_json)


def _lane_codes(config: dict, lane: str) -> dict:
    return {str(k): int(v) for k, v in cfg(config, f"lanes.{lane}.codes").items()}


# ----------------------------------------------------------------------------- sources

def cmd_sources(args, config) -> dict:
    run = create_run("sources", args.run, config, args=vars(args))
    records = src.build(config)
    counts = src.write_records(records, run["private"], run["public"])
    write_json(run["public"] / "sources_summary.json", {"run": args.run, "counts": counts,
               "records_total": len(records)}, private=False)
    finish(run["private"], "sources", {"records": len(records)})
    return {"records": len(records), "counts": counts}


# ----------------------------------------------------------------------------- events

def cmd_events(args, config) -> dict:
    run = create_run("events", args.run, config, args=vars(args), allow_existing=True)
    records = pd.read_parquet(run["private"] / "records.parquet").to_dict("records")
    out_dir = run["private"] / "events"
    sum_dir = run["private"] / "event_summaries"
    for d in (out_dir, sum_dir):
        d.mkdir(mode=0o700, exist_ok=True)
    mine = array_slice(sorted(records, key=lambda r: r["record_id"]))
    done = failed = skipped = 0
    for rec in mine:
        rid = rec["record_id"]
        target = sum_dir / f"{rid}.json"
        if target.exists():
            skipped += 1
            continue
        lane = rec["lane"]
        if not lane or not rec["d1_exported"]:
            write_json(target, {"record_id": rid, "status": "SKIPPED_NO_LANE_OR_NO_D1",
                                "lane": lane, "d1_exported": bool(rec["d1_exported"])}, private=True)
            skipped += 1
            continue
        codes = _lane_codes(config, lane)
        container = rec["record_id"] if rec["branch"] == "MFF" else rec["_d1_container_id"]
        meta = read_json(src.d1_meta_dir(config, rec["branch"]) / f"{container}.json")
        try:
            if rec["branch"] == "MFF":
                rows, info = ev.mff_events(rec, meta, config, codes)
            else:
                rows, info = ev.ha_events(rec, meta, config, codes)
            ev.write_events(rows, out_dir / f"{rid}.parquet")
            summary = {"record_id": rid, "status": "OK", "lane": lane, "branch": rec["branch"],
                       "d1_container_id": container, **info, **ev.record_event_summary(rows, codes)}
            done += 1
        except Exception as exc:  # recorded, never silently dropped
            summary = {"record_id": rid, "status": "FAILED", "lane": lane, "error_class": type(exc).__name__,
                       "error": str(exc)[:400], "traceback_tail": traceback.format_exc()[-1200:]}
            failed += 1
        write_json(target, summary, private=True)
    result = {"assigned": len(mine), "done": done, "failed": failed, "skipped": skipped}
    finish(run["private"], "events", result)
    return result


# ----------------------------------------------------------------------------- scope

def _event_summaries(private: Path) -> dict[str, dict]:
    out = {}
    for path in sorted((private / "event_summaries").glob("*.json")):
        payload = read_json(path)
        if payload.get("status") == "OK":
            out[payload["record_id"]] = payload
    return out


def cmd_scope(args, config) -> dict:
    run = create_run("scope", args.run, config, args=vars(args), allow_existing=True)
    records = pd.read_parquet(run["private"] / "records.parquet")
    summaries = _event_summaries(run["private"])
    statuses = {}
    for path in (run["private"] / "event_summaries").glob("*.json"):
        s = read_json(path).get("status", "MISSING")
        statuses[s] = statuses.get(s, 0) + 1
    expected = int(((records.lane.astype(str) != "") & records.d1_exported.astype(bool)).sum())
    if statuses.get("OK", 0) + statuses.get("FAILED", 0) < expected:
        raise ProvenanceError(f"EVENTS_INCOMPLETE:{statuses}:expected_{expected}")
    tables = {"data_scope_table": sc.data_scope_table(records, summaries, config),
              "task_event_table": sc.task_event_table(records, summaries, config),
              "record_support_table": sc.record_support_table(records, summaries)}
    hashes = sc.write_public_tables(run["public"], tables)
    failed = [{"record_id": read_json(p)["record_id"], "error_class": read_json(p).get("error_class")}
              for p in (run["private"] / "event_summaries").glob("*.json") if read_json(p).get("status") == "FAILED"]
    summary = {"run": args.run, "event_statuses": statuses, "expected_event_records": expected,
               "failed_records": failed, "table_sha256": hashes,
               "records_by_branch": {k: int(v) for k, v in records.branch.value_counts().items()},
               "identity_groups_by_branch": {k: int(v) for k, v in records.groupby("branch").identity_group.nunique().items()},
               "note": "Outcome-blind scope. No EEG readout has been fitted."}
    write_json(run["public"] / "scope_summary.json", summary, private=False)
    finish(run["private"], "scope", summary)
    return summary


# ----------------------------------------------------------------------------- features

def _lane_records(config: dict, scope_private: Path, lanes: list[str]) -> list[dict]:
    records = pd.read_parquet(scope_private / "records.parquet")
    summaries = _event_summaries(scope_private)
    keep = records[records.lane.isin(lanes) & records.d1_exported & records.record_id.isin(list(summaries))]
    keep = keep[keep.source_gate.isin(["eligible", "eligible_technical_measurement"])]
    return keep.sort_values("record_id").to_dict("records")


def cmd_features(args, config) -> dict:
    run = create_run("features", args.run, config, args=vars(args), allow_existing=True)
    scope_private = private_dir(config, args.scope_run)
    lanes = [x for x in args.lanes.split(",") if x]
    post = {lane: float(cfg(config, f"lanes.{lane}.post_seconds")) for lane in lanes}  # frozen per lane
    records = _lane_records(config, scope_private, lanes)
    out_dir = run["private"] / "features"
    sup_dir = run["private"] / "support"
    for d in (out_dir, sup_dir):
        d.mkdir(mode=0o700, exist_ok=True)
    if not (run["private"] / "scope_link.json").exists():
        write_json(run["private"] / "scope_link.json", {"scope_run": args.scope_run, "lanes": lanes,
                   "post_seconds": post, "records_sha256": digest(scope_private / "records.parquet")}, private=True)
    mine = array_slice(records)
    done = failed = skipped = 0
    for rec in mine:
        rid = rec["record_id"]
        target = sup_dir / f"{rid}.json"
        if target.exists():
            skipped += 1
            continue
        container = rid if rec["branch"] == "MFF" else rec["_d1_container_id"]
        meta = read_json(src.d1_meta_dir(config, rec["branch"]) / f"{container}.json")
        array_path = src.d1_meta_dir(config, rec["branch"]) / f"{container}.npy"
        try:
            frame = pd.read_parquet(scope_private / "events" / f"{rid}.parquet")
            out = ft.extract_record(array_path, meta, frame, config, post_seconds=post[rec["lane"]],
                                    codes=_lane_codes(config, rec["lane"]))
            ft.save_features(out, out_dir / f"{rid}.npz", record_id=rid, lane=rec["lane"],
                             identity_group=rec["identity_group"])
            support = {"record_id": rid, "lane": rec["lane"], "status": "OK", "post_seconds": post[rec["lane"]],
                       "n_windows": int(len(out["window_starts"])), "record_scale": out["record_scale"],
                       "features_sha256": digest(out_dir / f"{rid}.npz"), **ft.record_support(out, config)}
            done += 1
        except Exception as exc:
            support = {"record_id": rid, "lane": rec["lane"], "status": "FAILED",
                       "error_class": type(exc).__name__, "error": str(exc)[:400],
                       "traceback_tail": traceback.format_exc()[-1200:]}
            failed += 1
        write_json(target, support, private=True)
    result = {"assigned": len(mine), "done": done, "failed": failed, "skipped": skipped}
    finish(run["private"], "features", result)
    return result


def cmd_support(args, config) -> dict:
    run = create_run("support", args.run, config, args=vars(args), allow_existing=True)
    rows = [read_json(p) for p in sorted((run["private"] / "support").glob("*.json"))]
    frame = pd.DataFrame([{k: v for k, v in r.items() if k not in ("traceback_tail",)} for r in rows])
    if "accepted_per_class" in frame:
        frame["accepted_class0"] = frame.accepted_per_class.apply(lambda d: d.get("0", 0) if isinstance(d, dict) else 0)
        frame["accepted_class1"] = frame.accepted_per_class.apply(lambda d: d.get("1", 0) if isinstance(d, dict) else 0)
    public_cols = [c for c in ["record_id", "lane", "status", "post_seconds", "n_windows", "n_supported_epochs",
                               "n_accepted", "accepted_class0", "accepted_class1", "record_supported", "error_class"]
                   if c in frame]
    frame[public_cols].to_csv(run["public"] / "record_support.csv", index=False)
    (run["public"] / "record_support.csv").chmod(0o644)
    summary = {"run": args.run, "records": int(len(frame)),
               "by_lane": {lane: {"records": int(len(sub)), "ok": int((sub.status == "OK").sum()),
                                  "supported": int(sub.get("record_supported", pd.Series(dtype=bool)).fillna(False).astype(bool).sum())}
                           for lane, sub in frame.groupby("lane")}}
    write_json(run["public"] / "support_summary.json", summary, private=False)
    finish(run["private"], "support", summary)
    return summary


# ----------------------------------------------------------------------------- probe

def cmd_probe(args, config) -> dict:
    """One record end to end, twice: determinism, timing grid, class counts, manipulation check."""
    run = create_run("probe", args.run, config, args=vars(args))
    scope_private = private_dir(config, args.scope_run)
    records = pd.read_parquet(scope_private / "records.parquet")
    rec = records[records.record_id == args.record].to_dict("records")
    if len(rec) != 1:
        raise ProvenanceError(f"PROBE_RECORD_NOT_FOUND:{args.record}")
    rec = rec[0]
    lane = rec["lane"]
    post = float(cfg(config, f"lanes.{lane}.post_seconds"))
    container = rec["record_id"] if rec["branch"] == "MFF" else rec["_d1_container_id"]
    meta = read_json(src.d1_meta_dir(config, rec["branch"]) / f"{container}.json")
    array_path = src.d1_meta_dir(config, rec["branch"]) / f"{container}.npy"
    frame = pd.read_parquet(scope_private / "events" / f"{rec['record_id']}.parquet")
    codes = _lane_codes(config, lane)
    a = ft.extract_record(array_path, meta, frame, config, post_seconds=post, codes=codes)
    b = ft.extract_record(array_path, meta, frame, config, post_seconds=post, codes=codes)
    checks = {}
    checks["deterministic_features"] = bool(np.array_equal(a["features"], b["features"]))
    checks["deterministic_accepted"] = bool(np.array_equal(a["accepted"], b["accepted"]))
    checks["finite"] = bool(np.isfinite(a["features"]).all())
    rate = float(meta["rate_hz"])
    starts, length = a["window_starts"], int(a["window_length"])
    checks["window_length_samples"] = length
    checks["window_step_samples"] = int(starts[1] - starts[0]) if len(starts) > 1 else None
    checks["n_windows"] = int(len(starts))
    checks["first_centre_s"] = float(a["window_centres_s"][0])
    checks["last_centre_s"] = float(a["window_centres_s"][-1])
    checks["grid_ok"] = (length == int(round(cfg(config, "window.length_seconds") * rate))
                         and checks["window_step_samples"] == int(round(cfg(config, "window.step_seconds") * rate)))
    checks["shape"] = list(a["features"].shape)
    support = ft.record_support(a, config)
    checks.update(support)
    # Manipulation check: standardised class difference of the window means, pre vs post.
    X, y, acc = a["features"], a["y"], a["accepted"]
    if acc.sum() and len(np.unique(y[acc])) == 2:
        d = X[acc & (y == 1)].mean(0) - X[acc & (y == 0)].mean(0)            # [W, C]
        s = X[acc].std(0) + 1e-9
        z = np.abs(d / s).mean(1)                                             # [W]
        pre = a["window_centres_s"] < 0
        checks["mean_abs_z_pre"] = float(z[pre].mean()) if pre.any() else None
        checks["mean_abs_z_post"] = float(z[~pre].mean())
        checks["max_abs_z_post_centre_s"] = float(a["window_centres_s"][~pre][np.argmax(z[~pre])])
        # Standard-error scaled difference per channel/window (two-sample z); a pure-noise record gives
        # max over 128 channels of about 2.5-3.0 and about 5% of channels above 2.
        n1, n0 = int((acc & (y == 1)).sum()), int((acc & (y == 0)).sum())
        se = np.sqrt(X[acc & (y == 1)].var(0, ddof=1) / n1 + X[acc & (y == 0)].var(0, ddof=1) / n0) + 1e-9
        zse = np.abs(d / se)                                                  # [W, C]
        checks["se_z_max_per_window_pre_mean"] = float(zse[pre].max(1).mean()) if pre.any() else None
        checks["se_z_max_per_window_post_mean"] = float(zse[~pre].max(1).mean())
        checks["se_z_max_overall"] = float(zse.max())
        checks["se_z_max_overall_centre_s"] = float(a["window_centres_s"][int(np.argmax(zse.max(1)))])
        checks["frac_channels_se_z_gt2_pre"] = float((zse[pre] > 2).mean()) if pre.any() else None
        checks["frac_channels_se_z_gt2_post"] = float((zse[~pre] > 2).mean())
        checks["n_deviant_accepted"] = n1
        checks["n_standard_accepted"] = n0
    # Timing sanity against the events table
    sup = frame[(frame.event_kind == "target") & frame.epoch_supported]
    checks["events_supported_in_table"] = int(len(sup))
    checks["epochs_extracted"] = int(len(a["y"]))
    checks["max_alignment_residual_ms"] = float(sup.alignment_residual_ms.max()) if len(sup) else None
    gate = all([checks["deterministic_features"], checks["deterministic_accepted"], checks["finite"],
                checks["grid_ok"], checks["record_supported"]])
    payload = {"run": args.run, "record_id": rec["record_id"], "lane": lane, "branch": rec["branch"],
               "post_seconds": post, "checks": checks, "gate": "PASS" if gate else "FAIL"}
    write_json(run["public"] / "probe.json", payload, private=False)
    ft.save_features(a, run["private"] / f"{rec['record_id']}_probe.npz", record_id=rec["record_id"],
                     lane=lane, identity_group=rec["identity_group"])
    finish(run["private"], "probe", payload)
    return payload


# ----------------------------------------------------------------------------- readout

def cmd_readout(args, config) -> dict:
    run = create_run("readout", args.run, config, args=vars(args))
    lane = args.lane
    feat_private = private_dir(config, args.features_run)
    prereg = ROOT / cfg(config, "project.prereg_file")
    if not prereg.is_file():
        raise ProvenanceError("PREREG_MISSING: readout refuses to run before the frozen pre-registration exists")
    supports = [read_json(p) for p in sorted((feat_private / "support").glob("*.json"))]
    chosen = [s for s in supports if s.get("lane") == lane and s.get("status") == "OK" and s.get("record_supported")]
    held = [{"record_id": s["record_id"], "reason": ("failed" if s.get("status") != "OK" else "record_support_below_minimum")}
            for s in supports if s.get("lane") == lane and s not in chosen]
    # Native layouts must not be mixed inside one readout: keep the majority channel count.
    channel_counts = {}
    for s in chosen:
        with np.load(feat_private / "features" / f"{s['record_id']}.npz", allow_pickle=False) as store:
            channel_counts[s["record_id"]] = int(store["n_channels"])
    majority = max(set(channel_counts.values()), key=lambda k: sum(1 for v in channel_counts.values() if v == k))
    for s in list(chosen):
        if channel_counts[s["record_id"]] != majority:
            held.append({"record_id": s["record_id"], "reason": f"layout_channels_{channel_counts[s['record_id']]}_ne_majority_{majority}"})
            chosen.remove(s)
    paths = [feat_private / "features" / f"{s['record_id']}.npz" for s in chosen]
    data = rd.load_lane(paths, config)
    folds = rd.lane_folds(data, config)
    tg_on = bool(cfg(config, "readout.temporal_generalisation"))
    from joblib import Parallel, delayed
    n_jobs = max(1, int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
    results = Parallel(n_jobs=n_jobs, backend="loky")(
        delayed(rd.run_fold)(data, train, test, config, temporal_generalisation=tg_on) for _, train, test in folds)
    N, W = data.X.shape[0], data.X.shape[1]
    dec = np.full((N, W), np.nan, dtype=np.float32)
    p_cal = np.full((N, W), np.nan, dtype=np.float32)
    p_stack = np.full((N, W), np.nan, dtype=np.float32)
    p_hist = np.full(N, np.nan, dtype=np.float32)
    prior_p1 = np.full(N, np.nan, dtype=np.float32)
    child_rows, tg_mats, block_rows, within_rows = [], [], [], []
    partitions = {"early_late_halves": data.half, "odd_even_blocks": data.parity}
    for (g, _train, test), res in zip(folds, results):
        dec[test], p_cal[test], p_stack[test] = res["dec"], res["p_cal"], res["p_stack"]
        p_hist[test], prior_p1[test] = res["p_hist"], res["prior_p1"]
        y = data.y[test]
        m = rd.child_metrics(y, res["dec"], res["p_stack"], res["p_hist"], res["prior_p1"], res["prior_logit"],
                             p_cal=res["p_cal"])
        child_rows.append({"identity_group": g, "n_records": int(len(np.unique(data.record[test]))), **m})
        if tg_on:
            tg_mats.append(rd.tg_auc(y, res["tg"]))
        for pname, part in partitions.items():
            for blk in (0, 1):
                sel = part[test] == blk
                if sel.sum() and len(np.unique(y[sel])) == 2:
                    mb = rd.child_metrics(y[sel], res["dec"][sel], res["p_stack"][sel], res["p_hist"][sel],
                                          res["prior_p1"], res["prior_logit"], p_cal=res["p_cal"][sel])
                    block_rows.append({"identity_group": g, "partition": pname, "block": blk, **mb})
        if bool(cfg(config, "readout.within_child_secondary")):
            for pname, part in partitions.items():
                for row in rd.within_child(data, test, part, config):
                    within_rows.append({"identity_group": g, "partition": pname, **row})
    # ---- aggregates (children are the unit)
    boot = cfg(config, "metrics.bootstrap")
    curves = {}
    for key in ("bacc", "auc", "ll_eeg_raw", "ll_eeg", "ll_stack", "g_prior_raw", "g_prior", "g_hist"):
        arr = np.stack([r[key] for r in child_rows])
        mean, lo, hi = rd.bootstrap_mean(arr, n=int(boot["n"]), seed=int(boot["seed"]))
        curves[key] = {"mean": mean, "lo": lo, "hi": hi, "median": np.nanmedian(arr, 0),
                       "p25": np.nanpercentile(arr, 25, 0), "p75": np.nanpercentile(arr, 75, 0)}
    refs = {k: float(np.mean([r[k] for r in child_rows])) for k in ("ll_prior", "ll_hist", "bacc_hist", "auc_hist")}
    curve_rows = []
    for w in range(W):
        row = {"window_centre_s": float(data.centres_s[w])}
        for key, c in curves.items():
            for stat in ("mean", "lo", "hi", "median", "p25", "p75"):
                row[f"{key}_{stat}"] = float(c[stat][w])
        row.update(refs)
        curve_rows.append(row)
    pd.DataFrame(curve_rows).to_csv(run["public"] / "curves.csv", index=False)
    # pre-specified bands
    bands = {"pre": (-0.2, 0.0), "early": (0.05, 0.25), "mid": (0.25, 0.45), "late": (0.45, float(data.centres_s[-1]) + 0.04)}
    band_rows = []
    for name, (lo_s, hi_s) in bands.items():
        sel = (data.centres_s >= lo_s) & (data.centres_s < hi_s)
        if not sel.any():
            continue
        for key in ("bacc", "auc", "g_prior", "g_prior_raw", "g_hist"):
            arr = np.stack([np.nanmean(r[key][sel]) for r in child_rows])[:, None]
            mean, lo, hi = rd.bootstrap_mean(arr, n=int(boot["n"]), seed=int(boot["seed"]))
            band_rows.append({"band": name, "from_s": lo_s, "to_s": hi_s, "metric": key, "mean": float(mean[0]),
                              "ci_lo": float(lo[0]), "ci_hi": float(hi[0]),
                              "children_positive": int(np.sum(arr[:, 0] > (0.5 if key in ("bacc", "auc") else 0.0))),
                              "children": int(arr.shape[0])})
    pd.DataFrame(band_rows).to_csv(run["public"] / "bands.csv", index=False)
    if tg_on:
        tg_mean = np.nanmean(np.stack(tg_mats), 0)
        pd.DataFrame(tg_mean, index=[f"{c:.2f}" for c in data.centres_s],
                     columns=[f"{c:.2f}" for c in data.centres_s]).to_csv(run["public"] / "tg_auc_mean.csv")
        np.savez_compressed(run["private"] / "child_tg.npz", tg=np.stack(tg_mats),
                            groups=np.array([r["identity_group"] for r in child_rows]), centres_s=data.centres_s)
    # repeatability across independent blocks
    rep_rows = []
    if block_rows:
        bdf = pd.DataFrame(block_rows)
        for pname in partitions:
            sub = bdf[bdf.partition == pname]
            a = sub[sub.block == 0].set_index("identity_group")
            b = sub[sub.block == 1].set_index("identity_group")
            common = a.index.intersection(b.index)
            for key in ("bacc", "auc", "g_hist"):
                A = np.stack([a.loc[g, key] for g in common]) if len(common) else np.empty((0, W))
                B = np.stack([b.loc[g, key] for g in common]) if len(common) else np.empty((0, W))
                for w in range(W):
                    rep_rows.append({"partition": pname, "metric": key, "window_centre_s": float(data.centres_s[w]),
                                     "children": int(len(common)),
                                     "spearman_block0_block1": rd.spearman(A[:, w], B[:, w]) if len(common) else np.nan,
                                     "mean_abs_diff": float(np.nanmean(np.abs(A[:, w] - B[:, w]))) if len(common) else np.nan,
                                     "between_child_sd": float(np.nanstd((A[:, w] + B[:, w]) / 2)) if len(common) else np.nan})
    pd.DataFrame(rep_rows).to_csv(run["public"] / "repeatability.csv", index=False)
    within_summary = []
    if within_rows:
        for pname in partitions:
            ok = [r for r in within_rows if r["partition"] == pname and r["supported"]]
            if ok:
                auc = np.stack([r["auc"] for r in ok])
                mean, lo, hi = rd.bootstrap_mean(auc, n=int(boot["n"]), seed=int(boot["seed"]))
                for w in range(W):
                    within_summary.append({"partition": pname, "window_centre_s": float(data.centres_s[w]),
                                           "directions": int(len(ok)),
                                           "children": int(len({r["identity_group"] for r in ok})),
                                           "auc_mean": float(mean[w]), "auc_lo": float(lo[w]), "auc_hi": float(hi[w])})
    pd.DataFrame(within_summary).to_csv(run["public"] / "within_child.csv", index=False)
    # private trial-level and child-level artefacts
    np.savez_compressed(run["private"] / "trial_predictions.npz", trial=data.trial, record=data.record,
                        group=data.group, y=data.y, dec=dec, p_cal=p_cal, p_stack=p_stack, p_hist=p_hist,
                        prior_p1=prior_p1, centres_s=data.centres_s)
    pd.DataFrame([{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in r.items()} for r in child_rows]
                 ).to_json(run["private"] / "child_metrics.json", orient="records", indent=1)
    for p in run["private"].glob("*"):
        if p.is_file():
            p.chmod(0o600)
    summary = {"run": args.run, "lane": lane, "features_run": args.features_run,
               "prereg_sha256": digest(prereg), "config_sha256": config["_sha256"],
               "children": len(folds), "records": len(chosen), "trials": int(N),
               "deviant_trials": int(np.sum(data.y == 1)), "windows": int(W),
               "window_centres_s": [float(c) for c in data.centres_s],
               "held_records": held, "references": refs, "n_channels": int(majority),
               "class_prior_p1_mean_over_folds": float(np.nanmean(prior_p1)),
               "note": "Neutral result tables; interpretation lives in the results document."}
    write_json(run["public"] / "summary.json", summary, private=False)
    finish(run["private"], "readout", {"children": len(folds), "records": len(chosen)})
    return summary


# ----------------------------------------------------------------------------- report

def cmd_report(args, config) -> dict:
    run = create_run("report", args.run, config, args=vars(args))
    readouts = {}
    for name in [x for x in args.readout_runs.split(",") if x]:
        ro = rp.load_readout(config, name)
        if ro is None:
            raise ProvenanceError(f"READOUT_RUN_INCOMPLETE:{name}")
        readouts[ro["summary"]["lane"]] = ro
    fig_dir = ROOT / "figures/auditory_st" / args.run
    fig_dir.mkdir(parents=True, exist_ok=False)
    figures = {}
    for lane, ro in readouts.items():
        figures[lane + "_curves"] = rp.figure_lane(lane, ro, fig_dir)
        figures[lane + "_tg"] = rp.figure_tg(lane, ro, fig_dir)
        figures[lane + "_repeatability"] = rp.figure_repeatability(lane, ro, fig_dir)
    figures["overview"] = rp.figure_overview(readouts, fig_dir)
    rules = rp.rule_table(readouts)
    rules.to_csv(run["public"] / "rule_table.csv", index=False)
    scope = read_json(results_dir(config, args.scope_run) / "scope_summary.json")
    support_path = results_dir(config, args.features_run) / "record_support.csv"
    support = pd.read_csv(support_path) if support_path.is_file() else pd.DataFrame()
    probe = read_json(results_dir(config, args.probe_run) / "probe.json") if args.probe_run else {}
    doc_dir = ROOT / cfg(config, "paths.docs_relative")
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc = rp.write_results_md(config, args.run, readouts, rules, scope, support, probe, figures, doc_dir)
    summary = {"run": args.run, "lanes": list(readouts), "results_doc": str(doc.relative_to(ROOT)),
               "figures": {k: [str(p.relative_to(ROOT)) for p in v] for k, v in figures.items()},
               "rule_table_sha256": digest(run["public"] / "rule_table.csv"), "results_doc_sha256": digest(doc)}
    write_json(run["public"] / "report_summary.json", summary, private=False)
    finish(run["private"], "report", summary)
    return summary


# ----------------------------------------------------------------------------- main

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditory_st")
    parser.add_argument("command", choices=["sources", "events", "scope", "features", "support", "probe", "readout", "report"])
    parser.add_argument("--run", required=True)
    parser.add_argument("--config", default="configs/auditory_st_v1.yaml")
    parser.add_argument("--scope-run")
    parser.add_argument("--features-run")
    parser.add_argument("--lanes", default="mff_puretone,mff_bapa,bdf_puretone")
    parser.add_argument("--lane")
    parser.add_argument("--record")
    parser.add_argument("--readout-runs", default="")
    parser.add_argument("--probe-run", default="")
    args = parser.parse_args(argv)
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Slurm only")
    os.umask(0o077)
    config = load_config(args.config)
    result = {"sources": cmd_sources, "events": cmd_events, "scope": cmd_scope, "features": cmd_features,
              "support": cmd_support, "probe": cmd_probe, "readout": cmd_readout, "report": cmd_report}[args.command](args, config)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
