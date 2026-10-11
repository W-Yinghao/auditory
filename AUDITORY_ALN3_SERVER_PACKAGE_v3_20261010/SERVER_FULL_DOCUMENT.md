# ALN3 · 局部时空听觉对齐、基础模型细时间读出与私有儿童迁移

**发给server的完整执行文档 · v3.0 · 2026-10-10**

基准：W-Yinghao/auditory@d5b2315b465519fa2017ff3180fd34a090787164。本文接续ALN2后审阅；结果事实、代码审阅推论和新的候选方法分别标注。

## 阅读顺序

00纪律 → 01事实/主线 → 02汇总修正 → 03共同比较 → 04–08方法与任务 → 09科学分析 → 10接入与交付 → 11参考代码。入口文本见包内SERVER_START_PROMPT.md。

# 00 · 研究纪律、版本关系与本轮授权

**ALN3 / v3.0 / 2026-10-10**  
**读取基准**：`W-Yinghao/auditory@d5b2315b465519fa2017ff3180fd34a090787164`（ALN2内容提交 `d8f6d8e19a6c142561a0aab5fa6d179ccbbec0ae`）。

## 本轮要建设什么

以已经有效的局部时空声音–EEG对齐为基础，研究如何读取并利用预训练EEG表示中的补充信息；再以共同方法研究HA、CI、正常对照、儿童年龄与HA验配阶段，以及响应的时间组织。私有儿童任务是独立研究模块，不是公共结果末尾的附加AUC。

本包把上一轮审阅意见转为可实施方案。**ALN2数值是已报告结果；对瓶颈的解释是推论；密集读出、残差互补和新的迁移方法是候选实验，尚无真实训练结果。** 本地附带测试只检查代码和数学接口，不代替真实EEG实验。

## 必须置于server规则文件最前的纪律

**不能以负结果为研究导向。** 当前独立参与者、儿童与刺激内容的支持不足以把“这一配方未建立收益”升级为“数据没有信息、发育无作用、读出已到天花板、所有方法无效”。增加seed、fold和作业数不会增加独立儿童。不得自动将本文收束为能力地图、天花板或负结果审计稿。

这不等于追逐阳性。有效运行、低分、反向效应、负增益和未支持预期的儿童全部保留；不弱化基线、不按测试成绩删人、不用设备或年龄关联的显著性选网络。允许认定某个**具体配置**表现较差，并调整资源；不能据此对整个信息对象作不存在判断。

分析顺序为：**新建立或改善了什么能力 → 完整公平比较 → 哪几个解释仍可竞争 → 哪个干预最能推进方法与听觉问题。** 数值弱时，写清观察、适用范围和可实施改进，不预先指定退稿故事。

## Full experiments，而非绩效门控

所有主实验族按完整参与者外折、内容划分和登记seed执行。单seed、单fold或短probe不决定其他方法是否启动。冻结模型没超过小模型，不阻止PEFT、部分层或全参数训练；公共结果没有显著组差，不阻止私有实验。

只有真实技术依赖才阻塞相关作业：输入或身份映射错误、非有限损失、缺少合法teacher checkpoint等需要修复；它们不阻塞无依赖的训练族。Federici人类汇总修正不要求重跑所有模型，也不应阻塞FAU、DTU和私有训练。涉及Federici的新donor或组分析须先使用正确身份与实体清单。

配置中的维数、网格、学习率和epoch是**可修改的工程起点**，不是科学通过线。允许据训练/开发侧学习曲线续训、扩展合理配方；先写入增补记录再运行，不在测试结果上挑更有利的终点。

## 继承、修订与停用

继承：真实声音–EEG对应；身份级外折；内容与support/query隔离；通道身份保留；真实候选；有符号结果；可复用产物的来源记录；私有逐人数据与权重留服务器。

修订：ALN2的每秒一行基础模型接口增加密集时间读出；引入局部+预训练残差候选；Federici修正实体和聚类单位；私有原生NCE头增加截距校准；教师不再按“全量微调”名称自动指定。

停用为当前执行命令：旧v3的“早期必正常、差异只剩晚期”；按阴性自动转地图稿；可靠性/AUC/p值准入门槛；“不训练新编码器”“个体化已关闭”“同一批数据已用尽”；把NH当作佩戴0个月。历史原文件不删除，保留其当时措辞和结果，但不得覆盖本包纪律。

**不引入VCS-QMI、不引入未发表变分理论或神经critic。** 传统单尺度核CS与InfoNCE为主要竞争目标，FMCA作有理由的近邻对照。无需强行让某个损失胜出。

## 论文承诺

工作标题：*Time-Resolved Auditory–EEG Alignment Across Hearing Devices and Development*（工作题名，不是已完成结论）。方法要提供更有用的解码，科学部分要给出实际支持的听觉认识。修复经历和运行数量不是主要贡献；不承诺任何结果组合必然足以投稿。允许继续发展方法与问题，而不把缺乏支持写成确定阴性。


---

# 01 · ALN2证据、审阅判断与ALN3主线

本节来源均钉在基准提交；见 `SOURCE_INDEX.md`。没有重新运行真实EEG。下列区间为仓库报告的参与者bootstrap，以已训练模型为条件；多数主表seed为3401，跨seed只由指定面板提供。

## 1. 已建立的可用资产

| 观察 | ALN2报告 | ALN3用途 | 来源 |
|---|---|---|---|
| FAU完整Local对齐，统一读出 | NCE：legacy_pool4 0.740 → lag_local_tokens 1.026；配对差+0.287 | 局部编码器作为主通路，不只当待替换基线 | S02 §1 |
| DTU同类比较 | 1.324 → 1.994，约+0.670 | 同一设计在另一成人队列得到改善 | S02 §1 |
| 完整窗/联合窗 | FAU lag：1.026/1.010；DTU：1.994/1.959 | 旧“联合总比完整强”不再是默认事实；进一步拆局部性/压缩/容量 | S02 §1 |
| 修复后DTU CBraMod LoRA预训练收益 | 相对random_full：三个seed +0.143/+0.149/+0.156 bit/查询 | 预训练具有可用先验；仍不证明其单独优于局部模型 | S01 §2.6；S02 §7 |
| FAU REVE LoRA预训练收益 | +0.045/+0.050/+0.027 | 预训练收益不是仅一个seed的现象 | S01；S02 |
| 基础模型当前绝对值 | FAU较好REVE LoRA 0.055；DTU较好CBraMod LoRA 0.164 | 比较的是现接口，不作基础模型能力上限 | S01 §2.1 |
| DTU线性探针可高于主读出 | CS：CBraMod full 0.044/0.341；REVE partial 0.093/0.324（主/探针） | 优先研究读出能力；probe不是上限，差异不只来自K | S01 §2.3 |
| CS与目标交互 | FAU Ac-full NCE/CS 0.950/0.978；Lz-full 0.885/0.990；DTU相应NCE较高 | 保留CS竞争，不固化损失排行榜 | S02 §2 |
| 私有GX full | 原生AUC 0.553 [0.539,0.567]；重新拟合头0.531；原生gain 0.003 [0.001,0.006] | 原生任务头和统一probe并报 | S02 §4 |
| 私有GX历史孪生差 | 0.004 [0.001,0.008] bit/试次 | 沿用合法历史参照进一步研究，不称精确CMI | S02 §4 |
| 私有CBraMod LoRA预训练收益 | AUC差+0.017/+0.016/+0.027 | 继续比较先验、适配和局部任务读出 | S02 §7 |
| DTU小模型个人空间适配 | NCE、30% support：+0.098 [0.025,0.177] bit/查询 | 强局部模型之后重新研究support与适配位置 | S02 §6 |

