> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 B learned-representation core v1

This extension reuses the frozen L0 B implementation's history eligibility,
common-support pruning, candidate thresholds, context basis, candidate/class
weights, EEG PCA, logistic C grid, temperature calibration and paired summaries.
The already observed negative L0 result does not change any rule or parameter.
`route_b.py` and its completed outputs remain unchanged.

The entry point is
`run(config, split_run, representation_plan, modes, output_dir)`.
`representation_plan` is the path to the immutable plan JSON (not a run name).
Only R_SIM, R_SUP and R_RAND are accepted; the existing L0 runner stays separate.
Each mode and outer fold reads its own `outer{fold}_all_{mode}` feature ledger,
task, completion and encoder checkpoint. Plan/config/split hashes, frozen source
snapshot hashes, original P1 summary hashes, checkpoint/scaler/metadata fit
scopes, 20 input channels, and 64-dimensional pre/post features are checked.
The complete accepted feature ledger must correspond one-to-one, in order, to
the row parquet and frozen per-record accepted counts and identity assignments.
Its copied history/provenance must also exactly match the accepted slice of the
original exported event ledger; comparing this slice never recomputes history.
The task must exclude every outer-test identity. Missing outputs give explicit
insufficient status; inconsistent provenance is an implementation failure.

The readout's training identities are exactly the declared outer training
partition, subject to the unchanged B support gate. The representation encoder
may have used only the general-eligible subset of that partition, as recorded
by the original representation task. Its fitted scalers must use the same
encoder-training set. No outer-test EEG is admitted to encoder or readout fitting.
The new history readout does not load stimulus probe pickles or clinical values.

Current trials require literal current=1, previous=1, known H=0/1 and accepted
current EEG. History is the stored complete pre-QC chain, never a chain rebuilt
from accepted trials. Previous post features are resolved by original
`previous_event_id` within the same record, segment, identity and earlier sample
position in the full accepted feature ledger. If the preceding EEG was rejected,
its feature is missing while the current H remains unchanged. The lookup never
substitutes a nearby accepted event or an event from another record.

For each outer fold, the main set runs the same five models: linear context,
strong context, strong context+pre, strong context+post, and strong
context+pre+post. A separate common subset with available previous EEG reruns all
five and adds strong context+previous post and strong context+previous post+
current post. All compared heads within an analysis set use identical train/test
trial IDs. The subset retains the main training gap-bin boundaries and repeats
only the previously frozen support checks. Its losses are not subtracted from
the full-set losses.

Pre and post each have 64 coordinates from the same fold-specific frozen
encoder. Their candidate-weighted EEG scaler and at-most-32-dimensional PCA are
fit separately from context, again within every inner training fold. Context
does not enter PCA. Three-fold grouped head tuning, C=[.01,.1,1,10] and bounded
[.25,4] temperature calibration reuse only inner OOF readout predictions. This
is **readout-only inner validation conditional on an outer-training encoder**:
the encoder is not refitted without each inner-validation group. This extension
claims outer inductive validation only, and does not alter D's stricter nested
encoder isolation. Different outer-fold coordinates are never pooled for fitting.

Private outputs retain per-fold selected feature copies, their original ledger
indices, original history rows, fitted readouts, encoder/readout scopes, input
hashes, raw/calibrated OOF probabilities and per-candidate CE. Public outputs
contain eligibility counts and fixed-OOF 2,000 candidate-cluster paired gains,
separately for every mode and analysis set. No individual IDs or feature arrays
are public. Negative gains are preserved. No performance threshold selects a
mode or changes the cohort, and no cross-mode score subtraction is introduced.

At least 20 held-out candidate groups are required in each main and previous-EEG
analysis, with both analysis sets completing every planned outer fold. Completed
requested cores have status `INTERIM_B_LEARNED_CORE_COMPLETE`; missing support
or representation outputs produce `INSUFFICIENT`. These are execution/support
states, never full-B positive scientific screens. Early/late windows, quality
sensitivity, within-candidate circular-shift diagnostics, replication seeds,
and residual/artifact interpretation remain pending. A previous-response control
alone cannot establish neural memory or Shannon conditional mutual information.

Every execution and test requires Slurm; this module neither submits jobs nor
changes upstream artifacts. All run paths must be new private destinations.
