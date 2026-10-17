"""ALN3.4 R34_FUSION_FUNCTION: functional re-evaluation of ALN32_SIMPLE_COMPLEMENT (SC) and ALN32_RESIDUAL (RS) from saved assets.

Source: package AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016 docs/03 sections 1-2, card R34_FUSION_FUNCTION, reference math
src/aln34_reference/residuals.py (loaded from the package by file path and used as is). Exploratory re-evaluation; the analysis
note private/auditory_alignment_v3/aln34/COMPLEMENT_FUNCTION_NOTE.md was written before any value computed here (v2 corrections:
its section "Correction 1"). Version v2 (2026-10-16); the v1 code, note, unit list, report and JSON of 20:37 are kept in
private/auditory_alignment_v3/aln34/complement_function_v1_20261016T2037/.

(i)  Same-contract table (CPU, saved per-identity records). Every compared record was scored by the same evaluator
     (auditory_alignment_v2.evaluate.evaluate_continuous: identical test queries, candidate pools and grid stride, readouts and
     temperatures fitted on training participants with the same seed stream). Rows: original direct base L0 / L1, SC local_only
     (a ridge-remapped base, not the base), the other SC variants, RS at the selected epoch, RS at epoch 0 (= base L0 exactly: the
     residual's last layer is zero-initialised), plus already-reported context rows (frozen aligned FM; true-full FM). Unified and
     native readouts are separate families. Identity-level paired differences, bootstrap-t B = 4,000, max-t within each family
     (sci_r1.stats; the ADDENDUM_05 machinery mirrored for both readouts). Positive = candidate lower risk / better. Every member
     carries its input-access label (access_tag).
(ii) RS function, four layers. L1/L2 and L3 per query need forward passes: the per-unit evaluator in complement_function_eval.py
     (GPU for FM-context units). Units that selected epoch 0 are exactly zero on L1-L3 (checked on the checkpoint). L3 at identity
     level and L4 (dev vs outer test, epoch 0 vs the selected epoch) come from the saved records; parameter-level summaries of the
     residual's last layer from the saved checkpoints.

Entry points (python -B -m auditory_alignment_v3.aln34.complement_function ...):
  --audit                        asset audit only (no result values)
  --aggregate                    CPU part + merge of finished v2 per-unit outputs -> complement_function.json + report
  --write-units                  GPU unit list + sbatch template (written, never submitted by this module)
  --unit EID [--device D]        per-unit forward-pass evaluator; --tiny / --dev-only for CPU engineering checks
  --units-file F [--device D]    worker loop over a unit list: atomic claims, --shard K/N, at most --max-tries failures per unit
Not part of any training code hash; frozen modules are imported, never edited."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import complement_function_eval as EV
from auditory_alignment_v3.aln34.complement_function_eval import (  # noqa: F401  (re-exported evaluator API)
    LAYER3, LAYER12, PKG34, QMETRICS, READOUTS, REF_RESIDUALS, REPO, REPRO_KEYS, REPRO_TOL, RES, SEED, UNITS_DIR, Limits, SplitReps,
    _jl, _write_json, all_rows, build_unit, evaluate_unit, layer_rows_for, loader, metrics_from_queries, per_query_eval, query_logloss_bits,
    query_ranks, rank_change, reference_residuals, reproduces, residual_rows, residual_summary, rs_key, sha256, true_scores)
from auditory_alignment_v3.sci_r1 import stats as S

with open(__file__, "rb") as _fh:
    _SOURCE = _fh.read()  # the source this process loaded (EV.snapshot_code writes it from memory)
MODULE_SHA256 = hashlib.sha256(_SOURCE).hexdigest()
EV.register_cli(_SOURCE, MODULE_SHA256)

UNITS_V1_DIR = os.path.join(RES, "units")  # v1 outputs: kept, not merged
SNAP_DIR = os.path.join(RES, "code_snapshots")
DOC = os.environ.get("CF_DOC", os.path.join(REPO, "docs", "auditory_alignment_v3", "COMPLEMENT_FUNCTION_REPORT.md"))
NOTE = os.path.join(core.OUT, "aln34", "COMPLEMENT_FUNCTION_NOTE.md")
UNITS_TXT = os.path.join(core.OUT, "aln34", "complement_function_units.txt")
SBATCH_TXT = os.path.join(core.OUT, "aln34", "complement_function_gpu.sbatch")
V1_COPY = os.path.join(core.OUT, "aln34", "complement_function_v1_20261016T2037")
FROZEN_RS_JSON = os.path.join(REPO, "results", "auditory_alignment_v3", "aln32_residual", "aln32_residual.json")
FROZEN_SC_JSON = os.path.join(REPO, "results", "auditory_alignment_v3", "aln32_complement", "aln32_simple_complement.json")
PY = "/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python"
EID_RE = re.compile(r"(ALN3X?_[0-9a-f]{16})")
MAX_TRIES = 3
DS = ("fau", "dtu", "federici")
TARGET = {"fau": "local", "dtu": "local", "federici": "envelope"}
ARCH = ("cbramod", "reve")
OBJS = ("NCE", "CS_SINGLE")
SC_VARIANTS = ("local_only", "local_refit_capacity", "aligned_pretrained", "aligned_random", "small_context", "concat")  # complement32.VARIANTS
SC_CONTEXT_VARIANTS = ("aligned_pretrained", "aligned_random", "small_context", "concat")  # read the aligned window (complement32.Featurizer)
SC_FM_FREE = ("local_only", "local_refit_capacity", "small_context")  # read no FM feature: the cbramod and reve unit of a cell share the inputs
RS_CONF = [("residual_aligned_pretrained", a) for a in ARCH] + [("residual_aligned_random", a) for a in ARCH] + [("residual_small_capacity", "small_capacity_branch")]
TF_CONTEXT = [("pretrained_full", "full_onestep_v1", 1e-05), ("pretrained_full", "full_onestep_v1", 0.0003)]
TABLE_METRICS = tuple(f"{rd}/{m}" for rd in READOUTS for m in ("regular/logloss_bits", "regular/rank_pct", "regular/top1", "gain_bits"))
DIRECTION34 = {k: ("higher" if k.endswith(("top1", "gain_bits")) else "lower") for k in TABLE_METRICS}
PRIMARY34 = {rd: f"{rd}/regular/logloss_bits" for rd in READOUTS}
SECONDARY34 = {rd: (f"{rd}/regular/rank_pct", f"{rd}/regular/top1", f"{rd}/gain_bits") for rd in READOUTS}


# ================================================================================================ configurations and access
def cfg34(r):
    """Plan row (or SC pseudo-row) -> configuration key of the same-contract table (seed 3401 only)."""
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if r["seed"] != SEED or ds not in DS:
        return None
    o = s.get("objective")
    if f in ("A_LOCAL", "ALN32_LOCAL_SUPPORT", "ALN32_SIMPLE_COMPLEMENT", "ALN32_RESIDUAL", "B_ALIGNED", "ALN32_TRUE_FULL") and s.get("target") not in (None, TARGET[ds]):
        if f != "A_LOCAL":
            raise ValueError(f"{r['experiment_id']}: target {s.get('target')} != registered {TARGET[ds]} for {ds}")
        return None  # A_TARGETS-style rows are a different configuration
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32 and o in OBJS:
        return ("L0", ds, o)
    if f == "ALN32_LOCAL_SUPPORT" and s.get("variant") == "local_aligned1000":
        return ("L1", ds, o)
    if f == "ALN32_SIMPLE_COMPLEMENT" and "variant" in s:
        return ("SC", ds, "NCE", s["architecture"], s["base"], s["variant"])
    if f == "ALN32_RESIDUAL":
        return ("RS", ds, o, s["architecture"], s["variant"])
    if f == "B_ALIGNED" and s.get("adaptation") == "pretrained_frozen" and o == "NCE":
        return ("FM", ds, o, s["architecture"], "pretrained_frozen")
    if f == "ALN32_TRUE_FULL" and o == "NCE" and (s.get("adaptation"), s.get("recipe"), float(s.get("lr_backbone", -1))) in TF_CONTEXT:
        return ("TF", ds, o, s["architecture"], s["adaptation"], s["recipe"], float(s["lr_backbone"]))
    return None


def access_tag(cfg):
    """EEG access of a candidate relative to the base it is compared with (complement32.Featurizer / residual32.Rows):
    L0 reads [0, post); L1 and every context feature read the query-aligned window [-0.4 s, post)."""
    if cfg[0] == "SC":
        base, v = cfg[4], cfg[5]
        if v == "local_only":
            return "remap only (the base's own input)"
        if v == "local_refit_capacity":
            return "access-matched (the base's own tokens)"
        return "access-matched (aligned window = L1's window)" if base == "L1" else "context-assisted (adds [-0.4 s, 0) to L0's [0, post))"
    if cfg[0] == "RS":
        return "context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0)"
    return ""


def ckey(c):
    return "|".join(map(str, c))


def expand_rows(rows, load):
    """SC records hold six variant evaluations: pseudo-units '<id>|<variant>' (as aln32_complement_interim.expand)."""
    out, extra = [], {}
    for r in rows:
        if r["family_id"] != "ALN32_SIMPLE_COMPLEMENT":
            out.append(r); continue
        if r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        for v in SC_VARIANTS:
            e = f"{r['experiment_id']}|{v}"
            out.append({**r, "experiment_id": e, "spec": {**r["spec"], "variant": v}})
            if rec is not None:
                extra[e] = {"status": rec.get("status"), "eval": (rec.get("eval_variants") or {}).get(v)} if rec.get("status") == "complete" else {"status": rec.get("status")}
    return out, (lambda eid: extra[eid] if eid in extra else load(eid))


def load_values(rows, load, manifest, cfg_fn=cfg34, metrics=TABLE_METRICS):
    """Per identity and configuration: mean over the identity's units (bc_interim.load_continuous rules: Federici records ->
    subject_uid by the entity manifest, phantom excluded; every HC-v record has its own subject_uid), for both readouts."""
    from auditory_alignment.aggregate import unit_rows
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    grp, kind, counts, units, notes, status = {}, {}, defaultdict(dict), defaultdict(list), [], Counter()
    for r in rows:
        c = cfg_fn(r)
        if c is None:
            continue
        rec = load(r["experiment_id"])
        st = "missing" if rec is None else rec.get("status")
        status[(c[0], st)] += 1
        if st != "complete" or not rec.get("eval"):
            notes.append(f"{r['experiment_id']} {'|'.join(map(str, c))}: status {st}"); continue
        units[c].append(r["experiment_id"])
        fold = (r["subject_fold"], r["content_fold"])
        if fold in counts[c]:
            raise ValueError(f"two units for configuration {c} fold {fold}")
        counts[c][fold] = {pid: tuple((v[f"{rd}/regular"]["n_candidates"], v[f"{rd}/regular"]["n_queries"]) for rd in READOUTS)
                           for pid, v in rec["eval"]["per_participant"].items()}
        ds = r["dataset"]
        for pid, v in unit_rows(rec).items():
            if ds == "federici":
                if pid not in manifest:
                    raise KeyError(f"Federici record {pid} not in entity manifest")
                ident, g, k = manifest[pid]
            else:
                ident, g, k = pid, v.get("group"), "human"
            grp[(ds, ident)] = g if g is not None else grp.get((ds, ident)); kind[(ds, ident)] = k
            for m in metrics:
                x = v.get(m)
                if x is not None:
                    acc[c][ident][m].append(float(x))
    vals = {c: {i: {m: float(np.mean(x)) for m, x in d.items()} for i, d in per.items() if kind[(c[1], i)] == "human"} for c, per in acc.items()}
    return {"vals": vals, "grp": grp, "counts": counts, "units": units, "status": status, "notes": notes,
            "n_phantom_entities": {ds: len({i for (d, i), k in kind.items() if d == ds and k != "human"}) for ds in DS}}


def manifest_identities(manifest):
    """Federici entity manifest: records and identities by condition (each HC-v record has its own subject_uid)."""
    hum = [(rid, v) for rid, v in manifest.items() if v[2] == "human"]
    by = defaultdict(set)
    for _, (uid, cond, _) in hum:
        by[cond].add(uid)
    return {"human_records": len(hum), "human_identities": len({v[0] for _, v in hum}), "identities_by_condition": {k: len(v) for k, v in sorted(by.items())},
            "uids_shared_across_conditions": sorted(set.intersection(*by.values())) if len(by) > 1 else [],
            "non_human_records": sum(1 for v in manifest.values() if v[2] != "human"),
            "non_human_entities": len({v[0] for v in manifest.values() if v[2] != "human"})}


def pair_ok(data, ref, cand):
    """bc_interim.pair_ok for both readouts: same folds, participants, candidate and query counts."""
    a, b = data["counts"].get(ref), data["counts"].get(cand)
    if not a or not b:
        return "missing configuration"
    if set(a) != set(b):
        return f"fold sets differ ({len(a)} vs {len(b)})"
    for f in a:
        if set(a[f]) != set(b[f]):
            return f"participant sets differ in fold {f}"
        if any(a[f][p] != b[f][p] for p in a[f]):
            return f"candidate / query counts differ in fold {f}"
    return None


def cls(lo, hi):
    return "I>0" if lo > 0 else ("I<0" if hi < 0 else "contains 0")


def member_values(vals, ref, cand, metric):
    a, b = vals.get(ref, {}), vals.get(cand, {})
    out = {}
    for i in set(a) & set(b):
        x, y = a[i].get(metric), b[i].get(metric)
        if x is not None and y is not None and np.isfinite(x) and np.isfinite(y):
            out[i] = (x - y) if DIRECTION34[metric] == "lower" else (y - x)
    return out


def run_family(label, members, vals, metric, notes, simultaneous=True):
    """bc_interim.run_family (identity bootstrap-t, family max-t on the common identities, shared replicate indices) for the
    metrics of both readouts; with the same label and the unified primary it reproduces the frozen families exactly."""
    Ys = {m[0]: member_values(vals, m[1], m[2], metric) for m in members}
    present = [m for m in members if Ys[m[0]]]
    for m in members:
        if not Ys[m[0]]:
            notes.append(f"{label}/{m[0]}/{metric}: no paired identities")
    res = {"metric": metric, "members": {}}
    if not present:
        return res
    common = sorted(set.intersection(*[set(Ys[m[0]]) for m in present]))
    idx = S.draws(len(common), S.NB, S.group_seed(label, metric)) if len(common) >= 3 else None
    items = {}
    for name, ref, cand, tag in present:
        Y = Ys[name]
        if len(Y) != len(common):
            notes.append(f"{label}/{name}/{metric}: {len(Y)} paired identities, family common set {len(common)}")
        y = np.array([Y[i] for i in common])
        s = S.summary(y, idx=idx) if idx is not None else {"n": len(common), "note": "fewer than 3 identities"}
        r = {"ref": ckey(ref), "cand": ckey(cand), "tag": tag, "n": int(len(common))}
        if "est" in s:
            r.update({k: float(s[k]) for k in ("est", "se", "ci_low", "ci_high", "pct_low", "pct_high")})
            items[name] = (s["est"], s["se"], s["T"])
        res["members"][name] = r
    if simultaneous and items:
        fm = S.family_maxt(items)
        res["crit"] = fm["crit"]
        for name, iv in fm["intervals"].items():
            res["members"][name].update({"sim_low": iv["sim_low"], "sim_high": iv["sim_high"], "class": cls(iv["sim_low"], iv["sim_high"])})
    return res


def families34():
    """-> [(family, scope, {readout: label}, members)]; members (name, reference cfg, candidate cfg, access tag)."""
    out = []
    for ds in DS:
        for a in ARCH:
            for base in ("L0", "L1"):
                ref = (base, ds, "NCE")
                mem = [(v, ref, ("SC", ds, "NCE", a, base, v), access_tag(("SC", ds, "NCE", a, base, v))) for v in SC_VARIANTS]
                sc = f"{ds}|{a}|{base}"
                out.append(("FN-DIRECT-SC", sc, {rd: f"FN-DIRECT-SC|{sc}|{rd}" for rd in READOUTS}, mem))
        for o in OBJS:
            sc = f"{ds}|{o}"
            mem = [(f"{a}/{v}", ("L0", ds, o), ("RS", ds, o, a, v), access_tag(("RS", ds, o, a, v))) for v, a in RS_CONF]
            out.append(("FN-RS", sc, {"unified": f"RS-VALUE|{sc}", "native": f"FN-RS-NATIVE|{sc}"}, mem))
    return out


def same_contract(rows, load, manifest):
    data = load_values(rows, load, manifest)
    notes = list(data["notes"]); vals = data["vals"]
    out = {"families": {}, "secondary": {}, "excluded_pairs": [], "pairing": Counter()}
    for fam, sc, labels, members in families34():
        keep = []
        for m in members:
            why = pair_ok(data, m[1], m[2])
            out["pairing"]["matched" if why is None else "excluded"] += 1
            (out["excluded_pairs"].append(f"{fam}|{sc}/{m[0]}: {why}") if why else keep.append(m))
        for rd in READOUTS:
            lab = labels[rd]
            out["families"][lab] = {"family": fam, "scope": sc, "readout": rd, **run_family(lab, keep, vals, PRIMARY34[rd], notes, True)}
            out["secondary"][lab] = {m: run_family(f"{lab}|sec", keep, vals, m, notes, False) for m in SECONDARY34[rd]}
    lev = {}
    for c in sorted(vals, key=ckey):
        v = vals[c]; r = {"n": len(v)}
        for m in TABLE_METRICS:
            ids = sorted(i for i in v if m in v[i] and np.isfinite(v[i][m]))
            if not ids:
                continue
            y = np.array([v[i][m] for i in ids])
            if m in PRIMARY34.values() and len(y) >= 3:
                s = S.summary(y, seed=S.group_seed("fn-levels", ckey(c), m))
                r[m] = {"n": len(y), **{k: float(s[k]) for k in ("est", "ci_low", "ci_high")}}
            else:
                r[m] = {"n": len(y), "est": float(y.mean())}
        lev[ckey(c)] = r
    out["levels"] = lev
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": n for k, n in data["status"].items()}, "units": {ckey(c): len(u) for c, u in data["units"].items()},
                       "n_phantom_entities": data["n_phantom_entities"]}
    out["pairing"] = dict(out["pairing"])
    out["notes"] = notes
    return out, data


# ================================================================================================ access, budgets, copies, regression
def access_table(rows, load):
    """Input windows actually recorded per family and dataset (half-open, samples at the dataset rate)."""
    seen = defaultdict(set); fs = {}
    for r in rows:
        if r["seed"] != SEED or r["dataset"] not in DS:
            continue
        f = r["family_id"]
        if f == "ALN32_SIMPLE_COMPLEMENT":
            k = "SC"
        else:
            c = cfg34(r)
            k = c[0] if c else None
        if k is None:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        rc = rec.get("resolved_config") or {}
        if rc.get("fs"):
            fs[r["dataset"]] = rc["fs"]
        if k in ("L0", "L1"):
            w = str(rec.get("windows_samples"))
        elif k in ("SC", "RS"):
            w = str(rec.get("window_samples"))
        else:
            w = f"{rec.get('window_s')} s ({rec.get('window_native_samples')} samples)"
        seen[(k, r["dataset"])].add(w)
    return {"windows": {f"{k}|{ds}": sorted(v) for (k, ds), v in sorted(seen.items())}, "fs": fs,
            "reads": {"L0": "EEG [0, post): the lag_local_tokens full window (post-only)",
                      "L1": "EEG [-pre, post): the same encoder recipe on the query-aligned window",
                      "SC local_only": "the base's input only (ridge on the base output u)",
                      "SC local_refit_capacity": "the base's input only (ridge on u + the base encoder's own tokens)",
                      "SC aligned_pretrained / aligned_random": "the base's input + frozen FM tokens of [-pre, post)",
                      "SC small_context": "the base's input + the raw window [-pre, post)",
                      "SC concat": "the base's input + pretrained FM tokens of [-pre, post) (joint ridge)",
                      "RS (every variant)": "L0's input + a context branch on [-pre, post) (FM tokens or a small conv)",
                      "FM / TF context rows": "the query-aligned window [-0.4 s, +0.6 s)"},
            "source": "complement32.Featurizer (u, tok on bt.patches; raw / FM on masked_windows(E, e, -pre, post)); residual32.Rows; record fields"}


# budget constants read from the frozen sources (so the report states what the code does, not a copied literal)
PAT_PCA_RNG = r"default_rng\(GROUP_SEED \+ (\d+)\)\.choice"                    # complement32.run: PCA subsample
PAT_SC_ANCHORS = r"bt\.rows\(units\[k:k \+ 64\], rng, anchors=(\d+)\)"          # complement32.run: ridge rows per segment
PAT_UNI_ALPHAS = r"ua = (np\.logspace\([^)]*\))"                                   # ev1.Readouts: unified bridge alpha grid
PAT_CAL_QUERIES = r"size=min\((\d+), len\(q_es\)\)"                             # ev1.evaluate_continuous: calibration queries
PAT_PCA_NITER = r"pca_lowrank\(.*?niter=(\d+)\)"                                 # complement32.Featurizer.fit_pca
PAT_DEV_RNG = r"rng_d = np\.random\.default_rng\(GROUP_SEED \+ (\d+)\)"            # residual32.fit_residual: development draw
PAT_DEV_N = r"rng_d\.choice\(dv, size=min\((\d+), len\(dv\)\)"                    # residual32.fit_residual: development segments
PAT_CAL_N = r"rng_d\.choice\(tr_es, size=min\((\d+), len\(tr_es\)\)"              # residual32.fit_residual: temperature segments


def _src_int(fn, pattern):
    try:
        m = re.search(pattern, inspect.getsource(fn))
        return m.group(1) if m else None
    except (OSError, TypeError):
        return None


def budgets(rows, load):
    """Identities, content and row budgets of every fitted part (docs/03 §1: 记录桥、PCA、温度所用身份／内容及预算), from records and the
    frozen modules' constants."""
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v3 import complement32 as C32
    from auditory_alignment_v3 import residual32 as R32
    sc, rs = defaultdict(list), defaultdict(list)
    for r in rows:
        if r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        if r["family_id"] == "ALN32_SIMPLE_COMPLEMENT":
            sc[(r["dataset"], r["spec"]["base"])].append(rec)
        elif r["family_id"] == "ALN32_RESIDUAL":
            rs[(r["dataset"], r["spec"]["variant"])].append(rec)
    rng_ = lambda L, k: [min(x[k] for x in L), max(x[k] for x in L)]
    sig = inspect.signature(ev1.Readouts.__init__).parameters
    out = {"SC": {f"{ds}|{b}": {"records": len(L), "n_fit_rows": rng_(L, "n_fit_rows"), "n_train_participants": rng_(L, "n_train_participants"),
                                "n_pca_rows": sorted({x["n_pca_rows"] for x in L}), "k_pca": sorted({x["k_pca"] for x in L}),
                                "groups": sorted({x["groups"] for x in L}), "base_trained_on_all_groups": all(x.get("base_trained_on_all_groups") for x in L),
                                "alpha_grid": sorted({tuple(x["alpha_grid"]) for x in L})[0] if L else None}
                  for (ds, b), L in sorted(sc.items())},
           "SC_code": {"K_PCA": C32.K_PCA, "N_PCA_ROWS": C32.N_PCA_ROWS, "N_GROUPS": C32.N_GROUPS, "GROUP_SEED": C32.GROUP_SEED,
                       "pca_subsample_rng": f"GROUP_SEED + {_src_int(C32.run, PAT_PCA_RNG)}",
                       "pca": f"torch.pca_lowrank (randomised, niter = {_src_int(C32.Featurizer.fit_pca, PAT_PCA_NITER)}) per block tok / raw / fm_pretrained / fm_random",
                       "anchors_per_training_segment": _src_int(C32.run, PAT_SC_ANCHORS),
                       "training_rows": "fit + es segments of the outer-fold training participants (complement32.run: units = fit + es)",
                       "alpha_selection": f"grouped CV over the {C32.N_GROUPS} participant groups (correlation), residual ridges on out-of-fold base predictions"},
           "RS": {f"{ds}|{v}": {"records": len(L), "n_train_segments": rng_(L, "n_train_segments"), "n_dev_segments": sorted({x["n_dev_segments"] for x in L}),
                               "n_cal_segments": sorted({x["n_cal_segments"] for x in L}), "dev_group": sorted({x["dev_group"] for x in L}),
                               "epochs": sorted({x["epochs"] for x in L}), "trainable_params": sorted({x["trainable_params"] for x in L})}
                  for (ds, v), L in sorted(rs.items())},
           "RS_code": {"Q_anchors_per_segment": R32.Q, "N_SEG_batch_segments": R32.N_SEG, "GROUP_SEED": R32.GROUP_SEED, "DEV_GROUP": R32.DEV_GROUP,
                       "N_GROUPS": R32.N_GROUPS, "EPOCHS": R32.EPOCHS, "dev_rng": f"GROUP_SEED + {_src_int(R32.fit_residual, PAT_DEV_RNG)}",
                       "training_rows": f"fit segments of training participants outside group {R32.DEV_GROUP}",
                       "development": f"<= {_src_int(R32.fit_residual, PAT_DEV_N)} fit + es segments of group {R32.DEV_GROUP} (training participants)",
                       "dev_temperature": f"<= {_src_int(R32.fit_residual, PAT_CAL_N)} es segments outside group {R32.DEV_GROUP}, against their own pool",
                       "selection": "lowest development risk over epochs 0..E (epoch 0 = the base)"},
           "evaluator": {"readout_segments": sig["n_seg"].default, "readout_rng": "seed + 1000 (auditory_alignment_v2.evaluate.evaluate_continuous)",
                         "readout_rows": "all grid anchors of fit + es segments of the outer-fold training participants",
                         "unified_alpha_grid": _src_int(ev1.Readouts.__init__, PAT_UNI_ALPHAS),
                         "unified_alpha_selection": "fit rows -> es rows, mean per-dimension correlation; refit on fit + es rows",
                         "native_CS_SINGLE_alpha_grid": "np.logspace(-3, 3, 7)" if np.allclose(sig["alphas"].default, np.logspace(-3, 3, 7)) else str(sig["alphas"].default),
                         "native_NCE": "fixed dot product u . v (no fitted parameter)",
                         "calibration_queries": _src_int(ev1.evaluate_continuous, PAT_CAL_QUERIES),
                         "calibration": "one temperature per readout on training es queries against the es candidate pool",
                         "test": "all single-speaker test segments of the fold's test participants on the dense grid; candidates = unique test stimuli"}}
    return out


def sc_backbone_copies(rows, load, vals):
    """SC variants that read no FM feature appear in the cbramod and in the reve unit of each cell. Per dataset x base x variant:
    unit pairs, pairs with equal ridge alpha, max per-participant |Δ log-loss| between the two records, and max per-identity |ΔR| of
    the identity-level values entering the families."""
    by = defaultdict(dict)
    for r in rows:
        if r["family_id"] != "ALN32_SIMPLE_COMPLEMENT" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if rec and rec.get("status") == "complete":
            by[(r["dataset"], r["spec"]["base"], r["subject_fold"], r["content_fold"])][r["spec"]["architecture"]] = rec
    out = {}
    for (ds, base, _, _), d in sorted(by.items()):
        if set(d) != set(ARCH):
            continue
        for v in SC_VARIANTS:
            o = out.setdefault(f"{ds}|{base}|{v}", {"unit_pairs": 0, "alpha_equal": 0, **{f"max_participant_abs_diff_{rd}": 0.0 for rd in READOUTS}})
            a, b = d["cbramod"], d["reve"]
            o["unit_pairs"] += 1; o["alpha_equal"] += int(a["fit"][v]["alpha_rel"] == b["fit"][v]["alpha_rel"])
            ea, eb = a["eval_variants"][v]["per_participant"], b["eval_variants"][v]["per_participant"]
            for rd in READOUTS:
                dd = [abs(ea[p][f"{rd}/regular"]["logloss_bits"] - eb[p][f"{rd}/regular"]["logloss_bits"]) for p in set(ea) & set(eb)]
                o[f"max_participant_abs_diff_{rd}"] = max(o[f"max_participant_abs_diff_{rd}"], max(dd) if dd else 0.0)
    for k, o in out.items():
        ds, base, v = k.split("|")
        A, B = vals.get(("SC", ds, "NCE", "cbramod", base, v), {}), vals.get(("SC", ds, "NCE", "reve", base, v), {})
        for rd in READOUTS:
            m = PRIMARY34[rd]
            dd = [abs(A[i][m] - B[i][m]) for i in set(A) & set(B) if m in A[i] and m in B[i]]
            o[f"max_identity_abs_diff_{rd}"] = max(dd) if dd else None
        o["reads_fm"] = v not in SC_FM_FREE
    return out


def access_class(tag):
    t = (tag or "").lower()
    return ("remap only" if t.startswith("remap only") else "context-assisted" if "context-assisted" in t else
            "access-matched" if "access-matched" in t else "no access label")


def regression_checks(table, v1_json=None):
    """(a) RS-VALUE families vs the frozen aln32_residual.json; (b) SC level estimates vs the frozen aln32_simple_complement.json;
    (c) every family member and level vs the v1 output of this lane (only the tags were meant to change)."""
    out = {}
    if os.path.exists(FROZEN_RS_JSON):
        fr = json.load(open(FROZEN_RS_JSON)); mx, ncls, n = 0.0, 0, 0
        for lab, f in fr["families"].items():
            if not lab.startswith("RS-VALUE|"):
                continue
            for name, m in f["members"].items():
                mm = table["families"][lab]["members"][name]; n += 1
                mx = max(mx, *[abs(m[k] - mm[k]) for k in ("est", "ci_low", "ci_high", "sim_low", "sim_high")])
                ncls += int(m["class"] != mm["class"])
        out["rs_value_vs_frozen"] = {"members": n, "max_abs_diff": mx, "class_mismatches": ncls, "file": os.path.relpath(FROZEN_RS_JSON, REPO)}
    if os.path.exists(FROZEN_SC_JSON):
        fr = json.load(open(FROZEN_SC_JSON)); mx, n = 0.0, 0
        for k, lv in fr["levels"].items():
            mine = table["levels"].get(k)
            if not mine:
                continue
            for m in PRIMARY34.values():
                if m in lv and m in mine:
                    mx = max(mx, abs(lv[m]["est"] - mine[m]["est"])); n += 1
        out["sc_levels_vs_frozen"] = {"values": n, "max_abs_diff_est": mx, "file": os.path.relpath(FROZEN_SC_JSON, REPO)}
    if v1_json and os.path.exists(v1_json):
        v1 = json.load(open(v1_json))["same_contract"]; mx, ncls, n, ntag = 0.0, 0, 0, 0; acc = Counter()
        for lab, f in v1["families"].items():
            for name, m in f["members"].items():
                mm = table["families"][lab]["members"][name]; n += 1
                a1, a2 = access_class(m["tag"]), access_class(mm["tag"])
                if a1 != a2:
                    acc[f"{a1} -> {a2}"] += 1
                mx = max([mx] + [abs(m[k] - mm[k]) for k in ("est", "ci_low", "ci_high", "sim_low", "sim_high") if k in m and k in mm])
                ncls += int(m.get("class") != mm.get("class")); ntag += int(m["tag"] != mm["tag"])
        lmx = max([abs(v["est"] - table["levels"][k][m]["est"]) for k, lv in v1["levels"].items() for m, v in lv.items()
                   if isinstance(v, dict) and "est" in v and "est" in (table["levels"].get(k) or {}).get(m, {})], default=None)
        nrc = sum(1 for lab, f in v1["families"].items() if f.get("family") == "FN-DIRECT-SC" and f["scope"].endswith("|L0")
                  for name, m in f["members"].items() if name == "local_refit_capacity" and "context-assisted" in m["tag"])
        out["v1_vs_v2"] = {"members": n, "max_abs_diff": mx, "class_changes": ncls, "tag_changes": ntag, "levels_max_abs_diff_est": lmx,
                           "v1_refit_capacity_L0_context_tags": nrc, "access_class_changes": dict(acc),
                           "file": os.path.relpath(v1_json, REPO)}
    return out


# ================================================================================================ contract checks from records
def epoch0_identity(rows, load):
    """RS units that selected epoch 0 must reproduce the base L0 record on the outer test (same contract, r = 0)."""
    res, field_all = [], []
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        if rec.get("epoch0_max_abs_diff_vs_base") is not None:
            field_all.append(float(rec["epoch0_max_abs_diff_vs_base"]))
        if not rec.get("epoch0_selected"):
            continue
        base = load(rec["dependency"]["base"])
        mx = 0.0; mb = 0.0; n = 0
        for pid, v in rec["eval"]["per_participant"].items():
            bv = base["eval"]["per_participant"][pid]
            for rd in READOUTS:
                for m in QMETRICS:
                    d = abs(v[f"{rd}/regular"][m] - bv[f"{rd}/regular"][m]); mx = max(mx, d); n += 1
                    if f"{rd}/{m}" in REPRO_KEYS:
                        mb = max(mb, d)
        res.append({"eid": r["experiment_id"], "cfg": ckey(cfg34(r)), "base": rec["dependency"]["base"], "max_abs_diff": mx, "max_abs_diff_bounded": mb,
                    "n_values": n, "epoch0_max_abs_diff_vs_base_record": rec.get("epoch0_max_abs_diff_vs_base")})
    f0 = [u["epoch0_max_abs_diff_vs_base_record"] for u in res if u["epoch0_max_abs_diff_vs_base_record"] is not None]
    return {"units": res, "n": len(res), "max_abs_diff": max([u["max_abs_diff"] for u in res], default=None),
            "max_abs_diff_bounded": max([u["max_abs_diff_bounded"] for u in res], default=None),
            "within_tolerance": all(u["max_abs_diff_bounded"] <= REPRO_TOL for u in res),
            "record_field": {"name": "epoch0_max_abs_diff_vs_base", "epoch0_units_range": [min(f0), max(f0)] if f0 else None,
                             "all_units_range": [min(field_all), max(field_all)] if field_all else None, "n_all_units": len(field_all),
                             "where": "residual32.fit_residual at epoch 0: one training-side batch (N_SEG segments of training-fit participants x Q anchors), "
                                      "max |normalise(u_base + r) - u_base| with the zero-initialised last layer; not measured on the outer test"}}


