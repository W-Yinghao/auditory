> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Corrected-cohort encoder retraining

All commands below are scheduler submissions from the project root, using
`slurm/auditory_retrain_cpu.sbatch` or `slurm/auditory_retrain_gpu.sbatch`.
These wrappers set the EEG environment, four CPU threads, private umask,
explicit dataset root and supported GPU partitions. Do not run Python locally.

The initial commands were `probe` and `prepare`. Preparation verifies the427
existing EEG export files and constructs the corrected manifest and all
outer/inner assignments before freezing code/configuration. It is intentionally
non-overwriting and must not be rerun into the completed plan directory.

The frozen plan is
`private/auditory_retrain_v1/jobs/plan_001/plan.json`.
Its `source/` is the runnable snapshot for all representation/core/control work.
Worker, task, core and controls commands automatically re-execute from that
snapshot and verify its hashes and frozen metadata. EEG sizes and modification
times are checked against the preparation receipts before each task; preparation
performed full SHA256 verification. Final verification must check saved outputs.

The two GPU commands were `worker --resource gpu --lane 0` and
`worker --resource gpu --lane 1`, each dependent on successful probe/preparation.
The CPU command was `worker --resource cpu`, dependent on preparation. Each
learned lane has ten SUP and ten SIM scopes. The CPU lane has five L0 scopes.
The `core` command depends on all three workers; `controls` depends on core.

The task lists are finite and disjoint. Each worker starts a separate process
per task to release arrays between scopes. A completed task is skipped only
after checking its plan and output hashes. If fitting completed but downstream
export/probing failed, a retry can restore that task's saved new encoder; it
does not rerun completed optimization. Exact task scope/configuration must
match. Preserve any failed attempt's log. Do not alter a frozen snapshot.

Clinical outputs retain individual records privately. The readout wrapper
counts all calls to the grouped clinical ridge predictor and records the Slurm
job, plan hash and count. Historical screening flags produced by the unchanged
route-D implementation are retained as historical fields only and never govern
this round's continuation or final interpretation.

The independent report/verification completed in Slurm999581 using
`slurm/auditory_retrain_audit.sbatch`. Its own runnable source snapshot is
`private/auditory_retrain_v1/reviews/verification_001/source/`; its completion
receipt binds the report SHA256. The auditor consumes saved predictions without
fitting models again. The preceding independent auditor preflight999580 checked
15 completed task receipts and rejected a deliberately invalid fitting scope.
Its snapshot and receipt are in `private/auditory_retrain_v1/audit_preflight_001/`.
Do not rerun completed fitting to regenerate reporting or accounting.

The report is `reports/auditory_retrain_v1/verification_001/REPORT.md`, with PDF
and PNG figures. Metrics and all contrasts are in the matching aggregate
verification directory. `INTERPRETATION.md` is a subsequent written reading of
these saved aggregates, not another experiment. Publication requires a separate
user instruction.
