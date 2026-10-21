# ALN4.2 R3 external slot: MindMix readiness check (2026-10-21)

This is a readiness check, not the comparison. No external test score was computed, and no test person or test-content
window was scored. All computation ran as CPU `srun` steps inside 1047358 (no GPU job, no `scontrol`, nothing
cancelled). The MindMix repository at pin `98445f36` is unmodified; no project code was edited. The session ran
14:11–15:00 CEST, about 50 min of the 4 h bound.

## Inherited decision

- `private/auditory_alignment_v3/aln41/intake/EXTERNAL_SLOT_DECISION.json`
  - SHA256 `5e78e2aa14dedc772a1fbc427923875e5e108757e56f5b5fe0380b5314989e40`
  - Decided 2026-10-21T02:21:24+02:00, before any new target results.
- Rule: run complete MindMix (released fusion checkpoint plus the official `universal_eeg_finetune.py` CALRA
  downstream) if its readiness gates pass within one bounded session of at most 4 h. If any gate fails, use the fixed
  fallback Transformer-CLIP.
- The Stage-1 EEG-only asset failure (`STAGE1_GATE.json`) concerns a different asset and does not carry over.

## Verdicts

| Gate | Verdict | One-line evidence |
|---|---|---|
| 1 Asset | **PASS** | Full-file SHA256 equals the LFS oid `fe2603e3…5026`; 1,221,696,491 bytes |
| 2 Weights | **PASS** (one mechanical key rename) | 509/511 checkpoint tensors loaded bit-exactly (EEG 244, audio 211, eeg_proj 4, audio_proj 4, CALRA 46). The official loader alone silently misses 2 audio tensors in this env |
| 3 Input contract | **PASS** | 200 Hz / 2 s / 64 ch / 16 kHz contract documented (paper App. A.2 plus code). Raw target/masker wavs identified and onset-aligned. The official DTU loader and `train_epoch` run on our export |
| 4 Blind scoring | **PASS** (mechanical) | Order-symmetrised per-sample margin: exactly swap-antisymmetric, batch-invariant to ≤2.9e-6. The official scorer is neither |
| 5 Forward + backward | **PASS** | Official contrastive step on 4 real fit-role windows: finite gradients in every trained module, AdamW step changes all of them |

**Route implied by the pre-registered rule: A, MindMix released full architecture with common-protocol task adaptation.
Not the Transformer-CLIP fallback.** The disclosures in §6 do not change the route: routes may not be chosen on
expected scores. They must, however, be reported with the external result.

## 1. Asset

- Downloaded through the Git LFS batch API over HTTPS (`fetch_fusion_lfs.py`, run as a Slurm step), from
  `github-cloud.githubusercontent.com`, in 202 s.
- Saved to `/projects/EEG-foundation-model/auditory_public/foundation_models/github__CookieMikeLiu__MindMix@98445f3/lfs/best_model_loss_0.0909.pth`,
  next to `lfs/v2.4_large.pth`.
- Hash check: streamed and re-read SHA256 are both `fe2603e3ee2c95fa2e1e012710a2774e70b6dd5582560773aafd20b295f15026`,
  equal to the pointer oid. Size equals the pointer size.
- Receipt: `FETCH_FUSION_RECEIPT.json`. The repo working tree is clean (`git status` empty).
- The official code also instantiates `facebook/wav2vec2-base`. It was fetched at revision `0b5b8e86…`:
  - `config.json` SHA256 `4937977e…`
  - `pytorch_model.bin` SHA256 `3249fe98…`
  - Stored in `/projects/…/auditory_public/derived/hf_cache/hub`, with `refs/main` pinned so offline lookup works.
  - Receipt: `FETCH_WAV2VEC2_RECEIPT.json`.
  - Every audio tensor is afterwards overwritten from the fusion checkpoint.

## 2. Weights and key audit (`gate2_weights.py` → `GATE2_KEY_AUDIT.json`)

**Unpickling was done safely.**
- The pickle opcode scan found only `argparse.Namespace`, `OrderedDict`, `FloatStorage` and `_rebuild_tensor_v2`.
- The checkpoint was loaded with `weights_only=True`. The official `load_trusted_checkpoint` (`weights_only=False`) was
  swapped for this loader at runtime only; keys and values are unchanged.

**Checkpoint contents.**
- Top-level fields: `model_state_dict` (511 tensors), optimizer, scheduler, epoch 22, loss 0.09086.
- Stage-2 args: `labram_base_patch200_200`, `input_size` 400, `fusion_method` 'clara' (sic), Stage-2 init from the
  unreleased `checkpoints/v2.0.pth`.

