> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../PUBLICATION.md).

> Historical draft review. Executed processing decisions (including60s A blocks) are defined in docs/AUDITORY5_EXECUTION_DECISIONS_v1.md and the frozen configuration.

# Auditory5 v1：§8–13 有界规范审阅

本文件只复述和核对执行约束，不报告真实分析结果，不改变 v1 方案。人数均指安全的 `candidate_id/split_group_id` 支持；记录数、epoch 数、seed 数和 bootstrap 重抽样不增加人数。

## 路线首轮最低闭环

| 路线 | 首轮必做实验 | 必做控制 | 主终点/固定主设置 | 最低人数与支持 |
|---|---|---|---|---|
| A | 在共同冻结编码器上，用两个交替 30 s 半份、每类固定 20 trial 计算条件差分 `r` 的同人对角与错位非对角匹配；并列 L0、R_SUP、R_SIM、R_RAND；报告未条件化均值背景。 | 半份错位；未条件化均值 `m`；pre 条件差异/历史与块位置平衡；范数标准化与非标准化；同维随机投影；共同 trial 预算；背景调整 `Δ_post ~ m_post + Δ_pre + mean_pre + quality`。 | `T_A`（对角 cosine − 非对角 cosine），主为 `R_SIM`、20/class/half；同时报内积/平方距离、rank、范数和 `T_post−T_pre`。推进门槛为完整支持候选至少 25、`T_A≥0.05`、候选 bootstrap 下界>0，且背景调整仍为正、非单候选驱动。 | 至少 25 个完整候选；每条件每半份至少 20 trial、每半份至少 4 个支持块。40/class/half 只作预设次要支持敏感性。 |
| B | 固定当前/前一事件组合（HA `1,1`；已确认 MFF 任务 `stad,stad`），先按完整事件链生成 H，再比较 context-only、pre、post、pre+post 四类历史读出；L0_HISTORY、R_SIM、R_SUP。 | gap/记录位置共同支持；pre 与“前一 trial 可观测特征+C”；短/长 post 诊断窗；真实事件时钟；同段循环错位仅 diagnostic null；加入质量到 C 的敏感性；拒绝中间 EEG trial 不得改 H。 | 主 `G=CE(B0_context_spline)−CE(B2_post)`，单位 bits/trial；关键 `CE(B1_pre)−CE(B3_pre_post)`。主支持为 `G≥0.01`、配对 bootstrap 下界>0、至少 60% 可测候选 gain>0。 | 至少 20 个候选，且两类历史各至少 20 trial、至少 4 块，训练/测试两类均存在；仅在共同支持层报告。 |
| C | P2_SPATIAL_SPLIT 上以相同 trial 交集训练/评估 `C_L,C_R,C_LR`，另做 `C_LL,C_RR`、线性读出及固定 32-hidden MLP；联合头内左右置零/同人跨块/跨类替换。先通过三个合成世界：复制线索、单边线索、XOR。 | 原始输入双向干预测试；相同 trial、类别权重、正则和读出族；`C_LL/C_RR` 复制输入容量对照；32/64 hidden 容量检查；校准和同头干预；报告双向 gain 而非只报 min。 | `T_C=min(G_R|L,G_L|R)`，主为独立 `R_SIM` 分支+32-hidden MLP，单位 bits/trial；并报 `G_R|L` 与 `G_L|R`。推进门槛完整候选至少 25、`T_C≥0.01`、bootstrap 下界>0，且超过复制输入/单分支扩容收益、输入隔离精确通过。 | 至少 25 个完整候选；每名测试候选每类至少 20 trial；主评估为左右双方资格的固定交集。 |
| D | 每个临床 outer fold 内完整嵌套拟合 encoder、刺激头、中心化、visible/null 分解、null PCA 和分组 ridge；比较 D0–D7，主流程分别保留 R_SIM 与 R_SUP，L0 为资源不足时的 smoke。 | fixed-head 概率不变（float64 `<1e−10`，float32 `≤1e−6`）；null 内新刺激 probe；随机 null（20 seeds）；全 z 匹配维数 PCA；pre 摘要；量表上限/逐候选误差/删一敏感性；D1 临床基线必须保留；无跨 fold embedding 拼接或临床泄漏。 | `T_D=MAE(D2_CV)−MAE(D3_CVN)`，主终点 HA 原始 MUSS 百分比（0–100），同时要求 D3_CVN 相对 D1_C 的 MAE 也改善；推进门槛 `T_D≥0.5` 分、OOF 配对 bootstrap 下界>0、非单候选/量表或身份冲突驱动。 | 至少 30 个完整、唯一固定临床链接候选；每条件固定 40 trial，主 D 集合不足者排除并报告支持损失。协变量/主终点完整，阈值单位与同期性保留未知。 |
| E | E0 对现有可追踪同人纯音/bapa 配对做任务内分块解码、trial 预算和事件语义核验；满足支持后才做 E1 纯音→bapa 主方向及逆向完整报告的冻结表征迁移矩阵（E_P/E_Q，另报 UNION/RAND）。 | 任务/事件语义确认；共同布局、通道映射、时间窗、QC、容量；task acquisition confounding；共同儿童划分；source/target unique label ledger；head-only 与固定 32-hidden MLP 容量；有限 adapter 仅在 gap 支持后。 | `T_E=CE_Q(h_P(f_P(X_Q)))−CE_Q(h_Q(f_Q(X_Q)))`，同一 Q 测试 trial 评估；主为线性头，单位 bits/trial。E1 还需目标 `J_bal≥0.01`、`T_E≥0.02`、配对区间下界>0；强读出消除 gap 标为 readout-limited。 | E0 不设群体最小人数，当前约 7 对只能点图/宽区间；E1 要两任务各至少 20 个安全候选，且每训练折目标任务至少 12 人、各自每类至少 40 trial。少于此仅 `SUPPORT_INSUFFICIENT_FOR_E1`。 |

