# 项目进展梳理 — 2026-10-20（Claude Code 接手后）

> **同日更新（用户：“全部开始”）**：第 4 节两批结果已读出，见 `docs/auditory_alignment_v3/aln35/SCIENCE_V2_PRIOR_INTERPRETATION.md`（公开数据六种声音属性在所有模型中都可读、残差属性仍可读；私有共同读出 AUC 0.51–0.54、只在 0–400 ms、EEG 不超过刺激历史；1,088 个发育系数和 320 个先验发育系数无一排除 0；先验不提高声音属性解码）。私有 C10/H10 变差已核实为温度选择受支持集类别比例影响。第 5 节第 3、4 项已登记为调度器插件 `c3_s35cbaud`（20 单元）和 `c3_s35epirep`（10 单元），探针由调度器自动发起。

覆盖范围：上次 Claude 会话结束（2026-10-17 10:49，停在公共先验 FIXC 修复）到今天。
依据：live Slurm 队列、各结果报告原文、1050758 完整比较 summary.json。只读整理，没有新训练或重算统计。
数值单位：公开数据为 ΔR bits/query（正=候选更好），私有为 AUC 或 bits/trial；n 为人数，seed/fold 不增加 n。
「+」区间在 0 之上，「−」在 0 之下，「0」含 0；含 0 不等于等效。

## 1. 这三天发生了什么

| 时间 | 事件 |
|---|---|
| 10-17 | Codex 接手；完成 FIXC、rich PCA、生产 manifest、M12/M13；ALN3.4 新 lane 全部登记并开跑（预算、数据/inner、适配、融合、episode、注意力、CB 听觉续训、私有 current/time、私有 episode/factorial、prior LOO/science、breadth） |
| 10-18 | 公共先验生产 1154/1154、TRUE_FULL 800/800、content/time 180/180、私有 current/time v2 130/130、prior science 300/300 完成；GitHub publish_030/031/032，远端 main = `5ef4a60` |
| 10-19 | 采纳 ALN3.5 包（16 个工作包：APwrong、support 覆盖、episode 压力、matched updates、true-risk 选择、融合归因、bridge、CB 状态、history 接口、注意力顺序等）；私有 pre 窗全零输入勘误；V100 部分开放；清理 2.39 GiB 废弃 FAU 数组 |
| 10-20 | 1050758 完整比较（290 个 family，0 校验问题）；Codex → Claude Code 交接；调度器换为 fleet v3（1051045），GPU 从 6 张提到 10 张 |

ALN3.5 的 16 个工作包除下面 4 条训练尾巴外全部完成。

## 2. 现在在跑 / 在排队

| Lane | 完成 / 总数 | worker | 粗估 |
|---|---:|---:|---|
| DTU 预算加倍 | 96/150 | 3 | 约 1 天多 |
| DTU 规模曲线（排除 inner 源） | 约 215/440 | 3（含 A30 长 worker） | 约 20 h |
| breadth 预算加倍 | 约 59/75 | 2 | 约 12 h |
| breadth 规模曲线 | 约 200/300 | 2 | 约 12 h |

10/10 张 runfill GPU 在跑，无排队，无失败标记。breadth 结束后空出的卡自动给 DTU 两条 lane（fleet v3，每条至多 6）。
证据服务 1047358 会在输入变化时自动刷新 NEW_LANES_EFFICACY / PUBLIC_BREADTH 等汇总。没有其他登记任务等待；1,602 个 hold 是旧版本执行身份，不应释放。

## 3. 结果总览（按 ALN3.5 三个研究关切）

### 3.1 跨听觉经历的共享声音结构

