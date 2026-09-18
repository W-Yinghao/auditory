# Auditory v3：匹配分布解码、压缩诊断与表征目标干预

> **交给服务器执行代理的设计与实施指令。** 本文件是基于 v2.1 结果的新一轮探索方案，不是已经运行的结果，不覆盖任何旧实验。先实现本文件标为 `NEW` 的入口，再通过 Slurm 执行。本文本身不表示已提交服务器作业。

- 制定日期：2026-09-18（Europe/Paris）。
- 核查仓库：`W-Yinghao/auditory`。
- 冻结参考提交：`eb24106afe170b323859daa9dda597a85e548bb9`；提交时间为 2026-09-17 23:22:45 UTC，即巴黎时间 2026-09-18 01:22:45。
- 前轮结果：`docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md`、`reports/auditory_v21/final_001/`。
- 新工作命名空间：`auditory_v3/`、`private/auditory_v3/`、`results/auditory_v3/`、`reports/auditory_v3/`。
- 配套机器配置：`auditory_v3_plan.yaml`。它是待新入口实现的配置契约，不能直接传给旧 CLI。
- 科研定位：儿童听觉 EEG 解码与信息论；不转向 ERP 峰值/潜伏期、去噪重建、停止采集或量表搜索。

## 0. 给执行代理的总决定

**结束旧的读出器修补链，开始三个有限且可独立完成的工作包。**

| ID | 工作包 | 要获得的新答案 | 本轮方法上限 |
|---|---|---|---|
| P0 | 完整表征与 PCA8 压缩诊断 | 当前刺激读出是否被固定低维截断限制？ | 旧冻结特征、固定正则线性读出；0 新学习型编码器 |
| N2R | 新匹配袋的分布解码 | 在相同历史与试次数下，离散度是否提供均值之外的判别证据？ | L0 特征、嵌套线性读出、固定二次均值对照；0 新学习型编码器 |
| R3 | 表征学习目标干预 | 实例一致性、刺激监督、历史匹配的重复刺激对比，是否保留不同的刺激信息？ | 一个小型 CNN、三个目标、一个正式训练种子；最多 30 次正式编码器拟合 |

三个工作包不是串联的“阳性接力”。P0 没有阳性，不阻止 N2R 或 R3；N2R 没有阳性，也不阻止已获数据支持和能力检查的 R3。推进条件检查的是相应实现、数据及估计能力，不是要求另一条真实结果先显著。

### 0.1 明确关闭的范围

本轮不重跑旧 A/A2 匹配统计、不追问旧 SUP 相对 SIM/RAND 的优势、不重开左右 C/C2 网格、不继续旧 B 历史分类或 D/MUSS 回归；不重开 E0 失败 MLP 矩阵、E1 群体迁移、CI 临床模型；不扩展旧 N1/N3 的正则、种子或交互阶数。旧结果作为背景与限制保留。

不强制 Mamba、HFMCA、tPoE、foundation model。对比学习以 SimCLR / 标签监督的受限 SupCon 为现有方法基础，不预先声称新算法。小型 CNN 是控制变量，不是论文贡献。

### 0.2 这份文件允许服务器做什么

在数据访问及站点权限已存在的前提下，允许实现下面的代码、建立新输出、执行指定测试和能力检查，并按门控推进 P0、N2R、R3 的首轮实验。**不需要为已在本文确定的默认参数反复请示。** 缺少关键私有输入、来源互相冲突、身份/标签无法安全对应时，停止受影响的工作包并交付具体缺项，不编造映射，不阻断其他独立包。

允许新训练小型编码器是本轮相对于 v2/v2.1 的明确变更；旧轮“0 新编码器”不是永久禁令。没有授权自动训练 seed23、搜索新主干、选择新临床终点、修改原始数据或自动 push。

## 1. 已知证据与本轮假设

下列是前轮事实，不是本轮需要重复计算的任务。[R1–R4]

| 前轮事实 | 对本轮的约束 |
|---|---|
| v2.1 的 N1/N3 四条能力 lane 均通过指定强机制检验，但真实受控增量未建立 | 不再泛称“估计器都不能工作”；也不把弱结果当成真实 CMI 为零 |
| N3 R_SIM 五折都选择历史基线，产生逐试次相同预测与 `[0,0]` 区间 | 零宽区间是所选预测器相同，不是信息量精确为零 |
| A2 的四个 SUP−SIM / SUP−RAND 配对区间均跨零 | 不以旧监督表征作为已证实赢家 |
| 新匹配袋：57 个设计候选、114 个候选×half，其中103个half、49个双half候选满足规则 | 保留57、54（非空袋）和49（双half）等不同分母；模型以安全身份组计数，不把它们自动等同独立儿童 |
| 新袋没有进入真实分布比较，主要原因是五角色划分后若干训练/校准角色太小 | 可以改验证结构，不得降低装袋支持门槛来制造可行性 |
| 新读出流程曾先取最多8个PCA方向，且某些修正仅由5个身份组训练 | P0检验截断限制；N2R/R3取消A/B/C/D/E五角色切分 |
| 旧袋的无EEG历史基线 bAcc 约0.985 | 不把旧袋分类高分当作EEG分布收益；不能把该数值外推到新袋或单试次任务 |

**本轮三个假设均未被证实：**低方差方向可能含刺激信息；匹配后重复响应的离散度可能有增量；不同学习目标可能改变刺激信息的保留。任何一个失败都必须能够直接报告，不靠改标签、投影、主终点或样本使其转正。

## 2. 站点、版本、隐私与复用原则

1. 遵守最新 `AGENTS.md` 和 `docs/GPU_SCHEDULING_POLICY.md`。所有数值工作、测试、依赖探针、哈希验证及绘图在 Slurm 中；登录节点仅做阅读、代码编辑、Git与调度操作。[R2]
2. 禁止P100；优先A100/L40S/H100，备选V100/PRO6000。核实实际GPU型号，不能因空闲自动回退P100。
3. 原始EEG、临床表、旧split、旧bag、旧预测、旧源码快照与失败目录只读。不得用v3结果改写旧 `PASS/FAIL/NEGATIVE/NOT_EVALUABLE`。
4. 任何身份ID、精确日期、原始来源路径、逐试次/逐袋数据、特征、模型及预测均写 `private/`，目录0700、文件0600；公共结果仅为审阅过的聚合。**即便 bag_id 是不透明字符串，也不能作为可公开个体记录。**
5. 本轮不读取量表数值，也不用量表完整性新选人。旧N2设计候选集是历史选择限制，明确承认；不是声称全体采集人群的代表性。
6. 只校验这轮实际复用的输入、方法代码和输出，不为无关历史文件循环重做全仓库审计。旧缺失quality数组不是本轮所有任务的总闸门；但不得声称本轮已验证所有眼动/设备伪迹来源。
7. 不覆盖旧计划。本文件为新的v3探索；既有队列已被多轮查看，新外层划分也不会创造独立确认数据。

### 2.1 已存在的入口，与需要新实现的入口

**可读/复用，须先核对实际版本和scope：**

- `auditory_v21/n2_design.py`：`construct_matched_bags`、`build_h_bag_metadata`及既有新袋产物。
- `docs/auditory_v21/N2_DESIGN_LOCK.md`：匹配袋的固定定义。
- `auditory_next/features.py`、`auditory5/execution.py`及每运行源码快照：特征与encoder训练身份的对应。
- `auditory5/probes.py`：20ms分箱、候选权重及现有读出行为的参考。
- `auditory5/models/small_cnn.py`、`auditory5/models/simclr.py`：小型CNN/投影头结构参考。
- `auditory5/events.py`、v2.1完整事件表：QC前历史定义。

**本轮必须新实现，不假装已有可运行命令：**

```text
NEW auditory_v3/{cli,registry,splits,linear,statistics,pca_packet,
                 bags_packet,representation_data,objectives,train,
                 evaluate,capability,reporting}.py
NEW configs/auditory_v3_plan.yaml
NEW scripts/auditory_v3_cpu.sbatch
NEW scripts/auditory_v3_gpu.sbatch
NEW tests/auditory_v3/
```

模块可以合并；不得为了文件数量将一个小实验拆成复杂框架。下面CLI是接口契约，须实现并测试后方可提交。

## 3. 数据入口与不变的观察对象

### 3.1 逻辑来源登记

建立 `private/auditory_v3/<run>/source_registry.json`，将逻辑角色映射到服务器实际路径。**不得按最高/最新目录名猜测来源。** 从v2.1完成回执及input hashes追踪：

| 逻辑角色 | 已核实的历史入口/文件名 | v3用途 |
|---|---|---|
| `matched_bag_members` | v2.1 `n2_design_001` 对应的 `matched_bags.parquet` | 只读使用新匹配袋，不是旧3307袋 |
| `matched_bag_history` | 同运行 `matched_h_bag_metadata.parquet` | 16列H_BAG及来源核对 |
| `candidate_half_support` | 同运行 `candidate_half_support.parquet` | 冻结双half合格候选 |
| `common_cell_support` | 同运行 `common_cell_support.parquet` | 全部固定合格历史格 |
| `design_manifest` | 同运行 `design_manifest.json`、`support_manifest.json` | k、配额、源hash |
| `full_event_history` | `private/auditory_next_v2/S1_support_004/` 对应完整事件表 | QC前历史、block/segment、参考位置 |
| `legacy_outer_folds` | `private/auditory5_v1/splits/splits_001/folds.json` | 原外层身份分组，限制到本轮人群 |
| `legacy_features` | `plan_001` 对应outputs及scope registry | P0的L0/SUP/SIM/RAND，精确trial join |
| `processed_epochs` | 原合规P1_CAUSAL20导出及其回执 | N2R的L0；R3的多通道输入 |

表中是已存在的逻辑入口，不保证服务器绝对根目录相同。查明后写实际路径、SHA256、scope、数组维数和单位；根目录从现有站点配置解析，不另猜路径。

### 3.2 冻结人群 P_MATCH

- 从新匹配设计中取两个half均合格的候选，预期49个候选；以既有 `split_group_id` 连接全部同身份来源。
- 核查一个候选是否确实对应一个安全身份组。若多个候选合并成同组，按组计数并保留原分母，不能拆开提高N。
- 只保留这49组候选的**既有匹配袋成员**。其他单half合格候选不进入主实验。
- P0、N2R、R3尽量使用同一P_MATCH；若某个旧representation缺失成员，只把该P0 lane标为输入不足，不从全部方法中删掉不利人。L0可由已验证epoch重建，不补造神经特征。
- 预期计数不相等时先报告具体差异。不能强制填成49，也不能不声明地换成54或57。

### 3.3 不改变新匹配袋定义

完整继承v2.1：k=8；精确 `previous_code × previous_run_bin` 分层；同候选、half、record/segment内形成袋；两类每格袋数相同；每类格至少16个合格试次、至少3个来源物理块；每袋至少2块、单块最多4个成员；每候选每half每类至少2袋；无放回。[R3]

不增大k、不降低格门槛、不按EEG效果选择格、不在看到风险后重新装袋、不把不完整袋补零。此次直接读取已冻结成员文件，**不重抽10次后挑结果**。

每袋仍带有标签用于研究性构造。这是“已知条件重复观测的离线集合解码”，不是在线未知刺激串自动成袋；不能宣传无需标签部署或临床采集规则。

### 3.4 Schema与索引安全

袋成员至少包含：

```text
bag_id, matched_pair_id, trial_id, candidate_id, split_group_id,
record_id, segment_id, stimulus_local_id, A_half, A_block_id,
physical_block_id, previous_code, previous_run_bin, k
```

数组使用：`X_post [trial,20,100]` 对应250Hz、[0.05,0.45)秒；`X_pre [trial,20,50]` 对应[-0.2,0)秒。先核对实际导出定义，不直接reshape猜测。因果处理、平均参考、无逐trial方差标准化等保持历史P1；不重新优化滤波或寻找时移。

L0：每5个样本取20ms均值，得到post400维、pre200维。保留电极顺序、物理单位、时间轴和trial_id。未经检查不得把ROI包当20通道。

**禁止网络或读出器接收：**bag_id后缀、matched_pair_id、文件名、候选ID、record_id、segment_id、fold编号、原始label列及其衍生one-hot。旧bag_id包含 `_c0/_c1`，必须仅作关联键，绝不能进入特征。H_BAG的16列必须白名单化，不能把整张表转成数值输入。

历史只从QC前的完整事件链构造；未知事件/真实gap/restart的既有处理保持。不得在筛掉EEG后重新计算run-length。

## 4. 重新设计验证：保留身份隔离，提高训练数据利用率

### 4.1 外层划分

沿用原5个外折的 `split_group_id → outer_fold` 映射，限制到P_MATCH。同一身份的所有袋、half、试次与任务必须在同一外折。不得为了让某折更好而换seed。

预期约39组训练、10组测试，实际逐折记录。支持门槛：每个外折至少20个训练组、4个测试组；每个组必须有两类及所需half。若不满足，停止相应主比较并报告，不挑4个成功外折平均。

### 4.2 三种内层安排，分别服务不同问题

| 包 | 内层设计 | 为什么合法且不再切成5个角色 |
|---|---|---|
| P0 | **固定lambda，无模型选择/校准** | 使用旧外层encoder特征；仅训练组拟合scaler/PCA/头，测试组完全未参与encoder；无需让旧encoder参与新的内层筛选 |
| N2R | 外层训练组内3折GroupKFold（每身份一行） | L0无学习型encoder；每次内层重拟合trial scaler、PCA、bag特征变换和读出；用尽约2/3内层训练组 |
| R3 | 每个外层训练集合内一次固定20%身份验证；再全外层训练重训 | 验证身份不参与selection-stage encoder/scaler；选读出lambda后从随机初始化在全部外层训练组重训，测试身份始终隔离 |

R3另要求每外折训练组至少21组，使至少5组内验证与至少16组encoder-fit同时成立。R3另要求每外折训练组至少21组，使至少5组内验证与至少16组encoder-fit同时成立。R3是**外5折＋内单holdout**，不能写成内3折；每目标每外折2个encoder，共30个正式拟合。内验证数固定为max(5,ceil(0.2×外层训练身份数))，按SHA256(seed,outer_fold,identity_id)排序取前若干组，encoder-fit至少16组；不再另切残差训练/温度/候选选择三池。N2R内3折在排序后的“一身份一行”表上调用GroupKFold，不让袋数决定分折；每个fit至少12组、validation至少4组。最终身份映射写入split后冻结，不依赖不同特征视图重新生成。

