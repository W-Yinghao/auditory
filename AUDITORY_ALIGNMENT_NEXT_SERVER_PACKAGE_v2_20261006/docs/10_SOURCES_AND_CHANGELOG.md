# 10｜来源、证据与本版新增内容

## 10.1 基准和可追溯路径

仓库基准：`e993e3777989f3048f4c802c1697b0db3de3c205`，2026-10-06核查仍为最新；主体结果`84c73924ad3da12181e83400f58f0f67a37af8c4`。以下路径均相对此基准。

| 编号 | 来源 | 本包使用范围 |
|---|---|---|
| R1 | `docs/GITHUB_PUBLICATION_KERNEL_CS.md`；提交元数据 | 发布范围和版本，不代表本轮已经执行 |
| R2 | `docs/auditory_alignment_kernel_cs/IMPLEMENTATION_NOTES.md` | 实际数据接口、模型、选择/读出、更正及运行 |
| R3 | `docs/auditory_alignment_kernel_cs/FULL_RESULTS.md` | 方法、注意、wrong-pair、训练及重复性聚合 |
| R4 | `docs/auditory_alignment_kernel_cs/OPTIMIZATION_RESULTS.md` | 冻结随机声音头、带宽/batch等配方 |
| R5 | `docs/auditory_alignment_kernel_cs/TEMPORAL_RESULTS.md` | 时间窗、直接风险差与等宽比较 |
| R6 | `docs/auditory_alignment_kernel_cs/GROUP_DEVELOPMENT_RESULTS.md` | 组差、训练覆盖、年龄和功能 |
| R7 | `docs/auditory_alignment_kernel_cs/NEXT_INTERPRETATION.md` | 仓库候选解释；不当作已验证结论 |
| R8 | `auditory_alignment/model.py` | pool4、窗口与声音投影实际结构 |
| R9 | `auditory_alignment/losses_reference.py` | 传统核CS、FMCA、InfoNCE公式实现 |
| R10 | `auditory_alignment/train.py` | 群体训练、采样、E6目标与checkpoint选择 |
| R11 | `auditory_alignment/evaluate.py` | 原生/统一读出、查询错配、私有头 |
| R12 | `auditory_alignment/aggregate.py` | 聚合、风险差及儿童×窗口bootstrap近似 |
| R13 | `AGENTS.md` | 只读来源、Slurm、隐私与历史指令 |

永久目录：
`https://github.com/W-Yinghao/auditory/tree/e993e3777989f3048f4c802c1697b0db3de3c205`

使用某项来源时，服务器报告可以直接给出上述版本与文件路径，不需要引用对话中的不可访问工具编号。

## 10.2 历史材料

**H1** 用户上传《听觉EEG公开–私有联合研究方案v3（JBHI）》：第10页自动转地图稿、第11页新编码器限制、第14页阶段门槛是本次明确取代的旧策略；第1页本身说明它是候选规格而非执行报告。保留其文本和历史身份，不据其‘尚未下载公开EEG’覆盖现有已执行仓库。

**H2** 已上传的GX/PF/DV及私有分析文档与kernel-CS v1服务器包：作为历史任务与私有阶段的来源。早期‘数据用尽’‘全部方法关闭’‘临床不存在’不是本轮已采纳结论。人数、时长和任务覆盖以服务器当前有效身份/数据接入清单为准。

**H3** 当前对话2026-10-06用户指令：不以负结果为研究/论文导向；通过完整实验探索方法，私有数据承担公开数据不能替代的问题。这是研究策略来源，不伪装为统计学定理。

## 10.3 新增外部方法入口（2026-10-06核查）

- **W1 CBraMod作者实现**：https://github.com/wjq-learning/CBraMod （公开README提供pretraining/finetuning与B×C×patches×200示例）。这是输入/微调接口依据，不是听觉性能保证。另有作者仓库入口https://github.com/sell-hens/CbraMod；使用哪个版本由服务器pin并记录，不能混用权重和代码。
- **W2 REVE作者项目**：https://brain-bzh.github.io/reve/ （200Hz、电极位置接口与权重/微调入口）。
- **W3 REVE作者实现**：https://github.com/elouayas/reve_eeg （训练/微调与配置）。

本包不复制论文大段内容，不提供权重或用户数据。外部checkpoint版本、许可、代码SHA与预训练覆盖尚需在真实服务器接入时记录。

## 10.4 本版真正新增的方案

时间密度保留、lag-local token、foundation的并列适配、稳定声音目标对照、同试次选择性损失、公共到私有任务迁移、正确的报告纪律是本轮提出的**设计**。它们尚无本项目真实EEG运行结果，不写‘已验证提高’。

`reference/`只提供基本张量函数与独立代数检查；零相位时间传播、基础模型微调稳定性和临床效度未由这些短测试验证。

## 10.5 相对上一包的变化

| 上一轮要点 | 本版改变 |
|---|---|
| 以四种依赖目标的完整矩阵为主 | 以时间表示/预训练/注意/儿童迁移四个研究问题组织完整比较 |
| 固定pool4小网络覆盖所有任务 | 保留legacy，同时增加时间保留和基础模型路径 |
| CS为主要新增方法 | NCE目前为强基线，CS有针对性竞争，FMCA有依据的改进并行 |
| 竞争语音只对齐attended流 | 新增同试次选择与联合训练 |
| 私有任务沿同一低维接口 | 任务匹配baseline、原生/冻结头并列、公共先验迁移 |
| 仓库建议可能转基准/地图稿 | 明确取消负结果导向与自动成稿；完整报告但继续有依据的能力建设 |
