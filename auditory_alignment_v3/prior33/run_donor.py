"""E34_PUBLIC_PRIOR donor-group runner (module M5; PUBLIC_PRIOR_DESIGN.md §2.6-§2.10, §2.15, §2.16, §4.3, §6.1 `run_donor.py`,
§6.3 RUNNER prior33_donor / prior33_rich_donor -> prior33.run_donor): the pool entry point of one ALN32_PUBLIC_AUDIO_PRIOR_DONOR,
_RICH_DONOR or _CSX_DONOR row.

run(row, out, epochs=None, *, manifest=None, device=None)
  Follows the ALN3 runner conventions (auditory_alignment_v3/local_support.py, residual32.py): core.new_record, status
  "running" -> "complete" | "technical_failed", every exception caught into technical_failed with error and traceback,
  core.write_record (units/<gid>.json, or .FAILED.json and exit 1). It verifies spec.manifest_sha256 against the opened manifest,
  re-checks the dependencies (donor_train.resolve_upstreams: the horizon group's record and, for rich groups, the core AP
  checkpoint; a continuation's retained stable states) and writes a missing one as technical_failed, never as a silent return.
  epochs caps the main-run steps (probes only). manifest= (a views.Manifest or a path) and device= are for tests and probes; the
  pool calls run(row, out, epochs).
  The group's resume files (ckpt/<gid>_resume.pt, _wsd_resume.pt) are deleted only after core.write_record has written the
  complete record (train_donor_group(cleanup=False), then donor_train.remove_resume_files): an exception or a pre-emption between
  the end of training and the record leaves them, and the retry resumes a run marked done, which only redoes the post-training
  scores (bridge_cal, rich readout) and the record. A technical_failed record keeps them too.
Record (prior33_interfaces_M11.md; select.py pins the donor-group layout): the train_donor_group fields (members[M].{best, h30,
gainsel}.{ce_dev, gain, bridge_cal_ce, ep_eq}, steps, nonfinite_steps, horizon_ep_eq, ceiling_reached_while_improving, ...), plus
  joint_choice   select.joint_choice(record) (the lambda rule on members[J1 / J025].best.ce_dev), for groups with J1 and J025
  gain_rule      {rule, member, gain {J1, J025}, tie}: the same choice on the gain of the _gainsel_best checkpoints (sensitivity)
  target_contract (overwritten: the manifest's), selection_level, mode, coverage, normalisation_access, view_sha256,
  manifest_sha256, dependency (the upstream groups with code_hash_equal / same_code_group: whether the upstream record's
  code_hash equals this unit's; recorded, never refused), record_check (select.check_group_record on the finished record; an
  error is logged here, never turned into a failure of a finished group), nonfinite_to_null.
  Non-finite numbers: unit records carry no NaN / Infinity tokens (strict JSON; the ALN3 records are archived byte-identically).
  Every non-finite number is written as null and its path listed in nonfinite_to_null, except members[M].best.ce_dev, which
  select.py pins as a JSON number (NaN = +inf; it is non-finite only when every validation of that member was).
The default manifest is <CACHE_ROOT>/manifest.json, else the private copy private/auditory_alignment_v3/aln34/prior33/manifest.json
(cache root views.CACHE_ROOT); either is opened only with the row's sha256.
Run as a module (python -m auditory_alignment_v3.run ... dispatches here); select.py is imported at run time, so the donor code
groups must hash it (for M9).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
import traceback

import numpy as np
import torch

from .. import core
from . import donor_train as DT
from . import select as SEL
from . import views as V

MANIFEST = os.path.join(V.CACHE_ROOT, "manifest.json")
PRIVATE_MANIFEST = os.path.join(core.OUT, "aln34", "prior33", "manifest.json")
MODE = "donor_training"
NORMALISATION_ACCESS = ("donor caches: fixed input preprocessing (z-score per participant x channel over all of that participant's "
                        "loaded pieces at 64 Hz, guards and masked cells excluded, masked cells 0; design §2.1); targets: per-stream "
                        "RMS of the 2-8 Hz envelope (stimulus-only) and the shared standardiser sigma from SparrKULee donor fit with "
                        "mu = 0 (§2.3); no target-cohort data (leave-target-out donor set, §3.1)")
CODE_FILES = ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "donor_train.py", "run_donor.py")
PINNED_NUMBER = ("members", "*", "best", "ce_dev")       # select.py: a JSON number (NaN counts as +inf), never null


def _open_manifest(row, manifest):
    sha = (row.get("spec") or {}).get("manifest_sha256")
    if not sha:
        raise ValueError(f"{row['experiment_id']}: the row has no spec.manifest_sha256")
    if isinstance(manifest, V.Manifest):
        if not manifest.sha256 or not manifest.sha256.startswith(str(sha).lower()):
            raise ValueError(f"manifest sha256 {str(manifest.sha256)[:16]} differs from the row's {str(sha)[:16]}")
        rsha = (row.get("spec") or {}).get("manifest_rich_sha256")
        if rsha and not V._match_sha(getattr(manifest, "rich_sha256", ""), rsha):
            return V.open_with_rich(manifest, rsha)
        return manifest
    if manifest is not None:
        return V.open_for_row(row, paths=[manifest], rich_paths=[os.path.join(os.path.dirname(manifest), V.MANIFEST_RICH)])
    return V.open_for_row(row, paths=[PRIVATE_MANIFEST, MANIFEST], cache_root=V.CACHE_ROOT,
                          rich_paths=[os.path.join(os.path.dirname(p), V.MANIFEST_RICH) for p in (PRIVATE_MANIFEST, MANIFEST)])


def bound_row(row):
    """The record's bound_row: a donor group has no ALN2 binding (core.bind is for target-cohort units)."""
    return {"experiment_id": row["experiment_id"], "family_id": row["family_id"], "dataset": row["dataset"], "seed": row["seed"],
            "subject_fold": row.get("subject_fold"), "content_fold": row.get("content_fold"),
            "binding": "E34 donor group: trained on the leave-target-out donor set of the target cohort (no ALN2 binding)"}


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else -math.inf