不汇集不同外折或内层encoder的embedding训练同一个头。可以合并其标量预测、损失和分组统计；内层/最终特征空间分别拟合各自的头。

### 4.3 不把交叉验证当作新的独立队列

本轮是已探索队列上的新估计对象与新方法测试。外层隔离防止本次计算的测试泄漏，但不能抹去之前的选题与方案选择。任何下一阶段论文主张仍需冻结后的额外独立证据。

## 5. 统一读出器与评分约定

### 5.1 读出目标函数

统一实现二元正则logistic：

\[
\mathcal L(w,b)=\sum_i \bar w_i\{\operatorname{softplus}(w^Tx_i+b)-y_i(w^Tx_i+b)\}
+\frac{\lambda}{2}\|w\|_2^2,\qquad\sum_i\bar w_i=1.
\]

bias不惩罚。候选/half/格/类别加权先归一化；不得将sklearn的C、按总权重缩放的alpha和这里lambda直接互换。使用float64和解析梯度，权重缩放不改变目标。用合成有限差分测试验证。

首轮只用该凸读出器，不引入MLP读出族。默认L-BFGS最大1000步；从同一状态允许一次到2000步的数值恢复，目标、lambda和数据不变。每个fit记录初末目标、梯度∞范数、有限性与solver message。任何非有限或scope错误为硬失败。

预定合格条件：参数/预测有限，最终目标不高于初始目标（容差1e-10），且梯度∞范数≤1e-5，或求解器成功且梯度∞范数≤1e-4。不能仅靠最后100步loss平坦宣称合格。2000步仍不满足则标记该比较数值失败，不静默放宽。lambda默认[0.001,0.01,0.1]。

本轮主评分**不做temperature或混合校准**，logistic原生概率即预测。改变校准会增加选择自由度；不为得到正bits追加温度池。可以报告Brier/AUC诊断，不能事后以AUC替代CE主终点。

### 5.2 目标人群与权重

所有主风险以身份组等权。N2R先在每组内对两个half等权，再对该half固定合格历史格等权，再对两类等权，再对同格同类袋等权。P0/R3在相同层级内对袋成员试次等权；成员无重复，因此不把重复采样作为新的独立样本。

记该固定观察分布为 `P_MATCH_bal`。它不是自然临床刺激比例、不是整个档案分布，也不是原v2.1的P_nat。H_BAG仍可能因其他时序变量保留可预测性，必须报告而非删列。

### 5.3 主量与推断

- `gain = risk(reference) − risk(candidate)`，正数表示候选测试风险更低。
- 单试次单位为bits/trial；袋单位为bits/bag，绝不直接跨表相加。
- 在平衡二分类分布下可另报`J=1−CE_bits`；负值照实保留。J是读出器依赖的预测得分，不是精确MI。[R8]
- 每组先得到一个完整的配对风险差，再做2000次身份组bootstrap；同一对比族共享draws。按原外折分层重采样组，不把试次/袋/seed当独立儿童。
- CI条件于已拟合模型与冻结观察对象，不重拟合全流程。报告折别风险和正效应组比例；比例仅描述，不另当显著性门槛。
- 保留主对比族及次要对比全部结果，不将“某个区间跨0、另一个不跨0”当模型间差异。
- 数值0和缺失分开；复制模型/零修正导致相同预测时，注明零宽区间来源。

## 6. P0：完整表示与PCA8诊断

### 6.1 问题与样本

只检验：在相同P_MATCH成员、外折、预测器和正则尺度下，PCA8是否造成**可观察到的预测风险差**。不新训encoder，不挑新时窗，不把任一结果自动归因于Shannon信息丢失。

主representation为旧R_SIM，L0/R_SUP/R_RAND平行描述。使用各外折原来排除其test身份的特征，核验**实际**训练scope而不只看文件名。P0不做新的内层参数选择，避免将见过内validation的旧encoder伪装成完整嵌套重拟合。

### 6.2 四个坐标视图

仅用外层训练组拟合每坐标加权center/scale，得标准化特征U。拟合候选等权、无白化PCA。记Q8为前8个方向，QR为其正交补：

- `FULL`：完整U（R_SIM/SUP/RAND为64维，L0 post为400维）。
- `PC8`：UQ8。
- `REST`：UQR。
- `PC8_DUP`：[UQ8/√2, UQ8/√2]。

**投影后不再次逐轴标准化/白化。** 这样FULL、PC8及其补空间的L2几何可比较；PC8_DUP按1/√2复制是等距冗余对照，不是任意增加惩罚强度。训练rank≤8时，REST标为零维/不适用，FULL和PC8的等价性仍可检查，不补造方向。

所有视图使用lambda=0.01作为主配置；0.001和0.1为两项预先列出的敏感性，全部报告，不能选其中最好的替主。

### 6.3 主终点与解释

主终点：`T_P0 = R(PC8) − R(FULL)`，R_SIM、lambda0.01、post。

必报：FULL/PC8/REST/PC8_DUP的CE、J、bAcc、AUC；配对FULL−PC8；FULL与[PC8,REST]正交重构下的目标/预测等价测试；PC8与PC8_DUP的预测一致性；选定方向训练方差和数值rank。

pre诊断只做R_SIM与L0在lambda0.01下的FULL/PC8，注明pre200ms与post400ms长度不同。它是污染/背景提示，不是严格等长的神经阴性对照。

**如何判断：**

- T_P0>0.002 bits/trial且配对CI下界>0，并且FULL相对均匀先验具有正J：记录`COMPRESSION_LIMITATION_SIGNAL`，值得后续验证；不是本轮宣布低方差神经编码。
- T_P0小或CI跨0：`NO_DETECTABLE_COMPRESSION_PENALTY`，不再扫PCA维数。
- FULL/PC8都很弱：只能说该读出没有定位到截断代价，不能称信息不存在。
- FULL更差：可能是有限样本/估计代价；保留负值，不写成增加真实变量导致负互信息。

上述量级是本轮研究筛选规则，不是显著性校准或临床标准。

### 6.4 拟合规模

4 representations × 5 folds × 4 views × 3 lambdas = 240个主/敏感性线性头；pre额外20头，上限260。缺失lane单列，不能从其他lane挑最高值补齐。P0的结果不决定N2R的投影或R3的损失。

## 7. N2R：匹配重复响应中，离散度是否增加均值之外的信息？

### 7.1 本轮改变什么，不改变什么

**改变验证结构，不改变观察对象。** 使用第3节已经冻结的新k=8袋，取消旧五角色，将全部外层训练身份用于嵌套模型开发。

主representation是L0，避免旧encoder的D_inner排除范围限制。不是把旧L0结果改成阳性主结果，而是新匹配数据上的新比较。所有变换由本轮内层/外层训练身份重拟合。

### 7.2 低维主表征与完整L0敏感性

主低维试次表征：训练内L0 post标准化后，候选/half/格/类别等权拟合**无白化PCA8**，得z∈R^8。pre另行训练自己的8维变换，不跨post/pre复用轴。

每袋计算：

\[
\mu=\frac1k\sum_{j=1}^kz_j,\qquad
v=\log\left(1+\frac1{k-1}\sum_{j=1}^k(z_j-\mu)^2\right).
\]

v逐坐标计算，k固定8；**不是完整协方差、不是PID、不是任意分布的充分统计。** 不逐袋强制去均值原始输入，不用类别分别中心化。log1p之前的尺度由训练trial scaler固定。

