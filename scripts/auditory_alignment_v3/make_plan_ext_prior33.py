"""E34_PUBLIC_PRIOR (ALN3.4) plan rows, module M9 (PUBLIC_PRIOR_DESIGN.md §4.1-§4.4, §6.4, §6.6 M9): append the §4.1 block of
the ALN3.3 public auditory prior (logical family ALN32_PUBLIC_AUDIO_PRIOR, contract aln33_env64_125ms_v1) to plan_ext.jsonl, or,
with --continuation GID, the continuation version of one donor group and of its downstream rows (§2.10). The pattern is
make_plan_ext_block7.py: a guard on the LIVE plan_ext.jsonl (line count and sha256 prefix), assertions, tmp + os.replace.

Usage (repository root, eeg2025 interpreter):
  python -B private/auditory_alignment_v3/make_plan_ext_prior33.py [--dry-run] [--manifest PATH] [--manifest-sha SHA]
  python -B private/auditory_alignment_v3/make_plan_ext_prior33.py --apply --manifest PATH --manifest-sha SHA
  python -B private/auditory_alignment_v3/make_plan_ext_prior33.py [--apply] --continuation GID [--manifest PATH --manifest-sha SHA]
The default is a dry run: every row is built and checked, counts are printed, nothing is written. --apply appends.

Guard. GUARD_LINES / GUARD_SHA16 below must describe the live file exactly (3,325 lines, 85b44d8d... on 2026-10-16/17). When
another lane has appended first, re-base them here after checking what it appended; never skip the guard (it has no override).
The append (--apply) holds an exclusive flock on plan_ext.jsonl.lock next to the file (created 0600 on first use and never
removed; the holder's host, pid and time are written into it), re-reads the file under the lock (it must still be the guarded
one, same inode), writes tmp, keeps the previous file as plan_ext.jsonl.before_prior33_<date>, re-checks, os.replace, and then
checks that the new file is exactly what was written, that the old file did not change size meanwhile and, POST_CHECK_S (2 s)
later, that the file still begins with the written bytes. The lock serialises only the appenders that take it (this script;
the older make_plan_ext*.py block scripts do not); against those the remaining window is the instant between the last re-read
and the rename, and the post-replace checks report (exit 1) a concurrent write they could not prevent.
Queue indices of existing rows never change (index = 100000 + position).

Primary block (§4.1; counts asserted against DESIGN_COUNTS, the §4.1 table): core 540 (8 donor groups, 32 bridges, 300 targets,
200 mode-A zero-shot rows), access <= 210 (mode B for FAU; modes C / C_partial only where manifest.mode_c supports them), panel 120
(private_bdf, seeds 3407 / 3413), rich 126, CSX 158; at most 1,154 rows. Dependencies are resolved to ids inside the block (the
rich and CSX groups depend on the core group whose H* they adopt, the access rows on the core group and its core bridge of the
same slot); deps.check_plan runs on the existing plan plus the new rows; ids are unique and collide with no existing row; every
target / zero-shot row's spec.split_hash is the split_hash of the manifest cell (dataset, subject_fold, content_fold), and every
row carries the manifest's target_contract and sha256. A primary block is refused when the plan already holds any E34 row (the
contract: an existing execution is reused, never re-scheduled).

Continuation (--continuation GID, §2.10): GID is a DONOR (core or panel) group whose complete record has
ceiling_reached_while_improving true and whose retained stable states (select.retained_states) exist; every rich / CSX group
continued with it (spec.horizon_from = GID) that already has a complete record must satisfy the same two conditions (its
continuation resumes from its own retained states, and would otherwise wait for ever); one still without a record is continued
(M5 retains its states when it adopts a ceiling horizon). Built: the group again with
spec.continuation_of = GID (an upstream: it resumes from those states) and its own compute limit (+30: 60 -> 90 -> 120), every
bridge / target / zero-shot row of GID, and every rich / CSX group whose spec.horizon_from is GID (again with continuation_of = that
group, horizon_from = the new core group and the same limit) with its downstream rows. Every row of the version carries
spec.version = "continuation_<k>" (k = 1 + the depth of GID's continuation_of chain); bridge, target and zero-shot rows carry
spec.continuation_of = the id of the row they continue (a label; deps.py and prior33.analysis read it as such). S rows are never
re-registered (they have no donor group; analysis pairs the continuation arms with the primary S rows). Every continuation row
equals the row it continues except for spec.version, spec.continuation_of, spec.donor_group / spec.bridge (slot rows) and
spec.budget.continuation / spec.horizon_from (groups), `registered` and the dependencies (checked; so split_hash, target_contract
and the manifest sha256 are the primary block's); with --manifest the rows are also checked against the manifest.

Rows (plan_ext.jsonl): dataset, subject_fold, content_fold, seed, seed_scope, experiment_id, family_id, job_kind, spec, registered,
logical_dependencies, status = "registered_extension". Spec: design §4.3, as select.py / deps.py / prior33.analysis read it.
Interpretations (each is listed as a deviation in the M9 summary):
  - id = "ALN3X_" + sha256(json.dumps({"family": family_id, "dataset", "subject_fold", "content_fold", "seed", "spec"},
    sort_keys=True))[:16]; `registered` is not part of the id, so a dry run prints the ids an --apply writes.
  - donor-group and bridge rows have subject_fold = content_fold = None (one group serves every cell of its target, §3.1); target
    and zero-shot rows carry the manifest cell's folds (Federici and private content_fold 0, as the cells and the ALN3 rows).
  - row seed = donor_seed (donor, bridge and zero-shot rows) or target_seed (target rows, §4.3); sampler_seed = donor_seed;
    target_seed None on donor / bridge / zero-shot rows; from-scratch (S) rows have donor_seed = sampler_seed = None.
  - spec.target "current_class" on private_bdf target rows only (the donor groups and bridges of the private donor set are
    trained on envelopes); spec.target_contract = manifest.target_contract on every row.
  - S rows: variant = member = "S" (select.SCRATCH), init "random", donor_group None. Slot rows: variant = member = the slot.
  - zero-shot: variant = the full §2.13 name (contract.ZS_MODE_NAME), mode = A | B | C | C_partial, job_kind "eval" (also on the
    row), view "all_participants_trainp_empty_v1". Bridges: job_kind "fit"; donor groups and targets "train".
  - donor groups: donor_set = the manifest strata of donor_sets[target][core | rich | csx] (panel: core), stratum_weights =
    {stratum: weight}; lambda_rule only on groups with J1 / J025 and control only on groups with XM (core and panel); budget
    {epoch_equivalents 30, anchors_per_ep_eq and steps0 from manifest.budget, continuation "..._limit60_v1"}; optimizer {AdamW,
    lr 1e-3, weight_decay 1e-4, grad_clip 5}.
  - logical_dependencies: the symbolic tokens "frozen_manifest" and (rich) "rich_cache" (skipped by deps.upstreams), then the
    upstream ids.
  - access rows (design inconsistency): §4.1 gives their dependencies as "group + bridge", i.e. the core group and the core
    bridge of the slot, while §6.4 step 4 says "every dependency is inside the block, or is the block's own core group", which
    leaves the bridge out. §4.1 is followed: the upstreams of an access row are exactly its spec.donor_group (a core DONOR group)
    and its spec.bridge (that group's core bridge row of the same slot); check_rows accepts nothing else from outside the block.
  - registered = "E34_PUBLIC_PRIOR execution record <path> sha256 <sha>" (+ "; continuation_<k> of <gid> ..."); --apply requires
    the record (design §1), the manifest sha256 listed in it, prior33.analysis.frozen_check(new rows) ok, and the sha256 of every
    training code file (the files of the five prior33 code groups, registry_patch.group_files, and core.V2_DEPS) listed in it. A
    dry run without the record uses a placeholder and reports what --apply would refuse.
Reads plan files, the manifest (views.open_manifest: sha256, schema, contract, constants) and, for --continuation, one donor-group
record (select.load_record) and the existence of its stable states, and those of the rich / CSX groups continued with it; opens
no EEG or private data. API for tests: main(argv, plan_ext=, guard=, out=, record=, plan_rows=, code_files=); LOCK_WAIT_S and
POST_CHECK_S (module constants).
"""
from __future__ import annotations

import argparse
import copy
import datetime
import errno
import fcntl
import hashlib
import json
import os
import re
import shutil
import socket
import sys
import time
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from auditory_alignment_v3 import core  # noqa: E402
from auditory_alignment_v3.prior33 import contract as C  # noqa: E402
from auditory_alignment_v3.prior33 import deps as D  # noqa: E402
from auditory_alignment_v3.prior33 import registry_patch as RP  # noqa: E402
from auditory_alignment_v3.prior33 import select as S  # noqa: E402

