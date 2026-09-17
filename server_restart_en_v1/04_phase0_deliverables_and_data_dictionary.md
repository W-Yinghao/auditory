# Phase 0 Deliverables and Data Dictionary

Purpose: Ground the next discussion in the actual data on the server. The filenames below are suggested deliverables. `templates/` contains empty headers, **not completed data tables**.

## 1. First-Round Deliverables

| Deliverable | Minimum contents | Meaning of completion |
|---|---|---|
| `phase0_report.md` | Verified facts, differences from legacy results, feasible questions, limitations, and one priority next step | Every judgment points to an inventory, figure, record, or explicit gap |
| `environment.json` | Python and reader versions, CPU, memory, free disk space, processing volume, and error summary | Actual reading capability and resource limits are documented; no model installation is needed |
| `file_inventory.csv` | Per-file anonymized ID, directory alias, possible format, size, and optional hash | Files in the specified scope have been enumerated; this does not mean EEG was successfully read |
| `participant_index.csv` | One row per child, identity-confirmation status, sources, and cross-cohort relationships | Confirmable participant counts are evidence-based; unknown identities are not presented as new children |
| `visit_index.csv` | One row per confirmed or candidate visit, date evidence, device-use duration, and age | Visits and acquisition recordings are separated; unknown dates are explicitly marked |
| `recording_index.csv` | One row per acquisition, child/visit, device, protocol, data version, and matching status | Multiple files can be grouped into acquisitions; processed copies do not count as new acquisitions |
| `files_to_recordings.csv` | File ID, recording ID, file role, processing version, and pairing status | Data, event, header, segment, and copy relationships are traceable |
| `clinical_link.csv` | Links between acquisition and clinical records, time gaps, and evidence status | A scale record for the same person can be distinguished from a concurrent scale record for that EEG acquisition |
| `event_dictionary.csv` + `event_audit.csv` | Event definitions and evidence within each protocol; per-record counts, out-of-range/duplicate events, sources, and status | Event meanings are confirmed or the reason they remain missing is explicit; labels are not guessed from frequency |
| `clinical_audit_summary.csv` | Ranges, units, missingness, distributions, repeats, versions, and reconciliation with legacy results | Records and children are counted separately; return aggregate results only |
| `qc_summary.csv` + figures | Per-acquisition quality, reading status, representative waveforms and spectra, events, and preliminary averages | The inspected and uninspected scope is clear; leave unperformed checks empty |
| `cohort_support.csv` | Record and child counts by population x condition x device state x clinical-match status | It is clear which comparisons have sufficient, comparable data |
| `questions_to_resolve.csv` | Question, evidence already checked, affected analyses, next action, and status | Unresolved questions do not become implicit assumptions |

Save the configuration, time, script version, and output checksums for each run. Full raw reader-exception messages must remain in private server logs. Shareable reports should contain only anonymized recording IDs and error categories.

## 2. Meaning of the Five Levels

`Child -> visit -> acquisition recording -> file`; an acquisition recording may also contain multiple `stimulus events`.

- The child is the independent unit for population counts and cross-child validation. The same child may appear across visits, conditions, or cohorts.
- A visit is an assessment or clinic time point supported by evidence. Keep it as a candidate when timing evidence is unavailable; do not infer a visit from file ordering.
- An acquisition recording is one actual acquisition, which may have multiple data segments, event files, and postprocessing exports.
- A file is a storage unit. It may contain an entire acquisition, only companion information, or an averaged waveform.
- A clinical record is a measurement unit in a scale or audiology table. It may be concurrent with EEG or occur at a different time; do not assume a one-to-one relationship.

All tables should record `evidence_ref` or the relevant evidence status. Evidence references must use de-identified entry IDs, such as protocol-item IDs, file IDs, or private server registry indices, rather than original paths or personal names.

## 3. Key Fields

| Field | Meaning / unit | Rule |
|---|---|---|
| `participant_id` | Stable anonymized child ID | Reuse a legacy ID only after verifying its correspondence to the original table; use one master ID for the same child across cohorts |
| `identity_status` | confirmed / candidate / unresolved | For unresolved identities, report confirmable counts and the number of unknown entries; do not invent a "true participant count" |
| `visit_id` | Visit ID | Do not derive actual timing directly from device-use group labels |
| `visit_time_status` | verified / inferred_order_only / unknown | Keep exact dates private; reviewed relative day counts and source status may be shared |
| `age_months` | Age at measurement, in months | Verify whether this is age at EEG, scale assessment, or initial registration |
| `device_use_months` | Elapsed use of the relevant device, in months | Record what the starting point means, device changes, and the source; do not confuse it with daily hours |
| `daily_use_value`, `daily_use_unit` | Daily use amount and unit | The source field may contain codes, ranges, or text; do not automatically interpret values as hours when units are unclear |
| `recording_id` | Actual acquisition ID | Processed/exported copies from the same acquisition share this ID; create another ID only for a genuinely new acquisition |
| `data_version_id`, `parent_file_id` | Processing version and source-file relationship | Record them in the file-to-recording table; one version may contain several companion files |
| `data_level` | raw / preprocessed / epochs / evoked / unknown | Averaged waveforms cannot support trial-level analyses; do not combine counts across data levels |
| `protocol_id` | Acquisition/stimulus protocol ID | The same "pure tone" label does not guarantee the same protocol |
| `device_configuration` | NH / HA / CI / bimodal / unknown | Retain the evidence for the original grouping; do not infer severity from device type |
| `device_state` | on / off / unaided / mixed / unknown | Define per recording and, when needed, per block; unknown does not default to on |
| `stimulus_level_value/unit` | Stimulus intensity and unit | Keep dB SPL, dB HL, and dB SL separate; retain presentation method and ear side |
| `sampling_rate_hz` | Sampling rate | Distinguish the original rate from the current file rate; do not guess the original rate |
| `n_eeg_channels`, `reference` | Actual number of EEG channels and reference | Separate auxiliary/trigger channels; verify the source of the 32 -> 22 channel selection |
| `duration_s`, `n_epochs` | Continuous acquisition duration / number of epochs | Epoch count x window length cannot substitute for actual acquisition duration |
| `event_code_token` | De-identified event value or its stable token | If free-text annotations contain identifying information, retain that text only in the private mapping |
| `event_role` | standard / deviant / tone_1... / response / boundary / unknown | Confirm using protocol and timing evidence only; do not map automatically from common codes or probabilities |
| `clinical_row_id` | Anonymized source-record ID for a clinical measurement | It must support tracing back to the original table without including source names |
| `clinical_match_status` | confirmed_concurrent / confirmed_nonconcurrent / candidate / none | A scale assessment from the same child at a different time is not a concurrent label |
| `eeg_clinical_gap_days` | Time difference between EEG and assessment | Calculate only from reliable dates; define the sign convention in the dictionary, preferably scale-assessment date minus EEG date |
| `pta_definition` | Frequencies, ear side, unaided/aided status, and measurement method | Better-ear values, bilateral averages, and stimulus-ear values are different measures; retain the original frequency-specific thresholds |
| `scale_version` | Instrument version | Do not merge IT-MAIS and MAIS by default; verify score ranges and conversions |
| `qc_status` | not_read / read_error / reviewed / usable_for_task / unusable_for_task / pending | Specify the task to which the status applies; a weak response is not automatically technically bad data |

`recording_index.csv` must contain only one row per actual acquisition. Its `data_level` and reading parameters describe the main data version selected for inspection in the current round. Register other versions in `files_to_recordings.csv` using `data_level`, `data_version_id`, and `parent_file_id`. Do not duplicate acquisition rows and counts because several exports exist.

Keep unknown numeric values empty and explain them using status fields. Do not substitute 0, normal, or no events for unknown. A score of 0, a duration of 0 months, and a count of 0 events all have actual meanings.

## 4. Checks When Rebuilding the Clinical Tables

1. Multiple sheets in legacy workbooks may repeat the same records. First recover relationships between sheets, then identify the canonical source; do not concatenate them directly.
2. Check not only matching names but also source rows, device-use duration, age, audiology, and scores. Compare missingness and conversions in the original and legacy derived tables, and record reasons for discrepancies.
3. Check logical consistency among age, device-use months, and inferred fitting age; whether differences are stable across repeated records; and whether records with identical age and device-use months reflect retests, repeated form completion, or duplicate exports.
4. Check the distribution of SIR levels and their joint distribution with continuous device-use months. A high correlation does not by itself make the scale unusable.
5. Check IT-MAIS/MAIS and MUSS versions, raw scores versus percentages, the proportion at the maximum, missingness, and unusual score increments. Report both record and child counts for every distribution.
6. Check the original units and nonnumeric entries in daily-use fields. Do not treat every failure to parse a nonnumeric value as an absent record.
7. Check hearing-threshold ear side, frequency, units, and the nature of aided measurements; determine whether assessment timing and the assessor can be identified.
8. Freeze the current cleaning rules before generating a new set of tables, and retain legacy tables for reconciliation. Do not overwrite original files or legacy results.

