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

