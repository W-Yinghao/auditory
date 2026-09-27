N3：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `FAILED`；科学状态 `NOT_EVALUABLE`。固定来源 `N3_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主结果使用每个视图的训练OOF选族，禁止事后替换为某固定族。H基线风险与H→HP、HB→HBP、H→Hnoise并列；0.005 bits/trial主增量还须在H+pre以外成立。负增益表示当前有限读出下预测风险上升，可能包含扩维代价和OOF选择不同模型族的容量差异；噪声扩维也受损时尤其不能写成“EEG负信息”或“脑内无信息”。历史稀疏/结构空格只描述，不能补造两类支持。

保存的训练OOF选族（折数，不是人数）：

| mode | population | view | family | n_outer_folds |
| --- | --- | --- | --- | --- |
| L0 | P_bal | H | logistic | 5 |
| L0 | P_bal | HB | logistic | 5 |
| L0 | P_bal | HBP | logistic | 5 |
| L0 | P_bal | HP | logistic | 5 |
| L0 | P_bal | Hnoise | logistic | 5 |
| L0 | P_nat | H | logistic | 5 |
| L0 | P_nat | HB | logistic | 5 |
| L0 | P_nat | HBP | logistic | 5 |
| L0 | P_nat | HP | logistic | 5 |
| L0 | P_nat | Hnoise | logistic | 5 |
| R_SIM | P_bal | H | mlp32 | 5 |
| R_SIM | P_bal | HB | logistic | 5 |
| R_SIM | P_bal | HBP | logistic | 5 |
| R_SIM | P_bal | HP | logistic | 5 |
| R_SIM | P_bal | Hnoise | logistic | 5 |
| R_SIM | P_nat | H | mlp32 | 5 |
| R_SIM | P_nat | HB | logistic | 5 |
| R_SIM | P_nat | HBP | logistic | 5 |
| R_SIM | P_nat | HP | logistic | 5 |
| R_SIM | P_nat | Hnoise | logistic | 5 |

H与增强视图若选中不同模型族，主风险差同时包含选族/容量变化；固定族结果保留作诊断，不能事后替代主比较。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| selected_H_minus_HP | training_OOF_selected | -0.0506316587586698 | -0.0577564657244072 | -0.0411938981089999 | 60.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| prespecified_synthetic_execution_coverage | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| saved_training_OOF_family_selection | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| complete_required_head_families | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| declared_inner_OOF_calibration | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| selected_HB_minus_HBP | COMPLETE | 0.0001004002383222 | -0.0019035027100663 | 0.0021865901184356 | N3_core_001 |
| selected_H_minus_Hnoise | COMPLETE | -0.0519103031575786 | -0.0589538202026109 | -0.042284318799605 | N3_core_001 |
| fixed_history_strata_description | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| stratum_two_class_support_counts | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |
| fixed_prediction_metrics_and_influence | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |