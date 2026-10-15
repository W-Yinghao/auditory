"""ALN3 ADDENDUM_07 §5: ALN3.2 wave-1 analysis (seed 3401, NCE) with the ADDENDUM_05 machinery (bc_interim): identity-level paired
differences (positive = candidate lower true-query risk), bootstrap-t, max-t within each family. Configurations:
  L0  A_LOCAL lag_local_tokens full          L1  ALN32_LOCAL_SUPPORT local_aligned1000
  R0  raw_post600_ridge                      R1  raw_aligned1000_ridge
  A   B_ALIGNED (backbone, adaptation)       F2  ALN32_POSTONLY_FM (backbone, frozen / peft)
  T   ALN32_TRUE_FULL (backbone, random_full / pretrained_full, recipe, lr)
Families (per dataset x backbone unless noted): AI-ACCESS, AI-POSTONLY, AI-CONTEXT, AI-RAW (per dataset), AI-PASTEEG (per dataset),
TF-INIT, TF-RECIPE, TF-VS-LEGACY, TF-LOCAL. Also the per-unit update ledger of T and F2 (records' update_ledger).
Usage: python -m auditory_alignment_v3.aln32_interim"""
from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment_v3 import bc_interim as BI
from auditory_alignment_v3 import core

RES = os.environ.get("A32_RES", os.path.join(core.REPO, "results", "auditory_alignment_v3", "aln32_wave1"))
DOCS = os.environ.get("A32_DOCS", os.path.join(core.REPO, "docs", "auditory_alignment_v3"))
RECIPES = ("full_onestep_v1", "warmup_then_all_v1"); LRS = (1e-5, 3e-4); TINIT = ("random_full", "pretrained_full")
SEC = (("unified/regular/top1", "Δtop1"), ("unified/gain_bits", "Δgain"), ("native/regular/logloss_bits", "ΔR_native"), ("attention/unified/accuracy", "Δatt"))


def cfg(r):
    s, f, ds = r["spec"], r["family_id"], r["dataset"]
    if r["seed"] != BI.SEED or ds not in BI.DS or s.get("objective") != "NCE":
        return None
    if f == "A_LOCAL" and s.get("architecture") == "lag_local_tokens" and s.get("window") == "full" and s.get("projection_dim", 32) == 32:
        return ("L0", ds, "NCE")
    if f == "ALN32_LOCAL_SUPPORT":
        return ({"local_aligned1000": "L1", "raw_aligned1000_ridge": "R1", "raw_post600_ridge": "R0"}[s["variant"]], ds, "NCE")
    if f == "B_ALIGNED":
        return ("A", ds, "NCE", s["architecture"], s["adaptation"])
    if f == "ALN32_POSTONLY_FM":
        return ("F2", ds, "NCE", s["architecture"], s["adaptation"])
    if f == "ALN32_TRUE_FULL":
        return ("T", ds, "NCE", s["architecture"], s["adaptation"], s["recipe"], float(s["lr_backbone"]))
    return None


