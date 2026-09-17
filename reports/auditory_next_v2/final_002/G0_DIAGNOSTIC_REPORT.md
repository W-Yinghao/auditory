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