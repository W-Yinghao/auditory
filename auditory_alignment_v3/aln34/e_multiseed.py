"""ALN3.4 E seed panel: multi-seed aggregation of the completed private-task (E) seed panel (seeds 3401 / 3407 / 3413).

Panel (ADDENDUM_03, ALN3.1 role panel P5_PRIVATE; 85 rows per seed): E_GENERIC {NCE, CS_SINGLE} x {cbramod, reve} x
{random_full, pretrained_peft, pretrained_full}; E_LOCAL lag_local_tokens full (NCE, CS_SINGLE); E_PUBLIC_TRANSFER source
lag_local_tokens task_partial (NCE, CS_SINGLE); E_GX GX_NATIVE full. Rows: core.PLAN (the v3.0 panel rows) and
private/auditory_alignment_v3/plan_ext.jsonl block 2; seed links: governance/seed_panel_v31_registry.json.
Frozen rule: ADDENDUM_05 §6 (seed panel supplement). Analysis note, written before any panel value was computed:
private/auditory_alignment_v3/aln34/E_MULTI_SEED_NOTE.md (its "Code registration" section records the sha256 of this file
before the first real-data run).

The ADDENDUM_05 private machinery is imported, not re-implemented: bc_interim.load_private (per seed, bc_interim.SEED switched
for the duration of the call), private_families, run_family, member_values, levels, aggregate_private (seed-3401
reproduction), privacy_scan; sci_r1.stats (bootstrap-t over children, B = 4,000; max-t within a family). New here:
  * panel families: each frozen family restricted (by design, not by data) to the members whose reference and candidate are
    both panel configurations; the same member set for every seed; the frozen labels, so the replicate indices are shared by
    the three seeds, the identity mean and the published seed-3401 tables;
  * per seed 3401 / 3407 / 3413; the identity mean over the seeds in which the pair exists (a reference of one seed is never
    paired with a candidate of another), with the same family machinery; between-seed range, spread and SD; levels of the 17
    panel configurations per seed and on the per-child seed means; HA / NH columns (descriptive);
  * coverage, pairing QC, the number-by-number seed-3401 reproduction of the published private_e.json;
  * the declared exploratory additions of the note: A max-t for the history increment within the panel families (frozen label
    '<family>|<scope>|sec', so its pointwise intervals are the frozen ones); B a pointwise interval for the history-increment
    level; C between-seed spread against the per-seed simultaneous widths; D Monte-Carlo stability of the primary interval
    classes; E a determinism re-computation and the measured peak memory.
CORRECTION_01: 'random_full -> pretrained_full' is a recipe contrast; the frozen code's tag is kept as 'frozen_tag'.
v2 (2026-10-17, after version 1 had been generated and read; v1 archived in private/auditory_alignment_v3/aln34/e_multiseed/
v1_20261017T0011/): post hoc addition F (unit-level description of all 255 panel units, declared in the note's addendum before it
was computed) and a number-by-number comparison with version 1; every version-1 statistic is unchanged.
v3 (2026-10-17, after an independent verification of version 2; v2 archived in .../e_multiseed/v2_20261017T0018/; the note's
"correction 01" declares every change before it was computed): the training-recipe descriptors of every panel record (lr, epochs,
trainable backbone parameters, progressive-prefix records; with a check against the recipe files' 'chosen' pair), post hoc addition G
(unit NLL excess over the median of the 14 reference configurations in the same seed and fold), the seed-3401 critical-value ranges of
the panel and full frozen families, the Monte-Carlo cross-reference taken from the section order, exact wording of the version
comparison, and a number-by-number comparison with versions 1 and 2. No earlier statistic changes. Re-run once (code registered again)
after two wording fixes (code-registration phrase, §1.15 heading); the first version-3 run is archived in .../v3_first_run_20261017T0109/
and compared number by number as well.
Not part of any training code hash; reads unit records (and the ALN2 recipe files they name) only; no GPU.

Usage: python -m auditory_alignment_v3.aln34.e_multiseed [--update-doc] [--mc-k K]
  --update-doc  (re)generate docs/auditory_alignment_v3/E_MULTI_SEED_RESULTS.md, keeping its hand-written sections verbatim
                (without it, the generated version is written to the results directory only)."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import resource
import socket
import time
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3.sci_r1 import stats as S

SEEDS = (3401, 3407, 3413)
OBJ, ARCH = BI.OBJ, BI.ARCH
PANEL_ADAPT = ("random_full", "pretrained_peft", "pretrained_full")
PANEL_CONFIGS = (tuple(("E_GENERIC", o, a, ad) for o in OBJ for a in ARCH for ad in PANEL_ADAPT)
                 + tuple(("E_LOCAL", o, "lag_local_tokens", "full") for o in OBJ)
                 + tuple(("E_PUBLIC_TRANSFER", o, "lag_local_tokens", "task_partial") for o in OBJ)
                 + (("E_GX", "GX_NATIVE", "GX", "full"),))
PANEL_SET = frozenset(PANEL_CONFIGS)
PRIMARY = ("NLL", "AUC")                 # co-primary, separate families (ADDENDUM_05 §5)
SECONDARY = ("hist_gain", "twin_sens")   # frozen secondaries (pointwise)
METRICS = PRIMARY + SECONDARY
HG = "hist_gain"
FAMILY_ORDER = ("PE-GENERIC", "PE-LOCAL", "PE-TRANSFER")
FROZEN_FULL_TAG = "initialization (matched full update)"
CORRECTED_TAG = "recipe (CORRECTION_01)"
EQUIVALENT_HASHES = {"f2cf13bc441a6386": "51341741b9019c88"}  # IMPLEMENTATION_RECEIPT §5: registry move 2026-10-10 20:20, no computational change
MC_K, MC_STEP = 50, 1000  # alternative draw set k adds MC_STEP * k to sci_r1.stats.SEED (k = 1..MC_K); k = 0 is the declared draw
HAND = ("2.", "3.", "4.", "6.", "7.")  # hand-written sections of the results document (carried over verbatim)
DOC_VERSION = "Version 3"
# addition G (post hoc, note correction 01): reference = every panel configuration except the three E_GENERIC CS_SINGLE reve ones
G_EXCLUDED = tuple(("E_GENERIC", "CS_SINGLE", "reve", ad) for ad in PANEL_ADAPT)
G_REFERENCE = tuple(c for c in PANEL_CONFIGS if c not in G_EXCLUDED)
# section numbers of section 1, from the order in which render() writes them (so that cross-references follow the order)
SECTION_ORDER = tuple((fam, m) for fam in FAMILY_ORDER for m in PRIMARY) + ("hist", "twin", "levels", "groups", "coverage", "qc", "width", "mc",
                                                                           "unit", "recipe")
SECNO = {k: f"1.{j + 1}" for j, k in enumerate(SECTION_ORDER)}
DEC = {"NLL": 4, "AUC": 3, "hist_gain": 4, "twin_sens": 4}
NAME = {"NLL": "calibrated NLL", "AUC": "AUC", "hist_gain": "history increment", "twin_sens": "twin sensitivity"}
UNIT = {"NLL": "bits per trial, ΔNLL = reference − candidate", "AUC": "AUC difference, candidate − reference",
        "hist_gain": "bits per trial, candidate − reference", "twin_sens": "bits per trial, candidate − reference"}
NOT_IN_PANEL_FIXED = (
    "PE-COMPLEMENT and PE-DISTILL (whole families; E_COMPLEMENT and E_DISTILL have seed-3401 rows only; PRIVATE_E_INTERIM §5–§6)",
    "levels of every non-panel configuration: E_LOCAL density_tokens / legacy_pool4 and the lag_local early / late / joint windows; "
    "E_GX early / late / joint; E_GENERIC pretrained_frozen / pretrained_partial; E_PUBLIC_TRANSFER task_full and the cbramod / reve "
    "sources; E_COMPLEMENT; E_DISTILL (PRIVATE_E_INTERIM §1)",
    "the ADDENDUM_08 group / age / wearing-duration / stage associations (PRIVATE_RESEARCHER_SUMMARY) and the SCI_R1 private results")
RES = os.environ.get("EM_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln34", "e_multiseed"))
DOCS = os.environ.get("EM_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
PRIV = os.environ.get("EM_PRIV", os.path.join(core.OUT, "aln34", "e_multiseed"))
NOTE = os.path.join(core.OUT, "aln34", "E_MULTI_SEED_NOTE.md")
PUBLISHED = os.path.join(core.REPO, "results", "auditory_alignment_v3", "bc_interim_private", "private_e.json")
PUBLISHED_PRIVATE = os.path.join(core.OUT, "bc_interim", "private", "private_e.json")
REGISTRY = os.path.join(core.OUT, "governance", "seed_panel_v31_registry.json")
UNITS = os.path.join(core.OUT, "units")
TESTS = os.path.join(core.REPO, "tests", "auditory_alignment_v3", "aln34", "test_e_multiseed.py")
V1_ARCHIVE = os.path.join(core.OUT, "aln34", "e_multiseed", "v1_20261017T0011")
V2_ARCHIVE = os.path.join(core.OUT, "aln34", "e_multiseed", "v2_20261017T0018")
V3_FIRST_RUN = os.path.join(core.OUT, "aln34", "e_multiseed", "v3_first_run_20261017T0109")  # first version-3 run (code 1a94eb22), wording fixed after it
ARCHIVES = (("version 1", V1_ARCHIVE), ("version 2", V2_ARCHIVE), ("the first version-3 run", V3_FIRST_RUN))


# ------------------------------------------------------------------------------------------------ scopes
@contextlib.contextmanager
def seed_scope(seed):
    """bc_interim.SEED (the frozen loader's seed filter) set to `seed` for this block only."""
    old = BI.SEED
    BI.SEED = seed
    try:
        yield
    finally:
        BI.SEED = old


@contextlib.contextmanager
def draw_scope(offset):
    """shift every replicate-index seed by `offset` (sci_r1.stats.group_seed reads stats.SEED at call time), this block only."""
    old = S.SEED
    S.SEED = old + offset
    try:
        yield
    finally:
        S.SEED = old


# ------------------------------------------------------------------------------------------------ panel definition
def config_of(r):
    """frozen configuration key of a plan row at its own seed (bc_interim.pcfg_of with its seed filter set to the row's seed)."""
    with seed_scope(r["seed"]):
        return BI.pcfg_of(r)


def row_in_panel(r):
    """registered panel rows and their seed-3401 counterparts (by design): seeds 3401/3407/3413, one of the 17 panel configurations."""
    return r["seed"] in SEEDS and str(r.get("family_id", "")).startswith("E_") and config_of(r) in PANEL_SET


def relabel(tag):
    return CORRECTED_TAG if tag == FROZEN_FULL_TAG else tag


def panel_families():
    """frozen ADDENDUM_05 §5 families restricted to the members whose reference and candidate are panel configurations."""
    out = []
    for fam, sc, members in BI.private_families():
        keep = [m for m in members if m[1] in PANEL_SET and m[2] in PANEL_SET]
        if keep:
            out.append({"family": fam, "scope": sc, "members": [(n, r, c, relabel(t)) for n, r, c, t in keep],
                        "frozen_tags": {n: t for n, _, _, t in keep}, "n_members_frozen": len(members),
                        "non_panel_members": [m[0] for m in members if not (m[1] in PANEL_SET and m[2] in PANEL_SET)]})
    return out


def full_families_with_panel_members():
    """the full frozen families that contain at least one panel member (all members kept; for the seed-3401 comparison)."""
    out = []
    for fam, sc, members in BI.private_families():
        keep = [m[0] for m in members if m[1] in PANEL_SET and m[2] in PANEL_SET]
        if keep:
            out.append({"family": fam, "scope": sc, "members": members, "panel_members": keep})
    return out


def fkey(f):
    return f"{f['family']}|{f['scope']}"


def plabel(f, m):
    """frozen primary family label (aggregate_private: f'{fam}|{sc}|{m}')."""
    return f"{fkey(f)}|{m}"


def slabel(f):
    """frozen secondary label (aggregate_private: f'{fam}|{sc}|sec')."""
    return f"{fkey(f)}|sec"


def block(res, f, m, sim_hg=False):
    if m in PRIMARY:
        return res["families"][plabel(f, m)]
    if sim_hg and m == HG:
        return res["hist_gain_simultaneous"][fkey(f)]
    return res["secondary"][fkey(f)][m]


def fams_json(fams):
    return [{k: (v if k != "members" else [[m[0], BI.ckey(m[1]), BI.ckey(m[2]), m[3]] for m in v]) for k, v in f.items() if k != "orig_members"} for f in fams]


# ------------------------------------------------------------------------------------------------ loading
def _sha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=float).encode()).hexdigest()


def census_of(row, rec):
    """counts, ids, hashes and descriptors of one panel record; endpoint values are only tested for presence, never kept."""
    ev = rec.get("eval") or {}
    pp = ev.get("per_participant") or {}
    ncal = ev.get("native_calibration") or {}
    nc = ncal.get("per_participant") or {}
    pa = lambda c: (nc.get(c) or {}).get("positive_affine") or {}
    rrow = rec.get("row") or {}
    present = all(pa(c).get("nll_bits") is not None and pa(c).get("auc_score") is not None and pp[c].get("hist_gain_bits") is not None
                  and pp[c].get("hist_gain_twin_bits") is not None for c in pp)
    return {"family": row["family_id"], "seed": row["seed"], "config": BI.ckey(config_of(row)), "fold": [row["subject_fold"], row["content_fold"]],
            "record_seed": rrow.get("seed"), "bound_seed": (rec.get("bound_row") or {}).get("seed"), "record_spec_equals_row": rrow.get("spec") == row["spec"],
            "code_hash": rec.get("code_hash"), "code_group": rec.get("code_group"), "target_contract": rec.get("target_contract"),
            "stratum": rec.get("information_stratum"), "selection_rule": rec.get("selection_rule"), "calibration_set": ncal.get("calibration_set"),
            "n_calibration_trials": ncal.get("n_calibration_trials"), "head_fit": (ev.get("readout") or {}).get("head_fit"),
            "native_head": (ev.get("native_head") or {}).get("kind"), "children": {c: [pp[c].get("n"), pa(c).get("n")] for c in sorted(pp)},
            "groups": {c: pp[c].get("group") for c in sorted(pp)}, "endpoint_fields_present": bool(present), "donor": rec.get("donor"),
            "calibrator": {k: v for k, v in ((ncal.get("methods") or {}).get("positive_affine") or {}).items() if k in ("slope", "intercept")},
            "recipe": recipe_of(rec)}


