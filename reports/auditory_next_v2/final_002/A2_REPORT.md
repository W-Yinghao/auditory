A2：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `A2_core_001`；执行状态 `A2_CORE_RECORDED`。

共同 Ω、配额和候选集合由完整事件链、QC 与块支持冻结；所有候选使用同一 Ω/q，20 次固定无放回抽样先平均再做候选 bootstrap。主表示始终 R_SIM，R_SUP 是次要平行证据。post-minus-pre 是匹配统计量之差，不将不同宽度的 L0 向量补零相减。共同响应不能简单视为纯伪迹；残差重复性也可能由共享预测项及交叉内积产生，四项代数恒等式与合成反例单列。输出恢复只复用已保存的20次ridge，无新头/PCA/scaler拟合。

冻结 Ω=["run3_5_pos0", "run3_5_pos1"]；共同候选数=49。未入 Ω 的上下文不参与主估计，不由次要结果补回。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| post_delta_cosine | matching | 0.0153892995528579 | -0.0305961865681659 | 0.0593237586491848 | 49.0 | cosine_difference | MIXED |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | A2_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_delta_cosine | common_Omega_equal_candidate | matching | 未提供 | COMPLETE | 0.0153892995528579 | -0.0305961865681659 | 0.0593237586491848 | A2_core_001 |
| pre_delta_cosine | common_Omega_equal_candidate | matching | 未提供 | COMPLETE | 0.0106349769832528 | -0.0242502542988572 | 0.0463774679976754 | A2_core_001 |
| post_minus_pre_cosine | common_Omega_equal_candidate | matching | 未提供 | COMPLETE | 0.0047543225696051 | -0.0481146300298942 | 0.0561656422406773 | A2_core_001 |
| common_response_cosine | common_Omega_equal_candidate | matching | 未提供 | COMPLETE | 0.3697216313782003 | 0.3015292795180646 | 0.4351233174513417 | A2_core_001 |
| saved_residual_four_term_audit | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | A2_residual_recovered_001 |
| fixed_quality_summary_in_background | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | A2_residual_recovered_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |