"""Round-1 aggregation to the frozen text (SCI_R1_PREREG v3 §6, §8, §9, §12). Per-task outputs -> identity values -> summaries.

Identities: FAU / DTU participant id; Federici record -> subject_uid (reaggregate/entity_manifest.csv; HC, CI, HC-v independent;
the phantom = one entity, per-session values only, never in human summaries); private child id. Per identity: mean over its
units (content folds; seeds where stated), then records -> subject. Summaries: stats.summary / contrast / ols (bootstrap-t,
per-group replicate indices seeded by (dataset, group) so that members of a family share replicate b of each group).
Families (implementation note SCI_R1_ADDENDUM_01 §1): primary = dataset x objective (+ one objective-free raw family per
dataset); TG blocks = dataset x objective; S4 group / development / function = dataset x objective (raw objects: dataset).
Outputs: results/auditory_alignment_v3/sci_r1/ (continuous aggregates), results/.../sci_r1/private_agg/ (0700, private-task
aggregates, not a publication candidate without user approval), private/auditory_alignment_v3/sci_r1/agg/ (per-identity
tables, all spatial outputs of private-trained models). Cells with n < 5 report n only. E7 scan over every written JSON.
"""
from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict

import numpy as np

from auditory_alignment_v3 import core
from . import lags as L
from . import stats as S

