> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Phase 2 产物与复现

主解释见 [phase2_report.md](phase2_report.md)，运行前方案见 [PHASE2_PROTOCOL.md](PHASE2_PROTOCOL.md)。所有结果仅为服务器内研究产物，不是对外发布的数据集。不透明候选 ID 仍属于可连接的假名化信息。

固定配置 [phase2_v1.json](../configs/phase2_v1.json)，SHA256：`b2c30fb1f95fe20d18b0907415c540b6c3628f353993b6bfaa248938af2637e4`。继承 Phase 1 原 epoch，无原始文件改写。

| 当前产物 | 内容 | Slurm |
|---|---|---:|
| cohort_001（服务器产物：`../results/phase2_cohort_001/`） | 全 93 条来源的最早候选人索引、DOB/日期/链接状态、临床可用性汇总 | 995465 |
| [measurements_001](../results/phase2_measurements_001/) | 80,441 行 epoch 敏感性账本、全记录/半份分数、ICC、块误差和参考敏感性 | 995467 |
| [archival_001](../results/phase2_archival_001/) | 候选人流向、20×5 折记录、53 个 HA 候选模型聚合结果 | 995468 |
| final_001（服务器产物：`../results/phase2_final_001/`） | 独立对账、模型指标复核、28 项哈希、紧凑候选人支持表 | 995474 |
| [diagnostics_001](../results/phase2_diagnostics_001/) | 图后追加的留一影响诊断，不改变候选集合或模型 | 995478 |
| delivery_001（服务器产物：`../results/phase2_delivery_001/`） | 最终文档链接、图表及交付哈希核验 | 见其 verification.json |

检查入口 [21_phase2_checks.sbatch](../slurm/21_phase2_checks.sbatch)，最新测试作业 995464：19 项通过。初次 17 项测试为 995458，语法检查 995463。生产入口按 22–26 编号顺序，完整参数在 scripts 和配置快照中；生产脚本拒绝覆盖已有目录。重新运行须指定新版本/输出目录，不能直接覆盖已完成作业。

交付检查首次作业 995486 在导入缺失的 `pypdf` 时退出，尚未创建结果；随后改用本环境已有且 Phase 1 已使用的 `pdfminer` 检查 PDF，不安装新依赖、不重跑分析。

## 数值文件含义

- `cohort_001/index_recordings.csv` 覆盖全部 93 条来源。`index_recording_flag` 为最早排序位置；`eligible_measurement_identity_index` 还需完整可解析时间、无 DOB 冲突和来源技术合格。`strong_unique_link` 仅表示唯一姓名＋标签日期证据，不确证同期。
- `measurements_001/epoch_sensitivity_ledger.csv` 对每个存储 epoch 保留源事件序号、原采样位置、数字码、额枕差峰峰值和三个保留标记。主拒绝试次仍在表中；没有数据行代表独立儿童。9 个来源隔离记录无重建 epoch，仍在 source 和 index 表内。
- `features.csv` 为五个方案×三条件的全记录固定窗均值。`measurement_status=measured` 要求双码试次和时间块支持；`selected_index` 只说明候选最早索引技术可选，不自动说明均值可用。
- `half_scores.csv` 保存两种时间划分×原全部合格/每码两半平衡两种抽样。首尾中点取所有存储目标事件，固定于筛选之前。不同参考方案使用主试次和同随机子集；严格阈值方案具有各自子集。这里“平衡”指同一代码在两半的试次数相等，code 1 与 code 2 的数量不必相等。
- `amplitude_agreement.csv` 中 `variant_available` 是各方案自身支持，`all_variants_common` 是五方案都可评分的同一候选集合。ICC 可为负，少于八个候选不估计；各指标有效 bootstrap 少于 95% 不给区间。两半来自同次采集，不能当重测。
- `paired_processing_sensitivity.csv` 比较同一候选的全记录主方案与处理变体。`matched_trials=True` 仅用于 0.5 Hz 和 18 通道参考；另外两个方案删了不同试次。
- `block_uncertainty.csv` 为同试次 30/60/90 s 联合块 bootstrap。主测量协议没有用此处某个更小 SE 重新选参数。
- `archival_001/candidate_eligibility.csv` 覆盖所有来源，排除理由可重叠；不能把多标签排除数直接相加。`candidate_folds.csv` 包含每个候选每次重复唯一的测试折，同一个表用于四模型。模型原始分数和每人预测仅在 private。
- `diagnostics_001/leave_one_candidate_out.csv` 为查看散点图后追加的影响诊断，不是新的排除规则；主 ICC 和临床模型未变。

## 图表与私有来源

[半份幅值图](../figures/phase2_measurements_001/half_amplitude_agreement.png)、[共同候选敏感性图](../figures/phase2_measurements_001/common_support_sensitivity.png)、[模型比较 PNG](../figures/phase2_diagnostics_001/archival_feasibility.png)和[模型比较 PDF](../figures/phase2_diagnostics_001/archival_feasibility.pdf)。`figures/phase2_archival_001/` 首次图标题被裁切，保留作历史产物；报告引用单独重绘版本，统计不变。

`private/phase2_cohort_001/linked_index.csv` 包含实际 vendor 时间/DOB、临床行号、临床年龄、使用月数、MUSS、年龄差及链接状态。`private/phase2_archival_001/` 包含完整病例流向和每候选每模型每重复的预测。父目录 0700，源姓名和文件路径仍在既有 private 审计文件，不复制到公开结果表。所有目录仍仅在本服务器，未向外部发送。
