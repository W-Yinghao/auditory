"""ALN4.2 §4.2 private children's event/history definition audit -- stage 1 (read-only, CPU).

Chain audited for each of the 64 private children (one PF primary BDF record each):
  raw BDF event annotations (evt.bdf, pyedflib) and raw signal (data.bdf)
    -> ST1_scope_001 event table (archive/auditory_st/events.py ha_events/_finish_rows + auditory5.events.build_event_history)
    -> D1_bdf_001 export (receipt intervals/stride; arrays deleted 2026-10-11, regenerated here in memory only)
    -> GX_stage_001 epochs (auditory_gx/stage.py)
    -> loader (auditory_alignment.data.load_private -> auditory_c3.c3dl.hc.load_children, hist_codes;
       aln35.support_runtime.load_kids) -> aln35.support_contract.private_split.

Everything here is recomputed independently from the raw annotation stream (walk-back definitions, not a call of
build_event_history) and compared row by row. Nothing existing is modified; outputs go only to this private directory.
Rules taken from code/config (not chosen here):
  * literal map from archive/configs/auditory_st_v1.yaml lanes.bdf_puretone.codes ('1'->0 standard, '2'->1 deviant);
  * any other literal is an `unknown_sound` that breaks the history chain (archive/auditory_st/events.py ha_events +
    auditory5/events.py); the record start is a chain start whose first run length is unknown;
  * no reset at 60-s blocks (block_id = floor(onset_s / qc.block_seconds) is bookkeeping only);
  * since-last-deviant bins = auditory_c3/private_mi2.py BINS_SINCE; trials with unknown since (-1) are dropped by the
    loader (hc.load_children `since_last_deviant >= 0`);
  * GX epoch geometry from configs/auditory_gx_v1.yaml (pre 0.2 s, post 0.6 s, interval edge guard 2 s, QC thresholds).
Usage: python audit_events.py
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd
import pyedflib
import yaml

REPO = os.getcwd()
P = os.path.join(REPO, "private")
OUT = os.path.join(P, "auditory_alignment_v3", "aln42", "event_audit")
assert os.path.isdir(OUT)
os.umask(0o077)

ST_CFG = yaml.safe_load(open(os.path.join(REPO, "archive", "configs", "auditory_st_v1.yaml")))
GX_CFG = yaml.safe_load(open(os.path.join(REPO, "configs", "auditory_gx_v1.yaml")))
CODES = {str(k): int(v) for k, v in ST_CFG["lanes"]["bdf_puretone"]["codes"].items()}
BLOCK_S = float(ST_CFG["qc"]["block_seconds"])
GX_PRE_S, GX_POST_S = float(GX_CFG["epoch"]["pre_seconds"]), float(GX_CFG["epoch"]["post_seconds"])
GX_GUARD_S = float(GX_CFG["epoch"]["interval_edge_guard_seconds"])
QC = GX_CFG["qc"]
sys.path.insert(0, REPO)
from auditory_c3.private_mi2 import BINS_SINCE, hist_codes  # noqa: E402

LAGS = np.arange(-8, 9)
DELETED = dict(pd.read_csv(os.path.join(P, "auditory_d1", "DELETED_ARRAYS_20261011_sha256.tsv"), sep="\t")[["relpath", "sha256"]].values)
CHILD_DEEP = "child60"


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def since_bin(v):
    """Integer since-last-deviant (-1 unknown) -> BINS_SINCE index (-1 unknown)."""
    if v < 0:
        return -1
    for i, (lo, hi) in enumerate(BINS_SINCE):
        if lo <= min(v, 99) <= hi:
            return i
    raise ValueError(v)


def cohort():
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    out = []
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        r = pf.loc[int(c.primary_rec)]
        out.append({"child": f"child{int(c.child)}", "group": grp, "rid": str(r.record_id), "pf_row": r.to_dict(),
                    "n_records_child": int(c.n_records), "identity_group": str(c.identity_group)})
    return out


# ----------------------------------------------------------------------------------------------- raw stream
def raw_stream(evt_path, fs, n_original, stride):
    with pyedflib.EdfReader(evt_path) as rd:
        times, durs, codes = rd.readAnnotations()
    ev = []
    for i, (t, d, c) in enumerate(zip(times, durs, codes)):
        lit = str(c).strip()
        s = int(np.rint(float(t) * fs))
        ev.append({"idx": i, "literal": lit, "time_s": float(t), "sample": s, "duration": float(d),
                   "kind": "target" if lit in CODES else "unknown_sound",
                   "role": ("standard" if CODES[lit] == 0 else "deviant") if lit in CODES else "unresolved",
                   "code": CODES.get(lit, -1),
                   "in_signal": 0 <= s < n_original + stride})
    return ev


def recompute_history(ev, fs):
    """Before-event history by direct walk-back over the full raw stream (strictly earlier events only)."""
    n = len(ev)
    for i, e in enumerate(ev):
        h = {"prev_idx": None, "prev_code": -1, "prev_run": -1, "since": -1, "last_dev_idx": None, "gap_s": None,
             "status": "not_target", "max_idx_used": None, "since_dev_s": None}
        if e["kind"] == "target":
            j = i - 1
            if j < 0 or ev[j]["kind"] != "target":
                h["status"] = "no_previous_sound"
            else:
                pc = ev[j]["code"]
                k, run = j, 0
                while k >= 0 and ev[k]["kind"] == "target" and ev[k]["code"] == pc:
                    run += 1
                    k -= 1
                complete = k >= 0 and ev[k]["kind"] == "target"  # stopped at the other target class
                h.update(prev_idx=j, prev_code=pc, prev_run=run if complete else -1,
                         gap_s=(e["sample"] - ev[j]["sample"]) / fs, max_idx_used=j)
                h["status"] = ("incomplete_previous_run" if not complete else
                               "excluded_run_length_2" if run == 2 else "complete")
                # since-last-deviant: standards strictly between the last deviant and the current event
                if pc == 1:
                    h["since"], h["last_dev_idx"] = 0, j
                else:
                    k, cnt = j, 0
                    while k >= 0 and ev[k]["kind"] == "target" and ev[k]["code"] == 0:
                        cnt += 1
                        k -= 1
                    if k >= 0 and ev[k]["kind"] == "target" and ev[k]["code"] == 1:
                        h["since"], h["last_dev_idx"] = cnt, k
                if h["last_dev_idx"] is not None:
                    h["since_dev_s"] = (e["sample"] - ev[h["last_dev_idx"]]["sample"]) / fs
                assert h["max_idx_used"] < i and (h["last_dev_idx"] is None or h["last_dev_idx"] < i)
        h["bin"] = since_bin(h["since"])
        e["hist"] = h
    # leak control: the same quantities if the current label were (wrongly) included
    return ev


def accepted_only_since(ev, accepted_idx):
    """Variant using only accepted-epoch events (for HISTORY_INCLUDES_QC_DROPPED_STIMULI): returns {idx: since}."""
    out, last_dev, cnt, started = {}, None, 0, False
    seq = [e for e in ev if e["idx"] in accepted_idx]
    prev = None
    for e in seq:
        if prev is None:
            out[e["idx"]] = -1
        elif prev["code"] == 1:
            out[e["idx"]] = 0
        else:
            out[e["idx"]] = cnt if started else -1
        if e["code"] == 1:
            started, cnt = True, 0
        else:
            cnt += 1
        prev = e
    return out


# ----------------------------------------------------------------------------------------------- D1 regeneration
def regenerate_d1(signal_path):
    from auditory5.preprocessing import HA_CHANNELS
    from auditory_d1 import contract
    from auditory_d1.export import _chunk_windows
    from auditory_d1.export_bdf import CHUNK_SECONDS, _read_chunks
    with pyedflib.EdfReader(signal_path) as reader:
        names = reader.getSignalLabels()
        picks = [names.index(c) for c in HA_CHANNELS]
        rates = np.asarray(reader.getSampleFrequencies(), dtype=float)
        original_fs = float(rates[picks[0]])
        n_samples = int(reader.getNSamples()[picks[0]])
        stride = contract.stride_for(original_fs)
        step = int(round(CHUNK_SECONDS * original_fs))
        header = {"n_signals": int(reader.signals_in_file), "labels_sha": hashlib.sha256("|".join(names).encode()).hexdigest()[:16],
                  "equipment": str(reader.getEquipment()).strip(), "rates": sorted(set(rates.tolist())),
                  "dimension": sorted({reader.getSignalHeaders()[k]["dimension"] for k in picks}),
                  "physical_max": sorted({float(reader.getSignalHeaders()[k]["physical_max"]) for k in picks}),
                  "digital_max": sorted({int(reader.getSignalHeaders()[k]["digital_max"]) for k in picks}),
                  "prefilter": sorted({str(reader.getSignalHeaders()[k]["prefilter"]) for k in picks}),
                  "n_samples": n_samples, "original_fs": original_fs}
        pieces = []
        for block, centre in _chunk_windows(_read_chunks(reader, picks, n_samples, step)):
            filtered = contract.filter_whole(block, original_fs)[:, centre]
            pieces.append(contract.decimate(contract.average_reference(filtered), stride).astype(np.float32))
    data = np.concatenate(pieces, axis=1)
    buf = io.BytesIO()
    np.save(buf, data)
    return data, hashlib.sha256(buf.getvalue()).hexdigest(), header


def epoch_qc(ep):
    ptp = np.ptp(ep, axis=1)
    over = float(np.mean(ptp > float(QC["ptp_max_uv"])))
    flat = float(np.mean(ptp < float(QC["flat_ptp_uv"])))
    ok = np.isfinite(ep).all() and over <= float(QC["ptp_channel_fraction_max"]) and flat <= float(QC["flat_channel_fraction_max"])
    return bool(ok), over


# ----------------------------------------------------------------------------------------------- protocol stats
def protocol_stats(ev, fs, gx_rows_acc_bins):
    tg = [e for e in ev if e["kind"] == "target"]
    codes = np.array([e["code"] for e in tg])
    samples = np.array([e["sample"] for e in ev])
    ioi = np.diff(samples) / fs if len(samples) > 1 else np.array([])
    soa_t = []  # consecutive target-target within an unbroken chain
    for i in range(1, len(ev)):
        if ev[i]["kind"] == "target" and ev[i - 1]["kind"] == "target":
            soa_t.append((ev[i]["sample"] - ev[i - 1]["sample"]) / fs)
    soa_t = np.array(soa_t)
    # deviant spacing: standards between consecutive deviants inside unbroken chains
    spacing, dd = [], 0
    last_dev, cnt = None, 0
    for e in ev:
        if e["kind"] != "target":
            last_dev, cnt = None, 0
            continue
        if e["code"] == 1:
            if last_dev is not None:
                spacing.append(cnt)
                dd += int(cnt == 0)
            last_dev, cnt = e["idx"], 0
        else:
            cnt += 1
    spacing = np.array(spacing)
    # transition table P(deviant | since bin) on the full stream
    trans = {}
    for b in range(len(BINS_SINCE)):
        m = [e for e in tg if e["hist"]["bin"] == b]
        trans[str(b)] = {"n": len(m), "n_dev": int(sum(e["code"] == 1 for e in m))}
    dup = int(np.sum(np.diff(samples) == 0)) if len(samples) > 1 else 0
    nonmono = int(np.sum(np.diff(samples) < 0)) if len(samples) > 1 else 0
    unk = Counter(e["literal"] for e in ev if e["kind"] != "target")
    # unknown literals at a stimulus slot: both neighbours at a typical target SOA
    med = float(np.median(soa_t)) if len(soa_t) else float("nan")
    slot_like = 0
    for i, e in enumerate(ev):
        if e["kind"] == "target":
            continue
        g1 = (e["sample"] - ev[i - 1]["sample"]) / fs if i > 0 else None
        g2 = (ev[i + 1]["sample"] - e["sample"]) / fs if i + 1 < len(ev) else None
        if g1 is not None and g2 is not None and 0.5 * med <= g1 <= 1.5 * med and 0.5 * med <= g2 <= 1.5 * med:
            slot_like += 1
    blocks = {}
    for e in tg:
        b = int((e["sample"] / fs) // BLOCK_S)
        d = blocks.setdefault(b, {"n_std": 0, "n_dev": 0})
        d["n_std" if e["code"] == 0 else "n_dev"] += 1
    for b, d in blocks.items():
        d["dev_rate"] = d["n_dev"] / max(1, d["n_std"] + d["n_dev"])

    def q(a, p):
        return float(np.quantile(a, p)) if len(a) else None
    return {
        "n_events": len(ev), "n_targets": len(tg), "n_std": int(np.sum(codes == 0)), "n_dev": int(np.sum(codes == 1)),
        "dev_rate": float(np.mean(codes == 1)) if len(codes) else None,
        "unknown_literals": dict(unk), "n_unknown": int(sum(unk.values())), "unknown_at_stimulus_slot": slot_like,
        "duplicate_samples": dup, "nonmonotonic": nonmono,
        "soa_target_s": {"n": int(len(soa_t)), "mean": float(np.mean(soa_t)) if len(soa_t) else None, "median": q(soa_t, .5),
                         "sd": float(np.std(soa_t)) if len(soa_t) else None, "p05": q(soa_t, .05), "p95": q(soa_t, .95),
                         "min": q(soa_t, 0), "max": q(soa_t, 1)},
        "ioi_all_events_s": {"n": int(len(ioi)), "median": q(ioi, .5), "min": q(ioi, 0), "max": q(ioi, 1)},
        "spacing_hist": {str(k): int(v) for k, v in sorted(Counter(spacing.tolist()).items())},
        "spacing_n": int(len(spacing)), "spacing_min": int(spacing.min()) if len(spacing) else None,
        "spacing_max": int(spacing.max()) if len(spacing) else None,
        "spacing_mean": float(spacing.mean()) if len(spacing) else None,
        "dd_adjacent": dd, "dd_fraction": dd / len(spacing) if len(spacing) else None,
        "transition": trans,
        "blocks": {str(k): v for k, v in sorted(blocks.items())},
        "n_blocks": len(blocks),
        "block_dev_rate_min": min(d["dev_rate"] for d in blocks.values()) if blocks else None,
        "block_dev_rate_max": max(d["dev_rate"] for d in blocks.values()) if blocks else None,
        "duration_first_to_last_target_s": (tg[-1]["sample"] - tg[0]["sample"]) / fs if tg else None,
        "loader_bin_support": gx_rows_acc_bins,
    }


# ----------------------------------------------------------------------------------------------- main per record
def audit_record(kid, st, mismatch, rowwise, assets, deep):
    rid = kid["rid"]
    r = st.loc[rid]
    rec_out = {"child": kid["child"], "group": kid["group"], "rid": rid, "identity_group": kid["identity_group"],
               "n_records_child": kid["n_records_child"]}
    cnt = Counter()
    # --- D1 receipt (interval table) ---
    container = str(r["_d1_container_id"])
    rc_path = os.path.join(P, "auditory_d1", "D1_bdf_001", "receipts", f"{container}.json")
    rc = json.load(open(rc_path))
    fs, stride, rate = float(rc["original_fs"]), int(rc["stride"]), float(rc["rate_hz"])
    assert len(rc["intervals"]) == 1, "BDF: one stored interval expected"
    iv = rc["intervals"][0]
    n_original = int(rc["n_samples"]) * stride
    pre, post, guard = int(round(GX_PRE_S * rate)), int(round(GX_POST_S * rate)), int(round(GX_GUARD_S * rate))
    clock = float(r["ha_event_clock_offset_s"])
    cnt["CLOCK_OFFSET_NONZERO"] += int(clock != 0.0)
    # --- raw stream ---
    evt_path, sig_path = str(r["_event_path"]), str(r["_signal_path"])
    ev = raw_stream(evt_path, fs, n_original, stride)
    ev = recompute_history(ev, fs)
    cnt["RAW_EVENT_OUTSIDE_SIGNAL"] += sum(not e["in_signal"] for e in ev)
    for e in ev:
        s = e["sample"]
        if iv["original_start_sample"] <= s < iv["original_start_sample"] + (iv["stop"] - iv["start"]) * stride:
            off = s - iv["original_start_sample"]
            e["exported"], e["residual"] = iv["start"] + off // stride, off % stride
        else:
            e["exported"], e["residual"] = -1, None
        e["block_id"] = int((s / fs) // BLOCK_S)
        e["onset_s"] = s / fs
        e["gx_expected"] = (e["kind"] == "target" and e["exported"] >= 0 and e["exported"] - pre >= iv["start"] + guard
                            and e["exported"] + post <= iv["stop"] - guard)
    # --- ST1 event table ---
    stp = os.path.join(P, "auditory_st", "ST1_scope_001", "events", f"{rid}.parquet")
    se = pd.read_parquet(stp)
    assets[f"st_events:{kid['child']}"] = sha256_file(stp)
    if len(se) != len(ev):
        cnt["ST_ROWCOUNT"] += 1
    else:
        for e, row in zip(ev, se.itertuples()):
            h = e["hist"]
            cnt["ST_TRIAL_ID"] += int(row.trial_id != f"{rid}:e{e['idx'] + 1:05d}")
            cnt["ST_LITERAL"] += int(row.event_literal != e["literal"])
            cnt["ST_SAMPLE"] += int(int(row.onset_sample) != e["sample"])
            cnt["ST_KIND"] += int(row.event_kind != e["kind"])
            cnt["ST_LOCAL_ID"] += int(int(row.stimulus_local_id) != e["code"])
            cnt["ST_BLOCK"] += int(int(row.block_id) != e["block_id"])
            cnt["ST_EXPORTED_INDEX"] += int(int(row.exported_index) != e["exported"])
            cnt["ST_ONSET_SECONDS"] += int(abs(float(row.onset_seconds) - e["onset_s"]) > 1e-9)
            if e["kind"] == "target":
                spc = -1 if row.previous_code is None or (isinstance(row.previous_code, float) and math.isnan(row.previous_code)) else CODES.get(str(row.previous_code), -9)
                spr = -1 if row.previous_run_length != row.previous_run_length else int(row.previous_run_length)
                cnt["ST_PREV_CODE"] += int(spc != h["prev_code"])
                cnt["ST_PREV_RUN"] += int(spr != h["prev_run"])
                sg = row.previous_gap_s
                cnt["ST_PREV_GAP"] += int((h["gap_s"] is None) != (sg != sg) or (h["gap_s"] is not None and abs(sg - h["gap_s"]) > 1e-9))
                cnt["ST_STATUS"] += int(row.history_status != h["status"])
                pid = row.previous_event_id
                if isinstance(pid, str) and pid:
                    pidx = int(pid.split(":e")[-1]) - 1
                    cnt["ST_PREV_ID"] += int(pidx != h["prev_idx"])
                    cnt["ST_PREV_ID_NOT_PAST"] += int(pidx >= e["idx"])
                    e["st_prev_idx"] = pidx
                else:
                    cnt["ST_PREV_ID"] += int(h["prev_idx"] is not None)
                    e["st_prev_idx"] = None
    # --- GX epochs ---
    gxp = os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{rid}.npz")
    assets[f"gx_epochs:{kid['child']}"] = sha256_file(gxp)
    z = np.load(gxp)
    cnt["GX_GEOMETRY"] += int(not (float(z["rate_hz"]) == rate == 250.0 and int(z["pre_samples"]) == pre == 50
                                   and int(z["post_samples"]) == post == 150 and float(z["original_fs"]) == fs
                                   and z["x"].shape[1:] == (20, pre + post)))
    exp_rows = [e for e in ev if e["gx_expected"]]
    tid = [str(t) for t in z["trial_id"]]
    exp_tid = [f"{rid}:e{e['idx'] + 1:05d}" for e in exp_rows]
    if tid != exp_tid:
        cnt["GX_ROWSET"] += 1
        common = set(tid) & set(exp_tid)
        cnt["GX_ROWSET_MISSING"] += len(set(exp_tid) - common)
        cnt["GX_ROWSET_EXTRA"] += len(set(tid) - common)
    by_idx = {int(t.split(":e")[-1]) - 1: g for g, t in enumerate(tid)}
    acc = z["accepted"].astype(bool)
    stored_since = hist_codes(z["previous_code"], z["previous_run_length"])["since_last_deviant"]
    for e in ev:
        e["gx_row"] = by_idx.get(e["idx"])
        e["accepted"] = bool(acc[e["gx_row"]]) if e["gx_row"] is not None else False
    for e in exp_rows:
        g = e["gx_row"]
        if g is None:
            continue
        h = e["hist"]
        y = int(z["y"][g])
        bad = {
            "GX_Y": y != e["code"],
            "GX_ONSET": abs(float(z["onset_seconds"][g]) - e["onset_s"]) > 1e-9,
            "GX_BLOCK": int(z["block_id"][g]) != e["block_id"],
            "GX_PREV_CODE": int(z["previous_code"][g]) != h["prev_code"],
            "GX_PREV_RUN": int(z["previous_run_length"][g]) != h["prev_run"],
            "GX_PREV_GAP": abs(float(z["previous_gap_s"][g]) - (h["gap_s"] if h["gap_s"] is not None else -1.0)) > 1e-9,
            "GX_STATUS": str(z["history_status"][g]) != h["status"],
            "GX_HIST_BIN": int(stored_since[g]) != h["bin"],
        }
        for k, v in bad.items():
            cnt[k] += int(v)
            if acc[g]:
                cnt[k + "_ACCEPTED"] += int(v)
        e["stored"] = {"y": y, "prev_code": int(z["previous_code"][g]), "prev_run": int(z["previous_run_length"][g]),
                       "bin": int(stored_since[g]), "status": str(z["history_status"][g]),
                       "gap_s": float(z["previous_gap_s"][g])}
    # negative control: an after-event (leaky) history that includes the current label must NOT match the stored one
    leak_match, before_match = 0, 0
    for e in exp_rows:
        if e["gx_row"] is None:
            continue
        h = e["hist"]
        leaky = 0 if e["code"] == 1 else (h["since"] + 1 if h["since"] >= 0 else -1)
        leak_match += int(since_bin(leaky) == int(stored_since[e["gx_row"]]))
        before_match += int(h["bin"] == int(stored_since[e["gx_row"]]))
    # history must use QC-dropped stimuli: compare with an accepted-only chain
    acc_idx = {e["idx"] for e in ev if e["accepted"]}
    ao = accepted_only_since(ev, acc_idx)
    diff_ao = sum(1 for e in ev if e["idx"] in acc_idx and ao[e["idx"]] != e["hist"]["since"])
    prev_dropped = sum(1 for e in ev if e["idx"] in acc_idx and e["hist"]["prev_idx"] is not None
                       and not ev[e["hist"]["prev_idx"]]["accepted"])
    # --- signal-level alignment, QC and scale from the raw signal (D1 regenerated in memory) ---
    t0 = time.time()
    data, d1_sha, header = regenerate_d1(sig_path)
    cnt["D1_LENGTH"] += int(data.shape[1] != int(rc["n_samples"]))
    cnt["D1_SHA_DIFFERS_FROM_DELETED_ARRAY"] += int(DELETED.get(f"D1_bdf_001/arrays/{container}.npy") != d1_sha)
    x = z["x"]
    scale = float(z["record_scale"])
    rows = [e for e in exp_rows if e["gx_row"] is not None]
    lag_best, rmse_rel, qc_flip, over_diff, margins = [], [], 0, [], []
    rec_acc = np.zeros(len(rows), bool)
    raw_abs = []
    for j, e in enumerate(rows):
        g, c0 = e["gx_row"], e["exported"]
        A = x[g].astype(np.float32)
        m = np.abs(A) < 59.5
        cors = []
        for L in LAGS:
            lo, hi = c0 + L - pre, c0 + L + post
            if lo < 0 or hi > data.shape[1]:
                cors.append(-np.inf)
                continue
            B = data[:, lo:hi] / scale
            a, b = A[m], B[m]
            cors.append(float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else -np.inf)
        lb = int(LAGS[int(np.argmax(cors))])
        lag_best.append(lb)
        c0i = int(np.flatnonzero(LAGS == 0)[0])
        margins.append(cors[c0i] - max(c for i_, c in enumerate(cors) if i_ != c0i))
        ep = data[:, c0 - pre:c0 + post]
        B0 = ep / scale
        rmse_rel.append(float(np.sqrt(np.mean((A[m] - B0[m]) ** 2)) / max(1e-12, np.sqrt(np.mean(A[m] ** 2)))))
        ok, over = epoch_qc(ep)
        rec_acc[j] = ok
        over_diff.append(abs(over - float(z["qc_over_fraction"][g])))
        qc_flip += int(ok != bool(acc[g]))
        if ok:
            raw_abs.append(np.abs(ep).ravel())
        e["signal"] = {"best_lag": lb, "rmse_rel": rmse_rel[-1], "qc_recomputed": ok}
    scale_re = float(np.median(np.concatenate(raw_abs))) if raw_abs else float("nan")
    lag_best = np.array(lag_best)
    rmse_rel = np.array(rmse_rel)
    cnt["SIGNAL_LAG_NONZERO"] += int(np.sum(lag_best != 0))
    cnt["SIGNAL_VALUE_RMSE_GT_1PCT"] += int(np.sum(rmse_rel > 0.01))
    cnt["QC_ACCEPT_FLIP"] += qc_flip
    cnt["SCALE_REL_DIFF_GT_1E-4"] += int(abs(scale_re - scale) / scale > 1e-4)
    del data
    # residual of the 250 Hz zero sample relative to the 1000 Hz trigger
    resid = [e["residual"] for e in rows]
    rec_out.update(
        fs=fs, stride=stride, rate=rate, pre=pre, post=post, guard=guard, clock_offset_s=clock,
        n_raw=len(ev), n_targets=sum(e["kind"] == "target" for e in ev),
        n_gx_expected=len(exp_rows), n_gx_stored=len(tid), n_accepted=int(acc.sum()),
        n_no_epoch_support=sum(1 for e in ev if e["kind"] == "target" and not e["gx_expected"]),
        n_qc_rejected=int((~acc).sum()),
        history_accepted_only_variant_differs=diff_ao, accepted_rows_whose_previous_sound_was_dropped=prev_dropped,
        signal={"lag_hist": {str(k): int(v) for k, v in sorted(Counter(lag_best.tolist()).items())},
                "rmse_rel_median": float(np.median(rmse_rel)) if len(rmse_rel) else None,
                "rmse_rel_max": float(np.max(rmse_rel)) if len(rmse_rel) else None,
                "qc_flip": qc_flip, "qc_over_absdiff_max": float(max(over_diff)) if over_diff else None,
                "scale_stored": scale, "scale_recomputed": scale_re,
                "d1_regenerated_sha256": d1_sha, "d1_deleted_array_sha256": DELETED.get(f"D1_bdf_001/arrays/{container}.npy"),
                "corr_margin_lag0_min": float(min(margins)) if margins else None,
                "corr_margin_lag0_median": float(np.median(margins)) if margins else None,
                "seconds": time.time() - t0},
        history_controls={"stored_bin_equals_before_event": before_match, "stored_bin_equals_after_event_leaky": leak_match,
                          "n_epochs": sum(1 for e in exp_rows if e["gx_row"] is not None)},
        header=header, residual_samples_hist={str(k): int(v) for k, v in sorted(Counter(resid).items())},
        record_scale=scale, accept_fraction=float(acc.mean()), d1_seconds=float(rc["seconds"]),
        n_channels=int(z["n_channels"]), source_cohort_evidence=str(z["source_cohort_evidence"]),
        ha_index_recording_flag=str(r["ha_index_recording_flag"]), ha_index_hold_reason=str(r["ha_index_hold_reason"]),
        pf_counts={k: (int(kid["pf_row"][k]) if kid["pf_row"][k] == kid["pf_row"][k] else None) for k in ("n_epochs", "n_acc", "n_std", "n_dev")},
    )
    cnt["PF_COUNTS"] += int(rec_out["pf_counts"]["n_epochs"] != len(tid) or rec_out["pf_counts"]["n_acc"] != int(acc.sum())
                            or rec_out["pf_counts"]["n_dev"] != int(np.sum(z["y"][acc] == 1)))
    assets[f"raw_events:{kid['child']}"] = sha256_file(evt_path)
    assets[f"raw_signal:{kid['child']}"] = sha256_file(sig_path)
    assets[f"d1_receipt:{kid['child']}"] = sha256_file(rc_path)
    # bins among accepted rows used by the loader (since >= 0)
    acc_bins = Counter(e["hist"]["bin"] for e in ev if e["accepted"] and e["hist"]["bin"] >= 0)
    rec_out["protocol"] = protocol_stats(ev, fs, {str(k): int(v) for k, v in sorted(acc_bins.items())})
    rec_out["n_loader_expected"] = int(sum(acc_bins.values()))
    rec_out["mismatch"] = dict(cnt)
    for e in ev:
        h = e["hist"]
        rowwise.append({"child": kid["child"], "rid": rid, "idx": e["idx"], "literal": e["literal"], "sample": e["sample"],
                        "kind": e["kind"], "code": e["code"], "block_id": e["block_id"], "exported": e["exported"],
                        "gx_expected": e["gx_expected"], "gx_row": -1 if e["gx_row"] is None else e["gx_row"],
                        "accepted": e["accepted"], "re_prev_code": h["prev_code"], "re_prev_run": h["prev_run"],
                        "re_since": h["since"], "re_bin": h["bin"], "re_status": h["status"],
                        "re_gap_s": np.nan if h["gap_s"] is None else h["gap_s"],
                        "st_prev_idx": -1 if e.get("st_prev_idx") is None else e["st_prev_idx"],
                        "gx_y": e.get("stored", {}).get("y", -9), "gx_bin": e.get("stored", {}).get("bin", -9),
                        "gx_prev_code": e.get("stored", {}).get("prev_code", -9),
                        "gx_prev_run": e.get("stored", {}).get("prev_run", -9),
                        "sig_lag": e.get("signal", {}).get("best_lag", -99),
                        "sig_rmse_rel": e.get("signal", {}).get("rmse_rel", np.nan),
                        "qc_recomputed": e.get("signal", {}).get("qc_recomputed", None)})
    for k, v in cnt.items():
        mismatch[k] += v
    if deep:
        rec_out["_events"] = ev  # full private trace for the deep-dive child
    return rec_out


def loader_check(records, mismatch):
    """Run the actual loader chain and compare it with the raw recomputation (rows: accepted & since >= 0)."""
    from auditory_alignment_v3.aln35 import support_contract as SC
    from auditory_alignment_v3.aln35 import support_runtime as SR
    kids = SR.load_kids()
    out = {}
    by = {r["child"]: r for r in records}
    assert sorted(k["id"] for k in kids) == sorted(by), "loader roster differs from PF eligibility roster"
    for k in kids:
        r = by[k["id"]]
        ev = r["_ev_min"]
        rows = [e for e in ev if e["accepted"] and e["re_bin"] >= 0]
        c = Counter()
        c["LOADER_ROWCOUNT"] += int(len(rows) != len(k["y"]))
        if len(rows) == len(k["y"]):
            y = np.array([e["code"] for e in rows]); b = np.array([e["re_bin"] for e in rows])
            blk = np.array([e["block_id"] for e in rows]); on = np.array([e["sample"] / r["fs"] for e in rows])
            c["LOADER_Y"] += int(np.sum(y != k["y"]))
            c["LOADER_BIN"] += int(np.sum(b != k["bin"]))
            c["LOADER_BLOCK"] += int(np.sum(blk != k["block"]))
            c["LOADER_ONSET"] += int(np.sum(np.abs(on - k["_s35_onset_seconds"]) > 1e-9))
        # x rows: loader x must equal per-record z-scoring of stored accepted rows with since >= 0, same order
        with np.load(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{k['rid']}.npz")) as z:
            acc = z["accepted"].astype(bool)
            hs = hist_codes(z["previous_code"][acc], z["previous_run_length"][acc])["since_last_deviant"]
            xs = z["x"][acc].astype(np.float32)[hs >= 0]
        mu = xs.mean(axis=(0, 2), keepdims=True); sd = xs.std(axis=(0, 2), keepdims=True); sd[sd == 0] = 1
        c["LOADER_X_ROWS"] += int(xs.shape != k["x"].shape or not np.allclose((xs - mu) / sd, k["x"], atol=1e-5))
        # support/query guard (aln35.support_contract.private_split as used by aln41/support.py and aln36)
        s = SC.private_split(k)
        pool, q = np.asarray(s["pool"]), np.asarray(s["query"])
        on_raw = np.array([e["sample"] for e in rows]) / r["fs"] if len(rows) == len(k["y"]) else k["_s35_onset_seconds"]
        exp_idx = np.array([e["exported"] for e in rows]) if len(rows) == len(k["y"]) else None
        g = {"n_available": int(s["original_n"]), "n_blocks": int(s["original_block_n"]), "n_pool": int(len(pool)),
             "n_query": int(len(q)), "n10": int(s["n10"]), "guard_excluded": int(len(s["guard_excluded"])),
             "boundary_removed_support": len(s["boundary_removed_support"]), "boundary_removed_query": len(s["boundary_removed_query"])}
        if len(pool) and len(q):
            g["latest_support_end_s_minus_first_query_start_s"] = float(on_raw[pool].max() + 0.6 - (on_raw[q].min() - 0.2))
            g["overlap_count"] = int(sum(np.any((on_raw[q] - 0.2 < t + 0.6) & (on_raw[q] + 0.6 > t - 0.2)) for t in on_raw[pool]))
            if exp_idx is not None:
                g["latest_support_end_sample"] = int(exp_idx[pool].max() + 150)
                g["earliest_query_start_sample"] = int(exp_idx[q].min() - 50)
                g["sample_disjoint"] = bool(g["latest_support_end_sample"] <= g["earliest_query_start_sample"])
            g["block_intersection"] = len(set(k["block"][pool]) & set(k["block"][q]))
        else:
            g["overlap_count"] = 0
        c["GUARD_VIOLATION"] += int(g.get("overlap_count", 0) > 0 or g.get("block_intersection", 0) > 0
                                    or g.get("sample_disjoint", True) is False)
        g["query_hash"] = SR.serial_split(s, k["id"])["query_hash"]
        g["pool_hash"] = SR.serial_split(s, k["id"])["pool_hash"]
        g["fold"] = int(k["fold"]); g["es_rows"] = int(k["es_mask"].sum())
        g["pool_rows"] = pool.tolist(); g["query_rows"] = q.tolist(); g["es_mask"] = k["es_mask"].astype(int).tolist()
        out[k["id"]] = {"counts": dict(c), "guard": g, "geometry_sha256": k["_s35_geometry_sha256"]}
        for kk, v in c.items():
            mismatch[kk] += v
    return out


def main():
    t0 = time.time()
    kids = cohort()
    assert len(kids) == 64
    only = [a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--only=")]
    if only:  # debugging subset: prints only, writes nothing
        kids = [k for k in kids if k["child"] in only[0]]
    st = pd.read_parquet(os.path.join(P, "auditory_st", "ST1_scope_001", "records.parquet")).set_index("record_id")
    mismatch, rowwise, assets, records = Counter(), [], {}, []
    for kid in kids:
        rec = audit_record(kid, st, mismatch, rowwise, assets, deep=kid["child"] == CHILD_DEEP)
        rec["_ev_min"] = [{"idx": r["idx"], "code": r["code"], "accepted": r["accepted"], "re_bin": r["re_bin"],
                           "block_id": r["block_id"], "sample": r["sample"], "exported": r["exported"]}
                          for r in rowwise if r["child"] == kid["child"]]
        records.append(rec)
        print(f"{kid['child']} done {time.time() - t0:.0f}s mism={ {k: v for k, v in rec['mismatch'].items() if v} } "
              f"lag={rec['signal']['lag_hist']} rmse={rec['signal']['rmse_rel_max']:.2e} qcflip={rec['signal']['qc_flip']}", flush=True)
    if only:
        print("TEST", dict(mismatch), {r["child"]: r["protocol"]["n_events"] for r in records})
        return
    loader = loader_check(records, mismatch)
    deep = next(r for r in records if r["child"] == CHILD_DEEP)
    deep_ev = deep.pop("_events")
    for r in records:
        r.pop("_ev_min", None)
        r["loader"] = loader[r["child"]]
    pd.DataFrame(rowwise).to_parquet(os.path.join(OUT, "cohort_rowwise_private.parquet"), index=False)
    json.dump({"records": records, "mismatch_total": dict(mismatch), "assets_sha256": assets,
               "code_sha256": {p: sha256_file(os.path.join(REPO, p)) for p in CODE_FILES},
               "rules": {"codes": CODES, "block_seconds": BLOCK_S, "gx_pre_s": GX_PRE_S, "gx_post_s": GX_POST_S,
                         "gx_guard_s": GX_GUARD_S, "bins_since": BINS_SINCE, "qc": QC},
               "seconds": time.time() - t0},
              open(os.path.join(OUT, "audit_records_private.json"), "w"), indent=1, default=str)
    json.dump(deep_ev, open(os.path.join(OUT, "child60_events_private.json"), "w"), default=str)
    for f in ("cohort_rowwise_private.parquet", "audit_records_private.json", "child60_events_private.json"):
        os.chmod(os.path.join(OUT, f), 0o600)
    print("TOTAL", dict(mismatch), f"{time.time() - t0:.0f}s", flush=True)


CODE_FILES = ["archive/auditory_st/events.py", "archive/auditory_st/features.py", "archive/configs/auditory_st_v1.yaml",
              "auditory5/events.py", "auditory_gx/stage.py", "configs/auditory_gx_v1.yaml", "auditory_d1/export_bdf.py",
              "auditory_d1/export.py", "auditory_d1/contract.py", "auditory_c3/private_mi.py", "auditory_c3/private_mi2.py",
              "auditory_c3/c3dl/hc.py", "auditory_alignment/data.py", "auditory_alignment_v3/aln35/support_contract.py",
              "auditory_alignment_v3/aln35/support_runtime.py", "auditory_alignment_v3/aln41/support.py"]

if __name__ == "__main__":
    main()
