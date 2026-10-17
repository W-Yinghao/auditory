# 04 · D多seed立即汇总，听觉下游使用新执行版本

## A. 已完成面板现在汇总

[B01 L763–L767]报告240个新增seed记录已complete：NCE的D_ADAPT none/input_spatial，以及D_ATTENTION attended/align+sel两个整合器。先读取现场记录确认，不把文档时点当实时状态。

写一份简短分析说明：已见3401结果、哪些面板值已被查看、配对键、终点、身份汇总与同时区间范围。然后立即计算各seed差值、身份内seed平均差值和覆盖表。保留原D_ADAPT的gain主表，新增真实query风险作为明确的新分析；native/unified和rank/accuracy分开，不换掉不利的主指标。

每名身份只计一次；fold/content重复先按原合同合并，seed不是新样本。报告跨seed范围，不把3个seed当充足的总体随机性估计。缺失pair不填0。CS、coverage、output_low_rank和selection_only不在该面板，不能共享三seed结论。

## B. 学习型注意整合修正

基于简报的异常native列和此前代码审查提出修正，**尚未证明其解释所有异常**。恢复可用逐窗原始分数，候选顺序采用成对交换：同一观察评价(A,B)及(B,A)，标签随之反转，二者不能分到不同train/test。平均分数与所有学习型方法用相同测试窗。

推荐新评分：l(d)=0.5[h(d)−h(−d)]，p=σ(l)。则p(−d)=1−p(d)。模型训练也提供成对顺序。h可继续用固定摘要；或用对|d|等交换不变量的权重再加权d。不能让真实注意标签以隐含候选位置进入输入。

保存旧版本结果，不静默覆盖。5秒只有一个段时只是阈值／校准问题，不称时间整合。5/10/20秒在相同窗口长度内比较方法；不要把增加证据时长当成响应潜伏期。尽量重新评价已有分数，缺分数时从保存模型评价，不默认重训全主干。

## C. 个人适配：限制形式，而不是假定C×C已经足够小

当前input_spatial为C×C；64通道有4096个参数。新比较增加：

A_diag=I+diag(d)，A_rank=I+UV^T，A_full=I+M。

默认rank4起步，64通道时U/V共512个参数；同样把rank作为可调配方，不作理论最优。低秩identity初始化不能让U和V同时全零，否则两个因子都无一阶梯度；参考实现U小随机、V零，输出仍严格identity。

保留none、full-spatial、output-low-rank既有基线；增加diagonal/low-rank-spatial。沿用同一10%/30%支持及固定后70%查询以复核，记录实际分钟、独立内容和有效样本，实际EEG/滤波访问不跨support/query边界。

普通群体训练+同adapter，与源人support/query episode训练+同adapter成对比较；群体训练数据暴露和个人支持一致，额外计算另报。第一阶段local与真全量CBraMod并行，代表性REVE保留；不自动把全部backbone×loss×rank×支持做大交叉。

时间adapter仅在声明可访问的lag内组合，不把query窗外信息回流至早窗。以上均为同会话已知刺激监督，不叫无标签TTA或跨会话复现。组差收缩不是训练目标。

## D. 新策略臂的决定已经给出

旧fixed-grid/旧C执行保持原记录，完成部分如实汇总，未完成特定ID继续暂停。新策略使用`new-aligned-true-full`版本，候选含local与合法真全量CBraMod，代表REVE；不默认带上未证明有净收益的互补策略。

用目标任务的内层开发选择候选，不能按外test或HA/CI显著性选。若把一套声音检索模型直接迁移到注意任务，也单独记录其训练任务。性能是否迁移由实验回答，不由B的总分代答。合法checkpoint就绪后逐fold启动，无需再次统一go。
