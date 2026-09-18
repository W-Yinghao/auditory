> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../../PUBLICATION.md).

# 保守停止策略下的 PTA 修正与扩展探索：完整结果

本轮按预先列出的任务完成分析，没有根据显著性、置信区间是否跨零、效应大小或表征排名提前停止。所有结果均为已被反复研究的档案数据上的探索证据，不是独立临床验证。这里保留小的正向结果，也列出改变解释的控制实验。

## 本轮完成了什么

- HA：57 个候选身份，每人一个最早合格记录，5 个固定特征库、5 个任务、13 个模型方案，5 次重复的 5 折外层／3 折内层验证；65 个任务×模型结果全部保留。
- 在相同的两个主要任务上，补齐技术质量、振幅、完整质量和有限高斯核非线性检验。
- 旧 Phase 3：原 50 人、原划分，先复现旧预测，再修正 PTA；所有原任务及单独惩罚敏感性完成。
- 旧 auditory5 D：原 51 人、原划分、原训练范围的缓存表征，L0／监督／自监督三种模式，各 27 个模型全部完成。
- 试次数可靠性：同一批 43 个身份，32／64／128／256 试次、两种分半、五个特征库，40 行结果全部完成。
- CI／MFF：203 个 canonical 记录的来源和测量描述；另完成身份核验后的混合 MFF 档案分数回归，四终点、七个模型方案全部保留。
- 最终独立聚合验证、来源绑定核验、拟合记账、隐私权限与图表生成。最终验证没有重新训练模型。

## 数据、目标与验证方法

A 表示档案 IT-MAIS/MAIS 列；V 表示 MUSS 列；V_given_A 表示已知 A 时预测 V。A/V 的量表版本、EEG 与评估的同期性仍未全部确证，不能写作已确证的同期功能量。HA 使用原表分值，混合 MFF 的 0–40 原始值保留原单位，未擅自乘以 2.5。CAP、SIR 是原始有序分数的探索性误差比较，不产生诊断阈值。

HA 纳入以来源、身份、必要字段和至少每个字面事件码两次可用试次为基础；未沿用早期每条件 40／总数 64／队列 30 的科学推进门槛。五种特征为 HJORTH(60)、POST(320)、CONTRAST(160)、PRE(160)、SPATIAL(210)，每记录最多均匀取 256 个按时间排序的接受 epoch。1/2 未被擅自命名为标准／偏差音；CONTRAST 只是 code2−code1。

标准化、缺失值插补与指示变量、临床线性／二次基、惩罚和联合特征库选择均在训练内部完成。候选身份不跨训练和验证。EEG 联合模型包括退回临床基线的选择；外层最佳特征库不重新充当主要模型。质量控制与非线性补充是在看到首轮结果之后明确追加的探索分析。

表中 gain = 基线 MAE − 加入信息后 MAE，正值代表改善。区间来自 2,000 次候选身份 bootstrap：先对同一人的五次外层误差取平均，再抽取身份。它是固定 OOF 预测的 95% 区间，不包含整条训练流程重抽样的不确定性，也未对多任务／多表征比较作确证性校正。五次重复不是五倍人数。leave-one-out 是从固定误差中删去一个身份的敏感性，不是重训 LOOCV。

## PTA 历史错误与修正边界

旧脚本把非空记录的顺序号作为临床 ID，而注册表的 C 编号指向实际工作表行。57 行中，较好耳未助听 PTA 有 55 行改变，助听 PTA 有 47 行改变。实际源行号码改变 57 行；本次以数值比较修正了 pta_007 汇总中把字符串格式差异算作变更的问题，007 的 PTA 数值表经重新逐表校验一致。

未助听完整数 54→55；助听完整数 45→44。旧 D 支持 51→52，其中增加 3、失去 2。复现旧划分完全一致；仅修正支持后重新运行原平衡算法，会有 37/60 个外层组改变。

本轮旧模型的配对修正保留原队列和原划分，不把旧缓存投影用于新划分。新的 52 人 D 队列及新的 encoder 划分尚未整套训练；这与本轮已经完成的 51 人配对修正是不同实验。不能宣称所有下游旧结论已修复，也不能仅因反事实划分改变就宣称旧划分存在身份泄漏。历史原文件保留。

## HA：每个预定任务与特征库均保留