PLAN_EXT = os.path.join(core.OUT, "plan_ext.jsonl")
GUARD_LINES, GUARD_SHA16 = 3325, "85b44d8d7a654f58"   # the live plan_ext.jsonl (re-base when another lane appends; never skip)
MANIFEST = os.path.join(core.OUT, "aln34", "prior33", "manifest.json")   # §6.2: the 0444 copy whose sha256 enters every row
EXEC_RECORD = os.path.join(core.OUT, "aln34", "E34_PUBLIC_PRIOR_EXECUTION_RECORD.md")
LOGICAL_FAMILY, CARD = "ALN32_PUBLIC_AUDIO_PRIOR", "E34_PUBLIC_PRIOR"
TARGETS = ("fau", "dtu", "federici", "private_bdf")
PRIVATE = "private_bdf"
PUBLIC = tuple(C.ZS_COHORTS["A"])                           # fau, dtu, federici
OBJECTIVES = ("NCE", "CS_SINGLE")
BREADTH_SEED, PANEL_SEEDS = 3401, (3407, 3413)
CORE_SLOTS = ("AP", "XP", S.JOINT, "XM")
ACCESS_SLOTS = ("AP", "XP", S.JOINT)
GROUP_SLOTS = {S.DONOR: CORE_SLOTS, S.RICH_DONOR: ("APR",), S.CSX_DONOR: ("APC", "XPC")}
TARGET_VARIANTS = (S.SCRATCH,) + CORE_SLOTS
CSX_TARGETS, CSX_ZS = ("dtu", "federici", PRIVATE), ("dtu", "federici")
ACCESS_MODES = (("fau", "B"), ("fau", "C"), ("dtu", "C"), ("federici", "C_partial"))
CELL_GRID = {"fau": [(f, c) for f in range(5) for c in (0, 1)], "dtu": [(f, c) for f in range(5) for c in (0, 1)],
             "federici": [(f, 0) for f in range(5)], PRIVATE: [(f, 0) for f in range(5)]}     # §3.3: 30 cells
DESIGN_COUNTS = {  # §4.1 rows per (block, family) of the primary block; access: ACCESS_COUNTS, by manifest support
    ("core", S.DONOR): 8, ("core", S.BRIDGE): 32, ("core", S.TARGET): 300, ("core", S.ZEROSHOT): 200,
    ("panel", S.DONOR): 4, ("panel", S.BRIDGE): 16, ("panel", S.TARGET): 100,
    ("rich", S.RICH_DONOR): 8, ("rich", S.BRIDGE): 8, ("rich", S.TARGET): 60, ("rich", S.ZEROSHOT): 50,
    ("csx", S.CSX_DONOR): 6, ("csx", S.BRIDGE): 12, ("csx", S.TARGET): 80, ("csx", S.ZEROSHOT): 60}
ACCESS_COUNTS = {("fau", "B"): 60, ("fau", "C"): 60, ("dtu", "C"): 60, ("federici", "C_partial"): 30}   # 10/10/10/5 cells x 3 x 2
BLOCK_TOTALS = {"core": 540, "panel": 120, "rich": 126, "csx": 158}   # access <= 210; total <= 1,154
CONT_LIMIT_STEP = 30                                                 # §2.10: 60 -> 90 (the continuation's compute limit)
BUDGET_RULE = "group_wsd_any_last3_ext10_limit{}_v1"
READOUT_SEEDS = (f"runner-defined: target_seed + {{{', '.join(map(str, C.READOUT_SEED_OFFSETS))}}}; bridge rows {C.BRIDGE_SEED}; "
                 f"τ pools {C.TAU_POOL_SEED}")
BATCH = {"segments": 32, "anchors": C.N_ANCHORS, "views": 2}
OPTIMIZER = {"name": "AdamW", "lr": 1e-3, "weight_decay": 1e-4, "grad_clip": 5.0}
DONOR_SELECTION = {"primary": "donor_dev_ce_calibrated_v1", "sensitivity": "donor_dev_gain_v1"}
TARGET_SELECTION = {"primary": "min_es_loss", "sensitivity": "min_es_loss_minus_mismatch"}
RICH_TARGETS = {"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}
LOSS_WEIGHTS = [1.0, 0.5, 0.5]
PRIVATE_INPUT = "p64_lp20_z64_v1"
TOKENS = {"manifest": "frozen_manifest", "rich": "rich_cache"}
HEX = re.compile(r"(?<![0-9a-f])[0-9a-f]{16,64}(?![0-9a-f])")
SHORT = {f: f[len(S.PREFIX):] for f in S.FAMILIES}
LOCK_SUFFIX, LOCK_WAIT_S = ".lock", 10.0   # <plan_ext>.lock: the appenders' flock (module docstring); seconds to wait for it
POST_CHECK_S = 2.0                         # seconds after the rename before the file is read back once more (append_rows)
# spec fields a continuation row may change against the row it continues (everything else must be equal; module docstring)
CONT_FREE = {"donor_group": ("version", "continuation_of", "horizon_from", "budget"), "bridge": ("version", "continuation_of", "donor_group"),
             "target": ("version", "continuation_of", "donor_group"), "zero_shot": ("version", "continuation_of", "donor_group", "bridge")}
ROW_SAME = ("dataset", "subject_fold", "content_fold", "seed", "seed_scope", "family_id", "job_kind", "status")
_ABSENT = object()


class PlanError(RuntimeError):
    """The plan block cannot be built or appended (guard, manifest, record, count or consistency failure)."""


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _rel(p):
    try:
        return os.path.relpath(p, REPO) if os.path.commonpath([os.path.abspath(p), REPO]) == REPO else p
    except ValueError:
        return p


# ------------------------------------------------------------------------------------------------------------ guard
def read_guarded(path, guard):
    """(raw bytes, rows) of plan_ext.jsonl when its line count and sha256 prefix are `guard` = (lines, sha prefix >= 16 hex)."""
    lines, sha = guard
    if not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{16,64}", sha)) or isinstance(lines, bool) or not isinstance(lines, int):
        raise PlanError(f"guard {guard!r}: a line count and a sha256 prefix of >= 16 hex digits are required")
    with open(path, "rb") as f:
        raw = f.read()
    got_lines, got_sha = len(raw.decode("utf-8").splitlines()), _sha(raw)
    if got_lines != lines or not got_sha.startswith(sha) or (raw and not raw.endswith(b"\n")):
        raise PlanError(f"live guard: {_rel(path)} has {got_lines} lines and sha256 {got_sha[:16]}..., the guard expects {lines} "
                        f"lines and {sha[:16]}...: another lane has appended (or the file changed). Check what was appended, then "
                        f"re-base GUARD_LINES / GUARD_SHA16 in {_rel(os.path.abspath(__file__))}; never skip the guard")
    try:
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    except ValueError as ex:
        raise PlanError(f"{_rel(path)}: a line is not JSON ({ex})") from None
    return raw, rows


# ------------------------------------------------------------------------------------------------------------ manifest
def open_manifest(path, sha):
    """The frozen manifest through views.open_manifest (sha256, schema, contract, constants); sha None = computed, unverified."""
    from auditory_alignment_v3.prior33 import views  # torch; only here
    if not os.path.exists(path):
        raise PlanError(f"full manifest {_rel(path)} not found (C6 writes it to aln34/prior33/, §6.2); pass --manifest FULL_PATH")
    with open(path, "rb") as f:
        got = _sha(f.read())
    try:
        man = views.open_manifest(path, sha or got)
        if man.get("copy") == "public_redacted":
            raise ValueError("registration requires the private_full manifest; the public redacted copy omits private splits")
        if "rich" not in man and man.get("rich_supplement"):
            rich_path = os.path.join(os.path.dirname(path), "manifest_rich.json")
            if not os.path.exists(rich_path):
                raise ValueError(f"rich registration requires the completed supplement: {rich_path}")
            with open(rich_path, "rb") as f:
                rich_sha = _sha(f.read())
            man = views.open_with_rich(man, rich_sha, rich_path)
    except ValueError as ex:
        raise PlanError(str(ex)) from None
    return man, man.sha256, sha is not None


def _need(cond, msg):
    if not cond:
        raise PlanError(f"manifest: {msg}")


def manifest_context(man, sha):
    """Validated manifest facts the rows use: cells, donor sets, budget, target contract, the supported access modes."""
    _need(man.get("copy") != "public_redacted", "registration requires the full private copy, not public_redacted")
    rich_sha = getattr(man, "rich_sha256", None)
    _need(not man.get("rich_supplement") or rich_sha, "rich supplement must be opened and sha256-bound before registration")
    tc = man.get("target_contract")
    _need(isinstance(tc, str) and tc, "target_contract is missing")
    cells, seen = {t: [] for t in TARGETS}, set()
    for c in man.get("cells") or []:
        ds = c.get("dataset")
        _need(ds in cells, f"cell of unknown dataset {ds!r}")
        _need(isinstance(c.get("split_hash"), str) and c["split_hash"], f"{ds} cell without split_hash")
        _need(c["split_hash"] not in seen, f"split_hash {c['split_hash'][:16]} occurs twice")
        seen.add(c["split_hash"])
        cells[ds].append({"dataset": ds, "subject_fold": c.get("subject_fold"), "content_fold": c.get("content_fold"),
                          "split_hash": c["split_hash"]})
    for t in TARGETS:
        cells[t].sort(key=lambda c: (c["subject_fold"], c["content_fold"]))
        got = [(c["subject_fold"], c["content_fold"]) for c in cells[t]]
        _need(got == CELL_GRID[t], f"{t} cells {got} differ from the §3.3 grid {CELL_GRID[t]}")
    dsets = man.get("donor_sets") or {}
    sets = {}
    for t in TARGETS:
        blocks = dsets.get(t) or {}
        want = {"core", "rich"} | ({"csx"} if t in CSX_TARGETS else set())
        _need(set(blocks) == want, f"donor_sets[{t}] has blocks {sorted(blocks)}, expected {sorted(want)} (§3.1, §2.16)")
        for b, v in blocks.items():
            st, w = list(v.get("strata") or []), list(v.get("weights") or [])
            _need(st and len(st) == len(w) and len(set(st)) == len(st), f"donor_sets[{t}][{b}]: strata / weights malformed")
            _need(all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 for x in w) and abs(sum(w) - 1) < 1e-6,
                  f"donor_sets[{t}][{b}]: weights {w} are not positive shares")
            _need(t not in st and PRIVATE not in st and (t != "fau" or "fau_cs" not in st), f"donor_sets[{t}][{b}] holds the target "
                  f"cohort or private_bdf: {st} (leave-target-out, §3.1)")
            _need("sparrkulee" in st and set(st) <= {"sparrkulee", "fau", "dtu", "federici", "fau_cs"},
                  f"donor_sets[{t}][{b}]: strata {st}")
            _need(("fau_cs" in st) == (b == "csx"), f"donor_sets[{t}][{b}]: fau_cs belongs to the CSX block only (§2.16)")
        _need(blocks["rich"]["strata"] == blocks["core"]["strata"], f"donor_sets[{t}]: the rich strata differ from the core's (§2.15)")
        if "csx" in blocks:
            _need([s for s in blocks["csx"]["strata"] if s != "fau_cs"] == blocks["core"]["strata"],
                  f"donor_sets[{t}]: the CSX strata are not the core strata plus fau_cs")
        sets[t] = {b: {"strata": list(v["strata"]), "weights": [float(x) for x in v["weights"]]} for b, v in blocks.items()}
    bud = man.get("budget") or {}
    for k in ("S0", "anchors_per_ep_eq"):
        _need(isinstance(bud.get(k), int) and not isinstance(bud.get(k), bool) and bud[k] > 0, f"budget.{k} = {bud.get(k)!r}")
    _need(bud.get("ep_eq0", 30) == 30 and bud.get("ep_eq_limit", 60) == 60, "budget ep_eq0 / ep_eq_limit are not 30 / 60 (§2.10)")
    lw = (man.get("rich") or {}).get("loss_weights")
    _need(lw is None or [float(x) for x in lw] == LOSS_WEIGHTS, f"rich.loss_weights {lw} differ from {LOSS_WEIGHTS} (§2.15)")
    caches = {c: set((v or {}).get("caches") or {}) for c, v in (man.get("cohorts") or {}).items()}
    access = []
    for cohort, mode in ACCESS_MODES:
        if mode == "B":
            _need("B" in caches.get("fau", set()), "cohorts.fau.caches lacks the mode-B cache (§2.13: always registered)")
            access.append((cohort, mode))
            continue
        e = (man.get("mode_c") or {}).get(cohort)
        _need(isinstance(e, dict), f"mode_c[{cohort}] is missing (C5/C6 record mode-C support per cohort)")
        if e.get("supported") is True:
            _need(e.get("mode") in (None, mode), f"mode_c[{cohort}].mode {e.get('mode')!r}, expected {mode!r} (contract.ZS_COHORTS)")
            _need(mode in caches.get(cohort, set()), f"mode_c[{cohort}] is supported but cohorts.{cohort}.caches lacks {mode!r}")
            access.append((cohort, mode))
    return {"sha": sha, "rich_sha": rich_sha, "target_contract": tc, "cells": cells, "donor_sets": sets,
            "budget": {"S0": bud["S0"], "anchors_per_ep_eq": bud["anchors_per_ep_eq"]}, "access": access}


# ------------------------------------------------------------------------------------------------------------ rows
def row_id(family, dataset, subject_fold, content_fold, seed, spec):
    """§4.3: ALN3X_ + sha256(json({family, dataset, subject_fold, content_fold, seed, spec}, sort_keys))[:16]."""
    body = {"family": family, "dataset": dataset, "subject_fold": subject_fold, "content_fold": content_fold, "seed": seed,
            "spec": spec}
    return "ALN3X_" + _sha(json.dumps(body, sort_keys=True).encode())[:16]


def make_row(family, dataset, subject_fold, content_fold, seed, spec, deps, registered, job_kind):
    return {"dataset": dataset, "subject_fold": subject_fold, "content_fold": content_fold, "seed": seed,
            "seed_scope": spec["seed_scope"], "experiment_id": row_id(family, dataset, subject_fold, content_fold, seed, spec),
            "family_id": family, "job_kind": job_kind, "spec": spec, "registered": registered, "logical_dependencies": list(deps),
            "status": "registered_extension"}


def _common(ctx, block, seed, objective, target, donor_seed, target_seed):
    return {"logical_family": LOGICAL_FAMILY, "card": CARD, "execution_contract": C.CONTRACT, "manifest_sha256": ctx["sha"],
            **({"manifest_rich_sha256": ctx["rich_sha"]} if block == "rich" and ctx.get("rich_sha") else {}),
            "block": block, "queue_tier": D.BLOCK_TIER[block], "seed_scope": "breadth" if seed == BREADTH_SEED else "panel",
            "donor_seed": donor_seed, "sampler_seed": donor_seed, "target_seed": target_seed, "readout_seeds": READOUT_SEEDS,
            "architecture": "lag_local_tokens", "channel_map": "name_indexed_signed_v1", "window": "full", "input_samples": [0, C.L_IN],
            "fs": C.FS, "projection_dim": 32, "objective": objective, "target": target, "target_contract": ctx["target_contract"]}


class Builder:
    """Rows of one primary block (§4.1, §4.3); every row gets the same `registered` text."""

    def __init__(self, ctx, registered):
        self.ctx, self.reg, self.rows = ctx, registered, []

    def _add(self, *a):
        r = make_row(*a)
        self.rows.append(r)
        return r

    def group(self, fam, block, target, objective, seed, horizon=None):
        dblock = {S.RICH_DONOR: "rich", S.CSX_DONOR: "csx"}.get(fam, "core")
        dset = self.ctx["donor_sets"][target][dblock]
        members = S.GROUP_MEMBERS[fam]
        spec = _common(self.ctx, block, seed, objective, "envelope", seed, None)
        spec.update(stage="donor_group", members=list(members), donor_set=list(dset["strata"]),
                    stratum_weights=dict(zip(dset["strata"], dset["weights"])), batch=dict(BATCH),
                    budget={"epoch_equivalents": 30, "anchors_per_ep_eq": self.ctx["budget"]["anchors_per_ep_eq"],
                            "steps0": self.ctx["budget"]["S0"], "continuation": BUDGET_RULE.format(S.DEFAULT_LIMIT_EP_EQ)},
                    optimizer=dict(OPTIMIZER), temperature=C.TAU, bandwidth_multiplier=1.0, selection=dict(DONOR_SELECTION),
                    montage_augmentation="subset3_p05_v1")
        if all(m in members for m in S.JOINT_CANDIDATES):
            spec["lambda_rule"] = S.LAMBDA_RULE
        if "XM" in members:
            spec["control"] = "xm_task_state_matched_derangement_v1"
        deps = [TOKENS["manifest"]]
        if fam == S.RICH_DONOR:
            spec.update(rich_targets=dict(RICH_TARGETS), loss_weights=list(LOSS_WEIGHTS), horizon_from=horizon["experiment_id"])
            deps += [TOKENS["rich"], horizon["experiment_id"]]
        elif fam == S.CSX_DONOR:
            spec.update(extra_strata=["fau_cs"], horizon_from=horizon["experiment_id"])
            deps.append(horizon["experiment_id"])
        return self._add(fam, target, None, None, seed, spec, deps, self.reg, "train")

    def bridge(self, g, slot):
        gs = g["spec"]
        spec = _common(self.ctx, gs["block"], g["seed"], gs["objective"], "envelope", g["seed"], None)
        spec.update(stage="bridge", donor_group=g["experiment_id"], member=slot, bridge="ridge_u_to_stdenv8_v1",
                    fit_rows="donorfit_2000seg_seed20261016", alpha="logspace(-4,8,13)|bridge_cal_corr",
                    temperature="bridge_cal_ce_by_poolsize_v1", sensitivity="bridge_cal_fit_2fold_tau_crossfit_v1", artefact_probe=True)
        return self._add(S.BRIDGE, g["dataset"], None, None, g["seed"], spec, [g["experiment_id"]], self.reg, "fit")

    def target(self, block, cell, objective, seed, slot, g=None):
        private = cell["dataset"] == PRIVATE
        spec = _common(self.ctx, block, seed, objective, "current_class" if private else "envelope", None if g is None else g["seed"], seed)
        spec.update(stage="target", variant=slot, init="random" if g is None else "donor",
                    donor_group=None if g is None else g["experiment_id"], member=slot, recipe="a_local_recipe_on_aln33_v2", epochs=200,
                    nce="contract_lse_mask2s_v1", selection=dict(TARGET_SELECTION), split_hash=cell["split_hash"])
        if private:
            spec.update(training_task="current_class", private_input=PRIVATE_INPUT)
        return self._add(S.TARGET, cell["dataset"], cell["subject_fold"], cell["content_fold"], seed, spec,
                         [] if g is None else [g["experiment_id"]], self.reg, "train")

    def zero_shot(self, block, cell, g, b, slot, mode):
        spec = _common(self.ctx, block, g["seed"], g["spec"]["objective"], "envelope", g["seed"], None)
        spec.update(stage="zero_shot", variant=C.ZS_MODE_NAME[mode], member=slot, donor_group=g["experiment_id"],
                    bridge=b["experiment_id"], mode=mode, view="all_participants_trainp_empty_v1", split_hash=cell["split_hash"],
                    job_kind="eval")
        return self._add(S.ZEROSHOT, cell["dataset"], cell["subject_fold"], cell["content_fold"], g["seed"], spec,
                         [g["experiment_id"], b["experiment_id"]], self.reg, "eval")


def build_primary(ctx, registered):
    """The §4.1 block, upstreams first: core, access, panel, rich, CSX."""
    B, cells = Builder(ctx, registered), ctx["cells"]
    G = {(t, o): B.group(S.DONOR, "core", t, o, BREADTH_SEED) for t in TARGETS for o in OBJECTIVES}
    BR = {(t, o, s): B.bridge(G[t, o], s) for t in TARGETS for o in OBJECTIVES for s in CORE_SLOTS}
    for t in TARGETS:
        for c in cells[t]:
            for o in OBJECTIVES:
                for v in TARGET_VARIANTS:
                    B.target("core", c, o, BREADTH_SEED, v, None if v == S.SCRATCH else G[t, o])
    for t in PUBLIC:
        for c in cells[t]:
            for o in OBJECTIVES:
                for s in CORE_SLOTS:
                    B.zero_shot("core", c, G[t, o], BR[t, o, s], s, "A")
    for t, mode in ctx["access"]:                                    # access (tier 2): AP, XP, J* of the core groups
        for c in cells[t]:
            for o in OBJECTIVES:
                for s in ACCESS_SLOTS:
                    B.zero_shot("access", c, G[t, o], BR[t, o, s], s, mode)
    GP = {(o, sd): B.group(S.DONOR, "panel", PRIVATE, o, sd) for o in OBJECTIVES for sd in PANEL_SEEDS}   # panel (tier 3)
    BP = {(o, sd, s): B.bridge(GP[o, sd], s) for o in OBJECTIVES for sd in PANEL_SEEDS for s in CORE_SLOTS}
    assert len(BP) == 16
    for c in cells[PRIVATE]:
        for o in OBJECTIVES:
            for sd in PANEL_SEEDS:
                for v in TARGET_VARIANTS:
                    B.target("panel", c, o, sd, v, None if v == S.SCRATCH else GP[o, sd])
    GR = {(t, o): B.group(S.RICH_DONOR, "rich", t, o, BREADTH_SEED, horizon=G[t, o]) for t in TARGETS for o in OBJECTIVES}   # rich
    BRR = {k: B.bridge(g, "APR") for k, g in GR.items()}
    for t in TARGETS:
        for c in cells[t]:
            for o in OBJECTIVES:
                B.target("rich", c, o, BREADTH_SEED, "APR", GR[t, o])
    for t in PUBLIC:
        for c in cells[t]:
            for o in OBJECTIVES:
                B.zero_shot("rich", c, GR[t, o], BRR[t, o], "APR", "A")
    GX = {(t, o): B.group(S.CSX_DONOR, "csx", t, o, BREADTH_SEED, horizon=G[t, o]) for t in CSX_TARGETS for o in OBJECTIVES}  # CSX
    BX = {(t, o, s): B.bridge(GX[t, o], s) for t in CSX_TARGETS for o in OBJECTIVES for s in GROUP_SLOTS[S.CSX_DONOR]}
    for t in CSX_TARGETS:
        for c in cells[t]:
            for o in OBJECTIVES:
                for s in GROUP_SLOTS[S.CSX_DONOR]:
                    B.target("csx", c, o, BREADTH_SEED, s, GX[t, o])
    for t in CSX_ZS:
        for c in cells[t]:
            for o in OBJECTIVES:
                for s in GROUP_SLOTS[S.CSX_DONOR]:
                    B.zero_shot("csx", c, GX[t, o], BX[t, o, s], s, "A")
    return B.rows


def expected_counts(ctx):
    """{(block, family): rows} of the primary block: DESIGN_COUNTS plus the supported access modes."""
    exp = dict(DESIGN_COUNTS)
    n = sum(ACCESS_COUNTS[k] for k in ctx["access"])
    if n:
        exp[("access", S.ZEROSHOT)] = n
    return exp


# ------------------------------------------------------------------------------------------------------------ continuation
def _chain_depth(gid, by):
    """Number of continuation_of links behind a donor group (0 = primary)."""
    seen, d, g = set(), 0, by[gid]
    while (g.get("spec") or {}).get("continuation_of"):
        src = g["spec"]["continuation_of"]
        if src in seen or src not in by:
            raise PlanError(f"continuation chain of {gid} is broken or cyclic at {src}")
        seen.add(src)
        d, g = d + 1, by[src]
    return d


def _rewrite_limit(rule, limit):
    if not re.search(r"limit\d+", rule or ""):
        raise PlanError(f"budget.continuation {rule!r} names no compute limit")
    return re.sub(r"limit\d+", f"limit{limit}", rule, count=1)


def _again(row, spec, deps, registered):
    return make_row(row["family_id"], row["dataset"], row["subject_fold"], row["content_fold"], row["seed"], spec, deps, registered,
                    row["job_kind"])


def _continuable(out, row, what):
    """The complete record of donor group `row`, after checking that a continuation can resume from it (§2.10): the record sets
    ceiling_reached_while_improving true and every retained stable state exists. None while the group has no record."""
    eid = row["experiment_id"]
    try:
        rec = S.load_record(out, eid)
    except S.SelectionError as ex:
        raise PlanError(f"--continuation: {what} {eid}: {ex}") from None
    if rec is None:
        return None
    if rec.get("ceiling_reached_while_improving") is not True:
        raise PlanError(f"--continuation: {what} {eid}: its complete record does not set ceiling_reached_while_improving: true "
                        f"(§2.10, §6.4); a continuation resumes from the stable states kept at the ceiling and could never start")
    miss = [p for p in S.retained_states(out, row) if not os.path.exists(p)]
    if miss:
        raise PlanError(f"--continuation: {what} {eid}: {len(miss)} retained stable state(s) missing, e.g. {_rel(miss[0])} (the "
                        f"continuation resumes from them; they are never offloaded)")
    return rec


