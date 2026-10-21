# ALN3.6 R1 — server binding of the package contract

Package `AUDITORY_ALN3_SERVER_PACKAGE_v3_6_20261020` (zip SHA256 `34f1162c…a53d108`, baseline `3da8cf5`), received
2026-10-20 with the instruction "查看并完成这个包里的内容，你自己来判断优先级，可以调整". This note records how the
contract is bound to the server code and every choice the package leaves to the server. All comparisons are labelled
`prospective_protocol_after_2026_10_20_result_informed_design`. Code: `auditory_alignment_v3/aln36/`.

## Panel A — FAU whole-group sources (`fau_group.py`, `train_true_nll.py`)

- **Sources.** For held-out group g ∈ {CI, HA, TH}: every FAU identity with group ≠ g (TH dev people are sources unless
  g = TH). Gradients use their role=fit, kind=ss segments; checkpoint selection their role=es, kind=ss segments.
  Source counts: leave-CI 57, leave-HA 52, leave-TH 53 (no TH dev). Targets: the formal panel of g (CI 24, HA 29, TH 14).
  All three groups heard the same eight single-talker stimuli, so source-fit audio content is identical across groups
  (asserted).
- **Unique fits.** 2 tools × 3 groups × 2 content folds = 12 per seed; the 5 original person folds of g are evaluation
  slices of the same source (60 cells). The training signature holds seed, tool recipe, group, content fold, source
  IDs, fit/ES row hashes, scaler hash, initialisation, target coordinate, checkpoint rule and source-code hashes.
- **Input scaling.** The stageB `eeg_1_20_ica` signal is loaded without the per-person z-score of
  `auditory_alignment.data._stdz` (process-local identity patch). One channel mean/SD is computed over every sample of the
  source role=fit segments and frozen for source ES, target support and target query. Offline 1–20 Hz filtering and ICA
  are inherited and disclosed. Channel order is identical across all 81 files and equal to the CBraMod channel contract.
- **Recipes (unchanged from the direct parents).** Local L1 `local_aligned1000`: 200 epochs, AdamW lr 1e-3, weight
  decay 1e-4, cosine schedule (parents `ALN3X_84b5c4fd866b3b7a`, `ALN3X_f296f7a7e2f2176c`). CBpre: generic CBraMod
  `pretrained_weights.pth` (SHA256 `0792cb80…7178`), `full_onestep_v1`, 100 epochs, backbone 3e-4, head 1e-3, LLRD 1
  (parents `ALN3X_124a413438c432c7`, `ALN3X_fa1f6f11e410c0b3`). No project donor and no FAU-finetuned weights.
- **Checkpoint rule (replaces the es_loss − mismatch gain).** Candidates: the initial state plus every registered
  validation point (local every 5th epoch and the last; CB every epoch). Risk = native retrieval NLL (bits/query) of all
  source-ES segments against the frozen, deduplicated source-ES audio pool; native score = mean over 16 fixed grid
  anchors of u·v (the evaluator's NCE score). The temperature is fitted per candidate on a frozen source-fit calibration
  set: 600 source-fit segments drawn with `default_rng(seed+36006)` against all source-fit audio. ES never sets the
  temperature. Ties keep the earlier state. The inherited gain, CS diagnostics and an ES-profiled NLL are recorded as
  diagnostics only.

## Panel B — public readout (`public_features.py`, `public_readout.py`)

- **Banks.** 52 frozen banks: the 12 new sources plus the 40 seed-3401 pooled parents already used by content_time_v1
  (DTU and FAU × local and CBpre × 5 person folds × 2 content folds). Each bank has rows for every source person's
  fit+ES segment and every target person's fit and test segment, at 8 anchors (0.8:0.4:3.6 s) × 5 centres (−200…600 ms),
  window [c−400, c+600) ms. Pooled parents keep their inherited per-person z-score; this is disclosed, not relabelled.
- **Coordinate.** Current envelope (Local row 5). Mean/SD over the unique audio positions of the source people's
  role=fit content; the four past-envelope lags (20/100/200/500 ms) use the same scale.
- **H0.** OLS of y on [1, four lags] (EEG-free).
- **Window probes.** Ridge from the 32-d representation to the history residual y − H0. The alpha is taken from the 8
  content_time points by MSE on source ES rows after fitting on source fit rows, then refitted on fit+ES. Each window
  score is therefore EEG evidence beyond history, in the common audio unit.
- **Cross-fit.** 3 source-person folds (sha256 of seed|person). H0 and the probes are fitted on two folds; OOF
  offset/scores come from the held-out fold's role=es rows. The OOF score mean/SD is frozen. a0 is the least-squares
  fit of (y − OOF offset) on the scaled OOF scores, with no intercept. `TemporalBasis` is built on the OOF rows with
  history design [1, 4 scaled lags]. The final H0 and probes are refitted on all source people and applied with the frozen
  OOF scaler, a0 and basis.
- **Support/query.** Support is the first ceil(0.3 n) of the target person's role=fit segments in recording order
  (trial_NN, then segment start), all 8 anchors. Query is every role=test segment. EEG access intervals of support
  and query, covering the joint [−600, 1200) ms window, are asserted disjoint, and so is their sound content. λ = 1 for
  history, scale and time. `nested.py` is byte-identical to the package reference.
- **M0.** Query segments are taken in recording order, and the whole 8-anchor × 5-window score block is rolled by one
  segment. E0 parameters stay fixed and history/targets stay in place. At least 2 query segments are required.

## Panel C — private (`private_features.py`, `private_readout.py`)

- **Bundles.** The 10 ALN3.5 matched AP/APwrong target units (seed 3401, NCE, 5 outer folds). Each loads its recorded
  selected checkpoint (min source-ES loss, hash-checked) strictly. The rebuilt 64 Hz view must reproduce the training
  pool hash, and the view hash under the frozen manifest filter bytes (the ap_wrong_queries precedent). Whether this
  host's redesigned filter coefficients are byte-identical is recorded. Masks act on the encoder input (64 Hz samples
  0–12, 13–25, 26–37 after onset). Optional S reuses the existing prior_science_v1 caches; no new training.
- **H0.** logit q0[6-bin since-last-deviant] from the source children's trials, plus one source-ES intercept.
- **Window probes.** `history_interface.fit_offset` on the standardised features of source-ES rows with the H0 offset
  (sum NLL + 0.5‖slopes‖², the established C = 1). The score is the source-logit evidence beyond H0.
- **Cross-fit.** As for the public readout, over source children. a0 is the unpenalised logistic MLE of y on the scaled
  OOF scores with the OOF offset. The history design is [1, 5 standardised bin dummies].
- **Support/query.** `support_contract.private_split` (first ceil(0.3 blocks) physical blocks, boundary removal,
  full-epoch guard), applied to all trials of the outer child.
- **Strict twin.** Same child, same bin, other block, not the trial itself. Support partners come only from support and
  query partners only from query, using `history_interface.strict_twin_map` with seed 361819 + sha256(salt|child).
  Real and twin controls are fitted on the same twin-eligible support rows and evaluated on the same query
  intersection. The full natural analysis is kept separate.

## Statistics (`analysis.py`)

People are the unit. Content folds are averaged within person. The families follow the package's `plans/round1.json`.
Intervals use the validated `sci_r1.stats` identity bootstrap-t (B = 4000), with a family max-|T*| simultaneous 95%
interval. Within a family the members of one group share replicate indices, and groups are resampled independently. The
package's fixed-SE max-|z*| reference is reported as a secondary column. A family is marked incomplete, with no
simultaneous interval, if any expected person is missing for any member.

## Scheduling

The lanes are registered through `auditory_alignment_v3/aln35/aln36_fleet.py` (byte-checked providers) in the existing
fleet coordinator (researcher-approved 2026-10-21). They take released runfill slots ahead of the four registered
tails, within the aggregate 10-GPU cap, without cancelling running jobs. Each lane runs one engineering smoke check
before its production units.
