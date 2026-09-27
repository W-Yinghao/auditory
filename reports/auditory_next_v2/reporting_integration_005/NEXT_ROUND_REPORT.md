当前证据解读只使用下列固定完成来源，方向性描述不覆盖后面的四轴状态；待定项不填零，也不当阴性。

G0：within_child/R_SIM bAcc=0.515716；offline_bridge/causal bAcc=0.527914；offline_bridge/offline bAcc=0.524911。这是同儿童和共同试次处理敏感性的描述，不能据轻微准确率变化声称迁移或处理优越性；CE与平衡先验J仍须并读。

A2：主R_SIM未校正T=0.0153893（95% CI -0.0305962 至 0.0593238）；共同响应=0.369722（95% CI 0.301529 至 0.435123）；背景预测P=0.21398（95% CI 0.149608 至 0.273617）；残差=0.0286498（95% CI -0.0188016 至 0.0735006）。当前未校正实现未达到0.05且区间下界>0的推进条件。共享预测项本身可重复，残差不能替代未校正主终点；SUP次要结果不换主。

C2-S：跨组均值增量=-0.000237873（95% CI -0.000553362 至 2.66448e-05）；中线增量=0.000194068（95% CI -0.000368001 至 0.000678707） bits/trial。当前两个成分未共同通过正增量及重复列对照，不支持据该线性实现推进空间增量主张。精确重建说明代数完备性，不是预测收益；不能替代C2-R。

N3：H→HP=-0.0506317（95% CI -0.0577565 至 -0.0411939）；HB→HBP=0.0001004（95% CI -0.0019035 至 0.00218659）；H→Hnoise=-0.0519103（95% CI -0.0589538 至 -0.0422843） bits/trial。当前训练OOF选族实现未达到0.005且区间下界>0的EEG增量推进条件。负增益及噪声扩维代价反映有限读出风险和所选模型容量，不能称EEG负信息或无脑内信息。

N1：HP_minus_HPB=-0.0249567（95% CI -0.0279888 至 -0.0221692）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。

N2：post_gain_mu_var=-0.0014935（95% CI -0.00301731 至 -0.000257978）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。 这里仅描述源程序按完整族规则输出的logistic主矩阵；次要MLP32数值未解决，整包四轴仍保留NUMERICAL_FAILURE/NOT_EVALUABLE，不选取神经族的成功子集。 当前固定k=8均值加方差线性实现未触发本轮预定的集合网络推进条件；这不排除未检验的表示或分布特征。

C2_R：T_C=-0.000333856（95% CI -0.00104669 至 0.00030095）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。

E0_R：待定（STARTED_NO_COMPLETION）；完整族未完成/无合格聚合时不能给科学阴性。

本报告从固定版本的完成回执和公开聚合表组装，没有加载模型、读取EEG、重新拟合或重做效应bootstrap。主R_SIM与次要R_SUP/R_RAND/L0分列，不选择最好表示。实现、支持、对照、科学四轴独立；descriptive_screen仅描述已观察主量方向，不覆盖NOT_EVALUABLE，也不以阴性掩盖未完成。

主real-head gate固定tests_010；tests_009的literal-null解析错误尝试保留。tests_011仅补充当前模块实现验收，独立check-module不冒充全部真实分析gate。计划固定plan_004，共同支持固定S1_support_004。原A2残差失败是输出文件独占写入冲突；恢复只重建保存统计，不消耗新的20次ridge拟合。

