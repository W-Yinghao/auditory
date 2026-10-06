"""Aggregation over all fit units (spec 10-12, 16.1).

Resampling unit = participant (spec 12): per participant, a configuration's metrics are averaged over its units
(seeds x content folds); intervals are participant bootstraps that condition on the fitted models. Training variance
(seed / content fold) is reported separately as unit-level spread and the count of units with a positive mean.

Per-participant derived quantities (continuous speech, readout r in {native, unified}):
  r/gain_bits      = logloss(mismatched EEG) - logloss(true EEG), bits per 5 s query (same candidates, same calibration)
  r/rank_gain      = rank_pct(mismatched EEG) - rank_pct(true EEG)
  r/hard_gain_bits = log2(1 + K) - logloss(hard pool of K = 8 nearest real candidates)
  kernel_cs_diff   = test CS-QMI(true pairing) - CS-QMI(legal mismatch), nats, at the unit's training bandwidths
Private: head_gain_vs_base_bits, hist_gain_bits, hist_gain_twin_bits, hist_minus_twin_bits (+ common-support versions).

Usage: python -m auditory_alignment.aggregate
Outputs (counts / group summaries only): results/auditory_alignment_kernel_cs/{RUN_MANIFEST_summary.json, full_results.json,
contrasts.json, development_function.json}; per-participant tables stay in private/auditory_alignment_kernel_cs/.
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter, defaultdict

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(REPO, "results", "auditory_alignment_kernel_cs")
PRIV = os.path.join(REPO, "private", "auditory_alignment_kernel_cs")
MANIFEST = os.path.join(REPO, "AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_v1_20261005", "planned_jobs.jsonl")
HASHES = os.path.join(PRIV, "fleet_code_hashes.json")
EXT_MANIFEST = os.path.join(PRIV, "planned_jobs_ext.jsonl")
VARIANT_KEYS = ("projection_dim", "kernel_rows", "temperature", "fmca_relative_ridge", "bandwidth_multiplier", "audio_projection",
                "training_task", "pairing", "train_population")
DEFAULTS = {"projection_dim": 16, "kernel_rows": 256, "temperature": 0.1, "fmca_relative_ridge": 0.001, "bandwidth_multiplier": 1.0,
            "audio_projection": "trainable", "train_population": None}
CORE_POP = {"fau": "TH_HA_CI", "dtu": "NH_HI", "federici": "HC_CI_available_vocoder_conditions", "private_bdf": "HA_NH"}
REF_GROUP = {"fau": "th", "dtu": "nh", "federici": "HC", "private_bdf": "NH"}
OBJ = ("NCE", "FMCA", "CS_SINGLE", "CS_MULTI")
NB = 4000
K_HARD = 8


# ------------------------------------------------------------------------------------------------ statistics
def _clean(x):
    return np.asarray([v for v in x if v is not None and np.isfinite(v)], float)


def boot(x, seed=0):
    x = _clean(x)
    if len(x) == 0:
        return {"est": None, "n": 0}
    r = np.random.default_rng(seed); b = x[r.integers(0, len(x), (NB, len(x)))].mean(1)
    return {"est": float(x.mean()), "ci_low": float(np.percentile(b, 2.5)), "ci_high": float(np.percentile(b, 97.5)), "n": int(len(x))}


def diff_boot(a, b, seed=0):
    a, b = _clean(a), _clean(b)
    if len(a) == 0 or len(b) == 0:
        return {"est": None, "n_a": len(a), "n_b": len(b)}
    r = np.random.default_rng(seed)
    bs = a[r.integers(0, len(a), (NB, len(a)))].mean(1) - b[r.integers(0, len(b), (NB, len(b)))].mean(1)
    return {"est": float(a.mean() - b.mean()), "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5)),
            "n_a": int(len(a)), "n_b": int(len(b))}


def ols_boot(X, y, names, seed=0):
    """OLS with intercept; percentile bootstrap over rows (participants)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    ok = np.isfinite(y) & np.isfinite(X).all(1)
    X, y = X[ok], y[ok]
    if len(y) < X.shape[1] + 3:
        return {"n": int(len(y))}
    A = np.c_[np.ones(len(y)), X]
    beta = np.linalg.lstsq(A, y, rcond=None)[0]
    r = np.random.default_rng(seed); bs = []
    for _ in range(2000):
        i = r.integers(0, len(y), len(y))
        if np.linalg.matrix_rank(A[i]) == A.shape[1]:
            bs.append(np.linalg.lstsq(A[i], y[i], rcond=None)[0])
    bs = np.array(bs)
    return {"n": int(len(y)), "coef": {n: {"est": float(beta[k + 1]), "ci_low": float(np.percentile(bs[:, k + 1], 2.5)),
                                          "ci_high": float(np.percentile(bs[:, k + 1], 97.5))} for k, n in enumerate(names)}}


def loo_risk(X, y):
    n = len(y); e = np.empty(n)
    for i in range(n):
        tr = np.arange(n) != i
        if X.shape[1]:
            mu, sd = X[tr].mean(0), X[tr].std(0); sd[sd == 0] = 1; Z = (X - mu) / sd
        else:
            Z = X
        A = np.c_[np.ones(n), Z]; b = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
        e[i] = (y[i] - A[i] @ b) ** 2
    return e


def nested_models(y, blocks, seed=0):
    """C -> C + overall -> C + overall + structure: LOO-OLS risks and paired bootstrap of risk differences (big - small;
    negative = the added block improves held-out prediction)."""
    y = np.asarray(y, float); mats = [np.asarray(b, float).reshape(len(y), -1) for b in blocks]
    ok = np.isfinite(y)
    for m in mats:
        ok &= np.isfinite(m).all(1)
    y = y[ok]; mats = [m[ok] for m in mats]
    if len(y) < 8:
        return {"n": int(len(y))}
    E = [loo_risk(np.hstack(mats[:k + 1]), y) for k in range(len(mats))]
    out = {"n": int(len(y)), "risk": [float(e.mean()) for e in E]}
    r = np.random.default_rng(seed)
    for k in range(1, len(E)):
        d = E[k] - E[k - 1]; bs = d[r.integers(0, len(d), (NB, len(d)))].mean(1)
        out[f"step{k}_minus_step{k - 1}"] = {"est": float(d.mean()), "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5))}
    return out


# ------------------------------------------------------------------------------------------------ units -> participants
def variant(job):
    c = job["config"]
    parts = [f"{k}={c[k]}" for k in VARIANT_KEYS if k in c and c[k] is not None and c[k] != DEFAULTS.get(k)
             and not (k == "train_population" and c[k] == CORE_POP[job["dataset"]])
             and not (k == "audio_projection" and str(c[k]).startswith("not_applicable"))]  # private: no audio projection
    if job["train_population"] != CORE_POP[job["dataset"]]:
        parts.append(f"train_population={job['train_population']}")
    return ";".join(sorted(set(parts))) or "default"


def cfg_key(job):
    return "|".join(map(str, (job["block"], job["dataset"], job["objective"], job["target"], job["window"], variant(job))))


def unit_rows(rec):
    ev = rec["eval"]; out = {}
    for pid, r in ev["per_participant"].items():
        row = {"group": r["group"]}
        for k, v in r.items():
            if isinstance(v, dict):
                for m, x in v.items():
                    if isinstance(x, (int, float)) and not isinstance(x, bool) and m not in ("n_candidates", "n_queries", "n_rows", "draws"):
                        row[f"{k}/{m}"] = float(x)
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and v is not None and k not in ("n", "n_segments"):
                row[k] = float(v)
        for rd in ("native", "unified"):
            if f"{rd}/regular/logloss_bits" in row:
                row[f"{rd}/gain_bits"] = row[f"{rd}/mismatched_eeg/logloss_bits"] - row[f"{rd}/regular/logloss_bits"]
                row[f"{rd}/rank_gain"] = row[f"{rd}/mismatched_eeg/rank_pct"] - row[f"{rd}/regular/rank_pct"]
                row[f"{rd}/hard_gain_bits"] = float(np.log2(1 + K_HARD)) - row[f"{rd}/hard/logloss_bits"]
        if "kernel_dependence/cs_true_minus_mismatched" in row:
            row["kernel_cs_diff"] = row["kernel_dependence/cs_true_minus_mismatched"]
        if "hist_gain_bits" in row:
            row["hist_minus_twin_bits"] = row["hist_gain_bits"] - row["hist_gain_twin_bits"]
            if "hist_gain_common_support" in row and "hist_gain_twin_common_support" in row:
                row["hist_minus_twin_common_support"] = row["hist_gain_common_support"] - row["hist_gain_twin_common_support"]
        out[pid] = row
    for pid, r in ev.get("attention_2afc", {}).items():
        for rd, v in r.items():
            out.setdefault(pid, {"group": ev["per_participant"].get(pid, {}).get("group")})
            out[pid][f"attention/{rd}/accuracy"] = v["accuracy"]; out[pid][f"attention/{rd}/margin"] = v["mean_margin"]
    return out


KEY_METRICS = ("native/gain_bits", "unified/gain_bits", "native/rank_gain", "unified/rank_gain", "native/regular/top1", "unified/regular/top1",
               "native/regular/top5", "unified/regular/top5", "native/regular/mrr", "unified/regular/mrr", "native/regular/rank_pct",
               "unified/regular/rank_pct", "native/regular/logloss_bits", "unified/regular/logloss_bits", "native/mismatched_eeg/top1",
               "unified/mismatched_eeg/top1", "native/hard/top1", "unified/hard/top1", "native/hard_gain_bits", "unified/hard_gain_bits",
               "kernel_cs_diff", "kernel_dependence/cs_true_nats", "kernel_dependence/cs_mismatched_nats",
               "attention/native/accuracy", "attention/unified/accuracy", "attention/native/margin", "attention/unified/margin",
               "head_auc", "head_brier", "head_logloss_bits", "head_gain_vs_base_bits", "hist_gain_bits", "hist_gain_twin_bits",
               "hist_minus_twin_bits", "hist_gain_common_support", "hist_minus_twin_common_support", "qW_auc", "q0_auc", "qW_brier",
               "q0_brier", "common_support_fraction")
HALVES = {"native/regular_half": "native/regular/rank_pct", "unified/regular_half": "unified/regular/rank_pct",
          "head_gain_vs_base_half": "head_gain_vs_base_bits", "hist_gain_half": "hist_gain_bits"}


def load_units(hashes):
    plan = [json.loads(l) for l in open(MANIFEST)]
    if os.path.exists(EXT_MANIFEST):
        plan += [json.loads(l) for l in open(EXT_MANIFEST)]
    units, bad = {}, Counter()
    for p in glob.glob(os.path.join(PRIV, "units", "*.json")) + glob.glob(os.path.join(PRIV, "units_linear", "*.json")):
        if p.endswith(".FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") != "complete":
            continue
        ds = r["job"]["dataset"]
        if r["job"]["block"].startswith("ext_"):  # registered extensions: run_ext on top of code C
            valid = r.get("code_hash") == hashes.get("D")
        elif ds == "private_bdf":  # B->C changed evaluate_private: evaluation must come from C (direct or evaluation-only rerun)
            valid = r.get("code_hash") == hashes["C"] or r.get("reeval_code_hash") == hashes["C"]
        elif ds == "federici":  # A->B changed the Federici split
            valid = r.get("code_hash") in (hashes["B"], hashes["C"])
        else:
            valid = r.get("code_hash") in (hashes["A"], hashes["B"], hashes["C"])
        if not valid:
            bad[ds] += 1; continue
        units[r["job"]["experiment_id"]] = r
    return plan, units, dict(bad)


def participant_table(units):
    """cfg -> pid -> metric -> [unit values]; plus cfg -> unit-level means; groups and covariates per (dataset, pid)."""
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    U = defaultdict(lambda: defaultdict(list))
    info, meta = {}, defaultdict(lambda: {"best_epoch": [], "seconds": [], "units": 0, "steps": [], "resumed": 0, "curves": defaultdict(lambda: defaultdict(list))})
    for r in units.values():
        j = r["job"]; k = cfg_key(j); rows = unit_rows(r)
        m = meta[k]; m["units"] += 1; m["best_epoch"].append(r.get("best_epoch")); m["seconds"].append(r.get("total_seconds"))
        m["steps"].append(r.get("optimizer_steps")); m["resumed"] += int("resumed_from_epoch" in r)
        for c in r.get("curve", []):
            cv = m["curves"][c["epoch"]]
            for ck in ("selection_score", "train_loss", "es_loss", "es_loss_mismatched"):
                if c.get(ck) is not None:
                    cv[ck].append(c[ck])
            if c.get("es_cs_true_nats") is not None:
                cv["es_cs_true_minus_mismatched"].append(c["es_cs_true_nats"] - c["es_cs_mismatched_nats"])
        acc = defaultdict(list)
        for pid, row in rows.items():
            info[(j["dataset"], pid)] = {"group": row.get("group"), "age_months": row.get("age_months"), "duration_months": row.get("duration_months")}
            for mm, v in row.items():
                if mm in ("group", "age_months", "duration_months"):
                    continue
                T[k][pid][mm].append(v); acc[mm].append(v)
        for mm, vs in acc.items():
            U[k][mm].append(float(np.nanmean(vs)))
    P = {k: {pid: {mm: float(np.nanmean(v)) for mm, v in ms.items()} for pid, ms in pids.items()} for k, pids in T.items()}
    return P, U, info, meta


# ------------------------------------------------------------------------------------------------ main
def main():
    hashes = json.load(open(HASHES))
    plan, units, bad = load_units(hashes)
    planned_by_cfg = Counter(cfg_key(j) for j in plan)
    for ds, n_cf, tw in (("fau", 2, (("Ac", "full"), ("Lz", "full"), ("local", "full"), ("local", "early"), ("local", "late"), ("local", "joint"))),
                         ("dtu", 2, (("Ac", "full"), ("Lz", "full"), ("local", "full"), ("local", "early"), ("local", "late"), ("local", "joint"))),
                         ("federici", 1, tuple(("envelope", w) for w in ("full", "early", "late", "joint"))),
                         ("private_bdf", 1, tuple(("current_class", w) for w in ("full", "early", "late", "joint")))):
        for t, w in tw:  # extension E9 (linear reference): 5 subject folds x content folds, no seeds
            planned_by_cfg[f"linear_reference|{ds}|LINEAR|{t}|{w}|default"] = 5 * n_cf
    status = Counter(); by_block = defaultdict(Counter)
    manifest = []
    for j in plan:
        r = units.get(j["experiment_id"])
        st = "complete" if r else ("failed" if os.path.exists(os.path.join(PRIV, "units", f"{j['experiment_id']}.FAILED.json")) else "not_complete")
        status[st] += 1; by_block[f"{j['block']}|{j['dataset']}"][st] += 1
        manifest.append({"experiment_id": j["experiment_id"], "block": j["block"], "dataset": j["dataset"], "objective": j["objective"],
                         "target": j["target"], "window": j["window"], "variant": variant(j), "subject_fold": j["subject_fold"],
                         "content_fold": j["content_fold"], "seed": j["seed"], "status": st,
                         **({k: r.get(k) for k in ("code_hash", "config_hash", "device", "epochs_completed", "optimizer_steps", "best_epoch",
                                                   "total_seconds", "resumed_from_epoch", "gpu_peak_allocated_mb")} if r else {})})
    with open(os.path.join(PRIV, "RUN_MANIFEST.jsonl"), "w") as f:
        for m in manifest:
            f.write(json.dumps(m) + "\n")
    os.makedirs(RES, exist_ok=True)
    json.dump({"n_planned": len(plan), "status": dict(status), "by_block_dataset": {k: dict(v) for k, v in sorted(by_block.items())},
               "rejected_units_by_code_hash": bad, "code_hashes": hashes}, open(os.path.join(RES, "RUN_MANIFEST_summary.json"), "w"), indent=1)

    P, U, info, meta = participant_table(units)
    grp = lambda ds, pid: info[(ds, pid)]["group"]

    # ---- cells
    full = {}
    for k, pp in P.items():
        ds = k.split("|")[1]
        gnames = sorted({grp(ds, p) for p in pp}) + ["all"]
        m = meta[k]
        be = [b for b in m["best_epoch"] if b]; secs = [x for x in m["seconds"] if x]
        cell = {"n_units": m["units"], "n_units_planned": planned_by_cfg[k], "best_epoch_median": float(np.median(be)) if be else None,
                "best_epoch_iqr": [float(np.percentile(be, q)) for q in (25, 75)] if be else None,
                "seconds_median": float(np.median(secs)) if secs else None, "units_resumed": m["resumed"], "groups": {}}
        for g in gnames:
            ids = [p for p in pp if g == "all" or grp(ds, p) == g]
            cell["groups"][g] = {mm: boot([pp[i].get(mm) for i in ids]) for mm in KEY_METRICS if any(mm in pp[i] for i in ids)}
        cell["unit_level"] = {mm: {"n": len(v), "mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None,
                                   "n_positive": int(sum(x > 0 for x in v))} for mm, v in U[k].items() if mm in KEY_METRICS}
        rel = {}
        for hk, base in HALVES.items():
            if hk.endswith("_half"):
                a = [pp[i].get(f"{hk}0/rank_pct" if "regular" in hk else f"{hk}0") for i in pp]
                b = [pp[i].get(f"{hk}1/rank_pct" if "regular" in hk else f"{hk}1") for i in pp]
                ab = [(x, y) for x, y in zip(a, b) if x is not None and y is not None and np.isfinite(x) and np.isfinite(y)]
                if len(ab) >= 8:
                    x, y = np.array(ab).T
                    rr = np.random.default_rng(1); bs = []
                    for _ in range(2000):
                        i = rr.integers(0, len(x), len(x))
                        if np.std(x[i]) > 0 and np.std(y[i]) > 0:
                            bs.append(np.corrcoef(x[i], y[i])[0, 1])
                    rel[base] = {"split_half_r": float(np.corrcoef(x, y)[0, 1]), "ci_low": float(np.percentile(bs, 2.5)),
                                 "ci_high": float(np.percentile(bs, 97.5)), "n": int(len(x))}
        cell["split_half_reliability"] = rel
        cell["curve_median"] = {str(ep): {ck: [float(np.percentile(v, q)) for q in (25, 50, 75)] for ck, v in cv.items()} for ep, cv in sorted(m["curves"].items())}
        full[k] = cell
    # post-hoc R1: split-half reliability of the EEG-specific gain (per-half true-vs-mismatched log-loss difference)
    r1 = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for p in glob.glob(os.path.join(PRIV, "r1_reliability", "*.json")):
        d = json.load(open(p)); k = cfg_key(d["job"])
        for pid, row in d["per_participant"].items():
            for mm, v in row.items():
                if mm != "group":
                    r1[k][pid][mm].append(v)
    for k, pp in r1.items():
        if k not in full:
            continue
        rel = {}
        for rd in ("unified", "native"):
            ab = [(np.mean(m[f"{rd}/gain_half0"]), np.mean(m[f"{rd}/gain_half1"])) for m in pp.values() if m.get(f"{rd}/gain_half0") and m.get(f"{rd}/gain_half1")]
            if len(ab) >= 8:
                x, y = np.array(ab).T
                rr = np.random.default_rng(2); bs = []
                for _ in range(2000):
                    i = rr.integers(0, len(x), len(x))
                    if np.std(x[i]) > 0 and np.std(y[i]) > 0:
                        bs.append(np.corrcoef(x[i], y[i])[0, 1])
                r = float(np.corrcoef(x, y)[0, 1])
                rel[f"{rd}/gain_bits"] = {"split_half_r": r, "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5)),
                                          "spearman_brown": float(2 * r / (1 + r)) if r > -1 else None, "n": int(len(x))}
        full[k]["split_half_reliability_gain_R1"] = rel
    json.dump(full, open(os.path.join(RES, "full_results.json"), "w"), indent=1)
    json.dump({"participant_means": P, "groups": {f"{d}|{p}": v for (d, p), v in info.items()}},
              open(os.path.join(PRIV, "participant_means.json"), "w"))

    # ---- contrasts
    C = {"methods": {}, "groups": {}, "temporal": {}, "exclude_CI_training": {}, "wrong_pair": {}, "attention": {}, "equal_width": {},
         "optimization": {}, "vs_linear_reference": {}, "ext_combo": {}, "ext_class_balanced": {}}
    PRIMARY = {"private_bdf": ("head_gain_vs_base_bits", "hist_minus_twin_bits", "head_auc", "kernel_cs_diff")}
    CONT = ("native/gain_bits", "unified/gain_bits", "native/rank_gain", "unified/rank_gain", "unified/hard_gain_bits", "native/hard_gain_bits", "kernel_cs_diff")

    def metrics_for(ds):
        return PRIMARY.get(ds, CONT)

    def paired(ka, kb, ds, groups=True, metrics=None):
        A, B = P.get(ka), P.get(kb)
        if not A or not B:
            return None
        ids = sorted(set(A) & set(B)); out = {}
        for mm in (metrics or metrics_for(ds)):
            gs = sorted({grp(ds, i) for i in ids}) + ["all"] if groups else ["all"]
            out[mm] = {g: boot([A[i].get(mm, np.nan) - B[i].get(mm, np.nan) for i in ids if g == "all" or grp(ds, i) == g]) for g in gs}
        return out

    def temporal(k, ke, kl, ds):
        """Delta_{L|E} = R(early) - R(joint), Delta_{E|L} = R(late) - R(joint), R = query log loss (bits)."""
        if not (k in P and ke in P and kl in P):
            return
        risks = ("native/regular/logloss_bits", "unified/regular/logloss_bits") if ds != "private_bdf" else ("head_logloss_bits",)
        t = {}
        for rk in risks:
            ids = sorted(set(P[k]) & set(P[ke]) & set(P[kl]))
            gs = sorted({grp(ds, i) for i in ids}) + ["all"]
            t[rk] = {"Delta_L_given_E": {g: boot([P[ke][i][rk] - P[k][i][rk] for i in ids if g == "all" or grp(ds, i) == g]) for g in gs},
                     "Delta_E_given_L": {g: boot([P[kl][i][rk] - P[k][i][rk] for i in ids if g == "all" or grp(ds, i) == g]) for g in gs}}
            ref_ids = [i for i in ids if grp(ds, i) == REF_GROUP[ds]]
            for g in sorted({grp(ds, i) for i in ids} - {REF_GROUP[ds]}):
                gi = [i for i in ids if grp(ds, i) == g]
                for dn, kx in (("Delta_L_given_E", ke), ("Delta_E_given_L", kl)):
                    t[rk][f"{dn} {g}-{REF_GROUP[ds]}"] = diff_boot([P[kx][i][rk] - P[k][i][rk] for i in gi], [P[kx][i][rk] - P[k][i][rk] for i in ref_ids])
        C["temporal"][k] = t

    keys = list(P)
    parse = lambda k: dict(zip(("block", "dataset", "objective", "target", "window", "variant"), k.split("|")))
    for k in keys:
        q = parse(k)
        if q["block"] == "core" and q["variant"] == "default":
            ds = q["dataset"]
            # methods: every pair, same dataset / target / window
            for o2 in OBJ:
                if o2 <= q["objective"]:
                    continue
                k2 = "|".join(("core", ds, o2, q["target"], q["window"], "default"))
                if k2 in P:
                    C["methods"][f"{k} MINUS {o2}"] = paired(k, k2, ds)
            kl_ = "|".join(("linear_reference", ds, "LINEAR", q["target"], q["window"], "default"))
            if kl_ in P:
                C["vs_linear_reference"][f"{k} MINUS LINEAR"] = paired(k, kl_, ds)
            # group differences within the cell (vs reference group)
            pp = P[k]; ref = REF_GROUP[ds]
            gres = {}
            for g in sorted({grp(ds, p) for p in pp} - {ref}):
                gres[f"{g}-{ref}"] = {mm: diff_boot([pp[i].get(mm) for i in pp if grp(ds, i) == g], [pp[i].get(mm) for i in pp if grp(ds, i) == ref])
                                      for mm in metrics_for(ds)}
            if ds == "fau":
                gres["ci-ha"] = {mm: diff_boot([pp[i].get(mm) for i in pp if grp(ds, i) == "ci"], [pp[i].get(mm) for i in pp if grp(ds, i) == "ha"]) for mm in metrics_for(ds)}
            C["groups"][k] = gres
            if q["window"] == "joint":
                temporal(k, k.replace("|joint|", "|early|"), k.replace("|joint|", "|late|"), ds)
        if q["block"] in ("ext_target_windows", "ext_class_balanced") and q["window"] == "joint":
            temporal(k, k.replace("|joint|", "|early|"), k.replace("|joint|", "|late|"), q["dataset"])
        if q["block"] == "ext_combo":
            for part in q["objective"].split("+"):
                kc = "|".join(("core", q["dataset"], part, q["target"], q["window"], "default"))
                C["ext_combo"][f"{k} MINUS core_{part}"] = paired(k, kc, q["dataset"])
        if q["block"] == "ext_class_balanced":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], q["window"], "default"))
            C["ext_class_balanced"][f"{k} MINUS core_natural"] = paired(k, kc, q["dataset"])
        if q["block"] == "exclude_CI_training":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], q["window"], "default"))
            C["exclude_CI_training"][f"{k} MINUS core"] = paired(k, kc, q["dataset"])
        if q["block"] == "wrong_pair_training":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], q["window"], "default"))
            C["wrong_pair"][f"core MINUS {k}"] = paired(kc, k, q["dataset"])
        if q["block"] == "attention":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], q["window"], "default"))
            C["attention"][f"{k} MINUS core_zero_shot"] = paired(k, kc, q["dataset"], metrics=("attention/native/accuracy", "attention/unified/accuracy",
                                                                                             "attention/native/margin", "attention/unified/margin"))
        if q["block"] == "equal_width":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], "late", "default"))
            C["equal_width"][f"{k} MINUS core_late"] = paired(k, kc, q["dataset"])
        if q["block"] == "optimization":
            kc = "|".join(("core", q["dataset"], q["objective"], q["target"], q["window"], "default"))
            C["optimization"][f"{k} MINUS core_default"] = paired(k, kc, q["dataset"], groups=False)
    json.dump(C, open(os.path.join(RES, "contrasts.json"), "w"), indent=1)

    # ---- development and function (spec 11.2, 11.3)
    json.dump(development_function(P, info), open(os.path.join(RES, "development_function.json"), "w"), indent=1)
    print("units", len(units), dict(status), "rejected", bad, "cells", len(full))


