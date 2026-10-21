# 6. 汇总、可改变判断与报告

## 6.1 分析单位与预定家族

统计基本单位是独立person，先在同person、同seed的合法query上计算，再对重复seed等权平均后做paired population比较。不得把trial/anchor/seed当新增人。两个方法人数或query不同，先列覆盖和共同query，再作匹配对比；缺失、代码失败、有限值负结果分开。

预定四个family：F_CONTENT（DTU/FAU history-residual envelope与private history增量，TCS−B0/TNCE/GCS/wrong）；F_TIME（各队列W0→W2固定损失与重拟合恢复，同四对比）；F_UTILITY（private CE AUC、core3年龄MAE、public attention20s，TCS−B0/TNCE以及年龄vsraw/mean）；F_ASSOC（第5章的四个人端点及指定metadata系数）。R2支持属于独立F_SUPPORT，cross-stimulus单独F_CROSS_STIM。每族的全部列、有效人数、缺失规则在看新结果前冻结。

复用仓库现有以person为单位的paired bootstrap/同时区间实现，但其旧hardcoded13families必须替换成上述声明并保存列清单。建议沿用原实施4000 bootstrap draws和seed命名；确切旧实现先核对并写binding，不从两个aggregate CI相减构造差异CI。本包generic `paired_summary.py`提供一个可审查的person-paired max-|t| bootstrap参考（4000draws），不是静默替换旧统计。不同family独立报告；跨family比较不声称全局校正。单seed R1标探索性，最终三seed人口推断仍以person为n。

当source数据或representation训练人员相互依赖时，person bootstrap只刻画目标样本条件于已训练模型的不确定性，三seed不等于重采样所有source训练数据。报告这种范围；少数同日跨刺激paired children只作明确有限样本估计。

## 6.2 必备结果文件

- `intake/`：Git/server/queue快照、资产/旧证据审计、真实数据roster和依赖；敏感原始身份留private。
- `bindings/BINDING.json`：所有实际hash、训练/ES/support/query可见内容、窗口/采样/overlap、planned与actual fits。
- `source/`：step级loss与CS log-potentials、q/q²、rank/梯度、每人n/合法negatives、实际time access、optimizer/fullupdate/重载receipt、checkpoint索引。
- `features/`：缓存索引/hash/产生代码/role，不将大原始特征推送公共仓库。
- `person_results.jsonl`：已授权去标识person、dataset/group、arm/seed/fold、endpoint/条件、query hash、value、n_trials、status；age预测按已授权字段scope保存，不公开原始身份。
- `contrasts.json` 与 `coverage.json`：paired n、seed覆盖、query对应、预定family和同时区间、探索性新增问题。
- `ROUND1_REPORT.md`：主科学问题→证据→解释→具体剩余不确定性；最后列训练成本、故障/偏差和R2执行差异。

状态枚举：NOT_RUN、RUNNING、COMPLETE_VALID、MISSING_ASSET、IMPLEMENTATION_FAILURE、NUMERICAL_FAILURE、INSUFFICIENT_DATA。有效低分/反向结果是COMPLETE_VALID，不用FAILED标签把它藏起来。退化但有限的表示按有效结果+diagnostic flag报告，真实shape/梯度/数据错位不能算科学负结果。

## 6.3 R1后的判断表

| 观察 | 允许判断 | 下一步 |
|---|---|---|
| 正确配对优于B0，且内容/历史控制一致 | 声音训练有有用迁移的证据 | 固定重复，评估个体支持与任务范围 |
| TCS和TNCE相当 | CS可行，CS必要性不成立 | 保留两者，不靠扩大调参制造胜者 |
| TCS优于GCS，时间结构也改善 | 时间分布构造有贡献的候选证据 | 用唯一消融槽检验仍未区分的机制 |
| TCS只优于wrong | 可能wrong伤害了表示 | 不能单凭此宣布刺激特异收益 |
| private AUC改善但content/time无对应 | 事件任务收益成立，机制未定 | 报告分离结果，不重写听觉时间故事 |
| age/core指标弱或反向 | 该任务/配方支持不足 | 保留旧有效结果；不推无信息/天花板 |
| source末段未收敛或input不兼容 | 优化/可用性仍有限 | 工程错误定点修；有限预算未解决不称充分证伪 |

所有新探索性contrast写明结果已知时间与选择理由，但不把新措辞当必须重做整个实验的理由。三轮里允许一个方法实现失败，允许保留所有有用旧结果；不要求把每条证据挤成一致方向。

### 家族按队列落地

F_CONTENT、F_TIME、F_UTILITY、F_ASSOC首先按cohort分别绑定，例如 `F_CONTENT:DTU`、`F_CONTENT:FAU`、`F_CONTENT:PRIVATE_BDF`。不同队列没有共同person，不能对跨队列列做complete-person交集。包内paired mean参考只接收同一cohort同一family的已配对个人差值；它的同时区间覆盖该family，不覆盖所有cohort/全部论文端点。若最终要报告跨队列统一家族，另用按cohort独立重采样、在同一replicate取全family最大统计量的既有统计框架，先冻结实现，不把不同人强配对。

metadata回归系数与R²/Spearman不是个人均值差，不能直接交给`paired_summary.py`；按既有person bootstrap重拟合每次回归/重新计算统计量。年龄MAE的配对绝对误差差值可使用该参考。完整family交集、各contrast独立可用人数和描述性全覆盖结果都保留。