OUT = os.path.join(core.OUT, "sci_r1")
RES = os.environ.get("SCI_R1_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "sci_r1"))  # dry runs: a private scratch dir
PRIV_RES = os.path.join(RES, "private_agg")
AGG = os.environ.get("SCI_R1_AGG", os.path.join(OUT, "agg"))
GROUPS = {"fau": ["th", "ha", "ci"], "dtu": ["nh", "hi"], "federici": ["HC", "CI", "HC-v"], "private_bdf": ["HA", "NH"]}
CONTRASTS = {"fau": [("ha", "th"), ("ci", "th"), ("ci", "ha")], "dtu": [("hi", "nh")], "federici": [("CI", "HC"), ("HC-v", "HC")],
             "private_bdf": [("HA", "NH")]}
CM = ("gain_bits", "rank_gain", "hard_gain_bits", "regular_logloss_bits", "mismatched_logloss_bits", "top1", "rank_pct", "top5", "mrr")
PM = ("auc", "nll_bits", "brier", "gain_vs_base_bits", "hist_gain_bits", "hist_gain_cs_bits", "hist_gain_twin_bits",
      "hist_gain_twin_cs_bits", "auc_fit_all", "nll_bits_fit_all")
OBJ = ("NCE", "CS_SINGLE")
MIN_N = 5


def jl(x):
    if isinstance(x, dict):
        return {str(k): jl(v) for k, v in x.items() if k not in ("boot", "T")}
    if isinstance(x, (list, tuple)):
        return [jl(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


# ------------------------------------------------------------------------------------------------ loading
class Store:
    def __init__(self):
        import pandas as pd
        self.plan = json.load(open(os.path.join(OUT, "plan.json")))
        self.tasks = {t["key"]: dict(t, job=j["name"], dataset=j["dataset"], cf=j["content_fold"]) for j in self.plan["jobs"] for t in j["tasks"]}
        self.status = {}
        for k, t in self.tasks.items():
            base = os.path.join(OUT, "private" if t["dataset"] == "private_bdf" else "continuous", k)
            self.status[k] = "complete" if os.path.exists(base + ".json") else ("failed" if os.path.exists(base + ".FAILED.json") else "missing")
        m = pd.read_csv(os.path.join(core.OUT, "reaggregate", "entity_manifest.csv"))
        self.fed = {r.record_uid: r for r in m.itertuples()}
        self.fed_age = {r.subject_uid: (None if r.age_years != r.age_years else float(r.age_years)) for r in self.fed.values() if r.entity_type == "human"}
        self.fed_acc = {r.subject_uid: (None if r.behav_acc != r.behav_acc else float(r.behav_acc)) for r in self.fed.values() if r.entity_type == "human"}
        self._cache = {}

    def load(self, key):
        if key not in self._cache:
            t = self.tasks[key]
            base = os.path.join(OUT, "private" if t["dataset"] == "private_bdf" else "continuous", key)
            self._cache = {key: (json.load(open(base + ".json")), dict(np.load(base + ".npz")))}  # keep one task in memory
        return self._cache[key]

    def keys(self, ds, **flt):
        out = []
        for k, t in self.tasks.items():
            if t["dataset"] != ds or self.status[k] != "complete":
                continue
            if all((t.get(a) in b) if isinstance(b, (list, tuple, set)) else t.get(a) == b for a, b in flt.items()):
                out.append(k)
        return sorted(out)

    def identity(self, ds, pid, group):
        if ds != "federici":
            return pid, group, "human"
        r = self.fed[pid]
        return r.subject_uid, r.condition, ("phantom" if r.entity_type == "phantom" else "human")


def collect(st, ds, keys, arr, sel=lambda a: a, records=False):
    """keys' arrays [P, ...] -> {identity: (group, kind, mean over occurrences)}; records=True keeps record ids (phantom sessions)."""
    acc = defaultdict(list); grp = {}
    for k in keys:
        meta, A = st.load(k)
        if arr not in A:
            continue
        ids = meta.get("participants") or meta.get("children")
        for j, pid in enumerate(ids):
            ident, g, kind = st.identity(ds, pid, meta["groups"][j])
            key = pid if records else ident
            acc[key].append(np.asarray(sel(A[arr][j]), float)); grp[key] = (g, kind)
    return {i: (grp[i][0], grp[i][1], np.mean(np.stack(v), 0)) for i, v in acc.items()}


def mapv(vals, f):
    return {i: (g, k, f(v)) for i, (g, k, v) in vals.items()}


def pair(va, vb, f):
    common = sorted(set(va) & set(vb))
    return {i: (va[i][0], va[i][1], f(va[i][2], vb[i][2])) for i in common}


def wmean(c, ds, win, offset=0):
    idx = [k + offset for k in L.WINDOW_TOKENS[ds][win]]
    return np.nanmean(c[..., idx], -1)


def human(vals, group=None):
    items = sorted((i, v) for i, (g, k, v) in vals.items() if k == "human" and (group is None or g == group))
    return [i for i, _ in items], [v for _, v in items]


def finite(ids, Y, label, notes):
    Y = np.asarray(Y, float)
    if Y.size == 0:
        return ids, Y
    ok = np.isfinite(Y.reshape(len(Y), -1)).all(1)
    if (~ok).any():
        notes.append(f"{label}: {int((~ok).sum())} identities with non-finite values excluded")
    return [i for i, o in zip(ids, ok) if o], Y[ok]


def summ(vals, ds, label, notes, groups=True):
    """per group + all humans; bootstrap-t with (dataset, group)-seeded replicate indices; n < 5 -> n only."""
    out = {}
    for g in (["all"] + (GROUPS[ds] if groups else [])):
        ids, Y = human(vals, None if g == "all" else g)
        ids, Y = finite(ids, Y, f"{label}/{g}", notes)
        if len(Y) < MIN_N:
            out[g] = {"n": len(Y), "note": "n<5: estimate withheld"}; continue
        out[g] = S.summary(Y, idx=S.draws(len(Y), seed=S.group_seed(ds, g, len(Y))))
    ph = {i: v for i, (g, k, v) in vals.items() if k == "phantom"}
    if ph:
        out["phantom_descriptive"] = {"est": np.mean(np.stack(list(ph.values())), 0), "n_entities": 1}
    return out


def phantom_sessions(st, keys, arr, sel):
    """Federici phantom: per-session values (mean over the subject-fold units that scored it), mean and range; no intervals."""
    v = {i: x for i, (g, k, x) in collect(st, "federici", keys, arr, sel, records=True).items() if k == "phantom"}
    if not v:
        return None
    M = np.stack(list(v.values()))
    return {"n_sessions": len(v), "per_session": M, "mean": M.mean(0), "min": M.min(0), "max": M.max(0)}


def matrix_summ(vals, ds, label, notes):
    """matrices [K, K] per identity: group mean matrices and a max-t band over all cells (all humans)."""
    out = {}
    for g in ["all"] + GROUPS[ds]:
        ids, Y = human(vals, None if g == "all" else g)
        ids, Y = finite(ids, Y, f"{label}/{g}", notes)
        if len(Y) < MIN_N:
            out[g] = {"n": len(Y)}; continue
        if g == "all":
            K = Y.shape[1]; s = S.summary(Y.reshape(len(Y), -1), idx=S.draws(len(Y), seed=S.group_seed(ds, g, len(Y))))
            out[g] = {"n": len(Y), "mean": s["est"].reshape(K, K), "band_low": s["band_low"].reshape(K, K), "band_high": s["band_high"].reshape(K, K), "crit": s["crit"]}
        else:
            out[g] = {"n": len(Y), "mean": Y.mean(0)}
    return out


# ------------------------------------------------------------------------------------------------ continuous S1 / MD-SB
def s1_continuous(st, ds, notes):
    res = {"raw": {}, "objectives": {}}
    raw = st.keys(ds, panel="R")
    rv = {"raw": collect(st, ds, raw, "s1"), "rawpca": collect(st, ds, raw, "s1_pca"), "rawneg": collect(st, ds, raw, "s1_neg")}
    for n, v in rv.items():
        res["raw"][n] = {m: summ(mapv(v, lambda a, j=CM.index(m): a[:, j]), ds, f"{ds}/{n}/{m}", notes) for m in ("gain_bits", "rank_gain", "regular_logloss_bits")}
    rr = rv["raw"]
    res["raw"]["windows"] = {m: {w: summ(mapv(rr, lambda a, j=CM.index(m), w=w: wmean(a[:, j], ds, w)), ds, f"{ds}/raw/{m}/{w}", notes) for w in ("early", "late")}
                             for m in ("gain_bits", "rank_gain", "regular_logloss_bits")}
    res["raw"]["neg_mean_gain"] = summ(mapv(rv["rawneg"], lambda a: np.nanmean(a[:, 0])), ds, f"{ds}/rawneg/mean", notes)
    if ds == "federici":
        res["raw"]["phantom_sessions_gain"] = phantom_sessions(st, raw, "s1", lambda a: a[:, 0])
    res["raw"]["noica"] = None
    if ds == "fau":
        nv = collect(st, ds, st.keys(ds, panel="RN"), "s1")
        if nv:
            res["raw"]["noica"] = {"curve_gain": summ(mapv(nv, lambda a: a[:, 0]), ds, "fau/noica/curve", notes),
                                   "early_gain": summ(mapv(nv, lambda a: wmean(a[:, 0], ds, "early")), ds, "fau/noica/early", notes),
                                   "neg_mean_gain": summ(mapv(collect(st, ds, st.keys(ds, panel="RN"), "s1_neg"), lambda a: np.nanmean(a[:, 0])), ds, "fau/noica/neg", notes)}
            res["raw"]["noica_vals"] = nv
    vals_out = {}
    for obj in OBJ:
        r = {}
        fz = collect(st, ds, st.keys(ds, panel="P0", objective=obj), "s1")
        a2 = collect(st, ds, st.keys(ds, panel="P1", objective=obj), "s1")
        s3 = collect(st, ds, st.keys(ds, panel=["P0", "P3"], objective=obj, window="full"), "s1")
        un = collect(st, ds, st.keys(ds, panel="P2", seed=3401), "s1")
        un3 = collect(st, ds, st.keys(ds, panel="P2"), "s1")
        cur = {"frozen": fz, "aln2": a2, "frozen_3seed": s3, "untrained_s3401": un, "untrained_3draws": un3}
        r["curves"] = {n: {m: summ(mapv(v, lambda a, j=CM.index(m): a[:, j]), ds, f"{ds}/{obj}/{n}/{m}", notes) for m in ("gain_bits", "rank_gain", "regular_logloss_bits")}
                       for n, v in cur.items() if v}
        r["windows"] = {n: {m: {w: summ(mapv(v, lambda a, j=CM.index(m), w=w: wmean(a[:, j], ds, w)), ds, f"{ds}/{obj}/{n}/{m}/{w}", notes) for w in ("early", "late")}
                            for m in ("gain_bits", "rank_gain", "regular_logloss_bits")} for n, v in cur.items() if v}
        if ds == "federici":
            r["phantom_sessions_frozen_gain"] = phantom_sessions(st, st.keys(ds, panel="P0", objective=obj), "s1", lambda a: a[:, 0])
        pairs = {"frozen_minus_raw": (fz, rr), "frozen_minus_rawpca": (fz, rv["rawpca"]), "frozen_minus_untrained": (fz, un), "aln3_minus_aln2": (fz, a2),
                 "frozen3_minus_untrained3": (s3, un3)}
        r["paired"] = {}
        for name, (va, vb) in pairs.items():
            if not va or not vb:
                continue
            r["paired"][name] = {m: {"curve": summ(pair(va, vb, lambda x, y, j=CM.index(m): x[:, j] - y[:, j]), ds, f"{ds}/{obj}/{name}/{m}", notes),
                                     **{w: summ(pair(va, vb, lambda x, y, j=CM.index(m), w=w: wmean(x[:, j], ds, w) - wmean(y[:, j], ds, w)), ds, f"{ds}/{obj}/{name}/{m}/{w}", notes)
                                        for w in ("early", "late")}} for m in ("gain_bits", "rank_gain", "regular_logloss_bits")}
        r["seed_dispersion"] = {}
        for w in ("early", "late"):
            per = {}
            for seed in (3401, 3407, 3413):
                v = collect(st, ds, st.keys(ds, panel=["P0", "P3"], objective=obj, window="full", seed=seed), "s1", lambda a, w=w: wmean(a[:, 0], ds, w))
                _, Y = human(v)
                if Y:
                    per[seed] = float(np.mean(Y))
            vv = list(per.values())
            r["seed_dispersion"][w] = {"per_seed_mean_gain": per, "mean": float(np.mean(vv)) if vv else None,
                                       "range": [float(min(vv)), float(max(vv))] if vv else None, "sd": float(np.std(vv, ddof=1)) if len(vv) > 1 else None,
                                       "note": "seeds also change the readout's 400-segment / es-query draws"}
        for panel in ("P0", "P1"):
            for nm in ("md", "sb"):
                v = collect(st, ds, st.keys(ds, panel=panel, objective=obj), nm)
                if not v:
                    continue
                K = next(iter(v.values()))[2].shape[0] - 4
                r[f"{nm}_{panel}"] = {"curve_R": summ(mapv(v, lambda a, K=K: a[:K, 1]), ds, f"{ds}/{obj}/{nm}{panel}/R", notes),
                                      "curve_G": summ(mapv(v, lambda a, K=K: a[:K, 0]), ds, f"{ds}/{obj}/{nm}{panel}/G", notes),
                                      **{f"{w}_{sc}": summ(mapv(v, lambda a, c=K + ci, s=si: a[c, s]), ds, f"{ds}/{obj}/{nm}{panel}/{w}{sc}", notes)
                                         for ci, w in enumerate(("early", "late", "early_touching", "late_touching")) for si, sc in ((1, "R"), (0, "G"))}}
        for t in ("Ac", "Lz"):
            v = collect(st, ds, st.keys(ds, panel="P4", objective=obj, target=t), "s1", lambda a: a[:, 0])
            vr = collect(st, ds, st.keys(ds, panel="R4", target=t), "s1", lambda a: a[:, 0])
            if v:
                r[f"target_{t}"] = {"frozen": summ(v, ds, f"{ds}/{obj}/{t}", notes), "raw": summ(vr, ds, f"{ds}/{t}/raw", notes) if vr else None,
                                    "label": "Whisper-state target with full-window self-attention: acausal context"}
        for w in ("early", "late", "joint"):
            v = collect(st, ds, st.keys(ds, panel="P5", objective=obj, window=w), "s1", lambda a: a[:, 0])
            if v:
                r[f"window_trained_{w}"] = summ(v, ds, f"{ds}/{obj}/P5/{w}", notes)
        res["objectives"][obj] = r
        vals_out[obj] = {"frozen": fz, "raw": rr, "rawneg": rv["rawneg"], "noica": res["raw"].get("noica_vals"),
                         "md": collect(st, ds, st.keys(ds, panel="P0", objective=obj), "md"), "sb": collect(st, ds, st.keys(ds, panel="P0", objective=obj), "sb")}
    res["raw"].pop("noica_vals", None)
    return res, vals_out


# ------------------------------------------------------------------------------------------------ TG
def blocks(M, ds):
    e, l = L.WINDOW_TOKENS[ds]["early"], L.WINDOW_TOKENS[ds]["late"]
    DE = np.nanmean(np.stack([M[..., k, k] for k in e], -1), -1)
    DL = np.nanmean(np.stack([M[..., k, k] for k in l], -1), -1)
    GEL = np.nanmean(M[..., e, :][..., :, l].reshape(M.shape[:-2] + (-1,)), -1)
    GLE = np.nanmean(M[..., l, :][..., :, e].reshape(M.shape[:-2] + (-1,)), -1)
    return {"D_E": DE, "D_L": DL, "G_EL": GEL, "G_LE": GLE, "D_E_minus_G_EL": DE - GEL, "D_L_minus_G_LE": DL - GLE}


def tg(st, ds, notes):
    cells = {"R": 3, "G": 0, "rank_gain": 2, "G_tau_fixed": 1} if ds != "private_bdf" else {"AUC": 0, "NLL": 1}
    res = {}
    for obj in OBJ:
        r = {}
        srcs = {"frozen": st.keys(ds, panel="P0", objective=obj), "aln2": st.keys(ds, panel="P1", objective=obj),
                "untrained_s3401": st.keys(ds, panel="P2", seed=3401), "raw": st.keys(ds, panel="R")}
        for n, ks in srcs.items():
            for cname, ci in cells.items():
                v = collect(st, ds, ks, "tg", lambda a, c=ci: a[..., c])
                if not v:
                    continue
                r.setdefault(n, {})[cname] = {"matrix": matrix_summ(v, ds, f"tg/{ds}/{obj}/{n}/{cname}", notes),
                                              "blocks": {b: summ(mapv(v, lambda m, b=b: blocks(m, ds)[b]), ds, f"tg/{ds}/{obj}/{n}/{cname}/{b}", notes)
                                                         for b in ("D_E", "D_L", "G_EL", "G_LE", "D_E_minus_G_EL", "D_L_minus_G_LE")}}
        first = list(cells)[0]
        for w in ("early", "late"):  # P5 within-window TG (docs/13 l.25 sensitivity)
            v = collect(st, ds, st.keys(ds, panel="P5", objective=obj, window=w), "tg", lambda a, c=cells[first]: a[..., c])
            if v:
                r[f"window_trained_{w}"] = {first: matrix_summ(v, ds, f"tg/{ds}/{obj}/P5{w}", notes)}
        res[obj] = r
    return res


def tg_vals_for_s4(st, ds):
    out = {}
    ci = 3 if ds != "private_bdf" else 0
    for obj in OBJ:
        v = collect(st, ds, st.keys(ds, panel="P0", objective=obj), "tg", lambda a: a[..., ci])
        out[obj] = {b: mapv(v, lambda m, b=b: blocks(m, ds)[b]) for b in ("D_E", "D_L", "G_EL", "G_LE", "D_E_minus_G_EL", "D_L_minus_G_LE")} if v else {}
    return out


# ------------------------------------------------------------------------------------------------ Q4 triad (stored unit records)
def triad(st, ds, notes):
    from auditory_alignment.aggregate import unit_rows
    from auditory_alignment_v3 import run as r3
    fams = {"local": "E_LOCAL" if ds == "private_bdf" else "A_LOCAL"}
    if ds in ("fau", "dtu"):
        fams.update({"Ac": "A_TARGETS", "Lz": "A_TARGETS"})
    rows = r3.all_rows()
    res = {}
    for tname, fam in fams.items():
        for obj in OBJ:
            seeds = (3401, 3407, 3413) if (obj == "NCE" and tname == "local") else (3401,)
            per = defaultdict(lambda: defaultdict(list)); grp = {}
            for r in rows:
                s = r["spec"]
                if r["family_id"] != fam or r["dataset"] != ds or r["seed"] not in seeds or s.get("architecture") != "lag_local_tokens" or s["objective"] != obj:
                    continue
                if s.get("projection_dim", 32) != 32 or (fam == "A_TARGETS" and s.get("target") != tname):
                    continue
                p = os.path.join(core.OUT, "units", f"{r['experiment_id']}.json")
                if not os.path.exists(p):
                    continue
                rec = json.load(open(p))
                if rec.get("status") != "complete":
                    notes.append(f"triad: {r['experiment_id']} status {rec.get('status')}"); continue
                w = s.get("window", "full")
                if ds == "private_bdf":
                    for cid, v in rec["eval"]["native_calibration"]["per_participant"].items():
                        ident, g, kind = st.identity(ds, cid, rec["eval"]["per_participant"][cid]["group"]); grp[ident] = (g, kind)
                        per[ident][f"R_{w}"].append(v["positive_affine"]["nll_bits"]); per[ident][f"AUC_{w}"].append(v["positive_affine"]["auc_score"])
                else:
                    for pid, v in unit_rows(rec).items():
                        ident, g, kind = st.identity(ds, pid, v["group"]); grp[ident] = (g, kind)
                        per[ident][f"R_{w}"].append(v["unified/regular/logloss_bits"]); per[ident][f"G_{w}"].append(v["unified/gain_bits"])
                        per[ident][f"Rnat_{w}"].append(v.get("native/regular/logloss_bits", np.nan))
            vals = {i: {k: float(np.mean(x)) for k, x in d.items()} for i, d in per.items()}
            need = ("R_early", "R_late", "R_joint")
            out = {"seeds": list(seeds), "readout": "unified (native secondary)" if ds != "private_bdf" else "positive-affine native calibration (NLL, AUC)"}
            for name, f in (("R_early_minus_R_joint", lambda d: d["R_early"] - d["R_joint"]), ("R_late_minus_R_joint", lambda d: d["R_late"] - d["R_joint"]),
                            ("R_joint_minus_R_full", lambda d: d["R_joint"] - d.get("R_full", np.nan))):
                v = {i: (grp[i][0], grp[i][1], f(d)) for i, d in vals.items() if all(k in d for k in need)}
                out[name] = summ(v, ds, f"triad/{ds}/{tname}/{obj}/{name}", notes)
            if ds != "private_bdf":
                for name, f in (("Rnat_early_minus_Rnat_joint", lambda d: d.get("Rnat_early", np.nan) - d.get("Rnat_joint", np.nan)),
                                ("Rnat_late_minus_Rnat_joint", lambda d: d.get("Rnat_late", np.nan) - d.get("Rnat_joint", np.nan))):
                    v = {i: (grp[i][0], grp[i][1], f(d)) for i, d in vals.items() if all(k in d for k in need)}
                    out[name + "_secondary"] = summ(v, ds, f"triad/{ds}/{tname}/{obj}/{name}", notes)
            for w in ("early", "late", "joint", "full"):
                for m in (("R", "AUC") if ds == "private_bdf" else ("R", "G")):
                    v = {i: (grp[i][0], grp[i][1], d[f"{m}_{w}"]) for i, d in vals.items() if f"{m}_{w}" in d}
                    out[f"{m}_{w}"] = summ(v, ds, f"triad/{ds}/{tname}/{obj}/{m}{w}", notes)
            res[f"{tname}|{obj}"] = (out, {i: (grp[i][0], grp[i][1], d) for i, d in vals.items()})
    return res


# ------------------------------------------------------------------------------------------------ primary families
def family(ds, members, notes, label, simultaneous=True):
    """members {name: {identity: value}} (all humans) -> bootstrap-t per member on the common identities with shared replicate
    indices, and the family max-t simultaneous intervals."""
    sets = [set(i for i, x in m.items() if np.isfinite(x)) for m in members.values()]
    common = sorted(set.intersection(*sets)) if sets else []
    out = {"n_common": len(common), "members": {}}
    if len(common) < MIN_N:
        out["note"] = "n<5"; return out
    idx = S.draws(len(common), seed=S.group_seed(ds, "family", len(common)))
    items = {}
    for name, m in members.items():
        s = S.summary(np.array([m[i] for i in common]), idx=idx)
        out["members"][name] = s; items[name] = (float(s["est"]), float(s["se"]), s["T"])
        if len(m) - len(common):
            notes.append(f"{label}/{name}: {len(m) - len(common)} identities outside the common set")
    if simultaneous:
        out["family_maxt"] = S.family_maxt(items)
    return out


def primary_families(ds, s1vals, triad_res, notes):
    out = {}
    raw = s1vals["NCE"]["raw"]
    for obj in OBJ:
        v = s1vals[obj]; tri = triad_res.get(f"local|{obj}", (None, {}))[1]
        fz = v["frozen"]
        if not fz:
            continue
        K = next(iter(fz.values()))[2].shape[0]
        mem = {
            "triad_R_early_minus_R_joint": {i: d["R_early"] - d["R_joint"] for i, (g, k, d) in tri.items() if k == "human" and "R_early" in d and "R_joint" in d},
            "triad_R_late_minus_R_joint": {i: d["R_late"] - d["R_joint"] for i, (g, k, d) in tri.items() if k == "human" and "R_late" in d and "R_joint" in d},
            "SB_R_early": {i: a[K, 1] for i, (g, k, a) in v["sb"].items() if k == "human"},
            "SB_R_late": {i: a[K + 1, 1] for i, (g, k, a) in v["sb"].items() if k == "human"},
            "frozen_late_minus_early_gain": {i: wmean(a[:, 0], ds, "late") - wmean(a[:, 0], ds, "early") for i, (g, k, a) in fz.items() if k == "human"},
            "frozen_minus_raw_rank_gain_early": {i: wmean(a[:, 1], ds, "early") - wmean(raw[i][2][:, 1], ds, "early") for i, (g, k, a) in fz.items() if k == "human" and i in raw},
            "frozen_minus_raw_rank_gain_late": {i: wmean(a[:, 1], ds, "late") - wmean(raw[i][2][:, 1], ds, "late") for i, (g, k, a) in fz.items() if k == "human" and i in raw},
        }
        mem["interaction_rank_gain_late_minus_early"] = {i: mem["frozen_minus_raw_rank_gain_late"][i] - mem["frozen_minus_raw_rank_gain_early"][i]
                                                        for i in mem["frozen_minus_raw_rank_gain_late"] if i in mem["frozen_minus_raw_rank_gain_early"]}
        side = {"MD_R_early": {i: a[K, 1] for i, (g, k, a) in v["md"].items() if k == "human"},
                "MD_R_late": {i: a[K + 1, 1] for i, (g, k, a) in v["md"].items() if k == "human"},
                "frozen_minus_raw_gain_early": {i: wmean(a[:, 0], ds, "early") - wmean(raw[i][2][:, 0], ds, "early") for i, (g, k, a) in fz.items() if k == "human" and i in raw},
                "frozen_minus_raw_gain_late": {i: wmean(a[:, 0], ds, "late") - wmean(raw[i][2][:, 0], ds, "late") for i, (g, k, a) in fz.items() if k == "human" and i in raw},
                "frozen_minus_raw_R_early": {i: wmean(a[:, 3], ds, "early") - wmean(raw[i][2][:, 3], ds, "early") for i, (g, k, a) in fz.items() if k == "human" and i in raw},
                "frozen_minus_raw_R_late": {i: wmean(a[:, 3], ds, "late") - wmean(raw[i][2][:, 3], ds, "late") for i, (g, k, a) in fz.items() if k == "human" and i in raw}}
        out[obj] = family(ds, mem, notes, f"primary/{ds}/{obj}")
        out[obj]["listed_alongside_not_in_family"] = family(ds, side, notes, f"primary/{ds}/{obj}/side", simultaneous=False)
        out[obj]["seed_policy"] = "triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401"
    out["raw_objective_free"] = family(ds, {"raw_late_minus_early_gain": {i: wmean(a[:, 0], ds, "late") - wmean(a[:, 0], ds, "early") for i, (g, k, a) in raw.items() if k == "human"},
                                            "raw_late_minus_early_rank_gain": {i: wmean(a[:, 1], ds, "late") - wmean(a[:, 1], ds, "early") for i, (g, k, a) in raw.items() if k == "human"}},
                                       notes, f"primary/{ds}/raw")
    return out


# ------------------------------------------------------------------------------------------------ S4
def metas():
    import pandas as pd
    from auditory_alignment.data import PUB
    t = pd.read_csv(f"{PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
    aud = [c for c in t.columns if c.startswith("audiogram_") and any(f"_{f}Hz" in c for f in (500, 1000, 2000, 4000))]
    dtu = {r.participant_id: {"age": float(r.age), "srt": float(r.speech_reception_thresholds), "ssq_speech": float(r.SSQ_speech),
                              "pta": float(np.nanmean([getattr(r, c) for c in aud]))} for r in t.itertuples()}
    from auditory_c3.h7_function import _logit_pct, _num
    fau = {}
    for r in csv.DictReader(open(os.path.join(core.REPO, "private", "auditory_c3", "jehn_behaviour", "table4_parsed.csv"))):
        h = _num(r["HSM"])
        if np.isfinite(h):
            fau[r["ID"]] = {"hsm_logit": float(_logit_pct(np.array([h]))[0]), "age": _num(r["Age"]), "ci_years": max(_num(r["CIexpR"]), _num(r["CIexpL"]))}
    ch = pd.read_csv(os.path.join(core.REPO, "private", "auditory_pf", "prepare_002", "children.csv"))
    priv = {f"child{int(r.child)}": {"age": float(r.age_months) if r.age_months == r.age_months else None,
                                     "duration": float(r.duration_months) if r.duration_months == r.duration_months else None} for r in ch.itertuples()}
    return {"dtu": dtu, "fau": fau, "private_bdf": priv}


def stage(group, d):
    if group == "NH":
        return "NH"
    return None if d is None else ("0_2" if d <= 2 else ("ge13" if d >= 13 else "2_13"))


def s4_objects(ds, s1vals, tg_vals, triad_res):
    """{(family, object): identity values} for the S4 objects of SCI_R1_PREREG §9."""
    objs = {}
    for obj in OBJ:
        v = s1vals[obj]; fz = v["frozen"]
        if not fz:
            continue
        if ds == "private_bdf":
            col = lambda a, m: a[:, PM.index(m)]
            for w in ("early", "late"):
                objs[(obj, f"auc_{w}")] = mapv(fz, lambda a, w=w: wmean(col(a, "auc"), ds, w))
                objs[(obj, f"hist_increment_{w}")] = mapv(fz, lambda a, w=w: wmean(col(a, "hist_gain_bits"), ds, w))
                objs[(obj, f"twin_sensitivity_{w}")] = mapv(fz, lambda a, w=w: wmean(col(a, "hist_gain_bits") - col(a, "hist_gain_twin_bits"), ds, w))
            objs[(obj, "auc_late_minus_early")] = mapv(fz, lambda a: wmean(col(a, "auc"), ds, "late") - wmean(col(a, "auc"), ds, "early"))
        else:
            for w in ("early", "late"):
                objs[(obj, f"frozen_gain_{w}")] = mapv(fz, lambda a, w=w: wmean(a[:, 0], ds, w))
            objs[(obj, "frozen_gain_late_minus_early")] = mapv(fz, lambda a: wmean(a[:, 0], ds, "late") - wmean(a[:, 0], ds, "early"))
        if v["md"]:
            K = next(iter(v["md"].values()))[2].shape[0] - 4
            for nm, src in (("MD", v["md"]), ("SB", v["sb"])):
                for ci, w in enumerate(("early", "late")):
                    objs[(obj, f"{nm}_R_{w}")] = mapv(src, lambda a, c=K + ci: a[c, 1])
        tri = triad_res.get(f"local|{obj}", (None, {}))[1]
        objs[(obj, "triad_R_early_minus_R_joint")] = {i: (g, k, d.get("R_early", np.nan) - d.get("R_joint", np.nan)) for i, (g, k, d) in tri.items()}
        objs[(obj, "triad_R_late_minus_R_joint")] = {i: (g, k, d.get("R_late", np.nan) - d.get("R_joint", np.nan)) for i, (g, k, d) in tri.items()}
        for b, vals in tg_vals.get(obj, {}).items():
            objs[(obj, f"tg_{b}")] = vals
    raw = s1vals["NCE"]["raw"]
    if ds != "private_bdf":
        for w in ("early", "late"):
            objs[("raw", f"raw_gain_{w}")] = mapv(raw, lambda a, w=w: wmean(a[:, 0], ds, w))
        objs[("raw", "raw_gain_late_minus_early")] = mapv(raw, lambda a: wmean(a[:, 0], ds, "late") - wmean(a[:, 0], ds, "early"))
        objs[("raw", "neg_lag_mean_gain")] = mapv(s1vals["NCE"]["rawneg"], lambda a: np.nanmean(a[:, 0]))
        if s1vals["NCE"].get("noica"):
            objs[("raw", "noica_raw_gain_early")] = mapv(s1vals["NCE"]["noica"], lambda a: wmean(a[:, 0], ds, "early"))
    else:
        for w in ("early", "late"):
            objs[("raw", f"raw_auc_{w}")] = mapv(raw, lambda a, w=w: wmean(a[:, PM.index("auc")], ds, w, offset=9))
        objs[("raw", "prestim_mean_auc")] = mapv(raw, lambda a: np.nanmean(a[:9, PM.index("auc")]))
    return objs


def s4(st, ds, objs, md, notes):
    from auditory_alignment.aggregate import nested_models
    out = {"contrasts": {}, "development": {}, "function": {}, "families": {}}
    fam_items = defaultdict(lambda: defaultdict(dict))
    for (fam, name), vals in objs.items():
        if ds == "fau" and name == "noica_raw_gain_early":
            pass  # contrasts below (CI-TH, CI-HA) are the preregistered noica comparison
        for a, b in CONTRASTS[ds]:
            ia, ya = finite(*human(vals, a), f"s4/{ds}/{fam}/{name}/{a}", notes); ib, yb = finite(*human(vals, b), f"s4/{ds}/{fam}/{name}/{b}", notes)
            if len(ya) < MIN_N or len(yb) < MIN_N:
                out["contrasts"][f"{fam}|{name}|{a}-{b}"] = {"n_a": len(ya), "n_b": len(yb), "note": "n<5"}; continue
            c = S.contrast(ya, yb, idx_a=S.draws(len(ya), seed=S.group_seed(ds, a, len(ya))), idx_b=S.draws(len(yb), seed=S.group_seed(ds, b, len(yb))))
            out["contrasts"][f"{fam}|{name}|{a}-{b}"] = c; fam_items["group"][fam][f"{name}|{a}-{b}"] = (float(c["est"]), float(c["se"]), c["T"])
        if ds == "federici":
            for g in GROUPS[ds]:
                ids, Y = human(vals, g)
                X = [(st.fed_age.get(i), y) for i, y in zip(ids, Y)]
                X = [(x, y) for x, y in X if x is not None and np.isfinite(x) and np.isfinite(y)]
                if len(X) >= 8:
                    o = S.ols(np.array([[x] for x, _ in X]), np.array([y for _, y in X]), ["age_years"], seed=S.group_seed(ds, g, "ols"))
                    if "coef" in o:
                        o["note"] = "HC-v ages linked by file-number order (inferred)" if g == "HC-v" else ""
                        out["development"][f"{fam}|{name}|{g}|age"] = o
                        fam_items["development"][fam][f"{name}|{g}"] = (o["coef"]["age_years"]["est"], o["coef"]["age_years"]["se"], o["T"]["age_years"])
        if ds == "private_bdf":
            ids, Y = human(vals); gr = {i: g for i, (g, k, v) in vals.items()}
            X = [(md["private_bdf"].get(i, {}).get("age"), 1.0 if gr[i] == "HA" else 0.0, y) for i, y in zip(ids, Y)]
            X = [x for x in X if x[0] is not None and np.isfinite(x[2])]
            if len(X) >= 10:
                o = S.ols(np.array([[x[0], x[1]] for x in X]), np.array([x[2] for x in X]), ["age_months", "HA"], seed=S.group_seed(ds, "age+HA"))
                if "coef" in o:
                    out["development"][f"{fam}|{name}|age+HA"] = o
                    fam_items["development"][fam][f"{name}|age+HA"] = (o["coef"]["age_months"]["est"], o["coef"]["age_months"]["se"], o["T"]["age_months"])
            X = [(md["private_bdf"].get(i, {}).get("age"), md["private_bdf"].get(i, {}).get("duration"), y) for i, y in zip(ids, Y) if gr[i] == "HA"]
            X = [x for x in X if x[0] is not None and x[1] is not None and np.isfinite(x[2])]
            if len(X) >= 10:
                o = S.ols(np.array([[x[0], x[1]] for x in X]), np.array([x[2] for x in X]), ["age_months", "duration_months"], seed=S.group_seed(ds, "HA:age+dur"))
                if "coef" in o:
                    o["note"] = "two identifiable comparisons: age at fixed duration, duration at fixed age"
                    out["development"][f"{fam}|{name}|HA:age+duration"] = o
                    fam_items["development"][fam][f"{name}|HA:duration"] = (o["coef"]["duration_months"]["est"], o["coef"]["duration_months"]["se"], o["T"]["duration_months"])
            bins = defaultdict(list)
            for i, y in zip(ids, Y):
                lab = stage(gr[i], md["private_bdf"].get(i, {}).get("duration"))
                if lab and np.isfinite(y):
                    bins[lab].append(y)
            out["development"][f"{fam}|{name}|stage_bins"] = {b: (S.summary(np.array(v), seed=S.group_seed(ds, b)) if len(v) >= MIN_N else {"n": len(v), "note": "n<5: estimate withheld"})
                                                              for b, v in bins.items()}
        if ds == "dtu":
            for g in GROUPS[ds]:
                ids, Y = human(vals, g)
                X = [(md["dtu"][i]["age"], y) for i, y in zip(ids, Y) if i in md["dtu"] and np.isfinite(y)]
                if len(X) >= 8:
                    out["development"][f"{fam}|{name}|{g}|age_descriptive"] = S.ols(np.array([[x] for x, _ in X]), np.array([y for _, y in X]), ["age"], seed=S.group_seed(ds, g, "age"))
        specs = []
        if ds == "dtu":
            specs = [(m, None, (lambda i, m=m: md["dtu"].get(i, {}).get(m)), (lambda i: [md["dtu"][i]["age"], md["dtu"][i]["pta"]]), ["age", "pta"]) for m in ("srt", "ssq_speech")]
        elif ds == "fau":
            specs = [("hsm_logit", "ci", (lambda i: md["fau"].get(i, {}).get("hsm_logit")), (lambda i: [md["fau"][i]["age"], md["fau"][i]["ci_years"]]), ["age", "ci_years"])]
        elif ds == "federici":
            specs = [("behav_acc", g, (lambda i: st.fed_acc.get(i)), (lambda i: [st.fed_age.get(i)]), ["age_years"]) for g in GROUPS[ds]]
        for m, g, yf, cf, cn in specs:
            ids, Y = human(vals, g)
            X = []
            for i, x in zip(ids, Y):
                y = yf(i)
                if y is None or not np.isfinite(y) or not np.isfinite(x):
                    continue
                c = cf(i)
                if any(v is None or not np.isfinite(v) for v in c):
                    continue
                X.append((y, x, c))
            key = f"{fam}|{name}|{m}|{g or 'all'}"
            if len(X) < 10:
                out["function"][key] = {"n": len(X), "note": "too few linked identities"}; continue
            yv = np.array([x[0] for x in X]); rd = np.array([x[1] for x in X]); Cm = np.array([x[2] for x in X])
            o = S.ols(np.c_[rd, Cm], yv, ["readability"] + cn, seed=S.group_seed(ds, m, g or "all"))
            o["nested_loo"] = nested_models(yv, [Cm, rd[:, None]])
            out["function"][key] = o
            if "coef" in o:
                fam_items["function"][fam][f"{name}|{m}|{g or 'all'}"] = (o["coef"]["readability"]["est"], o["coef"]["readability"]["se"], o["T"]["readability"])
    for kind, fams in fam_items.items():
        for fam, items in fams.items():
            out["families"][f"{kind}|{fam}"] = S.family_maxt(items)
    return out


# ------------------------------------------------------------------------------------------------ S3, counts, time support
def spatial(st, ds, notes):
    from auditory_alignment_v2.foundation_adapter import CHANNELS
    out = {"channels": CHANNELS[ds], "note": "(a)(b) model-level maps: mean and range across units / folds, no identity bootstrap; (c) one value per test participant"}
    maps = defaultdict(list)
    for k in st.keys(ds, panel="R"):
        meta, A = st.load(k)
        for w in ("early", "late"):
            if "haufe_chan" in A:
                m = A["haufe_chan"][L.WINDOW_TOKENS[ds][w]].mean(0)
            elif "haufe" in A:
                m = A["haufe"][L.WINDOW_TOKENS[ds][w]].mean((0, 2))
            else:
                continue
            maps[w].append(m / (np.linalg.norm(m) + 1e-30))
    out["raw_haufe"] = {w: {"mean": np.mean(v, 0), "min": np.min(v, 0), "max": np.max(v, 0), "n_maps": len(v)} for w, v in maps.items()}
    for obj in OBJ:
        en = []
        for k in st.keys(ds, panel="P0", objective=obj):
            A = st.load(k)[1]
            if "filt_energy" in A:
                en.append(A["filt_energy"])
        if en:
            out[f"first_layer_explained_fraction_{obj}"] = {"mean": np.mean(en, 0), "min": np.min(en, 0), "max": np.max(en, 0), "n_units": len(en)}
        v = collect(st, ds, st.keys(ds, panel="P0", objective=obj), "chan_md", (lambda a: a[:, 0]) if ds == "private_bdf" else (lambda a: a))
        if v:
            out[f"channel_occlusion_{obj}"] = summ(v, ds, f"chan/{ds}/{obj}", notes)
    return out


def counts(st, ds):
    if ds == "private_bdf":
        ids = defaultdict(set)
        for k in st.keys(ds, panel="P0", objective="NCE"):
            meta, _ = st.load(k)
            for c, g in zip(meta["children"], meta["groups"]):
                ids[g].add(c)
        return {g: {"n_identities": len(v)} for g, v in ids.items()}
    per = defaultdict(lambda: {"ids": set(), "records": set(), "parts": set(), "queries": 0})
    for k in st.keys(ds, panel="P0", objective="NCE"):
        meta, _ = st.load(k)
        qps = meta.get("query_parts") or [[]] * len(meta["participants"])
        for pid, g, nq, qp in zip(meta["participants"], meta["groups"], meta["n_queries"], qps):
            ident, grp, kind = st.identity(ds, pid, g)
            key = "phantom" if kind == "phantom" else grp
            per[key]["ids"].add(ident); per[key]["records"].add(pid); per[key]["parts"] |= set(qp); per[key]["queries"] += nq
    out = {g: {"n_identities": len(d["ids"]), "n_records": len(d["records"]), "n_test_content_groups": len(d["parts"]),
               "n_queries_summed_over_units": d["queries"]} for g, d in per.items()}
    gs = sorted(per)
    out["test_content_overlap_jaccard"] = {f"{a}|{b}": len(per[a]["parts"] & per[b]["parts"]) / max(1, len(per[a]["parts"] | per[b]["parts"]))
                                           for i, a in enumerate(gs) for b in gs[i + 1:]}
    return out


def content_support(st):
    parts = defaultdict(list)
    for k in st.keys("federici", panel="P0", objective="NCE"):
        meta, _ = st.load(k)
        for pid, g, qp in zip(meta["participants"], meta["groups"], meta.get("query_parts", [])):
            ident, grp, kind = st.identity("federici", pid, g)
            if kind == "human":
                parts[(ident, grp)] += qp
    out = {}
    for g in GROUPS["federici"]:
        ids = [(i, st.fed_age.get(i)) for (i, gg) in parts if gg == g]
        ids = [(i, a) for i, a in ids if a is not None and np.isfinite(a)]
        if len(ids) < 3 * MIN_N:
            out[g] = {"n_identities": len(ids), "note": "fewer than 15 aged identities: tertiles not reported"}; continue
        cut = np.quantile([a for _, a in ids], [1 / 3, 2 / 3])
        for t, (lo, hi) in enumerate(((-np.inf, cut[0]), (cut[0], cut[1]), (cut[1], np.inf))):
            sel = [i for i, a in ids if (a > lo or t == 0) and a <= hi]
            q = [p for i in sel for p in parts[(i, g)]]
            out[f"{g}|tertile{t + 1}"] = {"n_identities": len(sel), "age_bounds_rounded_0p5y": [None if t == 0 else round(float(lo) * 2) / 2, None if t == 2 else round(float(hi) * 2) / 2],
                                         "n_queries": len(q), "n_content_groups": len(set(q))}
    return out


def time_support(st):
    out = {"filters": {"fau": "EEG 1-20 Hz zero-phase FIR (90% half-width ~25 ms); targets 1-8 Hz (~78 ms); stage-B ICA removed components whose envelope "
                              "cross-correlation peaked within +-23 ms (same rule for all groups)",
                       "dtu": "EEG 1-20 Hz zero-phase FIR (~25 ms); targets 1-8 Hz (~78 ms)",
                       "federici": "authors' 2-8 Hz cache (filter unknown; measured -3 dB 1.76-6.84 Hz); earliest negative-lag window touches the block start",
                       "private_bdf": "0.5-45 Hz zero-phase"},
           "target_window": {"fau": "8 frames = 62.5 ms", "dtu": "8 frames = 62.5 ms", "federici": "8 frames = 80 ms", "private_bdf": "current class (no audio target)"},
           "datasets": {}}
    for ds in ("fau", "dtu", "federici", "private_bdf"):
        ks = st.keys(ds, panel="P0")
        if not ks:
            continue
        meta, _ = st.load(ks[0])
        out["datasets"][ds] = {"lags": meta["lags"], "window_tokens_inside": L.WINDOW_TOKENS[ds], "window_tokens_touching": L.WINDOW_TOKENS_INTERSECT[ds],
                               "protocol_windows_ms": L.PROTOCOL_MS[ds], "negative_lag_starts_samples": L.NEG_OFFS[ds],
                               "adjacent_overlap": "40%" if ds in ("fau", "dtu") else "50%"}
    return out


# ------------------------------------------------------------------------------------------------ private S1
def s1_private(st, notes):
    ds = "private_bdf"; res = {"raw": {}, "objectives": {}}
    raw = collect(st, ds, st.keys(ds, panel="R"), "s1")
    for m in ("auc", "nll_bits", "hist_gain_bits", "auc_fit_all"):
        res["raw"][f"raw/{m}"] = summ(mapv(raw, lambda a, j=PM.index(m): a[:, j]), ds, f"private/raw/{m}", notes)
    res["raw"]["raw/twin_sensitivity"] = summ(mapv(raw, lambda a: a[:, PM.index("hist_gain_bits")] - a[:, PM.index("hist_gain_twin_bits")]), ds, "private/raw/twin", notes)
    vals_out = {}
    for obj in OBJ:
        r = {"curves": {}, "windows": {}}
        src = {"frozen": st.keys(ds, panel="P0", objective=obj), "aln2": st.keys(ds, panel="P1", objective=obj),
               "frozen_3seed": st.keys(ds, panel=["P0", "P3"], objective=obj, window="full"), "untrained_s3401": st.keys(ds, panel="P2", seed=3401),
               "untrained_3draws": st.keys(ds, panel="P2")}
        cv = {n: collect(st, ds, ks, "s1") for n, ks in src.items()}
        for n, v in cv.items():
            if not v:
                continue
            for m in ("auc", "nll_bits", "hist_gain_bits", "hist_gain_cs_bits"):
                r["curves"][f"{n}/{m}"] = summ(mapv(v, lambda a, j=PM.index(m): a[:, j]), ds, f"private/{obj}/{n}/{m}", notes)
                r["windows"][f"{n}/{m}"] = {w: summ(mapv(v, lambda a, j=PM.index(m), w=w: wmean(a[:, j], ds, w)), ds, f"private/{obj}/{n}/{m}/{w}", notes) for w in ("early", "late")}
            r["curves"][f"{n}/twin_sensitivity"] = summ(mapv(v, lambda a: a[:, PM.index("hist_gain_bits")] - a[:, PM.index("hist_gain_twin_bits")]), ds, f"private/{obj}/{n}/twin", notes)
        if cv["frozen"] and raw:
            r["paired_frozen_minus_raw_auc"] = {w: summ(pair(cv["frozen"], raw, lambda x, y, w=w: wmean(x[:, 0], ds, w) - wmean(y[:, 0], ds, w, offset=9)), ds, f"private/{obj}/fz-raw/{w}", notes)
                                                for w in ("early", "late")}
        mdv = collect(st, ds, st.keys(ds, panel="P0", objective=obj), "md"); sbv = collect(st, ds, st.keys(ds, panel="P0", objective=obj), "sb")
        if mdv:
            K = next(iter(mdv.values()))[2].shape[0] - 4
            for nm, src_ in (("md", mdv), ("sb", sbv)):
                r[nm] = {f"{w}_{sc}": summ(mapv(src_, lambda a, c=K + ci, s=si: a[c, s]), ds, f"private/{obj}/{nm}/{w}{sc}", notes)
                         for ci, w in enumerate(("early", "late", "early_touching", "late_touching")) for si, sc in ((0, "AUC_loss"), (1, "NLL_increase"))}
        res["objectives"][obj] = r
        vals_out[obj] = {"frozen": cv["frozen"], "raw": raw, "md": mdv, "sb": sbv, "rawneg": {}}
    return res, vals_out


# ------------------------------------------------------------------------------------------------ figures
def figures(cont, priv, outdir, privdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    made = []

    def curve(ax, s, col, lab, x=None):
        if not s or "est" not in s:
            return
        x = np.arange(len(s["est"])) if x is None else x
        ax.plot(x, s["est"], color=col, label=f"{lab} (n={s['n']})")
        ax.fill_between(x, s["band_low"], s["band_high"], color=col, alpha=0.15)
    for ds, r in cont["S1"].items():
        for obj, ro in r["objectives"].items():
            fig, ax = plt.subplots(figsize=(7.5, 4))
            curve(ax, ro["curves"].get("frozen", {}).get("gain_bits", {}).get("all"), "C0", "frozen local probe (ALN3)")
            curve(ax, r["raw"]["raw"]["gain_bits"].get("all"), "C1", "raw EEG strict-local linear")
            curve(ax, ro["curves"].get("untrained_s3401", {}).get("gain_bits", {}).get("all"), "C2", "untrained local encoder")
            curve(ax, ro["curves"].get("aln2", {}).get("gain_bits", {}).get("all"), "C3", "frozen local probe (ALN2)")
            ax.axhline(0, color="k", lw=0.5); ax.set_xlabel("lag token k (sample-access support: SCI_R1_TIME_SUPPORT.json)")
            ax.set_ylabel("unified gain (bits / 5 s query)"); ax.set_title(f"{ds} {obj}: per-lag readability (bootstrap-t max-t 95% bands)", fontsize=9); ax.legend(fontsize=7)
            p = os.path.join(outdir, f"S1_{ds}_{obj}.png"); fig.tight_layout(); fig.savefig(p, dpi=120); plt.close(fig); made.append(p)
    for ds, r in cont["TG"].items():
        for obj, ro in r.items():
            for n in ("frozen", "raw"):
                for cname in ("R", "G"):
                    m = ro.get(n, {}).get(cname, {}).get("matrix", {}).get("all", {}).get("mean")
                    if m is None:
                        continue
                    fig, ax = plt.subplots(figsize=(4.6, 4))
                    im = ax.imshow(np.asarray(m), origin="lower", cmap="viridis"); fig.colorbar(im, ax=ax, label="true-EEG logloss (bits)" if cname == "R" else "gain (bits)")
                    ax.set_xlabel("test lag tau'"); ax.set_ylabel("readout lag tau"); ax.set_title(f"TG {ds} {obj} {n} {cname}", fontsize=9)
                    p = os.path.join(outdir, f"TG_{ds}_{obj}_{n}_{cname}.png"); fig.tight_layout(); fig.savefig(p, dpi=120); plt.close(fig); made.append(p)
    if priv:
        for obj, ro in priv["S1"]["objectives"].items():
            fig, ax = plt.subplots(figsize=(7.5, 4))
            curve(ax, ro["curves"].get("frozen/auc", {}).get("all"), "C0", "frozen local probe AUC")
            curve(ax, priv["S1"]["raw"].get("raw/auc", {}).get("all"), "C1", "raw strict-local AUC", x=np.arange(-10, 29) * 20)
            ax.axhline(0.5, color="k", lw=0.5); ax.set_xlabel("raw: window start (ms from stimulus); frozen: token k"); ax.set_ylabel("AUC (mean over children)")
            ax.set_title(f"private {obj}: per-lag readability (bootstrap-t max-t bands)", fontsize=9); ax.legend(fontsize=7)
            p = os.path.join(privdir, f"S1_private_{obj}.png"); fig.tight_layout(); fig.savefig(p, dpi=120); plt.close(fig); os.chmod(p, 0o600); made.append(p)
    return made


# ------------------------------------------------------------------------------------------------ main
def _strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield str(k); yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)
    elif isinstance(o, str):
        yield o


def privacy_scan(paths, st):
    """E7: participant / identity ids may appear only as JSON strings (keys or values) if they leak; numbers are not scanned
    (one cohort uses 3-digit numeric ids that coincide with sample offsets and float digits)."""
    ids = set()
    for k in st.tasks:
        if st.status[k] != "complete":
            continue
        meta, _ = st.load(k)
        ds = st.tasks[k]["dataset"]
        for pid in (meta.get("participants") or meta.get("children") or []):
            ids.add(str(pid))
            if ds == "federici":
                ids.add(str(st.identity(ds, pid, "")[0]))
    ids = sorted((i for i in ids if len(i) >= 3), key=len, reverse=True)
    pat = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(i) for i in ids) + r")(?![A-Za-z0-9])") if ids else None
    bad = []
    for p in paths:
        if pat is not None and p.endswith(".json") and any(pat.search(s) for s in _strings(json.load(open(p)))):
            bad.append(p)
    return bad


def main():
    st = Store()
    notes = []
    md = metas()
    cont = {"S1": {}, "primary": {}, "TG": {}, "triad": {}, "S3": {}, "S4": {}, "counts": {}}
    for ds in ("fau", "dtu", "federici"):
        s1r, s1v = s1_continuous(st, ds, notes)
        tri = triad(st, ds, notes)
        cont["S1"][ds] = s1r; cont["triad"][ds] = {k: v[0] for k, v in tri.items()}
        cont["primary"][ds] = primary_families(ds, s1v, tri, notes)
        cont["TG"][ds] = tg(st, ds, notes)
        cont["S3"][ds] = spatial(st, ds, notes)
        cont["S4"][ds] = s4(st, ds, s4_objects(ds, s1v, tg_vals_for_s4(st, ds), tri), md, notes)
        cont["counts"][ds] = counts(st, ds)
        print("done", ds, flush=True)
    cont["counts"]["federici_content_support_by_age"] = content_support(st)
    s1p, s1pv = s1_private(st, notes)
    trip = triad(st, "private_bdf", notes)
    priv = {"S1": s1p, "TG": tg(st, "private_bdf", notes), "triad": {k: v[0] for k, v in trip.items()},
            "S4": s4(st, "private_bdf", s4_objects("private_bdf", s1pv, tg_vals_for_s4(st, "private_bdf"), trip), md, notes), "counts": counts(st, "private_bdf")}
    priv_spatial = spatial(st, "private_bdf", notes)
    status = {"complete": sum(v == "complete" for v in st.status.values()), "n_tasks": len(st.status),
              "failed": sorted(k for k, v in st.status.items() if v == "failed"), "missing": sorted(k for k, v in st.status.items() if v == "missing")}
    os.makedirs(os.path.join(RES, "figures"), exist_ok=True)
    os.makedirs(os.path.join(PRIV_RES, "figures"), mode=0o700, exist_ok=True); os.chmod(PRIV_RES, 0o700); os.chmod(os.path.join(PRIV_RES, "figures"), 0o700)
    os.makedirs(AGG, mode=0o700, exist_ok=True)
    head = {"prereg": "docs/auditory_alignment_v3/SCI_R1_PREREG.md (frozen v3, sha256 aab58bc1...)", "status": status}
    written = []
    for name, obj in (("SCI_R1_S1_time_curves", cont["S1"]), ("SCI_R1_primary_families", cont["primary"]), ("SCI_R1_temporal_generalization", cont["TG"]),
                      ("SCI_R1_window_triad", cont["triad"]), ("SCI_R1_spatial_readout", cont["S3"]), ("SCI_R1_group_development", cont["S4"]),
                      ("SCI_R1_counts", cont["counts"]), ("SCI_R1_TIME_SUPPORT", time_support(st))):
        p = os.path.join(RES, f"{name}.json"); json.dump(jl({**head, "data": obj}), open(p, "w")); written.append(p)
    for name, obj in priv.items():
        p = os.path.join(PRIV_RES, f"SCI_R1_private_{name}.json"); json.dump(jl({**head, "data": obj}), open(p, "w")); os.chmod(p, 0o600); written.append(p)
    json.dump(jl(priv_spatial), open(os.path.join(AGG, "private_spatial.json"), "w"))
    json.dump({"notes": notes}, open(os.path.join(AGG, "notes.json"), "w"), indent=1)
    figs = figures({"S1": cont["S1"], "TG": cont["TG"]}, priv, os.path.join(RES, "figures"), os.path.join(PRIV_RES, "figures"))
    bad = privacy_scan(written, st)
    print("written", len(written), "figures", len(figs), "status", {k: (v if isinstance(v, int) else len(v)) for k, v in status.items()},
          "notes", len(notes), "E7 privacy hits", bad, flush=True)
    if bad:
        raise SystemExit("E7: participant identifiers found in results files")


if __name__ == "__main__":
    main()
