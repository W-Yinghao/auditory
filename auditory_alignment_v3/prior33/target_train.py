"""E34_PUBLIC_PRIOR target-supervised adaptation (module M7; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.12, §3.3,
§4.3, §6.1 `target_train.py`, §6.6 M7; contract aln33_env64_125ms_v1; inherited PUBLIC_PRIOR_EXECUTION_v3_3.md §6).

  adapt_public(row, manifest, dev, ck, log, donor_state, epochs=None)
  adapt_private(row, manifest, dev, ck, log, donor_state, epochs=None, kids=None)
      -> {"eval", "eval_gainsel", "gainsel", "tensor_map", "selection_level", "selection", "checkpoints", "view", "coverage",
          "normalisation_access", "trainable", "cell", "bound_row"}
  Build the target view of the row's cell, train with the generated copy of the A_LOCAL / E_LOCAL recipe (fit_target.py:
  fit_continuous_p33 / fit_private_p33, written by gen_fit_target.py from local_train.py), then evaluate both checkpoints:
  <ck>_best.pt (primary: min es_loss) and <ck>_gainsel_best.pt (sensitivity: min es_loss - es_loss_mismatched / _permuted).
  When their epochs coincide, gainsel = "identical" and eval_gainsel is None; otherwise gainsel = "evaluated" (and "unavailable",
  with eval_gainsel None, in the numerical corner where the gain rule never had a finite score, so no _gainsel_best.pt exists).
  ck is the checkpoint prefix (ckpt/<eid>); log receives the training log (curve, both best epochs and scores, calibration).

Cells (§3.3): the 30 ALN3 A_LOCAL / E_LOCAL cells as the frozen manifest binds them (target_cells: FAU 10, DTU 10, Federici 5,
private_bdf 5). Public cells: views.target_view(cohort, cf, manifest, "A") holds ALL participants of the cohort (the zero-shot rows
of the cell see the same pools); views.TickBatcher trains on the manifest cell's training participants only (it refuses a cell
whose fold-derived training set differs from cell.train, and any cell.test / test_only participant), on fit segments, with the
40 fixed early-stopping batches on es segments of the same participants. Private cells: views.load_private64 (data.load_private()
plus the 64 Hz input x64, in memory); the children of PrivateBatcher64's training fold must equal the manifest cell's train list
and the fold's test children its test list.

Arms (§2.12, §4.1; the runner resolves the slot and passes donor_state): target_from_scratch (S; donor_state None: random
initialisation from the target seed, the same architecture and the shared coordinates) and the pretrained slots AP, XP, J*, XM
(and APR, APC, XPC in the rich / CSX blocks): the full SharedEncoder loaded strictly from the slot member's donor checkpoint
(model.build_target_encoder -> load_donor(strict=True, open_new=True): donor-unseen target channels opened at W = 0); every
parameter trains with the same learning rate. Every arm of a cell gets the identical budget: the same epochs, the same batcher
and seed (identical batch streams and anchors), the same optimiser, schedule and validation set. The private cohort trains a
new class head (§2.12: only EEG parameters transfer; the 2 x 32 prototypes are new and trained for NCE; the CS_SINGLE recipe has
no head parameter, its class readouts are fitted at evaluation as in E_LOCAL); no speech zero-shot is computed for it.

Evaluation (§2.12): ev2.evaluate_continuous with ev1.Reps replaced by views.TickReps inside try / finally (core.evaluate_grid
precedent); the unified ridge and the temperature are fitted on the target training side (ev1.Readouts / calibrate: training
participants' fit / es segments). Private: ev2.evaluate_private plus calib.private_variants under eval.native_calibration
(run_private / run_transfer precedent), both unchanged.

Interpretations (each also listed as a deviation in the M7 summary):
- bind(row, epochs=None): the ALN2-compatible row for the generated copy keeps the whole plan spec (init, target_seed and the §4.3
  geometry fields, which build_target_encoder checks) and sets epochs (the plan's, default 200; `epochs` overrides it for
  probes only), training_task (paired_alignment; private current_class), audio_head (a label: the head is SharedFixedHead) and
  content_fold 0 when the row has none (private), as core.bind does. check_row refuses rows whose objective is not NCE /
  CS_SINGLE, whose spec.target_seed differs from the row seed (§4.3: a target row's seed is its target_seed), whose spec.mode is
  not T / A, whose init / slot disagree, whose slot is a concrete joint member J1 / J025 (a target arm is J*, resolved by the
  lambda rule; M8 review item b), whose slot-like spec.variant names another slot (item h; a descriptive variant such as
  "cross_person_pretrain" is not checked), and whose spec.recipe / selection / target / training_task / nce / private_input
  (private), when present, differ from what this module implements (§4.3).
- Equal budgets (§2.12, §4.3, §4.4; inherited §6 "all versions the same budget"): check_row also refuses spec.epochs other than
  200 (EPOCHS) and any spec.train_population (views.TickBatcher would accept a subset of cell.train for it), the two spec fields
  through which a plan row could change its training budget or training set while still pairing with the other arms of its
  cell (analysis pairs on split_hash, target, target_contract, eval version and manifest only). The probe-only `epochs` argument
  is not a spec field: the runner records it as epochs_override. adapt_public / adapt_private run check_row themselves, so the
  library path is guarded as well as the runner.
- spec.nce on private rows: §4.3 lists nce = contract_lse_mask2s_v1 for every target row, and the plan writes it on private rows
  too, while the private path runs auditory_alignment.train.Objective unchanged (§2.12 item 6: its prototype NCE, or CS_SINGLE).
  check_row accepts that label (and None) on private rows and refuses any other value; the runner declares that the label does
  not apply and records what ran in resolved_config.nce.
- The target stage always reads the mode-A cache (the fixed input preprocessing, INPUT_MODE): §2.13 compares zero-shot modes
  with "the adapted row of the same cell", so the adapted rows have one input mode.
- The donor checkpoint (ckpt/<gid>_m<M>_best.pt, select.member_ckpt) holds the SharedEncoder state dict or a dict with it under
  "enc" (model's convention); it is read with torch.load(weights_only=True). A donor's rich.* heads are dropped and listed by
  load_donor.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

import numpy as np
import torch

from auditory_alignment import evaluate as ev1
from auditory_alignment_v2 import evaluate as ev2

from .. import calib as CAL
from . import contract as C
from . import fit_target as FT
from . import gen_fit_target as GEN
from . import losses as L
from . import model as M
from . import select as SEL
from . import views as V

PRIVATE = "private_bdf"
PUBLIC = V.TARGET_COHORTS                                   # fau, dtu, federici
CELL_COUNTS = {"fau": 10, "dtu": 10, "federici": 5, PRIVATE: 5}   # §3.3: the 30 ALN3 cells
OBJECTIVES = L.CONTRACT_OBJECTIVES                          # NCE, CS_SINGLE
EPOCHS = 200                                                # §2.12 / §4.3 (A_LOCAL / E_LOCAL)
D = M.D_OUT                                                 # 32
INPUT_MODE = "A"                                            # the cached contract input (fixed input preprocessing)
RECIPE = "a_local_recipe_on_aln33_v2"                       # §4.3 recipe
HEAD_LABEL = "shared_fixed_head_v1"                         # SharedFixedHead(sigma, P): manifest standardiser (mu = 0), stored P
ARMS_CORE = (SEL.SCRATCH, "AP", "XP", SEL.JOINT, "XM")      # §4.1 core / panel target variants; rich APR, CSX APC / XPC
CKPT = {"best": "_best.pt", "gainsel": "_gainsel_best.pt"}
SELECTION = {"primary": "min_es_loss", "sensitivity": "min_es_loss_minus_mismatch"}     # §4.3 spec.selection
SELECTION_LEVEL = {"public": "training identities, held-out early-stopping content (not new listeners)",     # §2.12
                   "private": "training children, last 20 % of each child's physical blocks"}
ACCESS_A = {  # §2.13 mode A: what the cached input touched in target data (the target stage reads the same cache)
    "fau": "z-score incl. test content; the stage-B ICA rule removes a component when its 1-8 Hz correlation with the presented "
           "envelopes of all 20 trials peaks within +-3 samples (> 15 dB); CI interpolation (masked)",
    "dtu": "z-score incl. test content; CAR over the 64 EEG channels",
    "federici": "z-score incl. test blocks; the authors' ICA and 2-8 Hz filter"}
Z_RULE = ("per participant x channel z-score at 64 Hz over all of that participant's cached pieces, guard samples and masked "
          "(piece, channel) cells excluded; masked channels set to 0 (§2.1, data._stdz semantics)")
TARGET_ACCESS = ("per-stream RMS normalisation (stimulus-only; with mu = 0 it cannot change a target-side output, §2.3); the "
                 "manifest standardiser (sigma fitted on the SparrKULee donor fit, mu = 0) and the stored P; the unified ridge and "
                 "the temperature fitted on the target training side (ev1 Readouts / calibrate)")
PRIVATE_ACCESS = ("hc.load_children per-child z-score at 250 Hz; reflect pad 75 samples, 32/125 with h_aa, 20 Hz Butterworth "
                  "low-pass; z-score per child x channel at 64 Hz over all of that child's [32, 70) windows (load_private64, in "
                  "memory, no label); window [32, 70) of the 90-sample output")


# ---------------------------------------------------------------------------------------------------------- rows and cells
def _sha_json(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bind(row, epochs=None):
    """ALN2-compatible row for fit_target / ev2: the plan row with its whole spec, plus epochs, training_task and audio_head."""
    s = dict(row.get("spec") or {})
    ds = row["dataset"]
    private = ds == PRIVATE
    ep = epochs if epochs is not None else (s.get("epochs") if s.get("epochs") is not None else EPOCHS)
    s.update({"architecture": s.get("architecture") or M.ARCH, "window": s.get("window") or "full",
              "training_task": "current_class" if private else (s.get("training_task") or "paired_alignment"),
              "epochs": int(ep), "audio_head": None if private else HEAD_LABEL})
    return {"experiment_id": row["experiment_id"], "family_id": row.get("family_id"), "dataset": ds, "subject_fold": row["subject_fold"],
            "content_fold": 0 if row.get("content_fold") is None else row["content_fold"], "seed": row["seed"], "spec": s}


def _bound(row, epochs):
    """check_row (the equal-budget and recipe guards also hold when adapt_* is called directly), then bind."""
    check_row(row)
    b = bind(row, epochs)
    if b["spec"]["epochs"] < 1:
        raise ValueError(f"epochs {b['spec']['epochs']}: at least one epoch (one validation) is needed for a checkpoint")
    return b


def arm_of(row):
    """(slot, init): ("S", "random") for target_from_scratch, else (slot name, "donor") with J* unresolved (select.slot_of)."""
    sl = SEL.slot_of(row)
    return (SEL.SCRATCH, "random") if sl is None else (sl[1], "donor")


def check_row(row):
    """Raise ValueError unless `row` is a target row this module can run (stage, objective, seeds, init / slot, input mode, the
    equal-budget guard on spec.epochs / spec.train_population, the §4.3 recipe fields) -> (slot, init)."""
    if SEL.stage_of(row) != "target":
        raise ValueError(f"{row.get('experiment_id')}: not a target row ({row.get('family_id')})")
    s = row.get("spec") or {}
    if s.get("objective") not in OBJECTIVES:
        raise ValueError(f"objective {s.get('objective')!r} is not one of {OBJECTIVES}")
    ts = s.get("target_seed")
    if ts is not None and int(ts) != int(row["seed"]):
        raise ValueError(f"spec.target_seed {ts} differs from the row seed {row['seed']} (§4.3: a target row's seed is its target_seed)")
    if s.get("mode") not in (None, "T", INPUT_MODE):
        raise ValueError(f"target rows train on the mode-{INPUT_MODE} input (mode T); spec.mode = {s['mode']!r}")
    slot, init = arm_of(row)
    if s.get("init") is not None and s["init"] != init:
        raise ValueError(f"spec.init {s['init']!r} disagrees with the slot {slot} ({init})")
    if slot in SEL.JOINT_CANDIDATES:
        raise ValueError(f"slot {slot}: a target row names the joint slot J*, resolved by the lambda rule, never J1 / J025 (§2.9, §4.1)")
    v = s.get("variant")
    try:
        cv = SEL.canonical_slot(v) if isinstance(v, str) else None
    except ValueError:
        cv = None                                            # a descriptive variant name (e.g. the contract's), not a slot
    if cv is not None and cv != slot:
        raise ValueError(f"spec.variant {v!r} disagrees with the slot {slot} the row resolves to (spec.member / init)")
    if row["dataset"] not in CELL_COUNTS:
        raise ValueError(f"dataset {row['dataset']!r} is not a target cohort {tuple(CELL_COUNTS)}")
    if s.get("epochs") is not None and (isinstance(s["epochs"], bool) or s["epochs"] != EPOCHS):
        raise ValueError(f"spec.epochs {s['epochs']!r}: every target arm trains {EPOCHS} epochs (§2.12, §4.3; equal budgets); "
                         "a probe caps epochs through the runner's epochs argument, never through the plan row")
    if s.get("train_population") is not None:
        raise ValueError(f"spec.train_population {s['train_population']!r}: every target arm trains on the manifest cell's training "
                         "participants (equal budgets, §2.12); a training subset is not part of this block")
    private = row["dataset"] == PRIVATE
    want = {"recipe": RECIPE, "selection": SELECTION, "target": "current_class" if private else "envelope",
            "training_task": "current_class" if private else "paired_alignment", "nce": L.NCE_TAG,     # private: a label (docstring)
            **({"private_input": V.PRIVATE_INPUT} if private else {})}
    bad = {k: s[k] for k, v in want.items() if s.get(k) is not None and s[k] != v}
    if bad:
        raise ValueError(f"the row asks for {bad}; this runner implements {({k: want[k] for k in bad})} (§4.3)")
    return slot, init


def seeds_used(row):
    """The seeds a target unit uses (§4.3 readout_seeds: runner-defined). The A_LOCAL target_stats seed (target_seed + 5) is not
    used: the standardiser is the manifest's."""
    t = int(row["seed"])
    private = row["dataset"] == PRIVATE
    cs = row["spec"]["objective"] == "CS_SINGLE"
    out = {"target_seed": t, "torch_and_batches": t,
           "objective_calibration_batch": t + 99,
           "objective_calibration_rows": t + 98 if not private else None,
           "evaluation_readouts": t + 1000 if not private else None,
           "early_stopping_batches": "batch index 0..39" if private else 12345,
           "early_stopping_anchors": None if private else "batch index 0..39 (same anchors for true and rolled audio)",
           "encoder_init": t if arm_of(row)[1] == "random" else "donor checkpoint"}
    if private:
        out.update({"early_stopping_label_permutation": 54321, "private_kernel_subsample": t + 77 if cs else None})
    return out


