# ALN3.4 data axes and independent inner-person sources

Recorded 2026-10-17 before these executions or their results. Result-informed: the completed DTU true-full/L1 three-seed panel, the existing D risk analysis and private E/calibration diagnosis have been viewed. This is continuing experimentation, not an independent replication of unseen data.

## Bounded questions and reuse

The DTU CBraMod advantage warrants testing its dependence on fitting people, fitting sound content and optimization budget. The separate doubled-budget plan already addresses budget. Here vary people and content one at a time, sharing the already-completed full-data reference. CBraMod pretrained/random at 3e-4 and local L1 use seeds 3401/3407/3413. Representative REVE pretrained/random at 1e-5 use seed 3401. All five person folds and both content folds are retained: 440 new reduced-data fits and 110 reused full-data records. This is not an exhaustive architecture/loss/LR cross-product.

Fractions 0.25/0.5 are nested. Person subsets are stable SHA256-ranked prefixes within each hearing stratum of the outer-training people; ceil(fraction*n) keeps small strata represented. The ranking is fixed across architectures, initialization and training seeds. No held-out-person outcome enters it. Content subsets are stable ranked prefixes of original fitting content groups, not windows; no outer-test content enters them. The original early-stopping content remains fixed. The content axis therefore varies **fitting content**, not all sound access including validation. Person fractions apply to both fitting and early-stopping people. Actual identities, content groups and segment counts are frozen in the plan.

Fixed target coordinates for data curves reuse the full outer-training audio-statistics rule, sampled with the original seed+5; no held-out EEG is used to construct them. This is reduced EEG supervision with a common known-audio target interface, not reduced access to every training sound. Unified/native readout fitting uses only the selected training people and selected fitting segments plus the declared early-stopping segments. Removed fitting segments cannot re-enter through readout fitting. The sound target itself is never a decoder input.

Epoch horizons, optimizer and checkpoint rule remain those of the matched full-data source. Reducing data also reduces optimizer steps per epoch. Therefore these are fixed-epoch data-budget interventions, not isolated effects at fixed optimizer steps; actual steps/exposure are reported and the separate doubled-budget intervention is interpreted alongside them. No test performance selects fractions, seeds, horizons or reporting.

## Independent inner-person source models

New D/fusion development needs source encoders that have never fitted the development identities. Completed outer models cannot supply that guarantee. Register 150 additional DTU source fits: CBraMod and REVE pretrained/random, plus local L1, all three seeds and ten outer folds. For outer person fold s, the inner development fold is (s+1) mod 5. Both sets of identities are excluded from every encoder update, checkpoint selection, bandwidth fit, audio-statistics fit and readout fit. The other three folds retain their original fit/es content rule. No individual outcome determines this split.

The inner source's recorded development evaluation uses only the inner identities' original **early-stopping content**, relabelled solely inside that evaluation view. Outer test content is excluded, including its candidate pool, and outer-test people are never evaluated by this source-fit lane. The same inner source can be reused by adaptation and fusion. Actual downstream policy fitting/evaluation is a separate implementation and record; completion of these 150 fits alone is not completion of whole-pipeline nested evaluation.

The matched outer full-data sources remain the refit stage and the direct standalone baselines. Later development must include epoch zero, select using the appropriate task and support fraction, preserve the same query set, and retain all valid negative changes. No outer-test-driven fallback to the base is permitted. Existing obsolete D/C execution holds remain intact.

## Execution and interpretation

Independent immutable plan and ALN34S IDs; no edits to legacy trainer files or old IDs. GPU tasks run through Slurm runfill within the existing ten-GPU cap. Checkpoints use <private checkpoint storage>/auditory_alignment_v3/aln34_data_inner_v1 with private permissions and a workspace symlink. Production is admitted only after a short full-interface GPU smoke test; its metrics are engineering checks, not a performance threshold. Resume is inherited per epoch block. Failure records remain visible and do not count as successful units.

Report identity-paired seed-averaged differences, actual coverage, within-seed results and simultaneous intervals across the declared axis/configuration contrasts. Seeds and content folds never increase the number of independent people. REVE reduced-data curves are explicitly single-seed. Do not infer a general absence of auditory information from an unfavorable curve. These within-DTU interventions do not establish cross-dataset generality or causal neural mechanisms.
