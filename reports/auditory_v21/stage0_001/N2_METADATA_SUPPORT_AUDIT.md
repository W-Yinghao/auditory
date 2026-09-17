# N2 v2.1 Stage 0 metadata support audit

This is an outcome-blind metadata audit of the immutable saved k=8 bags and complete event history. It opened no EEG feature array, fit no head, and read no prediction.

## Frozen bag and source constraints

Saved bag denominator: 3307; saved member-row denominator: 26456. Bad k=8 bags: 0; bad multi-block bags: 0; bad history alignment: 0; bags lacking the original four class×half record support: 0.
Source-group denominator: 228; groups below the frozen two-bag quota: 12; groups below the frozen three-source-block requirement: 1.

## Complete-chain member relation audit

Member-row denominator: 26456; direct previous-member numerator: 526; within-two-link numerator: 992; within-three-link numerator: 1534; any earlier-chain member numerator: 19308. Bag denominator: 3307; bags with any relation: 3307.
The walk follows the saved complete history, including rejected events: True. Members whose earlier chain contains a rejected event: 23943. This all-ancestor audit is a diagnostic; H_BAG itself uses member-level previous_code, previous_run_bin, previous_gap_s, position, block, and timing summaries, not arbitrary ancestor identity.

## Common history support

Candidate×half denominator: 114; both-class denominator: 114; design-eligible denominator after fixed quotas: 114; exact common-cell numerator: 114; saved-membership construction-feasibility numerator under equal exact-cell quotas and multi-block checks: 0.
Support status: NECESSARY_SUPPORT_ONLY. Descriptive code-marginal numerator: 114; run-bin-marginal numerator: 114. These marginals do not replace the exact previous_code×previous_run_bin intersection. Posthoc cell selection: False. Observed member imbalance limits necessary support only and does not rule out constructing a new balanced bag design.

## H_BAG source trace

H_BAG is assembled from member-level event metadata. Its columns are documented below; no current label or EEG array is a source column.

| column | source | frozen formula | role |
|---|---|---|---|
| previous_code_1_proportion | previous_code | mean(previous_code == '1') over the saved bag members | metadata history |
| previous_code_2_proportion | previous_code | mean(previous_code == '2') over the saved bag members | metadata history |
| previous_code_unknown_proportion | previous_code | mean(previous_code is missing or outside known_codes) | metadata history |
| previous_run_run_1_proportion | previous_run_bin | mean(previous_run_bin == 'run_1') over the saved bag members | metadata history |
| previous_run_run_2_proportion | previous_run_bin | mean(previous_run_bin == 'run_2') over the saved bag members | metadata history |
| previous_run_run_3_5_proportion | previous_run_bin | mean(previous_run_bin == 'run_3_5') over the saved bag members | metadata history |
| previous_run_run_6_plus_proportion | previous_run_bin | mean(previous_run_bin == 'run_6_plus') over the saved bag members | metadata history |
| previous_run_unknown_proportion | previous_run_bin | mean(previous_run_bin == 'unknown') over the saved bag members | metadata history |
| gap_mean | previous_gap_s | mean(previous_gap_s with missing values mapped to 0) | metadata history |
| gap_present | previous_gap_s | mean(isfinite(previous_gap_s)) | metadata history |
| position_mean | position_fraction | mean(position_fraction) | metadata/layout |
| position_squared | position_fraction | mean(position_fraction ** 2) | metadata/layout |
| gap_std | previous_gap_s | nanstd(previous_gap_s) | metadata history |
| position_std | position_fraction | std(position_fraction, ddof=1) | metadata/layout |
| block_count | A_block_id | number of distinct physical A blocks in the bag | metadata/layout |
| time_coverage_s | onset_seconds or onset_sample/original_fs | max(member time) - min(member time) | metadata/timing |

The support count documents an observational design property only. No N2 EEG contrast or scientific effect was computed in Stage 0.
