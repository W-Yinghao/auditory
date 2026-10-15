"""ALN3 ADDENDUM_11 §3: paired seed panel (seeds 3401, 3407, 3413) of the ALN3.2 core roles, ADDENDUM_05 machinery.
Per role x dataset: per-seed contrasts (members over backbone / lr), and the three-seed contrast on identity values averaged over
the seeds (only where reference and candidate are complete for all three seeds; otherwise the available seeds are listed).
Usage: python -m auditory_alignment_v3.aln32_panel_interim"""
from __future__ import annotations

import hashlib
import os
import time

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core

RES = os.environ.get("PN_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln32_panel"))
DOCS = os.environ.get("PN_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
SEEDS = (3401, 3407, 3413); LRS = (1e-5, 3e-4)


def cfg(r):
    s, f, ds, sd = r["spec"], r["family_id"], r["dataset"], r["seed"]
    if sd not in SEEDS or ds not in BI.DS or s.get("objective") != "NCE":
        return None
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L0", ds, sd)
    if f == "ALN32_LOCAL_SUPPORT" and s["variant"] == "local_aligned1000":
        return ("L1", ds, sd)
    if f == "B_ALIGNED" and s["adaptation"] in ("pretrained_frozen", "pretrained_peft"):
        return ("A", ds, s["architecture"], s["adaptation"], sd)
    if f == "ALN32_TRUE_FULL" and s["recipe"] == "full_onestep_v1":
        return ("T", ds, s["architecture"], s["adaptation"], float(s["lr_backbone"]), sd)
    if f == "ALN32_RESIDUAL":
        return ("RS", ds, s["architecture"], s["variant"], sd)
    return None


def roles(ds, sd):
    R = []
    for a in BI.ARCH:
        R.append(("aligned_access_matched", f"{a}", ("L1", ds, sd), ("A", ds, a, "pretrained_frozen", sd)))
        R.append(("adaptation", f"{a}", ("A", ds, a, "pretrained_frozen", sd), ("A", ds, a, "pretrained_peft", sd)))
        for lr in LRS:
            R.append(("initialization_true_full", f"{a}/lr{lr:g}", ("T", ds, a, "random_full", lr, sd), ("T", ds, a, "pretrained_full", lr, sd)))
        P = ("RS", ds, a, "residual_aligned_pretrained", sd)
        R.append(("complement_source", f"{a}", ("RS", ds, a, "residual_aligned_random", sd), P))
        R.append(("complement_value", f"{a}", ("L0", ds, sd), P))
        R.append(("capacity", f"{a}", ("RS", ds, "small_capacity_branch", "residual_small_capacity", sd), P))
    return R


def three_seed(vals, keyf):
    """identity values averaged over the three seeds (identities present in all three)."""
    per = [vals.get(keyf(sd), {}) for sd in SEEDS]
    if not all(per):
        return None
    ids = set(per[0]).intersection(*per[1:])
    return {i: {m: float(np.mean([p[i][m] for p in per])) for m in per[0][i] if all(m in p[i] for p in per)} for i in ids}


def aggregate(data):
    notes = list(data["notes"]); vals = data["vals"]; out = {"per_seed": {}, "three_seed": {}, "availability": {}}
    for ds in BI.DS:
        for sd in SEEDS:
            fams = {}
            for role, name, ref, cand in roles(ds, sd):
                fams.setdefault(role, []).append((name, ref, cand, role))
            for role, members in fams.items():
                keep = [m for m in members if BI.pair_ok(data, m[1], m[2]) is None]
                for m in members:
                    out["availability"][f"{ds}|{sd}|{role}|{m[0]}"] = m in keep
                if keep:
                    out["per_seed"][f"{role}|{ds}|{sd}"] = BI.run_family(f"PN|{role}|{ds}|{sd}", keep, vals, BI.PRIMARY, notes, True)
        # three-seed: pseudo-configs with seed 0 holding the seed-mean identity values
        v3 = dict(vals); fams = {}
        for role, name, ref, cand in roles(ds, 0):
            ok = True
            for c in (ref, cand):
                key = c[:-1]
                m = three_seed(vals, lambda sd, key=key: key + (sd,))
                if m is None:
                    ok = False; break
                v3[c] = m
            out["availability"][f"{ds}|3seed|{role}|{name}"] = ok
            if ok:
                fams.setdefault(role, []).append((name, ref, cand, role))
        for role, members in fams.items():
            out["three_seed"][f"{role}|{ds}"] = BI.run_family(f"PN3|{role}|{ds}", members, v3, BI.PRIMARY, notes, True)
    out["notes"] = notes
    return out


def report(out, meta, path):
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    L = ["# ALN3.2 paired seed panel (seeds 3401, 3407, 3413)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.aln32_panel_interim` under the frozen "
         "`ADDENDUM_11_ALN32_SEED_PANEL.md`. ΔR = R(reference) − R(candidate), positive = candidate lower true-query risk; per-seed families and the three-seed "
         "family (identity values averaged over seeds) each with max-t simultaneous intervals. Seed SD mixes training and readout-sampling variation.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + ".", "",
         "| role · dataset · member | seed 3401 | seed 3407 | seed 3413 | per-seed mean / range | three-seed ΔR [simultaneous] |", "|---|---|---|---|---|---|"]
    keys = sorted({k.rsplit("|", 2)[0] + "|" + k.rsplit("|", 2)[1] for k in out["per_seed"]} | set(out["three_seed"]))
    for rk in keys:
        role, ds = rk.split("|")
        names = set()
        for sd in SEEDS:
            names |= set(out["per_seed"].get(f"{role}|{ds}|{sd}", {}).get("members", {}))
        names |= set(out["three_seed"].get(rk, {}).get("members", {}))
        for n in sorted(names):
            ests = [out["per_seed"].get(f"{role}|{ds}|{sd}", {}).get("members", {}).get(n, {}).get("est") for sd in SEEDS]
            have = [e for e in ests if e is not None]
            t3 = out["three_seed"].get(rk, {}).get("members", {}).get(n, {})
            L.append(f"| {role} · {ds} · {n} | " + " | ".join(f3(e) for e in ests) + " | " + (f"{np.mean(have):+.3f} / [{min(have):+.3f}, {max(have):+.3f}]" if have else "–") + " | "
                     + (f"{t3['est']:+.3f} [{t3['sim_low']:+.3f}, {t3['sim_high']:+.3f}] {t3.get('class', '')}" if "sim_low" in t3 else "incomplete") + " |")
    L.append("")
    open(path, "w").write("\n".join(L))
    return path


def main():
    from auditory_alignment_v3 import run as r3
    BI.cfg_of = cfg
    rows = r3.all_rows(); data = BI.load_continuous(rows, BI.unit_loader(), BI.load_manifest())
    out = aggregate(data)
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_11_ALN32_SEED_PANEL.md", "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
                                                                         for f in ("aln32_panel_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    BI.write_json(os.path.join(RES, "aln32_panel.json"), {"meta": meta, **out})
    p = report(out, meta, os.path.join(DOCS, "ALN32_SEED_PANEL_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "aln32_panel.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad)
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
