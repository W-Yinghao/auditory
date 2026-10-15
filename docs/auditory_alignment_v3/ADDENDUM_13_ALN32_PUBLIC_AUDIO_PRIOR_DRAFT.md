# ALN3 ADDENDUM_13 · ALN32_PUBLIC_AUDIO_PRIOR — DRAFT (not frozen, nothing registered)

Status 2026-10-15 02:40: draft for the user's steer. No plan rows, no code, no compute. Freezing happens only after the decisions in §2
are settled; then code → synthetic tests → one-unit probe → release, as for ADDENDUM_07–12.

Package: docs/05 (main-method build: sound-supervised group prior), configs/experiments.yaml `ALN32_PUBLIC_AUDIO_PRIOR`
(targets fau, dtu, federici, private_bdf; sources verified existing public speech + SparrKULee; variants target_from_scratch,
audio_pair_pretrain, cross_person_pretrain, joint_pretrain; objectives NCE, CS_SINGLE; all target outer folds and content splits;
pretrain_then_adapt; no target test identity or content in a donor), configs/seed_and_reuse.yaml core role
`private_transfer` (private_local_native → private_public_audio_prior; seeds 3407 / 3413 later). Data: PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md
(SparrKULee 85 participants, 159 h, ≈ 70 contents; data-contract probe passed).

## 1. Question

Does speech-supervised pretraining on other listeners (public cohorts + SparrKULee) give a lag-local model that adapts better to a
target cohort than training on the target alone — and is the gain from audio–EEG pairs, from same-stimulus cross-person agreement, or both?

## 2. Decisions needed (recommended default first)

| # | decision | recommended default | alternative / cost |
|---|---|---|---|
| D1 | common input rate | **64 Hz for every source and target in this block** (SparrKULee native; the field's standard; 159 h fits in memory). target_from_scratch is retrained at 64 Hz too, so the comparison is within one contract; native-rate A_LOCAL stays as context, not as the reference | 128 Hz: upsample SparrKULee (no content above 32 Hz), memory ×2 |
| D2 | sound representation shared by all sources | **broadband envelope only** (the one feature every source has; Federici has nothing else; same envelope definition recomputed for all stimuli where audio exists, cached envelope otherwise) | add log-mel / spectral features: needs audio for every source (not Federici) → would split the donor pool |
| D3 | channel identity | **name-indexed input map**: one input weight per electrode name shared across sources (10-20 aliases mapped); a target channel no donor has (FAU F9/F10, Federici FT9/FT10) starts at zero | per-cohort input maps: simpler, but zero-shot impossible |
| D4 | donors per target (leave-target-out) | **SparrKULee + every other public cohort's training participants**; target fau → SparrKULee + dtu + federici; dtu → SparrKULee + fau + federici; federici → SparrKULee + fau + dtu; private → SparrKULee + fau + dtu + federici (Federici verified humans only, as in ALN2). One pretrained model per target × variant × objective | SparrKULee only: cleaner "public prior", smaller and single-language |
| D5 | cross-person positives | **same content key × same physical time anchor (±0 samples on the stimulus clock) × same presentation version, different participant, same cohort**; competing-talker trials only with the same attended stream; negatives = other anchors in the batch, same-content anchors within ±2 s masked out; the constraint acts on a shared 32-d projection only (person / task heads kept) | full-embedding constraint (docs/05 warns against) |
| D6 | adaptation and evaluation modes | per target cell: (a) zero-shot (pretrained encoder + shared envelope head, no target fitting; not for private, whose head is a class head), (b) unlabeled input adaptation = per-participant re-centring of the EEG covariance on the target's own training data (no sound labels), (c) labeled adaptation = full fine-tune with the target's A_LOCAL recipe (main row). target_from_scratch has (c) only | add PEFT adaptation: one more row per cell |
| D7 | pretraining budget | **equal update count across the three pretrain variants** (joint = same steps, two losses); fixed in advance, e.g. 30 epochs-equivalent of SparrKULee windows with early stopping on a donor-only held-out group | budget sweep: no (docs/05: no full hyper-parameter cross) |

## 3. Matrix (seed 3401; per objective NCE and CS_SINGLE)

- Pretraining: 4 targets (leave-target-out donor sets) × 3 pretrain variants × 2 objectives = **24 pretraining units**.
- Adaptation: 30 target cells per objective (FAU 10, DTU 10 = subject × content folds; Federici 5; private 5 outer folds) ×
  4 variants × 2 objectives = **240 adaptation units**; zero-shot and unlabeled-adaptation scores are computed inside the same units.
- Private: encoder transfer only, class head retrained (docs/07), E_PUBLIC_TRANSFER tensor-map bookkeeping (loaded / new / missing keys and
  parameter fractions recorded).
- Seed panel (private_transfer role, 3407 / 3413): registered after the seed-3401 analysis code is frozen, as for ADDENDUM_11.

Cost (rough, lag-local encoders): pretraining 24 × 1–3 GPU-h; adaptation 240 × ≈ 5–15 min → ≈ 50–100 GPU-h at the current 10-GPU cap,
i.e. 5–10 h of the fleet if run at the front of the FM queue, longer if it queues behind wave 1 / panel.

## 4. Engineering before the freeze can be executed

1. `sparrkulee.py` loader → our Cohort format (64 Hz EEG, envelope bank, segments with content key / presentation / stimulus clock;
   3 flagged runs out; `*.data_dict` never opened).
2. Down-sampling of FAU / DTU / Federici / private EEG and envelopes to 64 Hz with one filter (D1), cached once.
3. Name-indexed input map (D3) and the cross-person batcher (D5); pretrain runner; adaptation runner reusing the A_LOCAL recipe and the
   E_PUBLIC_TRANSFER tensor map; registry group `public_prior32` (new files only; no hashed file edited).
4. Synthetic tests: leave-target-out (no target identity / content in any donor batch), key rules (no self pairs, masked same-content
   neighbours), zero-shot path uses no target fitting, tensor-map report.
5. Probes: one pretraining unit (short budget) + one adaptation unit per target type (public, private) on a 16 GB card.

## 5. Analysis (to be frozen with the addendum)

ADDENDUM_05 machinery on identity-level paired differences; per target × objective: (i) audio_pair − scratch, (ii) cross_person − scratch,
(iii) joint − scratch, (iv) joint − max(audio_pair, cross_person) (complementarity); separately for modes (a)/(b)/(c); family max-t per
target. Model selection never uses hearing-group differences, age slopes or clinical significance (docs/05). A gain that only appears
with more data or capacity is reported as such.
