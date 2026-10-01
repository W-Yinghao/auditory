"""B1: stimulus-context support map, exposure summary and next-training task cards (execution spec section 9).

Reads the saved B0 outputs only. Cards are proposals with explicit feasibility and unresolved dependencies; nothing
here trains a model. Public output: counts per card; per-record lists stay private.
"""
from __future__ import annotations

import json

import pandas as pd

from .runtime import ROOT, cfg, close_run, open_run, write_csv_atomic, write_json_atomic

STRONG = ("DIRECT", "LINKED")


def _summary(config, run, name):
    p = ROOT / cfg(config, "paths.results_relative") / run / name
    return json.loads(p.read_text()) if p.exists() else {}


def support_table(C: pd.DataFrame, idx: pd.DataFrame, members: pd.DataFrame, d1: set, gx2: set, canon: set) -> pd.DataFrame:
    """One row per record with a strong stimulus pair: family, pair, data level, identity status, exposure."""
    stim = C[C.claim_field.str.startswith("stimulus_id") & C.evidence_grade.isin(STRONG)]
    fam = C[(C.claim_field == "task_family") & C.evidence_grade.isin(STRONG)]
    link = dict(zip(members.container_id, members.name_link_status)) if len(members) else {}
    known = dict(zip(members.container_id, members.links_existing_canonical_identity)) if len(members) else {}
    rows = []
    for rid, g in stim.groupby("record_id"):
        roles = {r.claim_field.split("[")[1].rstrip("]"): r.claim_value for r in g.itertuples()}
        fams = set(fam[fam.record_id == rid].claim_value)
        level = idx.loc[rid, "data_level"] if rid in idx.index else "unknown"
        grades = set(g.evidence_grade)
        rows.append({"record_id": rid, "task_family": "|".join(sorted(fams)) or "unknown",
                     "pair": " vs ".join(sorted(set(roles.values()))), "roles": json.dumps(roles, sort_keys=True),
                     "best_grade": "DIRECT" if "DIRECT" in grades else "LINKED", "data_level": level,
                     "canonical": rid in canon, "d1_exported": rid in d1, "in_gx2_ssl": rid in gx2,
                     "identity_status": ("canonical_identity_graph" if rid in canon else
                                         ("known_identity" if known.get(rid) else link.get(rid, "not_in_noncanonical_members")))})
    return pd.DataFrame(rows)


