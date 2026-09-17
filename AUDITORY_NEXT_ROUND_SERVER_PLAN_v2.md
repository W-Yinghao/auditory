# 儿童听觉 EEG：下一轮服务器执行方案

**版本：** v2.0 · 2026-09-17  
**项目：** `W-Yinghao/auditory`  
**本轮代号：** `auditory_next_v2`  
**依据快照：** `191b3a189bea116c4c91fdcfcb6d3bd2945b8dfa`  
**性质：** 看过 Auditory5 v1 结果后的有限探索、实现修复与研究对象重定义；不是预注册确认研究。  
**交付范围：** 实现、测试、有限运行、完整汇报。不自动扩展为新主干搜索、大型预训练或临床终点搜索。

> **给服务器执行代理的总指令：** 不重新铺开上一轮 90 个表征任务。复用既有受限输入、身份划分、已完成模型和失败记录；完成 G0 诊断、A2 重设计、C2 修复，以及 N1/N2/N3 三条新路线的最小实验。B-v1、D-v1 归档关闭；E 只进行一次受限的 E0 读出修复，不启动 E1。不能因某条支持不足而中止全部工作，也不能把实现失败写成科学阴性。所有计算在 Slurm 内运行。

---

## 目录

- §0 本轮决定、授权和禁止事项
- §1 已知结果与需要核对的输入
- §2 共享数据、时间与身份契约
- §3 评价分布、拟合隔离和信息指标
- §4 共享读出器与数值修复规范
- §5 G0：定位解码瓶颈，不再盲目训练
- §6 A2：有共同支持的刺激差异及背景校正反例
- §7 C2：完整读出修复与空间信息损失检查
- §8 N1：背景作为刺激读出的条件
- §9 N2：重复试次分布中的声音信息
- §10 N3：刺激序列先验之外的 EEG 证据
- §11 E0 维护与 B/D 关闭规则
- §12 合成反例、泄漏测试与真实数据集成测试
- §13 任务依赖、预算、停止条件和推进判据
- §14 软件接口、配置和 Slurm 入口
- §15 输出文件、最终报告和验收
- §16 依据与参考
- 附录 A：可直接交给执行代理的启动指令

---

## §0 本轮决定、授权和禁止事项

### 0.1 工作包不是五个旧方向原样重跑

| ID | 类型 | 本轮问题 | 首要交付 |
|---|---|---|---|
| G0 | 共享诊断 | 优化、处理、同儿童读出与跨儿童读出分别限制了什么？ | 有边界的解码能力定位表 |
| A2 | 旧 A 重设计 | 在真实共同支持的历史条件内，个体刺激差异是否可复现？背景回归是否会制造残差重复性？ | 支持冻结表、未校正主结果、校正反例 |
| C2-R | 旧 C 数值修复 | 同一左右分支任务能否完成非线性及容量对照？ | 完整读出矩阵，或明确的数值未完成状态 |
| C2-S | 新空间诊断 | 独立局部参考是否丢掉了有用的跨组均值差和中线信息？ | 可逆性测试、空间成分增量 |
| N1 | 新研究路线 | 哪些背景信息是理解当前声音响应的条件，而不只是干扰？ | 背景/响应/联合读出的配对增益 |
| N2 | 新研究路线 | 条件均值之外的重复响应分布是否提供声音判别信息？ | 固定试次数集合的均值与分布比较 |
| N3 | 新研究路线 | 已知事件历史时，当前 EEG 还增加多少当前刺激的预测证据？ | 强序列基线与 EEG 增量 |
| E0-R | 有限维护 | 修复旧 E0 读出后，两个任务内部能否稳定解码？ | 完整族结果或保留失败；不估计 E1 迁移 |

本轮新的论文候选是 **N1、N2、N3**。A2/C2 可以发展，也首先承担定义和实现修复。G0 是定位问题的诊断，不作为普通 cross-subject 论文包装。

### 0.2 明确关闭的工作

- **B-v1 关闭：** 不继续对固定 `run_length=1` 对 `>=3` 的历史标签追加 seed、网络、时窗或新历史阈值。N3 的目标是当前刺激，条件是历史，与旧 B 的目标/条件方向不同。
- **D-v1 关闭：** 不继续“弱刺激头 null 空间 → PCA → MUSS”搜索。不重新扫描 CAP、SIR、IT-MAIS/MAIS 等终点来替代阴性的 MUSS。
- **E1 暂停：** 不因原先 20 人门槛未满足就把 16 人称为完成群体迁移验证。不推断未知任务、不把全部 MFF 当作 CI。
- 不新增 Mamba、HFMCA、PoE、foundation model、PID 高维估计器、脑龄或 ERP 峰值任务。
- 不把新正值反向写入旧报告；不把新的估计对象命名为“v1 复现成功”。

### 0.3 方法立场

信息论用于明确预测对象、条件变量、比较分布和结论边界；不要求每条路线添加 MI/CMI 正则。需要新表征学习时仍可选择简单监督学习或 SimCLR，但 **本轮正式比较默认不训练新编码器**。复用旧编码器并完成固定读出，不等于证明这些表征已经充分提取真实 EEG 信息。

SimCLR 原理和 Deep Sets 可作为方法参考，不是本数据上的有效性结论。[R1–R2]

### 0.4 安全与工作区规则

遵守原仓库 `AGENTS.md`、`PUBLICATION.md`。[D1]

- 原始 EEG、临床、身份、Phase 0–3、Auditory5 v1 输入输出均只读。
- 读取/编辑文本、Git、调度属于编排；数值计算、环境探查、测试、导出、训练、绘图全部经 Slurm。
- 本轮目录统一为 `private/auditory_next_v2/`、`results/auditory_next_v2/`、`reports/auditory_next_v2/`；不要复用旧 run 名。
- 逐人/逐试次资料、模型、特征、原始路径、精确日期、详细日志和身份链接仅存 `private/`；目录权限 0700、文件权限 0600、`umask 077`。
- 聚合结果在本地生成不等于授权发布。**不自动 Git commit/push，不上传权重，不修改共享库版本。** 发布需单独审核。
- 不删除旧失败目录。每次运行记录源码、配置、输入、划分、特征和输出的哈希。
- 缺少受限输入时标 `BLOCKED_INPUT`，只做代码/合成测试；不从 GitHub 聚合表虚构个体数据。

---

## §1 已知结果与需要核对的输入

### 1.1 本轮不是从空白开始

以下是上一轮事实，只作对账，不是 v2 的期待值。[D2–D4]

| 对象 | v1 结果 | 本轮含义 |
|---|---|---|
| 表征矩阵 | 90/90 完成，60 个学习型编码器；173 项模块测试 | 优先复用，不重新训练 90 个任务 |
| 共享 HA 刺激读出 | 58 候选；L0、随机、监督、SimCLR bAcc 均约 52% | 尚无明确学习优势，不推断 EEG 信息为零 |
| SimCLR 共享刺激 J | 0.001739 bits/trial | 很小的已提取信息；不是 Shannon MI 的精确值 |
| 监督共享刺激 J | −0.007549 bits/trial | 预测对数损失较差，不是负互信息 |
| A | 55 候选；主 T=0.013350；共同响应 T=0.447841 | 共同结构很强，差分弱；共同响应不等于纯伪迹 |
| A 历史配额 | 0/55 满足全 24 格；码 2 的部分历史单元近乎结构空缺 | 重做支持对象，不调小配额凑结果 |
| B | 主增益 −0.002169 bits/trial；控制完成 | 关闭旧任务 |
| C | MLP32 主矩阵数值失败；线性矩阵已保存 | 有限修复，不替换成有利的线性结论 |
| D | 51 候选；MUSS 改善 0.10873，区间跨零 | 不再追加同一临床路线 |
| E | 7 对线性 E0；5 个记录×MLP 失败；E1 bapa 16<20 | 维护 E0，不启动群体迁移 |

已有区间是固定 OOF 结果的候选级 bootstrap，不是完整流程重拟合的泛化区间。全部队列已经被探索。1000 组合成结果不等于真实数据上的统计功效或临床验证。

### 1.2 必读与源文件登记

先读、再生成 `SOURCE_REGISTRY.json`，至少登记：

```text
AGENTS.md
PUBLICATION.md
AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md
docs/AUDITORY5_FINAL_STATUS_v1.md
docs/AUDITORY5_EXECUTION_DECISIONS_v1.md
docs/AUDITORY5_REPRODUCTION_v1.md
reports/auditory5_v1/S4_final_001/FIVE_IDEAS_SCREENING_REPORT.md
results/auditory5_v1/S4_final_001/metrics_aggregate.csv
results/auditory5_v1/S4_final_001/control_metrics.csv
results/auditory5_v1/S4_final_001/stimulus_decoding.csv
configs/auditory5_v1.yaml
auditory5/events.py
auditory5/preprocessing.py
auditory5/execution.py
auditory5/probes.py
auditory5/training.py
auditory5/routes/route_a.py
auditory5/routes/route_a_controls.py
auditory5/routes/a_matching.py
auditory5/routes/route_c.py
auditory5/routes/route_e.py
```

已知受限入口须经服务器核对，不根据公共路径猜数据：[D3]

```text
private/auditory5_v1/jobs/plan_001/plan.json
private/auditory5_v1/jobs/plan_001/outputs/
private/auditory5_v1/splits/splits_001/folds.json
private/auditory5_v1/splits/splits_001/support.parquet
private/auditory5_v1/data/<export_run>/
private/auditory5_v1/routes/<source_run>/
```

输出任务目录以 `plan.json` 为准，不自行拼出不存在的 inner 模型路径。必须区分 `outer` 和 `inner` 编码器、`all/left/right` 分支、post/pre 特征与对应 trial ID。

### 1.3 快照和环境

参考 commit 为 `191b3a189bea116c4c91fdcfcb6d3bd2945b8dfa`。若服务器有新代码或未提交改动：不 reset，生成 `SNAPSHOT_DELTA.md`，仅核查影响本轮的接口和结果，再冻结新快照。

历史工作区为 `/home/infres/yinwang/EEG_auditory`，原始数据根为 `/projects/EEG-foundation-model/auditory`，旧环境为 `/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python`。这些是待核对的历史入口，不是强行覆盖配置的依据。[D3]

环境探查记录已安装版本、BLAS 线程、CUDA 和有效 Slurm 分区。官方在线文档可能对应不同版本；C2 的数值目标必须与 **服务器已安装实现** 核对，不为了匹配网页自动升级。[R4]

### 1.4 状态以完成回执为准

旧配置中的 `NOT_RUN`、旧复跑说明中的 `queued/interim` 可能是保留的历史文字。以指定完成回执和最终报告为准，不重新提交已经完成的 worker。[D2–D3]

---

## §2 共享数据、时间与身份契约

### 2.1 数据范围

主队列仍为 HA，使用已冻结的最早候选索引和保守身份连通组。所有同一 `split_group_id` 的记录/任务/导出版本不得跨外层训练与测试。

MFF 不进入本轮新三路线的主训练；只用于 E0-R 的已有可支持记录。身份不明或设备条件变化的记录保留审计标签；不按新的解码成绩选择版本、移位事件或删除儿童。

### 2.2 复用的主信号

- 默认复用 `P1_CAUSAL20`、250 Hz、post `[0.05,0.45)` 秒、pre `[-0.2,0)` 秒。
- 不新增 baseline subtraction、逐试次方差归一化、相位补偿或按结果挑时窗。
- P1 与旧 Phase 1 不是同一预处理版本；不能把不同版本的好坏归因于一个算法。
- C2-R 复用 `P2_SPATIAL_SPLIT` 的真实左右独立处理。
- C2-S 只从有限的 HA 原始/受限导出重新构造规定的空间成分，不复制整套原始数据。
- 所有主对照使用完全相同的测试试次。两个处理版本共同支持集上的比较与各自可用全集的描述必须分开。

既有因果滤波的有效支持测量约为 10.823 s，启动保护为 20 s；实际值从冻结处理元数据读取，不硬编码为普适常数。[D4]

### 2.3 所需事件字段

新增分析表可复用旧字段，但语义必须逐项登记：

| 字段 | 含义 |
|---|---|
| `trial_id` | 稳定的事件主键；不得因是否通过 QC 重新编号 |
| `record_id / segment_id` | 真实来源与连续存储区间 |
| `candidate_id / split_group_id` | 候选身份与保守划分身份；不是临床确诊 ID |
| `event_literal / stimulus_local_id` | 字面事件码与任务内标签；不自动赋予频率或语言学含义 |
| `onset_sample / original_fs` | 原始采样轴上的触发点 |
| `accepted / qc_reason` | 本版本主 QC 状态与拒绝原因 |
| `previous_event_id / previous_code` | 上一个真实声音事件，包括 EEG 被拒绝者 |
| `previous_run_length` | 结束于上一声音的连续同码长度，不含当前声音 |
| `previous_gap_s` | 当前与上一声音的间隔 |
| `history_reset_reason` | 存储缺口、重启、未知声音等断链依据 |
| `segment_position_fraction / A_block_id` | 离线位置、块标识；不得输入身份字符串 |
| `feature_scope_id / encoder_scope_hash` | 该特征由哪个训练范围的编码器生成 |
| `raw_dependency_start/end` | 当前特征/QC/上下文所依赖的原始时间支持 |

历史必须从 **QC 前的完整事件链**计算。删掉当前 EEG、改变当前标签或打乱接受掩码，不应反向改变当前之前的历史。

### 2.4 N1/N3 的历史条件 H：严格不含当前标签

默认 `H_v2` 包含：

1. 前 3 个已知声音的字面码（任务内 one-hot），缺失/未知单独编码；
2. `log1p(previous_run_length)`、run bins `{1,2,3–5,>=6,unknown}`；
3. 最近最多 3 个已知声音间隔的 `log(gap_seconds)`，缺失指示；
4. 当前与上个声音间隔的二次项、记录位置线性/二次项；
5. 原来已确认且预先允许的布局/采样率类别；HA 内常量列删除。

允许过去事件形成的组合特征；**禁止**：当前码、`current_run_length`、`current==previous`、当前是否 deviant、下一刺激、距离下一事件的时间、按当前标签挑选的上下文、MUSS、年龄、设备经验、身份字符串。

`segment_position_fraction` 使用全记录长度，因此仅能支持离线分析；不宣称在线部署。位置敏感性另用“从段首到当前的已逝时间”替代，作为固定一个对照，不搜索多种位置函数。

对未知声音/真实重启遵循旧历史断链规则，不因间隔大就自行假定存储缺口。[D5]

**不要把旧 B 的二分类筛选当作新历史完整性规则。** `history_target` 在 run=2 时为空、`history_status=excluded_run_length_2` 只表示旧 B 不使用该中间组；N1/N3 允许有确切 `previous_run_length=2` 的记录，不因旧字段为空就丢弃。真正未知的历史与旧任务人为排除必须区分。A2 仍按自己预定的 run>=3 区域筛选。

### 2.5 时间隔离

外层留儿童保证人级隔离；涉及同儿童校准、分半重复、bag 稳定性及 E0 时，额外保证：

- 使用原始时间块，不随机拆相邻 trial。
- 合并直接 epoch、滤波状态、上下文和历史辅助信号的依赖区间，再检查训练/验证/测试是否相交。
- N1 当前试次的 pre 和 post 本来允许属于同一个观测；它们相关不算泄漏，但不能当作独立神经来源。
- 同儿童训练/测试边界至少用实际滤波支持的 embargo；预先验证边界重置后的等价范围。不因保护后支持少，就减小保护区。
- 同一 trial 的所有 bag、增强视图、编码版本和替代上下文必须随原始划分一起移动。

---

## §3 评价分布、拟合隔离和信息指标

### 3.1 外层划分不变，不能用旧特征省掉内层隔离

沿用 v1 的 5 个身份外折。路线资格可以变，但不为好成绩重新划分。

**新 N1/N2/N3 的主要可调读出：** 优先复用对应的既有 inner `all` 编码器；每个 inner 编码器不得见到该 inner 验证儿童。分别拟合 scaler、PCA、head、校准，在自己的特征坐标中评估。最后只汇总预测/标量，不把不同折 embedding 拼起来训练。

如果缺少合规 inner 特征：

- 不把 outer-trained embedding 冒充完整 nested；
- 可以在合成数据上冻结唯一的 head 参数后，进行 `FIXED_HEAD_OUTER_EVAL`；
- 或保留旧 C 式 `FROZEN_FEATURE_INNER_ONLY` 作为有明确范围的修复结果；
- 不自动重训几十个 inner 编码器。需要新增真实编码器训练时，本轮停止该扩展并报告缺口。

C2-R 的主要目的为完成原来的有限读出过程，保留旧“outer encoder 固定、inner 只拟合读出”的范围。这不是 outer test 泄漏，但不能宣称整个流程都严格内嵌重训。

### 3.2 两种评价分布不能混用

**P_bal：** 每名候选等权、候选内两个刺激类别各占一半。

\[
L_{bal}(q)=\frac1D\sum_d\frac12\sum_{s=0}^{1}
\frac1{n_{ds}}\sum_{i\in(d,s)}-\log_2 q(s\mid x_i).
\]

用于 G0 的主要刺激读出、C2、N2。可报告 `J_bal=1-L_bal`。

**P_nat：** 每名候选等权，候选内保留当前合格记录的自然类别比例。

\[
L_{nat}(q)=\frac1D\sum_d\frac1{n_d}\sum_{i\in d}-\log_2q(s_i\mid x_i).
\]

用于 N1/N3 的主条件预测增益。训练、调参、校准和测试都使用对应分布的权重。这里的“自然”仅指合格记录内的观测分布，仍受来源和 QC 选择限制，不是整个临床人群的自然分布。

N1/N3 另做 `P_bal` 敏感性：单独拟合/校准，不只给自然分布模型换测试权重。**不能因改变类别比例就继续使用原历史先验而不说明失配。** 不使用测试类别比例拟合先验或概率变换。

### 3.3 主要指标

统一采用测试逐观测对数损失，先候选内汇总，再候选等权：

\[
G_{X\mid C}=L(q_C)-L(q_{C,X}).
\]

- 正值表示指定模型与评价分布下的经验预测增益。
- 负值原样保留；不能裁剪为零。
- 不称为精确 Shannon CMI、神经信息容量或因果信息流。
- 两个不同模型损失之差不是互信息下界之差所自动提供的 CMI 下界。
- `CE_bits` 用 `logsumexp` 或数值稳定的 log-probability 计算；不从被四舍五入的概率反推 logit。
- bAcc、候选宏平均 AUROC、Brier 和校准诊断同时报告；Brier 是否双类求和必须写清楚。
- A2 的余弦匹配差和 N2 的 bit/bag 与 bit/trial 不同，不做跨路线“总分”。

预测信息与读出能力有关的理论背景见 [R3]。

### 3.4 先验和校准

C2-R 为数值修复，保留旧温度范围 `[0.25,4]`、候选权重和 alpha/C 网格；不在同一个修复里同时换概率目标。

G0/N1/N2/N3 使用以下固定方案：

1. 主校准为训练内 OOF logit 的单温度，范围 `[0.25,16]`；
2. 同时报告 raw；温度触边计数单列；
3. 固定一个诊断：`q_mix=(1-eta)q+eta*pi_train`，`eta∈{0,0.25,0.5,0.75,1}`，只在训练内 OOF 选择；它不是替换主结果的“修好信息量”；
4. `pi_train` 由相同评价权重下的训练标签估计；在 P_bal 下为 0.5，在 P_nat 下为训练候选等权的比例；
5. 无法产生合规训练内 OOF 时固定 `T=1,eta=0`，明确 `UNCALIBRATED_FIXED`，不读取测试标签补校准。

`q_C` 与 `q_{C,X}` 分别校准。主要判读检查收益是否只来自概率收缩；不得将只改善校准称为恢复了新的神经信息。

### 3.5 不确定性和多重探索

- 所有正式区间：2000 次候选 cluster bootstrap，成对使用完全相同的候选抽样。
- 重复 bag 分组、A2 试次抽样、随机 seed 均先在候选内平均，不能当成新增儿童。
- A2 匹配矩阵在原特征折内做身份 bootstrap，重复抽到的同一身份不能算“异人配对”。
- 明确 `fixed_oof_no_refit`，不声称包含了重新训练与研究选择的全部不确定性。
- 对缺失/失败候选不补零、不插值。主模型比较使用冻结的共同资格集合，数值失败不得事后删人保完整表。
- 对只有观察性时序依据的 label/circular permutation，仅作诊断；没有交换性证明不报“精确 p 值”。
- 不用重跑交叉验证把已看队列变成确认集。任何论文级确认需要后续独立证据。


## §4 共享读出器与数值修复规范

### 4.1 不把 L-BFGS 警告改成静默成功

旧 C/E 使用单隐藏层 ReLU MLP、L-BFGS，达到规定迭代上限后仍有收敛警告。它是数值未完成，不是科学阴性。[D6]

新增 `auditory_next/readouts.py`，保留旧模块不变。修复必须满足：输入、标签、权重、分割、结构、正则目标可追溯；只改变求解过程时标 `SOLVER_REPAIR`。若改变正则归一化、激活、特征压缩或模型矩阵，则另标 `NEW_ESTIMATOR`，不能称为同一个估计器复算。

### 4.2 C2-R 的目标函数等价性

对服务器安装的 sklearn 源码核对：数据项是否按权重和归一化、L2 是否除以权重和、是否惩罚 bias。不要仅凭网页上的“alpha”文字猜公式。

目标应以实际旧实现为准，并在 `OBJECTIVE_PARITY.md` 写出。通常需要检验以下形式，而非直接假定它正确：

\[
\mathcal L=\frac{\sum_i w_i\ell_i}{\sum_iw_i}
+\frac{\alpha}{2\sum_i w_i}\sum_l\|W_l\|_F^2.
\]

在相同参数上比较 sklearn 与新实现的 data loss、penalty、logit 和梯度；CPU float64 小型测试默认容差 `1e-7`，有限差分梯度相对误差 `1e-5`。二分类单 logit 与双类 logit 的差异只允许相差公共平移，不允许改变 softmax 温度。

**禁止**以 AdamW 的 decoupled weight decay 冒充旧的显式 L2 objective。需要精确等价时在 loss 中显式加入罚项，优化器 `weight_decay=0`。

### 4.3 求解器

C2-R 与 E0-R 新主求解器固定为：

```yaml
solver: torch_adam_full_batch
precision: float64
activation: relu
hidden: 32               # 容量对照 64，结构按旧模型矩阵
learning_rate: 0.001
weight_decay: 0           # 正则在 loss 中显式加入
steps_initial: 1000
steps_extension: 1000     # 全局预定的唯一延长，不是逐人救结果
schedule_horizon_steps: 2000  # 启动前固定，延长时不重启 scheduler
learning_rate_schedule: cosine
gradient_clip_norm: 5.0
seed: 11
```

full-batch 可分 microbatch 累积梯度，但必须累积 **整个训练集归一化后的加权 loss**，每轮只更新一次。不能对每个 microbatch 分别归一化后等权累积，否则候选权重可能改变。

保存每步/每固定间隔 objective、未裁剪梯度范数、参数范数与训练预测。2000 步是预算上限，不是数学收敛证明。

优化完成至少要求：参数/梯度/logit 全有限、无爆炸、objective 不劣于相同初始化、最后 100 步 objective 相对变化稳定在 `1e-4` 以内。使用这个停止判据只说明 `OPTIMIZATION_STABLE`，不声称达到全局最优。零信息合成例中常量模型可以稳定完成，不能要求“准确率够高”才叫成功。

在同一个完整比较族中，1000 步先只读取训练数值诊断，不打开测试成绩；只要其中一个规定成员未稳定，就将该族全部成员统一续算至 2000 步，scheduler 的 2000 步 horizon 从启动前固定，不能在延长时重启。若最终仍不稳定，保留 `OPTIMIZATION_UNRESOLVED`，不自动换第三个 solver、不读取测试表现决定延长。

### 4.4 读出范围和超参数

| 包 | 主读出 | 参数范围 |
|---|---|---|
| G0 | 原 logistic、原监督网络头、必要时 MLP32 | 复用旧选择；新增 logistic 的 C 为 `[0.01,0.1,1,10]` |
| A2 | 固定训练内 PCA/缩放及匹配统计 | 主维数上限 8；不按临床值选方向 |
| C2-R | 原 linear、MLP32、单侧 MLP64 | 原 4 值网格；C 与 MLP alpha 方向不同，不混用 |
| C2-S | logistic 主，MLP32 次 | 上述 4 值，保持全部对照 |
| N1/N3 | logistic 与 MLP32 | C/alpha 各 `[0.01,0.1,1,10]`；MLP 选择只用内层 |
| N2 | logistic 主，MLP32 固定次要 | 同上；主结果不能被次要模型替换 |
| E0-R | 旧 linear＋修复 MLP32 | 原有标签、原有原生布局与时间块 |

新 N1/N2/N3 可使用显式平均加权 loss 加 `lambda/2*||W||²`，但命名为 `lambda`，与 C2-R 旧 alpha 不共用数值语义。默认新 MLP `lambda∈{1e-4,1e-3,1e-2}`，不是上表的 sklearn alpha；配置中必须二选一明确 `objective_id`，不得把两个网格叠加搜索。**本文件默认新路线采用显式 lambda，C2/E0 修复采用旧 alpha。**

### 4.5 控制“增加参数”与“增加信息”

涉及联合输入时，必须有同维度/同宽度的重复输入控制，例如 `[P,P]` 与 `[P,B]`；不同维度先使用训练内独立压缩达到指定同维度。复制输入可能改变正则的有效强度，因此重复输入是控制，不是数学等价保证。

新联合模型若只在更大宽度下有收益，需标记 `CAPACITY_SENSITIVE`，不能直接归因于条件信息。新增分支允许训练内选择完全不使用（零增量或基础模型为一个候选），但测试增益仍可能为负。

---

## §5 G0：定位解码瓶颈，不再盲目训练

### 5.1 G0 必须先完成的对账

从原 `execution_status_003`、特征、probe 元数据及模型 checkpoint 核验：

1. 原共享表中 R_SUP 是“监督编码器＋重新拟合 logistic probe”，不是必然等于端到端网络原 head；两者分开评估。
2. 每个 outer/inner 编码器的训练范围、selected epoch、监督 monitor loss、最终 loss、梯度与 effective rank。
3. R_SIM 的 encoder 输出与 projector 输出区分；本轮分析 encoder，不把 projector 的不塌缩当成刺激信息有效。
4. 先复算旧 58 人共同表，允许浮点容差，不允许按某模型成功与否删人。
5. 监督训练是否已经可以拟合训练标签；同候选的标签平衡是否与预期一致；输入量纲和窗口是否正确。

### 5.2 最小能力定位矩阵

| 评估 | 输入/训练范围 | 用途 |
|---|---|---|
| `TRAIN_DIAGNOSTIC` | 编码器真实训练儿童的训练试次 | 只看拟合与优化，不作为泛化 |
| `OUTER_SHARED` | 原 5 外折测试儿童，复用旧模型与 probe | 对账和共享可读性 |
| `WITHIN_CHILD_READOUT` | 外层未见儿童的前段试次拟合小读出，后段独立块测试 | 判断固定表征是否有个体内可读信息 |
| `FIXED_FEATURE_INJECTION` | 合成已知信号通过真实维度/权重/划分 | 检查估计器在接近当前规模时能否检出信号 |

`WITHIN_CHILD_READOUT` 不训练新 encoder。使用该儿童所属外折的合规 L0、R_SIM、R_SUP、R_RAND 特征，编码器从未见该儿童。按带 embargo 的真实块，前 60% 完整块为校准，后 40% 为测试；两部分每类至少 20 个试次、各覆盖至少 3 个块。选 C/校准参数只能使用其他训练儿童的同样任务，不能在本儿童测试部分调参。

在同一后段测试集比较共享读出与个体校准读出。若资格不足，标 `SUPPORT_INSUFFICIENT`；不改成随机 trial CV。小样本校准不是真实信息上限，失败也不能解释成儿童听觉能力不足。

### 5.3 处理敏感性只做一个有限桥接

主输入不变。仅用 L0 比较 P1 因果处理与一个已经有完整溯源的离线处理版本；同 trial、同身份折、同读出族、同指标。

- 如果旧版本仅有不同信号/事件轴且无法一一对应，不运行，记录 `NOT_COMPARABLE`。
- 离线零相位结果仅是整段解码诊断，不能用于 N1/N3 的先后信息或未来可用性主张。
- 同时输出滤波 impulse/group-delay 说明和固定窗口覆盖；不根据标签挑最佳触发偏移。
- 不把“因果处理分数较低”自动归因为延迟；它还可能改变频谱、边缘及参考。

### 5.4 G0 结果怎样影响后续

- 训练都拟合不了且基本量纲/标签失败：修数据/实现，受影响学习表征分支暂停；L0 合规路线仍继续。
- 训练可拟合、同儿童好、跨儿童弱：支持研究条件化读出；不是证明个体神经信息充足。
- 同儿童与跨儿童都弱：N2 仍可研究重复分布；不要立即增加编码器规模。
- 随机/L0 与学习表征相当：继续把它们作为必要对照，不能因不利而移出正文候选。

**G0 不设“bAcc 超过某数才允许全部研究”的统一门槛。** 它必须输出诊断结论，不能成为重复审计循环。

---

## §6 A2：有共同支持的刺激差异及背景校正反例

### 6.1 与 A-v1 的区别

A-v1 主 T 弱，而且全历史×位置配额没有共同支持。本轮不降低旧配额重新宣称 A-v1 通过。A2 的新估计对象为：

> 在前一个声音为字面码 1、此前连续同码长度至少 3，且两种当前声音都具有观测支持的历史/位置子区域内，学习表征的条件差异能否跨块匹配同一候选？

这是对**指定事件上下文中的响应差异**的研究，不是所有听觉历史下的个体特征。

### 6.2 支持选择必须在查看新 EEG 效应前冻结

使用完整历史链，加当前 QC/块资格；不读取特征、预测或临床值。基本区域：

```text
previous_code == literal_code_1
previous_run_length >= 3
history chain complete
existing A block/embargo requirements passed
```

将该区域分成 4 个预定 cell：`run=3–5 / >=6` × `position=前半 / 后半`。

避免重新要求所有人覆盖全部四格，采用以下唯一、确定性的支持冻结算法：

1. 枚举四格中包含至少 2 格的子集 Ω，共最多 11 个候选区域；不枚举更多分箱。
2. 候选在 Ω 每个 cell、两个当前类别、两份独立块中各至少 6 个试次，并且每个 half×class 在 Ω 内合计至少覆盖 3 个原 A 块。
3. 选择满足至少 25 个候选、每个旧外折至少 2 个测试候选、每折至少 12 个训练候选的 Ω。
4. 优先选 cell 数最多者，再选候选数最多者，再按固定 cell ID 字典序决胜。
5. 没有满足者时，不自动降到一格或减少配额。可以对同一算法得到的最大支持结果做 `DESCRIPTIVE_ONLY`，但不宣布主 A2 完成；其他新路线照常继续。

这种全队列 **事件元数据驱动的研究设计选择** 不使用 EEG/临床结局，但使用了实验标签计数；必须在报告里披露。它不是纯 source-only 部署设计。冻结后不得根据 EEG T 值换 Ω。

### 6.3 所有人使用同一个条件分布

冻结统一 `q(c)=1/|Ω|`。每个候选、每个 half、每个 class、每个 cell 抽 6 个试次，固定 20 次重复抽样。

\[
\Delta_d^{(h)}=\sum_{c\in\Omega}q(c)
\big(\bar Z_{d,1,c,h}-\bar Z_{d,0,c,h}\big).
\]

**禁止**每个候选使用自己的 Ω 或 cell 权重后再做身份匹配；否则“哪些 cell 有数据”本身可能成为候选指纹。

scaler、均值中心和至多 8 维投影只由该外折合格训练候选拟合。所有模型使用同一 Ω、同一试次抽样、同一候选集。主 R_SIM，L0/R_SUP/R_RAND 平行。

### 6.4 A2 主终点与有限次要结果

主终点为未做背景回归的 matched-minus-mismatched cosine，沿用折内匹配/候选 bootstrap。输出：

- `T_delta_unadjusted`：主；
- 同一统计在 pre 条件差异中的结果及 post−pre 配对差；
- 两类 post 平均的共同响应匹配，名称写 `common_response`，不再标“纯背景”；
- 内积版本和向量范数，仅作尺度诊断；
- 本轮仅使用冻结的交替块半份；不额外要求与 Ω 的位置条件相矛盾的全记录前/后半配额。跨时段可读性由 G0 的独立诊断处理，不与本 T 合并。

主筛选量级仍为 T=0.05，仅为继续投入的研究约定，不是临床阈值。阳性需要同时说明共同支持和 pre 对照，不能只引用一个 bootstrap 下界。

### 6.5 背景校正：作为被审计对象，不作为新的主终点

旧校正路径的思想：`R_h=Delta_h-P_h`，其中 `P_h=g(B_h)`，B 含共同响应、pre 信息、质量摘要。

必须同时输出 `Delta`、`P` 和 `R` 的匹配统计。对线性内积（不要对 cosine 硬套）核对：

\[
\langle R_1,R_2\rangle
=\langle\Delta_1,\Delta_2\rangle
-\langle\Delta_1,P_2\rangle
-\langle P_1,\Delta_2\rangle
+\langle P_1,P_2\rangle.
\]

同候选与异候选之差也应逐项满足该分解。若残差重复性主要来自预测项自身，必须明确显示，不把它写成“恢复了听觉信号”。

### 6.6 必做反例

生成 `Delta_1=eps_1, Delta_2=eps_2`（相互独立、无真实刺激差异），B 为稳定个体背景。

- 固定一个非零 W，令 `R_h=eps_h-WB_h`，应能出现共享预测项带来的重复结构；
- 再用训练儿童有限样本拟合 W，对完全独立测试儿童重复整条流程；
- 分别做 W=0、真实可预测 nuisance、真实个体刺激信号三类世界；
- 每类 100 次，规模和缺失模式参考本轮冻结的支持计数，不拿真实临床值生成目标；
- 核对“交叉验证消除了泄漏”并不能自动证明“残差重复性是神经有效性”。

对真实数据可以追加在固定 Ω 内保留背景而打破刺激差异的诊断，但观察性事件标签置换不自动具有交换性；不得报精确 p 值。**A2 的继续依据以未校正主结果和对照为准，校正后单独转正不触发进一步训练。**

### 6.7 A2 输出

```text
A2/support_candidates_private.parquet
A2/support_cells_aggregate.csv
A2/omega_definition.json
A2/trial_draw_manifest_private.parquet
A2/repeatability_aggregate.csv
A2/residual_inner_product_decomposition.csv
A2/synthetic_residual_audit.csv
A2/A2_REPORT.md
```

状态允许 `SUPPORTED_SIGNAL / SMALL_OR_MIXED / NEGATIVE_SCREEN / SUPPORT_INSUFFICIENT / IMPLEMENTATION_FAIL`。支持不足与阴性同时存在时分别记录，不揉成一个 verdict。

---

## §7 C2：完整读出修复与空间信息损失检查

### 7.1 C2-R：只修旧估计器

原分支：

```text
L = [Fp1,F3,F7,C3,T3,P3,T5,O1]
R = [Fp2,F4,F8,C4,T4,P4,T6,O2]
```

复用原 trial alignment、分支独立 scaler、训练范围和全部失败日志。模型矩阵必须完整：

| family | views |
|---|---|
| linear | L, R, LR, LL, RR |
| MLP32 | L, R, LR, LL, RR |
| MLP64 | L, R |

R_SIM 为主；L0/R_SUP 完整平行；R_RAND 只复用原完整线性结果作为描述，不用它替代缺失非线性主矩阵。

超参数和候选平均方向沿用旧定义：

\[
T_C=\min\{L_L,L_R\}-L_{LR}.
\]

`min` 在候选等权平均 **之后**取，不先逐个儿童挑较好侧，再平均。容量 margin 也保持同一顺序。保留原 fixed-OOF bootstrap 与 raw/calibrated 两套。

若任何规定的主单元在预算内数值未完成，主族标 `INCOMPLETE_PRIMARY_MATRIX`；单独成功模型可展示，但不能在成功子集上重新计算“完整 C2”。

### 7.2 C2-S：新的观测对象，不伪装成旧 C 的 solver 修复

独立局部平均参考会丢失跨组均值差；同时旧 L/R 排除了四个中线通道。这是待诊断的信息损失，不是已经证明它解释了 C 的弱结果。

设原 20 通道被分成 L(8)、R(8)、M(4)，M 默认 `[Fz,Cz,Pz,Oz]`，必须用实际通道证据核对。定义：

\[
u_L=X_L-\bar X_L,\quad u_R=X_R-\bar X_R,\quad u_M=X_M-\bar X_M,
\]

\[
m_{LR}=\bar X_L-\bar X_R,\qquad
m_M=\bar X_M-\frac{\bar X_L+\bar X_R}{2}.
\]

五部分的有效空间维数为 `7+7+3+1+1=19`，与 20 通道整体平均参考相同。严格验证重建：

\[
X_L-\bar X_{20}=u_L+\tfrac12m_{LR}-\tfrac15m_M,
\]
\[
X_R-\bar X_{20}=u_R-\tfrac12m_{LR}-\tfrac15m_M,
\]
\[
X_M-\bar X_{20}=u_M+\tfrac45m_M.
\]

这是线性代数等式，不是解剖源分解。

### 7.3 构造规则

- 五部分从相同原始、参考一致、实际完整的通道输入构造，然后使用相同线性时间处理；不把不同 QC、滤波状态和坏通道插补混在等式里。
- 使用固定完整 20 通道定义；缺失通道不强行补零。独立局部坏通道策略与全头策略不同时，另记观测差异，不宣称精确重建。
- `u_L` 的数值计算不能读取 R/M；`u_R` 不能读取 L/M。`m_LR,m_M` 明确是联合成分，不能称独立专家。
- 联合 QC 可能使选择集合依赖其他分支；报告“数值计算隔离”与“选择规则隔离”的区别，不把前者当成后者。
- 新附加成分不输入旧训练 CNN 重新伪装为原 latent；主先做 L0 的固定 20 ms 分箱。

### 7.4 最小预测矩阵

在严格相同 trial 上比较：

1. `S0=[u_L,u_R]`；
2. `S1=[u_L,u_R,m_LR]`；
3. `S2=[u_L,u_R,m_LR,u_M,m_M]`；
4. `FULL20` 整体平均参考；
5. 与 S1/S2 同输入宽度的 S0 重复列控制（固定构造，不能使用标签）。

主 logistic、次 MLP32。S2 与 FULL20 是可逆坐标变换，但正则化、标准化、有限模型和优化不一定坐标不变；性能不完全相等不自动是代码错误。首先验证信号重建，再解释读出差异。对纯线性无正则可实现映射做单独一致性测试。

主要增益为 `G_crossmean=L(S0)-L(S1)` 与 `G_midline=L(S1)-L(S2)`；二者属于新的空间成分分析，不合并成旧 T_C。

### 7.5 必做空间合成例

- 只有左右组均值差携带标签：局部中心化 L/R 应丢失，m_LR 应恢复。
- 只有中线组携带标签：S0 不充分，增加中线成分有效。
- 全通道加相同参考漂移：全部差分成分应不变。
- 标签只与某组内部差异相关：该组内部表示保留信息。
- 扰动右组：左局部成分严格不变，但联合 m_LR 可变；测试需明确预期。

### 7.6 C2 决策

- C2-R 修复后若仍无联合增益：关闭“当前左右内部差异存在可用互补性”的扩展，不继续扫区域。
- 若只有 S1/S2 改善：说明空间观测定义值得调整，不证明半球协同或神经来源。
- 若联合信息只随模型容量增加：标 `CAPACITY_SENSITIVE`。
- 不启动 PID synergy 估计、通道组合大搜索或新 PoE 模型。


## §8 N1：背景作为刺激读出的条件

### 8.1 研究问题与主假设

> 在知道实验历史之后，当前试次的刺激前背景是否帮助解读刺激后响应，而不是仅仅提供标签先验？

这不是减背景，也不是 ERP 去噪。主张只有在独立测试的刺激预测中成立才有意义。不得以“背景很可重复”代替预测证据。

定义：`P` 为当前 post 表征，`B` 为当前 pre 表征，`H` 为 §2.4 的已知历史与位置。当前 pre 属于当前观测可用输入，不使用其他测试儿童的数据训练或归一化。

### 8.2 特征与样本

- 主 R_SIM 的同一个合规 encoder 输出：post 64 维、pre 64 维；保留“编码器在 post 上训练、pre 是另一输入分布”的事实。
- L0 平行：pre/post 独立做训练内候选加权 scaler＋PCA，各至多 32 维，不把 pre 填零到 post 时间长度。
- R_SUP、R_RAND 首先只输出共享诊断，不将四种表征全部扩展为完整 N1 网格。若需交叉表征核实，限 §13 的预定小范围，不挑最好的替主。
- 使用两类均有支持、H 可解析、P/B 成对完整的 HA 候选；每名候选每类至少 20 个试次，跨至少 4 个原 30 s 块。
- 至少 20 个候选且每外折至少 2 个、每训练折至少 12 个，才给主聚合。20 人是探索门槛，不是有效性证明；不足时保留描述而非换资格。

### 8.3 必做模型矩阵

所有模型采用同一 H、同一测试集合、同一训练权重。

| model | 输入 | 作用 |
|---|---|---|
| N1-H | H | 事件序列/位置基线 |
| N1-P | H＋P | 不使用背景的响应解码 |
| N1-B | H＋B | 背景自身的标签可预测性 |
| N1-PB | H＋P＋B | 联合模型 |
| N1-PP | H＋P＋P | 同维度/同宽度容量对照 |
| N1-PBnoise | H＋P＋固定独立噪声背景 | 检查新增参数/噪声特征影响 |

主读出 `MLP32`，logistic 为完整平行读出。无需新 encoder 或端到端融合。对噪声背景，其边际尺度由训练 B 估计、随机数由固定 seed 与无语义 trial key 确定；不能带入测试背景内容，也不能把 ID 数值当输入。

主评价 P_nat；P_bal 作为固定一个敏感性。

### 8.4 两个主要增益必须同时看

\[
G_{B\mid H,P}=L(H,P)-L(H,P,B),
\]
\[
G_{P\mid H,B}=L(H,B)-L(H,P,B).
\]

并报告 `G_P_over_H`、`G_B_over_H`、PB 相对于 PP 的 margin。

- 只有第二项为正：说明 post 在背景之外有用，不说明背景能辅助。
- 只有第一项为正：可能主要在读历史/状态，不能说恢复了声音响应。
- 二者都正、且 PB 超过 PP/噪声控制：支持上下文辅助的可用预测信息；仍不是严格 PID synergy 或因果神经解释。
- logistic 与 MLP 的差异可以提示可读性的模型依赖，不将其直接解释为神经编码非线性。

### 8.5 上下文错配：有限诊断，不作为因果干预

给已冻结的 PB 读出替换 B，P/H 不变：

**同儿童远端 pre：** 来自该儿童另一原始块，至少相隔实际原始依赖区间；优先取此前块。按前一个码、run bin 匹配，再按 gap 接近度择最近合法来源，最后用固定哈希决胜。

**其他儿童 pre：** 只从该 outer 的训练儿童池中取，匹配相同 H 类别与布局；不得从其他 outer 测试儿童借数据。

两种 donor 都 **不能根据当前刺激标签或模型分数挑选**。匹配规则与层级在新结果前冻结；无合法 donor 记录缺失，比较只在事先确定的 donor 共同集合上另列，不改主 N1 集合。

同儿童远端上下文是一项离线、额外未标注上下文辅助诊断，不是零上下文部署。donor 与 query 的直接波形及处理依赖不得重合。

替换会产生分布失配，因此“错配后变差”不自动证明该背景是必要的个体条件。至少补一个 **训练时也使用跨儿童匹配 donor、按相同构造测试** 的 PB-donor 模型（仅主 R_SIM/MLP32），判断下降是否只是训练测试输入构造不一致。

### 8.6 新增合成检验

- `PRIOR_ONLY`：H 决定大部分类别，B 只读到 H，P 没有额外信息。控制 H 后不能据表面 PB 提升宣称背景有用。
- `BACKGROUND_KEY`：P 的类别编码随稳定背景变换，B 提供解码条件；PB 应优于 P 和 B。
- `ADDITIVE_NOISE`：P 含背景偏移，B 是相关但有噪的偏移观测；PB 可改善读出，但解释应是条件去干扰，不是新刺激信息生成。
- `INDEPENDENT_BACKGROUND`：B 独立无用，联合模型不应稳定取得超过固定门槛的收益。

### 8.7 推进依据

预定最小探索量级：主 `G_B|H,P >=0.005 bits/trial`、候选 bootstrap 下界 >0，且 `G_P|H,B>0`、PB 相对 PP 的 margin >0；同时报告 raw/calibrated 是否一致。低于量级但方向一致记 `SMALL_SIGNAL`，不自动扩大模型。

通过只是后续研究依据，不是临床有效性。若只有 H/B 能预测标签而 post 无增量，写 `PRIOR_OR_CONTEXT_ONLY`；该情况仍是有用诊断，但不立“听觉响应改善”故事。

---

## §9 N2：重复试次分布中的声音信息

### 9.1 研究问题

> 单试次与条件均值读出较弱时，相同声音的一组重复响应，其离散程度或分布形状能否提供均值之外的判别信息？

分析单位变为同候选、同任务、同当前刺激的一组试次。这里利用的是 **实验已知同刺激重复这一组结构**，不是声称在完全未知类别的任意 EEG 流中已经知道如何分组。

它不是在线提前停止，也不重建 ERP。只看到 k 增大后 accuracy 上升，不足以支持新的论文主张。

### 9.2 固定 bag 构造

- 主 `k=8`，预定预算曲线 `k∈{1,4,8,16}`。
- 主 R_SIM、L0 平行；同 outer/inner 坐标体系内构造。先划分身份、时间块与 half，再组成 bag。
- 主每个 bag 只包含同一记录、同一当前刺激、同一独立 half 的 trial。half 明确复用带保护区的 `A_half` 交替 60 s 块及 `A_boundary_eligible`；不复用旧 A 的最终人数作为 N2 资格。不跨候选、跨任务、跨校准/测试合并。
- k>=4 时至少来自 2 个不同原时间块，每块最多 `ceil(k/2)` 个；不要求同一 bag 内独立同分布，但必须记录依赖与时间跨度。
- 每个主分组内同一 trial 只出现一次；不用有放回抽样把相同 epoch 复制 k 次。
- 两个 half 各自每类至少 2 个 bag；主 k=8 即每 half×class 至少 16 个试次，同时每 half×class 覆盖至少 3 个原块。
- 用固定 seed 排序与装袋，满足规则后剩余不足 k 的 trial 保留 unused 状态；不能按信号美观、预测置信或更小方差挑袋。
- 主采用一个固定、不重叠分组；另做 10 个固定随机分组作为敏感性。不同分组先在候选内平均，不作为独立样本。

以 k=8 支持集合为主；比较 k=4/8/16 曲线时另给三者共同候选/half/来源池上的曲线。k=16 支持不够不删除 k=8 主研究，也不能将改变人群后的曲线解释为纯预算效应。

### 9.3 冻结的特征表示

对每个 trial 的 R_SIM 或 L0 表征，在训练儿童内拟合 scaler＋8 维 PCA（不足有效秩时记录实际维数，所有对照匹配）。不要在所有测试 bag 上拟合 PCA。

令 bag 内 trial 表征为 `z_i∈R^p`，构造：

- `MU`：p 维均值；
- `VAR`：逐维无偏样本方差的 `log(var+1e-6)`；eps 作用于训练缩放后的坐标；
- `MU_VAR`：均值＋log 方差；
- `MU_DUP`：均值重复两份，同输入宽度控制；
- `RFF_MEAN`：固定 16 个随机 Fourier 特征的 bag 均值，作为分布特征次要对照；带宽仅由训练 trial 中固定 4096 对无标签距离的中位数确定；
- `H_BAG`：历史 run-bin 比例、previous-code 比例、gap 均值/标准差、位置均值/标准差、块数和时间跨度。

k=1 的 VAR 未定义，**不能填零后声称是同一个方差模型**。k=1 只评价单试次/MU/RFF 对应模型；MU_VAR 主比较仅在 k>=4。

RFF_MEAN 也是某种非线性特征的均值，不能把其成功自动命名为发现高阶神经编码。VAR 可以反映真实响应变化，也可以反映噪声、状态和伪迹。

### 9.4 主矩阵与主终点

主 logistic，次 MLP32；每 k 分别拟合、分别校准，不拿 k=8 模型直接套 k=16 后混淆分布改变。

| model | 输入 |
|---|---|
| N2-H | H_BAG |
| N2-M | H_BAG＋MU |
| N2-MV | H_BAG＋MU＋VAR |
| N2-MM | H_BAG＋MU＋MU |
| N2-V | H_BAG＋VAR |
| N2-RFF | H_BAG＋RFF_MEAN |

主终点：

\[
G_{dist}(8)=L(H_{bag},MU)-L(H_{bag},MU,VAR).
\]

同时要求 MV 相对 MM 的 margin，并报告 `J_k=1-L_bal`，单位 **bits/bag**。不能把 k 个单试次 J 直接相加作为 bag 的信息上限；二分类标签熵仍至多 1 bit。`J_k/k` 只可作资源归一化描述，不能称为通道容量。

### 9.5 强制的解释对照

1. **相同 trial/bag 的 pre 特征：** 使用相同模型矩阵，确认 post 的分布增益是否只是通用背景变化；pre 与 post 的时间长度不同，不能把数值差当成纯因果分量。
2. **历史/时间元数据基线：** 主矩阵已含 H_BAG。否则 code 2 的 bag 可能跨更长时间、不同历史，模型只读到分组结构。
3. **均值充分合成例：** 同协方差高斯类别仅均值不同；MU 是充分统计，VAR 不应稳定产生真实额外信息。
4. **等均值、不同协方差合成例：** MU 的最优判别有限，VAR/RFF 应能提供可检测增量；检验当前 bag 数和噪声下的功效。
5. **时间漂移例：** 类别与时间分布相关但神经响应无类别差异；应被 H_BAG/pre 对照提示，而不是解释为分布编码。
6. **置换 bag 内 trial 顺序：** MU/VAR/RFF 输出严格不变，排除顺序泄漏。
7. **重复同一个 trial 的伪 bag：** 作为故意错误输入的测试，pipeline 必须拒绝，不将其当成有效重复观测。

主分组使用刺激标签定义同类集合是任务设计的一部分。除这一合法构造外，bag 标识、当前类别组成计数、原始标签字符串、event code 列均不得进入预测器。

### 9.6 支持和推进

主至少 20 个合格候选，各外折至少 2 人；不足时不以增加重采样次数补“样本量”。

量级约定：`G_dist(8)>=0.01 bits/bag`、区间下界 >0、MV 相对 MM margin >0，且 post 主张不被 pre/H_BAG 解释。主分组与重复分组平均应方向一致；若仅 RFF 次要模型成功，写成新的探索线索，不替换预先固定的 MV 主结论。

只有预算曲线上升而无分布增量：记 `MEAN_ACCUMULATION_ONLY`，不自动启动 Deep Sets。Deep Sets、新集合对比目标或临床预测留到下一次立项，本轮不开发。[R2]

---

## §10 N3：刺激序列先验之外的 EEG 证据

### 10.1 新估计对象

旧 B 研究固定当前刺激后的历史可读性；本路线的目标为当前刺激 S，条件为过去历史 H：

\[
G_{EEG\mid H}=L(q_0(S\mid H))-L(q_1(S\mid H,Z)).
\]

理论动机是 `I(S;Z|H)`，实际只估计指定读出器下的 OOF 预测增益。不要称为 B 复现或 B 的阴性被推翻。

### 10.2 支持与结构性空格

原 v1 的结构空格必须保留。主 N3 使用训练内支持的历史区域，不通过填补构造罕见/不存在的刺激。

每个 outer 内，先仅依据训练事件计数定义 cell：`previous_code` × `previous_run_bin={1,2,3–5,>=6}`。cell 要在训练集中每当前类别至少 20 次，并分别由至少 5 个训练候选支持，才能进入该折的 `OMEGA_H`。

- `OMEGA_H` 不读取测试 EEG、测试预测或临床结局；测试仅按过去 H 进入相应区域。
- H 模型仍使用 §2.4 的完整过去三码和连续 gap/位置，不因粗 cell 合格就假定细历史条件处处有重叠。
- 主结果属于这个 **训练支持驱动的交叉拟合评估人群**，各外折 Ω 可能不同；逐折支持定义与覆盖率必须报告。
- 输出完整序列上的描述性结果，特别列出结构不可比较区域；不得把 overlap 结果外推全序列。
- 记录某些细历史近乎确定当前刺激的比例以及 q0 的置信分布，但不按测试模型置信事后删 trial。

主合格候选在保留区域内每类至少 10 个试次、合计至少 4 个块；至少 20 候选且每外折至少 2 个。数据不支持时停止主 N3，不发明概率倾向权重将零支持补成非零。

### 10.3 序列基线必须足够明确

`q0` 不是只用一个 run-length 数的弱基线。必须同时比较：

- H 的正则 logistic；
- H 的 MLP32；
- 训练内选择的一个最终 H 基线（相同 3 inner folds，仅按 OOF P_nat CE 选择，平局优先 logistic）。

当前刺激的 local code 不进入 H；过去三码的联合 one-hot 可以进入，因为它完全由过去确定。未知历史需要明确处理；不因未知而将其自动设为码 1。

### 10.4 EEG 增量矩阵

| model | 输入 | 说明 |
|---|---|---|
| N3-H | H | 强序列基线 |
| N3-HP | H＋post Z | 当前响应加入序列模型 |
| N3-HB | H＋pre Z | 先前响应/背景可解释的标签预测 |
| N3-HBP | H＋pre Z＋post Z | post 超过历史与背景的增量 |
| N3-Hnoise | H＋固定独立噪声，与 Z 同维 | 增加特征/参数的负对照 |

主 R_SIM，L0 平行。主 P_nat，P_bal 完整敏感性；不能用 P_bal 的均匀基线去解释自然稀有事件条件熵。

主要终点为：

\[
G_{P\mid H}=L(H)-L(H,P).
\]

关键控制终点为：

\[
G_{P\mid H,B}=L(H,B)-L(H,B,P).
\]

N1 与 N3 的模型可以共享已拟合单元，**仅在 trial 集合、评价权重、特征、划分和参数选择完全一致时**复用；不因名称相同就复用不同人群上的 q0。

### 10.5 限制模型差异带来的假增量

分别报告每个固定读出族内的 H 对 HP 增益，而不是只比较较弱 H-logistic 与较强 HP-MLP。最终主增益用各自训练内选择的模型，主族结果全部保留。

如果需要“基础模型＋EEG 残差”的 offset 读出，只允许作为下一阶段方法设计；本轮不将其加入额外搜索。尤其不拿 q0 对训练样本的过拟合 logit 当成无偏 offset 再声称精确条件信息。

校准变化、增加参数和 H 的欠拟合均可能造成经验增益；用 Hnoise、H-MLP 及 P_bal 敏感性限制这些解释。

### 10.6 预定次要分析，不扫 surprise 函数

在主模型已经冻结后，按过去 run bin `{1,2,3–5,>=6}` 分层报告同一个 q0/q1 的损失与增量；不在各层重选最有利模型。每层报告候选、trial、两类支持和区间；稀疏层描述而不作群体结论。

不能因为某层增益大就称“预测编码增强”；声学身份、稀有性、适应与历史角色在本数据中未完全实验分离。

### 10.7 必做反例和推进标准

- 标签由 H 强预测、Z 只复制 H：控制 H 后无真实新增信息。
- Z 包含独立的当前标签信号：HP 应有增量。
- 细历史近乎确定标签：验证剩余可改善误差很小，不把阴性当作 EEG 无信号。
- 当前标签误入 `current_run_length`：测试必须失败，证明禁用字段确实被拒绝。
- 保持过去链但替换当前/未来标签：当前 H 不变；未来标签不允许参与特征。

主量级约定 `G_P|H>=0.005 bits/trial`、区间下界 >0；关键控制 `G_P|H,B>0`；Hnoise 不应提供相近增益。只有 H 本身很好而 EEG 无增量时，写 `SEQUENCE_PRIOR_DOMINANT`，不写“脑信息不足”。

q0 的测试 CE 不是条件熵的精确估计；`G/CE(q0)` 如展示仅为模型风险改善比例，不是“剩余神经信息被恢复的百分比”。

---

## §11 E0 维护与 B/D 关闭规则

### 11.1 E0-R 的唯一授权动作

沿用 E0_native_003 的请求记录、task labels、原生 layout、原有时间分块和 trial 支持。使用 §4 的求解器修复同一个 MLP32 族，复算全族，不只补 5 个失败点后与旧成功点任意混合。

- linear 原结果复核保留；修复 MLP 的所有相同任务/记录都经过新求解器。
- 有多少请求记录、块支持记录、各族完整记录、完整同儿童任务对，分别报告。
- 只做记录内、带时间隔离的目标任务可读性；记录内结果不等于跨儿童迁移。
- 修复后仍失败，保留全族 `INCOMPLETE`；不得在成功子集上报“主要 MLP 结果”。

最多一个新 solver 方案和一次预定预算延长，不新增 encoder，不更换任务，不启动 E1，不将 MFF 来源一律命名为 CI。

### 11.2 B/D 归档产物

生成 `CLOSED_ROUTES.md`：逐项引用旧结果、关闭的确切问题、未被否定的更广泛问题、后续重新启动所需的新证据。除这个归档与旧结果读取外，本轮不计算新的 B/D 结局模型。

临床表不提供给 N1/N2/N3 的开发与筛选模块。本轮输出可复现的声音信息对象后，再由下一版方案决定是否建立固定的临床增量检验；不预先承诺这些对象与 MUSS 一定有关。


## §12 合成反例、泄漏测试与真实数据集成测试

### 12.1 不再只报告“测试通过多少项”

每项测试输出：要排除的错误、输入构造、期待方向/不变量、实际误差、通过阈值、关联的真实路线。模块 PASS、端到端 PASS、数值稳定、真实效应与临床效度是五个不同层次。

最少实现下表；测试数量不是科研贡献。

| ID | 测试/反例 | 必须满足的性质 |
|---|---|---|
| T01 | 旧输入和旧结果哈希 | 本轮结束前后完全不变 |
| T02 | 未来/当前标签字段禁用 | 替换当前或未来刺激不改变当前 H |
| T03 | QC 前事件链 | 拒绝一条 EEG 不删除其刺激历史作用 |
| T04 | 划分后 bag/增强 | 相同 trial 及相关版本不能跨 fit/test |
| T05 | raw dependency embargo | 跨角色时间支持无相交；不能仅查 event ID |
| T06 | outer/inner encoder 范围 | inner 验证儿童从对应 encoder 训练中排除 |
| T07 | 折坐标 | 不跨不同 encoder 坐标拼 embedding；只汇总预测/标量 |
| T08 | 候选与类别权重 | P_bal、P_nat 各自训练/评价/校准一致 |
| T09 | test-label perturbation | 改测试标签只改变评分，不改变已拟合参数、PCA、donor 或校准 |
| T10 | stable log loss | 极端 logit 无 NaN；负 J/负增益保留 |
| T11 | objective parity | C2 新旧目标、罚项及梯度等价性达到容差 |
| T12 | numerical receipt | 预算结束不自动等于收敛；警告/失败被结构化记录 |
| T13 | A2 固定 Ω | 不允许每个候选的 cell 权重变成身份指纹 |
| T14 | A2 残差反例 | 无真实 Delta 重复性时，共享预测项可以造成残差重复性，必须被审计捕捉 |
| T15 | A2 内积分解 | 四项分解逐折、逐配对数值相等 |
| T16 | C2 空间可逆性 | 五成分重建全 20 平均参考，误差达 float64 容差 |
| T17 | C2 空间隔离 | 右侧扰动不改左局部成分；联合成分按设计变化 |
| T18 | C2 丢失均值注入 | 仅 m_LR 有标签时局部参考应丢失，显式成分恢复 |
| T19 | N1 donor 防作弊 | donor 不按当前标签/预测/临床值选择；来源和支持合规 |
| T20 | N1 条件钥匙/先验世界 | 区分背景辅助与只读到历史先验 |
| T21 | N2 bag 顺序和重复 | 顺序不变性；同一个 trial 伪重复被拒绝 |
| T22 | N2 均值充分/协方差世界 | 不能把纯均值增益误称分布增益；方差世界应有检出能力 |
| T23 | N2 k/候选不变性 | 不把重分组次数、bags 或 k 当作新增儿童 |
| T24 | N3 强历史基线 | H-only 世界中 EEG 复制 H 不能稳定创造额外主信号 |
| T25 | 失败集合完整性 | 未成功的主模型不在汇总时被静默丢弃 |
| T26 | 发布扫描 | 无个人值、路径、精确日期、trial 预测、权重、checkpoint |

T09 的 Ω 研究设计选择应先冻结再测试。A2 使用实验标签计数确定设计的事实已经披露；冻结后不得因 test label perturbation 重新选 Ω。

### 12.2 合成实验的规模与角色

A2 残差反例按 §6 的每类 100 次；其他新路线每个规定世界先 30 次、每次约 50–60 个虚拟候选，trial 量按合格真实样本计数范围构造。关键零信息和注入世界总共最多 600 次。

使用虚拟身份、独立生成目标，不保留真实参与者值。可以复用真实数据的聚合计数和噪声尺度；若使用真实受限 EEG 做信号注入，所有注入输入输出仍留 private，不能发布原背景。

合成模型与读出器的标签关系已知时，检验功效与假阳性倾向。通过不保证真实数据效应存在；没通过则不能把相应真实阴性写成充分否定。

### 12.3 真实数据端到端 smoke

仅按来源/布局/计数选择少量记录，不按已有正结果选。完成一次：数据加载 → 训练内变换 → 小读出 → OOF 预测 → 候选汇总 → 输出哈希。

smoke 看的是接口与资源，不可作论文主结果。最多一次修复性重试；失败原因明确定位，不能连续 smoke 变成隐蔽模型搜索。

---

## §13 任务依赖、预算、停止条件和推进判据

### 13.1 执行顺序

```text
S0 只读盘点 / 快照与输入冻结 / B-D 归档
 ├─ S1A 事件与共同支持冻结 → A2
 ├─ S1B 旧特征/inner scopes/处理对账 → G0 → N1、N2、N3
 ├─ S1C 读出器 objective parity + synthetic → C2-R、E0-R
 └─ S1D 空间成分可逆性 + 受限导出 → C2-S

A2 / C2 / N1 / N2 / N3 / E0-R 分别完成或失败记录
 → S3 聚合判读 → NEXT_ROUND_REPORT.md
```

G0 的诊断报告先形成，但只有实现/量纲/标签错误阻断受影响路径；弱解码本身不能把全部新问题提前判死。A2 没有支持不阻断 N1/N2/N3。

### 13.2 本轮固定读出预算：避免隐性网格爆炸

为控制下一轮规模，**N1/N2/N3 首轮主矩阵采用固定正则，而不是全面扫 §4 的候选范围**：

```yaml
new_routes_fixed_first_pass:
  logistic_C: 1.0
  mlp_lambda: 0.001
  mlp_seed: 11
  inner_folds: 3
  purpose_of_inner_folds: calibration_and_declared_family_selection_only
```

固定值先通过合成数值测试，不以真实测试结果选择。§4 列出的范围仅用于 C2/E0 原协议修复所需范围，或后续另行授权的扩展；**本轮新 N 路线不得自动启用整个正则网格**。这一明确约定优先于泛化表格中的可选范围。

N3 的 H-logistic 对 H-MLP 仍可按训练内 OOF 选择；其他新主模型族按各路线已指定的主/次顺序，不按 outer test 选择。

N2 的 10 次重分组敏感性只重组测试 bags 并用相同已冻结 head 评价，训练仍为主分组；不乘以 10 重训整个流程。另行训练分组的变化留作后续，不混入本轮主区间。

### 13.3 配额上限

| 项目 | 本轮上限 | 说明 |
|---|---:|---|
| 新正式 encoder 训练 | **0** | 复用旧 outer/inner；不重跑 90 任务 |
| G0 专用诊断 encoder | 最多 2 个 fit | 仅合成端到端/极小训练拟合检查；不产生正式路线表征 |
| C2/E0 新 solver | 1 个 | 只有一次预定延长，不循环更换 solver |
| 新神经读出初始化 | 首轮 seed 11 | 不在结果后挑 seed |
| 新 N 路线固定模型的稳定性复核 | 最多 2 条路线，各 seed 23 | 只在主/控制达到 §13.5 后；固定全部主比较成员，不只复跑赢家 |
| 神经浅层 head fit | 最多 3000 个 | 一个外/内折×family×view×seed 记 1 fit，延长不记新 fit 但记算力 |
| 全部读出 fit | 最多 8000 个 | 包含线性、MLP、校准所需拟合和 C/E 修复 |
| GPU 并发 | 最多 2 | 一次只占一个 GPU/作业 |
| CPU 数值作业并发 | 最多 4 | BLAS 线程不得超申请 CPU |
| 累计 GPU 预算 | 最多 32 GPU·小时 | 资源上限，不是完成时间承诺 |
| 累计 CPU 预算 | 最多 256 CPU·小时 | 以实际可获得的 Slurm accounting 或保守上界登记 |
| 新数据导出 | 仅缺失的规定成分 | 不复制全部原始数据、不重新制造全部 MFF epochs |

提交真实任务前输出 `TASK_PLAN.csv`，按真实 folds/modes/views/candidates 计算总 fit 数、内存和预算上界。任务不能藏在一个 Slurm job 里而不记 fit 数。

若计划超额，按以下顺序运行，明确标出预算未完成项，不静默删表：

1. S0、支持审计、数值/空间单元测试、G0 对账；
2. A2 与 **N1/N2/N3 各自的 R_SIM 主矩阵和必要对照**，保证三个新方向都获得一次最低检验；
3. C2-R 完整主 R_SIM 矩阵、C2-S L0、E0-R；
4. 新 N 路线的 L0 平行与主 R_SIM 稳定性/次要对照；
5. C2 L0/R_SUP 的完整平行、固定预算曲线与种子复核。

必要对照缺失时不能判 `SUPPORTED_SIGNAL`。预算不足标 `BUDGET_LIMITED`，不得替代成阴性或声称整轮完整。不要为补充图绕过上限。

### 13.4 不反复询问，也不擅自扩题

本文件授权完成上述实现、测试和限定实验，不需要每个小阶段等待再次批准。仅在以下情况停止相应路径并记录：受限输入/权限缺失，身份/时钟证据无法确定，范围外依赖安装或资源申请，达到算力上限，或需要改变主要研究对象/标签/架构。

支持不足时继续其他路线；不要要求研究者重复提供已在仓库内可查的字段。需临床方确认的事件语义整理为问题清单，不由模型猜测。

### 13.5 推进判据是筛选规则，不是论文结论

| 包 | 主判据 | 不满足时 |
|---|---|---|
| A2 | 共同支持冻结；未校正 T 达 0.05 且区间下界 >0；pre/背景伪影解释受限制 | 小效应、阴性或支持不足分别报告；校正后单独转正不推进 |
| C2-R | 主完整矩阵数值稳定；T_C 达 0.01 bits/trial 且容量 margin >0 | 完成阴性则停止该分区扩展；未完成保留实现状态 |
| C2-S | 空间重建通过；跨组均值/中线增益超过重复列控制 | 只证明可逆性不算科学阳性 |
| N1 | 两类条件增益成立，背景增益达 0.005 bits/trial，PB 超过 PP | prior-only、small、mixed 与 negative 分开 |
| N2 | k=8 的分布增益达 0.01 bits/bag，超过均值重复控制，pre/H_BAG 不足以解释 | 只有均值累积则不开发集合网络 |
| N3 | EEG 超过强 H 基线达 0.005 bits/trial，且在 H＋pre 外仍有增量 | 可能先验占优；不推断脑内信息消失 |
| E0-R | 完整族可评价且任务内有稳定目标可读性 | 不自动进入 E1；给后续数据/任务可行性建议 |

所有正向推进还需候选覆盖充分、无主数值失败、非仅一个异常候选驱动、raw/calibrated 行为可解释。L0 与 R_SIM 没有差别并不否定现象，只否定“SimCLR 特别有效”的主张。

最多对两条完整新路线做 seed 23 的固定主比较复核；选择顺序不是简单选最高分：先按控制完成度，再按预定效应门槛与实际支持，最后固定优先顺序 `N1 > N2 > N3` 决胜。报告全部筛选过程；复核仍是探索，不冒充独立新样本。

---

## §14 软件接口、配置和 Slurm 入口

### 14.1 新模块目录：以下是需要实现的规格，不是已存在工具

```text
AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md
configs/
  auditory_next_v2.yaml
  auditory_next_site.local.yaml             # 私有/忽略发布
  auditory_next_sources_v2.yaml

auditory_next/
  __init__.py
  cli.py
  registry.py                              # 输入/代码/配置哈希与范围
  manifests.py                             # ID、trial、bag、H 与支持
  scopes.py                                # 旧 outer/inner 特征路由
  readouts.py                              # solver repair 和固定新读出
  weighting.py                             # P_nat/P_bal 及候选均衡
  calibration.py
  g0_diagnostics.py
  a2_overlap.py
  a2_residual_audit.py
  c2_repair.py
  c2_spatial.py
  n1_context.py
  n2_distribution.py
  n3_sequence.py
  e0_repair.py
  synthetic.py
  reporting.py

tests/auditory_next/
slurm/auditory_next_cpu.sbatch
slurm/auditory_next_readout_gpu.sbatch

private/auditory_next_v2/<run>/
results/auditory_next_v2/<run>/
reports/auditory_next_v2/<run>/
```

原 `auditory5` 模块可以只读导入；遇到旧函数内部写固定目录或隐含 global root 时，建立适配层，不原地修改旧函数和历史快照。

### 14.2 CLI 契约

建议实现并在合成数据上测试：

```bash
python -m auditory_next.cli --config configs/auditory_next_v2.yaml preflight --run S0_001
python -m auditory_next.cli --config configs/auditory_next_v2.yaml freeze-support --run S1_support_001 --source-run S0_001
python -m auditory_next.cli --config configs/auditory_next_v2.yaml test-contracts --run tests_001
python -m auditory_next.cli --config configs/auditory_next_v2.yaml make-plan --run plan_001 --support-run S1_support_001 --tests-run tests_001
python -m auditory_next.cli --config configs/auditory_next_v2.yaml run-packet --packet G0 --run G0_001 --plan private/auditory_next_v2/plan_001/plan.json
python -m auditory_next.cli --config configs/auditory_next_v2.yaml run-packet --packet A2 --run A2_001 --plan private/auditory_next_v2/plan_001/plan.json
# 其余 packet：C2_R、C2_S、N1、N2、N3、E0_R
python -m auditory_next.cli --config configs/auditory_next_v2.yaml aggregate --run final_001 --registry configs/auditory_next_sources_v2.yaml
python -m auditory_next.cli --config configs/auditory_next_v2.yaml validate-release --run releasecheck_001 --source-run final_001
```

上面的名字是待实现接口，不直接调用旧 `auditory5.route_runner --route N1`，旧 CLI 没有这些路由。不能仅生成 shell 文件就报告“实验已执行”。

`run-packet` 应能先输出内部拟合单元，再由 Slurm array/worker 执行；一个失败单元不得覆盖或删除其他已完成回执。`aggregate` 读取明确 source registry，不能搜索目录中“最新/最好”的 run。

### 14.3 配置骨架

本 YAML 为需要实现的配置契约。路径使用服务器本地配置，不能在公开配置中写出受限个体目录。

```yaml
project:
  name: auditory_next
  version: v2.0
  reference_commit: 191b3a189bea116c4c91fdcfcb6d3bd2945b8dfa
  status: NOT_RUN
  exploratory_after_v1_results: true
  overwrite: false
  site_config: configs/auditory_next_site.local.yaml
  source_registry: configs/auditory_next_sources_v2.yaml

scope:
  packets: [G0, A2, C2_R, C2_S, N1, N2, N3, E0_R]
  closed_routes: [B_v1, D_v1]
  allow_E1: false
  primary_cohort: HA
  mff_scope: existing_E0_only
  allow_clinical_modeling: false
  allow_new_formal_encoders: false
  allow_new_architecture_search: false
  allow_new_ssl_objective: false
  publish_individual_data: false
  automatic_commit_push: false

sources:
  legacy_project: auditory5_v1
  split_run: splits_001
  representation_plan_run: plan_001
  execution_run: execution_status_003
  screen_run: S4_final_001
  require_exact_trial_ids: true
  require_inner_scope_provenance: true
  preserve_metadata_addendum: true

representations:
  primary: R_SIM
  new_route_parallel: L0
  legacy_diagnostics: [R_SUP, R_RAND]
  use_encoder_output_not_projector: true
  retrain_legacy_90_jobs: false

preprocessing:
  default_source: P1_CAUSAL20
  spatial_source: P2_SPATIAL_SPLIT
  sample_rate: 250
  post_seconds: [0.05, 0.45]
  pre_seconds: [-0.2, 0.0]
  baseline_subtraction: false
  per_trial_variance_normalization: false
  use_actual_filter_support: true
  event_history_before_qc: true
  new_temporal_filter_search: false

validation:
  outer_identity_folds: legacy_fixed_5
  inner_folds: 3
  default_new_min_candidates: 20
  minimum_test_candidates_per_outer: 2
  minimum_training_candidates_per_outer: 12
  fixed_oof_cluster_bootstrap: 2000
  test_eeg_in_ssl_training: false
  combine_embedding_coordinates_across_folds: false
  conditional_label_permutation_p_values: false

readouts:
  new_fixed_logistic_C: 1.0
  new_fixed_mlp_lambda: 0.001
  new_mlp_weight_decay: 0.0
  legacy_C_or_alpha_grid: [0.01, 0.1, 1.0, 10.0]
  repair_hidden_primary: 32
  repair_hidden_capacity_control: 64
  repair_solver: torch_adam_full_batch
  precision: float64
  learning_rate: 0.001
  steps_initial: 1000
  steps_extension_once: 1000
  schedule_horizon_steps: 2000
  seed: 11
  objective_parity_required_for_repair: true
  failure_is_not_negative_effect: true

calibration:
  legacy_repair_T_bounds: [0.25, 4.0]
  new_T_bounds: [0.25, 16.0]
  fit_on_training_oof_only: true
  prior_mixture_diagnostic_eta: [0.0, 0.25, 0.5, 0.75, 1.0]
  no_oof_fallback: uncalibrated_fixed

A2:
  previous_code: literal_1
  minimum_previous_run: 3
  run_bins: [[3, 5], [6, null]]
  position_bins: [0.0, 0.5, 1.0]
  minimum_selected_cells: 2
  trials_each_cell_half_class: 6
  minimum_blocks_each_half_class: 3
  minimum_candidates: 25
  fixed_common_cell_weights: uniform
  resampling_repetitions: 20
  contrast_dimension_max: 8
  main_statistic: unadjusted_matched_minus_mismatched_cosine
  effect_floor: 0.05
  corrected_statistic_is_primary: false

C2:
  repair_matrix_complete_required: true
  spatial_geometry_tests_required: true
  add_crossmean_as_explicit_joint_component: true
  include_midline_geometry_diagnostic: true
  claim_PID_synergy: false
  primary_joint_gain_floor_bits: 0.01

N1:
  main_population: P_nat
  secondary_population: P_bal
  main_readout: mlp32
  parallel_readout: logistic
  models: [H, HP, HB, HPB, HPP, HPBnoise]
  donor_diagnostics: [same_child_remote_pre, training_child_matched_pre]
  donor_uses_current_label: false
  matched_donor_training_control: true
  background_gain_floor_bits: 0.005

N2:
  main_population: P_bal
  main_k: 8
  k_values: [1, 4, 8, 16]
  main_partition_seed: 20260917
  sensitivity_test_partitions: 10
  refit_each_sensitivity_partition: false
  main_readout: logistic
  secondary_readout: mlp32
  trial_pca_dimension: 8
  variance_epsilon: 0.000001
  rff_dimension: 16
  include_history_bag_controls: true
  main_gain_floor_bits_per_bag: 0.01
  deepsets_training_this_round: false

N3:
  main_population: P_nat
  secondary_population: P_bal
  target: current_stimulus
  history: H_v2_past_only
  overlap_fit_scope: outer_training_event_counts
  minimum_training_events_per_class_cell: 20
  minimum_training_candidates_per_class_cell: 5
  models: [H, HP, HB, HBP, Hnoise]
  main_gain_floor_bits: 0.005
  current_run_length_as_input: false
  eeg_increment_is_exact_cmi: false

E0_R:
  input_run: E0_native_003
  same_requested_records: true
  refit_entire_mlp_family: true
  new_tasks_or_E1: false

budget:
  max_formal_encoder_fits: 0
  max_diagnostic_encoder_fits: 2
  max_neural_head_fits: 3000
  max_all_readout_fits: 8000
  max_gpu_concurrent: 2
  max_cpu_jobs_concurrent: 4
  max_gpu_hours: 32
  max_cpu_core_hours: 256
  new_route_seed_replication_max_routes: 2
  replication_seed: 23
  overwrite_legacy: false
```

### 14.4 Slurm 编排模板

以下只是命令形状。服务器先实现接口、核对分区/账户/环境，再实际提交；不要复制一个未存在的模块就把 Slurm 提交错误当作科研阴性。

```bash
# 登录节点仅做文本/目录与调度操作。
ROOT=/home/infres/yinwang/EEG_auditory     # 由 site 配置核对，不强制覆盖
PY=/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python
RUN=S0_001                              # 必须换成未存在的唯一 run
LOGS="$ROOT/private/auditory_next_v2/logs"
mkdir -p "$LOGS"
chmod 700 "$ROOT/private/auditory_next_v2" "$LOGS"

sbatch --parsable \
  --chdir="$ROOT" \
  --cpus-per-task=2 --mem=8G --time=00:30:00 \
  --output="$LOGS/preflight-%j.log" \
  --wrap="umask 077; export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2; \
  export AUDITORY5_ROOT='$ROOT' AUDITORY_NEXT_ROOT='$ROOT'; \
  '$PY' -m auditory_next.cli --config configs/auditory_next_v2.yaml preflight --run '$RUN'"
```

