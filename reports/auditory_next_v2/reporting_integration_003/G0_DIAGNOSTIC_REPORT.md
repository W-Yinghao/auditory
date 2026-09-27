G0：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `G0_readouts_001`；执行状态 `G0_READOUTS_COMPLETE`。

共享旧表的重新拟合 logistic probe 与原 R_SUP CNN head 分开报告；原头的 TRAIN_DIAGNOSTIC 分数仅说明优化，不是外层泛化。G0_metadata_002 替代早期时间角色/桥接支持，不替代已复算旧指标。同儿童的后块预测和共享外儿童预测具有不同训练对象，不能只按准确率大小宣称迁移成功。因果/offline 桥接使用共同 QC 试次，仍是处理敏感性。微弱 bAcc/AUC 不保证 CE 优于先验，J 的负值保留。

旧共享表复算最大误差=2.22045e-16。原within_receipts中的n_calibration存在记录元数据错误，本报告不使用它；实际训练样本数应以原生fit start的n或时间角色核对，不能用校准参数字典长度。温度记录数是应用到各头的次数，不是独立校准参数数。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| prespecified_synthetic_execution_coverage | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| legacy_shared_table_reproduction | COMPLETE | 未提供 | 未提供 | 未提供 | G0_001 |
| refined_dependency_and_common_QC_mapping | COMPLETE | 未提供 | 未提供 | 未提供 | G0_metadata_002 |
| within_child_and_offline_bridge | COMPLETE | 未提供 | 未提供 | 未提供 | G0_readouts_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 | P_bal | 未提供 | logistic | ce_bits | 0.9952196366634588 | 0.9909592694747992 | 0.9989714635381874 | 未提供 | 57.0 |
| L0 | P_bal | 未提供 | logistic | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| L0 | P_bal | 未提供 | logistic | ce_bits | 0.9948250546548084 | 0.990337496038527 | 0.9987706838436736 | 未提供 | 57.0 |
| L0 | P_bal | 未提供 | logistic | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| L0 | P_bal | 未提供 | logistic | ce_bits | 0.9952196366634588 | 0.9909592694747992 | 0.9989714635381874 | 未提供 | 57.0 |
| L0 | P_bal | 未提供 | logistic | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | ce_bits | 0.9933677832436918 | 0.9898579214901584 | 0.9966239766830792 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | ce_bits | 0.9937373597829592 | 0.9896461572798216 | 0.9975851756156195 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | ce_bits | 0.9933677832436918 | 0.9898579214901584 | 0.9966239766830792 | 未提供 | 57.0 |
| R_RAND | P_bal | 未提供 | logistic | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | ce_bits | 0.9993870654747872 | 0.9966365257015692 | 1.0019406508562396 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | bacc | 0.5104487741256549 | 0.4990794738495093 | 0.5223295884139254 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | ce_bits | 1.0000828789526737 | 0.9958137426011316 | 1.0035987079512874 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | bacc | 0.5157157888620847 | 0.5033872549768809 | 0.5285903163351398 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | ce_bits | 0.999384107153054 | 0.996634146571726 | 1.0019384808270682 | 未提供 | 57.0 |
| R_SIM | P_bal | 未提供 | logistic | bacc | 0.5157157888620847 | 0.5033872549768809 | 0.5285903163351398 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | ce_bits | 0.996238453595228 | 0.9907054333641958 | 1.0011132727854408 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | ce_bits | 0.9979643519233168 | 0.9915614255753672 | 1.0035670782023218 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | ce_bits | 0.996238453595228 | 0.9907054333641958 | 1.0011132727854408 | 未提供 | 57.0 |
| R_SUP | P_bal | 未提供 | logistic | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| causal | P_bal | 未提供 | logistic | ce_bits | 0.9977619417771236 | 0.9959351621992564 | 0.999445428927846 | 未提供 | 59.0 |
| causal | P_bal | 未提供 | logistic | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| causal | P_bal | 未提供 | logistic | ce_bits | 0.9978213678165444 | 0.9963718962844792 | 0.999161441057451 | 未提供 | 59.0 |
| causal | P_bal | 未提供 | logistic | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| causal | P_bal | 未提供 | logistic | ce_bits | 0.9977619417771236 | 0.9959351621992564 | 0.999445428927846 | 未提供 | 59.0 |
| causal | P_bal | 未提供 | logistic | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | ce_bits | 0.9983666986831664 | 0.9971911087648438 | 0.9995360268338565 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | ce_bits | 0.9987959652131706 | 0.99711462542978 | 1.0005537548115349 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | ce_bits | 0.9983666986831664 | 0.9971911087648438 | 0.9995360268338565 | 未提供 | 59.0 |
| offline | P_bal | 未提供 | logistic | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |