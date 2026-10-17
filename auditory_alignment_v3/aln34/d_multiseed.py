"""ALN3.4 R34_D_PANEL: multi-seed aggregation of the completed D panel (seeds 3401 / 3407 / 3413).

Panel (ADDENDUM_03 §1.1, roles P4_ATTENTION_ADAPT): `lag_local_tokens`, NCE, FAU and DTU;
  D_ADAPT adapters none / input_spatial; D_ATTENTION attended_alignment / alignment_plus_selection with the mean_score and
  learned_temporal integrators (the learned_temporal row is a derived copy of its mean_score twin, so both integrators are
  read from the mean_score record, as in d_lag_interim).
Analysis note, written before any panel value was computed: private/auditory_alignment_v3/aln34/D_MULTI_SEED_NOTE.md. The v2
additions below were declared in its correction section (2026-10-16 20:34-20:36 CEST) before they were computed.

The ADDENDUM_12 machinery is imported, not re-implemented: d_lag_interim.collect / att_families / ad_families / run_fams /
NEW_DIR and bc_interim.run_family / member_values / diff (sci_r1.stats: bootstrap-t over identities, B = 4,000, max-t within a
family). What is new here:
  * panel families: every ADDENDUM_12 family restricted (by design, not by data) to the members whose two configurations are in
    the registered panel; the same member set for every seed; labels unchanged, so replicate indices are shared across seeds;
  * per seed: d_lag_interim.run_fams on that seed's identity values (BI.SEED switched for the duration of collect only);
  * identity mean: per identity, the mean over the seeds in which the pair exists of the within-seed paired difference (a
    reference of one seed is never paired with a candidate of another), then the same family machinery on these means;
  * between-seed range, coverage (identities x seeds, missing pairs listed, never filled), pairing QC, the seed-3401
    reproduction of the published results/auditory_alignment_v3/d_lag/d_lag.json, training-side choices (descriptive).
v2 (2026-10-16, after an independent verification of v1; v1 is archived in private/auditory_alignment_v3/aln34/d_multiseed/
v1_20261016T2003/; every v1 number is unchanged):
  * between-seed spread against the per-seed simultaneous widths (below every / between / above every width; descriptive);
  * Monte-Carlo stability of every primary interval class under MC_K alternative bootstrap draw sets (exploratory; the declared
    draws stay the reported result);
  * the two card contrasts with max-t across windows (AT-TASK) or support levels (AD-GAIN) within a dataset (post hoc sensitivity);
  * D_ADAPT support / query sizes; per-seed pointwise intervals of the secondary readouts in the document; rank unit fixed (a
    proportion, not percentile points); coverage-table rendering fixed;
  * run record: a determinism re-computation, the comparison with v1, measured peak memory; the results document's hand-written
    sections (2-4, 6, 7) are carried over verbatim, everything else in it is generated.
Not part of any training code hash; reads unit records only; no GPU.

Usage: python -m auditory_alignment_v3.aln34.d_multiseed [--update-doc] [--mc-k K]
  --update-doc  regenerate docs/auditory_alignment_v3/D_MULTI_SEED_RESULTS.md, keeping its hand-written sections verbatim
                (without it, the generated version is written to the results directory only)."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import resource
import socket
import time
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3 import d_lag_interim as DL
from auditory_alignment_v3.sci_r1 import stats as S

SEEDS = (3401, 3407, 3413)
DATASETS = ("fau", "dtu")
OBJ = "NCE"
TASKS = ("attended_alignment", "alignment_plus_selection")
ADAPTERS = ("none", "input_spatial")
ATT_METRICS, ATT_PRIMARY = ("acc", "acc_native", "margin"), "acc"
AD_METRICS, AD_PRIMARY = ("gain_bits", "rank_pct_q", "top1_q", "gain_bits_native"), "gain_bits"
METRICS = {"att": ATT_METRICS, "ad": AD_METRICS}
PRIMARY = {"att": ATT_PRIMARY, "ad": AD_PRIMARY}
ORDER_AFFECTED = ("AT-INTEGRATOR",)  # learned_temporal comparisons: provisional under R34_ATTENTION_ORDER
CARD_FAMILIES = ("AD-GAIN", "AT-TASK")  # card R34_D_PANEL: none_vs_input_spatial, attended_vs_alignment_selection
NOT_IN_PANEL = ("every CS_SINGLE cell (D_ATTENTION and D_ADAPT)", "output_low_rank (D_ADAPT)",
                "selection_only (D_ATTENTION; incl. the DTU AT-TASK 'align NCE->selection_only' cells)",
                "AT-TASK 'align->align+sel CS'", "D_COVERAGE (whole family)", "D policy arms dense_fm_policy / complement_policy (held)",
                "per-segment 5 s attention_2afc (not aggregated at 3401 either)")
MC_K, MC_STEP = 50, 1000  # alternative draw set k adds MC_STEP * k to sci_r1.stats.SEED (k = 1..MC_K); k = 0 is the declared draw
HAND = ("2.", "3.", "4.", "6.", "7.")  # hand-written sections of the results document (carried over verbatim)
DOC_VERSION = "Version 2"
RANK_UNIT = ("`rank_pct` is the mean over queries of rank / (n_candidates − 1), a proportion (0 = true candidate ranked first, about "
             "0.5 = chance); Δrank = reference − candidate in the same proportion units (positive = lower rank = better; ×100 = "
             "percentile points)")
RES = os.environ.get("DM_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln34", "d_multiseed"))
DOCS = os.environ.get("DM_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
PRIV = os.environ.get("DM_PRIV", os.path.join(core.OUT, "aln34", "d_multiseed"))
NOTE = os.path.join(core.OUT, "aln34", "D_MULTI_SEED_NOTE.md")
PUBLISHED = os.path.join(core.REPO, "results", "auditory_alignment_v3", "d_lag", "d_lag.json")
UNITS = os.path.join(core.OUT, "units")
V1_ARCHIVE = os.path.join(core.OUT, "aln34", "d_multiseed", "v1_20261016T2003")
TESTS = os.path.join(core.REPO, "tests", "auditory_alignment_v3", "aln34", "test_d_multiseed.py")


def setup():
    """directions of the D endpoints (positive = better), this process only - as d_lag_interim.main does."""
    BI.PDIR.update(DL.NEW_DIR)


def direction(metric):
    return BI.DIRECTION.get(metric) or BI.PDIR[metric]


# ------------------------------------------------------------------------------------------------ panel definition
def row_in_panel(r):
    """registered panel rows (by design): seeds 3401/3407/3413, lag_local_tokens, NCE, FAU/DTU, the panel adapters / tasks."""
    s = r["spec"]
    if r["seed"] not in SEEDS or r["dataset"] not in DATASETS or s.get("architecture") != "lag_local_tokens" or s.get("objective") != OBJ:
        return False
    if r["family_id"] == "D_ADAPT":
        return s.get("adapter") in ADAPTERS
    if r["family_id"] == "D_ATTENTION":
        return s.get("training_task") in TASKS and s.get("integrator") in ("mean_score", "learned_temporal")
    return False


def in_panel(c):
    """pseudo-configuration of d_lag_interim.collect -> True when it belongs to the registered panel."""
    if c[0] in ("ATT", "CHANCE"):
        return c[1] in DATASETS and c[2] in TASKS and c[3] == OBJ
    if c[0] == "AD":
        return c[1] in DATASETS and c[2] == OBJ and c[3] in ADAPTERS
    return False


def panel_families():
    """ADDENDUM_12 families restricted to panel members: [{family, scope, label, kind, members, n_members_addendum12}]."""
    out = []
    for kind, fams in (("att", DL.att_families()), ("ad", DL.ad_families())):
        for fam, sc, label, members in fams:
            keep = [m for m in members if in_panel(m[1]) and in_panel(m[2])]
            if keep:
                out.append({"family": fam, "scope": sc, "label": label, "kind": kind, "members": keep, "n_members_addendum12": len(members)})
    return out


def card_families():
    """post hoc sensitivity (note correction 2026-10-16): the two card contrasts with max-t across windows (AT-TASK) or support
    levels (AD-GAIN) within a dataset. Same members as the one-member panel families; new labels, so new draws (still shared
    across seeds). No control across datasets (different identities; ADDENDUM_12 families are per dataset)."""
    out = []
    for ds in DATASETS:
        A = lambda t, w, ds=ds: ("ATT", ds, t, OBJ, "ms", w)
        out.append({"family": "CARD-AT-TASK", "scope": ds, "label": f"R34-CARD|AT-TASK|{ds}", "kind": "att",
                    "members": [(f"{w}s", A(TASKS[0], w), A(TASKS[1], w), "task") for w in DL.WINS],
                    "panel_counterpart": {f"{w}s": [f"AT-TASK|{ds}|{w}s", "align->align+sel NCE"] for w in DL.WINS}})
        out.append({"family": "CARD-AD-GAIN", "scope": f"{ds}|{OBJ}", "label": f"R34-CARD|AD-GAIN|{ds}|{OBJ}", "kind": "ad",
                    "members": [(sf, ("AD", ds, OBJ, "none", sf), ("AD", ds, OBJ, "input_spatial", sf), "personal supervised adaptation")
                                for sf in DL.SUPPORTS],
                    "panel_counterpart": {sf: [f"AD-GAIN|{ds}|{OBJ}|{sf}", "input_spatial"] for sf in DL.SUPPORTS}})
    return out


def full_families_with_panel_members():
    """the full ADDENDUM_12 families (seed 3401) that contain at least one panel member, with the names of those members."""
    out = []
    for kind, fams in (("att", DL.att_families()), ("ad", DL.ad_families())):
        for fam, sc, label, members in fams:
            keep = [m[0] for m in members if in_panel(m[1]) and in_panel(m[2])]
            if keep:
                out.append({"family": fam, "scope": sc, "label": label, "kind": kind, "members": members, "panel_members": keep})
    return out


def as_tuples(fams, kind):
    return [(f["family"], f["scope"], f["label"], f["members"]) for f in fams if f["kind"] == kind]


@contextlib.contextmanager
def seed_scope(seed):
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


# ------------------------------------------------------------------------------------------------ loading
def _sha(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, default=float).encode()).hexdigest()


def census_of(row, rec):
    """counts, ids and hashes of one record (no metric value is kept)."""
    info = {"family": row["family_id"], "seed": row["seed"], "dataset": row["dataset"], "fold": [row["subject_fold"], row["content_fold"]],
            "code_hash": rec.get("code_hash"), "target_contract": rec.get("target_contract")}
    if row["family_id"] == "D_ATTENTION":
        aw = rec["eval"]["attention_windows"]
        info["participants"] = {pid: {k: (v or {}).get("n_windows") for k, v in d.items() if k != "group"} for pid, d in aw["per_participant"].items()}
        info["groups"] = {pid: d.get("group") for pid, d in aw["per_participant"].items()}
        info["aw_sha256"] = _sha(aw)
        info["chosen_sel_weight"] = rec.get("chosen_sel_weight")
        info["shared_model_with"] = rec.get("shared_model_with")
    elif row["family_id"] == "D_ADAPT":
        pp = rec["eval"]["per_participant"]
        info["participants"] = {pid: {f"{sf}|{rd}": [v[f"support_{sf}"][rd].get("n_query"), v[f"support_{sf}"].get("n_support")]
                                      for sf in DL.SUPPORTS if f"support_{sf}" in v for rd in ("unified", "native")} for pid, v in pp.items()}
        info["groups"] = {pid: v.get("group") for pid, v in pp.items()}
        dep = rec.get("dependency") or {}
        info["base"] = dep.get("base_same_fold"); info["base_checkpoint"] = dep.get("base_checkpoint")
        info["steps_chosen"] = (rec["eval"].get("steps") or {}).get("chosen")
    return info


class Census:
    """loader wrapper: returns the record unchanged and keeps census_of() of every complete record it served."""

    def __init__(self, load, rows):
        self.inner, self.rows, self.info, self.status = load, {r["experiment_id"]: r for r in rows}, {}, {}

    def __call__(self, eid):
        rec = self.inner(eid)
        self.status[eid] = "missing" if rec is None else rec.get("status")
        if rec is not None and rec.get("status") == "complete" and eid in self.rows:
            self.info[eid] = census_of(self.rows[eid], rec)
        return rec


def collect_seed(rows, load, seed):
    """d_lag_interim.collect for one seed (D_ATTENTION mean_score rows + D_ADAPT rows; D_COVERAGE is not part of the panel)."""
    d_rows = [r for r in rows if r["family_id"] in ("D_ATTENTION", "D_ADAPT")]
    with seed_scope(seed):
        vals, grp, status, _, _ = DL.collect(d_rows, load)
    return vals, grp, status


# ------------------------------------------------------------------------------------------------ seed mean
def seed_mean_deltas(vals_by_seed, ref, cand, metric):
    """{identity: (mean over the seeds with the pair of the within-seed paired difference, number of such seeds)}."""
    per = {s: BI.member_values(v, ref, cand, metric) for s, v in vals_by_seed.items()}
    ids = set().union(*[set(p) for p in per.values()]) if per else set()
    return {i: (float(np.mean([per[s][i] for s in per if i in per[s]])), int(sum(i in per[s] for s in per))) for i in ids}


def seed_mean_inputs(fams, vals_by_seed, complete_case=False):
    """pseudo-configurations holding the identity seed means, so that d_lag_interim.run_fams / bc_interim.run_family apply
    unchanged (reference 0, candidate = signed mean, so that BI.diff returns the mean difference for every direction)."""
    pv, out_fams, nseeds = {}, [], {}
    for f in fams:
        members = []
        for name, ref, cand, tag in f["members"]:
            R, C = ("SM_REF", f["label"], name), ("SM_CAND", f["label"], name)
            pr, pc = defaultdict(dict), defaultdict(dict)
            for m in METRICS[f["kind"]]:
                sgn = -1.0 if direction(m) == "lower" else 1.0
                d = seed_mean_deltas(vals_by_seed, ref, cand, m)
                if m == PRIMARY[f["kind"]]:
                    nseeds[(f["label"], name)] = {i: k for i, (_, k) in d.items()}
                for i, (x, k) in d.items():
                    if complete_case and k < len(vals_by_seed):
                        continue
                    pr[i][m] = 0.0; pc[i][m] = sgn * x
            pv[R], pv[C] = dict(pr), dict(pc)
            members.append((name, R, C, tag))
        out_fams.append({**f, "members": members, "orig_members": f["members"]})
    return pv, out_fams, nseeds


def run_seed_mean(fams, vals_by_seed, grp, notes, complete_case=False):
    pv, sfams, nseeds = seed_mean_inputs(fams, vals_by_seed, complete_case)
    res = {"families": {}, "secondary": {}}
    for kind in ("att", "ad"):
        r = DL.run_fams(as_tuples(sfams, kind), pv, grp, METRICS[kind], PRIMARY[kind], notes)
        res["families"].update(r["families"]); res["secondary"].update(r["secondary"])
    for f in sfams:  # put the real configurations back into the member records; add the seed-count distribution
        orig = {m[0]: m for m in f["orig_members"]}
        blocks = [res["families"][f["label"]]] + list(res["secondary"][f["label"]].values())
        for blk in blocks:
            for name, r in blk.get("members", {}).items():
                r["ref"], r["cand"] = BI.ckey(orig[name][1]), BI.ckey(orig[name][2])
        for name, r in res["families"][f["label"]].get("members", {}).items():
            ns = nseeds.get((f["label"], name), {})
            r["identities_by_n_seeds"] = {str(k): v for k, v in sorted(Counter(ns.values()).items())}
    return res, pv


# ------------------------------------------------------------------------------------------------ per seed / range
def run_per_seed(fams, vals, grp, notes):
    res = {"families": {}, "secondary": {}}
    for kind in ("att", "ad"):
        r = DL.run_fams(as_tuples(fams, kind), vals, grp, METRICS[kind], PRIMARY[kind], notes)
        res["families"].update(r["families"]); res["secondary"].update(r["secondary"])
    return res


def run_primary(fams, vals, notes):
    """primary readout only, no group columns: {label: bc_interim.run_family(...)} with max-t within each family."""
    return {f["label"]: BI.run_family(f["label"], f["members"], vals, PRIMARY[f["kind"]], notes, True, None) for f in fams}


def block(res, f, metric):
    return res["families"][f["label"]] if metric == PRIMARY[f["kind"]] else res["secondary"][f["label"]][metric]


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
            for m in METRICS[f["kind"]]:
                ests = {s: block(per_seed[s], f, m)["members"].get(name, {}).get("est") for s in per_seed}
                ests = {s: e for s, e in ests.items() if e is not None}
                if not ests:
                    continue
                v = list(ests.values())
                r = {"per_seed": {str(s): e for s, e in ests.items()}, "min": min(v), "max": max(v), "spread": max(v) - min(v), "n_seeds": len(v)}
                if m == PRIMARY[f["kind"]]:
                    mem = {s: block(per_seed[s], f, m)["members"].get(name, {}) for s in ests}
                    r["classes"] = {str(s): mem[s].get("class") for s in ests}
                    w = {str(s): mem[s]["sim_high"] - mem[s]["sim_low"] for s in ests if "sim_low" in mem[s]}
                    if len(w) == len(ests) >= 2:
                        lo, hi = min(w.values()), max(w.values())
                        r["sim_widths"] = w
                        r["spread_vs_widths"] = width_category(r["spread"], list(w.values()))
                        r["spread_over_narrowest_width"] = r["spread"] / lo if lo > 0 else None
                        r["spread_over_widest_width"] = r["spread"] / hi if hi > 0 else None
                out[f"{f['label']}|{name}|{m}"] = r
    return out


def run_card(card_fams, vals_by_seed, notes):
    """card-family sensitivity with the declared draws: per seed and identity mean (primary readout)."""
    res = {str(s): run_primary(card_fams, vals_by_seed[s], notes) for s in vals_by_seed}
    pv, sfams, nseeds = seed_mean_inputs(card_fams, vals_by_seed)
    mean = run_primary(sfams, pv, notes)
    for f in sfams:
        orig = {m[0]: m for m in f["orig_members"]}
        for name, r in mean[f["label"]].get("members", {}).items():
            r["ref"], r["cand"] = BI.ckey(orig[name][1]), BI.ckey(orig[name][2])
            r["identities_by_n_seeds"] = {str(k): v for k, v in sorted(Counter(nseeds.get((f["label"], name), {}).values()).items())}
    res["mean"] = mean
    return res


# ------------------------------------------------------------------------------------------------ Monte-Carlo stability
def _cells(res, only=None):
    """{label|member: (sim_low, sim_high, class, crit)} of run_primary output (only: {label: member names to keep})."""
    out = {}
    for label, blk in res.items():
        for name, m in blk.get("members", {}).items():
            if "class" in m and (only is None or name in only.get(label, ())):
                out[f"{label}|{name}"] = (m["sim_low"], m["sim_high"], m["class"], blk.get("crit"))
    return out


def mc_stability(fams, card_fams, vals_by_seed, k=MC_K, step=MC_STEP):
    """exploratory (declared in the note's correction of 2026-10-16): every primary simultaneous interval re-computed with k
    alternative bootstrap draw sets (sci_r1.stats.SEED + step * j, j = 1..k; same identities, estimates, families, B). Cells: the
    panel families per seed and for the identity mean, the card families, and the full ADDENDUM_12 families at seed 3401 (panel
    members only). The declared draw (j = 0) stays the reported result."""
    full = full_families_with_panel_members()
    only = {f["label"]: set(f["panel_members"]) for f in full}
    pv, sfams, _ = seed_mean_inputs(fams, vals_by_seed)
    pvc, sfams_c, _ = seed_mean_inputs(card_fams, vals_by_seed)

    def one(offset):
        sink, r = [], {}
        with draw_scope(offset):
            for s in vals_by_seed:
                r[("panel", str(s))] = _cells(run_primary(fams, vals_by_seed[s], sink))
            r[("panel", "mean")] = _cells(run_primary(sfams, pv, sink))
            for s in vals_by_seed:
                r[("card", str(s))] = _cells(run_primary(card_fams, vals_by_seed[s], sink))
            r[("card", "mean")] = _cells(run_primary(sfams_c, pvc, sink))
            if SEEDS[0] in vals_by_seed:
                r[("full_addendum12", str(SEEDS[0]))] = _cells(run_primary(full, vals_by_seed[SEEDS[0]], sink), only)
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
                "declared": {"sim_low": lo, "sim_high": hi, "class": c, "crit": crit}, "n_alternatives": len(al),
                "n_same_class": int(cl.get(c, 0)), "classes": dict(sorted(cl.items())), "sim_low_range": rng(0), "sim_high_range": rng(1),
                "crit_range": rng(3)}
    return {"k": k, "seed_step": step, "base_seed": S.SEED, "alternative_base_seeds": [S.SEED + step * j for j in range(1, k + 1)], "cells": cells}


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
    for blk, cs in mc.get("card", {}).items():
        for key, cell in cs.items():
            label, name = key.rsplit("|", 1)
            cmp(f"card|{blk}|{key}", cell, out["card_families"]["results"][blk][label]["members"][name])
    rep = out.get("reproduction_3401")
    n_pub = 0
    if rep:
        for blk, cs in mc.get("full_addendum12", {}).items():
            for key, cell in cs.items():
                ref = rep["published_full_family_simultaneous"].get(key)
                if ref is not None:
                    n_pub += 1; cmp(f"full_addendum12|{blk}|{key}", cell, ref)
    return {"n_numbers": n, "max_abs_diff": d, "class_mismatches": bad, "full_family_cells_checked_against_published": n_pub}


# ------------------------------------------------------------------------------------------------ coverage
def config_name(r):
    s = r["spec"]
    return f"{s['adapter']}" if r["family_id"] == "D_ADAPT" else f"{s['training_task']}|{s['integrator']}"


def coverage(rows, census, vals_by_seed, fams):
    unit = defaultdict(lambda: {"registered": 0, "complete": 0, "units_per_identity": Counter()})
    for r in rows:
        if not row_in_panel(r):
            continue
        k = f"{r['family_id']}|{r['dataset']}|{config_name(r)}|{r['seed']}"
        unit[k]["registered"] += 1
        unit[k]["complete"] += int(census.status.get(r["experiment_id"]) == "complete")
        info = census.info.get(r["experiment_id"])
        if info is not None and info.get("participants"):
            for pid in info["participants"]:
                unit[k]["units_per_identity"][pid] += 1
    units = {k: {"registered": v["registered"], "complete": v["complete"], "identities": len(v["units_per_identity"]),
                 "units_per_identity": {str(n): c for n, c in sorted(Counter(v["units_per_identity"].values()).items())}} for k, v in sorted(unit.items())}
    expected = defaultdict(set)  # (kind, dataset) -> identities seen in any panel configuration at any seed
    for s, vals in vals_by_seed.items():
        for c, per in vals.items():
            if c[0] in ("ATT", "AD") and in_panel(c):
                expected[("att" if c[0] == "ATT" else "ad", c[1])] |= set(per)
    fam_cov, missing, any_incomplete = {}, [], False
    for f in fams:
        ds = f["scope"].split("|")[0]; E = expected[(f["kind"], ds)]; prim = PRIMARY[f["kind"]]
        pres = {name: {s: set(BI.member_values(vals_by_seed[s], ref, cand, prim)) for s in vals_by_seed} for name, ref, cand, _ in f["members"]}
        per_seed_common = {str(s): len(set.intersection(*[pres[n][s] for n in pres])) for s in vals_by_seed}
        any_seed = set.intersection(*[set().union(*pres[n].values()) for n in pres])
        all_seeds = set.intersection(*[set.intersection(*pres[n].values()) for n in pres])
        miss = sorted((s, i, n) for n in pres for s in vals_by_seed for i in E - pres[n][s])
        any_incomplete |= bool(miss)
        missing += [{"family": f["label"], "member": n, "seed": s, "identity": i} for s, i, n in miss]
        fam_cov[f["label"]] = {"expected_identities": len(E), "per_seed_common": per_seed_common, "seed_mean_common": len(any_seed),
                               "all_three_seeds": len(all_seeds), "n_missing_pairs": len(miss)}
    return {"units": units, "families": fam_cov, "missing_pairs": missing, "any_incomplete": any_incomplete,
            "expected_identities": {f"{k}|{d}": len(v) for (k, d), v in sorted(expected.items())}}


def support_query_sizes(rows, census):
    """D_ADAPT n_support / n_query per participant-unit block (dataset, subject fold, content fold, identity), by dataset and support
    fraction; checks that every record of a block (3 seeds x 2 adapters) and both readouts carry the same counts."""
    byid = {r["experiment_id"]: r for r in rows}
    seen = defaultdict(set)
    for eid, info in census.info.items():
        r = byid.get(eid)
        if r is None or not row_in_panel(r) or r["family_id"] != "D_ADAPT":
            continue
        for pid, d in info["participants"].items():
            for sf in DL.SUPPORTS:
                u, nat = d.get(f"{sf}|unified"), d.get(f"{sf}|native")
                if u is not None:
                    seen[(r["dataset"], sf, r["subject_fold"], r["content_fold"], pid)].add((u[1], u[0], None if nat is None else nat[0]))
    equal = all(len(v) == 1 and next(iter(v))[1] == next(iter(v))[2] for v in seen.values())
    out = {"equal_across_seeds_adapters_and_readouts": bool(equal), "by_dataset_support": {}}
    q = lambda x: {"min": int(min(x)), "median": float(np.median(x)), "max": int(max(x))}
    for ds, sf in sorted({k[:2] for k in seen}):
        blocks = {k: v for k, v in seen.items() if k[:2] == (ds, sf)}
        ns = [t[0] for v in blocks.values() for t in v]; nq = [t[1] for v in blocks.values() for t in v]
        per_id = defaultdict(set)
        for k, v in blocks.items():
            per_id[k[4]] |= {t[0] for t in v}
        out["by_dataset_support"][f"{ds}|{sf}"] = {"blocks": len(blocks), "identities": len(per_id), "n_support": q(ns), "n_query": q(nq),
                                                   "identities_with_unequal_n_support_across_units": sum(len(v) > 1 for v in per_id.values())}
    return out


# ------------------------------------------------------------------------------------------------ QC
def qc(rows, census, vals_by_seed, grp_by_seed):
    byid = {r["experiment_id"]: r for r in rows}
    cells = defaultdict(dict)
    for r in rows:
        if row_in_panel(r):
            cells[(r["family_id"], r["seed"], r["dataset"], r["subject_fold"], r["content_fold"])][config_name(r)] = r["experiment_id"]
    bad = defaultdict(list); n = Counter()
    for k, d in sorted(cells.items(), key=str):
        fam, seed, ds, sf, cf = k
        if fam == "D_ADAPT":
            a, b = census.info.get(d.get("none")), census.info.get(d.get("input_spatial"))
            if a is None or b is None:
                bad["adapt_pair_record_missing"].append(str(k)); continue
            n["adapt_fold_pairs"] += 1
            if a["base"] != b["base"]:
                bad["adapt_base_differs"].append(str(k))
            if a["participants"] != b["participants"]:
                bad["adapt_participants_or_counts_differ"].append(str(k))
            base = byid.get(a["base"])
            if base is None or base["family_id"] != "A_LOCAL" or base["seed"] != seed or base["dataset"] != ds or (base["subject_fold"], base["content_fold"]) != (sf, cf) \
                    or base["spec"].get("architecture") != "lag_local_tokens":
                bad["adapt_base_not_same_seed_fold_local"].append(str(k))
        else:
            ms = {t: census.info.get(d.get(f"{t}|mean_score")) for t in TASKS}
            if any(v is None for v in ms.values()):
                bad["attention_pair_record_missing"].append(str(k)); continue
            n["attention_fold_pairs"] += 1
            if ms[TASKS[0]]["participants"] != ms[TASKS[1]]["participants"]:
                bad["attention_participants_or_windows_differ"].append(str(k))
            for t in TASKS:
                lt_eid, ms_eid = d.get(f"{t}|learned_temporal"), d.get(f"{t}|mean_score")
                if lt_eid is None:
                    bad["learned_temporal_row_missing"].append(f"{k}|{t}"); continue
                if lt_eid not in census.info:
                    census(lt_eid)
                lt = census.info.get(lt_eid)
                n["learned_temporal_twins"] += 1
                if lt is None:
                    bad["learned_temporal_record_not_complete"].append(f"{k}|{t}")
                elif lt["shared_model_with"] != ms_eid or lt["aw_sha256"] != ms[t]["aw_sha256"]:
                    bad["learned_temporal_not_identical_copy"].append(f"{k}|{t}")
    none_same = {}
    for s, vals in vals_by_seed.items():
        ok, cnt = True, 0
        for ds in DATASETS:
            a, b = vals.get(("AD", ds, OBJ, "none", "0.1"), {}), vals.get(("AD", ds, OBJ, "none", "0.3"), {})
            for i in set(a) & set(b):
                cnt += 1
                ok &= all(abs(a[i][m] - b[i][m]) < 1e-9 for m in AD_METRICS if m in a[i] and m in b[i])
        none_same[str(s)] = {"identical": bool(ok), "identities_checked": cnt}
    groups = defaultdict(set)
    for s, g in grp_by_seed.items():
        for k, v in g.items():
            groups[k].add(v)
    hashes = defaultdict(set)
    for eid, info in census.info.items():
        r = byid.get(eid)
        if r is not None and row_in_panel(r):
            hashes[info["family"]].add((info["code_hash"], info["target_contract"]))
    spec_bad = []
    for r in rows:
        if row_in_panel(r) and r["seed"] != SEEDS[0]:
            ref = byid.get(r.get("reference_3401_id"))
            if ref is None or ref["seed"] != SEEDS[0] or any(ref[k] != r[k] for k in ("family_id", "dataset", "subject_fold", "content_fold")) or ref["spec"] != r["spec"]:
                spec_bad.append(r["experiment_id"])
    return {"counts": dict(n), "failures": {k: v for k, v in bad.items()},
            "adapter_none_identical_across_support": none_same,
            "group_label_consistent_across_seeds": all(len(v) == 1 for v in groups.values()),
            "code_hash_and_target_contract": {f: sorted(map(list, v)) for f, v in hashes.items()},
            "code_hash_single_per_family": all(len(v) == 1 for v in hashes.values()),
            "panel_rows_spec_equal_to_reference_3401": {"checked": sum(1 for r in rows if row_in_panel(r) and r["seed"] != SEEDS[0]), "failures": spec_bad}}


def training_choices(rows, census):
    byid = {r["experiment_id"]: r for r in rows}
    out = defaultdict(Counter)
    for eid, info in census.info.items():
        r = byid.get(eid)
        if r is None or not row_in_panel(r):
            continue
        s = r["spec"]
        if r["family_id"] == "D_ADAPT" and s["adapter"] == "input_spatial":
            out[f"D_ADAPT|{r['dataset']}|input_spatial|adaptation_steps|{r['seed']}"][str(info.get("steps_chosen"))] += 1
        if r["family_id"] == "D_ATTENTION" and s["training_task"] == "alignment_plus_selection" and s["integrator"] == "mean_score":
            out[f"D_ATTENTION|{r['dataset']}|alignment_plus_selection|selection_weight|{r['seed']}"][str(info.get("chosen_sel_weight"))] += 1
    return {k: dict(v) for k, v in sorted(out.items())}


def base_checkpoints(rows, census):
    """availability of the frozen D_ADAPT bases (needed for any re-evaluation that records true-query R)."""
    byid = {r["experiment_id"]: r for r in rows}; out = defaultdict(lambda: {"bases": set(), "available": set()})
    for eid, info in census.info.items():
        r = byid.get(eid)
        if r is None or not row_in_panel(r) or r["family_id"] != "D_ADAPT" or not info.get("base_checkpoint"):
            continue
        k = str(r["seed"]); p = os.path.join(core.REPO, info["base_checkpoint"])
        out[k]["bases"].add(info["base"])
        if os.path.exists(p):
            out[k]["available"].add(info["base"])
    return {k: {"distinct_bases": len(v["bases"]), "checkpoint_present": len(v["available"])} for k, v in sorted(out.items())}


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


def reproduce_3401(vals, grp, published, per_seed_3401, fams):
    """(a) full ADDENDUM_12 families at seed 3401 vs the published d_lag.json (attention + adapt blocks), number by number;
    (b) panel-family pointwise values at 3401 vs the published values of the same members (identical draws and identities)."""
    notes = []
    att = DL.run_fams(DL.att_families(), vals, grp, ATT_METRICS, ATT_PRIMARY, notes)
    ad = DL.run_fams(DL.ad_families(), vals, grp, AD_METRICS, AD_PRIMARY, notes)
    mine = json.loads(json.dumps(BI.jl({"attention": att, "adapt": ad})))
    full = {k: compare_tree(mine[k], published[k]) for k in ("attention", "adapt")}
    for v in full.values():
        v["mismatches"] = v["mismatches"][:20]
        v.pop("n_added", None)
    pm = {"n_members": 0, "max_abs_diff": 0.0, "mismatches": []}; published_sim = {}
    for f in fams:
        pubblk = published["attention" if f["kind"] == "att" else "adapt"]
        for m in METRICS[f["kind"]]:
            pb = (pubblk["families"][f["label"]] if m == PRIMARY[f["kind"]] else pubblk["secondary"][f["label"]][m])["members"]
            mb = block(per_seed_3401, f, m)["members"]
            for name, *_ in f["members"]:
                if name not in pb or name not in mb:
                    if name in pb or name in mb:
                        pm["mismatches"].append(f"{f['label']}|{name}|{m}: present on one side only")
                    continue
                pm["n_members"] += 1
                for k in ("n", "est", "se", "ci_low", "ci_high", "pct_low", "pct_high"):
                    if k in pb[name] or k in mb[name]:
                        d = abs(float(pb[name].get(k, np.nan)) - float(mb[name].get(k, np.nan)))
                        pm["max_abs_diff"] = max(pm["max_abs_diff"], d if np.isfinite(d) else np.inf)
                        if not d <= 1e-12:
                            pm["mismatches"].append(f"{f['label']}|{name}|{m}|{k}")
                if m == PRIMARY[f["kind"]] and "sim_low" in pb[name]:
                    published_sim[f"{f['label']}|{name}"] = {"sim_low": pb[name]["sim_low"], "sim_high": pb[name]["sim_high"], "class": pb[name].get("class"),
                                                            "crit": pubblk["families"][f["label"]].get("crit"), "n_members_addendum12": f["n_members_addendum12"]}
    return {"full_families_vs_published": full, "panel_members_pointwise_vs_published": pm, "published_full_family_simultaneous": published_sim}


def non_panel_task_classes(published):
    """published seed-3401 classes of the AT-TASK members that are not in the panel (they have no seed panel)."""
    out = {}
    if not published:
        return out
    for label, f in published["attention"]["families"].items():
        if not label.startswith("AT-TASK|"):
            continue
        for name, m in f["members"].items():
            if not (in_panel(tuple(m["ref"].split("|"))) and in_panel(tuple(m["cand"].split("|")))):
                out[f"{label}|{name}"] = {"est": m.get("est"), "class": m.get("class")}
    return out


# ------------------------------------------------------------------------------------------------ analysis
def analyse(rows, load, published=None, mc_k=MC_K):
    setup()
    notes = []
    census = Census(load, rows)
    vals_by_seed, grp_by_seed, collect_status = {}, {}, {}
    for s in SEEDS:
        vals_by_seed[s], grp_by_seed[s], st = collect_seed(rows, census, s)
        collect_status[str(s)] = {f"{k[0]}|{k[1]}": v for k, v in st.items()}
    fams = panel_families()
    per_seed = {s: run_per_seed(fams, vals_by_seed[s], grp_by_seed[s], notes) for s in SEEDS}
    grp = {}
    for s in SEEDS:
        grp.update(grp_by_seed[s])
    status = Counter()
    for r in rows:  # registered panel rows not served to collect (the learned_temporal copies) are read here for status / QC
        if row_in_panel(r):
            if r["experiment_id"] not in census.status:
                census(r["experiment_id"])
            status[f"{r['family_id']}|{r['seed']}|{census.status[r['experiment_id']]}"] += 1
    seed_mean, pv = run_seed_mean(fams, vals_by_seed, grp, notes)
    cov = coverage(rows, census, vals_by_seed, fams)
    complete_case = run_seed_mean(fams, vals_by_seed, grp, notes, complete_case=True)[0] if cov["any_incomplete"] else None
    cfams, card_notes = card_families(), []
    out = {
        "families": [{k: (v if k != "members" else [[m[0], BI.ckey(m[1]), BI.ckey(m[2]), m[3]] for m in v]) for k, v in f.items()} for f in fams],
        "status": dict(sorted(status.items())), "collect_status": collect_status,
        "per_seed": {str(s): v for s, v in per_seed.items()}, "seed_mean": seed_mean, "seed_mean_complete_case": complete_case,
        "between_seed": between_seed(per_seed, fams), "coverage": cov, "qc": qc(rows, census, vals_by_seed, grp_by_seed),
        "training_choices": training_choices(rows, census), "base_checkpoints": base_checkpoints(rows, census),
        "reproduction_3401": reproduce_3401(vals_by_seed[SEEDS[0]], grp_by_seed[SEEDS[0]], published, per_seed[SEEDS[0]], fams) if published else None,
        "support_query_sizes": support_query_sizes(rows, census),
        "card_families": {"families": [{k: (v if k != "members" else [[m[0], BI.ckey(m[1]), BI.ckey(m[2]), m[3]] for m in v]) for k, v in f.items()} for f in cfams],
                          "results": run_card(cfams, vals_by_seed, card_notes), "notes": card_notes},
        "non_panel_task_classes_3401": non_panel_task_classes(published),
        "mc_stability": mc_stability(fams, cfams, vals_by_seed, mc_k) if mc_k else None,
        "notes": notes}
    if out["mc_stability"]:
        out["mc_stability"]["checks"] = mc_checks(out)
    per_identity = {"per_seed_values": {str(s): {BI.ckey(c): v for c, v in vals_by_seed[s].items() if c[0] in ("ATT", "AD") and in_panel(c)} for s in SEEDS},
                    "seed_mean_deltas": {}}
    for f in fams:
        for name, ref, cand, _ in f["members"]:
            for m in METRICS[f["kind"]]:
                per_identity["seed_mean_deltas"][f"{f['label']}|{name}|{m}"] = {i: list(v) for i, v in seed_mean_deltas(vals_by_seed, ref, cand, m).items()}
    return out, per_identity, census


# ------------------------------------------------------------------------------------------------ report
def f3(x):
    return "–" if x is None else f"{x:+.3f}"


def f4(x):
    return "–" if x is None else f"{x:+.4f}"


def iv(m, lo, hi):
    return "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"


def lab(label):
    return label.replace("|", " · ")


def _ns(out, f, name):
    ns = [out["per_seed"][str(s)]["families"][f["label"]]["members"].get(name, {}).get("n") for s in SEEDS]
    nm = out["seed_mean"]["families"][f["label"]]["members"].get(name, {}).get("n")
    return (f"{ns[0]}" if len(set(ns)) == 1 else "/".join(map(str, ns))) + ("" if nm == ns[0] and len(set(ns)) == 1 else f" → {nm}")


def primary_table(out, fams, family_names):
    L = ["| family · member | n | seed 3401 Δ [sim.] | seed 3407 Δ [sim.] | seed 3413 Δ [sim.] | between-seed range (spread) | identity mean over seeds Δ [95% CI] | identity mean [sim.] · class |",
         "|---|---|---|---|---|---|---|---|"]
    crit = []
    for f in fams:
        if f["family"] not in family_names:
            continue
        crit.append(f"{lab(f['label'])}: " + " / ".join(f"{out['per_seed'][str(s)]['families'][f['label']].get('crit', float('nan')):.2f}" for s in SEEDS)
                    + f" / mean {out['seed_mean']['families'][f['label']].get('crit', float('nan')):.2f}")
        for name, *_ in f["members"]:
            cells = []
            for s in SEEDS:
                m = out["per_seed"][str(s)]["families"][f["label"]]["members"].get(name)
                cells.append("missing" if not m or "est" not in m else f"{f3(m['est'])} {iv(m, 'sim_low', 'sim_high')} {m.get('class', '')}")
            b = out["between_seed"].get(f"{f['label']}|{name}|{PRIMARY[f['kind']]}")
            rng = "–" if not b else f"[{b['min']:+.3f}, {b['max']:+.3f}] ({b['spread']:.3f})"
            sm = out["seed_mean"]["families"][f["label"]]["members"].get(name, {})
            L.append(f"| {lab(f['label'])} · {name} | {_ns(out, f, name)} | " + " | ".join(cells) + f" | {rng} | {f3(sm.get('est'))} {iv(sm, 'ci_low', 'ci_high')} | "
                     f"{iv(sm, 'sim_low', 'sim_high')} {sm.get('class', '')} |")
    L += ["", "Critical values (3401 / 3407 / 3413 / identity mean): " + "; ".join(crit) + ".", ""]
    return L


def secondary_table(out, fams, family_names, labels):
    L = ["| family · member | readout | seed 3401 Δ [95% CI] | seed 3407 Δ [95% CI] | seed 3413 Δ [95% CI] | between-seed range | identity mean over seeds Δ [95% CI] |",
         "|---|---|---|---|---|---|---|"]
    for f in fams:
        if f["family"] not in family_names:
            continue
        for name, *_ in f["members"]:
            for m, lb in labels:
                if m not in METRICS[f["kind"]] or m == PRIMARY[f["kind"]]:
                    continue
                ms = [out["per_seed"][str(s)]["secondary"][f["label"]][m]["members"].get(name, {}) for s in SEEDS]
                if all("est" not in x for x in ms):
                    continue
                b = out["between_seed"].get(f"{f['label']}|{name}|{m}")
                rng = "–" if not b else "[{:+.3f}, {:+.3f}]".format(b["min"], b["max"])
                sm = out["seed_mean"]["secondary"][f["label"]][m]["members"].get(name, {})
                L.append(f"| {lab(f['label'])} · {name} | {lb} | " + " | ".join("–" if "est" not in x else f"{f3(x['est'])} {iv(x, 'ci_low', 'ci_high')}" for x in ms)
                         + f" | {rng} | {f3(sm.get('est'))} {iv(sm, 'ci_low', 'ci_high')} |")
    L.append("")
    return L


def group_table(out, fams, family_names):
    L = ["| family · member | per group, identity mean over seeds (pointwise; descriptive) |", "|---|---|"]
    for f in fams:
        if f["family"] not in family_names:
            continue
        for name, *_ in f["members"]:
            gs = out["seed_mean"]["families"][f["label"]]["members"].get(name, {}).get("groups", {})
            L.append(f"| {lab(f['label'])} · {name} | " + "; ".join(
                f"{g}: " + (f"{x['est']:+.3f} [{x['ci_low']:+.3f}, {x['ci_high']:+.3f}] (n={x['n']})" if "est" in x else f"n={x['n']}") for g, x in sorted(gs.items())) + " |")
    L.append("")
    return L


FAMILY_ORDER = ("AD-GAIN", "AD-SUPPORT", "AT-TASK", "AT-LEVEL", "AT-LENGTH", "AT-INTEGRATOR")
CAT_LABEL = {"below_every_width": "below every width", "between": "between", "above_every_width": "above every width"}


def width_tables(out, fams):
    L = ["Spread = max − min of the three per-seed estimates. Widths = sim_high − sim_low of each seed's simultaneous interval (declared "
         "draws). One rule for every family: *below every width* = spread smaller than the narrowest of the three widths; *above every "
         "width* = spread larger than the widest; otherwise *between*.", "",
         "| family | members | below every width | between | above every width |", "|---|---|---|---|---|"]
    rows = []
    for fam in FAMILY_ORDER:
        c, nm = Counter(), 0
        for f in fams:
            if f["family"] != fam:
                continue
            for name, *_ in f["members"]:
                b = out["between_seed"].get(f"{f['label']}|{name}|{PRIMARY[f['kind']]}", {})
                nm += 1; c[b.get("spread_vs_widths", "not computed")] += 1
                rows.append((f, name, b))
        L.append(f"| {fam} | {nm} | {c['below_every_width']} | {c['between']} | {c['above_every_width']} |")
    L += ["", "| family · member | spread | widths 3401 / 3407 / 3413 | spread ÷ narrowest width | spread ÷ widest width | category |", "|---|---|---|---|---|---|"]
    for f, name, b in rows:
        if "sim_widths" not in b:
            L.append(f"| {lab(f['label'])} · {name} | – | – | – | – | not computed |"); continue
        w = b["sim_widths"]
        L.append(f"| {lab(f['label'])} · {name} | {b['spread']:.4f} | " + " / ".join(f"{w[str(s)]:.4f}" for s in SEEDS if str(s) in w)
                 + " | " + " | ".join("–" if x is None else f"{x:.2f}" for x in (b["spread_over_narrowest_width"], b["spread_over_widest_width"]))
                 + f" | {CAT_LABEL[b['spread_vs_widths']]} |")
    L.append("")
    return L


def mc_tables(out):
    mc = out.get("mc_stability")
    if not mc:
        return ["Not computed in this run.", ""]
    k = mc["k"]
    L = [f"Every class in this document is that of the declared draws (B = 4,000 replicate index sets derived from the family label, the "
         f"metric and `sci_r1.stats.SEED` = {mc['base_seed']}). Here the same identities, estimates and families were re-run with {k} "
         f"alternative draw sets (`SEED` + {mc['seed_step']}·j, j = 1…{k}). The declared class stays the reported one; this only shows how "
         "close each class is to the Monte-Carlo margin. Checks: the declared cells of this table equal the main results and the published "
         f"full families ({mc['checks']['n_numbers']} bounds, max |Δ| {mc['checks']['max_abs_diff']:.1e}, "
         f"{len(mc['checks']['class_mismatches'])} class mismatches).", ""]
    names = {"panel": "Panel families (per seed and identity mean)", "full_addendum12": "Full ADDENDUM_12 families at seed 3401 (panel members only)",
             "card": "Card-contrast families of §1.14 (post hoc)"}
    for g in ("panel", "full_addendum12", "card"):
        blocks = mc["cells"].get(g, {})
        cells = [(blk, key, c) for blk, cs in blocks.items() for key, c in cs.items()]
        unstable = [(blk, key, c) for blk, key, c in cells if c["n_same_class"] < c["n_alternatives"]]
        L.append(f"**{names[g]}.** {len(cells) - len(unstable)} of {len(cells)} cells keep the declared class in all {k} alternative draws; "
                 + ("the others are listed." if unstable else "none differs."))
        L.append("")
        if unstable:
            L += ["| block | family · member | declared Δ bounds [sim.] · class | alternative draws with the declared class | classes over the alternatives | sim_low range | sim_high range |",
                  "|---|---|---|---|---|---|---|"]
            for blk, key, c in unstable:
                d = c["declared"]
                L.append(f"| {'identity mean' if blk == 'mean' else 'seed ' + blk} | {lab(key)} | [{d['sim_low']:+.4f}, {d['sim_high']:+.4f}] {d['class']} | "
                         f"{c['n_same_class']} / {c['n_alternatives']} | " + "; ".join(f"{a}: {b}" for a, b in c["classes"].items())
                         + f" | [{c['sim_low_range'][0]:+.4f}, {c['sim_low_range'][1]:+.4f}] | [{c['sim_high_range'][0]:+.4f}, {c['sim_high_range'][1]:+.4f}] |")
            L.append("")
    return L


def card_table(out):
    cf = out["card_families"]
    L = ["| family · member | n | seed 3401 Δ [sim.] | seed 3407 Δ [sim.] | seed 3413 Δ [sim.] | identity mean Δ [sim.] · class | one-member panel family, identity mean [sim.] · class |",
         "|---|---|---|---|---|---|---|"]
    crit = []
    for f in cf["families"]:
        res = cf["results"]
        crit.append(f"{lab(f['label'])}: " + " / ".join(f"{res[str(s)][f['label']].get('crit', float('nan')):.2f}" for s in SEEDS)
                    + f" / mean {res['mean'][f['label']].get('crit', float('nan')):.2f}")
        for name, *_ in f["members"]:
            cells = []
            for s in SEEDS:
                m = res[str(s)][f["label"]]["members"].get(name, {})
                cells.append("missing" if "est" not in m else f"{f3(m['est'])} {iv(m, 'sim_low', 'sim_high')} {m.get('class', '')}")
            mm = res["mean"][f["label"]]["members"].get(name, {})
            pl, pn = f["panel_counterpart"][name]
            pm = out["seed_mean"]["families"][pl]["members"].get(pn, {})
            L.append(f"| {lab(f['label'])} · {name} | {mm.get('n', '–')} | " + " | ".join(cells) + f" | {f3(mm.get('est'))} {iv(mm, 'sim_low', 'sim_high')} {mm.get('class', '')} | "
                     f"{iv(pm, 'sim_low', 'sim_high')} {pm.get('class', '')} |")
    L += ["", "Critical values (3401 / 3407 / 3413 / identity mean): " + "; ".join(crit) + ".", ""]
    return L


def render(out, meta):
    fams = [{**f, "members": [(m[0], tuple(m[1].split("|")), tuple(m[2].split("|")), m[3]) for m in f["members"]]} for f in out["families"]]
    cov, q, rep = out["coverage"], out["qc"], out["reproduction_3401"]
    v1 = meta.get("v1_comparison")
    v1_txt = ("not compared (no version-1 archive)" if not v1 else
              f"compared number by number with version 1 (archived in `{meta.get('v1_archive', '')}`): JSON {v1['json']['n_numbers']} numbers, max |Δ| "
              f"{v1['json']['max_abs_diff']:.1e}, {len(v1['json']['mismatches'])} mismatches, {v1['json']['n_added']} added fields; per-identity file "
              f"{v1['per_identity']['n_numbers']} numbers, max |Δ| {v1['per_identity']['max_abs_diff']:.1e}, {len(v1['per_identity']['mismatches'])} mismatches")
    L = ["# D multi-seed panel — seeds 3401 / 3407 / 3413 (R34_D_PANEL)", "",
         "<!-- Generated by `python -m auditory_alignment_v3.aln34.d_multiseed --update-doc`: the preamble, section 1, section 5 and 'Not in the "
         "panel'. Sections 2-4, 6 and 7 are written by hand after the generated tables were viewed; the generator carries them over verbatim "
         "from the previous version of this file. -->", "",
         f"**日期／代码与数据版本 (date, code and data versions).** {DOC_VERSION}, generated {meta['generated']} on `{meta['host']}` inside Slurm "
         f"allocation {meta['slurm_job']} (the session's own CPU allocation; no separately submitted job, no GPU). Code sha256: "
         + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + f". Plan files: `units.jsonl` {meta['plan_sha256']['units.jsonl'][:12]}, "
         f"`plan_ext.jsonl` {meta['plan_sha256']['plan_ext.jsonl'][:12]}. Unit-record digest {meta['record_digest'][:16]} ({meta['n_records_read']} records). "
         f"Analysis note `private/auditory_alignment_v3/aln34/D_MULTI_SEED_NOTE.md` sha256 {meta['note_sha256'][:12]} (last modified {meta['note_mtime']}, "
         f"{'before' if meta.get('note_before_run', True) else 'AFTER'} this run started; its correction section of 2026-10-16 20:34–20:36 declares "
         "the additions of this version). Version history and corrections: section 7.", "",
         f"**本轮完成／运行／待依赖 (live state).** Panel and reference rows by status: {out['status']}. No training or evaluation was run for "
         "this report; only completed unit records were read.", "",
         "**已见信息与本轮新增信息 (seen before / new).** Seen before this run: all seed-3401 D results (D_ATTENTION_RESULTS.md, D_ADAPT_RESULTS.md, "
         "D_COVERAGE_MATRIX.md), a summary check of the degenerate native learned_temporal column at 3401, version 1 of this document with every "
         "panel value, and the independent verifier's report on version 1 (which included a Monte-Carlo redraw of four cells and the "
         "AT-INTEGRATOR spread-versus-width counts). New in this version: the per-seed intervals of the secondary readouts (§1.7), the D_ADAPT "
         "support and query sizes (§1.9), the spread-versus-width table (§1.12), the Monte-Carlo stability of the classes (§1.13), the "
         "card-contrast sensitivity (§1.14) and, under 'Not in the panel', the published seed-3401 values of the non-panel AT-TASK members. "
         f"Every number of version 1: {v1_txt}.", "",
         "## 1. 当前观察 (observation)", "",
         "### Scope, units and statistics", "",
         f"- Seeds 3401 (breadth seed; the published ADDENDUM_12 units), 3407 and 3413 (ADDENDUM_03 §1.1 panel rows); `lag_local_tokens`; objective "
         "NCE; FAU and DTU; all 5 subject folds × 2 content folds. Expected test identities: "
         + ", ".join(f"{k} {v}" for k, v in cov["expected_identities"].items()) + ".",
         "- Unit of every Δ: D_ATTENTION 2AFC accuracy difference (proportion; AT-LEVEL is accuracy − 0.5); D_ADAPT `gain_bits` difference in bits per "
         f"query (query = last 70 % of each test participant's 5 s segments); rank: {RANK_UNIT}; top1 as a proportion. Positive = candidate better "
         "throughout.",
         "- n counts unique test identities. Per seed and configuration an identity's value is the mean over its units (its two content folds); the "
         "identity mean over seeds averages the within-seed paired differences over the seeds in which the pair exists. Seeds, folds and content "
         "folds never add n.",
         "- Intervals: bootstrap-t over identities (B = 4,000); [sim.] = simultaneous 95 % by max-t within the panel family (each ADDENDUM_12 family "
         "restricted to its panel members, the same member set for every seed). In a one-member family (AT-TASK, AD-GAIN, AD-SUPPORT) the "
         "simultaneous interval equals the pointwise bootstrap-t interval, so there is no multiplicity control across windows, datasets or "
         "support levels (§1.14 adds it across windows and support levels as a post hoc sensitivity). Replicate indices depend only on family "
         "label and metric, so the three seeds and the identity mean resample the same identities. Classes (I>0 / I<0 / contains 0) describe "
         "the simultaneous interval of the declared draws; §1.13 shows how stable they are under alternative draws. No p-values.",
         "- The intervals condition on the fitted models. The between-seed range is the only direct view of training randomness here, and three "
         "seeds give a coarse one (it also contains seed-dependent readout and probe sampling).", "",
         "### 1.1 Personal supervised adaptation, AD-GAIN (main table; unified gain_bits, bits per query)", ""]
    L += primary_table(out, fams, ("AD-GAIN",))
    L += ["### 1.2 Attention training task, AT-TASK (attended_alignment → alignment_plus_selection, NCE; unified mean_score accuracy)", ""]
    L += primary_table(out, fams, ("AT-TASK",))
    L += ["### 1.3 Support 10 % → 30 %, AD-SUPPORT (input_spatial; unified gain_bits)", ""]
    L += primary_table(out, fams, ("AD-SUPPORT",))
    L += ["### 1.4 Attention level above chance, AT-LEVEL (unified mean_score accuracy − 0.5)", ""]
    L += primary_table(out, fams, ("AT-LEVEL",))
    L += ["### 1.5 Window length, AT-LENGTH (unified mean_score accuracy)", ""]
    L += primary_table(out, fams, ("AT-LENGTH",))
    L += ["### 1.6 Integrator, AT-INTEGRATOR (mean_score → learned_temporal; legacy candidate order, provisional under R34_ATTENTION_ORDER)", "",
          "Every number in this subsection uses the legacy learned_temporal evaluation (test windows always presented as (attended, ignored)). "
          "The order correction of track R34_ATTENTION_ORDER can change all of them; at 5 s (one segment) learned_temporal only thresholds a single "
          "score difference.", ""]
    L += primary_table(out, fams, ("AT-INTEGRATOR",))
    L += ["### 1.7 Secondary readouts (separate from the primary; native never merged with unified, rank never merged with top-1)", "",
          "Per-seed estimates and the identity mean over seeds, each with its pointwise 95 % bootstrap-t CI (secondary readouts carry no "
          f"family max-t). Rank: {RANK_UNIT}.", ""]
    L += secondary_table(out, fams, ("AD-GAIN", "AD-SUPPORT"), (("gain_bits_native", "native gain_bits"), ("rank_pct_q", "unified Δrank proportion (ref − cand; positive = better)"),
                                                               ("top1_q", "unified top1")))
    L += secondary_table(out, fams, ("AT-TASK", "AT-LEVEL", "AT-LENGTH"), (("acc_native", "native accuracy"), ("margin", "unified mean margin")))
    L += ["Native learned_temporal (AT-INTEGRATOR, native column; degenerate at seed 3401, reported, not interpreted):", ""]
    L += secondary_table(out, fams, ("AT-INTEGRATOR",), (("acc_native", "native accuracy"),))
    L += ["### 1.8 Per-group description (identity mean over seeds; pointwise, descriptive, not a group contrast; n < 5 → n only)", ""]
    L += group_table(out, fams, ("AD-GAIN", "AT-TASK", "AT-LEVEL"))
    L += ["### 1.9 Coverage", "", "Units and identities per configuration and seed (units per identity: distribution of the number of units in "
          "which an identity is tested):", "", "| configuration | seed | units complete / registered | identities | units per identity |", "|---|---|---|---|---|"]
    for k, v in cov["units"].items():
        p = k.split("|")
        L.append(f"| {p[0]} · {p[1]} · {' · '.join(p[2:-1])} | {p[-1]} | {v['complete']} / {v['registered']} | {v['identities']} | {v['units_per_identity']} |")
    L += ["", "Paired identities per family (primary readout):", "", "| family | expected identities | per seed 3401 / 3407 / 3413 | identity mean | all three seeds | missing pairs |", "|---|---|---|---|---|---|"]
    for lb, v in cov["families"].items():
        L.append(f"| {lab(lb)} | {v['expected_identities']} | " + " / ".join(str(v['per_seed_common'][str(s)]) for s in SEEDS)
                 + f" | {v['seed_mean_common']} | {v['all_three_seeds']} | {v['n_missing_pairs']} |")
    L.append("")
    if cov["missing_pairs"]:
        L += ["Missing pairs (family, member, seed, identity) — not filled; the identity mean uses the seeds that have the pair:", ""]
        L += [f"- {m['family']} · {m['member']} · seed {m['seed']} · {m['identity']}" for m in cov["missing_pairs"][:200]]
        if len(cov["missing_pairs"]) > 200:
            L.append(f"- … {len(cov['missing_pairs']) - 200} more in the JSON")
        L.append("")
    else:
        L += ["Missing pairs: none. Every expected identity has every panel pair in every seed.", ""]
    sq = out["support_query_sizes"]
    L += ["D_ADAPT support and query sizes (5 s segments) per participant-unit block, i.e. per identity and content-fold unit. Equal across "
          f"seeds, adapters and readouts: {sq['equal_across_seeds_adapters_and_readouts']}.", "",
          "| dataset · support | blocks | identities | n_support min / median / max | n_query min / median / max | identities whose two units differ in n_support |",
          "|---|---|---|---|---|---|"]
    for k, v in sq["by_dataset_support"].items():
        a, b = v["n_support"], v["n_query"]
        L.append(f"| {lab(k)} | {v['blocks']} | {v['identities']} | {a['min']} / {a['median']:g} / {a['max']} | {b['min']} / {b['median']:g} / {b['max']} | "
                 f"{v['identities_with_unequal_n_support_across_units']} |")
    L += ["", "### 1.10 QC and reproduction of the published seed-3401 tables", ""]
    L.append(f"- Pairing checks: {q['counts']}; failures: {q['failures'] if q['failures'] else 'none'}.")
    L.append("  - D_ADAPT none vs input_spatial: the same frozen same-seed, same-fold A_LOCAL `lag_local_tokens` base, identical participants and "
             "identical n_query / n_support per support fraction and readout.")
    L.append("  - D_ATTENTION attended vs align+sel: identical participants and window counts per window length and readout; each learned_temporal "
             "record names its mean_score twin and carries an identical `attention_windows` block.")
    L.append(f"- Adapter none identical across support fractions (ADDENDUM_12 QC, all four D_ADAPT metrics): {q['adapter_none_identical_across_support']}.")
    L.append(f"- Group labels consistent across seeds: {q['group_label_consistent_across_seeds']}. One code hash and target contract per family across "
             f"seeds: {q['code_hash_single_per_family']} ({q['code_hash_and_target_contract']}).")
    L.append(f"- Panel rows whose spec equals their seed-3401 reference apart from the seed: {q['panel_rows_spec_equal_to_reference_3401']['checked'] - len(q['panel_rows_spec_equal_to_reference_3401']['failures'])}"
             f" / {q['panel_rows_spec_equal_to_reference_3401']['checked']}.")
    if rep:
        fa, fd = rep["full_families_vs_published"]["attention"], rep["full_families_vs_published"]["adapt"]
        pm = rep["panel_members_pointwise_vs_published"]
        L.append(f"- Reproduction (imported machinery, seed 3401, full ADDENDUM_12 families) vs `results/auditory_alignment_v3/d_lag/d_lag.json`: attention "
                 f"{fa['n_numbers']} numbers, max |Δ| {fa['max_abs_diff']:.1e}, {len(fa['mismatches'])} mismatches; adapt {fd['n_numbers']} numbers, max |Δ| "
                 f"{fd['max_abs_diff']:.1e}, {len(fd['mismatches'])} mismatches.")
        L.append(f"- Panel-family pointwise values at 3401 vs the published values of the same members: {pm['n_members']} member × readout blocks, max |Δ| "
                 f"{pm['max_abs_diff']:.1e}, {len(pm['mismatches'])} mismatches. Only the simultaneous intervals differ, because the published families also "
                 "contain non-panel members:")
        L += ["", "| family · member | published 3401 [sim.] (full ADDENDUM_12 family) | panel family 3401 [sim.] |", "|---|---|---|"]
        changed = []
        mcc = (out.get("mc_stability") or {}).get("cells", {})
        for k, v in rep["published_full_family_simultaneous"].items():
            label, name = k.rsplit("|", 1)
            m = out["per_seed"][str(SEEDS[0])]["families"][label]["members"].get(name, {})
            L.append(f"| {lab(label)} · {name} | [{v['sim_low']:+.3f}, {v['sim_high']:+.3f}] {v['class']} (crit {v['crit']:.2f}, {v['n_members_addendum12']} members) | "
                     f"{iv(m, 'sim_low', 'sim_high')} {m.get('class', '')} |")
            if m.get("class") != v["class"]:
                txt = (f"{lab(label)} · {name}: published {v['class']} [{v['sim_low']:+.4f}, {v['sim_high']:+.4f}] → panel family "
                       f"{m.get('class')} [{m.get('sim_low', float('nan')):+.4f}, {m.get('sim_high', float('nan')):+.4f}]")
                a, b = mcc.get("full_addendum12", {}).get(str(SEEDS[0]), {}).get(k), mcc.get("panel", {}).get(str(SEEDS[0]), {}).get(k)
                if a and b:
                    txt += (f". Under the {a['n_alternatives']} alternative draw sets of §1.13 the full-family class is {a['classes']} and the panel-family "
                            f"class is {b['classes']} (panel-family sim_low {b['sim_low_range'][0]:+.4f} … {b['sim_low_range'][1]:+.4f})")
                changed.append(txt)
        L += ["", "Seed-3401 class differences between the published full family and the panel family (same estimate, same identities, same "
              "replicate indices per label; only the family's critical value differs): " + ("; ".join(changed) if changed else "none") + ".", ""]
    L += ["### 1.11 Training-side choices (descriptive; made on training participants, not on test values)", "",
          "| choice | seed | counts over the 10 fold cells |", "|---|---|---|"]
    for k, v in out["training_choices"].items():
        p = k.split("|")
        L.append(f"| {' · '.join(p[:-1])} | {p[-1]} | {v} |")
    bc = out["base_checkpoints"]
    L += ["", f"Frozen D_ADAPT base checkpoints present on disk (for any re-evaluation): {bc}.", "",
          "### 1.12 Between-seed spread against the per-seed simultaneous widths (primary readout; descriptive)", ""]
    L += width_tables(out, fams)
    L += ["### 1.13 Monte-Carlo stability of the interval classes (exploratory; declared in the note's correction of 2026-10-16 20:34–20:36)", ""]
    L += mc_tables(out)
    L += ["### 1.14 Card contrasts with max-t across windows or support levels within a dataset (post hoc sensitivity)", "",
          "Same members, estimates and identities as the one-member panel families of §1.1 and §1.2; one family per dataset across the three "
          "windows (AT-TASK) or the two support levels (AD-GAIN), with new labels and therefore new (seed-shared) draws. No control across "
          "datasets. The declared panel families stay the main ones.", ""]
    L += card_table(out)
    L += ["## 2. 当前工作判断 (working interpretation)", "", "(written after the run)", "",
          "## 3. 仍竞争的解释 (competing explanations)", "", "(written after the run)", "",
          "## 4. 下一轮干预 (next intervention)", "", "(written after the run)", ""]
    det, mem = meta.get("determinism"), meta.get("peak_rss_mib")
    n_bases = sum(v["checkpoint_present"] for v in bc.values()); n_distinct = sum(v["distinct_bases"] for v in bc.values())
    L += ["## 5. 复用与运行 (reuse and execution)", "",
          f"- Reused: {meta['n_records_read']} completed unit records — {meta['records_by_role']['panel_3407_3413']} panel records (seeds 3407/3413), "
          f"{meta['records_by_role']['panel_3401']} distinct seed-3401 panel counterparts (each named by one 3407 and one 3413 row as "
          "`reference_3401_id`; the analysis note's \"240/240\" counts those references), and "
          f"{meta['records_by_role']['other_3401']} other seed-3401 lag_local records (D_ATTENTION mean_score rows of the CS_SINGLE and "
          "selection_only tasks, D_ADAPT CS_SINGLE and output_low_rank rows), read only for the reproduction check. New jobs: none. GPU: none.",
          f"- Run: {meta['runtime_seconds']:.0f} s wall time in the session's own 2-CPU allocation (nice 10), including the "
          f"{(out.get('mc_stability') or {}).get('k', 0)}-draw Monte-Carlo table and the determinism re-computation; measured peak resident memory "
          + ("not measured" if mem is None else f"{mem:.0f} MiB (ru_maxrss of this process)") + ".",
          "- Determinism: " + ("not checked in this run." if not det else
                               f"a second computation in the same process (same inputs, without the Monte-Carlo table) reproduced {det['json']['n_numbers']} "
                               f"numbers of the non-meta outputs (max |Δ| {det['json']['max_abs_diff']:.1e}, {len(det['json']['mismatches'])} mismatches) and "
                               f"{det['per_identity']['n_numbers']} numbers of the per-identity file (max |Δ| {det['per_identity']['max_abs_diff']:.1e}, "
                               f"{len(det['per_identity']['mismatches'])} mismatches). Replicate indices depend only on family label, metric and "
                               "`sci_r1.stats.SEED`."),
          f"- Version 1: {v1_txt}.",
          "- True-query risk R for D_ADAPT is not in the records (they store gain_bits, rank_pct, top1 and n_query per participant, support "
          "fraction and readout, plus n_support; there is no true-query logloss), so no R table is given. "
          f"Frozen same-fold bases present for an evaluation-only GPU rerun under a new execution version: {n_bases} of {n_distinct}.",
          "- Outputs (all 0600): `results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json`; this document; the private per-identity "
          "values in `private/auditory_alignment_v3/aln34/d_multiseed/per_identity.json`.",
          f"- Code: `auditory_alignment_v3/aln34/d_multiseed.py`. Synthetic tests: `{os.path.relpath(TESTS, core.REPO)}`.", "",
          "## 6. 暂不决定 (not decided here)", "", "(written after the run)", "",
          "## Not in the panel — these must not share a three-seed statement", "",
          "These configurations exist for seed 3401 only. The ADDENDUM_12 tables (D_ATTENTION_RESULTS.md, D_ADAPT_RESULTS.md) report them, but the "
          "three-seed statements of this document do not cover them.", ""]
    L += [f"- {x}" for x in NOT_IN_PANEL]
    npc = out.get("non_panel_task_classes_3401") or {}
    if npc:
        L += ["", "Published seed-3401 values of the non-panel AT-TASK members (no seed panel): "
              + "; ".join(f"{lab(k)} {f3(v['est'])} {v['class']}" for k, v in npc.items()) + "."]
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


def _plain(x):
    return json.loads(json.dumps(BI.jl(x)))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--update-doc", action="store_true", help="regenerate the results document, keeping its hand-written sections verbatim")
    a.add_argument("--mc-k", type=int, default=MC_K, help="alternative bootstrap draw sets for the Monte-Carlo table (0 = skip)")
    args = a.parse_args()
    os.umask(0o077)
    from auditory_alignment_v3 import run as r3
    t0 = time.time()
    rows = r3.all_rows(); load = BI.unit_loader()
    published = json.load(open(PUBLISHED))
    out, per_identity, census = analyse(rows, load, published, mc_k=args.mc_k)
    out2, per_identity2, _ = analyse(rows, load, published, mc_k=0)  # determinism re-computation (without the Monte-Carlo table)
    strip = lambda o: _plain({k: v for k, v in o.items() if k != "mc_stability"})
    det = {"json": compare_tree(strip(out), strip(out2)), "per_identity": compare_tree(_plain(per_identity), _plain(per_identity2))}
    for v in det.values():
        v["mismatches"] = v["mismatches"][:20]
    v1 = None
    if os.path.exists(os.path.join(V1_ARCHIVE, "d_multiseed.json")):
        old = json.load(open(os.path.join(V1_ARCHIVE, "d_multiseed.json"))); old.pop("meta", None)
        new = _plain({k: v for k, v in out.items() if k in old})
        v1 = {"json": compare_tree(new, old, one_sided=True),
              "per_identity": compare_tree(_plain(per_identity), json.load(open(os.path.join(V1_ARCHIVE, "per_identity.json"))), one_sided=True),
              "new_top_level_keys": sorted(set(out) - set(old))}
        for v in (v1["json"], v1["per_identity"]):
            v["mismatches"] = v["mismatches"][:20]
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
    meta = {"card": "R34_D_PANEL", "doc_version": DOC_VERSION, "note": os.path.relpath(NOTE, core.REPO), "note_sha256": _file_sha(NOTE),
            "note_mtime": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.path.getmtime(NOTE))), "note_before_run": os.path.getmtime(NOTE) < t0,
            "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "host": socket.gethostname(), "slurm_job": os.environ.get("SLURM_JOB_ID", "none"),
            "seeds": list(SEEDS), "n_boot": S.NB, "mc": {"k": args.mc_k, "seed_step": MC_STEP}, "runtime_seconds": None,
            "code_sha256": {f: _file_sha(os.path.join(here, *f.split("/"))) for f in ("aln34/d_multiseed.py", "d_lag_interim.py", "bc_interim.py", "sci_r1/stats.py")},
            "plan_sha256": {"units.jsonl": _file_sha(core.PLAN), "plan_ext.jsonl": _file_sha(os.path.join(core.OUT, "plan_ext.jsonl"))},
            "record_digest": dig.hexdigest(), "n_records_read": len(read), "records_by_role": {k: roles.get(k, 0) for k in ("panel_3407_3413", "panel_3401", "other_3401")},
            "published_reference": os.path.relpath(PUBLISHED, core.REPO), "tests": os.path.relpath(TESTS, core.REPO),
            "v1_archive": os.path.relpath(V1_ARCHIVE, core.REPO) if v1 else None, "v1_comparison": v1, "determinism": det,
            "not_in_panel": list(NOT_IN_PANEL), "order_affected_families": list(ORDER_AFFECTED), "card_families": list(CARD_FAMILIES)}
    meta["runtime_seconds"] = round(time.time() - t0, 1)
    meta["peak_rss_mib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    os.makedirs(RES, exist_ok=True); os.makedirs(PRIV, exist_ok=True)
    jp = os.path.join(RES, "d_multiseed.json")
    BI.write_json(jp, {"meta": meta, **out}, private=True)
    BI.write_json(os.path.join(PRIV, "per_identity.json"), per_identity, private=True)
    gen = render(out, meta)
    doc = os.path.join(DOCS, "D_MULTI_SEED_RESULTS.md")
    if args.update_doc:
        text = splice(gen, open(doc).read()) if os.path.exists(doc) else gen
    else:
        doc, text = os.path.join(RES, "D_MULTI_SEED_RESULTS.generated.md"), gen
    with open(doc, "w") as fh:
        fh.write(text)
    os.chmod(doc, 0o600)
    bad = BI.privacy_scan([jp, doc], set())
    rep = out["reproduction_3401"]
    print("doc:", doc)
    print("status:", out["status"])
    print("qc failures:", out["qc"]["failures"] or "none", "| none identical:", out["qc"]["adapter_none_identical_across_support"])
    print("reproduction:", {k: (v["n_numbers"], v["max_abs_diff"], len(v["mismatches"])) for k, v in rep["full_families_vs_published"].items()},
          "panel pointwise:", (rep["panel_members_pointwise_vs_published"]["n_members"], rep["panel_members_pointwise_vs_published"]["max_abs_diff"],
                               len(rep["panel_members_pointwise_vs_published"]["mismatches"])))
    print("coverage incomplete:", out["coverage"]["any_incomplete"], "| missing pairs:", len(out["coverage"]["missing_pairs"]))
    print("determinism:", {k: (v["n_numbers"], v["max_abs_diff"], len(v["mismatches"])) for k, v in det.items()})
    print("v1 comparison:", None if not v1 else {k: (v["n_numbers"], v["max_abs_diff"], len(v["mismatches"]), v.get("n_added")) for k, v in v1.items() if isinstance(v, dict)},
          None if not v1 else v1["new_top_level_keys"])
    print("mc checks:", (out.get("mc_stability") or {}).get("checks"))
    print("privacy scan:", "PASS" if not bad else bad, "| runtime", meta["runtime_seconds"], "s | peak rss", round(meta["peak_rss_mib"]), "MiB")
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