def recipe_of(rec):
    """training-recipe descriptors of one record (v3; no endpoint value): resolved_config (learning rates, epochs, optimizer, recipe
    file), the run-time learning rates, the backbone contract's trainable-parameter counts and whether any training-curve entry carries a
    progressive-prefix record ('open_groups', written by the fm_dense schedule)."""
    rc, bc = rec.get("resolved_config") or {}, rec.get("backbone_contract") or {}
    tl = bc.get("trainable_layers")
    return {"lr_backbone": rc.get("lr_backbone"), "lr_head": rc.get("lr_head"), "lr": rc.get("lr"), "optimizer": rc.get("optimizer"),
            "epochs": rc.get("epochs"), "recipe_file": rc.get("recipe_file"), "run_lr_backbone": rec.get("lr_backbone"),
            "run_lr_head": rec.get("lr_head"), "adaptation": bc.get("adaptation"),
            "trainable_layers": tl if tl is None or isinstance(tl, str) else json.dumps(tl, ensure_ascii=False), "n_params": bc.get("n_params"),
            "n_trainable_backbone": bc.get("n_trainable_backbone"), "has_resolved_config": bool(rc),
            "curve_open_groups": any(isinstance(e, dict) and "open_groups" in e for e in (rec.get("curve") or []))}


class Census:
    """loader wrapper: returns the record unchanged; keeps the status of every record it served and census_of() of panel records."""

    def __init__(self, load, rows):
        self.inner, self.rows, self.info, self.status = load, {r["experiment_id"]: r for r in rows}, {}, {}

    def __call__(self, eid):
        rec = self.inner(eid)
        self.status[eid] = "missing" if rec is None else rec.get("status")
        r = self.rows.get(eid)
        if rec is not None and rec.get("status") == "complete" and r is not None and row_in_panel(r):
            self.info[eid] = census_of(r, rec)
        return rec


def load_seed(rows, load, seed):
    """bc_interim.load_private for one seed: its own seed filter (bc_interim.SEED) is switched to `seed` during the call."""
    with seed_scope(seed):
        return BI.load_private(rows, load)


def registry_triples(path=REGISTRY):
    """canonical cell -> {seed: experiment_id} for the E requirements of the ALN3.1 seed-panel registry."""
    reg = json.load(open(path))
    trip = defaultdict(dict)
    for q in reg["requirements"]:
        if str(q["family_id"]).startswith("E_"):
            trip[q["canonical"]][q["seed"]] = q["experiment_id"]
    return dict(trip)


# ------------------------------------------------------------------------------------------------ per block (one seed or the identity mean)
def run_block(fams, vals, grp, notes):
    """frozen machinery on one set of child values. Primary: NLL and AUC families with max-t (+ HA / NH columns). Secondary:
    history increment and twin sensitivity, pointwise, frozen label '<family>|<scope>|sec'. Addition A: the history increment
    with max-t under the same label (pointwise numbers identical to the secondary block)."""
    g = lambda i: grp.get(i)
    res = {"families": {}, "secondary": {}, "hist_gain_simultaneous": {}}
    for f in fams:
        for m in PRIMARY:
            res["families"][plabel(f, m)] = {"family": f["family"], "scope": f["scope"], **BI.run_family(plabel(f, m), f["members"], vals, m, notes, True, g)}
        res["secondary"][fkey(f)] = {m: BI.run_family(slabel(f), f["members"], vals, m, notes, False, g) for m in SECONDARY}
        res["hist_gain_simultaneous"][fkey(f)] = BI.run_family(slabel(f), f["members"], vals, HG, notes, True, None)
    for f in fams:  # frozen tag of each member, next to the (CORRECTION_01) tag used here
        for blk in [res["families"][plabel(f, m)] for m in PRIMARY] + list(res["secondary"][fkey(f)].values()) + [res["hist_gain_simultaneous"][fkey(f)]]:
            for name, r in blk.get("members", {}).items():
                r["frozen_tag"] = f["frozen_tags"][name]
    return res


def seed_mean_deltas(vals_by_seed, ref, cand, metric):
    """{child: (mean over the seeds with the pair of the within-seed paired difference, number of such seeds)}."""
    per = {s: BI.member_values(v, ref, cand, metric) for s, v in vals_by_seed.items()}
    ids = set().union(*[set(p) for p in per.values()]) if per else set()
    return {i: (float(np.mean([per[s][i] for s in per if i in per[s]])), int(sum(i in per[s] for s in per))) for i in sorted(ids)}


def seed_mean_inputs(fams, vals_by_seed, complete_case=False):
    """pseudo-configurations holding the identity seed means (reference 0, candidate the signed mean, so that bc_interim.diff
    returns the mean difference for both directions); bc_interim.run_family then applies unchanged with the frozen labels."""
    pv, sfams, nseeds = {}, [], {}
    for f in fams:
        members = []
        for name, ref, cand, tag in f["members"]:
            R, C = ("SM_REF", fkey(f), name), ("SM_CAND", fkey(f), name)
            pr, pc = defaultdict(dict), defaultdict(dict)
            for m in METRICS:
                sgn = -1.0 if BI.PDIR[m] == "lower" else 1.0
                kept = {}
                for i, (x, k) in seed_mean_deltas(vals_by_seed, ref, cand, m).items():
                    if complete_case and k < len(vals_by_seed):
                        continue
                    pr[i][m] = 0.0; pc[i][m] = sgn * x; kept[i] = k
                nseeds[(fkey(f), name, m)] = kept
            pv[R], pv[C] = dict(pr), dict(pc)
            members.append((name, R, C, tag))
        sfams.append({**f, "members": members, "orig_members": f["members"]})
    return pv, sfams, nseeds


def run_seed_mean(fams, vals_by_seed, grp, notes, complete_case=False):
    pv, sfams, nseeds = seed_mean_inputs(fams, vals_by_seed, complete_case)
    res = run_block(sfams, pv, grp, notes)
    for f in sfams:  # the real configurations back into the member records; the seed-count distribution per member and metric
        orig = {m[0]: m for m in f["orig_members"]}
        blocks = [res["families"][plabel(f, m)] for m in PRIMARY] + list(res["secondary"][fkey(f)].values()) + [res["hist_gain_simultaneous"][fkey(f)]]
        for blk in blocks:
            for name, r in blk.get("members", {}).items():
                r["ref"], r["cand"] = BI.ckey(orig[name][1]), BI.ckey(orig[name][2])
                r["identities_by_n_seeds"] = {str(k): v for k, v in sorted(Counter(nseeds[(fkey(f), name, blk["metric"])].values()).items())}
    return res


# ------------------------------------------------------------------------------------------------ levels
def panel_levels(vals, grp, notes):
    """bc_interim.levels (label 'plevels') for the panel configurations present in `vals`; addition B: pointwise bootstrap-t
    interval and HA / NH means of the history-increment level (seeded like the frozen NLL / AUC levels)."""
    cfgs = [c for c in PANEL_CONFIGS if c in vals]
    g = lambda i: grp.get(i)
    out = BI.levels(vals, cfgs, list(METRICS), "plevels", notes, g)
    for c in cfgs:
        v = vals[c]
        ids = sorted(i for i in v if HG in v[i] and np.isfinite(v[i][HG]))
        if len(ids) < 3:
            continue
        s = S.summary(np.array([v[i][HG] for i in ids]), seed=S.group_seed("plevels", BI.ckey(c), HG))
        gs = defaultdict(list)
        for i in ids:
            gs[g(i)].append(v[i][HG])
        out[BI.ckey(c)]["hist_gain_ci"] = {"n": len(ids), **{k: float(s[k]) for k in ("est", "ci_low", "ci_high")},
                                           "groups": {str(k): ({"n": len(x), "est": float(np.mean(x))} if len(x) >= BI.MIN_N else {"n": len(x)})
                                                      for k, x in sorted(gs.items(), key=lambda kv: str(kv[0]))}}
    return out


def seed_mean_values(vals_by_seed):
    """per panel configuration and child: the mean over the seeds of each finite endpoint value; and the number of seeds."""
    out, nseeds = {}, {}
    for c in PANEL_CONFIGS:
        acc = defaultdict(lambda: defaultdict(list))
        for vals in vals_by_seed.values():
            for i, d in (vals.get(c) or {}).items():
                for m, x in d.items():
                    if x is not None and np.isfinite(x):
                        acc[i][m].append(float(x))
        if acc:
            out[c] = {i: {m: float(np.mean(x)) for m, x in d.items()} for i, d in sorted(acc.items())}
            nseeds[c] = {i: max(len(x) for x in d.values()) for i, d in acc.items()}
    return out, nseeds


def unit_levels(census, vals_by_seed):
    """addition F (post hoc, declared in the note after version 1 was read; descriptive): for every panel unit (configuration x seed
    x subject fold) the number of test children, the mean over them of calibrated NLL, AUC and history increment, and the unit's
    training-side positive-affine calibrator slope / intercept."""
    out = {}
    for eid, i in sorted(census.info.items(), key=lambda kv: (kv[1]["config"], kv[1]["seed"], kv[1]["fold"])):
        c = tuple(i["config"].split("|"))
        vals = vals_by_seed.get(i["seed"], {}).get(c, {})
        kids = [k for k in i["children"] if k in vals]
        r = {"config": i["config"], "seed": i["seed"], "fold": i["fold"], "n": len(kids)}
        for m in ("NLL", "AUC", HG):
            x = [vals[k][m] for k in kids if m in vals[k] and np.isfinite(vals[k][m])]
            r[m] = float(np.mean(x)) if x else None
        r["calibrator_slope"] = (i.get("calibrator") or {}).get("slope")
        r["calibrator_intercept"] = (i.get("calibrator") or {}).get("intercept")
        out[f"{i['config']}|{i['seed']}|{i['fold'][0]}|{i['fold'][1]}"] = r
    return out


def unit_nll_excess(ul):
    """addition G (post hoc; declared in the note's correction 01 before it was computed; descriptive): per panel unit, the unit NLL (addition
    F) minus the median of the unit NLLs of the 14 reference configurations (every panel configuration except E_GENERIC CS_SINGLE reve
    random_full / pretrained_peft / pretrained_full) in the same seed and subject fold; the range of the excess over the reference units;
    per configuration and seed, how many of its units lie above the largest reference excess. No interval, no threshold for any decision."""
    ref = {BI.ckey(c) for c in G_REFERENCE}
    cell = lambda r: f"{r['seed']}|{r['fold'][0]}|{r['fold'][1]}"
    vals = defaultdict(list)
    for r in ul.values():
        if r["config"] in ref and r.get("NLL") is not None:
            vals[cell(r)].append(r["NLL"])
    med = {k: float(np.median(v)) for k, v in sorted(vals.items())}
    exc = {k: (None if r.get("NLL") is None or cell(r) not in med else float(r["NLL"] - med[cell(r)])) for k, r in ul.items()}
    rx = [exc[k] for k, r in ul.items() if r["config"] in ref and exc[k] is not None]
    lo, hi = (min(rx), max(rx)) if rx else (None, None)
    per = defaultdict(dict)
    for k, r in ul.items():
        per[(r["config"], r["seed"])][r["fold"][0]] = exc[k]
    order = {BI.ckey(c): j for j, c in enumerate(PANEL_CONFIGS)}
    by = {}
    for (c, s), d in sorted(per.items(), key=lambda kv: (order.get(kv[0][0], 99), kv[0][1])):
        x = [d[f] for f in sorted(d) if d[f] is not None]
        by[f"{c}|{s}"] = {"reference": c in ref, "excess_by_subject_fold": {str(f): d[f] for f in sorted(d)}, "n_units": len(d),
                          "min": min(x) if x else None, "max": max(x) if x else None,
                          "n_above_reference_max": None if hi is None else sum(v > hi for v in x)}
    return {"definition": "unit NLL minus the median unit NLL of the 14 reference configurations in the same seed and subject fold (bits per trial)",
            "reference_configurations": [BI.ckey(c) for c in G_REFERENCE], "excluded_configurations": [BI.ckey(c) for c in G_EXCLUDED],
            "reference_median_by_seed_fold": med, "n_reference_units_by_seed_fold": {k: len(v) for k, v in sorted(vals.items())},
            "n_reference_units": len(rx), "reference_excess_range": [lo, hi], "excess": exc, "by_configuration_seed": by}


def _recipe_file(path, cache):
    """`chosen` pair, development cell, search epochs and candidate count of an ALN2 recipe file named by a record (read once)."""
    if not path:
        return None
    if path not in cache:
        try:
            d = json.load(open(os.path.join(core.REPO, path)))
            cache[path] = {"chosen": d.get("chosen"), "dev_cell": d.get("dev_cell"), "search_epochs": d.get("epochs"),
                           "n_candidates": len(d.get("candidates") or [])}
        except (OSError, ValueError):
            cache[path] = None
    return cache[path]


