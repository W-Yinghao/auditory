> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../PUBLICATION.md).

# F-series 阶段一状态

新 F1–F4 研究方案已阅读并进入执行。阶段一的 HA、CI/MFF、原始说明文档资格审计及路线汇总已完成。**这不等于四条预测路线已训练完成。** 当前状态为 `QUALIFICATION_COMPLETE_SUPPORT_INSUFFICIENT`，尚未启动临床模型、提取新 EEG 特征或计算 EEG—量表关联。

当前权威结果：

- [中文资格报告](../reports/auditory_fseries/STAGE1_QUALIFICATION_REPORT.md)
- [路线支持表](../results/auditory_fseries/qualification_final_001/route_support.csv)
- [终点定义与分布表](../results/auditory_fseries/qualification_final_001/endpoint_definitions.csv)
- [原说明文档补充](auditory_fseries/SOURCE_DOCUMENT_AMENDMENT_001.md)
- [F1/F2 最小实验设计](auditory_fseries/F1_F2_MINIMAL_EXPERIMENT_DRAFT.md)
- [完整执行记录](auditory_fseries/JOB_LEDGER.md)

HA：84 条量表行、69 个候选身份组，各主要量表均有数值；量表评估日期和 EEG 间隔仍不明确。MFF：203 份来源、104 条相关临床行、87 个候选身份组，不能整体称为 CI。9 对同日纯音—bapa 候选对只有 2 对关联量表数值；8 个多日期终点序列只涉及 2 个身份组，尚未确认真实功能随访。原说明文档中的 IT-MAIS、CAP-II、MUSS、SIR 定义已补回，不能再笼统说没有任何版本说明；逐行适用与时间关系仍需区分。

HA 当前运行为 `ha_qualification_002`/999281；MFF 为 `ci_qualification_001`/999272，附 999283 的字面值与身份计数补充；文档为 `document_evidence_002`/999256；总表为 `qualification_final_001`/999293。前期软件失败和旧文档解释错误均保留。交付核验以 `verification_002` 的 PASS 回执为准，首次核验的日志权限异常已记录。

各路线按原方案的支持不足条件暂停模型阶段，不把资格不足写成 EEG 阴性，不为继续训练而补造日期/版本或混合量表。未来继续时先读取上述证据；不要重复完成的审计或把旧 49/53 人子集自动转作新研究队列。全部原始数据和旧科学结果保持不变，本轮未 push GitHub。执行记录披露了辅助代理两次本地调试例外；正式统计与验证通过 Slurm，未使用 GPU。