def target_cells(manifest, expect=True):
    """The manifest's target cells [(dataset, subject_fold, content_fold, split_hash)] in manifest order; with `expect` the counts
    must be the §3.3 ones (FAU 10, DTU 10, Federici 5, private_bdf 5)."""
    cells = [(c["dataset"], int(c["subject_fold"]), int(c["content_fold"]), c.get("split_hash")) for c in manifest["cells"]]
    n = {k: sum(c[0] == k for c in cells) for k in CELL_COUNTS}
    if expect and (n != CELL_COUNTS or len(cells) != sum(CELL_COUNTS.values())):
        raise ValueError(f"manifest target cells {n} (total {len(cells)}) differ from the 30 ALN3 cells {CELL_COUNTS}")
    if len(set(c[:3] for c in cells)) != len(cells):
        raise ValueError("manifest target cells repeat a (dataset, subject_fold, content_fold)")
    return cells


def check_generated():
    """fit_target.py must be the generator's output for the current local_train.py: its recorded source sha256 equals the file's,
    and its text equals gen_fit_target.generate(local_train.py) byte for byte (no hand edit, no stale copy). The result lists
    the applied substitutions and, separately, the engineering ones beyond the design's §2.12 list (written into every record)."""
    src = GEN.read_source(GEN.SOURCE)
    sha = GEN.sha256_text(src)
    with open(GEN.OUTPUT, encoding="utf-8") as f:
        text = f.read()
    problems = []
    if FT.SOURCE_SHA256 != sha:
        problems.append(f"fit_target.py was generated from local_train.py sha256 {FT.SOURCE_SHA256[:16]}..., the file is {sha[:16]}...")
    if text != GEN.generate(src):
        problems.append("fit_target.py differs from gen_fit_target.generate(local_train.py)")
    return {"ok": not problems, "source": GEN.SOURCE_REL, "source_sha256": sha, "file": GEN.OUTPUT_REL,
            "file_sha256": GEN.sha256_text(text), "generator": GEN.GENERATOR_REL, "problems": problems,
            "substitutions": list(FT.SUBSTITUTIONS), "engineering_substitutions": list(FT.ENGINEERING_SUBSTITUTIONS)}


def load_donor_state(path):
    """A donor member checkpoint (select.member_ckpt) on the CPU, read with the restricted loader (tensors and containers only)."""
    return torch.load(path, map_location="cpu", weights_only=True)


# ---------------------------------------------------------------------------------------------------------- evaluation
def evaluate_public(b, enc, head, bt, coh, calib):
    """ev2.evaluate_continuous on the contract ticks (ev1.Reps -> views.TickReps for the call, restored in finally)."""
    orig = ev1.Reps
    ev1.Reps = V.TickReps
    try:
        return ev2.evaluate_continuous(b, enc, head, bt, coh, calib, None)
    finally:
        ev1.Reps = orig


def evaluate_private(b, enc, bt, calib, protos):
    """ev2.evaluate_private plus calib.private_variants under eval.native_calibration (E_LOCAL / run_transfer)."""
    out = ev2.evaluate_private(b, enc, bt, calib, protos)
    out["native_calibration"] = CAL.private_variants(b, enc, bt, protos, calib)
    return out


def _selection(log, ck):
    """(status, selection record): status "identical" (both rules chose the same epoch), "evaluated" (different epochs) or
    "unavailable" (the gain rule never had a finite score, so no _gainsel_best.pt exists; the primary result stands)."""
    eg = log["best_epoch_gainsel"]
    status = "unavailable" if eg is None or eg < 1 else ("identical" if eg == log["best_epoch"] else "evaluated")
    return status, {"primary": {"rule": SELECTION["primary"], "epoch": log["best_epoch"], "es_loss": log["best_es_loss"],
                                "checkpoint": os.path.basename(ck + CKPT["best"])},
                    "sensitivity": {"rule": SELECTION["sensitivity"], "epoch": eg, "selection_score": log["best_selection_score_gainsel"],
                                    "checkpoint": None if status == "unavailable" else os.path.basename(ck + CKPT["gainsel"])},
                    "identical": status == "identical", "status": status, "curves": log.get("selection_curves")}


