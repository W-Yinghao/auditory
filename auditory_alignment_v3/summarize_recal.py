"""ALN3 R_PRIVATE_CALIBRATION summary (package docs/08 §5): ALN2 private units re-evaluated from their best checkpoints with the
calibration variants of calib.py (recalibrate_private.py -> private/auditory_alignment_v3/units_recal/).

Variants (all fitted on the training children's early-stopping blocks only): NCE temperature (ALN2) | positive affine;
CS_SINGLE class-kernel posterior (ALN2) | positive affine; GX unconstrained affine (ALN2) | positive affine. Per test child:
AUC of the native score (identical for every variant of one unit: positive-slope maps do not change the ranking),
natural-distribution log loss (bits/trial), Brier, gain over the training base rate (bits/trial). Children appear once per
configuration (each child is in one outer fold); participant bootstrap (4000, 95 % percentile); contrasts paired per child.
Main tables: seed 3401 (registered scope); configurations with three seeds also get a per-seed contrast table.
A positive-affine improvement is a probability-interface repair, not stronger decoding (the AUC is unchanged).

Outputs: results/auditory_alignment_v3/r_private_calibration.json (aggregates), docs/auditory_alignment_v3/
R_PRIVATE_CALIBRATION_RESULTS.md, and the R_PRIVATE_CALIBRATION / R_FEDERICI unit records (pointers to their deliverables).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import time
from collections import defaultdict

import numpy as np

from auditory_alignment.aggregate import boot
from . import core

NATIVE = {"NCE": "temperature", "CS_SINGLE": "class_kernel", "task_native_CE": "unconstrained_affine_ALN2"}
METRICS = ("nll_bits", "brier", "gain_vs_base_bits")
DOC = os.path.join(core.REPO, "docs", "auditory_alignment_v3", "R_PRIVATE_CALIBRATION_RESULTS.md")
RES = os.path.join(core.REPO, "results", "auditory_alignment_v3", "r_private_calibration.json")


def cfg(r):
    s = r["row"]["spec"]
    return "|".join(str(x) for x in (r["row"]["family_id"], s["objective"], s.get("architecture", "GX"), s.get("adaptation", "-"), s.get("window", "-")))


def main():
    T = defaultdict(lambda: defaultdict(dict))  # (cfg, seed) -> child -> variant -> metrics
    for f in glob.glob(os.path.join(core.OUT, "units_recal", "*.json")):
        r = json.load(open(f))
        if r.get("status") != "complete":
            continue
        for cid, v in r["native_calibration"]["per_participant"].items():
            T[(cfg(r), r["row"]["seed"])][cid] = v
    out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "n_units": len(glob.glob(os.path.join(core.OUT, "units_recal", "*.json"))), "main": {}, "seed_panel": {}}
    for (k, sd), kids in sorted(T.items()):
        obj = k.split("|")[1]; nat = NATIVE[obj]
        if any(nat not in v or "positive_affine" not in v for v in kids.values()):
            continue
        res = {"n_children": len(kids), "auc": boot(np.array([v[nat]["auc_score"] for v in kids.values()]), seed=1)}
        for var in (nat, "positive_affine"):
            for m in METRICS:
                res[f"{var}/{m}"] = boot(np.array([v[var][m] for v in kids.values()]), seed=2)
        for m in METRICS:
            res[f"affine-native/{m}"] = boot(np.array([v["positive_affine"][m] - v[nat][m] for v in kids.values()]), seed=3)
        if sd == 3401:
            out["main"][k] = res
        out["seed_panel"].setdefault(k, {})[str(sd)] = {m: res[f"affine-native/{m}"] for m in ("nll_bits", "gain_vs_base_bits")}
    out["seed_panel"] = {k: v for k, v in out["seed_panel"].items() if len(v) >= 2}
    os.makedirs(os.path.dirname(RES), exist_ok=True); json.dump(out, open(RES, "w"), indent=1)
    write_doc(out); write_records()


def f(c, nd=3):
    return "—" if c.get("est") is None else f"{c['est']:.{nd}f} [{c['ci_low']:.{nd}f}, {c['ci_high']:.{nd}f}]"


def write_doc(out):
    L = []; w = L.append
    w("# ALN3 R_PRIVATE_CALIBRATION：私有任务概率校准接口——中性结果\n")
    w(f"生成时间 {out['generated']}；重新评价的 ALN2 私有单元 {out['n_units']} 个（从 best checkpoint 重载，不重新训练）。"
      "校准均只在训练儿童的早停块上拟合；测试儿童从不参与。每个配置每个儿童出现一次（各在一个外折）；参与者 bootstrap 95% 区间，配对对比。"
      "主表 seed 3401。\n")
    w("原生方式：NCE = 温度 sigmoid(s/τ)（ALN2，无截距）；CS_SINGLE = 类别核后验（ALN2）；GX = 无约束仿射（ALN2）。"
      "正斜率仿射 sigmoid(a·s+b)，a>0，不改变排序，因此 AUC 对两种方式相同；它的改善只说明概率接口被修复，不说明解码信号更强。\n")
    w("log loss 越低越好；gain（相对训练基率，比特/试次）越高越好。\n")
    w("| 配置（族·目标·架构·适配·窗口） | n 儿童 | AUC | 原生 log loss | 仿射 log loss | 原生 gain | 仿射 gain | 仿射−原生 log loss | 仿射−原生 gain |")
    w("|---|---|---|---|---|---|---|---|---|")
    for k, r in sorted(out["main"].items()):
        nat = NATIVE[k.split("|")[1]]
        w(f"| {k} | {r['n_children']} | {f(r['auc'])} | {f(r[f'{nat}/nll_bits'])} | {f(r['positive_affine/nll_bits'])} | {f(r[f'{nat}/gain_vs_base_bits'])} | "
          f"{f(r['positive_affine/gain_vs_base_bits'])} | {f(r['affine-native/nll_bits'])} | {f(r['affine-native/gain_vs_base_bits'])} |")
    if out["seed_panel"]:
        w("\n## 多 seed 配置：仿射−原生 gain（比特/试次），逐 seed\n")
        w("| 配置 | " + " | ".join(f"seed {s}" for s in ("3401", "3407", "3413")) + " |\n|---|---|---|---|")
        for k, v in sorted(out["seed_panel"].items()):
            w(f"| {k} | " + " | ".join(f(v[s]["gain_vs_base_bits"]) if s in v else "—" for s in ("3401", "3407", "3413")) + " |")
    w("\nBrier 见 `results/auditory_alignment_v3/r_private_calibration.json`。负 gain 也可能来自泛化/过拟合，不全部归于缺截距（包 docs/08 §5）。"
      "本文件只列结果；框架由用户决定。\n")
    open(DOC, "w").write("\n".join(L) + "\n")


def write_records():
    rows = core.load_rows(); sh = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    for fam, deliv in (("R_PRIVATE_CALIBRATION", [DOC, RES]),
                       ("R_FEDERICI", [os.path.join(core.REPO, "docs", "auditory_alignment_v3", "FEDERICI_REAGGREGATION_RECEIPT.md"),
                                       os.path.join(core.REPO, "results", "auditory_alignment_v3", "reaggregate", "federici_reaggregate.json"),
                                       os.path.join(core.REPO, "docs", "auditory_alignment_v3", "ADDENDUM_01_FEDERICI_IDENTITY.md")])):
        r = next(x for x in rows if x["family_id"] == fam)
        rec = {"experiment_id": r["experiment_id"], "row": r, "status": "complete", "runner": "auditory_alignment_v3 analysis", "job_kind": r.get("job_kind"),
               "deliverables": {os.path.relpath(p, core.REPO): sh(p) for p in deliv if os.path.exists(p)},
               "code": {"summarize_recal.py": sh(__file__), "recalibrate_private.py": sh(os.path.join(os.path.dirname(__file__), "recalibrate_private.py")),
                        "reaggregate_federici.py": sh(os.path.join(os.path.dirname(__file__), "reaggregate_federici.py"))}}
        p = os.path.join(core.OUT, "units", f"{r['experiment_id']}.json")
        json.dump(rec, open(p + ".tmp", "w"), indent=1); os.replace(p + ".tmp", p)


if __name__ == "__main__":
    main()