“gain_bits” = 错配EEG的对数损失 − 真实EEG的对数损失。它受候选、目标、温度和错配规则影响，不是Shannon信息量；不同数据集的绝对bit不合并。

## 2. 需要降为待复核的Federici总表

S04加载HC、CI、HC-v、Artifact；同儿童HC/HC-v分开记录但共享identity；Artifact为test_only。S05将test_only送入评价；S06/S07汇总对全部结果行统计，未在主表排除Artifact或把重复条件合成真实身份聚类。

因此旧表n=95不能称95名独立儿童。旧总表REVE-frozen 0.287、lag-local 0.258及其区间，标记 `legacy_mixed_entities`，不作人类总体优劣依据。先按02重汇总。该问题不等于训练泄漏，也不自动否定每个儿童的预测。

旧总表早/晚方向也不是统一晚期优势：lag-local早0.223、晚0.144。它仅提示需要**队列内、人类分组后的时间分析**；不由成人/儿童表的方向差直接推断发育机制。

## 3. 已报告的有限收益如何解释

同试次选择损失已实际做过，没有稳定改善现有density/CBraMod结果；不能再次将“加一个选择损失”当全新方案。下一步改变的是更强局部表示和跨时间证据整合。

全参数微调不总比冻结/LoRA强；原因可能包括目标粒度、读出、学习率与适配过度，尚未区分。当前继续听觉训练和指定全量教师的有限收益，仅约束这些配方，不是迁移或蒸馏普遍无效。

私有概率gain弱可能涉及先验/校准，但不能把所有负gain都归为校准。01所列原生AUC、自然损失、历史风险增量需分别保留。

## 4. 主线保持，方法角色重排

**研究问题**：如何学习保留局部时空结构的听觉EEG表示，并利用群体共享和预训练先验，读取不同听觉人群的声音响应及其时间组织？

**方法候选**：有效的局部听觉通路 + 基础模型的细时间读出 + 仅在真实收益得到支持时保留的互补分支。

**科学对象**：成人同协议HA/CI/TH；DTU HI/NH；Federici HC/CI/同儿童声码器；私有儿童HA验配阶段与当前刺激历史。各队列回答互补问题，不强迫所有队列方向相同。

**当前不能写成已完成贡献**：预训练残差互补、纯语义解码、正常成熟度、经验因果作用、统一的“早声学晚语言”、基础模型优于局部模型、临床结局预测改善。

三条预期贡献分别用实验建立：
1. 局部时空对齐的有效方法与可靠任务读出；
2. 群体共享、个人适配或预训练补充所能改善的具体听觉证据；
3. 改进测量下的实际人群/时间/儿童阶段认识，其中私有数据回答公开队列不能替代的问题。


---

# 02 · Federici实体与身份重汇总：复用结果、不重跑全部训练

## 目的与范围

修正“文件/条件/幻影头被汇总为独立儿童”的报告问题，保留全部历史结果。该修正来自代码审阅S04–S07；精确的实体计数、重汇总后的数值及对结论的影响需server从逐单元记录核实，本包不捏造修正结果。

## 身份清单

由原数据元信息与现有loader构建私有 `entity_manifest.csv`：
`dataset, record_uid, subject_uid, condition, entity_type, identity_source, source_hash`。

- HC/CI/HC-v应以来源核实后的 `entity_type=human` 标记，Artifact的实体含义从原始元信息核实并单独标记 `phantom`（不能仅凭文件夹名对任何未来数据自动判断）。
- HC和HC-v对应同一儿童时使用同一subject_uid。CI等编号空间不能只去前缀后合并。
- 身份不明确的对象标记unknown，保留明细并先单列；不按EEG相似度猜身份、不按解码分数决定是否人类。
- 区分record_uid、condition、subject_uid、content_id、subject_fold、seed，不能一列兼任。

## 从现有输出导出与重算

先保存旧aggregate与FULL_RESULTS的hash。新版本写到 `results/auditory_alignment_v3/reaggregate/`，不覆写ALN2。

导出规范化长表（私有）每行是一名记录/条件在一个单元下的度量：
`dataset,config_id,seed,subject_uid,record_uid,condition,entity_type,subject_fold,content_fold,unit_id,metric,value`。
同一单元同一记录同一metric只能一行。先在记录内平均重复内容折，再在同一儿童同一条件内平均记录；默认每名儿童同等权重。查询加权的版本可以另报，但不能静默改变目标人群。

输出四组表：
1. **HC、CI、HC-v分别报告**：每组唯一儿童数、记录数、内容数、gain与真实query损失/检索。HC-v不是新增独立儿童。
2. **同儿童HC−HC-v配对**：只用有两条件的来源核实对子，按儿童求差、按儿童bootstrap，报告缺失条件数量。该对比不是设备治疗因果效应。
3. **CI−HC**：在固定方法、同内容/目标规则下，按人类身份比较；年龄关系另行建模，不把CI当HC配对。
4. **Artifact/phantom独立**：仅用于声音同步污染的敏感性参照。重复折上的同一实体不累计为更多样本，不纳入儿童平均、年龄模型、训练或donor。

本次重汇总保持原候选池与原预测不变。另建human-only候选池属于重评价，所有比较须在新池上共同重算，不能只删汇总行却假称已改变检索任务。规范CSV一次只包含一个明确split合同；变更split的结果分别导出。

主文优先分组与配对，不推荐再生成一个所有条件混合的“总体儿童成绩”。确需一个人类汇总时，先对每个身份内部条件等权平均，再对身份平均，并明确该混合人群定义；不与HC/CI特定问题混用。

## 相关重新计算

对全部主模型都重算，不只重算REVE或有利模型。重算预训练−随机、局部−旧模型等同身份配对差。窗口曲线在每次bootstrap中整条重抽同一身份，避免不同时间点换不同儿童。

同一模型跨多个折对test_only幻影头的预测可以保留为模型变动分析，不能将其当多份独立实体。跨seed结果先分别报告，再按身份汇总配置均值；不能把seed×儿童当独立n。

## 阻塞范围与交付

这是CPU重汇总任务，无需重训只因汇总有错的checkpoint。并行开展FAU/DTU/私有新训练。新的Federici训练/多队列donor必须使用纠正后的human训练清单；这只是输入依赖，不是成绩门槛。

