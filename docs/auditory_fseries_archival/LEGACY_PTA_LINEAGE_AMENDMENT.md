> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Historical PTA linkage amendment

During the new archival F-series screen, the original HA workbook was read using the actual worksheet source row. The registered Phase 2 linkage constructs `C####` from that source row. The old `scripts/phase3_ha_covariates.py` instead constructs `C####` from a sequential count of nonempty rows. These keys are not interchangeable.

Slurm job 999420 compared all 57 old candidate records against direct worksheet-row lookup. All 57 had at least one discrepancy; 55 had differing source-row locations, 55 had different better-ear unaided PTA, and 47 had different better-ear aided PTA. The old entries and exact private differences remain preserved. Aggregate evidence is in `results/auditory_fseries_archival/legacy_lineage_001/mapping_summary.json`.

The present screen does not use the old PTA values. `auditory_fseries/data.py` uses the registered source-row key, checks the original name and four clinical fields against the prior clinical audit, and retains missing PTA for training-only imputation. Its production inputs are in the immutable `prepare_001` run.

Earlier PTA-adjusted results must not be treated as reliable adjusted evidence until a separately versioned correction is completed. The old Phase 3 PTA models are directly affected. `auditory5/manifest.py` consumes the old covariate table to construct `clinical_index.parquet`; `auditory5/splitting.py` uses clinical completeness for route D and includes D support in fold balancing. Consequently, effects on route D support, old balanced split assignments, and downstream experiments that reuse those splits/representations need to be assessed separately. The absence of a direct legacy-table reader in v3 does not establish absence of an indirect effect.

This amendment preserves historical results and failures; it does not recompute old representations or folds, or claim that every old finding reverses. The current 56-group screen provides correctly linked evidence for its own frozen archival estimand. Strict F1–F4 qualification remains limited by timing/version/clinical-support issues independently of this PTA error. Nothing has been pushed automatically.
