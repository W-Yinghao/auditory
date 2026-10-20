# 04 — 个人支持覆盖与适配友好的群体训练

本节问：个人更新缺少的是样本数量、支持覆盖、稳定概率接口，还是群体训练没有为少量支持创造可适配的表征？支持集实验和episode干预分别定位这两层，不以某个adapter获胜作为继续条件。

## 4.1 已有结果限定了什么

已完成DTU三seed input_spatial在10%支持下真实风险明显变坏，native gain却增加；新受约束D在部分完整配对中有收益，且0-step常获选。私有native科学在10%支持下local/CB的固定适配也有小幅伤害。这些结果要求同时报告真实风险、错配风险和选择行为，不能只看mismatch gain。

旧episode的一个bundle更新方向cosine约.99998，训练时adapter只有3个support步骤、低秩A约.01且B从0开始。它说明当前干预很弱，不证明所有episode目标都没有额外作用。该现象与“具体方法可以失败”并不冲突。

来源：[D真实风险](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/D_ADAPT_TRUE_RISK_RESULTS.md)、[新线结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md)、[episode参数诊断](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md)。

## 4.2 继续已经登记的有效任务

补齐现有受约束D、private_episode_v2及其inner源、private factorial、已有public episode和CS代表比较。按现场计划复用；旧3-step/ordinary/source结果保持原版本。REVE和CS有效配置保留，不将新支持/压力诊断自动复制成所有架构×loss×队列矩阵。

## 4.3 同一个query、同一个支持候选区域

首批固定DTU和private_bdf、NCE、seed3401、有效local与CBpre；各自原输入/读出合同不改。DTU复用原5秒segment/anchor合同；private复用native当前声音任务及其合法冻结source读出。两种任务的NLL不混合，private跨架构访问归因仍受docs/02限制。已有CS比较及单类支持勘误继续，但不自动复制本节新增支持策略。

1. 从真实时间序列建立前约30%的支持候选区域P与固定末段query Q；所有新支持策略共用完全相同Q。DTU依据原可用segment边界，private依据原物理block顺序，不能把private的block百分比偷换成trial百分比。
2. private旧 `split_blocks()` 还执行 `support[:-1]`、`query[1:]`。新版本先绑定统一的边界删样与实际sample/context guard，再固定P/Q；明确是否与旧query逐项相同。不能只写“末70%”便声称新旧完全配对。
3. 同时检查支持/query的完整FM上下文、anchor及预处理访问。ID不相交只是一项检查；所有条件使用共同安全query集，guard造成的损失逐人报告，不按分数删样。
4. “10/30”只作名义档位。DTU U10实际拟合数量取原可用segment总数的floor(10%)；U30取P中全部安全segment。private U10取原可用trial总数floor(10%)、最多为P内安全trial数；U30取P中全部安全trial。报告实际trial/segment数、物理block数及各自比例；P来源仍为同一个前30%区域。
5. n10为0、U10与U30数量因短记录相同或某query指标不可估时，保留身份/原因和其他可计算终点。不能伪造支持或删儿童以得到整齐曲线。

这里改变的是明确计数单位上的个人拟合量与支持构成；旧按前10%/30% blocks获得的结果另列。它们只有Q、指标及source实际一致时才能形成直接新旧差。

## 4.4 有限支持策略与访问预算

所有策略先固定实际 `n10,n30,P,Q`，不看Q标签或模型表现来选支持。U10从P内均匀无放回抽n10，嵌套于U30；五个预定抽样seed `351410–351414` 在每个人内重复，先在人内平均，不能把重复当新n或挑最有利子集。

| 策略 | 拟合样本 | 支持选择规则 | 回答的问题 |
|---|---:|---|---|
| U10 | n10 | 同P内均匀子集，固定五次重复 | 少量支持的平均效果 |
| U30 | n30 | P中全部安全样本 | 同来源区域增量数量及相伴覆盖 |
| C10 | n10 | private优先覆盖两类；DTU优先覆盖既有刺激/content groups；同等优先级用固定hash | 同数量下刺激/类别构成是否重要 |
| H10（仅private） | n10 | 优先覆盖既有六个history bins，并在P的三个时间分段间分散；ties固定hash | 同数量下历史/时间构成是否重要 |

C10的private配额先在两类间尽可能等分（稀少类不足则全部取入、余量由另一类补足），类内使用固定hash。DTU按真实刺激group轮转取样，不从EEG解码分数估计“有信息片段”。H10以尚未覆盖history bin优先、再以尚未覆盖时间三分位优先逐项取样；若全部已覆盖，选当前计数较少的bin/时间格，最后以固定hash打破tie。不能保证小n覆盖全部格，实际覆盖是结果的一部分。

以上是支持构成干预，C10同时改变类比例，H10同时改变历史与时间分布；不能称作只改变一个抽象“覆盖度”的纯因果分解。诊断先定位值得下一轮细分的机制，不追加所有覆盖轴的交叉矩阵。

**元数据访问与拟合预算分开。** C10/H10可能查看整个P（约前30%）的刺激日志、类别或历史元数据再选择n10进行梯度拟合。必须分别记录 `selection_pool_size / metadata_rows_accessed / label_rows_accessed / fit_rows / fit_updates`。只有实验设计日志中预先可知的刺激标签才可标为无需新增标注；若这些标签必须逐trial标注获得，明确它是覆盖干预，不宣称与仅观察10%标签的部署策略公平等预算。Q的类别、history结果和EEG分数永不用于选择。

规则/配额只用source开发确定，outer不调整。来源P、支持ID、排除/guard、query哈希、时间跨度、类别/history/content分布、有效独立声音数都输出。不能以某个儿童“支持难”将其预定为失败案例。

## 4.5 三类读出/适配，比较真实改变

在同一冻结source上保留三个条件：

- `zero_step`：原读出直接评价Q。
- `probability_only`：仅调整正温度，不动encoder。固定T候选{.5,1,2}，按该人的支持集真实NLL选择，精确ties优先T=1；候选池及正确标签须按支持角色合法构造。无合法支持风险则回退T=1并记录原因。
- `rank4_fixed20`：沿各任务已登记的rank4适配形式、目标与LR=1e-3，固定20次个人更新；DTU保留原lowrank_spatial接口，private保留原科学output-rank4接口。记录实际参数化，不把两种接口合成同一个统一效应。

不同时调rank、层数、LR和loss。已有source-inner选择的D策略另列，继续允许0-step；固定20步的干预不能被选出来的0-step政策收益替代。

按dataset/架构/readout分别给U30−U10、C10−U10、private H10−U10的真实风险改善差，以及rank4对zero-step、probability-only的直接差。风险改善统一为 `R_reference−R_candidate`；AUC另用candidate−reference。每个family在看新outer结果前写完整terms并使用docs/06的统计，五次U10重复先人内平均。U30−U10仍可能包含覆盖增量，C10/H10帮助理解它，不声称已经完全分离所有机制。

输出每人NLL、AUC（可估时）、检索rank/top1（适用时）、wrong风险、所选T/步数、概率TV/熵、表示变化及实际支持。query只有一类时AUC不可估，NLL和该人仍保留；不能为了有AUC删除儿童。

## 4.6 Episode：让源端有实质个人适配压力

首批只取DTU和private的local/CBpre、NCE、seed3401，复用对应合法inner/outer source。具体bundle由原注册身份确定，涵盖既定人/内容折；不是选表现最好的几个source。CS/REVE原有效episode队列继续，但不自动扩大新压力档位。

新两档是训练episode内部support优化 **20步、100步**；每档均配独立的ordinary与episode，从完全相同source起点、按相同人/支持/query采样流运行100次encoder更新。原3步版本作为已有诊断锚，只有来源和实现完全兼容时才作直接跨版本差。

| 组成 | 固定合同 |
|---|---|
| 个人adapter | 原lowrank_spatial，rank4；A约.01、B=0起点；Adam LR=1e-3；每个episode重新初始化 |
| encoder | local LR=1e-4、CB LR=3e-5；原AdamW/weight_decay=1e-4与100-update cosine；保持既有eval-with-grad模式 |
| episode query | 冻结已适配adapter参数，用适配后的模型产生query损失；保留现有一阶近似，不悄悄换完整二阶MAML |
| ordinary query | 做相同步数的sham support适配以匹配计算/曝光，但query走原base模型 |
| 成本 | 成对记录support/encoder optimizer步数、query数、重复曝光、wall time与显存；同更新不宣称完全同FLOPs |

两档均报告，不用outer选择20或100作为唯一结果。不得因为source中变化仍小自动加到1000步或改成更大adapter；新档位已经完成其有限问题后，先解释配方实际压力。非有限梯度、标签/身份泄漏是工程问题；分数不够好不是工程失败。

### 先记录功能压力，再解释目标效果

在source开发中记录实际BA范数、输入/表示相对变化、概率TV/NLL改变、adapter梯度、encoder更新方向与ordinary的夹角、trainable参数和实际更新计数。零向量的cosine应为未定义，不能编为0或1；不能只凭参数非零就声称功能改变。检查来源仅为source，不接触outer判断“压力是否足够”。

这些记录用于确认干预到底做了什么，不设必须达到某个ΔR或cosine阈值的准入门槛。若保持定义的两档仍近恒等，报告该配方尚未产生有效压力；若功能已改变却未改善目标风险，允许该训练方案失败。

### 目标评价与选择

ordinary/episode在相同Q上保留固定目标20-step适配的直接比较，先按每档分别报告。另沿既有source-inner候选{0,5,20}比较source/ordinary/episode策略，完整保存选择表和0-step比例；不把回退source获益当episode非零适配收益。两类评价来自同一版本记录，固定干预与选择政策分别解释。

合法独立inner来源优先复用；private v2已有真正排除inner儿童的source训练，不用见过该儿童的旧全source模型伪装。内层source ES内容和外层测试内容的边界按docs/03说明。

实现依据：[public episode](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/episode_training.py)、[private episode v2](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/private_episode_v2.py)、[adapter](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/adaptation_policy.py)。

## 4.7 CS单类支持：保留人，报告真实适配信号

现有private v2的 `support_policy()` 对CS只检查 `n_support<2`；多个trial但标签同一类仍可能进入优化。传统标签核CS在标签恒定时没有该类别依赖信号，梯度可能为零或只有浮点残差；优化循环计数不等于有效学习。

在新版本分别检查支持trial数、类别数、label-kernel状态、有效梯度和实际参数更新。单类CS保持身份adapter并标 `zero_signal_single_class_CS`，保留该人的全部可用query结果；0-step及接口基线仍评价。source episode发生单类支持时同样记录，无需删除该儿童或改变研究纳入标准。

不得暗中改用NCE替代CS以获得非零梯度、把相同标签拆为伪类、从query补少数类，或只报告具有两类支持的人。训练侧query若有合法的学习信号，其encoder更新仍按原目标执行，清楚区分“个人support没有信号”和“整个训练没有信息”。原执行保留，新修正另有code/analysis版本。

## 4.8 下一轮如何更新判断

同池增量有益而C10/H10也改变风险，说明支持数量和构成都值得研究；概率温度覆盖rank4收益，说明概率接口比新增表征自由度更优先；非零rank4稳定有益，才提供个人学习的具体证据。episode在有实质压力后仍未超过ordinary，只否定该有限配方的额外收益，不关闭适配友好群体学习问题。

每条报告先给真实配对效果和支持覆盖，再列剩余解释。正、负、不确定方向共同保留；私有儿童的支持结构是需要解释的研究对象，不是装饰外部测试。所有任务合计遵守10-GPU上限，真实依赖之外不另等go。