def _checkpoints(ck, log, status):
    out = {}
    for k, ep in (("best", log["best_epoch"]), ("gainsel", log["best_epoch_gainsel"])):
        p = ck + CKPT[k]
        if k == "gainsel" and status == "unavailable":
            out[k] = None
            continue
        if not os.path.exists(p):
            raise FileNotFoundError(f"the {k} checkpoint {p} was not written")
        out[k] = {"file": os.path.basename(p), "epoch": ep, "sha256": file_sha256(p)}
    return out


def _trainable(enc, layout, protos=None, train_protos=False):
    n = int(sum(p.numel() for p in enc.parameters() if p.requires_grad))
    off = int(enc.spatial.W.shape[1]) * (len(C.VOCAB) - len(layout))      # W rows of names outside the layout get no input
    return {"encoder": n, "encoder_reaching_the_layout": n - off, "prototypes": int(protos.numel()) if (protos is not None and train_protos) else 0,
            "audio_head": 0, "all_parameters_train": all(p.requires_grad for p in enc.parameters()), "learning_rate": 1e-3}


def _channels(tmap, layout):
    if "coverage" in tmap:                                   # donor arm: load_donor's coverage (seen before opening)
        return {**tmap["coverage"], "opened": list(tmap.get("opened_rows", [])), "init": "donor"}
    return {"n_seen": 0, "n_total": len(layout), "unseen": [], "opened": [], "init": "random",
            "note": "from scratch: every target channel is trained from the target-seed initialisation"}