def build_continuation(gid, rows, out, registered):
    """The continuation version of donor group `gid` and its downstream rows (module docstring). Rows: the existing plan.
    -> (new rows, version label, notes)."""
    by = D.index(rows)
    G = by.get(gid)
    if G is None or G.get("family_id") != S.DONOR:
        fam = None if G is None else G.get("family_id")
        raise PlanError(f"--continuation {gid}: not a {S.DONOR} plan row ({fam}); rich and CSX groups follow the core group whose "
                        f"horizon they adopt and are continued with it (§2.10)")
    if _continuable(out, G, "the group") is None:
        raise PlanError(f"--continuation {gid}: no complete record {_rel(S.record_path(out, gid))}")
    dup = [r["experiment_id"] for r in rows if r.get("family_id") == S.DONOR and (r.get("spec") or {}).get("continuation_of") == gid]
    if dup:
        raise PlanError(f"--continuation {gid}: a continuation of this group is already registered ({dup[0]})")
    followers = [r for r in rows if r.get("family_id") in (S.RICH_DONOR, S.CSX_DONOR) and (r.get("spec") or {}).get("horizon_from") == gid]
    notes = []
    for R in followers:     # rich / CSX groups continued with GID: the same two conditions once they have a record
        if _continuable(out, R, f"the {SHORT[R['family_id']]} group continued with {gid},") is None:
            notes.append(f"{SHORT[R['family_id']]} group {R['experiment_id']} has no record yet: its continuation waits for it (and "
                         f"for its retained stable states)")
    label = f"continuation_{_chain_depth(gid, by) + 1}"
    limit = S.compute_limit(G) + CONT_LIMIT_STEP
    note = f"{registered}; {label} of {gid} (PUBLIC_PRIOR_DESIGN.md §2.10)"
    new = []

    def group_again(src, horizon=None):
        spec = copy.deepcopy(src["spec"])
        spec["budget"]["continuation"] = _rewrite_limit(spec["budget"].get("continuation"), limit)
        spec.update(continuation_of=src["experiment_id"], version=label)
        deps = [d for d in src.get("logical_dependencies") or [] if not D.EID.match(d)]
        if horizon is not None:
            spec["horizon_from"] = horizon["experiment_id"]
            deps.append(horizon["experiment_id"])
        r = _again(src, spec, deps + [src["experiment_id"]], note)
        new.append(r)
        return r

    def downstream(src_gid, ng):
        mine = [r for r in rows if r.get("family_id") in S.FAMILIES and S.stage_of(r) != "donor_group"
                and (r.get("spec") or {}).get("donor_group") == src_gid]
        bmap = {}
        for stage in ("bridge", "target", "zero_shot"):
            for r in (x for x in mine if S.stage_of(x) == stage):
                spec = copy.deepcopy(r["spec"])
                spec.update(donor_group=ng["experiment_id"], continuation_of=r["experiment_id"], version=label)
                deps = [ng["experiment_id"]]
                if stage == "zero_shot":
                    if spec.get("bridge") not in bmap:
                        raise PlanError(f"{r['experiment_id']}: spec.bridge {spec.get('bridge')} is not a bridge of {src_gid}")
                    spec["bridge"] = bmap[spec["bridge"]]
                    deps.append(spec["bridge"])
                x = _again(r, spec, deps, note)
                new.append(x)
                if stage == "bridge":
                    bmap[r["experiment_id"]] = x["experiment_id"]
        return len(mine)

    Cg = group_again(G)
    downstream(gid, Cg)
    for R in followers:
        if any(r.get("family_id") == R["family_id"] and (r.get("spec") or {}).get("continuation_of") == R["experiment_id"] for r in rows):
            raise PlanError(f"{R['experiment_id']}: a continuation of this {SHORT[R['family_id']]} group is already registered")
        Rn = group_again(R, horizon=Cg)
        downstream(R["experiment_id"], Rn)
    return new, label, notes


# ------------------------------------------------------------------------------------------------------------ checks
def _upstream_ok(r, u, by_new, by_all, mode):
    """Is upstream u of new row r inside its block (§6.4 step 4, with the access rows as §4.1 gives them)?"""
    s, blk = r["spec"], r["spec"]["block"]
    nu = by_new.get(u)
    if nu is not None and nu["spec"]["block"] == blk:
        return True
    if S.stage_of(r) == "donor_group" and u == s.get("horizon_from"):     # rich / CSX: the core group whose H* they adopt
        h = by_new.get(u) or by_all.get(u)
        return h is not None and h["family_id"] == S.DONOR and h["spec"]["block"] == "core"
    if blk == "access":   # §4.1 "group + bridge": exactly the row's core group and that group's core bridge of the same slot
        if nu is None or nu["spec"]["block"] != "core":
            return False
        if u == s.get("donor_group"):
            return nu["family_id"] == S.DONOR
        return u == s.get("bridge") and nu["family_id"] == S.BRIDGE and nu["spec"].get("donor_group") == s.get("donor_group") \
            and nu["spec"].get("member") == s.get("member")
    if mode == "continuation" and S.stage_of(r) == "donor_group" and u == s.get("continuation_of"):
        src = by_all.get(u)
        return src is not None and src["family_id"] == r["family_id"] and src["spec"]["block"] == blk
    return False


def _manifest_problems(new, ctx):
    """The new rows against the manifest facts (manifest_context): spec.manifest_sha256 and spec.target_contract on every row;
    spec.split_hash of every target / zero-shot row = the split_hash of the manifest cell (dataset, subject_fold, content_fold),
    and no split_hash on donor-group or bridge rows."""
    probs = []
    cells = {(c["dataset"], c["subject_fold"], c["content_fold"]): c["split_hash"] for cs in ctx["cells"].values() for c in cs}
    for r in new:
        e, s = r.get("experiment_id"), r.get("spec") or {}
        if s.get("manifest_sha256") != ctx["sha"]:
            probs.append(f"{e}: spec.manifest_sha256 {str(s.get('manifest_sha256'))[:16]} is not the manifest's {ctx['sha'][:16]}")
        if s.get("block") == "rich" and ctx.get("rich_sha") and s.get("manifest_rich_sha256") != ctx["rich_sha"]:
            probs.append(f"{e}: spec.manifest_rich_sha256 is not the rich supplement's sha256")
        if s.get("target_contract") != ctx["target_contract"]:
            probs.append(f"{e}: spec.target_contract {str(s.get('target_contract'))[:16]} is not the manifest's target_contract "
                         f"{ctx['target_contract'][:16]}")
        st = S.STAGE.get(r.get("family_id"))
        if st in ("target", "zero_shot"):
            k = (r.get("dataset"), r.get("subject_fold"), r.get("content_fold"))
            if k not in cells:
                probs.append(f"{e}: (dataset, subject_fold, content_fold) {k} is not a manifest cell (§3.3)")
            elif s.get("split_hash") != cells[k]:
                probs.append(f"{e}: spec.split_hash {str(s.get('split_hash'))[:16]} is not the split_hash {cells[k][:16]} of the manifest "
                             f"cell {k}")
        elif st is not None and "split_hash" in s:
            probs.append(f"{e}: a {st} row carries a split_hash (only target and zero-shot rows are bound to a cell)")
    return probs


