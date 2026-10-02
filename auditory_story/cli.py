"""auditory_story command line (02_SERVER_EXECUTION section 12). Every command runs inside Slurm.

  prepare        P0  cohort / target / fold / encoder-scope / cache / block / label-mask checks, task plan
  synthetic      P0  two small synthetic scenarios (direction check of the learning rule; no real data)
  train-profile  P1  30 small summary models (3 seeds x 5 folds x {conditional, pooled}) + label-free outputs
  clinical       P2  SIR matrix (7350 calls), MUSS (600), technical sensitivity (300); PRIOR has no fit
  evaluate       P3  scores, child-level aggregation, bootstrap, E3 / E4 / E5, status
  report             completion summary (schema) and aggregate tables
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

from . import clinical as cl
from . import metrics as mt
from . import profile as prof
from .data import StorySource, inner_folds, label_sets
from .runtime import (ROOT, ProvenanceError, append_jsonl, cfg, close_run, code_hash, digest, hash_ids, load_config,
                      mark_done, open_run, private_dir, require_protocol, require_slurm, results_dir, task_units,
                      unit_done, write_csv_atomic, write_json_atomic, write_parquet_atomic)

PHASES = ("sir", "muss", "sir_technical")


# ====================================================================== P0

def cmd_prepare(args, config) -> dict:
    run = open_run("prepare", args.run, config, args=vars(args))
    priv, pub = run["private"], run["public"]
    src = StorySource(config)
    table = src.main_table()
    checks = []

    def check(name, ok, fatal=True, **detail):
        checks.append({"check": name, "ok": bool(ok), "fatal": bool(fatal), **detail})

    n_exp = int(cfg(config, "cohort.expected_n"))
    check("main_cohort_n_matches_expectation", len(table) == n_exp, fatal=False, actual=len(table), expected=n_exp,
          expected_is_target=False)
    check("targets_complete_sir_1_5_and_muss", (table.target_status == "complete").all(),
          n_incomplete=int((table.target_status != "complete").sum()))
    check("muss_within_scale_range", table.muss_original.between(*cfg(config, "targets.muss_range")).all())
    check("one_primary_visit_per_child", table.child.is_unique and table.record_id.is_unique and table.identity_group.is_unique)
    cross = src.clinical_cross_check(table)
    check("clinical_main_table_cross_check", cross["rows_found"] == len(table) and cross["records_with_multiple_rows"] == 0
          and cross["records_without_row"] == 0 and not any(cross["value_mismatches"].values()), **cross)
    co = src.co
    secondary = int((co.rec[co.rec.child.isin(src.children)].groupby("child").size() > 1).sum())
    gid = dict(zip(table.child, table.identity_group))
    folds, sources, scope_rows = {}, {"encoders": {}, "caches": {}}, []
    for s in src.seeds:
        outer = co.outer(s)
        folds[str(s)] = {str(c): int(outer[c]) for c in src.children}
    for s, k in src.units():
        train, test = src.split(s, k)
        ok = bool(train) and bool(test) and not (set(train) & set(test)) and \
            not ({gid[c] for c in train} & {gid[c] for c in test}) and \
            not ({src.prim[c] for c in train} & {src.prim[c] for c in test})
        check(f"outer_identity_and_acquisition_disjoint_s{s}_k{k}", ok, n_train=len(train), n_test=len(test))
        scope = src.encoder_scope(s, k)
        check(f"encoder_scope_s{s}_k{k}", scope["export_test_equals_fold"] and scope["train_disjoint_test"])
        mo = src.age.stim_dir / f"unit_s{s}_k{k}" / "models" / "M_o.pt"
        cache = src.embedding_path(s, k)
        emb = src.embeddings(s, k)
        gap = src.cache_consistency(s, k, emb)
        check(f"cache_matches_mo_exports_s{s}_k{k}", gap <= 1e-5 and mo.stat().st_mtime < cache.stat().st_mtime,
              draw0_max_abs_gap=gap)
        sources["encoders"][f"s{s}_k{k}"] = digest(mo)
        sources["caches"][f"s{s}_k{k}"] = digest(cache)
        lane_train = set(scope["train_children"])
        grp = co.ch.set_index("child").group
        scope_rows.append({"unit": f"s{s}_k{k}", "encoder_train_children": len(lane_train),
                           "encoder_train_main": len(lane_train & set(src.children)),
                           "encoder_train_by_group": {g: int(sum(1 for c in lane_train if grp.loc[c] == g))
                                                      for g in ("labelled", "nh", "unlabelled")},
                           "auxiliary_pool_main_train": len(train), "outer_test_main": len(test),
                           "outer_test_seen_by_encoder": len(lane_train & set(test)),
                           "inner_validation_eeg_visible_to_profile": True,
                           "inner_validation_targets_visible_to_profile": False})
    tt = src.trial_table
    write_parquet_atomic(tt, priv / "trial_table.parquet")
    sc = src.support_counts()
    write_csv_atomic(sc, priv / "support_counts.csv", private=True)
    check("trial_table_rows_equal_cache_rows", len(tt) == len(src.all_idx), rows=int(len(tt)))
    hist_missing = {c: int(tt[c].isna().sum()) for c in ("h_run", "h_gap", "h_pos")}
    budgets, repeats = cfg(config, "label_budgets.values"), cfg(config, "label_budgets.repeats")
    masks, mask_hashes = {}, {}
    for s, k in src.units():
        train, _ = src.split(s, k)
        sets = label_sets(train, int(cfg(config, "label_budgets.seed")), s, k, budgets, repeats)
        nested = all(set(sets["12"][r]) <= set(sets["24"][r]) for r in range(int(repeats["12"])))
        sizes = all(len(v) == int(b) for b in ("12", "24") for v in sets[b]) and sets["all"][0] == sorted(train)
        again = label_sets(train, int(cfg(config, "label_budgets.seed")), s, k, budgets, repeats)
        check(f"label_sets_s{s}_k{k}", nested and sizes and again == sets)
        masks[f"s{s}_k{k}"] = sets
        mask_hashes[f"s{s}_k{k}"] = {b: [hash_ids(v) for v in vs] for b, vs in sets.items()}
    spec, tech = src.spectral_view(src.children), src.technical(src.children)
    check("technical_view_finite", np.isfinite(tech).all())
    n_units = len(src.units())
    reps = {str(b): int(repeats[str(b)]) for b in budgets}
    calls_per = int(cfg(config, "splits.clinical_inner_folds")) * len(cfg(config, "clinical.lambda_mean_loss")) + 1
    plan = {"small_profile_fits": n_units * len(cfg(config, "profile.arms")),
            "sir_calls": n_units * sum(reps.values()) * len(cfg(config, "clinical.fitted_sir_arms")) * calls_per,
            "muss_calls": n_units * len(cfg(config, "clinical.muss_arms")) * calls_per,
            "technical_calls": n_units * len(cfg(config, "clinical.technical_full_label_arms")) * calls_per,
            "new_raw_backbones": 0, "new_frozen_inference_units": 0}
    plan["clinical_calls"] = plan["sir_calls"] + plan["muss_calls"] + plan["technical_calls"]
    check("plan_within_caps", plan["small_profile_fits"] <= int(cfg(config, "resources.small_profile_fits_max")) and
          plan["clinical_calls"] <= int(cfg(config, "resources.clinical_optimizer_calls_max")), **plan)
    st_paths = [ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs" / f"{r}.npz" for r in table.record_id]
    ev_paths = [ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "events" / f"{r}.parquet" for r in table.record_id]
    import hashlib
    agg = hashlib.sha256("".join(digest(p) for p in st_paths + ev_paths).encode()).hexdigest()
    sources.update({"config_sha256": config["_sha256"], "package": config["_package_sha256"],
                    "package_zip_sha256": digest(ROOT / cfg(config, "project.package_zip")),
                    "clinical_cohort": digest(ROOT / cfg(config, "sources.clinical_cohort")),
                    "spectral": digest(ROOT / cfg(config, "sources.spectral")),
                    "spectral_plus": digest(ROOT / cfg(config, "sources.spectral_plus")),
                    "stage_and_event_files_aggregate": agg, "pf2_prepare_dir": str(cfg(config, "sources.pf_prepare_run")),
                    "base_commit": cfg(config, "project.base_commit"), "code_hash": code_hash()})
    fatal_fail = [c["check"] for c in checks if c["fatal"] and not c["ok"]]
    status = "PASS" if not fatal_fail else "FAIL"
    write_csv_atomic(table, priv / "records.csv", private=True)
    write_json_atomic(priv / "folds.json", folds, private=True)
    write_json_atomic(priv / "label_masks.json", masks, private=True)
    write_json_atomic(priv / "sources.json", sources, private=True)
    write_json_atomic(priv / "exposure.json", scope_rows, private=True)
    write_json_atomic(priv / "checks.json", {"status": status, "checks": checks, "fatal_failures": fatal_fail}, private=True)
    summary = {"status": status, "n_children": int(len(table)), "secondary_visits_not_used": secondary,
               "fatal_failures": fatal_fail, "n_checks": len(checks), "trial_rows": int(len(tt)),
               "trials_per_child_median": float(tt.groupby("child").size().median()),
               "guard_respecting_fraction": float(tt.guard_ok.mean()),
               "episode_eligible_children": int(sc.episode_eligible.sum()),
               "history_missing_rows": hist_missing, "spectral_dim": int(spec.shape[1]),
               "spectral_nonfinite_values": int((~np.isfinite(spec)).sum()), "technical_dim": int(tech.shape[1]),
               "label_set_hashes": mask_hashes, "plan": plan,
               "encoder_scope": [{k: v for k, v in r.items()} for r in scope_rows],
               "cache_max_gap": max(c.get("draw0_max_abs_gap", 0.0) for c in checks)}
    write_json_atomic(pub / "summary_prepare.json", summary, private=False)
    close_run(config, "prepare", args.run, status)
    return {"status": status, "fatal_failures": fatal_fail, "n_children": int(len(table)),
            "episode_eligible": int(sc.episode_eligible.sum()), "plan": plan}


def _require_prepare(config, run: str) -> dict:
    p = private_dir(config, run) / "checks.json"
    if not p.exists() or json.loads(p.read_text())["status"] != "PASS":
        raise ProvenanceError(f"PREPARE_NOT_PASSED:{run}")
    return json.loads(p.read_text())


# ====================================================================== synthetic direction check (P0)

def cmd_synthetic(args, config) -> dict:
    """Scenario 'conditional': child latent shifts responses differently per condition and sets a synthetic target;
    scenario 'background': one child offset shared by both conditions, target independent of it. Both arms trained
    briefly; reports query NLL gains over q0 and the R^2 of the synthetic latent from mu. No real data."""
    import torch
    from . import transform as tf
    run = open_run("synthetic", args.run, config, args=vars(args))
    out = {}
    for scen in ("conditional", "background"):
        rng = np.random.default_rng(20261002 if scen == "conditional" else 20261003)
        n_child, D, n_tr = 40, 8, 160
        g = rng.normal(size=(2, D))
        u = rng.normal(size=(n_child, 2))
        Bm = rng.normal(size=(2, D, 2)) * (np.array([1.0, -1.0])[:, None, None] if scen == "conditional" else 0.0)
        bg = rng.normal(size=(n_child, D)) * (0.0 if scen == "conditional" else 0.8)
        rows = []
        for c in range(n_child):
            for k in (0, 1):
                e = g[k] + (Bm[k] @ u[c] if scen == "conditional" else 0.0) + bg[c] + rng.normal(size=(n_tr, D))
                for i in range(n_tr):
                    rows.append((c, k, i % 2, *e[i]))
        arr = np.array(rows)
        child, cls, group, E = arr[:, 0].astype(int), arr[:, 1].astype(int), arr[:, 2].astype(int), arr[:, 3:].astype(np.float32)
        H = np.zeros((len(E), 3), np.float32)
        tt = pd.DataFrame({"child": child, "cls": cls, "group": group, "guard_ok": True})
        train = list(range(30))
        test = list(range(30, 40))
        tr = np.isin(child, train)
        pop = tf.fit_population(E[tr], H[tr], cls[tr], child[tr])
        cfg_s = json.loads(json.dumps(config))
        cfg_s["profile"]["steps"] = 600
        cfg_s["profile"]["checkpoint_every_steps"] = 100
        res = {}
        for arm in ("conditional", "pooled"):
            model = prof.build_model(pop, cfg_s, arm, 7)
            sampler = prof.EpisodeSampler(prof.cells_of(tt, train), train, 32, 4, 11)
            ck = run["private"] / f"synthetic_{scen}_{arm}.pt"
            if ck.exists():
                ck.unlink()
            info = prof.train_arm(model, E, H, sampler, cfg_s, ck, 13)
            rows_e3 = prof.e3_rows(model, E, H, tt, test, cfg_s, 0, 0, arm)
            S = prof.summaries(model, E, tt, list(range(n_child)))
            Xtr = np.column_stack([S["mu"][train], np.ones(len(train))])        # fit on training children,
            Xte = np.column_stack([S["mu"][test], np.ones(len(test))])          # score held-out children
            r2 = []
            for j in range(2):
                coef, *_ = np.linalg.lstsq(Xtr, u[train, j], rcond=None)
                r2.append(1 - np.mean((u[test, j] - Xte @ coef) ** 2) / np.mean((u[test, j] - u[train, j].mean()) ** 2))
            gains = [r["q0_nll"] - r["model_nll"] for r in rows_e3 if r["supported"]]
            res[arm] = {"query_nll_gain_vs_q0": float(np.mean(gains)), "target_latent_r2_heldout": float(np.mean(r2)),
                        "final_loss": info["final_loss"]}
        out[scen] = res
    write_json_atomic(run["public"] / "summary_synthetic.json", out, private=False)
    close_run(config, "synthetic", args.run, "COMPLETED")
    return out


# ====================================================================== P1

def cmd_train_profile(args, config) -> dict:
    require_protocol(config)
    _require_prepare(config, args.prepare_run)
    prof.install_signal_handlers()
    run = open_run("train_profile", args.run, config, args=vars(args))
    src = StorySource(config)
    sources = json.loads((private_dir(config, args.prepare_run) / "sources.json").read_text())
    done, failed = [], []
    for s, k in task_units(src.units()):
        unit_dir = run["private"] / "representation_models" / f"s{s}_k{k}"
        t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            info = prof.run_unit(src, config, s, k, unit_dir)
        except prof.Preempted as exc:
            close_run(config, "train_profile", args.run, "PREEMPTED_CHECKPOINTED", detail=str(exc))
            sys.exit(75)
        except prof.NumericalFailure as exc:
            write_json_atomic(unit_dir / "FAILED.json", {"error": str(exc)}, private=True)
            failed.append(f"s{s}_k{k}")
            continue
        train, test = src.split(s, k)
        for arm, d in info["arms"].items():
            if d.get("ledgered"):
                continue
            append_jsonl(run["private"] / "fit_ledger.jsonl", {
                "unit_id": f"P1_s{s}_k{k}_{arm}", "arm": arm, "outer_seed": s, "outer_fold": k, "label_budget": None,
                "label_repeat": None, "source_commit": cfg(config, "project.base_commit"), "code_hash": code_hash(),
                "source_encoder_hash": sources["encoders"][f"s{s}_k{k}"], "training_scope_hash": hash_ids(train),
                "source_children_hash": hash_ids(train), "labelled_children_hash": None, "excluded_children_hash": hash_ids(test),
                "optimizer": "Adam", "objective_normalization": "mean_child(mean_class(mean_query(NLL/d_e)))+0.01*mean_child(KL/d_u)",
                "steps_or_iterations": d["steps"], "initial_loss": d["initial_loss"], "final_loss": d["final_loss"],
                "grad_norm": d["final_grad_norm"], "model_training_mode": "train_during_fit_eval_for_outputs",
                "selected_lambda": None, "convergence_status": "fixed_step_3000", "probability_floor_count": None,
                "start_time": t0, "end_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "attempt": int(os.environ.get("SLURM_RESTART_COUNT", "0")),
                "status": "COMPLETED", "resumed_from_step": d["resumed_from"]})
            mark_done(unit_dir / arm / "DONE.json", {**d, "ledgered": True})
        done.append(f"s{s}_k{k}")
    status = "COMPLETED" if not failed else "PARTIAL_NUMERICAL_FAILURE"
    close_run(config, "train_profile", args.run, status, units=len(done), failed=failed)
    return {"units": done, "failed": failed}


def _profile_status(config, run: str, src) -> dict:
    base = private_dir(config, run) / "representation_models"
    out = {}
    for s, k in src.units():
        for arm in cfg(config, "profile.arms"):
            out[f"s{s}_k{k}_{arm}"] = (base / f"s{s}_k{k}" / arm / "DONE.json").exists()
    return out


# ====================================================================== P2

def _views(config, profile_run: str, src, s: int, k: int, spec, tech) -> tuple[dict, dict]:
    d = private_dir(config, profile_run) / "representation_models" / f"s{s}_k{k}"
    with np.load(d / "transforms.npz", allow_pickle=False) as z:
        if list(z["children"]) != src.children:
            raise ProvenanceError("TRANSFORM_CHILD_ORDER")
        cm, split, mean8 = z["class_means"], z["split_class_means"], z["mean8"]
    S = {}
    for arm in ("conditional", "pooled"):
        with np.load(d / arm / "summaries.npz", allow_pickle=False) as z:
            if list(z["children"]) != src.children:
                raise ProvenanceError("SUMMARY_CHILD_ORDER")
            S[arm] = (z["mu"], z["mu_split"])
    n = len(src.children)
    mean = cm.reshape(n, -1)
    srp, pool = S["conditional"][0], S["pooled"][0]
    views = {"C": None, "C_MEAN": mean, "C_MEAN8": mean8, "C_SPEC": spec, "C_POOL": pool, "C_SRP": srp, "SRP_ONLY": srp,
             "C_TECH": tech, "C_TECH_SRP": np.concatenate([tech, srp], 1)}
    halves = {"C_MEAN": (split[:, 0].reshape(n, -1), split[:, 1].reshape(n, -1)),
              "C_SRP": (S["conditional"][1][:, 0], S["conditional"][1][:, 1])}
    return views, halves


def cmd_clinical(args, config) -> dict:
    require_protocol(config)
    _require_prepare(config, args.prepare_run)
    run = open_run("clinical", args.run, config, args=vars(args))
    src = StorySource(config)
    status = _profile_status(config, args.profile_run, src)
    missing = sorted(k for k, v in status.items() if not v)
    table = pd.read_csv(private_dir(config, args.prepare_run) / "records.csv").set_index("child")
    if list(table.index) != src.children:
        raise ProvenanceError("RECORDS_CHILD_ORDER")
    masks = json.loads((private_dir(config, args.prepare_run) / "label_masks.json").read_text())
    sources = json.loads((private_dir(config, args.prepare_run) / "sources.json").read_text())
    pos = {c: i for i, c in enumerate(src.children)}
    clin = cl.clinical_matrix(table.age_months.to_numpy(), table.device_months.to_numpy())
    y_sir, y_muss = table.sir_ordinal.to_numpy(float), table.muss_original.to_numpy(float)
    spec, tech = src.spectral_view(src.children), src.technical(src.children)
    cap = int(cfg(config, "resources.clinical_optimizer_calls_max"))
    n_inner = int(cfg(config, "splits.clinical_inner_folds"))
    udir = run["private"] / "clinical_units"
    tasks = []
    for s, k in src.units():
        unit = f"s{s}_k{k}"
        for b, sets in masks[unit].items():
            for r, L in enumerate(sets):
                for arm in cfg(config, "clinical.sir_arms"):
                    tasks.append(("sir", s, k, b, r, arm))
        for arm in cfg(config, "clinical.muss_arms"):
            tasks.append(("muss", s, k, "all", 0, arm))
        for arm in cfg(config, "clinical.technical_full_label_arms"):
            tasks.append(("sir_technical", s, k, "all", 0, arm))
    calls_used = sum(len(json.loads(p.read_text()).get("calls", [])) for p in udir.glob("*.json")) if udir.exists() else 0
    view_cache, ran, blocked = {}, 0, []
    for phase, s, k, b, r, arm in task_units(tasks):
        key = f"{phase}_s{s}_k{k}_b{b}_r{r}_{arm}"
        path = udir / f"{key}.json"
        if path.exists():
            continue
        need_profile = arm in ("C_MEAN", "C_MEAN8", "C_POOL", "C_SRP", "SRP_ONLY", "C_TECH_SRP")
        if need_profile and any(not status[f"s{s}_k{k}_{a}"] for a in cfg(config, "profile.arms")):
            blocked.append(key)
            continue
        if (s, k) not in view_cache:
            view_cache = {(s, k): _views(config, args.profile_run, src, s, k, spec, tech)}
        views, halves = view_cache[(s, k)]
        train, test = src.split(s, k)
        L = masks[f"s{s}_k{k}"][b][r]
        if not set(L) <= set(train):
            raise ProvenanceError(f"LABEL_SET_OUTSIDE_TRAIN:{key}")
        Li, Ti = np.array([pos[c] for c in L]), np.array([pos[c] for c in test])
        y = (y_sir if phase != "muss" else y_muss)
        t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
        rec = {"key": key, "phase": phase, "seed": s, "fold": k, "budget": b, "repeat": r, "arm": arm,
               "labelled_children": L, "test_children": test, "labelled_hash": hash_ids(L), "test_hash": hash_ids(test),
               "train_hash": hash_ids(train)}
        if arm == "PRIOR":
            P = np.tile(cl.prior_probabilities(y[Li], float(cfg(config, "clinical.prior_pseudocount_per_class"))), (len(Ti), 1))
            rec.update(proba=P.tolist(), calls=[], lambda_=None)
        else:
            if calls_used + n_inner * len(cfg(config, "clinical.lambda_mean_loss")) + 1 > cap:
                blocked.append(key)
                continue
            fo = inner_folds(L, n_inner, int(cfg(config, "splits.inner_fold_seed")), s, k, b, r)
            folds_L = np.array([fo[c] for c in L])
            view = views[arm]
            cmat = clin if arm != "SRP_ONLY" else np.zeros((len(src.children), 0))
            extra = {}
            if b == "all" and phase == "sir" and arm in halves:
                A, B = halves[arm]
                ok = [i for i in Ti if np.isfinite(A[i]).all() and np.isfinite(B[i]).all()]
                if ok:
                    ok = np.array(ok)
                    extra = {"half_A": (cmat[ok], A[ok]), "half_B": (cmat[ok], B[ok])}
                    rec["half_children"] = [src.children[i] for i in ok]
            res = cl.fit_head("sir" if phase != "muss" else "muss", cmat[Li], None if view is None else view[Li], y[Li],
                              folds_L, cmat[Ti], None if view is None else view[Ti], config, extra_tests=extra)
            calls_used += len(res["calls"])
            rec.update(lambda_=res["lambda"], inner_scores=res["inner_scores"], n_features=res["n_features"],
                       linear_fallbacks=res["linear_fallbacks"], imputed_fit_values=res["imputed_fit_values"], calls=res["calls"],
                       extra={n: v.tolist() for n, v in res["extra"].items()})
            if phase == "muss":
                rec.update(pred=res["pred"].tolist(), pred_raw=res["pred_raw"].tolist())
            else:
                rec.update(proba=res["proba"].tolist(), thresholds=res["thresholds"], train_level_counts=res["train_level_counts"])
        rec.update(start_time=t0, end_time=time.strftime("%Y-%m-%dT%H:%M:%S"), slurm_job_id=os.environ.get("SLURM_JOB_ID"),
                   attempt=int(os.environ.get("SLURM_RESTART_COUNT", "0")), code_hash=code_hash(),
                   source_encoder_hash=sources["encoders"][f"s{s}_k{k}"])
        write_json_atomic(path, rec, private=True)
        ran += 1
    close_run(config, "clinical", args.run, "TASKS_DONE", ran=ran, blocked=len(blocked))
    return {"tasks_total": len(tasks), "ran_now": ran, "blocked": blocked[:20], "n_blocked": len(blocked),
            "profile_missing": missing, "calls_used": calls_used}


def cmd_consolidate(args, config) -> dict:
    """Collect clinical task files into predictions_sir / predictions_muss and the per-call fit ledger."""
    run = open_run("consolidate", args.run, config, args=vars(args))
    src = StorySource(config)
    table = pd.read_csv(private_dir(config, args.prepare_run) / "records.csv").set_index("child")
    udir = private_dir(config, args.clinical_run) / "clinical_units"
    floor = float(cfg(config, "evaluation.probability_floor"))
    sir_rows, muss_rows, half_rows, n_calls, n_conv, n_tasks = [], [], [], 0, 0, 0
    ledger = run["private"] / "fit_ledger.jsonl"
    if ledger.exists():
        ledger.unlink()
    for p in sorted(udir.glob("*.json")):
        rec = json.loads(p.read_text())
        n_tasks += 1
        base = {"phase": rec["phase"], "seed": rec["seed"], "fold": rec["fold"], "budget": rec["budget"],
                "repeat": rec["repeat"], "arm": rec["arm"], "lambda": rec.get("lambda_")}
        if rec["phase"] == "muss":
            for c, v, vr in zip(rec["test_children"], rec["pred"], rec["pred_raw"]):
                muss_rows.append({**base, "child": c, "pred": v, "pred_raw": vr, "y": float(table.loc[c, "muss_original"])})
        else:
            for c, pr in zip(rec["test_children"], rec["proba"]):
                sir_rows.append({**base, "child": c, **{f"p{j + 1}": pr[j] for j in range(5)}, "y": int(table.loc[c, "sir_ordinal"])})
            for name, P in rec.get("extra", {}).items():
                for c, pr in zip(rec["half_children"], P):
                    half_rows.append({**base, "half": name, "child": c, **{f"p{j + 1}": pr[j] for j in range(5)},
                                      "y": int(table.loc[c, "sir_ordinal"])})
        for i, call in enumerate(rec.get("calls", [])):
            n_calls += 1
            n_conv += int(bool(call.get("converged")))
            floor_count = None
            if call["stage"] == "final" and rec["phase"] != "muss":
                floor_count = int((np.asarray(rec["proba"]) < floor).sum())
            append_jsonl(ledger, {"unit_id": f"{rec['key']}_c{i}", "arm": rec["arm"], "outer_seed": rec["seed"],
                                  "outer_fold": rec["fold"], "label_budget": rec["budget"], "label_repeat": rec["repeat"],
                                  "source_commit": cfg(config, "project.base_commit"), "code_hash": rec["code_hash"],
                                  "source_encoder_hash": rec["source_encoder_hash"], "training_scope_hash": rec["train_hash"],
                                  "source_children_hash": rec["train_hash"], "labelled_children_hash": rec["labelled_hash"],
                                  "excluded_children_hash": rec["test_hash"],
                                  "optimizer": "closed_form_ridge" if call.get("closed_form") else "L-BFGS-B",
                                  "objective_normalization": "mean_squared_error+lam||w||^2" if call.get("closed_form") else
                                  "mean_nll+lam/2||w||^2+0.001/2||t-logit(k/5)||^2",
                                  "steps_or_iterations": call.get("nit"), "initial_loss": call.get("initial_objective"),
                                  "final_loss": call.get("final_objective"), "grad_norm": call.get("grad_norm"),
                                  "model_training_mode": None, "selected_lambda": call["lambda"], "stage": call["stage"],
                                  "inner_fold": call["fold"], "convergence_status": "converged" if call.get("converged") else
                                  f"not_converged:{call.get('message', '')}", "probability_floor_count": floor_count,
                                  "start_time": rec["start_time"], "end_time": rec["end_time"], "slurm_job_id": rec["slurm_job_id"],
                                  "attempt": rec["attempt"], "status": "COMPLETED"})
    write_parquet_atomic(pd.DataFrame(sir_rows), run["private"] / "predictions_sir.parquet")
    write_parquet_atomic(pd.DataFrame(muss_rows), run["private"] / "predictions_muss.parquet")
    write_parquet_atomic(pd.DataFrame(half_rows), run["private"] / "predictions_sir_halves.parquet")
    out = {"tasks": n_tasks, "optimizer_calls": n_calls, "converged_calls": n_conv, "sir_rows": len(sir_rows),
           "muss_rows": len(muss_rows), "half_rows": len(half_rows)}
    write_json_atomic(run["public"] / "summary_consolidate.json", out, private=False)
    close_run(config, "consolidate", args.run, "COMPLETED", **out)
    return out


# ====================================================================== P3

def _sir_scores(frame: pd.DataFrame, floor: float) -> pd.DataFrame:
    P = frame[[f"p{j}" for j in range(1, 6)]].to_numpy(float)
    sc = mt.score_sir(P, frame.y.to_numpy(), floor=floor)
    out = frame.copy()
    for k, v in sc.items():
        out[k] = v
    return out


def cmd_evaluate(args, config) -> dict:
    require_protocol(config)
    run = open_run("evaluate", args.run, config, args=vars(args))
    src = StorySource(config)
    cdir = private_dir(config, args.consolidate_run)
    floor = float(cfg(config, "evaluation.probability_floor"))
    B, bseed = int(cfg(config, "evaluation.bootstrap_children")), int(cfg(config, "evaluation.bootstrap_seed"))
    S = _sir_scores(pd.read_parquet(cdir / "predictions_sir.parquet"), floor)
    kids = src.children
    n_units = len(src.units())
    reps = {str(b): int(v) for b, v in cfg(config, "label_budgets.repeats").items()}
    expected_rows = {b: n_units * reps[b] for b in reps}
    out = {"cohort_n": len(kids), "sir": {}, "completeness": {}}

    def per_child(frame, value):
        g = frame.groupby("child")[value].mean()
        return g.reindex(kids).to_numpy(float)

    sir = S[S.phase == "sir"]
    arms = list(cfg(config, "clinical.sir_arms"))
    child_vals = {}
    for b in ("12", "24", "all"):
        for arm in arms:
            f = sir[(sir.budget == b) & (sir.arm == arm)]
            n_pred = f.groupby("child").size().reindex(kids).fillna(0).to_numpy()
            complete = bool((n_pred == len(src.seeds) * reps[b]).all())
            out["completeness"][f"{b}/{arm}"] = {"complete": complete, "rows": int(len(f)),
                                                 "expected_rows": int(len(kids) * len(src.seeds) * reps[b])}
            if not complete:
                continue
            for m in ("rps", "nll_bits", "brier", "expected_mae"):
                child_vals[(b, arm, m)] = per_child(f, m)
            aucs = [mt.auc(g.p_gt3.to_numpy(), g.y.to_numpy() > 3) for _, g in f.groupby(["seed", "repeat"])]
            out["sir"][f"{b}/{arm}"] = {m: float(np.mean(child_vals[(b, arm, m)])) for m in ("rps", "nll_bits", "brier", "expected_mae")}
            out["sir"][f"{b}/{arm}"]["auc_sir_gt3_mean"] = float(np.nanmean(aucs))
            out["sir"][f"{b}/{arm}"]["auc_sir_gt3_by_seed_repeat"] = [float(a) for a in aucs]
            out["sir"][f"{b}/{arm}"]["floored_probabilities"] = int(f.floored.sum())
            for fl in cfg(config, "evaluation.rescore_floors"):
                re = mt.score_sir(f[[f"p{j}" for j in range(1, 6)]].to_numpy(float), f.y.to_numpy(), floor=float(fl))
                out["sir"][f"{b}/{arm}"][f"nll_bits_floor_{fl:g}"] = float(
                    pd.Series(re["nll_bits"], index=f.child.to_numpy()).groupby(level=0).mean().reindex(kids).mean())
    low = {}
    for arm in arms:
        if ("12", arm, "rps") in child_vals and ("24", arm, "rps") in child_vals:
            for m in ("rps", "nll_bits", "brier", "expected_mae"):
                low[(arm, m)] = 0.5 * (child_vals[("12", arm, m)] + child_vals[("24", arm, m)])
            out["sir"][f"low/{arm}"] = {m: float(low[(arm, m)].mean()) for m in ("rps", "nll_bits", "brier", "expected_mae")}
    # contrasts: positive = second-named model (C_SRP unless stated) has lower risk
    contrasts, pvals = {}, {}

    def contrast(name, a, b_, vec_a, vec_b):
        r = mt.bootstrap(vec_a - vec_b, B, bseed)
        r.update(first=a, second=b_)
        contrasts[name] = r
        return r

    if ("C", "rps") in low and ("C_SRP", "rps") in low and ("C_MEAN", "rps") in low:
        pvals["C_minus_C_SRP"] = contrast("low/C_minus_C_SRP", "C", "C_SRP", low[("C", "rps")], low[("C_SRP", "rps")])["p_boot_two_sided"]
        pvals["C_MEAN_minus_C_SRP"] = contrast("low/C_MEAN_minus_C_SRP", "C_MEAN", "C_SRP", low[("C_MEAN", "rps")],
                                               low[("C_SRP", "rps")])["p_boot_two_sided"]
    holm = mt.holm(pvals) if pvals else {}
    for name, (a, b_) in {"C_POOL_minus_C_SRP": ("C_POOL", "C_SRP"), "C_SPEC_minus_C_SRP": ("C_SPEC", "C_SRP"),
                          "C_MEAN8_minus_C_SRP": ("C_MEAN8", "C_SRP"), "PRIOR_minus_C": ("PRIOR", "C"),
                          "C_minus_C_MEAN": ("C", "C_MEAN"), "C_minus_C_SPEC": ("C", "C_SPEC"), "C_minus_C_POOL": ("C", "C_POOL"),
                          "C_minus_C_MEAN8": ("C", "C_MEAN8"), "PRIOR_minus_SRP_ONLY": ("PRIOR", "SRP_ONLY")}.items():
        if (a, "rps") in low and (b_, "rps") in low:
            contrast(f"low/{name}", a, b_, low[(a, "rps")], low[(b_, "rps")])
    for b in ("12", "24", "all"):
        for a, b_ in (("C", "C_SRP"), ("C_MEAN", "C_SRP"), ("C_POOL", "C_SRP"), ("C_SPEC", "C_SRP"), ("PRIOR", "C"),
                      ("C", "C_MEAN"), ("C", "C_SPEC")):
            if (b, a, "rps") in child_vals and (b, b_, "rps") in child_vals:
                contrast(f"{b}/{a}_minus_{b_}", a, b_, child_vals[(b, a, "rps")], child_vals[(b, b_, "rps")])
    # per-level losses (explanation, not stratified selection)
    levels = {}
    for b in ("low", "all"):
        for arm in arms:
            key = (arm, "rps")
            vec = low.get(key) if b == "low" else child_vals.get(("all", arm, "rps"))
            if vec is None:
                continue
            y = pd.read_csv(private_dir(config, args.prepare_run) / "records.csv").set_index("child").loc[kids, "sir_ordinal"].to_numpy()
            levels[f"{b}/{arm}"] = {str(int(l)): {"n": int((y == l).sum()), "rps": float(vec[y == l].mean()) if (y == l).any() else None}
                                    for l in (1, 2, 3, 4, 5)}
    out["sir_by_level"] = levels
    # E4: technical sensitivity at the full label budget
    tech = S[S.phase == "sir_technical"]
    e4 = {}
    for arm in cfg(config, "clinical.technical_full_label_arms"):
        f = tech[tech.arm == arm]
        if len(f) == len(kids) * len(src.seeds):
            child_vals[("all", arm, "rps")] = per_child(f, "rps")
            e4[arm] = {"rps": float(child_vals[("all", arm, "rps")].mean()), "nll_bits": float(per_child(f, "nll_bits").mean())}
    if all(("all", a, "rps") in child_vals for a in ("C_TECH", "C_TECH_SRP")):
        e4["C_TECH_minus_C_TECH_SRP"] = mt.bootstrap(child_vals[("all", "C_TECH", "rps")] - child_vals[("all", "C_TECH_SRP", "rps")], B, bseed)
        if ("all", "C", "rps") in child_vals:
            e4["C_minus_C_TECH"] = mt.bootstrap(child_vals[("all", "C", "rps")] - child_vals[("all", "C_TECH", "rps")], B, bseed)
    out["e4_technical"] = e4
    # E2: MUSS
    M = pd.read_parquet(cdir / "predictions_muss.parquet")
    e2, mvec = {}, {}
    for arm in cfg(config, "clinical.muss_arms"):
        f = M[M.arm == arm].copy()
        if len(f) != len(kids) * len(src.seeds):
            continue
        f["ae"], f["se"], f["ae_raw"] = (f.pred - f.y).abs(), (f.pred - f.y) ** 2, (f.pred_raw - f.y).abs()
        mvec[arm] = per_child(f, "ae")
        e2[arm] = {"mae": float(mvec[arm].mean()), "rmse": float(np.sqrt(per_child(f, "se").mean())),
                   "mae_unclipped": float(per_child(f, "ae_raw").mean()),
                   "clipped_predictions": int((f.pred != f.pred_raw).sum())}
    ymuss = pd.read_csv(private_dir(config, args.prepare_run) / "records.csv").set_index("child").loc[kids, "muss_original"]
    e2["at_scale_maximum"] = int((ymuss >= float(cfg(config, "targets.muss_range")[1])).sum())
    for a in ("C", "C_MEAN", "C_SPEC"):
        if a in mvec and "C_SRP" in mvec:
            e2[f"{a}_minus_C_SRP_mae"] = mt.bootstrap(mvec[a] - mvec["C_SRP"], B, bseed)
    out["e2_muss"] = e2
    # E3: held-out cross-block response prediction (P1 outputs; no clinical value)
    pdir = private_dir(config, args.profile_run) / "representation_models"
    frames = []
    for s, k in src.units():
        for arm in cfg(config, "profile.arms"):
            p = pdir / f"s{s}_k{k}" / arm / "e3.parquet"
            if p.exists():
                f = pd.read_parquet(p)
                f["seed"], f["fold"] = s, k
                frames.append(f)
    e3 = {}
    if frames:
        F = pd.concat(frames, ignore_index=True)
        F = F[F.supported.astype(bool)]
        piv = F.pivot_table(index=["seed", "fold", "child", "direction"], columns="arm",
                            values=["model_nll", "q0_nll", "model_mse", "q0_mse", "model_z2", "q0_z2"])
        cond, pool = piv[("model_nll", "conditional")], piv[("model_nll", "pooled")]
        q0 = piv[("q0_nll", "conditional")]
        g = pd.DataFrame({"q0_minus_cond": q0 - cond, "q0_minus_pooled": q0 - pool, "pooled_minus_cond": pool - cond}).dropna()
        gc = g.groupby(level="child").mean()
        for col in gc.columns:
            e3[col] = mt.bootstrap(gc[col].to_numpy(), B, bseed)
        e3["children_supported"] = int(len(gc))
        e3["children_unsupported"] = int(len(set(kids) - set(gc.index)))
        e3["rows"] = int(len(g))
        for m in ("mse", "z2"):
            e3[f"{m}_means"] = {"q0": float(piv[(f"q0_{m}", "conditional")].mean()),
                                "pooled": float(piv[(f"model_{m}", "pooled")].mean()),
                                "conditional": float(piv[(f"model_{m}", "conditional")].mean())}
        if "swapped_nll" in F.columns:
            fc = F[F.arm == "conditional"]
            e3["swapped_support_nll_increase"] = mt.bootstrap(
                (fc.swapped_nll - fc.model_nll).groupby(fc.child).mean().to_numpy(), B, bseed)
            e3["swap_mu_shift_mean"] = float(fc.swap_mu_shift.mean())
    out["e3_response"] = e3
    # E5: same-record split-half input sensitivity with the frozen full-label heads (no new fits)
    Hh = pd.read_parquet(cdir / "predictions_sir_halves.parquet")
    e5 = {}
    if len(Hh):
        full = sir[sir.budget == "all"].set_index(["seed", "fold", "arm", "child"])
        for arm in ("C_MEAN", "C_SRP"):
            f = Hh[Hh.arm == arm]
            a = _sir_scores(f[f.half == "half_A"], floor).set_index(["seed", "fold", "child"])
            bb = _sir_scores(f[f.half == "half_B"], floor).set_index(["seed", "fold", "child"])
            idx = a.index.intersection(bb.index)
            ea = a.loc[idx, [f"p{j}" for j in range(1, 6)]].to_numpy() @ np.arange(1, 6)
            eb = bb.loc[idx, [f"p{j}" for j in range(1, 6)]].to_numpy() @ np.arange(1, 6)
            fr = full.xs(arm, level="arm").loc[idx]
            ef = fr[[f"p{j}" for j in range(1, 6)]].to_numpy() @ np.arange(1, 6)
            e5[arm] = {"rows": int(len(idx)), "children": int(len(set(i[2] for i in idx))),
                       "mean_abs_expected_score_diff_halves": float(np.mean(np.abs(ea - eb))),
                       "mean_abs_expected_score_diff_half_vs_full": float(np.mean(np.abs(np.r_[ea, eb] - np.r_[ef, ef]))),
                       "rps_half_mean": float(np.r_[a.loc[idx, "rps"], bb.loc[idx, "rps"]].mean()),
                       "rps_full_mean_same_rows": float(fr.rps.mean()) if "rps" in fr else None,
                       "argmax_disagreement_halves": float(np.mean(
                           a.loc[idx, [f"p{j}" for j in range(1, 6)]].to_numpy().argmax(1) !=
                           bb.loc[idx, [f"p{j}" for j in range(1, 6)]].to_numpy().argmax(1)))}
    out["e5_split_half"] = e5
    out["contrasts"] = contrasts
    out["primary"] = {"low_C_minus_C_SRP": contrasts.get("low/C_minus_C_SRP"),
                      "low_C_MEAN_minus_C_SRP": contrasts.get("low/C_MEAN_minus_C_SRP"), "holm_adjusted_p": holm,
                      "sign": "positive = C_SRP lower RPS (better)"}
    out["status"] = classify(out, config)
    write_json_atomic(run["public"] / "aggregate_metrics.json", {k: v for k, v in out.items() if k != "primary"}, private=False)
    write_json_atomic(run["public"] / "primary_contrasts.json", {"primary": out["primary"], "status": out["status"],
                                                                 "strong_spectral": contrasts.get("low/C_SPEC_minus_C_SRP"),
                                                                 "pooled": contrasts.get("low/C_POOL_minus_C_SRP")}, private=False)
    close_run(config, "evaluate", args.run, out["status"]["primary_status"])
    return {"status": out["status"], "primary": out["primary"]}


def classify(out: dict, config: dict) -> dict:
    """Frozen status rule (docs/auditory_story/PROTOCOL.md section 9)."""
    comp = out["completeness"]
    mandatory_ok = all(v["complete"] for k, v in comp.items())
    e3 = out.get("e3_response", {})
    pr = out["primary"]
    a, m = pr.get("low_C_minus_C_SRP"), pr.get("low_C_MEAN_minus_C_SRP")
    flags = {}
    if not mandatory_ok or a is None or m is None:
        return {"primary_status": "TECHNICAL_FAILURE/SUPPORT_LIMITED", "flags": {"incomplete": [k for k, v in comp.items() if not v["complete"]]}}
    holm = pr["holm_adjusted_p"]
    sup_a = a["estimate"] > 0 and holm["C_minus_C_SRP"] < 0.05
    sup_m = m["estimate"] > 0 and holm["C_MEAN_minus_C_SRP"] < 0.05
    spec_ok = out["sir"]["low/C_SRP"]["rps"] <= out["sir"]["low/C_SPEC"]["rps"]
    aux = bool(e3) and e3.get("q0_minus_cond", {}).get("ci_low", -1) > 0
    gain_c = out["sir"]["low/PRIOR"]["rps"] - out["sir"]["low/C"]["rps"]
    delta = float(cfg(config, "evaluation.small_effect_fraction_of_C_gain_over_PRIOR")) * max(gain_c, 0.0)
    wide = any(c["ci_low"] < -delta and c["ci_high"] > delta for c in (a, m))
    flags.update({"clinical_contrast_supported": sup_a, "method_contrast_supported": sup_m, "c_srp_not_worse_than_c_spec": spec_ok,
                  "auxiliary_query_gain_supported": aux, "small_effect_delta_rps": delta, "wide_interval": wide})
    if sup_a and sup_m and spec_ok:
        status = "FUNCTIONAL_GAIN_SUPPORTED_WITHIN_SCOPE"
    elif sup_m and not sup_a:
        status = "METHOD_GAIN_WITHOUT_CLINICAL_INCREMENT"
    elif aux and not (sup_a or sup_m):
        status = "AUXILIARY_ONLY"
    elif wide:
        status = "LOW_PRECISION"
    else:
        status = "NO_ESTABLISHED_GAIN"
    if status == "AUXILIARY_ONLY" and wide:
        flags["also_low_precision"] = True
    return {"primary_status": status, "flags": flags}


def cmd_report(args, config) -> dict:
    run = open_run("report", args.run, config, args=vars(args))
    ev = results_dir(config, args.evaluate_run)
    agg = json.loads((ev / "aggregate_metrics.json").read_text())
    prim = json.loads((ev / "primary_contrasts.json").read_text())
    cons = json.loads((results_dir(config, args.consolidate_run) / "summary_consolidate.json").read_text())
    prof_status = _profile_status(config, args.profile_run, StorySource(config))
    completed = all(v["complete"] for v in agg["completeness"].values()) and all(prof_status.values())
    summary = {"status": "COMPLETED" if completed else "PARTIAL", "base_commit": cfg(config, "project.base_commit"),
               "actual_cohort_n": agg["cohort_n"], "primary_target": "sir_ordinal_1_5",
               "metrics": {"sir": agg["sir"], "primary": prim["primary"], "story_status": prim["status"]},
               "fit_counts": {"small_profile_fits": int(sum(prof_status.values())), "small_profile_fits_cap": 30,
                              "clinical_optimizer_calls": cons["optimizer_calls"], "clinical_optimizer_calls_cap": 9000,
                              "converged_calls": cons["converged_calls"], "new_frozen_inference_units": 0,
                              "new_raw_eeg_backbones": 0},
               "limitations": ["internal validation on a repeatedly explored cohort; not independent clinical replication",
                               "fixed-OOF bootstrap intervals; development-path uncertainty not covered",
                               "archived SIR/MUSS ratings; questionnaire dates, scale row versions and device settings unknown",
                               "record-level representation; no cross-day or biomarker claim"],
               "independent_clinical_validation": False}
    write_json_atomic(run["public"] / "completion_summary.json", summary, private=False)
    close_run(config, "report", args.run, summary["status"])
    return {"status": summary["status"], "story_status": prim["status"]["primary_status"]}


# ====================================================================== post hoc descriptive (addendum 001; no fits)

def cmd_posthoc(args, config) -> dict:
    """Written after the primary results (PROTOCOL_ADDENDUM_001.md): split-half reliability of the clinical summaries
    and selected-lambda / fallback counts of the clinical heads, read from saved outputs only."""
    run = open_run("posthoc", args.run, config, args=vars(args))
    src = StorySource(config)
    base = private_dir(config, args.profile_run) / "representation_models"
    rel = {"conditional": [], "pooled": [], "class_means": []}
    for s, k in src.units():
        d = base / f"s{s}_k{k}"
        for arm in ("conditional", "pooled"):
            with np.load(d / arm / "summaries.npz", allow_pickle=False) as z:
                ms = z["mu_split"]
            ok = np.isfinite(ms).all(axis=(1, 2))
            a, b = ms[ok, 0], ms[ok, 1]
            rs = [np.corrcoef(a[:, j], b[:, j])[0, 1] for j in range(a.shape[1]) if a[:, j].std() > 1e-9 and b[:, j].std() > 1e-9]
            rel[arm].append(float(np.mean(rs)))
        with np.load(d / "transforms.npz", allow_pickle=False) as z:
            sc = z["split_class_means"]
        flat = sc.reshape(sc.shape[0], 2, -1)
        ok = np.isfinite(flat).all(axis=(1, 2))
        a, b = flat[ok, 0], flat[ok, 1]
        rel["class_means"].append(float(np.mean([np.corrcoef(a[:, j], b[:, j])[0, 1] for j in range(a.shape[1])])))
    lam, fb = {}, {}
    for p in sorted((private_dir(config, args.clinical_run) / "clinical_units").glob("*.json")):
        r = json.loads(p.read_text())
        if r["arm"] == "PRIOR":
            continue
        key = f"{r['phase']}/{r['budget']}/{r['arm']}"
        lam.setdefault(key, {}).setdefault(str(r["lambda_"]), 0)
        lam[key][str(r["lambda_"])] += 1
        fb[key] = fb.get(key, 0) + int(r.get("linear_fallbacks", 0))
    out = {"split_half_mean_r_across_children": {k: {"mean_over_units": float(np.mean(v)), "min": float(np.min(v)),
                                                     "max": float(np.max(v))} for k, v in rel.items()},
           "selected_lambda_counts": lam, "linear_fallback_variables": fb, "fits": 0, "post_hoc_descriptive": True}
    write_json_atomic(run["public"] / "summary_posthoc.json", out, private=False)
    close_run(config, "posthoc", args.run, "COMPLETED")
    return out


# ====================================================================== entry

def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="auditory_story")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "synthetic", "train-profile", "clinical", "consolidate", "evaluate", "report", "posthoc"):
        s = sub.add_parser(name)
        s.add_argument("--config", default="configs/auditory_story_v1.yaml")
        s.add_argument("--run", required=True)
        s.add_argument("--prepare-run", default="story_p0_001")
        s.add_argument("--profile-run", default="story_p1_001")
        s.add_argument("--clinical-run", default="story_p2_001")
        s.add_argument("--consolidate-run", default="story_p2c_001")
        s.add_argument("--evaluate-run", default="story_p3_001")
    args = p.parse_args(argv)
    require_slurm()
    config = load_config(args.config)
    fn = {"prepare": cmd_prepare, "synthetic": cmd_synthetic, "train-profile": cmd_train_profile, "clinical": cmd_clinical,
          "consolidate": cmd_consolidate, "evaluate": cmd_evaluate, "report": cmd_report, "posthoc": cmd_posthoc}[args.cmd]
    out = fn(args, config)
    print(json.dumps(out, indent=1, default=str)[:20000], flush=True)


if __name__ == "__main__":
    main()
