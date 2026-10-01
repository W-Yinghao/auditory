"""Final aggregation (execution spec section 15): reads saved summaries / unit outputs only and never fits.

Writes results/<run>/summary.json (aggregates only) and a few descriptive extras computed from saved predictions:
C0 AUC by score type (latent vs raw vs floored probabilities, with tie counts) and the A0/A1 view table.
"""
from __future__ import annotations

import json

import numpy as np

from auditory_pf import stats as st

from .runtime import ROOT, cfg, close_run, open_run, write_json_atomic

RUNS = {"p0": ("p0_001", "summary_p0.json"), "plan": ("plan_001", "summary_plan.json"),
        "synthetic": ("synthetic_001", "summary_synthetic.json"), "a0": ("a0_001", "summary_a0.json"),
        "a1_prep": ("a1_prep_001", "summary_controls_prep.json"), "a1_infer": ("a1_infer_001", "summary_controls_infer.json"),
        "a1": ("a1_001", "summary_a1.json"), "c0_frozen_gate": ("c0_001", "summary_c0.json"),
        "c0_diag": ("c0_diag_001", "summary_c0_diag.json"), "c0": ("c0_rescore_001", "summary_c0.json"),
        "u1": ("b_u1_004", "summary_u1.json"), "u2": ("b_u2_003", "summary_u2.json"), "u3": ("b_u3_002", "summary_u3.json"),
        "u4": ("b_u4_001", "summary_u4.json"), "b1": ("b1_001", "summary_b1.json")}


def _load(config, run, name):
    p = ROOT / cfg(config, "paths.results_relative") / run / name
    return json.loads(p.read_text()) if p.exists() else None


def c0_auc_by_score(config) -> dict:
    """SIR>3 AUC from the latent, from raw q4+q5, and from floored/renormalised q4+q5 (saved c0_001 units)."""
    src = ROOT / cfg(config, "paths.private_relative") / config["headroom"]["amendment_001"]["source_run"] / "units"
    units = [json.loads(p.read_text()) for p in sorted(src.glob("s*_k*.json"))]
    from .adapters import round1_cohort
    _, co = round1_cohort(config)
    sir = co.ch.set_index("child").sir.to_dict()
    floor = float(config["headroom"]["probability_floor"])
    out = {}
    for s in sorted({u["seed"] for u in units}):
        lat, raw, flo, y = [], [], [], []
        for u in (u for u in units if u["seed"] == s):
            P = np.array(u["proba_raw"])
            Q = np.maximum(P, floor)
            Q = Q / Q.sum(1, keepdims=True)
            lat += u["latent"]
            raw += list(P[:, 3:].sum(1))
            flo += list(Q[:, 3:].sum(1))
            y += [float(sir[c] > 3) for c in u["test_children"]]
        raw, flo = np.array(raw), np.array(flo)
        out[str(s)] = {"auc_latent": st.auc(y, lat), "auc_raw_probability": st.auc(y, raw), "auc_floored_probability": st.auc(y, flo),
                       "raw_probability_ties_at_0_or_1": int(np.sum((raw <= 1e-15) | (raw >= 1 - 1e-15))),
                       "floored_distinct_values": int(len(np.unique(np.round(flo, 12))))}
    return out


def cmd_report(args, config) -> dict:
    run = open_run("report", args.run, config, args=vars(args))
    out = {name: _load(config, r, f) for name, (r, f) in RUNS.items()}
    out["status_by_package"] = {k: (v.get("status") if isinstance(v, dict) else None) for k, v in out.items()}
    try:
        out["c0_auc_by_score_type"] = c0_auc_by_score(config)
    except FileNotFoundError:
        out["c0_auc_by_score_type"] = None
    ledger = ROOT / cfg(config, "paths.private_relative") / "job_ledger.jsonl"
    events = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    out["jobs"] = sorted({e["job"].split("_r")[0] for e in events})
    out["requeues"] = sorted({e["job"] for e in events if "_r0" not in e["job"]})
    out["resources_used"] = {
        "new_encoder_fits": 0,
        "small_age_fits": int((out["a0"] or {}).get("small_age_fits", 0) + (out["a1"] or {}).get("small_age_fits", 0)),
        "ordinal_optimizer_calls": int((out["c0_diag"] or {}).get("ordinal_calls_cumulative", 0)),
        "trained_encoder_inference_units": int((out["a1_infer"] or {}).get("inference_units_trained", 0)),
        "random_encoder_inference_units": int((out["a1_infer"] or {}).get("inference_units_random", 0)),
        "synthetic_worlds": int((out["synthetic"] or {}).get("n_worlds", 0))}
    write_json_atomic(run["public"] / "summary.json", out, private=False)
    close_run(config, "report", args.run, "COMPLETED")
    return {"status_by_package": out["status_by_package"], "resources_used": out["resources_used"],
            "c0_auc_by_score_type": out["c0_auc_by_score_type"], "requeues": out["requeues"]}
