# 15 · 快速兼容迁移与复用

## 1. 本包替换什么

- 新的§02、Federici规范长表出口和相关测试替换旧版默认HC/HC-v配对。
- §12替换关于队列优先级和主seed使用的宽泛说法；与最近server去重安排一致。
- §13补充并行科学分析，不替换A–E训练。
- §14把新文档中的资源/方法建议区分为候选，避免无意把它们当成主训练依赖。
- 启动文本明确继承开跑授权，不等待第二次审批。

## 2. 本包不改变什么

核心读出、校准和风险参考的tensor接口保持；旧核心5996条logical ID保留。`configs/experiment_families.yaml`的旧version字段是其原登记来源，不是现行治理版本。当前治理以`configs/protocol.yaml`和`configs/seed_policy.yaml`为准。

`plans/units.jsonl`是原比较账本，不是server已提交任务，不可直接全部重新投递。已开始的新ALN3任务不因包名变更从头跑。实际execution hash至少绑定data/split/target/head/objective/recipe/seed以及base或teacher来源。

## 3. 快速接入动作

1. 记录实际HEAD，更新规则优先级，不checkout回旧commit。
2. 读取当前运行账本而非引用聊天中1474/2220等旧快照；做一次只读调度建议，按确切job ID应用到自己的任务。
3. 将Federici真实ID和人口学清单合入出口，重新汇总，标清哪些age分析受影响。
4. 将3b/3c逻辑问题映射到B；记录warm-up/LLRD/每epoch验证的新增执行版本。
5. 从已完成A/E/B checkpoint开始科学分析；tensor或身份错误只阻塞相关路径。
6. 绑定核心seed配对表；复用完全兼容结果，缺什么只补什么，不再全矩阵翻三倍。

## 4. 工具的限制

`queue_advice.py`接受一份规范化现场账本，只输出建议，不调用Slurm。`register_seed_pairs.py`接受原核心计划与本包规则，生成待绑定角色表，不提交或取消任何任务。它们不读取性能列决定停止，不能替代server现有worker/队列控制器。

依赖绑定、相同训练合同检查、实际资源授权由server现有系统完成。本包没有看见实时队列；不能将示例输出当成自己的job清单。

## 5. 发布纪律

私有年龄、身份、逐试次logits、checkpoint和私人路径留服务器。只按既有发布规则公开无敏感的配置、聚合与代码。不要在公开报告复制元数据中的个人身份，即使数据源有可访问编码。


`seed_pair_roles.json`的总行数是多个面板引用去重后的逻辑seed需求，包括已登记/已完成基线，不是新增作业数量。先用server真实执行账本逐项复用；只有最终绑定的缺失成对对照需要训练。角色候选中若配方尚未固定，可先登记选择规则，不等待它来阻止广覆盖。
