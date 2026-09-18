> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Matched-cohort HA trial-budget reliability

The first HA preparation summary reports reliability at each trial budget on a
different available-record set. This follow-on audit resolves that comparison
by constructing one common cohort before calculating any correlation.

It reads the 57-record preparation cohort and each corresponding Phase 1 epoch
package. Accepted trials are restricted to acceptance mask column 0 and literal
codes 1 and 2, then sorted chronologically by sample position with event
ordinal as the deterministic tie-break. Budgets 32, 64, 128 and 256 use the
fixed endpoint-inclusive uniform sampler. Each budget is split into odd/even
selected trials and early/late selected trials. A record enters the matched
cohort only when every budget and both splits contain at least one trial of
each literal code.

The exact outcome-blind five-bank feature implementation is reused. For each
bank, budget and split, feature-wise Pearson correlations are computed across
the matched records, followed by median, 25th and 75th percentiles, positive
fractions and the Spearman–Brown split-half heuristic. Early/late and
odd/even results remain separate; neither is treated as a clinical reliability
coefficient. No clinical fields or outcomes are read, and no feature subset is
selected.

The public aggregate reports support counts, the common-cohort size and all
bank summaries. Record identifiers and source hashes remain restricted to the
private run evidence. Existing preparation and model outputs are unchanged.
