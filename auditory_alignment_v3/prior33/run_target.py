"""E34_PUBLIC_PRIOR target-unit runner (module M7; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.12, §4.3, §6.1
`run_target.py`, §6.3 RUNNER["prior33_target"] = "prior33.run_target"; record interface: aln34/prior33_interfaces_M11.md).

run(row, out, epochs=None, *, device=None, manifest_path=None, cache_root=None, rows=None, kids=None) runs one
ALN32_PUBLIC_AUDIO_PRIOR_TARGET row and writes units/<eid>.json through core.new_record / core.write_record (a failure is
written as units/<eid>.FAILED.json with status technical_failed, error and traceback, and exits 1, like every ALN3 runner).
Every exception after the record path is named is caught (§6.1), including those of TT.bind and core.new_record (a row without
subject_fold or seed, a family that FAMILY_GROUP does not list): fallback_record then fills the identity fields it can.
`epochs` caps the epochs for probes only. The keywords are for the probe and the tests: device (default "cuda"), manifest_path
(default: the first of MANIFEST = <views.CACHE_ROOT>/manifest.json and PRIVATE_MANIFEST = the 0444 copy under
private/auditory_alignment_v3/aln34/prior33/ that exists and has the row's sha256, cache root views.CACHE_ROOT, as run_donor.py
does), cache_root, rows (default core.load_rows(), which run.py points at plan + plan_ext) and kids (private children already
loaded; default data.load_private()).

Checks before any training (each failure is a technical_failed record, never a silent return):
  - fit_target.py is the generator's output for the current local_train.py (target_train.check_generated);
  - the row is a target row this runner can run (target_train.check_row: objective, target_seed = row seed, init / slot, the
    §4.3 recipe fields, and the equal-budget guard: spec.epochs 200 or absent, no spec.train_population);
  - the manifest's sha256 equals spec.manifest_sha256 (views.open_manifest); spec.target_contract, when present, equals the
    manifest's target_contract; spec.split_hash, when present, equals the manifest cell's;
  - pretrained arms: the slot's donor-group row (select.group_row: members, lambda rule) has the row's dataset, objective,
    donor seed and manifest; its record units/<gid>.json is complete (select.load_record); a J* slot is resolved by the lambda
    rule on that record (select.check_group_record, then select.member_of); the member checkpoint
    ckpt/<gid>_m<M>_best.pt (select.member_ckpt) exists, and when it carries donor_train.py's provenance fields (format
    prior33_donor_member_v1) they name this group, member, kind "best", contract and manifest. Its path, format and sha256 are
    recorded.

Record (prior33_interfaces_M11.md; analysis.normalise reads it):
  core.new_record fields; status; target_contract (public: the manifest's target_contract, the sha of standardiser, P and
  filters; private: "current_class", the private target, with the envelope contract under envelope_target_contract);
  selection_level (public "training identities, held-out early-stopping content (not new listeners)", private "training
  children, last 20 % of each child's physical blocks"); member_resolved (J* -> J1 / J025; the slot's tag otherwise; None for
  S); eval (ev2.evaluate_continuous, or ev2.evaluate_private + native_calibration); gainsel ("identical" when the two
  selection rules chose the same epoch, else "evaluated"; "unavailable" if the gain rule never had a finite score) and
  eval_gainsel (the gain-selected checkpoint, same structure as eval, only when evaluated); mode "T" (target-supervised) with input_mode "A"; coverage; normalisation_access; view_sha256 /
  pool_sha256; split_hash; manifest_sha256; tensor_map; trainable; selection {primary, sensitivity, identical};
  checkpoints {best, gainsel: file, epoch, sha256}; dependency (donor group, member, checkpoint, sha256, donor code hash);
  the training log (curve with both selection series, best_epoch, best_epoch_gainsel, objective_calibration, encoder, ...);
  resolved_config; declarations (by dataset and objective: the shared envelope coordinates and the external sound statistics of
  target_from_scratch are declared for public rows only, the target-stage NCE for NCE rows only; spec.nce / objective_calibration
  .nce are declared not to apply where the row does not train that NCE); fit_target (generator check, with the substitution
  labels and, separately, the engineering substitutions beyond design §2.12); schedule_check (the inherited cosine schedule's
  T_max against the realised optimiser steps).
"""
from __future__ import annotations

import os
import time
import traceback

import torch

from .. import core
from . import contract as C
from . import losses as L
from . import select as SEL
from . import target_train as TT
from . import views as V

CARD, LOGICAL_FAMILY = "E34_PUBLIC_PRIOR", "ALN32_PUBLIC_AUDIO_PRIOR"
MANIFEST = os.path.join(V.CACHE_ROOT, "manifest.json")                        # §6.2 (as run_donor.py)
PRIVATE_MANIFEST = os.path.join(core.OUT, "aln34", "prior33", "manifest.json")  # §6.2: the 0444 copy in the 0700 area
CKPT_FORMAT = "prior33_donor_member_v1"                                        # donor_train.py member checkpoints


def open_manifest(row, manifest_path=None, cache_root=None):
    """The frozen manifest, opened only with the row's spec.manifest_sha256 (views.open_manifest). Default: the first of
    MANIFEST and PRIVATE_MANIFEST that exists and has that sha256, with the cache root views.CACHE_ROOT (§6.2)."""
    paths = [manifest_path] if manifest_path is not None else [PRIVATE_MANIFEST, MANIFEST]
    return V.open_for_row(row, paths=paths, cache_root=cache_root or (None if manifest_path else V.CACHE_ROOT),
                          rich_paths=[os.path.join(os.path.dirname(p), V.MANIFEST_RICH) for p in paths])


def _check_donor_ckpt(state, gid, member, row):
    """Cross-check the provenance fields that donor_train.py writes into a member checkpoint (when they are present)."""
    if not isinstance(state, dict) or "format" not in state:
        return None
    s = row.get("spec") or {}
    want = {"format": CKPT_FORMAT, "group": gid, "member": member, "kind": "best", "contract": C.CONTRACT}
    bad = {k: (state.get(k), v) for k, v in want.items() if state.get(k) != v}
    ms, rs = state.get("manifest_sha256"), s.get("manifest_sha256")
    if ms and rs and not (str(ms).startswith(str(rs)) or str(rs).startswith(str(ms))):
        bad["manifest_sha256"] = (str(ms)[:16], str(rs)[:16])
    if bad:
        raise ValueError(f"dependency: the donor checkpoint does not belong to this slot / contract: {bad}")
    return state["format"]


def resolve_donor(row, rows, out):
    """{slot, init, member, state, dependency}: target_from_scratch (no donor) or the slot member's donor checkpoint, after the
    dependency re-checks of the module docstring. `rows` may be None (then core.load_rows())."""
    slot, init = TT.check_row(row)
    if slot == SEL.SCRATCH:
        return {"slot": slot, "init": init, "member": None, "state": None, "dependency": None}
    rows = core.load_rows() if rows is None else rows
    g = SEL.group_row(row, rows)
    gid, gs, s = g["experiment_id"], g.get("spec") or {}, row.get("spec") or {}
    bad = []
    if g.get("dataset") != row["dataset"]:
        bad.append(f"dataset {g.get('dataset')} vs {row['dataset']}")
    if gs.get("objective") != s.get("objective"):
        bad.append(f"objective {gs.get('objective')} vs {s.get('objective')}")
    if s.get("donor_seed") is not None and int(s["donor_seed"]) != int(g["seed"]):
        bad.append(f"spec.donor_seed {s['donor_seed']} vs the group seed {g['seed']}")
    if gs.get("manifest_sha256") and s.get("manifest_sha256") and gs["manifest_sha256"] != s["manifest_sha256"]:
        bad.append("manifest_sha256 differs from the donor group's")
    if bad:
        raise ValueError(f"donor group {gid} does not match the target row: " + "; ".join(bad))
    grec = SEL.load_record(out, gid)
    if grec is None:
        raise FileNotFoundError(f"dependency: donor group {gid} has no complete record ({SEL.record_path(out, gid)})")
    if grec.get("experiment_id") != gid:
        raise ValueError(f"dependency: the record {SEL.record_path(out, gid)} belongs to {grec.get('experiment_id')}")
    if grec.get("truncated") and os.path.realpath(out) == os.path.realpath(core.OUT):
        raise ValueError(f"dependency: donor group {gid} is truncated; probe records cannot initialise production targets")
    if slot == SEL.JOINT:
        SEL.check_group_record(grec, g)
    member = SEL.member_of(row, grec)
    ck = SEL.member_ckpt(out, gid, member, "best")
    if not os.path.exists(ck):
        raise FileNotFoundError(f"dependency: donor checkpoint {ck} is missing")
    state = TT.load_donor_state(ck)
    fmt = _check_donor_ckpt(state, gid, member, row)
    dep = {"donor_group": gid, "slot": slot, "member": member, "checkpoint": os.path.relpath(ck, out), "checkpoint_kind": "best",
           "checkpoint_sha256": TT.file_sha256(ck), "checkpoint_format": fmt, "donor_code_hash": grec.get("code_hash"),
           "donor_code_group": grec.get("code_group"), "donor_status": grec.get("status"), "donor_seed": g["seed"],
           "joint_choice": grec.get("joint_choice") if slot == SEL.JOINT else None, "truncated": grec.get("truncated")}
    return {"slot": slot, "init": init, "member": member, "state": state, "dependency": dep}


def declarations(slot, dataset, objective, member=None, gid=None, spec_nce=None, calib_nce=None):
    """The record's declared choices, by dataset (public envelope target / private current class) and objective (NCE / CS_SINGLE).
    spec_nce: the row's spec.nce; calib_nce: objective_calibration.nce as losses.ContractObjective.record wrote it (it writes the
    contract NCE tag for every objective). Each is declared not to apply where the row does not train that NCE."""
    private = dataset == TT.PRIVATE
    if private:
        out = ["64 Hz contract geometry (36 lag tokens on [0, 38) samples of the private 64 Hz input), shared by every arm; the "
               "private target is the current class, so no envelope target coordinate (manifest standardiser, stored P) enters the "
               "private path; native-rate ALN3 rows are different-contract references (§1 (e))"]
    else:
        out = ["64 Hz contract geometry (36 lag tokens on [0, 38) samples) and the shared target coordinates (manifest standardiser, "
               "mu = 0, and the stored P), shared by every arm; native-rate ALN3 rows are different-contract references (§1 (e))"]
    out.append("primary checkpoint: min es_loss, a risk on held-out early-stopping content of the training identities; the inherited "
               "A_LOCAL / E_LOCAL gain rule is the sensitivity checkpoint (§1 (f), §2.12)")
    if private:
        out.append(f"private 64 Hz input {V.PRIVATE_INPUT} (§2.1); the private Objective is auditory_alignment.train.Objective, unchanged "
                   + ("(prototype NCE on new 2 x 32 class prototypes)" if objective == "NCE" else
                      "(CS_SINGLE on the class labels; the class readouts are fitted at evaluation, E_LOCAL)"))
        if spec_nce is not None:
            out.append(f"spec.nce {spec_nce} (§4.3) names the continuous-path NCE and does not apply to the private path; "
                       "resolved_config.nce records what ran")
    elif objective == "NCE":
        out.append(f"target-stage NCE {L.NCE_TAG} (multi-positive log-sum-exp with the +-2 s family-clock neighbour mask); the A_LOCAL "
                   "deduplicated NCE remains the ALN3 native reference (§2.7)")
    else:
        out.append("target-stage CS_SINGLE: the A_LOCAL kernel Cauchy-Schwarz objective (auditory_alignment.train.Objective, "
                   "delegated unchanged by losses.ContractObjective; kernel bandwidths from the objective-calibration batch)")
        named = [f"{k} {v}" for k, v in (("spec.nce", spec_nce), ("objective_calibration.nce", calib_nce)) if v is not None]
        if named:
            out.append(f"{' and '.join(named)} name the NCE of the NCE rows and do not apply to this CS_SINGLE row "
                       "(losses.ContractObjective.record writes the tag for every objective); resolved_config.nce is None")
    if slot == SEL.SCRATCH and private:
        out.append("target_from_scratch: random initialisation from the target seed and no donor EEG pretraining; the private path "
                   "uses no external sound statistics (current-class target with a new class head; inherited contract §6)")
    elif slot == SEL.SCRATCH:
        out.append("target_from_scratch uses the shared target coordinates computed from the SparrKULee donor fit (external sound "
                   "statistics) but no donor EEG pretraining (inherited contract §6; design §2.3)")
    else:
        out.append(f"the full encoder is loaded strictly from member {member} of donor group {gid} (_best.pt, min donor-dev CE_dev); "
                   "donor-unseen target channels are opened at W = 0; every parameter trains at the same learning rate (§2.12)"
                   + ("; only EEG parameters transfer, the class head is new (§2.12, inherited contract §6)" if private else ""))
    return out


