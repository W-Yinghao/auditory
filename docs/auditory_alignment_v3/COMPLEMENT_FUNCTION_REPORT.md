# Complement function report — R34_FUSION_FUNCTION (exploratory re-evaluation, ALN3.4) — v2.1 report-status correction

> Execution update, 2026-10-17: all234 listed nonzero-epoch units now have full comparable v2 outputs; 10 pre-existing CPU outputs were reused and224 were evaluated by GPU workers1043886/1043887. The16 epoch-zero units retain their exact-zero checkpoint evidence. Final CPU job1044112 verified coverage and reran the unchanged v2 analysis. Historical plan/estimate statements below describe the pre-launch snapshot, not missing work. The execution receipt is private/auditory_alignment_v3/aln34/complement_final_20261017/receipt.json.


Generated 2026-10-17 15:06 CEST (job 1044112) by `/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m auditory_alignment_v3.aln34.complement_function --aggregate` (PYTHONPATH = repo root). Version v2; it supersedes v1 (generated 2026-10-16 20:37), whose report, JSON, code, test and unit list are kept byte-identical in `private/auditory_alignment_v3/aln34/complement_function_v1_20261016T2037/`. Analysis note (written before the v1 values were computed; its section 'Correction 1 (2026-10-16 21:34 CEST)' was written before any v2 value): `private/auditory_alignment_v3/aln34/COMPLEMENT_FUNCTION_NOTE.md`. Seed 3401; identity-level paired differences; bootstrap-t B = 4000; simultaneous 95% intervals by max-t within each family. Positive = candidate better (lower risk R in bits, lower rank_pct, higher top-1). No p-values; no test-based selection; nothing here was retrained.

Code sha256: `complement_function.py` d98dce999c4b, `complement_function_eval.py` be2107d36af9, `sci_r1/stats.py` 8bb141cf6070, `bc_interim.py` 2840df81b608, `reference residuals.py` 022d29ef51cb. Loaded sources of the two lane modules: `results/auditory_alignment_v3/aln34/complement_function/code_snapshots/complement_function_eval.be2107d36af9.py`, `results/auditory_alignment_v3/aln34/complement_function/code_snapshots/complement_function.d98dce999c4b.py`.

**Reading rules.**
- SC `local_only` is the base passed through a supervised ridge to the raw target and the fixed audio head: a ridge-remapped base, not the base.
- Every SC variant is a supervised closed-form fit on frozen encoders; only the encoders are frozen.
- RS at epoch 0 equals base L0 exactly (zero-initialised last layer).
- Access (§3): base L0 reads [0, post). L1, the SC context features (aligned_pretrained, aligned_random, small_context, concat) and every RS context branch read the query-aligned window [-0.4 s, post). SC `local_only` and `local_refit_capacity` read only the base's own input. So against L0 the SC context variants and RS are context-assisted, while `local_only` / `local_refit_capacity` are access-matched; against L1 every SC variant is access-matched.
- Seeds and folds never add n; rows are identities (Federici: 86 human identities from 86 records, {'CI': 33, 'HC': 37, 'HC-v': 16}; each HC-v record has its own subject_uid; the 9 phantom sessions are excluded).

## 0. Version history and corrections

v2 corrects v1 as follows (details and the honest record of what was seen: analysis note, Correction 1):
- access labels: `local_refit_capacity` under L0 was labelled context-assisted (12 family rows in v1); it reads only L0's own tokens and is access-matched. The same label sits in the frozen `COMPLEMENT_REVISED_RESULTS.md` (SC-VALUE `local_refit_capacity` under L0, tag "vs local_only (context-assisted)"); that document is not edited, this line is its correction pointer. RS members now carry their access label (context-assisted vs L0);
- the SC calibration caveat names the unified bridge as well as the temperature (§2);
- the held-out development level actually achieved is stated (§1) and the fit budgets are tabulated (§3);
- the epoch-0 statement is computed, with where the record field was measured (§2);
- the asset audit searches by experiment id, inventories every checkpoint file and hashes the FM weights against the fetch receipt (§10);
- the GPU plan uses the project interpreter and offline flags, has a claim-based worker and an sbatch template, counts pending units only, and states GPU memory from the records as training + evaluation peaks (§11);
- bookkeeping: coverage of all 30 RS configurations (§9), record counts (§12.5), duplicated `local_only` members in the SC tallies (§5, §12.1);
- provenance: the evaluator moved to `complement_function_eval.py`; every per-unit output records the evaluator hash and its loaded source is snapshotted; the v1 per-unit outputs (recorded hashes of intermediate, unkept file versions) are kept in `results/auditory_alignment_v3/aln34/complement_function/units/` and not merged; they were re-run with the v2 evaluator (§9).

Value check against v1: 204 family members, max |Δ| over estimates and both intervals 0.0e+00, class changes 0; level estimates max |Δ| 0.0e+00. Every member label was reworded (204 members); access-class changes: {'context-assisted -> access-matched': 12, 'no access label -> context-assisted': 60}. So in §4–§6 only the access labels changed; every value is identical to v1.

## 1. Level of held-out development actually achieved (AGENTS ALN3.4 item 8; docs/03 §1)

- **SC**: ridge-only out-of-fold. Residual ridges are fitted on out-of-fold base predictions over 5 groups of the outer-fold training participants, and every alpha is chosen by grouped cross-validation over those groups. The base encoder itself was trained on all of them (record field `base_trained_on_all_groups`: true in all 100 SC records). The PCA bases and the final ridges are fitted on all training rows. So the old SC OOF values hold for the ridge step only, not for the whole pipeline.
- **RS**: residual-only cross-person selection. The residual and its context branch are trained on groups other than 0; the epoch (0..30, epoch 0 = the base) is selected on group 0 development segments. Group 0 participants were training participants of the frozen base L0, so only the residual is held out from the development identities.
- **This re-evaluation**: no selection and no new fit, except the evaluator's training-side readouts (unified bridge, CS_SINGLE native ridge, temperatures), refitted exactly as in the original records. Test participants enter no fit.
- Neither SC nor RS is whole-pipeline held-out-person development (docs/03 §4 describes that as a new execution).

## 2. Same-contract checks

- Pairing (folds, participants, candidate and query counts, both readouts): {'matched': 102}; excluded pairs: 0.
- RS units that selected epoch 0: 16. Their selected checkpoints have a zero last layer (16 / 16; §8), so r = 0 exactly and u = normalise(u_base) on every test anchor. Their outer-test records against the base L0 records (scored in separate GPU runs): max |Δ| on log-loss and rank_pct = 2.7e-04 (within the 1e-3 reproduction rule); over all metrics incl. top-1 / top-5 / MRR = 0.028, i.e. single near-tie flips (1/n_queries).
- The record field `epoch0_max_abs_diff_vs_base` is 6.0e-08 in these units (3.0e-08–1.2e-07 over all 250 units). Where it was measured: residual32.fit_residual at epoch 0: one training-side batch (N_SEG segments of training-fit participants x Q anchors), max |normalise(u_base + r) - u_base| with the zero-initialised last layer; not measured on the outer test.
- **SC in-sample caveat** (disclosed, not corrected). The SC ridges were fitted on fit **and** es rows of the training participants. The evaluator selects the unified bridge's alpha on es rows and refits it on fit + es rows, and calibrates both temperatures on es queries. So SC's unified R, rank_pct and top-1 all carry the in-sample es effect; SC's native ranks (NCE: fixed dot product, no fitted readout) do not; SC's native R carries it through the temperature. Base and RS used es rows for early stopping, selection or calibration only. The direction of the effect is not determined here.
- The native NCE score has no fitted parameter; only CS_SINGLE fits a native ridge (U → V).
- Regression: RS-VALUE families (30 members) vs the frozen `results/auditory_alignment_v3/aln32_residual/aln32_residual.json`: max |Δ| 0.0e+00, class mismatches 0.
- Regression: SC level estimates (144 values, both readouts) vs the frozen `results/auditory_alignment_v3/aln32_complement/aln32_simple_complement.json`: max |Δ| 0.0e+00.
- Checkpoints: epoch-0 selection ⇔ zero residual last layer, mismatches: none.

## 3. Input access and fit budgets (docs/03 §1)

| configuration | EEG read |
|---|---|
| L0 | EEG [0, post): the lag_local_tokens full window (post-only) |
| L1 | EEG [-pre, post): the same encoder recipe on the query-aligned window |
| SC local_only | the base's input only (ridge on the base output u) |
| SC local_refit_capacity | the base's input only (ridge on u + the base encoder's own tokens) |
| SC aligned_pretrained / aligned_random | the base's input + frozen FM tokens of [-pre, post) |
| SC small_context | the base's input + the raw window [-pre, post) |
| SC concat | the base's input + pretrained FM tokens of [-pre, post) (joint ridge) |
| RS (every variant) | L0's input + a context branch on [-pre, post) (FM tokens or a small conv) |
| FM / TF context rows | the query-aligned window [-0.4 s, +0.6 s) |

Windows recorded per family and dataset (half-open, samples): FM|dtu: [-0.4, 0.6] s (128 samples); FM|fau: [-0.4, 0.6] s (128 samples); FM|federici: [-0.4, 0.6] s (100 samples); L0|dtu: [[0, 77]]; L0|fau: [[0, 77]]; L0|federici: [[0, 60]]; L1|dtu: [[-51, 77]]; L1|fau: [[-51, 77]]; L1|federici: [[-40, 60]]; RS|dtu: [-51, 77]; RS|fau: [-51, 77]; RS|federici: [-40, 60]; SC|dtu: [-51, 77]; SC|fau: [-51, 77]; SC|federici: [-40, 60]; TF|dtu: [-0.4, 0.6] s (128 samples); TF|fau: [-0.4, 0.6] s (128 samples); TF|federici: [-0.4, 0.6] s (100 samples); sampling rates {'fau': 128, 'dtu': 128, 'federici': 100}. Source: complement32.Featurizer (u, tok on bt.patches; raw / FM on masked_windows(E, e, -pre, post)); residual32.Rows; record fields.

| fitted part | identities | content / rows | budget |
|---|---|---|---|
| SC ridges + PCA, dtu|L0 (20 records) | 34–36 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 19,464–21,864; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| SC ridges + PCA, dtu|L1 (20 records) | 34–36 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 19,464–21,864; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| SC ridges + PCA, fau|L0 (20 records) | 67–70 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 49,312–64,960; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| SC ridges + PCA, fau|L1 (20 records) | 67–70 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 49,312–64,960; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| SC ridges + PCA, federici|L0 (10 records) | 67–72 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 40,824–44,784; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| SC ridges + PCA, federici|L1 (10 records) | 67–72 outer-fold training participants, 5 groups | fit + es segments of the outer-fold training participants (complement32.run: units = fit + es); 8 grid anchors per segment | ridge rows 40,824–44,784; PCA K = 64 per block on 8,000 rows (torch.pca_lowrank (randomised, niter = 4) per block tok / raw / fm_pretrained / fm_random; subsample rng GROUP_SEED + 2); alpha grid 9 values 1e-05–1000 (grouped CV over the 5 participant groups (correlation), residual ridges on out-of-fold base predictions) |
| RS residual + context, dtu|residual_aligned_pretrained (40 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 1,375–1,639; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 877,104 / 2,155,680 (one value per backbone) |
| RS residual + context, dtu|residual_aligned_random (40 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 1,375–1,639; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 877,104 / 2,155,680 (one value per backbone) |
| RS residual + context, dtu|residual_small_capacity (20 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 1,375–1,639; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 74,976 |
| RS residual + context, fau|residual_aligned_pretrained (40 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 2,597–3,864; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 454,704 / 1,074,336 (one value per backbone) |
| RS residual + context, fau|residual_aligned_random (40 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 2,597–3,864; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 454,704 / 1,074,336 (one value per backbone) |
| RS residual + context, fau|residual_small_capacity (20 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 2,597–3,864; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 69,696 |
| RS residual + context, federici|residual_aligned_pretrained (20 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 3,015–3,384; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 475,696 / 1,115,296 (one value per backbone) |
| RS residual + context, federici|residual_aligned_random (20 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 3,015–3,384; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 475,696 / 1,115,296 (one value per backbone) |
| RS residual + context, federici|residual_small_capacity (10 records) | training participants; development group 0 | fit segments of training participants outside group 0; 8 anchors per segment | training segments 3,015–3,384; development 300 segments; temperature 300 segments; epochs 30; trainable parameters 78,048 |
| evaluator readouts (every row of §4) | outer-fold training participants | all grid anchors of fit + es segments of the outer-fold training participants | 400 segments (seed + 1000 (auditory_alignment_v2.evaluate.evaluate_continuous)); unified alpha grid np.logspace(-4, 8, 13) (fit rows -> es rows, mean per-dimension correlation; refit on fit + es rows); CS_SINGLE native alpha grid np.logspace(-3, 3, 7); NCE native: fixed dot product u . v (no fitted parameter) |
| evaluator temperatures | outer-fold training participants | one temperature per readout on training es queries against the es candidate pool | ≤ 300 queries |
| outer test | the fold's test participants | all single-speaker test segments of the fold's test participants on the dense grid; candidates = unique test stimuli | all |

## 4. Levels on the same identities (seed 3401)

Targets and units: dtu target local (contract dense20ms_v1; seeds 3401); fau target local (contract dense20ms_v1; seeds 3401); federici target envelope (contract dense20ms_v1; seeds 3401). R = candidate cross-entropy of the true test stimulus in bits; rank_pct = rank of the true candidate / (candidates − 1); n = identities.

| configuration | n | R unified [95% CI] | R native [95% CI] | rank_pct u / n | top1 u / n |
|---|---|---|---|---|---|
| L0|dtu|CS_SINGLE  (= RS at epoch 0) | 44 | 7.108 [+6.987, +7.228] | 7.205 [+7.093, +7.317] | 0.255 / 0.275 | 0.047 / 0.044 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 44 | 7.129 [+7.009, +7.249] | 7.227 [+7.118, +7.337] | 0.259 / 0.280 | 0.047 / 0.042 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 44 | 7.124 [+7.005, +7.242] | 7.214 [+7.101, +7.327] | 0.258 / 0.277 | 0.046 / 0.043 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 44 | 7.110 [+6.989, +7.231] | 7.205 [+7.089, +7.320] | 0.255 / 0.275 | 0.047 / 0.045 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 44 | 7.106 [+6.986, +7.226] | 7.204 [+7.090, +7.318] | 0.255 / 0.275 | 0.048 / 0.045 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 44 | 7.194 [+7.075, +7.313] | 7.260 [+7.148, +7.371] | 0.267 / 0.285 | 0.043 / 0.041 |
| L0|dtu|NCE  (= RS at epoch 0) | 44 | 6.869 [+6.708, +7.031] | 6.214 [+5.960, +6.468] | 0.224 / 0.159 | 0.066 / 0.136 |
| L1|dtu|NCE | 44 | 6.905 [+6.752, +7.059] | 6.365 [+6.139, +6.591] | 0.228 / 0.168 | 0.064 / 0.118 |
| SC|dtu|NCE|cbramod|L0|aligned_pretrained | 44 | 6.927 [+6.774, +7.080] | 6.799 [+6.621, +6.977] | 0.230 / 0.217 | 0.064 / 0.078 |
| SC|dtu|NCE|cbramod|L0|aligned_random | 44 | 6.934 [+6.782, +7.087] | 6.817 [+6.640, +6.994] | 0.231 / 0.219 | 0.061 / 0.078 |
| SC|dtu|NCE|cbramod|L0|concat | 44 | 6.924 [+6.771, +7.078] | 6.801 [+6.620, +6.982] | 0.229 / 0.217 | 0.063 / 0.078 |
| SC|dtu|NCE|cbramod|L0|local_only | 44 | 6.975 [+6.816, +7.135] | 6.793 [+6.614, +6.973] | 0.235 / 0.216 | 0.062 / 0.076 |
| SC|dtu|NCE|cbramod|L0|local_refit_capacity | 44 | 6.972 [+6.820, +7.124] | 6.803 [+6.621, +6.985] | 0.235 / 0.217 | 0.063 / 0.075 |
| SC|dtu|NCE|cbramod|L0|small_context | 44 | 6.930 [+6.779, +7.081] | 6.794 [+6.615, +6.973] | 0.229 / 0.216 | 0.062 / 0.079 |
| SC|dtu|NCE|cbramod|L1|aligned_pretrained | 44 | 6.986 [+6.853, +7.120] | 6.851 [+6.692, +7.010] | 0.236 / 0.222 | 0.062 / 0.074 |
| SC|dtu|NCE|cbramod|L1|aligned_random | 44 | 6.992 [+6.853, +7.131] | 6.870 [+6.713, +7.026] | 0.237 / 0.224 | 0.061 / 0.074 |
| SC|dtu|NCE|cbramod|L1|concat | 44 | 6.999 [+6.863, +7.135] | 6.862 [+6.706, +7.018] | 0.238 / 0.223 | 0.062 / 0.071 |
| SC|dtu|NCE|cbramod|L1|local_only | 44 | 7.035 [+6.899, +7.172] | 6.853 [+6.692, +7.013] | 0.242 / 0.221 | 0.054 / 0.073 |
| SC|dtu|NCE|cbramod|L1|local_refit_capacity | 44 | 6.995 [+6.861, +7.128] | 6.872 [+6.714, +7.030] | 0.236 / 0.220 | 0.057 / 0.071 |
| SC|dtu|NCE|cbramod|L1|small_context | 44 | 6.975 [+6.839, +7.110] | 6.843 [+6.686, +7.000] | 0.234 / 0.220 | 0.063 / 0.071 |
| SC|dtu|NCE|reve|L0|aligned_pretrained | 44 | 6.932 [+6.774, +7.089] | 6.808 [+6.627, +6.989] | 0.229 / 0.218 | 0.067 / 0.081 |
| SC|dtu|NCE|reve|L0|aligned_random | 44 | 6.924 [+6.776, +7.071] | 6.795 [+6.619, +6.970] | 0.229 / 0.216 | 0.067 / 0.079 |
| SC|dtu|NCE|reve|L0|concat | 44 | 6.942 [+6.787, +7.098] | 6.822 [+6.644, +7.000] | 0.231 / 0.219 | 0.065 / 0.079 |
| SC|dtu|NCE|reve|L0|local_only | 44 | 6.975 [+6.819, +7.132] | 6.793 [+6.617, +6.970] | 0.235 / 0.216 | 0.062 / 0.076 |
| SC|dtu|NCE|reve|L0|local_refit_capacity | 44 | 6.972 [+6.813, +7.131] | 6.803 [+6.631, +6.975] | 0.235 / 0.217 | 0.063 / 0.075 |
| SC|dtu|NCE|reve|L0|small_context | 44 | 6.928 [+6.775, +7.081] | 6.792 [+6.615, +6.970] | 0.228 / 0.215 | 0.062 / 0.079 |
| SC|dtu|NCE|reve|L1|aligned_pretrained | 44 | 6.986 [+6.843, +7.130] | 6.861 [+6.703, +7.019] | 0.236 / 0.223 | 0.062 / 0.071 |
| SC|dtu|NCE|reve|L1|aligned_random | 44 | 6.973 [+6.840, +7.107] | 6.843 [+6.682, +7.003] | 0.234 / 0.220 | 0.061 / 0.071 |
| SC|dtu|NCE|reve|L1|concat | 44 | 7.020 [+6.878, +7.163] | 6.875 [+6.715, +7.035] | 0.240 / 0.225 | 0.060 / 0.070 |
| SC|dtu|NCE|reve|L1|local_only | 44 | 7.035 [+6.899, +7.171] | 6.853 [+6.689, +7.017] | 0.242 / 0.221 | 0.054 / 0.073 |
| SC|dtu|NCE|reve|L1|local_refit_capacity | 44 | 6.995 [+6.862, +7.127] | 6.872 [+6.707, +7.037] | 0.236 / 0.220 | 0.057 / 0.071 |
| SC|dtu|NCE|reve|L1|small_context | 44 | 6.975 [+6.844, +7.106] | 6.842 [+6.677, +7.007] | 0.234 / 0.220 | 0.063 / 0.070 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 44 | 6.869 [+6.707, +7.031] | 6.212 [+5.951, +6.472] | 0.224 / 0.159 | 0.066 / 0.137 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 44 | 6.869 [+6.710, +7.028] | 6.212 [+5.951, +6.473] | 0.224 / 0.159 | 0.066 / 0.138 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 44 | 6.869 [+6.712, +7.027] | 6.211 [+5.951, +6.471] | 0.224 / 0.159 | 0.066 / 0.138 |
| RS|dtu|NCE|reve|residual_aligned_random | 44 | 6.869 [+6.704, +7.035] | 6.212 [+5.940, +6.483] | 0.224 / 0.159 | 0.066 / 0.138 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 44 | 6.854 [+6.692, +7.016] | 6.202 [+5.943, +6.461] | 0.222 / 0.158 | 0.068 / 0.138 |
| FM|dtu|NCE|cbramod|pretrained_frozen  (context, reported before) | 44 | 7.245 [+7.149, +7.341] | 7.080 [+6.951, +7.209] | 0.281 / 0.248 | 0.037 / 0.048 |
| FM|dtu|NCE|reve|pretrained_frozen  (context, reported before) | 44 | 7.145 [+7.021, +7.269] | 6.816 [+6.660, +6.971] | 0.257 / 0.212 | 0.043 / 0.065 |
| TF|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 44 | 6.692 [+6.527, +6.857] | 5.988 [+5.747, +6.229] | 0.197 / 0.141 | 0.076 / 0.144 |
| TF|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 44 | 6.743 [+6.590, +6.897] | 6.234 [+6.016, +6.452] | 0.204 / 0.155 | 0.072 / 0.122 |
| TF|dtu|NCE|reve|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 44 | 6.902 [+6.757, +7.048] | 6.303 [+6.088, +6.518] | 0.225 / 0.165 | 0.065 / 0.122 |
| TF|dtu|NCE|reve|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 44 | 6.911 [+6.753, +7.070] | 6.298 [+6.083, +6.513] | 0.218 / 0.164 | 0.067 / 0.118 |
| L0|fau|CS_SINGLE  (= RS at epoch 0) | 67 | 6.358 [+6.277, +6.439] | 6.340 [+6.259, +6.421] | 0.317 / 0.314 | 0.054 / 0.053 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 67 | 6.360 [+6.278, +6.441] | 6.342 [+6.263, +6.420] | 0.317 / 0.314 | 0.054 / 0.053 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 67 | 6.358 [+6.277, +6.440] | 6.341 [+6.263, +6.420] | 0.317 / 0.314 | 0.054 / 0.054 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 67 | 6.358 [+6.278, +6.438] | 6.340 [+6.262, +6.418] | 0.317 / 0.314 | 0.054 / 0.054 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 67 | 6.358 [+6.279, +6.438] | 6.341 [+6.263, +6.418] | 0.317 / 0.314 | 0.054 / 0.053 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 67 | 6.376 [+6.305, +6.448] | 6.361 [+6.285, +6.438] | 0.323 / 0.320 | 0.051 / 0.049 |
| L0|fau|NCE  (= RS at epoch 0) | 67 | 6.309 [+6.188, +6.429] | 6.004 [+5.843, +6.165] | 0.302 / 0.250 | 0.066 / 0.101 |
| L1|fau|NCE | 67 | 6.344 [+6.250, +6.438] | 6.087 [+5.955, +6.219] | 0.311 / 0.266 | 0.057 / 0.083 |
| SC|fau|NCE|cbramod|L0|aligned_pretrained | 67 | 6.337 [+6.226, +6.449] | 6.224 [+6.097, +6.351] | 0.307 / 0.290 | 0.064 / 0.075 |
| SC|fau|NCE|cbramod|L0|aligned_random | 67 | 6.326 [+6.220, +6.433] | 6.235 [+6.107, +6.363] | 0.306 / 0.291 | 0.061 / 0.072 |
| SC|fau|NCE|cbramod|L0|concat | 67 | 6.332 [+6.216, +6.448] | 6.227 [+6.103, +6.351] | 0.306 / 0.290 | 0.063 / 0.074 |
| SC|fau|NCE|cbramod|L0|local_only | 67 | 6.344 [+6.241, +6.448] | 6.226 [+6.101, +6.352] | 0.310 / 0.289 | 0.059 / 0.070 |
| SC|fau|NCE|cbramod|L0|local_refit_capacity | 67 | 6.344 [+6.244, +6.445] | 6.226 [+6.101, +6.351] | 0.310 / 0.289 | 0.059 / 0.070 |
| SC|fau|NCE|cbramod|L0|small_context | 67 | 6.345 [+6.235, +6.455] | 6.241 [+6.116, +6.366] | 0.309 / 0.292 | 0.064 / 0.072 |
| SC|fau|NCE|cbramod|L1|aligned_pretrained | 67 | 6.350 [+6.262, +6.438] | 6.275 [+6.153, +6.396] | 0.315 / 0.298 | 0.057 / 0.065 |
| SC|fau|NCE|cbramod|L1|aligned_random | 67 | 6.355 [+6.264, +6.446] | 6.277 [+6.156, +6.399] | 0.317 / 0.298 | 0.055 / 0.065 |
| SC|fau|NCE|cbramod|L1|concat | 67 | 6.354 [+6.266, +6.442] | 6.279 [+6.156, +6.402] | 0.316 / 0.299 | 0.056 / 0.065 |
| SC|fau|NCE|cbramod|L1|local_only | 67 | 6.358 [+6.272, +6.443] | 6.280 [+6.157, +6.402] | 0.319 / 0.298 | 0.054 / 0.065 |
| SC|fau|NCE|cbramod|L1|local_refit_capacity | 67 | 6.368 [+6.278, +6.457] | 6.282 [+6.160, +6.404] | 0.319 / 0.299 | 0.054 / 0.065 |
| SC|fau|NCE|cbramod|L1|small_context | 67 | 6.354 [+6.262, +6.447] | 6.275 [+6.155, +6.394] | 0.316 / 0.298 | 0.058 / 0.067 |
| SC|fau|NCE|reve|L0|aligned_pretrained | 67 | 6.339 [+6.236, +6.443] | 6.238 [+6.113, +6.362] | 0.309 / 0.292 | 0.060 / 0.071 |
| SC|fau|NCE|reve|L0|aligned_random | 67 | 6.340 [+6.229, +6.452] | 6.242 [+6.115, +6.368] | 0.310 / 0.292 | 0.063 / 0.071 |
| SC|fau|NCE|reve|L0|concat | 67 | 6.339 [+6.234, +6.443] | 6.238 [+6.110, +6.365] | 0.309 / 0.292 | 0.060 / 0.071 |
| SC|fau|NCE|reve|L0|local_only | 67 | 6.344 [+6.240, +6.449] | 6.226 [+6.101, +6.352] | 0.310 / 0.289 | 0.059 / 0.070 |
| SC|fau|NCE|reve|L0|local_refit_capacity | 67 | 6.344 [+6.239, +6.450] | 6.226 [+6.100, +6.353] | 0.310 / 0.289 | 0.059 / 0.070 |
| SC|fau|NCE|reve|L0|small_context | 67 | 6.355 [+6.247, +6.463] | 6.242 [+6.114, +6.369] | 0.311 / 0.292 | 0.063 / 0.071 |
| SC|fau|NCE|reve|L1|aligned_pretrained | 67 | 6.356 [+6.268, +6.445] | 6.282 [+6.156, +6.408] | 0.316 / 0.299 | 0.054 / 0.065 |
| SC|fau|NCE|reve|L1|aligned_random | 67 | 6.358 [+6.264, +6.452] | 6.276 [+6.155, +6.398] | 0.317 / 0.298 | 0.058 / 0.066 |
| SC|fau|NCE|reve|L1|concat | 67 | 6.359 [+6.270, +6.448] | 6.285 [+6.165, +6.405] | 0.317 / 0.300 | 0.054 / 0.064 |
| SC|fau|NCE|reve|L1|local_only | 67 | 6.358 [+6.273, +6.442] | 6.280 [+6.160, +6.399] | 0.319 / 0.298 | 0.054 / 0.065 |
| SC|fau|NCE|reve|L1|local_refit_capacity | 67 | 6.368 [+6.279, +6.457] | 6.282 [+6.158, +6.406] | 0.319 / 0.299 | 0.054 / 0.065 |
| SC|fau|NCE|reve|L1|small_context | 67 | 6.354 [+6.261, +6.447] | 6.275 [+6.154, +6.395] | 0.316 / 0.298 | 0.059 / 0.066 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 67 | 6.309 [+6.189, +6.429] | 6.009 [+5.848, +6.169] | 0.302 / 0.250 | 0.065 / 0.101 |
| RS|fau|NCE|cbramod|residual_aligned_random | 67 | 6.309 [+6.186, +6.431] | 6.008 [+5.846, +6.169] | 0.302 / 0.250 | 0.066 / 0.101 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 67 | 6.308 [+6.188, +6.429] | 6.007 [+5.840, +6.174] | 0.302 / 0.250 | 0.066 / 0.101 |
| RS|fau|NCE|reve|residual_aligned_random | 67 | 6.309 [+6.187, +6.431] | 6.009 [+5.848, +6.169] | 0.302 / 0.250 | 0.066 / 0.101 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 67 | 6.302 [+6.179, +6.425] | 6.000 [+5.836, +6.164] | 0.300 / 0.250 | 0.067 / 0.101 |
| FM|fau|NCE|cbramod|pretrained_frozen  (context, reported before) | 67 | 6.462 [+6.404, +6.521] | 6.418 [+6.363, +6.473] | 0.344 / 0.329 | 0.042 / 0.045 |
| FM|fau|NCE|reve|pretrained_frozen  (context, reported before) | 67 | 6.315 [+6.229, +6.401] | 6.135 [+6.014, +6.257] | 0.307 / 0.271 | 0.057 / 0.073 |
| TF|fau|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 67 | 6.200 [+6.075, +6.324] | 5.917 [+5.750, +6.084] | 0.282 / 0.236 | 0.074 / 0.102 |
| TF|fau|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 67 | 6.217 [+6.090, +6.343] | 5.980 [+5.842, +6.118] | 0.285 / 0.245 | 0.072 / 0.091 |
| TF|fau|NCE|reve|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 67 | 6.286 [+6.170, +6.402] | 5.965 [+5.810, +6.120] | 0.297 / 0.246 | 0.068 / 0.101 |
| TF|fau|NCE|reve|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 67 | 6.235 [+6.116, +6.353] | 5.974 [+5.810, +6.138] | 0.287 / 0.245 | 0.072 / 0.099 |
| L0|federici|CS_SINGLE  (= RS at epoch 0) | 86 | 8.077 [+8.043, +8.110] | 8.170 [+8.163, +8.176] | 0.396 / 0.491 | 0.012 / 0.001 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 86 | 8.076 [+8.044, +8.109] | 8.170 [+8.164, +8.176] | 0.396 / 0.491 | 0.012 / 0.001 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 86 | 8.077 [+8.043, +8.110] | 8.170 [+8.163, +8.176] | 0.396 / 0.491 | 0.013 / 0.001 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 86 | 8.077 [+8.043, +8.111] | 8.170 [+8.164, +8.176] | 0.396 / 0.491 | 0.013 / 0.001 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 86 | 8.077 [+8.042, +8.111] | 8.170 [+8.164, +8.176] | 0.396 / 0.491 | 0.012 / 0.001 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 86 | 8.079 [+8.045, +8.112] | 8.170 [+8.164, +8.175] | 0.397 / 0.491 | 0.014 / 0.001 |
| L0|federici|NCE  (= RS at epoch 0) | 86 | 8.056 [+8.023, +8.089] | 7.999 [+7.946, +8.052] | 0.390 / 0.365 | 0.012 / 0.016 |
| L1|federici|NCE | 86 | 7.984 [+7.939, +8.029] | 7.952 [+7.887, +8.016] | 0.358 / 0.347 | 0.011 / 0.018 |
| SC|federici|NCE|cbramod|L0|aligned_pretrained | 86 | 8.086 [+8.054, +8.118] | 8.064 [+8.018, +8.109] | 0.404 / 0.392 | 0.008 / 0.010 |
| SC|federici|NCE|cbramod|L0|aligned_random | 86 | 8.084 [+8.055, +8.114] | 8.056 [+8.013, +8.099] | 0.404 / 0.389 | 0.010 / 0.015 |
| SC|federici|NCE|cbramod|L0|concat | 86 | 8.084 [+8.054, +8.115] | 8.062 [+8.025, +8.099] | 0.404 / 0.391 | 0.011 / 0.013 |
| SC|federici|NCE|cbramod|L0|local_only | 86 | 8.083 [+8.053, +8.113] | 8.060 [+8.019, +8.102] | 0.404 / 0.391 | 0.010 / 0.013 |
| SC|federici|NCE|cbramod|L0|local_refit_capacity | 86 | 8.076 [+8.046, +8.106] | 8.052 [+8.009, +8.095] | 0.402 / 0.387 | 0.011 / 0.015 |
| SC|federici|NCE|cbramod|L0|small_context | 86 | 8.086 [+8.057, +8.115] | 8.056 [+8.015, +8.097] | 0.405 / 0.390 | 0.011 / 0.009 |
| SC|federici|NCE|cbramod|L1|aligned_pretrained | 86 | 8.022 [+7.979, +8.066] | 7.983 [+7.932, +8.034] | 0.377 / 0.366 | 0.016 / 0.017 |
| SC|federici|NCE|cbramod|L1|aligned_random | 86 | 8.026 [+7.983, +8.068] | 7.981 [+7.932, +8.029] | 0.379 / 0.365 | 0.012 / 0.018 |
| SC|federici|NCE|cbramod|L1|concat | 86 | 8.027 [+7.984, +8.071] | 7.988 [+7.936, +8.039] | 0.380 / 0.367 | 0.013 / 0.018 |
| SC|federici|NCE|cbramod|L1|local_only | 86 | 8.029 [+7.985, +8.072] | 7.990 [+7.939, +8.040] | 0.381 / 0.368 | 0.012 / 0.019 |
| SC|federici|NCE|cbramod|L1|local_refit_capacity | 86 | 8.020 [+7.975, +8.064] | 7.977 [+7.927, +8.027] | 0.376 / 0.362 | 0.012 / 0.016 |
| SC|federici|NCE|cbramod|L1|small_context | 86 | 8.021 [+7.980, +8.062] | 7.982 [+7.932, +8.032] | 0.378 / 0.364 | 0.010 / 0.017 |
| SC|federici|NCE|reve|L0|aligned_pretrained | 86 | 8.084 [+8.055, +8.113] | 8.054 [+8.014, +8.095] | 0.402 / 0.390 | 0.010 / 0.015 |
| SC|federici|NCE|reve|L0|aligned_random | 86 | 8.088 [+8.059, +8.117] | 8.058 [+8.018, +8.098] | 0.406 / 0.391 | 0.011 / 0.010 |
| SC|federici|NCE|reve|L0|concat | 86 | 8.082 [+8.053, +8.111] | 8.059 [+8.019, +8.099] | 0.402 / 0.390 | 0.010 / 0.012 |
| SC|federici|NCE|reve|L0|local_only | 86 | 8.083 [+8.053, +8.113] | 8.060 [+8.021, +8.100] | 0.404 / 0.391 | 0.010 / 0.013 |
| SC|federici|NCE|reve|L0|local_refit_capacity | 86 | 8.076 [+8.046, +8.106] | 8.052 [+8.010, +8.095] | 0.402 / 0.387 | 0.011 / 0.015 |
| SC|federici|NCE|reve|L0|small_context | 86 | 8.086 [+8.057, +8.116] | 8.056 [+8.016, +8.097] | 0.405 / 0.390 | 0.012 / 0.009 |
| SC|federici|NCE|reve|L1|aligned_pretrained | 86 | 8.023 [+7.980, +8.066] | 7.983 [+7.930, +8.036] | 0.378 / 0.366 | 0.009 / 0.018 |
| SC|federici|NCE|reve|L1|aligned_random | 86 | 8.025 [+7.984, +8.065] | 7.985 [+7.934, +8.035] | 0.380 / 0.366 | 0.010 / 0.016 |
| SC|federici|NCE|reve|L1|concat | 86 | 8.027 [+7.983, +8.071] | 7.989 [+7.940, +8.039] | 0.380 / 0.368 | 0.014 / 0.018 |
| SC|federici|NCE|reve|L1|local_only | 86 | 8.029 [+7.985, +8.072] | 7.990 [+7.938, +8.041] | 0.381 / 0.368 | 0.012 / 0.019 |
| SC|federici|NCE|reve|L1|local_refit_capacity | 86 | 8.020 [+7.977, +8.062] | 7.977 [+7.926, +8.028] | 0.376 / 0.362 | 0.012 / 0.016 |
| SC|federici|NCE|reve|L1|small_context | 86 | 8.022 [+7.980, +8.065] | 7.983 [+7.934, +8.032] | 0.379 / 0.365 | 0.010 / 0.017 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 86 | 8.055 [+8.022, +8.088] | 7.996 [+7.944, +8.049] | 0.390 / 0.365 | 0.012 / 0.015 |
| RS|federici|NCE|cbramod|residual_aligned_random | 86 | 8.056 [+8.023, +8.089] | 7.995 [+7.941, +8.049] | 0.390 / 0.365 | 0.012 / 0.015 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 86 | 8.055 [+8.022, +8.088] | 7.996 [+7.944, +8.048] | 0.390 / 0.365 | 0.011 / 0.017 |
| RS|federici|NCE|reve|residual_aligned_random | 86 | 8.056 [+8.022, +8.090] | 7.995 [+7.942, +8.049] | 0.390 / 0.364 | 0.012 / 0.015 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 86 | 8.055 [+8.020, +8.089] | 7.994 [+7.942, +8.047] | 0.390 / 0.364 | 0.011 / 0.015 |
| FM|federici|NCE|cbramod|pretrained_frozen  (context, reported before) | 86 | 8.103 [+8.072, +8.134] | 8.091 [+8.058, +8.123] | 0.416 / 0.407 | 0.007 / 0.009 |
| FM|federici|NCE|reve|pretrained_frozen  (context, reported before) | 86 | 7.915 [+7.855, +7.975] | 7.872 [+7.786, +7.958] | 0.339 / 0.330 | 0.017 / 0.026 |
| TF|federici|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 86 | 7.788 [+7.691, +7.885] | 7.732 [+7.623, +7.841] | 0.308 / 0.298 | 0.027 / 0.027 |
| TF|federici|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 86 | 7.803 [+7.706, +7.901] | 7.741 [+7.634, +7.848] | 0.312 / 0.301 | 0.024 / 0.026 |
| TF|federici|NCE|reve|pretrained_full|full_onestep_v1|0.0003  (context, reported before) | 86 | 7.817 [+7.734, +7.899] | 7.744 [+7.636, +7.853] | 0.315 / 0.301 | 0.026 / 0.030 |
| TF|federici|NCE|reve|pretrained_full|full_onestep_v1|1e-05  (context, reported before) | 86 | 7.896 [+7.826, +7.966] | 7.842 [+7.756, +7.929] | 0.334 / 0.321 | 0.022 / 0.024 |

## 5. SC variants vs the original direct base

`local_only` enters the cbramod and the reve family of each dataset · base; both copies are listed. They are the same ridge (same input, no PCA; alpha equal in all 50 unit pairs). `local_refit_capacity` and `small_context` also read no FM feature, so the two units of a cell see the same inputs; how far their copies differ is in the table at the end of this section.

**unified readout**

*fau · cbramod · L0* (critical value 2.48)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.036 | [-0.057, -0.014] | [-0.062, -0.009] | I<0 | -0.009 | -0.006 | -0.156 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.036 | [-0.057, -0.014] | [-0.062, -0.009] | I<0 | -0.009 | -0.006 | -0.156 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.029 | [-0.046, -0.012] | [-0.050, -0.008] | I<0 | -0.006 | -0.002 | -0.066 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.018 | [-0.039, +0.004] | [-0.045, +0.010] | contains 0 | -0.005 | -0.005 | -0.113 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.037 | [-0.059, -0.014] | [-0.065, -0.009] | I<0 | -0.008 | -0.002 | -0.116 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.023 | [-0.039, -0.007] | [-0.043, -0.004] | I<0 | -0.005 | -0.002 | -0.058 |

*fau · cbramod · L1* (critical value 2.43)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.014 | [-0.031, +0.003] | [-0.035, +0.008] | contains 0 | -0.008 | -0.003 | -0.142 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.024 | [-0.041, -0.007] | [-0.046, -0.002] | I<0 | -0.008 | -0.004 | -0.124 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 67 | -0.006 | [-0.022, +0.009] | [-0.025, +0.012] | contains 0 | -0.004 | -0.001 | -0.070 |
| aligned_random | access-matched (aligned window = L1's window) | 67 | -0.011 | [-0.031, +0.009] | [-0.036, +0.014] | contains 0 | -0.006 | -0.002 | -0.079 |
| small_context | access-matched (aligned window = L1's window) | 67 | -0.011 | [-0.027, +0.006] | [-0.031, +0.010] | contains 0 | -0.005 | +0.001 | -0.053 |
| concat | access-matched (aligned window = L1's window) | 67 | -0.010 | [-0.026, +0.006] | [-0.029, +0.009] | contains 0 | -0.005 | -0.001 | -0.071 |

*fau · reve · L0* (critical value 2.45)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.036 | [-0.057, -0.014] | [-0.062, -0.010] | I<0 | -0.009 | -0.006 | -0.156 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.036 | [-0.057, -0.014] | [-0.062, -0.009] | I<0 | -0.009 | -0.007 | -0.156 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.031 | [-0.056, -0.005] | [-0.061, -0.000] | I<0 | -0.007 | -0.005 | -0.137 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.032 | [-0.054, -0.010] | [-0.058, -0.005] | I<0 | -0.008 | -0.002 | -0.109 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.047 | [-0.069, -0.024] | [-0.074, -0.019] | I<0 | -0.009 | -0.003 | -0.148 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.030 | [-0.054, -0.006] | [-0.059, -0.001] | I<0 | -0.007 | -0.006 | -0.140 |

*fau · reve · L1* (critical value 2.44)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.014 | [-0.032, +0.004] | [-0.036, +0.008] | contains 0 | -0.008 | -0.003 | -0.142 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.024 | [-0.041, -0.006] | [-0.046, -0.002] | I<0 | -0.008 | -0.004 | -0.124 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 67 | -0.013 | [-0.029, +0.004] | [-0.033, +0.007] | contains 0 | -0.005 | -0.003 | -0.082 |
| aligned_random | access-matched (aligned window = L1's window) | 67 | -0.014 | [-0.031, +0.003] | [-0.035, +0.007] | contains 0 | -0.006 | +0.001 | -0.057 |
| small_context | access-matched (aligned window = L1's window) | 67 | -0.010 | [-0.027, +0.007] | [-0.031, +0.011] | contains 0 | -0.005 | +0.002 | -0.053 |
| concat | access-matched (aligned window = L1's window) | 67 | -0.015 | [-0.032, +0.001] | [-0.035, +0.005] | contains 0 | -0.006 | -0.004 | -0.085 |

*dtu · cbramod · L0* (critical value 2.56)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.106 | [-0.130, -0.082] | [-0.136, -0.076] | I<0 | -0.012 | -0.004 | -0.140 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.103 | [-0.129, -0.077] | [-0.136, -0.070] | I<0 | -0.011 | -0.003 | -0.132 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.058 | [-0.088, -0.028] | [-0.096, -0.020] | I<0 | -0.006 | -0.002 | -0.111 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.065 | [-0.093, -0.037] | [-0.101, -0.030] | I<0 | -0.007 | -0.005 | -0.120 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.061 | [-0.089, -0.032] | [-0.097, -0.024] | I<0 | -0.005 | -0.004 | -0.109 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.055 | [-0.087, -0.023] | [-0.095, -0.015] | I<0 | -0.005 | -0.003 | -0.111 |

*dtu · cbramod · L1* (critical value 2.51)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.130 | [-0.158, -0.102] | [-0.164, -0.095] | I<0 | -0.014 | -0.010 | -0.209 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.089 | [-0.117, -0.061] | [-0.124, -0.055] | I<0 | -0.009 | -0.007 | -0.137 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 44 | -0.081 | [-0.114, -0.048] | [-0.122, -0.040] | I<0 | -0.009 | -0.002 | -0.180 |
| aligned_random | access-matched (aligned window = L1's window) | 44 | -0.086 | [-0.111, -0.062] | [-0.117, -0.056] | I<0 | -0.009 | -0.003 | -0.191 |
| small_context | access-matched (aligned window = L1's window) | 44 | -0.069 | [-0.099, -0.040] | [-0.105, -0.033] | I<0 | -0.006 | -0.001 | -0.162 |
| concat | access-matched (aligned window = L1's window) | 44 | -0.093 | [-0.128, -0.059] | [-0.135, -0.051] | I<0 | -0.010 | -0.002 | -0.193 |

*dtu · reve · L0* (critical value 2.50)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.106 | [-0.130, -0.082] | [-0.136, -0.076] | I<0 | -0.012 | -0.004 | -0.140 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.103 | [-0.129, -0.077] | [-0.135, -0.071] | I<0 | -0.011 | -0.003 | -0.132 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.062 | [-0.096, -0.029] | [-0.104, -0.021] | I<0 | -0.006 | +0.001 | -0.124 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.054 | [-0.084, -0.024] | [-0.092, -0.016] | I<0 | -0.005 | +0.001 | -0.111 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.059 | [-0.088, -0.030] | [-0.095, -0.022] | I<0 | -0.005 | -0.004 | -0.107 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.073 | [-0.108, -0.038] | [-0.115, -0.031] | I<0 | -0.007 | -0.001 | -0.135 |

*dtu · reve · L1* (critical value 2.48)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.130 | [-0.157, -0.103] | [-0.164, -0.096] | I<0 | -0.014 | -0.010 | -0.209 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.089 | [-0.116, -0.062] | [-0.123, -0.055] | I<0 | -0.009 | -0.007 | -0.137 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 44 | -0.081 | [-0.111, -0.051] | [-0.118, -0.044] | I<0 | -0.009 | -0.002 | -0.129 |
| aligned_random | access-matched (aligned window = L1's window) | 44 | -0.068 | [-0.097, -0.039] | [-0.105, -0.031] | I<0 | -0.006 | -0.003 | -0.165 |
| small_context | access-matched (aligned window = L1's window) | 44 | -0.070 | [-0.099, -0.041] | [-0.106, -0.034] | I<0 | -0.006 | -0.001 | -0.163 |
| concat | access-matched (aligned window = L1's window) | 44 | -0.115 | [-0.148, -0.082] | [-0.156, -0.074] | I<0 | -0.013 | -0.004 | -0.160 |

*federici · cbramod · L0* (critical value 2.53)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.027 | [-0.040, -0.014] | [-0.043, -0.011] | I<0 | -0.014 | -0.001 | -0.055 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.020 | [-0.034, -0.007] | [-0.037, -0.003] | I<0 | -0.011 | -0.001 | -0.049 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.030 | [-0.043, -0.017] | [-0.047, -0.013] | I<0 | -0.014 | -0.004 | -0.062 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.028 | [-0.042, -0.015] | [-0.046, -0.011] | I<0 | -0.014 | -0.002 | -0.069 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.030 | [-0.045, -0.016] | [-0.048, -0.012] | I<0 | -0.014 | -0.001 | -0.071 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.028 | [-0.040, -0.016] | [-0.044, -0.013] | I<0 | -0.014 | -0.001 | -0.058 |

*federici · cbramod · L1* (critical value 2.47)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.045 | [-0.060, -0.029] | [-0.064, -0.026] | I<0 | -0.023 | +0.001 | -0.046 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.036 | [-0.051, -0.021] | [-0.055, -0.017] | I<0 | -0.018 | +0.001 | -0.041 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 86 | -0.038 | [-0.053, -0.024] | [-0.057, -0.020] | I<0 | -0.019 | +0.005 | -0.038 |
| aligned_random | access-matched (aligned window = L1's window) | 86 | -0.042 | [-0.056, -0.027] | [-0.060, -0.023] | I<0 | -0.021 | +0.001 | -0.048 |
| small_context | access-matched (aligned window = L1's window) | 86 | -0.037 | [-0.052, -0.022] | [-0.055, -0.019] | I<0 | -0.020 | -0.001 | -0.057 |
| concat | access-matched (aligned window = L1's window) | 86 | -0.044 | [-0.059, -0.029] | [-0.062, -0.025] | I<0 | -0.022 | +0.002 | -0.042 |

*federici · reve · L0* (critical value 2.50)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.027 | [-0.040, -0.014] | [-0.042, -0.011] | I<0 | -0.014 | -0.001 | -0.055 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.020 | [-0.034, -0.007] | [-0.037, -0.003] | I<0 | -0.011 | -0.001 | -0.049 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.028 | [-0.043, -0.014] | [-0.046, -0.011] | I<0 | -0.012 | -0.002 | -0.064 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.032 | [-0.047, -0.017] | [-0.051, -0.014] | I<0 | -0.016 | -0.001 | -0.074 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.031 | [-0.045, -0.016] | [-0.048, -0.013] | I<0 | -0.014 | -0.000 | -0.071 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.026 | [-0.039, -0.013] | [-0.042, -0.010] | I<0 | -0.012 | -0.001 | -0.065 |

*federici · reve · L1* (critical value 2.38)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.045 | [-0.060, -0.030] | [-0.063, -0.027] | I<0 | -0.023 | +0.001 | -0.046 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.036 | [-0.050, -0.021] | [-0.054, -0.018] | I<0 | -0.018 | +0.001 | -0.041 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 86 | -0.039 | [-0.054, -0.024] | [-0.057, -0.021] | I<0 | -0.020 | -0.002 | -0.044 |
| aligned_random | access-matched (aligned window = L1's window) | 86 | -0.041 | [-0.056, -0.026] | [-0.060, -0.022] | I<0 | -0.022 | -0.001 | -0.061 |
| small_context | access-matched (aligned window = L1's window) | 86 | -0.039 | [-0.053, -0.024] | [-0.056, -0.021] | I<0 | -0.020 | -0.001 | -0.057 |
| concat | access-matched (aligned window = L1's window) | 86 | -0.043 | [-0.059, -0.028] | [-0.062, -0.024] | I<0 | -0.022 | +0.003 | -0.046 |

**native readout**

*fau · cbramod · L0* (critical value 2.11)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.222 | [-0.273, -0.171] | [-0.276, -0.168] | I<0 | -0.039 | -0.031 | -0.550 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.222 | [-0.273, -0.171] | [-0.276, -0.168] | I<0 | -0.039 | -0.031 | -0.550 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.220 | [-0.271, -0.169] | [-0.274, -0.165] | I<0 | -0.039 | -0.026 | -0.556 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.231 | [-0.283, -0.179] | [-0.287, -0.175] | I<0 | -0.041 | -0.029 | -0.557 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.237 | [-0.289, -0.185] | [-0.292, -0.182] | I<0 | -0.042 | -0.029 | -0.576 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.223 | [-0.274, -0.172] | [-0.277, -0.169] | I<0 | -0.040 | -0.027 | -0.556 |

*fau · cbramod · L1* (critical value 2.17)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.193 | [-0.224, -0.161] | [-0.227, -0.159] | I<0 | -0.032 | -0.018 | -0.233 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.195 | [-0.225, -0.165] | [-0.228, -0.163] | I<0 | -0.033 | -0.019 | -0.236 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 67 | -0.188 | [-0.220, -0.155] | [-0.223, -0.152] | I<0 | -0.032 | -0.019 | -0.227 |
| aligned_random | access-matched (aligned window = L1's window) | 67 | -0.190 | [-0.223, -0.158] | [-0.225, -0.155] | I<0 | -0.032 | -0.018 | -0.227 |
| small_context | access-matched (aligned window = L1's window) | 67 | -0.188 | [-0.220, -0.155] | [-0.223, -0.152] | I<0 | -0.032 | -0.017 | -0.235 |
| concat | access-matched (aligned window = L1's window) | 67 | -0.193 | [-0.225, -0.160] | [-0.228, -0.157] | I<0 | -0.033 | -0.018 | -0.230 |

*fau · reve · L0* (critical value 2.11)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.222 | [-0.272, -0.172] | [-0.276, -0.168] | I<0 | -0.039 | -0.031 | -0.550 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.222 | [-0.272, -0.172] | [-0.276, -0.168] | I<0 | -0.039 | -0.031 | -0.550 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.233 | [-0.285, -0.182] | [-0.288, -0.178] | I<0 | -0.042 | -0.030 | -0.568 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.237 | [-0.289, -0.186] | [-0.293, -0.182] | I<0 | -0.042 | -0.030 | -0.575 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.238 | [-0.290, -0.186] | [-0.293, -0.182] | I<0 | -0.042 | -0.030 | -0.576 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 67 | -0.233 | [-0.285, -0.182] | [-0.288, -0.179] | I<0 | -0.042 | -0.029 | -0.570 |

*fau · reve · L1* (critical value 2.17)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 67 | -0.193 | [-0.224, -0.161] | [-0.227, -0.159] | I<0 | -0.032 | -0.018 | -0.233 |
| local_refit_capacity | access-matched (the base's own tokens) | 67 | -0.195 | [-0.225, -0.165] | [-0.228, -0.163] | I<0 | -0.033 | -0.019 | -0.236 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 67 | -0.195 | [-0.227, -0.163] | [-0.230, -0.160] | I<0 | -0.034 | -0.018 | -0.240 |
| aligned_random | access-matched (aligned window = L1's window) | 67 | -0.189 | [-0.222, -0.157] | [-0.225, -0.154] | I<0 | -0.032 | -0.017 | -0.236 |
| small_context | access-matched (aligned window = L1's window) | 67 | -0.188 | [-0.220, -0.155] | [-0.223, -0.152] | I<0 | -0.032 | -0.017 | -0.235 |
| concat | access-matched (aligned window = L1's window) | 67 | -0.198 | [-0.231, -0.166] | [-0.234, -0.163] | I<0 | -0.034 | -0.019 | -0.244 |

*dtu · cbramod · L0* (critical value 2.17)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.579 | [-0.687, -0.472] | [-0.696, -0.463] | I<0 | -0.057 | -0.061 | -1.452 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.589 | [-0.699, -0.479] | [-0.706, -0.472] | I<0 | -0.058 | -0.062 | -1.458 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.585 | [-0.702, -0.469] | [-0.711, -0.460] | I<0 | -0.058 | -0.058 | -1.465 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.603 | [-0.713, -0.492] | [-0.721, -0.484] | I<0 | -0.060 | -0.058 | -1.493 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.580 | [-0.696, -0.464] | [-0.704, -0.456] | I<0 | -0.056 | -0.057 | -1.459 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.587 | [-0.703, -0.471] | [-0.711, -0.463] | I<0 | -0.058 | -0.059 | -1.472 |

*dtu · cbramod · L1* (critical value 2.19)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.488 | [-0.575, -0.400] | [-0.582, -0.393] | I<0 | -0.053 | -0.045 | -1.222 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.507 | [-0.593, -0.420] | [-0.602, -0.412] | I<0 | -0.052 | -0.047 | -1.147 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 44 | -0.486 | [-0.578, -0.393] | [-0.586, -0.385] | I<0 | -0.053 | -0.044 | -1.222 |
| aligned_random | access-matched (aligned window = L1's window) | 44 | -0.504 | [-0.593, -0.416] | [-0.601, -0.408] | I<0 | -0.055 | -0.044 | -1.252 |
| small_context | access-matched (aligned window = L1's window) | 44 | -0.478 | [-0.566, -0.389] | [-0.575, -0.381] | I<0 | -0.052 | -0.047 | -1.161 |
| concat | access-matched (aligned window = L1's window) | 44 | -0.497 | [-0.590, -0.404] | [-0.599, -0.395] | I<0 | -0.055 | -0.047 | -1.236 |

*dtu · reve · L0* (critical value 2.15)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.579 | [-0.687, -0.472] | [-0.694, -0.465] | I<0 | -0.057 | -0.061 | -1.452 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.589 | [-0.699, -0.479] | [-0.705, -0.473] | I<0 | -0.058 | -0.062 | -1.458 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.594 | [-0.710, -0.478] | [-0.717, -0.470] | I<0 | -0.059 | -0.056 | -1.483 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.581 | [-0.697, -0.464] | [-0.704, -0.457] | I<0 | -0.057 | -0.057 | -1.462 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.578 | [-0.695, -0.462] | [-0.701, -0.456] | I<0 | -0.056 | -0.057 | -1.456 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 44 | -0.608 | [-0.724, -0.491] | [-0.732, -0.483] | I<0 | -0.060 | -0.058 | -1.502 |

*dtu · reve · L1* (critical value 2.22)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 44 | -0.488 | [-0.575, -0.400] | [-0.584, -0.391] | I<0 | -0.053 | -0.045 | -1.222 |
| local_refit_capacity | access-matched (the base's own tokens) | 44 | -0.507 | [-0.595, -0.418] | [-0.603, -0.410] | I<0 | -0.052 | -0.047 | -1.147 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 44 | -0.496 | [-0.590, -0.402] | [-0.599, -0.393] | I<0 | -0.055 | -0.047 | -1.230 |
| aligned_random | access-matched (aligned window = L1's window) | 44 | -0.478 | [-0.569, -0.386] | [-0.577, -0.378] | I<0 | -0.052 | -0.047 | -1.165 |
| small_context | access-matched (aligned window = L1's window) | 44 | -0.477 | [-0.567, -0.387] | [-0.575, -0.379] | I<0 | -0.052 | -0.048 | -1.162 |
| concat | access-matched (aligned window = L1's window) | 44 | -0.510 | [-0.604, -0.416] | [-0.614, -0.406] | I<0 | -0.056 | -0.048 | -1.247 |

*federici · cbramod · L0* (critical value 2.37)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.062 | [-0.084, -0.039] | [-0.089, -0.034] | I<0 | -0.026 | -0.003 | -0.127 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.053 | [-0.074, -0.032] | [-0.079, -0.028] | I<0 | -0.022 | -0.001 | -0.095 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.065 | [-0.089, -0.041] | [-0.093, -0.037] | I<0 | -0.027 | -0.005 | -0.114 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.057 | [-0.081, -0.033] | [-0.084, -0.030] | I<0 | -0.024 | -0.001 | -0.106 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.057 | [-0.083, -0.032] | [-0.088, -0.027] | I<0 | -0.025 | -0.007 | -0.121 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.063 | [-0.088, -0.039] | [-0.093, -0.034] | I<0 | -0.026 | -0.003 | -0.148 |

*federici · cbramod · L1* (critical value 2.37)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.038 | [-0.070, -0.006] | [-0.074, -0.001] | I<0 | -0.020 | +0.001 | -0.088 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.025 | [-0.055, +0.004] | [-0.060, +0.009] | contains 0 | -0.014 | -0.001 | -0.071 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 86 | -0.031 | [-0.060, -0.002] | [-0.065, +0.003] | contains 0 | -0.019 | -0.001 | -0.079 |
| aligned_random | access-matched (aligned window = L1's window) | 86 | -0.029 | [-0.060, +0.003] | [-0.065, +0.007] | contains 0 | -0.017 | +0.000 | -0.082 |
| small_context | access-matched (aligned window = L1's window) | 86 | -0.030 | [-0.060, +0.000] | [-0.065, +0.005] | contains 0 | -0.017 | -0.001 | -0.083 |
| concat | access-matched (aligned window = L1's window) | 86 | -0.036 | [-0.066, -0.006] | [-0.071, -0.001] | I<0 | -0.020 | +0.001 | -0.083 |

*federici · reve · L0* (critical value 2.32)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.062 | [-0.085, -0.038] | [-0.088, -0.035] | I<0 | -0.026 | -0.003 | -0.127 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.053 | [-0.075, -0.032] | [-0.078, -0.029] | I<0 | -0.022 | -0.001 | -0.095 |
| aligned_pretrained | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.055 | [-0.079, -0.032] | [-0.083, -0.028] | I<0 | -0.024 | -0.001 | -0.116 |
| aligned_random | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.059 | [-0.084, -0.033] | [-0.089, -0.029] | I<0 | -0.025 | -0.005 | -0.124 |
| small_context | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.058 | [-0.083, -0.032] | [-0.088, -0.028] | I<0 | -0.025 | -0.007 | -0.121 |
| concat | context-assisted (adds [-0.4 s, 0) to L0's [0, post)) | 86 | -0.060 | [-0.083, -0.037] | [-0.087, -0.033] | I<0 | -0.025 | -0.004 | -0.129 |

*federici · reve · L1* (critical value 2.40)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| local_only | remap only (the base's own input) | 86 | -0.038 | [-0.070, -0.006] | [-0.075, -0.001] | I<0 | -0.020 | +0.001 | -0.088 |
| local_refit_capacity | access-matched (the base's own tokens) | 86 | -0.025 | [-0.055, +0.005] | [-0.060, +0.009] | contains 0 | -0.014 | -0.001 | -0.071 |
| aligned_pretrained | access-matched (aligned window = L1's window) | 86 | -0.031 | [-0.062, -0.000] | [-0.067, +0.005] | contains 0 | -0.018 | +0.001 | -0.087 |
| aligned_random | access-matched (aligned window = L1's window) | 86 | -0.033 | [-0.065, -0.001] | [-0.070, +0.004] | contains 0 | -0.019 | -0.001 | -0.083 |
| small_context | access-matched (aligned window = L1's window) | 86 | -0.031 | [-0.062, -0.001] | [-0.067, +0.004] | contains 0 | -0.017 | -0.000 | -0.083 |
| concat | access-matched (aligned window = L1's window) | 86 | -0.038 | [-0.070, -0.005] | [-0.075, -0.000] | I<0 | -0.021 | +0.000 | -0.090 |

Cross-backbone copies of the FM-free SC variants (cbramod unit vs reve unit of the same cell; record values):

| dataset · base · variant | unit pairs | alpha equal | max per-participant \|Δ log-loss\| unified / native | max per-identity \|ΔR\| unified / native |
|---|---|---|---|---|
| dtu · L0 · local_only | 10 | 10 | 1.1e-04 / 1.5e-04 | 5.4e-05 / 7.6e-05 |
| dtu · L0 · local_refit_capacity | 10 | 9 | 1.1e-04 / 1.5e-04 | 5.4e-05 / 7.5e-05 |
| dtu · L0 · small_context | 10 | 8 | 4.1e-02 / 4.1e-02 | 2.0e-02 / 2.1e-02 |
| dtu · L1 · local_only | 10 | 10 | 1.4e-04 / 1.3e-04 | 9.8e-05 / 1.1e-04 |
| dtu · L1 · local_refit_capacity | 10 | 10 | 2.0e-04 / 1.8e-04 | 9.2e-05 / 6.5e-05 |
| dtu · L1 · small_context | 10 | 10 | 3.5e-02 / 2.8e-02 | 1.8e-02 / 1.4e-02 |
| fau · L0 · local_only | 10 | 10 | 1.1e-04 / 1.3e-04 | 6.3e-05 / 7.6e-05 |
| fau · L0 · local_refit_capacity | 10 | 10 | 1.1e-04 / 1.3e-04 | 6.3e-05 / 7.6e-05 |
| fau · L0 · small_context | 10 | 7 | 2.0e-01 / 3.1e-02 | 1.0e-01 / 1.5e-02 |
| fau · L1 · local_only | 10 | 10 | 9.7e-05 / 1.0e-04 | 4.9e-05 / 5.0e-05 |
| fau · L1 · local_refit_capacity | 10 | 9 | 9.9e-05 / 1.0e-04 | 4.9e-05 / 5.2e-05 |
| fau · L1 · small_context | 10 | 9 | 3.8e-02 / 3.0e-02 | 1.9e-02 / 1.5e-02 |
| federici · L0 · local_only | 5 | 5 | 2.3e-04 / 2.2e-04 | 1.1e-04 / 7.8e-05 |
| federici · L0 · local_refit_capacity | 5 | 4 | 2.0e-04 / 1.9e-04 | 2.0e-04 / 1.5e-04 |
| federici · L0 · small_context | 5 | 4 | 2.8e-02 / 2.7e-02 | 2.7e-02 / 2.7e-02 |
| federici · L1 · local_only | 5 | 5 | 4.0e-04 / 2.4e-04 | 2.2e-04 / 1.7e-04 |
| federici · L1 · local_refit_capacity | 5 | 3 | 1.8e-04 / 2.4e-04 | 1.4e-04 / 1.3e-04 |
| federici · L1 · small_context | 5 | 2 | 2.0e-02 / 2.2e-02 | 2.0e-02 / 2.2e-02 |

## 6. RS selected epoch vs epoch 0 (= base L0)

The unified family uses the frozen RS-VALUE labels and reproduces `COMPLEMENT_REVISED_RESIDUAL_RESULTS.md` §3 (already seen; regression in §2). The native family's point estimates were already visible there as the secondary column ΔR_native; its intervals and classes are new.

**unified readout**

*fau · NCE* (critical value 2.96)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.000 | -0.001 | -0.000 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.000 | +0.001 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | -0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 | -0.000 | -0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | +0.007 | [+0.001, +0.012] | [-0.001, +0.014] | contains 0 | +0.001 | +0.001 | +0.006 |

*fau · CS_SINGLE* (critical value 2.73)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.002 | [-0.004, +0.001] | [-0.005, +0.001] | contains 0 | -0.000 | -0.000 | -0.001 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.001 | [-0.002, +0.001] | [-0.003, +0.002] | contains 0 | +0.000 | +0.000 | -0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | -0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.018 | [-0.032, -0.005] | [-0.037, -0.000] | I<0 | -0.006 | -0.003 | -0.068 |

*dtu · NCE* (critical value 2.67)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.000 | +0.000 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | -0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.000 | +0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | -0.000 | +0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.016 | [+0.006, +0.026] | [+0.004, +0.028] | I>0 | +0.002 | +0.002 | +0.015 |

*dtu · CS_SINGLE* (critical value 2.86)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.021 | [-0.039, -0.003] | [-0.045, +0.003] | contains 0 | -0.004 | -0.000 | -0.016 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.003 | [-0.006, +0.001] | [-0.007, +0.002] | contains 0 | -0.000 | -0.000 | -0.001 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.016 | [-0.027, -0.005] | [-0.031, -0.001] | I<0 | -0.003 | -0.001 | -0.013 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.002 | [-0.000, +0.004] | [-0.001, +0.005] | contains 0 | +0.000 | +0.001 | +0.003 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.087 | [-0.105, -0.069] | [-0.112, -0.061] | I<0 | -0.012 | -0.004 | -0.071 |

*federici · NCE* (critical value 2.74)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.001 | [-0.000, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 | +0.000 | +0.001 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.001 | [+0.000, +0.002] | [-0.000, +0.002] | contains 0 | +0.001 | -0.001 | +0.001 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | -0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.001 | [+0.000, +0.003] | [-0.000, +0.003] | contains 0 | +0.000 | -0.000 | +0.001 |

*federici · CS_SINGLE* (critical value 2.40)

| member | access | n | ΔR unified | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 | +0.001 | +0.000 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | -0.001 | [-0.004, +0.003] | [-0.005, +0.004] | contains 0 | -0.000 | +0.001 | +0.011 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | +0.000 | +0.001 | +0.011 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | -0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | +0.000 | +0.000 | +0.011 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | -0.002 | [-0.010, +0.006] | [-0.012, +0.007] | contains 0 | -0.001 | +0.002 | +0.001 |

**native readout**

*fau · NCE* (critical value 2.59)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.004 | [-0.006, -0.003] | [-0.006, -0.002] | I<0 | -0.000 | +0.000 | -0.001 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.003 | [-0.004, -0.001] | [-0.004, -0.001] | I<0 | -0.000 | +0.001 | +0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.003 | [-0.005, -0.002] | [-0.005, -0.002] | I<0 | -0.000 | +0.000 | -0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.004 | [-0.006, -0.003] | [-0.006, -0.002] | I<0 | -0.000 | +0.000 | -0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | +0.004 | [-0.005, +0.013] | [-0.008, +0.016] | contains 0 | +0.001 | +0.001 | -0.040 |

*fau · CS_SINGLE* (critical value 2.74)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.001 | [-0.004, +0.001] | [-0.005, +0.002] | contains 0 | +0.000 | +0.000 | -0.001 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | +0.000 | +0.000 | -0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.001 | [-0.003, +0.001] | [-0.003, +0.001] | contains 0 | -0.000 | +0.000 | -0.002 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | -0.000 | -0.000 | -0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 67 | -0.021 | [-0.029, -0.013] | [-0.032, -0.010] | I<0 | -0.006 | -0.004 | -0.052 |

*dtu · NCE* (critical value 2.49)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.002 | [+0.001, +0.004] | [+0.001, +0.004] | I>0 | +0.000 | +0.001 | +0.001 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.003 | [+0.001, +0.004] | [+0.001, +0.005] | I>0 | +0.000 | +0.001 | +0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.002 | [+0.001, +0.004] | [+0.000, +0.004] | I>0 | +0.000 | +0.001 | +0.001 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.003 | [+0.001, +0.004] | [+0.001, +0.004] | I>0 | +0.000 | +0.001 | +0.001 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.012 | [-0.001, +0.026] | [-0.005, +0.029] | contains 0 | +0.001 | +0.001 | +0.004 |

*dtu · CS_SINGLE* (critical value 3.15)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.022 | [-0.043, -0.002] | [-0.051, +0.006] | contains 0 | -0.004 | -0.002 | -0.022 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.001 | [-0.001, +0.002] | [-0.002, +0.003] | contains 0 | +0.000 | +0.000 | +0.001 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.009 | [-0.017, -0.000] | [-0.021, +0.003] | contains 0 | -0.002 | -0.001 | -0.008 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | +0.001 | [-0.000, +0.003] | [-0.001, +0.004] | contains 0 | +0.000 | +0.000 | +0.002 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 44 | -0.054 | [-0.067, -0.042] | [-0.075, -0.034] | I<0 | -0.010 | -0.003 | -0.080 |

*federici · NCE* (critical value 2.35)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.002 | [-0.001, +0.005] | [-0.001, +0.006] | contains 0 | +0.000 | -0.000 | +0.000 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.003 | [-0.001, +0.006] | [-0.002, +0.007] | contains 0 | +0.000 | +0.001 | +0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.004 | [-0.000, +0.007] | [-0.001, +0.008] | contains 0 | +0.001 | -0.000 | +0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.004 | [-0.000, +0.007] | [-0.001, +0.008] | contains 0 | +0.001 | -0.000 | +0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.004 | [+0.001, +0.008] | [+0.001, +0.008] | I>0 | +0.001 | -0.000 | +0.002 |

*federici · CS_SINGLE* (critical value 2.63)

| member | access | n | ΔR native | 95% CI | 95% simultaneous | class | Δrank_pct | Δtop1 | Δgain |
|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | +0.000 | -0.000 |
| reve/residual_aligned_pretrained | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | -0.000 | [-0.000, -0.000] | [-0.000, +0.000] | contains 0 | -0.000 | +0.000 | -0.000 |
| cbramod/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 |
| reve/residual_aligned_random | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 |
| small_capacity_branch/residual_small_capacity | context-assisted (context branch reads [-0.4 s, post); epoch 0 = base L0) | 86 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.001 | -0.000 | -0.001 |

## 7. Layer 4 — development vs outer test, epoch 0 vs the selected epoch (unit-level, descriptive)

Δdev = dev risk(epoch 0) − dev risk(selected) ≥ 0 by construction (bits; the development pool of ≤ 300 group-0 segments, dot-product score). Δtest = base L0 − RS on the outer test (bits, mean over the unit's test participants; same scale as §6 but unit-level). Units share training participants; the identity-level test inference is §6.

| configuration | units | epoch 0 | sel. epoch median [range] | Δdev mean | Δdev/dev0 | Δtest unified | Δtest native | test better (native, epoch>0) | Spearman Δdev~Δtest native |
|---|---|---|---|---|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0 | 9.5 [2, 26] | +0.0013 | +0.0002 | -0.0222 | -0.0238 | 0.40 | -0.58 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0 | 2.5 [1, 21] | +0.0007 | +0.0001 | -0.0164 | -0.0097 | 0.30 | -0.37 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0 | 14.5 [1, 27] | +0.0004 | +0.0001 | -0.0025 | +0.0006 | 0.60 | +0.27 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 10 | 1 | 10 [0, 27] | +0.0002 | +0.0000 | +0.0019 | +0.0014 | 0.67 | +0.15 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0 | 17.5 [1, 26] | +0.0045 | +0.0006 | -0.0883 | -0.0568 | 0.00 | +0.10 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 0 | 13 [3, 24] | +0.0035 | +0.0005 | +0.0003 | +0.0025 | 0.60 | -0.08 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 0 | 8.5 [2, 24] | +0.0035 | +0.0005 | +0.0002 | +0.0023 | 0.60 | -0.26 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 0 | 16.5 [4, 24] | +0.0040 | +0.0006 | +0.0001 | +0.0030 | 0.70 | -0.09 |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 0 | 13 [1, 24] | +0.0034 | +0.0005 | +0.0000 | +0.0025 | 0.70 | -0.36 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 10 | 3 | 8 [0, 30] | +0.0078 | +0.0012 | +0.0153 | +0.0118 | 0.86 | -0.57 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 1 | 15 [0, 30] | +0.0008 | +0.0001 | -0.0015 | -0.0012 | 0.67 | -0.28 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 10 | 1 | 7.5 [0, 27] | +0.0004 | +0.0001 | -0.0005 | -0.0011 | 0.56 | -0.02 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 1 | 16.5 [0, 30] | +0.0001 | +0.0000 | +0.0000 | -0.0001 | 0.44 | -0.30 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 10 | 1 | 16.5 [0, 30] | +0.0001 | +0.0000 | -0.0004 | -0.0004 | 0.44 | -0.57 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 1 | 4 [0, 29] | +0.0014 | +0.0002 | -0.0183 | -0.0205 | 0.22 | +0.28 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 0 | 8.5 [1, 27] | +0.0047 | +0.0008 | -0.0006 | -0.0043 | 0.40 | -0.61 |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 0 | 9 [3, 24] | +0.0042 | +0.0007 | -0.0002 | -0.0034 | 0.30 | -0.47 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 0 | 14 [7, 27] | +0.0044 | +0.0007 | +0.0002 | -0.0026 | 0.50 | -0.55 |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 0 | 18.5 [8, 27] | +0.0040 | +0.0006 | -0.0005 | -0.0045 | 0.30 | -0.43 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 10 | 1 | 10.5 [0, 25] | +0.0123 | +0.0020 | +0.0063 | +0.0043 | 0.56 | -0.17 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 5 | 1 | 1 [0, 2] | +0.0007 | +0.0001 | +0.0010 | -0.0000 | 0.50 | – |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 5 | 1 | 14 [0, 28] | +0.0006 | +0.0001 | -0.0020 | +0.0000 | 0.75 | – |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 5 | 1 | 8 [0, 25] | +0.0006 | +0.0001 | -0.0032 | -0.0002 | 0.50 | – |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 5 | 3 | 0 [0, 28] | +0.0000 | +0.0000 | -0.0024 | +0.0000 | 0.50 | – |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0 | 8 [2, 18] | +0.0037 | +0.0005 | +0.0016 | +0.0007 | 0.20 | +0.30 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 0 | 24 [4, 30] | +0.0009 | +0.0001 | +0.0001 | +0.0028 | 0.80 | +0.80 |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 0 | 11 [1, 30] | +0.0010 | +0.0001 | +0.0000 | +0.0047 | 0.60 | +0.80 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 0 | 11 [1, 30] | +0.0009 | +0.0001 | +0.0004 | +0.0036 | 0.60 | +1.00 |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 0 | 23 [2, 30] | +0.0009 | +0.0001 | +0.0000 | +0.0046 | 0.80 | +0.80 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 0 | 22 [3, 30] | +0.0014 | +0.0002 | -0.0010 | +0.0035 | 0.80 | +0.20 |

Readout temperatures refitted by the evaluator (training side), RS selected / base, median over epoch>0 units:

| configuration | units epoch>0 | τ unified ratio | τ native ratio [range] | α unified changed |
|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0.998 | 1.002 [0.930, 1.023] | 0.20 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 1.000 | 1.000 [0.939, 1.006] | 0.20 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 1.000 | 1.002 [0.997, 1.020] | 0.00 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 9 | 1.000 | 1.000 [0.997, 1.003] | 0.00 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0.979 | 0.969 [0.934, 1.282] | 0.50 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 1.000 | 0.981 [0.908, 1.020] | 0.00 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 1.000 | 0.976 [0.906, 1.020] | 0.00 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 1.000 | 0.976 [0.909, 1.031] | 0.00 |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 1.000 | 0.984 [0.951, 1.019] | 0.00 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 7 | 1.007 | 1.012 [0.943, 1.058] | 0.00 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 9 | 1.000 | 0.999 [0.996, 1.039] | 0.00 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 9 | 1.000 | 0.999 [0.997, 1.000] | 0.00 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 9 | 1.000 | 1.000 [0.998, 1.004] | 0.00 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 9 | 1.000 | 1.000 [0.999, 1.003] | 0.00 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 9 | 0.991 | 0.980 [0.938, 1.310] | 0.22 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 1.000 | 0.983 [0.940, 1.009] | 0.00 |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 1.000 | 0.965 [0.945, 0.997] | 0.00 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 1.000 | 0.965 [0.944, 1.000] | 0.00 |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 1.000 | 0.967 [0.915, 1.000] | 0.00 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 9 | 1.000 | 0.976 [0.936, 1.435] | 0.22 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 4 | 1.000 | 1.000 [0.999, 1.001] | 0.00 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 4 | 0.999 | 1.000 [1.000, 1.001] | 0.00 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 4 | 0.998 | 1.000 [0.999, 1.000] | 0.00 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 2 | 0.875 | 1.000 [1.000, 1.000] | 0.00 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0.999 | 0.999 [0.995, 1.328] | 0.20 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 1.000 | 1.012 [0.952, 1.044] | 0.20 |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 1.000 | 1.016 [0.980, 1.047] | 0.00 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 1.000 | 1.000 [0.985, 1.038] | 0.20 |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 1.000 | 1.013 [0.964, 1.047] | 0.00 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 1.000 | 0.994 [0.950, 1.038] | 0.20 |

## 8. Residual last layer at the selected epoch (parameter level, not ||r||)

| configuration | units | epoch 0 (zero layer) | ‖W₂‖_F median | ‖W₂‖₂ median [max] | ‖b₂‖ median [max] |
|---|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0 (0) | +0.3657 | +0.1969 [+0.6936] | +0.0526 [+0.1652] |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0 (0) | +0.2597 | +0.1390 [+0.2070] | +0.0346 [+0.0756] |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0 (0) | +0.2821 | +0.1460 [+0.2363] | +0.0616 [+0.1346] |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 10 | 1 (1) | +0.2123 | +0.1253 [+0.1422] | +0.0821 [+0.2188] |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0 (0) | +0.9122 | +0.7038 [+0.9463] | +0.0621 [+0.1700] |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 0 (0) | +0.2388 | +0.1093 [+0.1638] | +0.0296 [+0.1177] |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 0 (0) | +0.2161 | +0.0959 [+0.1074] | +0.0299 [+0.1198] |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 0 (0) | +0.2160 | +0.1094 [+0.2120] | +0.0364 [+0.1175] |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 0 (0) | +0.2053 | +0.1146 [+0.1547] | +0.0267 [+0.0623] |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 10 | 3 (3) | +0.5829 | +0.2962 [+0.4981] | +0.0421 [+0.0835] |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 1 (1) | +0.4599 | +0.2361 [+0.4527] | +0.0364 [+0.0652] |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 10 | 1 (1) | +0.3187 | +0.1528 [+0.4071] | +0.0351 [+0.0925] |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 1 (1) | +0.4005 | +0.1976 [+0.5804] | +0.0406 [+0.0652] |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 10 | 1 (1) | +0.2953 | +0.1552 [+0.2411] | +0.0482 [+0.0653] |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 1 (1) | +0.7338 | +0.4182 [+1.1470] | +0.0439 [+0.1052] |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 0 (0) | +0.2723 | +0.1283 [+0.1892] | +0.0326 [+0.0724] |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 0 (0) | +0.2533 | +0.1233 [+0.2171] | +0.0480 [+0.0670] |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 0 (0) | +0.3144 | +0.1678 [+0.3103] | +0.0465 [+0.0671] |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 0 (0) | +0.2576 | +0.1486 [+0.2260] | +0.0435 [+0.1061] |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 10 | 1 (1) | +0.5449 | +0.2745 [+0.6058] | +0.0376 [+0.0633] |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 5 | 1 (1) | +0.2977 | +0.1541 [+0.1683] | +0.0464 [+0.0506] |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 5 | 1 (1) | +0.3290 | +0.1685 [+0.1750] | +0.0397 [+0.0584] |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 5 | 1 (1) | +0.4239 | +0.2464 [+0.4422] | +0.0577 [+0.1001] |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 5 | 3 (3) | +0.2257 | +0.1137 [+0.1200] | +0.0496 [+0.0583] |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0 (0) | +0.5054 | +0.2897 [+0.5909] | +0.0911 [+0.1099] |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 0 (0) | +0.2940 | +0.2648 [+0.3586] | +0.0405 [+0.0510] |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 0 (0) | +0.2342 | +0.1972 [+0.3201] | +0.0213 [+0.0464] |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 0 (0) | +0.2505 | +0.1978 [+0.2509] | +0.0190 [+0.0403] |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 0 (0) | +0.1917 | +0.1479 [+0.3093] | +0.0377 [+0.0467] |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 0 (0) | +0.3465 | +0.2608 [+0.3294] | +0.0117 [+0.0530] |

## 9. Layers 1–3 per query (forward passes)

Merged: v2 outputs in `results/auditory_alignment_v3/aln34/complement_function/units_v2/` only. Units run and reproduced: 234; epoch-0 units (exact zeros, checkpoint-verified): 16; pending: 0; flagged (re-run did not reproduce the record): 0. Evaluator sha256 of the merged runs: be2107d36af9 (234 units). CLI module versions recorded by the v2 outputs (the CLI was edited during the CPU batch; its per-unit path is main() -> evaluate_unit): 056fdb0de95b (3 outputs; snapshot present; main() identical to the current one); 6cd5e3fc51ff (1 outputs; snapshot present; main() identical to the current one); d98dce999c4b (224 outputs; snapshot present; main() identical to the current one); fadfbf789ff7 (9 outputs; snapshot present; main() identical to the current one).

Coverage over the 30 RS configurations: complete 30, partly covered 0 (epoch-0 zeros and/or some runs), not covered 0. A configuration is summarised only when every unit is covered (epoch-0 zeros alone would bias it).

| configuration | units | epoch-0 zeros | runs reproduced | coverage |
|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0 | 10 | complete |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 10 | 1 | 9 | complete |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0 | 10 | complete |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 0 | 10 | complete |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 0 | 10 | complete |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 10 | 3 | 7 | complete |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 1 | 9 | complete |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 10 | 1 | 9 | complete |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 1 | 9 | complete |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 10 | 1 | 9 | complete |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 1 | 9 | complete |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 0 | 10 | complete |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 0 | 10 | complete |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 0 | 10 | complete |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 10 | 1 | 9 | complete |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 5 | 1 | 4 | complete |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 5 | 1 | 4 | complete |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 5 | 1 | 4 | complete |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 5 | 3 | 2 | complete |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0 | 5 | complete |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 0 | 5 | complete |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 0 | 5 | complete |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 0 | 5 | complete |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 0 | 5 | complete |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 0 | 5 | complete |

Pointwise bootstrap-t over identities (diagnostics, not a contrast family).

| configuration | identities | ‖r‖/‖u‖ [95% CI] | parallel coef (r·u/u·u) | ‖r∥‖/‖u‖ | ‖r⊥‖/‖u‖ | angle (deg) | post-norm change |
|---|---|---|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 44 | +1.0261 [+0.501, +1.551] | +0.4120 | +0.7026 | +0.6599 | +17.441 | +0.2903 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 44 | +0.2462 [+0.186, +0.307] | +0.0083 | +0.1643 | +0.1608 | +9.871 | +0.1688 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 44 | +0.1119 [+0.098, +0.125] | +0.0061 | +0.0774 | +0.0702 | +3.853 | +0.0670 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 44 | +0.0887 [+0.077, +0.101] | -0.0059 | +0.0650 | +0.0512 | +2.977 | +0.0519 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 44 | +1.3068 [+1.073, +1.541] | +0.8980 | +1.0186 | +0.6948 | +20.366 | +0.3488 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 44 | +0.0441 [+0.036, +0.053] | +0.0300 | +0.0337 | +0.0259 | +1.421 | +0.0248 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 44 | +0.0434 [+0.036, +0.051] | +0.0308 | +0.0344 | +0.0242 | +1.331 | +0.0232 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 44 | +0.0492 [+0.042, +0.056] | +0.0328 | +0.0390 | +0.0275 | +1.507 | +0.0263 |
| RS|dtu|NCE|reve|residual_aligned_random | 44 | +0.0348 [+0.032, +0.038] | +0.0220 | +0.0256 | +0.0212 | +1.186 | +0.0207 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 44 | +0.0351 [+0.029, +0.041] | +0.0125 | +0.0172 | +0.0290 | +1.629 | +0.0284 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 67 | +0.1299 [+0.099, +0.161] | +0.0385 | +0.0841 | +0.0887 | +4.371 | +0.0757 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 67 | +0.0803 [+0.065, +0.095] | +0.0126 | +0.0464 | +0.0594 | +3.246 | +0.0565 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 67 | +0.0434 [+0.039, +0.047] | +0.0000 | +0.0270 | +0.0306 | +1.716 | +0.0299 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 67 | +0.0529 [+0.046, +0.060] | -0.0015 | +0.0292 | +0.0398 | +2.281 | +0.0398 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 67 | +0.8211 [+0.671, +0.971] | +0.4836 | +0.5599 | +0.5231 | +17.476 | +0.3013 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 67 | +0.0329 [+0.030, +0.036] | +0.0198 | +0.0221 | +0.0208 | +1.167 | +0.0204 |
| RS|fau|NCE|cbramod|residual_aligned_random | 67 | +0.0427 [+0.040, +0.046] | +0.0338 | +0.0338 | +0.0240 | +1.326 | +0.0231 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 67 | +0.0430 [+0.040, +0.046] | +0.0310 | +0.0313 | +0.0253 | +1.410 | +0.0246 |
| RS|fau|NCE|reve|residual_aligned_random | 67 | +0.0479 [+0.043, +0.053] | +0.0351 | +0.0355 | +0.0272 | +1.500 | +0.0262 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 67 | +0.0388 [+0.036, +0.041] | +0.0258 | +0.0293 | +0.0235 | +1.311 | +0.0229 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 86 | +0.1174 [+0.104, +0.131] | +0.0026 | +0.0627 | +0.0891 | +5.100 | +0.0889 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 86 | +0.0493 [+0.040, +0.059] | -0.0008 | +0.0273 | +0.0374 | +2.149 | +0.0375 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 86 | +0.1086 [-0.057, +0.275] | +0.0189 | +0.0715 | +0.0733 | +2.052 | +0.0356 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 86 | +0.0201 [+0.015, +0.025] | -0.0003 | +0.0146 | +0.0121 | +0.696 | +0.0121 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 86 | +0.6155 [+0.511, +0.720] | +0.2403 | +0.3873 | +0.4213 | +18.068 | +0.3085 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 86 | +0.0340 [+0.031, +0.037] | -0.0075 | +0.0328 | +0.0082 | +0.471 | +0.0082 |
| RS|federici|NCE|cbramod|residual_aligned_random | 86 | +0.0281 [+0.025, +0.031] | -0.0150 | +0.0270 | +0.0074 | +0.432 | +0.0075 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 86 | +0.0217 [+0.019, +0.024] | -0.0074 | +0.0202 | +0.0063 | +0.367 | +0.0064 |
| RS|federici|NCE|reve|residual_aligned_random | 86 | +0.0325 [+0.030, +0.035] | -0.0097 | +0.0313 | +0.0080 | +0.468 | +0.0082 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 86 | +0.0226 [+0.019, +0.027] | -0.0019 | +0.0202 | +0.0078 | +0.453 | +0.0079 |

| configuration | readout | queries with rank change | mean |Δrank| | mean Δrank (− = better) | top-1 gained / lost | ΔR (base − RS) [95% CI] | Δ true-candidate z-score |
|---|---|---|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | unified | +0.821 | +8.553 | +0.847 | +0.0088 / +0.0092 | -0.0210 [-0.039, -0.003] | -0.0144 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | native | +0.778 | +6.879 | +0.868 | +0.0077 / +0.0094 | -0.0221 [-0.042, -0.002] | -0.0171 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | unified | +0.768 | +5.580 | +0.568 | +0.0052 / +0.0061 | -0.0161 [-0.028, -0.005] | -0.0100 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | native | +0.627 | +3.290 | +0.430 | +0.0040 / +0.0051 | -0.0088 [-0.017, -0.000] | -0.0100 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | unified | +0.667 | +2.079 | +0.018 | +0.0020 / +0.0021 | -0.0025 [-0.006, +0.001] | -0.0014 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | native | +0.568 | +1.385 | -0.010 | +0.0022 / +0.0017 | +0.0007 [-0.001, +0.002] | +0.0001 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | unified | +0.514 | +1.373 | -0.051 | +0.0014 / +0.0008 | +0.0018 [-0.000, +0.004] | +0.0012 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | native | +0.460 | +0.967 | -0.027 | +0.0013 / +0.0009 | +0.0013 [-0.000, +0.003] | +0.0005 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | unified | +0.915 | +11.807 | +2.589 | +0.0113 / +0.0156 | -0.0866 [-0.105, -0.069] | -0.0589 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | native | +0.871 | +7.396 | +2.101 | +0.0068 / +0.0098 | -0.0544 [-0.067, -0.042] | -0.0426 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | unified | +0.244 | +0.334 | -0.008 | +0.0001 / +0.0005 | +0.0004 [-0.000, +0.001] | +0.0002 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | native | +0.395 | +0.718 | -0.037 | +0.0025 / +0.0018 | +0.0025 [+0.001, +0.004] | +0.0009 |
| RS|dtu|NCE|cbramod|residual_aligned_random | unified | +0.258 | +0.362 | -0.004 | +0.0001 / +0.0005 | +0.0003 [-0.001, +0.001] | +0.0001 |
| RS|dtu|NCE|cbramod|residual_aligned_random | native | +0.392 | +0.692 | -0.035 | +0.0023 / +0.0010 | +0.0022 [+0.001, +0.004] | +0.0008 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | unified | +0.292 | +0.420 | +0.002 | +0.0005 / +0.0009 | +0.0002 [-0.001, +0.001] | +0.0000 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | native | +0.370 | +0.695 | -0.051 | +0.0026 / +0.0012 | +0.0029 [+0.001, +0.004] | +0.0010 |
| RS|dtu|NCE|reve|residual_aligned_random | unified | +0.208 | +0.272 | -0.004 | +0.0001 / +0.0005 | +0.0001 [-0.000, +0.001] | +0.0000 |
| RS|dtu|NCE|reve|residual_aligned_random | native | +0.372 | +0.655 | -0.040 | +0.0025 / +0.0013 | +0.0025 [+0.001, +0.004] | +0.0006 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | unified | +0.551 | +2.816 | -0.369 | +0.0065 / +0.0049 | +0.0158 [+0.006, +0.026] | +0.0080 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | native | +0.524 | +3.084 | -0.175 | +0.0110 / +0.0098 | +0.0125 [-0.001, +0.026] | +0.0030 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | unified | +0.468 | +1.431 | +0.031 | +0.0041 / +0.0041 | -0.0016 [-0.004, +0.001] | -0.0015 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | native | +0.365 | +1.040 | -0.009 | +0.0024 / +0.0024 | -0.0013 [-0.004, +0.001] | -0.0004 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | unified | +0.382 | +0.967 | -0.001 | +0.0022 / +0.0022 | -0.0005 [-0.002, +0.001] | -0.0000 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | native | +0.291 | +0.602 | +0.013 | +0.0016 / +0.0013 | -0.0012 [-0.003, +0.001] | -0.0008 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | unified | +0.359 | +0.559 | -0.013 | +0.0014 / +0.0011 | +0.0000 [-0.001, +0.001] | +0.0000 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | native | +0.274 | +0.381 | -0.004 | +0.0010 / +0.0007 | -0.0002 [-0.001, +0.000] | -0.0002 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | unified | +0.353 | +0.522 | +0.005 | +0.0009 / +0.0012 | -0.0003 [-0.001, +0.000] | -0.0003 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | native | +0.266 | +0.351 | +0.002 | +0.0006 / +0.0007 | -0.0003 [-0.001, +0.000] | -0.0004 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | unified | +0.793 | +6.322 | +0.655 | +0.0132 / +0.0164 | -0.0185 [-0.032, -0.005] | -0.0268 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | native | +0.716 | +3.380 | +0.622 | +0.0051 / +0.0090 | -0.0211 [-0.029, -0.013] | -0.0230 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | unified | +0.195 | +0.247 | +0.010 | +0.0005 / +0.0010 | -0.0004 [-0.001, +0.000] | -0.0003 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | native | +0.443 | +0.749 | +0.010 | +0.0034 / +0.0031 | -0.0044 [-0.006, -0.003] | +0.0004 |
| RS|fau|NCE|cbramod|residual_aligned_random | unified | +0.197 | +0.254 | +0.007 | +0.0004 / +0.0007 | -0.0000 [-0.001, +0.001] | -0.0000 |
| RS|fau|NCE|cbramod|residual_aligned_random | native | +0.421 | +0.705 | +0.011 | +0.0031 / +0.0028 | -0.0034 [-0.005, -0.002] | +0.0004 |
| RS|fau|NCE|reve|residual_aligned_pretrained | unified | +0.194 | +0.250 | -0.003 | +0.0004 / +0.0007 | +0.0004 [-0.000, +0.001] | +0.0003 |
| RS|fau|NCE|reve|residual_aligned_pretrained | native | +0.389 | +0.614 | +0.001 | +0.0028 / +0.0022 | -0.0027 [-0.004, -0.001] | +0.0005 |
| RS|fau|NCE|reve|residual_aligned_random | unified | +0.182 | +0.235 | +0.012 | +0.0007 / +0.0006 | -0.0002 [-0.002, +0.001] | -0.0002 |
| RS|fau|NCE|reve|residual_aligned_random | native | +0.432 | +0.710 | +0.008 | +0.0031 / +0.0031 | -0.0043 [-0.006, -0.003] | +0.0005 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | unified | +0.578 | +2.083 | -0.123 | +0.0058 / +0.0045 | +0.0066 [+0.001, +0.012] | +0.0047 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | native | +0.582 | +1.743 | -0.078 | +0.0070 / +0.0066 | +0.0039 [-0.005, +0.013] | +0.0038 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | unified | +0.671 | +2.870 | -0.052 | +0.0016 / +0.0006 | +0.0002 [-0.001, +0.002] | -0.0000 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | native | +0.459 | +0.827 | +0.023 | +0.0000 / +0.0000 | +0.0000 [-0.000, +0.000] | +0.0000 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | unified | +0.461 | +1.096 | -0.079 | +0.0013 / +0.0003 | +0.0001 [-0.004, +0.004] | +0.0004 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | native | +0.247 | +0.363 | -0.022 | +0.0000 / +0.0000 | +0.0000 [-0.000, +0.000] | +0.0002 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | unified | +0.501 | +1.490 | +0.060 | +0.0013 / +0.0000 | -0.0005 [-0.004, +0.003] | -0.0010 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | native | +0.295 | +0.472 | +0.002 | +0.0000 / +0.0000 | -0.0000 [-0.000, -0.000] | -0.0005 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | unified | +0.249 | +0.471 | -0.004 | +0.0000 / +0.0000 | -0.0001 [-0.004, +0.004] | +0.0000 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | native | +0.115 | +0.143 | +0.001 | +0.0000 / +0.0000 | +0.0000 [-0.000, +0.000] | +0.0000 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | unified | +0.924 | +11.357 | +0.277 | +0.0052 / +0.0032 | -0.0021 [-0.010, +0.006] | -0.0022 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | native | +0.806 | +3.291 | +0.189 | +0.0000 / +0.0004 | -0.0001 [-0.001, +0.001] | -0.0044 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | unified | +0.247 | +1.242 | -0.140 | +0.0008 / +0.0004 | +0.0009 [-0.000, +0.002] | +0.0021 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | native | +0.696 | +3.241 | -0.104 | +0.0013 / +0.0016 | +0.0023 [-0.001, +0.005] | +0.0025 |
| RS|federici|NCE|cbramod|residual_aligned_random | unified | +0.146 | +0.165 | -0.019 | +0.0000 / +0.0000 | +0.0000 [-0.000, +0.000] | +0.0000 |
| RS|federici|NCE|cbramod|residual_aligned_random | native | +0.717 | +4.017 | -0.216 | +0.0013 / +0.0016 | +0.0036 [-0.000, +0.007] | +0.0045 |
| RS|federici|NCE|reve|residual_aligned_pretrained | unified | +0.350 | +0.945 | -0.164 | +0.0000 / +0.0006 | +0.0009 [+0.000, +0.002] | +0.0019 |
| RS|federici|NCE|reve|residual_aligned_pretrained | native | +0.835 | +4.396 | -0.105 | +0.0024 / +0.0016 | +0.0027 [-0.001, +0.006] | +0.0030 |
| RS|federici|NCE|reve|residual_aligned_random | unified | +0.129 | +0.141 | -0.010 | +0.0000 / +0.0000 | +0.0000 [-0.000, +0.000] | +0.0001 |
| RS|federici|NCE|reve|residual_aligned_random | native | +0.764 | +3.964 | -0.248 | +0.0013 / +0.0016 | +0.0035 [-0.000, +0.007] | +0.0045 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | unified | +0.554 | +2.767 | -0.139 | +0.0003 / +0.0006 | +0.0014 [+0.000, +0.003] | +0.0027 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | native | +0.861 | +4.505 | -0.412 | +0.0019 / +0.0024 | +0.0045 [+0.001, +0.008] | +0.0050 |

| configuration | unified prediction: relative difference | unified prediction: z-correlation base~RS | native prediction relative difference |
|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | +0.2665 | +0.9215 | +0.2723 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | +0.1737 | +0.9610 | +0.1602 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | +0.0605 | +0.9956 | +0.0541 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | +0.0429 | +0.9982 | +0.0418 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | +0.3355 | +0.8842 | +0.2880 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | +0.0109 | +0.9999 | +0.0248 |
| RS|dtu|NCE|cbramod|residual_aligned_random | +0.0123 | +0.9999 | +0.0232 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | +0.0130 | +0.9999 | +0.0263 |
| RS|dtu|NCE|reve|residual_aligned_random | +0.0089 | +1.0000 | +0.0207 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | +0.1061 | +0.9938 | +0.0284 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | +0.0730 | +0.9896 | +0.0621 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | +0.0467 | +0.9960 | +0.0372 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | +0.0250 | +0.9994 | +0.0207 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | +0.0257 | +0.9995 | +0.0212 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | +0.2914 | +0.9058 | +0.2144 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | +0.0138 | +0.9999 | +0.0204 |
| RS|fau|NCE|cbramod|residual_aligned_random | +0.0120 | +0.9999 | +0.0231 |
| RS|fau|NCE|reve|residual_aligned_pretrained | +0.0115 | +0.9996 | +0.0246 |
| RS|fau|NCE|reve|residual_aligned_random | +0.0126 | +0.9998 | +0.0262 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | +0.1213 | +0.9863 | +0.0229 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | +0.0742 | +0.9974 | +0.0201 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | +0.0278 | +0.9994 | +0.0083 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | +0.0338 | +0.9983 | +0.0089 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | +0.0110 | +0.9999 | +0.0029 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | +0.2827 | +0.9547 | +0.0823 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | +0.0752 | +0.9975 | +0.0082 |
| RS|federici|NCE|cbramod|residual_aligned_random | +0.0073 | +1.0000 | +0.0075 |
| RS|federici|NCE|reve|residual_aligned_pretrained | +0.0709 | +0.9989 | +0.0064 |
| RS|federici|NCE|reve|residual_aligned_random | +0.0054 | +1.0000 | +0.0082 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | +0.1205 | +0.9963 | +0.0079 |

Native prediction difference: NCE scores u itself, so it equals the post-normalisation change; CS_SINGLE scores the native ridge prediction B_nat(u), whose relative change is reported.

Development vs outer-test anchors of the same units (unit means; development = group-0 segments, training participants of the base, 8 anchors per segment; test = all grid anchors):

| configuration | units | ‖r‖/‖u‖ dev / test | angle dev / test (deg) | post-norm change dev / test |
|---|---|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 1.0656 / 1.1041 | 18.025 / 18.317 | 0.3005 / 0.3043 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0.2464 / 0.2527 | 9.854 / 10.192 | 0.1689 / 0.1742 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0.1108 / 0.1122 | 3.882 / 3.890 | 0.0675 / 0.0677 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 9 | 0.1010 / 0.1010 | 3.411 / 3.425 | 0.0595 / 0.0597 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 1.2572 / 1.3549 | 20.720 / 20.883 | 0.3546 / 0.3574 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 0.0418 / 0.0418 | 1.372 / 1.382 | 0.0239 / 0.0241 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 0.0414 / 0.0413 | 1.286 / 1.292 | 0.0224 / 0.0226 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 0.0475 / 0.0473 | 1.463 / 1.468 | 0.0255 / 0.0256 |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 0.0339 / 0.0339 | 1.170 / 1.179 | 0.0204 / 0.0206 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 7 | 0.0489 / 0.0487 | 2.308 / 2.289 | 0.0403 / 0.0399 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 9 | 0.1457 / 0.1401 | 4.759 / 4.725 | 0.0824 / 0.0819 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 9 | 0.0893 / 0.0873 | 3.454 / 3.529 | 0.0601 / 0.0614 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 9 | 0.0481 / 0.0480 | 1.918 / 1.902 | 0.0335 / 0.0332 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 9 | 0.0614 / 0.0612 | 2.685 / 2.687 | 0.0468 / 0.0469 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 9 | 0.8815 / 0.8827 | 18.847 / 19.060 | 0.3251 / 0.3287 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 0.0337 / 0.0337 | 1.171 / 1.167 | 0.0204 / 0.0204 |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 0.0434 / 0.0434 | 1.332 / 1.329 | 0.0232 / 0.0232 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 0.0438 / 0.0438 | 1.414 / 1.411 | 0.0247 / 0.0246 |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 0.0495 / 0.0495 | 1.520 / 1.520 | 0.0265 / 0.0265 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 9 | 0.0428 / 0.0425 | 1.448 / 1.427 | 0.0253 / 0.0249 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 4 | 0.1493 / 0.1454 | 6.470 / 6.340 | 0.1128 / 0.1105 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 4 | 0.0597 / 0.0611 | 2.596 / 2.701 | 0.0453 / 0.0471 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 4 | 0.1102 / 0.3827 | 2.535 / 5.457 | 0.0439 / 0.0892 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 2 | 0.0496 / 0.0496 | 1.696 / 1.747 | 0.0296 / 0.0305 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0.5907 / 0.6111 | 17.637 / 18.726 | 0.3012 / 0.3196 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 0.0347 / 0.0347 | 0.468 / 0.468 | 0.0082 / 0.0082 |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 0.0273 / 0.0273 | 0.425 / 0.426 | 0.0074 / 0.0074 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 0.0209 / 0.0209 | 0.364 / 0.364 | 0.0063 / 0.0064 |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 0.0316 / 0.0316 | 0.463 / 0.464 | 0.0081 / 0.0081 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 0.0238 / 0.0239 | 0.449 / 0.454 | 0.0078 / 0.0079 |

**Engineering checks — v2 outputs (merged when full and reproducing)**, `results/auditory_alignment_v3/aln34/complement_function/units_v2/`. Rule: max |Δ| ≤ 1e-3 on per-participant log-loss and rank_pct (both readouts, both records) and on both saved development risks; top-1 / top-5 / MRR can move by 1/n_queries on a single near-tie flip and are reported, not bounded. The tolerance is for float order, not a performance gate. Tiny and development-only runs are not comparable to the records by design; the development-side layer values (dev ‖r‖/‖u‖ · angle · post-norm change, unit means over the development anchors) are shown for every output and are merged into the configuration summaries only through reproducing full runs.

| output | kind | device | seconds | bounded max |Δ| | all-metric max |Δ| base / RS | dev risk |Δ| selected / epoch 0 | u/r split vs forward | dev ‖r‖/‖u‖ · angle (deg) · post-norm change | peak RSS MB | code sha256 | reproduces |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALN3X_0150eb06b7558743.json (RS|federici|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 136.4 | 3.6e-07 | 3.1e-07 / 3.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0129 · +0.319 · +0.0056 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_025e0931cfe9c2e9.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 33.2 | 1.5e-08 | 1.5e-08 / 1.2e-09 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +2.3605 · +28.455 · +0.4825 | 11667 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_030dd347f750acc1.json (RS|federici|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 140.7 | 4.6e-07 | 4.6e-07 / 3.8e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0403 · +0.709 · +0.0124 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_03586fa3ea62f100.json (RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | cpu | 104.7 | 7.0e-07 | 7.0e-07 / 7.8e-08 | 9.5e-07 / 9.5e-07 | 0.0e+00 | +1.4738 · +30.108 · +0.5124 | 2203 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_03ae54a8f9e4f921.json (RS|federici|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 143.2 | 3.9e-04 | 1.0e-07 / 3.9e-04 | 3.3e-06 / 2.9e-06 | 0.0e+00 | +0.0408 · +1.456 · +0.0254 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_04a301cd3fb68a85.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 181.8 | 2.8e-07 | 2.6e-07 / 2.8e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0322 · +1.263 · +0.0220 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_04ae9707a8a6a863.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 52.4 | 1.2e-04 | 1.4e-08 / 1.1e-02 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0536 · +2.086 · +0.0364 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_055b40c731b388bc.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 60.0 | 1.7e-08 | 7.1e-09 / 1.7e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0246 · +1.158 · +0.0202 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_05b5791a5987ebd9.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 185.1 | 3.6e-04 | 2.1e-07 / 1.8e-03 | 1.7e-05 / 1.5e-05 | 0.0e+00 | +0.0560 · +1.429 · +0.0249 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_07e8b3d158408971.json (RS|federici|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 137.5 | 3.8e-07 | 3.1e-07 / 3.8e-07 | 9.5e-07 / 0.0e+00 | 0.0e+00 | +0.0153 · +0.375 · +0.0066 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_09346fff29d534e4.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 35.0 | 5.1e-07 | 4.2e-08 / 5.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +1.1096 · +18.670 · +0.3202 | 11646 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_0ad1931c0529dfc1.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 227.8 | 8.2e-05 | 2.1e-08 / 8.2e-05 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.0950 · +4.602 · +0.0802 | 12110 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_0b65fe1d80952bd2.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 70.0 | 5.2e-07 | 5.2e-07 / 3.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0297 · +0.861 · +0.0150 | 11923 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_0eea1953f258f1c8.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 30.9 | 1.5e-07 | 1.2e-07 / 1.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0683 · +1.483 · +0.0259 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_0f171ebf5d0f5036.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 37.6 | 1.0e-08 | 1.0e-08 / 7.7e-09 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1192 · +5.848 · +0.1019 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_0f54b46f2e0c483f.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 55.7 | 3.0e-07 | 2.1e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0560 · +1.438 · +0.0251 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_10ba16de1e174fa3.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 55.8 | 7.5e-05 | 7.1e-09 / 7.2e-04 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.0244 · +1.154 · +0.0201 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_125af94e1a1dc34f.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 67.5 | 2.2e-08 | 2.1e-08 / 2.2e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0758 · +2.954 · +0.0515 | 11909 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_13379c7b29e678cb.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 35.5 | 1.4e-08 | 1.3e-08 / 1.4e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.8883 · +20.610 · +0.3563 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_155d9c35388abdcc.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 211.9 | 1.5e-04 | 2.6e-08 / 1.5e-04 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0482 · +1.783 · +0.0311 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_173c3c1b6d711141.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 256.0 | 5.2e-07 | 5.2e-07 / 2.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0272 · +0.838 · +0.0146 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_18d86364bd045826.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 269.5 | 1.1e-06 | 3.8e-07 / 1.1e-06 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0044 · +0.177 · +0.0031 | 2190 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_1c22b5dd7b26f286.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 208.1 | 2.2e-04 | 2.0e-07 / 2.2e-04 | 3.3e-06 / 2.9e-06 | 0.0e+00 | +0.0516 · +1.244 · +0.0217 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_1d48e8941571c920.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 55.9 | 2.4e-04 | 2.6e-07 / 2.4e-04 | 7.6e-06 / 7.6e-06 | 0.0e+00 | +0.0334 · +1.350 · +0.0236 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_1e52f576224bd773.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 184.0 | 2.4e-04 | 2.1e-07 / 5.4e-04 | 1.6e-05 / 1.5e-05 | 0.0e+00 | +0.0564 · +1.421 · +0.0248 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_1e8815d991df83f3.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 186.9 | 1.2e-08 | 7.1e-09 / 1.2e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0244 · +1.153 · +0.0201 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_2052d82b0c1fadcd.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 70.0 | 5.1e-08 | 4.2e-08 / 5.1e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0323 · +1.130 · +0.0197 | 11880 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_208c75ebbc607047.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 212.6 | 1.5e-04 | 1.2e-07 / 8.6e-03 | 7.2e-06 / 7.6e-06 | 0.0e+00 | +0.0699 · +1.633 · +0.0285 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_20c9a54ea0a04714.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 35.4 | 7.5e-05 | 2.6e-08 / 7.5e-05 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.7792 · +20.880 · +0.3607 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_21a236f9a412aeeb.json (RS|federici|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 32.4 | 3.9e-04 | 3.1e-07 / 3.9e-04 | 8.1e-06 / 5.7e-06 | 0.0e+00 | +0.0157 · +0.270 · +0.0047 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_2234673f984e9746.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 55.8 | 3.5e-07 | 3.2e-07 / 3.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0164 · +0.741 · +0.0129 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_23d5b6458a76f0da.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 32.1 | 4.0e-06 | 4.3e-07 / 4.0e-06 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0362 · +1.967 · +0.0343 | 11681 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_244f1b1ab8813eef.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 35.9 | 8.6e-08 | 4.0e-08 / 8.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.4858 · +13.222 · +0.2298 | 11637 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_24dc4921e665c00f.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 215.0 | 2.0e-08 | 2.0e-08 / 6.5e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0592 · +2.299 · +0.0401 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_26a666ffcd1137c5.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 67.1 | 6.9e-08 | 3.4e-08 / 6.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1113 · +4.853 · +0.0847 | 11883 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_271dffae89bf6759.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 227.2 | 2.4e-04 | 1.6e-07 / 2.4e-04 | 1.7e-05 / 1.8e-05 | 0.0e+00 | +0.0262 · +1.015 · +0.0177 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_273cb9bd9323c25c.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 184.0 | 2.1e-07 | 2.0e-07 / 2.1e-07 | 4.8e-07 / 9.5e-07 | 0.0e+00 | +0.0671 · +1.444 · +0.0252 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_276d4e240c82c857.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 208.2 | 2.2e-04 | 1.9e-07 / 8.6e-03 | 1.9e-06 / 1.4e-06 | 0.0e+00 | +0.0228 · +1.073 · +0.0187 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_296731e3fae9993f.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 182.8 | 1.1e-08 | 7.1e-09 / 1.1e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0338 · +1.862 · +0.0325 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_29fce9a4e2f3bba6.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 251.5 | 4.3e-07 | 4.3e-07 / 3.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0610 · +1.642 · +0.0287 | 12148 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_2ad1c08cf8ba2e69.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 64.7 | 1.2e-04 | 1.8e-08 / 1.2e-04 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0367 · +1.608 · +0.0281 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_2b0bb34201a501c8.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 187.7 | 2.4e-08 | 2.4e-08 / 1.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0653 · +2.365 · +0.0413 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_2ca06e5127b26ba8.json (RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | cpu | 103.1 | 1.3e-04 | 9.6e-08 / 1.3e-04 | 9.5e-07 / 9.5e-07 | 0.0e+00 | +0.1743 · +8.417 · +0.1463 | 2213 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_32e623eb8a92dd5f.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.0 | 3.0e-04 | 1.9e-07 / 1.5e-03 | 2.4e-06 / 1.4e-06 | 0.0e+00 | +0.0486 · +1.610 · +0.0281 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_344cef4fc9c6707a.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 69.0 | 3.0e-07 | 3.0e-07 / 2.6e-07 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0465 · +1.432 · +0.0250 | 11740 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_34b101ed999a6297.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 210.9 | 2.2e-04 | 1.2e-07 / 2.2e-04 | 8.1e-06 / 8.1e-06 | 0.0e+00 | +0.0543 · +1.245 · +0.0217 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_352bb03800b071e8.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 60.2 | 2.2e-07 | 1.2e-07 / 2.2e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0542 · +1.195 · +0.0209 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_3677f4b427f5ad4d.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 64.7 | 1.8e-07 | 1.8e-07 / 2.6e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0295 · +0.910 · +0.0159 | 11944 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_36bb8b59a1179a2e.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 97.9 | 5.2e-07 | 5.2e-07 / 3.4e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0305 · +0.860 · +0.0150 | 10747 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_376a4cc6e6b7dd13.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 30.9 | 1.7e-04 | 2.0e-07 / 1.7e-04 | 4.8e-07 / 2.9e-06 | 0.0e+00 | +0.0372 · +1.173 · +0.0205 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_37a7e8f2c2fc5872.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 72.2 | 5.9e-08 | 5.3e-08 / 5.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.3113 · +14.477 · +0.2518 | 11736 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_3d84d0391cfd79dc.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 62.8 | 1.5e-04 | 1.6e-07 / 1.5e-04 | 4.8e-06 / 5.2e-06 | 0.0e+00 | +0.0198 · +1.028 · +0.0179 | 11940 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_3d9055227c7db8c0.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 232.2 | 3.5e-08 | 3.3e-08 / 3.5e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0852 · +2.694 · +0.0470 | 12127 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_3e945ae4a925a60f.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 63.1 | 2.2e-04 | 2.0e-08 / 2.2e-04 | 1.9e-06 / 2.4e-06 | 0.0e+00 | +0.3109 · +13.760 · +0.2393 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_412f63a398a5d0ab.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 59.9 | 1.1e-04 | 1.2e-07 / 8.6e-03 | 6.2e-06 / 8.1e-06 | 0.0e+00 | +0.0384 · +0.922 · +0.0161 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_42057c2a09ce8ee9.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 261.5 | 5.6e-07 | 5.8e-08 / 5.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0869 · +2.054 · +0.0352 | 12104 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_44d14ac25c75d739.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 233.0 | 3.1e-07 | 1.6e-07 / 3.1e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0390 · +1.389 · +0.0242 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_456a4005e9846938.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 50.5 | 2.7e-04 | 2.7e-07 / 1.8e-03 | 2.4e-05 / 2.2e-05 | 0.0e+00 | +0.0322 · +0.789 · +0.0138 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4684ec0c6f933730.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 68.0 | 7.3e-08 | 3.3e-08 / 7.3e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.7570 · +24.588 · +0.4100 | 11888 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_478816e2f36324f6.json (RS|federici|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 138.8 | 3.8e-07 | 3.8e-07 / 0.0e+00 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0467 · +0.467 · +0.0082 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_47bef4e37c454976.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 56.5 | 2.4e-08 | 2.4e-08 / 1.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0652 · +2.365 · +0.0413 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_47f9daf0bb3ce036.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 39.2 | 1.9e-04 | 2.3e-08 / 1.9e-04 | 2.9e-06 / 3.8e-06 | 0.0e+00 | +0.1634 · +6.986 · +0.1217 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_490cb6494d28bdf1.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 183.2 | 1.8e-08 | 1.8e-08 / 1.2e-08 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0406 · +1.628 · +0.0284 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_499ed8410a7788d8.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 66.5 | 1.3e-08 | 1.3e-08 / 8.3e-09 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0300 · +1.223 · +0.0214 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4b43b00cfeeaba00.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 66.5 | 2.0e-08 | 2.0e-08 / 1.4e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.3243 · +13.668 · +0.2377 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4bc5bc8db84fb0fa.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 65.4 | 4.3e-07 | 4.3e-07 / 2.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0257 · +1.277 · +0.0223 | 11934 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4cf9ddd48a66fe21.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 59.8 | 1.8e-04 | 4.2e-07 / 8.6e-03 | 1.7e-05 / 2.1e-05 | 0.0e+00 | +0.0175 · +0.941 · +0.0164 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4e5e290e34c0afce.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 181.6 | 2.4e-04 | 3.2e-07 / 9.1e-04 | 4.8e-06 / 2.9e-06 | 0.0e+00 | +0.0354 · +1.119 · +0.0195 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_4fff04643cf1e3d7.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 66.9 | 8.1e-05 | 5.1e-08 / 8.1e-05 | 0.0e+00 / 4.8e-04 | 0.0e+00 | +0.2749 · +11.680 · +0.2033 | 11916 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5059dc8e2b42d8fc.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 59.5 | 2.0e-07 | 2.0e-07 / 1.8e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0454 · +1.169 · +0.0204 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_507e307c45561e2b.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 28.5 | 1.8e-04 | 2.1e-07 / 5.4e-04 | 1.6e-05 / 1.5e-05 | 0.0e+00 | +0.0295 · +1.000 · +0.0175 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_515a59d960b00e9f.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 67.0 | 2.7e-07 | 2.7e-07 / 2.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1177 · +2.985 · +0.0521 | 11930 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_51cdec7aea7e09aa.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 59.9 | 1.2e-04 | 1.8e-08 / 1.2e-04 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0850 · +3.877 · +0.0676 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_526b5aa9e5c8193f.json (RS|federici|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 142.0 | 1.6e-08 | 1.4e-08 / 1.6e-08 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.0583 · +1.935 · +0.0338 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_544007987cb9cc3f.dev_only.json (RS|federici|NCE|cbramod|residual_aligned_random) | dev_only | cpu | 87.8 | – | – / – | 1.4e-06 / 4.8e-07 | 0.0e+00 | +0.0107 · +0.300 · +0.0052 | 2209 | be2107d36af9 (evaluator, snapshot) | n/a |
| ALN3X_544007987cb9cc3f.json (RS|federici|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 32.3 | 4.0e-07 | 4.0e-07 / 4.8e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0107 · +0.300 · +0.0052 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5526b7f14cbfb4e6.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 41.2 | 1.9e-04 | 1.4e-07 / 1.9e-04 | 9.5e-07 / 9.5e-07 | 0.0e+00 | +0.1503 · +7.944 · +0.1385 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5702d5df3401bff0.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 259.4 | 3.9e-07 | 3.0e-07 / 3.9e-07 | 4.8e-07 / 4.8e-07 | 0.0e+00 | +0.0623 · +1.749 · +0.0305 | 12150 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_57397b73b004b163.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 183.8 | 3.6e-04 | 3.2e-07 / 3.6e-04 | 3.8e-06 / 2.9e-06 | 0.0e+00 | +0.0416 · +1.741 · +0.0304 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_57ac4496bc754dd8.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 233.8 | 4.5e-08 | 4.3e-08 / 4.5e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0684 · +2.641 · +0.0461 | 12132 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_57adcd7f2c0948df.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 224.5 | 3.1e-07 | 1.6e-07 / 3.1e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0181 · +0.933 · +0.0163 | 12156 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_57d6b53bd33edc06.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 210.8 | 7.5e-05 | 1.3e-08 / 7.5e-05 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0558 · +2.123 · +0.0370 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_58a1749353d7b769.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 164.6 | 1.6e-08 | 1.4e-08 / 1.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1757 · +9.176 · +0.1600 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_594d76a7d27e97b3.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 228.4 | 7.5e-05 | 1.5e-08 / 7.5e-05 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.2192 · +7.335 · +0.1276 | 12280 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_59b881c86fef5638.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 181.7 | 3.6e-07 | 3.6e-07 / 3.9e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0423 · +2.414 · +0.0421 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_59bdf028cb7a8a1f.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.6 | 4.2e-07 | 4.2e-07 / 2.3e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0365 · +1.239 · +0.0216 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_59f53c7a7389fdda.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 70.8 | 5.5e-08 | 4.2e-08 / 5.5e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0295 · +1.068 · +0.0186 | 11902 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5a2c00065b48c6a4.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 231.9 | 4.7e-08 | 3.4e-08 / 4.7e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0659 · +2.518 · +0.0439 | 12121 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5ab8d80774f53f70.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 60.4 | 4.2e-07 | 4.2e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0176 · +0.947 · +0.0165 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5be5183794592a92.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.9 | 1.8e-04 | 2.7e-07 / 1.8e-04 | 2.5e-05 / 2.2e-05 | 0.0e+00 | +0.0833 · +3.193 · +0.0557 | 11677 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5d1b8587585cac25.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 210.6 | 7.5e-05 | 1.4e-08 / 7.5e-05 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0172 · +0.851 · +0.0149 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5d3e101eaaa3ad13.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 233.5 | 3.6e-08 | 3.3e-08 / 3.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0853 · +2.695 · +0.0470 | 12274 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5e4f4d7bb12d07e6.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 55.3 | 1.4e-07 | 2.5e-08 / 1.4e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.6479 · +15.237 · +0.2615 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_5f7897b91170e3a4.json (RS|federici|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 141.1 | 1.9e-04 | 1.4e-08 / 1.9e-04 | 0.0e+00 / 1.9e-06 | 0.0e+00 | +0.0915 · +3.015 · +0.0526 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6101fe58340cd015.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 35.4 | 5.8e-08 | 5.8e-08 / 1.6e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.4427 · +12.769 · +0.2218 | 11652 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6186f58d2698ee2b.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.3 | 2.4e-04 | 1.6e-07 / 2.4e-04 | 2.1e-05 / 1.8e-05 | 0.0e+00 | +0.0447 · +2.246 · +0.0392 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_62213d18fbbcce40.json (RS|federici|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 140.4 | 1.9e-04 | 2.3e-08 / 2.5e-04 | 2.9e-06 / 3.8e-06 | 0.0e+00 | +0.0174 · +0.981 · +0.0171 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_624c731c845bd7c0.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 212.0 | 2.0e-07 | 2.0e-07 / 9.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0447 · +1.134 · +0.0198 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6389fd1cd5085757.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 66.9 | 1.5e-08 | 1.5e-08 / 9.4e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.8231 · +32.923 · +0.5500 | 11917 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_63f00ab52e1f2f87.json (RS|federici|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 33.1 | 4.6e-07 | 4.6e-07 / 4.6e-07 | 9.5e-07 / 0.0e+00 | 0.0e+00 | +0.0407 · +0.741 · +0.0129 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_64631148f7c0b4ad.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 183.0 | 2.5e-08 | 2.5e-08 / 1.8e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0448 · +1.683 · +0.0294 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_658d67548cf7fa2e.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 71.0 | 3.0e-07 | 3.0e-07 / 3.0e-07 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0619 · +1.741 · +0.0304 | 11931 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_66030862c7c7a5ea.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 36.8 | 1.0e-07 | 1.0e-07 / 0.0e+00 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1643 · +5.118 · +0.0892 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_66bddf767f68c0d1.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 68.6 | 4.3e-07 | 4.3e-07 / 1.5e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0600 · +1.530 · +0.0267 | 11948 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_66e6e5c3f0ea729e.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 28.3 | 1.9e-04 | 2.6e-07 / 1.9e-04 | 5.7e-06 / 7.6e-06 | 0.0e+00 | +0.0147 · +0.749 · +0.0131 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6b94fadac4e59212.json (RS|federici|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 141.4 | 3.9e-04 | 3.1e-07 / 3.9e-04 | 9.1e-06 / 9.1e-06 | 0.0e+00 | +0.0377 · +0.390 · +0.0068 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6bb801c9730ca819.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 109.4 | 3.9e-04 | 4.7e-07 / 5.1e-04 | 2.9e-06 / 4.3e-06 | 0.0e+00 | +0.0530 · +0.469 · +0.0082 | 2191 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6cd777f0415e91d7.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 63.4 | 1.5e-08 | 1.4e-08 / 1.5e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0226 · +1.224 · +0.0214 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6d412b6de40d9b23.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 30.9 | 2.4e-08 | 2.4e-08 / 0.0e+00 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +2.4742 · +26.750 · +0.4581 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6d7e49d21a3a0cf6.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.5 | 2.1e-07 | 5.1e-08 / 2.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.3494 · +12.109 · +0.2106 | 11664 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6dee7bccba8be1d6.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 52.7 | 2.0e-07 | 2.0e-07 / 8.0e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0724 · +1.560 · +0.0272 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6e21279e2353ea01.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 73.8 | 4.0e-08 | 4.0e-08 / 1.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0300 · +1.407 · +0.0245 | 11901 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6e2e0ba8cd20ba24.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 66.4 | 2.7e-07 | 2.7e-07 / 2.4e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1198 · +2.973 · +0.0519 | 11950 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6e394c1e24387069.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 33.5 | 3.3e-06 | 4.3e-08 / 3.3e-06 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +1.2673 · +28.286 · +0.4800 | 11671 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_6eaa8d2dbc2a486a.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 59.2 | 1.6e-07 | 1.6e-07 / 1.4e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0219 · +1.152 · +0.0201 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_72d55bfa49208d06.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 224.6 | 5.5e-07 | 1.6e-07 / 5.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0358 · +1.164 · +0.0203 | 12142 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_72e3915442273a89.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 215.2 | 3.0e-04 | 2.6e-08 / 8.6e-03 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0330 · +1.253 · +0.0219 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7473fec7dcca4106.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 133.8 | 1.3e-04 | 3.2e-07 / 1.3e-04 | 0.0e+00 / 1.4e-06 | 0.0e+00 | +0.0075 · +0.336 · +0.0059 | 2199 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_764fb4f8a97de3c2.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 208.1 | 4.2e-07 | 4.2e-07 / 2.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0174 · +0.931 · +0.0163 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_76bb4b79a4a7f71d.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 231.5 | 1.8e-07 | 1.8e-07 / 3.0e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0502 · +1.270 · +0.0222 | 12146 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_77fcfc45afed19d1.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 249.1 | 4.3e-07 | 4.3e-07 / 3.5e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0275 · +0.757 · +0.0132 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_79b02526d4f8b18a.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 40.6 | 1.1e-07 | 5.3e-08 / 1.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +1.0093 · +15.245 · +0.2639 | 10747 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7aba72ee017e0c3d.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 60.5 | 4.2e-07 | 1.6e-07 / 4.2e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0263 · +1.013 · +0.0177 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7b0e0ea794289c04.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 257.1 | 5.3e-08 | 5.3e-08 / 4.8e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1829 · +4.900 · +0.0855 | 12281 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7b119a1d5834881f.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 300.1 | 4.3e-07 | 4.3e-07 / 3.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0289 · +1.412 · +0.0246 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7b7e974cc8ec45a6.json (RS|federici|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 137.5 | 3.8e-07 | 3.8e-07 / 3.8e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0276 · +0.263 · +0.0046 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7cd5a67042395c7a.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 162.7 | 2.7e-04 | 2.7e-07 / 1.8e-03 | 2.5e-05 / 2.2e-05 | 0.0e+00 | +0.1061 · +2.394 · +0.0418 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_7f47352e9e834da3.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 165.6 | 1.2e-04 | 1.4e-08 / 1.2e-04 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0540 · +2.100 · +0.0366 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8032ca8a27a5555d.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 67.2 | 4.2e-08 | 3.3e-08 / 4.2e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0751 · +4.129 · +0.0720 | 11913 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_80aa1fea26db9714.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 67.3 | 7.5e-05 | 1.5e-08 / 1.9e-04 | 4.8e-07 / 9.5e-07 | 0.0e+00 | +1.3733 · +32.994 · +0.5522 | 11895 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_83798d5d4c69843e.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 232.1 | 4.5e-07 | 4.3e-07 / 4.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0290 · +1.425 · +0.0249 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_861bff15d9107bcf.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 273.9 | 7.2e-08 | 5.3e-08 / 7.2e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1955 · +6.440 · +0.1123 | 12022 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8634740a76fbb666.json (RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | cpu | 141.3 | 2.6e-04 | 2.7e-08 / 2.6e-04 | 9.5e-07 / 0.0e+00 | 0.0e+00 | +0.3545 · +17.095 · +0.2956 | 1935 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_868ac7697f2282db.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 36.7 | 1.0e-07 | 1.0e-07 / 0.0e+00 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0387 · +1.406 · +0.0245 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_86ceb414eb57e340.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 32.2 | 4.1e-06 | 4.0e-07 / 4.1e-06 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0410 · +2.146 · +0.0375 | 11684 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_878cddd92dd6901e.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 74.9 | 1.2e-07 | 5.8e-08 / 1.2e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.4379 · +16.341 · +0.2816 | 11906 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_879c25079fb35d1e.json (RS|federici|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 140.9 | 4.6e-07 | 4.6e-07 / 4.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0407 · +0.708 · +0.0124 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_895b887bb017ba18.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 56.1 | 2.0e-07 | 2.0e-07 / 1.4e-07 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.0670 · +1.602 · +0.0280 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8a341caf3c68d8e4.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 225.1 | 4.0e-07 | 4.0e-07 / 1.0e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0201 · +1.138 · +0.0199 | 12140 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8c879ed72aaa5e9e.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 36.4 | 3.9e-04 | 1.4e-08 / 3.9e-04 | 0.0e+00 / 1.9e-06 | 0.0e+00 | +0.1191 · +5.832 · +0.1017 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8dd7318a6852848b.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 233.1 | 6.0e-08 | 3.4e-08 / 6.0e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0625 · +2.560 · +0.0446 | 12274 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_8f571c0b6d2f7ab6.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 56.2 | 3.3e-07 | 2.6e-07 / 3.3e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0333 · +1.350 · +0.0236 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_90f0cedc4192fe49.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 271.2 | 5.5e-07 | 2.7e-07 / 5.5e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.1175 · +3.124 · +0.0545 | 12322 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9126cc5b45cb0170.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 270.9 | 1.9e-07 | 4.0e-08 / 1.9e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0912 · +3.603 · +0.0617 | 11852 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_914385e62d0849c8.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 32.8 | 6.1e-07 | 2.1e-08 / 6.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +2.0591 · +30.704 · +0.5222 | 11660 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9193c36b73ced370.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 63.1 | 7.5e-05 | 1.3e-08 / 1.4e-03 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0101 · +0.553 · +0.0097 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9290e3541f8db2a8.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 243.2 | 1.1e-07 | 4.2e-08 / 1.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0449 · +1.339 · +0.0232 | 12266 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9556d9d962547076.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 241.9 | 2.7e-07 | 2.7e-07 / 2.5e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0238 · +0.703 · +0.0123 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_958208bece282092.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 28.5 | 3.2e-07 | 3.2e-07 / 2.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0561 · +2.036 · +0.0355 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_969471cf51c5606b.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 209.0 | 7.5e-05 | 1.9e-07 / 7.5e-05 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0276 · +1.482 · +0.0259 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_97c4d115a33cb0e3.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 68.0 | 4.3e-08 | 4.3e-08 / 3.8e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.3937 · +15.887 · +0.2751 | 11920 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_98d2a143bd5d3fc3.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 180.5 | 1.2e-04 | 3.6e-07 / 1.8e-03 | 4.8e-06 / 5.7e-06 | 0.0e+00 | +0.0414 · +2.366 · +0.0413 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9936fe568cdc2ce7.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 55.4 | 3.2e-07 | 3.2e-07 / 2.3e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0361 · +1.161 · +0.0203 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_993d8d82cf2a5724.json (RS|federici|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 32.0 | 3.1e-07 | 3.1e-07 / 3.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0176 · +0.296 · +0.0052 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_9b1a0e0ce11373e7.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 211.8 | 2.0e-08 | 2.0e-08 / 4.3e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0604 · +2.314 · +0.0404 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a2cabda8f4af2503.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 161.6 | 2.7e-04 | 2.7e-07 / 2.7e-04 | 2.3e-05 / 2.2e-05 | 0.0e+00 | +0.0534 · +1.445 · +0.0252 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a35c6eb441fda0f9.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 60.1 | 2.3e-07 | 1.9e-07 / 2.3e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0213 · +1.000 · +0.0174 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a4022d7c0cf90b7c.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 55.6 | 3.6e-07 | 3.6e-07 / 2.8e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0526 · +2.258 · +0.0394 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a435e4c011c50eac.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 32.5 | 3.1e-06 | 5.2e-07 / 3.1e-06 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0431 · +2.251 · +0.0393 | 11671 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a68fac5aa2a0e04f.json (RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | cpu | 99.7 | 6.3e-08 | 6.1e-08 / 6.3e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.4174 · +15.037 · +0.2592 | 2214 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a6b8268144565499.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 34.9 | 7.5e-05 | 1.4e-08 / 7.9e-05 | 4.8e-07 / 4.8e-07 | 0.0e+00 | +1.6865 · +25.519 · +0.4383 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a721859d08fc759f.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 63.3 | 2.2e-04 | 1.4e-08 / 2.2e-04 | 1.4e-06 / 4.8e-07 | 0.0e+00 | +0.0371 · +1.676 · +0.0292 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_a9220da31a87fec3.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 276.3 | 5.2e-07 | 5.2e-07 / 3.9e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0271 · +0.774 · +0.0135 | 12320 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ab2cb5fa6a9a7c26.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 259.2 | 3.0e-07 | 3.0e-07 / 8.6e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0571 · +1.779 · +0.0310 | 12137 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ac703650bc13b5b0.json (RS|federici|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 32.8 | 4.6e-07 | 4.6e-07 / 8.9e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0405 · +0.683 · +0.0119 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_aff40ca7ee4b657e.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 66.4 | 8.1e-05 | 5.1e-08 / 8.1e-05 | 1.9e-06 / 4.8e-04 | 0.0e+00 | +0.5116 · +14.508 · +0.2448 | 11891 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b2a3957bce3c60c2.json (RS|federici|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 32.8 | 3.1e-07 | 3.1e-07 / 2.5e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0223 · +0.500 · +0.0087 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b2c4630f2474c88f.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 73.3 | 5.3e-08 | 5.3e-08 / 5.3e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.2137 · +7.569 · +0.1319 | 11898 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b5ad434aba05b114.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 59.3 | 8.9e-05 | 4.0e-07 / 8.9e-05 | 2.8e-05 / 2.5e-05 | 0.0e+00 | +0.0147 · +0.744 · +0.0130 | 11751 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b64ad1c50d32bc18.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 62.8 | 2.6e-08 | 2.6e-08 / 4.3e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0286 · +1.170 · +0.0204 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b872ec6953f642d5.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 70.8 | 4.3e-07 | 4.3e-07 / 2.8e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0604 · +1.573 · +0.0274 | 11926 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b8d3c77c826793ff.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 232.1 | 4.3e-07 | 4.3e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0254 · +1.318 · +0.0230 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_b9c00e2a5ba1f550.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 28.5 | 1.5e-04 | 2.0e-07 / 8.6e-03 | 4.8e-07 / 4.8e-07 | 0.0e+00 | +0.0509 · +1.428 · +0.0249 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ba7a65935eea462b.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 233.8 | 7.2e-05 | 4.3e-08 / 7.2e-05 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1204 · +4.618 · +0.0806 | 12118 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ba8236d659025ef4.json (RS|fau|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 51.3 | 2.7e-04 | 2.7e-07 / 2.7e-04 | 2.3e-05 / 2.2e-05 | 0.0e+00 | +0.0507 · +1.202 · +0.0210 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ba8d7fc66a6f6f4d.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 64.4 | 4.0e-07 | 4.0e-07 / 2.9e-07 | 4.8e-07 / 0.0e+00 | 0.0e+00 | +0.0158 · +0.812 · +0.0142 | 11934 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_bb073dec1e311c1f.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 184.7 | 2.0e-07 | 2.0e-07 / 4.2e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0661 · +1.529 · +0.0267 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_bb7651c5891ddd1d.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 58.2 | 2.4e-08 | 2.4e-08 / 1.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0931 · +3.795 · +0.0662 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_bcf880a27c906a4b.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 32.7 | 3.3e-06 | 3.0e-07 / 3.3e-06 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0557 · +2.162 · +0.0377 | 11677 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_bdbc7bfd0b755c6e.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 246.0 | 2.3e-08 | 2.1e-08 / 2.3e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0821 · +3.127 · +0.0546 | 12286 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_bfc78e765679fcfb.json (RS|federici|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 135.8 | 3.9e-04 | 4.0e-07 / 3.9e-04 | 4.8e-07 / 4.8e-06 | 0.0e+00 | +0.0047 · +0.269 · +0.0047 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c10ec07420bbce63.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 36.4 | 1.5e-08 | 1.4e-08 / 1.5e-08 | 0.0e+00 / 9.5e-07 | 0.0e+00 | +0.0586 · +1.949 · +0.0340 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c28a6ab10f64adf4.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 68.6 | 5.0e-08 | 3.4e-08 / 5.0e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1102 · +4.584 · +0.0800 | 11909 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c2b2274f25d23ab5.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 59.6 | 1.9e-07 | 1.9e-07 / 1.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0227 · +1.067 · +0.0186 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c2e79e77fc028c57.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 231.2 | 2.1e-04 | 1.8e-07 / 9.9e-04 | 5.1e-05 / 5.1e-05 | 0.0e+00 | +0.0509 · +1.325 · +0.0231 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c2ebc78a0e06ee7b.json (RS|federici|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 145.1 | 3.9e-04 | 1.0e-08 / 3.9e-04 | 1.9e-06 / 9.5e-07 | 0.0e+00 | +0.2759 · +3.840 · +0.0658 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c3331a53468038c9.json (RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 226.7 | 7.1e-05 | 5.1e-08 / 7.1e-05 | 0.0e+00 / 4.8e-04 | 0.0e+00 | +0.1069 · +3.572 · +0.0623 | 12113 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c3755aa63750fa8e.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 72.6 | 4.1e-08 | 4.0e-08 / 4.1e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1840 · +7.648 · +0.1329 | 11873 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c379ca0e5a16dc1e.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 64.9 | 4.3e-07 | 4.3e-07 / 0.0e+00 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0304 · +1.463 · +0.0255 | 11936 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c3ad4715bf6d58f4.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 188.2 | 1.8e-08 | 1.8e-08 / 1.4e-08 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0406 · +1.628 · +0.0284 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c480291dea4be624.json (RS|federici|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 142.3 | 1.3e-07 | 1.0e-07 / 1.3e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0560 · +2.304 · +0.0402 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c590f1de25070831.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 59.7 | 2.5e-08 | 2.5e-08 / 1.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.2240 · +5.730 · +0.0998 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c7156e55d0662e83.json (RS|dtu|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 251.0 | 4.3e-07 | 4.3e-07 / 3.4e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0716 · +1.827 · +0.0319 | 12135 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c7695ca1a6918694.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 55.1 | 3.6e-07 | 3.6e-07 / 3.4e-07 | 4.8e-07 / 4.8e-07 | 0.0e+00 | +0.0446 · +2.549 · +0.0445 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c8761e66a5958d20.json (RS|dtu|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 225.6 | 4.0e-07 | 4.0e-07 / 1.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0146 · +0.752 · +0.0131 | 12153 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c92c66b012c09a2a.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 215.4 | 1.3e-08 | 1.3e-08 / 6.8e-09 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0382 · +1.502 · +0.0262 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_c9e632a3fa0cc933.json (RS|fau|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 209.1 | 4.2e-07 | 4.2e-07 / 2.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0149 · +0.801 · +0.0140 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_cb81abb6db3e2382.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 34.7 | 2.0e-08 | 2.0e-08 / 9.6e-09 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.7678 · +24.659 · +0.4247 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_cc5e27a084a0b324.json (RS|dtu|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 63.5 | 1.9e-07 | 1.6e-07 / 1.9e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0272 · +1.065 · +0.0186 | 11940 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d00f5782f4c8f86c.json (RS|federici|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 31.8 | 7.7e-04 | 4.0e-07 / 7.7e-04 | 1.9e-06 / 4.8e-06 | 0.0e+00 | +0.0510 · +0.484 · +0.0084 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d22f815f9dc0db51.json (RS|federici|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 32.7 | 3.9e-04 | 3.8e-07 / 3.9e-04 | 1.2e-05 / 1.1e-05 | 0.0e+00 | +0.0439 · +0.404 · +0.0071 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d3ff8609b4625a3d.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 64.8 | 5.9e-05 | 4.3e-07 / 5.9e-05 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0222 · +1.079 · +0.0188 | 11952 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d4066df8f8eff098.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 80.8 | 2.6e-08 | 2.6e-08 / 1.6e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0428 · +1.523 · +0.0260 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d7992250480b7061.json (RS|federici|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 33.1 | 3.9e-04 | 3.1e-07 / 3.9e-04 | 8.1e-06 / 9.1e-06 | 0.0e+00 | +0.0213 · +0.328 · +0.0057 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d7a3fed4b2658c9b.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 28.4 | 1.2e-04 | 1.4e-08 / 1.2e-04 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.2109 · +10.967 · +0.1910 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d97db6176c2baff3.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 234.8 | 2.5e-08 | 1.5e-08 / 2.5e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.2188 · +7.906 · +0.1378 | 12318 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_d9c687236f565bbd.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 33.1 | 1.1e-06 | 3.3e-08 / 1.1e-06 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +1.5495 · +23.195 · +0.3957 | 11663 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_da499e76c04bfd73.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 300.5 | 3.9e-04 | 5.0e-07 / 4.2e-04 | 1.1e-05 / 8.6e-06 | 0.0e+00 | +0.0139 · +0.590 · +0.0103 | 2192 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_db190265561a53c9.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 55.6 | 3.0e-07 | 2.1e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0141 · +0.607 · +0.0106 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_dc17f2b1668d2eb9.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 74.2 | 1.7e-07 | 5.8e-08 / 1.7e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.4007 · +13.129 · +0.2272 | 11881 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_dcd1f8f8b689345c.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 69.2 | 2.3e-04 | 4.3e-08 / 1.8e-03 | 1.4e-06 / 0.0e+00 | 0.0e+00 | +6.6007 · +53.120 · +0.8438 | 11895 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_de562e583dee3e32.json (RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | cpu | 110.8 | 2.2e-07 | 1.0e-07 / 2.2e-07 | 4.8e-07 / 9.5e-07 | 0.0e+00 | +0.5333 · +17.530 · +0.2925 | 2215 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_df0b779b1e05ca4d.json (RS|federici|CS_SINGLE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 36.8 | 2.3e-08 | 2.3e-08 / 1.2e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0222 · +1.180 · +0.0206 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_df5a10dee634d098.json (RS|federici|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 32.4 | 4.2e-07 | 3.8e-07 / 4.2e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0464 · +0.460 · +0.0080 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_e06b62fbd19ef7b2.json (RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 66.5 | 5.9e-08 | 2.1e-08 / 5.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.3740 · +13.808 · +0.2382 | 11884 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_e18c27ef9c230866.json (RS|fau|NCE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 59.9 | 3.0e-04 | 2.0e-07 / 7.9e-04 | 3.8e-06 / 2.9e-06 | 0.0e+00 | +0.0453 · +1.180 · +0.0206 | 11757 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_e2a8384a04704c2f.json (RS|fau|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 187.3 | 2.5e-08 | 2.5e-08 / 1.9e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0553 · +2.061 · +0.0360 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_e2acc1d6ae5f7531.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 227.3 | 7.4e-08 | 5.1e-08 / 7.4e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1216 · +4.099 · +0.0715 | 12130 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_e6046341049b2a23.json (RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 33.3 | 3.1e-07 | 3.4e-08 / 3.1e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +1.9386 · +24.547 · +0.4192 | 11655 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_eadc3739260e8be6.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 211.1 | 1.4e-08 | 1.4e-08 / 2.6e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0716 · +3.242 · +0.0565 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_eb9fc79c5afda51f.dev_only.json (RS|federici|NCE|reve|residual_aligned_random) | dev_only | cpu | 714.8 | – | – / – | 9.5e-07 / 4.3e-06 | 0.0e+00 | +0.0175 · +0.376 · +0.0066 | 2214 | be2107d36af9 (evaluator, snapshot) | n/a |
| ALN3X_eb9fc79c5afda51f.json (RS|federici|NCE|reve|residual_aligned_random) | full | NVIDIA A40 | 136.0 | 5.2e-04 | 4.0e-07 / 5.2e-04 | 4.8e-07 / 4.8e-06 | 0.0e+00 | +0.0175 · +0.376 · +0.0066 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_eb9fc79c5afda51f.tiny.json (RS|federici|NCE|reve|residual_aligned_random) | tiny | cpu | 1014.6 | 2.6e-01 | 2.6e-01 / 2.6e-01 | 3.9e+00 / 3.9e+00 | 0.0e+00 | +0.0175 · +0.380 · +0.0066 | 3373 | be2107d36af9 (evaluator, snapshot) | n/a |
| ALN3X_ebed0f020cba4a85.json (RS|dtu|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 30.8 | 1.6e-07 | 1.6e-07 / 4.8e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0384 · +2.188 · +0.0382 | 11687 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ec2d132d3406e1f0.json (RS|fau|CS_SINGLE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 183.2 | 2.4e-04 | 2.4e-08 / 1.1e-02 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0673 · +2.402 · +0.0419 | 12158 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_ece06589ffeec5f2.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 254.4 | 4.0e-08 | 4.0e-08 / 1.7e-10 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0240 · +1.139 · +0.0199 | 12119 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_edc2014cee117863.json (RS|dtu|CS_SINGLE|reve|residual_aligned_random) | full | NVIDIA A40 | 251.7 | 4.2e-08 | 4.2e-08 / 7.6e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0597 · +1.679 · +0.0293 | 12284 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f0bd876085c01d84.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 276.0 | 5.4e-07 | 5.4e-07 / 3.8e-07 | 9.5e-07 / 9.5e-07 | 0.0e+00 | +0.0403 · +0.674 · +0.0118 | 2191 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f637d095283ec4e5.json (RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained) | full | NVIDIA A40 | 53.7 | 1.4e-08 | 1.4e-08 / 1.3e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0540 · +2.099 · +0.0366 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f725c1c2387278d4.json (RS|federici|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 140.0 | 3.9e-04 | 3.1e-07 / 3.9e-04 | 5.2e-06 / 9.1e-06 | 0.0e+00 | +0.0190 · +0.259 · +0.0045 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f7d798a24e3ceee1.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.6 | 1.4e-08 | 7.1e-09 / 1.4e-08 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.1795 · +8.467 · +0.1476 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f8dac5bdcb81c7f3.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 65.1 | 3.0e-07 | 1.8e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0293 · +0.861 · +0.0150 | 11956 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_f9634521db062b3a.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.1 | 2.4e-04 | 2.5e-08 / 2.4e-04 | 1.4e-06 / 9.5e-07 | 0.0e+00 | +0.3047 · +13.237 · +0.2301 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_fd19aef057479b32.json (RS|fau|NCE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 27.9 | 2.4e-04 | 3.6e-07 / 2.4e-04 | 2.4e-06 / 5.7e-06 | 0.0e+00 | +0.0433 · +2.315 · +0.0404 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_fd4c13c298383a2f.json (RS|dtu|NCE|cbramod|residual_aligned_random) | full | NVIDIA A40 | 64.0 | 4.3e-07 | 4.3e-07 / 2.6e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0422 · +1.217 · +0.0212 | 11950 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_fe02d248b66d4cea.json (RS|fau|NCE|reve|residual_aligned_pretrained) | full | NVIDIA A40 | 183.9 | 3.0e-07 | 2.6e-07 / 3.0e-07 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.0318 · +1.227 · +0.0214 | 12325 | be2107d36af9 (evaluator, snapshot) | yes |
| ALN3X_febcc3ed15236b38.json (RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity) | full | NVIDIA A40 | 31.5 | 1.8e-08 | 1.8e-08 / 1.3e-11 | 0.0e+00 / 0.0e+00 | 0.0e+00 | +0.6421 · +18.537 · +0.3195 | 11688 | be2107d36af9 (evaluator, snapshot) | yes |

Failed outputs: none.

**Engineering checks — v1 outputs (kept; recorded hash = the file on disk at call time, intermediate versions not kept; not merged)**, `results/auditory_alignment_v3/aln34/complement_function/units/`. Rule: max |Δ| ≤ 1e-3 on per-participant log-loss and rank_pct (both readouts, both records) and on both saved development risks; top-1 / top-5 / MRR can move by 1/n_queries on a single near-tie flip and are reported, not bounded. The tolerance is for float order, not a performance gate. Tiny and development-only runs are not comparable to the records by design; the development-side layer values (dev ‖r‖/‖u‖ · angle · post-norm change, unit means over the development anchors) are shown for every output and are merged into the configuration summaries only through reproducing full runs.

| output | kind | device | seconds | bounded max |Δ| | all-metric max |Δ| base / RS | dev risk |Δ| selected / epoch 0 | u/r split vs forward | dev ‖r‖/‖u‖ · angle (deg) · post-norm change | peak RSS MB | code sha256 | reproduces |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALN3X_18d86364bd045826.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 190.8 | 1.1e-06 | 3.8e-07 / 1.1e-06 | 0.0e+00 / 4.8e-07 | 0.0e+00 | +0.0044 · +0.177 · +0.0031 | – | f7e0ac65c7bd (file) | yes |
| ALN3X_544007987cb9cc3f.dev_only.json (RS|federici|NCE|cbramod|residual_aligned_random) | dev_only | cpu | 131.4 | – | – / – | 1.4e-06 / 4.8e-07 | 0.0e+00 | +0.0107 · +0.300 · +0.0052 | – | 783beb72f72d (file) | n/a |
| ALN3X_6bb801c9730ca819.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 197.5 | 3.9e-04 | 4.7e-07 / 5.1e-04 | 2.9e-06 / 4.3e-06 | 0.0e+00 | +0.0530 · +0.469 · +0.0082 | – | 4aca86167aa0 (file) | yes |
| ALN3X_7473fec7dcca4106.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 114.0 | 1.3e-04 | 3.2e-07 / 1.3e-04 | 0.0e+00 / 1.4e-06 | 0.0e+00 | +0.0075 · +0.336 · +0.0059 | – | 783beb72f72d (file) | yes |
| ALN3X_da499e76c04bfd73.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 138.7 | 3.9e-04 | 5.0e-07 / 4.2e-04 | 1.1e-05 / 8.6e-06 | 0.0e+00 | +0.0139 · +0.590 · +0.0103 | – | d3ce4e505aa8 (file) | yes |
| ALN3X_f0bd876085c01d84.json (RS|federici|NCE|small_capacity_branch|residual_small_capacity) | full | cpu | 219.1 | 5.4e-07 | 5.4e-07 / 3.8e-07 | 9.5e-07 / 9.5e-07 | 0.0e+00 | +0.0403 · +0.674 · +0.0118 | – | 0d69bcc916b7 (file) | yes |

Failed outputs: none.

v1 vs v2 per-unit outputs of the same unit (every numeric result leaf; timing and provenance fields excluded):

| output | numeric leaves | max |Δ| | largest at | per-query float arrays max |Δ| | per-query rank arrays: max fraction differing |
|---|---|---|---|---|---|
| ALN3X_18d86364bd045826.json | 843 | 8.5e-08 | dev/layers/angle_deg_p90 | 0.0e+00 | 0.0e+00 |
| ALN3X_544007987cb9cc3f.dev_only.json | 37 | 0.0e+00 | selected_epoch | – | – |
| ALN3X_6bb801c9730ca819.json | 731 | 1.5e-09 | dev/layers/angle_deg_mean | 0.0e+00 | 0.0e+00 |
| ALN3X_7473fec7dcca4106.json | 815 | 1.0e-07 | dev/layers/angle_deg_p90 | 0.0e+00 | 0.0e+00 |
| ALN3X_da499e76c04bfd73.json | 871 | 6.4e-08 | dev/layers/angle_deg_p90 | 0.0e+00 | 0.0e+00 |
| ALN3X_f0bd876085c01d84.json | 843 | 1.2e-07 | dev/layers/angle_deg_p90 | 0.0e+00 | 0.0e+00 |

## 10. Asset audit

- SC: 100 rows, 100 complete records (600 variant evaluations); {"(3401, 'complete', 'link', True, True)": 100}. Checkpoint files per unit: {'<eid>_best.pt': 100}; link targets {'/projects/EEG-foundation-model': 100}. Saved: per-identity evaluations of the six variants; ridge alphas and grouped-CV curves; PCA means and bases (ckpt). Not saved: ridge coefficients (closed-form; a refit with the saved PCA bases and alphas needs the training rows' features again, FM forwards for the FM variants); per-query predictions; FM / raw features.
- RS: 500 rows, per seed {'3401': {'rows': 250, 'complete': 250}, '3407': {'rows': 125, 'complete': 125}, '3413': {'rows': 125, 'complete': 125}}; selected epoch {"(3401, 'epoch>0')": 234, "(3401, 'epoch0')": 16, "(3407, 'epoch>0')": 123, "(3413, 'epoch>0')": 120, "(3413, 'epoch0')": 5, "(3407, 'epoch0')": 2}.
  - Seed-3401 checkpoint files per unit: {'<eid>_best.pt': 250} over 250 units; link states {'link': 250}; link targets {'/projects/EEG-foundation-model': 250}; units without exactly one file: 0.
  - Saved: per-identity evaluation at the selected epoch; dev curve per epoch (risk, rank, temperature, train loss); selected-epoch trainable weights (residual head + context LayerNorm/Linear or small conv; frozen encoder / backbone excluded). Epoch 0: no unit has a separate epoch-0 file: residual32 writes epoch 0 to <eid>_best.pt first and overwrites it when a later epoch has lower development risk; for the units that selected epoch 0 the single file is the epoch-0 state (zero last layer, see the checkpoint layer); for every other unit epoch 0 is reconstructed exactly (zero last layer -> r = 0). Not saved: intermediate epochs (resume file removed at completion); per-query outputs; the random-init backbone weights (regenerated from torch.manual_seed(seed) + Backbone(random_full); checked by the development-only runs listed under the engineering checks and by each unit's own reproduction check).
- Missing dependencies: none.
- L0 (A_LOCAL lag_local_tokens full): {"('dtu', 'CS_SINGLE', 'complete', 'link')": 10, "('dtu', 'NCE', 'complete', 'link')": 10, "('fau', 'CS_SINGLE', 'complete', 'link')": 10, "('fau', 'NCE', 'complete', 'link')": 10, "('federici', 'CS_SINGLE', 'complete', 'link')": 5, "('federici', 'NCE', 'complete', 'link')": 5}; checkpoint files per unit {'<eid>_best.pt': 50}.
- L1 (ALN32_LOCAL_SUPPORT local_aligned1000): {"('dtu', 'NCE', 'complete', 'link')": 10, "('fau', 'NCE', 'complete', 'link')": 10, "('federici', 'NCE', 'complete', 'link')": 5}; checkpoint files per unit {'<eid>_best.pt': 25}.
- FM weights vs the fetch receipt (sha256 computed now): brain-bzh/reve-base 7/7 files match (revision dc2a075); weighting666/CBraMod 3/3 files match (revision 500543c); brain-bzh/reve-positions 7/7 files match (revision befa5b5); github:wjq-learning/CBraMod 16/16 files present (no hashes in the receipt). All hashed files match: True.
- Files named by an SC / RS / base experiment id (search by id; file names containing an experiment id (regex ALN3X?_<16 hex>) under results/auditory_alignment_v3 and private/auditory_alignment_v3):

| role | directory | name | files | kind | contents |
|---|---|---|---|---|---|
| L0 | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 50 | checkpoint | – |
| L0 | private/auditory_alignment_v3/logs/units | <eid>.log | 50 | unit log | – |
| L0 | private/auditory_alignment_v3/probe_out/ckpt | <eid>_best.pt | 1 | engineering probe of the runner | – |
| L0 | private/auditory_alignment_v3/probe_out/units | <eid>.json | 1 | engineering probe of the runner | – |
| L0 | private/auditory_alignment_v3/sci_r1/continuous | <eid>__frozen.json | 50 | sci_r1 continuous-science output | – |
| L0 | private/auditory_alignment_v3/sci_r1/continuous | <eid>__frozen.npz | 50 | sci_r1 continuous-science output | arrays {'s1': [14, 25, 9], 'tg': [14, 25, 25, 4], 'pooled_full': [14, 9], 'md': [14, 29, 2], 'sb': [14, 29, 2], 'pooled_lam': [3], 'chan_md': [14, 31], 'filt_patterns': [31, 16], 'filt_energy': [31]}; first dimension = participants in {'s1': 50, 'tg': 50, 'pooled_full': 50, 'md': 50, 'sb': 50, 'chan_md': 50}; = test queries in none |
| L0 | private/auditory_alignment_v3/units | <eid>.json | 50 | unit record | – |
| L1 | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 25 | checkpoint | – |
| L1 | private/auditory_alignment_v3/logs/units | <eid>.log | 25 | unit log | – |
| L1 | private/auditory_alignment_v3/probe_out_aln32/ckpt | <eid>_best.pt | 1 | engineering probe of the runner | – |
| L1 | private/auditory_alignment_v3/probe_out_aln32/units | <eid>.json | 1 | engineering probe of the runner | – |
| L1 | private/auditory_alignment_v3/units | <eid>.json | 25 | unit record | – |
| RS seed 3401 | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 250 | checkpoint | – |
| RS seed 3401 | private/auditory_alignment_v3/logs/units | <eid>.log | 250 | unit log | – |
| RS seed 3401 | private/auditory_alignment_v3/probe_out_r32/ckpt | <eid>_best.pt | 1 | engineering probe of the runner | – |
| RS seed 3401 | private/auditory_alignment_v3/probe_out_r32/units | <eid>.json | 1 | engineering probe of the runner | – |
| RS seed 3401 | private/auditory_alignment_v3/units | <eid>.json | 250 | unit record | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units | <eid>.dev_only.json | 1 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units | <eid>.json | 5 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units | <eid>_queries.npz | 5 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units_v2 | <eid>.dev_only.json | 2 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units_v2 | <eid>.json | 234 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units_v2 | <eid>.tiny.json | 1 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units_v2 | <eid>.tiny_queries.npz | 1 | this lane's evaluator output | – |
| RS seed 3401 | results/auditory_alignment_v3/aln34/complement_function/units_v2 | <eid>_queries.npz | 234 | this lane's evaluator output | – |
| RS seed 3407 | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 125 | checkpoint | – |
| RS seed 3407 | private/auditory_alignment_v3/logs/units | <eid>.log | 125 | unit log | – |
| RS seed 3407 | private/auditory_alignment_v3/units | <eid>.json | 125 | unit record | – |
| RS seed 3413 | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 125 | checkpoint | – |
| RS seed 3413 | private/auditory_alignment_v3/logs/units | <eid>.log | 125 | unit log | – |
| RS seed 3413 | private/auditory_alignment_v3/units | <eid>.json | 125 | unit record | – |
| SC | private/auditory_alignment_v3/ckpt | <eid>_best.pt | 100 | checkpoint | – |
| SC | private/auditory_alignment_v3/logs/units | <eid>.log | 100 | unit log | – |
| SC | private/auditory_alignment_v3/probe_out_c32/ckpt | <eid>_best.pt | 2 | engineering probe of the runner | – |
| SC | private/auditory_alignment_v3/probe_out_c32/units | <eid>.FAILED.json | 2 | engineering probe of the runner | – |
| SC | private/auditory_alignment_v3/probe_out_c32/units | <eid>.json | 2 | engineering probe of the runner | – |
| SC | private/auditory_alignment_v3/units | <eid>.json | 100 | unit record | – |

- File groups whose arrays have a first dimension equal to a unit's number of test queries (per-query outputs) outside this lane: 0. The sci_r1 arrays of the 50 L0 units (chan_md, filt_energy, filt_patterns, md, pooled_full, pooled_lam, s1, sb, tg) are indexed by participant (first dimension = the participants of the paired .json), i.e. per-participant lag and temporal-generalisation summaries, not per-query evaluator predictions. No per-query output of any SC, RS, L1 or L0 unit was saved, so L1–L3 need forward passes (§9, §11).

## 11. GPU plan (written, not submitted)

- Unit list `private/auditory_alignment_v3/aln34/complement_function_units.txt`: 234 RS units with selected epoch > 0, of which 0 are pending (the others have a reproducing v2 output); the 16 epoch-0 units need no run.
- Estimate for the pending units: about 0.0 GPU-minutes (range 0.0–0.0); assumed, not measured: per unit 1.25 x the record's eval_seconds + 90 s (range 1.0 x + 60 s to 1.6 x + 120 s). The records ran on {'Tesla V100-PCIE-16GB': 37, 'Tesla V100S-PCIE-32GB': 92, 'NVIDIA A100-PCIE-40GB': 58, 'NVIDIA A30': 14, 'NVIDIA A40': 33}.
- GPU memory of this evaluator: ALN3X_0150eb06b7558743.json 2474 MB; ALN3X_025e0931cfe9c2e9.json 2208 MB; ALN3X_030dd347f750acc1.json 2474 MB; ALN3X_03ae54a8f9e4f921.json 2474 MB; ALN3X_04a301cd3fb68a85.json 3480 MB; ALN3X_04ae9707a8a6a863.json 2295 MB; ALN3X_055b40c731b388bc.json 2295 MB; ALN3X_05b5791a5987ebd9.json 3480 MB; ALN3X_07e8b3d158408971.json 2474 MB; ALN3X_09346fff29d534e4.json 2208 MB; ALN3X_0ad1931c0529dfc1.json 5436 MB; ALN3X_0b65fe1d80952bd2.json 3263 MB; ALN3X_0eea1953f258f1c8.json 1809 MB; ALN3X_0f171ebf5d0f5036.json 1099 MB; ALN3X_0f54b46f2e0c483f.json 2295 MB; ALN3X_10ba16de1e174fa3.json 2295 MB; ALN3X_125af94e1a1dc34f.json 3263 MB; ALN3X_13379c7b29e678cb.json 1809 MB; ALN3X_155d9c35388abdcc.json 3480 MB; ALN3X_173c3c1b6d711141.json 5436 MB; ALN3X_1c22b5dd7b26f286.json 3480 MB; ALN3X_1d48e8941571c920.json 2295 MB; ALN3X_1e52f576224bd773.json 3480 MB; ALN3X_1e8815d991df83f3.json 3480 MB; ALN3X_2052d82b0c1fadcd.json 3263 MB; ALN3X_208c75ebbc607047.json 3480 MB; ALN3X_20c9a54ea0a04714.json 1809 MB; ALN3X_21a236f9a412aeeb.json 1099 MB; ALN3X_2234673f984e9746.json 2295 MB; ALN3X_23d5b6458a76f0da.json 2208 MB; ALN3X_244f1b1ab8813eef.json 2208 MB; ALN3X_24dc4921e665c00f.json 3480 MB; ALN3X_26a666ffcd1137c5.json 3263 MB; ALN3X_271dffae89bf6759.json 5436 MB; ALN3X_273cb9bd9323c25c.json 3480 MB; ALN3X_276d4e240c82c857.json 3480 MB; ALN3X_296731e3fae9993f.json 3480 MB; ALN3X_29fce9a4e2f3bba6.json 5436 MB; ALN3X_2ad1c08cf8ba2e69.json 2295 MB; ALN3X_2b0bb34201a501c8.json 3480 MB; ALN3X_32e623eb8a92dd5f.json 1809 MB; ALN3X_344cef4fc9c6707a.json 3263 MB; ALN3X_34b101ed999a6297.json 3480 MB; ALN3X_352bb03800b071e8.json 2295 MB; ALN3X_3677f4b427f5ad4d.json 3263 MB; ALN3X_36bb8b59a1179a2e.json 3263 MB; ALN3X_376a4cc6e6b7dd13.json 1809 MB; ALN3X_37a7e8f2c2fc5872.json 3263 MB; ALN3X_3d84d0391cfd79dc.json 3263 MB; ALN3X_3d9055227c7db8c0.json 5436 MB; ALN3X_3e945ae4a925a60f.json 2295 MB; ALN3X_412f63a398a5d0ab.json 2295 MB; ALN3X_42057c2a09ce8ee9.json 5436 MB; ALN3X_44d14ac25c75d739.json 5436 MB; ALN3X_456a4005e9846938.json 2295 MB; ALN3X_4684ec0c6f933730.json 3263 MB; ALN3X_478816e2f36324f6.json 2474 MB; ALN3X_47bef4e37c454976.json 2295 MB; ALN3X_47f9daf0bb3ce036.json 1099 MB; ALN3X_490cb6494d28bdf1.json 3480 MB; ALN3X_499ed8410a7788d8.json 2295 MB; ALN3X_4b43b00cfeeaba00.json 2295 MB; ALN3X_4bc5bc8db84fb0fa.json 3263 MB; ALN3X_4cf9ddd48a66fe21.json 2295 MB; ALN3X_4e5e290e34c0afce.json 3480 MB; ALN3X_4fff04643cf1e3d7.json 3263 MB; ALN3X_5059dc8e2b42d8fc.json 2295 MB; ALN3X_507e307c45561e2b.json 1809 MB; ALN3X_515a59d960b00e9f.json 3263 MB; ALN3X_51cdec7aea7e09aa.json 2295 MB; ALN3X_526b5aa9e5c8193f.json 2474 MB; ALN3X_544007987cb9cc3f.json 1099 MB; ALN3X_5526b7f14cbfb4e6.json 1099 MB; ALN3X_5702d5df3401bff0.json 5436 MB; ALN3X_57397b73b004b163.json 3480 MB; ALN3X_57ac4496bc754dd8.json 5436 MB; ALN3X_57adcd7f2c0948df.json 5436 MB; ALN3X_57d6b53bd33edc06.json 3480 MB; ALN3X_58a1749353d7b769.json 3480 MB; ALN3X_594d76a7d27e97b3.json 5436 MB; ALN3X_59b881c86fef5638.json 3480 MB; ALN3X_59bdf028cb7a8a1f.json 1809 MB; ALN3X_59f53c7a7389fdda.json 3263 MB; ALN3X_5a2c00065b48c6a4.json 5436 MB; ALN3X_5ab8d80774f53f70.json 2295 MB; ALN3X_5be5183794592a92.json 2208 MB; ALN3X_5d1b8587585cac25.json 3480 MB; ALN3X_5d3e101eaaa3ad13.json 5436 MB; ALN3X_5e4f4d7bb12d07e6.json 2295 MB; ALN3X_5f7897b91170e3a4.json 2474 MB; ALN3X_6101fe58340cd015.json 2208 MB; ALN3X_6186f58d2698ee2b.json 2208 MB; ALN3X_62213d18fbbcce40.json 2474 MB; ALN3X_624c731c845bd7c0.json 3480 MB; ALN3X_6389fd1cd5085757.json 3263 MB; ALN3X_63f00ab52e1f2f87.json 1099 MB; ALN3X_64631148f7c0b4ad.json 3480 MB; ALN3X_658d67548cf7fa2e.json 3263 MB; ALN3X_66030862c7c7a5ea.json 1099 MB; ALN3X_66bddf767f68c0d1.json 3263 MB; ALN3X_66e6e5c3f0ea729e.json 1809 MB; ALN3X_6b94fadac4e59212.json 2474 MB; ALN3X_6cd777f0415e91d7.json 2295 MB; ALN3X_6d412b6de40d9b23.json 1809 MB; ALN3X_6d7e49d21a3a0cf6.json 2208 MB; ALN3X_6dee7bccba8be1d6.json 2295 MB; ALN3X_6e21279e2353ea01.json 3263 MB; ALN3X_6e2e0ba8cd20ba24.json 3263 MB; ALN3X_6e394c1e24387069.json 2208 MB; ALN3X_6eaa8d2dbc2a486a.json 3263 MB; ALN3X_72d55bfa49208d06.json 5436 MB; ALN3X_72e3915442273a89.json 3480 MB; ALN3X_764fb4f8a97de3c2.json 3480 MB; ALN3X_76bb4b79a4a7f71d.json 5436 MB; ALN3X_77fcfc45afed19d1.json 5436 MB; ALN3X_79b02526d4f8b18a.json 2208 MB; ALN3X_7aba72ee017e0c3d.json 3263 MB; ALN3X_7b0e0ea794289c04.json 5436 MB; ALN3X_7b119a1d5834881f.json 5436 MB; ALN3X_7b7e974cc8ec45a6.json 2474 MB; ALN3X_7cd5a67042395c7a.json 3480 MB; ALN3X_7f47352e9e834da3.json 3480 MB; ALN3X_8032ca8a27a5555d.json 3263 MB; ALN3X_80aa1fea26db9714.json 3263 MB; ALN3X_83798d5d4c69843e.json 5436 MB; ALN3X_861bff15d9107bcf.json 5436 MB; ALN3X_868ac7697f2282db.json 1099 MB; ALN3X_86ceb414eb57e340.json 2208 MB; ALN3X_878cddd92dd6901e.json 3263 MB; ALN3X_879c25079fb35d1e.json 2474 MB; ALN3X_895b887bb017ba18.json 2295 MB; ALN3X_8a341caf3c68d8e4.json 5436 MB; ALN3X_8c879ed72aaa5e9e.json 1099 MB; ALN3X_8dd7318a6852848b.json 5436 MB; ALN3X_8f571c0b6d2f7ab6.json 2295 MB; ALN3X_90f0cedc4192fe49.json 5436 MB; ALN3X_9126cc5b45cb0170.json 5436 MB; ALN3X_914385e62d0849c8.json 2208 MB; ALN3X_9193c36b73ced370.json 2295 MB; ALN3X_9290e3541f8db2a8.json 5436 MB; ALN3X_9556d9d962547076.json 5436 MB; ALN3X_958208bece282092.json 1809 MB; ALN3X_969471cf51c5606b.json 3480 MB; ALN3X_97c4d115a33cb0e3.json 3263 MB; ALN3X_98d2a143bd5d3fc3.json 3480 MB; ALN3X_9936fe568cdc2ce7.json 2295 MB; ALN3X_993d8d82cf2a5724.json 1099 MB; ALN3X_9b1a0e0ce11373e7.json 3480 MB; ALN3X_a2cabda8f4af2503.json 3480 MB; ALN3X_a35c6eb441fda0f9.json 2295 MB; ALN3X_a4022d7c0cf90b7c.json 2295 MB; ALN3X_a435e4c011c50eac.json 2208 MB; ALN3X_a6b8268144565499.json 1809 MB; ALN3X_a721859d08fc759f.json 2295 MB; ALN3X_a9220da31a87fec3.json 5436 MB; ALN3X_ab2cb5fa6a9a7c26.json 5436 MB; ALN3X_ac703650bc13b5b0.json 1099 MB; ALN3X_aff40ca7ee4b657e.json 3263 MB; ALN3X_b2a3957bce3c60c2.json 1099 MB; ALN3X_b2c4630f2474c88f.json 3263 MB; ALN3X_b5ad434aba05b114.json 3263 MB; ALN3X_b64ad1c50d32bc18.json 2295 MB; ALN3X_b872ec6953f642d5.json 3263 MB; ALN3X_b8d3c77c826793ff.json 5436 MB; ALN3X_b9c00e2a5ba1f550.json 1809 MB; ALN3X_ba7a65935eea462b.json 5436 MB; ALN3X_ba8236d659025ef4.json 2295 MB; ALN3X_ba8d7fc66a6f6f4d.json 3263 MB; ALN3X_bb073dec1e311c1f.json 3480 MB; ALN3X_bb7651c5891ddd1d.json 2295 MB; ALN3X_bcf880a27c906a4b.json 2208 MB; ALN3X_bdbc7bfd0b755c6e.json 5436 MB; ALN3X_bfc78e765679fcfb.json 2474 MB; ALN3X_c10ec07420bbce63.json 1099 MB; ALN3X_c28a6ab10f64adf4.json 3263 MB; ALN3X_c2b2274f25d23ab5.json 2295 MB; ALN3X_c2e79e77fc028c57.json 5436 MB; ALN3X_c2ebc78a0e06ee7b.json 2474 MB; ALN3X_c3331a53468038c9.json 5436 MB; ALN3X_c3755aa63750fa8e.json 3263 MB; ALN3X_c379ca0e5a16dc1e.json 3263 MB; ALN3X_c3ad4715bf6d58f4.json 3480 MB; ALN3X_c480291dea4be624.json 2474 MB; ALN3X_c590f1de25070831.json 2295 MB; ALN3X_c7156e55d0662e83.json 5436 MB; ALN3X_c7695ca1a6918694.json 2295 MB; ALN3X_c8761e66a5958d20.json 5436 MB; ALN3X_c92c66b012c09a2a.json 3480 MB; ALN3X_c9e632a3fa0cc933.json 3480 MB; ALN3X_cb81abb6db3e2382.json 1809 MB; ALN3X_cc5e27a084a0b324.json 3263 MB; ALN3X_d00f5782f4c8f86c.json 1099 MB; ALN3X_d22f815f9dc0db51.json 1099 MB; ALN3X_d3ff8609b4625a3d.json 3263 MB; ALN3X_d4066df8f8eff098.json 2295 MB; ALN3X_d7992250480b7061.json 1099 MB; ALN3X_d7a3fed4b2658c9b.json 1809 MB; ALN3X_d97db6176c2baff3.json 5436 MB; ALN3X_d9c687236f565bbd.json 2208 MB; ALN3X_db190265561a53c9.json 2295 MB; ALN3X_dc17f2b1668d2eb9.json 3263 MB; ALN3X_dcd1f8f8b689345c.json 3263 MB; ALN3X_df0b779b1e05ca4d.json 1099 MB; ALN3X_df5a10dee634d098.json 1099 MB; ALN3X_e06b62fbd19ef7b2.json 3263 MB; ALN3X_e18c27ef9c230866.json 2295 MB; ALN3X_e2a8384a04704c2f.json 3480 MB; ALN3X_e2acc1d6ae5f7531.json 5436 MB; ALN3X_e6046341049b2a23.json 2208 MB; ALN3X_eadc3739260e8be6.json 3480 MB; ALN3X_eb9fc79c5afda51f.json 2474 MB; ALN3X_ebed0f020cba4a85.json 2208 MB; ALN3X_ec2d132d3406e1f0.json 3480 MB; ALN3X_ece06589ffeec5f2.json 5436 MB; ALN3X_edc2014cee117863.json 5436 MB; ALN3X_f637d095283ec4e5.json 2295 MB; ALN3X_f725c1c2387278d4.json 2474 MB; ALN3X_f7d798a24e3ceee1.json 1809 MB; ALN3X_f8dac5bdcb81c7f3.json 3263 MB; ALN3X_f9634521db062b3a.json 1809 MB; ALN3X_fd19aef057479b32.json 1809 MB; ALN3X_fd4c13c298383a2f.json 3263 MB; ALN3X_fe02d248b66d4cea.json 3480 MB; ALN3X_febcc3ed15236b38.json 1809 MB. The records' `gpu_peak_allocated_mb` is one process per unit covering training and evaluation: dtu|cbramod 3276–3296 MB; dtu|reve 5462–5504 MB; dtu|small_capacity_branch 2200–14391 MB; fau|cbramod 2303–2314 MB; fau|reve 3494–3511 MB; fau|small_capacity_branch 1812–9947 MB; federici|cbramod 1104–1116 MB; federici|reve 2487–2508 MB; federici|small_capacity_branch 503–2449 MB. Units above twice their group minimum: dtu|small_capacity_branch 2 units 14390–14391 MB on NVIDIA A30, NVIDIA A100-PCIE-40GB; fau|small_capacity_branch 11 units 9945–9947 MB on NVIDIA A100-PCIE-40GB, NVIDIA A30; federici|small_capacity_branch 3 units 2449–2449 MB on NVIDIA A100-PCIE-40GB.
- Worker: `/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python -B -m auditory_alignment_v3.aln34.complement_function --units-file private/auditory_alignment_v3/aln34/complement_function_units.txt --device cuda [--shard K/N]` with HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 (REVE loads) and PYTHONPATH at the repo root; atomic claims prevent duplicate work across parallel workers, a requeued worker releases its own claims, a unit is tried at most 3 times. Slurm template: `private/auditory_alignment_v3/aln34/complement_function_gpu.sbatch` (follows the pool sbatch; not submitted; scheduling stays inside the 10-GPU cap).

## 12. Experiment update (observation → working judgement → competing explanations → next intervention → execution)

- Date and versions: 2026-10-17 15:06 CEST; code hashes in the header; unit records as read at aggregation ({'FM|complete': 50, 'L0|complete': 50, 'L1|complete': 25, 'RS|complete': 250, 'SC|complete': 100, 'TF|complete': 100}).
- Done / running / pending: SC and RS seed-3401 records complete; L1–L3 per query: 234 units reproduced (10 CPU outputs reused;224 GPU outputs), 16 exact epoch-0 zeros, 0 pending the GPU run; RS panel seeds (ADDENDUM_11, not used here): seed 3407 125/125 complete; seed 3413 125/125 complete.
- Already seen before this lane: the frozen SC / RS result tables (incl. their ΔR_native point estimates) and the brief's cross-document levels (analysis note §3). New in this lane (v1, recomputed identically in v2): the paired base → SC families of both readouts, the intervals of the native RS families, L4, the checkpoint layer and the L1–L3 values of RS·federici·NCE·small_capacity. New in v2 (analysis note, Correction 1, C1.12): the access table, the budgets, the cross-backbone copies, the asset search by id, the FM-weight hashes, and the CPU runs listed in §9 beyond the v1 ones.

### 12.1 Observation (complete differences in §4–§9)

- SC variant vs the original direct base, unified readout: simultaneous classes over the 72 members {'I<0': 61, 'contains 0': 11}. These include `local_only` twice per dataset · base (the cbramod and reve units share that ridge); over the 66 distinct contrasts {'I<0': 56, 'contains 0': 10}. I>0: none. Per dataset · base (both backbones, 12 members each, `local_only` in both):
  - fau·L0: {'I<0': 11, 'contains 0': 1}; ΔR from -0.047 to -0.018 (largest ΔR: cbramod/aligned_random -0.018, simultaneous [-0.045, +0.010])
  - fau·L1: {'contains 0': 10, 'I<0': 2}; ΔR from -0.024 to -0.006 (largest ΔR: cbramod/aligned_pretrained -0.006, simultaneous [-0.025, +0.012])
  - dtu·L0: {'I<0': 12}; ΔR from -0.106 to -0.054 (largest ΔR: reve/aligned_random -0.054, simultaneous [-0.092, -0.016])
  - dtu·L1: {'I<0': 12}; ΔR from -0.130 to -0.068 (largest ΔR: reve/aligned_random -0.068, simultaneous [-0.105, -0.031])
  - federici·L0: {'I<0': 12}; ΔR from -0.032 to -0.020 (largest ΔR: reve/local_refit_capacity -0.020, simultaneous [-0.037, -0.003])
  - federici·L1: {'I<0': 12}; ΔR from -0.045 to -0.036 (largest ΔR: cbramod/local_refit_capacity -0.036, simultaneous [-0.055, -0.017])
- SC variant vs the original direct base, native readout: simultaneous classes over the 72 members {'I<0': 64, 'contains 0': 8}. These include `local_only` twice per dataset · base (the cbramod and reve units share that ridge); over the 66 distinct contrasts {'I<0': 58, 'contains 0': 8}. I>0: none. Per dataset · base (both backbones, 12 members each, `local_only` in both):
  - fau·L0: {'I<0': 12}; ΔR from -0.238 to -0.220 (largest ΔR: cbramod/aligned_pretrained -0.220, simultaneous [-0.274, -0.165])
  - fau·L1: {'I<0': 12}; ΔR from -0.198 to -0.188 (largest ΔR: cbramod/aligned_pretrained -0.188, simultaneous [-0.223, -0.152])
  - dtu·L0: {'I<0': 12}; ΔR from -0.608 to -0.578 (largest ΔR: reve/small_context -0.578, simultaneous [-0.701, -0.456])
  - dtu·L1: {'I<0': 12}; ΔR from -0.510 to -0.477 (largest ΔR: reve/small_context -0.477, simultaneous [-0.575, -0.379])
  - federici·L0: {'I<0': 12}; ΔR from -0.065 to -0.053 (largest ΔR: reve/local_refit_capacity -0.053, simultaneous [-0.078, -0.029])
  - federici·L1: {'I<0': 4, 'contains 0': 8}; ΔR from -0.038 to -0.025 (largest ΔR: reve/local_refit_capacity -0.025, simultaneous [-0.060, +0.009])
- The two `local_only` copies agree in class in 12 of 12 dataset · base · readout cells (max per-identity |ΔR| between the copies 2.2e-04). `local_refit_capacity` and `small_context` read no FM feature either, so both units of a cell see the same inputs: the `local_refit_capacity` copies differ by at most 2.0e-04 per identity (alpha equal in 45 of 50 pairs), the same order as the `local_only` copies; the `small_context` copies by up to 1.0e-01 (alpha equal in 40 of 50 pairs); its raw-window block is reduced by a randomised PCA drawn separately in each unit. They are near-duplicates or two draws of one design, not independent evidence.
- RS selected epoch vs epoch 0, unified readout: simultaneous classes {'contains 0': 26, 'I<0': 3, 'I>0': 1}. I<0: fau·CS_SINGLE/small_capacity_branch/residual_small_capacity -0.018; dtu·CS_SINGLE/cbramod/residual_aligned_random -0.016; dtu·CS_SINGLE/small_capacity_branch/residual_small_capacity -0.087. I>0: dtu·NCE/small_capacity_branch/residual_small_capacity +0.016.
- RS selected epoch vs epoch 0, native readout: simultaneous classes {'I<0': 6, 'contains 0': 19, 'I>0': 5}. I<0: fau·NCE/cbramod/residual_aligned_pretrained -0.004; fau·NCE/reve/residual_aligned_pretrained -0.003; fau·NCE/cbramod/residual_aligned_random -0.003; fau·NCE/reve/residual_aligned_random -0.004; fau·CS_SINGLE/small_capacity_branch/residual_small_capacity -0.021; dtu·CS_SINGLE/small_capacity_branch/residual_small_capacity -0.054. I>0: dtu·NCE/cbramod/residual_aligned_pretrained +0.002; dtu·NCE/reve/residual_aligned_pretrained +0.003; dtu·NCE/cbramod/residual_aligned_random +0.002; dtu·NCE/reve/residual_aligned_random +0.003; federici·NCE/small_capacity_branch/residual_small_capacity +0.004.
- Remapping alone (original base → SC `local_only`; the cbramod copy): fau·L0·unified -0.036 [-0.062, -0.009]; fau·L0·native -0.222 [-0.276, -0.168]; fau·L1·unified -0.014 [-0.035, +0.008]; fau·L1·native -0.193 [-0.227, -0.159]; dtu·L0·unified -0.106 [-0.136, -0.076]; dtu·L0·native -0.579 [-0.696, -0.463]; dtu·L1·unified -0.130 [-0.164, -0.095]; dtu·L1·native -0.488 [-0.582, -0.393]; federici·L0·unified -0.027 [-0.043, -0.011]; federici·L0·native -0.062 [-0.089, -0.034]; federici·L1·unified -0.045 [-0.064, -0.026]; federici·L1·native -0.038 [-0.074, -0.001].
- L4 dtu·CS_SINGLE: 50 units, 1 at epoch 0; mean Δdev +0.0014 bits (relative +0.00019); mean unit Δtest unified -0.0255, native -0.0177; Spearman Δdev~Δtest native over epoch>0 units -0.49.
- L4 dtu·NCE: 50 units, 3 at epoch 0; mean Δdev +0.0045 bits (relative +0.00069); mean unit Δtest unified +0.0032, native +0.0044; Spearman Δdev~Δtest native over epoch>0 units +0.04.
- L4 fau·CS_SINGLE: 50 units, 5 at epoch 0; mean Δdev +0.0005 bits (relative +0.00008); mean unit Δtest unified -0.0041, native -0.0047; Spearman Δdev~Δtest native over epoch>0 units -0.32.
- L4 fau·NCE: 50 units, 1 at epoch 0; mean Δdev +0.0059 bits (relative +0.00094); mean unit Δtest unified +0.0011, native -0.0021; Spearman Δdev~Δtest native over epoch>0 units -0.20.
- L4 federici·CS_SINGLE: 25 units, 6 at epoch 0; mean Δdev +0.0011 bits (relative +0.00014); mean unit Δtest unified -0.0010, native +0.0001; Spearman Δdev~Δtest native over epoch>0 units -0.15.
- L4 federici·NCE: 25 units, 0 at epoch 0; mean Δdev +0.0010 bits (relative +0.00013); mean unit Δtest unified -0.0001, native +0.0039; Spearman Δdev~Δtest native over epoch>0 units +0.66.
- L1–L3 RS·dtu·CS_SINGLE·cbramod·residual_aligned_pretrained (44 identities, all 10 units): ‖r‖/‖u‖ +1.0261, mean ‖r∥‖ / mean ‖r‖ 0.685 with signed parallel coefficient mean +0.4120, ‖r⊥‖/‖u‖ +0.6599, post-normalisation change +0.2903, angle +17.441°; queries whose true-candidate rank changed: unified +0.821, native +0.778; ΔR unified -0.0210, native -0.0221; native prediction relative difference +0.2723.
- L1–L3 RS·dtu·CS_SINGLE·cbramod·residual_aligned_random (44 identities, all 10 units): ‖r‖/‖u‖ +0.2462, mean ‖r∥‖ / mean ‖r‖ 0.667 with signed parallel coefficient mean +0.0083, ‖r⊥‖/‖u‖ +0.1608, post-normalisation change +0.1688, angle +9.871°; queries whose true-candidate rank changed: unified +0.768, native +0.627; ΔR unified -0.0161, native -0.0088; native prediction relative difference +0.1602.
- L1–L3 RS·dtu·CS_SINGLE·reve·residual_aligned_pretrained (44 identities, all 10 units): ‖r‖/‖u‖ +0.1119, mean ‖r∥‖ / mean ‖r‖ 0.692 with signed parallel coefficient mean +0.0061, ‖r⊥‖/‖u‖ +0.0702, post-normalisation change +0.0670, angle +3.853°; queries whose true-candidate rank changed: unified +0.667, native +0.568; ΔR unified -0.0025, native +0.0007; native prediction relative difference +0.0541.
- L1–L3 RS·dtu·CS_SINGLE·reve·residual_aligned_random (44 identities, all 10 units): ‖r‖/‖u‖ +0.0887, mean ‖r∥‖ / mean ‖r‖ 0.733 with signed parallel coefficient mean -0.0059, ‖r⊥‖/‖u‖ +0.0512, post-normalisation change +0.0519, angle +2.977°; queries whose true-candidate rank changed: unified +0.514, native +0.460; ΔR unified +0.0018, native +0.0013; native prediction relative difference +0.0418.
- L1–L3 RS·dtu·CS_SINGLE·small_capacity_branch·residual_small_capacity (44 identities, all 10 units): ‖r‖/‖u‖ +1.3068, mean ‖r∥‖ / mean ‖r‖ 0.779 with signed parallel coefficient mean +0.8980, ‖r⊥‖/‖u‖ +0.6948, post-normalisation change +0.3488, angle +20.366°; queries whose true-candidate rank changed: unified +0.915, native +0.871; ΔR unified -0.0866, native -0.0544; native prediction relative difference +0.2880.
- L1–L3 RS·dtu·NCE·cbramod·residual_aligned_pretrained (44 identities, all 10 units): ‖r‖/‖u‖ +0.0441, mean ‖r∥‖ / mean ‖r‖ 0.763 with signed parallel coefficient mean +0.0300, ‖r⊥‖/‖u‖ +0.0259, post-normalisation change +0.0248, angle +1.421°; queries whose true-candidate rank changed: unified +0.244, native +0.395; ΔR unified +0.0004, native +0.0025; native prediction relative difference +0.0248.
- L1–L3 RS·dtu·NCE·cbramod·residual_aligned_random (44 identities, all 10 units): ‖r‖/‖u‖ +0.0434, mean ‖r∥‖ / mean ‖r‖ 0.792 with signed parallel coefficient mean +0.0308, ‖r⊥‖/‖u‖ +0.0242, post-normalisation change +0.0232, angle +1.331°; queries whose true-candidate rank changed: unified +0.258, native +0.392; ΔR unified +0.0003, native +0.0022; native prediction relative difference +0.0232.
- L1–L3 RS·dtu·NCE·reve·residual_aligned_pretrained (44 identities, all 10 units): ‖r‖/‖u‖ +0.0492, mean ‖r∥‖ / mean ‖r‖ 0.792 with signed parallel coefficient mean +0.0328, ‖r⊥‖/‖u‖ +0.0275, post-normalisation change +0.0263, angle +1.507°; queries whose true-candidate rank changed: unified +0.292, native +0.370; ΔR unified +0.0002, native +0.0029; native prediction relative difference +0.0263.
- L1–L3 RS·dtu·NCE·reve·residual_aligned_random (44 identities, all 10 units): ‖r‖/‖u‖ +0.0348, mean ‖r∥‖ / mean ‖r‖ 0.737 with signed parallel coefficient mean +0.0220, ‖r⊥‖/‖u‖ +0.0212, post-normalisation change +0.0207, angle +1.186°; queries whose true-candidate rank changed: unified +0.208, native +0.372; ΔR unified +0.0001, native +0.0025; native prediction relative difference +0.0207.
- L1–L3 RS·dtu·NCE·small_capacity_branch·residual_small_capacity (44 identities, all 10 units): ‖r‖/‖u‖ +0.0351, mean ‖r∥‖ / mean ‖r‖ 0.491 with signed parallel coefficient mean +0.0125, ‖r⊥‖/‖u‖ +0.0290, post-normalisation change +0.0284, angle +1.629°; queries whose true-candidate rank changed: unified +0.551, native +0.524; ΔR unified +0.0158, native +0.0125; native prediction relative difference +0.0284.
- L1–L3 RS·fau·CS_SINGLE·cbramod·residual_aligned_pretrained (67 identities, all 10 units): ‖r‖/‖u‖ +0.1299, mean ‖r∥‖ / mean ‖r‖ 0.647 with signed parallel coefficient mean +0.0385, ‖r⊥‖/‖u‖ +0.0887, post-normalisation change +0.0757, angle +4.371°; queries whose true-candidate rank changed: unified +0.468, native +0.365; ΔR unified -0.0016, native -0.0013; native prediction relative difference +0.0621.
- L1–L3 RS·fau·CS_SINGLE·cbramod·residual_aligned_random (67 identities, all 10 units): ‖r‖/‖u‖ +0.0803, mean ‖r∥‖ / mean ‖r‖ 0.578 with signed parallel coefficient mean +0.0126, ‖r⊥‖/‖u‖ +0.0594, post-normalisation change +0.0565, angle +3.246°; queries whose true-candidate rank changed: unified +0.382, native +0.291; ΔR unified -0.0005, native -0.0012; native prediction relative difference +0.0372.
- L1–L3 RS·fau·CS_SINGLE·reve·residual_aligned_pretrained (67 identities, all 10 units): ‖r‖/‖u‖ +0.0434, mean ‖r∥‖ / mean ‖r‖ 0.622 with signed parallel coefficient mean +0.0000, ‖r⊥‖/‖u‖ +0.0306, post-normalisation change +0.0299, angle +1.716°; queries whose true-candidate rank changed: unified +0.359, native +0.274; ΔR unified +0.0000, native -0.0002; native prediction relative difference +0.0207.
- L1–L3 RS·fau·CS_SINGLE·reve·residual_aligned_random (67 identities, all 10 units): ‖r‖/‖u‖ +0.0529, mean ‖r∥‖ / mean ‖r‖ 0.552 with signed parallel coefficient mean -0.0015, ‖r⊥‖/‖u‖ +0.0398, post-normalisation change +0.0398, angle +2.281°; queries whose true-candidate rank changed: unified +0.353, native +0.266; ΔR unified -0.0003, native -0.0003; native prediction relative difference +0.0212.
- L1–L3 RS·fau·CS_SINGLE·small_capacity_branch·residual_small_capacity (67 identities, all 10 units): ‖r‖/‖u‖ +0.8211, mean ‖r∥‖ / mean ‖r‖ 0.682 with signed parallel coefficient mean +0.4836, ‖r⊥‖/‖u‖ +0.5231, post-normalisation change +0.3013, angle +17.476°; queries whose true-candidate rank changed: unified +0.793, native +0.716; ΔR unified -0.0185, native -0.0211; native prediction relative difference +0.2144.
- L1–L3 RS·fau·NCE·cbramod·residual_aligned_pretrained (67 identities, all 10 units): ‖r‖/‖u‖ +0.0329, mean ‖r∥‖ / mean ‖r‖ 0.673 with signed parallel coefficient mean +0.0198, ‖r⊥‖/‖u‖ +0.0208, post-normalisation change +0.0204, angle +1.167°; queries whose true-candidate rank changed: unified +0.195, native +0.443; ΔR unified -0.0004, native -0.0044; native prediction relative difference +0.0204.
- L1–L3 RS·fau·NCE·cbramod·residual_aligned_random (67 identities, all 10 units): ‖r‖/‖u‖ +0.0427, mean ‖r∥‖ / mean ‖r‖ 0.791 with signed parallel coefficient mean +0.0338, ‖r⊥‖/‖u‖ +0.0240, post-normalisation change +0.0231, angle +1.326°; queries whose true-candidate rank changed: unified +0.197, native +0.421; ΔR unified -0.0000, native -0.0034; native prediction relative difference +0.0231.
- L1–L3 RS·fau·NCE·reve·residual_aligned_pretrained (67 identities, all 10 units): ‖r‖/‖u‖ +0.0430, mean ‖r∥‖ / mean ‖r‖ 0.728 with signed parallel coefficient mean +0.0310, ‖r⊥‖/‖u‖ +0.0253, post-normalisation change +0.0246, angle +1.410°; queries whose true-candidate rank changed: unified +0.194, native +0.389; ΔR unified +0.0004, native -0.0027; native prediction relative difference +0.0246.
- L1–L3 RS·fau·NCE·reve·residual_aligned_random (67 identities, all 10 units): ‖r‖/‖u‖ +0.0479, mean ‖r∥‖ / mean ‖r‖ 0.741 with signed parallel coefficient mean +0.0351, ‖r⊥‖/‖u‖ +0.0272, post-normalisation change +0.0262, angle +1.500°; queries whose true-candidate rank changed: unified +0.182, native +0.432; ΔR unified -0.0002, native -0.0043; native prediction relative difference +0.0262.
- L1–L3 RS·fau·NCE·small_capacity_branch·residual_small_capacity (67 identities, all 10 units): ‖r‖/‖u‖ +0.0388, mean ‖r∥‖ / mean ‖r‖ 0.754 with signed parallel coefficient mean +0.0258, ‖r⊥‖/‖u‖ +0.0235, post-normalisation change +0.0229, angle +1.311°; queries whose true-candidate rank changed: unified +0.578, native +0.582; ΔR unified +0.0066, native +0.0039; native prediction relative difference +0.0229.
- L1–L3 RS·federici·CS_SINGLE·cbramod·residual_aligned_pretrained (86 identities, all 5 units): ‖r‖/‖u‖ +0.1174, mean ‖r∥‖ / mean ‖r‖ 0.534 with signed parallel coefficient mean +0.0026, ‖r⊥‖/‖u‖ +0.0891, post-normalisation change +0.0889, angle +5.100°; queries whose true-candidate rank changed: unified +0.671, native +0.459; ΔR unified +0.0002, native +0.0000; native prediction relative difference +0.0201.
- L1–L3 RS·federici·CS_SINGLE·cbramod·residual_aligned_random (86 identities, all 5 units): ‖r‖/‖u‖ +0.0493, mean ‖r∥‖ / mean ‖r‖ 0.555 with signed parallel coefficient mean -0.0008, ‖r⊥‖/‖u‖ +0.0374, post-normalisation change +0.0375, angle +2.149°; queries whose true-candidate rank changed: unified +0.461, native +0.247; ΔR unified +0.0001, native +0.0000; native prediction relative difference +0.0083.
- L1–L3 RS·federici·CS_SINGLE·reve·residual_aligned_pretrained (86 identities, all 5 units): ‖r‖/‖u‖ +0.1086, mean ‖r∥‖ / mean ‖r‖ 0.658 with signed parallel coefficient mean +0.0189, ‖r⊥‖/‖u‖ +0.0733, post-normalisation change +0.0356, angle +2.052°; queries whose true-candidate rank changed: unified +0.501, native +0.295; ΔR unified -0.0005, native -0.0000; native prediction relative difference +0.0089.
- L1–L3 RS·federici·CS_SINGLE·reve·residual_aligned_random (86 identities, all 5 units): ‖r‖/‖u‖ +0.0201, mean ‖r∥‖ / mean ‖r‖ 0.728 with signed parallel coefficient mean -0.0003, ‖r⊥‖/‖u‖ +0.0121, post-normalisation change +0.0121, angle +0.696°; queries whose true-candidate rank changed: unified +0.249, native +0.115; ΔR unified -0.0001, native +0.0000; native prediction relative difference +0.0029.
- L1–L3 RS·federici·CS_SINGLE·small_capacity_branch·residual_small_capacity (86 identities, all 5 units): ‖r‖/‖u‖ +0.6155, mean ‖r∥‖ / mean ‖r‖ 0.629 with signed parallel coefficient mean +0.2403, ‖r⊥‖/‖u‖ +0.4213, post-normalisation change +0.3085, angle +18.068°; queries whose true-candidate rank changed: unified +0.924, native +0.806; ΔR unified -0.0021, native -0.0001; native prediction relative difference +0.0823.
- L1–L3 RS·federici·NCE·cbramod·residual_aligned_pretrained (86 identities, all 5 units): ‖r‖/‖u‖ +0.0340, mean ‖r∥‖ / mean ‖r‖ 0.966 with signed parallel coefficient mean -0.0075, ‖r⊥‖/‖u‖ +0.0082, post-normalisation change +0.0082, angle +0.471°; queries whose true-candidate rank changed: unified +0.247, native +0.696; ΔR unified +0.0009, native +0.0023; native prediction relative difference +0.0082.
- L1–L3 RS·federici·NCE·cbramod·residual_aligned_random (86 identities, all 5 units): ‖r‖/‖u‖ +0.0281, mean ‖r∥‖ / mean ‖r‖ 0.961 with signed parallel coefficient mean -0.0150, ‖r⊥‖/‖u‖ +0.0074, post-normalisation change +0.0075, angle +0.432°; queries whose true-candidate rank changed: unified +0.146, native +0.717; ΔR unified +0.0000, native +0.0036; native prediction relative difference +0.0075.
- L1–L3 RS·federici·NCE·reve·residual_aligned_pretrained (86 identities, all 5 units): ‖r‖/‖u‖ +0.0217, mean ‖r∥‖ / mean ‖r‖ 0.928 with signed parallel coefficient mean -0.0074, ‖r⊥‖/‖u‖ +0.0063, post-normalisation change +0.0064, angle +0.367°; queries whose true-candidate rank changed: unified +0.350, native +0.835; ΔR unified +0.0009, native +0.0027; native prediction relative difference +0.0064.
- L1–L3 RS·federici·NCE·reve·residual_aligned_random (86 identities, all 5 units): ‖r‖/‖u‖ +0.0325, mean ‖r∥‖ / mean ‖r‖ 0.964 with signed parallel coefficient mean -0.0097, ‖r⊥‖/‖u‖ +0.0080, post-normalisation change +0.0082, angle +0.468°; queries whose true-candidate rank changed: unified +0.129, native +0.764; ΔR unified +0.0000, native +0.0035; native prediction relative difference +0.0082.
- L1–L3 RS·federici·NCE·small_capacity_branch·residual_small_capacity (86 identities, all 5 units): ‖r‖/‖u‖ +0.0226, mean ‖r∥‖ / mean ‖r‖ 0.896 with signed parallel coefficient mean -0.0019, ‖r⊥‖/‖u‖ +0.0078, post-normalisation change +0.0079, angle +0.453°; queries whose true-candidate rank changed: unified +0.554, native +0.861; ΔR unified +0.0014, native +0.0045; native prediction relative difference +0.0079.

### 12.2 Working judgement (provisional; applies to these recipes and seed 3401 only)

- Every SC number in the older tables is an increment over a remapped base. Whether a variant improves on what the base itself delivers is read from §5 (FN-DIRECT-SC); §5 is the same-system comparison asked for in docs/03 §1. Against L0, only `local_only` and `local_refit_capacity` are access-matched.
- RS at epoch 0 is the base. A selected epoch > 0 is a training-side choice; whether it changed the representation, the predictions or the risk is read from §6–§9, not from the selected epoch.
- RS·dtu·CS_SINGLE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.2903 (angle +17.44°; ‖r‖/‖u‖ +1.0261); the true-candidate rank changes in 0.82 (unified) / 0.78 (native) of the queries; the identity-level ΔR is -0.0210 [-0.039, -0.003] unified and -0.0221 [-0.042, -0.002] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0221 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·CS_SINGLE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.1688 (angle +9.87°; ‖r‖/‖u‖ +0.2462); the true-candidate rank changes in 0.77 (unified) / 0.63 (native) of the queries; the identity-level ΔR is -0.0161 [-0.028, -0.005] unified and -0.0088 [-0.017, -0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0161 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·CS_SINGLE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0670 (angle +3.85°; ‖r‖/‖u‖ +0.1119); the true-candidate rank changes in 0.67 (unified) / 0.57 (native) of the queries; the identity-level ΔR is -0.0025 [-0.006, +0.001] unified and +0.0007 [-0.001, +0.002] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0025 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·CS_SINGLE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0519 (angle +2.98°; ‖r‖/‖u‖ +0.0887); the true-candidate rank changes in 0.51 (unified) / 0.46 (native) of the queries; the identity-level ΔR is +0.0018 [-0.000, +0.004] unified and +0.0013 [-0.000, +0.003] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0018 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·CS_SINGLE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.3488 (angle +20.37°; ‖r‖/‖u‖ +1.3068); the true-candidate rank changes in 0.91 (unified) / 0.87 (native) of the queries; the identity-level ΔR is -0.0866 [-0.105, -0.069] unified and -0.0544 [-0.067, -0.042] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0866 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·NCE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0248 (angle +1.42°; ‖r‖/‖u‖ +0.0441); the true-candidate rank changes in 0.24 (unified) / 0.39 (native) of the queries; the identity-level ΔR is +0.0004 [-0.000, +0.001] unified and +0.0025 [+0.001, +0.004] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0025 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·NCE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.0232 (angle +1.33°; ‖r‖/‖u‖ +0.0434); the true-candidate rank changes in 0.26 (unified) / 0.39 (native) of the queries; the identity-level ΔR is +0.0003 [-0.001, +0.001] unified and +0.0022 [+0.001, +0.004] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0022 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·NCE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0263 (angle +1.51°; ‖r‖/‖u‖ +0.0492); the true-candidate rank changes in 0.29 (unified) / 0.37 (native) of the queries; the identity-level ΔR is +0.0002 [-0.001, +0.001] unified and +0.0029 [+0.001, +0.004] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0029 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·NCE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0207 (angle +1.19°; ‖r‖/‖u‖ +0.0348); the true-candidate rank changes in 0.21 (unified) / 0.37 (native) of the queries; the identity-level ΔR is +0.0001 [-0.000, +0.001] unified and +0.0025 [+0.001, +0.004] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0025 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·dtu·NCE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.0284 (angle +1.63°; ‖r‖/‖u‖ +0.0351); the true-candidate rank changes in 0.55 (unified) / 0.52 (native) of the queries; the identity-level ΔR is +0.0158 [+0.006, +0.026] unified and +0.0125 [-0.001, +0.026] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0158 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·CS_SINGLE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0757 (angle +4.37°; ‖r‖/‖u‖ +0.1299); the true-candidate rank changes in 0.47 (unified) / 0.37 (native) of the queries; the identity-level ΔR is -0.0016 [-0.004, +0.001] unified and -0.0013 [-0.004, +0.001] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0016 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·CS_SINGLE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.0565 (angle +3.25°; ‖r‖/‖u‖ +0.0803); the true-candidate rank changes in 0.38 (unified) / 0.29 (native) of the queries; the identity-level ΔR is -0.0005 [-0.002, +0.001] unified and -0.0012 [-0.003, +0.001] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0012 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·CS_SINGLE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0299 (angle +1.72°; ‖r‖/‖u‖ +0.0434); the true-candidate rank changes in 0.36 (unified) / 0.27 (native) of the queries; the identity-level ΔR is +0.0000 [-0.001, +0.001] unified and -0.0002 [-0.001, +0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0002 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·CS_SINGLE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0398 (angle +2.28°; ‖r‖/‖u‖ +0.0529); the true-candidate rank changes in 0.35 (unified) / 0.27 (native) of the queries; the identity-level ΔR is -0.0003 [-0.001, +0.000] unified and -0.0003 [-0.001, +0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0003 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·CS_SINGLE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.3013 (angle +17.48°; ‖r‖/‖u‖ +0.8211); the true-candidate rank changes in 0.79 (unified) / 0.72 (native) of the queries; the identity-level ΔR is -0.0185 [-0.032, -0.005] unified and -0.0211 [-0.029, -0.013] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0211 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·NCE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0204 (angle +1.17°; ‖r‖/‖u‖ +0.0329); the true-candidate rank changes in 0.20 (unified) / 0.44 (native) of the queries; the identity-level ΔR is -0.0004 [-0.001, +0.000] unified and -0.0044 [-0.006, -0.003] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0044 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·NCE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.0231 (angle +1.33°; ‖r‖/‖u‖ +0.0427); the true-candidate rank changes in 0.20 (unified) / 0.42 (native) of the queries; the identity-level ΔR is -0.0000 [-0.001, +0.001] unified and -0.0034 [-0.005, -0.002] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0034 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·NCE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0246 (angle +1.41°; ‖r‖/‖u‖ +0.0430); the true-candidate rank changes in 0.19 (unified) / 0.39 (native) of the queries; the identity-level ΔR is +0.0004 [-0.000, +0.001] unified and -0.0027 [-0.004, -0.001] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0027 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·NCE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0262 (angle +1.50°; ‖r‖/‖u‖ +0.0479); the true-candidate rank changes in 0.18 (unified) / 0.43 (native) of the queries; the identity-level ΔR is -0.0002 [-0.002, +0.001] unified and -0.0043 [-0.006, -0.003] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0043 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·fau·NCE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.0229 (angle +1.31°; ‖r‖/‖u‖ +0.0388); the true-candidate rank changes in 0.58 (unified) / 0.58 (native) of the queries; the identity-level ΔR is +0.0066 [+0.001, +0.012] unified and +0.0039 [-0.005, +0.013] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0066 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·CS_SINGLE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0889 (angle +5.10°; ‖r‖/‖u‖ +0.1174); the true-candidate rank changes in 0.67 (unified) / 0.46 (native) of the queries; the identity-level ΔR is +0.0002 [-0.001, +0.002] unified and +0.0000 [-0.000, +0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0002 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·CS_SINGLE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.0375 (angle +2.15°; ‖r‖/‖u‖ +0.0493); the true-candidate rank changes in 0.46 (unified) / 0.25 (native) of the queries; the identity-level ΔR is +0.0001 [-0.004, +0.004] unified and +0.0000 [-0.000, +0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0001 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·CS_SINGLE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0356 (angle +2.05°; ‖r‖/‖u‖ +0.1086); the true-candidate rank changes in 0.50 (unified) / 0.30 (native) of the queries; the identity-level ΔR is -0.0005 [-0.004, +0.003] unified and -0.0000 [-0.000, -0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0005 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·CS_SINGLE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0121 (angle +0.70°; ‖r‖/‖u‖ +0.0201); the true-candidate rank changes in 0.25 (unified) / 0.11 (native) of the queries; the identity-level ΔR is -0.0001 [-0.004, +0.004] unified and +0.0000 [-0.000, +0.000] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0001 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·CS_SINGLE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.3085 (angle +18.07°; ‖r‖/‖u‖ +0.6155); the true-candidate rank changes in 0.92 (unified) / 0.81 (native) of the queries; the identity-level ΔR is -0.0021 [-0.010, +0.006] unified and -0.0001 [-0.001, +0.001] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0021 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·NCE·cbramod·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0082 (angle +0.47°; ‖r‖/‖u‖ +0.0340); the true-candidate rank changes in 0.25 (unified) / 0.70 (native) of the queries; the identity-level ΔR is +0.0009 [-0.000, +0.002] unified and +0.0023 [-0.001, +0.005] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0023 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·NCE·cbramod·residual_aligned_random: the selected residual moves the normalised representation by +0.0075 (angle +0.43°; ‖r‖/‖u‖ +0.0281); the true-candidate rank changes in 0.15 (unified) / 0.72 (native) of the queries; the identity-level ΔR is +0.0000 [-0.000, +0.000] unified and +0.0036 [-0.000, +0.007] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0036 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·NCE·reve·residual_aligned_pretrained: the selected residual moves the normalised representation by +0.0064 (angle +0.37°; ‖r‖/‖u‖ +0.0217); the true-candidate rank changes in 0.35 (unified) / 0.83 (native) of the queries; the identity-level ΔR is +0.0009 [+0.000, +0.002] unified and +0.0027 [-0.001, +0.006] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0027 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·NCE·reve·residual_aligned_random: the selected residual moves the normalised representation by +0.0082 (angle +0.47°; ‖r‖/‖u‖ +0.0325); the true-candidate rank changes in 0.13 (unified) / 0.76 (native) of the queries; the identity-level ΔR is +0.0000 [-0.000, +0.000] unified and +0.0035 [-0.000, +0.007] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0035 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.
- RS·federici·NCE·small_capacity_branch·residual_small_capacity: the selected residual moves the normalised representation by +0.0079 (angle +0.45°; ‖r‖/‖u‖ +0.0226); the true-candidate rank changes in 0.55 (unified) / 0.86 (native) of the queries; the identity-level ΔR is +0.0014 [+0.000, +0.003] unified and +0.0045 [+0.001, +0.008] native (pointwise). So the representation and the rankings change while the identity-level point estimates of ΔR stay within ±0.0045 bits here; the pointwise intervals above allow larger changes. All FM-context configurations are now included; this statement describes this configuration only.

### 12.3 Competing explanations for RS ΔR ≈ 0 and the layer that separates them

| explanation | evidence that separates it | status |
|---|---|---|
| normalisation removes most of r (radial residual, D34) | L1 parallel share, L2 post-normalisation change and angle | computed for RS·dtu·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·dtu·CS_SINGLE·cbramod·residual_aligned_random, RS·dtu·CS_SINGLE·reve·residual_aligned_pretrained, RS·dtu·CS_SINGLE·reve·residual_aligned_random, RS·dtu·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·dtu·NCE·cbramod·residual_aligned_pretrained, RS·dtu·NCE·cbramod·residual_aligned_random, RS·dtu·NCE·reve·residual_aligned_pretrained, RS·dtu·NCE·reve·residual_aligned_random, RS·dtu·NCE·small_capacity_branch·residual_small_capacity, RS·fau·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·fau·CS_SINGLE·cbramod·residual_aligned_random, RS·fau·CS_SINGLE·reve·residual_aligned_pretrained, RS·fau·CS_SINGLE·reve·residual_aligned_random, RS·fau·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·fau·NCE·cbramod·residual_aligned_pretrained, RS·fau·NCE·cbramod·residual_aligned_random, RS·fau·NCE·reve·residual_aligned_pretrained, RS·fau·NCE·reve·residual_aligned_random, RS·fau·NCE·small_capacity_branch·residual_small_capacity, RS·federici·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·federici·CS_SINGLE·cbramod·residual_aligned_random, RS·federici·CS_SINGLE·reve·residual_aligned_pretrained, RS·federici·CS_SINGLE·reve·residual_aligned_random, RS·federici·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·federici·NCE·cbramod·residual_aligned_pretrained, RS·federici·NCE·cbramod·residual_aligned_random, RS·federici·NCE·reve·residual_aligned_pretrained, RS·federici·NCE·reve·residual_aligned_random, RS·federici·NCE·small_capacity_branch·residual_small_capacity; all30 configurations have complete functional outputs |
| readout invariance: refitted bridge / temperature absorb the change | L3 unified prediction difference and rank changes vs the L2 change; τ ratios (§7) | τ ratios from the saved records for all units; per-query part computed for RS·dtu·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·dtu·CS_SINGLE·cbramod·residual_aligned_random, RS·dtu·CS_SINGLE·reve·residual_aligned_pretrained, RS·dtu·CS_SINGLE·reve·residual_aligned_random, RS·dtu·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·dtu·NCE·cbramod·residual_aligned_pretrained, RS·dtu·NCE·cbramod·residual_aligned_random, RS·dtu·NCE·reve·residual_aligned_pretrained, RS·dtu·NCE·reve·residual_aligned_random, RS·dtu·NCE·small_capacity_branch·residual_small_capacity, RS·fau·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·fau·CS_SINGLE·cbramod·residual_aligned_random, RS·fau·CS_SINGLE·reve·residual_aligned_pretrained, RS·fau·CS_SINGLE·reve·residual_aligned_random, RS·fau·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·fau·NCE·cbramod·residual_aligned_pretrained, RS·fau·NCE·cbramod·residual_aligned_random, RS·fau·NCE·reve·residual_aligned_pretrained, RS·fau·NCE·reve·residual_aligned_random, RS·fau·NCE·small_capacity_branch·residual_small_capacity, RS·federici·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·federici·CS_SINGLE·cbramod·residual_aligned_random, RS·federici·CS_SINGLE·reve·residual_aligned_pretrained, RS·federici·CS_SINGLE·reve·residual_aligned_random, RS·federici·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·federici·NCE·cbramod·residual_aligned_pretrained, RS·federici·NCE·cbramod·residual_aligned_random, RS·federici·NCE·reve·residual_aligned_pretrained, RS·federici·NCE·reve·residual_aligned_random, RS·federici·NCE·small_capacity_branch·residual_small_capacity; all30 configurations have complete functional outputs |
| the representation changes but carries no acoustic increment | ΔR ≈ 0 (§6, identity level, all units) while L2 / L3 changes are non-zero | identity-level ΔR answered for all units; the L2 / L3 side computed for RS·dtu·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·dtu·CS_SINGLE·cbramod·residual_aligned_random, RS·dtu·CS_SINGLE·reve·residual_aligned_pretrained, RS·dtu·CS_SINGLE·reve·residual_aligned_random, RS·dtu·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·dtu·NCE·cbramod·residual_aligned_pretrained, RS·dtu·NCE·cbramod·residual_aligned_random, RS·dtu·NCE·reve·residual_aligned_pretrained, RS·dtu·NCE·reve·residual_aligned_random, RS·dtu·NCE·small_capacity_branch·residual_small_capacity, RS·fau·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·fau·CS_SINGLE·cbramod·residual_aligned_random, RS·fau·CS_SINGLE·reve·residual_aligned_pretrained, RS·fau·CS_SINGLE·reve·residual_aligned_random, RS·fau·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·fau·NCE·cbramod·residual_aligned_pretrained, RS·fau·NCE·cbramod·residual_aligned_random, RS·fau·NCE·reve·residual_aligned_pretrained, RS·fau·NCE·reve·residual_aligned_random, RS·fau·NCE·small_capacity_branch·residual_small_capacity, RS·federici·CS_SINGLE·cbramod·residual_aligned_pretrained, RS·federici·CS_SINGLE·cbramod·residual_aligned_random, RS·federici·CS_SINGLE·reve·residual_aligned_pretrained, RS·federici·CS_SINGLE·reve·residual_aligned_random, RS·federici·CS_SINGLE·small_capacity_branch·residual_small_capacity, RS·federici·NCE·cbramod·residual_aligned_pretrained, RS·federici·NCE·cbramod·residual_aligned_random, RS·federici·NCE·reve·residual_aligned_pretrained, RS·federici·NCE·reve·residual_aligned_random, RS·federici·NCE·small_capacity_branch·residual_small_capacity; all30 configurations have complete functional outputs |
| cross-person selection mismatch: development gains do not carry to new listeners | L4: Δdev vs Δtest per unit (§7) | answered from saved records |

### 12.4 Next intervention

- Completed: the per-unit evaluator has0 pending units (`private/auditory_alignment_v3/aln34/complement_function_units.txt`; about 0.0 GPU-minutes, range 0.0–0.0; assumption-based), the final CPU aggregation1044112 is complete. No retraining; old checkpoints were only read.
- Each unit carries its own reproduction check; a flagged unit is reported, not merged.
- When the ADDENDUM_11 panel completes, L4 can be repeated on seeds 3407 / 3413 (NCE).
- SC per-query predictions would need a closed-form refit with the saved PCA bases and alphas on the same training rows (FM forwards for the FM variants). They are not needed for this card's questions and are not scheduled.

### 12.5 Reuse and execution

- Reused unit records (seed 3401): {'FM|complete': 50, 'L0|complete': 50, 'L1|complete': 25, 'RS|complete': 250, 'SC|complete': 100, 'TF|complete': 100}. SC: 100 records holding 600 variant evaluations. RS checkpoints read: 250.
- FM weight files were hashed (§10). Evaluator runs (v2): RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x10; RS|dtu|CS_SINGLE|cbramod|residual_aligned_random full on NVIDIA A40 x10; RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained full on NVIDIA A40 x10; RS|dtu|CS_SINGLE|reve|residual_aligned_random full on NVIDIA A40 x9; RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity full on NVIDIA A40 x10; RS|dtu|NCE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x10; RS|dtu|NCE|cbramod|residual_aligned_random full on NVIDIA A40 x10; RS|dtu|NCE|reve|residual_aligned_pretrained full on NVIDIA A40 x10; RS|dtu|NCE|reve|residual_aligned_random full on NVIDIA A40 x10; RS|dtu|NCE|small_capacity_branch|residual_small_capacity full on NVIDIA A40 x7; RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x9; RS|fau|CS_SINGLE|cbramod|residual_aligned_random full on NVIDIA A40 x9; RS|fau|CS_SINGLE|reve|residual_aligned_pretrained full on NVIDIA A40 x9; RS|fau|CS_SINGLE|reve|residual_aligned_random full on NVIDIA A40 x9; RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity full on NVIDIA A40 x9; RS|fau|NCE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x10; RS|fau|NCE|cbramod|residual_aligned_random full on NVIDIA A40 x10; RS|fau|NCE|reve|residual_aligned_pretrained full on NVIDIA A40 x10; RS|fau|NCE|reve|residual_aligned_random full on NVIDIA A40 x10; RS|fau|NCE|small_capacity_branch|residual_small_capacity full on NVIDIA A40 x9; RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x4; RS|federici|CS_SINGLE|cbramod|residual_aligned_random full on NVIDIA A40 x4; RS|federici|CS_SINGLE|reve|residual_aligned_pretrained full on NVIDIA A40 x4; RS|federici|CS_SINGLE|reve|residual_aligned_random full on NVIDIA A40 x2; RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity full on cpu x5; RS|federici|NCE|cbramod|residual_aligned_pretrained full on NVIDIA A40 x5; RS|federici|NCE|cbramod|residual_aligned_random dev_only on cpu x1; RS|federici|NCE|cbramod|residual_aligned_random full on NVIDIA A40 x5; RS|federici|NCE|reve|residual_aligned_pretrained full on NVIDIA A40 x5; RS|federici|NCE|reve|residual_aligned_random dev_only on cpu x1; RS|federici|NCE|reve|residual_aligned_random full on NVIDIA A40 x5; RS|federici|NCE|reve|residual_aligned_random tiny on cpu x1; RS|federici|NCE|small_capacity_branch|residual_small_capacity full on cpu x5; each read its unit checkpoint and its base checkpoint. FM-context runs: cbramod residual_aligned_pretrained: pretrained weights read; cbramod residual_aligned_random: random init regenerated from the seed, no pretrained weights read; reve residual_aligned_pretrained: pretrained weights read; reve residual_aligned_random: random init regenerated from the seed, no pretrained weights read.
- New CPU computation in this lane: this aggregation; the evaluator runs listed in §9. GPU continuation:224 evaluations completed by1043886/1043887; no training was repeated.

### 12.6 Not decided here

- Scheduling the listed GPU units within the 10-GPU cap is an operational step. Nothing in this report waits on a researcher decision.

## Appendix: notes


## Report-status correction, 2026-10-17

The unchanged v2 report generator contained pre-launch CPU-only/pending-GPU sentences. This report-only amendment corrects those stale execution statements after all234 nonzero-epoch outputs passed the original reproduction checks. No numeric result, interval, selected configuration, source code hash or historical note was changed. The generated v2 document, hashes and exact replacement counts are retained in private/auditory_alignment_v3/aln34/complement_final_20261017/.
