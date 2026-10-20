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
