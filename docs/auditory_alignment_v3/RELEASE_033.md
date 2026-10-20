# publish_033 — ALN3.5 completed comparisons, first readout of the science aggregates, Claude Code handover

Researcher instruction 2026-10-20: "push到github上". Established publication scope (everything except the private
dataset itself, names and identity mappings; no weights, run logs or storage-cleanup tooling). This is a snapshot of
continuing experiments, not a declaration that the registered work is complete.

## What is new since publish_032 (2026-10-18 20:08–20:11 CEST)

- **ALN3.5 package** `AUDITORY_ALN3_SERVER_PACKAGE_v3_5_20261018` (zip and byte-identical extracted copy) and the
  standalone ALN3.4 full-experiment document.
- **ALN3.5 code, tests and Slurm entries**: `auditory_alignment_v3/aln35/`, `tests/auditory_alignment_v3/aln35/`,
  `slurm/aln35_*.sbatch`; orchestration copies (fleet v2/v3, evidence service, plugin registration, bindings) under
  `scripts/auditory_alignment_v3/aln35/`; intake receipts under `docs/auditory_alignment_v3/aln35/ops/`.
- **Completed ALN3.5 comparisons**: APwrong (`aln35/AP_WRONG_RESULTS_V2.md`), fusion attribution (44 people, 3 seeds),
  attention order, bridge B×T factors, CB auditory state, history interface, paired science and group effects,
  private pre-input correction, and the complete support / episode-pressure / matched-updates / true-risk summary
  (job 1050758; `results/auditory_alignment_v3/aln35/support_summary_v1/`).
- **First interpretation of completed aggregates** (no refit):
  [1050758 interpretation](aln35/SUPPORT_EPISODE_SELECTION_INTERPRETATION.md),
  [content/time, private current/time and prior science](aln35/SCIENCE_V2_PRIOR_INTERPRETATION.md) with readouts
  [science v2](aln35/SCIENCE_V2_READOUT.md) and [prior science](aln35/PRIOR_SCIENCE_READOUT.md); every cell is in
  `results/auditory_alignment_v3/aln35/science_readout_v1/`. The private C10/H10 calibration loss is traced to
  temperature selection under a shifted support class mix (`results/auditory_alignment_v3/aln35/support_prior_shift_check_v1/`).
- **Refreshed ALN3.4 extension results** (attention transfer, breadth, budget/data curves interim, CB auditory
  continuation, CS episode, strong fusion, private episode/factorial, prior diagnostics) with their own generation
  times and coverage.
- **Project review** [2026-10-20](../PROJECT_PROGRESS_REVIEW_20261020.md).
- **Two bounded new lanes, registered and running** (designs frozen before any result):
  [S35_CBAUD_PEOPLE](aln35/CBAUD_PEOPLE_DESIGN.md) — auditory-continued vs direct CBraMod start at 25%/50% source
  people (20 units) — and [S35_EPISODE_REPLICATION_S3407](aln35/EPISODE_REPLICATION_S3407_DESIGN.md) (10 units).
  Both engineering probes passed; production results are not in this release.
- **Operations**: the GPU coordinator is fleet v3 (`scripts/auditory_alignment_v3/aln35/maintain_fleet_v3.py`):
  DTU budget/curves base concurrency 3, committed (running + pending) runfill cap of 10 GPUs, workers never exceed
  unfinished units. Receipt in `scripts/auditory_alignment_v3/aln35/fleet_v3_20261020/`.

## Lane records

`results/auditory_alignment_v3/unit_records/lanes_033_*.tar.gz` with `LANES_MANIFEST_033.tsv`: ALN3.4 lane records
not already published byte-identically in publish_030/031/032, plus all completed ALN3.5 lane records (prefix
`aln35/`). Main-runner archives are unchanged since publish_032 (8,719 records). Records, releases and seeds do not
increase independent participant n.

## Still running at this snapshot

DTU learning budget and data curves, breadth budget and curves (ALN3.4 tails), and the two new lanes above.

## Not published

Private raw data, file/event/clinical source tables, identity mappings, names/contact details, server-only support
geometry bindings, model weights, run logs, storage-cleanup tools/lists, agent handoff notes and their audit scripts.
Source and publication hashes: `results/auditory_alignment_v3/publication_033/MANIFEST.tsv`.
