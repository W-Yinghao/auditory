# Review and Corrections of Legacy Materials

Date: 2026-09-16 | Conclusion: Keep the candidate questions and retest their premises.

## 1. Review Scope and Evidence Level

The synchronization bundle contains 61 files, with a total uncompressed size of 6,614,406 bytes; its CRC check passed. It contains no raw EEG, only three placeholder files under `data/raw/`. The candidate-storyline document has the same hash as the separately supplied file.

We recalculated the original candidate findings F9-F12 using the bundled `visit_manifest.csv` and inspected `participant_manifest.csv`, `analysis_summary.json`, `clinical_three_clocks.py`, and the clinical-field extraction code. Most numerical results can be reproduced. The main issue is that exploratory results were interpreted too definitively.

**This review did not reread the original clinical workbook or access the server EEG.** Therefore, "reproducible" refers only to the legacy anonymized derived tables and their calculations. It does not yet establish that the original tables were converted correctly, device conditions were consistent, or EEG matching is usable.

Source verification follows. "Candidate Storylines and Decision Criteria" is an English descriptive label for a historical source with a non-English filename, not a literal source path. The original content hashes are unchanged.

```text
EEG-SIR_sync_bundle.zip
SHA256 7488c4bd9ee00655e5585fb3bbfe18a9e2cd2d148444036d1e680cfd454d2010

Candidate Storylines and Decision Criteria
(The separately supplied file and the copy inside the bundle are identical.)
SHA256 d2eccde9286053bd80980274b8b64544a8ff93010fac5a24d63fda2d000a2f9d
```

Detailed aggregate values are saved in `evidence/aggregate_verified.json`. The additional sensitivity calculations in that file are also exploratory audits, not new confirmatory results.

## 2. Facts That Can Be Retained and Their Scope

| Fact | Verification in this review | Appropriate use |
|---|---|---|
| Cohort B size | 95 records / 80 children; HA 84 / 69, NH 11 / 11 | A starting point for reconciling clinical derived tables, not the EEG sample size |
| HA, 0-60 months | 67 records / 55 children | Can align historical results; the server must reconfirm the scope |
| Age versus device-use months | One index record per child within 0-60 months, n=55; Spearman rho approximately 0.266 | There is scope to analyze conditional associations; this is not causal separation |
| Clue within one age range | 60 <= age in months < 96, n=24; device-use months 0-52; age-versus-duration rho approximately -0.01 | An exploratory description of this age window, not evidence for the whole cohort |
| 0-month group | n=15 index records; median age 74 months, IQR 62-84 | First verify whether "0 months" means initial fitting or the start of using the current device |
| Repeated records in all HA data | 13 children / 28 records; device-use months vary for 12 children | Dates are unverified; do not call all repeats longitudinal follow-up |
| Repeated HA records within 0-60 months | 10 children / 22 records | A small repeated-record subset, suitable only for cautious exploration of stability |

No negative values of age minus device-use months were found in the derived table; the differences range from 5 to 177 months. For 3 children with repeated records, this difference changes by 1-2 months. Rounding, measurement timing, or field definitions may be involved and require source verification. This arithmetic difference must not simply be renamed a verified age at first fitting.

Two additional records have the same age and device-use months as other records from the same child. It is not yet clear whether they are same-day retests or duplicate entries. **Do not delete them without verification.** In the current data, filtering to 0-60 months before selecting the shortest-duration index record yields the same set as applying these operations in the reverse order. The server must still specify rules for nonnegative values, missing values, and actual dates.

## 3. F10: Age Does Contribute

Original claim: "Scale scores are almost entirely determined by experience; audibility does not contribute."

For the same 54 index records with complete age, device-use months, unaided PTA, and MUSS:

| MUSS model | In-sample R-squared | Leave-one-out predictive R-squared |
|---|---:|---:|
| Device-use months | 0.677 | 0.652 |
| Add age | 0.774 | 0.735 |
| Then add unaided PTA | 0.788 | 0.743 |
| Then add log(1 + device-use months) | 0.828 | 0.778 |

