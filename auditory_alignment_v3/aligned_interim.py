"""ALN3 ADDENDUM_06 §5: B_ALIGNED analysis (seed 3401, NCE) with the ADDENDUM_05 machinery (bc_interim): identity-level paired
differences (positive = candidate better), bootstrap-t, family max-t per dataset x backbone. Families:
  AL-LOCAL      A_LOCAL lag_local_tokens full -> B_ALIGNED (5 adaptations)
  AL-INTERFACE  B_DENSE channel_phase_linear (same backbone / adaptation / NCE) -> B_ALIGNED
  AL-INIT       B_ALIGNED random_full -> pretrained_{frozen, peft, partial, full} (full = initialization, others recipe)
  AL-ADAPT      B_ALIGNED pretrained_frozen -> pretrained_{peft, partial, full}
Usage: python -m auditory_alignment_v3.aligned_interim"""
from __future__ import annotations

import os
import time

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core

RES = os.environ.get("AL_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "b_aligned"))
DOCS = os.environ.get("AL_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
SEC = (("unified/regular/top1", "Δtop1"), ("unified/gain_bits", "Δgain"), ("native/regular/logloss_bits", "ΔR_native"), ("attention/unified/accuracy", "Δatt"))


def cfg(r):
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if r["seed"] != BI.SEED or ds not in BI.DS or s.get("objective") != "NCE":
        return None
    if f == "B_ALIGNED":
        return ("A", ds, "NCE", s["architecture"], s["adaptation"])
    if f == "B_DENSE" and s["readout"] == "channel_phase_linear":
        return ("B", ds, "NCE", s["architecture"], s["adaptation"], "channel_phase_linear")
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L", ds, "NCE")
    return None


def families():
    out = []
    for ds in BI.DS:
        for a in BI.ARCH:
            A = lambda ad: ("A", ds, "NCE", a, ad)
            sc = f"{ds}|NCE|{a}"
            out.append(("AL-LOCAL", sc, f"AL-LOCAL|{sc}", [(ad, ("L", ds, "NCE"), A(ad), "vs local") for ad in BI.ADAPT]))
            out.append(("AL-INTERFACE", sc, f"AL-INTERFACE|{sc}", [(ad, ("B", ds, "NCE", a, ad, "channel_phase_linear"), A(ad), "aligned vs fixed-grid interface") for ad in BI.ADAPT]))
            out.append(("AL-INIT", sc, f"AL-INIT|{sc}", [(ad, A("random_full"), A(ad), "initialization (matched full update)" if ad == "pretrained_full" else "recipe") for ad in BI.PRE]))
            out.append(("AL-ADAPT", sc, f"AL-ADAPT|{sc}", [(ad, A("pretrained_frozen"), A(ad), "adaptation") for ad in BI.PRE[1:]]))
    return out


def aggregate(data):
    notes = list(data["notes"]); vals = data["vals"]
    out = {"families": {}, "secondary": {}, "excluded_pairs": []}
    for fam, sc, label, members in families():
        keep = []
        for m in members:
            why = BI.pair_ok(data, m[1], m[2])
            (out["excluded_pairs"].append(f"{label}/{m[0]}: {why}") if why else keep.append(m))
        ds = sc.split("|")[0]
        g = (lambda i, ds=ds: data["grp"][(ds, i)]) if fam == "AL-LOCAL" else None
        out["families"][label] = {"family": fam, "scope": sc, **BI.run_family(label, keep, vals, BI.PRIMARY, notes, True, g)}
        out["secondary"][label] = {m: BI.run_family(f"{label}|sec", keep, vals, m, notes, False) for m in BI.DIRECTION if m != BI.PRIMARY}
    out["levels"] = BI.levels(vals, sorted(vals, key=BI.ckey), list(BI.DIRECTION), "al-levels", notes, None)
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}, "units": {BI.ckey(c): len(u) for c, u in data["units"].items()}}
    out["notes"] = notes
    return out


def report(out, meta, path):
    f3, iv = (lambda x: "–" if x is None else f"{x:+.3f}"), (lambda m, lo="ci_low", hi="ci_high": "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]")
    L = ["# ALN3 B_ALIGNED query-aligned foundation-model readout — results (seed 3401, NCE)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm job {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.aligned_interim` "
         "under the frozen `ADDENDUM_06_B_ALIGNED.md` §5 with the ADDENDUM_05 machinery. Intervals: identity-level bootstrap-t conditional on the seed-3401 "
         "training (not seed uncertainty); simultaneous = max-t within the named family. Sign: positive = candidate better (ΔR = R(reference) − R(candidate), "
         "bits per 5 s query, unified readout).", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + ".", "",
         f"Coverage: {out['coverage']['status']}. Excluded pairs: {len(out['excluded_pairs'])}.", "", "## 1. Levels (unified readout, NCE)", ""]
    for ds in BI.DS:
        L += [f"**{ds}**", "", "| configuration | n | R [95% CI] | top1 | gain | R_native |", "|---|---|---|---|---|---|"]
        for k, r in out["levels"].items():
            p = k.split("|")
            if p[1] != ds:
                continue
            R = r.get(BI.PRIMARY, {}); gt = lambda m: "–" if m not in r else f"{r[m]['est']:.3f}"
            L.append(f"| {k} | {r['n']} | {R.get('est', float('nan')):.3f} {iv(R)} | {gt('unified/regular/top1')} | {gt('unified/gain_bits')} | {gt('native/regular/logloss_bits')} |")
        L.append("")
    titles = {"AL-INTERFACE": "2. Aligned vs fixed-grid interface: B_DENSE channel_phase_linear → B_ALIGNED", "AL-LOCAL": "3. Local model → B_ALIGNED",
              "AL-INIT": "4. Initialization: random_full → pretrained_* (full = matched-update initialization; others recipe)",
              "AL-ADAPT": "5. Adaptation: pretrained_frozen → peft / partial / full"}
    for fam, title in titles.items():
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
    import hashlib
    BI.cfg_of = cfg
    rows = r3.all_rows()
    data = BI.load_continuous(rows, BI.unit_loader(), BI.load_manifest())
    out = aggregate(data)
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_06_B_ALIGNED.md", "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
                                                                  for f in ("aligned_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    BI.write_json(os.path.join(RES, "b_aligned.json"), {"meta": meta, **out})
    p = report(out, meta, os.path.join(DOCS, "B_ALIGNED_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "b_aligned.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad, "| excluded pairs", len(out["excluded_pairs"]), "| coverage", out["coverage"]["status"])
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
