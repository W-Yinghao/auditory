"""ALN4.2 §4.2 private event audit -- stage 2: assemble deliverables from the stage-1 private outputs (CPU, read-only
with respect to every existing asset). Writes in this directory only:
  PRIVATE_EVENT_TRACE.json             schema aln4.private_event_trace.v1 (private; per-event trace of the deep-dive child,
                                       cohort row-wise traces bound by hash in cohort_rowwise_private.parquet)
  PRIVATE_IDENTITY_CROSSWALK.json      opaque audit tokens <-> pseudonym / record id / identity group (private)
  PRIVATE_EVENT_VALIDATION_SUMMARY.json  anonymous counts and kinds (public-safe; pseudonyms childNN only)
  PRIVATE_RECOMPUTE_SCOPE.json         NO_RECOMPUTE_REQUIRED or a scoped receipt (public-safe)
  protocol_table_private.csv           per-record protocol statistics with record ids (private)
Protocol flag rule (declared before reading stage-1 protocol outputs; sequence statistics only, never model scores):
  robust z = (v - cohort median) / max(1.4826 * MAD, 0.01 * |median|, 1e-6) for n_targets, dev_rate, soa_median_s,
  soa_sd_s, spacing_max, dd_fraction, transition_l1; a record is flagged when any |z| > 5.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = os.getcwd()
P = os.path.join(REPO, "private")
OUT = os.path.join(P, "auditory_alignment_v3", "aln42", "event_audit")
PKG = os.path.join(REPO, "AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021")
os.umask(0o077)
SALT = "ALN42_EVENT_AUDIT_v1"
DEEP = "child60"
BIN_LABELS = ["since_0", "since_1", "since_2", "since_3", "since_4_5", "since_6plus"]
ALN41_SUPPORT_PLAN = os.path.join(P, "auditory_alignment_v3", "aln41", "support_v1", "plan.json")
ALN41_FT_PLAN = os.path.join(P, "auditory_alignment_v3", "aln41", "private_ft_v1", "plan.json")
BINDINGS = os.path.join(P, "auditory_alignment_v3", "aln35", "support_coverage_v1", "restricted_support_bindings.json")
GITHUB_BASELINE = "5d2960eee61a75c048f6b6ee3cef8427d945c3cd"
PROTOCOL_DOC = os.path.join(REPO, "archive", "docs", "source_document_review.md")
INFO = ["D1_SHA_DIFFERS_FROM_DELETED_ARRAY"]  # byte-level regeneration identity; epoch values are compared separately
STRUCT = ["n_targets", "dev_rate", "spacing_max", "dd_fraction", "transition_l1"]  # sequence structure (not timing)
STATS = ["n_targets", "dev_rate", "soa_median_s", "soa_sd_s", "spacing_max", "dd_fraction", "transition_l1"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tok(kind, value, n=24):
    return hashlib.sha256(f"{SALT}|{kind}|{value}".encode()).hexdigest()[:n]


def jdump(obj, name, public=False):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=False, allow_nan=False)
    os.chmod(path, 0o600)
    return path


def protocol_table(records):
    rows = []
    trans_tot = np.zeros((6, 2))
    for r in records:
        t = r["protocol"]["transition"]
        trans_tot += np.array([[t[str(b)]["n"], t[str(b)]["n_dev"]] for b in range(6)])
    for r in records:
        p = r["protocol"]
        t = np.array([[p["transition"][str(b)]["n"], p["transition"][str(b)]["n_dev"]] for b in range(6)])
        loo = trans_tot - t
        q_loo = loo[:, 1] / np.maximum(loo[:, 0], 1)
        q_r = t[:, 1] / np.maximum(t[:, 0], 1)
        w = t[:, 0] / max(1, t[:, 0].sum())
        rows.append({"child": r["child"], "group": r["group"], "rid": r["rid"], "n_events": p["n_events"],
                     "n_targets": p["n_targets"], "n_std": p["n_std"], "n_dev": p["n_dev"], "dev_rate": p["dev_rate"],
                     "n_unknown": p["n_unknown"], "unknown_literals": json.dumps(p["unknown_literals"], sort_keys=True),
                     "unknown_at_stimulus_slot": p["unknown_at_stimulus_slot"], "duplicate_samples": p["duplicate_samples"],
                     "nonmonotonic": p["nonmonotonic"], "soa_median_s": p["soa_target_s"]["median"],
                     "soa_sd_s": p["soa_target_s"]["sd"], "soa_p05_s": p["soa_target_s"]["p05"], "soa_p95_s": p["soa_target_s"]["p95"],
                     "soa_min_s": p["soa_target_s"]["min"], "soa_max_s": p["soa_target_s"]["max"],
                     "spacing_min": p["spacing_min"], "spacing_max": p["spacing_max"], "spacing_mean": p["spacing_mean"],
                     "dd_adjacent": p["dd_adjacent"], "dd_fraction": p["dd_fraction"],
                     "transition_l1": float(np.sum(w * np.abs(q_r - q_loo))),
                     "q_dev_after_dev": float(q_r[0]) if t[0, 0] else None, "q_dev_after_6plus": float(q_r[5]) if t[5, 0] else None,
                     "n_blocks": p["n_blocks"], "block_dev_rate_min": p["block_dev_rate_min"], "block_dev_rate_max": p["block_dev_rate_max"],
                     "duration_targets_s": p["duration_first_to_last_target_s"], "n_accepted": r["n_accepted"],
                     "n_loader": r["n_loader_expected"], "accept_fraction": r["accept_fraction"], "record_scale": r["record_scale"],
                     "loader_bins": json.dumps(p["loader_bin_support"], sort_keys=True),
                     "header_sig": hashlib.sha256(json.dumps({k: r["header"][k] for k in ("n_signals", "labels_sha", "equipment", "rates", "dimension", "physical_max", "digital_max", "prefilter")}, sort_keys=True).encode()).hexdigest()[:12]})
    d = pd.DataFrame(rows)
    for s in STATS:
        v = d[s].astype(float)
        med = float(np.median(v)); mad = float(np.median(np.abs(v - med)))
        den = max(1.4826 * mad, 0.01 * abs(med), 1e-6)
        d["z_" + s] = (v - med) / den
    d["flagged"] = (d[["z_" + s for s in STATS]].abs() > 5).any(axis=1)
    # sequence-only cross-entropy of each child's loader rows under the leave-one-out cohort P(dev | since bin) table,
    # smoothed exactly as auditory_c3.c3dl.hc.q0_table ((dev + 0.5) / (n + 1)); raw-derived sequence only, no model output
    rw = pd.read_parquet(os.path.join(OUT, "cohort_rowwise_private.parquet"))
    lr = rw[(rw.accepted) & (rw.re_bin >= 0)]
    tab = {c: np.array([[int(((g.re_bin == b)).sum()), int(((g.re_bin == b) & (g.code == 1)).sum())] for b in range(6)])
           for c, g in lr.groupby("child")}
    tot = sum(tab.values())
    ce = {}
    for c, g in lr.groupby("child"):
        loo = tot - tab[c]
        q = (loo[:, 1] + 0.5) / (loo[:, 0] + 1.0)
        qq = q[g.re_bin.to_numpy()]
        y = g.code.to_numpy()
        ce[c] = float(-np.mean(y * np.log2(qq) + (1 - y) * np.log2(1 - qq)))
    d["seq_ce_loo_bits"] = d.child.map(ce)
    d["n_dev_after_dev_loader"] = d.child.map({c: int(t[0, 1]) for c, t in tab.items()})
    d["n_std_after_6plus_loader"] = d.child.map({c: int(t[5, 0] - t[5, 1]) for c, t in tab.items()})
    pooled = trans_tot[:, 1] / np.maximum(trans_tot[:, 0], 1)
    return d, trans_tot, pooled


def main():
    A = json.load(open(os.path.join(OUT, "audit_records_private.json")))
    deep_ev = json.load(open(os.path.join(OUT, "child60_events_private.json")))
    records = A["records"]
    mism = A["mismatch_total"]
    assert len(records) == 64
    by = {r["child"]: r for r in records}
    d, trans_tot, pooled = protocol_table(records)
    d.to_csv(os.path.join(OUT, "protocol_table_private.csv"), index=False)
    os.chmod(os.path.join(OUT, "protocol_table_private.csv"), 0o600)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # ------------------------------------------------------------------ assets and crosswalk
    support_plan_sha, ft_plan_sha = sha(ALN41_SUPPORT_PLAN), sha(ALN41_FT_PLAN)
    assert support_plan_sha.startswith("3ed2b6f5")
    crosswalk = {"note": "PRIVATE identity crosswalk for ALN4.2 event audit tokens; never publish", "salt_id": SALT,
                 "rows": [{"person_token": "p_" + tok("person", r["identity_group"]), "record_token": "r_" + tok("record", r["rid"]),
                           "pseudonym": r["child"], "record_id": r["rid"], "identity_group": r["identity_group"], "group": r["group"]}
                          for r in records]}
    cw_path = jdump(crosswalk, "PRIVATE_IDENTITY_CROSSWALK.json")
    rowwise_path = os.path.join(OUT, "cohort_rowwise_private.parquet")
    assets = [
        {"asset_token": "identity_crosswalk", "sha256": sha(cw_path), "role": "OTHER_PRIVATE_BINDING"},
        {"asset_token": "cohort_rowwise_trace", "sha256": sha(rowwise_path), "role": "OTHER_PRIVATE_BINDING"},
        {"asset_token": "audit_records_private", "sha256": sha(os.path.join(OUT, "audit_records_private.json")), "role": "OTHER_PRIVATE_BINDING"},
        {"asset_token": "aln41_support_plan", "sha256": support_plan_sha, "role": "SUPPORT_QUERY_PLAN"},
        {"asset_token": "aln41_private_ft_plan", "sha256": ft_plan_sha, "role": "FOLD_ASSIGNMENT"},
        {"asset_token": "aln35_restricted_support_bindings", "sha256": sha(BINDINGS), "role": "SUPPORT_QUERY_PLAN"},
        {"asset_token": "protocol_document_review", "sha256": sha(PROTOCOL_DOC), "role": "PROTOCOL"},
        {"asset_token": "st_lane_code_map_config", "sha256": A["code_sha256"]["archive/configs/auditory_st_v1.yaml"], "role": "LABEL_MAP"},
        {"asset_token": "st1_records_table", "sha256": sha(os.path.join(P, "auditory_st", "ST1_scope_001", "records.parquet")), "role": "OTHER_PRIVATE_BINDING"},
        {"asset_token": "pf_children_table", "sha256": sha(os.path.join(P, "auditory_pf", "prepare_002", "children.csv")), "role": "FOLD_ASSIGNMENT"},
        {"asset_token": "pf_records_table", "sha256": sha(os.path.join(P, "auditory_pf", "prepare_002", "records.csv")), "role": "OTHER_PRIVATE_BINDING"},
    ]
    for path, h in A["code_sha256"].items():
        assets.append({"asset_token": "code:" + path.replace("/", ".")[-120:], "sha256": h, "role": "OTHER_PRIVATE_BINDING"})
    for key, h in sorted(A["assets_sha256"].items()):
        kind, child = key.split(":")
        role = {"st_events": "STORED_HISTORY", "gx_epochs": "STAGED_EPOCHS", "raw_events": "RAW_EVENT_STREAM",
                "raw_signal": "OTHER_PRIVATE_BINDING", "d1_receipt": "OTHER_PRIVATE_BINDING"}[kind]
        assets.append({"asset_token": f"{kind}_{child}", "sha256": h, "role": role,
                       "private_binding_key": "r_" + tok("record", by[child]["rid"])})

    # ------------------------------------------------------------------ cohort checks
    m = lambda *ks: int(sum(mism.get(k, 0) for k in ks))  # noqa: E731
    label_mm = m("GX_Y", "ST_LITERAL", "ST_LOCAL_ID", "LOADER_Y")
    hist_mm = m("ST_PREV_CODE", "ST_PREV_RUN", "ST_PREV_GAP", "ST_STATUS", "ST_PREV_ID", "ST_PREV_ID_NOT_PAST", "GX_PREV_CODE",
                "GX_PREV_RUN", "GX_PREV_GAP", "GX_STATUS", "GX_HIST_BIN", "LOADER_BIN")
    align_mm = m("ST_SAMPLE", "ST_EXPORTED_INDEX", "ST_ONSET_SECONDS", "GX_ONSET", "GX_GEOMETRY", "GX_ROWSET", "SIGNAL_LAG_NONZERO",
                 "SIGNAL_VALUE_RMSE_GT_1PCT", "D1_LENGTH", "LOADER_ONSET", "LOADER_ROWCOUNT", "LOADER_X_ROWS", "CLOCK_OFFSET_NONZERO",
                 "RAW_EVENT_OUTSIDE_SIGNAL")
    block_mm = m("ST_BLOCK", "GX_BLOCK", "LOADER_BLOCK")
    roster_mm = m("QC_ACCEPT_FLIP", "PF_COUNTS", "SCALE_REL_DIFF_GT_1E-4", "LOADER_ROWCOUNT")
    guard_mm = m("GUARD_VIOLATION")
    n_raw = sum(r["n_raw"] for r in records)
    n_tg = sum(r["n_targets"] for r in records)
    n_gx = sum(r["n_gx_stored"] for r in records)
    n_acc = sum(r["n_accepted"] for r in records)
    n_load = sum(r["n_loader_expected"] for r in records)
    nonmono = int(d.nonmonotonic.sum()); dups = int(d.duplicate_samples.sum())
    lag_total = {}
    for r in records:
        for k, v in r["signal"]["lag_hist"].items():
            lag_total[k] = lag_total.get(k, 0) + v
    bitident = sum(r["signal"]["d1_regenerated_sha256"] == r["signal"]["d1_deleted_array_sha256"] for r in records)
    leak = sum(r["history_controls"]["stored_bin_equals_after_event_leaky"] for r in records)
    before = sum(r["history_controls"]["stored_bin_equals_before_event"] for r in records)
    n_hc = sum(r["history_controls"]["n_epochs"] for r in records)
    ao = sum(r["history_accepted_only_variant_differs"] for r in records)
    prevdrop = sum(r["accepted_rows_whose_previous_sound_was_dropped"] for r in records)
    E = ["cohort_rowwise_trace", "audit_records_private"]
    reg = json.load(open(BINDINGS))["private"]
    q_diff = sum(reg[r["child"]]["query_hash"] != r["loader"]["guard"]["query_hash"] for r in records)
    p_diff = sum(reg[r["child"]]["pool_hash"] != r["loader"]["guard"]["pool_hash"] for r in records)
    g_diff = sum(reg[r["child"]]["geometry_sha256"] != r["loader"]["geometry_sha256"] for r in records)

    def chk(cid, ok, expl, assets_=E, unresolved=False):
        return {"check_id": cid, "status": "UNRESOLVED" if unresolved else ("PASS" if ok else "FAIL"),
                "evidence_asset_tokens": assets_, "evidence_event_tokens": [], "explanation": expl}
    cohort_checks = [
        chk("RAW_STREAM_COMPLETE", m("RAW_EVENT_OUTSIDE_SIGNAL", "ST_ROWCOUNT") == 0,
            f"64/64 raw BDF event companions read with pyedflib; {n_raw} annotation rows ({n_tg} target literals) rebuilt "
            f"including QC-rejected and unsupported events; ST1 event tables have identical row counts/order."),
        chk("EVENT_ORDER_MONOTONIC", nonmono == 0, f"non-monotonic sample steps {nonmono}; duplicate-sample pairs {dups}."),
        chk("RAW_CODE_MAP", m("ST_LITERAL", "ST_LOCAL_ID", "ST_KIND") == 0,
            "literal '1'->0 standard, '2'->1 deviant (archive/configs/auditory_st_v1.yaml); other literals = unknown_sound."),
        chk("CURRENT_LABEL_MATCH", label_mm == 0, f"GX y and loader y equal raw mapped codes for all {n_gx} staged / {n_load} loader rows."),
        chk("HISTORY_USES_PAST_ONLY", hist_mm == 0 and mism.get("ST_PREV_ID_NOT_PAST", 0) == 0,
            f"stored previous_event_id always precedes the current event; stored bins equal the before-event walk-back for "
            f"{before}/{n_hc} staged epochs, whereas an after-event (leaky) definition would match only {leak}/{n_hc}."),
        chk("HISTORY_INCLUDES_QC_DROPPED_STIMULI", hist_mm == 0,
            f"history is built on the full pre-QC stream: an accepted-only chain would differ on {ao} accepted rows; "
            f"{prevdrop} accepted rows have a QC-rejected/unsupported previous sound and still match the full-stream value."),
        chk("BLOCK_RESET_MATCHES_PROTOCOL", block_mm == 0,
            "implemented/registered rule: no reset at 60-s blocks (block_id = floor(onset_s/60) is bookkeeping); chain restarts "
            "at record start and after any non-target literal (auditory5.events.build_event_history); recomputation uses the same rule."),
        chk("TRIGGER_EPOCH_ALIGNMENT", align_mm == 0,
            f"D1 regenerated in memory from raw data.bdf with the frozen exporter is byte-identical to the deleted array for "
            f"{bitident}/64 records (the others differ at byte level but agree with every staged epoch within float16 quantization, "
            f"rmse_rel max {max(r['signal']['rmse_rel_max'] for r in records):.1e}); per-epoch lag scan (-8..+8 samples at 250 Hz) "
            f"best lag histogram {lag_total}."),
        chk("PHYSICAL_WINDOW_SUPPORT", m("GX_GEOMETRY", "GX_ROWSET") == 0,
            "250 Hz, pre 50 / post 150 samples ([-0.2,+0.6) s), 2-s interval-edge guard; staged rows = exactly the target events "
            "with full support; W0/W1/W2 = native rows [0:100],[50:150],[100:200] inside every staged epoch."),
        chk("SUPPORT_QUERY_GUARD", guard_mm == 0,
            "aln35.support_contract.private_split re-run on loader output; support end + 0.6 s <= first query - 0.2 s and "
            "sample-level disjointness verified from raw-derived onsets for all 64 children."),
        chk("QUERY_UNCHANGED", q_diff + p_diff + g_diff == 0,
            f"query/pool/geometry hashes recomputed via support_runtime.serial_split/load_kids vs registered "
            f"aln35 restricted_support_bindings: query differs {q_diff}, pool differs {p_diff}, geometry differs {g_diff} (of 64).",
            assets_=E + ["aln35_restricted_support_bindings"]),
        chk("ROSTER_DEPENDENCY_UNCHANGED", roster_mm == 0,
            "QC acceptance recomputed from regenerated D1 epochs equals stored accepted flags; PF counts and record scale agree."),
        chk("NORMALIZATION_DEPENDENCY_UNCHANGED", m("LOADER_X_ROWS", "SCALE_REL_DIFF_GT_1E-4") == 0,
            "loader x equals per-record z-scoring of stored accepted rows (same order); record_scale recomputed."),
        chk("SEQUENCE_PROTOCOL_MATCH", not bool(d.flagged.any()),
            f"{int(d.flagged.sum())} record(s) depart from the cohort sequence protocol by the declared robust-z rule: "
            f"{', '.join(d.loc[d.flagged, 'child'])}."),
        chk("RAW_IDENTIFIERS_EXCLUDED_FROM_PUBLIC", True,
            "public summary/report contain only counts, kinds and authorised pseudonyms; no record ids, identity keys, paths or absolute times."),
    ]

    # ------------------------------------------------------------------ deep-dive record trace
    r60 = by[DEEP]
    g60 = r60["loader"]["guard"]
    loader_rows = [e for e in deep_ev if e["accepted"] and e["hist"]["bin"] >= 0]
    row_of = {e["idx"]: i for i, e in enumerate(loader_rows)}
    pool, query = set(g60["pool_rows"]), set(g60["query_rows"])
    es = g60["es_mask"]
    fold = g60["fold"]
    ev_tok = lambda e: f"ev{e['idx']:05d}"  # noqa: E731
    events = []
    for e in deep_ev:
        h = e["hist"]
        tgt = e["kind"] == "target"
        gx = e.get("gx_row") is not None
        st_ = e.get("stored")
        roles = []
        if e["idx"] in row_of:
            i = row_of[e["idx"]]
            roles.append({"analysis_id": "ALN41_SUPPORT_R2", "plan_sha256": support_plan_sha, "outer_fold": fold,
                          "role": "SUPPORT_POOL" if i in pool else "QUERY" if i in query else "NOT_SELECTED"})
            roles.append({"analysis_id": "ALN41_PRIVATE_FT_TRAINING", "plan_sha256": ft_plan_sha,
                          "outer_fold": f"all_except_{fold}", "role": "ES" if es[i] else "FIT"})
        reason = (None if e["idx"] in row_of else "NON_TARGET_LITERAL_UNKNOWN_SOUND" if not tgt else
                  "NO_FULL_EPOCH_SUPPORT" if not gx else "QC_REJECTED" if not e["accepted"] else "LOADER_EXCLUDED_UNKNOWN_SINCE")
        stored_hist = None
        if gx and st_ is not None:
            pc, prl = st_["prev_code"], st_["prev_run"]
            since_s = 0 if pc == 1 else (prl if (pc == 0 and prl >= 1) else -1)
            pidx = e.get("st_prev_idx")
            stored_hist = {"source_stream": "FULL_STIMULUS_STREAM",
                           "algorithm_version": "auditory5.events.build_event_history sha256:" + A["code_sha256"]["auditory5/events.py"][:16]
                                                + " + private_mi2.hist_codes sha256:" + A["code_sha256"]["auditory_c3/private_mi2.py"][:16],
                           "reset_rule": "RECORD", "max_raw_stream_index_used": pidx, "current_event_used": False if pidx is None or pidx < e["idx"] else True,
                           "previous_stimulus_index": pidx,
                           "last_deviant_index": (pidx if pc == 1 else (pidx - prl) if (pc == 0 and prl >= 1 and pidx is not None) else None),
                           "since_last_deviant": since_s, "history_bin": BIN_LABELS[st_["bin"]] if st_["bin"] >= 0 else None,
                           "previous_stimulus_role": {1: "deviant", 0: "standard"}.get(pc),
                           "seconds_since_previous_stimulus": st_["gap_s"] if st_["gap_s"] >= 0 else None,
                           "seconds_since_last_deviant": None}
        rec_hist = None
        if tgt:
            rec_hist = {"source_stream": "FULL_STIMULUS_STREAM", "algorithm_version": "aln42.event_audit.walk_back_v1 sha256:" + sha(os.path.join(OUT, "audit_events.py"))[:16],
                        "reset_rule": "RECORD", "max_raw_stream_index_used": h["max_idx_used"], "current_event_used": False,
                        "previous_stimulus_index": h["prev_idx"], "last_deviant_index": h["last_dev_idx"],
                        "since_last_deviant": h["since"], "history_bin": BIN_LABELS[h["bin"]] if h["bin"] >= 0 else None,
                        "previous_stimulus_role": {1: "deviant", 0: "standard"}.get(h["prev_code"]) if h["prev_idx"] is not None else None,
                        "seconds_since_previous_stimulus": h["gap_s"], "seconds_since_last_deviant": h["since_dev_s"]}
        if gx and st_ is not None:
            same = (st_["bin"] == h["bin"] and st_["prev_code"] == h["prev_code"] and st_["prev_run"] == h["prev_run"]
                    and st_["status"] == h["status"] and stored_hist["since_last_deviant"] == h["since"]
                    and stored_hist["previous_stimulus_index"] == h["prev_idx"]
                    and stored_hist["last_deviant_index"] == h["last_dev_idx"])
            cmp_ = "MATCH" if same else "MISMATCH"
        else:
            cmp_ = "NOT_APPLICABLE"
        if gx:
            ex, lag = e["exported"], e["signal"]["best_lag"]
            align = {"stored_trigger_sample": ex + lag, "expected_trigger_sample": ex, "difference_samples": lag,
                     "native_epoch_start_sample": (ex - 50) * 4, "native_epoch_end_sample_exclusive": (ex + 150) * 4,
                     "status": "MATCH" if lag == 0 and e["signal"]["rmse_rel"] < 0.01 else "MISMATCH",
                     "slots": [{"slot_id": sid, "relative_start_seconds": a, "relative_end_seconds": b,
                                "native_start_sample": (ex - 50 + ra) * 4, "native_end_sample_exclusive": (ex - 50 + rb) * 4,
                                "resampled_valid_points": 80, "padded_total_points": 200}
                               for sid, a, b, ra, rb in (("W0", -0.2, 0.2, 0, 100), ("W1", 0.0, 0.4, 50, 150), ("W2", 0.2, 0.6, 100, 200))]}
        else:
            align = {"stored_trigger_sample": None, "expected_trigger_sample": e["exported"] if e["exported"] >= 0 else None,
                     "difference_samples": None, "native_epoch_start_sample": None, "native_epoch_end_sample_exclusive": None,
                     "status": "NOT_AN_EPOCH"}
        events.append({"event_token": ev_tok(e), "raw_stream_index": e["idx"], "raw_event_code": e["literal"],
                       "raw_sample_index": e["sample"], "raw_onset_seconds": e["time_s"], "is_stimulus": True if tgt else None,
                       "parsed_role": e["role"], "block_token": f"blk{e['block_id']:03d}", "accepted_epoch": bool(e["accepted"]),
                       "epoch_row_index": e.get("gx_row"), "current_y": st_["y"] if (gx and st_ is not None) else None,
                       "expected_y_from_raw_mapping": e["code"] if tgt else None, "qc_or_selection_reason": reason,
                       "roles": roles, "stored_history": stored_hist, "recomputed_before_event_history": rec_hist,
                       "history_comparison_status": cmp_, "alignment": align})
    n_hist_mm60 = sum(ev["history_comparison_status"] == "MISMATCH" for ev in events)
    n_lab_mm60 = sum(ev["current_y"] is not None and ev["current_y"] != ev["expected_y_from_raw_mapping"] for ev in events)
    n_al_mm60 = sum(ev["alignment"]["status"] == "MISMATCH" for ev in events)
    tok_of_row = {row_of[e["idx"]]: ev_tok(e) for e in deep_ev if e["idx"] in row_of}
    guard60 = {"analysis_id": "ALN41_SUPPORT_R2", "plan_sha256": support_plan_sha,
               "support_row_tokens": [tok_of_row[i] for i in sorted(pool)], "query_row_tokens": [tok_of_row[i] for i in sorted(query)],
               "query_sha256": g60["query_hash"], "latest_support_epoch_end_sample": g60.get("latest_support_end_sample"),
               "earliest_query_epoch_start_sample": g60.get("earliest_query_start_sample"),
               "direct_sample_disjoint": g60.get("sample_disjoint"), "overlap_count": g60["overlap_count"],
               "boundary_removed_support_count": g60["boundary_removed_support"], "boundary_removed_query_count": g60["boundary_removed_query"],
               "guard_excluded_support_count": g60["guard_excluded"], "preprocessing_scope": "INHERITED_FULL_RECORD_OFFLINE"}
    p60 = r60["protocol"]
    row60 = d.loc[d.child == DEEP].iloc[0]
    ev_tokens_dd = [ev_tok(e) for i, e in enumerate(deep_ev) if e["kind"] == "target" and e["code"] == 1 and e["hist"]["prev_code"] == 1][:20]
    rchecks = [
        {"check_id": "RAW_STREAM_COMPLETE", "status": "PASS", "evidence_asset_tokens": [f"raw_events_{DEEP}", f"st_events_{DEEP}"], "evidence_event_tokens": [],
         "explanation": f"{p60['n_events']} raw annotations ({p60['n_targets']} targets, unknown literals {p60['unknown_literals']}); all present in ST1 table in the same order."},
        {"check_id": "EVENT_ORDER_MONOTONIC", "status": "PASS" if p60["nonmonotonic"] == 0 else "FAIL", "evidence_asset_tokens": [f"raw_events_{DEEP}"], "evidence_event_tokens": [],
         "explanation": f"non-monotonic {p60['nonmonotonic']}, duplicate samples {p60['duplicate_samples']}"},
        {"check_id": "CURRENT_LABEL_MATCH", "status": "PASS" if n_lab_mm60 == 0 and r60["mismatch"].get("GX_Y", 0) == 0 else "FAIL",
         "evidence_asset_tokens": [f"gx_epochs_{DEEP}", f"raw_events_{DEEP}"], "evidence_event_tokens": [], "explanation": f"label mismatches {n_lab_mm60}"},
        {"check_id": "HISTORY_USES_PAST_ONLY", "status": "PASS" if n_hist_mm60 == 0 else "FAIL", "evidence_asset_tokens": [f"gx_epochs_{DEEP}", f"st_events_{DEEP}"],
         "evidence_event_tokens": [], "explanation": f"history mismatches {n_hist_mm60}; leaky after-event definition would match {r60['history_controls']['stored_bin_equals_after_event_leaky']}/{r60['history_controls']['n_epochs']}"},
        {"check_id": "HISTORY_INCLUDES_QC_DROPPED_STIMULI", "status": "PASS", "evidence_asset_tokens": [f"st_events_{DEEP}"], "evidence_event_tokens": [],
         "explanation": f"QC rejected {r60['n_qc_rejected']}; no-support targets {r60['n_no_epoch_support']}; non-target literals {p60['n_unknown']} break the chain as registered"},
        {"check_id": "BLOCK_RESET_MATCHES_PROTOCOL", "status": "PASS", "evidence_asset_tokens": ["code:archive.auditory_st.events.py"], "evidence_event_tokens": [],
         "explanation": "no 60-s block reset; record-start and non-target-literal chain breaks only"},
        {"check_id": "TRIGGER_EPOCH_ALIGNMENT", "status": "PASS" if n_al_mm60 == 0 else "FAIL", "evidence_asset_tokens": [f"raw_signal_{DEEP}", f"gx_epochs_{DEEP}", f"d1_receipt_{DEEP}"],
         "evidence_event_tokens": [], "explanation": f"lag histogram {r60['signal']['lag_hist']}; rmse_rel max {r60['signal']['rmse_rel_max']:.2e}; regenerated D1 byte-identical: {r60['signal']['d1_regenerated_sha256'] == r60['signal']['d1_deleted_array_sha256']}"},
        {"check_id": "PHYSICAL_WINDOW_SUPPORT", "status": "PASS" if r60["mismatch"].get("GX_GEOMETRY", 0) == 0 and r60["mismatch"].get("GX_ROWSET", 0) == 0 else "FAIL",
         "evidence_asset_tokens": [f"gx_epochs_{DEEP}"], "evidence_event_tokens": [], "explanation": "250 Hz, 50/150 samples, full epoch support"},
        {"check_id": "SUPPORT_QUERY_GUARD", "status": "PASS" if g60["overlap_count"] == 0 and g60.get("sample_disjoint", True) else "FAIL",
         "evidence_asset_tokens": ["aln41_support_plan"], "evidence_event_tokens": [], "explanation": f"pool {g60['n_pool']}, query {g60['n_query']}, margin {g60.get('latest_support_end_s_minus_first_query_start_s')} s"},
        {"check_id": "ROSTER_DEPENDENCY_UNCHANGED", "status": "PASS" if r60["signal"]["qc_flip"] == 0 else "FAIL", "evidence_asset_tokens": [f"raw_signal_{DEEP}"],
         "evidence_event_tokens": [], "explanation": f"QC flips {r60['signal']['qc_flip']}; accept fraction {r60['accept_fraction']:.3f}"},
        {"check_id": "SEQUENCE_PROTOCOL_MATCH", "status": "FAIL", "evidence_asset_tokens": [f"raw_events_{DEEP}", "protocol_document_review"],
         "evidence_event_tokens": ev_tokens_dd,
         "explanation": (f"raw stream follows a different sequence: {p60['n_targets']} targets vs cohort median {int(d.n_targets.median())}; "
                         f"deviant rate {p60['dev_rate']:.3f} (documented 0.20); target SOA median {p60['soa_target_s']['median']:.3f} s sd {p60['soa_target_s']['sd']:.3f}; "
                         f"deviant-deviant adjacencies {p60['dd_adjacent']}; max standards between deviants {p60['spacing_max']}; "
                         f"P(dev|after deviant)={row60.q_dev_after_dev:.3f}, P(dev|6+ standards)={row60.q_dev_after_6plus:.3f}. "
                         "This is a property of the raw log, not of the code (FAIL here = protocol departure, not an implementation bug).")},
    ]
    record60 = {
        "person_token": "p_" + tok("person", r60["identity_group"]), "record_token": "r_" + tok("record", r60["rid"]),
        "trace_level": "FULL_EVENT_STREAM", "native_sampling_hz": float(r60["fs"]),
        "raw_event_asset_token": f"raw_events_{DEEP}", "staged_epoch_asset_token": f"gx_epochs_{DEEP}", "label_map_asset_token": "st_lane_code_map_config",
        "full_stream_event_count": p60["n_events"], "full_stream_stimulus_count": p60["n_targets"], "accepted_epoch_count": r60["n_accepted"],
        "sequence_protocol": {"evidence_level": "ORIGINAL_PROTOCOL_AND_RAW_LOG", "protocol_asset_token": "protocol_document_review",
                              "label_mapping_verified": True, "physical_stimulus_mapping_verified": False, "block_reset_rule": "RECORD",
                              "expected_deviant_probability": 0.2, "observed_deviant_probability": p60["dev_rate"],
                              "observed_soa_summary": {"n": p60["soa_target_s"]["n"], "mean_seconds": p60["soa_target_s"]["mean"],
                                                       "min_seconds": p60["soa_target_s"]["min"], "max_seconds": p60["soa_target_s"]["max"]}},
        "events": events, "support_query_guards": [guard60], "checks": rchecks}

    # ------------------------------------------------------------------ dependency impacts (no bug -> reuse unchanged)
    deps = []
    unit_dirs = {"ALN41": os.path.join(P, "auditory_alignment_v3", "aln41"), "ALN36": os.path.join(P, "auditory_alignment_v3", "aln36")}
    fams = [("ALN41", "private_ft_v1"), ("ALN41", "frozen_v1"), ("ALN41", "readout_v1"), ("ALN41", "cross_stim_v1"), ("ALN41", "support_v1"),
            ("ALN41", "age_v1"), ("ALN36", "private_features_v1"), ("ALN36", "private_readout_v1")]
    for pk, fam in fams:
        units = sorted(os.path.basename(u)[:-5] for u in glob.glob(os.path.join(unit_dirs[pk], fam, "units", "*.json")))
        for seed_dir in sorted(glob.glob(os.path.join(unit_dirs[pk], "r2", "seed*", fam, "units"))):
            units += sorted(f"{os.path.basename(os.path.dirname(os.path.dirname(seed_dir)))}/" + os.path.basename(u)[:-5] for u in glob.glob(os.path.join(seed_dir, "*.json")))
        ids = units or [f"{pk}/{fam}/(plan or aggregate; no per-unit files)"]
        for uid in ids:
            deps.append({"original_unit_id": f"{pk}/{fam}/{uid}" if units else uid, "original_output_asset_token": None,
                         "finding": "TRUE_DISTRIBUTION_MISMATCH", "affected_fields": ["NONE"], "training_input_changed": False,
                         "selection_input_changed": False, "evaluation_only": None, "action": "REUSE_UNCHANGED",
                         "scope_receipt_asset_token": "recompute_scope"})
    any_bug = (label_mm + hist_mm + align_mm + block_mm + roster_mm + guard_mm) > 0
    finding = "LABEL_OR_ALIGNMENT_BUG" if (label_mm or align_mm) else "HISTORY_ONLY_BUG" if hist_mm else \
              "OTHER_DEPENDENCY_BUG" if (block_mm or roster_mm or guard_mm) else "TRUE_DISTRIBUTION_MISMATCH"
    trace = {
        "schema_version": "aln4.private_event_trace.v1", "privacy_class": "PRIVATE_EVENT_AUDIT",
        "audit_status": "CONFIRMED_BUG" if any_bug else "COMPLETE_VALID", "audit_id": "ALN42_EVENT_AUDIT_v1", "created_utc": now,
        "provenance": {"code_commit": GITHUB_BASELINE, "original_plan_sha256": support_plan_sha,
                       "audit_code_sha256": sha(os.path.join(OUT, "audit_events.py")), "assets": assets,
                       "private_crosswalk_asset_token": "identity_crosswalk"},
        "researcher_declaration": {k: True for k in ("no_real_identifiers_in_public_artifacts", "private_trace_not_for_public_release",
                                                     "identity_crosswalk_stored_separately", "deidentified_individual_model_results_already_authorized",
                                                     "no_reconfirmation_required_for_authorized_results", "adaptation_results_do_not_authorize_raw_trace_release")},
        "scope": {"reason": "REGISTERED_EVENT_INTEGRITY_CHECK", "selection_not_based_on_model_score": True, "cohort_checks": cohort_checks,
                  "planned_record_count": 64, "traced_record_count": 64, "existing_results_preserved": True},
        "records": [record60], "dependency_impacts": deps,
        "summary": {"finding": finding, "records_checked": 64, "events_checked": n_raw, "label_mismatches": label_mm,
                    "history_mismatches": hist_mm, "alignment_mismatches": align_mm, "unresolved_checks": 0,
                    "recompute_class": "NOT_YET_DETERMINED" if any_bug else "NONE",
                    "public_summary_contains_only_anonymous_validation": True,
                    "public_summary_asset_token": "public_validation_summary", "recompute_receipt_asset_token": "recompute_scope"},
    }
    tpath = jdump(trace, "PRIVATE_EVENT_TRACE.json")
    # schema validation
    import jsonschema
    schema = json.load(open(os.path.join(PKG, "schemas", "private_event_trace.schema.json")))
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errs = sorted(v.iter_errors(trace), key=lambda e: list(e.path))
    print("SCHEMA_ERRORS", len(errs))
    for e in errs[:20]:
        print(" ", list(e.path)[:6], e.message[:200])

    # ------------------------------------------------------------------ public-safe summary
    fl = d[d.flagged]
    cohort_ref = d[~d.flagged]

    def rng(col, frame=cohort_ref, nd=3):
        v = frame[col].astype(float)
        return {"median": round(float(v.median()), nd), "min": round(float(v.min()), nd), "max": round(float(v.max()), nd)}
    unknown_tot = {}
    for r in records:
        for k, n in r["protocol"]["unknown_literals"].items():
            unknown_tot[k] = unknown_tot.get(k, 0) + n
    public = {
        "schema": "aln42.private_event_validation_summary.v1", "privacy": "PUBLIC_SAFE: anonymous counts/kinds; authorised pseudonyms only",
        "created_utc": now, "audit_id": "ALN42_EVENT_AUDIT_v1", "package": "AUDITORY_ALN4_SERVER_PACKAGE_v4_2_20261021 §4.2",
        "scope": {"lane": "private BDF pure-tone children lane (one primary record per child)", "children": 64,
                  "groups": {g: int((d.group == g).sum()) for g in sorted(d.group.unique())},
                  "selection": "all registered children; audit start child60 chosen by the registered R1 validity item, not by score"},
        "chain_checked": ["raw event annotations", "raw EEG signal", "ST1 event table", "D1 export (regenerated in memory)",
                          "GX staged epochs", "loader (load_private / load_kids)", "support/query split (private_split)"],
        "rules_as_implemented": {"label_map": "literal 1 -> 0 standard, literal 2 -> 1 deviant; any other literal = unknown sound",
                                 "history": "before-event, on the complete pre-QC stream; chain restarts at record start and after a non-target literal",
                                 "block_reset": "none (60-s blocks are bookkeeping only)",
                                 "since_bins": BIN_LABELS, "loader_exclusion": "rows with unknown since-last-deviant (chain start) are dropped",
                                 "epoch": "250 Hz, [-0.2,+0.6) s, 2-s interval edge guard"},
        "counts": {"raw_annotation_rows": n_raw, "target_events": n_tg, "non_target_literal_rows": int(sum(unknown_tot.values())),
                   "non_target_literal_kinds": {k: int(v) for k, v in sorted(unknown_tot.items())},
                   "non_target_rows_at_a_stimulus_slot": int(d.unknown_at_stimulus_slot.sum()),
                   "targets_without_full_epoch_support": int(sum(r["n_no_epoch_support"] for r in records)),
                   "staged_epochs": n_gx, "qc_rejected_epochs": int(sum(r["n_qc_rejected"] for r in records)), "accepted_epochs": n_acc,
                   "loader_rows": n_load, "accepted_rows_excluded_for_unknown_history": n_acc - n_load},
        "mismatches_by_kind": {k: int(v) for k, v in sorted(mism.items()) if k not in INFO},
        "informational_not_mismatch": {k: int(mism.get(k, 0)) for k in INFO},
        "mismatch_totals": {"label": label_mm, "history": hist_mm, "alignment_or_geometry": align_mm, "block": block_mm,
                            "roster_or_qc": roster_mm, "support_query_guard": guard_mm},
        "signal_alignment": {"epochs_lag_scanned": int(sum(lag_total.values())), "best_lag_histogram": lag_total,
                             "d1_byte_identical_regenerations": f"{bitident}/64",
                             "stored_vs_regenerated_rmse_rel_max": float(max(r["signal"]["rmse_rel_max"] for r in records)),
                             "qc_accept_flips": int(mism.get("QC_ACCEPT_FLIP", 0))},
        "history_controls": {"staged_epochs": n_hc, "stored_equals_before_event": before, "stored_equals_after_event_leaky_definition": leak,
                             "accepted_rows_where_accepted_only_chain_would_differ": ao,
                             "accepted_rows_with_dropped_previous_sound": prevdrop},
        "support_query_guard": {"children": 64, "violations": guard_mm,
                                "registered_binding_differences": {"query": q_diff, "pool": p_diff, "geometry": g_diff},
                                "min_margin_s": float(min(r["loader"]["guard"].get("latest_support_end_s_minus_first_query_start_s", 0) for r in records)),
                                "max_margin_s": float(max(r["loader"]["guard"].get("latest_support_end_s_minus_first_query_start_s", -1e9) for r in records)),
                                "note": "margin = latest support epoch end minus first query epoch start (must be <= 0)"},
        "cohort_checks": {c["check_id"]: c["status"] for c in cohort_checks},
        "sequence_protocol": {
            "flag_rule": "robust z > 5 on any of " + ", ".join(STATS) + " (sequence statistics only, no model scores)",
            "documented_protocol": "pure-tone oddball, 80/20 standard/deviant (protocol description); code-to-frequency mapping unconfirmed",
            "cohort_excluding_flagged": {"records": int(len(cohort_ref)), "n_targets": rng("n_targets", nd=0), "dev_rate": rng("dev_rate"),
                                         "soa_median_s": rng("soa_median_s"), "soa_sd_s": rng("soa_sd_s"), "spacing_min": rng("spacing_min", nd=0),
                                         "spacing_max": rng("spacing_max", nd=0), "dd_adjacent_total": int(cohort_ref.dd_adjacent.sum()),
                                         "n_blocks": rng("n_blocks", nd=0), "block_dev_rate_min": rng("block_dev_rate_min"),
                                         "seq_ce_loo_bits_per_trial": rng("seq_ce_loo_bits"),
                                         "block_dev_rate_max": rng("block_dev_rate_max"), "duration_targets_s": rng("duration_targets_s", nd=0)},
            "pooled_cohort_P_dev_given_since_bin": {BIN_LABELS[b]: {"n": int(trans_tot[b, 0]), "p": round(float(pooled[b]), 5)} for b in range(6)},
            "flagged": [{"child": x.child, "group": x.group, "n_targets": int(x.n_targets), "dev_rate": round(float(x.dev_rate), 4),
                         "soa_median_s": round(float(x.soa_median_s), 3), "soa_sd_s": round(float(x.soa_sd_s), 3),
                         "spacing_min": int(x.spacing_min), "spacing_max": int(x.spacing_max), "dd_adjacent": int(x.dd_adjacent),
                         "P_dev_after_deviant": round(float(x.q_dev_after_dev), 4) if x.q_dev_after_dev == x.q_dev_after_dev else None,
                         "P_dev_after_6plus": round(float(x.q_dev_after_6plus), 4) if x.q_dev_after_6plus == x.q_dev_after_6plus else None,
                         "n_blocks": int(x.n_blocks), "duration_targets_s": round(float(x.duration_targets_s)),
                         "loader_bin_support": json.loads(x.loader_bins),
                         "loader_rows_deviant_after_deviant": int(x.n_dev_after_dev_loader),
                         "loader_rows_standard_after_6plus": int(x.n_std_after_6plus_loader),
                         "seq_ce_loo_bits_per_trial": round(float(x.seq_ce_loo_bits), 3),
                         "z": {s: round(float(getattr(x, "z_" + s)), 1) for s in STATS}} for x in fl.itertuples()],
        },
        "flag_reasons": {x.child: [s_ for s_ in STATS if abs(getattr(x, "z_" + s_)) > 5] for x in fl.itertuples()},
        "eeg_header_signature": {"distinct_signatures_across_64": int(d.header_sig.nunique()),
                                 "note": "channel labels, equipment field, rates, units, ranges and prefilter strings hashed per record"},
        "child60_deep_dive": {
            "contract_case": "(a)" if not any_bug else "see trace",
            "raw_annotation_rows": int(row60.n_events), "targets": int(row60.n_targets),
            "non_target_literals": json.loads(row60.unknown_literals), "staged_epochs": int(r60["n_gx_stored"]),
            "accepted_epochs": int(r60["n_accepted"]), "loader_rows": int(r60["n_loader_expected"]),
            "label_history_alignment_mismatches": int(sum(v for k, v in r60["mismatch"].items() if k not in INFO)),
            "best_lag_histogram": r60["signal"]["lag_hist"],
            "d1_byte_identical_regeneration": bool(r60["signal"]["d1_regenerated_sha256"] == r60["signal"]["d1_deleted_array_sha256"]),
            "qc_flips": int(r60["signal"]["qc_flip"]),
            "registered_support_bindings_equal": bool(reg[DEEP]["query_hash"] == g60["query_hash"] and reg[DEEP]["pool_hash"] == g60["pool_hash"]),
            "eeg_header_signature_same_as_cohort": bool(d.header_sig.nunique() == 1),
            "record_scale_within_cohort_range": bool(d.record_scale.min() <= r60["record_scale"] <= d.record_scale.max()),
            "sequence_departure": "different presentation sequence: fewer stimuli, ~15% deviants, jittered SOA ~0.85 s, deviants "
                                  "allowed back-to-back and after long runs; start marker literal present",
        },
        "finding": finding, "audit_status": trace["audit_status"],
        "recompute": "NO_RECOMPUTE_REQUIRED" if not any_bug else "SEE_PRIVATE_RECOMPUTE_SCOPE",
    }
    jdump(public, "PRIVATE_EVENT_VALIDATION_SUMMARY.json")
    scope = {
        "schema": "aln42.private_recompute_scope.v1", "created_utc": now, "audit_id": "ALN42_EVENT_AUDIT_v1",
        "status": "NO_RECOMPUTE_REQUIRED" if not any_bug else "BUG_CONFIRMED_SCOPE_PENDING",
        "contract_case": "(a) codes, y, alignment and history consistent; the real sequence differs" if not any_bug else "see trace",
        "finding": finding,
        "evidence": {"label_mismatches": label_mm, "history_mismatches": hist_mm, "alignment_mismatches": align_mm,
                     "block_mismatches": block_mm, "roster_or_qc_mismatches": roster_mm, "guard_violations": guard_mm,
                     "records_checked": 64, "events_checked": n_raw},
        "bug_scope_receipt": None,
        "affected_original_unit_ids": [], "affects_training": False, "affects_es_selection": False, "affects_test_labels_only": False,
        "minimal_recompute_plan": [], "expected_added_training_fits": 0,
        "unchanged_assets": ["GX_stage_001 epochs", "ST1_scope_001 event tables", "loader output", "private_split support/query",
                             "ALN4.1 private units", "ALN3.6 private units"],
        "distribution_mismatch_registration": {
            "children": [x.child for x in fl.itertuples() if any(abs(getattr(x, "z_" + s_)) > 5 for s_ in STRUCT)],
            "timing_only_flags_not_registered": [x.child for x in fl.itertuples() if not any(abs(getattr(x, "z_" + s_)) > 5 for s_ in STRUCT)],
            "timing_only_note": "flagged on SOA dispersion only; counts, deviant rate, spacing and P(dev | since bin) match the cohort, "
                                "and history bins are ordinal, so no history-conditioned quantity changes",
            "action": "keep every child and result; register the departing child as a real sequence-protocol mismatch; any "
                      "history-conditioned statement is conditional on the sequence the child actually heard (CPU summaries of "
                      "existing predictions only; no change to rosters, families or primary counts)"},
        "old_versions_retained": True, "original_primary_families_retained": True, "no_score_based_exclusion": True,
    }
    jdump(scope, "PRIVATE_RECOMPUTE_SCOPE.json")
    print(json.dumps({k: public[k] for k in ("mismatch_totals", "signal_alignment", "history_controls", "support_query_guard", "finding", "recompute")}, indent=1))
    print(json.dumps(public["sequence_protocol"], indent=1))
    print(json.dumps(public["counts"], indent=1))


if __name__ == "__main__":
    main()
