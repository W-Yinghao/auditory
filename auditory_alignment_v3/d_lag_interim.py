"""ALN3 ADDENDUM_12: results of the completed D lag-arm families (D_ATTENTION, D_ADAPT, D_COVERAGE; seed 3401, lag_local_tokens).
Identity-level paired contrasts with the ADDENDUM_05 machinery (bc_interim.run_family; bootstrap-t; max-t within families).
Pseudo-configurations: ATT (dataset, task, objective, integrator, window), AD (dataset, objective, adapter, support),
CV (dataset, objective, population, control); CHANCE = 0.5 for the attention level family.
Usage: python -m auditory_alignment_v3.d_lag_interim"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core

RES = os.environ.get("DL_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "d_lag"))
DOCS = os.environ.get("DL_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
PRIVD = os.path.join(core.OUT, "d_lag")
WINS = (5, 10, 20)
TASKS = [("attended_alignment", "NCE"), ("attended_alignment", "CS_SINGLE"), ("selection_only", "SELECTION_CE"),
         ("alignment_plus_selection", "NCE"), ("alignment_plus_selection", "CS_SINGLE")]
ADAPTERS = ("none", "input_spatial", "output_low_rank"); SUPPORTS = ("0.1", "0.3")
POPS = ("TH_ONLY", "TH_HA", "TH_HA_CI"); CTRLS = ("full_available", "matched_exposure")
NEW_DIR = {"acc": "higher", "acc_native": "higher", "margin": "higher", "gain_bits": "higher", "rank_pct_q": "lower", "top1_q": "higher",
           "gain_bits_native": "higher"}


def collect(rows, load):
    vals = defaultdict(lambda: defaultdict(lambda: defaultdict(list))); grp = {}; status = defaultdict(int)
    cv_rows, cv_recs = [], {}
    for r in rows:
        s = r["spec"]
        if r["seed"] != BI.SEED or s.get("architecture") != "lag_local_tokens" or r["family_id"] not in ("D_ATTENTION", "D_ADAPT", "D_COVERAGE"):
            continue
        if r["family_id"] == "D_ATTENTION" and s.get("integrator") != "mean_score":
            continue
        rec = load(r["experiment_id"]); st = "missing" if rec is None else rec.get("status"); status[(r["family_id"], st)] += 1
        if st != "complete":
            continue
        ds = r["dataset"]
        if r["family_id"] == "D_ATTENTION":
            for pid, v in rec["eval"]["attention_windows"]["per_participant"].items():
                grp[(ds, pid)] = v.get("group")
                for w in WINS:
                    for rd in ("unified", "native"):
                        x = v.get(f"{w}s|{rd}")
                        if not x or not x.get("n_windows"):
                            continue
                        for integ, key in (("ms", "mean_score_accuracy"), ("lt", "learned_temporal_accuracy")):
                            c = ("ATT", ds, s["training_task"], s["objective"], integ, w)
                            vals[c][pid]["acc" if rd == "unified" else "acc_native"].append(float(x[key]))
                            if rd == "unified" and integ == "ms":
                                vals[c][pid]["margin"].append(float(x["mean_margin"]))
        elif r["family_id"] == "D_ADAPT":
            for pid, v in rec["eval"]["per_participant"].items():
                grp[(ds, pid)] = v.get("group")
                for sf in SUPPORTS:
                    x = v.get(f"support_{sf}")
                    if not x:
                        continue
                    c = ("AD", ds, s["objective"], s["adapter"], sf)
                    vals[c][pid]["gain_bits"].append(float(x["unified"]["gain_bits"])); vals[c][pid]["rank_pct_q"].append(float(x["unified"]["rank_pct"]))
                    vals[c][pid]["top1_q"].append(float(x["unified"]["top1"])); vals[c][pid]["gain_bits_native"].append(float(x["native"]["gain_bits"]))
        else:
            for ctrl in CTRLS:
                e = f"{r['experiment_id']}|{ctrl}"
                cv_rows.append({**r, "experiment_id": e, "family_id": "D_COVERAGE_CTRL", "spec": {**s, "control": ctrl}})
                cv_recs[e] = {"status": "complete", "eval": rec["fits"][ctrl]["eval"]}
    out = {c: {i: {m: float(np.mean(x)) for m, x in d.items()} for i, d in per.items()} for c, per in vals.items()}
    for c in [c for c in out if c[0] == "ATT"]:  # chance reference for AT-LEVEL
        out[("CHANCE",) + c[1:]] = {i: {"acc": 0.5, "acc_native": 0.5} for i in out[c]}
    return out, grp, dict(status), cv_rows, cv_recs.get


def att_families():
    out = []
    for ds in ("fau", "dtu"):
        for t, o in TASKS:
            out.append(("AT-LEVEL", f"{ds}|{t}|{o}", f"AT-LEVEL|{ds}|{t}|{o}", [(f"{w}s", ("CHANCE", ds, t, o, "ms", w), ("ATT", ds, t, o, "ms", w), "above chance") for w in WINS]))
            out.append(("AT-INTEGRATOR", f"{ds}|{t}|{o}", f"AT-INTEGRATOR|{ds}|{t}|{o}", [(f"{w}s", ("ATT", ds, t, o, "ms", w), ("ATT", ds, t, o, "lt", w), "mean_score -> learned_temporal") for w in WINS]))
            out.append(("AT-LENGTH", f"{ds}|{t}|{o}", f"AT-LENGTH|{ds}|{t}|{o}", [(f"5s->{w}s", ("ATT", ds, t, o, "ms", 5), ("ATT", ds, t, o, "ms", w), "longer window") for w in (10, 20)]))
        for w in WINS:
            A = lambda t, o: ("ATT", ds, t, o, "ms", w)
            out.append(("AT-TASK", f"{ds}|{w}s", f"AT-TASK|{ds}|{w}s", [("align->align+sel NCE", A("attended_alignment", "NCE"), A("alignment_plus_selection", "NCE"), "task"),
                                                                        ("align->align+sel CS", A("attended_alignment", "CS_SINGLE"), A("alignment_plus_selection", "CS_SINGLE"), "task"),
                                                                        ("align NCE->selection_only", A("attended_alignment", "NCE"), A("selection_only", "SELECTION_CE"), "task")]))
    return out


def ad_families():
    out = []
    for ds in ("fau", "dtu"):
        for o in ("NCE", "CS_SINGLE"):
            for sf in SUPPORTS:
                out.append(("AD-GAIN", f"{ds}|{o}|support{sf}", f"AD-GAIN|{ds}|{o}|{sf}", [(a, ("AD", ds, o, "none", sf), ("AD", ds, o, a, sf), "personal supervised adaptation") for a in ADAPTERS[1:]]))
            out.append(("AD-SUPPORT", f"{ds}|{o}", f"AD-SUPPORT|{ds}|{o}", [(a, ("AD", ds, o, a, "0.1"), ("AD", ds, o, a, "0.3"), "support 0.1 -> 0.3") for a in ADAPTERS[1:]]))
    return out


def cv_cfg(r):
    s = r["spec"]
    return ("CV", r["dataset"], s["objective"], s["population"], s["control"]) if r["family_id"] == "D_COVERAGE_CTRL" else None


def cv_families():
    out = []
    for o in ("NCE", "CS_SINGLE"):
        for c in CTRLS:
            V = lambda p: ("CV", "fau", o, p, c)
            out.append(("CV-POP", f"fau|{o}|{c}", f"CV-POP|{o}|{c}", [("TH_ONLY->TH_HA", V("TH_ONLY"), V("TH_HA"), "add HA"), ("TH_HA->TH_HA_CI", V("TH_HA"), V("TH_HA_CI"), "add CI"),
                                                                    ("TH_ONLY->TH_HA_CI", V("TH_ONLY"), V("TH_HA_CI"), "add HA and CI")]))
        out.append(("CV-BUDGET", f"fau|{o}", f"CV-BUDGET|{o}", [(p, ("CV", "fau", o, p, "full_available"), ("CV", "fau", o, p, "matched_exposure"), "full -> matched exposure") for p in POPS]))
    return out


def run_fams(fams, vals, grp, metrics, primary, notes):
    out = {"families": {}, "secondary": {}}
    for fam, sc, label, members in fams:
        ds = sc.split("|")[0]
        g = lambda i, ds=ds: grp.get((ds, i))
        out["families"][label] = {"family": fam, "scope": sc, **BI.run_family(label, members, vals, primary, notes, True, g)}
        out["secondary"][label] = {m: BI.run_family(f"{label}|sec", members, vals, m, notes, False) for m in metrics if m != primary}
    return out


def render(title, intro, res, sec_cols, path, extra=None):
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    iv = lambda m, lo="ci_low", hi="ci_high": "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"
    L = [f"# {title}", "", intro, ""] + (extra or [])
    for label, f in res["families"].items():
        if not f["members"]:
            continue
        L += [f"**{label.replace('|', ' · ')}** (critical value {f.get('crit', float('nan')):.2f})", "",
              "| member | label | n | Δ | 95% CI | 95% simultaneous | class | " + " | ".join(s for _, s in sec_cols) + " | per group |", "|---|---|---|---|---|---|---|" + "---|" * len(sec_cols) + "---|"]
        for name, m in f["members"].items():
            gs = "; ".join(f"{g}: " + (f"{x['est']:+.3f} (n={x['n']})" if "est" in x else f"n={x['n']}") for g, x in sorted(m.get("groups", {}).items()))
            L.append(f"| {name} | {m['tag']} | {m['n']} | {f3(m.get('est'))} | {iv(m)} | {iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | "
                     + " | ".join(f3(res["secondary"][label][k]["members"].get(name, {}).get("est")) for k, _ in sec_cols) + f" | {gs} |")
        L.append("")
    open(path, "w").write("\n".join(L))
    return path


def main():
    from auditory_alignment_v3 import run as r3
    rows = r3.all_rows(); load = BI.unit_loader()
    BI.PDIR.update(NEW_DIR)  # directions of the D endpoints (positive = better), this process only
    vals, grp, status, cv_rows, cv_load = collect(rows, load)
    notes = []
    att = run_fams(att_families(), vals, grp, ("acc", "acc_native", "margin"), "acc", notes)
    ad = run_fams(ad_families(), vals, grp, ("gain_bits", "rank_pct_q", "top1_q", "gain_bits_native"), "gain_bits", notes)
    BI.cfg_of = cv_cfg
    cvd = BI.load_continuous(cv_rows, cv_load, BI.load_manifest())
    cv = run_fams(cv_families(), cvd["vals"], cvd["grp"], list(BI.DIRECTION), BI.PRIMARY, notes)
    lv = BI.levels(cvd["vals"], sorted(cvd["vals"], key=BI.ckey), list(BI.DIRECTION), "cv-levels", notes, lambda i: cvd["grp"][("fau", i)])
    qc = {"adapter_none_identical_across_support": all(abs(vals[("AD", ds, o, "none", "0.1")][i]["gain_bits"] - vals[("AD", ds, o, "none", "0.3")][i]["gain_bits"]) < 1e-9
                                                      for ds in ("fau", "dtu") for o in ("NCE", "CS_SINGLE") for i in vals.get(("AD", ds, o, "none", "0.1"), {})
                                                      if i in vals.get(("AD", ds, o, "none", "0.3"), {}))}
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_12_D_LAG_RESULTS.md", "status": {f"{k[0]}|{k[1]}": v for k, v in status.items()}, "qc": qc,
            "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest() for f in ("d_lag_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    os.makedirs(RES, exist_ok=True)
    BI.write_json(os.path.join(RES, "d_lag.json"), {"meta": meta, "attention": att, "adapt": ad, "coverage": cv, "coverage_levels": lv, "notes": notes})
    os.makedirs(PRIVD, mode=0o700, exist_ok=True)
    BI.write_json(os.path.join(PRIVD, "per_identity.json"), {BI.ckey(c): v for c, v in vals.items()}, private=True)
    job = os.environ.get("SLURM_JOB_ID", "local"); when = time.strftime("%Y-%m-%d %H:%M %Z")
    head = (f"Generated {when} (Slurm job {job}) by `python -m auditory_alignment_v3.d_lag_interim` under the frozen `ADDENDUM_12_D_LAG_RESULTS.md`. Seed 3401, "
            "`lag_local_tokens`, all folds; identity-level bootstrap-t, simultaneous = max-t within the named family; positive = candidate better. "
            f"Unit status: {meta['status']}. QC: {qc}.")
    p1 = render("D_ATTENTION results — attended vs ignored 2AFC (lag-local arm)", head + " Primary: unified readout, mean_score integrator; chance 0.5.", att,
                (("acc_native", "Δacc native"), ("margin", "Δmargin")), os.path.join(DOCS, "D_ATTENTION_RESULTS.md"))
    p2 = render("D_ADAPT results — personal supervised adaptation (lag-local arm)", head + " Primary: unified gain_bits on the fixed query set (last 70 %); "
                "support blocks use known-stimulus supervision (not label-free TTA); same session.", ad,
                (("rank_pct_q", "Δrank% (lower better)"), ("top1_q", "Δtop1"), ("gain_bits_native", "Δgain native")), os.path.join(DOCS, "D_ADAPT_RESULTS.md"))
    ex = ["## Levels: training population × control × test group (R, bits; lower is better)", "", "| configuration | n | R [95% CI] | per test group (mean R) |", "|---|---|---|---|"]
    for k, r in lv.items():
        R = r.get(BI.PRIMARY, {}); gs = "; ".join(f"{g}: " + (f"{x['est']:.3f} (n={x['n']})" if "est" in x else f"n={x['n']}") for g, x in sorted(R.get("groups", {}).items()))
        ex.append(f"| {k} | {r['n']} | {R.get('est', float('nan')):.3f} [{R.get('ci_low', float('nan')):.3f}, {R.get('ci_high', float('nan')):.3f}] | {gs} |")
    ex.append("")
    p3 = render("D_COVERAGE matrix — training population and sampling budget (FAU, lag-local arm)", head + " Primary: unified true-query risk R (positive Δ = lower risk); "
                "matched_exposure separates the population change from the update count.", cv, (("unified/gain_bits", "Δgain"), ("unified/regular/top1", "Δtop1")),
                os.path.join(DOCS, "D_COVERAGE_MATRIX.md"), ex)
    bad = BI.privacy_scan([os.path.join(RES, "d_lag.json"), p1, p2, p3], set())
    print("privacy scan:", "PASS" if not bad else bad, "| status", meta["status"], "| qc", qc)
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