def recipes(census):
    """v3: training-recipe descriptors per panel configuration, from every panel record of the three seeds (descriptor sets, units per
    seed, the recipe file's `chosen` pair against the record's learning rates) and the PE-GENERIC recipe differences random_full ->
    candidate. Descriptors only; no endpoint value."""
    by = defaultdict(lambda: {"units_per_seed": Counter(), "sets": Counter(), "example": {}})
    for i in census.info.values():
        r = i.get("recipe") or {}
        k = json.dumps(r, sort_keys=True, default=str)
        b = by[i["config"]]
        b["units_per_seed"][str(i["seed"])] += 1; b["sets"][k] += 1; b["example"][k] = r
    cache, cfgs = {}, {}
    for c in PANEL_CONFIGS:
        ck = BI.ckey(c)
        if ck not in by:
            continue
        sets = []
        for k, n in sorted(by[ck]["sets"].items()):
            r = {**by[ck]["example"][k], "n_units": n}
            rf = _recipe_file(r.get("recipe_file"), cache)
            ch = (rf or {}).get("chosen") or None
            r["recipe_chosen"], r["recipe_dev_cell"], r["recipe_search_epochs"] = ch, (rf or {}).get("dev_cell"), (rf or {}).get("search_epochs")
            r["lr_equals_recipe_chosen"] = None if not ch else bool(
                ch.get("lr_backbone") == r["lr_backbone"] == r["run_lr_backbone"] and ch.get("lr_head") == r["lr_head"] == r["run_lr_head"])
            sets.append(r)
        cfgs[ck] = {"units_per_seed": dict(sorted(by[ck]["units_per_seed"].items())), "n_descriptor_sets": len(sets), "descriptor_sets": sets}
    contrasts = {}
    for f in panel_families():
        if f["family"] != "PE-GENERIC":
            continue
        for name, ref, cand, _ in f["members"]:
            a, b = cfgs.get(BI.ckey(ref)), cfgs.get(BI.ckey(cand))
            if not a or not b or a["n_descriptor_sets"] != 1 or b["n_descriptor_sets"] != 1:
                contrasts[f"{fkey(f)}|{name}"] = None
                continue
            x, y = a["descriptor_sets"][0], b["descriptor_sets"][0]
            pair = lambda key: [x.get(key), y.get(key)]
            contrasts[f"{fkey(f)}|{name}"] = {
                "ref": BI.ckey(ref), "cand": BI.ckey(cand), **{key: pair(key) for key in ("lr_backbone", "lr_head", "epochs", "n_params",
                                                                                          "n_trainable_backbone", "curve_open_groups")},
                "backbone_lr_ref_over_cand": (x["lr_backbone"] / y["lr_backbone"]) if x.get("lr_backbone") and y.get("lr_backbone") else None,
                "every_backbone_parameter_trained": [x.get("n_params") is not None and x.get("n_trainable_backbone") == x.get("n_params"),
                                                     y.get("n_params") is not None and y.get("n_trainable_backbone") == y.get("n_params")]}
    return {"configurations": cfgs, "pe_generic_contrasts": contrasts, "n_records": len(census.info),
            "n_records_with_open_groups": sum(1 for i in census.info.values() if (i.get("recipe") or {}).get("curve_open_groups")),
            "one_descriptor_set_per_configuration": all(v["n_descriptor_sets"] == 1 for v in cfgs.values())}


# ------------------------------------------------------------------------------------------------ between seeds
def spread_stats(ests):
    v = [ests[s] for s in sorted(ests)]
    return {"per_seed": {str(s): ests[s] for s in sorted(ests)}, "min": min(v), "max": max(v), "spread": max(v) - min(v),
            "sd": float(np.std(v, ddof=1)) if len(v) >= 2 else None, "n_seeds": len(v)}


def width_category(spread, widths):
    """between-seed spread against the per-seed simultaneous widths: one symmetric rule for every family."""
    if spread < min(widths):
        return "below_every_width"
    if spread > max(widths):
        return "above_every_width"
    return "between"


def between_seed(per_seed, fams):
    out = {}
    for f in fams:
        for name, *_ in f["members"]:
            for m in METRICS:
                ests = {s: block(per_seed[s], f, m)["members"].get(name, {}).get("est") for s in per_seed}
                ests = {s: e for s, e in ests.items() if e is not None}
                if not ests:
                    continue
                r = spread_stats(ests)
                if m in PRIMARY or m == HG:  # simultaneous intervals exist (primary: frozen; history increment: addition A)
                    mem = {s: block(per_seed[s], f, m, sim_hg=True)["members"].get(name, {}) for s in ests}
                    r["classes"] = {str(s): mem[s].get("class") for s in ests}
                    w = {str(s): mem[s]["sim_high"] - mem[s]["sim_low"] for s in ests if "sim_low" in mem[s]}
                    if len(w) == len(ests) >= 2:
                        lo, hi = min(w.values()), max(w.values())
                        r["sim_widths"] = w
                        r["spread_vs_widths"] = width_category(r["spread"], list(w.values()))
                        r["spread_over_narrowest_width"] = r["spread"] / lo if lo > 0 else None
                        r["spread_over_widest_width"] = r["spread"] / hi if hi > 0 else None
                out[f"{fkey(f)}|{m}|{name}"] = r
    return out


def levels_between_seed(levels_by_seed):
    out = {}
    for c in PANEL_CONFIGS:
        k = BI.ckey(c)
        for m in METRICS:
            ests = {int(s): (lv.get(k) or {}).get(m, {}).get("est") for s, lv in levels_by_seed.items()}
            ests = {s: e for s, e in ests.items() if e is not None}
            if ests:
                out[f"{k}|{m}"] = spread_stats(ests)
    return out


# ------------------------------------------------------------------------------------------------ coverage and QC
def coverage(rows, census, vals_by_seed, fams):
    """-> (aggregate coverage without child ids, private list of missing pairs)."""
    unit = defaultdict(lambda: {"registered": 0, "complete": 0, "per_child": Counter()})
    for r in rows:
        if not row_in_panel(r):
            continue
        k = f"{BI.ckey(config_of(r))}|{r['seed']}"
        unit[k]["registered"] += 1
        unit[k]["complete"] += int(census.status.get(r["experiment_id"]) == "complete")
        info = census.info.get(r["experiment_id"])
        if info is not None:
            for ch in info["children"]:
                unit[k]["per_child"][ch] += 1
    units = {k: {"registered": v["registered"], "complete": v["complete"], "children": len(v["per_child"]),
                 "units_per_child": {str(n): c for n, c in sorted(Counter(v["per_child"].values()).items())}} for k, v in sorted(unit.items())}
    expected = set()
    for vals in vals_by_seed.values():
        for c, per in vals.items():
            if c in PANEL_SET:
                expected |= set(per)
    fam_cov, missing = {}, []
    for f in fams:
        for m in METRICS:
            pres = {name: {s: set(BI.member_values(vals_by_seed[s], ref, cand, m)) for s in vals_by_seed} for name, ref, cand, _ in f["members"]}
            per_seed_common = {str(s): len(set.intersection(*[pres[n][s] for n in pres])) for s in vals_by_seed}
            any_seed = set.intersection(*[set().union(*pres[n].values()) for n in pres])
            all_seeds = set.intersection(*[set.intersection(*pres[n].values()) for n in pres])
            miss = sorted((s, i, n) for n in pres for s in vals_by_seed for i in expected - pres[n][s])
            missing += [{"family": fkey(f), "metric": m, "member": n, "seed": s, "child": i} for s, i, n in miss]
            fam_cov[f"{fkey(f)}|{m}"] = {"expected_children": len(expected), "per_seed_common": per_seed_common, "seed_mean_common": len(any_seed),
                                         "all_three_seeds": len(all_seeds), "n_missing_pairs": len(miss)}
    lev = {BI.ckey(c): {str(s): len(vals_by_seed[s].get(c, {})) for s in vals_by_seed} for c in PANEL_CONFIGS}
    miss_count = Counter((x["family"], x["metric"], x["member"], x["seed"]) for x in missing)
    return ({"units": units, "families": fam_cov, "levels_children": lev, "expected_children": len(expected), "n_missing_pairs": len(missing),
             "missing_pairs_by_member_seed": {f"{a}|{b}|{c}|{d}": v for (a, b, c, d), v in sorted(miss_count.items())}, "any_incomplete": bool(missing)},
            missing)


def qc(rows, census, triples, grp_by_seed):
    byid = {r["experiment_id"]: r for r in rows}
    bad = defaultdict(list); n = Counter()
    reg_ids = {e for t in triples.values() for e in t.values()}
    for r in rows:
        if row_in_panel(r):
            n["panel_and_counterpart_rows"] += 1
            if r["experiment_id"] not in reg_ids:
                bad["row_not_in_registry"].append(r["experiment_id"])
    for cano, t in sorted(triples.items()):
        if set(t) != set(SEEDS):
            bad["registry_cell_without_three_seeds"].append(cano[:16]); continue
        n["registry_cells"] += 1
        r0, i0 = byid.get(t[SEEDS[0]]), census.info.get(t[SEEDS[0]])
        for s in SEEDS[1:]:
            r, i = byid.get(t[s]), census.info.get(t[s])
            if r is None or r0 is None:
                bad["registry_id_not_in_rows"].append(cano[:16]); continue
            n["panel_rows_checked_against_3401"] += 1
            if any(r[k] != r0[k] for k in ("family_id", "dataset", "subject_fold", "content_fold")) or r["spec"] != r0["spec"]:
                bad["spec_or_fold_differs_from_3401"].append(r["experiment_id"])
            if r.get("reference_3401_id") is not None:
                n["reference_3401_id_links"] += 1
                if r["reference_3401_id"] != r0["experiment_id"]:
                    bad["reference_3401_id_differs_from_registry"].append(r["experiment_id"])
            if i is None or i0 is None:
                bad["record_not_complete"].append(r["experiment_id"]); continue
            if i["children"] != i0["children"]:
                bad["children_or_trial_counts_differ_from_3401"].append(r["experiment_id"])
    for eid, i in sorted(census.info.items()):
        n["panel_records"] += 1
        r = byid[eid]
        if i["record_seed"] != r["seed"] or i["bound_seed"] != r["seed"]:
            bad["record_seed_differs_from_row"].append(eid)
        if not i["record_spec_equals_row"]:
            bad["record_spec_differs_from_row"].append(eid)
        if not i["endpoint_fields_present"]:
            bad["endpoint_field_missing"].append(eid)
        if any(a != b for a, b in i["children"].values()):
            bad["trial_counts_differ_between_record_tables"].append(eid)
    cells = defaultdict(dict)
    for eid, i in census.info.items():
        cells[(i["seed"], tuple(i["fold"]))][i["config"]] = i
    ncal = {}
    for k, d in sorted(cells.items()):
        n["fold_cells"] += 1
        ref = next(iter(d.values()))["children"]
        if any(i["children"] != ref for i in d.values()):
            bad["children_or_trial_counts_differ_across_configurations"].append(f"{k[0]}|{k[1][0]}|{k[1][1]}")
        if len(d) != len(PANEL_CONFIGS):
            bad["fold_cell_configuration_missing"].append(f"{k[0]}|{k[1][0]}|{k[1][1]}")
        ncal[f"{k[0]}|{k[1][0]}|{k[1][1]}"] = sorted({str(i["n_calibration_trials"]) for i in d.values()})
    desc, hashes = defaultdict(set), defaultdict(Counter)
    for eid, i in census.info.items():
        fs = f"{i['family']}|{i['seed']}"
        hashes[fs][i["code_hash"]] += 1
        desc[fs].add((EQUIVALENT_HASHES.get(i["code_hash"], i["code_hash"]), i["code_group"], i["target_contract"], i["stratum"], i["selection_rule"],
                      i["calibration_set"], i["head_fit"]))
    by_family = defaultdict(set)
    for fs, v in desc.items():
        by_family[fs.split("|")[0]] |= v
    donors = Counter()
    for eid, i in sorted(census.info.items()):
        if i["family"] != "E_PUBLIC_TRANSFER":
            continue
        r = byid[eid]
        did = os.path.basename(i["donor"] or "").replace("_best.pt", "")
        d = byid.get(did)
        ok = (d is not None and d["family_id"] == "A_LOCAL" and d["dataset"] == "fau" and (d["subject_fold"], d["content_fold"]) == (0, 0)
              and d["seed"] == r["seed"] and d["spec"].get("objective") == r["spec"].get("objective")
              and d["spec"].get("architecture") == "lag_local_tokens" and d["spec"].get("window") == "full")
        donors[f"{r['seed']}|{'same_seed_same_objective_fau_lag_local_full' if ok else 'mismatch'}"] += 1
        if not ok:
            bad["donor_not_the_same_seed_fau_local_unit"].append(eid)
        donors[f"{r['seed']}|checkpoint_present_{bool(i['donor']) and os.path.exists(os.path.join(core.REPO, i['donor']))}"] += 1
    groups = defaultdict(set)
    for i in census.info.values():
        for c, g in i["groups"].items():
            groups[c].add(g)
    for g in grp_by_seed.values():
        for c, v in g.items():
            groups[c].add(v)
    return {"counts": dict(n), "failures": {k: v for k, v in bad.items()},
            "children_and_trial_counts_equal_across_configurations_and_seeds": not bad.get("children_or_trial_counts_differ_across_configurations")
            and not bad.get("children_or_trial_counts_differ_from_3401"),
            "n_calibration_trials_per_fold_cell": ncal,
            "code_hash_counts": {k: dict(v) for k, v in sorted(hashes.items())},
            "equivalent_hashes": EQUIVALENT_HASHES,
            "descriptors_per_family": {k: sorted(map(list, v)) for k, v in sorted(by_family.items())},
            "one_descriptor_set_per_family_across_seeds": all(len(v) == 1 for v in by_family.values()),
            "donors": dict(sorted(donors.items())),
            "group_label_consistent": all(len(v) == 1 for v in groups.values()), "n_children_with_group": len(groups)}


# ------------------------------------------------------------------------------------------------ reproduction of seed 3401
def compare_tree(a, b, path="", acc=None, tol=1e-12, one_sided=False):
    """number-by-number comparison of two JSON trees; one_sided: keys only in `a` are counted as added, not as mismatches."""
    acc = acc if acc is not None else {"n_numbers": 0, "n_other": 0, "max_abs_diff": 0.0, "mismatches": [], "n_added": 0}
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k in a and k not in b and one_sided:
                acc["n_added"] += 1
            elif k not in a or k not in b:
                acc["mismatches"].append(f"{path}/{k}: present on one side only")
            else:
                compare_tree(a[k], b[k], f"{path}/{k}", acc, tol, one_sided)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            acc["mismatches"].append(f"{path}: list lengths {len(a)} vs {len(b)}")
        for j, (x, y) in enumerate(zip(a, b)):
            compare_tree(x, y, f"{path}[{j}]", acc, tol, one_sided)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        acc["n_numbers"] += 1
        if not (np.isnan(a) and np.isnan(b)):
            d = abs(float(a) - float(b)); acc["max_abs_diff"] = max(acc["max_abs_diff"], d)
            if d > tol:
                acc["mismatches"].append(f"{path}: {a} vs {b}")
    else:
        acc["n_other"] += 1
        if a != b:
            acc["mismatches"].append(f"{path}: {a!r} vs {b!r}")
    return acc


def _plain(x):
    return json.loads(json.dumps(BI.jl(x)))


