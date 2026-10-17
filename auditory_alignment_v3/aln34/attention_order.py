"""ALN3.4 R34_ATTENTION_ORDER: candidate-order correction of the D_ATTENTION learned attention integrator (v2).

Basis: package AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016 docs/04 section B, configs/adaptation_and_fusion.yaml `attention`
(orders both_A_B_and_B_A, new_logit half_h_d_minus_h_minus_d, tie_credit 0.5, refit head_only_when_possible, 5/10/20 s),
card R34_ATTENTION_ORDER, reference src/aln34_reference/attention.py. Analysis note (written before any value was computed):
private/auditory_alignment_v3/aln34/ATTENTION_ORDER_NOTE.md, v2 design in its section 11 (after an independent verification;
v1 archived unchanged in private/auditory_alignment_v3/aln34/attention_order_v1_20261016T2011/, v1 never produced a value).
Correction track: the old D_ATTENTION records, D_ATTENTION_RESULTS.md, d_lag.json and the D_MULTI_SEED outputs stay unchanged;
new rows carry evaluation_version aln34_attention_order_v2.

Legacy (auditory_alignment_v3/run_attention.py, frozen, imported only; the policy arms call the same attention_windows through
run_attention_policy._windows on FM representations): per window of 1/2/4 consecutive 5 s segments, d = score(attended)
- score(ignored) per segment; mean_score = 1(mean d > 0); learned_temporal = LogisticRegression(C=1) on [mean, sd, min, max,
last - first] fitted on the training participants' windows, each presented once in a random order (one rng, seed + 4242, shared
by every unit of a seed), and tested only in the fixed correct order. Per-window d was never saved: stage 1 recomputes it.

Arms: lag_local_tokens (seeds 3401/3407/3413; 180 models), dense_fm_policy and complement_policy (seed 3401; 58 + 55 completed
models; the incomplete policy rows are held executions and stay held).

Stage 1 (score extraction, GPU; one process per job, on the GPU model recorded in each unit record, note section 11.5):
    python -m auditory_alignment_v3.aln34.attention_order --unit-list FILE [--unit EID ...] [--arm A] [--dataset D]
        [--content-fold K] [--shard i/n] [--device auto|cuda|cpu] [--allow-device-mismatch] [--scores DIR]
  reloads the unit's saved model (the chosen candidate for alignment_plus_selection; dense arm: DenseFM + the fixed-feature head of
  the training-side target statistics; complement arm: Complement on the lag twin's frozen base and head), rebuilds the legacy
  readouts, segment lists and windows exactly as run_attention.attention_windows (frozen loaders / batchers / readouts imported) and
  writes per-segment d and the two scores (unified, native) of the unit's training and test windows to <scores>/<eid>.npz plus
  <eid>.json (meta and checks). Units whose recorded device is not the current GPU are skipped (listed) unless
  --allow-device-mismatch (then marked device_mismatch: never in the primary tables). Units sharing (dataset, content_fold) share
  one cohort load; existing score files are skipped (requeue-safe).
Stage 2 (CPU):  python -m auditory_alignment_v3.aln34.attention_order --analyze
  paired-order evaluation (both presentations of every window on the same split side, tie 0.5) of mean_score, the saved legacy
  learned_temporal and the antisymmetric learned integrator l(d) = 0.5[h(d) - h(-d)] (h on the legacy summaries of d / sigma,
  sigma = training-window RMS; tol 1e-10; fit status ok / zero_fit / not_converged / zero_scale / no_fit, only ok is scored);
  unit-level pairing; per-unit reproduction checks against the records (tier 1 primary, tier 2 sensitivity); identity-level
  bootstrap-t (B = 4,000) with max-t families; reproduction of the old fixed-order AT-INTEGRATOR under the original labels
  (seed 3401: d_lag.json; 3407 / 3413 / seed mean: d_multiseed.json); JSON + docs/auditory_alignment_v3/ATTENTION_ORDER_CORRECTION.md.
Utilities: --write-unit-list [FILE] (unit list + GPU plan from the record timings), --check-ckpt (presence + sha256 against the
offload manifest, incl. complement bases and the dense arm's lag-twin checkpoints).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import time
import warnings
from collections import Counter, defaultdict

import numpy as np

EVAL_VERSION = "aln34_attention_order_v2"
LAG, DENSE, COMP = "lag_local_tokens", "dense_fm_policy", "complement_policy"
ARMS = (LAG, DENSE, COMP)
SECONDS = (5, 10, 20)                      # = run_attention.SECONDS
READOUTS = ("unified", "native")
TIE_CREDIT = 0.5                           # configs/adaptation_and_fusion.yaml attention.tie_credit
MIN_TRAIN_WINDOWS = 20                     # run_attention: the learned integrator is fitted only with >= 20 training windows
LR_KW = {"C": 1.0, "max_iter": 1000}       # run_attention's LogisticRegression settings (lbfgs, tol 1e-4 default): legacy refit only
AS_LR_KW = {"C": 1.0, "max_iter": 10000, "tol": 1e-10}   # antisymmetric fit on d / sigma (note section 11.4)
FIT_STATUSES = ("ok", "zero_fit", "not_converged", "zero_scale", "no_fit")
LN2 = float(np.log(2.0))
DATASETS = ("fau", "dtu")
TASKS = (("attended_alignment", "NCE"), ("attended_alignment", "CS_SINGLE"), ("selection_only", "SELECTION_CE"),
         ("alignment_plus_selection", "NCE"), ("alignment_plus_selection", "CS_SINGLE"))   # = d_lag_interim.TASKS
SEL_WEIGHTS = (0.1, 1.0)                   # alignment_plus_selection candidates -> checkpoint suffix _c0 / _c1
SEEDS = (3401, 3407, 3413)
# tier 1 (primary inclusion; unchanged from note section 10) and tier 2 (sensitivity only; note section 11.5, kappa from 11.12)
QC_TOL = {"margin_abs": 1e-6, "margin_rel": 1e-5, "acc_windows": 1.0, "stats_rel": 1e-4, "coef_rel_flag": 1e-2}
QC_TOL2 = {"margin_abs": 1e-6, "margin_rel": 1e-5, "kappa_rms_s": None, "acc_frac": 0.02, "acc_min": 1}
# kappa_rms_s None = tier 2 not used in v2: the declared acceptance rule (note 11.5) failed in the TF32 calibration (note 11.12)
DEVICE_PARTITION = {"NVIDIA A40": "A40", "NVIDIA A30": "A30", "Tesla V100-PCIE-16GB": "V100-16GB", "Tesla V100S-PCIE-32GB": "V100-32GB"}
PARTITION_EXCLUDE = {"V100-16GB": "node42"}  # node42 (V100-16GB partition) also carries a V100-PCIE-32GB card
INTEG = {"ms": "mean_score, paired orders (tie 0.5)",
         "ms_fixed": "mean_score, legacy rule mean(d) > 0",
         "lt_fixed": "legacy learned_temporal, fixed correct order (as recorded)",
         "lt_paired": "legacy learned_temporal (saved coefficients), paired orders",
         "as": "antisymmetric learned 0.5[h(d) - h(-d)], h on s(d / sigma), paired-order training and evaluation"}
FAMS = (("AO-ANTISYM", "ms", "as", "mean_score -> antisymmetric_learned (paired orders)"),
        ("AO-PAIRED-LEGACY", "ms", "lt_paired", "mean_score -> legacy learned_temporal (paired orders)"),
        ("AO-FIXED", "ms_fixed", "lt_fixed", "mean_score -> legacy learned_temporal (fixed order, as recorded)"))
AO_FIXED_ARMS = (DENSE, COMP)              # lag arm: AO-FIXED only as the original-label reproduction (note section 11.6)
PROVENANCE = (
    "Seen before this analysis: the seed-3401 D_ATTENTION lag-arm results (D_ATTENTION_RESULTS.md, d_lag.json), including the "
    "degenerate native learned_temporal column. The panel's legacy fixed-order AT-INTEGRATOR values (3407, 3413, seed mean; unified "
    "and native) had been computed and written by the R34_D_PANEL lane of the same session (d_multiseed.json 20:01, "
    "D_MULTI_SEED_RESULTS.md §1.6 20:03) before this track's design was finalised; this lane did not read them (note §11.1), and "
    "here they are reproduction targets, not new evidence. The policy-arm attention values had never been aggregated and were not "
    "read. Every paired-order value (AO-PAIRED-LEGACY, AO-ANTISYM) and every policy-arm aggregate in this document is computed for "
    "the first time by this run.")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "private", "auditory_alignment_v3")
RES = os.environ.get("AO_RES", os.path.join(REPO, "results", "auditory_alignment_v3", "aln34", "attention_order"))
SCORES = os.environ.get("AO_SCORES", os.path.join(RES, "scores"))
DOCS = os.environ.get("AO_DOCS", os.path.join(REPO, "docs", "auditory_alignment_v3"))
NOTE = os.path.join(OUT, "aln34", "ATTENTION_ORDER_NOTE.md")
UNIT_LIST = os.path.join(OUT, "aln34", "attention_order_units.txt")
SBATCH = os.path.join(REPO, "auditory_alignment_v3", "aln34", "attention_order_extract.sbatch")
MANIFEST = os.path.join(OUT, "ckpt_offload_manifest.tsv")
A3C_LIST = os.path.join(REPO, "private", "ckpt_cleanup_20261015", "A3c_D_ATTENTION_D_COVERAGE_nondep.tsv")
OLD_D_LAG = os.path.join(REPO, "results", "auditory_alignment_v3", "d_lag", "d_lag.json")
OLD_D_MULTI = os.path.join(REPO, "results", "auditory_alignment_v3", "aln34", "d_multiseed", "d_multiseed.json")
CODE_FILES = ("auditory_alignment_v3/aln34/attention_order.py", "auditory_alignment_v3/run_attention.py",
              "auditory_alignment_v3/run_attention_policy.py", "auditory_alignment_v3/fm_attention.py", "auditory_alignment_v3/fm_dense.py",
              "auditory_alignment_v3/fm_complement.py", "auditory_alignment_v3/core.py", "auditory_alignment_v3/local_train.py",
              "auditory_alignment_v3/bc_interim.py", "auditory_alignment_v3/sci_r1/stats.py", "auditory_alignment/evaluate.py",
              "auditory_alignment/data.py", "auditory_alignment_v2/train.py", "auditory_alignment_v2/temporal.py",
              "auditory_alignment_v2/audio_targets.py", "auditory_alignment_v2/foundation_adapter.py", "auditory_alignment_v2/run.py")


# ================================================================================================ order-consistent scoring (numpy)
def summaries(D):
    """[windows, segments] -> [windows, 5] = [mean, sd, min, max, last - first] (row-wise run_attention._summ)."""
    D = np.asarray(D, dtype=np.float64)
    if D.ndim != 2 or D.shape[1] == 0:
        raise ValueError("D must be [windows, segments] with at least one segment")
    return np.column_stack([D.mean(1), D.std(1), D.min(1), D.max(1), D[:, -1] - D[:, 0]])


def linear_logit(coef, intercept, D):
    """h(d) = b0 + w . s(d); sklearn's order of operations (X @ coef^T + intercept)."""
    return (summaries(D) @ np.asarray(coef, np.float64).reshape(-1, 1) + float(intercept)).reshape(-1)


def antisymmetric_logit(h, D):
    """l(d) = 0.5 [h(d) - h(-d)], so l(-d) = -l(d) and sigmoid(l(-d)) = 1 - sigmoid(l(d)) (exactly, in floating point)."""
    D = np.asarray(D, np.float64)
    return 0.5 * (h(D) - h(-D))


def symmetric_part(h, D):
    """s(d) = 0.5 [h(d) + h(-d)]: the part of a logit that does not change when the two candidates are swapped."""
    D = np.asarray(D, np.float64)
    return 0.5 * (h(D) + h(-D))


def sigmoid(x):
    from scipy.special import expit
    return expit(np.asarray(x, np.float64))


def order_credit(lp, lm, tie=TIE_CREDIT):
    """Credit of one physical window presented as (A, B) with label 1 (logit lp) and as (B, A) with label 0 (logit lm): the mean of
    the two presentation credits, a logit of exactly 0 earning `tie`. One value per physical window (the swap adds no n)."""
    lp, lm = np.asarray(lp, np.float64), np.asarray(lm, np.float64)
    return 0.5 * ((lp > 0) + tie * (lp == 0) + (lm < 0) + tie * (lm == 0))


def order_logloss_bits(lp, lm):
    lp, lm = np.asarray(lp, np.float64), np.asarray(lm, np.float64)
    return 0.5 * (np.logaddexp(0.0, -lp) + np.logaddexp(0.0, lm)) / LN2


def legacy_fixed_correct(lp):
    """run_attention's test rule: correct iff predict_proba(attended first) > 0.5, i.e. expit(h(d)) > 0.5."""
    return (sigmoid(lp) > 0.5).astype(np.float64)


def paired_training_set(Dtr):
    """Both presentations of every training window, label flipped: (s(d), 1) and (s(-d), 0), weight 0.5 each (one unit of weight
    per physical window); `win` is the physical window id, so the two orders of a window can never fall on different split sides."""
    Dtr = np.asarray(Dtr, np.float64)
    n = len(Dtr)
    X = np.vstack([summaries(Dtr), summaries(-Dtr)])
    y = np.r_[np.ones(n, dtype=int), np.zeros(n, dtype=int)]
    return X, y, np.full(2 * n, 0.5), np.r_[np.arange(n), np.arange(n)]


def train_scale(Dtr):
    """sigma = sqrt(mean d^2) over every segment of the training windows: swap-invariant, training participants only."""
    Dtr = np.asarray(Dtr, np.float64)
    return float(np.sqrt(np.mean(Dtr ** 2))) if Dtr.size else float("nan")


def fit_antisymmetric(Dtr, lr_kw=None, min_train=MIN_TRAIN_WINDOWS):
    """h(d) = b0 + w . s(d / sigma) with the legacy summaries and estimator family, trained on paired orders (note section 11.4);
    scored as 0.5[h(d) - h(-d)]. Returns the fit with its status; only status 'ok' is ever scored."""
    from sklearn.linear_model import LogisticRegression
    kw = dict(AS_LR_KW if lr_kw is None else lr_kw)
    Dtr = np.asarray(Dtr, np.float64)
    n = int(len(Dtr))
    out = {"status": None, "n_train_windows": n, "sigma": None, "coef": None, "coef_scaled": None, "intercept": None, "n_iter": None,
           "estimator": {"class": "LogisticRegression", "solver": "lbfgs", **kw}}
    if n < min_train:
        out["status"] = "no_fit"
        return out
    sigma = train_scale(Dtr)
    out["sigma"] = sigma
    if not (np.isfinite(sigma) and sigma > 0):
        out["status"] = "zero_scale"
        return out
    X, y, w, _ = paired_training_set(Dtr / sigma)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lr = LogisticRegression(**kw).fit(X, y, sample_weight=w)
    cs, b0 = lr.coef_[0].astype(np.float64), float(lr.intercept_[0])
    n_iter = int(np.max(lr.n_iter_))
    anti = np.array([cs[0], 0.5 * (cs[2] + cs[3]), cs[4]])
    status = "ok"
    if n_iter == 0 or not np.any(anti != 0):
        status = "zero_fit"
    elif n_iter >= kw.get("max_iter", 100):
        status = "not_converged"
    h = lambda D: linear_logit(cs, b0, np.asarray(D, np.float64) / sigma)
    a, s = antisymmetric_logit(h, Dtr), symmetric_part(h, Dtr)
    out.update({"status": status, "coef_scaled": cs.tolist(), "coef": (cs / sigma).tolist(), "intercept": b0, "n_iter": n_iter,
                "warnings": sorted({str(c.message)[:160] for c in caught})[:3],
                "antisym_weights_scaled": {"mean": float(cs[0]), "min_plus_max": float(anti[1]), "last_minus_first": float(cs[4])},
                "coef_sum_5s": float(cs[0] + cs[2] + cs[3]),
                "sym_over_antisym_train": float(np.mean(np.abs(s)) / max(float(np.mean(np.abs(a))), 1e-300))})
    return out


def antisym_scorer(fit):
    """l(d) of an 'ok' fit, evaluated on d / sigma exactly as fitted."""
    cs, b0, sigma = fit["coef_scaled"], fit["intercept"], fit["sigma"]
    return lambda D: antisymmetric_logit(lambda X: linear_logit(cs, b0, np.asarray(X, np.float64) / sigma), D)


def evaluate_cell(Dtr, Dte, legacy=None, min_train=MIN_TRAIN_WINDOWS):
    """One (unit, window length, readout). Dtr: training windows (fit only), Dte: test windows (scored only), legacy: the saved
    run_attention integrator {coef, intercept} or None. Returns per-test-window arrays and the antisymmetric fit (with status)."""
    Dte = np.asarray(Dte, np.float64)
    m = Dte.mean(1)
    out = {"ms": order_credit(m, -m), "ms_fixed": (m > 0).astype(np.float64), "margin": m}
    if legacy is not None:
        h = lambda D: linear_logit(legacy["coef"], legacy["intercept"], D)
        lp, lm = h(Dte), h(-Dte)
        a, s = 0.5 * (lp - lm), 0.5 * (lp + lm)
        out.update({"lt_fixed": legacy_fixed_correct(lp), "lt_fixed_logit": (lp > 0).astype(np.float64), "lt_paired": order_credit(lp, lm),
                    "pos_plus": (s > np.abs(a)).astype(np.float64), "pos_minus": (s < -np.abs(a)).astype(np.float64),
                    "ll_lt_paired": order_logloss_bits(lp, lm), "lt_sym_abs": np.abs(s), "lt_antisym_abs": np.abs(a)})
    fit = fit_antisymmetric(Dtr, min_train=min_train)
    if fit["status"] == "ok":
        la = antisym_scorer(fit)(Dte)
        out.update({"as": order_credit(la, -la), "ll_as": order_logloss_bits(la, -la)})
    return out, fit


# ================================================================================================ unit rows, records, checkpoints
def arm_of(row):
    return row["spec"].get("architecture")


def unit_rows(rows=None):
    """[(mean_score row, learned_temporal twin id)] of the D_ATTENTION models of every arm (plan + plan_ext order)."""
    if rows is None:
        from auditory_alignment_v3 import run as r3
        rows = r3.all_rows()
    is_d = lambda r: r["family_id"] == "D_ATTENTION" and arm_of(r) in ARMS
    key = lambda r: (r["dataset"], r["subject_fold"], r["content_fold"], r["seed"],
                     json.dumps({k: v for k, v in r["spec"].items() if k != "integrator"}, sort_keys=True))
    twins = {key(r): r["experiment_id"] for r in rows if is_d(r) and r["spec"].get("integrator") == "learned_temporal"}
    return [(r, twins.get(key(r))) for r in rows if is_d(r) and r["spec"].get("integrator") == "mean_score"]


