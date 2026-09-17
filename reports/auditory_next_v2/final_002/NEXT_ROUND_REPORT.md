当前证据解读只使用下列固定完成来源，方向性描述不覆盖后面的四轴状态；待定项不填零，也不当阴性。

G0：G0_within__/R_SIM bAcc=0.515716；G0_bridge__causal/source-defined bAcc=0.527914；G0_bridge__offline/source-defined bAcc=0.524911。这是同儿童和共同试次处理敏感性的描述，不能据轻微准确率变化声称迁移或处理优越性；CE与平衡先验J仍须并读。

A2：主R_SIM未校正T=0.0153893（95% CI -0.0305962 至 0.0593238）；共同响应=0.369722（95% CI 0.301529 至 0.435123）；背景预测P=0.21398（95% CI 0.149608 至 0.273617）；残差=0.0286498（95% CI -0.0188016 至 0.0735006）。当前未校正实现未达到0.05且区间下界>0的推进条件。共享预测项本身可重复，残差不能替代未校正主终点；SUP次要结果不换主。

C2-S：跨组均值增量=-0.000237873（95% CI -0.000553362 至 2.66448e-05）；中线增量=0.000194068（95% CI -0.000368001 至 0.000678707） bits/trial。当前两个成分未共同通过正增量及重复列对照，不支持据该线性实现推进空间增量主张。精确重建说明代数完备性，不是预测收益；不能替代C2-R。

N3：H→HP=-0.0506317（95% CI -0.0577565 至 -0.0411939）；HB→HBP=0.0001004（95% CI -0.0019035 至 0.00218659）；H→Hnoise=-0.0519103（95% CI -0.0589538 至 -0.0422843） bits/trial。当前训练OOF选族实现未达到0.005且区间下界>0的EEG增量推进条件。负增益及噪声扩维代价反映有限读出风险和所选模型容量，不能称EEG负信息或无脑内信息。

N1：HP_minus_HPB=-0.0249567（95% CI -0.0279888 至 -0.0221692）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。

N2：post_gain_mu_var=-0.0014935（95% CI -0.00301731 至 -0.000257978）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。 这里仅描述源程序按完整族规则输出的logistic主矩阵；次要MLP32数值未解决，整包四轴仍保留NUMERICAL_FAILURE/NOT_EVALUABLE，不选取神经族的成功子集。 不含EEG的H_BAG基线：ce_bits=0.131678；bacc=0.982883。高准确率须先与此历史基线比较，不能归为EEG分布收益。 当前固定k=8均值加方差线性实现未触发本轮预定的集合网络推进条件；这不排除未检验的表示或分布特征。

C2_R：T_C=-0.000333856（95% CI -0.00104669 至 0.00030095）。当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。

E0_R：本轮数值未完成（INCOMPLETE_PRIMARY_MATRIX）；完整族未完成/无合格聚合时不能给科学阴性。

交付修订：首版postflight_001记录51项日志权限异常；本版固定复核为postflight_002，状态PASS。final_001的旧round_complete字段只检查来源终态，未阻止权限失败，不能作为最终验收依据；本版要求旧文件、private权限及资源预算通过后才允许round_complete。原失败回执和首版报告保留。

本报告从固定版本的完成回执和公开聚合表组装，没有加载模型、读取EEG、重新拟合或重做效应bootstrap。主R_SIM与次要R_SUP/R_RAND/L0分列，不选择最好表示。实现、支持、对照、科学四轴独立；descriptive_screen仅描述已观察主量方向，不覆盖NOT_EVALUABLE，也不以阴性掩盖未完成。

主real-head gate固定tests_010；tests_009的literal-null解析错误尝试保留。tests_011仅补充当前模块实现验收，独立check-module不冒充全部真实分析gate。计划固定plan_004，共同支持固定S1_support_004。原A2残差失败是输出文件独占写入冲突；恢复只重建保存统计，不消耗新的20次ridge拟合。

| packet | implementation_status | support_status | control_status | scientific_status | descriptive_screen |
| --- | --- | --- | --- | --- | --- |
| G0 | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | DIAGNOSTIC_ONLY |
| A2 | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | MIXED |
| C2_R | PASS | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | NEGATIVE_SCREEN |
| C2_S | PASS | SUFFICIENT_FOR_SCREEN | COMPLETE | MIXED | MIXED |
| N1 | PASS | SUFFICIENT_FOR_SCREEN | FAILED | NOT_EVALUABLE | NEGATIVE_SCREEN |
| N2 | NUMERICAL_FAILURE | SUFFICIENT_FOR_SCREEN | MISSING | NOT_EVALUABLE | NEGATIVE_SCREEN |
| N3 | PASS | SUFFICIENT_FOR_SCREEN | FAILED | NOT_EVALUABLE | NEGATIVE_SCREEN |
| E0_R | NUMERICAL_FAILURE | DESCRIPTIVE_ONLY | MISSING | NOT_EVALUABLE | DIAGNOSTIC_ONLY |

G0：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `G0_readouts_001`；执行状态 `G0_READOUTS_COMPLETE`。

共享旧表的重新拟合 logistic probe 与原 R_SUP CNN head 分开报告；原头的 TRAIN_DIAGNOSTIC 分数仅说明优化，不是外层泛化。G0_metadata_002 替代早期时间角色/桥接支持，不替代已复算旧指标。同儿童的后块预测和共享外儿童预测具有不同训练对象，不能只按准确率大小宣称迁移成功。因果/offline 桥接使用共同 QC 试次，仍是处理敏感性。微弱 bAcc/AUC 不保证 CE 优于先验，J 的负值保留。

旧共享表复算最大误差=2.22045e-16。原within_receipts中的n_calibration存在记录元数据错误，本报告不使用它；实际训练样本数应以原生fit start的n或时间角色核对，不能用校准参数字典长度。温度记录数是应用到各头的次数，不是独立校准参数数。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| legacy_shared_table_reproduction | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | G0_001 |
| refined_dependency_and_common_QC_mapping | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | G0_metadata_002 |
| within_child_and_offline_bridge | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | G0_readouts_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.9952196366634584 | 0.991156956597764 | 0.9992176814468224 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.004780363336541638 | 0.0007823185531775634 | 0.008843043402235962 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.5383519414026579 | 0.5257928046248131 | 0.5510146976568764 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | raw | ce_bits | 0.9948250546548082 | 0.9904676318654768 | 0.998953705550806 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | raw | J_bits | 0.005174945345191806 | 0.0010462944491940185 | 0.009532368134523184 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | raw | bacc | 0.5383519414026579 | 0.5257928046248131 | 0.5510146976568764 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.9952196366634584 | 0.991156956597764 | 0.9992176814468224 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.004780363336541638 | 0.0007823185531775634 | 0.008843043402235962 | 57.0 | 未提供 |
| G0_within__ | L0 | P_bal | 未提供 | 未提供 | temperature | bacc | 0.5383519414026579 | 0.5257928046248131 | 0.5510146976568764 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.9933677832436922 | 0.9898260262647436 | 0.9968361779478526 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.006632216756307763 | 0.0031638220521473803 | 0.010173973735256414 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.531802085690703 | 0.5222344531743864 | 0.541622551875583 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | raw | ce_bits | 0.9937373597829592 | 0.9895141359262438 | 0.99782478209978 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | raw | J_bits | 0.006262640217040816 | 0.0021752179002200167 | 0.01048586407375618 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | raw | bacc | 0.531802085690703 | 0.5222344531743864 | 0.541622551875583 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.9933677832436922 | 0.9898260262647436 | 0.9968361779478526 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.006632216756307763 | 0.0031638220521473803 | 0.010173973735256414 | 57.0 | 未提供 |
| G0_within__ | R_RAND | P_bal | 未提供 | 未提供 | temperature | bacc | 0.531802085690703 | 0.5222344531743864 | 0.541622551875583 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.9993870654747872 | 0.9967908395200556 | 1.0018097747877672 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.0006129345252128271 | -0.0018097747877672266 | 0.0032091604799443507 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.510448774125655 | 0.4991450269764961 | 0.5215792328538947 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | raw | ce_bits | 1.000082878952674 | 0.9961621215866998 | 1.0036150529759944 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | raw | J_bits | -8.287895267389267e-05 | -0.003615052975994404 | 0.0038378784133001886 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | raw | bacc | 0.5157157888620847 | 0.5033695017519826 | 0.5284275857349129 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.999384107153054 | 0.996789749257077 | 1.001806886015285 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.0006158928469459646 | -0.001806886015284892 | 0.0032102507429230265 | 57.0 | 未提供 |
| G0_within__ | R_SIM | P_bal | 未提供 | 未提供 | temperature | bacc | 0.5157157888620847 | 0.5033695017519826 | 0.5284275857349129 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.996238453595228 | 0.9908963918401058 | 1.0013131767810552 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.003761546404771998 | -0.0013131767810552475 | 0.009103608159894194 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.5262440246899021 | 0.5113489321123936 | 0.5414317168982237 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | raw | ce_bits | 0.9979643519233168 | 0.9918951199268972 | 1.0038094048512634 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | raw | J_bits | 0.0020356480766832163 | -0.003809404851263354 | 0.008104880073102838 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | raw | bacc | 0.5262440246899021 | 0.5113489321123936 | 0.5414317168982237 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.996238453595228 | 0.9908963918401058 | 1.0013131767810552 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.003761546404771998 | -0.0013131767810552475 | 0.009103608159894194 | 57.0 | 未提供 |
| G0_within__ | R_SUP | P_bal | 未提供 | 未提供 | temperature | bacc | 0.5262440246899021 | 0.5113489321123936 | 0.5414317168982237 | 57.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.997761941777124 | 0.99598746785709 | 0.999479295126224 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.002238058222876038 | 0.000520704873775979 | 0.004012532142909975 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.5279141276085417 | 0.5187634635012316 | 0.5370964688933926 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | raw | ce_bits | 0.9978213678165444 | 0.9963712129289009 | 0.9992031525577276 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | raw | J_bits | 0.0021786321834555977 | 0.0007968474422723748 | 0.0036287870710991488 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | raw | bacc | 0.5279141276085417 | 0.5187634635012316 | 0.5370964688933926 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.997761941777124 | 0.99598746785709 | 0.999479295126224 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.002238058222876038 | 0.000520704873775979 | 0.004012532142909975 | 59.0 | 未提供 |
| G0_bridge__causal | 未提供 | P_bal | 未提供 | 未提供 | temperature | bacc | 0.5279141276085417 | 0.5187634635012316 | 0.5370964688933926 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | ce_bits | 0.9983666986831662 | 0.9972024801717836 | 0.9995688571149984 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | J_bits | 0.0016333013168338129 | 0.0004311428850015675 | 0.0027975198282164104 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | mixture_diagnostic | bacc | 0.5249109771536226 | 0.5162958223147801 | 0.5340112323639854 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | raw | ce_bits | 0.9987959652131706 | 0.9971567979100748 | 1.000557218029461 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | raw | J_bits | 0.0012040347868294 | -0.0005572180294610707 | 0.0028432020899251675 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | raw | bacc | 0.5249109771536226 | 0.5162958223147801 | 0.5340112323639854 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | temperature | ce_bits | 0.9983666986831662 | 0.9972024801717836 | 0.9995688571149984 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | temperature | J_bits | 0.0016333013168338129 | 0.0004311428850015675 | 0.0027975198282164104 | 59.0 | 未提供 |
| G0_bridge__offline | 未提供 | P_bal | 未提供 | 未提供 | temperature | bacc | 0.5249109771536226 | 0.5162958223147801 | 0.5340112323639854 | 59.0 | 未提供 |

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

C2_R：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `C2R_core_001`；执行状态 `COMPLETE_REPAIRED_CORE`。

这是旧独立左/右 encoder 特征上的完整读出矩阵数值修复。目标、候选/类权重和 alpha 网格继承；优化器改为全批 float64 Adam，全部神经成员先1000步，任一不稳则全族统一2000步，四个最终alpha都先拟合，随后才按最终预算的内层OOF选alpha。旧LBFGS失败保留，不视为神经科学阴性。T_C每次bootstrap都重新取两侧总体CE均值的min；重复列与MLP64容量对照不能省略。置零/替换是OOD诊断，不能声称解剖因果作用。

内折仅重新拟合读出与其缩放，outer encoder保持冻结，inner_encoder_refitted=False；这不是编码器在内外折都重新训练的完整嵌套验证。容量控制的margin与主T_C并列，不由替换诊断改变主结论。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T_C | mlp32 | -0.0003338560786889 | -0.0010466867636584 | 0.0003009497742223 | 60.0 | bits/trial | NEGATIVE_SCREEN |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| G_R_given_L | P_bal | mlp32 | calibrated | COMPLETE | -0.0003338560786889 | -0.0010466867636584 | 0.0003378555627182 | C2R_core_001 |
| G_L_given_R | P_bal | mlp32 | calibrated | COMPLETE | 0.0008516398255963 | -3.631088196499044e-05 | 0.0016885799796268 | C2R_core_001 |
| J_joint | P_bal | mlp32 | calibrated | COMPLETE | 0.0008527709627847 | -0.000639723408614 | 0.002333069141316 | C2R_core_001 |
| duplicate_margin | P_bal | mlp32 | calibrated | COMPLETE | -0.0003291631193925 | -0.0010247696600563 | 0.0002929831616585 | C2R_core_001 |
| expanded_margin | P_bal | mlp32 | calibrated | COMPLETE | -0.0003408975563351 | -0.0010509406680846 | 0.0002903328394023 | C2R_core_001 |
| capacity_margin | P_bal | mlp32 | calibrated | COMPLETE | -0.0003408975563351 | -0.0010846966184331 | 0.0002271483718436 | C2R_core_001 |
| complete_fixed_head_replacement_matrix | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | C2R_core_001 |
| parallel_repair_and_inherited_raw_isolation | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | C2R_core_001 |

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

C2_S：实现 `PASS`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `COMPLETE`；科学状态 `MIXED`。固定来源 `C2S_core_001`；执行状态 `C2S_LINEAR_MATRIX_COMPLETE`。

这是新的20通道观测对象：L8/R8/M4的五种空间成分在共同平均参考下含19个有效自由度；精确重建只证明代数完备性。S0→S1检验跨组均值差，S1→S2检验中线局部信息，两者须与匹配宽度重复列比较；FULL20为参考。局部成分数值不依赖对侧原始数值，但完整记录QC决定入选，selection_isolation=False。主L0 logistic六视图完整矩阵独立于C2-R；次要MLP处于预算限制。