# ---------------------------------------------------------------------------------------------------------- public targets
def adapt_public(row, manifest, dev, ck, log, donor_state, epochs=None):
    """Train and evaluate one public target cell (FAU / DTU / Federici) for one arm (module docstring)."""
    b = _bound(row, epochs)
    ds, sf, cf = b["dataset"], int(b["subject_fold"]), int(b["content_fold"])
    if ds not in PUBLIC:
        raise ValueError(f"adapt_public: {ds!r} is not a public target cohort {PUBLIC}")
    cell = V.manifest_cell(manifest, ds, sf, cf)
    coh = V.target_view(ds, cf, manifest, INPUT_MODE)
    meta, layout = dict(coh.meta), list(coh.layout)
    enc, head, bt = FT.fit_continuous_p33(b, coh, dev, ck, log, d=D, manifest=manifest, donor_state=donor_state)
    access = bt.training_access(coh)
    outer = set(map(str, cell["test"])) | set(map(str, cell.get("test_only", ())))
    if set(access["train_participants"]) & outer or bt.zero_shot:
        raise AssertionError("adapt_public: an outer-test participant entered the training side")
    status, selection = _selection(log, ck)
    ckpts = _checkpoints(ck, log, status)
    cal = log["objective_calibration"]
    t1 = time.time()
    ev = evaluate_public(b, enc, head, bt, coh, cal)
    evg = None
    if status == "evaluated":
        sd = torch.load(ck + CKPT["gainsel"], map_location=dev)
        enc.load_state_dict(sd["enc"]); head.load_state_dict(sd["head"]); enc.eval(); head.eval()
        evg = evaluate_public(b, enc, head, bt, coh, cal)
    n_q = len(V.test_queries(coh, sf))
    return {"eval": ev, "eval_gainsel": evg, "gainsel": status, "tensor_map": enc.tensor_map, "selection_level": SELECTION_LEVEL["public"],
            "selection": selection, "checkpoints": ckpts, "bound_row": b, "eval_seconds": round(time.time() - t1, 1),
            "view": {k: meta.get(k) for k in ("view_sha256", "pool_sha256", "content_sha256", "manifest_sha256", "mode", "cache", "contract",
                                              "n_segments", "n_participants", "n_segments_meeting_shared_audio")},
            "coverage": {"channels": _channels(enc.tensor_map, layout), "manifest_zero_shot_coverage": (manifest.get("coverage") or {}).get(ds),
                         "n_participants": meta.get("n_participants"), "n_train_participants": len(bt.train_p),
                         "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es), "n_test_query_participants": n_q,
                         "n_test_candidates": (ev.get("readout") or {}).get("n_test_candidates"), "training_access": access},
            "normalisation_access": {"input_mode": INPUT_MODE, "mode_name": C.ZS_SUFFIX[INPUT_MODE].strip("_"), "cache": meta.get("cache"),
                                     "eeg": Z_RULE, "cached_input": ACCESS_A[ds], "target": TARGET_ACCESS},
            "trainable": _trainable(enc, layout),
            "cell": {"dataset": ds, "subject_fold": sf, "content_fold": cf, "split_hash": cell.get("split_hash"),
                     "n_train": len(cell["train"]), "n_test": len(cell["test"]), "n_test_only": len(cell.get("test_only", ()))}}