**The EEG part matches the pinned factory.**
- 12 blocks, embed 200, 10 heads (q_norm dim 20), `q_bias`/`v_bias`, `time_embed` [1,16,200], `fc_norm`.
- No `pos_embed` tensor. This agrees with the code, which forces `pos_embed=None`.

**Audit A: official loader, as is.**
- 507 tensors loaded.
- `audio_model.encoder.pos_conv_embed.conv.weight_g` / `weight_v` are reported as "Skipped". torch ≥2.1 and
  transformers 5.2 name them `parametrizations.weight.original0/1`, so they stay at the HF wav2vec2-base values.
  That is 4,718,720 parameters, 2 audio backbone tensors.
- On its own, Audit A would fail the pre-registered "zero missing backbone tensors" criterion.

**Audit B: official loader plus a pure key rename of the same two tensors.**
- 509/511 tensors loaded; 101,754,136 of 101,787,291 parameters come from the checkpoint.
- The effective conv weight equals `_weight_norm(v, g, dim=2)` from the checkpoint exactly (max |diff| 0.0).
- Not from the checkpoint:
  - `classifier.*` (4 tensors). This task head is never reached by the AAD path: `clip_train` returns before it and
    `forward_contrastive` does not use it. The checkpoint's Stage-2 256→1 head is excluded.
  - `clip_loss.logit_scale`. It is not saved and is initialised at ln(1/0.07) = 2.659.

## 3. Input contract (code, paper App. A.2/A.3, DTU44 evidence)

### EEG

- **Code:** `input_size` 400; `rearrange 'B N (A T) -> B N A T', A=2, T=200`, i.e. 200 Hz × 2 s.
- **Paper A.2:**
  - Band-pass 1–40 Hz, zero-phase 4th-order Butterworth.
  - Resample to 200 Hz.
  - Non-overlapping 2 s epochs.
  - Per-epoch, per-channel z-score.
  - No re-referencing beyond the dataset's own; all channels used.
- **Channels:** our 64 BioSemi scalp channels, in recorded order, equal MindMix `ch_names` after case-folding, in the
  same order. EXG1–8 and Status are excluded (`CHANNEL_CONTRACT.json`).
- **Channel order does not matter at the pin.**
  - `pos_embed` is forced to `None` and no `input_chans` are passed, so no spatial embedding is used.
  - With mean pooling, the encoder is invariant to channel permutation.
  - The paper's eq. (1) 10-20 spatial embedding is not in the code or the weights.
- **Amplitude and reference:** the per-window z-score makes the unit immaterial. The recorded CMS reference is kept
  (proposed), as in the project's c3 preprocessing. The authors' DTU18 reference is undocumented.

### Audio

- 16 kHz mono waveform, 2 s = 32000 samples, peak-abs normalised (paper A.2).
- Encoder path: wav2vec2-base `last_hidden_state.mean(1)` (768) → `audio_proj` (256).

### How the target enters CALRA

- `forward_contrastive`: `fused_eeg = CALRA(eeg_emb, target_emb)[0]`, i.e. the EEG representation is conditioned on
  the target-slot audio.
- `aligned_target = CALRA(eeg_emb, target_emb)[1]` and `aligned_negative = CALRA(eeg_emb, negative_emb)[1]`.
- Training (`_train_contrastive`) uses `ClipLoss(fused_eeg, aligned_target)` with in-batch negatives only.
  `negative_audio` is never used in training.

### Stage-3 recipe (README table = public CLI = code defaults)

- Batch 32, 50 epochs, LR 1e-5, weight decay 0.01.
- AdamW over all parameters (betas 0.9/0.95, eps 1e-8); no gradient clipping.
- Warmup: LinearLR, 3 epochs, 1e-6 → 1e-5. Then CosineAnnealingLR with T_max 47 and eta_min 1e-7, stepped per epoch.
  Per-epoch LR values come from the official classes.
- drop_path 0.1, CALRA dropout 0.1, fp32, shuffled DataLoader.
- Protocol: one model per subject, 5-fold KFold.

**Checkpoint selection and differences from the paper.**
- The code saves no checkpoint. It reports the maximum accuracy across epochs on the evaluated fold and early-stops
  on that fold's F1 (patience 20). That is selection on test.
- The paper says only "until convergence on the validation set".
- Binding: **fixed final epoch 50**.
- Paper A.3 text differs from the code (batch 64, wd 0.05, 10-epoch warmup). Table A2 agrees with the code
  (wd 0.01, warmup 3). Recorded, not run.

### Raw audio and alignment (`GATE345_RESULTS.json` → `gate3_alignment`; `stereo_check.log`)

- **Files:** DRCMR raw wavs (`audio_drcmr/DOWNLOAD_RECEIPT.json`), 44.1 kHz, 2 channels.
  - Both channels carry the same talker, lateralised: ITD 0.70 ms, with ILD on opposite sides for target vs masker.
  - Mono = L/R mean, as in the official derivative envelopes.
- **Per trial:** target = `stim_file` of the targetonset event; masker = `stim_file` of the maskeronset event.
- **Onset check** against the official derivative envelopes (`t` is re trial onset; masker `t_first` equals
  `masker_onset_rel_s`), on 8 streams (2 NH + 2 HI fit-role trials):
  - Target wav sample 0 = targetonset; masker wav sample 0 = maskeronset.
  - Best lag −3.9 ms in all 8 streams; r at lag 0 between 0.71 and 0.85.
  - Wav length equals trial duration within 12 ms.
- **'woa' vs plain:**
  - HI listeners heard the CamEQ-equalised files.
  - 'woa' is the same speech without CamEQ; mono correlation with the CamEQ files is 0.64–0.82, so the waveforms
    differ materially.
  - Proposed: HI → woa, NH → plain. This is the project convention and matches the core methods' envelopes.
  - This must be frozen in the binding.

### Official loader on our export (`GATE3_OFFICIAL_LOADER.json`)

- 8 fit-role windows (sub-021, trial_007) were written as `sub-021.pkl` in the official format: `eeg` [64,400],
  `target_audio` [32000], `negative_audio` [32000], `attended_label`.
- They ran through, unmodified: `DatasetLoader.load_dataset('DTU')` → `UniversalDataset` → DataLoader → official
  `setup_optimizer` + `train_epoch` + `update_learning_rate`. Result: 2 batches, finite loss.
- The export was deleted afterwards; its SHA256 was `b89b8a42…`.

### Geometry (proposed)

- Two non-overlapping 2 s sub-windows at +0.5 s and +2.5 s inside each project 5 s two-talker segment.
- Segment margin = mean of the two sub-window margins.
- Then the original 20 s mean-score with tau fitted on training-side windows, double order (`readout.attention`).

## 4. Blind scoring (`GATE345_RESULTS.json` → `gate4_*`)

**Mechanical changes only.** Fusion, loss and training are unchanged:
1. Export per-sample logits: the row diagonal of the official `get_scores`, without in-batch softmax.
2. Call the official `forward_contrastive` twice, with each candidate in the target slot once.
3. Antisymmetrise the result.

`s(x|t) = exp(logit_scale)·cos(fused_eeg(eeg,t), aligned_audio(eeg,x))`;
`m(c1,c2) = ½[(s(c1|c1) − s(c2|c1)) − (s(c2|c2) − s(c1|c2))]`.

The scorer takes `(eeg, c1, c2)` only; the truth is used after scoring. Scoring must run in eval mode: train mode
changed m by up to 0.73.

| Check | Synthetic (6) | Real training-side (16; sub-021 NH, sub-001 HI, fit role, cf0/sf0) |
|---|---|---|
| max \|m(c1,c2)+m(c2,c1)\| | 0.0 | 0.0 |
| batch of 1 vs full batch | 1.9e-6 | 2.9e-6 (0 decision flips) |
| permuted batch / with unrelated samples added | 0.0 / 0.0 | 0.0 / 0.0 |
| Official scorer: slot 1 wins in **both** orders | 100% | 100% |
| Official scorer at batch size 1 | always tie → pred 0 | always tie → pred 0 |
| Official pA change when unrelated samples are added | 0.123 | 0.0019 |

The official AAD scorer prefers whichever stream sits in the target slot, even for pure-noise inputs. Its accuracy
(the published 99.93% DTU) is therefore not a blind two-candidate accuracy.

## 5. Forward and backward (`GATE345_RESULTS.json` → `gate5`)

- Official `_train_contrastive` on 4 real fit-role windows, then `backward`, then an AdamW step.
- Gradients are finite and non-zero in `eeg_encoder`, all wav2vec2 parts, `eeg_proj`, `audio_proj`, CALRA and
  `logit_scale`. The classifier has no gradient, as expected.
- All trained tensors changed after the step.
- Timing: 20 s on 2 CPU cores; peak RSS 3.1 GB, including the checkpoint load.

## 6. Disclosures

These are training-side, label-free or loss-only checks on the released weights, not scores.

- **Objective shortcut** (`DIAG_SHORTCUT_FLOPS.json`, 16 training-side windows, eval mode). The official Stage-3
  ClipLoss with in-batch top-1 retrieval:

  | Condition | ClipLoss | In-batch top-1 |
  |---|---|---|
  | Attended stream as target | 0.0087 | 1.0 |
  | **Ignored** stream as target | 0.0049 | 1.0 |
  | **Gaussian-noise EEG** | 0.0087 | 1.0 |
  | Without CALRA (projections only) | 3.26 | 0.0625 (chance 1/16) |

  - The positive pair shares `CALRA(eeg_i, a_i)`, so the objective is met without any EEG–audio correspondence.
  - Real-batch training losses were 3.7e-4 and 2.4e-5, so the author recipe gives very small gradients.