交付 `FEDERICI_REAGGREGATION_RECEIPT.md`、分组/配对/phantom聚合表、旧新数字对照及结论更正说明。身份表和逐儿童长表留private。本包 `scripts/reaggregate_federici.py` 是对上述规范长表的参考实现，不是对当前私有JSON结构的自动猜测器；server需要完成一次明确的数据导出适配。


---

# 03 · 数据、声音目标、时间访问与统一评价

## 1. 数据与任务不混同

| 队列 | 核心任务 | 独立贡献 | 本轮依据 |
|---|---|---|---|
| FAU/TUD | 真实声音检索、两说话人注意选择 | 同协议TH/HA/CI比较 | ALN2现有合法人群/内容划分 |
| DTU | 声音对齐、HI/NH及注意选择 | 听损状态与个体适配的另一情境 | ALN2划分与声音实际呈现条件 |
| Federici | 包络对齐、HC/CI/HC-v | 儿童与同儿童刺激条件 | 02身份修正后；保留2–8 Hz缓存事实 |
| private_bdf | 当前标准/偏差任务与历史条件预测 | HA验配初期、儿童年龄、可观测序列 | ALN2同协议64儿童作连续性比较；人数由清单核实 |

私有没有可核实波形时继续用类别/事件身份，不制造Whisper目标或语义标签。MFF未知任务不为凑齐多模态而恢复虚构语义。本轮不以联系医生或新采集作为开工前提。

## 2. 训练与划分

继承参与者外折与真实内容隔离；HC/HC-v在同外折。跨队列donor排除目标测试身份；来源不明的预训练数据重叠仍记unresolved。新增训练内容和旧协议不同，必须单独版本化，不把两种泛化问题混成一个结果。

每个外折的预处理拟合、声音投影、读出正则化、校准和teacher选择只用训练侧。公共→私有允许公共EEG先验，但不能把私有查询标签带进donor。个体support在任务已知刺激/已知指令下适配，查询独立；不能称无监督零样本TTA。

数据量按独立人、不同声音内容、记录、有效片段分别记录。密集时间网格只是更多相关监督位置，不是增加独立样本。

## 3. 声音目标合同

保留Local、Ac、Lz、envelope名称及来源。Ac/Lz是已有声音模型特征，不自动对应“纯声学/纯语言”。本轮不新增语音大模型，也不微调Whisper/GPT-2。

为每个比较面板生成不可变 `audio_target_contract.json`：原特征版本、物理采样时间、每个target的实际时间支持、标准化训练来源、投影矩阵hash、输出维数、是否L2、候选池和query UID。

**legacy目标**沿用ALN2的8原始帧锚点目标与16维设置，作可追溯连接；**dense目标**在同一物理网格上供局部/FＭ/融合共同训练与评分，初始取20 ms间隔。网格选择是工程配置：保留原音频时间映射，重采样/插值不创造新信息；按真实缓存带宽处理，不为不同网络分别改变目标。

dense目标有两条并列路径：
- `fixed_latent`：固定训练侧标准化投影，初始d=32，d=16/64作登记维数敏感性。NCE/传统核CS/FMCA作用于配对表示。监督任务只变投影维数时应单列，不宣称同一estimand。
- `fixed_audio_features`：直接预测同一标准化声音特征，MSE或正则化线性读出作为任务参照。可与依赖损失组合，但先报告各单独项及λ=0基线；不要求组合必须更好。

**禁止用真实query音频作为EEG解码器的输入。** 候选音频只进入匹配评分或训练监督。密集query只给相对时间坐标，不给文件ID、故事ID或全记录绝对时间。

## 4. 时间访问分层

- `local_only`：推理只访问指定query窗口。窗口按ALN2半开区间；FAU/DTU full 0–600 ms、early 0–80、late90–300；Federici0–600/0–150/150–600；私有0–600/120–200/240–320。数字仅用于沿用已有比较，不代表神经成分身份。
- `foundation_context`：基础模型访问5 s或声明的真实上下文。输出可在20 ms网格预测，不等于具有20 ms独立时间来源；不能叫“早窗独有证据”。
- `support_conditioned_local`：独立support提供个人上下文，query只读本地窗口。报告support的信息来源，不能让当前query的窗外内容进入support特征。

私有ALN2基础模型默认读取[-200,600] ms整epoch再补零，而local full只读[0,600] ms。连接旧结果时分层标明；新直接比较增加同样[0,600] ms裁剪/补零的FM版本或把上下文差作为显式因素，不把额外前窗收益自动归于预训练。

基础模型token经过全局注意力后，即使只选择某个patch token，它也可能含其他patch上下文。query位置编码和密集预测不会恢复已丢失的因果隔离。

全部时间结论需考虑已有滤波时间扩散；尤其Federici仅有预处理缓存时，报告为缓存上的窗口受限读出，不命名精确神经潜伏期。

## 5. 评价与读出

每个比较固定query、真实候选、声音目标和信息访问；使用训练侧选择温度/读出。保留原生匹配、共同读出和真实EEG风险，不只报一种最有利读出。探针不同维数/样本量/正则化时明确标记，不称上限。

`G = R(mismatched EEG) - R(true EEG)`是对应敏感性；`R0-R1`才是指定同任务下的预测增量。早晚联合增量用 `R(E)-R(E,L)`，预训练补充用 `R(local)-R(local+FM)`。不同目标/候选/温度的G不能互相相减称独有信息。两个模型温度均在同样训练侧规则拟合，但query风险保持同一自然分布。

连续检索记录top1/top5/MRR、rank、真实NLL、错配NLL和G；注意记录同试次2AFC、分数margin和时间整合长度；私有记录AUC、自然NLL/Brier、原生/探针、q_hist与q_hist+EEG。负值保留。

合法错配保持相应参与者/时间块/任务背景，不选择特别容易的错配来抬高G。依赖训练的乘积分布允许同类别碰撞；私有类别不是instanceID，不能把同类所有交叉配对删掉后仍称原CS-QMI。

## 6. 仅针对传统核CS

复用ALN2核密度信息势估计：`log A + log B - 2 log C`；A=mean(K*L)，B=mean(K)mean(L)，C=mean(rowmean(K)rowmean(L))。带宽、表示尺度与维数只在训练侧选择，记录非对角核量与合法错配。不要部分去掉对角后继续沿用旧估计名。

核CS不自动建立原始余弦坐标；继续使用训练侧统一读出/已定义核后验。若为残差融合使用共同音频预测空间，先拟合训练侧桥，不把两个任意旋转的latent直接相加。FMCA同样保留训练侧白化/配对旋转。核CS目标不是精确神经MI。


---

# 04 · 工作包A：把局部时空对齐发展成主方法

## 科学与方法动机

ALN2的lag_local_tokens已经在FAU、DTU明显改善真实声音对应；不再把它只当基础模型替换前的弱基线。当前实现同时改变局部感受野、时间压缩和参数共享，所以“仅因为时间分辨率”仍是解释而非定论。[S02,S08]

## 完整比较

沿用ALN2完整窗、早窗、晚窗与联合窗，NCE与CS_SINGLE并行。主因素对比：

| 变体 | 定义 | 分辨的解释 |
|---|---|---|
| legacy_pool4 | 旧模型原样，半开/旧右端差异记录 | 连接历史结果 |
| density_tokens | 保留固定时间密度的旧卷积主体 | 单纯减少压缩是否够用 |
| lag_local_tokens | 40 ms局部编码、约20 ms滞后步长、跨lag共享 | 局部性与共享是否有效 |
| lag_local_capacity_control | 调整宽度/深度，使参数量接近density；保持局部结构 | 改善是否只是容量差异 |
| local_unshared_control（扩展） | 取消跨lag共享但约束总容量可比 | 参数共享本身的贡献 |

无需把所有工程超参数做笛卡尔积。先让以上有明确问题的单元跑满外折与训练时长；维数/局部长度在代表性主比较上完整扩展。参数数、FLOPs、每epoch不同刺激量实际记录，不用“相近”代替数值。

## 训练和输出

保留forward_tokens的局部序列，同时输出声音锚点表示。主任务不需要跨所有lag强制独立，也不先规定哪些lag对应声学/语言。统一dense声音目标时，所有方法同网格、同target时间支持；legacy桥接表和新dense表分开。

`forward_tokens`可用于事后受限读出，但只遮掉一个模型输入并不能单独证明窗独有信息。对主要时间结论同时报告：各窗独立训练、完整模型删窗后重拟合、早晚联合的真实query风险差。既有早晚窗之外的局部扫描作为新登记探索，不根据设备显著性挪窗口。

为避免完整窗只能通过更强压缩使用输入，完整模型需保留至少与早/晚子模型可比的局部token密度；这不保证有限样本下必优，优化和正则化也作为竞争解释。

## 关键交付

`A_LOCAL_FULL_RESULTS.md`：每种结构全配置、所有预定数据及seed；`A_TIME_SUPPORT.json`：物理输入/输出时间支持；`A_LOCAL_COMPARISONS.csv`：同query风险差和任务成绩；保存折内token及原生输出，逐人量留private。

将有效局部模型直接送入注意与私有模块；不等待基础模型超过它，也不按临床关联选择哪一个local checkpoint。


---

# 05 · 工作包B：基础模型的细时间读出

## 1. 当前观察与待检验解释

空间平均已经修复。当前接口仍是每个约1秒patch→一行16维对齐，声音目标约1.2秒；DTU通道保留probe高于主读出，说明至少一些可读结构没有充分进入最终评分。[S01,S09,S10]

**本工作包检验读出与监督粒度，不假设基础模型必然胜出。** 初始仅CBraMod和REVE，复用已钉住代码/权重，不新增一排模型。原始预训练语料重叠未核实的部分继续记unresolved。

## 2. 统一输入和token合同

backbone适配器返回：
`tokens[B,C,P,D]`、`channel_names[C]`、`patch_start/end[P]`、`valid_patch[B,P]`、完整真实EEG访问区间、幅值单位/缩放来源、模型版本与层索引。

通道身份保留到学习型组合；使用带符号空间滤波或通道保留线性读出。不能退回无权重通道平均。对不同布局使用明确的位置/通道映射或布局专用输入模块；不按文件列序盲目加载权重。

REVE当前5秒片段最后约0.4秒未落入patch。新的共同评分要么仅取所有比较实际覆盖的query，要么使用声明的合法上下文/填充策略；不能对FM之外的模型偷偷多评价一段。填零不是读取真实窗外EEG；context模型实际访问范围仍由整个forward决定。[S10]

CBraMod的0.15×z是当前工程幅值假设，不是恢复出的真实15µV。沿用以连接ALN2；模型原生尺度的敏感性可独立做，来源未知不能标“已校准”。

## 3. 三类读出，逐项回答问题

### B0 · 当前patch单行

原`SpatialPatchHead`及相应目标作历史对照；另加同样粗网格的小模型评分，区分backbone与时间网格。旧1.2秒目标与新dense目标不能只因候选相同就称完全相同任务。

### B1 · 通道保留的线性/相位线性读出

对固定backbone输出所有通道token，从训练侧拟合regularized ridge；低秩/PCA维数、训练片段数、标准化和校准与学习型读出明确列出。既有PCA256/300片段只是参考起点，不是信息上限。

密集线性版本用位置基函数与token外积构造固定特征，再作线性读出：
`phi(q)=vec(H_selected ⊗ basis(relative_time_q))`。basis只含相对时间，不含真实声音或文件身份。采用低秩/分块实现避免不必要的巨大矩阵。另报位置only、均值token等对照，检查query时刻本身是否预测声音。

计划中的`B_DENSE/channel_phase_linear`是可随NCE/CS反向训练的相位线性头；`B_LAYER_PROBE/channel_linear_ridge`是固定主干的正则化探针。二者分开命名、分开报告，不能把一方的probe拟合与另一方端到端训练混为同一个干预。

### B2 · patch内多query学习型读出（主要候选）

`H=F_EEG(X)`；用共享特征投影和多个带符号空间滤波形成每patch表示，保留patch时间坐标。

`A_hat(q)=D(H, time_encoding(q))`。

query由已声明的相对时间编码产生，经轻量cross-attention或局部MLP读取token。**不把真实音频嵌入作为query，不以故事ID/全记录时间提示目标。** 输出与局部模型相同的dense声音网格与目标维数。

本包`DenseQueryReadout`为张量参考：输入channel tokens、patch中心时间、query相对时间和有效patch mask，输出未归一化dense预测。它不含真实backbone和data loader；server需绑定物理时间、原生层、缓存和目标。

密集输出不等于新增独立时间证据。即使输出每20 ms一个点，若backbone使用完整上下文，仍属于foundation_context。窗口受限分析使用04或真正受限输入学生。

## 4. 适配与层级实验

每类主读出完成 `random_full / pretrained_frozen / pretrained_peft / pretrained_partial / pretrained_full` 比较。冻结失败不阻断微调。相同架构随机初始化是预训练比较必要项，不以小CNN替代它。

冻结backbone另设input/patch embedding、中间层、末层的读出面板。层名依真实架构绑定，三层不是三次自动择优挑测试；全部报告。主矩阵仍用同一预定层，训练侧层混合可作扩展。

开发配方不再只看一个任意单元的短目标loss。使用训练身份内保留内容，覆盖多个固定开发内容块；沿相同候选网格评价真实NLL/检索和loss。可选：头预热→部分/全量解冻，并与一步联合训练完整比较。开发策略本身记为变体，不把微调弱的所有原因归为“样本不够”。

## 5. 训练与资源

共同比较用相同物理片段池、目标网格和sampling规则。FM密集query增加相关行数，不把它们当新独立样本；日志同时写片段数、不同声音数、每步query数、更新步数。batch显存差异时可累积梯度，但CS/FMCA的统计batch应按实际估计样本说明，不能用梯度累积假装已联合估计大核矩阵。