# ---------------------------------------------------------------------------------------------------------- private target
def _private_cell(kids, cell, sf):
    if "train" not in cell or "test" not in cell:
        raise ValueError("the manifest's private cell lists no children (open the 0700 manifest copy, §3.3 / §6.2)")
    train = {str(k["id"]) for k in kids if k["fold"] != sf}
    test = {str(k["id"]) for k in kids if k["fold"] == sf}
    if train != set(map(str, cell["train"])) or test != set(map(str, cell["test"])):
        raise ValueError(f"private sf{sf}: the folds of data.load_private() differ from the manifest cell (train {len(train)} vs "
                         f"{len(cell['train'])}, test {len(test)} vs {len(cell['test'])})")
    return train, test


def _private_view(kids, sf):
    lo, hi = C.PRIVATE_WIN
    pool = {"input": V.PRIVATE_INPUT, "window": [lo, hi], "fs": C.FS, "subject_fold": int(sf),
            "children": [[str(k["id"]), k.get("group"), int(k["fold"]), int(len(k["y"])), int(np.asarray(k["es_mask"]).sum())] for k in kids]}
    pool_sha = _sha_json(pool)
    filters = C.filter_shas()
    return {"pool_sha256": pool_sha, "view_sha256": _sha_json({"pool": pool_sha, "lp20_sos": filters["lp20_sos"], "aa_fir_250": filters["aa_fir_250"],
                                                                "contract": C.CONTRACT}),
            "input": V.PRIVATE_INPUT, "window": [lo, hi], "n_children": len(kids)}


