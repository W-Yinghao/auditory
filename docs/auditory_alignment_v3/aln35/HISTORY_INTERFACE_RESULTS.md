# ALN3.5 private history 接口与严格异 block twin

CPU Slurm 1047305，2026-10-19T03:52:23.969603+02:00；20/20 个 frozen source，64 儿童，seed 3401。

这次等校准读出没有把 AP 的正 log-score gain 吸收为 history 截距修正：完整 query 上 B1−B0 为 −0.000312 bits/trial，AP 的 EEG−B1 为 +0.002314，严格异 block twin 对照为 +0.003470。J* 和 XM 的 EEG−B1 描述均值也为正，S 为负；q0 内区间中 XM 的 EEG−B1 转为负。它们是这组固定表征和源端拟合的有限比较，尚不是带群体不确定性的新显著性结论。

独立核验 CPU 1047311 PASS：100 个来源文件与缓存不变；四 arm 的真实 query、source-ES 和 twin hash 完全一致，B0/B1 数值也完全一致。64 儿童共 56,426 trial 全部有严格异 block twin，33,260 trial 位于 q0 的 (0.01,0.99) 区间；原 swap 实际同 block 回退和 self twin 均为 0。这说明本面板的严格 twin 效果不能归咎于这些回退，但仍是固定 seed 的描述结果。

100 个读出拟合均满足收敛条件，34 次按预定源端梯度规则重试，最大绝对梯度/源行数为 9.986e−8。新执行用 float64 特征与同 source-ES 行标准化，并加严优化终止条件；相对保留的旧 full-query 值，每儿童最大绝对差为 9.31e−5 bits/trial，四 arm 的平均有符号差均小于 2.9e−6。结果哈希及完整核验记录见 `results/auditory_alignment_v3/aln35/history/run_1047305/verification_receipt.json`。

没有重训或前向运行 encoder；复用 prior_science 的 full 特征。B1 为与 EEG 同一 source-ES 行拟合的单截距 history-only 校准；EEG 与 strict twin 使用原 C=1、有截距的 offset logistic 目标，新数值执行保存优化终止及梯度证据。

严格 twin 仅由同儿童、同 history bin、异物理 block 的非自身 trial 组成；source 拟合两端都限制为 source-ES。无合法 twin 的 trial 保留为显式缺项；完整 query 与严格交集、q0 在 (0.01,0.99) 子集分别报告。以下为等儿童描述均值，不补造新的显著性 family。

| Arm | 拟合/评价范围 | Query 子集 | 人数 | B1−B0 bits/trial | EEG−B0 | EEG−B1 | EEG−strict twin |
|---|---|---|---:|---:|---:|---:|---:|
| S | full_query | all_queries | 64 | -0.000312 | -0.001788 | -0.001476 | NA |
| S | full_query | q0_common_support | 64 | -0.001491 | -0.004456 | -0.002965 | NA |
| S | strict_other_block | all_queries | 64 | -0.000314 | -0.001787 | -0.001473 | +0.002867 |
| S | strict_other_block | q0_common_support | 64 | -0.001494 | -0.004455 | -0.002960 | +0.004456 |
| AP | full_query | all_queries | 64 | -0.000312 | +0.002002 | +0.002314 | NA |
| AP | full_query | q0_common_support | 64 | -0.001491 | +0.001394 | +0.002885 | NA |
| AP | strict_other_block | all_queries | 64 | -0.000314 | +0.002003 | +0.002317 | +0.003470 |
| AP | strict_other_block | q0_common_support | 64 | -0.001494 | +0.001396 | +0.002890 | +0.004536 |
| J* | full_query | all_queries | 64 | -0.000312 | +0.000616 | +0.000928 | NA |
| J* | full_query | q0_common_support | 64 | -0.001491 | -0.000803 | +0.000687 | NA |
| J* | strict_other_block | all_queries | 64 | -0.000314 | +0.000615 | +0.000929 | +0.003106 |
| J* | strict_other_block | q0_common_support | 64 | -0.001494 | -0.000806 | +0.000689 | +0.003653 |
| XM | full_query | all_queries | 64 | -0.000312 | +0.000183 | +0.000495 | NA |
| XM | full_query | q0_common_support | 64 | -0.001491 | -0.001867 | -0.000376 | NA |
| XM | strict_other_block | all_queries | 64 | -0.000314 | +0.000182 | +0.000496 | +0.002746 |
| XM | strict_other_block | q0_common_support | 64 | -0.001494 | -0.001870 | -0.000375 | +0.003464 |

每儿童完整/严格 trial、standard/deviant、history bin、common-support、原 twin 的同 block/self 回退，以及每 fold 的 source-ES 类别计数、row/twin-map hashes、拟合终止状态均在同目录 unit JSON。旧 full-query 原值和新收敛验证重拟合差额一并保留；外层 query 结果不触发重试或选择。

如果 EEG−B0 主要由 B1−B0 吸收，概率背景修正是竞争解释；EEG−B1 与严格 twin 的剩余表现则继续约束表征解释。这里不将 log-score gain 写作精确条件互信息或临床获益。
