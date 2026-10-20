# ALN3.4 · 阶段证据、竞争解释与下一轮实验

**服务器完整执行文档 · 2026-10-16**

当前阶段：持续探索，不要求现在写论文或冻结最终故事。兼容ALN3.3，复用现有实验；本轮依据用户简报而非新的远端检查。

入口：[启动指令](AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/SERVER_START_PROMPT.md) · [来源](AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/SOURCE_INDEX.md) · [比较卡](AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/plans/comparison_cards.json)


---

# ALN3.4：现在直接执行

**当前目标：继续几轮方法与听觉探索。最终论文主题表述、正文／附录和定稿时点均不是本轮的先决条件。**

| 工作 | 现在的决定 |
|---|---|
| D 的 240 个已完成多 seed 记录 | 对账后写一份简短分析说明，立即配对汇总；不重训、不等“措辞冻结” |
| TRUE_FULL、访问匹配与现有主要面板 | 按原合同完成；新增 TF–L1 多 seed 对比先复用已有同 seed/同 fold 记录，只补真实缺项 |
| CBraMod 真全量 | 与 local 并列为主要候选；下一轮优先检验数据需求、优化过程、公共先验与个人适配 |
| REVE | 保留随机与预训练的代表性比较，尤其保留 native/unified 差异；不判整类预训练无效 |
| 公共听觉先验 | ALN3.3 已授权定义继续实施；工程就绪即提交，不等本包其他分析 |
| SC/RS | 先用已有预测、日志或可用 checkpoint 检查 base、残差、声音预测与开发泛化；同时推进有限的新融合比较 |
| D 旧 fixed-grid/旧 complement policy | 已完成部分完整存档／透明汇总；未完成特定旧执行保持暂停，不清空全局 hold |
| D 新 aligned/true-full 版本 | 使用新 ID，任务内开发选择；可从合法上游逐 fold 启动，不等待互补成功 |
| 注意整合器 | 两种候选顺序成对评价／交换反对称评分；尽量复用分数。该修正不阻塞独立主干训练 |
| 科学分析／私有任务 | 与方法训练并行，固定候选后研究内容、时间和适配；不把方法总表的局部解释限制扩成全项目禁令 |

## 接入动作

记录现场 HEAD、有效记录、checkpoint 可用性与 running/pending。用 `plans/actions.json` 对账，将 `AGENTS_APPEND.md` 放到规则顶部并保留旧记录。此后按实际数据依赖启动；不必再请求统一的 go。

只核对与本任务有关的张量、时间访问、参数更新、身份划分和输出正确性，不新增任何准确率、显著性、信度或“保留信息比例”的开工阈值。独立模块无需互等。

## 下一次报告

先报告实际已提交／运行／完成、新建立的能力与完整方法差值，再说明仍然竞争的解释和下一项干预。不再以“框架待定”“数值永远不变”“请选择正文或附录”作为交付结尾。


---

# 00 · 从“待定框架”改为证据驱动的继续探索

## 工作目标与来源层级

工作主题保持：通过声音监督与信息论驱动的依赖学习，构造可在听者之间使用、保留时间组织的 EEG 表征；研究预训练、群体覆盖和个人适配怎样改善声音内容与注意目标的读取，再在 HA、CI、正常对照和儿童任务中检验。当前仍允许几条竞争方法并行，不要求现在选择唯一故事或写论文。

本包的数值来自用户上传简报 [B01]，不是本次重新计算。ALN3.3 的公共预训练合同是已批准的执行设计 [P33]。下文的实验、优先级和数学示例是新决定／推理 [D34]，不冒称已有结果。原简报里广泛的措辞限制仅作为历史记录，不作为新执行规则。

## 管理方式改为三种记录

| 类型 | 操作 | 不需要做的事 |
|---|---|---|
| 结果勘误 | 记录旧版本、具体错误、受影响范围和修正版；可复用预测就不重训 | 为维护冻结而保留错误；修改所有无关历史实验 |
| 数据启发的探索分析 | 一份简短说明写已见信息、问题、估计对象、比较／不确定性与输出，然后执行 | 假装是盲验证；为普通措辞申请许可；每个图一轮审批 |
| 新训练／新数据合同 | 先定义训练/开发/test、输入目标、选择、对照和执行版本，再完成训练 | 用单次 pilot 的 AUC 或 p 值决定其他独立任务开工 |

对旧结果沿用原定主要终点和同时区间；新探索可以另定义合理量，但明确标识，不因结果方向而替换主要量。已有区间跨零不等于效果为零，一侧较好也不等于普遍优越。不能仅计数 I>0/I<0，应展示效应与适用范围。

## 直接撤掉的执行阻碍

- 不再要求决定“放正文还是附录”之后才汇总或训练。
- 不再要求负向结果描述必须预先登记措辞；较差、较好、尚未建立均按真实比较报告。
- B/C 总表不能独自支持组间效应，这不构成研究 HA/CI/年龄的全局禁令。
- 不采用“冻结文字只能收紧”的规则；科学解释可以被新证据修正。
- 不因一族缺少登记的面板汇总语句，就让已完成多 seed 记录闲置。

## 不改变的原则

同一批参与者被反复分析后，新 seed 不恢复独立盲验证。更多作业不增加样本。所有有效不利结果保留；不按临床／年龄显著性选择模型，不削弱线性或 local 参照。继续完整实验，但允许根据具体问题与信息价值调整资源；这不是对数据或方法家族的不存在证明。

传统核 CS 与 NCE 竞争；不引入 VCS-QMI 或未发表的神经 critic。不做 ERP 主线，不以脑龄／临床量表预测替代本任务；不要求现在联系医生或新增采集才能继续。最终论文结构暂不决定，稳定的是听觉问题，不是必须成功的方法名单。


---

# 01 · 这份简报改变了哪些研究判断

所有数值均转录自 [B01] 指定行，尚未由本包重新汇总。以下“工作判断”不是机制或跨数据集普遍定律。

| 证据 | 源范围 | 工作判断与下一项问题 |
|---|---|---|
| CBraMod 真全量、同数值 LR/日程/数据/选择：12/12 配置预训练风险更低 | B01 L257–L278；seed 3401 | 提升为主要候选。检验初始化如何影响学习速度、目标数据需求和迁移，不再只查“是否有信号” |
| one-step 3e−4 的预训练−随机 ΔR：FAU +0.120 [0.083,0.156]；DTU +0.231 [0.160,0.302]；Federici +0.055 [0.013,0.096] | B01 L260；95%同时区间，bit/5秒查询 | 较大 LR 下仍有收益，不完全等同随机小 LR 学不动；未分离优化与可迁移内容 |
| 预训练 CBraMod 对同访问 L1 的12格均风险更低，ΔR +0.127…+0.232 | B01 L264–L278 | 与 local 并列发展；参数量、结构、监督与优化仍不同，不能直接称纯信息增加 |
| REVE 没有一致初始化优势，随机架构在 FAU/Federici若干格强；native/unified方向可不同 | B01 L259–L280、L350 | 保留代表配置、学习曲线及两种读出，不得直接称“预训练无用” |
| SC 的 DTU融合相对自己的重映射 local_only 好，但所有SC水平仍差于原base直接读出 | B01 L558–L565 | 先做真正同系统成对比较，不用弱化的新base宣称净收益 |
| RS 多数选中非zero epoch，测试 ΔR 接近0，未报残差或开发变化 | B01 L578–L585 | 区分归一化消除、读出不变性、无声学增量和跨人选择失配 |
| D 的240个3407/3413面板记录已完成、未汇总，只覆盖NCE指定子集 | B01 L763–L767 | 立即汇总。不能把未覆盖的CS/coverage/out-low-rank也写成三seed |
| SCI_R2 spec/flux和部分Lz有嵌套预测增量；负lag仍可读 | B01 L887–L917 | 分析声音内容及时间特异性；不等同语言真值或精确潜伏期 |
| C3收敛背景版本仍报告约70%保留 | B01 L1133–L1149 | 更新旧“只因背景未收敛”的批评；仍是指定模型量，不是真实语言信息比例 |
| 私有GX最高AUC约0.553；多个先验/迁移增量较弱，历史条件与阶段未稳定建立 | B01 L1151–L1167 | 保留任务与有效原生头；继续定点先验、时间和适配实验，不转成预定校准／失败案例 |

## 当前候选排序不是论文排名

**主要候选**：有效 local L0/L1，查询锚定 CBraMod 真全量；后者的 matched 初始化面板优先完成。

**竞争候选**：代表性 REVE随机／预训练、公共声音先验及跨人监督、适配友好群体训练。

**继续探索但不强制成功**：低复杂度组合、任务适配教师与残差。旧弱分支的结果保留，不因其写进旧包就持续原样扩张。

## 待区分的四类解释

1. 初始化改善优化速度，还是在充足训练下仍改善目标任务？有限预算内不能宣称极限能力。
2. 任务适配是否提升原生对齐，还是主要使统一线性桥更好拟合？二者都是可用收益，但对象不同。
3. 好的群体表征是否更易用少量个人支持适配？普通训练后适配与episode训练需要公平比较。
4. 模型更好后，听觉内容、时间曲线与组间关系是否更可重复？不能用平均检索提升代替这一证据。


---

# 02 · 预训练怎样被用起来：主要方法实验

## A. 完成当前匹配结果的成对证据

继续现有 ALN32_TRUE_FULL one-step 两档 LR 的预训练／随机面板；若已完成，直接汇总。与 L1 的多 seed 对比先查找同 seed、fold、声音目标和评价合同记录，允许新透明分析复用；仅训练真实缺项。不能把“旧附录未指定TF-LOCAL面板”理解成必须重新跑全体。

固定数值LR/日程比较识别的是**这个预算下的初始化效果**。另可比较两侧经过相同开发预算各自选配方后的系统性能；后者叫开发选择后的配方比较，不与前者混成一个量。

CBraMod one-step 3e−4作为新深入面板的明确起点，1e−5保留为已有并行参照；这项选择是看过结果后的设计。REVE保留随机／预训练、one-step代表比较及native/unified读出。不要再对两个主干强制同一种warm-up结论。

## B. 学习过程、目标人群量与内容量

先复用完整曲线、已有checkpoint和参数更新账本；只有缺少相应训练状态时新增训练。

| 轴 | 默认起点（配置，不是通过线） | 对照要求 |
|---|---|---|
| 训练过程 | 当前完整预算中1/4、1/2、1倍时点；必要的预算扩展作为一个独立比较 | 相同优化步数、batch暴露与读出预算；已删除checkpoint不假装存在 |
| 目标训练人数 | 外层train内嵌套约25%、50%、100%身份，内容固定 | 同一子集用于pretrained/random/local；外test不变 |
| 不同声音内容 | 外层train内嵌套约25%、50%、100%内容，人数固定 | 按完整内容/物理块抽取，不能将密集重叠窗当新内容 |
| 预算扩展 | 对代表性完整数据pair使用同样约2倍预算的独立版本 | 不在测试上选择延训到哪一轮；开发仍改善时同规则允许续训 |

人数轴与内容轴不做无结构全交叉；全数据基线只拟合一次并复用。极小来源不能形成这些比例时使用最近的合法非空分组并记录，不以样本量阈值关闭任务。需要解释不同数据量和不同训练步数时，分别给matched-update与原训练预算版本。

检验的是曲线与方法差值，不拟合预定scaling law，不设最终分数必须达标，不要求单seed胜出才补pair。峰值的时间、速度和最终风险分开报告。

## C. 公共听觉先验：ALN3.3的批准继续有效

完整合同在 `inherited/PUBLIC_PRIOR_EXECUTION_v3_3.md`、`inherited/public_prior_v3_3.yaml` 和 `inherited/OBJECTIVES_v3_3.md`，原样附带。不要重新生成旧438条意向，先在server注册表去重。

第一波继续使用local共享通道映射，比较 target_from_scratch / audio_pair_pretrain / cross_person_pretrain / joint_pretrain。64Hz、125ms声音目标、源侧共享坐标、独立供体声音桥、目标队列完全留出、NCE与传统核CS不同采样定义均保持。纯EEG跨人预训练的zero-shot需供体声音桥；这不是完全不使用声音标签。

包络轨道先启动，谱结构/谱变化用真实存在的声音标签并行增加，不制造Federici缺失波形。未见电极、不同目标预处理及未知滤波来源如实记录，不把不兼容内容硬合成同一“域”。

**新真全量结果不要求重写这条local主预训练路线。** 增加一条CBraMod连续适配问题作为下一阶段比较：generic EEG → target；generic EEG → public auditory → target；random same architecture → public auditory → target。公共训练步数与数据配对，研究听觉中间训练是否带来额外帮助，而不是让所有backbone交叉全部source/loss。

公共先验不等融合结果或全部TF seed面板才开跑。供体所有标签、校准、头和开发都不得接触目标外test；供体复用需记录真正相同的数据与目标hash。无法证明通用预训练语料绝无受试者重叠时，只报告所能核实的范围，不伪造断言。


---

# 03 · 互补：先分清功能变化，再比较强单模型

## 1. 立即可做的重评价

将以下预测放在相同测试query、候选、fit/calibration合同下：原始local直接输出；SC重映射local_only；SC各融合；现有RS；有效FM单支。统一读出与原生读出各自成表，不能只比较跨文档均值。

闭式ridge是监督参数拟合，不写“完全不训练”。冻结的是编码器。记录桥、PCA、温度所用身份／内容及预算。SC原base本身见过OOF中的训练人，故旧OOF只针对ridge；旧值有效范围标清，不假装全链路OOF。

## 2. RS功能诊断：一个文件同时输出四层

设base为u，残差为r，最终表示为 normalise(u+r)。对共同query，输出：

- 残差相对幅度 ||r||/||u||；平行分量 r_parallel=(r·u)/(u·u)u 与正交分量；
- 归一化前差、归一化后差、向量夹角；
- native分数／声音预测差与unified预测差、候选排名变化；
- 开发／外test的对应值，epoch0、selected epoch与选择风险差。

这些量用于分辨解释，不设残差幅度通过线；神经活动幅值不是网络残差范数。跨query统计只是诊断样本数，推断以身份与物理内容为单位。

**数学参考 [D34]**：r=alpha*u且alpha>−1时，L2归一化后的表示完全不变。非zero epoch不等于采纳了功能修正。对于无额外逐维标准化、各向同性ridge与正交Q，U'=UQ、W'=Q^T W给出同一预测。真实管线若含逐维缩放等，不一定精确不变。`src/aln34_reference/residuals.py`和tests只验证这些例子，不推断真实RS成因。

若权重已删除，仅用已保存日志／预测回答能回答的部分；标记无法恢复的层，不为这项诊断重训整轮。必要时在代表性的、已登记新实验里保存小量功能记录。

## 3. 新的互补比较使用有效分支

现在CBraMod真全量可以是强单模型。新参照包括：

| 候选 | 用途 |
|---|---|
| local原生、同合同统一读出 | 不削弱的局部参照 |
| auditory-adapted CBraMod true-full单支 | 不是旧generic-frozen分支的替代名称 |
| 训练侧选出的强单模型策略 | 只在内层开发选择，外test不能逐人取best |
| 概率融合／共同声音预测的正则线性融合 | 低复杂度互补是否存在 |
| 有限的零初始化声音预测残差 | 相比简单融合是否值得联合训练 |
| 同架构随机/普通容量分支 | 收益能否归因于pretrained representation |

概率融合 q_w=w*q_local+(1−w)*q_fm 在开发侧选w，包含两个端点；两侧候选集合必须相同，校准只在训练侧。包含端点不保证外test不退化。可训练残差优先放在共同声音预测空间，保留epoch0；不同CS latent没有天然共用旋转坐标，不能直接相加后命名为声音残差。

正确FM、错配FM或position-only敏感性若用于归因，保持local输入固定。测试干预可能是分布外条件，不能单独证明因果信息来源；训练对照和真实风险改进需共同看。无需等FM单支超过local才研究互补，但不能只超过重映射弱base就宣称整个系统提升。

## 4. 新选择面向整条链的新听者

**首选新执行**：outer-train划分inner-fit与inner-dev身份，base、任务适配FM、桥和残差只用inner-fit训练，inner-dev用于配方/epoch选择；outer-test始终留出。方法固定后可按登记规则在outer-train重拟合，不能重用outer-test选择。通用预训练的语料范围另列，不把无法核实的历史语料当作已清空。

**资源替代**：使用已存在的合法fold-specific base交叉拟合，但逐项检查该base从未见对应dev身份和排除的内容。只留出残差头训练，不满足全链路选择；可作为效率对照，明确命名。

新强单模型或分支就绪即可逐fold运行，不等全矩阵。若没有互补收益，保留单模型路线并改变具体方法，不自动转为“互补不存在”论文。


---

# 04 · D多seed立即汇总，听觉下游使用新执行版本

## A. 已完成面板现在汇总

[B01 L763–L767]报告240个新增seed记录已complete：NCE的D_ADAPT none/input_spatial，以及D_ATTENTION attended/align+sel两个整合器。先读取现场记录确认，不把文档时点当实时状态。

写一份简短分析说明：已见3401结果、哪些面板值已被查看、配对键、终点、身份汇总与同时区间范围。然后立即计算各seed差值、身份内seed平均差值和覆盖表。保留原D_ADAPT的gain主表，新增真实query风险作为明确的新分析；native/unified和rank/accuracy分开，不换掉不利的主指标。

每名身份只计一次；fold/content重复先按原合同合并，seed不是新样本。报告跨seed范围，不把3个seed当充足的总体随机性估计。缺失pair不填0。CS、coverage、output_low_rank和selection_only不在该面板，不能共享三seed结论。

## B. 学习型注意整合修正

基于简报的异常native列和此前代码审查提出修正，**尚未证明其解释所有异常**。恢复可用逐窗原始分数，候选顺序采用成对交换：同一观察评价(A,B)及(B,A)，标签随之反转，二者不能分到不同train/test。平均分数与所有学习型方法用相同测试窗。

