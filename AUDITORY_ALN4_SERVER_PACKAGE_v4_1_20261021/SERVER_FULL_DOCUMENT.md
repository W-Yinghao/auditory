# AUDITORY ALN4.1 — 完整服务器合同

版本：4.1；日期：2026-10-21；基线：`3da8cf5758214c0cf87a1f1c8d67fb84b574000e`。

本文件与 plans/round1.json、reference/ 共同构成执行合同。对研究设计以 ALN4.1 正文和计划为准；evidence/ 原报告保留其原始时间/方法，不被重贴标签。



---

# 发给 server 的启动指令

请接续 W-Yinghao/auditory，按 AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021 实施下一轮。不要重新立项，不要重复已经完成且合同兼容的计算。

先读本包 `SERVER_FULL_DOCUMENT.md`、`plans/round1.json`、`docs/08_IMPLEMENTATION_AND_HANDOFF.md`，再读服务器现行 `AGENTS.md`、`CLAUDE_HANDOFF.md`、`CODEX_HANDOFF.md`。查当前 GitHub HEAD、工作树和真实 squeue，记录与包基线的差异；任何旧日进度数字都只是快照。

研究目标是“哪些声音相关关系能够跨听者/听觉经验/任务迁移，时间组织如何影响共享读出和个人适配”。不要把工作缩成五臂 AUC 排行榜。已经完成的内容成分、时间迁移、history/twin、年龄/组别、支持实验是本轮的依据和复用对象。

## 固定执行顺序

1. 保留原始结果、hold、执行身份；为 ALN4.1 创建隔离代码/结果命名空间。若 ALN4.0 已开始，登记为旧设计，保留其输出；不得静默改名成新 TCS/GCS。
2. 完成 D2/GX/NEXTMAP 旧证据 intake、私有数据 roster 与公共源/目标 overlap 核验。旧报告缺本地 blob 时，从服务器原文读取并登记；不用重新训练来“恢复历史”。
3. 选定一个可精确加载的 EEG Stage1：有界恢复 MindMix 释放的 EEG-only 资产；就绪失败则固定可信 CBraMod。不是按儿童分数选 backbone。完整 MindMix 外部方法是另一身份。
4. 建立三个原生采样时间窗、两人 × 每人 S32/Q32 episode、同一音频三视图、五臂接口。填写 BINDING，冻结数据/访问/代码/计划 hash。运行参考数学、真实模型梯度/保存重载、split/access 和 rich 三视图检查。
5. R1：TCS/TNCE/GCS 各两档 LR ×1000 updates，共 6 个短校准；共同源 dev ridge 选 LR；从同一初始化重新训练 TCS/TNCE/GCS/TCS_WRONG 各10000 updates。B0 不做 Stage2。
6. 五臂输出同一公共和私有冻结表示及内容/时间结果；B0/TCS/TNCE 做 5fold 私有 CE 全量微调（15fits）和冻结年龄回归；公共 attention 用同一 margin 的 mean-score 20s 主窗口，不开 integrator 网格。
7. 先报告科学端点、配对覆盖与身份清楚的对照，再报告 AUC/准确率、算力和优化诊断。输出完整个人级授权字段、失败/缺失原因和下一轮判断。有限值的弱/负结果不是重新调参的工程理由。

保留既定全项目 running+pending GPU 合计不超过10的约束；不使用 scontrol，不批量取消或释放旧 holds。工程和计算按 Slurm 规则执行。开发/冻结/实施按已经授权范围继续，不为一般 framing 或每个作业再请求 go；遇到真实无法解决的数据访问、正确性或资源冲突才升级。不要自动发布新的原始私有数据或身份映射；已授权去标识个人结果不需要再次询问。

先提交 `INTAKE.md`、`BINDING.json`、`IMPLEMENTATION_RECEIPT.json` 和 readiness 结果；它们是执行记录，不是等待研究者逐项批准的门槛。准备好即执行已授权 R1，期间按任务完成更新 `ROUND1_REPORT.md`。后两轮按固定闭合范围收束，保留所有有效结果，不把弱结果升级为无信息或天花板。


---

# 1. 研究关切、假设与工具

## 1.1 文章要解释什么

听觉任务的难点不仅是从 EEG 中找出可分的类别。同一段声音在不同听者、不同听觉经验和不同刺激范式中，可能有可共享的刺激关系，却不在同一个时间位置、读出方向或置信尺度上显现。我们要建立一种能学习这些关系、容纳有限个人调整的表征，并用内容、时间和多种下游用途检验它。

给 Pattern Recognition 的候选科学叙事是：**学习对响应时间组织保有分辨能力、又可用少量个体数据适配的声音–EEG统计依赖，以支持跨听者和跨听觉任务的共享读出。**这是待检验的研究解释，不是已证实结论。论文的应用价值由实际公共/私有任务承担，方法价值由可归因的训练/表示改进承担；只换预训练外壳或只换 loss 名称都不充分。

| 层次 | 固定关切或可改变内容 | 结果怎样改变判断 |
|---|---|---|
| 研究关切 | 可共享的声音关系；时间组织；个人所需支持；听觉经验与发育 | 某个模型失败不关闭这些问题 |
| H1 内容 | 声音配对训练增加与当前刺激有关、超出历史可预测性的读出 | 正确配对对 B0/wrong、history residual/twin 分别提供不同证据 |
| H2 组织 | 共享内容与时间读出具有可区分的迁移结构，时间标记的依赖学习有用 | 同窗口、固定跨窗、目标窗重拟合与 pooled CS 比较；可能不支持新方法 |
| H3 适配 | 低维个人时间权重可改善共同 query 上的读出，且不全由概率校准解释 | R2 支持预算、相同 query、校准对照直接检验 |
| H4 用途 | 同一冻结表示保留当前声音之外的发育/跨刺激用途 | 年龄按未见儿童预测；跨刺激按语义合格的共同对象检验 |
| 实现工具 | MindMix/CBraMod、local/REVE、传统核 CS/InfoNCE、PCA/ridge/CE | 可替换；不把赢家写入假设 |

年龄、HA、CI 和不同刺激不保证 CS 比 MindMix 更好。MindMix 自身有时间嵌入和多任务设计；其论文 Stage2 的融合与 pooling 也不等于完全没有时间结构。这里提出的是更直接的听觉时间/个体统计合同，需要匹配比较来证明价值。

## 1.2 已有证据承担的具体作用

下面数值来自本包 `evidence/evidence_ledger.json` 的 E01–E08 原始报告（含 commit、文件SHA、blob OID）。旧实验和 ALN4.1 的时间支持、head、训练可能不同，不跨合同直接相减。

| 已完成证据 | 可复用的发现 | 本轮承担的作用 |
|---|---|---|
| 声音内容与历史残差 | CBpre−local 的 history-conditional envelope r：DTU +0.008995 [0.000566,0.017424]；FAU +0.011993 [0.004213,0.019772]（E02） | 共享声音成分有可分析对象；保留 local/强CB作证据和现成输出 |
| 时间读出迁移 | DTU旧0→600ms固定读出损失0.222192、重拟合恢复0.136274；FAU分别0.098419、0.030371，报告区间均为正（E02/E03） | 区分内容可用与读出可复用；新方法进入同类问题，但新三窗独立定义 |
| 私有当前声音 | 一个有效 CB/CS 配置 full AUC≈.537，0–200/.516、200–400/.521、400–600/.508（报告精度，E03） | 儿童有有效当前声音读出；不能预定为失败外测 |
| history 与 strict twin | AP 相对校准history B1描述性增量 +.002314 bits/trial；相对其他block同history twin +.003470（E04） | 分清事件序列与当前EEG；这些是描述性人均值，不能补造置信区间 |
| auditory prior 配对机制 | AP−S儿童AUC +.0093125 [.0015238,.017101]；AP−APwrong +.0029003 [−.0047884,.010589]（E05） | 先验收益与正确声音对应的特异性是两个问题，wrong必须保留 |
| 人群/发育 | 既有1088年龄/时长系数未在原同时区间族中排除0（E03）；并不等于无年龄信息 | 年龄预测与既有endpoint关联分开；新轮只分析少量固定个人端点 |
| 支持与episode | 已有U30适配和两seed episode压力结果（E06/E07） | 适配友好的群体训练有依据；保留原支持合同，不重新搜索所有预算 |
| attention顺序修正 | 双顺序/antisymmetric修正已明确（E08） | 公共attention继承正确候选顺序，复用margin做有限积分 |

更正：旧讨论中 +0.009193 [0.000611,0.017774] 是 AP−XM，不能写 AP−S。包内以原报告标签为准。旧 native local/E_PUBLIC_TRANSFER 的 all-zero `pre` 与受影响 TG cell 仍无效；实际有 pre 输入的 FM 及有效 post 条件不连带作废。旧严格局部40ms结果与新400ms窗不能合并为同一时间分辨率。

D2/GX/NEXTMAP 的旧报告路径和 Git tree OID 已定位，但本机未成功取回这些原始 blob。旧 map 中的 MFF 年龄 MAE 12.50 vs 19.07 months 等只登记为待核验线索，不作为本轮已复核结论。服务器需读取原始报告、fold、预测与修正说明。已知 `gpu_age.train_age` 验证后未恢复train模式影响 G1 direct-age 与 H3 ft_from_stim，不能因此否定其它 D2 线性年龄结果。缺材料时报告缺失，不重跑所有旧实验。

## 1.3 哪些结果会改变 story

正确配对优于 B0 且优于 wrong，同时改善 history-conditional 内容，会支持“有用的刺激关系迁移”。只有优于 wrong 可能只是 wrong 损害表示，不能充分支持有用迁移。

TCS 优于 pooled GCS，且时间迁移/个人适配有相应改善，才增强时间组织方法主张；若只 AUC 有利而内容/时间端点不一致，就保留任务收益，不补写机制。TCS 与 TNCE 相当时，两者都是有效方法，不能宣称 CS 必要。缺少 global NCE 时，不宣称已识别 CS×时间结构的全因子交互。

年龄可预测只支持此队列、此表示及划分下的发育相关信息；不等价于听觉成熟度、临床效用或HA因果效果。若年龄相对原始EEG基线没有增量，仍保留其结果与当前声音/时间任务。跨刺激语义不兼容时不强造统一二分类。

三轮后按已获得证据定稿。如果新方法没有可靠增益，明确承认这一实现未得到支持；旧有效结果仍是研究成果。不会为保住一篇预想文章，把弱结果改写成无信息/天花板，也不会为保住CS继续开无限调参轮。


---

# 2. 时间标记的传统 CS 与支持适配

## 2.1 输入表示

对声音锚点 i，从实际 EEG 构造 W0=[−200,200)、W1=[0,400)、W2=[200,600) ms 三个窗口。分别调用同一 EEG backbone，保留通道身份，不允许跨窗 attention 后再把 token 命名成局部时间。物理访问见第3章。每个声音视图 v∈{env,ss,sc} 使用一个跨窗口共享的32维 EEG线性投影和现有固定32维声音head，两个模态各自 L2 normalize。

令 U_i,k 为某个视图的EEG投影，A_i为同一锚点音频表示，q=softmax(a+δ) 是一个人episode内所有锚点共用的三维权重。a 是学习的群体prior logits；δ是仅由该人支持集更新、每个episode重置的个人偏移。q不是神经潜伏期分布，也不是每个trial按声音自适应的注意力。

## 2.2 分布与精确定义

以离散时间标签 T 的 counting measure 和连续高斯 KDE 定义 p(U,T,A)，时间分量k质量q_k/n。比较联合密度与其边缘乘积的传统 Cauchy–Schwarz divergence。每个视图、每个人分别计算，不把人混合后让身份相关性冒充共同声音关系。

设 K^k_ij=exp(−||U_i,k−U_j,k||²/(2σ_u²))，L_ij=exp(−||A_i−A_j||²/(2σ_a²))，则

\[
A_k=n^{-2}\sum_{ij}K^k_{ij}L_{ij},\quad
B_k=(n^{-2}\sum_{ij}K^k_{ij})(n^{-2}\sum_{ij}L_{ij}),\quad
C_k=n^{-3}\sum_i(\sum_jK^k_{ij})(\sum_jL_{ij}).
\]
\[
D_{TCS}=\log\sum_k q_k^2 A_k+\log\sum_kq_k^2B_k-2\log\sum_kq_k^2C_k.
\]

这是 p(U,T,A) 与 p(U,T)p(A) 的经典CS，不是新divergence、不等于Shannon互信息的bits估计、不是条件MI的chain rule，也不是 Σq_k D_k。每个视图内所有窗口必须共享 EEG σ_u、维度和尺度，否则窗口间被省略的Gaussian归一化常数不能抵消。σ是**overlap kernel**标准差，等于KDE component标准差的√2倍。

完整保留对角项；不用Gram中心化、不删nearby pair、不加入InfoNCE mask、不按得分截断到0。float64 log-domain求和；有限值退化如实记录，数值溢出修复。每人 query 只有32个anchor，不能将三窗展开的96行称为96个独立样本。

初始 source-fit 面板下校准带宽并冻结：每个view将三窗EEG合并，仅取**同一window内不同anchor**的全部非对角距离汇总，取lower median作为一个共同σ_u；audio同理得到σ_a。不是每窗各取σ。若距离全部为0或σ不正，按数值/表示就绪故障查因；不得用target结果调bandwidth。乘子固定1。GCS在均匀q下先池化再归一，单独校准其一个EEGσ；audioσ复用。诊断需记录距分布、kernel均值/有效秩以及GCS池化前norm，避免相消被隐瞒。

## 2.3 支持适配与一阶训练

每个update抽2个人；每人32 support和32 query。先从support求δ，再从query更新backbone、投影和群体a。初始a=0；δ每次从0开始，只更新三个logits并减去其均值。

inner目标：三视图均值 L_support + (0.1/2)||δ||²；5步梯度下降、步长0.1。inner只读support；其特征和a均detach。outer使用 live backbone/a、q=softmax(a+stopgrad(δ_final))，两人query loss等权平均，另加0.01 KL(softmax(a)||Uniform(3))。这是明确的一阶surrogate，不声称 exact bilevel differentiation。原生实现不需要对torch.cdist求二阶梯度。

| Arm | query/support目标 | 时间信息与适配 |
|---|---|---|
| B0 | 无Stage2 | 同Stage1，q0均匀 |
| TCS | −D_TCS，三view等权 | 带时间标签的分布，支持更新δ |
| TNCE | Σq_k L_NCE,k，三view等权 | 同三窗/同S/Q/同一阶δ步骤；不是pooled NCE |
| GCS | −D_CS(L2(Σq_k U_k), A) | 同三窗/同S/Q/同δ步骤，只在依赖估计前做pooling |
| TCS_WRONG | 与TCS完全相同 | 同EEG、预算/超参数，跨family错配整套audio row |

TNCE温度0.1，采用仓库已经修正的symmetric masked multi-positive NCE。正例包含对应锚点；同内容的合法多正例按既定规则登记，same-family ±2s的其他近邻不作负例。每个方向分子/分母和无合法负例情况必须可审计。不能把这些masks传入CS。TCS、TNCE和GCS都有支持适配，比较不能被“只有新方法得到支持”混淆。

wrong在每人support/query各自构造跨family双射置换，三个audio view使用同一行置换；保持音频边缘和各view之间关系，破坏与EEG的对应。11/11/10的family计数允许无同family匹配；每episode重新确定，保存seed及mapping hash，不能同一固定映射跨epoch形成新可学的词典。

## 2.4 真正的贡献候选

CSAligner等已有工作已研究CS跨模态对齐，不能以“首次CS对齐”作为创新。候选方法贡献是：以听觉时间访问为显式变量构造依赖；在人内计算、在人间学习；训练时用支持/query分离压力，使一个低维个人组织变量可被使用；在EEG-only目标上区分共享内容、读出变换和支持校准。

这一设计不保证可识别的生理分解，也不自动解决年龄/听力confounding。q和q²归一化权重、log A/B/C及per-slot score都导出，但q峰值不能当响应时间；时间表型来自held-out读出曲线、重拟合恢复与稳定性。冻结读出同时报告使用q0与同头均匀权重重置，识别源prior究竟是否参与了收益。

## 2.5 转移内容

源→目标传EEG backbone θ和群体a。源64通道audio投影不直接套在20通道儿童上；保存用于源诊断，目标建立共同新head。query的真实audio从不进入EEG encoder。公共attention评分可以访问两个候选audio，但应明确这是候选可见的应用场景。

R1目标测试人δ=0。儿童全FT允许用外层训练儿童更新θ和群体a，所有臂相同；它不是测试儿童适配。R2儿童支持δ使用已获支持标签的CE，和源侧有paired audio的CS适配是不同的监督入口，不能称无标签TTA。年龄冻结probe只读backbone的有序三窗特征，使用δ=0且不用q缩放；不把会被后续标准化抵消的q乘法写成方法作用。


---

# 3. 数据、物理时间与身份隔离

## 3.1 固定源数据

继承有效 SparrKULee core/rich manifests 和 presentation exclusions [4,5,19]：fit 81,732 segments/64 people/48 content families；dev 6,332/10/9；bridge_cal 6,162/6/6。这些是已读取manifest的基线，server须核对实际纳入与文件hash。fit/dev/cal人和内容隔离；源与DTU/FAU/私有目标的重叠排除维持。cal不做R1 LR选择。

- core manifest SHA256 `3ffa6e6d013283368d1f7eb09bf6c9e7573c0ae4009304cf3bc1d9836c197046`。
- rich manifest SHA256 `c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd`。
- server完整manifest SHA256 `b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426`；路径 `private/auditory_alignment_v3/aln34/prior33/manifest.json`。

声音固定env、ss、sc三view等权：env为8样本包络，ss为8帧×4个source-fit谱PCA分量，sc为相邻PCA帧差范数。rich来自Whisper 128-bin logmel再PCA，不叫MFCC。必须 `open_with_rich` 合并core/rich、`DonorBank(...,rich=True)`、`rich_targets()`、现有`fixed_heads()`；原CBaud Stream只有env，不可照搬后静默丢两view。PCA/标准化/32d固定head仅用source-fit；三view每个batch都需完整。

## 3.2 先裁原生样本，再重采样，再padding

两种候选FM的一秒patch不能自动产生细时间轴。三窗各自独立backbone forward，共享参数，没有跨窗上下文。以原生样本时间落入半开区间为定义，端点取ceil；下表不是把400ms拉伸成1秒。

| 视图 | 名义支持ms | source64Hz相对anchor切片 | source200Hz有效点数 | private250Hz epoch切片 | private200Hz有效点数 |
|---|---|---|---:|---|---:|
| W0 | [−200,200) | [−12:13]，25点 | 78 | [0:100]，100点 | 80 |
| W1 | [0,400) | [0:26]，26点 | 81 | [50:150]，100点 | 80 |
| W2 | [200,600) | [13:39]，26点 | 81 | [100:200]，100点 | 80 |

source首/末实际采样时刻分别为W0 −187.5/+187.5ms、W1 0/+390.625ms、W2 +203.125/+593.75ms。每窗先裁实际样本，再用固定resampling实现得到 round(n_native×200/fs_native) 个点，保留其原生时长近似；右侧零pad到200，pad在缩放之后。可用 `scipy.signal.resample` 只对该crop计算，不能整秒FFT重采样后mask并声称只访问crop。实现也可用有确定边界处理的等价crop-only方案，必须冻结并验证。幅值/通道归一化继承资产合同，不能按每窗单独使用目标label选尺度；padding不能参与估计实际信号均值。

旧source接口用q+[-26:38]的64点窗，缺少新W2需要的q+38点。必须从原生DonorBank segment span读取，不能补零冒充数据。span长度357，保留原offset≥26且offset+39≤357，缓存几何上限为offset≤318、229个旧grid ticks（旧末tick319不能用）；生产采样进一步固定为 TICK_OFFS∩[26,281]，共200ticks、实际末tick280，使新W2的offset+39≤320、三crop均落在各自5s segment内。每条实际access记录native segment、anchor、crop start/stop、实际首末样本、resampled_valid_n、pad_n；拒绝越界。

本研究披露已有整记录offline滤波/标准化；以上是**模型直接输入样本支持**，不等于因果隔离或真实生理响应潜伏期。重叠400ms窗支持时间组织比较，不能把相关峰或q峰称行为反应时。旧40ms strict-local与旧全1s位置迁移保留各自方法定义。

## 3.3 人内支持/query采样

每update先抽2人，再各自选择3个可用content families。每个S32、Q32由11/11/10个不同5s segment组成，每segment只取1合法anchor。S/Q使用不同segment与不交叠physical access；相邻segment可能属于同一连续记录，需从native时间戳和full access envelope验证guard，而非仅比较segment ID。抽样失败先重抽满足合同的segment，不能自动减小S/Q、混人或静默复用同片。

已审计源fit 64人每人≥518segments、≥3families，人×family至少23segments。该计数只支持抽样可行性预判，**不替代物理guard核验**；某人若实际不满足，记录原因并修正共同采样池，在所有arms采用同一个版本。被排除人员/内容需报告，不能按分数排除。

S与Q可来自同一family但不允许原始时间范围/guard重叠；这检验同人跨片段支持，不等于新内容任务。source fit/dev的完整人和family外隔离另行承担泛化。batch流预生成/可重放，所有臂共用。每人单算CS/NCE、再等权平均；episode数量、anchor数和独立person数分别计。

## 3.4 目标数据合同

公共DTU/FAU继承现有严格participant/content/fit-ES-test划分与候选声音规则。主共同目标是已具备的envelope与history residual；已有频谱成分在可用队列继续复用，不假装所有队列都有相同rich流。DTU 44人HI/NH各22；FAU 67人HA/CI/TH；HI不自动等于HA。三者不与私有儿童混成一个临床样本。

私有主lane为BDF pure-tone的既定64儿童（55HA/9NH）一人一主记录，20channels×200 samples、250Hz、epoch[−200,600)ms，标准/偏差标签与history/bin/block/fold/age/device-duration可用。outer split seed20261005，5fold人数13/13/13/13/12；fit/ES为外层训练儿童的physical block划分，末约20%blocks作ES。这是train-person内的ES，不冒称inner heldout-person。

源loader依赖 `private/auditory_gx/GX_stage_001/epochs`、`private/auditory_pf/prepare_002/{records,children}.csv` 及GX1 shared predictions文件等；后者即使新模型不使用ev也可能是现有loader入口依赖。不得仅按“旧prediction”删除。NH device duration为NA，不填0。

MFF pure-tone已有41records/37ids（GX旧分析40/36），bapa29/27；9个同日同儿童候选配对中旧报告7个完整。先核绑定，不预先当成9个可比人。unknown语义不等于bapa，ba1/ba4稀少对象不能变成独立大任务。R1只恢复资产/旧结果；R2最多一项冻结跨刺激问题，见第5章。

所有角色列出可见EEG、音频、标签、metadata和选择用途。模型可以在目标训练儿童标签上学习，不可用测试儿童query标签选epoch/window/支持/分支。已存在无标签整记录预处理需明确披露，不能为了简写称完全inductive。

### 公共128Hz输入与唯一重采样责任层

现有 `load_dtu/load_fau` 是128Hz，DTU64通道、FAU31通道。公共三窗原生相对anchor切片依次为[-25:26]、[0:52]、[26:77]，51/52/51点；重采样有效点80/81/80，再pad200。必须用真实sampling rate计算，不能套source64Hz offsets。

本包固定**新time-bank wrapper**拥有crop→`scipy.signal.resample`→pad流程：给现成 `Backbone` 的已采样输入为200Hz/200点，构造`fs_native=200`，其resampler因长度相同直接返回。幅值缩放由backbone/资产adapter单独执行一次，外部wrapper不再乘0.15。MindMix新adapter遵守同一责任划分，并登记自身资产幅值合同。旧 `resample_fft` 对Nyquist的处理不保证逐点等于SciPy；不要一部分arm走旧resampler、一部分走新resampler。CPU缓存可复用三crop，但必须以原生crop为输入、记录正确有效点数且没有后续二次重采样。真实前向probe需断言单patch和20/31/64通道映射。


---

# 4. 有限优化与三轮收束

## 4.1 R1：方法及科学接口一起跑通

Stage1通过第7章资产核验后，在所有arm/seed间冻结身份。R1 seed3401。每个view/sourcehead初值、群体a=0、batch流与crop处理成对一致。全backbone从第一步更新；不得再用历史prefix-update配置冒称full。

六个短校准：TCS/TNCE/GCS × LR{1e-4,3e-4}，各1000updates。source-fit/dev各固定512合法anchor面板，seed3420；尽量均衡人和内容，确切ID和hash冻结。共同probe取原始backbone三窗tokens按固定slot/channel顺序串联；用fit面板逐维标准化，ridge λ=1e-3 trace(XXᵀ)/n、train截距，预测三view标准化原始声学特征；dev normalized MSE三view等权选LR，精确相同取1e-4。不用各loss自己的native score，不用儿童/DTU/FAU测试。

若两个LR候选都仅因有限值完全退化使probe不可辨，固定LR1e-4并标`uninformative_selection`；NaN/错位/漏梯度是工程故障，不能用这个fallback遮掩。TCS_WRONG继承TCS LR和带宽，不自行调参。

四个生产训练从相同Stage1/head随机初值重新开始，各10000updates；AdamW、weight decay1e-4、cosine LR、clip global norm5。主transfer固定final10000步，保存0/2500/5000/10000及resume；源dev/native loss、共同probe、核谱、表示rank和梯度是诊断，不按臂挑不同最佳epoch。总优化量是6000短校准+40000生产updates；三crop和inner/outer计算成本完整计入，不能与旧一秒单forward用相同“step数”冒充相同算力。

每person64anchor、每update2人、3crop→384 crop forwards的逻辑规模，支持特征可缓存于同update的inner步骤，但outer query必须保持有效梯度。显存不足按确定顺序microbatch backbone并重组完整每人Gram；不能缩小CS的n或把microbatch CS平均当同一估计。记录dropout/RNG与forward顺序，断点恢复需等价。

| R1项目 | 固定范围 | 计数/约束 |
|---|---|---|
| source短校准 | 3objective×2LR | 6fits |
| source生产 | TCS/TNCE/GCS/TCS_WRONG | 4fits |
| 冻结表征/内容/时间 | 5arms×DTU/FAU/private，各自既有fold | CPU heads与exports逐单位展开；不是15次encoder训练 |
| private CE full FT | B0/TCS/TNCE×5fold | 15fits |
| frozen age | core3 + raw EEG ridge + train-mean | 若5outer/4inner/5alpha，4ridge模型共420次小CPU拟合，另5trainmean；不含新backbone训练 |
| attention | core3×DTU/FAU | 20s主，5/10s由同margin描述性导出 |
| 旧跨刺激/age intake | D2/GX/NEXTMAP与私有roster | 读原资产，无新encoder训练 |

## 4.2 私有充分微调的共同配方

core3全部使用三窗共享backbone、每slot相同结构但独立参数的channel-aware signed spatial readout(k8/e32,d32)+2class linear CE classifier；同fold/seed的随机head初值一致。概率p=Σ softmax(a)_k p_k，loss为真实标签−log p_y；用logsumexp计算混合，不把logits平均冒称概率混合。全θ与a从首步可训练，测试人δ=0。对比的是有无源训练的初始化影响；新target训练可覆盖源prior，需导出前后a、θ变化和slot结果。

AdamW，backbone/readout/a LR均1e-4，wd1e-4（logits/bias/norm参数wd0，所有arms同一参数组规则），batch64，100epochs，cosine，clip5。每epoch updates=ceil(N_fit_trials/64)，先均匀抽训练儿童，再在该儿童内按自然trial分布抽样；不把类别强行均衡为50:50。所有arms跑完共同预算，选每儿童等权ES true-label NLL最低的epoch（含epoch0，tie早者）；最后状态也保留，test完全不参与。ES/fit标签访问分别计数。

输出每儿童AUC、NLL、Brier、BA(阈值.5)、原始类别比例、三slot概率和q0混合概率。主科学分析仍包含frozen比较与history/twin，不用全FT AUC替代所有端点。GCS/wrong在R1只做冻结科学对比，不补成25个private FT；后续若需要其FT说明机制，使用唯一消融预算槽并预先登记。

## 4.3 R2：复现、有限适配与一个跨刺激问题

seed3407/3413重复四条原始source生产（8fits），不重选LR，不根据R1测试结果删弱臂；重复核心3×5fold私有FT（30fits），冻结主科学端点也重复。R1提供优化诊断，若确有实现故障，修复受影响版本而非把出错结果并入主seed平均；如果只是预算未收敛，报告而不自动扩展至无限训练。

个人支持问题只用core3：既定U0/U10/U30合同、相同query，对照低维时间δ与概率校准。U10的n10=min(floor(0.1×全部available trials数), guarded early-support-pool大小)，不是支持池的10%；U30是最早ceil(0.3×物理block数)经过边界删除和guard后的全部pool，**不是10/30trials或秒**。U10固定原取样seed351410…351414，不用标签覆盖挑选support；五次支持抽样先在同人内平均，不增加人口n。沿用support_contract的pool/query、边界trial排除、完整EEG访问guard；允许的query一次固定。δ以每个arm/fold选定的private CE checkpoint为底座，从其a_target出发、每个新儿童δ=0重置；θ与三slot heads冻结，用支持标签CE更新δ。对照是同checkpoint混合概率的二参数正斜率affine-logit校准 pcal=sigmoid(exp(s)×logit(p)+b)，s=b=0起步、同支持上更新，penalty=(0.1/2)(s²+b²)，五步梯度下降lr0.1；仅logit计算将p固定截于[1e-6,1−1e-6]，对所有臂相同并登记。支持不足/单类不丢该人，按事先无更新fallback并记录。δ固定五步/lr0.1/L2系数0.1，不称待调的起点；校准与δ均只用support。主适配端点为共同query NLL，Brier与AUC作补充；affine校准通常不改变排序，不能仅凭AUC差异宣称优于校准。所有参数在R2 query评价前冻结。

跨刺激问题只占一席：优先选经身份/标签审核后可共享“当前声音身份或deviance关系”的两个刺激lane，在源lane训练冻结表示的读出并测试另一lane，再做同一表示的目标训练侧重拟合，区分关系可用与读出可复用。若标签语义不可共享，就改为两个lane各自训练读出并比较同儿童的时间/历史条件表型，这叫跨刺激表征评估，不能冒称zero-shot分类。两种问题只能在**查看新结果之前**由资产语义决定一个，并留选择记录；不取结果较好的路线。样本过少时报告配对描述，不新增未批准队列。

## 4.4 R3：外部比较和结束

固定一个外部方法席位：优先完整MindMix在其可忠实支持的共同公共听觉任务上比较；若资产/输入/依赖不能恢复，则以Transformer-CLIP替代这个席位。R1 intake先绑定可行路线与失败条件，不到R3看本方法成绩再选对手。同backbone TNCE不是完整MindMix，提取MindMix EEG-only encoder只是初始化/probe，二者必须标清。

整个R2/R3合计只有**一个可选方法消融槽**，上限3个source fits+15个private FT；例如无episode支持适配，或补GCS target FT，按最终想支持的单一主张选择，不能两个都做。该槽不是默认开满。外部方法若需独立source训练最多3seed、目标FT最多5fold×3seed；在输入不支持儿童时只做忠实公共比较，未用预算不转给其它模型。无新增架构×loss×window sweep，无R4。

最终报告依据内容特异性、时间读出、群体/个人变化和实际用途决定贡献的强度。统计不显著不触发反复训练；有效负结果保留。若方法组件不必要，删去对应必要性主张，保留成立的研究发现。


---

# 5. 下游科学评价与私有儿童的功能

## 5.1 共同冻结读出

五臂都缓存每个目标fold、每个人、每trial/anchor、每slot的原始backbone token表示，不把source64ch音频head错接到private20ch。冻结probe用相同结构与标签访问；同一target fold中的标准化/PCA只用其fit部分。

为了保持channel信息并限制CPU规模，按固定channel/token次序flatten，使用一个跨三slot共享的PCA64（维数min(64,D,Nfit−1)）；fit行最多8192个，按固定ID排序+seed3437选择，所有arms同一行集合，每slot等量，8192上限下实际最多8190行；严禁每slot独立PCA后直接做TG。只用fit统计、不能用ES/query做PCA；保存components/mean/scale和row hash。此降维为共同读出工具，raw维数/保留方差记录；不称无监督transductive test训练。

公共声学内容用现有ridge/源侧校准合同；私有用已有logistic/positive affine source-ES校准合同。相同hyperparameter候选和fit/ES access对所有arm一致，server复用已注册实现并把其参数hash写binding；不临时给TCS扩大readout搜索。参数/solver有不兼容时先做共同新版本，旧输出独立保留。

## 5.2 内容与时间分别问

公共共同内容端点：held-out人上的envelope r，以及用训练侧history-only模型解释后剩余的envelope readout r。已有谱成分结果继续呈现；缺少rich的队列不补造目标。private主要内容端点：当前standard/deviant AUC与history-conditional log-risk增量。后者使用同label access的history-only B1，并在其他physical block、同child/history-bin的strict-twin子集再比较当前EEG与twin EEG。完整query与strict subset分别报告人数、trials和风险，不用不同覆盖的两均值互相相减。

时间迁移固定三slot×三slot的同表示读出。对每个源窗r用训练侧数据拟合readout/calibrator；直接应用到目标窗s得到固定读出性能。然后在目标训练侧的窗s重新拟合相同容量readout，评价同一query。主时间对比预定W0→W2，完整3×3为描述性结构；报告同窗、固定迁移损失和重拟合恢复，方向按“更好”为正。重拟合恢复不是增加EEG数据、不是目标测试人labels、也不是个人δ支持。

当前源训练q0用于slot概率/预测混合，同时输出相同heads下q=uniform的结果和各slot结果。这项重置不新增encoder或head训练，只检查源time prior是否实际有用。相同head下融合可能改善方差，不能据此宣称潜在神经成分完成独立分解。稳定性可用既有block split-half，把不可靠的个人曲线明确标出来，不按可靠性阈值排除结果以制造人群差异。

## 5.3 年龄是独立可回答的用途

R1设置冻结表示年龄回归，回答“公共声音/时间训练后的同一编码器，是否保留可在未见儿童预测年龄的EEG信息”。这与年龄对AUC或history增量的关联是两个问题，不用后者的弱结果否定前者。

输入为每儿童一个主记录、每slot原始token向量的自然trial均值和std（ddof0），按固定slot/统计/channel顺序串联；不用事件标签、不用个体q、不把五个private FT网络产出的特征拼成统一空间。所有儿童由同一个source Stage2模型编码；B0同Stage1。可用age roster在看模型结果前按metadata缺失确定，年龄单位months。

既有5fold outer child identities；outer train内以seed3431固定child shuffle做4fold inner。每个inner fit单独逐维标准化、目标减train mean，dual ridge的alpha∈{.01,.1,1,10,100}乘trace(XXᵀ)/n，以inner MAE选，tie取小alpha；outer train重拟合，outer heldout预测。head的outer test年龄只用于最后算分。若metadata不足使某fold无法4折，记录实际原因，统一固定min(4,Ntrain)且至少2，不挑可预测子集。

