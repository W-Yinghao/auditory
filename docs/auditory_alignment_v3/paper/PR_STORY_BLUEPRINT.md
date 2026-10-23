# Pattern Recognition 投稿：主线与论证蓝图（草案 v1，2026-10-21）

研究者方向（2026-10-21）：针对 MindMix 发起攻击并改进。Stage1 用通用 EEG foundation model（我们用 CBraMod）；要论证的是 Stage2/3
的对齐方式。MindMix 用 InfoNCE 式目标强行对齐两个 token，我们用 CS divergence 这类统计依赖方法，让通用 EEG 特征适用于不同听觉任务。
不停留在 "CS beat InfoNCE"，要用 CS 的性质（信息论、可分解）回答"别的数据集里什么内容支持迁移"，从多个角度论证，偏解释与分析。

本文件只做证据组织与计划。数字全部引自已有报告（文末来源），没有新计算。人是统计单位；多数 ALN4.1 对比目前仅 seed 3401，R2 补 3407/3413。

---

## 0. 一句话主张（候选）

> 对比式融合对齐（MindMix/CALRA + InfoNCE）的目标可以在没有大脑信号的情况下被满足，其高准确率依赖特权槽位打分；
> 以 Cauchy–Schwarz 二次互信息为核心的依赖框架既能训练对齐，又给出**有零点、可检验、可分解**的依赖度量。
> 用它可以回答：哪些声音内容、在哪个时间组织、对哪些听者，携带可跨数据集迁移的 EEG 依赖。

"更好"的含义分六个角度（A–F），准确率只是其中一个（G），而且要如实报告。

## 1. MindMix 的准确定位（审稿人会核对）

- 论文为 ICLR 2026。Stage1：LaBraM-base **结构**，在 3,564 h 非听觉 EEG 上**自己预训练**，不是 LaBraM 权重。Stage2：CALRA（双向
  cross-attention + 共享低秩）后接 InfoNCE，在约 100 h 配对数据上训练。Stage3：下游微调。
- 它的消融显示：用 CBraMod 初始化，KUL 从 99.82% 降到 96.37%。我们固定 CBraMod 作为共同 Stage1 需要在文中说明是控制骨干的设计。
- 缺陷不在 InfoNCE 本身，而在 **CALRA 的交叉条件化**：正样本对两侧都是 `CALRA(eeg_i, a_i)` 的输出，EEG 表征被候选音频条件化。

## 2. 论证框架

状态：✓ 已有证据；◐ 部分；○ 待做。

### A. 审计：对比融合对齐可以不需要大脑（攻击）

| 证据 | 数值 | 状态 |
|---|---|---|
| 官方 Stage3 ClipLoss，真实 EEG + 被注意流 | 0.0087，batch 内 top-1 1.0 | ✓ |
| 换成被忽略流当 target | 0.0049，top-1 1.0 | ✓ |
| 高斯噪声 EEG | 0.0087，top-1 1.0 | ✓ |
| 去掉 CALRA（只用投影） | 3.26，top-1 0.0625（随机 1/16） | ✓ |
| 官方 AAD 打分器 | 两种候选顺序下 target 槽都赢 100%，噪声输入同样；batch=1 永远平局 | ✓ |
| 盲（顺序对称化）margin，真实 vs 噪声 EEG | r = 0.997，符号一致 100% | ✓（发布权重，未微调） |
| 10 单元忠实运行（DTU44，官方代码与配方，固定第 50 epoch，盲打分，20 s 共同协议） | 进行中 | ◐ |
| 同一批模型再用官方打分器算一遍（特权槽位 vs 盲，并排） | 每单元已存 final_model.pt | ○ W2 |
| MindMix 的信息审计：CS(EEG 分支嵌入; 声音属性)、CS(融合输出; 声音属性) 真实 vs 噪声 EEG | — | ○ W2 |

论文写法：同一模型、两种打分器并排；再给出依赖来源审计（融合输出的依赖来自音频分支）。
这比"我们准确率更高"更有力，也直接引出 B 角度。

### B. 度量：CS 依赖是有零点、可检验、对 batch 不敏感的量（方法性质）