## 5. Six Figure Types for the First Round

| Figure | Contents | Required annotations |
|---|---|---|
| Data flow | Files -> acquisitions -> clinical matches -> confirmable children | Separate counts; show unmatched and repeated items separately |
| Coverage matrix | Children x stimulus/device state/visit | Anonymized IDs; distinguish confirmed and unknown status |
| Events and conditions | Timing, intervals, event-code counts, device states, and duration distributions | Do not name unknown events standard/deviant in advance; show blocks and timing anomalies |
| EEG quality | Representative raw segments, PSD, event-locked averages, and per-record quality | Units, reference, filtering, trial counts, and inspection scope; do not show only the best records |
| Age and use history | Age x device-use months, marking device state and original/processed version | State whether observations are record-level or one index record per child; do not label the plot as evidence of "causal separation" |
| Scales | SIR x device-use months; MUSS and IT-MAIS/MAIS distributions and ceilings | Use actual data and separate instrument versions; provide n records, n children, and missing counts |

The first round does not require an EEG-scale correlation heatmap or a neural-network performance table. If events remain unconfirmed, label preliminary averages "alignment pending validation." Do not plot them if alignment cannot be established.

## 6. Using the Lightweight Inventory Script

Before running the command below, replace the example paths with actual directories. Supply `--root` once or repeat it for multiple roots. A and B are neutral directory aliases; they do not mean the script has verified the populations.

```bash
python scripts/first_pass_inventory.py \
  --root A=/actual/raw/cohortA \
  --root B=/actual/raw/cohortB \
  --out /actual/work/runs/p0_inventory_001 \
  --private-out /actual/private/p0_inventory_001
```

This step only enumerates files and metadata. It does not load EEG waveforms, read clinical contents, recover events, or match children. Outputs:

- May be returned after review: `file_inventory.csv`, `errors.csv`, and `summary.json`.
- Must remain on the server: `file_path_map.csv` and `errors_private.csv` in the private directory.

Output directories must be new and must not overlap the raw-data directories or each other. The script refuses to follow symbolic links or Windows junctions. If raw data are accessed through a link, explicitly provide the real target directory. Skipped links are counted; "scan completed" refers only to the scope of regular files reachable without following links.

The default does not read file contents. If file-level SHA-256 reconciliation is required, run in new output directories and add `--sha256`. Fully hashing large files increases I/O. Matching hashes establish identical contents, not the same child or visit.

Exit code 0 means scanning of the agreed scope completed; 1 means the scan is incomplete; 2 means configuration or output failure. A successful file inventory does not mean all of P0 is complete. The server should implement event reading and EEG quality checks after confirming the formats.

On Linux, private directories are created with permissions 0700 and files with 0600. Windows also depends on actual account permissions. This helper script is not a general-purpose de-identification tool for arbitrary outputs. Do not package and return the entire private-results directory.

The server may refer to the legacy `inventory_raw_eeg.py` when developing readers. However, its event labels, participant-count inferences, or name-replacement outputs must not be treated directly as confirmed facts. See `03_legacy_review_and_corrections.md` for the reasons.

## 7. Closing Format for the Report

Complete the end of `phase0_report.md` with:

- The currently most reliable data subset: its definition, child count, record count, match count, and reasons for exclusion.
- The highest-priority question: one sentence and the data evidence supporting it.
- Conclusions that cannot currently be supported, such as individual rehabilitation trajectories, an MMN mechanism, or cross-child generalization, with reasons.
- Specific tasks for the next round: required inputs, outputs, proposed primary measurements, the most important comparison, and its conditions.
- Missing materials: list only items that cannot be resolved from server files and existing materials, and identify the analysis each gap would block.

For the next return package, provide the report, anonymized aggregate tables, and the figures above. Do not include raw EEG, clinical name tables, or source-path mappings.
