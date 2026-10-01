"""A1: information-source controls without training any encoder (execution spec section 5; protocol section 2).

controls-prep (CPU): per primary record, rebuild every staged target epoch from D1 + ST1 events and require bit-exact
equality with GX_stage_001 (and the same QC acceptance); store draw0 trials, raw 20 ms bins, and seeded non-aligned
windows that match the draw0 60-s block counts, stay inside the stored interval with the 2 s guard, sit > 80 ms from
every recorded target / unknown-sound event and pass the staging QC in uV. controls-infer (GPU, bf16): per (seed, fold)
re-embed draw0 with M_o (consistency against agg_base[:,0]), embed the non-aligned windows with M_o, and embed draw0
with an untrained same-architecture EEGNet. age-controls (CPU): ridge readouts with the A0 rules.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from auditory_st.features import epoch_qc

from . import age_core
from . import age_readout as ar
from . import representations as rp
from .adapters import AgeSource, d1_array, d1_meta, load_stage, st_events, st_records, units
from .runtime import (ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, save_npz_atomic, stable_int,
                      write_json_atomic, write_parquet_atomic)

FORBIDDEN_GPU_TOKENS = ("P100", "H100", "RTX PRO 6000", "RTX6000", "PRO 6000")


def _gx(config: dict) -> dict:
    from auditory_gx.runtime import load_config as gx_load
    return gx_load(cfg(config, "sources.gx_config"))


def _qc_fn(gx: dict):
    q = gx["qc"]
    return lambda e: epoch_qc(e, ptp_max=float(q["ptp_max_uv"]), ptp_fraction_max=float(q["ptp_channel_fraction_max"]),
                              flat_ptp=float(q["flat_ptp_uv"]), flat_fraction_max=float(q["flat_channel_fraction_max"]))


def draw0_indices(src: AgeSource, child: int, stage: dict) -> dict:
    """Staged trial indices of the draw0 budget (draw positions index the accepted trials in stage order)."""
    r = src.primary(child)
    row = src.co.draw_row[r]
    acc = np.flatnonzero(stage["accepted"].astype(bool))
    out = {}
    for cls, pos in ((0, src.co.draw_std[row, 0]), (1, src.co.draw_dev[row, 0])):
        idx = acc[np.asarray(pos, dtype=np.int64)]
        if not np.all(stage["y"][idx] == cls):
            raise ProvenanceError(f"DRAW0_CLASS_MISMATCH:child{child}")
        out[cls] = idx
    return out


def rebuild_check(config: dict, gx: dict, rid: str, stage: dict, events: pd.DataFrame, meta: dict, data) -> dict:
    """Re-cut every staged target epoch exactly as auditory_gx.stage.stage_record does and compare bit for bit."""
    rate = float(meta["rate_hz"])
    pre, post = int(round(0.2 * rate)), int(round(0.6 * rate))
    guard = int(round(float(gx["epoch"]["interval_edge_guard_seconds"]) * rate))
    intervals = {int(r["interval_index"]): r for r in meta["intervals"]}
    t = events[(events.event_kind == "target") & (events.exported_index >= 0)]
    keep = [int(r.exported_index) - pre >= int(intervals[int(r.exported_interval_index)]["start"]) + guard
            and int(r.exported_index) + post <= int(intervals[int(r.exported_interval_index)]["stop"]) - guard
            for r in t.itertuples()]
    t = t[np.asarray(keep, dtype=bool)]
    on = t.exported_index.to_numpy(dtype=np.int64)
    ep = np.stack([np.asarray(data[:, e - pre:e + post], dtype=np.float32) for e in on]) if len(on) else np.zeros((0, 20, 200), np.float32)
    x16 = rp.stage_transform(ep, float(stage["record_scale"]))
    qc = _qc_fn(gx)
    acc = np.array([qc(e)[0] for e in ep], dtype=bool)
    same_shape = x16.shape == stage["x"].shape
    return {"n_epochs": int(len(on)), "x_bit_exact": bool(same_shape and np.array_equal(x16.view(np.uint16), stage["x"].view(np.uint16))),
            "accepted_equal": bool(same_shape and np.array_equal(acc, stage["accepted"].astype(bool))),
            "onsets_equal": bool(same_shape and np.allclose(t.onset_seconds.to_numpy(), stage["onset_seconds"]))}


def nonaligned_windows(config: dict, gx: dict, rid: str, stage: dict, d0: dict, events: pd.DataFrame, meta: dict, data) -> dict:
    na = config["controls"]["nonaligned"]
    rate = float(meta["rate_hz"])
    pre, post = int(round(float(na["pre_seconds"]) * rate)), int(round((float(na["source_epoch_seconds"]) - float(na["pre_seconds"])) * rate))
    guard = int(round(float(na["interval_guard_seconds"]) * rate))
    excl = int(round(float(na["anchor_exclusion_seconds"]) * rate))
    kinds = set(na["exclusion_event_kinds"])
    blocks = stage["block_id"][np.concatenate([d0[0], d0[1]])]
    quota = pd.Series(blocks).value_counts().to_dict()
    qc = _qc_fn(gx)
    anchors, ablock, aint, n_cand, n_cand_raw, shortfall, tested = [], [], [], 0, 0, {}, 0
    ev_all = events[(events.exported_index >= 0) & (events.event_kind.isin(kinds))]
    for iv in meta["intervals"]:
        ev = ev_all[ev_all.exported_interval_index == int(iv["interval_index"])].exported_index.to_numpy(dtype=np.int64)
        raw = rp.candidate_anchors(iv, np.zeros(0, np.int64), pre=pre, post=post, guard=guard, exclusion=excl)
        cand = rp.candidate_anchors(iv, ev, pre=pre, post=post, guard=guard, exclusion=excl)
        n_cand_raw += raw.size
        n_cand += cand.size
        cb = np.array([rp.block_of_anchor(a, iv, stride=int(meta["stride"]), original_fs=float(meta["original_fs"]),
                                          block_seconds=float(na["physical_block_seconds"])) for a in cand], dtype=np.int64)
        for b, q in sorted(quota.items()):
            sel = cand[cb == int(b)]
            if sel.size == 0:
                continue
            rng = np.random.default_rng(stable_int(int(na["seed"]), rid, int(b)) % (2 ** 63))
            got, t = rp.select_block_windows(sel, int(q) - sum(1 for x in ablock if x == int(b)), rng,
                                             lambda a: qc(np.asarray(data[:, a - pre:a + post], dtype=np.float32))[0])
            tested += t
            anchors += got
            ablock += [int(b)] * len(got)
            aint += [int(iv["interval_index"])] * len(got)
    have = pd.Series(ablock).value_counts().to_dict() if ablock else {}
    for b, q in quota.items():
        if have.get(int(b), 0) < int(q):
            shortfall[int(b)] = int(q) - have.get(int(b), 0)
    anchors = np.asarray(anchors, dtype=np.int64)
    order = np.argsort(anchors, kind="stable")
    anchors, ablock, aint = anchors[order], np.asarray(ablock)[order], np.asarray(aint)[order]
    ev_any = events[events.exported_index >= 0].exported_index.to_numpy(dtype=np.int64)
    win = np.stack([np.asarray(data[:, a - pre:a + post], dtype=np.float32) for a in anchors]) if anchors.size else np.zeros((0, 20, pre + post), np.float32)
    return {"x": rp.stage_transform(win, float(stage["record_scale"])), "anchors": anchors, "blocks": ablock, "intervals": aint,
            "nearest_event": rp.nearest_event_distance(anchors, ev_any), "quota_total": int(sum(quota.values())),
            "shortfall": shortfall, "n_candidates": int(n_cand), "n_candidates_before_exclusion": int(n_cand_raw),
            "n_qc_tested": int(tested), "pre": pre, "post": post}


def cmd_controls_prep(args, config) -> dict:
    require_protocol(config)
    run = open_run("controls_prep", args.run, config, args=vars(args))
    src = AgeSource(config)
    gx = _gx(config)
    st = st_records(config).set_index("record_id")
    bin_samples = int(round(float(cfg(config, "controls.raw_bin_seconds")) * float(cfg(config, "controls.rate_hz"))))
    out_dir = run["private"] / "inputs"
    rows, recs = [], []
    for c in src.main_children:
        r = src.primary(c)
        rid = str(src.rec.loc[r, "record_id"])
        path = out_dir / f"{rid}.npz"
        if not path.exists():
            stage = load_stage(config, rid)
            events = st_events(config, rid)
            cid = str(st.loc[rid, "_d1_container_id"])
            meta, data = d1_meta(config, cid), d1_array(config, cid)
            chk = rebuild_check(config, gx, rid, stage, events, meta, data)
            d0 = draw0_indices(src, c, stage)
            x0, x1 = stage["x"][d0[0]], stage["x"][d0[1]]
            raw0 = rp.raw_bins(x0, bin_samples).mean(0)
            raw1 = rp.raw_bins(x1, bin_samples).mean(0)
            span = stage["onset_seconds"][np.concatenate([d0[0], d0[1]])]
            na = nonaligned_windows(config, gx, rid, stage, d0, events, meta, data)
            save_npz_atomic(path, child=np.int64(c), x_std=x0, x_dev=x1, raw_mu0=raw0, raw_mu1=raw1, x_nonaligned=na["x"],
                            anchors=na["anchors"], blocks=na["blocks"], intervals=na["intervals"], nearest_event=na["nearest_event"],
                            meta=np.asarray(json.dumps({**chk, "quota_total": na["quota_total"], "shortfall": na["shortfall"],
                                                        "n_candidates": na["n_candidates"],
                                                        "n_candidates_before_exclusion": na["n_candidates_before_exclusion"],
                                                        "n_qc_tested": na["n_qc_tested"], "draw0_span_s": float(np.ptp(span)),
                                                        "raw_bins_dropped_samples": int(x0.shape[-1] % bin_samples)})))
        with np.load(path, allow_pickle=False) as z:
            m = json.loads(str(z["meta"]))
            recs.append({"child": c, **{k: v for k, v in m.items() if k != "shortfall"}, "n_windows": int(len(z["anchors"])),
                         "fully_supported": not m["shortfall"], "nearest_event_min_samples": int(z["nearest_event"].min()) if len(z["anchors"]) else None})
            for a, b, iv, d in zip(z["anchors"], z["blocks"], z["intervals"], z["nearest_event"]):
                rows.append({"record_id": rid, "interval": int(iv), "anchor": int(a), "start": int(a) - 50, "stop": int(a) + 150,
                             "block": int(b), "nearest_event_samples": int(d)})
    write_parquet_atomic(pd.DataFrame(rows), run["private"] / "nonaligned_windows.parquet")
    R = pd.DataFrame(recs)
    summary = {"records": int(len(R)), "x_bit_exact": int(R.x_bit_exact.sum()), "accepted_equal": int(R.accepted_equal.sum()),
               "onsets_equal": int(R.onsets_equal.sum()), "nonaligned_fully_supported": int(R.fully_supported.sum()),
               "windows_total": int(R.n_windows.sum()), "quota_total": int(R.quota_total.sum()),
               "candidates_removed_by_exclusion_fraction": float(1 - R.n_candidates.sum() / R.n_candidates_before_exclusion.sum()),
               "min_nearest_event_ms": float(R.nearest_event_min_samples.min() * 4.0),
               "draw0_span_s_median": float(R.draw0_span_s.median()), "draw0_span_s_range": [float(R.draw0_span_s.min()), float(R.draw0_span_s.max())]}
    summary["gate_rebuild"] = bool(summary["x_bit_exact"] == len(R) and summary["accepted_equal"] == len(R))
    write_json_atomic(run["public"] / "summary_controls_prep.json", summary, private=False)
    close_run(config, "controls_prep", args.run, "COMPLETED" if summary["gate_rebuild"] else "SOURCE_UNRESOLVED")
    return summary


# ====================================================================== GPU inference

def _device(config: dict):
    import torch
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("controls-infer needs a bf16 GPU (A100/A40/L40S/A30)")
    name = torch.cuda.get_device_name(0)
    if any(tok in name.upper() for tok in FORBIDDEN_GPU_TOKENS):
        raise RuntimeError(f"FORBIDDEN_GPU:{name}")
    return torch.device("cuda"), name


def _eegnet(gx: dict):
    from auditory_gx.models import EEGNet
    m = gx["model"]
    return EEGNet(20, 200, 2, F1=int(m["F1"]), D=int(m["D"]), F2=int(m["F2"]), k1=int(m["k1"]), k2=int(m["k2"]),
                  dropout=float(m["dropout"]))


def _embed(model, x16: np.ndarray, dev) -> np.ndarray:
    import torch
    if len(x16) == 0:
        return np.zeros((0, 192), np.float32)
    with torch.no_grad():
        xb = torch.from_numpy(np.asarray(x16)).to(dev).float()
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            e = model.embed(xb)
    return e.float().cpu().numpy()


def cmd_controls_infer(args, config) -> dict:
    import torch
    from auditory_gx import train as gxt
    require_protocol(config)
    dev, gpu_name = _device(config)
    run = open_run("controls_infer", args.run, config, args=vars(args))
    src = AgeSource(config)
    gx = _gx(config)
    prep = ROOT / cfg(config, "paths.private_relative") / args.prep_run / "inputs"
    kids = src.main_children
    inputs = {}
    for c in kids:
        rid = str(src.rec.loc[src.primary(c), "record_id"])
        with np.load(prep / f"{rid}.npz", allow_pickle=False) as z:
            inputs[c] = {"x0": z["x_std"], "x1": z["x_dev"], "xn": z["x_nonaligned"],
                         "full": not json.loads(str(z["meta"]))["shortfall"]}
    stim = ROOT / "private/auditory_pf" / cfg(config, "sources.pf_stim_run")
    tol = float(cfg(config, "controls.consistency.embedding_abs_tol"))
    out = {}
    for s, k in units(config):
        path = run["private"] / "units" / f"s{s}_k{k}.npz"
        if not path.exists():
            model = _eegnet(gx)
            model.load_state_dict(torch.load(stim / f"unit_s{s}_k{k}" / "models" / "M_o.pt", map_location="cpu"), strict=True)
            model.to(dev).eval()
            gxt.seed_all(stable_int(int(cfg(config, "controls.random_initialization_seed")), s, k) % (2 ** 31 - 1))
            rnd = _eegnet(gx).eval().to(dev)
            agg = src.exports(s, k)["agg_base"]
            T = np.zeros((len(kids), 2, 192), np.float32)
            Rn = np.zeros_like(T)
            N = np.full((len(kids), 192), np.nan, np.float32)
            for i, c in enumerate(kids):
                T[i, 0], T[i, 1] = _embed(model, inputs[c]["x0"], dev).mean(0), _embed(model, inputs[c]["x1"], dev).mean(0)
                Rn[i, 0], Rn[i, 1] = _embed(rnd, inputs[c]["x0"], dev).mean(0), _embed(rnd, inputs[c]["x1"], dev).mean(0)
                if inputs[c]["full"]:
                    N[i] = _embed(model, inputs[c]["xn"], dev).mean(0)
            ref = agg[[src.primary(c) for c in kids], 0]
            diff = np.abs(T - ref)
            save_npz_atomic(path, children=np.asarray(kids), trained_draw0=T, random_draw0=Rn, nonaligned=N,
                            max_abs_diff=np.float64(diff.max()), median_abs_diff=np.float64(np.median(diff)),
                            gpu=np.asarray(gpu_name))
        with np.load(path, allow_pickle=False) as z:
            out[f"s{s}_k{k}"] = {"max_abs_diff": float(z["max_abs_diff"]), "median_abs_diff": float(z["median_abs_diff"]),
                                 "gpu": str(z["gpu"])}
    gate = all(v["max_abs_diff"] <= tol for v in out.values())
    summary = {"units": out, "gate_consistency": bool(gate), "tolerance": tol, "inference_units_trained": len(out),
               "inference_units_random": len(out), "gpu_names": sorted({v["gpu"] for v in out.values()})}
    write_json_atomic(run["public"] / "summary_controls_infer.json", summary, private=False)
    close_run(config, "controls_infer", args.run, "COMPLETED" if gate else "SOURCE_UNRESOLVED")
    return {"gate_consistency": gate, "max_abs_diff": max(v["max_abs_diff"] for v in out.values()),
            "gpu_names": summary["gpu_names"]}


# ====================================================================== readouts

def _fit_common(src, config, mu0, mu1, children, s, k, view, ledger):
    tr, te = age_core.split(src, s, k, children)
    pos = {c: i for i, c in enumerate(children)}
    rows = [pos[c] for c in tr + te]
    m0, m1 = mu0[rows], mu1[rows]
    y = np.array([src.age(c) for c in tr + te])
    a = config["age"]
    floor = float(a["scale_floor"])
    res = ar.select_and_fit(lambda trr, evr: rp.paired_design("common", m0, m1, trr, evr, floor=floor), y, len(tr),
                            np.arange(len(tr), len(rows)), kind="ridge", alphas=a["alpha_sse"],
                            inner_folds=int(a["inner_folds"]), inner_seed=age_core.inner_seed(s, k),
                            tie_tol=float(a["tie_tolerance"]), ledger=ledger, key={"view": view, "seed": s, "fold": k})
    return {"seed": s, "fold": k, "view": view, "test_children": te, "pred": res["pred"].tolist(), "alpha": res["alpha"],
            "inner_mae": res["inner_mae"], "constant_prediction": res["constant_prediction"], "n_fits": res["n_fits"],
            "status": "COMPLETED", "fits": ledger}


def cmd_age_controls(args, config) -> dict:
    require_protocol(config)
    run = open_run("age_controls", args.run, config, args=vars(args))
    src = AgeSource(config)
    kids = src.main_children
    priv = ROOT / cfg(config, "paths.private_relative")
    prep_sum = json.loads((ROOT / cfg(config, "paths.results_relative") / args.prep_run / "summary_controls_prep.json").read_text())
    inf_sum = json.loads((ROOT / cfg(config, "paths.results_relative") / args.infer_run / "summary_controls_infer.json").read_text())
    raw0, raw1, full = [], [], []
    for c in kids:
        rid = str(src.rec.loc[src.primary(c), "record_id"])
        with np.load(priv / args.prep_run / "inputs" / f"{rid}.npz", allow_pickle=False) as z:
            raw0.append(z["raw_mu0"]); raw1.append(z["raw_mu1"])
            full.append(not json.loads(str(z["meta"]))["shortfall"])
    raw0, raw1 = np.stack(raw0).astype(np.float64), np.stack(raw1).astype(np.float64)
    support = [c for c, f in zip(kids, full) if f]
    views = ["random_common", "raw_common"]
    if prep_sum["gate_rebuild"] and inf_sum["gate_consistency"]:
        views.append("nonaligned_common")
    matched_refit = "nonaligned_common" in views and len(support) < len(kids)
    if matched_refit:
        views.append("trained_common_matched")
    for s, k in units(config):
        with np.load(priv / args.infer_run / "units" / f"s{s}_k{k}.npz", allow_pickle=False) as z:
            if [int(c) for c in z["children"]] != kids:
                raise ProvenanceError("INFER_CHILD_ORDER")
            Rn, N = z["random_draw0"].astype(np.float64), z["nonaligned"].astype(np.float64)
        for view in views:
            path = run["private"] / "units" / view / f"s{s}_k{k}.json"
            if path.exists():
                continue
            if view == "random_common":
                res = _fit_common(src, config, Rn[:, 0], Rn[:, 1], kids, s, k, view, [])
            elif view == "raw_common":
                res = _fit_common(src, config, raw0, raw1, kids, s, k, view, [])
            elif view == "nonaligned_common":
                idx = [kids.index(c) for c in support]
                res = _fit_common(src, config, N[idx], N[idx], support, s, k, view, [])
            else:
                idx = [kids.index(c) for c in support]
                m0, m1 = src.class_means(s, k, support, "single_draw80")
                res = _fit_common(src, config, m0, m1, support, s, k, view, [])
            write_json_atomic(path, res, private=True)
    summary = summarize_controls(config, args.run, args.a0_run, views, support, matched_refit)
    summary.update({"rebuild_gate": prep_sum["gate_rebuild"], "consistency_gate": inf_sum["gate_consistency"],
                    "nonaligned_support": len(support)})
    write_json_atomic(run["public"] / "summary_a1.json", summary, private=False)
    close_run(config, "age_controls", args.run, summary["status"])
    return {"status": summary["status"], "comparisons": {k: v.get("mean") for k, v in summary["comparisons"].items()}}


def summarize_controls(config, run, a0_run, views, support, matched_refit) -> dict:
    src = AgeSource(config)
    kids = src.main_children
    ages = {c: src.age(c) for c in kids}
    priv = ROOT / cfg(config, "paths.private_relative")
    ul = units(config)

    def load(view, base, budget=None):
        rows = []
        for s, k in ul:
            p = (age_core.unit_path(priv / base, budget, view, s, k) if budget else priv / base / "units" / view / f"s{s}_k{k}.json")
            u = json.loads(p.read_text())
            if u["status"] != "COMPLETED":
                raise ProvenanceError(f"UNIT_NOT_COMPLETED:{view}:{s}_{k}")
            rows.append(u)
        return rows
    tables, n_fits = {}, 0
    a0_common = load("common", a0_run, "single_draw80")
    tables["trained_common"] = age_core.view_table(age_core.collect_predictions(a0_common, kids), ages, kids)
    for view in views:
        us = load(view, run)
        n_fits += sum(u["n_fits"] for u in us)
        ch = support if view in ("nonaligned_common", "trained_common_matched") else kids
        tables[view] = age_core.view_table(age_core.collect_predictions(us, ch), ages, ch)
        tables[view]["children"] = ch
    B = int(cfg(config, "age.bootstrap_children"))
    comps = {}
    for view in ("random_common", "raw_common", "nonaligned_common"):
        if view not in tables:
            comps[f"trained_minus_{view}"] = {"status": "TECHNICAL_INVALID"}
            continue
        ch = tables[view].get("children", kids)
        if len(ch) == len(kids):
            ref = tables["trained_common"]["err"]
            idx = np.random.default_rng(int(cfg(config, "age.bootstrap_seed"))).integers(0, len(kids), size=(B, len(kids)))
            ref_name = "single_draw80/common (A0, reused)"
        else:
            ref = tables["trained_common_matched"]["err"]
            idx = np.random.default_rng(int(cfg(config, "age.bootstrap_seed"))).integers(0, len(ch), size=(B, len(ch)))
            ref_name = "trained_common_matched (refit on support)"
        comps[f"trained_minus_{view}"] = {"reference": ref_name, "n": len(ch), **age_core.paired_boot(ref - tables[view]["err"], idx)}
    return {"status": "COMPLETED", "views": {v: {k: x for k, x in t.items() if k not in ("err", "children")} for v, t in tables.items()},
            "comparisons": comps, "matched_refit": matched_refit, "small_age_fits": n_fits,
            "sign_convention": "trained_common error minus control error; positive = control better"}
