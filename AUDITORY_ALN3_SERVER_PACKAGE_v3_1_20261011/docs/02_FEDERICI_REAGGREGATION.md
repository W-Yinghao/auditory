# 02 · Federici实体、身份与人口学修正（v3.1替代旧§02）

## 已纠正的前提

上一版将loader里相同文件编号的HC与HC-v关联过度当成同儿童事实。这一假设撤回。根据用户转发的server原始元数据核对，HC-v有自己的`1vocod…16vocod`代码、年龄与性别。默认作为独立参与者组，不按同编号并入HC，不按年龄/性别相似推断同人。

Artifact是**一个phantom、九次会话**。这些记录独立于人类预测和人类统计；它们可说明这个对象的不同会话表现，不支持9个phantom总体的推断。

## 1. 正确的出口清单

私有清单字段：
`dataset,record_uid,subject_uid,condition,entity_type,identity_source,source_hash,age_source,demographic_hash,split_contract_hash`。

HC、CI、HC-v各自使用来自元数据的命名空间。人口学按来源表逐行连接，不继承HC同编号的年龄。不能依据解码分数、EEG相似度或性别年龄组合猜身份。

来自server的结论作为本次依据；在接入回执保存元数据文件hash、字段和脚本即可，不需要等另一轮人工确认才继续其他模块。存在明确未知的身份留unknown单列。

## 2. 复用ALN2而非一律重训

旧代码强迫不同儿童同fold，并不因此造成同人跨fold泄漏。若仅如此，旧预测继续作为原训练清单与原fold下的预测，分开正确身份后重汇总。

旧HC-v年龄关联无效，使用正确年龄重算。另检查年龄是否实际进入模型训练、采样、teacher选择或调参；若进入，只重跑受影响依赖项。没有参与这些步骤的模型不重训。

新ALN3训练使用纠正的subject_uid。为连接旧比较，可保留旧record到fold分配，但身份含义必须更新；如需重新分折则建立新split版本，不冒充同一比较。

## 3. 汇总输出

每行规范长表：
`dataset,config_id,seed,subject_uid,record_uid,condition,entity_type,identity_source,subject_fold,content_fold,unit_id,metric,value`。
一次导出只对应一个split合同。失败单元在状态账本报告，不能用NaN行静默删除。

1. HC、CI、HC-v分别报告真实人数、记录数、内容数和性能；默认不生成人类与phantom混合的总分。
2. HC−HC-v、CI−HC作为独立组差，用真实参与者做组内重抽；保持方法与候选一致。HC-v不是同儿童声码器干预，不作个体因果效应。
3. 同一模型内的预训练−随机、局部−旧结构仍可按**同一测试儿童**配对。不要把“组间独立”误解成所有模型对比都不能配对。
4. 同phantom的会话保留每次分数、均值和范围。默认不提供基于n=1的总体置信区间；seed/fold只反映模型改变，不增加phantom实体。
5. 预测量/年龄分析按正确元数据单独版本化。所有预定主要模型都重算，不只挑有利模型。

## 4. 代码行为

本包`reaggregate_federici.py`默认产生独立组差，不再调用HC/HC-v配对输出。参考validator拒绝Federici中的HC/HC-v共享subject_uid，要求Artifact只含一个有来源的phantom ID。这些是当前数据的已知修正，不是所有未来资料的通用规律。

若以后原始来源明确证明某两个条件同人，应单独修改身份政策并记录证据，不能通过跳过检查掩盖变化。人类同一subject仍须落在同一outer fold；不同split的结果分开文件。

## 5. 并行与交付

复用原候选和原预测先做CPU重汇总；候选或校准要变则另做evaluation-only并对所有比较一致处理。缺少逐试次分数时，从旧checkpoint补短推理并写新文件，不重训。

输出：`FEDERICI_IDENTITY_CORRECTION.md`、`summary_by_condition.json`、`independent_group_contrasts.json`、`phantom_sessions.json`、旧新数值/年龄影响表。身份、年龄、逐人预测留private。

该修正只阻塞用到错误Federici清单的训练或统计，不阻塞FAU、DTU或私有BDF。