源几何回执：post重建最大误差=2.84217e-14；全epoch=2.84217e-14；19维=1.13687e-13 μV。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G_crossmean | logistic | -0.0002378729953003 | -0.0005533624027012 | 2.664475798420659e-05 | 60.0 | bits/trial | NEGATIVE_SCREEN |
| G_midline | logistic | 0.0001940675437963 | -0.0003680012893737 | 0.0006787072926472 | 60.0 | bits/trial | MIXED |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | C2S_core_001 |
| full_twenty_channel_reconstruction_and_numeric_isolation | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | C2S_core_001 |
| crossmean_matched_width_margin | P_bal | logistic | calibrated | COMPLETE | -0.0001580471590236 | -0.0004775529740335 | 0.0001191032558647 | C2S_core_001 |
| complete_spatial_matched_width_margin | P_bal | logistic | calibrated | COMPLETE | 0.0001720193938619 | -0.0003867936546282 | 0.0006868262924856 | C2S_core_001 |

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

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| complete_required_head_families | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| declared_inner_OOF_calibration | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| two_fixed_head_donor_assignments | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| matched_donor_training_same_support_reference | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N1_core_001 |
| fixed_head_donor:same_child_B-actual_B | 未提供 | 未提供 | 未提供 | COMPLETE | 0.0030460265981769 | 0.0003866922786802 | 0.0056752592411666 | N1_core_001 |
| fixed_head_donor:training_child_B-actual_B | 未提供 | 未提供 | 未提供 | COMPLETE | -0.002205871766235 | -0.0060475978099179 | 0.0012624272082767 | N1_core_001 |
| matched_training_donor_vs_same_support_reference:HPB_donor_support_reference-HPB_training_child_donor | 未提供 | 未提供 | 未提供 | COMPLETE | -0.0062084418450781 | -0.0126918063498331 | -0.0012426184504645 | N1_core_001 |
| HPP_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | -0.0119874380903146 | -0.0145278597463982 | -0.0094226354263356 | N1_core_001 |
| HPBnoise_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | 0.004886121246093 | -0.0011759657678446 | 0.0099085427205381 | N1_core_001 |
| HB_minus_HPB | P_nat | mlp32 | temperature | COMPLETE | -0.0241528137667634 | -0.027591464758276 | -0.020944091986163 | N1_core_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1__ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.6816646689589353 | 0.615715531370024 | 0.7817816728054325 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | H | logistic | temperature | J_bits | 0.3183353310410647 | 0.21821832719456746 | 0.384284468629976 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | H | logistic | temperature | bacc | 0.7592954109045562 | 0.7434866670636346 | 0.7706574442969031 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | ce_bits | 0.6826324291503479 | 0.6180985772472891 | 0.7802615586750894 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | J_bits | 0.31736757084965206 | 0.2197384413249106 | 0.3819014227527109 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HB | logistic | temperature | bacc | 0.7536227118251613 | 0.7386906913506722 | 0.7644238523618141 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | ce_bits | 0.6818467766733127 | 0.6172347608684853 | 0.7792942871878095 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | J_bits | 0.3181532233266873 | 0.22070571281219054 | 0.3827652391315147 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HP | logistic | temperature | bacc | 0.7539367187264326 | 0.7386225043861374 | 0.7649590694026864 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | ce_bits | 0.6828137520849988 | 0.6195908217070192 | 0.7776990236010952 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | J_bits | 0.31718624791500116 | 0.22230097639890478 | 0.3804091782929808 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPB | logistic | temperature | bacc | 0.7504839104327774 | 0.7348652620740461 | 0.7616986688071774 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | ce_bits | 0.6823815984413184 | 0.6184635332367358 | 0.778223153511472 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | J_bits | 0.3176184015586816 | 0.22177684648852802 | 0.38153646676326425 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPBnoise | logistic | temperature | bacc | 0.7507259102444152 | 0.7347313149926431 | 0.7621040049827441 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | ce_bits | 0.6818783906529151 | 0.6173357593894979 | 0.7791852916556798 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | J_bits | 0.3181216093470849 | 0.22081470834432015 | 0.3826642406105021 | 59.0 | 未提供 |
| N1__ | L0 | P_bal | HPP | logistic | temperature | bacc | 0.7540199091084676 | 0.7387301074727143 | 0.76499811999026 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | H | logistic | temperature | ce_bits | 0.5168787240299256 | 0.4854082842310701 | 0.562709126199008 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | H | logistic | temperature | bacc | 0.5960072439282826 | 0.5890294646339228 | 0.6015014259714037 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HB | logistic | temperature | ce_bits | 0.5176488654073991 | 0.4864012622352835 | 0.5630974596246463 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HB | logistic | temperature | bacc | 0.5958278434121863 | 0.5886761344016732 | 0.6012613215053115 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HP | logistic | temperature | ce_bits | 0.5174078787545053 | 0.4861857209069933 | 0.5630623408715435 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HP | logistic | temperature | bacc | 0.5979792663040185 | 0.5905042533092109 | 0.6037612649604212 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPB | logistic | temperature | ce_bits | 0.5181274930550498 | 0.4871033348511925 | 0.5633811225090242 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPB | logistic | temperature | bacc | 0.599367281157731 | 0.5920513104724775 | 0.6050064423495756 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPBnoise | logistic | temperature | ce_bits | 0.5176662977419385 | 0.4867514928816455 | 0.562998157066107 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPBnoise | logistic | temperature | bacc | 0.5992065159831401 | 0.5917133733371861 | 0.6049707320720076 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPP | logistic | temperature | ce_bits | 0.5174557076517331 | 0.4862879444383458 | 0.5631087844167438 | 59.0 | 未提供 |
| N1__ | L0 | P_nat | HPP | logistic | temperature | bacc | 0.5979612809956782 | 0.5905576335636846 | 0.6037803204728562 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.6816646689589353 | 0.615715531370024 | 0.7817816728054325 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.3183353310410647 | 0.21821832719456746 | 0.384284468629976 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.7592954109045562 | 0.7434866670636346 | 0.7706574442969031 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | ce_bits | 0.6838943264566825 | 0.6188922967096954 | 0.782448542549118 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | J_bits | 0.31610567354331753 | 0.217551457450882 | 0.38110770329030463 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | logistic | temperature | bacc | 0.7492669970902255 | 0.7342271551742174 | 0.7600482167303835 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | ce_bits | 0.681940301899874 | 0.6169501731939675 | 0.7803372185551298 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | J_bits | 0.318059698100126 | 0.21966278144487017 | 0.3830498268060325 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | logistic | temperature | bacc | 0.7517139649300288 | 0.7360797866731087 | 0.7628817333234947 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | ce_bits | 0.6839717661564899 | 0.6199528758770108 | 0.7805596856099494 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | J_bits | 0.3160282338435101 | 0.21944031439005063 | 0.38004712412298924 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | logistic | temperature | bacc | 0.7485199765509246 | 0.7327690845178161 | 0.7598272109232329 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | ce_bits | 0.6826365450728091 | 0.6189001769347153 | 0.7791266392981626 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | J_bits | 0.31736345492719087 | 0.22087336070183738 | 0.38109982306528467 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | logistic | temperature | bacc | 0.7505952962238893 | 0.7352374728763631 | 0.7616502650640188 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | ce_bits | 0.6822176460061098 | 0.6176565113042913 | 0.7800234269409457 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | J_bits | 0.3177823539938902 | 0.21997657305905427 | 0.38234348869570867 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | logistic | temperature | bacc | 0.7514326457864384 | 0.7362083603083768 | 0.7625533659728755 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | ce_bits | 0.5974988715589957 | 0.5561056430841236 | 0.6629475536474032 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | J_bits | 0.4025011284410043 | 0.3370524463525968 | 0.4438943569158764 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | H | mlp32 | temperature | bacc | 0.7900614651620187 | 0.7722640424372186 | 0.8019870113180696 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | ce_bits | 0.6638285900472644 | 0.6360805024991172 | 0.7056853788327865 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | J_bits | 0.33617140995273564 | 0.2943146211672135 | 0.3639194975008828 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HB | mlp32 | temperature | bacc | 0.73944443783777 | 0.7250648681624771 | 0.7501782866638865 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | ce_bits | 0.664780542257348 | 0.6387443609379745 | 0.7029948147154567 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | J_bits | 0.33521945774265205 | 0.29700518528454334 | 0.3612556390620255 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HP | mlp32 | temperature | bacc | 0.7352023349879699 | 0.7205914165095121 | 0.7468668416045642 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | ce_bits | 0.7108820030851594 | 0.688431820235743 | 0.7433882114609142 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | J_bits | 0.28911799691484064 | 0.25661178853908584 | 0.311568179764257 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPB | mlp32 | temperature | bacc | 0.7096835605908637 | 0.6955044817074735 | 0.7206465616399909 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | ce_bits | 0.7198670763246329 | 0.698437420740833 | 0.7497389193216332 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | J_bits | 0.28013292367536713 | 0.25026108067836683 | 0.30156257925916696 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPBnoise | mlp32 | temperature | bacc | 0.7062928031162161 | 0.6941703131247182 | 0.716000229403836 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | ce_bits | 0.6818471532294217 | 0.6565681235639379 | 0.7189300098702359 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | J_bits | 0.3181528467705783 | 0.2810699901297641 | 0.3434318764360621 | 59.0 | 未提供 |
| N1__ | R_SIM | P_bal | HPP | mlp32 | temperature | bacc | 0.7296584523934543 | 0.7154091049801344 | 0.7397529809700117 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | logistic | temperature | ce_bits | 0.5168787240299256 | 0.4854082842310701 | 0.562709126199008 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | logistic | temperature | bacc | 0.5960072439282826 | 0.5890294646339228 | 0.6015014259714037 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | logistic | temperature | ce_bits | 0.5184389061795361 | 0.4867874514598857 | 0.5642595660956659 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | logistic | temperature | bacc | 0.596286157601168 | 0.5891405175353669 | 0.6019543578888509 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | logistic | temperature | ce_bits | 0.5172168957393931 | 0.4852876893627936 | 0.563770614909887 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | logistic | temperature | bacc | 0.5983195763327688 | 0.5909072998115513 | 0.6041482638148895 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | logistic | temperature | ce_bits | 0.5185906053364068 | 0.4864576725943297 | 0.5653501199666141 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | logistic | temperature | bacc | 0.5994118799771317 | 0.5917385534608478 | 0.6052218440032825 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | logistic | temperature | ce_bits | 0.5174763719742054 | 0.4856750855104371 | 0.5636027870666132 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | logistic | temperature | bacc | 0.6007880074097856 | 0.5934666018044239 | 0.6066497614642072 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | logistic | temperature | ce_bits | 0.5175120013175425 | 0.4856227550208974 | 0.5641929508055683 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | logistic | temperature | bacc | 0.5993044848991945 | 0.5916577212443046 | 0.6051434802300214 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | mlp32 | temperature | ce_bits | 0.464342194257184 | 0.4448913809749162 | 0.4926395961536024 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | H | mlp32 | temperature | bacc | 0.6254978598844075 | 0.6179160828660061 | 0.6314068324335649 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | mlp32 | temperature | ce_bits | 0.4941164259421147 | 0.47474592938935 | 0.5221583633553374 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HB | mlp32 | temperature | bacc | 0.6181902087031488 | 0.6088903084311078 | 0.6249977811567861 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | mlp32 | temperature | ce_bits | 0.4933125570499458 | 0.4744217452802981 | 0.5207403106941679 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HP | mlp32 | temperature | bacc | 0.6213819945087977 | 0.6136848802837344 | 0.6274990522775377 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | mlp32 | temperature | ce_bits | 0.5182692397088782 | 0.4981590567949723 | 0.5467690675230501 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB | mlp32 | temperature | bacc | 0.641582087356711 | 0.632124159111239 | 0.6495148487484562 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_donor_support_reference | mlp32 | temperature | ce_bits | 0.518998061772856 | 0.4987262209992136 | 0.5476550852227112 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_donor_support_reference | mlp32 | temperature | bacc | 0.64121063679215 | 0.6309519020374244 | 0.6494596535460724 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_training_child_donor | mlp32 | temperature | ce_bits | 0.5252065036179342 | 0.5017493498597769 | 0.5588317085158632 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPB_training_child_donor | mlp32 | temperature | bacc | 0.64050285264189 | 0.6307184538949918 | 0.6481891771991674 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | mlp32 | temperature | ce_bits | 0.5231553609549712 | 0.5070024460860415 | 0.5458775340618757 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPBnoise | mlp32 | temperature | bacc | 0.6367551402507866 | 0.6279361941790867 | 0.6433720963458293 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | mlp32 | temperature | ce_bits | 0.5062818016185635 | 0.4873076805111612 | 0.5330814275168769 | 59.0 | 未提供 |
| N1__ | R_SIM | P_nat | HPP | mlp32 | temperature | bacc | 0.6323018551602554 | 0.6234626778558922 | 0.6398016087681095 | 59.0 | 未提供 |

N2：实现 `NUMERICAL_FAILURE`；支持 `SUFFICIENT_FOR_SCREEN`；对照 `MISSING`；科学状态 `NOT_EVALUABLE`。固定来源 `N2_core_001`；执行状态 `CORE_MATRIX_RECORDED`。

主对象固定 R_SIM/P_bal/logistic、k=8同一袋上的HMU−HMUVAR，量级0.01 bits/bag；需要超过重复均值列、pre与H_BAG解释。10次测试重组不重新拟合，必须先按候选平均后评价方向。k=4/8/16共同支持审计只说明支持；未运行的k曲线不得作图或宣称已完成。pre与post窗长度不同，二者差异不是纯因果响应。

主预设效应（空表表示尚无合格主聚合，不能当作零）：

| analysis_id | readout_family | estimate | ci_lower | ci_upper | n_candidates | unit | descriptive_screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| post_gain_mu_var | logistic | -0.0014935038347629 | -0.0030173067911442 | -0.0002579784684654 | 57.0 | bits/bag | NEGATIVE_SCREEN |

固定对照执行状态：

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| post_mv_vs_dup | P_bal | logistic | temperature | COMPLETE | -0.000828735991338 | -0.0017620540304157 | 0.0001031153272239 | N2_core_001 |
| pre_gain_mu_var | P_bal | logistic | temperature | COMPLETE | 0.0009098707435204 | -0.000192159062132 | 0.0021043825935774 | N2_core_001 |
| post_minus_pre_gain_mu_var_post_minus_pre | P_bal | logistic | temperature | COMPLETE | -0.0024033745782834 | -0.0048201105577513 | -0.0006369280766953 | N2_core_001 |
| ten_frozen_test_regroupings | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N2_core_001 |
| regrouping_average_post_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | -0.0005423520268466 | -0.0012754500941366 | 0.0002696078337295 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | -0.0007018547620667 | -0.0012637186230403 | -0.0001684802534161 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | 0.0001980273794837 | -0.0006700764805348 | 0.0012713640031106 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | 0.0003318463390711 | -0.0005460152322084 | 0.0014053793057686 | N2_core_001 |
| regrouping_average_post_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | -0.0015236912218686 | -0.0031559840655442 | -0.0001977305286167 | N2_core_001 |
| regrouping_average_post_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | -0.0009215024675311 | -0.0019632072946629 | 8.140796169223956e-05 | N2_core_001 |
| regrouping_average_pre_gain_mu_var | 未提供 | logistic | temperature | COMPLETE | 0.0002111274306447 | -0.0005299652825255 | 0.0008989215655122 | N2_core_001 |
| regrouping_average_pre_mv_vs_dup | 未提供 | logistic | temperature | COMPLETE | 0.0003473490596605 | -0.0003338576645715 | 0.0010259126528834 | N2_core_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N2_post_ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | ce_bits | 0.1310694608270171 | 0.0414915846601707 | 0.3034124244493481 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | J_bits | 0.8689305391729829 | 0.6965875755506519 | 0.9585084153398293 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMU | logistic | temperature | bacc | 0.9831944547696632 | 0.9669115093698252 | 0.9924282990768662 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | ce_bits | 0.132738225049188 | 0.0412086493659619 | 0.3081211123350146 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | J_bits | 0.867261774950812 | 0.6918788876649854 | 0.9587913506340381 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMU | logistic | temperature | bacc | 0.9826342367221196 | 0.9666485733417528 | 0.9919521607472084 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1308508212660176 | 0.0415927482673073 | 0.3022773106712539 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | J_bits | 0.8691491787339825 | 0.697722689328746 | 0.9584072517326927 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUMU | logistic | temperature | bacc | 0.9831944547696632 | 0.9669115093698252 | 0.9924282990768662 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1330495879693615 | 0.0413548817768483 | 0.3086741781207411 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | J_bits | 0.8669504120306385 | 0.6913258218792588 | 0.9586451182231517 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUMU | logistic | temperature | bacc | 0.983005356830082 | 0.9674736587432284 | 0.992088767365704 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.132520710895277 | 0.0425904048024619 | 0.304813382173483 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8674792891047229 | 0.6951866178265169 | 0.9574095951975381 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HMUVAR | logistic | temperature | bacc | 0.9828685051653862 | 0.9666508376243464 | 0.9922745527472256 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.132586500564046 | 0.0413177968339404 | 0.3074556430906874 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | J_bits | 0.867413499435954 | 0.6925443569093126 | 0.9586822031660596 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HMUVAR | logistic | temperature | bacc | 0.9834815279976 | 0.9680583528979532 | 0.992509247224373 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | ce_bits | 0.1307694336291982 | 0.0417572748158828 | 0.3013696828695573 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | J_bits | 0.8692305663708018 | 0.6986303171304427 | 0.9582427251841172 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HRFF | logistic | temperature | bacc | 0.9830103596423728 | 0.9666095776579676 | 0.9923931382615092 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | ce_bits | 0.1321577878818285 | 0.0415902283679843 | 0.3051090173768433 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | J_bits | 0.8678422121181715 | 0.6948909826231566 | 0.9584097716320157 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HRFF | logistic | temperature | bacc | 0.983332774319522 | 0.9670341643984582 | 0.9927025040171364 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | ce_bits | 0.1334939780290358 | 0.042435275662987 | 0.308003359855611 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | J_bits | 0.8665060219709642 | 0.691996640144389 | 0.957564724337013 | 57.0 | 未提供 |
| N2_post_ | L0 | P_bal | HVAR | logistic | temperature | bacc | 0.9830201750517834 | 0.9668084669698812 | 0.9923890800304124 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | ce_bits | 0.1312945219106828 | 0.0412310011283996 | 0.304178114537713 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | J_bits | 0.8687054780893172 | 0.6958218854622871 | 0.9587689988716004 | 57.0 | 未提供 |
| N2_pre_ | L0 | P_bal | HVAR | logistic | temperature | bacc | 0.9832572427526876 | 0.9673515786384538 | 0.9923024215384284 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.1316776394975503 | 0.0410395742365194 | 0.3054368325976156 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.8683223605024497 | 0.6945631674023844 | 0.9589604257634806 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.982883404569792 | 0.9665593462892385 | 0.9921385816004068 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | ce_bits | 0.134407589765505 | 0.0413365855448929 | 0.3125812626740535 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | J_bits | 0.865592410234495 | 0.6874187373259465 | 0.958663414455107 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMU | logistic | temperature | bacc | 0.9836186358260464 | 0.967613521893532 | 0.9926828539534892 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | ce_bits | 0.1320580278930576 | 0.0410060504229425 | 0.3068333380118441 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | J_bits | 0.8679419721069423 | 0.6931666619881559 | 0.9589939495770575 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMU | logistic | temperature | bacc | 0.9841883861379314 | 0.9685221065423956 | 0.9933261447658384 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | ce_bits | 0.1350723576089299 | 0.0415313357965784 | 0.3140234890055557 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | J_bits | 0.8649276423910701 | 0.6859765109944442 | 0.9584686642034216 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUMU | logistic | temperature | bacc | 0.983469959049359 | 0.9674214211017852 | 0.992569551594943 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | ce_bits | 0.13212559503386 | 0.0410556078261355 | 0.3070373351677106 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | J_bits | 0.86787440496614 | 0.6929626648322894 | 0.9589443921738645 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUMU | logistic | temperature | bacc | 0.9841883861379314 | 0.9685221065423956 | 0.9933261447658384 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.1359010936002679 | 0.0422932674356787 | 0.3156224299706782 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8640989063997321 | 0.6843775700293218 | 0.9577067325643213 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HMUVAR | logistic | temperature | bacc | 0.9830656469551166 | 0.9666221353137908 | 0.992446425306288 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | ce_bits | 0.1311481571495371 | 0.0403835811999361 | 0.3057230909544814 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | J_bits | 0.8688518428504629 | 0.6942769090455185 | 0.9596164188000639 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HMUVAR | logistic | temperature | bacc | 0.9836610096203868 | 0.967366387950882 | 0.9929724018991096 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | ce_bits | 0.1348756825174286 | 0.0416371466882159 | 0.3130001083109076 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | J_bits | 0.8651243174825713 | 0.6869998916890925 | 0.9583628533117841 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HRFF | logistic | temperature | bacc | 0.9826006393127968 | 0.966193766529442 | 0.9919441022041376 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | ce_bits | 0.1328186739499093 | 0.0410788115536551 | 0.3086402104088894 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | J_bits | 0.8671813260500907 | 0.6913597895911106 | 0.9589211884463449 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HRFF | logistic | temperature | bacc | 0.983328544225458 | 0.9668905980623914 | 0.9926815765461956 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | ce_bits | 0.1329928573584442 | 0.0418821556812007 | 0.3079558288299015 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | J_bits | 0.8670071426415558 | 0.6920441711700984 | 0.9581178443187993 | 57.0 | 未提供 |
| N2_post_ | R_SIM | P_bal | HVAR | logistic | temperature | bacc | 0.983523363968677 | 0.9670638910534302 | 0.993056263282231 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | ce_bits | 0.1309097021092248 | 0.0406278589431721 | 0.304516434500991 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | J_bits | 0.8690902978907752 | 0.695483565499009 | 0.9593721410568279 | 57.0 | 未提供 |
| N2_pre_ | R_SIM | P_bal | HVAR | logistic | temperature | bacc | 0.9826666579239624 | 0.965916054193232 | 0.9921916788620958 | 57.0 | 未提供 |

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

