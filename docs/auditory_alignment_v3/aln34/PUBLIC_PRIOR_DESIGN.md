# E34_PUBLIC_PRIOR · implementation design for `aln33_env64_125ms_v1`

This is a design document. A read-only design workflow under ALN3.4 wrote it on 2026-10-16 between 20:45 and 21:55 CEST. A second read-only workflow revised it the same evening (about 22:10–22:50 CEST) against `PUBLIC_PRIOR_DESIGN_CRITIQUE.md` (sha256 a236fe875424cd0a…, 27 findings), starting from version f72abfed3f91a17e…. Nothing was registered, built, submitted or trained, and no other file was changed. The **Revision log** at the end lists every finding and what changed.

**Inputs:**
- the ALN3.4 block of `AGENTS.md`;
- `INTAKE_20261016.md`;
- the package `AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/`: the inherited ALN3.3 contract, docs/02 §C, docs/06, `configs/execution.yaml` (lane `gpu_now`) and `configs/seed_and_reporting.yaml`;
- the ADDENDUM_13 draft and the SparrKULee receipt;
- the live code;
- three read-only scouts of 2026-10-16 covering the SparrKULee donor, the four target cohorts, and the model, loss and execution infrastructure;
- the critique, and for the revision these metadata files and code: `c3_features_v1/dtu/inventory.json`, FAU `zenodo_17952231_th/hdf5_dataset_info.txt`, Federici `kcs_targets_v1/content_groups.json`, the SparrKULee `stimuli/eeg/` file listing and `dataset_description.json`, `auditory_c3/stageb.py`, `auditory_alignment/prep_targets.py`, `auditory_alignment_v3/sci_r2.py`, `aln3_gpu_pool.sbatch`, `keeper.sh`, `make_queue.py`, `ckpt_offload.py`, `watch_anyhost.sh`, `local_train.py`, `auditory_alignment/evaluate.py`, and the Slurm partition limits.

Numbers marked *(design count)* were computed for this file from header-level tables or metadata. Appendix A lists the provenance. The manifest builder (§6.2) recomputes every number from the data, and its manifest is the authority.

---

## 1. Execution record

**Object and authority.**
- The object is the ALN3.3 logical family `ALN32_PUBLIC_AUDIO_PRIOR` under the execution contract `aln33_env64_125ms_v1`. It is executed as card E34_PUBLIC_PRIOR under ALN3.4.
- Contract files (sha256 prefixes): `inherited/PUBLIC_PRIOR_EXECUTION_v3_3.md` 8a4217a8…, `OBJECTIVES_v3_3.md` b85b9d27…, `public_prior_v3_3.yaml` e8ecded1….
- Authority: AGENTS.md ALN3.4 item 6, intake action A03, and the user's "按这个包执行". The contract is approved, so it needs no reapproval. The controls, the rich-target track, the source-statistics-only zero-shot variant, the competing-talker extension (the contract's donor pool of "all legal human training data") and the seed panel added in this revision are all named by that contract or by the package (docs/06, `seed_and_reporting.yaml`); none needs a new approval.
- This design settles the open items of the ADDENDUM_13 draft (00d8d65b…). The draft itself stays unchanged as history. Its analysis item (iv), joint − max(audio_pair, cross_person), is dropped, because OBJECTIVES §4 asks for the two separate paired differences instead (§5.4).

**What was known before any result:**
- **This contract.** No unit of it exists, and nothing has been trained on SparrKULee.
- **Data facts.** These come from the receipt (2026-10-15), the scouts and this revision (2026-10-16). They cover:
  - run, presentation and participant tables;
  - start alignment, from a backward-decoder audit of about 40 runs: reconstruction r 0.03–0.13; one run misaligned by −566 samples; one run where τ = 0 is unsupported;
  - shared intro/outro audio across SparrKULee files;
  - envelope spectra;
  - reference schemes and montages;
  - reproduction of the ALN3 folds;
  - (revision) DTU trial and stimulus structure from `inventory.json`, FAU stimulus-code semantics, Federici item groups, and the SparrKULee stimulus file names.

  These facts define the data. None of them is an outcome of any arm.
- **Results of other contracts.** ALN3 A_LOCAL, E_LOCAL, E_PUBLIC_TRANSFER and the B/C/D families were seen earlier, by the researcher and by agents, through brief B01. SCI_R2 results (spectral-change and spectral-structure increments in nested forward models) were also seen; they motivated nothing here beyond reusing SCI_R2's feature definitions for the contract's rich track. None of them is used for any other choice below beyond what the contract already fixes (the `lag_local_tokens` backbone).
- **Target tests.** No target-cohort test value under this contract has been computed or viewed.
- **Scout outputs that touched restricted participants** (`aln34_sparrk/decoder_lag.py` and `isc_lag.py` audited (026, audiobook_1); `car_scale.json` covers all 666 runs) are not used for any decision. Every exclusion is recomputed by the CPU jobs of §6.2 without those participants.

**Fixed here, before the first donor result** (the definitions are in §2–§5):
1. **Donor roles.** SparrKULee is split by session block into fit (shortstories01, varyingStories01–04 and 08–10), dev (varyingStories05–06) and bridge_cal (varyingStories07). FAU, DTU and Federici contribute to donor fit only (§3.2).
2. **Exclusions.**
   - The 5 access-restricted SparrKULee participants (sub-019/020/021/022/026) are excluded, as the host's own `dataset_description.json` states for the re-host. Their EEG arrays are never loaded by any job, the alignment audit included (§3.2).
   - SparrKULee runs are excluded only by two fixed rules that the CPU jobs recompute from the data: the clock-validity rule (a consistent nonzero lag in both halves), and the structural-anomaly rule combined with an unverifiable clock (§3.2). The 3 README-flagged runs are asserted absent.
   - DTU donors are normal-hearing (NH) listeners only, because HI listeners heard individually equalised audio and so have no shared presentation key.
   - Core donor data are single-talker only, for the reason given in §2.16. FAU competing-talker anchors enter only the registered competing-talker extension (CSX).
3. **EEG harmonisation inside this contract.**
   - SparrKULee is band-passed to 1–20 Hz.
   - DTU is re-referenced to the 64-channel common average (CAR).
   - FAU electrodes interpolated in CI users are masked.
   - A fixed outcome-blind channel QC rule is applied to SparrKULee.
   - Private epochs are low-passed at 20 Hz and z-scored per child × channel at 64 Hz (§2.1).
4. **Target.** Each existing envelope is resampled to 64 Hz, band-passed at 2–8 Hz with a fixed Butterworth filter, then divided by its own stream RMS (stimulus-only). One standardiser σ ∈ ℝ⁸ is fitted on SparrKULee donor-fit data with **μ fixed to 0**, and one projection P (seed 20261016) is stored once (§2.3).
5. **Donor group units.** One unit per (target, objective, seed) trains five members in lockstep on one batch stream: audio_pair (AP), cross_person (XP), joint with λ = 1 (J1), joint with λ = 0.25 (J025), and the mismatched-partner control (XM). Each step draws 32 listener segments × 8 tick anchors × 2 listeners, with montage-subset augmentation and stratum weights proportional to eligible donor-fit segments (§2.6).
6. **Losses.** One NCE definition applies at both stages: log-sum-exp over positives, with an inclusive ±2 s (±128-sample) family-clock neighbour mask; keys are pinned in §2.5. CS uses the full kernel with a fixed calibrated bandwidth (§2.7–§2.8).
7. **Budget.** 1 epoch-equivalent (ep-eq) = 8 anchors × each eligible SparrKULee donor-fit listener segment. Training starts at 30 ep-eq on a stable-then-decay schedule (no warmup). Continuation follows one **group-synchronous** rule, so every member of a group always runs the same steps on the same batches. 60 ep-eq is this execution's compute limit; a group that reaches it while still improving gets a registered continuation version (§2.10).
8. **Selection.**
   - Donor checkpoints and the joint λ are chosen by the calibrated donor-dev retrieval cross-entropy, a development risk on new listeners and new content. The former correct-pairing gain is stored as a sensitivity checkpoint.
   - Target-stage checkpoints are chosen by the early-stopping risk; the inherited A_LOCAL gain rule is kept as a sensitivity.
   - Every record names its selection level (§2.10, §2.12).
9. **Bridge.**
   - Ridge from U to the standardised 8-d target, fitted on a fixed donor-fit sample shared by all members.
   - α and temperature come from bridge_cal; the temperature is tabulated by candidate-pool size.
   - A bridge_cal sensitivity bridge has its temperature cross-fitted over listeners.
   - An artefact-run probe is reported (§2.11).
10. **Target cells.** Cells are bound exactly as the ALN3 A_LOCAL and E_LOCAL cells (Option A). The target stage uses the A_LOCAL recipe with the contract NCE (§2.12, §3.3).
11. **Zero-shot.** Views load every participant, so candidate pools equal those of the adapted rows. There are three input-access modes, and mode A is primary (§2.13).
12. **Blocks.** Core breadth (seed 3401), zero-shot access modes, the private_transfer seed panel (3407, 3413), the rich-target block and the CSX extension, in fixed queue tiers (§4).
13. **Analysis.** Endpoints, contrasts, families, identity units and seed handling are in §5. The analysis code is frozen with this record.

**Declared choices.** These are places where the contract leaves room, or where this execution differs from native ALN3:
- (a) Per-stream RMS normalisation of every envelope (stimulus-only). With μ ≡ 0 it has provably no effect on any target-side score or loss (§2.3). It matters only for the pooled donor bridge, where it makes donor sources commensurate.
- (b) μ ≡ 0 for the standardiser, justified by the 2–8 Hz band-pass. The estimate is recorded.
- (c) A single-talker core donor pool; competing-talker anchors go into the CSX extension (§2.16).
- (d) The contract's 24 donor trainings, the 8 joint λ candidates and the 8 control trainings run as 8 lockstep group units (§2.6, §4.2).
- (e) The 64 Hz geometry (36 lag tokens), the target-stage NCE mask and the private 64 Hz input differ from native ALN3. All arms share them, and native rows remain different-contract references.
- (f) The target-stage primary selection is the early-stopping risk, not A_LOCAL's gain rule, which is kept as a sensitivity.
- (g) Zero-shot mode A uses the fixed target preprocessing, and declares that access. Modes B and C remove the stimulus-informed ICA and the target statistics, where the caches allow.

**After this point.**
- Engineering defects found by the tests or the probe are fixed before registration.
- After registration:
  - any change to inputs, training or selection gets a new execution id;
  - wrong labels or summaries get a versioned correction note;
  - analyses informed by results are labelled exploratory.
- No performance threshold gates any stage.
- A group that reaches the compute limit while its trigger still fires gets a continuation version (new ids) by the rule in §2.10. The primary rows are not changed.
- Before registration, the scout scripts and outputs that this design quotes are copied into `private/auditory_alignment_v3/aln34/prior33_provenance/` (0700), with a sha256 list (Appendix A). The copy must happen before the session allocation ends (job 1039458, 2026-10-18 10:26).
- At registration, §1–§5 are copied verbatim into `private/auditory_alignment_v3/aln34/E34_PUBLIC_PRIOR_EXECUTION_RECORD.md` (0444). That copy adds the manifest sha256, the sha256 of every code file (training and analysis) and the provenance list. Its sha256 is quoted in every plan row's `registered` field.
- A versioned correction note records the receipt corrections found by the scouts and this revision:
  - 666, not 668, runs;
  - 1,024 Hz BDF headers;
  - probe D used 963, not 1,005, windows;
  - probe E included resting-state runs;
  - 67 content families;
  - the DTU NH single-talker counts of §3.5.

---

## 2. Contract definitions

### 2.1 EEG at 64 Hz

**Anti-alias filter `h_aa`.** One specification serves every resampling ratio:
- Kaiser FIR designed at f_in × up: cutoff 26 Hz (−6 dB), passband edge 22 Hz, stopband edge 30 Hz, 60 dB design, odd length.
- Applied as `scipy.signal.resample_poly(x, up, down, axis=time, window=h_aa)`; scipy scales h by `up`.
- Measured *(design count)*:

| ratio | taps | sha256 prefix |
|---|---|---|
| 128→64 | 61 | b0fb5a2b6761efa3 |
| 100→64 | 727 | fd778051ceda90d8 |
| 250→64 | 3,627 | e0d15bfab3fc284a |

- Passband deviation ≤ 0.011 dB up to 22 Hz; stopband ≤ −59.7 dB from 30 Hz; half-support ≈ 230 ms.
- Sample 0 is preserved: a pulse at 5.000 s comes out at 5.000 s. This was checked for 1/2 and for 16/25.
- The scipy default (Kaiser β 5) is only −6 dB at 32 Hz, which would alias the private data's 32–45 Hz content. That is why it is replaced.

**Per cohort.** Guards are in 64 Hz samples.

| cohort | array read | native | to 64 Hz | reference | band | guard start / end |
|---|---|---|---|---|---|---|
| SparrKULee (donor only) | `derivatives/preprocessed_eeg/…/*_eeg.npy` (64, T) float64, `allow_pickle=False`. The arrays of the 5 restricted participants are never opened; their runs are listed from file names and `.npy` headers only | 64 | none | CAR-64 (authors) | authors' pipeline (gentle high-pass, content to ≈28 Hz), **then our 1–20 Hz**: `butter(4,[1,20],'band',fs=64,'sos')`, `sosfiltfilt(padtype='odd', padlen=min(256,T−1))` over each whole run. sha e014c236…; −6 dB at 1 and 20 Hz; 99.99 % of the impulse energy within ±64 samples | 128 / 128 |
| FAU | stage-B `trial_XX/eeg_1_20_ica` (mode A), `eeg_1_20_noica` (modes B, C), 31 ch | 128 | 1/2 | average (31, incl. reconstructed Cz) | 1–20 Hz FIR + ICA (unchanged) | 157 / 157 (= the ALN guard of 314 at 128 Hz) |
| DTU | `trial_NNN/eeg_1_20[:64]` | 128 | 1/2 | **CAR over the 64 EEG channels, applied by us** (the cache is CMS; common-mode ratio 7.0) | 1–20 Hz FIR | 41 / 41 |
| Federici | `eeg` [blocks, 32, 5000] | 100 | 16/25 | average (32) | authors' 2–8 Hz + ICA (unchanged) | 41 / 41 |
| private_bdf (target only) | `hc.load_children()` epochs [20, 200], onset at index 50 | 250 | reflect-pad 75 samples at both ends, then 32/125 with `h_aa`, then `butter(4, 20, 'low', fs=64, output='sos')` with `sosfiltfilt(padtype='odd')` over the 90-sample epoch | average (20) | 0.5–45 Hz at source; < 20 Hz after the low-pass, matching the donors' upper edge | n/a: window [32, 70) of the 90-sample output |

**Normalisation.** "Fixed input preprocessing" here means:
- z-score per participant × channel over all of that participant's loaded pieces, computed at 64 Hz after resampling;
- the pieces are FAU/DTU single- and competing-talker trials, every Federici block, and every cached SparrKULee run;
- guard samples and masked (piece, channel) cells are excluded from the statistics;
- masked channels are then set to 0.

These are the semantics of `data._stdz`. The pre-z SD of every participant × channel, in the cache's physical unit, is also stored; mode C needs it (§2.13).

**Private inputs.** The per-child z-score of `hc.load_children` at 250 Hz is kept. After resampling and the 20 Hz low-pass, each child × channel is z-scored again at 64 Hz, over all of that child's [32, 70) windows. This matches the public cohorts' unit-variance input at 64 Hz. It differs from the native private rows (250 Hz, 0.5–45 Hz), and is shared by all arms. It uses no label.

**Masks** (fixed, outcome-blind):
- **FAU:** the stage-B attribute `bads_interpolated`, i.e. electrodes interpolated in CI users (P7 17×, P8 13×, CP6 7×, …), is masked in every role.
- **SparrKULee:** a (run, channel) cell is masked when its SD over the run, after the 1–20 Hz filter, exceeds 10× that run's median channel SD or falls below 0.1× of it. The scout found 21 runs with SD > 50 in a raw 100-s slice. The number of masked cells is recorded.

**Private epochs.**
- The reflect pad puts the onset exactly at output index 32 (synthetic 3 Hz check: output 1.0003 at index 32).
- Window [32, 70) covers 0–578.1 ms of sample times, a 593.75-ms span.
- The last ≈230 ms of the window depend on the reflected end extension. Synthetic error: 1.3 % for a 3 Hz cosine, and 0.03 % in the first 24 samples.
- The 20 Hz Butterworth's impulse response decays within ≈5 samples, so its edge transient stays outside [32, 70).
- The D1 continuous arrays were deleted, so wider epochs are impossible. This limit is recorded.

### 2.2 Query grid, segments and windows

**Ticks.**
- Ticks k ≥ 0 count from each stream's physical origin, which is sample 0 of the EEG piece. Origins:
  - the SparrKULee presentation (envelope index 0 is EEG index 0);
  - the FAU or DTU trial (stimulus at lead 0);
  - the Federici block.
- **i_k = (64 k + 25) // 50**, in integer arithmetic. This equals `round(1.28 k)`, and no rounding ties exist (asserted to k = 2·10⁶).
- Steps are 1 sample (179 of every 249) or 2 samples (70 of 249), and i_{k+25} = i_k + 32.
- Records keep t_req = 0.020 k and t_act = i_k / 64. Their difference lies within ±7.5 ms.
- A denser output grid does not mean finer neural time resolution.