为避免把PCA8阴性误写成完整原始信息阴性，预先另列`FULL_MU`与`FULL_MU_VAR`两个400维L0均值/对角方差敏感性。它们仅检验线性均值读出之外的有限增益，不替换下述主低维二次均值控制。

### 7.3 让“均值基线”可以读出简单非线性

即使两个类别的总体均值相同，有限bag的样本均值分布也可能不同。若均值只接线性头、方差可直接提供二次信息，不能把优势自动归因于均值从未包含的信息。

因此定义固定二次均值基：

\[
\phi_2(\mu)=[\mu_1,\ldots,\mu_8,\{\mu_i\mu_j:1\le i\le j\le8\}],
\]

共44维。训练内对这44维做一次块标准化，各视图复用同一变换。重复列对照在标准化后按1/√2构造，不能再逐列归一化抵消该缩放。

**二次均值控制也不是全体非线性读出器上界。** 最终只能写“超过这套预定均值读出族”，不声称严格识别了条件互信息。

### 7.4 固定九视图矩阵

H为旧新袋设计锁中的16列H_BAG，完整保留，不因为其预测强而删列。所有视图在同一bag与身份上训练/评分。

| ID | 输入 | 作用 |
|---|---|---|
| H | H | 无EEG基线 |
| HM | H, μpost | 对接早期线性均值问题 |
| HMV | H, μpost, vpost | 早期均值加方差的匹配袋版本 |
| HQ | H, φ2(μpost) | **主参考**，允许二次均值信息 |
| HQV | H, φ2(μpost), vpost | **主候选** |
| HQQ | H, φ2(μpost)/√2, φ2(μpost)/√2 | 冗余/实现对照 |
| HPRE | H, φ2(μpre), vpre | pre背景对照 |
| HPREQ | H, φ2(μpre), vpre, φ2(μpost) | pre与post均值共同参考 |
| HPREQV | 上一行, vpost | 检查pre之外的post方差增量 |

每个视图的lambda仅在外层训练组内3折，以候选等权OOF CE选择[0.001,0.01,0.1]；精确平局选更强惩罚。每个内折重拟合全部trial变换、PCA和bag-feature scaler。最终用全部外层训练组重拟合后测试。没有额外temperature、残差训练池或5角色选族。

九视图×五折×(三lambda×三内折＋一次最终拟合)=450个头。完整400维敏感性两视图额外100头；主包上限550头。

### 7.5 主终点与必要对照

主终点：`T_N2R = R(HQ) − R(HQV)`，单位bits/bag。

必须同时交付：

- `R(H)−R(HQV)`：是否真的优于无EEG元数据，而不只优于一个差的均值模型。
- `R(HQQ)−R(HQV)`及HQQ/HQ的数值等价：避免扩维/重复列解释。
- `R(HPREQ)−R(HPREQV)`：post方差是否在预刺激信息之外仍增加预测证据。
- `R(HM)−R(HMV)`：预定次要结果；若只有这项阳性而主项阴性，说明简单均值非线性可以解释该改善，不宣传分布信息独有性。
- FULL_MU/FULL_MU_VAR敏感性与所有CE；若仅该敏感性阳性，标记新线索，不替换主PCA8/二次均值结论。
- 固定两half分列风险；两half不能当作两批独立儿童，也不要求各自显著。成员/袋数全量保留。

### 7.6 研究决定

`PROMISING_DISTRIBUTIONAL_EVIDENCE`需同时满足：主gain≥0.005 bits/bag且CI下界>0；候选相对H和HQQ优势CI下界>0；pre条件增量点估计>0且其CI下界>0；全部直接相关测试和支持完整。

这是本轮“值得追加独立验证”的复合筛选，不是正式家族错误率控制或临床阈值。只满足主数值而pre/元数据对照不支持，标为`UNRESOLVED_ALTERNATIVE_EXPLANATION`，不自动开发集合网络。

若主CI跨0或效应很小，记录`NO_CONTROLLED_GAIN_ESTABLISHED`。CI仍覆盖最小量级时，明说“不精确”，不是已排除该效应。单一敏感性好看不授权继续扫k、维数、covariance、RFF或量表。

### 7.7 下一步边界

本轮不运行k曲线、不用重新装袋增加名义样本、不训练Deep Sets。首轮真实矩阵完成后才考虑下一轮独立复制或新分布模型；不把一个有信号的概率误差改名为听觉容量、康复速度或临床诊断。

## 8. R3：真正改变一次表征学习目标

### 8.1 研究问题与公平比较

问题：在相同身份、事件历史匹配、原始试次预算和编码器下，实例对比、直接刺激监督和跨重复刺激对比，是否产生不同的**未见身份刺激可读性**？

研究重点是学习目标选择，而不是跨被试准确率排名本身。主干固定`SmallEEGCNN_v1`的20通道、64维结构（可直接按已核查源码复用），不新增深层架构；不强制任何旧原创模块。

三个目标都从随机初始化训练，使用**完全相同的训练trial池和原始试次曝光计划**。正式训练种子固定11。不得将旧的不同人群/训练长度SimCLR作为这次目标对照的主基线。

### 8.2 训练单元：同身份/历史格内的四元组

只从P_MATCH既有袋成员构造训练四元组，保持同`split_group_id × A_half × record_id × segment_id × previous_code × previous_run_bin`。

每组四个不同原始trial：两个class0，两个class1；每类两个trial来自不同physical block，彼此原始时刻间距至少为已核查有效滤波支持（不得小于10.823秒）；任何两成员不重复且直接epoch不能重叠。主分组不用当前`current_run_length`，因为它含当前事件信息。

不要求两类共享完全相同的物理block ID（这可能制造新空格）；但四元组在同half/精确历史格，且两类在固定池内等权。慢状态及设备影响依然可能存在，作为限制与pre/元数据对照处理。

该配对不是一套重新挑人的规则。若某固定合格格无法形成四元组，先保留其计数、停止R3主目标对比，不自动删除这个格或儿童。P0/N2R不因此阻断。

### 8.3 采样计划

- batch原始trial数64，即16个四元组；每个batch优先16个不同身份，训练集少于16组则支持不足，不缩小到很少的身份强行跑。
- 每epoch抽样步数 `ceil(N_unique_train_trials/64)`；身份、half、合格历史格逐级等权，再在格内选试次。允许跨batch/epoch重复抽训练样本，记录实际曝光，不算新增N。
- batch内部同一trial不能重复；四元组两类对称；记录采样失败/重试，若无法达到冻结曝光计划，作为采样实现问题修复，不按效果减弱条件。
- 三个目标共用固定的每epoch trial ID计划和增强随机数。计划只由训练元数据及seed决定，测试/验证trial不进入负样本池。
- 每trial生成两个视图：训练尺度下加0.02标准差高斯噪声。不做时间打乱、通道置换、大幅随机裁剪或强幅值缩放。

**SimCLR目标不读取class label，但本实验的匹配池和采样器使用了标签。** 方法报告必须写“在标签匹配的训练池上使用实例级SimCLR目标”，不能宣称整个流程完全无监督。[R6–R7]

### 8.4 三个固定目标

#### SUP：直接刺激监督

同一64维encoder后接线性二类头，对两个增强视图的CE取均值。评估时使用64维encoder输出的新线性probe，不以原训练头替代其他方法的probe。原头表现作为优化诊断单列。

#### SIM：实例级SimCLR

投影头64→128→64，最后L2归一化，温度0.2；正对是同一trial的两个噪声视图，负对来自batch其他原始trial；标准NT-Xent掩去自身。[R6]

#### MATCH：刺激监督＋历史匹配的跨重复SupCon

沿用SIM同样encoder和projector，并加入与SUP完全同型的线性刺激训练头。先定义一个四元组内的对比项；对每个anchor视图，只在其四元组内计算：

- 正样本：**另一个同class原始trial的两个视图**；
- 分母：其余三个原始trial的全部六个视图；
- anchor自身原始trial的两个视图均不进入分母，不能通过自身增强捷径完成目标；
- 对两个正样本的log-softmax损失取均值，然后平均全部anchor。

\[
L_{contrast}= -\frac1{|A|}\sum_{a\in A}\frac12\sum_{p\in P(a)}
\log\frac{\exp(\mathrm{cos}(g_a,g_p)/0.2)}
{\sum_{j\in D(a)}\exp(\mathrm{cos}(g_a,g_j)/0.2)}.
\]

总训练目标固定为：

\[
L_{MATCH}=L_{CE}+0.1L_{contrast}.
\]

CE与SUP使用同一标签、线性头和两个增强视图均值；系数0.1事先固定，不调参。**不单独用四元组对比项训练MATCH。** 仅在每个身份/历史格内部定义同类和异类，允许不同组出现不一致的类别方向；统一CE提供跨组类别读出的约束。该约束不证明消除了所有个体或设备信息。

`|P(a)|=2, |D(a)|=6`以及总目标中的CE项必须写单元测试。这个目标是标签监督的受限对比学习，不声称是新MI下界或新HFMCA。与SIM的比较同时改变了正样本含义和负样本结构；结果属于**整个预定目标/采样策略**的差异，不能独立归因于其中某一条边。

### 8.5 训练预算与内层选择

三个目标共同使用：AdamW，lr=3e-4、weight_decay=1e-4，60个固定epoch，前5个epoch线性warmup之后cosine，grad clip5，float32，batch64。无BatchNorm、无dropout，与既有小CNN结构一致。每次从同seed初始encoder参数出发。

不根据测试表现延长epoch或选择checkpoint。**默认取第60个epoch**；每10epoch仅存训练loss、梯度、表征尺度、实际样本曝光和阶段时间。SIM/MATCH损失不同，不能直接比较数值大小作为优劣。

每外折：

1. 用20%的外层训练身份作固定inner validation，其余训练selection-stage encoder；val不进入训练scaler、对比队列、统计量或梯度。
2. encoder训练固定60epoch。在inner-fit身份上拟合指定probe，在inner-val上从三个lambda中选一个。不能用outer-test挑lambda/epoch。
3. 从相同初始化重新在**全部外层训练身份**训练60epoch；重拟合scaler与probe，在outer-test评价一次。

每目标每外折两个encoder：3×5×2=30正式拟合。允许3个合成训练smoke，另计；不再训练一个“更好的主干”。除事故恢复同目标同状态之外，不自动追加seed23。

### 8.6 评价矩阵：完整表示为主，不强制PCA8

所有方法probe使用完整64维encoder输出（不是projector输出）。训练内标准化。每个目标、每外折三个视图：

- `Zpost`：仅刺激后表征；
- `Htrial+Zpost`：加入相同显式历史/时间上下文；
- `Htrial+Zpre`：pre诊断。

另外共同拟合一次`Htrial`基线、L0 post基线与随机初始化CNN的同范围probe。Htrial白名单：previous_code one-hot、previous_run_bin one-hot、log1p(previous_gap_s)、缺失gap指示、position_fraction、position_fraction²及half；未知值单列。**不含当前run-length、当前位置的类别频率、trial编号、bag标签后缀或任何临床字段。**

Htrial+Z使用同一种logistic，不重开旧N3的offset/校准/四候选链。它只是新表征实验中必要的有限条件读出控制；即使有收益，也叫给定读出族的风险增益，不声称精确条件信息。

pre时窗长度为post的一半且encoder在post上训练：pre结果只作诊断，不能以较低pre分数证明皮层来源。若post优势与pre同方向，解释应更谨慎，而非删pre。

### 8.7 主终点及成功的含义

主终点：

`T_R3 = R(Htrial+Zpost_SUP) − R(Htrial+Zpost_MATCH)`。

以SUP为主参考，检验增加历史匹配的跨重复约束是否提供额外价值；MATCH相对SIM为预定次要对比，不把“使用标签”本身包装为方法优势。

必报：MATCH−SIM、SIM−SUP的配对比较；MATCH/SIM/SUP相对Htrial、L0、随机encoder的风险；post-only与pre控制；不同fold预测表现、训练曝光、参数量、训练时间、representation rank（仅诊断）。

本轮推进信号需：主gain≥0.005 bits/trial且CI下界>0；MATCH相对Htrial的增益CI下界>0；不被pre/元数据单独解释。若仅超过SIM而不能超过SUP，记录`NO_ADDED_VALUE_OVER_SUPERVISION`，不宣称匹配对比有增量。若只比一个弱SIM强、不比L0/RAND强，标记`NO_LEARNING_ADVANTAGE_ESTABLISHED`。

任何目标表征接近常数都保留训练结果，诊断是学习失败/目标未提供可用信息，不通过排除这些fold制造有效族。严格NaN/Inf或输入错位才属于硬数值失败。

R3的目标是回答“是否值得继续研究这种信息目标”，不是立刻建立听觉功能生物标志物。无临床回归、无A2重复性复活、无声调/跨任务扩展。

## 9. 最小能力与单元测试：足够阻止错误，不再建设无限审计矩阵

### 9.1 必须通过的硬测试

| 类别 | 本轮必须覆盖 |
|---|---|
| 身份与来源 | 原外层test不进入旧/新encoder；内validation不进入R3 selection-stage encoder；trial join不依赖行顺序；bag两个类别及半份完整；跨归档同身份不拆分 |
| 泄漏 | 修改outer-test标签/EEG后，训练参数、lambda选择、PCA、四元组计划hash不变（只有推断输出可变）；网络输入白名单拒绝 `_c0/_c1` 等ID信息 |
| 权重 | 每身份总权重相同，每half/格/类别按第5节；重复抽样不改变独立N；权重整体倍乘不改变目标 |
| PCA | FULL与完整正交重构风险一致；PC8_DUP的1/√2与L2等价；投影后没有隐式白化；rank不足保留真实维数 |
| Bag | 恰好8成员；无重复trial；同record/segment；≥2物理块且单块≤4；所有共同合格格保留；内层fit只读train成员 |
| 特征 | v的ddof=1、log1p顺序正确；二次均值44维；所有scaler仅在fit组训练；H白名单不含current_run_length；预刺激映射独立但对齐 |
| 训练目标 | SIM自身掩码/正对正确；MATCH每anchor正对2、分母6且排除同原trial，含统一CE约束；跨subject或跨history替换会被pair audit拦截；三目标曝光一致 |
| 优化与统计 | 正则目标/梯度finite difference；复制输入等价；固定概率手工CE与程序一致；同预测的差值为0；bootstrap以身份非bag为单位；NaN不记为0 |

不要求重新执行不被本轮调用的全部历史测试。复用旧模块的相关测试运行一次，并保存其代码hash；代码改变后只重跑受影响测试与对应能力门控，保留旧回执。

### 9.2 P0定向能力检查

3类合成输入，每类5个固定评估seed：

1. 高相关背景方向主导方差，标签在低方差正交方向；标准化后仍保持低特征值标签方向。
2. 标签只在主PCA子空间。
3. 标签独立的null。

每世界仅FULL/PC8、lambda0.01，用与真实P0相同变换和读出；30头。另做正交/复制恒等式测试，不通过就不运行P0真实比较。第一类强注入应至少4/5世界FULL优于PC8且FULL bAcc≥0.75；第二类应能读出主子空间；null不要求精确零，但不能出现源代码/标签直通。若能力不通过，修算法/测试后换一组从未看过的合成seed，禁止调整真实参数后“补一个容易世界”。最多一次合成开发修订。

P0检查验证固定强方向与坐标实现，不声称对真实微弱差异有充分功效。

### 9.3 N2R独立能力评估

能力机制在新匹配袋的实际元数据规模上建立：使用真实身份数/每组袋数/half/格/时间依赖结构，但生成全新的合成数值特征；不读取临床或用真实EEG效果拟合生成器。每世界指定一个外折（轮换0–4），内3折与lambda选择均使用真实将要执行的代码。

三机制，每机制20个独立评估seed（53001起的固定不交叠编号），仅拟合HQ/HQV两个核心视图；每世界20个头，上限1200头：

- `VAR_EXTRA`：同类别总体均值不变、类别协方差在固定低维方向不同，含相关重复噪声；**不逐bag去均值**。强方差设定先在独立开发seed上确定，允许一次冻结，不用真实结果调强度。均值可能已有部分信息，考查HQV相对HQ的增量。
- `MEAN_SUFFICIENT`：标签在条件均值，方差在给定H和均值后不再增加构造中的信息。二次均值基线应可工作，不因多8列自动通过。
- `HISTORY_ONLY`：标签由已提供H字段决定，数值响应仅携带H/时间相关扰动，给定H后没有注入额外标签信号。防止背景/扩维被当分布信息。

门槛在运行前冻结：所有核心世界可评价；VAR_EXTRA中至少16/20世界gain>0.01 bits/bag；两个null分别不超过2/20世界满足“gain≥0.005且配对CI下界>0”。完整分母、实际gain、CI和Monte Carlo二项区间都交付。20世界并不证明任意实际假阳性率受控；它只是有限的算法能力筛查。

若强世界失败，不执行N2R真实矩阵，写明能力不足；不以零个真实结果称分布不存在。若只有弱信号不能恢复，不据此无限调生成器，报告该灵敏度限制即可。无需要求P0真实先阳性。

### 9.4 R3最小训练能力检查

最多3个合成训练smoke（每目标1个），用非临床合成20通道数据，带独立身份背景、显式强刺激模式与重复块。它们验证训练图、采样、GPU与loss，而非评价真实数据功效：

- SUP/MATCH须能在强合成未见身份上学到明显高于机会水平的刺激解码（固定门槛bAcc0.80）。
- SIM须满足正确pair mask、有限loss/梯度和训练输出；不要求它在合成刺激分类中优于监督/MATCH，因为这正是方法比较要检验的内容。
- 通用CNN全量forward/backward、恢复checkpoint、重新启动后的同状态预测一致性通过。

不得把测试fold中的一部分真实数据拿来作“合成smoke”。可用真实训练fold的shape/单位作零拟合接口检查，但看过真实模型风险后不能修augmentation再称预先冻结。

### 9.5 各包门控独立

```text
来源/数据安全通过 → 支持与配置冻结 → 对应测试/能力通过 → 对应真实包
                                              ├─ P0
                                              ├─ N2R
                                              └─ R3
```

门控代码在加载模型训练数据和调用fit之前检查回执及算法hash。不能把“capability已经提交”“脚本结束码0”或另一包的能力PASS当作本包授权。

## 10. 具体执行顺序

### Phase S0：一次性接入与冻结，零真实模型拟合

1. 读取第2–3节文档和来源，记录当前HEAD以及相对eb24106的差异。若有新推送，只检查相关数据/代码是否变化；不要自动切换主结果版本。
2. 注册匹配bag、支持表、完整历史、P1 epoch、旧fold及旧特征。核对49个双half候选的实际身份组，保留57/54/49不同分母。
3. 冻结P_MATCH成员、五外折、N2R内三折、R3内单holdout及四元组规则。只依据元数据，不读取新科学效果。
4. 输出精确fit catalog和资源reservations。若预算不足，先删未授权的额外任务，而不是降低数据门槛。
5. 保存本文件和机器配置hash，创建不可变源码快照。做一次privacy/scope smoke。

### Phase S1：测试与独立能力

实现新增模块；运行第9节测试/能力。P0/N2R的CPU能力可并行；R3合成GPU smoke独立。不要重跑880世界的旧N1/N3门控。

### Phase S2：P0与N2R真实比较

通过各自门控即运行；两包可并行。生成一次完整结果表，不用P0结果调整N2R的PCA维数。若P0提示截断问题，记录为下一轮方向；本轮预定完整400维N2R敏感性已经覆盖有限检查，不临时增加更多维数。

### Phase S3：R3真实训练与读出

数据支持与训练能力通过后即可启动，不要求P0/N2R阳性。先完成所有selection-stage的15个encoder及其训练内probe选择，再训练15个final encoder并做outer-test推断。这样能清楚分开选择与测试，同时不用五角色训练池。

禁止第一外折测试结果好看后给某目标加epoch；禁止某目标不好后换backbone；一次硬件中断可以从已保存同状态恢复，不能当作重新随机启动的机会。

### Phase S4：汇总与研究决定

聚合所有外层预测和限制，完成三包比较与方向建议。未通过能力、缺少输入、数值失败、真实未见增量分别标记；不输出一个掩盖差异的“总体科研PASS”。本轮结束后不自动追加种子或再次开旧路线。

## 11. 任务与预算上限

预算是本轮服务器执行的上限，不是对完成时间的承诺。按站点已授权配额核实，可减少非必要并发；不得使用禁用硬件。

| 类别 | 最大规模 |
|---|---:|
| P0真实线性头 | 260 |
| N2R真实线性头（含400维敏感性） | 550 |
| R3 probe / H / L0 / random对照 | 280 |
| N2R独立能力头 | 1200 |
| P0能力头、模块测试和R3 smoke probe | 预留，不超过其余710 |
| **本轮所有新CPU head fits上限** | **3000（失败及恢复的重新fit也计入）** |
| **R3正式encoder fits** | **30** |
| 合成encoder smoke | 最多3，单独计数 |
| 训练随机种子 | 正式仅11；不自动启动23 |
| CPU申请预算上限 | 160 CPU core·h |
| GPU申请预算上限 | 16 GPU·h |
| 最大并发 | 4个CPU作业、2个GPU作业 |

CPU预算包含GPU作业同时申请的CPU核时，不另建一个不计账的CPU池。GPU训练任务按实际计划最多15 GPU·h、3个smoke最多0.5 GPU·h，余下0.5 GPU·h仅用于已登记的必要测试/同状态恢复。CPU默认2核/16GB，GPU每作业1卡/4CPU/16GB；需要的实际内存由一次shape和小批前向探针确定。内存不足是实现/资源问题，不通过删除长记录或差质量儿童来挽救。

R3 array最多30个训练任务，按 `%2` 限制并发。每个正式任务先以30分钟申请作为最大初始资源单位，则30任务上界15 GPU·h，另给3个≤10分钟smoke和测试留预算；执行前必须按实际计划核对总上界，不能同时把每任务1小时和16小时总上限写成可兼容。

若单任务硬预算不够，先记录已完成步数、checkpoint和资源，再按仍可用的本轮总预算登记一次同状态恢复；不能悄悄多跑完整epoch。预算无法支持全部主对比时输出`BUDGET_LIMITED`和具体缺项，不选择性缩减差的目标。

`fit_events.jsonl`在每次真实fit前登记；一套源码/配置的重复hash不应造成重复昂贵作业。复制数值结果/已有完成模型的推断不算新训练，但仍计运行资源。

## 12. 新CLI契约与作业示例

下面入口均为**NEW，服务器须先实现**。不能直接把示例命令当作仓库已经支持的功能。所有命令接受`--config`、唯一`--run`；涉及来源的命令接受`--registry-run`、`--split-run`；涉及真实fit的命令必须显式接受`--gate-run`。

```text
python -m auditory_v3.cli inspect
python -m auditory_v3.cli freeze-support
python -m auditory_v3.cli test
python -m auditory_v3.cli make-plan
python -m auditory_v3.cli capability --packet P0|N2R|R3
python -m auditory_v3.cli run-pca
python -m auditory_v3.cli run-bags
python -m auditory_v3.cli train-representation --task-index INTEGER
python -m auditory_v3.cli select-probes
python -m auditory_v3.cli evaluate-representations
python -m auditory_v3.cli finalize
```

### 12.1 公共wrapper行为

`scripts/auditory_v3_cpu.sbatch`和`auditory_v3_gpu.sbatch`：

- `set -euo pipefail; umask 077`，环境Python从现有站点配置读取；不安装或升级整套环境。
- 实际运行进程来自该run的不可变source snapshot，保存snapshot/config/输入hash；不让排队期间的源码编辑改变任务。
- 检查 `SLURM_JOB_ID`，以及GPU型号白名单/禁止P100；任何入口都不能绕过数据或能力门控。
- 允许任一目录不存在时创建唯一新run，存在时拒绝覆盖。resume必须指向同状态、同目标、同计划的已登记checkpoint。
- 日志写private；不在stdout打印参与者名、原始路径或逐人结果。

### 12.2 提交示例（实现之后）

下面变量从已核实站点配置设置，不猜账号/分区；run后缀仅示意，存在则生成新的唯一名字。shell命令只做调度，不在登录节点运行分析。

```bash
export AUDITORY_ROOT="/absolute/path/resolved/from/site/config"
export CPU_PARTITION="<verified_cpu_partition>"
export GPU_PARTITION="<verified_A100_or_other_allowed_partition>"
cd "$AUDITORY_ROOT"
umask 077
mkdir -p private/auditory_v3/logs
chmod 700 private/auditory_v3 private/auditory_v3/logs
CFG=configs/auditory_v3_plan.yaml

# 接入和支持冻结；wrapper将参数传给已实现的NEW CLI。
J0=$(sbatch --parsable --partition="$CPU_PARTITION" --cpus-per-task=2 \
  --mem=16G --time=00:15:00 --output='private/auditory_v3/logs/%j.log' \
  scripts/auditory_v3_cpu.sbatch inspect --config "$CFG" --run inspect_001)

J1=$(sbatch --parsable --dependency="afterok:$J0" --partition="$CPU_PARTITION" \
  --cpus-per-task=2 --mem=16G --time=00:15:00 \
  --output='private/auditory_v3/logs/%j.log' \
  scripts/auditory_v3_cpu.sbatch freeze-support --config "$CFG" \
  --registry-run inspect_001 --run support_001)

# 测试、计划、三包能力分别提交；这里只示例一个能力lane。
# 测试/计划run必须实际完成并与源码绑定，不以字符串存在当作PASS。
sbatch --partition="$CPU_PARTITION" --cpus-per-task=2 --mem=16G \
  --time=01:00:00 --output='private/auditory_v3/logs/%j.log' \
  scripts/auditory_v3_cpu.sbatch capability --packet N2R --config "$CFG" \
  --registry-run inspect_001 --split-run support_001 --gate-run tests_001 \
  --run capability_N2R_001

# 只有对应能力回执PASS后，才调度真实包；模块内部也二次校验。
sbatch --partition="$CPU_PARTITION" --cpus-per-task=2 --mem=16G \
  --time=02:00:00 --output='private/auditory_v3/logs/%j.log' \
  scripts/auditory_v3_cpu.sbatch run-bags --config "$CFG" \
  --registry-run inspect_001 --split-run support_001 \
  --gate-run capability_N2R_001 --run N2R_001

# R3分selection/final两阶段array，每阶段15个任务，最大2并发。
# --stage属于wrapper计划分发参数；task-index由SLURM_ARRAY_TASK_ID提供。
sbatch --partition="$GPU_PARTITION" --gres=gpu:1 --cpus-per-task=4 \
  --mem=16G --time=00:30:00 --array=0-14%2 \
  --output='private/auditory_v3/logs/%A_%a.log' \
  scripts/auditory_v3_gpu.sbatch train-representation --stage selection \
  --config "$CFG" --registry-run inspect_001 --split-run support_001 \
  --gate-run capability_R3_001 --run R3_selection_001
```

执行代理必须补齐test/make-plan/选择probe/final训练/evaluate/finalize的真实依赖，不能照抄一个没有tests_001的示例启动后续任务。依赖以`afterok`和显式receipt双重检查，不能用固定sleep。数组父run可以共享目录，**每个任务只能写自己的唯一子目录**，由原子创建保证不会互相覆盖；不沿用单worker独占父目录的冲突模式。

## 13. 输出契约

### 13.1 私有文件

```text
private/auditory_v3/<run>/
  start.json                         # git/source/config、授权范围、资源
  source_registry.json               # 实际受限路径与hash
  members.parquet                    # P_MATCH及精确bag/trial映射
  splits.json                        # 外层、N2R内层、R3内holdout
  fit_catalog.csv / fit_events.jsonl # 拟合前登记、失败/恢复
  task_<id>/                         # 独立不可变训练子目录
  transforms/ models/ checkpoints/
  predictions.parquet               # trial或bag层，不能公开
  group_losses.parquet              # 身份层，不能公开
  completion.json
```

### 13.2 聚合与文档

```text
results/auditory_v3/<round>/
  input_support_aggregate.csv
  P0_metrics.csv / P0_paired_effects.csv
  N2R_metrics.csv / N2R_paired_effects.csv
  R3_metrics.csv / R3_paired_effects.csv
  capability_summary.csv
  training_summary.csv
  route_status.csv
  resource_summary.json
  source_hashes_public.json          # 不含原始个体路径
reports/auditory_v3/<round>/
  RESEARCH_REPORT_CN.md
  EXECUTION_REPORT.md
  LIMITATIONS.md
  figures/                          # 仅聚合图
```

每条效应记录：packet、representation/target、population、reference、candidate、window、unit、lambda或选择规则、estimate/CI、n_identity_groups、n_bags/n_trials、outer_folds、bootstrap_scope、control_state、source_run、primary_flag。

不包含身份行的高维列表；人数很小的格不发布逐格可重识别细目。正文不引用先前不可用的“缺失quality”作为已完成对照。