| 性质 | 已有证据 | 状态 |
|---|---|---|
| 独立时期望为零；可用置换零分布检验 | 噪声 EEG 对照在所有臂和窗口约为 0（DTU B0 +0.09e-4 [−0.18,+0.35]），真实表示全部为正（C.1） | ✓ W1 |
| InfoNCE 受 log N 上限约束，并可经投影塌缩达到 | TNCE query loss 从 update 2500 起停在 ln 32 = 3.466；投影有效秩 18→3.3–3.6，平均余弦 1.00。TCS 保持秩约 12（余弦 0.67） | ✓ ALN4.2 诊断 |
| 不依赖负样本数量 | KCS：batch 128→512，CS_SINGLE −0.003 [−0.017,+0.011]，NCE +0.157 [+0.131,+0.185] | ✓（旧编码器） |
| 概率校准 | 私有儿童：CS_SINGLE native 校准 +0.002，NCE prototype head −0.040 [−0.046,−0.034] | ✓ |
| 训练得到的表征可被同一度量检验 | 测试集 CS(true)−CS(mismatch)：CS 训练 +0.005/+0.013/+0.003 nats，NCE 训练约 1e-4 | ✓（描述性） |
| 对错误配对敏感 | wrong-pair 训练损失：CS +0.27（FAU）/+0.56（DTU）bits；NCE 约两倍 | ✓ |

### C. 解释：依赖图谱（核心新贡献，CPU）

问题：哪些声音内容（env、onset、spec、flux、Ac、Lz、history 残差）、哪个时间槽（W0/W1/W2），在哪个队列 / 听力群体 / 个人身上，
冻结表征与刺激之间有**超出置换零分布**的 CS 依赖？Stage2 各目标相对 B0 增加了哪一类依赖？

- 已有的线性读出证据（作为交叉验证）：
  - 六种属性在所有模型中都可读：DTU 120/120 格、FAU 101/120 格；去掉前序特征后的残差仍可读：119/120、82/120。
  - 前向模型在包络之外的增量（DTU）：spec +0.0056、flux +0.0038、Lz +0.0012；onset、Ac 不确定。
  - CBpre 相对 CBrand 的优势落在包络 history 残差上：DTU +0.0153、FAU +0.0156（r）。
  - 公共先验训练没有让属性更可读：960 个对角格 0 个为正。
- 已有、可直接复用的数据：
  - ALN4.1 冻结特征：5 arm × DTU/FAU × 2 content fold × 3 seed，PCA64 × 3 槽。
  - aln34 缓存：local / CBpre / CBrand / REVEpre × 6 属性 × 5 个窗口中心，已存。
  - 私有儿童的分类标签：stad/devt + 6 档 since-deviant history，用 cs_qmi 的分类分支。
- 估计器：`aln41/cs_qmi_reference.cs_qmi`，σ 只在训练人上校准。零分布为人内循环移位（保持自相关），另做噪声 EEG 和换人 EEG 对照。
- 成本：约 1–2 CPU-h（每人 500–800 anchor，100 次置换）。

#### C.1 W1 结果（2026-10-22；探索性，在 ALN4.1 R1 / ALN4.2 之后设计）

计划 `cs_atlas_v1`（sha `060e2998…`，232 个单元），结果在 `results/auditory_alignment_v3/paper/cs_atlas/ATLAS.md`。

- **统计设置**：
  - 指标是超额 CS 依赖，即真实值减去人内片段循环移位零分布（20 次）的均值，单位 1e-4 nats；
  - 先在人内平均 content fold，ALN4.1 非 B0 臂再平均 3 个 seed；
  - 族内用 bootstrap-t max-|T*| 给出同时 95% 区间；
  - DTU 44 人，FAU 67 人。

**零点（B 角度）**：
- 噪声 EEG 对照在所有臂、所有窗口约为 0，例如 DTU B0 +0.09 [−0.18, +0.35]。
- 真实表示在所有臂、所有窗口、两个队列都为正，例如 DTU B0 W0 +1.19 [+0.86, +1.55]。
- 这在实测上证明了"独立时为零"的性质。InfoNCE 损失没有这样的零点。

