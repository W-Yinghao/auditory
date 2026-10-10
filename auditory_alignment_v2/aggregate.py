"""ALN2 aggregation (interim or final): neutral tables over every completed unit, no selection.

Resampling unit = participant: per participant, a configuration's metrics are averaged over its units (content folds; one
seed), then summarised with a participant bootstrap (95% percentile CI). Contrasts are paired per participant (participants
present in both configurations). Main tables use the registered seed scope (seed 3401, user 2026-10-07); A_TIME, the only
family run with 3 seeds, also gets a seed-stability table. Metric definitions are those of the kernel-CS round
(auditory_alignment.aggregate.unit_rows): gain_bits = logloss(mismatched EEG) - logloss(true EEG), bits per query, same
candidates and calibration; rank_gain, hard_gain_bits; private head/native AUC and gain over the base rate; history minus twin.

Usage: python -m auditory_alignment_v2.aggregate
Outputs: results/auditory_alignment_v2/aggregate.json (aggregates only), docs/auditory_alignment_v2/FULL_RESULTS.md,
private/auditory_alignment_v2/agg/participant_table.json (per participant; stays private).
"""
from __future__ import annotations

import glob
import json
import os
import time
from collections import Counter, defaultdict

import numpy as np

from auditory_alignment.aggregate import boot, unit_rows

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(REPO, "AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006")
PLAN = os.path.join(PKG, "plans", "planned_comparisons.jsonl")
PRIV = os.path.join(REPO, "private", "auditory_alignment_v2")
RES = os.path.join(REPO, "results", "auditory_alignment_v2")
DOC = os.path.join(REPO, "docs", "auditory_alignment_v2", "FULL_RESULTS.md")
NB = 4000

FM_FAMS = {"B_FM", "D_FM_GENERIC", "B_AUDITORY_CONTINUE", "D_FM_PUBLIC", "C_ATTENTION", "C_SELECTION", "C_COVERAGE"}
CONT = ("unified/gain_bits", "native/gain_bits", "unified/regular/top1", "unified/regular/rank_pct", "unified/hard_gain_bits",
        "attention/unified/accuracy", "attention/native/accuracy", "attention/trained/accuracy", "probe/gain_bits", "probe/regular/top1",
        "attention/probe/accuracy")
PRIVM = ("head_auc", "head_gain_vs_base_bits", "native_auc", "native_gain_vs_base_bits", "hist_minus_twin_bits", "probe_auc", "probe_gain_vs_base_bits")
LEGACY = os.path.join(PRIV, "legacy_chmean_v1", "units")


def pboot(diffs, seed=0):
    return boot(diffs, seed)


def load(units_dir=None):
    plan = [json.loads(l) for l in open(PLAN)]
    scope = json.load(open(os.path.join(PRIV, "seed_scope.json")))
    recs = {}
    for p in glob.glob(os.path.join(units_dir or os.path.join(PRIV, "units"), "ALN2_*.json")):
        if p.endswith(".FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") == "complete":
            recs[r["experiment_id"]] = r
    return plan, scope, recs


def rows_of(rec, recs):
    """Per-participant metric rows of a unit (reuse rows resolve to their source unit)."""
    src = recs.get(rec.get("reuse_of"), rec) if rec.get("reuse_of") else rec
    if "eval" not in src:
        return None
    ev = src["eval"]
    if src.get("runner") == "run_adapt":  # C_ADAPT: support-fraction results on a fixed query
        out = {}
        for pid, r in ev["per_participant"].items():
            row = {"group": r.get("group")}
            for k, v in r.items():
                if k.startswith("support_") and isinstance(v, dict):
                    for rd in ("unified", "native"):
                        for m in ("gain_bits", "top1", "rank_pct", "auc", "gain_vs_base_bits"):
                            if isinstance(v.get(rd), dict) and isinstance(v[rd].get(m), (int, float)):
                                row[f"{k}/{rd}/{m}"] = float(v[rd][m])
            out[pid] = row
        return out
    out = unit_rows(src)
    cp = ev.get("channel_probe")  # channels-preserved linear-probe reference (amendment A1)
    if cp:
        for pid, r in cp.get("per_participant", {}).items():
            row = out.setdefault(pid, {"group": ev["per_participant"].get(pid, {}).get("group")})
            for k, v in r.items():
                if isinstance(v, dict):
                    for m, x in v.items():
                        if isinstance(x, (int, float)) and not isinstance(x, bool) and m not in ("n_candidates", "n_queries"):
                            row[f"{k}/{m}"] = float(x)
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    row[k] = float(v)
            if "probe/regular/logloss_bits" in row and "probe/mismatched_eeg/logloss_bits" in row:
                row["probe/gain_bits"] = row["probe/mismatched_eeg/logloss_bits"] - row["probe/regular/logloss_bits"]
                if "probe/hard/logloss_bits" in row:
                    row["probe/hard_gain_bits"] = float(np.log2(9)) - row["probe/hard/logloss_bits"]
        for pid, r in cp.get("attention_2afc", {}).items():
            out.setdefault(pid, {"group": ev["per_participant"].get(pid, {}).get("group")})["attention/probe/accuracy"] = r["probe"]["accuracy"]
    for pid, r in ev.get("attention_2afc_trained_score", {}).items():
        out.setdefault(pid, {"group": ev["per_participant"].get(pid, {}).get("group")})
        out[pid]["attention/trained/accuracy"] = r["accuracy"]
    for pid, r in ev.get("per_participant", {}).items():  # task-native private head (absent from the v1 key list)
        for k in ("native_auc", "native_gain_vs_base_bits"):
            if isinstance(r.get(k), (int, float)):
                out[pid][k] = float(r[k])
    return out


def cfg_key(row):
    return row["family_id"] + "|" + row["dataset"] + "|" + json.dumps(row["spec"], sort_keys=True)


def table(plan, recs, seeds):
    """cfg -> pid -> metric -> mean over the configuration's units; plus counts and group labels."""
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    n_units, n_plan, group = Counter(), Counter(), {}
    for row in plan:
        if row["seed"] not in seeds:
            continue
        k = cfg_key(row); n_plan[k] += 1
        rec = recs.get(row["experiment_id"])
        if rec is None:
            continue
        rs = rows_of(rec, recs)
        if rs is None:
            continue
        n_units[k] += 1
        for pid, m in rs.items():
            group[(row["dataset"], pid)] = m.get("group")
            for mm, v in m.items():
                if mm != "group" and v is not None and np.isfinite(v):
                    T[k][pid][mm].append(v)
    P = {k: {pid: {mm: float(np.mean(v)) for mm, v in ms.items()} for pid, ms in pids.items()} for k, pids in T.items()}
    return P, n_units, n_plan, group


def summ(P, k, metrics):
    if k not in P:
        return {}
    out = {}
    for m in metrics:
        x = [r[m] for r in P[k].values() if m in r]
        if x:
            out[m] = boot(x)
    return out


def contrast(P, a, b, m):
    if a not in P or b not in P:
        return None
    d = [P[a][p][m] - P[b][p][m] for p in P[a] if p in P[b] and m in P[a][p] and m in P[b][p]]
    return pboot(d) if d else None


def key(fam, ds, **spec):
    return fam + "|" + ds + "|" + json.dumps(spec, sort_keys=True)


def specs_of(plan, fam, ds):
    seen = []
    for r in plan:
        if r["family_id"] == fam and r["dataset"] == ds and r["spec"] not in seen:
            seen.append(r["spec"])
    return seen


def fmt(s, digits=3):
    if not s or s.get("est") is None:
        return "–"
    return f"{s['est']:.{digits}f} [{s['ci_low']:.{digits}f}, {s['ci_high']:.{digits}f}]"


def main():
    t0 = time.time()
    plan, scope, recs = load()
    seeds = set(scope["seeds"])
    P, n_units, n_plan, group = table(plan, recs, seeds)
    os.makedirs(RES, exist_ok=True); os.makedirs(os.path.join(PRIV, "agg"), exist_ok=True)
    json.dump({"participants": P, "groups": {f"{d}|{p}": g for (d, p), g in group.items()}},
              open(os.path.join(PRIV, "agg", "participant_table.json"), "w"))

    fams = sorted({r["family_id"] for r in plan})
    status = {f: {"units_done": sum(n_units[k] for k in n_units if k.startswith(f + "|")),
                  "units_in_scope": sum(n_plan[k] for k in n_plan if k.startswith(f + "|"))} for f in fams}
    agg = {"generated": time.strftime("%Y-%m-%d %H:%M"), "seed_scope": sorted(seeds), "status": status, "configs": {}, "contrasts": {}}
    for k in n_plan:
        ds = k.split("|")[1]
        agg["configs"][k] = {"units_done": n_units[k], "units_planned": n_plan[k], "n_participants": len(P.get(k, {})),
                             **summ(P, k, PRIVM if ds == "private_bdf" else CONT)}
    L = []
    w = L.append
    w("# ALN2 全部结果（自动生成；完成情况见第 0 节，未完成的族只含已完成单元）\n")
    w(f"生成时间：{agg['generated']}。范围：seed {sorted(seeds)}（A_TIME 另列 3 seed）。数值为参与者均值及参与者 bootstrap 95% 区间；"
      "对比为同一批参与者的配对差。gain = 错配 EEG 的 log loss − 真实 EEG 的 log loss（比特/查询，统一读出 unified 或原生读出 native）。"
      "单 seed 不含训练波动；区间以已训练模型为条件。\n")
    w("## 0. 完成情况\n\n| 族 | 已完成 / 范围内 |\n|---|---|")
    for f in fams:
        w(f"| {f} | {status[f]['units_done']} / {status[f]['units_in_scope']} |")
    w("")

    def cont_table(title, rows, extra_cols=(), A=None):
        A = agg["configs"] if A is None else A
        cols = ("unified/gain_bits", "native/gain_bits", "unified/regular/top1") + tuple(extra_cols)
        w(f"\n### {title}\n\n| 配置 | 单元 | n | " + " | ".join(cols) + " |\n|" + "---|" * (3 + len(cols)))
        for label, k in rows:
            a = A.get(k, {})
            if not a:
                continue
            w(f"| {label} | {a['units_done']}/{a['units_planned']} | {a['n_participants']} | " + " | ".join(fmt(a.get(c)) for c in cols) + " |")

    def priv_table(title, rows, A=None):
        A = agg["configs"] if A is None else A
        cols = PRIVM
        w(f"\n### {title}\n\n| 配置 | 单元 | n | " + " | ".join(cols) + " |\n|" + "---|" * (3 + len(cols)))
        for label, k in rows:
            a = A.get(k, {})
            if a:
                w(f"| {label} | {a['units_done']}/{a['units_planned']} | {a['n_participants']} | " + " | ".join(fmt(a.get(c)) for c in cols) + " |")

    def ctr(name, a, b, m="unified/gain_bits"):
        c = contrast(P, a, b, m)
        agg["contrasts"][f"{name} :: {m}"] = c
        return c

    # ---------------------------------------------------------------- A_TIME
    w("\n## 1. A_TIME：时间表示（小编码器，固定声音特征）")
    for ds in ("fau", "dtu", "federici"):
        for obj in ("NCE", "CS_SINGLE"):
            rows = []
            for s in specs_of(plan, "A_TIME", ds):
                if s["objective"] == obj:
                    rows.append((f"{s['architecture']} · {s['window']} · {s['target']}", key("A_TIME", ds, **s)))
            rows.sort()
            cont_table(f"A_TIME · {ds} · {obj}", rows, ("attention/unified/accuracy",) if ds != "federici" else ())
    w("\n**配对对比（统一读出 gain，比特）**\n\n| 对比 | 差值 [95% CI] | n |\n|---|---|---|")
    for ds in ("fau", "dtu", "federici"):
        for obj in ("NCE", "CS_SINGLE"):
            base = [s for s in specs_of(plan, "A_TIME", ds) if s["objective"] == obj]
            tgt = base[0]["target"] if base else None
            for s in base:
                if s["window"] == "full" and s["architecture"] != "legacy_pool4":
                    ref = dict(s, architecture="legacy_pool4")
                    c = ctr(f"A_TIME {ds} {obj} {s['architecture']} − legacy_pool4 (full)", key("A_TIME", ds, **s), key("A_TIME", ds, **ref))
                    if c: w(f"| {ds} · {obj} · {s['architecture']} − legacy_pool4（完整窗） | {fmt(c)} | {c['n']} |")
            for s in base:
                if s["window"] == "joint":
                    for other in ("full", "early", "late"):
                        c = ctr(f"A_TIME {ds} {obj} {s['architecture']} joint − {other}", key("A_TIME", ds, **s), key("A_TIME", ds, **dict(s, window=other)))
                        if c: w(f"| {ds} · {obj} · {s['architecture']}：joint − {other} | {fmt(c)} | {c['n']} |")
    # seed stability
    w("\n### A_TIME 的 seed 稳定性（3 seed）\n")
    by_cfg_seed = defaultdict(lambda: defaultdict(list))
    for r in plan:
        if r["family_id"] != "A_TIME" or r["experiment_id"] not in recs:
            continue
        rs = rows_of(recs[r["experiment_id"]], recs)
        if rs:
            v = [m["unified/gain_bits"] for m in rs.values() if "unified/gain_bits" in m]
            if v:
                by_cfg_seed[cfg_key(r)][r["seed"]].append(float(np.mean(v)))
    cfg_means = {k: {s: float(np.mean(v)) for s, v in d.items()} for k, d in by_cfg_seed.items() if len(d) == 3}
    seed_sd = [float(np.std(list(d.values()), ddof=1)) for d in cfg_means.values()]
    by_ds = defaultdict(list)
    for k, d in cfg_means.items():
        by_ds[k.split("|")[1] + "|" + json.loads(k.split("|")[2])["objective"]].append(np.mean(list(d.values())))
    between = [float(np.std(v, ddof=1)) for v in by_ds.values() if len(v) > 1]
    ranks = []
    for grp in by_ds:
        ks = [k for k in cfg_means if k.split("|")[1] + "|" + json.loads(k.split("|")[2])["objective"] == grp]
        if len(ks) > 2:
            M = np.array([[cfg_means[k][s] for s in (3401, 3407, 3413)] for k in ks])
            from scipy.stats import spearmanr
            ranks += [spearmanr(M[:, i], M[:, j])[0] for i, j in ((0, 1), (0, 2), (1, 2))]
    agg["a_time_seed_stability"] = {"n_configs": len(cfg_means), "median_seed_sd_bits": float(np.median(seed_sd)) if seed_sd else None,
                                    "median_between_config_sd_bits": float(np.median(between)) if between else None,
                                    "median_spearman_config_ranking_between_seeds": float(np.median(ranks)) if ranks else None}
    s_ = agg["a_time_seed_stability"]
    if s_["n_configs"]:
        w(f"{s_['n_configs']} 个配置有 3 个 seed。统一读出 gain 的配置均值：seed 间标准差中位数 {s_['median_seed_sd_bits']:.3f} 比特；"
          f"同一数据集·目标函数内配置间标准差中位数 {s_['median_between_config_sd_bits']:.3f} 比特；"
          f"两两 seed 之间配置排序的 Spearman 相关中位数 {s_['median_spearman_config_ranking_between_seeds']:.2f}。\n")

    # ---------------------------------------------------------------- other A families and controls
    w("\n## 2. A_TARGET_TIME、A_ANCHOR、S_CONTROLS")
    for fam, lab in (("A_TARGET_TIME", lambda s: f"{s['target']} · {s['window']} · {s['objective']}"),
                     ("A_ANCHOR", lambda s: f"{s['audio_head']} · {s['objective']}"),
                     ("S_CONTROLS", lambda s: f"{s.get('pairing', 'correct')} · {s['objective']} · {s['target']}")):
        for ds in ("fau", "dtu", "federici"):
            rows = sorted((lab(s), key(fam, ds, **s)) for s in specs_of(plan, fam, ds))
            if rows:
                cont_table(f"{fam} · {ds}", rows)
    w("\n**正确配对 − 错误配对训练（S_CONTROLS，统一读出 gain）**\n\n| 数据集 · 目标函数 | 差值 | n |\n|---|---|---|")
    for ds in ("fau", "dtu", "federici"):
        for s in specs_of(plan, "S_CONTROLS", ds):
            if s.get("pairing") == "declared_wrong_pair":
                c = ctr(f"S_CONTROLS {ds} {s['objective']} correct − wrong", key("S_CONTROLS", ds, **dict(s, pairing="correct")), key("S_CONTROLS", ds, **s))
                if c: w(f"| {ds} · {s['objective']} · {s['target']} | {fmt(c)} | {c['n']} |")

    # ---------------------------------------------------------------- B_FM
    w("\n## 3. B_FM：基础模型（CBraMod / REVE）× 适配方式")
    heads = Counter(r.get("readout_head", "?") for r in recs.values() if r.get("row", {}).get("family_id") in FM_FAMS and r["row"]["spec"].get("architecture") in ("cbramod", "reve"))
    w("\n> 读出层（修正 A1，实现回执 §11–§12）：保留通道身份与空间对比，由学习的带符号空间滤波器组合，保留 patch 时间轴；"
      "另列保留通道的线性探针参照（probe/*）。本节单元的读出层版本：" + ", ".join(f"{k} {v}" for k, v in heads.items()) +
      "。通道平均的旧结果见附录 L，不作为基础模型结论。\n")
    for ds in ("fau", "dtu", "federici"):
        for obj in ("NCE", "CS_SINGLE"):
            rows = []
            for s in specs_of(plan, "B_FM", ds):
                if s["objective"] == obj:
                    rows.append((f"{s['architecture']} · {s['adaptation']}", key("B_FM", ds, **s)))
            rows.sort()
            ref = [x for x in specs_of(plan, "A_TIME", ds) if x["objective"] == obj and x["architecture"] == "density_tokens" and x["window"] == "full"]
            rows += [(f"参照：A_TIME density_tokens · full · {x['target']}", key("A_TIME", ds, **x)) for x in ref]
            cont_table(f"B_FM · {ds} · {obj}", rows, ("probe/gain_bits",) + (("attention/unified/accuracy",) if ds != "federici" else ()))
    w("\n**配对对比（统一读出 gain）**\n\n| 对比 | 差值 [95% CI] | n |\n|---|---|---|")
    for ds in ("fau", "dtu", "federici"):
        for obj in ("NCE", "CS_SINGLE"):
            for s in specs_of(plan, "B_FM", ds):
                if s["objective"] != obj:
                    continue
                if s["adaptation"] != "random_full":
                    c = ctr(f"B_FM {ds} {obj} {s['architecture']} {s['adaptation']} − random_full", key("B_FM", ds, **s), key("B_FM", ds, **dict(s, adaptation="random_full")))
                    if c: w(f"| {ds} · {obj} · {s['architecture']}：{s['adaptation']} − random_full | {fmt(c)} | {c['n']} |")
                ref = [x for x in specs_of(plan, "A_TIME", ds) if x["objective"] == obj and x["architecture"] == "density_tokens" and x["window"] == "full" and x["target"] == s["target"]]
                if ref:
                    c = ctr(f"B_FM {ds} {obj} {s['architecture']} {s['adaptation']} − A_TIME density full", key("B_FM", ds, **s), key("A_TIME", ds, **ref[0]))
                    if c: w(f"| {ds} · {obj} · {s['architecture']} {s['adaptation']} − 小编码器 density_tokens（完整窗） | {fmt(c)} | {c['n']} |")

    # ---------------------------------------------------------------- B_AUDITORY_CONTINUE
    def find(fam, ds, **m):
        return next((x for x in specs_of(plan, fam, ds) if all(x.get(k) == v for k, v in m.items())), None)
    w("\n## 3b. B_AUDITORY_CONTINUE：公开听觉配对数据上继续训练的主干（donor 不含目标队列）")
    for ds in ("fau", "dtu"):
        for obj in ("NCE", "CS_SINGLE"):
            rows = sorted((f"{x['architecture']} · {x['adaptation']}", key("B_AUDITORY_CONTINUE", ds, **x)) for x in specs_of(plan, "B_AUDITORY_CONTINUE", ds) if x["objective"] == obj)
            cont_table(f"B_AUDITORY_CONTINUE · {ds} · {obj}", rows, ("probe/gain_bits",))
    w("\n**配对对比（统一读出 gain）：继续训练 − 同深度的普通预训练；继续训练 − 随机初始化**\n\n| 对比 | 差值 [95% CI] | n |\n|---|---|---|")
    for ds in ("fau", "dtu"):
        for x in sorted(specs_of(plan, "B_AUDITORY_CONTINUE", ds), key=lambda x: (x["objective"], x["architecture"], x["adaptation"])):
            depth = x["adaptation"].split("_")[-1]
            for ref_ad in (f"pretrained_{depth}", "random_full"):
                y = find("B_FM", ds, architecture=x["architecture"], objective=x["objective"], adaptation=ref_ad)
                if y:
                    c = ctr(f"B_AUDITORY_CONTINUE {ds} {x['objective']} {x['architecture']} {x['adaptation']} − B_FM {ref_ad}", key("B_AUDITORY_CONTINUE", ds, **x), key("B_FM", ds, **y))
                    if c: w(f"| {ds} · {x['objective']} · {x['architecture']}：{x['adaptation']} − {ref_ad} | {fmt(c)} | {c['n']} |")

    # ---------------------------------------------------------------- private
    w("\n## 4. 私有儿童任务（当前类别）")
    for fam, lab in (("D_TASK_LOCAL", lambda s: f"{s['architecture']} · {s['window']} · {s['objective']}"),
                     ("D_GX", lambda s: f"GX · {s['window']}"),
                     ("D_FM_GENERIC", lambda s: f"{s['architecture']} · {s['adaptation']} · {s['objective']}"),
                     ("D_FM_PUBLIC", lambda s: f"{s['architecture']} · {s['adaptation']} · {s['objective']}"),
                     ("D_LOCAL_DISTILL", lambda s: f"{s['teacher']} · {s['window']} · {s['objective']}")):
        rows = sorted((lab(s), key(fam, "private_bdf", **s)) for s in specs_of(plan, fam, "private_bdf"))
        if any(agg["configs"].get(k) and agg["configs"][k]["units_done"] for _, k in rows):
            priv_table(fam, rows)

    w("\n**私有任务配对对比（head AUC；head gain 见 aggregate.json）**\n\n| 对比 | 差值 [95% CI] | n |\n|---|---|---|")
    for x in sorted(specs_of(plan, "D_FM_PUBLIC", "private_bdf"), key=lambda x: (x["objective"], x["architecture"], x["adaptation"])):
        y = find("D_FM_GENERIC", "private_bdf", architecture=x["architecture"], objective=x["objective"], adaptation=x["adaptation"].replace("auditory_", ""))
        if y:
            for m in ("head_auc", "head_gain_vs_base_bits"):
                c = ctr(f"D_FM_PUBLIC {x['objective']} {x['architecture']} {x['adaptation']} − D_FM_GENERIC {y['adaptation']}", key("D_FM_PUBLIC", "private_bdf", **x), key("D_FM_GENERIC", "private_bdf", **y), m)
                if c and m == "head_auc": w(f"| 公开听觉 donor − 通用预训练：{x['objective']} · {x['architecture']} · {y['adaptation']} | {fmt(c)} | {c['n']} |")
    for x in sorted(specs_of(plan, "D_LOCAL_DISTILL", "private_bdf"), key=lambda x: (x["objective"], x["teacher"], x["window"])):
        y = find("D_TASK_LOCAL", "private_bdf", architecture=x["architecture"], objective=x["objective"], window=x["window"])
        if y:
            for m in ("head_auc", "head_gain_vs_base_bits"):
                c = ctr(f"D_LOCAL_DISTILL {x['objective']} {x['teacher']} {x['window']} − D_TASK_LOCAL", key("D_LOCAL_DISTILL", "private_bdf", **x), key("D_TASK_LOCAL", "private_bdf", **y), m)
                if c and m == "head_auc": w(f"| 蒸馏学生 − 无蒸馏学生：{x['objective']} · 教师 {x['teacher']} · {x['window']} | {fmt(c)} | {c['n']} |")

    # ---------------------------------------------------------------- attention / coverage / selection
    w("\n## 5. 注意选择（同一试次 2AFC）与训练人群覆盖")
    for fam in ("C_ATTENTION", "C_SELECTION"):
        for ds in ("fau", "dtu"):
            rows = sorted((f"{s['architecture']} · {s['training_task']} · {s['objective']}", key(fam, ds, **s)) for s in specs_of(plan, fam, ds))
            cont_table(f"{fam} · {ds}", rows, ("attention/unified/accuracy", "attention/native/accuracy", "attention/trained/accuracy"))
    w("\n### C_COVERAGE · fau：按测试组的统一读出 gain\n")
    groups = sorted({g for (d, p), g in group.items() if d == "fau" and g})
    w("| 训练人群 · 架构 · 目标函数 | 单元 | " + " | ".join(groups) + " |\n|" + "---|" * (2 + len(groups)))
    for s in sorted(specs_of(plan, "C_COVERAGE", "fau"), key=lambda s: (s["architecture"], s["objective"], s["train_population"])):
        k = key("C_COVERAGE", "fau", **s); a = agg["configs"].get(k)
        if not a or k not in P:
            continue
        cells = []
        for g in groups:
            x = [r["unified/gain_bits"] for p, r in P[k].items() if group.get(("fau", p)) == g and "unified/gain_bits" in r]
            b = boot(x); agg["configs"][k][f"by_group/{g}/unified/gain_bits"] = b
            cells.append(fmt(b) + f" (n={b['n']})")
        w(f"| {s['train_population']} · {s['architecture']} · {s['objective']} | {a['units_done']}/{a['units_planned']} | " + " | ".join(cells) + " |")

    # ---------------------------------------------------------------- C_ADAPT
    w("\n## 6. C_ADAPT：个体支持集适配（查询集固定为每人最后 70%）")
    for ds in ("fau", "dtu", "private_bdf"):
        specs = specs_of(plan, "C_ADAPT", ds)
        if not any(n_units[key("C_ADAPT", ds, **s)] for s in specs):
            continue
        m = "unified/gain_bits" if ds != "private_bdf" else "unified/auc"
        w(f"\n### C_ADAPT · {ds}（{m}）\n\n| 架构 · 目标函数 · 适配 | 单元 | 支持 10% | 支持 30% | 30% − 无适配 |\n|---|---|---|---|---|")
        for s in sorted(specs, key=lambda s: (s["architecture"], s["objective"], s["adapter_kind"])):
            k = key("C_ADAPT", ds, **s)
            if k not in P:
                continue
            b1 = boot([r.get(f"support_0.1/{m}") for r in P[k].values() if r.get(f"support_0.1/{m}") is not None])
            b3 = boot([r.get(f"support_0.3/{m}") for r in P[k].values() if r.get(f"support_0.3/{m}") is not None])
            kn = key("C_ADAPT", ds, **dict(s, adapter_kind="none"))
            c = None
            if s["adapter_kind"] != "none" and kn in P:
                d = [P[k][p][f"support_0.3/{m}"] - P[kn][p][f"support_0.3/{m}"] for p in P[k] if p in P[kn] and f"support_0.3/{m}" in P[k][p] and f"support_0.3/{m}" in P[kn][p]]
                c = boot(d)
            agg["configs"][k].update({f"support_0.1/{m}": b1, f"support_0.3/{m}": b3, "vs_none_0.3": c})
            w(f"| {s['architecture']} · {s['objective']} · {s['adapter_kind']} | {n_units[k]}/{n_plan[k]} | {fmt(b1)} | {fmt(b3)} | {fmt(c) if c else '–'} |")

    # ---------------------------------------------------------------- registered multi-seed panel
    PN = scope.get("panel")
    if PN:
        w("\n## 7. 多 seed 面板（登记于修复结果产生之前：repair/PANEL_REGISTRATION.json）")
        w("\n每格：参与者均值 [95% CI]（以该 seed 的已训练模型为条件）。最后两列为各 seed 配置均值的跨 seed 均值与标准差（只计已有的 seed）。\n")
        Ps = {sd: table(plan, recs, {sd})[0] for sd in (3401,) + tuple(PN["seeds"])}
        for fam in PN["families"]:
            for ds in (("private_bdf",) if fam == "D_FM_GENERIC" else ("fau", "dtu", "federici")):
                m = "head_auc" if ds == "private_bdf" else "unified/gain_bits"
                specs = [x for x in specs_of(plan, fam, ds) if x["objective"] == PN["objective"] and x["adaptation"] in PN["adaptations"]]
                if not specs:
                    continue
                w(f"\n### {fam} · {ds} · {PN['objective']}（{m}）\n\n| 架构 · 适配 | " + " | ".join(f"seed {sd}" for sd in Ps) + " | 跨 seed 均值 | 跨 seed SD |\n|" + "---|" * (3 + len(Ps)))
                for x in sorted(specs, key=lambda x: (x["architecture"], x["adaptation"])):
                    k = key(fam, ds, **x); cells, means = [], []
                    for sd, Pd in Ps.items():
                        b = boot([r[m] for r in Pd.get(k, {}).values() if m in r]); cells.append(fmt(b))
                        if b.get("est") is not None:
                            means.append(b["est"])
                    agg.setdefault("panel", {})[k] = {"per_seed": dict(zip(map(str, Ps), cells)), "seed_means": means}
                    w(f"| {x['architecture']} · {x['adaptation']} | " + " | ".join(cells) + f" | {np.mean(means):.3f} | " + (f"{np.std(means, ddof=1):.3f}" if len(means) > 1 else "–") + " |" if means else
                      f"| {x['architecture']} · {x['adaptation']} | " + " | ".join(cells) + " | – | – |")
                w(f"\n预训练 − 随机初始化（配对，{m}），按 seed：\n\n| 架构 · 适配 | " + " | ".join(f"seed {sd}" for sd in Ps) + " |\n|" + "---|" * (1 + len(Ps)))
                for x in sorted(specs, key=lambda x: (x["architecture"], x["adaptation"])):
                    if x["adaptation"] == "random_full":
                        continue
                    a, b0 = key(fam, ds, **x), key(fam, ds, **dict(x, adaptation="random_full"))
                    cells = []
                    for sd, Pd in Ps.items():
                        d = [Pd[a][p][m] - Pd[b0][p][m] for p in Pd.get(a, {}) if p in Pd.get(b0, {}) and m in Pd[a][p] and m in Pd[b0][p]]
                        cells.append(fmt(boot(d)) if d else "–")
                    w(f"| {x['architecture']} · {x['adaptation']} | " + " | ".join(cells) + " |")
    # ---------------------------------------------------------------- probe failures (never silent)
    perr = [r["experiment_id"] for r in recs.values() if "channel_probe_error" in r.get("eval", {})]
    agg["channel_probe_errors"] = perr
    w(f"\n探针参照出错的单元：{len(perr)}" + (f"（{', '.join(perr[:10])}{' …' if len(perr) > 10 else ''}）" if perr else "") + "。\n")
    # ---------------------------------------------------------------- legacy channel-mean variant (appendix)
    if os.path.isdir(LEGACY):
        _, _, lrecs = load(LEGACY)
        PL, nl, npl, _ = table(plan, lrecs, seeds)
        AL = {k: {"units_done": nl[k], "units_planned": npl[k], "n_participants": len(PL.get(k, {})),
                  **summ(PL, k, PRIVM if k.split("|")[1] == "private_bdf" else CONT)} for k in nl}
        agg["legacy_chmean_v1"] = AL
        w("\n## 附录 L：通道平均变体（legacy_chmean_v1）\n\n> 对齐头先对通道取无权重平均（修正 A1 之前的实现）。保留为有记录的变体，"
          "不作为基础模型或数据听觉内容的证据；完成的单元数按停止时为准，未补齐。\n")
        for ds in ("fau", "dtu", "federici"):
            for obj in ("NCE", "CS_SINGLE"):
                rows = sorted((f"{x['architecture']} · {x['adaptation']}", key("B_FM", ds, **x)) for x in specs_of(plan, "B_FM", ds) if x["objective"] == obj)
                cont_table(f"L · B_FM · {ds} · {obj}", rows, ("attention/unified/accuracy",) if ds != "federici" else (), A=AL)
        rows = sorted((f"{x['architecture']} · {x['adaptation']} · {x['objective']}", key("D_FM_GENERIC", "private_bdf", **x)) for x in specs_of(plan, "D_FM_GENERIC", "private_bdf"))
        priv_table("L · D_FM_GENERIC", rows, A=AL)
        for fam in ("C_ATTENTION", "C_SELECTION", "C_COVERAGE"):
            for ds in ("fau", "dtu"):
                rows = sorted((f"{x['architecture']} · {x.get('training_task')} · {x.get('train_population', '')} · {x['objective']}", key(fam, ds, **x))
                              for x in specs_of(plan, fam, ds) if x["architecture"] == "cbramod")
                if any(AL.get(k) for _, k in rows):
                    cont_table(f"L · {fam} · {ds}", rows, ("attention/unified/accuracy",), A=AL)
    json.dump(agg, open(os.path.join(RES, "aggregate.json"), "w"), indent=1, default=float)
    open(DOC, "w").write("\n".join(L) + "\n")
    print(f"done in {time.time() - t0:.0f}s; units {sum(n_units.values())}; configs {len(agg['configs'])}")


if __name__ == "__main__":
    main()
