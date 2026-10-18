# ALN3.4 completed main panels and numerical recovery — publish_031

This is the 2026-10-18 afternoon update to publish_030. Training and aggregation continue during publication. Each report and archive retains its snapshot time; completed main panels do not imply completion of all ALN3.4 extensions.

The TRUE_FULL panel is complete at 800/800. The additional-seed one-step subset is 400/400, with the full identity coverage shown in [the paired report](TRUE_FULL_PAIRED_EVIDENCE.md). Official ADDENDUM_11 aggregation completed in Slurm 1045980 at 13:28; its execution receipt is in `results/auditory_alignment_v3/publication_031/evidence/add11_final_receipt.json`. The paired report's generic instruction to run the official analysis predates that receipt. Both the exploratory same-access comparison and the frozen official roles remain available.

The production public auditory prior is complete at 1,154/1,154 new units. [Its final report](PUBLIC_PRIOR_RESULTS.md) includes 30 historical references separately, for 1,184/1,184 records, with no engineering exclusions. FIXC, rich PCA, production manifests and M12/M13 were already included in publish_030; this release adds the completed results without restarting that work.

## Numerical recovery and provenance

- Private current/time execution v2 completed 130/130 units. It explicitly reuses 26 compatible v1 completions; those are not 26 additional independent experiments or participants. The [correction note](aln34/PRIVATE_TIME_CALIBRATION_CORRECTION_20261018.md), versioned code, plan and full failed-case GPU receipt preserve the same objective and test separation. GPU 1045978 passed and exercised two numerical fallbacks. Original v1 failures and sources remain unchanged on the server; v1 and v2 aggregates have separate paths. The [v2 report](NEW_SCIENCE_RESULTS_V2.md) states its actual analysed coverage, which can lag production completion.
- Prior private leave-self-out calibration had a reproduction mismatch after moving a V100-trained source to an A100. An initial replay 1045971 selected the wrong V100 variant and stopped before evaluation. Corrected replay 1046236 used the original node42 / Tesla V100-PCIE-16GB. AUC, NLL and Brier differences were all zero under unchanged tolerances. The original failure was archived before the passing replay was promoted, and the remaining lane resumed. The receipt and routing script are included; no endpoint, model or participant was dropped.
- The current fleet uses coordinator v16 and evidence monitor v11. Private science v2 is the active successor; earlier orchestration copies remain historical. An already-completed prior worker was drained after a stale-file-handle loop. No scientific result follows from a scheduling repair.

## Reading the snapshot

[Unit archives](../../results/auditory_alignment_v3/unit_records/README.md) contain the authorized pseudonymous model outputs and per-member hashes. Their completed-record counts can exceed a report's coverage when the report was generated earlier. A lane record may bundle multiple evaluations; neither bundles nor seeds increase independent participant n. All original direct local and standalone foundation-model comparisons remain available.

The new runtime audit estimates only currently registered work, using saved full-production timings and explicit extrapolations. It is operational planning, not a confidence interval or promised finish time. Its per-lane worker-cap limitation is stated in `results/auditory_alignment_v3/publication_031/evidence/runtime_forecast_20261018.json`.

Server orchestration is exported under `scripts/auditory_alignment_v3/`, and server design notes under `docs/auditory_alignment_v3/aln34/`. Historical execution paths and frozen identities remain provenance. Publication-only private-storage placeholders retain their existing meaning; source and publication hashes are listed in [the release manifest](../../results/auditory_alignment_v3/publication_031/MANIFEST.tsv).

Private raw EEG/audio, acquisition and clinical source tables, names, identity mappings, model weights, runtime logs and checkpoint cleanup lists remain excluded. The archive-directory reorganisation is not part of this release. Previous valid weak, unfavorable and uncertain results are retained.
