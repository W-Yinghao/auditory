# 2. Methods

## 2.1 Cohorts

Two branches of a single paediatric hearing-clinic corpus, recorded on different
hardware, are used. Identities were established in earlier work under an evidenced
criterion (a unique participant matched by exact name on the same day) and are not
re-derived here; age is the value that criterion yields from one parsed date of birth
and the selected EEG record time. No identity is inferred from a filename or a device
identifier count.

| Branch | Exported recordings | Labelled identities | Channels | Age (months) | Training-mean MAE |
|---|---|---|---|---|---|
| High-density (HydroCel GSN-128) | 378 (99.94 h) | 62 | 128 after reference exclusion | 20-123, SD 23.5 | 19.07 |
| Clinical 10-20 | 93 (20.53 h) | 56 | 20 scalp | 6-186, SD 41.1 | 32.20 |

The two age ranges differ, so the two branches are never pooled and their errors are
never compared directly.

## 2.2 Signal export

One frozen contract, `auditory_d1_continuous_v1`, is applied identically to both
branches. Each stored interval is filtered independently, so filtering never spans an
acquisition gap. Filtering is zero phase (a 4th-order Butterworth high-pass at 0.5 Hz
followed by an 8th-order low-pass at 45 Hz, applied forward and backward), which is
appropriate here because there are no events whose pre-stimulus boundary must be
protected and because a group delay would otherwise distort relations between bands.
The band reaches 45 Hz rather than the 30 Hz used elsewhere in this corpus so that the
aperiodic part of the spectrum has a usable fit range while staying clear of mains.
Resampling to 250 Hz is by integer stride only (1000 -> 4, 500 -> 2, 250 -> 1); any
other original rate is refused rather than approximated, since no verified resampler
exists in this codebase. An average reference is taken over all retained physical
channels after filtering, with declared reference sensors excluded from both the average
and the output.

Long recordings are filtered by overlap-save with one full 60 s chunk of real signal on
each side of every emitted block, so that only the true interval edges rely on the
filter's own edge handling. This is verified rather than asserted: the streaming path
reproduces whole-interval `filtfilt` to a relative difference of **2e-12** across chunk
counts from one to seven, and the check is run as a job before any export.

Per-4 s-block quality statistics (per-channel peak-to-peak, flat-channel counts) are
stored alongside each recording but **never used to drop samples at export time**;
window admissibility is a downstream decision, recorded with its threshold.

## 2.3 Windows and normalisation

Analysis windows are 8 s (2000 samples at 250 Hz) starting on 4 s quality-block
boundaries, so consecutive windows overlap by half. A window is admissible when no
constituent block has more than 25% of channels exceeding 150 microvolts peak to peak,
and when it lies entirely inside one stored interval.

Each recording is divided by a single robust gain, the median absolute value over a
fixed sample of its windows. One scalar per recording removes amplifier and impedance
gain without flattening the relative amplitude structure across channels, which
per-channel scaling would destroy.

## 2.4 Features and readouts

Per channel and per window: log power in six bands (0.5-4, 4-8, 8-13, 13-20, 20-30,
30-45 Hz) by Welch periodogram (2 s Hann segments, 50% overlap, power spectral density
times the frequency resolution), plus log variance and log Hjorth mobility and
complexity. Nine values per channel. A recording is summarised by the mean of these
values over its admissible windows. Because every feature is a function of one channel
alone, the full-array matrix is computed once and any electrode subset is a row slice of
it; recomputing per subset would repeat identical work for every point on the curve.

Two readouts are compared. The linear arm is ridge regression with the penalty chosen by
inner-fold squared error over a fixed grid. The nonlinear arm is RBF kernel ridge with
penalty and bandwidth chosen the same way on the same folds, so any difference is
attributable to the readout rather than to the protocol.

## 2.5 Information readout

Age is continuous, so the probabilistic readout is derived from the regression rather
than from a separate classifier. Within each outer training fold, quantile bin edges and
the marginal class distribution are estimated from training children only, and the
inner-fold residuals give an honest predictive scale. The predictive Gaussian is
integrated over those bins, and

    bits recovered = CE(training-fold marginal) - CE(model)      [log base 2]

evaluated on the held-out children. Calibration therefore comes from held-out residuals,
not from a model's own confidence. Mean absolute error in months is reported alongside
as the clinically legible quantity.

## 2.6 Validation protocol

All splits are grouped by identity: every recording of one child lies in exactly one
fold. Hyperparameters, bin edges, marginals, residual scales, bias-correction slopes and
electrode subsets are all derived inside training folds only.

Budgets are compared **paired** on the same children with an identity-level bootstrap
(2000 replicates, one shared resampling index set across contrasts so all comparisons on
a curve are mutually comparable), because comparing independent means across budgets
discards the pairing and buries the effect in between-child variance.

**Every curve is repeated across independent fold-assignment seeds and reported with its
cross-seed dispersion.** This is not decoration. A saturation point we first measured on
one fold split did not survive repetition (Section 4.5), and at this sample size a single
split produces results that look entirely publishable.

Negative controls: identities are permuted and the whole pipeline re-run, at every
electrode budget and on both branches.

## 2.7 Electrode subsets and selection

Two subset families are used. **Spread** subsets come from greedy farthest-point sampling
on the electrode coordinates, from several deterministic starting sensors; using spread
rather than random subsets makes the curve a statement about electrode count rather than
about luck in coverage. **Selected** subsets come from greedy forward selection driven by
inner-fold error, re-run from scratch inside each outer training fold, so the reported
number is the out-of-fold error of the whole selection procedure. A consensus montage
across folds is reported separately, with its selection frequency, and never as the
source of an error estimate.

## 2.8 Cross-cohort transfer

High-density sensors are matched one-to-one to the twenty 10-20 targets by linear sum
assignment under a 40 mm limit frozen earlier in this project; the achieved maximum
distance is 22.1 mm. A model is fitted on one branch, with hyperparameters chosen by
inner folds of that branch alone, and applied to the other. No label, and no statistic,
from the target branch enters any step.

## 2.9 Clinical analysis and brain-age bias correction

For each clinical variable, three out-of-fold models are compared on identical folds: an
age-only model, an EEG-only model, and EEG plus age. The quantity of interest is the
increment of the joint model over the age-only model, because a model of hearing history
that merely rediscovers age is not a finding.

The decoding residual (predicted minus chronological age) is negatively correlated with
age by construction whenever the decoder is imperfect, so raw gap correlations are not
reported as results. The correction slope is fitted on training-fold children and applied
to held-out children.

## 2.10 Compute

All numerical work runs through the cluster scheduler. Exports and analyses are CPU;
the learned-representation arm uses a single GPU with the labelled corpus resident in
device memory, since assembling batches on the host would move about 130 MB per step and
make host memory rather than the accelerator the bottleneck. Identifying information,
per-child predictions, run logs and the exported signal arrays remain on the research
server; only aggregates are reported.
