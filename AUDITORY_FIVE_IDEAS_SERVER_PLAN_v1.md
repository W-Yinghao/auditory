# 儿童听觉 EEG：五条解码与信息论路线的服务器执行方案

**版本：** v1.0 · 2026-09-17  
**项目：** `W-Yinghao/auditory`  
**目标：** 并行探索五个有区分度的研究问题，为 IEEE JBHI 论文选择有实证支持的主线。  
**交付类型：** 研究设计、实现规格和执行任务书；不是已完成的实验报告，也不包含已经实现的训练程序。  
**本轮授权范围：** 实现共享基础设施、完成测试、开展 A–E 的首轮探索并汇报；不自动启动大模型搜索或后续方法扩展。

> 给服务器执行代理：先读 §0、§2–7，再按 §13 的依赖顺序工作。每条路线必须得到 `完成 / 阴性 / 混合 / 支持不足 / 实现失败` 中的明确状态，不能只运行最容易阳性的路线。真实数据缺失时只完成代码和合成测试，不虚构结果，也不要反复重做整个 Phase 0。

---

## 目录

- §0 研究任务与不可变边界
- §1 已有工作的联系及本项目的区别
- §2 当前数据依据、复用入口与服务器环境
- §3 数据契约与样本资格
- §4 信号处理与信息隔离
- §5 训练、验证与跨阶段隔离
- §6 共享模型、SimCLR 和训练默认值
- §7 信息指标、统计与继续条件
- §8 Idea A：刺激条件化的个体响应表征
- §9 Idea B：听觉历史的条件信息解码
- §10 Idea C：听觉判别证据的互补与冗余
- §11 Idea D：刺激分类头之外的临床功能信息
- §12 Idea E：跨听觉范式的信息充分性
- §13 分阶段执行、任务矩阵与计算预算
- §14 软件目录、命令接口及 Slurm 模板
- §15 必须通过的测试与反例
- §16 结果文件、报告模板及验收
- §17 后续方法扩展与论文推进条件
- §18 配置模板
- §19 来源与参考文献
- 附录：首次交接给服务器的执行指令

---

## §0 研究任务与不可变边界

### 0.1 五个问题，不是五种主干网络

| ID | 主问题 | 首轮产物 | 不允许替换成的故事 |
|---|---|---|---|
| A | 哪些个体刺激响应差异在独立重复块中可复现，而不是一般个体背景？ | 独立重复的表征对比与背景对照 | EEG 去噪、ERP 重建、身份识别准确率 |
| B | 控制当前声音及可观测实验条件后，当前 EEG 还包含多少前序刺激信息？ | 条件历史解码及可观测混杂检查 | 一般序列网络准确率、直接宣称预测编码 |
| C | 两部分 EEG 的声音判别证据可互相替代，还是具有条件预测增益？ | 单分支与联合读出的配对比较 | 多加一个 attention/PoE 模块 |
| D | 固定刺激分类头看不见的表征，是否仍有儿童级功能信息？ | 固定头分解与嵌套临床增量检验 | 不加约束地回归量表、重复旧身份擦除实验 |
| E | 源听觉任务学到的表征，是否保留目标任务所需的信息？ | 匹配目标读出条件的表征迁移矩阵 | 两个任务谁的 accuracy 更高 |

### 0.2 方法立场

- 不要求 Mamba、HFMCA、FMCA、tPoE、foundation model 或信息瓶颈。
- 默认从线性基线与小型卷积编码器开始。需要对比学习时，优先标准两视图 SimCLR；同时保留相同编码器的刺激监督版本。
- SimCLR 是优先实现选择，不是“已经证明在本数据上更稳定”的实验结论。[R1]
- 信息论首先用于定义问题、比较条件信息和限制解释，不强制每条路线都有 MI/CMI 训练损失。
- 普通跨被试解码只是数据与表征可用性的基线，不是最终主要贡献。
- 不做 ERP 波峰识别、P1/MMN 主线、平均波形重建、在线停止采集或复杂清理算法开发。
- 同一事件的多通道短片段仍可称 epoch；使用事件对齐输入，不等于以 ERP 为研究主线。

### 0.3 事实、假设和授权分开

本文数值分为三类：

1. **已有报告事实**：来自指定仓库快照，只说明当时已经运行的工作。
2. **本轮设计默认值**：维数、学习率、样本资格和筛选门槛，均是待执行的工程/研究约定，不是公认临床阈值。
3. **待检验假设**：A–E 的科学主张；不能在任何摘要或报告里写成已经成立。

本轮应完成五条路线的最低可行实验。出现路线级数据缺口，只暂停受影响路线，其他路线继续。后续新损失、大范围扫参、新终点或改变主任务须形成 v2 方案，不能为了阳性自动追加。

### 0.4 复用而不污染原项目

遵守仓库 `AGENTS.md` 和 `PUBLICATION.md`。[D1]

- 原始 EEG、临床表、Phase 0–3 结果只读。
- 计算、测试、环境探查、安装依赖、绘图均通过 Slurm；登录节点只读写文本、做 Git 与调度操作。
- 每次正式运行使用新目录，禁止覆盖旧模型、旧配置或阴性结果。
- 个体路径、姓名、精确日期、身份映射、临床行、逐试次信号/特征/预测全部放受限 `private/`，不提交到 GitHub。
- 不因仓库公开就认为允许发布新的参与者衍生数据。模型权重和匿名 ID 也不自动获得发布许可。
- 本文只交付文件；没有替服务器提交作业，也没有在原始数据上运行下述实验。

## §1 已有工作的联系及本项目的区别

依据用户提供的 thesis 源码中 `chapters/learning.tex`、`chapters/identity.tex`、`chapters/grounding.tex`。[T1]

| 旧工作 | 本项目继承的问题意识 | 不直接继承的实现 |
|---|---|---|
| HFMCA/HFMCA++ | 多视图共同信息、可迁移表征与依赖不等于任务价值 | log-det、正交白化、层次依赖训练 |
| CMI-Trace | 编码了什么、固定头用了什么、任务影响、移除后收益是不同问题 | 整套身份擦除方法和 domain generalization 搜索 |
| tPoE-EIB | 多份证据的整合、限制预测路径、直接干预而非仅画热图 | Gaussian experts、PoE 温度和特定门控结构 |

五条路线分别利用重复刺激、事件顺序、分开的输入信息、临床标签和跨任务结构；与旧工作的联系来自研究对象，不来自模型名称。

## §2 当前数据依据、复用入口与服务器环境

### 2.1 本文核对的仓库快照

```text
repository: W-Yinghao/auditory
observed_commit: aac4c366fdaf23507cc5d8b6510f675ae7af615b
snapshot_checked_on: 2026-09-17
```

服务器运行时记录实际 commit 和未提交改动。若已出现更新，不重置或覆盖；先产生 `snapshot_delta.md`，核对与本文相关的 schema、元数据、样本集合差异，再冻结本轮输入。

### 2.2 目前已知的数据支持度

| 项目 | 仓库报告事实 | 本轮含义 |
|---|---|---|
| HA | 57 个主测量合格候选；含完整阈值的既有临床比较为同一 50 个候选 | A–D 优先从 HA 开始；新资格规则需重新计数，不保证仍为 57/50 |
| MFF | 203 份 canonical 来源、145,180 个主 QC 保留试次 | 不是 203 名儿童，不允许按文件当独立人训练/检验 |
| MFF 临床 | 混合来源中 37 个完整候选；确认 CI/CIHA 来源或明确同日 CI 史范围内交集为 2 | 不启动确认 CI 临床模型，不与 HA 量表直接混合 |
| 任务 | 纯音 41 份、bapa 29 份、ba1ba4 1 份、未知 132 份来源 | 是记录数；先核对身份和任务兼容性，不能推导出四声调分类数据集 |
| 配对 | 同日纯音–bapa 9 个候选，既有完整解码支持 7 对，组别未知 | E 可以技术探索，不足以自动支持分组/临床推断 |
| 旧解码 | MFF 使用两个 ROI 的分箱特征与固定收缩 LDA | 不等于完整多通道解码已被否定 |
| 旧临床 | 50 HA：临床 MAE 7.048；临床＋分别惩罚 EEG 为 7.075 | 保留阴性；新的表征分解尚未被该实验检验 |

来源：[D2–D4]。这些值用于对账，不作为新的纳入目标。不能通过修改资格条件“凑回原人数”。

### 2.3 必读与可复用入口

| 文件/目录 | 用途 |
|---|---|
| `README.md`, `AGENTS.md`, `PUBLICATION.md` | 研究状态、运行规范和公开边界 |
| `docs/phase0_report.md` 至 `docs/phase3_report.md` | 来源、时钟、身份、信号与阴性证据 |
| `docs/PHASE1_ARTIFACTS.md`, `docs/PHASE3_ARTIFACTS.md` | 实际产物位置和版本含义 |
| `configs/phase1_v1.json`, `configs/phase3_science_v1.json` | 通道、旧处理、旧模型定义 |
| `results/phase1_sources_001/` | HA 来源资格及原始记录索引 |
| `results/phase1_epochs_001/` | HA 已有 epoch；须读 schema 再决定复用 |
| `results/phase2_archival_001/` | 最早记录与候选资格 |
| `results/phase3_ha_covariates_004/` | 阈值、年龄与设备时长的审计 |
| `results/phase3_ci_sources_001/` | MFF 去重后的来源 |
| `results/phase3_ci_linkage_005/` | 候选身份与同日链接 |
| `results/phase3_ci_epochs_001/` | MFF 事件账本；`epochs_roi.npz` **不是全通道数据** |
| `results/phase3_metadata_addendum_001/` | 最后的组别、佩戴说明及条件变化标记；必须合并读取 |
| `private/` 中对应来源映射 | 受限身份、原始路径、临床值，禁止复制进报告 |

这些入口来自现有文档，但公开副本不包含全部受限文件。[D3] 必须通过服务器本地 `exists/schema/hash` 核验，不能假设克隆仓库即有原始数据。

### 2.4 路径与运行环境

已读历史 Slurm 脚本提供以下线索，运行时仍需确认：[D5]

```text
historical_project_root = /home/infres/yinwang/EEG_auditory
historical_raw_root = /projects/EEG-foundation-model/auditory
historical_cpu_partition = CPU
```

历史早期脚本使用过 `EEG` 环境，后续报告使用 `eeg2025`。**不能直接调用最早脚本的 Python 路径作为新训练环境。** 在 CPU Slurm 作业内核对可用环境、PyTorch/CUDA、磁盘空间和现有依赖，再写入受限 `environment.lock.json`。GPU 分区、account 和 gres 从当前集群和有效模板解析；本文不编造它们。

## §3 数据契约与样本资格

### 3.1 四级分析单位

```text
candidate/person component -> session/record -> continuous segment -> trial/event
```

- `candidate_id` 是有证据支持的候选身份，不自动等于临床确认的儿童身份。
- `split_group_id` 使用已知同人关系、跨档案重叠与可信同人候选边的连通分量；允许保守地把疑似同人放同折。
- 歧义到无法确定安全连通关系的来源，不进入归纳式跨儿童训练；仅保留独立标记的记录内探索。
- 同一人的后续记录、不同任务、不同导出和所有增强视图必须留在同一外折。
- 不能利用量表值、模型准确率或波形美观决定身份或选择记录。

### 3.2 新 manifest 的最低字段

所有逐记录/逐试次 manifest 放 `private/auditory5_v1/data/`。

| 字段 | 类型/定义 |
|---|---|
| `candidate_id`, `split_group_id` | 不透明字符串；用于配对/划分，不输入 EEG 编码器 |
| `record_id`, `segment_id`, `trial_id` | 不重复的溯源键；`trial_id` 跨所有派生处理不变 |
| `source_sha256`, `raw_locator_key` | 来源哈希与私有路径键 |
| `cohort_evidence`, `device_evidence`, `device_change_flag` | 证据类型与未知状态，不自动补全 |
| `paradigm_id`, `task_evidence_level` | 任务版本及证据强度 |
| `event_literal`, `stimulus_local_id` | 原始事件码及当前任务内部类别，不跨任务自动共享 |
| `code_map_hash`, `label_semantics` | 映射版本；`literal_only/confirmed_acoustic` |
| `onset_sample`, `onset_seconds_relative` | 连续区间内事件位置；精确访问日期另存 |
| `previous_event_id`, `previous_code`, `previous_gap_s`, `previous_run_length` | **从完整原始事件链计算**，不是 QC 后剩余链 |
| `time_block_id`, `segment_position_fraction` | 预定义时间位置，只作划分/混杂参照 |
| `channel_map_hash`, `original_fs`, `processed_fs` | 几何与采样定义 |
| `preprocessing_id`, `qc_version`, `accepted`, `reject_reason` | 处理和拒绝留痕 |
| `dynamic_condition_unknown` | 设备/配合变化未定位时不能造一个精确切点 |
| `clinical_link_status`, `clinical_assessment_timing_status` | 唯一链接与同期性分别表示 |

