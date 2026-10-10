# Auditory Alignment Next — 服务器材料包 v2.0

**日期：2026-10-06｜阶段标识：ALN2｜仓库：W-Yinghao/auditory**  
**核查基准：e993e3777989f3048f4c802c1697b0db3de3c205；上一轮主体结果：84c73924ad3da12181e83400f58f0f67a37af8c4。**

## 本轮要做什么

发展**保留时间结构的声音–EEG群体对齐模型**：以现有InfoNCE为强基线，以传统核CS为主要竞争目标；加入稳定声音目标、EEG基础模型的听觉微调、同试次注意选择，以及公开听觉先验到私有HA儿童的任务迁移。FMCA保留有实验依据的改进配置。HA、CI、正常对照、儿童年龄和HA验配阶段仍是研究对象，不预先规定其结果方向。

> **本项目不以负结果为研究终点，也不以“能力地图、天花板、没有信息、方法失效”作为自动成稿路径。弱结果必须完整报告，但首先用于定位可改善的学习、任务与数据支持问题。更多seed、fold和模型运行不会增加独立儿童，也不会把未建立收益变成不存在证明。**

本纪律不是“只要阳性”：数据、失败运行、反向效应和未改善结果全部保留；方法选择不使用组间显著性，不削弱对照、不移动临床终点、不删除不符合预期的儿童。

## 阅读与交接

| 文件 | 用途 |
|---|---|
| `SERVER_START_PROMPT.md` | 可直接发给服务器代理的独立启动文本 |
| `docs/00_RESEARCH_DISCIPLINE.md` | 新研究纪律、旧规则的失效范围、报告语言 |
| `docs/01_STORY_AND_EVIDENCE.md` | 当前证据、待检验解释和论文主线 |
| `docs/02_SERVER_MASTER_PLAN.md` | 四个工作方向与并行执行安排 |
| `docs/03_TEMPORAL_METHOD.md` | 时间表示、窗口读出与线性参照 |
| `docs/04_FOUNDATION_AND_AUDIO_TARGETS.md` | CBraMod/REVE微调、声音目标和教师–学生 |
| `docs/05_GROUP_ATTENTION_TRANSFER.md` | 群体共享、注意选择、个体适配和跨队列训练 |
| `docs/06_PRIVATE_CHILDREN.md` | 私有HA验配初期的独立问题、类别与历史任务 |
| `docs/07_EVALUATION_AND_INTERPRETATION.md` | 评分、统计、功能/发育分析与解释 |
| `docs/08_IMPLEMENTATION_AND_RUNS.md` | 代码接入、完整训练、调度与交付 |
| `docs/09_REPORT_TEMPLATE.md` | 阶段结果报告模板 |
| `docs/10_SOURCES_AND_CHANGELOG.md` | 可追溯来源及与旧方案的区别 |
| `docs/11_RUN_PLAN_SUMMARY.md` | 默认完整计划的实际展开规模与运行说明 |
| `SERVER_FULL_DOCUMENT.md` | 全部章节合并版 |
| `AGENTS_APPEND.md` | 建议添加到服务器工作副本AGENTS最前的新研究规则 |
| `configs/`、`schemas/` | 可调整配置、实验族注册、结果结构 |
| `scripts/` | 计划展开、包检查和干运行脚本；不含真实训练控制器 |
| `reference/`、`tests/` | 局部时间接口与注意损失的参考实现、短测试 |
| `plans/`、`receipts/` | 已生成的计划、实际数值测试和包检查结果 |

## 现成代码与待实现代码

包内Python只负责**计划生成、格式核对、数学/张量接口示例**。它们不是已连接私有EEG的生产训练程序。基础模型权重、真实数据加载、跨折迁移控制器、完整训练/评价及Slurm接入由服务器实施。不要把`planned`写成`complete`。

现有`auditory_alignment/`可复用。新代码建议进入`auditory_alignment_v2/`，旧结果不覆盖。旧材料中的科学关闭规则不再有效；身份、隐私、划分和数据授权要求继续有效。**本包不授权向GitHub公开任何新数据或权重，也不授权发邮件联系医生。**

短测试只检查运算是否成立，不是科研门槛。通过后按完整实验族执行；某一模块暂时无法接入不阻止其他模块。更多扩展用新版本登记，不能伪装成事前确认研究。
