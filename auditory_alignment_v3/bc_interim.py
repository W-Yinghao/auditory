"""ALN3 ADDENDUM_05 (docs/auditory_alignment_v3/ADDENDUM_05_BC_INTERIM_AGGREGATION.md): interim aggregation of the seed-3401
B_DENSE / C_COMPLEMENT / C_CAPACITY_CONTROL comparisons against the same-fold A_LOCAL lag_local_tokens base, the private E
summary and the D binding / progress status.

Per identity and configuration: mean over the identity's units (content folds, outer folds; Federici records -> subject_uid,
phantom excluded). Contrasts are within-identity paired differences, sign "positive = candidate better" (logloss-type:
reference - candidate). Inference: sci_r1.stats (bootstrap-t, family max-t with shared replicate indices). Not part of any
training code hash.

Usage: python -m auditory_alignment_v3.bc_interim [--skip-private] [--skip-d]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment_v3 import core
from auditory_alignment_v3.sci_r1 import stats as S

SEED = 3401
RES = os.environ.get("BC_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "bc_interim"))
PRIV = os.environ.get("BC_PRIV", os.path.join(core.OUT, "bc_interim"))
DOCS = os.environ.get("BC_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
DS = ("fau", "dtu", "federici")
OBJ = ("NCE", "CS_SINGLE")
ARCH = ("cbramod", "reve")
ADAPT = ("random_full", "pretrained_frozen", "pretrained_peft", "pretrained_partial", "pretrained_full")
PRE = ADAPT[1:]
READOUT = ("channel_phase_linear", "dense_query")
VARIANTS = ("concat_pretrained", "residual_pretrained_frozen", "residual_pretrained_peft", "residual_pretrained_full",
            "residual_random_frozen", "residual_random_trainable")
CAP = "residual_small_capacity"
FMONLY = {"concat_pretrained": "pretrained_frozen", "residual_pretrained_frozen": "pretrained_frozen", "residual_pretrained_peft": "pretrained_peft",
          "residual_pretrained_full": "pretrained_full", "residual_random_frozen": "random_full", "residual_random_trainable": "random_full"}
TARGET = {"fau": "local", "dtu": "local", "federici": "envelope"}
PRIMARY = "unified/regular/logloss_bits"
METRICS = (  # key, label, direction: lower -> reference - candidate; higher / raw -> candidate - reference
    (PRIMARY, "R", "lower"), ("unified/gain_bits", "gain", "higher"), ("unified/mismatched_eeg/logloss_bits", "R_mm", "raw"),
    ("unified/regular/top1", "top1", "higher"), ("unified/regular/rank_pct", "rank_pct", "lower"), ("unified/hard_gain_bits", "hard_gain", "higher"),
    ("native/regular/logloss_bits", "R_native", "lower"), ("attention/unified/accuracy", "att_acc", "higher"), ("kernel_cs_diff", "kernel_cs_diff", "raw"))
DIRECTION = {k: d for k, _, d in METRICS}
LABEL = {k: l for k, l, _ in METRICS}
PMETRICS = (("NLL", "lower"), ("AUC", "higher"), ("hist_gain", "higher"), ("twin_sens", "higher"))
PDIR = dict(PMETRICS)
MIN_N = 5
TRANSFER_AD = {"task_partial": "pretrained_partial", "task_full": "pretrained_full"}


# ------------------------------------------------------------------------------------------------ helpers
def jl(x):
    if isinstance(x, dict):
        return {str(k): jl(v) for k, v in x.items() if k not in ("T",)}
    if isinstance(x, (list, tuple)):
        return [jl(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


def diff(ref, cand, direction):
    return ref - cand if direction == "lower" else cand - ref


def cls(lo, hi):
    return "I>0" if lo > 0 else ("I<0" if hi < 0 else "contains 0")


def ckey(c):
    return "|".join(map(str, c))


def load_manifest(path=None):
    import csv
    path = path or os.path.join(core.OUT, "reaggregate", "entity_manifest.csv")
    return {r["record_uid"]: (r["subject_uid"], r["condition"], r["entity_type"]) for r in csv.DictReader(open(path))}


def unit_loader(out=None):
    out = out or core.OUT
    def load(eid):
        p = os.path.join(out, "units", f"{eid}.json")
        return json.load(open(p)) if os.path.exists(p) else None
    return load


# ------------------------------------------------------------------------------------------------ continuous: loading
def cfg_of(r):
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if ds not in DS or r["seed"] != SEED:
        return None
    o = s.get("objective")
    if f == "B_DENSE":
        c = ("B", ds, o, s["architecture"], s["adaptation"], s["readout"])
    elif f == "C_COMPLEMENT":
        c = ("C", ds, o, s["architecture"], s["variant"])
    elif f == "C_CAPACITY_CONTROL":
        c = ("C", ds, o, "-", CAP)
    elif f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        c = ("L", ds, o)
    else:
        return None
    if s.get("target") != TARGET[ds]:
        raise ValueError(f"{r['experiment_id']}: target {s.get('target')} != registered {TARGET[ds]} for {ds}")
    return c


def load_continuous(rows, load, manifest):
    from auditory_alignment.aggregate import unit_rows
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    grp, kind, counts, units, notes = {}, {}, defaultdict(dict), defaultdict(list), []
    status = Counter()
    for r in rows:
        c = cfg_of(r)
        if c is None:
            continue
        rec = load(r["experiment_id"])
        st = "missing" if rec is None else rec.get("status")
        status[(c[0], st)] += 1
        if st != "complete":
            notes.append(f"{r['experiment_id']} {ckey(c)}: status {st}"); continue
        units[c].append(r["experiment_id"])
        ds = r["dataset"]
        fold = (r["subject_fold"], r["content_fold"])
        if fold in counts[c]:
            raise ValueError(f"two units for configuration {ckey(c)} fold {fold}")
        counts[c][fold] = {pid: (v["unified/regular"]["n_candidates"], v["unified/regular"]["n_queries"]) for pid, v in rec["eval"]["per_participant"].items()}
        for pid, v in unit_rows(rec).items():
            if ds == "federici":
                if pid not in manifest:
                    raise KeyError(f"Federici record {pid} not in entity manifest")
                ident, g, k = manifest[pid]
            else:
                ident, g, k = pid, v.get("group"), "human"
            if g is None:
                g = grp.get((ds, ident))
            grp[(ds, ident)] = g; kind[(ds, ident)] = k
            for m in DIRECTION:
                x = v.get(m)
                if x is not None:
                    acc[c][ident][m].append(float(x))
    vals = {c: {i: {m: float(np.mean(x)) for m, x in d.items()} for i, d in per.items() if kind[(c[1], i)] == "human"} for c, per in acc.items()}
    phantoms = {ds: sorted({i for (d, i), k in kind.items() if d == ds and k != "human"}) for ds in DS}
    return {"vals": vals, "grp": grp, "counts": counts, "units": units, "status": status, "notes": notes,
            "n_phantom_entities": {ds: len(v) for ds, v in phantoms.items()}}


def pair_ok(data, ref, cand):
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


# ------------------------------------------------------------------------------------------------ continuous: design
def continuous_families():
    """-> [(family, scope, label, [(member, reference cfg, candidate cfg, tag)])]"""
    fams = []
    for ds in DS:
        for o in OBJ:
            L = ("L", ds, o)
            for a in ARCH:
                B = lambda ad, ro: ("B", ds, o, a, ad, ro)
                C = lambda v: ("C", ds, o, a, v)
                sc = f"{ds}|{o}|{a}"
                fams.append(("B-READOUT", sc, f"B-READOUT|{sc}", [(ad, B(ad, "channel_phase_linear"), B(ad, "dense_query"), "readout") for ad in ADAPT]))
                fams.append(("B-INIT", sc, f"B-INIT|{sc}", [(f"{ro}/{ad}", B("random_full", ro), B(ad, ro),
                                                             "initialization (matched full update)" if ad == "pretrained_full" else "recipe")
                                                            for ro in READOUT for ad in PRE]))
                fams.append(("B-ADAPT", sc, f"B-ADAPT|{sc}", [(f"{ro}/{ad}", B("pretrained_frozen", ro), B(ad, ro), "adaptation")
                                                             for ro in READOUT for ad in PRE[1:]]))
                fams.append(("B-LOCAL", sc, f"B-LOCAL|{sc}", [(f"{ro}/{ad}", L, B(ad, ro), "vs local") for ro in READOUT for ad in ADAPT]))
                fams.append(("C-ATTRIB", sc, f"C-ATTRIB|{sc}", [
                    ("init_full", C("residual_random_trainable"), C("residual_pretrained_full"), "initialization (matched update)"),
                    ("init_frozen", C("residual_random_frozen"), C("residual_pretrained_frozen"), "initialization (frozen)"),
                    ("capacity_frozen", ("C", ds, o, "-", CAP), C("residual_pretrained_frozen"), "capacity"),
                    ("capacity_peft", ("C", ds, o, "-", CAP), C("residual_pretrained_peft"), "capacity"),
                    ("capacity_full", ("C", ds, o, "-", CAP), C("residual_pretrained_full"), "capacity"),
                    ("residual_vs_concat", C("concat_pretrained"), C("residual_pretrained_frozen"), "residual structure")]))
                fams.append(("C-FMONLY", sc, f"C-FMONLY|{sc}", [(v, B(FMONLY[v], "dense_query"), C(v), "vs foundation only") for v in VARIANTS]))
            sc = f"{ds}|{o}"
            fams.append(("C-LOCAL", sc, f"C-LOCAL|{sc}", [(f"{a}/{v}", L, ("C", ds, o, a, v), "primary increment") for a in ARCH for v in VARIANTS]
                         + [(f"-/{CAP}", L, ("C", ds, o, "-", CAP), "primary increment (capacity control)")]))
    return fams


def member_values(vals, ref, cand, metric):
    a, b = vals.get(ref, {}), vals.get(cand, {})
    out = {}
    for i in set(a) & set(b):
        x, y = a[i].get(metric), b[i].get(metric)
        if x is not None and y is not None and np.isfinite(x) and np.isfinite(y):
            out[i] = diff(x, y, DIRECTION.get(metric) or PDIR[metric])
    return out


def run_family(label, members, vals, metric, notes, simultaneous=True, groups=None):
    """members [(name, ref, cand, tag)] -> per-member pointwise summaries (+ family max-t on the common identities)."""
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
        if groups is not None:
            r["groups"] = {}
            for g in sorted({groups(i) for i in common}, key=str):
                yg = np.array([Y[i] for i in common if groups(i) == g])
                if len(yg) < MIN_N:
                    r["groups"][str(g)] = {"n": int(len(yg))}
                else:
                    sg = S.summary(yg, seed=S.group_seed(label, metric, name, g))
                    r["groups"][str(g)] = {"n": int(len(yg)), **{k: float(sg[k]) for k in ("est", "ci_low", "ci_high")}}
        res["members"][name] = r
    if simultaneous and len(items) >= 1:
        fm = S.family_maxt(items)
        res["crit"] = fm["crit"]
        for name, iv in fm["intervals"].items():
            res["members"][name].update({"sim_low": iv["sim_low"], "sim_high": iv["sim_high"], "class": cls(iv["sim_low"], iv["sim_high"])})
    return res


def levels(vals, cfgs, metrics, label, notes, grp=None):
    out = {}
    for c in cfgs:
        v = vals.get(c)
        if not v:
            continue
        r = {"n": len(v)}
        for m in metrics:
            ids = sorted(i for i in v if m in v[i] and np.isfinite(v[i][m]))
            if not ids:
                continue
            y = np.array([v[i][m] for i in ids])
            if m in (PRIMARY, "NLL", "AUC") and len(y) >= 3:
                s = S.summary(y, seed=S.group_seed(label, ckey(c), m))
                r[m] = {"n": len(y), **{k: float(s[k]) for k in ("est", "ci_low", "ci_high")}}
            else:
                r[m] = {"n": len(y), "est": float(y.mean())}
            if grp is not None and m in (PRIMARY, "NLL", "AUC"):
                gs = defaultdict(list)
                for i in ids:
                    gs[grp(i)].append(v[i][m])
                r[m]["groups"] = {str(g): ({"n": len(x), "est": float(np.mean(x))} if len(x) >= MIN_N else {"n": len(x)}) for g, x in gs.items()}
        out[ckey(c)] = r
    return out


def aggregate_continuous(data):
    notes = list(data["notes"])
    vals = data["vals"]
    fams = continuous_families()
    pairing = Counter(); excluded = []
    for _, _, label, members in fams:
        for m in members:
            why = pair_ok(data, m[1], m[2])
            pairing["matched" if why is None else "excluded"] += 1
            if why is not None:
                excluded.append(f"{label}/{m[0]}: {why}")
    keep = lambda members, label: [m for m in members if pair_ok(data, m[1], m[2]) is None]
    out = {"families": {}, "secondary": {}, "pairing": dict(pairing), "excluded_pairs": excluded}
    for fam, sc, label, members in fams:
        ms = keep(members, label)
        ds = sc.split("|")[0]
        g = (lambda i, ds=ds: data["grp"][(ds, i)]) if fam in ("B-LOCAL", "C-LOCAL") else None
        out["families"][label] = {"family": fam, "scope": sc, **run_family(label, ms, vals, PRIMARY, notes, True, g)}
        out["secondary"][label] = {m: run_family(f"{label}|sec", ms, vals, m, notes, False) for m in DIRECTION if m != PRIMARY}
    cfgs = sorted(vals, key=ckey)
    out["levels"] = levels(vals, cfgs, list(DIRECTION), "levels", notes, None)
    for c in cfgs:
        ds = c[1]
        out["levels"][ckey(c)]["groups_R"] = {}
        gs = defaultdict(list)
        for i, v in vals[c].items():
            if PRIMARY in v:
                gs[data["grp"][(ds, i)]].append(v[PRIMARY])
        out["levels"][ckey(c)]["groups_R"] = {str(g): ({"n": len(x), "est": float(np.mean(x))} if len(x) >= MIN_N else {"n": len(x)}) for g, x in gs.items()}
    out["complement_wording"] = complement_wording(out)
    out["mismatched_only"] = mismatched_only(out)
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}, "units": {ckey(c): len(u) for c, u in data["units"].items()},
                       "identities": {ds: {str(g): n for g, n in Counter(data["grp"][(ds, i)] for i in vals.get(("L", ds, "NCE"), {})).items()} for ds in DS},
                       "n_phantom_entities": data["n_phantom_entities"]}
    out["notes"] = notes
    return out


def complement_wording(out):
    """ADDENDUM_05 §7: 'complement from the pretrained representation' only with C-LOCAL I>0 and both C-ATTRIB init + capacity I>0."""
    init = {"residual_pretrained_full": "init_full", "residual_pretrained_frozen": "init_frozen"}
    cap = {"residual_pretrained_frozen": "capacity_frozen", "residual_pretrained_peft": "capacity_peft", "residual_pretrained_full": "capacity_full"}
    res = {}
    for ds in DS:
        for o in OBJ:
            fl = out["families"].get(f"C-LOCAL|{ds}|{o}", {}).get("members", {})
            for a in ARCH:
                fa = out["families"].get(f"C-ATTRIB|{ds}|{o}|{a}", {}).get("members", {})
                for v in VARIANTS:
                    m = fl.get(f"{a}/{v}")
                    if not m or "class" not in m:
                        continue
                    ci = fa.get(init.get(v, ""), {}).get("class"); cc = fa.get(cap.get(v, ""), {}).get("class")
                    if m["class"] != "I>0":
                        w = "no complement resolved" if m["class"] == "contains 0" else "combined worse than local"
                    elif ci == "I>0" and cc == "I>0":
                        w = "complement from the pretrained representation"
                    else:
                        w = "added branch lowers risk; source (pretraining vs added capacity / structure) not separated"
                    res[f"{ds}|{o}|{a}|{v}"] = {"c_local": m["class"], "init": ci, "capacity": cc, "wording": w}
    return res


def mismatched_only(out):
    res = {}
    for label, f in out["families"].items():
        if f.get("family") != "C-LOCAL":
            continue
        sec = out["secondary"][label]
        for name, m in f["members"].items():
            g = sec["unified/gain_bits"]["members"].get(name, {}); mm = sec["unified/mismatched_eeg/logloss_bits"]["members"].get(name, {})
            if "ci_low" not in g or "class" not in m:
                continue
            flag = g["ci_low"] > 0 and m["class"] != "I>0"
            res[f"{label}|{name}"] = {"dR_class": m["class"], "d_gain": [g["est"], g["ci_low"], g["ci_high"]],
                                      "d_mismatched_logloss": [mm.get("est"), mm.get("ci_low"), mm.get("ci_high")], "mismatched_only": bool(flag)}
    return res


# ------------------------------------------------------------------------------------------------ private
def pcfg_of(r):
    s, f = r["spec"], r["family_id"]
    if r["seed"] != SEED or not f.startswith("E_"):
        return None
    o = s.get("objective")
    if f == "E_LOCAL":
        return ("E_LOCAL", o, s["architecture"], s["window"])
    if f == "E_GX":
        return ("E_GX", o, "GX", s["window"])
    if f == "E_GENERIC":
        return ("E_GENERIC", o, s["architecture"], s["adaptation"])
    if f == "E_PUBLIC_TRANSFER":
        return ("E_PUBLIC_TRANSFER", o, s["source_architecture"], s["adaptation"])
    if f == "E_COMPLEMENT":
        return ("E_COMPLEMENT", o, s["architecture"], s["variant"])
    if f == "E_DISTILL":
        return ("E_DISTILL", o, s["teacher_policy"], s["window"])
    return None


def child_values(ev):
    nc = ev["native_calibration"]["per_participant"]
    out = {}
    for c, v in ev["per_participant"].items():
        d = {"group": v.get("group")}
        pa = (nc.get(c) or {}).get("positive_affine")
        if pa:
            d["NLL"] = float(pa["nll_bits"]); d["AUC"] = float(pa["auc_score"])
        if v.get("hist_gain_bits") is not None:
            d["hist_gain"] = float(v["hist_gain_bits"])
            if v.get("hist_gain_twin_bits") is not None:
                d["twin_sens"] = float(v["hist_gain_bits"] - v["hist_gain_twin_bits"])
        out[c] = d
    return out


def load_private(rows, load):
    vals = defaultdict(dict); grp = {}; status = Counter(); notes = []
    for r in rows:
        c = pcfg_of(r)
        if c is None:
            continue
        rec = load(r["experiment_id"])
        st = "missing" if rec is None else rec.get("status")
        status[(c[0], st)] += 1
        if st != "complete":
            notes.append(f"{c[0]} unit status {st}"); continue
        if c[0] == "E_COMPLEMENT":
            parts = {}
            for ch, v in rec["eval"]["per_participant"].items():
                for side in ("combined", "local_only"):
                    parts.setdefault(side, {})[ch] = {"group": v.get("group"), "NLL": float(v[side]["nll_bits"]), "AUC": float(v[side]["auc"])}
        elif c[0] == "E_DISTILL":
            parts = {"chosen": child_values(rec["eval"]), "lambda0": child_values(rec["baseline_lambda0_eval"])}
        else:
            parts = {"": child_values(rec["eval"])}
        for side, cv in parts.items():
            k = c + ((side,) if side else ())
            for ch, d in cv.items():
                if ch in vals[k]:
                    raise ValueError(f"child appears twice in configuration {ckey(k)}")
                vals[k][ch] = {m: x for m, x in d.items() if m != "group"}
                if d.get("group") is not None:
                    grp[ch] = d["group"]
    return {"vals": dict(vals), "grp": grp, "status": status, "notes": notes}


def private_families():
    fams = []
    for o in OBJ:
        Lr = ("E_LOCAL", o, "lag_local_tokens", "full")
        for a in ARCH:
            fams.append(("PE-GENERIC", f"{o}|{a}", [(ad, ("E_GENERIC", o, a, "random_full"), ("E_GENERIC", o, a, ad),
                                                     "initialization (matched full update)" if ad == "pretrained_full" else "recipe") for ad in PRE]))
            Cx = lambda v, side: ("E_COMPLEMENT", o, a, v, side)
            fams.append(("PE-COMPLEMENT", f"{o}|{a}", [(f"{v}", Cx(v, "local_only"), Cx(v, "combined"), "combined vs local_only (within record)")
                                                        for v in ("residual_pretrained_frozen", "residual_pretrained_peft", "residual_random_trainable")]
                         + [(f"{v}_vs_random_trainable", Cx("residual_random_trainable", "combined"), Cx(v, "combined"), "recipe")
                            for v in ("residual_pretrained_frozen", "residual_pretrained_peft")]))
        tr = [(f"transfer/{src}/{ad}", ("E_PUBLIC_TRANSFER", o, src, ad), "transfer") for src in ("lag_local_tokens",) + ARCH for ad in TRANSFER_AD]
        fams.append(("PE-LOCAL", o, [(f"generic/{a}/{ad}", Lr, ("E_GENERIC", o, a, ad), "vs local") for a in ARCH for ad in ADAPT]
                     + [(n, Lr, c, "vs local") for n, c, _ in tr]))
        fams.append(("PE-TRANSFER", o, [(n, Lr if c[2] == "lag_local_tokens" else ("E_GENERIC", o, c[2], TRANSFER_AD[c[3]]), c, "transfer vs non-transferred twin")
                                        for n, c, _ in tr]))
        fams.append(("PE-DISTILL", o, [(f"{p}/{w}", ("E_DISTILL", o, p, w, "lambda0"), ("E_DISTILL", o, p, w, "chosen"), "chosen lambda vs lambda 0 (within record)")
                                       for p in ("local_teacher", "generic_pretrained_teacher", "auditory_adapted_teacher", "legacy_full_teacher_control")
                                       for w in ("early", "late", "full")]))
    return fams


def aggregate_private(pdata):
    notes = list(pdata["notes"]); vals = pdata["vals"]
    out = {"families": {}, "secondary": {}}
    for fam, sc, members in private_families():
        for m in ("NLL", "AUC"):
            label = f"{fam}|{sc}|{m}"
            out["families"][label] = {"family": fam, "scope": sc, **run_family(label, members, vals, m, notes, True)}
        out["secondary"][f"{fam}|{sc}"] = {m: run_family(f"{fam}|{sc}|sec", members, vals, m, notes, False) for m in ("hist_gain", "twin_sens")}
    cfgs = sorted(vals, key=ckey)
    out["levels"] = levels(vals, cfgs, [m for m, _ in PMETRICS], "plevels", notes, lambda i: pdata["grp"].get(i))
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in pdata["status"].items()},
                       "children_per_config": dict(Counter(len(v) for v in vals.values())),
                       "groups": dict(Counter(pdata["grp"].values()))}
    out["notes"] = [re.sub(r"child\w*", "<child>", n) for n in notes]
    return out


# ------------------------------------------------------------------------------------------------ D status (training side only)
def d_status(rows, out_dir):
    from . import policy as POL
    prog = defaultdict(Counter); cells = {}
    for r in rows:
        if r["family_id"] not in ("D_ADAPT", "D_COVERAGE", "D_ATTENTION") or r["seed"] != SEED:
            continue
        arm = r["spec"].get("architecture")
        p = os.path.join(out_dir, "units", f"{r['experiment_id']}.json")
        done = os.path.exists(p) and json.load(open(p)).get("status") == "complete"
        prog[f"{r['family_id']}|{arm}"]["complete" if done else "not complete"] += 1
        if POL.is_policy_row(r):
            o = r["spec"]["objective"]; o = "NCE" if o == "SELECTION_CE" else o
            cells.setdefault((arm, r["dataset"], r["subject_fold"], r["content_fold"], o), r)
    choice = defaultdict(Counter); unresolved = Counter()
    for (arm, ds, sf, cf, o), r in sorted(cells.items(), key=lambda kv: str(kv[0])):
        pol = POL.resolve(r, rows, out_dir)
        if pol is None:
            unresolved[arm] += 1; continue
        s = pol["chosen_row"]["spec"]
        name = f"{s['architecture']}/{s['adaptation']}/{s['readout']}" if arm == "dense_fm_policy" else f"{s['architecture']}/{s['variant']}"
        choice[f"{arm}|{ds}|{o}"][name] += 1
    return {"progress": {k: dict(v) for k, v in prog.items()}, "choices": {k: dict(v) for k, v in choice.items()},
            "n_cells": dict(Counter(k[0] for k in cells)), "unresolved": dict(unresolved)}


# ------------------------------------------------------------------------------------------------ privacy
def privacy_scan(paths, child_ids):
    bad = []
    pat = re.compile(r"\bchild\d+\b")
    for p in paths:
        txt = open(p).read()
        if pat.search(txt) or any(re.search(rf"\b{re.escape(c)}\b", txt) for c in child_ids):
            bad.append(p)
    return bad


def code_sha():
    here = os.path.dirname(__file__)
    return {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
            for f in ("bc_interim.py", "bc_interim_report.py", "sci_r1/stats.py")}


def write_json(path, obj, private=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(jl(obj), f, indent=1)
    if private:
        os.chmod(path, 0o600)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--skip-private", action="store_true"); a.add_argument("--skip-d", action="store_true")
    args = a.parse_args()
    from auditory_alignment_v3 import run as r3
    from auditory_alignment_v3 import bc_interim_report as REP
    rows = r3.all_rows(); load = unit_loader()
    os.makedirs(os.path.join(PRIV, "agg"), mode=0o700, exist_ok=True); os.makedirs(os.path.join(PRIV, "private"), mode=0o700, exist_ok=True)
    for d in (PRIV, os.path.join(PRIV, "agg"), os.path.join(PRIV, "private")):
        os.chmod(d, 0o700)
    meta = {"addendum": "ADDENDUM_05_BC_INTERIM_AGGREGATION.md", "seed": SEED, "code_sha256": code_sha(), "n_boot": S.NB}
    data = load_continuous(rows, load, load_manifest())
    write_json(os.path.join(PRIV, "agg", "per_identity_continuous.json"), {ckey(c): v for c, v in data["vals"].items()}, private=True)
    cont = aggregate_continuous(data)
    dst = d_status(rows, core.OUT) if not args.skip_d else None
    write_json(os.path.join(RES, "continuous.json"), {"meta": meta, **cont, "d_status": dst})
    public = REP.write_continuous(cont, dst, meta, DOCS)
    child_ids = set()
    if not args.skip_private:
        pdata = load_private(rows, load)
        child_ids = {c for v in pdata["vals"].values() for c in v}
        priv = aggregate_private(pdata)
        write_json(os.path.join(PRIV, "private", "private_e.json"), {"meta": meta, **priv}, private=True)
        pm = REP.write_private(priv, meta, os.path.join(PRIV, "private"))
        os.chmod(pm, 0o600)
    bad = privacy_scan([os.path.join(RES, "continuous.json")] + public, child_ids)
    print("privacy scan (public outputs):", "PASS" if not bad else f"FAIL {bad}")
    print("pairing:", cont["pairing"], "excluded:", len(cont["excluded_pairs"]))
    print("coverage:", json.dumps(cont["coverage"]["status"]), "| identities:", json.dumps(cont["coverage"]["identities"]))
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
