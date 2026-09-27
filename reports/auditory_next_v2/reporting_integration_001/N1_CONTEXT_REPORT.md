N1：实现 `NOT_RUN`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `N1_core_001`；执行状态 `STARTED_NO_COMPLETION`。

主量为 R_SIM/P_nat/MLP32/temperature 的 HP−HPB，背景增益需达到0.005 bits/trial且区间下界>0；还需 HB−HPB>0并超过PP和噪声扩维对照。raw、自然先验与平衡先验分列。donor冻结时不使用当前标签；固定头替换及匹配训练donor对照保留同支持参考，其变化可能反映输入分布失配，不能直接解释为背景的因果必要性。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| prespecified_synthetic_execution_coverage | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| complete_required_head_families | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| declared_inner_OOF_calibration | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| two_fixed_head_donor_assignments | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| matched_donor_training_same_support_reference | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| HPP_minus_HPB | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| HPBnoise_minus_HPB | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| HB_minus_HPB | MISSING | 未提供 | 未提供 | 未提供 | N1_core_001 |
| fixed_prediction_metrics_and_influence | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |