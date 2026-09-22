"""Gather every GX result into one JSON + markdown table (numbers only; interpretation is written by hand)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, cfg, done, open_run, read_json, write_json_overwrite


def gx1_table(results_root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(results_root.glob("GX1_*/child_metrics_*.csv")):
        f = pd.read_csv(path)
        lane = path.parent.name.replace("GX1_", "")
        for suffix in ("_shared", "_child_spatial", "_per_child", "_film_age_shuffled", "_film_age", "_adapt"):
            if lane.endswith(suffix):
                lane = lane[: -len(suffix)]
                break
        for model, sub in f.groupby("model"):
            per_child = sub.groupby("child").agg(auc=("auc", "mean"), j=("j_bits", "mean"), bacc=("bacc", "mean"))
            per_seed = sub.groupby("seed").apply(lambda d: d.groupby("child").auc.mean().mean(), include_groups=False)
            row = {"lane": lane, "model": model, "children": int(len(per_child)),
                   "auc_child_mean": float(per_child.auc.mean()), "auc_child_median": float(per_child.auc.median()),
                   "auc_child_q25": float(per_child.auc.quantile(0.25)), "auc_child_q75": float(per_child.auc.quantile(0.75)),
                   "children_auc_gt_half": int((per_child.auc > 0.5).sum()),
                   "auc_seed_min": float(per_seed.min()), "auc_seed_max": float(per_seed.max()),
                   "j_bits_child_mean": float(per_child.j.mean()), "bacc_child_mean": float(per_child.bacc.mean())}
            if "auc_pitch_direction" in sub:
                pd_ = sub.groupby("child").auc_pitch_direction.mean()
                row["auc_pitch_direction_child_mean"] = float(pd_.mean())
                row["children_pitch_gt_0.5"] = int((pd_ > 0.5).sum())
            if "partition" in sub:
                for part, s2 in sub.groupby("partition"):
                    row[f"auc_{part}"] = float(s2.groupby("child").auc.mean().mean())
            rows.append(row)
    return pd.DataFrame(rows)


def collect_all(results_root: Path) -> dict:
    out = {"gx1": gx1_table(results_root).to_dict("records")}
    for name, pattern in (("gx2_ssl", "GX2_ssl_*/summary_ssl_*.json"), ("gx2_eventprobe", "GX2_eventprobe_*/summary_event_probe_*.json"),
                          ("gx3_age", "GX3_age_*/summary_age_*.json"), ("gx4", "GX4_*/summary_gx4.json"),
                          ("gx5", "GX5_*/summary_gx5_conditions.json"), ("gx6", "GX6_*/summary_gx6_*.json"),
                          ("gx7", "GX7_*/summary_gx7.json")):
        items = []
        for path in sorted(results_root.glob(pattern)):
            payload = read_json(path)
            payload.pop("history", None)
            for k in ("pretrained", "scratch"):
                if isinstance(payload.get(k), dict):
                    payload[k].pop("per_seed", None)
            items.append({"path": str(path.relative_to(ROOT)), **payload})
        out[name] = items
    gx7 = results_root / "GX7_relations" / "relations.csv"
    if gx7.is_file():
        out["gx7_relations"] = pd.read_csv(gx7).to_dict("records")
    gx5 = results_root / "GX5_conditions" / "condition_case_series.csv"
    if gx5.is_file():
        f = pd.read_csv(gx5)
        within = f[f.transfer_to_record.isna()] if "transfer_to_record" in f else f
        out["gx5_within_record_by_condition"] = within.groupby(["child", "condition"]).auc.mean().reset_index().to_dict("records")
        if "transfer_to_condition" in f:
            tr = f[f.transfer_to_record.notna()]
            out["gx5_transfer_matrix"] = tr.groupby(["child", "condition", "transfer_to_condition"]).transfer_auc.mean().reset_index().to_dict("records")
    gx4 = results_root / "GX4_crosstask" / "within_child_cross_task.csv"
    if gx4.is_file():
        f = pd.read_csv(gx4)
        out["gx4_within_child"] = f.groupby(["child", "direction"]).agg(same=("same_task_val_auc", "mean"), cross=("cross_task_auc", "mean")).reset_index().to_dict("records")
    return out


def markdown(all_results: dict) -> str:
    lines = ["# GX 结果汇总（数值；解释见 GX_ANALYSIS.md）", ""]
    g = pd.DataFrame(all_results["gx1"])
    if len(g):
        lines.append("## GX1 跨儿童 vs 儿童内（儿童均值 AUC；seed 范围）")
        lines.append("")
        lines.append("| lane | model | children | AUC mean | median | IQR | >0.5 | seed range | J bits | pitch AUC |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in g.sort_values(["lane", "model"]).itertuples():
            pitch = f"{r.auc_pitch_direction_child_mean:.3f}" if hasattr(r, "auc_pitch_direction_child_mean") and np.isfinite(getattr(r, "auc_pitch_direction_child_mean", np.nan)) else ""
            lines.append(f"| {r.lane} | {r.model} | {r.children} | {r.auc_child_mean:.3f} | {r.auc_child_median:.3f} | "
                         f"[{r.auc_child_q25:.3f}, {r.auc_child_q75:.3f}] | {r.children_auc_gt_half}/{r.children} | "
                         f"{r.auc_seed_min:.3f}–{r.auc_seed_max:.3f} | {r.j_bits_child_mean:+.4f} | {pitch} |")
        lines.append("")
    for name in ("gx2_ssl", "gx2_eventprobe", "gx3_age", "gx4", "gx5", "gx6"):
        items = all_results.get(name, [])
        if items:
            lines.append(f"## {name}")
            lines.append("")
            for it in items:
                lines.append("```")
                lines.append(json.dumps(it, ensure_ascii=False, indent=1, default=str)[:4000])
                lines.append("```")
            lines.append("")
    if all_results.get("gx7_relations"):
        lines.append("## GX7 相关（Spearman）")
        lines.append("")
        lines.append("| lane | model | variable | n | rho | p |")
        lines.append("|---|---|---|---|---|---|")
        for r in all_results["gx7_relations"]:
            lines.append(f"| {r['lane']} | {r['model']} | {r['variable']} | {r['n']} | {r['spearman']:+.3f} | {r['p']:.3g} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def cmd_summarize(args, config) -> dict:
    run = open_run("summarize", args.run, config, args=vars(args))
    results_root = ROOT / cfg(config, "paths.results_relative")
    all_results = collect_all(results_root)
    write_json_overwrite(run["public"] / "all_results.json", all_results, private=False)
    doc = ROOT / "docs/auditory_gx/GX_RESULTS_TABLES.md"
    doc.write_text(markdown(all_results), encoding="utf-8")
    doc.chmod(0o644)
    done(run["private"], "summarize", {"gx1_rows": len(all_results["gx1"])})
    return {"gx1_rows": len(all_results["gx1"]), "doc": str(doc.relative_to(ROOT))}