def cmd_unlock_plan(args, config) -> dict:
    run = open_run("unlock_plan", args.run, config, args=vars(args))
    priv = ROOT / cfg(config, "paths.private_relative")
    C = pd.read_csv(priv / "b_u1_004" / "semantic_claims.csv", dtype={"claim_value": str})
    idx = pd.read_csv(ROOT / "results/mff_001/container_index.csv").set_index("container_id")
    members = pd.read_csv(priv / "b_u3_002" / "noncanonical_members.csv")
    exp = pd.read_csv(priv / "b_u3_002" / "exposure_ledger.csv")
    d1 = {p.stem for p in (ROOT / "private/auditory_d1" / cfg(config, "sources.d1_mff_run") / "arrays").glob("*.json")}
    gx2 = set(exp[(exp.model_or_run == "GX2_ssl_mff") & (exp.exposure_status == "pretraining_used")].container_id)
    canon = set(pd.read_csv(ROOT / cfg(config, "sources.canonical_labels")).container_id)
    S = support_table(C, idx, members, d1, gx2, canon)
    write_csv_atomic(S, run["private"] / "stimulus_support.csv", private=True)
    u1, u2 = _summary(config, "b_u1_004", "summary_u1.json"), _summary(config, "b_u2_003", "summary_u2.json")
    u3, u4 = _summary(config, "b_u3_002", "summary_u3.json"), _summary(config, "b_u4_001", "summary_u4.json")
    cont = S[S.data_level == "continuous_or_discontinuous"] if len(S) else S
    fam_counts = {}
    for fam, g in (cont.groupby("task_family") if len(cont) else []):
        fam_counts[fam] = {"continuous_records": int(len(g)), "pairs": sorted(set(g.pair)),
                           "d1_exported": int(g.d1_exported.sum()), "canonical": int(g.canonical.sum()),
                           "identity_resolved": int(g.identity_status.isin(["canonical_identity_graph", "known_identity", "name_link"]).sum()),
                           "in_gx2_ssl": int(g.in_gx2_ssl.sum()), "linked_only": int((g.best_grade == "LINKED").sum())}
    cards = []
    for fam, f in fam_counts.items():
        feasible = f["d1_exported"] > 0 and f["identity_resolved"] == f["continuous_records"]
        cards.append({
            "task_id": f"B1_pair_{fam}", "research_question": f"Within-record discrimination of the recovered {fam} sound pair(s)",
            "target_semantics": f"concrete stimulus pair(s) {f['pairs']} (name literals; audio unverified); not an abstract category",
            "input_unit": "event-locked trials of D1 continuous exports, child as the unit",
            "allowed_evidence_grades": list(STRONG), "included_source_scopes": "non-canonical and canonical MFF with strong stimulus claims",
            "identity_partition_rule": "conservative identity groups; unresolved containers grouped with any possible overlap",
            "age_range_support": "unknown for unresolved identities", "trial_budget": "fixed per class, as GX/PF",
            "within_record_comparison": True, "stimulus_context_confounding": "pair == record/block (each record carries one pair)",
            "preprocessing_and_reference": "auditory_d1_continuous_v1 (no new montage search)",
            "model_comparison": "target-only readout vs population encoder; no four-way pooling",
            "exposure_limitations": f"{f['in_gx2_ssl']} of {f['continuous_records']} records were in GX2 self-supervised pretraining",
            "support": f, "feasible_now": bool(feasible),
            "unresolved_dependencies": [d for d, bad in (("identity of unresolved containers", f["identity_resolved"] < f["continuous_records"]),
                                                           ("records not D1-exported", f["d1_exported"] < f["continuous_records"])) if bad],
            "status": "DEFERRED_NEW_TRAINING_SPEC_REQUIRED" if feasible else "NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT"})
    cards.append({"task_id": "B1_protocol_conditioned_sharing", "research_question":
                  "Does protocol-conditioned sharing (shared encoder + protocol head) beat target-only and naive pooling on MFF?",
                  "target_semantics": "standard vs deviant within known protocols (canonical puretone 41, bapa 29) plus any recovered protocol",
                  "model_comparison": "target-only / naive pooling / shared encoder + protocol head; same test children, label and optimisation budget",
                  "identity_partition_rule": "conservative identity graph (111 canonical groups); recovered records only if identity-resolved",
                  "exposure_limitations": "GX lanes already trained on these canonical records (exploratory reuse, not validation)",
                  "feasible_now": True, "unresolved_dependencies": ["new training specification (GPU) and user approval"],
                  "status": "DEFERRED_NEW_TRAINING_SPEC_REQUIRED"})
    cards.append({"task_id": "B1_frozen_age_evaluation_new_samples",
                  "research_question": "Frozen age models on net-new, unexposed identities",
                  "support": {"net_new_identity_candidates": u3.get("net_new_identity_candidates"),
                              "with_age": u3.get("net_new_identity_candidates_with_age"),
                              "with_pretraining_exposure": (u3.get("exposure") or {}).get("net_new_identities_with_pretraining_exposure"),
                              "set_net_new": u2.get("net_new_identity_candidates")},
                  "feasible_now": False, "unresolved_dependencies": ["no unexposed net-new identity with age"],
                  "status": "NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT"})
    cards.append({"task_id": "B1_bdf_clock_held_records", "research_question": "Recover 9 clock-held BDF records for event analyses",
                  "support": {"held": u4.get("held"), "candidate_status": u4.get("candidate_status")},
                  "feasible_now": False, "unresolved_dependencies": ["header resolution 1 s, no sub-second metadata; a separately "
                                                                     "pre-specified support/query validation would be required"],
                  "status": "SOURCE_UNRESOLVED", "note": "these are existing children (no identity gain)"})
    out = {"stimulus_support_records": int(len(S)), "continuous_records_with_strong_pair": int(len(cont)),
           "by_family": fam_counts, "role_reversal_candidates": u1.get("role_reversal_candidates"),
           "cards": cards, "status": "COMPLETED"}
    write_json_atomic(run["public"] / "summary_b1.json", out, private=False)
    close_run(config, "unlock_plan", args.run, "COMPLETED")
    return {"by_family": fam_counts, "cards": [(c["task_id"], c["status"]) for c in cards]}
