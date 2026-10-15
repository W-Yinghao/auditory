# ALN3.2 完整分析与服务器执行文档

**2026-10-14 · 查询锚定接口与听觉群体先验 · 兼容ALN3.1**

# ALN3.2：现在立即做什么

1. **继续已经启动的250个B_ALIGNED。** 不停止、不重复、不暗改旧日程。新结果按ADDENDUM_06先出完整表；加实际更新范围的sidecar解释。
2. **旧B/C失配版本保持定点暂停，local/private/科学分析并行。** 不清空整个hold列表；不能因为D家族含FM policy而把local D也停掉。
3. **补两项完整对照**：与aligned相同1秒EEG访问的local/post-only FM；真正full更新的pretrained/random成对版本。无需等250行显著才开始。
4. **C改成可保留base的补充训练与选择**：共同预测空间、epoch0候选、训练侧跨人开发。B单支不必超过local才允许C。
5. **科学主线现在就推进**：共同时间/声音特征的SCI_R2，局部模型注意与适配，已完成私有E的研究者版汇总；公共听觉预训练并行准备。
6. **新seed只做规定的成对核心面板**，不恢复旧矩阵全量重复，不给测试赢家单独补seed。

本包是兼容增补，未重新生成旧5996行或server6496行。执行许可继承，工程绑定通过后无需再次询问go。下一次更新首先给实际提交/运行/完成、可复用产物及完整比较，不再进行一轮空转规划。


---

# 00 · 即时决定、兼容性与研究纪律

**ALN3.2 / 2026-10-14。是ALN3.1的执行增补，不另起ALN4，不整体重启。**

主问题仍是：怎样用声音监督学习有效、时间结构明确的群体EEG表征，并研究它在HA、CI、正常对照及儿童发育背景中的共享范围、时间组织与适配需求。私有HA验配初期的当前刺激与历史条件证据，是独立问题；不是公共论文末尾的负例。

## 现在执行

| 工作 | 本版决定 |
|---|---|
| 已启动的B_ALIGNED 250行 | 继续其已冻结规格，不重排同一矩阵，不因新包删除或重命名。是一个有用的接口组合比较，但不是纯相位单因素、纯初始化效应或已实现full-update的证明。 |
| 旧B_DENSE/C原接口及其上游依赖重复 | 保持针对具体执行版本的可恢复暂停，不为完成率恢复909行。 |
| 局部A、局部D、与旧FM无依赖的私有E和科学分析 | 继续并行。不得因family级暂停误伤不相关的有效局部比较。 |
| 真正full-update对照、相同EEG访问的局部对照 | 新建执行版本并完整运行；不修改正在跑的B_ALIGNED代码。 |
| C补充性 | 用查询锚定/简单读出、epoch0候选和训练侧跨人选择开展独立完整比较；不以B必须超过local为前提。 |
| 公共听觉预训练和SCI_R2 | 与接口支线并行；不是等基础模型“修好”后的任务。 |
| 多seed | 完成当前主比较的配对稳定性面板；旧失配接口不无差别补seed；新面板不是只给赢家补。 |

## 不以负结果为导向，但完整报告结果

当前独立听者、儿童及不同声音内容不支持由某批模型的弱值推出“没有听觉信息”“发育无效”“达到模型天花板”。更多epoch、seed或作业不产生新的儿童。方法和数据的限制应限定到具体输入、目标、读出、初始化与人群。

这不等于追逐阳性。所有有效弱值、反向差值、校准失败和无收益配置都保留；不删低分儿童、不弱化基线、不按听力组差或年龄显著性挑模型。可以暂缓一个具体实现，把资源投入新的可检验干预；算力取舍不是不存在证明。

科学结果由估计对象、效应大小、稳定性和外部适用性共同判断，不能只计数I>0/I<0的格子。不建立“r提高0.02才准继续”“保留50%才算有信息”等科研准入线。形状、实际参数更新、时间边界、身份隔离是必要正确性检查；检查通过即可开始已授权的完整实验，不再等待逐项go。

## 不变约束

不做ERP主线；不把脑龄误差当正常成熟度；不要求早段正常晚段受损；不混同声音匹配与言语理解。传统核CS、NCE可竞争，FMCA保留既有参照；**不使用VCS-QMI、混合参照变分CS或未发表神经critic**。不新增采集或医生联系作为启动条件。保留原本的10-GPU同时运行授权；不能凭本包追加付费算力。

## 接入权限

继承用户已给服务器的开跑授权。本包本身不执行任何远端写入、提交、取消、上传或删除。server在其授权工作副本合并指令，记录实际HEAD与现场队列。线上出现更新时先看差异，不回退用户的新代码；只为真正阻塞、使用许可或资源越权请求决定。


---

# 01 · 最新证据如何修改上一轮分析

读取基准为`9b9e03e`（13:27 CEST），内容提交`8962b5c`与`6326b9b`。这是发布快照，不是实时集群。P5/P6是探针；B_ALIGNED是已启动的新训练，发布时尚无结果。[S01–S05,S08]

## 证据台账

