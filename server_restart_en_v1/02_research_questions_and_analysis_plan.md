# Research Questions and Analysis Plan

Version: 2026-09-16 v1 | Status: Candidate design; to be finalized after server-side P0/P1 results

## 1. Preferred Candidate Storyline

**Among children with different amounts of hearing-device experience, what reliable information does auditory evoked EEG provide, and how does it relate to clinical auditory and speech function?**

This storyline addresses measurement first, clinical meaning second, and computational methods third. Cohort B, the hearing-aid (HA) cohort, is the current first candidate because the historical material indicates that it includes clinical variables. Whether it becomes the main cohort will depend on EEG matching rates, recording conditions, and measurement quality.

The historical candidate-storyline document raises two ideas worth retaining: "experience and maturation" and "individual differences among children with similar experience." Replace its "three clocks" with a more accurate variable framework: **age, elapsed device-use duration, and hearing and recording conditions**. Pure-tone average (PTA) measures hearing thresholds, not time; age is only a proxy for maturation.

## 2. Three Levels of Questions

| Level | Question | Preferred evidence | Interpretation limits |
|---|---|---|---|
| Measurement | Can each child's response to sound be measured reliably? | Individual-record waveforms, repeated-trial or split-half estimates, measurement error, and missingness rates | Establishes measurability under the specified conditions; does not establish that rehabilitation status has been measured |
| Association | How are age, device-use duration, and hearing status each related to the response? | Within-condition estimates over ranges with common support, effect sizes, and confidence intervals | Observational conditional associations; cannot be directly attributed to device-based training |
| Function | Does EEG contain information about concurrent function that clinical variables do not already describe? | Comparison of a clinical baseline with a model adding EEG, using the same population and identical data splits | A credible improvement supports complementary information; it does not establish a causal mechanism or future prognosis |

The paper does not have to include all three levels. One reliable, bounded question is preferable to several questions with insufficient evidence.

## 3. Cohort B: Define the Comparison Correctly First

### 3.1 Population, Time, and Outcomes

Inventory all available records. A 0-60-month window is a candidate scope for alignment with historical analyses; also report the full range and the structure of records beyond 60 months to avoid discarding data without examination. Define the main analysis scope and the rule for selecting records per child before testing EEG-outcome relationships.

The main analysis can start with one trustworthy matched record per child. If dates are confirmed, select a prespecified visit. If dates are unavailable, a prespecified "smallest nonnegative device-use duration in months" rule can select an index record, but its meaning must be disclosed; it must not be called the true first visit. Use repeated records in appropriate cluster-aware or mixed-model sensitivity analyses. Do not analyze rehabilitation speed, future prediction, or formal longitudinal trajectories until dates and measurement timing have been recovered.

Select the outcome according to its purpose, not according to which outcome has the strongest EEG association:

| Candidate | Purpose and strengths | Issues to resolve first |
|---|---|---|
| MUSS | Everyday speech use; the historical table has a lower maximum-score proportion than IT-MAIS/MAIS | Does not measure pure auditory sensitivity; language, training, and scoring practices can affect it; verify the anomalous score of 87 |
| IT-MAIS/MAIS | Everyday auditory function, which is relatively close to the auditory-processing question | Confirm the instrument version and scoring source for each child and visit; substantial ceiling effects; a combined column name does not make the instruments identical |
| SIR | Supplementary description of speech-intelligibility levels | Strong association with device-use duration and coarse ordinal levels; retain the ordinal scale rather than prespecifying binary classification as the main task |
| CAP and related measures | Supplementary description of auditory performance | Confirm the exact version, score range, and assessment time |

If only MUSS is trustworthy, state the main question explicitly as its "relationship with everyday speech use." If the auditory-scale versions are confirmed and provide sufficient distinguishable variation, auditory function can be considered as the main focus. A measurement or device-experience association paper that does not require clinical outcomes is another option. Lock the primary endpoint after reviewing data quality and constructs, but before examining EEG-scale associations.

### 3.2 Choose EEG Measurements According to the Actual Paradigm

For pure-tone stimulation, first examine stimulus-locked responses. Define the P1 channels, time window, peak-identification criteria, and non-identifiable-response criteria using methodological material and quality-control examples assessed without knowledge of the outcomes. Waveforms in young children do not have to peak near 100 ms. Do not search all time points for the peak most strongly associated with a clinical scale.

Compute the relevant difference wave only after confirming the meaning of standard and deviant stimuli and their event codes. When standards and deviants differ physically in their acoustics, the difference wave may combine sensory responses, adaptation, and mismatch processing. Until those contributions can be distinguished, call it the "deviant-minus-standard difference wave" and do not automatically assign it a pure mismatch negativity (MMN) mechanism.

Start with a small number of interpretable features, such as mean amplitude in a predefined window and latency when peak-identification criteria are met. If waveform shape is the research target, a low-dimensional waveform representation may be appropriate, but any projection learned across children must be fitted within training folds. Whether power spectral density (PSD), connectivity, phase-amplitude coupling (PAC), or deep representations are needed depends on the question; they are not a mandatory checklist of features.

