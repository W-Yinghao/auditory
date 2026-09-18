"""Aggregate reporting from saved predictions only; never refits any model."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from auditory5.provenance import ROOT, require_slurm, write_json
from auditory5.statistics import paired_cluster_bootstrap


def table(frame, columns):
    lines = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---'] * len(columns)) + ' |']
    for row in frame[columns].itertuples(index=False, name=None):
        lines.append('| ' + ' | '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in row) + ' |')
    return '\n'.join(lines)


def run(plan_path, summary, run_name):
    require_slurm()
    plan = json.loads(Path(plan_path).read_text())
    config = plan['config']
    base = ROOT / config['paths']['private_relative']
    public = ROOT / config['paths']['aggregates_relative'] / run_name
    report = ROOT / config['paths']['reports_relative'] / run_name
    report.mkdir(parents=True, exist_ok=False)
    figures = report / 'figures'
    figures.mkdir()
    core = pd.read_parquet(base / 'core_001/clinical_oof.parquet').assign(variant='budget40')
    controls = pd.read_parquet(base / 'controls_001/clinical_sensitivity_oof.parquet')
    all_predictions = pd.concat([core, controls], ignore_index=True)
    mae = all_predictions.groupby(['mode', 'variant', 'model'], sort=True).agg(
        n=('split_group_id', 'nunique'), MAE=('absolute_error', 'mean')).reset_index()
    mae.to_csv(public / 'model_metrics.csv', index=False)
    rows = []
    for (mode, variant), frame in all_predictions.groupby(['mode', 'variant'], sort=True):
        errors = frame.pivot(index='split_group_id', columns='model', values='absolute_error').sort_index()
        assert len(errors) == 52 and not errors.isna().any().any()
        pairs = [('D1_C', model) for model in errors if model not in ['D0_mean', 'D1_C']]
        pairs += [('D2_CV', 'D3_CVN')]
        for baseline, augmented in pairs:
            effect = paired_cluster_bootstrap(errors[baseline], errors[augmented], errors.index,
                                              n_boot=2000, seed=20260917)
            differences = errors[baseline].to_numpy() - errors[augmented].to_numpy()
            loo = (differences.sum() - differences) / (len(differences) - 1)
            fold_effects = []
            mapping = frame.drop_duplicates('split_group_id').set_index('split_group_id').outer_fold
            for fold in range(5):
                ids = mapping.index[mapping == fold]
                fold_effects.append(float((errors.loc[ids, baseline] - errors.loc[ids, augmented]).mean()))
            rows.append(dict(mode=mode, variant=variant, baseline=baseline, augmented=augmented,
                             n=len(errors), **effect, leave_one_out_min=float(loo.min()),
                             leave_one_out_max=float(loo.max()), positive_folds=sum(x > 0 for x in fold_effects),
                             fold_min=min(fold_effects), fold_max=max(fold_effects)))
    contrasts = pd.DataFrame(rows)
    contrasts.to_csv(public / 'contrasts.csv', index=False)
    modes = ['L0', 'R_SUP', 'R_SIM']
    variants = ['budget40', 'all_trials', 'budget40_count_qc', 'all_trials_count_qc']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True, constrained_layout=True)
    labels = [f'{mode} / {variant}' for mode in modes for variant in variants]
    colors = {'L0': '#757575', 'R_SUP': '#b05b20', 'R_SIM': '#2576a5'}
    for ax, baseline, title in zip(axes, ['D2_CV', 'D1_C'], ['Null contribution beyond C + visible', 'Visible + null beyond clinical C']):
        for i, (mode, variant) in enumerate((m, v) for m in modes for v in variants):
            r = contrasts[(contrasts['mode'] == mode) & (contrasts.variant == variant) &
                          (contrasts.baseline == baseline) & (contrasts.augmented == 'D3_CVN')].iloc[0]
            ax.plot([r.ci_lower, r.ci_upper], [i, i], color=colors[mode], lw=1.5)
            ax.scatter([r.estimate], [i], color=colors[mode], s=22, zorder=3)
        ax.axvline(0, color='black', linewidth=.7)
        ax.set_title(title)
        ax.set_xlabel('MAE reduction (source score points)')
        ax.grid(axis='x', alpha=.2)
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    fig.suptitle('Corrected cohort, fully retrained encoders: n = 52\nPointwise 95% identity bootstrap intervals conditional on saved OOF predictions', fontsize=10)
    fig.savefig(figures / 'clinical_increments.pdf')
    fig.savefig(figures / 'clinical_increments.png', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.3), sharey=True, constrained_layout=True)
    for ax, mode in zip(axes, modes):
        selected = contrasts[(contrasts['mode'] == mode) & (contrasts.variant == 'budget40') & (contrasts.baseline == 'D1_C')]
        random = selected[selected.augmented.str.startswith('D6_CRANDOM_')].sort_values('estimate')
        ax.scatter(np.arange(1, 21), random.estimate, color=colors[mode], s=16)
        main = float(selected[selected.augmented == 'D3_CVN'].estimate.iloc[0])
        ax.axhline(main, color='#222222', label='C + visible + null')
        ax.axhline(0, color='#aaaaaa', linestyle='--')
        ax.set_title(mode)
        ax.set_xlabel('Random null subspace (sorted)')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('MAE reduction beyond clinical C')
    axes[0].legend(fontsize=8)
    fig.savefig(figures / 'random_null_controls.pdf')
    fig.savefig(figures / 'random_null_controls.png', dpi=180)
    plt.close(fig)
    main_models = ['D0_mean', 'D1_C', 'D2_CV', 'D3_CVN', 'D4_CN', 'D5_CFULL', 'D7_CPRE']
    main_mae = mae[(mae.variant == 'budget40') & mae.model.isin(main_models)]
    display = contrasts[(contrasts.augmented == 'D3_CVN')].copy()
    display['95%区间'] = display.apply(lambda r: f'[{r.ci_lower:.3f}, {r.ci_upper:.3f}]', axis=1)
    display['去一人范围'] = display.apply(lambda r: f'[{r.leave_one_out_min:.3f}, {r.leave_one_out_max:.3f}]', axis=1)
    display = display.rename(columns={'mode': '表征', 'variant': '分析', 'baseline': '比较基线', 'estimate': '增益', 'positive_folds': '正向外折数'})
    main = contrasts[(contrasts['mode'] == 'R_SIM') & (contrasts.variant == 'budget40') &
                     (contrasts.baseline == 'D2_CV') & (contrasts.augmented == 'D3_CVN')].iloc[0]
    full = contrasts[(contrasts['mode'] == 'R_SIM') & (contrasts.variant == 'budget40') &
                     (contrasts.baseline == 'D1_C') & (contrasts.augmented == 'D3_CVN')].iloc[0]
    null_probe = json.loads((ROOT / config['paths']['aggregates_relative'] / 'controls_001/null_stimulus_probe.json').read_text())
    null_rows = []
    for row in null_probe:
        interval = row['J_bits']
        null_rows.append(dict(mode=row['mode'], probability=row['probability_mode'], CE_bits=row['ce_bits'],
                              J_bits=interval['estimate'], CI95=f"[{interval['ci_lower']:.3f}, {interval['ci_upper']:.3f}]"))
    head_calls = {name: json.loads((base / name / 'execution_receipt.json').read_text())['head_calls']
                  for name in ['core_001', 'controls_001']}
    write_json(public / 'report_accounting.json', dict(clinical_head_calls=head_calls,
               report_model_refits=0, bootstrap_intervals='pointwise fixed OOF; no training refits or multiplicity adjustment'))
    old_table = []
    for item in summary['old_corrected_replay_comparison']:
        for model in ['D1_C', 'D2_CV', 'D3_CVN']:
            old_table.append({'mode': item['mode'], 'n_common': item['intersection_candidates'], 'model': model,
                              'MAE_new_minus_old': item['MAE_new_minus_old'][model]})
    text = f'''# 修正队列与新划分下的完整编码器重训

第一项已完成：40 个学习编码器、5 个固定表征任务，以及相应的嵌套临床读出和预定对照均已完成并通过独立核验。
R_SIM 主要分析中，在临床变量与刺激可见方向之外加入 null 特征，MAE 改善为 {main.estimate:+.3f} 分，
95% 条件 bootstrap 区间 [{main.ci_lower:.3f}, {main.ci_upper:.3f}]；相对纯临床模型，
可见与 null 联合特征改善为 {full.estimate:+.3f} 分，区间 [{full.ci_lower:.3f}, {full.ci_upper:.3f}]。
完整正向、接近零和负向比较均保留，不使用效应大小或显著性作为停止门槛。

## 实际完成范围

- 原工作表行号修正后的 PTA；临床完整且满足既定 EEG 支持规则的52个候选身份。
- 外层支持身份共60个，37个外层折归属改变；5外折，各3内折。
- R_SUP 与 R_SIM 各20个独立训练范围，全部从头训练。5个L0外层表征；L0内层刺激头、标准化、PCA重新拟合。
- 三种表征各27个主要模型；全试次各27模型；两项试次数／QC敏感性各3模型；新训练的null刺激探针；FP64/FP32不变性检验。
- 实际GPU：{', '.join(summary['actual_GPU_names'])}。相关43项模块测试通过，准备阶段427个EEG文件校验通过。

## 主要模型绝对误差

原始MUSS来源分值单位，越小越好。C为年龄、设备使用时长的log1p值和修正后的较好耳PTA；
V为刺激可见方向，N为该头的null方向。FULL/PRE分别为完整刺激后／刺激前表征。

{table(main_mae, ['mode', 'model', 'n', 'MAE'])}

## 增量、对照和影响范围

增益 = 比较基线MAE − D3_CVN MAE；正值代表改善。区间是2000次候选身份bootstrap，
以已保存的外层OOF预测为条件。它不包含编码器重训／划分不确定性，也未作多重比较校正。
去一人范围仅重算误差均值，不重新训练模型。正向外折数用于描述，不是独立重复实验。

{table(display, ['表征', '分析', '比较基线', '增益', '95%区间', '正向外折数', '去一人范围'])}

全部模型的误差见同版本 `model_metrics.csv`；包括20个随机null方向的全部点估计、区间与影响范围见 `contrasts.csv`。
全试次敏感性沿用本轮相应训练范围内重新拟合的投影基，只改变试次汇总；临床惩罚在相同内折重新选择。
count/QC敏感性加入最少条件接受试次数的log1p和目标事件拒绝比例。这些控制不等于排除所有技术或临床混杂。
随机方向图用于判断方向特异性；不能将普通随机子空间也能得到的改善直接归因于功能分离。
`null_stimulus_probe.json` 保留新刺激头的解码诊断；几何上消除旧线性头的方向，不保证新头无法重新读出刺激信息。
FP32控制的通过仅说明相应数值恒等近似成立，不是临床有效性检验。

新null刺激探针的J = 1 − 条件／候选平衡交叉熵，正值表示优于平衡机会基线。
它在对应外层临床训练身份上重新拟合，在该折临床测试身份上评估；内部刺激头调参为固定上游表征下的条件验证。

{table(pd.DataFrame(null_rows), ['mode', 'probability', 'CE_bits', 'J_bits', 'CI95'])}

## 与上一轮修正PTA、旧划分回放的交集比较

正数表示本轮误差更高。这里同时改变训练队列、外层／内层划分和拟合表征，
且旧51人分析保留两条修正后PTA缺失记录并在训练折内插补，新52人分析采用原定义的完整临床支持。
因此这不是单独增加一人的因果效果，也不是独立验证。

{table(pd.DataFrame(old_table), ['mode', 'n_common', 'model', 'MAE_new_minus_old'])}

## 训练、核验与解释限制

固定seed11，沿用原SmallEEGCNN及优化超参数。SIM全部100epochs；SUP使用当前训练身份内部的刺激损失监测，
max80/patience12，并按选定轮数重新初始化网络和标准化、用当前训练范围全量重训。
SUP所选epoch集合：{summary['checkpoint_epochs']['R_SUP']}。临床结果从未用于科学提前停止。
外层测试身份和临床内层验证身份的全部EEG均排除在对应编码器拟合之外。
标准化、刺激头和临床PCA/投影的拟合范围逐项保存并核验；表征、临床表及epoch ID保持绑定。

临床主分析调用次数：{head_calls['core_001']}；对照阶段：{head_calls['controls_001']}。
这些计数是临床岭预测函数调用，包含内层候选和均值模型，不是独立模型数或统计检验数；
不包含刺激分类头拟合、神经网络优化步骤和43项测试。汇总和核验没有重新拟合任何模型。

这是反复研究过的档案数据上的单seed探索。候选身份不能无条件视为已核实独立儿童；
量表与EEG同期性、部分设备状态与量表／阈值单位仍依赖来源证据。事件1/2仍保留字面编码。
本轮完成HA D的新队列／新划分重训；它没有新增独立临床队列验证，也没有补出真实功能随访。
原始数据只读，个人数据和权重留在private，未自动推送GitHub。

图表：`figures/clinical_increments.pdf` 与 `figures/random_null_controls.pdf`，各有PNG副本。
'''
    (report / 'REPORT.md').write_text(text)
    write_json(public / 'null_stimulus_probe.json', null_probe)
    return report
