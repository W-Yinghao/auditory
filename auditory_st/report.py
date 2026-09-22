"""Neutral results report for ST1: tables, figures and the mechanical pre-registered rule outcome.

Reads only public aggregates of finished runs. Produces figures/auditory_st/<run>/ and
docs/auditory_st/ST1_RESULTS.md. Interpretation beyond the frozen grid is not written here.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .runtime import ROOT, cfg, digest, read_json, results_dir

# Reference palette (dataviz skill, light mode): categorical slots 1-3 for the three primary lanes,
# gray for the supplementary event-condition lane, muted ink for reference lines.
LANE_COLOURS = {"mff_puretone": "#2a78d6", "mff_bapa": "#eb6834", "bdf_puretone": "#1baf7a",
                "mff_unknown_event": "#8a8984"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
DIVERGING = ["#2a78d6", "#f0efec", "#e34948"]
LANE_LABELS = {"mff_puretone": "MFF pure tone (stad/devt)", "mff_bapa": "MFF bapa (stad/devt)",
               "bdf_puretone": "HA clinical pure tone (literal 1/2)",
               "mff_unknown_event": "MFF task-unknown event layer (stad/devt)"}


def load_readout(config: dict, run: str) -> dict | None:
    public = results_dir(config, run)
    if not (public / "summary.json").is_file():
        return None
    out = {"run": run, "summary": read_json(public / "summary.json"),
           "curves": pd.read_csv(public / "curves.csv"), "bands": pd.read_csv(public / "bands.csv"),
           "repeatability": pd.read_csv(public / "repeatability.csv"),
           "within": pd.read_csv(public / "within_child.csv") if (public / "within_child.csv").stat().st_size > 1 else pd.DataFrame(),
           "tg": pd.read_csv(public / "tg_auc_mean.csv", index_col=0) if (public / "tg_auc_mean.csv").is_file() else None,
           "hashes": {p.name: digest(p) for p in sorted(public.glob("*")) if p.is_file()}}
    return out


def _style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                         "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                         "figure.dpi": 200, "savefig.dpi": 200, "text.color": INK})
    return plt


def _band_shade(ax, lo_s, hi_s):
    ax.axvspan(lo_s, hi_s, color=GRID, alpha=0.5, lw=0, zorder=0)


def figure_lane(lane: str, ro: dict, out_dir: Path) -> list[Path]:
    plt = _style()
    c = ro["curves"]
    colour = LANE_COLOURS.get(lane, "#2a78d6")
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.4), sharex=True, constrained_layout=True)
    t = c.window_centre_s.to_numpy()
    for ax, key, ylabel in ((axes[0], "auc", "AUC (child mean)"), (axes[1], "bacc", "balanced accuracy"),
                            (axes[2], "g_hist", "gain over history, bits/trial")):
        ax.fill_between(t, c[f"{key}_lo"], c[f"{key}_hi"], color=colour, alpha=0.18, lw=0)
        ax.plot(t, c[f"{key}_mean"], color=colour, lw=2, label="EEG readout (mean, 95% child bootstrap)")
        ax.plot(t, c[f"{key}_median"], color=colour, lw=1, ls=":", label="median child")
        ax.axvline(0, color=INK2, lw=0.8, ls="--")
        ax.set_ylabel(ylabel)
    axes[0].axhline(0.5, color=INK2, lw=0.8)
    axes[0].axhline(c.auc_hist.iloc[0], color=INK2, lw=1.2, ls="-.", label="history-only reference")
    axes[1].axhline(0.5, color=INK2, lw=0.8)
    axes[1].axhline(c.bacc_hist.iloc[0], color=INK2, lw=1.2, ls="-.", label="history-only reference")
    axes[2].axhline(0.0, color=INK2, lw=0.8)
    if "g_prior_mean" in c:
        axes[2].plot(t, c.g_prior_mean, color=INK2, lw=1.2, ls="-.", label="gain over class prior (calibrated)")
    axes[2].set_xlabel("time from event marker (s)")
    axes[0].legend(loc="upper left", ncol=1, fontsize=7.5)
    axes[2].legend(loc="upper left", fontsize=7.5)
    s = ro["summary"]
    fig.suptitle(f"{LANE_LABELS.get(lane, lane)} - {s['children']} children, {s['records']} records, "
                 f"{s['trials']} trials ({s['deviant_trials']} class 1)", fontsize=9.5, color=INK)
    paths = []
    for ext in ("png", "pdf"):
        p = out_dir / f"curves_{lane}.{ext}"
        fig.savefig(p)
        paths.append(p)
    plt.close(fig)
    return paths


def figure_tg(lane: str, ro: dict, out_dir: Path) -> list[Path]:
    if ro["tg"] is None:
        return []
    plt = _style()
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("div_auc", DIVERGING)
    m = ro["tg"].to_numpy(dtype=float)
    t = np.array([float(x) for x in ro["tg"].index])
    amp = float(np.nanmax(np.abs(m - 0.5))) if np.isfinite(m).any() else 0.1
    amp = max(amp, 0.02)
    fig, ax = plt.subplots(figsize=(4.6, 4.2), constrained_layout=True)
    ax.grid(False)
    im = ax.imshow(m, origin="lower", cmap=cmap, norm=TwoSlopeNorm(vcenter=0.5, vmin=0.5 - amp, vmax=0.5 + amp),
                   extent=[t[0], t[-1], t[0], t[-1]], aspect="equal", interpolation="nearest")
    ax.axhline(0, color=INK2, lw=0.6, ls="--")
    ax.axvline(0, color=INK2, lw=0.6, ls="--")
    ax.set_xlabel("test window centre (s)")
    ax.set_ylabel("train window centre (s)")
    ax.set_title(f"temporal generalisation, mean AUC over children\n{LANE_LABELS.get(lane, lane)}", fontsize=9)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("AUC (0.5 = chance)")
    paths = []
    for ext in ("png", "pdf"):
        p = out_dir / f"tg_{lane}.{ext}"
        fig.savefig(p)
        paths.append(p)
    plt.close(fig)
    return paths


def figure_repeatability(lane: str, ro: dict, out_dir: Path) -> list[Path]:
    rep = ro["repeatability"]
    if rep.empty:
        return []
    plt = _style()
    colour = LANE_COLOURS.get(lane, "#2a78d6")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True, constrained_layout=True)
    for ax, part in zip(axes, ("early_late_halves", "odd_even_blocks")):
        sub = rep[(rep.partition == part) & (rep.metric == "auc")]
        ax.plot(sub.window_centre_s, sub.spearman_block0_block1, color=colour, lw=2, label="AUC")
        sub2 = rep[(rep.partition == part) & (rep.metric == "g_hist")]
        ax.plot(sub2.window_centre_s, sub2.spearman_block0_block1, color=colour, lw=1.2, ls="--", label="gain over history")
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvline(0, color=INK2, lw=0.8, ls="--")
        ax.set_title(f"{part.replace('_', ' ')} (n children = {int(sub.children.max()) if len(sub) else 0})", fontsize=9)
        ax.set_xlabel("time from event marker (s)")
    axes[0].set_ylabel("Spearman r, block A vs block B\n(child scores)")
    axes[0].legend(fontsize=7.5)
    fig.suptitle(f"between-block repeatability of child scores - {LANE_LABELS.get(lane, lane)}", fontsize=9.5)
    paths = []
    for ext in ("png", "pdf"):
        p = out_dir / f"repeatability_{lane}.{ext}"
        fig.savefig(p)
        paths.append(p)
    plt.close(fig)
    return paths


def figure_overview(readouts: dict[str, dict], out_dir: Path) -> list[Path]:
    plt = _style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    for lane, ro in readouts.items():
        c = ro["curves"]
        colour = LANE_COLOURS.get(lane, "#8a8984")
        lw = 1.4 if lane == "mff_unknown_event" else 2.0
        axes[0].fill_between(c.window_centre_s, c.auc_lo, c.auc_hi, color=colour, alpha=0.12, lw=0)
        axes[0].plot(c.window_centre_s, c.auc_mean, color=colour, lw=lw, label=LANE_LABELS.get(lane, lane))
        axes[1].fill_between(c.window_centre_s, c.g_hist_lo, c.g_hist_hi, color=colour, alpha=0.12, lw=0)
        axes[1].plot(c.window_centre_s, c.g_hist_mean, color=colour, lw=lw)
    axes[0].axhline(0.5, color=INK2, lw=0.8)
    axes[1].axhline(0.0, color=INK2, lw=0.8)
    for ax in axes:
        ax.axvline(0, color=INK2, lw=0.8, ls="--")
        ax.set_xlabel("time from event marker (s)")
    axes[0].set_ylabel("AUC, child mean (95% CI)")
    axes[1].set_ylabel("gain over history, bits/trial")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("child-held-out sound-condition readout by lane (windows 80 ms, step 20 ms)", fontsize=9.5)
    paths = []
    for ext in ("png", "pdf"):
        p = out_dir / f"overview_lanes.{ext}"
        fig.savefig(p)
        paths.append(p)
    plt.close(fig)
    return paths


def rule_table(readouts: dict[str, dict]) -> pd.DataFrame:
    """Mechanical application of prereg section 6: a band is 'readable' if AUC CI low > 0.5 and G_hist CI low > 0."""
    rows = []
    for lane, ro in readouts.items():
        b = ro["bands"]
        for band in ("pre", "early", "mid", "late"):
            sub = b[b.band == band].set_index("metric")
            if sub.empty:
                continue
            auc, g = sub.loc["auc"], sub.loc["g_hist"]
            bacc = sub.loc["bacc"]
            gp = sub.loc["g_prior"] if "g_prior" in sub.index else None
            rows.append({"lane": lane, "band": band, "from_s": float(auc.from_s), "to_s": float(auc.to_s),
                         "children": int(auc.children),
                         "auc_mean": float(auc["mean"]), "auc_ci_lo": float(auc.ci_lo), "auc_ci_hi": float(auc.ci_hi),
                         "children_auc_gt_0.5": int(auc.children_positive),
                         "bacc_mean": float(bacc["mean"]), "bacc_ci_lo": float(bacc.ci_lo), "bacc_ci_hi": float(bacc.ci_hi),
                         "g_hist_mean": float(g["mean"]), "g_hist_ci_lo": float(g.ci_lo), "g_hist_ci_hi": float(g.ci_hi),
                         "children_g_hist_gt_0": int(g.children_positive),
                         "g_prior_mean": float(gp["mean"]) if gp is not None else np.nan,
                         "g_prior_ci_lo": float(gp.ci_lo) if gp is not None else np.nan,
                         "readable_by_frozen_rule": bool(auc.ci_lo > 0.5 and g.ci_lo > 0)})
    return pd.DataFrame(rows)


def _fmt(x, nd=3):
    return "nan" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{nd}f}"


def write_results_md(config: dict, run: str, readouts: dict[str, dict], rules: pd.DataFrame, scope: dict,
                     support: pd.DataFrame, probe: dict, figures: dict[str, list[Path]], out_dir: Path) -> Path:
    lines = []
    lines.append(f"# ST1 结果（中性报告）：做法一第一轮，刺激×时间解码画像")
    lines.append("")
    lines.append(f"**运行：** `{run}`；预注册 `docs/auditory_st/ST1_PREREGISTRATION_FROZEN.md`（含附录 A/B）；配置 `configs/auditory_st_v1.yaml`。  ")
    lines.append("**性质：** 表格、区间、QC 与哈希。解释只到预注册第 6 节的机械判定；措辞另议。  ")
    lines.append("**单位：** 儿童 = 保守身份组；每个儿童等权；区间 = 以儿童为单位的 bootstrap（n=2000，seed 20260920）。  ")
    lines.append("")
    lines.append("## 1. 进入读出的数据")
    lines.append("")
    lines.append("| lane | 儿童 | 记录 | 试次 | 类别 1 试次 | 窗口数 | post (s) | 保留记录（原因） |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for lane, ro in readouts.items():
        s = ro["summary"]
        held = "; ".join(f"{h['record_id']}({h['reason']})" for h in s.get("held_records", [])) or "无"
        post = float(cfg(config, f"lanes.{lane}.post_seconds"))
        lines.append(f"| `{lane}` | {s['children']} | {s['records']} | {s['trials']} | {s['deviant_trials']} | {s['windows']} | {post:.2f} | {held} |")
    lines.append("")
    lines.append("范围表（`results/auditory_st/ST1_scope_001`）：MFF 203 条记录 / 111 身份组，HA 93 条 / 78 身份组；事件读取 295/295。特征阶段每记录支持见 `results/auditory_st/ST1_features_001/record_support.csv`。")
    if not support.empty:
        lines.append("")
        lines.append("| lane | 记录 | 提取成功 | 满足支持（两类 ≥40 且 ≥4 块） |")
        lines.append("|---|---|---|---|")
        for lane, sub in support.groupby("lane"):
            lines.append(f"| `{lane}` | {len(sub)} | {int((sub.status == 'OK').sum())} | {int(sub.record_supported.fillna(False).astype(bool).sum())} |")
    lines.append("")
    lines.append("## 2. 参照")
    lines.append("")
    lines.append("| lane | 类别先验 p(1) | 先验对数损失 (bits) | 历史模型对数损失 (bits) | 历史 bAcc | 历史 AUC |")
    lines.append("|---|---|---|---|---|---|")
    for lane, ro in readouts.items():
        s, r = ro["summary"], ro["summary"]["references"]
        lines.append(f"| `{lane}` | {_fmt(s['class_prior_p1_mean_over_folds'])} | {_fmt(r['ll_prior'])} | {_fmt(r['ll_hist'])} | {_fmt(r['bacc_hist'])} | {_fmt(r['auc_hist'])} |")
    lines.append("")
    lines.append("## 3. 固定时间带结果与预注册规则的机械判定（第 6 节 E1/E2）")
    lines.append("")
    lines.append("判定规则：某带 AUC 区间下界 > 0.5 且 G_hist 区间下界 > 0 → 可读。G_prior 为校准后验相对类别先验的增益（附录 B1）。")
    lines.append("")
    lines.append("| lane | 带 | 区间 (s) | 儿童 | AUC 均值 [95% CI] | 儿童 AUC>0.5 | bAcc 均值 [CI] | G_hist 均值 [CI] (bits) | 儿童 G_hist>0 | G_prior 均值 (CI 下界) | 规则判定 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rules.itertuples():
        lines.append(f"| `{r.lane}` | {r.band} | [{r.from_s:.2f}, {r.to_s:.2f}) | {r.children} | {r.auc_mean:.3f} [{r.auc_ci_lo:.3f}, {r.auc_ci_hi:.3f}] | "
                     f"{getattr(r, '_9')}/{r.children} | {r.bacc_mean:.3f} [{r.bacc_ci_lo:.3f}, {r.bacc_ci_hi:.3f}] | "
                     f"{r.g_hist_mean:+.4f} [{r.g_hist_ci_lo:+.4f}, {r.g_hist_ci_hi:+.4f}] | {r.children_g_hist_gt_0}/{r.children} | "
                     f"{_fmt(r.g_prior_mean, 4)} ({_fmt(r.g_prior_ci_lo, 4)}) | {'可读' if r.readable_by_frozen_rule else '不满足'} |")
    lines.append("")
    lines.append("## 4. 时间分辨曲线的峰值描述（描述性，不作为判定）")
    lines.append("")
    lines.append("| lane | 刺激后 AUC 均值最大值 (窗口中心 s) | 该窗 95% CI | 刺激后 G_hist 均值最大值 (s) | 该窗 CI | 预刺激带 AUC 均值最大值 |")
    lines.append("|---|---|---|---|---|---|")
    for lane, ro in readouts.items():
        c = ro["curves"]
        post = c[c.window_centre_s >= 0.04]
        pre = c[c.window_centre_s < 0]
        ia = int(post.auc_mean.idxmax())
        ig = int(post.g_hist_mean.idxmax())
        lines.append(f"| `{lane}` | {c.auc_mean[ia]:.3f} ({c.window_centre_s[ia]:.2f}) | [{c.auc_lo[ia]:.3f}, {c.auc_hi[ia]:.3f}] | "
                     f"{c.g_hist_mean[ig]:+.4f} ({c.window_centre_s[ig]:.2f}) | [{c.g_hist_lo[ig]:+.4f}, {c.g_hist_hi[ig]:+.4f}] | {pre.auc_mean.max():.3f} |")
    lines.append("")
    lines.append("## 5. 跨时间读取（E4，描述性）")
    lines.append("")
    for lane, ro in readouts.items():
        if ro["tg"] is None:
            continue
        m = ro["tg"].to_numpy(dtype=float)
        t = np.array([float(x) for x in ro["tg"].index])
        post = t >= 0.04
        diag = np.diag(m)
        off = m.copy()
        np.fill_diagonal(off, np.nan)
        lines.append(f"- `{lane}`：对角线（同窗）刺激后均值 AUC {np.nanmean(diag[post]):.3f}，最大 {np.nanmax(diag[post]):.3f}；"
                     f"非对角刺激后子矩阵均值 {np.nanmean(off[np.ix_(post, post)]):.3f}，最大 {np.nanmax(off[np.ix_(post, post)]):.3f}；"
                     f"预刺激训练→刺激后测试均值 {np.nanmean(m[np.ix_(~post, post)]):.3f}。图：`{figures.get(lane + '_tg', [''])[0]}`")
    lines.append("")
    lines.append("## 6. 独立时间块重复性（E5）与儿童内次要分析")
    lines.append("")
    lines.append("| lane | 划分 | 儿童 | early 带 Spearman(AUC) 均值 | mid 带 | late 带 | early 带 |A−B| 均值 / 儿童间 SD |")
    lines.append("|---|---|---|---|---|---|---|")
    for lane, ro in readouts.items():
        rep = ro["repeatability"]
        for part in ("early_late_halves", "odd_even_blocks"):
            sub = rep[(rep.partition == part) & (rep.metric == "auc")]
            if sub.empty:
                continue
            def band_mean(lo, hi, col="spearman_block0_block1"):
                s = sub[(sub.window_centre_s >= lo) & (sub.window_centre_s < hi)][col]
                return float(s.mean()) if len(s) else float("nan")
            lines.append(f"| `{lane}` | {part} | {int(sub.children.max())} | {_fmt(band_mean(0.05, 0.25))} | {_fmt(band_mean(0.25, 0.45))} | "
                         f"{_fmt(band_mean(0.45, 9))} | {_fmt(band_mean(0.05, 0.25, 'mean_abs_diff'))} / {_fmt(band_mean(0.05, 0.25, 'between_child_sd'))} |")
    lines.append("")
    for lane, ro in readouts.items():
        w = ro["within"]
        if w.empty:
            continue
        for part in ("early_late_halves", "odd_even_blocks"):
            sub = w[w.partition == part]
            if sub.empty:
                continue
            post = sub[sub.window_centre_s >= 0.04]
            i = int(post.auc_mean.idxmax())
            lines.append(f"- `{lane}` 儿童内（块 A 训练→块 B 测试，{part}，{int(sub.children.max())} 名儿童 / {int(sub.directions.max())} 个方向）："
                         f"刺激后 AUC 均值最大 {post.auc_mean[i]:.3f} [{post.auc_lo[i]:.3f}, {post.auc_hi[i]:.3f}] @ {post.window_centre_s[i]:.2f} s；"
                         f"刺激后各窗均值 {post.auc_mean.mean():.3f}。")
    lines.append("")
    lines.append("## 7. 探针与 QC 披露")
    lines.append("")
    c = probe.get("checks", {})
    lines.append(f"探针 `{probe.get('run')}`（记录 {probe.get('record_id')}，lane {probe.get('lane')}）：门 = {probe.get('gate')}；"
                 f"两次提取逐位一致 {c.get('deterministic_features')}；窗口 {c.get('n_windows')}；接受试次 {c.get('n_accepted')}/{c.get('n_supported_epochs')}"
                 f"（类别 {c.get('accepted_per_class')}）。单记录类别差异统计：平均 |z| 预刺激 {_fmt(c.get('mean_abs_z_pre'))} / 刺激后 {_fmt(c.get('mean_abs_z_post'))}；"
                 f"SE 标准化每窗最大 |z| 预刺激 {_fmt(c.get('se_z_max_per_window_pre_mean'), 2)} / 刺激后 {_fmt(c.get('se_z_max_per_window_post_mean'), 2)}；"
                 f"|z|>2 通道比例预刺激 {_fmt(c.get('frac_channels_se_z_gt2_pre'))} / 刺激后 {_fmt(c.get('frac_channels_se_z_gt2_post'))}。"
                 "这些值与纯噪声期望一致（附录 B2），单记录检查无功效，不作门。")
    lines.append("")
    lines.append("QC 规则：epoch 峰峰值 >150 µV 的通道占比 >10% 或 <0.5 µV 占比 >10% 则拒绝；区间边缘 2 s 保护；记录尺度 = 接受 epoch |x| 中位数。各记录接受数见 `record_support.csv`。")
    lines.append("")
    lines.append("## 8. 图")
    lines.append("")
    for key, paths in figures.items():
        if paths:
            lines.append(f"- {key}: `{paths[0].relative_to(ROOT)}`")
    lines.append("")
    lines.append("## 9. 哈希与运行")
    lines.append("")
    for lane, ro in readouts.items():
        lines.append(f"- `{ro['run']}`（config sha256 `{ro['summary']['config_sha256'][:16]}…`，prereg sha256 `{ro['summary']['prereg_sha256'][:16]}…`）：" +
                     ", ".join(f"{k} `{v[:12]}`" for k, v in ro["hashes"].items()))
    lines.append(f"- 范围表：{', '.join(f'{k} `{v[:12]}`' for k, v in scope.get('table_sha256', {}).items())}")
    lines.append("")
    lines.append("## 10. 本报告不包含")
    lines.append("")
    lines.append("成分命名、任务难度排序、听觉能力解释、与年龄/设备/量表的关系（做法二/四/五另行预注册）。")
    path = out_dir / "ST1_RESULTS.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o644)
    return path
