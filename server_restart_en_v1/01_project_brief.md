# Pediatric Auditory EEG Project Brief

Version: 2026-09-16 v1 | Lead: the researcher | Stage: server-side data audit and research design

## 1. What this restart should resolve

Provisional working title: **Auditory stimulus processing, device-use experience, and everyday auditory and speech function in children**.

The central questions are: Which EEG responses to sound can be measured reliably in children? How do these responses relate to age, device-use experience, and hearing status? Can they add information to clinical descriptions of everyday function?

These are research questions, not established conclusions. Data are now available on the server, so the actual files can guide the research direction. First reconstruct the experimental structure and assess data quality, then select one primary question and the methods needed to answer it.

This brief replaces the previous plan's predetermined architecture, fixed endpoints, fixed "six types of results," and target journal. Whether to use LiteBiMamba, EEGNet, another network, or no deep learning should depend on the questions and evidence that emerge. The roles of MUSS, IT-MAIS/MAIS, SIR, and other measures should likewise depend on what they measure and their data quality.

## 2. What has already been checked locally

The local review covered the user-provided `EEG-SIR_sync_bundle.zip` and the legacy candidate-storyline document. The sync bundle contains 61 files and passed the archive integrity check. Its `data/raw/` directory contains only placeholder files: **the bundle contains no raw EEG**.

The review covered the project handover notes, milestones, candidate storylines, clinical analysis and inventory scripts, and anonymized derived clinical tables in the bundle. The candidate-storyline document inside the bundle has the same content as the Markdown document provided separately by the user. The supervisor evaluation report and the original manuscript's model rationale were not used as the basis for this design.

Numbers reported below are recalculations from legacy derived clinical tables or records in historical documents. They do not mean that the server-side EEG has already been verified. The server report must establish whether the original data are complete, whether additional children are present, and how many records can be matched.

The legacy bundle includes private clinical workbooks and data documentation. This startup packet does not copy those materials or include child-level clinical data. When verification is needed, read the existing source tables in the server's private directory.

## 3. Working assumptions about the two cohorts

| Item | Cohort A | Cohort B |
|---|---|---|
| Participants described in existing materials | Normal-hearing children, cochlear implant users, and a small number of hearing-aid and bimodal records | Children using hearing aids and normal-hearing reference records |
| Stimulus types | Pure tones, syllables, and Mandarin lexical tones; confirm the exact design from event codes and experimental records | Pure tones; verify whether an oddball design was used and, if so, how it was implemented |
| Clinical scales | Legacy materials state that none are available; verify against the newly received files | Legacy tables include MUSS, IT-MAIS/MAIS, SIR, CAP, and other measures |
| Time information | Insufficient historical documentation | Device-use duration in months and a small number of repeated records; the original clinical table lacks actual visit dates |
| Main opportunities | Condition contrasts, stimulus processing, and within-child comparisons across stimuli, depending on actual pairing | Relationships of age, device-use experience, and hearing status with EEG and function |
| Primary unknowns | Number of unique children, pairing across stimuli, classification of bimodal records, and event meanings | Matching EEG to clinical visits, device state during recording, and the reliability of duration and age information |

The historical Cohort A slide reports the counts below. **Each cell counts records or condition entries; these values must not be summed and treated as independent children.**

| Group label | Pure tone | Syllable | Lexical tone | Bimodal entries |
|---|---:|---:|---:|---:|
| Normal hearing (NH) | 14 | 6 | 1 | 0 |
| Cochlear implant (CI) | 24 | 16 | 16 | 0 |
| Hearing aid (HA) | 1 | 1 | 1 | 15 |

Bimodal means a CI in one ear and an HA in the other; it is a device configuration. Its placement in the "hearing aid" row of the source table does not establish the actual group assignment, stimulus type, or number of children represented by these entries.

Starting point for reconciling the legacy anonymized Cohort B table:

| Scope | Clinical records | Unique children |
|---|---:|---:|
| Entire table | 95 | 80 |
| All HA | 84 | 69 |
| NH | 11 | 11 |
| HA use duration of 0-60 months | 67 | 55 |
| The 0-60-month scope plus NH | 78 | 66 |

