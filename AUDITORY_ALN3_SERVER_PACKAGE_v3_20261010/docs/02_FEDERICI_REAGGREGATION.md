# 02 · Federici实体与身份重汇总：复用结果、不重跑全部训练

## 目的与范围

修正“文件/条件/幻影头被汇总为独立儿童”的报告问题，保留全部历史结果。该修正来自代码审阅S04–S07；精确的实体计数、重汇总后的数值及对结论的影响需server从逐单元记录核实，本包不捏造修正结果。

## 身份清单

由原数据元信息与现有loader构建私有 `entity_manifest.csv`：
`dataset, record_uid, subject_uid, condition, entity_type, identity_source, source_hash`。

- HC/CI/HC-v应以来源核实后的 `entity_type=human` 标记，Artifact的实体含义从原始元信息核实并单独标记 `phantom`（不能仅凭文件夹名对任何未来数据自动判断）。
- HC和HC-v对应同一儿童时使用同一subject_uid。CI等编号空间不能只去前缀后合并。
- 身份不明确的对象标记unknown，保留明细并先单列；不按EEG相似度猜身份、不按解码分数决定是否人类。
- 区分record_uid、condition、subject_uid、content_id、subject_fold、seed，不能一列兼任。

## 从现有输出导出与重算

先保存旧aggregate与FULL_RESULTS的hash。新版本写到 `results/auditory_alignment_v3/reaggregate/`，不覆写ALN2。

导出规范化长表（私有）每行是一名记录/条件在一个单元下的度量：
`dataset,config_id,seed,subject_uid,record_uid,condition,entity_type,subject_fold,content_fold,unit_id,metric,value`。
同一单元同一记录同一metric只能一行。先在记录内平均重复内容折，再在同一儿童同一条件内平均记录；默认每名儿童同等权重。查询加权的版本可以另报，但不能静默改变目标人群。

输出四组表：
1. **HC、CI、HC-v分别报告**：每组唯一儿童数、记录数、内容数、gain与真实query损失/检索。HC-v不是新增独立儿童。
2. **同儿童HC−HC-v配对**：只用有两条件的来源核实对子，按儿童求差、按儿童bootstrap，报告缺失条件数量。该对比不是设备治疗因果效应。
3. **CI−HC**：在固定方法、同内容/目标规则下，按人类身份比较；年龄关系另行建模，不把CI当HC配对。
4. **Artifact/phantom独立**：仅用于声音同步污染的敏感性参照。重复折上的同一实体不累计为更多样本，不纳入儿童平均、年龄模型、训练或donor。

本次重汇总保持原候选池与原预测不变。另建human-only候选池属于重评价，所有比较须在新池上共同重算，不能只删汇总行却假称已改变检索任务。规范CSV一次只包含一个明确split合同；变更split的结果分别导出。

主文优先分组与配对，不推荐再生成一个所有条件混合的“总体儿童成绩”。确需一个人类汇总时，先对每个身份内部条件等权平均，再对身份平均，并明确该混合人群定义；不与HC/CI特定问题混用。

## 相关重新计算

对全部主模型都重算，不只重算REVE或有利模型。重算预训练−随机、局部−旧模型等同身份配对差。窗口曲线在每次bootstrap中整条重抽同一身份，避免不同时间点换不同儿童。

同一模型跨多个折对test_only幻影头的预测可以保留为模型变动分析，不能将其当多份独立实体。跨seed结果先分别报告，再按身份汇总配置均值；不能把seed×儿童当独立n。

## 阻塞范围与交付

这是CPU重汇总任务，无需重训只因汇总有错的checkpoint。并行开展FAU/DTU/私有新训练。新的Federici训练/多队列donor必须使用纠正后的human训练清单；这只是输入依赖，不是成绩门槛。

交付 `FEDERICI_REAGGREGATION_RECEIPT.md`、分组/配对/phantom聚合表、旧新数字对照及结论更正说明。身份表和逐儿童长表留private。本包 `scripts/reaggregate_federici.py` 是对上述规范长表的参考实现，不是对当前私有JSON结构的自动猜测器；server需要完成一次明确的数据导出适配。