def load_record(eid, out=OUT):
    p = os.path.join(out, "units", f"{eid}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def checkpoint_file(row, rec):
    """The checkpoint the legacy evaluation used: <eid>_best.pt, or <eid>_c{k}_best.pt of the chosen alignment_plus_selection weight."""
    eid = row["experiment_id"]
    if row["spec"]["training_task"] != "alignment_plus_selection":
        return f"{eid}_best.pt", None
    w = rec["chosen_sel_weight"]
    k = SEL_WEIGHTS.index(w)
    if [c["sel_weight"] for c in rec["candidates"]] != list(SEL_WEIGHTS):
        raise ValueError(f"{eid}: candidate order {[c['sel_weight'] for c in rec['candidates']]} != {SEL_WEIGHTS}")
    return f"{eid}_c{k}_best.pt", k


def lag_twin_of(row, rows):
    """The lag_local_tokens mean_score unit of a policy-arm row (same dataset / folds / seed / task / objective)."""
    from auditory_alignment_v3 import run_attention_policy as RAP
    return RAP.lag_twin_row(row, rows)


def dependency_files(row, rec, rows=None, out=OUT):
    """Other checkpoints a unit's extraction reads: complement -> its frozen base (record dependency); dense -> the lag twin's
    checkpoint (target-statistics check only)."""
    arm = arm_of(row)
    if arm == COMP:
        return {"base": os.path.basename(rec["dependency"]["lag_base_checkpoint"])}
    if arm == DENSE:
        t = lag_twin_of(row, rows if rows is not None else _all_rows())
        trec = load_record(t["experiment_id"], out) if t else None
        if trec is None:
            return {"lag_twin": None}
        return {"lag_twin": checkpoint_file(t, trec)[0]}
    return {}


def _all_rows():
    from auditory_alignment_v3 import run as r3
    return r3.all_rows()


def manifest_index(path=MANIFEST):
    """file name -> sha256 of the last manifest line for it (offload manifest: time, eid, file, size, sha256, home, target, state)."""
    idx = {}
    if os.path.exists(path):
        for line in open(path):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 5:
                idx[p[2]] = p[4]
    return idx


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def code_sha256():
    return {f: sha256_file(os.path.join(REPO, f)) for f in CODE_FILES if os.path.exists(os.path.join(REPO, f))}


def a3c_files(path=A3C_LIST):
    return {os.path.basename(l.split("\t")[0]) for l in open(path)} if os.path.exists(path) else set()


def non_training_seconds(rec):
    """Recorded wall time of a unit outside training (cohort load(s) + full evaluation incl. the attention windows)."""
    tr = sum(c["curve"][-1]["seconds"] for c in rec["candidates"]) if rec.get("candidates") else rec.get("train_seconds", 0.0)
    return float(rec.get("total_seconds", 0.0)) - float(tr)


def unit_table(out=OUT, rows=None):
    """One entry per completed trained model of every arm (held / incomplete rows are counted, not listed)."""
    rows = rows if rows is not None else _all_rows()
    a3c, table, skipped = a3c_files(), [], Counter()
    for row, twin in unit_rows(rows):
        rec = load_record(row["experiment_id"], out)
        if rec is None or rec.get("status") != "complete":
            skipped[(arm_of(row), "incomplete_or_held")] += 1
            continue
        f, _ = checkpoint_file(row, rec)
        dep = dependency_files(row, rec, rows, out)
        dev = rec.get("device")
        table.append({"eid": row["experiment_id"], "arm": arm_of(row), "dataset": row["dataset"], "content_fold": row["content_fold"],
                      "subject_fold": row["subject_fold"], "seed": row["seed"], "task": row["spec"]["training_task"], "objective": row["spec"]["objective"],
                      "ckpt": f, "dep": dep.get("base") or dep.get("lag_twin") or "-", "record_device": dev,
                      "partition": DEVICE_PARTITION.get(dev, "?"), "on_A3c": f in a3c, "dep_on_A3c": (dep.get("base") or dep.get("lag_twin") or "") in a3c,
                      "twin": twin or "-", "non_training_seconds": round(non_training_seconds(rec), 1)})
    table.sort(key=lambda u: (u["partition"], u["dataset"], u["content_fold"], ARMS.index(u["arm"]), u["seed"], u["task"], u["objective"], u["subject_fold"]))
    return table, dict(skipped)


def gpu_plan(table):
    """Per partition: units, recorded non-training seconds (upper bound of the extraction wall time; see the unit-list header)."""
    plan = {}
    for u in table:
        p = plan.setdefault(u["partition"], {"units": 0, "by_arm": Counter(), "sum_s": 0.0, "max_s": 0.0, "cohorts": set()})
        p["units"] += 1; p["by_arm"][u["arm"]] += 1; p["sum_s"] += u["non_training_seconds"]; p["max_s"] = max(p["max_s"], u["non_training_seconds"])
        p["cohorts"].add((u["dataset"], u["content_fold"]))
    for p in plan.values():
        p["by_arm"] = dict(p["by_arm"]); p["cohorts"] = len(p["cohorts"]); p["sum_min"] = round(p["sum_s"] / 60.0, 1)
    return plan


def write_unit_list(path=UNIT_LIST, out=OUT, rows=None):
    table, skipped = unit_table(out, rows)
    plan = gpu_plan(table)
    tot = sum(p["sum_s"] for p in plan.values()) / 60.0
    rel = lambda p: os.path.relpath(p, REPO)
    hdr = [f"# R34_ATTENTION_ORDER unit list v2 ({len(table)} completed trained D_ATTENTION models; generated {time.strftime('%Y-%m-%d %H:%M %Z')} by",
           "# python -m auditory_alignment_v3.aln34.attention_order --write-unit-list; v1 list archived in",
           "# private/auditory_alignment_v3/aln34/attention_order_v1_20261016T2011/). One line per trained model; the learned_temporal twin",
           "# record is derived from the same model. ckpt = the checkpoint the legacy evaluation used (alignment_plus_selection: chosen",
           "# candidate). dep = complement_policy: its frozen lag base checkpoint (record dependency); dense_fm_policy: the lag twin's",
           "# checkpoint (target-statistics check only). Not listed (held / incomplete, they stay held): " + json.dumps({f"{a}|{k}": v for (a, k), v in sorted(skipped.items())}),
           "# on_A3c / dep_on_A3c = on private/ckpt_cleanup_20261015/A3c_D_ATTENTION_D_COVERAGE_nondep.tsv (pending deletion list):",
           "#   do not execute that deletion before every score file below exists, or these units need retraining.",
           "#",
           "# Stage 1 (score extraction; NOT submitted by the writing agent). Each unit must run on the GPU model recorded in its unit record",
           "#   (note section 11.5; the script skips other units). One job per partition, one process per job (units sorted by cohort):",
           ]
    for part in sorted(plan):
        p = plan[part]
        exc = f" --exclude={PARTITION_EXCLUDE[part]}" if part in PARTITION_EXCLUDE else ""
        hdr.append(f"#   cd /home/infres/yinwang/EEG_auditory && sbatch --partition={part}{exc} {rel(SBATCH)}")
        hdr.append(f"#     -> {p['units']} units {p['by_arm']}, {p['cohorts']} cohort loads; recorded non-training time sum {p['sum_min']} min, "
                   f"max {p['max_s']:.0f} s per unit")
    hdr += [f"#   GPU-time upper bound: {tot:.0f} GPU-min in total = the sum of the recorded non-training time of these units (cohort load +",
            "#   the full evaluation incl. the attention windows; lag units measured on A40 under MPS with up to 8 units per GPU, policy units",
            "#   one per GPU). Stage 1 loads each cohort once per job and recomputes only the attention-window forward passes, so the realised",
            "#   time should be below this bound; it is logged per unit (score meta 'seconds').",
            "#   Resources per job: --qos=runfill --gres=gpu:1 --cpus-per-task=4 --mem=32G (one process: the frozen loader peaks at ~8-9 GB",
            "#   host RAM; GPU <= ~11 GB). Under --qos=runfill the scheduler counts every job against the per-user gres/gpu=10 limit",
            "#   (MaxTRESPU), the same limit the pool uses, so the 10-GPU cap holds without any queue or hold edit: while 10 GPUs are in use",
            "#   the job pends (QOSMaxGRESPerUser) and takes the next free slot. The jobs are requeue-safe (existing score files are skipped).",
            "#   Do not run several stage-1 processes inside one job.",
            f"# Stage 2 (CPU, after all score files exist): sbatch -p CPU --cpus-per-task=2 --mem=8G --wrap 'cd /home/infres/yinwang/EEG_auditory && "
            "PYTHONPATH=$PWD /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m auditory_alignment_v3.aln34.attention_order --analyze'",
            "# eid\tarm\tdataset\tcontent_fold\tsubject_fold\tseed\ttraining_task\tobjective\tckpt\tdep\trecord_device\tpartition\ton_A3c\tdep_on_A3c\t"
            "twin_learned_temporal\trecorded_non_training_s"]
    body = [f"{u['eid']}\t{u['arm']}\t{u['dataset']}\t{u['content_fold']}\t{u['subject_fold']}\t{u['seed']}\t{u['task']}\t{u['objective']}\t{u['ckpt']}\t"
            f"{u['dep']}\t{u['record_device']}\t{u['partition']}\t{'yes' if u['on_A3c'] else 'no'}\t{'yes' if u['dep_on_A3c'] else ('-' if u['dep'] == '-' else 'no')}\t"
            f"{u['twin']}\t{u['non_training_seconds']}" for u in table]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as fh:
        fh.write("\n".join(hdr + body) + "\n")
    os.replace(path + ".tmp", path); os.chmod(path, 0o600)
    return path, len(body), plan


def read_unit_list(path):
    return [l.split("\t")[0].strip() for l in open(path) if l.strip() and not l.startswith("#")]


def check_checkpoints(out=OUT, rows=None):
    """Presence and sha256 (against the offload manifest) of every checkpoint stage 1 reads; reads the files, moves nothing."""
    man, a3c, res = manifest_index(), a3c_files(), []
    table, _ = unit_table(out, rows)
    for u in table:
        for kind, f in (("model", u["ckpt"]), ("dep", u["dep"])):
            if f == "-":
                continue
            p = os.path.join(out, "ckpt", f)
            ok = os.path.exists(p)
            sha = sha256_file(p) if ok else None
            res.append({"eid": u["eid"], "arm": u["arm"], "seed": u["seed"], "kind": kind, "file": f, "exists": ok, "symlink": os.path.islink(p),
                        "sha256_matches_manifest": (sha is not None and man.get(f) == sha), "manifest_entry": f in man, "on_A3c": f in a3c})
    return res


# ================================================================================================ stage 1: score extraction
def bound_row(row):
    """core.bind + the spec updates of run_attention.run (lag arm); compared with the record's bound_row."""
    from auditory_alignment_v3 import core
    b = core.bind(row); task = row["spec"]["training_task"]
    b["spec"].update({"architecture": "lag_local_tokens", "window": "full", "training_task": task,
                      "objective": "SELECTION_CE" if task == "selection_only" else row["spec"]["objective"]})
    return b


def legacy_attention_scores(b, enc, head, bt, coh, grid, reps=None):
    """run_attention.attention_windows up to the integrators, keeping d and both scores: the same readouts (training participants'
    single-speaker fit + es segments, rng seed + 1000), segment lists, 64-segment chunks (a chunk without any needed segment is
    skipped; the others are computed whole, as before) and windows (run_attention._runs / _windows). `reps`: the representation
    object the legacy code used (default ev1.Reps(enc, head, bt, stride=grid); policy arms: fm_dense.DenseReps / fm_complement.CompReps,
    as run_attention_policy._windows)."""
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v3 import run_attention as RA
    segs = coh.segments
    obj = "NCE" if b["spec"]["objective"] == "SELECTION_CE" else b["spec"]["objective"]
    reps = ev1.Reps(enc, head, bt, stride=grid) if reps is None else reps
    train_ss = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == "ss"]
    ro = ev1.Readouts(obj, reps, train_ss, np.random.default_rng(b["seed"] + 1000))
    cs = [s for s in segs if s["kind"] == "cs" and s.get("s0_ign") is not None]
    tr = [s for s in cs if s["p"] in bt.train_p and s["role"] in ("fit", "es")]
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and coh.participants[s["p"]]["fold"] == b["subject_fold"]})
    te = [s for s in cs if s["p"] in test_p and s["role"] == "test"]
    need = {id(s) for s in tr} | {id(s) for s in te}
    D, SA, SI = {}, {}, {}
    for k in range(0, len(cs), 64):
        q = cs[k:k + 64]
        if not any(id(s) in need for s in q):
            continue
        U = reps.u([s["e0"] for s in q]); Va, Aa = reps.va([s["s0"] for s in q]); Vi, Ai = reps.va([s["s0_ign"] for s in q])
        for i, s in enumerate(q):
            if id(s) in need:
                D[id(s)], SA[id(s)], SI[id(s)] = {}, {}, {}
                for kr in READOUTS:
                    sa = ro.scores(U[i:i + 1], Va[i:i + 1], Aa[i:i + 1], kr)[0, 0]
                    si = ro.scores(U[i:i + 1], Vi[i:i + 1], Ai[i:i + 1], kr)[0, 0]
                    D[id(s)][kr], SA[id(s)][kr], SI[id(s)][kr] = float(sa - si), float(sa), float(si)   # d as the legacy expression
    seg = [s for s in cs if id(s) in need]
    pos = {id(s): j for j, s in enumerate(seg)}
    out = {}
    for kr in READOUTS:
        out["d_" + kr] = np.array([D[id(s)][kr] for s in seg], np.float64)
        out["sa_" + kr] = np.array([SA[id(s)][kr] for s in seg], np.float64)
        out["si_" + kr] = np.array([SI[id(s)][kr] for s in seg], np.float64)
    out.update({"seg_p": np.array([s["p"] for s in seg], np.int64), "seg_e0": np.array([s["e0"] for s in seg], np.int64),
                "seg_role": np.array([s["role"] for s in seg]), "seg_code": np.array([str(s.get("code")) for s in seg]),
                "seg_uid": np.array([str(s.get("uid")) for s in seg]), "seg_pid": np.array([str(coh.participants[s["p"]]["id"]) for s in seg])})
    for L in SECONDS:
        for side, pool in (("train", tr), ("test", te)):
            W = RA._windows(RA._runs(pool, bt.seg_len), L // 5)
            out[f"win_{side}_{L}"] = np.array([[pos[id(s)] for s in w] for w in W], dtype=np.int64).reshape(-1, L // 5)
    parts = sorted({s["p"] for s in seg})
    out["part_id"] = np.array([str(coh.participants[p]["id"]) for p in parts]); out["part_group"] = np.array([str(coh.participants[p]["group"]) for p in parts])
    out["test_part_id"] = np.array([str(coh.participants[p]["id"]) for p in test_p])
    info = {"readout_objective": obj, "alpha_unified": float(ro.alpha_uni), "alpha_native": float(ro.alpha_nat) if hasattr(ro, "alpha_nat") else None,
            "n_train_ss": len(train_ss), "n_cs": len(cs), "n_segments_scored": len(seg)}
    return out, info


class CohortCache:
    """One (dataset, content_fold) cohort at a time. The EEG / target banks go to the device once, exactly as Batcher.__init__ makes
    them, and every unit's batcher (GridBatcher or fm_dense.DenseBatcher) is built by the frozen code on 1-sample placeholders and
    then pointed at the shared banks."""

    def __init__(self, dev, loader=None):
        self.dev, self.key, self.loader = dev, None, loader
        self.load_seconds = None

    def get(self, b):
        import torch
        from auditory_alignment_v2.train import TARGET
        t = TARGET[b["spec"]["target"]]
        key = (b["dataset"], b["content_fold"], t)
        if key != self.key:
            self.release()
            if self.loader is None:
                from auditory_alignment_v2.run import load_cohort as loader
            else:
                loader = self.loader
            t0 = time.time()
            coh = loader(b)
            self.E = torch.tensor(coh.eeg, device=self.dev, dtype=torch.float16)   # as Batcher.__init__
            self.S = torch.tensor(coh.stim[t], device=self.dev)                     # as Batcher.__init__ (the unit's target only)
            coh.eeg, coh.stim = None, None
            self.coh, self.key, self.load_seconds = coh, key, round(time.time() - t0, 1)
        return self.coh

    def batcher(self, b, grid, spec=None, cls=None):
        from auditory_alignment.data import AUDIO_FRAMES
        from auditory_alignment_v2.train import TARGET
        from auditory_alignment_v3 import local_train
        cls = cls or local_train.GridBatcher
        spec = spec if spec is not None else b["spec"]
        t = TARGET[spec["target"]]
        assert self.key == (b["dataset"], b["content_fold"], t)
        self.coh.eeg = np.zeros((self.E.shape[0], 1), np.float32); self.coh.stim = {t: np.zeros((self.S.shape[0], 1), np.float32)}
        bt = cls(self.coh, spec, b, self.dev, grid)
        bt.E, bt.S = self.E, self.S
        assert bt.audio_dim == bt.S.shape[0] * AUDIO_FRAMES
        return bt

    def release(self):
        if self.key is not None:
            import torch
            self.E = self.S = self.coh = None; self.key = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


def _write_npz(path, arrays):
    tmp = path + ".tmp.npz"
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path); os.chmod(path, 0o600)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(_jl(obj), f, indent=1)
    os.replace(path + ".tmp", path); os.chmod(path, 0o600)


def _jl(x):
    if isinstance(x, dict):
        return {str(k): _jl(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jl(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


class DeviceMismatch(RuntimeError):
    pass


def current_device_name(dev):
    import torch
    return torch.cuda.get_device_name(dev) if dev.type == "cuda" else "cpu"


def numerics_env(dev):
    import torch
    return {"device": current_device_name(dev), "torch": torch.__version__, "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
            "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32), "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "cudnn_benchmark": bool(torch.backends.cudnn.benchmark), "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
            "numpy": np.__version__}


def _head_stats_qc(stats, head_sd):
    mu_ck, sd_ck = head_sd["std.mu"].double().cpu().numpy(), head_sd["std.sd"].double().cpu().numpy()
    dmu = np.abs(np.asarray(stats[0], np.float64) - mu_ck)
    return {"mu_max_abs": float(np.max(dmu)), "mu_max_over_sd": float(np.max(dmu / np.abs(sd_ck))),
            "sd_max_rel": float(np.max(np.abs(np.asarray(stats[1], np.float64) - sd_ck) / np.abs(sd_ck)))}


def build_unit_model(row, rec, b, coh, cache, dev, ckpt_dir, rows=None):
    """Rebuild the trained model of one unit exactly as the legacy evaluation held it and load the saved checkpoint (strict).
    -> (reps, bt, info) where reps is the legacy representation object (ev1.Reps / DenseReps / CompReps)."""
    import torch
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v3 import core
    arm, d = arm_of(row), int(row["spec"].get("projection_dim", 32))
    g = core.grid_samples(coh.fs)
    fname, cand = checkpoint_file(row, rec)
    ck = os.path.join(ckpt_dir, fname)
    info = {"arm": arm, "grid": g, "checkpoint_file": fname, "candidate_index": cand, "checkpoint_path": ck}
    torch.manual_seed(b["seed"])
    if arm == LAG:
        bt = cache.batcher(b, g)
        enc = build_encoder(b["spec"]["architecture"], coh.n_ch, d, bt.W, coh.fs).to(dev)
        stats = target_stats(bt, np.random.default_rng(b["seed"] + 5))
        head = build_head(b["spec"].get("audio_head", "trainable_head"), bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
        sd = torch.load(ck, map_location=dev, weights_only=True)
        info["stats_qc"] = _head_stats_qc(stats, sd["head"]); info["stats_reference"] = "own checkpoint head buffers"
        enc.load_state_dict(sd["enc"], strict=True); head.load_state_dict(sd["head"], strict=True); enc.eval(); head.eval()
        return ev1.Reps(enc, head, bt, stride=g), bt, info
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v3 import fm_complement, fm_dense
    cs = rec["policy"]["chosen_spec"]
    if arm == DENSE:
        arch, ad, readout = cs["architecture"], cs["adaptation"], cs["readout"]
        if (b["spec"].get("architecture"), b["spec"].get("adaptation")) != (arch, ad):
            raise ValueError(f"{row['experiment_id']}: bound spec {b['spec'].get('architecture')}/{b['spec'].get('adaptation')} != chosen {arch}/{ad}")
        bb = Backbone(arch, coh.meta["dataset"], ad, coh.fs)
        bt = cache.batcher(b, g, cls=fm_dense.DenseBatcher)
        model = fm_dense.DenseFM(bb, readout, d, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
        stats = target_stats(bt, np.random.default_rng(b["seed"] + 5))
        head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
        sd = torch.load(ck, map_location=dev, weights_only=True)
        model.load_state_dict(sd["model"], strict=True); model.eval(); head.eval()
        dep = dependency_files(row, rec, rows)["lag_twin"]
        if dep:
            tsd = torch.load(os.path.join(ckpt_dir, dep), map_location="cpu", weights_only=True)
            info["stats_qc"] = _head_stats_qc(stats, tsd["head"]); info["stats_reference"] = f"lag twin checkpoint head buffers ({dep})"
        info.update({"chosen": rec["policy"].get("chosen"), "backbone": arch, "adaptation": ad, "readout": readout, "dependency_file": dep})
        return fm_dense.DenseReps(model, head, bt, g), bt, info
    if arm == COMP:
        variant, fm_arch = cs["variant"], cs["architecture"]
        bspec = dict(b["spec"]); bspec["architecture"] = "lag_local_tokens"; bspec["window"] = "full"
        bt = cache.batcher(b, g, spec=bspec, cls=fm_dense.DenseBatcher)
        base = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
        stats = target_stats(bt, np.random.default_rng(b["seed"] + 5))
        head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
        dep = dependency_files(row, rec, rows)["base"]
        bsd = torch.load(os.path.join(ckpt_dir, dep), map_location=dev, weights_only=True)
        info["stats_qc"] = _head_stats_qc(stats, bsd["head"]); info["stats_reference"] = f"base checkpoint head buffers ({dep})"
        base.load_state_dict(bsd["enc"], strict=True); head.load_state_dict(bsd["head"], strict=True); base.eval(); head.eval()
        ad, _ = fm_complement.VARIANT_FM[variant]
        bb = Backbone(fm_arch, coh.meta["dataset"], "random_full" if ad == "random_frozen" else ad, coh.fs)
        ctx = fm_complement.FMContext(bb, coh.fs, bt.seg_len, bt.ctx_len).to(dev)
        model = fm_complement.Complement(base, ctx, variant, d, base.n_tokens * 32).to(dev)
        sd = torch.load(ck, map_location=dev, weights_only=True)
        model.load_state_dict(sd["model"], strict=True); model.eval()
        info.update({"chosen": rec["policy"].get("chosen"), "backbone": fm_arch, "variant": variant, "dependency_file": dep})
        return fm_complement.CompReps(model, head, bt, g), bt, info
    raise ValueError(arm)


def extract_unit(row, twin, cache, dev, scores_dir=SCORES, out=OUT, man=None, ckpt_dir=None, rows=None, allow_device_mismatch=False):
    """Stage 1 for one trained model: per-segment d and scores of its training and test windows -> <scores>/<eid>.npz + .json
    (json = done)."""
    import torch
    eid = row["experiment_id"]
    jp, npz = os.path.join(scores_dir, f"{eid}.json"), os.path.join(scores_dir, f"{eid}.npz")
    if os.path.exists(jp) and os.path.exists(npz):
        print("skip (scores exist)", eid, flush=True); return jp
    rec = load_record(eid, out)
    if rec is None or rec.get("status") != "complete":
        raise RuntimeError(f"{eid}: no complete unit record")
    env = numerics_env(dev)
    dev_match = env["device"] == rec.get("device")
    if not dev_match and not allow_device_mismatch:
        raise DeviceMismatch(f"{eid}: recorded on {rec.get('device')}, current {env['device']}")
    t0 = time.time()
    ckpt_dir = ckpt_dir or os.path.join(out, "ckpt")
    man = manifest_index() if man is None else man
    b = copy.deepcopy(rec["bound_row"])
    binding = None
    if arm_of(row) == LAG:
        rb = bound_row(row)
        binding = all(rb.get(k) == b.get(k) for k in ("dataset", "subject_fold", "content_fold", "seed")) and \
            all(rb["spec"].get(k) == b["spec"].get(k) for k in rb["spec"] if k != "epochs")
    coh = cache.get(b)
    reps, bt, info = build_unit_model(row, rec, b, coh, cache, dev, ckpt_dir, rows)
    with torch.no_grad():
        arrays, rinfo = legacy_attention_scores(b, None, None, bt, coh, info["grid"], reps=reps)
    wc = {L: {"train": int(len(arrays[f"win_train_{L}"])), "test": int(len(arrays[f"win_test_{L}"]))} for L in SECONDS}
    rwc = rec["eval"]["attention_windows"]["window_counts"]
    files = {"model": info["checkpoint_file"], **({"dependency": info["dependency_file"]} if info.get("dependency_file") else {})}
    ck = {}
    for k, f in files.items():
        p = os.path.join(ckpt_dir, f); sha = sha256_file(p)
        ck[k] = {"file": f, "sha256": sha, "manifest_sha256": man.get(f), "manifest_match": man.get(f) == sha, "resolved": os.path.realpath(p)}
    meta = {"experiment_id": eid, "evaluation_version": EVAL_VERSION, "arm": arm_of(row), "twin_learned_temporal": twin, "row": row,
            "bound_row": b, "binding_matches_reconstruction": binding,
            "checkpoint": {**ck["model"], "candidate_index": info["candidate_index"], "chosen_sel_weight": rec.get("chosen_sel_weight")},
            "dependency_checkpoint": ck.get("dependency"), "model_info": {k: v for k, v in info.items() if k not in ("stats_qc", "checkpoint_path")},
            "record": {"code_hash": rec.get("code_hash"), "code_group": rec.get("code_group"), "device": rec.get("device")},
            "numerics": env, "device_match": dev_match, "stats_qc": info.get("stats_qc"), "stats_reference": info.get("stats_reference"),
            "window_counts": wc, "window_counts_match_record": all(wc[L] == {"train": rwc[str(L)]["train"], "test": rwc[str(L)]["test"]} for L in SECONDS),
            "readout": rinfo, "code_sha256": code_sha256(), "cohort_load_seconds": cache.load_seconds, "seconds": round(time.time() - t0, 1),
            "slurm_job": os.environ.get("SLURM_JOB_ID"), "host": os.environ.get("SLURMD_NODENAME"), "created": time.strftime("%Y-%m-%d %H:%M:%S %Z")}
    os.makedirs(scores_dir, exist_ok=True)
    _write_npz(npz, arrays)
    _write_json(jp, meta)
    print(eid, arm_of(row), "scores", rinfo["n_segments_scored"], "segments", meta["seconds"], "s", "device", env["device"], "match", dev_match,
          "manifest", {k: v["manifest_match"] for k, v in ck.items()}, "windows_match", meta["window_counts_match_record"], "stats", info.get("stats_qc"), flush=True)
    return jp


def scores_from_arrays(z, meta=None):
    """Score arrays (as written by extract_unit / returned by legacy_attention_scores) -> the structure evaluate_unit reads."""
    sc = {"meta": meta or {}, "d": {kr: np.asarray(z["d_" + kr]) for kr in READOUTS}, "seg_pid": np.asarray(z["seg_pid"]),
          "win_train": {L: np.asarray(z[f"win_train_{L}"]) for L in SECONDS}, "win_test": {L: np.asarray(z[f"win_test_{L}"]) for L in SECONDS},
          "part_group": dict(zip(np.asarray(z["part_id"]).tolist(), np.asarray(z["part_group"]).tolist()))}
    if all(f"sa_{kr}" in z and f"si_{kr}" in z for kr in READOUTS):
        sc["s_att"] = {kr: np.asarray(z["sa_" + kr]) for kr in READOUTS}
        sc["s_ign"] = {kr: np.asarray(z["si_" + kr]) for kr in READOUTS}
    return sc


def load_scores(scores_dir, eid):
    jp, npz = os.path.join(scores_dir, f"{eid}.json"), os.path.join(scores_dir, f"{eid}.npz")
    if not (os.path.exists(jp) and os.path.exists(npz)):
        return None
    with np.load(npz, allow_pickle=False) as z:
        return scores_from_arrays({k: z[k] for k in z.files}, json.load(open(jp)))


# ================================================================================================ stage 2: per-unit evaluation + QC
def evaluate_unit(sc, aw):
    """Per test participant x window x readout: mean credits of every integrator (+ diagnostics, rms_s for the tier-2 QC); the
    antisymmetric fits use training windows only."""
    per, fits = defaultdict(dict), {}
    pid = sc["seg_pid"]
    for L in SECONDS:
        wtr, wte = sc["win_train"][L], sc["win_test"][L]
        wp = pid[wte[:, 0]] if len(wte) else np.array([], dtype=str)
        for kr in READOUTS:
            d = sc["d"][kr]
            cell, fit = evaluate_cell(d[wtr] if len(wtr) else np.zeros((0, L // 5)), d[wte], aw.get("integrators", {}).get(f"{L}s|{kr}"))
            fits[f"{L}s|{kr}"] = fit
            sa, si = sc.get("s_att", {}).get(kr), sc.get("s_ign", {}).get(kr)
            for p in sorted(set(wp.tolist())):
                sel = wp == p
                r = {k: float(v[sel].mean()) for k, v in cell.items()}
                r["n_windows"] = int(sel.sum())
                if sa is not None:
                    j = wte[sel].ravel()
                    r["rms_s"] = float(np.sqrt(np.mean(np.r_[sa[j], si[j]] ** 2)))
                per[str(p)][f"{L}s|{kr}"] = r
    return dict(per), fits


def legacy_refit(sc, seed):
    """The run_attention learned_temporal fit on the recomputed training windows (same flip stream, rng seed + 4242, same order)."""
    from sklearn.linear_model import LogisticRegression
    from auditory_alignment_v3 import run_attention as RA
    rng = np.random.default_rng(seed + 4242); out = {}
    for L in SECONDS:
        wtr = sc["win_train"][L]
        for kr in READOUTS:
            if len(wtr) >= MIN_TRAIN_WINDOWS:
                X, y = [], []
                for w in wtr:
                    d = sc["d"][kr][w]; flip = rng.random() < 0.5
                    X.append(RA._summ(-d if flip else d)); y.append(0 if flip else 1)
                lr = LogisticRegression(**LR_KW).fit(np.array(X), np.array(y))
                out[f"{L}s|{kr}"] = {"coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]), "n_train_windows": int(len(wtr)),
                                     "label1_share": float(np.mean(y))}
    return out


def unit_qc(sc, per, aw, refit=None, tol=QC_TOL, tol2=QC_TOL2):
    """Recomputed legacy quantities against the unit record. Tier 1 (primary inclusion): every check at the tight tolerance on a
    device-matched extraction. Tier 2 (sensitivity only): the structural checks hold and margins / accuracies agree within the
    device-robust tolerance (note section 11.5)."""
    hard, num1, num2 = [], [], []
    err = {"margin": 0.0, "margin_over_rms_s": 0.0, "ms_windows": 0.0, "lt_windows": 0.0, "coef_rel": 0.0}
    meta = sc.get("meta", {}) or {}
    if meta:
        if not meta.get("checkpoint", {}).get("manifest_match", False):
            hard.append("checkpoint sha256 differs from the offload manifest (or no entry)")
        dep = meta.get("dependency_checkpoint")
        if dep is not None and not dep.get("manifest_match", False):
            hard.append(f"dependency checkpoint {dep.get('file')} sha256 differs from the offload manifest (or no entry)")
        sq = meta.get("stats_qc")
        if sq is None and meta.get("arm", LAG) != DENSE:
            hard.append("no target-statistics check")
        elif sq is not None and max(sq.get("sd_max_rel", 0.0), sq.get("mu_max_over_sd", sq.get("mu_max_abs", 0.0))) > tol["stats_rel"]:
            hard.append(f"recomputed target statistics differ from the reference head buffers: {sq}")
        if meta.get("binding_matches_reconstruction") is False:
            hard.append("record bound_row differs from the reconstructed binding")
    device_mismatch = meta.get("device_match") is False
    for kr, d in (sc.get("d") or {}).items():  # NaN/inf differences would otherwise score 0 credit silently (review 2026-10-16)
        if not np.isfinite(np.asarray(d, np.float64)).all():
            hard.append(f"non-finite score differences ({kr}): {int((~np.isfinite(np.asarray(d, np.float64))).sum())} segments")
    for L in SECONDS:
        rc = aw["window_counts"].get(str(L), aw["window_counts"].get(L))
        if rc != {"train": int(len(sc["win_train"][L])), "test": int(len(sc["win_test"][L]))}:
            hard.append(f"window counts {L}s differ from the record")
    rp = aw["per_participant"]
    if set(rp) != set(per):
        hard.append(f"test participants differ: record {len(rp)}, recomputed {len(per)}")
    k2 = tol2.get("kappa_rms_s") if tol2 else None
    for p, r in rp.items():
        for key, v in r.items():
            if not isinstance(v, dict):
                continue
            x = per.get(p, {}).get(key)
            if x is None:
                hard.append(f"{p}/{key} missing in the recomputation"); continue
            n = v["n_windows"]
            if x["n_windows"] != n:
                hard.append(f"{p}/{key} n_windows {x['n_windows']} != {n}"); continue
            acc2 = max(tol2.get("acc_min", 1), math.ceil(tol2.get("acc_frac", 0.0) * n)) if tol2 else None
            if v.get("mean_margin") is not None:
                if not math.isfinite(x["margin"]):
                    hard.append(f"{p}/{key} recomputed mean margin is not finite"); continue
                e = abs(x["margin"] - v["mean_margin"]); err["margin"] = max(err["margin"], e)
                if e > tol["margin_abs"] + tol["margin_rel"] * abs(v["mean_margin"]):
                    num1.append(f"{p}/{key} mean margin differs by {e:.3g}")
                rms = x.get("rms_s")
                if rms is not None and rms > 0:
                    err["margin_over_rms_s"] = max(err["margin_over_rms_s"], e / rms)
                if k2 is not None:
                    if rms is None:
                        num2.append(f"{p}/{key}: no score scale for the tier-2 margin check")
                    elif e > tol2["margin_abs"] + tol2["margin_rel"] * abs(v["mean_margin"]) + k2 * rms:
                        num2.append(f"{p}/{key} mean margin differs by {e:.3g} (> tier-2 tolerance)")
            for name, xk, vk, ek in (("mean_score", "ms_fixed", "mean_score_accuracy", "ms_windows"), ("learned_temporal", "lt_fixed", "learned_temporal_accuracy", "lt_windows")):
                if v.get(vk) is None:
                    continue
                if xk not in x:
                    hard.append(f"{p}/{key} legacy integrator missing"); continue
                e = abs(x[xk] - v[vk]) * n; err[ek] = max(err[ek], e)
                if e > tol["acc_windows"] + 1e-9:
                    num1.append(f"{p}/{key} {name} accuracy differs by {e:.2f} windows")
                if acc2 is not None and e > acc2 + 1e-9:
                    num2.append(f"{p}/{key} {name} accuracy differs by {e:.2f} windows (> tier-2 tolerance {acc2})")
    flags = []
    for k, sv in (refit or {}).items():
        ov = aw["integrators"].get(k)
        if ov is None:
            flags.append(f"{k}: no saved integrator"); continue
        a, o = np.r_[sv["coef"], sv["intercept"]], np.r_[ov["coef"], ov["intercept"]]
        e = float(np.max(np.abs(a - o)) / max(float(np.max(np.abs(o))), 1e-12)); err["coef_rel"] = max(err["coef_rel"], e)
        if e > tol["coef_rel_flag"]:
            flags.append(f"{k}: legacy refit coefficients differ (relative {e:.3g})")
    tier1 = not hard and not num1 and not device_mismatch
    tier2 = (not tier1) and not hard and k2 is not None and not num2
    return {"pass": tier1, "tier": 1 if tier1 else (2 if tier2 else 0), "device_mismatch": device_mismatch,
            "reasons": (hard + num1)[:50], "n_reasons": len(hard) + len(num1), "structural_reasons": hard[:20],
            "tier2_reasons": num2[:20], "flags": flags, "max_errors": err}


# ================================================================================================ stage 2: aggregation
def _mean_dict(d):
    return {i: {m: float(np.mean(v)) for m, v in x.items() if v} for i, x in d.items()}


def _summ_level(S, y, seed_key):
    y = np.asarray(y, np.float64)
    if len(y) < 3:
        return {"n": int(len(y)), "est": float(y.mean()) if len(y) else None}
    s = S.summary(y, seed=S.group_seed(*seed_key))
    return {"n": int(len(y)), **{k: float(s[k]) for k in ("est", "ci_low", "ci_high")}}


def fam_label(fam, arm, ds, task, obj, seed):
    """lag arm: the labels declared in note sections 6 / 10; policy arms carry the arm."""
    return f"{fam}|{ds}|{task}|{obj}|{seed}" if arm == LAG else f"{fam}|{arm}|{ds}|{task}|{obj}|{seed}"


class Acc:
    """Accumulators of one inclusion tier: unit-level paired contrasts, integrator levels, logloss pairs, diagnostics."""

    def __init__(self):
        dd = lambda: defaultdict(lambda: defaultdict(list))
        self.pairs = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))   # (fam, arm, ds, task, obj, L, seed) -> pid -> metric -> [(ref, cand)]
        self.lev = defaultdict(dd)                                                  # ("AO", arm, ds, task, obj, integ, L, seed) -> pid -> metric -> [x]
        self.ll = defaultdict(lambda: defaultdict(list))                            # (arm, ds, task, obj, L, seed, kr) -> pid -> [(ll_lt, ll_as)]
        self.diag = defaultdict(dd)                                                 # (arm, ds, task, obj, seed, L, kr) -> pid -> key -> [x]
        self.att = defaultdict(lambda: defaultdict(dd))                             # seed -> ("ATT", ds, task, obj, ms|lt, L) -> pid -> metric -> [x]
        self.excl = Counter()                                                       # (fam, arm, ds, task, obj, seed, L, kr, reason) -> unit-cells

    def add_unit(self, arm, ds, task, obj, seed, per, fits):
        for pid, r in per.items():
            for L in SECONDS:
                for kr in READOUTS:
                    x = r.get(f"{L}s|{kr}")
                    if not x or not x["n_windows"]:
                        continue
                    met = "acc" if kr == "unified" else "acc_native"
                    for integ in INTEG:
                        if integ in x:
                            self.lev[("AO", arm, ds, task, obj, integ, L, seed)][pid][met].append(x[integ])
                    for fam, ref, cand, _ in FAMS:
                        if ref in x and cand in x:
                            self.pairs[(fam, arm, ds, task, obj, L, seed)][pid][met].append((x[ref], x[cand]))
                        else:
                            why = (fits.get(f"{L}s|{kr}") or {}).get("status") if cand == "as" else "no saved legacy integrator"
                            self.excl[(fam, arm, ds, task, obj, seed, L, kr, why or "missing")] += 1
                    if "ll_lt_paired" in x and "ll_as" in x:
                        self.ll[(arm, ds, task, obj, L, seed, kr)][pid].append((x["ll_lt_paired"], x["ll_as"]))
                    for k in ("pos_plus", "pos_minus", "ll_lt_paired", "ll_as", "lt_sym_abs", "lt_antisym_abs"):
                        if k in x:
                            self.diag[(arm, ds, task, obj, seed, L, kr)][pid][k].append(x[k])
                    if "lt_fixed_logit" in x and "lt_paired" in x:
                        self.diag[(arm, ds, task, obj, seed, L, kr)][pid]["fixed_minus_paired"].append(x["lt_fixed_logit"] - x["lt_paired"])
                        self.diag[(arm, ds, task, obj, seed, L, kr)][pid]["identity_rhs"].append(0.5 * (x["pos_plus"] - x["pos_minus"]))
                    if arm == LAG:   # d_lag_interim.collect format (fixed-order legacy values), for the original-label reproduction
                        for integ, key in (("ms", "ms_fixed"), ("lt", "lt_fixed")):
                            if key in x:
                                self.att[seed][("ATT", ds, task, obj, integ, L)][pid][met].append(x[key])


def contrast_vals(acc):
    """Unit-level paired contrasts -> pseudo-configurations ("AOP", fam, arm, ds, task, obj, ref|cand, L, seed) of identity means
    (reference and candidate averaged over the same units), plus the complete-case seed mean of the lag panel cells."""
    vals = {}
    for (fam, arm, ds, task, obj, L, seed), per in acc.pairs.items():
        R, C = ("AOP", fam, arm, ds, task, obj, "ref", L, seed), ("AOP", fam, arm, ds, task, obj, "cand", L, seed)
        vr, vc = {}, {}
        for pid, mets in per.items():
            for m, prs in mets.items():
                if prs:
                    vr.setdefault(pid, {})[m] = float(np.mean([a for a, _ in prs])); vc.setdefault(pid, {})[m] = float(np.mean([c for _, c in prs]))
        vals[R], vals[C] = vr, vc
    seed_cov = {}
    for fam, _, _, _ in FAMS:
        for arm, ds, task, obj in sorted({k[1:5] for k in acc.pairs if k[0] == fam}):
            for L in SECONDS:
                cells = [(("AOP", fam, arm, ds, task, obj, "ref", L, s), ("AOP", fam, arm, ds, task, obj, "cand", L, s)) for s in SEEDS]
                if not all(R in vals and C in vals for R, C in cells):
                    continue
                vr, vc, cov = {}, {}, {}
                for m in ("acc", "acc_native"):
                    ids = sorted(set.intersection(*[{i for i in vals[R] if m in vals[R][i]} for R, _ in cells]))
                    cov[m] = len(ids)
                    for i in ids:
                        vr.setdefault(i, {})[m] = float(np.mean([vals[R][i][m] for R, _ in cells]))
                        vc.setdefault(i, {})[m] = float(np.mean([vals[C][i][m] for _, C in cells]))
                vals[("AOP", fam, arm, ds, task, obj, "ref", L, "mean")], vals[("AOP", fam, arm, ds, task, obj, "cand", L, "mean")] = vr, vc
                seed_cov[f"{fam}|{arm}|{ds}|{task}|{obj}|{L}s"] = {"identities_all_seeds": cov,
                                                                  **{str(s): len(vals[R]) for s, (R, _) in zip(SEEDS, cells)}}
    return vals, seed_cov


def build_families(vals, include_fixed_arms=AO_FIXED_ARMS):
    """Declared families: per family type, arm, dataset, task / objective and seed (incl. 'mean'): 3 members (5 / 10 / 20 s)."""
    out = []
    present = sorted({(c[1], c[2], c[3], c[4], c[5], c[8]) for c in vals if c[0] == "AOP"}, key=str)
    for fam, arm, ds, task, obj, seed in present:
        if fam == "AO-FIXED" and arm not in include_fixed_arms:
            continue
        tag = next(t for f, _, _, t in FAMS if f == fam)
        members = [(f"{L}s", ("AOP", fam, arm, ds, task, obj, "ref", L, seed), ("AOP", fam, arm, ds, task, obj, "cand", L, seed), tag) for L in SECONDS]
        members = [m for m in members if m[1] in vals and m[2] in vals]
        if members:
            out.append((fam, arm, f"{arm}|{ds}|{task}|{obj}|{seed}", fam_label(fam, arm, ds, task, obj, seed), members))
    return out


def run_families(vals, grp, BI, notes):
    fams = {"families": {}, "secondary": {}}
    for fam, arm, scope, label, members in build_families(vals):
        ds = scope.split("|")[1]
        g = lambda i, ds=ds: grp.get((ds, i))
        fams["families"][label] = {"family": fam, "arm": arm, "scope": scope, **BI.run_family(label, members, vals, "acc", notes, True, g)}
        fams["secondary"][label] = {"acc_native": BI.run_family(f"{label}|sec", members, vals, "acc_native", notes, False)}
    return fams


def logloss_table(acc, S):
    """Secondary, pointwise (note section 11.7): identity-level logloss (bits) of the two learned integrators on the same units and
    their paired difference (antisymmetric - legacy; negative = antisymmetric better)."""
    out = {}
    for key, per in sorted(acc.ll.items(), key=lambda kv: str(kv[0])):
        arm, ds, task, obj, L, seed, kr = key
        ids = sorted(per)
        lt = np.array([np.mean([a for a, _ in per[i]]) for i in ids]); an = np.array([np.mean([b for _, b in per[i]]) for i in ids])
        k = f"{arm}|{ds}|{task}|{obj}|{seed}|{L}s|{kr}"
        out[k] = {"n": len(ids), "legacy_paired": _summ_level(S, lt, ("AO-LOGLOSS", k, "legacy")),
                  "antisymmetric": _summ_level(S, an, ("AO-LOGLOSS", k, "antisym")),
                  "antisym_minus_legacy": _summ_level(S, an - lt, ("AO-LOGLOSS", k, "diff"))}
    return out


def _cmp_member(new, old, fields=("est", "se", "ci_low", "ci_high", "sim_low", "sim_high")):
    ks = [k for k in fields if k in new and k in old]
    return {"max_abs_diff": max([abs(new[k] - old[k]) for k in ks] or [float("nan")]), "fields": ks, "n_new": new.get("n"), "n_old": old.get("n"),
            "class_new": new.get("class"), "class_old": old.get("class"), "class_agree": new.get("class") == old.get("class")}


def _summarise_cmp(rows):
    diffs = [r["max_abs_diff"] for r in rows if r["max_abs_diff"] == r["max_abs_diff"]]
    cls_rows = [r for r in rows if r["class_old"] is not None]
    return {"members_compared": len(rows), "max_abs_diff": max(diffs) if diffs else None,
            "class_agreement": f"{sum(r['class_agree'] for r in cls_rows)}/{len(cls_rows)}", "n_agreement": f"{sum(r['n_new'] == r['n_old'] for r in rows)}/{len(rows)}"}


def _att_members(ds, task, obj):
    return [(f"{L}s", ("ATT", ds, task, obj, "ms", L), ("ATT", ds, task, obj, "lt", L), "mean_score -> learned_temporal") for L in SECONDS]


def reproduce_old(att3401, path, BI, notes):
    """Seed 3401: the old AT-INTEGRATOR families recomputed from the new scores under their original labels (same bootstrap draws),
    compared field by field with results/auditory_alignment_v3/d_lag/d_lag.json (ADDENDUM_12)."""
    if not path or not os.path.exists(path):
        return {"available": False, "members_compared": 0, "reference": path}
    ref = json.load(open(path))
    old = ref["attention"]["families"]; oldsec = ref["attention"].get("secondary", {})
    out, rows, rows_sec = {}, [], []
    for ds in DATASETS:
        for task, obj in TASKS:
            label = f"AT-INTEGRATOR|{ds}|{task}|{obj}"
            members = _att_members(ds, task, obj)
            if label not in old or not all(m[1] in att3401 and m[2] in att3401 for m in members):
                continue
            new = BI.run_family(label, members, att3401, "acc", notes, True)
            nsec = BI.run_family(f"{label}|sec", members, att3401, "acc_native", notes, False)
            fam = {}
            for name, m in new["members"].items():
                o = old[label]["members"].get(name)
                if o is None:
                    continue
                c = _cmp_member(m, o); rows.append(c)
                os_ = oldsec.get(label, {}).get("acc_native", {}).get("members", {}).get(name)
                cs = _cmp_member(nsec["members"].get(name, {}), os_, ("est", "se", "ci_low", "ci_high")) if os_ else None
                if cs:
                    rows_sec.append(cs)
                fam[name] = {"primary": c, "native": cs}
            out[label] = fam
    return {"available": True, "reference": os.path.relpath(path, REPO), "reference_sha256": sha256_file(path), "families": out,
            **_summarise_cmp(rows), "native": _summarise_cmp(rows_sec)}


def reconcile_panel(att_by_seed, path, BI, notes):
    """Seeds 3401 / 3407 / 3413 and the seed mean of the panel AT-INTEGRATOR families recomputed from the new scores with
    d_multiseed's own construction (labels unchanged; seed mean = per identity the mean over the seeds with the pair of the
    within-seed paired difference, reference 0) and compared with results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json."""
    if not path or not os.path.exists(path):
        return {"available": False, "members_compared": 0, "reference": path}
    ref = json.load(open(path))
    out, rows, rows_sec = {"per_seed": {}, "seed_mean": {}}, [], []
    labels = sorted({l for s in ref.get("per_seed", {}).values() for l in s.get("families", {}) if l.startswith("AT-INTEGRATOR|")})
    for label in labels:
        _, ds, task, obj = label.split("|")
        members = _att_members(ds, task, obj)
        for s in SEEDS:
            blk = ref["per_seed"].get(str(s), {})
            if label not in blk.get("families", {}) or s not in att_by_seed:
                continue
            new = BI.run_family(label, members, att_by_seed[s], "acc", notes, True)
            nsec = BI.run_family(f"{label}|sec", members, att_by_seed[s], "acc_native", notes, False)
            fam = {}
            for name, m in new["members"].items():
                o = blk["families"][label]["members"].get(name)
                if o is None:
                    continue
                c = _cmp_member(m, o); rows.append(c)
                os_ = blk.get("secondary", {}).get(label, {}).get("acc_native", {}).get("members", {}).get(name)
                cs = _cmp_member(nsec["members"].get(name, {}), os_, ("est", "se", "ci_low", "ci_high")) if os_ else None
                if cs:
                    rows_sec.append(cs)
                fam[name] = {"primary": c, "native": cs}
            out["per_seed"][f"{s}|{label}"] = fam
        sm = ref.get("seed_mean", {}).get("families", {}).get(label)
        if sm is None or not all(s in att_by_seed for s in SEEDS):
            continue
        pv, smm = {}, []
        for name, rc, cc, tag in members:
            R, C = ("SM_REF", label, name), ("SM_CAND", label, name)
            pr, pc = defaultdict(dict), defaultdict(dict)
            for m in ("acc", "acc_native"):
                sgn = -1.0 if (BI.DIRECTION.get(m) or BI.PDIR[m]) == "lower" else 1.0
                per = {s: BI.member_values(att_by_seed[s], rc, cc, m) for s in SEEDS}
                for i in set().union(*[set(p) for p in per.values()]):
                    pr[i][m] = 0.0; pc[i][m] = sgn * float(np.mean([per[s][i] for s in per if i in per[s]]))
            pv[R], pv[C] = dict(pr), dict(pc); smm.append((name, R, C, tag))
        new = BI.run_family(label, smm, pv, "acc", notes, True)
        nsec = BI.run_family(f"{label}|sec", smm, pv, "acc_native", notes, False)
        fam = {}
        for name, m in new["members"].items():
            o = sm["members"].get(name)
            if o is None:
                continue
            c = _cmp_member(m, o); rows.append(c)
            os_ = ref.get("seed_mean", {}).get("secondary", {}).get(label, {}).get("acc_native", {}).get("members", {}).get(name)
            cs = _cmp_member(nsec["members"].get(name, {}), os_, ("est", "se", "ci_low", "ci_high")) if os_ else None
            if cs:
                rows_sec.append(cs)
            fam[name] = {"primary": c, "native": cs}
        out["seed_mean"][label] = fam
    return {"available": True, "reference": os.path.relpath(path, REPO), "reference_sha256": sha256_file(path),
            "reference_generated": ref.get("meta", {}).get("generated"), "reference_doc_version": ref.get("meta", {}).get("doc_version"),
            "families": out, **_summarise_cmp(rows), "native": _summarise_cmp(rows_sec)}


def analyze(scores_dir=SCORES, res_dir=RES, docs_dir=DOCS, out=OUT, rows=None, load=None, old_d_lag=OLD_D_LAG, old_d_multi=OLD_D_MULTI, write_doc=True):
    from auditory_alignment_v3 import bc_interim as BI
    from auditory_alignment_v3.sci_r1 import stats as S
    for m in ("acc", "acc_native", "margin"):
        BI.PDIR.setdefault(m, "higher")   # endpoint directions (= d_lag_interim.NEW_DIR), this process only
    load = load or (lambda e: load_record(e, out))
    units = unit_rows(rows)
    tiers = {"primary": Acc(), "sensitivity": Acc()}
    grp, coverage, per_unit = {}, [], {}
    for row, twin in units:
        eid, s = row["experiment_id"], row["spec"]
        arm, ds, task, obj, seed = arm_of(row), row["dataset"], s["training_task"], s["objective"], row["seed"]
        rec = load(eid)
        cov = {"eid": eid, "arm": arm, "dataset": ds, "task": task, "objective": obj, "seed": seed, "subject_fold": row["subject_fold"],
               "content_fold": row["content_fold"]}
        twin_rec = load(twin) if twin else None
        cov["twin_shared_model"] = bool(twin_rec and twin_rec.get("shared_model_with") == eid)
        sc = load_scores(scores_dir, eid) if rec is not None and rec.get("status") == "complete" else None
        if rec is None or rec.get("status") != "complete":
            cov["status"] = "record_incomplete_or_held"
        elif sc is None:
            cov["status"] = "scores_missing"
        else:
            aw = rec["eval"]["attention_windows"]
            per, fits = evaluate_unit(sc, aw)
            qc = unit_qc(sc, per, aw, legacy_refit(sc, seed))
            cov["status"] = {1: "included", 2: "sensitivity_only"}.get(qc["tier"], "qc_failed")
            if qc["device_mismatch"]:
                cov["device_mismatch"] = True
            per_unit[eid] = {"qc": qc, "antisymmetric_fits": fits, "legacy_integrators": aw.get("integrators"), "arm": arm,
                             "score_meta": {k: sc["meta"].get(k) for k in ("numerics", "device_match", "checkpoint", "dependency_checkpoint", "stats_qc",
                                                                            "stats_reference", "window_counts_match_record", "seconds", "slurm_job", "readout")}}
            if qc["tier"] in (1, 2):
                for pid in per:
                    grp[(ds, pid)] = sc["part_group"].get(pid)
                if qc["tier"] == 1:
                    tiers["primary"].add_unit(arm, ds, task, obj, seed, per, fits)
                tiers["sensitivity"].add_unit(arm, ds, task, obj, seed, per, fits)
        coverage.append(cov)
    notes = []
    results, per_identity = {}, {}
    for tname, acc in tiers.items():
        if tname == "sensitivity" and not any(c["status"] == "sensitivity_only" for c in coverage):
            results[tname] = None
            continue
        vals, seed_cov = contrast_vals(acc)
        fams = run_families(vals, grp, BI, notes)
        lev, lev_vals = {}, {k: _mean_dict(p) for k, p in acc.lev.items()}
        for c, v in sorted(lev_vals.items(), key=lambda kv: str(kv[0])):
            for m in ("acc", "acc_native"):
                y = [v[i][m] - 0.5 for i in sorted(v) if m in v[i]]
                if y:
                    lev.setdefault(BI.ckey(c), {})[m] = _summ_level(S, y, ("AO-LEVEL", BI.ckey(c), m))
        dg = {}
        for key, per in sorted(acc.diag.items(), key=lambda kv: str(kv[0])):
            arm, ds, task, obj, seed, L, kr = key
            r_ = {}
            for k in ("pos_plus", "pos_minus", "ll_lt_paired", "ll_as", "fixed_minus_paired", "identity_rhs", "lt_sym_abs", "lt_antisym_abs"):
                y = [float(np.mean(per[i][k])) for i in sorted(per) if per[i].get(k)]
                if y:
                    r_[k] = {"n": len(y), "mean": float(np.mean(y)), "min": float(np.min(y)), "max": float(np.max(y))}
            dg[f"{arm}|{ds}|{task}|{obj}|{seed}|{L}s|{kr}"] = r_
        ranges = {}
        for label, f in fams["families"].items():
            if f["arm"] != LAG or label.endswith("|mean"):
                continue
            fam, ds, task, obj, seed = label.split("|")
            for name, m in f["members"].items():
                if "est" in m:
                    ranges.setdefault(f"{fam}|{ds}|{task}|{obj}|{name}", {})[seed] = m["est"]
        between = {k: {"per_seed": v, "min": min(v.values()), "max": max(v.values())} for k, v in ranges.items() if len(v) >= 2}
        att = {s: {c: _mean_dict(per) for c, per in p.items()} for s, p in acc.att.items()}
        excl_summary = Counter()
        for (fam, arm, ds, task, obj, seed, L, kr, why), v in acc.excl.items():
            excl_summary[f"{fam}|{arm}|{L}s|{kr}|{why}"] += v
        results[tname] = {"attention_order": fams, "levels": lev, "logloss": logloss_table(acc, S), "diagnostics": dg, "between_seed": between,
                          "seed_mean_coverage": seed_cov,
                          "participant_cell_exclusions": {"|".join(map(str, k)): v for k, v in sorted(acc.excl.items(), key=str)},
                          "participant_cell_exclusions_summary": dict(sorted(excl_summary.items())),
                          "reproduction_d_lag_3401": reproduce_old(att.get(3401, {}), old_d_lag, BI, notes),
                          "reconciliation_d_multiseed": reconcile_panel(att, old_d_multi, BI, notes)}
        per_identity[tname] = {BI.ckey(c): v for c, v in vals.items()}
    fit_diag = defaultdict(lambda: {"n": 0, **{s: 0 for s in FIT_STATUSES}, "coef_sum_5s_nonpositive_ok": 0, "sym_over_antisym_train_max_ok": 0.0,
                                    "n_iter_max_ok": 0})
    for eid, u in per_unit.items():
        if u["qc"]["tier"] not in (1, 2):
            continue
        for k, f in (u["antisymmetric_fits"] or {}).items():
            fd = fit_diag[f"{u['arm']}|{k}"]; fd["n"] += 1; fd[f["status"]] += 1
            if f["status"] == "ok":
                fd["coef_sum_5s_nonpositive_ok"] += int(k.startswith("5s") and f["coef_sum_5s"] <= 0)
                fd["sym_over_antisym_train_max_ok"] = max(fd["sym_over_antisym_train_max_ok"], f["sym_over_antisym_train"])
                fd["n_iter_max_ok"] = max(fd["n_iter_max_ok"], f["n_iter"])
    cnt = Counter(f"{c['arm']}|{c['seed']}|{c['dataset']}|{c['task']}|{c['objective']}|{c['status']}" for c in coverage)
    ref_files = {}
    for p in (old_d_lag, old_d_multi):
        if p and os.path.exists(p):
            ref_files[os.path.relpath(p, REPO)] = {"sha256": sha256_file(p), "mtime": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(os.path.getmtime(p)))}
    meta = {"evaluation_version": EVAL_VERSION, "card": "R34_ATTENTION_ORDER", "note": os.path.relpath(NOTE, REPO),
            "note_sha256": sha256_file(NOTE) if os.path.exists(NOTE) else None, "code_sha256": code_sha256(), "provenance": PROVENANCE,
            "reference_files": ref_files, "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "slurm_job": os.environ.get("SLURM_JOB_ID", "local"),
            "units": len(units), "status_counts": dict(cnt), "qc_tolerances": {"tier1": QC_TOL, "tier2": QC_TOL2},
            "antisymmetric_estimator": AS_LR_KW, "legacy_estimator": LR_KW,
            "qc_failed": {e: u["qc"]["reasons"][:5] for e, u in per_unit.items() if u["qc"]["tier"] == 0},
            "sensitivity_only": {e: u["qc"]["reasons"][:5] for e, u in per_unit.items() if u["qc"]["tier"] == 2},
            "qc_flags": {e: u["qc"]["flags"] for e, u in per_unit.items() if u["qc"]["flags"]},
            "qc_max_errors": {k: max([u["qc"]["max_errors"][k] for u in per_unit.values()] or [0.0]) for k in ("margin", "margin_over_rms_s", "ms_windows", "lt_windows", "coef_rel")},
            "devices": sorted({str((u["score_meta"].get("numerics") or {}).get("device")) for u in per_unit.values()}),
            "integrators": INTEG, "families_declared": [f[0] + ": " + f[3] for f in FAMS],
            "statistics": "identity-level paired differences (unit-level pairing within each contrast); bootstrap-t over identities "
                          f"(B = {S.NB}); simultaneous 95% by max-t within each family; classes I>0 / I<0 / contains 0; no p-values; conditional on the fitted models"}
    result = {"meta": meta, "primary": results["primary"], "sensitivity_tier2": results["sensitivity"], "antisymmetric_fit_diagnostics": dict(fit_diag),
              "coverage": coverage, "notes": notes,
              "per_unit": {e: {"qc": u["qc"], "antisymmetric_fits": u["antisymmetric_fits"], "score_meta": u["score_meta"]} for e, u in per_unit.items()}}
    os.makedirs(res_dir, exist_ok=True)
    _write_json(os.path.join(res_dir, "attention_order.json"), {k: v for k, v in result.items()})
    _write_json(os.path.join(res_dir, "per_identity.json"), {"vals": per_identity, "groups": {f"{k[0]}|{k[1]}": g for k, g in grp.items()}})
    if write_doc:
        os.makedirs(docs_dir, exist_ok=True)
        render(result, os.path.join(docs_dir, "ATTENTION_ORDER_CORRECTION.md"))
    return result


# ================================================================================================ report (EXPERIMENT_UPDATE template)
def _f(x, nd=3):
    return "–" if x is None else f"{x:+.{nd}f}"


def _iv(m, lo, hi):
    return "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"


def repro_sentence(rp, what):
    if not rp or not rp.get("available"):
        return f"{what}: reference file not available; reproduction not established."
    if not rp.get("members_compared"):
        return f"{what}: no member could be compared (0 members); reproduction not established."
    nat = rp.get("native", {})
    return (f"{what} (`{rp['reference']}`, sha256 `{rp['reference_sha256'][:12]}…`): {rp['members_compared']} members compared, "
            f"max |Δ| over est / se / CI / simultaneous {rp['max_abs_diff']:.2e}, class agreement {rp['class_agreement']}, n agreement "
            f"{rp['n_agreement']}; native secondary {nat.get('members_compared', 0)} members, max |Δ| "
            + (f"{nat['max_abs_diff']:.2e}." if nat.get("max_abs_diff") is not None else "–."))


def _family_tables(L, fams):
    for label, f in fams["families"].items():
        if not f["members"]:
            continue
        sec = fams["secondary"][label]["acc_native"]["members"]
        L += [f"**{label.replace('|', ' · ')}** (critical value {f.get('crit', float('nan')):.2f})", "",
              "| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |", "|---|---|---|---|---|---|---|---|"]
        for name, m in f["members"].items():
            s = sec.get(name, {})
            gs = "; ".join(f"{g}: " + (f"{x['est']:+.3f} (n={x['n']})" if "est" in x else f"n={x['n']}") for g, x in sorted(m.get("groups", {}).items()))
            L.append(f"| {name} | {m['n']} | {_f(m.get('est'))} | {_iv(m, 'ci_low', 'ci_high')} | {_iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | "
                     f"{_f(s.get('est'))} {_iv(s, 'ci_low', 'ci_high')} | {gs} |")
        L.append("")


def render(res, path):
    meta, P = res["meta"], res["primary"]
    fams = P["attention_order"]
    count = defaultdict(lambda: defaultdict(int))
    for label, f in fams["families"].items():
        seed = label.split("|")[-1]
        for m in f["members"].values():
            count[(f["family"], f["arm"], seed)][m.get("class", "no interval")] += 1
    st = Counter()
    for c in res["coverage"]:
        st[(c["arm"], c["status"])] += 1
    L = ["# ATTENTION_ORDER_CORRECTION — candidate order in the D_ATTENTION learned integrator (R34_ATTENTION_ORDER)", "",
         f"日期／代码与数据版本：generated {meta['generated']} (Slurm job {meta['slurm_job']}) by `python -m auditory_alignment_v3.aln34.attention_order --analyze`; "
         f"evaluation_version `{meta['evaluation_version']}`; scores on {', '.join(meta['devices']) or '–'}; code sha256 in "
         "`results/auditory_alignment_v3/aln34/attention_order/attention_order.json`.", "",
         f"本轮完成／运行／待依赖：{meta['units']} D_ATTENTION trained-model rows (all arms); unit status "
         + "; ".join(f"{a} {s} {n}" for (a, s), n in sorted(st.items())) + f". QC tier-1 failures {len(meta['qc_failed'])}, tier-2-only (sensitivity) "
         f"{len(meta['sensitivity_only'])}; max reproduction errors {meta['qc_max_errors']}. Held policy executions stay held and are not filled.", "",
         f"已见信息与本轮新增信息：analysis note `{meta['note']}` (sha256 `{(meta['note_sha256'] or '')[:16]}…`; v2 design in its §11, written before any "
         f"value here was computed). {meta['provenance']} Old rows (D_ATTENTION_RESULTS.md, d_lag.json, D_MULTI_SEED outputs, unit records) are "
         "unchanged; this is a versioned correction.", "",
         "## 1. 当前观察", "",
         "Paired-order evaluation: every test window is presented as (attended, ignored) with label 1 and as (ignored, attended) with label 0, "
         "both on the test side; credit per physical window = mean of the two presentations (tie 0.5). `antisymmetric_learned` = 0.5[h(d) − h(−d)] "
         "with h the legacy logistic model on the five summaries of d / σ (σ = training-window RMS of d), refitted on the training participants' "
         "windows in both orders (tol 1e-10); only fits with status `ok` are scored. Within each contrast the reference and the candidate are averaged "
         "over the same units. Positive Δ = learned integrator more accurate than mean_score. Unified readout primary; native secondary (pointwise). "
         "Identity-level bootstrap-t, simultaneous = max-t within the family. Arms are never pooled; the policy arms have seed 3401 only.", "",
         "### 1.0 Coverage (trained models per arm × seed × dataset × task/objective; complete = 10 = 5 subject folds × 2 content folds)", "",
         "| arm | seed | dataset | task / objective | included | sensitivity only | QC failed | scores missing | held / incomplete |",
         "|---|---|---|---|---|---|---|---|---|"]
    cov = defaultdict(Counter)
    for c in res["coverage"]:
        cov[(ARMS.index(c["arm"]), c["arm"], c["seed"], c["dataset"], f"{c['task']} {c['objective']}")][c["status"]] += 1
    for k, c in sorted(cov.items()):
        L.append(f"| {k[1]} | {k[2]} | {k[3]} | {k[4]} | {c['included']} | {c['sensitivity_only']} | {c['qc_failed']} | {c['scores_missing']} | "
                 f"{c['record_incomplete_or_held']} |")
    L += ["", "### 1.1 Class counts (unified, simultaneous intervals; one cell = arm × dataset × task/objective × window)", "",
          "| family | arm | seed | I>0 | contains 0 | I<0 |", "|---|---|---|---|---|---|"]
    for (fam, arm, seed), c in sorted(count.items(), key=str):
        L.append(f"| {fam} | {arm} | {seed} | {c.get('I>0', 0)} | {c.get('contains 0', 0)} | {c.get('I<0', 0)} |")
    L += ["", "Reproduction of the old fixed-order AT-INTEGRATOR from the new scores, original labels and bootstrap draws (lag arm; note §11.6):", "",
          "- " + repro_sentence(P["reproduction_d_lag_3401"], "Seed 3401 against ADDENDUM_12"),
          "- " + repro_sentence(P["reconciliation_d_multiseed"], "Seeds 3401 / 3407 / 3413 and the seed mean against R34_D_PANEL"), "",
          "### 1.2 Families (primary inclusion tier)", ""]
    _family_tables(L, fams)
    L += ["### 1.3 Logloss of the two learned integrators (bits; pointwise 95% bootstrap-t; Δ = antisymmetric − legacy, negative = antisymmetric better)", "",
          "| cell | n | legacy paired | antisymmetric | Δ |", "|---|---|---|---|---|"]
    for k, r in P["logloss"].items():
        g = lambda x: "–" if x.get("est") is None else (f"{x['est']:.3f}" + (f" [{x['ci_low']:.3f}, {x['ci_high']:.3f}]" if "ci_low" in x else ""))
        d = r["antisym_minus_legacy"]
        L.append(f"| {k.replace('|', ' ')} | {r['n']} | {g(r['legacy_paired'])} | {g(r['antisymmetric'])} | "
                 + ("–" if d.get("est") is None else f"{d['est']:+.3f}" + (f" [{d['ci_low']:+.3f}, {d['ci_high']:+.3f}]" if "ci_low" in d else "")) + " |")
    L += ["", "### 1.4 Diagnostics of the legacy integrator (identity means over test windows)", "",
          "pos+ / pos− = share of test windows whose legacy decision is set by the swap-invariant part s of its logit (strictly s > |a| / s < −|a|), "
          "i.e. by candidate position, not by d. Exact identity: fixed − paired = ½(pos+ − pos−).", "",
          "| cell | readout | pos+ | pos− | fixed−paired | ½(pos+−pos−) |", "|---|---|---|---|---|---|"]
    g = lambda r, k: f"{r[k]['mean']:.3f}" if k in r else "–"
    for k, r in P["diagnostics"].items():
        arm, ds, task, obj, seed, w, kr = k.split("|")
        L.append(f"| {arm} {ds} {task} {obj} {seed} {w} | {kr} | {g(r, 'pos_plus')} | {g(r, 'pos_minus')} | {g(r, 'fixed_minus_paired')} | {g(r, 'identity_rhs')} |")
    fd = res["antisymmetric_fit_diagnostics"]
    L += ["", "Antisymmetric fits per arm × window × readout over included units (status counts; among `ok` fits: 5 s weight sum ≤ 0, max |sym|/|antisym| "
          "of the paired-trained h on training windows, max lbfgs iterations): " + "; ".join(
              f"{k}: n={v['n']}, " + ", ".join(f"{s} {v[s]}" for s in FIT_STATUSES if v[s]) + f", w-sum ≤ 0 {v['coef_sum_5s_nonpositive_ok']}, "
              f"sym/antisym {v['sym_over_antisym_train_max_ok']:.1e}, n_iter ≤ {v['n_iter_max_ok']}" for k, v in sorted(fd.items())) + ".", "",
          "Exclusions from a contrast (unit × participant × window × readout cells; status of the candidate's fit or a missing legacy integrator; "
          "both sides of the contrast drop the cell): " + (json.dumps(P["participant_cell_exclusions_summary"]) if P["participant_cell_exclusions_summary"] else "none")
          + ". Full list in the JSON.", "",
          "### 1.5 Between-seed range (lag panel cells; per-seed estimates)", "", "| family · cell · window | per seed | min | max |", "|---|---|---|---|"]
    for k, v in sorted(P["between_seed"].items()):
        L.append(f"| {k.replace('|', ' · ')} | " + ", ".join(f"{s}: {e:+.3f}" for s, e in sorted(v["per_seed"].items())) + f" | {v['min']:+.3f} | {v['max']:+.3f} |")
    L += ["", f"Seed-mean coverage (identities present in all three seeds): {P['seed_mean_coverage']}", ""]
    if res.get("sensitivity_tier2"):
        L += ["### 1.6 Sensitivity: units included under the tier-2 (device-robust) QC (never part of the primary tables)", ""]
        _family_tables(L, res["sensitivity_tier2"]["attention_order"])
    L += ["## 2. 当前工作判断", "",
          "- Mechanical summary only (fixed rules of the analysis note §6 and §11): the class counts above per family type, arm and seed, favourable and "
          "unfavourable alike; no generalisation beyond this recipe (5 fixed summaries, linear logistic, C = 1, these models). mean_score results "
          "(AT-LEVEL / AT-LENGTH / AT-TASK) are unaffected by the order correction.",
          "- 5 s windows contain one segment: the learned integrators are thresholds there, and the antisymmetric one equals mean_score whenever its "
          "coefficient sum is positive (count of exceptions in §1.4); 5 s cells are a check, not evidence about temporal integration.", "",
          "## 3. 仍竞争的解释", "",
          "- Candidate position: the swap-invariant part of the legacy logit (intercept, sd, range terms) decides the pos± share of test windows (§1.4). "
          "For native CS the saved intercepts equal logit(label-1 share) of the shared flip stream (note §11.11).",
          "- A weak or wrongly weighted swap-antisymmetric part of the summaries: visible in AO-ANTISYM after the position term is removed.",
          "- If AO-PAIRED-LEGACY native cells stay below chance, the old native anomaly is not explained by candidate order alone.", "",
          "## 4. 下一轮干预", "",
          "- Package docs/04 §B alternatives, not run here and without a performance gate: h reweighting d by swap-invariant quantities such as |d|; "
          "same-window method comparisons at 5/10/20 s.", "",
          "## 5. 复用与运行", "",
          f"- Reused: the unit records and saved checkpoints (no retraining, no backbone refit). New: per-unit score extraction (stage 1, device-matched) "
          f"and this CPU analysis. Notes: {len(res['notes'])} (see JSON).", "",
          "## 6. 暂不决定", "",
          "- Placement of the corrected integrator rows (main text / appendix) is not decided here and does not block further experiments.", ""]
    with open(path + ".tmp", "w") as fh:
        fh.write("\n".join(L))
    os.replace(path + ".tmp", path); os.chmod(path, 0o600)
    return path


# ================================================================================================ CLI
def _select(units, args):
    want = list(args.unit or [])
    if args.unit_list:
        want += read_unit_list(args.unit_list)
    by = {r["experiment_id"]: (r, t) for r, t in units}
    missing = [e for e in want if e not in by]
    if missing:
        raise SystemExit(f"unknown D_ATTENTION mean_score unit ids: {missing[:5]}")
    sel = [by[e] for e in dict.fromkeys(want)]
    if getattr(args, "arm", None):
        sel = [u for u in sel if arm_of(u[0]) == args.arm]
    if args.dataset:
        sel = [u for u in sel if u[0]["dataset"] == args.dataset]
    if args.content_fold is not None:
        sel = [u for u in sel if u[0]["content_fold"] == args.content_fold]
    sel.sort(key=lambda u: (u[0]["dataset"], u[0]["content_fold"], ARMS.index(arm_of(u[0])), u[0]["seed"], u[0]["spec"]["training_task"],
                            u[0]["spec"]["objective"], u[0]["subject_fold"]))
    if args.shard:
        i, n = map(int, args.shard.split("/"))
        sel = [u for k, u in enumerate(sel) if k % n == i]
    return sel


def main(argv=None):
    os.umask(0o077)
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--unit", action="append"); a.add_argument("--unit-list"); a.add_argument("--arm", choices=ARMS); a.add_argument("--dataset", choices=DATASETS)
    a.add_argument("--content-fold", type=int); a.add_argument("--shard"); a.add_argument("--device", default="auto")
    a.add_argument("--allow-device-mismatch", action="store_true", help="extract units recorded on another GPU model (marked device_mismatch)")
    a.add_argument("--scores", default=SCORES); a.add_argument("--analyze", action="store_true"); a.add_argument("--no-doc", action="store_true")
    a.add_argument("--write-unit-list", nargs="?", const=UNIT_LIST); a.add_argument("--check-ckpt", action="store_true")
    args = a.parse_args(argv)
    if args.write_unit_list:
        p, n, plan = write_unit_list(args.write_unit_list); print("unit list", p, n, json.dumps(plan, default=str)); return
    if args.check_ckpt:
        res = check_checkpoints()
        bad = [r for r in res if not (r["exists"] and r["sha256_matches_manifest"])]
        print(json.dumps({"n": len(res), "by_kind": Counter(r["kind"] for r in res), "exists": sum(r["exists"] for r in res),
                          "sha256_matches_manifest": sum(r["sha256_matches_manifest"] for r in res), "on_A3c": sum(r["on_A3c"] for r in res),
                          "bad": bad[:10]}, indent=1, default=str)); return
    if args.analyze:
        r = analyze(scores_dir=args.scores, write_doc=not args.no_doc)
        print("analysis written", r["meta"]["status_counts"]); return
    import torch
    dev = torch.device(("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device)
    rows = _all_rows()
    sel = _select(unit_rows(rows), args)
    if not sel:
        raise SystemExit("no units selected (use --unit / --unit-list)")
    env = numerics_env(dev)
    print("stage 1 on", json.dumps(env), "units selected", len(sel), flush=True)
    cache, man, failed, skipped = CohortCache(dev), manifest_index(), [], []
    for row, twin in sel:
        try:
            extract_unit(row, twin, cache, dev, scores_dir=args.scores, man=man, rows=rows, allow_device_mismatch=args.allow_device_mismatch)
        except DeviceMismatch as ex:
            skipped.append(row["experiment_id"]); print("skip (device)", ex, flush=True)
        except Exception as ex:  # noqa: BLE001 (a technical failure is reported, never written as a result)
            failed.append(row["experiment_id"]); print("FAILED", row["experiment_id"], f"{type(ex).__name__}: {ex}", flush=True)
    cache.release()
    print("done", len(sel) - len(failed) - len(skipped), "of", len(sel), "skipped for device", len(skipped), "failed", failed, flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