| task | comparison | gain | interval | positive_repeats | leave_one_out |
| --- | --- | --- | --- | --- | --- |
| A | increment_HJORTH | 0.141 | [-0.213, 0.500] | 4/5 | [0.059, 0.233] |
| A | increment_POST | -0.177 | [-0.502, 0.122] | 2/5 | [-0.232, -0.097] |
| A | increment_CONTRAST | -0.097 | [-0.344, 0.131] | 1/5 | [-0.143, -0.052] |
| A | increment_PRE | -0.165 | [-0.367, -0.006] | 1/5 | [-0.193, -0.096] |
| A | increment_SPATIAL | -0.138 | [-0.320, 0.019] | 1/5 | [-0.163, -0.094] |
| A | joint_selector | -0.152 | [-0.547, 0.218] | 1/5 | [-0.232, -0.048] |
| A | quality_adjusted | -0.392 | [-0.691, -0.103] | 0/5 | [-0.450, -0.307] |
| A | content_control | -0.191 | [-0.566, 0.111] | 2/5 | [-0.242, -0.074] |
| A | EEG_alone | -1.470 | [-2.477, -0.521] | 1/5 | [-1.627, -1.256] |
| A | clinical_nonlinearity | 1.396 | [0.510, 2.353] | 5/5 | [1.158, 1.502] |
| V | increment_HJORTH | -0.020 | [-0.051, 0.010] | 1/5 | [-0.027, -0.014] |
| V | increment_POST | 0.000 | [0.000, 0.000] | 0/5 | [0.000, 0.000] |
| V | increment_CONTRAST | 0.004 | [-0.092, 0.108] | 2/5 | [-0.024, 0.023] |
| V | increment_PRE | -0.468 | [-0.858, -0.092] | 1/5 | [-0.511, -0.389] |
| V | increment_SPATIAL | 0.003 | [-0.089, 0.087] | 2/5 | [-0.016, 0.028] |
| V | joint_selector | -0.555 | [-0.937, -0.190] | 0/5 | [-0.602, -0.475] |
| V | quality_adjusted | -0.332 | [-0.984, 0.232] | 1/5 | [-0.429, -0.110] |
| V | content_control | -0.278 | [-0.722, 0.136] | 3/5 | [-0.336, -0.173] |
| V | EEG_alone | -2.801 | [-4.341, -1.395] | 0/5 | [-3.015, -2.529] |
| V | clinical_nonlinearity | 0.893 | [-0.255, 2.040] | 5/5 | [0.681, 1.163] |
| V_given_A | increment_HJORTH | 0.054 | [-0.055, 0.172] | 3/5 | [0.037, 0.073] |
| V_given_A | increment_POST | 0.111 | [0.009, 0.241] | 2/5 | [0.072, 0.125] |
| V_given_A | increment_CONTRAST | 0.098 | [-0.012, 0.227] | 3/5 | [0.062, 0.111] |
| V_given_A | increment_PRE | 0.018 | [-0.273, 0.299] | 3/5 | [-0.059, 0.076] |
| V_given_A | increment_SPATIAL | 0.152 | [0.007, 0.320] | 1/5 | [0.107, 0.183] |
| V_given_A | joint_selector | 0.289 | [0.010, 0.583] | 3/5 | [0.232, 0.352] |
| V_given_A | quality_adjusted | -0.190 | [-0.576, 0.161] | 1/5 | [-0.262, -0.073] |
| V_given_A | content_control | 0.376 | [0.009, 0.750] | 4/5 | [0.287, 0.452] |
| V_given_A | EEG_alone | -2.801 | [-4.341, -1.395] | 0/5 | [-3.015, -2.529] |
| V_given_A | clinical_nonlinearity | 0.778 | [-0.070, 1.682] | 5/5 | [0.652, 1.002] |
| CAP | increment_HJORTH | -0.018 | [-0.033, -0.004] | 1/5 | [-0.020, -0.013] |
| CAP | increment_POST | -0.018 | [-0.039, -0.000] | 1/5 | [-0.021, -0.013] |
| CAP | increment_CONTRAST | -0.018 | [-0.034, 0.002] | 0/5 | [-0.024, -0.015] |
| CAP | increment_PRE | 0.005 | [-0.032, 0.043] | 4/5 | [-0.004, 0.014] |
| CAP | increment_SPATIAL | 0.001 | [-0.013, 0.016] | 3/5 | [-0.004, 0.004] |
| CAP | joint_selector | -0.011 | [-0.049, 0.026] | 1/5 | [-0.020, -0.002] |
| CAP | quality_adjusted | -0.025 | [-0.059, 0.009] | 0/5 | [-0.031, -0.018] |
| CAP | content_control | 0.019 | [-0.015, 0.055] | 4/5 | [0.011, 0.028] |
| CAP | EEG_alone | -0.141 | [-0.261, -0.028] | 0/5 | [-0.161, -0.122] |
| CAP | clinical_nonlinearity | 0.085 | [-0.046, 0.207] | 5/5 | [0.061, 0.122] |
| SIR | increment_HJORTH | -0.008 | [-0.014, -0.003] | 0/5 | [-0.009, -0.007] |
| SIR | increment_POST | -0.015 | [-0.026, -0.005] | 0/5 | [-0.016, -0.011] |
| SIR | increment_CONTRAST | -0.012 | [-0.025, 0.001] | 1/5 | [-0.013, -0.008] |
| SIR | increment_PRE | -0.005 | [-0.012, 0.000] | 0/5 | [-0.006, -0.003] |
| SIR | increment_SPATIAL | -0.011 | [-0.026, -0.000] | 0/5 | [-0.012, -0.005] |
| SIR | joint_selector | -0.025 | [-0.041, -0.009] | 0/5 | [-0.027, -0.021] |
| SIR | quality_adjusted | -0.015 | [-0.036, 0.008] | 2/5 | [-0.019, -0.010] |
| SIR | content_control | -0.026 | [-0.045, -0.008] | 0/5 | [-0.028, -0.021] |
| SIR | EEG_alone | -0.066 | [-0.147, 0.006] | 2/5 | [-0.076, -0.052] |
| SIR | clinical_nonlinearity | 0.045 | [-0.010, 0.105] | 5/5 | [0.027, 0.053] |

主要值得保留的线索是 V_given_A 的联合选择增益约 +0.289 分，固定 OOF 区间约 [0.010, 0.583]，3/5 次重复正向；去掉任何单个身份后，固定误差平均增益仍为正。相较训练内打乱 EEG 的对照也呈正向。它说明当前数据存在一个条件关联线索，不证明听觉与言语功能已被成功分离，更不证明临床效用。

A 的 Hjorth 单库改善约 +0.141 分，区间跨零，4/5 次重复正向；联合选择并未改善。该小效应没有被门槛删去，但事后挑出最好的库不能替代联合选择的泛化结果。临床二次基相对线性基的改善需要单列，避免将欠拟合临床基线造成的差距误归因于 EEG。

### 绝对预测误差

| task | model | n | MAE | RMSE | R2 |
| --- | --- | --- | --- | --- | --- |
| A | MEAN | 57 | 14.239 | 17.115 | -0.035 |
| A | C_LINEAR | 57 | 5.135 | 7.471 | 0.803 |
| A | C_BEST | 57 | 3.739 | 5.757 | 0.883 |
| A | C_Q | 57 | 3.761 | 5.695 | 0.885 |
| A | C_HJORTH | 57 | 3.598 | 5.322 | 0.900 |
| A | C_POST | 57 | 3.916 | 6.588 | 0.847 |
| A | C_CONTRAST | 57 | 3.836 | 5.799 | 0.881 |
| A | C_PRE | 57 | 3.904 | 6.051 | 0.871 |
| A | C_SPATIAL | 57 | 3.876 | 5.930 | 0.876 |
| A | BEST_CZ | 57 | 3.891 | 5.748 | 0.883 |
| A | BEST_CQZ | 57 | 4.153 | 6.417 | 0.855 |
| A | BEST_SHUFFLED | 57 | 3.700 | 5.469 | 0.894 |
| A | Z_ONLY | 57 | 15.710 | 19.404 | -0.330 |
| V | MEAN | 57 | 18.100 | 21.405 | -0.023 |
| V | C_LINEAR | 57 | 7.582 | 10.733 | 0.743 |
| V | C_BEST | 57 | 6.689 | 9.935 | 0.780 |
| V | C_Q | 57 | 6.411 | 9.459 | 0.800 |
| V | C_HJORTH | 57 | 6.709 | 9.987 | 0.777 |
| V | C_POST | 57 | 6.689 | 9.935 | 0.780 |
| V | C_CONTRAST | 57 | 6.686 | 9.928 | 0.780 |
| V | C_PRE | 57 | 7.157 | 10.776 | 0.741 |
| V | C_SPATIAL | 57 | 6.686 | 9.935 | 0.780 |
| V | BEST_CZ | 57 | 7.244 | 10.884 | 0.735 |
| V | BEST_CQZ | 57 | 6.743 | 9.922 | 0.780 |
| V | BEST_SHUFFLED | 57 | 6.966 | 10.361 | 0.760 |
| V | Z_ONLY | 57 | 20.902 | 25.016 | -0.398 |
| V_given_A | MEAN | 57 | 18.100 | 21.405 | -0.023 |
| V_given_A | C_LINEAR | 57 | 6.943 | 9.481 | 0.799 |
| V_given_A | C_BEST | 57 | 6.165 | 8.971 | 0.820 |
| V_given_A | C_Q | 57 | 5.684 | 8.274 | 0.847 |
| V_given_A | C_HJORTH | 57 | 6.111 | 8.937 | 0.822 |
| V_given_A | C_POST | 57 | 6.054 | 8.843 | 0.825 |
| V_given_A | C_CONTRAST | 57 | 6.067 | 8.836 | 0.826 |
| V_given_A | C_PRE | 57 | 6.147 | 9.275 | 0.808 |
| V_given_A | C_SPATIAL | 57 | 6.013 | 8.832 | 0.826 |
| V_given_A | BEST_CZ | 57 | 5.876 | 8.998 | 0.819 |
| V_given_A | BEST_CQZ | 57 | 5.875 | 8.719 | 0.830 |
| V_given_A | BEST_SHUFFLED | 57 | 6.252 | 8.948 | 0.821 |
| V_given_A | Z_ONLY | 57 | 20.902 | 25.016 | -0.398 |
| CAP | MEAN | 57 | 1.546 | 1.841 | -0.028 |
| CAP | C_LINEAR | 57 | 0.575 | 0.751 | 0.829 |
| CAP | C_BEST | 57 | 0.490 | 0.747 | 0.831 |
| CAP | C_Q | 57 | 0.467 | 0.719 | 0.843 |
| CAP | C_HJORTH | 57 | 0.508 | 0.766 | 0.822 |
| CAP | C_POST | 57 | 0.509 | 0.765 | 0.822 |
| CAP | C_CONTRAST | 57 | 0.508 | 0.742 | 0.833 |
| CAP | C_PRE | 57 | 0.485 | 0.717 | 0.844 |
| CAP | C_SPATIAL | 57 | 0.490 | 0.753 | 0.828 |
| CAP | BEST_CZ | 57 | 0.501 | 0.733 | 0.837 |
| CAP | BEST_CQZ | 57 | 0.492 | 0.729 | 0.839 |
| CAP | BEST_SHUFFLED | 57 | 0.521 | 0.768 | 0.821 |
| CAP | Z_ONLY | 57 | 1.687 | 2.007 | -0.222 |
| SIR | MEAN | 57 | 0.861 | 1.022 | -0.025 |
| SIR | C_LINEAR | 57 | 0.456 | 0.590 | 0.658 |
| SIR | C_BEST | 57 | 0.411 | 0.529 | 0.725 |
| SIR | C_Q | 57 | 0.455 | 0.590 | 0.658 |
| SIR | C_HJORTH | 57 | 0.420 | 0.536 | 0.718 |
| SIR | C_POST | 57 | 0.426 | 0.554 | 0.699 |
| SIR | C_CONTRAST | 57 | 0.423 | 0.549 | 0.704 |
| SIR | C_PRE | 57 | 0.417 | 0.541 | 0.713 |
| SIR | C_SPATIAL | 57 | 0.423 | 0.547 | 0.706 |
| SIR | BEST_CZ | 57 | 0.436 | 0.562 | 0.689 |
| SIR | BEST_CQZ | 57 | 0.469 | 0.614 | 0.629 |
| SIR | BEST_SHUFFLED | 57 | 0.410 | 0.532 | 0.722 |
| SIR | Z_ONLY | 57 | 0.928 | 1.128 | -0.250 |

### 天花板与预定分层

| target | n | minimum | median | maximum | unique_values | ceiling_count | floor_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 57 | 40.000 | 97.500 | 100.000 | 17 | 28 | 0 |
| V | 57 | 17.500 | 87.500 | 100.000 | 21 | 18 | 0 |
| CAP | 57 | 2.000 | 7.000 | 9.000 | 8 | 17 | 0 |
| SIR | 57 | 1.000 | 4.000 | 5.000 | 5 | 17 | 2 |

| task | stratum | n | MAE | gain_vs_clinical |
| --- | --- | --- | --- | --- |
| A | age_le_36 | 4 | 6.933 | 0.324 |
| A | age_gt_36 | 53 | 3.661 | -0.188 |
| A | duration_le_6 | 18 | 6.100 | 0.497 |
| A | duration_gt_6 | 39 | 2.872 | -0.452 |
| A | ceiling | 28 | 2.284 | -0.429 |
| A | non_ceiling | 29 | 5.443 | 0.115 |
| V | age_le_36 | 4 | 23.474 | -1.411 |
| V | age_gt_36 | 53 | 6.019 | -0.491 |
| V | duration_le_6 | 18 | 11.391 | -1.008 |
| V | duration_gt_6 | 39 | 5.330 | -0.346 |
| V | ceiling | 18 | 3.465 | 0.198 |
| V | non_ceiling | 39 | 8.989 | -0.903 |
| V_given_A | age_le_36 | 4 | 20.315 | 0.076 |
| V_given_A | age_gt_36 | 53 | 4.786 | 0.305 |
| V_given_A | duration_le_6 | 18 | 8.872 | 0.036 |
| V_given_A | duration_gt_6 | 39 | 4.493 | 0.406 |
| V_given_A | ceiling | 18 | 2.665 | 0.371 |
| V_given_A | non_ceiling | 39 | 7.358 | 0.251 |
| CAP | age_le_36 | 4 | 1.240 | 0.152 |
| CAP | age_gt_36 | 53 | 0.446 | -0.023 |
| CAP | duration_le_6 | 18 | 0.473 | 0.020 |
| CAP | duration_gt_6 | 39 | 0.514 | -0.025 |
| CAP | ceiling | 17 | 0.352 | -0.020 |
| CAP | non_ceiling | 40 | 0.565 | -0.007 |
| SIR | age_le_36 | 4 | 0.816 | -0.040 |
| SIR | age_gt_36 | 53 | 0.407 | -0.024 |
| SIR | duration_le_6 | 18 | 0.506 | -0.029 |
| SIR | duration_gt_6 | 39 | 0.404 | -0.023 |
| SIR | ceiling | 17 | 0.394 | -0.033 |
| SIR | non_ceiling | 40 | 0.454 | -0.021 |

分层共享全队列训练模型，没有在小亚组内重新调参，也没有选择最有利年龄／时长切点。它们只帮助理解误差来自哪里。A 有 28/57、V 有 18/57 位于字面最大值；CAP/SIR 各 17/57。误差降低的空间并不均匀，不能只报告总体相关系数。

## 条件关联是否受技术因素或非线性影响

| task | comparison | gain | interval | positive_repeats | leave_one_out |
| --- | --- | --- | --- | --- | --- |
| A | technical_adjusted | -0.355 | [-0.815, 0.024] | 1/5 | [-0.436, -0.184] |
| A | amplitude_adjusted | -0.245 | [-0.599, 0.068] | 1/5 | [-0.317, -0.143] |
| A | full_quality | -0.392 | [-0.691, -0.103] | 0/5 | [-0.450, -0.307] |
| A | kernel_vs_clinical | 0.071 | [-0.251, 0.381] | 2/5 | [0.007, 0.166] |
| A | kernel_vs_linear_EEG | 0.224 | [-0.019, 0.498] | 3/5 | [0.157, 0.254] |
| A | technical_vs_clinical | -0.016 | [-0.361, 0.324] | 1/5 | [-0.103, 0.075] |
| A | amplitude_vs_clinical | 0.037 | [-0.181, 0.269] | 2/5 | [-0.028, 0.104] |
| V_given_A | technical_adjusted | -0.591 | [-1.170, -0.108] | 0/5 | [-0.666, -0.424] |
| V_given_A | amplitude_adjusted | -0.165 | [-0.584, 0.242] | 3/5 | [-0.218, -0.047] |
| V_given_A | full_quality | -0.190 | [-0.576, 0.161] | 1/5 | [-0.262, -0.073] |
| V_given_A | kernel_vs_clinical | -0.064 | [-0.363, 0.220] | 1/5 | [-0.116, -0.019] |
| V_given_A | kernel_vs_linear_EEG | -0.354 | [-0.654, -0.043] | 0/5 | [-0.445, -0.311] |
| V_given_A | technical_vs_clinical | 0.572 | [-0.087, 1.263] | 5/5 | [0.402, 0.687] |
| V_given_A | amplitude_vs_clinical | 0.148 | [-0.091, 0.449] | 3/5 | [0.057, 0.194] |

V_given_A 的技术摘要基线相对临床基线改善约 +0.572 分，5/5 次重复为正，但区间跨零。在技术摘要基线上继续加入 EEG 的增益为约 −0.591 分，5 次重复均不改善。仅控制振幅后也没有保持原来的正向点估计，区间仍宽。因此原线索的脆弱性不能仅解释为“振幅调整把生理信号去掉了”。技术摘要可关联配合度、数据可用性、采集过程和真实个体差异；这里不能从预测结果判定因果解释。

