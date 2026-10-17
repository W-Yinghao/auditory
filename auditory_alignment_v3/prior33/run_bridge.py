"""E34_PUBLIC_PRIOR bridge unit (family ALN32_PUBLIC_AUDIO_PRIOR_BRIDGE, code group prior33_bridge; PUBLIC_PRIOR_DESIGN.md §2.11,
§4.3 Bridge, §6.1 `run_bridge.py`, §6.6 M6). Pool entry point: run(row, out, epochs=None), dispatched by run.py (RUNNER
"prior33_bridge": "prior33.run_bridge").

One unit = one slot (donor group, member): resolve the member (J* by the lambda rule on the complete donor-group record; only the
§2.11 slots select.SLOTS), load its `<gid>_m<M>_best.pt`, fit the source sound bridge on donor data only (bridge.fit_bridge, which
stores the checkpoint's sha256 in the npz), run the artefact-run probe, write ckpt/<bid>_bridge.npz (never offloaded) and the
unit record through core.new_record / core.write_record.

Record (beside core.new_record's fields; prior33_interfaces_M11.md): status (complete | technical_failed), target_contract
overwritten with the registered spec value, selection_level, member_resolved, alpha_uni, alpha_nat, tau_cal (scalar at n = 256;
tau_cal_by_pool_size), bridge_cal_r, artefact_probe {r_own, r_other, ...}, the accounting n_pairs / n_pairs_uni_cal / n_pairs_all /
bridge_seconds (inherited contract §6), tau tables, sigma and its source, native readout, mode "donor_bridge", normalisation
access, coverage, view_sha256 (the row lists and manifest), dependency (group id and code hash, checkpoint and its sha256),
bridge_file (npz path and sha256), and the fit diagnostics. A missing dependency (group record, checkpoint) is a technical_failed
record, never a silent return; every exception after the record path is named is caught into technical_failed (§6.1), including
those of core.bind and core.new_record (bridge.fallback_record then fills the identity fields it can), except that the
descriptive artefact probe records its own failure (artefact_probe.status technical_failed) without failing the bridge. No
gradient step is taken, so there is no resume state; `epochs` (the probe cap of the training runners) does not apply and is
recorded as such. Run as a module (python -m ...; select.py docstring "Entry points")."""
from __future__ import annotations

import os
import time
import traceback

import torch

from auditory_alignment_v3 import core

from . import bridge as BR
from . import select as SEL


def header(row, epochs=None):
    """Record fields set before any check (also on a fallback record): the registered target_contract, stage, mode, levels."""
    s = row.get("spec") if isinstance(row.get("spec"), dict) else {}
    h = {"stage": "bridge", "mode": "donor_bridge", "selection_level": BR.SELECTION_LEVEL, "normalisation_access": BR.NORMALISATION_ACCESS,
         "method": dict(BR.SPEC_RULES)}
    if s.get("target_contract") is not None:
        h["target_contract"] = s["target_contract"]      # the registered spec value, not core's dense20ms_v1 constant
    if epochs is not None:
        h["epochs_cap"] = f"{epochs} not applied: a bridge unit takes no gradient step"
    return h


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
        if SEL.stage_of(row) != "bridge":
            raise ValueError(f"{eid}: not a bridge row ({row.get('family_id')})")
        if s.get("target_contract") is None:
            raise ValueError(f"{eid}: spec.target_contract is required (§4.3); the record carries the registered value")
        BR.check_spec_rules(row)
        man = BR.open_row_manifest(row, manifest_path, cache_root)
        dep = BR.load_member(row, core.load_rows() if rows is None else rows, out)
        rec["member_resolved"] = dep["member"]
        rec["dependency"] = {"donor_group": dep["gid"], "slot": dep["slot"], "member": dep["member"],
                             "donor_group_code_hash": dep["group_record"].get("code_hash"),
                             "checkpoint": os.path.relpath(dep["ckpt_path"], core.REPO), "checkpoint_sha256": dep["ckpt_sha256"],
                             "checkpoint_kind": "best", "checkpoint_format": dep["ckpt_format"]}
        target, objective = row["dataset"], s["objective"]
        enc, tmap = BR.donor_encoder(dep["ckpt"], man, target, dev)
        sigma = BR.donor_bandwidths(dep["ckpt"], dep["group_record"], dep["member"])
        banks = BR.bridge_banks(man, target, dev, man.root)
        bridge = BR.fit_bridge(enc, man, target, objective, slot=dep["slot"], member=dep["member"], bridge_id=eid,
                               donor_group=dep["gid"], sigma=sigma, device=dev, root=man.root, banks=banks,
                               checkpoint_sha256=dep["ckpt_sha256"])
        try:                                      # descriptive only (§2.11): a probe failure is recorded, never fatal to the bridge
            probe = BR.artefact_probe(enc, bridge, man, device=dev, root=man.root, banks=banks)
        except Exception as ex:  # noqa: BLE001
            probe = {"status": "technical_failed", "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-2000:]}
        npz = BR.save_bridge(SEL.bridge_npz(out, eid), bridge)
        m = bridge.meta
        rec.update(BR.record_fields(bridge))
        rec.update(BR.jsonable({
            "artefact_probe": probe, "view_sha256": BR.sha_json({"manifest": m["manifest_sha256"], "fit": m["fit_rows_sha256"],
                                                                 "cal": m["cal_rows_sha256"], "uni_cal": m["uni_cal_rows_sha256"],
                                                                 "tau": m["tau_draws_sha256"]}),
            "coverage": {"donor_seen": tmap["seen_after"], "n_donor_seen": len(tmap["seen_after"]), "strata": m["strata"],
                         "fit_cohorts": m["fit_cohorts"], **bridge.info["counts"],
                         "target_cohort_rows": 0, "note": "leave-target-out: no row, file or statistic of the target cohort"},
            "fit_participants": m["fit_participants"], "cal_participants": m["cal_participants"],
            "uni_cal_participants": m["uni_cal_participants"],
            "rows_sha256": {k: m[k] for k in ("fit_rows_sha256", "cal_rows_sha256", "uni_cal_rows_sha256", "tau_draws_sha256")},
            "bridge_file": {"npz": os.path.relpath(npz, core.REPO), "sha256": BR.file_sha256(npz),
                            "checkpoint_sha256": m["checkpoint_sha256"]},
            "tensor_map": tmap, "manifest_sha256": m["manifest_sha256"]}))
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001 (every failure is a technical_failed record)
        if rec is None:                           # core.bind or core.new_record raised: a record is still written
            rec = BR.fallback_record(row, out, b)
            rec.update(header(row, epochs))
        rec["status"] = "technical_failed"
        rec["error"] = f"{type(ex).__name__}: {ex}"
        rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
