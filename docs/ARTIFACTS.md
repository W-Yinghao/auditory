> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Audit artifacts and execution

Phase 1 has subsequently been executed. See [PHASE1_ARTIFACTS.md](PHASE1_ARTIFACTS.md) and [phase1_report.md](phase1_report.md) for the latest reconstructed epochs and measurement results. The following table describes Phase 0.

Keep the initial inventory's private file map for local reproduction: a fresh inventory generates new opaque file IDs. Scripts are snapshot audit stages with explicit output directories, not yet a packaged production pipeline. Use new run directories for reruns. Sources and the supplied restart package remain unchanged.

| Current artifact | Content | Successful Slurm job |
|---|---|---:|
| `results/inventory_001/` | Complete file inventory; old-environment probe then failed | 994914 |
| `results/discovery_001/` | Actual environment, branches, workspace hashes and inventory tests | 994919 |
| `results/probe_001/` | Initial schemas; workbook/DOCX extracts are private | 994921 |
| `private/layout_examples.json` | Private format examples | 994929 |
| `results/other_eeg_001/` | SET/BDF/EGI headers, SET epochs, BDF annotations | 994941 |
| `results/supporting_001/` | PDF extraction, archive listing, JSON/text inventory | 994949 |
| `results/mff_001/` | MFF epochs, categories, events, export index | 994937 |
| `results/mff_recovery_001/` | Empty-track recovery and candidate history graph | 995058 |
| `results/mff_validation_001/` | Declared EEG binary and epoch/block consistency | 994985 |
| `results/egi_events_001/` | Every raw event channel and both segmented headers | 994981 |
| `results/clinical_003/` | Corrected groups, candidate identities, scales | 994974 |
| `results/linkage_001/` | Participant/recording/clinical candidate links, BDF clocks | 994979 |
| `results/processed_link_001/` | SET to raw candidate links and code sequences | 995070 |
| `results/signal_001/` | Full readable SET QC, epoch hashes, MNE cross-checks, BDF previews | 994967 |
| `results/extra_002/` | All vendor JSONs and 13 MFF previews | 995062 |
| `results/overview_001/` | Flow, MFF counts, source issues, candidate FDT | 995066 |
| `results/assets_001/` | Visual asset inventory and directory condition clues | 995069 |
| `results/descriptive_002/` | MAT audit, HA age/duration plots and repeat counts | 995083 |
| `tests/test_epoch_readers.py` | Four reader checks and restart checksums | 995057 |
| `results/visual_review_001/` | All PNG hashes and private contact sheets; AVI decoder unavailable | 995113 |
| `results/video_001/` | Both AVI headers/chunk counts; FMP4 sampled-frame decoding unavailable | 995118 |
| `results/finalization_001/` | Canonical MFF events, structural quarantine and output verification | 995112 |

Clinical 001/002, extra 001 and interrupted descriptive 001 are superseded. Discovery errors can include AppleDouble files and empty event tracks; use later format-specific reading statuses. The extra MFF directory is a wrapper with subdirectories, not an empty acquisition.

## Main tables and scopes

- `manifests/file_inventory.csv`: every regular file; a file is not a child.
- `manifests/participant_index.csv`, `recording_index.csv`, `clinical_link.csv`, `visit_index.csv`: **BDF/vendor branch only**, with candidate status. Candidate acquisition dates are not verified clinical visits.
- `manifests/mff_export_index.csv`: MFF processing exports, separately counted.
- `results/mff_001/epoch_ledger.csv`: 194,860 storage epochs; use data_level to distinguish blocks/trials/averages.
- `results/mff_001/category_segment_ledger.csv`: category entries and historical good/bad/fault information.
- `results/other_eeg_001/epoch_ledger.csv` and `results/signal_001/epoch_signal_qc.csv`: 10,965 existing SET epochs with metadata and numeric QC.
- `results/egi_events_001/segmented_epoch_ledger.csv`: six segments from two exports; average status remains a provenance question.
- `results/mff_recovery_001/provenance_edges.csv`: candidate parent relations; components are not children.
- `manifests/questions_to_resolve.csv`: evidence limitations and feasible next actions.

## Event recovery

Use `results/finalization_001/mff_event_ledger.csv`. It excludes the 70 revisited containers from the first MFF event ledger and replaces their rows with recovered rows. The canonical count is 1,858,215. Do not concatenate unfiltered ledgers. Finalization verifies strictly increasing event indices within each container/track, validates per-container recovery counts and retains only an explicit whitelist of numeric event-structure keys in the non-private MFF metadata. Original metadata backups remain under `private/finalization_001/`.

The recovered ledger now uses file IDs instead of track basenames and shares the canonical schema. `manifests/mff_export_index.csv` adds `canonical_event_entries`, final event-reader status and topology status; its original `n_events`/`read_status` columns retain first-pass meanings. `mff_quarantine.csv` identifies structurally problematic versions. Structural success does not establish signal usability or valid clinical labels. Event native units use the independent topology reader's supported time precision; unresolved units remain unknown.

`verification.json` records final checks and `artifact_checksums.csv` identifies the code, documentation, manifests, result summaries and canonical ledger at finalization. Source EEG payloads were not fully hashed; no claim of a complete immutable raw-data snapshot is made. These pseudonymized artifacts are for local research and are not a public release.

## Figures

Start with `figures/overview_001/`, `figures/descriptive_002/`, `figures/mff_002/` and the clinical 003 scale figure. `figures/signal_001/` has per-SET and three BDF previews; its original caption “Unfiltered stored signal” means no **additional** filtering by the preview script. Sources can already be preprocessed. Current overview/MFF figures use corrected captions. Native-unit MFF previews are not calibrated biomarker measurements. Source screenshot coverage and the video decoding limitation are detailed in `docs/visual_review.md`.

## Execution and limits

CPU jobs requested 1–2 cores and 3–12 GB; no GPU jobs were submitted. Source data were not renamed or repaired in place. Slurm accounting was unavailable, so historical MaxRSS and billable usage are not reported. Existing user job 994815 was not changed. Earlier failed environment/schema/plot checks remain in private logs.

EEGLAB event handling follows its official [data structures](https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html). EGI binary layout was checked against the official [header reader](https://raw.githubusercontent.com/sccn/eeglab/develop/functions/sigprocfunc/readegihdr.m) and [data reader](https://raw.githubusercontent.com/sccn/eeglab/develop/functions/sigprocfunc/readegi.m). Local MNE 1.11.0 source was used for declared MFF EEG streams and block validation.