两基线：同outer train平均年龄；相同epochs/同人/同fold的20-channel mean log-variance原始EEG ridge（从GX staged epoch读取，在hc整人channel z-score之前，先trial内真实样本variance再log再trial均值，确定epsilon=1e-12并登记信号单位，不能用padding；如原幅值资产不可用，明确MISSING_ASSET而不偷换成归一后参考），用同inner ridge流程。这个raw基线不是旧D2连续频谱基线；旧D2结果另表复用，合同一致才作直接数值比较。

输出每儿童OOF预测和误差、MAE(月)、RMSE、R²、Spearman、对train-mean/raw的配对误差变化及fold选择；按HA/NH描述并列，NH9人的不确定性明确。年龄和HA/佩戴时长相关，预测不自动表明听觉特异发育。三seed先计算每人每seed绝对误差、再在人内平均，之后作paired人口汇总；平均预测后算MAE属于ensemble另端点。RMSE由逐人OOF残差计算。fold/seed不是独立样本。`reference/age_probe.py`仅实现该小CPU读出，不替代真实EEG特征导出。

## 5.4 组别与发育关联收住范围

只预定四个人级端点：history-conditional当前声音增量、W0→W2固定读出损失、目标窗readout重拟合恢复、R2 U30相对U0的变化。core3均保留；用TCS−B0和TCS−TNCE的直接个人差异形成方法×组/年龄解释，不在一组显著另一组不显著时声称组间差异。

private用既有两式：全体age(year)+HA indicator；仅HA age(year)+device-duration(year)，NH时长不填0。FAU HA/CI/TH与DTU HI/NH各自按现有协变量/身份合同分析，不并队列强造疾病轴。控制预定端点/contrast多重比较，报告效应与区间；不给每个head/window/historybin都回归metadata。设备时长是横断面，不写成疗效轨迹。

## 5.5 Attention 与外部方法

公共attention使用attended/ignored两个候选，双顺序评分并遵守已修正的antisymmetric规则，tie=.5。主为mean-score连续20s证据积分，5/10s从同一margin流描述性导出；这些是积分时长而非神经/行为响应时间。采用共同声音readout评分，不要求CS native cosine天然具备一一坐标对齐。不得把需要候选音频的任务与儿童EEG-only任务混称相同输入预算。

完整MindMix比较遵循其三阶段、可用模态、训练数据和下游head，记录是否音频参与测试EEG表示。共同任务同split/metrics，并报告模态/预训练数据差异；如果接口不等价，不把失败归因到方法。此前local、CB真full、REVE与FMCA结果保留为历史外部/内部参照；本轮不为每个已试组件重新开网格。


---

# 6. 汇总、可改变判断与报告

## 6.1 分析单位与预定家族

统计基本单位是独立person，先在同person、同seed的合法query上计算，再对重复seed等权平均后做paired population比较。不得把trial/anchor/seed当新增人。两个方法人数或query不同，先列覆盖和共同query，再作匹配对比；缺失、代码失败、有限值负结果分开。

预定四个family：F_CONTENT（DTU/FAU history-residual envelope与private history增量，TCS−B0/TNCE/GCS/wrong）；F_TIME（各队列W0→W2固定损失与重拟合恢复，同四对比）；F_UTILITY（private CE AUC、core3年龄MAE、public attention20s，TCS−B0/TNCE以及年龄vsraw/mean）；F_ASSOC（第5章的四个人端点及指定metadata系数）。R2支持属于独立F_SUPPORT，cross-stimulus单独F_CROSS_STIM。每族的全部列、有效人数、缺失规则在看新结果前冻结。

复用仓库现有以person为单位的paired bootstrap/同时区间实现，但其旧hardcoded13families必须替换成上述声明并保存列清单。建议沿用原实施4000 bootstrap draws和seed命名；确切旧实现先核对并写binding，不从两个aggregate CI相减构造差异CI。本包generic `paired_summary.py`提供一个可审查的person-paired max-|t| bootstrap参考（4000draws），不是静默替换旧统计。不同family独立报告；跨family比较不声称全局校正。单seed R1标探索性，最终三seed人口推断仍以person为n。

当source数据或representation训练人员相互依赖时，person bootstrap只刻画目标样本条件于已训练模型的不确定性，三seed不等于重采样所有source训练数据。报告这种范围；少数同日跨刺激paired children只作明确有限样本估计。

## 6.2 必备结果文件

- `intake/`：Git/server/queue快照、资产/旧证据审计、真实数据roster和依赖；敏感原始身份留private。
- `bindings/BINDING.json`：所有实际hash、训练/ES/support/query可见内容、窗口/采样/overlap、planned与actual fits。
- `source/`：step级loss与CS log-potentials、q/q²、rank/梯度、每人n/合法negatives、实际time access、optimizer/fullupdate/重载receipt、checkpoint索引。
- `features/`：缓存索引/hash/产生代码/role，不将大原始特征推送公共仓库。
- `person_results.jsonl`：已授权去标识person、dataset/group、arm/seed/fold、endpoint/条件、query hash、value、n_trials、status；age预测按已授权字段scope保存，不公开原始身份。
- `contrasts.json` 与 `coverage.json`：paired n、seed覆盖、query对应、预定family和同时区间、探索性新增问题。
- `ROUND1_REPORT.md`：主科学问题→证据→解释→具体剩余不确定性；最后列训练成本、故障/偏差和R2执行差异。

状态枚举：NOT_RUN、RUNNING、COMPLETE_VALID、MISSING_ASSET、IMPLEMENTATION_FAILURE、NUMERICAL_FAILURE、INSUFFICIENT_DATA。有效低分/反向结果是COMPLETE_VALID，不用FAILED标签把它藏起来。退化但有限的表示按有效结果+diagnostic flag报告，真实shape/梯度/数据错位不能算科学负结果。

## 6.3 R1后的判断表

| 观察 | 允许判断 | 下一步 |
|---|---|---|
| 正确配对优于B0，且内容/历史控制一致 | 声音训练有有用迁移的证据 | 固定重复，评估个体支持与任务范围 |
| TCS和TNCE相当 | CS可行，CS必要性不成立 | 保留两者，不靠扩大调参制造胜者 |
| TCS优于GCS，时间结构也改善 | 时间分布构造有贡献的候选证据 | 用唯一消融槽检验仍未区分的机制 |
| TCS只优于wrong | 可能wrong伤害了表示 | 不能单凭此宣布刺激特异收益 |
| private AUC改善但content/time无对应 | 事件任务收益成立，机制未定 | 报告分离结果，不重写听觉时间故事 |
| age/core指标弱或反向 | 该任务/配方支持不足 | 保留旧有效结果；不推无信息/天花板 |
| source末段未收敛或input不兼容 | 优化/可用性仍有限 | 工程错误定点修；有限预算未解决不称充分证伪 |

所有新探索性contrast写明结果已知时间与选择理由，但不把新措辞当必须重做整个实验的理由。三轮里允许一个方法实现失败，允许保留所有有用旧结果；不要求把每条证据挤成一致方向。