CBraMod/REVE冻结、PEFT、全量各有完整训练预算。沿用ALN2的100/50 epoch可作连接点，新的default是可续训的起点而非上限；是否续训只看训练/开发曲线，不靠测试组差。每个大模型作业一GPU，数量上限继承server当前许可。

## 6. 交付与判读

报告分成：固定backbone换读出；固定读出换初始化；固定初始化换适配；同dense任务下对局部模型。若只是密集评分改善，写时间接口收益；若预训练优于随机，写先验收益；若组合优于局部，再写互补。不预定这些结果同时成立。

交付 `B_DENSE_READOUT_RESULTS.md`、每层/读出表、原生/统一probe表、模型与target合同、训练曲线；弱配置完整保留，不将修复过程作为论文主故事。


---

# 06 · 工作包C：局部听觉通路与预训练补充

## 候选方法，不是已有结论

ALN2证明局部模型有效，并显示若干预训练收益；**并未证明二者具有互补信息**。本工作包的任务就是在同一query目标上检验补充价值，而不是强迫基础模型取代小模型。

## 共同输出空间

先得到局部预测 `A_local(q)`。残差模型为：
`A_combined(q)=A_local(q)+R(H_local(q), H_FM, q)`。

输出在同一个固定声音特征/训练侧桥接空间。NCE/FMCA/CS的两个latent可能有不同坐标规约；不能把它们直接相加后声称音频残差。采用fixed_latent时两支必须由同一固定音频参照训练，仍保留独立probe；最清楚的主参照是显式声音预测空间。

私有任务对应logit：`logit_combined=logit_local+residual_logit`，最终在训练侧统一校准。不能混加AUC或已sigmoid概率。

## 必须有的完整比较

| 变体 | 说明 |
|---|---|
| local_only | 04的有效基线；不要把较弱density代替它 |
| foundation_only | 05同grid可用读出 |
| concat_pretrained | 简单拼接和共同头；检验残差结构是否必要 |
| residual_pretrained_frozen | 冻结原始/任务适配前backbone，仅学补充头 |
| residual_pretrained_peft | 小规模适配补充分支 |
| residual_pretrained_full | 允许全量任务适配，完整训练 |
| residual_random_frozen / random_trainable | 同架构随机分支，区分预训练和新增结构 |
| residual_small_capacity | 类似容量/计算的小分支，区分通用先验与模型容量 |

不是每个控制都与所有超参数交叉；核心比较的初始化、输出网格、局部基线、query池必须一致。

默认frozen/PEFT/full补充分支从**原始预训练checkpoint**初始化；使用已听觉适配donor的版本必须另列initialization字段，不在同一个配置中混用两种起点。

## 初始化与训练阶段

残差输出层初始化为零，使**初始输出**与局部基线逐元素相同。不要在加法后新增会改变基线的归一化/门控。初始等同不保证训练后测试不退化。

先冻结局部基线训练补充头；随后把联合微调作为独立配方完成。残差最后层为零时，第一步上游残差特征梯度可为零，这是结构性质而非LoRA失效；第二步及后续检查真实梯度路径。保留λ=0/local-only参照。

NCE和传统CS作为主要学习目标；预测MSE或固定目标桥作为相同任务参照。先比较单目标，再有目的地比较组合，不默认“三种loss相加”。调节权重只用训练侧内容，不能按儿童发育/设备差异调参。

## 区分价值来自哪里

主增量 `R(local)-R(combined)` 用同一真实query风险。若只有错配损失变大而真实风险未改善，不称性能补充。检索、自然NLL、重建与attention分别看；不能因为任一指标变好就称所有听觉功能改善。

比较：原FM上下文、合法错配FM上下文、位置only、随机权重FM。错配只作对照，不要求它们必须达到预设数值。结合主体小分支容量对照，判断是否确实利用了正确的预训练EEG观测。

## 早晚研究的两种合法使用

- full-context residual：面向整体声音/注意任务，不能叫早期独有证据。
- support-conditioned local residual：个人背景来自独立support；query只取早或晚窗。support、query与目标标签访问写清，不把当前query的全局token作为背景绕过窗口。

严格局部通路始终单独评价，即使融合表现更好也不能抹掉这一部分。没有互补收益时，保留结果并研究读出、任务匹配和目标尺度，不默认成稿为“基础模型无用”。


---

# 07 · 工作包D：注意选择、训练覆盖与个人适配

## 1. 注意：改变表示与证据整合，而不是重复宣称“新加选择损失”

ALN2已做同试次attended/ignored的选择、纯选择及联合训练；主要用density和CBraMod，联合损失未稳定改善。[S02 §5]

本轮把lag-local主干、dense FM读出和局部+预训练候选接入。三个训练任务完整比较：`attended_alignment / selection_only / alignment_plus_selection`。两个候选均为同一时刻真实呈现的声音；随机交换候选次序及标签保持训练不依赖位置。忽略流仍可能被脑电追踪，不能强制其依赖为零。

时间整合比较：相同局部分数序列的简单平均与小型学习型聚合。初始评价5/10/20秒，可按真实试次长度补充既有标准长窗；不跨试次/故事拼接，不为某组使用更长输入。长度分析是注意证据整合问题，**不是采集预算或“最少录多久”论文路线**。

整体对齐与选择性可使用共享EEG主干、不同任务头。支持训练任务从对齐预训练进入选择微调；与从头选择、联合训练并列，不以一个短pilot选唯一配方。5秒弱不代表更长证据聚合也弱，长窗较好也不等于早晚神经潜伏期改变。

## 2. 训练人群覆盖

FAU继续比较TH_ONLY、TH_HA、TH_HA_CI，测试参与者/候选一致。使用有效局部主干及预训练补充；旧CBraMod单支仅作为连接参照。

比较两种预算：真实可用数据全部使用；匹配训练步数/每组曝光的对照。这样区分新增人群与更新步数/采样权重。不能把“加CI后某读出下降”直接写成CI是有害训练数据。

共享主干为主，系统输入映射/小型适配器作为候选；设备组专属头可以比较，但不将不同组各自最优模型分数直接当神经差异。输出训练人群×测试人群表，另用固定共同模型作组比较。

## 3. 个人适配

基线以同fold、同target的已完成局部模型或候选融合模型为起点。support_fraction先保留0.1与0.3，query固定为同一最后70%；真实时间块与保护带沿用，支持长度不是结果准入线。

比较无适配、恒等初始化输入空间映射、输出低秩残差；步数和正则化在训练参与者的模拟support/query上选择。可以冻结局部主干，只适配输入/补充头；与全局模型从头训练不混同。

初始support/query连续性可能反映会话状态，另做合法时间块拆分敏感性；年龄/设备与适配收益分析用固定规则。适配使用已知声音/指令监督时写明，不叫标签无关TTA。不同support配置的query必须相同。

## 4. 交付

