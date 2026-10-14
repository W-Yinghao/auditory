"""Markdown rendering for ADDENDUM_05 (bc_interim): neutral tables only; wording limited to the frozen interpretation grid."""
from __future__ import annotations

import os
import time
from collections import Counter

from .bc_interim import DS, OBJ, PRIMARY

SEC = (("unified/regular/top1", "Δtop1"), ("unified/regular/rank_pct", "Δrank%"), ("unified/gain_bits", "Δgain"),
       ("native/regular/logloss_bits", "ΔR_native"), ("attention/unified/accuracy", "Δatt"))
DSN = {"fau": "FAU", "dtu": "DTU", "federici": "Federici"}


def f3(x):
    return "–" if x is None else f"{x:+.3f}"


def iv(m, lo="ci_low", hi="ci_high"):
    return "–" if lo not in m else f"[{m[lo]:+.3f}, {m[hi]:+.3f}]"


def header(title, meta, extra):
    sha = meta["code_sha256"]
    job = os.environ.get("SLURM_JOB_ID", "local")
    return [f"# {title}", "",
            f"**Interim, seed 3401 only.** Generated {time.strftime('%Y-%m-%d %H:%M %Z')} (Slurm job {job}) by "
            f"`python -m auditory_alignment_v3.bc_interim` under the frozen `{meta['addendum']}`. Intervals are identity-level "
            f"bootstrap-t ({meta['n_boot']} replicates) conditional on the seed-3401 training; they are not training-seed uncertainty. "
            "Simultaneous intervals: max-t within the family named in each table. Sign: positive = the candidate is better "
            "(ΔR = R(reference) − R(candidate), bits per 5 s query, unified readout). Classes follow ADDENDUM_05 §7; no other "
            "interpretation is made here.", "",
            "Code sha256: " + ", ".join(f"`{k}` {v[:12]}" for k, v in sha.items()) + ".", ""] + extra


def coverage_lines(cont, sets):
    cov = cont["coverage"]
    st = Counter()
    for k, v in cov["status"].items():
        st[k] += v
    lines = ["## 0. Coverage and checks", "",
             "| set | complete | other |", "|---|---|---|"]
    for s in sets:
        c = sum(v for k, v in st.items() if k.startswith(s + "|") and k.endswith("|complete"))
        o = sum(v for k, v in st.items() if k.startswith(s + "|") and not k.endswith("|complete"))
        lines.append(f"| {s} | {c} | {o} |")
    lines += ["", "Identities (local reference, NCE): " + "; ".join(
        f"{DSN[ds]} " + ", ".join(f"{g} {n}" for g, n in sorted(cov["identities"][ds].items())) for ds in DS)
              + f". Federici phantom entities excluded: {cov['n_phantom_entities'].get('federici', 0)}.",
              f"Pairing check (identical participant sets and candidate / query counts per fold): {cont['pairing']}; "
              f"excluded pairs: {len(cont['excluded_pairs'])}.", ""]
    return lines


def overview(cont, fams):
    lines = ["## 1. Overview: interval classes (simultaneous 95%)", "", "| family | dataset | objective | I>0 | I<0 | contains 0 |", "|---|---|---|---|---|---|"]
    for fam in fams:
        for ds in DS:
            for o in OBJ:
                c = Counter()
                for label, f in cont["families"].items():
                    if f.get("family") == fam and f["scope"].startswith(f"{ds}|{o}"):
                        c.update(m.get("class") for m in f["members"].values() if m.get("class"))
                if c:
                    lines.append(f"| {fam} | {DSN[ds]} | {o} | {c['I>0']} | {c['I<0']} | {c['contains 0']} |")
    return lines + [""]


def cfg_name(k):
    p = k.split("|")
    if p[0] == "L":
        return "local `lag_local_tokens` full"
    if p[0] == "B":
        return f"B {p[3]} / {p[4]} / {p[5]}"
    return f"C {p[3]} / {p[4]}"


def levels_table(cont, ds, o, prefixes):
    lines = [f"**{DSN[ds]} · {o}**", "", "| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |", "|---|---|---|---|---|---|---|---|"]
    for k, r in cont["levels"].items():
        p = k.split("|")
        if p[1] != ds or p[2] != o or p[0] not in prefixes:
            continue
        R = r.get(PRIMARY, {})
        g = lambda m: "–" if m not in r else f"{r[m]['est']:.3f}"
        lines.append(f"| {cfg_name(k)} | {r['n']} | {R.get('est', float('nan')):.3f} {iv(R)} | {g('unified/regular/top1')} | {g('unified/regular/rank_pct')} | "
                     f"{g('unified/gain_bits')} | {g('native/regular/logloss_bits')} | {g('attention/unified/accuracy')} |")
    return lines + [""]


def family_table(cont, fam, ds, o, groups=False):
    lines = []
    labels = [l for l, f in cont["families"].items() if f.get("family") == fam and f["scope"].startswith(f"{ds}|{o}")]
    for label in sorted(labels):
        f = cont["families"][label]
        if not f["members"]:
            continue
        sc = f["scope"].split("|")
        lines += [f"**{DSN[ds]} · {o}" + (f" · {sc[2]}" if len(sc) > 2 else "") + f"** (family `{label}`, critical value {f.get('crit', float('nan')):.2f})", "",
                  "| member | label | n | ΔR | 95% CI | 95% simultaneous | class | " + " | ".join(s for _, s in SEC) + " |",
                  "|---|---|---|---|---|---|---|" + "---|" * len(SEC)]
        sec = cont["secondary"][label]
        for name, m in f["members"].items():
            s2 = [f3(sec[k]["members"].get(name, {}).get("est")) for k, _ in SEC]
            lines.append(f"| {name} | {m['tag']} | {m['n']} | {f3(m.get('est'))} | {iv(m)} | {iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | " + " | ".join(s2) + " |")
        lines.append("")
        if groups:
            gs = sorted({g for m in f["members"].values() for g in m.get("groups", {})})
            lines += ["Per group (descriptive, pointwise; n < 5 → n only):", "", "| member | " + " | ".join(gs) + " |", "|---|" + "---|" * len(gs)]
            for name, m in f["members"].items():
                cells = []
                for g in gs:
                    x = m.get("groups", {}).get(g, {})
                    cells.append(f"n={x.get('n', 0)}" if "est" not in x else f"{x['est']:+.3f} {iv(x)} (n={x['n']})")
                lines.append(f"| {name} | " + " | ".join(cells) + " |")
            lines.append("")
    return lines


def notes_lines(cont, n=40):
    ns = cont["notes"]
    lines = ["## Appendix: notes", "", f"{len(ns)} notes" + (f" (first {n} listed; all in the JSON)" if len(ns) > n else "") + ":", ""]
    return lines + [f"- {x}" for x in ns[:n]] + [""]