def readout_scales(rows, load):
    """Readout temperatures fitted by the evaluator (training side): RS selected vs its base, per unit."""
    per = defaultdict(list)
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        base = load(rec["dependency"]["base"])
        a, b = rec["eval"]["readout"], base["eval"]["readout"]
        per[ckey(cfg34(r))].append({"tau_ratio_unified": a["tau"]["unified"] / b["tau"]["unified"], "tau_ratio_native": a["tau"]["native"] / b["tau"]["native"],
                                    "alpha_unified_changed": bool(a["alpha_unified"] != b["alpha_unified"]), "epoch0": bool(rec.get("epoch0_selected"))})
    out = {}
    for k, L in per.items():
        L1 = [x for x in L if not x["epoch0"]]
        out[k] = {"n_units": len(L), "n_epoch_gt0": len(L1),
                  "tau_ratio_unified_median": float(np.median([x["tau_ratio_unified"] for x in L1])) if L1 else None,
                  "tau_ratio_native_median": float(np.median([x["tau_ratio_native"] for x in L1])) if L1 else None,
                  "tau_ratio_native_range": [float(min(x["tau_ratio_native"] for x in L1)), float(max(x["tau_ratio_native"] for x in L1))] if L1 else None,
                  "frac_alpha_unified_changed": float(np.mean([x["alpha_unified_changed"] for x in L1])) if L1 else None}
    return out


# ================================================================================================ layer 4 from records
def _spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 5 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def dev_test_layer(rows, load):
    """Per RS unit: development risk at epoch 0 and at the selected epoch (saved curve) against the outer-test change of the same
    unit (RS record vs its base record, mean over the unit's test participants). Unit-level descriptives: units share training
    participants and are not independent identities; the identity-level test inference is family FN-RS."""
    units = []
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        base = load(rec["dependency"]["base"])
        curve = rec["curve"]; e0 = curve[0]; sel = int(rec["selected_epoch"])
        cs = next(c for c in curve if c["epoch"] == sel)
        if abs(cs["dev_risk_bits"] - rec["selected_dev_risk_bits"]) > 1e-9 or e0["epoch"] != 0:
            raise ValueError(f"{r['experiment_id']}: curve and selected epoch disagree")
        pids = sorted(set(rec["eval"]["per_participant"]) & set(base["eval"]["per_participant"]))
        d = {}
        for rd in READOUTS:
            d[f"d_test_R_{rd}"] = float(np.mean([base["eval"]["per_participant"][p][f"{rd}/regular"]["logloss_bits"] - rec["eval"]["per_participant"][p][f"{rd}/regular"]["logloss_bits"] for p in pids]))
            d[f"d_test_rank_{rd}"] = float(np.mean([base["eval"]["per_participant"][p][f"{rd}/regular"]["rank_pct"] - rec["eval"]["per_participant"][p][f"{rd}/regular"]["rank_pct"] for p in pids]))
            d[f"test_R_base_{rd}"] = float(np.mean([base["eval"]["per_participant"][p][f"{rd}/regular"]["logloss_bits"] for p in pids]))
        devs = [c["dev_risk_bits"] for c in curve]
        units.append({"eid": r["experiment_id"], "cfg": ckey(cfg34(r)), "ds": r["dataset"], "obj": r["spec"]["objective"], "selected_epoch": sel,
                      "epochs": int(rec.get("epochs", len(curve) - 1)), "dev0": float(e0["dev_risk_bits"]), "dev_sel": float(rec["selected_dev_risk_bits"]),
                      "d_dev": float(e0["dev_risk_bits"] - rec["selected_dev_risk_bits"]), "d_dev_rank": float(e0["dev_rank"] - cs["dev_rank"]),
                      "n_epochs_below_epoch0": int(sum(x < e0["dev_risk_bits"] for x in devs[1:])), "dev_last_minus_epoch0": float(devs[-1] - devs[0]),
                      "n_test_participants": len(pids), **d})

    def summ(L):
        L1 = [u for u in L if u["selected_epoch"] > 0]
        f = lambda k, LL: float(np.mean([u[k] for u in LL])) if LL else None
        out = {"n_units": len(L), "n_epoch0": len(L) - len(L1), "selected_epoch_median": float(np.median([u["selected_epoch"] for u in L])),
               "selected_epoch_range": [min(u["selected_epoch"] for u in L), max(u["selected_epoch"] for u in L)],
               "d_dev_mean": f("d_dev", L), "d_dev_mean_epoch_gt0": f("d_dev", L1), "d_dev_rel_mean": float(np.mean([u["d_dev"] / u["dev0"] for u in L])),
               "d_dev_rank_mean": f("d_dev_rank", L), "n_epochs_below_epoch0_mean": f("n_epochs_below_epoch0", L)}
        for rd in READOUTS:
            out[f"d_test_R_{rd}_mean"] = f(f"d_test_R_{rd}", L)
            out[f"d_test_R_{rd}_rel_mean"] = float(np.mean([u[f"d_test_R_{rd}"] / u[f"test_R_base_{rd}"] for u in L]))
            out[f"frac_test_better_{rd}_epoch_gt0"] = float(np.mean([u[f"d_test_R_{rd}"] > 0 for u in L1])) if L1 else None
            out[f"spearman_d_dev_d_test_{rd}_epoch_gt0"] = _spearman([u["d_dev"] for u in L1], [u[f"d_test_R_{rd}"] for u in L1])
        out["dev_minus_test_native_mean"] = float(np.mean([u["d_dev"] - u["d_test_R_native"] for u in L]))
        return out
    by_cfg, by_scope = defaultdict(list), defaultdict(list)
    for u in units:
        by_cfg[u["cfg"]].append(u); by_scope[f"{u['ds']}|{u['obj']}"].append(u)
    return {"per_config": {k: summ(v) for k, v in sorted(by_cfg.items())}, "per_scope": {k: summ(v) for k, v in sorted(by_scope.items())}, "units": units}


# ================================================================================================ checkpoint layer
def checkpoint_layer(rows, load, out=None):
    """Residual last layer (res.residual.2) of each RS selected-epoch checkpoint: zero for epoch-0 selections (r = 0 exactly)
    and parameter norms otherwise. Parameter-level only: ||r|| needs the hidden activations (forward passes)."""
    import torch
    out = out or core.OUT
    per = defaultdict(list); bad = []
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        p = os.path.join(out, "ckpt", r["experiment_id"] + "_best.pt")
        st = torch.load(p, map_location="cpu", weights_only=True)["model"]
        W2, b2, W1 = st["res.residual.2.weight"].double(), st["res.residual.2.bias"].double(), st["res.residual.0.weight"].double()
        zero = bool((W2 == 0).all() and (b2 == 0).all())
        e0 = bool(rec.get("epoch0_selected"))
        if e0 != zero:
            bad.append(r["experiment_id"])
        per[ckey(cfg34(r))].append({"epoch0": e0, "zero_last_layer": zero, "W2_fro": float(W2.norm()), "W2_spec": float(torch.linalg.matrix_norm(W2, 2)),
                                    "b2_norm": float(b2.norm()), "W1_fro": float(W1.norm()), "n_params": int(sum(t.numel() for t in st.values()))})
        del st
    summ = {}
    for k, L in sorted(per.items()):
        L1 = [x for x in L if not x["epoch0"]]
        med = lambda key: float(np.median([x[key] for x in L1])) if L1 else None
        summ[k] = {"n_units": len(L), "n_epoch0": len(L) - len(L1), "n_zero_last_layer": int(sum(x["zero_last_layer"] for x in L)),
                   "W2_fro_median": med("W2_fro"), "W2_spec_median": med("W2_spec"), "b2_norm_median": med("b2_norm"),
                   "W2_spec_max": float(max(x["W2_spec"] for x in L1)) if L1 else None, "b2_norm_max": float(max(x["b2_norm"] for x in L1)) if L1 else None}
    return {"per_config": summ, "epoch0_vs_zero_mismatch": bad,
            "n_epoch0_units": sum(v["n_epoch0"] for v in summ.values()), "n_epoch0_with_zero_last_layer": sum(v["n_zero_last_layer"] for v in summ.values())}


# ================================================================================================ asset audit
def _link_state(p):
    if not os.path.lexists(p):
        return "absent"
    if os.path.islink(p):
        return "link" if os.path.exists(p) else "broken_link"
    return "file"


def ckpt_inventory(eids, out=None):
    """Every file in ckpt/ named by one of the ids: name patterns per unit, link states and link-target roots."""
    out = out or core.OUT
    d = os.path.join(out, "ckpt"); want = set(eids); names = defaultdict(list)
    for f in os.listdir(d):
        m = EID_RE.match(f)
        if m and m.group(1) in want:
            names[m.group(1)].append(f)
    pat, states, roots, not_one = Counter(), Counter(), Counter(), []
    for e in eids:
        fs = sorted(names.get(e, []))
        pat[" + ".join(f.replace(e, "<eid>") for f in fs) or "(none)"] += 1
        for f in fs:
            p = os.path.join(d, f); st = _link_state(p); states[st] += 1
            if st == "link":
                roots["/".join(os.path.realpath(p).split(os.sep)[:3])] += 1
        if len(fs) != 1:
            not_one.append(e)
    return {"units": len(eids), "file_patterns": dict(pat), "link_states": dict(states), "link_target_roots": dict(roots), "units_without_exactly_one_file": not_one}


def _sha256_stream(p, chunk=1 << 24):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                return h.hexdigest()
            h.update(b)


def fm_weights_check():
    """Every file listed with a sha256 in the FM fetch receipt, hashed now and compared; code repositories without hashes: presence."""
    from auditory_alignment_v2 import foundation_adapter as FA
    receipt = os.path.join(FA.FM_ROOT, "FETCH_RECEIPT.json")
    if not os.path.exists(receipt):
        return {"fetch_receipt": None}
    rc = json.load(open(receipt)); out = {"fetch_receipt": receipt, "repos": {}}
    for repo, info in rc.items():
        files = info.get("files")
        if isinstance(files, dict):
            st = {}
            for name, h in files.items():
                p = os.path.join(info["dir"], name)
                st[name] = "absent" if not os.path.exists(p) else ("match" if _sha256_stream(p) == h else "MISMATCH")
            out["repos"][repo] = {"revision": info.get("revision"), "n_files": len(st), "n_match": sum(v == "match" for v in st.values()), "files": st}
        else:
            pres = [os.path.exists(os.path.join(info["dir"], "models", f)) or os.path.exists(os.path.join(info["dir"], f)) for f in files or []]
            out["repos"][repo] = {"head": info.get("head"), "n_files": len(pres), "n_present": int(sum(pres)), "hashes_in_receipt": False}
    used = {"cbramod pretrained weights": FA.CBRAMOD_W, "reve-base weights": os.path.join(FA.REVE_DIR, "model.safetensors"),
            "reve positions": os.path.join(FA.REVE_POS, "model.safetensors")}
    out["used_by_the_evaluator"] = {k: os.path.relpath(v, FA.FM_ROOT) for k, v in used.items()}
    out["all_hashed_files_match"] = all(r.get("n_match") == r.get("n_files") for r in out["repos"].values() if "n_match" in r)
    return out


def eid_file_search(roles, roots):
    """Every file under roots whose name contains one of the ids, grouped by (role, directory, name pattern)."""
    groups = defaultdict(list)
    for root in roots:
        for dp, _, fs in os.walk(root):
            for f in fs:
                m = EID_RE.search(f)
                if m and m.group(1) in roles:
                    groups[(roles[m.group(1)], os.path.relpath(dp, REPO), f.replace(m.group(1), "<eid>"))].append(os.path.join(dp, f))
    return groups


def _npz_contents(paths):
    """Keys and shapes of the arrays (first file) and, over all files, the keys whose first dimension equals the number of
    participants listed in the paired .json ('participants') or the number of test queries ('n_queries' summed)."""
    first = None; per_part, per_query, n_ok = Counter(), Counter(), 0
    for p in paths:
        try:
            z = np.load(p, allow_pickle=False)
        except Exception as ex:  # noqa: BLE001 - reported
            return {"error": f"{type(ex).__name__}: {ex}"}
        shapes = {k: list(z[k].shape) for k in z.files}
        first = first or shapes
        j = p[:-4] + ".json"
        if os.path.exists(j):
            meta = json.load(open(j))
            n_p = len(meta.get("participants") or [])
            nq = meta.get("n_queries")
            n_q = int(sum(nq)) if isinstance(nq, list) and all(isinstance(x, (int, float)) for x in nq) else None
            n_ok += 1
            for k, sh in shapes.items():
                if sh and sh[0] == n_p:
                    per_part[k] += 1
                if sh and n_q is not None and sh[0] == n_q and n_q != n_p:
                    per_query[k] += 1
    return {"files": len(paths), "shapes_first_file": first, "files_with_json": n_ok, "first_dim_equals_participants": dict(per_part),
            "first_dim_equals_test_queries": dict(per_query)}


def file_kind(d, pattern):
    dd = "/" + d.strip("/") + "/"
    if "/probe_out" in dd:
        return "engineering probe of the runner"
    if "/aln34/" in dd:
        return "this lane's evaluator output"
    if "/pool/" in dd:
        return "scheduler marker"
    if "/sci_r1/" in dd:
        return "sci_r1 continuous-science output"
    if dd.endswith("/auditory_alignment_v3/units/") and pattern in ("<eid>.json", "<eid>.FAILED.json"):
        return "unit record"
    if dd.endswith("/ckpt/"):
        return "checkpoint"
    if dd.endswith("/logs/units/"):
        return "unit log"
    return "other"


def describe_group(role, d, pattern, paths):
    kind = file_kind(d, pattern)
    g = {"role": role, "dir": d, "pattern": pattern, "files": len(paths), "kind": kind}
    if pattern.endswith(".npz") and kind != "this lane's evaluator output":
        g["contents"] = _npz_contents(paths)
    if pattern.endswith(".json") and kind == "sci_r1 continuous-science output":
        g["json_keys"] = sorted(json.load(open(paths[0])).keys())
    return g


