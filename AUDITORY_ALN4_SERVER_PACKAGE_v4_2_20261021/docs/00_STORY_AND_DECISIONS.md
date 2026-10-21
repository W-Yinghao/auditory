# ALN4.2：研究命题、证据结构与收束决定

本包承接已经确定的“跨听觉范式可迁移判别知识”主线，接续现有 R2，并在 R3 收束；4.2 是交付版本，不是第四轮研究。证据基准为仓库 `5d2960eee61a75c048f6b6ee3cef8427d945c3cd`。下述 R1 为已报告结果，R2 已启动事项以接手时的实际状态核对，不重复提交。[1–3]

## 一、论文真正要解释什么

**哪些刺激相关关系能够跨听者、听觉经验和任务迁移，响应的时间组织如何影响共享读出与个人适配？**

自然聆听中的连续声音监督与儿童事件识别具有不同标签空间。值得研究的学习问题是：能否从公共声音—EEG 数据学到对新听者、新刺激仍有用的判别依据，并以有限适配应对响应形式的变化。公共队列提供可核验的声音配对；私有儿童数据承担新任务、不同刺激及个体发展差异上的实质检验。它们共同约束“究竟迁移了什么”。

沿用 ALN4.1 面向 Pattern Recognition 的候选科学叙事：**学习对响应时间组织保有分辨能力、又可用少量个体数据适配的声音–EEG统计依赖，以支持跨听者和跨听觉任务的共享读出。** 人内依赖、物理时间表示和低维个人调整是其方法原则。方法贡献需要同时得到学习机制和实际用途的支持。CS 是候选实现；其优越性尚未成立。论文不能靠事后选取某个最有利指标决定赢家。[6]

## 二、研究关切、具体假设与实现工具

研究关切保持稳定：共享的是哪些判别依据，变化的是哪些响应组织，以及新个体需要补充什么信息。以下假设可以被结果改变。

- **H1，刺激相关学习：** 正确声音监督相对无 Stage2，能够增加新听者上的内容可读性；错误配对和 history 控制帮助判别收益来源。
- **H2，时间组织：** 不同时窗包含可用但读出方式可能不同的关系。保留时间标签有望减少过早池化造成的损失；跨窗固定读出与重新拟合分别检验读出复用和表征可用性。
- **H3，个人适配：** 相同少量支持信息下，时间权重适配能比普通概率校准更有效地改善独立 query。这个比较直接决定时间适配组件是否有必要。
- **H4，多用途：** 同一表示能够支持儿童事件判别、跨刺激 standard/deviant 关系复用和发展相关预测。三项用途分别评价；年龄预测不替代事件识别或跨刺激迁移的证据。

实现工具可替换：当前共同 Stage1 为可核验的 CBraMod；传统核 TCS、同条件 TNCE 和池化 GCS 提供方法比较，wrong pairing 检验对应关系。MindMix 资产可恢复性不构成科学主张，外部比较也不能简化成同骨干换 loss。现有 local、REVE、有效 CB 和传统读出各自保留其证据功能，不为补齐排行榜重跑。时间权重不是生理或行为潜伏期；CS 分数不是 Shannon 信息量。

## 三、现有证据把主张推进到哪里

ALN4.1 R1 只有一个训练 seed；区间刻画目标人群条件于该已训练模型的不确定性，不包含所有源训练随机性。[1,4]

公共 history-residual envelope 上，TCS−B0 在 FAU 为 +.018，区间 [.009,.027]；DTU 为 +.003，区间 [−.006,.012]。声音训练的收益目前具有队列差异。TCS−TNCE 在 DTU/FAU 分别为 −.034/−.012，区间均低于零，因此当前内容证据支持 TNCE。TCS−wrong 两队列明确为正，但 wrong 本身低于 B0，不能把整个差值算作正确配对收益。

TCS 相对 GCS 的 FAU 内容结果为正，支持继续检验保留时间标签的价值。TCS 的跨窗重拟合恢复较大，同时也可能意味着固定读出失配更大；必须联合同窗性能、固定迁移损失和恢复判断，不能单独称为时间优势。群体权重近乎均匀，也不能直接诊断 KL 过强或个人适配无效。[1]

儿童充分微调 AUC 为 B0 .535、TCS .537、TNCE .538，差异未解决；history 增量也尚不明确。年龄上 B0 MAE 25.05 月，优于 raw/训练均值约32月，但没有明确 Stage2 增益。它支持通用 EEG 表征的儿童用途，不支持声音训练已经促进发育建模。年龄、HA 与设备时长的同时关联检验尚未分辨出可靠差异。[1,4]

另一个待解释事实是：TNCE 源 query loss 长期接近 ln32，而公共内容读出改善；高维 source ridge 的 dev 误差又劣于均值。用已有 checkpoint 核读配对 margin、支持适配幅度及读出泛化，区分优化、读出和迁移现象。参数改变不能证明预定关系已学好；具体实现故障可以修复，有限值弱结果继续保留。[1]

## 四、五张科学主图各承担什么论证

| 主图 | 要回答的问题与证据角色 | 结果如何改变主张 |
|---|---|---|
| **图1：刺激相关关系的学习与共享** | 公共内容及 history-residual 读出、正确/错误配对与 B0 对比，并列儿童 history/twin 证据；给出共同方法示意。旧有效 local、CB、REVE 结果按原合同进入参照面板。[1,4–6] | 正确配对相对 B0 的收益才增加刺激监督价值；只有相对 wrong 的优势不够。TNCE 更强则保留该结论。 |
| **图2：时间组织如何改变读出** | 展示三窗固定读出、同窗性能与重拟合恢复；旧局部时间探针和成分迁移结果提供独立证据。旧细时间尺度与新400毫秒窗分别标明，不混算。[1,5,6] | 固定迁移成功支持读出复用；重拟合成功支持目标窗表征可用；两者均弱则缩小时间方法主张。 |
| **图3：新个体究竟需要怎样的适配** | 同一 query 上比较 U0/U10/U30 的时间 δ 与 affine 校准，并展示个人差异及预定 HA/年龄关联。主适配端点为 NLL，Brier/AUC 为补充；支持量沿用合同含义。[2,6] | δ 超过普通校准才支持时间适配必要性；affine 通常不改变排序，不能仅凭 AUC 宣称超越校准。若 TNCE 同样受益，贡献属于共同时间接口。 |
| **图4：儿童跨刺激判别知识** | 固定 puretone→bapa 的 standard/deviant 语义，比较源刺激读出的直接迁移与目标训练侧重拟合，并保留 history 控制。[3] | 直接迁移支持判别关系复用；仅重拟合有效支持表征可用。共同标签名称本身不保证声学或历史结构相同。 |
| **图5：儿童发展信息与实际用途** | 年龄 OOF 预测比较 B0/TCS/TNCE、raw 和均值，说明表征中的发展相关信息；公共 attention 与一个忠实外部方法检验应用价值。[1,2] | 年龄增益归属实际产生它的阶段；attention 改善须相对 B0。20秒证据积分不解释成响应时间，年龄预测不解释成听觉发育机制。 |

五图是证据的论证位置，不要求每图都有阳性结果。旧 local/REVE 说明已有可读内容、时间变化与可迁移成分是否真实存在；新增方法负责证明这些发现能否转化成更有用的学习原则。合同不一致的旧结果单独呈现，不拼接成新的方法排名。继承证据账本已标无效的 all-zero `pre` 和受影响 TG 单元继续排除，有效条件保留。[5,6]

## 五、R2 接续与 R3 收束的决定

完成现有两个种子的既定 R2，不因 R1 的 CS/TNCE 顺序改变主要端点。下一步最有信息价值的比较是“时间 δ 是否超过普通校准”，以及已经固定语义的儿童跨刺激迁移。二者分别决定个人适配与跨范式判别关系的主张；年龄和总体 AUC 提供用途证据，不能替代这两个问题。[2,3]

不因群体权重接近均匀自动启用“去 KL”消融。先使用既有输出判定个人 δ 是否更新、是否改善独立 query；唯一可选消融应服务于仍未区分的中心机制，不能成为寻找阳性的续跑入口。R3 完成一个忠实外部听觉比较并汇总，保持原有轮次和预算。

三轮结束时，CS 若没有比较优势，就取消其优越性主张；时间适配若没有额外收益，就取消其必要性主张。成立的内容、迁移及儿童用途结果仍保留。若只有 Stage1 年龄预测有效，它不足以证明跨听觉范式判别迁移；这时应据实判断方法贡献是否足够，而不是另造负结果主线或继续增加模型。

## 证据来源

下列链接固定到基准 SHA；服务器当前运行状态由接手记录更新。

1. [ALN4.1 ROUND1_REPORT.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/docs/auditory_alignment_v3/aln41/ROUND1_REPORT.md)。
2. [ALN4.1 R2_PLAN.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/docs/auditory_alignment_v3/aln41/R2_PLAN.md)。
3. [R2_CROSS_STIM_DECISION.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/docs/auditory_alignment_v3/aln41/R2_CROSS_STIM_DECISION.md)。
4. [ALN4.1 R1 FAMILY_TABLES.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/results/auditory_alignment_v3/aln41/r1/FAMILY_TABLES.md)，同目录 `contrasts.json`、`person_results.csv`。
5. [ALN3.6 R1_SCIENTIFIC_DECISION.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/docs/auditory_alignment_v3/aln36/R1_SCIENTIFIC_DECISION.md)、[R1_BINDING.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/docs/auditory_alignment_v3/aln36/R1_BINDING.md)及[ALN3.6 R1 FAMILY_TABLES.md](https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/results/auditory_alignment_v3/aln36/r1/r1_final/FAMILY_TABLES.md)。local/REVE 等更早结果的逐项数值和可比合同由本包证据索引绑定；本文件不补造其结果。
6. 恢复的 ALN4.1 原包 `docs/01_RESEARCH_AND_EVIDENCE.md`、`docs/04_ROUNDS_AND_OPTIMIZATION.md` 与 `evidence/evidence_ledger.json`（E01–E08，旧快照 `3da8cf5758214c0cf87a1f1c8d67fb84b574000e`）。旧内容/时间证据可核对 [SCIENCE_PRIVATE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/SCIENCE_PRIVATE_RESULTS.md)与[SCIENCE_V2_READOUT.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/SCIENCE_V2_READOUT.md)。历史状态不视为当前执行状态。