| control | population_id | readout_family | calibration | status | estimate | ci_lower | ci_upper | source_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frozen_implementation_contracts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | tests_010 |
| legacy_integrity_and_private_permissions | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | postflight_002 |
| complete_prespecified_primary_aggregates | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| prespecified_synthetic_execution_coverage | 未提供 | 未提供 | 未提供 | FAILED | 未提供 | 未提供 | 未提供 | synthetic_001 |
| prespecified_synthetic_direction_and_controls | 未提供 | 未提供 | 未提供 | MISSING | 未提供 | 未提供 | 未提供 | synthetic_001 |
| saved_training_OOF_family_selection | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| complete_required_head_families | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| declared_inner_OOF_calibration | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| selected_HB_minus_HBP | P_nat | training_OOF_selected | temperature | COMPLETE | 0.0001004002383222 | -0.0019035027100663 | 0.0021865901184356 | N3_core_001 |
| selected_H_minus_Hnoise | P_nat | training_OOF_selected | temperature | COMPLETE | -0.0519103031575786 | -0.0589538202026109 | -0.042284318799605 | N3_core_001 |
| fixed_history_strata_description | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | N3_core_001 |
| stratum_two_class_support_counts | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |
| fixed_prediction_metrics_and_influence | 未提供 | 未提供 | 未提供 | COMPLETE | 未提供 | 未提供 | 未提供 | metrics_001 |

