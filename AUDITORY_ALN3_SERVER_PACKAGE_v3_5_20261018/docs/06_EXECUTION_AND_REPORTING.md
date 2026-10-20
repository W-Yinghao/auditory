# 06 — 执行身份、资源、统计与交付

## 6.1 执行状态与授权

本包是在既有ALN3.4探索与10-GPU授权下的限定下一轮。server接入后，完成相关必要工程检查即可执行；不因论文框架、措辞、显著性或新一轮go等待。准备本包的本地环境未执行真实EEG训练、未提交Slurm、未推送GitHub。

所有任务在`plans/workpackages.json`列明性质：重分析、继承继续、限定新增或依赖敏感性。一个任务缺checkpoint只影响其真实依赖；不能形成全项目总gate。区分failed execution、未完成覆盖、数值不可估计和有效阴性结果。

## 6.2 不改写旧执行身份

建议新生产模块使用`auditory_alignment_v3/aln35/`，新配置/入口用`scripts/auditory_alignment_v3/aln35/`，私有运行输出`private/auditory_alignment_v3/aln35/`，公开可发布派生结果`results/auditory_alignment_v3/aln35/`。这是需要server实际接入的目标路径，包内参考脚本不假装这些模块已经存在。

每个新unit的signature至少包含：

`workpackage_id, design_version, dataset, source/donor lineage, target exclusion, source execution/checkpoint/plan hashes, code hash, objective, EEG/audio access, target coordinates, candidate/query identifiers, fit/cal/selection roles, seed, outer/content fold, support-selection rule, adaptation/training budget, readout, comparison version`。

使用canonical JSON哈希生成新ID，明确parent IDs。保持原始records、失败副本、运行中源码与旧计划。修改实现产生新code/design版本；对仍运行旧版本的任务保持其源码快照可用。不能把新统计结果写回旧训练unit冒充原注册分析。

旧`held_executions.json`维持精确列表。已完成旧结果可读、可比较；未完成且obsolete的执行不批量恢复。不得为本包删除checkpoint、清空hold、重置队列或取消其他项目作业。

## 6.3 10-GPU调度与实际成本

- 项目同时运行GPU总数最多10张，计入所有旧/new runner、replay与工程probe；不是每条lane各10张。
- source/inner依赖优先给能够解锁多个已登记比较的任务。CPU重分析与文档勘误立即并行；其完成不依赖GPU阳性。
- 首个代表工程运行记录device、实际wall time、显存、更新/样本次数、cache IO、失败/恢复。之后按实测更新成本估计，给范围和依据，不将估算当消耗或完成承诺。
- 新APwrong、support、episode、checkpoint-selection、matched-update任务按专题限定范围登记，不自动扩展所有数据集/loss/backbone/种子。首批完整比较完成后，先解释结果，再决定后续轮次的问题。
- 既有有效在跑任务不因为本包优先级改变而强行中断。确实需要资源重排，只修改确切project-owned待运行任务或其已支持的调度权重，保存回执。

保持现有数据位置规则：新下载若确有必要使用`/projects/EEG-foundation-model`内既有数据根；本轮默认不需要新数据集。不把私有数据复制到用户home或公开包。

## 6.4 选择层级必须如实

训练人内的held-out声音/早停、ridge-only OOF、整个模型训练流程排除inner人，是不同协议。每项结果报告实际层级；不能改个名称就把旧checkpoint变成新的人群独立开发。

新策略超参数、checkpoint、support选取、窗口或模型身份只能依照source fit/cal/独立inner开发数据。所有outer query用于最后评估；其标签、真风险、组差、显著性不能参与选择或停止。支持池的元数据访问也必须单列，不能把访问30%刺激日志择出10%训练样本暗称仅10%标签预算。

固定候选包括0-step/原模型，ties按预先声明的更简单候选优先。epoch0获选是合法结果，区分“有效回退”与“非零个人学习”。原native/unified策略差异保留；新策略需要新policy ID。

## 6.5 统计合同

### 继承结果

原已注册主分析、bootstrap-t/max-t family和已报告区间原样保留。修复解释或数值执行不能静默改变统计对象。凡改变分析方法、对比集合、目标或样本集合，写新analysis version与已见结果说明。

### 本轮新增探索性直接比较

1. 使用真实逐人结果，在同一个人内形成规定arm/window/support差；先按真实重复content/session评估cells汇总，再按所需seed平均。
2. `outer subject_fold`是该人的排除归属，不是每个人都应具备的重复fold。适配导出器明确重复fold语义；已经合法汇总的逐人值可使用`reported_identity_mean`，必须保留上游完整性溯源。
3. 每个family明确metric、unit、readout、访问合同、query集合、固定比较、所需seeds与expected identities。不能从观察到的人反推总体就是这些人。
4. 对需要的全部条件取共同完整人；同时输出每个条件覆盖与缺失原因。未完整也可报告描述性interim，但不能按临时p值停止或选择更好子集。
5. 新小family参考实现采用4000次整人bootstrap，按预先指定听觉组/stratum独立重采样，所有同人条件共用抽样索引；用原样本固定SE归一化的max-|z*|构造同时区间。区别于每次bootstrap重估SE的旧bootstrap-t。
6. 直接组间改善差由各组人内改善再做组差；组内独立重采样，同一组抽样索引在整个family复用。组差不能由两条独立CI相减生成。
7. 少于3完整人、零经验方差或其他非正规条件，报告`nonregular`、覆盖及点估计（若有），CI缺失；不能把零经验方差解释成总体等效。小组（如NH9、中间佩戴阶段5）即使满足计算条件，仍保留有限精度边界。
8. 每个原始family、所需条件、SE、bootstrap seed、临界值、B、方法名及探索性标签一并输出。采用本包reference工具需按docs/08转换真实输入，不能把synthetic example当生产数据。

此新统计法是透明的探索性补充，不是为了获得更小区间；同时保留原注册方法的结果或失败诊断。无需替换所有旧表，也不声称有限样本下精确家族覆盖。

### 效应对象

检索主风险用bits/query、儿童分类用bits/trial/AUC，group比较为改善差。不同采样率、音频维度、候选数/候选池、输入时间范围或native/unified readout不能随意合并。音频线性残差可预测性及history模型log-score gain均不是精确CMI。概率校准改善、排序改善、表征功能变化分开报告。

## 6.6 必要检查，不设科学绩效门槛

| 风险 | 必要检查 | 失败时影响 |
|---|---|---|
| 时间访问误标 | 由实际sample indices核算mask交集、half-open边界和采样时刻 | 只纠正受影响条件 |
| 训练/开发人重叠 | source/inner/outer身份与拟合对象全链记录；不只查head | 只停止不满足所宣称协议的新增策略 |
| 假错配 | canonical刺激/anchor组置换、重复视图一致、无真实重配、曝光记录 | 修复该wrong lineage，原有效AP继续 |
| support泄漏/覆盖混淆 | 固定query、support pool/fit/metadata访问分开、源端选择 | 修复对应支持策略 |
| 概率错列 | candidate IDs/order/hash与query集合一致、归一化/有限值 | 只排除不兼容融合输入并报告 |
| episode干预近恒等 | 实际BA、表示/预测位移、梯度与更新方向；CS单类支持检查 | 解释配方实际压力，不删儿童或伪造非零梯度 |
| 统计退化 | SE、临界值、共同人集、重复行与非有限值 | 标非正规/缺失，保留原结果 |

性能低、区间跨零、配方没赢不属于工程失败。检查已经足以解决风险后停止重复测试，继续有效比较。

## 6.7 结果文件和最小交付

server每轮输出：

- `INTAKE.md`、`ALN35_BINDINGS.json`、`ALN35_EXECUTION_PLAN.json`；
- `CORRECTION_PRIVATE_PRE_ACCESS.md`和affected-IDs机器清单，旧数值来源哈希；
- `paired_science.json`、`group_effects.json`、`support_coverage.json`等按实际完成生成的逐人/汇总文件；
- 每条新增方法的implementation、engineering receipt、complete/expected覆盖及原始选择轨迹；
- `ROUND_REPORT.md`：观察→竞争解释→本轮区分→实际结果→仍未分清，正/负/不确定对称；
- provenance/manifest，复用、缺失、失败、nonregular与旧hold分别列出；
- GitHub可发布副本的实际来源与哈希，沿用既有发布工作流。不得将“已准备包”写成“已训练/已发布”。

個体级模型结果公开已授权，不再询问相同范围。沿用当前已批准字段白名单，包括既有匿名人ID及已允许的模型得分/年龄/佩戴时长字段；原始EEG、真实身份、映射表、联系信息、私有checkpoint和逐trial原始记录不由本包新增公开。support覆盖可发布聚合或既有允许粒度，新增原始事件序列不自动公开。

本包本地交付另有`reports/LOCAL_VALIDATION.md`、`MANIFEST.json`、`SHA256SUMS`，只证明文件与参考工具检查，不证明server生产结果。