| 结论 | 数字 | 状态 | 来源 |
|---|---|---|---|
| CB 预训练 true-full 优于同访问 local | DTU +0.213 [0.129,0.297]、FAU +0.141、Federici +0.180（三 seed，44/67/86 人） | + | TRUE_FULL_PAIRED_EVIDENCE.md:84-100 |
| CB 预训练优于随机初始化 | DTU +0.20~+0.48、FAU +0.09~+0.12、Federici +0.05~+0.11 | + | ALN32_SEED_PANEL_RESULTS.md:39-48 |
| 冻结 CB 弱于 local | DTU −0.345、FAU −0.130、Federici −0.151 | − | 同上 :15-19 |
| REVE | 依数据集和学习率变号；Federici 预训练劣于随机 −0.099 | 混合 | 同上 :41-50 |
| 数据少时预训练更重要 | 25% 人数时 CBpre−CBrand +0.345 [0.242,0.449]，CBpre−local +0.149（DTU native） | + | NEW_LANES_EFFICACY.md:787 附近 |
| **训练人数是最强因素** | 同等更新次数下，50% 人数比 100% 差 0.27~0.77 bits（6/6 配置）；曲线 25% 人数在 DTU/FAU/Federici 都明显变差 | − for 少人数 | 1050758；NEW_LANES / PUBLIC_BREADTH |
| 公共听觉先验（含 SparrKULee 供体） | DTU S→AP +0.074 [0.050,0.099]；FAU、Federici 近零；私有 AUC +0.009 | DTU +，其余 0 | PUBLIC_PRIOR_RESULTS.md |
| 正确声音配对的特异性 | AP−APwrong：DTU −0.002、FAU −0.021、私有 AUC +0.003，全部含 0；APwrong 对 S 与 AP 同样有利 | 0 | AP_WRONG_RESULTS_V2.md:9-20 |
| CB 听觉续训 | paired vs direct +0.017 [−0.016,0.050]（DTU 三 seed）；wrong 音频续训严重有害 −0.91 | 对 direct 0，对 wrong + | CB_AUDITORY_CONTINUATION_RESULTS.md:49-51 |
| local+CB 概率融合 | 对 CB direct +0.051 [0.026,0.077]；对重复 CB-seed 混合 +0.025 [−0.001,0.052] | + / 0 | FUSION_ATTRIBUTION_RESULTS_1047619.md:9-12 |

**解读**：同一数据集里多加人（同样刺激、同样设备）收益很大；通用 EEG 预训练（CBraMod）在数据少时收益最大；
跨数据集的听觉配对预训练只在 DTU 有收益，而且错配音频同样有收益，所以目前看不出声音配对本身的贡献。
融合收益主要可以由多模型平均解释。

### 3.2 新听者还缺什么（个人支持与适配）

| 结论 | 数字 | 状态 |
|---|---|---|
| 30% 支持时低秩适配有益 | DTU rank4 vs 0 步 +0.024~+0.093（4/4）；FAU diagonal +0.033 | + |
| 10% 支持时适配不确定 | DTU U10/C10 +0.005~+0.028 | 0 |
| 支持数量重要 | U30 vs U10：rank4 +0.016~+0.065，仅校准 +0.18~+0.26 | + |
| 同数量下内容覆盖 | C10 vs U10 8/8 含 0 | 0 |
| 低秩适配优于仅校准概率 | +0.08~+0.32 | + |
| episode 训练（100 内步） | local native +0.034/+0.036 vs ordinary；CBpre native U30 −0.018；20 内步全部 0；旧 3 步版本 0 | 依骨干而定 |
| 选模规则 | true-risk vs 旧 gain：50% 人数 +0.10~+0.33（6/6）；100% 人数多数 0，2 格小 + | + |
| 私有儿童适配 | NLL ≤0.006 bits/trial，AUC ≤0.001；10% 支持时 rank4 输出适配略有害 | 无实际空间 |

详细解读：`docs/auditory_alignment_v3/aln35/SUPPORT_EPISODE_SELECTION_INTERPRETATION.md`。

### 3.3 时间读出组织

- 固定读出相对位置移 600 ms 后 DTU 损失 +0.222 [0.198,0.246]，重拟合恢复 +0.136；FAU 损失 +0.098、恢复 +0.030（SCIENCE_PRIVATE_RESULTS.md:58-61）。读出关系依赖位置，但输入是完整 1 s，不能当神经潜伏期。
- 因果滤波相对零相位在 +200 ms 使 r 下降 −0.038 [−0.051,−0.025]（DTU，CAUSAL_FILTER_BOUNDARY_RESULTS.md）。
- 私有 AP 的 early/mid 窗 AUC 高于 late 窗（+0.021，SCIENCE_PRIVATE_RESULTS.md:34-35）。
- 注意力：DTU 上 CBpre 比 local 判别 attended 准确率高 +0.020~+0.026（5/10/20 s，三 seed）；FAU 全部含 0（ATTENTION_TRANSFER_RESULTS.md）。

### 3.4 私有儿童（64 人：HA 55、NH 9）