| 层次 | 最新观察 | 本版判读 |
|---|---|---|
| P5，输入前后线性读出 | FAU：r 0.0207→0.0211/0.0221；DTU：0.0453→0.0440/0.0443。通道顺序核对一致；REVE截断比例很小。 | 在被测试数据与读出下，预处理没有明显破坏原来线性可读的对应。降低“整体输入管线损坏”的优先级，不再重复同一排查。[S02] |
| P6，DTU查询对齐patch | 原始同窗R10 r≈0.034；CBraMod预训练末层0.031、固定网格选中token0.003；REVE为0.034与约0。 | 查询锚定表示值得完整训练。只支持该探针中的线性可读性恢复，不是75–97%的真实神经信息。[S02,S03] |
| P6，随机权重 | REVE对齐随机末层r≈0.033，接近预训练0.034；CBraMod预训练相对随机更好。 | 接口收益和预训练权重收益要分开；不能将P6作为“FM预训练已经成功”。[S02] |
| P6，FAU | R10≈0.005，R06≈0.015；比值不稳定；对齐方向不全一致。 | 只能说本探针精度不足、分母弱，未确定失配；不是正式功效证明，也不是FAU没有可读信息。 |
| B_ALIGNED | 250行，NCE、3401、两主干×五适配×25个fold/content格子；已放行。 | 继续；不能另起一模一样的“修复矩阵”。[S04,S08] |
| 旧C | FM、随机与小容量分支都退化；epoch0未进入候选。 | 补充训练与选择仍需单独解决，不能都归因于FM没有信号。[S10–S12] |
| 私有E | seed3401已完成；研究者版汇总不在公开仓库。 | 不以缺少公开数值推断结果。先向研究者交付脱敏决策表。 |

## 对上一轮分析的四个修改

**收窄输入原因。** 上轮建议的输入前后比较现在已经做过，能复用；“输入准备或主干丢失”不再是同等优先的总解释。线性读出可吸收全局缩放，因而r近似不变不能单独验证0.15z与预训练幅值分布相容；幅值先验是否最适配仍未确定，但不能把它当已确认bug。

**重新打开基础模型局部接口。** 不再主要维护“dense全局query从粗token解出每20ms细节”的方案。查询锚定patch能够把相对时间放进输入表示，值得作为听觉任务接口。与已有效的局部编码器共享的是“以声音锚点组织EEG响应”，不是模型规模。

**不接受排他性定位。** P6的UNALIGNED是固定网格中包含t+0.3s的一个token；不是对B_DENSE全部token和所有读出方法的证明。ALIGNED还改变输入区间、上下文长度、token数、头结构以及逐patch重采样。结论应是“该接口组合提高线性可读性”，而非唯一证明某个相位因素。[S03–S05]

**保留并明确full-update问题。** B_ALIGNED复制旧训练日程，尚未纠正REVE默认50轮只开放顶端9/22块、非block参数未开放的问题。比较仍有价值，但只能称同一旧日程下的接口或初始化/学习率配方效果，不能声称完整主干训练或纯初始化效应。[S05,S06]

## 不再发散成另一篇故障论文

工作故事保持：**刺激锚定、保留局部时空结构的声音–EEG学习，形成可共享的听觉表征；通过独立任务与适配研究HA、CI、对照和儿童中的时间组织。**

基础模型是竞争编码器或先验来源；本轮局部对齐是有效基础；公共声音预训练是直接的听觉先验来源。论文不能预先承诺三者必互补，也不能在某一支线受挫时自动改成能力地图。

候选方法主张需要三类证据：同任务下真实查询预测改善；接口/容量/初始化归因；在听觉人群、注意、儿童任务中形成具体新认识。仅修了patch或增加预训练模型，不足以单独成为主要创新。已有群体声音对比学习是先例[E03]。


---

# 02 · 查询锚定接口：继续现有训练，补齐可解释的比较

## 1. 继承而不改写B_ALIGNED

每个声音查询q，取`[q−0.4s,q+0.6s)`；查询位于5秒段首时，段首之前置零。128Hz下pre=51、post=77，共128点；实际边界为−398.44到+601.56ms，按代码整数样本定义而非理想小数。100Hz下为40+60点。随后重采样到200Hz、单patch、各通道token LayerNorm→展平线性头→L2。与旧B_DENSE的多patch上下文读出不是同一结构。[S04,S05]

继续现有250行、ID、代码hash与recipe。其命名增加描述性字段`effective_recipe=legacy_progressive_prefix`，不能更改旧原始记录或暗中换权重；通过sidecar补实际更新范围。后续新训练用新execution版本。

B_ALIGNED只继承整个片段允许的EEG访问上限：这不等于它与local `[q,q+0.6s)`逐query访问相同。负lag输入是连续声音中的过去EEG，不是无刺激基线。

## 2. 最小而完整的支持匹配

| 对照 | EEG输入与作用 |
|---|---|
| L0 existing_local_post600 | 现有local读取[q,q+0.6)；复用既有结果。 |
| L1 local_aligned1000 | 有效局部架构读取与B_ALIGNED完全相同的1秒窗、同段首mask；评价额外过去EEG与对齐模型的共同影响。 |
| F1 aligned1000 | 已在跑的B_ALIGNED；不再生成同一250行。 |
| F2 aligned_post600_padded | FM单patch的前0.4s固定零，后0.6s用与L0同一真实EEG；不能叫读取1秒真实EEG。先对冻结与PEFT做两主干、全部fold/content。 |
| R1 raw_aligned1000 | 同一1秒原始输入的训练侧正则化线性参照；读出预算与高维正则化单列。 |

历史local的末点可能沿用旧inclusive索引，因此先从真实batcher导出样本offset；不能只因都叫600ms就宣称匹配。若F2的77个post样本与旧local的78个样本不同，新增`local_post_exact_matched_to_F2`作为精确对照，旧L0只作历史桥接；不要暗中裁短已有checkpoint输入。比较L0↔L1时先对齐这一个端点约定，F1↔F2估计FM中额外上下文的价值；F1↔L1和F2↔精确匹配local才更接近访问匹配的方法比较。仍需说明参数量、头、监督与优化不同，不称纯神经信息量。

所有主格完成原有全部参与者外折与内容fold；不根据P6比值先筛队列。段首补零与内部完整窗口分层重评价，同时保留全部query主结果，不为抬分只删边界。真实record边界不能从文件邻接推断；不得读取下一人/下一记录。保留有效样本mask、nominal/actual support与query/candidate哈希。

## 3. 接口归因，不将一个成功点包装成唯一原因

优先复用P5/P6，不重跑相同“查错”流程。需要解释对齐收益时，用固定主干、相同LN+flatten线性头比较query-aligned单patch与固定网格选中patch。若增加单patch/多patch比较，记录总上下文与其mask，不把不同信息访问当同一输入。

`aligned_patch_linear`比旧头更好，也可能来自局部context、头的复杂度、预训练输入分布变化或参数共享。单patch会改变Transformer能使用的上下文：尤其一个时间patch时不能把它等同原多patch时序建模。P6是选择新接口的证据，不是完整机制分离。

## 4. 时间query与EEG贡献分别量化

旧dense输出随q变化，可能来自时间位置编码。本包的`query_content_diagnostic`区分跨query公共模板、固定query下的片段差异；再以同query合法交换EEG检查任务风险。不能用方差比例大或相邻余弦低证明EEG被用到。

该诊断面向旧dense或新的融合分支；B_ALIGNED没有显式query_pos通路，但段首补零和数据采样仍要记录。无须让此诊断数值“达标”才启动其他模块。

## 5. 细时间输出与早晚神经解释

查询步长不是实际EEG时间访问长度；本轮1秒窗覆盖过去和未来响应。它适合总体声音检索或支持条件下的个体适配，不直接给出早窗独有信息。

严格时间科学主线继续用原本的局部受限输入编码器和raw局部参照。0.4秒前窗、上下文FM输出不可回流到同query的早期局部分支。Teacher训练可读丰富输入，但student推理必须只读其声明窗口。


---

# 03 · 训练范围、实际full-update与开发选择

## 1. 当前代码的可复算事实

默认`WARMUP=5, UNFREEZE_EVERY=5, LLRD=0.75`；CBraMod100轮，REVE50轮。旧日程在0-based ep>=5时开放`1+(ep−5)//5`组；先顶层block，最后non-block。B_ALIGNED逐字继承。[S05,S06]

| 模型 | 最后一个epoch开放 | 输入embedding/non-block |
|---|---|---|
| CBraMod 12块、100轮 | 12块全部 | 第66轮才开放，最多35轮 |
| REVE 22块、50轮 | 顶部9块 | 未开放 |

REVE最低层的名义LLRD乘子为0.75^21≈0.00238，non-block为0.75^22≈0.00178；若基础lr=1e−5，后者初始名义值约1.78e−8，再受全局cosine影响。此处是日程算术，不是实际gradient已测量，也不是对所有失败的唯一解释。

此外当前旧配方的random_full基础学习率为3e−4，pretrained_full为1e−5，相差30倍；即使两者开放组相同，也不是只改变初始化。旧比较应称“带不同初始化/学习率的受限更新配方”，不能称matched full update或纯初始化效应。partial/PEFT/frozen依各自定义仍有效。对所有实际单元用运行记录核对覆盖的epoch值；若server覆盖了默认值，以实际值为准。

## 2. 不干扰在跑矩阵的两条完整对照

新增两种有明确语义的训练配方，不改旧B_ALIGNED：

- **full_onestep_v1**：从第1轮更新所有允许的主干参数及读出。random_full与pretrained_full使用同一更新日程、相同训练数据/目标和相同开发选择规则。主要受控初始化比较在相同数值lr格子上逐格配对；不能把各自择优后的不同lr结果称纯初始化效应。分别调优的配方结果另列。
- **warmup_then_all_v1**：头部预热5轮，第6轮开放全部允许参数，剩余轮数完整更新。random与pretrained在同一对照中使用相同日程。它与逐层缓慢开放是不同实验。

受控主比较默认LLRD=1，避免把极小底层lr与初始化贡献混在一起；既有LLRD=0.75配方保留为适配敏感性，不宣称其必然错误。epoch起点沿用100/50，可按训练/开发曲线登记续训，不用test结果决定。

每个配方完成两主干、两个初始化、三个公开队列的原有全部fold/content。不是先看一个短probe决定是否让另一模型训练。主干冻结版不“解冻”；PEFT仅更新允许的LoRA/adapter，不因“all”把原权重全打开。

## 3. 实际更新账本

训练结束输出每组：首次允许更新轮、允许更新轮数、实际optimizer步数、含gradient的步数、起止权重变化范数（相对尺度）、lr起止/积分摘要。只记录`requires_grad=True`不等于训练过；state加载和非block漏载分别记录。

`src/aln32_reference/schedules.py`仅提供计划与算术参考。server需绑定真实命名组、优化器和resume；不覆盖现有runner。正确性测试检查语义，不设置任务分数门槛。

## 4. 开发集要对应最终的跨人使用

旧checkpoint按训练参与者的留出内容选择`own−mismatched`，并不能保证跨人泛化。[S11] 旧结果照原协议保留。

对新增主方法，使用outer-train内部固定的开发参与者与开发内容：两种泛化轴都报告；选择主量为同一真实query风险或相应任务概率风险，rank作为并列评价，不再只靠错配差择模。人数较少时做固定的inner group cross-fitting，而不是反复改开发人群寻找好结果。

读出、校准、学习率、老师和阶段模型选择全部在外层训练侧。测试参与者的支持块只在明确的个人适配任务允许；不能用于重新选择全局方法。outer-test历史已看过的事实披露，新登记不使这些数据重新变盲。

保持一项原选择规则对照，以分辨结构改变与择模规则改变。B_ALIGNED正在跑的选择规则不追改；新规则用新版本并与之并列。


---

# 04 · 重新检验补充性，而不是强迫融合成立

当前C的全部成人变体、甚至小容量分支都比local差；共同点包括dense上下文头、同参与者内容验证、epoch0未入候选。[S10–S13] 这不能证明所有FM无互补信息，也不能被“以后一定修好”掩盖。

## 首先将问题分成三项

1. 新分支在自己的合法输入上提供什么可读结构？
2. 在已有效的local预测之外，是否能降低同一任务的真实query风险？
3. 即使有潜在增量，训练/选择是否稳定利用了它？

C不需要B单独超过local才能有价值；弱单支也可能互补。反之B变强也不保证C增加价值。

## 第一组：低复杂度、共同预测空间的完整比较

冻结local与候选特征提取器，将它们映射到同一、训练侧定义的声音特征坐标。主对照：local-only；local特征再拟合的同容量修正；加aligned预训练特征；加相同结构随机特征；加小型局部/上下文特征。保留简单拼接。按相同fold/目标/查询/实际EEG访问和概率校准比较。

先用正则化线性/低秩融合，仍完成所有外fold而非少数漂亮被试。新分支使用1秒历史窗时，local参照也有访问匹配版本；否则标为上下文辅助，不作纯预训练归因。

为减少在训练内残差过小而测试误差大的失配，残差拟合使用outer-train中的跨人OOF局部预测或与base训练不重叠的stack-fit参与者。固定组划分，记录base是否见过这些人。不能拿outer-test的局部预测误差训练补充分支。

## 第二组：训练型残差

候选式为`Ahat = Ahat_local + r(H_local,H_aligned)`，或者私有任务`logit = logit_local + r(...)`。不是在两个任意旋转latent中直接相加后称声学残差。若保留固定latent路线，应记录两分支的音频头/标准化对象；但对传统核CS或FMCA，同一固定声音目标本身并不足以确定EEG侧旋转坐标。需训练侧的声音预测桥、配对旋转或显式预测监督后再相加；独立正交旋转可保持高斯核依赖目标不变而改变向量加法。因此主补充比较使用显式声音预测空间，并单列原生与共同读出。

- 零输出初始化后，保存epoch0及其训练侧开发评分，让它进入候选。
- 第一阶段冻结local，只训练补充头；联合微调是另一个配方。
- 选模用预先固定的训练侧跨人开发；可在候选中选择epoch0，但不能按test表现事后退回base。
- epoch0回退表示“不采用此项修正”，不是互补阳性或医学结论；零初始化只保证初始输出一致，不保证训练后测试不退化。
- 保存真实EEG风险`R(local)−R(combined)`，不是仅比较各自G。加错配EEG风险不等于更好的预测。

## 保留能够区分原因的对照

同query下正确上下文、合法交换上下文、query位置only、随机权重特征。随机/位置分支也改善时，不自动归为听觉预训练贡献。小容量分支退化时，优先检验融合训练与选择，不用它证明FM特有缺陷。

同时需要预训练对随机、普通容量参照，但不以“所有I>0才允许继续”作硬门槛。结果分别回答方法价值与归因，尚未区分归因时如实说明。

## Teacher与D策略

旧B/C teacher和D policy不能因为新包出现就自动升级。已训练的原policy结果标清来源；新aligned policy从对应fold的候选在训练侧选择，必要时local-only也是合法候选。获得一个合法checkpoint即可启动其所需下游，不等所有基础模型配置或全部seed完成。

只对新依赖重生成teacher-target；原始预训练checkpoint、输入缓存、有效local可复用。禁止跨fold加载“碰巧更好”的base。


---

# 05 · 主方法建设：声音监督的群体先验，不被FM接口牵住

## 主张仍是待验证的

目标不是训练另一个“通用脑基础模型”，而是学习能跨听者使用的声音响应表示。有效的lag-local是主起点；query-aligned FM是竞争结构/先验，可平行发展。公共大模型不是本文必须成功的部件。

## 直接听觉预训练的比较

| 训练策略 | 研究问题 |
|---|---|
| target_from_scratch | 目标队列现有local完整基线 |
| public_audio_pair_pretrain → target_adapt | 更多真实声音配对能否提供可迁移先验 |
| same_stimulus_cross_person → target_adapt | 同刺激跨人的共享监督能否帮助群体对应 |
| joint_audio_and_cross_person → target_adapt | 两种监督是否互补，而非重复要求所有人一致 |

每个目标队列仍用其全部规定外层fold；分别报告零样本、无标签输入适配、带声音标签适配。不能将目标侧拟合读出叫严格zero-shot。NCE与传统核CS保持一组主要方法对照，不将所有超参数全交叉。

## 数据接入：先一套足够相关的公共语音资源

优先核实SparrKULee原始发布/合法镜像。原论文85名、168h[E01]，2026 NEMAR镜像列80名[E02]；这些数字不是server已经获得的样本。下载日志明确参与者数、唯一声音内容、记录小时、许可、实际获取项和未获取项；同一个故事重复多人不算多倍的声音内容。EEG与刺激许可分别核实。使用已授权的`/projects/EEG-foundation-model`，先看可用空间和断点续传，不占满训练盘。

下载与现有训练并行。无需等所有公开库齐全再训练；可用的完整登记子集先按版本运行后再增加数据，不能根据成绩决定保留哪些记录。普通话资源是后续独立接入，不混入本批主矩阵，也不把朗读/MEG算成听觉EEG样本。

## 跨人正样本

键由真实刺激内容及物理时间锚点、呈现版本和任务状态决定，排除同人自配对。竞争语音需要同一被注意流/任务条件；同混合声但不同注意目标不是无条件正对。连续片段重复、同类别碰撞按各损失的分布定义处理，不能为了造负样本随意删除同类。

跨人约束只施加于明确的共享分量；保留任务头/个人修正，不要求HA、CI和对照的全部EEG不可区分。先做简单共享头与有限空间输入适配，不默认加入域对抗、互信息惩罚、全分支独立性或复杂PID训练。

## 通道与声音坐标

声音目标先选时间支持清楚的包络/局部声学特征；跨队列共用同一声音表示和训练源定义的投影。各队列独立随机半正交映射不能直接互测。

输入用明确通道身份或电极位置；系统映射与共享时序部分分开。迁移保存loaded/new/missing键和参数数量；允许新输入层，不允许漏载大部分网络仍写迁移成功。刺激哈希/片段重叠跨所有source/target清查，只排真正重叠，不因组差剔除。

## 评价不只是一张跨被试排行榜

同队列任务泛化、跨队列适配、同刺激跨人收益、注意选择，以及私有儿童的当前声音/历史条件任务共同决定方法用途。若收益只来自更多数据或容量，就报告该范围；不因想突出算法而压低强基线。方法模型选择不使用听力组差、年龄斜率或临床显著性。

既有群体声音对比学习[E03]已提供方法先例。本项目需贡献时间锚定/共享与适配的具体有效设计，以及在听觉人群和儿童中的新证据，不能靠加几个公开库宣布首次。


---

# 06 · 科学分析继续并行：内容、时间、共享与适配

SCI_R1已完成，B/C新结果不替换它。当前新B_ALIGNED也不是早晚分析的前置条件。

## 论文问题与可交付证据

| 科学问题 | 使用的读出/比较 | 不预定的答案 |
|---|---|---|
| 什么声音证据可读？ | 固定方法下局部声学、包络/起始、谱变化；上下文化特征作扩展 | 不预定“只有声学”或“深层就是语言” |
| 证据如何随时间组织？ | 共同绝对lag下局部预测、TG、独立早/晚/联合风险与冻结读出重拟合 | 不预定成人晚儿童早，或TRF峰必须重合 |
| 哪些能群体共享？ | 共同模型→空间/时间映射适配，支持块与query分离 | 不预定HI强即更好、CI低即神经缺陷 |
| 儿童经验与发育背景？ | 任务能力、时间组织与日历年龄/既定HA阶段关联 | 不把未显著当不存在，不将年龄、验配年龄、时长当独立三轴 |

## 共同时间面板

保留原生窗口，并新增一个预先统一的绝对lag网格和等宽局部支持面板。原成人早[0,80)、晚[90,300)，Federici早[0,150)、晚[150,600)不能直接比较早晚标签。私有窗也不同，报告实际毫秒与采样点。

采用共同包络目标及可比较频带作为桥接；Federici仅有2–8Hz缓存时，不补造未保存频率。成人可以新增同频带敏感性，但原宽带结果保留。将窗口、目标、频带三个改变分别登记，不声称已经单独识别发育。

负lag可预测性可能来自声音自相关、滤波或慢状态，不一律叫训练泄漏。以因果/零相位敏感性、声音历史参照和合法移位分别检验。不做“正lag减负lag=纯神经信息”。

## 显式声音特征与前向参照

完成已计划但未完成的S2：[包络/起始]→[谱与谱变化]→[实际可核实的F0/voicing等]。增量比较同一预测目标、相同query/风险和训练侧容量选择；Ac/Lz分别训练后的gain不能相减称语言独有信息。

前向TRF是补充对照，不是唯一能研究表征动态的方法；不设峰差30ms的通过线，也不把浅层响应幅度和解码准确率当同一量。TG固定训练映射，校准是否跨时间重做需区分，避免将模型再适配掩盖成完全零适配泛化。

## 人群与功能

FAU HA/CI/TH、DTU HI/NH在各自协议内比较。模型共同、query相同；先报任务与时间结构，另报适配前后。空间适配与时间组合的低自由度变化可解释为读出匹配，不直接称治疗机制。

不同队列的HSM、SRT、理解、努力、SSQ、SIR等构念不因z化而相同。固定表示后用各自低维功能头，比较临床/人口背景、背景+整体对齐、再加时间/选择指标。有效负值保留，但不因多个小样本终点未显著转向“无临床信息”结论。

CI来源敏感性独立保留；phantom仅一个实体多会话。去伪迹目标是减少已知注入污染的影响并保留参考任务，不按CI−TH差距是否缩小选方法。半合成参考EEG不是已知纯神经真值。

## Federici实体与内容

HC、CI、HC-v按独立真实身份；HC-v年龄的推定连接仍标明来源等级，不用性别年龄相同确认身份。Artifact不进入人类bootstrap。共同内容支持、全数据结果和年龄/内容关联并列；不能把不同年龄听不同故事后的趋势单独归因年龄。

## 五张科学图（不是保证阳性）

1. 刺激锚定、局部响应与群体学习的模型及任务关系；
2. 方法在同任务/同访问下的真实风险与检索改善；
3. 同一声音参照下的时间结构及窗口互补；
4. HA/CI/对照的结构与适配变化；
5. 私有儿童当前声音、历史条件、迁移和验配阶段。

修复日志和大矩阵放方法补充，不让它们替代这些科学问题。每一图说明已完成、尚未知和依赖，不自动变成负结果地图。


---

# 07 · 私有儿童：独立推进，不受公开FM支线暂停牵连

## 先交付已经完成的研究者版结果

公开仓库未包含新私有E结果，不代表没有结果。server通过研究者已有私有交付渠道提供脱敏汇总，而非默认push到公开仓库：GX/local/FM、原生与共同probe、AUC、自然NLL/Brier、历史条件增量、校准变化、source donor、实际参与者与终点n、年龄/HA阶段的规定分析。

本包不推测这些结果方向。不再用ALN2的0.50–0.55范围代替新一轮结果。

## 主问题

公共听觉先验是否帮助读取儿童HA验配初期的当前声音响应，改善发生在整体可读性、某些时间范围、还是个人映射？在合法过去历史已经提供的预测之外，EEG是否仍有可用增量？

只有标准/偏差时使用类别核/原型或任务头，明确是刺激身份读出，不伪造连续音频/音素/语言监督。二类别限制对确定性声学属性的独立归因，但不等于AUC必须接近0.5。

## 继续的完整比较

GX原生及统一probe；有效局部模型；通用先验；公共听觉先验迁移；查询/刺激锚定表示；局部预测+低复杂度预训练补充。已有兼容结果直接复用。新公共donor只迁移可用EEG参数，私有重新训练真实类别头。

新公开B_ALIGNED读取负0.4到正0.6秒，不直接套私有epoch。私有真实可访问的前窗由数据决定；若仅[-0.2,+0.6]可用，不能生成[-0.4,-0.2]EEG，使用明确zero-mask或改窗口并登记。任务比较尽量同[0,0.6]，历史上下文扩展另列。

## 校准与历史

正斜率仿射校准只改概率，不增加AUC。读出/校准需训练侧隔离或cross-fit，避免把小样本高维拟合乐观写成任务收益。基率与q_hist从训练儿童估计；加入EEG后用相同自然query风险比较。对历史已确定类别的状态不要求存在剩余信息；共同支持子集与全数据同时报告。

试次历史严格结束于当前刺激之前。NH佩戴时长不适用，不填0；月龄与验配年龄/使用时长之间的代数关系仍存在。既有0–2月等分箱不按结果调整；连续年龄/时长低自由度分析同时保留。不在每个小组单独训练大模型再比较“最佳分数”。

## 迁移、教师和适配

有效local或generic教师按训练侧预测选择，不默认full微调最佳。老师预测与学生在相同类别/真实候选上匹配；不强迫任意latent坐标一致。老师只能在训练期访问丰富响应；学生的query输入不扩大。每个outerfold使用合法source/teacher，不从别fold借测试见过的教师。

个人support与query分开；若同访问中可以用已知刺激监督，称个人有监督适配，不叫无标签TTA。真实多访问才报告跨访问，不从分半推断长期监测能力。

阶段、年龄和功能分析跟随固定方法并行，不设置任务成绩门槛；解释要说明弱测量带来的精度限制。没有新医生资料也可完成当前任务；不以新采集为本包执行前提。


---

# 08 · 排程、多seed与复用

## 当前状态只能按server现场读取

HEAD发布快照为ALN3约82%完成；250个B_ALIGNED已放行，尚无其结果；旧909重复和约200 D策略行暂停。[S01,S08] 这些不是新包生成时的实时数字。先读取running/pending/completed及checkpoint依赖，不请求它们“回到”发布状态。

## 条件暂停，避免整个family误伤

当前`families_on_hold`包含D_ADAPT/D_ATTENTION等较宽family名。改为按具体execution/architecture/policy/source-version匹配；旧FM/dense/complement依赖继续暂停，合法local分支不因同family名被拦。**不得简单将暂停文件清空为[]来恢复全部作业。**

`queue_advice.py`是离线建议器，不调用Slurm、不改队列，遇到依赖不明输出`needs_binding`。实际解除暂停由server在原授权范围对确定行执行。

## 执行波次：是依赖顺序，不是成绩门槛

- **立即并行**：现有B_ALIGNED；A/local-D/private有效剩余单元；私有脱敏汇总；已有onestep/LR结果提取；SCI_R2目标准备；公共数据许可与下载。
- **相同访问与实际更新对照**：工程绑定后整组完成，不等aligned必须显著。真实full-update单元单独命名。
- **补充性与下游**：在合法同fold base/checkpoint就绪后启动，不等全部模型/全部seed。C独立处理epoch0和跨人验证；D新policy保留local候选。
- **公共听觉预训练/迁移**：数据合同完成即可按版本训练，不等待FM支线。资源扩展不是先把所有库搬到盘上。