def families():
    out = []
    for ds in BI.DS:
        L0, L1, R0, R1 = (("L0", ds, "NCE"), ("L1", ds, "NCE"), ("R0", ds, "NCE"), ("R1", ds, "NCE"))
        out.append(("AI-PASTEEG", ds, f"AI-PASTEEG|{ds}", [("L0->L1", L0, L1, "past 0.4 s EEG for the local encoder")]))
        out.append(("AI-RAW", ds, f"AI-RAW|{ds}", [("R0->L0", R0, L0, "encoder vs ridge, post window"), ("R1->L1", R1, L1, "encoder vs ridge, aligned window")]
                    + [(f"R1->A/{a}/frozen", R1, ("A", ds, "NCE", a, "pretrained_frozen"), "frozen FM vs ridge, aligned window") for a in BI.ARCH]))
        for a in BI.ARCH:
            A = lambda ad: ("A", ds, "NCE", a, ad); F2 = lambda ad: ("F2", ds, "NCE", a, ad); T = lambda ad, rc, lr: ("T", ds, "NCE", a, ad, rc, lr)
            sc = f"{ds}|{a}"
            out.append(("AI-ACCESS", sc, f"AI-ACCESS|{sc}", [(ad, L1, A(ad), "FM vs local, same EEG access") for ad in BI.ADAPT]))
            out.append(("AI-POSTONLY", sc, f"AI-POSTONLY|{sc}", [(ad, L0, F2(ad), "FM vs local, same post-only access") for ad in ("pretrained_frozen", "pretrained_peft")]))
            out.append(("AI-CONTEXT", sc, f"AI-CONTEXT|{sc}", [(ad, F2(ad), A(ad), "value of the 0.4 s past EEG in the FM") for ad in ("pretrained_frozen", "pretrained_peft")]))
            out.append(("TF-INIT", sc, f"TF-INIT|{sc}", [(f"{rc}/lr{lr:g}", T("random_full", rc, lr), T("pretrained_full", rc, lr), "initialization (matched schedule and lr)")
                                                        for rc in RECIPES for lr in LRS]))
            out.append(("TF-RECIPE", sc, f"TF-RECIPE|{sc}", [(f"{ad}/lr{lr:g}", T(ad, RECIPES[0], lr), T(ad, RECIPES[1], lr), "recipe: one-step -> warm-up then all")
                                                            for ad in TINIT for lr in LRS]))
            out.append(("TF-VS-LEGACY", sc, f"TF-VS-LEGACY|{sc}", [(f"{ad}/{rc}/lr{lr:g}", A(ad), T(ad, rc, lr), "recipe: legacy prefix -> true full")
                                                                  for ad in TINIT for rc in RECIPES for lr in LRS]))
            out.append(("TF-LOCAL", sc, f"TF-LOCAL|{sc}", [(f"{ref}->{ad}/{rc}/lr{lr:g}", R, T(ad, rc, lr), f"FM vs local ({ref})")
                                                          for ref, R in (("L0", L0), ("L1", L1)) for ad in TINIT for rc in RECIPES for lr in LRS]))
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
        g = (lambda i, ds=ds: data["grp"][(ds, i)]) if fam in ("AI-ACCESS", "AI-POSTONLY", "TF-LOCAL") else None
        out["families"][label] = {"family": fam, "scope": sc, **BI.run_family(label, keep, vals, BI.PRIMARY, notes, True, g)}
        out["secondary"][label] = {m: BI.run_family(f"{label}|sec", keep, vals, m, notes, False) for m in BI.DIRECTION if m != BI.PRIMARY}
    out["levels"] = BI.levels(vals, sorted(vals, key=BI.ckey), list(BI.DIRECTION), "a32-levels", notes, None)
    out["coverage"] = {"status": {f"{k[0]}|{k[1]}": v for k, v in data["status"].items()}, "units": {BI.ckey(c): len(u) for c, u in data["units"].items()}}
    out["notes"] = notes
    return out


def ledger_summary(rows, load):
    """per T / F2 configuration: median first-open epoch, open epochs, grad steps and relative weight change per group kind."""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["family_id"] not in ("ALN32_TRUE_FULL", "ALN32_POSTONLY_FM") or r["seed"] != BI.SEED:
            continue
        rec = load(r["experiment_id"])
        if not rec or rec.get("status") != "complete" or "update_ledger" not in rec:
            continue
        c = BI.ckey(cfg(r))
        for L in rec["update_ledger"]["groups"]:
            kind = "readout" if L["name"] == "readout" else ("non-block" if str(L["name"]).startswith("other") else "block")
            for k in ("first_open_epoch", "epochs_open", "grad_steps", "rel_weight_change"):
                if L.get(k) is not None:
                    acc[c][f"{kind}|{k}"].append(L[k])
    return {c: {k: {"median": float(np.median(v)), "min": float(np.min(v)), "max": float(np.max(v)), "n": len(v)} for k, v in d.items()} for c, d in acc.items()}