### 13.3 最终研究报告必须直接回答

1. P0：有无固定PCA8带来的预测代价？它是否依赖representation或lambda？如果两者都弱，是否清楚地保留不可排除范围？
2. N2R：新匹配袋是否真正完成了实验？方差增益是否超过二次均值、完整H和pre解释？不是只报告总bag准确率。
3. R3：三目标是否真的用了相同输入、曝光与编码器？MATCH是否超过SIM、SUP、L0/RAND？改善是否可能主要来自pre/历史？
4. 哪个**新观察**值得下一轮独立验证；哪个具体实现停止；哪些仍只是支持/实现限制？不能把“代码总测试通过”写成论文故事。

## 14. 状态、有限恢复与收束规则

每包分别给出：

- `execution_status`：NOT_RUN / COMPLETE / NUMERICAL_FAIL / BUDGET_LIMITED。
- `support_status`：SUFFICIENT / LIMITED / MISSING_INPUT。
- `capability_status`：PASS_FOR_DEFINED_TESTS / FAIL / NOT_EVALUABLE。
- `research_status`：PROMISING_EXPLORATORY / NO_CONTROLLED_GAIN_ESTABLISHED / UNRESOLVED_ALTERNATIVE_EXPLANATION / NOT_EVALUABLE。

代码失败可以在同目标同数据下有限修复；任何改变lambda集合、主时窗、配对定义、支持格、归一化或损失都属于新版本，不能混合成旧主比较。一次硬件中断恢复不视为新研究设计，但须保存原失败回执和增加的资源。

主要对比所需成员不完整时不从成功身份/折挑子集。**不同包或独立次要敏感性允许分别完成**，不因一个次要模型失败而抹去完整主矩阵。旧E0“所有64个头必须通过”的全族门槛不复制到这里。

本轮结束条件是三包获得完整结果或明确合法停止回执，附资源/隐私核验。不得自动将结果写入论文摘要、宣称首次发现、启动临床回归、增加seed或创建新的自动任务。

## 15. 本设计的限制必须保留

- 仍然是已多次探索的私有HA/BDF子集，不代表CI、正常听力或所有儿童。
- 匹配控制的是已定义的历史格，不能消除所有刺激声学、设备锁定伪迹、配合状态或物理延迟的不确定性。
- 完整信息、PCA预测信息、同trial对比目标和临床功能是不同对象；风险差不直接等于MI/CMI。[R8]
- N2R的低维方差是一个有限分布摘要；阴性不排除完整协方差/其他分布信息。其400维敏感性也不穷尽所有模型。
- R3的MATCH使用标签和CE＋对比联合目标，且改变了正负样本关系；不能把相对SimCLR改善写成纯无监督优势。标签预算三目标相同但利用方式不同。
- 小样本内holdout和有限训练种子仍限制R3的稳定性判断；本轮不通过大量重复训练制造虚假独立样本。
- 所有原始模型结果与失败回执保留。禁止把“统计效率更高的新设计”写成旧设计已经成功。

## 16. 直接交给服务器代理的启动指令

> 在现有auditory工作区执行本v3计划。先读取本文件、配套YAML、eb24106的v2.1科学报告及最新AGENTS/GPU规则。不要重开旧N1/N3、A2、C2、B/D或E0/E1矩阵。
>
> 第一步只实现和核验来源接入、P_MATCH成员及split：读取v2.1已经生成的matched_bags，不重新装袋、不改变历史格与k=8。沿用旧外层身份分组，N2R改用内3折；R3改用一个20%内验证再全外层重训，不再使用五角色。核实所有fit实际身份，不允许旧encoder已看过的validation被称为未见。
>
> 然后实现三个NEW工作包：P0固定lambda全特征/PCA8诊断；N2R均值、二次均值与方差对比；R3同一个小CNN上的SUP/SIM/MATCH三个目标。P0与N2R不训练新encoder。R3最多30个正式encoder，seed11，固定60epoch；必要合成smoke另计。
>
> 每包只在对应测试/能力及数据支持通过后启动真实比较。P0/N2R阴性不作为禁止R3的理由；能力失败也不能当作真实科学阴性。不要建设新的MLP网格，不扫临床终点，不因个别候选不利而换样本。
>
> 全部数值和验证通过Slurm，禁止P100；最大4个CPU/2个GPU并发；新head fits≤3000，CPU申请≤160 core·h、GPU申请≤16 h。运行前写fit catalog和资源预约。原始数据、旧输出和旧失败目录只读，个体数据/预测/模型全部private，不自动push。
>
> 最终用中文交付三个包的主对比、必要对照、人数与作用域、能力范围、资源与失败说明，并明确哪个新观察值得下一轮继续。缺少关键输入时停止受影响包并写具体缺项，继续其余独立包，不提出已经在文档中有默认值的问题。

## 17. 参考来源与方法边界

这些来源用于核实旧状态、接口和现有方法基础，不替代本轮的实验结果。仓库链接固定到eb24106；本文公式和新比较设计是本轮提出的操作定义，不声称已有发表验证。

- [R1] 仓库 v2.1 科学结果：<https://github.com/W-Yinghao/auditory/blob/eb24106afe170b323859daa9dda597a85e548bb9/docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md>。
- [R2] 仓库执行与隐私规则：<https://github.com/W-Yinghao/auditory/blob/eb24106afe170b323859daa9dda597a85e548bb9/AGENTS.md>；GPU规则同提交的`docs/GPU_SCHEDULING_POLICY.md`。
- [R3] 新匹配袋定义：<https://github.com/W-Yinghao/auditory/blob/eb24106afe170b323859daa9dda597a85e548bb9/docs/auditory_v21/N2_DESIGN_LOCK.md>。
- [R4] 袋实现与私有输出字段：<https://github.com/W-Yinghao/auditory/blob/eb24106afe170b323859daa9dda597a85e548bb9/auditory_v21/n2_design.py>。
- [R5] 旧表征与读出入口：同提交的`auditory5/execution.py`、`auditory5/probes.py`、`auditory5/models/small_cnn.py`；实际复用前以运行快照核验，不假定当前文件等于每个历史执行版本。
- [R6] Chen et al., *A Simple Framework for Contrastive Learning of Visual Representations*, ICML 2020：<https://proceedings.mlr.press/v119/chen20j.html>。仅作为SimCLR目标/投影头基础；原文不是儿童EEG有效性证据。
- [R7] Khosla et al., *Supervised Contrastive Learning*, NeurIPS 2020：<https://proceedings.neurips.cc/paper/2020/hash/d89a66c7c80a29b1bdbab0f2a1a94af8-Abstract.html>。MATCH是本轮限制配对范围的实验设计，不宣称SupCon新颖性。
- [R8] Xu et al., *A Theory of Usable Information under Computational Constraints*, ICLR 2020：<https://arxiv.org/abs/2002.10689>。用于区分真实统计信息与具体读出族的可用信息；有限风险差不是自动一致的MI/CMI估计。
- [R9] scikit-learn官方文档，Data leakage / Common pitfalls：<https://scikit-learn.org/stable/common_pitfalls.html>。训练/测试隔离原则；本轮还对encoder、配对与投影实施相同作用域约束。

---

**文件完成不等于服务器运行完成。** 执行后应由服务器新增不可变研究报告，不修改本方案来适配已看结果。