推荐新评分：l(d)=0.5[h(d)−h(−d)]，p=σ(l)。则p(−d)=1−p(d)。模型训练也提供成对顺序。h可继续用固定摘要；或用对|d|等交换不变量的权重再加权d。不能让真实注意标签以隐含候选位置进入输入。

保存旧版本结果，不静默覆盖。5秒只有一个段时只是阈值／校准问题，不称时间整合。5/10/20秒在相同窗口长度内比较方法；不要把增加证据时长当成响应潜伏期。尽量重新评价已有分数，缺分数时从保存模型评价，不默认重训全主干。

## C. 个人适配：限制形式，而不是假定C×C已经足够小

当前input_spatial为C×C；64通道有4096个参数。新比较增加：

A_diag=I+diag(d)，A_rank=I+UV^T，A_full=I+M。

默认rank4起步，64通道时U/V共512个参数；同样把rank作为可调配方，不作理论最优。低秩identity初始化不能让U和V同时全零，否则两个因子都无一阶梯度；参考实现U小随机、V零，输出仍严格identity。

保留none、full-spatial、output-low-rank既有基线；增加diagonal/low-rank-spatial。沿用同一10%/30%支持及固定后70%查询以复核，记录实际分钟、独立内容和有效样本，实际EEG/滤波访问不跨support/query边界。

普通群体训练+同adapter，与源人support/query episode训练+同adapter成对比较；群体训练数据暴露和个人支持一致，额外计算另报。第一阶段local与真全量CBraMod并行，代表性REVE保留；不自动把全部backbone×loss×rank×支持做大交叉。

时间adapter仅在声明可访问的lag内组合，不把query窗外信息回流至早窗。以上均为同会话已知刺激监督，不叫无标签TTA或跨会话复现。组差收缩不是训练目标。

## D. 新策略臂的决定已经给出

旧fixed-grid/旧C执行保持原记录，完成部分如实汇总，未完成特定ID继续暂停。新策略使用`new-aligned-true-full`版本，候选含local与合法真全量CBraMod，代表REVE；不默认带上未证明有净收益的互补策略。

用目标任务的内层开发选择候选，不能按外test或HA/CI显著性选。若把一套声音检索模型直接迁移到注意任务，也单独记录其训练任务。性能是否迁移由实验回答，不由B的总分代答。合法checkpoint就绪后逐fold启动，无需再次统一go。


---

# 05 · 声音内容、时间组织与私有儿童：方法实验并行

## 1. 固定候选，不固定想得到的生理结论

代表模型先列出有效local、查询锚定CBraMod真全量及匹配随机、代表REVE、之后完成的公共听觉先验。方法选定依赖训练侧任务，不依赖组差或年龄。对这些候选完整生成相应分析，不只给最好看的模型作解释图。

科学问题：方法改善发生在何种声音结构、哪个可访问时间范围、哪些听者的适配前后？解码表现、表征动态与因果神经机制分层。允许分析HA/CI/年龄，不因为旧B/C总表的限制而禁做；不预定早声学/晚语言、CI低=神经缺陷或HI强=听得更好。

## 2. 内容分析

延续SCI_R2的env→onset→spec→flux→Ac→Lz，使用既有主要同时区间，不事后选逐点CI来改变主要判读。现有spec/flux增量是指定顺序和模型下的预测增量。用解码方向的固定EEG表示读对应声音属性，并与前向参照并列，不要求二者峰重合。

后续可加真实波形支持的F0/voicing；数据不可得时明确缺失，其他分析照常推进。不将Whisper深层自动称为纯语言，不将两个单独训练目标的分数相减解释成独有语义信息。C3收敛背景约70%结果按其新版本作为证据，不继续重复旧“背景未收敛”批评；仍不换算成真实语言信息比例。

## 3. 时间泛化与负lag

保留原生时间合同，另在共同绝对ms范围和实际频带可比时做面板；成人“晚”与儿童“早”可能覆盖相同时间，不能仅凭标签建立发育差异。Federici原缓存2–8Hz，不能恢复缺失频带；标题错误可直接修正并记版本。

负lag可读性分别考虑声音自相关、滤波双向扩散、真实未来信息访问与train/test泄漏。一个因果响应也可因声音自相关而预测当前声音。不能通过“正lag−负lag”获得纯神经信息。因果滤波、边界、声音历史参照作为敏感性分析并行，不成为其他模型训练或描述性分析开工条件。

时间泛化比较在τ训练、τ'评价。跨时间低于0.5可能与符号翻转有关，不自动认定两个独立发生源。若加入符号/小旋转校正，只能训练侧拟合；不能测试时取max(AUC,1−AUC)。比较未经训练、原始线性、监督表征与适配后表征。

## 4. 组别与适配

同任务下计算个体适配前后差，并直接比较组×适配的差中之差，不能用“一组显著另一组不显著”。年龄与佩戴经验的定义、共线性和共同内容支持写清；有适当支持时做连续关系，不反复切年龄箱找显著。组内重复性与合并组重复性分开，防止群体差放大相关。

Federici：HC、CI、HC-v为独立身份；不做未经证实的HC–HC-v同儿童配对；phantom是一个实体的多会话，单列。相同过滤不能消除不同刺激/年龄支持的混杂，全部数据与共同内容敏感性分别报告。

## 5. 私有HA任务的独立角色

保留GX原生、local-CS/NCE、已定义通用先验与特定公共迁移对照。公共连续语音先验只迁移EEG结构，当前类别头重新训练；私有epoch本来事件锁定，不能机械复制成人“固定patch没锚定”的故障解释。

下一轮围绕三项：当前声音类别的可读性；在声明历史背景之上的真实预测增量；这些结构在时间与个人适配后的变化。AUC、自然NLL、history增量分别报告。GX类别AUC为正，不自动意味着history之外增益已建立。新方法不因某个指标低而禁止年龄/阶段分析，但解释应结合测量本身的不确定性。

正斜率仿射作用于同一组分数仅改变概率不改排序；两个不同模型汇总AUC相同，不证明它们逐样本排序完全相同。校准是评价接口，不成为替代儿科研究目标的新故事。

不把小规模NH/验配早期组当作充分的独立临床验证；也不以其精度不足预定数据无用。已有多轮已见结果如实披露，新seed与新内部划分不伪称新外部队列。无需新增医生联系或采集才能执行当前方法研究。