def check_rows(new, existing, mode, ctx=None):
    """Consistency of the new rows beyond deps.check_plan (M8 review items (a)-(i)); with `ctx` (manifest_context) also the
    manifest bindings (_manifest_problems: split_hash, target_contract, manifest sha256); then deps.check_plan on the existing
    plan plus the new rows. Raises PlanError listing the problems; returns {(block, family): rows}."""
    probs = [] if ctx is None else _manifest_problems(new, ctx)
    ids = [r["experiment_id"] for r in new]
    dup = [e for e, n in Counter(ids).items() if n > 1]
    if dup:
        probs.append(f"{len(dup)} duplicate new ids (first {dup[0]})")
    old = {r.get("experiment_id") for r in existing}
    clash = sorted(set(ids) & old)
    if clash:
        probs.append(f"{len(clash)} new ids collide with existing plan rows (first {clash[0]})")
    by_new, by_all = D.index(new), D.index(existing)
    by = {**by_all, **by_new}
    shas = {r["spec"].get("manifest_sha256") for r in new}
    if len(shas) != 1 or None in shas:
        probs.append(f"manifest_sha256 differs between the new rows: {sorted(map(str, shas))}")
    bridges = Counter()
    for r in new:
        e, s, fam = r["experiment_id"], r["spec"], r["family_id"]
        try:
            st = S.stage_of(r)
        except ValueError as ex:
            probs.append(str(ex))
            continue
        if s.get("stage") != st or row_id(fam, r["dataset"], r["subject_fold"], r["content_fold"], r["seed"], s) != e:
            probs.append(f"{e}: stage or id does not reproduce")
        if r["seed_scope"] != s.get("seed_scope") or s.get("seed_scope") != ("breadth" if r["seed"] == BREADTH_SEED else "panel"):
            probs.append(f"{e}: seed_scope {r['seed_scope']} / {s.get('seed_scope')} for seed {r['seed']}")
        if (s.get("block") == "panel") != (r["seed"] in PANEL_SEEDS) or r["seed"] not in (BREADTH_SEED,) + PANEL_SEEDS:
            probs.append(f"{e}: seed {r['seed']} in block {s.get('block')} (panel = private_bdf at 3407 / 3413, every other block 3401)")
        if s.get("block") == "panel" and r["dataset"] != PRIVATE:
            probs.append(f"{e}: a panel row for {r['dataset']} (§4.1: private_bdf only)")
        if (fam == S.TARGET and s.get("target") != ("current_class" if r["dataset"] == PRIVATE else "envelope")) or \
                (fam != S.TARGET and s.get("target") != "envelope"):
            probs.append(f"{e}: spec.target {s.get('target')!r}")
        lab = s.get("version")
        if mode == "primary" and (lab is not None or s.get("continuation_of") is not None):
            probs.append(f"{e}: a primary row carries version / continuation_of")
        if mode == "continuation" and (not isinstance(lab, str) or not re.fullmatch(r"continuation_\d+", lab)
                                       or s.get("continuation_of") is None):
            probs.append(f"{e}: a continuation row without its version label / continuation_of")
        if st == "donor_group":
            if s.get("donor_seed") != r["seed"] or s.get("sampler_seed") != r["seed"] or s.get("target_seed") is not None:
                probs.append(f"{e}: donor-group seeds {s.get('donor_seed')} / {s.get('sampler_seed')} / {s.get('target_seed')}, row {r['seed']}")
            if list(s.get("members") or []) != list(S.GROUP_MEMBERS[fam]):
                probs.append(f"{e}: members {s.get('members')}")
            if r["subject_fold"] is not None or r["content_fold"] is not None:
                probs.append(f"{e}: a donor group carries folds")
            if any(x in s.get("donor_set", []) for x in (r["dataset"], PRIVATE)) or (r["dataset"] == "fau" and "fau_cs" in s.get("donor_set", [])):
                probs.append(f"{e}: the donor set {s.get('donor_set')} holds the target cohort or private_bdf (§3.1)")
            if fam == S.CSX_DONOR and r["dataset"] not in CSX_TARGETS:
                probs.append(f"{e}: a CSX group for {r['dataset']} (§2.16: none for fau)")
            if fam == S.DONOR and s.get("block") not in ("core", "panel"):
                probs.append(f"{e}: a DONOR group in block {s.get('block')}")
            if fam in (S.RICH_DONOR, S.CSX_DONOR):
                h = by.get(s.get("horizon_from"))
                if h is None or h["family_id"] != S.DONOR or S.compute_limit(h) != S.compute_limit(r) or \
                        (h["dataset"], h["spec"].get("objective"), h["seed"]) != (r["dataset"], s.get("objective"), r["seed"]):
                    probs.append(f"{e}: horizon_from {s.get('horizon_from')} is not a {S.DONOR} group of the same (dataset, objective, "
                                 f"seed) and compute limit (§2.15, §2.16: equal updates)")
                elif lab is not None and (h["spec"].get("version") != lab or
                                          by.get(s.get("continuation_of"), {}).get("spec", {}).get("horizon_from") != h["spec"].get("continuation_of")):
                    probs.append(f"{e}: the horizon source of a continuation must be the continuation of its source's horizon group")
            if lab is not None:
                src = by.get(s.get("continuation_of"))
                if src is None or src["family_id"] != fam or src["spec"].get("block") != s.get("block") or \
                        S.compute_limit(r) <= S.compute_limit(src):
                    probs.append(f"{e}: continuation_of {s.get('continuation_of')} is not a {SHORT[fam]} group of the same block with a "
                                 f"lower compute limit")
            continue
        g = by.get(s.get("donor_group"))
        if st == "target" and s.get("init") == "random":
            if s.get("member") != S.SCRATCH or s.get("variant") != S.SCRATCH or s.get("donor_group") is not None or \
                    s.get("donor_seed") is not None or s.get("sampler_seed") is not None:
                probs.append(f"{e}: malformed from-scratch target")
            if mode != "primary" or s.get("block") not in ("core", "panel"):
                probs.append(f"{e}: a from-scratch target outside the primary core / panel block (S rows are never re-registered)")
            if s.get("target_seed") != r["seed"]:
                probs.append(f"{e}: target_seed {s.get('target_seed')} vs row seed {r['seed']}")
            continue
        if g is None or g["family_id"] not in S.DONOR_FAMILIES:
            probs.append(f"{e}: spec.donor_group {s.get('donor_group')} is not a donor group")
            continue
        slot = s.get("member")
        if slot not in GROUP_SLOTS[g["family_id"]]:
            probs.append(f"{e}: slot {slot!r} is not one of {GROUP_SLOTS[g['family_id']]} (concrete J1 / J025 members are never slots)")
        if lab != g["spec"].get("version"):
            probs.append(f"{e}: version label {lab!r} differs from its group's {g['spec'].get('version')!r}")
        if s.get("donor_seed") != g["seed"] or s.get("sampler_seed") != g["seed"]:
            probs.append(f"{e}: donor_seed / sampler_seed {s.get('donor_seed')} / {s.get('sampler_seed')}, group seed {g['seed']}")
        if st == "bridge":
            bridges[(g["experiment_id"], slot)] += 1
            if r["seed"] != g["seed"] or r["subject_fold"] is not None or r["content_fold"] is not None or s.get("target_seed") is not None:
                probs.append(f"{e}: bridge seed / folds")
        elif st == "target":
            if s.get("variant") != slot or s.get("init") != "donor" or s.get("target_seed") != r["seed"]:
                probs.append(f"{e}: target variant {s.get('variant')!r} / member {slot!r} / init {s.get('init')!r} / target_seed")
        else:
            mode_ = D.zero_shot_mode(r)
            if r["seed"] != g["seed"] or s.get("target_seed") is not None or s.get("variant") != C.ZS_MODE_NAME[mode_]:
                probs.append(f"{e}: zero-shot seed / target_seed / variant")
            if mode_ != "A" and (s.get("block") != "access" or slot not in ACCESS_SLOTS):
                probs.append(f"{e}: access mode {mode_} for slot {slot} in block {s.get('block')} (§4.1: AP, XP, J* only)")
            b = by.get(s.get("bridge"))
            if b is None or b["family_id"] != S.BRIDGE or b["spec"].get("donor_group") != g["experiment_id"] or b["spec"].get("member") != slot:
                probs.append(f"{e}: spec.bridge {s.get('bridge')} is not the bridge of ({g['experiment_id']}, {slot})")
    probs += [f"slot ({k[0]}, {k[1]}) has {n} bridge rows" for k, n in bridges.items() if n != 1]
    groups = [r for r in new if r["family_id"] in S.DONOR_FAMILIES]
    for gr in groups:
        have = {k[1] for k in bridges if k[0] == gr["experiment_id"]}
        if have != set(GROUP_SLOTS[gr["family_id"]]):
            probs.append(f"{gr['experiment_id']}: bridges for slots {sorted(have)}, expected {list(GROUP_SLOTS[gr['family_id']])}")
    for r in new:
        try:
            ups = D.upstreams(r, by)
        except ValueError as ex:
            probs.append(str(ex))
            continue
        bad = [u for u in ups if not _upstream_ok(r, u, by_new, by_all, mode)]
        if bad:
            probs.append(f"{r['experiment_id']} ({r['spec']['block']}): upstream(s) {bad} outside the block (§6.4)")
    if not probs:
        try:
            D.check_plan(list(existing) + list(new))
        except ValueError as ex:
            probs.append(f"deps.check_plan: {ex}")
    if probs:
        more = f" (+{len(probs) - 20} more)" if len(probs) > 20 else ""
        raise PlanError(f"{len(probs)} consistency problem(s): " + "; ".join(probs[:20]) + more)
    return Counter((r["spec"]["block"], r["family_id"]) for r in new)


