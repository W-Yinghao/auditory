# 7. 科学报告、交接与停止

## 7.1 最终报告先回答研究问题

报告正文先按下面五个问题给出结论、逐人证据与直接对比，再报告工程状态。不能以队列清空、表格格数或所有脚本退出0代替科学结果。

| 问题 | 必须一起呈现 | 对主张的影响 |
|---|---|---|
| 学到了哪些声音相关关系？ | TCS/TNCE/GCS/wrong/B0的内容与history-residual；旧有效local/CB/REVE成分结果；source诊断 | correct−wrong不能替代correct−B0；CS必要性须直接对比TNCE/GCS |
| 时间改变了什么？ | 同窗、固定跨窗、重拟合三者；旧细时间探针单列 | 重拟合恢复不单独等于迁移优势；窗权重不叫神经潜伏期 |
| 新个体需要哪种适配？ | δ对U0、对affine；ALN3.6 NET_C/NET_T与旧分项；每人分布 | 相对弱HP的改善不等于超越E0；共同接口收益与CS专属收益分开 |
| 儿童承担了什么科学功能？ | frozen/FT/history/twin；纯音→ba/pa transfer/refit；年龄与既定关联 | 分别判断判别复用、表征可用、发展相关信息；不互相替代归因 |
| 与外部方法相比实际怎样？ | 一个忠实任务适配系统的同Q20秒结果、输入/训练access和成本 | 不能以同名数据或论文acc替代共同评价；不足则诚实标出缺证据 |

每个结论给出：原结果文件/hash、样本与query覆盖、效应与区间、各seed方向、该结论依赖的假设/有效性状态。不使用“未显著所以没有信息/已到天花板”，也不因为一个seed阳性就称稳健。零效应附近的区间宽度、实际量级和直接方法差异一起解释。

## 7.2 必须交回的研究产物

下列文件名是建议的新汇总名称；服务器实际目录写在binding。旧输出保持原名与原key，用索引连接，不要求复制大缓存。

1. ROUND2_AND_CLOSURE_REPORT.md：上述五问题的独立可读正文；末尾给支持/未解决/不支持的主张表。
2. SCIENCE_FIGURES/：docs/00五图PDF/SVG及图用数据；图内显示单位、n、seed、CI定义和覆盖；时间细尺度与400ms窗口不混成同轴。
3. EVIDENCE_INDEX.json：每个有效旧/新结果→研究问题/figure/panel/单位/比较合同/路径/完整hash/版本状态。all-zero pre或受已知代码错误影响的旧单元标invalid，不能把同系列全部删掉。
4. R2_REUSE_INDEX.json、INTAKE_AND_BINDING.json：当前HEAD、原计划、live queue观察时间、已有/缺失/复用/新算；记录真实工作量。
5. SOURCE_LEARNING_REPORT.md及诊断JSON/CSV：固定panel与checkpoint、native正确/错误目标、NCE精确null、CS potentials、raw/projection rank、δ/q变化、源ridge fit/dev、梯度，不在诊断中挑新赢家。
6. PRIVATE_EVENT_VALIDATION_SUMMARY.json、PRIVATE_RECOMPUTE_SCOPE.json：核验覆盖、来源等级、bug依赖或真实序列失配。原始事件trace只在私有根。
7. SUPPORT_INTERPRETATION.json、CROSS_STIM_INTERPRETATION.json、AGE_AND_CLINICAL_REUSE.md：原20/13/既定关联family完整保留，Q/训练侧与归因清楚。
8. paired_net_diagnostic_s3401_s3407.json及adapter receipt：新净收益明确post-R1 diagnostic/reference CI；原ALN3.6 production CI并列保留。
9. EXTERNAL_COMPARISON_BINDING.json、EXTERNAL_COMPARISON_REPORT.md及逐人20秒scores：唯一外部路线、10真实public units或具体阻塞；不把fallback称MindMix结果。
10. RESOURCE_AND_COVERAGE.json：原R2成本与本包增量、每job实际GPU时、失败原因、重用件、缺失单元、严格有效coverage。
11. FINAL_CLAIM_DECISIONS.json：按plans/decision_rules.json逐项回答，不自动开R4。

未完成、工程无效、来源未解决、有效但效应弱四种状态不得合并成“失败”。原代码/数据更正保留旧版、替代hash与依赖说明；含bug结果不能和修复版简单合并seed平均。

## 7.3 报告的固定结构

使用templates/ROUND2_AND_CLOSURE_REPORT.md。研究结论的主语是可读内容、读出复用、适配收益或儿童用途；不要让目录名、作业号和模型版本成为论文的逻辑主语。图表由已固定的科学问题组织，不按最终p值挑图。

bootstrap推断以人为单位，所有slot、tool、arm、seed、draw在同人内保留配对；一个人的多记录、seed、支持抽样不增加n。明确每个family控制什么，不把不同family各自95%区间说成全论文95%覆盖。既有原算法、reference helper和任何必要修复版本分别命名。

## 7.4 接包动作和提交范围

SERVER_START_PROMPT.md是直接交给服务器助手的启动入口。AGENTS_APPEND.md只供在现有规则中追加本轮约束，不能覆盖原AGENTS、原发布授权或安全机制。

本包没有发送外部消息、GitHub推送、取消作业或删产物脚本。用户已授权去标识个体结果公开；沿用已有发布流程即可，不再次询问同一授权。原始EEG、身份crosswalk、精细原始事件轨迹不会因为这项授权自动变为公开材料。

A3d/A3c/A3b/ALN2 D_FM的清理属于独立的依赖清理判断。此次先完成资产引用与本轮复用索引；不在实验包中自动删除或顺带清理它们。

## 7.5 明确终点

原R2的有限已授权任务完成或被具体有效性证据定点勘误，一个外部席位有可审计结果或具体阻塞，五问题证据整合完成后，本轮执行结束。存在论文证据缺口时在结论中写清，而不是继续扩model/seed/window/数据集矩阵。

优先保留真实、可复核的研究结果。CS没有独特优势时取消“CS优越”的主张；δ没有优于校准时取消“时间适配必要”的主张；这些判断不抹掉其它有效迁移、时间和儿童结果。也不把仅Stage1年龄预测成功重新包装成原定跨范式迁移已经成功。

