"""ALN2 supplementary item 1: analyses the package requires beyond the training units (no new training).

  1. Raw-EEG linear baseline: the kernel-CS round's E9 linear reference (ridge from raw EEG lags to the target; no seeds, no
     training) - its test participants, candidate sets and segment counts are identical to ALN2's in every compared cell
     (checked 2026-10-10: 25/25). Its window definitions are the previous round's. Paired contrasts against fixed ALN2
     configurations.
  2. Reference risks (package §7.2): R_true, R_mismatch and the uniform-candidate risk log2(K) per participant.
  3. Group-stratified results and group differences for a fixed set of configurations (declared below, not chosen on
     results); Federici's phantom-head 'Artifact' recordings are reported separately and never pooled with participants.
  4. Development / function (fixed method, package §5.6/§7.6): private children (age, HA, HA duration); Federici (age within
     HC / CI; behavioural accuracy); DTU (SRT given age + PTA); FAU CI (HSM given age + CI experience). Nested LOO-OLS as in
     the kernel-CS round (step risks; negative difference = the added block improves held-out prediction).
  5. Split-half reliability (pooled and within group): continuous - true-EEG rank percentile of the first vs second half of
     each participant's test queries (recording order); private - head gain over the base rate per half.
Resampling unit = participant (percentile bootstrap, 4000). Intervals condition on the fitted models.

Usage: python -m auditory_alignment_v2.analysis_item1 [--seeds 3401[,3407,3413]]
Outputs: results/auditory_alignment_v2/item1_analyses.json (aggregates only), docs/auditory_alignment_v2/ITEM1_ANALYSES.md.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment.aggregate import boot, nested_models, ols_boot, unit_rows
from .aggregate import PRIV, RES, cfg_key, key, load, rows_of, specs_of, table

DOC = os.path.join(os.path.dirname(RES).replace("results", "docs"), "auditory_alignment_v2", "ITEM1_ANALYSES.md")
KCS = os.path.join(os.path.dirname(PRIV), "auditory_alignment_kernel_cs")
NB = 4000
REF_TARGET = {"fau": "local", "dtu": "local", "federici": "envelope"}


def fmt(s, d=3):
    return "–" if not s or s.get("est") is None else f"{s['est']:.{d}f} [{s['ci_low']:.{d}f}, {s['ci_high']:.{d}f}]"


def diff_ind(a, b, seed=0):
    """difference of means between independent participant sets (bootstrap each set)."""
    a, b = np.asarray([x for x in a if x is not None and np.isfinite(x)]), np.asarray([x for x in b if x is not None and np.isfinite(x)])
    if len(a) < 3 or len(b) < 3:
        return {"est": None, "n_a": len(a), "n_b": len(b)}
    r = np.random.default_rng(seed)
    bs = a[r.integers(0, len(a), (NB, len(a)))].mean(1) - b[r.integers(0, len(b), (NB, len(b)))].mean(1)
    return {"est": float(a.mean() - b.mean()), "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5)), "n_a": len(a), "n_b": len(b)}


def corr_boot(x, y, seed=0):
    x, y = np.asarray(x, float), np.asarray(y, float); ok = np.isfinite(x) & np.isfinite(y); x, y = x[ok], y[ok]
    if len(x) < 6:
        return {"est": None, "n": int(len(x))}
    r = np.random.default_rng(seed); bs = []
    for _ in range(NB):
        i = r.integers(0, len(x), len(x))
        if np.std(x[i]) > 0 and np.std(y[i]) > 0:
            bs.append(np.corrcoef(x[i], y[i])[0, 1])
    rr = float(np.corrcoef(x, y)[0, 1])
    sb = lambda v: 2 * v / (1 + v)
    return {"est": rr, "ci_low": float(np.percentile(bs, 2.5)), "ci_high": float(np.percentile(bs, 97.5)), "n": int(len(x)),
            "spearman_brown": float(sb(rr)), "sb_ci_low": float(sb(np.percentile(bs, 2.5))), "sb_ci_high": float(sb(np.percentile(bs, 97.5)))}


def extra_rows(rec):
    """per participant: uniform-candidate risk log2(K) and half metrics needed here (taken from the unit record)."""
    out = {}
    for pid, r in rec.get("eval", {}).get("per_participant", {}).items():
        x = {}
        for rd in ("unified", "native"):
            reg = r.get(f"{rd}/regular")
            if isinstance(reg, dict) and reg.get("n_candidates"):
                x["uniform_bits"] = float(np.log2(reg["n_candidates"]))
            for h in (0, 1):
                v = r.get(f"{rd}/regular_half{h}")
                if isinstance(v, dict):
                    x[f"{rd}/half{h}/rank_pct"] = float(v["rank_pct"])
        for h in (0, 1):
            for k in ("head_gain_vs_base_half", "native_gain_half"):
                if isinstance(r.get(f"{k}{h}"), (int, float)):
                    x[f"{k}{h}"] = float(r[f"{k}{h}"])
        for k in ("age_months", "duration_months"):
            if isinstance(r.get(k), (int, float)):
                x[k] = float(r[k])
        out[pid] = x
    return out


def participant_table(plan, recs, seeds):
    """cfg -> pid -> metric (rows_of metrics + extra_rows), averaged over the configuration's units."""
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list))); group = {}
    for row in plan:
        if row["seed"] not in seeds or row["experiment_id"] not in recs:
            continue
        rec = recs[row["experiment_id"]]; src = recs.get(rec.get("reuse_of"), rec) if rec.get("reuse_of") else rec
        rs = rows_of(rec, recs)
        if rs is None:
            continue
        ex = extra_rows(src); k = cfg_key(row)
        for pid, m in rs.items():
            group[(row["dataset"], pid)] = m.get("group")
            for mm, v in {**m, **ex.get(pid, {})}.items():
                if mm != "group" and v is not None and np.isfinite(v):
                    T[k][pid][mm].append(v)
    return {k: {p: {m: float(np.mean(v)) for m, v in ms.items()} for p, ms in pids.items()} for k, pids in T.items()}, group


