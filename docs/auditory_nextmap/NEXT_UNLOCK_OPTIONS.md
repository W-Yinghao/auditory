# 下一次训练的任务卡（B1，`b1_001`）

这些任务卡只是方案，**不自动执行**。凡是需要 GPU 训练的，都要另写训练规格并经你批准。完整字段见 `results/auditory_nextmap/b1_001/summary_b1.json`。

| 任务卡 | 研究问题 | 支持 | 状态 | 卡在哪里 |
|---|---|---|---|---|
| `B1_pair_puretone` | 恢复出的纯音对（1000 vs 1500 Hz；1k vs 2k）在记录内能否判别 | 6 条连续记录，全部已导出 D1，全部是 LINKED | NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT | 6 条的身份都未解决；声音对与记录完全混淆；2 条进入过 GX2 自监督 |
| `B1_pair_bapa` | ba vs pa | 1 条 | NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT | 同上，且只有 1 条 |
| `B1_pair_ba1ba4` | ba vs ba4（声调） | 1 条（加上规范来源原有的 1 条） | NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT | 支持过少，不能做跨儿童统计 |
| `B1_protocol_conditioned_sharing` | 在 MFF 已知协议上，共享编码器 + 协议头，是否优于目标单训和朴素混训 | 规范车道：纯音 41 条/37 名、bapa 29 条/27 名；身份图 111 组 | DEFERRED_NEW_TRAINING_SPEC_REQUIRED | 需要新训练规格（同一批测试儿童、同样的标签与优化预算）。这些记录已被 GX 用过，只能算探索性再用，不是验证 |
| `B1_frozen_age_evaluation_new_samples` | 用净新增、未曝光的儿童评价冻结的年龄模型 | 净新增身份 1 名（有年龄，但进入过自监督）；SET 净新增 0 | NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT | 没有"未曝光且有年龄"的新儿童 |
| `B1_bdf_clock_held_records` | 恢复 9 条时钟待定的 BDF 记录 | 9 条（都是已有儿童） | SOURCE_UNRESOLVED | 头文件只有整秒精度，没有亚秒信息；需要另行预定的支持集/查询集验证方案 |

另外，A 线可以考虑两张卡。它们不在 B1 的范围内，详见 `AGE_INFORMATION_SOURCE_REPORT.md` §5：

- **A_equal_capacity_readout**：在同等读出容量下，比较平均波形与逐试次特征承载的年龄信息（例如同一 EEGNet 架构直接以年龄为目标），把"读出容量"和"表示来源"分开。需要 GPU 训练。
- **A_cross_system**：在 MFF 上复现"事件锁定的共同响应携带年龄"。需要先有更好的 MFF 事件编码器，或者改用同等容量的年龄目标学习。
