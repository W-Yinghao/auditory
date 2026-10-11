"""ALN3 R_FEDERICI: entity / identity re-aggregation of every ALN2 Federici model (no retraining; predictions unchanged).

Entity manifest (private, built from the original metadata; ALN3 addendum 01): record_uid = '<condition>:<file id>';
subject_uid HC:<code> | CI:<code> | HCv:<N>vocod | phantom:junior; HC-v are separate identities (no evidence of overlap with
HC); the 9 Artifact sessions are one phantom entity. HC-v ages / sex / behavioural accuracy from the metadata rows 'Nvocod'
(file number N <-> 'Nvocod' by order; recorded as inferred).
Per unit, per record the ALN2 per-participant metrics are taken as reported (same candidate pools, same predictions); then
averaged over the configuration's units (one content fold for Federici), then within subject (one record per subject per
condition here), each child weighted equally. Tables: HC / CI / HC-v separately (children, records, gain, true NLL, top-1);
CI - HC (independent groups); the phantom as one entity (session spread reported as model variation, never as n);
a human pool (HC + CI + HC-v, child-equal; population stated) for continuity with the legacy n=95 mixed table; paired
contrasts (pretrained - random, local - legacy) by identity; HC-v age slopes with corrected ages.
Usage: python -m auditory_alignment_v3.reaggregate_federici
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment.aggregate import boot, ols_boot, unit_rows

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(REPO, "private", "auditory_alignment_v2")
KCS = os.path.join(REPO, "private", "auditory_alignment_kernel_cs")
PRIV = os.path.join(REPO, "private", "auditory_alignment_v3", "reaggregate")
RES = os.path.join(REPO, "results", "auditory_alignment_v3", "reaggregate")
DOC = os.path.join(REPO, "docs", "auditory_alignment_v3", "FEDERICI_REAGGREGATION_RECEIPT.md")
PLAN2 = os.path.join(REPO, "AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006", "plans", "planned_comparisons.jsonl")
METRICS = ("unified/gain_bits", "native/gain_bits", "unified/regular/logloss_bits", "unified/regular/top1", "unified/mismatched_eeg/logloss_bits")
NB = 4000


def fmt(s, d=3):
    return "–" if not s or s.get("est") is None else f"{s['est']:.{d}f} [{s['ci_low']:.{d}f}, {s['ci_high']:.{d}f}]"


def diff_ind(a, b, seed=0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3:
        return {"est": None}
    r = np.random.default_rng(seed)
    bs = a[r.integers(0, len(a), (NB, len(a)))].mean(1) - b[r.integers(0, len(b), (NB, len(b)))].mean(1)
    return {"est": float(a.mean() - b.mean()), "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5)), "n_a": len(a), "n_b": len(b)}


def entity_manifest():
    import pandas as pd
    from auditory_alignment.data import FED_META, FED_PRE, _fed_id
    meta = pd.read_excel(FED_META); meta["code"] = meta["codice exp"].astype(str).str.strip()
    hc = {c: r for c, r in meta[meta.Group == 0].set_index("code").iterrows()}
    ci_rows = meta[meta.Group.isin([1, 2])]
    hv = {c: r for c, r in meta[meta.Group == 3].set_index("code").iterrows()}
    rows = []
    src_hash = hashlib.sha256(open(FED_META, "rb").read()).hexdigest()[:16]
    for grp in ("HC", "CI", "HC-v", "Artifact"):
        for p in sorted(glob.glob(os.path.join(FED_PRE, grp, "*.h5"))):
            fid = os.path.basename(p)[:-3]; rec = f"{grp}:{fid}"
            if grp == "HC":
                m = hc.get(_fed_id(fid), hc.get(fid)); subj = f"HC:{fid}"; et = "human"; src = "metadata Group 0 code = file id"
            elif grp == "HC-v":
                code = f"{int(fid) - 1000}vocod"; m = hv.get(code); subj = f"HCv:{code}"; et = "human"
                src = "metadata Group 3 'Nvocod' by file-number order (inferred); no evidence of identity with HC"
            elif grp == "CI":
                key = "S" + fid.lstrip("0").rjust(3, "0")
                m = None
                for _, r in ci_rows.iterrows():
                    if r.code.upper().replace("S", "").lstrip("0") == fid.lstrip("0"):
                        m = r; break
                subj = f"CI:{key}"; et = "human"; src = "metadata Group 1/2 code matched on the numeric part"
            else:
                m = None; subj = "phantom:junior"; et = "phantom"; src = "dataset README section 6 'Phantom Head (only Artifact activity)'; PhantomHeadJunior.xlsx session"
            rows.append({"dataset": "federici", "record_uid": rec, "subject_uid": subj, "condition": grp, "entity_type": et, "identity_source": src,
                         "source_hash": src_hash, "age_years": None if m is None else float(m["età al test in anni"]),
                         "sex": None if m is None else str(m["Sex"]), "behav_acc": None if m is None or m["Behav acc"] != m["Behav acc"] else float(m["Behav acc"])})
    return rows


def unit_records():
    """config key -> list of (unit id, per-record metrics) for every ALN2 Federici unit (repaired main units) + E9."""
    plan = {json.loads(l)["experiment_id"]: json.loads(l) for l in open(PLAN2)}
    cfg = defaultdict(list)
    for p in glob.glob(os.path.join(V2, "units", "ALN2_*federici*.json")):
        if p.endswith(".FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") != "complete":
            continue
        src = r
        if r.get("reuse_of"):
            sp = os.path.join(V2, "units", f"{r['reuse_of']}.json")
            if not os.path.exists(sp):
                continue
            src = json.load(open(sp))
        if "eval" not in src:
            continue
        row = plan.get(r["experiment_id"]) or r["row"]
        key = f"{row['family_id']}|seed{row['seed']}|" + json.dumps(row["spec"], sort_keys=True)
        cfg[key].append((r["experiment_id"], unit_rows(src)))
    for p in glob.glob(os.path.join(KCS, "units_linear", "*.json")):
        r = json.load(open(p))
        if r.get("status") == "complete" and r["job"]["dataset"] == "federici":
            cfg[f"LIN_E9|seed0|{r['job']['target']}|{r['job']['window']}"].append((os.path.basename(p)[:-5], unit_rows(r)))
    return cfg


def main():
    t0 = time.time()
    os.makedirs(PRIV, exist_ok=True); os.makedirs(RES, exist_ok=True)
    os.chmod(PRIV, 0o700)
    man = entity_manifest(); byrec = {m["record_uid"]: m for m in man}
    with open(os.path.join(PRIV, "entity_manifest.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(man[0])); w.writeheader(); w.writerows(man)
    cfg = unit_records()
    long_rows = []
    T = {}  # cfg -> subject -> metric (child-equal after unit / record averaging)
    PH = {}  # cfg -> session -> metric
    for k, units in cfg.items():
        acc = defaultdict(lambda: defaultdict(list))
        for uid, rows in units:
            for rec, m in rows.items():
                if rec not in byrec:
                    continue
                for mm in METRICS:
                    if mm in m:
                        acc[rec][mm].append(m[mm])
                        long_rows.append([k, uid, rec, byrec[rec]["subject_uid"], byrec[rec]["condition"], byrec[rec]["entity_type"], mm, m[mm]])
        per_rec = {rec: {mm: float(np.mean(v)) for mm, v in ms.items()} for rec, ms in acc.items()}
        subj = defaultdict(lambda: defaultdict(list)); ph = {}
        for rec, ms in per_rec.items():
            if byrec[rec]["entity_type"] == "phantom":
                ph[rec] = ms; continue
            for mm, v in ms.items():
                subj[byrec[rec]["subject_uid"]][mm].append(v)
        T[k] = {s: {mm: float(np.mean(v)) for mm, v in ms.items()} for s, ms in subj.items()}
        PH[k] = ph
    with open(os.path.join(PRIV, "federici_long.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["config", "unit_id", "record_uid", "subject_uid", "condition", "entity_type", "metric", "value"]); w.writerows(long_rows)
    cond = lambda s: s.split(":")[0]
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "entities": {}, "configs": {}, "contrasts": {}, "phantom": {}, "hcv_age": {}}
    from collections import Counter
    out["entities"] = {"children_by_condition": dict(Counter(m["condition"] for m in man if m["entity_type"] == "human")),
                       "independent_children": len({m["subject_uid"] for m in man if m["entity_type"] == "human"}),
                       "phantom_entities": len({m["subject_uid"] for m in man if m["entity_type"] == "phantom"}),
                       "phantom_sessions": sum(m["entity_type"] == "phantom" for m in man),
                       "hcv_identity": "separate from HC (no evidence of overlap; ALN3 addendum 01)"}
    for k, S in T.items():
        c = {}
        for g, lab in (("HC", "HC"), ("CI", "CI"), ("HCv", "HC-v")):
            ss = [s for s in S if cond(s) == g]
            c[lab] = {mm: boot([S[s][mm] for s in ss if mm in S[s]]) for mm in METRICS}
            c[lab]["n_children"] = len(ss)
        c["human_pool_child_equal"] = {mm: boot([v[mm] for v in S.values() if mm in v]) for mm in METRICS}
        c["CI_minus_HC"] = {mm: diff_ind([S[s][mm] for s in S if cond(s) == "CI" and mm in S[s]], [S[s][mm] for s in S if cond(s) == "HC" and mm in S[s]]) for mm in ("unified/gain_bits", "unified/regular/logloss_bits")}
        c["HCv_minus_HC_independent"] = {mm: diff_ind([S[s][mm] for s in S if cond(s) == "HCv" and mm in S[s]], [S[s][mm] for s in S if cond(s) == "HC" and mm in S[s]]) for mm in ("unified/gain_bits",)}
        out["configs"][k] = c
        ph = [v["unified/gain_bits"] for v in PH[k].values() if "unified/gain_bits" in v]
        if ph:
            out["phantom"][k] = {"entity_mean_gain": float(np.mean(ph)), "session_min": float(np.min(ph)), "session_max": float(np.max(ph)), "n_sessions": len(ph),
                                 "note": "one phantom entity; sessions are not independent samples"}
    # paired contrasts by identity (same children): pretrained - random_full; lag_local - legacy_pool4 (A_TIME full)
    def find(pred):
        return [k for k in T if pred(k)]
    for k in find(lambda k: k.startswith("B_FM|seed3401|") and '"pretrained_' in k):
        sp = json.loads(k.split("|", 2)[2]); kr = f"B_FM|seed3401|" + json.dumps({**sp, "adaptation": "random_full"}, sort_keys=True)
        if kr in T:
            for g in ("HC", "CI", "HCv"):
                d = [T[k][s]["unified/gain_bits"] - T[kr][s]["unified/gain_bits"] for s in T[k] if cond(s) == g and s in T[kr] and "unified/gain_bits" in T[k][s] and "unified/gain_bits" in T[kr][s]]
                out["contrasts"][f"{sp['architecture']}|{sp['adaptation']}|{sp['objective']}|{g}|pretrained-random"] = boot(d)
    for k in find(lambda k: k.startswith("A_TIME|seed3401|") and '"lag_local_tokens"' in k and '"window": "full"' in k):
        sp = json.loads(k.split("|", 2)[2]); kl = f"A_TIME|seed3401|" + json.dumps({**sp, "architecture": "legacy_pool4"}, sort_keys=True)
        if kl in T:
            for g in ("HC", "CI", "HCv"):
                d = [T[k][s]["unified/gain_bits"] - T[kl][s]["unified/gain_bits"] for s in T[k] if cond(s) == g and s in T[kl] and "unified/gain_bits" in T[k][s] and "unified/gain_bits" in T[kl][s]]
                out["contrasts"][f"lag_local-legacy|{sp['objective']}|{g}"] = boot(d)
    # HC-v age with corrected ages (and HC, CI for reference)
    age = {m["subject_uid"]: m["age_years"] for m in man if m["entity_type"] == "human"}
    for k in find(lambda k: (k.startswith("A_TIME|seed3401|") and '"window": "full"' in k) or (k.startswith("B_FM|seed3401|") and '"pretrained_frozen"' in k and '"reve"' in k) or k == "LIN_E9|seed0|envelope|full"):
        r = {}
        for g in ("HC", "CI", "HCv"):
            ss = [s for s in T[k] if cond(s) == g and age.get(s) is not None and "unified/gain_bits" in T[k][s]]
            r[g] = ols_boot(np.array([[age[s]] for s in ss]), [T[k][s]["unified/gain_bits"] for s in ss], ["age_years"])
        out["hcv_age"][k] = r
    # legacy (n=95 mixed) vs corrected, for the published configurations
    old = json.load(open(os.path.join(REPO, "results", "auditory_alignment_v2", "aggregate.json")))
    out["legacy_aggregate_sha256"] = {p: hashlib.sha256(open(os.path.join(REPO, p), "rb").read()).hexdigest()
                                      for p in ("results/auditory_alignment_v2/aggregate.json", "docs/auditory_alignment_v2/FULL_RESULTS.md")}
    json.dump(out, open(os.path.join(RES, "federici_reaggregate.json"), "w"), indent=1, default=float)
    # ---------------------------------------------------------------- receipt
    E = out["entities"]; L = []; w = L.append
    w("# Federici 实体/身份重汇总回执（ALN3 R_FEDERICI；自动生成）\n")
    w(f"生成 {out['generated']}。依据：ALN3 包 docs/02 与增补 01。只重汇总已有预测，不重训、不改候选池。\n")
    w(f"- 独立儿童：{E['independent_children']}（{E['children_by_condition']}）；幻影实体 {E['phantom_entities']} 个，{E['phantom_sessions']} 次会话。")
    w("- HC-v 与 HC 为不同身份（元信息中无身份重叠证据），不做同儿童配对；HC-v 年龄取元信息 `Nvocod` 行（按序号推定）。")
    w("- 每个配置：单元内逐记录度量 → 配置内单元平均 → 儿童内平均，儿童等权；区间为儿童 bootstrap（以已训练模型为条件）。")
    w(f"- 旧表 hash：{json.dumps(out['legacy_aggregate_sha256'])}（旧表不覆写；旧 n=95 混合表标记 legacy_mixed_entities）。\n")
    w("## 主要配置（seed 3401；统一读出 gain，比特）\n\n| 配置 | HC | CI | HC-v | CI − HC（独立组） | HC-v − HC（独立组） | 人类合并（儿童等权） | 幻影实体（会话范围） |\n|---|---|---|---|---|---|---|---|")
    def lab(k):
        if k.startswith("LIN_E9"):
            return "线性参照 E9 · " + k.split("|", 2)[2]
        fam, seed, sp = k.split("|", 2); sp = json.loads(sp)
        return f"{fam} · " + " · ".join(str(sp.get(f)) for f in ("architecture", "adaptation", "window", "pairing", "objective") if sp.get(f) is not None)
    keys = [k for k in out["configs"] if k.startswith(("A_TIME|seed3401|", "B_FM|seed3401|", "S_CONTROLS|seed3401|", "A_TARGET_TIME|seed3401|")) or k.startswith("LIN_E9")]
    for k in sorted(keys, key=lambda k: (k.split("|")[0], lab(k))):
        c = out["configs"][k]; g = "unified/gain_bits"; ph = out["phantom"].get(k)
        w(f"| {lab(k)} | {fmt(c['HC'][g])} (n={c['HC']['n_children']}) | {fmt(c['CI'][g])} (n={c['CI']['n_children']}) | {fmt(c['HC-v'][g])} (n={c['HC-v']['n_children']}) | "
          f"{fmt(c['CI_minus_HC'][g])} | {fmt(c['HCv_minus_HC_independent'][g])} | {fmt(c['human_pool_child_equal'][g])} | "
          + (f"{ph['entity_mean_gain']:.3f}（{ph['session_min']:.3f} 至 {ph['session_max']:.3f}，{ph['n_sessions']} 次）" if ph else "–") + " |")
    w("\n## 同身份配对差（统一读出 gain）\n\n| 对比 | 差值 [95% CI] | n |\n|---|---|---|")
    for k, v in sorted(out["contrasts"].items()):
        w(f"| {k} | {fmt(v)} | {v.get('n')} |")
    w("\n## 年龄斜率（更正后的年龄；统一读出 gain 对年龄，组内）\n\n| 配置 | HC | CI | HC-v |\n|---|---|---|---|")
    for k, r in out["hcv_age"].items():
        w(f"| {lab(k)} | " + " | ".join(f"{fmt(r[g].get('coef', {}).get('age_years'))} (n={r[g].get('n')})" for g in ("HC", "CI", "HCv")) + " |")
    w("\n逐儿童长表与身份表留在 `private/auditory_alignment_v3/reaggregate/`。")
    open(DOC, "w").write("\n".join(L) + "\n")
    print(f"done in {time.time() - t0:.0f}s; configs {len(out['configs'])}; children {E['independent_children']}")


if __name__ == "__main__":
    main()