### 家族按队列落地

F_CONTENT、F_TIME、F_UTILITY、F_ASSOC首先按cohort分别绑定，例如 `F_CONTENT:DTU`、`F_CONTENT:FAU`、`F_CONTENT:PRIVATE_BDF`。不同队列没有共同person，不能对跨队列列做complete-person交集。包内paired mean参考只接收同一cohort同一family的已配对个人差值；它的同时区间覆盖该family，不覆盖所有cohort/全部论文端点。若最终要报告跨队列统一家族，另用按cohort独立重采样、在同一replicate取全family最大统计量的既有统计框架，先冻结实现，不把不同人强配对。

metadata回归系数与R²/Spearman不是个人均值差，不能直接交给`paired_summary.py`；按既有person bootstrap重拟合每次回归/重新计算统计量。年龄MAE的配对绝对误差差值可使用该参考。完整family交集、各contrast独立可用人数和描述性全覆盖结果都保留。


---

# 7. Stage1 初始化资产：MindMix 优先核验，可信起点必须落地

本轮最多用一个 Stage1 初始化。先对 MindMix 释放的 EEG-only 资产做有界核验；在 ALN4 生产计划冻结前通过就采用，未通过即使用项目已有可严格加载的 CBraMod。核验不使用任何儿童目标表现。本包不要求重新训练数千小时 Stage1。

## 7.1 已核实与仍未核实

MindMix 仓库此前资产审计使用的代码 pin：`98445f368efcb161c638172501bd16f92d09a89d`。官方 README 把 `checkpoints/v2.4_large.pth` 列为 EEG-only 预训练资产，把 `pretrain_fusion_checkpoints/best_model_loss_0.0909.pth` 列为 Stage2 fusion 资产。现成 `load_pretrained_eeg.py` 从后者提取 `eeg_model.model.*`，不能拿它的输出冒充 Stage1。

已对 EEG-only 文件做 HTTP Range 和静态 pickle opcode 元数据审计，没有执行 unpickle、torch.load 或完整模型推理。文件不是不可用的小指针：响应给出总长166,531,622 bytes；LFS对象/响应 ETag 对应 SHA256 `707dfabf98e7c471fe7096722f97ac9aa06c3df1c86383b095cfc71f667455a0`。本地只读取190,971字节头部，**未独立计算完整文件 SHA**。

元数据中 `student.*` 是24个 transformer blocks、hidden=200；`cls_token=[1,1,200]`、`pos_embed=[1,109,200]`、`time_embed=[1,128,200]`、`qkv=[600,200]`。args含 `labram_large_patch200_1600_8k_vocab`、input1600、patch200；epoch=29。当前公开 factory 的 base 是12×200、large 是24×400，不能根据文件名选择 large 并忽略不匹配。位置/时间嵌入的当前实现也要逐项核对。

资产加入时的 commit 描述与后来 README 定位有差异；二者不能证明权重等于某个原始 LaBraM release，也不构成对作者的指控。现有公开材料尚不足以在本机确认“准确恢复了论文 Stage1”。即使 exact-load 成功，也应先标注为“MindMix-released EEG-only asset，恢复的24×200配置”；只有来源、架构、训练配置都吻合才能标论文 Stage1 reproduced。

## 7.2 Server 的有界核验

intake阶段给一次集中恢复尝试，不超过一个工作时段（建议4小时工程时间）；这不是效果搜索预算。应完成：下载完整资产并计算 SHA；识别真实 state_dict；记录每个 tensor 的名字、shape、用途；使用作者可追溯的结构恢复完整 EEG backbone；仅允许明确剥离 token-prediction/classification heads。记录 trainable backbone loaded numel / expected numel=1，且没有静默丢弃不匹配 backbone tensor。`strict=False` 单独不构成证据。

明确列出位置嵌入选择/重排、通道表、采样率、振幅归一化、本包三个实际crop、resampled有效点数、padding及完整儿童epoch的处理。只允许对现有 EEG 支持作重采样、合法位置映射或显式 padding；不能读取目标窗外数据来凑输入。完成独立 EEG 前向、所有 backbone 层梯度、保存→strict reload 输出一致性和20/31/64通道输入探针。只有 shape 不够，必须有运行验证。

若仍存在未解释架构缺口、部分随机 backbone 或输入不支持，记录 `asset_gate=not_passed`，采用已验证 CBraMod `pretrained_full`。这是一项事先固定的就绪决策，不能按分数把某个模型换上来。CB 资产应从项目 `FETCH_RECEIPT.json` 继承完整来源和权重 SHA；已知代码 pin `b9e96100`，HF `weighting666/CBraMod@500543c`，实际完整hash由server复核。

Stage1身份一经在 `BINDING.json` 冻结，五臂完全相同；R2复现也不换起点。后续另一 backbone 只能作为单独、明确命名的可移植性实验，不能与主结果混算。REVE仍保留竞争配置，但不是R1新增分支。


## 7.3 新版时间与外部比较补充

资产实际运行核验必须覆盖20/31/64通道、每窗78/81/80有效点+右pad200的接口；不能只用原1秒/800ms整段通过后声称新三窗已验证。记录patch定位与通道映射，所有backbone tensor完整恢复、从首步有效梯度、保存→strict reload同输入一致。

R1 intake优先核验完整MindMix外部比较的Stage2/downstream资产与可忠实公共任务；若工程就绪失败，固定Transformer-CLIP替代该外部席位。不得按本方法成绩选择对手。外部预训练数据重叠、audio可见性、license和输入合同必须真实记录。未在本机完成完整权重下载/torch加载；LFS SHA是来源声明，不冒充本机完整文件校验。

论文：https://proceedings.iclr.cc/paper_files/paper/2026/file/b0ae046e198a5e43141519868a959c74-Paper-Conference.pdf

官方代码：https://github.com/CookieMikeLiu/MindMix/tree/98445f368efcb161c638172501bd16f92d09a89d

Transformer-CLIP官方代码：https://github.com/exporl/transformer-clip-eeg

CSAligner（用于界定已有CS跨模态方法）：https://proceedings.iclr.cc/paper_files/paper/2026/file/42bc612558891859b1b8717051f2c7b0-Paper-Conference.pdf

经典CS依赖学习来源：https://people.csail.mit.edu/fisher/publications/papers/principe00vlsi.pdf


---

# 8. 服务器实现、就绪与历史资产

本包提供已明确的研究/统计合同、数学参考、年龄小读出和只读计划工具；**实际数据封装、backbone训练与目标缓存适配仍要在server实现并核验**。不把reference代码冒称已完成生产实现，也不把缺Torch的本地检查冒称GPU成功。

## 8.1 精确复用边界

详见 `evidence/REPO_INTERFACES_AND_REUSE.md`。主要现成入口：

| 现有入口 | 可以复用 | 必须补的部分 |
|---|---|---|
| `foundation_adapter.Backbone` / `fm_aligned32` | FM构造、token与真full骨干路径 | 独立原生三crop、完整更新/位置映射；不沿用旧progressive默认 |
| `aln34.cb_auditory.Stream/run_donor` | donor解析、旧训练周边 | 原Stream只有env且NCE hardcode；新增rich三view/人内episode/CS/TNCE/GCS |
| `prior33.views.open_with_rich` / `DonorBank` / `fixed_heads` | core+rich、固定声音空间 | 物理guard、200个segment-contained ticks与多view完整性assert |
| `local_train.fit_private_fm` | 私有fold/旧FM接口部分 | 原CS/NCE prototype不是本包CE；实现共同三slot概率混合CE薄封装 |
| `aln34.content_time` / `private_current_time_v2` | 内容/历史/时间探针机制 | 旧checkpoint ID/plan不可直接接新arm；新三窗缓存与共同PCA |
| `aln35.history_interface` | 严格other-block twin、B1校准 | 核验新query与同label access、保留full与subsetcoverage |
| `aln35.support_contract/support_runtime` | U10/U30、固定query、guard | 新δ支持头与概率校准匹配，R2才运行 |
| `aln34.attention_transfer` | 修正后的候选顺序、margin/window | 同新冻结源与20smean主端点 |
| `science_aggregate_v2/science_export` | 人级配对/组别输出 | 替换旧13family硬编码；不得调用旧ALN4四臂/64人专用summary |

新模块建议隔离在 `auditory_alignment_v3/aln41/`，production配置/Slurm按项目规范生成。先复制受影响代码到隔离版本，不编辑运行中的源码。包内reference可直接导入或等价重写，但每个等价实现需比对数值与梯度；记录最终生产code commit和hash。

## 8.2 工程就绪检查

Stage1完整权重/20、31与64通道、三crop输入、全层梯度、optimizer参数组、保存重载一致；rich三view完整；人/内容split与source/target overlap；native crop与物理guard；S/Q无数据或label泄漏；wrong保持audio多view同置换；NCE与CS数学接口；低维δ只读support；source10000步transfer选择；private CE真实标签ES选择；age child内外fold；结果缓存hash均需要receipt。

先跑纯数学与一个真实小batch前后向/保存恢复，再跑生产。不设AUC/r/p-value就绪线；有限值低效模型进入结果。缺实际private数据只阻断该数据任务，不阻断已经就绪的公共工作。验证通过也不意味着方法有效。

`scripts/validate_binding.py`检查必要键、已确认字段、路径hash格式和训练/test隔离记录；它不访问server数据库，不能替代实际split/access扫描。`scripts/materialize_plan.py`仅输出有依赖的逻辑单位，不提交Slurm；实际publicfold/CPUhead/featurecache数量由binding materializer展开并登记。

## 8.3 旧结果复用与删除问题

GitHub本包基线HEAD为3da8cf5；CBAUD_PEOPLE20/20、episode seed3407 10/10等已完成。README 2026-10-20 19:55的remaining计数是旧快照，不写成现在还在运行。真正job状态由server squeue、日志和receipt确定；readme/source更新后重新绑定，不拿旧聊天状态覆盖它。

先保留 A3d 233GiB、A3c43.1GiB、A3b13.8GiB、ALN2 D_FM32.1GiB 的原始资产身份。容量不是可删证据。登记每类路径、真实bytes、checkpoint/预测/缓存性质、复用到哪些已完成/新分析、是否有不可重建权重/划分/receipt。只有某资产无后继依赖且已有验证完整的输出/来源/重建方案，才另写逐文件可删建议。本包不执行删除、不使新结果依赖已被假定删除的checkpoint。

source新资产优先保存0/2500/5000/10000四个step checkpoints、源/目标预测、可复用冻结表示索引及receipt；避免每个probe复制整个backbone。计算/磁盘成本单列，不把工程清理替代研究判断。

## 8.4 既有权限与调度

保留用户既定10-GPU running+pending总帽、Slurm计算规则、项目精确job所有权；不得scontrol或一键cancel/重置holds。`/projects/EEG-foundation-model/auditory`只读。新下载数据/模型依既有/projects约定放置，不占home重复复制。当前包准备不代表本地已连接server或提交job。

新的研究收束指令优先于旧“永远探索不定story”的表述；其余泄漏/隐私/版本边界继续。个体去标识结果在用户已授权字段范围内无需重复询问；不扩展到原始EEG、身份映射或新个人敏感字段。新GitHub发布按既有明确授权处理，本包不自动push或发送给他人。


---

# Local validation and implementation status — ALN4.1

## Passed here

- Time-tagged CS NumPy reference: 16/16. Expanded counting-measure KDE agrees with the q² expression; degenerate limits, slot normalization and analytic gate gradients checked. Maximum gate finite-difference error about 6.1e-10.
- Classical CS independent Gaussian-mixture/quadrature checks: 10 NumPy/oracle checks passed. Torch-dependent part not run.
- Physical time access: 9/9. Native64/128/250Hz indices, resampled lengths, exact 200-tick source sampling, border rejection, zero padding and outside-crop perturbation isolation checked.
- Nested child age ridge: 11/11. Independent primal/dual prediction, heldout-label and feature isolation, duplicate-ID rejection, roster filtering, row-order invariance and NPZ/JSON CLI checked. Synthetic data only.
- Handoff checks: 9/9. Python syntax, logical DAG, exact core fit roster, sample contracts, template rejection, seed-before-person inference, paired bootstrap translation, missingness/duplicate handling and eight evidence hashes checked.
- The read-only materializer emits 72 logical units: these are not 72 model fits. Six short source fits, four production source fits and fifteen private full-FT fits are fixed. Frozen bundles expand to target folds/head fits after binding.

## Explicitly incomplete

Torch is not installed in this environment. `verify_temporal_torch.py` exits2 with `torch_not_installed`; the inherited classical CS verifier also exits2 because its Torch checks did not run. No real EEG backbone, GPU forward/backward, Stage1 exact-load, private feature export or model-training result has been validated here. The server must implement the thin wrappers and run its engineering checks through Slurm before production.

`BINDING.template.json` intentionally fails readiness with unbound fields. It is a template, not a fabricated run receipt. `validate_binding.py --scope source` can validate source readiness separately, so missing private/age or legacy report assets need not block independently ready public work. The validator is structural and cannot prove actual data leakage checks on its own.

## Repository evidence and access

The task's most recent successful GitHub HEAD check was `3da8cf5758214c0cf87a1f1c8d67fb84b574000e`. The final retry failed because the shell network proxy could not be reached; the web API fallback was also unavailable. This does not establish a new remote state. Server intake must recheck its current remote, working tree, handoff files and real queue.

Eight public report bytes are included under `evidence/repo_snapshots/` and match the pinned evidence ledger. D2/GX/NEXTMAP older reports are tree-identified but were not fully retrievable here; their original contents/results must be read on the server. No claim is made that the complete prior conversation or unavailable original ALN3.4 attachment was newly read in this turn.

## Design review corrections applied

Independent method, private and repository reviews led to: matched GCS support adaptation; only core-three private FT; TICK_OFFS∩[26,281] with200 actual source ticks; explicit128Hz public access and31-channel input; one resampling owner; exact U10 denominator; fixed CE-checkpoint support adaptation and two-parameter probability control; age raw-reference extraction before person z-score; per-cohort simultaneous families. These were interface/design corrections, not additional efficacy searches.

No server connection, training submission, raw private-data publication or deletion was executed by this local package build.
