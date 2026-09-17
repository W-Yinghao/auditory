# 儿童听觉 EEG：数据审计与科学探索

本仓库保存面向 IEEE JBHI 同级期刊研究的 **Phase 0–3、Auditory5、auditory_next v2 和 v2.1 的代码、方案、报告、汇总结果和图表**。v2.1 条件计划与最终验收已完成，保留阴性、支持不足、数值失败和缺少对照；尚未形成可投稿论文或经验证的临床模型。原始 EEG、身份映射、逐人临床信息、逐 epoch 数据、个体预测和模型权重不在仓库中。

从 [v2.1 科学结果](docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md)、[路线决策](docs/auditory_v21/ROUTE_DECISIONS_v2_1.md)和[最终验收](reports/auditory_v21/final_001/FINAL_REPORT_CN.md)开始阅读；前轮见 [v2 报告](reports/auditory_next_v2/final_002/NEXT_ROUND_REPORT.md)和 [Auditory5 报告](reports/auditory5_v1/S4_final_001/FIVE_IDEAS_SCREENING_REPORT.md)，前期依据见 [Phase 3 报告](docs/phase3_report.md)与[原项目目标映射](docs/ORIGINAL_IDEA_EVIDENCE_MAP.md)。数据来源包含 HA、CI/CIHA 字面标签及大量组别未知记录；文件数、处理版本和 epoch 数不能当作独立儿童数。

## v2.1：能力门控后的真实比较

新有限预算读出器先完成独立能力评估 **880/880 世界**，N1/N3 × R_SIM/L0 四条路线均通过冻结门槛，再完成全部 20 个真实外折、130 个 EEG 读出头。它保留基线候选，不是旧 MLP 求解器修复；强合成信号通过也不保证微小效应可检出。真实结果均为 `NO_CONTROLLED_INCREMENT_ESTABLISHED`。

| 比较 | 风险增益及 95% 区间（bits/trial） | 解释 |
|---|---|---|
| N1 R_SIM：HP → HPB | 0.000348 [−0.000200, 0.001120] | 59 身份组；反方向及噪声/复制对照也未建立受控增益 |
| N1 L0：HP → HPB | 0.000114 [−0.000225, 0.000432] | 次要表征，控制比较区间跨零 |
| N3 R_SIM：H → HP | 0 [0, 0] | 60 身份组；五折均选择历史基线，不能推断总体条件信息为零 |
| N3 L0：H → HP | −0.000710 [−0.001386, −0.000181] | 测试风险小幅退步，不是负互信息 |

A2 四个配对 SUP−SIM / SUP−RAND 比较区间均跨零。N2 旧袋的无 EEG 历史基线 bAcc 约 0.985；新匹配袋在 49/57 候选中有双半份共同支持，但固定角色分割的 4/5 外折组数不足，**按计划停止 N2 后续分布能力与真实比较**，不能写成分布信息不存在。来源收尾审计保留 4 项未解决控制/隔离限制。

所有区间均为固定预测/统计的身份组 bootstrap，未重训完整流程；身份组不是已经确认的独立儿童。当前真实比较属于 HA/BDF 工作包，不能推广为 CI 整体结论。科学验收 `final_001` 无必需回执缺失或失败，59 项模块测试通过；0 新编码器、0 GPU，科研申请资源上界 32 CPU core·h。发布检查另计，原结果与失败版本保留。

![v2.1 real risk comparisons](reports/auditory_v21/figures_002/new_real_risk_comparisons.png)

## auditory_next v2 结果

本轮复用既有表示，没有训练新编码器；按固定主比较探索背景条件读出、重复试次分布和序列先验之外的 EEG 增量，并修复旧读出。下表是探索结果，完整科学状态还取决于必要对照；数值未完成不能当作阴性。