| packet | implementation_status | support_status | control_status | scientific_status | descriptive_screen |
| --- | --- | --- | --- | --- | --- |
| G0 | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | DIAGNOSTIC_ONLY |
| A2 | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | MIXED |
| C2_R | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | NEGATIVE_SCREEN |
| C2_S | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | MIXED |
| N1 | PASS | SUFFICIENT_FOR_SCREEN | FAILED | NOT_EVALUABLE | NEGATIVE_SCREEN |
| N2 | NUMERICAL_FAILURE | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | NEGATIVE_SCREEN |
| N3 | PASS | SUFFICIENT_FOR_SCREEN | FAILED | NOT_EVALUABLE | NEGATIVE_SCREEN |
| E0_R | NOT_RUN | BLOCKED_INPUT | MISSING | NOT_EVALUABLE | NOT_EVALUABLE |

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
| prespecified_synthetic_execution_coverage | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| legacy_shared_table_reproduction | COMPLETE | 未提供 | 未提供 | 未提供 | G0_001 |
| refined_dependency_and_common_QC_mapping | COMPLETE | 未提供 | 未提供 | 未提供 | G0_metadata_002 |
| within_child_and_offline_bridge | COMPLETE | 未提供 | 未提供 | 未提供 | G0_readouts_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| within_child | L0 | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.9952196366634588 | 0.9909592694747992 | 0.9989714635381874 | 未提供 | 57.0 |
| within_child | L0 | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| within_child | L0 | P_bal | 未提供 | logistic | raw | ce_bits | 0.9948250546548084 | 0.990337496038527 | 0.9987706838436736 | 未提供 | 57.0 |
| within_child | L0 | P_bal | 未提供 | logistic | raw | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| within_child | L0 | P_bal | 未提供 | logistic | temperature | ce_bits | 0.9952196366634588 | 0.9909592694747992 | 0.9989714635381874 | 未提供 | 57.0 |
| within_child | L0 | P_bal | 未提供 | logistic | temperature | bacc | 0.538351941402658 | 0.5254570479131397 | 0.552183038508699 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.9933677832436918 | 0.9898579214901584 | 0.9966239766830792 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | raw | ce_bits | 0.9937373597829592 | 0.9896461572798216 | 0.9975851756156195 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | raw | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | temperature | ce_bits | 0.9933677832436918 | 0.9898579214901584 | 0.9966239766830792 | 未提供 | 57.0 |
| within_child | R_RAND | P_bal | 未提供 | logistic | temperature | bacc | 0.5318020856907029 | 0.5221185719438952 | 0.5419195401829081 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.9993870654747872 | 0.9966365257015692 | 1.0019406508562396 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.5104487741256549 | 0.4990794738495093 | 0.5223295884139254 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | raw | ce_bits | 1.0000828789526737 | 0.9958137426011316 | 1.0035987079512874 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | raw | bacc | 0.5157157888620847 | 0.5033872549768809 | 0.5285903163351398 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | temperature | ce_bits | 0.999384107153054 | 0.996634146571726 | 1.0019384808270682 | 未提供 | 57.0 |
| within_child | R_SIM | P_bal | 未提供 | logistic | temperature | bacc | 0.5157157888620847 | 0.5033872549768809 | 0.5285903163351398 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.996238453595228 | 0.9907054333641958 | 1.0011132727854408 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | raw | ce_bits | 0.9979643519233168 | 0.9915614255753672 | 1.0035670782023218 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | raw | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | temperature | ce_bits | 0.996238453595228 | 0.9907054333641958 | 1.0011132727854408 | 未提供 | 57.0 |
| within_child | R_SUP | P_bal | 未提供 | logistic | temperature | bacc | 0.5262440246899017 | 0.5119124452413613 | 0.5412332768185579 | 未提供 | 57.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.9977619417771236 | 0.9959351621992564 | 0.999445428927846 | 未提供 | 59.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | raw | ce_bits | 0.9978213678165444 | 0.9963718962844792 | 0.999161441057451 | 未提供 | 59.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | raw | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | temperature | ce_bits | 0.9977619417771236 | 0.9959351621992564 | 0.999445428927846 | 未提供 | 59.0 |
| offline_bridge | causal | P_bal | 未提供 | logistic | temperature | bacc | 0.5279141276085417 | 0.5188093563161499 | 0.5373052631836698 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | mixture_diagnostic | ce_bits | 0.9983666986831664 | 0.9971911087648438 | 0.9995360268338565 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | mixture_diagnostic | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | raw | ce_bits | 0.9987959652131706 | 0.99711462542978 | 1.0005537548115349 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | raw | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | temperature | ce_bits | 0.9983666986831664 | 0.9971911087648438 | 0.9995360268338565 | 未提供 | 59.0 |
| offline_bridge | offline | P_bal | 未提供 | logistic | temperature | bacc | 0.5249109771536224 | 0.5156243733271599 | 0.5337727889825908 | 未提供 | 59.0 |

A2：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `A2_core_001`；执行状态 `A2_CORE_RECORDED`。

共同 Ω、配额和候选集合由完整事件链、QC 与块支持冻结；所有候选使用同一 Ω/q，20 次固定无放回抽样先平均再做候选 bootstrap。主表示始终 R_SIM，R_SUP 是次要平行证据。post-minus-pre 是匹配统计量之差，不将不同宽度的 L0 向量补零相减。共同响应不能简单视为纯伪迹；残差重复性也可能由共享预测项及交叉内积产生，四项代数恒等式与合成反例单列。输出恢复只复用已保存的20次ridge，无新头/PCA/scaler拟合。

