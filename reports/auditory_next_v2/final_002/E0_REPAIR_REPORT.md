E0_R：实现 `NUMERICAL_FAILURE`；支持 `DESCRIPTIVE_ONLY`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `E0R_core_001`；执行状态 `INCOMPLETE_PRIMARY_MATRIX`。

这是预定同日配对中的native128、记录内独立块目标任务可读性维护。全套有块支持记录的MLP族都数值稳定后才允许整族聚合，不能挑成功记录。旧linear精确复用，不计为新fit。纯音与bapa分别报告J及CE；混合MFF不是全CI群体。即使目标任务可读，也不证明跨儿童、跨任务迁移或临床效度；E1保持关闭。

训练时按记录内filter block/class加权；最终测试CE沿用旧classification_metrics的记录内candidate/class平衡，再按完整配对记录汇总，不声称最终评分按block等权。E0不设本轮其他路线的0.01 bits推进阈值，J及区间只作描述。

记录流：请求18，有块支持16；旧linear完整16记录，任务汇总只用7个完整配对。新MLP每记录所有64个规定头均稳定的记录数为0，整族门限允许进入主聚合的记录数为0。头部稳定765/1024，未解决259；0聚合许可不是阴性效应。

保留旧E0_native_003的完整linear结果（零重拟合，不替代新MLP主矩阵；estimate为J bits/trial）：

| task | calibration | complete_pairs | ce_bits | estimate | ci_lower | ci_upper |
| --- | --- | --- | --- | --- | --- | --- |
| puretone | calibrated | 7 | 1.0019366427088854 | -0.001936642708885304 | -0.008220011745785969 | 0.0036278042055953546 |
| bapa | calibrated | 7 | 1.011900031438339 | -0.011900031438338954 | -0.017373607378354826 | -0.006668964215837625 |
| puretone | raw | 7 | 1.0320832902419492 | -0.032083290241949225 | -0.05814053307844621 | -0.010196371149396104 |
| bapa | raw | 7 | 1.0495364140987717 | -0.04953641409877193 | -0.060823615002854006 | -0.03859482311645262 |

任务J只用完整配对，不代表全部有块支持记录的均值；旧linear、单条记录数值完成及全族科学可评价保持分开。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| same_requested_native128_records_complete_family | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| E1_transfer | 未提供 | 未提供 | 未提供 | NOT_APPLICABLE | 未提供 | 未提供 | 未提供 | E0R_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |