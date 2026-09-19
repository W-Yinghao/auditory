# Acquisition Budgets for Paediatric Clinical EEG: Electrode Count, Recording Length, and What Ongoing Activity Does Not Encode

Draft v1. Target: IEEE JBHI. All numbers are from `D2_MANUSCRIPT_SKELETON.md` and are
reproducible from the runs listed there. Nothing in this draft is an ERP analysis.

---

## Abstract

Paediatric clinical EEG is limited less by algorithms than by what a young child will
tolerate: how many electrodes can be placed, and for how long they will sit still. We
treat that as an information question and map both axes on 118 children recorded at a
paediatric hearing clinic - 62 on a 128-channel high-density net and 56 on a 20-channel
clinical 10-20 montage - using continuous EEG only, with no events, no trial averaging
and no evoked components.

Decoding chronological age from ongoing activity serves as the anchor, and information
is reported operationally as bits recovered against a training-fold marginal, with
identity-grouped folds, label-shuffled controls, and dispersion across independent fold
seeds attached to every curve.

Three results follow. First, recoverable developmental information rises with electrode
count and does not saturate below roughly 96 electrodes (age MAE 17.7 to 12.5 months
against a 19.1-month training-mean baseline), whereas recording length saturates at
**two minutes**: two minutes of EEG matches a fifteen-minute session at every electrode
budget (12.22 +/- 0.05 vs 12.50 +/- 0.27 months at 128 channels). Electrodes, not
minutes, are the binding constraint. Second, **where** electrodes sit matters more than
how many there are: sixteen electrodes chosen by nested selection inside training folds
reach 12.49 +/- 0.81 months, indistinguishable from the full 128-channel array, while
sixteen spatially spread electrodes reach only 15.69 +/- 1.00. Third, the same ongoing
activity carries **no** information about hearing status beyond age - device-use
duration, unaided and aided pure-tone average, and four parent-report auditory and
speech scales all show zero or negative increment over an age-only model - and an
uncorrected brain-age gap in this cohort would have reported a publishable-looking
r = -0.51 with device-use duration that vanishes entirely under standard age-bias
correction.

We also report a correction to our own analysis: a saturation point we first measured on
a single fold split did not survive repetition, which is why every curve here carries
cross-seed dispersion.

---

## 1. Introduction

### 1.1 The constraint that actually binds

Most work on clinical EEG decoding assumes the recording as given and asks what can be
extracted from it. In paediatrics, and especially in young children wearing hearing
devices, the recording is not given. Electrode application time, cap tolerance and the
child's willingness to sit still determine what is acquired, and these limits are
routinely the reason a paediatric protocol is shortened or a high-density net is not
used at all. An informatics contribution to this setting is therefore not another
decoder but an answer to: how much of the extractable information survives a smaller
acquisition, and which axis of the acquisition should be cut first.

### 1.2 Why a developmental anchor, and why not a clinical one

Choosing the decoding target is where this kind of study usually goes wrong. A target
that cannot be decoded at all makes every negative result uninterpretable, because a
null cannot distinguish "no relation" from "broken pipeline". We therefore anchor on
chronological age, which is decodable from paediatric EEG a priori and whose decoders
are well characterised [A1]-[A7], and we report a label-shuffled control at every point
of every curve so that the reader can see the floor.

We then ask separately whether the same representation carries clinical information
about hearing. It does not, and we report that negative with the same machinery and the
same controls rather than as a footnote.

### 1.3 Why not evoked responses

The corpus was acquired with an auditory paradigm, so an evoked-response analysis would
be the conventional route. We deliberately do not take it. Within-record reliability of
the trial-averaged and difference-wave feature banks in this corpus, measured earlier on
a matched cohort, is near zero for the deviant-minus-standard contrast (median split-half
r = 0.07 at 32 trials and 0.06 at 256, i.e. eight times the trials does not lift it),
while the ongoing spectral and waveform-shape banks reach 0.89 to 0.98. A measure with
no between-child reliability has no validity ceiling to study. Everything here is
therefore continuous-EEG decoding.

### 1.4 Contributions

1. A channel-budget information curve for developmental decoding on real paediatric
   clinical EEG, with the stability of that curve as a reported quantity rather than an
   assumption.
2. A second, clinically harder axis - recording length - and the resulting
   two-dimensional acquisition budget map.
3. Evidence that electrode placement dominates electrode count at a fixed budget, from a
   properly nested selection procedure.
4. Cross-amplifier, cross-array transfer with no target-cohort labels.
5. Three independently confirmed negatives about what ongoing paediatric EEG does not
   encode, including a concrete near-miss false positive from an uncorrected brain-age
   gap.
