"""ALN3 ADDENDUM_10 §5: ALN32_RESIDUAL analysis (seed 3401; NCE and CS_SINGLE) with the ADDENDUM_05 machinery.
  RS-VALUE   (dataset x objective)            base L0 (A_LOCAL lag_local_tokens full) -> each residual configuration
  RS-ATTRIB  (dataset x objective x backbone) residual_aligned_random -> residual_aligned_pretrained;
                                              residual_small_capacity -> residual_aligned_pretrained
plus the per-configuration fraction of units whose selected epoch is 0 (descriptive).
Usage: python -m auditory_alignment_v3.aln32_residual_interim"""
from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core

RES = os.environ.get("RS_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln32_residual"))
DOCS = os.environ.get("RS_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
OBJS = ("NCE", "CS_SINGLE")
CONF = [("residual_aligned_pretrained", a) for a in BI.ARCH] + [("residual_aligned_random", a) for a in BI.ARCH] + [("residual_small_capacity", "small_capacity_branch")]
SEC = (("unified/regular/top1", "Δtop1"), ("unified/gain_bits", "Δgain"), ("native/regular/logloss_bits", "ΔR_native"), ("attention/unified/accuracy", "Δatt"))


def cfg(r):
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if r["seed"] != BI.SEED or ds not in BI.DS or s.get("objective") not in OBJS:
        return None
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L0", ds, s["objective"])
    if f == "ALN32_RESIDUAL":
        return ("RS", ds, s["objective"], s["architecture"], s["variant"])
    return None


def families():
    out = []
    for ds in BI.DS:
        for o in OBJS:
            sc = f"{ds}|{o}"
            out.append(("RS-VALUE", sc, f"RS-VALUE|{sc}", [(f"{a}/{v}", ("L0", ds, o), ("RS", ds, o, a, v), "vs base (epoch-0 candidate allowed)") for v, a in CONF]))
            for a in BI.ARCH:
                P = ("RS", ds, o, a, "residual_aligned_pretrained")
                out.append(("RS-ATTRIB", f"{sc}|{a}", f"RS-ATTRIB|{sc}|{a}", [("pretrained_vs_random", ("RS", ds, o, a, "residual_aligned_random"), P, "pretrained weights"),
                                                                            ("pretrained_vs_small", ("RS", ds, o, "small_capacity_branch", "residual_small_capacity"), P, "beyond a small branch, same access")]))
    return out


def aggregate(data, rows, load):
    notes = list(data["notes"]); vals = data["vals"]
    out = {"families": {}, "secondary": {}, "excluded_pairs": [], "epoch0": {}, "wording": {}}
    for fam, sc, label, members in families():
        keep = []
        for m in members:
            why = BI.pair_ok(data, m[1], m[2])
            (out["excluded_pairs"].append(f"{label}/{m[0]}: {why}") if why else keep.append(m))
        ds = sc.split("|")[0]
        g = (lambda i, ds=ds: data["grp"][(ds, i)]) if fam == "RS-VALUE" else None
        out["families"][label] = {"family": fam, "scope": sc, **BI.run_family(label, keep, vals, BI.PRIMARY, notes, True, g)}
        out["secondary"][label] = {m: BI.run_family(f"{label}|sec", keep, vals, m, notes, False) for m in BI.DIRECTION if m != BI.PRIMARY}
    e0 = defaultdict(list)
    for r in rows:
        if r["family_id"] == "ALN32_RESIDUAL" and r["seed"] == BI.SEED:
            rec = load(r["experiment_id"])
            if rec and rec.get("status") == "complete":
                e0[BI.ckey(cfg(r))].append(bool(rec.get("epoch0_selected")))
    out["epoch0"] = {k: {"n": len(v), "fraction_epoch0": sum(v) / len(v)} for k, v in e0.items()}
    for ds in BI.DS:
        for o in OBJS:
            fv = out["families"].get(f"RS-VALUE|{ds}|{o}", {}).get("members", {})
            for a in BI.ARCH:
                v = fv.get(f"{a}/residual_aligned_pretrained", {}).get("class")
                at = out["families"].get(f"RS-ATTRIB|{ds}|{o}|{a}", {}).get("members", {})
                r_, s_ = at.get("pretrained_vs_random", {}).get("class"), at.get("pretrained_vs_small", {}).get("class")
                if v is None:
                    continue
                w = ("complement from the pretrained representation" if v == "I>0" and r_ == "I>0" and s_ == "I>0" else
                     "residual lowers risk; source not separated" if v == "I>0" else "no correction resolved" if v == "contains 0" else "residual worse than the base on test people")
                out["wording"][f"{ds}|{o}|{a}"] = {"value": v, "vs_random": r_, "vs_small": s_, "wording": w}
    out["levels"] = BI.levels(vals, sorted(vals, key=BI.ckey), list(BI.DIRECTION), "rs-levels", notes, None)
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}}
    out["notes"] = notes
    return out


def report(out, meta, path):
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    iv = lambda m, lo="ci_low", hi="ci_high": "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"
    L = ["# ALN3.2 revised complement — wave 2b: trained residual with an epoch-0 candidate (seed 3401)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm job {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.aln32_residual_interim` "
         "under the frozen `ADDENDUM_10_ALN32_RESIDUAL.md` §5. Positive = candidate lower true-query risk. Selection on a fixed inner development group of "
         "training participants (epoch 0 = the base is a legal choice); test participants are never used.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + ".", "",
         f"Coverage: {out['coverage']['status']}. Excluded pairs: {len(out['excluded_pairs'])}.", "",
         "## 1. Selected epoch 0 (no correction adopted), per configuration", "", "| configuration | units | fraction epoch 0 |", "|---|---|---|"]
    for k, v in sorted(out["epoch0"].items()):
        L.append(f"| {k} | {v['n']} | {v['fraction_epoch0']:.2f} |")
    L += ["", "## 2. Wording rule (mechanical)", "", "| dataset · objective · backbone | RS-VALUE pretrained | vs random | vs small | wording |", "|---|---|---|---|---|"]
    for k, w in out["wording"].items():
        L.append(f"| {k.replace('|', ' · ')} | {w['value']} | {w['vs_random']} | {w['vs_small']} | {w['wording']} |")
    L.append("")
    for fam, title in (("RS-VALUE", "3. Value over the base"), ("RS-ATTRIB", "4. Attribution")):
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
    L += ["## Appendix: notes", ""] + [f"- {n}" for n in out["notes"][:40]] + [""]
    open(path, "w").write("\n".join(L))
    return path


def main():
    from auditory_alignment_v3 import run as r3
    BI.cfg_of = cfg
    rows = r3.all_rows(); load = BI.unit_loader()
    data = BI.load_continuous(rows, load, BI.load_manifest())
    out = aggregate(data, rows, load)
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_10_ALN32_RESIDUAL.md", "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
                                                                       for f in ("aln32_residual_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    BI.write_json(os.path.join(RES, "aln32_residual.json"), {"meta": meta, **out})
    p = report(out, meta, os.path.join(DOCS, "COMPLEMENT_REVISED_RESIDUAL_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "aln32_residual.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad, "| excluded", len(out["excluded_pairs"]), "| coverage", out["coverage"]["status"])
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