全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。


预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：

| analysis_id | representation | population_id | model | readout_family | calibration | metric | estimate | ci_lower | ci_upper | n_candidates | n_records |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N3__ | L0 | P_bal | H | logistic | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | H | logistic | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | H | logistic | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | ce_bits | 0.9594781792065176 | 0.9548098853954118 | 0.9653309645546432 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | J_bits | 0.04052182079348243 | 0.03466903544535682 | 0.045190114604588216 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HB | logistic | temperature | bacc | 0.5906127296802212 | 0.5861591586282564 | 0.594923367810437 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | ce_bits | 0.9596257264577068 | 0.9546902513199162 | 0.9652037624627738 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | J_bits | 0.04037427354229317 | 0.03479623753722616 | 0.04530974868008375 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HBP | logistic | temperature | bacc | 0.5946131054356076 | 0.5895548264230801 | 0.5994201514100107 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | ce_bits | 0.957455431777726 | 0.9521341467673532 | 0.9635602520441472 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | J_bits | 0.04254456822227404 | 0.03643974795585281 | 0.047865853232646804 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | HP | logistic | temperature | bacc | 0.5948393998686197 | 0.5899790075852244 | 0.5995988556445804 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | ce_bits | 0.9581353341580426 | 0.95263145597115 | 0.9645524149651036 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | J_bits | 0.04186466584195736 | 0.03544758503489642 | 0.047368544028850046 | 60.0 | 未提供 |
| N3__ | L0 | P_bal | Hnoise | logistic | temperature | bacc | 0.5898682992236205 | 0.5827163389728793 | 0.5961327765634196 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | H | logistic | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | H | logistic | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HB | logistic | temperature | ce_bits | 0.817245398007364 | 0.8069177365847071 | 0.8254506676221782 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HB | logistic | temperature | bacc | 0.5071887769347464 | 0.505311345213348 | 0.5092968317290846 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HBP | logistic | temperature | ce_bits | 0.8174024758796351 | 0.8070252467472939 | 0.8258722939148332 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HBP | logistic | temperature | bacc | 0.5155237359207681 | 0.5118460053047513 | 0.5203236170571621 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HP | logistic | temperature | ce_bits | 0.8158266391511464 | 0.8054721981347824 | 0.8242202944513302 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | HP | logistic | temperature | bacc | 0.5117411913446529 | 0.5090988964934376 | 0.5143710465917004 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | Hnoise | logistic | temperature | ce_bits | 0.8163627099895986 | 0.8062500819668796 | 0.8246094733081969 | 60.0 | 未提供 |
| N3__ | L0 | P_nat | Hnoise | logistic | temperature | bacc | 0.5071206723857823 | 0.5054101383003804 | 0.5089134583111967 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | logistic | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | ce_bits | 0.961136904160612 | 0.9559179493301122 | 0.9674970843233752 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | J_bits | 0.03886309583938796 | 0.03250291567662478 | 0.044082050669887796 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | logistic | temperature | bacc | 0.5925004332998837 | 0.5877834208979628 | 0.5972252567493139 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | ce_bits | 0.9616525803629404 | 0.9562448701690088 | 0.9681115335233512 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | J_bits | 0.038347419637059565 | 0.03188846647664878 | 0.04375512983099117 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | logistic | temperature | bacc | 0.594954102671769 | 0.5891676064120173 | 0.6002408274742568 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | ce_bits | 0.9584800967944934 | 0.9528945750327632 | 0.9655649915492436 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | J_bits | 0.04151990320550658 | 0.03443500845075642 | 0.0471054249672368 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | logistic | temperature | bacc | 0.5970903432648306 | 0.5921455029565192 | 0.6020159544105882 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | ce_bits | 0.9590574492592449 | 0.9538913592891076 | 0.965244683194816 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | J_bits | 0.040942550740755146 | 0.034755316805183956 | 0.04610864071089238 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | logistic | temperature | bacc | 0.590808469393013 | 0.5845065811034045 | 0.5968722476871099 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | ce_bits | 0.7634127077121525 | 0.71496520572871 | 0.8322095244977264 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | J_bits | 0.23658729228784747 | 0.16779047550227355 | 0.28503479427128997 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | H | mlp32 | temperature | bacc | 0.7491621215379928 | 0.7328881299524258 | 0.7617516106535697 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | ce_bits | 0.98071550424745 | 0.9771154003941536 | 0.9852758942277372 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | J_bits | 0.01928449575254998 | 0.014724105772262797 | 0.022884599605846434 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HB | mlp32 | temperature | bacc | 0.5781743815125856 | 0.5717113890937201 | 0.5845016182965214 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | ce_bits | 0.9889090979802316 | 0.9866216387945071 | 0.9912627443054024 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | J_bits | 0.011090902019768367 | 0.008737255694597601 | 0.01337836120549285 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HBP | mlp32 | temperature | bacc | 0.5577720817141786 | 0.5505465222519733 | 0.5653407040901939 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | ce_bits | 0.9807829425728888 | 0.9777140591873787 | 0.9843162962180092 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | J_bits | 0.019217057427111217 | 0.0156837037819908 | 0.022285940812621252 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | HP | mlp32 | temperature | bacc | 0.5723844671367665 | 0.5637278426898478 | 0.5816728193459823 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | ce_bits | 0.9819504975739588 | 0.9791742573158436 | 0.985606820911018 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | J_bits | 0.018049502426041197 | 0.014393179088981967 | 0.02082574268415638 | 60.0 | 未提供 |
| N3__ | R_SIM | P_bal | Hnoise | mlp32 | temperature | bacc | 0.5723805597903717 | 0.5646191379670719 | 0.5802596557265891 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | logistic | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | logistic | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | logistic | temperature | ce_bits | 0.8183336119028356 | 0.8080351298861365 | 0.8264922818166528 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | logistic | temperature | bacc | 0.5062037016427512 | 0.504515825835739 | 0.5080331812623596 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | logistic | temperature | ce_bits | 0.8182332116645135 | 0.8082223110500023 | 0.8267001705724492 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | logistic | temperature | bacc | 0.5143077076225571 | 0.5114526612561212 | 0.5171656891130265 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | logistic | temperature | ce_bits | 0.8159380310265735 | 0.806076968120524 | 0.8241352544084134 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | logistic | temperature | bacc | 0.5107464232627433 | 0.5081261552350594 | 0.5132997869756438 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | logistic | temperature | ce_bits | 0.8172166754254823 | 0.8070427389482789 | 0.8252415261734305 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | logistic | temperature | bacc | 0.506953962486104 | 0.5051253708857694 | 0.508781347752491 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | mlp32 | temperature | ce_bits | 0.7653063722679035 | 0.7599001436075518 | 0.7703434872196671 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | H | mlp32 | temperature | bacc | 0.5693354908829352 | 0.564810266098376 | 0.5737795187167852 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | mlp32 | temperature | ce_bits | 0.8378239151811048 | 0.8308311079399191 | 0.8445236911967503 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HB | mlp32 | temperature | bacc | 0.5578068138122673 | 0.5518515341392685 | 0.5642683784624685 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | mlp32 | temperature | ce_bits | 0.8852904316463069 | 0.8790431525343563 | 0.8914296066435632 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HBP | mlp32 | temperature | bacc | 0.550752165913507 | 0.5441545312887309 | 0.557100526765441 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | mlp32 | temperature | ce_bits | 0.8430879627434601 | 0.8350892088379308 | 0.8500970444588017 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | HP | mlp32 | temperature | bacc | 0.5561701900484363 | 0.5508409256701596 | 0.5616705419331429 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | mlp32 | temperature | ce_bits | 0.8563722787669646 | 0.8505041517016553 | 0.8620271678477276 | 60.0 | 未提供 |
| N3__ | R_SIM | P_nat | Hnoise | mlp32 | temperature | bacc | 0.5543989275499076 | 0.5470829126321971 | 0.561172023869432 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | ce_bits | 0.95716464373869 | 0.9518673719708886 | 0.96384898706531 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | J_bits | 0.042835356261309965 | 0.03615101293469003 | 0.048132628029111446 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | H | training_OOF_selected | temperature | bacc | 0.5868926844577007 | 0.5816213572740079 | 0.5916559740504514 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | ce_bits | 0.9594781792065176 | 0.9548098853954118 | 0.9653309645546432 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | J_bits | 0.04052182079348243 | 0.03466903544535682 | 0.045190114604588216 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HB | training_OOF_selected | temperature | bacc | 0.5906127296802212 | 0.5861591586282564 | 0.594923367810437 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | ce_bits | 0.9596257264577068 | 0.9546902513199162 | 0.9652037624627738 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | J_bits | 0.04037427354229317 | 0.03479623753722616 | 0.04530974868008375 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HBP | training_OOF_selected | temperature | bacc | 0.5946131054356076 | 0.5895548264230801 | 0.5994201514100107 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | ce_bits | 0.957455431777726 | 0.9521341467673532 | 0.9635602520441472 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | J_bits | 0.04254456822227404 | 0.03643974795585281 | 0.047865853232646804 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | HP | training_OOF_selected | temperature | bacc | 0.5948393998686197 | 0.5899790075852244 | 0.5995988556445804 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | ce_bits | 0.9581353341580426 | 0.95263145597115 | 0.9645524149651036 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | J_bits | 0.04186466584195736 | 0.03544758503489642 | 0.047368544028850046 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_bal | Hnoise | training_OOF_selected | temperature | bacc | 0.5898682992236205 | 0.5827163389728793 | 0.5961327765634196 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | H | training_OOF_selected | temperature | ce_bits | 0.8157495346233741 | 0.8055410528208818 | 0.8238556030168733 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | H | training_OOF_selected | temperature | bacc | 0.5043256875553204 | 0.5035435325805954 | 0.5051683897578405 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HB | training_OOF_selected | temperature | ce_bits | 0.817245398007364 | 0.8069177365847071 | 0.8254506676221782 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HB | training_OOF_selected | temperature | bacc | 0.5071887769347464 | 0.505311345213348 | 0.5092968317290846 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HBP | training_OOF_selected | temperature | ce_bits | 0.8174024758796351 | 0.8070252467472939 | 0.8258722939148332 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HBP | training_OOF_selected | temperature | bacc | 0.5155237359207681 | 0.5118460053047513 | 0.5203236170571621 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HP | training_OOF_selected | temperature | ce_bits | 0.8158266391511464 | 0.8054721981347824 | 0.8242202944513302 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | HP | training_OOF_selected | temperature | bacc | 0.5117411913446529 | 0.5090988964934376 | 0.5143710465917004 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | Hnoise | training_OOF_selected | temperature | ce_bits | 0.8163627099895986 | 0.8062500819668796 | 0.8246094733081969 | 60.0 | 未提供 |
| N3_selected__ | L0 | P_nat | Hnoise | training_OOF_selected | temperature | bacc | 0.5071206723857823 | 0.5054101383003804 | 0.5089134583111967 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | ce_bits | 0.7634127077121525 | 0.71496520572871 | 0.8322095244977264 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | J_bits | 0.23658729228784747 | 0.16779047550227355 | 0.28503479427128997 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | H | training_OOF_selected | temperature | bacc | 0.7491621215379928 | 0.7328881299524258 | 0.7617516106535697 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | ce_bits | 0.961136904160612 | 0.9559179493301122 | 0.9674970843233752 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | J_bits | 0.03886309583938796 | 0.03250291567662478 | 0.044082050669887796 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HB | training_OOF_selected | temperature | bacc | 0.5925004332998837 | 0.5877834208979628 | 0.5972252567493139 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | ce_bits | 0.9616525803629404 | 0.9562448701690088 | 0.9681115335233512 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | J_bits | 0.038347419637059565 | 0.03188846647664878 | 0.04375512983099117 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HBP | training_OOF_selected | temperature | bacc | 0.594954102671769 | 0.5891676064120173 | 0.6002408274742568 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | ce_bits | 0.9584800967944934 | 0.9528945750327632 | 0.9655649915492436 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | J_bits | 0.04151990320550658 | 0.03443500845075642 | 0.0471054249672368 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | HP | training_OOF_selected | temperature | bacc | 0.5970903432648306 | 0.5921455029565192 | 0.6020159544105882 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | ce_bits | 0.9590574492592449 | 0.9538913592891076 | 0.965244683194816 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | J_bits | 0.040942550740755146 | 0.034755316805183956 | 0.04610864071089238 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_bal | Hnoise | training_OOF_selected | temperature | bacc | 0.590808469393013 | 0.5845065811034045 | 0.5968722476871099 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | H | training_OOF_selected | temperature | ce_bits | 0.7653063722679035 | 0.7599001436075518 | 0.7703434872196671 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | H | training_OOF_selected | temperature | bacc | 0.5693354908829352 | 0.564810266098376 | 0.5737795187167852 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HB | training_OOF_selected | temperature | ce_bits | 0.8183336119028356 | 0.8080351298861365 | 0.8264922818166528 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HB | training_OOF_selected | temperature | bacc | 0.5062037016427512 | 0.504515825835739 | 0.5080331812623596 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HBP | training_OOF_selected | temperature | ce_bits | 0.8182332116645135 | 0.8082223110500023 | 0.8267001705724492 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HBP | training_OOF_selected | temperature | bacc | 0.5143077076225571 | 0.5114526612561212 | 0.5171656891130265 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HP | training_OOF_selected | temperature | ce_bits | 0.8159380310265735 | 0.806076968120524 | 0.8241352544084134 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | HP | training_OOF_selected | temperature | bacc | 0.5107464232627433 | 0.5081261552350594 | 0.5132997869756438 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | Hnoise | training_OOF_selected | temperature | ce_bits | 0.8172166754254823 | 0.8070427389482789 | 0.8252415261734305 | 60.0 | 未提供 |
| N3_selected__ | R_SIM | P_nat | Hnoise | training_OOF_selected | temperature | bacc | 0.506953962486104 | 0.5051253708857694 | 0.508781347752491 | 60.0 | 未提供 |

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
| E0_R | E0R_core_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | NUMERICAL_FAILURE |
| SYNTHETIC | synthetic_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | NUMERICAL_FAILURE |
| FIT_AUDIT | fit_accounting_001 | source_summary_not_per_fit_count | 未提供 | 未提供 | 未提供 | PASS |
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
| ALL | fit_accounting_001 | independent_receipt_accounting | 7639 | 6829 | 20 | FIT_ACCOUNTING_PARTIAL |