def check_primary_counts(counts, ctx):
    exp = expected_counts(ctx)
    if dict(counts) != exp:
        diff = {f"{b}/{SHORT[f]}": (counts.get((b, f), 0), exp.get((b, f), 0)) for b, f in set(counts) | set(exp)
                if counts.get((b, f), 0) != exp.get((b, f), 0)}
        raise PlanError(f"row counts differ from §4.1 (got, expected): {diff}")
    blk = Counter()
    for (b, _), n in counts.items():
        blk[b] += n
    for b, n in BLOCK_TOTALS.items():
        if blk[b] != n:
            raise PlanError(f"block {b}: {blk[b]} rows, §4.1 says {n}")
    if blk["access"] > 210 or sum(blk.values()) > 1154:
        raise PlanError(f"access {blk['access']} > 210 or total {sum(blk.values())} > 1154")
    fam = Counter()
    for (_, f), n in counts.items():
        fam[f] += n
    want = {S.DONOR: 12, S.RICH_DONOR: 8, S.CSX_DONOR: 6, S.BRIDGE: 68, S.TARGET: 540, S.ZEROSHOT: 310 + blk["access"]}
    if dict(fam) != want:
        raise PlanError(f"family totals {dict(fam)} differ from §4.1 {want}")
    return blk, fam


def continuation_drift(r, old):
    """Fields in which continuation row `r` differs from the row `old` it continues, beyond those a continuation may change
    (CONT_FREE; of spec.budget only `continuation`, the compute limit; spec.horizon_from only on a group that has one)."""
    st, s, o = S.stage_of(r), r.get("spec") or {}, old.get("spec") or {}
    bad = [k for k in ROW_SAME if r.get(k, _ABSENT) != old.get(k, _ABSENT)]
    bad += [f"spec.{k}" for k in sorted(set(s) | set(o)) if k not in CONT_FREE[st] and s.get(k, _ABSENT) != o.get(k, _ABSENT)]
    if st == "donor_group":
        b, ob = dict(s.get("budget") or {}), dict(o.get("budget") or {})
        b.pop("continuation", None)
        ob.pop("continuation", None)
        if b != ob or "budget" not in s:
            bad.append("spec.budget (other than continuation)")
        if ("horizon_from" in s) != ("horizon_from" in o):
            bad.append("spec.horizon_from (present on one side only)")
    return bad


def check_continuation_counts(new, existing, gid):
    """Every downstream row of the continued groups is replicated exactly once (per block and family), and each continuation row
    equals the row it continues except for the fields a continuation may change (continuation_drift)."""
    by = D.index(existing)
    src = Counter()
    for r in new:
        s = r["spec"]
        old = by.get(s.get("continuation_of"))
        if old is None:
            raise PlanError(f"{r['experiment_id']}: continuation_of {s.get('continuation_of')} is not an existing row")
        if S.stage_of(old) != S.stage_of(r) or old["family_id"] != r["family_id"] or old["spec"].get("block") != s.get("block"):
            raise PlanError(f"{r['experiment_id']}: it continues a row of another stage, family or block")
        drift = continuation_drift(r, old)
        if drift:
            raise PlanError(f"{r['experiment_id']}: differs from the row it continues ({old['experiment_id']}) in {drift}; a continuation "
                            f"changes only {list(CONT_FREE[S.stage_of(r)])} (spec.budget: only continuation)")
        src[old["experiment_id"]] += 1
    if any(n != 1 for n in src.values()):
        raise PlanError("a row is continued twice")
    groups = {r["spec"]["continuation_of"] for r in new if r["family_id"] in S.DONOR_FAMILIES}
    want = {r["experiment_id"] for r in existing if r.get("family_id") in S.FAMILIES and S.stage_of(r) != "donor_group"
            and (r.get("spec") or {}).get("donor_group") in groups}
    got = {r["spec"]["continuation_of"] for r in new if r["family_id"] not in S.DONOR_FAMILIES}
    if got != want:
        raise PlanError(f"continuation of {gid}: {len(want - got)} downstream rows not replicated, {len(got - want)} unexpected")
    return Counter((r["spec"]["block"], r["family_id"]) for r in new)


# ------------------------------------------------------------------------------------------------------------ record
def training_code_files():
    """Repository paths of the training code of every prior33 code group (registry_patch.group_files) and core.V2_DEPS."""
    fs = {f"{d}/{f}" for g in RP.GROUPS for d, f in RP.group_files(g)} | {f"{d}/{f}" for d, f in core.V2_DEPS}
    return sorted(fs)


def record_status(record, rows, code_files=None):
    """(sha256 or None, problems) of the execution record for these rows (design §1, §5.1): present; the manifest sha256 listed;
    prior33.analysis.frozen_check(rows) ok; every training code file's sha256 listed (full or >= 16 hex digits)."""
    if not os.path.exists(record):
        return None, [f"the execution record {_rel(record)} is absent (design §1: written at registration, before the rows)"]
    with open(record, "rb") as f:
        raw = f.read()
    tokens = set(HEX.findall(raw.decode("utf-8", "replace").lower()))
    listed = lambda sha: bool(sha) and any(sha.startswith(t) for t in tokens)  # noqa: E731 (as prior33.analysis._listed)
    probs = []
    for m in sorted({r["spec"].get("manifest_sha256") for r in rows}):
        if not listed(m):
            probs.append(f"manifest sha256 {str(m)[:16]}... is not listed in the record")
    for m in sorted({r["spec"]["manifest_rich_sha256"] for r in rows if r["spec"].get("manifest_rich_sha256")}):
        if not listed(m):
            probs.append(f"rich manifest sha256 {str(m)[:16]}... is not listed in the record")
    from auditory_alignment_v3.prior33 import analysis as A  # numpy; only here
    fz = A.frozen_check(rows=rows, record_path=record)
    probs += [f"analysis.frozen_check: {p}" for p in fz["problems"]]
    for rel in (training_code_files() if code_files is None else code_files):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            probs.append(f"training code file {rel} is missing")
            continue
        with open(p, "rb") as f:
            if not listed(_sha(f.read())):
                probs.append(f"training code file {rel}: sha256 not listed in the record")
    return _sha(raw), probs


# ------------------------------------------------------------------------------------------------------------ main
BLOCK_ORDER = ("core", "access", "panel", "rich", "csx")   # §4.1 table order
STAGE_ORDER = (S.DONOR, S.RICH_DONOR, S.CSX_DONOR, S.BRIDGE, S.TARGET, S.ZEROSHOT)


def _table(counts):
    L, blk = [], Counter()
    for (b, f), n in sorted(counts.items(), key=lambda kv: (BLOCK_ORDER.index(kv[0][0]), STAGE_ORDER.index(kv[0][1]))):
        L.append(f"  {b:<7} {SHORT[f]:<11} {n:>5}")
        blk[b] += n
    L.append("  total   " + str(sum(blk.values())) + "  (" + ", ".join(f"{b} {blk[b]}" for b in BLOCK_ORDER if b in blk) + ")")
    return L


def _backup_path(path):
    """<path>.before_prior33_<date>, or with _<time>[_<n>] appended when that exists (an existing backup is never overwritten)."""
    stamp = datetime.datetime.now()
    p = f"{path}.before_prior33_{stamp:%Y%m%d}"
    if not os.path.exists(p):
        return p
    q, n = f"{p}_{stamp:%H%M%S}", 1
    while os.path.exists(q):
        q, n = f"{p}_{stamp:%H%M%S}_{n}", n + 1
    return q


def lock_plan(path, wait=None):
    """Exclusive flock on <path>.lock (module docstring) -> the open descriptor (os.close releases the lock). The lock file is
    created 0600 when absent and never removed (removing it would let two appenders lock different inodes); the holder's host,
    pid and time are written into it. PlanError when another appender holds it for longer than `wait` seconds."""
    lp = path + LOCK_SUFFIX
    wait = LOCK_WAIT_S if wait is None else wait
    fd = os.open(lp, os.O_RDWR | os.O_CREAT, 0o600)     # read-write: on NFS flock is a POSIX write lock
    t0 = time.monotonic()
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError as ex:
            if ex.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK) or time.monotonic() - t0 >= wait:
                try:
                    holder = os.pread(fd, 300, 0).decode("utf-8", "replace").strip() or "unknown holder"
                finally:
                    os.close(fd)
                raise PlanError(f"{_rel(lp)} is held by another plan appender ({holder}) [{ex.strerror}]: nothing written; rerun when "
                                f"it has finished. If that holder is gone (an NFSv3 lock of a crashed node outlives it), move the lock "
                                f"file aside and rerun") from None
            time.sleep(0.2)
    stamp = f"{socket.gethostname()} pid {os.getpid()} {datetime.datetime.now():%Y-%m-%dT%H:%M:%S} make_plan_ext_prior33.py\n"
    os.ftruncate(fd, 0)
    os.pwrite(fd, stamp.encode("utf-8"), 0)
    return fd