**Segments.**
- A 5-s segment is 250 ticks starting at a tick k0 ≡ 0 (mod 25), i.e. at a start sample s that is a multiple of 32.
- Every segment therefore has the same sample offsets `TICK_OFFS[j] = i_j`: j = 0…249, with values 0, 1, 3, 4, 5, 6, 8, 9, 10, 12, …, 319.
- The segment grid of a stream is s_m = s_first + 320 m, where s_first is the smallest multiple of 32 that is ≥ the start guard: SparrKULee 128, FAU 160, DTU 64, Federici 64.
- A segment is eligible on a piece when s_m + 357 ≤ T_eeg − end_guard and s_m + 327 ≤ T_stream − 41. Here 357 = i_249 + 38 and 327 = i_249 + 8.
- Competing-talker segments (DTU target-stage evaluation, FAU in CSX only) start at max(guard, distractor or masker onset + 1.7 s), rounded up to a multiple of 32.

**Windows** (half-open):
- EEG: **x_k = eeg[i_k : i_k + 38]**, all channels, 593.75 ms.
- Target: **y_k = env[i_k : i_k + 8]**.
- The EEG window follows the query in time; query audio is never an EEG input.

**Anchors.**
- Training: 8 per segment, at ticks j = φ + 31 a (a = 0…7, φ ~ U{0…30}). They lie 0.62 s apart, on the tick grid.
- Evaluation: all 250 ticks of every query and candidate segment.

### 2.3 Target: 2–8 Hz envelope, 125 ms, shared coordinates

**Sources.** The existing envelopes; origin and band are recorded per source.

| cohort | stream | origin and original band |
|---|---|---|
| SparrKULee | `derivatives/preprocessed_stimuli/<stim>_envelope.npy` (T, 1), 64 Hz. The duplicate `audiobook_9_2_envelope-1.npy` is ignored | Authors' pipeline; the extractor was neither run nor verified, and `*.data_dict` is never opened. Broadband: +11 dB at 0.5 Hz, −4 dB at 8 Hz, relative to 3–7 Hz |
| FAU | `c3_preproc_v1/fau_tud/stimulus_env_128.h5` `<code>/{attended,distractor}_env/raw`; `nan_to_num` as in `prep_targets.py`, NaN count recorded | Authors' 1 kHz envelope (method undocumented, ≈0.3–9 Hz with a steep low-pass), copied by us at 128 Hz |
| DTU | `c3_features_v1/dtu/kcs_targets_v1/audio_local.h5` `<sha>/env` (targets and maskers), 128 Hz | Ours: abs(Hilbert) of the original unequalised 16 kHz audio. Broadband. HI trials point to the `woa` originals, as in ALN3 |
| Federici | block `env` [blocks, 5000] (`AudioEnvSp`, not normalised), 100 Hz | Authors' cache. Low-pass only (−3 dB ≈ 6.9 Hz), **not** high-passed; the 2 Hz edge comes from our filter |

**Processing chain:**
1. Resample to 64 Hz with `h_aa`.
2. Band-pass with `sos = butter(4, [2, 8], 'band', fs=64, output='sos')`: 4 sections, sha256 a5457201db325d21. Apply `sosfiltfilt(padtype='odd', padlen=min(128, T−1))` over each whole stream (SparrKULee presentation, FAU code stream, DTU waveform, Federici block).
   - The zero-phase response is −6 dB at 2 and 8 Hz, −26 dB at 10 Hz and −63 dB at 1 Hz.
   - 99.9 % of the impulse energy lies within ±41 samples, which sets the 41-sample target edge guard.
3. **Stream RMS normalisation:** env_n = env_bl / RMS(env_bl over the stream). This is stimulus-only and identical for every listener of a stream. It is a declared choice (§1 (a)): it makes donor sources commensurate for the pooled bridge ridge, and the invariance below shows that it cannot change any target-side output.
4. y_k = env_n[i_k : i_k+8]: 8 samples, physical span [t, t + 125 ms), 109.4 ms from the first to the last sample.

Secondary band-limiting does not restore missing broadband content, and it does not make the envelope extractors identical. In particular, Federici gains no information below 2 Hz.

**Standardiser.**
- σ ∈ ℝ⁸ over the unique (presentation, tick) windows of the eligible SparrKULee donor-fit anchors. Each window counts once, whatever its listener count: 1,970,250 windows before the shared-audio mask *(design count)*.
- **μ ≡ 0.** The 2–8 Hz band-pass makes the stream mean zero in expectation. The estimated μ and |μ|/σ are recorded in the manifest. C6 asserts |μ|/σ < 0.05 as an engineering check: a larger value would mean the filter is not doing what is assumed.
- Fitting on SparrKULee only makes it valid for every target: SparrKULee is part of every donor set and is never a target.
- One standardiser is shared by all donor sets, targets, arms and modes, including strict zero-shot and the from-scratch arm. The from-scratch arm's use of external sound statistics is declared.

**Invariance (exact with μ ≡ 0).** Let a stream be scaled by c > 0. Then:
- v = normalize((c·y/σ) Pᵀ) = normalize((y/σ) Pᵀ), so the head output does not change;
- the unified score is invariant anyway, because `ev1._zt` z-scores each segment and dimension;
- the native NCE score (u·v), the native CS ridge target (v), the kernel-dependence statistic (on v) and every training loss depend on y only through v, so none of them changes.

So the RMS of a target stream cannot change any target-side output. Test 3c checks this to 1e-6 with c ∈ {0.1, 10}.

**Projection.**
- P = `audio_targets.semi_orthogonal(32, 8, 20261016)`, shape [32, 8].
- Pᵀ P = I to 1.2·10⁻⁷, rank 8, sha256 of the float32 bytes 706c4ff4441f4940 *(design count; matches the scout and the critique)*.
- P is generated once by the manifest builder, stored as `P_32x8_seed20261016_f32.npy`, and loaded by every unit. It is never regenerated, because QR signs depend on the BLAS library.
- Head: v = normalize((y/σ) Pᵀ). It has no trainable parameters. Its state-dict keys `std.mu` (stored as zeros), `std.sd` and `P` are those of `FixedFeatureHead`.

**Recorded per result:**
- frame rate 64 Hz;
- coverage 125 ms;
- projection rank 8 (effective ≈3: eigen-fractions 0.483 / 0.446 / 0.064).

### 2.4 Shared channel map and encoder

**Vocabulary.** 70 names in a fixed order: the BioSemi-64 list (the SparrKULee and DTU row order, Fp1 … O2), then F9, F10, TP9, TP10, FT9, FT10.

**Aliases.**
- Private: T3→T7, T4→T8, T5→P7, T6→P8.
- SparrKULee: P07→PO7 and P03→PO3. These label typos occur in the sub-015 to sub-018 BDF headers only; the `.npy` rows follow the canonical order.

**Layouts.**
- FAU (31), DTU (64) and Federici (32) layouts are read from the cache attributes; the private layout (20) comes from `HA_CHANNELS`.
- Every name must map into the vocabulary.

**`NameIndexedSpatial`.**
- Weights W ∈ ℝ^{70×16}, signed and unconstrained, plus bias b ∈ ℝ¹⁶ and a boolean buffer `seen[70]`.
- s(x)[b, f, t] = Σ_c x[b, c, t] · W[idx_c, f] · seen[idx_c] + b_f.
- A donor's seen set is the union of its donor montages. Unseen rows hold 0, so they contribute nothing and receive zero gradient.
- In target-supervised mode, unseen target channels are opened (`seen = True`) at W = 0 and trained.
- Initialisation: U(±1/√n_c) for W and b, where n_c is the number of names the unit trains (the donor union, or the target montage for the from-scratch arm), with the unit's model seed.
- This was verified by the scout's prototype:
  - with copied rows it matches a per-cohort `Conv1d` to within 2.1·10⁻⁷;
  - perturbing an unseen channel changes the output by 0;
  - the gradient on unseen rows is 0.

**Zero-shot coverage** with leave-target-out donors:

| target | channels with donor weights | channels set to zero |
|---|---|---|
| FAU | 29/31 | F9, F10 (TP9/TP10 seen via Federici) |
| Federici | 30/32 | FT9, FT10 (TP9/TP10 seen via FAU) |
| DTU | 64/64 | none |
| private | 20/20 | none (target-supervised only) |

Interpolated FAU channels are masked in addition, per participant.

**`SharedEncoder`.**
- Structure: `NameIndexedSpatial`, then `TokenEncoder('lag_local_tokens', n_ch=16, d=32, windows=[(0, 38)], fs=64)` with `branches[0].local[0] = Identity`. The spatial step is per time sample, so the composition is exact.
- The inherited `temporal.py` rules give, at 64 Hz:
  - a token step of 1 sample (15.6 ms);
  - a local window of 3 samples (46.9 ms);
  - **36 lag tokens**;
  - `proj` = LayerNorm(1152) → Linear(1152, 32), then L2-normalisation.
- Parameters: 44,176, of which `proj.1` holds 36,896.
- Shapes are identical in every cohort, so every tensor transfers.
- This geometry differs from the 128 Hz A_LOCAL (25 tokens, 23.4 ms step). All arms share it, and the native-rate ALN3 rows remain a different-contract reference.
- `forward_tokens()` returns [B, 36, 32] for task heads and personal adaptation; `trunk()` returns the 1152-d pre-projection features (used by the rich heads, §2.15).

**Strict construction and loading.**
- `build_target_encoder(row, layout, manifest, donor_state)` always builds the 64 Hz geometry above on the given layout. It takes no sampling rate or channel-count argument, so no caller can request another geometry. It asserts 36 tokens and `proj` in-features 1152. This closes the private path, whose native code passes 250 Hz and 20 channels to `build_encoder`; the generated copy replaces that call, and the generator asserts the replacement (§2.12).
- `load_donor(enc, state, layout, open_new=True, strict=True)` asserts that every donor tensor of `SharedEncoder` exists in `enc` with an identical shape, and that no key is missing or unexpected. The only exceptions are declared ones: the rich heads `rich.*` (dropped and listed, §2.15), and the `seen` rows opened for the target montage.
- The returned tensor map lists loaded tensors, opened rows, dropped donor heads and parameter fractions; `new` and `missing` must both be empty.

### 2.5 Cross-person keys and family clocks

**Key** (one packing for donors and the target stage):
- key = (family << 40) | (presentation << 24) | s, where:
  - `family` is a global id, < 2²³;
  - `presentation` is a global id, < 2¹⁶. It encodes the stimulus file, variant, condition (SNR, noise file), attended stream and loudspeaker side;
  - s is the **family-clock sample** of the anchor's first target sample: s = family_offset[presentation] + i_k, with s < 2²⁴ (72.8 h at 64 Hz).
- The bit budgets are asserted when keys are packed. Python `hash()` is never used.
- **Positive** ⇔ equal keys. Equal keys imply the same presentation, hence the same offset, hence the same tick, because i_k is strictly increasing.
- **NCE mask** ⇔ same `family` field, |Δs| ≤ 128 (inclusive), and not positive.
- `TickBatcher` packs target-stage keys in the same way. In `fit_continuous`, the rolled early-stopping rows carry the rolled audio's keys (`ks[bi][src][b]`). `ContractObjective` decodes family and s from those keys, so the mask of a rolled batch is the mask of the rolled audio. Test 4g checks this.

**Family clocks** (which streams share a time base):

| cohort | families and offsets |
|---|---|
| SparrKULee | Declared structure: the `audiobook_1` family covers the halves at +1,711 and +30,986 samples, the shifted-voice copies and the artefact excerpt. C3 re-measures these offsets by envelope cross-correlation and asserts them to ±1 sample. Every other file is its own family, unless the duplicate scan below merges it |
| FAU | Each code stream is its own family, unless merged by the scan. Single-talker parts 1–4 and competing-talker parts 5–10 of the two audiobooks are different content |
| DTU | Each presented waveform (sha) is its own family. The 46 transcript groups (Jaccard ≥ 0.8) are different recordings and not time-aligned; they remain the content-split unit only |
| Federici | Each natural/vocoded content group is one family. The second item's offset is the lag of the 2–8 Hz envelope cross-correlation within ±2 s (C3). If the peak r is < 0.5 or the lag lies outside ±2 s, the group is "same family, unknown clock", and the mask then covers the whole partner item at any time |
| any donor cohort | Duplicate scan (C3): two streams of different content ids whose aligned overlap at r ≥ 0.9 covers ≥ 50 % of the shorter stream are merged into one family at the detected lag. Shorter overlaps are masked as shared audio, like the SparrKULee jingles |

**Donor positives:**

| donor cohort | family (content) | presentation_id | condition / stream | eligible |
|---|---|---|---|---|
| SparrKULee | as above | stimulus file, with variant and (condition, snr, noise_file) | listeningActive / single | ≥2 listeners in the role, after guards and the shared-audio mask |
| FAU | code | code: the same file and the same loudspeaker for everyone; hearing devices count as part of the listener | single-speaker / single | single-talker codes; all 81 listeners hear all 8 |
| FAU, CSX only | competing-talker code | (code, attended loudspeaker side from the trial attributes); the code fixes the attended story and part | competing / attended stream | all 12 competing-talker codes (210, 215–220, 225–229), heard by all 81 listeners |
| DTU | presented waveform | sha of the presented waveform. NH = original file. HI audio is equalised for each listener, so each HI listener's presentation is unique | single-talker / single | NH only; inventory level: 79 shas with ≥2 NH listeners, 341 trials *(design count, §3.5)* |
| Federici | natural/vocoded content group | item envelope hash | natural or vocoded / single | human children; items with ≥2 listeners; HC-v kept as separate identities |

**HC / HC-v.** The ALN3 folds keep HC N with HC-v N in the same fold, so that either identity hypothesis is leakage-safe. For the same reason, partner sampling never pairs HC N with HC-v N (same N). The number of such would-be pairs is recorded. It is expected to be ≈0, because vocoded items carry a different presentation id.

### 2.6 Donor group units and the shared sampler

**Group unit.** One unit per (target donor set, objective, seed, block) trains its members in lockstep:

| block | members |
|---|---|
| core and panel | AP, XP, J1, J025, XM |
| rich | APR (§2.15) |
| CSX | APC, XPC (§2.16) |

- Every member has its own model and its own AdamW state.
- All members are initialised identically: the torch seed is reset to `donor_seed` before each build.
- One batch per step feeds every member, so EEG forward exposure, anchors, montage choices and step counts are identical by construction, not only by matched seeds.

**Sampler.** A single generator (seed = `sampler_seed` = `donor_seed`) draws, for every step:
1. A stratum: one donor cohort c (or the `fau_cs` stratum in CSX), drawn with the weights of §3.1. **Batches are single-stratum.**
2. 32 eligible listener segments from c:
   - participant-balanced, i.e. a uniform participant and then a uniform segment, as in the ALN `Batcher`;
   - with no repeated (presentation, segment) within the batch.
3. For each segment, a partner chosen uniformly among the other listeners for whom that segment is eligible (never the excluded HC/HC-v pairs).
4. 8 anchors per segment (§2.2), shared by both listeners.
5. Montage-subset augmentation, for 64-channel cohorts only (SparrKULee, DTU):
   - with p = 0.5 the batch keeps only the channels of one of the FAU∩64 (27), Federici∩64 (28) or private (20) montages, chosen uniformly;
   - the other channels are zeroed, in both views;
   - the choice is target-agnostic and identical for every donor set.

**Per step.** Each step draws 256 anchors:
- 512 EEG windows X₁, X₂ of shape [256, C, 38];
- 256 targets y (and the rich targets in the rich block);
- keys, participant ids and family times.

AP matches each view to y; XP matches X₁ to X₂; J1 and J025 do both; XM matches X₁ to a deranged X₂ (below).

**XM derangement.**
- A second generator (seed `donor_seed + 7`) draws a permutation π of the batch's 32 segments.
- Hard constraints: family(π(i)) ≠ family(i), and partner(π(i)) ≠ listener(i).
- Preference: condition(π(i)) = condition(i).
- Up to 100 draws are tried. The draw kept is the one that satisfies the hard constraints with the most same-condition pairs. If none satisfies them (small strata), the best draw is used and its violations are counted.
- XM's view-2 rows are X₂[π] and carry the keys of X₁, a structure-preserving mismatch. Its masks therefore have exactly XP's structure.
- Recorded per run: the same-condition fraction and the violation count.
- The derangement generator is separate, so the main stream is identical for every member.

**Stream hash.** A running sha256 of (stratum, segment ids, partner ids, anchor ticks, montage choice) is stored every 1,000 steps in the group record. The rich block asserts that its stream equals the core group's (§2.15).

**Validation.** Validation and the selection score use the full montage, without augmentation.

**audiobook_1 share.** audiobook_1 (60 listeners in P2 fit; 76 in P2 overall) takes 13.4 % of the participant-balanced draws *(design count)*. The share is recorded; it is not re-weighted.

### 2.7 NCE (multi-positive log-sum-exp with a neighbour mask)

**Loss.** For a query q with candidates j, with s_qj = cos(·,·)/τ, τ = 0.1, computed in float64:

ℓ_q = − log Σ_{j∈P(q)} e^{s_qj} + log Σ_{j∉E(q)} e^{s_qj}, where P(q) ∩ E(q) = ∅ and positives stay in the denominator.

**Masked set.** E(q) holds the candidates of the same family whose family-clock sample lies within ±128 (2.000 s, inclusive), excluding P(q). In cross_person and XM it also holds any candidate from the same participant at the same key. A query's own observation is never a candidate.

**audio_pair.**
- EEG→audio: the 2B EEG rows are queries over the B unique audio rows, with 1 positive each.
- audio→EEG: the B audio rows are queries over the 2B EEG rows, with 2 positives each (both views).
- L = ½(mean ℓ^{E→A} + mean ℓ^{A→E}).

**cross_person.** Bipartite: view 1 → view 2 and view 2 → view 1, each B×B. L = ½(mean + mean). XM uses the same definition on (X₁, X₂[π]) with X₁'s keys.