§15.2逐fit字段覆盖来自独立fit_accounting，不由本报告补造；attempt与completed分开，transform另列，recovery reuse不是新head预算。没有原生记录的预测hash、校准scope、资源等字段保持缺失，源run层hash不冒充逐fit原生字段。

| field | attempted_units | present_count | missing_count | coverage_fraction |
| --- | --- | --- | --- | --- |
| fit_id | 7553 | 4016 | 3537 | 0.5317092546008209 |
| packet | 7553 | 0 | 7553 | 0.0 |
| mode | 7553 | 1218 | 6335 | 0.1612604263206672 |
| view | 7553 | 1974 | 5579 | 0.2613531047265987 |
| objective_id | 7553 | 3701 | 3852 | 0.4900039719316827 |
| optimizer_id | 7553 | 0 | 7553 | 0.0 |
| outer_fold | 7553 | 390 | 7163 | 0.0516351118760757 |
| inner_fold | 7553 | 360 | 7193 | 0.0476631801933006 |
| seed | 7553 | 3701 | 3852 | 0.4900039719316827 |
| training_scope_hash | 7553 | 4151 | 3402 | 0.5495829471733086 |
| input_hash | 7553 | 4859 | 2694 | 0.6433205348868 |
| feature_scope_hash | 7553 | 0 | 7553 | 0.0 |
| label_map_hash | 7553 | 0 | 7553 | 0.0 |
| weight_distribution | 7553 | 0 | 7553 | 0.0 |
| hyperparameter_source | 7553 | 0 | 7553 | 0.0 |
| calibration_scope_hash | 7553 | 0 | 7553 | 0.0 |
| n_train_candidates | 7553 | 0 | 7553 | 0.0 |
| n_train_trials_or_bags | 7553 | 0 | 7553 | 0.0 |
| n_eval_candidates | 7553 | 0 | 7553 | 0.0 |
| n_eval_trials_or_bags | 7553 | 0 | 7553 | 0.0 |
| step_count | 7553 | 3509 | 4044 | 0.4645836091619224 |
| final_train_loss | 7553 | 0 | 7553 | 0.0 |
| gradient_diagnostic | 7553 | 0 | 7553 | 0.0 |
| finite_parameters | 7553 | 0 | 7553 | 0.0 |
| optimizer_status | 7553 | 3701 | 3852 | 0.4900039719316827 |
| resource_usage | 7553 | 0 | 7553 | 0.0 |
| code_hash | 7553 | 7553 | 0 | 1.0 |
| config_hash | 7553 | 7553 | 0 | 1.0 |
| model_hash | 7553 | 0 | 7553 | 0.0 |
| prediction_hash | 7553 | 0 | 7553 | 0.0 |
| exception_class | 7553 | 0 | 7553 | 0.0 |
| failure_stage | 7553 | 0 | 7553 | 0.0 |

