# STORY v1 实现说明

按材料包 `templates/IMPLEMENTATION_NOTES.md` 填写。冻结协议见 `PROTOCOL.md`（只读，SHA256 `d798f5e6…dcd2`），机器配置见 `configs/auditory_story_v1.yaml`。

## 1. 已有入口与新入口映射

| 对象 | 实际来源 | 新代码 |
|---|---|---|
| 主访问、外折 | `auditory_nextmap.adapters.AgeSource`（PF2 `prepare_002`，`Cohort.outer(seed)`） | `auditory_story.data.StorySource.main_table / split` |
| 临床字段 | PF2 `records.csv`（由 `ha_prepare_001/cohort.csv` 合并） | `clinical_cross_check` 直接重读原表复核 |
| 试次索引 | `Cohort.trial_idx_of_records`（55 个主记录的全部接受试次，48,747 个） | `StorySource.all_idx`，与缓存 `all_idx` 逐元素相等 |
| 试次历史、物理位置 | GX `GX_stage_001` 的 `trial_id` 连接 ST1 `ST1_scope_001/events/*.parquet`；D1 `D1_bdf_001` 区间 | `StorySource.trial_table` |
| 冻结编码器 | `private/auditory_pf/stim_002/unit_s{s}_k{k}/models/M_o.pt`（SHA256 记在 P0 `sources.json`） | 只读，不推理 |
| 全试次嵌入 | `private/auditory_nextmap/h_infer_001/items/ha_s{s}_k{k}.npz`（H 系列，bf16 推理） | `StorySource.embeddings`，P0 复核 |
| 谱视图 | `private/auditory_pf/features_001/features.npz`（cont）＋`private/auditory_nextmap/h4_features_001/specplus_ha.npz` | `StorySource.spectral_view`（340 维） |
| 技术视图 | `AgeSource.technical`（5 列） | `StorySource.technical` |

材料包 CLI 与本实现的一一对应（全部经 `slurm/auditory_story_cpu.sbatch` 在 Slurm 中运行）：

| 材料包 | 本实现 |
|---|---|
| `prepare` | `python -m auditory_story.cli prepare --run story_p0_001` |
| （P0 合成场景） | `... synthetic --run story_syn_002` |
| `train-profile` | `... train-profile --run story_p1_001 --prepare-run story_p0_001`（2 个数组任务） |
| `clinical` | `... clinical --run story_p2_001`，再 `... consolidate --run story_p2c_001`（汇总预测与逐调用台账） |
| `evaluate` | `... evaluate --run story_p3_001` |
| `report` | `... report --run story_final_001` |

## 2. 协议与代码差异

以下各项都在任何 SIR/MUSS 拟合之前写定，并写进冻结协议；没有一项是看到相应结果后改的。

1. **PCA 白化**：32 维分数除以特征值平方根。材料包只写"标准化与 PCA"。白化让冻结的 log 方差界和 tanh 输入尺度不起截断作用。C_MEAN/C_MEAN8 在临床头内重新标准化，不受影响。
2. **历史字段**：用 ST1 已审计的 `previous_run_length`，即"到前一个声音为止的同码连续长度"，与配置字段名一致。正文的"前置标准数"与它只在偏差音后的第一个标准音上不同。位置用时间比例定义。缺失值（链断点）：接受试次中 run 缺 556 个、gap 缺 179 个，用训练池中位数填补。
3. **物理块**：以 epoch 中心（onset＋0.2 s）在 D1 区间内的相对秒计。55 个主记录都只有一个区间；守护 5 秒也作用于区间末端。
4. **episode**：方向逐步交替；两臂共用初始权重和 episode 流（共同随机数），使两臂差异只来自支持集合的组织方式。
5. **临床设计**：边界外常数外推（sklearn 默认）；分位结点重复时也走线性回退；MUSS 内层按裁剪后的 MAE 选 λ。
6. **内层折**：在 L 内用种子置换后轮流分折（12 → 4/4/4），不复用 PF2 内层折，否则在 L 上会很不均衡。
7. **E3 细节**：选择种子与臂无关；另报交换支持条件后的 NLL。E5 的两半摘要只用两组的守护试次。
8. **多一个 `consolidate` 步骤**：把 825 个原子临床任务文件汇成预测表和逐调用台账，不做拟合。
9. **合成场景**：第一次运行（`story_syn_001`）的目标 R² 是样本内拟合（10 个点配 9 个参数），没有意义。改为训练儿童拟合、留出儿童评分后重跑为 `story_syn_002`，两次运行都保留。
10. **判读规则**：把材料包的六个状态写成确定性次序，并给"宽区间"定了 δ = 0.1×(R_low(PRIOR) − R_low(C))。

## 3. 必要测试（`tests/auditory_story/test_story.py`，Slurm 1018084：22 项通过）

- **SRP 模型与损失**：同条件置换不变；u=0 精确恢复 q0；缺类拒绝；儿童×条件等权 NLL。
- **摘要计算**：流式 φ 均值与逐试次均值一致；`encode_from_means` 与 `encode` 一致；pooled 臂对支持条件标签不变。
- **变换**：child×class 权重；白化后单位方差；秩不足不补方向；PCA 抽样上限；人群截距不惩罚、权重和为 1；历史填补用训练中位数。
- **episode 与断点**：支持与查询来自不同块组、不重叠，方向交替；断点恢复与连续训练逐位相同；两臂初始化相同。
- **隐藏标签**：P1 代码不读取任何目标（静态检查）。
- **有序头**：解析梯度与有限差分一致；缺等级时五类概率合法；目标按均值缩放。
- **MUSS 与临床设计**：岭闭式解对应 nλ；设计只在拟合行上拟合，含线性回退；每次头部 10 次调用、平局取较大 λ；PRIOR 伪计数。
- **标签集合与评分**：标签集合嵌套、不读目标、内层 4/4/4；RPS、AUC、bootstrap、Holm。
- **预算**：计数为 30 / 8250 / 上限 9000；可选分支关闭。

## 4. P0 实际核对（`story_p0_001`，Slurm 1018088）：PASS，68 项

- **队列**：55 名儿童，SIR/MUSS 全部完整且合法；临床原表逐项一致；6 名儿童另有访问，不使用。
- **外折**：15 个单元在儿童、身份组和主记录层面都不相交。
- **编码器范围**：例如 s404_k0 的编码器训练范围是 58 名 lane 儿童，其中 44 名主队列、2 名非主队列有标签、7 名 NH、5 名无标签；测试儿童被编码器见过的数目为 0。
- **缓存**：draw0 最大差 2.4e-8；`all_idx` 一致；M_o 早于缓存。
- **试次**：48,747 个，中位数 948/人，83.3% 满足块守护；54/55 人可进 episode。
- **特征**：谱视图 340 维，1 个非有限值（拟合内用中位数填补）。
- **合成方向检查**（`story_syn_002`）：
  - 条件个体信息与目标相关时，两臂查询 NLL 都比 q0 改善约 0.39/维，留出目标 R² 为 0.997 / 0.987；
  - 只有与目标无关的稳定背景时，查询改善 0.077，但留出目标 R² 为 −0.35 / −0.49。

  这说明重建个体结构不等于预测功能（故事 §6.3）。另外，两类条件平均响应不同时，pooled 臂经非线性 φ 仍可携带条件特异信息。因此 C_POOL ≈ C_SRP 不能被读成"条件结构无用"。

## 5. 临床头

- 样条：`SplineTransformer(n_knots=3, degree=2, knots='quantile', include_bias=False, extrapolation='constant')`，只在当前有标签拟合行上拟合；唯一值 <4 或结点重复时走线性回退。
- 阈值参数化：t1＋累积 softplus(r)＋1e-4；稳定 log 差分 logσ(b)＋logσ(−a)＋log(1−e^{a−b})。
- 目标与优化：平均 NLL＋λ/2‖w‖²＋0.0005·Σ(t−logit(k/5))²；L-BFGS-B，最多 400 次迭代，gtol 1e-6。
- 训练集缺等级时保留五类输出，不删儿童、不并类。
- MUSS：目标在拟合集上中心化并标准化，(X'X＋nλI)w = X'y，裁到 [0,100]，另存未裁剪值。
- 评分：RPS、NLL bit（floor 1e-6，重评分 1e-8 / 1e-4）、Brier、期望 MAE、P(SIR>3) AUC。

## 6. 曝光范围

- 外层测试儿童不进入任何拟合：f_o 训练、PCA 与历史尺度、q0、SRP、C_MEAN8 PCA、临床头的结点/标准化/填补与 λ 选择。
- 内层临床验证儿童的无标签 EEG 进入 P1，这是声明的辅助池协议；他们的临床值不进入 P1。
- f_o 的刺激训练范围包括 T_o 中的 NH 与无标签儿童。
- 本队列此前被多轮探索，本轮是内部验证，不是独立确证。

## 7. 完成与未完成

| 模块 | implemented | tested_on_synthetic | tested_on_server | run_completed |
|---|---|---|---|---|
| P0 prepare | 是 | 是 | 是（PASS） | 是 |
| 合成场景 | 是 | 是 | 是 | 是 |
| P1 表示训练与 E3/E5 输出 | 是 | 是 | 是 | 是（30/30，作业 1018092） |
| P2 临床矩阵 | 是 | 是 | 是 | 是（825 个拟合任务、8250 次调用全部收敛，作业 1018101；汇总 1018126） |
| P3 评价 | 是 | 部分（评分与 bootstrap） | 是 | 是（作业 1018127） |
| report | 是 | 否 | 是 | 是（作业 1018128，`completion_summary.json`） |
| 事后描述（附录 001） | 是 | 否 | 是 | 是（作业 1018130，0 次拟合） |
| MFF 验证 / 竞争 story | 否（默认关闭） | — | — | — |