`D_ATTENTION_RESULTS.md`：每主干×目标×整合方式、全部长度；`D_COVERAGE_MATRIX.md`：覆盖和预算匹配；`D_ADAPT_RESULTS.md`：support/query、适配增益及按人群的范围。

全矩阵与主seed面板执行。任何具体适配不提升都完整记录；不据此关闭个体化，也不把个体模型成功自动解释成临床监测能力。


---

# 08 · 工作包E：私有儿童、公共听觉先验与教师

## 1. 私有问题保持独立

研究公共听觉训练形成的先验能否帮助读取HA验配初期儿童的当前声音响应，以及改善发生在整体可读性、局部时段还是个人映射。与公共成人连续语音不是同一个监督任务；私有不需要伪造语音波形/语言语义，也不因公共结果不显著而等待。

主分析沿用ALN2同协议儿童清单。任务训练不因缺少临床字段删儿童；关联分析用实际可链接子集并报告每一终点独立n。NH单列，佩戴时长为不适用，不填0、不与初期HA混成一组。历史阶段边界沿用既定0–2月、2<月数<13、≥13月；连续年龄/时长另行报告，不据结果重选分箱。

## 2. 任务匹配的完整比较

- GX原生网络和原生头（保留其较好的AUC），与统一冻结probe并报；
- lag-local/density/legacy的任务原生与共同probe；
- CBraMod/REVE通用预训练：冻结、PEFT、部分、全量与同架构随机初始化；
- 公共听觉适配后的局部/基础模型迁移，私有重新训练真实类别任务头；
- 局部任务模型＋预训练残差logit；
- 局部学生的输出蒸馏与不蒸馏基线。

原生AUC、自然分布概率损失、历史参照增益分别报告。不要用冻结probe最差的成绩替代模型已有的原生能力；也不要让原生校准与probe拟合用不对等的儿童信息。

## 3. 迁移到底迁移哪一部分

公共→私有通道数不同，不能strict=False后把几乎所有关键层漏载而称成功迁移。写明加载的张量名、比例、哪些新建、为何新建。共享可迁移的时序/局部编码/transformer参数；通道布局专用输入映射和私有类别头重新初始化。必要时按实际电极坐标构造固定对应，但不可按测试效果重选通道。

公共donor使用训练许可允许的EEG、已核实的paired stimuli；Federici只用核实人类，不用Artifact。目标公开队列留出的身份不能出现在其donor中。公共→私有不含私有儿童；原始预训练语料重叠如未知继续披露。

公共局部模型的迁移和公共foundation迁移都做：前者检验听觉任务先验，后者检验通用+听觉先验。没有收益时分辨任务目标、空间接口、监督量和适配方式，不说所有跨范式信息不可迁移。

## 4. 纠正教师指定方式

ALN2 D_LOCAL_DISTILL使用固定的auditory_pretrained_full教师。新方案不再用“全量微调”名称保证教师优越。[S03]

主教师政策：`local_teacher / generic_pretrained_teacher / auditory_adapted_teacher`；各政策在训练侧固定内容上选择自己的配方，并保留旧全量教师为连接对照。选择标准为目标任务的留出预测，不读取HA/CI差异、年龄相关或query测试成绩。

教师输入可更丰富，学生的query仍只读其声明窗口。教师表示不一定与学生同坐标，因此优先比较固定声音目标预测、候选分布/排序或私有类别logit蒸馏；任意latent余弦蒸馏保留为旧对照。

推荐损失：`L_student = L_task + λ KL(p_teacher || p_student)`，概率均在相同真实候选/类别上、相同温度定义；λ=0作为完整基线。私有binary目标不生成大量假负类；多正样本按真实类别处理。teacher只用于训练，推理不用query窗外响应。

严格的train-side教师选择与teacher-target生成放在同一outer-fold内；teacher看过query身份就不能给该query宣称独立泛化。依赖模型失效或接口更改只重跑真正依赖项，不覆盖旧结果。

## 5. 概率校准：修复接口，不把它当主要贡献

现有原生NCE头 `sigmoid(score/tau)` 只有温度，无截距。score接近0时输出趋向0.5，不能独立表示自然20%偏差先验。[S11]

比较：现温度、正斜率仿射 `sigmoid(a*score+b)`、共同逻辑回归头、CS类别核后验。a>0保证不通过反转方向改善排序；校准只在训练儿童的指定校准块上拟合，另分开发评分块或交叉拟合。单一块不足时披露已复用开发数据，不使用查询结果补救。

正斜率仿射校准不改变AUC排序；只改善概率不称解码信号更强。负gain可能还来自泛化与过拟合，不能全部归为缺截距。本包提供数值稳定的参考校准器，真实拟合在server训练侧完成。

## 6. 历史之外的当前证据

C=当前之前的合法事件历史。比较q_hist与q_hist+EEG，并保留错配孪生作为对应敏感性。主结果用自然分布query风险；共同支持结果单列支持比例，不静默删掉难状态。历史已确定类别的状态没有剩余类别不确定性，不能要求该处产生增益。

这一模块研究当前刺激证据，不宣称变化检测/MMN机制、听觉理解或已验证康复指标。既有听觉阶段问题继续开展，不以SIR预测成功为主路线条件。


---

# 09 · 听觉问题、发育分析与最终报告

## 三个科学问题与输出

**Q1 群体共享的声音响应。** 固定共同模型、同任务下，HA/CI/TH或HI/NH的总对齐、局部窗口结构、注意选择怎样不同？共享模型与有限个人适配后，哪些差异改变？不训练一个组别分类器代替声音解码。

**Q2 响应的时间组织。** 局部窗口分别能够支持哪些声音目标；联合后真实query风险是否下降；较长上下文是否仅改善整体检索而不改善局部重复性？不同目标的时间支持和滤波保持可追溯，不预定“早声学、晚语言”。

**Q3 儿童发育与验配阶段。** 在公开儿童人类分组和私有HA中，固定模型的声音证据、时间结构、支持适配收益如何随日历年龄或既定佩戴阶段变化？私有提供验配初期和历史条件问题；不把NH构造成0个月设备经验，不把年龄预测误差叫成熟度。

这些分析与方法训练并行登记；不需要先通过AUC/信度/p值门槛。缺乏任务可读性的指标仍完整展示，同时说明其关联结果的信息有限；不能从中推出“发育没有作用”。

## 估计对象和样本单位

主任务单位是片段/试次，推断单位是实际参与者/儿童；多条件、多记录、访视属于身份内层级。先按预定任务规则计算每人的量，再作身份bootstrap；同一个人跨seed/内容折的值不累计成新n。主要方法差比较使用相同query与身份的配对值。

时间曲线重抽整条身份向量；不同组/条件差异直接估计交互或差之差，不用“一组显著另一组不显著”。先报效应大小和区间，再按登记问题族处理多重比较。解释条件bootstrap与训练不确定性：主矩阵以拟合模型为条件，主面板另报跨seed变化；不声称新seed或重分折等于新儿童复现。

