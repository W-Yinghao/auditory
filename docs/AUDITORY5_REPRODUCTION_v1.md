> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 v1 reproduction navigation

Final update: the previously queued final chain has completed. Start with [S4_final_001](../reports/auditory5_v1/S4_final_001/FIVE_IDEAS_SCREENING_REPORT.md) and [the final status note](AUDITORY5_FINAL_STATUS_v1.md). The interim/queued descriptions below are historical; do not submit duplicate workers or reuse their run names. The final report preserves support and numerical failures.

This is an execution map for a later researcher. It does not add a scientific result or authorize a new analysis. The governing design remains [`AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md`](../AUDITORY_FIVE_IDEAS_SERVER_PLAN_v1.md); the implementation decisions recorded before real outcomes are in [`AUDITORY5_EXECUTION_DECISIONS_v1.md`](AUDITORY5_EXECUTION_DECISIONS_v1.md).

## Frozen inputs and provenance

Use the immutable representation task list at `private/auditory5_v1/jobs/plan_001/plan.json` (90 tasks) and the frozen identity/split file at `private/auditory5_v1/splits/splits_001/folds.json`; `results/auditory5_v1/splits_001/` is the public support summary. The latest tested snapshot is `results/auditory5_v1/contracts_023/validation.json` (173 tests, status `PASS`; its `hard_gate_scope` is module contracts and does not by itself complete export/training integration). Earlier021/022 gates passed172/173 tests and remain intact. Existing source and output runs are read-only historical evidence.

The orchestration ledger is [`AUDITORY5_JOB_LEDGER.md`](AUDITORY5_JOB_LEDGER.md). It records completed, ongoing, cancelled and failed jobs, including the 90-task plan, the two-GPU/four-CPU concurrency policy, and preserved numerical failures. Keep failed or superseded runs under their original names; output directories are immutable and the code refuses overwrite by default.

The current aggregate is [`reports/auditory5_v1/S4_interim_002/FIVE_IDEAS_SCREENING_REPORT.md`](../reports/auditory5_v1/S4_interim_002/FIVE_IDEAS_SCREENING_REPORT.md), with route detail in the adjacent A–E reports. It is explicitly `IN_PROGRESS`: R_SIM work and prespecified controls remain pending, and C/E have unresolved implementation/support states. The 1,000-world synthetic validation has completed; it remains implementation validation and is not real-data evidence. `S4_final_001` has been queued as job995979 after execution audit995977; do not resubmit it or cite it as completed before its receipt exists.

Private source snapshots, candidate-level predictions, clinical rows, model weights, exact source paths and verbose logs remain under `private/` with restricted permissions. They must not be copied to reports, committed, or published. `/projects/EEG-foundation-model/auditory` remains read-only.

## Execution rules and entry points

All preflight, environment probes, tests, exports, training, controls and aggregation run inside Slurm jobs. Login-node actions are limited to reading files, preparing a new run name, checking scheduler state and submitting/cancelling the researcher’s own job. Use the verified environment from the site configuration; the current wrappers default to `/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python` and `configs/auditory5_v1.yaml`.

The main CLI parser in `auditory5/cli.py` exposes `preflight`, `build-manifest`, `build-splits`, `test-contracts`, `export-eeg`, `make-job-plan`, `run-job`, `aggregate` and `validate-release`. Since the current gate is `contracts_021`, pass the contract explicitly when the selected entry point accepts `--contracts` or `--contract-run`; do not silently assume a parser default is current.

The CPU wrapper is `slurm/auditory5_cpu.sbatch`; the GPU wrapper is `slurm/auditory5_gpu.sbatch`. Representation workers use `slurm/auditory5_worker.sbatch` or the array wrapper according to the ledger and fixed plan. The route and sensitivity parsers are `auditory5/route_runner.py` and `auditory5/control_runner.py`; both require a Slurm environment, a new `--run`, and preserve a frozen source snapshot.

## New immutable run templates

Replace every `*_002`/`S4_replay_001` value below with a new, unique alphanumeric underscore-only identifier. Do not reuse an existing run name. These are command shapes read from the parser definitions; they are templates only and have not been executed here.

Core route template (direct route entry point, CPU allocation):

```bash
sbatch --partition=CPU --cpus-per-task=2 --mem=8G --time=02:00:00 \
  --output=private/auditory5_v1/logs/auditory5-core-%j.log \
  --wrap='umask 077; export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2; cd /home/infres/yinwang/EEG_auditory && \
  AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory \
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory5.route_runner \
  --route A --run A_core_002 --split-run splits_001 \
  --plan private/auditory5_v1/jobs/plan_001/plan.json \
  --modes L0 R_SUP R_SIM R_RAND --contracts contracts_021'
```

Use the same shape for B, C, D or E after checking route-specific `--modes` and input support in the parser; C may additionally use `--c-linear-only`, and B learned modes must not mix `L0` with learned modes. A route run is a new immutable output, not an overwrite or in-place repair.

Controls template (A/B/D only; explicit completed core mapping is required for B/D):

```bash
sbatch --partition=CPU --cpus-per-task=2 --mem=8G --time=02:00:00 \
  --output=private/auditory5_v1/logs/auditory5-controls-%j.log \
  --wrap='umask 077; export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2; cd /home/infres/yinwang/EEG_auditory && \
  AUDITORY5_ROOT=/home/infres/yinwang/EEG_auditory \
  /home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -m auditory5.control_runner \
  --route A --run A_controls_002 --modes L0 R_SUP R_SIM R_RAND \
  --contracts contracts_021 --split-run splits_001 \
  --plan private/auditory5_v1/jobs/plan_001/plan.json'
```

For B or D, supply one `--core` argument followed by every mapping, for example `--core L0=B_L0_001 R_SUP=B_SUP_RAND_core_001` for those B modes. Use completed private route runs. For A, `--core` is not used; optional A smoke uses the parser’s `--outer-folds` argument. Keep control runs separate from their cores and retain all missing/failed controls in the later report.

The existing `slurm/auditory5_screen.sbatch` is the screening entry point. It takes a new screening run, a passed contract run, and an absolute per-run source-registry copy:

```bash
sbatch slurm/auditory5_screen.sbatch \
  S4_replay_001 contracts_023 /absolute/path/to/S4_replay_001_sources.yaml
```

This wrapper checks the passed contract snapshot, runs the screening snapshot, and produces the five-route report and plots. The CLI `aggregate` command is a separate aggregate-only operation and is not itself the S4 screening command.

For a new representation aggregate from the tested source, use `sbatch slurm/auditory5_aggregate.sbatch execution_replay_001 contracts_023`. A screening registry must then explicitly reference that execution run and the intended core/control runs. Missing files remain missing, not zero effects. The already queued final chain uses `execution_status_003` and an immutable copy of `configs/auditory5_screening_sources_v1.yaml`.

Before submitting any template, check `sbatch --help`, the relevant module parser text, available partition/account settings and the intended dependency gate. Use `afterok` job dependencies or an explicit PASS gate file; do not start a dependent stage based on elapsed time.

## What remains open

The interim report is not a final five-route verdict. Preserve the distinction between completed code, submitted jobs, synthetic controls, route cores, route controls and an actual scientific completion status. In particular, the current ledger says SIM representation work is ongoing, and the final `S4_final_001` plan/report has not been completed.