另建 `clinical_index.parquet`，保存每个候选的固定索引、年龄、`log1p` 设备月数、明确四频双耳阈值摘要及量表原始值/单位。临床值不得复制成数百条“独立训练标签”。

**Label provenance 单独冻结：** HA 主任务仅为来源内 literal `1/2`；MFF 仅在已确认同一范式/码定义的来源内建立标签。相同数字或字符串不构成跨设备、跨任务同一标签的证据。

### 3.3 三个输入视图，限制可见字段

```text
EEGTrainingView: X, stimulus_local_id, split_group_id(for sampler only), trial_id
HistoryView: X, history_target, observable_context, grouping_keys
ClinicalView: candidate_level_features, clinical_covariates, one_outcome, split_group_id
```

`EEGTrainingView` 不返回临床终点；`HistoryView` 不把预测目标作为特征；所有视图禁止把文件名、姓名、精确日期、候选 ID 和来源路径交给网络。`split_group_id` 的使用必须局限于采样/划分。

### 3.4 数据资格的固定默认值

以下是资源与可估计性门槛，不是临床标准。先用元数据和计数生成支持表，再冻结，不看模型输出调整。

| 场景 | 首轮门槛 |
|---|---|
| 一般二分类试次 | 每条索引记录每类至少 40 个合格试次，覆盖至少 8 个 30 s 块 |
| A 独立半份 | 每个条件、每个半份至少 20 个试次；每半份至少 4 个有支持时间块 |
| B 历史条件 | 主匹配层中，两个历史组每组至少 20 个试次、至少 4 个块；实际训练/测试两类都存在 |
| C 配对比较 | 左/右/联合使用完全相同 trial_id；每名测试候选每类至少 20 个试次 |
| D 临床 | 唯一固定临床链接；主分析每人一条既定索引；主协变量和主终点完整 |
| E 配对探索 | 同人关系可追踪、两个任务明确、各自每类至少 40 个试次；不要求诊断组已知，但不得据此推断组别 |
| 5 折归纳式建模 | 至少 25 个安全划分的候选；20–24 个可用固定 4 折并标记 small_support；少于 20 仅记录级/配对探索 |
| D 嵌套临床比较 | 主完整集合至少 30 个候选；不足时不拟合 64 维临床模型，只做描述和合成测试 |
| E 跨任务群体训练 | 两个任务各至少 20 个安全候选、每个训练折目标任务至少 12 人；否则降为小样本配对技术探索 |

未知诊断不自动阻止技术解码；未知身份会阻止安全的跨儿童验证；未知任务会阻止跨范式解释。这三个条件必须分别处理。

### 3.5 记录选择

HA 主分析沿用既有最早索引，不因其质量或模型分数不佳换后续记录。需要额外 per-paradigm 索引时，在看信号结果前按真实采集时间选择该任务最早记录，另存 `task_index_policy_v1`，不得冒称复用了旧主索引。无法确证事件时钟的记录继续隔离。

## §4 信号处理与信息隔离

### 4.1 三个处理输入版本

| ID | 用途 | 允许的解释 |
|---|---|---|
| `P0_LEGACY` | 旧 ROI/LDA 和既有结果的有限对账 | 旧离线处理条件下的解码；不作新主结果 |
| `P1_CAUSAL20` | A、B、D，以及一般刺激解码 | 因果信号处理后的离线事件条件解码；不自动等于部署验证 |
| `P2_SPATIAL_SPLIT` | C 的主实验 | 两组传感器各自预处理后的条件互补性；不是独立脑源 |

E 对同一采集布局的两个任务使用同一新处理版本；跨布局不是首轮必选项。

### 4.2 主通道集

HA 依据现有配置使用 20 个头皮通道：[D4]

```text
Fp1 Fp2 Fz F3 F4 F7 F8 Cz C3 C4 T3 T4 Pz P3 P4 T5 T6 Oz O1 O2
```

排除 A1/A2 作为模型输入；不把历史耳通道异常当成可利用的个体特征。

MFF 不套用 HA 电极序号。优先按同一原生布局单独训练。需要 20 通道共同映射时，由已有坐标和已验证几何关系建立一对一映射，距离阈值预设 40 mm；某电极不能被重复分配给多个位置。坐标方向、参考虚拟通道和误差必须出表。缺映射时该来源不进入跨布局共同模型；不通过任意插值隐瞒缺失。

### 4.3 `P1_CAUSAL20` 的实现规格

1. 从通过时钟/拓扑门控的原始连续信号读取，保持真实存储缺口；不填零跨缺口滤波。
2. 每个连续区间独立进行固定线性参考；HA 主版本为平均头皮参考。质量资格可用固定离线规则，但禁止根据任务成绩更改。
3. 在原采样率上使用固定单向 SOS IIR：4 阶 Butterworth 高通 0.5 Hz，再接 8 阶 Butterworth 低通 30 Hz；不 `filtfilt`，不反向处理，不作数据驱动相位补偿。
4. 以连续流保持滤波状态；每个真实区间重置。起始保护取 `max(20 s, 实测脉冲衰减保护长度)`，长度由滤波测试确定而不是脑信号成绩。IIR 的“有效支持”按脉冲响应绝对尾和占总绝对和小于 `1e-6` 定义，记录计算长度；这是数值容差，不是数学上的有限支持。
5. 若采样率可整除 250 Hz，低通后按固定原始采样栅格抽取；**不能逐事件重置抽取相位**。其他采样率实现有明确因果支持的流式重采样，否则保留原生采样率并独立处理。
6. 对重采样验证幅频响应、混叠控制、输出时标及 future-perturbation 测试。若默认滤波未达固定反混叠测试要求，先修订配置版本，再导出真实数据。
7. 保存 `[-0.2, 0.5)` s；主解码窗 `[0.05, 0.45)` s；刺激前诊断窗 `[-0.2, 0)` s。事件仅按已知 trigger 对齐，不估计“最优声学延迟”。
8. 不做逐试次基线减法和逐试次方差归一化；全局尺度仅在训练候选上拟合。滤波会改变时序形态和相位，因此不据此命名真实生理潜伏期。
9. QC 规则从既有通过审计的规则迁移为新版本，逐试次留痕。新旧保留集合必须对账，不能把不同处理下的试次数默认为相同。

**因果滤波不等于各窗口独立。** 后续输出含有先前输入的滤波状态；B 的“历史信息”仍需残留信号对照，不能因改成因果滤波就解释成神经记忆。

### 4.4 为什么 C 首轮选择空间划分而不是前后时间窗

两段时间窗即使不重叠，滤波状态和卷积感受野仍可能把前一段带入后一段。为了让首轮信息来源契约容易验证，C 固定使用两组镜像头皮通道：

```text
left  = [Fp1, F3, F7, C3, T3, P3, T5, O1]
right = [Fp2, F4, F8, C4, T4, P4, T6, O2]
midline = [Fz, Cz, Pz, Oz]   # C 主实验不用
```

从原始信号开始，左右各自局部平均参考、各自滤波、各自训练尺度、各自编码。不能先对 20 通道全局重参考、做 ICA/PCA 或共同卷积，再切为左右分支。物理公共参考与体积传导仍可能导致依赖，所以只能称“两组传感器信息”，不称左右脑独立信息。

必须做原始输入干预测试：任意改变右侧原始信号，不得改变左侧处理数组、尺度参数或左侧编码器输出，反之亦然。主评估 trial 集是两侧资格的固定交集；这一选择本身也须报告，不将其外推到所有儿童。

### 4.5 预处理 fit 范围与归一化

每个外折、内折保存 `preprocess_fit_groups`。训练尺度建议为按候选等权的通道中心和标准差；推理使用训练常数。不用整个测试记录估计新的均值、方差或 PCA。

若质量门控沿用全记录离线统计，应显式标为 `offline_record_qc=true`。它不使用标签，但不能包装成只见过去的完整部署流程。A/B 的块级重复/时序实验 additionally 排除跨边界受滤波支持影响的试次，并报告保护时长。

设备伪迹不能靠“解码显著”自动排除。保留来源布局、设备备注、全记录质量和刺激前表现的分层；条件变化无法定位者不进入 A/B/C 的主稳定条件分析，另列敏感性结果。不能用含糊的“约八分钟”自动裁剪。

## §5 训练、验证与跨阶段隔离

### 5.1 外层儿童划分

固定 `split_seed=20260917`，默认 5 个外折。先按 `split_group_id` 分组，再按任务和候选数量做结果盲的平衡；不按临床分数挑一个“更好”的 split。

```text
outer_train_groups ∩ outer_test_groups = ∅
encoder_fit_groups ⊆ outer_train_groups
scaler/PCA/head/tuning/calibration_fit_groups ⊆ outer_train_groups
```

测试儿童的所有记录、任务、试次和增强视图都不参与监督训练或 SimCLR。少量校准/记录内训练仅在显式的独立协议中使用，不能混入归纳式主结果。

### 5.2 内层选择

默认外层训练候选内 3 折用于线性正则、概率校准与临床超参数。深度编码器不在外层测试集早停。监督编码器从外层训练内部固定 20% 候选作 early-stopping validation，最终按所选 epoch 在全部外层训练候选重训；SimCLR 主版本固定 epoch，不用外层测试或临床分数选 checkpoint。

如果内层结果用于选择整个表征/临床流程，内层验证候选也必须从编码器训练中排除。**“不看临床标签但使用了该验证儿童的 EEG”不等于严格的归纳式内层验证。** D 必须重新拟合或安全复用满足这一条件的每个内折表征。若 R_SUP 要早停，再从当前 inner-training 候选内部划分监控组；不能把 inner-validation 同时用作 encoder 早停和临床超参数比较的未触碰验证。也可使用在独立开发数据上预先冻结的固定 epoch，明确记录选择来源。

### 5.3 同记录时间划分

固定 30 s 块，用完整事件时间轴划分，不按接受试次数分块。A 用交替块半份；首尾半份作预定义复核。B 的记录内补充协议、固定头拟合等使用连续块交叉验证，并在训练/测试边界留 `max(10 s, preprocessing_support)` 的间隔。

同一 epoch 的直接取样区间、相邻重叠原始采样区间和增强视图不能横跨两侧。A 的不同半份只是同次采集的分块重复，不是跨日重测；IIR 的有效支持保护也不把它们变成严格统计独立。

任何**训练了该候选的记录内分类头**的严格分块验证，必须先划分连续原始区间，再在各自区间独立重置/执行滤波并舍弃起始保护，禁止把跨训练/测试边界的 IIR 状态带入另一侧。A 的主实验不在测试儿童上拟合 encoder/读出器，可保留连续滤波的分块重复定义，但必须增加首尾半份及独立分段滤波的受限复核；二者不能合写成完全独立重测。

### 5.4 跨折表示坐标不能直接拼接

不同 outer fold 独立训练的 64 维坐标不具备共同语义。禁止把这些折的逐人 embedding 拼成一个表，再拟合一个临床模型或计算跨人距离。

- A：只在同一固定编码器覆盖的测试候选集合内部计算距离/相似度，再汇总标量。
- D：每个 outer fold 在该折编码器坐标中训练临床预测器，最后只合并 OOF 预测与损失。
- E：迁移矩阵的每个设置在同一目标测试折上配对比较损失，不比较不同编码器原始坐标。

### 5.5 数据被看过的范围

Phase 0–3 的数据已经被探索。本轮重复 CV 仍属于新方案的内部探索，不是独立确认集。不得用“重新换 seed”或“重新划分”把数据重新命名为 untouched。首轮发现可推进时，冻结最终假设和分析；新独立记录、外部同类数据或后续真正保留的样本才可提供更强确认性证据。

## §6 共享模型、SimCLR 和训练默认值

### 6.1 表征组

| ID | 定义 | 用途 |
|---|---|---|
| `L0` | 固定 20 ms 时间箱、全通道特征＋训练折标准化＋L2 logistic regression；可用训练折 PCA 至最多 32 维 | 不依赖深度学习的信息可读性基线 |
| `R_SUP` | SmallEEGCNN＋线性刺激头，刺激监督训练 | 主可训练基线 |
| `R_SIM` | 同一 SmallEEGCNN，标准两视图 NT-Xent 预训练，丢弃 projector 后冻结 encoder，另拟合线性刺激头 | 首轮默认对比学习方案 |
| `R_RAND` | 同结构随机冻结编码器，只拟合读出头 | 检查随机映射/维数是否足以解释结果，不作为强方法 |

`R_SUP` 和 `R_SIM` 两条都运行，不能只发布更好的。B 另外允许 `L0_HISTORY` 直接预测历史，避免用只为刺激训练的表征来否定历史可解码性。D 分解的头始终为线性 softmax。

### 6.2 默认小型编码器：不冒称标准 EEGNet

输入 `[batch, channels, time]`。本轮实现命名 `SmallEEGCNN_v1`：

```text
Conv1d(C, 32, kernel=15, padding=7)
GroupNorm(4, 32) -> GELU
Conv1d(32, 64, kernel=9, padding=4, stride=2)
GroupNorm(8, 64) -> GELU
Conv1d(64, 64, kernel=7, padding=3, stride=2)
GroupNorm(8, 64) -> GELU
AdaptiveAvgPool1d(4) -> Flatten(256)
Linear(256, 64) -> representation z
Linear(64, K) -> supervised/probe head
```

无 batch normalization、无跨记录状态；dropout 首轮为 0。GroupNorm 位于编码器内部，不代替原始输入尺度处理，也不保证保留幅值信息，所以保留 `L0` 和幅度敏感性对照。

该网络是本文指定的小基线，不是原版 EEGNet。EEGNet 可作为后续第二种小主干复核，需要注明其官方实现/版本。[R2] 首轮不要求 Transformer、Mamba 或大型预训练模型。

C 的两个分支分别用相同架构、独立参数；联合特征为 `[z_L,z_R]`。B 的当前试次编码器不能输入真实历史标签。所有网络记录参数量和实际输入长度。

### 6.3 固定训练默认值

| 项 | `R_SUP` | `R_SIM` |
|---|---|---|
| seed | 初筛 11；支持路线复核增加 23、37 | 同左 |
| optimizer | AdamW，lr=1e-3，weight_decay=1e-4 | AdamW，lr=3e-4，weight_decay=1e-4 |
| batch | 64 | 128 个原始 trial、每个 2 views；不是 128 views |
| epoch | 最多 80；训练内候选验证 patience=12 | 固定 100，不依据外层测试选 checkpoint |
| schedule | 5 epoch warm-up＋cosine | 5 epoch warm-up＋cosine |
| gradient clipping | norm=5 | norm=5 |
| precision | FP32 为可核查默认；AMP 另存配置 | 同左 |
| representation | 64 维，主结果使用未做逐样本 L2 的 encoder 输出 | 同左 |
| projection head | 无 | 64→128→64，GELU；仅 projector 输出 L2 normalize |
| temperature | 不适用 | τ=0.2 |

首轮不扫学习率、层数和嵌入维数。OOM 时首先缩减 batch 到 64、再到 32，明确记录新配置和实际 batch；**梯度累积不等于更大的 SimCLR 负样本池**。不默默改变比较条件。

### 6.4 采样与 SimCLR 正负样本

监督训练按候选等权、候选内类别平衡采样，避免长记录主导。SimCLR 按候选等权、候选内 trial 均匀采样，不看刺激或临床标签。一个 batch 尽量不重复原始 trial，不含近重复导出；同记录取样间隔至少为 epoch 支持长度，记录实际违反率。

SimCLR 正样本只有**同一个 trial 的两个增强视图**；不同 trial 默认是负样本。相同刺激的不同试次可能成为 false negatives，保留这一局限，不能声称训练目标只保留刺激信息。

同刺激跨试次正样本属于标签辅助/监督对比设计，不属于本轮标准 SimCLR；若后续加入，作为独立消融命名，不混写。[R1, R3]

### 6.5 保守增强

```text
主增强：独立高斯噪声，std = 0.02 × 训练折通道尺度。
两视图独立随机种子；原始 trial 与来源不变。
不做：时间重排、时间翻转、跨通道 permutation、裁剪后拉伸、强幅度缩放、全通道 dropout。
```

噪声增强弱可能使预训练任务过易，这是需报告的风险；不是自动增加复杂增强的理由。固定敏感性只允许噪声比例 0.01 与 0.05，在有现象的路线中追加；不得根据临床终点逐个挑增强。

检查增强前后 trigger、trial_id、通道组和历史标签完全不变。记录 encoder/projector 方差、有效秩、平均余弦和梯度，不仅记录 loss。SimCLR 不能因为 loss 降低就判定学到了听觉信息。

### 6.6 线性读出与校准

Logistic regression 的正则使用 `C=[0.01,0.1,1,10]`，训练候选内选择；拟合权重与评估目标分布一致。主要概率指标保留原始版与训练内 temperature scaling 版，校准只看内层数据，温度在 `[0.25,4]` 约束。

所有比较使用同一测试 trial_id 和类别权重；不得为某个模型单独剔除预测失败的试次。对特征降维、尺度与校准分别保存训练 group 集。

## §7 信息指标、统计与继续条件

### 7.1 主要度量是经验预测信息，不是通用 MI 估计器

给定已有信息 C、新特征 Z、目标 Y，固定模型与划分后计算：

\[
\widehat G_{Z\mid C}
=\widehat{\mathrm{CE}}_2(q_0(Y\mid C))
-\widehat{\mathrm{CE}}_2(q_1(Y\mid C,Z)).
\]

`CE_2` 使用以 2 为底的 log，单位写 `bits/trial of held-out predictive gain`，中文为“留出预测对数损失增益”。它依赖模型、训练、校准和评估分布；**不是无条件等于 Shannon CMI**。[R4, R5]

对于真实分布 p：

\[
\mathrm{CE}_2(q_0)-\mathrm{CE}_2(q_1)
=I(Y;Z\mid C)
+\mathbb E D_{\mathrm{KL},2}(p(Y\mid C)\|q_0)
-\mathbb E D_{\mathrm{KL},2}(p(Y\mid C,Z)\|q_1).
\]

所以基线欠拟合也会增加 G。必须同时有可比较的模型容量、强 context-only 基线和固定试次支持。固定训练模型的结果也不自动等于预测 V-information 中模型类的精确最优值。[R4]

### 7.2 类别和候选等权

刺激二分类的主要 CE 定义为先在每名候选内按两类等权，再在候选间等权：

\[
\mathrm{CE}_{\rm bal}=
\frac1D\sum_d\frac1K\sum_{s=1}^{K}
\frac1{n_{ds}}\sum_{i\in(d,s)}-\log_2q(s\mid X_i).
\]

主描述分数 `J=log2(K)-CE_bal`；可为负，不截断成零。对总体分布且理想条件下它有相应的信息下界关系，但有限样本的 J 不是有保证的置信下界。不同 K、不同任务和不同重加权分布不直接比较 J 大小为功能高低。B 对二元历史组按其明确的匹配评估分布计算，不能偷换为原始 oddball 分布。

同步报告 bAcc、AUROC、NLL/CE、Brier、覆盖候选数、每类试次数和失效状态。AUROC 不是 bit；二分类标签熵最多 1 bit，不叫“整个听觉系统的信息容量”。

D 的 MUSS 主终点使用 MAE、RMSE、R²；没有拟合和验证概率密度时，不把 MAE/MSE 差叫作 CMI 或 bit。

### 7.3 统计单位与区间

- 主统计单位为安全身份组/候选，而不是 epoch、seed、fold 或随机重复次数。
- 对每名候选先在同一 split 下计算配对差异，再汇总；多 seed 平均后按候选重采样。
- 首轮 2,000 次候选 cluster bootstrap 给出固定 OOF 预测的描述性 95% 区间，明确**没有重训完整流程**。
- 有重复访问时同人所有访问共同抽样；E 同人两任务作为一对抽样。
- A 的试次重复抽样用来描述有限试次敏感性，不算新增人数。A 的匹配统计依赖整张对角/非对角矩阵，bootstrap 时在每折内部给候选重采样权重并重算统计；非匹配项始终要求原始 candidate_id 不同，不能把同一候选被重复抽中的副本当作两个不同人。某折有效不同候选少于 2 时，该次重抽样无效并留痕。
- 置换必须说明零假设与交换性。打乱有时序依赖的 trial 标签、打乱临床 Y 后忽略 C，都不自动给出有效检验。
- 条件匹配/循环错位若不能证明交换性，报告 `diagnostic_null`，不输出“精确 p 值”。合成数据的已知随机机制可以做精确校准检查。
- 五条路线的主要检验分别预先固定。需要正式 p 值时，对合法且预先指定的检验做 Holm 校正；探索到哪报哪不能被补做校正自动变成确认性研究。

### 7.4 筛选状态与阈值

初筛的目的为资源分配，不是宣告科学假设成立。

| 状态 | 含义 | 动作 |
|---|---|---|
| `IMPLEMENTATION_FAIL` | 泄漏、数值或数据契约测试失败 | 修实现，禁止解释科学结果 |
| `BLOCKED_INPUT` | 必需的受限输入缺失 | 报缺失键/权限，不造数据；其他路线继续 |
| `SUPPORT_INSUFFICIENT` | 身份、条件重叠或独立人数不足 | 完成代码和可用描述，暂停群体推断 |
| `NEGATIVE_SCREEN` | 当前协议/模型无足够信号 | 留下阴性，不能断言所有模型都无信息 |
| `MIXED_SCREEN` | 效果或控制不一致、区间宽 | 仅执行已经预设的一轮敏感性检查 |
| `POSITIVE_SCREEN` | 主效应、量级、覆盖及关键控制支持继续 | 进入冻结方案复核，不自动启动新方法搜索 |
| `READY_FOR_FROZEN_REPLICATION` | 多 seed/受限敏感性复核仍支持 | 提交下一阶段方案，寻求更独立证据 |

路线自己的效应量门槛见各节。所有阈值在本轮首次真实结果前冻结，属于本项目探索性筛选约定，不是临床有效阈值，也不应压过效应大小、区间和控制的完整报告。

## §8 Idea A：刺激条件化的个体响应表征

### A.1 论文问题与假设

**问题：** 能否从重复刺激中学习到“这个儿童如何响应刺激”的可复现结构，而不仅是普通被试背景或两个统一类别原型？

**H_A：** 在共同的冻结编码器中，去除总体共同刺激对比后，测试儿童的条件响应向量在不重叠时间块之间仍有可复现的个体对应结构；该结构不能仅由预刺激背景或尺度差异解释。

这不是 ERP 波形可靠性任务，也不以“认出儿童”为终点。个体匹配只是检验重复结构的工具。可复现的设备伪迹也能通过匹配，所以临床/另一任务关联和伪迹控制是后续意义验证，不可省略。

### A.2 信息对象与可计算估计

设 `z=f(X)`，只在同一任务的两个固定 local stimulus class 上分析。对候选 d、块集合 h∈{A,B}：

\[
\Delta_d^h = \overline z_{d,1}^{h}-\overline z_{d,0}^{h},
\qquad
r_d^h = L\left(\Delta_d^h-\overline\Delta_{\mathrm{train}}\right).
\]

`mean_delta_train` 按训练候选等权估计；L 为训练候选条件对比上的 8 维 PCA 投影后逐维训练尺度标准化，不做硬截断白化。维数取 `min(8,n_train_candidates-2, numerical_rank)`。r 不是已经识别出的“纯神经个体因子”。

动机来自加性模型 `z=u_d+a_s+b_ds+noise`：条件差分抵消刺激无关的 u_d。但如果个体背景与刺激发生交互或受非线性 f 影响，就不会被完整抵消。因此，背景对照是必要实验，不是公式已经证明可免除的步骤。

同一外折测试候选内定义：

\[
T_A = \frac1D\sum_d \cos(r_d^A,r_d^B)
-\frac1{D(D-1)}\sum_{d\ne e}\cos(r_d^A,r_e^B).
\]

同时报告不做逐向量单位化的内积/平方距离结果，避免只看到方向、遗漏幅值结构。零范数向量按未定义保留，并报告比例，不加任意向量使其匹配。

`T_A` 是重复对应效应，不是 MI。特征维数、PCA 和相似度规则不能在测试儿童上选择。

### A.3 数据与分块

- 首选 HA，每人固定索引记录；MFF 在身份和任务明确的单独层复制。
- 主对比为 HA literal `2 - 1`；不从码数推断频率。MFF 则在每个已确认任务内固定 `devt - stad`，其他码对次要。
- A/B 半份以交替 30 s 时间块构造；在半份边界去除受处理支持重叠影响的试次。
- 若滤波保护宽度导致 30 s 块没有足够内部区域，在看 EEG/临床结果前，将**整条路线所有记录**的块宽统一扩至满足 `block_width ≥ 4×embargo + epoch_duration` 的最小 30 s 整倍数；更新支持表。不根据哪种分块效果更高选择。
- 两个半份的每类试次数统一取 20 作为主预算，按固定 seed 无放回抽样 20 次；40 作为已有支持子集的次要预算，必须报告共同支持集合。
- 首尾半份重复分析为预设敏感性，不替换主结果。

### A.4 首轮步骤

1. 对 `L0/R_SUP/R_SIM/R_RAND` 分别在外层训练儿童中拟合或固定表征。
2. 从训练儿童估计共同条件对比、PCA 和尺度，冻结。
3. 在测试儿童独立块中估计 r，计算 `T_A`、对角/非对角相似度、匹配 rank、范数分布与试次预算敏感性。
4. 每折单独计算匹配；不同折只合并标量，不合并 embedding 坐标。
5. 同时估计未条件化的个体均值 `m_d^h=(mean(z_1)+mean(z_0))/2` 作为背景。
6. 用预刺激片段提取同样的条件对比；检查当前刺激标签是否在事件前已可由序列/处理伪影预测。该诊断不是严格神经零信息对照。
7. 训练候选内拟合 `Δ_post ~ m_post + Δ_pre + mean_pre + quality` 的受正则低维预测，测试上取残差后重复 T_A。此为“可观测背景调整”敏感性，不称因果去混杂。

### A.5 必做对照

| 对照 | 用途 |
|---|---|
| 同折测试儿童半份 B 的候选配对错位 | 估计无个体对应的参考；只在可信可交换分层中计算正式置换 p |
| 未条件化均值 m 的重复性 | 识别“只是普通背景身份可重复” |
| 预刺激条件差异及历史/块位置平衡 | 识别刺激序列可预测性和跨事件污染 |
| 范数标准化与非标准化并列 | 检查匹配是否完全来自信号整体尺度 |
| 相同维数随机投影 | 检查特殊投影是否确有价值 |
| 共同试次预算、同一候选 | 排除多试次/高质量儿童占优势 |

不能以“post 的 p<0.05，而 pre 的 p>0.05”代替直接比较。应报告 `T_post - T_pre` 的配对效应及区间。

### A.6 首轮主判据

默认主设置 `R_SIM, n=20/class/half`；`R_SUP` 为预定平行复核，不从二者中挑胜者替换主设置。

`POSITIVE_SCREEN` 需同时满足：至少 25 个候选有完整主支持；`T_A≥0.05`；固定结果候选 bootstrap 区间下界大于 0；背景调整后的效应仍为正且不是少数一个候选驱动；关键时间/数据泄漏测试通过。这里 0.05 是 cosine 对应效应的探索阈值，不是临床阈值。

若只有未调整 T_A 阳性，而背景/预刺激解释同样强，标记 `MIXED_SCREEN: general_identity_or_sequence`。若只有 `R_SUP` 支持，不自动否定路线，完整标记方法依赖。

### A.7 首轮输出与后续方法

```text
private/.../A/delta_features.parquet
private/.../A/matching_matrices.npz
results/.../A/support_summary.csv
results/.../A/repeatability_summary.csv
results/.../A/background_controls.csv
reports/.../A_screen.md
```

可推进后才考虑：基于独立重复块的条件对比一致性损失，加在普通监督或 SimCLR encoder 上；不预设 FMCA。可研究临床变量之外的响应表征价值，但使用 §11 的独立嵌套临床流程，不能将本节测试儿童选出的响应轴直接拿去训练量表模型。

**可接受结论：** 存在条件化后可重复的个体响应表征。  
**不可接受结论：** 已识别儿童听觉能力、已消除个体身份、已证明反应来自皮层。

## §9 Idea B：听觉历史的条件信息解码

### B.1 论文问题与假设

**问题：** 面对当前相同的事件，EEG 中是否仍存在关于前序声音的可读信息？

**H_B：** 在控制当前事件、前一个事件、刺激间隔和记录位置后，当前试次 EEG 相对这些可观测上下文提高了历史类别的留出预测。

这是观察性条件解码，不把结果直接命名为 prediction error、认知学习速率或因果听觉记忆。

### B.2 历史变量必须在拒绝试次之前计算

在每个已确认连续刺激序列内，用**原始完整目标事件链**计算：

```text
r[t-1] = 在事件 t 之前、以事件 t-1 结尾的相同事件码连续出现次数
H[t] = 0 if r[t-1] == 1
       1 if r[t-1] >= 3
       NA if r[t-1] == 2 or history is incomplete
```

H 是刺激 t 出现前即可确定的变量，不用未来事件、EEG 或临床值生成。真实记录缺口、范式重启、无法辨认的声事件中断历史；不是对所有非声学日志码盲目重置。QC 拒绝一个 EEG trial **不删除那个刺激事件**，否则 run-length 就改变了。

### B.3 固定主匹配层与上下文

首轮优先分析最频繁的固定事件码当前/前一事件组合：HA 为 `current=1, previous=1`；MFF 已知任务为 `current=stad, previous=stad`。该约定在看 EEG 结果前核对码频次与语义；若不满足本意，先做新映射配置，不能凭解码成绩换码。

这种设置让短历史表示“前一事件是一个刚开始的同码序列”，长历史表示“前一事件已经处于较长同码序列”。两组当前与前一事件相同，避免仅解码前一个声音类别。

context-only 输入 C 固定为：

```text
log(previous_gap_s)
record_position_fraction
log(previous_gap_s)^2
record_position_fraction^2
```

若扩展到多个 current/previous 组合，额外加入固定 one-hot 码组合。首轮不能把 run length、由其确定的 surprise 或 H 本身放进 C。

依据训练数据预设 gap 分箱和记录位置粗分层，生成 H×层的支持表，只在共同支持区域报告条件比较。某层单一 H 时标为 positivity failure，不能依靠神经网络外推恢复不存在的对照。

### B.4 核心实验

| 模型 | 输入 | 目标 |
|---|---|---|
| `B0_context_linear` | C | H |
| `B0_context_spline` | 固定低自由度 C 样条/二次项 | H；避免弱 context baseline |
| `B1_pre` | C＋刺激前 EEG 表征 | H |
| `B2_post` | C＋当前窗 EEG 表征 | H |
| `B3_pre_post` | C＋pre＋post | H |

主 gain 为 `CE(B0_context_spline) - CE(B2_post)`。关键支持性结果为 `CE(B1_pre)-CE(B3_pre_post)`；这是相对于可测前段信号的额外预测，不是已经扣除所有过去影响。

使用 `L0_HISTORY`、`R_SIM`、`R_SUP` 三种特征。主表征 `R_SIM`，同时保留线性原始时空特征直接拟合历史；不能只用 stimulus-supervised 的 z 失败就说历史不可解码。

所有读出器在相同外层训练儿童中拟合，测试儿童完全不参与。记录内留块训练的历史头是明确命名的次要 `within_record_calibrated` 协议，不与主归纳结果合并。

### B.5 固定混杂与伪影检查

1. 刺激间隔/记录位置平衡；报告两组分布及共同支持比例。
2. 预刺激和“前一 trial 可观测特征＋C”作为增强基线，检验 post 是否只是先前状态的可读副本。前一 EEG 若被拒绝，历史 H 仍然保留；需要前一 EEG 特征的对照则在预先定义的共同可用子集重算所有被比较模型，报告覆盖损失，不能与全样本 post 成绩直接相减。
3. 当前反应窗口分别使用 `[0.05,0.25)` 和 `[0.25,0.45)` 作为预设诊断；不能挑最高窗口改主窗。
4. 使用正确的原始事件时间，不把重采样后四舍五入偏差或存储边界作为 H 的替代标签。
5. 循环错位只在足够长、近似稳定的同一段内做诊断，明确其不是自动有效的 CMI 显著性检验。
6. 质量信息加入 C 为敏感性而非主处理；如果收益在加入质量后消失，应报告而不是删掉该对照。

历史可能反映感觉适应、前一刺激残留、注意、运动或设备状态。即使 B3 有增益，也不能排除所有这些解释。

### B.6 首轮主判据

至少 20 个候选满足两类历史的支持；主 `G≥0.01 bits/trial`，配对 bootstrap 下界大于 0，且至少 60% 可测候选的主 gain 为正。

若只有 post 相对简单 C 有增益，而相对 pre/previous-response 没有额外收益，标记 `MIXED_SCREEN: history_present_not_current_specific`，仍保留结果，不写成当前声音的新增历史计算。

若 gap/位置共同支持不足，标记 `SUPPORT_INSUFFICIENT: history_context_confounding`，不是“没有历史信息”。

### B.7 输出与后续方法

```text
private/.../B/history_events.parquet
private/.../B/oof_history_predictions.parquet
results/.../B/context_overlap.csv
results/.../B/conditional_gains.csv
results/.../B/pre_post_controls.csv
reports/.../B_screen.md
```

现象成立后，可以研究只保留当前信号相对于历史上下文的新增判别证据；先用简单条件读出或残差表征，不自动开发 Mamba、surprise 模型和全套 cognitive model。

**可接受结论：** 当前实验条件下存在历史相关、在指定模型与上下文之外可读的 EEG 信息。  
**不可接受结论：** 已测量神经记忆容量、已发现儿童预测编码缺陷或康复因果机制。

## §10 Idea C：听觉判别证据的互补与冗余

### C.1 论文问题与假设

**问题：** 两组传感器都能预测声音时，联合输入是否提供其中一组无法替代的判别信息？

**H_C：** 在输入隔离、相同样本和读出容量对照下，左右两组传感器的联合表征在留出数据上优于各自单独表征，并存在可复现的双向条件预测增益。

这里的空间划分只是一个预先固定的可审计分区，不预设左右脑功能机制。若只有单向增益，则另一组可能被一组包含/替代，也属于有意义但不同的结果。

### C.2 严格输入契约

使用 §4.4 的 `P2_SPATIAL_SPLIT`。`z_L=f_L(X_L)`、`z_R=f_R(X_R)`，两个编码器无共享数据依赖；参数可以同结构，但主实验独立拟合。全头模型只作额外基线，不能切其隐藏状态冒充独立视图。

神经原始源之间是否独立不在本节的可识别范围。局部平均参考避免人为混入另一组，但无法消除真实体积传导和共同刺激驱动。

### C.3 主模型矩阵

| 模型 | 输入 | 目的 |
|---|---|---|
| `C_L` | z_L | 左组单独可用信息 |
| `C_R` | z_R | 右组单独可用信息 |
| `C_LR` | [z_L,z_R] | 联合可用信息 |
| `C_LL` | [z_L,z_L] | 与联合模型同输入维数、无新增观测 |
| `C_RR` | [z_R,z_R] | 同上 |
| `C_LR_linear` | 两组表征的线性读出 | 与固定 32 hidden MLP 读出并列 |

所有模型采用同一读出族、相同正则候选和同一测试 trial 集。线性与 MLP 为两个分别报告的族，不能选不同族后把差异全算成信息增益。

`C_LL/C_RR` 是容量/冗余参照，不是完美的有效容量匹配；还需比较单分支头隐藏宽度增加后的固定小型对照。首轮只用 32 hidden，容量检查为 64 hidden，不继续扫宽度。

### C.4 主要量与解释

\[
G_{R\mid L}=\mathrm{CE}(C_L)-\mathrm{CE}(C_{LR}),\quad
G_{L\mid R}=\mathrm{CE}(C_R)-\mathrm{CE}(C_{LR}).
\]

\[
T_C=\min(G_{R\mid L},G_{L\mid R})
=\min(\mathrm{CE}(C_L),\mathrm{CE}(C_R))-\mathrm{CE}(C_{LR}).
\]

主终点 T_C 是相对较好单分支的联合预测增益。同步报告两项 gain，不用一个 min 掩盖方向不对称。

- 两项为正：支持本协议下的双向预测互补。
- 仅一项为正：支持单向新增信息，可能是包含关系。
- 两项接近零：可能信息冗余，也可能联合模型欠拟合/样本不足；不证明真实冗余。

**这些不是 PID 的 unique/redundancy/synergy 分量。** CMI 同时包含 unique 与 synergistic 部分，不可直接将 T_C 命名为 synergy。

### C.5 配套反例与干预

首先通过三个合成任务：两个视图复制同一标签线索；只有左视图有信号；XOR 中两个视图单独无信息、联合有信息。线性头在 XOR 上失败可以是正确的模型类局限；MLP 联合头应能读出，以此验证“模型不可读不等于统计无信息”。

真实数据上在固定联合头内做：左/右置零、同人同类跨块替换、同人不同类替换。零输入/跨类替换可能分布外，所以这些只支持固定模型使用审计，不是原始脑信息量估计。

对 C_LL/C_RR 完成相同干预，检查重复证据是否导致不必要的过置信。概率校准只在训练候选上完成。

### C.6 首轮主判据

默认主模型为 `R_SIM` 独立分支＋32 hidden MLP。至少 25 个完整候选；`T_C≥0.01 bits/trial` 且候选 bootstrap 下界大于 0；联合收益大于仅复制输入/扩展单分支头的收益；输入隔离测试必须精确通过。

如果只有一种读出族支持，标记模型类依赖；如果联合收益只在高维/大头中出现且控制不通过，标记 `MIXED_SCREEN: capacity_or_calibration`。

不要求单分支先都达到某个高准确率；XOR 类互补可能单分支弱。要求的是联合任务相对合法 null 确有可读信息。

### C.7 输出与后续方法

```text
results/.../C/input_isolation_tests.json
private/.../C/paired_predictions.parquet
results/.../C/single_joint_gains.csv
results/.../C/capacity_controls.csv
results/.../C/fixed_head_interventions.csv
reports/.../C_screen.md
```

可推进后研究“保留联合任务信息，而非让每个分支都独立完成任务”的学习目标；首先简单残差/联合监督，再讨论压缩。高维 PID、PoE、脑区组合搜索不是本轮工作。

**可接受结论：** 两组预定义传感器在匹配解码条件下具有预测互补性。  
**不可接受结论：** 已证明左右脑协同机制、某名儿童协同功能受损。

## §11 Idea D：刺激分类头之外的临床功能信息

### D.1 论文问题与假设

**问题：** 足以判断播放了哪个声音的表征，是否仍遗漏了儿童级功能预测所需的信息？

**H_D：** 对固定线性刺激头不可见的表征成分，在年龄、设备经验、听力阈值和该头可见成分之外，仍可提高儿童级 MUSS 的留出预测。

这是旧 CMI-Trace 的“固定头使用”概念向另一个目标的延伸，不是重复 subject erasure。主终点是临床增量，不是零空间还能够解出身份。

### D.2 固定头的精确几何定义

令固定刺激头 `softmax(Wz+b)`，K 类、p=64 维：

\[
M=\left(I_K-\frac1K\mathbf1\mathbf1^\top\right)W.
\]

对 M 做 float64 SVD，取非零奇异值的右奇异向量为 U_v，`P_v=U_v U_v^T`、`P_n=I-P_v`。相对阈值 `max(K,p)×eps64×s_max`；若数值噪声导致近秩问题，报告谱，不按临床结果挑 rank。

用训练特征中心 μ：

\[
z_v=P_v(z-\mu),\quad z_n=P_n(z-\mu),\quad
z_{\rm visible\ only}=\mu+z_v.
\]

应满足 `softmax(Wz+b) = softmax(W(μ+z_v)+b)`，在 float64 随机样本和真实特征上逐点测试 `max_abs_prob_diff<1e-10`；float32 推理另报 ≤1e-6 的数值误差。

**二分类时 rank(M) 至多 1。** 因而 64 维表征里可能 63 维都“头不可见”。临床增量很容易与维度差混淆，必须做降维/随机子空间控制，不能将高维 null 优势直接包装成发现。

分类头不可见不等于 stimulus-independent；新 nonlinear probe 仍可能从 null 中解码声音。该新探针只用于性质检查，不改写原固定头的定义。

### D.3 儿童级特征：小维度，而非把每个 trial 当一个临床样本

主临床特征为每个条件的表征均值：

```text
F_visible = [mean(U_v^T(z-μ) | class0), mean(U_v^T(z-μ) | class1)]
F_null    = [mean(V_n^T(z-μ) | class0), mean(V_n^T(z-μ) | class1)]
```

V_n 是在外层训练候选的 null 成分上拟合的最多 3 个 PCA 方向；按候选等权，不能让长记录决定 PCA。二分类时主 F_visible 最多 2 维、F_null 最多 6 维。临床总 EEG 特征最多 8 维。

每条件均匀使用固定 40 个合格 trial 形成均值，20 次固定重抽样的均值作为同一儿童的稳健摘要；重抽样不是额外样本。真实每类少于 40 者不进入本轮主 D 集合，另报支持损失；禁止为有利候选改预算。敏感性使用所有合格 trial，并报告计数/QC 协变量控制。

主随机对照：从同一 null 空间抽取 3 个 Haar/QR 随机正交方向，固定 20 个随机种子，走相同临床流程。还需全 z 的最多 4 个 PCA 方向×两条件摘要、以及预刺激特征作比较。

### D.4 临床终点与模型

主终点固定为 **HA 原始 MUSS 百分比列**，沿用 0–100 取值说明，不与 MFF 0–40 原始分相混。唯一性、版本和同期性未知的限制写入报告；不声称前瞻康复预测。

主 C：年龄月数、`log1p(device_duration_months)`、明确来源单位的更好耳四频均值。阈值单位未确证时不标 dB HL。[D2]

比较：

| ID | 输入 | 主用途 |
|---|---|---|
| `D0_mean` | 训练 Y 均值 | 最低基线 |
| `D1_C` | C | 临床基线 |
| `D2_CV` | C＋F_visible | 刺激读出可见部分 |
| `D3_CVN` | C＋F_visible＋F_null | 主要新增成分 |
| `D4_CN` | C＋F_null | 分解诊断 |
| `D5_CFULL` | C＋全 z 的匹配维数 PCA | 检查分解必要性 |
| `D6_CRANDOM` | C＋F_visible＋随机 null 摘要 | 子空间/维度对照 |
| `D7_CPRE` | C＋匹配维数 pre 摘要 | 背景信息对照 |

主效应 `T_D=MAE(D2_CV)-MAE(D3_CVN)`，同时要求相对 `D1_C` 不只是从劣化模型恢复原水平。不能只报 D3 对 D2 的收益而隐藏 D3 仍不如临床基线。

使用分组惩罚 ridge，三组惩罚独立：`alpha_C=[0.1,1,10]`，`alpha_V=[1,10,100,INF]`，`alpha_N=[1,10,100,INF]`。INF 表示明确关闭该组，不通过巨大数值近似。由内层 MAE 选择，预测在内层和外层统一截断到 `[0,100]`。必须含完全不使用 EEG 的候选，不能迫使模型使用 EEG。

### D.5 嵌套流程的实现要求

```text
for each outer clinical fold:
    exclude all outer-test identities from every EEG task/record
    for each inner clinical fold:
        choose supervised stopping epoch within inner-training identities only
        fit encoder only on inner-training identities
        fit stimulus head, centering, visible/null bases and PCA there
        build candidate features in that shared coordinate system
        evaluate clinical hyperparameters on inner-validation identities
    freeze all choices
    refit encoder/head/bases/features using outer-training identities only
    fit clinical predictor on outer-training candidate features
    predict outer-test candidates once
aggregate only OOF predictions/losses, not fold-specific coordinates
```

`R_SIM`/`R_SUP` 各自形成一套完整流程，主流程为 `R_SIM`。监督 encoder 见过训练候选的刺激标签是允许的，但没有任何临床标签进入 encoder；整个临床 outer test 始终隔离。

这是最需要额外拟合的路线。不得用“已经有全体 EEG 的 self-supervised features”代替这些隔离。若资源不足，先只完成 `L0` 和一个 outer fold 的完整嵌套 smoke；报告未完成，不用泄漏的 shortcut 冒充结果。

### D.6 控制与解释

- 分解前后固定刺激头预测数值一致，是实现正确性，不是临床假设成立。
- 新刺激 probe 在 null 中仍然可解码时，报告“头不可见但仍有刺激信息”，不删除这一结果。
- 随机 null 与 PCA-null 相当时，只支持“大量未被固定头使用的可用特征”，不支持所选方向特别有意义。
- 若 pre 的临床增量同样好，不可称为“特异的听觉刺激响应功能信息”。
- 同时输出量表上限比例、每个候选误差和删一影响诊断；删一结果只能报告敏感性，不能据此移除不利儿童。
- 不在本轮切换 CAP/SIR/IT-MAIS 为新的主终点。其他终点仅生成覆盖审计，后续单独冻结方案。

### D.7 首轮主判据

至少 30 个完整候选；`T_D≥0.5 MUSS 分`；固定 OOF 配对损失 bootstrap 下界大于 0；`D3_CVN` 相对 `D1_C` 的 MAE 改善也为正；结果不是一个候选或明显量表/身份冲突驱动。

0.5 分仅是探索资源筛选阈值，**不是临床最小重要差异**。若只有 D2→D3 改善而 D3 仍不如 C，标记 `MIXED_SCREEN: recovers_bad_visible_baseline`。只有 R²/相关提高但主 MAE 不支持时不能改主判据。

### D.8 输出与后续方法

```text
private/.../D/fold_projection_artifacts/
private/.../D/candidate_features_by_fold.parquet
private/.../D/clinical_oof.parquet
results/.../D/head_invariance_tests.json
results/.../D/clinical_increment.csv
results/.../D/random_and_prestim_controls.csv
reports/.../D_screen.md
```

确认存在稳定增量后，再考虑“刺激目标与功能目标需求不同”的双目标表征学习。新临床训练头也必须维持儿童级验证；不把本轮调过方向的样本称为确认集。

**可接受结论：** 某固定刺激读出未使用的低维表征，可在指定协变量之外提高探索性功能预测。  
**不可接受结论：** 所有刺激分类器都会遗漏临床信息、null 是纯临床因子、已建立可部署康复预测器。

## §12 Idea E：跨听觉范式的信息充分性

### E.1 论文问题与假设

**问题：** 纯音任务学习到的表征，在音节任务中究竟保留了多少可读信息？缺口能否由有限目标任务调整补充？

**H_E：** 在目标任务确有可读信息、目标读出标签和测试试次相同的前提下，源任务冻结表征相对目标任务表征存在可复现的经验缺口；有限任务残差可补充其中一部分。

经验缺口可能来自有限模型与学习方式，不能等同于真实 Shannon 信息丢失。不同任务的原始 accuracy 不能直接比较为儿童能力差异。

### E.2 先分两级，不强行启动大模型

**E0：配对可行性。** 对当前可确认的同儿童纯音/bapa 配对，完成任务内线性/小网络的分块解码、trial 数和事件语义检查。7 对级别只报告成对点图与宽区间，不写组别效应或训练多任务大网络。

**E1：跨儿童迁移。** 两任务各有至少 20 个安全身份且满足训练折支持时才开展。候选的所有任务共同划分，任一测试儿童不能出现在源预训练或目标训练。

某些记录任务未知，不因其事件码相似就补成纯音或 bapa。只有一份明确 ba1ba4 来源时，不自动增加第三条正式任务线。[D2]

### E.3 匹配输入与任务标签

优先限于 MFF 同一采集布局；不同任务采用相同通道映射、时间窗、QC 和模型容量。若纯音与音节恰好来自不同硬件或源批次而没有重叠，标记 `task_acquisition_confounded`，不能把硬件变化当任务特有信息。

源任务标签记 `S_P`，目标任务标签记 `S_Q`，使用各自 head。`stad/devt` 的字面重合不意味着对应相同物理声音，不能用共享 class ID 强制对齐。

### E.4 主迁移矩阵

对 P→Q 与 Q→P 分别执行：

| 编码器 | 编码器训练数据 | 目标读出头训练数据 | 测试 |
|---|---|---|---|
| `E_P` | 源任务训练候选 | 完全相同的目标任务训练候选及 trial 标签 | 目标任务测试候选 |
| `E_Q` | 目标任务训练候选 | 同上 | 同上 |
| `E_UNION` | 两任务训练候选，任务分头 | 同上 | 同上；作为额外上参照 |
| `E_RAND` | 随机固定 | 同上 | 同上 |

首轮主要比较 `E_P` 与 `E_Q`。训练候选数、每候选 trial 数和训练更新数做匹配，另报使用全部可用训练数据的次要结果。目标训练阶段不能为 E_Q 提供更多**独立目标试次**而隐藏在 encoder 训练里；需完整计数每个模型所有阶段见过的 unique target labels。

`R_SIM` 的编码器不见刺激标签但见源/目标 EEG 域；`R_SUP` 见各自任务标签。因此它们的 exposure ledger 分开解释，不把两种迁移当成相同监督预算。

### E.5 主效应与有限适配

定义目标任务上的经验 gap：

\[
T_E=\mathrm{CE}_Q(h_{P\to Q}(f_P(X_Q)))
-\mathrm{CE}_Q(h_Q(f_Q(X_Q))).
\]

两模型在完全相同 Q 测试 trial 上评分。主要读出族为同一个线性头；固定 32 hidden MLP 为读出容量检查。若增加读出能力即消除差距，则支持读出不匹配，不优先称为表征缺失。

只在 gap 有支持后，开展预设小型适配：冻结 f_P 的早期卷积层，仅调整最后线性表征层或一个 rank-4 adapter，在目标训练候选上训练；与相同 target labels、训练步数的 head-only 方案比较。**只基于 z_P 的 deterministic adapter 不能恢复已经丢失的 Shannon 信息**；它可以改善可读性。因此，“信息补充”若需接触原始 X_Q，必须明确模型获得了新的输入路径，不混同两种情况。

首轮不自动训练共享/私有大网络。需要 raw-input private branch 时作为后续方法阶段，并和同容量目标网络比较。

### E.6 首轮主判据

群体 E1 的主方向为纯音→bapa；逆向完整报告但不因更阳性替代主方向。目标任务 E_Q 的 `J_bal≥0.01 bits/trial` 且相对机会的区间有支持；`T_E≥0.02 bits/trial`，配对区间下界大于 0，并且不是输入布局或 unique target labels 不匹配导致。

若 E_Q 本身不可读，不能解释源表征没有目标信息，状态为 `NEGATIVE_SCREEN: target_decodability_unresolved`。若同一个较强读出消除 gap，状态为 `MIXED_SCREEN: readout_limited`，这仍可引导后续问题但不支持表征信息缺失。

只有 E0 可运行时，输出 `SUPPORT_INSUFFICIENT_FOR_E1`，不妨碍 A–D 完成。

### E.7 输出与后续方法

```text
private/.../E/paired_task_index.parquet
private/.../E/exposure_ledger.parquet
private/.../E/paired_predictions.parquet
results/.../E/task_support_and_confounding.csv
results/.../E/transfer_matrix.csv
results/.../E/readout_capacity_controls.csv
reports/.../E_screen.md
```

可推进后，研究源任务的可读信息与目标任务新增需求，避免无差别跨任务对齐。临床问题可问迁移 gap 是否关联功能，但必须另有足够独立候选，不能用当前少量配对强行训练临床模型。

**可接受结论：** 在匹配目标读出/数据条件下，源学习表征存在经验迁移不足或读出限制。  
**不可接受结论：** 儿童语言处理缺陷、纯音神经编码无法支持语言、已发现因果信息瓶颈。

## §13 分阶段执行、任务矩阵与计算预算

### 13.1 执行顺序：五条都进入首轮，不把某条成功作为其他路线的前提

```text
S0 本地输入与 schema 核验
  -> S1 manifest / splits / 合成与泄漏单元测试
  -> S2 L0 线性基线 + 小样本端到端 smoke（A–E 全覆盖）
  -> S3 R_SUP / R_SIM 一 seed 完整外折探索（各路线达到自身支持门槛时）
  -> S4 冻结筛选报告，判定每条路线状态
  -> S5 仅对可推进/混合路线做预设 seed 23、37 及有限敏感性复核
  -> 交付五路线状态矩阵；新方法阶段另写 v2
```

S0–S4 属于本轮执行目标；S5 可在配置预算内运行，不需要为了已写明的正常步骤再次询问。新增终点、私有数据外传、新增高成本架构或超预算训练不属于本轮。

### 13.2 各阶段完成条件

| 阶段 | 要做什么 | 完成条件 |
|---|---|---|
| S0 | 定位现有根目录、源码、受限产物和环境；只核对本轮需要的字段 | `input_contract.json`；不造缺失字段；可按路线部分 PASS |
| S1 | 去重/身份组、事件完整链、资格、通道图、折划分、预处理测试 | `validation.json` 所有 hard tests PASS；失败输入隔离 |
| S2 | 少量候选 smoke、每条路线的合成正负世界、L0 真实数据检验 | 一条从原始键到报告的可复现路径；smoke 不作科学结论 |
| S3 | 一 seed、全部冻结外折、两种表征及主对照 | 五条各有结果或可复核的支持不足状态，禁止只留最高折 |
| S4 | 聚合、统计、失效原因、确认数据/模型暴露范围 | `FIVE_IDEAS_SCREENING_REPORT.md` 和五行 verdict |
| S5 | 预设多 seed 与单个关键敏感性复核 | 全部原主结果保留，报告复核一致/不一致，不事后换主方案 |

### 13.3 共享缓存范围

安全复用以以下键完全匹配为条件：

```text
source_manifest_hash
identity_graph_hash
preprocessing_hash
train_group_hash
validation_group_hash
task_and_label_map_hash
model_architecture_hash
representation_mode
seed
```

任一项不同就不是同一个合法缓存。尤其 D 的 inner fold、C 的独立空间输入、E 的双任务统一排除集合，不能共享一个“全局 encoder”。

可以共享**结果盲的原始信号导出**和只读 manifest；尺度/PCA/encoder 仍按 fold 拟合。特征文件应有 `fit_scope.json`，加载时自动核对请求的验证集未参与训练。

### 13.4 预期任务矩阵，不等于实际已运行数量

| 子任务 | 首轮范围 | 可共享性 |
|---|---|---|
| 基础 R_SUP/R_SIM | HA，5 outer folds，seed 11 | A、一般 stimulus、部分 B 可共享 |
| D 编码器 | 每 clinical outer fold × 3 inner folds，再 outer refit，两种表征 | 只有 exact group hash 相同才复用；不能省略 inner fit |
| C 编码器 | 2 空间分支 × 两种表征 × 有支持 outer folds | 不复用全头 encoder |
| E 编码器 | 每有支持任务/方向所需的训练集合、两种表征 | 相同任务与排除组时复用；E0 不触发全量训练 |
| B 历史读出 | 固定表征上的 context/pre/post 模型 | 以 CPU 小头为主 |
| A 重复分析 | 每冻结模型 20 次 trial 重抽样 | 不重训 encoder、不增加统计人数 |
| D 统计/随机方向 | 固定 fold 流程中的低维回归 | 不为每个随机方向重训相同 encoder |

先生成 `job_plan.json`，列出每项真实必要训练。首轮最多 100 个 encoder 训练作业；预计超过时先用缓存去重、完成全部 L0 及核心 R_SIM，再输出未完成任务与预算原因，不能偷用不安全的全局预训练替代。100 是研究预算上限，不是需要凑满的目标。

不要做五路线×所有模型×所有损失×所有增强×所有种子的笛卡尔积。

### 13.5 资源和失败处理

- 单训练作业默认 1 GPU，不需要多机/DDP；GPU 型号和分区通过实际探查决定。
- 同时最多 2 个 GPU 训练作业；CPU 处理最多 4 个作业，避免 I/O 竞争和大数组同时展开。
- 长 MFF 继续分块读取，复用已验证流式处理思想；不能一次把四小时全记录转成多个 RAM 副本。[D3]
- 首先估算导出字节数，输出盘空间不足时保留原始只读索引、按记录流式处理；不复制整套原始数据。
- OOM 可在同一配置语义下调整 chunk/batch 并记录；数值/标签错误必须新版本重跑，不把残留输出接到新配置。
- 只允许处理本次作业，不能取消其他项目作业或清理未知目录。
- `squeue/sacct` 的可用性按实际情况记录，不编造 GPU 时间或内存峰值。

## §14 软件目录、命令接口及 Slurm 模板

### 14.1 新实现目录

以下路径是**本方案要求新建的文件**，不是声称当前仓库已经存在这些接口。

```text
<project_root>/
  auditory5/
    __init__.py
    cli.py
    contracts.py
    provenance.py
    adapters/ha.py
    adapters/mff.py
    events.py
    preprocessing.py
    splitting.py
    datasets.py
    models/small_cnn.py
    models/simclr.py
    training.py
    probes.py
    metrics.py
    statistics.py
    routes/route_a.py
    routes/route_b.py
    routes/route_c.py
    routes/route_d.py
    routes/route_e.py
    reporting.py
  configs/auditory5_v1.yaml
  configs/auditory5_site.local.yaml          # gitignored, local paths/resources
  tests/auditory5/
  slurm/auditory5_cpu.sbatch
  slurm/auditory5_gpu.sbatch
  docs/AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md
  private/auditory5_v1/                     # 0700
    inputs/ data/ splits/ features/ models/ predictions/ logs/
  results/auditory5_v1/<unique_run_id>/      # only reviewed aggregate outputs
  reports/auditory5_v1/<unique_run_id>/      # no individual paths/clinical values
```

读取旧脚本时复用验证过的功能，不复制其硬编码旧路径和输出覆盖行为。必要变更应在新 adapter 中完成，不直接改变旧科学结果定义。

### 14.2 CLI 合同

服务器先实现以下接口和 `--help`，再执行生产命令。命令仅演示实现后用法。

```bash
python -m auditory5.cli --config configs/auditory5_v1.yaml preflight
python -m auditory5.cli --config configs/auditory5_v1.yaml build-manifest
python -m auditory5.cli --config configs/auditory5_v1.yaml build-splits
python -m auditory5.cli --config configs/auditory5_v1.yaml test-contracts
python -m auditory5.cli --config configs/auditory5_v1.yaml export-eeg --bank P1_CAUSAL20
python -m auditory5.cli --config configs/auditory5_v1.yaml export-eeg --bank P2_SPATIAL_SPLIT
python -m auditory5.cli --config configs/auditory5_v1.yaml make-job-plan --stage S3
python -m auditory5.cli --config configs/auditory5_v1.yaml run-job --plan private/auditory5_v1/job_plan.json --index 0
python -m auditory5.cli --config configs/auditory5_v1.yaml aggregate --stage S3
python -m auditory5.cli --config configs/auditory5_v1.yaml validate-release
```

这些命令在服务器上必须经 Slurm wrapper 调用，不在登录节点直接运行。`run-job` 读取冻结 plan 中明确的 CPU/GPU 类型、路线、fold、mode 和 seed，不根据之前的结果自动生成不同模型。

### 14.3 必需 CLI 行为

- `--dry-run` 只展示将读取的输入契约、任务计数和输出目录，不打印姓名/私有原始路径。
- 配置缺少原始数据或 private manifest 时退出，写 `BLOCKED_INPUT`；禁止使用公开统计量合成“真实训练集”。
- 输出目录存在时默认拒绝覆盖；`--resume` 仅允许 hash 全匹配且 checkpoint 有完整状态的同任务恢复。
- 依赖任一 hard gate 未通过时不训练；写具体 gate 名称。
- `run-job` 的随机性来自显式 seed，数据顺序与 split hash 可复现。
- 输出 checkpoint 包含模型、optimizer、scheduler、RNG、epoch、fit-group hash；保存前验证没有携带临床原始表。
- 模型/特征默认始终受限保存；`validate-release` 只检查允许发布的汇总产物，不自动 `git push`。

### 14.4 安全启动步骤

下面只做目录、Git 和调度准备，属于允许的登录节点编排。不要对 dirty working tree 自动 stash/reset/clean。

```bash
set -euo pipefail
umask 077
PROJECT_ROOT="${PROJECT_ROOT:-/home/infres/yinwang/EEG_auditory}"
cd "$PROJECT_ROOT"
git status --short
git rev-parse HEAD
mkdir -p private/auditory5_v1/logs reports/auditory5_v1 results/auditory5_v1
chmod 700 private/auditory5_v1 private/auditory5_v1/logs
# Read AGENTS.md / PUBLICATION.md and the referenced existing configs.
# Implement the new module and site-local settings before invoking the commands below.
```

不把上面的默认根目录存在当成保证；缺目录时先定位已有项目，不在错误位置新造一个空原始数据目录。

### 14.5 CPU wrapper 规格

`slurm/auditory5_cpu.sbatch` 的建议内容如下。环境探查应先用已知可用的 CPU Python 做受限小作业；这里的 `PYTHON_BIN` 必须填探查确认的环境。若集群不使用 `CPU` 分区，按本地有效配置替换。

```bash
#!/usr/bin/env bash
#SBATCH --job-name=auditory5_cpu
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
: "${PROJECT_ROOT:?set verified project root}"
: "${PYTHON_BIN:?set verified python executable}"
: "${AUDITORY5_CONFIG:?set frozen config path}"
cd "$PROJECT_ROOT"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
"$PYTHON_BIN" -m auditory5.cli --config "$AUDITORY5_CONFIG" "$@"
```

### 14.6 GPU wrapper 规格

GPU 分区/gres/account 不在文档里猜测。由本地配置传给 sbatch；不存在的 account 不应由代理随便补上。

```bash
#!/usr/bin/env bash
#SBATCH --job-name=auditory5_gpu
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=private/auditory5_v1/logs/%x-%j.log
set -euo pipefail
umask 077
: "${PROJECT_ROOT:?set verified project root}"
: "${PYTHON_BIN:?set verified python executable}"
: "${AUDITORY5_CONFIG:?set frozen config path}"
cd "$PROJECT_ROOT"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
"$PYTHON_BIN" -m auditory5.cli --config "$AUDITORY5_CONFIG" "$@"
```

提交示例（要求 `site.local` 已经确定相关环境变量）：

```bash
# All these are orchestration commands, not local model execution.
sbatch --chdir="$PROJECT_ROOT" --export=ALL \
  slurm/auditory5_cpu.sbatch preflight

# Submit only after the explicit dependency gates passed.
# GPU_RESOURCE_ARGS is intentionally not given an invented value in this document.
# The server agent should construct sbatch as an argument array from verified site settings.
# Example shape, not a ready-to-run GPU command:
# sbatch --partition=<verified> --gres=<verified> [--account=<verified>] \
#   --chdir="$PROJECT_ROOT" --export=ALL slurm/auditory5_gpu.sbatch \
#   run-job --plan private/auditory5_v1/job_plan.json --index <gpu_job_index>
```

wrapper 的 walltime 是调度限额，不是运行时间承诺。依赖控制使用 job ID 和 `afterok` 或读取已通过的 gate 文件，不通过“等一会儿应该好了”启动下一阶段。

## §15 必须通过的测试与反例

### 15.1 数据与信息泄漏测试

| 测试名 | 操作 | 必须结果 |
|---|---|---|
| `test_identity_component_disjoint` | 同人不同任务/导出分别输入 splitter | 都进入同一外折 |
| `test_no_raw_overlap` | 比较两侧 epoch 直接取样区间及滤波来源 | 无重复 trial/直接重叠；记录内训练须独立滤波状态；A 连续块仅按有效支持报告限制 |
| `test_train_groups_only` | 检查 scaler/PCA/encoder/head/calibrator fit scope | 不含 outer test；D inner 也不含 inner validation |
| `test_test_label_mutation` | 任意改测试刺激/临床标签后重建训练产物 | 模型参数、超参数和训练特征 hash 不变 |
| `test_test_eeg_mutation` | 改 outer-test EEG 后重新执行训练步骤 | 训练变换和模型 hash 不变 |
| `test_future_perturbation` | 改时刻 t 之后的 raw | 因果输出在 t 及之前不变到容差 |
| `test_independent_spatial_branch` | 改右 raw / 改左 raw | 另一分支输出不变；全局平均参考错误实现应被抓住 |
| `test_history_before_qc` | 拒绝中间 trial 的 EEG | 后续历史标签仍按原声事件计算 |
| `test_history_reset_gap` | 插入真实存储缺口/任务重启 | 不跨缺口继承 run length |
| `test_history_target_not_feature` | 检查 B feature schema | H/run length/surprise 不进入 context baseline |
| `test_no_fold_embedding_concat` | 尝试拼不同 encoder hash 坐标训练临床头 | 显式报错 |
| `test_no_clinical_to_ssl` | 用带量表列的 manifest 调 EEGTrainingView | 量表不返回、不进入 sampler/augmenter |
| `test_event_semantics` | 任务未知但含 devt/stad | 不自动生成 acoustic label 或 bapa task |
| `test_canonical_only` | 原始与导出副本一起请求 | 不增加训练 trial/儿童数量 |

### 15.2 模型与数值测试

- SimCLR 正样本索引正确、self-pair 从分母排除、双向损失一致、温度和 projector normalize 正确。
- 相同 trial 的两个增强只在当前训练 fold；验证 view 不进入负样本池。
- 训练、恢复后的固定 batch 输出和 loss 在容差内一致；固定 seed 重复稳定。
- 常量输入、一个类别缺失、NaN、空 trial 集、零向量不返回虚假的高分。
- NLL 使用 `log_softmax`；概率报表 clip 仅为显示/指标数值保护，记录 epsilon=1e-7，不用测试集挑 clip。
- CE 的自然对数→log2 转换单元测试，二分类均匀概率 CE=1 bit；完美 toy logits 接近0；负 gain 保留。
- D 分解逐点概率不变；二分类 rank≤1；rank0/退化头给出诊断，不能假装完成正常可见/不可见比较。
- D 的 INF 惩罚确实关闭分组，并精确复现相应低维基线。
- MFF 原采样栅格、gain 单位、virtual reference、通道坐标与边界有最少一个已验证样例；不重写全部读取器。

### 15.3 五路线合成世界

| 路线 | 正向世界 | 反例/阴性世界 | 应验证什么 |
|---|---|---|---|
| A | 共同刺激成分＋稳定个体×刺激交互＋独立噪声 | 只有稳定个体背景与共同类别原型 | 条件对比不把背景匹配误当个体刺激响应 |
| B | 当前 X 显式含 H 成分且当前 S 有共同支持 | H 只与 S/gap 有关，给定 C 后 X 不含 H | 强 context 控制和支持检查能阻止伪增益 |
| C | XOR 或互补独有线索 | 重复副本、只有单边信号 | 区分读出族限制、冗余复制和联合信息 |
| D | W 只读刺激方向，独立 null 方向含 Y−g(C) | null 只含身份/纯噪声，外测试 Y 独立 | 固定头不变不代表临床有效；嵌套控制 false positives |
| E | 源任务目标不同，源压缩丢掉目标独有方向 | 两任务仅可逆重参数化，较强 head 可恢复 | 区分 empirical gap、读出不足与真实构造的信息缺失 |

合成实验使用已知随机生成机制，重复至少 100 次小型模拟估计失败率；不需要训练 100 次大 CNN。设置应包含 SNR/样本量变化，避免只用极容易的正例证明实现“总能成功”。真实数据的科学有效性不能由合成 PASS 代替。

### 15.4 硬阻断与软诊断

信息泄漏、身份污染、分支相互读入、标签字段错误、固定头不变测试失败属于 hard fail。负 gain、低秩、低准确率、宽区间属于需解释的科学/估计结果，不允许简单当作 bug 修到阳性。

## §16 结果文件、报告模板及验收

### 16.1 每个运行都保存

```text
run_manifest.json
resolved_config.yaml
input_contract.json
source_hashes.json
fit_scope.json
environment.lock.json
split_manifest_hash.txt
job_status.json
validation.json
metrics_aggregate.csv
README_run.md
```

`run_manifest` 记录实际开始/结束、commit、配置 SHA256、数据 schema、任务模式、seed、fold、SLURM_JOB_ID 和输出范围。私有逐人/逐试次文件位于 private，公开报告只引用受限键的聚合统计。

### 16.2 聚合指标表 schema

```text
route, stage, experiment_id, preprocessing_id, dataset_scope,
representation_mode, reader_family, split_protocol, seed,
outer_fold, comparison_id, primary_endpoint,
value, unit, ci_lower, ci_upper, ci_scope,
n_candidate_groups, n_records, n_trials,
coverage_fraction, control_status, verdict, limitation_code
```

每项有 `primary_endpoint=true/false`，避免报告时选择性提升次要结果。公开聚合不包含 candidate_id、精确日期、个体临床值及可链接到个人的罕见组合；极小分组只在 private 完整保存，公共版合并或抑制。

### 16.3 候选级配对文件的最低字段（仅 private）

```text
candidate_id, split_group_id, record_ids, task_pair_id,
outer_fold, encoder_hash, comparison_id,
baseline_loss, augmented_loss, signed_gain,
trial_count_by_class, block_support, clinical_link_status,
preprocessing_id, calibration_id, fit_scope_hash
```

记录 `signed_gain` 的正方向；D 的 gain 为 MAE 基线减增强，E 的 gap 为源表征 CE 减目标表征 CE，与 A/B/C 的单位不同，不在一个“总分”中相加。

### 16.4 五路线总报告模板

```markdown
# Auditory5 首轮报告

## 实际执行范围
- code/data/config hash：
- 已完成阶段和作业：
- 未执行部分及具体原因：
- 与方案差异（无则写无）：

## 数据支持
[候选/记录/试次分别统计；身份、任务、设备和量表未知分别列出]

## 共享基线
[L0 / R_SUP / R_SIM；同一折、同一试次；报告所有结果]

## A–E 主结果
| Route | Main endpoint | Effect/interval | N | Key controls | Verdict |
|---|---|---|---|---|---|

## 对每条路线分别回答
1. 现象是否出现？在哪个明确 estimand 和评估分布下？
2. 简单基线能否解释？
3. 哪个关键替代解释尚未排除？
4. 与原 thesis 工作有什么实质区别？
5. 下一步是否值得方法扩展，还是只应补数据/保留阴性？

## 完整性与限制
[泄漏测试、概率校准、缺失、已看过数据、探索性、多重比较]

## 下一步建议
[只列本次证据支持的有限动作，不写自动无上限调参计划]
```

### 16.5 验收条件

交付时必须有五行 verdict，不允许只给“最好路线”的报告。没有运行的部分明确 `NOT_RUN`，不能把代码已写、合成 PASS、Slurm 已提交和真实实验完成混在一起。

服务器还需交付：可运行的实现和测试；全部冻结配置；实际 job_plan；输入/输出哈希；不含隐私的总报告；失败/阴性目录导航；可复跑命令。文档中建议但尚未实现的扩展单独列出，不加入已完成清单。

## §17 后续方法扩展与论文推进条件

### 17.1 不同路线的最小增量方法

| 路线 | 只有现象成立后才考虑的方法 | 需要证明超越的基线 |
|---|---|---|
| A | 对独立重复的条件对比施加弱一致性约束 | 普通监督、标准 SimCLR、背景回归/尺度控制 |
| B | 当前 EEG 相对历史上下文的条件残差解码 | 强 context-only、pre/previous-response 基线 |
| C | 保留联合有用信息的简单融合/压缩 | 单分支、拼接、重复视图、读出容量对照 |
| D | 兼顾刺激可读性与低维功能残差的训练 | 临床基线、全特征低维摘要、随机 null、pre |
| E | 受限目标适配或原始输入任务残差 | 重新拟合 head、同预算目标训练、匹配模型容量 |

不会因为用了 SimCLR、CMI、PID 或信息瓶颈就自动有新颖性。CLASH 等已有刺激配对 EEG 表征研究，[R6] 本项目必须说明所测的是哪种不同的信息对象。论证最终新颖性时再做有针对性的完整文献比较，不在首轮前承诺“首次”。

### 17.2 论文可以如何成立

A/B/C 可以先形成可复现的个体/条件信息发现，但针对 JBHI 仍需说明听觉评估价值；这不是保证任何解码现象都足够投稿。D 需要实际临床增量支持；E 需要足够可信的任务和身份数据。

若多个方向都支持，优先将一个主问题与一个互补验证组织成论文，例如 A＋D 或 B＋C，而不是把五个互不相关的实验硬拼成统一模型。本轮不预先选唯一路线，也不为任何路线保证阳性。

### 17.3 明确禁止的结论跳跃

```text
记录数 != 儿童数
重复试次数 != 临床样本数
SimCLR loss 下降 != 听觉信息增加
HFMCA/相似度分数 != Shannon MI
两个预测器 CE 差 != 精确 CMI
双向条件增益 != 纯 PID synergy
固定头零空间 != 刺激无关或纯临床信息
校准/强读出改善 != 原始脑信号产生了新信息
历史相关性 != 神经预测编码机制
task transfer gap != 因果信息丢失
同次采集重复 != 跨日重测
技术解码成功 != 临床有效性
内部探索 CV != 新独立确认集
```

## §18 配置模板

以下 YAML 是新实现需支持的配置合同。`site_config` 的实际路径/资源在本地创建，不能把下述占位项当作已经定位的数据。路线字段与正文有冲突时以更严格的数据隔离和声明范围为准；应先修正配置并记录，不自行选择更有利解释。

