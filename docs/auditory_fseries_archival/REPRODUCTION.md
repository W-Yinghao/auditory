> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Reproduction

Invoke `slurm/fseries_archival_cpu.sbatch` with precreated mode-0600 output logs under the mode-0700 private namespace. Do not run Python directly on a login node. Every run name must be fresh. Executed source and configuration snapshots are under each private run's `source/` directory.

Commands used after the bounded data probes:

```text
sbatch --time=00:10:00 --output=PRIVATE_LOG slurm/fseries_archival_cpu.sbatch test --run tests_001
sbatch --time=00:20:00 --output=PRIVATE_LOG slurm/fseries_archival_cpu.sbatch prepare --run prepare_001 --test-run tests_001
sbatch --time=00:40:00 --output=PRIVATE_LOG slurm/fseries_archival_cpu.sbatch fit --run screen_001 --test-run tests_001 --input-run prepare_001
sbatch --time=00:05:00 --output=PRIVATE_LOG slurm/fseries_archival_cpu.sbatch recover --run screen_recovery_001 --input-run screen_001
```

These identifiers now refer to occupied immutable runs: commands are documentation, not instructions to resubmit them. Recovery only accepts the specific final-receipt serialization failure, checks that all task/fold outputs exist, and performs zero model fits. New valid code handles NumPy scalar JSON serialization. The model/data sources are unchanged between tested, prepared, fitted and recovered runs.

The global private `fit_events.jsonl` uses an exclusive lock and enforces an 8,000-attempt budget across tests and fits. It counts a requested head before preprocessing, including failed attempts. Clinical-only candidates cached across model names count only once per actual fit. The bootstrap resamples saved out-of-fold losses, not model fits.

Final verification uses `report --run verification_003 --input-run screen_recovery_001` with 2 CPU, 8 GB and a 10-minute limit. Submit it on hold, register the actual job ID in `jobs.json`, then release it only after the shared ledger is visible. The verifier requires the current job in the ledger, so resource accounting includes verification itself. Earlier verification runs are retained; see `JOB_LEDGER.md`.

Preparation hashes the workbook, registered source/linkage tables and every consumed epoch archive. No raw EEG is reprocessed. The current data adapter never reads the mismatched historical PTA covariate table. Public artifacts contain aggregate values only; candidate identities, clinical rows, source paths, splits, predictions, fitted coefficients and detailed exceptions remain private.