def reproduce_3401(pdata_3401, published, per_seed_3401, levels_3401, fams):
    """(a) the full frozen aggregation (bc_interim.aggregate_private) at seed 3401 vs the published private_e.json, number by
    number; (b) panel-family pointwise values at 3401 vs the published values of the same members (same labels, draws and
    children), including addition A's pointwise numbers; (c) panel levels vs the published levels; (d) the published
    full-family simultaneous intervals of the panel members."""
    mine = _plain(BI.aggregate_private(pdata_3401))
    full = compare_tree(mine, {k: v for k, v in published.items() if k != "meta"})
    full["mismatches"] = full["mismatches"][:20]; full.pop("n_added", None)
    pm = {"n_member_blocks": 0, "max_abs_diff": 0.0, "mismatches": []}
    published_sim = {}
    keys = ("n", "est", "se", "ci_low", "ci_high", "pct_low", "pct_high")
    for f in fams:
        for m in METRICS:
            pb = (published["families"][plabel(f, m)] if m in PRIMARY else published["secondary"][fkey(f)][m])["members"]
            blocks = [("frozen", block(per_seed_3401, f, m)["members"])]
            if m == HG:
                blocks.append(("A", per_seed_3401["hist_gain_simultaneous"][fkey(f)]["members"]))
            for tag, mb in blocks:
                for name, *_ in f["members"]:
                    if name not in pb or name not in mb:
                        pm["mismatches"].append(f"{fkey(f)}|{m}|{name}|{tag}: present on one side only"); continue
                    pm["n_member_blocks"] += 1
                    for k in keys:
                        if k in pb[name] or k in mb[name]:
                            d = abs(float(pb[name].get(k, np.nan)) - float(mb[name].get(k, np.nan)))
                            pm["max_abs_diff"] = max(pm["max_abs_diff"], d if np.isfinite(d) else np.inf)
                            if not d <= 1e-12:
                                pm["mismatches"].append(f"{fkey(f)}|{m}|{name}|{tag}|{k}")
            if m in PRIMARY:
                fam_pub = published["families"][plabel(f, m)]
                for name, *_ in f["members"]:
                    x = fam_pub["members"].get(name, {})
                    if "sim_low" in x:
                        published_sim[f"{plabel(f, m)}|{name}"] = {"sim_low": x["sim_low"], "sim_high": x["sim_high"], "class": x.get("class"),
                                                                   "crit": fam_pub.get("crit"), "n_members_frozen": f["n_members_frozen"]}
    lv = {"n_numbers": 0, "max_abs_diff": 0.0, "mismatches": [], "n_configurations": 0}
    for c in PANEL_CONFIGS:
        k = BI.ckey(c)
        a, b = levels_3401.get(k), published["levels"].get(k)
        if a is None or b is None:
            lv["mismatches"].append(f"{k}: present on one side only"); continue
        lv["n_configurations"] += 1
        acc = compare_tree(_plain({x: y for x, y in a.items() if x != "hist_gain_ci"}), b)
        lv["n_numbers"] += acc["n_numbers"]; lv["max_abs_diff"] = max(lv["max_abs_diff"], acc["max_abs_diff"])
        lv["mismatches"] += [f"{k}{x}" for x in acc["mismatches"]]
    pm["mismatches"] = pm["mismatches"][:20]; lv["mismatches"] = lv["mismatches"][:20]
    return {"full_aggregation_vs_published": full, "panel_members_pointwise_vs_published": pm, "panel_levels_vs_published": lv,
            "published_full_family_simultaneous": published_sim}


def non_panel_published(published, fams):
    """published seed-3401 values of the non-panel members of the panel families (they have no seed panel)."""
    out = {}
    for f in fams:
        for m in PRIMARY:
            fam = published["families"].get(plabel(f, m), {})
            for name in f["non_panel_members"]:
                x = fam.get("members", {}).get(name)
                if x:
                    out[f"{plabel(f, m)}|{name}"] = {k: x.get(k) for k in ("est", "ci_low", "ci_high", "sim_low", "sim_high", "class", "tag", "n")}
    whole = sorted({v.get("family") for v in published["families"].values()} - {f["family"] for f in fams})
    return {"members": out, "whole_families_not_in_panel": whole}


# ------------------------------------------------------------------------------------------------ Monte-Carlo stability (addition D)
def _primary_cells(fams, vals, sink, only=None):
    out = {}
    for f in fams:
        for m in PRIMARY:
            r = BI.run_family(plabel(f, m), f["members"], vals, m, sink, True, None)
            for name, mm in r.get("members", {}).items():
                if "class" in mm and (only is None or name in only.get(plabel(f, m), ())):
                    out[f"{plabel(f, m)}|{name}"] = (mm["sim_low"], mm["sim_high"], mm["class"], r.get("crit"))
    return out


def mc_stability(fams, vals_by_seed, full_vals_3401=None, k=MC_K, step=MC_STEP):
    """every primary simultaneous interval re-computed with k alternative bootstrap draw sets (stats.SEED + step * j, j = 1..k; same
    children, estimates, families, B). Cells: panel families per seed and for the identity mean; the full frozen families at
    seed 3401 (all seed-3401 configurations in `full_vals_3401`; panel members only). The declared draw (j = 0) stays the reported
    result."""
    full = full_families_with_panel_members()
    only = {plabel(f, m): set(f["panel_members"]) for f in full for m in PRIMARY}
    pv, sfams, _ = seed_mean_inputs(fams, vals_by_seed)

    def one(offset):
        sink, r = [], {}
        with draw_scope(offset):
            for s in vals_by_seed:
                r[("panel", str(s))] = _primary_cells(fams, vals_by_seed[s], sink)
            r[("panel", "mean")] = _primary_cells(sfams, pv, sink)
            if full_vals_3401:
                r[("full_frozen", str(SEEDS[0]))] = _primary_cells(full, full_vals_3401, sink, only)
        return r

    declared = one(0)
    alts = [one(step * j) for j in range(1, k + 1)]
    cells = {}
    for key, cs in declared.items():
        g, blk = key
        for cell, (lo, hi, c, crit) in cs.items():
            al = [a[key][cell] for a in alts if cell in a.get(key, {})]
            cl = Counter(x[2] for x in al)
            rng = lambda j: [min(x[j] for x in al), max(x[j] for x in al)] if al else None
            cells.setdefault(g, {}).setdefault(blk, {})[cell] = {
                "declared": {"sim_low": lo, "sim_high": hi, "class": c, "crit": crit}, "n_alternatives": len(al), "n_same_class": int(cl.get(c, 0)),
                "classes": dict(sorted(cl.items())), "sim_low_range": rng(0), "sim_high_range": rng(1), "crit_range": rng(3)}
    return {"k": k, "seed_step": step, "base_seed": S.SEED, "cells": cells}


def mc_checks(out):
    """the declared (j = 0) cells of the Monte-Carlo table must equal the main results and the published full families."""
    mc = out["mc_stability"]["cells"]; n, d, bad = 0, 0.0, []

    def cmp(tag, cell, ref):
        nonlocal n, d
        for k in ("sim_low", "sim_high"):
            n += 1; d = max(d, abs(cell["declared"][k] - ref[k]))
        if cell["declared"]["class"] != ref.get("class"):
            bad.append(tag)
    for blk, cs in mc.get("panel", {}).items():
        res = out["seed_mean"] if blk == "mean" else out["per_seed"][blk]
        for key, cell in cs.items():
            label, name = key.rsplit("|", 1)
            cmp(f"panel|{blk}|{key}", cell, res["families"][label]["members"][name])
    n_pub = 0
    rep = out.get("reproduction_3401")
    if rep:
        for blk, cs in mc.get("full_frozen", {}).items():
            for key, cell in cs.items():
                ref = rep["published_full_family_simultaneous"].get(key)
                if ref is not None:
                    n_pub += 1; cmp(f"full_frozen|{blk}|{key}", cell, ref)
    return {"n_numbers": n, "max_abs_diff": d, "class_mismatches": bad, "full_family_cells_checked_against_published": n_pub}


# ------------------------------------------------------------------------------------------------ analysis
def _sanitize(notes):
    return [re.sub(r"child\w*", "<child>", x) for x in notes]


def analyse(rows, load, published=None, mc_k=MC_K, triples=None):
    notes = []
    census = Census(load, rows)
    pdata, vals_by_seed, grp_by_seed, loader_status = {}, {}, {}, {}
    for s in SEEDS:
        pdata[s] = load_seed(rows, census, s)
        vals_by_seed[s] = {c: pdata[s]["vals"][c] for c in PANEL_CONFIGS if c in pdata[s]["vals"]}
        grp_by_seed[s] = dict(pdata[s]["grp"])
        loader_status[str(s)] = {f"{k[0]}|{k[1]}": v for k, v in sorted(pdata[s]["status"].items())}
    fams = panel_families()
    grp = {}
    for s in SEEDS:
        grp.update(grp_by_seed[s])
    per_seed = {s: run_block(fams, vals_by_seed[s], grp_by_seed[s], notes) for s in SEEDS}
    seed_mean = run_seed_mean(fams, vals_by_seed, grp, notes)
    levels = {str(s): panel_levels(vals_by_seed[s], grp_by_seed[s], notes) for s in SEEDS}
    mvals, mseeds = seed_mean_values(vals_by_seed)
    levels["mean"] = panel_levels(mvals, grp, notes)
    for c, ns in mseeds.items():
        if BI.ckey(c) in levels["mean"]:
            levels["mean"][BI.ckey(c)]["children_by_n_seeds"] = {str(k): v for k, v in sorted(Counter(ns.values()).items())}
    cov, missing = coverage(rows, census, vals_by_seed, fams)
    complete_case = run_seed_mean(fams, vals_by_seed, grp, notes, complete_case=True) if cov["any_incomplete"] else None
    status = Counter()
    for r in rows:
        if row_in_panel(r):
            if r["experiment_id"] not in census.status:
                census(r["experiment_id"])
            status[f"{r['family_id']}|{r['seed']}|{census.status[r['experiment_id']]}"] += 1
    triples = registry_triples() if triples is None else triples
    panel_children = sorted({c for vals in vals_by_seed.values() for per in vals.values() for c in per})
    ul = unit_levels(census, vals_by_seed)
    out = {
        "panel": {"configurations": [BI.ckey(c) for c in PANEL_CONFIGS], "families": fams_json(fams),
                  "full_families_with_panel_members": [{"family": f["family"], "scope": f["scope"], "n_members": len(f["members"]), "panel_members": f["panel_members"]}
                                                       for f in full_families_with_panel_members()]},
        "status": dict(sorted(status.items())), "loader_status": loader_status,
        "children": {"n": len(panel_children), "groups": dict(sorted(Counter(grp.get(c) for c in panel_children).items(), key=lambda kv: str(kv[0])))},
        "per_seed": {str(s): per_seed[s] for s in SEEDS}, "seed_mean": seed_mean, "seed_mean_complete_case": complete_case,
        "levels": levels, "between_seed": between_seed(per_seed, fams), "levels_between_seed": levels_between_seed({str(s): levels[str(s)] for s in SEEDS}),
        "coverage": cov, "qc": qc(rows, census, triples, grp_by_seed),
        "reproduction_3401": reproduce_3401(pdata[SEEDS[0]], published, per_seed[SEEDS[0]], levels[str(SEEDS[0])], fams) if published else None,
        "non_panel_published_3401": non_panel_published(published, fams) if published else None,
        "mc_stability": mc_stability(fams, vals_by_seed, pdata[SEEDS[0]]["vals"], mc_k) if mc_k else None,
        "unit_levels": ul, "unit_nll_excess": unit_nll_excess(ul), "recipes": recipes(census),
        "notes": _sanitize(notes)}
    if out["mc_stability"]:
        out["mc_stability"]["checks"] = mc_checks(out)
    ntr = defaultdict(set)
    for i in census.info.values():
        for c, (a, _) in i["children"].items():
            ntr[c].add(a)
    per_identity = {
        "scope": "private; child pseudonyms with group and trial counts, scores; no name, no identity map",
        "children": {c: {"group": grp.get(c), "n_trials": (sorted(ntr[c])[0] if len(ntr[c]) == 1 else sorted(ntr[c]))} for c in panel_children},
        "per_seed_values": {str(s): {BI.ckey(c): vals_by_seed[s][c] for c in PANEL_CONFIGS if c in vals_by_seed[s]} for s in SEEDS},
        "per_seed_deltas": {}, "seed_mean_deltas": {},
        "seed_mean_levels": {BI.ckey(c): v for c, v in mvals.items()},
        "missing_pairs": missing}
    for f in fams:
        for name, ref, cand, _ in f["members"]:
            for m in METRICS:
                key = f"{fkey(f)}|{m}|{name}"
                per_identity["per_seed_deltas"][key] = {str(s): BI.member_values(vals_by_seed[s], ref, cand, m) for s in SEEDS}
                per_identity["seed_mean_deltas"][key] = {i: list(v) for i, v in seed_mean_deltas(vals_by_seed, ref, cand, m).items()}
    return out, per_identity, census


# ------------------------------------------------------------------------------------------------ report
def fx(x, m):
    return "–" if x is None else f"{x:+.{DEC[m]}f}"


def ivx(d, m, lo="ci_low", hi="ci_high"):
    return "–" if not d or lo not in d else f"[{d[lo]:+.{DEC[m]}f}, {d[hi]:+.{DEC[m]}f}]"


def lab(label):
    return label.replace("|", " · ")


def _member(res, f, m, name, sim_hg=False):
    return block(res, f, m, sim_hg)["members"].get(name, {})


def _ns(out, f, m, name):
    ns = [_member(out["per_seed"][str(s)], f, m, name).get("n") for s in SEEDS]
    nm = _member(out["seed_mean"], f, m, name).get("n")
    return (f"{ns[0]}" if len(set(ns)) == 1 else "/".join(map(str, ns))) + ("" if nm == ns[0] and len(set(ns)) == 1 else f" → {nm}")


def _range(b, m):
    if not b:
        return "–"
    sd = "–" if b.get("sd") is None else f"{b['sd']:.{DEC[m]}f}"
    return f"[{b['min']:+.{DEC[m]}f}, {b['max']:+.{DEC[m]}f}] ({b['spread']:.{DEC[m]}f}) · {sd}"