已确认的个体级结果发布按现有范围继续，不再请求同一隐私授权。不得因本包把原始数据、姓名或身份映射加入发布。


---

# 06 · 成对多seed、选择与复用

## 主问题而非“每行乘三”

| 比较 | 行动 |
|---|---|
| 已完成D_NCE指定面板 | 立即汇总3401/3407/3413，输出覆盖；不补未请求的所有D配置 |
| TRUE_FULL one-step pretrained vs random | 完成已登记两档LR匹配pair，不只重复阳性；warm-up未覆盖则明确 |
| TRUE_FULL vs same-access L1 | 查相同seed/fold/内容/目标/评估合同现有记录，创建探索性配对汇总；只补确实缺失的参照 |
| 新公共先验 | 先按ALN3.3广覆盖与既定成对面板进行，供体与target随机性都记录 |
| 新个人适配/episode | 普通训练与episode训练使用相同adapter/support；上游模型seed成对，不只改adapter随机性 |
| 新互补 | local、强单FM、简单融合／残差和来源对照一起报告；不同合同不得凑对 |
| 旧fixed-grid/旧C重复 | 保持特定执行暂停，不为完整率复活全矩阵 |

## 配对键

至少核对 dataset、subject_fold、content_fold、split_hash、target_hash、input_access_contract、evaluation_version、training_seed；初始化或head恰为自变量时允许该字段不同，但列明。访问不同的比较可以做，命名为访问扩展而非纯架构/初始化。特殊L0/L1模型对比使用各自合同，配对程序不能强迫等同。

每个outer-test身份先按原候选/内容规则汇总；重复fold测试的TH只作为同一身份平均，不当多个新人。每个seed给出配对效应，再给身份内seed平均及跨seed差异。条件于训练模型的身份bootstrap不包含全部训练随机性；3seed也不是精准估计无限种子分布。

旧primary family max-t继续。新增分析在读取新配对值前写简短说明；如果值已经看过，诚实写已见，仍可分析但不叫预先盲验证。不能因为一次未预登记就禁止有用分析，也不能通过新登记抹去已经看过的信息。

## 整条训练链的选择

新主方法的开发组应在base、任务适配、桥与残差中均未参与拟合；供体阶段也按明确身份与内容划分。旧开发组只对某一层未见时保留原称谓并注明范围。不能把训练身份上的留出内容选择等同新听者选择。

模型选择优先使用定义明确的真实开发任务风险/准确率；gain作为正确配对敏感性另报，不将其自动等同风险改善。对于已有用gain选checkpoint的单元，不篡改记录；有完整保存曲线时可新增选择规则敏感性，否则新执行中比较。校准数据不与其拟合读出重新混用而不披露。

## 资产复用与排程

先读取现场manifest；已删除checkpoint只列不可用，不能假定可重算。可用单元记录、逐人预测、分数、日志和当前权重分层复用。更正标签或新增聚合不改原运行hash；真正更改输入、初始化、训练或选择需新execution id。

CPU重汇总、少量评分重评价、GPU主训练并行。10-GPU上限保持。不要让公共先验和独立private任务一直被旧FM worker排队占满；按已授权的实际调度能力公平推进，不承诺本包未测量的小时数。


---

# 07 · 报告改为“证据 → 问题 → 实验”

## 第一批交付

1. `D_MULTI_SEED_RESULTS`：已完成面板的真实覆盖、配对结果、native/unified与缺项，说明评分更正范围。
2. `PRETRAINING_LEARNING_EVIDENCE`：CBraMod匹配初始化、TF–L1复用面板、REVE代表对照与学习轨迹；不把12格当12独立复现。
3. `COMPLEMENT_FUNCTION_REPORT`：直接base/SC-base/融合的同合同风险，RS功能四层及dev/test差；资产不可用处明示。
4. `PUBLIC_PRIOR_EXECUTION_STATUS`：实际已注册、提交和完成的训练，不再只是一份待定草稿。
5. `HEARING_CONTENT_TIME_ADAPTATION`：固定候选的内容、时间、人群与私有任务研究进展，以及仍未检验的问题。

每张结果表标真实来源版本、实际seed范围、身份数、目标和单位；不需要重复几十条“允许短语”。稳定的科学对象写清即可。

## 新报告模板

按 `templates/EXPERIMENT_UPDATE.md`：当前观察（完整差值）→工作解释→竞争解释→下一干预→实际执行。最终论文标题、正文/附录、成稿与否都可保持未决定，但不能继续把它们作为实验等待项。

方法比较与新分析分开：已有统计结果可以立刻形成带限定的工作结论；解释可以随数据更正。探索得到的候选在未来新队列/内容上验证是额外证据，不能由增加seed替代。

## 代码接入说明

`src/aln34_reference/`只包含合成可验证的：残差功能指标、交换反对称评分、身份初始化adapter与严格配对工具。它不加载EEG，不替换当前CBraMod/REVE实现，不包含Slurm控制器。`scripts/audit_seed_pairs.py`只读用户提供的标准化元数据索引，输出可配对/缺失项，不按性能筛选，不提交或取消作业。

测试覆盖数学/张量/元数据语义，不证明真实数据对齐或模型有效。生产server仍需绑定实际tensor轴、更新范围、input support、split和target hash。工程检查应短而针对真实错误，不是一个新的科学performance gate。

## 来源与版本

主输入 `sources/ALN3_BRIEF_20261016.md`原样保存，hash在`SOURCE_INDEX.json`；包含旧规则与已经看过的结果，**不是本包生效指令**。ALN3.3公共合同原样保留。未在本轮查看新GitHub提交；现场若已实施部分工作，直接复用并记映射，不回退新代码。

包内所有任务卡是执行意向，非生产作业行，没有声称某任务已经提交或完成。发布授权继承，勿再次询问。需要超出既有资源或数据权限时仍按真实范围处理；这不影响已批准模块继续。


---

# 附录 · 已批准的公共听觉先验合同

以下两节原样继承ALN3.3，来源[Sxx]见随后的历史来源索引。它们是公共先验这一特定工作包的已批准合同，不覆盖本包对真全量CBraMod和探索模式的新决定。当前即实施，不重新等待ADDENDUM_13的方向确认。

---

# 03 · 公共听觉预训练：ADDENDUM_13现在按什么实施

本节将旧草稿待决项转为**新的作者执行决定**。数值默认是起始配方，不是效果门槛；确需调整用供体开发数据登记，不用目标测试挑选。[S05]

## 1. 任务与四种训练来源

| 版本 | 预训练 | 目标队列阶段 |
|---|---|---|
| target_from_scratch | 无公共预训练 | 同一新合同的小模型从头训练 |
| audio_pair_pretrain | 源EEG与声音配对 | 源头零样本（仅连续语音）＋目标训练侧适配 |
| cross_person_pretrain | 同刺激/时刻/呈现/任务、不同人EEG配对 | 先做供体声音桥接；再零样本或目标适配 |
| joint_pretrain | 两种监督共同训练 | 同上 |

主干先用有效`lag_local_tokens`加共享通道身份映射；不先更换为第三个foundation model。通用预训练与这里的听觉任务预训练是不同轴。目标模型参数量、目标适配数据与训练预算在对应比较中一致。

## 2. 数据与供体：不再重复审批下载

SparrKULee按server已经核对的实际清单使用；已获得85名/约159小时的当前版本以现场receipt为准，不拿论文总小时或另一个镜像人数代替。[S05,S16]

主供体池：SparrKULee＋所有**非目标公开队列**的合法人类训练数据。整个目标队列从供体预训练与供体开发/桥接中排除；private_bdf绝不进公共供体。Federici的phantom不参与供体训练。HC-v独立身份，不能按HC编号合并。

供体的fit、development、sound-bridge calibration按参与者及物理内容分组；清单冻结于第一次供体结果之前。目标外层test参与者和test刺激的任何重叠从源里排除。一个供体可以在目标外fold之间复用的条件是它完全独立于这些目标身份和内容，而不是因为同名模型就自动复用。

不同实验使用同一可配对锚点集合：核心audio_pair也使用满足跨人配对条件的锚点，避免cross-person因可用数据少而被误判。每个锚点在audio_pair中也使用同一对听者的两份EEG，各与同一声音匹配；跨人臂用这两份EEG互配，因此EEG forward暴露量可匹配。joint仍多算一个目标，额外计算单列。使用全部声音锚点的audio-only扩展可以另列，用来研究更多数据；不混作纯loss比较。跨人可用覆盖率和未使用记录数报告出来。

## 3. 新公共合同：64 Hz、物理时长、共用坐标

**新合同名 `aln33_env64_125ms_v1`，不是重命名旧`dense20ms_v1`。**

- EEG以64 Hz为共同起点；从高采样率降采样使用抗混叠处理。保留原生采样率模型作为不同合同参照；不靠上采样生成不存在频率信息。
- 主局部输入范围为查询后约0–600 ms。64 Hz实际半开样本范围为[0,38)，记录实际593.75 ms长度；所有主版本相同。需要精确600 ms的插值版本另登记，不悄悄改变旧local。
- 新声音目标明确为查询起点后**125 ms的包络向量**，64 Hz下8个采样值，半开[0,125 ms)。这是本包新设计，不声称与旧各队列8-frame对象相同。每个结果记录目标frame rate、物理覆盖和投影rank。
- 每20 ms请求一个查询，用从片段原点计算的累积整数索引四舍五入，不不断累加`round(0.020*fs)`造成漂移。在64 Hz上实际跳步是1/2样本，记录请求时间与真实样本时间。输出网格变密不代表神经时间分辨率变高。
- 8维目标到32维固定投影只能嵌入已有维度，不宣称32个独立声学维度。投影由一个固定种子生成，所有供体/目标共用，不按cohort重新抽样。[S06]
- 声音统计量只从供体fit估计，按内容/锚点去重后估计，避免同音频被多人重复计权；严格零样本保留该统计。目标监督适配允许重拟合目标训练侧头/校准，但需另记模式并对所有方法相同。

**包络来源不假装一致**：主跨队列公共轨道使用2–8 Hz包络起伏作为可兼容起点，在所有已存在包络上做明示的带限处理。来自原始音频的包络与作者缓存各记origin、原始band和filter hash。二次带限不等于恢复缺失宽带，也不保证未知原始包络提取完全相同。不能声称Federici补回了低于2 Hz的信息。

若现场缓存确认其包络合同不同，先将其标记为有版本差异的envelope轨道或采用可验证的共同滤波，不因不能恢复原始音频而阻塞其他来源。新合同与native目标分别报告，不能只用新合同成绩代替以前更丰富声音任务。

## 4. 丰富声音监督：并行第二轨道

对已有波形来源增加谱结构/谱变化或已验证局部声学特征的独立任务头；对缺波形的来源使用缺失标签mask，不填零假标签。共同时间单位仍固定。单一包络模型与multi-target模型分开ID；各头损失按合法样本和预定权重求平均，不让有更多头的cohort被隐性加权。

第一批包络训练不等待rich轨道全部完成。新增rich目标使用明确来源和extractor版本，不能将Whisper深层称作已去除声学的语言真值。

## 5. 共享通道映射

主实现为name-indexed、带符号的空间投影，再接共享局部时间网络。T3/T4/T5/T6等确定别名映射一次；电极名、实际顺序与缺失mask入合同。不先平均所有通道。

供体未见电极在严格零样本中没有可训练先验：贡献置零并报告覆盖率，不能用目标测试数据补学。目标监督适配可以开放新电极权重，从零或指定初始化开始。每个新层的loaded/new/missing及可训练参数量记录。

## 6. 零样本读出与公平桥接

纯EEG–EEG预训练没有声音坐标。**所有预训练版本**完成后，都在相同供体fit/calibration数据上拟合相同的低复杂度声音桥（源侧ridge/线性头）与温度，冻结后进入严格目标零样本评价。

跨人版本因此是“没有音频参与表征预训练＋供体音频桥接”，不是完全没用声音标签。供体桥接所用声音配对数和计算开销显式计入。NCE原生匹配可以作补充，但主zero-shot比較使用同型源侧桥；CS不假定原始余弦已经可用。