年龄与设备时长关联使用低自由度模型与连续散点，不逐个扫描分箱找峰。日历年龄=首次验配年龄+时长的代数关系没有因新网络消失；不能同时当三个独立因果效应估计。已有配对访视仅在确认为独立采集、元数据明确时补充，儿童内变化亦混有成熟和时间变化。

私有多轮探索和来源不全在报告中披露：本轮是ALN2之后登记的新实验，不是假称对这批儿童从未看过。临床字段缺失按终点给n，不猜量表日期或代码频率。

## 来源敏感性与功能验证

CI保留已有的刺激同步污染/通道清理敏感性，Artifact独立报告，不把更强解码器自动当更纯神经信号。没有新增证明时，不作纯神经来源或临床诊断声明。

公开HSM、理解或努力变量只使用已核实可连接的字段，在固定方法之后作低维功能验证。目标分布和统计单位由真实数据决定；不能由于这轮未产生临床收益就转成“EEG没有临床信息”。也不以抢救阳性为由启动几十种问卷终点搜索。

## 主图建议

1. 问题与方法：局部通路、dense预训练读出、候选互补以及公开/私有角色。
2. 方法能力：时间结构/目标/读出/初始化的公平比较，含真实风险与原生/probe。
3. 人群与注意：同协议HA/CI/TH，另一队列HI/NH；共同与适配的差异。
4. 时间组织：同条件局部曲线、独立窗口与联合风险；有充分输出时的目标层级。
5. 儿童与私有：Federici人类分组/同儿童声码器配对；私有验配阶段与历史条件当前证据。

这些是需要实验填充的图，不保证每图得到预期阳性；修复经历置方法补充，不取代科学图。

## 每轮报告格式

按 `templates` 内容（本包reports/ROUND_REPORT_TEMPLATE.md）写：
1. 新建立/改善的能力，给精确配置与可复用产物；
2. 全部主比较（包括弱值、反向值和失败状态）；
3. 对主线新增了什么听觉证据、哪些仍未知；
4. 竞争解释与可检验干预，不直接写关闭/天花板；
5. 新方法、数据与统计单位的改动及其来源；
6. 下轮完整实验与技术依赖。

修正旧数字时保留旧新对照和原因。任何“无收益”句子都带配置、任务、人群范围；禁止用总作业数作为“已经试尽”的论据。


---

# 10 · Server接入、排程和交付

## 1. 目录与状态

在研究工作副本新增 `auditory_alignment_v3/`、`docs/auditory_alignment_v3/`、`results/auditory_alignment_v3/`、`private/auditory_alignment_v3/`。ALN2代码与结果不覆写；可引用复用的checkpoint、预处理和分折清单。先记录实际HEAD；若与本包基准不同，检查新增差异并写接入回执，不自动回退用户代码。

本包代码是独立的聚类统计/校准/张量读出参考，不是已完成的真实训练控制器。以下仍由server接入：真实backbone层hooks、原数据loader与物理时间、同一声音合同、Slurm worker、逐fold教师和迁移、查询级结果导出、隐私发布扫描。不得把本地合成测试通过写成EEG训练通过。

## 2. 建议接入顺序（不是成绩门槛）

**并行CPU**：02重汇总，已有输出的私有校准重评价，登记数据/target合同。

**GPU主通路**：A局部因素/目标比较；B固定backbone读出与五类适配。

**依赖后接续**：C残差与融合使用对应fold的已完成局部base；D注意/个人适配使用合法base；E迁移/蒸馏使用合法donor/teacher。私有通用训练与GX不依赖公共阳性，可立即运行。

先做张量/形状/梯度/时间访问/身份正确性测试，再完整训练。测试不设置最低检索成绩；短probe是查接口，不是筛掉研究方向。

## 3. 计划文件与执行量

`configs/experiment_families.yaml`定义有问题导向的实验族；`scripts/expand_plan.py`生成`plans/units.jsonl`。行包括：数据、目标、折、seed、配方、信息访问层级、任务类型、逻辑依赖及结果来源。所有新行初始为`planned_needs_binding`，不伪称已运行。精确行数由生成器输出，不手工编一个GPU工作量。

default覆盖seed3401；指定主比较使用3407/3413面板，先登记、不只复跑赢家。计划包含训练、阶段训练、support适配、重评价和统计，它们**不是相同成本的拟合单元**。运行清单可以据训练侧问题扩展，记录增补；不以matrix完整性继续消耗已知错误接口的算力。

未绑定的dependencies是逻辑需求：`local_base_same_fold`、`public_donor_no_target_identity`、`teacher_selected_training_only`、`human_identity_manifest`。server在提交前将它们解析为具体hash/路径，并验证真实来源。无需基于成绩批准，但不允许缺checkpoint时偷偷用测试模型/别的折替代。

## 4. 学习率、训练时长与输入预算

初始工程配方见protocol.yaml。完整训练的小模型与FM/adapter分别选择合理学习率；训练侧开发内容允许多个固定块，不只一个短单元。保留头预热与联合训练的比较；epoch起点不是终止上限，开发仍改善时登记续训。失败/抢占允许从完整状态恢复，恢复不改实验身份。

不同方法统计batch、梯度累积、片段数、query数都记录。匹配数据量和计算量是两种不同控制；至少一张表在相同数据暴露下比较，不把训练时间差写成神经差异。

资源默认继承10-GPU同时运行上限、大模型一GPU一个训练；server可按研究者当前规则调整。模板不擅自占GPU，不提交任何作业。主训练不要被一大批CPU合成模拟占满资源。

## 5. 复用与修复

只有输入清单、分折、目标合同、模型/头、损失、适配、seed与输出协议完全匹配才复用训练结果；重汇总或校准可引用旧预测但产生新评价版本。每个复用记录指向实际源文件hash。

新head改变teacher输出时，旧teacher-target失效但原始pretrained checkpoint仍可复用。旧chmean只作legacy；不得进入主teacher/donor。来源不明或错折的产物不使用，不是“模型表现差”的科研停止理由。

禁止用`strict=False`隐藏跨通道迁移的漏载：为每条迁移保存loaded/missing/new keys、参数量与解释。允许合法的新输入层/任务头，但不能静默丢掉绝大部分网络后称“预训练迁移”。

## 6. 单元最小记录

计划与结果schema分开。每个结果含resolved_code_sha、source_checkpoint/hash、task/split/target/candidate hashes、time_access、真实读出、数据独立规模、训练时长、seed、fit/cal/test来源、query损失及组聚合。失败保留原因，基础设施失败不归为方法阴性。结果原子写入，只有完整记录才进统计。

逐人量、身份键、预测、checkpoint和私人路径留服务器。对外发布仅文档、代码、聚合、配置hash和必要run receipt；本包生成不等于授权自动push所有私有产物。

## 7. 交付清单