| 问题 | 固定主结果及95%区间 | 决策与限制 |
| --- | --- | --- |
| A2：刺激差异重复性 | 49组，T=0.01539 [−0.03060, 0.05932] | 未达推进条件；背景预测项可重复，残差不能替代主终点 |
| C2-R：左右联合收益 | 60组，−0.000334 [−0.001047, 0.000301] bits/trial | 560个神经头与325个线性头完成；未显示明确联合收益，平行修复及部分隔离对照缺失 |
| N1：背景条件读出 | 59组，−0.024957 [−0.027989, −0.022169] bits/trial | 当前实现不推进；关键合成正对照仍不可评价 |
| N2：均值之外的方差增益 | k=8、57组，−0.001494 [−0.003017, −0.000258] bits/bag | 主线性结果为负；次要240个神经头失败，无EEG历史基线已达bAcc=0.98288 |
| N3：序列先验之外的EEG增量 | 60组，−0.050632 [−0.057756, −0.041194] bits/trial | 未达推进条件；训练选族和容量不同，负风险增益不等于负互信息 |
| E0-R：记录内目标可读性 | 1,024个神经头中765稳定、259未解决 | 全族新MLP结果扣留；旧7对linear结果单列，混合MFF来源不能整体称为CI |

C2-S几何重建精确，但两个新增空间成分没有共同显示明确预测收益。G0同记录后块R_SIM bAcc约0.516。合成审计发现共享背景预测可能制造残差重复性；另有90个分类世界因数值门限不可评价，未知分母保留。N1/N2/N3未触发seed23扩展或新架构开发。详见[路线四轴状态](results/auditory_next_v2/final_002/route_status.csv)。

最终版本为 **final_002**，历史文件与私有权限复核通过，45个最终交付文件通过结构/已知标识符扫描。`final_001`的旧完成标记未拦截日志权限异常，不能作为最终验收；修订记录保留。历史资源实际总量未知，保守上界138.773 CPU core·h / 13.713 GPU·h低于本轮上限。发布打包与测试另记在[发布核验](release/verification.json)，不改写科研预算回执。

![N1 fixed primary estimates](reports/auditory_next_v2/final_002/N1_primary.png)

## Auditory5 五路线首轮结果

90/90 表征任务完成（60 个学习型编码器、30 个 L0/随机任务）；173 项模块测试通过，完成 1,000 组合成实验。最终执行状态为 `S4_RECORDED_WITH_FAILURES`，不等于五条科学路线全部成功。主表征固定为 SimCLR（R_SIM），监督模型为平行分析。

| 路线 | 主结果及 95% 区间 | 状态 |
|---|---|---|
| A：刺激差分重复性 | N=55；T=0.01335 [−0.02700, 0.05356] | 效应较弱；0/55 满足全部固定历史×位置配额，关键对照支持不足 |
| B：条件历史信息 | N=60；增益 −0.00217 [−0.00309, −0.00122] bits/trial | 控制完成；`NEGATIVE_SCREEN` |
| C：左右证据互补 | 主 MLP32 读出未完成；线性结果完整保留 | 数值不收敛，`IMPLEMENTATION_FAIL`；不能解释为科学阴性 |
| D：刺激头 null 空间的临床增益 | N=51；MAE 改善 0.10873 [−0.14220, 0.38796] MUSS 源分 | 控制完成；未达到 0.5 分探索阈值，`NEGATIVE_SCREEN` |
| E：跨任务充分性 | E0 线性结果有 7 对；5 个 MLP 记录×读出失败；E1 bapa 16<20 | E0 部分数值失败；E1 群体迁移支持不足 |

区间来自固定 OOF 结果的 2,000 次候选级 bootstrap，没有重训完整流程。不同路线单位不同；上述量级阈值是探索筛选规则，不是临床有效性阈值。已探索队列不作为未经查看的确认样本。

![Auditory5 first-pass estimates](results/auditory5_v1/S4_final_001/screen_estimates.png)

## Phase 0–3 已有结果