| metric | value | unit | status |
| --- | --- | --- | --- |
| jobs | 118 | count | ACCOUNTING_PARTIAL |
| accounted_jobs | 12 | count | ACCOUNTING_PARTIAL |
| missing_jobs | 106 | count | ACCOUNTING_PARTIAL |
| ongoing_jobs | 1 | count | ACCOUNTING_PARTIAL |
| actual_cpu_core_hours | 未提供 | CPU core hours | ACCOUNTING_PARTIAL |
| actual_gpu_hours | 未提供 | GPU hours | ACCOUNTING_PARTIAL |
| actual_cpu_core_hours_lower_bound | 未提供 | CPU core hours | ACCOUNTING_PARTIAL |
| actual_gpu_hours_lower_bound | 未提供 | GPU hours | ACCOUNTING_PARTIAL |
| reservation_upper_cpu_core_hours | 138.77277777777778 | CPU core hours | ACCOUNTING_PARTIAL |
| reservation_upper_gpu_hours | 13.713333333333333 | GPU hours | ACCOUNTING_PARTIAL |
| max_cpu_core_hours | 256.0 | CPU core hours | ACCOUNTING_PARTIAL |
| max_gpu_hours | 32.0 | GPU hours | ACCOUNTING_PARTIAL |
| cpu_actual_complete | False | 未提供 | ACCOUNTING_PARTIAL |
| gpu_actual_complete | False | 未提供 | ACCOUNTING_PARTIAL |
| cpu_lower_bound_complete | False | 未提供 | ACCOUNTING_PARTIAL |
| gpu_lower_bound_complete | False | 未提供 | ACCOUNTING_PARTIAL |
| upper_bound_complete | True | 未提供 | ACCOUNTING_PARTIAL |
| budget_status | WITHIN_CONSERVATIVE_BOUND | 未提供 | ACCOUNTING_PARTIAL |

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
| e0r | E0R_core_001 | INCOMPLETE_PRIMARY_MATRIX | NUMERICAL_FAILURE | 未提供 |
| synthetic | synthetic_001 | NUMERICAL_INCOMPLETE | NUMERICAL_FAILURE | 未提供 |
| metrics | metrics_001 | FIXED_PREDICTION_METRICS_COMPLETE | PASS | 未提供 |
| postflight | postflight_002 | PASS | PASS | 未提供 |
| resources | resources_002 | ACCOUNTING_PARTIAL | PASS | 未提供 |
| postflight_retained | postflight_001 | PERMISSION_ANOMALIES | BUG | 未提供 |
| fit_accounting | fit_accounting_001 | FIT_ACCOUNTING_PARTIAL | PASS | 未提供 |
| tests_supplement | tests_011 | PASS | PASS | 未提供 |

来源精确SHA256在source_hashes.csv的逻辑别名下；真实路径映射和异常细节仅保存在private。各packet图只画预设主比较及必要对照的总体点和完整区间，不画个体点，不隐藏负值；缺输入不绘制零值替代图。

旧结论保持冻结，本轮没有新的临床终点或B/D重新选型。固定来源为Auditory5的S4_final_001/metrics_aggregate.csv及AUDITORY5_FINAL_STATUS_v1.md。旧B完整控制后的R_SIM条件历史增益为−0.002169 bits/trial（60个候选组），未达到原0.01 bits门槛；旧D的R_SIM临床增量为0.108730源量表分，95%区间[−0.142199,0.387963]（51个候选组），未达到原0.5源量表单位门槛。这些是已有阴性筛查，不能由本轮新N3估计对象改写。旧C/E数值失败不是科学阴性，修复前后源回执均保留。

E1跨任务迁移保持关闭：原bapa安全候选支持16，低于20；E0记录内目标可读性不替代E1。MFF来源混合，不能整体称CI样本。本轮已见数据下的探索不能把已有候选重新描述为未触碰外部验证。

下一步只可针对已缺证据推进：A2须限制共享背景预测项解释；C2-R须先完成预定整族与继承隔离控制；N1/N3须解释先验、pre和容量代价；N2须在相同bag预算与共同队列验证分布增量。已完成且增量阴性的具体估计器不因改名或扩大网络重新成为原假设的确认性检验。

重新启动旧B需要新的证据证明固定历史对象有可靠、超出刺激与序列先验的可读增量；本轮N3改变了目标，不能充当旧B复现。重新启动旧D需要先获得可靠且解释明确的EEG测量对象，并解决量表单位和同期性，再冻结临床增量检验及独立评价队列。当前结果不否定所有历史效应或EEG临床信息，但不授权继续旧阈值、null空间和临床终点搜索。
