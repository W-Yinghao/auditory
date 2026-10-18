# ALN3.4 completed science analyses and evening progress — publish_032

This release follows the 2026-10-18 afternoon publish_031 snapshot. It adds completed science analyses, later extension results, the evening runtime audit and a second matched-device reproduction recovery. Each result retains its generation time and actual paired coverage; registered extensions are still running.

## Completed analyses

The [fixed-model science v2 report](NEW_SCIENCE_RESULTS_V2.md), generated at 16:45 CEST, covers all 180 public content/time units and 130 private current/time units. The latter includes 26 explicitly reused compatible v1 completions. The [public-prior science report](PRIOR_SCIENCE_RESULTS.md), generated at 18:09, covers 300/300 frozen primary targets across all registered datasets and objectives, using representative seed 3401. Full matrices, group contrasts and developmental models remain in their aggregate JSONs; complete execution does not establish every contrast or a neural latency interpretation.

The already completed TRUE_FULL 800/800 panel, its official ADDENDUM_11 analysis and the public-prior 1,154 new units plus 30 historical references remain available from publish_031. Their scope and original controls are unchanged.

## Matched-device calibration recovery

Prior-private calibration unit `ALN3X_642554812e473fee` failed its original-score reproduction check on an A100 after a V100S source execution. The maximum AUC difference was 0.000111688 against the registered 0.0001 tolerance; NLL and Brier stayed within tolerance. CPU preflight 1046586 verified the frozen sources, plan and routing-only driver.

GPU replay 1046588 used node08 / Tesla V100S-PCIE-32GB and passed the unchanged checks: maximum AUC/NLL/Brier differences were 0, 2.22e-16 and 5.55e-17. The original failed outputs and hashes were preserved before promoting the passing result and relocating its stop marker. This is a numerical reproduction recovery, not a changed scientific endpoint. The remaining calibration lane resumed; its report states the snapshot coverage. The earlier V100-16GB recovery from publish_031 remains separate.

Receipts and the evening runtime inventory are under `results/auditory_alignment_v3/publication_032/evidence/`. The [evening progress note](aln34/EVENING_PROGRESS_20261018.md) preserves its original 19:59 pending status and appends the subsequent passing replay. Frozen experimental identities and failure provenance are retained.

## Reading later results

Private episode adaptation, private CBraMod factorial comparisons, attention transfer, inner-person selection, learning curves, longer budgets, CBraMod auditory continuation and fusion results are refreshed to their available snapshots. Intermediate families remain labelled intermediate. A report generated before the unit archive may have lower coverage; neither unit bundles, reused records nor seeds increase independent participant n.

The 19:59 runtime audit estimates 1,458 remaining registered execution units and 495.7 GPU hours centrally. This is an operational estimate with explicit extrapolations, not measured remaining wall time or a confidence interval. Per-lane worker caps, dependencies and queue waits matter; the estimate does not include future experiments or historical held executions.

The latest authorized model-output snapshot is described in the [unit archive README](../../results/auditory_alignment_v3/unit_records/README.md). New lane parts have release-specific names and per-member hashes; older release archives remain historical snapshots. The [publication manifest](../../results/auditory_alignment_v3/publication_032/MANIFEST.tsv) maps frozen source bytes to publication bytes, including established storage-path placeholders. Raw datasets, names, identity mappings, model weights, runtime logs and cleanup lists remain outside this release.

The large public-prior science aggregate uses compact JSON formatting in this publication. All parsed fields, values and array ordering are preserved; semantic equality and source/publication hashes are checked during the Slurm release build. The server analysis output is unchanged.