**Target stage** (single view, A_LOCAL batches): P = same key; E = same family within ±128 samples. The ALN `Batcher` admits each content segment once per batch, so P(q) is the query's own row.

**Behaviour.**
- With unique keys and no mask, the loss equals `symmetric_infonce` (checked by the scout).
- With anchors 0.62 s apart, the mask removes up to 6 of the 7 other anchors of the same segment. This is a different task from the A_LOCAL deduplicated NCE, which has no mask; that NCE remains the ALN3 native reference.

### 2.8 Traditional kernel CS (full kernel)

**Estimator.** I = log A + log B − 2 log C, where:
- A = n⁻² Σ K L;
- B = (n⁻² Σ K)(n⁻² Σ L);
- C = n⁻³ Σᵢ (Σⱼ K)(Σⱼ L).

The function is `auditory_alignment.losses_reference.cs_qmi`, imported unchanged. It keeps the diagonal and uses uniform weights. The loss is −I.

**Rows.**
- audio_pair: (u_r, v_{a(r)}) for r = 1…2B, with v repeated.
- cross_person: ([u₁; u₂], [u₂; u₁]), i.e. 2B rows with both orderings. XM: the same with X₂[π].
- joint: both terms.

**Masks and strata.** No NCE mask ever enters K or L. There is one estimate per (single-stratum) batch, so the stratum average is set by the sampling weights.

**Bandwidths.**
- Gaussian kernels, one bandwidth per term and side.
- σ_u is the median off-diagonal distance of the initial encoder's outputs, on one calibration batch per donor cohort. The batches come from a separate stream (seed donor_seed + 99), and the medians are averaged with the stratum weights.
- σ_v is the same statistic on the unique audio rows. cross_person and XM use σ_u on both sides.
- Bandwidths are fixed for the run and saved in the checkpoint. All members start from the same weights, so σ_u is identical across members.
- At the target stage, σ comes from the `Objective` rule: the initial model on a target-training calibration batch, multiplier 1.

**Logged at every validation:**
- off-diagonal kernel statistics;
- true and mismatched dev CS (`cs_diag`);
- effective rank.

The n = 512 ceiling of log n is 6.24 nats; training values are not evidence of generalisation.

### 2.9 Joint loss

- L = L_audio + λ L_cross. Both terms use the same loss family, and one forward pass of the two views feeds both.
- λ = 1.0 (J1) and λ = 0.25 (J025) are both members of every core and panel group. They therefore train on the same batches with the same number of updates, so they are compared at equal updates (§2.10).
- The joint slot J* takes the member with the lower donor-dev cross-entropy of its `_best.pt`. A difference below 1e-4 bits counts as a tie, and ties go to J1. The choice under the gain rule is recorded as a sensitivity.
- Recorded: both curves, both terms' row counts, averaging units and raw magnitudes, and joint's extra compute (the second term and the second λ).

### 2.10 Donor optimisation, group horizon, selection and continuation

**Optimiser and batch.**
- AdamW, lr 1e-3, weight decay 1e-4, gradient clip 5, per member.
- 256 anchors / 512 windows per step.
- A member whose loss or gradient norm is non-finite skips that step's update; `nonfinite_steps` is recorded per member.

**Budget.**
- 1 ep-eq = 8 × N_SK anchor draws, where N_SK is the number of eligible SparrKULee donor-fit listener segments. Before the shared-audio mask, N_SK = 86,285, so 1 ep-eq = 690,280 anchors = 2,696.4 steps, rounded up to 2,697 *(design count; reproduced by the critique)*.
- **S0 = 30 ep-eq = 80,893 steps.** The exact value comes from the frozen manifest.
- S0 is identical for every group, because N_SK depends only on SparrKULee. The mixture shares these steps through the stratum weights, so every donor cohort receives a similar number of passes (≈23–27).

**Schedule (stable then decay; no warmup, as in the ALN recipe).** The learning rate is constant at 1e-3 from step 0, then decays linearly to 0 over the final 3 ep-eq of the current horizon H (H₀ = 30 ep-eq).

**Validation scores.** Validation runs every ep-eq and at the end of every decay. The score set is identical for every member and group of a seed:
- U is computed for 300 fixed SparrKULee donor-fit listener segments (all ticks). A ridge U → standardised y is fitted with relative penalty 1e-2 · mean diag(UᵀU), with no search.
- The queries are 400 fixed SparrKULee dev listener segments. The candidates are their unique content segments, deduplicated by (presentation, segment).
- S(q, c) is the unified-type score: the mean over the 8 target dimensions of Pearson r, over the segment's 250 ticks, between q's reconstruction and c's standardised target (`ev1._zt` semantics).
- **Primary, CE_dev** (bits; lower is better): the minimum over τ ∈ logspace(−3, 2, 41) · sd(S) of the mean over queries of −log₂ softmax(S(q, ·)/τ)[own(q)]. This is a calibrated development retrieval risk on new listeners and new content.
- **Sensitivity, gain** (higher is better): the former selection score, the mean over queries of S(q, own) − S(q, o(q)), where o(q) is a fixed other dev segment of the same listener.
- Also logged: r̄_own = mean S(q, own), the candidate count and τ*.
- Selection level, written into every donor record: "donor dev: SparrKULee participants and content families disjoint from donor fit (new listeners, new content)".

**Checkpoints per member** (member tag M ∈ {AP, XP, J1, J025, XM, APR, APC, XPC}):
- `<gid>_m<M>_best.pt`: the minimum CE_dev over all validations of the run, side branch included;
- `<gid>_m<M>_gainsel_best.pt`: the maximum gain;
- `<gid>_m<M>_h30_best.pt`: the minimum CE_dev over the validations up to and including the 30-ep-eq decay end (main run or side branch). This is the fixed-recipe model.

**Group horizon** (one rule for the whole group):
- In core and panel groups, at the start of each decay (H − 3 ep-eq), H is extended by 10 ep-eq **for all members** if, for any contract member (AP, XP, J1, J025), the best stable-phase CE_dev lies within that member's last 3 stable-phase validations.
- XM does not trigger; it follows the group horizon.
- On the first extension, the 30-ep-eq decay also runs, for every member, as a side branch from the saved stable state. This gives the exact equal-update fixed-recipe models `_h30`.
- The rich and CSX groups do not run their own trigger. They adopt the realised horizon H* of the core group with the same (target, objective, seed), read from its record, so their paired contrasts with the core members are also at equal updates (§2.15, §2.16).

**Compute limit, not a scientific stop.**
- H_max = 60 ep-eq is this execution version's compute limit. The yaml's `hard_cap: false` is respected as follows:
  - if the trigger still fires at 57 ep-eq, the group decays to 60;
  - the record sets `ceiling_reached_while_improving: true`;
  - the stable states are kept as `<gid>_m<M>_stable57.pt` (never offloaded; a few MB);
  - `make_plan_ext_prior33.py --continuation <gid>` then registers a continuation version: new ids for the group and its downstream rows, resuming from those states under the same rule, with limit 90.
- The primary rows are not replaced. The continuation is reported as its own version.

**Resume and records.**
- `<gid>_resume.pt` is written at every validation via tmp file and `os.replace`. It holds, for every member, the model, optimiser, σ, best scores and curve; and, for the group, the sampler and derangement generator states, the torch RNG, H, phase, side-branch status and trigger log.
- `<gid>_wsd_resume.pt` holds the stable-state snapshot while a side branch runs.
- Both files are deleted at the end; both match the offload daemon's `*_resume.pt*` guard.
- The group record contains: steps by phase, ep-eq used, realised stratum and presentation shares, the stream hashes, the XM derangement statistics, the joint choice under both rules, GPU seconds and a FLOP proxy. Per member it contains: steps, nonfinite steps, curves, best positions and the scores under both rules.

### 2.11 Source sound bridge and temperature

There is one bridge per slot, i.e. per (donor group, member) for AP, XP, J*, XM, APR, APC and XPC. Every member gets the same procedure on the same rows.

**Bridge-fit rows.**
- 2,000 donor-fit listener segments × 250 ticks = 500,000 rows.
- Drawn once per donor set (seed 20261016) with the stratum weights, and identical for every member of that donor set.
- Montage augmentation as in training, seeded.

**Unified bridge.**
- Ridge with intercept, U → standardised y (8 dimensions).
- α ∈ `logspace(−4, 8, 13)`, chosen on bridge_cal by the mean per-dimension Pearson r (the ev1 `corr` criterion).
- B_uni is the donor-fit solution at α\* (yaml: fit on donor_fit_only).

**Native readout.**
- NCE: cosine u·v, with no fit.
- CS: ridge U → v (32 dimensions), α chosen by MSE on bridge_cal.
- For cross_person NCE and XM NCE the native readout is reported as not applicable, because those encoders were never trained against v.

**Temperatures.**
- τ(n) for n ∈ {64, 128, 256, 512, 1024}.
- Computed on 300 bridge_cal query segments, each scored against its own candidate plus n − 1 random bridge_cal content segments (seeded, 20261017).
- τ minimises the candidate cross-entropy on the ev1 grid (`logspace(−3, 2, 41)` × sd).
- Computed for both the unified and the native readout.
- Zero-shot uses the table entry nearest, in log₂, to the target's test-pool size. The pool size is evaluation-design metadata, not target data.

**Sensitivity bridge B_uni_cal.**
- Fitted on bridge_cal rows, with α chosen by a 2-fold split of the 6 bridge_cal participants (3 + 3, seeded).
- Its temperature is **cross-fitted on the same split**: B is fitted on fold a and τ calibrated on fold b's queries, and vice versa; the geometric mean is stored. The two folds share presentations, so this is cross-fitting over listeners only. The record says so.
- It exposes the in-sample optimism of audio_pair, whose encoder was trained against the same donor-fit audio.

**Artefact-run probe.** The frozen B_uni is applied to the insert-phone artefact control run (`audiobook_1_artefact`, sub-002 run-01; role `control_artefact`). Recorded descriptively: the reconstruction r̄ against its own envelope, and against other `audiobook_1` segments. This bears on risk 3 (stimulus-locked non-neural components). It is never used for any selection.

**Also stored:**
- σ_v for kernel-dependence reporting;
- the number of audio–EEG pairs used and the seconds spent.

**Output:** `ckpt/<bid>_bridge.npz`, keyed by the bridge row's id. It holds `objective`, `B_uni`, `alpha_uni`, `a_mu`, `a_sd`, `B_nat` (CS), `alpha_nat`, `tau_unified[n]`, `tau_native[n]`, `B_uni_cal`, `tau_cal`, `sigma_u`, `sigma_v` and the row lists' sha. It is never offloaded and never matched by the pool's `_last.pt` cleanup.

### 2.12 Target-supervised adaptation

**Generated training copy.** `prior33/gen_fit_target.py` writes `prior33/fit_target.py` from `local_train.py`, following the `gen_local_train.py` precedent. `local_train.py` itself is not touched. The generator asserts that each substitution applies exactly once, and the copy's header names the source sha256. The substitutions are:
1. `GridBatcher(coh, spec, row, dev, grid)` → `TickBatcher(coh, spec, row, dev, manifest)`.
2. `build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs)` → `build_target_encoder(row, coh.layout, manifest, donor_state)` (§2.4). Donor tensors are loaded strictly when the row is pretrained.
3. `target_stats(bt, …)` → the manifest standardiser (σ, μ ≡ 0); `build_head(…)` → `SharedFixedHead(σ, P)`.
4. `Objective(obj_job, …)` → `ContractObjective(obj_job, …)`, on the continuous path only.
5. **Two selection rules.** At every validation, `<eid>_best.pt` is saved when `es_loss` improves (the primary, a risk on held-out content), and `<eid>_gainsel_best.pt` when `es_loss − es_loss_rolled` improves (the inherited A_LOCAL rule, a correct-pairing sensitivity). `log` records both best epochs and both curves.
6. **Private path.**
   - `build_encoder(spec["architecture"], 20, d, bt.W, 250)` → `build_target_encoder(row, PRIVATE_LAYOUT, manifest, donor_state)`, so the 250 Hz geometry can never be built;
   - `PrivateBatcher` → `PrivateBatcher64` (window [32, 70) of x64);
   - the private `Objective` stays `auditory_alignment.train.Objective` (asserted), because its label and prototype path must stay unchanged;
   - selection as in 5, with `es_loss − es_loss_permuted` as the sensitivity.

**Public targets.**
- The A_LOCAL recipe is otherwise unchanged: 200 epochs, AdamW 1e-3 with cosine annealing, validation every 5 epochs on 40 fixed early-stopping (es) batches.
- Evaluation is `ev2.evaluate_continuous`, with `ev1.Reps` replaced by `TickReps` inside `try/finally`, as in `core.evaluate_grid`. Readouts and τ are fitted on the target training side, as in ALN3.
- Both checkpoints are evaluated. When their epochs coincide, the record states `gainsel: identical`.
- Selection level, written into every target record: "training identities, held-out early-stopping content (not new listeners)".

**Arms.**
- target_from_scratch (S): random initialisation (`target_seed`) with the same architecture and the shared coordinates.
- AP, XP, J*, XM (and APR, APC, XPC in their blocks): the full encoder is loaded strictly from the slot's group member, unseen target rows are opened at 0, all parameters train, and the learning rate is the same.
- The tensor map is recorded; about 99.9 % of parameters load for FAU.

**Private target.**
- `fit_private_p33` (the generated copy) is used, with the private input of §2.1.
- Only EEG parameters transfer; new 2×32 prototypes are trained.
- `ev2.evaluate_private` and `calib.private_variants` are reused unchanged. Speech zero-shot is not computed.
- Selection level: "training children, last 20 % of each child's physical blocks".

### 2.13 Zero-shot evaluation, access modes and naming

**Modes.** Each mode is a separate execution id (the contract: 另行建立, build separately):

| mode | name suffix | cohorts | EEG input | normalisation | what the input touched in target data |
|---|---|---|---|---|---|
| A (primary) | `__fixed_input_preprocessing` | FAU, DTU, Federici | the cached contract input | per participant × channel z-score over all loaded pieces | FAU: z-score incl. test content; the stage-B ICA rule removes a component when its 1–8 Hz correlation with the **presented envelopes** of all 20 trials peaks within ±3 samples (> 15 dB); CI interpolation (masked). DTU: z-score incl. test content; CAR. Federici: z-score incl. test blocks; the authors' ICA and 2–8 Hz filter |
| B | `__fau_noica_target_z` | FAU | `eeg_1_20_noica` | as A | z-score incl. test content; CI interpolation (masked). No stimulus-informed step |
| C | `__source_statistics_only` | FAU (noica), DTU | FAU noica; DTU with CAR | each channel divided by a donor-derived scale | nothing beyond fixed filters and the instantaneous CAR |
| C-partial | `__source_statistics_partial` | Federici | the authors' preprocessed blocks | donor-derived scale | the authors' ICA (method not ours) |

The per-stream RMS of the test envelopes is applied in every mode and provably has no effect (§2.3).

The full mode name is `zero_shot__no_target_supervised_fit` + suffix.

**Mode C scale.**
- s_T[n] = the median, over the leave-T-out donor participants that have channel n, of their pre-z SD of the same-band 64 Hz signal, in µV. For names no donor has, it is the median over all donor channels.
- A cohort enters mode C only if C5 can establish the physical unit of its own cache and of every donor cache. The unit comes from documented metadata where it exists. Otherwise it comes from the order of magnitude of the median channel SD, by a fixed rule recorded in the manifest. If neither works, the manifest marks the cohort unsupported, and no mode-C row is registered for it.
- The donors were trained on z-scored inputs, so mode C also carries a train/test scale mismatch. This is part of what mode C measures, and is declared.

**FAU caveat.** The noica input keeps the CI stimulation artefacts that the stage-B rule removes. Mode B and C values for CI users therefore do not separate neural tracking from artefact. They are access sensitivities.

**Procedure** (all modes):
- **Every participant of the cohort is loaded** (the Federici phantom as `test_only`), through the same loader as the adapted rows. The stimulus-defined test pool `pool_of("test", kind)` is therefore identical to the adapted row of the same cell.
- `TickBatcher` is constructed with `train_p = ∅` (forced, not derived from the fold). The runner asserts that `train_segs == []` and that the early-stopping query list is empty.
- Queries are the fold's participants only (plus `test_only` sessions), as `ev1` already restricts them.
- `ev1.Readouts` is replaced by `FrozenBridge`, and `ev1.Reps` by `TickReps`. `ev1._ridge` is monkeypatched to raise for the duration of the evaluation, all inside `try/finally`.
- `FrozenBridge(ev1.Readouts)` bypasses `__init__` and defines every attribute that `ev1` reads: `objective`, `B_uni`, `alpha_uni`, `a_mu`, `a_sd` (donor values), `B_nat` (CS), and `tau = {"unified": τ_u(n), "native": τ_n(n)}`. Its `calibrate` raises. On its own, that would prove nothing, since `calibrate` is never reached when the query list is empty; the `_ridge` raise and the empty-list asserts carry the proof.
- Unseen channels carry zero weight. Kernel dependence uses the donor σ.
- Metrics are the full ev1 set: regular, hard and mismatched-EEG retrieval, split-half, attention 2AFC for FAU and DTU, and kernel dependence. The set is computed for B_uni, then again for B_uni_cal as a sensitivity check.
- `readout.n_test_candidates` is recorded. The analysis asserts that it equals the adapted row of the same cell (§5.8).

**Not in this matrix:** unlabelled covariance adaptation (deferred by the contract).

### 2.14 Controls (OBJECTIVES §4)

| contract control | here |
|---|---|
| no-cross-person | AP (audio_pair) |
| mismatched training | XM: the same sampler and windows as XP, with the partner deranged to a different content family and a different participant in the same stratum (§2.6) |
| task-state-matched | XM again. Every donor stratum is a single task state: SparrKULee is all `listeningActive` single-talker narrative, FAU and DTU are single-talker, Federici is natural/vocoded single-talker, and CSX's `fau_cs` stratum is all attended-stream competing talker. "The same task and condition, but a different content or time" is therefore exactly the deranged partner drawn within the stratum with the same-condition preference. The realised same-condition fraction is recorded |

- XM gets bridges, target rows and mode-A zero-shot rows like the contract arms. Its contrasts are in §5.4.
- The artefact-run probe (§2.11) is the cheap check against stimulus-locked non-neural components.
- No metadata enters any prediction path, and no group consistency is forced.

### 2.15 Rich-target block (spectral structure and spectral change; parallel, non-blocking)

**Question.** Does adding spectral targets to audio-supervised pretraining change transfer, compared with envelope-only pretraining of the same arm, at identical batches and equal updates?

**Status.**
- The block has separate ids and families (`…_RICH_DONOR`). The yaml's `same_envelope_core_first` holds: the core never waits for this block.
- The block waits only for its cache (C7) and for the core group's horizon.

**Sources** (real waveforms only):
- **SparrKULee:** `stimuli/eeg/<stim>.npz.gz`. C7 gunzips each file in memory and reads it with `np.load(…, allow_pickle=False)`. It requires a numeric 1-D or 2-D audio array and a scalar sampling rate; anything else makes that stream "waveform unavailable". Nothing is unpickled, no dataset code runs, and the `noise_*` and `t_*` files are not read.
- **FAU:** `fau_tud/stimuli/stimuli/S1xx.wav` (48 kHz, single-talker codes), and its existing `c3_features_v1/fau_tud/whisper_logmel128.h5`.
- **DTU:** the NH originals and the existing `kcs_targets_v1/audio_local.h5 <sha>/logmel`.
- **Federici:** no waveform. Its rich targets are masked, never fabricated.

**Features.** These are the project's validated local acoustic features, with the SCI_R2 definitions adapted to the shared coordinates:
- The 128-bin Whisper log-mel at 100 Hz: 16 kHz mono, `WhisperFeatureExtractor` from the local offline snapshot and `auditory_c3.features._windows`, exactly as `prep_targets.dtu_audio`. FAU and DTU reuse the existing files; SparrKULee is computed by C7.
- 100 → 64 Hz with `h_aa` (727 taps).
- **Spectral structure:** projection onto a PCA-4 basis fitted on the unique SparrKULee donor-fit windows. The basis is shared by every donor set; it is not refitted per cohort.
- **Spectral change:** the L2 norm of the first difference of that 4-d vector (SCI_R2 `flux`).
- Each time course is band-passed at 2–8 Hz with the envelope SOS and RMS-normalised per stream and dimension.

**Clock check (no EEG).** Our abs(Hilbert) envelope of the same waveform (64 Hz, 2–8 Hz) is cross-correlated with the stream's contract envelope. The lag must be 0 ± 1 sample; otherwise the stream's rich targets are masked and listed.

**Targets per tick.**
- y_ss: 8 samples × 4 dimensions = 32; y_sc: 8 × 1 = 8.
- σ per dimension from the unique SparrKULee donor-fit windows, with μ ≡ 0.
- P_ss = `semi_orthogonal(32, 32, 20261017)` (orthogonal); P_sc = `semi_orthogonal(32, 8, 20261018)`. Both are stored once.

**Model.**
- Member APR = `SharedEncoder` (trunk and the envelope projection `proj`) plus independent EEG-side heads `rich.proj_ss` and `rich.proj_sc`. Each is LayerNorm(1152) → Linear(1152, 32), then L2-normalisation, fed by `trunk()`.
- Only the trunk and `proj` transfer downstream. The rich heads are dropped and listed in the tensor map.

**Loss.**
- L = (L_env + 0.5 L_ss + 0.5 L_sc) / (1 + 0.5·[ss present] + 0.5·[sc present]).
- Each term is the audio_pair loss of the objective on its own head pair; for CS, each head has its own σ_v.
- A head is present in a batch when the batch's cohort has that target. Batches are single-cohort, so a Federici batch trains the envelope only, at the same scale. This keeps cohorts with more heads from being implicitly up-weighted.
- The weights are fixed now.

**Batch stream and budget.**
- The sampler, seed and pools are those of the core group with the same (target, objective). The batch stream is therefore identical, and the stream hash is asserted every 1,000 steps; a mismatch is a `technical_failed`.
- The horizon is the core group's realised H*, so APR − AP is at identical batches and equal updates.

**Downstream.**
- Bridges, mode-A zero-shot rows and target rows, all on the envelope contract.
- After training, the rich donor unit also reports, descriptively, the donor-side rich readouts: bridge_cal reconstruction r̄ of y_ss and y_sc from ridges fitted on the 300 fixed fit segments, for APR and for the core AP of the same group.

### 2.16 Competing-talker donor extension (CSX)

**Why the core stays single-talker.**
- On a competing-talker anchor, the contract's single presented-stream envelope does not exist. audio_pair would pair the EEG with the attended stream, which is an attended-alignment task. Meanwhile, two listeners' EEG shares the response to the whole two-talker scene.
- The two arms would therefore supervise different signals on those anchors, and the core variant contrast would partly become an attention-task contrast.
- ALN3's target-stage training data for FAU and DTU are also single-talker.
- The contract's "all legal human training data of the non-target public cohorts" is therefore taken up as a declared, registered extension, not dropped.

**Eligible data.**
- **FAU:** the 12 competing-talker codes (210, 215–220, 225–229). The code fixes the attended story and part (`hdf5_dataset_info.txt`), and every one of the 81 listeners heard every code. The presentation id is (code, attended loudspeaker side from the trial attributes), so cross-person keys are shared by all listeners who share that pair. C6 counts them.
- **DTU** NH two-talker trials contribute nothing *(design count, `inventory.json`)*. Of 704 trials, the masker onsets vary from 3.0 to 5.0 s (515 distinct values), giving 702 distinct presentations; only 2 of them were heard by ≥2 NH listeners (4 trials). There is therefore no CSX group for target FAU, whose only competing-talker donor data would be DTU.

**Block.**
- Donor groups for targets DTU, Federici and private_bdf × 2 objectives. Members:
  - APC: audio_pair, with the attended-stream envelope on competing-talker anchors;
  - XPC: cross_person, with the attended-stream key.
- `fau_cs` is its own stratum, with weight proportional to eligible segments. Segments start at max(guard, distractor onset + 1.7 s).
- The horizon is the core group's H*.

**Downstream.** Bridges; mode-A zero-shot rows for DTU and Federici, including the DTU attention 2AFC; target rows for DTU, Federici and private_bdf.

---

## 3. Data binding

### 3.1 Donor sets (leave the target cohort out)

**Rules.**
- The target cohort never appears in its own donor set.
- `private_bdf` is never a donor.
- The Federici phantom is never a donor.
- The stratum weight is each stratum's share of eligible donor-fit listener segments. Values are design estimates; SparrKULee is exact, before masking.

| target | donor set (core, panel, rich) | estimated eligible donor-fit listener segments | stratum weights | CSX adds |
|---|---|---|---|---|
| fau | sparrkulee, dtu (NH), federici (humans) | 86,285 + ≈3,000 + ≈8,500 | ≈0.88 / 0.03 / 0.09 | — (no group) |
| dtu | sparrkulee, fau, federici | 86,285 + ≈16,800 + ≈8,500 | ≈0.77 / 0.15 / 0.08 | `fau_cs` (count from C6) |
| federici | sparrkulee, fau, dtu (NH) | 86,285 + ≈16,800 + ≈3,000 | ≈0.81 / 0.16 / 0.03 | `fau_cs` |
| private_bdf | sparrkulee, fau, dtu (NH), federici | 86,285 + ≈16,800 + ≈3,000 + ≈8,500 | ≈0.75 / 0.15 / 0.03 / 0.07 | `fau_cs` |

There is one donor group per (target, objective, seed, block). Each group member is reused across all of that target's cells.

### 3.2 Donor fit / dev / bridge_cal

**SparrKULee** (policy P2, by participant **and** content family; counts are *(design count)* before the shared-audio mask, reproduced exactly by the critique):

| role | sessions | participants | eligible presentations | listener segments | content segments |
|---|---|---|---|---|---|
| fit | shortstories01, vS01–04, vS08–10 | 64 | 49 | 86,285 (119.8 h) | 7,881 (10.95 h) |
| dev | vS05, vS06 | 10 | 11 | 8,520 (11.8 h) | 1,756 (2.44 h) |
| bridge_cal | vS07 | 6 | 6 | 6,366 (8.8 h) | 1,090 (1.51 h) |

**Role details.**
- dev content: audiobook_11_1/11_2/12_1/12_2 and podcasts 16–23. podcast_18 has a single listener.
- bridge_cal content: audiobook_13_1/13_2 and podcasts 24–27.
- `audiobook_1` is used only in fit. Its 16 runs from dev and bridge_cal participants get the role `holdout_seen_content` and are not used.
- podcast_10 and audiobook_14 stay inside fit blocks.
- Across roles, participants and content families are disjoint; the only cross-role audio shared is jingles, which are masked.

**Exclusions** (fixed before any result; never selected by score):
- **Restricted participants** sub-019/020/021/022/026: 50 runs, 11.6 h. Their EEG arrays are never opened by any job: not by the cache build, not as decoder references in C2, and not by the probe. Their runs appear in the coverage table from file names and `.npy` headers only.
- `audiobook_1_artefact` (sub-002 run-01, the insert-phone control): kept in the cache with role `control_artefact`. It is used only by the artefact-run probe (§2.11).
- **Clock-validity rule (C2).** This is a clock check, not a performance rule; no run is ever excluded for weak tracking, and no run is ever shifted.
  - For each run with at least 2 eligible co-listeners, a backward ridge decoder is trained on up to 8 other listeners of the same stimulus. The references exclude restricted participants and structurally excluded runs. The decoder uses 1–8 Hz, 64 channels × 7 lags 0–375 ms, λ = 1e-2 · tr(G)/p.
  - For each half h, r_h(τ) is computed between the reconstruction and the envelope shifted by τ ∈ [−40 s, +40 s] (±2,560 samples). The window was widened from ±10 s because the receipt saw off-peak lags up to +37 s.
  - τ̂_h = argmax r_h(τ). z_h is the peak's prominence over the background lags |τ − τ̂_h| > 1 s: (r_h(τ̂_h) − mean) / SD.
  - A half is *measurable* when z_h ≥ 5. This prominence threshold only decides whether a lag can be measured at all. It never excludes a run: unmeasurable runs are kept as unverifiable.
  - **aligned:** both halves measurable, and |τ̂_1|, |τ̂_2| ≤ 4 samples. **misaligned:** both halves measurable, |τ̂_1 − τ̂_2| ≤ 4, and |mean τ̂| > 4. **unverifiable:** otherwise.
  - Only misaligned runs are excluded. The list (run, τ̂ per half, z per half) goes into the manifest and the execution record. sub-051 audiobook_12_2 (−566 samples in both halves in the scout) is expected here; the job recomputes it rather than assuming it.
- **Structural-anomaly rule (C1).** A run whose T_eeg differs by more than 8 samples from the modal T_eeg of its presentation's co-listeners is structurally anomalous. It is excluded when C2 does not classify it as aligned. sub-011 audiobook_6_1 (64 samples longer than its 23 co-listeners) is expected here, again recomputed.
- The 3 runs flagged in the README are asserted absent.

**Single-listener presentations** contribute no anchors: in P2 fit the four `audiobook_1` halves and shifted variants; in dev, podcast_18.

**FAU, DTU, Federici: donor fit only.** They use all eligible data:
- FAU: 81 participants × 8 single-talker codes (CSX adds the 12 competing-talker codes);
- DTU: NH single-talker trials on shas with ≥2 NH listeners;
- Federici: 86 human identities (HC 37, CI 33, HC-v 16).

Donor dev and bridge_cal are SparrKULee-only. SparrKULee belongs to every donor set and is never a target, so one dev/bridge_cal definition serves all four donor sets, and roles stay disjoint by participant and content. The yaml's `calibrate: donor_development_only` is satisfied because bridge_cal is a donor development partition, separate from the checkpoint dev set.

### 3.3 The 30 target cells

The cells are bound exactly as the ALN3 A_LOCAL and E_LOCAL cells (seed 3401 plan, `AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010/plans/units.jsonl`). This keeps every new row cell-by-cell comparable with the native-contract rows and leaves training/test separation unchanged.

The scouts reproduced the memberships from file listings with `data._folds` (seed 20261005) and `hc.folds`. This design re-checked them against completed unit records: FAU sf4/cf0 (11 test participants), DTU sf2/cf1 (8) and Federici sf3 (14 humans + 9 phantom sessions) all match. The critique confirmed every fold table.

Each row's `split_hash` is the sha256 of canonical JSON holding: train IDs, test IDs, the FAU always-train TH IDs, fit/es/test content lists, rules and seeds.

**FAU** (10 cells = 5 subject folds × 2 content folds).
- The TH selection half is always in training and never tested: 301 302 304 311 314 315 317 319 321 322 325 327 330 331.

| fold | TH | HA | CI | test n | train n |
|---|---|---|---|---|---|
| f0 | 305 313 318 | 203 212 213 220 224 229 | 102 110 118 122 128 | 14 | 67 |
| f1 | 306 316 328 | 202 206 209 222 226 228 | 109 114 116 120 123 | 14 | 67 |
| f2 | 307 309 323 | 201 207 211 215 217 218 | 103 106 111 113 127 | 14 | 67 |
| f3 | 303 324 329 | 204 205 210 221 223 225 | 108 112 119 121 130 | 14 | 67 |
| f4 | 308 326 | 208 214 216 219 227 | 104 105 107 125 | 11 | 70 |

Content folds (`FAU_CF`):
- **cf0:** single-talker fit 111 121, es 112 122, test 113 114 123 124. Competing-talker test (attention 2AFC only): 217–219 and 227–229.
- **cf1:** single-talker fit 113 123, es 114 124, test 111 112 121 122. Competing-talker test: 210 215 216 220 225 226.
- Training uses single-talker data only. Competing-talker trials are loaded for normalisation and attention evaluation.

**DTU** (10 cells).

| fold | NH | HI | test n |
|---|---|---|---|
| f0 | 026 027 028 037 038 | 002 005 010 016 018 | 10 |
| f1 | 023 024 031 035 039 | 003 007 011 014 015 | 10 |
| f2 | 022 025 029 040 | 004 006 012 042 | 8 |
| f3 | 032 034 043 044 | 001 009 013 017 | 8 |
| f4 | 021 030 033 036 | 008 019 020 041 | 8 |

Content folds come from `kcs_targets_v1/content_groups.json`: 336 target waveforms in 46 groups.
- cf0: test = half 0 (23 groups), es 7, fit 16.
- cf1: test = half 1 (23 groups), es 3, fit 20.
- The trials that ALN3 does not load stay out. The earlier design names `sub-024_run-2`; C6 derives the actual list from the cache (§3.5).
- NH and HI both train at the target stage. Each group's audio target is the original or `woa` envelope, as in ALN3.

**Federici** (5 cells).
- Option A: the ALN2/ALN3 folds, in which HC-v N shares a fold with HC N. This is leakage-safe under either identity hypothesis. It is not reported as identity merging: HC-v children are separate identities in every count (n = 86).

| fold | HC | CI | HC-v | humans |
|---|---|---|---|---|
| f0 | 1002 1005 1009 1015 1019 1027 1036 1037 | 00010 0023 0027 0035 0038 0043 0049 | 1002 1005 1009 1015 | 19 |
| f1 | 1001 1006 1010 1017 1020 1030 1032 1034 | 0015 0016 0020 0028 0042 0044 0046 | 1001 1006 1010 | 18 |
| f2 | 1003 1007 1012 1016 1024 1025 1028 | 00011 0009 0033 0041 0048 0051 0052 | 1003 1007 1012 1016 | 18 |
| f3 | 1008 1018 1026 1029 1031 1033 1035 | 0002 0013 0029 0030 0036 0047 | 1008 | 14 |
| f4 | 1004 1011 1013 1014 1021 1022 1023 | 0006 0018 0031 0040 0050 0054 | 1004 1011 1013 1014 | 17 |

- The 9 phantom sessions are `test_only` in every fold, never trained, and kept outside human inference.
- There is one content split: groups fit 54 / es 14 / test 22, i.e. items 84 / 25 / 32.

**private_bdf** (5 cells). Only counts and structure were inspected.
- `hc.folds` (seed 20261005, strata HA/NH): test children per fold 13/13/13/13/12 (HA 11 each; NH 2/2/2/2/1), training children 51–52.
- fit/es comes from `es_mask`: the last 20 % of each child's physical blocks. Children with fewer than 3 blocks contribute no es trials.
- There is no content axis.
- Child IDs are bound by the manifest builder inside the 0700 area. They never appear in this file.

### 3.4 Overlap exclusion and duplicate content

1. The whole target cohort is out of its donor set, which covers identity, content, dev and calibration data.
2. Stimulus overlap across cohorts is checked by the manifest scan C3 (§6.2):
   - every pair of the four public cohorts, on 64 Hz 2–8 Hz envelopes;
   - 10-s windows with a 2-s hop, normalised cross-correlation over all lags, flag at r ≥ 0.7.

   A flagged donor content item is removed from that target's donor set. The rule is fixed now.

   The receipt's probe D (SparrKULee against FAU, DTU and Federici) found a maximum r of 0.39–0.43, but it sampled only a third of the audio. FAU, DTU and Federici have never been checked against each other.