冻结 Ω=["run3_5_pos0", "run3_5_pos1"]；共同候选数=49。未入 Ω 的上下文不参与主估计，不由次要结果补回。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| post_delta_cosine | matching | 0.0153892995528579 | -0.0305961865681659 | 0.0593237586491848 | 49.0 | cosine_difference | MIXED |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | A2_core_001 |
| prespecified_synthetic_execution_coverage | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_delta_cosine | COMPLETE | 0.0153892995528579 | -0.0305961865681659 | 0.0593237586491848 | A2_core_001 |
| pre_delta_cosine | COMPLETE | 0.0106349769832528 | -0.0242502542988572 | 0.0463774679976754 | A2_core_001 |
| post_minus_pre_cosine | COMPLETE | 0.0047543225696051 | -0.0481146300298942 | 0.0561656422406773 | A2_core_001 |
| common_response_cosine | COMPLETE | 0.3697216313782003 | 0.3015292795180646 | 0.4351233174513417 | A2_core_001 |
| saved_residual_four_term_audit | COMPLETE | 未提供 | 未提供 | 未提供 | A2_residual_recovered_001 |
| fixed_quality_summary_in_background | MISSING | 未提供 | 未提供 | 未提供 | A2_residual_recovered_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

C2_R：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `C2R_core_001`；执行状态 `COMPLETE_REPAIRED_CORE`。

这是旧独立左/右 encoder 特征上的完整读出矩阵数值修复。目标、候选/类权重和 alpha 网格继承；优化器改为全批 float64 Adam，全部神经成员先1000步，任一不稳则全族统一2000步，四个最终alpha都先拟合，随后才按最终预算的内层OOF选alpha。旧LBFGS失败保留，不视为神经科学阴性。T_C每次bootstrap都重新取两侧总体CE均值的min；重复列与MLP64容量对照不能省略。置零/替换是OOD诊断，不能声称解剖因果作用。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T_C | mlp32 | -0.0003338560786889 | -0.0010466867636584 | 0.0003009497742223 | 60.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | COMPLETE | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| complete_fixed_head_replacement_matrix | COMPLETE | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| parallel_repair_and_inherited_raw_isolation | MISSING | 未提供 | 未提供 | 未提供 | C2R_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_L | linear | calibrated | ce_bits | 0.9988480781747344 | 0.997669447872081 | 1.0000328536479568 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_LL | linear | calibrated | ce_bits | 0.9989432681374832 | 0.9977818850595468 | 1.00015167539036 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_LR | linear | calibrated | ce_bits | 0.9990089025751476 | 0.9976195875025424 | 1.0004487955656018 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_R | linear | calibrated | ce_bits | 0.9996947069767146 | 0.998756235829676 | 1.0007006291170266 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_RR | linear | calibrated | ce_bits | 0.9996373820559944 | 0.9987181082213952 | 1.0006154631839792 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_L | mlp32 | calibrated | ce_bits | 0.9988133729585262 | 0.9974949833576922 | 1.0001338499214496 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_LL | mlp32 | calibrated | ce_bits | 0.9988180659178226 | 0.9976078532596948 | 1.0000572194899555 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_LR | mlp32 | calibrated | ce_bits | 0.9991472290372152 | 0.997666930858684 | 1.000639723408614 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_R | mlp32 | calibrated | ce_bits | 0.9999988688628116 | 0.9988579916279794 | 1.0012242645613978 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_RR | mlp32 | calibrated | ce_bits | 0.9996845845709126 | 0.9986290866617114 | 1.0007892317478444 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_L64 | mlp32 | calibrated | ce_bits | 0.99880633148088 | 0.9974635743412316 | 1.000154448318385 | 60.0 | 未提供 |
| complete_repaired_readout_matrix | R_SIM | P_bal | C_R64 | mlp32 | calibrated | ce_bits | 1.000004369986242 | 0.9988689325428968 | 1.0012206478768235 | 60.0 | 未提供 |

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

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| six_view_spatial | L0 | P_bal | FULL20 | logistic | calibrated | ce_bits | 0.997891666700872 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | FULL20 | logistic | calibrated | J_bits | 0.0021083332991279 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | FULL20 | logistic | calibrated | bacc | 0.5292440857825536 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0 | logistic | calibrated | ce_bits | 0.9979101685773324 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0 | logistic | calibrated | J_bits | 0.0020898314226677 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0 | logistic | calibrated | bacc | 0.5298939652081095 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S1 | logistic | calibrated | ce_bits | 0.9979899944136092 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S1 | logistic | calibrated | J_bits | 0.0020100055863909 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S1 | logistic | calibrated | bacc | 0.5304283058214708 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S2 | logistic | calibrated | ce_bits | 0.998125993422698 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S2 | logistic | calibrated | J_bits | 0.0018740065773018 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S0_DUP_S2 | logistic | calibrated | bacc | 0.5284490630779783 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S1 | logistic | calibrated | ce_bits | 0.9981480415726328 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S1 | logistic | calibrated | J_bits | 0.0018519584273672 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S1 | logistic | calibrated | bacc | 0.5256788752491391 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S2 | logistic | calibrated | ce_bits | 0.997953974028836 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S2 | logistic | calibrated | J_bits | 0.0020460259711639 | 未提供 | 未提供 | 未提供 | 未提供 |
| six_view_spatial | L0 | P_bal | S2 | logistic | calibrated | bacc | 0.5274131389405733 | 未提供 | 未提供 | 未提供 | 未提供 |

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
| prespecified_synthetic_execution_coverage | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
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

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

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

