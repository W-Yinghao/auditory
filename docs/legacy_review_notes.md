> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Legacy Review Notes for Phase 0

Date: 2026-09-16

## Status and scope

This memo records **historical baselines and design cautions** from the restart packet. It is not a verification of the server, raw EEG, the original clinical workbook, or the eventual analysis dataset. The supplied synchronization bundle contained 61 files, passed CRC validation, and contained no raw EEG (only placeholder files under `data/raw/`). The historical aggregates were recomputed from anonymized derived clinical manifests. “Reproducible” therefore means reproducible from those derived tables and legacy calculations; it does not establish source-table correctness, EEG availability, matching, device state, or cortical origin.

The current publication target is IEEE JBHI. Any older instruction to leave the journal unspecified is superseded by that user-specified target; journal positioning must still follow the evidence obtained in P0/P1.

## Historical numerical baselines to reconcile

These numbers are audit anchors, not current sample-size claims:

| Historical scope or check | Records / children or result |
|---|---:|
| Cohort B entire derived table | 95 / 80 |
| HA and NH subsets | HA 84 / 69; NH 11 / 11 |
| HA with 0–60 months device use | 67 / 55 |
| Complete HA 0–60-month index records (MUSS, age, unaided PTA) | 54 |
| Repeated HA records | 13 children / 28 records overall; 10 / 22 within 0–60 months |
| Additional same-child age-duration records | 2; duplicate or same-day retest unresolved |
| HA duration strata across all records | 0: 15; (0,6): 9; [6,12): 3; [12,24]: 13; (24,36]: 14; (36,60]: 13; >60: 17 |

The legacy Cohort A slide counts condition entries, not independent children: NH pure tone/syllable/lexical tone = 14/6/1; CI = 24/16/16; HA row = 1/1/1, with 15 bimodal entries. Bimodal denotes a CI in one ear plus HA in the other and is not established by the table as a separate child group. These entries must be reconciled against actual child, visit, acquisition, stimulus, and device-configuration records.

Historical association/model anchors include Spearman age-versus-duration rho 0.266 for 55 HA index children in 0–60 months (0.422 across all HA records); no negative age-minus-duration values were found in the derived table. For 54 complete index records, MUSS R² was 0.677 with duration alone, 0.774 after adding age, 0.788 after unaided PTA, and 0.828 with the additional log-duration term; reported LOO R² for the full model was 0.778, falling to 0.631 after excluding the 0-month group (39 complete records). Duration and log-duration correlated about 0.914 (VIFs about 6.39 and 6.16), and six fitted MUSS values exceeded the maximum of 100. These are exploratory, outcome-informed historical calculations, not confirmatory performance estimates.

Historical residual checks found approximately 0.527 exploratory ICC, adjusted MUSS–IT-MAIS residual Spearman rho about 0.673 (n=54), and daily-wear residual rho about 0.627 from only 15 records / 11 children in the 0–60-month scope. The daily-wear field’s source, units, reporting method, and conversion remain unverified. The original residual and p-value calculations must not be treated as independent validation or evidence of a stable neural trait.

## Most likely research-design traps

1. **Counting records, epochs, exports, or condition entries as children.** Repeated records must stay clustered by anonymized child; duplicate exports and companion files must be collapsed to acquisition provenance.
2. **Calling derived `visit_id` or duration order a true longitudinal timeline.** File order and modification time do not establish visit dates. A shortest-duration index record is only a prespecified index rule when dates are unavailable.
3. **Treating age, device-use duration, and PTA as independent “clocks.”** PTA is a hearing-threshold measure. Age, elapsed use, and implied age at first fitting can be algebraically dependent; duration and log-duration are one effect block.
4. **Interpreting observational associations causally.** Age, age at fitting, residual hearing, device state, protocol, acquisition batch, audibility, and selection may be confounded. Excluding 0-month records does not solve this globally.
5. **Inferring paradigm semantics from event frequencies.** Frequent event codes do not prove standard/deviant labels or MMN; verify triggers, annotations, event files, delays, SOA, probabilities, and acoustic differences before naming a response or fixing a window.
6. **Mistaking device artifacts for cortex.** CI artifacts can be stimulus locked; classification, a peak, or a difference wave alone cannot establish cortical information. Check device-state channels, timing, preprocessing, and non-target controls.
7. **Selecting peaks/features/endpoints using clinical outcomes.** Define measurement windows and identifiability from outcome-blinded QC evidence. Report valid-trial counts, reliability, and missingness; never encode an unextractable feature as zero.
8. **Inflating generalization through leakage.** All visits and epochs for a child belong to one split. Fit imputation, scaling, feature selection, nonlinear forms, outcome-driven windows, and tuning inside training folds; use nested grouped validation for prediction.
9. **Over-reading nulls, p-values, or residuals.** A nonsignificant result is imprecision, not proof of no effect. One significant versus one nonsignificant effect is not a test of their difference. Residual correlations inherit model, rater, ceiling, and repeated-measure uncertainty.
10. **Reusing legacy labels and scripts mechanically.** Four historical group labels disagree with continuous duration. The omitted 6–11-month display stratum contains one index child. Legacy eligibility flags and SIR folds must not define the new task; event parsing, companion-file handling, de-identification, and resource controls require correction.

## Phase 0 evidence gates

Proceed to P1 only for a branch with all of the following documented:

- **Traceable inventory:** every candidate recording has format-aware companion-file checks, provenance (raw/preprocessed/epoched/average/export), duplicate handling, readable status, and a safe read plan. Headers and bounded segments are preferred initially.
- **Identity and visit evidence:** stable anonymized child IDs are separated from visit and acquisition IDs; each match is marked confirmed, pending, or unmatched using joint evidence. Cohort overlap and repeated records are explicitly checked without exposing identifying information.
- **Interpretable conditions:** stimulus definitions, event source and timing, standard/deviant status where applicable, presentation ear, sound level units, SOA, and device state are supported by records rather than frequency assumptions.
- **Confounding inventory:** device configuration, manufacturer/processing mode, aided versus unaided state, age, duration definitions, hearing measures, channel/reference setup, sampling rate, acquisition batch, and preprocessing version are recorded, with inseparable factors disclosed.
- **Signal evidence:** units, saturation/flat signals, bad channels, reference, mains/device artifacts, boundaries, event alignment, and valid trial counts are checked across representative protocols. “Readable” and “usable for this question” are separate statuses.
- **Measurement readiness:** candidate features have outcome-blinded definitions, interpretable child/record waveforms, reliability or split-half evidence, error estimates, and explicit missingness/non-identifiability rules. No clinical outcome is used to decide data quality.
- **Analysis readiness:** one primary question, EEG measure, outcome, adjustment set, estimand, child-level inclusion rule, and validation plan are written before testing EEG–outcome associations. Any 0–60-month restriction and >60-month records are reported and justified, not silently filtered.

If a gate fails, retain a bounded descriptive or feasibility branch and document the exact missing evidence; do not force a causal, longitudinal, normative, or cross-child prediction claim. Historical numbers in this memo should be replaced or annotated with server-derived values after P0 reconciliation.