Adding age increases in-sample R-squared by approximately 0.097, so these results do not support saying that "almost only experience contributes." In the full model, device-use months and its log term correlate at approximately 0.914. They are two functions of the same variable, and the entire curve needs to be interpreted. Of the 54 fitted values, 6 exceed the MUSS maximum of 100, indicating that the effects of bounded scores and ceiling effects on model fit must be checked.

After excluding the 0-month group, 39 complete cases remain, and leave-one-out R-squared for the same full model is approximately 0.631. This is an important sensitivity result and makes the inclusion of the 0-month group and device state priority checks. R-squared values from different data ranges cannot be treated mechanically as directly comparable performance measures because outcome variance also changes.

The legacy comparison involving aided PTA used 47 complete cases and a baseline **without the log term**: leave-one-out R-squared changed from 0.736 to 0.716. This does not directly support saying that "adding aided PTA to the full model contributes nothing," much less establish that actual audibility has no role.

Revised wording:

> In the historical clinical table, device-use months are strongly associated with MUSS, and age provides additional explanation. An exploratory model including age, device-use months and its log term, and unaided PTA achieved relatively high in-sample and leave-one-out predictive performance. These results do not establish a causal effect of device experience or exclude a role for hearing or audibility.

The original leave-one-out prediction used one index record per child. We found no direct leakage caused by repeated records from the same child crossing training and test sets. However, the model form, subgroups, and storyline had already been informed by the full dataset, so the analysis remains exploratory. Formal prediction must put the selection process inside the training data.

## 4. F11: Residuals Merit Study but Are Not Yet Stable Neural Traits

| Check | Result | Interpretation limit |
|---|---|---|
| Original clinical-model residuals | 66 records; SD approximately 8.5; 9 records with absolute residual >10 points | Mixes in-sample errors for index records with errors for additional records |
| First-versus-last residuals in children with repeated records | 10 children; rho approximately 0.576; ordinary p approximately 0.082 | Substantial uncertainty; dates and the origin of repeats are unconfirmed |
| Residuals after refitting with each child held out | SD approximately 9.53; 14/66 records with absolute residual >10 points | Original in-sample residuals cannot be treated as independent validation measures |
| Adjusted association between two scales | Simultaneous adjustment for age, duration, the log term, and unaided PTA; n=54; residual rho approximately 0.673 | Can be retained as an adjusted association; does not establish a shared neural construct |
| Daily-use field versus residuals | 15 records from 11 children; record-level rho approximately 0.627 | Original p approximately 0.012 does not account for repeats; field units and conversion of nonnumeric values still require source verification |

The original approximate ICC of 0.5 can be reproduced, but the calculation for unbalanced repeated records and the naming of variance components were insufficiently precise. The code's "between-child SD of 6.4" is actually the standard deviation of child means, not a pure child random-effect SD. An exploratory random-intercept model still estimates ICC at approximately 0.527. **Numerical similarity does not remove limitations arising from the small sample, model residuals, or measurement sources.**

The original cross-scale residual calculation adjusted only for linear age and duration. This review obtained a similar correlation using the full adjustment model, so the relationship is not an artifact entirely explained by the log term. However, shared raters, overlapping scale content, nonlinear ceiling effects, and unmeasured variables could all produce this relationship.

`daily_wear` comes from column 40 of an auxiliary sheet. The legacy script checked identity consistency for the corresponding rows; **we found no unguarded row-misalignment merge**. The outstanding checks concern the column's meaning, units, whether the source is parent report or device logging, and whether ranges or text were lost when converting to floating-point values. The current derived table contains 16 nonmissing HA records in total and 15 within 0-60 months. These records must not be treated as 15 independent children.

Bias from raters knowing device-use duration cannot be assumed to disappear through residualization. The new question should be: "Can EEG add information about concurrent functional differences unexplained by a specified clinical model?" It should not be: "Can EEG identify a neural trait whose existence has already been established?"

## 5. Other Legacy Conclusions That Must Be Revised