def primary_table(out, fams, family, m):
    L = [f"| family · member | tag | n | seed 3401 Δ [sim.] | seed 3407 Δ [sim.] | seed 3413 Δ [sim.] | between-seed range (spread) · SD | identity mean Δ [95% CI] | identity mean [sim.] · class |",
         "|---|---|---|---|---|---|---|---|---|"]
    crit = []
    for f in fams:
        if f["family"] != family:
            continue
        crit.append(f"{lab(plabel(f, m))}: " + " / ".join(f"{out['per_seed'][str(s)]['families'][plabel(f, m)].get('crit', float('nan')):.2f}" for s in SEEDS)
                    + f" / mean {out['seed_mean']['families'][plabel(f, m)].get('crit', float('nan')):.2f}")
        for name, *_ in f["members"]:
            cells = []
            for s in SEEDS:
                x = _member(out["per_seed"][str(s)], f, m, name)
                cells.append("missing" if "est" not in x else f"{fx(x['est'], m)} {ivx(x, m, 'sim_low', 'sim_high')} {x.get('class', '')}")
            b = out["between_seed"].get(f"{fkey(f)}|{m}|{name}")
            sm = _member(out["seed_mean"], f, m, name)
            tag = "recipe (C01)" if sm.get("tag") == CORRECTED_TAG else sm.get("tag", "")
            L.append(f"| {lab(plabel(f, m))} · {name} | {tag} | {_ns(out, f, m, name)} | " + " | ".join(cells) + f" | {_range(b, m)} | "
                     f"{fx(sm.get('est'), m)} {ivx(sm, m)} | {ivx(sm, m, 'sim_low', 'sim_high')} {sm.get('class', '')} |")
    L += ["", "Critical values (3401 / 3407 / 3413 / identity mean): " + "; ".join(crit) + ".", ""]
    return L


def secondary_table(out, fams, m, with_sim):
    head = "| family · member | n | seed 3401 Δ [95% CI] | seed 3407 Δ [95% CI] | seed 3413 Δ [95% CI] | between-seed range (spread) · SD | identity mean Δ [95% CI] |"
    sep = "|---|---|---|---|---|---|---|"
    if with_sim:
        head += " identity mean [sim., A] · class | per-seed [sim., A] classes 3401 / 3407 / 3413 |"
        sep += "---|---|"
    L = [head, sep]
    for fam in FAMILY_ORDER:
        for f in fams:
            if f["family"] != fam:
                continue
            for name, *_ in f["members"]:
                xs = [_member(out["per_seed"][str(s)], f, m, name) for s in SEEDS]
                b = out["between_seed"].get(f"{fkey(f)}|{m}|{name}")
                sm = _member(out["seed_mean"], f, m, name)
                row = (f"| {lab(fkey(f))} · {name} | {_ns(out, f, m, name)} | " + " | ".join("–" if "est" not in x else f"{fx(x['est'], m)} {ivx(x, m)}" for x in xs)
                       + f" | {_range(b, m)} | {fx(sm.get('est'), m)} {ivx(sm, m)} |")
                if with_sim:
                    sa = _member(out["seed_mean"], f, m, name, sim_hg=True)
                    cl = [_member(out["per_seed"][str(s)], f, m, name, sim_hg=True).get("class", "–") for s in SEEDS]
                    row += f" {ivx(sa, m, 'sim_low', 'sim_high')} {sa.get('class', '')} | {' / '.join(cl)} |"
                L.append(row)
    L.append("")
    if with_sim:
        crit = []
        for f in fams:
            crit.append(f"{lab(fkey(f))}: " + " / ".join(f"{out['per_seed'][str(s)]['hist_gain_simultaneous'][fkey(f)].get('crit', float('nan')):.2f}" for s in SEEDS)
                        + f" / mean {out['seed_mean']['hist_gain_simultaneous'][fkey(f)].get('crit', float('nan')):.2f}")
        L += ["Addition A critical values (3401 / 3407 / 3413 / identity mean): " + "; ".join(crit) + ".", ""]
    return L


def level_table(out, m):
    with_ci = m in PRIMARY or m == HG
    L = ["| configuration | n | seed 3401 | seed 3407 | seed 3413 | between-seed range (spread) · SD | identity mean over seeds | HA / NH (identity mean) |",
         "|---|---|---|---|---|---|---|---|"]
    for c in PANEL_CONFIGS:
        k = BI.ckey(c)
        def cell(lv):
            x = (lv.get(k) or {})
            d = x.get("hist_gain_ci") if m == HG else x.get(m)
            if not d or "est" not in d:
                return "–"
            return f"{d['est']:.{DEC[m]}f}" + (f" [{d['ci_low']:.{DEC[m]}f}, {d['ci_high']:.{DEC[m]}f}]" if with_ci and "ci_low" in d else "")
        ns = [str((out["levels"][str(s)].get(k) or {}).get("n", "–")) for s in SEEDS]
        nm = (out["levels"]["mean"].get(k) or {}).get("n", "–")
        b = out["levels_between_seed"].get(f"{k}|{m}")
        mm = out["levels"]["mean"].get(k) or {}
        gd = (mm.get("hist_gain_ci") if m == HG else mm.get(m)) or {}
        gs = " / ".join((f"{x['est']:.{DEC[m]}f}" if "est" in x else f"n={x['n']}") for _, x in sorted((gd.get("groups") or {}).items())) or "–"
        rng = "–" if not b else f"[{b['min']:.{DEC[m]}f}, {b['max']:.{DEC[m]}f}] ({b['spread']:.{DEC[m]}f}) · " + ("–" if b.get("sd") is None else f"{b['sd']:.{DEC[m]}f}")
        L.append(f"| {lab(k)} | {ns[0] if len(set(ns)) == 1 else '/'.join(ns)}{'' if str(nm) == ns[0] else f' → {nm}'} | "
                 + " | ".join(cell(out["levels"][str(s)]) for s in SEEDS) + f" | {rng} | {cell(out['levels']['mean'])} | {gs} |")
    L.append("")
    return L


def group_table(out, fams):
    L = ["| family · member | endpoint | HA: identity mean Δ [95% CI] (n) | NH: identity mean Δ [95% CI] (n) |", "|---|---|---|---|"]
    for fam in FAMILY_ORDER:
        for f in fams:
            if f["family"] != fam:
                continue
            for name, *_ in f["members"]:
                for m in PRIMARY + (HG,):
                    gs = _member(out["seed_mean"], f, m, name).get("groups", {})
                    cells = []
                    for g in ("HA", "NH"):
                        x = gs.get(g)
                        cells.append("–" if not x else (f"{fx(x['est'], m)} {ivx(x, m)} (n={x['n']})" if "est" in x else f"n={x['n']}"))
                    L.append(f"| {lab(fkey(f))} · {name} | {NAME[m]} | " + " | ".join(cells) + " |")
    L.append("")
    return L


CAT_LABEL = {"below_every_width": "below every width", "between": "between", "above_every_width": "above every width"}


def width_tables(out, fams):
    L = ["Spread = max − min of the three per-seed estimates. Widths = sim_high − sim_low of each seed's simultaneous interval (declared draws; "
         "for the history increment the addition-A intervals). One rule for every family: *below every width* = spread smaller than the narrowest "
         "of the three widths; *above every width* = spread larger than the widest; otherwise *between*.", "",
         "| family · endpoint | members | below every width | between | above every width |", "|---|---|---|---|---|"]
    rows = []
    for fam in FAMILY_ORDER:
        for m in PRIMARY + (HG,):
            c, nm = Counter(), 0
            for f in fams:
                if f["family"] != fam:
                    continue
                for name, *_ in f["members"]:
                    b = out["between_seed"].get(f"{fkey(f)}|{m}|{name}", {})
                    nm += 1; c[b.get("spread_vs_widths", "not computed")] += 1
                    rows.append((f, m, name, b))
            if nm:
                L.append(f"| {fam} · {NAME[m]} | {nm} | {c['below_every_width']} | {c['between']} | {c['above_every_width']} |")
    L += ["", "| family · member · endpoint | spread | widths 3401 / 3407 / 3413 | spread ÷ narrowest width | spread ÷ widest width | category |", "|---|---|---|---|---|---|"]
    for f, m, name, b in rows:
        if "sim_widths" not in b:
            L.append(f"| {lab(fkey(f))} · {name} · {NAME[m]} | – | – | – | – | not computed |"); continue
        w = b["sim_widths"]
        L.append(f"| {lab(fkey(f))} · {name} · {NAME[m]} | {b['spread']:.{DEC[m] + 1}f} | " + " / ".join(f"{w[str(s)]:.{DEC[m] + 1}f}" for s in SEEDS if str(s) in w)
                 + " | " + " | ".join("–" if x is None else f"{x:.2f}" for x in (b["spread_over_narrowest_width"], b["spread_over_widest_width"]))
                 + f" | {CAT_LABEL[b['spread_vs_widths']]} |")
    L.append("")
    return L


def mc_tables(out):
    mc = out.get("mc_stability")
    if not mc:
        return ["Not computed in this run.", ""]
    k = mc["k"]
    L = [f"Every class in this document is that of the declared draws (B = 4,000 replicate index sets derived from the family label, the metric "
         f"and `sci_r1.stats.SEED` = {mc['base_seed']}). Here the same children, estimates and families were re-run with {k} alternative draw "
         f"sets (`SEED` + {mc['seed_step']}·j, j = 1…{k}). The declared class stays the reported one; this only shows how close each class is to "
         f"the Monte-Carlo margin. Checks: the declared cells of this table equal the main results and the published full families "
         f"({mc['checks']['n_numbers']} bounds, max |Δ| {mc['checks']['max_abs_diff']:.1e}, {len(mc['checks']['class_mismatches'])} class "
         f"mismatches; {mc['checks']['full_family_cells_checked_against_published']} published full-family cells).", ""]
    names = {"panel": "Panel families (per seed and identity mean; NLL and AUC)", "full_frozen": "Full frozen families at seed 3401 (panel members only)"}
    for g in ("panel", "full_frozen"):
        blocks = mc["cells"].get(g, {})
        cells = [(blk, key, c) for blk, cs in blocks.items() for key, c in cs.items()]
        unstable = [(blk, key, c) for blk, key, c in cells if c["n_same_class"] < c["n_alternatives"]]
        L.append(f"**{names[g]}.** {len(cells) - len(unstable)} of {len(cells)} cells keep the declared class in all {k} alternative draws; "
                 + ("the others are listed." if unstable else "none differs."))
        L.append("")
        if unstable:
            L += ["| block | family · member | declared [sim.] · class | alternative draws with the declared class | classes over the alternatives | sim_low range | sim_high range |",
                  "|---|---|---|---|---|---|---|"]
            for blk, key, c in unstable:
                d = c["declared"]
                m = key.rsplit("|", 1)[0].rsplit("|", 1)[1]
                L.append(f"| {'identity mean' if blk == 'mean' else 'seed ' + blk} | {lab(key)} | [{d['sim_low']:+.{DEC[m] + 1}f}, {d['sim_high']:+.{DEC[m] + 1}f}] {d['class']} | "
                         f"{c['n_same_class']} / {c['n_alternatives']} | " + "; ".join(f"{a}: {b}" for a, b in c["classes"].items())
                         + f" | [{c['sim_low_range'][0]:+.{DEC[m] + 1}f}, {c['sim_low_range'][1]:+.{DEC[m] + 1}f}] | [{c['sim_high_range'][0]:+.{DEC[m] + 1}f}, {c['sim_high_range'][1]:+.{DEC[m] + 1}f}] |")
            L.append("")
    return L


def crit_comparison(out, rep, fams):
    """v3: seed-3401 critical values of the panel families against the published full frozen families (range over scopes and endpoints),
    the member counts, whether every panel value is at or below its full-family value, and the direction of the class differences."""
    s0 = str(SEEDS[0])
    by = defaultdict(lambda: {"panel": [], "full": [], "n_panel": set(), "n_full": set()})
    le, moves = True, Counter()
    nmem = {plabel(f, m): len(f["members"]) for f in fams for m in PRIMARY}
    for k, v in rep["published_full_family_simultaneous"].items():
        label, name = k.rsplit("|", 1)
        fam = label.split("|")[0]
        pc = out["per_seed"][s0]["families"][label].get("crit")
        b = by[fam]
        b["panel"].append(pc); b["full"].append(v["crit"]); b["n_panel"].add(nmem.get(label)); b["n_full"].add(v["n_members_frozen"])
        le = le and pc <= v["crit"] + 1e-12
        x = out["per_seed"][s0]["families"][label]["members"].get(name, {})
        if x.get("class") != v["class"]:
            moves[f"{v['class']} → {x.get('class')}"] += 1
    rng = lambda x: f"{min(x):.2f}–{max(x):.2f}"
    one = lambda s: next(iter(s)) if len(s) == 1 else "/".join(map(str, sorted(s)))
    parts = [f"{fam} {rng(b['panel'])} ({one(b['n_panel'])} of {one(b['n_full'])} members per scope) against {rng(b['full'])}" for fam, b in by.items()]
    single = [fam for fam, b in by.items() if b["n_panel"] == {1}]
    return [f"Critical values at seed 3401 (max-t, range over the scopes and endpoints of each family), panel family against the published full "
            f"frozen family: {'; '.join(parts)}. Every panel critical value is at or below its full-family value: {le}. "
            + (f"The {', '.join(single)} panel families have a single member, so their simultaneous interval is the pointwise one and carries no "
               "multiplicity control. " if single else "")
            + "With the same estimates, standard errors and replicate indices, a lower critical value can only narrow an interval, so the restriction "
              "can turn 'contains 0' into a resolved class but not the reverse. Seed-3401 class differences by direction: "
            + (", ".join(f"{k}: {v}" for k, v in sorted(moves.items())) if moves else "none") + ".", ""]