E0_R：实现 `NOT_RUN`；支持 `BLOCKED_INPUT`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `E0R_core_001`；执行状态 `STARTED_NO_COMPLETION`。

这是预定同日配对中的native128、记录内独立块目标任务可读性维护。全套有块支持记录的MLP族都数值稳定后才允许整族聚合，不能挑成功记录。旧linear精确复用，不计为新fit。纯音与bapa分别报告J及CE；混合MFF不是全CI群体。即使目标任务可读，也不证明跨儿童、跨任务迁移或临床效度；E1保持关闭。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | MISSING | 未提供 | 未提供 | 未提供 | postflight_001 |
| complete_prespecified_primary_aggregates | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| same_requested_native128_records_complete_family | MISSING | 未提供 | 未提供 | 未提供 | E0R_core_001 |
| E1_transfer | NOT_APPLICABLE | 未提供 | 未提供 | 未提供 | E0R_core_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

拟合回执与预算：

| packet | source_run | scope | attempted_fits | completed_fits | reused_fits | status |
| --- | --- | --- | --- | --- | --- | --- |
| GATES | tests_010 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| GATES | tests_009 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | BUG |
| G0 | G0_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| G0 | G0_metadata_002 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| G0 | G0_readouts_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| A2 | A2_core_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| A2 | A2_residual_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | BUG |
| A2 | A2_residual_recovered_001 | source_summary_not_per_fit_count | 0 | 0 | 20 | PASS |
| N1 | N1_core_001 | source_summary_not_per_fit_count | 760 | 未提供 | 未提供 | PASS |
| N2 | N2_core_001 | source_summary_not_per_fit_count | 720 | 480 | 未提供 | NUMERICAL_FAILURE |
| N3 | N3_core_001 | source_summary_not_per_fit_count | 600 | 未提供 | 未提供 | PASS |
| C2_S | C2S_core_001 | source_summary_not_per_fit_count | 390 | 390 | 未提供 | PASS |
| C2_R | C2R_core_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| E0_R | E0R_core_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | NOT_RUN |
| SYNTHETIC | synthetic_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | NUMERICAL_FAILURE |
| FIT_AUDIT | fit_accounting_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | NOT_RUN |
| GATES | tests_011 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N1 | N1_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_nat | 未提供 | 未提供 | 未提供 | PASS |
| N3 | N3_core_001 | complete_family:P_bal | 未提供 | 未提供 | 未提供 | PASS |

§15.2逐fit字段覆盖来自独立fit_accounting，不由本报告补造；attempt与completed分开，transform另列，recovery reuse不是新head预算。没有原生记录的预测hash、校准scope、资源等字段保持缺失，源run层hash不冒充逐fit原生字段。

| field | attempted_units | present_count | missing_count | coverage_fraction |
| --- | --- | --- | --- | --- |

| metric | value | unit | status |
| --- | --- | --- | --- |
| jobs | 未提供 | count | NOT_STARTED |
| accounted_jobs | 未提供 | count | NOT_STARTED |
| missing_jobs | 未提供 | count | NOT_STARTED |
| ongoing_jobs | 未提供 | count | NOT_STARTED |
| actual_cpu_core_hours | 未提供 | CPU core hours | NOT_STARTED |
| actual_gpu_hours | 未提供 | GPU hours | NOT_STARTED |
| actual_cpu_core_hours_lower_bound | 未提供 | CPU core hours | NOT_STARTED |
| actual_gpu_hours_lower_bound | 未提供 | GPU hours | NOT_STARTED |
| reservation_upper_cpu_core_hours | 未提供 | CPU core hours | NOT_STARTED |
| reservation_upper_gpu_hours | 未提供 | GPU hours | NOT_STARTED |
| max_cpu_core_hours | 未提供 | CPU core hours | NOT_STARTED |
| max_gpu_hours | 未提供 | GPU hours | NOT_STARTED |
| cpu_actual_complete | 未提供 | 未提供 | NOT_STARTED |
| gpu_actual_complete | 未提供 | 未提供 | NOT_STARTED |
| cpu_lower_bound_complete | 未提供 | 未提供 | NOT_STARTED |
| gpu_lower_bound_complete | 未提供 | 未提供 | NOT_STARTED |
| upper_bound_complete | 未提供 | 未提供 | NOT_STARTED |
| budget_status | 未提供 | 未提供 | NOT_STARTED |

