# Auditory NEXTMAP v1.0：服务器执行与交付指令
## 年龄信息来源 · MFF 语义／身份恢复 · SIR 预测余量

**日期：2026-09-27**  
**基准提交：`b9c0d9fdbe1da394c6d3b4ca4372e6dd3d96ba9d`**  
**主体提交：`ab9c340807aff8f1be7e2a173a61d565a8345101`**  
**研究依据：`AUDITORY_RESEARCH_REFRESH_v1_20260927_b9c0d9f.md`**  
**新工作包标识：`auditory_nextmap`。此命名仅用于与旧 PF、DV 等产物隔离。**

> 本文件是新执行规格，不代表所列新模块、CLI、配置或任务已存在。先实现和测试，再提交规定范围的服务器任务。GitHub 只提供了部分代码和汇总；私有数组、身份关联、模型权重及源资料必须在服务器验证。
>
> **本轮默认：0 个新 EEG 编码器训练；已有权重的有限推理；小型年龄读出；定向资料恢复；既有 SIR 概率重评分。**
> 新恢复的任务先输出任务卡，不自动启动四声分类、跨系统池化、大规模预训练或新的临床 EEG 模型。

---

## 0. 授权、禁区和独立推进

### 0.1 允许现在执行

| 包 | 允许内容 | 不依赖什么 |
|---|---|---|
| P0 | 核对本轮必要来源、版本、形状、身份和训练范围；生成确定任务表 | 不等待医生，不重新审计全部数据 |
| A0 | 在 PF2 已有同编码器嵌入上，分析共同／差异年龄信息、谱与技术参照 | 不要求 B 恢复出新任务或新儿童 |
| B0 | U1 任务语义、U3 非规范身份／年龄、U2 SET来源、U4 BDF时钟关系 | 不要求 A0 得到阳性 |
| C0 | 既有 SIR 概率预测重评分；必要时有限临床头重拟合 | 不要求新 EEG 预测器成功 |
| A1 | 既有编码器的非对齐片段推理、同架构随机网络推理、固定时空特征对照 | 只要求对应输入和模型范围合法；不以 A0 p 值决定是否做 |
| B1 | 恢复后的任务支持图、曝光清单与下一次训练任务卡 | 不自动训练 |
| Final | 对全部已规定比较汇总、解释、写路线决定 | 不把技术完成等同科学阳性 |

### 0.2 明确禁止

不联系医院；不要求新病例；不从外网下载新 EEG；不按年龄模型输出填年龄；不按解码成绩决定身份、刺激名或时间偏移；不将 NH 时长填0并并入 HA；不重训 PF/PF2/DV 已完成的整套网络；不继续优化晚权重阶段分类；不改旧结果或覆盖失败产物；不自动 push 数据或报告。

全部服务器数值计算、数据扫描、环境探针和测试通过 Slurm。数据根目录 `/projects/EEG-foundation-model/auditory` 只读。禁止 P100；GPU 如确有必要，遵守现有 A100/L40S/H100/V100/RTX6000PRO 调度规则与默认 QoS。[R11]

### 0.3 执行优先级

身份隔离、数据安全和只读规则不可放宽。本文件仅替换“下一轮做什么”的旧计划，不撤销旧结果、不授权发布。

如果工作树已比基准更新，不执行 `git reset`、不覆盖新代码。只比较本轮依赖的源文件及产物；记录差异。无关更新不阻断；输入、身份、时间轴或编码器语义变化时，为受影响包写 `SOURCE_VERSION_DIVERGENCE`，采用明确的新适配版本，不混用后静默运行。

---

## 1. 首次阅读范围：只读与本轮有关的文件

按顺序读：

1. 当前 `AGENTS.md`、GPU调度及发布约束；其中历史结果解释与新版不一致时，不沿用“普遍无信息”措辞。
2. `configs/auditory_pf_v2.yaml`、`configs/auditory_dv_v1.yaml`、`configs/auditory_gx_v1.yaml`。
3. PF2结果、DV结果、PF嵌入修正附录。
4. `auditory_pf/cohort.py`、`stim.py`、`features.py`、`stats.py` 和 `auditory_dv/analyze.py`、`audit.py`。
5. 为 B 包读取已有来源图、SET关联和时钟回执；只有缺口相关的原始字段才继续读取。

不要把“读完全部历史方案”设为开始条件；不要重复执行已完成环境兼容探针。

### 1.1 已核对的配置绑定

这些是基准仓库实际配置，不是本轮虚构的入口。[R9]

| 绑定 | 值 |
|---|---|
| PF2配置 | `configs/auditory_pf_v2.yaml` |
| DV配置 | `configs/auditory_dv_v1.yaml` |
| GX配置 | `configs/auditory_gx_v1.yaml` |
| PF2准备运行 | `prepare_002`，位于 `private/auditory_pf/` 下 |
| PF2刺激模型运行 | `stim_002`，位于 `private/auditory_pf/` 下 |
| 连续谱缓存 | `private/auditory_pf/features_001/features.npz` |
| GX事件暂存 | `private/auditory_gx/GX_stage_001/epochs/` |
| BDF D1运行 | `D1_bdf_001` |
| MFF D1运行 | `D1_mff_001` |
| ST记录表 | `private/auditory_st/ST1_scope_001/records.csv` |
| HA临床来源 | `private/auditory_repair/ha_prepare_001/cohort.csv` |
| 修正PTA | `private/auditory_repair/pta_007/candidate_covariates.csv` |
| NH补充来源 | `private/auditory_gx/clinical_override.csv` |
| MFF registry/history | `private/mff_001/registry.json`、`private/mff_001/history.json` |
| 规范标签配置值 | `results/phase3_ci_linkage_005/canonical_source_labels.csv` |
| 临床原始路径定位 | `private/inventory_001/file_path_map.csv` |
| CI列原始信息 | `private/phase3_ci_clinical_004/candidate_rows_index.csv`、`schema_private.json` |
| PF2外层种子 | `404,505,606,707,808`；每种子5外折 |
| 已有每类预算／重复数 | 80／10 |
| GX主epoch | 250 Hz，触发前0.2s、后0.6s，即原定义下0.8s |

某些带逐人内容的历史 `results/` 文件没有公开到 GitHub，但服务器原路径可能仍存在。公开缺失不等于服务器不存在；只在本地限定路径/现有索引中解决，不全盘按姓名搜索。

### 1.2 已有 API 与新 API 的区别

可参考已有 `Cohort`、`gpu.infer`、`gpu.load_lane_checked`、D2 `RecordStore`／`record_feature_matrix` 和 `OrdinalLogistic.proba`。先核对实际签名、数组顺序和预处理，不直接假定新包能无改动调用。

下文的 `auditory_nextmap.cli`、`age-core`、`recover`、`headroom` 等均为**待实现接口**。不要把它们写成仓库已有功能，也不要在空模块上提交批量作业。

---

## 2. 新目录与状态管理

建议新建以下结构，不修改旧包的数据和快照：

```text
auditory_nextmap/
  adapters.py        # 已有 Cohort、权重、谱、临床概率和来源图的适配
  manifest.py        # 输入/身份/训练曝光范围
  representations.py # 配对缩放、共同/差异、固定时空与非对齐输入
  age_readout.py     # 明确 SSE/L2 目标的有限读出
  recovery.py        # 语义、身份、年龄、SET、时钟
  headroom.py        # 离散概率评分与边界
  reporting.py
  cli.py
configs/auditory_nextmap_v1.yaml       # 按本文规格实现
scripts/slurm/auditory_nextmap_cpu.sbatch
scripts/slurm/auditory_nextmap_gpu.sbatch
tests/test_auditory_nextmap_*.py
docs/auditory_nextmap/
private/auditory_nextmap/<run>/
results/auditory_nextmap/<run>/
```

这是建议结构；可以复用现有工具而减少文件，但不能让科学定义藏在多个旧版本的默认参数中。

### 2.1 每次运行必须保存

`input_manifest.json`、`resolved_config.yaml`、代码提交/差异标记、源模型权重hash、身份与折hash、选样规则、运行命令、Slurm job id、包版本、开始/结束状态、异常原因与所消耗的拟合/推理单元。

涉及身份和原始路径的版本放私有目录。`DONE.json` 只表示该限定计算完成，不自动写“科学成立”。

### 2.2 不覆盖与不重复

每个计算单元键为 `(package,analysis,source_hash,seed,fold,view,budget,model_spec)`。启动前检查已有 receipt 及活动作业；同键成功产物复用。同键失败保留，修订后增加 attempt/version，不覆盖。

报告修订只读已保存预测。不能为了修表格、补摘要或改状态词而重复拟合。

---

## 3. P0：建立一个有限、可读的本轮来源表

### 3.1 产物

私有 `records_manifest.csv` 至少包含：

```text
identity_group, record_id, primary_record, source_system, source_group_status,
source_container_id, physical_acquisition_id, visit_id, age_months,
age_source_status, n_std, n_dev, has_draws, fold_assignment_ref,
encoder_scope_ref, epoch_source_ref, spectral_source_ref, source_conflict
```

不得把实际姓名、DOB或完整路径写到公共表。相同身份的所有访问必须共享外层 fold。

### 3.2 A 包主队列

- **主队列：**PF2 `group=labelled`、primary record 有效年龄、两类80个预算及已有同编码器导出；按既有资料预计55名HA，但以核对结果为准。
- NH仅作既有64人结果的描述参照，不在本轮自动增加一套新组间比较。
- 年龄未知不推断；量表日期未知不阻断年龄分析。
- 源谱不足时，谱比较采用共同支持子集，并在该子集重算对应事件模型；不静默让主C/CD改变人群。
- 如果主队列与预计不同，先报告逐项原因，不通过删/加记录凑55。

### 3.3 编码器范围硬检查

对于每个 `(seed,outer_fold)`：

1. A 包训练和测试记录必须使用同一个 `M_o` 的嵌入。
2. 该外折测试儿童的任何访问都不在 M_o 的训练或早停验证中。
3. `agg_source` 应为 `single_encoder_M_o`，或由等价推理来源和hash证明。
4. 不复用旧 `M_i` 混合坐标的 `agg_base`；旧 PF `exports_mo.npz` 与 PF2 `exports.npz` 不互相冒充。
5. 不先把每名儿童“自己的OOF向量”拼成表，再进行新的外层年龄划分。这会混坐标，也可能让第二层测试儿童参与别人的上游模型。

任何一项无法核清，只阻断相关嵌入比较；B恢复和C临床概率分析继续。

---

## 4. A0：已有嵌入的年龄信息分解

### 4.1 读取规则

PF2 单元默认路径：

```text
private/auditory_pf/stim_002/unit_s<seed>_k<fold>/exports.npz
private/auditory_pf/stim_002/unit_s<seed>_k<fold>/models/M_o.pt
```

从实际键读取 `agg_base`、`test_children`、`train_children`、`agg_source`。基准形状为 `[n_record,10,2,192]`。如果形状不符，报告语义差异，不 reshape 猜维度。

类别0/1语义以源 `Cohort` 和事件映射为准；沿用操作标签，不补充800/1200Hz物理含义。

### 4.2 预算层

| budget_id | 取法 | 报告要求 |
|---|---|---|
| `single_draw80`（主） | 每源seed使用 `draw=0`，每类80个 | 报160个试次及实际时段，不称五分钟 |
| `draw_ensemble10`（敏感性） | 对10个draw的每类嵌入取均值 | 报实际唯一试次数；不称仅80个/类 |

主层运行全部规定视图；敏感性层只运行 C 和 CD，避免再次铺开全矩阵。原DV数值主要对应原先重复抽样聚合及不同读出规则，本版不要求新主层恢复24.4个月等旧值。

### 4.3 成对标准化与旋转

在每次实际拟合的训练儿童上，对于维度j，汇总每名儿童两类均值，儿童与类别等权，得到共同 `m_j,s_j`：

\[
\tilde\mu_{is,j}=(\mu_{is,j}-m_j)/s_j.
\]

两类必须使用同一对 `m_j,s_j`。`s_j<1e-8` 的维度按冻结规则置尺度1并报告数量；不可非有限填零后隐瞒源问题。

再计算：

\[
c=(\tilde\mu_0+\tilde\mu_1)/\sqrt2,
\quad d=(\tilde\mu_1-\tilde\mu_0)/\sqrt2.
\]

STD、DEV也使用这套共同尺度。C/D/CD/PAIR **不再分别 StandardScaler**。截距始终不惩罚；可以解析中心化处理，但必须保持等价目标。

在内层选参中，这套尺度必须在该内层训练子集重估；外层最终拟合时才在全部外层训练HA上估计。

### 4.4 主读出：限定的岭回归族

为避免新的 SSE/MSE 错位，统一写成：

\[
\min_{b,w}\sum_{i\in train}(A_i-b-x_i^Tw)^2+\alpha\|w\|_2^2.
\]

使用双精度线性求解，不求逆矩阵；截距不罚。若用平均损失接口，必须传入 `alpha/n_train`，其中 n 是当前实际拟合人数。

**本版新增有限网格：**`alpha=[1,100,10000]`，是源网格的固定子集；不要看到误差后扩网格。内层3折、按儿童、固定seed（由source seed和outer fold导出）；以平均验证 MAE 选alpha，精确并列时选更大的alpha。外层测试完全不参与选参。

外层 M_o 是冻结的既有表示。内层只重新拟合缩放和年龄探针，不训练 M_o；报告“冻结表示的内层探针选参”，不写成重新训练编码器的全嵌套验证。外层测试仍用于评价这个明确的算法。

若某个视图训练数据有限／求解条件不良，保存线性残差、rank、参数范数；不得以某个alpha测试表现更好为理由直接使用它。三档都数值失败时该单元失败，不输出均值预测冒充模型完成。

### 4.5 核心视图和基线

| view_id | 内容 | 是否选alpha |
|---|---|---|
| `std` | 共同缩放后的 \(\mu_0\) | 是 |
| `dev` | 共同缩放后的 \(\mu_1\) | 是 |
| `common` | c | 是 |
| `contrast` | d | 是 |
| `joint` | [c,d] | 是 |
| `pair_equivalence` | [\(\mu_0,\mu_1\)] | 只使用joint选定alpha验证预测等价，不另选 |
| `spectral_ridge` | 源cont `[20,9]`展平，训练内缩放 | 是 |
| `spectral_rbf` | 同cont，单一RBF核规则 | 是，使用下面的对应目标 |
| `technical` | 源已有质量/规模摘要，不含年龄、时长或量表 | 是 |
| `median_train` | 当前外层训练年龄中位数 | 否 |
| `mean_train` | 当前外层训练年龄均值 | 否 |

技术输入固定为可用的 `record_scale,accept_fraction,qc_over_mean,log1p(n_acc),log1p(d1_seconds)`；每个缺失指标在训练内处理并加缺失标志。若字段本身无来源，不以其他临床列替代。该基线用于解释，不能声称排除了所有技术混杂。

RBF核：采用独立的固定三档 `kernel_alpha=[0.01,1,100]`。核的尺度与线性设计矩阵不同，不为追求数值相同而照抄线性alpha；这不是看到结果后新增网格。仅在当前训练子集缩放后，令 `gamma=1/median(nonzero_squared_pairwise_distance)`；无正距离时回退预定gamma=1并记录。核为 `exp(-gamma*distance²)`；按训练均值中心化核和目标，验证／测试用相同训练核中心化；解 `(K_centered + alpha I)a = y_centered` 并加训练均值。kernel_alpha按上述三档选择，内层重算scale、gamma、kernel中心。不得从测试距离选择gamma。

这是一个受限的非线性谱参照，不是保证谱模型已充分优化。事件与谱的最终比较仍是算法风险比较，不是原始信号信息量排序。

### 4.6 主终点和汇总

对每名儿童先在源5个seed上平均绝对误差：

\[
e_i^{(m)}=\frac1{5}\sum_s|A_i-\hat A_{i,s}^{(m)}|.
\]

主估计：

\[
G_{D|C}=\frac1N\sum_i(e_i^{common}-e_i^{joint}).
\]

同时报告每seed MAE、儿童误差分布、MSE及每fold支持。不要把“平均5份预测后再算误差”与“平均5份误差”混报；前者可另存为集成敏感性，不替代主结果。

95%区间采用相同儿童重采样索引的配对bootstrap（2000次，固定seed）。这是**条件于已有训练／预测的描述性区间**，不覆盖全部重新训练不确定性。fold和seed不作为独立样本量。不增加新的置换显著性筛选或功效阈值。

预定次要风险差：`std-dev`、`median-contrast`、`spectral_ridge-joint`、`spectral_rbf-joint`，方向明确标注。全表保留负值；无论主结果大小都完成这些比较。

### 4.7 年龄范围及来源控制

按主队列的年龄分布报告总体误差及训练范围外的测试个体计数；不按成绩删尾部儿童。

可以在训练侧定义的年龄三分位报告描述误差，但不得从中挑最阳性的年龄窗。HA与MFF的绝对MAE不能直接相减来证明系统或电极效果。本轮不自动重跑完整MFF年龄矩阵。

---

## 5. A1：最小的信息来源对照，不训练新编码器

### 5.1 三个比较和一个匹配参照

| view_id | 定义 | 比较对象 |
|---|---|---|
| `trained_common_matched` | A-C在对应可用子集上重评分／重拟合 | 所有对照的共同参照 |
| `random_common` | 相同架构、固定未训练权重的逐试次嵌入，再按两类等预算取共同表示 | 刺激训练是否增加年龄可读性 |
| `raw_common` | 同一0.8s epoch做20ms非重叠均值，每通道40个bin；两类共同聚合 | 固定原始时空特征能否解释优势 |
| `nonaligned_common` | 同记录、同物理时间块、同数量和长度的非事件对齐片段，经该fold M_o提取后聚合 | 对齐组织是否重要 |

所有读出均用 A0 同一岭回归规则。不同维数仍可能影响估计难度，报告维数、有效rank和alpha；不以性能差直接宣布某类生理信息存在／不存在。

### 5.2 随机网络

每个 `(source_seed,outer_fold)` 一个随机网络，架构与 M_o 一致；初始化种子由固定主seed和单元键生成。`eval()`，无BatchNorm适配、无dropout、无训练，也不按年龄性能选seed。

随机网络只说明未经刺激训练的该架构保留了什么。不得把“随机网络差”直接解释为刺激训练学到纯听觉发育信息。

### 5.3 原始分箱

沿用对应GX输入的数值单位、参考、基线校正、归一化及接受掩码。适配器须从原暂存代码核对基线扣除、通道顺序和record_scale的实际用法；不能直接把D1片段当作已满足GX输入定义。先用少量既有事件重建输入，并与原暂存张量及冻结网络预测作数值一致性检查，未通过只阻断A1的新增片段推理。默认250Hz、200samples，5samples一个20ms bin。形状若与源epoch不同，记录并用配置确定，不硬截到200。

按与A0相同的draw0、类别和记录聚合。不要把基线换成更短、更少通道或不同QC的信号后宣称神经表示更好。

### 5.4 非对齐片段的合法构造

这是本轮新诊断，不是无声对照。实现顺序：