def adapt_private(row, manifest, dev, ck, log, donor_state, epochs=None, kids=None):
    """Train and evaluate one private_bdf cell for one arm: EEG parameters only transfer, a new class head (module docstring).
    `kids`: already loaded children (tests); by default data.load_private() through views.load_private64."""
    b = _bound(row, epochs)
    if b["dataset"] != PRIVATE:
        raise ValueError(f"adapt_private: {b['dataset']!r} is not {PRIVATE}")
    sf = int(b["subject_fold"])
    cell = V.manifest_cell(manifest, PRIVATE, sf, 0)
    kids = V.load_private64(kids)
    train, test = _private_cell(kids, cell, sf)
    enc, bt, protos = FT.fit_private_p33(b, kids, dev, ck, log, d=D, manifest=manifest, donor_state=donor_state)
    if {str(kids[i]["id"]) for i in bt.train} != train:
        raise AssertionError("adapt_private: PrivateBatcher64 trains other children than the manifest cell")
    status, selection = _selection(log, ck)
    ckpts = _checkpoints(ck, log, status)
    cal = log["objective_calibration"]
    t1 = time.time()
    ev = evaluate_private(b, enc, bt, cal, protos)
    evg = None
    if status == "evaluated":
        sd = torch.load(ck + CKPT["gainsel"], map_location=dev)
        enc.load_state_dict(sd["enc"]); protos.data.copy_(sd["protos"]); enc.eval()
        evg = evaluate_private(b, enc, bt, cal, protos)
    obj = b["spec"]["objective"]
    n_es = int(sum(len(v) for v in bt.es_idx.values()))
    return {"eval": ev, "eval_gainsel": evg, "gainsel": status, "tensor_map": enc.tensor_map, "selection_level": SELECTION_LEVEL["private"],
            "selection": selection, "checkpoints": ckpts, "bound_row": b,
            "eval_seconds": round(time.time() - t1, 1), "view": _private_view(kids, sf),
            "coverage": {"channels": _channels(enc.tensor_map, C.PRIVATE_LAYOUT), "n_children": len(kids), "n_train_children": len(train),
                         "n_test_children": len(test), "n_fit_trials": int(sum(len(v) for v in bt.fit_idx.values())), "n_es_trials": n_es},
            "normalisation_access": {"input": V.PRIVATE_INPUT, "eeg": PRIVATE_ACCESS, "labels": "training children only (fit and es blocks)"},
            "trainable": _trainable(enc, C.PRIVATE_LAYOUT, protos, obj == "NCE"),
            "class_head": ("new 2 x 32 prototypes, trained (NCE)" if obj == "NCE" else
                           "no trainable head in the CS_SINGLE recipe; the class readouts are fitted at evaluation (E_LOCAL)"),
            "cell": {"dataset": PRIVATE, "subject_fold": sf, "content_fold": 0, "split_hash": cell.get("split_hash"),
                     "n_train": len(cell["train"]), "n_test": len(cell["test"])}}
