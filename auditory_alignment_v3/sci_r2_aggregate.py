"""SCI_R2 aggregation (SCI_R2_PREREG §6): task outputs -> identity values (mean over units; Federici records -> subject_uid, phantom
excluded) -> bootstrap-t (sci_r1.stats): Q1 levels and nested increments (family max-t per cohort), Q2 / Q3 lag curves (max-t bands),
group levels and independent-group contrasts. Writes results/auditory_alignment_v3/sci_r2/ + docs/.../SCI_R2_RESULTS.md.
Usage: python -m auditory_alignment_v3.sci_r2_aggregate"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core
from auditory_alignment_v3 import sci_r2 as R2
from auditory_alignment_v3.sci_r1 import stats as S

RES = os.environ.get("R2_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "sci_r2"))
DOCS = os.environ.get("R2_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
CONTRASTS = {"fau": [("ha", "th"), ("ci", "th"), ("ci", "ha")], "dtu": [("hi", "nh")], "federici": [("CI", "HC"), ("HC-v", "HC")]}
MIN_N = 5


def identities(tasks, manifest):
    """-> {ds: {identity: {"group": g, key: [values over units]}}}"""
    out = defaultdict(lambda: defaultdict(lambda: defaultdict(list))); grp = {}; phantom = defaultdict(set)
    for t in tasks:
        ds = t["dataset"]
        for j, pid in enumerate(t["test_ids"]):
            g = t["test_groups"][j]
            if ds == "federici":
                ident, g, kind = manifest[pid]
                if kind != "human":
                    phantom[ds].add(ident); continue
            else:
                ident = pid
            grp[(ds, ident)] = g
            for m, v in t["q1"].items():
                out[ds][ident][f"q1|{m}"].append(v["r"][j])
            for key in ("q2", "q3"):
                if t[key]:
                    out[ds][ident][key].append([t[key][str(L)]["r"][j] for L in R2.LAG_GRID_MS])
    vals = {ds: {i: {k: np.mean(np.asarray(v, float), 0) for k, v in d.items()} for i, d in per.items()} for ds, per in out.items()}
    return vals, grp, {k: len(v) for k, v in phantom.items()}


def summ(Y, seed):
    s = S.summary(np.asarray(Y, float), seed=seed)
    return {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in s.items() if k != "T"}


def aggregate(vals, grp):
    res = {}
    for ds, per in vals.items():
        ids = sorted(per); groups = sorted({grp[(ds, i)] for i in ids})
        r = {"n": len(ids), "groups": {g: sum(grp[(ds, i)] == g for i in ids) for g in groups}, "q1_levels": {}, "q1_increments": {}, "q1_group": {}, "q2": {}, "q3": {}}
        models = [m for m in R2.MODELS if all(f"q1|{m}" in per[i] for i in ids)]
        for m in models:
            r["q1_levels"][m] = summ([per[i][f"q1|{m}"] for i in ids], S.group_seed(ds, "q1", m))
        inc = [(models[k - 1], models[k]) for k in range(1, len(models))]
        if inc:
            idx = S.draws(len(ids), S.NB, S.group_seed(ds, "q1inc")); items = {}
            for a, b in inc:
                d = np.array([per[i][f"q1|{b}"] - per[i][f"q1|{a}"] for i in ids]); s = S.summary(d, idx=idx)
                r["q1_increments"][f"{a}->{b}"] = {k: float(s[k]) for k in ("est", "se", "ci_low", "ci_high")}; items[f"{a}->{b}"] = (s["est"], s["se"], s["T"])
            fm = S.family_maxt(items)
            for k, iv in fm["intervals"].items():
                r["q1_increments"][k].update({"sim_low": iv["sim_low"], "sim_high": iv["sim_high"]})
        for key in ("q2", "q3"):
            have = [i for i in ids if key in per[i]]
            if len(have) >= 3:
                r[key]["all"] = summ([per[i][key] for i in have], S.group_seed(ds, key))
                for g in groups:
                    gi = [i for i in have if grp[(ds, i)] == g]
                    r[key][g] = summ([per[i][key] for i in gi], S.group_seed(ds, key, g)) if len(gi) >= MIN_N else {"n": len(gi)}
        if r["q3"]:
            have = [i for i in ids if "q3" in per[i]]
            r["q3_minus_q2"] = summ([per[i]["q3"] - per[i]["q2"] for i in have], S.group_seed(ds, "q3-q2"))
        for g in groups:
            gi = [i for i in ids if grp[(ds, i)] == g]
            r["q1_group"][g] = {m: (summ([per[i][f"q1|{m}"] for i in gi], S.group_seed(ds, g, m)) if len(gi) >= MIN_N else {"n": len(gi)}) for m in models}
        r["contrasts"] = {}
        for a, b in CONTRASTS.get(ds, []):
            A = [i for i in ids if grp[(ds, i)] == a]; Bn = [i for i in ids if grp[(ds, i)] == b]
            if len(A) < MIN_N or len(Bn) < MIN_N:
                r["contrasts"][f"{a}-{b}"] = {"n": [len(A), len(Bn)]}; continue
            c = {}
            for m in models[:1]:
                c[f"q1|{m}"] = {k: float(v) for k, v in S.contrast(np.array([per[i][f"q1|{m}"] for i in A]), np.array([per[i][f"q1|{m}"] for i in Bn]), seed=S.group_seed(ds, a, b, m)).items() if k in ("est", "ci_low", "ci_high")}
            for x, y in inc:
                d = lambda L: np.array([per[i][f"q1|{y}"] - per[i][f"q1|{x}"] for i in L])
                c[f"q1|{x}->{y}"] = {k: float(v) for k, v in S.contrast(d(A), d(Bn), seed=S.group_seed(ds, a, b, x, y)).items() if k in ("est", "ci_low", "ci_high")}
            cv = S.contrast(np.array([per[i]["q2"] for i in A]), np.array([per[i]["q2"] for i in Bn]), seed=S.group_seed(ds, a, b, "q2"))
            c["q2_curve"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in cv.items() if k in ("est", "band_low", "band_high", "crit")}
            r["contrasts"][f"{a}-{b}"] = c
        res[ds] = r
    return res


def report(res, meta, path):
    f3 = lambda x: f"{x:+.4f}"
    L = ["# SCI_R2 results — nested forward models (S2) and the common time panel", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.sci_r2_aggregate` under the frozen "
         "`SCI_R2_PREREG.md`. Identity-level bootstrap-t (4,000 replicates), conditional on the fitted models; curves with max-t bands; increments with family max-t "
         "within a cohort. Q1 r = mean over channels of the held-out Pearson r of the forward prediction of EEG. Q2 r = Pearson r of the envelope read from a "
         "40 ms raw-EEG window at lag L (negative lags are controls). Ac / Lz are contextual (Whisper) feature increments, not a language claim; F0 / voicing pending.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + f". Tasks: {meta['n_tasks']}. Federici phantom entities excluded: {meta['phantom']}.", ""]
    for ds, r in res.items():
        L += [f"## {ds} (n = {r['n']}; groups {r['groups']})", "", "### Q1 levels and nested increments", "", "| model / increment | estimate | 95% CI | 95% simultaneous |", "|---|---|---|---|"]
        for m, s in r["q1_levels"].items():
            L.append(f"| {m} | {f3(s['est'])} | [{f3(s['ci_low'])}, {f3(s['ci_high'])}] | – |")
        for k, s in r["q1_increments"].items():
            L.append(f"| Δ {k} | {f3(s['est'])} | [{f3(s['ci_low'])}, {f3(s['ci_high'])}] | [{f3(s['sim_low'])}, {f3(s['sim_high'])}] |")
        L += ["", "Per group (Q1 levels, estimate [95% CI]):", "", "| group | " + " | ".join(r["q1_levels"]) + " |", "|---|" + "---|" * len(r["q1_levels"])]
        for g, d in r["q1_group"].items():
            L.append(f"| {g} | " + " | ".join((f"{f3(s['est'])} [{f3(s['ci_low'])}, {f3(s['ci_high'])}]" if "est" in s else f"n={s['n']}") for s in d.values()) + " |")
        for key, title in (("q2", "Q2 common time panel (1–20 Hz EEG)"), ("q3", "Q3 band-matched 2–8 Hz EEG")):
            if not r[key]:
                continue
            L += ["", f"### {title}: r by lag (estimate; max-t band over lags)", "", "| lag (ms) | all | " + " | ".join(g for g in r[key] if g != "all") + " |",
                  "|---|---|" + "---|" * (len(r[key]) - 1)]
            for j, lag in enumerate(R2.LAG_GRID_MS):
                a = r[key]["all"]
                cells = [f"{a['est'][j]:+.3f} [{a['band_low'][j]:+.3f}, {a['band_high'][j]:+.3f}]"]
                for g, s in r[key].items():
                    if g == "all":
                        continue
                    cells.append(f"{s['est'][j]:+.3f}" if "est" in s else f"n={s['n']}")
                L.append(f"| {lag} | " + " | ".join(cells) + " |")
        if r.get("q3_minus_q2"):
            d = r["q3_minus_q2"]
            L += ["", "Q3 − Q2 (band-matched minus primary), estimate [max-t band] at selected lags: " + "; ".join(
                f"{lag} ms {d['est'][j]:+.3f} [{d['band_low'][j]:+.3f}, {d['band_high'][j]:+.3f}]" for j, lag in enumerate(R2.LAG_GRID_MS) if lag in (-100, 0, 100, 200, 300, 400))]
        if r["contrasts"]:
            L += ["", "### Group contrasts (independent groups; pointwise for Q1, max-t band for the Q2 curve)", ""]
            for c, d in r["contrasts"].items():
                if "n" in d:
                    L.append(f"- {c}: n = {d['n']} (a group has n < 5)"); continue
                parts = [f"{k}: {v['est']:+.4f} [{v['ci_low']:+.4f}, {v['ci_high']:+.4f}]" for k, v in d.items() if k != "q2_curve"]
                qc = d["q2_curve"]; outside = [lag for j, lag in enumerate(R2.LAG_GRID_MS) if qc["band_low"][j] > 0 or qc["band_high"][j] < 0]
                L.append(f"- {c}: " + "; ".join(parts) + f"; Q2 curve band excludes 0 at lags {outside if outside else 'none'} ms")
        L.append("")
    open(path, "w").write("\n".join(L))
    return path


def main():
    tasks = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(R2.OUT, "tasks", "*.json")))]
    vals, grp, phantom = identities(tasks, BI.load_manifest())
    res = aggregate(vals, grp)
    here = os.path.dirname(__file__)
    meta = {"prereg": "SCI_R2_PREREG.md", "n_tasks": len(tasks), "phantom": phantom,
            "code_sha256": {f: hashlib.sha256(open(os.path.join(here, f), "rb").read()).hexdigest() for f in ("sci_r2.py", "sci_r2_aggregate.py")}}
    BI.write_json(os.path.join(RES, "sci_r2.json"), {"meta": meta, **res})
    os.makedirs(os.path.join(R2.OUT, "agg"), mode=0o700, exist_ok=True)
    BI.write_json(os.path.join(R2.OUT, "agg", "per_identity.json"), {ds: {i: {k: np.asarray(v).tolist() for k, v in d.items()} for i, d in per.items()} for ds, per in vals.items()}, private=True)
    p = report(res, meta, os.path.join(DOCS, "SCI_R2_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "sci_r2.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad, "| tasks", len(tasks))
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