目标监督适配的主行采用实际全参数更新的小模型，目标训练/开发/外test保持原划分，所有版本相同预算。from-scratch可以共用仅由供体声音fit计算的固定目标坐标，但没有供体EEG预训练；这项声音统计使用要明示，不能暗称完全没有任何外部声音信息。无标签协方差重定位从主矩阵移到后续独立可选项，不因草稿提过就默认实现不清楚的transductive流程。私有任务只迁移EEG参数，训练类别头，不报告speech-zero-shot。

### 已预处理缓存与zero-shot命名

若目标EEG缓存已经按整条记录z-score，不能假装它完全未使用目标无标签统计。核心报告称“无目标监督拟合、沿用固定输入预处理的zero-shot”，同时记录归一化访问范围。真正source-statistics-only的版本只有原始/可逆缓存支持时另行建立；不能凭空撤销旧z-score，不能把这一元数据区别作为其他完整训练的等待条件。声音桥、温度、任务head不得用目标标签或query风险重拟合。

## 7. 训练预算与选择

供体预训练版本按相同优化步数和相同合格锚点暴露量比较；joint同时算两种损失，报告实际GPU时间/FLOPs代理，不能声称计算完全相同。起点为30个SparrKULee窗口epoch-equivalent，不是硬上限；开发曲线仍有改进可以按统一规则续训，记录结果已见范围。三种策略用同样的声学桥与供体开发任务选择checkpoint，不按目标队列组差或临床值选择。

NCE温度、CS带宽、学习率只在供体/目标训练侧规定的开发预算内选。不要为每个模型临时开新组差/行为终点搜索。按所有目标outer/content folds完成适配，无perf gate。

## 8. 第一批实际任务与复用

核心seed3401：4个目标×3种预训练×2目标函数＝24个供体训练；每个配相同规则的源声音桥；4种目标初始化/先验×30个目标格子×2目标函数＝240个目标适配。连续语音零样本是冻结供体＋桥的评价，不是另训模型。

目标格子来源：FAU5×2、DTU5×2、Federici5×1、private5×1。这里只沿用现有设计的名义fold数；真实subject/content清单由server绑定。相同供体和相同零样本预测跨目标fold复用，不能重复当独立样本。

包内生成438条**待绑定意向**：24供体训练、24源桥拟合、240目标训练和150零样本评价引用。它们不是438次等成本训练。若已有相同合同执行，复用，不再次排程。后续rich轨道和episode训练按自己的比较卡登记，不无脑乘到核心矩阵。


---

# 04 · 两种监督、两类损失：明确比较对象

## 1. 配对键

跨人正对要求：同cohort、同真实内容、同呈现版本、同任务状态、同被注意流（如有）、同物理刺激时刻，不同参与者。同文件序号不代表同内容，同混合声但注意不同说话人不是无条件正对。时钟通过已验证刺激对齐表映射，不通过EEG峰对齐。

共享监督作用于一个32维投影头；保留编码器的局部token供任务读出和个人适配。32是实施起点，不是必须丢弃所有其他特征的理论要求。无须把HA/CI全部表示强行不可分，也不引入域对抗和全分支独立约束。

## 2. InfoNCE

正对可有多个，采用多正样本log-sum-exp匹配；同一刺激另一个人不是错误负样本。跨人batch中不把同一物理观测自配作正对。允许在NCE候选构造中掩蔽同内容相邻±2秒的模糊负例，这是**NCE任务设计**，保持音频配对与跨人版本暴露量匹配。已有近邻对照可以继续，不称普遍最优。

## 3. 传统核CS

音频配对使用P(U,V)相对于P(U)P(V)的传统核估计；跨人使用合法双听者配对分布的P(U_i,U_j)。在一个预定cohort/任务stratum内构造联合样本后，核矩阵计算其经验边缘乘积。独立项中出现同刺激/同类碰撞是允许的，不能为了造“负例”把它删掉。

\[
A=n^{-2}\sum_{ij}K_{ij}L_{ij},\quad
B=(n^{-2}\sum_{ij}K_{ij})(n^{-2}\sum_{ij}L_{ij}),\quad
C=n^{-3}\sum_i(\sum_jK_{ij})(\sum_jL_{ij}),
\]
\[
\widehat I_{CS}=\log A+\log B-2\log C,\qquad \mathcal L=-\widehat I_{CS}.
\]

核使用两侧各自的高斯距离，带宽由源fit校准/开发固定；保留对角项，除非另行定义一致的去偏估计。本包代码仅实现上述原始经验式。它能反向传播，但有限batch、窄核接近单位阵会出现\(\log n\)的高值，训练值不是泛化证据。需记录核非对角统计与真实/错配评价，不增加r通过线。

不同cohort/task的目标按预定stratum权重求平均，不从pooled量直接命名条件MI；批次时间点相关性通过跨内容/跨参与者抽样和块评价处理，密集采样不增加独立听者数。不能把NCE的逐元素负样本mask直接放进CS的K/L后仍声称同一估计对象。

## 4. 联合预训练与归因

\[
\mathcal L_{joint}=\mathcal L_{audio}+\lambda\mathcal L_{cross-person}.
\]

默认同一损失家族用于两项，\(\lambda\)在供体开发上选；起点1，有限候选0.25/1可调整，不用测试选择。两项的样本数、求平均单位和原始量级都要记录。joint与audio、joint与cross-person分别做配对差；不计算测试儿童逐人最优单方法作为基线。

跨人一致性不是绝对目的：只有当它改善任务泛化、适配或可重复时间结构时才形成贡献。保留no-cross-person、错配训练和任务状态匹配对照，既不强制组别一致，也不让元数据进入预测路径。

## 5. 统一坐标

传统核CS对两侧各自的距离几何优化，不保证跨模态原始坐标可以直接相加或余弦检索。源声音桥及融合的共同预测空间是必需的定义。给两边使用相同目标名称，不等于已经消除了旋转/尺度自由度。

不涉及VCS-QMI、混合参考变分公式或新神经critic。旧FMCA作为已有参照保留，不扩张成第三套全部供体矩阵。