def gain_rule(rec):
    """Sensitivity choice of the joint member: higher dev gain of the _gainsel_best checkpoint, J025 only by >= GAIN_TIE, ties J1."""
    g = {m: rec["members"][m]["gainsel"]["gain"] for m in SEL.JOINT_CANDIDATES}
    a, b = _num(g["J1"]), _num(g["J025"])
    member = "J025" if b - a >= DT.GAIN_TIE else "J1"          # non-finite gains count as -inf; two of them tie (nan -> J1)
    return {"rule": DT.GAIN_RULE, "member": member, "gain": g, "tie": DT.GAIN_TIE, "checkpoint": "_gainsel_best.pt",
            "note": "sensitivity of the lambda choice; J* is resolved by joint_choice (select.LAMBDA_RULE)"}


def view_sha(manifest, row, log):
    """sha256 of what the unit trains and scores on: the manifest, the donor set entry and the fixed score-set rows."""
    blk = DT.SM.BLOCKS[row["spec"]["block"]]
    body = {"manifest_sha256": manifest.sha256, "target": row["dataset"], "donor_set_block": blk,
            "donor_set": manifest["donor_sets"][row["dataset"]][blk], "score_sets": (log.get("score_sets") or {}).get("rows_sha")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def coverage(manifest, row, log):
    smp = log.get("sampler") or {}
    return {"donor_set": {"strata": smp.get("strata"), "weights": smp.get("weights"), "n_segments": smp.get("n_segments"),
                          "n_participants": smp.get("n_participants"), "excluded_presentations": smp.get("excluded_presentations")},
            "seen_names": len(manifest["seen"][row["dataset"]]), "target_channel_coverage": manifest.get("coverage", {}).get(row["dataset"]),
            "hc_hcv_excluded_pairs": manifest.get("hc_hcv_excluded_pairs"), "score_sets": {k: v for k, v in (log.get("score_sets") or {}).items()
                                                                                          if k not in ("bank", "rows_sha")}}


def dependency(ups, rec, out):
    """The record's dependency field: the resolved upstreams without their bulky lists, each group upstream with code_hash_equal
    (its record's code_hash equals this unit's) and same_code_group (a rich group hashes rich.py too, so its hash differs from
    its core group's by construction). Recorded only: a continuation under changed code is not refused."""
    dep = {}
    for k, v in ups.items():
        if not isinstance(v, dict):
            dep[k] = os.path.relpath(v, out)
            continue
        d = {kk: vv for kk, vv in v.items() if kk not in ("hash_log", "files")}
        if "code_hash" in d:
            d["code_hash_equal"] = d.get("code_hash") is not None and d.get("code_hash") == rec.get("code_hash")
            d["same_code_group"] = d.get("code_group") == rec.get("code_group")
        dep[k] = d
    return dep


def _pinned(path):
    return len(path) == len(PINNED_NUMBER) and all(p == "*" or p == q for p, q in zip(PINNED_NUMBER, path))


def json_safe(o, path=(), replaced=None):
    """A copy of `o` with every non-finite float written as None, except the select.py-pinned members[M].best.ce_dev; the dotted
    paths replaced are appended to `replaced`."""
    if isinstance(o, dict):
        return {k: json_safe(v, path + (str(k),), replaced) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v, path + (str(i),), replaced) for i, v in enumerate(o)]
    if isinstance(o, (float, np.floating)) and not math.isfinite(float(o)):
        if _pinned(path):
            return float(o)
        if replaced is not None:
            replaced.append(".".join(path))
        return None
    return o


