# 第一轮：两种直接干预，一套嵌套读出

版本：ALN3.6 / R1。主seed3401。所有新增科学比较登记为 `prospective_protocol_after_2026_10_20_result_informed_design`：利用既有结果形成的新方案，不冒称从未看过任何外层数据的预注册确认性发现。

## A. FAU：训练排除整个目标听觉组

将 CI、HA、TH 依次作为完全不参与本研究模型开发的目标组。其他组为source，包括合法TH dev；leave-TH时这些dev也必须排除。两种固定工具为既有有效local L1和query-anchored true-full CBpre。主训练用InfoNCE，不新增backbone×loss扫描；传统CS和REVE的现有竞争结果保留在补充。

沿用每种有效工具的实际父配方：local200 epochs、lr1e-3；CB100 epochs、backbone3e-4/head1e-3，full-onestep；详细绑定以04及真实parent resolved_config为准。不能把local缩到100后再称公平竞争，也不继承2×预算。checkpoint改为固定合法source ES的实际query NLL；适当温度／读出参数从source-fit内部独立校准，ES仅选择checkpoint。不是新的selector比较。

### 去重和范围

整个目标组排除后，source集合不随该组原五个人折变化。每seed仅2工具×3组×2content folds=12次唯一训练。目标组人仍按原5折输出60个eval cell，用于与历史身份/内容索引对齐；不是60次独立训练。每个目标人的两个内容划分先在人内平均。

训练键包含encoder、held-out group、content fold、seed、source身份／内容哈希、预处理／归一化、配置和代码哈希。所有目标组人不参与source encoder、数据尺度、history、时间probe、组合、checkpoint或正则选择。通用CB固定预训练权重可用；不接曾见FAU目标组的本项目听觉donor。CB原始预训练是否含同类听觉状态不可由本设计排除。

**主要检验是目标组内 `G0=R(H0)-R(E0)`。** 它不需要与不同source人数的pooled风险相减。旧pooled20个cell作为描述和既有个人读出背景；不得由pooled−excluded差宣称组特异性或组间共享程度，更不得宣称等效。三个组源人数/组成不同，原始风险排名不承担神经解释。

### 新FAU输入尺度

旧loader按每个人所有role一起做_std z；不能把它称source-fit normalization。新whole-group版本从既有stageB预处理EEG读取，按合法source组fit内容估计固定channel尺度，冻结应用到sourceES及目标人support/query。所有五状态共用它。记录channel顺序、均值/尺度和合法训练行哈希。既有离线滤波/ICA仍为继承预处理，不声称从原始电压开始的因果时间隔离。DTU/旧pooled/private保留既有权重的预处理范围并如实说明，不能靠改名变成新严格全链处理。

## B. 公共数据：直接区分共享声音证据、个人标定、个人时间读出

### 同一个科学目标

主声音目标固定为当前包络，history控制固定20/100/200/500ms的过去包络。目标按**唯一source-fit音频内容**估计均值/尺度，每content fold在两个工具/held-out-group之间使用同一合法音频坐标。不是按目标组人的EEG或query重新标准化，也不是将候选真实当前声音作为EEG模型输入。

主风险为source标准化当前包络的MSE；历史模型与EEG模型预测同一目标。报告 `H0→E0` 等差值及历史条件残差Pearson r作为读者熟悉的辅助端点。MSE、r、原检索bits不能相加或视为同一个信息量。历史控制只用于科学条件预测，不是宣称实际声音检索在部署时得到了隐藏query答案。

### 时间证据bank和等访问

固定既有center `[-200,0,200,400,600]` ms，每个encoder窗 `[c-400,c+600)` ms。每个窗的32维表征经source-only probe成为一个标量声音证据，K=5。用source上的OOF读出证据确定共享组合；原encoder可见过这些source人，因此OOF只保证读出层，不称whole-pipeline inner-person验证。

**E0、EC、ET全部看到同一完整五窗scorebank**。E0使用固定source组合；EC只改变组合的整体正尺度；ET额外改变相对时间权重。不允许E0只看单窗却让ET看五窗后把额外访问归因个人化。与旧单窗0ms结果的比较仅作为背景。

固定每个合法5秒段恰好8个anchor：0.8、1.2、1.6、2.0、2.4、2.8、3.2、3.6秒，实际索引为round(fs×秒)。source、support和query共用网格；输出并校验物理anchor唯一性，不重复导出加权，不改hop或用8个anchor声称8个独立听者。公共数值参考的总损失每anchor等权，λ=1对应这个固定密度；私有每trial等权。任何缺少完整8个合法anchor的段由几何规则整体标为不可用并报告，不能按表现保留部分点。

五窗联合访问约[-600,1200)ms。读出和支持/query选择的guard必须覆盖这个实际联合访问，不只沿用单窗guard。窗口高度重叠，权重不能当作神经潜伏期或反应时。

### 个人支持和query

- 目标人的source-fit内容提供support。选择固定自然U30：按该人可用fit段的物理时间顺序取前ceil(30%)的完整合法5s段；不看标签、group效果或query分数。记录实际秒数、段数、anchor数；不把它叫30%全部记录。候选source-fit与test内容独立。
- Query为该人的全部原source-test内容，所有状态同query。同人source-ES内容不作为新增个人择模集，也不能隐含用于调lambda。
- 支持与query必须验证原content group/part与物理样本访问范围；仅不同uid但重叠EEG不够。
- FAU整组模型中每个目标人都没有参与source学习。DTU及FAU pooled既有模型只使用其原outer-held-person，不能把别人的source人误作新目标人。

### 公共当前对应性控制 M0

仅增加一个不训练的固定E0评估控制：在每个目标人的Q内，按真实recording和segment起点排序，将完整5秒段的8个anchor×5窗scorebank循环错移一段；保持8个anchor相对位置、同一partner的五窗关系以及原query history/y不动。使用固定E0参数，不重训、不按损失选partner。至少2段时得到`R(M0)-R(E0)`；不足2段标不可估计，保留该人的所有真实主结果。该控制继承旧segment-roll思路，但使用本轮完整bank和稳定物理ID，不对anchor单独乱序。它是对应性敏感性，不能叫history条件随机化或纯神经因果控制。

公共H0固定为截距加四个过去包络lag的线性history模型；个人HP/EC/ET恰使用[1,同四个source标准化lag]五列，不把HP弱化为只有截距。主目标坐标在全合法source-fit音频内容上固定；每个source读出OOF行保留其对应H0 offset与窗口scores。a0用这些OOF行拟合。最后H0/window probes按全部合法source重拟合，但应用冻结的OOF score尺度和a0，不另换一个scaler、不在目标Q重标定。输出单位和坐标映射必须完全记录。

## C. 私有儿童：当前声音与历史的辨别

固定 matched AP/APwrong V2 的NCE、seed3401、相同初始化/曝光lineage，5个outer人折共10个冻结bundle。新AP需要新提取分段特征；旧AP−XM与新APwrong不可混为严格消融。兼容的S既有特征可做5个补充参照，不阻塞核心，也不扩J*/XM/loss矩阵。

保持64个儿童（HA55/NH9）；不要因信号、阶段、AUC或twin覆盖筛掉儿童。支持沿用自然U30完整物理block，query是后续独立blocks，保留边界guard；实际试次比例由block决定，旧规则平均约36.65%，不能标作精确30% trial。没有未见声音身份的声学内容轴，只能声称新儿童和独立block泛化。

source-only history基线沿用6档since-last-deviant的q0定义，儿童当前标签不进入history；实际历史标签来自实验已知的过去刺激序列。三个时间输入是编码前0–200/200–400/400–600ms masks。64Hz实际访问见03，且仍受继承离线预处理限制。三窗source-only logits形成K=3时间证据bank。

HP、EC、ET有相同的6档个人history收缩修正；EC添加固定共享EEG方向的整体正尺度；ET最多再增加两个source条件残差时间方向自由度，实际数量受source残差rank约束。使用自然support，不人为平衡类别，不做C10/H10。

### Strict twin

同儿童、同history、异block、非自身的partner由固定seed和合法索引决定，不接收当前y、预测分数或损失。三个窗口整体替换到同一partner。support partner只来自support，query partner只来自query，不跨集合，不回退到自身/同block。

real与twin共用真实source上冻结的H0、窗口probes、scaler、a0及时间基底，不重拟合一套twin source。E0仅在相同合法query交集替换scorebank。个人对照在同一twin-eligible支持行集合上分别拟合real-control和twin-control的HP/EC/ET；后者只替换完整K3 scores，当前history/y保留。两者再在同一合法Q交集比较。不能用real的全support对twin的较小support；完整自然支持/查询下的真实主分析另报。每次以替换后的scores和当前history重新调用冻结的时间投影，不只替换raw scores却保留real时间特征。

ET的real-control与twin-control差反映支持和Q两侧声音对应性的共同变化，不命名为单独query干预或纯时间机制。该对照复用本包数值拟合，不增加source训练。

无合法support twin时，该人twin-personal状态记`not_estimable_no_support_partner`，保留其所有真实数据结果；不能删出64人主分析，不能将缺失置零。twin是当前对应性敏感性，不是精确条件随机化检验：6档history不穷尽所有历史。

## 五状态和直接估计量

| 状态 | 使用的信息 |
|---|---|
| H0 | source-only历史预测，无EEG、无目标support |
| E0 | source-only历史加固定共享时间EEG组合，无目标support |
| HP | 个人自然support拟合历史修正，无EEG |
| EC | 与HP同一历史修正类＋共享EEG方向的个人正尺度 |
| ET | EC＋最多K−1个source确定的条件残差时间方向 |

`G0=R(H0)-R(E0)`：无支持共享EEG增量。`GC=R(HP)-R(EC)`：个人标定后的EEG增量。`DT=R(EC)-R(ET)`：额外时间重权收益。`GT=R(HP)-R(ET)`：时间读出后的EEG增量。`J=GT-G0`：个人化是否增加了公平history基线之上的EEG贡献。它们全部是同人同query直接计算的差／交互。

G0和DT是本轮主估计量；GC/GT/J/GH是预先指定的机制分解，分family同时区间，成员已在plans/round1.json冻结。主结论不能只用ET−E0，因为它混合history、尺度和时间。E0不成功而EC成功时，结论为“有限个人校准后可转移”，不能称无支持群体读出已经共享。

个人正则采用包内固定λ=1（标准化设计、sum loss + quadratic penalty）；一旦开始outer计算不得改。R1不新扫网格；使用凸拟合至数值收敛。不得按目标query退回E0；所有固定状态逐一报告。精确参数化见03。

## 一次必要的工程验证后完整运行

检查合法source组/THdev、fit/test内容与联合访问guard、source统计来源、真实full update、凸模型嵌套、错配partner合法性和同query对齐。正确性通过即可启动全计划，不要求r/AUC/p达到门槛。工程失败修复受影响依赖，不用表现好坏选择重跑。实际训练与缓存提取由server完成；包内合成测试不代表真实数据实验已完成。
