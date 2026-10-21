# ALN4.2完整server交接正文

编制日期2026-10-21 UTC。本文由本包启动指令和8章设计正文逐字合并；机器计划与原ALN4.1完整包另附。

---

来源文件：SERVER_START_PROMPT.md

# 给 server 的完整启动指令

请在现有 W-Yinghao/auditory 项目上接续执行本 ALN4.2 包。研究者本次授权的目标是：围绕既定 Pattern Recognition story 完成下一轮必要工作，并在总共三轮内结束。请读完 SERVER_FULL_DOCUMENT.md 与 plans/*.json，再落实接包绑定；不要把版本号 4.2 当成新增第四个研究轮次。

## 一、沿用的研究判断

核心问题仍是：哪些刺激相关关系可以跨听者、听觉经验和任务迁移，时间组织如何影响共享读出与个人适配。保留内容成分、history/twin、时间泛化、HA/CI/TH、年龄和不同刺激的已有有效结果。CS 是主要候选，匹配 TNCE 是实质竞争者；使用已发表传统核 CS，不使用 VCS-QMI。Stage1 本轮已冻结为 CBraMod，不重开 MindMix Stage1 资产选择。

本包不是以“适配失败”为新主线，也不保证 CS 获胜。支持哪个具体假设由相应直接比较决定。儿童数据负责事件历史之外的声音证据、个人支持、跨刺激判别读出以及年龄相关信息，不能变成装饰性外测。

## 二、先完成接包核对，并继续已授权的现有任务

1. 读取当前 AGENTS.md、服务器交接文件、R1/R2 冻结计划及 receipts，查看 live Slurm 状态与工作树。本包的 GitHub 观察基准是 5d2960e；实际 HEAD 若更新，比较关键依赖，不强制 checkout/重置，不覆盖在跑代码。
2. 运行 tools/verify_package.py。tools/inspect_existing_state.py 只生成只读检查记录，不会提交作业；其结果不能代替 live queue 和结果 receipt。
3. 保存 templates/INTAKE_AND_BINDING.template.json 的实际填写版，含当前 repo SHA、原计划完整 hash、已完成/运行/缺失单元、权重/表示/人群/query 身份、外部方法旧决定、诊断新增量。所有未知占位值先解析，不能把本包示例当实际路径或实际 hash。
4. ALN4.1 R2 和 ALN3.6 R2 按原计划继续；复用完整且依赖一致的产物。R2 已完成也不重跑。有效低分、负效应和不确定结果保持有效状态。
5. 新增内容在独立 aln42 命名空间实现；原生产文件保持原样。允许在已授权范围内完成 adapter、最小有效测试、CPU 汇总及有界 frozen forwards，不需再因同一工作询问研究者。

## 三、本包新增工作按以下顺序落实

A. 立即并行做两项有效性检查（不阻断无关的有效 R2 工作）：
- 现成 source checkpoint 的学习诊断：docs/03，固定 0/2500/5000/10000，不按结果换 checkpoint；所有四个 Stage2 臂同一面板。
- 私有事件/history 定义追溯：docs/04，先做适用全队列的定义检查，再解释已识别的异常序列。原始身份与事件行留服务器。确认错误才版本化修正受影响依赖。

B. 完成已冻结 R2 的关键科学读出：
- F_SUPPORT：相同 support/query 的时间 δ 对比正斜率 affine 校准；保留 U0/U10/U30、20 项原 family、NLL 主端点。
- F_CROSS_STIM：只做已定 pure-tone→bapa，原 13 项 AUC family 和 history 描述家族；保持身份排除、训练侧 PCA/标准化/校准和 refit 规则。
- 输出 EC 与 ET 相对 E0 的个人净收益，不能把 GC 正值直接叫整体个人适配改善。新净收益分析标为看过 R1 后设计的诊断；不替换原 family。
- 合并全部预定 seed，每人先 seed 平均再人口推断；原统计家族和每 seed 结果均保留。

C. R3：
- 读取 R1 已固定的 EXTERNAL_SLOT_DECISION；依既定工程就绪规则执行一个外部方法席位（MindMix发布的完整架构在共同协议上的任务适配，既定fallback为Transformer-CLIP原生回归读出族）。两者不按新测试成绩择优，不把 EEG-only 初始化叫完整 MindMix。
- 公共主任务沿用 DTU 20 s attention 的共同合法 query、原身份/内容排除、候选双顺序规则和原聚合。精确 adapter 与作者配方在任何新测试分数前登记。核对DTU44与论文DTU18的身份差异、真实音频和盲候选评分；不得把本项目任务适配叫作者原协议复现。默认不增加儿童外部 FT。
- 输出五张问题驱动主图、逐人/逐 seed 表和方法主张判定。复用旧 local、真正 full CB、代表 REVE 与有效声音成分/时间结果，不追加全交叉网格。

## 四、计算和修正规则

- 新诊断最多 4 A100 等效 GPU 小时、0 optimizer updates；若无法直接估算，先用一个固定单元计时，调 microbatch 而不改科学对象。超出预算时保存已完成部分和成本，不悄悄扩量。
- R3 外部席位固定一个发布模型、下游 seed3401；DTU44 的2个content folds×5个人folds共10个公共下游拟合单位。完整MindMix路线最多10个Stage3 fits，Transformer-CLIP fallback为10个冻结表示读出；两路互斥，新source pretraining/儿童外部FT均为0。先登记真实训练次数，精确上限见 plans/round3_closure.json。
- 原 R2 训练不计为本包新增量，但必须计入项目同时占卡；running+pending 总上限 10 张，保留已有 GPU 路由和 P100 排除。已知 node51 故障排除继续有效，除非有独立硬件修复回执；不自行清 holds 或调用 scontrol。
- 对真实 bug，输出 BUG_SCOPE_RECEIPT，列出错误字段、依赖 DAG、受影响 IDs、无关结果和唯一替代版本。不要直接改在跑源码或批量取消无关作业；若某错误已证实影响仍在执行的同一任务，按项目既有精确 job ownership 流程处理该范围并保留原 receipts。
- 仅弱效应、有限收敛、低表示 rank 或近均匀门控，不是自动重训/加预算的理由。

## 五、交付与停止条件

交付 docs/07 中所列研究报告、机器可读结果、诊断与依赖收据，完整记录未通过就绪/缺失/有效负结果。不用日志数量或成功退出码代替科学完成度。原始 EEG、身份表、原始事件行保持私有；既定去标识个体结果授权继续有效，不再次询问。公开推送沿用当前用户授权与项目发布流程；本包本身不等于自动新增推送许可。

当原 R2 有限工作、一个外部席位（完成或有具体不可复现证据）、必要有效性处理和证据整合完成，进入论文写作收束。保留 CS 能被直接证据支持的主张，删除未获支持的必要性或优越性主张。不得自动增加第四轮、多个新方法或新的调参网格。

执行结束先用科学问题回答研究者：共享了什么，时间读出改变了什么，个人支持实际改善了什么，儿童跨刺激/年龄各提供了什么，CS 的额外贡献是否成立；工程状态放在其后。


---

来源文件：docs/00_STORY_AND_DECISIONS.md

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

---

来源文件：docs/01_EVIDENCE_BASELINE.md

# 1. 设计基准与当前证据

## 1.1 信息来源和时点

2026-10-21 本次制作时已通过 GitHub 页面重新读取 main；HEAD 仍为 5d2960eee61a75c048f6b6ee3cef8427d945c3cd。主要实验发布为其父提交 20592b0bd6213fb6b0e2ef667f8d225dcff2a778。已完整阅读两轮 R1 报告、两套 R2 计划、cross-stim 决定和两份 FAMILY_TABLES；source.py 已抽查实际音频/裁窗与更新循环。没有接入 live Slurm、私有数据和权重，没有本地复跑报告的人级统计。所有进度在 server 接包时刷新。

权威路径（相对上述 repo）：
- docs/auditory_alignment_v3/RELEASE_035.md
- docs/auditory_alignment_v3/aln36/R1_SCIENTIFIC_DECISION.md、R2_BINDING.md
- results/auditory_alignment_v3/aln36/r1/r1_final/FAMILY_TABLES.md
- docs/auditory_alignment_v3/aln41/ROUND1_REPORT.md、R2_PLAN.md、R2_CROSS_STIM_DECISION.md
- results/auditory_alignment_v3/aln41/r1/FAMILY_TABLES.md

下列数值是已经看到的 R1 结果，不能把据此选择的新问题称为未见结果的验证设计。R1 单 seed；人级区间条件于当前训练好的模型。

## 1.2 结果怎样改变假设

| 对象 | 已有证据 | 对下一轮的具体影响 |
| --- | --- | --- |
| HA 完全组外固定读出 | 本研究训练/标准化/选择/读出不含 HA；local G0 +.00173 [.00058,.00288]，CBpre +.00233 [.00139,.00327]，单位 MSE | 保留为共享关系的核心证据；R2 复制。这里不宣称 CB 通用预训练一生从未接触 HA |
| CI 与 TH | G0 不确定；CI 旧 pooled 同样 near 0 | 不把“未参与训练”作为 CI 空结果唯一解释；不推无信息，也不由各组显著性差异推出组间差异 |
| 时间个人更新 | 公共各组 DT=R(EC)−R(ET) 为负，约−.006至−.012，同时区间排0 | 固定复制并检查 support→query 泛化；不扩大 λ/窗 grid 救援 |
| 个人尺度项 | HA/DTU 的 GC=R(HP)−R(EC)>0，而 GH=R(H0)−R(HP)<0 | 新增 NET_C=R(E0)−R(EC) 的直接配对结果；GC 不代表净个人收益 |
| TCS−B0 内容 | DTU +.00288 [−.00628,.01204]；FAU +.01769 [.00874,.02664]，history-conditional r | CS 在 FAU 有局部增益；不称跨队列普遍优势 |
| TCS−TNCE 内容 | DTU −.03379 [−.04442,−.02316]；FAU −.01222 [−.02176,−.00269] | TNCE 是有实质证据的竞争者，原样复现 |
| TCS−GCS 内容 | FAU +.03427 [.02169,.04686]；DTU不确定 | 时间标记构造有部分依据；不等同已学好个人时间组织 |
| TCS−wrong | 两公共队列明确正，wrong本身低于B0 | 不能把全部差异归因正确配对训练的收益 |
| 源任务学习 | TNCE约step200后loss近ln32；群体q接近均匀；共同LR probe dev NMSE>1 | 用真实mask基准/投影与原tokens/δ/梯度做固定checkpoint诊断；不直接宣告数据无信号 |
| 儿童事件 full FT | B0 .535、TCS .537、TNCE .538；TCS−B0 .00239 [−.00517,.00994] | 未证实Stage2新增用途；保留完整预算和旧有效结果 |
| 儿童年龄 | MAE B0 25.05、TCS25.37、TNCE24.90，raw32.38，mean32.02月 | 年龄用途有效；当前新增收益不属于Stage2/CS |
| DTU attention | TCS/B0约.626；TCS−TNCE+.02884 [.00221,.05547] | 内容与候选判别不是一个终点；不能把胜TNCE写成胜B0 |
| 私有history异常 | 一名儿童的事件规律使H0极端失配，一个机制family临界值159.7 | 先核查原始定义与依赖，不靠剔除个体或换区间获得阳性 |

数值完整版本见上述固定提交原表；本表不能代替逐人 CSV。FAU/DTU MSE、r 与私有 bits/trial 分开，不拼成一个“统一信息量”。

以 FAU HA CBpre 已公布均值为例，NET_C=−.00604+.00243−.00233=−.00594；这只是均值恒等式推算，新的 CI 必须从同人同 query 风险构造，不能从旧 CI 相减。

## 1.3 有效历史证据的保留

inherited 的原包和 evidence/inherited_aln41_evidence_ledger.json 保留旧 SHA 与证据归属。历史主线包括六类声音成分及历史残差、固定跨窗损失与目标窗重拟合、有效 local/真正全量 CB/代表 REVE、AP−S/AP−XM/APwrong、严格 twin、支持预算与 episode 交互。它们继续承担科学论证，不因新 wrapper 出现而降为“预实验”。

必须继承的更正：
- +.009193 是 AP−XM，不能写成 AP−S。
- 旧全零 pre 输入的 local/E_PUBLIC_TRANSFER cell 无效；真实有 pre 输入的 FM 和有效 post 不连带作废。
- “儿童信息只在0–400ms”超过已有部分 FM 400–600ms 有效读出的支持范围，不沿用该笼统表述。
- 旧1秒访问窗、严格20/40ms raw参考与新400ms窗的物理访问不同，不能作同合同差值或神经潜伏期。
- ALN3.6 给旧 ALN3.5 history描述增量补出的区间跨0：不能继续把旧描述均值称为已明确的刺激特异增益。
- 原包旧 D2/GX 未完整取回的状态已被 ALN4.1 R1 intake 更新：MFF12.50是单seed线性或4seed RBF；4seed线性12.97。G1/H的train模式bug未重跑；D1数组已删除而GX staged arrays仍在。复用时以原始来源和勘误核验为准。

这些历史结果不与新 R2 合并为更多受试者、更多独立重复，也不触发整套历史重训。


---

来源文件：docs/02_EXECUTION_AND_BUDGET.md

# 2. 执行顺序、既有任务和成本

## 2.1 本包接到正在运行的第二轮上

| 工作流 | 已冻结范围 | 本包动作 |
| --- | --- | --- |
| ALN4.1 R2 | seed3407/3413；4 source臂×2=8；core3×5fold×2=30 private CE；non-B0 frozen20×2=40 | 保留原 unit ID、LR1e−4、stream/panel规则、final10000；完成的依赖一致单位直接复用 |
| B0 frozen | R1 seed-free基线，PCA seed3437 | 沿用既有复用；不得为了凑3seed复制成3次独立观测 |
| F_SUPPORT | core3×全部3seed，既定20成员family | 完成原计划，增加明确净收益解释和δ诊断导出 |
| F_CROSS_STIM | B0+TCS/TNCE各3seed=7次frozen extraction；pure-tone→bapa | 完成原计划与13成员family，声明refit完整流程和训练覆盖 |
| ALN3.6 R2 | seed3407，12 FAU整组source、52公共feature banks；匹配AP/APwrong供体及target | 完成原绑定；旧 pooled parents 和已完成同依赖资产不重训 |
| ALN3.4 尾巴 | 发布时DTU budget剩1、breadth curves剩18 | 接包刷新队列；不以这些数值重新提交任务，也不新增旧探索线 |

一次训练可产生多个评估格；不要按表格格数计算训练量。已有任务属于原合同，不因新包改名或重新计费。R2里已看到的新结果也保留，新增诊断标注设计时间。

## 2.2 优先级

P0：只读 intake / 原计划身份与代码绑定；核实依赖并继续原有效队列。  
P1：源学习诊断和儿童事件定义核验，两者可并行，优先 CPU / frozen forward。  
P2：完成原 R2 主结果、F_SUPPORT、F_CROSS_STIM；并行完成旧结果证据归位。  
P3：完成 R3 的一个外部比较席位和最终科学图表。  
P4：最终研究判断、方法说明、结果覆盖与资源账本。

工程问题只影响实际依赖其错误字段的任务。不能因一个family的CI问题停止无关公共训练。若真实错误使一项仍在跑的任务目标/标签无效，按既有job所有权规则处理精确范围并保存旧版本；禁止仅因弱分数取消任务。

## 2.3 新增预算

| 新增项 | 上限 | optimizer更新 |
| --- | --- | --- |
| source诊断 | 固定fit32+dev32 episodes，每episode原2人；4arms×4既有snapshots；合计最多4 A100等效GPU小时 | 0 |
| private事件审计、净风险、图表与coverage | CPU；复用已有预测与元数据 | 0 |
| R3外部方法 | 一条已固定路线；一个发布checkpoint、下游seed3401；DTU44的2content×5person=10公共单位 | MindMix最多10个Stage3 fits，或Transformer-CLIP的10个冻结表示线性读出；两路互斥 |
| 新儿童外部full FT | 本版未启用 | 0 |
| 方法消融 | 本版未启用（原合同单一槽仍记录为未用，不转移预算） | 0 |

原R3只占一个外部席位；本版根据实际公共代码明确10个下游训练单位，source pretraining为0、儿童外部FT为0，不运行被试内44×5=220个模型。完整MindMix有合法原始输入与盲候选评分时保留其Stage3训练；fallback沿用Transformer-CLIP冻结encoder的原生回归用途。两条都标明共同协议任务适配，不用缩减作者阶段冒称复现。参见docs/06及机器计划。

4 GPU小时是诊断预算上限，不是效果门槛或完成时间承诺。预估首次固定单元的实际秒数与显存，再确定microbatch；人内Gram和32anchors不拆成不同估计。IO与CPU时间另报。缺checkpoint时报告实际缺失，不重训补checkpoint、不择优改选snapshot。

项目 running+pending 合计10GPU不变，原ALN4.1优先级不变。使用Slurm、现成硬件兼容规则与精确作业所有权；node51已排除，P100不使用。不得在主节点直接启动未登记GPU训练；不修改正在运行的源码。

## 2.4 实施文件的边界

本包工具是数据合同校验与数学参考，不伪造生产CLI。建议新建服务器模块 auditory_alignment_v3/aln42/ 下的诊断/导出/报告层，具体函数由现成接口适配，实际新增文件名和调用在binding中记录。

必须提交的实现收据：导出器源hash、父模型/源计划hash、完整panel IDs私有hash、软件版本、所读checkpoint列表、没有optimizer.step的检查、同query对照重现误差，以及每个结果的实际覆盖。

旧生产source/frozen/private_ft/support/cross_stim模块在未确认bug时保持字节不变；新增诊断从它们调用相同的模型、采样、crop和objective接口，不重写一套相近的训练定义。


---

来源文件：docs/03_SOURCE_LEARNING_DIAGNOSIS.md

# 3. 有界源任务诊断：确认声音依赖和时间适配实际发生在哪里

## 3.1 问题与范围

R1中TNCE的投影空间query loss接近随机基准，冻结backbone的公共内容读出却更好。TCS的群体q近均匀，不能直接推出KL过强、数据无信号或个人时间组织相同。本节用已有checkpoint区分：表示学习、投影头退化、弱配对学习、个人支持是否作用，以及共同probe是否失灵。

这是看过R1后指定的机制诊断，不改变原生产训练、选模或主统计。不更新encoder/projector/群体a或写回checkpoint；允许原每episode的临时δ五步与每snapshot固定probe的训练侧ridge求解。这些不是新主模型训练。没有按下游分数挑checkpoint，没有自动去KL。

## 3.2 冻结面板

- 模型：TCS、TNCE、GCS、TCS_WRONG；seed3401为主诊断。已有其它seed只导出原日志和最终小结，不把64episode全诊断扩成三倍。
- checkpoint：0/2500/5000/10000；初始同一状态可以哈希去重，但每臂必须关联其准确初始身份。
- fit panel：原production stream的前32个episodes（每episode原两人、每人S32/Q32）。完全复用 rows、off、wrong、packed keys。
- dev panel：复用原source-dev pool，使用同采样/guard规则生成32个episodes，固定seed348201。构造时不看任何分数；若某dev人没有3个各≥22合法segments的family，记录结构性覆盖，不从结果选择人。优先用现成sampler的明确eligibility；若全dev无法满足，保留可行覆盖并报告，不改N和family数来伪装同合同。
- dev与fit的人/内容排除继续执行；S/Q物理访问、三个native crops、固定audio heads、sigma与wrong permutation均沿用真实生产定义。
- private target / DTU / FAU test 不参与诊断调参。固定当前已有512fit/512dev LR probe的样本与hash，原λ不变。

保存panels.json、实际完整hash与可行人数。不同snapshot/arm使用同一合法面板。主诊断model.eval()、启用需要的autograd；采样RNG、dropout设置明确，不能拿eval损失逐值冒充历史train-mode损失。必须复核日志时，仅另用固定前2个fit episodes在独立clone上记录train-mode参考；不写回任何权重或BN状态。

## 3.3 必须导出的四层信息

### A. 声音配对是否变得可辨

每person、view(env/ss/sc)、slot、split(S/Q)、snapshot：
- 实际positive/exclusion masks、合法正例/负例数量、真实N；
- 正例与合法负例score均值、同mask下的检索分数；三view分别报，不能仅用平均遮住一个view；
- TNCE的每slot loss与真实mask均匀score基准；
- TCS的log_A_slot/log_B_slot/log_C_slot、q及归一化q²、原混合CS分数；GCS用自己的pooled sigma和pooled norm。CS Gram不引入NCE排除mask。
- TCS_WRONG首先用其注册wrong音频配对重现训练目标，另以真实配对做共同只读probe；必须区分这两种评价，不能混列。

NCE均匀score损失应为
L_uniform = 1/2 * [mean_i log(n_allowed_row_i/n_positive_row_i) + mean_j log(n_allowed_col_j/n_positive_col_j)]。
只有每行每列各1个positive且32个allowed时才是ln32。正例是分子log-sum-exp，不是将多正例CE简单平均。

tools/source_probe_metrics.py 可读规范化NPZ并算上述共同NCE统计与表示rank参考；它不替代生产CS目标，CS值直接调用原temporal_objectives_torch.py。helper字段中的supplied_nce明确是所输入S或Q上的共同NCE诊断，split与native/correct配对身份由export receipt提供，不能把S命名为query或将CS臂的NCE诊断当原CS目标。原objective的nats和下游预测risk的bits/trial不得混为一个MI。

### B. 改变发生在投影头还是backbone

对同一面板，分开保存：
- 原始channel-aware、slot有序的backbone tokens（仅私有诊断缓存）；
- 各view的投影向量；
- 固定音频向量。

导出中心化方差、有效rank、off-diagonal相似度、norm分布，以及与step0的相同输入差异。effrank应注明定义exp(entropy of normalized squared singular values))；近零方差时标退化，不编造“信息为0”。raw tokens与projected features不得互相代称。

使用原512fit/512dev token→audio ridge probe，同时给fit NMSE和dev NMSE、有效rank、原λ与fit/dev预测均值。每个snapshot在相同fit面板上重新求该snapshot的ridge系数，dev只评价；不跨snapshot复用某套读出系数，否则测的是坐标漂移与读出复用，不是各snapshot线性可读性。它仍是原读出；不因其过拟合另搜PCA维数/λ再改LR或生产checkpoint。若要解释它为何失灵，条件数/训练误差/平均预测已足够构成有界诊断；本包不新增一个调优probe。

### C. 时间权重和个人支持是否有作用

同一query、同一模型、同一view同时算：
1. q_uniform；
2. q_prior=softmax(a)；
3. q_support=softmax(a+δ)，δ仅从本episode的support取5步后得到。

记录source prior、每episode δ、各步support原目标/含penalty目标、query原目标三条件。目标方向统一：NCE loss越低越好，CS score越高越好，汇总时显式转换为risk改善。delta非零不是query收益；q_prior均匀也不排除q_support个体差异。

在相同前2个fit/dev episodes上，严格按原first-order outer目标测a的数据梯度 ∇a L_Q(a+stopgrad(δ)) 与 ∇a[0.01 KL(softmax(a)||U)]（L2范数、逐slot向量、cosine；零向量时null）；两项使用相同的生产view/person reduction，不能用q_prior或单view数据梯度替代。并导出projection/backbone梯度范数。对encoder/projector/群体a不调用optimizer.step；临时δ仅在S上完成原五步后丢弃。若data梯度近零，不能仅靠去掉KL宣称可学；若KL确实相对数据项占优，也只形成机制线索，本版不启动消融。

### D. 历史报告的复现边界

确认 source.run_unit 的query projection保留梯度、support detach、a在optimizer组、delta每episode重置；不把仅一次首步“有梯度”当持续学习证明。检查实际sigma、temperature和normalization不是仅凭配置文件名。

用于源diagnostic的全部forward必须在现成checkpoint上，记录读取而非写回模型的receipt。不同源码修复前后分开版本，原R1有效结果不被静默覆盖。

## 3.4 解释出口

- backbone读出改善、projected pairing仍弱：可以报告表征改变及目标空间尚未辨明，不能写已证明CS/InfoNCE学到特定生理机制。
- support目标改善而query变差：这是该个人更新的泛化问题，继续保留为科学结果。
- 原probe过拟合：限制的是该LR判据的解释，不是“EEG没有声音信息”的证据。
- finite低rank或近均匀q：有效结果加diagnostic flag；不触发重训。
- 真实错位、mask错误、double resampling、无梯度或错误权重：输出BUG_SCOPE_RECEIPT并按实际依赖定点修复；不能混入原seed平均。
- 最终snapshot缺失：明确标缺失，不用测试分数选择其它snapshot代替主模型。

输出 SOURCE_LEARNING_REPORT.md（按四个问题回答）、source_probe_person.jsonl、source_gradient_audit.json、panel/代码/checkpoint哈希与coverage。先读这个报告，再对source机制下结论。


---

来源文件：docs/04_PRIVATE_SUPPORT_AND_CROSS_STIM.md

# 4. 私有儿童：R2 接续、事件核验与 R3 收束

## 4.1 执行范围与原注册优先级

本章接续已经注册的 ALN4.1 R2，不创建研究第四轮，不重新启动已经完成或正在运行且合同一致的 R2。研究问题仍是：共享 EEG 表示中的听觉判别关系可复用到什么程度，目标范式或新儿童需要改变什么，以及这些关系与已有的发展信息怎样并存。

继承依据为 ALN4.1 包的 `docs/04_ROUNDS_AND_OPTIMIZATION.md`、`05_DOWNSTREAM_AND_PRIVATE_ROLE.md`、`06_ANALYSIS_AND_REPORTING.md`，以及服务器已注册的 `R2_PLAN.md`、`R2_CROSS_STIM_DECISION`、`auditory_alignment_v3/aln41/support.py` 和其原计划。ALN4.1 原包 SHA256 为 `eb9b343beb81994bf564a81b65577f0160547005a162db7894766e36e7971b2c`。支持计划已知位置为 `private/auditory_alignment_v3/aln41/support_v1/plan.json`，已知哈希前缀为 `3ed2b6f5`；**完整哈希必须从原资产读取，不能根据前缀补造**。

本包编制时母会话最近核对的 GitHub HEAD 短码是 `5d2960e`。这里不证明服务器作业、私有缓存或 R2 完成状态；执行时按本包 intake 取得完整 commit、现有 job/output、原计划及哈希。历史本地 checkout 不能代替最新服务器状态。原计划与本文存在实质差异时先输出差异和受影响范围，保留原结果，不用本章静默重写已注册估计量。

首先生成 `R2_REUSE_INDEX.json`，逐原 unit 登记 `original_unit_id/original_result_keys/arm/seed/fold/plan_hash/code_commit/input_hashes/output_hashes/status/action`。行动只有：复用合同一致的完成件、等待同一正在运行的 unit、接续原注册尚未完成的 unit、或进入已确认 bug 的定点修复。不得仅因报告格式不同而重复训练或提取特征。

## 4.2 优先完成事件与历史核验

### 4.2.1 核验对象与顺序

把服务器内部代号 `child60` 所指的事件问题提前核查；代号仅用于已有私有资产定位，不写入公开事件追踪。它是审计起点，不是按模型低分筛选的排除对象。先对所用事件生成器、代码映射和历史算法做全队列一致性检查，再在该对象上核对原始链条；是否扩大逐事件追踪由共用代码和资产依赖决定，不由其他儿童分数决定。

执行以下只读核验，先保存原输入与派生资产的哈希，原文件不覆盖：

1. **恢复完整刺激流。** 从原始事件/annotation 与实验记录读取全记录事件索引、原始码、原生 sample/onset、物理 block、刺激/非刺激事件身份。保留未成为 accepted EEG epoch 的刺激；EEG QC 丢弃一次试次不等于该声音没有发生。缺完整流时明确 `UNRESOLVED_PROVENANCE`，不能用保留下来的 epochs 冒充完整刺激历史。
2. **核对原始码到当前标签。** 对每个 accepted epoch 追踪原始事件索引、当前 `y`、映射版本及可由原始记录支持的角色。`standard→0/deviant→1` 的注册规则不因预测方向改变。文件名、派生容器及推定语义分别标注证据级别；没有音频就不补造波形或声学属性。相同采样点重复码、未知码、缺失触发均保留并按已有协议解释。
3. **先取 event-before-history，再更新当前事件。** 试次 i 的历史只能使用其之前真实发生的刺激。核对 previous event、last deviant、since-last-deviant、history bin、时间间隔与 block/reset 规则；逐行比较 stored history 与从完整流重算的 before-event history。当前标签不能进入自身历史。block 内重置还是跨 block 延续必须来自协议/原注册，不能为解释某个结果临时选择。
4. **核对对齐与实际样本。** 将 epoch 对齐索引反查原始触发，验证采样率、epoch 起止、被保留 trial 行序及三槽 `[-200,200)、[0,400)、[200,600) ms` 的原生样本支持。以真实400ms crop重采样再padding；padding不是新增EEG。无法校准声学 onset 时仍以触发为零点，不把解码时间称神经潜伏期或行为反应时。
5. **核对完整 block guard。** 复核原 fit/ES/support/query 角色、被删除边界 trial、原始 onset 及完整 `[-0.2,+0.6)` epoch 的 sample access。必须满足保留 support 末端不晚于第一个 query 起点；不得只用某个短槽的范围放宽既有完整 epoch guard。
6. **核对实际序列协议。** 输出每 block 的 standard/deviant 数、实际出现率、deviant 间距、可用 SOA 摘要、历史 bin 支持度、重复/遗漏码和协议偏离。区分“代码未遵循原始事件”与“事件本身遵循另一种实际序列”。真实分布失配是研究结果/适用范围，不是标签 bug；仅分数异常不足以判定错误。

身份对应表、原始事件码逐行轨迹、绝对/精细时间、record路径和原始标签链只保存在私有审计根。`schemas/private_event_trace.schema.json` 定义私有追踪格式；通过 schema 只表示结构合规，不能替代上述语义核验。公开输出只包含匿名验证摘要、影响范围与校正说明，不包含逐事件追踪或真实身份对应。已授权的去标识个人模型结果继续按原 scope 公开，无需再次询问。

### 4.2.2 修复分级：按依赖决定，不能一律重跑

| 核验结论 | 行动 | 允许重新计算的范围 |
|---|---|---|
| 原码、y、对齐、历史均一致；实际序列/设备条件不同 | 保留结果，登记真实分布失配；解释条件化结果 | 已有预测的CPU摘要，不改变主要人数或family |
| 仅history字段/顺序错误，y、epochs、训练与评价roster不变 | 新版本重算history、其训练侧B1/offset、strict twin及依赖汇总 | 仅相关CPU拟合/导出；source、private CE和无依赖age缓存复用 |
| y或EEG/event对齐错误 | 先冻结原版本并建立数据→特征→checkpoint→选模→预测的依赖图 | 只重算受影响版本；若错误进入训练/ES，相关fold训练或checkpoint选择才需要重做；纯测试标签错误不自动重训模型 |
| 完整流/映射无法恢复 | 标记未解决的来源限制，保留已有效的其他部分 | 不凭模型输出猜正确标签，不用新筛选规则得到更好结果 |

历史字段可能曾参与 `since_last_deviant>=0` 的 trial 筛选。故“仅history修复”必须证明原训练roster、归一化输入与角色不变；默认不扩充既定query。如果历史错误曾改变训练输入，须在依赖收据中准确列出，不把有训练影响的变更伪装成单纯报告修正。

所有确认修复须生成 `PRIVATE_RECOMPUTE_SCOPE.json`：bug证据、旧/新代码与数据哈希、保持不变的资产、受影响的原unit/seed/fold/endpoint、是否影响训练/选模、重新计算资源、替代关系与理由。只暂停依赖该错误的结论，不全局阻断无关R2。不能按score剔除儿童、翻标签、改窗口，不能修复后借新的阳性结果重选主family。旧输出保留为已被具体勘误的版本，不混入新版本seed平均。

## 4.3 儿童个人支持：保留原20项family

### 4.3.1 底座、支持与共同query

只使用 core3：B0/TCS/TNCE；seed为3401/3407/3413。每个儿童使用其原外层fold选定的 private CE checkpoint；冻结backbone θ与三slot heads，复用原 per-trial slot log-probabilities 和 `a_target`。从同一底座比较 U0、仅δ适配、仅affine校准；不增添δ+affine组合或新的支持策略。

沿用注册划分和 `support_contract`：

- `available` 是该合同允许的全部trial集合，不是支持池。
- early pool来自最早 `ceil(0.3×物理block数)` 个block，经原边界trial删除与完整epoch guard。
- `n10 = min(floor(0.1×len(available)), len(guarded_early_pool))`；U10从该pool不放回均匀抽取n10，不使用标签覆盖筛选。
- U10取样seed固定为351410、351411、351412、351413、351414；U30为guard后整个early pool。U10/U30都不是10/30 trials或秒。
- U0、所有U10 draw、U30、δ和affine使用**同一个冻结query**；保存query/support行哈希、直接标签访问量与guard删除数。少量/单类support执行原无更新fallback并保留该儿童；若query本身不可用，按原缺失规则报告，不能填零风险。
- 全记录离线滤波和每人/record标准化的无标签访问仍按原合同披露。直接sample guard不等于证明预处理完全因果隔离。

δ从每个新儿童的零向量开始，作用于 `a_target+δ`，以支持标签更新5步，学习率0.1、L2系数0.1，θ/head不更新。affine以同checkpoint的混合概率为输入：`pcal=sigmoid(exp(s)×logit(p)+b)`，s=b=0，惩罚`0.1/2×(s²+b²)`，5步、学习率0.1；仅为logit计算将p截于`[1e-6,1−1e-6]`。精确更新和损失单位继承冻结的 `aln41/support.py`，不可为了输出bits而改变拟合目标与惩罚相对尺度。不同实际实现须记版本差异，不静默重算已注册结果。

### 4.3.2 原family成员与方向

主端点是同query的NLL，单位bits/trial，**风险越低越好**；Brier/AUC为辅助。以下列出原注册的对比身份，实际输出必须保留server原始key和原符号定义，不能自行重命名主结果：

| 每个arm的6项；arm=B0/TCS/TNCE | 数量 |
|---|---:|
| δU10−U0；δU30−U0 | 2×3 |
| calU10−U0；calU30−U0 | 2×3 |
| δU10−calU10；δU30−calU30 | 2×3 |
| δU30 gain 的 TCS−B0；TCS−TNCE 直接交互 | 2 |
| 合计 | **20** |

已核对基准analysis_r2.py的support_values：δ与cal原值采用U0 NLL减去更新后NLL的正向gain，再在人内平均seed。表中的“对比”表示比较身份，最终family表达式与输出key仍从原注册绑定。

登记每个原key的精确 `estimand_expression/unit/better_direction`，并核验family列集合/顺序及计划哈希。不可只保留δ相对U0的显著项：**δ相对U0及相对affine的比较都必须报告**。

可另导出易读的normalized gain，但它只是原列的符号变换，不形成新检验：令R为query风险，`g_delta=R_U0−R_delta`、`g_cal=R_U0−R_cal`、`g_delta_over_cal=R_cal−R_delta`，均正值为好。直接方法交互为`g_delta_U30(TCS)−g_delta_U30(B0/TNCE)`。必须同时保存原key、原value及sign multiplier；变号时CI为`[-upper,-lower]`，不能只翻点估计。原注册若已使用正向gain，直接对应，不重复变号。

五个U10 draw先在同儿童、同arm、同seed内平均，再在同儿童内平均三个模型seed，最后做population比较。人的n仍是原64人面板及原缺失合同，不是64×5×3。按原20-member family运行person-paired bootstrap-t，4000 draws、max-absolute-t同时区间；bootstrap seed、覆盖集合和有限方差处理原样继承并输出。严禁从两个aggregate CI相减构造直接差异CI。

δ降低风险说明少量支持改变了该儿童的概率使用；只有相对affine的额外风险收益才支持超出通用概率校准的作用。TCS特有必要性必须看已注册的直接arm interaction，不能用“一臂显著、一臂不显著”替代。affine为正斜率单调变换，AUC通常不变；不以AUC作为δ胜过affine的主证据。

## 4.4 跨刺激：固定纯音→ba/pa，保留13项AUC family

### 4.4.1 已冻结的语义与样本

沿用已注册决定，不根据R2结果换方向、替换任务或改变主端点。下表是编制本包时已核对的注册摘要，执行时应与原decision、roster和哈希逐项相符；它不是本包新完成的原始数据核验。

| 项目 | MFF puretone | MFF ba/pa |
|---|---|---|
| 记录中的刺激标识 | 1000/1500 Hz | `/ba/`、`/pa/`范式 |
| 任务标签 | standard=0，deviant=1 | standard=0，deviant=1 |
| 注册deviant比例 / 平均SOA | 0.150 / 0.873 s | 0.151 / 1.074 s |
| 原始记录 / 身份数 | 41 / 37 | 29 / 27 |
| ST1每类≥40且≥4block之后 | 35 / 33 | 25 / 24 |

同日跨刺激配对为8对；旧7对仅使用earliest record而遗漏第二条过gate记录，第9对因只有39个deviant未过原门槛。这是资产覆盖更正，不降低门槛补人；8对只做描述性呈现，不增添配对推断family。全部128 EGI通道、250Hz、epoch `[-0.2,+0.6)` 秒；保留E1–E128顺序及现有CB位置适配局限，不声称新增已校准的空间对应。

ba/pa没有真实声音waveform；音节标识来自记录命名，standard/deviant角色依据既有派生容器及未观察到swap的一致性判断。软件记录的一致性不是物理刺激反平衡证据。现任务是standard/deviant角色读出的跨范式迁移，不是语音理解或声音身份的zero-shot匹配。

### 4.4.2 输入、split与两条读出路径

复用冻结core3：B0一套Stage1提取、TCS/TNCE各三个source seed，总7套原注册提取；已完成时直接复用。原注册约2 GPU小时是提取预算记录，不是本包新增提取授权或完成证明。三槽先native crop再真实时长resample/pad；每record channel z-score与测试无标签访问范围原样披露。

ba/pa24个身份按原sha-rank分为5个外层fold。**使用已保存身份→fold表，不重新按当前文件排序生成。** 同人多record整体同fold并按原规则pool；不能让另一记录进入训练。跨刺激重叠身份也按人排除。

- **Transfer：**fit集合是所有不属于当前ba/pa测试fold身份的合格纯音数据。PCA64、标准化、L2 logistic(C=1)、positive-affine校准以及history B1/offset的可拟合参数，全部来自该路径允许的纯音训练/校准角色；不使用ba/pa测试标签或特征拟合PCA。不得因transfer低于0.5而翻转标签、符号、角色或方向。
- **Refit：**固定同一public-source encoder，用另4个ba/pa身份fold拟合相同容量的整个读出流程，包括其PCA、标准化、logistic和校准，评价相同测试儿童。此路径使用目标范式训练儿童的标签，不使用测试儿童标签。

精确fit/ES/calibration行分配、PCA采样与维数、solver、class weighting及校准参数从原cross计划读取并写binding。若这些元数据尚未保存，先从生成代码/原缓存恢复，不能由当前结果反推设置或让server自由选一套“相近实现”。三slot保留共同表示空间及原q0概率混合，source q0与uniform/slot输出只有原计划已保存者才复用，不额外开展新的模型搜索。

每fold、arm、seed输出两条路径的训练/校准/test人数、records、trials、各类数、身份交集检查、PCA拟合行哈希、q0来源及query哈希。refit与transfer的训练域和样本量不同；`refit−transfer`称**目标范式监督重拟合收益**，不单独解释成等预算的数据效率或只改变最后一层的机制。

### 4.4.3 主要与解释性结果

主要端点仍是每儿童AUC，F_CROSS_STIM保留原13项及同时区间：

- 每臂B0/TCS/TNCE的 `transfer−0.5`、`refit−0.5`、`refit−transfer`，共9项；
- transfer和refit各自的 `TCS−B0`、`TCS−TNCE`，共4项。

每儿童、每seed先在固定Q上计算AUC，再在人内等权平均三个seed的AUC；不先平均预测概率再算AUC，那会改成ensemble。B0使用单份既定冻结baseline，不伪造三个独立seed。该顺序与基准analysis_r2.py的endpoint内种子平均一致；n为ba/pa24身份及原缺失合同。用原4000次person bootstrap-t、max-absolute-t同时区间；8对同日子集仅描述，不将它另立“更干净”的主分析。保存所有低分/反向结果，不把低于0.5重标为预测失败或据此删人。

现有history为6bin+B1 offset。若原R2已保存history-conditional bits，复用同布局但独立的描述性family，**不替换主AUC，也不借它筛选主成功案例**。若严格twin及其共同query预测已经存在，导出当前EEG与其他physical block、同child/history-bin twin的既有差异，并分别报告完整query与strict subset覆盖；不从覆盖不同的均值相减。没有合法twin映射/预测时登记`NOT_AVAILABLE_IN_REGISTERED_R2`，不自动新增twin训练、匹配策略或新科学任务。

已有预测、事件和校准缓存足以恢复原已执行的history/twin统计时允许CPU导出；需要新的拟合或输入、且原R2没有该任务时只记录缺口。事件核验确认的history bug依第4.2节定点修复，不能以“解释性结果”名义另开搜索。

跨范式transfer高于0.5支持**standard/deviant EEG读出可跨刺激复用**。它不能排除声音物理差异、稀有性、重复适应或未被6bin穷尽的sequence，因而不能推出与声音身份无关的抽象deviance/预测误差。若B0/TCS/TNCE都有迁移但直接差异弱，保留共享表示的科学结果，不归功于CS。若transfer弱而refit可用，说明当前固定读出不通用，不说明EEG无目标信息。

## 4.5 年龄、HA与设备经历：保留用途，保持归因

既有年龄任务是同一公共源冻结encoder的独立下游，不由五个private FT网络拼坐标。原R1摘要中，64人面板B0/TCS/TNCE的MAE为25.05/25.37/24.90月，raw参考32.38、训练均值32.02月；这些数值用于说明继承的证据位置，server应按原结果哈希核实，不据此伪造新的R2完成状态。

B0已经有可读的年龄信息；目前未观察到Stage2年龄增益，不将既有年龄效用归因于CS，也不把接近的点估计解释为等效证明。其功能是说明共同EEG表示的儿童发展相关用途，与事件分类、history和时间读出形成不同任务的证据。它不是临床脑龄诊断、听觉特异成熟度或治疗效果。

继续复用原OOF预测：先计算每人每seed的绝对误差，再在人内平均，最后作paired人口汇总；平均prediction后算MAE属于ensemble，不替换原主端点。R²/Spearman与回归系数按原person bootstrap重新计算统计量，不作为个人均值差直接输入paired-mean程序。训练均值和raw参考保持同人同fold；原20-channel mean log-variance只是一项已匹配的简单参考，不代表所有临床/频谱基线，更不能用它的较弱预测否定旧D2/GX及HA/设备经历证据。

HA、年龄和设备时长仍按已注册F_ASSOC及其四个人级端点处理：history-conditional当前增量、W0→W2固定损失、目标窗重拟合恢复、U30相对U0变化。全体`age(year)+HA`、仅HA `age(year)+device_duration(year)`；NH时长不填0。方法解释用TCS−B0/TNCE的直接个人差异，不根据某一组显著另一组不显著推组间不同。不新增年龄段、HA分层、佩戴阶段或每个window/head的回归。横断面设备经历不改写成治疗轨迹；现有不确定区间和有效结果均保留。

## 4.6 必备产物与资源上限

下列是新增说明/审计的交付文件，不替代原R2输出路径或key。实际根目录写入binding；私有根与公开根必须分开。

| 产物 | 位置与最低内容 |
|---|---|
| `R2_REUSE_INDEX.json` | 原unit/plan/结果key、完整哈希、完成/运行/缺失状态、reuse/resume/修复行动；已经完成的R2必须进入复用清单 |
| `PRIVATE_EVENT_TRACE.json` | 仅私有根；遵循schema；完整事件链、stored/recomputed history、y/对齐、roles、guard与检查结果；身份crosswalk另存 |
| `PRIVATE_EVENT_VALIDATION_SUMMARY.json` | 公开匿名摘要；审核状态、覆盖计数、错误种类与影响端点、不可恢复项；无真实身份、原始路径或逐事件轨迹 |
| `PRIVATE_RECOMPUTE_SCOPE.json` | 私有依赖明细及可公开匿名版本；旧/新资产、受影响unit、训练/选模影响、拟重算成本、替代关系；无bug时明确`NO_RECOMPUTE_REQUIRED` |
| `SUPPORT_INTERPRETATION.json` | 原20列及原方向、可选normalized gain映射、同query/支持访问、draw与seed汇总、δ对U0及affine、两项直接arm交互 |
| `CROSS_STIM_INTERPRETATION.json` | 原13列AUC及人数、每路径train/cal/test计数、原history/twin可用性与覆盖、8对描述、标签证据级别与允许主张 |
| `AGE_AND_CLINICAL_REUSE.md` | 原预测/结果哈希、Stage1用途与Stage2归因、error-before-seed-average规则、旧D2/GX/HA证据及不确定性；不新建subgroup family |
| `PRIVATE_R2_R3_REPORT.md` | 科学问题→结果→可支持解释→剩余限制；已完成复用与新增CPU工作分开；确认bug按版本说明 |

本章**额外训练预算为0：不增加source训练、private FT、age head sweep或新的跨刺激/支持训练单元**。仍需完成的原注册R2由原预算和原unit继续；已有完成件直接复用。现有预测/缓存的CPU汇总、事件核验、原已完成统计的恢复不新增研究轮次。必要bug修复必须另附scope与资源收据，按已确认依赖最小重算，不自动启用新的消融或第4轮。

R3据这些证据收束主张：共享表示的效用、跨刺激读出复用、个人支持的额外价值与CS特有收益分别判断。任何一项方法增益不成立，都不抹掉有效儿童科学结果；任何一项科学结果成立，也不自动证明TCS必要。

---

来源文件：docs/05_PAIRED_RISK_AND_INFERENCE.md

# 05 — 个人净改善与配对推断合同

## 1. 分析问题与地位

本工具解决一个具体误读：`GC = R(HP) − R(EC)` 为正，并不表示个人校准后的 EC 优于未经个人拟合的 E0。HP 可能已经偏离较好的 H0。需要在同一人的同一查询集上，直接比较 E0、EC、ET。

`tools/paired_risk_summary.py` 是独立 CPU reference helper；不提取 EEG、不拟合模型、不提交作业、不联网、不清理文件、不修改仓库，也不替代服务器 production 推断入口。它依赖 Python 3.10+ 与 NumPy 1.22+。

**这两个 NET 对比是在观察 R1 之后确定的诊断问题。** 它们在本包中固定用于后续 R2 与固定双 seed 面板，标签为 `post_R1_diagnostic_net_contrasts`；不能改写为观察 R1 前预注册的 confirmatory 终点。实际冻结时间与 source 绑定由运行收据记录，程序不能替代时间戳证明。原 R1/R2 families、原估计和原区间完整保留；新增 NET family 另列，不把更好看的新区间用于替换原区间。

## 2. 估计量：只用直接风险相减

所有量均以“风险减少为正”。每个风险是一个目标人、一个固定 tool、一个 seed 在同一物理查询集上的均风险。

| 名称 | 直接式 | 可检验的等式 |
|---|---|---|
| G0 | H0 − E0 | 固定 source EEG 相对 source history 的增量 |
| GH | H0 − HP | 个人 history 更新增量 |
| GC | HP − EC | 相对个人 history 基线的整体 EEG 尺度增量 |
| DT | EC − ET | 相对 EC 的额外时间读出增量 |
| NET_C | E0 − EC | GH + GC − G0 |
| NET_T | E0 − ET | GH + GC + DT − G0 |

表中 H0 等均指 `R(H0)` 等。代码的 NET 估计使用直接式；输出逐人代数重构误差，便于发现汇总口径问题。**不推定、重命名或计算 J。** 不从独立区间相减构造配对区间。

例如 H0=1.00、E0=0.80、HP=1.30、EC=1.20，GC=+0.10，但 NET_C=−0.40：尺度项收回部分损失，个人模型仍逊于原固定读出。这个反例包含在可运行检查中。

## 3. 输入 CSV 与共同 Q

必须字段：

```text
cohort,person_id,tool,seed,unit,risk_H0,risk_E0,risk_HP,risk_EC,risk_ET
```

`cohort` 应分到本次预定的独立分析组，例如 `FAU_HA`、`FAU_CI`、`FAU_TH`、`DTU`、`PRIVATE`。不能先把 FAU 的三个组混合为一个 cohort 再解释组差。`unit` 必须明确，例如 `mse` 或 `bits_per_trial`；一个 cohort 内所有人、tool、seed 必须一致。不同 cohort 始终分别汇总，即使 unit 名称相同也不合并。源端目标标准化、NLL 的 bits/nats 转换必须由 adapter 正确完成并保留其 receipt，本工具不猜单位、不转换。

共同 Q 可用两种明确方式声明：

1. **优先提供五个字段** `risk_H0_query_fingerprint`、`risk_E0_query_fingerprint`、`risk_HP_query_fingerprint`、`risk_EC_query_fingerprint`、`risk_ET_query_fingerprint`。每行五者必须相等；若同时给 `query_fingerprint`，它也必须相等。
2. 只给一个 `query_fingerprint` 时，执行者必须加 `--shared-query-declaration`，明确确认 adapter 已把五个风险绑定在相同 Q 上。输出会保留这个较弱的 `adapter_declared_shared_Q` 状态，不冒称工具检查过底层 trial。

所有 fingerprint 都必须是 SHA-256 的 64 位十六进制摘要。同一 cohort、同一人的全部 tools 与 seeds 也必须一致。这是本轮冻结 Q 的严格合同，不允许静默使用每个工具或 seed 各自剩余的 query 子集。摘要的 canonical payload 应包含排序后的物理 query ID、目标定义、风险权重及目标值的摘要；需要保存构造规则和相应 manifest。相等 hash 只能验证声明一致，不能证明 adapter 实际用了这些行。

若目前只能取得各模型在不同 Q 上的 aggregate 风险，**不能直接送入工具，也不能伪造相同 fingerprint**。由 adapter 从现有逐 query 输出在预定共同交集上重算风险并报告覆盖；不能仅靠人级均值恢复共同 Q。此工具不会进行这种交集筛选。

每个 `(cohort, person_id, tool, seed)` 必须唯一。每个 cohort 的所有人必须拥有全部已声明 tools 和 `--expected-seeds` 中的每一个 seed。缺一项、重复、额外 seed、空 seed、NaN/Inf、负风险都会失败；即使负数仅为 `−1e−16` 也不静默截断。上游若需处理数值误差，应记录原因并重新导出。原始 MSE/NLL 非负不意味着净改善也非负。

默认可发现观测面板中的缺项，不能发现整个人或整个 tool 完全未进入 CSV。正式运行应同时提供 `--expected-panel expected_panel.json`，格式为：

```json
{
  "SYNTHETIC_ONLY": {
    "person_ids": ["synthetic_1", "synthetic_2", "synthetic_3"],
    "tools": ["local", "cbpre"],
    "unit": "mse"
  }
}
```

该示例不是任何真实队列名册。实际文件由本轮冻结 source/target roster 导出；所有 cohort、人、tools、单位必须精确匹配，不做缺失后 complete-case 筛选。没有这个文件时，输出 `expected_panel_status=not_supplied`，不能宣称覆盖了完整队列。

若源数据尚有内容 fold 或 support draw，adapter 须先按原合同在每人、每 tool、每 seed 内聚合，保留逐 fold/draw 溯源与公共 Q manifest。不能把 fold、draw 或 seed 伪装成新的人；也不能把跨 seed 均值复制回两个 seed 行。工具能检查输入面板，但无法仅凭最终均值证明这些上游操作。

## 4. 人级均值、独立 NET family 与参考区间

每人首先等权平均固定 seed 列表的五个风险，随后直接计算各效应；这与先算逐 seed 效应再等权平均代数等价。人群均值再按人等权。`seed=3401/3407` 不使 n 翻倍，训练 seed 不是 bootstrap 的独立样本。

每个 cohort 创建一个独立 NET family，成员固定为该 cohort 的全部 tools × `[NET_C, NET_T]`。G0/GH/GC/DT 只输出逐人及描述均值，不在这里补做原终点的新显著性检验。不增加 cross-tool 或 cross-cohort contrast。各 cohort 的区间只控制各自这个 family 的名义同时覆盖，不宣称所有 cohort 的联合覆盖。

**参考方法为 fixed-original-SE max-|z*| 人级 bootstrap，不是 production bootstrap-t 的复制。** 对 family 的整个人效应向量进行有放回重采样，保留同人的 tools 与 NET 对比配对；默认 B=4000。在原始 n 人上计算每个效应的 `SE_j=sd(d_ij)/sqrt(n)`。对每次重采样取：

\[
M_b=\max_j\left|\frac{\bar d^*_{bj}-\bar d_j}{SE_j}\right|,
\quad c=Q_{0.95}^{\mathrm{higher}}(M_b),
\quad CI_j=\bar d_j\pm cSE_j.
\]

分母始终是原始人样本的 SE，**不是每次重采样的 SE**；没有复制原算法的 studentized bootstrap-t。区间只是在给定已拟合模型、固定 seed 列表、当前人群抽样假设下的参考近似，不包含重新训练模型的不确定性，也不修复高影响个体、错误事件定义或模型构造问题。它不是用来把 child60 导致的不稳定原区间“修成显著”的替代主分析。原 production 区间与状态必须并列保留；若需要一比一复现原算法，另按其实际源码实现并验证，本工具不作此声称。

退化处理固定如下：

- n<3：输出人级数据、均值与明确状态，family 区间全部为 `null`。
- 任一 family 成员原始 SE=0：不删除该成员、不把点估计伪装为确定区间；整个 family 区间为 `null`，列出退化成员。
- 重采样中 SE=0：计数并完整保留这些 draw。因为本参考方法不以重采样 SE 作分母，它们没有除零；不能用这一规则模拟 bootstrap-t 后再丢弃 bad draws。
- 非有限统计量或区间：失败，不产生 NaN/Infinity JSON；若临界值退化为0，输出不可估计状态与 `null` 区间。
- 不使用自动剔人、winsorization、改终点、换分母或只报告显著 tool。

child60 的事件/标签/history 原始记录审计与本统计 helper 是两项不同任务。若确认上游错误，按依赖修复并保留版本；若记录属实，保留该儿童。不能从一个异常均值判断其应被删除，也不能把 R2 seed 复制当作数据定义审计。

## 5. 运行、输出与检查

优先五个逐风险 fingerprint 字段：

```bash
python -B tools/paired_risk_summary.py --input normalized_person_risks.csv --expected-seeds 3401 3407 --expected-panel expected_panel.json --output paired_net_diagnostic_s3401_s3407.json
```

只有共享 fingerprint 时，命令加 `--shared-query-declaration`。R1 单 seed 描述可以用 `--expected-seeds 3401`，保留独立输出名称；不能把单 seed 输出伪装成双 seed 完成结果。可通过 `--family-id` 设置明确的版本标签，family 成员仍固定为全部 tools 的两个 NET 对比；bootstrap 参数及随机种子均写入 JSON。

输出拒绝覆盖已有文件；输出目录须已存在。无效输入退出码2，不写结果。有效但区间退化时仍写结构化报告，退出码0，必须读取 `net_family.status`，不能仅看进程成功。

主要字段：

- `analysis_scope`：观察 R1 后诊断、reference-only、条件化对象及原 families 保留声明。
- `input`：CSV SHA-256、共同 Q 声明模式、预期名册验证状态、观测面板与忽略的额外 metadata 列。
- `cohorts[].per_person`：人级 seed 均值、六个效应、每个 seed 原值与 query fingerprint。
- `descriptive_by_tool`：五状态风险与六效应人均值。
- `net_family`：明确 family 成员、n、参考方法、原始 SE、名义同时95%区间、零重采样 SE 计数、实际保留的 bootstrap 次数、退化状态。

执行有意义的合成检查：

```bash
python -B tools/check_paired_risk_summary.py
```

检查 GC 正而 NET 负的反例；固定 seed 平均不导致伪重复；同 Q 绑定；不完整/重复面板与名册缺失；负值/非有限值/混单位拒绝；单摘要必须显式声明；零原始 SE 不伪造区间、零重采样 SE 不丢 draw；CLI 不覆盖已有输出。所有记录均为合成 fixture，不是研究观测。

---

来源文件：docs/06_EXTERNAL_COMPARISON_AND_CLOSURE.md

# 6. 外部比较与第三轮收束

## 6.1 外部比较要回答的问题

核心的同条件方法证据来自 TCS/TNCE/GCS/B0/wrong；外部席位回答的是：**与现有独立听觉方法相比，这套学习和读出原则在共同听觉应用合同下是否有实际价值。** 外部对手使用自己的已发布架构和输入方式，因此这是系统层面的应用比较，不把架构、预训练数据及输入时长差异归因给 CS。

整个 R3 只占原来一个外部方法席位。先读取 server 在 R1 intake 已保存的 EXTERNAL_SLOT_DECISION.json，记录其 hash、时间、代码 pin、资产和准入结论。已定 fallback 时不重开 MindMix；原决定尚有未完成的工程条件时，按该条件完成一次核验。不能按刚取得的本方法或对手分数换路线。旧决定若缺失，记录 provenance 缺口，并在读取任何新外部 test score 前按下列输入/可恢复性规则冻结；不能追记为 R1 已完成的决定。

## 6.2 两个叫 DTU 的资源必须分清

| 资源 | 原始身份 | 对本次的意义 |
|---|---|---|
| MindMix 论文所引 AAD DTU | Fuglsang et al. 2017；Zenodo 1199011，18人，发布 AUDIO.zip | 论文的被试内5折、2秒任务不能直接当作本项目的44人结果 |
| 本项目 DTU | Fuglsang et al. 2020；Zenodo 3618205，22 HI+22 NH | 官方发布的是 speech envelopes，原语音需要另外取得；server是否已有合法raw audio必须查实 |

不能通过 envelope 上采样构造“16 kHz waveform”，不能因两个数据集都叫 DTU 就转用模型成绩、fold表或刺激ID。这里只核查 server 已有原始资产，不自动联系作者、申请新数据或启动新队列。[1–4]

公共读出代码已经给出本项目的训练单位：aln41/frozen.py 的 DTU content folds 为0/1；aln41/readout.py 的每个 content fold 内循环5个 pooled person folds。每个公共方法因此有 **2×5=10个下游拟合单位**，不是儿童5fold，也不是44人各自5fold。接包时必须逐个绑定原 train people、fit/es/test roles、内容排除及共同 query，不能只复制数字10。[5]

## 6.3 互斥的两条合法路线

### A. 原决定仍指向完整 MindMix，且输入与评分合同可恢复

使用官方已发布 fusion checkpoint，完整恢复 EEG、audio、projection、CALRA；不是 EEG-only 提取。记录实际文件 SHA、完整配置、加载覆盖和排除的任务头。独立 Stage1 资产曾失败，不自动推出这个 fusion checkpoint 失败。

原生输入核验包括200 Hz的2秒 EEG、16 kHz真实语音、通道映射、振幅/参考与频带。使用真实已有 EEG 重新生成所需处理，不能靠低频缓存恢复已经丢失的频带。所有输入访问必须落在允许的训练或 query 物理段内。

作者推荐的 Stage3 路线为 multimodal_real + calra，released fusion initialization；本包固定采用当前公开推荐CLI配方：batch32、50epochs、LR1e−5、wd0.01（当前README训练表/公开CLI）；论文Appendix A.3的batch64、wd0.05等差异必须记录在binding，不追加另一套配方。完整记录实际pinned code的optimizer、scheduler、checkpoint选择和其余默认值；有冲突时说明作者来源和采用值，不能用目标test选一组。[3]

**评分准入必须先于 test 指标。** 当前公开实现中需要核对 target_audio 进入融合及 batch 归一化的行为。用合成候选和训练侧无评分样本验证：

- 评分函数只接收 EEG 和两个未标注候选，真 attended 标记仅在得分后用于评价。
- 交换候选次序后两个分数相应交换；整段预测对物理候选的选择不变。
- 改变 batch 排列、batch size 或加入无关样本不改变同一个样本的候选比较。
- 不把正确声音永远放在 privileged target 槽，再把其高分当盲二选一成功。

允许机械的候选双次调用、顺序对称化和合法单样本分数导出，但必须记录公式与改动；若需要新设计 fusion、损失或以真值挑分支才能满足合同，判定本席位尚不能忠实执行，按已登记 fallback 处理。不能悄悄“修好”作者方法再称原版复现。

本路线使用一个 released fusion checkpoint、下游seed3401，在本项目10个公共训练单位完成作者 Stage3 配方。没有测试人的训练标签，fit/ES数据访问与自有方法相同。每fold使用fit拟合、es按预先登记的作者合法规则选状态；作者没有可直接沿用的选择规则时固定final50，不由test挑epoch。确切选择必须在首次读取新test得分前写入binding。

名称固定为 **MindMix released full architecture, common-protocol task adaptation**。它保留完整多模态系统，但不同于论文被试内2秒协议；不能把它称为作者99.93%结果的复现，也不能用一个本地seed声称全面否定MindMix。

### B. 已登记 fallback：Transformer-CLIP 的原生回归用途

使用官方发布的单模型 EEG encoder 和对应配置，冻结 encoder，按论文的线性卷积读出族预测 envelope。原论文回归使用3秒、64 Hz EEG表征、kernel32的500ms线性读出，以及50% overlap/Hann overlap-add。此支路在目标应用不需要原语音，适合本项目真实存在的 envelope。[4]

这不是把 MindMix 换成同backbone TNCE，也不是声称重现 Transformer-CLIP 的原生20秒AAD；作者论文原任务是 match–mismatch 与 envelope regression。本包名称固定为 **Transformer-CLIP published frozen encoder + native envelope-readout family, adapted to the common AAD protocol**。

接包时完成以下绑定后运行10个读出单位：

1. 选用官方链接预先指定的一个 released model，恢复 args/config、EEG encoder与权重；不挑本项目得分最高的 checkpoint，不额外组成16模型ensemble。
2. 验证64通道名称/顺序/参考/单位，原生3秒与64 Hz处理。不能把3秒压缩成400ms，不能以零填充通道冒称完整空间对应。
3. 读出训练采用可恢复的作者回归配置和实现；若原配置没有公开到可复原程度，固定使用同一线性卷积函数族的训练侧平方误差拟合（带bias，kernel32），采用确定性最小二乘最小范数解，不加新的λ/epoch搜索。该fallback必须标为“native readout family, deterministic LS implementation”，记录与作者优化差异。可用分块QR/SVD或LSMR避免形成巨型design matrix；不以不受控normal-equation逆矩阵替代稳定求解，报告残差/condition。
4. 读出的所有中心化、输入缩放及参数只由对应fit侧估计；ES仅供原固定配置需要的选择或既有tau校准。不得使用outer test儿童/成人标签、features拟合PCA，或给外部方法额外的subject-specific适配。
5. 从3秒预测拼接到既定5秒物理segment，保持原20秒窗口与候选；边界padding与Hann零端点应有显式有效支持mask。若原query部分无法无越界地得到合法预测，先按几何可用性冻结共同有效窗口，并在这些窗口上从已有输出重算所有core3；不根据正确与否筛query。

论文原native读出比本项目三短窗可看到更长上下文，必须在表中披露；这个系统比较不替代同输入TCS/TNCE的因果归因。表征预训练数据与目标/声音内容重叠也必须查证，未知状态保持未知，不默认为无重叠。

## 6.4 共同20秒评价与具体预算

沿用原attention流程：相同5秒物理segment组成相同20秒连续窗口；各窗口的评分按两个候选顺序评价，平分记0.5；每人先在原content folds/合法窗口按原规则汇总，再人口推断。自有core3使用原q0结果，uniform只作为原有描述。

Transformer-CLIP先导出每5秒段 predicted-envelope 对两个候选的相关差，再用原mean-score积分；tau只在原fit/es窗口上拟合。MindMix先导出合法候选margin，其原生2秒子窗须在5秒段内用预先冻结的几何铺法聚合，再走同一20秒mean-score、训练侧tau与双顺序汇总；实际铺法写在结果前的binding中，不搜索窗口偏移。

输出20秒每人accuracy及NLL bits、raw候选margin、有效窗口数、Q哈希及覆盖。5/10秒若可从相同既有margin直接导出，只作描述，不新增选择任务。

比较家族为同一共同Q上的 **external−B0、external−TCS、external−TNCE**，对accuracy和NLL分别保持独立三成员family，使用原person bootstrap-t 4000与原退化处理。NLL注明越低越好，禁止与accuracy反向混读。core3在人内先平均原三个seed；外部是一个固定发布checkpoint及下游seed3401，CI条件于这些模型，不覆盖外部预训练随机性。附上自有方法各seed，不能把不对称seed数解释成外部训练稳定性结论。

| 资源 | 本版上限 |
|---|---:|
| 外部方法/路线 | 1；A/B互斥 |
| 新Stage1/Stage2 source pretraining | 0 |
| 外部下游seed | 仅3401 |
| 公共下游训练单位 | DTU44：2 content folds ×5 person folds=10 |
| A路线encoder FT | 最多10；完整Stage3，不藏在“1个method”里 |
| B路线encoder FT | 0；10个冻结表示线性读出拟合 |
| 新儿童外部FT、FAU外部任务、ensemble、外部HPO | 0 |
| 可选方法消融 | 未启用 |

这替代草案中不适合实际公共fold结构的“总3次optimizer run”计数。原R3允许一个外部席位和有限下游训练，本版明确为这10个共同公共单位；不同时运行两条路线，不占用未启用的消融预算。中途已完成合法外部路线后不得因分数弱再转另一方法。

先对一个固定fit单元测内存/耗时，登记10单位成本和队列；不以估计时间代替资源账本。若真实资产/输入不能忠实恢复，交付具体失败证据与已核定可行的fallback；两条均有实质阻塞时关闭本轮执行并明确“外部比较尚缺”，不能写成论文已满足外部验证。

## 6.5 R3 的科学结束条件

R3依次回答：公共学习是否添加刺激相关判别依据；时间读出是否可复用；个人δ是否胜过普通校准；儿童是否支持跨刺激读出与独立发展信息；外部方法比较把应用表现放在什么位置。

结束研究轮次不等于宣称PR投稿条件自动满足。如果额外方法价值仍没有成立，应明确“目前不足以支持所拟方法贡献”，保留所有有效科学结果，进入写作/选题取舍；不通过另开第四轮或换终点挽救预定结论。

## Primary sources 与本项目依据

1. MindMix正式论文，§4及Appendix A：https://proceedings.iclr.cc/paper_files/paper/2026/file/b0ae046e198a5e43141519868a959c74-Paper-Conference.pdf
2. DTU18数据：https://zenodo.org/records/1199011；DTU44数据：https://zenodo.org/records/3618205 （Audio段）。
3. MindMix官方README与原实现：https://github.com/CookieMikeLiu/MindMix；universal_eeg_finetune.py、universal_models.py、universal_trainer.py。原资产审计pin为98445f368efcb161c638172501bd16f92d09a89d；server实际采用pin必须记录，不随main变化。
4. Bollens et al. 2025，Regression/Finetuning：https://pmc.ncbi.nlm.nih.gov/articles/PMC12329020/；官方模型/代码：https://github.com/exporl/transformer-clip-eeg。
5. 本项目固定基准：https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/auditory_alignment_v3/aln41/frozen.py；同目录readout.py。所有上列网站核阅于2026-10-21；这不替代server的实际完整资产加载验证。


---

来源文件：docs/07_REPORTING_AND_HANDOFF.md

# 7. 科学报告、交接与停止

## 7.1 最终报告先回答研究问题

报告正文先按下面五个问题给出结论、逐人证据与直接对比，再报告工程状态。不能以队列清空、表格格数或所有脚本退出0代替科学结果。

| 问题 | 必须一起呈现 | 对主张的影响 |
|---|---|---|
| 学到了哪些声音相关关系？ | TCS/TNCE/GCS/wrong/B0的内容与history-residual；旧有效local/CB/REVE成分结果；source诊断 | correct−wrong不能替代correct−B0；CS必要性须直接对比TNCE/GCS |
| 时间改变了什么？ | 同窗、固定跨窗、重拟合三者；旧细时间探针单列 | 重拟合恢复不单独等于迁移优势；窗权重不叫神经潜伏期 |
| 新个体需要哪种适配？ | δ对U0、对affine；ALN3.6 NET_C/NET_T与旧分项；每人分布 | 相对弱HP的改善不等于超越E0；共同接口收益与CS专属收益分开 |
| 儿童承担了什么科学功能？ | frozen/FT/history/twin；纯音→ba/pa transfer/refit；年龄与既定关联 | 分别判断判别复用、表征可用、发展相关信息；不互相替代归因 |
| 与外部方法相比实际怎样？ | 一个忠实任务适配系统的同Q20秒结果、输入/训练access和成本 | 不能以同名数据或论文acc替代共同评价；不足则诚实标出缺证据 |

每个结论给出：原结果文件/hash、样本与query覆盖、效应与区间、各seed方向、该结论依赖的假设/有效性状态。不使用“未显著所以没有信息/已到天花板”，也不因为一个seed阳性就称稳健。零效应附近的区间宽度、实际量级和直接方法差异一起解释。

## 7.2 必须交回的研究产物

下列文件名是建议的新汇总名称；服务器实际目录写在binding。旧输出保持原名与原key，用索引连接，不要求复制大缓存。

1. ROUND2_AND_CLOSURE_REPORT.md：上述五问题的独立可读正文；末尾给支持/未解决/不支持的主张表。
2. SCIENCE_FIGURES/：docs/00五图PDF/SVG及图用数据；图内显示单位、n、seed、CI定义和覆盖；时间细尺度与400ms窗口不混成同轴。
3. EVIDENCE_INDEX.json：每个有效旧/新结果→研究问题/figure/panel/单位/比较合同/路径/完整hash/版本状态。all-zero pre或受已知代码错误影响的旧单元标invalid，不能把同系列全部删掉。
4. R2_REUSE_INDEX.json、INTAKE_AND_BINDING.json：当前HEAD、原计划、live queue观察时间、已有/缺失/复用/新算；记录真实工作量。
5. SOURCE_LEARNING_REPORT.md及诊断JSON/CSV：固定panel与checkpoint、native正确/错误目标、NCE精确null、CS potentials、raw/projection rank、δ/q变化、源ridge fit/dev、梯度，不在诊断中挑新赢家。
6. PRIVATE_EVENT_VALIDATION_SUMMARY.json、PRIVATE_RECOMPUTE_SCOPE.json：核验覆盖、来源等级、bug依赖或真实序列失配。原始事件trace只在私有根。
7. SUPPORT_INTERPRETATION.json、CROSS_STIM_INTERPRETATION.json、AGE_AND_CLINICAL_REUSE.md：原20/13/既定关联family完整保留，Q/训练侧与归因清楚。
8. paired_net_diagnostic_s3401_s3407.json及adapter receipt：新净收益明确post-R1 diagnostic/reference CI；原ALN3.6 production CI并列保留。
9. EXTERNAL_COMPARISON_BINDING.json、EXTERNAL_COMPARISON_REPORT.md及逐人20秒scores：唯一外部路线、10真实public units或具体阻塞；不把fallback称MindMix结果。
10. RESOURCE_AND_COVERAGE.json：原R2成本与本包增量、每job实际GPU时、失败原因、重用件、缺失单元、严格有效coverage。
11. FINAL_CLAIM_DECISIONS.json：按plans/decision_rules.json逐项回答，不自动开R4。

未完成、工程无效、来源未解决、有效但效应弱四种状态不得合并成“失败”。原代码/数据更正保留旧版、替代hash与依赖说明；含bug结果不能和修复版简单合并seed平均。

## 7.3 报告的固定结构

使用templates/ROUND2_AND_CLOSURE_REPORT.md。研究结论的主语是可读内容、读出复用、适配收益或儿童用途；不要让目录名、作业号和模型版本成为论文的逻辑主语。图表由已固定的科学问题组织，不按最终p值挑图。

bootstrap推断以人为单位，所有slot、tool、arm、seed、draw在同人内保留配对；一个人的多记录、seed、支持抽样不增加n。明确每个family控制什么，不把不同family各自95%区间说成全论文95%覆盖。既有原算法、reference helper和任何必要修复版本分别命名。

## 7.4 接包动作和提交范围

SERVER_START_PROMPT.md是直接交给服务器助手的启动入口。AGENTS_APPEND.md只供在现有规则中追加本轮约束，不能覆盖原AGENTS、原发布授权或安全机制。

本包没有发送外部消息、GitHub推送、取消作业或删产物脚本。用户已授权去标识个体结果公开；沿用已有发布流程即可，不再次询问同一授权。原始EEG、身份crosswalk、精细原始事件轨迹不会因为这项授权自动变为公开材料。

A3d/A3c/A3b/ALN2 D_FM的清理属于独立的依赖清理判断。此次先完成资产引用与本轮复用索引；不在实验包中自动删除或顺带清理它们。

## 7.5 明确终点

原R2的有限已授权任务完成或被具体有效性证据定点勘误，一个外部席位有可审计结果或具体阻塞，五问题证据整合完成后，本轮执行结束。存在论文证据缺口时在结论中写清，而不是继续扩model/seed/window/数据集矩阵。

优先保留真实、可复核的研究结果。CS没有独特优势时取消“CS优越”的主张；δ没有优于校准时取消“时间适配必要”的主张；这些判断不抹掉其它有效迁移、时间和儿童结果。也不把仅Stage1年龄预测成功重新包装成原定跨范式迁移已经成功。