def report(out, led, meta, path):
    f3 = lambda x: "–" if x is None else f"{x:+.3f}"
    iv = lambda m, lo="ci_low", hi="ci_high": "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"
    L = ["# ALN3.2 wave 1 — aligned interface controls and true full updates (seed 3401, NCE)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm job {os.environ.get('SLURM_JOB_ID', 'local')}) by `python -m auditory_alignment_v3.aln32_interim` under the "
         "frozen `ADDENDUM_07_ALN32_SUPPORT_AND_TRUE_FULL.md` §5 (ADDENDUM_05 machinery). Identity-level bootstrap-t intervals conditional on the seed-3401 "
         "training; simultaneous = max-t within the named family. Positive = candidate lower true-query risk (ΔR = R(reference) − R(candidate), bits per 5 s "
         "query, unified readout). B_ALIGNED / B_DENSE `pretrained_full − random_full` are recipe contrasts (CORRECTION_01); TF-INIT is the matched "
         "initialization contrast. The aligned interface changes window, context and head together; no result here is a pure phase effect.", "",
         "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in meta["code_sha256"].items()) + ".", "",
         f"Coverage: {out['coverage']['status']}. Excluded pairs: {len(out['excluded_pairs'])}.", "", "## 1. Levels (unified readout)", ""]
    for ds in BI.DS:
        L += [f"**{ds}**", "", "| configuration | n | R [95% CI] | top1 | gain | R_native |", "|---|---|---|---|---|---|"]
        for k, r in out["levels"].items():
            if k.split("|")[1] != ds:
                continue
            R = r.get(BI.PRIMARY, {}); gt = lambda m: "–" if m not in r else f"{r[m]['est']:.3f}"
            L.append(f"| {k} | {r['n']} | {R.get('est', float('nan')):.3f} {iv(R)} | {gt('unified/regular/top1')} | {gt('unified/gain_bits')} | {gt('native/regular/logloss_bits')} |")
        L.append("")
    titles = [("AI-ACCESS", "2. FM vs local under the same EEG access: L1 → B_ALIGNED"), ("AI-POSTONLY", "3. FM vs local under post-only access: L0 → F2"),
              ("AI-CONTEXT", "4. Value of the 0.4 s past EEG inside the FM: F2 → B_ALIGNED"), ("AI-PASTEEG", "5. Value of the 0.4 s past EEG for the local encoder: L0 → L1"),
              ("AI-RAW", "6. Encoder vs regularised linear readout on the same window"),
              ("TF-INIT", "7. True full update — initialization (random → pretrained, matched schedule and lr)"),
              ("TF-RECIPE", "8. True full update — recipe (one-step → warm-up then all)"), ("TF-VS-LEGACY", "9. Legacy progressive prefix (B_ALIGNED) → true full"),
              ("TF-LOCAL", "10. Local (L0 / L1) → true-full FM")]
    for fam, title in titles:
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
    L += ["## 11. Update ledger (true-full and post-only units)", "", "| configuration | group kind | first open epoch (median) | open epochs (median) | grad steps (median) | rel. weight change median [min, max] |",
          "|---|---|---|---|---|---|"]
    for c, d in sorted(led.items()):
        for kind in ("block", "non-block", "readout"):
            if f"{kind}|epochs_open" not in d:
                continue
            g = lambda k: d.get(f"{kind}|{k}", {})
            w = g("rel_weight_change")
            L.append(f"| {c} | {kind} | {g('first_open_epoch').get('median', float('nan')):.0f} | {g('epochs_open').get('median', float('nan')):.0f} | "
                     f"{g('grad_steps').get('median', float('nan')):.0f} | " + (f"{w['median']:.2e} [{w['min']:.2e}, {w['max']:.2e}]" if w else "–") + " |")
    L += ["", "## Appendix: notes", ""] + [f"- {n}" for n in out["notes"][:40]] + [""]
    open(path, "w").write("\n".join(L))
    return path


def main():
    from auditory_alignment_v3 import run as r3
    BI.cfg_of = cfg
    rows = r3.all_rows(); load = BI.unit_loader()
    data = BI.load_continuous(rows, load, BI.load_manifest())
    out = aggregate(data); led = ledger_summary(rows, load)
    here = os.path.dirname(__file__)
    meta = {"addendum": "ADDENDUM_07_ALN32_SUPPORT_AND_TRUE_FULL.md", "code_sha256": {f: hashlib.sha256(open(os.path.join(here, *f.split("/")), "rb").read()).hexdigest()
                                                                                    for f in ("aln32_interim.py", "bc_interim.py", "sci_r1/stats.py")}}
    BI.write_json(os.path.join(RES, "aln32_wave1.json"), {"meta": meta, **out, "ledger": led})
    p = report(out, led, meta, os.path.join(DOCS, "ALIGNED_INTERFACE_RESULTS.md"))
    bad = BI.privacy_scan([os.path.join(RES, "aln32_wave1.json"), p], set())
    print("privacy scan:", "PASS" if not bad else bad, "| excluded pairs", len(out["excluded_pairs"]), "| coverage", out["coverage"]["status"])
    if bad:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
