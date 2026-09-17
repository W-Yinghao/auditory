> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# CI/MFF scientific summary rules

Recorded before the full MFF measurement summaries are available; the four technical smoke records have been seen. All results remain exploratory.

- Retain all 203 canonical source records in record-level quality and decoder availability tables. Literal CI/CIHA/NH/HA labels are source metadata, not independently verified diagnoses or device-on evidence.
- Report event discrimination separately for each literal deviant code. Average five temporal-fold AUCs only when every fold has sufficient support. Compare prestimulus, 50–250 ms and 250–450 ms windows on the same record/code support. Prestimulus is a diagnostic reference, not a clean causal null under zero-phase filtering and possible adaptation.
- Candidate-level descriptive indices require one exact full-pinyin candidate, same-calendar-day clinical/source linkage and no alternative exact-name participant. Select the earliest recorded acquisition for each candidate / literal source group / known task before signal-quality or decoder availability gates; do not replace failed indices. Names and dates remain private. Pinyin homophones and imperfect clinical identities remain a limitation.
- Within-day task contrasts require the same candidate and source calendar day. Select the earliest source per task on that day, then select the earliest day containing both known tasks; never combine different days or substitute a later higher-quality recording. Unknown task labels do not establish a task pair.
- Configuration contrasts additionally require the same known task, day and candidate, with explicit CI and CIHA labels. These are source-label comparisons, not verified device-state effects.
- Summarize pairwise AUC differences descriptively. These small, selected candidate sets do not support a causal or language-specific interpretation. No post-hoc responder threshold, outcome-based record selection or uncorrected multiple hypothesis claims will be introduced.
- The CI workbook MUSS column is labeled percent but contains values 0–40. Do not rescale or pool with HA percentage scores, and do not train CI clinical models until score construction and unique visit-level values are supported by the archive.
