"""ALN2 item 3a (X_READOUT_DIAG) analysis per docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md §2.

Three readout levels per seed-3401 B_FM unit, all on the same test candidates and scored with the unified ridge readout:
  R0  trained 16-d readout (B_FM eval, unified/gain_bits)
  D1  spatial components before the final 16-d projection (X_READOUT_DIAG, spatial/*)
  R2  channel-preserving linear probe (B_FM eval channel_probe, probe/*)
gain_bits = logloss(mismatched EEG) - logloss(true EEG), bits per query. Per participant, a configuration's metric is the mean
over its units (content folds); Federici phantom-head ('Artifact') recordings are excluded; Federici recordings are separate
identities (ALN3 addendum 01). Participant bootstrap (4000, percentile 95 %); contrasts paired per participant. Intervals
condition on the trained models (single seed).
Operationalisation of the prereg's '≈' / '>' (fixed here, before the tables are read): a paired difference is called '>' or
'<' when its 95 % interval excludes 0, '≈' otherwise.

Outputs: results/auditory_alignment_v2/item3a.json (aggregates only), docs/auditory_alignment_v2/ITEM3A_RESULTS.md,
private/auditory_alignment_v2/agg/item3a_participants.json (per participant; stays private).
"""
from __future__ import annotations

import glob
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment.aggregate import boot
from .aggregate import PRIV, REPO, RES, rows_of

DOC = os.path.join(REPO, "docs", "auditory_alignment_v2", "ITEM3A_RESULTS.md")
LEVELS = ("R0", "D1", "R2")
METRIC = {"R0": "unified", "D1": "spatial", "R2": "probe"}
ADS = ("random_full", "pretrained_frozen", "pretrained_peft", "pretrained_partial", "pretrained_full")


def _gain(r, pre):
    a, b = r.get(f"{pre}/mismatched_eeg"), r.get(f"{pre}/regular")
    return (a["logloss_bits"] - b["logloss_bits"]) if a and b else None


def load():
    U = os.path.join(PRIV, "units"); recs = {}
    for p in glob.glob(os.path.join(U, "ALN2_B_FM_*.json")) + glob.glob(os.path.join(U, "ALN2X_READOUT_DIAG_*.json")):
        if p.endswith(".FAILED.json"):
            continue
        r = json.load(open(p))
        if r.get("status") == "complete":
            recs[r["experiment_id"]] = r
    return recs


def participant_table(recs):
    T = defaultdict(lambda: defaultdict(lambda: defaultdict(list))); meta = {}; n_units = defaultdict(int)
    for eid, r in recs.items():
        if r["row"].get("family_id") != "X_READOUT_DIAG":
            continue
        b = recs.get(r["base_unit_resolved"])
        if b is None or b["row"]["seed"] != 3401:
            continue
        s = b["row"]["spec"]; key = (b["row"]["dataset"], s["objective"], s["architecture"], s["adaptation"]); n_units[key] += 1
        base = rows_of(b, recs) or {}
        for pid, m in base.items():
            if m.get("group") == "Artifact":
                continue
            meta[(key[0], pid)] = m.get("group")
            for lv, k in (("R0", "unified/gain_bits"), ("R2", "probe/gain_bits"), ("R0_top1", "unified/regular/top1"), ("R2_top1", "probe/regular/top1"),
                          ("R0_att", "attention/unified/accuracy"), ("R2_att", "attention/probe/accuracy")):
                if isinstance(m.get(k), float) and np.isfinite(m[k]):
                    T[key][pid][lv].append(m[k])
        sp = r["eval"]["spatial_readout"]
        for pid, m in sp["per_participant"].items():
            if m.get("group") == "Artifact":
                continue
            g = _gain(m, "spatial")
            if g is not None and np.isfinite(g):
                T[key][pid]["D1"].append(g); T[key][pid]["D1_top1"].append(m["spatial/regular"]["top1"])
        for pid, m in sp.get("attention_2afc", {}).items():
            v = m.get("spatial", m) if isinstance(m, dict) else None
            if isinstance(v, dict) and isinstance(v.get("accuracy"), (int, float)):
                T[key][pid]["D1_att"].append(float(v["accuracy"]))
    P = {k: {pid: {mm: float(np.mean(v)) for mm, v in ms.items()} for pid, ms in pids.items()} for k, pids in T.items()}
    return P, dict(n_units), meta


def paired(P, k, a, b, ka=None):
    A = P.get(ka or k, {}); B = P.get(k, {})
    pids = [p for p in B if a in A.get(p, {}) and b in B[p]]
    return boot(np.array([A[p][a] - B[p][b] for p in pids]), seed=7), len(pids)


def sign(ci):
    if ci.get("est") is None:
        return "n/a"
    return ">" if ci["ci_low"] > 0 else ("<" if ci["ci_high"] < 0 else "≈")


def main():
    recs = load(); P, n_units, meta = participant_table(recs)
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "prereg": "docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md", "n_units": {"|".join(k): v for k, v in n_units.items()},
           "configs": {}, "ft_vs_frozen_R2": {}}
    for k in sorted(P):
        c = {lv: boot(np.array([m[lv] for m in P[k].values() if lv in m]), seed=1) for lv in LEVELS + ("R0_top1", "D1_top1", "R2_top1", "R0_att", "D1_att", "R2_att")}
        for a, b in (("D1", "R0"), ("R2", "D1"), ("R2", "R0")):
            c[f"{a}-{b}"], c[f"n_{a}-{b}"] = paired(P, k, a, b)
        c["pattern"] = f"D1{sign(c['D1-R0'])}R0, R2{sign(c['R2-D1'])}D1, R2{sign(c['R2-R0'])}R0"
        out["configs"]["|".join(k)] = c
        if k[3] != "pretrained_frozen":
            fz = (k[0], k[1], k[2], "pretrained_frozen")
            if fz in P:
                A = P[k]; B = P[fz]; pids = [p for p in A if "R2" in A[p] and "R2" in B.get(p, {})]
                d = boot(np.array([A[p]["R2"] - B[p]["R2"] for p in pids]), seed=11)
                out["ft_vs_frozen_R2"]["|".join(k)] = {**d, "n": len(pids), "sign": sign(d)}
    os.makedirs(RES, exist_ok=True); os.makedirs(os.path.join(PRIV, "agg"), exist_ok=True)
    json.dump(out, open(os.path.join(RES, "item3a.json"), "w"), indent=1)
    json.dump({"|".join(k): v for k, v in P.items()}, open(os.path.join(PRIV, "agg", "item3a_participants.json"), "w"))
    write_doc(out)


def f(ci, nd=3):
    return "—" if ci.get("est") is None else f"{ci['est']:.{nd}f} [{ci['ci_low']:.{nd}f}, {ci['ci_high']:.{nd}f}]"


def write_doc(out):
    L = []; w = L.append
    w("# ALN2 第 3a 项：读出瓶颈诊断（X_READOUT_DIAG）——中性结果\n")
    w(f"生成时间 {out['generated']}；预登记 `{out['prereg']}` §2；seed 3401；只评价，不训练。数值为参与者均值与参与者 bootstrap 95% 区间"
      "（以已训练模型为条件，单 seed）。gain = 错配 EEG − 真实 EEG 的 log loss（比特/查询），三级均用统一 ridge 读出、同一测试候选集。"
      "Federici 排除幻影头记录；HC-v 记录按独立身份（ALN3 附录 01）。\n")
    w("R0 = 训练出的 16 维读出；D1 = 最终 16 维投影之前的空间分量（K×e = 256 维/patch）经统一 ridge；R2 = 保留全部通道的线性探针。"
      "\n\n'>'/'<' 表示配对差的 95% 区间不含 0，'≈' 表示含 0（这一操作化在读表之前写入分析脚本，预登记本身未给阈值，如实披露）。\n")
    total = sum(out["n_units"].values()); w(f"单元数：{total}（预登记 500）。\n")
    for ds in ("dtu", "fau", "federici"):
        for obj in ("NCE", "CS_SINGLE"):
            ks = [k for k in out["configs"] if k.startswith(f"{ds}|{obj}|")]
            if not ks:
                continue
            w(f"\n## {ds.upper() if ds != 'federici' else 'Federici'} · {obj}\n")
            w("| 架构 | 适配 | n 单元 | R0 | D1 | R2 | D1−R0 | R2−D1 | R2−R0 | 模式 |")
            w("|---|---|---|---|---|---|---|---|---|---|")
            for arch in ("cbramod", "reve"):
                for ad in ADS:
                    k = f"{ds}|{obj}|{arch}|{ad}"
                    if k not in out["configs"]:
                        continue
                    c = out["configs"][k]
                    w(f"| {arch} | {ad} | {out['n_units'].get(k, 0)} | {f(c['R0'])} | {f(c['D1'])} | {f(c['R2'])} | {f(c['D1-R0'])} | {f(c['R2-D1'])} | {f(c['R2-R0'])} | {c['pattern']} |")
    w("\n## R2(微调) − R2(同外折冻结)\n")
    w("| 配置 | n | 差 | 符号 |\n|---|---|---|---|")
    for k, d in sorted(out["ft_vs_frozen_R2"].items()):
        w(f"| {k} | {d['n']} | {f(d)} | {d['sign']} |")
    w("\n## 次要终点（top-1 与注意 2AFC）\n")
    w("| 配置 | R0 top-1 | D1 top-1 | R2 top-1 | R0 2AFC | D1 2AFC | R2 2AFC |\n|---|---|---|---|---|---|---|")
    for k, c in sorted(out["configs"].items()):
        w(f"| {k} | {f(c['R0_top1'])} | {f(c['D1_top1'])} | {f(c['R2_top1'])} | {f(c['R0_att'])} | {f(c['D1_att'])} | {f(c['R2_att'])} |")
    w("\n## 解读表（预登记 §2，原文）\n")
    w("| 结果 | 含义 |\n|---|---|\n| D1 ≈ R2 > R0 | 信息在 8 个空间滤波后仍在，损失发生在最终 16 维投影/目标函数这一步 |\n| R2 > D1 ≈ R0 | 8 个空间滤波（K=8）是瓶颈 |\n"
      "| R2 > D1 > R0 | 两步都有损失 |\n| D1 ≈ R0 ≈ R2 | 训练读出不是瓶颈（与已观察到的 R2 > R0 矛盾，需检查） |\n| R2(微调) ≤ R2(冻结) | 微调没有改善线性可读的表示，反而可能损害（与过拟合一致） |\n")
    w("\n## 说明与需检查的单元格（只陈述事实）\n")
    w("- R2(微调) − R2(冻结) 表中 random_full 行比较的是随机初始化训练与预训练冻结，不是对预训练模型的微调；按预登记一并列出。")
    w("- 预登记解读表未覆盖 D1 > R2 的结果（空间分量经 ridge 高于保留通道的探针）；出现时如实列为表外模式。")
    odd = [k for k, c in out["configs"].items() if c["R0"].get("est") is not None and c["R2"].get("est") is not None and c["R0"]["est"] > 0.1 and c["R2"]["ci_high"] < 0.01]
    if odd:
        w("- 需检查：" + "；".join(f"{k}（R0 {out['configs'][k]['R0']['est']:.3f}，R2 {out['configs'][k]['R2']['est']:.3f}）" for k in odd) +
          "。训练读出明显为正而探针约为 0，与其它配置不一致；探针拟合（PCA 256 / 300 片段）在该配置是否失效尚未核查，核查前不据此解读。")
    w("\n本文件只列结果；按解读表的归纳与框架由用户决定。\n")
    os.makedirs(os.path.dirname(DOC), exist_ok=True); open(DOC, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