1. 以A0两类draw0事件所在的60秒物理时间块及其计数，确定抽样配额。
2. 在该记录对应D1真实存储区间内生成候选0.8秒片段；不跨断点，不拼接不相邻存储区间。区间边缘沿用源2秒guard。
3. 候选锚点不能落在已知声音触发±80ms内；未明确是否声音的事件不据此补标签。该排除仅避免精确对齐，不声称窗口内没有其他响应。
4. 按固定种子从每块合格候选中抽取规定数量，不看年龄、阶段、AUC或波形峰值。在源定义的单位/处理阶段应用与真实epoch同一QC规则，再使用相同基线校正和record_scale；不能对已归一化数据直接套微伏阈值。
5. 每记录总数与两类draw0合计相同。非对齐片段不附加原标准／偏差标签；全部聚合后乘 \(\sqrt2\)，使其与共同表示的线性尺度可比。
6. 保存每个窗口的原始存储区间、起止sample、与最近触发距离、QC及实际覆盖时间，全部私有。

不能用现有epoch首尾循环移位冒充真实非对齐连续片段，也不能用独立增益归一化悄悄消除某一组的幅值。

若部分记录无法满足同块预算，不从其他时段或记录补样。该比较采用完整支持子集，两侧重新拟合；报告与主队列的差异。A0主分析不受影响。

### 5.5 如何读结果

- trained common优于nonaligned：事件对齐可能提高当前读出的有效性；仍需注意输入分布变化。
- random common接近trained common：当前架构/输入已经保留年龄结构，不支持训练特异优势。
- contrast有增量而common稳定：值得后续检验相对条件信息；不能单凭增量判定新神经发生源。
- 所有表征只与技术摘要相当：保留为该处理流程的结果，不再设计年龄网络大搜索。

A1不得因为A0区间跨零被取消；它正是用来区分不同解释的。

---

## 6. B0-U1：恢复 MFF 任务与刺激语义

### 6.1 遍历范围与优先来源

先加载既有203条规范来源及132条未知任务清单、1,160容器的registry/history、类别/segment/event ledger。优先读取：

1. `categories.xml`、Events结构、历史分段/平均参数与明确的音频／stimulus字段；
2. 有证据的原始记录—分段—平均来源链；
3. 现有工作簿、说明文档、JSON导出和已解析的文字线索；
4. 只对仍能解决具体映射缺口的截图做定向查看。

不得把所有515个平均文件导出成新trial；不得重新扫描所有EEG波形寻找“像声调”的模式。

### 6.2 私有语义表 schema

```text
record_id, acquisition_id, task_family, presentation_role,
stimulus_id, token_id, physical_frequency_hz, lexical_tone_label,
block_id, context_id, role_reversal_supported, source_system,
claim_field, claim_value, evidence_grade, evidence_file_id,
evidence_locator, lineage_edge_ids, scope_definition, conflict_status,
review_status, raw_literal
```

`task_family`建议枚举：`puretone,bapa,ba1ba4,lexical_tone_other,other,unknown`。不能因为想要统一声调车道就把所有ba类标签写成同一种任务。

`presentation_role`：`standard,deviant,high_deviant,low_deviant,other,unknown`。保留原始字面值，不以频率高低或出现比例自动填角色。

### 6.3 证据规则

DIRECT、LINKED、SCOPED、CANDIDATE、UNKNOWN、CONFLICT采用研究文档定义。

- 同名文件不自动同源；同一父目录不自动同一任务。
- 来源图的原始候选边可复用，但必须核对承载标签传播的边。
- 角色、任务、token各字段独立升级，不允许因一个字段确定而整行变成“已确证”。
- 两个强来源冲突时保留双方与CONFLICT，不多数投票消除。
- 文献、幻灯片预期人数、SOA和模型成绩不能填成证据。
- 未找到音频或刺激字典时，具体物理刺激身份可为空；任务家族已知不必退回整条记录未知。

### 6.4 输出任务—刺激—上下文支持图

私有统计每个刺激在哪些block、visit、identity、role出现；公共只发布不暴露个体的聚合结构。

必须识别：

- 同一声音是否跨上下文出现；
- 某个标签是否与记录／block完全同一；
- 两个tone对是否相互断开；
- 是否有标准／偏差角色互换的证据；
- 每个候选比较是否在同一记录内有两类、多少独立儿童有对应条件。

支持不足时输出“可以研究的较窄任务”而非强行四分类；没有可验证任务也如实结束本包。恢复人数没有预定成功阈值。

---

## 7. B0-U3：非规范来源的身份与年龄恢复

### 7.1 不沿用 `new_subject` 字段作为真值

已有audit_c的55个非规范分量是候选集合。逐个拆成可读采集、重复加工和未知结构；42个未匹配分量仅表示未与规范subject-fields哈希相交。[R5]

空subject_fields、字段拼写变化、通用文件名不得自动产生新儿童。不同分量之间仍需去重；“未知是谁”不能作为“确定是新的人”。

### 7.2 身份关系表

```text
entity_a, entity_b, relation_type,
evidence_type, evidence_file_id, evidence_locator,
match_status, confidence_basis, conflict_fields, reviewed
```

`relation_type`分别为：`same_container_version,same_acquisition,same_visit,same_identity,possible_identity_overlap`。不能把处理版本链接直接变成儿童链接，或把所有同日同名自动压成一个采集。

不要用 EEG 相似度来给主分析指定身份。存在可能同人的记录在跨折划分时应保守共组，或者只限制其进入需独立身份的分析；不能在不同折中当作“应该不是同一人”。

### 7.3 年龄恢复

优先可信原始DOB与recording time；其次是与该次记录有直接对应的年龄列。采用原始文件的日期定义，不用mtime或处理日期。

日期只有部分精度时保存年龄区间及精度。存在歧义且无法解开时不自动取中点；该记录仍可用于不依赖精确年龄的任务。不得利用预期年龄范围修正DOB或用年龄网络生成标签。

### 7.4 模型曝光清单

```text
identity_group, acquisition_id,
model_or_run, role_in_run, exposure_status, evidence_ref
```

区分`not_found_in_checked_runs,pretraining_used,supervised_train_used,
validation_or_selection_used,test_or_exploration_viewed,unknown`。

`not_found_in_checked_runs`不是“从未使用”的证明，报告核对的模型范围。只有能够证明相关上游未暴露且身份隔离，才可在以后称其为该模型的新测试资料。未知曝光不阻断资料整理，但阻断“独立验证”措辞。

### 7.5 必须交付的计数

容器数、来源分量数、去重物理采集、已有身份新访问、净新增高证据身份、有年龄的净新增身份、满足输入支持的净新增身份、曝光已知／未知数量。不得把这些数合并成一个扩样率。

---

## 8. B0-U2 与 U4：有限的来源补充

### 8.1 SET/FDT

从已审计的27组及23组原始候选关系开始；重新确认11个epoched与16个continuous分母。任务是查净新增身份及匹配处理版本，不是重新计算10,965个epoch的全部质量统计。

如果为同次采集：保存BDF/SET处理对照关系、参考、滤波、采样率、event/index对应和丢弃规则。处理桥接优先比较单位、时钟、接受掩码和少量固定特征，不自动训练NH分类器。

若发现真正新的NH，仍需明确临床组别证据、任务和与HA的采集差异。新NH全部来自SET而HA来自BDF时，不能直接合并下组结论。输出匹配比较任务卡即可。

### 8.2 BDF时钟

仅处理已记录的9条header不一致记录。先区分annotation onset是相对各自header、相对同一检查、还是已校正绝对时间。绝不能简单看见−1s就无条件再减1s。

来源允许的候选偏移来自已有timestamp/sample关系，不扫描连续时间找响应最大值。不通过NH常模峰反推声学延迟。

元数据不能唯一决定时，可输出允许候选；只有在单独预定的支持／查询验证中才能用信号选择候选。若需要这一额外步骤，先写明支持块选择规则、统计量、候选集合和查询验证，再执行；不新增无界搜索。

本轮默认只交付元数据确定的修正映射与未决清单，不重训GX或阶段网络。恢复的记录数不等于新增儿童数。

---

## 9. B1：根据恢复结果生成下一次训练任务卡

本轮不直接调用旧 `auditory_dv/pooled.py` 开始训练；跨系统通道边界仍不是已有授权。[R11]

每张任务卡应包含：

```text
task_id, research_question, target_semantics, input_unit,
allowed_evidence_grades, included_source_scopes,
identity_partition_rule, age_range_support, trial_budget,
within_record_comparison, stimulus_context_confounding,
preprocessing_and_reference, model_comparison,
exposure_limitations, feasible_now, unresolved_dependencies
```

可填写三种有限设计之一：

1. **具体二元声音对比：**任务／token有证据，不提升为抽象语言类别。
2. **多个已知协议内的联合学习：**target-only、naive pooling、shared encoder＋protocol-specific head，同测试儿童、同目标标签预算和优化预算。
3. **新增年龄样本的冻结评价：**首先评价已有冻结模型与同范围基线，后续重训另立版本，不以目标MAE决定纳入哪些年龄。

不设“恢复≥10条自动四分类”“补30名必须降低MAE”等规则。若区组与标签完全混淆、身份无法隔离或通道处理未定义，训练卡为`NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT`，但保留可用较窄问题。

---

## 10. C0：SIR 概率与预测余量

### 10.1 固定目标与条件

主目标完整SIR 1–5；已有SIR>3是附属参照。保留原记录级标签与HA临床匹配，不引入MUSS、CAP等多目标搜索。

条件C严格采用原PF临床模型实际使用的年龄/佩戴时长变换与训练规则；先读保存的设计矩阵说明与模型规格，不能从汇总文本猜样条节点。若原模型实际不止这两项，应逐列记录，不静默删改。

这里“档案目标”不要求问卷同日已确认，但不能写成同期临床效度。

### 10.2 优先读取，不优先重拟合

首先查找旧PF私有目录中与H14对应的：儿童/record映射、外层fold、训练范围、真值、五类概率、模型选择及训练成功回执。

若已经有完整五类概率，直接重评分，不重新训练。

若仅有latent、预测等级或AUC：不能从它们推造概率。允许两种合法办法：

- 从同一已保存OrdinalLogistic参数，通过其 `proba` 接口导出；
- 参数未保存但原设计可完整复现时，按同一来源与临床模型规则做一次有限临床-only重拟合，命名为新run，说明不是旧预测的原始重评分。

原规格无法确定时，C0输出`PROBABILITY_SOURCE_UNRESOLVED`；不擅自创造一个更好临床模型来承接旧0.982。A/B继续。

### 10.3 概率检查和评分

每条OOF记录的概率向量应有限、非负、和为1，标签在1–5。固定数值保护：`p <- max(p,1e-6)`后逐行归一化；保留保护前最小概率及受影响比例，所有模型同规则。

计算：

\[
CE_i=-\log_2 q_i(Y_i),\quad
Brier_i=\sum_{k=1}^5(q_i(k)-1\{Y_i=k\})^2.
\]

同时保留原协议MAE，以及由 `sum_{k=4}^5 q(k)` 得到的二元概率评分。不要把latent score的AUC与概率CE混成同一个校准结果。

参照为每个外层训练集的有平滑经验类频率（每类加0.5），也报告均匀五类参照。训练类频率不使用测试儿童。

校准只作描述：五类分布、SIR>3预测概率与实际比例、错误主要来自哪些等级。默认不新增温度选择或重校准。如果模型数值无效，写数值缺口，不用事后clip掩盖失败。

### 10.4 解释报告的必要内容

写明总体恒等式：

\[
I(Y;X|C)\le H(Y|C)\le CE(q_C).
\]

并紧接说明：

- 经验OOF CE不是已知总体CE，固定预测bootstrap不是真实CMI上界的覆盖保证；
- CE低可以限制剩余预测空间，CE高却不证明EEG一定有信息；
- 高AUC不推出低条件熵；
- 这一结论针对固定SIR档案分布及C，不推广到所有言语功能；
- 不把输入C的强预测叫“病历决定言语能力”。

可以给一张“剩余CE × 已观察EEG增量”的解释表，但不得标成个体临床证书。

---

## 11. 必须通过的有限测试

这些测试针对已发生过或本轮直接相关的错误，不新建大规模模拟项目。

| 测试 | 精确要求 |
|---|---|
| T1 编码器坐标 | 同一外折每个候选的向量来源相同；故意混入其他fold向量必须拒绝 |
| T2 上游身份范围 | 测试身份及所有访问与训练/早停验证无交集；可能同人的分组规则不被忽略 |
| T3 旋转与岭等价 | PAIR与CD在同尺度/alpha下能量、预测、目标值一致，FP64相对误差≤1e-8 |
| T4 SSE/MSE | `SSE+alpha*norm²` 与 `MSE+(alpha/n)*norm²`预测一致；错误alpha直接用于MSE应被测试识别 |
| T5 抽样计数 | draw0确实每类80、不放回；10draw聚合报告唯一计数，不能伪称单80预算 |
| T6 时间轴 | 非对齐窗口不跨存储断点，单位和source sample一致；不得通过数组回绕生成 |
| T7 语义证据 | Standard/hdev或SOA单独不能生成声调/频率标签；冲突证据保留 |
| T8 身份计数 | 2个未知分量可对应1名新儿童；缺subject字段不能自动产生“已确认新儿童” |
| T9 概率 | 五类概率归一化、标签索引、CE与Brier手算一致；logit不能直接当概率 |
| T10 A3反例 | 两年龄读数共享时长项，但其差与时长无关；报告逻辑不得误写为两个读数都无关 |
| T11 协议混合反例 | XOR枚举得到无条件MI=0、给定Q后MI=1；仅验证逻辑可能性 |
| T12 输出完整性 | 缺折/缺模型/非有限不得对成功部分静默平均；敏感性子集成对一致 |

另外最多24个小型可恢复世界用于检验年龄表示流程：common-only、contrast-only、纯噪声各若干固定seed，包含独立训练/测试儿童。评价目的是实现是否能表达预设强信号和保留负值，不估计真实队列功效，不用它们证明模型足以检出所有弱效应。

首次测试通过后，修改影响定义的代码才重测对应项，不每次报告都重新跑全部环境探针。

---

## 12. 拟合日志、失败和统计输出

### 12.1 每个年龄头保存

训练/验证/测试identity列表引用；输入view与维数；scale来源；alpha及候选内层MAE；训练误差；线性求解残差、条件数诊断、参数范数；测试预测；constant-prediction标志；非有限计数。

这些日志全部私有。只保存最终测试MAE不足以解释比较。

### 12.2 每个有序头保存

目标函数值、optimizer成功状态、梯度/求解诊断、阈值顺序、所有等级概率、正则尺度、训练/测试支持。不能沿用忽略所有warning的旧默认而不记录。

### 12.3 状态词

```text
PLANNED
RUNNING
COMPLETED
COMPLETED_LOW_PRECISION
SOURCE_UNRESOLVED
SOURCE_VERSION_DIVERGENCE
IDENTITY_CONFLICT
MODEL_SCOPE_INVALID
NUMERICAL_FAILURE
PROBABILITY_SOURCE_UNRESOLVED
NOT_IDENTIFIABLE_WITH_CURRENT_SUPPORT
DEFERRED_NEW_TRAINING_SPEC_REQUIRED
```

数值完成与科学解释分栏。`p>0.2`、AUC<0.65、恢复人数少，都不能写成普遍“推翻”。来源/数值错误应解决或明确保留，不能转成科学阴性。

---

## 13. 资源边界与 Slurm

### 13.1 固定边界

| 资源 | 本轮上限与说明 |
|---|---|
| 新正式EEG编码器训练 | **0** |
| 既有训练权重推理 | 最多25个PF2 M_o分别提取规定非对齐输入；原嵌入优先缓存 |
| 随机网络推理 | 最多25个对应随机网络；不训练、不筛种子 |
| CPU年龄小型拟合/内层求解 | 预计数千以内；硬上限7500个；完整任务表先计算准确数量 |
| SIR临床有序优化 | 优先0；缺概率且规则可复现时硬上限600个优化调用 |
| 数学/合成案例 | 单元测试＋最多24个恢复世界，不跑数百世界的功效工程 |
| bootstrap | 每个规定配对比较2000次，共用相同儿童重采样索引 |
| 队列恢复 | 仅规定清单和明确来源链；不全量复制原始EEG |
| 并发 | 默认最多2个CPU作业＋1个GPU推理作业；站点规则更严格时服从站点 |

上述是资源上限，不是预测运行耗时。若任务规划已超上限，在提交前缩减非必需敏感性并生成显式新plan；不能跑到一半按结果好坏截断。

### 13.2 CPU模板（待创建）

以下路径/CLI是新规格。站点分区、环境激活脚本从现有可用Slurm脚本中读取，不猜账号、不请求高优先级QoS。

```bash
#!/usr/bin/env bash
#SBATCH --job-name=aud-nextmap
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=04:00:00
set -euo pipefail
umask 077
: "${SLURM_JOB_ID:?must_run_under_slurm}"
: "${AUDITORY_REPO_ROOT:?set_from_existing_workspace}"
: "${AUDITORY_ENV_SCRIPT:?set_to_verified_environment_script}"
source "$AUDITORY_ENV_SCRIPT"
cd "$AUDITORY_REPO_ROOT"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export MKL_NUM_THREADS="$OMP_NUM_THREADS"
python -m auditory_nextmap.cli "$@"
```

GPU推理模板沿用站点GPU资源申请方式，单GPU；在worker内检查设备名并明确拒绝P100。没有GPU不应阻断B/C或已有嵌入A0。原权重在CPU上可推理时可以选择CPU，但不能静默改变精度/批归一化行为。

### 13.3 CLI规格（全部待实现）

```text
python -m auditory_nextmap.cli source-check --config <cfg> --run p0_001
python -m auditory_nextmap.cli contract-tests --config <cfg> --run tests_001
python -m auditory_nextmap.cli plan --config <cfg> --run plan_001
python -m auditory_nextmap.cli age-core --config <cfg> --plan <frozen-plan> --run a0_001
python -m auditory_nextmap.cli age-controls --config <cfg> --plan <frozen-plan> --run a1_001
python -m auditory_nextmap.cli recover --unit U1 --config <cfg> --run b_u1_001
python -m auditory_nextmap.cli recover --unit U3 --config <cfg> --run b_u3_001
python -m auditory_nextmap.cli recover --unit U2 --config <cfg> --run b_u2_001
python -m auditory_nextmap.cli recover --unit U4 --config <cfg> --run b_u4_001
python -m auditory_nextmap.cli headroom --config <cfg> --run c0_001
python -m auditory_nextmap.cli unlock-plan --config <cfg> --run b1_001
python -m auditory_nextmap.cli report --config <cfg> --run final_001
```

`source-check`、测试及数值plan验证本身也通过Slurm。`plan`只生成确定矩阵，不读取测试表现。`report`不触发拟合。

依赖图：

```text
必要source-check → tests → frozen plan → A0 → A1（只依赖输入，不依赖A0阳性）
                  ├──────────────────→ B-U1/U3 → B-U2/U4 → B1
                  └──────────────────→ C0
所有已授权包的完成/明确未决回执 → Final
```

B-U2/U4也可在对应源检查后与U1/U3并行；图中顺序仅表示优先级，不要求等待恢复人数。

---

## 14. 配置规格（待实现，不是现有可运行配置）

```yaml
project:
  name: auditory_nextmap
  version: "1.0"
  base_commit: b9c0d9fdbe1da394c6d3b4ca4372e6dd3d96ba9d
  content_commit: ab9c340807aff8f1be7e2a173a61d565a8345101
  research_document: AUDITORY_RESEARCH_REFRESH_v1_20260927_b9c0d9f.md
  execution_document: AUDITORY_SERVER_EXECUTION_v1_20260927_b9c0d9f.md
permissions:
  contact_clinicians: false
  download_new_datasets: false
  modify_raw_data: false
  train_new_eeg_encoders: false
  run_pooled_dv_direction_f: false
  publish_or_push: false
sources:
  pf_config: configs/auditory_pf_v2.yaml
  dv_config: configs/auditory_dv_v1.yaml
  gx_config: configs/auditory_gx_v1.yaml
  pf_prepare_run: prepare_002
  pf_stim_run: stim_002
  pf_feature_file: private/auditory_pf/features_001/features.npz
  pta_file: private/auditory_repair/pta_007/candidate_covariates.csv
paths:
  private_root: private/auditory_nextmap
  aggregate_root: results/auditory_nextmap
  documentation_root: docs/auditory_nextmap
age:
  primary_group: labelled
  primary_visit: source_primary_rec
  outer_seeds: [404, 505, 606, 707, 808]
  outer_folds: 5
  new_outer_splits: false
  k_per_class: 80
  primary_draw: 0
  sensitivity_draw_average: 10
  pair_scale: train_pooled_equal_class_equal_child
  rotate_after_scale: true
  rescale_after_rotation: false
  alpha_sse: [1.0, 100.0, 10000.0]
  kernel_alpha: [0.01, 1.0, 100.0]
  inner_folds: 3
  inner_metric: mae
  tie_break: larger_alpha
  primary_views: [std, dev, common, contrast, joint]
  baselines: [spectral_ridge, spectral_rbf, technical, median_train, mean_train]
  sensitivity_views: [common, joint]
  primary_contrast: common_minus_joint_mae
  prediction_aggregation: mean_absolute_error_across_source_seeds_per_child
  new_significance_gate: false
  bootstrap_children: 2000
  bootstrap_seed: 27092701
controls:
  enabled: true
  refit_matching_reference: true
  random_networks: 25
  random_initialization_seed: 27092702
  raw_bin_seconds: 0.02
  nonaligned:
    physical_block_seconds: 60
    source_epoch_seconds: 0.8
    interval_guard_seconds: 2.0
    anchor_exclusion_seconds: 0.08
    match_block_counts: true
    infer_silence: false
    seed: 27092703
recovery:
  units: [U1, U3, U2, U4]
  start_from_existing_ledgers: true
  identity_from_eeg: false
  semantic_labels_from_performance: false
  expected_recovered_subjects: null
  expected_recovered_tone_records: null
  train_after_recovery: false
  preserve_unknown_and_conflict: true
  exposure_ledger_required: true
headroom:
  target: sir_ordinal_1_5
  secondary_target: sir_gt_3
  prefer_existing_probabilities: true
  allow_exact_clinical_only_refit: true
  allow_new_eeg_models: false
  probability_floor: 0.000001
  renormalize_after_floor: true
  prior_pseudocount: 0.5
  log_base: 2
  formal_cmi_confidence_claim: false
resources:
  slurm_required: true
  default_qos: true
  forbidden_gpu: [P100]
  cpu_jobs_max: 2
  gpu_jobs_max: 1
  new_encoder_fits_max: 0
  trained_encoder_inference_units_max: 25
  random_encoder_inference_units_max: 25
  small_age_fits_max: 7500
  ordinal_optimizer_calls_max: 600
  synthetic_worlds_max: 24
privacy:
  identifying_outputs_private: true
  exact_dates_private: true
  per_person_predictions_private: true
  source_paths_private: true
  auto_release: false
```

服务器可以增加适配器字段，但不能改变科学目标、数据预算或授权。新增默认值必须写入 `resolved_config.yaml`，不能依赖隐藏环境变量。

---

## 15. 私有与可审核汇总的交付清单

### 私有产物

| 文件 | 内容 |
|---|---|
| `records_manifest.csv` | 记录、身份、主访视、来源和资格 |
| `model_scope_manifest.json` | 各M_o训练/验证/测试身份及权重来源 |
| `age_predictions.parquet` | 每儿童、seed、fold、view、budget的年龄预测与误差 |
| `age_fit_ledger.jsonl` | 每个内/外拟合的规格和诊断 |
| `nonaligned_windows.parquet` | 真实片段的物理索引和QC |
| `semantic_claims.csv` | 任务/角色/token/context逐字段证据 |
| `identity_edges.csv`、`age_provenance.csv` | 身份、年龄来源和冲突 |
| `exposure_ledger.csv` | 既往模型暴露范围 |
| `set_source_bridge.csv`、`bdf_clock_candidates.csv` | 有限恢复结果 |
| `sir_probabilities.parquet` | 标签、五类概率、fold、模型范围及来源 |
| `job_ledger.jsonl` | 作业与单元完成状态 |

### 可供发布审核的汇总（不自动公开）

```text
SOURCE_STATUS.md
AGE_INFORMATION_SOURCE_REPORT.md
SEMANTIC_RECOVERY_REPORT.md
NET_COHORT_ADDITIONS.md
SIR_PREDICTIVE_HEADROOM_REPORT.md
NEXT_UNLOCK_OPTIONS.md
FINAL_RESEARCH_DECISIONS.md
summary.json
```

仅去掉姓名仍不保证隐私。不可公开逐儿童曲线、年龄/设备散点、能由相邻汇总作差恢复个体的数据。小单元格、唯一组合和极值也需复核。不得因本轮输入曾公开过某表，就继续扩大发布。

### 每份科学报告统一五栏

`数据对象 → 实际完成的比较 → 数值及精度 → 尚不能推出什么 → 哪个下一步问题因此值得/不值得做`。

恢复报告额外分列确定与候选数量。不要写“恢复成功所以四声可做”，要写具体刺激与上下文支持。

---

## 16. 验收与下一轮条件

### 必须满足的技术验收

同坐标、身份隔离、paired scaling/rotation等价、预算真实、概率有效、成对支持一致、缺失和失败没有被隐瞒。报告只引用可回到具体缓存/代码/行定义的数字。

### 不要求满足的科学验收

不要求任何风险差为正；不要求恢复人数达到阈值；不要求SIR余量很低；不要求MFF中出现四个声调；不要求最后形成独立成熟度或经验时钟。

### 下一轮训练的合理触发

由已有结果明确指出：需要验证哪一种条件信息、哪种共享关系、或者哪个新支持的目标。不使用“本次不显著，所以再加一个网络”作为触发。

本轮可输出三类后续建议，但均不自动执行：

- 在已验证年龄对象上，设计有限的新学习目标；
- 在恢复并锁定的同系统协议上，比较有/无协议条件化的共享学习；
- 在确实未暴露且身份独立的新增年龄资料上评价冻结模型。

若没有形成这样的对象，本轮以事实和限制收束，不给每种失败结果安排一篇备用论文。

---

## 17. 可直接交给服务器代理的启动说明

> 以 `b9c0d9fdbe1da394c6d3b4ca4372e6dd3d96ba9d` 为研究基准阅读本文件及配套研究版。不要重置当前工作树，不覆盖旧结果。
>
> 这次不是重跑PF/PF2/DV。请新建 `auditory_nextmap` 工作包，先核对本轮必要数据入口、模型训练范围和真实数组键；按 §11 完成有限测试并生成确定的任务表。所有计算/数据扫描/测试通过Slurm，原始目录只读、无P100、无新医生资料、无自动发布。
>
> 独立推进三项工作：A0/A1用已有同编码器嵌入及有限推理，区分共同／差异年龄信息与背景、随机网络和原始特征参照；B0恢复任务语义、净身份/年龄、SET来源与BDF时钟关系，保留未知和冲突；C0优先重评分既有SIR五类概率，缺失时只允许可完整复现的有限临床头重拟合。
>
> 主年龄预算用PF2每seed第一份80/类抽样；10份平均只做明确标注的敏感性。不要混不同网络坐标；不要把折、seed、draw当儿童；不要以测试成绩选窗口/标签/时钟。所有预定比较完整报告负值与不确定性。
>
> MFF恢复后只输出刺激—上下文支持表与下一次训练任务卡，不自动做四声分类或旧DV方向F。所谓42个“新被试”必须重新区分来源分量、采集、访问与身份；新增标签也要查既往模型曝光。
>
> 最终交付 §15 的报告与可追溯私有产物。某包遇到来源或数值问题时记录并处理该包，不让普通元数据未知阻断其余工作。不要为满足恢复人数、AUC或MAE目标改变规则，也不要把计算完成写成研究主张成立。

## 来源索引与核查范围

下列 `[S#]` 是用户材料；`[R#]` 是在基准提交中核对的仓库来源；`[N]` 表示本版新增设计或独立推导。原材料与仓库报告的解释不一致时，正文明确记录采用、修改或不采纳的部分，不将修订伪装成原作者结论。

仓库：`https://github.com/W-Yinghao/auditory`  
基准提交：`b9c0d9fdbe1da394c6d3b4ca4372e6dd3d96ba9d`  
主体内容提交：`ab9c340807aff8f1be7e2a173a61d565a8345101`

| 索引 | 文件／范围 | 用途 |
|---|---|---|
| S1 | 用户附件 `未用数据发散_标签复原与队列扩张.md`，§1–§3、§5 | U1–U7 原设想、标签恢复与扩样预期 |
| S2 | 用户附件 `新结果分析_PF_PF2_DV.md`，§1–§2、§4–§6 | PF/PF2/DV 的整理、原收束建议 |
| R1 | `docs/auditory_pf/PF2_RESULTS.md`；`results/auditory_pf/analyze2_001/summary_pf2.json` | 阶段关联稳定性、年龄增量、H2 未复现 |
| R2 | `docs/auditory_dv/DV_RESULTS.md`；`results/auditory_dv/analyze_001/summary_dv.json`；`results/auditory_dv/a1_sensitivity_001/` | 年龄结果、MFF 对照、其他 DV 比较 |
| R3 | `docs/auditory_pf/PF_PROTOCOL_ADDENDUM_001.md`；`auditory_pf/stim.py` | 跨网络嵌入错误及单编码器修正；PF2 的实际导出 |
| R4 | `auditory_dv/analyze.py` | 事件表示拼接、年龄读出、A3 的真实计算对象 |
| R5 | `auditory_dv/audit.py`；`results/auditory_dv/audit_c_001/summary_audit_c.json` | 55／47／42 的来源分量计数含义 |
| R6 | `docs/phase1_report.md`；`docs/source_document_review.md` | SET 构成、来源线索、BDF 时钟、工作簿任务命名 |
| R7 | `results/auditory_pf/analyze_004/PF_TABLES_final.md` | SIR 模型、个体判别、学习曲线等汇总 |
| R8 | `docs/PROJECT_OVERALL_SUMMARY_20260927.md` | 371 次成功 MFF 导出、规范来源与各轮使用范围 |
| R9 | `configs/auditory_pf_v2.yaml`；`configs/auditory_dv_v1.yaml`；`configs/auditory_gx_v1.yaml` | 数据入口、5 个外层划分种子、80×2 预算、10 次抽样、时间轴 |
| R10 | `auditory_pf/cohort.py`；`auditory_pf/features.py`；`auditory_pf/stats.py` | 主记录、身份分组、抽样、谱输入、岭回归及有序概率接口 |
| R11 | `AGENTS.md`；`docs/GPU_SCHEDULING_POLICY.md`；`docs/GITHUB_PUBLICATION_PF_DV.md` | Slurm、只读数据、禁止 P100、私有产物和发布范围 |

私有文件路径是仓库代码中引用的服务器入口，本轮文档作者没有取得这些私有文件，也没有重新计算真实 EEG。服务器须在现有工作目录内核对实际存在性、形状、来源与训练范围；不能仅因为路径写在文档里就认定产物已验证。

本版没有新增文献系统检索，也不作“首次提出”判断。正文公式为定义、条件推导或反例，不因列出公式而被称为新定理。正式投稿前仍需对拟保留方法的近邻文献单独核查。

### 输入文件校验

- `未用数据发散_标签复原与队列扩张.md`：SHA-256 `fcac3c499d897581c4aa85bbbb697ef4dc7645ec27148e8770d5f72ba7392e99`。
- `新结果分析_PF_PF2_DV.md`：SHA-256 `9fa353626e9cc91bfb0f00b5a35661b5c2d3df3e0d87f3d3c2edb694ce0e141c`。