def write_continuous(cont, dst, meta, docs):
    out = []
    # ---- B
    L = header("ALN3 B_DENSE dense readout — interim results", meta, [])
    L += coverage_lines(cont, ["B", "L"])
    L += overview(cont, ("B-READOUT", "B-INIT", "B-ADAPT", "B-LOCAL"))
    L += ["## 2. Levels (unified readout)", "", "R = true-query candidate cross-entropy (bits, lower is better); other columns are identity means.", ""]
    for ds in DS:
        for o in OBJ:
            L += levels_table(cont, ds, o, ("B", "L"))
    sections = (("B-READOUT", "3. Readout at fixed backbone and adaptation: `channel_phase_linear` → `dense_query`", False),
                ("B-INIT", "4. Initialization at fixed readout: `random_full` → `pretrained_*` (only `pretrained_full` is the matched-update initialization contrast; others are recipe contrasts)", False),
                ("B-ADAPT", "5. Adaptation at fixed initialization: `pretrained_frozen` → `pretrained_{peft, partial, full}`", False),
                ("B-LOCAL", "6. Foundation dense readout vs the local model (same dense task): local → B configuration", True))
    for fam, title, groups in sections:
        L += [f"## {title}", ""]
        for ds in DS:
            for o in OBJ:
                L += family_table(cont, fam, ds, o, groups)
    L += ["## 7. Not in this interim", "",
          "- Seed panel (3407 / 3413): to be added with the same code when the registered cells complete (ADDENDUM_05 §6).",
          "- B_LAYER_PROBE layer panel, B_LR_PANEL, B_CTRL_ONESTEP, training curves.",
          "- The ALN2 coarse `SpatialPatchHead` interface (1.2 s target) is not differenced against ALN3 (docs/05 l.24).", ""]
    L += notes_lines(cont)
    p = os.path.join(docs, "B_DENSE_READOUT_RESULTS.md"); open(p, "w").write("\n".join(L)); out.append(p)
    # ---- C
    L = header("ALN3 C_COMPLEMENT local + pretrained complement — interim results", meta, [])
    L += coverage_lines(cont, ["C", "L"])
    L += overview(cont, ("C-LOCAL", "C-ATTRIB", "C-FMONLY"))
    L += ["## 2. Levels (unified readout)", ""]
    for ds in DS:
        for o in OBJ:
            L += levels_table(cont, ds, o, ("C", "L"))
    L += ["## 3. Primary increment R(local) − R(combined): local base → C variant (and → capacity control)", ""]
    for ds in DS:
        for o in OBJ:
            L += family_table(cont, "C-LOCAL", ds, o, True)
    L += ["### 3a. Mismatched-only check (docs/06)", "",
          "Δgain = gain(candidate) − gain(local), Δ mismatched logloss = candidate − local (pointwise 95%). Flag = Δgain interval > 0 while the ΔR "
          "simultaneous interval does not lie above 0.", "",
          "| cell | ΔR class | Δgain [95% CI] | Δ mismatched logloss [95% CI] | mismatched-only |", "|---|---|---|---|---|"]
    for k, v in cont["mismatched_only"].items():
        g, mm = v["d_gain"], v["d_mismatched_logloss"]
        L.append(f"| {k.replace('C-LOCAL|', '')} | {v['dR_class']} | {g[0]:+.3f} [{g[1]:+.3f}, {g[2]:+.3f}] | "
                 + ("–" if mm[0] is None else f"{mm[0]:+.3f} [{mm[1]:+.3f}, {mm[2]:+.3f}]") + f" | {'yes' if v['mismatched_only'] else 'no'} |")
    L += ["", "## 4. Attribution (per backbone): initialization, capacity, residual structure", ""]
    for ds in DS:
        for o in OBJ:
            L += family_table(cont, "C-ATTRIB", ds, o)
    L += ["### 4a. Wording rule (ADDENDUM_05 §7), mechanical", "", "| cell | C-LOCAL | init | capacity | wording |", "|---|---|---|---|---|"]
    for k, v in cont["complement_wording"].items():
        L.append(f"| {k} | {v['c_local']} | {v['init'] or 'n/a'} | {v['capacity'] or 'n/a'} | {v['wording']} |")
    L += ["", "## 5. Combined vs foundation only: B_DENSE `dense_query` (matched adaptation) → C variant", ""]
    for ds in DS:
        for o in OBJ:
            L += family_table(cont, "C-FMONLY", ds, o)
    L += ["## 6. D policy arms: binding and progress (training side only; no D test value read)", ""]
    if dst:
        L += ["| family / arm | complete | not complete |", "|---|---|---|"]
        for k, v in sorted(dst["progress"].items()):
            L.append(f"| {k} | {v.get('complete', 0)} | {v.get('not complete', 0)} |")
        L += ["", f"Policy cells: {dst['n_cells']}; unresolved: {dst['unresolved'] or 0}. Chosen configuration counts (lowest training-side "
              "`best_selection_score`, ADDENDUM_04 §1):", "", "| arm · dataset · objective | chosen configuration: cells |", "|---|---|"]
        for k, v in sorted(dst["choices"].items()):
            L.append(f"| {k.replace('|', ' · ')} | " + "; ".join(f"{n}: {c}" for n, c in sorted(v.items(), key=lambda x: -x[1])) + " |")
        L.append("")
    L += ["## 7. Not in this interim / pending", "",
          "- Mismatched-FM-context and position-only controls (docs/06 last line) are not implemented in the C records; the attribution "
          "of any C gain to the correct pretrained EEG observation is therefore not tested beyond the random-initialization and capacity controls.",
          "- Seed panel (3407 / 3413); D results; group × method interactions.", ""]
    L += notes_lines(cont)
    p = os.path.join(docs, "C_COMPLEMENT_RESULTS.md"); open(p, "w").write("\n".join(L)); out.append(p)
    return out