历史sacct缺失时actual资源未知，不置0；资源保守上界与实际量分列。600合成机制draw的假阳性倾向/恢复率及未知世界固定分母见synthetic_summary；A2共用draw的W条件、N3同世界两族不算新儿童。合成机制检验不能直接声称真实样本功效。完整分母不代表正负世界已按预期区分；方案没有冻结跨世界恢复率/FPR验收阈值，本报告不事后新增。机制方向的定性复核见SYNTHETIC_INTERPRETATION.md；该复核不将数值未解决世界或未覆盖控制改为PASS，也不因完成自动支撑科学阳性。

固定来源与保留失败：

| role | source_run | execution_status | implementation_status | issues |
| --- | --- | --- | --- | --- |
| support | S1_support_004 | PASS | PASS | 未提供 |
| tests | tests_010 | PASS | PASS | 未提供 |
| tests_retained | tests_009 | FAILED | BUG | RETAINED_FAILURE |
| plan | plan_004 | PASS | PASS | 未提供 |
| g0_legacy | G0_001 | PASS | PASS | 未提供 |
| g0_metadata | G0_metadata_002 | PASS | PASS | 未提供 |
| g0_readouts | G0_readouts_001 | G0_READOUTS_COMPLETE | PASS | 未提供 |
| a2_core | A2_core_001 | A2_CORE_RECORDED | PASS | 未提供 |
| a2_residual_failed | A2_residual_001 | FAILED | BUG | RETAINED_FAILURE |
| a2_residual | A2_residual_recovered_001 | OUTPUT_FINALIZATION_REPAIRED | PASS | 未提供 |
| n1 | N1_core_001 | CORE_MATRIX_RECORDED | PASS | 未提供 |
| n2 | N2_core_001 | CORE_MATRIX_RECORDED | NUMERICAL_FAILURE | 未提供 |
| n3 | N3_core_001 | CORE_MATRIX_RECORDED | PASS | 未提供 |
| c2s | C2S_core_001 | C2S_LINEAR_MATRIX_COMPLETE | PASS | 未提供 |
| c2r | C2R_core_001 | COMPLETE_REPAIRED_CORE | PASS | 未提供 |
| e0r | E0R_core_001 | STARTED_NO_COMPLETION | NOT_RUN | 未提供 |
| synthetic | synthetic_001 | NUMERICAL_INCOMPLETE | NUMERICAL_FAILURE | 未提供 |
| metrics | metrics_001 | NOT_STARTED | NOT_RUN | 未提供 |
| postflight | postflight_001 | NOT_STARTED | NOT_RUN | 未提供 |
| resources | resources_001 | NOT_STARTED | NOT_RUN | 未提供 |
| fit_accounting | fit_accounting_001 | NOT_STARTED | NOT_RUN | 未提供 |
| tests_supplement | tests_011 | PASS | PASS | 未提供 |

来源精确SHA256在source_hashes.csv的逻辑别名下；真实路径映射和异常细节仅保存在private。各packet图只画预设主比较及必要对照的总体点和完整区间，不画个体点，不隐藏负值；缺输入不绘制零值替代图。

旧结论保持冻结，本轮没有新的临床终点或B/D重新选型。旧B完整控制后的R_SIM条件历史增益未达到原0.01 bits门槛；旧D的临床增量未达到原0.5源量表单位门槛。这些是已有阴性筛查，不能由本轮新N3估计对象改写。旧C/E数值失败不是科学阴性，修复前后源回执均保留。

E1跨任务迁移保持关闭：原bapa安全候选支持16，低于20；E0记录内目标可读性不替代E1。MFF来源混合，不能整体称CI样本。本轮已见数据下的探索不能把已有候选重新描述为未触碰外部验证。

下一步只可针对已缺证据推进：A2须限制共享背景预测项解释；C2-R须先完成预定整族与继承隔离控制；N1/N3须解释先验、pre和容量代价；N2须在相同bag预算与共同队列验证分布增量。已完成且增量阴性的具体估计器不因改名或扩大网络重新成为原假设的确认性检验。
