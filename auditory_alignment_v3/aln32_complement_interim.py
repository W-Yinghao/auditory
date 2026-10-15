"""ALN3 ADDENDUM_09 §5: ALN32_SIMPLE_COMPLEMENT analysis (seed 3401, NCE) with the ADDENDUM_05 machinery. Each unit's six variant
evaluations become pseudo-units ("<id>|<variant>"). Families per dataset x backbone x base:
  SC-VALUE   local_only -> each other variant
  SC-ATTRIB  aligned_random -> aligned_pretrained; local_refit_capacity -> aligned_pretrained; small_context -> aligned_pretrained;
             concat -> aligned_pretrained
Wording rule (ADDENDUM_09 §5): "complement from the pretrained representation" only with SC-VALUE aligned_pretrained I>0 and both
pretrained-vs-random and pretrained-vs-capacity I>0; base L0 results are "context-assisted".
Usage: python -m auditory_alignment_v3.aln32_complement_interim"""
from __future__ import annotations

import hashlib
import os
import time

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import complement32 as C32
from auditory_alignment_v3 import core

RES = os.environ.get("SC_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln32_complement"))
DOCS = os.environ.get("SC_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
SEC = (("unified/regular/top1", "Δtop1"), ("unified/gain_bits", "Δgain"), ("native/regular/logloss_bits", "ΔR_native"), ("attention/unified/accuracy", "Δatt"))


def expand(rows, load):
    prow, precs = [], {}
    for r in rows:
        if r["family_id"] != "ALN32_SIMPLE_COMPLEMENT" or r["seed"] != BI.SEED:
            continue
        rec = load(r["experiment_id"])
        for v in C32.VARIANTS:
            e = f"{r['experiment_id']}|{v}"
            prow.append({**r, "experiment_id": e, "spec": {**r["spec"], "variant": v}})
            if rec is not None:
                precs[e] = {"status": rec.get("status"), "eval": (rec.get("eval_variants") or {}).get(v)} if rec.get("status") == "complete" else {"status": rec.get("status")}
    return prow, precs.get


def cfg(r):
    s = r["spec"]
    if r["family_id"] != "ALN32_SIMPLE_COMPLEMENT" or r["dataset"] not in BI.DS:
        return None
    return ("SC", r["dataset"], "NCE", s["architecture"], s["base"], s["variant"])


def families():
    out = []
    for ds in BI.DS:
        for a in BI.ARCH:
            for base in ("L0", "L1"):
                V = lambda v: ("SC", ds, "NCE", a, base, v)
                sc = f"{ds}|{a}|{base}"
                out.append(("SC-VALUE", sc, f"SC-VALUE|{sc}", [(v, V("local_only"), V(v), "vs local_only" + (" (context-assisted)" if base == "L0" else " (access-matched)"))
                                                              for v in C32.VARIANTS[1:]]))
                out.append(("SC-ATTRIB", sc, f"SC-ATTRIB|{sc}", [("pretrained_vs_random", V("aligned_random"), V("aligned_pretrained"), "pretrained weights"),
                                                                ("pretrained_vs_capacity", V("local_refit_capacity"), V("aligned_pretrained"), "capacity"),
                                                                ("pretrained_vs_raw_window", V("small_context"), V("aligned_pretrained"), "beyond the raw window"),
                                                                ("residual_vs_concat", V("concat"), V("aligned_pretrained"), "residual stacking vs joint fit")]))
    return out


def aggregate(data):
    notes = list(data["notes"]); vals = data["vals"]
    out = {"families": {}, "secondary": {}, "excluded_pairs": [], "wording": {}}
    for fam, sc, label, members in families():
        keep = []
        for m in members:
            why = BI.pair_ok(data, m[1], m[2])
            (out["excluded_pairs"].append(f"{label}/{m[0]}: {why}") if why else keep.append(m))
        ds = sc.split("|")[0]
        g = (lambda i, ds=ds: data["grp"][(ds, i)]) if fam == "SC-VALUE" else None
        out["families"][label] = {"family": fam, "scope": sc, **BI.run_family(label, keep, vals, BI.PRIMARY, notes, True, g)}
        out["secondary"][label] = {m: BI.run_family(f"{label}|sec", keep, vals, m, notes, False) for m in BI.DIRECTION if m != BI.PRIMARY}
    for ds in BI.DS:
        for a in BI.ARCH:
            for base in ("L0", "L1"):
                sc = f"{ds}|{a}|{base}"
                v = out["families"].get(f"SC-VALUE|{sc}", {}).get("members", {}).get("aligned_pretrained", {}).get("class")
                at = out["families"].get(f"SC-ATTRIB|{sc}", {}).get("members", {})
                r_, c_ = at.get("pretrained_vs_random", {}).get("class"), at.get("pretrained_vs_capacity", {}).get("class")
                if v is None:
                    continue
                w = ("complement from the pretrained representation" if v == "I>0" and r_ == "I>0" and c_ == "I>0" else
                     "added aligned features lower risk; source not separated" if v == "I>0" else
                     "no complement resolved" if v == "contains 0" else "residual fit worse than local_only on test people")
                out["wording"][sc] = {"value": v, "vs_random": r_, "vs_capacity": c_, "wording": w + (" (context-assisted: base L0 reads post-only EEG)" if base == "L0" and v == "I>0" else "")}
    out["levels"] = BI.levels(vals, sorted(vals, key=BI.ckey), list(BI.DIRECTION), "sc-levels", notes, None)
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}}
    out["notes"] = notes
    return out


def report(out, meta, path):
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    iv = lambda m, lo="ci_low", hi="ci_high": "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"
    L = ["# ALN3.2 revised complement — wave 2a: low-complexity fusion in the common prediction space (seed 3401, NCE)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm job {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.aln32_complement_interim` "
         "under the frozen `ADDENDUM_09_ALN32_SIMPLE_COMPLEMENT.md` §5 (ADDENDUM_05 machinery). Positive = candidate lower true-query risk. Residual ridges are "
         "fitted on out-of-fold base predictions over 5 groups of training participants; alphas by grouped CV. Base L0 reads post-only EEG (candidates read the "
         "aligned window: context-assisted); base L1 is access-matched.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + ".", "",
         f"Coverage: {out['coverage']['status']}. Excluded pairs: {len(out['excluded_pairs'])}.", "",
         "## 1. Wording rule (mechanical)", "", "| dataset · backbone · base | SC-VALUE aligned_pretrained | vs random | vs capacity | wording |", "|---|---|---|---|---|"]
    for sc, w in out["wording"].items():
        L.append(f"| {sc.replace('|', ' · ')} | {w['value']} | {w['vs_random']} | {w['vs_capacity']} | {w['wording']} |")
    L.append("")
    for fam, title in (("SC-VALUE", "2. Value over local_only"), ("SC-ATTRIB", "3. Attribution of the aligned-pretrained gain")):
        L += [f"## {title}", ""]
        for label, f in out["families"].items():
            if f["family"] != fam or not f["members"]:
                continue
            L += [f"**{f['scope'].replace('|', ' · ')}** (critical value {f.get('crit', float('nan')):.2f})", "",
                  "| member | label | n | ΔR | 95% CI | 95% simultaneous | class | " + " | ".join(s for _, s in SEC) + " |", "|---|---|---|---|---|---|---|" + "---|" * len(SEC)]
            sec = out["secondary"][label]
            for name, m in f["members"].items():
                L.append(f"| {name} | {m['tag']} | {m['n']} | {f3(m.get('est'))} | {iv(m)} | {iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | "
                         + " | ".join(f3(sec[k]["members"].get(name, {}).get("est")) for k, _ in SEC) + " |")
            L.append("")
    L += ["## 4. Levels", "", "| configuration | n | R [95% CI] | gain |", "|---|---|---|---|"]
    for k, r in out["levels"].items():
        R = r.get(BI.PRIMARY, {}); gn = r.get("unified/gain_bits", {}).get("est")
        L.append(f"| {k} | {r['n']} | {R.get('est', float('nan')):.3f} {iv(R)} | {f3(gn)} |")
    L += ["", "## Appendix: notes", ""] + [f"- {n}" for n in out["notes"][:40]] + [""]
    open(path, "w").write("\n".join(L))
    return path


def main():
    from auditory_alignment_v3 import run as r3
    rows = r3.all_rows(); prow, pload = expand(rows, BI.unit_loader())
    BI.cfg_of = cfg
    data = BI.load_continuous(prow, pload, BI.load_manifest())
    out = aggregate(data)
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_09_ALN32_SIMPLE_COMPLEMENT.md", "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
                                                                                for f in ("aln32_complement_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    BI.write_json(os.path.join(RES, "aln32_simple_complement.json"), {"meta": meta, **out})
    p = report(out, meta, os.path.join(DOCS, "COMPLEMENT_REVISED_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "aln32_simple_complement.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad, "| excluded", len(out["excluded_pairs"]), "| coverage", out["coverage"]["status"])
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
