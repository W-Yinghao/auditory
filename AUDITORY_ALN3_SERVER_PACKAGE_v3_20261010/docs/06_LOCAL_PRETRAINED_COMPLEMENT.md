# 06 · 工作包C：局部听觉通路与预训练补充

## 候选方法，不是已有结论

ALN2证明局部模型有效，并显示若干预训练收益；**并未证明二者具有互补信息**。本工作包的任务就是在同一query目标上检验补充价值，而不是强迫基础模型取代小模型。

## 共同输出空间

先得到局部预测 `A_local(q)`。残差模型为：
`A_combined(q)=A_local(q)+R(H_local(q), H_FM, q)`。

输出在同一个固定声音特征/训练侧桥接空间。NCE/FMCA/CS的两个latent可能有不同坐标规约；不能把它们直接相加后声称音频残差。采用fixed_latent时两支必须由同一固定音频参照训练，仍保留独立probe；最清楚的主参照是显式声音预测空间。

私有任务对应logit：`logit_combined=logit_local+residual_logit`，最终在训练侧统一校准。不能混加AUC或已sigmoid概率。

## 必须有的完整比较

| 变体 | 说明 |
|---|---|
| local_only | 04的有效基线；不要把较弱density代替它 |
| foundation_only | 05同grid可用读出 |
| concat_pretrained | 简单拼接和共同头；检验残差结构是否必要 |
| residual_pretrained_frozen | 冻结原始/任务适配前backbone，仅学补充头 |
| residual_pretrained_peft | 小规模适配补充分支 |
| residual_pretrained_full | 允许全量任务适配，完整训练 |
| residual_random_frozen / random_trainable | 同架构随机分支，区分预训练和新增结构 |
| residual_small_capacity | 类似容量/计算的小分支，区分通用先验与模型容量 |

不是每个控制都与所有超参数交叉；核心比较的初始化、输出网格、局部基线、query池必须一致。

默认frozen/PEFT/full补充分支从**原始预训练checkpoint**初始化；使用已听觉适配donor的版本必须另列initialization字段，不在同一个配置中混用两种起点。

## 初始化与训练阶段

残差输出层初始化为零，使**初始输出**与局部基线逐元素相同。不要在加法后新增会改变基线的归一化/门控。初始等同不保证训练后测试不退化。

先冻结局部基线训练补充头；随后把联合微调作为独立配方完成。残差最后层为零时，第一步上游残差特征梯度可为零，这是结构性质而非LoRA失效；第二步及后续检查真实梯度路径。保留λ=0/local-only参照。

NCE和传统CS作为主要学习目标；预测MSE或固定目标桥作为相同任务参照。先比较单目标，再有目的地比较组合，不默认“三种loss相加”。调节权重只用训练侧内容，不能按儿童发育/设备差异调参。

## 区分价值来自哪里

主增量 `R(local)-R(combined)` 用同一真实query风险。若只有错配损失变大而真实风险未改善，不称性能补充。检索、自然NLL、重建与attention分别看；不能因为任一指标变好就称所有听觉功能改善。

比较：原FM上下文、合法错配FM上下文、位置only、随机权重FM。错配只作对照，不要求它们必须达到预设数值。结合主体小分支容量对照，判断是否确实利用了正确的预训练EEG观测。

## 早晚研究的两种合法使用

- full-context residual：面向整体声音/注意任务，不能叫早期独有证据。
- support-conditioned local residual：个人背景来自独立support；query只取早或晚窗。support、query与目标标签访问写清，不把当前query的全局token作为背景绕过窗口。

严格局部通路始终单独评价，即使融合表现更好也不能抹掉这一部分。没有互补收益时，保留结果并研究读出、任务匹配和目标尺度，不默认成稿为“基础模型无用”。
