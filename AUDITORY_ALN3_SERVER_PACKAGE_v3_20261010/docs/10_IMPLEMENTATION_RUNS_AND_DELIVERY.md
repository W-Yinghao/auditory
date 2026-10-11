# 10 · Server接入、排程和交付

## 1. 目录与状态

在研究工作副本新增 `auditory_alignment_v3/`、`docs/auditory_alignment_v3/`、`results/auditory_alignment_v3/`、`private/auditory_alignment_v3/`。ALN2代码与结果不覆写；可引用复用的checkpoint、预处理和分折清单。先记录实际HEAD；若与本包基准不同，检查新增差异并写接入回执，不自动回退用户代码。

本包代码是独立的聚类统计/校准/张量读出参考，不是已完成的真实训练控制器。以下仍由server接入：真实backbone层hooks、原数据loader与物理时间、同一声音合同、Slurm worker、逐fold教师和迁移、查询级结果导出、隐私发布扫描。不得把本地合成测试通过写成EEG训练通过。

## 2. 建议接入顺序（不是成绩门槛）

**并行CPU**：02重汇总，已有输出的私有校准重评价，登记数据/target合同。

**GPU主通路**：A局部因素/目标比较；B固定backbone读出与五类适配。

**依赖后接续**：C残差与融合使用对应fold的已完成局部base；D注意/个人适配使用合法base；E迁移/蒸馏使用合法donor/teacher。私有通用训练与GX不依赖公共阳性，可立即运行。

先做张量/形状/梯度/时间访问/身份正确性测试，再完整训练。测试不设置最低检索成绩；短probe是查接口，不是筛掉研究方向。

## 3. 计划文件与执行量

`configs/experiment_families.yaml`定义有问题导向的实验族；`scripts/expand_plan.py`生成`plans/units.jsonl`。行包括：数据、目标、折、seed、配方、信息访问层级、任务类型、逻辑依赖及结果来源。所有新行初始为`planned_needs_binding`，不伪称已运行。精确行数由生成器输出，不手工编一个GPU工作量。

default覆盖seed3401；指定主比较使用3407/3413面板，先登记、不只复跑赢家。计划包含训练、阶段训练、support适配、重评价和统计，它们**不是相同成本的拟合单元**。运行清单可以据训练侧问题扩展，记录增补；不以matrix完整性继续消耗已知错误接口的算力。

未绑定的dependencies是逻辑需求：`local_base_same_fold`、`public_donor_no_target_identity`、`teacher_selected_training_only`、`human_identity_manifest`。server在提交前将它们解析为具体hash/路径，并验证真实来源。无需基于成绩批准，但不允许缺checkpoint时偷偷用测试模型/别的折替代。

## 4. 学习率、训练时长与输入预算

初始工程配方见protocol.yaml。完整训练的小模型与FM/adapter分别选择合理学习率；训练侧开发内容允许多个固定块，不只一个短单元。保留头预热与联合训练的比较；epoch起点不是终止上限，开发仍改善时登记续训。失败/抢占允许从完整状态恢复，恢复不改实验身份。

不同方法统计batch、梯度累积、片段数、query数都记录。匹配数据量和计算量是两种不同控制；至少一张表在相同数据暴露下比较，不把训练时间差写成神经差异。

资源默认继承10-GPU同时运行上限、大模型一GPU一个训练；server可按研究者当前规则调整。模板不擅自占GPU，不提交任何作业。主训练不要被一大批CPU合成模拟占满资源。

## 5. 复用与修复

只有输入清单、分折、目标合同、模型/头、损失、适配、seed与输出协议完全匹配才复用训练结果；重汇总或校准可引用旧预测但产生新评价版本。每个复用记录指向实际源文件hash。

新head改变teacher输出时，旧teacher-target失效但原始pretrained checkpoint仍可复用。旧chmean只作legacy；不得进入主teacher/donor。来源不明或错折的产物不使用，不是“模型表现差”的科研停止理由。

禁止用`strict=False`隐藏跨通道迁移的漏载：为每条迁移保存loaded/missing/new keys、参数量与解释。允许合法的新输入层/任务头，但不能静默丢掉绝大部分网络后称“预训练迁移”。

## 6. 单元最小记录

计划与结果schema分开。每个结果含resolved_code_sha、source_checkpoint/hash、task/split/target/candidate hashes、time_access、真实读出、数据独立规模、训练时长、seed、fit/cal/test来源、query损失及组聚合。失败保留原因，基础设施失败不归为方法阴性。结果原子写入，只有完整记录才进统计。

逐人量、身份键、预测、checkpoint和私人路径留服务器。对外发布仅文档、代码、聚合、配置hash和必要run receipt；本包生成不等于授权自动push所有私有产物。

## 7. 交付清单

- `IMPLEMENTATION_RECEIPT.md`：各模块接入、与本包偏离、实际默认值和时间/数据合同。
- `FEDERICI_REAGGREGATION_RECEIPT.md`：实体/儿童单位修正及全模型新表。
- `FULL_RESULTS.md`：完整矩阵，原生/共同读出与真实风险分开。
- `METHOD_PROGRESS.md`：局部、dense、互补、初始化的主要方法对比。
- `HEARING_GROUP_TIME_RESULTS.md`：人群×窗口×注意，不预定方向。
- `PRIVATE_TRANSFER_DEVELOPMENT.md`：私有任务能力、校准、迁移、年龄/阶段与历史结果。
- `NEXT_INTERPRETATION.md`：按09的建设式结构提出下一步。

每轮说明哪些仅在已有汇总上重算，哪些重新训练、哪些新增数据、哪些只是实现检查。不得用“全部完成”掩盖逻辑依赖未绑定或数据子集变化。
