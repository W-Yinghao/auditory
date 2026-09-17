> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 五条思路第一轮筛查报告

执行状态：**S4_RECORDED_WITH_FAILURES**；表征状态：**S3_COMPLETE**（90/90）。

本文件是 S4 聚合记录。报告已生成、作业提交、合成契约通过和科学实验完成是不同状态。任何路线失败或未完成均保留；没有宣称五路线全部科学完成。

主表征固定为 R_SIM，R_SUP 为平行分析，L0 与随机表示为基线。不同路线的效应单位不同，不构造跨路线总分。

| 路线 | 主终点 | verdict | 控制 | 样本支持 | 科学完成 |
|---|---|---|---|---|---|
| A | post_T | NEED_CONTROLS | PENDING | SUPPORT_INSUFFICIENT_FOR_HISTORY_POSITION_CONTROL | False |
| B | calibrated_main_gain | NEGATIVE_SCREEN | COMPLETE | SEE_EFFECT_AND_CONTROLS | True |
| C | T_C_mlp32_calibrated | IMPLEMENTATION_FAIL | FAIL | SEE_EFFECT_AND_CONTROLS | False |
| D | D2_minus_D3 | NEGATIVE_SCREEN | COMPLETE | SEE_EFFECT_AND_CONTROLS | True |
| E | E1_transfer_gap_not_estimated | IMPLEMENTATION_FAIL | FAIL | SUPPORT_INSUFFICIENT_FOR_E1 | False |

所有区间直接继承各来源的候选等权、固定 OOF 2000 次 cluster bootstrap；不是 pipeline-refit 区间。负 J / 负增益原样保留。

## 路线 A

判定：**NEED_CONTROLS**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | post_T | 0.0184137 [-0.0231942, 0.0599399] | 55 | cosine_difference | A_L0_core_001 |
| R_SUP | post_T | 0.0418133 [-0.00163692, 0.0889623] | 55 | cosine_difference | A_SUP_RAND_core_001 |
| R_RAND | post_T | 0.023167 [-0.0122139, 0.062219] | 55 | cosine_difference | A_SUP_RAND_core_001 |
| R_SIM | post_T | 0.01335 [-0.0270006, 0.0535584] | 55 | cosine_difference | A_SIM_core_001 |

现象与 estimand：刺激差值表征的同候选跨时间块匹配是否超过异候选匹配。

基线解释：背景、刺激前、随机投影、配对时序与训练内白化可解释重复性。

剩余替代解释：共享滤波历史、序列位置及一般个体状态仍需重置/平衡敏感性约束。

与旧工作区别：终点是固定表征的候选级重复性，不复用旧波形相关作为临床证据。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：A_controls_L0_SUP_RAND_001:L0:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:L0:continuous_balanced；A_controls_L0_SUP_RAND_001:L0:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:L0:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:L0:reset_balanced；A_controls_L0_SUP_RAND_001:L0:reset_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_balanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_balanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_balanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_balanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_unbalanced_on_balanced；A_controls_SIM_001:R_SIM:continuous_balance_minus_unbalanced；A_controls_SIM_001:R_SIM:continuous_balanced；A_controls_SIM_001:R_SIM:continuous_unbalanced_on_balanced；A_controls_SIM_001:R_SIM:reset_balance_minus_unbalanced；A_controls_SIM_001:R_SIM:reset_balanced；A_controls_SIM_001:R_SIM:reset_unbalanced_on_balanced；A:frozen_history_position_balance_support

失败保留：无记录到的实现失败

来源：A_L0_core_001、A_SUP_RAND_core_001、A_SIM_core_001、A_controls_L0_SUP_RAND_001、A_controls_SIM_001

固定六格历史×位置平衡支持：55 候选中，满足所有 24 个 half/class/cell 固定配额的候选为 0。
该序列支持限制不是代码失败，不调小配额补成阳性。字面码 2 的 H0 单元几乎结构为空；各半份/位置单元的零计数见 history_position_support.csv。有效的独立 reset 项仍单独保留。


## 路线 B

判定：**NEGATIVE_SCREEN**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | calibrated_main_gain | -0.00167271 [-0.00260096, -0.000745914] | 60 | bits/trial | B_L0_001 |
| R_SUP | calibrated_main_gain | -0.00133677 [-0.00228316, -0.000411545] | 60 | bits/trial | B_SUP_RAND_core_001 |
| R_RAND | calibrated_main_gain | -0.00151634 [-0.00254784, -0.000462401] | 60 | bits/trial | B_SUP_RAND_core_001 |
| R_SIM | calibrated_main_gain | -0.00216897 [-0.00308903, -0.00122239] | 60 | bits/trial | B_SIM_core_001 |

现象与 estimand：在当前及前一个字面码均为 1 时，历史 run-length 对当前反应是否仍有条件预测增量。

基线解释：强 gap/position 上下文、刺激前和前次反应均使用同试次对照。

剩余替代解释：残余历史、适应、质量和序列混杂不能解释为因果信息传递。

与旧工作区别：估计固定 OOF 条件 CE 增益，不以已有负结果重新选择历史或窗口。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：无记录到的实现失败

来源：B_L0_001、B_SUP_RAND_core_001、B_SIM_core_001、B_controls_L0_SUP_001、B_controls_SIM_001


## 路线 C

判定：**IMPLEMENTATION_FAIL**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | T_C_linear_calibrated | -0.000196746 [-0.000922888, 0.000208532] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| L0 | T_C_linear_raw | -9.78564e-05 [-0.00136014, 0.00066845] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_RAND | T_C_linear_calibrated | 9.349e-05 [-0.000605844, 0.000602018] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_RAND | T_C_linear_raw | -0.000473747 [-0.00147779, 0.000307219] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_SUP | T_C_linear_calibrated | -0.00805367 [-0.0113482, -0.00605344] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_SUP | T_C_linear_raw | -0.00933457 [-0.0129051, -0.00741267] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_SIM | T_C_linear_calibrated | -0.000160824 [-0.000814803, 0.000418705] | 60 | bits/trial | C_linear_SIM_001 |
| R_SIM | T_C_linear_raw | -0.000226436 [-0.00109012, 0.00055669] | 60 | bits/trial | C_linear_SIM_001 |

现象与 estimand：独立预处理及编码的左右分支联合读出是否优于任一单分支。

基线解释：LL/RR、扩展单分支容量及温度校准约束模型容量解释。

剩余替代解释：固定头置零与替换是分布外诊断；预测互补性不等于 PID synergy。

与旧工作区别：左右原始输入隔离，不能从全头表示事后切片宣称独立视角。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：C_L0_003；C_SIM_full_001；C_SUP_full_001

来源：C_L0_003、C_SIM_full_001、C_SUP_full_001、C_linear_L0_SUP_RAND_002、C_linear_SIM_001


## 路线 D

判定：**NEGATIVE_SCREEN**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | D2_minus_D3 | -0.32886 [-0.590976, -0.0991506] | 51 | MUSS_source_points | D_L0_core_001 |
| R_SUP | D2_minus_D3 | 0 [0, 0] | 51 | MUSS_source_points | D_SUP_core_001 |
| R_SIM | D2_minus_D3 | 0.10873 [-0.142199, 0.387963] | 51 | MUSS_source_points | D_SIM_core_001 |

现象与 estimand：刺激固定线性头的 null 空间是否在临床协变量及 visible 之外降低 MUSS 源分 MAE。

基线解释：临床单独、完整特征、刺激前、随机投影与试次数/QC 敏感性保持原终点。

剩余替代解释：固定头不变性只说明该头几何；新 null 读出可能恢复刺激信息。

与旧工作区别：outer 和 inner encoder 均独立拟合；不以旧临床阴性结果后的新终点替换主 MAE。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：无记录到的实现失败

来源：D_L0_core_001、D_SUP_core_001、D_SIM_core_001、D_controls_L0_SUP_001、D_controls_SIM_001


## 路线 E

判定：**IMPLEMENTATION_FAIL**。主表征：E1:puretone_to_bapa。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| E0_native | linear_calibrated_J_puretone | -0.00193664 [-0.00822001, 0.0036278] | 7 | bits/trial | E0_native_003 |
| E0_native | linear_calibrated_J_bapa | -0.0119 [-0.0173736, -0.00666896] | 7 | bits/trial | E0_native_003 |

现象与 estimand：E0 描述记录内独立时间块的任务可读性；E1 才检验纯音到 bapa 迁移。

基线解释：E0 的 linear 与 MLP32 分族核对完整记录，失败族不在成功子集聚合。

剩余替代解释：任务、布局及来源设备差异仍可能解释迁移；E0 不估计迁移信息瓶颈。

与旧工作区别：MFF 包含混合及未知来源，不能整体称 CI；现有 E1 bapa 16 候选不足 20。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：E0_native_003

来源：E0_native_003

E0 请求记录 18；具有块支持 16；两族均成功记录 11。
族状态：{"linear": "COMPLETE", "MLP32": "NUMERICAL_FAILURE"}；数值失败 record-head 数：5。


## 共享刺激读出

以下数字来自显式 execution run 的已汇总 OOF 表；这里没有重新拟合或重新 bootstrap。略高的 bAcc 不保证正的 J=1−CE_bits；过度自信的错误可以使 J 为负。

| mode | bAcc | AUROC | calibrated CE bits | J bits [95% CI] | n candidates |
|---|---:|---:|---:|---|---:|
| L0 | 0.524629 | 0.532557 | 0.998802 | 0.00119766 [-0.000512568, 0.00286262] | 58 |
| R_RAND | 0.52521 | 0.534162 | 0.997509 | 0.0024906 [0.000920278, 0.00412265] | 58 |
| R_SUP | 0.522603 | 0.533992 | 1.00755 | -0.00754936 [-0.0122902, -0.00271314] | 58 |
| R_SIM | 0.523572 | 0.529396 | 0.998261 | 0.00173867 [0.00014868, 0.00337019] | 58 |

## 已看数据和范围限制

Phase 0–3 与已完成 A/B/D 阴性或弱结果均保留。原有 53 候选及当前开发队列不是未经查看的独立验证集。HA 数字码不自动命名标准/偏差音；设备开关、精确声学起点、临床量表与 EEG 同期性仍有未知。元数据 addendum 的少量设备史线索不等同于精确 EEG 状态。

MFF 是混合及未知来源，不能把全部记录称为 CI。E1 bapa 安全候选 16 < 20；E0 记录内时间块分析不替代儿童外推迁移。任何数值失败的族不以仅成功记录的聚合替代。

所有失败与取消尝试保留，未覆盖原结果。源版本由 source YAML 明确指定，未搜索最好或最高版本。逐候选误差、预测和临床记录继续留在原 private 产物；本聚合器不发布或复算个人明细。

历史尝试：C_L0_001 (CANCELLED_BEFORE_OUTCOMES)；C_L0_002 (NUMERICAL_FAILURE)；C_linear_L0_SUP_RAND_001 (AGGREGATION_IMPLEMENTATION_FAILURE_REPAIRED)

精确输入与代码 SHA256 见 source_hashes.csv；路径与异常详情仅写 private 审计。补充控制估计见 control_metrics.csv；所有任务/分支/窗口刺激读出见 stimulus_decoding.csv。metrics_aggregate.csv 按方案 §16.2 列出主终点标记；来源指标未提供的记录数、试次数、覆盖比例留空，不能由人数推造。
