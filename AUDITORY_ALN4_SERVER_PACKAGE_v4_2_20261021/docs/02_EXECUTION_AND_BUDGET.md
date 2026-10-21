# 2. 执行顺序、既有任务和成本

## 2.1 本包接到正在运行的第二轮上

| 工作流 | 已冻结范围 | 本包动作 |
| --- | --- | --- |
| ALN4.1 R2 | seed3407/3413；4 source臂×2=8；core3×5fold×2=30 private CE；non-B0 frozen20×2=40 | 保留原 unit ID、LR1e−4、stream/panel规则、final10000；完成的依赖一致单位直接复用 |
| B0 frozen | R1 seed-free基线，PCA seed3437 | 沿用既有复用；不得为了凑3seed复制成3次独立观测 |
| F_SUPPORT | core3×全部3seed，既定20成员family | 完成原计划，增加明确净收益解释和δ诊断导出 |
| F_CROSS_STIM | B0+TCS/TNCE各3seed=7次frozen extraction；pure-tone→bapa | 完成原计划与13成员family，声明refit完整流程和训练覆盖 |
| ALN3.6 R2 | seed3407，12 FAU整组source、52公共feature banks；匹配AP/APwrong供体及target | 完成原绑定；旧 pooled parents 和已完成同依赖资产不重训 |
| ALN3.4 尾巴 | 发布时DTU budget剩1、breadth curves剩18 | 接包刷新队列；不以这些数值重新提交任务，也不新增旧探索线 |

一次训练可产生多个评估格；不要按表格格数计算训练量。已有任务属于原合同，不因新包改名或重新计费。R2里已看到的新结果也保留，新增诊断标注设计时间。

## 2.2 优先级

P0：只读 intake / 原计划身份与代码绑定；核实依赖并继续原有效队列。  
P1：源学习诊断和儿童事件定义核验，两者可并行，优先 CPU / frozen forward。  
P2：完成原 R2 主结果、F_SUPPORT、F_CROSS_STIM；并行完成旧结果证据归位。  
P3：完成 R3 的一个外部比较席位和最终科学图表。  
P4：最终研究判断、方法说明、结果覆盖与资源账本。

工程问题只影响实际依赖其错误字段的任务。不能因一个family的CI问题停止无关公共训练。若真实错误使一项仍在跑的任务目标/标签无效，按既有job所有权规则处理精确范围并保存旧版本；禁止仅因弱分数取消任务。

## 2.3 新增预算

| 新增项 | 上限 | optimizer更新 |
| --- | --- | --- |
| source诊断 | 固定fit32+dev32 episodes，每episode原2人；4arms×4既有snapshots；合计最多4 A100等效GPU小时 | 0 |
| private事件审计、净风险、图表与coverage | CPU；复用已有预测与元数据 | 0 |
| R3外部方法 | 一条已固定路线；一个发布checkpoint、下游seed3401；DTU44的2content×5person=10公共单位 | MindMix最多10个Stage3 fits，或Transformer-CLIP的10个冻结表示线性读出；两路互斥 |
| 新儿童外部full FT | 本版未启用 | 0 |
| 方法消融 | 本版未启用（原合同单一槽仍记录为未用，不转移预算） | 0 |

原R3只占一个外部席位；本版根据实际公共代码明确10个下游训练单位，source pretraining为0、儿童外部FT为0，不运行被试内44×5=220个模型。完整MindMix有合法原始输入与盲候选评分时保留其Stage3训练；fallback沿用Transformer-CLIP冻结encoder的原生回归用途。两条都标明共同协议任务适配，不用缩减作者阶段冒称复现。参见docs/06及机器计划。

4 GPU小时是诊断预算上限，不是效果门槛或完成时间承诺。预估首次固定单元的实际秒数与显存，再确定microbatch；人内Gram和32anchors不拆成不同估计。IO与CPU时间另报。缺checkpoint时报告实际缺失，不重训补checkpoint、不择优改选snapshot。

项目 running+pending 合计10GPU不变，原ALN4.1优先级不变。使用Slurm、现成硬件兼容规则与精确作业所有权；node51已排除，P100不使用。不得在主节点直接启动未登记GPU训练；不修改正在运行的源码。

## 2.4 实施文件的边界

本包工具是数据合同校验与数学参考，不伪造生产CLI。建议新建服务器模块 auditory_alignment_v3/aln42/ 下的诊断/导出/报告层，具体函数由现成接口适配，实际新增文件名和调用在binding中记录。

必须提交的实现收据：导出器源hash、父模型/源计划hash、完整panel IDs私有hash、软件版本、所读checkpoint列表、没有optimizer.step的检查、同query对照重现误差，以及每个结果的实际覆盖。

旧生产source/frozen/private_ft/support/cross_stim模块在未确认bug时保持字节不变；新增诊断从它们调用相同的模型、采样、crop和objective接口，不重写一套相近的训练定义。