有限高斯核 EEG 在 A 上有小的正向点估计，在 V_given_A 上没有改善。它只覆盖一个明确定义的非线性替代，不等于排除所有非线性，更不构成深度模型一定无效的证据。本轮没有因为原线性结果弱而跳过它。

## 测量可靠性：比较同一批身份

| bank | odd_even_32 | odd_even_256 | early_late_32 | early_late_256 |
| --- | --- | --- | --- | --- |
| CONTRAST | 0.074 | 0.062 | 0.086 | -0.039 |
| HJORTH | 0.894 | 0.984 | 0.819 | 0.899 |
| POST | 0.136 | 0.515 | 0.156 | 0.369 |
| PRE | -0.025 | 0.134 | -0.022 | 0.095 |
| SPATIAL | 0.824 | 0.972 | 0.779 | 0.909 |

完整 40 行见 `results/auditory_repair/reliability_matched_001/reliability_matched.csv`。这里的 r 是同一特征在两个半段之间、跨 43 个候选身份的相关，再对特征取中位数；不是单个儿童的可靠性置信区间。奇偶与前后半分开报告，Spearman–Brown 仅作启发性描述。

Hjorth 和空间统计保留较稳定的个体差异；刺激后波形随试次数增加而改善；字面条件差值仍弱。稳定性也可能包含稳定的头部／电极／噪声差异，不能由高 r 直接认定为听觉功能标志物。这个结果支持继续研究可重复的记录表征，以及为什么平均响应与条件差值的误差不同。试次数曲线是回顾性子采样，没有证明缩短实际采集时长具有相同效果。

## 旧 Phase 3：原样复现后修正

| target | model | n | MAE | RMSE |
| --- | --- | --- | --- | --- |
| MUSS | original_clinical | 50 | 7.048 | 10.178 |
| MUSS | corrected_clinical | 50 | 6.693 | 9.990 |
| MUSS | original_clinical_plus_fixed_amplitude | 50 | 7.366 | 10.518 |
| MUSS | corrected_clinical_plus_fixed_amplitude | 50 | 6.959 | 10.298 |
| MUSS | original_clinical_plus_poststim_pattern | 50 | 13.579 | 18.728 |
| MUSS | corrected_clinical_plus_poststim_pattern | 50 | 13.233 | 18.148 |
| MUSS | original_clinical_plus_prestim_pattern | 50 | 11.529 | 15.205 |
| MUSS | corrected_clinical_plus_prestim_pattern | 50 | 11.738 | 15.629 |
| MUSS | corrected_post_separate | 50 | 6.705 | 10.001 |
| MUSS | corrected_pre_separate | 50 | 7.059 | 10.364 |
| MUSS | age_duration_only | 50 | 6.842 | 9.847 |
| age | original_clinical | 50 | 28.843 | 37.273 |
| age | corrected_clinical | 50 | 28.622 | 37.381 |
| age | original_clinical_plus_fixed_amplitude | 50 | 29.428 | 38.151 |
| age | corrected_clinical_plus_fixed_amplitude | 50 | 29.531 | 38.497 |
| age | original_clinical_plus_poststim_pattern | 50 | 28.739 | 37.592 |
| age | corrected_clinical_plus_poststim_pattern | 50 | 28.860 | 37.617 |
| age | original_clinical_plus_prestim_pattern | 50 | 29.512 | 37.812 |
| age | corrected_clinical_plus_prestim_pattern | 50 | 29.423 | 38.105 |
| log_duration | original_clinical | 50 | 1.429 | 1.637 |
| log_duration | corrected_clinical | 50 | 1.437 | 1.647 |
| log_duration | original_clinical_plus_fixed_amplitude | 50 | 1.455 | 1.662 |
| log_duration | corrected_clinical_plus_fixed_amplitude | 50 | 1.464 | 1.673 |
| log_duration | original_clinical_plus_poststim_pattern | 50 | 1.507 | 1.704 |
| log_duration | corrected_clinical_plus_poststim_pattern | 50 | 1.508 | 1.703 |
| log_duration | original_clinical_plus_prestim_pattern | 50 | 1.498 | 1.699 |
| log_duration | corrected_clinical_plus_prestim_pattern | 50 | 1.495 | 1.690 |

| task | comparison | gain | interval | positive_repeats | leave_one_out |
| --- | --- | --- | --- | --- | --- |
| MUSS | original_clinical | -0.355 | [-0.839, 0.129] | 0/5 | [-0.450, -0.287] |
| MUSS | original_clinical_plus_fixed_amplitude | -0.673 | [-1.282, -0.063] | 0/5 | [-0.795, -0.571] |
| MUSS | corrected_clinical_plus_fixed_amplitude | -0.266 | [-0.687, 0.063] | 0/5 | [-0.330, -0.114] |
| MUSS | original_clinical_plus_poststim_pattern | -6.886 | [-9.919, -4.181] | 0/5 | [-7.263, -5.999] |
| MUSS | corrected_clinical_plus_poststim_pattern | -6.540 | [-9.548, -3.863] | 0/5 | [-6.914, -5.676] |
| MUSS | original_clinical_plus_prestim_pattern | -4.836 | [-6.968, -2.594] | 0/5 | [-5.129, -4.424] |
| MUSS | corrected_clinical_plus_prestim_pattern | -5.045 | [-7.098, -2.885] | 0/5 | [-5.327, -4.655] |
| MUSS | corrected_post_separate | -0.012 | [-0.038, 0.005] | 0/5 | [-0.014, -0.000] |
| MUSS | corrected_pre_separate | -0.366 | [-0.749, -0.013] | 0/5 | [-0.411, -0.253] |
| MUSS | age_duration_only | -0.149 | [-0.515, 0.229] | 1/5 | [-0.239, -0.099] |
| age | original_clinical | -0.221 | [-0.959, 0.546] | 2/5 | [-0.393, -0.099] |
| age | original_clinical_plus_fixed_amplitude | -0.806 | [-1.944, 0.233] | 1/5 | [-0.997, -0.508] |
| age | corrected_clinical_plus_fixed_amplitude | -0.909 | [-1.951, 0.080] | 0/5 | [-1.088, -0.599] |
| age | original_clinical_plus_poststim_pattern | -0.117 | [-4.062, 3.750] | 2/5 | [-0.827, 0.573] |
| age | corrected_clinical_plus_poststim_pattern | -0.238 | [-4.153, 3.553] | 1/5 | [-0.919, 0.447] |
| age | original_clinical_plus_prestim_pattern | -0.890 | [-4.214, 2.453] | 0/5 | [-1.522, -0.285] |
| age | corrected_clinical_plus_prestim_pattern | -0.801 | [-4.714, 3.053] | 1/5 | [-1.490, -0.105] |
| log_duration | original_clinical | 0.008 | [-0.056, 0.069] | 3/5 | [-0.001, 0.017] |
| log_duration | original_clinical_plus_fixed_amplitude | -0.018 | [-0.079, 0.041] | 2/5 | [-0.027, -0.009] |
| log_duration | corrected_clinical_plus_fixed_amplitude | -0.027 | [-0.052, -0.001] | 1/5 | [-0.034, -0.023] |
| log_duration | original_clinical_plus_poststim_pattern | -0.070 | [-0.194, 0.055] | 0/5 | [-0.098, -0.051] |
| log_duration | corrected_clinical_plus_poststim_pattern | -0.071 | [-0.194, 0.055] | 0/5 | [-0.098, -0.052] |
| log_duration | original_clinical_plus_prestim_pattern | -0.061 | [-0.176, 0.050] | 2/5 | [-0.086, -0.048] |
| log_duration | corrected_clinical_plus_prestim_pattern | -0.058 | [-0.175, 0.063] | 2/5 | [-0.084, -0.045] |

12 个旧目标×模型预测组合已先复现。MUSS 临床 MAE 由旧 PTA 的约 7.048 变为约 6.693；修正后共享惩罚的高维刺激后模型明显较差，单独惩罚后约 6.705，与临床基线非常接近。这区分了正则化失配和缺乏稳定增量，不能只引用旧共享惩罚模型的坏结果作为 EEG 无效依据。

## 旧 auditory5 D：三种表征及随机方向完整保留

| representation | contrast | gain | interval |
| --- | --- | --- | --- |
| L0 | C_vs_CV | -0.041 | [-0.417, 0.284] |
| L0 | CV_vs_CVN | -0.226 | [-0.437, -0.036] |
| L0 | C_vs_CVN | -0.268 | [-0.698, 0.124] |
| L0 | C_vs_FULL | -0.034 | [-0.141, 0.064] |
| L0 | C_vs_PRE | 0.000 | [0.000, 0.000] |
| R_SUP | C_vs_CV | 0.275 | [-0.117, 0.666] |
| R_SUP | CV_vs_CVN | 0.081 | [-0.162, 0.314] |
| R_SUP | C_vs_CVN | 0.356 | [-0.126, 0.849] |
| R_SUP | C_vs_FULL | -0.054 | [-0.510, 0.411] |
| R_SUP | C_vs_PRE | 0.060 | [-0.167, 0.297] |
| R_SIM | C_vs_CV | 0.163 | [-0.407, 0.781] |
| R_SIM | CV_vs_CVN | -0.027 | [-0.199, 0.132] |
| R_SIM | C_vs_CVN | 0.136 | [-0.436, 0.777] |
| R_SIM | C_vs_FULL | -0.036 | [-0.563, 0.458] |
| R_SIM | C_vs_PRE | -0.312 | [-0.935, 0.299] |

监督表征 C→CVN 的正向点估计约 +0.356，区间跨零；自监督约 +0.136，区间也宽；L0 为负。三种模式各 20 个随机方向控制均已完成，正向个数分别为 1/20、16/20、14/20，说明不能把监督表征中的正向点估计直接解释为功能方向特异性。所有 27 模型绝对误差、随机方向、区间和影响范围见 `results/auditory_repair/legacy_d_002/aggregate.json`。

旧 51 人队列保留两条修正后 PTA 缺失记录，插补仅使用相应训练折；没有借用其他儿童的行或删除不利记录。旧缓存回放三模式各 1,377 行通过，最大绝对差不超过 4.3e−14。

## CI 与混合 MFF：已有内容继续利用，来源仍分开

203 个 canonical MFF 记录中有 20 个字面 CI、18 个 CIHA、3 个 HA、1 个 NH、161 个未明确来源。临床同日设备历史线索加入后，扩展 CI 证据范围为 41 条记录。源标签是证据线索，不是已经确证的诊断或设备开关状态，也不是 41 个独立儿童。

扩展 CI 范围内，已有 primary 的 devt−stad 主窗／晚窗成对记录各 39 条，中位数约 −0.678／−0.345 µV；strict 下各 10 条，约 −0.287／−0.520 µV。它们是记录内描述，不能命名为已确证的 MMN 或康复获益。该范围内有数值临床链接且可测 stad 的记录每终点仅两条，仍给出数值分布，没有因为少而隐去；无法据此训练或验证独立 CI 临床模型。

### 混合来源档案回归

准备版本 `ci_prepare_004` 已核对原始表头、出生／日期字段、身份冲突和可解释时间来源。保存的完整 10 个 sheet 表头没有可数值提取的植入／开机／验配／使用时长专用列；通用自由文本设备线索不足以补出有定义的时长。71 个候选身份中，66 个可用唯一 DOB 和实际 EEG 时间派生年龄，另 5 个保留缺失。一个 DOB 矛盾身份被暂缓纳入。每个候选身份选最早唯一链接且有 canonical EEG 时间的记录，选择先于终点和特征可用性；这不宣称覆盖所有未链接的更早记录。各终点冲突值保留为无效，不取均值或挑最有利值。来源、范式、技术元数据作为基线；可信且可用的年龄／时长才纳入。完整 preparation 摘要是结果的一部分。

| task | n | finite_age | sources |
| --- | --- | --- | --- |
| A | 38 | 38 | {"unknown": 37, "CI": 1} |
| V | 38 | 38 | {"unknown": 37, "CI": 1} |
| CAP | 36 | 36 | {"unknown": 35, "CI": 1} |
| SIR | 36 | 36 | {"unknown": 35, "CI": 1} |

| task | model | n | MAE | RMSE |
| --- | --- | --- | --- | --- |
| A | MEAN | 38 | 7.850 | 10.343 |
| A | SOURCE_TECH | 38 | 7.376 | 9.895 |
| A | SOURCE_TECH_Z | 38 | 7.401 | 9.910 |
| A | SOURCE_TECH_SHUFFLE | 38 | 7.531 | 10.025 |
| A | ALL_Q | 38 | 7.924 | 10.856 |
| A | ALL_Q_Z | 38 | 7.955 | 10.864 |
| A | Z_ONLY | 38 | 7.868 | 10.343 |
| V | MEAN | 38 | 11.891 | 13.676 |
| V | SOURCE_TECH | 38 | 10.506 | 12.495 |
| V | SOURCE_TECH_Z | 38 | 10.554 | 12.542 |
| V | SOURCE_TECH_SHUFFLE | 38 | 10.565 | 12.628 |
| V | ALL_Q | 38 | 11.216 | 13.298 |
| V | ALL_Q_Z | 38 | 11.313 | 13.410 |
| V | Z_ONLY | 38 | 11.970 | 13.738 |
| CAP | MEAN | 36 | 1.635 | 2.157 |
| CAP | SOURCE_TECH | 36 | 1.675 | 2.117 |
| CAP | SOURCE_TECH_Z | 36 | 1.695 | 2.134 |
| CAP | SOURCE_TECH_SHUFFLE | 36 | 1.731 | 2.156 |
| CAP | ALL_Q | 36 | 1.693 | 2.168 |
| CAP | ALL_Q_Z | 36 | 1.741 | 2.221 |
| CAP | Z_ONLY | 36 | 1.640 | 2.161 |
| SIR | MEAN | 36 | 1.256 | 1.466 |
| SIR | SOURCE_TECH | 36 | 1.242 | 1.466 |
| SIR | SOURCE_TECH_Z | 36 | 1.248 | 1.470 |
| SIR | SOURCE_TECH_SHUFFLE | 36 | 1.258 | 1.485 |
| SIR | ALL_Q | 36 | 1.240 | 1.484 |
| SIR | ALL_Q_Z | 36 | 1.252 | 1.495 |
| SIR | Z_ONLY | 36 | 1.276 | 1.479 |

| task | comparison | gain | interval | positive_repeats | leave_one_out |
| --- | --- | --- | --- | --- | --- |
| A | source_technical_increment | -0.026 | [-0.074, 0.005] | 0/5 | [-0.029, -0.007] |
| A | content | 0.129 | [-0.061, 0.354] | 2/5 | [0.060, 0.163] |
| A | full_quality_increment | -0.031 | [-0.069, -0.001] | 1/5 | [-0.034, -0.021] |
| A | EEG_alone | -0.018 | [-0.059, 0.018] | 0/5 | [-0.027, -0.006] |
| V | source_technical_increment | -0.048 | [-0.118, 0.003] | 0/5 | [-0.054, -0.019] |
| V | content | 0.011 | [-0.322, 0.441] | 2/5 | [-0.137, 0.062] |
| V | full_quality_increment | -0.097 | [-0.188, -0.026] | 0/5 | [-0.106, -0.066] |
| V | EEG_alone | -0.079 | [-0.168, -0.025] | 0/5 | [-0.083, -0.042] |
| CAP | source_technical_increment | -0.020 | [-0.042, -0.004] | 1/5 | [-0.022, -0.011] |
| CAP | content | 0.036 | [0.006, 0.068] | 4/5 | [0.029, 0.043] |
| CAP | full_quality_increment | -0.048 | [-0.081, -0.018] | 0/5 | [-0.052, -0.039] |
| CAP | EEG_alone | -0.005 | [-0.009, -0.001] | 0/5 | [-0.005, -0.003] |
| SIR | source_technical_increment | -0.005 | [-0.014, 0.001] | 0/5 | [-0.006, -0.002] |
| SIR | content | 0.011 | [-0.013, 0.033] | 2/5 | [0.007, 0.019] |
| SIR | full_quality_increment | -0.012 | [-0.022, -0.003] | 0/5 | [-0.013, -0.010] |
| SIR | EEG_alone | -0.020 | [-0.042, -0.001] | 0/5 | [-0.022, -0.011] |

混合回归所有目标都有可用年龄；每个终点只有 1 个字面 CI，其他都是未知来源。A/V 的增量分别约 −0.026／−0.048 原分，CAP/SIR 约 −0.020／−0.005。CAP 的真实 EEG 相比打乱对照改善约 +0.036，但仍差于不含 EEG 的基线；不能将“优于打乱”偷换为“具有基线之外的价值”。小的正向内容差异和原始误差都完整保留。

以上是混合 MFF 的档案关联，不是 CI-only，也不是已经调整所有重要临床混杂因素的效用结论。来源及缺失指示有控制不等于解决未知字段；小来源亚组不能承受独立来源外推结论。固定 stad 三值统计包含主窗、晚窗及其差，后者与前两者线性相关，岭惩罚下保留这一预定表达，不把它解释成第三个独立生理维度。

## 小样本任务配对和重复采集也保留描述

原始 F3 是纯音与 bapa 两任务的临床信息互补，F4 是已知基线功能后预测未来功能。既有资格核验发现 9 对同候选同日且都有 stad 测量的任务配对，其中 2 对有一致的档案量表值；HA 有 15 对候选重复采集、涉及 13 个身份；MFF 的多日期档案涉及 2 个身份、8 个身份×终点序列，其中 7 个数值不变、1 个变化。

本轮另对现有配对测量作零拟合描述，完整结果见 `results/auditory_repair/pairs_003/`。9 对的主窗／晚窗跨任务 Pearson r 约为 0.604／0.836；bapa−纯音的差值中位数约为 +0.126／−0.631 µV。HA 的 15 对中 10 对有两次可比固定幅度，后次减前次的中位数约 +0.368 µV；全部 15 对的 vendor 采集间隔中位数约 5.217 月。没有把缺失的 5 对删掉后报告成 15 对完整测量，也没有将这些记录对当作独立人数。

两任务刺激和测量的含义不必相同，相关或差值不是临床互补证据；重复 EEG 的时间顺序也不补出功能量表的真实随访日期。较高的跨任务幅度相关提示共享个体差异值得继续研究，但也可能包括稳定非神经因素。保留这些小规模描述的原因是它们有数据价值；不强行训练临床模型的原因是临床对象尚未成立，并非未达到人为的高效应阈值。

## 对原始科研目的的判断

| 科研目的 | 目前能支持的部分 | 仍不能宣称的部分 |
| --- | --- | --- |
| F1 听觉功能相关表征 | 57 身份的基线、全部固定库、质量和非线性对照；A 上小的 Hjorth／核方法线索 | 稳定且可临床推广的独立 EEG 增量 |
| F2 听觉与言语功能的条件关系 | 已知 A 时预测 V 的小正向关联及控制实验，明确脆弱性 | 两种临床功能已被机制性分离，或模型可替代量表 |
| F3 跨任务临床互补 | 9 对同日任务测量的来源与描述性比较；其中 2 对有一致档案量表 | 用非配对人数充样本、将跨任务相关直接解释为临床互补 |
| F4 基线之外的随访预测 | HA 重复采集及 MFF 多日期档案的支持／变化描述 | 把未确证问卷日期的档案序列称为真实功能随访，或由设备月数构造康复轨迹 |
| CI／跨设备研究 | 明确 CI／CIHA／历史线索／未知来源，CI 波形描述与混合来源回归 | 将未知来源当作 CI、用极少临床交集验证 CI 模型或推断设备获益 |
| 记录表征与测量研究 | 同一身份集合的可靠性曲线、临床天花板、技术摘要与表征增量比较 | 可靠性自动等同临床有效性，或离线子采样等同前瞻缩短采集 |

尚未进行的是新支持／新划分下的整套 encoder 重训、整流程重抽样验证、独立队列复现，以及需确证临床时间／设备／量表版本的临床问题。本轮完成的是以上明确列出的有限实验集合，不是声称穷尽所有模型。后续若扩展，应围绕可重复的测量和条件关联的替代解释提出新的有限假设，不能通过无限增加架构／种子将探索结果伪装为确证结果。停止依据不使用“增益必须很大／区间必须排除零”的门槛。

## 执行、验证与资源

最终核验重算 138 个模型指标行、104 个效应行，检查持久化 OOF 完整性、原划分、来源快照与输入哈希，未重新拟合。所有生产、测试、探测、统计和绘图均走 CPU Slurm；GPU 使用为零，也未使用 P100。

本轮累计 298,686 次 head 调用尝试（包含均值头、测试和历史回放，不等于独立模型或独立统计检验）。上限为 300,000；这是运行保护，不是科学推进阈值。legacy_D 首次完成后因记账修补而不必要地重跑了一遍，两遍都计费，并将首遍遗漏的 405 次回放计入；首个核测试遗漏的 3 次求解也补计。后续汇总修复均采用零重训方式。

已登记 43 个 Slurm 任务，按完整申请时限及保守 CPU 数计算的预留上界为 23.80 core-hours。调度记账历史不可用，未将该上界说成实际 CPU 消耗。失败／被替代版本均保留，资源和失败原因见 `docs/auditory_repair/JOBS.json`。

原始数据只读。候选身份、姓名、日期、原路径、逐人预测和拟合参数均留在 private 目录；本报告只包含聚合结果。没有自动推送 GitHub。

图表：`figures/ha_primary_controls.pdf`、`ha_mechanism.pdf`、`matched_reliability.pdf`、`legacy_D_repaired.pdf`、`mixed_mff.pdf`，每图另有 PNG。详细机器可读证据见同版本 `results/auditory_repair/verification_001/`；若验证需更正，将创建新版本并在 STATUS 中指向最终成功版本。
