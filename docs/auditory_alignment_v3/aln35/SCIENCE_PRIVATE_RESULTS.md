# ALN3.5：成对科学分析与原主端点组差

现有结果支持继续研究声音结构的共享和读出：CB 真全量模型在 DTU 与 FAU 的 history 残差包络读取上优于同访问 local；私有先验的 AP 相对 XM 在线性 probe 上增加 AUC 0.00919（同时区间 [0.00061, 0.01777]，64 儿童、seed 3401）。这些差异限定于具体训练包和读出，正确声音配对的特异性仍需 APwrong 区分。

时间读出对相对位置敏感：DTU/FAU 固定读出从 0 移到 600 ms 后相关下降，在新位置重拟合读出能恢复部分表现。该比较始终包含完整一秒 EEG 访问，说明读取关系的位置依赖，不能定位单点神经潜伏期。原主方法中，FAU 的 HA 相对 CI 获得更大的 AP−S 风险改善；私有儿童的 HA−NH 改善差仍不确定。所有指定的弱结果和不确定结果均保留在下表。

计算：2026-10-19T03:49:08.195312+02:00，Slurm CPU 1047290。基准提交 `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`。

本轮复用已完成表征和原主方法输出；不新增训练，也不按外层结果挑选人、seed、窗口或方法。
以下全部为 `exploratory_after_2026_10_18_review`。10 个科学 family 的 30 项对比与 3 个原主端点 family 的 10 项对比分开报告；原注册 bootstrap-t 统计仍保留在原 ALN3.4 报告中。

每个 family 先在同一人的完整内容重复内求均值，再平均所需 seeds，最后以人为抽样单位。新区间采用包中原样的 4,000 次 bootstrap、固定原始 SE 的 max-|z*|；不是旧 bootstrap-t，也不是独立区间相减。

| Family | 端点 | 完整 / 预期人数（按组） | 状态 |
|---|---|---|---|
| SCI35_PRIVATE_PRIOR_NCE_AUC4 | AUC | all: 64/64 | regular |
| SCI35_PRIVATE_PRIOR_NCE_HISTORY2 | bits/trial | all: 64/64 | regular |
| SCI35_PRIVATE_PRIOR_NCE_TWIN2 | bits/trial | all: 64/64 | regular |
| SCI35_PRIVATE_HA_NH_PRIOR_EFFECT2 | AUC | HA: 55/55, NH: 9/9 | regular |
| SCI35_FAU_PRIOR_GROUP_EFFECT2 | Pearson_r | ci: 24/24, ha: 29/29, th: 14/14 | regular |
| SCI35_DTU_NATIVE_CONTENT6 | Pearson_r | all: 44/44 | regular |
| SCI35_FAU_NATIVE_CONTENT6 | Pearson_r | all: 67/67 | regular |
| SCI35_FEDERICI_NATIVE_ENV2 | Pearson_r | all: 86/86 | regular |
| SCI35_DTU_NATIVE_TEMPORAL_MAP2 | Pearson_r | all: 44/44 | regular |
| SCI35_FAU_NATIVE_TEMPORAL_MAP2 | Pearson_r | all: 67/67 | regular |
| S35_MAIN_FAU_APS_GROUP | bits/5s_query | ci: 24/24, ha: 29/29, th: 14/14 | regular |
| S35_MAIN_FAU_TF_GROUP | bits/5s_query | ci: 24/24, ha: 29/29, th: 14/14 | regular |
| S35_MAIN_PRIVATE_APS_GROUP | AUC | HA: 55/55, NH: 9/9 | regular |

