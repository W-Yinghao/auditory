> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Archival F-series execution ledger

All computation, environment/schema probes, tests, feature extraction, model fits, bootstrap and plots ran through Slurm. Raw sources were read only. Every job and its requested resource limit is listed in `jobs.json`; the canceled dependent probe is conservatively included in the requested-resource upper bound. No GPU was requested.

The data agent's preliminary tests 999403/999409 failed at import collection because the test package shadowed the implementation package. Probe 999404 was canceled before execution. Subsequent data/schema checks passed. Combined contract job 999417 passed 15 tests; its 98 attempted synthetic heads are included in the global fit ledger.

Preparation 999418 read the full 93-record source index, retained 61 technically eligible earliest HA indices, 57 unique archived clinical links and 56 records with at least 64 primary accepted epochs. It saved original-source and epoch hashes privately.

Model job 999419 completed all 5,301 production head attempts and persisted all 120 task/fold/model artifacts, 1,344 identity/model/task predictions and aggregate metrics. Writing the final JSON receipt failed because a NumPy integer was not serialized. This was an engineering failure after fitting, not an incomplete-fold scientific result. No model was retrained. Job 999421 checked the complete saved artifacts, recomputed MAE and recovered the summary in `screen_recovery_001`. Original failure and source snapshots remain in `screen_001`.

The global ledger contains 5,399 attempted heads, including tests and failures, within the 8,000 limit. `screen_recovery_001` is the authoritative complete screen receipt. Its private recovery binding points back to the actual production source snapshot. The later verification report recomputes all metrics and checks inputs, identity isolation, resources and privacy.

Job 999420 separately confirmed the historical PTA row-mapping error. See `LEGACY_PTA_LINEAGE_AMENDMENT.md`. This does not change the current frozen source-row mapping or permit reinterpretation of earlier PTA-adjusted results as valid.

Slurm's accounting database was unavailable during this round. Requested resource limits and CLI elapsed-time receipts are retained; requested core-hour upper bounds must not be described as measured CPU use. No automatic GitHub publication was performed.

Verifier 999424 completed metric recomputation, input hashing and plotting, then rejected pytest's internal `...current` symlink although its resolved target was a mode-0700 synthetic fixture directory within the private namespace. The verifier was corrected to require private containment and private target permissions; no scientific artifact was changed and no fits were added. Verification 999426 uses the fresh `verification_002` run. The first failure is preserved.

Verification 999426 passed the scientific, provenance and privacy checks. Its accounting figure included the preceding jobs but omitted itself: the compute node read the job ledger before the post-submission append became visible. Final verifier 999428 is submitted on hold, registered first, and released after the shared file update; it requires its own job ID in the ledger. `verification_003` is the final delivery receipt, including every registered job in the resource upper bound. No model fits are repeated.

Final result: 999428 PASS. All 24 task/model combinations, source hashes, complete OOF predictions, identity separation and private/public artifact checks passed. Requested-resource upper bound is 4.250 CPU core-hours including all registered probes, failures, the canceled dependency and verification jobs; 0 GPU-hours. The global head-attempt count remains 5,399. No round jobs remain queued or running; unrelated job 994815 was left untouched.
