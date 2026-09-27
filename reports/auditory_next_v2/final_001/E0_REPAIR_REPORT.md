E0_R：实现 `NUMERICAL_FAILURE`；支持 `DESCRIPTIVE_ONLY`；对照 `FAILED`；科学状态 `NOT_EVALUABLE`。固定来源 `E0R_core_001`；执行状态 `INCOMPLETE_PRIMARY_MATRIX`。

这是预定同日配对中的native128、记录内独立块目标任务可读性维护。全套有块支持记录的MLP族都数值稳定后才允许整族聚合，不能挑成功记录。旧linear精确复用，不计为新fit。纯音与bapa分别报告J及CE；混合MFF不是全CI群体。即使目标任务可读，也不证明跨儿童、跨任务迁移或临床效度；E1保持关闭。

训练时按记录内filter block/class加权；最终测试CE沿用旧classification_metrics的记录内candidate/class平衡，再按完整配对记录汇总，不声称最终评分按block等权。E0不设本轮其他路线的0.01 bits推进阈值，J及区间只作描述。

记录流：请求=未提供；具备块支持=未提供。linear整族可聚合记录=未提供/整族未通过；MLP32整族可聚合记录=未提供/整族未通过；任务J只用完整配对，其每任务记录数与配对组数见效应和风险表，不代表全部有块支持记录的均值。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | FAILED | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| same_requested_native128_records_complete_family | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| E1_transfer | 未提供 | 未提供 | 未提供 | NOT_APPLICABLE | 未提供 | 未提供 | 未提供 | E0R_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |