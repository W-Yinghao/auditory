"""Markdown tables from the analyze summary (numbers only; interpretation is written separately)."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def f(x, n=3):
    if x is None:
        return "—"
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return f"[{f(x[0], n)}, {f(x[1], n)}]"
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def auc_cell(d):
    if not d:
        return "—"
    return f'{f(d["mean"])}（{f(d["min"])}–{f(d["max"])}）'


def tables(summary: dict) -> str:
    b1, b2, b3, C = summary["b1"], summary.get("b2", {}), summary.get("b3", {}), summary["claims"]
    out = []
    out.append("## 表 1　主张状态总表\n")
    out.append("| 主张 | 关键估计 | 状态 |\n|---|---|---|")
    for k in sorted(C, key=lambda s: int(s[1:])):
        v = {a: b for a, b in C[k].items() if a != "status"}
        out.append(f"| {k} | {json.dumps(v, ensure_ascii=False)} | **{C[k]['status']}** |")
    out.append("\n## 表 2　阶段分类（0–12 vs ≥13 月，3 种子 OOF AUC 均值（最小–最大））\n")
    out.append("| 模型 | AUC | 置换 p | 95% CI | 严格单次抽样 |\n|---|---|---|---|---|")
    rows = [("(a1) 折内模板 w_late", b1["a1"]), ("(a2) 标签化模板", b1["a2"]), ("(b) 冻结表示 + logistic", b1["b"]),
            ("(b-dev) 偏差聚合", b1["b_dev"]), ("(b-std) 标准聚合", b1["b_std"])]
    for v in ("rec", "bc", "rec_dev", "rec_std"):
        if f"c_{v}" in b1:
            rows.append((f"(c-{v}) 端到端", b1[f"c_{v}"]))
    for name, d in rows:
        out.append(f'| {name} | {auc_cell(d.get("auc"))} | {f(d.get("perm_p"), 4)} | {f(d.get("ci"))} | {auc_cell(d.get("strict_single_draw"))} |')
    bg = b1["background"]
    out.append(f'| 背景基线（月龄、PTA、技术） | {auc_cell(bg["stage_background"])} | | | |')
    out.append(f'| 仅月龄（固定分数） | {auc_cell(bg["age_only_auc"])} | | | |')
    out.append(f'| H2 背景（技术 + 预刺激谱） | {auc_cell(bg["h2_background"])} | | | |')
    out.append(f'| (a1) + 背景 | {auc_cell(bg["a1_plus_background"])} | | | |')
    out.append(f'| (b) + 背景 | {auc_cell(bg["b_plus_background"])} | | | |')
    if "a5_perm" in b1:
        a5 = b1["a5_perm"]
        out.append(f'\n附录 A5（探索性，n={a5["n"]}）：偏差聚合置换 p {f(a5["p_dev"], 4)}；标准聚合下尾 p {f(a5["p_std_lower_tail"], 4)}；'
                   f'偏差 − 标准之差的置换 p {f(a5["p_diff"], 4)}。')
    bgx = b1["background"]
    if "exploratory_age_plus_a1" in bgx:
        out.append(f'附录 A3（探索性）：仅月龄 logistic {auc_cell(bgx["exploratory_age_lr"])}；月龄 + w_late {auc_cell(bgx["exploratory_age_plus_a1"])}；'
                   f'差的 95% 区间 {f(bgx["exploratory_age_plus_a1_minus_age_ci"])}。')
    s = b1["a1"]["sens_0_2_vs_13"]
    out.append(f'\n敏感性 0–2 vs ≥13 月（n={s["n"]}）：(a1) AUC {auc_cell(s)}，置换 p {f(s["perm_p"], 4)}。')
    out.append("\n## 表 3　H3 遮挡（阶段 AUC 下降）\n")
    out.append("| 窗/组 | (b) 移除-重训 | (c-rec) 仅测试遮挡 |\n|---|---|---|")
    cdrop = b1.get("h3_c_drop", {})
    for n, v in b1["h3_b_drop"].items():
        out.append(f"| {n} | {f(v, 4)} | {f(cdrop.get(n), 4)} |")
    si = b1["si"]
    out.append("\n## 表 4　SI 线\n")
    out.append(f'- H11 b-ord：AUC(SIR>3) {auc_cell(si["h11_b_ord"]["auc_sir_gt3"])}，MAE {f(si["h11_b_ord"]["mae"]["mean"])}')
    if "h11_c_ord" in si:
        out.append(f'- H11 c-ord（次要）：AUC {auc_cell(si["h11_c_ord"]["auc_sir_gt3"])}')
    for k, v in si.get("h12", {}).items():
        out.append(f'- H12（{k}）：打乱 AUC 均值 {f(v["auc_shuffled_mean"])}，Δ_AUC {f(v["delta_auc"])}，Δ_MAE {f(v["delta_mae"])}，p_AUC {f(v["p_auc"], 4)}，p_MAE {f(v["p_mae"], 4)}（n={v["n"]}）')
    h13 = si["h13"]
    out.append(f'- H13：阶段分数 → SIR AUC {auc_cell(h13["auc_stage_score"])}，全 EEG {f(h13["auc_full"])}，技能比 {f(h13["skill_ratio"])}；(b) 阶段分数技能比 {f(si["h13_b_stage_score"]["skill_ratio"])}')
    h14 = si["h14"]
    out.append(f'- H14：MAE_C {f(h14["mae_C"])}，MAE_C+Z {f(h14["mae_CZ"])}，Δ {f(h14["delta"])} CI {f(h14["ci"])}；AUC_C {auc_cell(h14["auc_C"])}，AUC_C+Z {auc_cell(h14["auc_CZ"])}')
    for k, v in si["h15"].items():
        out.append(f'- H15（{k}）：{v["n_high"]} vs {v["n_low"]}，Cliff δ {f(v["delta"])} CI {f(v["ci"])}')
    m = si["muss_b_ridge"]
    out.append(f'- MUSS（次要）：MAE {f(m["mae"])}（留一均值基线 {f(m["mae_train_mean_baseline"])}），Spearman {f(m["spearman"]["rho"])}')
    out.append("\n## 表 5　其他 B1 量\n")
    out.append(f'- H5：{json.dumps(b1["h5"], ensure_ascii=False)}')
    out.append(f'- H6：{json.dumps(b1["h6"], ensure_ascii=False)}')
    out.append(f'- H9：{json.dumps(b1["h9"], ensure_ascii=False)}')
    out.append(f'- 刺激解码（上游质控）：{json.dumps(b1["stimulus"], ensure_ascii=False)}')
    if b2:
        out.append("\n## 表 6　B2\n")
        out.append(f'- {json.dumps(b2, ensure_ascii=False)}')
    if b3:
        out.append("\n## 表 7　B3\n")
        out.append(f'- {json.dumps(b3, ensure_ascii=False)}')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    s = json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(tables(s), encoding="utf-8")