For each feature, also report the number of valid trials, an error or reliability estimate, and missingness status. For grand averages, first obtain averages for each child or record and then weight them according to the target estimand, so that children with more trials do not dominate the waveform.

### 3.3 Conditional Associations with Age and Device Experience

Inspect joint distributions, missingness, value coverage, and device-state distributions before deciding which variables can be estimated in the same model. A low linear correlation does not guarantee sufficient variation in experience within every age range, nor does it rule out unmeasured confounding.

If the field definitions are consistent, "age at measurement approximately equals age at first fitting plus elapsed device-use duration." These three quantities cannot all be entered directly into an ordinary regression as independent explanatory variables. Across repeated records, the implied age at first fitting should be approximately stable. Investigate field definitions and units before analyzing substantial inconsistencies. The duration of hearing loss before first fitting cannot be derived from this identity.

A candidate model is:

`EEG measure ~ age + f(device_use_months) + prespecified hearing measure + estimable recording conditions`

Device-use duration in months and log(1 + months) are functions of the same variable. If both are used, treat them as one device-experience effect block and interpret the full curve; the two coefficients do not represent two independent mechanisms. Limit degrees of freedom in a small sample. Compare only a few prespecified linear or nonlinear forms, and report intervals, the supported range, and sensitivity analyses.

Unaided PTA primarily describes hearing loss. Aided thresholds and stimulus sensation levels more closely reflect audibility during recording, but their definitions must first be confirmed. Do not indiscriminately enter every covariate into a model with a limited sample. Select covariates in advance according to the question and plausible relationships. If a recording or device state is completely tied to group membership, acknowledge that their effects cannot be separated; regression does not replace an informative design.

Prespecify one EEG measure, one outcome, and one core effect for the primary inference. Label the remaining analyses as secondary or exploratory and explain the approach to multiple comparisons. Report effect sizes and intervals. Describe a "nonsignificant association" as insufficient evidence, not as proof that the factor has no effect.

### 3.4 Additional EEG Information and Residuals

Residuals can help examine "deviation from a specified clinical model," but they depend on model form, noise, omitted variables, raters, and ceiling effects. Do not name them "children's neural traits" in advance.

For a prediction question, compare a training-mean baseline, a clinical-variable model, an EEG model, and a clinical-plus-EEG model using the same children and identical test folds. The clinical model should reasonably cover age, device-use duration, and confirmed necessary hearing and condition variables; do not deliberately construct a weak baseline. Do not add another concurrently measured clinical scale as an input for predicting the target scale without explaining and justifying it.

Use nested cross-validation grouped by child; children in the outer test fold are used only for evaluation. Choose the number of folds according to the final number of usable children and the distribution of conditions, rather than mechanically copying the old SIR splits. Fit imputation, standardization, feature selection, and nonlinear-form selection within the training data. All visits and epochs from the same child must remain in the same fold. When implementing this, check the meaning of [grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).

Report mean absolute error (MAE), out-of-sample R^2, correlations, and uncertainty intervals. Improvement can be defined as `MAE(clinical) - MAE(clinical + EEG)`, with positive values indicating lower error. Estimate uncertainty with pairing at the child level. A bootstrap interval computed only from fixed out-of-fold (OOF) predictions is an approximation conditional on the fitted workflow. To assess instability from training and tuning, rerun the relevant resampling workflow; multiple seeds or folds are not independent observations.

For a formal test of residual association, use the same predefined adjustment set on both sides and correctly account for uncertainty from fitting and repeated measurements. For prediction or data-adaptive analyses, fit the adjustment model within the training fold and then compute residuals for the test children. An adjusted association in a conventional prespecified regression can be estimated directly, but in-sample residuals are not independent validation.

A model trained with device-use duration as its supervised target can validly be evaluated by the association between its output and device-use duration in held-out data. That evaluation is not an independent line of mechanistic evidence. If the output is then used to study clinical scales, explicitly describe it as a "score trained to predict device-use duration," not as a target-free measure of brain maturation. The same principle applies to an output trained to predict MUSS and then correlated with MUSS.

## 4. Cohort A: Retain Opportunities Supported by Its Actual Structure

Do not conclude in advance that "there is only one possible story" simply because clinical scales are missing. First verify within-child pairing, physical stimulus parameters, and usable sample sizes.

| Actual data structure | Candidate question | Required constraints |
|---|---|---|
| The same child with a cochlear implant (CI) has multiple comparable stimulus conditions | Response shape, reliability, or discriminability across stimulus conditions | Use within-child analyses; control sound duration, intensity, probability, and trial counts; do not directly compare peaks elicited by physically different stimuli and attribute the differences to language processing |
| The four Mandarin tone identities, syllables, and presentation conditions are clear, with enough trials | Neural discriminability and confusion structure of Mandarin tones | Validate classification by child or explicitly defined within-child time blocks; control stimulus exemplars and device artifacts; decoding a single exemplar does not establish an abstract tone representation |
| Pure-tone conditions are comparable between normal-hearing (NH) and CI children | Group differences in responses under specified conditions | Address age, hearing, acquisition, and device artifacts; group membership is not a mild/moderate/severe impairment label |
| Clinical variables are recovered and the protocols of the two cohorts can be aligned | Compare the same definable question in HA and CI children | First establish comparability of measurements and variables; do not simply concatenate tables and call this independent external validation |
| Identities or key conditions cannot be recovered | Descriptive signal or protocol-feasibility results | Do not make modeling claims about generalization across children; preserve traceable records and document data gaps |

Behavioral confusion matrices from third-party papers can provide background comparisons. Without corresponding behavioral measurements from this cohort, they cannot establish brain-behavior validation for this cohort. A single NH tone record cannot support a stable normative reference for tone responses in normal-hearing children.

## 5. Match Controls to the Question

| Control or check | What it can assess | How it must not be used |
|---|---|---|
| Known examples or synthetic signals with specified time axes, units, and event delays | Whether implementation and time alignment are correct | Cannot validate clinical biological conclusions |
| Reproduction of authors' results on public auditory ERP data, if needed | Whether the reading and analysis workflow has an independent reproducible reference | Public adult data are not external validation for a pediatric clinical population; this is not a prerequisite for starting |
| Permutation or temporal perturbation compatible with event order and block structure | Whether stimulus-related results exceed an appropriate null hypothesis | Do not arbitrarily shuffle adjacent epochs that are dependent |
| Residual or restricted permutation that preserves covariate relationships, using appropriate child-level blocks | Whether an adjusted association or improvement exceeds the corresponding null hypothesis | Do not shuffle scale scores unconditionally, destroy the existing duration-scale relationship, and then claim to test incremental value |
| Prestimulus or non-target windows, device-related channels, and metadata baselines | Clues to temporal contamination, persistent individual states, and device or acquisition confounding | Above-chance performance does not always imply label leakage; prestimulus activity may contain persistent states related to clinical labels |
| Split-half estimates, trial-count matching, and preprocessing sensitivity | Whether noise or processing choices dominate a result | Split-half reliability does not validate a stable personality or neural trait across visits |

Prestimulus controls can also be affected by responses remaining from the preceding stimulus and by temporal spreading from filters. Check the stimulus onset asynchrony (SOA) and filter response before interpreting the results; see the [MNE filtering background tutorial](https://mne.tools/stable/auto_tutorials/preprocessing/25_background_filtering.html).

If a public reference is needed, consider the [ERP CORE author resource page](https://erpinfo.org/blog/2020/6/7/erp-core). It provides adult ERP data and analysis scripts; here it is only a candidate for methodological checks.

"Can EEG predict device-use duration?" is a research test, not a positive control that must succeed. Failure does not establish that the paradigm is invalid. Success still requires examination of age, hearing, and acquisition-batch effects. If training-test leakage is confirmed, suspend the affected prediction claims, fix the problem, and rerun the analyses. Do not interpret every unusual control result as invalidating all the data.

## 6. Let the Evidence Shape the Storyline

| Data result | Story direction that can be discussed | Explanations still to examine or retain |
|---|---|---|
| Measurable EEG is associated with device-use duration, and the adjusted estimate remains supported | Device experience is associated with cortical responses in the specified population and recording conditions | Selection bias, previous residual hearing, age at fitting, and condition confounding; do not claim that experience causes maturation |
| EEG provides a credible improvement over clinical variables for concurrent outcomes | Neural measurements complement descriptions of everyday function | Validation on independent children, device artifacts, scoring bias, and uncertainty from model selection |
| EEG is reliable, but intervals for its relationships with function or experience are wide | The current sample provides limited evidence about the association | Statistical power, restricted range, and mismatch between the measurement and the target construct; do not claim that individual differences exist "only in the scales" |
| EEG is reliable and intervals exclude a prespecified meaningful effect | A bound on the association size in the specified measurement and population | Equivalence or smallest-meaningful-effect criteria must be defined in advance, not after observing a null result |
| Cohort A shows clear within-child stimulus differences | Processing or discriminability of specified auditory stimuli | Physical acoustic differences, memory for the same exemplars, and device responses |
| Data quality, events, or matching are insufficient | A bounded data-resource or methodological-feasibility report, or further recovery of information | Do not promise that a paper will automatically follow or force a fallback paper for a particular journal |

The record of storyline selection should state which clinical patterns had already been examined and which EEG results arose during the current exploration. Locking subsequent tests in advance does not turn earlier exploratory results into preregistered discoveries. Do not search all features, endpoints, and subgroups for the most significant result and then report only that result.

## 7. Minimum Structure of the Final Paper

1. Data structure and comparable conditions: readers can identify where the sample came from and who is actually being compared.
2. Measurement evidence: readers can see real waveforms, differences in quality, and uncertainty for individual children.
3. One core result: an age or experience association, a complementary relationship with function, or a difference in stimulus processing.
4. Key controls and sensitivity analyses: explain why the result is not an obvious consequence of device effects, trial counts, processing, or validation choices.
5. Interpretation limits: explicitly describe the observational, cross-sectional, small-sample, and measurement limitations.

Models serve a specific part of this structure. Start with a small number of interpretable features and simple statistical or predictive baselines. Decide whether to introduce a neural network only when those analyses identify a problem that calls for a better representation.