def _versions_txt(meta):
    """number-by-number comparison with each archived earlier version (v3: both archives; exact wording of added fields and blocks)."""
    vc = meta.get("version_comparisons") or {}
    if not vc:
        return "not compared (no archive of an earlier version)"
    parts = []
    for name, v in vc.items():
        j, p = v["json"], v["per_identity"]
        new = v["new_top_level_keys"]
        parts.append(f"{name} (archived in `{v['archive']}`): JSON {j['n_numbers']} numbers in the {v['n_compared_blocks']} top-level blocks it has, "
                     f"max |Δ| {j['max_abs_diff']:.1e}, {len(j['mismatches'])} mismatches, {j['n_added']} fields added inside those blocks; new "
                     f"top-level blocks: {', '.join(f'`{k}`' for k in new) if new else 'none'}"
                     + (f"; top-level blocks MISSING here: {', '.join(v['missing_top_level_keys'])}" if v.get("missing_top_level_keys") else "")
                     + f"; per-identity file {p['n_numbers']} numbers, max |Δ| "
                     f"{p['max_abs_diff']:.1e}, {len(p['mismatches'])} mismatches, {p['n_added']} fields added")
    return "compared number by number with " + "; with ".join(parts)


def unit_table(out):
    """addition F: per configuration and seed, the five unit values (subject folds 0-4) of NLL, AUC and calibrator slope; addition G (v3):
    the unit NLL excess over the reference median, with a summary of the excluded (E_GENERIC CS_SINGLE reve) configuration-seed cells."""
    ul = out.get("unit_levels") or {}
    g = out.get("unit_nll_excess") or {}
    exc = g.get("excess") or {}
    by = defaultdict(dict)
    for k, r in ul.items():
        by[(r["config"], r["seed"])][r["fold"][0]] = {**r, "excess": exc.get(k)}
    folds = sorted({f for d in by.values() for f in d})
    f4 = lambda x: "–" if x is None else f"{x:.4f}"
    s4 = lambda x: "–" if x is None else f"{x:+.4f}"
    f3_ = lambda x: "–" if x is None else f"{x:.3f}"
    fs = lambda x: "–" if x is None else f"{x:.3g}"
    L = [f"Unit = one trained record (configuration × seed × subject fold, 12–13 test children). Values are means over the unit's test children; "
         "the calibrator slope is the unit's training-side positive-affine fit (comparable only within a configuration). No intervals; every unit "
         f"of every panel configuration is listed (folds {', '.join(map(str, folds))} in order).", ""]
    if g:
        lo, hi = g["reference_excess_range"]
        L += [f"**NLL excess (post hoc addition G, version 3; declared in the note's correction 01 before it was computed; descriptive).** NLL excess = "
              "unit NLL − the median unit NLL of the 14 reference configurations in the same seed and subject fold (reference = every panel "
              "configuration except " + ", ".join(lab(c) for c in g["excluded_configurations"]) + f"; bits per trial). Over the {g['n_reference_units']} "
              f"reference units the excess lies in [{s4(lo)}, {s4(hi)}]. The excluded configurations, per seed:", "",
              "| configuration | seed | NLL level (§" + SECNO["levels"] + ") | unit NLL excess, folds " + " / ".join(map(str, folds))
              + f" | units above the largest reference excess ({s4(hi)}) |", "|---|---|---|---|---|"]
        for c in g["excluded_configurations"]:
            for s in SEEDS:
                b = g["by_configuration_seed"].get(f"{c}|{s}")
                if not b:
                    continue
                lv = ((out["levels"].get(str(s)) or {}).get(c) or {}).get("NLL", {}).get("est")
                L.append(f"| {lab(c)} | {s} | {f4(lv)} | " + " / ".join(s4(b["excess_by_subject_fold"].get(str(f))) for f in folds)
                         + f" | {b['n_above_reference_max']} of {b['n_units']} |")
        L.append("")
    L += ["| configuration | seed | unit NLL | NLL excess over the reference median (G) | unit AUC | calibrator slope |", "|---|---|---|---|---|---|"]
    order = {BI.ckey(c): j for j, c in enumerate(PANEL_CONFIGS)}
    for (cfg, s), d in sorted(by.items(), key=lambda kv: (order.get(kv[0][0], 99), kv[0][1])):
        L.append(f"| {lab(cfg)} | {s} | " + " / ".join(f4(d[f]["NLL"]) if f in d else "–" for f in folds) + " | "
                 + " / ".join(s4(d[f]["excess"]) if f in d else "–" for f in folds) + " | "
                 + " / ".join(f3_(d[f]["AUC"]) if f in d else "–" for f in folds) + " | "
                 + " / ".join(fs(d[f]["calibrator_slope"]) if f in d else "–" for f in folds) + " |")
    L.append("")
    return L


def _lr(x):
    return "–" if x is None else ("0" if x == 0 else f"{x:.0e}".replace("e-0", "e-").replace("e+0", "e+"))


def _int(x):
    return "–" if x is None else f"{x:,}"


def _layers(tl):
    """short form of a backbone contract's trainable_layers ('all', or a LoRA list ending in a '…<scope>' item)."""
    if tl is None:
        return "–"
    try:
        x = json.loads(tl) if isinstance(tl, str) and tl.startswith("[") else tl
    except ValueError:
        x = tl
    if isinstance(x, list) and x and all(isinstance(e, str) for e in x):
        rank = sorted({e.split(":")[0] for e in x if e.startswith("lora_")})
        scope = [e.lstrip("…").strip() for e in x if e.startswith("…")]
        if rank:
            return f"{'/'.join(r.replace('lora_r', 'LoRA r') for r in rank)} adapters ({scope[-1] if scope else 'listed modules'})"
        return ", ".join(x)
    return str(x)


def recipe_summary(out):
    """one sentence on random_full -> pretrained_full in the private records, built from the recipe block (the 'Contrasts' bullet)."""
    rc = (out.get("recipes") or {}).get("pe_generic_contrasts") or {}
    full = {k: v for k, v in rc.items() if k.endswith("|pretrained_full")}
    if not full or any(v is None for v in full.values()):
        return "the recipe descriptors are incomplete in the records (§" + SECNO["recipe"] + ")"
    ratios = [v["backbone_lr_ref_over_cand"] for v in full.values() if v["backbone_lr_ref_over_cand"]]
    if len(ratios) != len(full):
        return "the learning rates are not recorded for every scope (§" + SECNO["recipe"] + ")"
    head = sum(v["lr_head"][0] != v["lr_head"][1] for v in full.values())
    same_ep = all(v["epochs"][0] == v["epochs"][1] for v in full.values())
    all_bb = all(all(v["every_backbone_parameter_trained"]) for v in full.values())
    prefix = any(any(v["curve_open_groups"]) for v in full.values())
    lr_txt = (f"the backbone learning rate of pretrained_full is {min(ratios):.3g}× to {max(ratios):.3g}× lower than that of random_full" if min(ratios) > 1
              else f"the backbone learning-rate ratio random_full ÷ pretrained_full is {min(ratios):.3g} to {max(ratios):.3g}")
    return (f"in the private records {lr_txt} and the head learning rate differs in {head} of {len(full)} scopes; "
            + ("the epochs are the same; " if same_ep else "the epochs differ; ")
            + ("both arms train every backbone parameter from the start" if all_bb else "not every backbone parameter is trained in both arms")
            + ("" if not prefix else "; a progressive-prefix record is present") + " (§" + SECNO["recipe"] + ")")


def recipe_tables(out):
    """v3: training-recipe descriptors of the panel configurations, read from the records (descriptors, not results)."""
    rc = out.get("recipes") or {}
    cfgs = rc.get("configurations") or {}
    if not cfgs:
        return ["Not available in this run.", ""]
    L = [f"Read from every panel record ({rc['n_records']} records; units per seed in the table): `resolved_config` (learning rates, "
         "epochs, recipe file), the run-time learning rates, the backbone contract (trainable backbone parameters) and whether any training-curve "
         f"entry carries a progressive-prefix record (`open_groups`; {rc['n_records_with_open_groups']} records do). One descriptor set per configuration "
         f"across seeds and folds: {rc['one_descriptor_set_per_configuration']}. The E_GENERIC learning rates are the `chosen` pair of the ALN2 private "
         "recipe search named in each record (`auditory_alignment_v2.run_fm.lr_select`: candidates trained on one development cell, scored by the "
         "checkpoint-selection score on the training participants' early-stopping content; the chosen pair is fixed for every fold and seed). "
         "`local_train.fit_private_fm` (E_GENERIC) trains one backbone parameter group and one head group with AdamW (weight decay 1e-4) and cosine "
         "annealing over all steps: no progressive prefix, no layer-wise decay. For pretrained_peft the backbone learning rate applies to the LoRA "
         "adapter parameters.", "",
         "| configuration | units per seed 3401 / 3407 / 3413 | backbone lr | head lr | epochs | trainable backbone parameters / all | trainable layers | "
         "progressive-prefix record | record lr = recipe `chosen` (development cell, search epochs) |", "|---|---|---|---|---|---|---|---|---|"]
    others = []
    for c in PANEL_CONFIGS:
        k = BI.ckey(c)
        v = cfgs.get(k)
        if not v:
            continue
        ups = " / ".join(str(v["units_per_seed"].get(str(s), 0)) for s in SEEDS)
        if c[0] != "E_GENERIC":
            for d in v["descriptor_sets"]:
                others.append(f"{lab(k)} ({ups} units): " + (f"`resolved_config` optimizer {d['optimizer']}, lr {_lr(d['lr'])}, {d['epochs']} epochs"
                                                              if d["has_resolved_config"] else "no `resolved_config` recorded")
                              + f"; progressive-prefix record {'yes' if d['curve_open_groups'] else 'no'} ({d['n_units']} units)")
            continue
        for d in v["descriptor_sets"]:
            dev = d.get("recipe_dev_cell") or {}
            ch = "–" if d["lr_equals_recipe_chosen"] is None else ("yes" if d["lr_equals_recipe_chosen"] else "NO")
            extra = "" if v["n_descriptor_sets"] == 1 else f" ({d['n_units']} units in this set)"
            L.append(f"| {lab(k)} | {ups}{extra} | {_lr(d['lr_backbone'])} | "
                     f"{_lr(d['lr_head'])} | {d['epochs']} | {_int(d['n_trainable_backbone'])} / {_int(d['n_params'])} | {_layers(d.get('trainable_layers'))} | "
                     f"{'yes' if d['curve_open_groups'] else 'no'} | {ch}"
                     + (f" (fold {dev.get('subject_fold')} / {dev.get('content_fold')}, seed {dev.get('seed')}; {d.get('recipe_search_epochs')} epochs)" if dev else "")
                     + " |")
    L.append("")
    if others:
        L += ["Other panel configurations: " + "; ".join(others) + ".", ""]
    L += ["PE-GENERIC recipe differences (random_full → candidate; ratio = random_full backbone lr ÷ candidate backbone lr, formed for pretrained_full only):", "",
          "| scope · member | backbone lr | ratio | head lr | epochs | trainable backbone parameters | every backbone parameter trained |", "|---|---|---|---|---|---|---|"]
    for key, v in (rc.get("pe_generic_contrasts") or {}).items():
        sc, name = key.split("|", 1)[1].rsplit("|", 1)
        if v is None:
            L.append(f"| {lab(sc)} · {name} | – | – | – | – | – | descriptors not unique |"); continue
        ratio = f"{v['backbone_lr_ref_over_cand']:.3g}×" if name == "pretrained_full" and v["backbone_lr_ref_over_cand"] else "–"
        L.append(f"| {lab(sc)} · {name} | {_lr(v['lr_backbone'][0])} → {_lr(v['lr_backbone'][1])} | {ratio} | {_lr(v['lr_head'][0])} → {_lr(v['lr_head'][1])} | "
                 f"{v['epochs'][0]} → {v['epochs'][1]} | {_int(v['n_trainable_backbone'][0])} → {_int(v['n_trainable_backbone'][1])} | "
                 + " / ".join("yes" if x else "no" for x in v["every_backbone_parameter_trained"]) + " |")
    L.append("")
    return L


