N1：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `FAILED`；科学状态 `NOT_EVALUABLE`。固定来源 `N1_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主量为 R_SIM/P_nat/MLP32/temperature 的 HP−HPB，背景增益需达到0.005 bits/trial且区间下界>0；还需 HB−HPB>0并超过PP和噪声扩维对照。raw、自然先验与平衡先验分列。donor冻结时不使用当前标签；固定头替换及匹配训练donor对照保留同支持参考，其变化可能反映输入分布失配，不能直接解释为背景的因果必要性。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HP_minus_HPB | mlp32 | -0.0249566826589322 | -0.027988789208733 | -0.0221691542158125 | 59.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| prespecified_synthetic_execution_coverage | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| complete_required_head_families | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| declared_inner_OOF_calibration | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| two_fixed_head_donor_assignments | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| matched_donor_training_same_support_reference | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| fixed_head_donor:same_child_B-actual_B | COMPLETE | 0.0030460265981769 | 0.0003866922786802 | 0.0056752592411666 | N1_core_001 |
| fixed_head_donor:training_child_B-actual_B | COMPLETE | -0.002205871766235 | -0.0060475978099179 | 0.0012624272082767 | N1_core_001 |
| matched_training_donor_vs_same_support_reference:HPB_donor_support_reference-HPB_training_child_donor | COMPLETE | -0.0062084418450781 | -0.0126918063498331 | -0.0012426184504645 | N1_core_001 |
| HPP_minus_HPB | COMPLETE | -0.0119874380903146 | -0.0145278597463982 | -0.0094226354263356 | N1_core_001 |
| HPBnoise_minus_HPB | COMPLETE | 0.004886121246093 | -0.0011759657678446 | 0.0099085427205381 | N1_core_001 |
| HB_minus_HPB | COMPLETE | -0.0241528137667634 | -0.027591464758276 | -0.020944091986163 | N1_core_001 |
| fixed_prediction_metrics_and_influence | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |