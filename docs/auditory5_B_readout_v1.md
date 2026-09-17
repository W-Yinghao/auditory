> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 B L0_HISTORY first-pass readout v1

This is an interim implementation of the fixed-bin CPU representation. It is
not completion of route B: R_SIM and R_SUP, the early/late window diagnostic,
quality-covariate sensitivity, within-candidate circular-shift diagnostic, and further residual/artifact interpretation
remain pending. No neural-memory or Shannon-CMI claim is permitted.

Inputs are the new P1 export named in the actual `folds.json` metadata and its
verified summary hashes. Only accepted current trials with literal current=1,
previous=1, and stored binary history H=0/1 are used. History was computed on
the complete original event chain before QC; this runner never recomputes it.
Identity components define folds, weights, eligibility, and bootstrap clusters,
conservatively treating each component as the candidate unit. Candidate IDs,
trial IDs and all paths are bookkeeping fields, never model inputs.

Each outer training partition fits gap strata at its empirical 1/3 and 2/3
quantiles of log(previous gap). Repeated cut points collapse. Position uses
three fixed equal-width bins on [0,1]. Test gaps outside the observed training
range are excluded. A stratum needs at least five trials of each H in training.
Each training and test candidate then needs at least 20 retained trials of
each H, each covering at least four original 30 s blocks. If candidate removal
invalidates a stratum's training counts, training-only monotone pruning repeats
to a fixed point while keeping the original gap cut points. Test data cannot
change any training boundary or retained stratum. Inner readout folds repeat
their own training-only overlap and candidate eligibility process as well.

The four context columns are log gap, record/segment position, and their two
squares. The stronger context adds cubic splines with three uniformly spaced
knots fitted to each training feature's range, without interactions or bias
columns; extrapolation is constant. A constant training feature contributes no
spline, while its original context column remains. Every context scaler and
spline is fitted again inside each inner fold.

L0 EEG uses channel-major nonoverlapping 20 ms bins: five samples at exactly
250 Hz. Pre is [-0.2,0); post is [0.05,0.45). Candidate-weighted EEG scaling and
PCA to at most 32 dimensions are fitted independently of context in each inner
and outer training set. Context never enters EEG PCA. Classifier weights total
one per candidate and one-half per H. C is chosen from .01/.1/1/10 by pooled
inner OOF candidate-balanced natural-log loss; reported loss is converted to
bits. Temperature is fitted only on selected-C training inner OOF predictions,
bounded to [.25,4]. Shared inner OOF coverage is explicitly saved if overlap
screening removes some validation trials. These losses are training diagnostics.

The main shared test set compares linear context, strong context, strong
context+pre, strong context+post, and strong context+pre+post. The primary
comparison is strong-context CE minus post CE; post increment over pre is
pre CE minus pre+post CE. Both raw and calibrated predictions are retained.

A second analysis requires the preceding event's EEG to have been accepted
and stored. It keeps the main training gap boundaries, rechecks common H
support using only this training subset, and reruns all five models on exactly
the same subset. It additionally compares strong context+previous post against
strong context+previous post+current post. A rejected preceding EEG can remove
a trial from this control, but does not change H or the full-sample analysis.
Subset and full-sample scores are never subtracted from each other.

Per-trial predictions, fitted readouts, histories, per-candidate losses, complete
support gates and fit scopes stay private. Public results contain aggregate
eligibility flow and paired gains with 2,000 fixed-OOF identity-group bootstrap
draws. These intervals do not refit the workflow or provide external validation.
Missing support is not a negative scientific result. The overall verdict is
at most `INTERIM_B_L0_ONLY`, with route completion and remaining checks explicit.
Fewer than 20 held-out candidate groups in the main analysis yields
`SUPPORT_INSUFFICIENT`; any computed gains remain descriptive.