def run(row, out, epochs=None, *, manifest=None, device=None):
    gid = row["experiment_id"]
    path = os.path.join(out, "units", f"{gid}.json")
    dev = torch.device(device or "cuda")
    t0 = time.time()
    rec = core.new_record(row, bound_row(row), out)
    rec.update({"mode": MODE, "selection_level": DT.SELECTION_LEVEL, "target_contract": None,   # core's default is ALN3's dense20ms_v1
                "code_files_imported": [f"auditory_alignment_v3/prior33/{f}" for f in CODE_FILES]
                + (["auditory_alignment_v3/prior33/rich.py"] if row.get("family_id") == SEL.RICH_DONOR else [])})
    try:
        if epochs is not None and os.path.realpath(out) == os.path.realpath(core.OUT):
            raise ValueError("step overrides are probes and must write outside the production output directory")
        if SEL.stage_of(row) != "donor_group":
            raise ValueError(f"{gid}: run_donor runs donor-group rows only")
        man = _open_manifest(row, manifest)
        rec["manifest_sha256"], rec["target_contract"] = man.sha256, man["target_contract"]
        rec["manifest_rich_sha256"] = getattr(man, "rich_sha256", None)
        ups = DT.resolve_upstreams(row, out)
        rec["dependency"] = dependency(ups, rec, out)
        log = {}
        DT.train_donor_group(row, man, dev, os.path.join(out, "ckpt", gid), log, max_steps=epochs, upstream=ups,
                             cleanup=False, code_hash=rec["code_hash"])
        rec.update(log)
        if all(m in rec["members"] for m in SEL.JOINT_CANDIDATES):
            rec["joint_choice"] = SEL.joint_choice(rec)
            rec["gain_rule"] = gain_rule(rec)
        rec.update({"normalisation_access": NORMALISATION_ACCESS, "coverage": coverage(man, row, log), "view_sha256": view_sha(man, row, log)})
        try:
            jstar = SEL.check_group_record(rec, row)
            rec["record_check"] = {"ok": True, "joint_member": jstar}
        except SEL.SelectionError as ex:  # a finished group is never failed for this; the queue lists its J* rows as unresolved
            rec["record_check"] = {"ok": False, "error": str(ex)}
            print(f"WARNING {gid}: select.check_group_record: {ex}", flush=True)
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"
        rec["error"] = f"{type(ex).__name__}: {ex}"
        rec["traceback"] = traceback.format_exc()[-4000:]
    replaced = []
    rec = json_safe(rec, (), replaced)
    rec["nonfinite_to_null"] = {"count": len(replaced), "paths": replaced[:50],
                                "kept": "members[M].best.ce_dev (select.py pins a JSON number; NaN counts as +inf)"}
    core.write_record(path, rec, t0)              # technical_failed: writes .FAILED.json and exits 1 (the resume files stay)
    try:
        DT.remove_resume_files(out, gid)          # only after the complete record exists
    except OSError as ex:
        print(f"WARNING {gid}: resume files not removed: {ex!r}", flush=True)
