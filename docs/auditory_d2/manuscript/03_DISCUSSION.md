# 4. Related work

**Paediatric EEG brain age.** Age decoding from children's EEG is established and the
accuracy frontier is held by large samples: a 1056-child sleep-EEG model reaches a
weighted MAE near 0.85 y [A1], a 659-child resting-EEG model reaches about 1.31 y over
3-14 y [A3], and infant-range models reach months [A4], [A5]. Normalised by target
dispersion - the comparison [A6] argues for, since raw MAE is not comparable across age
ranges - those are roughly 0.17-0.20 and 0.44; our 12.50 months against SD 23.5 is 0.53. We therefore do not present age accuracy as a
contribution. Age is the instrument, not the result: it is the one variable in this
cohort known a priori to be decodable, which is what makes the budget curves and the
hearing-related negatives interpretable.

**EEG information capacity.** A recent analysis [D6] argues on simulation grounds that
the neural information recoverable from scalp EEG saturates in the region of 64-128
electrodes and that linear decoders recover far less than the channel capacity. To our
knowledge the present study is the first empirical test of that saturation claim on
real paediatric clinical recordings. Our data do not support saturation below about 96
electrodes for spread montages, and the nonlinear-versus-linear comparison in Section
3.1 gives an empirical handle on the second half of the claim: a strictly stronger
readout lowers the curve by roughly half a month to one and a third months without
changing where it flattens.

**EEG foundation models.** Masked-reconstruction and contrastive pretraining have
produced a rapid sequence of general EEG encoders [E2]-[E5] and at least five benchmarks
in eighteen months [E8], with reviews noting that evaluation remains largely
in-distribution and that paediatric validation is essentially absent [E6], and that
embeddings can encode recording-site identity [E7]. The pretext task we use is the
within-recording relative positioning introduced for clinical EEG in [E1]. We do not position against that literature, and Section 3.8 is
offered as a small, specific mechanistic observation rather than a benchmark entry: a
pretext task built on within-recording differences provably discards the subject-level
subspace.

**Brain-age gaps as biomarkers.** Gap residuals have been related to clinical status in
paediatric populations [A3], [A4], and MRI-based gaps have been reported as elevated in
adults with severe hearing loss [B1], though a mild-to-moderate cohort gave a null [B2].
A published criticism [B3] holds that clinically altered brain activity need not resemble
aged brain activity and that gap-based inference can mislead. Section
3.6 is a concrete instance of that criticism rather than a rebuttal of it: in our cohort
the uncorrected gap produces a coherent, sizeable, entirely spurious association with
device-use duration.

---

# 5. Discussion

## 5.1 What the two axes mean for a clinic

The two-dimensional budget map has an operational reading. Shortening a high-density
paediatric session from fifteen minutes to two costs nothing measurable, while reducing
the array from 128 to 16 spread electrodes costs about 1.7-2.2 months of age resolution
and reducing it to a handful costs several. If a protocol has to give something up, it
should give up minutes before it gives up electrodes. That ordering is the opposite of
what shortened paediatric protocols usually do.

The placement result softens this considerably. Sixteen electrodes chosen by data reach
the accuracy of the full array, so the practical question is not only how many sensors a
child will tolerate but where the tolerated ones go. We stop short of publishing a
montage: between-fold overlap of 0.245 says our data determine that sixteen well-chosen
electrodes suffice, not which sixteen. Establishing a transferable reduced montage would
require either a larger cohort or an explicit stability-selection procedure with its own
validation, and we flag it as the natural next step rather than claiming it.

## 5.2 What ongoing activity encodes here, and what it does not

Three independent lines - a skill-score diagnostic on a different feature construction,
the increment analysis of Section 3.6, and the bias-corrected gap analysis - agree that
ongoing EEG in this cohort tracks the developmental axis and not the auditory one. This
bounds what an ongoing-EEG biomarker can be asked to do in this population. It does not
say that EEG carries no auditory information; it says that the reliable, ongoing,
event-independent part of it does not, which is consistent with the near-zero
between-child reliability of the evoked contrast banks in the same corpus (Section 1.3).

## 5.3 The methodological point we did not plan to make

Section 3.7 is the part of this study we would most want a reader in a similar position
to take away. At n around 60, a single identity-grouped five-fold split produced a clean,
monotone, internally consistent result - a nonlinear readout saturating at 16 electrodes
- that simply disappeared under four repetitions of the split. Nothing about the original
run looked wrong. The dispersion we now report alongside every curve (0.24 months at 128
electrodes, 1.69 at one) is the diagnostic that makes the difference visible, and we
would argue it belongs in any budget-style ablation at this sample size.

The brain-age near-miss in Section 3.6 is the same lesson in a different register: an
analysis choice that is standard in a mature literature (correcting the age bias of the
gap) is the difference between a spurious r = -0.51 and a null.

## 5.4 Limitations

Single centre; 62 and 56 labelled children. The high-density branch is limited by an
evidenced identity criterion that we chose not to relax. The clinical branch spans only
1-20 electrodes, which lies entirely inside the noisy part of the curve, so it cannot
replicate the budget effect and cannot host the selection experiment at all. The parity
between 16 selected and 128 electrodes is partly a regularisation effect at this sample
size. Age is an anchor, not a clinical endpoint, and no causal claim about cortical
maturation is made. The two-minute row is reported as no worse than the full session and
its small advantage is not interpreted. Cross-cohort transfer is evaluated on cohorts
with different age distributions, and the in-range restriction that makes them comparable
uses 42 of 56 children.

## 5.5 Why the information readout is a cross-entropy difference

Variational mutual-information estimators have known sample-complexity and
self-consistency limits [D2], [D3], and partial information decomposition is currently
contested on subsystem grounds [D7]. We therefore report an operational quantity - the
cross-entropy of the model against the cross-entropy of a training-fold marginal - which
requires no density estimator, is a lower bound on the mutual information up to the
generalisation gap, and comes with a shuffled control at every point. The InfoNCE bound
[D1] appears only as the pretraining objective in Section 3.8, not as a reported estimate.

## 5.6 Next

A transferable reduced montage via stability selection with its own held-out validation;
replication of the budget curves on an external paediatric corpus; and, if a learned
representation is to be revisited, a pretext task whose objective does not cancel the
subject-level subspace.
