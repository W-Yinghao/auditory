# Public auditory pretraining data — receipt (SparrKULee, 2026-10-15)

Package docs/05 asks for a download log that states participants, unique stimulus content, recorded hours, licence, what was obtained and
what was not. User approved the download on 2026-10-14 ("可以下载"). This file records what the server holds. No model has been trained on
it, and no registration (addendum) exists yet.

## Source and integrity

- NEMAR `nm000238` v1.0.0 (BIDS 1.9.0; "SparrKULee … Containing the EEG of 85 Participants", Accou et al., Data 2024, 9, 94).
- Downloaded by `private/sparrkulee/download_nemar.py` (Slurm 1040219, 2026-10-14 17:5x → 2026-10-15 01:41; resumable). Each file was
  checked against the mirror's checksum: 4,082 / 4,082 files present and verified, 135.83 GB
  (`private/sparrkulee/download_receipt.json`, per-file log `download_log.jsonl`).
- Location: `/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0` (the authorised shared volume; not the training disk).
- Licence (dataset_description.json): CC BY-NC 4.0 for the EEG; the stimuli may only be used for non-commercial purposes. Use is
  research-only; derived weights inherit the non-commercial restriction.
- Nothing from the dataset is executed: its `code/convert_accou2023.py` is not run, and the 73 pickled `*.data_dict` stimulus files are
  not loaded (unpickling runs code). Only `.npy` arrays (`allow_pickle=False`), JSON and TSV are read.

## What was obtained (inventory, `private/sparrkulee/inventory.py`, Slurm 1040733)

| item | value |
|---|---|
| participants in `participants.tsv` | 85 (all normal hearing, ≤ 30 dB HL; native Dutch/Flemish; 3-year age bins only) |
| participants with preprocessed EEG | 85 |
| participants whose raw EEG is access-restricted | 5 (sub-019, 020, 021, 022, 026: raw BDF returns HTTP 403 upstream; their preprocessed EEG is in the mirror) |
| preprocessed EEG recordings | 666 `.npy`, each 64 channels × T, float64, 64 Hz (checked against raw BDF durations) |
| preprocessed EEG hours | 159.1 h (paper: 168 h; the difference is not explained by the 5 restricted participants, whose preprocessed files are present) |
| raw EEG | 659 `.bdf.gz`, BioSemi 64 ch, 8,192 Hz, CMS/DRL reference, 50 Hz mains; raw → preprocessed map lists 668 runs, all with output |
| stimulus envelopes (preprocessed) | 72 at 64 Hz (35 audiobook parts, 37 podcasts), 15.9 h in total; 2 of them are `audiobook_1_{1,2}_shifted` presentation variants of the same content, so ≈ 70 distinct contents |
| raw stimuli | `stimuli/eeg/*.npz.gz` (204 files) plus `.apx` / `.xml` presentation files |
| participants per stimulus | min 1, median 6, max 78; 68 of 72 stimuli were heard by ≥ 2 participants (cross-person same-stimulus keys exist) |
| flagged unalignable runs (README) | sub-006 shortstories01 run-06, sub-017 shortstories01 run-03, sub-048 varyingStories05 run-04 — to be excluded |

Recording hours are not stimulus content: the 159 h of EEG cover ≈ 16 h of distinct audio, heard by many listeners (a story repeated by
many participants is not more stimulus content).

## Not obtained / not yet checked

- Raw EEG of the 5 restricted participants (upstream permission needed; not requested).
- Mel / spectral stimulus features are not shipped as arrays; they would be computed from the raw stimuli by our code.
- EEG–envelope alignment: preprocessed EEG runs are slightly longer than their envelopes (e.g. 50,752 vs 48,747 samples). The start
  alignment and the trailing samples must be checked in a probe before any training row is registered.
- Channel mapping to FAU / DTU / Federici / private montages: not yet done (docs/05: explicit channel identity or electrode positions).
- Stimulus overlap with the target cohorts (hash / segment check across all sources and targets): not yet done.

## Data-contract probe (2026-10-15 02:07, `private/sparrkulee/data_contract_probe.py`, Slurm 1040738, read-only)

| check | result |
|---|---|
| A channels (by name, legacy aliases mapped) | DTU 64/64, private 20/20, FAU 27/31 (missing F9, F10, TP9, TP10), Federici 28/32 (missing FT9, FT10, TP9, TP10) |
| B preprocessed channel order = raw BDF label order | channel-correlation structure of one run: identity order r = 0.72; 200 random orders max 0.10 → order matches |
| C EEG index 0 = envelope index 0 | 170 runs (2 per participant, 85 participants; 3 flagged runs excluded): envelope–EEG cross-correlation peak median +0.14 s, 81% of runs in [0, 0.4] s, 0.6% near the end-aligned lag; the pooled curve peaks at +0.05–0.13 s (normalised S 0.54 at 62 ms vs 0.13–0.18 at −1 s / −0.25 s) → start-aligned. The other 19% of runs peak anywhere from −4.4 to +37 s, at no common offset; no run is dropped for this (docs/05: records are not selected by score) |
| D stimulus overlap with targets | 1,005 SparrKULee 20-s windows vs FAU (32 streams), DTU (582 trials), Federici (141 distinct envelopes), 2–8 Hz: max local r 0.39 / 0.41 / 0.43, no window ≥ 0.7. Positive control (audiobook_1_x_shifted vs audiobook_1_x): median r 0.98, min 0.97, all at the right offset; the same windows against the podcasts give at most 0.39 → no overlap. Private stimuli were not part of this public probe |
| E cross-person keys | 663 runs with events: presentation versions in_noise SNR 100 dB (609), no_noise (44), in_noise −4 dB (5), in_noise +2.5 dB (5); every content has a single presentation version, so the (content, presentation) key = content key: 73 keys, 67 heard by ≥ 2 participants (median 6, max 77) |

## Next (in order; each before any compute that uses the data)

1. ~~Data contract and probe~~ done (above).
2. Frozen addendum `ALN32_PUBLIC_AUDIO_PRIOR` for the docs/05 matrix (target_from_scratch, public_audio_pair_pretrain → target_adapt,
   same_stimulus_cross_person → target_adapt, joint → target_adapt), with leave-target-out donors, then a probe, then the fleet.