分区/账户/GPU 型号由实际 site 加入，不假定公共范例适合当前集群。正式 readout job 使用经环境核验的 wrapper；显式 `afterok` 或读取 PASS gate，不根据“已经等了多久”推断前置任务完成。

对失败包的最终汇总用 `afterany` 配合回执解析，确保失败也进入报告；不得因为某个 worker 失败导致没有最终交付。只取消本轮自己提交且确认不再需要的作业。

---

## §15 输出文件、最终报告和验收

### 15.1 必交文件

```text
reports/auditory_next_v2/<final_run>/
  NEXT_ROUND_REPORT.md
  G0_DIAGNOSTIC_REPORT.md
  A2_REPORT.md
  C2_REPAIR_AND_GEOMETRY_REPORT.md
  N1_CONTEXT_REPORT.md
  N2_DISTRIBUTION_REPORT.md
  N3_SEQUENCE_REPORT.md
  E0_REPAIR_REPORT.md
  CLOSED_ROUTES.md
  REMAINING_METADATA_QUESTIONS.md

results/auditory_next_v2/<final_run>/
  route_status.csv
  eligibility_aggregate.csv
  metrics_aggregate.csv
  paired_effects.csv
  controls_aggregate.csv
  numerical_status.csv
  synthetic_summary.csv
  resource_usage.csv
  source_hashes.csv
  output_manifest.json
```

受限配套：`trial_manifest.parquet`、`bag_manifest.parquet`、`donor_manifest.parquet`、`scope_manifest.json`、`predictions.parquet`、`fit_receipts/`、`models/`、`failure_logs/` 全部在 private。公开只列计数和聚合，不把 ID 哈希当成可自由发布的匿名化证明。

### 15.2 每个 fit 的回执

至少包含：

```text
fit_id, packet, mode, view, objective_id, optimizer_id,
outer_fold, inner_fold, seed, training_scope_hash,
input_hash, feature_scope_hash, label_map_hash, weight_distribution,
hyperparameter_source, calibration_scope_hash,
n_train_candidates, n_train_trials_or_bags,
n_eval_candidates, n_eval_trials_or_bags,
step_count, final_train_loss, gradient_diagnostic,
finite_parameters, optimizer_status, resource_usage,
code_hash, config_hash, model_hash, prediction_hash,
exception_class, failure_stage
```

不得将候选人数从 trial 数倒推，或只以完成 receipt 数代表科学完成。

### 15.3 效应表 schema

```text
packet, analysis_id, primary_or_secondary, representation,
population_id, overlap_definition_hash, unit,
model_base, model_augmented, readout_family, calibration,
n_candidates, n_records, n_trials, n_bags,
coverage_numerator, coverage_denominator,
estimate, ci_lower, ci_upper, bootstrap_scope,
raw_effect, capacity_control_margin,
support_status, implementation_status, control_status,
scientific_status, source_run, code_hash
```

不存在的字段留空并说明原因；不能用 0 表示没运行。

`route_status.csv` 至少分四轴：

- `implementation_status`: NOT_RUN / PASS / NUMERICAL_FAILURE / BUG / BUDGET_LIMITED；
- `support_status`: SUFFICIENT_FOR_SCREEN / DESCRIPTIVE_ONLY / INSUFFICIENT / BLOCKED_INPUT；
- `control_status`: COMPLETE / FAILED / MISSING / NOT_APPLICABLE；
- `scientific_status`: NOT_EVALUABLE / NEGATIVE_SCREEN / SMALL_SIGNAL / MIXED / SUPPORTED_SIGNAL。

一项可以同时 `PASS + INSUFFICIENT + NOT_EVALUABLE`；禁止自动压成“失败”或“阴性”。

### 15.4 主报告必须回答的具体问题

1. G0：共享表是否复现？监督原 head 与重新拟合 probe 有何区别？同儿童读出是否明显不同？处理敏感性是否可比？
2. A2：最终 Ω 是什么、排除了哪些上下文？未校正差异是否存在？残差变得重复是否可能来自共同预测项？
3. C2：旧 MLP 矩阵是否真的完成？solver 改变了哪些定义？空间重建是否精确？被局部参考移除的成分是否带来预测增量？
4. N1：背景和 post 是否都提供条件增益，还是只有历史/背景标签先验？donor 结果是否可能只是分布失配？
5. N2：同样 k 下分布是否超越均值？pre/H_BAG 与重复列对照说明什么？曲线是否使用相同人群？
6. N3：强 H 基线已经解释多少预测风险？post 是否在 H＋pre 之外仍有增量？结构性不重叠区域被如何处理？
7. E0：完整修复结果能否支持“目标任务可读”？不能支持哪些迁移解释？
8. 本轮哪些结果是阴性、哪些是未完成、哪些值得新算法开发？不要只列最好的表格。

### 15.5 推荐图表，非新增搜索许可

每条新路线最多两张主图：配对模型损失/增益及候选支持/关键控制。A2 展示未校正、预测项、残差并列；C2 展示几何信息组成及读出矩阵；N2 展示共同队列的 k 曲线；N3 展示历史基线和 EEG 增量。

图中不公开个体可识别信息，少量候选层级点须经发布审核。禁止为了图好看更换样本、时窗、色标截断或隐藏负值。

### 15.6 完成定义

本轮完成不要求五条路线都阳性。完成要求：每个授权包有可核查回执或明确阻断原因；主要判据与必要对照被执行或标缺失；旧数据未改；输出完整；预算明确；没有将待做工作写成已完成。

最终结论应为“继续哪个**明确问题**、停止哪条**具体实现/估计对象**、下一次还缺什么**新证据**”，而不是泛泛写“需要更多数据/更大模型”。

---

## §16 依据与参考

### 16.1 项目来源（同一冻结 commit）

基准：`https://github.com/W-Yinghao/auditory/tree/191b3a189bea116c4c91fdcfcb6d3bd2945b8dfa`。

- **[D1]** `AGENTS.md`、`PUBLICATION.md`：只读、Slurm、隐私、旧结果保留与发布范围。
- **[D2]** `README.md`、`docs/AUDITORY5_FINAL_STATUS_v1.md`、`reports/auditory5_v1/S4_final_001/FIVE_IDEAS_SCREENING_REPORT.md`：本轮起点的完成/阴性/失败状态。
- **[D3]** `docs/AUDITORY5_REPRODUCTION_v1.md`、`docs/AUDITORY5_JOB_LEDGER.md`：实际工作区、私有索引、已有入口与历史作业；其中历史 queued 文字服从最终回执。
- **[D4]** `docs/AUDITORY5_EXECUTION_DECISIONS_v1.md`、`configs/auditory5_v1.yaml`、`auditory5/preprocessing.py`：因果滤波、参考、分割与支持定义。
- **[D5]** `auditory5/events.py`：完整 QC 前历史链及 previous_run_length 语义。
- **[D6]** `auditory5/routes/route_c.py`、`auditory5/routes/route_e.py`、`auditory5/probes.py`：旧读出目标、权重、校准与失败处理。
- **[D7]** `auditory5/routes/route_a.py`、`auditory5/routes/route_a_controls.py`、`auditory5/routes/a_matching.py`：条件差分、共同响应、回归校正与匹配统计。
- **[D8]** `auditory5/execution.py`、`auditory5/training.py`、`auditory5/models/simclr.py`：编码器与重拟合 probe 的区别、SimCLR 视图和作用范围。
- **[D9]** `results/auditory5_v1/S4_final_001/control_metrics.csv`、`stimulus_decoding.csv`，以及 `A_balance_support_001/`：结果量级、控制、结构空格。
- **[D10]** 用户提供的 `AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md`：前轮意图。本文件在 §0/§13 明确修改本轮授权与预算，不改写前轮已经执行的主方案。

所有路径通过 source registry 保存真实 SHA256。若实际服务器新快照改变接口，须记录 delta，而非伪装成同一版本。

### 16.2 外部方法参考（不是本项目有效性证明）

- **[R1]** Chen et al., *A Simple Framework for Contrastive Learning of Visual Representations*, ICML 2020. `https://proceedings.mlr.press/v119/chen20j.html`。用于说明实例级视图和投影头定义；不声称在本听觉数据中优于监督模型。
- **[R2]** Zaheer et al., *Deep Sets*, NeurIPS 2017. `https://papers.nips.cc/paper/2017/hash/f22e4747da1aa27e363d86d40ff442fe-Abstract.html`。集合不变性背景；本轮 N2 不要求训练 Deep Sets。
- **[R3]** Xu et al., *A Theory of Usable Information under Computational Constraints*, ICLR 2020. `https://arxiv.org/abs/2002.10689`。区分信息与可用读出能力；本轮经验 CE 差不自动等于论文定义的最优预测信息。
- **[R4]** scikit-learn 官方 `MLPClassifier` 文档。`https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html`。求解器/正则背景；真正的修复目标以服务器安装版本源码与数值等价测试为准。

---

## 附录 A：可直接交给执行代理的启动指令

请在现有儿童听觉 EEG 工作区执行 `AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md`。

**先做什么：** 阅读 §0–4 和旧 `AGENTS.md`、v1 最终报告，核对当前 git/未提交改动、受限输入、旧 outer/inner scopes 和已完成任务。冻结本轮独立 source registry，不覆盖 v1，不重新提交 90 个旧表征任务。所有数值操作、测试、环境检查和绘图必须通过 Slurm。

**本轮实际任务：** 实现新 `auditory_next` 适配层并通过单元/集成测试；完成 G0 解码瓶颈诊断；A2 先冻结可比较历史支持，再报告未校正差分和背景校正反例；C2 完成旧 MLP 读出修复，并独立检查跨组均值差/中线信息；N1/N2/N3 分别完成背景条件读出、重复试次分布解码、序列先验之外的 EEG 增量。E 仅修 E0，B/D 不追加新实验。

**计算默认：** 新正式 encoder 训练为 0；新 N 路线的首轮 logistic C=1、MLP lambda=0.001、seed=11，优先复用已存在的合规 inner 特征。不要把新路线每个小变体都乘上多个 seed、正则网格和重训练。C2/E0 的旧网格只为完成原估计器修复。实施前按 §13 生成可审计任务矩阵并遵守资源上限。

**遇到问题：** 缺受限输入则标 `BLOCKED_INPUT`；支持不足则停止该主估计但保留描述；数值失败则留完整回执；预算不足则标 `BUDGET_LIMITED`。继续其他独立包，不反复盘点整个 Phase 0，不用调小配额或换量表制造可运行/阳性结果。主失败族不能在成功子集上聚合成完整科学结果。

**必须守住：** 历史不包含当前/未来标签；bag 不跨身份/时间角色；不同 fold embedding 不混坐标；校准只用训练 OOF；R_SIM、L0 与旧平行结果不择优替换；共同响应不自动等于伪迹，零空间不自动等于非刺激信息，CE 增益不自动等于精确 CMI，数值完成不自动等于发现。

**交付：** 按 §15 提供 `NEXT_ROUND_REPORT.md`、各包报告、完整聚合表、支持/失败/资源账本与哈希。报告哪些明确问题有了新证据、哪些具体实现应停止，保留所有阴性与未完成状态。不要自动发布任何新 participant-derived artifacts，不 Git push。

---

**编写声明：** 本文交付的是下一轮执行规格；文中的 v2 CLI、模块和实验均未在本次文档生成过程中替服务器实现或运行。文档中的旧结果来自指定公共快照；原始 EEG、个体临床值与模型权重未在本地读取。
