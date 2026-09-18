> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../../PUBLICATION.md)。

# P0_001 结果记录

本记录依据公开的 `P0_metrics.csv`、`P0_paired_effects.csv` 和 `summary.json`，对应冻结的 P0 `R_SIM` 主表示、post 窗口、`lambda=0.01`。P0 的风险单位是 bits/trial；本包使用 49 个身份组、5 个外折、5,584 个观测，计划与实际头数均为 260，算法哈希为 `ea6973f767102ea2c41525093536c3e9f73c81d8a69a74d8a14395a1b8fef089`。

## 预先冻结的主比较

主对比为 `R_SIM__post__lambda0.01__PC8_minus_FULL`。代码中的对比符号是

`gain = CE(PC8) - CE(FULL)`。

因此结果为 **−0.001750 bits/trial**，95% identity bootstrap CI 为 **[−0.007433, 0.003619]**，49 个身份组中正值比例为 0.408。对应的总体 CE 为 PC8 **0.999557**、FULL **1.001306** bits/trial；PC8 的点估计 CE 略低，但区间跨零，不能建立可重复的压缩惩罚或 FULL 优势。该主比较的记录状态为 PASS，含义是估计完整并成功保存，不表示科学阳性。

## 控制与边界

`PC8_DUP_minus_PC8` 为约 **−1.36×10⁻¹⁷** bits/trial，CI 为 **[−3.63×10⁻¹⁷, 9.06×10⁻¹⁸]**，支持重复列的数值等价。`REST_minus_FULL` 为 **0.000574**，CI 为 **[−0.000909, 0.002082]**，同样跨零。pre 诊断的 `PC8_minus_FULL` 为 **−0.007398**，CI 为 **[−0.010848, −0.003582]**；其窗口长度与 post 不同，报告中明确标注为诊断，不能替代主 post 比较。L0、R_SUP、R_RAND 以及其它 lambda 结果保留为背景和敏感性信息，不能挑选来改写主结论。

FULL 的 `R_SIM` post CE 为 1.001306、bAcc 0.5251、AUC 0.5356；PC8 CE 为 0.999557、bAcc 0.5155、AUC 0.5162。数值控制均通过，包含 FULL 正交运输和 PC8_DUP 等价性；没有将这些控制当作新的主终点。

## 门控状态与结论

`execution=COMPLETE`、`support=PASS`、`capability=PASS`，且没有 incomplete model key。独立 P0 能力包为 PASS：低方差机制恢复 5/5、TOP-PCA 机制恢复 5/5，15 个能力世界和 30 个能力头均完成；这只证明预定算法检查通过，不是现实数据效果证据。科学研究状态为 **NO_DETECTABLE_COMPRESSION_PENALTY**：在冻结主比较中，CI 跨零，未建立 PC8 相对 FULL 的明确性能代价，也未建立新的临床或神经科学结论。
