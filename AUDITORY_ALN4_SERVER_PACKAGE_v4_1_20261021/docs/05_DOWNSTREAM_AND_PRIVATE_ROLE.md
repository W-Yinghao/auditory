# 5. 下游科学评价与私有儿童的功能

## 5.1 共同冻结读出

五臂都缓存每个目标fold、每个人、每trial/anchor、每slot的原始backbone token表示，不把source64ch音频head错接到private20ch。冻结probe用相同结构与标签访问；同一target fold中的标准化/PCA只用其fit部分。

为了保持channel信息并限制CPU规模，按固定channel/token次序flatten，使用一个跨三slot共享的PCA64（维数min(64,D,Nfit−1)）；fit行最多8192个，按固定ID排序+seed3437选择，所有arms同一行集合，每slot等量，8192上限下实际最多8190行；严禁每slot独立PCA后直接做TG。只用fit统计、不能用ES/query做PCA；保存components/mean/scale和row hash。此降维为共同读出工具，raw维数/保留方差记录；不称无监督transductive test训练。

公共声学内容用现有ridge/源侧校准合同；私有用已有logistic/positive affine source-ES校准合同。相同hyperparameter候选和fit/ES access对所有arm一致，server复用已注册实现并把其参数hash写binding；不临时给TCS扩大readout搜索。参数/solver有不兼容时先做共同新版本，旧输出独立保留。

## 5.2 内容与时间分别问

公共共同内容端点：held-out人上的envelope r，以及用训练侧history-only模型解释后剩余的envelope readout r。已有谱成分结果继续呈现；缺少rich的队列不补造目标。private主要内容端点：当前standard/deviant AUC与history-conditional log-risk增量。后者使用同label access的history-only B1，并在其他physical block、同child/history-bin的strict-twin子集再比较当前EEG与twin EEG。完整query与strict subset分别报告人数、trials和风险，不用不同覆盖的两均值互相相减。

时间迁移固定三slot×三slot的同表示读出。对每个源窗r用训练侧数据拟合readout/calibrator；直接应用到目标窗s得到固定读出性能。然后在目标训练侧的窗s重新拟合相同容量readout，评价同一query。主时间对比预定W0→W2，完整3×3为描述性结构；报告同窗、固定迁移损失和重拟合恢复，方向按“更好”为正。重拟合恢复不是增加EEG数据、不是目标测试人labels、也不是个人δ支持。

当前源训练q0用于slot概率/预测混合，同时输出相同heads下q=uniform的结果和各slot结果。这项重置不新增encoder或head训练，只检查源time prior是否实际有用。相同head下融合可能改善方差，不能据此宣称潜在神经成分完成独立分解。稳定性可用既有block split-half，把不可靠的个人曲线明确标出来，不按可靠性阈值排除结果以制造人群差异。

## 5.3 年龄是独立可回答的用途

R1设置冻结表示年龄回归，回答“公共声音/时间训练后的同一编码器，是否保留可在未见儿童预测年龄的EEG信息”。这与年龄对AUC或history增量的关联是两个问题，不用后者的弱结果否定前者。

输入为每儿童一个主记录、每slot原始token向量的自然trial均值和std（ddof0），按固定slot/统计/channel顺序串联；不用事件标签、不用个体q、不把五个private FT网络产出的特征拼成统一空间。所有儿童由同一个source Stage2模型编码；B0同Stage1。可用age roster在看模型结果前按metadata缺失确定，年龄单位months。

既有5fold outer child identities；outer train内以seed3431固定child shuffle做4fold inner。每个inner fit单独逐维标准化、目标减train mean，dual ridge的alpha∈{.01,.1,1,10,100}乘trace(XXᵀ)/n，以inner MAE选，tie取小alpha；outer train重拟合，outer heldout预测。head的outer test年龄只用于最后算分。若metadata不足使某fold无法4折，记录实际原因，统一固定min(4,Ntrain)且至少2，不挑可预测子集。

两基线：同outer train平均年龄；相同epochs/同人/同fold的20-channel mean log-variance原始EEG ridge（从GX staged epoch读取，在hc整人channel z-score之前，先trial内真实样本variance再log再trial均值，确定epsilon=1e-12并登记信号单位，不能用padding；如原幅值资产不可用，明确MISSING_ASSET而不偷换成归一后参考），用同inner ridge流程。这个raw基线不是旧D2连续频谱基线；旧D2结果另表复用，合同一致才作直接数值比较。

输出每儿童OOF预测和误差、MAE(月)、RMSE、R²、Spearman、对train-mean/raw的配对误差变化及fold选择；按HA/NH描述并列，NH9人的不确定性明确。年龄和HA/佩戴时长相关，预测不自动表明听觉特异发育。三seed先计算每人每seed绝对误差、再在人内平均，之后作paired人口汇总；平均预测后算MAE属于ensemble另端点。RMSE由逐人OOF残差计算。fold/seed不是独立样本。`reference/age_probe.py`仅实现该小CPU读出，不替代真实EEG特征导出。

## 5.4 组别与发育关联收住范围

只预定四个人级端点：history-conditional当前声音增量、W0→W2固定读出损失、目标窗readout重拟合恢复、R2 U30相对U0的变化。core3均保留；用TCS−B0和TCS−TNCE的直接个人差异形成方法×组/年龄解释，不在一组显著另一组不显著时声称组间差异。

private用既有两式：全体age(year)+HA indicator；仅HA age(year)+device-duration(year)，NH时长不填0。FAU HA/CI/TH与DTU HI/NH各自按现有协变量/身份合同分析，不并队列强造疾病轴。控制预定端点/contrast多重比较，报告效应与区间；不给每个head/window/historybin都回归metadata。设备时长是横断面，不写成疗效轨迹。

## 5.5 Attention 与外部方法

公共attention使用attended/ignored两个候选，双顺序评分并遵守已修正的antisymmetric规则，tie=.5。主为mean-score连续20s证据积分，5/10s从同一margin流描述性导出；这些是积分时长而非神经/行为响应时间。采用共同声音readout评分，不要求CS native cosine天然具备一一坐标对齐。不得把需要候选音频的任务与儿童EEG-only任务混称相同输入预算。

完整MindMix比较遵循其三阶段、可用模态、训练数据和下游head，记录是否音频参与测试EEG表示。共同任务同split/metrics，并报告模态/预训练数据差异；如果接口不等价，不把失败归因到方法。此前local、CB真full、REVE与FMCA结果保留为历史外部/内部参照；本轮不为每个已试组件重新开网格。