## S0–S5 依赖与预算

执行依赖固定为：`S0 → S1 → S2 → S3 → S4 → S5`。S0–S4 是本轮目标；S5 只在 S4 判为可推进或混合且命中预设敏感性范围时执行。

| 阶段 | 必须完成/依赖 | 预算与边界 |
|---|---|---|
| S0 | 输入根、源码、受限产物、环境、schema/hash 核验，输出 `input_contract.json`；缺失键按路线隔离。 | 只读核验；CPU/GPU 探查经 Slurm；不因对账人数不足改资格。 |
| S1 | 去重与身份连通组、完整事件链、资格、通道图、固定折、P1/P2 预处理与泄漏单元测试；所有 hard gate PASS 才能进入训练。 | 合成/契约测试；生成新 manifest/splits，不能污染旧结果。 |
| S2 | L0 线性基线及 A–E 全覆盖小样本端到端 smoke；每路线正/负合成世界；建立从原始键到报告的路径。 | smoke 不作科学结论；合成机制至少重复 100 次小模拟，非 100 次大 CNN。 |
| S3 | 一 seed（11）完整冻结外折探索：共享基础 R_SUP/R_SIM；A–E 达到各自支持门槛者执行主路线和主控制。 | 最多 100 个 encoder 训练作业；最多同时 2 GPU、4 CPU 作业；不做路线×模型×损失×增强×seed 笛卡尔积。D 仍须 inner 3-fold 嵌套，不能用全局 encoder shortcut；C 两空间分支独立；E 按方向/任务隔离。 |
| S4 | 聚合所有已执行路线，保存暴露范围、支持/失败原因、控制与五行 verdict；未执行写 `NOT_RUN`。 | 仅合并同折标量/OOF 预测，不拼跨 fold 坐标；固定 2,000 次候选 cluster bootstrap，不重训完整流程。 |
| S5 | 对 S4 可推进/混合路线做预设 seed 23、37 与最多一轮关键敏感性；保留 v1 主结果。 | 仍在 100 encoder 总预算内；敏感性不根据结果新增终点/架构/扫参；失败或阴性不修到阳性。 |

## 真实结果前必须补写/冻结的歧义

1. **滤波支持与 30 s block 的优先级。** `P1_CAUSAL20` 同时出现起始保护 `max(20 s, pulse-tail)`、IIR 有效支持（绝对尾和 `<1e−6`）和 A 的 `block_width≥4×embargo+epoch_duration`。须在配置中明确 `embargo` 取哪一个（含采样率/边界取整）、保护舍弃如何应用于每个连续区间、若 30 s 不足时统一扩为多少个整 30 s，以及该规则如何与 B 的 `max(10 s, preprocessing_support)` 边界间隔相接。不能在看结果后用更宽/更窄 block 选择阳性。
2. **连续滤波 vs 分块独立滤波。** A 主分析允许连续流状态并只报告支持限制，却又要求独立分段滤波复核；需预先标明哪一个是主 estimand、哪一个是敏感性，不能把交替半份称为跨日独立重测。
3. **A 的块宽与试次抽样。** 固定 20/class/half 的无放回抽样在支持不足时的候选排除、40 trial 次要分析的共同支持集合和“至少 4 个块”的计数应写成机器可执行规则。
4. **B 的事件码语义与共同支持。** 先验核对发现 `1,1`/`stad,stad` 不满足固定匹配含义时，须冻结新 `code_map` 版本并重新计数；gap 分箱、位置粗分层、共同支持判定和单一 H 层的处理需在结果前锁定。循环错位只能是 diagnostic null。
5. **C 的输入与读出预算。** 明确局部平均参考、左右通道缺失映射、固定 trial 交集的排除顺序；固定 32/64 hidden、线性/MLP 的比较族及校准参数来源，防止容量差被写成互补信息。
6. **D 的临床可识别性。** 结果前固定 HA MUSS 百分比列、唯一链接/同期性状态、`device_duration` 缺失编码及阈值单位未知的处理；固定 SVD rank 相对阈值、INF 关闭组语义、40 trial 重抽样规则与 `[0,100]` 截断。不得因 MAE 方向选择另一个量表或把 MFF 0–40 合并进主终点。
7. **E 的任务/身份/曝光账本。** 预先固定 E0→E1 启动门槛、P→Q 主方向、共同布局与每候选 unique target labels/训练更新匹配；明确 adapter 是否仅用 `z_P`（可读性适配）或重新接触 raw `X_Q`（新输入路径），两者不能合并解释。
8. **跨路线与跨折可复用范围。** 只有完整 manifest、身份图、预处理、训练/验证组、任务标签、架构、模式和 seed hash 全匹配才可缓存；跨 fold 64 维 embedding 不得拼接，D inner fold 与 C/E 专用 encoder 不得借用共享全局模型。