| Family / contrast | 估计 | 同 family 同时 95% 区间 |
|---|---:|---|
| SCI35_PRIVATE_PRIOR_NCE_AUC4 / AP_minus_XM_full | +0.009193 | [+0.000611, +0.017774] |
| SCI35_PRIVATE_PRIOR_NCE_AUC4 / Jstar_minus_XM_full | +0.004844 | [-0.003059, +0.012747] |
| SCI35_PRIVATE_PRIOR_NCE_AUC4 / AP_early_minus_late | +0.020690 | [+0.002405, +0.038975] |
| SCI35_PRIVATE_PRIOR_NCE_AUC4 / AP_mid_minus_late | +0.021410 | [+0.007173, +0.035647] |
| SCI35_PRIVATE_PRIOR_NCE_HISTORY2 / AP_minus_XM_full | +0.001817 | [+0.000521, +0.003113] |
| SCI35_PRIVATE_PRIOR_NCE_HISTORY2 / Jstar_minus_XM_full | +0.000430 | [-0.000988, +0.001847] |
| SCI35_PRIVATE_PRIOR_NCE_TWIN2 / AP_minus_XM_full | +0.001151 | [-0.000152, +0.002453] |
| SCI35_PRIVATE_PRIOR_NCE_TWIN2 / Jstar_minus_XM_full | +0.000606 | [-0.000797, +0.002008] |
| SCI35_PRIVATE_HA_NH_PRIOR_EFFECT2 / HA_minus_NH_AP_minus_XM | -0.010249 | [-0.031695, +0.011196] |
| SCI35_PRIVATE_HA_NH_PRIOR_EFFECT2 / HA_minus_NH_Jstar_minus_XM | +0.006512 | [-0.007833, +0.020857] |
| SCI35_FAU_PRIOR_GROUP_EFFECT2 / HA_minus_TH_AP_minus_XM_history_r | +0.014616 | [+0.003374, +0.025858] |
| SCI35_FAU_PRIOR_GROUP_EFFECT2 / CI_minus_TH_AP_minus_XM_history_r | +0.004720 | [-0.010759, +0.020198] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_CBrand_env_history | +0.015250 | [+0.007849, +0.022651] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_env_history | +0.008995 | [+0.000566, +0.017424] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_CBrand_spec | +0.005014 | [+0.001852, +0.008176] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_spec | +0.003998 | [+0.000058, +0.007938] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_CBrand_flux | +0.009188 | [+0.003046, +0.015330] |
| SCI35_DTU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_flux | +0.004303 | [-0.004434, +0.013040] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_CBrand_env_history | +0.015572 | [+0.008167, +0.022976] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_env_history | +0.011993 | [+0.004213, +0.019772] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_CBrand_spec | +0.002456 | [-0.000305, +0.005217] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_spec | +0.003951 | [-0.000402, +0.008303] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_CBrand_flux | +0.001506 | [-0.004671, +0.007684] |
| SCI35_FAU_NATIVE_CONTENT6 / CBpre_minus_LOCAL_flux | +0.003703 | [-0.002948, +0.010354] |
| SCI35_FEDERICI_NATIVE_ENV2 / CBpre_minus_CBrand_env_history | +0.008481 | [-0.008420, +0.025383] |
| SCI35_FEDERICI_NATIVE_ENV2 / CBpre_minus_LOCAL_env_history | +0.015933 | [-0.004127, +0.035992] |
| SCI35_DTU_NATIVE_TEMPORAL_MAP2 / aligned_readout_loss_at_shift600 | +0.222192 | [+0.198404, +0.245981] |
| SCI35_DTU_NATIVE_TEMPORAL_MAP2 / readout_refit_recovery_at_shift600 | +0.136274 | [+0.116821, +0.155726] |
| SCI35_FAU_NATIVE_TEMPORAL_MAP2 / aligned_readout_loss_at_shift600 | +0.098419 | [+0.082740, +0.114097] |
| SCI35_FAU_NATIVE_TEMPORAL_MAP2 / readout_refit_recovery_at_shift600 | +0.030371 | [+0.018333, +0.042408] |
| S35_MAIN_FAU_APS_GROUP / ha_minus_ci_S_minus_AP | +0.098640 | [+0.021786, +0.175495] |
| S35_MAIN_FAU_APS_GROUP / ha_minus_th_S_minus_AP | +0.034963 | [-0.032208, +0.102135] |
| S35_MAIN_FAU_APS_GROUP / ci_minus_th_S_minus_AP | -0.063677 | [-0.151954, +0.024600] |
| S35_MAIN_FAU_TF_GROUP / ha_minus_ci_LOCAL_minus_CBpre | +0.117080 | [+0.022389, +0.211772] |
| S35_MAIN_FAU_TF_GROUP / ha_minus_th_LOCAL_minus_CBpre | +0.049281 | [-0.049579, +0.148142] |
| S35_MAIN_FAU_TF_GROUP / ci_minus_th_LOCAL_minus_CBpre | -0.067799 | [-0.191965, +0.056367] |
| S35_MAIN_FAU_TF_GROUP / ha_minus_ci_CBrand_minus_CBpre | +0.074187 | [-0.004949, +0.153323] |
| S35_MAIN_FAU_TF_GROUP / ha_minus_th_CBrand_minus_CBpre | +0.017866 | [-0.050836, +0.086568] |
| S35_MAIN_FAU_TF_GROUP / ci_minus_th_CBrand_minus_CBpre | -0.056321 | [-0.147702, +0.035061] |
| S35_MAIN_PRIVATE_APS_GROUP / HA_minus_NH_AP_minus_S | +0.001126 | [-0.008397, +0.010649] |

原主 FAU 风险改善按 reference − candidate（bits/5 s query），私有原主 AUC 按 AP − S；组差按名称的第一组减第二组。科学 probe 的 r/AUC 与原主端点不混合。

SCI35-C01：native E_LOCAL / E_PUBLIC_TRANSFER 的 pre 输入实际全零，故标为 `all_zero_input_control_no_pre_access`，不作刺激前 EEG 证据。其余后刺激、full、个人适配、FM 真正 pre 以及新 prior 科学输出保留。详见 `CORRECTION_PRIVATE_PRE_ACCESS.md`。

AP−XM 是两种特定先验训练包的差异，尚不是正确声音配对的纯消融；APwrong 为独立待绑定对照。时间对比保留完整一秒访问窗，600 ms 指相对读出位置，不是单点神经潜伏期。HA/CI/NH 直接效应差来自独立组人级抽样，不是治疗效应。

完整 per-family 参数、实际缺项、来源哈希、个体 contrasts 及原主统计引用见 `results/auditory_alignment_v3/aln35/science/`。含真实 query 索引的规范行和原始 metadata provenance 留在 `private/auditory_alignment_v3/aln35/science/`，本轮未推送 GitHub。

下一步的竞争解释是声音配对特异性、history 概率接口，以及有限个人支持的覆盖和适配强度。匹配 APwrong 将区分 AP 的配对作用与一般训练包差异；同 source-ES 校准的 history-only 和严格异 block twin 将区分表征增量与背景概率修正；固定 query 的 support 覆盖实验则检验已有适配伤害的来源。已完成的科学模型不为这些解释重训。