优先输出完整的成对比较结果，而不是等所有逻辑行结束。运行中发现纯技术错误可暂停其依赖，范围明确；新假设的弱结果不等于整个方向无效。

## seed政策

1. 原250行B_ALIGNED按3401完整运行，已产生什么都保留。
2. 新注册少量明确的成对稳定性面板：query-aligned与访问匹配local；CBraMod/REVE真正full更新下pretrained与random；一组冻结/PEFT适配；C local、预训练、随机、普通容量；私有GX/local/当前迁移。主对照一起用3407和3413，不只重复获胜方。
3. 选择面板来自研究问题与规定的角色，不由B_ALIGNED测试排名产生。新版本已在看过旧结果之后设计，明确是建设性后续而非原始盲验证。
4. 固定一套主要probe/calibration抽样帮助隔离训练seed变化，另外独立报告读出抽样敏感性。上游base/teacher不换seed的结果称固定上游条件稳定性；关键全链比较使用配对同seed上游。
5. 旧粗接口全矩阵不补重复；已完成的原面板保存，不当新的数据复现。身份bootstrap区间条件于拟合模型，多个seed不增加n。

## 资源与运行ID

继承10-GPU上限。query-aligned重复推理比固定grid成本不同，按实际吞吐、显存和合法缓存安排；不承诺一天跑完。生成comparison inventory而非盲目扩展所有交叉；`configs`列出必须回答的问题和主变体，server复用已有相同hash。所有外fold和内容fold覆盖，不把完整实验误解成每个超参数都乘所有新轴。

旧目录和包只读；新增版本文件/sidecar/注册表，不编辑正在运行的hash代码。原结果ID保留，新输入、优化或择模用新execution hash及parent lineage；不得把新结果覆盖到原B_ALIGNED。

源checkpoint可位于已有offload符号链接；引用真实hash并保护所需依赖，不硬编码发布时的私有路径。本包不产生实际Slurm计划/取消动作。


---

# 09 · Server接入、交付与本地参考工具

## 最短接入路径

先读`START_NOW.md`与`SERVER_START_PROMPT.md`，合并`AGENTS_APPEND.md`到规则最前，保留历史。记录实际HEAD，确认ADDENDUM_06现有250行和它们的运行状态。读`configs/reuse_actions.yaml`及比较清单，复用已有结果，绑定缺失的具体fold/目标/seed/checkpoint。

本包不是一个已经完成真实数据集成的新runner；不覆盖`auditory_alignment_v3`。建议在该目录新增有版本号的schedule/control/analysis文件，沿用现有batcher、身份清单、目标和原生读出。真正变化的训练用独立注册，不改已经冻结版本。

## 必交结果

| 文件（建议名） | 内容 |
|---|---|
| ALN32_IMPLEMENTATION_RECEIPT.md | 当前代码、复用与新执行、实际输入支持、暂停范围和已提交作业。不要写再次等待go。 |
| ALIGNED_INTERFACE_RESULTS.md | 250行B_ALIGNED原结果、访问匹配local/post-only、实际更新范围注释；原生与共同读出分开。 |
| EFFECTIVE_UPDATE_REPORT.json/md | 每层允许和实际更新、one-step/真实全量对照；名称与事实对应。 |
| COMPLEMENT_REVISED_RESULTS.md | epoch0/训练选择、同query真实风险差、正确与错配context、随机/容量归因。 |
| HEARING_SHARED_TIME_RESULTS.md | SCI_R2共同时间、声音特征、HA/CI/对照及适配后的结构。 |
| PRIVATE_RESEARCHER_SUMMARY.md | 私下交付儿童任务、历史、迁移、年龄/阶段及可用n；不默认公开。 |
| PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md | 已取得/缺失数据和许可、实际规模、方法训练与目标迁移。 |

每轮先说明新建立/改善的能力，再给全部主对照，再说明未支持的配置和竞争解释。解释不能只写“框架由用户决定”；本包科学问题已固定，但不固定答案。

## 核对范围

短工程测试：真实token轴和通道对应、声明窗外扰动不影响strict-local输出、采样边界、非finite、优化器实际更新、epoch0等价、fit/dev/test来源和依赖配对。无分数阈值；测试通过不是神经效度验证。

P5/P6已经做过的检查优先复用，不重复制造大量CPU基准。按当前方法真正新增的接口补检查即可。运行正确性和数据许可之外，不把额外审计当全文实验的前置条件。

## 包内代码

`src/aln32_reference/schedules.py`：旧日程覆盖与清楚的full-update参考；不自动替换生产优化器。
`geometry.py`：带record/segment边界的查询窗与mask，供server对照真实切片；不包含数据loader。
`diagnostics.py`：公共query模板与片段变化分解、风险差、phase-readability合成例子；不估计真实神经MI。
`queue_policy.py`和CLI：逐行只读排程建议，不读取成绩、不调用Slurm。
`tests/`：合成、边界与数值测试，不能作为真实EEG成功证据。

测试命令：
```bash
PYTHONPATH=src python -m pytest -q tests
PYTHONPATH=src python scripts/run_numeric_checks.py --out reports/numeric_checks.json
python scripts/validate_package.py
```

保存私有预测/checkpoint时沿用server权限；公开仅聚合与获准的研究材料。不得因“新包已生成”推断已经push或提交了任何作业。


---

# 10 · 本地独立核对：范围与结果

本节只含源码日程算术、人工构造数据和张量边界；没有真实EEG、backbone权重、远程训练或临床验证。

## 日程核对

复算fm_aligned/fm_dense的默认开放组：REVE 50轮结束时开放9/22个block，non-block未开放；CBraMod100轮结束时开放全部block，non-block第66轮开放，共35轮。真正的生产更新还需server用梯度/optimizer/权重差证实，不能只看requires_grad。

## 物理窗口

128Hz的0.4/0.6秒按round变成51/77点；实际半开边界为[-398.4375,+601.5625)ms。参考实现测试了段首mask、record边界、窗外扰动、post-only和真实样本集合相等；它不代替server的data loader核对。

## 相位坐标反例

人工构造Y为标准高斯、P为独立±1变量、H=P·Y+小噪声。训练和测试各16000行。只从H线性读取Y的测试r=-0.009880；从对齐特征H·P读取为0.998765；允许P与H交互为0.998765。

这个例子说明：相位坐标不一致可以让线性读出接近零，而显式相位条件化恢复可读性；不意味着信息在物理上消失。它不是对P6真实成因的证明，也不保证B_ALIGNED训练有效。

## query时间模板

构造所有片段共享的sin/cos时间轨迹，片段内输出显著变化，但固定query下的片段间方差为0。故P4类时间变化检测不能单独证明模型使用正确EEG。参考诊断不设置百分比通过线。

## 训练与方法边界

校验通过只说明附带工具在其覆盖条件下正确。真正模型新版本需绑定实际层与张量，保持相同目标/候选/外层身份，不从合成核对推断听觉成效。


---

# 来源索引与证据等级

核查HEAD：`9b9e03eb229b93c357f6d222a93ba354deb85b06`。本包中的事实、推论、合成验证和新实验分别标注；不声称读取服务器私有结果。

- **S01** [README.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/README.md)：发布时进度；B_ALIGNED已启动、尚无结果；不是实时队列。
- **S02** [docs/auditory_alignment_v3/BC_PROBE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_PROBE_RESULTS.md)：P5输入路径与P6对齐token探针；主要是训练参与者内的留出内容，不是完整泛化结果。
- **S03** [docs/auditory_alignment_v3/BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md)：P6定义；aligned单patch与固定网格选中token的区别；记录原先启发式判读而不继承绩效门槛。
- **S04** [docs/auditory_alignment_v3/ADDENDUM_06_B_ALIGNED.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/ADDENDUM_06_B_ALIGNED.md)：已冻结的250行、输入[-0.4,+0.6)秒、线性读出、继承训练配方。
- **S05** [auditory_alignment_v3/fm_aligned.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_aligned.py)：aligned_windows、AlignedFM、fit_aligned、实际解冻与评价路径。
- **S06** [auditory_alignment_v3/fm_dense.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_dense.py)：epoch、warm-up、逐步解冻、LLRD与学习率常量。
- **S07** [auditory_alignment_v2/foundation_adapter.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v2/foundation_adapter.py)：backbone参数分组、CBraMod 12块、REVE 22块及patch输入；之前已核查实现。
- **S08** [docs/auditory_alignment_v3/IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/IMPLEMENTATION_RECEIPT.md)：暂停范围与B_ALIGNED放行回执；旧hash不改。
- **S09** [docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md)：上一批1000个B单元的seed3401完整比较；不是B_ALIGNED结果。
- **S10** [docs/auditory_alignment_v3/C_COMPLEMENT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/C_COMPLEMENT_RESULTS.md)：650个C/容量对照的seed3401比较。
- **S11** [docs/auditory_alignment_v3/BC_INTERIM_QC_NOTES.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_INTERIM_QC_NOTES.md)：C缺epoch0、内容验证未识别跨人退化、dense时间路径等已见问题。
- **S12** [auditory_alignment_v3/fm_complement.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_complement.py)：旧残差分支与选择；全部分支共用dense上下文读出，不归因单一FM。
- **S13** [auditory_alignment_v3/aln3_reference/readouts.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/aln3_reference/readouts.py)：query显式时间路径与通道投影；不随q恒定不等于依赖正确EEG。
- **S14** [docs/auditory_alignment_v3/SCI_R1_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_R1_RESULTS.md)：已完成SCI_R1；time/group结果及限制。
- **S15** [docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md)：原有seed角色与账本继承，不全量再乘三。
- **S16** [docs/auditory_alignment_v3/SCI_FEATURE_INCREMENT.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_FEATURE_INCREMENT.md)：S2显式声音特征增量尚未完成。
- **S17** [docs/auditory_alignment_v3/SCI_R1_PREREG.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_R1_PREREG.md)：各队列时间支持、身份、probe/calibration范围。

## 外部原始来源

- **E01** [SparrKULee原始论文](https://www.mdpi.com/2306-5729/9/8/94)：85名参与者、168小时EEG。
- **E02** [NEMAR发布页](https://nemar.org/dataset/nm000238)：镜像列出80名，另5名受限；不能将85写成已获取样本数。
- **E03** [Défossez et al., 2023](https://www.nature.com/articles/s42256-023-00714-5)：群体共享声音解码与预训练声音表示的先例。

## 旧包

ALN3.1上传附件为兼容基准。只继承没有被本包明确更正的工作；原始zip不改写。文件hash见`reports/INPUT_PROVENANCE.json`。

这两份2026-10-10/11的候选分析是历史资源，不是当前指令：其中“私有oddball停止所有新模型”“任何gain≤log2K”“CI差距缩小才算去伪迹成功”“自动改写边界稿”不采纳。