def federici_participants():
    """Participant ids / groups / age / behavioural accuracy exactly as data.load_federici builds them (no EEG loaded)."""
    from .data import FED_PRE, _fed_ages, _fed_id
    ages = _fed_ages(); out = []
    for grp in ("HC", "CI", "HC-v", "Artifact"):
        for p in sorted(glob.glob(os.path.join(FED_PRE, grp, "*.h5"))):
            fid = os.path.basename(p)[:-3]
            key = fid if grp in ("HC", "HC-v") else ("S" + fid.lstrip("0").rjust(3, "0") if grp == "CI" else None)
            a = ages.get(_fed_id(fid), ages.get(key, {})) if key else {}
            out.append({"id": f"{grp}:{fid}", "group": grp, "age_years": a.get("age_years"), "behav_acc": a.get("behav_acc")})
    return out


def development_function(P, info):
    import pandas as pd
    out = {"private_development": {}, "federici_development": {}, "function": {}}
    # private: alignment ~ age, per window and pooled with age x window; HA: + duration (Age = AgeAtFitting + Duration)
    for o in OBJ:
        rows = []
        for w in ("full", "early", "late", "joint"):
            k = f"core|private_bdf|{o}|current_class|{w}|default"
            for pid, m in P.get(k, {}).items():
                inf = info[("private_bdf", pid)]
                rows.append({"pid": pid, "w": w, "group": inf["group"], "age": inf["age_months"], "dur": inf["duration_months"], **{x: m.get(x) for x in ("head_gain_vs_base_bits", "hist_minus_twin_bits", "head_auc")}})
        if not rows:
            continue
        df = pd.DataFrame(rows); res = {}
        for y in ("head_gain_vs_base_bits", "hist_minus_twin_bits", "head_auc"):
            per_w = {}
            for w, d in df.groupby("w"):
                per_w[w] = {"age_slope_all": ols_boot(np.c_[d.age, (d.group == "HA").astype(float)], d[y], ["age_months", "HA"]),
                            "HA_age_duration": ols_boot(d[d.group == "HA"][["age", "dur"]].to_numpy(float), d[d.group == "HA"][y], ["age_months", "duration_months"])}
            sub = df[df.w.isin(["early", "late"])]
            late = (sub.w == "late").astype(float)
            pooled = ols_boot(np.c_[sub.age, (sub.group == "HA").astype(float), late, sub.age * late, (sub.group == "HA").astype(float) * late], sub[y],
                              ["age_months", "HA", "late", "age_x_late", "HA_x_late"])
            res[y] = {"per_window": per_w, "early_late_template": pooled,
                      "note": "rows are child x window (2 per child); bootstrap resamples rows, so the pooled interval is approximate"}
        out["private_development"][o] = res
    # Federici: alignment ~ age within HC and CI (envelope, full window), and behavioural accuracy (function)
    fed_cov = {}
    try:
        for p in federici_participants():
            fed_cov[p["id"]] = p
    except Exception as ex:  # covariates are optional for the aggregate; reported when missing
        out["federici_development"]["error"] = repr(ex)
    for o in OBJ:
        for w in ("full", "early", "late", "joint"):
            k = f"core|federici|{o}|envelope|{w}|default"
            if k not in P or not fed_cov:
                continue
            ids = [i for i in P[k] if i in fed_cov and fed_cov[i].get("age_years") is not None]
            r = {}
            for y in ("unified/gain_bits", "native/gain_bits"):
                for g in ("HC", "CI", "HC-v"):
                    gi = [i for i in ids if fed_cov[i]["group"] == g]
                    r[f"{y}|{g}|age_slope"] = ols_boot(np.array([[fed_cov[i]["age_years"]] for i in gi]), [P[k][i].get(y) for i in gi], ["age_years"])
                ba = [i for i in ids if fed_cov[i].get("behav_acc") is not None and fed_cov[i]["group"] in ("HC", "CI")]
                if w == "full" and len(ba) >= 8:
                    yv = np.array([fed_cov[i]["behav_acc"] for i in ba], float)
                    Cm = np.array([[fed_cov[i]["age_years"], float(fed_cov[i]["group"] == "CI")] for i in ba], float)
                    ov = np.array([P[k][i].get(y, np.nan) for i in ba])
                    kj = f"core|federici|{o}|envelope|joint|default"; ke = kj.replace("|joint|", "|early|"); kl = kj.replace("|joint|", "|late|")
                    rk = y.replace("gain_bits", "regular/logloss_bits")
                    st = np.array([[P[ke].get(i, {}).get(rk, np.nan) - P[kj].get(i, {}).get(rk, np.nan),
                                    P[kl].get(i, {}).get(rk, np.nan) - P[kj].get(i, {}).get(rk, np.nan)] for i in ba]) if (kj in P and ke in P and kl in P) else np.full((len(ba), 2), np.nan)
                    out["function"][f"federici|{o}|{y}|behav_acc"] = nested_models(yv, [Cm, ov[:, None], st])
            out["federici_development"][f"{o}|{w}"] = r
    # DTU SRT and FAU CI HSM: C -> C + overall alignment -> + temporal structure (Local target)
    try:
        import pandas as pd
        tsv = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
        aud = [c for c in tsv.columns if c.startswith("audiogram_") and any(f"_{f}Hz" in c for f in (500, 1000, 2000, 4000))]
        dcov = {r.participant_id: {"age": r.age, "srt": r.speech_reception_thresholds, "pta": np.nanmean([getattr(r, c) for c in aud])} for r in tsv.itertuples()}
        for o in OBJ:
            k = f"core|dtu|{o}|local|full|default"
            if k not in P:
                continue
            for y in ("unified/gain_bits", "native/gain_bits"):
                ids = [i for i in P[k] if i in dcov]
                kj = f"core|dtu|{o}|local|joint|default"; ke = kj.replace("|joint|", "|early|"); kl = kj.replace("|joint|", "|late|")
                rk = y.replace("gain_bits", "regular/logloss_bits")
                st = np.array([[P.get(ke, {}).get(i, {}).get(rk, np.nan) - P.get(kj, {}).get(i, {}).get(rk, np.nan),
                                P.get(kl, {}).get(i, {}).get(rk, np.nan) - P.get(kj, {}).get(i, {}).get(rk, np.nan)] for i in ids])
                out["function"][f"dtu|{o}|{y}|SRT"] = nested_models([dcov[i]["srt"] for i in ids], [np.array([[dcov[i]["age"], dcov[i]["pta"]] for i in ids], float),
                                                                                         np.array([P[k][i].get(y, np.nan) for i in ids])[:, None], st])
    except Exception as ex:
        out["function"]["dtu_error"] = repr(ex)
    try:
        import csv
        from auditory_c3.h7_function import _logit_pct, _num
        t4 = {r["ID"]: r for r in csv.DictReader(open(os.path.join(REPO, "private", "auditory_c3", "jehn_behaviour", "table4_parsed.csv")))}
        for o in OBJ:
            k = f"core|fau|{o}|local|full|default"
            if k not in P:
                continue
            ids = [i for i in P[k] if i in t4 and np.isfinite(_num(t4[i]["HSM"]))]
            for y in ("unified/gain_bits", "native/gain_bits"):
                kj = f"core|fau|{o}|local|joint|default"; ke = kj.replace("|joint|", "|early|"); kl = kj.replace("|joint|", "|late|")
                rk = y.replace("gain_bits", "regular/logloss_bits")
                st = np.array([[P.get(ke, {}).get(i, {}).get(rk, np.nan) - P.get(kj, {}).get(i, {}).get(rk, np.nan),
                                P.get(kl, {}).get(i, {}).get(rk, np.nan) - P.get(kj, {}).get(i, {}).get(rk, np.nan)] for i in ids])
                Cm = np.array([[_num(t4[i]["Age"]), max(_num(t4[i]["CIexpR"]), _num(t4[i]["CIexpL"]))] for i in ids], float)
                out["function"][f"fau_ci|{o}|{y}|HSM_logit"] = nested_models(_logit_pct(np.array([_num(t4[i]["HSM"]) for i in ids])),
                                                                             [Cm, np.array([P[k][i].get(y, np.nan) for i in ids])[:, None], st])
    except Exception as ex:
        out["function"]["fau_error"] = repr(ex)
    out["sign"] = "nested_models: risk differences are bigger model - smaller model on LOO squared error; negative = improvement"
    return out


if __name__ == "__main__":
    main()