| 问题 | 实验结果 | 解释范围 |
|---|---|---|
| 试次数量与幅值一致性 | 同一 49 个 HA 候选，每半份 20→160 个试次，ICC 中位数 0.394→0.809 | 完整采集内回顾性抽样；不是跨日重测或已验证的提前停止规则 |
| EEG 是否改善 MUSS 预测 | 同一 50 个 HA 候选，临床基线 MAE 7.048；加入分别惩罚的 EEG 时空特征为 7.075 | 测试的特征和模型未显示临床增量；惩罚敏感性检查是在看到初始结果后追加 |
| CI/MFF 事件响应 | 203 份 canonical MFF，164,735 个目标事件，145,180 个主 QC 保留试次；明确 CI、任务未知的 18 份完整支持记录，刺激后 AUC 中位数 0.517 | 记录内事件码解码较弱；203 份记录不是 203 名 CI 儿童 |
| CI 临床建模支持 | 来源 CI/CIHA 标签或同日明确 CI 设备史共 17 个候选索引，年龄/MUSS/可测 EEG 交集为 2 | 37 个混合来源完整候选不能直接视为确认 CI 样本；量表单位仍有问题 |

最后的元数据补充识别了部分设备佩戴说明，以及 6 份 `normal` 字面标签来源，留下 155 份未知组别来源。`normal` 不等同于临床确认正常听力，佩戴说明也不确证设备开启或逐 epoch 条件。初始实验分层及后续修正均保留。

![HA 临床预测比较](figures/phase3_final/ha_clinical_increment.png)

![试次数与采集内幅值一致性](results/phase3_trial_budget_001/trial_budget.png)

## 阅读与复现入口

- v2.1：[审阅修订方案](AUDITORY_V2_1_REVIEW_AMENDMENT_79b3521%20%281%29.md)、[科学结果](docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md)、[复现导航](docs/auditory_v21/REPRODUCTION.md)、[作业记录](docs/auditory_v21/JOB_LEDGER.md)、[路线状态](results/auditory_v21/final_001/four_axis_routes.csv)、[PDF/PNG 图表](reports/auditory_v21/figures_002/)。
- auditory_next v2：[执行方案](AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md)、[最终报告](reports/auditory_next_v2/final_002/NEXT_ROUND_REPORT.md)、[研究决策](docs/AUDITORY_NEXT_RESEARCH_DECISIONS_v2.md)、[复现导航](docs/AUDITORY_NEXT_REPRODUCTION_v2.md)、[聚合指标](results/auditory_next_v2/final_002/metrics_aggregate.csv)、[GPU规则](docs/GPU_SCHEDULING_POLICY.md)。
- Auditory5：[执行方案](AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md)、[最终报告](reports/auditory5_v1/S4_final_001/FIVE_IDEAS_SCREENING_REPORT.md)、[作业记录](docs/AUDITORY5_JOB_LEDGER.md)、[复跑导航](docs/AUDITORY5_REPRODUCTION_v1.md)、[聚合指标](results/auditory5_v1/S4_final_001/metrics_aggregate.csv)。
- Phase 3：[报告](docs/phase3_report.md)、[科学方案](docs/PHASE3_SCIENTIFIC_PROTOCOL.md)、[产物导航](docs/PHASE3_ARTIFACTS.md)。
- Phase 2：[报告](docs/phase2_report.md)、[固定方案](docs/PHASE2_PROTOCOL.md)、[产物导航](docs/PHASE2_ARTIFACTS.md)。
- Phase 1：[报告](docs/phase1_report.md)、[固定测量方案](docs/PHASE1_MEASUREMENT_PROTOCOL.md)、[产物导航](docs/PHASE1_ARTIFACTS.md)。
- Phase 0：[数据审计](docs/phase0_report.md)、[产物导航](docs/ARTIFACTS.md)、[项目规划](docs/PROJECT_PLAN.md)。
- [发布范围与复现说明](PUBLICATION.md)、[汇总文件导航](results/README.md)、[发布文件清单与 SHA256](release/manifest.json)。

`auditory_v21/`、`auditory_next/`、`auditory5/`、`scripts/`、`configs/`、`slurm/` 保存分析代码、配置和批任务入口；`server_restart_en_v1/` 是早期历史计划，不代表最新证据。所有分析和验证均通过 Slurm 运行；后续GPU禁用P100，优先A100/L40S/H100，备选V100/PRO6000。完整数据流程依赖服务器上的受限源数据、映射及分运行源码快照，单独克隆此仓库不能重建全部实验。
