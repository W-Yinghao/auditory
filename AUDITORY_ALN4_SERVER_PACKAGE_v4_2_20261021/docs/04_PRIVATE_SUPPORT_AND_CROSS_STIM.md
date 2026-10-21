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
