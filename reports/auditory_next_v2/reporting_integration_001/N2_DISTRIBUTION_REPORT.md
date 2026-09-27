N2：实现 `NOT_RUN`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `N2_core_001`；执行状态 `STARTED_NO_COMPLETION`。

主对象固定 R_SIM/P_bal/logistic、k=8同一袋上的HMU−HMUVAR，量级0.01 bits/bag；需要超过重复均值列、pre与H_BAG解释。10次测试重组不重新拟合，必须先按候选平均后评价方向。k=4/8/16共同支持审计只说明支持；未运行的k曲线不得作图或宣称已完成。pre与post窗长度不同，二者差异不是纯因果响应。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | MISSING | 未提供 | 未提供 | 未提供 | N2_core_001 |
| prespecified_synthetic_execution_coverage | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_mv_vs_dup | MISSING | 未提供 | 未提供 | 未提供 | N2_core_001 |
| pre_gain_mu_var | MISSING | 未提供 | 未提供 | 未提供 | N2_core_001 |
| post_minus_pre_gain_mu_var_post_minus_pre | MISSING | 未提供 | 未提供 | 未提供 | N2_core_001 |
| ten_frozen_test_regroupings | MISSING | 未提供 | 未提供 | 未提供 | N2_core_001 |
| fixed_prediction_metrics_and_influence | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |