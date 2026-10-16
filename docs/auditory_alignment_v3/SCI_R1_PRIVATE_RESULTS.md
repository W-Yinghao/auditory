# SCI_R1 私有任务结果（docs/13 S1、S4 的私有部分；第 1 轮）

> **发布副本**：只含组层面聚合，不含任何逐儿童数值；私有原件标题注明本文件为 0600 私有文件、不作发布候选，其余未改动。

> 预登记：`SCI_R1_PREREG.md`（冻结 v3）。
> 只含组层面聚合，汇总存于 `results/auditory_alignment_v3/sci_r1/private_agg/`（0700）。逐儿童数据与一切空间模式只存 `private/`。
> 儿童：HA 55、NH 9，共 64 名；n<5 的格只报 n。
> AUC 为每名儿童的 AUC 取均值。NLL 为正斜率仿射校准后的自然 NLL（比特/试次）。
> 历史条件主量（`hist_gain_bits`）定义为 `R(q_hist) − R(q_hist+EEG_k)`，为负表示加入该 lag 的 EEG 后风险升高。

## 1. 窗口值（全部儿童；冻结 = E_LOCAL P0，旧基线 = ALN2 D_TASK_LOCAL）

| 曲线 | 指标 | 早窗 | 晚窗 |
|---|---|---|---|
| NCE frozen | auc | +0.5105 [+0.5044, +0.5167] (n=64) | +0.5168 [+0.5108, +0.5228] (n=64) |
| NCE frozen | hist_gain_bits | -0.0028 [-0.0039, -0.0018] (n=64) | -0.0025 [-0.0078, +0.0028] (n=64) |
| NCE frozen_3seed | auc | +0.5081 [+0.5010, +0.5153] (n=64) | +0.5154 [+0.5095, +0.5212] (n=64) |
| NCE frozen_3seed | hist_gain_bits | -0.0033 [-0.0039, -0.0027] (n=64) | -0.0023 [-0.0076, +0.0030] (n=64) |
| NCE aln2 | auc | +0.5044 [+0.4970, +0.5118] (n=64) | +0.5154 [+0.5089, +0.5219] (n=64) |
| NCE aln2 | hist_gain_bits | -0.0041 [-0.0050, -0.0032] (n=64) | -0.0020 [-0.0094, +0.0054] (n=64) |
| NCE untrained_s3401 | auc | +0.5032 [+0.4968, +0.5096] (n=64) | +0.5148 [+0.5081, +0.5216] (n=64) |
| NCE untrained_s3401 | hist_gain_bits | -0.0029 [-0.0047, -0.0010] (n=64) | -0.0022 [-0.0073, +0.0030] (n=64) |
| NCE untrained_3draws | auc | +0.5053 [+0.4990, +0.5116] (n=64) | +0.5162 [+0.5100, +0.5224] (n=64) |
| NCE untrained_3draws | hist_gain_bits | -0.0027 [-0.0039, -0.0016] (n=64) | -0.0020 [-0.0090, +0.0050] (n=64) |
| CS_SINGLE frozen | auc | +0.5061 [+0.4986, +0.5137] (n=64) | +0.5135 [+0.5064, +0.5206] (n=64) |
| CS_SINGLE frozen | hist_gain_bits | -0.0034 [-0.0041, -0.0026] (n=64) | -0.0028 [-0.0065, +0.0009] (n=64) |
| CS_SINGLE frozen_3seed | auc | +0.5086 [+0.5017, +0.5155] (n=64) | +0.5148 [+0.5081, +0.5215] (n=64) |
| CS_SINGLE frozen_3seed | hist_gain_bits | -0.0032 [-0.0038, -0.0026] (n=64) | -0.0020 [-0.0071, +0.0030] (n=64) |
| CS_SINGLE aln2 | auc | +0.5027 [+0.4952, +0.5101] (n=64) | +0.5156 [+0.5096, +0.5216] (n=64) |
| CS_SINGLE aln2 | hist_gain_bits | -0.0029 [-0.0042, -0.0017] (n=64) | -0.0014 [-0.0086, +0.0058] (n=64) |
| CS_SINGLE untrained_s3401 | auc | +0.5032 [+0.4968, +0.5096] (n=64) | +0.5148 [+0.5081, +0.5216] (n=64) |
| CS_SINGLE untrained_s3401 | hist_gain_bits | -0.0029 [-0.0047, -0.0010] (n=64) | -0.0022 [-0.0073, +0.0030] (n=64) |
| CS_SINGLE untrained_3draws | auc | +0.5053 [+0.4990, +0.5116] (n=64) | +0.5162 [+0.5100, +0.5224] (n=64) |
| CS_SINGLE untrained_3draws | hist_gain_bits | -0.0027 [-0.0039, -0.0016] (n=64) | -0.0020 [-0.0090, +0.0050] (n=64) |
| NCE md (P0) | NLL increase | +0.0005 [+0.0001, +0.0010] (n=64) | +0.0006 [+0.0003, +0.0010] (n=64) |
| CS_SINGLE md (P0) | NLL increase | +0.0017 [+0.0008, +0.0026] (n=64) | +0.0012 [+0.0005, +0.0019] (n=64) |
| NCE sb (P0) | NLL increase | +0.0008 [+0.0001, +0.0016] (n=64) | +0.0006 [-0.0002, +0.0014] (n=64) |
| CS_SINGLE sb (P0) | NLL increase | +0.0012 [+0.0001, +0.0022] (n=64) | +0.0016 [+0.0003, +0.0028] (n=64) |

## 2. 窗口三件套（单元记录；正斜率仿射 NLL）

| 目标|objective | seed | R(E)−R(E,L) | R(L)−R(E,L) | R(E,L)−R(full) |
|---|---|---|---|---|
| local|NCE | 3401,3407,3413 | +0.000 [-0.000, +0.000] (n=64) | +0.000 [-0.000, +0.001] (n=64) | +0.000 [-0.000, +0.001] (n=64) |
| local|CS_SINGLE | 3401 | +0.000 [-0.000, +0.001] (n=64) | +0.001 [-0.000, +0.002] (n=64) | +0.002 [+0.000, +0.003] (n=64) |

## 3. 时间泛化（AUC 与 NLL）

离对角的 AUC 低于 0.5 时，表示读出方向反转（预登记解读表）。

| 模型 | 格值 | D_E | D_L | G_EL | G_LE | D_E−G_EL | D_L−G_LE |
|---|---|---|---|---|---|---|---|
| NCE frozen | AUC | +0.511 [+0.504, +0.517] (n=64) | +0.517 [+0.511, +0.523] (n=64) | +0.493 [+0.487, +0.499] (n=64) | +0.491 [+0.482, +0.499] (n=64) | +0.017 [+0.010, +0.025] (n=64) | +0.026 [+0.016, +0.036] (n=64) |
| NCE frozen | NLL | +0.719 [+0.713, +0.725] (n=64) | +0.720 [+0.714, +0.726] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.002] (n=64) | +0.002 [+0.001, +0.003] (n=64) |
| NCE raw | AUC | +0.504 [+0.497, +0.511] (n=64) | +0.510 [+0.503, +0.516] (n=64) | +0.500 [+0.495, +0.506] (n=64) | +0.496 [+0.490, +0.501] (n=64) | +0.004 [-0.003, +0.010] (n=64) | +0.014 [+0.007, +0.020] (n=64) |
| NCE raw | NLL | +0.737 [+0.731, +0.743] (n=64) | +0.739 [+0.731, +0.747] (n=64) | +0.719 [+0.713, +0.726] (n=64) | +0.720 [+0.713, +0.726] (n=64) | +0.018 [+0.013, +0.023] (n=64) | +0.019 [+0.012, +0.026] (n=64) |
| NCE untrained_s3401 | AUC | +0.503 [+0.497, +0.510] (n=64) | +0.515 [+0.508, +0.522] (n=64) | +0.496 [+0.490, +0.502] (n=64) | +0.489 [+0.482, +0.496] (n=64) | +0.007 [-0.002, +0.017] (n=64) | +0.026 [+0.016, +0.035] (n=64) |
| NCE untrained_s3401 | NLL | +0.720 [+0.714, +0.726] (n=64) | +0.720 [+0.714, +0.726] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.003] (n=64) | +0.002 [+0.001, +0.003] (n=64) |
| NCE aln2 | AUC | +0.504 [+0.497, +0.512] (n=64) | +0.515 [+0.509, +0.522] (n=64) | +0.495 [+0.489, +0.502] (n=64) | +0.488 [+0.480, +0.496] (n=64) | +0.009 [+0.000, +0.018] (n=64) | +0.027 [+0.017, +0.038] (n=64) |
| NCE aln2 | NLL | +0.720 [+0.715, +0.725] (n=64) | +0.720 [+0.714, +0.726] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.003] (n=64) | +0.002 [+0.001, +0.003] (n=64) |
| CS_SINGLE frozen | AUC | +0.506 [+0.499, +0.514] (n=64) | +0.513 [+0.506, +0.521] (n=64) | +0.497 [+0.491, +0.503] (n=64) | +0.493 [+0.484, +0.501] (n=64) | +0.009 [-0.000, +0.019] (n=64) | +0.021 [+0.010, +0.031] (n=64) |
| CS_SINGLE frozen | NLL | +0.720 [+0.714, +0.725] (n=64) | +0.720 [+0.714, +0.727] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.003] (n=64) | +0.002 [+0.001, +0.004] (n=64) |
| CS_SINGLE raw | AUC | +0.504 [+0.497, +0.511] (n=64) | +0.510 [+0.503, +0.516] (n=64) | +0.500 [+0.495, +0.506] (n=64) | +0.496 [+0.490, +0.501] (n=64) | +0.004 [-0.003, +0.010] (n=64) | +0.014 [+0.007, +0.020] (n=64) |
| CS_SINGLE raw | NLL | +0.737 [+0.731, +0.743] (n=64) | +0.739 [+0.731, +0.747] (n=64) | +0.719 [+0.713, +0.726] (n=64) | +0.720 [+0.713, +0.726] (n=64) | +0.018 [+0.013, +0.023] (n=64) | +0.019 [+0.012, +0.026] (n=64) |
| CS_SINGLE untrained_s3401 | AUC | +0.503 [+0.497, +0.510] (n=64) | +0.515 [+0.508, +0.522] (n=64) | +0.496 [+0.490, +0.502] (n=64) | +0.489 [+0.482, +0.496] (n=64) | +0.007 [-0.002, +0.017] (n=64) | +0.026 [+0.016, +0.035] (n=64) |
| CS_SINGLE untrained_s3401 | NLL | +0.720 [+0.714, +0.726] (n=64) | +0.720 [+0.714, +0.726] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.003] (n=64) | +0.002 [+0.001, +0.003] (n=64) |
| CS_SINGLE aln2 | AUC | +0.503 [+0.495, +0.510] (n=64) | +0.516 [+0.510, +0.522] (n=64) | +0.500 [+0.493, +0.506] (n=64) | +0.490 [+0.482, +0.498] (n=64) | +0.003 [-0.006, +0.012] (n=64) | +0.026 [+0.015, +0.036] (n=64) |
| CS_SINGLE aln2 | NLL | +0.720 [+0.715, +0.726] (n=64) | +0.720 [+0.713, +0.726] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.718 [+0.711, +0.725] (n=64) | +0.002 [+0.001, +0.003] (n=64) | +0.002 [+0.001, +0.003] (n=64) |

## 4. 组间（HA−NH）与发育

NH 只有 9 名儿童，组差的检验力低。私有分箱阶段沿用 docs/08（0–2 月、2<月数<13、≥13 月，NH 单列）。

| 族 | 对象 | 组差 | 估计 [95% CI] {族内同时区间} |
|---|---|---|---|
| NCE | auc_early | HA-NH | -0.013 [-0.032, +0.006] {-0.046, +0.021} (n=55) |
| NCE | hist_increment_early | HA-NH | -0.000 [-0.002, +0.002] {-0.004, +0.004} (n=55) |
| NCE | twin_sensitivity_early | HA-NH | -0.002 [-0.004, +0.001] {-0.006, +0.003} (n=55) |
| NCE | auc_late | HA-NH | +0.003 [-0.013, +0.018] {-0.025, +0.031} (n=55) |
| NCE | hist_increment_late | HA-NH | +0.002 [-0.003, +0.008] {-0.006, +0.011} (n=55) |
| NCE | twin_sensitivity_late | HA-NH | +0.002 [-0.002, +0.007] {-0.005, +0.010} (n=55) |
| NCE | auc_late_minus_early | HA-NH | +0.016 [-0.004, +0.036] {-0.021, +0.053} (n=55) |
| NCE | MD_R_early | HA-NH | -0.001 [-0.003, +0.002] {-0.005, +0.003} (n=55) |
| NCE | MD_R_late | HA-NH | -0.000 [-0.001, +0.001] {-0.002, +0.001} (n=55) |
| NCE | SB_R_early | HA-NH | -0.003 [-0.005, +0.000] {-0.007, +0.002} (n=55) |
| NCE | SB_R_late | HA-NH | -0.001 [-0.003, +0.002] {-0.005, +0.004} (n=55) |
| NCE | triad_R_early_minus_R_joint | HA-NH | +0.000 [-0.000, +0.001] {-0.001, +0.001} (n=55) |
| NCE | triad_R_late_minus_R_joint | HA-NH | +0.000 [-0.001, +0.002] {-0.003, +0.003} (n=55) |
| NCE | tg_D_E | HA-NH | -0.013 [-0.032, +0.006] {-0.046, +0.021} (n=55) |
| NCE | tg_D_L | HA-NH | +0.003 [-0.013, +0.018] {-0.025, +0.031} (n=55) |
| NCE | tg_G_EL | HA-NH | +0.013 [-0.008, +0.034] {-0.021, +0.047} (n=55) |
| NCE | tg_G_LE | HA-NH | +0.017 [-0.020, +0.053] {-0.046, +0.079} (n=55) |
| NCE | tg_D_E_minus_G_EL | HA-NH | -0.026 [-0.056, +0.004] {-0.082, +0.030} (n=55) |
| NCE | tg_D_L_minus_G_LE | HA-NH | -0.014 [-0.052, +0.024] {-0.083, +0.054} (n=55) |
| CS_SINGLE | auc_early | HA-NH | -0.025 [-0.048, -0.002] {-0.066, +0.016} (n=55) |
| CS_SINGLE | hist_increment_early | HA-NH | -0.001 [-0.003, +0.001] {-0.005, +0.002} (n=55) |
| CS_SINGLE | twin_sensitivity_early | HA-NH | -0.002 [-0.007, +0.002] {-0.008, +0.003} (n=55) |
| CS_SINGLE | auc_late | HA-NH | +0.007 [-0.015, +0.029] {-0.033, +0.047} (n=55) |
| CS_SINGLE | hist_increment_late | HA-NH | +0.002 [-0.003, +0.007] {-0.006, +0.010} (n=55) |
| CS_SINGLE | twin_sensitivity_late | HA-NH | +0.003 [-0.001, +0.006] {-0.004, +0.009} (n=55) |
| CS_SINGLE | auc_late_minus_early | HA-NH | +0.032 [+0.010, +0.054] {-0.007, +0.071} (n=55) |
| CS_SINGLE | MD_R_early | HA-NH | -0.004 [-0.006, -0.001] {-0.009, +0.002} (n=55) |
| CS_SINGLE | MD_R_late | HA-NH | +0.001 [-0.002, +0.003] {-0.004, +0.005} (n=55) |
| CS_SINGLE | SB_R_early | HA-NH | -0.005 [-0.008, -0.002] {-0.010, +0.000} (n=55) |
| CS_SINGLE | SB_R_late | HA-NH | +0.000 [-0.003, +0.003] {-0.006, +0.006} (n=55) |
| CS_SINGLE | triad_R_early_minus_R_joint | HA-NH | +0.000 [-0.002, +0.002] {-0.003, +0.003} (n=55) |
| CS_SINGLE | triad_R_late_minus_R_joint | HA-NH | -0.002 [-0.004, +0.000] {-0.005, +0.002} (n=55) |
| CS_SINGLE | tg_D_E | HA-NH | -0.025 [-0.048, -0.002] {-0.066, +0.016} (n=55) |
| CS_SINGLE | tg_D_L | HA-NH | +0.007 [-0.015, +0.029] {-0.033, +0.047} (n=55) |
| CS_SINGLE | tg_G_EL | HA-NH | +0.016 [-0.006, +0.037] {-0.022, +0.053} (n=55) |
| CS_SINGLE | tg_G_LE | HA-NH | +0.017 [-0.011, +0.044] {-0.032, +0.065} (n=55) |
| CS_SINGLE | tg_D_E_minus_G_EL | HA-NH | -0.041 [-0.076, -0.006] {-0.099, +0.017} (n=55) |
| CS_SINGLE | tg_D_L_minus_G_LE | HA-NH | -0.010 [-0.052, +0.033] {-0.084, +0.065} (n=55) |
| raw | raw_auc_early | HA-NH | -0.027 [-0.047, -0.007] {-0.053, -0.001} (n=55) |
| raw | raw_auc_late | HA-NH | -0.004 [-0.020, +0.011] {-0.024, +0.015} (n=55) |
| raw | prestim_mean_auc | HA-NH | -0.001 [-0.015, +0.012] {-0.018, +0.016} (n=55) |

