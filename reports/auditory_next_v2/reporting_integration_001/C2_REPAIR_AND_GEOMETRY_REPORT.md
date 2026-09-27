C2_R：实现 `NOT_RUN`；支持 `BLOCKED_INPUT`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `C2R_core_001`；执行状态 `NOT_STARTED`。

这是旧独立左/右 encoder 特征上的完整读出矩阵数值修复。目标、候选/类权重和 alpha 网格继承；优化器改为全批 float64 Adam，全部神经成员先1000步，任一不稳则全族统一2000步，四个最终alpha都先拟合，随后才按最终预算的内层OOF选alpha。旧LBFGS失败保留，不视为神经科学阴性。T_C每次bootstrap都重新取两侧总体CE均值的min；重复列与MLP64容量对照不能省略。置零/替换是OOD诊断，不能声称解剖因果作用。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | MISSING | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| complete_fixed_head_replacement_matrix | MISSING | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| parallel_repair_and_inherited_raw_isolation | MISSING | 未提供 | 未提供 | 未提供 | C2R_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

C2_S：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `C2S_core_001`；执行状态 `C2S_LINEAR_MATRIX_COMPLETE`。

这是新的20通道观测对象：L8/R8/M4的五种空间成分在共同平均参考下含19个有效自由度；精确重建只证明代数完备性。S0→S1检验跨组均值差，S1→S2检验中线局部信息，两者须与匹配宽度重复列比较；FULL20为参考。局部成分数值不依赖对侧原始数值，但完整记录QC决定入选，selection_isolation=False。主L0 logistic六视图完整矩阵独立于C2-R；次要MLP处于预算限制。

源几何回执：post重建最大误差=2.84217e-14；全epoch=2.84217e-14；19维=1.13687e-13 μV。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G_crossmean | logistic | -0.0002378729953003 | -0.0005533624027012 | 2.664475798420659e-05 | 60.0 | bits/trial | NEGATIVE_SCREEN |
| G_midline | logistic | 0.0001940675437963 | -0.0003680012893737 | 0.0006787072926472 | 60.0 | bits/trial | MIXED |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | C2S_core_001 |
| full_twenty_channel_reconstruction_and_numeric_isolation | COMPLETE | 未提供 | 未提供 | 未提供 | C2S_core_001 |
| crossmean_matched_width_margin | COMPLETE | -0.0001580471590236 | -0.0004775529740335 | 0.0001191032558647 | C2S_core_001 |
| complete_spatial_matched_width_margin | COMPLETE | 0.0001720193938619 | -0.0003867936546282 | 0.0006868262924856 | C2S_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| representation | population_id | model | readout_family | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 | P_bal | FULL20 | logistic | ce_bits | 0.997891666700872 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | FULL20 | logistic | J_bits | 0.0021083332991279 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | FULL20 | logistic | bacc | 0.5292440857825536 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0 | logistic | ce_bits | 0.9979101685773324 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0 | logistic | J_bits | 0.0020898314226677 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0 | logistic | bacc | 0.5298939652081095 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S1 | logistic | ce_bits | 0.9979899944136092 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S1 | logistic | J_bits | 0.0020100055863909 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S1 | logistic | bacc | 0.5304283058214708 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S2 | logistic | ce_bits | 0.998125993422698 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S2 | logistic | J_bits | 0.0018740065773018 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S0_DUP_S2 | logistic | bacc | 0.5284490630779783 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S1 | logistic | ce_bits | 0.9981480415726328 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S1 | logistic | J_bits | 0.0018519584273672 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S1 | logistic | bacc | 0.5256788752491391 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S2 | logistic | ce_bits | 0.997953974028836 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S2 | logistic | J_bits | 0.0020460259711639 | 未提供 | 未提供 | 未提供 | 未提供 |
| L0 | P_bal | S2 | logistic | bacc | 0.5274131389405733 | 未提供 | 未提供 | 未提供 | 未提供 |