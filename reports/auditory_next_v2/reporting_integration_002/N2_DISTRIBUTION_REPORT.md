N2：实现 `NUMERICAL_FAILURE`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `N2_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主对象固定 R_SIM/P_bal/logistic、k=8同一袋上的HMU−HMUVAR，量级0.01 bits/bag；需要超过重复均值列、pre与H_BAG解释。10次测试重组不重新拟合，必须先按候选平均后评价方向。k=4/8/16共同支持审计只说明支持；未运行的k曲线不得作图或宣称已完成。pre与post窗长度不同，二者差异不是纯因果响应。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| post_gain_mu_var | logistic | -0.0014935038347629 | -0.0030173067911442 | -0.0002579784684654 | 57.0 | bits/bag | NEGATIVE_SCREEN |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| prespecified_synthetic_execution_coverage | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_mv_vs_dup | COMPLETE | -0.000828735991338 | -0.0017620540304157 | 0.0001031153272239 | N2_core_001 |
| pre_gain_mu_var | COMPLETE | 0.0009098707435204 | -0.000192159062132 | 0.0021043825935774 | N2_core_001 |
| post_minus_pre_gain_mu_var_post_minus_pre | COMPLETE | -0.0024033745782834 | -0.0048201105577513 | -0.0006369280766953 | N2_core_001 |
| ten_frozen_test_regroupings | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| regrouping_average_post_gain_mu_var | COMPLETE | -0.0005423520268466 | -0.0012754500941366 | 0.0002696078337295 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | COMPLETE | -0.0007018547620667 | -0.0012637186230403 | -0.0001684802534161 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | COMPLETE | 0.0001980273794837 | -0.0006700764805348 | 0.0012713640031106 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | COMPLETE | 0.0003318463390711 | -0.0005460152322084 | 0.0014053793057686 | N2_core_001 |
| regrouping_average_post_gain_mu_var | COMPLETE | -0.0015236912218686 | -0.0031559840655442 | -0.0001977305286167 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | COMPLETE | -0.0009215024675311 | -0.0019632072946629 | 8.140796169223956e-05 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | COMPLETE | 0.0002111274306447 | -0.0005299652825255 | 0.0008989215655122 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | COMPLETE | 0.0003473490596605 | -0.0003338576645715 | 0.0010259126528834 | N2_core_001 |
| fixed_prediction_metrics_and_influence | MISSING | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |