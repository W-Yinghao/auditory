# 3. Results

## 3.1 Developmental information rises with electrode count (Fig. 1)

On the high-density branch, across four independent fold seeds and three spread subsets
per budget:

| Electrodes | Linear MAE (months) | RBF MAE (months) |
|---|---|---|
| 1 | 17.68 +/- 1.36 | 18.04 +/- 1.69 |
| 8 | 15.23 +/- 0.77 | 14.68 +/- 0.64 |
| 16 | 16.01 +/- 1.74 | 14.69 +/- 0.50 |
| 32 | 14.10 +/- 0.75 | 13.29 +/- 0.81 |
| 64 | 13.57 +/- 0.54 | 12.95 +/- 0.24 |
| 128 | 12.97 +/- 0.57 | 12.50 +/- 0.27 |

against a training-mean baseline of 19.07 months. Information rises monotonically to
about 96 electrodes, with clearly diminishing but non-zero returns above 64. The
nonlinear readout is consistently better by 0.47 to 1.32 months, with the largest margin
between 4 and 32 electrodes; it lowers the whole curve rather than moving its knee.

Permuting identities and re-running the pipeline flattens the curve completely: MAE
19.29 to 20.21 months against a 19.07 baseline, bits recovered -0.001 to +0.047, at every
budget. The clinical branch behaves the same way (33.06 to 33.89 against 32.20).

**Cross-seed dispersion is itself informative.** It falls monotonically with budget, from
1.26-1.69 months at one or two electrodes to **0.24-0.27 months at 64-128**. Low-density
estimates depend strongly on which children land in which fold; high-density estimates do
not.

On the clinical 20-channel branch the total span from one to twenty electrodes is only
about 2-4 months while cross-seed dispersion is 0.7-2.2 months. This branch does **not**
independently replicate the budget effect - but that is consistent with, not contrary to,
the high-density result, because its entire range lies in the noisy part of the curve.
Measuring this curve reliably requires high-density hardware.

## 3.2 Recording length saturates at two minutes (Fig. 2)

The duration axis keeps each recording's **earliest** admissible windows, which is what a
shortened session would actually have produced.

| Duration | 16 ch | 64 ch | 128 ch |
|---|---|---|---|
| 1 min | 15.13 +/- 0.93 | 14.29 +/- 0.32 | 13.78 +/- 0.40 |
| **2 min** | **13.90 +/- 0.69** | **12.70 +/- 0.37** | **12.22 +/- 0.05** |
| 4 min | 13.95 +/- 1.41 | 12.99 +/- 0.31 | 12.50 +/- 0.16 |
| Full (median ~15 min) | 14.69 +/- 0.50 | 12.95 +/- 0.24 | 12.50 +/- 0.27 |

Two minutes is no worse than the full session at any electrode budget, and one minute is
clearly insufficient. At a fixed two minutes the electrode axis still improves
monotonically (13.90 -> 12.70 -> 12.22). **The binding constraint on acquisition is
electrode count, not recording length.** We claim only "no worse than" for the two-minute
row; its slight advantage over the full recording is not interpreted.

## 3.3 Placement dominates count (Fig. 3A)

Across five independent fold seeds, with the montage re-selected inside each training
fold:

| Configuration | Out-of-fold MAE (months) |
|---|---|
| Predict the training mean | 19.07 |
| 16 electrodes, spatially spread | 15.69 +/- 1.00 |
| **16 electrodes, nested selection** | **12.49 +/- 0.81** |
| All 128 electrodes | 12.50 +/- 0.27 |

Sixteen selected electrodes are indistinguishable from the full array, while sixteen
spread electrodes are 3.20 months worse. Two caveats are stated rather than buried.
Between-fold overlap of the selected sets is only 0.245, so the **procedure** generalises
but the specific montage does not; E55, E9, E126 and E16 recur across seeds, and no fixed
electrode list is offered for transcription. And selection also acts as regularisation:
at n = 62, 144 features are easier to fit than 1152, so part of the parity with 128
channels is dimensional rather than informational.

## 3.4 Where the information lives (Fig. 3B)

At 64 electrodes, five feature families are individually sufficient to beat the training
mean - log variance (+4.12 [+1.93, +6.38] months), delta (+3.89 [+1.98, +5.95]), alpha
(+3.35 [+1.05, +5.69]), theta (+3.10 [+0.38, +5.82]) and log complexity (+2.96 [+0.33,
+5.65]) - while **no family's removal costs anything measurable**. The information is
redundantly distributed across low-frequency power and waveform-shape descriptors. The
30-45 Hz band alone yields exactly +0.00 [-1.75, +1.76], a useful internal check, since
that band carries mostly muscle and instrumentation noise.

## 3.5 Cross-amplifier, cross-array transfer

Fitting on one branch and predicting the other, with no target-branch label or statistic
used at any step:

| Direction | Target MAE | Source-mean baseline | Correlation |
|---|---|---|---|
| High-density -> clinical | 38.22 | 43.28 | +0.533 |
| Clinical -> high-density | 31.60 | 38.43 | +0.390 |

Both directions beat a no-EEG predictor. Restricted to the 42 target children inside the
source age range, high-density -> clinical reaches **25.71 months**, the same order as the
clinical branch's own within-cohort 20-electrode result of 26.04. Most of the apparent
transfer penalty is the mismatch in age distribution, not the change of hardware.

## 3.6 Ongoing EEG carries no hearing information beyond age

Across three fold seeds on the clinical branch (n = 56):

| Target | EEG increment over age-only (months or scale points) | Bias-corrected gap correlation |
|---|---|---|
| Device-use duration | -5.56 +/- 0.84 | -0.186 +/- 0.036 |
| MUSS | -3.18 +/- 0.22 | +0.019 +/- 0.027 |
| IT-MAIS/MAIS | -1.68 +/- 0.17 | +0.006 +/- 0.048 |
| CAP | -0.32 +/- 0.04 | -0.013 +/- 0.037 |
| SIR | -0.23 +/- 0.02 | -0.081 +/- 0.019 |
| Unaided PTA | -0.22 +/- 0.46 | -0.008 +/- 0.037 |
| Aided PTA | +0.16 +/- 0.49 | -0.272 +/- 0.045 |

Not one target gains; several lose significantly, which is overfitting of 180 features at
n = 56. Independently, an earlier diagnostic on a different feature construction found
skill scores of -0.008 and -0.051 for unaided and aided PTA against a training-mean
baseline, while the same features reached +0.574 for age.

**The near-miss.** The uncorrected decoding residual correlates with chronological age at
**-0.725**, the signature of regression dilution. Before correction, that residual
correlates with device-use duration at **-0.509** - a clean, plausible, publishable-looking
"children with longer device experience have younger-appearing brain activity". After
standard age-bias correction the same quantity is -0.179 with a bootstrap interval of
[-0.489, +0.145], and every other target's corrected interval also spans zero. We report
this because the uncorrected version would have survived casual review.

## 3.7 A correction to our own analysis

An earlier pass of this study, run on a single fold split, found that the nonlinear
readout reached its ceiling at 16 electrodes and was indistinguishable from 128 there.
**That result did not survive repetition.** With four independent fold seeds (Section
3.1) the nonlinear arm continues to improve to about 96 electrodes. The original
measurement was not a coding error and would have passed any internal check that did not
repeat the split.

The claim that did survive is the different one in Section 3.3: 16 **selected**
electrodes match the full array, whereas 16 **spread** electrodes do not. The 3.20-month
difference between those two configurations is exactly what the single-split result had
confused.

## 3.8 A learned representation that cannot transfer, and why

Self-supervised pretraining on 119 unlabelled recordings (50.68 h; every acquisition
belonging to a labelled child excluded, so no probe is ever tested on pretraining data)
using within-recording relative positioning learns the pretext task well - validation
cross-entropy 0.4968 bits against a 1.0-bit chance level - yet a frozen linear probe on
age reaches MAE 19.06 against a 19.07 training-mean baseline, i.e. nothing.

The reason is structural, not a matter of tuning. The pretext head takes
`|z1 - z2|` for two windows of the same recording, so **any embedding component that is
constant within a recording cancels exactly** and receives no gradient. Subject-level
attributes, including age, live precisely in that cancelled subspace. A pretext task
whose negatives come from other recordings would restore the gradient but would also
reward recording identity, which is the shortcut that made a from-scratch supervised
decoder on this cohort memorise its training recordings (training loss 0.027 bits,
best validation step 99 of 2000, validation cross-entropy 3.48 bits against a 3.00-bit
marginal). We report the learned arm as a control, not as a competitive method; at this
sample size the spectral features are not displaced.