- `IMPLEMENTATION_RECEIPT.md`：各模块接入、与本包偏离、实际默认值和时间/数据合同。
- `FEDERICI_REAGGREGATION_RECEIPT.md`：实体/儿童单位修正及全模型新表。
- `FULL_RESULTS.md`：完整矩阵，原生/共同读出与真实风险分开。
- `METHOD_PROGRESS.md`：局部、dense、互补、初始化的主要方法对比。
- `HEARING_GROUP_TIME_RESULTS.md`：人群×窗口×注意，不预定方向。
- `PRIVATE_TRANSFER_DEVELOPMENT.md`：私有任务能力、校准、迁移、年龄/阶段与历史结果。
- `NEXT_INTERPRETATION.md`：按09的建设式结构提出下一步。

每轮说明哪些仅在已有汇总上重算，哪些重新训练、哪些新增数据、哪些只是实现检查。不得用“全部完成”掩盖逻辑依赖未绑定或数据子集变化。


---

# 11 · 附带参考代码能做什么、不能做什么

`src/aln3_reference/`与当前仓库训练器解耦，避免发布未经真实数据验证的“万能runner”。

| 文件 | 可直接使用的能力 | 不包含的部分 |
|---|---|---|
| aggregation.py | 规范长表的身份/条件等权聚合、HC/HC-v配对、人类与phantom分离 | 私有JSON导出、真实身份核实、复杂年龄模型 |
| calibration.py | 正斜率仿射logit校准，截距与稳定NLL | 自动选择临床标签、query校准 |
| readouts.py | 通道保留的相位线性/dense query decoder；零初始化残差输出 | CBraMod/REVE加载、物理时间和实际层hook |
| metrics.py | 对数损失、配对真实风险增量、候选评分 | 实际候选生成、历史条件分布估计 |
| scripts/expand_plan.py | 确定性配置展开、主seed面板、逻辑依赖登记 | Slurm自动提交、checkpoint自动择优 |
| scripts/reaggregate_federici.py | 对规范CSV执行分组/配对重汇总 | 用字符串猜儿童身份 |

参考代码的显式shape/finite/身份检查是数学和工程正确性检查，不是AUC/显著性门槛。测试样本全部人工合成，名称带SYNTHETIC前缀，不能被误作真实队列结果。

运行：
```bash
python -m pip install -r requirements-reference.txt
PYTHONPATH=src python -m pytest -q tests
python scripts/expand_plan.py --config configs/experiment_families.yaml --out plans
python scripts/validate_package.py
```

输出在reports/中记录实际测试状态。测试只覆盖这里提供的模块，不证明已修复server数据集、FM接口或统计结果；真实集成后应运行小规模工程端到端检查，不设置科学绩效准入线。


---

# 来源索引与证据等级

本包依据最近一轮审阅及以下ALN2来源编写；代码和结果钉在同一提交。数值由仓库报告，不声称本地重新计算了真实EEG。

## S01 · ALN2修复后基础模型结果

类型：result_report。位置：§1–3；Federici混合总表须按S04–S07重汇总。

- [docs/auditory_alignment_v2/REPAIRED_FM_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/REPAIRED_FM_RESULTS.md)

## S02 · ALN2全部结果

类型：result_report。位置：A_TIME、目标、私有、注意、覆盖、适配、多seed；结果为已拟合模型条件汇总。

- [docs/auditory_alignment_v2/FULL_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/FULL_RESULTS.md)

## S03 · ALN2实现回执

类型：implementation_report。位置：§2–7、§11–12；实现与修复、教师、输入、配方。

- [docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md)

## S04 · 数据与身份加载

类型：code。位置：load_federici；人类/HC-v/Artifact、共享identity。

- [auditory_alignment/data.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/data.py)

## S05 · 基础模型评价

类型：code。位置：test_only测试、共同readout、patch评分。

- [auditory_alignment_v2/eval_fm.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/eval_fm.py)

## S06 · ALN2汇总

类型：code。位置：rows_of、table、summ；按输出键聚合而非真实儿童身份。

- [auditory_alignment_v2/aggregate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/aggregate.py)

## S07 · 旧汇总的行提取

类型：code。位置：unit_rows；gain=错配NLL−真实NLL。

- [auditory_alignment/aggregate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/aggregate.py)

## S08 · 局部时间编码器

类型：code。位置：LagLocalBranch、TokenEncoder；40ms/20ms为工程设置。

- [auditory_alignment_v2/temporal.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/temporal.py)

## S09 · 修复后空间头与probe

类型：code。位置：SpatialPatchHead、ProbeReps。

- [auditory_alignment_v2/fm_readout.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/fm_readout.py)

## S10 · 基础模型输入和patch级训练

类型：code。位置：patch范围、0.15*z工程假设、1.2s声音目标。

- [auditory_alignment_v2/foundation_adapter.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/foundation_adapter.py)
- [auditory_alignment_v2/train_fm.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/train_fm.py)

## S11 · 私有原生头评价

类型：code。位置：evaluate_private；NCE温度无截距、CS类别核后验。

- [auditory_alignment_v2/evaluate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/evaluate.py)

## S12 · 历史窗口常量

类型：code。位置：WINDOWS_MS；legacy右端多一采样点。

- [auditory_alignment/model.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/model.py)

## S13 · 固定声音目标

类型：code。位置：训练侧标准化、固定半正交映射。

- [auditory_alignment_v2/audio_targets.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/audio_targets.py)

## S14 · 蒸馏与公共donor

类型：code。位置：与S03共同描述旧teacher/donor路径；不复制私有权重。

- [auditory_alignment_v2/distill.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/distill.py)
- [auditory_alignment_v2/donor.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/donor.py)

## S15 · ALN2发布回执

类型：publication_receipt。位置：公开与扣留产物范围。

- [docs/GITHUB_PUBLICATION_ALN2.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/GITHUB_PUBLICATION_ALN2.md)

## H01 · 历史附件只用于版本关系

《听觉 EEG 公开–私有联合研究方案 v3（JBHI）》2026-10-02：§2的“早期正常、差异只在晚期”、§11和§13的自动地图稿/绩效门槛，均是当时的候选方案；本包明确停用为当前命令，不篡改历史原文。其“公开主线＋私有独立问题、不做ERP主线”的偏好保留。

2026-09-24至09-27的《深挖计划》《发散_解码视角的候选方向》《新结果分析_PF_PF2_DV》《未用数据发散_标签复原与队列扩张》及附录包含早期“关闭/天花板/数据已用尽”表述，不作为ALN3的科学结论或停止规则。未在本包中复刻其过时数字。

## 等级声明

- **报告事实**：S01/S02明确列出的数字及其当时协议。Federici混合总表特标待重汇总。
- **代码审阅结论**：S04–S07给出的实体/身份汇总路径，S11的温度无截距；server核实实际产物后修正输出。
- **解释假设**：时间接口、读出能力和预训练适配可能限制对齐；不是唯一已确定原因。
- **新实施规格**：dense query、相位线性、残差互补、训练侧教师政策、概率仿射校准、实验配置和代码参考；均是ALN3拟开展内容，无真实性能承诺。
