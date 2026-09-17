> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Analysis protocol draft — not yet frozen

Date: 2026-09-16. Target: IEEE JBHI or a comparable journal. This is an analysis proposal informed by the current audit, not a preregistration and not evidence that a publication is guaranteed. Historical clinical relationships were already explored in the restart packet.

Execution note: [Phase 2's separately frozen protocol](PHASE2_PROTOCOL.md) has now been executed for within-acquisition amplitude agreement and an explicitly limited archival-label feasibility experiment using MUSS and one fixed code1 amplitude. It is not a confirmed concurrent clinical study. The main index/feature/model results are in [phase2_report.md](phase2_report.md); later feature or model work cannot treat those 53 HA candidates as untouched validation. The formal question and unresolved clinical-validity gates below remain a draft.

## Proposed primary question

Does a reproducible auditory EEG measurement add information about **concurrent** everyday auditory or speech function beyond prespecified clinical variables in children using hearing devices?

The first practical experiment is measurement reliability in a traceable, timing-validated subset. Clinical incremental value follows only after participant, visit, scale version, and recording-state checks pass. HA is a candidate main branch; the expanded CI workbook means CI should no longer be dismissed as a branch without clinical outcomes.

## Required dataset lock

1. Establish a master participant table using source identity evidence, aliases, DOB consistency, and manual resolution of conflicts. Names and export-specific GUIDs alone do not establish independent children. Register cross-cohort overlap.
2. Select one acquisition/version per target analysis and document its parent signal and event sources. Preserve other versions for sensitivity analysis. MFF storage segments, averaged categories, vendor averages, and acquisition counts are distinct units.
3. Resolve BDF data/event start differences and acoustic trigger delay. Verify code-to-stimulus assignments. For MFF, retain original segmentation offsets and historical artifact status; assess their correctness independently.
4. Verify device on/off state, presentation level and ear, stimulus acoustics, age at EEG, and device-use definition. Resolve scale assessment time independently of the date embedded in the EEG/clinical row name.
5. Freeze eligibility using data availability and outcome-blinded technical rules. Inventory the full duration range; an analysis limited to 0–60 months requires a stated scientific justification. Do not remove repeated records as duplicates merely because age and duration coincide.

## Measurement study

- Reprocess from the earliest trustworthy continuous version when feasible. Define filters, reference, channel inclusion, boundaries, artifact handling, epoch interval, baseline, and minimum trials from stimulus timing and pediatric methodology, without inspecting EEG–scale relationships.
- Start with condition-specific waveform summaries and a small number of interpretable amplitude/latency features. Determine pediatric latency windows before outcome analysis. Do not assume a 100 ms adult peak.
- Estimate within-record uncertainty by resampling trials and assess reliability with time-block-aware split halves. Match or account for trial count, report feature failures as missing, and quantify their distribution across recording conditions.
- Evaluate device artifacts, reference channels, onset offsets, bad-channel treatment, preprocessing sensitivity, and whether condition effects could reflect acoustics. A successful decoder or a stimulus-locked average does not prove cortical origin.
- Report per-record estimates before group summaries. Weight children according to the estimand instead of allowing trial-rich children to dominate.

## Clinical question and validation

- Select a single primary outcome by construct and scoring validity before screening EEG associations. MUSS is a candidate for everyday speech use; IT-MAIS and MAIS must be distinguished before an auditory-function endpoint is selected. Preserve SIR's ordinal nature. CAP version and upper bound require confirmation.
- Define the index record using trustworthy assessment dates, or transparently use the smallest valid device-use duration if chronology cannot be recovered. This latter rule is not a confirmed first visit. Use repeats in prespecified cluster-aware sensitivity analyses.
- Compare a training-mean baseline, a clinical-only baseline, an EEG-only model, and clinical-plus-EEG using exactly the same children and outer folds. The clinical baseline should cover age, device-use duration, and a defined hearing/audibility measure with few degrees of freedom. Confirm estimability of recording-condition terms.
- Use child-grouped nested validation when choosing features or tuning models. Imputation, scaling, dimensionality reduction, outcome residualization, and feature selection belong inside training folds. Keep all visits, protocols, versions, and epochs of a child together. Check duplicate provenance before splitting.
- Prespecify the principal metric (e.g. paired change in MAE for a continuous percentage scale), confidence intervals, and secondary metrics. Resample children, not epochs, and distinguish fixed-OOF uncertainty from uncertainty that refits the complete workflow.
- Assess ceiling effects, limited common support, trial-count confounding, sensitivity to device-state uncertainty, and protocol/batch effects. Permutation tests must respect the child and temporal dependence structure and preserve covariate relationships when testing incremental information.

## When a complex model would be justified

A neural network or frozen EEG representation becomes a secondary method only if a defined measurement problem and credible participant-level validation warrant it. Thousands of epochs do not provide thousands of independent clinical labels. A new architecture without a strong clinical baseline, reliability evidence, and subject-level validation is not the proposed contribution. External pretraining and any public reference dataset require overlap checks and a clearly bounded transfer claim.

## Claims currently out of scope

Causal rehabilitation effects; prospective prognosis without actual future outcomes; normal developmental standards from the small NH reference group; an MMN-specific mechanism without the relevant controls; verified longitudinal trajectories from duration labels alone; or a cross-child claim from within-child trial splits.

## Source basis

The journal describes its remit at the intersection of information technology and health/biomedicine: [IEEE JBHI](https://www.embs.org/jbhi/articles/jbhi/). Our emphasis on clinical incremental value and validated measurement is a project-design judgment, not a stated acceptance rule. EEGLAB's official [data-structure documentation](https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html) distinguishes original events, epoch events, and their time units; the audit preserves these distinctions. The local references are reviewed separately in `reference_review.md`; this audit is not a complete current-literature novelty review.
