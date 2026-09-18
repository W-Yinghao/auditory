> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../../PUBLICATION.md)。

# N2R_001 结果记录

本记录依据公开的 `N2R_metrics.csv`、`N2R_paired_effects.csv`、`summary.json` 及 `capability_N2R_001/summary.json`。这是 `P_MATCH_bal` 探索性队列上的算法结果，不是形式化临床注册或在线部署评估。风险单位为 bits/bag；共有 49 个身份组、698 个 bag，五个外折，550/550 计划头完成。

## 主终点

预设主比较为 `HQ_minus_HQV`，符号为 `CE(HQ) − CE(HQV)`。结果为 **−0.000843949 bits/bag**，95% 固定 OOF identity bootstrap CI 为 **[−0.008416885, 0.006606403]**，49 个身份组中正差异比例为 0.469。对应 CE 为 HQ **1.009895**、HQV **1.010739** bits/bag；HQV 点估计略差，区间跨零，不能建立方差视图的受控增益。summary 的研究状态为 `NO_CONTROLLED_GAIN_ESTABLISHED`。

## 预定控制与敏感性

相对无 EEG 元数据基线的 `H_minus_HQV` 为 **−0.015340**，CI **[−0.042425, 0.011314]**，因此 HQV 也没有相对 H 的明确优势。`HQQ_minus_HQV` 与主终点相同，为 **−0.000843949**，CI **[−0.008416884, 0.006606403]**；`HQQ_minus_HQ` 为约 **6.8×10⁻¹⁷**，CI 跨零，支持重复二次均值列的数值等价。pre 条件对照 `HPREQ_minus_HPREQV` 为 **0.000830**，CI **[−0.006919, 0.008181]**；次要 `HM_minus_HMV` 为 **−0.005194**，CI **[−0.011846, 0.001348]**，均不支持稳定增量。

FULL400 敏感性同样不能替换主结果。`FULL_MU` CE 为 **1.039030**，`FULL_MU_VAR` CE 为 **1.141758**；`FULL_MU_minus_FULL_MU_VAR` 为 **−0.102728**，CI **[−0.146315, −0.059988]**，表示该固定全维均值加对角方差读出在本队列中 CE 更高。它是有限的 400D 敏感性结果，不排除其它分布表征，也不等同于互信息结论。

## 门控、能力与限制

N2R summary 显示 `execution=COMPLETE`、`support=PASS`、所有 550 个头完整；能力包单独为 PASS：`VAR_EXTRA` 强信号恢复 20/20，`MEAN_SUFFICIENT` 与 `HISTORY_ONLY` 的 null screen 均为 0/20。能力结果只说明冻结算法在有限合成机制上的检查通过，不证明真实效应或普遍假阳性率。

所有 CI 使用 seed 63017、2,000 次、按身份并在原外折内抽样的 fixed-OOF bootstrap，未重新拟合流水线；因此推断范围受该设计限制。bag 为已知刺激类别构造的固定 k=8 重复袋，结果不能直接外推到在线装袋、未知类别或临床部署。
