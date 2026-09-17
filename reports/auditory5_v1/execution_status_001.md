> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../PUBLICATION.md).

# Auditory5 首轮执行状态

生成时间：2026-09-17T04:21:08.052131+00:00。这是运行记录，不是五路线最终结论。

已完成输入冻结、原始信号重新导出、身份连通组划分和五折冻结。HA 的全头/独立左右处理各保存59,997个完整epoch，保留拒绝标记与完整事件历史；合格数分别44,358和47,245。

支持人数：一般解码58，A 55，B 60（读出时仍检查共同支持），C 60，D 51。

表示任务完成 57/90，其中计划60个学习型编码器、30个L0/随机编码器任务。并发上限2 GPU/4 CPU作业；大数组受Slurm提交限额限制，改为固定worker顺序执行。

五路线各完成100次正向、100次阴性小型模拟。阴性误筛率A为2/100，其余四路线0/100；这不等于真实数据有效性证明。C在低SNR模拟中功效不足，保留该限制。

## 已得出的基线信息

- A，L0、55人：条件对比对应效应 T=0.0184，95%区间[-0.023194224533799566, 0.059939867178531676]；post−pre=0.0535，配对区间[0.006986029930170257, 0.09783533131860324]。背景调整后T=0.0471。独立重置滤波和额外历史/位置平衡仍待完成，状态INTERIM。
- B，L0_HISTORY、60人：强context以外的post增益 -0.00167 bits/trial，95%区间[-0.00260, -0.00075]，不支持0.01的初筛阈值。学习表征和其余预设诊断待完成。
- D，L0、51人、完整临床内外嵌套：临床基线MAE=6.555，C+visible=6.646，加入null=6.975。增益-0.329，95%区间[-0.591, -0.099]；当前为负向结果，不更换主终点。学习型模型和剩余预设诊断待完成。
- C：尚无完成的读出汇总，不能记为阴性或阳性。
- E：尚无完成的读出汇总，不能记为阴性或阳性。

E1：同布局bapa只有16个安全候选索引，低于20人门槛，SUPPORT_INSUFFICIENT。E0已有18条配对记录完成128通道、真实缺口保留、独立60s滤波块导出；16条达到每类40个试次。MFF不是全部CI，不由未知来源组推断诊断。

## 继续执行

GPU任务会继续产出每折独立的R_SUP/R_SIM及D内折模型。A/B/C/D的后续读出必须使用对应的冻结模型和身份边界；缺少预设控制的路线保持INTERIM/NEED_CONTROLS，不自动升级阳性判断。只在首轮完整判据支持后考虑预设的23/37种子，当前未扩展架构或临床终点。

所有逐人信息、模型、epoch、路径和详细日志保存在private/。本轮没有自动推送GitHub。既有Phase0–3结果及失败的开发/数值运行保持原样。

聚合表：results/auditory5_v1/execution_status_001/stimulus_decoding.csv；任务状态：results/auditory5_v1/execution_status_001/task_status.csv。