Across all HA records, 13 children contribute 28 records in total, while the remaining 56 children contribute one record each. Among HA records in the 0-60-month scope, 10 children contribute 22 records in total. Neither 84, 67, nor the number of epochs is the independent sample size. Inventory the full range first. **Do not delete records with device-use duration >60 months during the file audit.** The final scope should depend on data quality, the range supported by the data, and the research question.

## 4. Five issues the first round must resolve

### 4.1 Can the files be assembled into traceable acquisition records?

Create a file inventory and verify companion-file relationships such as `.set/.fdt`, `data.bdf/evt.bdf`, and `.vhdr/.vmrk/.eeg`. Directory-based recordings and recordings split into segments may consist of multiple files. Distinguish raw data, preprocessed data, epoched data, averaged waveforms, and duplicate exports, and preserve their processing provenance. Two exports of the same signal must not be counted as two acquisitions.

By default, read only headers and necessary signal segments. Report CPU, memory, free disk space, and the existing software environment first, then read files in batches appropriate to their size. A GPU is not a prerequisite for starting.

### 4.2 Can children, visits, recordings, and conditions be matched reliably?

Assign a stable anonymized ID to each unique child and separate IDs to visits and acquisitions. Record the evidence and status for each match: confirmed, pending confirmation, or unmatched. Names may assist local lookup on the server, but identical names must not trigger automatic merging, and different export names do not establish that records belong to different children.

The legacy Cohort B `visit_id` is a derived identifier. Do not match it to EEG merely by file order. Prioritize joint verification using participant IDs, actual acquisition times, clinical assessment times, and acquisition logs. File modification times can assist troubleshooting but cannot replace visit dates. When dates are missing, use "records ordered by device-use duration in months," not "confirmed first/last follow-up."

Check for children appearing in both cohorts or across acquisition protocols. Treat the meeting statement that "there is no overlap" as a historical description requiring verification. If future analyses share training, pretraining, or evaluation data, use a unified child identity system to prevent leakage.

### 4.3 What stimuli were actually presented?

For each protocol, document sound type, level, duration, presentation ear, standard/deviant definitions, probabilities, sequence, intervals, and corresponding events. Determine whether events come from annotations, a trigger channel, a separate event file, or an experimental log, and cross-check these sources.