def schedule_check(log):
    """The inherited A_LOCAL schedule, CosineAnnealingLR(T_max = epochs x steps_per_epoch), against the realised optimiser steps
    (the scheduler steps with every finite optimiser step). A ratio above 1 means the cosine wrapped past its minimum and the
    learning rate rose again at the end: the A_LOCAL recipe, unchanged and identical across the arms of a cell (it depends on
    the cell's segment table only), recorded so that the engineering probe can read it on the 64 Hz segment tables."""
    t_max = int(log["epochs_completed"]) * int(log["steps_per_epoch"])
    n = int(log["optimizer_steps"])
    return {"cosine_t_max": t_max, "optimizer_steps": n, "realised_over_scheduled": n / t_max if t_max else None,
            "wrapped": n > t_max}


def header(row, epochs):
    """This runner's fields of every record (also of one whose binding failed)."""
    private = row.get("dataset") == TT.PRIVATE
    return {"card": CARD, "logical_family": LOGICAL_FAMILY, "execution_contract": C.CONTRACT, "stage": "target", "mode": "T",
            "mode_name": "target_supervised", "input_mode": V.PRIVATE_INPUT if private else TT.INPUT_MODE,
            "recipe": TT.RECIPE, "epochs_override": epochs, "truncated": {"epochs": epochs} if epochs is not None else None,
            "target_contract": "current_class" if private else None,
            "selection_level": TT.SELECTION_LEVEL["private" if private else "public"]}


def fallback_record(row, out, b=None):
    """The record of a unit whose binding (TT.bind) or core.new_record raised (a row without subject_fold or seed, a family that
    FAMILY_GROUP does not list): core.new_record's identity fields as far as they can be filled, so that the failure is still
    written as a technical_failed record (§6.1) instead of escaping the runner."""
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    fam = row.get("family_id")
    try:
        ch = core.code_hash(fam)
    except Exception:  # noqa: BLE001 - an unregistered family: the record says so through code_group None
        ch = None
    try:
        device = torch.cuda.get_device_name(0)
    except Exception:  # noqa: BLE001
        device = None
    return {"experiment_id": row["experiment_id"], "row": row, "bound_row": b, "code_hash": ch,
            "code_group": core.FAMILY_GROUP.get(fam) if isinstance(fam, str) else None, "runner": "auditory_alignment_v3",
            "status": "running", "device": device, "target_contract": None,
            "information_stratum": (row.get("spec") or {}).get("information_stratum") if isinstance(row.get("spec"), dict) else None}