3. Within each donor cohort, C3 scans stream pairs of different content ids: 10-s windows with a 1-s hop, all lags, flag at r ≥ 0.9.
   - A pair whose aligned overlap covers ≥ 50 % of the shorter stream is merged into one family at the detected lag (§2.5).
   - Shorter overlaps, such as the SparrKULee jingles, are masked. At the matched lag, a span is extended over 2-s windows sliding by 0.25 s while r ≥ 0.8, and a 0.5-s margin is added. Any segment intersecting a masked span is removed from every role. The scout's estimate for SparrKULee is ≈17 min, about 1.8 % of the content.
4. C3 also measures the Federici natural/vocoded lags and the SparrKULee `audiobook_1` offsets (§2.5).
5. Identity overlap across cohorts is implausible: the cohorts come from different sites, countries and ages, and share no identifiers. It cannot be verified, and records say so.

### 3.5 Coverage and unused records (reported, never hidden)

- **SparrKULee:**
  - restricted participants: 50 runs, listed and never loaded;
  - control and holdout runs: 1 + 16;
  - runs excluded by the clock-validity and structural rules (list in the manifest);
  - single-listener presentations;
  - guard and segment-grid losses;
  - masked jingle segments.
- **DTU** *(design count from `inventory.json`)*:
  - 2,112 trials: 1,056 NH and 1,056 HI, each 352 single-talker and 704 two-talker.
  - NH single-talker: 352 trials on 90 shas. Of these, 341 are on the 79 shas heard by ≥2 NH listeners, and 11 on single-listener shas.
  - The earlier design's "334 + 15" and the critique's "338 + 11" both total 349 = 352 − 3. That is consistent with three NH single-talker trials being absent from the ALN3 DTU cache; the earlier design attributes them to `sub-024_run-2`. This revision found no code reference to that name. C6 therefore derives the exclusion from the cache contents, and prints the trial ids, their reason and whether any sha drops below 2 listeners.
  - Unused as donors: HI single-talker (352), all two-talker trials (NH: 702 of 704 presentations unique), and NH trials on single-listener shas.
- **FAU:** all competing-talker trials as core donors (they are CSX donors).
- **Federici:** phantom sessions, and single-listener items (12 of 141); no waveform, so no rich targets.
- **Rich block:** streams whose waveform is unavailable or whose clock check fails.
- **Extensions listed, not registered:** an audio-only extension on all sound anchors, and a relaxed DTU HI key.

---

## 4. Row matrix

### 4.1 Blocks

| block (tier) | family_id | code group | rows | content | `logical_dependencies` | queue weight |
|---|---|---|---|---|---|---|
| core (1) | `ALN32_PUBLIC_AUDIO_PRIOR_DONOR` | `prior33_donor` | **8** | 4 targets × 2 objectives; members AP, XP, J1, J025, XM | none (the frozen manifest) | 8 (set from the probe) |
| core (1) | `…_BRIDGE` | `prior33_bridge` | **32** | 8 groups × {AP, XP, J*, XM} | the group | 6 |
| core (1) | `…_TARGET` | `prior33_target` | **300** | 30 cells × {S, AP, XP, J*, XM} × 2 | S: none; others: the group | 3 |
| core (1) | `…_ZEROSHOT` | `prior33_zeroshot` | **200** | 25 public cells × {AP, XP, J*, XM} × 2, mode A | group + bridge | 2 |
| access (2) | `…_ZEROSHOT` | `prior33_zeroshot` | **≤ 210** | B: FAU 10 × {AP, XP, J*} × 2 = 60. C: FAU 10 + DTU 10, and C-partial: Federici 5, each × 3 × 2 = 150. Mode-C rows only for cohorts the manifest supports | group + bridge | 2 |
| panel (3) | `…_DONOR` | `prior33_donor` | **4** | private_bdf × 2 objectives × seeds 3407, 3413; members as core | manifest | 8 |
| panel (3) | `…_BRIDGE` | `prior33_bridge` | **16** | 4 groups × 4 members | the group | 6 |
| panel (3) | `…_TARGET` | `prior33_target` | **100** | 5 private cells × 5 variants × 2 × 2 seeds | as core | 3 |
| rich (4) | `…_RICH_DONOR` | `prior33_rich_donor` | **8** | 4 targets × 2; member APR | manifest + rich cache + core group (H*) | 8 |
| rich (4) | `…_BRIDGE` | `prior33_bridge` | **8** | APR | the rich group | 6 |
| rich (4) | `…_ZEROSHOT` | `prior33_zeroshot` | **50** | 25 × 2, mode A | group + bridge | 2 |
| rich (4) | `…_TARGET` | `prior33_target` | **60** | 30 × 2 | the rich group | 3 |
| CSX (4) | `…_CSX_DONOR` | `prior33_donor` | **6** | DTU, Federici, private × 2; members APC, XPC | manifest + core group (H*) | 8 |
| CSX (4) | `…_BRIDGE` | `prior33_bridge` | **12** | 6 × 2 | the CSX group | 6 |
| CSX (4) | `…_ZEROSHOT` | `prior33_zeroshot` | **60** | (DTU 10 + Federici 5) × 2 × 2, mode A | group + bridge | 2 |
| CSX (4) | `…_TARGET` | `prior33_target` | **80** | (10 + 5 + 5) × 2 × 2 | the CSX group | 3 |

**Totals.** At most 1,154 rows: core 540, access ≤ 210, panel 120, rich 126, CSX 158. They form 26 donor-group units holding 80 member trainings, 68 bridges, 540 target units and up to 520 zero-shot units.

**Tiers.** Tiers are a resource order, not gates. Every tier starts as soon as its own dependencies are complete. From-scratch targets are runnable from the start.

### 4.2 Mapping to the contract's 438 intents

| contract intent | here |
|---|---|
| 24 donor trainings | the AP, XP and J* members of the 8 core groups. The unselected λ member (8) is joint's declared extra selection compute; the XM members (8) are the controls |
| 24 source bridges | 24 of the 32 core bridge rows (the other 8 are XM) |
| 240 target trainings | 240 of the 300 core target rows (the other 60 are XM) |
| 150 zero-shot references | 150 of the 200 core mode-A rows (the other 50 are XM) |

None of the 438 intents had been registered, so nothing needs deduplicating. The access, panel, rich and CSX blocks are the contract's own additional items (§1, Authority).

### 4.3 IDs and spec fields

**IDs.** Each id is `ALN3X_` + sha256(json({family, dataset, subject_fold, content_fold, seed, spec}, sort_keys))[:16]. `seed` is the row's own seed: `donor_seed` for donor, bridge and zero-shot rows, and `target_seed` for target rows.

**Spec fields common to every row:**
- `logical_family`: "ALN32_PUBLIC_AUDIO_PRIOR"
- `card`: "E34_PUBLIC_PRIOR"
- `execution_contract`: "aln33_env64_125ms_v1"
- `manifest_sha256`
- `block`: "core" | "access" | "panel" | "rich" | "csx"; `queue_tier`
- `seed_scope`: "breadth" (3401) | "panel" (3407, 3413)
- `donor_seed`, `sampler_seed` (= donor_seed), `target_seed` (null where not applicable), and `readout_seeds`: "runner-defined: target_seed + {5, 98, 99, 1000}; bridge rows 20261016; τ pools 20261017". These follow `upstream_seed_scope: donor_base_adapter_and_readout_seeds_separately_recorded`.
- `architecture`: "lag_local_tokens"
- `channel_map`: "name_indexed_signed_v1"
- `window`: "full"; `input_samples`: [0, 38]; `fs`: 64; `projection_dim`: 32
- `objective`: NCE | CS_SINGLE
- `target`: "envelope", or "current_class" for private; `target_contract` (sha of the standardiser, P and filters)