def audit_assets(rows=None, load=None, check_ckpt_keys=True):
    """What is on disk for SC, RS and their bases (no result values)."""
    import torch
    rows = all_rows() if rows is None else rows; load = loader() if load is None else load
    out = {}
    fam_rows = lambda f: [r for r in rows if r["family_id"] == f]
    # SC
    sc = fam_rows("ALN32_SIMPLE_COMPLEMENT"); a = Counter(); deps = set(); keys = Counter(); secs = []
    for r in sc:
        rec = load(r["experiment_id"]); st = rec.get("status") if rec else "missing"
        ck = _link_state(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt"))
        a[(r["seed"], st, ck, bool(rec and rec.get("eval_variants")), bool(rec and rec.get("fit")))] += 1
        if rec and st == "complete":
            deps.add(rec["dependency"]["base"]); secs.append(rec.get("total_seconds"))
            if check_ckpt_keys and ck in ("link", "file"):
                d = torch.load(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt"), map_location="cpu", weights_only=True)
                keys[str(tuple(sorted(d)))] += 1; keys["pca:" + ",".join(sorted(d.get("pca", {})))] += 1; del d
    out["SC"] = {"rows": len(sc), "records_complete": sum(v for k, v in a.items() if k[1] == "complete"), "variant_evaluations": len(SC_VARIANTS) * sum(v for k, v in a.items() if k[1] == "complete"),
                 "state(seed,status,ckpt,eval_variants,fit_log)": {str(k): v for k, v in a.items()}, "ckpt_keys": dict(keys),
                 "ckpt_inventory": ckpt_inventory([r["experiment_id"] for r in sc if (load(r["experiment_id"]) or {}).get("status") == "complete"]),
                 "saved": "per-identity evaluations of the six variants; ridge alphas and grouped-CV curves; PCA means and bases (ckpt)",
                 "not_saved": "ridge coefficients (closed-form; a refit with the saved PCA bases and alphas needs the training rows' features again, "
                              "FM forwards for the FM variants); per-query predictions; FM / raw features",
                 "base_dependencies": len(deps), "total_seconds_median": float(np.median([s for s in secs if s])) if secs else None}
    # RS
    rs = fam_rows("ALN32_RESIDUAL"); a = Counter(); keys = Counter(); deps = set(); sel = Counter(); per_seed = defaultdict(Counter)
    for r in rs:
        rec = load(r["experiment_id"]); st = rec.get("status") if rec else "missing"
        per_seed[r["seed"]]["rows"] += 1; per_seed[r["seed"]][st] += 1
        ck = _link_state(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt"))
        rp = _link_state(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_resume.pt"))
        a[(r["seed"], st, ck, rp)] += 1
        if rec and st == "complete":
            deps.add(rec["dependency"]["base"])
            sel[(r["seed"], "epoch0" if rec.get("epoch0_selected") else "epoch>0")] += 1
            if check_ckpt_keys and r["seed"] == SEED and ck in ("link", "file"):
                d = torch.load(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt"), map_location="cpu", weights_only=True)["model"]
                keys[str((r["spec"]["variant"], tuple(sorted({k.rsplit(".", 1)[0] for k in d}))))] += 1; del d
    rs_done = [r["experiment_id"] for r in rs if r["seed"] == SEED and (load(r["experiment_id"]) or {}).get("status") == "complete"]
    out["RS"] = {"rows": len(rs), "per_seed": {str(k): dict(v) for k, v in sorted(per_seed.items())},
                 "state(seed,status,best_ckpt,resume_ckpt)": {str(k): v for k, v in a.items()},
                 "selected_epoch": {str(k): v for k, v in sel.items()}, "ckpt_param_groups(seed 3401)": dict(keys),
                 "ckpt_inventory(seed 3401)": ckpt_inventory(rs_done),
                 "saved": "per-identity evaluation at the selected epoch; dev curve per epoch (risk, rank, temperature, train loss); selected-epoch "
                          "trainable weights (residual head + context LayerNorm/Linear or small conv; frozen encoder / backbone excluded)",
                 "epoch0": "no unit has a separate epoch-0 file: residual32 writes epoch 0 to <eid>_best.pt first and overwrites it when a later "
                           "epoch has lower development risk; for the units that selected epoch 0 the single file is the epoch-0 state (zero "
                           "last layer, see the checkpoint layer); for every other unit epoch 0 is reconstructed exactly (zero last layer -> r = 0)",
                 "not_saved": "intermediate epochs (resume file removed at completion); per-query outputs; the random-init backbone weights "
                              "(regenerated from torch.manual_seed(seed) + Backbone(random_full); checked by the development-only runs listed "
                              "under the engineering checks and by each unit's own reproduction check)",
                 "base_dependencies": len(deps)}
    # bases and context
    roles = {}
    for name, pred in (("L0 (A_LOCAL lag_local_tokens full)", lambda r: cfg34(r) is not None and cfg34(r)[0] == "L0"),
                       ("L1 (ALN32_LOCAL_SUPPORT local_aligned1000)", lambda r: cfg34(r) is not None and cfg34(r)[0] == "L1"),
                       ("FM context (B_ALIGNED pretrained_frozen NCE)", lambda r: cfg34(r) is not None and cfg34(r)[0] == "FM"),
                       ("TF context (ALN32_TRUE_FULL pretrained_full full_onestep_v1)", lambda r: cfg34(r) is not None and cfg34(r)[0] == "TF")):
        a = Counter(); eids = []
        for r in rows:
            if r["seed"] != SEED or r["family_id"] == "ALN32_SIMPLE_COMPLEMENT" or not pred(r):
                continue
            rec = load(r["experiment_id"]); st = rec.get("status") if rec else "missing"
            a[(r["dataset"], r["spec"].get("objective"), st, _link_state(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt")))] += 1
            eids.append(r["experiment_id"])
            if name[:2] in ("L0", "L1"):
                roles[r["experiment_id"]] = name[:2]
        out[name] = {"state(dataset,objective,status,ckpt)": {str(k): v for k, v in sorted(a.items())}, "ckpt_inventory": ckpt_inventory(eids)}
    # dependency closure: every SC / RS base has record + checkpoint
    missing = []
    for r in sc + rs:
        rec = load(r["experiment_id"])
        if rec and rec.get("status") == "complete":
            b = rec["dependency"]["base"]
            if not (load(b) and load(b).get("status") == "complete" and _link_state(os.path.join(core.OUT, "ckpt", b + "_best.pt")) in ("link", "file")):
                missing.append(r["experiment_id"])
    out["dependency_missing"] = missing
    out["fm_weights"] = fm_weights_check()
    # every file named by an SC / RS / base id (search by experiment id)
    for r in sc:
        roles[r["experiment_id"]] = "SC"
    for r in rs:
        roles[r["experiment_id"]] = f"RS seed {r['seed']}"
    groups = eid_file_search(roles, [os.path.join(REPO, "results", "auditory_alignment_v3"), core.OUT])
    out["files_by_id"] = [describe_group(k[0], k[1], k[2], v) for k, v in sorted(groups.items())]
    out["files_by_id_search"] = "file names containing an experiment id (regex ALN3X?_<16 hex>) under results/auditory_alignment_v3 and private/auditory_alignment_v3"
    out["per_query_prediction_files_outside_this_lane"] = [g for g in out["files_by_id"] if g["kind"] not in ("unit record", "checkpoint", "unit log", "scheduler marker",
                                                                                                             "this lane's evaluator output")
                                                           and (g.get("contents") or {}).get("first_dim_equals_test_queries")]
    return out


# ================================================================================================ merge of per-unit outputs
def collect_units(rows, load, manifest, out_dir=UNITS_DIR, ckpt=None):
    """Identity-level layer summaries per configuration from finished v2 per-unit outputs (comparable runs whose re-run reproduces
    the saved records), plus the exact zeros of epoch-0 units (checkpoint verified). Pointwise bootstrap-t intervals over identities
    (descriptive diagnostics, not a contrast family). Coverage is reported for every configuration."""
    ok, flagged, missing = [], [], []
    n_cfg, n_zero, n_run = Counter(), Counter(), Counter()
    zero_mismatch = set((ckpt or {}).get("epoch0_vs_zero_mismatch", []))
    ev_hash = Counter()
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        c = ckey(cfg34(r)); n_cfg[c] += 1
        if rec.get("epoch0_selected"):
            if r["experiment_id"] in zero_mismatch:  # a non-zero last layer at an epoch-0 selection would contradict r = 0
                flagged.append(r["experiment_id"]); continue
            ok.append(("zero", r, rec)); n_zero[c] += 1; continue
        p = os.path.join(out_dir, f"{r['experiment_id']}.json")
        if not os.path.exists(p):
            missing.append(r["experiment_id"]); continue
        u = json.load(open(p))
        if reproduces(u):
            ok.append(("run", r, u)); n_run[c] += 1
            ev_hash[(u.get("code_sha256") or {}).get("complement_function_eval.py")] += 1
        else:
            flagged.append(r["experiment_id"])
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    dev_test = defaultdict(list)
    for kind, r, u in ok:
        c = ckey(cfg34(r)); ds = r["dataset"]
        if kind == "zero":
            pids = list(u["eval"]["per_participant"])
            vals = {pid: {**{f"L12/{k}": 0.0 for k in LAYER12}, **{f"L3/{rd}/{k}": 0.0 for rd in READOUTS for k in LAYER3},
                          "L3/unified_prediction/rel_diff": 0.0, "L3/unified_prediction/zcorr": 1.0, "L3/native_prediction/rel_diff": 0.0} for pid in pids}
        else:
            vals = {}
            for pid, v in u["per_identity"].items():
                x = {f"L12/{k}": v["layers"][k] for k in LAYER12}
                for rd in READOUTS:
                    x.update({f"L3/{rd}/{k}": v["layer3"][rd][k] for k in LAYER3})
                x["L3/unified_prediction/rel_diff"] = v["layer3"]["unified_prediction"]["rel_diff"]; x["L3/unified_prediction/zcorr"] = v["layer3"]["unified_prediction"]["zcorr"]
                x["L3/native_prediction/rel_diff"] = v["layer3"]["native_prediction"]["rel_diff"]
                vals[pid] = x
            dev_test[c].append({"dev_rel_norm": u["dev"]["layers"]["relative_residual_norm_mean"], "test_rel_norm": u["test_layers"]["relative_residual_norm_mean"],
                                "dev_angle": u["dev"]["layers"]["angle_deg_mean"], "test_angle": u["test_layers"]["angle_deg_mean"],
                                "dev_post": u["dev"]["layers"]["normalized_change_mean"], "test_post": u["test_layers"]["normalized_change_mean"]})
        for pid, x in vals.items():
            if ds == "federici":
                ident, _, k = manifest[pid]
                if k != "human":
                    continue
            else:
                ident = pid
            for m, y in x.items():
                acc[c][ident][m].append(float(y))
    summary = {}
    for c in sorted(n_cfg):
        cov = n_zero[c] + n_run[c]
        summary[c] = {"n_units": n_cfg[c], "n_epoch0_zero": n_zero[c], "n_run_reproduced": n_run[c], "n_units_covered": cov, "complete": cov == n_cfg[c],
                      "coverage": "complete" if cov == n_cfg[c] else ("partial" if cov else "none")}
        if cov != n_cfg[c]:
            continue  # partial coverage: no summary (epoch-0 zeros alone would bias it)
        per = acc[c]; ids = sorted(per); summary[c]["n_identities"] = len(ids)
        for m in sorted({m for i in ids for m in per[i]}):
            y = np.array([np.mean(per[i][m]) for i in ids if m in per[i]])
            s = S.summary(y, seed=S.group_seed("fn-layers", c, m)) if len(y) >= 3 and np.ptp(y) > 0 else {"est": float(y.mean()) if len(y) else None}
            summary[c][m] = {"n": int(len(y)), **{k: float(s[k]) for k in ("est", "ci_low", "ci_high") if k in s}}
    dt = {c: {k: float(np.mean([x[k] for x in L])) for k in L[0]} | {"n_units": len(L)} for c, L in dev_test.items()}
    cnt = Counter(v["coverage"] for v in summary.values())
    return {"per_config": summary, "configs": {k: cnt.get(k, 0) for k in ("complete", "partial", "none")}, "dev_vs_test_units": dt,
            "n_units_run": sum(1 for k, *_ in ok if k == "run"), "n_units_zero": sum(1 for k, *_ in ok if k == "zero"),
            "pending_units": missing, "flagged_units": flagged, "evaluator_sha256_of_merged_runs": {str(k): v for k, v in ev_hash.items()}, "units_dir": os.path.relpath(out_dir, REPO)}


def engineering_checks(out_dir=UNITS_DIR, snap_dir=SNAP_DIR):
    """Every per-unit output in a directory with its reproduction deviations (full re-runs, development-only and tiny runs)."""
    out = []
    if not os.path.isdir(out_dir):
        return {"outputs": out, "failed": [], "dir": os.path.relpath(out_dir, REPO)}
    for f in sorted(os.listdir(out_dir)):
        if not f.endswith(".json") or f.endswith(".FAILED.json"):
            continue
        u = json.load(open(os.path.join(out_dir, f)))
        d = u.get("dev", {}); cs = u.get("code_sha256") or {}
        evh = cs.get("complement_function_eval.py")
        out.append({"file": f, "eid": u.get("eid"), "cfg": u.get("cfg"), "kind": "dev_only" if u.get("dev_only") else ("full" if u.get("comparable_to_record") else "tiny"),
                    "device": u.get("device_name"), "seconds": u.get("seconds"), "selected_epoch": u.get("selected_epoch"),
                    "repro_max_abs_base": (u.get("reproduction") or {}).get("max_abs", {}).get("base"),
                    "repro_max_abs_rs": (u.get("reproduction") or {}).get("max_abs", {}).get("rs"),
                    "repro_bounded_max": max([x for v in ("base_record", "rs_record") for k in REPRO_KEYS
                                              if (x := ((u.get("reproduction") or {}).get(v) or {}).get(k)) is not None], default=None),
                    "within_tolerance": reproduces(u),
                    "dev_selected_abs_diff": (d.get("selected") or {}).get("abs_diff"), "dev_epoch0_abs_diff": (d.get("epoch0") or {}).get("abs_diff"),
                    "epoch0_max_abs_diff_vs_base": d.get("epoch0_max_abs_diff_vs_base"), "forward_check": u.get("forward_check", d.get("forward_check")),
                    "code_sha256_file": cs.get("complement_function.py"), "code_sha256_evaluator": evh,
                    "evaluator_snapshot": bool(evh and os.path.exists(os.path.join(snap_dir, f"complement_function_eval.{evh[:12]}.py"))),
                    "dev_rel_norm": (d.get("layers") or {}).get("relative_residual_norm_mean"), "dev_angle_deg": (d.get("layers") or {}).get("angle_deg_mean"),
                    "dev_post_change": (d.get("layers") or {}).get("normalized_change_mean"),
                    "process_peak_rss_mb": (u.get("runtime") or {}).get("process_peak_rss_mb"), "torch_threads": u.get("torch_threads"),
                    "gpu_peak_allocated_mb": (u.get("runtime") or {}).get("gpu_peak_allocated_mb")})
    failed = sorted(f for f in os.listdir(out_dir) if f.endswith(".FAILED.json"))
    return {"outputs": out, "failed": failed, "dir": os.path.relpath(out_dir, REPO)}


_SKIP = {"seconds", "build_seconds", "test_seconds", "runtime", "code_sha256", "code_snapshot", "started_utc", "limits", "row", "queries_file", "device",
         "device_name", "torch", "torch_threads", "output_version", "gpu_peak_allocated_mb", "rule", "epoch0_check_where"}


def _leaves(x, path=()):
    if isinstance(x, dict):
        for k, v in x.items():
            if k not in _SKIP:
                yield from _leaves(v, path + (str(k),))
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            yield from _leaves(v, path + (str(i),))
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield "/".join(path), float(x)


def compare_versions(dir_a=UNITS_V1_DIR, dir_b=UNITS_DIR):
    """v1 vs v2 per-unit outputs of the same unit: max |Δ| over every numeric leaf of the result (timing / provenance fields excluded)
    and over the per-query arrays."""
    out = {}
    if not (os.path.isdir(dir_a) and os.path.isdir(dir_b)):
        return out
    for f in sorted(os.listdir(dir_a)):
        if not f.endswith(".json") or f.endswith(".FAILED.json") or not os.path.exists(os.path.join(dir_b, f)):
            continue
        a, b = json.load(open(os.path.join(dir_a, f))), json.load(open(os.path.join(dir_b, f)))
        la, lb = dict(_leaves(a)), dict(_leaves(b))
        common = [k for k in la if k in lb and np.isfinite(la[k]) and np.isfinite(lb[k])]
        diffs = {k: abs(la[k] - lb[k]) for k in common}
        worst = max(diffs, key=diffs.get) if diffs else None
        r = {"numeric_leaves": len(common), "only_v1": len(set(la) - set(lb)), "only_v2": len(set(lb) - set(la)),
             "max_abs_diff": diffs[worst] if worst else None, "worst_leaf": worst,
             "code_sha256_v1": (a.get("code_sha256") or {}).get("complement_function.py"), "code_sha256_v2_evaluator": (b.get("code_sha256") or {}).get("complement_function_eval.py")}
        qa, qb = os.path.join(dir_a, f[:-5] + "_queries.npz"), os.path.join(dir_b, f[:-5] + "_queries.npz")
        if os.path.exists(qa) and os.path.exists(qb):
            za, zb = np.load(qa), np.load(qb); arr = {}
            for k in za.files:
                if k in zb.files and za[k].shape == zb[k].shape:
                    if za[k].dtype.kind in "fc":
                        arr[k] = float(np.max(np.abs(za[k] - zb[k]))) if za[k].size else 0.0
                    elif za[k].dtype.kind in "iub":
                        arr[k] = float(np.mean(za[k] != zb[k]))  # fraction of differing entries (ranks)
                    else:
                        arr[k] = float(np.mean(za[k] != zb[k]))
            r["queries"] = {"arrays": len(arr), "max_abs_diff_float": max([v for k, v in arr.items() if za[k].dtype.kind in "fc"], default=None),
                            "max_frac_differing_int": max([v for k, v in arr.items() if za[k].dtype.kind not in "fc"], default=None)}
        out[f] = r
    return out


# ================================================================================================ unit list, GPU estimate, sbatch template
def gpu_memory_from_records(rows, load):
    """gpu_peak_allocated_mb of the RS records: one process per unit (pool), covering training and evaluation together."""
    per = defaultdict(list)
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if rec and rec.get("status") == "complete" and rec.get("gpu_peak_allocated_mb") is not None:
            per[f"{r['dataset']}|{r['spec']['architecture']}"].append((int(rec["gpu_peak_allocated_mb"]), rec.get("device")))
    out = {}
    for k, L in sorted(per.items()):
        mb = [x[0] for x in L]; lo = min(mb)
        hi = [x for x in L if x[0] > 2 * lo]  # the small-capacity groups are bimodal (card-dependent peaks)
        out[k] = {"units": len(L), "min_mb": lo, "median_mb": float(np.median(mb)), "max_mb": max(mb), "devices": dict(Counter(x[1] for x in L)),
                  "units_above_2x_min": len(hi), "their_range_mb": [min(x[0] for x in hi), max(x[0] for x in hi)] if hi else None,
                  "their_devices": dict(Counter(x[1] for x in hi))}
    return out


def gpu_units(rows=None, load=None, out_dir=UNITS_DIR):
    rows = all_rows() if rows is None else rows; load = loader() if load is None else load
    need, zero = [], []
    for r in rows:
        if r["family_id"] != "ALN32_RESIDUAL" or r["seed"] != SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        if _link_state(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt")) not in ("link", "file"):
            continue
        (zero if rec.get("epoch0_selected") else need).append((r, rec))

    def done(eid):
        p = os.path.join(out_dir, f"{eid}.json")
        return os.path.exists(p) and reproduces(json.load(open(p)))
    pending = [(r, rec) for r, rec in need if not done(r["experiment_id"])]

    def est_of(L):
        est = defaultdict(lambda: np.zeros(3)); n = Counter()
        for r, rec in L:
            k = f"{r['dataset']}|{r['spec']['architecture']}"
            # assumption, not a measurement: the FM / encoder forward volume equals the record's own evaluation (one pass gives u_base
            # and r); the numpy readout part runs twice (base and RS views); + two development risks and cohort load / model build
            e = float(rec.get("eval_seconds") or 120.0)
            est[k] += np.array([1.0 * e + 60.0, 1.25 * e + 90.0, 1.6 * e + 120.0]); n[k] += 1
        tot = sum(est.values()) if est else np.zeros(3)
        mn = lambda x: round(float(x) / 60, 1)
        return {"per_dataset_backbone": {k: {"units": n[k], "gpu_minutes": mn(v[1]), "gpu_minutes_range": [mn(v[0]), mn(v[2])]} for k, v in sorted(est.items())},
                "total_gpu_minutes": mn(tot[1]), "total_gpu_minutes_range": [mn(tot[0]), mn(tot[2])]}
    devices = Counter(rec.get("device") for _, rec in need)
    return need, zero, pending, {"pending": est_of(pending), "all_listed": est_of(need), "record_devices": dict(devices),
                                 "basis": "assumed, not measured: per unit 1.25 x the record's eval_seconds + 90 s (range 1.0 x + 60 s to 1.6 x + 120 s)"}


def sbatch_text(units_txt=UNITS_TXT):
    rel = os.path.relpath(units_txt, REPO)
    return "\n".join([
        "#!/bin/bash",
        "# TEMPLATE written by auditory_alignment_v3.aln34.complement_function --write-units. NOT submitted by this lane; submitting it is",
        "# an operational step inside the project's 10-GPU cap (the c3_aln3fm pool shares that cap). Settings follow slurm/aln3_gpu_pool.sbatch.",
        "# One unit at a time per worker; several workers may run on the same list: atomic claims (<out>/claims/<eid>.claim) prevent",
        "# duplicates, a requeued worker releases its own claims, finished units (<out>/<eid>.json) are skipped, a unit is tried at most 3 times.",
        "#SBATCH --job-name=c3_aln34cf",
        "#SBATCH --nice=50",
        "#SBATCH --qos=runfill",
        "#SBATCH --partition=A100,A40,L40S,A30,V100",
        "#SBATCH --gres=gpu:1",
        "#SBATCH --exclude=node52",
        "#SBATCH --cpus-per-task=8",
        "#SBATCH --mem=48G",
        "#SBATCH --time=24:00:00",
        "#SBATCH --requeue",
        "#SBATCH --open-mode=append",
        "#SBATCH --output=private/auditory_alignment_v3/logs/%x-%j.log",
        "set -uo pipefail",
        "umask 077",
        'cd "$SLURM_SUBMIT_DIR"',
        "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 "
        "PYTHONHASHSEED=0 PYTHONPATH=$PWD MNE_USE_NUMBA=false",
        "export _MNE_FAKE_HOME_DIR=$(mktemp -d)",
        f"PY={PY}",
        'SHARD=${1:-}  # optional K/N (e.g. 0/4); claims alone already prevent duplicate work',
        f'$PY -B -m auditory_alignment_v3.aln34.complement_function --units-file {rel} --device cuda ${{SHARD:+--shard $SHARD}}',
        ""])


def write_units_file(rows=None, load=None, path=UNITS_TXT, out_dir=UNITS_DIR, sbatch_path=SBATCH_TXT):
    rows = all_rows() if rows is None else rows; load = loader() if load is None else load
    need, zero, pending, est = gpu_units(rows, load, out_dir)
    mem = gpu_memory_from_records(rows, load)
    pend = {r["experiment_id"] for r, _ in pending}
    env = "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 MNE_USE_NUMBA=false PYTHONPATH=$PWD"
    rel = os.path.relpath(path, REPO)
    L = ["# R34_FUSION_FUNCTION per-unit forward-pass evaluator (layers 1-3 + development layers), v2 (2026-10-16).",
         f"# Listed: the {len(need)} ALN32_RESIDUAL seed-3401 units whose selected epoch is > 0; the {len(zero)} epoch-0 units are exactly zero on",
         "# layers 1-3 (zero last layer, checkpoint-verified) and are not listed.",
         f"# Pending: {len(pending)} units. {len(need) - len(pending)} listed units already have a reproducing v2 output in {os.path.relpath(out_dir, REPO)}/ "
         "(CPU runs); the worker skips them.",
         f"# Estimate for the {len(pending)} pending units: {est['pending']['total_gpu_minutes']} GPU-minutes, range {est['pending']['total_gpu_minutes_range'][0]}-"
         f"{est['pending']['total_gpu_minutes_range'][1]} ({est['basis']}). All {len(need)} listed: {est['all_listed']['total_gpu_minutes']}.",
         "#   pending per dataset|backbone: " + "; ".join(f"{k} {v['units']} units {v['gpu_minutes']} min" for k, v in est["pending"]["per_dataset_backbone"].items()),
         "# GPU memory: no measurement of this evaluator on a GPU exists. The RS records' gpu_peak_allocated_mb is one process per unit covering",
         "# training and evaluation together (max per dataset|backbone): " + "; ".join(f"{k} {v['max_mb']} MB" for k, v in mem.items()) + ".",
         "#   Units above 2x their group minimum: " + ("; ".join(f"{k} {v['units_above_2x_min']} units {v['their_range_mb'][0]}-{v['their_range_mb'][1]} MB on "
                                                               f"{', '.join(map(str, v['their_devices']))}" for k, v in mem.items() if v["units_above_2x_min"]) or "none") + ".",
         "# The evaluator runs the record's evaluation forwards (8 segments per chunk) plus development passes, without optimiser state.",
         "# order: small-capacity branch, then CBraMod, then REVE (cost).",
         f"# command per unit (repo root):  {env} {PY} -B -m auditory_alignment_v3.aln34.complement_function --unit <eid> --device cuda",
         f"# worker (repo root):            {env} {PY} -B -m auditory_alignment_v3.aln34.complement_function --units-file {rel} --device cuda [--shard K/N]",
         f"# Slurm template (not submitted): {os.path.relpath(sbatch_path, REPO)}",
         f"# afterwards (CPU):              PYTHONPATH=$PWD {PY} -B -m auditory_alignment_v3.aln34.complement_function --aggregate",
         "# columns: eid dataset objective architecture variant subject_fold content_fold record_eval_seconds status"]
    pri = {"small_capacity_branch": 0, "cbramod": 1, "reve": 2}
    for r, rec in sorted(need, key=lambda x: (pri[x[0]["spec"]["architecture"]], x[0]["dataset"], x[0]["spec"]["objective"], x[0]["spec"]["variant"],
                                              x[0]["subject_fold"], x[0]["content_fold"])):
        L.append(f"{r['experiment_id']} {r['dataset']} {r['spec']['objective']} {r['spec']['architecture']} {r['spec']['variant']} {r['subject_fold']} "
                 f"{r['content_fold']} {rec.get('eval_seconds')} {'pending' if r['experiment_id'] in pend else 'done_v2'}")
    for p_, txt in ((path, "\n".join(L) + "\n"), (sbatch_path, sbatch_text(path))):
        fd = os.open(p_ + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(txt)
        os.chmod(p_ + ".tmp", 0o600); os.replace(p_ + ".tmp", p_)
    return path, len(need), len(zero), len(pending), est, mem


# ================================================================================================ worker loop (claims, shards, tries)
def _me():
    job = os.environ.get("SLURM_JOB_ID") or f"local-{socket.gethostname()}-{os.getpid()}"
    return {"job": job, "host": socket.gethostname(), "pid": os.getpid(), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def live_jobs():
    """Job ids of this user's running Slurm jobs, or None when squeue fails / lists nothing (then no foreign claim is released)."""
    try:
        p = subprocess.run(["squeue", "-u", os.environ.get("USER", ""), "-h", "-t", "RUNNING,CONFIGURING,COMPLETING", "-o", "%i"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    ids = set(p.stdout.split())
    return ids if p.returncode == 0 and ids else None


def _pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def sweep_claims(claims_dir, me, live):
    """Release own claims (a requeued Slurm job restarts from scratch with the same job id), claims of finished jobs (not in squeue),
    claims of dead local processes on this host, and owner-less claims older than 10 min; never a foreign claim younger than 2 min."""
    released = []
    if not os.path.isdir(claims_dir):
        return released
    for d in sorted(os.listdir(claims_dir)):
        p = os.path.join(claims_dir, d)
        if not d.endswith(".claim") or not os.path.isdir(p):
            continue
        try:
            owner = json.load(open(os.path.join(p, "owner.json")))
        except (OSError, ValueError):
            owner = None
        age_min = (time.time() - os.path.getmtime(p)) / 60
        job = (owner or {}).get("job")
        if job is not None and job == me["job"]:
            drop = True
        elif owner is None:
            drop = age_min > 10
        elif age_min < 2:
            drop = False
        elif str(job).startswith("local-"):
            drop = owner.get("host") == socket.gethostname() and not _pid_alive(owner.get("pid"))
        else:
            drop = live is not None and str(job) not in live
        if drop:
            shutil.rmtree(p, ignore_errors=True); released.append(d[:-len(".claim")])
    return released


def try_claim(claims_dir, eid, me):
    os.makedirs(claims_dir, mode=0o700, exist_ok=True)
    p = os.path.join(claims_dir, f"{eid}.claim")
    try:
        os.mkdir(p, 0o700)  # atomic: exactly one worker succeeds
    except FileExistsError:
        return False
    _write_json(os.path.join(p, "owner.json"), me)
    return True


def release_claim(claims_dir, eid):
    shutil.rmtree(os.path.join(claims_dir, f"{eid}.claim"), ignore_errors=True)


def parse_shard(s):
    if not s:
        return None
    k, n = (int(x) for x in s.split("/"))
    if not 0 <= k < n:
        raise ValueError(f"shard {s}: need 0 <= K < N")
    return k, n


def run_units_file(path, device, out_dir=UNITS_DIR, shard=None, max_tries=MAX_TRIES, rows=None, load=None, limits=None, live=None):
    """Worker loop: units in file order (optionally the K-th of N shards), one at a time; a unit is skipped when its output exists,
    when it failed max_tries times, or when another worker holds its claim. Failures are recorded (<eid>.FAILED.json with the try
    count), never hidden."""
    eids = [l.split()[0] for l in open(path) if l.strip() and not l.startswith("#")]
    if shard:
        eids = [e for i, e in enumerate(eids) if i % shard[1] == shard[0]]
    rows = all_rows() if rows is None else rows; load = loader() if load is None else load
    claims = os.path.join(out_dir, "claims"); me = _me()
    released = sweep_claims(claims, me, live_jobs() if live is None else live)
    tally = Counter({"released_stale_claims": len(released)})
    for eid in eids:
        outp, failp = os.path.join(out_dir, f"{eid}.json"), os.path.join(out_dir, f"{eid}.FAILED.json")
        if os.path.exists(outp):
            tally["skip_done"] += 1; continue
        tries = json.load(open(failp)).get("tries", 1) if os.path.exists(failp) else 0
        if tries >= max_tries:
            tally["skip_failed"] += 1; continue
        if not try_claim(claims, eid, me):
            tally["skip_claimed"] += 1; continue
        try:
            if os.path.exists(outp):
                tally["skip_done"] += 1; continue
            p = evaluate_unit(eid, device, limits or Limits(), False, out_dir, rows, load)
            tally["done"] += 1
            print("done", eid, p, flush=True)
        except Exception as ex:  # noqa: BLE001 - recorded, never hidden
            _write_json(failp, {"eid": eid, "error": f"{type(ex).__name__}: {ex}", "traceback": traceback.format_exc()[-4000:], "tries": tries + 1, "owner": me})
            tally["failed"] += 1
            print("FAILED", eid, ex, flush=True)
        finally:
            release_claim(claims, eid)
            import gc
            gc.collect()
            if str(device).startswith("cuda"):
                import torch
                torch.cuda.empty_cache()
    print("worker", dict(tally), flush=True)
    return dict(tally)


# ================================================================================================ aggregate + report
def targets_of(rows, load):
    """Target (plan spec) and target contract (record) of every compared configuration, per dataset."""
    out = defaultdict(lambda: {"target": set(), "target_contract": set(), "seeds": set()})
    for r in rows:
        if r["family_id"] == "ALN32_SIMPLE_COMPLEMENT":
            ok = r["seed"] == SEED and r["dataset"] in DS
        else:
            ok = cfg34(r) is not None
        if not ok:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete":
            continue
        o = out[r["dataset"]]
        o["target"].add(r["spec"].get("target") or TARGET[r["dataset"]]); o["target_contract"].add(rec.get("target_contract")); o["seeds"].add(r["seed"])
    return {ds: {k: sorted(map(str, v)) for k, v in o.items()} for ds, o in sorted(out.items())}


def record_counts(rows, load):
    c = Counter()
    for r in rows:
        if r["seed"] != SEED:
            continue
        if r["family_id"] == "ALN32_SIMPLE_COMPLEMENT":
            k = "SC"
        else:
            cc = cfg34(r)
            if cc is None:
                continue
            k = cc[0]
        rec = load(r["experiment_id"])
        c[f"{k}|{'missing' if rec is None else rec.get('status')}"] += 1
    return dict(sorted(c.items()))


def aggregate(skip_ckpt=False):
    from auditory_alignment_v3 import bc_interim as BI
    t0 = time.time()
    rows0 = all_rows(); load = loader()
    rows, xload = expand_rows(rows0, load)
    manifest = BI.load_manifest()
    table, data = same_contract(rows, xload, manifest)
    meta = {"card": "R34_FUSION_FUNCTION", "status": "exploratory re-evaluation (ALN3.4)", "version": "v2", "note": os.path.relpath(NOTE, REPO),
            "note_correction": "section 'Correction 1 (2026-10-16 21:34 CEST)'", "supersedes": os.path.relpath(V1_COPY, REPO), "seed": SEED, "n_boot": S.NB,
            "code_sha256": {"complement_function.py": MODULE_SHA256, "complement_function_eval.py": EV.MODULE_SHA256, "sci_r1/stats.py": sha256(S.__file__),
                            "bc_interim.py": sha256(BI.__file__), "reference residuals.py": sha256(REF_RESIDUALS)},
            "code_snapshot": EV.snapshot_code(SNAP_DIR), "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "slurm_job": os.environ.get("SLURM_JOB_ID", "local")}
    out = {"meta": meta, "same_contract": table, "record_counts": record_counts(rows0, load), "targets": targets_of(rows0, load),
           "federici_identities": manifest_identities(manifest),
           "access": access_table(rows0, load), "budgets": budgets(rows0, load), "sc_backbone_copies": sc_backbone_copies(rows0, load, data["vals"]),
           "regression": regression_checks(table, os.path.join(V1_COPY, "complement_function.json")),
           "epoch0_identity": epoch0_identity(rows0, load), "readout_scales": readout_scales(rows0, load), "layer4_dev_test": dev_test_layer(rows0, load)}
    out["checkpoint_layer"] = None if skip_ckpt else checkpoint_layer(rows0, load)
    out["asset_audit"] = audit_assets(rows0, load, check_ckpt_keys=not skip_ckpt)
    need, zero, pending, est = gpu_units(rows0, load)
    out["gpu_plan"] = {"units_file": os.path.relpath(UNITS_TXT, REPO), "sbatch_template": os.path.relpath(SBATCH_TXT, REPO), "n_units_listed": len(need),
                       "n_units_pending": len(pending), "n_epoch0_units_exact_zero": len(zero), **est, "gpu_memory_records": gpu_memory_from_records(rows0, load)}
    out["layers_1_3"] = collect_units(rows0, load, manifest, ckpt=out["checkpoint_layer"])
    out["engineering_checks"] = {"v2": engineering_checks(UNITS_DIR), "v1_kept_not_merged": engineering_checks(UNITS_V1_DIR)}
    out["v1_vs_v2_unit_outputs"] = compare_versions(UNITS_V1_DIR, UNITS_DIR)
    out["meta"]["note_sha256"] = sha256(NOTE) if os.path.exists(NOTE) else None
    out["seconds"] = round(time.time() - t0, 1)
    per_ident = {ckey(c): v for c, v in data["vals"].items()}
    _write_json(os.path.join(RES, "per_identity_values.json"), per_ident)
    p = _write_json(os.path.join(RES, "complement_function.json"), out)
    d = write_report(out, DOC)
    bad = BI.privacy_scan([p, d], set())
    print("privacy scan:", "PASS" if not bad else bad, "| excluded pairs", len(table["excluded_pairs"]), "| seconds", out["seconds"])
    if bad:
        raise SystemExit(2)
    return p, d


def _f(x, k=3):
    return "–" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{k}f}"


def _iv(m, lo="ci_low", hi="ci_high"):
    return "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"


def _e(x):
    return "–" if x is None else f"{x:.1e}"


def _rng(r):
    return "–" if not r else (_e(r[0]) if r[0] == r[1] else f"{_e(r[0])}–{_e(r[1])}")


def _vals(x, fmt="{:,}"):
    """[5] -> '5'; [877104, 2155680] -> '877,104 / 2,155,680'."""
    return " / ".join(fmt.format(v) for v in (x if isinstance(x, (list, tuple)) else [x]))


def class_counts(tb, fam, rd, dedupe=False):
    """Simultaneous classes of a family type and readout; dedupe = count local_only once per dataset x base (the cbramod and reve
    units share that ridge), keeping the cbramod copy."""
    c, ex = Counter(), defaultdict(list)
    for lab, f in tb["families"].items():
        if f["family"] != fam or f["readout"] != rd:
            continue
        for name, m in f["members"].items():
            if dedupe and fam == "FN-DIRECT-SC" and name == "local_only" and f["scope"].split("|")[1] == "reve":
                continue
            k = m.get("class", "–"); c[k] += 1
            if k in ("I>0", "I<0"):
                ex[k].append(f"{f['scope'].replace('|', '·')}/{name} {m['est']:+.3f}")
    return c, ex


def local_only_copy_classes(tb):
    agree = n = 0
    for rd in READOUTS:
        for ds in DS:
            for base in ("L0", "L1"):
                k = [tb["families"].get(f"FN-DIRECT-SC|{ds}|{a}|{base}|{rd}", {}).get("members", {}).get("local_only", {}).get("class") for a in ARCH]
                if all(k):
                    n += 1; agree += int(k[0] == k[1])
    return agree, n


def write_report(out, path):
    tb = out["same_contract"]; meta = out["meta"]; rg = out.get("regression") or {}
    cs = meta["code_sha256"]; fi = out["federici_identities"]
    L = ["# Complement function report — R34_FUSION_FUNCTION (exploratory re-evaluation, ALN3.4) — v2", "",
         f"Generated {meta['generated']} (job {meta['slurm_job']}) by `{PY} -B -m auditory_alignment_v3.aln34.complement_function --aggregate` (PYTHONPATH = repo root). Version v2; it "
         f"supersedes v1 (generated 2026-10-16 20:37), whose report, JSON, code, test and unit list are kept byte-identical in `{meta['supersedes']}/`. "
         f"Analysis note (written before the v1 values were computed; its {meta['note_correction']} was written before any v2 value): `{meta['note']}`. "
         f"Seed {meta['seed']}; identity-level paired differences; bootstrap-t B = {meta['n_boot']}; simultaneous 95% intervals by max-t within each family. "
         "Positive = candidate better (lower risk R in bits, lower rank_pct, higher top-1). No p-values; no test-based selection; nothing here was retrained.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in cs.items()) + f". Loaded sources of the two lane modules: {', '.join(f'`{v}`' for v in meta['code_snapshot'].values())}.", "",
         "**Reading rules.**",
         "- SC `local_only` is the base passed through a supervised ridge to the raw target and the fixed audio head: a ridge-remapped base, not the base.",
         "- Every SC variant is a supervised closed-form fit on frozen encoders; only the encoders are frozen.",
         "- RS at epoch 0 equals base L0 exactly (zero-initialised last layer).",
         "- Access (§3): base L0 reads [0, post). L1, the SC context features (aligned_pretrained, aligned_random, small_context, concat) and every RS context branch "
         "read the query-aligned window [-0.4 s, post). SC `local_only` and `local_refit_capacity` read only the base's own input. So against L0 the SC context "
         "variants and RS are context-assisted, while `local_only` / `local_refit_capacity` are access-matched; against L1 every SC variant is access-matched.",
         f"- Seeds and folds never add n; rows are identities (Federici: {fi['human_identities']} human identities from {fi['human_records']} records, "
         f"{fi['identities_by_condition']}; each HC-v record has its own subject_uid; the {fi['non_human_records']} phantom sessions are excluded).", ""]
    # ---- 0. version
    v12 = rg.get("v1_vs_v2", {})
    L += ["## 0. Version history and corrections", "",
          "v2 corrects v1 as follows (details and the honest record of what was seen: analysis note, Correction 1):",
          f"- access labels: `local_refit_capacity` under L0 was labelled context-assisted ({v12.get('v1_refit_capacity_L0_context_tags', '?')} family rows in v1); "
          "it reads only L0's own tokens and is access-matched. "
          "The same label sits in the frozen `COMPLEMENT_REVISED_RESULTS.md` (SC-VALUE `local_refit_capacity` under L0, tag \"vs local_only (context-assisted)\"); "
          "that document is not edited, this line is its correction pointer. RS members now carry their access label (context-assisted vs L0);",
          "- the SC calibration caveat names the unified bridge as well as the temperature (§2);",
          "- the held-out development level actually achieved is stated (§1) and the fit budgets are tabulated (§3);",
          "- the epoch-0 statement is computed, with where the record field was measured (§2);",
          "- the asset audit searches by experiment id, inventories every checkpoint file and hashes the FM weights against the fetch receipt (§10);",
          "- the GPU plan uses the project interpreter and offline flags, has a claim-based worker and an sbatch template, counts pending units only, "
          "and states GPU memory from the records as training + evaluation peaks (§11);",
          "- bookkeeping: coverage of all 30 RS configurations (§9), record counts (§12.5), duplicated `local_only` members in the SC tallies (§5, §12.1);",
          "- provenance: the evaluator moved to `complement_function_eval.py`; every per-unit output records the evaluator hash and its loaded source is "
          "snapshotted; the v1 per-unit outputs (recorded hashes of intermediate, unkept file versions) are kept in "
          f"`{os.path.relpath(UNITS_V1_DIR, REPO)}/` and not merged; they were re-run with the v2 evaluator (§9).", ""]
    if v12:
        same = v12["max_abs_diff"] == 0 and v12["class_changes"] == 0 and not v12["levels_max_abs_diff_est"]
        L += [f"Value check against v1: {v12['members']} family members, max |Δ| over estimates and both intervals {_e(v12['max_abs_diff'])}, class changes "
              f"{v12['class_changes']}; level estimates max |Δ| {_e(v12['levels_max_abs_diff_est'])}. Every member label was reworded ({v12['tag_changes']} "
              f"members); access-class changes: {v12.get('access_class_changes') or 'none'}. "
              + ("So in §4–§6 only the access labels changed; every value is identical to v1." if same else "Values differ from v1: see `regression.v1_vs_v2` in the JSON."), ""]
    # ---- 1. development level
    bd = out["budgets"]; rsc = bd["RS_code"]; scc = bd["SC_code"]
    L += ["## 1. Level of held-out development actually achieved (AGENTS ALN3.4 item 8; docs/03 §1)", "",
          f"- **SC**: ridge-only out-of-fold. Residual ridges are fitted on out-of-fold base predictions over {scc['N_GROUPS']} groups of the outer-fold training "
          f"participants, and every alpha is chosen by grouped cross-validation over those groups. The base encoder itself was trained on all of them "
          f"(record field `base_trained_on_all_groups`: {'true in all ' + str(sum(v['records'] for v in bd['SC'].values())) + ' SC records' if all(v['base_trained_on_all_groups'] for v in bd['SC'].values()) else 'NOT true in every SC record'}). The PCA bases and the "
          "final ridges are fitted on all training rows. So the old SC OOF values hold for the ridge step only, not for the whole pipeline.",
          f"- **RS**: residual-only cross-person selection. The residual and its context branch are trained on groups other than {rsc['DEV_GROUP']}; the epoch "
          f"(0..{rsc['EPOCHS']}, epoch 0 = the base) is selected on group {rsc['DEV_GROUP']} development segments. Group {rsc['DEV_GROUP']} participants were "
          "training participants of the frozen base L0, so only the residual is held out from the development identities.",
          "- **This re-evaluation**: no selection and no new fit, except the evaluator's training-side readouts (unified bridge, CS_SINGLE native ridge, "
          "temperatures), refitted exactly as in the original records. Test participants enter no fit.",
          "- Neither SC nor RS is whole-pipeline held-out-person development (docs/03 §4 describes that as a new execution).", ""]
    # ---- 2. contract checks
    e0 = out["epoch0_identity"]; ck = out.get("checkpoint_layer"); rf = e0["record_field"]
    if e0["n"]:
        e0_lines = [f"- RS units that selected epoch 0: {e0['n']}. Their selected checkpoints have a zero last layer "
                    f"({ck['n_epoch0_with_zero_last_layer'] if ck else '?'} / {ck['n_epoch0_units'] if ck else '?'}; §8), so r = 0 exactly and u = normalise(u_base) on every "
                    "test anchor. Their outer-test records against the base L0 records (scored in separate GPU runs): max |Δ| on log-loss and rank_pct "
                    f"= {e0['max_abs_diff_bounded']:.1e} ({'within' if e0['within_tolerance'] else 'OUTSIDE'} the 1e-3 reproduction rule); over all metrics incl. "
                    f"top-1 / top-5 / MRR = {e0['max_abs_diff']:.3f}" + (", i.e. single near-tie flips (1/n_queries)." if e0["max_abs_diff"] > e0["max_abs_diff_bounded"] else "."),
                    f"- The record field `{rf['name']}` is {_rng(rf['epoch0_units_range'])} in these units "
                    f"({_rng(rf['all_units_range'])} over all {rf['n_all_units']} units). Where it was measured: {rf['where']}."]
    else:
        e0_lines = ["- No RS unit selected epoch 0."]
    L += ["## 2. Same-contract checks", "",
          f"- Pairing (folds, participants, candidate and query counts, both readouts): {tb['pairing']}; excluded pairs: {len(tb['excluded_pairs'])}."] + e0_lines + [
          "- **SC in-sample caveat** (disclosed, not corrected). The SC ridges were fitted on fit **and** es rows of the training participants. The evaluator "
          "selects the unified bridge's alpha on es rows and refits it on fit + es rows, and calibrates both temperatures on es queries. So SC's unified R, "
          "rank_pct and top-1 all carry the in-sample es effect; SC's native ranks (NCE: fixed dot product, no fitted readout) do not; SC's native R carries it "
          "through the temperature. Base and RS used es rows for early stopping, selection or calibration only. The direction of the effect is not determined here.",
          "- The native NCE score has no fitted parameter; only CS_SINGLE fits a native ridge (U → V)."]
    if rg.get("rs_value_vs_frozen"):
        r_ = rg["rs_value_vs_frozen"]
        L.append(f"- Regression: RS-VALUE families ({r_['members']} members) vs the frozen `{r_['file']}`: max |Δ| {r_['max_abs_diff']:.1e}, class mismatches {r_['class_mismatches']}.")
    if rg.get("sc_levels_vs_frozen"):
        r_ = rg["sc_levels_vs_frozen"]
        L.append(f"- Regression: SC level estimates ({r_['values']} values, both readouts) vs the frozen `{r_['file']}`: max |Δ| {r_['max_abs_diff_est']:.1e}.")
    if ck:
        L.append(f"- Checkpoints: epoch-0 selection ⇔ zero residual last layer, mismatches: {ck['epoch0_vs_zero_mismatch'] or 'none'}.")
    L.append("")
    # ---- 3. access and budgets
    ac = out["access"]
    L += ["## 3. Input access and fit budgets (docs/03 §1)", "", "| configuration | EEG read |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in ac["reads"].items()]
    L += ["", "Windows recorded per family and dataset (half-open, samples): " + "; ".join(f"{k}: {', '.join(v)}" for k, v in ac["windows"].items())
          + f"; sampling rates {ac['fs']}. Source: {ac['source']}.", ""]
    L += ["| fitted part | identities | content / rows | budget |", "|---|---|---|---|"]
    for k, v in bd["SC"].items():
        L.append(f"| SC ridges + PCA, {k} ({v['records']} records) | {v['n_train_participants'][0]}–{v['n_train_participants'][1]} outer-fold training participants, "
                 f"{_vals(v['groups'])} groups | {scc['training_rows']}; {scc['anchors_per_training_segment']} grid anchors per segment | ridge rows {v['n_fit_rows'][0]:,}–"
                 f"{v['n_fit_rows'][1]:,}; PCA K = {_vals(v['k_pca'])} per block on {_vals(v['n_pca_rows'])} rows ({scc['pca']}; subsample rng {scc['pca_subsample_rng']}); "
                 f"alpha grid {len(v['alpha_grid'])} values {v['alpha_grid'][0]:g}–{v['alpha_grid'][-1]:g} ({scc['alpha_selection']}) |")
    for k, v in bd["RS"].items():
        L.append(f"| RS residual + context, {k} ({v['records']} records) | training participants; development group {_vals(v['dev_group'])} | {rsc['training_rows']}; "
                 f"{rsc['Q_anchors_per_segment']} anchors per segment | training segments {v['n_train_segments'][0]:,}–{v['n_train_segments'][1]:,}; development "
                 f"{_vals(v['n_dev_segments'])} segments; temperature {_vals(v['n_cal_segments'])} segments; epochs {_vals(v['epochs'])}; trainable parameters "
                 f"{_vals(v['trainable_params'])}{' (one value per backbone)' if len(v['trainable_params']) == 2 else ''} |")
    ev = bd["evaluator"]
    L += [f"| evaluator readouts (every row of §4) | outer-fold training participants | {ev['readout_rows']} | {ev['readout_segments']} segments ({ev['readout_rng']}); "
          f"unified alpha grid {ev['unified_alpha_grid']} ({ev['unified_alpha_selection']}); CS_SINGLE native alpha grid {ev['native_CS_SINGLE_alpha_grid']}; "
          f"NCE native: {ev['native_NCE']} |",
          f"| evaluator temperatures | outer-fold training participants | {ev['calibration']} | ≤ {ev['calibration_queries']} queries |",
          f"| outer test | the fold's test participants | {ev['test']} | all |", ""]
    # ---- 4. levels
    tg = out.get("targets") or {}
    L += ["## 4. Levels on the same identities (seed 3401)", "",
          "Targets and units: " + "; ".join(f"{ds} target {', '.join(v['target'])} (contract {', '.join(v['target_contract'])}; seeds {', '.join(v['seeds'])})"
                                             for ds, v in tg.items())
          + ". R = candidate cross-entropy of the true test stimulus in bits; rank_pct = rank of the true candidate / (candidates − 1); n = identities.", "",
          "| configuration | n | R unified [95% CI] | R native [95% CI] | rank_pct u / n | top1 u / n |", "|---|---|---|---|---|---|"]
    order = {"L0": 0, "L1": 1, "SC": 2, "RS": 3, "FM": 4, "TF": 5}
    lv = lambda x: "–" if x is None else f"{x:.3f}"
    for k in sorted(tb["levels"], key=lambda s: (s.split("|")[1], s.split("|")[2], order.get(s.split("|")[0], 9), s)):
        r = tb["levels"][k]; ru, rn = r.get(PRIMARY34["unified"], {}), r.get(PRIMARY34["native"], {})
        g = lambda m: r.get(m, {}).get("est")
        lab = k + ("  (= RS at epoch 0)" if k.startswith("L0|") else "") + ("  (context, reported before)" if k.startswith(("FM|", "TF|")) else "")
        L.append(f"| {lab} | {r['n']} | {lv(ru.get('est'))} {_iv(ru)} | {lv(rn.get('est'))} {_iv(rn)} | "
                 f"{lv(g('unified/regular/rank_pct'))} / {lv(g('native/regular/rank_pct'))} | {lv(g('unified/regular/top1'))} / {lv(g('native/regular/top1'))} |")
    L.append("")
    # ---- 5./6. contrasts
    for fam, title in (("FN-DIRECT-SC", "5. SC variants vs the original direct base"), ("FN-RS", "6. RS selected epoch vs epoch 0 (= base L0)")):
        L += [f"## {title}", ""]
        if fam == "FN-DIRECT-SC":
            cp = out.get("sc_backbone_copies") or {}
            lo = [v for k, v in cp.items() if k.endswith("|local_only")]
            same = bool(lo) and all(v["alpha_equal"] == v["unit_pairs"] for v in lo)
            L += [f"`local_only` enters the cbramod and the reve family of each dataset · base; both copies are listed. "
                  + (f"They are the same ridge (same input, no PCA; alpha equal in all {sum(v['unit_pairs'] for v in lo)} unit pairs)." if same else
                     "Their alphas differ in some unit pairs (table below).")
                  + " `local_refit_capacity` and `small_context` also read no FM feature, so the two units of a cell see the same inputs; how far "
                  "their copies differ is in the table at the end of this section.", ""]
        else:
            L += ["The unified family uses the frozen RS-VALUE labels and reproduces `COMPLEMENT_REVISED_RESIDUAL_RESULTS.md` §3 (already seen; regression in §2). "
                  "The native family's point estimates were already visible there as the secondary column ΔR_native; its intervals and classes are new.", ""]
        for rd in READOUTS:
            L += [f"**{rd} readout**", ""]
            for lab, f in tb["families"].items():
                if f["family"] != fam or f["readout"] != rd or not f["members"]:
                    continue
                sec = tb["secondary"][lab]
                L += [f"*{f['scope'].replace('|', ' · ')}* (critical value {f.get('crit', float('nan')):.2f})", "",
                      f"| member | access | n | ΔR {rd} | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |", "|---|---|---|---|---|---|---|---|---|---|"]
                for name, m in f["members"].items():
                    s2 = [sec[x]["members"].get(name, {}).get("est") for x in SECONDARY34[rd]]
                    L.append(f"| {name} | {m['tag']} | {m['n']} | {_f(m.get('est'))} | {_iv(m)} | {_iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | "
                             + " | ".join(_f(x) for x in s2) + " |")
                L.append("")
        if fam == "FN-DIRECT-SC":
            cp = out.get("sc_backbone_copies") or {}
            L += ["Cross-backbone copies of the FM-free SC variants (cbramod unit vs reve unit of the same cell; record values):", "",
                  "| dataset · base · variant | unit pairs | alpha equal | max per-participant \\|Δ log-loss\\| unified / native | max per-identity \\|ΔR\\| unified / native |",
                  "|---|---|---|---|---|"]
            for k, v in cp.items():
                if v["reads_fm"]:
                    continue
                L.append(f"| {k.replace('|', ' · ')} | {v['unit_pairs']} | {v['alpha_equal']} | {_e(v['max_participant_abs_diff_unified'])} / {_e(v['max_participant_abs_diff_native'])} | "
                         f"{_e(v['max_identity_abs_diff_unified'])} / {_e(v['max_identity_abs_diff_native'])} |")
            L.append("")
    # ---- 7. layer 4
    l4 = out["layer4_dev_test"]
    L += ["## 7. Layer 4 — development vs outer test, epoch 0 vs the selected epoch (unit-level, descriptive)", "",
          "Δdev = dev risk(epoch 0) − dev risk(selected) ≥ 0 by construction (bits; the development pool of ≤ 300 group-0 segments, "
          "dot-product score). Δtest = base L0 − RS on the outer test (bits, mean over the unit's test participants; same scale as §6 "
          "but unit-level). Units share training participants; the identity-level test inference is §6.", "",
          "| configuration | units | epoch 0 | sel. epoch median [range] | Δdev mean | Δdev/dev0 | Δtest unified | Δtest native | test better (native, epoch>0) | Spearman Δdev~Δtest native |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in l4["per_config"].items():
        L.append(f"| {k} | {v['n_units']} | {v['n_epoch0']} | {v['selected_epoch_median']:.0f} [{v['selected_epoch_range'][0]}, {v['selected_epoch_range'][1]}] | "
                 f"{_f(v['d_dev_mean'], 4)} | {_f(v['d_dev_rel_mean'], 4)} | {_f(v['d_test_R_unified_mean'], 4)} | {_f(v['d_test_R_native_mean'], 4)} | "
                 f"{'–' if v['frac_test_better_native_epoch_gt0'] is None else format(v['frac_test_better_native_epoch_gt0'], '.2f')} | "
                 f"{_f(v['spearman_d_dev_d_test_native_epoch_gt0'], 2)} |")
    L.append("")
    rs_ = out["readout_scales"]
    L += ["Readout temperatures refitted by the evaluator (training side), RS selected / base, median over epoch>0 units:", "",
          "| configuration | units epoch>0 | τ unified ratio | τ native ratio [range] | α unified changed |", "|---|---|---|---|---|"]
    for k, v in sorted(rs_.items()):
        if v["n_epoch_gt0"]:
            L.append(f"| {k} | {v['n_epoch_gt0']} | {v['tau_ratio_unified_median']:.3f} | {v['tau_ratio_native_median']:.3f} "
                     f"[{v['tau_ratio_native_range'][0]:.3f}, {v['tau_ratio_native_range'][1]:.3f}] | {v['frac_alpha_unified_changed']:.2f} |")
    L.append("")
    # ---- 8. checkpoint layer
    if ck:
        L += ["## 8. Residual last layer at the selected epoch (parameter level, not ||r||)", "",
              "| configuration | units | epoch 0 (zero layer) | ‖W₂‖_F median | ‖W₂‖₂ median [max] | ‖b₂‖ median [max] |", "|---|---|---|---|---|---|"]
        for k, v in ck["per_config"].items():
            L.append(f"| {k} | {v['n_units']} | {v['n_epoch0']} ({v['n_zero_last_layer']}) | {_f(v['W2_fro_median'], 4)} | {_f(v['W2_spec_median'], 4)} [{_f(v['W2_spec_max'], 4)}] | "
                     f"{_f(v['b2_norm_median'], 4)} [{_f(v['b2_norm_max'], 4)}] |")
        L.append("")
    # ---- 9. layers 1-3
    l13 = out["layers_1_3"]; gp = out["gpu_plan"]; cf = l13["configs"]
    L += ["## 9. Layers 1–3 per query (forward passes)", "",
          f"Merged: v2 outputs in `{l13['units_dir']}/` only. Units run and reproduced: {l13['n_units_run']}; epoch-0 units (exact zeros, checkpoint-verified): "
          f"{l13['n_units_zero']}; pending: {len(l13['pending_units'])}; flagged (re-run did not reproduce the record): {len(l13['flagged_units'])}. "
          f"Evaluator sha256 of the merged runs: {', '.join(f'{k[:12]} ({v} units)' for k, v in l13['evaluator_sha256_of_merged_runs'].items()) or 'none'}.", "",
          f"Coverage over the {sum(cf.values())} RS configurations: complete {cf['complete']}, partly covered {cf['partial']} (epoch-0 zeros and/or some runs), "
          f"not covered {cf['none']}. A configuration is summarised only when every unit is covered (epoch-0 zeros alone would bias it).", "",
          "| configuration | units | epoch-0 zeros | runs reproduced | coverage |", "|---|---|---|---|---|"]
    for k, v in l13["per_config"].items():
        L.append(f"| {k} | {v['n_units']} | {v['n_epoch0_zero']} | {v['n_run_reproduced']} | {v['coverage']} |")
    L.append("")
    done = {k: v for k, v in l13["per_config"].items() if v.get("complete") and "L12/rel_norm" in v}
    if done:
        L += ["Pointwise bootstrap-t over identities (diagnostics, not a contrast family).", "",
              "| configuration | identities | ‖r‖/‖u‖ [95% CI] | parallel coef (r·u/u·u) | ‖r∥‖/‖u‖ | ‖r⊥‖/‖u‖ | angle (deg) | post-norm change |",
              "|---|---|---|---|---|---|---|---|"]
        for k, v in done.items():
            g = lambda m: v.get(m, {}).get("est")
            L.append(f"| {k} | {v['n_identities']} | {_f(g('L12/rel_norm'), 4)} {_iv(v.get('L12/rel_norm', {}))} | {_f(g('L12/coef'), 4)} | {_f(g('L12/rel_par'), 4)} | "
                     f"{_f(g('L12/rel_orth'), 4)} | {_f(g('L12/angle_deg'), 3)} | {_f(g('L12/post_change'), 4)} |")
        L += ["", "| configuration | readout | queries with rank change | mean |Δrank| | mean Δrank (− = better) | top-1 gained / lost | ΔR (base − RS) [95% CI] | Δ true-candidate z-score |",
              "|---|---|---|---|---|---|---|---|"]
        for k, v in done.items():
            g = lambda m: v.get(m, {}).get("est")
            for rd in READOUTS:
                L.append(f"| {k} | {rd} | {_f(g(f'L3/{rd}/frac_rank_changed'), 3)} | {_f(g(f'L3/{rd}/mean_abs_drank'), 3)} | {_f(g(f'L3/{rd}/mean_drank'), 3)} | "
                         f"{_f(g(f'L3/{rd}/top1_gain'), 4)} / {_f(g(f'L3/{rd}/top1_loss'), 4)} | {_f(g(f'L3/{rd}/d_logloss'), 4)} {_iv(v.get(f'L3/{rd}/d_logloss', {}))} | "
                         f"{_f(g(f'L3/{rd}/d_true_z'), 4)} |")
        L += ["", "| configuration | unified prediction: relative difference | unified prediction: z-correlation base~RS | native prediction relative difference |",
              "|---|---|---|---|"]
        for k, v in done.items():
            g = lambda m: v.get(m, {}).get("est")
            L.append(f"| {k} | {_f(g('L3/unified_prediction/rel_diff'), 4)} | {_f(g('L3/unified_prediction/zcorr'), 4)} | {_f(g('L3/native_prediction/rel_diff'), 4)} |")
        L += ["", "Native prediction difference: NCE scores u itself, so it equals the post-normalisation change; CS_SINGLE scores the native ridge "
              "prediction B_nat(u), whose relative change is reported.", ""]
    else:
        L += ["No configuration is fully covered yet: layers 1–2 and the per-query part of layer 3 are pending the GPU run, except the "
              f"{l13['n_units_zero']} epoch-0 units, which are exactly zero on every layer. The identity-level part of layer 3 is §6.", ""]
    if l13.get("dev_vs_test_units"):
        L += ["Development vs outer-test anchors of the same units (unit means; development = group-0 segments, training participants of the base, "
              "8 anchors per segment; test = all grid anchors):", "",
              "| configuration | units | ‖r‖/‖u‖ dev / test | angle dev / test (deg) | post-norm change dev / test |", "|---|---|---|---|---|"]
        for k, v in sorted(l13["dev_vs_test_units"].items()):
            L.append(f"| {k} | {v['n_units']} | {v['dev_rel_norm']:.4f} / {v['test_rel_norm']:.4f} | {v['dev_angle']:.3f} / {v['test_angle']:.3f} | "
                     f"{v['dev_post']:.4f} / {v['test_post']:.4f} |")
        L.append("")
    ec = out.get("engineering_checks") or {}
    hdr = ["| output | kind | device | seconds | bounded max |Δ| | all-metric max |Δ| base / RS | dev risk |Δ| selected / epoch 0 | u/r split vs forward | "
           "dev ‖r‖/‖u‖ · angle (deg) · post-norm change | peak RSS MB | code sha256 | reproduces |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for ver, title in (("v2", "v2 outputs (merged when full and reproducing)"), ("v1_kept_not_merged", "v1 outputs (kept; recorded hash = the file on disk at call time, "
                                                                                                          "intermediate versions not kept; not merged)")):
        e_ = ec.get(ver) or {}
        if not e_.get("outputs"):
            continue
        L += [f"**Engineering checks — {title}**, `{e_['dir']}/`. Rule: max |Δ| ≤ 1e-3 on per-participant log-loss and rank_pct (both readouts, both records) "
              "and on both saved development risks; top-1 / top-5 / MRR can move by 1/n_queries on a single near-tie flip and are reported, not bounded. "
              "The tolerance is for float order, not a performance gate. Tiny and development-only runs are not comparable to the records by design; "
              "the development-side layer values (dev ‖r‖/‖u‖ · angle · post-norm change, unit means over the development anchors) are shown for every "
              "output and are merged into the configuration summaries only through reproducing full runs.", ""] + hdr
        for e in e_["outputs"]:
            h = e["code_sha256_evaluator"] or e["code_sha256_file"]
            L.append(f"| {e['file']} ({e['cfg']}) | {e['kind']} | {e['device']} | {e['seconds']} | {_e(e['repro_bounded_max'])} | {_e(e['repro_max_abs_base'])} / "
                     f"{_e(e['repro_max_abs_rs'])} | {_e(e['dev_selected_abs_diff'])} / {_e(e['dev_epoch0_abs_diff'])} | {_e(e['forward_check'])} | "
                     f"{_f(e.get('dev_rel_norm'), 4)} · {_f(e.get('dev_angle_deg'), 3)} · {_f(e.get('dev_post_change'), 4)} | "
                     f"{e.get('process_peak_rss_mb') or '–'} | {(h or '–')[:12]}{' (evaluator, snapshot)' if e['evaluator_snapshot'] else (' (file)' if h else '')} | "
                     f"{'yes' if e['within_tolerance'] else ('n/a' if e['kind'] != 'full' else 'NO')} |")
        L += ["", f"Failed outputs: {e_.get('failed') or 'none'}.", ""]
    vv = out.get("v1_vs_v2_unit_outputs") or {}
    if vv:
        L += ["v1 vs v2 per-unit outputs of the same unit (every numeric result leaf; timing and provenance fields excluded):", "",
              "| output | numeric leaves | max |Δ| | largest at | per-query float arrays max |Δ| | per-query rank arrays: max fraction differing |", "|---|---|---|---|---|---|"]
        for f, v in vv.items():
            q = v.get("queries") or {}
            L.append(f"| {f} | {v['numeric_leaves']} | {_e(v['max_abs_diff'])} | {v['worst_leaf']} | {_e(q.get('max_abs_diff_float'))} | {_e(q.get('max_frac_differing_int'))} |")
        L.append("")
    # ---- 10. assets
    au = out["asset_audit"]; fm = au["fm_weights"]
    inv = au["RS"]["ckpt_inventory(seed 3401)"]
    L += ["## 10. Asset audit", "",
          f"- SC: {au['SC']['rows']} rows, {au['SC']['records_complete']} complete records ({au['SC']['variant_evaluations']} variant evaluations); "
          f"{au['SC']['state(seed,status,ckpt,eval_variants,fit_log)']}. Checkpoint files per unit: {au['SC']['ckpt_inventory']['file_patterns']}; "
          f"link targets {au['SC']['ckpt_inventory']['link_target_roots']}. Saved: {au['SC']['saved']}. Not saved: {au['SC']['not_saved']}.",
          f"- RS: {au['RS']['rows']} rows, per seed {au['RS']['per_seed']}; selected epoch {au['RS']['selected_epoch']}.",
          f"  - Seed-3401 checkpoint files per unit: {inv['file_patterns']} over {inv['units']} units; link states {inv['link_states']}; link targets "
          f"{inv['link_target_roots']}; units without exactly one file: {len(inv['units_without_exactly_one_file'])}.",
          f"  - Saved: {au['RS']['saved']}. Epoch 0: {au['RS']['epoch0']}. Not saved: {au['RS']['not_saved']}.",
          f"- Missing dependencies: {au['dependency_missing'] or 'none'}."]
    for k in ("L0 (A_LOCAL lag_local_tokens full)", "L1 (ALN32_LOCAL_SUPPORT local_aligned1000)"):
        i_ = au[k]["ckpt_inventory"]
        L.append(f"- {k}: {au[k]['state(dataset,objective,status,ckpt)']}; checkpoint files per unit {i_['file_patterns']}.")
    L.append("- FM weights vs the fetch receipt (sha256 computed now): " + "; ".join(
        f"{k} {v['n_match']}/{v['n_files']} files match (revision {str(v.get('revision'))[:7]})" if "n_match" in v else f"{k} {v['n_present']}/{v['n_files']} files present (no hashes in the receipt)"
        for k, v in fm.get("repos", {}).items()) + f". All hashed files match: {fm.get('all_hashed_files_match')}.")
    L += ["- Files named by an SC / RS / base experiment id (search by id; " + au["files_by_id_search"] + "):", "",
          "| role | directory | name | files | kind | contents |", "|---|---|---|---|---|---|"]
    for g in au["files_by_id"]:
        c = g.get("contents")
        cc = "–" if not c else (f"arrays {c.get('shapes_first_file')}; first dimension = participants in {c.get('first_dim_equals_participants')}; "
                                f"= test queries in {c.get('first_dim_equals_test_queries') or 'none'}")
        L.append(f"| {g['role']} | {g['dir']} | {g['pattern']} | {g['files']} | {g['kind']} | {cc} |")
    pq = au["per_query_prediction_files_outside_this_lane"]
    sci = [g for g in au["files_by_id"] if g["kind"] == "sci_r1 continuous-science output" and g["pattern"].endswith(".npz")]
    L += ["", f"- File groups whose arrays have a first dimension equal to a unit's number of test queries (per-query outputs) outside this lane: {len(pq)}"
          + (" (" + "; ".join(f"{g['dir']}/{g['pattern']}" for g in pq) + ")." if pq else ".")
          + (f" The sci_r1 arrays of the {sum(g['files'] for g in sci)} L0 units ({', '.join(sorted({k for g in sci for k in (g.get('contents') or {}).get('shapes_first_file', {})}))}) "
             "are indexed by participant (first dimension = the participants of the paired .json), i.e. per-participant lag and temporal-generalisation "
             "summaries, not per-query evaluator predictions." if sci else "")
          + " No per-query output of any SC, RS, L1 or L0 unit was saved, so L1–L3 need forward passes (§9, §11).", ""]
    # ---- 11. GPU plan
    gm = gp["gpu_memory_records"]
    gpu_runs = [(e["file"], e.get("gpu_peak_allocated_mb")) for e in (out.get("engineering_checks") or {}).get("v2", {}).get("outputs", []) if e.get("gpu_peak_allocated_mb")]
    L += ["## 11. GPU plan (written, not submitted)", "",
          f"- Unit list `{gp['units_file']}`: {gp['n_units_listed']} RS units with selected epoch > 0, of which {gp['n_units_pending']} are pending (the others have a "
          f"reproducing v2 output); the {gp['n_epoch0_units_exact_zero']} epoch-0 units need no run.",
          f"- Estimate for the pending units: about {gp['pending']['total_gpu_minutes']} GPU-minutes (range {gp['pending']['total_gpu_minutes_range'][0]}–"
          f"{gp['pending']['total_gpu_minutes_range'][1]}); {gp['basis']}. The records ran on {gp['record_devices']}.",
          ("- GPU memory: never measured for this evaluator (no GPU run). " if not gpu_runs else
           f"- GPU memory of this evaluator: {'; '.join(f'{f} {mb} MB' for f, mb in gpu_runs)}. ")
          + "The records' `gpu_peak_allocated_mb` is one process per unit covering training and evaluation: "
          + "; ".join(f"{k} {v['min_mb']}–{v['max_mb']} MB" for k, v in gm.items()) + ". Units above twice their group minimum: "
          + ("; ".join(f"{k} {v['units_above_2x_min']} units {v['their_range_mb'][0]}–{v['their_range_mb'][1]} MB on {', '.join(map(str, v['their_devices']))}"
                       for k, v in gm.items() if v["units_above_2x_min"]) or "none") + ".",
          f"- Worker: `{PY} -B -m auditory_alignment_v3.aln34.complement_function --units-file {gp['units_file']} --device cuda [--shard K/N]` with "
          "HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 (REVE loads) and PYTHONPATH at the repo root; atomic claims prevent duplicate work across parallel workers, a "
          "requeued worker releases its own claims, a unit is tried at most 3 times. Slurm template: "
          f"`{gp['sbatch_template']}` (follows the pool sbatch; not submitted; scheduling stays inside the 10-GPU cap).", ""]
    L += update_section(out)
    L += ["## Appendix: notes", ""] + [f"- {n}" for n in (tb["excluded_pairs"] + tb["notes"])[:60]] + [""]
    fd = os.open(path + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(L))
    os.chmod(path + ".tmp", 0o600); os.replace(path + ".tmp", path)
    return path


def update_section(out):
    """Package template EXPERIMENT_UPDATE: observation lines are computed; framing lines hold whatever the values are."""
    tb, l4, l13, gp = out["same_contract"], out["layer4_dev_test"], out["layers_1_3"], out["gpu_plan"]
    agree, ncell = local_only_copy_classes(tb)
    rcn0 = out["record_counts"]; ps = out["asset_audit"]["RS"]["per_seed"]
    L = ["## 12. Experiment update (observation → working judgement → competing explanations → next intervention → execution)", "",
         f"- Date and versions: {out['meta']['generated']}; code hashes in the header; unit records as read at aggregation ({rcn0}).",
         f"- Done / running / pending: SC and RS seed-3401 records complete; L1–L3 per query: {l13['n_units_run']} units run on CPU and reproduced, "
         f"{l13['n_units_zero']} exact epoch-0 zeros, {len(l13['pending_units'])} pending the GPU run; RS panel seeds (ADDENDUM_11, not used here): "
         + "; ".join(f"seed {k} {v.get('complete', 0)}/{v['rows']} complete" for k, v in ps.items() if k != str(SEED)) + ".",
         "- Already seen before this lane: the frozen SC / RS result tables (incl. their ΔR_native point estimates) and the brief's cross-document "
         "levels (analysis note §3). New in this lane (v1, recomputed identically in v2): the paired base → SC families of both readouts, the intervals "
         "of the native RS families, L4, the checkpoint layer and the L1–L3 values of RS·federici·NCE·small_capacity. New in v2 (analysis note, "
         "Correction 1, C1.12): the access table, the budgets, the cross-backbone copies, the asset search by id, the FM-weight hashes, and the CPU runs "
         "listed in §9 beyond the v1 ones.", "",
         "### 12.1 Observation (complete differences in §4–§9)", ""]
    for rd in READOUTS:
        c, ex = class_counts(tb, "FN-DIRECT-SC", rd)
        cd, _ = class_counts(tb, "FN-DIRECT-SC", rd, dedupe=True)
        L.append(f"- SC variant vs the original direct base, {rd} readout: simultaneous classes over the {sum(c.values())} members {dict(c)}. These include "
                 f"`local_only` twice per dataset · base (the cbramod and reve units share that ridge); over the {sum(cd.values())} distinct contrasts {dict(cd)}. "
                 f"I>0: {'; '.join(ex.get('I>0', [])) or 'none'}. Per dataset · base (both backbones, 12 members each, `local_only` in both):")
        for ds in DS:
            for base in ("L0", "L1"):
                ms = [m for lab, f in tb["families"].items() if f["family"] == "FN-DIRECT-SC" and f["readout"] == rd
                      and f["scope"].split("|")[0] == ds and f["scope"].split("|")[2] == base for m in f["members"].values() if "est" in m]
                if ms:
                    cc = Counter(m.get("class") for m in ms); best = max(ms, key=lambda m: m["est"])
                    L.append(f"  - {ds}·{base}: {dict(cc)}; ΔR from {min(m['est'] for m in ms):+.3f} to {best['est']:+.3f} "
                             f"(largest ΔR: {best['cand'].split('|')[3]}/{best['cand'].split('|')[5]} {best['est']:+.3f}, simultaneous "
                             f"[{best['sim_low']:+.3f}, {best['sim_high']:+.3f}])")
    cp = out.get("sc_backbone_copies") or {}
    cmax = lambda v: max([x for k, o in cp.items() if k.endswith("|" + v) for x in (o["max_identity_abs_diff_unified"], o["max_identity_abs_diff_native"]) if x is not None], default=None)
    aeq = lambda v: (sum(o["alpha_equal"] for k, o in cp.items() if k.endswith("|" + v)), sum(o["unit_pairs"] for k, o in cp.items() if k.endswith("|" + v)))
    L.append(f"- The two `local_only` copies agree in class in {agree} of {ncell} dataset · base · readout cells (max per-identity |ΔR| between the copies "
             f"{_e(cmax('local_only'))}). `local_refit_capacity` and `small_context` read no FM feature either, so both units of a cell see the same inputs: "
             f"the `local_refit_capacity` copies differ by at most {_e(cmax('local_refit_capacity'))} per identity (alpha equal in {aeq('local_refit_capacity')[0]} of "
             f"{aeq('local_refit_capacity')[1]} pairs), the same order as the `local_only` copies; the `small_context` copies by up to {_e(cmax('small_context'))} "
             f"(alpha equal in {aeq('small_context')[0]} of {aeq('small_context')[1]} pairs); its raw-window block is reduced by a randomised PCA drawn "
             "separately in each unit. They are near-duplicates or two draws of one design, not independent evidence.")
    for rd in READOUTS:
        c, ex = class_counts(tb, "FN-RS", rd)
        L.append(f"- RS selected epoch vs epoch 0, {rd} readout: simultaneous classes {dict(c)}. I<0: {'; '.join(ex.get('I<0', [])) or 'none'}. "
                 f"I>0: {'; '.join(ex.get('I>0', [])) or 'none'}.")
    rc = []
    for lab, f in tb["families"].items():
        sc = f["scope"].split("|")
        if f["family"] == "FN-DIRECT-SC" and sc[1] == "cbramod" and "est" in f["members"].get("local_only", {}):
            m = f["members"]["local_only"]
            rc.append(f"{sc[0]}·{sc[2]}·{f['readout']} {m['est']:+.3f} [{m['sim_low']:+.3f}, {m['sim_high']:+.3f}]")
    L.append("- Remapping alone (original base → SC `local_only`; the cbramod copy): " + "; ".join(rc) + ".")
    for k, v in l4["per_scope"].items():
        L.append(f"- L4 {k.replace('|', '·')}: {v['n_units']} units, {v['n_epoch0']} at epoch 0; mean Δdev {v['d_dev_mean']:+.4f} bits "
                 f"(relative {v['d_dev_rel_mean']:+.5f}); mean unit Δtest unified {v['d_test_R_unified_mean']:+.4f}, native {v['d_test_R_native_mean']:+.4f}; "
                 f"Spearman Δdev~Δtest native over epoch>0 units {_f(v['spearman_d_dev_d_test_native_epoch_gt0'], 2)}.")
    done = {k: v for k, v in l13["per_config"].items() if v.get("complete") and "L12/rel_norm" in v}
    for k, v in done.items():
        g = lambda m: v.get(m, {}).get("est")
        par = (g("L12/rel_par") or 0) / g("L12/rel_norm") if g("L12/rel_norm") else float("nan")
        L.append(f"- L1–L3 {k.replace('|', '·')} ({v['n_identities']} identities, all {v['n_units']} units): ‖r‖/‖u‖ {_f(g('L12/rel_norm'), 4)}, "
                 f"mean ‖r∥‖ / mean ‖r‖ {par:.3f} with signed parallel coefficient mean {_f(g('L12/coef'), 4)}, ‖r⊥‖/‖u‖ {_f(g('L12/rel_orth'), 4)}, "
                 f"post-normalisation change {_f(g('L12/post_change'), 4)}, angle {_f(g('L12/angle_deg'), 3)}°; queries whose true-candidate rank changed: unified "
                 f"{_f(g('L3/unified/frac_rank_changed'), 3)}, native {_f(g('L3/native/frac_rank_changed'), 3)}; ΔR unified {_f(g('L3/unified/d_logloss'), 4)}, "
                 f"native {_f(g('L3/native/d_logloss'), 4)}; native prediction relative difference {_f(g('L3/native_prediction/rel_diff'), 4)}.")
    if not done:
        L.append("- L1–L3: no configuration fully covered yet (pending the GPU run).")
    dn = ", ".join(k.replace("|", "·") for k in done) if done else ""
    st_l12 = (f"computed for {dn}; the other {len(l13['per_config']) - len(done)} configurations pending the GPU run" if done else "pending the GPU run")
    rcn = out["record_counts"]
    ev2_ = (out.get("engineering_checks") or {}).get("v2", {}).get("outputs", [])
    runs_desc = "; ".join(f"{k} x{v}" for k, v in sorted(Counter(f"{e['cfg']} {e['kind']} on {e['device']}" for e in ev2_).items()))
    fm_desc = sorted({f"{e['cfg'].split('|')[3]} {e['cfg'].split('|')[4]}: " + ("random init regenerated from the seed, no pretrained weights read"
                                                                           if e["cfg"].endswith("_random") else "pretrained weights read")
                      for e in ev2_ if e.get("cfg") and e["cfg"].split("|")[3] in ARCH})
    L += ["", "### 12.2 Working judgement (provisional; applies to these recipes and seed 3401 only)", "",
          "- Every SC number in the older tables is an increment over a remapped base. Whether a variant improves on what the base itself "
          "delivers is read from §5 (FN-DIRECT-SC); §5 is the same-system comparison asked for in docs/03 §1. Against L0, only `local_only` and "
          "`local_refit_capacity` are access-matched.",
          "- RS at epoch 0 is the base. A selected epoch > 0 is a training-side choice; whether it changed the representation, the predictions "
          "or the risk is read from §6–§9, not from the selected epoch."]
    for k, v in done.items():
        g = lambda m: v.get(m, {}).get("est")
        dr = [g(f"L3/{rd}/d_logloss") for rd in READOUTS]
        L.append(f"- {k.replace('|', '·')}: the selected residual moves the normalised representation by {_f(g('L12/post_change'), 4)} (angle "
                 f"{_f(g('L12/angle_deg'), 2)}°; ‖r‖/‖u‖ {_f(g('L12/rel_norm'), 4)}); the true-candidate rank changes in {g('L3/unified/frac_rank_changed'):.2f} "
                 f"(unified) / {g('L3/native/frac_rank_changed'):.2f} (native) of the queries; the identity-level ΔR is {_f(dr[0], 4)} "
                 f"{_iv(v.get('L3/unified/d_logloss', {}))} unified and {_f(dr[1], 4)} {_iv(v.get('L3/native/d_logloss', {}))} native (pointwise). "
                 f"So the representation and the rankings change while the identity-level risk moves by at most {max(abs(x) for x in dr if x is not None):.4f} "
                 "bits here (intervals as given); this says nothing about the FM-context configurations, which are pending the GPU run.")
    L += ["",
          "### 12.3 Competing explanations for RS ΔR ≈ 0 and the layer that separates them", "",
          "| explanation | evidence that separates it | status |", "|---|---|---|",
          f"| normalisation removes most of r (radial residual, D34) | L1 parallel share, L2 post-normalisation change and angle | {st_l12} |",
          f"| readout invariance: refitted bridge / temperature absorb the change | L3 unified prediction difference and rank changes vs the L2 change; τ ratios (§7) | "
          f"τ ratios from the saved records for all units; per-query part {st_l12} |",
          f"| the representation changes but carries no acoustic increment | ΔR ≈ 0 (§6, identity level, all units) while L2 / L3 changes are non-zero | "
          f"identity-level ΔR answered for all units; the L2 / L3 side {st_l12} |",
          "| cross-person selection mismatch: development gains do not carry to new listeners | L4: Δdev vs Δtest per unit (§7) | answered from saved records |", "",
          "### 12.4 Next intervention", "",
          f"- Run the per-unit evaluator on the {gp['n_units_pending']} pending units (`{gp['units_file']}`; about {gp['pending']['total_gpu_minutes']} GPU-minutes, range "
          f"{gp['pending']['total_gpu_minutes_range'][0]}–{gp['pending']['total_gpu_minutes_range'][1]}; assumption-based), then `--aggregate` on CPU. No retraining; old "
          "checkpoints are only read.",
          "- Each unit carries its own reproduction check; a flagged unit is reported, not merged.",
          "- When the ADDENDUM_11 panel completes, L4 can be repeated on seeds 3407 / 3413 (NCE).",
          "- SC per-query predictions would need a closed-form refit with the saved PCA bases and alphas on the same training rows (FM forwards for the FM "
          "variants). They are not needed for this card's questions and are not scheduled.", "",
          "### 12.5 Reuse and execution", "",
          f"- Reused unit records (seed 3401): {rcn}. SC: {out['asset_audit']['SC']['records_complete']} records holding "
          f"{out['asset_audit']['SC']['variant_evaluations']} variant evaluations. RS checkpoints read: "
          f"{sum(v['n_units'] for v in (out.get('checkpoint_layer') or {}).get('per_config', {}).values())}.",
          f"- FM weight files were hashed (§10). Evaluator runs (v2): {runs_desc or 'none'}; each read its unit checkpoint and its base checkpoint. "
          + (f"FM-context runs: {'; '.join(fm_desc)}." if fm_desc else "No FM-context run."),
          "- New CPU computation in this lane: this aggregation; the evaluator runs listed in §9. GPU: none submitted.", "",
          "### 12.6 Not decided here", "",
          "- Scheduling the listed GPU units within the 10-GPU cap is an operational step. Nothing in this report waits on a researcher decision.", ""]
    return L


def main(argv=None):
    os.umask(0o077)
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--audit", action="store_true"); g.add_argument("--aggregate", action="store_true"); g.add_argument("--write-units", action="store_true")
    g.add_argument("--unit"); g.add_argument("--units-file")
    a.add_argument("--device", default="cuda"); a.add_argument("--out", default=UNITS_DIR)
    a.add_argument("--tiny", action="store_true"); a.add_argument("--dev-only", action="store_true"); a.add_argument("--skip-ckpt", action="store_true")
    a.add_argument("--max-test-participants", type=int); a.add_argument("--max-queries", type=int); a.add_argument("--threads", type=int)
    a.add_argument("--shard"); a.add_argument("--max-tries", type=int, default=MAX_TRIES)
    args = a.parse_args(argv)
    if args.threads:
        import torch
        torch.set_num_threads(args.threads)
    if args.audit:
        print(json.dumps(_jl(audit_assets()), indent=1, default=str))
    elif args.aggregate:
        print(aggregate(skip_ckpt=args.skip_ckpt))
    elif args.write_units:
        print(write_units_file()[:5])
    elif args.unit:
        lim = Limits(tiny=args.tiny, max_test_participants=args.max_test_participants, max_queries=args.max_queries)
        print(evaluate_unit(args.unit, args.device, lim, args.dev_only, args.out))
    else:
        run_units_file(args.units_file, args.device, args.out, parse_shard(args.shard), args.max_tries)


if __name__ == "__main__":
    main()
