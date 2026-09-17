> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Clinical Table Audit Notes (Current: Clinical 003)

The preliminary clinical 001/002 attempts have been superseded by clinical 003. The current audit was completed in Slurm job `994974` (CPU, 1 core, 4 GB, 10 minutes); the earlier successful 002 job was `994966`.

Clinical 003 read the original workbook identified by `file_e254c9a75c971ac7d4e76bf6df2b4030` through the inventory path map. Excel merged ranges were used to fill group labels, and true worksheet row numbers were retained. The source workbook was read without saving or modifying it. The source SHA256 and workbook comparisons are in `results/clinical_003/clinical_003_summary.json`.

The primary table contains 95 records: HA 84 and NH 11. Group counts after confirmed merged-cell filling are NH 11, 0m 15, <6m 12, 12–24m 14, 25–36m 13, 37–60m 13, and >60m 17. Continuous HA duration from 0 through 60 months contains 67 records. Four anonymous source rows disagree between historical group label and continuous-duration stratum: worksheet rows 35, 39, 40, and 45.

Candidate identity handling uses the leading contiguous Han-character portion of each original name string. The result is 80 candidate clusters. Original strings and suffixes remain private; every cluster is a candidate only, and no identity or visit is confirmed. Date-like suffixes occur in 87 records and device-like suffixes in 81. These suffixes are label evidence only and must not be treated as confirmed visit dates, device state, or longitudinal ordering.

Scale summaries are stratified by HA/NH and separated into ordinal and percentage scales. CAP, SIR, IT-MAIS/MAIS, and MUSS values are present across the archival tables, so an “across-table scales absent” premise is not supported. CAP maxima are reported as observed maxima rather than theoretical ceilings. The daily-wear field is sparse and has no verified unit. Assessment-date coverage differs among workbook exports; dates and repeated records cannot be assumed to define matched visits.

The audit preserves duplicate PTA headers by source column number and keeps same-age/same-duration records. Cross-workbook overlap and SHA256 evidence, anonymized clean rows, and candidate-only mappings are retained in the corresponding `results/clinical_003/` and `private/clinical_003/` outputs. No raw files were changed, and no identity confirmation or EEG association/modeling was performed.
