"""ALN3.4 R34_TF_L1_PANEL: true-full FM vs the same-access local L1 across seeds, interim TF-INIT, and a pairing audit.

Analysis note (written before this file computed anything): private/auditory_alignment_v3/aln34/TF_L1_NOTE.md.

Roles (NCE, d = 32; fau / dtu / federici; seeds 3401 breadth, 3407 / 3413 panel):
  L0  A_LOCAL lag_local_tokens window full                 audit only (access extension)
  L1  ALN32_LOCAL_SUPPORT local_aligned1000                reference of TF-LOCAL (same EEG access as TF)
  TF  ALN32_TRUE_FULL (backbone, init, recipe, lr)         one-step in every seed; warm-up registered for seed 3401 only
Contrasts (positive = candidate lower true-query risk; dR = R(reference) - R(candidate), bits per 5 s query):
  TF-LOCAL  L1 -> TF {random_full, pretrained_full} x lr {1e-5, 3e-4}: per seed, identity mean over seeds, between-seed range
            (new exploratory paired summary; TF-LOCAL is not an ADDENDUM_11 role)
  TF-INIT   TF random_full -> pretrained_full per lr and backbone: per seed only, INTERIM (ADDENDUM_11's frozen role
            initialization_true_full is computed by aln32_panel_interim.py once the panel completes; not replaced here)
Readouts: unified/regular/logloss_bits (primary) and native/regular/logloss_bits (separate families).
Inference: bc_interim.run_family / sci_r1.stats (identity-level bootstrap-t, B = 4000, max-t within a declared
dataset x backbone [x seed] family). An identity enters a contrast only if every fold cell it appears in is
pair-complete; no partial-cell averaging, no zero filling.
Checks: per complete pair record rows, split, target, evaluation, access and initialization (backbone_contract); seed 3401 against the
frozen ADDENDUM_07 analysis (aln32_wave1.json): point estimates of the declared families, and the frozen families recomputed with their own
labels and members (bootstrap replicates are seeded by the family label, so the declared families' intervals differ by Monte Carlo error;
analysis note, Correction 1).

Read-only on plan rows, unit records, queue files and claims; writes only RES/tf_l1_pairs.json and
DOCS/TRUE_FULL_PAIRED_EVIDENCE.md (mode 600, atomic replace). Deterministic: rerun as the panel completes.
Usage: python -B -m auditory_alignment_v3.aln34.tf_l1_pairs [--no-doc]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import time
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3.sci_r1 import stats as S

RES = os.environ.get("TFL1_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln34", "tf_l1"))
DOCS = os.environ.get("TFL1_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
DOC_NAME = "TRUE_FULL_PAIRED_EVIDENCE.md"
JSON_NAME = "tf_l1_pairs.json"
FROZEN_WAVE1 = os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln32_wave1", "aln32_wave1.json")
NOTE = "private/auditory_alignment_v3/aln34/TF_L1_NOTE.md"

SEEDS = (3401, 3407, 3413)
BREADTH = 3401
DS, ARCH = BI.DS, BI.ARCH
INITS = ("random_full", "pretrained_full")
ONESTEP, WARMUP = "full_onestep_v1", "warmup_then_all_v1"
RECIPES = (ONESTEP, WARMUP)
RTAG = {ONESTEP: "onestep", WARMUP: "warmup"}
LRS = (1e-5, 3e-4)
READOUTS = (("unified", "unified/regular/logloss_bits"), ("native", "native/regular/logloss_bits"))
METRICS = tuple(m for _, m in READOUTS)
FAMILY = {"L0": "A_LOCAL", "L1": "ALN32_LOCAL_SUPPORT", "TF": "ALN32_TRUE_FULL"}
COMPLETE, PENDING_ST, MISSING_ST = "complete", ("running", "queued", "no_queue_entry"), ("technical_failed", "failed_marker", "held", "deferred")
REL_TOL = 1e-6
EVAL_FILES = (("auditory_alignment", "evaluate.py"), ("auditory_alignment_v2", "evaluate.py"))

FIELD_DERIVATION = {
    "dataset, subject_fold, content_fold, seed": "record row and bound_row against the plan row (content_fold None -> 0 as core.bind); all three must agree",
    "split_fingerprint": "closest verifiable equivalent of split_hash (not written by the runners): sha256 of dataset, subject_fold, content_fold, "
                         "n_train_participants, n_fit_segments, n_es_segments, eval.readout.n_test_candidates and the sorted (test record id, "
                         "n_candidates, n_queries) of unified/regular. Code: the split is train_participants(subject_fold) + data.load_*(content_fold) "
                         "roles and does not depend on the seed; must be identical for every complete record of a fold cell",
    "target_fingerprint": "closest verifiable equivalent of target_hash: sha256 of spec.target, record target_contract, resolved d, grid_samples, fs and "
                          "the audio head (bound_row.spec.audio_head; fixed_features is also hard-coded in fm_aligned32.fit_aligned32), plus "
                          "objective_calibration sigma_v / ridge_v compared with relative tolerance 1e-6 (deterministic training-side statistics of the "
                          "target head on the seed's calibration rows: projection seeded per cohort, standardisation rng(seed + 5), calibration batch "
                          "rng(seed + 99 / 98) in both trainers); seed-specific by design",
    "access_contract": "normalised (support, window [a, b) in native samples relative to the query, mask). L1: resolved_config.support, windows_samples, "
                       "resolved_config.mask; TF: resolved_config.input_support, window_s x fs (b - a = window_native_samples), mask from code "
                       "(fm_aligned.aligned_windows: zero before the segment start); L0: windows_samples [0, post) = post600. Both model types read every "
                       "cohort channel (code: Backbone uses CHANNELS[dataset], the local encoder coh.n_ch)",
    "evaluation_version": "evaluator ev2.evaluate_continuous -> ev1.evaluate_continuous (unified ridge bridge + native score, rng(seed + 1000)) on the "
                          "dense grid (grid_samples), sha256 of auditory_alignment/evaluate.py + auditory_alignment_v2/evaluate.py; valid only if the "
                          "record's code_hash equals core.code_hash(family) recomputed now (hashed files incl. both evaluate.py byte-identical)",
    "initialization (declared difference of TF-INIT)": "record backbone_contract.arch and backbone_contract.adaptation (random_full / pretrained_full) must "
                          "equal the configuration, and backbone_contract.init_state_loaded must be null: that field records only donor init_state "
                          "weights (auditory_alignment_v2/foundation_adapter.py Backbone.__init__); public pretrained weights load through the "
                          "adaptation flag (CBraMod strict load_state_dict of the published weights, REVE AutoModel.from_pretrained; random init "
                          "from_config). Local sides (L0/L1) must have an encoder record and no backbone_contract. Added in Correction 1 of the note",
}


# ------------------------------------------------------------------------------------------------ small helpers
def sha16(obj):
    return hashlib.sha256(json.dumps(BI.jl(obj), sort_keys=True).encode()).hexdigest()[:16]


def file_sha(*parts):
    h = hashlib.sha256()
    for d, f in parts:
        h.update(open(os.path.join(core.REPO, d, f), "rb").read())
    return h.hexdigest()[:16]


def ck(c):
    return "|".join(f"{x:g}" if isinstance(x, float) else str(x) for x in c)


def role_of(r):
    """plan row -> configuration (kind, dataset, *params, seed) or None."""
    s, f, ds, sd = r["spec"], r["family_id"], r["dataset"], r["seed"]
    if ds not in DS or sd not in SEEDS or s.get("objective") != "NCE":
        return None
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L0", ds, sd)
    if f == "ALN32_LOCAL_SUPPORT" and s.get("variant") == "local_aligned1000":
        return ("L1", ds, sd)
    if f == "ALN32_TRUE_FULL":
        return ("TF", ds, s["architecture"], s["adaptation"], s["recipe"], float(s["lr_backbone"]), sd)
    return None


def cell_of(r):
    return (int(r["subject_fold"]), int(r["content_fold"]) if r["content_fold"] is not None else 0)


def live_state(out=None):
    """read-only snapshot of holds, deferrals, failure markers, claims (running) and queue files."""
    out = out or core.OUT
    j = lambda p, k="ids": set(json.load(open(p))[k]) if os.path.exists(p) else set()
    running = {os.path.basename(p).split(".")[0] for p in glob.glob(os.path.join(out, "pool", "*", "*.claim"))}
    queued = set()
    for q in glob.glob(os.path.join(out, "queue_*.txt")):
        if q.endswith("_weights.txt"):
            continue
        for line in open(q):
            if line.strip():
                queued.add(line.split("|")[0].strip())
    failed = {os.path.basename(p)[:-len(".FAILED.json")] for p in glob.glob(os.path.join(out, "units", "*.FAILED.json"))}
    defer = j(os.path.join(out, "governance", "deferred_redundant_v30_panel.json")) if not os.path.exists(os.path.join(out, "PANEL_V30_RESUME")) else set()
    fam_hold = set(json.load(open(os.path.join(out, "families_on_hold.json")))) if os.path.exists(os.path.join(out, "families_on_hold.json")) else set()
    return {"held": j(os.path.join(out, "governance", "held_executions.json")), "families_on_hold": fam_hold, "deferred": defer,
            "running": running, "queued": queued, "failed_marker": failed}


def unit_status(row, rec, live):
    eid = row["experiment_id"]
    if rec is not None:
        return COMPLETE if rec.get("status") == COMPLETE else "technical_failed"
    if eid in live["failed_marker"]:
        return "failed_marker"
    if eid in live["held"] or row["family_id"] in live["families_on_hold"]:
        return "held"
    if eid in live["deferred"]:
        return "deferred"
    if eid in live["running"]:
        return "running"
    if eid in live["queued"]:
        return "queued"
    return "no_queue_entry"


# ------------------------------------------------------------------------------------------------ fingerprints
def access_of(rec, kind):
    rc = rec.get("resolved_config") or {}
    if kind in ("L0", "L1"):
        w = rec.get("windows_samples") or []
        if len(w) != 1:
            return {"support": None, "window_samples": None, "mask": None, "source": "record windows_samples malformed"}
        a, b = (int(x) for x in w[0])
        if kind == "L1":
            mask = "zero_before_segment_start" if rc.get("mask") == "zero before the anchor's segment start" else rc.get("mask")
            return {"support": rc.get("support"), "window_samples": [a, b], "mask": mask, "source": "record resolved_config.support / windows_samples / mask"}
        return {"support": "post600" if a == 0 else None, "window_samples": [a, b], "mask": "not_applicable_window_starts_at_query",
                "source": "record windows_samples (A_LOCAL lag_local_tokens full)"}
    fs, ws, n = rc.get("fs"), rec.get("window_s") or rc.get("window_s"), rec.get("window_native_samples")
    if not fs or not ws:
        return {"support": rc.get("input_support"), "window_samples": None, "mask": None, "source": "record window fields missing"}
    a, b = -int(round(-ws[0] * fs)), int(round(ws[1] * fs))
    ok = n is None or (b - a) == int(n)
    return {"support": rc.get("input_support"), "window_samples": [a, b] if ok else None, "mask": "zero_before_segment_start",
            "source": "record resolved_config.input_support / window_s x fs / window_native_samples; mask from code fm_aligned.aligned_windows"}


def fingerprints(rec, kind, row, code_now, eval_sha):
    """-> (fingerprint dict, [(test record id, n_candidates, n_queries)])."""
    rr, br = rec.get("row") or {}, rec.get("bound_row") or {}
    sf, cf = cell_of(row)
    consistent = (rr.get("experiment_id") == row["experiment_id"] and rr.get("family_id") == row["family_id"] and rr.get("spec") == row["spec"]
                  and all(rr.get(k) == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed"))
                  and br.get("dataset") == row["dataset"] and br.get("subject_fold") == sf and br.get("content_fold") == cf and br.get("seed") == row["seed"])
    ev = rec.get("eval") or {}
    pp = ev.get("per_participant") or {}
    test = sorted((pid, int(v["unified/regular"]["n_candidates"]), int(v["unified/regular"]["n_queries"])) for pid, v in pp.items())
    split = {"dataset": row["dataset"], "subject_fold": sf, "content_fold": cf, "n_train_participants": rec.get("n_train_participants"),
             "n_fit_segments": rec.get("n_fit_segments"), "n_es_segments": rec.get("n_es_segments"),
             "n_test_candidates": (ev.get("readout") or {}).get("n_test_candidates"), "test": test}
    rc, oc = rec.get("resolved_config") or {}, rec.get("objective_calibration") or {}
    target = {"target": (rr.get("spec") or {}).get("target"), "target_contract": rec.get("target_contract"), "d": rc.get("d"),
              "grid_samples": rc.get("grid_samples"), "fs": rc.get("fs"), "audio_head": (br.get("spec") or {}).get("audio_head")}
    acc = access_of(rec, kind)
    bc = rec.get("backbone_contract")
    backbone = None if bc is None else {"arch": bc.get("arch"), "adaptation": bc.get("adaptation"), "init_state_loaded": bc.get("init_state_loaded")}
    readouts = sorted({k.split("/")[0] for v in pp.values() for k in v if k.endswith("/regular")})
    evaluation = {"evaluator": "auditory_alignment_v2.evaluate.evaluate_continuous", "grid_samples": rc.get("grid_samples"), "readouts": readouts,
                  "eval_code_sha16": eval_sha}
    fp = {"row_consistent": bool(consistent), "split": sha16(split), "n_test_records": len(test), "n_train_participants": split["n_train_participants"],
          "target": sha16(target), "target_fields": target, "target_stats": [oc.get("sigma_v"), oc.get("ridge_v")],
          "access": {k: acc[k] for k in ("support", "window_samples", "mask")}, "access_key": sha16({k: acc[k] for k in ("support", "window_samples", "mask")}),
          "access_source": acc["source"], "evaluation": sha16(evaluation), "code_group": rec.get("code_group"), "code_hash": rec.get("code_hash"),
          "code_hash_reproduced": rec.get("code_hash") == code_now.get(FAMILY[kind]), "information_stratum": rec.get("information_stratum"),
          "base_plan_row": row.get("base_plan_row"), "logical_dependencies": row.get("logical_dependencies", []),
          "backbone": backbone, "local_encoder": rec.get("encoder") is not None}
    return fp, test


def init_ok(fp, cfg):
    """the record realises the configured initialization: TF backbone_contract arch / adaptation equal the configuration and no donor
    init_state was loaded; a local side (L0 / L1) has an encoder record and no backbone_contract."""
    b = fp.get("backbone")
    if cfg[0] != "TF":
        return b is None and bool(fp.get("local_encoder"))
    return b is not None and b.get("arch") == cfg[2] and b.get("adaptation") == cfg[3] and b.get("init_state_loaded") is None


def close(a, b, tol=REL_TOL):
    if a is None or b is None:
        return False
    return all(x is not None and y is not None and abs(x - y) <= tol * max(abs(x), abs(y), 1e-12) for x, y in zip(a, b))


def rel_dev(a, b):
    if a is None or b is None or None in a or None in b:
        return None
    return max(abs(x - y) / max(abs(x), abs(y), 1e-12) for x, y in zip(a, b))


# ------------------------------------------------------------------------------------------------ scan
def scan(rows, load, manifest, live, code_now, eval_sha):
    """plan rows -> units (status, fingerprints), (configuration, cell) index, per-cell identity metric lists, split map."""
    from auditory_alignment.aggregate import unit_rows
    units, index, values, notes = {}, {}, {}, []
    split_ids = defaultdict(dict)  # (ds, cell) -> {split fingerprint: set of test record ids}
    kind_of = {}
    cells = defaultdict(set)
    for r in rows:
        c = role_of(r)
        if c is None:
            continue
        cell = cell_of(r); ds = c[1]
        cells[ds].add(cell)
        key = (c, cell)
        if key in index:
            raise ValueError(f"ambiguous duplicate rows {index[key]} / {r['experiment_id']} for {ck(c)} cell {cell}; deduplicate by provenance, not by score")
        index[key] = r["experiment_id"]
        rec = load(r["experiment_id"])
        st = unit_status(r, rec, live)
        u = {"cfg": ck(c), "kind": c[0], "dataset": ds, "seed": c[-1], "cell": list(cell), "status": st, "seed_scope": r.get("seed_scope"),
             "registered": r.get("registered")}
        if st == COMPLETE:
            fp, test = fingerprints(rec, c[0], r, code_now, eval_sha)
            u["fp"] = fp
            u["initialization_ok"] = init_ok(fp, c)
            u["n_params"] = ({"backbone": (rec.get("backbone_contract") or {}).get("n_params"), "readout": rec.get("readout_params")} if c[0] == "TF"
                             else {"encoder": (rec.get("encoder") or {}).get("n_params")})
            split_ids[(ds, cell)].setdefault(fp["split"], set()).update(pid for pid, _, _ in test)
            per = defaultdict(lambda: defaultdict(list))
            for pid, v in unit_rows(rec).items():
                if ds == "federici":
                    if pid not in manifest:
                        raise KeyError(f"Federici record {pid} not in entity manifest")
                    ident, _, k = manifest[pid]
                else:
                    ident, k = pid, "human"
                kind_of[(ds, ident)] = k
                if k != "human":
                    continue
                for m in METRICS:
                    x = v.get(m)
                    if x is not None:
                        per[ident][m].append(float(x))
            values[key] = {i: dict(d) for i, d in per.items()}
        units[r["experiment_id"]] = u
    # split map: one fingerprint per fold cell (all complete records of all roles and seeds)
    split_map, split_bad = {}, []
    for (ds, cell), d in split_ids.items():
        if len(d) != 1:
            split_bad.append(f"{ds} cell {cell}: {len(d)} different split fingerprints among complete records")
        split_map[(ds, cell)] = set().union(*d.values())
    ident_cells = defaultdict(lambda: defaultdict(set))
    for (ds, cell), pids in split_map.items():
        for pid in pids:
            if ds == "federici":
                if pid not in manifest:
                    raise KeyError(f"Federici record {pid} not in entity manifest")
                ident, _, k = manifest[pid]
            else:
                ident, k = pid, "human"
            if k == "human":
                ident_cells[ds][ident].add(cell)
    for ds in DS:
        missing_cells = sorted(c for c in cells[ds] if (ds, c) not in split_map)
        if missing_cells:
            notes.append(f"{ds}: no complete record in cells {missing_cells}; their test identities are unknown, identities there cannot be complete")
    n_phantom = {ds: len({i for (d, i), k in kind_of.items() if d == ds and k != "human"}) for ds in DS}
    return {"units": units, "index": index, "values": values, "split_map": split_map, "split_bad": split_bad,
            "ident_cells": {ds: {i: sorted(c) for i, c in d.items()} for ds, d in ident_cells.items()}, "cells": {ds: sorted(c) for ds, c in cells.items()},
            "n_phantom_entities": n_phantom, "notes": notes}


# ------------------------------------------------------------------------------------------------ design and pairing audit
def design(ds, sd):
    """-> [(contrast, recipe, backbone, member, reference cfg, candidate cfg, declared difference, tag)] for one dataset and seed."""
    out = []
    for a in ARCH:
        T = lambda ad, rc, lr: ("TF", ds, a, ad, rc, lr, sd)
        for rc in RECIPES:
            for ad in INITS:
                for lr in LRS:
                    out.append(("TF-LOCAL", rc, a, f"L1->{ad}/{rc}/lr{lr:g}", ("L1", ds, sd), T(ad, rc, lr), "model (local encoder -> FM)", "FM vs same-access local L1"))
            for lr in LRS:
                out.append(("TF-INIT", rc, a, f"{rc}/lr{lr:g}", T("random_full", rc, lr), T("pretrained_full", rc, lr), "adaptation (initialization)",
                            "initialization (matched schedule and lr)"))
            for ad in INITS:
                for lr in LRS:
                    out.append(("L0-TF (audit only)", rc, a, f"L0->{ad}/{rc}/lr{lr:g}", ("L0", ds, sd), T(ad, rc, lr), "access_contract (declared access extension)",
                                "access extension, not same-access"))
    out.append(("L0-L1 (audit only)", "-", "-", "L0->L1", ("L0", ds, sd), ("L1", ds, sd), "access_contract (declared access extension)", "past 0.4 s EEG, access extension"))
    return out


def pair_check(ru, cu, access_declared, ref_cfg=None, cand_cfg=None):
    a, b = ru["fp"], cu["fp"]
    checks = {"record_rows": a["row_consistent"] and b["row_consistent"], "split": a["split"] == b["split"],
              "target": a["target"] == b["target"] and close(a["target_stats"], b["target_stats"]),
              "evaluation": a["evaluation"] == b["evaluation"] and a["code_hash_reproduced"] and b["code_hash_reproduced"]}
    same_access = a["access_key"] == b["access_key"] and a["access"]["window_samples"] is not None
    checks["access"] = ("declared difference" if not same_access else "equal (declared difference not realised)") if access_declared else same_access
    if ref_cfg is not None and cand_cfg is not None:
        checks["initialization"] = init_ok(a, ref_cfg) and init_ok(b, cand_cfg)
    return checks, [k for k, v in checks.items() if v is False]


def pair_status(sc, ref, cand, cell, access_declared):
    rid, cid = sc["index"].get((ref, cell)), sc["index"].get((cand, cell))
    ent = {"cell": list(cell), "reference": rid, "candidate": cid}
    if rid is None or cid is None:
        side = " and ".join(s for s, e in (("reference", rid), ("candidate", cid)) if e is None)
        ent.update(status="missing", reason=f"{side} not registered")
        return ent
    ru, cu = sc["units"][rid], sc["units"][cid]
    ent["reference_status"], ent["candidate_status"] = ru["status"], cu["status"]
    if ru["status"] == COMPLETE and cu["status"] == COMPLETE:
        checks, bad = pair_check(ru, cu, access_declared, ref, cand)
        ent["checks"] = checks
        ent["target_stats_rel_dev"] = rel_dev(ru["fp"]["target_stats"], cu["fp"]["target_stats"])
        if bad:
            ent.update(status="missing", reason="match-field mismatch: " + ", ".join(bad))
        else:
            ent.update(status="complete", reason="")
        return ent
    bad = [f"{s} {u['status']}" for s, u in (("reference", ru), ("candidate", cu)) if u["status"] in MISSING_ST]
    if bad:
        ent.update(status="missing", reason="; ".join(bad))
    else:
        ent.update(status="pending", reason="; ".join(f"{s} {u['status']}" for s, u in (("reference", ru), ("candidate", cu)) if u["status"] != COMPLETE))
    return ent


def audit(sc):
    """every designed pair x fold cell x seed -> status; identity status per member."""
    pairs, members = [], {}
    for ds in DS:
        for sd in SEEDS:
            for contrast, rc, a, name, ref, cand, declared, tag in design(ds, sd):
                access_declared = declared.startswith("access_contract")
                cells = [pair_status(sc, ref, cand, tuple(cell), access_declared) for cell in sc["cells"].get(ds, [])]
                by = {tuple(e["cell"]): e["status"] for e in cells}
                ids = {"complete": [], "pending": [], "missing": []}
                for ident, ic in sc["ident_cells"].get(ds, {}).items():
                    st = [by.get(tuple(c), "missing") for c in ic]
                    ids["missing" if "missing" in st else "pending" if "pending" in st else "complete"].append(ident)
                mk = f"{contrast}|{RTAG.get(rc, rc)}|{ds}|{a}|{sd}|{name}"
                members[mk] = {"contrast": contrast, "recipe": rc, "dataset": ds, "backbone": a, "seed": sd, "member": name, "reference": ck(ref),
                               "candidate": ck(cand), "ref_cfg": ref, "cand_cfg": cand, "declared_difference": declared, "tag": tag,
                               "registered": any(e["reference"] and e["candidate"] for e in cells),
                               "cells": dict(Counter(e["status"] for e in cells)), "identities": {k: len(v) for k, v in ids.items()},
                               "complete_identities": sorted(ids["complete"]), "complete_cells": sorted(tuple(e["cell"]) for e in cells if e["status"] == "complete")}
                for e in cells:
                    pairs.append({"member": mk, **e})
    summary = Counter((p["member"].split("|")[0], p["status"], p["reason"].split(":")[0]) for p in pairs)
    mism = [p for p in pairs if p["reason"].startswith("match-field mismatch")]
    return {"pairs": pairs, "members": members, "summary": [{"contrast": k[0], "status": k[1], "reason": k[2], "n": v} for k, v in sorted(summary.items())],
            "n_mismatch": len(mism), "mismatches": mism[:50]}


# ------------------------------------------------------------------------------------------------ values and families
def identity_values(sc, cfg, cells_ok, idents):
    """identity -> {metric: pooled mean over the identity's (unit, record) entries}, only for identities whose cells are all in cells_ok."""
    out = {}
    for ident in idents:
        cells = sc["ident_cells"][cfg[1]][ident]
        if not all(tuple(c) in cells_ok for c in cells):
            continue
        acc = defaultdict(list)
        for c in cells:
            for m, x in (sc["values"].get((cfg, tuple(c)), {}).get(ident) or {}).items():
                acc[m].extend(x)
        if acc:
            out[ident] = {m: float(np.mean(x)) for m, x in acc.items()}
    return out


def family_members(au, contrast, rc, ds, a, sd):
    pre = f"{contrast}|{RTAG[rc]}|{ds}|{a}|{sd}|"
    return {k[len(pre):]: m for k, m in au["members"].items() if k.startswith(pre)}


def run_fam(label, mem, vals, metric, notes):
    """bc_interim.run_family on per-member pseudo-configurations; adds each member's own complete-identity count."""
    members = [(name, ("pair", label, name, "ref"), ("pair", label, name, "cand"), m["tag"]) for name, m in mem.items()]
    res = BI.run_family(label, [x for x in members if vals.get(x[1])], vals, metric, notes, True)
    for name, m in mem.items():
        r = res["members"].setdefault(name, {"n": 0, "note": "no complete paired identity"})
        r["ref"], r["cand"] = m["reference"], m["candidate"]
        r["n_own"] = len(BI.member_values(vals, ("pair", label, name, "ref"), ("pair", label, name, "cand"), metric))
    return res


def per_seed_family(sc, au, contrast, rc, ds, a, sd, notes):
    mem = family_members(au, contrast, rc, ds, a, sd)
    label = f"TFL1|{contrast}|{RTAG[rc]}|{ds}|{a}|{sd}"
    vals = {}
    for name, m in mem.items():
        ids, ok = m["complete_identities"], set(m["complete_cells"])
        vals[("pair", label, name, "ref")] = identity_values(sc, m["ref_cfg"], ok, ids)
        vals[("pair", label, name, "cand")] = identity_values(sc, m["cand_cfg"], ok, ids)
    out = {"contrast": contrast, "recipe": rc, "dataset": ds, "backbone": a, "seed": sd, "label": label, "readouts": {}}
    for rd, metric in READOUTS:  # same label for both readouts: sci_r1.stats.group_seed(label, metric) already differs by metric
        out["readouts"][rd] = run_fam(label, mem, vals, metric, notes)
    return out, vals


def seed_mean_family(sc, au, ds, a, per_seed_vals, notes):
    """TF-LOCAL one-step: identity values averaged over the seeds; identities pair-complete in all seeds only; between-seed range."""
    label = f"TFL1|TF-LOCAL|onestep|{ds}|{a}|seedmean"
    mem0 = family_members(au, "TF-LOCAL", ONESTEP, ds, a, SEEDS[0])
    vals, meta = {}, {}
    for name, m in mem0.items():
        per = [per_seed_vals.get(sd, {}) for sd in SEEDS]
        lab = [f"TFL1|TF-LOCAL|onestep|{ds}|{a}|{sd}" for sd in SEEDS]
        refs = [p.get(("pair", l, name, "ref"), {}) for p, l in zip(per, lab)]
        cands = [p.get(("pair", l, name, "cand"), {}) for p, l in zip(per, lab)]
        common = set.intersection(*[set(x) & set(y) for x, y in zip(refs, cands)]) if refs else set()
        sm = lambda side: {i: {mt: float(np.mean([s[i][mt] for s in side])) for mt in METRICS if all(mt in s[i] for s in side)} for i in common}
        vals[("pair", label, name, "ref")], vals[("pair", label, name, "cand")] = sm(refs), sm(cands)
        n_seeds = Counter(sum(1 for x, y in zip(refs, cands) if i in x and i in y) for i in sc["ident_cells"].get(ds, {}))
        meta[name] = {"identities_by_n_seeds_complete": {str(k): v for k, v in sorted(n_seeds.items())}, "refs": refs, "cands": cands}
    out = {"contrast": "TF-LOCAL", "recipe": ONESTEP, "dataset": ds, "backbone": a, "seed": "seedmean", "seeds": list(SEEDS), "label": label, "readouts": {},
           "between_seed": {}}
    mem = {name: {**m, "reference": ck(("L1", ds, "seedmean")), "candidate": m["candidate"].rsplit("|", 1)[0] + "|seedmean"} for name, m in mem0.items()}
    for rd, metric in READOUTS:
        res = run_fam(label, mem, vals, metric, notes)
        out["readouts"][rd] = res
        present = [n for n in mem if BI.member_values(vals, ("pair", label, n, "ref"), ("pair", label, n, "cand"), metric)]
        common = sorted(set.intersection(*[set(BI.member_values(vals, ("pair", label, n, "ref"), ("pair", label, n, "cand"), metric)) for n in present])) if present else []
        bs = {}
        for name in mem:
            if not common or name not in present:
                bs[name] = {"n": 0, "note": "no identity pair-complete in all seeds for every member of the family"}
                continue
            r, c = meta[name]["refs"], meta[name]["cands"]
            d = [float(np.mean([BI.diff(r[k][i][metric], c[k][i][metric], "lower") for i in common])) for k in range(len(SEEDS))]
            bs[name] = {"n": len(common), "per_seed": {str(sd): x for sd, x in zip(SEEDS, d)}, "min": min(d), "max": max(d), "range": max(d) - min(d),
                        "sd": float(np.std(d, ddof=1))}
        out["between_seed"][rd] = bs
    out["coverage"] = {name: m["identities_by_n_seeds_complete"] for name, m in meta.items()}
    return out


def analyse(sc, au):
    notes = list(sc["notes"])
    fams, per_seed_vals = {}, defaultdict(dict)
    for ds in DS:
        for a in ARCH:
            for sd in SEEDS:
                for contrast in ("TF-LOCAL", "TF-INIT"):
                    for rc in RECIPES:
                        mem = family_members(au, contrast, rc, ds, a, sd)
                        if not any(m["registered"] for m in mem.values()):
                            continue  # recipe not registered for this seed (warm-up in the panel seeds): audit only
                        f, vals = per_seed_family(sc, au, contrast, rc, ds, a, sd, notes)
                        f["interim"] = any(m["cells"].get("pending", 0) for m in mem.values()) or (contrast == "TF-INIT" and rc == ONESTEP)  # TF-INIT one-step is always an interim view of ADDENDUM_11's frozen role
                        f["coverage_complete"] = all(m["cells"].get("complete", 0) == sum(m["cells"].values()) for m in mem.values())
                        f["status"] = "; ".join(x for x in ("warm-up recipe, registered for seed 3401 only" if rc == WARMUP else "",
                                                            "interim view of ADDENDUM_11's frozen role; official result by aln32_panel_interim.py"
                                                            if contrast == "TF-INIT" and rc == ONESTEP else "",
                                                            "new exploratory paired summary" if contrast == "TF-LOCAL" else "") if x)
                        fams[f"{contrast}|{RTAG[rc]}|{ds}|{a}|{sd}"] = f
                        if contrast == "TF-LOCAL" and rc == ONESTEP:
                            per_seed_vals[ds, a][sd] = vals
            if per_seed_vals.get((ds, a)):
                fams[f"TF-LOCAL|onestep|{ds}|{a}|seedmean"] = seed_mean_family(sc, au, ds, a, per_seed_vals[ds, a], notes)
                per = [fams.get(f"TF-LOCAL|onestep|{ds}|{a}|{sd}", {}) for sd in SEEDS]
                fams[f"TF-LOCAL|onestep|{ds}|{a}|seedmean"].update(interim=any(p.get("interim", True) for p in per),
                                                                   coverage_complete=all(p.get("coverage_complete", False) for p in per),
                                                                   status="new exploratory paired summary; identities pair-complete in all seeds")
    return fams, notes


INTERVAL_DIFF_CAUSE = ("bootstrap replicate indices are drawn with `sci_r1.stats.group_seed(label, metric)` and the family labels here "
                       "(`TFL1|contrast|recipe|dataset|backbone|seed`) differ from the frozen ones (`TF-INIT|dataset|backbone`, `TF-LOCAL|dataset|backbone`, "
                       "and `<label>|sec` for the native readout), so the pointwise intervals differ by bootstrap Monte Carlo error; the simultaneous "
                       "intervals differ by that and by the family composition (frozen TF-INIT: 4 members, recipe x lr; frozen TF-LOCAL: 16 members, "
                       "{L0, L1} x init x recipe x lr; frozen native readout: pointwise only). Point estimates are unaffected")


def reproduction_check(fams, frozen_path=FROZEN_WAVE1):
    """seed-3401 point estimates must equal the frozen ADDENDUM_07 analysis (aln32_wave1.json) for the same members. Also reports how far
    the intervals of the declared families are from the frozen ones (descriptive; cause in INTERVAL_DIFF_CAUSE)."""
    if not os.path.exists(frozen_path):
        return {"status": "frozen file absent", "path": frozen_path}
    fz = json.load(open(frozen_path))
    diffs, n_bad, compared = [], [], 0
    ci_d, sim_d = defaultdict(list), defaultdict(list)
    for key, f in fams.items():
        if f["seed"] != BREADTH:
            continue
        flab = f"{f['contrast']}|{f['dataset']}|{f['backbone']}"
        for rd, metric in READOUTS:
            for name, m in f["readouts"][rd]["members"].items():
                if "est" not in m:
                    continue
                src = fz["families"].get(flab, {}).get("members", {}) if rd == "unified" else fz["secondary"].get(flab, {}).get(metric, {}).get("members", {})
                z = src.get(name)
                if not z or "est" not in z:
                    continue
                compared += 1
                diffs.append(abs(z["est"] - m["est"]))
                if z.get("n") != m.get("n"):
                    n_bad.append(f"{key}|{rd}|{name}: n {m.get('n')} vs frozen {z.get('n')}")
                if "ci_low" in z and "ci_low" in m:
                    ci_d[rd].append(max(abs(z["ci_low"] - m["ci_low"]), abs(z["ci_high"] - m["ci_high"])))
                if "sim_low" in z and "sim_low" in m:
                    sim_d[rd].append(max(abs(z["sim_low"] - m["sim_low"]), abs(z["sim_high"] - m["sim_high"])))
    mx = max(diffs) if diffs else None
    iv = {rd: {"n_members": len(ci_d[rd]), "n_pointwise_differ": int(sum(d > 1e-9 for d in ci_d[rd])),
               "pointwise_max_abs_diff": max(ci_d[rd]) if ci_d[rd] else None, "n_simultaneous_compared": len(sim_d[rd]),
               "simultaneous_max_abs_diff": max(sim_d[rd]) if sim_d[rd] else None} for rd, _ in READOUTS}
    return {"status": "pass" if compared and mx is not None and mx < 1e-9 and not n_bad else ("not compared" if not compared else "FAIL"),
            "n_compared": compared, "max_abs_diff": mx, "n_mismatch": n_bad, "path": os.path.relpath(frozen_path, core.REPO),
            "declared_interval_diff": iv, "declared_interval_diff_cause": INTERVAL_DIFF_CAUSE}


def frozen_families(ds, a):
    """the ADDENDUM_07 TF-INIT and TF-LOCAL families of aln32_interim.families (frozen labels, member names, compositions), seed 3401."""
    L0, L1 = ("L0", ds, BREADTH), ("L1", ds, BREADTH)
    T = lambda ad, rc, lr: ("TF", ds, a, ad, rc, lr, BREADTH)
    return [(f"TF-INIT|{ds}|{a}", [(f"{rc}/lr{lr:g}", T("random_full", rc, lr), T("pretrained_full", rc, lr), "initialization (matched schedule and lr)")
                                   for rc in RECIPES for lr in LRS]),
            (f"TF-LOCAL|{ds}|{a}", [(f"{ref}->{ad}/{rc}/lr{lr:g}", R, T(ad, rc, lr), f"FM vs local ({ref})")
                                    for ref, R in (("L0", L0), ("L1", L1)) for ad in INITS for rc in RECIPES for lr in LRS])]


def complete_cells(sc, cfg):
    out = set()
    for c in sc["cells"].get(cfg[1], []):
        eid = sc["index"].get((cfg, tuple(c)))
        if eid and sc["units"][eid]["status"] == COMPLETE:
            out.add(tuple(c))
    return out


def frozen_interval_check(sc, frozen_path=FROZEN_WAVE1, tol=1e-9):
    """Correction 1 of the note: recompute the frozen ADDENDUM_07 TF-INIT / TF-LOCAL families with the frozen labels, member names and
    compositions (unified readout with max-t; native readout as '<label>|sec', pointwise, as aln32_interim.aggregate) from this script's
    seed-3401 identity values, and compare est, se, pointwise CI, simultaneous bounds and crit with aln32_wave1.json."""
    if not os.path.exists(frozen_path):
        return {"status": "frozen file absent", "path": frozen_path}
    fz = json.load(open(frozen_path))
    notes, diffs, n_bad, problems, compared, fams_done, n_absent = [], defaultdict(list), [], [], 0, 0, 0
    for ds in DS:
        idents = sorted(sc["ident_cells"].get(ds, {}))
        for a in ARCH:
            for label, members in frozen_families(ds, a):
                vals = {}
                for _, ref, cand, _ in members:
                    for c in (ref, cand):
                        if c not in vals:
                            vals[c] = identity_values(sc, c, complete_cells(sc, c), idents)
                spec = ((METRICS[0], label, True, fz.get("families", {}).get(label)),
                        (METRICS[1], f"{label}|sec", False, (fz.get("secondary", {}).get(label) or {}).get(METRICS[1])))
                for metric, lab, simultaneous, src in spec:
                    res = BI.run_family(lab, members, vals, metric, notes, simultaneous)
                    have = [k for k, v in res["members"].items() if "est" in v]
                    if not src or not src.get("members"):
                        if have:  # values here but no frozen family to compare with
                            problems.append(f"{lab} {metric}: not in the frozen file")
                        continue
                    fams_done += 1
                    if simultaneous:
                        if "crit" in src and "crit" in res:
                            diffs["crit"].append(abs(src["crit"] - res["crit"]))
                        else:
                            n_absent += 1
                    extra = sorted(set(have) - set(src["members"]))
                    if extra:
                        problems.append(f"{lab} {metric}: members not in the frozen family: {extra}")
                    for name, z in src["members"].items():
                        m = res["members"].get(name) or {}
                        if "est" not in z:
                            continue
                        compared += 1
                        if m.get("n") != z.get("n"):
                            n_bad.append(f"{lab}/{name}/{metric}: n {m.get('n')} vs frozen {z.get('n')}")
                        for k in ("est", "se", "ci_low", "ci_high") + (("sim_low", "sim_high") if simultaneous else ()):
                            if k in z and k in m:
                                diffs[k].append(abs(z[k] - m[k]))
                            elif k in z:
                                n_absent += 1
    mx = {k: max(v) for k, v in diffs.items()}
    ok = compared > 0 and not n_bad and not problems and not n_absent and all(x < tol for x in mx.values())
    return {"status": "pass" if ok else ("not compared" if not compared else "FAIL"), "n_families": fams_done, "n_members_compared": compared,
            "max_abs_diff": mx, "n_values_absent_here": n_absent, "tolerance": tol, "n_mismatch": n_bad, "problems": problems,
            "path": os.path.relpath(frozen_path, core.REPO),
            "what": "frozen ADDENDUM_07 TF-INIT (4 members) and TF-LOCAL (16 members) families per dataset x backbone, frozen labels, "
                    "recomputed from this script's seed-3401 identity values; unified with max-t, native '<label>|sec' pointwise"}


# ------------------------------------------------------------------------------------------------ coverage
def coverage(sc):
    out = defaultdict(Counter)
    for u in sc["units"].values():
        kind = u["cfg"].split("|")[0]
        if kind == "TF":
            kind = "TF/" + u["cfg"].split("|")[4]
        out[f"{kind}|{u['seed']}|{u['dataset']}"][u["status"]] += 1
    panel = Counter(u["status"] for u in sc["units"].values() if u["kind"] == "TF" and u["seed"] != BREADTH)
    by_rs = defaultdict(Counter)
    for k, v in out.items():
        kind, sd, _ = k.split("|")
        by_rs[f"{kind} · {sd}"].update(v)
    params = defaultdict(set)  # parameter counts read from the records (context for the competing explanations)
    for u in sc["units"].values():
        for part, n in (u.get("n_params") or {}).items():
            if n is not None:
                arch = u["cfg"].split("|")[2] if u["kind"] == "TF" else "lag_local_tokens"
                params[f"{u['kind']}|{arch}|{part}|{u['dataset']}"].add(int(n))
    return {"units": {k: dict(v) for k, v in sorted(out.items())}, "by_role_seed": {k: dict(v) for k, v in sorted(by_rs.items())},
            "tf_panel": {"complete": panel.get(COMPLETE, 0), "registered": sum(panel.values()), "by_status": dict(panel)},
            "identities": {ds: len(v) for ds, v in sc["ident_cells"].items()}, "n_phantom_entities": sc["n_phantom_entities"],
            "split_consistency": sc["split_bad"] or "one split fingerprint per fold cell", "parameter_counts": {k: sorted(v) for k, v in sorted(params.items())}}


# ------------------------------------------------------------------------------------------------ report
def _iv(m, lo="sim_low", hi="sim_high"):
    return f"[{m[lo]:+.3f}, {m[hi]:+.3f}]" if lo in m else "–"


def family_tag(key, f):
    """status words of a family: interim ADDENDUM_11 role (TF-INIT one-step), exploratory (TF-LOCAL), warm-up 3401 only, partial coverage."""
    contrast, rc = key.split("|")[:2]
    tags = []
    if contrast == "TF-INIT" and rc == RTAG[ONESTEP]:
        tags.append("interim (ADDENDUM_11 role)")
    elif contrast == "TF-LOCAL":
        tags.append("exploratory")
    if rc == RTAG[WARMUP]:
        tags.append("warm-up, 3401 only")
    if f.get("interim"):
        tags.append("partial coverage")
    return "; ".join(tags) or "–"


def _cellfmt(m, total=None):
    if not m or "est" not in m:
        n = (m or {}).get("n_own", 0)
        return f"not available (n {n}{'/' + str(total) if total else ''})"
    return f"{m['est']:+.3f} {_iv(m)} n {m['n']}"


def report(out, path):
    fams, cov, au = out["families"], out["coverage"], out["pair_audit"]
    tp = cov["tf_panel"]; ids = cov["identities"]
    interim = tp["complete"] < tp["registered"]
    gen = out["meta"]["generated"]
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    L = ["# True-full FM vs same-access local L1, and matched initialization, across seeds" + (" — INTERIM" if interim else ""), "",
         f"> **{'Interim' if interim else 'Panel complete'}.** Generated {gen} by `python -B -m auditory_alignment_v3.aln34.tf_l1_pairs` (analysis note "
         f"`{NOTE}`, written before any value was computed; its Correction 1 was appended at 2026-10-16 20:36, before the corrected code ran). ALN32_TRUE_FULL panel (seeds 3407/3413, one-step): **{tp['complete']}/{tp['registered']} units "
         "complete**. " + ("Every panel number below covers only the identities whose fold cells are complete and changes when the script is rerun. "
                           if interim else "")
         + "TF-LOCAL across seeds is a new exploratory paired summary (not an ADDENDUM_11 role). TF-INIT per seed is an interim view of ADDENDUM_11's "
         "frozen role; the official version is `aln32_panel_interim.py` " + ("after the panel completes." if interim else "(run it now that the panel is complete)."), "",
         "日期／代码与数据版本 · Date, code and data: " + f"{gen}; code sha256 " + ", ".join(f"`{k}` {v[:12]}" for k, v in out["meta"]["code_sha256"].items())
         + f"; unit code hashes recomputed now: " + ", ".join(f"{k} `{v}`" for k, v in out["meta"]["code_hash_now"].items()) + ".", "",
         "本轮完成／运行／待依赖 · Live state (units by role · seed, summed over datasets): " + "; ".join(
             f"{k} " + ", ".join(f"{s} {n}" for s, n in sorted(v.items())) for k, v in cov["by_role_seed"].items()) + ".", "",
         "已见信息与本轮新增信息 · Seen before / new here: all seed-3401 values were already reported in `ALIGNED_INTERFACE_RESULTS.md` (TF-INIT §7, "
         "TF-LOCAL §10). The 3401 point estimates here reproduce them exactly. The 3401 intervals do not: bootstrap replicates are seeded by the "
         "family label, and the families here have other labels and other members (§1.3, §1.4; §1.6 also recomputes the frozen families). "
         "New here: the seed-3407/3413 paired values, the identity mean over seeds, the between-seed range, and the pairing audit. Earlier runs of "
         "this script (the first at 2026-10-16 20:09) had been read before this run; the corrections made since then are listed in §5 and in the "
         "analysis note (Correction 1).", "",
         "Sign and unit: ΔR = R(reference) − R(candidate) in bits per 5 s test query; positive = candidate lower true-query risk. Intervals: identity-level "
         "bootstrap-t (B = 4,000), conditional on the fitted models (training randomness is not in them); `[a, b]` = 95 % simultaneous (max-t within "
         "the dataset × backbone × seed × recipe family; member counts in §1.2–§1.4); n = identities used. No p-values. The 2 inits × 2 lrs × 2 backbones × 3 datasets cells share "
         "identities, references and seeds: they are not independent replications, and nothing here extends beyond the seeds, lrs, recipes and the "
         "100 / 50-epoch budgets present.", "", "## 1. 当前观察 · Current observations", "", "### 1.1 Coverage", "",
         f"Identities (human, test): " + ", ".join(f"{ds} {n}" for ds, n in ids.items()) + f"; phantom entities excluded: {cov['n_phantom_entities']}. "
         f"Split consistency: {cov['split_consistency']}.", "",
         "| family (contrast · recipe · dataset · backbone · seed) | members | fold cells per member: complete / pending / missing | identities pair-complete per member | identities used (family common set) / cohort |",
         "|---|---|---|---|---|"]
    agg = defaultdict(lambda: [[], [], False])
    for k, m in au["members"].items():
        c, rc, ds, a, sd, _ = k.split("|", 5)
        if c.endswith("(audit only)"):
            continue
        g = agg[(c, rc, ds, a, sd)]
        g[0].append(tuple(m["cells"].get(s, 0) for s in ("complete", "pending", "missing"))); g[1].append(m["identities"].get("complete", 0))
        g[2] = g[2] or m["registered"]
    rng_ = lambda xs: f"{min(xs)}" if min(xs) == max(xs) else f"{min(xs)}–{max(xs)}"
    unreg = defaultdict(lambda: [0, set()])
    for (c, rc, ds, a, sd), (cells, idc, reg) in sorted(agg.items()):
        if not reg:
            unreg[(c, rc)][0] += len(cells) * sum(cells[0]); unreg[(c, rc)][1].add(sd); continue
        f = fams.get(f"{c}|{rc}|{ds}|{a}|{sd}", {}).get("readouts", {}).get("unified", {}).get("members", {})
        used = max([m.get("n", 0) for m in f.values() if "est" in m] or [0])
        L.append(f"| {c} · {rc} · {ds} · {a} · {sd} | {len(cells)} | " + " / ".join(rng_([x[i] for x in cells]) for i in range(3))
                 + f" | {rng_(idc)} | {used} / {ids.get(ds, 0)} |")
    L.append("")
    L.append("An identity is pair-complete only when every fold cell it appears in is pair-complete; identities with a pending cell are excluded, never "
             "averaged over the cells that happen to be done. Family statistics use the identities pair-complete for every member.")
    if unreg:
        L.append("Not registered (listed as missing in the JSON audit; nothing is trained for them): " + "; ".join(
            f"{c} {rc} in seeds {'/'.join(sorted(s))} ({n} member × cell pairs)" for (c, rc), (n, s) in sorted(unreg.items())) + ".")
    L.append("")

    def lines_tf_local(rd):
        X = [f"| dataset · backbone | member | seed 3401 | seed 3407 | seed 3413 | identity mean over seeds | between-seed range (same identities) |",
             "|---|---|---|---|---|---|---|"]
        for ds in DS:
            for a in ARCH:
                sm = fams.get(f"TF-LOCAL|onestep|{ds}|{a}|seedmean")
                names = list(sm["readouts"][rd]["members"]) if sm else []
                for name in names:
                    cells = [_cellfmt(fams.get(f"TF-LOCAL|onestep|{ds}|{a}|{sd}", {}).get("readouts", {}).get(rd, {}).get("members", {}).get(name), ids.get(ds))
                             for sd in SEEDS]
                    s = sm["readouts"][rd]["members"].get(name, {})
                    b = sm["between_seed"][rd].get(name, {})
                    rng = (f"{b['min']:+.3f} … {b['max']:+.3f} (" + ", ".join(f"{sd}: {x:+.3f}" for sd, x in b["per_seed"].items()) + f"; n {b['n']})"
                           if "per_seed" in b else "not available")
                    X.append(f"| {ds} · {a} | {name.replace('/full_onestep_v1', '')} | " + " | ".join(cells) + f" | {_cellfmt(s, ids.get(ds))} | {rng} |")
        return X

    L += ["### 1.2 TF-LOCAL one-step: L1 → true-full FM, unified readout (primary)", "",
          "Each per-seed cell: ΔR [95 % simultaneous within dataset × backbone × seed, 4 members] n. Identity mean over seeds: identities pair-complete in "
          "all three seeds, 95 % simultaneous within dataset × backbone. Between-seed range: per-seed mean paired difference on those same identities "
          "(descriptive; three seeds do not estimate a seed distribution).",
          "", "**Per-seed cells use each seed's own pair-complete identities (n shown).** Seed 3401 covers every identity; the panel seeds cover only "
          "the outer folds completed so far. Per-seed values on different identity sets are not a seed comparison; compare seeds through the last two "
          "columns, which use the same identities in every seed.", ""] + lines_tf_local("unified") + [""]

    def lines_simple(contrast, rc, rd, seeds, tag=""):
        X = [f"| dataset · backbone | member | " + " | ".join(f"seed {sd}" for sd in seeds) + " |", "|---|---|" + "---|" * len(seeds)]
        for ds in DS:
            for a in ARCH:
                f0 = fams.get(f"{contrast}|{RTAG[rc]}|{ds}|{a}|{seeds[0]}")
                if not f0:
                    continue
                for name in f0["readouts"][rd]["members"]:
                    X.append(f"| {ds} · {a} | {name}{tag} | " + " | ".join(
                        _cellfmt(fams.get(f"{contrast}|{RTAG[rc]}|{ds}|{a}|{sd}", {}).get("readouts", {}).get(rd, {}).get("members", {}).get(name), ids.get(ds))
                        for sd in seeds) + " |")
        return X

    rp, ir = out["reproduction_check"], out.get("interval_reproduction_check") or {}
    div = (rp.get("declared_interval_diff") or {}).get("unified") or {}
    mc = (f" Over the seed-3401 unified members, the largest bound difference from the frozen intervals is {div['pointwise_max_abs_diff']:.4f} bits "
          f"pointwise and {div['simultaneous_max_abs_diff']:.4f} bits simultaneous."
          if div.get("pointwise_max_abs_diff") is not None and div.get("simultaneous_max_abs_diff") is not None else "")
    why = ("The point estimates are identical. The intervals are not, for two reasons. Bootstrap replicate indices are seeded by the family label "
           "(`sci_r1.stats.group_seed(label, metric)`), and the labels here differ from the frozen ones, so even the pointwise intervals differ by "
           "bootstrap Monte Carlo error. The simultaneous intervals differ by that error and also by the family's members." + mc + " "
           + ("Recomputed with the frozen labels and members, this script's identity values reproduce the frozen intervals exactly (§1.6)."
              if ir.get("status") == "pass" else f"The recomputation with the frozen labels and members is in §1.6 (status: {ir.get('status', 'not run')})."))
    L += ["### 1.3 TF-LOCAL warm-up recipe (seed 3401 only; not registered in the panel)", "",
          "ΔR [95 % simultaneous within dataset × backbone, 4 warm-up members] n. Already reported in `ALIGNED_INTERFACE_RESULTS.md` §10, where the "
          "family is `TF-LOCAL|<dataset>|<backbone>` with 16 members ({L0, L1} × init × recipe × lr). " + why, ""]
    L += lines_simple("TF-LOCAL", WARMUP, "unified", (BREADTH,)) + [""]
    L += ["### 1.4 TF-INIT: random → pretrained at the same recipe and numeric lr — INTERIM", "",
          "One-step, per seed: ΔR [95 % simultaneous within dataset × backbone × seed, 2 members] n. **Every one-step row is interim.** It is an "
          "interim look at ADDENDUM_11's frozen role `initialization_true_full`. That role's official family is dataset × seed with 4 members "
          "(backbone × lr), computed by `aln32_panel_interim.py` once the panel is complete. The family used here (dataset × backbone × seed, recipe "
          "split off, 2 members over lr) is neither that family nor ADDENDUM_07's. No seed mean and no between-seed summary is formed for TF-INIT. "
          "Seed 3401 covers every identity and the panel seeds only the outer folds completed so far, so the per-seed values rest on different "
          "identity sets (n shown) and are not a seed comparison. Seed 3401 is also in `ALIGNED_INTERFACE_RESULTS.md` §7, where the family is "
          "`TF-INIT|<dataset>|<backbone>` with 4 members (recipe × lr). " + why, ""]
    L += lines_simple("TF-INIT", ONESTEP, "unified", SEEDS, " · interim") + [""]
    L += ["Warm-up recipe (seed 3401 only):", ""] + lines_simple("TF-INIT", WARMUP, "unified", (BREADTH,)) + [""]
    L += ["### 1.5 Native readout (separate families; never pooled with the unified readout)", "", "TF-LOCAL one-step:", ""] + lines_tf_local("native") + [""]
    L += ["TF-INIT one-step (interim):", ""] + lines_simple("TF-INIT", ONESTEP, "native", SEEDS, " · interim") + [""]
    L += ["TF-LOCAL warm-up (seed 3401 only):", ""] + lines_simple("TF-LOCAL", WARMUP, "native", (BREADTH,)) + [""]
    L += ["TF-INIT warm-up (seed 3401 only):", ""] + lines_simple("TF-INIT", WARMUP, "native", (BREADTH,)) + [""]
    L += ["### 1.6 Pairing audit", "",
          "The unit records carry no split hash, target hash or evaluation-version field (the ALN3 result schema asked for them; the runners never wrote "
          "them). The closest verifiable equivalents used for every complete pair:", "", "| field | derivation |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in FIELD_DERIVATION.items()]
    rs = out.get("role_summary", {})
    if rs:
        L += ["", "Derived fields per role and dataset (complete units only; every unit's values are in the JSON `units` table):", "",
              "| role · dataset | complete units | plan/record rows consistent | code_hash (reproduced now) | access: support, window [a, b) samples, mask | "
              "initialization: backbone_contract arch/adaptation (consistent with the configuration, no donor init_state) | information_stratum (plan label) |",
              "|---|---|---|---|---|---|---|"]
        for k, v in rs.items():
            acc_ = "; ".join(f"{a['support']}, {a['window_samples']}, {a['mask']}" for a in (json.loads(x) for x in v["access"]))
            ini = ", ".join(f"{x} {n}" for x, n in sorted((v.get("initialization") or {}).items())) + f" ({v.get('initialization_consistent', 0)})"
            L.append(f"| {k.replace('|', ' · ')} | {v['complete']} | {v['rows_consistent']} | " + ", ".join(f"`{h}`" for h in v["code_hash"])
                     + f" ({', '.join(f'{r}: {n}' for r, n in v['reproduced'].items())}) | {acc_} | {ini} | {', '.join(v['stratum'])} |")
    L += ["", "Pair statuses (fold cell × seed × member; L0 rows are audit-only access extensions):", "", "| contrast | status | reason | pairs |", "|---|---|---|---|"]
    L += [f"| {s['contrast']} | {s['status']} | {s['reason'] or '–'} | {s['n']} |" for s in au["summary"]]
    e1 = lambda x: "–" if x is None else f"{x:.1e}"
    e4 = lambda x: "–" if x is None else f"{x:.4f}"
    dv = rp.get("declared_interval_diff") or {}
    du, dn = dv.get("unified") or {}, dv.get("native") or {}
    imx = ir.get("max_abs_diff") or {}
    L += ["", f"Match-field mismatches among complete units: **{au['n_mismatch']}** (checked per complete pair: record rows, split, target, "
              "evaluation, access and initialization). Largest relative deviation of the target calibration statistics (sigma_v, ridge_v) within "
              f"complete pairs: {out['max_target_rel_dev']:.1e}.", "",
          f"Seed-3401 reproduction of the frozen ADDENDUM_07 analysis (`{rp.get('path')}`):", "",
          f"- Point estimates and n of the declared families: **{rp['status']}** ({rp.get('n_compared', 0)} member × readout values, max |Δ| "
          f"{e1(rp.get('max_abs_diff'))}; n mismatches {len(rp.get('n_mismatch', []))}).",
          f"- Intervals of the declared families against the frozen ones (descriptive): pointwise bounds differ in {du.get('n_pointwise_differ', 0)} of "
          f"{du.get('n_members', 0)} unified members, by up to {e4(du.get('pointwise_max_abs_diff'))} bits (native: {dn.get('n_pointwise_differ', 0)} "
          f"of {dn.get('n_members', 0)}, up to {e4(dn.get('pointwise_max_abs_diff'))}); simultaneous bounds by up to "
          f"{e4(du.get('simultaneous_max_abs_diff'))} bits (unified; the frozen native readout has no simultaneous intervals). Cause: "
          f"{INTERVAL_DIFF_CAUSE}.",
          f"- Frozen labels, member names and compositions recomputed from this script's identity values (per dataset × backbone: TF-INIT 4 members, "
          f"TF-LOCAL 16 members; unified with max-t, native `<label>|sec` pointwise): **{ir.get('status', 'not run')}** "
          f"({ir.get('n_members_compared', 0)} member × readout values in {ir.get('n_families', 0)} families; largest |Δ| over est, se, pointwise "
          f"CI, simultaneous bounds and crit: {e1(max(imx.values()) if imx else None)}; n mismatches {len(ir.get('n_mismatch', []))}"
          + (f"; problems: {'; '.join(ir['problems'][:5])}" if ir.get("problems") else "") + ").", ""]
    L += ["## 2. 当前工作判断 · Current working judgement", "",
          "TF-LOCAL one-step only. Per member, the seeds whose 95 % simultaneous interval lies above zero, contains zero or lies below zero (unified "
          "readout; seeds not yet available are listed separately). This is a description of each member across seeds, not a count of independent "
          "replications.", "",
          "TF-INIT is not judged across seeds here: the analysis note declares no seed mean and no between-seed summary for it. Its per-seed values "
          "are in §1.4 and §1.5, every one-step row tagged interim; the frozen `aln32_panel_interim.py` gives the official ADDENDUM_11 version once "
          "the panel is complete.", "",
          "| dataset · backbone | contrast · member | above 0 | contains 0 | below 0 | not available | identity mean over seeds |", "|---|---|---|---|---|---|---|"]
    for ds in DS:
        for a in ARCH:
            for contrast, rc in (("TF-LOCAL", ONESTEP),):
                f0 = fams.get(f"{contrast}|{RTAG[rc]}|{ds}|{a}|{BREADTH}")
                if not f0:
                    continue
                for name in f0["readouts"]["unified"]["members"]:
                    cls = defaultdict(list)
                    for sd in SEEDS:
                        m = fams.get(f"{contrast}|{RTAG[rc]}|{ds}|{a}|{sd}", {}).get("readouts", {}).get("unified", {}).get("members", {}).get(name, {})
                        cls[{"I>0": "above", "I<0": "below", "contains 0": "contains"}.get(m.get("class"), "na")].append(f"{sd} (n {m.get('n', 0)})" if m.get("class") else str(sd))
                    sm = fams.get(f"TF-LOCAL|onestep|{ds}|{a}|seedmean", {}).get("readouts", {}).get("unified", {}).get("members", {}).get(name, {}) if contrast == "TF-LOCAL" else {}
                    smt = (f"{sm['est']:+.3f} {_iv(sm)} n {sm['n']} ({sm.get('class')})" if "est" in sm else ("–" if contrast == "TF-INIT" else "not available"))
                    L.append(f"| {ds} · {a} | {contrast} · {name.replace('/full_onestep_v1', '').replace('full_onestep_v1/', 'one-step/')} | "
                             + " | ".join(", ".join(cls[k]) or "–" for k in ("above", "contains", "below", "na")) + f" | {smt} |")
    sub = []
    for ds in DS:
        for a in ARCH:
            sm = fams.get(f"TF-LOCAL|onestep|{ds}|{a}|seedmean")
            f0 = fams.get(f"TF-LOCAL|onestep|{ds}|{a}|{BREADTH}")
            if not sm or not f0:
                continue
            for name, b in sm["between_seed"]["unified"].items():
                m0 = f0["readouts"]["unified"]["members"].get(name, {})
                if "per_seed" in b and "est" in m0 and b["n"] < m0["n"]:
                    sub.append(f"| {ds} · {a} | {name.replace('/full_onestep_v1', '')} | {m0['est']:+.3f} (n {m0['n']}) | {b['per_seed'][str(BREADTH)]:+.3f} (n {b['n']}) | "
                               + ", ".join(f"{sd}: {b['per_seed'][str(sd)]:+.3f}" for sd in SEEDS if sd != BREADTH) + " |")
    if sub:
        L += ["", "Identity-subset check (TF-LOCAL one-step, unified; descriptive means, no intervals). Where the panel covers only part of a cohort, "
                  "seed 3401 restricted to the same identities shows how much of the gap between the 3401 column and the panel columns of §1.2 comes "
                  "from the identity subset rather than from the seed:", "",
              "| dataset · backbone | member | seed 3401, all identities | seed 3401, seed-mean identities | panel seeds, same identities |", "|---|---|---|---|---|"] + sub
    rngs = []
    for ds in DS:
        for a in ARCH:
            sm = fams.get(f"TF-LOCAL|onestep|{ds}|{a}|seedmean")
            for name, b in ((sm or {}).get("between_seed", {}).get("unified") or {}).items():
                if "per_seed" in b:
                    rngs.append((b["range"], ds, a, name, b))
    if rngs:
        hi = max(rngs, key=lambda x: x[0])
        L += ["", f"On the same identities the seeds still differ: over the {len(rngs)} TF-LOCAL one-step members with all three seeds, the "
                  f"between-seed range of the per-seed means runs from {min(x[0] for x in rngs):.3f} to {hi[0]:.3f} bits (largest: {hi[1]} · {hi[2]} "
                  f"{hi[3].replace('/full_onestep_v1', '')}, " + ", ".join(f"{sd}: {x:+.3f}" for sd, x in hi[4]["per_seed"].items())
                  + f"; n {hi[4]['n']}). These are descriptive means of three seeds, not an estimate of a seed distribution."]
    pan_ds = sorted({m["dataset"] for m in au["members"].values() if m["seed"] != BREADTH and m["contrast"] == "TF-LOCAL" and m["identities"].get("complete", 0)})
    L += ["", "Scope of these judgements:",
          (f"- Seeds 3407/3413 currently contribute only in: {', '.join(pan_ds) or 'no dataset'}; the panel-seed entries cover the identities counted in §1.1 "
           "(the outer folds completed so far), not the whole cohort. Datasets without a complete panel pair rest on seed 3401 alone." if interim else
           "- All registered panel units are complete; identity counts per family are in §1.1."),
          "- What is compared is this registered recipe: aligned [−0.4, +0.6) s interface, one-step full update with backbone lr 1e-5 or 3e-4 (head 1e-3, "
          "LLRD 1), 100 (CBraMod) / 50 (REVE) epochs, checkpoint by the training-side early-stopping rule. It is not a statement about other optimizers, "
          "budgets, data amounts or backbones.",
          "- TF-LOCAL is an FM-versus-local contrast under the same EEG access, target and evaluation. It is not a pure pretraining or pure architecture "
          "effect (§3). Only TF-INIT is an initialization contrast, and it remains interim until the panel is complete.", ""]
    pc = cov.get("parameter_counts", {})
    pcs = lambda pre: ", ".join(f"{k.rsplit('|', 1)[1]} " + "/".join(f"{x:,}" for x in v) for k, v in pc.items() if k.startswith(pre)) or "not recorded"
    L += ["## 3. 仍竞争的解释 · Competing explanations", "",
          "- **L1 → pretrained TF** mixes the pretraining prior with architecture (12-block CBraMod / 22-block REVE transformer vs the lag-local "
          "encoder), parameter count, input resampling to one 200 Hz patch, the readout head and the optimizer/schedule (the local encoder: AdamW 1e-3, "
          "200 epochs). The same-access match removes only the EEG-window difference. Parameter counts read from the records: L1 encoder "
          f"{pcs('L1|lag_local_tokens|encoder|')}; CBraMod backbone {pcs('TF|cbramod|backbone|')}; REVE backbone {pcs('TF|reve|backbone|')}; aligned "
          f"readout head {pcs('TF|cbramod|readout|')} (CBraMod) and {pcs('TF|reve|readout|')} (REVE).",
          "- **L1 → random TF** carries the same architecture/optimizer differences without the prior. Comparing it with L1 → pretrained TF in the same "
          "seed is TF-INIT, the matched initialization contrast.",
          "- **TF-INIT at a fixed budget** does not separate faster optimization from transferable content (package docs/01, question 1). Whether the "
          "initialization effect shrinks or grows from lr 1e-5 to 3e-4 does not by itself distinguish the two.",
          "- **Unified vs native readout.** The unified readout fits a ridge bridge into the standardized target space on training participants; the "
          "native readout is the model's own NCE score. They can rank models differently; a difference between them is about the bridge, not the EEG access.",
          "- **Seed variation.** A panel seed changes the whole pipeline (initialization of random parts, data order, readout subsample, calibration rows). "
          "Identity-level intervals condition on the fitted models; three seeds can show whether results are stable across these draws; they are not a seed distribution, and §2 shows large spreads on the same identities."]
    if interim:
        L.append("- **Interim coverage.** The panel queue runs DTU first and outer folds in order; the current panel identities are the earliest folds "
                 "and need not represent the cohort. This is availability, not selection by performance, but it limits what the panel entries say now.")
    L.append("")
    L += ["## 4. 下一轮干预 · Next interventions", "",
          "- Let the registered panel finish (no new registration needed: every missing one-step pair is registered and queued; L0/L1 are complete). "
          "Rerun this script after each batch; it is idempotent. When 400/400 are complete, run the frozen `aln32_panel_interim.py` for the official "
          "ADDENDUM_11 roles (including TF-INIT); this script does not replace it.",
          "- Warm-up is not registered for 3407/3413 and is not needed for this card (package docs/02 §A: one-step 3e-4 is the explicit starting point "
          "for the deeper CBraMod panel).",
          "- Package docs/02 §B (learning process, target-population size, content amount, ~2× budget) is the next intervention for separating "
          "optimization speed from transferable content; it needs its own registration with matched updates. Not started here.",
          "- REVE keeps its representative random/pretrained comparison and both readouts (package docs/02 §A).", ""]
    L += ["## 5. 复用与运行 · Reuse and running", "",
          f"- Reused unit records: " + ", ".join(f"{k} {v}" for k, v in out["meta"]["reused_records"].items()) + ". No training, no GPU job, no queue or "
          f"hold change. CPU aggregation run locally ({out['meta']['runtime_s']:.0f} s).",
          f"- Outputs: `{os.path.relpath(out['meta']['json_path'], core.REPO)}` (pairing audit with every pair's status and checks, coverage, all "
          f"families with pointwise and simultaneous intervals, seed means, ranges, native readout) and this document. Both mode 600.",
          "- Blocking: none. Missing panel pairs are pending in the queue, not failed.",
          "- Implementation details relative to the analysis note. Decided while coding, before the first real run: the target calibration "
          "statistics (sigma_v, ridge_v) are compared with relative tolerance 1e-6 next to the hash of the exact target fields rather than inside "
          f"the hash (largest deviation observed {out['max_target_rel_dev']:.1e}, so both readings agree here); the evaluation key also lists the "
          "readout set (unified, native). Added after the first real run had been seen: the parameter counts in §3, the per-role table of derived "
          "fields in §1.6, and the identity-subset check in §2 (prompted by the DTU panel identities showing smaller seed-3401 effects than the full "
          "cohort). These are descriptive and change no estimate, family or interval.",
          "- Corrections after an independent verification of the 20:09 run (analysis note, Correction 1, written 2026-10-16 20:36 before the "
          "corrected code ran). No estimate, family or interval changed.",
          "  1. The seed-3401 interval differences from `ALIGNED_INTERFACE_RESULTS.md` were explained by family composition alone. The pointwise "
          "intervals differ too, because bootstrap replicates are seeded by the family label. §1.3 and §1.4 now say so, and §1.6 recomputes the frozen "
          "families with their own labels and members.",
          "  2. The TF-INIT difference is evidenced by `backbone_contract.adaptation` (random_full / pretrained_full) and `.arch`, not by "
          "`init_state_loaded`. That field records only donor weights and is null in every TF record. A pair check `initialization` was added (§1.6).",
          "  3. The code and test files were mode 644 while the note said 600. They are 600 now.",
          "  4. The note misnamed the TF-INIT family scope. It is dataset × backbone × seed × recipe (2 members over lr), which is neither "
          "ADDENDUM_07's family (dataset × backbone, recipe × lr) nor ADDENDUM_11's (dataset × seed, backbone × lr). The package card specifies none.",
          "  5. TF-INIT left the §2 cross-seed table. Every TF-INIT one-step row carries an interim tag.",
          "  6. §2 adds the between-seed spread on the same identities.",
          "  7. The script was rerun on the live state, and outputs give the generation time to the second.", ""]
    L += ["## 6. 暂不决定 · Not decided here", "",
          "- Nothing here needs a researcher decision. Paper organisation, wording and contribution order stay open and do not block the interventions above.", ""]
    L += ["## Appendix A. Per-member detail (unified readout)", "",
          "| family | status | member | n (own) | ΔR | 95 % CI | 95 % simultaneous | class |", "|---|---|---|---|---|---|---|---|"]
    for key, f in fams.items():
        st = family_tag(key, f)
        for name, m in f["readouts"]["unified"]["members"].items():
            L.append(f"| {key.replace('|', ' · ')} | {st} | {name} | {m.get('n', 0)} ({m.get('n_own', 0)}) | {f3(m.get('est'))} | {_iv(m, 'ci_low', 'ci_high')} | "
                     f"{_iv(m)} | {m.get('class', '–')} |")
    L += ["", "## Appendix B. Notes", ""] + ([f"- {n}" for n in out["notes"][:60]] or ["- none"]) + ([f"- … {len(out['notes']) - 60} more in the JSON"] if len(out["notes"]) > 60 else []) + [""]
    _atomic_write(path, "\n".join(L))
    return path


# ------------------------------------------------------------------------------------------------ io and main
def _atomic_write(path, text):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def role_summary(sc):
    """per role kind x dataset: complete units, distinct code hashes (and whether they reproduce now), access, stratum, distinct split / target keys."""
    acc = defaultdict(lambda: {"complete": 0, "code_hash": Counter(), "reproduced": Counter(), "access": Counter(), "stratum": Counter(), "rows_consistent": 0,
                               "initialization": Counter(), "initialization_consistent": 0})
    for u in sc["units"].values():
        if u["status"] != COMPLETE:
            continue
        k = f"{u['kind']}|{u['dataset']}"; fp = u["fp"]; a = acc[k]
        a["complete"] += 1; a["code_hash"][fp["code_hash"]] += 1; a["reproduced"][str(fp["code_hash_reproduced"])] += 1
        a["access"][json.dumps(fp["access"], sort_keys=True)] += 1; a["stratum"][str(fp["information_stratum"])] += 1; a["rows_consistent"] += fp["row_consistent"]
        b = fp.get("backbone")
        a["initialization"]["local encoder" if b is None and fp.get("local_encoder") else "no encoder or backbone record" if b is None else
                            f"{b.get('arch')}/{b.get('adaptation')}" + ("" if b.get("init_state_loaded") is None else " + donor init_state")] += 1
        a["initialization_consistent"] += bool(u.get("initialization_ok"))
    return {k: {kk: (dict(vv) if isinstance(vv, Counter) else vv) for kk, vv in v.items()} for k, v in sorted(acc.items())}


def strip_private(au):
    """the JSON keeps identity counts, not identity lists (and the readable configuration strings, not the tuples)."""
    return {**au, "members": {k: {kk: vv for kk, vv in m.items() if kk not in ("complete_identities", "ref_cfg", "cand_cfg")} for k, m in au["members"].items()}}


def compute(rows, load, manifest, live, code_now, eval_sha):
    sc = scan(rows, load, manifest, live, code_now, eval_sha)
    au = audit(sc)
    fams, notes = analyse(sc, au)
    devs = [p["target_stats_rel_dev"] for p in au["pairs"] if p.get("status") == "complete" and p.get("target_stats_rel_dev") is not None]
    return sc, au, fams, notes, (max(devs) if devs else 0.0)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--no-doc", action="store_true")
    args = a.parse_args()
    t0 = time.time()
    started = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    from auditory_alignment_v3 import run as r3
    rows = r3.all_rows()
    code_now = {f: core.code_hash(f) for f in FAMILY.values()}
    eval_sha = file_sha(*EVAL_FILES)
    sc, au, fams, notes, maxdev = compute(rows, BI.unit_loader(), BI.load_manifest(), live_state(), code_now, eval_sha)
    here = os.path.dirname(os.path.abspath(__file__))
    reused = Counter(u["cfg"].split("|")[0] for u in sc["units"].values() if u["status"] == COMPLETE)
    meta = {"generated": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "snapshot_started": started, "note": NOTE, "card": "R34_TF_L1_PANEL", "status": "interim",
            "corrections": "analysis note Correction 1 (2026-10-16 20:36): interval-difference cause, initialization evidence and pair check, file "
                           "modes, TF-INIT family scope wording, TF-INIT out of the cross-seed judgement, same-identity spread, live rerun",
            "code_sha256": {"aln34/tf_l1_pairs.py": hashlib.sha256(open(os.path.join(here, "tf_l1_pairs.py"), "rb").read()).hexdigest(),
                            **{f: hashlib.sha256(open(os.path.join(os.path.dirname(here), *f.split("/")), "rb").read()).hexdigest()
                               for f in ("bc_interim.py", "sci_r1/stats.py")}},
            "code_hash_now": code_now, "eval_code_sha16": eval_sha, "seeds": list(SEEDS), "lrs": list(LRS), "bootstrap_B": S.NB,
            "reused_records": dict(reused), "json_path": os.path.join(RES, JSON_NAME)}
    out = {"meta": meta, "coverage": coverage(sc), "pair_audit": strip_private(au), "field_derivation": FIELD_DERIVATION, "role_summary": role_summary(sc),
           "units": sc["units"], "families": fams, "max_target_rel_dev": maxdev, "reproduction_check": reproduction_check(fams),
           "interval_reproduction_check": frozen_interval_check(sc), "notes": notes}
    meta["runtime_s"] = round(time.time() - t0, 1)
    if out["coverage"]["tf_panel"]["complete"] == out["coverage"]["tf_panel"]["registered"]:
        meta["status"] = "panel complete (run aln32_panel_interim.py for the frozen ADDENDUM_11 roles)"
    jpath = os.path.join(RES, JSON_NAME)
    _atomic_write(jpath, json.dumps(BI.jl(out), indent=1))
    paths = [jpath]
    if not args.no_doc:
        paths.append(report(out, os.path.join(DOCS, DOC_NAME)))
    bad = BI.privacy_scan(paths, set())
    print(f"TF panel {out['coverage']['tf_panel']['complete']}/{out['coverage']['tf_panel']['registered']} | mismatches {au['n_mismatch']} | "
          f"reproduction {out['reproduction_check']['status']} | frozen-label intervals {out['interval_reproduction_check']['status']} | "
          f"privacy scan {'PASS' if not bad else bad} | {meta['runtime_s']} s")
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