def linear_table():
    """E9 linear reference of the kernel-CS round: 'LIN|dataset|target|window' -> pid -> metric."""
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list))); group = {}
    for p in glob.glob(os.path.join(KCS, "units_linear", "*.json")):
        if p.endswith("FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") != "complete":
            continue
        j = r["job"]; k = f"LIN|{j['dataset']}|{j['target']}|{j['window']}"
        rows = unit_rows(r); ex = extra_rows(r)
        for pid, m in rows.items():
            group[(j["dataset"], pid)] = m.get("group")
            for mm, v in {**m, **ex.get(pid, {})}.items():
                if mm != "group" and v is not None and np.isfinite(v):
                    T[k][pid][mm].append(v)
    return {k: {p: {m: float(np.mean(v)) for m, v in ms.items()} for p, ms in pids.items()} for k, pids in T.items()}, group


def paired(Pa, Pb, m):
    d = [Pa[p][m] - Pb[p][m] for p in Pa if p in Pb and m in Pa[p] and m in Pb[p]]
    return boot(d) if d else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", default="3401"); args = ap.parse_args()
    seeds = {int(s) for s in args.seeds.split(",")}
    t0 = time.time()
    plan, scope, recs = load()
    P, group = participant_table(plan, recs, seeds)
    L, lgroup = linear_table()
    group.update({k: v for k, v in lgroup.items() if k not in group})
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "seeds": sorted(seeds), "linear": {}, "reference_risks": {}, "groups": {}, "development_function": {}, "reliability": {}}
    W = []; w = W.append
    w("# ALN2 补充第 1 项：线性参照、参照风险、组别、发育/功能与重复性（自动生成）\n")
    w(f"生成时间 {out['generated']}；seed {sorted(seeds)}。参与者均值与参与者 bootstrap 95% 区间（以已训练模型为条件）。gain = 错配 EEG − 真实 EEG 的 log loss（比特/查询，统一读出）。"
      "配置事先固定（见代码文档），不按结果挑选。Federici 的幻影头（Artifact）记录单列，不与参与者合并。\n")

    def g(fam, ds, **m):
        x = next((s for s in specs_of(plan, fam, ds) if all(s.get(k) == v for k, v in m.items())), None)
        return key(fam, ds, **x) if x else None

    # fixed configuration set (declared before computing)
    def fixed(ds):
        t = REF_TARGET[ds]; c = {}
        for o in ("NCE", "CS_SINGLE"):
            for a in ("lag_local_tokens", "density_tokens", "legacy_pool4"):
                c[f"A_TIME {a} full {o}"] = g("A_TIME", ds, architecture=a, window="full", objective=o, target=t)
            for arch in ("cbramod", "reve"):
                for ad in ("pretrained_frozen", "pretrained_peft", "pretrained_full", "random_full"):
                    c[f"B_FM {arch} {ad} {o}"] = g("B_FM", ds, architecture=arch, adaptation=ad, objective=o)
            c[f"S_CONTROLS wrong-pair {o}"] = g("S_CONTROLS", ds, pairing="declared_wrong_pair", objective=o)
        return {k: v for k, v in c.items() if v}

    # ---------------------------------------------------------------- 1 + 2: linear baseline and reference risks
    w("## 1. 不训练的原始 EEG 线性参照（上一轮 E9，复用）与参照风险\n")
    w("E9 与本轮在全部可比较的 25 个外折×内容折中，测试参与者、候选集与片段数完全一致；E9 的时间窗按上一轮的定义。\n")
    for ds in ("fau", "dtu", "federici"):
        t = REF_TARGET[ds]; lk = f"LIN|{ds}|{t}|full"
        if lk not in L:
            continue
        Lf = {p: v for p, v in L[lk].items() if group.get((ds, p)) != "Artifact"}
        w(f"\n### {ds}（目标 {t}，完整窗）\n\n| 配置 | n | 统一读出 gain | 真实风险 R_true | 错配风险 R_mismatch | 均匀候选风险 log2 K | 减线性参照（配对 gain 差） |\n|---|---|---|---|---|---|---|")
        rows = [("线性参照 E9", Lf)] + [(lab, {p: v for p, v in P.get(k, {}).items() if group.get((ds, p)) != "Artifact"}) for lab, k in fixed(ds).items()]
        for lab, T_ in rows:
            if not T_:
                continue
            gb = boot([v["unified/gain_bits"] for v in T_.values() if "unified/gain_bits" in v])
            rt = boot([v["unified/regular/logloss_bits"] for v in T_.values() if "unified/regular/logloss_bits" in v])
            rm = boot([v["unified/mismatched_eeg/logloss_bits"] for v in T_.values() if "unified/mismatched_eeg/logloss_bits" in v])
            un = boot([v["uniform_bits"] for v in T_.values() if "uniform_bits" in v])
            c = None if lab.startswith("线性") else paired(T_, Lf, "unified/gain_bits")
            out["linear"][f"{ds}|{lab}"] = {"gain": gb, "R_true": rt, "R_mismatch": rm, "uniform": un, "minus_linear": c}
            w(f"| {lab} | {gb.get('n', 0)} | {fmt(gb)} | {fmt(rt, 2)} | {fmt(rm, 2)} | {fmt(un, 2)} | {fmt(c) if c else '–'} |")
        # windows of the linear reference
        wl = []
        for win in ("early", "late", "joint"):
            k2 = f"LIN|{ds}|{t}|{win}"
            if k2 in L:
                b2 = boot([v["unified/gain_bits"] for p, v in L[k2].items() if group.get((ds, p)) != "Artifact" and "unified/gain_bits" in v])
                wl.append(f"{win} {fmt(b2)}"); out["linear"][f"{ds}|LIN {win}"] = b2
        if wl:
            w(f"\n线性参照其他时间窗：{'；'.join(wl)}。")
    # private
    w("\n### 私有儿童当前类别（head AUC）\n\n| 配置 | n | head AUC | head gain（比特） | 减线性参照（配对 AUC 差） |\n|---|---|---|---|---|")
    for win in ("full", "early", "late", "joint"):
        lk = f"LIN|private_bdf|current_class|{win}"
        if lk not in L:
            continue
        rows = [(f"线性参照 E9 · {win}", L[lk])]
        for a in ("lag_local_tokens", "density_tokens"):
            for o in ("NCE", "CS_SINGLE"):
                k = g("D_TASK_LOCAL", "private_bdf", architecture=a, window=win, objective=o)
                if k: rows.append((f"D_TASK_LOCAL {a} · {win} · {o}", P.get(k, {})))
        for lab, T_ in rows:
            au = boot([v["head_auc"] for v in T_.values() if "head_auc" in v]); hg = boot([v["head_gain_vs_base_bits"] for v in T_.values() if "head_gain_vs_base_bits" in v])
            c = None if lab.startswith("线性") else paired(T_, L[lk], "head_auc")
            out["linear"][f"private|{lab}"] = {"head_auc": au, "head_gain": hg, "minus_linear_auc": c}
            w(f"| {lab} | {au.get('n', 0)} | {fmt(au)} | {fmt(hg)} | {fmt(c) if c else '–'} |")

    # ---------------------------------------------------------------- 3: groups
    w("\n## 2. 按测试组的结果与组间差（统一读出 gain）\n\n组间差为独立参与者集合的均值差（各自 bootstrap）。组别模式描述的是这些模型与读出，不是人群可用信息的结论。\n")
    for ds, pairs_ in (("fau", (("ci", "th"), ("ha", "th"), ("ci", "ha"))), ("dtu", (("hi", "nh"),)), ("federici", (("CI", "HC"), ("HC-v", "HC")))):
        fx = fixed(ds); grs = sorted({gr for (d, p), gr in group.items() if d == ds and gr})
        w(f"\n### {ds}\n\n| 配置 | " + " | ".join(f"{gr}" for gr in grs) + " | " + " | ".join(f"{a} − {b}" for a, b in pairs_) + " |\n|" + "---|" * (1 + len(grs) + len(pairs_)))
        for lab, k in [("线性参照 E9", f"LIN|{ds}|{REF_TARGET[ds]}|full")] + list(fx.items()):
            T_ = L.get(k) if lab.startswith("线性") else P.get(k)
            if not T_:
                continue
            by = {gr: [v["unified/gain_bits"] for p, v in T_.items() if group.get((ds, p)) == gr and "unified/gain_bits" in v] for gr in grs}
            cells = [fmt(boot(by[gr])) + f" (n={len(by[gr])})" for gr in grs]
            dd = [diff_ind(by.get(a, []), by.get(b, [])) for a, b in pairs_]
            out["groups"][f"{ds}|{lab}"] = {"by_group": {gr: boot(by[gr]) for gr in grs}, "diffs": {f"{a}-{b}": d for (a, b), d in zip(pairs_, dd)}}
            w(f"| {lab} | " + " | ".join(cells) + " | " + " | ".join(fmt(d) for d in dd) + " |")
    # private groups
    w("\n### 私有儿童（head AUC）\n\n| 配置 | HA | NH | HA − NH |\n|---|---|---|---|")
    for win in ("full", "late"):
        for lab, k in ((f"D_TASK_LOCAL lag_local · {win} · NCE", g("D_TASK_LOCAL", "private_bdf", architecture="lag_local_tokens", window=win, objective="NCE")),
                       (f"D_TASK_LOCAL lag_local · {win} · CS_SINGLE", g("D_TASK_LOCAL", "private_bdf", architecture="lag_local_tokens", window=win, objective="CS_SINGLE"))):
            T_ = P.get(k, {})
            by = {gr: [v["head_auc"] for p, v in T_.items() if group.get(("private_bdf", p)) == gr and "head_auc" in v] for gr in ("HA", "NH")}
            d = diff_ind(by["HA"], by["NH"]); out["groups"][f"private|{lab}"] = {"HA": boot(by["HA"]), "NH": boot(by["NH"]), "HA-NH": d}
            w(f"| {lab} | {fmt(boot(by['HA']))} | {fmt(boot(by['NH']))} | {fmt(d)} |")

    # ---------------------------------------------------------------- 4: development / function
    w("\n## 3. 发育与功能（固定方法之后；嵌套 LOO-OLS：协变量 C → C + 整体对齐 → + 早/晚结构；差值为大模型 − 小模型的留一平方误差，负值 = 加入的块改善了留一预测）\n")
    dfun = out["development_function"]
    # private: age / HA / duration, per window
    w("\n### 私有儿童：head gain 与年龄、HA、HA 佩戴时长（每个时间窗分别回归）\n\n| 配置 | 年龄斜率（全部，控制 HA） | HA 系数 | HA 内：年龄斜率 | HA 内：佩戴时长斜率 |\n|---|---|---|---|---|")
    for o in ("NCE", "CS_SINGLE"):
        for win in ("full", "early", "late", "joint"):
            k = g("D_TASK_LOCAL", "private_bdf", architecture="lag_local_tokens", window=win, objective=o)
            T_ = P.get(k, {})
            ids = [p for p in T_ if "age_months" in T_[p] and "head_gain_vs_base_bits" in T_[p]]
            X = np.array([[T_[p]["age_months"], float(group.get(("private_bdf", p)) == "HA")] for p in ids]); y = [T_[p]["head_gain_vs_base_bits"] for p in ids]
            a = ols_boot(X, y, ["age_months", "HA"])
            ha = [p for p in ids if group.get(("private_bdf", p)) == "HA" and "duration_months" in T_[p]]
            b = ols_boot(np.array([[T_[p]["age_months"], T_[p]["duration_months"]] for p in ha]), [T_[p]["head_gain_vs_base_bits"] for p in ha], ["age_months", "duration_months"])
            dfun[f"private|lag_local|{win}|{o}"] = {"all": a, "HA": b}
            c = lambda r, n: fmt(r.get("coef", {}).get(n), 5)
            w(f"| lag_local · {win} · {o}（n={a.get('n')}，HA n={b.get('n')}） | {c(a, 'age_months')} | {c(a, 'HA')} | {c(b, 'age_months')} | {c(b, 'duration_months')} |")
    # Federici
    try:
        from auditory_alignment.aggregate import federici_participants
        fed = {p["id"]: p for p in federici_participants()}
    except Exception as ex:  # covariates optional; reported
        fed = {}; dfun["federici_error"] = repr(ex)
    if fed:
        w("\n### Federici：与年龄（HC、CI 组内）和行为正确率的关系\n\n| 配置 | HC 年龄斜率 | CI 年龄斜率 | 行为正确率：C→C+整体 | +结构 |\n|---|---|---|---|---|")
        for lab, k in (("A_TIME lag_local full NCE", g("A_TIME", "federici", architecture="lag_local_tokens", window="full", objective="NCE", target="envelope")),
                       ("A_TIME density full NCE", g("A_TIME", "federici", architecture="density_tokens", window="full", objective="NCE", target="envelope")),
                       ("B_FM reve pretrained_frozen NCE", g("B_FM", "federici", architecture="reve", adaptation="pretrained_frozen", objective="NCE")),
                       ("线性参照 E9 full", "LIN|federici|envelope|full")):
            T_ = L.get(k) if k and k.startswith("LIN") else P.get(k, {})
            if not T_:
                continue
            sl = {}
            for gr in ("HC", "CI"):
                ids = [p for p in T_ if p in fed and fed[p]["group"] == gr and fed[p].get("age_years") is not None and "unified/gain_bits" in T_[p]]
                sl[gr] = ols_boot(np.array([[fed[p]["age_years"]] for p in ids]), [T_[p]["unified/gain_bits"] for p in ids], ["age_years"])
            ba = [p for p in T_ if p in fed and fed[p].get("behav_acc") is not None and fed[p]["group"] in ("HC", "CI") and fed[p].get("age_years") is not None]
            st = None
            if not k.startswith("LIN"):
                kj = k.replace('"window": "full"', '"window": "joint"'); ke = k.replace('"window": "full"', '"window": "early"'); kl = k.replace('"window": "full"', '"window": "late"')
                if all(x in P for x in (kj, ke, kl)) and kj != k:
                    st = np.array([[P[ke].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan),
                                    P[kl].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan)] for p in ba])
            blocks = [np.array([[fed[p]["age_years"], float(fed[p]["group"] == "CI")] for p in ba]), np.array([T_[p].get("unified/gain_bits", np.nan) for p in ba])[:, None]]
            if st is not None:
                blocks.append(st)
            nm = nested_models([fed[p]["behav_acc"] for p in ba], blocks)
            dfun[f"federici|{lab}"] = {"age_slope": sl, "behav_acc": nm}
            w(f"| {lab} | {fmt(sl['HC'].get('coef', {}).get('age_years'))} (n={sl['HC'].get('n')}) | {fmt(sl['CI'].get('coef', {}).get('age_years'))} (n={sl['CI'].get('n')}) | "
              f"{fmt(nm.get('step1_minus_step0'), 4)} (n={nm.get('n')}) | {fmt(nm.get('step2_minus_step1'), 4) if 'step2_minus_step1' in nm else '–'} |")
    # DTU SRT
    try:
        import pandas as pd
        tsv = pd.read_csv("/projects/EEG-foundation-model/auditory_public/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv", sep="\t")
        aud = [c for c in tsv.columns if c.startswith("audiogram_") and any(f"_{f}Hz" in c for f in (500, 1000, 2000, 4000))]
        dcov = {r.participant_id: {"age": r.age, "srt": r.speech_reception_thresholds, "pta": np.nanmean([getattr(r, c) for c in aud])} for r in tsv.itertuples()}
        w("\n### DTU：言语接受阈 SRT（协变量：年龄、PTA）\n\n| 配置 | n | C→C+整体对齐 | +早/晚结构 |\n|---|---|---|---|")
        for o in ("NCE", "CS_SINGLE"):
            for a in ("lag_local_tokens", "density_tokens"):
                k = g("A_TIME", "dtu", architecture=a, window="full", objective=o, target="local"); kj = g("A_TIME", "dtu", architecture=a, window="joint", objective=o, target="local")
                ke = g("A_TIME", "dtu", architecture=a, window="early", objective=o, target="local"); kl = g("A_TIME", "dtu", architecture=a, window="late", objective=o, target="local")
                T_ = P.get(k, {}); ids = [p for p in T_ if p in dcov]
                st = np.array([[P[ke].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan),
                                P[kl].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan)] for p in ids])
                nm = nested_models([dcov[p]["srt"] for p in ids], [np.array([[dcov[p]["age"], dcov[p]["pta"]] for p in ids], float),
                                                                   np.array([T_[p].get("unified/gain_bits", np.nan) for p in ids])[:, None], st])
                dfun[f"dtu_srt|{a}|{o}"] = nm
                w(f"| A_TIME {a} · {o} | {nm.get('n')} | {fmt(nm.get('step1_minus_step0'), 3)} | {fmt(nm.get('step2_minus_step1'), 3)} |")
    except Exception as ex:
        dfun["dtu_error"] = repr(ex)
    # FAU CI HSM
    try:
        from auditory_c3.h7_function import _logit_pct, _num
        t4 = {r["ID"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(PRIV), "auditory_c3", "jehn_behaviour", "table4_parsed.csv")))}
        w("\n### FAU CI：HSM 言语理解（logit；协变量：年龄、CI 使用年限）\n\n| 配置 | n | C→C+整体对齐 | +早/晚结构 |\n|---|---|---|---|")
        for o in ("NCE", "CS_SINGLE"):
            for a in ("lag_local_tokens", "density_tokens"):
                k = g("A_TIME", "fau", architecture=a, window="full", objective=o, target="local"); kj = g("A_TIME", "fau", architecture=a, window="joint", objective=o, target="local")
                ke = g("A_TIME", "fau", architecture=a, window="early", objective=o, target="local"); kl = g("A_TIME", "fau", architecture=a, window="late", objective=o, target="local")
                T_ = P.get(k, {}); ids = [p for p in T_ if p in t4 and np.isfinite(_num(t4[p]["HSM"]))]
                st = np.array([[P[ke].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan),
                                P[kl].get(p, {}).get("unified/regular/logloss_bits", np.nan) - P[kj].get(p, {}).get("unified/regular/logloss_bits", np.nan)] for p in ids])
                Cm = np.array([[_num(t4[p]["Age"]), max(_num(t4[p]["CIexpR"]), _num(t4[p]["CIexpL"]))] for p in ids], float)
                nm = nested_models(_logit_pct(np.array([_num(t4[p]["HSM"]) for p in ids])), [Cm, np.array([T_[p].get("unified/gain_bits", np.nan) for p in ids])[:, None], st])
                dfun[f"fau_ci_hsm|{a}|{o}"] = nm
                w(f"| A_TIME {a} · {o} | {nm.get('n')} | {fmt(nm.get('step1_minus_step0'), 3)} | {fmt(nm.get('step2_minus_step1'), 3)} |")
    except Exception as ex:
        dfun["fau_error"] = repr(ex)

    # ---------------------------------------------------------------- 5: reliability
    w("\n## 4. 个体重复性（前一半与后一半测试查询；合并与组内）\n\n连续任务：真实 EEG 的 rank 百分位（越低越好）两半之间的 Pearson r 及 Spearman–Brown 全长值；私有：head gain 两半。"
      "组别混合造成的稳定分数不等于组内个体能力可靠，因此同时给组内值。\n\n| 配置 | 合并 r [CI]（SB） | 组内 r（各组） |\n|---|---|---|")
    rel = out["reliability"]
    for ds in ("fau", "dtu", "federici"):
        for lab, k in [(f"{ds} 线性参照 E9", f"LIN|{ds}|{REF_TARGET[ds]}|full")] + [(f"{ds} {l}", k) for l, k in fixed(ds).items() if "NCE" in l and ("lag_local" in l or "density" in l or "reve pretrained_frozen" in l or "cbramod pretrained_peft" in l)]:
            T_ = L.get(k) if k.startswith("LIN") else P.get(k, {})
            if not T_:
                continue
            ids = [p for p in T_ if group.get((ds, p)) != "Artifact" and "unified/half0/rank_pct" in T_[p] and "unified/half1/rank_pct" in T_[p]]
            pooled = corr_boot([T_[p]["unified/half0/rank_pct"] for p in ids], [T_[p]["unified/half1/rank_pct"] for p in ids])
            wg = {}
            for gr in sorted({group.get((ds, p)) for p in ids}):
                gi = [p for p in ids if group.get((ds, p)) == gr]
                wg[gr] = corr_boot([T_[p]["unified/half0/rank_pct"] for p in gi], [T_[p]["unified/half1/rank_pct"] for p in gi])
            rel[lab] = {"pooled": pooled, "within": wg}
            sb = f"（SB {pooled['spearman_brown']:.2f}）" if pooled.get("est") is not None else ""
            w(f"| {lab} | {fmt(pooled, 2)}{sb} | " + "；".join(f"{gr} {fmt(v, 2)}" for gr, v in wg.items()) + " |")
    for o in ("NCE", "CS_SINGLE"):
        k = g("D_TASK_LOCAL", "private_bdf", architecture="lag_local_tokens", window="full", objective=o); T_ = P.get(k, {})
        ids = [p for p in T_ if "head_gain_vs_base_half0" in T_[p] and "head_gain_vs_base_half1" in T_[p]]
        pooled = corr_boot([T_[p]["head_gain_vs_base_half0"] for p in ids], [T_[p]["head_gain_vs_base_half1"] for p in ids])
        wg = {gr: corr_boot([T_[p]["head_gain_vs_base_half0"] for p in ids if group.get(("private_bdf", p)) == gr],
                            [T_[p]["head_gain_vs_base_half1"] for p in ids if group.get(("private_bdf", p)) == gr]) for gr in ("HA", "NH")}
        rel[f"private lag_local full {o}"] = {"pooled": pooled, "within": wg}
        w(f"| 私有 lag_local · full · {o}（head gain） | {fmt(pooled, 2)} | " + "；".join(f"{gr} {fmt(v, 2)}" for gr, v in wg.items()) + " |")

    os.makedirs(RES, exist_ok=True)
    json.dump(out, open(os.path.join(RES, "item1_analyses.json"), "w"), indent=1, default=float)
    open(DOC, "w").write("\n".join(W) + "\n")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
