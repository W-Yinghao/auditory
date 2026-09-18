> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# 原始说明文档的量表定义补充

F-series 定向核查重新读取了此前登记的两份 DOCX 正文及附属 Word XML。HA 数据说明文档的“问卷说明”部分确实包含以下定义。旧 `docs/source_document_review.md` 对这一部分的摘要不完整，因此不能再使用“本档案没有任何量表版本或评分说明”的笼统表述。

| 文档明示名称 | 文档明示评分 | 构念 |
|---|---|---|
| IT-MAIS | 每项 0–4，总分 40；百分比为总分/40×100 | 日常听觉行为 |
| CAP-II | 0–9，共 10 个有序等级 | 听觉能力分级 |
| MUSS | 10 项，每项 0–4；百分比为总分/40×100 | 日常言语使用 |
| SIR | 1–5，共 5 个有序等级 | 言语可懂度 |

同一文档的听力损失程度说明使用 500–4000 Hz 行为测听及 dB HL 分级。这是文档层面的单位背景，不能替代每一耳、每一频率、裸耳/助听条件与评估日期的记录。

仍需分开判断：定义是否存在、定义适用于哪些原表行、评估是否与 EEG 有可解释时间关系。HA 表的 IT-MAIS/MAIS 合并标题未逐行给出版本；CI 扩展表的百分比标题下出现 0–40 数值，不能仅凭 HA 文档把它们统一换算。文档中没有说明逐行问卷日期或问卷与 EEG 的时间间隔，也没有以同次访问说明消除该缺口。文件末尾的个人信息与联系信息没有进入本补充。

证据入口为 [document_evidence_002 汇总](../../results/auditory_fseries/document_evidence_002/summary.json)，原始定位、文本与哈希保留于对应 private 目录。Slurm 作业 999256 完成此版本。`document_evidence_001`（999252）的词项计数有效，但其预置的“未发现可提供版本的文字”解释没有依据；该解释由 002 明确更正，001 原输出保留。此处是文档证据修订，没有修改旧量表数值或任何既有科学结果。
