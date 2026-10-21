# 输出、统计与保留

## 主结果表

每人、每content fold、每seed、每合法parent输出H0/E0/HP/EC/ET的同query风险，support预算、query集合哈希、source排除范围、模型/尺度/时间基底哈希。公共同时输出source标准化MSE、r，私有输出NLL bits/trial、AUC、Brier。r/AUC均辅助，不能替代本轮proper-risk主比较。

每个query先对所有状态使用同一索引；人内平均完整content repeats，再按预定seeds平均；最后每个独立人等权。不要把重复seed、内容折、5个人折切片、时间窗、trial数或job数当独立n。FAU使用CI24、HA29、TH14正式目标面板；TH dev不计入目标样本。DTU44；儿童64。错误/缺项透明输出，不能将缺失当0。H0/E0必须在personal fit之前独立保存；个人拟合失败或没有合法support不删除其共享基线。缺少必要成员时family标incomplete、不生成完整family区间；保留全员G0点值和每个缺项原因，不把可完成者冒称全队列。

## 预定统计families

1. `F_FAU_GROUP_SHARED_TIME`：2工具×3目标组×(G0,DT)，12个主对比；每组内人级成对bootstrap，组间独立重抽，所有成员共用相应人索引。输出该family同时95%区间及逐人值。
2. `F_DTU_SHARED_TIME`：2工具×(G0,DT)，4个主对比。
3. `F_PRIVATE_SHARED_TIME`：AP/APwrong×(G0,DT)，以及AP−APwrong的G0/DT直接差，共6个主对比。
4. `F_PRIVATE_CURRENT_CORRESPONDENCE`：AP/APwrong×真实E0对twin E0、真实ET对twin ET，共4个；在每family声明的相同合法twin-query和完整人覆盖上计算。与full natural-query主family分开，不以twin可估计性删主结果。

公共对应性family另固定为`F_FAU_ALIGNMENT`（2工具×3组=6项M0−E0风险差）和`F_DTU_ALIGNMENT`（2项）。它们仅检验固定E0对EEG—声音对应关系的敏感性；query错移不产生新样本，也不代替history主控制。

机制分解另有固定family：`F_FAU_MECHANISM`为2工具×3组×(GC,GT,J,GH)=24项；`F_DTU_MECHANISM`为2工具×4=8项；`F_PRIVATE_MECHANISM`为2 arms×4=8项。它们与上述主family分开给同时区间，不把额外成员偷偷放进或拿出主family，不凭单个漂亮差值升级为主终点。GC不是主family中遗漏的端点。所有组间调节分析使用逐人效应的直接差，不能“一个组显著另一个不显著”代替组差。私人HA/NH与年龄／阶段仅报告预定观察性估计，NH9限制明确，不追加切点。

采用B=4000的按人重抽，主实现沿用经验证的同时区间代码并标明确切统计法。包内`paired_summary.py`提供固定原始SE的max-|z*|参考，非旧bootstrap-t；旧历史结果不重命名统计法。退化方差、不完整人、缺乏可比较twin必须输出非regular状态。不同family之间不声称全局95%覆盖。区间条件于已拟合模型；两seed不是训练随机性的完整分布。

`plans/round1.json`登记范围，`evidence/`登记既有依据，`MANIFEST.json`记录本包字节。真实server额外生成：INTAKE、唯一trainplan、evalplan、binding_receipt、source-exclusion receipt、unit records、per-person contrasts、family summaries、R1_SCIENTIFIC_DECISION.md。关键stdout/失败日志按现有规则保存，不能只留汇总均值。

## 下一次给研究者的报告应先回答

无目标support时有没有可迁移的当前声音证据？整体概率/历史校准后，时间重权还增加多少？儿童当前EEG对应性是否存在？这些结果使哪条具体假设变强、变弱或仍未确定？之后才列完成度和耗时。不能再用大段调度流水账替代科学判断。

## 存储清理的范围

此前提及A3d约233GiB、A3c43.1GiB、A3b13.8GiB、ALN2 D_FM32.1GiB，合计约322GiB。容量名称不是可删除性的证据；真实候选列表未随GitHub发布。本包不执行或授权一条未核对的整目录`rm -rf`。

优先保护：local/CB直接父权重、genericCB初始权重、matched AP/APwrong donor与target权重、现有content/private缓存、sound/history目标和physical split绑定、所有unit记录/逐人预测摘要/统计/代码hash。新实验只保存best/source必要checkpoint和轻量逐人读出结果，避免无目的保留每步快照。

旧A3c attention已完成读出若预测cache足够，相关无后续消费的权重可以列为精确删除候选；D_COVERAGE分开核对。ALN2 D_FM旧teacher/校准/蒸馏相关权重在实际依赖都结束后可列候选；public donor目录不是同一批。A3b/A3d需要现场路径分类，不能按旧容量整体判废。已有episode3407完成会解除它特定旧依赖，不代表所有其他消费结束。

删除前只做一次基于本轮真实依赖的文件清单，保留派生结果、来源hash与重建方式；清理不再新增一个科研实验分支。此处未远程删除任何文件。