**ALN4.1 冻结特征 × 包络**：
- **哪个臂都有依赖**：所有臂都携带超出零分布的包络依赖。DTU W0：B0 +1.19，TCS +1.45，TNCE +1.26，GCS +0.80，TCS_WRONG +0.76。
- **去掉包络自身 history 后多数仍为正**（DTU B0 +0.50；FAU TNCE W0 +1.74）。
- **时间分布**：W0/W1 高于 W2。
- **Stage2 相对 B0**：
  - TCS−B0 处处含 0；
  - FAU W1 上 TNCE−B0 +0.69 [+0.04, +1.35]，GCS−B0 +0.70 [+0.16, +1.24]；
  - TCS−TNCE 处处含 0。在 env|history 上 TNCE 的点估计更高，例如 FAU W0 −0.93 [−2.08, +0.21]。
  - 所以 CS 目标没有让冻结特征比 InfoNCE 保留更多包络依赖。这一点要如实写进 G。
- **T1 特异性**：
  - 原始包络上，最早窗口 TCS−TCS_WRONG 在 DTU 为 +0.69 [+0.07, +1.32]，FAU 为 +0.71 [−0.03, +1.45]（边缘）。
  - 去掉包络 history 后差异消失：DTU +0.11 [−0.32, +0.54]，FAU +0.19 [−0.17, +0.54]。
  - 解读：正确配对多保留的是包络里能由自身历史预测的慢结构，不是当前时刻的新刺激信息。
  - 同一窗口 TCS−GCS 为 +0.65 [+0.03, +1.27]（DTU）：时间标记在最早窗口保留更多。

**ALN3.4 四类模型 × 六种属性 × 五个窗口中心**（任务训练的表示，对照为同窗原始 EEG）：
- **学到的表示远多于原始 EEG**：learned−raw 在 6 种属性、2 个队列的多数窗口都为正，例如 DTU env 0 ms +14.34，FAU env 0 ms +6.26。
- **去掉前序特征后的 conditional 视图仍为正**，例如 DTU flux +9.50、Ac +4.82。依赖不只是包络的副本。
- **时间分布**：峰值在 0 ms 中心。
- **T3（预训练是否让属性更可读）**：
  - 改用非线性的 CS 依赖重测，CBpre−CBrand 大多仍含 0。
  - 例外只有 DTU Ac 0 ms（conditional +1.60，direct +1.31）和 DTU flux −200 ms（+1.04 / +0.95）；少数格为负（DTU Ac 600 ms −0.48，FAU flux 200 ms −0.58）。
  - 结论与线性读出一致：Stage1 预训练对属性依赖的贡献小而局部。依赖主要来自任务训练。
- **CBpre−local**：
  - DTU 上 local 在 env、Lz、flux、spec 多个窗口更高（env 0 ms −3.52）。
  - FAU 方向不一：onset 0 ms 上 CBpre 更高（+1.80），env 200/400 ms 上 local 更高。
- **REVE 预训练数值最高**（DTU env 0 ms +18.48，CBpre +12.16）。它不在预设对比内，只作描述。

**对论文的含义**：
- B 的零点性质有了实测图。
- C 回答"什么内容"：六种属性都有依赖，去掉前序后仍在，峰值在 0 ms；来源是任务训练，不是通用预训练。
- T1 有弱的正面证据，但仅限于可由 history 解释的部分。措辞应为"正确配对使表示保留更多包络慢结构"，不写成"学到了刺激关系"。
- 这一估计器可直接用于 W2 的 MindMix 信息审计（EEG 分支、融合输出，真实 vs 噪声）。

### D. 迁移：源数据集的哪类内容支持迁移（信息论 + 因果两条腿）

- **相关一侧（W3，小 GPU）**：在 SparrKULee 源人上抽同样的冻结特征，得到源侧依赖图谱。检验源侧各属性 / 时间槽的依赖
  （及 Stage2 带来的变化）能否预测目标侧（DTU、FAU 各群体）的依赖与读出收益。
- **因果一侧（W4，需批准）**：单视图 Stage2。源训练本来同时用三个视图：env（包络）、ss（Whisper log-mel PCA4 谱结构）、
  sc（谱变化）。各训一个只用单一视图的 TCS，每个 3 seed，看哪类源内容带来哪类目标收益。
- 已有的相关证据：
  - DTU 上听觉续训可以部分替代人数：50% 人数时 +0.156 [+0.057,+0.256]，100% 时 +0.017（不确定）。
  - 错误音频续训强烈有害：−0.911 [−1.101,−0.720]。
  - 公共先验只在 DTU 有收益：+0.074 [+0.050,+0.099]，FAU、Federici 不确定。

### E. 跨听者与听力群体

| 证据 | 数值 | 状态 |
|---|---|---|
| HA 整组排除后的固定共享读出（训练、标准化、选择、读出都不含 HA EEG） | CBpre +0.00233 [+0.00139,+0.00327]，local +0.00173 [+0.00058,+0.00288]（MSE） | ✓ |
| CI 在排除与否两种情况下都约 0 | 不是"未参与训练"造成的 | ✓（限制） |
| FAU：AP 收益 HA−CI | +0.099 [+0.022,+0.176] | ✓ |
| DTU：HI−NH 的 late−early 增益 | NCE +0.239，CS +0.205（同向） | ✓ |
| 群体依赖图谱（C 的分组版本） | 队列层面完成（C.1）；按 HA/CI/TH 分组的汇总未做 | ◐ W1 |
| TCS−B0（FAU 内容） | +0.018 [+0.009,+0.027]；DTU +0.003（不确定） | ✓ 单 seed，R2 复制中 |

### F. 跨任务用途

| 任务 | 现状 |
|---|---|
| DTU 注意解码（20 s，盲，双顺序） | B0 = TCS = 0.626；TCS−TNCE +0.029 [+0.002,+0.055]，即 TNCE 掉了、TCS 没掉。MindMix 盲结果进行中 |
| 儿童事件（stad/devt） | AUC 约 0.55；Stage2 没有改变微调 AUC（B0 .535 / TCS .537 / TNCE .538）。作为压力测试与边界 |
| 儿童跨刺激 puretone→bapa | R2 已抽特征，读出按约定留到 R2 最终分析 |
| 年龄 | Stage1 token 有发育信息：MAE B0 25.05 月 vs raw 32.38 月；Stage2 无增益 |
| 时间组织 | TCS−GCS FAU +0.034 [+0.022,+0.047]；固定读出右移 600 ms 损失 +0.222，重拟合恢复 +0.136（DTU） |

### G. 准确率：必须如实给出的一张表

- TNCE（同骨干、同数据、无交叉条件化的 InfoNCE）在内容读出上优于 TCS：DTU −0.034、FAU −0.012。
- 旧 KCS 线：NCE 在多数检索设置上高于 CS_SINGLE；CS 只在 Federici unified（+0.042）和儿童校准上占优。
- 写法：准确率"可比、不主导"。优越性由 A–F 承担，不用挑选的指标决定赢家。

## 3. 必须正面处理的威胁

| 威胁 | 证据 | 论文中的处理 |
|---|---|---|
| T1 正确配对的特异性未成立 | AP−APwrong 全含 0（DTU −0.0016 [−0.0254,+0.0222]）；TCS_WRONG 学到的 CS 依赖与 GCS 同幅（0.011→0.019）；投影空间正确配对检索全部是随机水平。W1：最早窗口 TCS−TCS_WRONG DTU +0.69e-4 [+0.07,+1.32]，FAU 边缘；去掉包络 history 后消失 | 写成"正确配对使冻结表示多保留包络的慢结构"，不写成学到刺激关系；与"迁移的是 EEG 域结构"并列为信息论结论 |
| T2 非融合 InfoNCE 准确率不低于 CS | 见 G | 不主张准确率优越；以 B（塌缩、log N、batch）和 C/D（可分解、可检验）论证 |
| T3 预训练没有让属性更可读 | 960 格中 0 个为正；CB 的风险优势不能由内容可读性解释。W1 用 CS 重测：CBpre−CBrand 大多含 0，只在 DTU Ac 0 ms、flux −200 ms 为正 | 作为发现报告：属性依赖主要来自任务训练，Stage1 预训练贡献小而局部 |
| T4 人数 / 内容量主导 | 50% 人数 vs 100%：−0.77；25% 内容：−0.99 | 加一条"规模轴"讨论，并与 D 的替代效应对照 |
| T5 儿童接近随机 | AUC 约 0.55 | 定位为边界条件与分类 CS 图谱的应用，不作主卖点 |
| T6 单 seed | 多数 ALN4.1 对比 | R2 补到 3 seed 后再定稿 |

## 4. 新增工作

| ID | 内容 | 资源 | 是否需要批准 |
|---|---|---|---|
| W1 | CS 依赖图谱（C、E 分组、T1 特异性、噪声 EEG 对照） | CPU 约 2.7 h（实际） | **已完成**（2026-10-22，见 C.1）；E 分组汇总待做 |
| W2 | MindMix：官方 vs 盲打分并排、信息审计 | 10 单元完成后；小 GPU | 建议做 |
| W3 | SparrKULee 源侧冻结特征 + 源侧图谱 | GPU 约 1 h | 建议做 |
| W4 | 单视图 Stage2（env / ss / sc × 3 seed）+ 冻结 + 读出 | GPU 约 10–12 h（R1 每个生产单元 37–53 min） | **需要**（超出 ALN4.2，不自动进 R4） |
| W5 | CBraMod + CALRA + InfoNCE，并做噪声 EEG 对照 | GPU 待估 | **需要**（可选） |
| W6 | 下载公开 KUL AAD，在 KUL 上复现攻击（MindMix 头条 99.82%） | 下载 + 约 20 GPU-h | **需要**（外部数据） |
| W7 | PR 稿件骨架、图、相关工作 | — | — |

## 5. 论文结构（PR）

1. 引言：听觉 EEG FM 的对齐主张；审计结果；依赖框架。
2. 方法：
   - CS-QMI 估计器、时间标记 TCS、分类分支；
   - 分解（属性 × 时间 × 群体 × 个人）与置换零分布；
   - 盲双顺序评测协议。
3. 实验一：对比融合的审计（A，W2）。
4. 实验二：对齐学习与表征性质（B、G）：TCS / GCS / TNCE / B0 / WRONG，3 seed，含塌缩与校准。
5. 实验三：依赖图谱——什么内容在何时对谁可迁移（C、D、E；W1、W3、W4）。
6. 实验四：用途——跨听者、注意、儿童、跨刺激、年龄（E、F）。
7. 讨论：特异性、规模、儿童边界、局限。

ALN4.2 包要求的五张图映射到实验三、四。新增图一张：审计（A）。

## 6. 时间线（截至 2026-10-21 晚）

- 进行中：
  - MindMix 10 单元；
  - ALN4.1 R2 私有微调（约 20 个，有抢占重跑）；
  - ALN3.6 R2 私有特征 10 个（lane 修复后已解锁）。
- 不等 GPU 即可开始：W1。
- R2 全部完成后：analysis_r2 → support → cross_stim 读出 → families，然后 ALN4.2 收束报告。

## 来源

- `docs/auditory_alignment_v3/aln41/ROUND1_REPORT.md`
- `results/auditory_alignment_v3/paper/cs_atlas/ATLAS.md`（W1）
- `results/auditory_alignment_v3/aln41/r1/FAMILY_TABLES.md`
- `docs/auditory_alignment_v3/aln42/SOURCE_LEARNING_REPORT.md`
- `docs/auditory_alignment_v3/aln36/R1_SCIENTIFIC_DECISION.md`
- `docs/auditory_alignment_v3/aln35/{SCIENCE_V2_READOUT, SCIENCE_V2_PRIOR_INTERPRETATION, PRIOR_SCIENCE_READOUT, SCIENCE_PRIVATE_RESULTS, AP_WRONG_RESULTS_V2, CBAUD_PEOPLE_RESULTS}.md`
- `docs/auditory_alignment_v3/{SCI_R2_RESULTS, CB_AUDITORY_CONTINUATION_RESULTS, PUBLIC_PRIOR_RESULTS, R_PRIVATE_CALIBRATION_RESULTS, ATTENTION_TRANSFER_RESULTS}.md`
- `docs/auditory_alignment_kernel_cs/{FULL_RESULTS, OPTIMIZATION_RESULTS}.md`
- MindMix 审计数字来自私有 readiness 报告第 6 节（只引用数字）