def pname(k):
    return k.replace("|", " / ")


def write_private(priv, meta, d):
    L = header("ALN3 private task (E families) — interim summary (PRIVATE, not for publication)", meta,
               ["Private children, seed 3401. NLL = positive-affine calibrated natural-distribution NLL (bits, lower is better); AUC = "
                "positive-affine AUC (= native ranking). Contrasts: ΔNLL = NLL(reference) − NLL(candidate), ΔAUC = AUC(candidate) − "
                "AUC(reference); positive = candidate better. NLL changes with unchanged AUC are probability / calibration changes "
                "(docs/08 §5). No age, duration, stage or function analysis here.", ""])
    cov = priv["coverage"]
    L += ["## 0. Coverage", "", f"Unit status: {cov['status']}. Children per configuration: {cov['children_per_config']}. Groups: {cov['groups']}.", ""]
    L += ["## 1. Levels", "", "| configuration | n | NLL [95% CI] | AUC [95% CI] | hist gain | twin sens. | NLL HA / NH | AUC HA / NH |", "|---|---|---|---|---|---|---|---|"]
    for k, r in priv["levels"].items():
        def lv(m):
            x = r.get(m, {})
            return "–" if "est" not in x else (f"{x['est']:.3f} {iv(x)}" if "ci_low" in x else f"{x['est']:.3f}")
        def gp(m):
            g = r.get(m, {}).get("groups", {})
            return " / ".join((f"{g[s]['est']:.3f}" if "est" in g.get(s, {}) else f"n={g.get(s, {}).get('n', 0)}") for s in ("HA", "NH"))
        L.append(f"| {pname(k)} | {r['n']} | {lv('NLL')} | {lv('AUC')} | {lv('hist_gain')} | {lv('twin_sens')} | {gp('NLL')} | {gp('AUC')} |")
    L.append("")
    titles = {"PE-GENERIC": "2. Generic FM: `random_full` → `pretrained_*` (full = matched-update initialization contrast; others recipe)",
              "PE-LOCAL": "3. vs the local model: E_LOCAL `lag_local_tokens` full → E_GENERIC / E_PUBLIC_TRANSFER configuration",
              "PE-TRANSFER": "4. Public auditory transfer vs the non-transferred twin",
              "PE-COMPLEMENT": "5. Local + pretrained residual logit (within record) and recipe contrasts",
              "PE-DISTILL": "6. Distillation: λ = 0 baseline → chosen λ (within record)"}
    for fam, title in titles.items():
        L += [f"## {title}", ""]
        for label, f in priv["families"].items():
            if f.get("family") != fam or not f["members"]:
                continue
            ep = label.split("|")[-1]
            L += [f"**{f['scope'].replace('|', ' · ')} · {ep}** (critical value {f.get('crit', float('nan')):.2f})", "",
                  f"| member | label | n | Δ{ep} | 95% CI | 95% simultaneous | class | Δhist gain | Δtwin sens. |", "|---|---|---|---|---|---|---|---|---|"]
            sec = priv["secondary"][f"{fam}|{f['scope']}"]
            for name, m in f["members"].items():
                h = sec["hist_gain"]["members"].get(name, {}).get("est"); t = sec["twin_sens"]["members"].get(name, {}).get("est")
                L.append(f"| {name} | {m['tag']} | {m['n']} | {f3(m.get('est'))} | {iv(m)} | {iv(m, 'sim_low', 'sim_high')} | {m.get('class', '–')} | {f3(h)} | {f3(t)} |")
            L.append("")
    L += ["## Appendix: notes", ""] + [f"- {x}" for x in priv["notes"][:60]] + [""]
    p = os.path.join(d, "PRIVATE_E_INTERIM.md"); open(p, "w").write("\n".join(L))
    return p
