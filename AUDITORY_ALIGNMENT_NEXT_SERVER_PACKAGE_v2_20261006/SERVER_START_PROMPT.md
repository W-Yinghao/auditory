# 给服务器代理：ALN2 时间对齐与预训练完整实验

请在W-Yinghao/auditory的可写工作副本实施本包。核查基准为e993e3777989f3048f4c802c1697b0db3de3c205，上一轮kernel-CS结果主体84c73924ad3da12181e83400f58f0f67a37af8c4。若HEAD已更新，先记录差异并接续真实最新版本，不覆盖新结果。

## 第一条研究纪律

用户要求：**分析不能负结果为导向。现有数据量与覆盖不支持用‘没检出/方法未改善’构造广泛的无信息、天花板或普遍方法失效论文。验证再完整也不能代替科学贡献。**

完整保留失败、反向、负增益和不确定结果，不编造阳性、不按测试成绩删人、不削弱基线。它们首先用于定位目标、表征、时间组织、适配和数据支持问题，指导有依据的新实验。不得自动转成能力地图/失效稿；也不得把旧AGENTS的‘所有新模型、迁移或适配已关闭’当成本轮禁令。参考`AGENTS_APPEND.md`把新纪律写到工作副本最前，保留旧历史。

## 这次确实要实施的方向

A. 时间表示：不再让80/210/600ms都压成同样四格；实现固定时间密度和局部lag-token，与legacy同协议比较。  
B. EEG预训练：CBraMod和REVE，随机同架构、冻结、PEFT、部分层和全参数微调并列；固定声音目标/头作为核心干预；不以冻结成绩决定是否继续。  
C. 群体与注意：共同主干、系统/个人小型适配；同一时刻注意流与忽略流的直接二选一损失，区别于只对齐attended流。  
D. 私有HA：GX同协议baseline、时间保留、通用先验及公共听觉先验迁移；真实当前类别、严格过去历史、早晚与年龄/验配阶段；不以公共阳性作私有前置条件。

InfoNCE为当前强基线，单尺度传统核CS为主要竞争，FMCA做有证据的锚定/统计batch配置。不要引入VCS-QMI或神经critic，不要求CS一定胜出。不联系医生，不虚构私有音频/任务/临床标签。

## 实际执行

1. 读`README.md`、`docs/00`、`docs/02`和最新kernel-CS实现说明，记录worktree、HEAD、diff与数据入口。主要复用`auditory_alignment/`，新增`auditory_alignment_v2/`。
2. 所有真实CPU/GPU数值工作经Slurm。来源目录`/projects/EEG-foundation-model/auditory`只读；使用已批准可写目录。依据集群填写模板，不猜partition或account。
3. 通过包内短测试与一个真实batch的shape/时序/梯度检查。它只验证程序，不是科研门槛。
4. 使用`configs/study.json`与`experiment_families.json`生成完整计划；填好foundation checkpoint与donor来源。未落实字段保持unresolved并解决，不用零结果占位。
5. 全部外折、多seed、完整训练。A/B/C/D可并行；有donor依赖的迁移任务在文件完成后自动继续，不看其p值。新改法可以登记扩展；禁止用一个短run替代完整研究。
6. 模型/配方在训练侧任务验证选择；HA/CI组差、年龄/阶段相关、功能结果不得选checkpoint。原生/统一读出、真实风险/错配增益全部保留。
7. 全面输出`FULL_METHOD_RESULTS`、`TEMPORAL_RESULTS`、`FOUNDATION_ADAPTATION_RESULTS`、`ATTENTION_AND_SHARED_MODEL_RESULTS`、`PRIVATE_TRANSFER_RESULTS`和`NEXT_METHOD_DECISIONS`。使用`docs/09_REPORT_TEMPLATE.md`，不要只给负结果列表或最优单元。

训练参数是可调整起点，不是硬停止阈值。完整训练后如果方法不佳，报告精确范围并比较合理改法；不以‘审计已完成’宣告科学问题已结束。没有新贡献时如实写尚未建立，不制造负面主线作保底。

本包脚本仅能生成计划/测试，真实loader、foundation适配、跨折donor、训练runner和Slurm控制器仍需接入；不要假装它们已经运行。本轮不自动push、不公开私有逐人数据或checkpoint。
