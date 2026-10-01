"""P0 source check and the frozen plan (execution spec sections 3 and 13).

source-check: hashes, shapes, keys, model scope (T1/T2 on the real exports), identity uniqueness, record order, draw
budgets (T5), technical/spectral/stage/D1 availability and age-source status for the A cohort; writes the private
records manifest and model-scope manifest. plan: the deterministic unit table with exact counts against the caps.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from . import age_core
from .adapters import AgeSource, d1_meta, h14_errors, round1_cohort, stage_path, st_records, units
from .runtime import (ROOT, ProvenanceError, cfg, close_run, digest, open_run, refuse_existing, write_csv_atomic,
                      write_json_atomic)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name: str, ok: bool, detail=None, *, warn: bool = False):
        self.rows.append({"check": name, "status": "OK" if ok else ("WARN" if warn else "FAIL"), "detail": detail})
        return ok

    @property
    def failed(self) -> list[str]:
        return [r["check"] for r in self.rows if r["status"] == "FAIL"]


def _hash_files(paths) -> dict:
    return {str(p.relative_to(ROOT)): (digest(p) if p.exists() else None) for p in paths}


def cmd_source_check(args, config) -> dict:
    run = open_run("source_check", args.run, config, args=vars(args))
    ck = Checks()
    pf_priv = ROOT / "private/auditory_pf"
    files = [ROOT / cfg(config, f"sources.{k}") for k in ("pf_config", "pf_config_round1", "dv_config", "gx_config",
                                                           "pf_feature_file", "pf_h14_private", "ha_cohort", "pta_file",
                                                           "nh_override")]
    for prep in (cfg(config, "sources.pf_prepare_run"), cfg(config, "sources.pf_prepare_round1")):
        files += [pf_priv / prep / n for n in ("records.csv", "children.csv", "folds.json", "draws.npz", "trials.npz")]
    stim = pf_priv / cfg(config, "sources.pf_stim_run")
    for s, k in units(config):
        files += [stim / f"unit_s{s}_k{k}" / n for n in ("exports.npz", "models/M_o.pt", "fit_info.json", "DONE.json")]
    hashes = _hash_files(files)
    ck.add("source_files_present", all(v is not None for v in hashes.values()),
           [k for k, v in hashes.items() if v is None])

    src = AgeSource(config)
    co, rec, ch = src.co, src.co.rec, src.co.ch
    # identity: child <-> identity group one-to-one
    g = rec.groupby("child").identity_group.nunique()
    c_per_g = rec.groupby("identity_group").child.nunique()
    ck.add("identity_child_one_to_one", bool((g == 1).all() and (c_per_g == 1).all()))
    # record order identical in prepare_001 / prepare_002 and spectra rows
    _, co1 = round1_cohort(config)
    ck.add("record_order_round1_equals_pf2", list(co1.rec.record_id) == list(rec.record_id))
    ck.add("spectra_rows_equal_records", src.spectra.shape == (len(rec), 20, 9), list(src.spectra.shape))
    # model scope per unit (T1/T2 on real data)
    scope = {}
    for s, k in units(config):
        try:
            age_core.check_scope(src, s, k)
            ex = src.exports(s, k)
            train = sorted(int(c) for c in ex["train_children"])
            test = sorted(int(c) for c in ex["test_children"])
            val = sorted(int(c) for c in co.val_children(train, ("M_o", s, k)))
            info = json.loads((stim / f"unit_s{s}_k{k}" / "fit_info.json").read_text())["M_o"]
            ok = (set(val) <= set(train) and not (set(test) & set(train))
                  and info["n_val_children"] == len(val) and info["n_train_children"] == len(train) - len(val))
            finite = np.isfinite(ex["agg_base"].reshape(len(rec), -1)).all(1)
            ok &= bool(np.array_equal(finite, rec.rec.isin(list(co.draw_row)).to_numpy()))
            scope[f"s{s}_k{k}"] = {"test_children": test, "early_stop_children": val,
                                   "fit_children": sorted(set(train) - set(val)), "agg_source": str(ex["agg_source"]),
                                   "M_o_sha256": hashes[str((stim / f'unit_s{s}_k{k}' / 'models/M_o.pt').relative_to(ROOT))],
                                   "epochs_run": info.get("epochs_run"), "ok": bool(ok)}
        except ProvenanceError as exc:
            scope[f"s{s}_k{k}"] = {"ok": False, "error": str(exc)}
    ck.add("model_scope_all_units", all(v["ok"] for v in scope.values()), [k for k, v in scope.items() if not v["ok"]])
    # main cohort
    kids = src.main_children
    ck.add("main_cohort_count", True, {"n": len(kids), "expected_from_documents": 55, "equal": len(kids) == 55})
    lab = ch[ch.group == "labelled"]
    excluded = {"labelled_total": int(len(lab)), "no_draws": int((~lab.has_draws.astype(bool)).sum()),
                "nonfinite_age": int(sum(1 for c in lab.child if not np.isfinite(src.rec.loc[src.primary(int(c)), "age_months"])))}
    ck.add("main_cohort_exclusions_reported", True, excluded)
    # draws (T5): draw 0 = 80 distinct trials per class, of the right class, within the primary record
    bad = []
    for c in kids:
        r = src.primary(c)
        for cls in (0, 1):
            gi = co.budget_idx(r, 0, cls)
            if len(np.unique(gi)) != 80 or not np.all(co.t_record[gi] == r) or not np.all(co.t_y[gi] == cls):
                bad.append(int(c))
    ck.add("draw0_80_per_class_without_replacement", not bad, bad)
    tech = src.technical(kids)
    ck.add("technical_fields_finite", bool(np.isfinite(tech).all()), int((~np.isfinite(tech)).sum()))
    ck.add("spectra_finite_main", bool(np.isfinite(src.spectral(kids)).all()))
    # round-1 E (H14) equals the PF2 main cohort and the stored H14 errors cover it
    E1 = sorted(co1.ch[(co1.ch.group == "labelled") & (co1.ch.eligible == True)].child.astype(int))   # noqa: E712
    ck.add("round1_E_equals_main_cohort", E1 == kids, {"n_round1": len(E1)})
    h14 = h14_errors(config)
    ck.add("h14_stored_errors_cover_E", set(h14["C"]) == set(E1), {"n": len(h14["C"])})
    # staged epochs, D1 exports and events for the A1 inputs
    st = st_records(config).set_index("record_id")
    stage_bad, d1_bad, ev_missing, n_intervals = [], [], [], []
    for c in kids:
        r = src.primary(c)
        rid = str(src.rec.loc[r, "record_id"])
        sp = stage_path(config, rid)
        if not sp.exists():
            stage_bad.append(rid)
            continue
        with np.load(sp, allow_pickle=False) as z:
            ok = (str(z["lane"]) == "bdf_puretone" and int(z["n_channels"]) == 20 and int(z["pre_samples"]) == 50
                  and int(z["post_samples"]) == 150 and float(z["rate_hz"]) == 250.0 and float(z["record_scale"]) > 0
                  and int(z["accepted"].sum()) == int(src.rec.loc[r, "n_acc"]))
        if not ok:
            stage_bad.append(rid)
        cid = str(st.loc[rid, "_d1_container_id"])
        try:
            meta = d1_meta(config, cid)
            n_intervals.append(len(meta["intervals"]))
            if float(meta["rate_hz"]) != 250.0 or int(meta["n_channels"]) != 20:
                d1_bad.append(rid)
        except FileNotFoundError:
            d1_bad.append(rid)
        if not (ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "events" / f"{rid}.parquet").exists():
            ev_missing.append(rid)
    ck.add("stage_files_match_cohort", not stage_bad, len(stage_bad))
    ck.add("d1_exports_present", not d1_bad, len(d1_bad))
    ck.add("st_events_present", not ev_missing, len(ev_missing))
    # records manifest (private)
    rows = []
    chi = ch.set_index("child")
    for r in co.rec.itertuples():
        rid = str(r.record_id)
        srow = st.loc[rid] if rid in st.index else None
        cid = str(srow["_d1_container_id"]) if srow is not None else ""
        try:
            acq = d1_meta(config, cid).get("candidate_acquisition_id", "") if cid and cid != "nan" else ""
        except FileNotFoundError:
            acq = ""
        child = int(r.child)
        rows.append({"identity_group": r.identity_group, "record_id": rid, "child": child,
                     "primary_record": bool(int(chi.loc[child, "primary_rec"]) == int(r.rec)),
                     "in_main_cohort": child in kids and src.primary(child) == int(r.rec),
                     "source_system": "BDF", "source_group_status": chi.loc[child, "group"],
                     "source_container_id": cid, "physical_acquisition_id": acq, "visit_id": rid,
                     "age_months": r.age_months,
                     "age_source_status": (srow["age_source_status"] if srow is not None else "unknown"),
                     "n_std": int(r.n_std), "n_dev": int(r.n_dev), "has_draws": bool(r.has_draws),
                     "fold_assignment_ref": f"{cfg(config, 'sources.pf_prepare_run')}/folds.json",
                     "encoder_scope_ref": cfg(config, "sources.pf_stim_run"),
                     "epoch_source_ref": f"{cfg(config, 'sources.stage_run')}/epochs/{rid}.npz",
                     "spectral_source_ref": f"features_001:cont[{int(r.rec)}]",
                     "source_conflict": "|".join(str(srow[k]) for k in ("metadata_caution_flags", "source_candidate_ambiguity")
                                                 if srow is not None and isinstance(srow[k], str) and srow[k])})
    man = pd.DataFrame(rows)
    write_csv_atomic(man, run["private"] / "records_manifest.csv", private=True)
    write_json_atomic(run["private"] / "model_scope_manifest.json", scope, private=True)
    status_counts = man[man.in_main_cohort].age_source_status.value_counts().to_dict()
    write_json_atomic(run["private"] / "source_check.json", {"checks": ck.rows, "hashes": hashes}, private=True)
    summary = {"status": "COMPLETED" if not ck.failed else "SOURCE_UNRESOLVED", "failed": ck.failed,
               "checks": [{k: v for k, v in r.items() if k != "detail" or not isinstance(v, list) or len(v) < 6}
                          for r in ck.rows],
               "main_cohort": len(kids), "records": int(len(man)), "age_source_status_main": status_counts,
               "d1_intervals_main": {"min": int(min(n_intervals)), "max": int(max(n_intervals))} if n_intervals else None,
               "gpu_policy": {"allowed": cfg(config, "resources.allowed_gpu_partitions"),
                              "forbidden": cfg(config, "resources.forbidden_gpu")}}
    write_json_atomic(run["public"] / "summary_p0.json", summary, private=False)
    close_run(config, "source_check", args.run, summary["status"])
    return summary


# ====================================================================== plan (deterministic unit table)

def plan_counts(config: dict) -> dict:
    a = config["age"]
    n_units = len(units(config))
    per_view = {}
    for budget, view in age_core.work_list(config):
        if view in age_core.CONSTANT_VIEWS:
            fits = 0
        elif view == "pair_equivalence":
            fits = 1
        else:
            n_alpha = len(a["kernel_alpha"] if view == "spectral_rbf" else a["alpha_sse"])
            fits = n_alpha * int(a["inner_folds"]) + 1
        per_view[f"{budget}/{view}"] = {"units": n_units, "fits_per_unit": fits, "fits": fits * n_units}
    a0 = sum(v["fits"] for v in per_view.values())
    per_unit = len(a["alpha_sse"]) * int(a["inner_folds"]) + 1
    a1_views = ["random_common", "raw_common", "nonaligned_common"]
    a1 = {"views": a1_views, "fits": len(a1_views) * n_units * per_unit,
          "conditional_matched_refit": n_units * per_unit}
    pf1 = round1_cohort(config)[0]
    c0 = len(cfg(pf1, "folds.seeds")) * int(cfg(pf1, "folds.n_outer")) * (len(cfg(pf1, "stats.ordinal_lambda")) * 5 + 1)
    r = config["resources"]
    total_max = a0 + a1["fits"] + a1["conditional_matched_refit"]
    caps = {"small_age_fits": {"planned_max": total_max, "cap": int(r["small_age_fits_max"]), "ok": total_max <= int(r["small_age_fits_max"])},
            "ordinal_optimizer_calls": {"planned": c0, "cap": int(r["ordinal_optimizer_calls_max"]), "ok": c0 <= int(r["ordinal_optimizer_calls_max"])},
            "trained_encoder_inference_units": {"planned": n_units, "cap": int(r["trained_encoder_inference_units_max"]), "ok": n_units <= int(r["trained_encoder_inference_units_max"])},
            "random_encoder_inference_units": {"planned": int(cfg(config, "controls.random_networks")), "cap": int(r["random_encoder_inference_units_max"]),
                                               "ok": int(cfg(config, "controls.random_networks")) <= int(r["random_encoder_inference_units_max"])},
            "new_encoder_fits": {"planned": 0, "cap": int(r["new_encoder_fits_max"]), "ok": True}}
    return {"a0": {"per_view": per_view, "fits": a0}, "a1": a1, "c0_ordinal_calls": c0, "caps": caps}


def cmd_plan(args, config) -> dict:
    out_path = ROOT / cfg(config, "paths.private_relative") / args.run / "plan.json"
    refuse_existing(out_path)
    run = open_run("plan", args.run, config, args=vars(args))
    counts = plan_counts(config)
    if not all(v["ok"] for v in counts["caps"].values()):
        raise ProvenanceError(f"PLAN_EXCEEDS_CAPS:{counts['caps']}")
    p0 = json.loads((ROOT / cfg(config, "paths.private_relative") / args.p0_run / "source_check.json").read_text())
    if any(r["status"] == "FAIL" for r in p0["checks"]):
        raise ProvenanceError("P0_HAS_FAILURES")
    plan = {"config_sha256": config["_sha256"], "protocol_sha256": config.get("_protocol_sha256"),
            "documents": config.get("_document_sha256"), "p0_run": args.p0_run, "source_hashes": p0["hashes"],
            "units": [list(u) for u in units(config)], "a0_work_list": [list(w) for w in age_core.work_list(config)],
            **counts}
    write_json_atomic(out_path, plan, private=True)
    os.chmod(out_path, 0o400)
    write_json_atomic(run["public"] / "summary_plan.json", {k: v for k, v in plan.items() if k != "source_hashes"},
                      private=False)
    close_run(config, "plan", args.run, "COMPLETED")
    return {"caps": counts["caps"], "a0_fits": counts["a0"]["fits"], "a1_fits": counts["a1"]["fits"],
            "c0": counts["c0_ordinal_calls"]}
