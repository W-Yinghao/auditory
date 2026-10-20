# S35_EPISODE_REPLICATION_S3407 v1 — source-seed replication of the pressure-100 local episode effect

2026-10-20, Claude Code, at the researcher's instruction to start all proposed next steps ("全部开始").
Written before any unit of this design ran. Exploratory; result-informed.

## Question

The complete S35_EPISODE_PRESSURE summary (1050758) found, on DTU with seed-3401 sources, that episode training
at pressure 100 beat ordinary training for the local (lag_local_tokens) model with native readout
(fixed target-20: U10 +0.034 [+0.012, +0.057], U30 +0.036 [+0.014, +0.059] bits/query; selected policies
+0.024 / +0.034), while CBpre native was slightly unfavourable and pressure 20 was null. Does the local
pressure-100 effect hold with independently trained seed-3407 sources?

## Units

DTU, local, NCE, pressure 100 only: the 10 seed-3407 `data_inner_v1` inner-person sources (5 subject × 2 content
folds) and their seed-3407 outer ALN32 baselines; all exist and are complete. 10 new units. Every frozen v1
method is reused unchanged through the `episode_lineage_v2` pattern (module paths swapped in the worker process):
ordinary vs episode with matched 100 encoder updates, rank-4 spatial adapter, target steps 0/5/20, U10 five
draws and U30, fixed-20 and independent inner-person selected policies, the same support/query geometry binding.

Declared limitation: the frozen v1 episode and target-fit sampling streams use fixed constants (3401+61000,
3401+62000+update, 3401+person+63000). They are kept, so the replicated factor is the independently trained
source model (seed 3407: different initialization and training stream), not the episode sampling stream.

## Analysis (declared now)

Same estimands as S35_SUPPORT_SUMMARY_v1.1 episode families, restricted to this cell: per person (DTU 44),
true-query NLL bits/query, native and unified readouts separately; U10 draws averaged, then content folds within
person; columns episode − ordinary, episode − source, ordinary − source at fixed target 20 for U10 and U30
(positive = first-named better), plus selected-episode − selected-ordinary. Intervals: identity bootstrap,
B = 4000, simultaneous across the family. Reported side by side with the seed-3401 values; no pooled claim beyond
two source seeds of one cohort. No performance gate; all results reported.

## Execution

Engineering smoke: one truncated unit (2 encoder updates, one person per stage). Production requires the passing
receipt bound to the plan hash. Runfill GPU under the 10-GPU cap via the fleet plugin; STORE under `/projects`.