def append_rows(path, raw, new):
    """Append via tmp + os.replace under lock_plan: the file must still be the guarded one (content and inode) when the lock is
    held and again just before the rename; the previous file is kept as a backup. Afterwards the new file must be exactly what
    was written, the old file must not have changed size during the rename, and POST_CHECK_S seconds later the file must still
    begin with the written bytes (an appender that ignores the lock and replaces the file from an older read would drop these
    rows); PlanError otherwise (the rows were appended, but the other write needs a look). -> (sha256, line count, backup)."""
    data = raw + "".join(json.dumps(r) + "\n" for r in new).encode("utf-8")
    tmp = f"{path}.tmp_prior33_{os.getpid()}"
    lock = lock_plan(path)
    other = f"an appender that does not take {_rel(path + LOCK_SUFFIX)}"
    try:
        with open(path, "rb") as old:
            ino = os.fstat(old.fileno())
            if old.read() != raw:
                raise PlanError(f"{_rel(path)} changed while the block was built (another lane appended): nothing written; re-base and rerun")
            with open(tmp, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            bak = _backup_path(path)
            shutil.copy2(path, bak)
            st = os.stat(path)
            with open(path, "rb") as f:
                same = f.read() == raw
            if not same or (st.st_ino, st.st_dev) != (ino.st_ino, ino.st_dev):
                raise PlanError(f"{_rel(path)} changed while the block was written ({other}): nothing replaced; {_rel(bak)} is a copy of "
                                f"the file before that write; re-base and rerun")
            os.replace(tmp, path)
            moved = os.fstat(old.fileno()).st_size - len(raw)
        with open(path, "rb") as f:
            out = f.read()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
        os.close(lock)
    late = None
    if out == data and not moved and POST_CHECK_S > 0:
        time.sleep(POST_CHECK_S)
        with open(path, "rb") as f:
            late = f.read()
    if out != data or moved or (late is not None and not late.startswith(data)):
        what = ("the file read back is not the one written" if out != data else
                f"the old file changed size by {moved} bytes during the rename (those bytes are not in the new file)" if moved else
                f"{POST_CHECK_S:g} s later the file no longer begins with the written bytes (it was replaced from an older read)")
        raise PlanError(f"{len(new)} rows were appended to {_rel(path)}, but {what} ({other}): compare the file with {_rel(bak)} and "
                        f"with this block's rows before re-basing any guard")
    return _sha(out), len(out.decode("utf-8").splitlines()), bak


def main(argv=None, plan_ext=PLAN_EXT, guard=(GUARD_LINES, GUARD_SHA16), out=core.OUT, record=EXEC_RECORD, plan_rows=None,
         code_files=None):
    a = argparse.ArgumentParser(description="E34_PUBLIC_PRIOR plan rows (PUBLIC_PRIOR_DESIGN.md §4, §6.4); default: dry run")
    m = a.add_mutually_exclusive_group()
    m.add_argument("--dry-run", action="store_true", help="build and check, print counts, write nothing (the default)")
    m.add_argument("--apply", action="store_true", help="append the rows to plan_ext.jsonl")
    a.add_argument("--continuation", metavar="GID", help="the continuation version of donor group GID and its downstream rows (§2.10)")
    a.add_argument("--manifest", default=None, help=f"frozen manifest (default {_rel(MANIFEST)})")
    a.add_argument("--manifest-sha", default=None, help="its sha256 (full or >= 16 hex digits); required with --apply")
    args = a.parse_args(argv)
    apply = bool(args.apply)
    if apply and not args.continuation and not args.manifest_sha:
        raise PlanError("--apply needs --manifest-sha (the frozen manifest's sha256)")
    raw, ext = read_guarded(plan_ext, guard)
    base = core.load_rows() if plan_rows is None else list(plan_rows)
    existing = base + ext
    guard_line = f"plan_ext: {_rel(plan_ext)}: {len(ext)} lines, sha256 {_sha(raw)[:16]}... (guard ok)"
    placeholder = "E34_PUBLIC_PRIOR execution record not written yet (dry run)"
    rsha = None
    if os.path.exists(record):
        with open(record, "rb") as f:
            rsha = _sha(f.read())
    registered = placeholder if rsha is None else f"E34_PUBLIC_PRIOR execution record {_rel(record)} sha256 {rsha}"
    lines = [guard_line]
    if args.continuation:
        new, label, notes = build_continuation(args.continuation, existing, out, registered)
        msha = {r["spec"].get("manifest_sha256") for r in new}
        ctx = None
        if args.manifest or args.manifest_sha:
            man, got, _ = open_manifest(args.manifest or MANIFEST, args.manifest_sha)
            if msha != {got}:
                raise PlanError(f"the manifest {got[:16]}... is not the one of the continued rows ({sorted(map(str, msha))})")
            ctx = manifest_context(man, got)
        counts = check_rows(new, existing, "continuation", ctx)
        check_continuation_counts(new, existing, args.continuation)
        lines.append(f"continuation: {label} of {args.continuation} (compute limit {S.compute_limit(new[0])} ep-eq); rows checked against "
                     + ("the manifest and " if ctx else "") + "the rows they continue")
        lines += [f"note: {n}" for n in notes]
    else:
        e34 = [r["experiment_id"] for r in existing if r.get("family_id") in S.FAMILIES]
        if e34:
            raise PlanError(f"the plan already holds {len(e34)} E34_PUBLIC_PRIOR rows (first {e34[0]}): the primary block is registered "
                            f"once; use --continuation for a continuation version")
        man, msha, verified = open_manifest(args.manifest or MANIFEST, args.manifest_sha)
        ctx = manifest_context(man, msha)
        new = build_primary(ctx, registered)
        counts = check_rows(new, existing, "primary", ctx)
        check_primary_counts(counts, ctx)
        unsupported = [f"{c} {mo}" for c, mo in ACCESS_MODES if (c, mo) not in ctx["access"]]
        lines.append(f"manifest: {_rel(args.manifest or MANIFEST)} sha256 {msha[:16]}... ({'verified' if verified else 'computed, not verified'})"
                     + (f"; access modes not supported by the manifest: {', '.join(unsupported)}" if unsupported else ""))
    rec_sha, rec_probs = record_status(record, new, code_files)
    lines.append(f"execution record: {_rel(record)} " + ("absent" if rec_sha is None else f"sha256 {rec_sha[:16]}...")
                 + (f"; --apply would refuse: {len(rec_probs)} problem(s)" if rec_probs else "; complete for --apply"))
    if apply and rec_probs:
        raise PlanError("--apply refused, execution record: " + "; ".join(rec_probs[:12]) + (" ..." if len(rec_probs) > 12 else ""))
    print(("E34_PUBLIC_PRIOR plan rows: " + ("APPEND" if apply else "dry run, nothing written")))
    print("\n".join(lines))
    for problem in rec_probs:
        print("execution record check: " + problem)
    print("\n".join(_table(counts)))
    res = {"mode": "continuation" if args.continuation else "primary", "applied": apply, "rows": new, "counts": dict(counts),
           "plan_ext_lines": len(ext), "plan_ext_sha256": _sha(raw), "record_sha256": rec_sha, "record_problems": rec_probs}
    if apply:
        if any(r["registered"] == placeholder for r in new):
            raise PlanError("internal: placeholder registration on an --apply")
        sha, n, bak = append_rows(plan_ext, raw, new)
        print(f"appended {len(new)} rows: {_rel(plan_ext)} now {n} lines, sha256 {sha} (backup {_rel(bak)}); re-base the other lanes' "
              f"guards to these values")
        res.update(new_sha256=sha, new_lines=n, backup=bak)
    return res


if __name__ == "__main__":
    try:
        main()
    except PlanError as ex:
        print(f"refused: {ex}", file=sys.stderr)
        sys.exit(1)