| Legacy statement or rule | Revision in this review |
|---|---|
| A low rho means experience and maturation are identifiable, and a trajectory analysis is valid | Reframe as a conditional association to be tested; actual within-child trajectories require identity and timing evidence |
| PTA is a third clock | Treat PTA as a hearing or hearing-threshold measure, separate from age and elapsed device-use time |
| External literature says age does not change P1, so changes must reflect experience | Age, acquisition, and selection factors in this cohort cannot be excluded; remove this inference |
| Pure-tone data automatically imply MMN and a fixed 100-250 ms window | First verify the protocol, events, and child waveforms; a difference wave is not automatically a pure MMN |
| Use 11 NH children to create an age-normative band | Use them only as a descriptive reference for this sample, not to establish normal ranges or age standards |
| EEG decoding of duration is a positive control | Treat it as a research task; failure cannot establish that the paradigm is invalid |
| OOF scores trained on duration or scale scores provide independent mechanistic evidence | OOF evaluation supports predictive assessment; it must not be repackaged as independent validation of a neural mechanism |
| One effect is significant and another is not, so two clocks are separated | This is not a test of the difference between effects; report estimates and intervals |
| A null result means individual differences are specific to the scales or that EEG is insensitive | Describe evidence strength and precision, retaining noise, power, range, and other possible explanations |
| Six possible results automatically imply six paper titles and journals | Remove this guarantee; decide whether a paper is warranted from the question, quality, effects, and limitations |
| Cohort A has no scales, so four-tone decoding is its only possible storyline | Also investigate opportunities such as within-condition reliability and within-child stimulus comparisons |
| Excluding the 0-month group resolves confounding by device conditions | This only restricts the new analysis population; conditions in the remaining records also require verification |

This review did not fully verify the literature supporting the original statements about research gaps, the specific ages and methods in other studies, novelty, or journal positioning. These remain leads for follow-up, not established evidence in the startup materials.

## 6. Limits on Using Legacy Groups and Scripts

Historical group labels and continuous duration values disagree in 4 places. Regrouping by continuous values gives the following counts across all HA records: 0 months, 15; (0,6) months, 9; [6,12) months, 3; [12,24] months, 13; (24,36] months, 14; (36,60] months, 13; >60 months, 17.

The legacy script omitted the 6-11 month category when printing strata; it includes 1 index child. A filter written only as `<=60` should also be replaced by an explicit `0 <= device-use months <= 60` condition and validity checks. There are no negative values in the current derived table, so this did not change the present numbers. Do not directly reuse the legacy `eligible_primary_clinical` flag or SIR binary-classification folds to define the new task.

The legacy EEG inventory script contains a reading framework that may be reusable, but the following issues must be corrected first:

- Stopping the trigger-channel search as soon as annotations are present may miss actual events. Not every annotation other than bad/boundary is a stimulus.
- Treating the two most frequent event classes as standard/deviant and imposing a fixed SOA may misidentify the protocol.
- When attaching separate event files, verify time offsets, synchronization, and how original annotations are retained. Do not overwrite annotations and assume the result is correct.
- Verify companion files using each format's internal references. Assuming a same-stem `.fdt` file does not cover all EEGLAB files; split FIF, compressed FIF, and other formats also need handling.
- For epoched files, "number of epochs x window length" is not the original continuous recording duration. The number of exported files is not the number of acquisition recordings.
- Replacing known names from a mapping table does not guarantee that unknown names, aliases, paths, or reader logs are de-identified.
- The legacy script lacks separation between output and raw-data directories, protection for existing files, and resource controls for staged reading.

The new bundled script performs only conservative file enumeration, avoiding automatic event naming, identity inference, and full loading. The server must implement and verify detailed readers according to the actual formats.

## 7. Recommendation from This Review

Retain the useful questions about device experience, age, cortical responses, and everyday function. Return claims that "experience has already been separated," "a trait already exists," or "EEG must show a particular pattern" to the status of hypotheses to be tested. The first round should recover data structure, device and event conditions, clinical matching, and initial measurement checks. Build the new storyline from that evidence.
