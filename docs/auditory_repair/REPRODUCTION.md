> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Repair round: reproduction and evidence

The executed run snapshots and source bindings are authoritative. The workspace
is not the publication Git checkout. All numerical execution, including hashes,
tests and plotting, requires Slurm. Use a fresh output name for every execution;
never overwrite immutable outputs. The raw dataset remains read-only.

## Current analytical artifacts

| Component | Authoritative output | Main job |
| --- | --- | --- |
| Corrected PTA values | private/auditory_repair/pta_007/candidate_covariates.csv | 999476 |
| PTA final summary and old-D formula assertion | results/auditory_repair/verification_001/pta_revalidated/ | final verifier |
| Expanded HA preparation | results/auditory_repair/ha_prepare_001/ | 999477 |
| All five HA targets and all 13 models | results/auditory_repair/ha_extended_001/ | 999479 |
| Clinical/quality/amplitude/kernel follow-up | results/auditory_repair/ha_mechanism_001/ | 999493 |
| Same-identity trial-budget reliability | results/auditory_repair/reliability_matched_001/ | 999489 |
| Original-cohort Phase 3 PTA replay | results/auditory_repair/phase3_replay_002/ | 999481 |
| Original-cohort legacy D PTA replay | results/auditory_repair/legacy_d_002/ | 999491 |
| CI/MFF source/measurement description | results/auditory_repair/ci_scope_001/ | 999466 |
| Final identity/DOB-audited MFF preparation | results/auditory_repair/ci_prepare_004/ | 999505 |
| Age/source/technical-adjusted mixed-MFF regression | results/auditory_repair/mff_archival_001/ | 999507 |
| Small paired-task/repeated-acquisition description | results/auditory_repair/pairs_003/ | 999516 |

The pta_007 numerical covariate table is correct; its source_row_changed_n summary
used string comparison. The final verifier rebuilds the summary with numeric row
comparison and verifies identical corrected table values. Keep pta_007 immutable.
CI preparation 001 lacked the derived age and contradiction hold; only 004 was
used for model fitting. Early attempts and summary repairs remain recorded.

## Entrypoints

Root runs use `slurm/auditory_repair_cpu.sbatch` and
`slurm/auditory_repair_followups.sbatch`. They set one-thread math libraries,
require `SLURM_JOB_ID`, preserve private logs, and snapshot sources. The private
`start.json` records exact arguments and input/config/source hashes. Main runs:

```
extended test --run contracts_001
extended prepare --run ha_prepare_001 --test-run contracts_001
extended experiment --run ha_extended_001 --input-run ha_prepare_001 --test-run contracts_001
extended legacy_phase3 --run phase3_replay_002
followups test --run followup_tests_001
followups quality --run ha_mechanism_001
followups ci --run mff_archival_001 --input-run ci_prepare_004
extended report --run verification_001
```

These are recorded subcommands, not shell commands to rerun in place. Submit the
appropriate sbatch entrypoint with a new run name and a precreated mode-0600 log.
Some delegated scripts bind the output version in their executed source; their
private snapshots are required for exact historical reproduction. D's executed
source manifest and separately verified snapshot are under legacy_d_002.

`followups.py` gates its unchanged numerical implementation against the first
passed follow-up tests. The second test run corrected only counting of the three
synthetic kernel solves and independently passed; both executions are charged.
The final source/report checks and aggregate regeneration fit no models.

## Scope and units

All target/bank comparisons are exploratory. Five repetitions do not increase
the independent candidate count. Intervals resample fixed per-identity OOF loss;
they are not full-pipeline resampling intervals. Positive means lower MAE for
the augmented model. Original clinical rows, exact dates, predictions, weights,
fold membership and feature arrays are private. Public outputs are aggregates.

Changing D support changes the deterministic fold balance. The paired historical
repair uses original folds and original fold-scoped encoder projections. A new
52-group D cohort with corrected folds requires fresh fold-scoped encoders;
reusing old projections under those new folds is not a valid shortcut.

The original F1/F2 clinical questions still have scale/date qualification limits.
F3 is cross-task clinical complementarity; F4 is future function conditional on
baseline. Their small descriptive tables do not establish those clinical claims.
No GPU was required, and no P100 was used. No automatic GitHub publication.