def run(row, out, epochs=None, *, device=None, manifest_path=None, cache_root=None, rows=None, kids=None):
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")     # without an experiment_id no record can be named
    t0 = time.time()
    rec, b = None, None
    try:
        if epochs is not None and os.path.realpath(out) == os.path.realpath(core.OUT):
            raise ValueError("epoch overrides are probes and must write outside the production output directory")
        b = TT.bind(row, epochs)
        rec = core.new_record(row, b, out)
        rec.update(header(row, epochs))
        dev = torch.device(device or "cuda")
        ds, s = row["dataset"], row.get("spec") or {}
        private = ds == TT.PRIVATE
        ck = os.path.join(out, "ckpt", row["experiment_id"])
        gen = TT.check_generated()
        rec["fit_target"] = gen
        if not gen["ok"]:
            raise RuntimeError("; ".join(gen["problems"]))
        TT.check_row(row)
        man = open_manifest(row, manifest_path, cache_root)
        rec["manifest_sha256"] = man.sha256
        rec["manifest_rich_sha256"] = getattr(man, "rich_sha256", None)
        tc = man.get("target_contract")
        if not tc:
            raise ValueError("the manifest has no target_contract")
        if s.get("target_contract") not in (None, tc):
            raise ValueError(f"spec.target_contract {str(s['target_contract'])[:16]}... is not the manifest's {str(tc)[:16]}...")
        if private:
            rec["envelope_target_contract"] = tc
        else:
            rec["target_contract"] = tc
        cell = V.manifest_cell(man, ds, int(row["subject_fold"]), b["content_fold"])
        if s.get("split_hash") not in (None, cell.get("split_hash")):
            raise ValueError("spec.split_hash differs from the manifest cell's split_hash")
        rec["split_hash"] = cell.get("split_hash")
        dep = resolve_donor(row, rows, out)
        rec.update({"slot": dep["slot"], "init": dep["init"], "member_resolved": dep["member"], "dependency": dep["dependency"]})
        log = {}
        if private:
            res = TT.adapt_private(row, man, dev, ck, log, dep["state"], epochs=epochs, kids=kids)
        else:
            res = TT.adapt_public(row, man, dev, ck, log, dep["state"], epochs=epochs)
        rec.update(log)
        rec["eval"] = res["eval"]
        rec["gainsel"] = res["gainsel"]
        if res["gainsel"] == "evaluated":
            rec["eval_gainsel"] = res["eval_gainsel"]
        for k in ("tensor_map", "selection_level", "selection", "checkpoints", "coverage", "normalisation_access", "trainable", "cell",
                  "eval_seconds", "view"):
            rec[k] = res[k]
        if "class_head" in res:
            rec["class_head"] = res["class_head"]
        rec["view_sha256"], rec["pool_sha256"] = res["view"]["view_sha256"], res["view"]["pool_sha256"]
        rec["resolved_config"] = {
            "d": TT.D, "fs": C.FS, "input_samples": [0, C.L_IN], "epochs": res["bound_row"]["spec"]["epochs"], "optimizer": "AdamW",
            "lr": 1e-3, "weight_decay": 1e-4, "grad_clip": 5.0, "schedule": "cosine annealing over epochs x steps_per_epoch, no warmup",
            "validation": "every 5 epochs and the last epoch, on 40 fixed early-stopping batches", "temperature": 0.1,
            "bandwidth_multiplier": 1.0, "objective": s.get("objective"),
            "nce": None if s.get("objective") != "NCE" else ("prototype_nce (auditory_alignment.train.Objective)" if private else L.NCE_TAG),
            "audio_head": None if private else TT.HEAD_LABEL, "input": V.PRIVATE_INPUT if private else f"mode {TT.INPUT_MODE} cache",
            "init": dep["init"], "slot": dep["slot"], "member": dep["member"], "selection": TT.SELECTION,
            "batch": "up to 32 training children x 8 trials" if private else "up to 32 content-unique segments x 8 anchors (TickBatcher)",
            "seeds": TT.seeds_used(row)}
        rec["schedule_check"] = schedule_check(log)
        rec["declarations"] = declarations(dep["slot"], ds, s.get("objective"), dep["member"], (dep["dependency"] or {}).get("donor_group"),
                                           spec_nce=s.get("nce"), calib_nce=(rec.get("objective_calibration") or {}).get("nce"))
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001 - recorded, never hidden
        if rec is None:                                  # TT.bind or core.new_record raised: a record is still written
            rec = fallback_record(row, out, b)
            rec.update(header(row, epochs))
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
