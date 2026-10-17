"""E34_PUBLIC_PRIOR zero-shot unit (family ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT, code group prior33_zeroshot; PUBLIC_PRIOR_DESIGN.md
§2.13, §4.3 Zero-shot, §6.1 `run_zeroshot.py`, §6.6 M6). Pool entry point: run(row, out, epochs=None), dispatched by run.py
(RUNNER "prior33_zeroshot": "prior33.run_zeroshot").

One unit = one (slot, cell, access mode): resolve the member (J* by the lambda rule on the complete donor-group record; only the
§2.11 slots), load its `<gid>_m<M>_best.pt` and the slot's frozen bridge ckpt/<bid>_bridge.npz (spec.bridge), then
zeroshot.evaluate_zero_shot (every participant loaded, train_p empty, queries of the fold only, nothing fitted on target data) and
write the record through core.new_record / core.write_record.

Checks before the evaluation (each failure is a technical_failed record): spec.variant is the full §2.13 name of spec.mode
(contract.ZS_MODE_NAME, as make_plan_ext_prior33.py writes it); the bridge record units/<bid>.json is complete and is the record
of spec.bridge for the same donor group and member; the npz is the file that record names (its sha256 equals bridge_file.sha256)
and names the same bridge id, group, slot, member, objective and manifest; and the bridge was fitted on THIS member checkpoint:
the npz's checkpoint_sha256 and the bridge record's dependency.checkpoint_sha256 both equal the sha256 of the _best.pt loaded
now (a checkpoint replaced after the bridge was fitted is refused).

Record (beside core.new_record's fields; prior33_interfaces_M11.md): status, target_contract overwritten with the registered spec
value, selection_level (zeroshot.SELECTION_LEVEL, containing "donor dev"), member_resolved, eval (B_uni) and eval_uni_cal (the
sensitivity bridge), mode / mode_name, normalisation_access, coverage, view_sha256 / pool_sha256, zero_shot (purity), the
temperatures used, native readout, bridge (bridge.bridge_row_info: incl. the bridge's audio-pair count and seconds), dependency
(group, checkpoint, bridge record and npz with their sha256). The private cohort is refused (technical_failed: speech zero-shot is
not computed for it). A missing dependency is a technical_failed record; every exception after the record path is named is
caught into technical_failed, including those of core.bind and core.new_record (bridge.fallback_record). No gradient step:
`epochs` does not apply and is recorded as such. Run as a module."""
from __future__ import annotations

import os
import time
import traceback

import torch

from auditory_alignment_v3 import core

from . import bridge as BR
from . import contract as C
from . import select as SEL
from . import zeroshot as ZS


def header(row, epochs=None):
    """Record fields set before any check (also on a fallback record): the registered target_contract, stage, level."""
    s = row.get("spec") if isinstance(row.get("spec"), dict) else {}
    h = {"stage": "zero_shot", "selection_level": ZS.SELECTION_LEVEL}
    if s.get("target_contract") is not None:
        h["target_contract"] = s["target_contract"]      # the registered spec value, not core's dense20ms_v1 constant
    if epochs is not None:
        h["epochs_cap"] = f"{epochs} not applied: a zero-shot unit takes no gradient step"
    return h


def check_bridge(bridge, row, dep, brec, npz_sha):
    """The frozen bridge belongs to this row's slot, manifest and member checkpoint (module docstring); raises ValueError."""
    s = row.get("spec") or {}
    m = bridge.meta
    want = {"bridge_id": s.get("bridge"), "donor_group": dep["gid"], "slot": dep["slot"], "member": dep["member"],
            "manifest_sha256": s.get("manifest_sha256")}
    bad = {k: (m.get(k), v) for k, v in want.items() if v is not None and m.get(k) != v}
    if bridge.objective != s.get("objective"):
        bad["objective"] = (bridge.objective, s.get("objective"))
    bd, bf = brec.get("dependency") or {}, brec.get("bridge_file") or {}
    if brec.get("experiment_id") != s.get("bridge"):
        bad["bridge_record"] = (brec.get("experiment_id"), s.get("bridge"))
    for k in ("donor_group", "member"):
        if bd.get(k) != want[k]:
            bad[f"bridge_record.dependency.{k}"] = (bd.get(k), want[k])
    if bf.get("sha256") != npz_sha:
        bad["bridge_file.sha256"] = (str(bf.get("sha256"))[:16], npz_sha[:16])
    ck = dep["ckpt_sha256"]
    if m.get("checkpoint_sha256") != ck:
        bad["npz checkpoint_sha256"] = (str(m.get("checkpoint_sha256"))[:16], ck[:16])
    if bd.get("checkpoint_sha256") != ck:
        bad["bridge_record.dependency.checkpoint_sha256"] = (str(bd.get("checkpoint_sha256"))[:16], ck[:16])
    if bad:
        raise ValueError(f"{row['experiment_id']}: the bridge does not belong to this slot / manifest / checkpoint: {bad}")


def run(row, out, epochs=None, *, device=None, manifest_path=None, cache_root=None, rows=None):
    """Pool entry point (module docstring). The keywords are for the probe and the tests (the pool calls run(row, out, epochs)):
    device (default "cuda"); manifest_path / cache_root (default: <views.CACHE_ROOT>/manifest.json, else the private 0444 copy,
    with the cache root views.CACHE_ROOT; bridge.open_row_manifest, as run_donor.py / run_target.py); rows (default
    core.load_rows(), which run.py points at plan + plan_ext)."""
    eid = row["experiment_id"]                    # without an experiment_id no record can be named
    path = SEL.record_path(out, eid)
    t0 = time.time()
    rec, b = None, None
    try:
        b = core.bind(BR.bindable(row))
        rec = core.new_record(row, b, out)
        rec.update(header(row, epochs))
        dev = torch.device(device or "cuda")
        s = row.get("spec") or {}
        if SEL.stage_of(row) != "zero_shot":
            raise ValueError(f"{eid}: not a zero-shot row ({row.get('family_id')})")
        if row.get("dataset") == "private_bdf":
            raise ValueError(ZS.PRIVATE_NO_ZS)
        rec["mode"] = ZS.canonical_mode(s.get("mode"))
        rec["mode_name"] = C.ZS_MODE_NAME[rec["mode"]]
        if s.get("variant") != rec["mode_name"]:
            raise ValueError(f"{eid}: spec.variant {s.get('variant')!r} is not the §2.13 name {rec['mode_name']!r} of mode {rec['mode']}")
        if s.get("target_contract") is None:
            raise ValueError(f"{eid}: spec.target_contract is required (§4.3); the record carries the registered value")
        man = BR.open_row_manifest(row, manifest_path, cache_root)
        dep = BR.load_member(row, core.load_rows() if rows is None else rows, out)
        rec["member_resolved"] = dep["member"]
        bid = s.get("bridge")
        if not bid:
            raise ValueError(f"{eid}: spec.bridge (the slot's bridge row) is required (§4.3)")
        brec = SEL.load_record(out, bid)
        if brec is None:
            raise BR.DependencyError(f"bridge {bid}: no complete record units/{bid}.json")
        npz = SEL.bridge_npz(out, bid)
        if not os.path.exists(npz):
            raise BR.DependencyError(f"bridge {bid}: {os.path.basename(npz)} is missing")
        npz_sha = BR.file_sha256(npz)
        bridge = BR.load_bridge(npz, expect_id=bid)
        check_bridge(bridge, row, dep, brec, npz_sha)
        rec["dependency"] = {"donor_group": dep["gid"], "slot": dep["slot"], "member": dep["member"],
                             "donor_group_code_hash": dep["group_record"].get("code_hash"),
                             "checkpoint": os.path.relpath(dep["ckpt_path"], core.REPO), "checkpoint_sha256": dep["ckpt_sha256"],
                             "checkpoint_kind": "best", "checkpoint_format": dep["ckpt_format"],
                             "bridge": bid, "bridge_code_hash": brec.get("code_hash"),
                             "bridge_npz": os.path.relpath(npz, core.REPO), "bridge_npz_sha256": npz_sha,
                             "bridge_checkpoint_sha256": bridge.meta.get("checkpoint_sha256")}
        rec.update(ZS.evaluate_zero_shot(row, man, dev, dep["ckpt"], bridge, root=man.root))
        rec["manifest_sha256"] = man.sha256
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001 (every failure is a technical_failed record)
        if rec is None:                           # core.bind or core.new_record raised: a record is still written
            rec = BR.fallback_record(row, out, b)
            rec.update(header(row, epochs))
        rec["status"] = "technical_failed"
        rec["error"] = f"{type(ex).__name__}: {ex}"
        rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
