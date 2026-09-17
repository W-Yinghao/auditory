> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Phase 1 outputs and reproducibility

Use [phase1_report.md](phase1_report.md) for interpretation and [PHASE1_MEASUREMENT_PROTOCOL.md](PHASE1_MEASUREMENT_PROTOCOL.md) for fixed rules. Outputs are local pseudonymized research artifacts, not a public data release.

| Current output | Contents | Slurm job |
|---|---|---:|
| `results/phase1_sources_001/` | All 93 sources, event timing, units, channel headers and independent readers | 995327 |
| `tests/test_phase1.py` plus earlier reader tests | 11 tests, including ear-reference saturation protection | 995358 |
| `results/phase1_smoke_002/` | HA/NH engineering run after reference protection | 995363 |
| `results/phase1_measure_smoke_002/` | End-to-end measurement engineering run | 995364 |
| `results/phase1_epochs_001/` | Full 93-record signal QC; 84 records with reconstructed epochs | 995365, array 0–7 |
| `results/phase1_measurements_001/` | Scores, precision, half comparisons and fixed sensitivities | 995367 |
| `results/phase1_final_001/` | Canonical annotation ledger, cohort flow and bookkeeping checks | 995380 |
| `results/phase1_diagnostics_001/` | Condition/cohort summaries, reference checks, SET timing and illustrations | 995390 |
| `results/phase1_similarity_002/` | Average similarity and 11 targeted trial-residual checks | 995396 |
| `results/phase1_delivery_001/` | Final counts, document links, 84-page waveform PDF and checksum snapshot | 995400 |

Smoke 001 and similarity 001 are superseded. Smoke 001 source mtimes were moved to private backups during finalization; original smoke checksums describe the pre-redaction version. Source data were unchanged. Some Slurm tasks allocate two CPUs even for a one-CPU request; requested resources and measured memory must not be confused.

## Per-record epoch packages

`results/phase1_epochs_001/<recording_id>/epochs.npz` contains arrays loadable with `numpy.load(..., allow_pickle=False)`:

| Key | Meaning |
|---|---|
| `data_uv` | All stored candidate epochs × 20 scalp channels × 176 samples; primary 0.1 Hz high-pass, average reference, baseline corrected |
| `roi_uv` | Epoch × 3 variants × 176 samples; Fz/Cz mean |
| `roi_variant_names` | Array order: hp01 average, hp05 average, hp01 ear reference |
| `times_s` | −0.2 through +0.5 s; event zero retained, 250 Hz |
| `accepted` | Boolean epoch × 3 threshold masks; order given by `acceptance_thresholds_uv` (150, 100, 200) |
| `codes`, `event_indices_1based`, `samples_0based`, `blocks` | Numerical condition, source annotation ordinal, raw signal sample and 30 s block |
| `channels`, `roi_channels`, `config_sha256` | Channel order and version evidence |

**Stored epochs include rejected trials.** Apply the mask explicitly; do not train on every saved row or attach candidate clinical labels as confirmed outcomes. Ear-reference arrays are retained for diagnostic inspection even when the measurement stage marks that entire record's ear-reference variant invalid. Use `trial_counts.csv` and feature status, not array existence, to determine supported measurements.

Baseline correction occurred at 1000 Hz before decimation; the mean of only the decimated baseline samples need not be numerically zero. No new filtering or per-epoch resampling is required to read the package.

`epoch_ledger.csv` in each record retains all source annotations, including non-target codes. Rejection reasons, original indices and sample coordinates link every saved or rejected epoch to its event. The nine held sources have channel QC and summary only. Source mtimes and verbose failures are private.

## Measurement tables

- `trial_counts.csv`: trials/time-block support for each record and variant; includes `invalid_reference_channels`.
- `features.csv`: fixed-window mean, IID SME, block-bootstrap SE/CI, condition, support and bootstrap status. `feature_status=measured` describes the mean; inspect `bootstrap_status` separately for uncertainty availability.
- `split_agreement.csv`: alternating time-block and early/late waveform correlation, RMSE and window differences. These are not person-level psychometric reliability coefficients.
- `trial_count_curves.csv`: per-record, equal-code-count, disjoint-block-half comparisons, including finite repetition counts.
- `sensitivity.csv`: paired score changes; threshold variants may have different trial masks, filter/reference variants use matched primary trials when valid.
- `results/phase1_final_001/epoch_ledger.csv`: all 83,202 annotations for the 84 epoched records; not 83,202 accepted EEG trials.
- `cohort_flow.csv`, `measurement_candidate_groups.csv`: record counts, candidate groups and repeated acquisition candidates, with no confirmed-visit inference.

Figures: `figures/phase1_measurements_001/measurement_overview.png`, `trial_count_curves.png`, and `record_waveforms.pdf` (all 84 records); additional reference and retention-stratified figures in `figures/phase1_diagnostics_001/`.

## Reproduction and next versions

The production configuration SHA256 is `316d03d5dd87f274e0fd5f777479e67b87a9bedd758f888e0dbf4f5dbfe1748c`. Production array shards save configuration and source-code snapshots; per-record epoch hashes and measurement output checksums are present. The finalization snapshot's 25 checksums were independently verified by diagnostics.

These scripts are snapshot stages with guarded output directories. For another run, use new output names and a new configuration if rules change. Do not rerun into an existing stage, change v1 thresholds after viewing results, or rerun downstream analyses against mismatched configuration hashes. Submit through the saved `slurm/11_...` to `slurm/19_...` entries with appropriate dependencies and new run arguments.