```yaml
project:
  name: auditory5
  version: v1.0
  reference_commit: aac4c366fdaf23507cc5d8b6510f675ae7af615b
  stage: S3
  site_config: configs/auditory5_site.local.yaml
  real_data_execution_status: NOT_RUN
  overwrite: false
  raw_read_only: true
  publish_individual_data: false

paths:
  private_relative: private/auditory5_v1
  aggregates_relative: results/auditory5_v1
  reports_relative: reports/auditory5_v1
  resolve_existing_artifacts_before_training: true

scope:
  routes: [A, B, C, D, E]
  primary_cohort: HA
  mff_replication: eligibility_gated
  clinical_cohort: HA_only
  force_mamba: false
  force_hfmca: false
  allow_large_foundation_model: false
  allow_new_clinical_endpoint_search: false

splits:
  seed: 20260917
  group_key: split_group_id
  outer_folds: 5
  inner_folds: 3
  min_groups_five_folds: 25
  small_support_four_folds_min_groups: 20
  isolate_all_tasks_of_test_identity: true
  exclude_test_eeg_from_ssl: true
  block_seconds: 30
  minimum_embargo_seconds: 10
  enlarge_blocks_by_filter_support_before_results: true
  isolate_inner_validation_from_encoder: true

preprocessing:
  main: P1_CAUSAL20
  complementary: P2_SPATIAL_SPLIT
  output_hz: 250
  epoch_seconds: [-0.2, 0.5]
  main_window_seconds: [0.05, 0.45]
  pre_window_seconds: [-0.2, 0.0]
  highpass_hz: 0.5
  highpass_butter_order: 4
  lowpass_hz: 30.0
  lowpass_butter_order: 8
  zero_phase: false
  baseline_subtract: false
  per_trial_variance_normalization: false
  initial_segment_guard_seconds: 20
  phase_compensation: none
  channel_scaling: training_candidates_equal_weight
  source_clock_uncertain: quarantine
  preserve_rejected_event_history: true

representations:
  modes: [L0, R_SUP, R_SIM, R_RAND]
  primary_learned_mode: R_SIM
  parallel_supervised_mode: R_SUP
  encoder: SmallEEGCNN_v1
  latent_dim: 64
  batch_norm: false
  dropout: 0.0
  first_pass_seeds: [11]
  replication_seeds: [23, 37]
  classifier_C: [0.01, 0.1, 1.0, 10.0]
  temperature_calibration_bounds: [0.25, 4.0]

supervised:
  optimizer: AdamW
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_trials: 64
  max_epochs: 80
  patience: 12
  warmup_epochs: 5
  scheduler: cosine
  candidate_balanced: true
  class_balanced_within_candidate: true

simclr:
  method: two_view_nt_xent
  optimizer: AdamW
  learning_rate: 0.0003
  weight_decay: 0.0001
  epochs: 100
  batch_original_trials: 128
  views_per_trial: 2
  temperature: 0.2
  projector_dims: [64, 128, 64]
  projector_l2_normalize: true
  encoder_output_l2_normalize: false
  positive_rule: same_trial_two_augmentations
  class_labels_in_sampler: false
  noise_std_training_scale_fraction: 0.02
  shuffle_time: false
  permute_channels: false
  crop_resize: false
  strong_amplitude_scaling: false
  clinical_labels_visible: false
  checkpoint_selection: final_fixed_epoch

route_A:
  enabled: true
  stimulus_contrast: local_class1_minus_local_class0
  trials_per_class_per_half: 20
  resampling_repetitions: 20
  contrast_pca_max_dim: 8
  min_candidates: 25
  primary_effect: matched_minus_mismatched_cosine
  screening_effect_floor: 0.05
  background_control: required
  prestim_control: required

route_B:
  enabled: true
  history: previous_run_length
  short_value: 1
  long_minimum: 3
  omit_intermediate_run_length: 2
  main_stratum: current_modal_code_and_previous_same_code
  min_trials_per_history_group: 20
  min_candidates: 20
  history_target_as_input: false
  context_control: required
  prestim_and_previous_response_controls: required
  screening_gain_bits: 0.01
  minimum_candidate_positive_fraction: 0.60

route_C:
  enabled: true
  partition: left_right_sensor_groups
  left: [Fp1, F3, F7, C3, T3, P3, T5, O1]
  right: [Fp2, F4, F8, C4, T4, P4, T6, O2]
  reference: independent_within_group_average
  split_before_preprocessing_and_encoding: true
  readout_primary_hidden: 32
  capacity_control_hidden: 64
  duplicate_view_controls: required
  min_candidates: 25
  screening_joint_gain_bits: 0.01
  claim_pid_synergy: false

route_D:
  enabled: true
  outcome: HA_MUSS_source_percentage
  covariates: [age_months, log1p_device_duration_months, better_ear_4freq_source_units]
  candidate_index: frozen_earliest_index
  min_candidates: 30
  trials_per_class: 40
  trial_resampling_repetitions: 20
  head: linear_softmax
  projection: rowspace_of_class_centered_weights
  null_pca_dim: 3
  random_null_projections: 20
  alpha_C: [0.1, 1.0, 10.0]
  alpha_visible: [1.0, 10.0, 100.0, drop]
  alpha_null: [1.0, 10.0, 100.0, drop]
  prediction_bounds: [0.0, 100.0]
  require_full_nested_encoder_fitting: true
  screening_mae_gain_source_points: 0.5
  must_also_improve_clinical_only_baseline: true

route_E:
  enabled: true
  primary_direction: pure_tone_to_bapa
  reverse_direction: prespecified_secondary
  task_labels_shared: false
  min_candidates_each_task: 20
  min_target_training_candidates_each_fold: 12
  paired_small_sample_fallback: descriptive_E0
  same_test_trials: true
  track_unique_target_label_exposure: true
  screening_target_information_bits: 0.01
  screening_transfer_gap_bits: 0.02
  rank4_adaptation: only_after_supported_gap

statistics:
  aggregate_unit: split_group_id
  primary_class_weighting: equal_within_candidate
  primary_candidate_weighting: equal
  bootstrap_repetitions: 2000
  bootstrap_scope: fixed_oof_predictions_not_full_pipeline_refit
  exact_permutation_requires_exchangeability: true
  keep_negative_information_scores: true
  treat_seeds_as_independent_people: false
  formal_multiple_test_adjustment: Holm_when_valid_and_prespecified

resources:
  max_concurrent_gpu_jobs: 2
  max_concurrent_cpu_jobs: 4
  gpu_per_training_job: 1
  max_initial_encoder_jobs: 100
  copy_entire_raw_dataset: false
  overwrite_or_delete_historical_outputs: false
  auto_expand_to_new_architectures: false
```

### 18.1 配置中 `drop` 的精确定义

`drop` 对应关闭特征组，并使用剩余组重新拟合，不把字符串直接交给数值 solver。解析后保存成枚举，避免 YAML 中的 `INF` 被当作普通文本而静默忽略。

### 18.2 预算降低的唯一允许方式

优先去重合法缓存，其次只完成单 seed 和 L0；不删随机控制、不取消预刺激检查、不减少 D 的必要隔离、不偷偷改测试集合。确实无法完成时明确 `NOT_RUN_RESOURCE_LIMIT`，保留完整待运行 job_plan。

## §19 来源与参考文献

以下资料用于数据依据、研究背景和实现定位；文中所有实验设计、默认超参数与继续门槛均为本方案提出，不声称这些来源已经验证本项目新假设。外部文献只核验与本方案相关的基础内容，不将本节视为穷尽的新颖性审查。

### 19.1 项目文件

- **[D1]** 仓库运行与发布边界：`AGENTS.md`、`PUBLICATION.md`。固定快照：
  <https://github.com/W-Yinghao/auditory/tree/aac4c366fdaf23507cc5d8b6510f675ae7af615b>
- **[D2]** `docs/phase3_report.md`：HA 临床阴性、MFF 计数、任务/身份限制、最终元数据补充。
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/docs/phase3_report.md>
- **[D3]** `docs/PHASE3_ARTIFACTS.md`：受限产物路径、ROI 包语义和流式处理。
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/docs/PHASE3_ARTIFACTS.md>
- **[D4]** `configs/phase1_v1.json`、`configs/phase3_science_v1.json`：原通道、处理、ROI 和旧解码配置。
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/configs/phase1_v1.json>
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/configs/phase3_science_v1.json>
- **[D5]** `slurm/01_inventory.sbatch` 与 `docs/phase0_report.md`：历史目录和环境线索，不替代当前环境探查。
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/slurm/01_inventory.sbatch>
  <https://github.com/W-Yinghao/auditory/blob/aac4c366fdaf23507cc5d8b6510f675ae7af615b/docs/phase0_report.md>
- **[T1]** 用户提供的 `phd_thesis_ipparis_Yinghao_edited(1).zip`；本方案核对了 `learning.tex`、`identity.tex`、`grounding.tex` 的章节定位和固定头定义。
  ZIP SHA256：`59021ffeefb527fc5f58337f9658ea7a2a0538c8c5f6585333ebf8fd9ed8a154`。
  该文件未在此文档中发布或上传到任何外部服务。

### 19.2 方法背景

- **[R1]** Chen, T., Kornblith, S., Norouzi, M., & Hinton, G. (2020). *A Simple Framework for Contrastive Learning of Visual Representations*. ICML/PMLR 119. 用途：标准 SimCLR、encoder/projector 区分、增强定义学习目标；不是 EEG 上稳定性的保证。
  <https://proceedings.mlr.press/v119/chen20j.html>
- **[R2]** Lawhern, V. J., et al. (2018). *EEGNet: A Compact Convolutional Network for EEG-based Brain-Computer Interfaces*. Journal of Neural Engineering. 用途：可选的小型 EEG 网络复核，不将本文 CNN 冒称为原版 EEGNet。
  <https://arxiv.org/abs/1611.08024>
- **[R3]** Khosla, P., et al. (2020). *Supervised Contrastive Learning*. NeurIPS. 用途：说明同类标签定义正样本与实例级 SimCLR 不同。
  <https://proceedings.neurips.cc/paper/2020/hash/d89a66c7c80a29b1bdbab0f2a1a94af8-Abstract.html>
- **[R4]** Xu, Y., Zhao, S., Song, J., Stewart, R., & Ermon, S. (2020). *A Theory of Usable Information Under Computational Constraints*. ICLR. 用途：信息读出依赖模型类；有限训练模型的预测增益不自动等于模型类最优 V-information。
  <https://arxiv.org/abs/2002.10689>
- **[R5]** Poole, B., Ozair, S., van den Oord, A., Alemi, A., & Tucker, G. (2019). *On Variational Bounds of Mutual Information*. ICML/PMLR 97. 用途：避免无条件把高维神经估计结果当精确 MI；本轮不优先实施 MINE/PID。
  <https://proceedings.mlr.press/v97/poole19a.html>
- **[R6]** Accou, B., Van hamme, H., & Francart, T. *CLASH: Contrastive learning through alignment shifting to extract stimulus information from EEG*. arXiv:2302.01924，版本更新至 2024-05-14。用途：同刺激 EEG 配对学习已有先例；本项目 A 必须区分共享刺激信息与条件化个体响应差异。
  <https://arxiv.org/abs/2302.01924>

---

## 附录：首次交接给服务器的执行指令

> 在现有 `W-Yinghao/auditory` 项目中执行本文 v1。先遵守 `AGENTS.md`，保留原始和 Phase 0–3 结果，所有计算/测试经 Slurm。
>
> 不重新发明整个数据审计流程。先解析已有受限来源、候选索引、MFF 元数据补充和本轮必需字段，创建独立的 `auditory5/`、配置、测试及受限产物目录。明确区分本文要求实现的新接口与现有脚本。
>
> 并行推进 A 刺激相关个体响应、B 历史条件信息、C 多源预测互补、D 刺激头不可见临床信息、E 跨听觉任务表征充分性。先完成合成正负对照、输入隔离、身份/时间拆分和固定头数值测试，再做 L0、小型监督 CNN 与标准两视图 SimCLR 的首轮实验。无需 Mamba/HFMCA/PoE/foundation model，不做 ERP 主线，不大范围扫参。
>
> 每条路线按正文固定其主终点和对照。某条身份/任务/临床支持不足时，输出确切状态并继续其他路线。D 的所有临床外测试和内验证身份必须从相应 encoder 训练排除；C 必须原始输入分组后独立处理；B 必须从完整事件链计算历史；A 不跨 encoder 坐标比较；E 必须追踪所有目标标签暴露。
>
> 最后交付五条路线的状态矩阵、主效应与区间、覆盖人数、关键控制、失败/阴性、实际作业和复跑命令。只报告真正运行完成的工作。新方法扩展由首轮证据决定，不将探索筛选包装为确认性临床结论。