| 模型 | 系数 | 估计 [95% CI] (n) |
|---|---|---|
| NCE|auc_early|age+HA | age_months | -0.0000 [-0.0002, +0.0002] (n=64)  |
| NCE|auc_early|HA:age+duration | duration_months | +0.0001 [-0.0002, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|auc_early|stage_bins | 阶段分箱 | ge13: +0.508 [+0.500, +0.516] (n=36); 0_2: +0.509 [+0.491, +0.527] (n=14); NH: +0.522 [+0.502, +0.541] (n=9); 2_13: +0.513 [+0.463, +0.563] (n=5) |
| NCE|hist_increment_early|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|hist_increment_early|HA:age+duration | duration_months | +0.0000 [+0.0000, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|hist_increment_early|stage_bins | 阶段分箱 | ge13: -0.002 [-0.004, -0.001] (n=36); 0_2: -0.003 [-0.005, -0.001] (n=14); NH: -0.003 [-0.005, -0.001] (n=9); 2_13: -0.005 [-0.011, +0.001] (n=5) |
| NCE|twin_sensitivity_early|age+HA | age_months | -0.0000 [-0.0001, +0.0000] (n=64)  |
| NCE|twin_sensitivity_early|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|twin_sensitivity_early|stage_bins | 阶段分箱 | ge13: -0.000 [-0.002, +0.002] (n=36); 0_2: +0.002 [-0.001, +0.004] (n=14); NH: +0.002 [-0.001, +0.004] (n=9); 2_13: -0.002 [-0.011, +0.007] (n=5) |
| NCE|auc_late|age+HA | age_months | +0.0001 [-0.0001, +0.0002] (n=64)  |
| NCE|auc_late|HA:age+duration | duration_months | -0.0001 [-0.0003, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|auc_late|stage_bins | 阶段分箱 | ge13: +0.516 [+0.508, +0.525] (n=36); 0_2: +0.514 [+0.498, +0.530] (n=14); NH: +0.514 [+0.500, +0.529] (n=9); 2_13: +0.532 [+0.368, +0.696] (n=5) |
| NCE|hist_increment_late|age+HA | age_months | +0.0000 [-0.0001, +0.0002] (n=64)  |
| NCE|hist_increment_late|HA:age+duration | duration_months | +0.0000 [-0.0001, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|hist_increment_late|stage_bins | 阶段分箱 | ge13: -0.002 [-0.013, +0.010] (n=36); 0_2: -0.004 [-0.007, -0.001] (n=14); NH: -0.004 [-0.008, -0.001] (n=9); 2_13: -0.001 [-0.015, +0.014] (n=5) |
| NCE|twin_sensitivity_late|age+HA | age_months | +0.0000 [-0.0001, +0.0001] (n=64)  |
| NCE|twin_sensitivity_late|HA:age+duration | duration_months | -0.0000 [-0.0001, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|twin_sensitivity_late|stage_bins | 阶段分箱 | ge13: +0.002 [-0.003, +0.007] (n=36); 0_2: +0.001 [-0.002, +0.003] (n=14); NH: -0.000 [-0.007, +0.007] (n=9); 2_13: +0.005 [-0.001, +0.011] (n=5) |
| NCE|auc_late_minus_early|age+HA | age_months | +0.0001 [-0.0002, +0.0004] (n=64)  |
| NCE|auc_late_minus_early|HA:age+duration | duration_months | -0.0001 [-0.0005, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|auc_late_minus_early|stage_bins | 阶段分箱 | ge13: +0.008 [-0.002, +0.019] (n=36); 0_2: +0.005 [-0.025, +0.034] (n=14); NH: -0.007 [-0.025, +0.011] (n=9); 2_13: +0.019 [-0.058, +0.097] (n=5) |
| NCE|MD_R_early|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|MD_R_early|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|MD_R_early|stage_bins | 阶段分箱 | ge13: +0.001 [+0.000, +0.001] (n=36); 0_2: +0.000 [-0.001, +0.001] (n=14); NH: +0.001 [-0.001, +0.004] (n=9); 2_13: -0.000 [-0.002, +0.001] (n=5) |
| NCE|MD_R_late|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|MD_R_late|HA:age+duration | duration_months | -0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|MD_R_late|stage_bins | 阶段分箱 | ge13: +0.001 [+0.000, +0.001] (n=36); 0_2: +0.001 [-0.000, +0.001] (n=14); NH: +0.001 [+0.000, +0.001] (n=9); 2_13: +0.001 [-0.001, +0.002] (n=5) |
| NCE|SB_R_early|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|SB_R_early|HA:age+duration | duration_months | -0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|SB_R_early|stage_bins | 阶段分箱 | ge13: +0.000 [-0.001, +0.001] (n=36); 0_2: +0.000 [-0.001, +0.002] (n=14); NH: +0.003 [+0.001, +0.006] (n=9); 2_13: +0.002 [-0.003, +0.008] (n=5) |
| NCE|SB_R_late|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|SB_R_late|HA:age+duration | duration_months | -0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|SB_R_late|stage_bins | 阶段分箱 | ge13: +0.000 [-0.001, +0.001] (n=36); 0_2: +0.001 [-0.001, +0.002] (n=14); NH: +0.001 [-0.001, +0.004] (n=9); 2_13: +0.002 [-0.003, +0.006] (n=5) |
| NCE|triad_R_early_minus_R_joint|age+HA | age_months | -0.0000 [-0.0000, -0.0000] (n=64)  |
| NCE|triad_R_early_minus_R_joint|HA:age+duration | duration_months | -0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|triad_R_early_minus_R_joint|stage_bins | 阶段分箱 | ge13: +0.000 [-0.000, +0.001] (n=36); 0_2: +0.000 [-0.000, +0.001] (n=14); NH: -0.000 [-0.001, +0.000] (n=9); 2_13: +0.000 [-0.005, +0.005] (n=5) |
| NCE|triad_R_late_minus_R_joint|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| NCE|triad_R_late_minus_R_joint|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|triad_R_late_minus_R_joint|stage_bins | 阶段分箱 | ge13: +0.000 [-0.000, +0.001] (n=36); 0_2: +0.000 [-0.001, +0.001] (n=14); NH: -0.000 [-0.002, +0.002] (n=9); 2_13: +0.001 [-0.002, +0.004] (n=5) |
| NCE|tg_D_E|age+HA | age_months | -0.0000 [-0.0002, +0.0002] (n=64)  |
| NCE|tg_D_E|HA:age+duration | duration_months | +0.0001 [-0.0002, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_D_E|stage_bins | 阶段分箱 | ge13: +0.508 [+0.500, +0.516] (n=36); 0_2: +0.509 [+0.491, +0.527] (n=14); NH: +0.522 [+0.502, +0.541] (n=9); 2_13: +0.513 [+0.463, +0.563] (n=5) |
| NCE|tg_D_L|age+HA | age_months | +0.0001 [-0.0001, +0.0002] (n=64)  |
| NCE|tg_D_L|HA:age+duration | duration_months | -0.0001 [-0.0003, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_D_L|stage_bins | 阶段分箱 | ge13: +0.516 [+0.508, +0.525] (n=36); 0_2: +0.514 [+0.498, +0.530] (n=14); NH: +0.514 [+0.500, +0.529] (n=9); 2_13: +0.532 [+0.368, +0.696] (n=5) |
| NCE|tg_G_EL|age+HA | age_months | -0.0001 [-0.0002, +0.0001] (n=64)  |
| NCE|tg_G_EL|HA:age+duration | duration_months | -0.0000 [-0.0003, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_G_EL|stage_bins | 阶段分箱 | ge13: +0.492 [+0.484, +0.499] (n=36); 0_2: +0.504 [+0.488, +0.519] (n=14); NH: +0.482 [+0.455, +0.509] (n=9); 2_13: +0.497 [+0.455, +0.539] (n=5) |
| NCE|tg_G_LE|age+HA | age_months | -0.0001 [-0.0003, +0.0001] (n=64)  |
| NCE|tg_G_LE|HA:age+duration | duration_months | -0.0000 [-0.0003, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_G_LE|stage_bins | 阶段分箱 | ge13: +0.493 [+0.482, +0.505] (n=36); 0_2: +0.493 [+0.480, +0.506] (n=14); NH: +0.476 [+0.441, +0.512] (n=9); 2_13: +0.492 [+0.460, +0.524] (n=5) |
| NCE|tg_D_E_minus_G_EL|age+HA | age_months | +0.0001 [-0.0001, +0.0002] (n=64)  |
| NCE|tg_D_E_minus_G_EL|HA:age+duration | duration_months | +0.0001 [-0.0002, +0.0004] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_D_E_minus_G_EL|stage_bins | 阶段分箱 | ge13: +0.016 [+0.006, +0.027] (n=36); 0_2: +0.005 [-0.012, +0.023] (n=14); NH: +0.039 [+0.010, +0.069] (n=9); 2_13: +0.016 [-0.157, +0.189] (n=5) |
| NCE|tg_D_L_minus_G_LE|age+HA | age_months | +0.0002 [-0.0001, +0.0004] (n=64)  |
| NCE|tg_D_L_minus_G_LE|HA:age+duration | duration_months | -0.0000 [-0.0004, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| NCE|tg_D_L_minus_G_LE|stage_bins | 阶段分箱 | ge13: +0.023 [+0.010, +0.036] (n=36); 0_2: +0.021 [-0.001, +0.043] (n=14); NH: +0.038 [-0.000, +0.077] (n=9); 2_13: +0.040 [-0.010, +0.089] (n=5) |
| CS_SINGLE|auc_early|age+HA | age_months | +0.0000 [-0.0002, +0.0002] (n=64)  |
| CS_SINGLE|auc_early|HA:age+duration | duration_months | -0.0000 [-0.0003, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|auc_early|stage_bins | 阶段分箱 | ge13: +0.502 [+0.491, +0.512] (n=36); 0_2: +0.506 [+0.491, +0.521] (n=14); NH: +0.528 [+0.505, +0.550] (n=9); 2_13: +0.502 [+0.473, +0.530] (n=5) |
| CS_SINGLE|hist_increment_early|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|hist_increment_early|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|hist_increment_early|stage_bins | 阶段分箱 | ge13: -0.003 [-0.005, -0.002] (n=36); 0_2: -0.004 [-0.005, -0.002] (n=14); NH: -0.002 [-0.004, -0.000] (n=9); 2_13: -0.004 [-0.009, +0.001] (n=5) |
| CS_SINGLE|twin_sensitivity_early|age+HA | age_months | -0.0000 [-0.0002, +0.0001] (n=64)  |
| CS_SINGLE|twin_sensitivity_early|HA:age+duration | duration_months | +0.0000 [-0.0001, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|twin_sensitivity_early|stage_bins | 阶段分箱 | ge13: -0.001 [-0.012, +0.010] (n=36); 0_2: +0.001 [-0.001, +0.003] (n=14); NH: +0.002 [+0.001, +0.003] (n=9); 2_13: -0.001 [-0.003, +0.000] (n=5) |
| CS_SINGLE|auc_late|age+HA | age_months | +0.0000 [-0.0001, +0.0002] (n=64)  |
| CS_SINGLE|auc_late|HA:age+duration | duration_months | -0.0000 [-0.0004, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|auc_late|stage_bins | 阶段分箱 | ge13: +0.515 [+0.506, +0.524] (n=36); 0_2: +0.504 [+0.489, +0.519] (n=14); NH: +0.507 [+0.487, +0.528] (n=9); 2_13: +0.538 [+0.432, +0.645] (n=5) |
| CS_SINGLE|hist_increment_late|age+HA | age_months | +0.0000 [-0.0000, +0.0001] (n=64)  |
| CS_SINGLE|hist_increment_late|HA:age+duration | duration_months | +0.0000 [-0.0001, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|hist_increment_late|stage_bins | 阶段分箱 | ge13: -0.002 [-0.010, +0.006] (n=36); 0_2: -0.005 [-0.008, -0.003] (n=14); NH: -0.005 [-0.008, -0.001] (n=9); 2_13: +0.000 [-0.014, +0.014] (n=5) |
| CS_SINGLE|twin_sensitivity_late|age+HA | age_months | +0.0000 [-0.0000, +0.0001] (n=64)  |
| CS_SINGLE|twin_sensitivity_late|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|twin_sensitivity_late|stage_bins | 阶段分箱 | ge13: +0.002 [-0.002, +0.005] (n=36); 0_2: -0.001 [-0.004, +0.001] (n=14); NH: -0.002 [-0.005, +0.002] (n=9); 2_13: +0.003 [-0.011, +0.017] (n=5) |
| CS_SINGLE|auc_late_minus_early|age+HA | age_months | +0.0000 [-0.0003, +0.0003] (n=64)  |
| CS_SINGLE|auc_late_minus_early|HA:age+duration | duration_months | -0.0000 [-0.0004, +0.0004] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|auc_late_minus_early|stage_bins | 阶段分箱 | ge13: +0.014 [+0.000, +0.027] (n=36); 0_2: -0.002 [-0.024, +0.020] (n=14); NH: -0.020 [-0.043, +0.002] (n=9); 2_13: +0.037 [-0.020, +0.094] (n=5) |
| CS_SINGLE|MD_R_early|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|MD_R_early|HA:age+duration | duration_months | -0.0000 [-0.0001, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|MD_R_early|stage_bins | 阶段分箱 | ge13: +0.001 [-0.000, +0.002] (n=36); 0_2: +0.002 [+0.001, +0.004] (n=14); NH: +0.005 [+0.002, +0.007] (n=9); 2_13: -0.000 [-0.004, +0.003] (n=5) |
| CS_SINGLE|MD_R_late|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|MD_R_late|HA:age+duration | duration_months | -0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|MD_R_late|stage_bins | 阶段分箱 | ge13: +0.002 [+0.001, +0.003] (n=36); 0_2: +0.000 [-0.001, +0.002] (n=14); NH: +0.001 [-0.002, +0.003] (n=9); 2_13: +0.001 [-0.004, +0.006] (n=5) |
| CS_SINGLE|SB_R_early|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|SB_R_early|HA:age+duration | duration_months | -0.0000 [-0.0001, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|SB_R_early|stage_bins | 阶段分箱 | ge13: +0.000 [-0.001, +0.002] (n=36); 0_2: +0.002 [-0.001, +0.004] (n=14); NH: +0.005 [+0.002, +0.009] (n=9); 2_13: -0.003 [-0.024, +0.017] (n=5) |
| CS_SINGLE|SB_R_late|age+HA | age_months | +0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|SB_R_late|HA:age+duration | duration_months | -0.0000 [-0.0001, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|SB_R_late|stage_bins | 阶段分箱 | ge13: +0.002 [-0.000, +0.003] (n=36); 0_2: +0.002 [-0.000, +0.004] (n=14); NH: +0.002 [-0.002, +0.005] (n=9); 2_13: +0.000 [-0.015, +0.016] (n=5) |
| CS_SINGLE|triad_R_early_minus_R_joint|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|triad_R_early_minus_R_joint|HA:age+duration | duration_months | +0.0000 [+0.0000, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|triad_R_early_minus_R_joint|stage_bins | 阶段分箱 | ge13: +0.001 [-0.000, +0.002] (n=36); 0_2: -0.000 [-0.002, +0.002] (n=14); NH: +0.000 [-0.001, +0.002] (n=9); 2_13: -0.001 [-0.008, +0.005] (n=5) |
| CS_SINGLE|triad_R_late_minus_R_joint|age+HA | age_months | -0.0000 [-0.0000, +0.0000] (n=64)  |
| CS_SINGLE|triad_R_late_minus_R_joint|HA:age+duration | duration_months | +0.0000 [-0.0000, +0.0000] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|triad_R_late_minus_R_joint|stage_bins | 阶段分箱 | ge13: +0.000 [-0.001, +0.002] (n=36); 0_2: +0.001 [-0.001, +0.003] (n=14); NH: +0.002 [-0.000, +0.005] (n=9); 2_13: -0.002 [-0.006, +0.003] (n=5) |
| CS_SINGLE|tg_D_E|age+HA | age_months | +0.0000 [-0.0002, +0.0002] (n=64)  |
| CS_SINGLE|tg_D_E|HA:age+duration | duration_months | -0.0000 [-0.0003, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_D_E|stage_bins | 阶段分箱 | ge13: +0.502 [+0.491, +0.512] (n=36); 0_2: +0.506 [+0.491, +0.521] (n=14); NH: +0.528 [+0.505, +0.550] (n=9); 2_13: +0.502 [+0.473, +0.530] (n=5) |
| CS_SINGLE|tg_D_L|age+HA | age_months | +0.0000 [-0.0001, +0.0002] (n=64)  |
| CS_SINGLE|tg_D_L|HA:age+duration | duration_months | -0.0000 [-0.0004, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_D_L|stage_bins | 阶段分箱 | ge13: +0.515 [+0.506, +0.524] (n=36); 0_2: +0.504 [+0.489, +0.519] (n=14); NH: +0.507 [+0.487, +0.528] (n=9); 2_13: +0.538 [+0.432, +0.645] (n=5) |
| CS_SINGLE|tg_G_EL|age+HA | age_months | -0.0001 [-0.0002, +0.0000] (n=64)  |
| CS_SINGLE|tg_G_EL|HA:age+duration | duration_months | +0.0001 [-0.0001, +0.0004] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_G_EL|stage_bins | 阶段分箱 | ge13: +0.497 [+0.490, +0.504] (n=36); 0_2: +0.504 [+0.489, +0.520] (n=14); NH: +0.484 [+0.462, +0.505] (n=9); 2_13: +0.501 [+0.370, +0.631] (n=5) |
| CS_SINGLE|tg_G_LE|age+HA | age_months | -0.0002 [-0.0004, +0.0000] (n=64)  |
| CS_SINGLE|tg_G_LE|HA:age+duration | duration_months | -0.0002 [-0.0004, +0.0001] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_G_LE|stage_bins | 阶段分箱 | ge13: +0.492 [+0.481, +0.503] (n=36); 0_2: +0.494 [+0.478, +0.510] (n=14); NH: +0.478 [+0.450, +0.507] (n=9); 2_13: +0.519 [+0.450, +0.588] (n=5) |
| CS_SINGLE|tg_D_E_minus_G_EL|age+HA | age_months | +0.0001 [-0.0001, +0.0003] (n=64)  |
| CS_SINGLE|tg_D_E_minus_G_EL|HA:age+duration | duration_months | -0.0001 [-0.0005, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_D_E_minus_G_EL|stage_bins | 阶段分箱 | ge13: +0.005 [-0.007, +0.016] (n=36); 0_2: +0.001 [-0.021, +0.024] (n=14); NH: +0.044 [+0.008, +0.081] (n=9); 2_13: +0.001 [-0.065, +0.066] (n=5) |
| CS_SINGLE|tg_D_L_minus_G_LE|age+HA | age_months | +0.0002 [+0.0000, +0.0005] (n=64)  |
| CS_SINGLE|tg_D_L_minus_G_LE|HA:age+duration | duration_months | +0.0001 [-0.0003, +0.0005] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| CS_SINGLE|tg_D_L_minus_G_LE|stage_bins | 阶段分箱 | ge13: +0.023 [+0.010, +0.036] (n=36); 0_2: +0.010 [-0.013, +0.033] (n=14); NH: +0.029 [-0.012, +0.070] (n=9); 2_13: +0.020 [-0.051, +0.090] (n=5) |
| raw|raw_auc_early|age+HA | age_months | -0.0000 [-0.0002, +0.0002] (n=64)  |
| raw|raw_auc_early|HA:age+duration | duration_months | -0.0001 [-0.0004, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| raw|raw_auc_early|stage_bins | 阶段分箱 | ge13: +0.495 [+0.483, +0.507] (n=36); 0_2: +0.503 [+0.491, +0.515] (n=14); NH: +0.525 [+0.506, +0.545] (n=9); 2_13: +0.506 [+0.444, +0.569] (n=5) |
| raw|raw_auc_late|age+HA | age_months | -0.0001 [-0.0002, +0.0001] (n=64)  |
| raw|raw_auc_late|HA:age+duration | duration_months | +0.0000 [-0.0003, +0.0003] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| raw|raw_auc_late|stage_bins | 阶段分箱 | ge13: +0.507 [+0.498, +0.515] (n=36); 0_2: +0.505 [+0.494, +0.516] (n=14); NH: +0.510 [+0.495, +0.525] (n=9); 2_13: +0.505 [+0.444, +0.566] (n=5) |
| raw|prestim_mean_auc|age+HA | age_months | -0.0000 [-0.0001, +0.0001] (n=64)  |
| raw|prestim_mean_auc|HA:age+duration | duration_months | +0.0000 [-0.0002, +0.0002] (n=55) two identifiable comparisons: age at fixed duration, duration at fixed age |
| raw|prestim_mean_auc|stage_bins | 阶段分箱 | ge13: +0.498 [+0.493, +0.503] (n=36); 0_2: +0.501 [+0.488, +0.514] (n=14); NH: +0.499 [+0.486, +0.511] (n=9); 2_13: +0.484 [+0.457, +0.510] (n=5) |

## 5. 与既往轮次的关系（披露）

核 CS 轮报告的私有类别任务约为 0，也未见功能或发育关联。本轮的私有设计与之同型，见预登记 §0。
