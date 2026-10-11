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
