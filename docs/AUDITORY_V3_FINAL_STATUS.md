> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../PUBLICATION.md)。

# Auditory v3 final status

The requested v3 design and YAML have been executed. The authoritative aggregate is `reports/auditory_v3/final_002/V3_RESULTS.md`, with `results/auditory_v3/final_002/primary_results.csv`, `primary_effects.png`, `primary_effects.pdf`, resource accounting and identifier-scan receipts. Slurm997679 completed with `V3_EXECUTION_COMPLETE`. `final_001` is preserved; final_002 changes reporting/figure layout and includes the final interpretive documents, not model fits or scientific results.

P0_001 completed260/260heads; N2R_001 completed550/550heads. R3 completed15selection encoders,180selection heads,15final encoders and60final heads. All3packages have complete primary estimates and independent capabilityPASS, while all3scientific primary screens failed their advancement criteria. The analysis uses49safe identity groups,698frozen bags and5584unique trial members from the existing explored cohort.

| Packet | Primary gain | 95% identity bootstrap CI | Scientific status |
|---|---:|---|---|
| P0 | −0.001749788 bits/trial | [−0.007432838,0.003619029] | NO_DETECTABLE_COMPRESSION_PENALTY |
| N2R | −0.000843949 bits/bag | [−0.008416885,0.006606403] | NO_CONTROLLED_GAIN_ESTABLISHED |
| R3 | 0.034124750 bits/trial | [−0.031362724,0.098477156] | NO_ADDED_VALUE_OVER_SUPERVISION |

Read `docs/auditory_v3/SCIENTIFIC_DECISION_001.md` and the three packet result documents for interpretation. In R3, SUP/MATCH have roughly chance discrimination and CE about2.7; their performance is worse than the SIM/history/random baselines. These findings do not establish a clinical biomarker or a method advantage, and do not generalize this frozen P_MATCH experiment to every CI source in the dataset.

R3's successful source is `tests_R3_005/source`; all3objective smoke checks passed under A100. Native CUDA pooling's first-backward deterministic errors remain recorded, with parameter-free equivalent pooling and same-initial-state continuations. R3 scoring uses the separately tested `tests_R3_scoring_001/source` correction: stable logaddexp loss from saved finite logits. `R3_probe_selection_002` is the authoritative complete60-choice receipt, replacing the probability-rounding failure status of `R3_probe_selection_001` without any refitting. Final R3_001 retains both original probability artifacts and stable logit results privately. Do not rerun any completed encoder/head or overwrite any historical/source snapshot.

Global ledger:2357head optimizer attempts/3000,30formalencoder allocations/30,3synthetic allocations/3 plus3same-state recoveries. Conservative resource upper bounds are45.776111CPU core-hours/160 and8.3075GPU-hours/16, using full reservations whenever completed scheduler records expired. GPUhardware was A100; noP100. Knownidentifier scan:110textfiles,6429matched-population tokens,0matches. This is a bounded identifier check, not a claim to detect all possible free-text identifiers.

All v3 jobs are finished. Unrelated Slurm994815was left untouched. The publication checkout remains at reference main`eb24106`; no v3automatic GitHubpush occurred. See `docs/auditory_v3/REPRODUCTION.md`, `EXECUTION_DECISIONS.md` and `JOB_LEDGER.md` for immutable run/source mappings, numerical amendments, counts and complete failure history.