def render(out, meta):
    fams = [{**f, "members": [(m[0], tuple(m[1].split("|")), tuple(m[2].split("|")), m[3]) for m in f["members"]]} for f in out["panel"]["families"]]
    cov, q, rep = out["coverage"], out["qc"], out["reproduction_3401"]
    ch = out["children"]
    per_seed_rows = Counter()
    for k, v in out["status"].items():
        per_seed_rows[k.split("|")[1]] += v
    n_folds = q["counts"].get("fold_cells", 0) // len(SEEDS)
    fold_txt = (f"each tested in one of {n_folds} subject folds (content fold 0); the children and per-child trial counts of every fold are "
                "identical across the 17 configurations and the three seeds" if q["children_and_trial_counts_equal_across_configurations_and_seeds"]
                else f"{n_folds} subject folds; fold membership or trial counts DIFFER somewhere (see §QC)")
    reg = meta.get("code_registration") or {}
    reg_txt = ("registered in the note before the first real-data run of this code version" if reg.get("current_sha_registered") else
               "NOT registered in the note (see section 7)") + (f"; registered values, in order: {', '.join(x[:12] for x in reg.get('registered', []))}"
                                                                if reg.get("registered") else "")
    L = ["# E seed panel — private task, seeds 3401 / 3407 / 3413 (E_MULTI_SEED)", "",
         "<!-- Generated by `python -m auditory_alignment_v3.aln34.e_multiseed --update-doc`: the preamble, section 1, section 5 and 'Not in the "
         "panel'. Sections 2-4, 6 and 7 are written by hand after the generated tables were viewed; the generator carries them over verbatim "
         "from the previous version of this file. -->", "",
         f"**日期／代码与数据版本 (date, code and data versions).** {DOC_VERSION}, generated {meta['generated']} on `{meta['host']}` inside Slurm "
         f"allocation {meta['slurm_job']} (the session's own CPU allocation; no separately submitted job, no GPU). Code sha256: "
         + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + f" (`aln34/e_multiseed.py` {reg_txt}). Plan files: `units.jsonl` "
         f"{meta['plan_sha256']['units.jsonl'][:12]}, `plan_ext.jsonl` {meta['plan_sha256']['plan_ext.jsonl'][:12]}, seed-panel registry "
         f"{meta['plan_sha256']['seed_panel_v31_registry.json'][:12]}. Unit-record digest {meta['record_digest'][:16]} ({meta['n_records_read']} records). "
         f"Published seed-3401 reference `{meta['published_reference']}` sha256 {meta['published_sha256'][:12]}. Analysis note "
         f"`private/auditory_alignment_v3/aln34/E_MULTI_SEED_NOTE.md` sha256 {meta['note_sha256'][:12]} (last modified {meta['note_mtime']}, "
         f"{'before' if meta.get('note_before_run', True) else 'AFTER'} this run started). Frozen rule: ADDENDUM_05 §6 (seed panel supplement). "
         "Version history and corrections: section 7.", "",
         f"**本轮完成／运行／待依赖 (live state).** Panel rows and their seed-3401 counterparts by status: {out['status']}. No training or evaluation "
         "was run for this report; only completed unit records were read.", "",
         "**已见信息与本轮新增信息 (seen before / new).** Seen before version 1: every seed-3401 private E result (PRIVATE_E_INTERIM.md, read in "
         "full; its source private_e.json; the ADDENDUM_08 researcher summary through the brief B01) and the brief's summary of them; for the panel "
         "only completion status and record structure (no value). New in version 1 (generated 2026-10-17 00:11, tables only): every seed-3407 and "
         "seed-3413 value, the identity means over seeds, the between-seed ranges and every interval. New in version 2 (00:18): the unit-level "
         f"description of §{SECNO['unit']} (post hoc addition F, declared in the note's addendum after version 1 had been read) and the hand-written "
         "sections. New in this version: corrections of the text after an independent verification of version 2 (listed in section 7; declared in "
         f"the note's 'correction 01' before this run), the NLL-excess column of §{SECNO['unit']} (post hoc addition G), the training-recipe "
         f"descriptors of §{SECNO['recipe']} and the seed-3401 critical-value ranges of §{SECNO['qc']}. Earlier numbers: {_versions_txt(meta)}.", "",
         "## 1. 当前观察 (observation)", "",
         "### Scope, units and statistics", "",
         f"- **Seed scope.** Seeds 3401 (breadth seed; the published ADDENDUM_05 units), 3407 and 3413 (ADDENDUM_03 panel rows, registered before "
         f"any of them ran; panel rows and counterparts per seed: {', '.join(f'{s} {per_seed_rows.get(str(s), 0)}' for s in SEEDS)}). Panel "
         "configurations (17): E_GENERIC {NCE, CS_SINGLE} × {cbramod, reve} × {random_full, pretrained_peft, pretrained_full}; E_LOCAL "
         "lag_local_tokens full (NCE, CS_SINGLE); E_PUBLIC_TRANSFER source lag_local_tokens task_partial (NCE, CS_SINGLE); E_GX GX_NATIVE full. "
         "Every other E configuration keeps its seed-3401-only statement (see 'Not in the panel').",
         f"- **Children.** {ch['n']} children ({', '.join(f'{k} {v}' for k, v in ch['groups'].items())}), {fold_txt}. Expected children per "
         f"family: {cov['expected_children']}; missing pairs: {cov['n_missing_pairs']}. n counts children; seeds and folds never add n.",
         "- **Endpoints, kept separate.** Calibrated NLL = positive-affine calibrated natural-distribution NLL (bits per trial; ΔNLL = reference − "
         "candidate). AUC = positive-affine `auc_score` (= native ranking; ΔAUC = candidate − reference). History increment = `hist_gain_bits` "
         "(EEG added to the declared history model q_hist, bits per trial; Δ = candidate − reference). Twin sensitivity = history increment − "
         "the increment of the null-twin EEG (a same-record, same-history-bin trial from another block). Positive = candidate better throughout. "
         "NLL and the history increments are printed with 4 decimals, AUC with 3.",
         "- **Contrasts.** The frozen ADDENDUM_05 §5 families restricted, by design, to the members whose reference and candidate are both panel "
         "configurations (PE-GENERIC 2 of 4 members per scope, PE-LOCAL 7 of 16, PE-TRANSFER 1 of 6; PE-COMPLEMENT and PE-DISTILL have no panel "
         "rows). The PE-TRANSFER member and the PE-LOCAL member `transfer/lag_local_tokens/task_partial` are the same paired difference in two "
         "families. Tag `recipe (C01)`: `random_full → pretrained_full` is a recipe contrast (CORRECTION_01): the initialisation changes together "
         f"with the learning-rate cell; {recipe_summary(out)}. The frozen code's tag 'initialization (matched full update)' is kept in the JSON as "
         "`frozen_tag`. `random_full → pretrained_peft` changes the initialisation, the trainable parameters (LoRA adapters) and the learning rates. PE-LOCAL "
         "and PE-TRANSFER compare different declared input access (E_LOCAL local_only 0–600 ms; E_GENERIC zero-padded −200…600 ms epoch; "
         "E_PUBLIC_TRANSFER private_task_declared_input): access-extended comparisons, not pure architecture contrasts.",
         "- **Intervals.** Bootstrap-t over children (B = 4,000); [sim.] = simultaneous 95 % by max-t within the panel family, for NLL and AUC "
         "separately (the frozen families). In the one-member PE-TRANSFER families the simultaneous interval equals the pointwise one. Replicate "
         "indices depend only on the frozen label, the metric and n, so the three seeds and the identity mean resample the same children (whole "
         "seed vectors jointly). Identity mean = per child, the mean over seeds of the within-seed paired difference; its intervals use the same "
         "families. History increment and twin sensitivity: pointwise 95 % (frozen secondaries); the history increment also gets a max-t within "
         "the same family (addition A, exploratory). Classes (I>0 / I<0 / contains 0) describe simultaneous intervals of the declared draws; "
         f"§{SECNO['mc']} shows their Monte-Carlo stability. No p-values.",
         "- **Uncertainty scope.** Intervals condition on the fitted models. The between-seed range and SD are the only direct view of training "
         "randomness, and three seeds give a coarse one. The seed changes initialisation and batch order, the training-side target statistics and "
         "calibration batches, E_GENERIC heads and adaptation (`random_full` also re-draws the backbone), and the E_PUBLIC_TRANSFER donor (donor "
         "seed = target seed); the early-stopping blocks, the folds and the E_GENERIC learning rates (chosen once on the seed-3401 development cell, "
         f"§{SECNO['recipe']}) do not change. The same children are reused, so agreement across seeds is not an independent replication.", ""]
    for fam, title in (("PE-GENERIC", "Generic FM recipe, PE-GENERIC (E_GENERIC random_full → pretrained_peft / pretrained_full; recipe contrasts)"),
                       ("PE-LOCAL", "Against the local model, PE-LOCAL (E_LOCAL lag_local_tokens full → E_GENERIC / E_PUBLIC_TRANSFER panel configurations)"),
                       ("PE-TRANSFER", "Public auditory transfer against its non-transferred twin, PE-TRANSFER (one-member families)")):
        for m in PRIMARY:
            L += [f"### {SECNO[(fam, m)]} {title} — {NAME[m]}", ""]
            L += primary_table(out, fams, fam, m)
    L += [f"### {SECNO['hist']} History increment (frozen secondary, pointwise; addition A adds a max-t within the same family, exploratory)", "",
          f"Unit: {UNIT[HG]}. The per-seed and identity-mean intervals are pointwise bootstrap-t (frozen label `<family>|<scope>|sec`, so the seed-3401 "
          "pointwise values are the published ones). The last two columns are addition A.", ""]
    L += secondary_table(out, fams, HG, True)
    L += [f"### {SECNO['twin']} Twin sensitivity (frozen secondary, pointwise)", "", f"Unit: {UNIT['twin_sens']}.", ""]
    L += secondary_table(out, fams, "twin_sens", False)
    L += [f"### {SECNO['levels']} Levels of the 17 panel configurations", "",
          "Per seed: the frozen `bc_interim.levels` (pointwise 95 % bootstrap-t for NLL and AUC; HA / NH means for groups with n ≥ 5). Identity "
          "mean: the same on the per-child three-seed means. History-increment intervals and its HA / NH means are addition B (exploratory). AUC "
          "0.5 = chance; an AUC above 0.5 does not by itself show an increment over the declared history.", ""]
    for m in (("NLL", "Calibrated NLL (bits per trial; lower is better)"), ("AUC", "AUC"), (HG, "History increment (bits per trial)"),
              ("twin_sens", "Twin sensitivity (bits per trial; estimates only, as frozen)")):
        L += [f"**{m[1]}**", ""]
        L += level_table(out, m[0])
    L += [f"### {SECNO['groups']} Per-group description (HA / NH; identity mean over seeds; pointwise, descriptive, not a group contrast)", "",
          "NH n = 9. No group contrast is computed and nothing is chosen by group. Groups with n < 5 would show n only.", ""]
    L += group_table(out, fams)
    L += [f"### {SECNO['coverage']} Coverage", "", "Units and children per panel configuration and seed (units per child: how many units test a child):", "",
          "| configuration | seed | units complete / registered | children | units per child |", "|---|---|---|---|---|"]
    for k, v in cov["units"].items():
        p = k.rsplit("|", 1)
        L.append(f"| {lab(p[0])} | {p[1]} | {v['complete']} / {v['registered']} | {v['children']} | {v['units_per_child']} |")
    L += ["", "Paired children per family and endpoint:", "", "| family · endpoint | expected children | per seed 3401 / 3407 / 3413 | identity mean | all three seeds | missing pairs |",
          "|---|---|---|---|---|---|"]
    for k, v in cov["families"].items():
        L.append(f"| {lab(k)} | {v['expected_children']} | " + " / ".join(str(v["per_seed_common"][str(s)]) for s in SEEDS)
                 + f" | {v['seed_mean_common']} | {v['all_three_seeds']} | {v['n_missing_pairs']} |")
    L.append("")
    L.append("Missing pairs: none. Every expected child has every panel pair in every seed." if not cov["any_incomplete"] else
             f"Missing pairs: {cov['n_missing_pairs']} (by family, endpoint, member and seed: {cov['missing_pairs_by_member_seed']}); the children are listed "
             "in the private per-identity file; the complete-case identity means are in the JSON (`seed_mean_complete_case`).")
    L.append("")
    L += [f"### {SECNO['qc']} QC and reproduction of the published seed-3401 tables", ""]
    L.append(f"- Pairing and record checks: {q['counts']}; failures: {q['failures'] if q['failures'] else 'none'}.")
    L.append("  - Within every seed and fold cell, all 17 panel configurations test the same children with the same per-child trial counts; every "
             "panel record has the children and trial counts of its seed-3401 counterpart: "
             f"{q['children_and_trial_counts_equal_across_configurations_and_seeds']}.")
    L.append(f"  - Calibration-set sizes per seed and fold cell (distinct values over the 17 configurations): {q['n_calibration_trials_per_fold_cell']}.")
    L.append(f"- Code hashes per family and seed: {q['code_hash_counts']}. Documented equivalence (IMPLEMENTATION_RECEIPT §5): {q['equivalent_hashes']}. "
             f"One descriptor set (hash after equivalence, code group, target contract, information stratum, selection rule, calibration set, head fit) "
             f"per family across seeds: {q['one_descriptor_set_per_family_across_seeds']}.")
    for k, v in q["descriptors_per_family"].items():
        L.append(f"  - {k}: {v}")
    L.append(f"- E_PUBLIC_TRANSFER donors (seed | check): {q['donors']}.")
    L.append(f"- Group labels consistent across records and seeds: {q['group_label_consistent']} ({q['n_children_with_group']} children).")
    if rep:
        fa, pm, lv = rep["full_aggregation_vs_published"], rep["panel_members_pointwise_vs_published"], rep["panel_levels_vs_published"]
        L.append(f"- Reproduction (imported frozen machinery, seed 3401, all {sum(out['loader_status'][str(SEEDS[0])].values())} seed-3401 E records, every "
                 "frozen family and level) vs "
                 f"`{meta['published_reference']}`: {fa['n_numbers']} numbers, max |Δ| {fa['max_abs_diff']:.1e}, {len(fa['mismatches'])} mismatches"
                 + (f" ({fa['mismatches'][:5]})" if fa["mismatches"] else "") + ".")
        L.append(f"- Panel-family pointwise values at 3401 vs the published values of the same members (frozen secondaries and addition A included): "
                 f"{pm['n_member_blocks']} member × endpoint blocks, max |Δ| {pm['max_abs_diff']:.1e}, {len(pm['mismatches'])} mismatches. Panel levels: "
                 f"{lv['n_configurations']} configurations, {lv['n_numbers']} numbers, max |Δ| {lv['max_abs_diff']:.1e}, {len(lv['mismatches'])} mismatches. "
                 "Only the simultaneous intervals differ from the published ones, because the published families also contain non-panel members:")
        L += ["", "| family · member | published 3401 [sim.] (full frozen family) · class | panel family 3401 [sim.] · class |", "|---|---|---|"]
        changed = []
        mcc = (out.get("mc_stability") or {}).get("cells", {})
        for k, v in rep["published_full_family_simultaneous"].items():
            label, name = k.rsplit("|", 1)
            m = label.rsplit("|", 1)[1]
            x = out["per_seed"][str(SEEDS[0])]["families"][label]["members"].get(name, {})
            L.append(f"| {lab(label)} · {name} | [{v['sim_low']:+.{DEC[m]}f}, {v['sim_high']:+.{DEC[m]}f}] {v['class']} (crit {v['crit']:.2f}, {v['n_members_frozen']} members) | "
                     f"{ivx(x, m, 'sim_low', 'sim_high')} {x.get('class', '')} (crit {out['per_seed'][str(SEEDS[0])]['families'][label].get('crit', float('nan')):.2f}) |")
            if x.get("class") != v["class"]:
                txt = (f"{lab(label)} · {name}: published {v['class']} [{v['sim_low']:+.{DEC[m] + 1}f}, {v['sim_high']:+.{DEC[m] + 1}f}] → panel family "
                       f"{x.get('class')} [{x.get('sim_low', float('nan')):+.{DEC[m] + 1}f}, {x.get('sim_high', float('nan')):+.{DEC[m] + 1}f}]")
                a, b = mcc.get("full_frozen", {}).get(str(SEEDS[0]), {}).get(k), mcc.get("panel", {}).get(str(SEEDS[0]), {}).get(k)
                if a and b:
                    txt += f" (alternative draws: full family {a['classes']}, panel family {b['classes']})"
                changed.append(txt)
        L += ["", "Seed-3401 class differences between the published full family and the panel family (same estimate, same children, same replicate "
              "indices per label; only the family's critical value differs): " + ("; ".join(changed) if changed else "none") + ".", ""]
        L += crit_comparison(out, rep, fams)
    L += [f"### {SECNO['width']} Between-seed spread against the per-seed simultaneous widths (addition C; descriptive)", ""]
    L += width_tables(out, fams)
    L += [f"### {SECNO['mc']} Monte-Carlo stability of the interval classes (addition D; exploratory)", ""]
    L += mc_tables(out)
    L += [f"### {SECNO['unit']} Unit-level description (exploratory, descriptive: post hoc addition F, version 2, declared after version 1 had "
          "been read; post hoc addition G, version 3, declared after version 2 had been read)", ""]
    L += unit_table(out)
    L += [f"### {SECNO['recipe']} Training-recipe descriptors of the panel configurations (version 3; from the unit records; descriptors, not results)", ""]
    L += recipe_tables(out)
    L += ["## 2. 当前工作判断 (working interpretation)", "", "(written after the run)", "",
          "## 3. 仍竞争的解释 (competing explanations)", "", "(written after the run)", "",
          "## 4. 下一轮干预 (next intervention)", "", "(written after the run)", ""]
    det, mem = meta.get("determinism"), meta.get("peak_rss_mib")
    L += ["## 5. 复用与运行 (reuse and execution)", "",
          f"- Reused: {meta['n_records_read']} completed unit records — {meta['records_by_role']['panel_3407_3413']} panel records (seeds 3407/3413), "
          f"{meta['records_by_role']['panel_3401']} seed-3401 counterparts of the panel configurations, and {meta['records_by_role']['other_3401']} other "
          "seed-3401 E records (E_LOCAL other architectures / windows, E_GX other windows, E_GENERIC frozen / partial, E_PUBLIC_TRANSFER task_full and "
          "FM sources, E_COMPLEMENT, E_DISTILL), read only for the full seed-3401 reproduction. New jobs: none. GPU: none.",
          f"- Run: {meta['runtime_seconds']:.0f} s wall time in the session's own CPU allocation (nice 10), including the "
          f"{(out.get('mc_stability') or {}).get('k', 0)}-draw Monte-Carlo table and the determinism re-computation; measured peak resident memory "
          + ("not measured" if mem is None else f"{mem:.0f} MiB (ru_maxrss of this process)") + ".",
          "- Determinism: " + ("not checked in this run." if not det else
                               f"a second computation in the same process (same inputs, without the Monte-Carlo table) reproduced {det['json']['n_numbers']} "
                               f"numbers of the non-meta outputs (max |Δ| {det['json']['max_abs_diff']:.1e}, {len(det['json']['mismatches'])} mismatches) and "
                               f"{det['per_identity']['n_numbers']} numbers of the per-identity file (max |Δ| {det['per_identity']['max_abs_diff']:.1e}, "
                               f"{len(det['per_identity']['mismatches'])} mismatches)."),
          f"- Code registration: the sha256 of `aln34/e_multiseed.py` used here is {meta['code_sha256']['aln34/e_multiseed.py'][:12]}; {reg_txt}.",
          f"- Earlier versions: {_versions_txt(meta)}.",
          "- Outputs (all 0600): `results/auditory_alignment_v3/aln34/e_multiseed/e_multiseed.json` (aggregates only); this document; the private "
          "per-identity values in `private/auditory_alignment_v3/aln34/e_multiseed/per_identity.json` (child pseudonym, group, trial counts, per seed "
          "and configuration NLL / AUC / history increment / twin sensitivity, the within-seed paired differences and the identity means; no name, "
          f"no identity map). Privacy scan of the two aggregate outputs: {meta.get('privacy_scan', 'not run')}.",
          f"- Code: `auditory_alignment_v3/aln34/e_multiseed.py`. Synthetic tests: `{os.path.relpath(TESTS, core.REPO)}`.", "",
          "## 6. 暂不决定 (not decided here)", "", "(written after the run)", "",
          "## Not in the panel — these keep seed-3401-only statements", "",
          "These configurations and contrasts exist for seed 3401 only. PRIVATE_E_INTERIM.md (ADDENDUM_05) reports them; the three-seed statements "
          "of this document do not cover them.", ""]
    for f in fams:
        L.append(f"- {lab(fkey(f))}: {', '.join(f['non_panel_members']) if f['non_panel_members'] else 'none'}")
    L += [f"- {x}" for x in NOT_IN_PANEL_FIXED]
    npp = out.get("non_panel_published_3401") or {}
    if npp.get("members"):
        L += ["", "Published seed-3401 values of the non-panel members of the panel families (Δ, simultaneous class in the full frozen family; no seed panel):", ""]
        by = defaultdict(list)
        for k, v in npp["members"].items():
            label, name = k.rsplit("|", 1)
            m = label.rsplit("|", 1)[1]
            by[label].append(f"{name} {fx(v.get('est'), m)} {v.get('class')}")
        L += [f"- {lab(label)}: " + "; ".join(v) for label, v in by.items()]
    L += ["", "## 7. 版本与更正 (version history and corrections)", "", "(written after the run)", ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------------------------ document splice
def sections(text):
    """[(level-2 heading or None for the preamble, body)] in order."""
    out, head, buf = [], None, []
    for line in text.split("\n"):
        if line.startswith("## "):
            out.append((head, buf)); head, buf = line, []
        else:
            buf.append(line)
    out.append((head, buf))
    return [(h, "\n".join(b)) for h, b in out]


def _hand_key(h):
    return None if h is None or len(h.split()) < 2 or h.split()[1] not in HAND else h.split()[1]


def splice(generated, existing):
    """generated sections from `generated`; hand-written sections (HAND) verbatim from `existing` when present there."""
    old = {_hand_key(h): (h, b) for h, b in sections(existing) if _hand_key(h)}
    used, parts = set(), []
    for h, b in sections(generated):
        k = _hand_key(h)
        if k in old:
            h, b = old[k]; used.add(k)
        parts.append(b if h is None else f"{h}\n{b}")
    lost = set(old) - used
    if lost:
        raise ValueError(f"hand-written sections of the existing document missing from the template: {sorted(lost)}")
    return "\n".join(parts)


# ------------------------------------------------------------------------------------------------ main
def _file_sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def registered_shas(note_path=NOTE):
    """sha256 values recorded for e_multiseed.py in the note's 'Code registration' section(s), in order."""
    if not os.path.exists(note_path):
        return []
    txt = open(note_path).read()
    i = txt.find("## Code registration")
    return re.findall(r"(?<![\w])e_multiseed\.py`?\s*(?:sha256)?\s*`?([0-9a-f]{64})", txt[i:]) if i >= 0 else []


def compare_with_archives(out, per_identity, archives=ARCHIVES):
    """number-by-number comparison of the current outputs with every archived earlier version: the JSON blocks the archive has (meta
    excluded; fields only in the current version counted as added, not as mismatches), the new top-level blocks, and the per-identity file."""
    res = {}
    for name, path in archives:
        jp, pp = os.path.join(path, "e_multiseed.json"), os.path.join(path, "per_identity.json")
        if not (os.path.exists(jp) and os.path.exists(pp)):
            continue
        old = json.load(open(jp)); old.pop("meta", None)
        r = {"archive": os.path.relpath(path, core.REPO), "n_compared_blocks": len(old),
             "json": compare_tree(_plain({k: v for k, v in out.items() if k in old}), old, one_sided=True),
             "per_identity": compare_tree(_plain(per_identity), json.load(open(pp)), one_sided=True),
             "new_top_level_keys": sorted(set(out) - set(old)), "missing_top_level_keys": sorted(set(old) - set(out))}
        for v in (r["json"], r["per_identity"]):
            v["mismatches"] = v["mismatches"][:20]
        res[name] = r
    return res


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--update-doc", action="store_true", help="(re)generate the results document, keeping its hand-written sections verbatim")
    a.add_argument("--mc-k", type=int, default=MC_K, help="alternative bootstrap draw sets for the Monte-Carlo table (0 = skip)")
    args = a.parse_args()
    os.umask(0o077)
    from auditory_alignment_v3 import run as r3
    t0 = time.time()
    rows = r3.all_rows(); load = BI.unit_loader()
    published = json.load(open(PUBLISHED))
    pub_sha = _file_sha(PUBLISHED)
    out, per_identity, census = analyse(rows, load, published, mc_k=args.mc_k)
    out2, per_identity2, _ = analyse(rows, load, published, mc_k=0)  # determinism re-computation (without the Monte-Carlo table)
    strip = lambda o: _plain({k: v for k, v in o.items() if k != "mc_stability"})
    det = {"json": compare_tree(strip(out), strip(out2)), "per_identity": compare_tree(_plain(per_identity), _plain(per_identity2))}
    for v in det.values():
        v["mismatches"] = v["mismatches"][:20]; v.pop("n_added", None)
    versions = compare_with_archives(out, per_identity)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    read = sorted(e for e, st in census.status.items() if st is not None)
    byid = {r["experiment_id"]: r for r in rows}
    roles = Counter("panel_3407_3413" if row_in_panel(byid[e]) and byid[e]["seed"] != SEEDS[0] else "panel_3401" if row_in_panel(byid[e]) else "other_3401"
                    for e in read if e in byid)
    dig = hashlib.sha256()
    for e in read:
        p = os.path.join(UNITS, f"{e}.json")
        if os.path.exists(p):
            dig.update(e.encode()); dig.update(_file_sha(p).encode())
    code = {f: _file_sha(os.path.join(here, *f.split("/"))) for f in ("aln34/e_multiseed.py", "bc_interim.py", "sci_r1/stats.py")}
    regs = registered_shas()
    meta = {"analysis": "E seed panel (ADDENDUM_05 §6 seed panel supplement; ALN3.4 docs/00)", "doc_version": DOC_VERSION,
            "note": os.path.relpath(NOTE, core.REPO), "note_sha256": _file_sha(NOTE),
            "note_mtime": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.path.getmtime(NOTE))), "note_before_run": os.path.getmtime(NOTE) < t0,
            "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "host": socket.gethostname(), "slurm_job": os.environ.get("SLURM_JOB_ID", "none"),
            "seeds": list(SEEDS), "n_boot": S.NB, "mc": {"k": args.mc_k, "seed_step": MC_STEP}, "runtime_seconds": None, "code_sha256": code,
            "code_registration": {"registered": regs, "current_sha_registered": code["aln34/e_multiseed.py"] in regs},
            "plan_sha256": {"units.jsonl": _file_sha(core.PLAN), "plan_ext.jsonl": _file_sha(os.path.join(core.OUT, "plan_ext.jsonl")),
                            "seed_panel_v31_registry.json": _file_sha(REGISTRY)},
            "record_digest": dig.hexdigest(), "n_records_read": len(read),
            "records_by_role": {k: roles.get(k, 0) for k in ("panel_3407_3413", "panel_3401", "other_3401")},
            "published_reference": os.path.relpath(PUBLISHED, core.REPO), "published_sha256": pub_sha,
            "published_private_copy_identical": os.path.exists(PUBLISHED_PRIVATE) and _file_sha(PUBLISHED_PRIVATE) == pub_sha,
            "tests": os.path.relpath(TESTS, core.REPO), "determinism": det, "correction_01": "random_full -> pretrained_full is a recipe contrast",
            "version_comparisons": versions}
    meta["runtime_seconds"] = round(time.time() - t0, 1)
    meta["peak_rss_mib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    os.makedirs(RES, exist_ok=True); os.makedirs(PRIV, exist_ok=True)
    for d in (RES, PRIV):
        os.chmod(d, 0o700)
    jp = os.path.join(RES, "e_multiseed.json")
    doc = os.path.join(DOCS, "E_MULTI_SEED_RESULTS.md") if args.update_doc else os.path.join(RES, "E_MULTI_SEED_RESULTS.generated.md")
    child_ids = set(per_identity["children"])
    meta["privacy_scan"] = "pending"
    BI.write_json(jp, {"meta": meta, **out}, private=True)
    BI.write_json(os.path.join(PRIV, "per_identity.json"), per_identity, private=True)
    gen = render(out, meta)
    text = splice(gen, open(doc).read()) if args.update_doc and os.path.exists(doc) else gen
    with open(doc, "w") as fh:
        fh.write(text)
    os.chmod(doc, 0o600)
    bad = BI.privacy_scan([jp, doc], child_ids)
    meta["privacy_scan"] = "PASS (no child pseudonym in either file)" if not bad else f"FAIL {bad}"
    BI.write_json(jp, {"meta": meta, **out}, private=True)
    text = splice(render(out, meta), open(doc).read()) if args.update_doc else render(out, meta)
    with open(doc, "w") as fh:
        fh.write(text)
    os.chmod(doc, 0o600)
    bad = BI.privacy_scan([jp, doc], child_ids) or bad
    rep = out["reproduction_3401"]
    print("doc:", doc)
    print("status:", out["status"])
    print("qc failures:", out["qc"]["failures"] or "none", "| equal children/counts:", out["qc"]["children_and_trial_counts_equal_across_configurations_and_seeds"])
    print("reproduction full:", {k: rep["full_aggregation_vs_published"][k] for k in ("n_numbers", "max_abs_diff")}, len(rep["full_aggregation_vs_published"]["mismatches"]),
          "| panel pointwise:", rep["panel_members_pointwise_vs_published"]["n_member_blocks"], rep["panel_members_pointwise_vs_published"]["max_abs_diff"],
          len(rep["panel_members_pointwise_vs_published"]["mismatches"]), "| levels:", rep["panel_levels_vs_published"]["n_numbers"],
          len(rep["panel_levels_vs_published"]["mismatches"]))
    print("coverage incomplete:", out["coverage"]["any_incomplete"], "| missing pairs:", out["coverage"]["n_missing_pairs"])
    print("determinism:", {k: (v["n_numbers"], v["max_abs_diff"], len(v["mismatches"])) for k, v in det.items()})
    for name, v in versions.items():
        print(f"{name} comparison:", {k: (v[k]["n_numbers"], v[k]["max_abs_diff"], len(v[k]["mismatches"]), v[k].get("n_added")) for k in ("json", "per_identity")},
              "| new top-level blocks:", v["new_top_level_keys"])
    print("mc checks:", (out.get("mc_stability") or {}).get("checks"))
    print("code registered:", meta["code_registration"]["current_sha_registered"], "| privacy scan:", "PASS" if not bad else bad,
          "| runtime", meta["runtime_seconds"], "s | peak rss", round(meta["peak_rss_mib"]), "MiB")
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
