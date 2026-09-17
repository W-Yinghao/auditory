> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Source-Document Review (Probe 001)

Date: 2026-09-16

## Scope and evidence status

This review reads only the Slurm-generated schema/document artifacts under `private/probe_001/`, identified by anonymous `file_id`, plus the requested probe summary when available. No names, patient numbers, dates of birth, telephone numbers, or child-level rows are reproduced here. At review time, `results/probe_001/probe_summary.json` was not present, so the conclusions below are documentary/schema findings only. They are not validation of raw signal content, event alignment, or participant identity.

## Workbook structures and repetition clues

`file_8a9c2767bddf88cb1bc2531e0dd4ea00` contains ten EEG-result sheets: pure-tone and ba1ba4/bapa variants for normal-hearing, cochlear-implant, hearing-aid, and bimodal configurations. The small normal/hearing-aid sheets mainly have overall P1/MMN fields; CI sheets have standard/deviant P1 latency and amplitude plus MMN P1 latency and amplitude. The bimodal sheet has separate CI and CIHA result fields. Headers include assessment date, DOB, sometimes patient number, bad-point count, cooperation status, and notes.

`file_d4bd0c2924e725928f61c2756853cb38` repeats the same ten-sheet topology and nearly the same dimensions/headers as `file_8a9c2767bddf88cb1bc2531e0dd4ea00`. This is a structural duplicate clue, not evidence of additional acquisitions or children.

`file_225d0f1d5180f1dc47fb96cedbde60d7` repeats the EEG sheets but expands the CI/CI-related sheets with audiology and developmental fields: ABR/DPOAE/CMR/IAR-style measures, frequency-specific aided/unaided thresholds, developmental quotient/age fields, and CAP, SIR, IT-MAIS/MAIS, and MUSS. It should be treated as an expanded export/version until file provenance and row-level correspondence are established.

`file_e254c9a75c971ac7d4e76bf6df2b4030` contains four clinical sheets. Its headers document actual age in months, HA-use duration in months, ear-specific unaided thresholds at 500/1000/2000/4000 Hz, PTA variants, hearing-loss severity categories, aided thresholds/PTAs, CAP, SIR, IT-MAIS/MAIS (%), MUSS (%), daily wear duration, speech-training frequency/mode, and left/right channel counts. Some sheets repeat the same clinical fields with slightly different column sets, and the two training-frequency/mode groups appear duplicated in the widest sheet. These are schema-level repetition clues only; do not count them as independent assessments.

Units explicitly supported by headers/documentation are: age and device use in months; hearing thresholds/PTA in dB HL where stated; IT-MAIS/MAIS and MUSS as percentages; CAP and SIR as score fields; EEG P1 latency in milliseconds and amplitude in microvolts. The broad clinical workbook’s first sheet labels PTA without consistently repeating `dBHL`, so units and PTA calculation conventions require source confirmation. Daily wear duration has no unit in the schema.

## Experimental and preprocessing documentation

The document artifact `file_fb30d5c47a7336642835a336782da5c1` states that HA CAEP was recorded with a domestic NSM2 medical ERP system, using 32 saline electrodes placed according to the international 10–5 system, with impedance below 20 kΩ before testing. It describes pure tones: 800 Hz standard, 1200 Hz deviant, 200 ms duration, 500–700 ms interval, 80%/20% sequence proportions, approximately 13 minutes, E-Prime 2.0 presentation, a loudspeaker 1 m in front at both-ear height, and a sound-attenuated room below 30 dB SPL.

The same document states that the report tests MMN and presents standard, deviant, and difference traces at Fz; one report template contains latency in ms and amplitude in μV. This is a reporting/documentation statement, not evidence that those event labels, timing, or peaks are present and correctly aligned in the signal files. `file_08a60863dfa6ba33e6d21f368562af39.document.json` is a report-form artifact that names MMN/P300/N400 as possible report labels and gives an Fz latency/amplitude example; it does not document acquisition timing or preprocessing.

No reviewed document explicitly states device-on/device-off status during recording, unilateral/bilateral state for each record, manufacturer/processing mode, sound level in SPL/HL at the child, trigger-channel/event-code mapping, trigger delays, exact SOA distribution, or whether standard/deviant acoustics were otherwise matched. No reviewed document specifies filtering, referencing, bad-channel/bad-segment rules, artifact rejection, epoch windows, baseline correction, averaging, or preprocessing version. Therefore these items remain P0 verification requirements. The documents also do not establish that the reported MMN/difference is cortical rather than device- or stimulus-locked artifact.

## Required P0 handling

Use the anonymous `file_id` and a separate stable child/visit/acquisition mapping when reconciling exports. Deduplicate by internal provenance and row correspondence; do not add sheet row counts. Treat the 80/20 and 800/1200 descriptions as protocol hypotheses until event logs/triggers and signal timing agree. Record missing device state and undocumented preprocessing as unknown, not as presumed device-on or a standard pipeline. Any EEG feature analysis should report which records have a documentary definition versus a signal-verified definition.