**Spec fields by stage:**
- **Donor group:**
  - `stage`: "donor_group"; `members`; `donor_set`; `stratum_weights`; `batch`: {segments 32, anchors 8, views 2}
  - `budget`: {epoch_equivalents 30, anchors_per_ep_eq, steps0, continuation "group_wsd_any_last3_ext10_limit60_v1"}
  - `optimizer`: AdamW 1e-3 / 1e-4 / clip 5; `temperature`: 0.1; `bandwidth_multiplier`: 1.0
  - `selection`: {primary "donor_dev_ce_calibrated_v1", sensitivity "donor_dev_gain_v1"}; `lambda_rule`: "min_dev_ce_tie1e-4_lambda1"
  - `montage_augmentation`: "subset3_p05_v1"; `control`: "xm_task_state_matched_derangement_v1"
  - rich only: `rich_targets` {"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}, `loss_weights` [1, 0.5, 0.5], `horizon_from` (the core group id)
  - CSX only: `extra_strata` ["fau_cs"], `horizon_from`
- **Bridge:**
  - `stage`: "bridge"; `donor_group`; `member`
  - `bridge`: "ridge_u_to_stdenv8_v1"; `fit_rows`: "donorfit_2000seg_seed20261016"
  - `alpha`: "logspace(-4,8,13)|bridge_cal_corr"; `temperature`: "bridge_cal_ce_by_poolsize_v1"
  - `sensitivity`: "bridge_cal_fit_2fold_tau_crossfit_v1"; `artefact_probe`: true
- **Target:**
  - `stage`: "target"; `variant`; `init`: "random" | "donor"; `donor_group`; `member`
  - `recipe`: "a_local_recipe_on_aln33_v2"; `epochs`: 200; `nce`: "contract_lse_mask2s_v1"
  - `selection`: {primary "min_es_loss", sensitivity "min_es_loss_minus_mismatch"}; `split_hash`
  - private only: `training_task` "current_class", `target` "current_class", `private_input` "p64_lp20_z64_v1"
- **Zero-shot:**
  - `stage`: "zero_shot"; `variant`; `member`; `donor_group`; `bridge`
  - `mode`: "A" | "B" | "C" | "C_partial"; `view`: "all_participants_trainp_empty_v1"
  - `split_hash`; `job_kind`: "eval"

### 4.4 Budget recap

- Donor groups: S0 = 30 ep-eq ≈ 80.9 k steps for every member of every group. Continuation follows the group rule to at most 60 ep-eq in this version. Rich and CSX groups use the core H*.
- Targets: 200 epochs, as in A_LOCAL and E_LOCAL; two checkpoints are evaluated.
- Bridges and zero-shot units: no gradient steps.

---

## 5. Analysis (frozen with the execution record)

### 5.1 What has been seen, and the analysis note

- The disclosure is §1, "What was known before any result".
- The analysis code `auditory_alignment_v3/prior33/analysis.py` and its tests are written and their sha256 is frozen in the execution record before any donor-group record is read. This section is the ALN3.4 analysis note (`templates/ANALYSIS_NOTE.md`) for the 3401 breadth, the access modes, the panel, rich and CSX.
- Fleet monitoring reads only completion and failure counts, run times and device data. The donor-side quantities that drive the rules (CE_dev curves, the trigger, the λ choice) are read by the code, and their values are reported with the results; they are not test values.

### 5.2 Identities and per-identity values

As SCI_R1_PREREG §2 and ADDENDUM_05 §2:

| cohort | test identities | rule |
|---|---|---|
| FAU | 67: TH-heldout 14, HA 29, CI 24 | The always-train TH selection half is never tested |
| DTU | 44: NH 22, HI 22 | |
| Federici | record → `subject_uid` via `reaggregate/entity_manifest.csv` | HC, CI and HC-v are independent identities; the phantom is excluded from every summary, and its count is listed |
| private | 64 children: HA 55, NH 9 | |

- Per identity and configuration, the value is the mean over that identity's units: content folds, outer folds, records → subject.
- Seeds, folds, content folds and repeated zero-shot evaluations never add to n.
- Donor reuse: one member model per (target, member, objective, seed) serves every cell of its target. It is a fixed upstream. Intervals condition on it (`bootstrap_scope: conditional_on_available_fitted_models_not_full_training_population`).
- Zero-shot values of one identity across content folds come from the same donor and bridge, and are averaged into one identity value.

### 5.3 Endpoints

**Continuous** (FAU, DTU, Federici), in the target-supervised mode T and the zero-shot modes A/B/C:
- **Primary: R = `unified/regular/logloss_bits`**, the candidate cross-entropy (bits per 5-s query) of the true test segment among all test candidates under the unified readout. Mode T uses the training-side ridge and temperature; the zero-shot modes use the frozen donor bridge and τ(n). This is the inherited ALN3 primary.
- Secondary (pointwise intervals only):
  - `unified/gain_bits`, `unified/mismatched_eeg/logloss_bits`, `unified/regular/top1`, `unified/regular/rank_pct`, `unified/hard_gain_bits`;
  - `native/regular/logloss_bits`, where applicable (§2.11);
  - `attention/unified/accuracy` (FAU, DTU);
  - `kernel_cs_diff` (CS_SINGLE only).

**Private** (mode T only), per child:
- **primary NLL** = positive-affine calibrated natural-distribution NLL (bits), via `calib.private_variants`;
- co-primary AUC (positive-affine `auc_score`);
- secondary `hist_gain_bits` and the twin sensitivity `hist_gain_bits − hist_gain_twin_bits`.

### 5.4 Contrasts and families

Every contrast is a within-identity paired difference, written so that **positive = the candidate has lower risk**: ΔR = R(reference) − R(candidate). For AUC it is candidate − reference.

- Families are defined per cohort × objective × mode. Simultaneous 95 % intervals use max-t over the members of a family, with shared replicate indices.
- Pairs are matched on dataset, subject_fold, content_fold, split_hash, target_hash, input-access mode, evaluation version and seed (docs/06). Only the declared independent variable may differ. A mismatched pair is excluded with its reason.

| family | modes | members (reference → candidate) | estimand |
|---|---|---|---|
| INIT | T | S → AP, S → XP, S → J*, S → XM | donor pretraining with this supervision vs scratch, at the same target budget. S → XM is donor-EEG exposure without stimulus-locked pairing |
| SUPERVISION | T, A | AP → XP, AP → J*, XP → J* | AP → J* and XP → J* are OBJECTIVES §4's two separate paired differences; AP → XP compares the supervision types. No max over arms, and no per-child best method |
| CONTROL | T, A | XM → AP, XM → XP, XM → J* | stimulus-locked supervision vs exposure-matched mismatched pretraining |
| RICH | T, A | AP → APR | spectral targets added to audio pairing, at identical batches and equal updates |
| CSX | T, A | AP → APC, XP → XPC (DTU, Federici; private in T) | competing-talker anchors added to the donor pool ("more data of another task") |
| ACCESS (descriptive, pointwise) | A, B, C | A → B (FAU), A → C (FAU, DTU), A → C-partial (Federici), per member | dependence of zero-shot values on the stimulus-informed ICA and on target statistics. Not a method comparison |
| SELECTION (descriptive, pointwise) | T | risk-selected → gain-selected checkpoint, per variant | sensitivity of the selection rule. Donor side: `_best` vs `_h30` vs `_gainsel` on CE_dev and bridge_cal, and the λ choice under both rules |
| PANEL (private) | T | INIT, SUPERVISION and CONTROL as above, per seed 3401, 3407, 3413 | the established `private_transfer` role |

**PANEL details.**
- The role's declared reference, "private local native", is the existing complete E_LOCAL `lag_local_tokens` full rows, 5 folds × 2 objectives at each of the three seeds. It is reported against S and each arm as a **different-input-contract reference** (250 Hz native, 0.5–45 Hz, ALN3 recipe). It is descriptive, not an initialization contrast.
- Three-seed summary, as ADDENDUM_11: the identity value is the mean over seeds. Each table lists the per-seed estimates, the mean, the range and the SD. A contrast without a complete common seed set reports the available seeds and the missing status.

**Per-group levels** are descriptive and pointwise, for groups with n ≥ 5: FAU TH/HA/CI, DTU NH/HI, Federici HC/CI/HC-v, private HA (NH n = 9 reported). No group contrasts and no method choice by group are made here. Group-by-adaptation questions are a separate S34 analysis.

### 5.5 Statistics and seeds

- `sci_r1.stats` is used unchanged: bootstrap-t with per-replicate studentisation, B = 4,000; pointwise symmetric bootstrap-t intervals, with percentile intervals as a secondary column; families by max-t over members sharing replicate b of the identity resampling, seeded by `group_seed(family label)`.
- Non-finite values are excluded upstream, with a listed reason.
- All intervals condition on the fitted donors and targets. Tables outside the panel are labelled "seed 3401 only". An identity bootstrap does not contain the training randomness, and 3 seeds do not estimate the seed distribution precisely; both points are stated. No p-values are reported.
- Effects are shown with their size and scope. Cells are not merely counted by interval sign (ALN3.4 docs/00).

### 5.6 What each contrast does and does not separate

- **INIT > 0** shows that the pretrained initialization lowers risk at this target budget. It does not by itself separate transferable sound structure from easier optimization. S → XM, together with the CONTROL family, separates the two partly.
- **CONTROL > 0** for an arm shows that its stimulus-locked supervision adds beyond exposure-matched pretraining on the same donor EEG. Without it, a gain of that arm over scratch is reported as possibly an exposure or optimization effect.
- **SUPERVISION:** "both supervisions contribute" requires both AP → J* and XP → J* above 0 at the λ chosen on donor dev. A gain only at one λ, or only in one mode, is reported with that scope.
- **RICH and CSX** are data-and-target additions at equal updates. Gains that appear only with more data or more targets are reported as such, not as a loss-function advantage.
- **Zero-shot mode A** values carry the declared target-side preprocessing access. Modes B and C show how much they depend on it. FAU CI values in B and C are not interpretable as neural tracking (§2.13).
- These statements describe estimands. They are not a list of permitted sentences. Interpretation may change with new evidence, and corrections are versioned (ALN3.4 items 2 and 3).

### 5.7 Outputs

- `docs/auditory_alignment_v3/PUBLIC_PRIOR_RESULTS.md` (tables per block), aggregate JSON in `results/auditory_alignment_v3/public_prior/`, and per-identity tables in `private/auditory_alignment_v3/prior33/agg/` (0700). Publication follows the standing rule in AGENTS.md.
- `PUBLIC_PRIOR_EXECUTION_STATUS` (package docs/07, deliverable 4) lists what was actually registered, submitted and completed, refreshed as the blocks complete.

### 5.8 Engineering checks of the analysis (no performance thresholds)

- **Coverage:** every expected unit is present and complete. A missing unit is listed, and its cell is reported on the available identities, with the count.
- **Pairing:** identical participant sets, identical query counts, and `n_test_candidates` equal between mode T and the zero-shot rows of the same cell.
- **Synthetic tests:** known paired differences and signs are recovered; family intervals contain the pointwise intervals; FAU two-content-fold means, HC/HC-v separation and phantom exclusion are correct; a planted pairing-key mismatch is excluded with its reason.
- **Privacy scan** of every public output. The analysis runs as one CPU Slurm job and is not part of any training code hash.

---

## 6. Code: new files only, plus the allowed integration edits

`core.py`, `local_train.py`, the 14 `V2_DEPS` files and all existing runners stay untouched. Behaviour changes come from new files, from a generated copy of `local_train.py` (§2.12), and from in-process `ev1` patches inside `try/finally`, following the `core.evaluate_grid`, `run_transfer`, `local_support` and `residual32` precedents. Each unit is a separate process.

### 6.1 Package `auditory_alignment_v3/prior33/`

| file | contents |
|---|---|
| `__init__.py` | empty |
| `contract.py` | Constants: FS, L_IN = 38, N_TGT = 8, TICK_OFFS, the segment rule and guards, `VOCAB` (70), `ALIASES`, `MONTAGES`, ENV_EDGE = 41, NEIGHBOR = 128, TAU, PROJ_SEED, RICH_SEEDS, PRIVATE_LAYOUT, key bit budgets.<br>Functions: `tick(k)`, `segment_starts(T_stream, T_eeg, cohort, onset=None)`, `aa_fir(fs_in, up)`, `resample64(x, fs_in)`, `private_to64(x)` (reflect pad 75 → 32/125 → LP20; `ONSET64 = 32`), `z64_per_child(x64)`, `env_sos()`, `eeg_sos()`, `lp20_sos()`, `band(x, sos)`, `rms_norm(e)`, `pack_key` / `unpack_key`, `canonical(name)`.<br>numpy/scipy only |
| `select.py` | light (json/os); hashed. `slot_of(row)`, `group_row(row, rows)`, `member_of(row, group_record)` (resolves J* by the λ rule), `slot_member(slot, rows, out)` |
| `views.py` | `open_manifest(path, sha)`.<br>`DonorBank`: role slabs of one cohort's time-major fp16 cache moved to the GPU; segment tables; `gather(piece, start, offs)` → [B, C, 38].<br>`target_view(cohort, cf, manifest, mode="A")`: an ALN `Cohort` of **all** participants, with eeg [C, N] for the mode, `stim['envelope']` [1, M], segments carrying e0/s0/s0_ign/role/kind/uid/hard_key/part/feat, participants, layout and `meta` (dataset, content_fold, seg_len 320).<br>`load_private64()`: `data.load_private()` plus `x64` per child (LP20 and the 64 Hz z-score, in memory).<br>`TickBatcher(Batcher)` (rows on ticks, packed keys, `train_p` override); `TickReps(ev1.Reps)` (offs = TICK_OFFS); `PrivateBatcher64(PrivateBatcher)` |
| `model.py` | `NameIndexedSpatial`, `SharedEncoder` (`forward`, `forward_tokens`, `trunk`), `RichHeads`, `SharedFixedHead(σ, P)` (μ ≡ 0), `build_shared(layout, train_names, seed)`, `build_target_encoder(row, layout, manifest, donor_state)`, `load_donor(enc, state, layout, open_new=True, strict=True)` → tensor map, `describe()` |
| `losses.py` | `masked_lse_nce(S, pos, excl)`, `nce_audio_pair`, `nce_cross_person`, `nce_single_view`, `cs_audio_pair`, `cs_cross_person` (both via the imported `cs_qmi`), `calibrate_sigma`, `ContractObjective(Objective)` (continuous path; the labels/prototypes path delegates unchanged) |
| `rich.py` | rich head pairs, `rich_loss(u_heads, v_heads, present, objective)` with the §2.15 normalisation, the donor-side rich readout |
| `sampler.py` | `DonorSampler(manifest, donor_set, block, seed, device)` with `next_batch()`, `derangement(batch)`, `stream_hash()`, `state()`, `load_state()`; `selection_sets()`; `bridge_rows(donor_set)`; montage masks |
| `donor_train.py` | `train_donor_group(row, manifest, dev, ckpt_prefix, log, max_steps=None)`; `dev_scores()` (CE_dev, gain, r̄_own); `GroupWSD` (schedule, group trigger, side branch, compute limit, adopted horizon); resume |
| `bridge.py` | `fit_bridge(enc, …)`; `save_bridge` / `load_bridge`; `FrozenBridge(ev1.Readouts)`; `artefact_probe()` |
| `gen_fit_target.py` | writes `fit_target.py` from `local_train.py` with the asserted substitutions of §2.12; hashed |
| `fit_target.py` | generated: `fit_continuous_p33`, `fit_private_p33` (two selection rules); hashed |
| `target_train.py` | `adapt_public(row, manifest, dev, ck, log, donor_state)` and `adapt_private(…)`: build the view, train with the generated copy, evaluate both checkpoints |
| `zeroshot.py` | `evaluate_zero_shot(row, manifest, dev, donor_state, bridge)`: applies the §2.13 procedure and asserts that no training participant is used and that no ridge is fitted on target data |
| `run_donor.py`, `run_bridge.py`, `run_target.py`, `run_zeroshot.py` | `run(row, out, epochs=None)`. Each verifies `manifest_sha256` and re-checks dependencies; a missing dependency is written as a `technical_failed` record, never as a silent return. Each uses `core.new_record` and `core.write_record`, overwrites `target_contract`, records `mode`, coverage, normalisation access, selection level and `view_sha256`, and catches all exceptions into `technical_failed`. `epochs` caps steps or epochs for probes only |
| `deps.py` | light, not hashed. Imported by `make_queue` and `ckpt_offload`. `upstreams(row, rows)`, `ready(row, rows, out)` (upstream record complete and checkpoint/npz present), `blocked(row, rows, out)` (an upstream, transitively, has a `.failed` marker), `ckpt_deps(row, rows)` (the owning group ids, until every dependent is done), `order_key(row)` (tier, then donor < bridge < target < zero-shot, then dataset and folds), `write_queue(out, rows, held)` (writes `queue_v3_prior.txt` with three-field lines `eid\|idx\|up1,up2` (§6.5), `queue_v3_prior_weights.txt`, `queue_v3_prior.remaining`, `.waiting` and `.blocked`), `WEIGHTS` |
| `analysis.py` | §5; not hashed in any training group; its sha256 is frozen in the execution record |
| `cache_build.py`, `audit_align.py`, `scan_audio.py`, `rich_build.py`, `manifest.py` | CPU builders (§6.2) |

### 6.2 CPU jobs, memmap caches and the manifest

All of these run through the new `slurm/aln33_prior_cpu.sbatch`, a copy of the `bc_interim_cpu.sbatch` pattern: `--partition=CPU`, normal QOS (no runfill), 4–8 CPUs, 16–32 GB, `--time=2-00:00:00`, `--open-mode=append`, logs under `private/auditory_alignment_v3/logs/`.
- The user's normal-QOS total stays at 25 jobs or fewer, so other sessions keep their headroom.
- Each job is resumable per item, with done markers and tmp + `os.replace`.
- Order: C1, then C2, C3, C4, C5 and C7 in parallel (C7 needs C1's and C5's stream tables), then C6.

**C1. `cache_build sparrkulee-table`** (minutes).
- Reads `.npy` headers, `events.tsv`, `.save_metadata.json` (with its 2 duplicate keys) and `participants.tsv`. Produces the run table: sub, ses, run, stimulus, condition and SNR, T_eeg, T_env, flags, role, and the sha256 of each source file.
- Restricted participants appear from file names and headers only.
- Computes the structural-anomaly flags (§3.2).
- Asserts 666 runs, the 3 README-flagged runs absent, and the 72 envelope files.

**C2. `audit_align`** (2–3 CPU-h). The clock-validity rule of §3.2: ±40 s search, measurability z ≥ 5, references without restricted participants. Writes `align_audit.jsonl`.

**C3. `scan_audio`** (≈1 h). Cross-cohort overlap, within-cohort duplicates and jingles, family merges and offsets, Federici natural/vocoded lags, SparrKULee `audiobook_1` offsets (§3.4). Writes `scan_audio.json`.

**C4. `cache_build sparrkulee`** (≈30–45 min).
- Processes participant by participant: read float64 → 1–20 Hz filter → QC mask → statistics → normalise → zero the masked cells → write float16. Restricted participants are skipped before any array is opened.
- Writes into `/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1/sparrkulee/eeg_f16_tmajor.npy`, created with `np.lib.format.open_memmap(…, 'w+', np.float16, (N, 64))`.
- **Layout:** time-major, rows ordered by role: fit, dev, bridge_cal, holdout, control, excluded-by-rule. A 38 × 64 window is one contiguous 4,864-byte read, and each role is one sequential slab.
- **Size:** ≈4.3 GB.
- Also writes:
  - `runs.json`: ids, role, flags, row_offset, T_eeg, T_env, segment starts, masked channels, per-channel mean and pre-z SD, source sha256;
  - `env_f32.npy` + `streams.json`: per presentation, the 2–8 Hz RMS-normalised envelope, its offset, family, family_offset and RMS (14.6 MB);
  - per-run done markers.
- Sanity checks: a full NaN/Inf scan, and CAR confirmed (max |Σ_ch| / median SD).

**C5. `cache_build public`** (≈45 min). Produces `fau/`, `dtu/` and `federici/`:
- `eeg_f16_tmajor.npy` [N, C], mode A: resampled, DTU re-referenced to CAR, normalised per §2.1, masks zeroed;
- FAU `eeg_noica_z_f16_tmajor.npy` (mode B), and, where mode C is supported, `eeg_raw_f16_tmajor.npy` in µV (FAU noica, DTU, Federici; mode C);
- `pieces.json`: participant, identity uid, group, fold, trial or block, kind (ss/cs), stimulus ids, presentation id, family id and offset, attended side, masker or distractor lead, row_offset, length, segment starts, pre-z SD;
- `env_f32.npy` + `streams.json`;
- the physical unit of each cache, with its basis.

The total is ≈4 GB. The same arrays serve these cohorts' donor, target and zero-shot units, so all views are identical by construction.

**C7. `rich_build`** (≈1 h). §2.15:
- SparrKULee `.npz.gz` validation and log-mel extraction (FAU and DTU log-mel are reused);
- 64 Hz resampling; the PCA-4 basis fitted on the unique SparrKULee donor-fit windows; flux; 2–8 Hz; RMS;
- the clock checks.

Writes `rich_f32.npy` [M, 5] aligned with each cohort's `env_f32.npy`, `rich_streams.json` (availability, clock lag, extractor version, source sha), `rich_pca4_f64.npy`, σ_ss, σ_sc, P_ss and P_sc.

**C6. `manifest`** (minutes). The manifest is frozen before any donor unit runs. It holds:
- the roles and exclusions, with reasons and rule outputs;
- shared-audio and overlap masks, families and offsets;
- segment tables and anchor pools per block (core, CSX `fau_cs`);
- N_SK, S0 and the stratum weights for each donor set and block;
- the standardiser (σ, the μ estimate), the P file with its sha, and the rich basis and projections;
- filter shas;
- vocabulary, montages, seen sets and coverage;
- the 30 cell bindings with split hashes, where private IDs are stored only in the 0700 copy;
- the selection and bridge sample lists;
- mode-C support per cohort, and the scales;
- the HC/HC-v exclusion count, and the DTU trial reconciliation;
- the unused-record table;
- the builder code sha256.

It is written to `…/derived/aln33_env64_125ms_v1/manifest.json` (0444). A copy goes to `private/auditory_alignment_v3/aln34/prior33/manifest.json` (0444), and its sha256 enters every row spec.

No private data is cached: `load_private64()` resamples, filters and normalises in memory inside each unit. Nothing from the dataset's `code/` is run. `*.data_dict` and `*.pkl` files are never opened. `stimuli/eeg/<stim>.npz.gz` members are read only by C7, with gzip and `np.load(…, allow_pickle=False)`.

### 6.3 `registry.py` and `run.py` additions

Both edits follow the same safety steps:
- write a backup `private/auditory_alignment_v3/{registry,run}.py.before_prior33_<date>`;
- write a tmp file, import-test `auditory_alignment_v3.core` and `auditory_alignment_v3.run` in the eeg2025 interpreter, then `os.replace`;
- before `os.replace`, assert that there are no key collisions in `FAMILY_CODE`, `FAMILY_GROUP` and `RUNNER`, and that every existing family's `code_hash` is unchanged, against its latest unit record.

```python
# registry.py — appended after FAMILY_GROUP (E34_PUBLIC_PRIOR; PUBLIC_PRIOR_DESIGN.md §6.3)
_p33 = lambda *fs: [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
                   [("auditory_alignment_v3/prior33", f) for f in fs]
FAMILY_CODE.update({
    "prior33_donor":      _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "donor_train.py", "run_donor.py"),
    "prior33_rich_donor": _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "rich.py", "donor_train.py", "run_donor.py"),
    "prior33_bridge":     _p33("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "bridge.py", "run_bridge.py"),
    "prior33_target":     _p33("contract.py", "views.py", "model.py", "losses.py", "select.py", "gen_fit_target.py", "fit_target.py",
                               "target_train.py", "run_target.py")
                          + [("auditory_alignment_v3", "calib.py"), ("auditory_alignment_v3/aln3_reference", "calibration.py")],
    "prior33_zeroshot":   _p33("contract.py", "views.py", "model.py", "select.py", "bridge.py", "zeroshot.py", "run_zeroshot.py"),
})
FAMILY_GROUP.update({"ALN32_PUBLIC_AUDIO_PRIOR_DONOR": "prior33_donor", "ALN32_PUBLIC_AUDIO_PRIOR_CSX_DONOR": "prior33_donor",
                     "ALN32_PUBLIC_AUDIO_PRIOR_RICH_DONOR": "prior33_rich_donor", "ALN32_PUBLIC_AUDIO_PRIOR_BRIDGE": "prior33_bridge",
                     "ALN32_PUBLIC_AUDIO_PRIOR_TARGET": "prior33_target", "ALN32_PUBLIC_AUDIO_PRIOR_ZEROSHOT": "prior33_zeroshot"})

# run.py — appended after RUNNER (module path is imported as auditory_alignment_v3.<value>)
RUNNER.update({"prior33_donor": "prior33.run_donor", "prior33_rich_donor": "prior33.run_donor", "prior33_bridge": "prior33.run_bridge",
               "prior33_target": "prior33.run_target", "prior33_zeroshot": "prior33.run_zeroshot"})
```

### 6.4 Plan rows: `private/auditory_alignment_v3/make_plan_ext_prior33.py`

The pattern follows `make_plan_ext_block7.py`:
1. Assert the **live** `plan_ext.jsonl` line count and sha prefix at execution time. At 20:5x and again at 22:39 these were 3,325 and `85b44d8d…`. Other ALN3.4 lanes may append first, in which case re-base the guard; never skip it.
2. Read the frozen manifest and its sha.
3. Build the blocks of §4.1, with the dependencies resolved to ids inside the block. Mode-C rows are built only for cohorts the manifest supports.
4. Assert:
   - the per-block and per-family counts (540 / ≤ 210 / 120 / 126 / 158);
   - unique ids;
   - no collision with existing ids;
   - every dependency is inside the block, or is the block's own core group.
5. Append via tmp + `os.replace` and print the new sha.

`--continuation <gid>` builds, under the same guard, the continuation version of one group and its downstream rows (§2.10). It requires that the group's record has `ceiling_reached_while_improving: true`.

Queue indices of existing rows do not change: an index is 100000 + the position in `plan_ext`.

### 6.5 Queue, pool, keeper, offload and watcher integration

Each file gets a backup before editing, and each edit is import-tested.

**Live-edit order** (pinned; a broken `registry.py` or `run.py` would make every new unit of the fleet fail, and those failures count toward the 3 tries):
1. Add `prior33/` (including the generated `fit_target.py`), the tests, the four sbatch files and `keeper_prior.sh`. Run the synthetic tests as one Slurm CPU job.
2. Edit `registry.py` and `run.py` (§6.3).
3. Edit `ckpt_offload.py`:
   - `NO_DEPS |= {…_DONOR, …_CSX_DONOR}` (the CSX group reads only the core group's record); `HANDLED |= {…_RICH_DONOR, …_BRIDGE, …_TARGET, …_ZEROSHOT}` (the rich group also loads the core AP checkpoint for its donor-side readout);
   - in `deps_of`, add the branch `elif f.startswith("ALN32_PUBLIC_AUDIO_PRIOR_"): out |= set(P33.ckpt_deps(r, rows))`;
   - **restart daemon 1040276 gracefully**: `scancel --batch --signal=TERM 1040276`. The sbatch traps TERM and lets the daemon finish its current file. Then resubmit `slurm/aln3_ckpt_offload.sbatch` at once. Expect at most a 3-minute watcher window.
   - The daemon holds a flock and loads its constants once. If the restart is skipped, any queued prior row makes every pass fail closed for the whole fleet.
4. Append the plan block (§6.4).
5. Edit `make_queue.py`:
   - add `QUEUES["prior"] = [the six families]`;
   - for `q == "prior"`, inside a `try`, call `deps.write_queue(O, ALL, held=HELD ∪ families_on_hold)` and skip the generic path. The `prior33` import is inside the `try`. On any exception, print the error and write the prior queue and counters empty, so the fm and small queues are never affected;
   - the existing family filters do not touch these families;
   - the remote refresher starts `make_queue.py` as a fresh process every 10 min, so the edit takes effect without touching the refresher.
6. Edit `watch_anyhost.sh`: add the spec `"queue_v3_prior c3_aln3pr 4"` and restart the watcher in its session. Then submit the keeper job, which submits the workers.

**Queue lines.** The prior queue's lines are `eid|idx|up1,up2,…`.
- `ckpt_offload.queued()` (`split("|", 1)[0]`), `keeper.sh`'s and the watcher's `unclaimed()` read only the first field, so they are unaffected.
- The counters `queue_v3_prior.remaining`, `.waiting` and `.blocked` (the last a list of eids) do not end in `.txt`, so the offload daemon's `queue_v3_*.txt` glob never reads them.

**New `slurm/aln33_prior_pool.sbatch`.** A copy of `aln3_gpu_pool.sbatch` with these changes:
- job name `c3_aln3pr`;
- no `--nice`;
- **no `--time`**: the user's rule is no time limit on V100/A40, and A100 is excluded here. With `DefaultTime=NONE`, a worker's limit is the partition maximum: L40S 1 day, V100 2 days, A30 and A40 4 days. Running units resume from their checkpoints after a timeout;
- `--partition=V100,A30,A40,L40S`, leaving the A100s with FM;
- `Q = queue_v3_prior.txt`, with three fields parsed per line;
- **a polling loop in place of the pass-and-wait loop** (the source loop reads the queue once per pass, blocks on the current row until it fits, and then `wait`s for every running unit):
  - every 30 s: reap finished children, re-read the queue, the weights and `.blocked`;
  - walk the rows in queue order, skipping rows that are done, failed, blocked or claimed, rows whose upstreams lack a complete record, and OOM-marked rows on cards < 20 GB;
  - admit a row when fewer than PAR units run and its weight fits CAP; otherwise **continue with the next, lighter row**. A row always starts on an idle card;
  - claim with `mkdir`, launch, keep the 20-s stagger;
- **exit rule**: `STOP_queue_v3_prior` exists, or `.infra_<jobid>` (stop claiming, wait for running units, exit), or no unit has run and no row has been admissible for 20 consecutive minutes. In the last case the GPU returns to the FM lane, and the keeper resubmits when rows become ready;
- claims, tries, OOM and INFRA handling, MPS, weights and the `_last.pt` cleanup are unchanged.

**Keeper.** `private/auditory_alignment_v3/keeper_prior.sh` runs as `slurm/aln33_prior_keeper.sbatch`: CPU partition, 1 CPU, 1 GB, no `--time` (CPU maximum 4 days), output `logs/keeper_prior.log`, append mode.
- Every 60 s it counts the ready unclaimed rows, using the same three-field test as the worker.
- If there are any, and there are fewer than 4 `c3_aln3pr` jobs and fewer than 2 pending, it submits one worker at nice 0.
- It writes a heartbeat line every loop, so the watcher sees it alive.
- It stops when `.remaining` is 0, or on `STOP_queue_v3_prior`.
- If `sbatch` is refused from compute nodes (the probe checks `sbatch --test-only`), the same script runs in the session, like the existing keepers.

**`ckpt_offload.py` details.**
- Its EID regex `^(ALN3X?_[0-9a-f]{16})(?:_[A-Za-z0-9]+)*_best\.pt$` matches `<gid>_m<M>_best.pt`, `_gainsel_best.pt` and `_h30_best.pt` with owner `<gid>`. It does not match `_bridge.npz` or `_stable57.pt`.
- Its `queued()` and `claims()` globs already cover `queue_v3_prior.txt` and `pool/queue_v3_prior/`.
- `_best.pt` files are offloadable once their unit is done and no pending row depends on their group. `_bridge.npz` never is.

**`watch_anyhost.sh`.** The fm spec stays `c3_aln3fm 10` (§8 explains why it does not alarm). The prior spec raises an EVENT if the keeper's log is stale for 10 min while workers are missing and rows are unclaimed.

**Probe and CPU entry points.**
- New `slurm/aln33_prior_gpu_probe.sbatch`: a copy of `aln2_gpu_probe.sbatch` with `--partition=V100,A30,A40,L40S`, no nice, and ALN3 logs.
- New `private/auditory_alignment_v3/probe_prior33.py`.
- The CPU sbatch of §6.2.

### 6.6 Implementation modules (for parallel agents)

| module | files | depends on (interfaces) |
|---|---|---|
| M0 provenance and guards | `aln34/prior33_provenance/`, live hash list | — |
| M1 contract and fixtures | `contract.py`, `tests/…/prior33/fixtures.py` (a synthetic manifest and caches) | — |
| M2a SparrKULee builders | `cache_build.py` (C1, C4), `audit_align.py` (C2) | M1 |
| M2b public builders | `cache_build.py public` (C5, mode-C units and scales) | M1 |
| M2c scan | `scan_audio.py` (C3) | M1 |
| M2d rich builder | `rich_build.py` (C7) | M1; C1 and C5 stream tables |
| M2e manifest | `manifest.py` (C6) | M2a–d output schemas |
| M3 views and sampler | `views.py`, `sampler.py` | M1, manifest schema (fixture) |
| M4 model and losses | `model.py`, `losses.py`, `rich.py` | M1 |
| M5 donor training | `donor_train.py`, `run_donor.py` | M3, M4 |
| M6 bridge and zero-shot | `bridge.py`, `run_bridge.py`, `zeroshot.py`, `run_zeroshot.py` | M3, M4 |
| M7 target training | `gen_fit_target.py`, `fit_target.py`, `target_train.py`, `run_target.py` | M3, M4 |
| M8 dependencies | `select.py`, `deps.py` | row schema (§4.3) |
| M9 plan and registry | `make_plan_ext_prior33.py`, registry/run.py snippets | M8, manifest sha |
| M10 infrastructure | the four sbatch files, `keeper_prior.sh`, make_queue/offload/watcher patches | M8 |
| M11 analysis | `analysis.py` and its tests | record schemas (§2.10–§2.13) |
| M12 probe | `probe_prior33.py` | all |
| M13 execution record | `E34_PUBLIC_PRIOR_EXECUTION_RECORD.md` | all, frozen manifest |

---

## 7. Tests and engineering probe (engineering only; no performance thresholds)

### 7.1 Synthetic tests

Location: `tests/auditory_alignment_v3/prior33/`. They run as a Slurm CPU job; precedents run under one in about 10 min.

1. **Grid.**
   - i_k matches `np.round(1.28 k)`, with no ties.
   - i_{k+25} = i_k + 32.
   - TICK_OFFS has length 250 and maximum 319.
   - The segment rule gives the spans 357 and 327 and starts that are multiples of 32; the competing-talker onset rule rounds up to a multiple of 32.
   - Anchors stay within [0, 249] and lie on ticks.
   - `TickReps` offsets equal TICK_OFFS.
2. **Resampling and private input.**
   - `h_aa` passband ≤ 0.02 dB and stopband ≤ −59 dB.
   - Sine gains: 10 and 20 Hz ≈ 1; 34 and 40 Hz < 10⁻³.
   - Pulse timing is preserved for 1/2 and 16/25.
   - The private onset lands at output index 32. After LP20, 25 Hz is attenuated by > 10 dB and the edge transient is < 1e-3 inside [32, 70). `z64_per_child` gives unit variance per channel.
   - The filter shas are stable.
3. **Envelope.**
   - (a) The filter is zero-phase, and ≥ 99.9 % of the energy lies within ±41 samples.
   - (b) The RMS of each normalised stream is 1, and y windows never touch the 41-sample edges.
   - (c) **Scale invariance:** with μ ≡ 0, scaling a stream by 0.1 or 10 leaves v, the unified score, the native NCE and CS scores, kernel dependence and the NCE and CS losses unchanged to 1e-6.
   - (d) The manifest stores μ as zeros, and the μ estimate separately.
4. **Keys and pairs.**
   - (a) No self pairs; partners are different participants with the same presentation and tick.
   - (b) Family-clock masks are correct for synthetic halves at +1,711 and +30,986 samples; the boundary at exactly 128 samples is masked; positives are never masked.
   - (c) DTU HI rows are never cross-person eligible.
   - (d) Keys are unique per anchor.
   - (e) `pack_key` raises when any bit budget is exceeded, and `unpack_key(pack_key(·))` is the identity.
   - (f) A Federici pair with a known lag, and a scan-merged duplicate, get the right family offsets; an "unknown clock" pair masks the whole partner item.
   - (g) **Rolled path:** for a `fit_continuous` rolled early-stopping batch, `ContractObjective`'s mask equals the mask computed from the rolled audio's keys.
   - (h) HC N / HC-v N pairs are never drawn.
   - (i) XM: π satisfies the hard constraints on feasible batches, violations are counted on infeasible ones, XM keys equal X₁'s, and the main stream is unchanged by the derangement generator.
5. **NCE.**
   - With unique keys and no mask, it equals `symmetric_infonce`.
   - With repeated keys it differs from `deduplicated_infonce`.
   - Gradients are finite.
   - Removing the mask changes the value exactly as expected on a hand case.
6. **CS.**
   - `cs_audio_pair` equals `cs_qmi` with v duplicated.
   - The two orderings of cross_person are symmetric.
   - The estimator approaches log n when σ → 0.
   - The CS functions take no mask argument.
7. **Spatial map, head and loading.**
   - (a) Equivalence to `Conv1d` (≤ 1e-6).
   - (b) Unseen-channel perturbation gives an output change of 0, and unseen rows get zero gradient.
   - (c) P sha is 706c4ff4…, Pᵀ P = I, rank 8, and the state-dict keys match `FixedFeatureHead`.
   - (d) **Strict loading:** a shape mismatch raises; the rich heads are dropped and listed; the generated private path builds 36 tokens at 64 Hz on the 20-name layout, and contains no `build_encoder(…, 250)` call; the tensor map's `new` and `missing` are empty.
   - (e) The private path's `Objective` is the unpatched class.
8. **Leave-target-out and data use.**
   - 10⁴ sampled batches per donor set and block contain no target-cohort piece.
   - `private_bdf` and the phantom never appear.
   - SparrKULee roles are disjoint by participant and family.
   - Jingle spans are absent from all pools.
   - The flagged runs and the rule-excluded runs are absent.
   - An open-file audit hook shows that no restricted participant's array is opened by C2, C4 or the sampler.
   - `fau_cs` appears only in CSX pools.
9. **Zero-shot purity.**
   - With a synthetic cohort, the zero-shot view's test pool equals the adapted view's pool.
   - `train_p` is ∅; `train_segs` and the early-stopping query list are empty.
   - `FrozenBridge` defines every attribute `ev1` reads.
   - `ev1._ridge` raises if called.
   - Mode C: changing a target participant's variance changes the mode-A input but not the mode-C scale.
   - Metrics come out finite.
10. **Determinism, lockstep and budget.**
    - (a) Every member of a group receives identical batches, and two runs with the same seed give identical streams and stream hashes.
    - (b) The group trigger extends when any contract member is still improving, and ignores XM.
    - (c) The side branch reproduces the 30-ep-eq decay exactly.
    - (d) The compute limit sets the flag and retains the stable states.
    - (e) Resume in the middle of a side branch reproduces the next batch and the curves.
    - (f) A rich or CSX group adopts H* from the core record.
11. **Selection.**
    - CE_dev on a hand case equals the closed form.
    - The λ tie rule holds.
    - Both donor checkpoints and both target checkpoints are written, and identical epochs are recorded as identical.
    - The generator applies each substitution exactly once and fails on drift.
12. **Rich.**
    - Object or structured `.npz` members are rejected, and the stream is marked unavailable.
    - The clock check flags a shifted synthetic stream.
    - Masked heads contribute zero; the normalised loss scale is the same for a batch with one head and a batch with three.
13. **Plan block and dependencies.**
    - On a temp copy, the block builder yields the §4.1 counts, unique ids and internal dependencies.
    - `deps.ready` holds only when the upstream record is complete and its file exists.
    - `blocked` propagates transitively from a `.failed` marker.
    - The queue lines have three fields and the counters are consistent.
    - `code_hash` of every existing family is unchanged after the registry edit.
14. **Analysis** (§5.8).
15. **Pool and keeper** (bash, on a temp directory with fake runners):
    - a light row is admitted while a heavy row does not fit;
    - the worker exits after 20 idle minutes (time-compressed);
    - blocked rows are ignored;
    - STOP and infra stop claiming;
    - the keeper submits only when ready rows exist and caps at 4.

### 7.2 Engineering probe on real data

The probe is `probe_prior33.py`, run as one GPU job on any of **V100, A30, A40 or L40S**. Measured peak memory is checked against the budget of the smallest card in the pool: V100-16GB, CAP 13 GB. The probe writes only to `private/auditory_alignment_v3/probe_out_prior33/`, never to `units/`.

1. **Shapes and integrity.**
   - Cache shapes match `runs.json` and `pieces.json`.
   - One SparrKULee run is reproduced from its source `.npy` through the same filter and normalisation (equal to within fp16 rounding).
   - The masked-cell count matches.
2. **Time access.**
   - Perturbing EEG outside [i_k, i_k+38) leaves the outputs unchanged; perturbing inside changes them.
   - No window crosses a guard.
   - The private window is [32, 70).
3. **Alignment.**
   - The C2 decoder is recomputed on cached data for 3 aligned runs; expect |τ̂| ≤ 4.
   - Envelope index 0 is confirmed as the row offset of each presentation.
   - The C7 clock lag is 0 ± 1 for 3 SparrKULee, FAU and DTU streams.
4. **Channel coverage.** Seen/total counts per target, and masked counts per FAU participant.
5. **Loss sanity.**
   - At initialisation, every member's NCE is near its chance value and CS is finite.
   - σ values are recorded.
6. **Tiny-batch overfit.**
   - Setup: one fixed donor batch (32 × 8 × 2), 300 steps, a 5-member group for each objective.
   - The NCE loss should fall and CS should rise for AP, XP and J*. XM is expected not to learn a stimulus-locked score. A flat or non-finite curve for a contract member is treated as a bug.
7. **Short real runs:**
   - donor: one core group (FAU, NCE) for 2 ep-eq and one (FAU, CS) for 1 ep-eq; one rich group for 1 ep-eq, if C7 is done; one CSX sampler pass;
   - bridge: one member;
   - zero-shot: FAU sf0/cf0 in modes A, B and C; DTU sf0/cf0 in mode C;
   - target: FAU sf0/cf0 and private sf0, 2 epochs each, from scratch and donor-initialised.
8. **Resources.** Measured: ms per step per member, steps per ep-eq, load seconds per slab, GPU peak, host RSS peak, and time per target epoch. From these the probe sets the queue weights (§4.1) and extrapolates the fleet (§8). `sbatch --test-only slurm/aln33_prior_pool.sbatch` is run from a CPU job for the keeper check.

---

## 8. GPU estimate and scheduling

**Estimate.** Packed units under MPS, from ALN3 measurements: 7–12 ms per 256-row step; A_LOCAL 186–333 s per unit at 1.8–2.2 GB peak.

| stage | units | per unit | GPU memory | GPU-h | card-h, packed |
|---|---|---|---|---|---|
| donor groups | 26 (80 member trainings) | per member: 81 k steps × 10–20 ms ≈ 13.5–27 min at S0; × 1.0–1.6 with continuation | ≈5–7 GB (bank ≈4.5 GB fp16) | 18–58 | ≈9–29 (2–3 per card) |
| bridges | 68 | 3–6 min | ≈2–3 GB | 3–7 | ≈1–3 |
| targets | 540 | 5–8 min, including the second-checkpoint evaluation | ≈2 GB | 45–72 | ≈11–20 |
| zero-shot | ≤ 520 | 1–2 min | < 1 GB | 9–17 | ≈3–6 |

- **Total:** ≈24–58 card-hours; tier 1 alone ≈11–25. On 4 GPUs that is ≈3–7 h of wall time for tier 1 and ≈6–15 h for everything. The critical path (a core group, then the rich or CSX group that adopts its horizon, then their downstream rows) is ≈7–12 h.
- **Before the fleet:** the CPU jobs (C1; then C2–C5 and C7 in parallel; then C6; ≈2–3 h), the tests (≈15 min) and the probe (≈1–1.5 h).
- This revision roughly doubles the earlier 12–20 card-h estimate, because of the controls, the access modes, the panel, rich and CSX.

**Share: up to 4 of the 10 c3 runfill GPUs, through dedicated workers.**
- Prior rows cannot simply join the fm queue:
  - a worker opens the queue file once per pass and keeps reading that snapshot;
  - fm passes last hours, so new rows would wait;
  - nothing there would cap the prior at 4 cards.
- The FM keeper and the refresher run on another host and cannot be restarted from here. The design therefore does not touch them.

**Sequence:**
1. **Probe slot.**
   - Submit the probe at nice 0. It outranks the nice-50 replacements that the FM keeper submits, so it takes the next runfill GPU that frees on one of its four partitions.
   - To speed this up, touch `private/auditory_alignment_v3/pool/queue_v3_fm/.infra_<jobid>` for the FM worker whose running units are closest to completion. This flag is the pool's only graceful stop for running workers: the worker finishes its current units and then exits with the log line "infrastructure failure…", which is expected and noted in `operations.log`.
   - Draining frees a QOS slot, not a particular card; the slot may come only when some worker ends (FM workers have a 24 h limit). That latency is accepted.
2. **Fleet.** Once the probe passes, the execution record is frozen and the rows are registered in the §6.5 order. Then:
   - submit the keeper job, which keeps up to 4 `c3_aln3pr` workers at nice 0;
   - optionally drain up to 4 FM workers, starting with those whose units are oldest, so the slots free sooner.
3. **Steady state.**
   - FM runs 6 workers, and the FM keeper holds ≤ 3 pending replacements.
   - Total running c3 jobs stay ≤ 10, the runfill cap.
   - The watcher's fm check sees 9 `c3_aln3fm` jobs with 3 pending, so it raises no false alarm.
4. **Idle periods.** When no prior row is ready for 20 minutes (for example, while the last donor groups train), idle prior workers exit, and pending FM workers take the slots. The keeper resubmits as soon as rows become ready.
5. **End.** The keeper stops when `.remaining` is 0. `STOP_queue_v3_prior` stops the prior lane at any time.
6. **Unit order inside the prior queue:** tier; then donor groups, bridges, targets and zero-shot units; then dataset and folds. From-scratch targets are runnable from the start and fill gaps; the other rows start as their dependencies complete.

---

## 9. Risks and open questions

### Risks

| # | risk | mitigation |
|---|---|---|
| 1 | Undetected misaligned SparrKULee runs would silently corrupt cross-person positives. The receipt's probe C left 19 % of runs off-peak, without per-run identities. | Full audit C2 under a fixed clock-validity rule (±40 s) before the freeze. Unverifiable runs are kept and counted, and excluded runs are listed. |
| 2 | Shared jingles act as NCE false negatives and leak across roles. | Two-stage scan and mask in all roles; within-cohort duplicate scan for every donor cohort (§3.4). |
| 3 | The cross-person signal is weak (inter-listener r median 0.0055; decoder r 0.03–0.13). Shared stimulus-locked non-neural components could be learned instead. | The XM control in every group; the artefact-run probe; mismatched dev scores logged. |
| 4 | Reference, band and montage differ across cohorts: SparrKULee CAR-64, FAU average-31 with ICA, Federici 2–8 Hz average-32, private 0.5–45 Hz average-20. CAR over different montages is not the same signal, and 36–44 donor channels are absent from FAU, Federici and private. | SparrKULee is harmonised to 1–20 Hz; DTU to CAR; private to < 20 Hz and z-scored at 64 Hz; montage-subset augmentation; per-target coverage recorded. The Federici band cannot be harmonised; this is declared. |
| 5 | Bridge optimism: the donor-fit bridge is in-sample for audio_pair but out-of-sample for cross_person. | All members get the same rows; the sensitivity bridge B_uni_cal, with its cross-fitted τ, is reported next to the main result. |
| 6 | Zero-shot inputs carry target-side whole-recording z-scores and, for FAU, a stimulus-informed ICA. | Naming and access declaration; modes B and C (§2.13). |
| 7 | The 64 Hz model geometry (36 tokens), the target-stage NCE mask and the private 64 Hz input depart from ALN3 native. | All arms share them, and they are declared. Native ALN3 rows remain different-contract references and are never mixed into contrasts. |
| 8 | Unequal updates between arms. | Removed by the lockstep group horizon. Equal-update `_h30` models and all curves are kept. Joint's second λ is declared extra compute. |
| 9 | Infrastructure failures: a hashed-file edit would re-hash every group; an unmodelled family makes offload fail closed fleet-wide; an import error in `make_queue`, `registry` or `run.py` breaks refresh or unit start quietly. | New files only; the pinned live-edit order (§6.5); atomic, import-tested edits with backups; prior import errors are trapped inside `make_queue`. |
| 10 | Parallel ALN3.4 lanes edit the same `plan_ext`, `registry`, `run.py` and `make_queue`. | Live guards in the block script; `.update` blocks appended, never rewritten. |
| 11 | NFS IO (≈70–110 MB/s). | Sequential role slabs; a 20-s stagger between unit starts; fp16 caches. |
| 12 | Private epochs leave the last ≈230 ms of the window dependent on padding, and the window cannot be recut. | Recorded. |
| 13 | Licences: SparrKULee is CC BY-NC 4.0 (stimuli for non-commercial use only); DTU audio is research-only with no redistribution. | Derived weights are non-commercial; caches and rich features stay under `/projects`. |
| 14 | A lockstep group is a larger failure domain: one failure stops 5 members. | Resume at every validation; 3 tries; per-member non-finite handling. |
| 15 | Blocked dependents of a failed unit could idle GPUs. | Blocked rows are listed and never counted as waiting; workers exit after 20 idle minutes; the watcher reports the failed marker. |
| 16 | A SparrKULee `.npz.gz` member may not be a plain numeric array. | It is rejected with `allow_pickle=False`, and the stream's rich targets are masked and listed. The core is unaffected. |
| 17 | The physical units of the caches may be uncertain. | Mode C is registered only for cohorts with an established unit. |
| 18 | Compute is about twice the earlier estimate. | Tiers order the work; the 4-GPU share and the 10-GPU cap are unchanged. |

### Questions that need the researcher

None. Every decision above is an engineering or contract-interpretation matter, settled under ALN3.4 items 1, 6 and 11, and declared.

Note, for information only: the 5 access-restricted SparrKULee participants stay excluded, as the host's `dataset_description.json` states for the re-host. Including them would need the provider's data-use agreement, which only the researcher could request, and a new manifest version built before the first donor result. Nothing waits on it.

---

## 10. Reuse for the CBraMod continual-adaptation stage

docs/02 §C adds a next-stage comparison:
- generic EEG → target;
- generic EEG → public auditory → target;
- random same architecture → public auditory → target.

That stage is not part of this contract and is not registered here. The 64 Hz caches cannot serve a 200 Hz CBraMod. The manifest is built for reuse:
- roles, exclusions, families, masks and segment tables are stored in physical seconds as well as in 64 Hz indices;
- keys are defined on stimulus clocks;
- the overlap scan, the clock audit and the cell bindings are rate-independent.

A CBraMod-rate cache builder would reuse these and add only its own resampling and window geometry. The public training steps and data of that comparison should then be paired as docs/02 §C asks.

---

## Appendix A. Provenance of the design counts

The scratch scripts of the first version are read-only and ran under `nice -n 10`, `-I -B`, with < 1 GB RAM. They live in `/tmp/claude-34987/-home-infres-yinwang/e9de8994-9c52-494a-8342-34e8ecdbe1ba/scratchpad/`. Before registration they are copied, with their outputs, into `private/auditory_alignment_v3/aln34/prior33_provenance/`, and their sha256 values are listed in the execution record. The CPU jobs recompute every value that a rule depends on.

- `prior_design/seg_counts.py` (input: the scout's header-level run table, `aln34_sparrk/runtable.json`) produced:
  - the §3.2 role counts;
  - N_SK, the ep-eq size and S0;
  - the participant-balanced audiobook_1 share (0.134; per participant 540–1,730 fit segments, median 1,334).
- `prior_design/filters.py` produced:
  - the `h_aa` designs, the synthetic gain, pulse and private-onset checks;
  - the envelope filter's response and energy;
  - the tick checks to 2·10⁶;
  - the P sha.
- An inline check gave the SparrKULee 1–20 Hz filter figures in §2.1.
- FAU and Federici fold memberships were re-derived from file listings with `data.fau_panel` and `data._folds`, and three cells were checked against ALN3 unit records.
- The FAU/DTU/Federici donor segment numbers in §3.1 are estimates from scout hours; C6 replaces them.
- The scout scripts are under `aln34_sparrk/` and `probe/` in the same scratchpad. The critique's scripts are under `critique/`.
- **This revision** wrote no scratch file. It ran inline `python -I -B -` probes (stdin) under `nice -n 10`, reading JSON and text only:
  - DTU `inventory.json`: 3,520 entries, 2,112 trials. NH 1,056 (352 single-talker on 90 shas; 341 trials on the 79 shas with ≥2 NH listeners; 11 on single-listener shas; two-talker 704 trials, 702 distinct presentations including the masker onset, 2 shared, masker onsets 3.0–5.0 s with 515 distinct values). HI 1,056.
  - FAU `hdf5_dataset_info.txt`: code semantics (D1 condition, D2 attended story, D3 part; 20 trials per subject).
  - Federici `content_groups.json`: 141 items, 90 groups, union-find on max-lag cross-correlation ≥ 0.3, lags not stored.
  - SparrKULee `stimuli/eeg/`: one `<stim>.npz.gz` per stimulus, plus `noise_*` and `t_*` files; and the `dataset_description.json` Notes on the 5 excluded participants.
  - The Slurm partition limits: `DefaultTime=NONE`; MaxTime V100 2 d, A30 4 d, A40 4 d, L40S 1 d, A100 1 d, CPU 4 d.
- The earlier Appendix counted "334 trials" for DTU NH; §3.5 explains the difference.
- Input file hashes at design time (sha256 prefixes; all re-matched by the critique):

| file | sha256 prefix |
|---|---|
| core.py | a3851b4a |
| local_train.py | dee8d0cd |
| registry.py | 2e451e0b |
| run.py | 7c84b692 |
| make_queue.py | 78dea053 |
| ckpt_offload.py | 2850f647 |
| aln3_gpu_pool.sbatch | ee96fa7e |
| watch_anyhost.sh | 0f7d6344 |
| receipt | fb5524f9 |
| plan_ext.jsonl (3,325 lines, at 22:39) | 85b44d8d |

---

## Revision log

Revision of 2026-10-16, about 22:10–22:50 CEST, against `PUBLIC_PRIOR_DESIGN_CRITIQUE.md` (a236fe875424cd0a…). The previous version was f72abfed3f91a17e…. Section numbers below are the new ones: the analysis is new as §5, so code, tests, GPU and risks move to §6–§9, and §10 is new.

| finding | severity | verdict | what changed (where) |
|---|---|---|---|
| F1 per-arm continuation breaks equal updates | HIGH | accepted | Donors are now lockstep group units per (target, objective, seed). All members, including both λ candidates and XM, share every batch and step under one group-synchronous horizon. Rich and CSX groups adopt the core H*. §1 item 5, §2.6, §2.9, §2.10, §4.1, tests 10a–f |
| F2 retained controls missing | MED-HIGH | accepted, for all four targets | XM (a task-state-matched mismatched partner) in every core and panel group, with bridges, target rows and mode-A zero-shot rows. The task-state-matched control coincides with XM for these single-task donors, and the reason is recorded. §2.6, §2.14, §4.1, §5.4 CONTROL |
| F3 rich track absent; `.npz.gz` ban | MED | accepted | A separate non-blocking rich block: spectral structure (PCA-4 of the project's Whisper log-mel, with a SparrKULee-fit basis) and spectral change (flux), independent EEG-side heads, Federici masked. The `.npz.gz` ban is replaced by "gzip + `allow_pickle=False`, never unpickle". §2.15, §6.2 C7, §4.1, tests 12 |
| F4 source-statistics-only variant not registered | MED | accepted | Mode B (FAU noica with target z) and mode C (no target statistics: FAU noica and DTU; Federici partial) registered, limited to cohorts the manifest supports. FAU CI artefact caveat. §2.13, §4.1, §5.4 ACCESS |
| F5 zero-shot pools differ from adapted rows | MED | accepted | Zero-shot views load all participants with `train_p` forced empty; asserts on `train_segs` and es queries; `n_test_candidates` compared by the analysis. §2.13, §5.8, test 9 |
| F6 no frozen analysis; seeds; panel | MED | accepted | New §5 (identities, endpoints, families, statistics, estimand guide) frozen with the record. Seed fields `donor_seed`, `sampler_seed`, `target_seed`, `readout_seeds`. The established `private_transfer` panel (3407, 3413) registered, with the E_LOCAL native reference. The draft's joint − max(…) dropped. §1, §4.1, §4.3, §5 |
| F7 selection by gain, not risk | MED-LOW | accepted | Donor primary: calibrated dev retrieval cross-entropy; target primary: early-stopping risk. Gain-selected checkpoints stored (both stages) and evaluated at the target stage. Selection levels written into records. §2.10, §2.12, §5.4 SELECTION |
| F8 RMS uses target test-stream statistics | LOW-MED | accepted | μ ≡ 0 makes the invariance exact, so a target stream's RMS cannot change any target-side output. RMS listed as declared choice (a). §1, §2.3, test 3c |
| F9 competing-talker donors dropped without rationale | LOW-MED | accepted via the critique's first option | Reason stated (arm comparability on two-talker anchors; single-talker target training). FAU competing-talker anchors registered as the CSX extension. DTU NH two-talker presentations are individually timed (2 of 702 shared), so they add nothing. §2.16, §3.1, §4.1 |
| F10 restricted participants already read; C2 references | LOW-MED | accepted | Their arrays are never opened by any job, audits included; the scout outputs that touched them are not used for any decision. §1, §2.1, §3.2, test 8 |
| F11 C2 depends on an EEG decoder; ±10 s window | LOW | accepted | C2 is declared a clock-validity rule: exclusion only on a consistent nonzero lag in both halves, no shifting, ±40 s search, excluded runs listed. §3.2 |
| F12 60 ep-eq acts as a hard cap | LOW | accepted | 60 ep-eq is a compute limit: a ceiling flag, retained stable states, and a continuation version via `--continuation`. §2.10, §6.4 |
| F13 private path hard-codes 250 Hz and 20 ch | MED-LOW | accepted | `build_target_encoder` always builds the 64 Hz geometry; strict `load_donor`; the generated private path keeps the original `Objective` (asserted). §2.4, §2.12, tests 7d–e |
| F14 key spec contradictory; loss sees only keys | LOW-MED | accepted | Key pinned as (family, presentation, family-clock sample) with bit budgets; target-stage keys packed the same way; rolled-path test. §2.5, tests 4e, 4g |
| F15 pool loop will not pack | MED-LOW | accepted | New 30-s polling loop that skips to lighter rows and re-reads the queue, with no full-pass wait. §6.5, test 15 |
| F16 persistent exit can idle GPUs | MED-LOW | accepted | Blocked rows listed (`.blocked`), never counted as waiting; 20-min idle exit; the keeper submits only for ready rows. §6.5, test 15 |
| F17 inherited time limit; no resubmission | LOW | accepted | No `--time` (the user's rule; partition maxima 1–4 days apply); a CPU keeper job keeps up to 4 workers. §6.5 |
| F18 CPU jobs "runfill, CPU partition" | LOW | accepted | `bc_interim` pattern (CPU partition, normal QOS, no runfill); ≤ 25 normal-QOS jobs. §6.2 |
| F19 probe slot not guaranteed | LOW | accepted | Probe on V100/A30/A40/L40S, with memory checked against the 16-GB budget; drain latency accepted. §7.2, §8 |
| F20 FrozenBridge interface; bridge_cal reuse | LOW | accepted | Full attribute list; the `_ridge` raise and empty-list asserts carry the proof; B_uni_cal τ cross-fitted over the same participant split, and disclosed. §2.11, §2.13 |
| F21 exclusions rest on scratch files | LOW | accepted | Provenance copies with hashes before registration; every exclusion recomputed by C1–C3 under fixed rules. §1, §3.2, Appendix A |
| F22 family clocks undefined outside SparrKULee | LOW | accepted | A per-cohort family-clock table with measured offsets, a duplicate-merge rule and an unknown-clock fallback; tests. §2.5, §3.4, test 4f |
| F23 private input differs from donors | LOW | accepted, both parts | 20 Hz low-pass and per-child z-score at 64 Hz; declared. §2.1, test 2 |
| F24 HC/HC-v pairs in donor keys | LOW | accepted | Partner sampling never pairs HC N with HC-v N; count recorded. §2.5, test 4h |
| F25 CBraMod next stage not mentioned | LOW | accepted | New §10; manifest fields kept in physical time for reuse. The stage itself is not registered here |
| F26 DTU NH counts differ | LOW | accepted | Inventory-level counts re-derived (352 / 341 / 11; 90 / 79 shas). C6 derives and prints the 3-trial exclusion and its reason, because no code reference to `sub-024_run-2` was found. §2.5, §3.5, Appendix A |
| F27 order of live edits | LOW | accepted | Six-step order pinned, including the graceful offload restart. §6.5 |

**Rejected points.** No finding was rejected outright. Two alternatives that the critique offered were not taken, for these reasons:
- **F9, "include competing-talker anchors in the core":** not taken. On those anchors audio_pair and cross_person would supervise different signals (the attended stream versus the whole two-talker scene), which would turn part of the core variant contrast into an attention-task contrast. The data enter as the registered CSX extension instead.
- **F11, "lag consistency only, not r magnitude":** a prominence threshold (z ≥ 5) remains, because a lag cannot be measured without a detectable peak. It only separates measurable from unverifiable runs, unverifiable runs are kept, and no run is excluded for weak tracking. This satisfies the intent of the finding.

**Other changes made while revising.**
- Rows grow from 446 to at most 1,154 (§4.1), and the GPU estimate is revised accordingly (§8).
- The earlier "Questions that need the researcher" item, the restricted participants, is now a note: the host's own metadata settles the exclusion, and nothing waits on it.
- The receipt-correction list adds the DTU counts.
- `queue_v3_prior` counters gain `.blocked`.
- The donor checkpoint names gain a member tag (`<gid>_m<M>_…`), which matches the offload regex.