---

# 来源与证据等级

**[B01]** 用户提供《ALN3 待定框架结果简报》（2026-10-16），原样副本：[查看](AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/sources/ALN3_BRIEF_20261016.md)。本包数值和已完成状态来自该简报，不是本次独立复算。正文L标记按对话提供的原文件行号；完整hash见JSON。

重点：L257–L285真全量与同访问结果；L338–L350选择与native/unified；L558–L604互补；L763–L775已完成D面板及旧策略；L855–L976科学分析；L1133–L1167 C3与私有结果。

**[P33]** 已批准 `AUDITORY_ALN3_SERVER_PACKAGE_v3_3_20261016.zip`。本包原样附带公共先验配置、执行文档和损失/声音坐标定义；`inherited/SOURCE_INDEX_v3_3.md`中的来源编号只解释该历史文档，不表示本轮重新访问外网。

**[D34]** 本轮基于简报与上轮评议的新执行决定、模型设计和数学示例。它们是待检验方案，不是已经得到的真实EEG发现。结果解释与旧候选规则发生冲突时，按`AGENTS_APPEND.md`和本包正文执行；源简报仍保留原样。

本轮未刷新GitHub或实时集群。最后对话中的HEAD为a3eb744；上传简报包含更晚的服务器结果。server按现场manifest定位原结果并绑定新执行，不能把最后已知HEAD伪装成最新实测。


---

## 历史公共先验来源编号

# 来源索引与证据层级

本包基于固定仓库版本 `a3eb744411e79e780c83acf8a5d07be135e8241b` 和当前研究者指令。不是新的真实EEG实验报告。报告数值来自仓库，方法解释为作者判断，新配方为待执行设计。

**[S01] latest repository snapshot**

[README.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/README.md)

发布快照，不是实时队列；B_ALIGNED完成，公共先验仍为草稿。

**[S02] B_ALIGNED results**

[docs/auditory_alignment_v3/B_ALIGNED_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/B_ALIGNED_RESULTS.md)

seed3401；真实风险、原生风险和局部参照；旧full标签服从更正01。

**[S03] full-update correction**

[docs/auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md)

旧full对比是更新范围及学习率不同的配方对比。

**[S04] ALN3.2 implementation**

[docs/auditory_alignment_v3/ALN32_IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/ALN32_IMPLEMENTATION_RECEIPT.md)

继承已登记的访问匹配、真正全量更新、残差及seed面板。

**[S05] public auditory prior draft**

[docs/auditory_alignment_v3/ADDENDUM_13_ALN32_PUBLIC_AUDIO_PRIOR_DRAFT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/ADDENDUM_13_ALN32_PUBLIC_AUDIO_PRIOR_DRAFT.md)

本包将其待决项转为执行决定，不重启全部ALN3。

**[S06] audio target implementation**

[auditory_alignment_v2/audio_targets.py](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/auditory_alignment_v2/audio_targets.py)

旧8-frame、按cohort随机投影不是天然共用的声音坐标。

**[S07] personal adaptation**

[docs/auditory_alignment_v3/D_ADAPT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/D_ADAPT_RESULTS.md)

同会话、已知声音支持，不能叫无标签TTA或临床改善。

**[S08] attention integration implementation**

[auditory_alignment_v3/run_attention.py](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/auditory_alignment_v3/run_attention.py)

随机翻转训练、固定正确方向测试；需候选交换一致性重评价。

**[S09] private E results**

[docs/auditory_alignment_v3/PRIVATE_E_INTERIM.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/PRIVATE_E_INTERIM.md)

保留原生GX、局部CS、特定迁移及其对照；不选择测试赢家。

**[S10] private SCI_R1**

[docs/auditory_alignment_v3/SCI_R1_PRIVATE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/SCI_R1_PRIVATE_RESULTS.md)

部分跨时AUC方向反转，未训练表示也存在类似结构；不是两个独立神经源证明。

**[S11] private calibration**

[docs/auditory_alignment_v3/R_PRIVATE_CALIBRATION_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/R_PRIVATE_CALIBRATION_RESULTS.md)

ALN2 checkpoint重评；正斜率仿射不增加排序/AUC，不保证测试NLL必改善。

**[S12] readout diagnostic**

[docs/auditory_alignment_v2/ITEM3A_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v2/ITEM3A_RESULTS.md)

最终投影/投影前空间分量/全通道探针可分离；更多维度不保证更好。

**[S13] Federici identities**

[docs/auditory_alignment_v3/FEDERICI_REAGGREGATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/FEDERICI_REAGGREGATION_RECEIPT.md)

HC37、CI33、HC-v16独立；phantom一实体九会话；HC-v年龄连接来源等级保留。

**[S14] unit record snapshot**

[results/auditory_alignment_v3/unit_records/README.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/results/auditory_alignment_v3/unit_records/README.md)

6452条快照；公开结果字段和资产存在性；不声称已解包全部。

**[S15] publication receipt**

[docs/GITHUB_PUBLICATION_ALN3.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/GITHUB_PUBLICATION_ALN3.md)

个体级公开此前经研究者批准；当前用户再次确认，既定范围无须再问。

**[S16] source-data acquisition receipt**

[docs/auditory_alignment_v3/PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md)

依server已有下载清单核对SparrKULee，不重申请不重下载；本地未读取原始EEG。

**[S17] science R2**

[docs/auditory_alignment_v3/SCI_R2_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/SCI_R2_RESULTS.md)

已有共同时间和显式特征分析复用；新增只针对模型变化与适配。

**[P32] ALN3.2 author package**

继承，不以旧状态覆盖新结果；已发布字段的交付规则由当前授权更新。

**[H01] 下一阶段方向设计_2026-10-11**

历史候选文档。只吸收§E3同刺激跨人监督等已明确采纳部分；不采纳私有关闭、阈值关线、预定组差。

**[H02] 项目进展检查_2026-10-10**

历史候选评议。保留强度/内容/时间组织问题；其“只能线性机理”“私有极限案例”等不是执行纪律。

**[U01] current user instruction**

将上一轮分析转成执行包；既定个体级结果公开已确认，不重复询问。
