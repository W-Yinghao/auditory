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