Many event codes do not necessarily mean many stimulus conditions. Event counts near an 80:20 ratio are also insufficient to establish standard/deviant meanings. Define prestimulus windows, averaging windows, and filter parameters only after the actual intervals and trigger delays are understood. The MNE [event parsing tutorial](https://mne.tools/stable/auto_tutorials/intro/20_events_from_raw.html) can help verify the reading procedure.

### 4.4 Are recording conditions confounded with the research variables?

At minimum, check:

- Whether the 0-month group was recorded unaided while other groups wore devices, and whether each record has device-on/device-off conditions.
- Whether device type, unilateral/bilateral configuration, manufacturer, and processing mode are tied to stimulus protocol, age, or device-use duration.
- Whether sound level is expressed in dB SPL, dB HL, or a level relative to threshold, and whether actual audibility is comparable across children.
- Whether online reference, channel count, sampling rate, acquisition batch, and preprocessing version vary by group.
- Whether age means age at assessment, device-use duration means elapsed time since the first fitting, and daily use hours have a clear unit and source.

If device state completely coincides with membership in the 0-month group, simply "adding a variable" to a model cannot separate them. Excluding the 0-month group can only estimate relationships in the remaining population; it cannot establish an "initial rehabilitation effect." List records with unknown conditions separately at first.

### 4.5 Do the data support stable EEG measurements?

First check units, saturation/flat signals, bad channels, reference, spectra, mains interference, event alignment, device artifacts, boundaries, and valid stimulus counts. In P0, inspect representative records from each acquisition protocol and summarize the status of every record as checked, not yet checked, or failed to read. Prioritize results stratified by protocol, device state, and data version.

Do not use clinical outcomes to determine quality. A weak auditory response does not automatically mean poor data, and a good grand average does not guarantee stable measurements for every child. In P1, systematically report uncertainty for individual recordings, split-half stability, and the proportion of recordings from which a feature cannot be extracted reliably. Do not replace missing features with zero.

CI device artifacts can be stimulus-locked. Successful group classification, successful standard/deviant classification, or detection of a peak does not, by itself, establish that the information is cortical.

## 5. How the project should proceed

| Phase | Question | Deliverables | Basis for proceeding to the next phase |
|---|---|---|---|
| P0: Data audit | What data are present, and are their provenance and identities trustworthy? | Reconciled counts, matching tables, event dictionary, quality examples, and issue list | At least one branch has trustworthy identities, interpretable conditions, and readable signals |
| P1: Measurement and description | Which responses can be measured reliably, and how large is the measurement error? | Outcome-blinded quality rules, waveforms, feature definitions, reliability, and missingness | Target features are interpretable, and measurement error and selective missingness have been characterized |
| P2: Formal question testing | How do responses relate to age, experience, hearing, and function? | Prespecified primary analyses, effects and intervals, and sensitivity analyses | The range supported by the data and the confounding limitations permit meaningful estimation |
| P3: Computational method extensions | What do simple measurements miss, and are complex models needed? | Baseline comparisons and incremental evaluation using identical child-level splits | A clear question, sufficient data, and credible validation are available; otherwise omit this phase |

The first server work order covers P0 and enough preliminary signal inspection to support P1 design. Specific P2/P3 routes are described in `02_research_questions_and_analysis_plan.md`. If one branch fails its checks, continue with the other branches. Report "readable" and "usable for this research question" separately.

The first delivery should preferably include six types of figures: data inclusion flow, child-by-condition coverage, event/device conditions, signals and quality, age versus device-use duration, and scale distributions. Label each figure with the current data scope and counting unit. Document gaps when data are unavailable; do not create illustrative "results."

## 6. Project files and working boundaries

Create an independent research working directory, using this packet as the starting point and accessing raw data through explicit read-only paths. Do not directly overwrite the new project's root-level rules with those from the legacy bundle.

```text
research_workspace/
  docs/             This packet, audit reports, formal analysis protocols, decision logs
  configs/          Path aliases, parameters, environment records; no identifying information
  manifests/        Anonymized child, visit, recording, event, and matching tables
  scripts/          Reproducible scripts
  results/          Statistical tables and run logs
  figures/          Figures generated from the current data
  tests/            Small examples and necessary checks

raw_data/           Keep in its original location; read-only
private_mapping/    Identity mappings, source paths, original clinical tables; do not return
derived_data/       Epochs, features, and caches, separate from original files
```

Configure dependencies for the actual file formats and lock the versions used. The initial helper script requires only Python 3.10 or later. Subsequent readers may require MNE, NumPy, pandas, SciPy, openpyxl, or other format support. Do not install a full GPU software stack in advance for the legacy model.

For any prediction task evaluating generalization to new children, split data by child. A separately designed within-child decoding task should use isolated time blocks and explicitly state that it evaluates only within-child performance. Fit standardization, imputation, feature selection, outcome-driven time windows, model selection, and hyperparameter selection using training data only. When tuning is needed, use nested validation to avoid using the same validation results both to choose a method and to report its performance; see the [scikit-learn nested cross-validation example](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

## 7. Terminology

| Abbreviation | Meaning and use in this project |
|---|---|
| HA | Hearing aid; HA children are hearing-aid users |
| CI | Cochlear implant; CI children are cochlear implant recipients |
| NH | Normal hearing; a reference population with a limited sample size |
| Bimodal | A CI in one ear and an HA in the other; a device configuration |
| EEG | Electroencephalography; recorded brain electrical signals |
| ERP / CAEP | Event-related potential / cortical auditory evoked potential; trustworthy stimulus timing is required |
| P1 | An early positive auditory response component; verify its time window and morphology in children rather than fixing it at 100 ms |
| MMN | Mismatch negativity; first verify the relevant experimental design and condition definitions |
| PTA | Pure-tone average hearing threshold; specify frequencies, ear, unaided/aided condition, and measurement unit |
| MUSS | Meaningful Use of Speech Scale; concerns everyday speech use |
| IT-MAIS / MAIS | Infant-Toddler Meaningful Auditory Integration Scale / Meaningful Auditory Integration Scale; distinguish the instrument versions |
| SIR | Speech Intelligibility Rating; preserve its ordinal interpretation |

"Device-use duration in months" means elapsed time using the device. "Daily device-use hours" describes the daily amount of use; keep these variables separate. Children using hearing aids may have had residual auditory experience before their first fitting, so device-use duration must not be treated as their total auditory experience.