- 当前声音 AUC 在所有方法下都在 0.55 左右：E_GX 0.553 [0.538,0.568]、CB CS 0.548、local CS 0.545，没有超过旧 EEGNet 0.556（E_MULTI_SEED_RESULTS.md:215-224）。
- FM 对 local、公共迁移、history 增量、episode、个人适配、校准都没有实际改善（量级 1e-3 AUC 或 1e-4 bits）。唯一的稳定正值是先验 AP vs XM AUC +0.009 [0.001,0.018]，但 APwrong 同样有效。
- REVE 私有 NLL 异常来自校准的自参照，LOO 后消失，AUC 不变。
- 勘误：68 条 native 私有 pre/TG 记录的 pre 输入实际全零，不能当刺激前 EEG 证据（CORRECTION_PRIVATE_PRE_ACCESS.md）。

### 3.5 听觉组与发育

- FAU：AP 相对 scratch 的风险改善 HA−CI +0.099 [0.022,0.176]；HA−TH、CI−TH 含 0。FAU HA−TH history_r +0.015 [0.003,0.026]。
- 私有 HA−NH 差异都含 0（NH 仅 9 人）。
- 年龄、佩戴时长、分期：只有 10-14 的单 seed 汇总（多数含 0）。10-17 之后的新发育/分期结果已计算但没有整理（见第 4 节）。

## 4. 已完成但还没被读过的结果

| 输出 | 内容 | 现状 |
|---|---|---|
| `results/auditory_alignment_v3/aln34/science_v2/science.json`（39 MB） | content/time 180 + 私有 current/time v2 130，2,056 个 family，含发育、时间遮罩、TG、个人适配 | 报告 NEW_SCIENCE_RESULTS_V2.md 只列覆盖，没有效应量 |
| `results/auditory_alignment_v3/aln34/prior_science/science.json`（64 MB） | 先验 300 个目标：start shift、私有 3×3 TG、arm 对比、组效应、发育模型 | PRIOR_SCIENCE_RESULTS.md 只列覆盖 |

这是目前最大的信息缺口：时间组织、私有儿童发育/分期这两个研究关切的主要证据都在这里。

## 5. 下一步建议（按优先级）

1. **整理 science_v2 与 prior_science 的效应量**（CPU，Slurm；不训练）。按研究关切出可读报告，特别是私有 current/time、发育/分期、时间遮罩和 TG。所有 family 都报告，不挑显著项。
2. **等 4 条尾巴跑完**，让证据服务生成最终 NEW_LANES / PUBLIC_BREADTH，再把规模曲线、预算加倍和 matched updates 放在一起解读。预算加倍目前的中期结果偏不利（DTU fixed 2.0 vs 1.0 为 −0.03~−0.15），需要等最终数据。
3. **一个有区分力的新 GPU 实验（建议）**：在 25%/50%/100% 源人数下比较 CB 听觉续训起点和 CB direct 起点（DTU，seed 3401，复用规模曲线代码和已有供体 checkpoint）。
   问题：听觉配对预训练能否在人少时替代人数？
   - 优势随人数减少而变大：说明共享声音结构可以替代部分数据。
   - 各人数下都接近 0：说明目前的收益主要来自本数据集内的共享结构。
   这直接对应第 3.1 节最大的未解问题，不需要扩大骨干 × 损失 × 窗口矩阵。
4. **小规模复核**：
   - 在 FAU 或 DTU 第二个 seed 上复核 local native 的 100 内步 episode 收益。
   - 用已有输出检查私有 C10/H10 仅校准变差是不是类别先验偏移（纯 CPU）。
5. **默认改用 source-side true-risk 选模**。新的有限数据训练都用 true-risk，旧 gain 只作诊断报告。

不建议现在为私有儿童再开新的 GPU 训练：所有方法都停在 AUC 0.55 附近。应先读完第 4 节的私有 current/time 和发育结果，再决定私有线的方向。

## 6. 需要你决定的事

- **GitHub 发布**：ALN3.5 和 10-19 之后的结果还没推送（远端停在 `5ef4a60`）。是否开新的发布批次？
- **存储**：A3c（43.1 GiB）、A3d（233.2 GiB）按依赖暂缓删除，列表需要重新生成后再决定。
- **V100**：预算/曲线 lane 未做 V100 检查，目前 A100 充足，不急。
