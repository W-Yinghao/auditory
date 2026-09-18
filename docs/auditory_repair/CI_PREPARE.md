> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# CI/MFF archival cohort preparation

Final preparation run `ci_prepare_004` completed under Slurm job `999505` with
one CPU and a ten-minute allocation. Earlier preparation outputs `ci_prepare_001`
through `ci_prepare_003` are preserved; the final input snapshot and arrays are
under the `ci_prepare_004` run directory.

The selection rule is the earliest uniquely linked canonical timestamped EEG
record per candidate identity, selected before outcome or feature availability
filtering. Exact-name/same-day linkage and source-level identity evidence were
required. One candidate group was held because linked clinical rows contained
multiple parsed DOB values. No vendor DOB conflict, vendor name-overlap hold,
or unparsed-name identity hold remained among the selected groups. Multiple
linked rows with conflicting A/V/CAP/SIR values remain invalid through target
masks; no later source or last-row value replaces them.

The final private cohort contains 71 candidate groups. Its target masks have
38 valid literal A values, 38 valid literal V values, and 36 valid CAP and SIR
values. The selected source evidence categories are CI 8, NH 1, and unknown
62. The expanded CI evidence scope contributes 11 selected records; the
remaining 60 are mixed-MFF archive records. An unknown source label remains
unknown even when a separate history clue contributes to the expanded scope.

The registered CI clinical parser's alias table explicitly checks EEG date,
implant date, activation date, device state, and age-month fields, and emits
corresponding raw columns. The `phase3_ci_clinical_004` schema and field audit
report no matched recognized fields and zero populated rows for those fields
(DOB and assessment date are recognized and populated). This establishes that
the registered CI parse has no usable source-verified numeric duration or
explicit age field; it does not prove that the original workbook had no
nonstandard or unrecognized headings. A separate older HA workbook contains
age and HA-duration columns, but those fields were not merged into this CI/MFF
cohort.

Age is therefore derived only for 66 groups with one unique parsed DOB, using
the selected EEG record timestamp; five groups remain
`dob_absent_or_unparsed`. Clinical assessment dates are never used as EEG
timestamps. CI and HA duration remain NaN because no source-verified numeric
duration field is available in the registered CI parse.

The fixed bank is recorded in `feature_schema.json`: Z contains primary
`stad` main amplitude, late amplitude, and late-minus-main amplitude; Q
contains trial/retention, reliability, channel/ROI/sampling, and availability
features; C contains age and the two unavailable duration slots. Slope,
latency, and picked-peak substitutes were not added. NaNs and endpoint masks
are retained for the later training-fold imputation and target-specific fits.
No model fitting, unit normalization, or raw EEG read occurred in this run.

## Direct source-header audit

The saved Slurm source snapshot `private/phase3_ci_clinical_schema_001/schema.json`
was checked directly before deciding whether another workbook read was needed. It
contains the complete nonempty header inventory for all 10 source sheets (13 header
candidates, including the secondary header layout). No header in that inventory
identifies implant or surgery date, activation/power-on date, fitting/mapping date,
or a numeric CI/HA wearing or use duration. The only device-related strings in the
inventory are signal-feature headers such as CI/CIHA ba1ba4 measurements; they are
not device-history fields.

The inventory does contain generic note/remark and cooperation columns. These are
free-text clinical annotations, so any mention of wearing, fitting, surgery, or a
number of minutes cannot be promoted to a source-verified duration without a
registered field definition and unit. The preserved parser output independently
reports zero rows for its EEG, implant, activation, device-state, and age-month
aliases. Thus the conclusion is more specific than “the parser did not recognize a
field”: the complete saved source-header inventory has no dedicated nonstandard
device-history header available for numeric extraction. No new prep or model fit was
run; the cohort and masks above are unchanged. The separate HA workbook's explicit
age/HA-duration fields remain out of scope for this CI/MFF cohort.
