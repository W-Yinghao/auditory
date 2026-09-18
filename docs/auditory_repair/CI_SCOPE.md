> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# CI/MFF scope continuation: descriptive record summaries

Run `ci_scope_001` completed under Slurm job `999466`. It consumed the frozen
Phase 3 linkage, endpoint audit, and record-level measurement tables from
measurement job `995601` and qualification job `999272`. It did not read EEG
arrays, reprocess raw signals, compute new features, or fit a clinical
regression.

The expanded CI evidence scope contains 41 canonical records: 20 literal CI,
18 literal CIHA, and three records with explicit same-day clinical CI history
whose source label remains unknown. The all-canonical MFF scope contains 203
records: CI 20, CIHA 18, HA 3, NH 1, and unknown 161. Source labels remain
evidence classes and are not diagnoses or device-on states.

The exact literal endpoint summaries are in
`results/auditory_repair/ci_scope_001/endpoint_scope_summary.csv` and the
source-level value counts are in
`results/auditory_repair/ci_scope_001/endpoint_literal_value_distribution.csv`.
For the 41-record expanded scope, each endpoint has two unique numeric linked
sources with a primary `stad` feature: IT-MAIS/MAIS literal 40; MUSS 25–29;
CAP 5–7; SIR 3–4. For all 203 canonical records, unique numeric linked
sources are IT-MAIS/MAIS 46, MUSS 46, CAP 44, and SIR 44; corresponding
primary `stad` feature intersections are 45, 45, 43, and 43. Literal ranges
are IT-MAIS/MAIS 2–40, MUSS 0–40, CAP 0–7, and SIR 1–5. The percent headers,
literal 0–40 values, row scale/version, and functional assessment timing are
left unresolved. Two linked source records have conflicting values for each
endpoint in this source-level summary; this is separate from the prior
candidate identity row conflict counts.

Existing record features are summarized by scope and source evidence in
`record_feature_summary.csv`. Existing split reliability is in
`within_record_reliability_summary.csv`; paired event and primary/strict
within-record contrasts are in `paired_within_record_summary.csv`. In the
expanded scope, primary deviant-minus-standard feature contrasts have 39
record pairs, with median −0.678 µV in the main window and −0.345 µV in the
late window. Strict contrasts have 10 pairs, with medians −0.287 and −0.520
µV. These are record summaries, not child-level or causal effects. The
expanded scope includes only two records with unique numeric endpoint values,
so it is appropriate to preserve the descriptive trajectories and reliability
tables without treating them as a regression cohort.

The broader mixed MFF archive is technically large enough for a record-level
exploratory fit in original literal units, but it is not clinically qualified.
`mixed_mff_regression_feasibility.json` records the barriers: unresolved
percent-versus-0–40 units, endpoint version and functional-date role, mixed
source labels, and non-adjudicated identity links. No regression was fit in
this run. Any later exploratory fit would need to retain source-cohort strata,
original literal units, one source record per row, and the unresolved status in
its interpretation.

The aggregate outputs contain no names, dates, participant IDs, source IDs, or
private paths. Identifier-level endpoint evidence and input hashes are kept
under the private run directory.