- **EEG sensitivity at release** (`DIAG_EEG_SENSITIVITY.json`). Blind margins with real vs noise EEG: r = 0.997,
  sign agreement 100%. At release the blind score is driven by the candidate audio. Whether 50 epochs change this is
  unknown. No accuracy was computed.
- **Implication.** A faithful MindMix run may come out near chance, by construction of its fusion objective, under a
  blind scorer. That would be a property of the method, not a failure of feasibility. It must be reported next to the
  paper's privileged-slot numbers, and the route stays A.

## 7. What a faithful 10-unit run needs

1. **Data adapter** (`dtu_mm_input.py` is the readiness version). The production version should:
   - Filter each continuous BDF run (1–40 Hz Butterworth, sosfiltfilt), resample to 200 Hz, and cache per-trial
     64-channel arrays for all 44 people.
   - Make 16 kHz mono streams per unique waveform: woa for HI, plain for NH; masker placed at maskeronset.
   - Use the project's two-talker 5 s segments from `load_dtu` (roles from `content_groups`, folds from `_folds`
     seed 20261005), two 2 s sub-windows each.
   - Write fit/es/test window manifests per unit and the common-Q manifest (identical to core3), each hashed.
2. **Driver.** Official `create_model` + released checkpoint + pos-conv rename, then for each unit (10 units:
   `PUBLIC_UNITS.draft.json`):
   - Official `setup_optimizer`, `train_epoch` and `update_learning_rate` for 50 epochs.
   - Person-homogeneous shuffled batches of 32, seed 3401; final epoch kept.
   - Blind margins for every fit/es window of training people and every test window of test people.
   - Mean-score 20 s integration with training-side tau and double order, reusing the `readout.attention` path; core3
     recomputed on the same Q.
3. **Freeze `EXTERNAL_COMPARISON_BINDING.draft.json`** before reading any external test score. The open items are
   listed in the file.
4. **Compute.**
   - Measured cost: 130 GFLOP per training sample and 114 GFLOP per scored window.
   - Window counts: fit 5,964–6,470 (cf0) or 8,422–8,936 (cf1) per unit × 50 epochs.
   - Estimate: about 1.7–2.5 V100-h or 0.9–1.4 A100-h per unit; about 21 V100-h or 12 A100-h for all 10. These assume
     fp32 efficiencies; they are not measured on GPU.
   - Expected GPU memory is at most about 10 GB at batch 32.
   - Measure one fixed fit unit first, then register a lane with the fleet scheduler.

## Blockers

- **No GPU budget is free.** The 10-GPU cap is held by the fleet; the run needs a registered lane of about 12–21
  GPU-hours, and CPU execution is infeasible.
- **Binding items must be confirmed and frozen:** woa vs CamEQ, reference, filter order, sub-window geometry, batch
  composition, two-talker-only training, and the common Q hash.
- **The production adapter and driver are not yet written.**
- **Researcher acknowledgement of §6 is recommended** before spending GPU. The route itself is fixed by the rule.

## Files (all in this directory, mode 0700)

| File | Contents |
|---|---|
| `fetch_fusion_lfs.py`, `FETCH_FUSION_RECEIPT.json` | Gate 1 |
| `fetch_wav2vec2_base.py`, `FETCH_WAV2VEC2_RECEIPT.json` | wav2vec2-base fetch |
| `inspect_fusion.py`, `FUSION_CKPT_SUMMARY.json` | Checkpoint inspection |
| `mm_common.py`, `gate2_weights.py`, `GATE2_KEY_AUDIT.json` | Gate 2 |
| `gate345_dtu.py`, `GATE345_RESULTS.json` | Gates 3–5 |
| `dtu_mm_input.py`, `gate3_official_loader.py`, `GATE3_OFFICIAL_LOADER.json` | Official loader check |
| `stereo_check.py` | Stereo channel check |
| `diag_shortcut_flops.py`, `diag_eeg_sensitivity.py`, `DIAG_*.json` | §6 disclosures and FLOPs |
| `make_units.py`, `PUBLIC_UNITS.draft.json`, `CHANNEL_CONTRACT.json` | Unit bindings and channel contract |
| `paper_src/` | Paper PDF (SHA256 `20a781eb…`) and text |
| `*.log` | Run logs |

The JSON hashes are recorded in the binding draft under `readiness_evidence`.
