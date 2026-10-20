# AUDITORY ALN3.5 — 完整下一轮 server 执行说明

**版本：2026-10-18；延续 ALN3.4。** 本文与ZIP内的 `SERVER_FULL_DOCUMENT.md` 字节一致。ZIP同时包含专题文件、声明性计划、参考Python工具、回执模板、继承合同及校验清单。

制作基线：`5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`；远端封版核对：`2026-10-18T20:47:50Z`。现场接入需重新查看实际状态。

本文按研究判断、证据及执行顺序展开；末尾附可复制清单与回执。不要从历史附件的旧启动指令开始执行。

## 阅读导航

| 顺序 | 内容 |
|---|---|
| 1 | 复制给server的启动指令与接入顺序 |
| 2 | 研究关切、最新证据、科学及儿童问题 |
| 3 | 先验、支持/episode、融合与时间读出 |
| 4 | 执行与统计合同、参考工具 |
| 5 | 活动规则、任务清单、两份比较清单和回执模板 |
| 6 | 来源与本地交付核查 |

---

# 复制给 server agent 的启动指令

这是 `W-Yinghao/auditory` 的 ALN3.5，延续已执行的 ALN3.4，不重新立项、不重训兼容结果。本包来自研究者阅读最新 GitHub `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11` 后要求准备的下一轮工作。请按包接入和执行限定范围，保持既有 10-GPU 上限；依赖就绪且相关工程检查通过后，不再等待论文框架、措辞、显著性或第二次 go。

先读 `START_NOW.md`、`docs/00_RESEARCH_DECISIONS.md`、`docs/01_BASELINE_AND_INTAKE.md` 与当前服务器 AGENTS 的最新区块。如果 `CODEX_HANDOFF.md` 在服务器存在，读取其最新交接；GitHub 未提供的文件不能假装已经读取。将 `AGENTS_APPEND.md` 的最新规则合并到活动规则顶部，保留旧历史及既有精确 hold。不要取消全部旧作业、清空 hold、覆盖在跑源码或删除缓存/checkpoint。

先记录实际 local/remote HEAD、已登记计划、完成记录、运行/等待任务、真实 checkpoint/cache 可用性和代码 hash。旧报告计数不是服务器此刻状态；main 若更晚，以新输出更新 intake，但保持本包研究关切与已见结果记录，不能据新结果选择有利人员、窗口或模型。

本轮立即工作：

1. 给旧 private local/E_PUBLIC_TRANSFER 的 `pre` 全零输入及相关 TG 行列作版本化勘误，保存原数值；其后刺激、新 prior 三窗、同架构初始化分析继续。
2. 从真实 unit 的 per-participant 输出补规定的直接成对差、组间改善差、支持覆盖；不能从 aggregate CI 相减恢复配对区间。已有有效主分析不改写，本轮新增分析明确 exploratory。
3. 补齐已登记的 CB auditory continuation、受约束 D、强融合及其 inner sources；private factorial/episode、attention、prior LOO、数据曲线等有效在跑任务继续按其真实依赖和现场优先级执行，避免重复。
4. 按专题规格实现有限新增：local AP 的同目标错音频控制；固定 query 下支持数量与覆盖分离；有实质适配压力的 episode 对照；整条流程跨人开发的真实风险 checkpoint 选择；利用已有预测分解概率融合收益。现有 CS/REVE 竞争配置保留，不自动展开全模型×全loss×全时间矩阵。
5. 用新 execution ID 和独立输出路径绑定设计、数据、source/selection/access、种子及代码。先完成必要的源端/工程检查，再执行固定生产比较；禁止将 outer-test 风险、组别差或 p 值作为选择器或运行准入门槛。

研究者关心的是声音–EEG 对齐、不同听觉经历的共享表征、个人支持与时间组织。不要转成 ERP 主线、普通跨被试排行榜、校准修复论文或预定的负结果故事。具体方法失败可以保留为失败；弱结果不能升级为无信息、普遍天花板。所有有效阳性、阴性和不确定结果都保留。

只使用已发表传统核 CS、InfoNCE 与现有允许方法，不引入 VCS-QMI/未发表变分 critic。私有儿童是当前声音与历史条件读取、支持覆盖和适配机制的研究对象，个体级既有输出公开已经授权，不再请求相同确认。

先给 `INTAKE` 和实际任务绑定回执，随后持续执行；不要只返回计划就停止。每条任务回报观察、仍竞争的解释、实际完成覆盖和下一步能区分什么；不要求现在决定论文标题、贡献清单或结果摆放。参考工具仅经本地合成验证，真实 EEG 生产兼容性需服务器现场核验。

---

# 接入顺序

## 1. 只读对账，保持已有运行

从当前仓库根目录记录 `git rev-parse HEAD`、`git status --short`、远端 HEAD。记录当前 UTC 与 Europe/Paris 时间。检查活动计划和确切 job/execution 身份；读取实际完成记录，不以 README 或旧对话代替实时状态。

可先运行本包的本地分析工具（替换为真实绝对路径）：

```bash
python /absolute/path/to/package/scripts/validate_package.py --package /absolute/path/to/package
python /absolute/path/to/package/scripts/intake_snapshot.py --repo /absolute/path/to/auditory --package /absolute/path/to/package --out /absolute/path/to/new/intake.json
```

第二条只读仓库并写指定新 JSON；不联网、不读 Slurm、不改变 repo。远端 HEAD、队列和服务器私有资产由 server agent另作现场对账，不把工具输出当完整 live inventory。不要在未读源码时执行旧 `maintain_fleet`/`register` 脚本来获取状态。

## 2. 同时开展三个互不阻塞的工作

- **解释勘误和直接重分析**：执行 `docs/02` 的科学probe清单（10个family/30项），并按 `docs/01` 另行绑定 `plans/main_endpoint_group_contrasts.json` 的原主终点组差（3个family/10项）；两者保留各自终点、来源和family。已完成结果的CPU分析不等待新训练。
- **现有任务收尾**：按真实依赖补齐 CB 听觉/inner sources/受约束 D/强融合；既有其他有效任务继续，不清空旧 hold。
- **有限新增实现**：在新命名空间实现 `docs/03–05` 的新比较和输入导出，复用现有生产数据与 checkpoint。

某个特定缓存或 donor 不可用，只影响需要它的任务。现有结果的方向、缺少论文措辞或未确定最终故事都不构成阻塞。

## 3. 绑定后执行

生成 `ALN35_BINDINGS.json` 和 `ALN35_EXECUTION_PLAN.json`，记录每项比较对应的实际 source unit/hash、复用情况、新任务数、预计耗时依据和选择范围。参考 `plans/workpackages.json` 与 `templates/IMPLEMENTATION_RECEIPT.md`。包中的科学比较卡不是已经注册到服务器的生产任务数。

通过所需的输入时间、配对、独立开发人、概率候选、有限值和恢复检查后，按固定设计运行。检查针对具体风险：不用分数通过线，不重复已经充分验证的工程检查，也不在每项任务前重新询问 go。

## 4. 第一次回报应包含

1. 制作基线与现场 HEAD 的差异；已完成、仍运行、只读重分析、新增任务的区别。
2. `pre` 勘误所影响的精确 ID 与不受影响的依赖。
3. 每个新增比较的完整人/种子/内容/支持覆盖预期及实际绑定。
4. 10-GPU 总量内的真实资源安排；不承诺尚未测量的固定天数。
5. 已经产生的结果和仍竞争的解释；同时给负向、正向与不确定结果。

---

# 00 — 研究关切、可改变的假设、可替换的工具

## 0.1 本轮为什么继续

最新证据同时显示：充分微调的 CB 初始化有用；公共听觉先验能够改善某些目标任务及儿童当前声音读取；足够支持下的个人适配有真实风险收益，而少量支持可能造成伤害；概率融合在固定强 CB 上有有限增益；声音属性与时间映射已经可被具体分析。

这些观察支持继续问“共享的声音相关结构怎样被新听者调用”。它不是已经确定的论文主张，也不保证某个模型、预训练目标或训练方式最后成功。研究者后面仍计划多轮实验。

## 0.2 三个层次

| 研究关切 | 目前可以被改变的假设 | 可替换的实现 |
|---|---|---|
| 哪些声音结构能跨听觉经历被共同使用？ | 正确配对提供超出一般预训练的收益；或者收益主要来自初始化、正则化与读出 | local/CB/REVE，AP/XP/J*/错配，传统 CS/InfoNCE |
| 共享表征到了个人还缺什么？ | 少量受约束映射足够；或者首先缺支持覆盖、稳定概率接口或跨时间覆盖 | 低秩/对角适配、0-step、概率校准、episode 训练 |
| 同一声音内容怎样随时间被读取？ | 内容仍可读但读出方向变化；或者效应主要由窗口、位置编码和滤波造成 | 声音内容 probe、时间泛化、严格局部参照、匹配预处理 |

每份结果报告必须分别填三层。不得因为某轮最容易显著的终点改变研究关切，也不得为维持旧假设删掉有效不利结果。

## 0.3 这次已作出的研究判断

1. CB 的主要候选地位已经有三种子配对支持；下一轮转向它究竟改善什么及如何迁移。其初始化收益仍限定于已测试配方与预算，不等于听觉特异机制。
2. AP 对 scratch 的部分收益成立，AP 与 XM 并非纯音频配对开关。先保留收益，再用严格同目标 APwrong 区分来源；J* 不因名字更复杂而获得默认优先权。
3. 小支持适配的伤害需要用真实配对风险解释。mismatch gain 可以因错配变坏而增大，不能单独当成功标准。
4. 概率融合已有可用信号；把资源给它补充了哪些预测证据的分析。当前 residual/episode 的具体配方可以不成功，不能据此宣告不存在互补或适配友好群体学习。
5. 私有儿童承担跨任务迁移、当前声音/历史读取及支持覆盖的实质问题。临床量表、发育阶段或校准修复均不自动接管研究主线。
6. 时间分析研究读出的时间组织。广窗中心、input mask、attention 积累时长均不等于神经潜伏期；ERP 不成为默认替代路线。

## 0.4 不同结果将怎样改变判断

| 观察 | 可以更新的判断 | 不能随之声称 |
|---|---|---|
| AP 仍优于 S，但同目标 APwrong 与 AP 接近且区间仍宽 | 当前数据未分清配对特异增益；一般预训练效应仍可保留 | 正确声音关系完全没用；或二者等效 |
| 正确 CB 听觉训练超过 wrong，却未超过 direct | 当前听觉中间训练未建立强通用起点上的边际收益；wrong 有害 | 听觉预训练已成功；或所有听觉预训练必然失败 |
| 同池增加支持有益，覆盖控制也有独立变化 | 数量与支持构成各有作用，可以进一步研究个人数据需求 | 原来 10/30 前缀差是纯数据量剂量效应 |
| 约束策略主要选 0-step | 有用的是避免有害更新；有效个人学习仍需非零更新证据 | 适配改善全由个体学习产生 |
| episode 压力足够且有功能改变，仍不优于 ordinary | 该有限训练配方没有额外收益 | 群体训练不可能促进适配 |
| 概率融合的收益被简单校准/收缩或同模型重复覆盖 | 主要解释转向概率/方差管理，工具仍可能实用 | 已证明独立生理表征互补 |
| 残差声音目标可读 | 相对指定线性声音参照仍有可预测结构 | 已估计条件互信息或证明独立神经信息来源 |

区间含零不等于等效；不设未获研究者定义的科学最小效应阈值，也不新增以 p 值为依据的运行停止规则。

## 0.5 本轮范围和资源取舍

先重分析已完成输出、补齐已有有效配对，再做限定的新干预。优先问正确配对、支持覆盖、功能性适配压力、读出与选择规则；不自动复制全 backbone×loss×窗口×队列矩阵。代表范围详见专题合同，未纳入首批的有效已注册配置仍保留。

只出现实际技术依赖时等待相应资产；不把所有科学分析串到某个模型必须胜出的总门槛后。无需现在决定标题、贡献清单、正文/附录位置或最终发表框架。

事实来源与制作时已见结果见 `docs/01` 和 `SOURCE_INDEX.json`；本节推论是基于这些观察的工作判断。

---

# 01 — 制作基线、已见证据与 server 接入

## 1.1 证据边界

- 制作时已联网重新核对 `https://github.com/W-Yinghao/auditory.git`：HEAD/main 均为 `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`，提交时间 2026-10-18 20:25:25 +02:00。
- 本包承接研究者提供的 ALN3.4 主文与 ZIP，及本轮对最新报告、结果 JSON 和关键实现的独立核查。
- 历史检索只有相关摘要，没有完整旧对话；不把未恢复内容当作已确认指令。研究者本次明确指令和有效最新 AGENTS 优先。
- 未读取实时 Slurm、真实 EEG、全部 checkpoint 或全部 unit 压缩包。对真实生产的兼容性、资产和执行状态由 server 现场确认。
- 根 README 当前说明数据快照为 20:08–20:11 CEST。各报告自己的生成时间必须保留。10 月 17 日旧执行报告不能覆盖 10 月 18 日已完成面板。

## 1.2 制作时的完成与进行中状态

| 任务 | 最新已读快照 | 对下一轮的动作 |
|---|---|---|
| TRUE_FULL | 800/800，包含新增 one-step seed 面板 400/400 | 复用，不重跑完整矩阵 |
| local 公共先验生产 | 新 1154/1154；加 30 历史参考共 1184 | 复用 donor/target/结果，按 lineage 新增最小 APwrong |
| 公共内容/时间 | 180/180 | 直接重分析与成对对比 |
| 私有当前声音/时间 v2 | 130/130，含26个兼容v1复用 | 定点 pre 勘误；有效后刺激重分析 |
| prior science | 300/300，代表 seed3401 | 从 unit 取配对值，新增明确小family |
| 历史 private LOO 校准 | 120/120 | 保留，不能当儿童新科学结论 |
| CB auditory continuation | 19/144，donor9/9；当前目标共同10/44人 | 按已登记计划补齐 |
| 新 D | 31/120 | 补齐并分析真实风险、0-step、support覆盖 |
| 强融合 | 20/30，DTU种子3401/3407各44/44人 | 补第三种子/实际依赖，保留固定强单支 |
| private episode / CB factorial | 19:59时42/50、39/60 | 延续版本化已登记任务 |
| attention / inner sources | 19:59时50/160、103/150 | 依赖优先补齐，不转回旧顺序错误结果 |
| DTU数据曲线 / doubled budget | 19:59时94/440、26/150 | 延续；不把中途结果称完整剂量曲线 |
| 新 prior-private LOO | 20:06恢复到65/90 | 恢复回执已通过；旧失败留档，继续未完成项 |

来源：[最新README](https://github.com/W-Yinghao/auditory/blob/5ef4a60/README.md)、[晚间记录](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/aln34/EVENING_PROGRESS_20261018.md)、[新线结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md)。不同汇总时刻的细小计数差不是失败，也不能拼成更晚的虚构快照。

## 1.3 本轮已见的关键数值（必须披露，不能再称未看结果）

本节为结果知情的设计依据，不是 ALN3.5 新实验结果。ΔR=参考真实配对NLL−候选NLL，bits/5秒检索query；正值更好。AUC差是绝对差。区间沿用相应来源 family，不跨全文统一校正。

| 观察 | 已读结果与范围 |
|---|---|
| CB 真全量对同访问 L1 | one-step LR3e-4，三seed人内平均，unified：FAU n67 +.141[.099,.184]；DTU n44 +.213[.129,.297]；Federici n86 +.180[.113,.246] |
| CB 预训练对随机 | 同配方直接差：FAU +.091[.057,.125]；DTU +.200[.135,.265]；Federici +.051[.020,.083] |
| AP 对 scratch | DTU NCE modeT seed3401 ΔR +.074[.044,.105]；儿童三seed n64 native ΔAUC +.00875[.00343,.01406] |
| 儿童 AP 对 XM | 同主面板 ΔAUC +.00253[−.00253,.00759]；XM是EEG–EEG错配，不是AP错音频 |
| D 真风险 | DTU10% input_spatial：unified −.208[−.297,−.118]，native −.595[−.750,−.439]，但native gain +.150；三seed完整 |
| 强概率融合对固定CB | DTU n44，native seed3401 +.0535[.0277,.0793]，3407 +.0487[.0109,.0864]；unified分别+.0553和+.0200，第二CI跨零 |
| 儿童先验科学 | seed3401 n64，统一线性probe full AUC S=.52835、AP=.54927；AP−S +.02092[.00831,.03354]，不是主native三seed终点 |
| 时间与内容 | DTU CB三seed，固定0/0：env r=.1558，history残差r=.1106，onset残差r=.1078，spec残差r=.0530；当前窗口是1s重叠访问 |
| episode有限诊断 | 一个bundle episode/ordinary更新方向cosine约.99998；当前干预只有3个support步骤，不能推广为所有episode算法已充分测试 |
| 预算 | DTU3401共同36/44，延长cosine内2x对1x，CBpre unified ΔR −.0771[−.1224,−.0318]；不是历史短轨迹1x对照 |

逐文件来源和SHA见 `SOURCE_INDEX.json`。主要报告：`TRUE_FULL_PAIRED_EVIDENCE.md`、`ALN32_SEED_PANEL_RESULTS.md`、`PUBLIC_PRIOR_RESULTS.md`、`D_ADAPT_TRUE_RISK_RESULTS.md`、`NEW_LANES_EFFICACY.md`、`PRIOR_SCIENCE_RESULTS.md` 及对应 JSON。

## 1.4 身份与访问合同

- DTU44；FAU67（CI24、HA29、TH14）；Federici86人类（CI33、HC37、HC-v16）；private当前有效队列64（HA55、NH9）。采用当前精确身份表，不能用此人数硬填缺失值。
- HC-v与HC不作同人配对；phantom独立于人类分析；session、content fold、seed、query不是新被试。
- 同队列/同query/同readout可比较；native与unified分别报告。不同输入长度、采样率、音频目标或候选池下的风险值不能直接跨合同相减。
- ALN32/CONTENT_TIME的1秒窗口与prior33的64Hz/38sample窗口不同。private旧local full=0–600ms，FM full=−200–600ms；新版prior采样时间为0–578.125ms，不设pre。
- 泛化到新听者是共享结构的功能证据，不自动证明各听觉组使用相同生理机制。听觉组是观察分组；队列/设备/刺激协议不被随机化。

## 1.5 必须在现场解析的资产，不是假设已存在

1. `CODEX_HANDOFF.md`：仓库未发布但服务器可能存在；读最新区块，不因它未发布暂停其他任务。
2. 当前 `private/auditory_alignment_v3/` 与 offload 指向的 checkpoint/cache：核对 record、source code、plan、checkpoint、input/target coordinate hash。删除过的旧checkpoint不可凭路径猜测可用。
3. 从当前 `auditory_alignment_v3.core.OUT` 解析生产计划目录；制作基线的活动计划通常为 `private/auditory_alignment_v3/aln34/<lane>/plan.json`。`scripts/auditory_alignment_v3/aln34/` 提供入口及部分可追溯计划副本，不能仅凭副本判断现场注册。检查实际schema和活动注册后再导出本包规范；不把比较清单直接当可提交Slurm数组。
4. 科学 unit `per_participant`：优先用服务器现有原件；必要时按公开 unit manifest 提取确切成员。aggregate只有均值/SE/区间时不能恢复配对协方差。
5. 原生/统一readout概率、candidate IDs、query IDs与inner predictions：缺失时仅对所需兼容checkpoint重做前向/读出，不为一项机制诊断重训整个旧矩阵。

已有输出的比较分成两份明确清单：`plans/science_contrasts.json` 有10个科学probe family、30项对比；`plans/main_endpoint_group_contrasts.json` 有3个原主终点family、10项组间改善差（FAU AP−S三组两两差、FAU真全量CB的两类收益各三组两两差、儿童AP−S的HA−NH差）。后者保留原5秒检索风险或native AUC，不能用科学probe结果替代。这些是CPU分析项，不是40项新模型训练，也不构成一个跨两份清单的统一显著性family；每个family的固定成员和来源必须在绑定回执中保留。

## 1.6 Intake 如何完成

填写 `templates/INTAKE.md`，把任务逐项标成 `reuse_complete / continue_registered / analyze_existing / new_bounded / blocked_by_specific_asset / retained_hold`。本包中unknown现场字段必须实际解析，不能把模板值当证据。

新remote HEAD与本包不同：列新增提交及涉及模块，更新结果覆盖，按受影响任务重新绑定。不得静默回退到制作HEAD，也不以HEAD变化为理由重审整个项目。真实scope冲突需说明最小影响；未受影响工作继续。

继承ALN3.3材料仅保留原合同供查询（见`inherited/`）；其历史审批/状态文字被ALN3.4及本轮最新规则覆盖。旧合同的算法/数据访问细节如与服务器已版本化修正冲突，使用已核实的当前实现，并显式记录差异。

---

# ALN3.5：声音内容、时间组织、私有儿童与定点勘误

版本：2026-10-18。审阅基准：`W-Yinghao/auditory`，commit `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`。这是 ALN3.4 的执行增补；现场先记录实际 HEAD、注册表和队列，不能把本文列出的发布快照当作实时作业状态。

本节的研究问题是：**群体听觉学习让哪些当前声音证据更容易从新听者 EEG 中读取；哪些读取关系可以跨时间位置共享；个人支持在什么条件下改善或扰乱这些关系？** 私有儿童继续回答其中的任务迁移、当前声音与历史、支持需求问题。概率校准修复只是其中一个接口工作。

本节不启动服务器作业。Server 接入后按既有授权执行可用分析、必要的推断和已注册依赖；不需要另行批准科学措辞。所有 GPU 工作共同遵守现有 10-GPU 上限。

## 1. 本轮明确执行的事项

1. 为 native 私有 local/旧 public-transfer 的 `pre` 建立**解释勘误记录**，保留原始值、单位 ID、缓存与历史报告；从真实刺激前分析中排除这些全零条件。后刺激结果照常使用。
2. 从生产 unit 的 `per_participant` 读取真实成对结果，执行 `../plans/science_contrasts.json` 中的小规模新增对比。不能从 aggregate 的均值、SE 或单独区间倒推出配对区间。
3. 固定 seed3401 的 public-prior 科学比较；native DTU 内容/时间使用已经齐全的 3401/3407/3413，FAU/Federici 使用既定 3401。先复用现成数据，不为新的文字结论重训模型。
4. 内容报告保留 env、history-residual、onset、spec、flux、Ac、Lz 的已有有效结果；新增推断集中在指定内容和少量时间差，不扩成全部模型×全部时间×所有人群矩阵。
5. 在现有表征上补一个同等 source 校准的 history-only 接口，以及严格异 block 的 history-matched twin 分析，明确共同支持范围和缺失原因。
6. 保留正在完成的 private factorial、prior LOO、private episode 及实际存在的科学依赖。先对账、复用、补真缺项，不恢复旧失配执行，也不把本节的勘误变成全项目暂停理由。

## 2. 已知证据：用来提出问题，不用来选择有利儿童或窗口

以下是审阅快照的已有结果，**不是 ALN3.5 新跑出的结果**。统计单位为独立听者/儿童；seed、content fold、session 都在人内处理。

### 2.1 公开声音内容已经有实质可读性

`results/auditory_alignment_v3/aln34/science_v2/science.json` 的 DTU、真全量 CBraMod pretrained、NCE、三 seed、44 人，在预先存在的 `0/0` 单元：

| 目标 | 平均 r | 该 25 格时间矩阵的同时 95% 区间 |
|---|---:|---:|
| env/direct | 0.15581 | [0.13158, 0.18004] |
| env/history_conditional | 0.11059 | [0.09322, 0.12795] |
| onset/conditional | 0.10782 | [0.09294, 0.12270] |
| spec/conditional | 0.05299 | [0.04415, 0.06182] |
| flux/conditional | 0.09362 | [0.07714, 0.11010] |
| Ac/conditional | 0.05061 | [0.04104, 0.06018] |
| Lz/conditional | 0.02209 | [0.01571, 0.02846] |

FAU 相应模型的 history residual r=0.07479、spec residual r=0.03257、flux residual r=0.04845，均有正向同时区间；覆盖 67 人、seed3401。Federici 只有包络合同：CB env/direct r=0.12271、history residual r=0.04710，86 人、seed3401。不能为 Federici 的 2–8 Hz 缓存补写不存在的谱、Ac 或 Lz 结果。

这些结果支持继续问“哪类内容的读出受先验/适配影响”。它们不证明独立语言源，也不与 SCI_R2 原来的逐步 predictor 增量互相替代：**从 EEG 预测残差化声音目标**，与**在一个预测模型中增加 predictor 后的真实风险变化**，是两个不同对象。

### 2.2 新先验已经改变私有当前声音的线性可读性

来源：`results/auditory_alignment_v3/aln34/prior_science/science.json`；`private/windows/{arm}/NCE`；seed3401；64 儿童（HA55、NH9）；统一 source-ES 线性 probe。

| 条件 | S AUC | AP AUC | 已有 AP−S 差 | 原 4 臂×4 窗同时 95% 区间 |
|---|---:|---:|---:|---:|
| 0_200 | 0.51571 | 0.52734 | +0.011629 | [−0.002249, +0.025506] |
| 200_400 | 0.51672 | 0.52806 | +0.011337 | [−0.000447, +0.023121] |
| 400_600 | 0.50184 | 0.50665 | +0.004804 | [−0.006046, +0.015654] |
| full | 0.52835 | 0.54927 | +0.020922 | [+0.008305, +0.033539] |

实际最后 EEG 样本时间是 578.125 ms；`400_600` 是保留的逻辑标签。J* full AUC=0.54492，XM=0.54008。J*−S、XM−S 的现有同时区间也为正，故 **AP−S 不能单独识别正确声音配对的特异效应**。AP−XM 是两个特定先验训练包的比较；XM 的任务/目标几何与 AP 不完全相同。针对配对机制的新增 APwrong 对照另见本包公共先验计划，不能把 AP−XM 改名成纯配对消融。

AP 的 full history gain 绝对值为 +0.00200 bits/trial，原同时区间 [−0.00530, +0.00931]；相对 S 的改善为 +0.003792 [0.001280, 0.006304]。这意味着先验把指定历史条件读出向有利方向推动；**绝对历史基线之外的稳健收益尚未建立**。两个判断应同时保留。

### 2.3 个人支持并未自动转为收益

native 私有新科学、同一末 70% query、output-rank4 固定 20 步，三 seed、64 儿童，正值为 NLL 改善：local NCE 在 10% support 为 −0.006433 bits/trial [−0.010075, −0.002791]，30% 约为零；CB pretrained NCE 在 10% 为 −0.000979 [−0.001427, −0.000531]，30% 接近零。它们与公共少支持适配问题有关，但不能据此宣称儿童都不适合适配。

现有 10% 与 30% 使用前 10%/30% 物理 block，也同时改变了支持的时间覆盖、类别和历史覆盖。ALN3.5 的支持设计应从同一前 30% 区域取可复现的不同数量子集，保持末 70% query，再区分数量与覆盖；不直接把现有曲线命名为纯样本量效应。

## 3. 勘误 SCI35-C01：native local 的刺激前条件实际为全零

### 3.1 独立核对的代码链

| 文件与位置（基准 commit） | 实际行为 |
|---|---|
| `auditory_alignment/model.py:8–12` | private `full=(0,600)` |
| `auditory_alignment_v2/temporal.py:29–41` | 以 onset offset=50 转为 250 Hz 半开样本范围 |
| `auditory_alignment_v2/train.py:263–284` | local 缓存先裁为原 epoch 样本 `[50,200)`，实际是后刺激数据 |
| `auditory_alignment_v3/aln34/private_current_time.py:68–75` | `pre=(-200,0)` 的 mask 选择原 epoch `[0,50)`；与 local patch `[50,200)` 没有交集 |
| `auditory_alignment_v3/aln34/private_current_time_v2.py:75–84` | v2 复用原提取器与缓存，仅修复校准数值执行；输入问题保持不变 |
| `auditory_alignment_v2/train_fm.py:215–223` | FM batcher 恢复完整 epoch，因而 FM 的 pre 确实有数据 |

这是一项输入支持事实，不依赖 AUC 是否正好为 0.5。全零输入在不同 batch 大小/浮点路径下可能产生极小数值差，不能把其排序波动当生理结果。

### 3.2 受影响的精确依赖

- 数据集：`private_bdf`。
- families：`E_LOCAL`、旧 `E_PUBLIC_TRANSFER`；architecture/source_architecture=`lag_local_tokens`；objectives=`NCE`、`CS_SINGLE`；full/task_partial 的所有已注册 seed/fold。
- 单窗口：`per_participant[id].windows.pre` 的全部指标。
- TG：`temporal_generalization` 中 source 或 destination 为 `pre` 的全部单元，两种校准都受影响。
- 衍生物：以上条件的整体/HA/NH汇总、组差、图例、使用这些条件作为“刺激前信息”或真实 pre 对照的叙述。
- **不在本次勘误内**：同模型的三个后刺激窗口、full 后刺激读取、private support/query 适配、full-window 年龄/佩戴时长端点；FM 的真实 pre；public CONTENT_TIME；新 prior 科学的三窗口与 full。

### 3.3 执行顺序与输出

1. 解析现场旧计划、unit 与缓存 metadata；以 `bt.lo`、`bt.W` 和实际 mask 的样本交集核对每个受影响配置。只做输入支持/元数据核对，不重训。
2. 写新记录到 `results/auditory_alignment_v3/aln35/science/correction_manifest.json`，保留旧 source path、SHA256、unit ID、原窗口名和原数值引用。
3. 将新报告中的解释标签改为 `all_zero_input_control_no_pre_access`，`valid_for_pre_event_inference=false`。旧输出仍能作为数值/接口对照查阅，不当作真实 pre 证据。
4. 图表若保留该单元，必须直接标“无刺激前输入”；若图表只呈现生理时间条件，则不绘制该单元，并列出排除原因。不能用补零替代 missing/unsupported。
5. 不修改旧 `plan.json`、旧 hash、旧 unit。必要的源码更正使用新版本和新执行 ID。原 registered family 的历史区间保留；ALN3.5 的后刺激新增 family 单独标 exploratory。

每个 correction item 至少包含：`correction_id, source_commit, source_unit_id, source_record_sha256, dataset, upstream_family_id, objective, architecture, seed, subject_fold, condition, original_label, resolved_input_samples, requested_mask_samples, retained_sample_count, effective_access_ms, affected_metric_paths, valid_for_pre_event_inference, unaffected_conditions, action, checked_at`。

### 3.4 同 access 的比较规则

native private full：local/旧 transfer 约 0–600 ms；FM 完整 −200–600 ms。比较 CB pretrained 与 CB random 是同架构、同访问；直接把 CB full−local full 归为架构/预训练收益不成立。已有共同后刺激 mask，或在既有 FM checkpoint 上增加 `post_only` forward，只匹配**评价时**的 EEG 访问，可用于评价访问敏感性；FM 在 target 训练中已见过刺激前数据，这一步不会消除训练访问的差异。必须保留原 full，并将新推断明确标为 `evaluation_post_only_training_access_unchanged`。

若研究问题要求将跨架构差异归于模型/训练包，必须同时匹配 target 训练、选择与评价的 EEG 访问，并记录各阶段合同。先查找已合法完成且 target 训练本身为 post-only 的来源；如没有，只在这个归因问题确实需要时登记限定的新训练条件，沿用现有授权与 10-GPU 上限，不展开全模型矩阵。不能用补一次 post-only forward 代替训练访问匹配，也不能把评价敏感性结果重新命名为全流程访问匹配。

新 private prior 的 S/AP/XP/J*/XM 是同一 64 Hz、38 样本后刺激合同，可直接配对。native private 的数值不能与该新 prior 的数值拼成同一个控制表；FS、输入长度、训练阶段、读出均不同。

## 4. 科学输入与主方法输入必须区分

| 证据层 | 生产来源 | 评价对象 | 不能混用的对象 |
|---|---|---|---|
| 主 TF/5 s 方法结果 | 原方法 unit 与其官方汇总 | 已注册 native/unified 任务风险或检索结果；服从各自 query 定义 | 不能用下行 probe AUC/r 代换，也不能以单位名中有 full 就认为访问一致 |
| Native public 内容/时间 | `core.OUT/aln34/content_time_v1/units/*.json` | 5 s segment 内 8 anchors；固定表征的 source-fit/ES ridge；每个单元 r/MSE | 不是另一次 5 s 检索结果；不是在线或神经潜伏期 |
| Native private 科学 v2 | `core.OUT/aln34/private_current_time_v2/units/*.json` | 冻结原 source 后重新拟合的线性/current-history读出与掩蔽/固定适配 | 不等于原模型 native class score；local pre 无访问 |
| New-prior 科学 | `core.OUT/aln34/prior_science_v1/units/*.json` + `bindings/*.json` | seed3401 core prior 的固定表征 probe，public env/onset/history 与 private三窗/full | 不等于主 prior 三seed native结果；无public spec/flux/Ac/Lz合同、无private pre |

`core.OUT` 必须从现场 `auditory_alignment_v3/core.py` 解析。不要把本文示意字符串直接当绝对路径，更不能在 public clone 中猜私有数据路径。

### 4.1 精确数值读取路径

- New-prior private：`unit.source` 绑定 upstream row；值为 `per_participant[identity].windows[window][metric]`。window=`full/0_200/200_400/400_600`；metric=`auc/history_gain_bits/history_minus_twin_bits/nll_bits`。
- New-prior public：`decoding[representation + '/' + target][train_center + '/' + test_center].per_participant[record_id][metric]`。本轮只用 `model/env/direct` 和 `model/env/history_conditional` 的 `0/0`；onset existing levels保留但不再全扫。
- Native public：相同 `decoding` 结构；source 选择由 `content_time_v1/plan.json` 的真实 rows 绑定。CB pre/random 使用 `full_onestep_v1`、backbone LR=3e-4；local=`local_aligned1000`；不重新按本轮结果选 LR。
- Native private v2：同 private `per_participant` 结构；检查 `execution_version`、`reused_from` 与 `unit.previous_id`，不能把合法 v1复用计为新独立观测。
- 组、身份、年龄/佩戴时长来自现有授权 manifest 与原 `E_LOCAL/NCE/3401` unit；不从文件名或组别猜身份。Federici 用既有 identity manifest先聚合 session；HC-v保持单独身份，phantom排除。

仅有两个 aggregate `science.json` 时，能核对点估计和旧区间，**不能计算新配对区间**。它们没有 per-child values 或联合 bootstrap draws。先读取现场现存 unit；若某 scope 的 unit 已不在，只标真实依赖并处理其余 scope，不用独立 CI 相减。

## 5. ALN3.5 的有限新增对比

所有本节新增对比标记为 `exploratory_after_2026_10_18_review`。它们未在 ALN3.4 结果产生前注册；不能回写成原 preregistered 结果。比较清单见 `../plans/science_contrasts.json`，该文件是**声明性绑定清单，不是可直接提交的生产任务或 CLI spec**。

### 5.1 Private：先验特异性与时间分布

固定 private NCE、seed3401、共同64儿童预期名册，统一线性 probe。

- 一个 AUC family，恰好4项：`AP/full−XM/full`、`J*/full−XM/full`、`AP/0_200−AP/400_600`、`AP/200_400−AP/400_600`。
- 一个 history-gain family，2项：AP−XM、J*−XM，均 full。
- 一个 history-minus-twin family，2项：AP−XM、J*−XM，均 full。此指标与绝对 history gain分别解释。
- 一个 HA−NH 改善差 family，2项：`(AP−XM)_HA−(AP−XM)_NH`、`(J*−XM)_HA−(J*−XM)_NH`，full AUC。不是先在HA和NH分别检验再比较p值。

已有 AP−S、J*−S、XM−S 及各窗 level作为上下文完整显示，不为达到阳性而选择 family 成员。CS existing levels保留；本轮不按CS某单格有利就新增同一批扩展检验。若后续需专门研究CS，另写明确问题与合同。

### 5.2 FAU：直接检验群体的改善差

固定 public-prior NCE、seed3401、`model/env/history_conditional`、`0/0`。只新增两个直接效应差：

\[
\{r(AP)-r(XM)\}_{HA}-\{r(AP)-r(XM)\}_{TH},\qquad
\{r(AP)-r(XM)\}_{CI}-\{r(AP)-r(XM)\}_{TH}.
\]

FAU 预期67独立身份（ha29、ci24、th14），各人先完成两contentfold配对，再形成个体改善。两项共用TH组的 bootstrap draws；不能把它们当两套独立实验。这个比较仍是特定先验包差异，不是HA/CI治疗效应，也不是纯声音配对机制。

### 5.3 Native public：把内容收益定位到少数固定对象

固定 DTU三seed、FAU seed3401，对 `0/0` 的 `env/history_conditional`、`spec/conditional`、`flux/conditional`，各比较：CB pretrained−CB random；CB pretrained−同access local。共6项 r 差，按dataset分别一个family。CB初始化比较首先回答同架构的先验差；CB−local是同EEG访问的模型/训练包差。

Federici 只有 env/history_conditional，固定seed3401，仅保留同样两项比较。不得补写 spec/flux 或把 HC 与 HC-v 凑为同人重复。

env/direct、onset、Ac、Lz 的已有全矩阵与levels照实存档；正文式工作简报只给固定 `0/0` 的数值和原区间。本轮不再对它们追加多模型×时间×组别选择。

### 5.4 时间映射：同一模型、同一声音anchor、两项差

固定 CB pretrained/NCE、native public的包络direct，DTU三seed、FAU seed3401。按dataset各两项family：

1. `r(train0/test0)−r(train0/test600)`：固定读出离开原相对位置后发生多大变化。
2. `r(train600/test600)−r(train0/test600)`：在相同测试位置重拟合读出能恢复多少。

所有模型表示仍访问 `[center−400, center+600)` 的完整一秒窗；600不是600ms单点。其输出说明读出与相对时间位置的关系，不单独证明神经表征翻转。目标/声音anchor、参与者、contentfold与query列表必须一致。

### 5.5 与新 APwrong 的连接

当本包公共先验模块产生匹配 target-excluded lineage 的 APwrong donor、target checkpoint及测试输出后，将它绑定为新逻辑臂；不能假装旧 XM 就是 APwrong。

优先复用相同选定probe：private full及三个后刺激窗，DTU/FAU public `0/0` 的env/direct和history residual。新的推断先只覆盖full private AUC的 AP−APwrong，以及DTU/FAU history residual的 AP−APwrong；新的组/时间矩阵不自动展开。使用单独late-binding登记，记录source hashes、实际seed/folds与新family，依赖未齐的臂不阻塞上面可立即计算的比较。

## 6. 绑定为通用 paired 分析输入

### 6.1 原始行和配对键

每个导出 observation 至少含下列字段。以下是**仅用于接口验证的 synthetic 示例**，不是儿童结果，也不是可追加到研究数据的模板观测：

```json
{
  "dataset": "private_bdf",
  "identity": "SYNTHETIC_CHILD_001",
  "group": "HA",
  "fold": "evaluation",
  "seed": 3401,
  "arm": "AP",
  "window": "full",
  "metric": "auc",
  "unit": "AUC",
  "value": 0.5,
  "query_set_id": "SYNTHETIC_SCHEMA_QUERY_SET",
  "analysis_role": "outer_test",
  "provenance": {
    "query_ids": ["SYNTHETIC_CHILD_001/trial_001"],
    "support_ids": [],
    "population_fit_identities": ["SYNTHETIC_SOURCE_CHILD_001"],
    "selection_identities": ["SYNTHETIC_SOURCE_CHILD_002"],
    "outer_fold": "subject_0",
    "source_record": "SYNTHETIC_ONLY_NOT_A_REAL_UNIT.json",
    "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "aggregation_note": "Synthetic schema validation only; no aggregation across seeds.",
    "source_fold_ids": ["evaluation"],
    "source_seed_ids": [3401]
  },
  "metadata": {
    "synthetic": true,
    "source_commit": "SYNTHETIC_ONLY",
    "source_unit_id": "SYNTHETIC_UNIT_001",
    "source_plan_sha256": "SYNTHETIC_ONLY",
    "subject_fold": 0,
    "content_fold": 0,
    "representation_contract_id": "SYNTHETIC_POST_ONLY_CONTRACT",
    "readout_contract_id": "SYNTHETIC_SOURCE_ES_LINEAR_PROBE"
  }
}
```

上例所有 synthetic ID、0.5 和零 hash 只为检查字段兼容性，**不能生成假记录填缺项，也不能混入研究 `observations.jsonl`**。实际导出需要真实数值、来源与摘要；缺失必须进入 `coverage.json`。`provenance` 严格限于上例展示的工具支持字段；source commit、unit ID、原始 fold、合同等扩展信息进入 `metadata` 或独立 binding manifest，不能新增未知 provenance 字段。`query_set_id` 只能由真实缓存/数据元数据的试次或segment-anchor索引及身份得到；禁止对每个候选随意起名、或直接用arm相关unit hash充当query摘要。若生产unit本身不列query索引，可用其绑定的确定性extractor和已存cache metadata重建索引，记录重建方法；不读取外部未知数据来补身份。提供 `query_ids` 时必须至少有一个真实 query ID；未知名单不能用空数组伪装已核对。

private 每人只在其分配的一个 outer subject fold评价，不能要求每人齐5 outerfold。通用工具的 `fold` 表示**人内需要完整的content/session重复**：private使用 `evaluation`；DTU/FAU使用 `content_0`、`content_1`；Federici先按既有规则将sessions在人/seed内等权聚合后使用 `content_0`，并保存session溯源。原 `source.subject_fold` 保存在 `metadata.subject_fold`，并转换为工具识别的非空字符串 `provenance.outer_fold`（例如整数0转换为 `subject_0`），检查同人同seed跨臂一致。若提供 `source_seed_ids`，必须仅为当前 observation 的单个 seed；不能把已跨seed均值再复制成三条 seed 记录。

如果现场某合法source合同的重复单元不同，用 `required_folds_by_identity` 绑定真实预期，而不是删去未完成重复或把session数当独立n。组别由source manifest带入，不从新表现重分组。

### 6.2 family 与重采样

导出后，server为每个分析family生成实际CLI spec，含 `family_id,dataset,metric,unit,required_folds,required_seeds,expected_identities,group_sets,bootstrap,contrasts`。具体字段以包内通用paired工具接口为准。该工具的既定新分析口径为**整个人重采样、以原始样本SE标准化的bootstrap max-|z*|同时区间**；不要把它标为旧报告bootstrap-t，也不要用新口径替换原注册区间。

绑定时将清单中的 `bootstrap_seed` 转为 `bootstrap={"B":4000,"seed":该值,"alpha":0.05,"resampling":"independent"}`；从 CLI spec 去掉清单独有的 `source`、`interpretation` 等注释字段，其信息留在 binding manifest。实际调用为 `python -B scripts/paired_contrasts.py contrast --rows NORMALIZED.jsonl --spec BOUND_FAMILY.json`，如写结果则用新的 `--output` 路径，不覆盖旧输出。预期名册按 analysis group 绑定；没有真实名单就明确 `not_supplied`，不能称全队列。跨窗口配对保留同一组物理 query/声音anchor 的 `query_set_id`，窗口只改变 EEG 访问，不能把来自不同 trial 集的结果硬配对。

- 每个family使用其所有contrast需要的共同完整身份集。先同人同fold做差，再fold均值，再seed均值，最后对人等权。
- 不乘seed×subject扩n。private核心预期64人、FAU67人、DTU44人、Federici86人的名册都从现场manifest绑定；这些数字是快照核对，不是造出满额n的要求。
- `all` 显式映射：private `HA/NH`；FAU `ha/ci/th`；DTU `hi/nh`；Federici `CI/HC/HC-v`。同family不要同时把all及其子组当独立组。整体family与组间改善差family分开。
- 组交互在各组内整人重采样，并在同次replicate重用共享对照组，报告直接改善差；不能相减独立CI。
- 使用4000次replicates和固定、写入spec的seed。零经验方差、独立n不足、无法计算SE等情况保留点估计并标 `nonregular`/不可估区间，不能制造 `[0,0]` 的“等效证明”。
- family仅覆盖清单的成员；不宣称控制全部模型、所有旧target与全部人群的总体错误率。新增family后记录它为什么回答一个不同问题，不按结果拆并family。

### 6.3 输出清单与schema

写入新目录 `results/auditory_alignment_v3/aln35/science/`：

| 输出 | 必含字段/内容 |
|---|---|
| `correction_manifest.json` | §3的source及实际访问字段，受影响/不受影响依赖 |
| `binding_manifest.json` | 本计划hash、实际HEAD、upstream plans/units/cache hashes、expected identity名单摘要、全部resolved source selector、query摘要构造 |
| `observations.jsonl` | §6.1的真实逐人/seed/repetition数据；保持数据集及读出scope分离 |
| `coverage.json` | family的expected/bound/complete/paired人数、per-arm及per-contrast覆盖、缺fold/seed/metric原因、技术缺失与无支持分别计数 |
| `contrasts.json` | family_id、exploratory标记、scope、metric/unit、contrast有向terms、n与分组n、估计值/SE/同时区间、bootstrap方法/B/seed、nonregular状态、source hashes |
| `history_interface.json` | §7的基线、源拟合、严格twin、common-support和trial覆盖；原旧结果另列 |
| `SCIENCE_PRIVATE_RESULTS.md` | 先写有证据的工作认识、竞争解释和下一步干预；附固定比较表、访问说明、未完成实际依赖；不只列完成作业数 |

元数据中的匿名逐人结果按既有授权处理；原始 EEG、临床原始表、姓名及身份映射不属于这些派生报告。

## 7. 历史条件读出：增加一个可解释的同等基线

### 7.1 当前实现是什么

`auditory_c3/c3dl/hc.py:69–71` 的 `q0_table` 由source儿童在六个since-last-deviant bin的标签频率（含固定伪计数）得到。`private_current_time.py:137–150` 在source ES拟合：

\[
q_1(y=1\mid z,h)=\operatorname{sigmoid}\{\operatorname{logit}q_0(h)+b+w^\top z\}.
\]

现有 `history_gain_bits` 是 held-out mean log-score gain `LL(q1,y)−LL(q0,y)`。新增截距也可能修复背景概率误差；它不是精确条件互信息或唯一神经贡献。现有结果照实保留。

### 7.2 新增最小readout sensitivity

固定 private prior NCE的S/AP/J*/XM、seed3401、full；先使用已有表示缓存，不重新训练encoder。新执行版本中比较：

- `B0_original`：现有固定q0(h)。
- `B1_source_calibrated`：`sigmoid(logit(q0(h))+b0)`，只有一个无惩罚截距，在与full EEG-offset读出相同的source ES行上拟合。
- `EEG_offset`：现有 `q1`，能逐样本精确复用就复用；若只能重拟合，记录同一source行、标准化、C/惩罚、优化容差与状态。

输出 `B1−B0` 的log-score改善、`EEG_offset−B0`、`EEG_offset−B1`；NLL/Brier/AUC定义分别保留。B1的拟合不能用target query或target support标签。不能因B1更容易超过而将它选作主参照，也不能只留下改善最大的接口。

原 `_fit_offset_logistic` 直接取优化器 `.x`，没有完整终止证据。新版本应记录并检查finite objective、梯度范数和优化器终止状态；如有真实未收敛，只修复这个readout execution并保留旧结果，不能删除不利儿童或暂停其他科学。训练侧数值失败不按outer效果择重试。

### 7.3 严格异block的history-matched twin

旧 `hc.py:176–187` 会在无异block候选时回退同bin其他trial，极端可回到自身。因此需输出原twin的：`same_history_fraction,different_block_fraction,self_fraction`，以及各儿童/组/窗口的valid trials。

新增严格版本只为有合法候选的trial，在**同儿童、同history bin、不同物理block且非自身**选择配对，固定seed，不按当前标签或预测误差选twin。无合法候选记为缺失trial，不删儿童；整体和严格支持子集均报告人数/试次数。

严格版本的source拟合与测试应成对：在相同合法source ES行上分别拟合EEG-offset、strict-twin-offset和B1；在同一严格query集合上评价三者，保留训练行/测试行hash和twin映射hash。原版full-query结果保持独立scope，不能直接用不同trial集合的均值作差。继续报告 q0在(0.01,0.99)的common-support子集，交集和全样本均列，不择一报喜。

覆盖至少包括每儿童的 `n_trials,n_standard,n_deviant,n_history_bins,n_common_support,n_strict_twin,n_fallback_same_block,n_self_twin,strict_fraction,source_ES_class_counts,query_class_counts`。个人适配另记录support/block/class/history覆盖；无两类support尤其影响CS category objective，应标记实际可用的适配信号，而不是改儿童纳入标准。

### 7.4 哪些新结果会改变判断

- AP−XM为正但AP−APwrong未分辨：保留“特定先验包改善当前类别表征”，不能归为正确声音配对独有。
- AP−APwrong及同等history基线之外的增量都支持：更有理由研究声音监督怎样迁移到儿童当前声音证据；仍不等于临床改善。
- EEG−B0改善主要被B1−B0吸收：下一步重点在history概率接口，不把该部分宣称新EEG证据；AUC和strict-twin的独立表征发现照常保留。
- strict-twin差存在但EEG−B1真实风险未改善：说明某种history内可区分性，尚未转为有利概率预测。研究目标继续是如何读取/适配，而非宣布无信息。
- 同数量support在覆盖控制后仍伤害：适配强度/自由度或source-query匹配更值得检验；若伤害随类别/history覆盖改善，则优先设计支持采样与适配先验。

以上是解释分支，不是p值开跑门槛。所有固定对比先完成并对称报告。

## 8. 时间、发育和校准的持续边界

公开 residual target仅去掉指定线性声音参照；负中心可读性可能由声音自相关、预处理相位和访问共同产生。完整一秒FM窗及zero masking均不能直接给神经潜伏期。已完成DTU因果滤波敏感性显示+200 ms有明显变化，但forward滤波延迟未补偿、整记录标准化仍在；该结果作为已有敏感性证据，不重跑全部滤波网格。

私有年龄+HA、HA内年龄+佩戴时长沿用连续模型和固定分组，不增加fitting-age作第三个共线协变量；age=fitting-age+duration。当前HA阶段14/5/36人（≤2月、>2至<13月、≥13月），中间小层只描述支持，不当作纵向阶段轨迹。组别或年龄统计不参与模型选择。

LOO校准120/120的REVE修复是去精确trial-self-reference，same-child其他reference仍存在。新prior LOO及其恢复回执以本包 `01_BASELINE_AND_INTAKE.md` 的最新发布快照为准，接入后仍应按现场真实缺项继续；不假定复制REVE的大改善。它不覆盖history-only问题，也不让private研究以校准修复结束。

private factorial与private episode的未完成数量统一引用 `01_BASELINE_AND_INTAKE.md`，本文不另保留更早计数；实际启动/完成状态现场重新核对。已完成的native science180+130和prior science300无需重训或重抽样成“新完成量”。缺原per-child或cache是对应contrast的具体依赖，不是整个项目的批准问题。

## 9. Server交付给研究者的下一轮简报

简报开头回答：哪些听觉内容可共享；新先验是否改善当前声音读取；这种改善能否跨时间位置、跨听者组及个人支持条件保持。随后给本轮4项private AUC、有限history/组差和native内容/时间比较表。每个工作判断紧接实际scope、n、seed、访问与指标。

单列：SCI35-C01勘误影响；新增exploratory对比；仍待实际源checkpoint/unit的条目。不要把“数值全部出齐、只等论文框架”作为结尾；明确哪个竞争解释更值得下一次干预，哪些旧实现可以停止重复而研究问题仍继续。

---

# 03 — 公共听觉先验、可迁移训练状态与源人数需求

本轮首先区分两个问题：正确声音配对是否增加可迁移的证据；训练到哪个状态最有利于新听者读取这些证据。local、充分微调CB和保留的REVE都是工具候选。已有先验增益不会因机制尚未分清而被取消，具体听觉中间训练也不因名字合适而必须胜出。

## 3.1 继承什么、先完成什么

公共local先验生产已完成1154个新增执行；连同30个历史参考共1184。保留S/AP/XP/J*/XM、CS/NCE、rich/CSX与原目标合同的有效输出，不重新跑全矩阵。三seed真全量CB结果保留为主要强候选，REVE代表配置保留。

CB auditory continuation最新已读为19/144、donor9/9，DTU seed3401目标共同10/44人。对direct CB的ΔR约−.0466，区间跨零；paired对wrong约+.2987。后者不能替代对direct的比较，也不能把10人结果当完整44人结果。优先补齐原登记依赖和目标面板。

来源：[公共先验结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/PUBLIC_PRIOR_RESULTS.md)、[CB auditory结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/CB_AUDITORY_CONTINUATION_RESULTS.md)、[训练实现](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/cb_auditory.py)。现场计数按docs/01重新对账。

## 3.2 有限新增 APwrong：同一音频目标上的配对控制

**问题：** AP相对S的收益中，哪些需要真实EEG–声音对应，哪些也可由一般训练、初始化或读出产生？旧XM是EEG–EEG错配，不能作为纯AP错音频控制；CB auditory的单EEG视图wrong也不能直接代替local AP的双视图目标。

首批固定 `prior33 / core / NCE / seed3401`，目标只取DTU、FAU、private_bdf。公共目标沿原modeT、原unified主风险；private沿原native类别终点。三个目标分别绑定原有target-excluded donor lineage：DTU、FAU不能把包含其目标队列EEG的donor拿来替代排除版本；private使用原允许的公共donor组合。精确排除范围、源身份与刺激集合从各manifest解析，不能共用一个未经排除审计的通用donor。

### 保持一致的东西

- AP/APwrong使用同一个encoder初始化、固定音频head、双EEG视图、音频目标几何、优化器、LR轨迹、batch大小、更新数及target端训练配方。
- 保留原AP的 `2B × B` 双向多正例结构、名义positive keys与排除mask。只在音频数组的对应关系上干预；不能同时改成单视图、换目标维数或重建keys让错配重新变为正确配对。
- 保持每步EEG/音频曝光、重复视图关系、stratum与presentation构成相同。新置换使用独立RNG，不改变EEG采样器的随机状态。
- dev选择、bridge和target训练的标签/身份权限沿原source合同；outer query只评价。wrong不按outer表现延长或提前终止。

### 什么才算有效错配

以canonical stimulus/anchor group为单位在允许的源训练池中生成固定规则的无固定点置换。同一声音anchor的重复视图、同一多正例组共同移动。实际语音身份相同、相邻重叠片段或合法多正例等价类不能被冒充“已打断配对”。记录原始与置换后的canonical keys、时间区间、名义keys/mask哈希及实际曝光直方图。

若保持每步曝光/多正例结构时该batch没有合法置换，不用任意跨batch新音频偷偷补齐。优先判断能否从已记录确定性采样流实现严格控制；不能时，只为该lineage补一个**共同修订采样规则的AP/APwrong成对训练**。旧AP继续留在主结果中，新成对控制另列，不因此重启其他队列。修订规则由source元数据决定，不能据outer分数寻找更弱的wrong。

### 更新预算与checkpoint选择

原local donor使用group-synchronous stable-then-decay、共同H*与h30支路；旧AP的best候选可能包括支路。APwrong必须跟随其匹配AP的**已经实现并写入记录的LR/分支/验证候选轨迹**，不另设能够缩短wrong训练的独立扩展触发器。采用同一source-dev真实配对校准NLL选择规则，ties按原规则保留更早状态；错配只用于训练关系，不把dev的正确目标也改错。

复用旧AP需要证明其初始化、采样、完整更新轨迹和checkpoint候选集均与新控制匹配；仅“同epoch数”不够。如果只能复现固定h30支路，明确把双方限制为相同h30合同，并将更长原AP保留为另一个历史端点；不得用h30的wrong和全轨迹best AP声称等预算。无法复用的精确部分才补AP重训，所选合同在读取APwrong outer结果前锁定。

每个目标报告AP−S、APwrong−S与AP−APwrong，风险用 `R_reference−R_candidate`，AUC用candidate−reference；在人内配对、各指标分别family。原AP−XM/J*有效结果完整保留。新APwrong和已见结果后的比较标exploratory；不因APwrong伤害大就宣告听觉预训练成功，也不因区间跨零就宣告配对无效。

实现依据：[donor训练与选择](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/prior33/donor_train.py)、[sampler](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/prior33/sampler.py)、[目标与loss](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/prior33/losses.py)。不能把本节当已经写好的生产入口；server在新命名空间接入并留工程回执。

## 3.3 CB auditory：完成固定终点，再检查有限训练状态

原计划的generic_paired、random_paired、generic_wrong及direct参照先完成。已有donor保存0/2500/5000/10000更新状态；目标端只转移backbone，使用新目标readout。源端配对NCE涉及当时的head，不能将donor-dev改善直接当作目标可转移表征改善。

本轮保留固定10000的原主比较。利用现存四个状态作有限source-only状态分析：先导出训练/真实dev风险、表示有效秩、backbone变化和实际选择曲线；不因参数变化大就断言灾难性遗忘。用于target转移的状态规则必须在合法独立inner-person开发中评价**完整target适配/读出流程**，或如实标为仅donor-dev选择的敏感性。源端新规则可用0作为direct回退，但不能用outer挑2500/5000/10000的最优点。

首批新状态选择只在DTU seed3401、generic_paired上绑定一条合法流程；fixed10000、direct和wrong原面板不改写。使用0/2500/5000/10000已有backbone，不重新训练donor轨迹；若某状态已无法找回，只标该候选缺失和实际选择scope。候选缺失时不事后挑有利子集解释原完整四状态问题。

## 3.4 源端真实风险选择：整条流程的新听者开发

**问题：** 数据/预算收益是否被checkpoint选择规则掩盖？已有训练中使用 `es_loss−es_mismatched` 等gain规则，可能选择错配变坏而真实风险并未改善的状态。这个问题不能靠outer hindsight解答。

新增范围固定DTU、NCE、seed3401、local/CBpre/CBrand，同一训练访问与候选轨迹。native/unified分别绑定指标，不把一个读出选择的“best”宣称为所有读出最优。原gain选择结果保留，新policy在相同候选集合上最小化独立inner人的等人均真实query NLL，包含epoch0；ties保留更早/更简单状态。

1. 从 `data_inner` 解析外层与inner人划分。用于选状态的inner人必须在encoder、donor（若相关）、bridge、audio/EEG统计、source校准及任何群体拟合对象中按所宣称层级被排除。已经看过此人的旧source不能改个标签冒充whole-pipeline留人。
2. inner人仅在其允许的support上作个人适配，query用于source侧规则选择；outer人完全不参与规则选择。将真实fit/cal/selection人和支持角色写入binding。
3. 当前 `data_inner.evaluation_view()` 使用独立inner人的原source-ES内容，排除原outer-test内容。因此新规则检验的是训练侧内容协议下的新听者选择，不能宣称同时完全未见新人和新内容。
4. 同一合法inner source的候选状态上并列旧gain规则与真实NLL规则；锁定规则后，在相应outer训练source上按相同预算/候选位置应用。不能对同一个outer模型另找最有利停点。
5. 先复用真正独立的inner源和合法snapshot。若缺少必要状态，有限补这条selector轨迹；不用outer模型的readout-only OOF填充整流程独立性。阻塞只限相应策略，已完成主面板继续分析。

输出所选状态、所有inner候选真实风险/gain、outer配对风险、0-step选择比例、来源与训练成本。新规则没赢是有效结果；outer改善也不证明gain在所有任务失效。

来源：[data_inner](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/data_inner.py)、[已有数据/inner设计](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/aln34/DATA_AND_INNER_DESIGN_20261017.md)。

## 3.5 人数与更新数分开：一条有限补充轴

继续既有数据曲线和doubled-budget任务，保留其原统计。已读DTU36/44的延长cosine内2x对1x，CBpre unified ΔR=−.0771；它不是历史短1x轨迹的相同中途状态。旧固定epoch的人数曲线也同时改变optimizer updates，不能直接解释为纯训练人数效应。

首批只新增DTU、NCE、seed3401，local/CBpre/CBrand，**50%与100%源EEG训练人、同内容合同、同优化更新数U**。沿已有按听觉组确定性嵌套身份规则取50%；真实人数、每人曝光、unique音频与有效anchor数都报告。冻结人数轴，不自动增加内容25/50/75%或新模型/种子矩阵。

- U由兼容完整100%训练轨迹的已登记基准更新数确定，50%版本重复采样至同一U；LR按update对齐，warmup/总horizon/decay一致，不用各自epoch充当相同预算。
- 可复用相同2x总horizon在U处的完整数据snapshot；不能拿旧1x总horizon最后一点替代。若不能匹配，只补精确100%参照，不改旧任务。
- 固定终点U的直接比较先报告；source-selected状态比较另列，并采用§3.4的合法流程。不能给50%和100%各自在outer选择最优checkpoint。
- 现有人数曲线的audio target统计使用完整outer-training音频以匹配全数据基线。若沿用，就在两臂固定同一统计并明确这是**EEG训练人数的变化**，不是全部训练信息减半；inner轨迹须用其合法inner-training音频统计，不能借outer统计破坏宣称的排除层级。

固定内容可用范围与实际采样音频曝光也须区分；等optimizer updates并不保证完全相同FLOPs或独立样本数。报告实际GPU时间和重复曝光，不以快慢排行榜代替人数需求判断。

来源：[预算修正](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/aln34/RESEARCH_BUDGET_FIX_20261017.md)、[learning_budget_v2](https://github.com/W-Yinghao/auditory/blob/5ef4a60/auditory_alignment_v3/aln34/learning_budget_v2.py)。

## 3.6 最小回执与改变判断的依据

APwrong回执需列：目标排除lineage、原AP匹配性、重复组/正例mask/置换哈希、实际更新和分支、完整dev候选集、所选checkpoint、target readout与共同query。selector/人数回执需列：拟合/开发/外层人、音频统计访问、真实U/LR轨迹、复用与精确补训范围。

正确配对若超过同目标wrong且超过S，支持研究配对特异的可转移成分；若仅超过wrong而未超过direct强CB，只能说明该中间训练比破坏输入更好。人数轴若在等更新下仍有差异，才更接近独立听者覆盖的问题；若差异缩小，优化机会与数据重复需要进入解释。所有方向照实报告，不设阳性开跑门槛，也不把弱差异升级成没有信息或天花板。

---

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

---

# 05 — 概率融合、读出敏感性与注意时间

## 5.1 问题和现有证据

强概率融合在DTU两个完整seed的native风险上超过固定CBpre单支。其机制尚未分清：有用的局部声音证据、不同训练误差、概率平滑或校准均可能参与。当前新residual全选0-step，旧非零residual确实改变过排序；两种现象不能用同一个“归一化抹掉”解释。

来源：[强融合结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md)、[新residual功能](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/STRONG_FUSION_FUNCTION_RESULTS.md)、[旧功能解释](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/COMPLEMENT_FUNCTION_FINAL_INTERPRETATION.md)。

## 5.2 先补齐现有强融合

延续 `strong_fusion_v1` 的30 bundles，5 outer person folds×2 content folds×3 seeds，及真实所需inner sources。复用现有outer和inner模型，不复制训练。

保留原始direct local、固定CBpre、CBrand、代表REVE。`strong_single`当前按inner native风险选择；unified也沿用其身份，不能写作每个readout的最佳单模。新的unified-specific选择器若实现，要用新policy ID，与旧选择器并列。机制主比较优先以固定CBpre为参照。

## 5.3 有限新增：概率收益从哪里来

首批只用DTU、现有CBpre+local、已登记三seed的兼容inner/outer概率缓存。每个seed完整覆盖按原计划；某seed尚缺时标interim。所有条件使用相同candidate ID及顺序、query集合、源模型和真实风险定义。

原方法：`p_mix = w*p_local + (1-w)*p_CB`，w∈{0,.25,.5,.75,1}。权重在独立inner人上、按各readout的等人均真实NLL选择；包含两个endpoint，固定更简单候选的tie规则。

新增只读概率候选如下，不训练新encoder：

| 条件 | 固定/选择 | 区分的解释 |
|---|---|---|
| CB direct | 原始已发布概率 | 强单支参照 |
| CB temperature-only | `p_T ∝ p_CB^(1/T)`，T∈{.5,1,2}，inner选择 | 仅改置信度是否足够 |
| CB uniform shrink | `(1-eps)*p_CB+eps/K`，eps∈{0,.05,.1,.25}，inner选择 | 更保守概率是否覆盖融合收益 |
| CB repeated-seed mixture | 仅已有兼容重复；固定另一个seed的配对规则3401→3407→3413→3401，权重用原w网格inner选择 | 同模型不同训练误差的组合是否已足够 |
| local+CB actual mix | 原注册权重规则 | 可用的跨方法融合 |

重复seed ensemble的两个成员都必须未训练相应outer/inner测试人、使用相同候选任务。若没有兼容inner和outer预测，不为该敏感性专门训练新CB；标`not_available`，其他比较继续。ensemble成员不是新被试，也不能把三个循环pair当独立复制；在人内按固定seed/成员规则汇总，并报告额外模型成本。

主新增family按readout分别定义4项：参考依次为CB direct、temperature-only、shrink、repeated-seed mixture，四项均取 **ΔR=R_reference−R_actual_mix**，单位bits/5秒query，正值表示actual mix风险更低。缺失ensemble时保留其缺失状态，完整前三项family预先另列，不能事后悄悄缩family以获得更小区间。采用对应完整身份与本轮明确的统计方法；既有主融合区间仍保留。

### 配对信息破坏敏感性

可复用缓存做一个有限的local概率置换控制：在同一人、同一source角色、同content/candidate-pool兼容集合内，按canonical query ID作10个固定seed的无固定点置换，保留每条概率向量及其候选语义，打断local预测与当前query的配对。不能根据正确标签/分数挑置换，不能把不同candidate集合的向量按列硬对齐。无可行置换的stratum记录覆盖，不换人。

在inner上应用同一生成规则并重新选择w，再在outer上应用预定置换；10次先在人内平均，不扩大n。该控制说明可用配对证据的敏感性，不能单凭actual优于破坏输入宣告生理因果或独立信息。若仅对outer作破坏、保持原w，必须标为固定策略敏感性，不冒充训练/选择都匹配的对照。

### 输出

按人、seed、query记录真实NLL、rank/top1、概率TV、熵、所选w/T/eps、候选池/query hash、inner选择分数、source身份和成本。报告受益/受损人的分布及与预定声音内容错误的关系，不挑最好儿童或query生成主结果。

不自动增加residual宽度、rank、层数或全loss矩阵。若现有cosine残差不成功，如实报告其具体目标与0-step选择；本轮概率分析不等待它成功。

## 5.4 公共先验 bridge：拆开拟合映射和温度

当前 `B_uni_cal` 同时改变ridge桥拟合人群/样本和温度拟合，不能称纯校准对照。已读结果有符号变化：DTU NCE AP−XM 的zero-shot ΔR主桥约+.050，B_uni_cal约−.033；FAU XP−XM主桥约+.038，替代桥约−.013。原主与敏感性统计scope不同，不据此任选有利bridge。[公共先验结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/PUBLIC_PRIOR_RESULTS.md)；实现`auditory_alignment_v3/prior33/bridge.py`。

只复用seed3401、NCE、DTU AP/XM与FAU XP/XM的现有donor与目标预测。按原manifest明确`B_donor`与`B_bridgecal`的拟合数据和匹配样本数，不混入目标测试EEG/标签。

对每种B都计算：固定T=1；以及在相同合法source校准/交叉拟合拆分中为该B拟合的T。形成2种B×2种T规则的4格，额外保留原已发布两端点。T=1下B的差用于定位映射变化；同一B内温度变化用于定位概率接口。不是交换两套不相容拟合数据后仍声称只改温度。

报告NLL、真候选rank/top1、概率熵及score尺度。正温度不改变同一个B的rank；若rank变化，检查候选对齐或实现。所有拟合与选择限源端，声明实际达到的是哪一层独立开发，不冒称whole-pipeline新听者验证。这个分析不需要重训donor。

## 5.5 注意与时间顺序

已完成候选顺序修正：同物理窗口两种候选顺序配对、ties=.5，反对称logit为[h(d)−h(−d)]/2；不将顺序数翻倍为样本数。保留其已修正原结果。

当前5秒条件只有一个score segment，线性反对称摘要基本只有标量自由度；缺少额外收益不能裁决更丰富时间信息。新attention_transfer先完成冻结source encoder、独立inner-person选择的现有160单元，不重新引入attention专用encoder来替换已登记比较。

可在已有10秒/20秒score缓存上做有限顺序敏感性：保持同一窗口的score多重集合、候选顺序反对称性和标签，分别原顺序、反转顺序、固定随机置换。mean_score应严格不变；learned integrator在冻结参数下的变化只说明该读出使用顺序。主表示CB对local的迁移收益与integrator对mean的增益分别报告。5秒单segment不增加无意义置换任务。

注意积累时长是决策观测窗口，不等于神经潜伏期或已测量的行为反应时。现有资料没有某行为RT变量时，明确该变量不存在，不用5/10/20秒代替。

## 5.6 小样本区间的数值退化

已读attention seed3407仅10/44人的部分表出现极大max-t临界值，涉及稀疏bootstrap重采样SE近零。保留原注册输出，标明数值退化与未完整覆盖；不能把异常宽度翻译成生物学变异或等效证据。

本轮新增小family使用`docs/06`/`docs/08`声明的固定原始SE identity max-|z*|敏感性分析。不要修改旧studentized bootstrap代码后覆盖旧主表。两种统计方法、样本覆盖、原始SE和临界值均可并列查看。

---

# 06 — 执行身份、资源、统计与交付

## 6.1 执行状态与授权

本包是在既有ALN3.4探索与10-GPU授权下的限定下一轮。server接入后，完成相关必要工程检查即可执行；不因论文框架、措辞、显著性或新一轮go等待。准备本包的本地环境未执行真实EEG训练、未提交Slurm、未推送GitHub。

所有任务在`plans/workpackages.json`列明性质：重分析、继承继续、限定新增或依赖敏感性。一个任务缺checkpoint只影响其真实依赖；不能形成全项目总gate。区分failed execution、未完成覆盖、数值不可估计和有效阴性结果。

## 6.2 不改写旧执行身份

建议新生产模块使用`auditory_alignment_v3/aln35/`，新配置/入口用`scripts/auditory_alignment_v3/aln35/`，私有运行输出`private/auditory_alignment_v3/aln35/`，公开可发布派生结果`results/auditory_alignment_v3/aln35/`。这是需要server实际接入的目标路径，包内参考脚本不假装这些模块已经存在。

每个新unit的signature至少包含：

`workpackage_id, design_version, dataset, source/donor lineage, target exclusion, source execution/checkpoint/plan hashes, code hash, objective, EEG/audio access, target coordinates, candidate/query identifiers, fit/cal/selection roles, seed, outer/content fold, support-selection rule, adaptation/training budget, readout, comparison version`。

使用canonical JSON哈希生成新ID，明确parent IDs。保持原始records、失败副本、运行中源码与旧计划。修改实现产生新code/design版本；对仍运行旧版本的任务保持其源码快照可用。不能把新统计结果写回旧训练unit冒充原注册分析。

旧`held_executions.json`维持精确列表。已完成旧结果可读、可比较；未完成且obsolete的执行不批量恢复。不得为本包删除checkpoint、清空hold、重置队列或取消其他项目作业。

## 6.3 10-GPU调度与实际成本

- 项目同时运行GPU总数最多10张，计入所有旧/new runner、replay与工程probe；不是每条lane各10张。
- source/inner依赖优先给能够解锁多个已登记比较的任务。CPU重分析与文档勘误立即并行；其完成不依赖GPU阳性。
- 首个代表工程运行记录device、实际wall time、显存、更新/样本次数、cache IO、失败/恢复。之后按实测更新成本估计，给范围和依据，不将估算当消耗或完成承诺。
- 新APwrong、support、episode、checkpoint-selection、matched-update任务按专题限定范围登记，不自动扩展所有数据集/loss/backbone/种子。首批完整比较完成后，先解释结果，再决定后续轮次的问题。
- 既有有效在跑任务不因为本包优先级改变而强行中断。确实需要资源重排，只修改确切project-owned待运行任务或其已支持的调度权重，保存回执。

保持现有数据位置规则：新下载若确有必要使用`/projects/EEG-foundation-model`内既有数据根；本轮默认不需要新数据集。不把私有数据复制到用户home或公开包。

## 6.4 选择层级必须如实

训练人内的held-out声音/早停、ridge-only OOF、整个模型训练流程排除inner人，是不同协议。每项结果报告实际层级；不能改个名称就把旧checkpoint变成新的人群独立开发。

新策略超参数、checkpoint、support选取、窗口或模型身份只能依照source fit/cal/独立inner开发数据。所有outer query用于最后评估；其标签、真风险、组差、显著性不能参与选择或停止。支持池的元数据访问也必须单列，不能把访问30%刺激日志择出10%训练样本暗称仅10%标签预算。

固定候选包括0-step/原模型，ties按预先声明的更简单候选优先。epoch0获选是合法结果，区分“有效回退”与“非零个人学习”。原native/unified策略差异保留；新策略需要新policy ID。

## 6.5 统计合同

### 继承结果

原已注册主分析、bootstrap-t/max-t family和已报告区间原样保留。修复解释或数值执行不能静默改变统计对象。凡改变分析方法、对比集合、目标或样本集合，写新analysis version与已见结果说明。

### 本轮新增探索性直接比较

1. 使用真实逐人结果，在同一个人内形成规定arm/window/support差；先按真实重复content/session评估cells汇总，再按所需seed平均。
2. `outer subject_fold`是该人的排除归属，不是每个人都应具备的重复fold。适配导出器明确重复fold语义；已经合法汇总的逐人值可使用`reported_identity_mean`，必须保留上游完整性溯源。
3. 每个family明确metric、unit、readout、访问合同、query集合、固定比较、所需seeds与expected identities。不能从观察到的人反推总体就是这些人。
4. 对需要的全部条件取共同完整人；同时输出每个条件覆盖与缺失原因。未完整也可报告描述性interim，但不能按临时p值停止或选择更好子集。
5. 新小family参考实现采用4000次整人bootstrap，按预先指定听觉组/stratum独立重采样，所有同人条件共用抽样索引；用原样本固定SE归一化的max-|z*|构造同时区间。区别于每次bootstrap重估SE的旧bootstrap-t。
6. 直接组间改善差由各组人内改善再做组差；组内独立重采样，同一组抽样索引在整个family复用。组差不能由两条独立CI相减生成。
7. 少于3完整人、零经验方差或其他非正规条件，报告`nonregular`、覆盖及点估计（若有），CI缺失；不能把零经验方差解释成总体等效。小组（如NH9、中间佩戴阶段5）即使满足计算条件，仍保留有限精度边界。
8. 每个原始family、所需条件、SE、bootstrap seed、临界值、B、方法名及探索性标签一并输出。采用本包reference工具需按docs/08转换真实输入，不能把synthetic example当生产数据。

此新统计法是透明的探索性补充，不是为了获得更小区间；同时保留原注册方法的结果或失败诊断。无需替换所有旧表，也不声称有限样本下精确家族覆盖。

### 效应对象

检索主风险用bits/query、儿童分类用bits/trial/AUC，group比较为改善差。不同采样率、音频维度、候选数/候选池、输入时间范围或native/unified readout不能随意合并。音频线性残差可预测性及history模型log-score gain均不是精确CMI。概率校准改善、排序改善、表征功能变化分开报告。

## 6.6 必要检查，不设科学绩效门槛

| 风险 | 必要检查 | 失败时影响 |
|---|---|---|
| 时间访问误标 | 由实际sample indices核算mask交集、half-open边界和采样时刻 | 只纠正受影响条件 |
| 训练/开发人重叠 | source/inner/outer身份与拟合对象全链记录；不只查head | 只停止不满足所宣称协议的新增策略 |
| 假错配 | canonical刺激/anchor组置换、重复视图一致、无真实重配、曝光记录 | 修复该wrong lineage，原有效AP继续 |
| support泄漏/覆盖混淆 | 固定query、support pool/fit/metadata访问分开、源端选择 | 修复对应支持策略 |
| 概率错列 | candidate IDs/order/hash与query集合一致、归一化/有限值 | 只排除不兼容融合输入并报告 |
| episode干预近恒等 | 实际BA、表示/预测位移、梯度与更新方向；CS单类支持检查 | 解释配方实际压力，不删儿童或伪造非零梯度 |
| 统计退化 | SE、临界值、共同人集、重复行与非有限值 | 标非正规/缺失，保留原结果 |

性能低、区间跨零、配方没赢不属于工程失败。检查已经足以解决风险后停止重复测试，继续有效比较。

## 6.7 结果文件和最小交付

server每轮输出：

- `INTAKE.md`、`ALN35_BINDINGS.json`、`ALN35_EXECUTION_PLAN.json`；
- `CORRECTION_PRIVATE_PRE_ACCESS.md`和affected-IDs机器清单，旧数值来源哈希；
- `paired_science.json`、`group_effects.json`、`support_coverage.json`等按实际完成生成的逐人/汇总文件；
- 每条新增方法的implementation、engineering receipt、complete/expected覆盖及原始选择轨迹；
- `ROUND_REPORT.md`：观察→竞争解释→本轮区分→实际结果→仍未分清，正/负/不确定对称；
- provenance/manifest，复用、缺失、失败、nonregular与旧hold分别列出；
- GitHub可发布副本的实际来源与哈希，沿用既有发布工作流。不得将“已准备包”写成“已训练/已发布”。

個体级模型结果公开已授权，不再询问相同范围。沿用当前已批准字段白名单，包括既有匿名人ID及已允许的模型得分/年龄/佩戴时长字段；原始EEG、真实身份、映射表、联系信息、私有checkpoint和逐trial原始记录不由本包新增公开。support覆盖可发布聚合或既有允许粒度，新增原始事件序列不自动公开。

本包本地交付另有`reports/LOCAL_VALIDATION.md`、`MANIFEST.json`、`SHA256SUMS`，只证明文件与参考工具检查，不证明server生产结果。

---

# 08 — 配对对比、物理覆盖与支持量参考工具

## 定位与边界

本目录提供 ALN3.5 的**可运行参考实现**，用于检查本轮新探索性小 family 的统计定义和输入完整性。它不是实际 EEG pipeline，不发现服务器数据，不训练模型，不拟合选择器，不提交或取消作业，不调用 Git，也不删除文件。输入均只读；结果默认写到 stdout，指定 `--output` 时只创建不存在的新文件。

这些工具不改写 ALN3.4 及更早注册分析的 bootstrap-t 输出，不回算出一个更有利的旧结论。真实分析必须先由 server 端依据完整 unit records／per-participant 数据及注册预期名册，导出可追溯的规范行；本包的合成数据不能作为任何 EEG 发现的证据。

运行要求：Python 3.10 或以上，仅标准库，无需安装依赖。以下命令从本包根目录执行，所有输入路径由调用者指定；没有预设服务器根目录。

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paired_contrasts.py --help
```

## 1. 一行代表什么

`schemas/normalized_rows.schema.json` 描述 JSONL 单行格式。`examples/synthetic_rows.jsonl` 含 128 个纯合成行：8 个唯一人、2 个 seeds、2 个内容评估 cell、2 个 arms、2 个时间窗口。它不含真实参与者。

| 字段 | 约定 |
|---|---|
| `dataset`, `identity` | 数据集与稳定的人 ID；不是窗口或 seed 的伪参与者 ID。 |
| `group` | 输入中的人群标签；同一个人的标签不能随 arm、fold 或 seed 改变。 |
| `stratum` | 可选预先定义的重采样层。使用 `stratified` 时，每个选中的行必须显式提供。 |
| `fold` | 同一个人实际重复的内容／session 评估 cell。**不是要求每个人都经历全部 outer subject folds。** |
| `seed` | 该行所属的单个实际 seed，非负整数。 |
| `arm`, `window` | 精确的条件和窗口名称。条件身份应含足以区分生产配置的信息，不把不同 readout 默默合并。 |
| `metric`, `unit`, `value` | 指标名、单位和有限数值。对比符号由 spec 的权重明确指定。一个 family 只使用同一 dataset、metric、unit。 |
| `query_set_id` | 同人、同 seed、同内容 cell 下，所有配对条件共同的底层评估 query 集合 ID／哈希。跨窗口对比也须有可说明的共同评估单位。 |
| `analysis_role` | `outer_test` 或 `inner_dev`；默认分析 `outer_test`。工具不做 inner 选择或重新选赢家。 |
| `provenance` | 可选来源与分割 ID；真实绑定尽量提供，并开启 `require_full_provenance`。 |
| `metadata` | 可选补充信息，工具不把它自动解释为统计变量。 |

唯一行 key 是 `(dataset, identity, fold, seed, arm, window, metric, analysis_role)`。重复 key 一律报错，不能通过平均重复记录消除问题。JSON 内部的重复字段名也报错。

`provenance` 支持：

```json
{
  "query_ids": ["participant_01:trial_07:query"],
  "support_ids": ["participant_01:trial_02:support"],
  "population_fit_identities": ["source_01", "source_02"],
  "selection_identities": ["inner_01", "inner_02"],
  "outer_fold": "subject_partition_0",
  "source_record": "a caller-supplied immutable record identifier",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

上面的 ID 与哈希只是格式示例，不能拿来替代真实 provenance。`population_fit_identities` 指群体 encoder、bridge、source calibration 等的来源人，不包含允许用于该人的 support adapter 的个人支持样本。`selection_identities` 指用于选择配置／步数／窗口的人；outer test 人不得出现在其中。`inner_dev` 人可以用于选择，但仍不得出现在 population fit 人列表。

检查包括：有限数值、重复 key、标签改变、同名 query 集合实际 ID 不同、support/query ID 相交、目标人与 population fit／outer-test selection 人相交，以及配对条件的 outer subject fold 改变。只有提供的 ID 能被检查；缺少 provenance 时，输出明确记录检查覆盖数，**不能把“未发现交集”写成“已证明无泄漏”**。`require_full_provenance=true` 要求每个实际用于配对的行包含 query、support、population-fit、selection IDs 和 outer fold；不需要某类数据时可以提供真实空列表。

### 已聚合输入与不同的人拥有不同内容 cell

当 source 已经正确计算了单人、单 seed 的内容均值，可用 `fold="reported_identity_mean"`，但必须额外提供 `aggregation_note`、非空 `source_fold_ids` 和 `source_seed_ids=[该行seed]`。工具不替 source 审查均值是否正确；注释必须说明其内容权重和完整性来源。

**已经把多个 seeds 平均成一行的数据，不能复制成多个 seed 行，也不能伪造一个新 seed 来代替。** 需要找回单 seed 结果，或保留在其原有分析中；本工具会拒绝 `source_seed_ids` 不是单元素当前 seed 的行。

`required_folds_by_identity` 可覆盖默认的 `required_folds`，例如某个人按注册设计只有一场 session。不能根据这次恰好下载到哪些 cell 临时把缺失项从要求中删掉。私有儿童若每人只有一个 outer test 归属，通常可统一编码 `fold="evaluation"`，把真实 `subject_fold` 放入 provenance；公开数据中同人两个 content folds 应保持为两个评估 cell。

## 2. 小 family 的声明格式

分析 spec 是一个 JSON 对象，不是运行队列。科学问题清单、服务器 job plan 或生产注册表若有额外字段，需先完成明确的 binding，不能直接塞给 CLI。

必要字段为 `family_id`, `dataset`, `metric`, `unit`, `required_seeds`, `contrasts`，并声明 `required_folds` 或 `required_folds_by_identity`。一个 contrast 的 terms 按 `group × arm × window` 指定有符号权重。

```json
{
  "family_id": "example_new_exploratory_family",
  "dataset": "example_dataset",
  "metric": "true_query_nll_unified",
  "unit": "bits/query",
  "required_folds": ["content_0", "content_1"],
  "required_seeds": [3401, 3407, 3413],
  "expected_identities": {"HA": ["ha_01", "ha_02", "ha_03"], "NH": ["nh_01", "nh_02", "nh_03"]},
  "minimum_n": 3,
  "require_full_provenance": true,
  "bootstrap": {"B": 4000, "seed": 351001, "alpha": 0.05, "resampling": "independent"},
  "contrasts": [
    {"id": "HA_benefit", "terms": [
      {"group": "HA", "arm": "reference", "window": "full", "weight": 1},
      {"group": "HA", "arm": "candidate", "window": "full", "weight": -1}
    ]},
    {"id": "HA_minus_NH_benefit", "terms": [
      {"group": "HA", "arm": "reference", "window": "full", "weight": 1},
      {"group": "HA", "arm": "candidate", "window": "full", "weight": -1},
      {"group": "NH", "arm": "reference", "window": "full", "weight": -1},
      {"group": "NH", "arm": "candidate", "window": "full", "weight": 1}
    ]}
  ]
}
```

风险改善按 `reference − candidate`，正数表示 candidate 风险更低。窗口差例如 `candidate/early − candidate/late`；如果比较的是“早期干预损害减晚期干预损害”，应把各自 full/reference 项写全，并明确其符号。代码不猜测“越大越好”，也不根据结果修改 family。

`expected_identities` 来自注册名册而非当前已有输出；允许逐 group 指定。若未给某组名册，输出 `expected_status="not_supplied"`、`expected_n=null`。`common_complete_n` 只表示本次可配对的样本数。若给了名册，输出缺失整个人的 ID、缺失具体条件的 ID，以及观察到但不在预期名册中的 ID；后者不擅自加入主 panel。

默认 `group` 按文字精确匹配。需要核心全人群 family 时可以声明 `"group_sets":{"all":["HA","NH"]}`，terms 使用 `group="all"`。`all` 没有隐式通配语义。同一 family 的不同分析组不得覆盖同一个人群层级；全体与 HA/NH 交互宜分开成已解释的 family。否则把重叠的人当独立组会破坏重采样协方差。

## 3. 精确统计定义

在每个分析组内，工具先取 **family 中全部相关条件、全部所需 folds 和 seeds 都齐全的共同人集**。同组内所有对比共享这个人集，不逐对比挑不同的人。完整性是数据配对要求，不是按性能设定的继续／终止门槛。

设 `c` 为 family 成员，`g` 为不重叠分析组，`i` 为人。对于该人的每个所需 seed `s`、内容 cell `f`，先计算有符号条件和：

\[
d_{igcfs}=\sum_{t\in(c,g)} w_t y_{igfs,t},\qquad
d_{igc}=\frac{1}{|S|}\sum_{s\in S}\frac{1}{|F_i|}\sum_{f\in F_i}d_{igcfs}.
\]

每个人先对其 required folds 等权平均，再对 required seeds 等权平均。最后：

\[
\widehat\theta_c=\sum_g\frac{1}{n_g}\sum_{i\in g}d_{igc}.
\]

组差的负号已经在 terms 中。一个人仍然是一个抽样单位；content folds、seeds、query 数量都不增加 n。不同组人数不同也不默认把组效应按人数重新加权。这种区间条件于所评估的内容和已声明的 seeds 集合；它不另外估计推广到新内容总体或新训练 seeds 分布的额外不确定性。

### 本轮新探索性区间：固定原始 SE 的 max-|z*|

`B=4000` 固定；随机 seed 必須写入实际分析记录。每次 bootstrap 对整个人的完整 family 向量重采样，保持同人的条件、fold 平均与 seed 平均的依赖关系。

`independent` 模式：各不重叠组独立有放回抽取 `n_g` 人，原始估计方差为 \(\sum_g s_{gc}^2/n_g\)。

`stratified` 模式：每组内每个预先定义的 stratum 独立、有放回抽取原来的 `n_gh` 人。固定该组的样本层权重 \(w_{gh}=n_{gh}/n_g\)，方差为 \(\sum_{g,h} w_{gh}^2 s_{ghc}^2/n_{gh}\)。它保持观察到的层组成，不估计未知总体层占比的不确定性；层的选择必须有科学或抽样设计理由。

对可估计的 family 成员：

\[
z^*_{bc}=\frac{\widehat\theta^*_{bc}-\widehat\theta_c}{\widehat{SE}_{c,\mathrm{original}}},\quad
m_b=\max_c |z^*_{bc}|,\quad
CI_c=\widehat\theta_c\pm q_{.95}(m_b)\widehat{SE}_{c,\mathrm{original}}.
\]

分母是**原始样本的固定 SE**，不使用每次重采样重新估计的 SE；因此不是旧报告的 studentized bootstrap-t。分位数使用线性插值（type 7）。输出同时保存 method、B、seed、原始 SE、critical value 和适用的 family 成员名。没有 p 值，也不把跨分析文件的所有比较自动纳入同一个校正 family。

这是有限样本探索性 bootstrap 近似，合成测试证明的是实现遵守上述定义，**不证明真实小样本人群有精确 95% 覆盖率**。固定 SE 避免某次重采样 SE 近零引起的极端临界值，不消除稀疏数据的全部推断限制。区间不裁剪到指标的自然边界。

### nonregular 不能叫“等效”

默认任何必需组 `n<3`，或任意用于该 contrast 的重采样 block 少于 2 人、经验 contrast 方差为零，都会使该 contrast 标为 `nonregular`。对应 `simultaneous_ci=null`；仍保留可计算的点估计、实际人数和原因。分层模式中出现常数层也按此处理，不能用其他层的变异代替该层未知的总体变异。

nonregular 成员不参与 max statistic；输出 `simultaneous_scope` 明确剩余可估计成员。如果 family 部分成员 nonregular，family 状态为 `partially_nonregular`，不能宣称整个原 family 都有区间覆盖。全零差值仅是样本上的精确观察，不是总体等效、没有信息或达到天花板的证据。

## 4. 可直接运行的合成示例

下例在 8 个合成人中合并 HA/NH 为 `all`，得到 early risk 改善均值 **1.8 bits/query**。这只是人为设置的数值，完全没有研究意义。

```bash
python -B scripts/paired_contrasts.py contrast \
  --rows examples/synthetic_rows.jsonl \
  --spec-json '{"family_id":"SYNTHETIC_ONLY_pooled","dataset":"synthetic_demo","metric":"true_query_nll","unit":"bits/query","required_folds":["content_0","content_1"],"required_seeds":[3401,3407],"group_sets":{"all":["HA","NH"]},"expected_identities":{"all":["SYN_HA_1","SYN_HA_2","SYN_HA_3","SYN_HA_4","SYN_NH_1","SYN_NH_2","SYN_NH_3","SYN_NH_4"]},"require_full_provenance":true,"bootstrap":{"B":4000,"seed":351001,"resampling":"independent"},"contrasts":[{"id":"pooled_benefit","terms":[{"group":"all","arm":"reference","window":"early","weight":1},{"group":"all","arm":"candidate","window":"early","weight":-1}]}]}'
```

真实文件的调用方式：

```bash
python -B scripts/paired_contrasts.py contrast \
  --rows /caller/chosen/normalized_rows.jsonl \
  --spec /caller/chosen/bound_small_family.json \
  --output /caller/chosen/new_reference_result.json
```

这里的 `/caller/chosen/` 是占位路径，不是服务器目录建议。省略 `--output` 就只向 stdout 输出；指定的输出文件若已存在会报错，不会覆盖输入或旧结果。

## 5. 物理 mask 覆盖：local pre 的 0 与 FM pre 的 50 samples

`mask` 子命令按生产函数的 **keep-mask** 语义核查：**保留指定时间窗内的输入样本，窗外位置全部置零**。`private_current_time.py` 的 `mask_patches`（仓库基线 `5ef4a60`，68–75 行）直接把 patches 乘以窗口指示函数。输入、mask 的样本位置必须相对于同一个 query anchor，且来自**实际进入 encoder 的数组坐标**。区间采用半开 `[start, stop)`，避免把零时刻算到 pre 区间。

下面使用当前私有任务的真实访问几何：采样率 **250 Hz**，pre 为 **[−200,0) ms**；local 访问 **[0,600) ms**，FM 访问 **[−200,600) ms**。换成相对事件零点的样本下标，分别是 mask `[−50,0)`、local `[0,150)`、FM `[−50,150)`。这组参考输入用于核查该几何和 keep 操作的含义，运行时仍须从实际批次导出坐标。

```bash
python -B scripts/paired_contrasts.py mask --spec-json \
  '{"sample_rate_hz":250,"mask_samples":[-50,0],"contexts":[{"id":"local_pre","input_samples":[0,150],"expected_overlap_samples":0},{"id":"fm_pre","input_samples":[-50,150],"expected_overlap_samples":50}]}'
```

| 访问路径 | `retained_samples` | `zeroed_samples` | `has_requested_data` | `all_zero_input_after_keep_mask` |
|---|---:|---:|---|---|
| local `[0,150)` | 0 | 150 | false | true：keep 操作强制整个输入全零 |
| FM `[−50,150)` | 50 | 150 | true | null：保留区间实际值未知 |

FM 保留 **50 samples = 200 ms**，覆盖所请求 pre 区间的全部50个位置；local 没有被请求的 pre 数据，keep 操作会把已有的150个 post 样本全部置零。`zeroed_samples` 统计被操作设置为零的位置，不声称这些位置原来非零。FM 保留的值也可能恰好全零，所以工具没有读实际 EEG 时，将 `all_zero_input_after_keep_mask` 设为 null，不能猜测“真实输入一定改变”或“一定不全零”。输出还保存几何 overlap、请求区间覆盖率及 `input_values_inspected=false`。

若 expected count 不匹配，仍输出核查结果，但退出码为 3；输入格式错误为 2，正常为 0。

因此 local pre 与 FM pre 的比较同时受**可访问的物理数据不同**影响：前者的 encoder 输入被强制全零，后者保留 pre 样本。这不能直接解释为两个模型对同一 pre 信息的利用差异。该工具也不能单独证明服务器 mask 放到了正确张量位置，或证明模型有／没有 pre 信息。实际加载、重采样、归一化、padding、context 长度与 receptive field 仍须从生产实现和真实批次核对；不能仅复制这个示例的区间来通过核查。工具仍支持其他采样率及任意合法半开区间，其合成边界测试与上述真实访问几何测试分别保留。

## 6. 可选纯 ID 支持量分配

`support` 输入为 `{"segments":[{"id":"segment_000","order":0}, ...],"seed":351007}`。`order` 是外部已确定的严格时间顺序，ID 和 order 都不能重复。

算法令总数为 N，前 `floor(.30*N)` 个 ID 是共同支持来源区域；30% arm 使用该区域全部 ID，10% arm 从同一区域中按固定 seed 无放回抽取 `floor(.10*N)` 个 ID。两个 arm 使用**同一个剩余末端 query ID 列表**。报告实际整数数量，不能在 N 无法整除时声称恰好 70%；N 太小则报错而非虚构支持样本。

```bash
python -B scripts/paired_contrasts.py support \
  --spec /caller/chosen/chronological_segment_ids.json
```

这只提供“同一前段来源区域内改变数量”的纯 ID 参考，10% 子集不固定为最早 10%。它不检查片段时长、类别平衡、滤波跨界、anchor 间距或 FM context halo；输出明确 `physical_context_leakage_checked=false`。真实适配仍需依据实际物理样本和 query 边界处理 context 交叉，不能仅凭 ID 集合不相交宣称没有泄漏。

## 7. 已执行的合成验证与真实验收的区别

`tests/test_reference.py` 对以下具体风险提供检查：手算的 arm 差、窗口差及组间改善差和 SE；先内容后 seed 的人级均值；条件／seed 不全排除整个 family 的该人；预期名册缺人；不同人内容 cell 数不同仍等权；显式全体合并；独立与分层 SE；零方差／小样本／singleton 层的 nonregular；稀疏 n=10 数据不采用近零的重采样 SE；重复、NaN、泄漏及 query mismatch 拒绝；inner/outer 角色区分；250 Hz 真实访问几何下 local 保留0、置零150与FM保留50、置零150 samples，以及保留位置不等于观测到非零值的 keep-mask 语义；另外的泛化区间边界；纯 ID 支持嵌套与固定 query。

示例的三个已知对比值分别是 HA early 改善 **2.8**、HA−NH 改善差 **2.0**、HA candidate early−late 风险差 **0.625**，人数每组仍是 **4**。测试还核对固定 seed 下输入行重排不改变输出、CLI 不改变输入文件且拒绝覆盖已有输出。交付前已运行 **28 项合成／参考几何测试，全部通过**；另以标准库解析 schema，核对其顶层字段与 runtime 契约一致，128 行示例全部通过 runtime 检查。当前环境未安装外部 JSON Schema 验证器，因此未执行该引擎验证；CLI 没有此依赖。实际运行记录应与包的交付核查记录一起保存。

这些合成检查没有读取真实 EEG、没有复现任何真实训练、没有验证 server exporter，也没有证明临床或神经机制结论。真实结果交回时仍须附源记录与哈希、所需 panel 的覆盖状态、实际物理 mask 核查及每个新 contrast 的统计说明。

---

# 附录A — 活动规则

# ACTIVE RESEARCH INSTRUCTIONS — ALN3.5 (2026-10-18)

This block carries the researcher's current ALN3.5 instructions. Place it above conflicting historical research/approval wording and preserve the history. It continues ALN3.4; it does not reset old execution identities or remove scoped holds.

1. Keep research concerns, changeable hypotheses and replaceable tools distinct. The active concerns are shared sound–EEG structure across hearing experiences, personal support requirements, and temporal organization of decoding. This round is exploration, not a manuscript or a cross-subject leaderboard.
2. Use current GitHub and live server evidence for execution status. Package baseline is `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`; bind to actual source/code/plan hashes. Earlier counts are snapshots.
3. Continue effective local and query-aligned truly full-finetuned CBraMod as main candidates. Retain representative REVE/random and published kernel-CS/InfoNCE comparisons. No unpublished VCS-QMI or neural variational critic.
4. Preserve all valid favorable, unfavorable and uncertain results. No AUC/r/p-value entry gates, no selection of people/seeds/hearing-group significance, no claim of universal absence or ceiling from a weak configuration. A concrete implementation may fail without closing the research concern.
5. Correct the native private local/E_PUBLIC_TRANSFER all-zero `pre` condition and affected TG cells with exact scope and versioned provenance. Do not reinterpret it as actual pre-event EEG. Retain original outputs and unaffected post-event/prior/within-architecture results.
6. Aggregate completed per-identity outputs now. Do not derive paired or group-effect uncertainty by subtracting aggregate confidence intervals. New result-informed contrasts are exploratory and named; old registered primary statistics remain visible.
7. Finish useful registered CB auditory, adaptation, fusion and dependent inner-source panels. Other valid registered private/attention/prior/budget work continues with factual dependencies. Do not bulk-release old holds or restart the project.
8. Implement only the bounded new comparisons in ALN3.5: matched AP wrong-audio, support-count/coverage separation, effective episode pressure, whole-pipeline new-person true-risk selection, and probability-fusion attribution. No automatic architecture×loss×window Cartesian expansion.
9. Selection is source-side at the declared level. A source model that has already seen a proposed inner person cannot be relabeled as whole-pipeline held-out-person. No outer-test query labels or outer results may choose a model, support subset, checkpoint, window or stopping point. Declared source-side inner query outcomes may select a rule; a person's support subset cannot be selected using that person's evaluation-query outcomes.
10. Private children answer current-sound, history-conditioned, temporal and support/adaptation questions. Hearing-group and developmental analyses are allowed with direct effect differences and proper scope. Cross-sectional device duration is not longitudinal change; broad input masks are not neural latencies.
11. Individual-level publication within the user's already-approved fields remains authorized; do not ask again. This does not authorize raw EEG, names, identity mappings or new raw private records. Keep stage/group/identity definitions and human/phantom exclusions intact.
12. Maintain the existing aggregate 10-GPU cap and exact job ownership. Reuse compatible assets. No blanket cancellation, queue/hold reset, checkpoint deletion or editing running source in place. Within scope, engineering readiness is sufficient to proceed; no further paper/framing/go approval is needed.

---

# 附录B — 声明性任务与比较清单

以下JSON是范围和绑定清单，不是Slurm队列或可直接输入通用CLI的spec；生产unit数、真实身份、source hashes和缺项必须现场填写。科学probe与原主终点的指标和family分别保留。

## configs/research_scope.json

```json
{
  "version": "ALN3.5",
  "baseline_commit": "5ef4a60bf77eeaeab5582c2cb076077c0b15bd11",
  "project": "W-Yinghao/auditory",
  "stage": "continuing_exploration",
  "max_running_project_gpus": 10,
  "reference_tools_submit_jobs": false,
  "main_candidates": ["effective_local_L0_L1", "query_aligned_true_full_CB"],
  "retained_competitors": ["representative_REVE", "matched_random_initialization", "published_kernel_CS", "InfoNCE"],
  "excluded_tools": ["unpublished_VCS_QMI", "unpublished_variational_critic"],
  "existing_primary_seeds": [3401, 3407, 3413],
  "new_mechanism_representative_seed": 3401,
  "new_analyses_status": "exploratory_after_observing_ALN34_results",
  "old_primary_statistics": "preserve_versioned_outputs",
  "new_reference_statistics": "identity_bootstrap_fixed_original_SE_max_abs_z",
  "bootstrap_draws": 4000,
  "min_complete_group_n_for_reference_interval": 3,
  "performance_admission_threshold": null,
  "source_selection": "declared_source_fit_cal_or_independent_inner_only",
  "individual_publication": "already_authorized_existing_fields",
  "new_raw_private_publication": false,
  "inherit_registered_valid_work": true,
  "bulk_release_holds": false,
  "overwrite_running_sources": false,
  "delete_checkpoints_or_data": false
}
```

## plans/workpackages.json

```json
{
  "schema_version": "aln35_workpackages_v1",
  "note": "Research workpackages, not a live scheduler manifest. Resolve exact unit IDs and counts on the server; no automatic job submission.",
  "workpackages": [
    {"id":"S35_INTAKE","concern":"all","action":"analyze_existing","priority":0,"document":"docs/01_BASELINE_AND_INTAKE.md","dependencies":[],"output":"INTAKE.md + ALN35_BINDINGS.json","gpu":"none","scope":"current HEAD, plans, exact completed/running/held IDs, source and cache lineage"},
    {"id":"S35_PRE_CORRECTION","concern":"time_readout","action":"analyze_existing","priority":1,"document":"docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md","dependencies":["S35_INTAKE"],"output":"CORRECTION_PRIVATE_PRE_ACCESS.md + affected_ids.json","gpu":"none unless a single scoped source-forward check is needed","scope":"old native E_LOCAL/E_PUBLIC_TRANSFER pre and incident TG cells; preserve post/prior outputs"},
    {"id":"S35_PAIRED_SCIENCE","concern":"shared_content_and_time","action":"analyze_existing","priority":1,"document":"docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md","dependencies":["S35_INTAKE"],"output":"paired_science + original_main_endpoint_group_effects + per_identity_coverage","gpu":"CPU; only missing exact cache extraction may need forward inference","scope":"plans/science_contrasts.json (10 families/30 contrasts) and plans/main_endpoint_group_contrasts.json (3 families/10 contrasts); preserve each endpoint and family; no new training matrix"},
    {"id":"S35_CLOSE_CB_AUDIO","concern":"auditory_specific_prior","action":"continue_registered","priority":1,"document":"docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md","dependencies":["S35_INTAKE"],"output":"complete existing paired/direct/wrong panel at actual coverage","gpu":"existing registered tasks","scope":"cb_auditory_v1; retain fixed10000 and actual donor lineage"},
    {"id":"S35_CB_AUDIO_STATE","concern":"transferable_auditory_training_state","action":"new_bounded","priority":2,"document":"docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md","dependencies":["S35_INTAKE"],"output":"existing donor-state diagnostics and one lawful source-only state-selection sensitivity","gpu":"reuse donor snapshots; bounded target/inner refit only for the declared selector","scope":"DTU seed3401 generic_paired; existing0/2500/5000/10000 backbone states; retain fixed10000/direct/wrong; actual checkpoint and inner-source availability are local dependencies, not completion of every old target unit"},
    {"id":"S35_CLOSE_D_FUSION","concern":"personal_support_and_complement","action":"continue_registered","priority":1,"document":"docs/05_FUSION_READOUT_ATTENTION.md","dependencies":["S35_INTAKE"],"output":"complete registered adaptation_policy/strong_fusion and required inner-source pairs","gpu":"existing registered tasks","scope":"actual remaining valid units only; no repeat complete records"},
    {"id":"S35_CONTINUE_OTHER_VALID","concern":"existing_research_questions","action":"continue_registered","priority":2,"document":"docs/06_EXECUTION_AND_REPORTING.md","dependencies":["S35_INTAKE"],"output":"current coverage for private factorial/episode, attention, prior LOO, learning curves and valid breadth","gpu":"existing registered tasks","scope":"preserve active work and true dependencies; keep old exact holds"},
    {"id":"S35_AP_WRONG","concern":"auditory_specific_prior","action":"new_bounded","priority":2,"document":"docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md","dependencies":["S35_INTAKE"],"output":"same-audio-objective AP versus APwrong mechanism pairs","gpu":"new donor/target only where compatible reuse is impossible","scope":"local prior33 NCE seed3401; DTU, FAU, private; distinct target-excluded donor lineages"},
    {"id":"S35_SUPPORT_COVERAGE","concern":"personal_support","action":"new_bounded","priority":2,"document":"docs/04_SUPPORT_AND_EPISODE.md","dependencies":["S35_INTAKE"],"output":"support_pool/fit/metadata access + fixed-query quantity/coverage contrasts","gpu":"source reuse plus bounded adaptation evaluation","scope":"DTU and private, NCE seed3401 local/CBpre; one fixed tail query after actual block/context guards; U10/U30/C10 and private-only H10; nominal percentages accompanied by actual segment/trial/block counts; retain existing CS without copying this new matrix"},
    {"id":"S35_EPISODE_PRESSURE","concern":"adaptation_friendly_group_learning","action":"new_bounded","priority":2,"document":"docs/04_SUPPORT_AND_EPISODE.md","dependencies":["S35_INTAKE"],"output":"source-only functional-pressure record then fixed ordinary/episode pairs","gpu":"limited source refinements under shared cap","scope":"DTU and private, NCE seed3401 local/CBpre;20/100 internal support steps,100 encoder updates for each ordinary/episode pair; retain existing CS/REVE without automatic new strengths"},
    {"id":"S35_TRUE_RISK_SELECTION","concern":"transferable_training_state","action":"new_bounded","priority":2,"document":"docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md","dependencies":["S35_INTAKE"],"output":"whole-pipeline inner-person selection by true query risk versus inherited gain selection","gpu":"reuse lawful inner sources or bounded new independent source fits","scope":"DTU local/CBpre/CBrand seed3401; same trajectory and access"},
    {"id":"S35_MATCHED_UPDATES","concern":"source_people_requirement","action":"new_bounded","priority":3,"document":"docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md","dependencies":["S35_INTAKE"],"output":"50 percent versus100 percent source people at equal optimizer updates","gpu":"reuse compatible full-data snapshots; one limited people axis","scope":"DTU local/CBpre/CBrand seed3401, content held fixed; no automatic content-axis extension"},
    {"id":"S35_FUSION_ATTRIBUTION","concern":"usable_complement","action":"analyze_existing","priority":1,"document":"docs/05_FUSION_READOUT_ATTENTION.md","dependencies":["S35_INTAKE"],"output":"fixed-CB, temperature/shrink/repeated-seed and actual-mixture direct comparisons","gpu":"CPU/readout or exact forward extraction only","scope":"DTU compatible inner/outer score caches; inherited seeds; no new encoder for optional self-ensemble"},
    {"id":"S35_BRIDGE_FACTOR","concern":"readout_dependence","action":"analyze_existing","priority":2,"document":"docs/05_FUSION_READOUT_ATTENTION.md","dependencies":["S35_INTAKE"],"output":"two source-only bridges x fixed versus source-calibrated temperature","gpu":"readout only","scope":"NCE seed3401 DTU AP/XM, FAU XP/XM; old endpoints retained"},
    {"id":"S35_HISTORY_INTERFACE","concern":"private_current_sound_given_history","action":"analyze_existing","priority":1,"document":"docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md","dependencies":["S35_INTAKE"],"output":"equally calibrated history-only control and strict other-block twin coverage","gpu":"readout only when source features available","scope":"private prior NCE full, limited declared arms; no new raw private publication"},
    {"id":"S35_ATTENTION_ORDER","concern":"temporal_readout","action":"analyze_existing","priority":3,"document":"docs/05_FUSION_READOUT_ATTENTION.md","dependencies":["S35_INTAKE"],"output":"fixed trained-integrator 10/20-second order sensitivity and unchanged mean-score reference","gpu":"none with existing score cache","scope":"corrected paired candidate order; no new attention encoder"}
  ]
}
```

## plans/science_contrasts.json

```json
{
  "schema_version": "ALN35_SCIENCE_DECLARATIVE_PLAN_v1",
  "plan_id": "ALN35_SCIENCE_PRIVATE_20261018",
  "recorded_date": "2026-10-18",
  "reviewed_repository": "W-Yinghao/auditory",
  "reviewed_commit": "5ef4a60bf77eeaeab5582c2cb076077c0b15bd11",
  "execution_mode": "declarative_binding_manifest_not_direct_cli_input",
  "status": "authorized_analysis_specification_requires_real_site_binding",
  "analysis_origin": "exploratory_after_2026_10_18_review",
  "companion_document": "docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md",
  "purpose": "把已有声音内容、时间组织与私有儿童结果转为有限的直接配对问题；不重训已完成科学模型。",
  "global_rules": {
    "read_current_head_plans_and_actual_queue_first": true,
    "preserve_original_units_plans_hashes_and_statistics": true,
    "no_training_or_queue_commands_in_this_manifest": true,
    "aggregate_gpu_cap_inherited": 10,
    "no_performance_or_significance_entry_gate": true,
    "independent_unit": "human_identity",
    "pairing_order": ["within_identity_and_repetition", "mean_repetitions", "mean_required_seeds", "equal_identity_mean"],
    "reject_duplicate_observation_keys": true,
    "require_common_complete_identity_set_within_family": true,
    "missing_values_are_not_zero": true,
    "do_not_infer_pairwise_covariance_from_aggregate_intervals": true,
    "do_not_select_seeds_windows_groups_or_models_by_outer_test_results": true,
    "do_not_count_seed_content_fold_or_session_as_independent_n": true,
    "do_not_pool_main_native_5s_metrics_with_science_probe_metrics": true,
    "individual_output_publication_scope": "inherit_user_authorized_derived_results_excluding_raw_data_names_and_identity_mapping"
  },
  "path_resolution": {
    "repo_root": "resolve_from_auditory_alignment_v3.core.REPO",
    "core_out": "resolve_from_auditory_alignment_v3.core.OUT",
    "output_dir_relative_to_repo": "results/auditory_alignment_v3/aln35/science",
    "do_not_guess_private_absolute_paths": true
  },
  "sources": {
    "prior_science": {
      "plan_relative_to_core_out": "aln34/prior_science_v1/plan.json",
      "units_relative_to_core_out": "aln34/prior_science_v1/units",
      "bindings_relative_to_core_out": "aln34/prior_science_v1/bindings",
      "aggregate_relative_to_repo": "results/auditory_alignment_v3/aln34/prior_science/science.json",
      "upstream_family_id": "ALN32_PUBLIC_AUDIO_PRIOR_TARGET",
      "upstream_filters": {"spec.block": "core", "spec.objective": "NCE", "seed": 3401},
      "logical_arm_resolver": "auditory_alignment_v3.prior33.target_train.arm_of(row)[0]",
      "allowed_arms": ["S", "AP", "XP", "J*", "XM"],
      "private_value_path": "per_participant[identity].windows[window][metric]",
      "public_value_path": "decoding[representation+'/'+target][train_center+'/'+test_center].per_participant[record_id][metric]",
      "validate": ["status_complete", "probe_false", "plan_sha256", "unit_source_matches_plan", "binding_sha256", "source_record_sha256", "resolved_access_and_readout_contract", "exact_query_pairing"],
      "private_contract": {"fs_hz": 64, "input_samples": 38, "sample_times_ms": {"first": 0.0, "last": 578.125}, "nominal_windows": ["0_200", "200_400", "400_600", "full"], "pre_event_condition_available": false, "readout": "source_ES_linear_probe"},
      "public_contract": {"fs_hz": 64, "input_samples": 38, "access_duration_ms": 593.75, "window_position_semantics": "start_shift_relative_to_current_sound_anchor", "available_targets": ["env/direct", "env/history_conditional", "onset/direct", "onset/conditional"], "new_contrast_cell": "0/0"}
    },
    "native_public_science": {
      "plan_relative_to_core_out": "aln34/content_time_v1/plan.json",
      "units_relative_to_core_out": "aln34/content_time_v1/units",
      "aggregate_relative_to_repo": "results/auditory_alignment_v3/aln34/science_v2/science.json",
      "value_path": "decoding[representation+'/'+target][train_center+'/'+test_center].per_participant[record_id][metric]",
      "readout": "source_fit_ES_selected_ridge_refit_on_source_fit_plus_ES",
      "query_definition": "eight_fixed_anchors_per_eligible_5s_segment_not_5s_native_retrieval",
      "access_definition_ms": "[center-400,center+600)",
      "logical_arms": {
        "CB_PRE": {"family_id": "ALN32_TRUE_FULL", "spec.architecture": "cbramod", "spec.adaptation": "pretrained_full", "spec.recipe": "full_onestep_v1", "spec.lr_backbone": 0.0003, "spec.objective": "NCE"},
        "CB_RANDOM": {"family_id": "ALN32_TRUE_FULL", "spec.architecture": "cbramod", "spec.adaptation": "random_full", "spec.recipe": "full_onestep_v1", "spec.lr_backbone": 0.0003, "spec.objective": "NCE"},
        "LOCAL": {"family_id": "ALN32_LOCAL_SUPPORT", "spec.architecture": "lag_local_tokens", "spec.variant": "local_aligned1000", "spec.objective": "NCE"}
      },
      "fixed_seeds_by_dataset": {"dtu": [3401, 3407, 3413], "fau": [3401], "federici": [3401]},
      "available_targets_by_dataset": {
        "dtu": ["env/direct", "env/history_conditional", "onset/direct", "onset/conditional", "spec/direct", "spec/conditional", "flux/direct", "flux/conditional", "Ac/direct", "Ac/conditional", "Lz/direct", "Lz/conditional"],
        "fau": ["env/direct", "env/history_conditional", "onset/direct", "onset/conditional", "spec/direct", "spec/conditional", "flux/direct", "flux/conditional", "Ac/direct", "Ac/conditional", "Lz/direct", "Lz/conditional"],
        "federici": ["env/direct", "env/history_conditional"]
      }
    },
    "native_private_science": {
      "plan_relative_to_core_out": "aln34/private_current_time_v2/plan.json",
      "units_relative_to_core_out": "aln34/private_current_time_v2/units",
      "aggregate_relative_to_repo": "results/auditory_alignment_v3/aln34/science_v2/science.json",
      "value_path": "per_participant[identity].windows[window][metric]",
      "track_v1_reuse": ["execution_version", "reused_from", "unit.previous_id"],
      "use_in_this_plan": ["correction_manifest", "existing_poststimulus_context", "existing_support_and_developmental_context"],
      "cross_architecture_full_comparison_is_not_same_access": true,
      "common_post_mask_scope": "evaluation_access_sensitivity_only_target_training_access_unchanged",
      "post_only_forward_label": "evaluation_post_only_training_access_unchanged",
      "cross_architecture_access_attribution_rule": "match_target_training_selection_and_evaluation_access_use_existing_legitimate_post_only_training_sources_first_register_limited_new_training_only_if_the_specific_attribution_question_requires_it_never_replace_training_match_with_forward_only"
    }
  },
  "population_binding": {
    "expected_names_must_come_from_site_manifest": true,
    "reported_snapshot_counts_are_checks_not_synthetic_rows": {
      "private_bdf": {"total": 64, "groups": {"HA": 55, "NH": 9}},
      "dtu": {"total": 44, "groups": {"hi": 22, "nh": 22}},
      "fau": {"total": 67, "groups": {"ha": 29, "ci": 24, "th": 14}},
      "federici": {"total": 86, "groups": {"CI": 33, "HC": 37, "HC-v": 16}}
    },
    "repetition_fold_semantics": "content/session_repetition_not_outer_subject_fold",
    "required_folds_by_dataset": {"private_bdf": ["evaluation"], "dtu": ["content_0", "content_1"], "fau": ["content_0", "content_1"], "federici": ["content_0"]},
    "federici_session_rule": "resolve_existing_manifest_and_average_required_sessions_within_identity_seed_content_before_export_preserving_session_provenance",
    "subject_fold_rule": "retain_source.subject_fold_in_metadata.subject_fold_and_convert_to_nonempty_string_provenance.outer_fold_e.g._0_to_subject_0_then_check_consistency_across_arms",
    "allowed_identity_specific_override": "required_folds_by_identity_from_actual_registered_manifest_never_from_available_results_only",
    "HC_v_rule": "distinct_humans_not_paired_with_HC_without_explicit_identity_evidence",
    "exclude_nonhuman_entities": ["phantom:junior"]
  },
  "observation_export": {
    "format": "JSONL",
    "required_fields": ["dataset", "identity", "group", "fold", "seed", "arm", "window", "metric", "unit", "value", "query_set_id", "analysis_role"],
    "analysis_role": "outer_test",
    "key_fields": ["dataset", "identity", "fold", "seed", "arm", "window", "metric"],
    "provenance_fields": ["query_ids", "support_ids", "population_fit_identities", "selection_identities", "outer_fold", "source_record", "source_sha256", "aggregation_note", "source_fold_ids", "source_seed_ids"],
    "metadata_fields": ["source_commit", "source_unit_id", "source_plan_sha256", "subject_fold", "content_fold", "representation_contract_id", "readout_contract_id", "additional_source_records_and_hashes_if_aggregated"],
    "provenance_types": {"outer_fold": "nonempty_string_e.g._subject_0", "source_record": "nonempty_string", "source_sha256": "64_lowercase_hex_characters", "query_ids": "nonempty_list_of_unique_real_query_ID_strings_when_supplied", "source_seed_ids": "single_element_integer_list_equal_to_row.seed"},
    "synthetic_example_policy": "documentation_schema_validation_only_never_include_synthetic_rows_or_placeholder_hashes_in_research_observations",
    "source_seed_ids_if_supplied": "must_equal_singleton_current_observation_seed_never_expand_an_already_cross_seed_average",
    "cli_spec_binding": {"keep": ["family_id", "dataset", "metric", "unit", "required_seeds", "required_folds", "group_sets", "contrasts"], "add_from_real_manifest": ["expected_identities", "required_folds_by_identity_if_needed"], "bootstrap": {"B": 4000, "seed": "family.bootstrap_seed", "alpha": 0.05, "resampling": "independent"}, "analysis_role": "outer_test", "retain_non_CLI_annotations_in_binding_manifest": ["source", "interpretation"], "command": "python -B scripts/paired_contrasts.py contrast --rows NORMALIZED.jsonl --spec BOUND_FAMILY.json", "never_overwrite_original_outputs": true},
    "query_set_id_rule": "hash_actual_ordered_identity_trial_or_segment_anchor_keys_for_the_paired_evaluation_scope_not_arm_or_source_unit_id",
    "query_ids_missing_from_unit_rule": "derive_only_from_bound_deterministic_extractor_and_existing_cache_metadata_record_method_and_hash_otherwise_mark_dependency_unavailable",
    "window_aliases": {"full": "full", "early": "0_200", "mid": "200_400", "late": "400_600"},
    "public_window_encoding": "target@train_center/test_center; representation_fixed_as_model",
    "metric_units": {"auc": "AUC", "r": "Pearson_r", "history_gain_bits": "bits/trial", "history_minus_twin_bits": "bits/trial"}
  },
  "statistics": {
    "method_for_new_exploratory_families": "identity_bootstrap_simultaneous_max_abs_standardized_error_with_original_SE",
    "tool_name_for_studentization": "fixed_original_SE_bootstrap_max_abs_zstar",
    "B": 4000,
    "confidence_level": 0.95,
    "preserve_old_registered_bootstrap_t_results": true,
    "do_not_relabel_new_method_as_old_bootstrap_t": true,
    "resampling": "independent_analysis_groups_with_shared_draws_for_all_contrasts_in_a_family",
    "use_common_complete_people_per_group_per_family": true,
    "reject_overlapping_analysis_groups_in_same_family": true,
    "zero_variance_or_n_below_three": "retain_point_estimate_mark_nonregular_and_no_invented_interval",
    "family_scope": "only_listed_contrasts_not_all_historical_models_targets_or_populations"
  },
  "families": [
    {
      "family_id": "SCI35_PRIVATE_PRIOR_NCE_AUC4",
      "source": "prior_science", "dataset": "private_bdf", "metric": "auc", "unit": "AUC", "required_seeds": [3401], "required_folds": ["evaluation"], "bootstrap_seed": 351801,
      "group_sets": {"all": ["HA", "NH"]}, "direction": "positive_is_candidate_minus_reference_AUC",
      "contrasts": [
        {"id": "AP_minus_XM_full", "terms": [{"group": "all", "arm": "AP", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]},
        {"id": "Jstar_minus_XM_full", "terms": [{"group": "all", "arm": "J*", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]},
        {"id": "AP_early_minus_late", "terms": [{"group": "all", "arm": "AP", "window": "0_200", "weight": 1}, {"group": "all", "arm": "AP", "window": "400_600", "weight": -1}]},
        {"id": "AP_mid_minus_late", "terms": [{"group": "all", "arm": "AP", "window": "200_400", "weight": 1}, {"group": "all", "arm": "AP", "window": "400_600", "weight": -1}]}
      ],
      "interpretation": "AP对XM是特定先验包差异；直接窗差是固定模型掩蔽输入可读性差，不是神经潜伏期或正确声音配对的纯因果效应。"
    },
    {
      "family_id": "SCI35_PRIVATE_PRIOR_NCE_HISTORY2",
      "source": "prior_science", "dataset": "private_bdf", "metric": "history_gain_bits", "unit": "bits/trial", "required_seeds": [3401], "required_folds": ["evaluation"], "bootstrap_seed": 351802,
      "group_sets": {"all": ["HA", "NH"]},
      "contrasts": [
        {"id": "AP_minus_XM_full", "terms": [{"group": "all", "arm": "AP", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]},
        {"id": "Jstar_minus_XM_full", "terms": [{"group": "all", "arm": "J*", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]}
      ],
      "interpretation": "指定history-offset预测增量的先验差；另列每臂绝对gain，不把相对改善当作已超过history基线。"
    },
    {
      "family_id": "SCI35_PRIVATE_PRIOR_NCE_TWIN2",
      "source": "prior_science", "dataset": "private_bdf", "metric": "history_minus_twin_bits", "unit": "bits/trial", "required_seeds": [3401], "required_folds": ["evaluation"], "bootstrap_seed": 351803,
      "group_sets": {"all": ["HA", "NH"]},
      "contrasts": [
        {"id": "AP_minus_XM_full", "terms": [{"group": "all", "arm": "AP", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]},
        {"id": "Jstar_minus_XM_full", "terms": [{"group": "all", "arm": "J*", "window": "full", "weight": 1}, {"group": "all", "arm": "XM", "window": "full", "weight": -1}]}
      ],
      "interpretation": "沿用原history-matched twin的增量差，必须同时报告原twin异block及自身回退覆盖；不是严格条件互信息。"
    },
    {
      "family_id": "SCI35_PRIVATE_HA_NH_PRIOR_EFFECT2",
      "source": "prior_science", "dataset": "private_bdf", "metric": "auc", "unit": "AUC", "required_seeds": [3401], "required_folds": ["evaluation"], "bootstrap_seed": 351804,
      "group_sets": {"HA": ["HA"], "NH": ["NH"]},
      "contrasts": [
        {"id": "HA_minus_NH_AP_minus_XM", "terms": [{"group": "HA", "arm": "AP", "window": "full", "weight": 1}, {"group": "HA", "arm": "XM", "window": "full", "weight": -1}, {"group": "NH", "arm": "AP", "window": "full", "weight": -1}, {"group": "NH", "arm": "XM", "window": "full", "weight": 1}]},
        {"id": "HA_minus_NH_Jstar_minus_XM", "terms": [{"group": "HA", "arm": "J*", "window": "full", "weight": 1}, {"group": "HA", "arm": "XM", "window": "full", "weight": -1}, {"group": "NH", "arm": "J*", "window": "full", "weight": -1}, {"group": "NH", "arm": "XM", "window": "full", "weight": 1}]}
      ],
      "interpretation": "直接比较每儿童改善的组均值，不能从两组p值差推断交互；私有没有CI组。"
    },
    {
      "family_id": "SCI35_FAU_PRIOR_GROUP_EFFECT2",
      "source": "prior_science", "dataset": "fau", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401], "required_folds": ["content_0", "content_1"], "bootstrap_seed": 351805,
      "group_sets": {"ha": ["ha"], "ci": ["ci"], "th": ["th"]},
      "contrasts": [
        {"id": "HA_minus_TH_AP_minus_XM_history_r", "terms": [{"group": "ha", "arm": "AP", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "ha", "arm": "XM", "window": "env/history_conditional@0/0", "weight": -1}, {"group": "th", "arm": "AP", "window": "env/history_conditional@0/0", "weight": -1}, {"group": "th", "arm": "XM", "window": "env/history_conditional@0/0", "weight": 1}]},
        {"id": "CI_minus_TH_AP_minus_XM_history_r", "terms": [{"group": "ci", "arm": "AP", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "ci", "arm": "XM", "window": "env/history_conditional@0/0", "weight": -1}, {"group": "th", "arm": "AP", "window": "env/history_conditional@0/0", "weight": -1}, {"group": "th", "arm": "XM", "window": "env/history_conditional@0/0", "weight": 1}]}
      ],
      "interpretation": "64Hz科学probe的history残差读出改善差，非主5s检索风险，非治疗或纯声音配对效应。"
    },
    {
      "family_id": "SCI35_DTU_NATIVE_CONTENT6",
      "source": "native_public_science", "dataset": "dtu", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401, 3407, 3413], "required_folds": ["content_0", "content_1"], "bootstrap_seed": 351806,
      "group_sets": {"all": ["hi", "nh"]},
      "contrasts": [
        {"id": "CBpre_minus_CBrand_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "env/history_conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "env/history_conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_CBrand_spec", "terms": [{"group": "all", "arm": "CB_PRE", "window": "spec/conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "spec/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_spec", "terms": [{"group": "all", "arm": "CB_PRE", "window": "spec/conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "spec/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_CBrand_flux", "terms": [{"group": "all", "arm": "CB_PRE", "window": "flux/conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "flux/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_flux", "terms": [{"group": "all", "arm": "CB_PRE", "window": "flux/conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "flux/conditional@0/0", "weight": -1}]}
      ]
    },
    {
      "family_id": "SCI35_FAU_NATIVE_CONTENT6",
      "source": "native_public_science", "dataset": "fau", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401], "required_folds": ["content_0", "content_1"], "bootstrap_seed": 351807,
      "group_sets": {"all": ["ha", "ci", "th"]},
      "contrasts": [
        {"id": "CBpre_minus_CBrand_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "env/history_conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "env/history_conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_CBrand_spec", "terms": [{"group": "all", "arm": "CB_PRE", "window": "spec/conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "spec/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_spec", "terms": [{"group": "all", "arm": "CB_PRE", "window": "spec/conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "spec/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_CBrand_flux", "terms": [{"group": "all", "arm": "CB_PRE", "window": "flux/conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "flux/conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_flux", "terms": [{"group": "all", "arm": "CB_PRE", "window": "flux/conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "flux/conditional@0/0", "weight": -1}]}
      ]
    },
    {
      "family_id": "SCI35_FEDERICI_NATIVE_ENV2",
      "source": "native_public_science", "dataset": "federici", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401], "required_folds": ["content_0"], "bootstrap_seed": 351808,
      "group_sets": {"all": ["CI", "HC", "HC-v"]},
      "contrasts": [
        {"id": "CBpre_minus_CBrand_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "CB_RANDOM", "window": "env/history_conditional@0/0", "weight": -1}]},
        {"id": "CBpre_minus_LOCAL_env_history", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/history_conditional@0/0", "weight": 1}, {"group": "all", "arm": "LOCAL", "window": "env/history_conditional@0/0", "weight": -1}]}
      ],
      "interpretation": "只用实际2–8Hz缓存及包络目标；HC-v身份独立，phantom排除。"
    },
    {
      "family_id": "SCI35_DTU_NATIVE_TEMPORAL_MAP2",
      "source": "native_public_science", "dataset": "dtu", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401, 3407, 3413], "required_folds": ["content_0", "content_1"], "bootstrap_seed": 351809,
      "group_sets": {"all": ["hi", "nh"]},
      "contrasts": [
        {"id": "aligned_readout_loss_at_shift600", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/direct@0/0", "weight": 1}, {"group": "all", "arm": "CB_PRE", "window": "env/direct@0/600", "weight": -1}]},
        {"id": "readout_refit_recovery_at_shift600", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/direct@600/600", "weight": 1}, {"group": "all", "arm": "CB_PRE", "window": "env/direct@0/600", "weight": -1}]}
      ],
      "interpretation": "每个中心仍访问完整一秒窗；读出位置敏感性与恢复，不是600ms单点神经潜伏期。"
    },
    {
      "family_id": "SCI35_FAU_NATIVE_TEMPORAL_MAP2",
      "source": "native_public_science", "dataset": "fau", "metric": "r", "unit": "Pearson_r", "required_seeds": [3401], "required_folds": ["content_0", "content_1"], "bootstrap_seed": 351810,
      "group_sets": {"all": ["ha", "ci", "th"]},
      "contrasts": [
        {"id": "aligned_readout_loss_at_shift600", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/direct@0/0", "weight": 1}, {"group": "all", "arm": "CB_PRE", "window": "env/direct@0/600", "weight": -1}]},
        {"id": "readout_refit_recovery_at_shift600", "terms": [{"group": "all", "arm": "CB_PRE", "window": "env/direct@600/600", "weight": 1}, {"group": "all", "arm": "CB_PRE", "window": "env/direct@0/600", "weight": -1}]}
      ]
    }
  ],
  "corrections": [
    {
      "correction_id": "SCI35-C01",
      "dataset": "private_bdf",
      "upstream_families": ["E_LOCAL", "E_PUBLIC_TRANSFER"],
      "architecture_or_source_architecture": "lag_local_tokens",
      "objectives": ["NCE", "CS_SINGLE"],
      "condition": "pre",
      "requested_original_epoch_samples": [0, 50],
      "actual_original_epoch_samples": [50, 200],
      "interval_semantics": "half_open_250Hz_epoch_with_onset_at50",
      "expected_retained_sample_count": 0,
      "replacement_interpretation": "all_zero_input_control_no_pre_access",
      "valid_for_pre_event_inference": false,
      "affected_paths": ["per_participant[*].windows.pre.*", "per_participant[*].temporal_generalization[pre/*].*", "per_participant[*].temporal_generalization[*/pre].*", "their_group_or_plot_or_claim_derivatives"],
      "unaffected_conditions": ["0_200", "200_400", "400_600", "local_full_poststimulus", "private_support_query_adaptation", "full_window_developmental_endpoints", "FM_true_pre_condition", "public_science", "new_prior_three_window_and_full_science"],
      "required_action": "verify_resolved_patch_mask_intersection_at_site_then_append_correction_manifest_preserving_original_values_and_hashes",
      "no_whole_science_invalidation": true,
      "code_evidence": ["auditory_alignment/model.py:8-12", "auditory_alignment_v2/temporal.py:29-41", "auditory_alignment_v2/train.py:263-284", "auditory_alignment_v3/aln34/private_current_time.py:68-75", "auditory_alignment_v3/aln34/private_current_time_v2.py:75-84", "auditory_alignment_v2/train_fm.py:215-223"]
    }
  ],
  "readout_extensions": [
    {
      "id": "SCI35_PRIVATE_HISTORY_INTERFACE",
      "kind": "versioned_source_only_readout_sensitivity_not_encoder_training",
      "dataset": "private_bdf", "source": "prior_science", "objective": "NCE", "seeds": [3401], "arms": ["S", "AP", "J*", "XM"], "windows": ["full"],
      "definitions": {
        "B0_original": "fixed_source_q0_table_of_six_since_last_deviant_bins",
        "B1_source_calibrated": "sigmoid(logit(q0(h))+b0)_intercept_only_fit_on_same_source_ES_rows",
        "EEG_offset": "sigmoid(logit(q0(h))+b+w^Tz)_same_source_ES_rows_original_penalty_and_standardization_recorded",
        "strict_twin_offset": "same_child_same_history_different_physical_block_nonself_partner_on_common_eligible_rows_no_label_or_error_based_partner_selection"
      },
      "reuse_original_predictions_when_exactly_available": true,
      "source_and_test_rows_for_strict_comparison_must_be_common": true,
      "keep_original_full_query_results_as_separate_scope": true,
      "report_metrics": ["B1_minus_B0_logscore_bits", "EEG_minus_B0_logscore_bits", "EEG_minus_B1_logscore_bits", "EEG_minus_strict_twin_logscore_bits", "auc", "nll_bits", "brier"],
      "coverage_fields": ["n_trials", "n_standard", "n_deviant", "n_history_bins", "n_common_support", "n_strict_twin", "n_fallback_same_block", "n_self_twin", "strict_fraction", "source_ES_class_counts", "query_class_counts", "source_row_hash", "query_row_hash", "twin_map_hash"],
      "numerical_receipt_fields": ["optimizer_success", "optimizer_message", "objective_finite", "gradient_norm", "tolerance", "retry_reason", "source_rows_unchanged"],
      "forbidden_inferences": ["exact_CMI", "unique_neural_information", "clinical_improvement_from_calibration_alone"],
      "if_cache_unavailable": "record_actual_missing_source_dependency_and_recover_only_needed_embeddings_with_frozen_checkpoint_under_existing_GPU_cap"
    }
  ],
  "late_bound_extensions": [
    {
      "id": "SCI35_APWRONG_MINIMAL_SCIENCE",
      "dependency": "matching_target_excluded_donor_and_target_sources_from_ALN35_public_prior_plan",
      "logical_arm": "APwrong",
      "do_not_alias_old_XM_to_APwrong": true,
      "seeds": [3401],
      "datasets": ["private_bdf", "dtu", "fau"],
      "required_matching": ["donor_lineage", "target_exclusion", "sample_exposure", "architecture", "audio_target_geometry", "target_training_recipe", "checkpoint_selection_definition", "query_set", "readout_definition"],
      "minimal_science_extraction": {"private_bdf": ["full", "0_200", "200_400", "400_600"], "public": ["model/env/direct@0/0", "model/env/history_conditional@0/0"]},
      "first_new_contrasts": ["private_full_AUC_AP_minus_APwrong", "dtu_history_residual_r_AP_minus_APwrong_at0/0", "fau_history_residual_r_AP_minus_APwrong_at0/0"],
      "family_rule": "one_explicit_separate_dataset_endpoint_family_per_listed_comparison_with_actual_source_hashes_and_real_complete_identity_binding",
      "do_not_expand_all_time_by_group_grid": true,
      "unready_dependency_does_not_block_existing_families": true,
      "execution_ids": "new_ALN35_ids_never_reuse_ALN34_primary_source_identity"
    }
  ],
  "continue_existing_dependencies": {
    "refresh_real_site_status_before_action": true,
    "known_snapshot_not_live_status": {"native_public_science": "180/180_complete", "native_private_science_v2": "130/130_complete", "prior_science": "300/300_complete", "original_private_LOO": "120/120_complete"},
    "incomplete_lane_status_source": "docs/01_BASELINE_AND_INTAKE.md_latest_published_snapshot_then_refresh_actual_site_status_do_not_reuse_earlier_counts",
    "action": "reuse_completed_compatible_units_continue_only_real_missing_registered_dependencies_and_independent_ready_scopes",
    "no_reapproval_for_ordinary_scientific_interpretation": true,
    "no_duplicate_training_for_completed_science": true
  },
  "deliverables": ["correction_manifest.json", "binding_manifest.json", "observations.jsonl", "coverage.json", "contrasts.json", "history_interface.json", "SCIENCE_PRIVATE_RESULTS.md"],
  "final_report_requirements": ["lead_with_supported_auditory_findings", "separate_stable_question_changeable_hypotheses_replaceable_implementations", "report_actual_identity_seed_repetition_and_query_scope", "retain_favorable_and_unfavorable_results", "state_exploratory_origin_and_multiplicity_scope", "state_what_next_result_would_change_the_working_hypothesis", "do_not_end_with_waiting_for_manuscript_framing"]
}
```

## plans/main_endpoint_group_contrasts.json

```json
{
  "schema_version": "ALN35_MAIN_ENDPOINT_GROUP_PLAN_v1",
  "status": "exploratory_after_2026_10_18_review_requires_site_binding",
  "not_direct_cli_input": true,
  "purpose": "Direct differences of improvements on the original main endpoints; do not substitute science probe r/AUC for these endpoints.",
  "families": [
    {
      "family_id": "S35_MAIN_FAU_APS_GROUP",
      "dataset": "fau",
      "source": "public_prior main target-supervised modeT, block core, NCE, original unified readout",
      "required_seeds": [3401],
      "arm_contrast": "true_query_risk_S minus true_query_risk_AP",
      "group_effect_differences": ["HA minus CI", "HA minus TH", "CI minus TH"],
      "n_contrasts": 3,
      "bootstrap_seed": 351301,
      "expected_group_counts_for_inventory_only": {"ha":29,"ci":24,"th":14},
      "interpretation": "Direct group differences of AP-versus-scratch improvement; cannot identify pure auditory pairing because APwrong is a separate control. Group mean directions were already seen."
    },
    {
      "family_id": "S35_MAIN_FAU_TF_GROUP",
      "dataset": "fau",
      "source": "matched true-full one-step LR3e-4 versus same-access L1 and random CB; original unified 5-second retrieval risk",
      "required_seeds": [3401,3407,3413],
      "arm_contrasts": ["true_query_risk_L1 minus true_query_risk_CBpre", "true_query_risk_CBrand minus true_query_risk_CBpre"],
      "group_effect_differences_for_each": ["HA minus CI", "HA minus TH", "CI minus TH"],
      "n_contrasts": 6,
      "bootstrap_seed": 351302,
      "expected_group_counts_for_inventory_only": {"ha":29,"ci":24,"th":14},
      "interpretation": "FAU is selected because it contains HA, CI and a normal comparison group under one cohort protocol; do not infer architecture-only or treatment effects."
    },
    {
      "family_id": "S35_MAIN_PRIVATE_APS_GROUP",
      "dataset": "private_bdf",
      "source": "public_prior main target-supervised modeT NCE original native class endpoint, not science linear probe",
      "required_seeds": [3401,3407,3413],
      "arm_contrast": "AUC_AP minus AUC_S",
      "group_effect_differences": ["HA minus NH"],
      "n_contrasts": 1,
      "bootstrap_seed": 351303,
      "expected_group_counts_for_inventory_only": {"HA":55,"NH":9},
      "interpretation": "Current-sound task transfer in children. Limited NH precision does not establish equal or unequal benefits."
    }
  ],
  "binding_rules": [
    "Export actual per-person per-seed values with the same content-fold completeness rule as each primary source.",
    "Resolve real authorized identity rosters and exact group codes from source manifests; do not create observations from counts.",
    "Compile group differences as weighted arm terms, preserving same-person pairing and independent group resampling.",
    "Use B4000 identity bootstrap with fixed original SE max-abs-z for these new explicitly exploratory families; retain old primary estimates/intervals.",
    "Require matched query sets, access, target coordinates and readout contracts within each family.",
    "Source aggregation may yield one reported_identity_mean per person and seed only with complete fold provenance; never expand an existing cross-seed mean into seed rows.",
    "Do not choose group pairs, models or seeds by new outer results; all listed contrasts remain in their family.",
    "These are CPU analyses of existing outputs. Missing exact source values blocks only the affected family; no automatic new training."
  ]
}
```

---

# 附录C — Server回执模板

模板中的待填字段不构成已执行记录；只填实际已核查或已产生的内容。

## 包内模板：templates/INTAKE.md

# ALN3.5 现场接入回执

> 模板。所有待解析字段均为未知，不能作为执行证据；填写后另存新版本。

## 时间与来源

- 现场 UTC / Europe/Paris 时间：
- package baseline：`5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`
- 实际 local HEAD / remote HEAD / dirty tree：
- 比制作基线新增的相关提交与结果：
- 已读 AGENTS / CODEX_HANDOFF 最新版本：

## 已有任务对账

| workpackage/lane | registered expected | complete | running/pending | exact held IDs | source/checkpoint/cache可用性 | 动作 |
|---|---:|---:|---|---|---|---|
| 逐项填写，不用旧快照复制 | | | | | | |

区分复用记录、新训练单元、独立参与者数；实际生产完整性按冻结计划，不按文件总数猜。

## 本轮绑定

- correction 精确影响范围：
- 新配对分析需要的 unit / per-participant 字段：
- 可立即分析的family；特定缺失依赖：
- APwrong 每个 target-excluded donor lineage 的复用/新增：
- support 选择池、拟合量、元数据访问及query：
- episode / selection 的真正inner-person排除证据：
- 现有10-GPU总量和实际调度：

## 首批执行

- 立即低成本工作：
- 继续的已登记任务：
- 首批有限新增与必要工程检查：
- 仍保留的旧hold与理由：
- 预计成本依据及尚未知部分：

不以结果方向、论文框架或措辞审批作为等待项。

## 包内模板：templates/IMPLEMENTATION_RECEIPT.md

# ALN3.5 实现与执行回执

## 研究对象与比较

- workpackage / design version：
- 研究关切：
- 本次要区分的两个或多个解释：
- 改变的因素；固定的因素：
- 研究者/执行者在登记时已经看过的结果：

## 真实绑定

- current HEAD、代码路径与hash：
- source/donor/target units及hash：
- target排除与fit/cal/inner/outer身份：
- access、sample indices、target coordinates、candidate/query hash：
- required seeds/content folds/expected identities：
- support pool、fit、selection metadata、query footprint：
- optimizer updates、seen anchors、scheduler horizon、选择规则：
- 新建/复用/缺失/保留hold：

## 工程有效性（只填实际做过的检查）

| 具体风险 | 检查与范围 | 实际结果 | 未覆盖部分 | 受影响依赖 |
|---|---|---|---|---|
| 输入访问、配对、选择独立性、有限值、恢复等按需填写 | | | | |

不得用该表的PASS宣称模型有用；低分不是工程FAIL。

## 生产执行

- 登记的精确ID列表/manifest hash：
- source snapshot / runner版本 / device与资源：
- complete/expected和失败/恢复记录：
- 测得GPU时间、内存与外推成本依据：
- 输出目录、逐人值、选择轨迹和source provenance：

## 结果与解释

- 真实endpoint、单位和符号：
- 实际独立n/seed/content覆盖：
- 正向、负向、不确定结果及nonregular条目：
- 哪个解释得到支持/削弱，为什么：
- 仍无法区分的解释；下一次最少需要什么：

## 包内模板：templates/ANALYSIS_NOTE.md

# ALN3.5 新探索性分析登记

- 日期、作者/agent、当前HEAD：
- 来源结果截至时间：
- 已经看过的点估计、组方向、CI或图：
- 研究问题：
- 为什么现有统计还没有直接回答：
- family ID、完整有向contrast列表：
- 固定source/模型/recipe/readout/访问/窗口/目标：
- 名册、required content/session cells与seeds：
- 逐人配对来源、query一致性与缺失处理：
- 指标、单位、符号、组差定义：
- 重采样单位、B、seed、固定原始SE/max统计、family边界：
- zero variance / 小n / nonregular处理：
- 原注册结果保留位置：
- 本次新增版本输出位置与hash：

这是已看历史结果后的新增分析；不回写成事前注册，不用测试结果改变成员或组别。

## 包内模板：templates/ROUND_REPORT.md

# ALN3.5 本轮研究更新

## 这轮弄清楚了什么

用完整句子说明共享声音内容、个人支持与时间读出的工作认识，紧接其证据范围。不要以作业数量或表格数作为主要发现。

## 三层关系

| 研究关切 | 本轮改变的具体假设 | 对应工具/实现结果 | 仍竞争的解释 |
|---|---|---|---|
| 共享声音结构 | | | |
| 个人支持需求 | | | |
| 时间读出组织 | | | |

## 关键直接比较

| family/contrast | 同一输入与query合同 | 独立n/组n | seed/fold完整性 | 估计与区间/状态 | 解释边界 |
|---|---|---|---|---|---|
| 所有固定比较均列，不按方向筛选 | | | | | |

## 儿童与听觉组

分别给当前声音、同等history基线、strict twin、支持覆盖及直接组改善差。把整体/组内水平与组间改善差分开。年龄/佩戴时长为横断面关联；没有行为RT就明确未测该变量。

## 勘误与来源

列SCI35-C01等具体更正，保留旧值、旧family及来源；说明有效后刺激/同架构/先验结果为何仍可用。列引用的发布commit与真实现场新版本。

## 执行范围

已完成的有效实验、未完成覆盖、特定缺资产、数值不可估、失败恢复和旧hold分别列。GPU时间区分实测与估计，不把已有复用计新训练。

## 下一步研究判断

哪个具体方法可以停止重复；哪个问题因出现了新的区分值得继续；新证据需要什么最小干预。不要以“等待论文框架/待安排正文附录”结束。

---

# 附录D — 来源与本地核查

# ALN3.5 来源索引

制作基线：`5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`。封版前远端核对：`2026-10-18T20:47:50Z`，HEAD 与 main 均一致。

本索引固定本包据以判断的公开报告、结果文件及关键实现。SHA-256对应本地所读仓库字节；文件被列出不表示其所有代码行均完成独立审计，也不表示已经复现真实训练。真实unit配对与资产可用性仍需server绑定。

完整哈希、字节数和附件对应见 `SOURCE_INDEX.json`。以下链接固定在同一个完整提交，不随main漂移。

## 当前状态与规则

| 路径 | SHA-256前16位 |
|---|---|
| [AGENTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/AGENTS.md) | `24073b4a5118dacb` |
| [README.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/README.md) | `cacc81c995cb26f7` |
| [docs/auditory_alignment_v3/aln34/EVENING_PROGRESS_20261018.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/EVENING_PROGRESS_20261018.md) | `3c6e31e06d49ed68` |

## 结果报告

| 路径 | SHA-256前16位 |
|---|---|
| [docs/auditory_alignment_v3/ALN32_SEED_PANEL_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/ALN32_SEED_PANEL_RESULTS.md) | `3e967e95e9c2f358` |
| [docs/auditory_alignment_v3/ATTENTION_ORDER_CORRECTION.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/ATTENTION_ORDER_CORRECTION.md) | `701247c2084b85ec` |
| [docs/auditory_alignment_v3/ATTENTION_TRANSFER_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/ATTENTION_TRANSFER_RESULTS.md) | `006d3892f8523f9e` |
| [docs/auditory_alignment_v3/CAUSAL_FILTER_BOUNDARY_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/CAUSAL_FILTER_BOUNDARY_RESULTS.md) | `1d322481f1e19bc8` |
| [docs/auditory_alignment_v3/CB_AUDITORY_CONTINUATION_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/CB_AUDITORY_CONTINUATION_RESULTS.md) | `b19d7eb6e4617675` |
| [docs/auditory_alignment_v3/COMPLEMENT_FUNCTION_FINAL_INTERPRETATION.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/COMPLEMENT_FUNCTION_FINAL_INTERPRETATION.md) | `7fd6fe78279a455c` |
| [docs/auditory_alignment_v3/D_ADAPT_TRUE_RISK_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/D_ADAPT_TRUE_RISK_RESULTS.md) | `e3c21d125ea9399e` |
| [docs/auditory_alignment_v3/D_MULTI_SEED_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/D_MULTI_SEED_RESULTS.md) | `16f27228b11c046f` |
| [docs/auditory_alignment_v3/FIRST_EPISODE_DIAGNOSTIC.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/FIRST_EPISODE_DIAGNOSTIC.md) | `824d0e330ade46f5` |
| [docs/auditory_alignment_v3/FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md) | `1031c7e53fc033e8` |
| [docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md) | `01c9c18ccaf3bb5f` |
| [docs/auditory_alignment_v3/NEW_SCIENCE_RESULTS_V2.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/NEW_SCIENCE_RESULTS_V2.md) | `c3714be1773d9d3a` |
| [docs/auditory_alignment_v3/PRIOR_SCIENCE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/PRIOR_SCIENCE_RESULTS.md) | `6dc989c87167e688` |
| [docs/auditory_alignment_v3/PRIVATE_CALIBRATION_LOO_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/PRIVATE_CALIBRATION_LOO_RESULTS.md) | `0384ceaa850229bf` |
| [docs/auditory_alignment_v3/PUBLIC_PRIOR_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/PUBLIC_PRIOR_RESULTS.md) | `c1c49d6fe62c3997` |
| [docs/auditory_alignment_v3/STRONG_FUSION_FUNCTION_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/STRONG_FUSION_FUNCTION_RESULTS.md) | `7f3727f7f2c3b2af` |
| [docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md) | `3d740f45bb3abfe4` |

## 已有设计与勘误

| 路径 | SHA-256前16位 |
|---|---|
| [docs/auditory_alignment_v3/aln34/ATTENTION_TRANSFER_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/ATTENTION_TRANSFER_DESIGN_20261017.md) | `40168a7eccde88c6` |
| [docs/auditory_alignment_v3/aln34/CB_AUDITORY_CONTINUATION_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/CB_AUDITORY_CONTINUATION_DESIGN_20261017.md) | `dcf59267a051c9c3` |
| [docs/auditory_alignment_v3/aln34/CONTENT_TIME_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/CONTENT_TIME_DESIGN_20261017.md) | `46fffeb056c34fe3` |
| [docs/auditory_alignment_v3/aln34/DATA_AND_INNER_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/DATA_AND_INNER_DESIGN_20261017.md) | `49e8448ddb828920` |
| [docs/auditory_alignment_v3/aln34/EPISODE_TRAINING_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/EPISODE_TRAINING_DESIGN_20261017.md) | `67d327176f8ec7cd` |
| [docs/auditory_alignment_v3/aln34/NEW_D_POLICY_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/NEW_D_POLICY_DESIGN_20261017.md) | `2b80a250d377f71c` |
| [docs/auditory_alignment_v3/aln34/PRIOR_PRIVATE_LOO_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIOR_PRIVATE_LOO_DESIGN_20261017.md) | `77fccf08d2bd5a45` |
| [docs/auditory_alignment_v3/aln34/PRIOR_SCIENCE_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIOR_SCIENCE_DESIGN_20261017.md) | `e9b96ac48511f0b8` |
| [docs/auditory_alignment_v3/aln34/PRIVATE_CB_FACTORIAL_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIVATE_CB_FACTORIAL_DESIGN_20261017.md) | `91ee9bba71e01131` |
| [docs/auditory_alignment_v3/aln34/PRIVATE_CURRENT_HISTORY_TIME_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIVATE_CURRENT_HISTORY_TIME_DESIGN_20261017.md) | `4321f1f98cf74dca` |
| [docs/auditory_alignment_v3/aln34/PRIVATE_EPISODE_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIVATE_EPISODE_DESIGN_20261017.md) | `66b0319e66c6298d` |
| [docs/auditory_alignment_v3/aln34/PRIVATE_EPISODE_SINGLETON_CORRECTION_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIVATE_EPISODE_SINGLETON_CORRECTION_20261017.md) | `3ae1c1cf9b06e6fd` |
| [docs/auditory_alignment_v3/aln34/PRIVATE_TIME_CALIBRATION_CORRECTION_20261018.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PRIVATE_TIME_CALIBRATION_CORRECTION_20261018.md) | `10740c3eaff87bbb` |
| [docs/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md) | `292130327b8dd379` |
| [docs/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN_CRITIQUE.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN_CRITIQUE.md) | `a236fe875424cd0a` |
| [docs/auditory_alignment_v3/aln34/RESEARCH_BUDGET_FIX_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/RESEARCH_BUDGET_FIX_20261017.md) | `ebcd05497bd44ebe` |
| [docs/auditory_alignment_v3/aln34/STRONG_FUSION_DESIGN_20261017.md](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/docs/auditory_alignment_v3/aln34/STRONG_FUSION_DESIGN_20261017.md) | `1917412b00a1b541` |

## 实现引用

| 路径 | SHA-256前16位 |
|---|---|
| [auditory_alignment/model.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment/model.py) | `bc8f2962f4805a8c` |
| [auditory_alignment_v2/temporal.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v2/temporal.py) | `790d66525b87aa3e` |
| [auditory_alignment_v2/train.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v2/train.py) | `1a00101c1514c1cb` |
| [auditory_alignment_v2/train_fm.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v2/train_fm.py) | `611b945aad7f86c5` |
| [auditory_alignment_v3/aln34/adaptation_policy.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/adaptation_policy.py) | `7ec7c37fe4312a9d` |
| [auditory_alignment_v3/aln34/attention_order.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/attention_order.py) | `3daa4dd4669b4923` |
| [auditory_alignment_v3/aln34/attention_transfer.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/attention_transfer.py) | `2f2569c4d14675ba` |
| [auditory_alignment_v3/aln34/cb_auditory.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/cb_auditory.py) | `a163609ae718f9ca` |
| [auditory_alignment_v3/aln34/content_time.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/content_time.py) | `c601c89a3198a4f1` |
| [auditory_alignment_v3/aln34/data_inner.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/data_inner.py) | `7146dfba65865b42` |
| [auditory_alignment_v3/aln34/episode_training.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/episode_training.py) | `c21d62bee65a0d0f` |
| [auditory_alignment_v3/aln34/learning_budget.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/learning_budget.py) | `6d233c7648b43154` |
| [auditory_alignment_v3/aln34/learning_budget_v2.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/learning_budget_v2.py) | `91c9bdba74ac8d2a` |
| [auditory_alignment_v3/aln34/prior_science.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/prior_science.py) | `13dba78ae90f231a` |
| [auditory_alignment_v3/aln34/prior_science_aggregate.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/prior_science_aggregate.py) | `6719168094575ca3` |
| [auditory_alignment_v3/aln34/private_current_time.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/private_current_time.py) | `85719e9ac455a9cd` |
| [auditory_alignment_v3/aln34/private_current_time_v2.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/private_current_time_v2.py) | `0f8b4876eebc6d09` |
| [auditory_alignment_v3/aln34/private_episode_v2.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/private_episode_v2.py) | `0d239a99af2e9def` |
| [auditory_alignment_v3/aln34/science_aggregate_v2.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/science_aggregate_v2.py) | `304bbd31b3a3a152` |
| [auditory_alignment_v3/aln34/strong_fusion.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/aln34/strong_fusion.py) | `7c7e4356809efd59` |
| [auditory_alignment_v3/core.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/core.py) | `a3851b4a601a1bd7` |
| [auditory_alignment_v3/fm_aligned.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/fm_aligned.py) | `5f99cbc5617a978d` |
| [auditory_alignment_v3/fm_aligned32.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/fm_aligned32.py) | `7579f2a16368d3ae` |
| [auditory_alignment_v3/prior33/bridge.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/bridge.py) | `e7b945d099a0baff` |
| [auditory_alignment_v3/prior33/contract.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/contract.py) | `6831169926263244` |
| [auditory_alignment_v3/prior33/donor_train.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/donor_train.py) | `259525c53a5e8666` |
| [auditory_alignment_v3/prior33/losses.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/losses.py) | `144c5f0b065c6057` |
| [auditory_alignment_v3/prior33/sampler.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/sampler.py) | `574ed2b7d32a208f` |
| [auditory_alignment_v3/prior33/target_train.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/prior33/target_train.py) | `7d301bf3ba744058` |
| [auditory_alignment_v3/sci_r1/private_task.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/sci_r1/private_task.py) | `57d1b002a324a63e` |
| [auditory_alignment_v3/sci_r1/stats.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_alignment_v3/sci_r1/stats.py) | `8bb141cf6070dabb` |
| [auditory_c3/c3dl/hc.py](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/auditory_c3/c3dl/hc.py) | `6d66f84aec7d1f2c` |

## 结果数据引用

| 路径 | SHA-256前16位 |
|---|---|
| [results/auditory_alignment_v3/aln32_panel/aln32_panel.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln32_panel/aln32_panel.json) | `9074a273fea01d72` |
| [results/auditory_alignment_v3/aln34/attention_transfer/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/attention_transfer/efficacy.json) | `3b79d055be619cc0` |
| [results/auditory_alignment_v3/aln34/causal_filter/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/causal_filter/efficacy.json) | `66d4fad5f68aec74` |
| [results/auditory_alignment_v3/aln34/cb_auditory/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/cb_auditory/efficacy.json) | `d0b5c335cfe5b6d4` |
| [results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json) | `3c88b114952d0ec1` |
| [results/auditory_alignment_v3/aln34/d_multiseed/per_identity.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/d_multiseed/per_identity.json) | `2c61440d51bcdf11` |
| [results/auditory_alignment_v3/aln34/dadapt_r/dadapt_r.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/dadapt_r/dadapt_r.json) | `9c619492ce9aa154` |
| [results/auditory_alignment_v3/aln34/dadapt_r/per_identity.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/dadapt_r/per_identity.json) | `f3eb81fd0502dd4c` |
| [results/auditory_alignment_v3/aln34/episode_diagnostics/first_weights.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/episode_diagnostics/first_weights.json) | `690b5dc2712cc170` |
| [results/auditory_alignment_v3/aln34/new_lanes/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/new_lanes/efficacy.json) | `12388b54ee7ed574` |
| [results/auditory_alignment_v3/aln34/prior_private_loo/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/prior_private_loo/efficacy.json) | `3e375fe49ba0ca4e` |
| [results/auditory_alignment_v3/aln34/prior_science/science.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/prior_science/science.json) | `36f34303b1b458cc` |
| [results/auditory_alignment_v3/aln34/private_cb_factorial/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/private_cb_factorial/efficacy.json) | `27e9ae2fb28c3fa0` |
| [results/auditory_alignment_v3/aln34/private_episode_v2/efficacy.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/private_episode_v2/efficacy.json) | `830850afe6d2be50` |
| [results/auditory_alignment_v3/aln34/science_v2/science.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/science_v2/science.json) | `008ec2cd8a1843e5` |
| [results/auditory_alignment_v3/aln34/strong_fusion_function/function.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/strong_fusion_function/function.json) | `1ef2ca4fc0899488` |
| [results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json) | `609781fd2c266314` |
| [results/auditory_alignment_v3/public_prior/public_prior.json](https://github.com/W-Yinghao/auditory/blob/5ef4a60bf77eeaeab5582c2cb076077c0b15bd11/results/auditory_alignment_v3/public_prior/public_prior.json) | `193099f2779c7dad` |

## 附件与继承材料

研究者提供的 ALN3.4 主文、ZIP 及9份原样继承文件均已记录完整哈希。附件内部历史状态与审批文字不覆盖本包最新活动规则；完整旧聊天记录仍未获得。

---

# ALN3.5 本地交付核查

本报告验证交付文件、分析参考实现和声明的输入几何；它不是服务器验收，也不表示新EEG实验已经完成。

## 已实际执行

- 封版前以只读 `git ls-remote` 核对 HEAD/main：`5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`，UTC `2026-10-18T20:47:50Z`；随后本地 `git status --short` 为空。未修改或推送项目仓库。
- CPython 3.12.14、标准库环境中运行 `python3 -B -m unittest discover -s tests -v`：**28/28通过**。
- 128行合成JSONL通过runtime契约；schema的required/properties/provenance白名单与runtime一致。未执行外部JSON Schema引擎，工具无该依赖。
- 科学清单10个family转换为明确CLI字段后均通过spec检查，合计30项对比；原主终点清单另列3个family/10项。这里只检查格式、范围和方向；没有伪造真实名册或逐人结果来完成绑定。
- 科学说明中的synthetic observation单独通过字段检查；它不进入研究observations。
- 250 Hz实际访问几何：local pre保留0个位置、置零150个位置；FM pre保留50个位置（200 ms）、置零150个位置。参考工具没有读取EEG值，FM的实际全零状态保持未知。
- 只读intake工具对公开本地checkout的87个选定来源逐个核对SHA-256，全部匹配；不查询调度器或训练。该结果不是live server inventory。
- 9份继承原文与研究者附件逐字节一致；其历史状态和审批措辞不覆盖本包活动规格。
- 对研究关切、终点、支持元数据预算、训练/评价访问、统计方向和资源边界完成交叉审阅；实际源码地址按 `core.OUT` 解析。

具体机器记录：`reports/REFERENCE_VALIDATION.json`、`reports/LOCAL_INTAKE_REFERENCE.json`。

## 文件与压缩包封装

构建程序在全部文件定稿后生成 `MANIFEST.json`、`SHA256SUMS`，调用 `scripts/validate_package.py` 检查本地链接、JSON/JSONL、Python语法、成员清单、字节数和SHA-256；校验失败即不生成最终ZIP。ZIP生成后检查CRC与逐成员字节一致，且完整说明的独立Markdown副本与包内 `SERVER_FULL_DOCUMENT.md` 逐字节一致。

`MANIFEST.json`不对自身递归求hash；`SHA256SUMS`另含MANIFEST本身，且不对自身求hash。交付不含pycache、pyc或符号链接。server接收后可重新运行同一静态校验命令。

## 真实生产仍须绑定的内容

实际现场HEAD、live jobs/holds、可用checkpoint/cache、完整逐人unit、support/query的真实物理边界，以及训练/选择层级由server核验。本包提供输入合同、声明性比较、参考代码与回执模板；训练接入仍需按服务器当前实现完成，不能把本地合成验证报为真实生产兼容性或真实临床结果。
