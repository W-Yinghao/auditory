# C2-S 共同试次上的空间成分线性读出

六个视图复用冻结的 P1/P2 accepted 交集和 P1 全20通道参考/因果滤波。每条 trial 严格使用其 post_start_index 起100个250Hz样本，5样本形成20ms箱。逐批核验完整epoch及post重建、19维有效坐标和右侧扰动不改变左局部数值。所有候选保留原共同trial；只检查每候选两类存在、总候选至少20和每外折训练至少12/测试至少2，不追加20试次/类排除。

六视图各自训练内候选等权 scaler，不做PCA；GroupKFold3选择四值C，内折重新拟合scaler/head。本路线是NEW_ESTIMATOR，采用新温度范围[0.25,16]，仅训练OOF校准，不加先验混合。共390次logistic拟合。raw和cal使用稳定logit交叉熵，以候选/类别等权的bits/trial报告；FULL20与S2可逆，正则化性能无需相等。

主增益为S0−S1、S1−S2，另报两个同宽度重复输入对照及FULL20参考。2000次候选bootstrap共享抽样，属于fixed OOF，不含流程重拟合。局部数值隔离不代表选择隔离：原整记录全头QC及P1/P2交集共同决定试次集合，selection_isolation=False。次要MLP受预算限制未运行，不能写成阴性；此结果不完成所有C2科学对照，也不证明解剖来源或PID协同。
