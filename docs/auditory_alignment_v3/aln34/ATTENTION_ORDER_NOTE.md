# R34_ATTENTION_ORDER — analysis note (candidate order in the learned attention integrator)

Written 2026-10-16, 19:50–20:10 CEST. It was written **before any value it covers was computed**: no paired-order value existed when it was written, and none exists yet.

- Template: package `templates/ANALYSIS_NOTE.md`.
- Status: a **correction track with versioned provenance** (`evaluation_version = aln34_attention_order_v1`). The antisymmetric scorer is exploratory.
- Old results are kept unchanged: D_ATTENTION_RESULTS.md, d_lag.json, the private per-identity file and every unit record. Nothing is overwritten.

Sources:
- card `R34_ATTENTION_ORDER` (package `plans/comparison_cards.json`, sha256 `b2435220…`);
- package docs/04 §B (`f40ba55a…`);
- `configs/adaptation_and_fusion.yaml` → `attention` (`dfff5e85…`). The `attention` block says:
  - `orders: both_A_B_and_B_A`;
  - `new_logit: half_h_d_minus_h_minus_d`;
  - `tie_credit: 0.5`;
  - `refit: head_only_when_possible`;
  - windows 5 / 10 / 20 s;
- reference `src/aln34_reference/attention.py` (`e2b50c93…`, matches the package SHA256SUMS).

## 1. Question and analysis object

**Question (card):** does the D_ATTENTION integrator comparison (`mean_score` → learned integrator) still hold once the candidate order is handled by paired swapping?

**Object:** the D_ATTENTION `lag_local_tokens` models. Each trained configuration is one model; its `learned_temporal` row is a derived record of the same model (`shared_model_with`).

| seed | trained models (`mean_score` units) | derived `learned_temporal` records | cells |
|---|---|---|---|
| 3401 | 100 | 100 | FAU, DTU × {attended_alignment NCE / CS_SINGLE, selection_only SELECTION_CE, alignment_plus_selection NCE / CS_SINGLE} × 5 subject folds × 2 content folds |
| 3407 | 40 | 40 | FAU, DTU × {attended_alignment, alignment_plus_selection} NCE × 10 folds |
| 3413 | 40 | 40 | as 3407 |

All 360 records are `complete` and all 180 used `code_group attention`, `code_hash 988bda85c8d8e404`, on A40 GPUs.

## 2. Audit of the legacy evaluation

The audit covers `auditory_alignment_v3/run_attention.py`, sha256 `6c386954…`, read-only.

### Windows and scores

- **Windows:** 5 / 10 / 20 s = 1 / 2 / 4 consecutive 5 s segments of one participant's trial (same participant + trial code, `e0` step = segment length).
  - Windows do not overlap and never cross trials. The window lengths are the same for every group.
  - Training windows: training participants' competing-speech segments, roles fit + es.
  - Test windows: the test-fold participants' test-content segments.
- **Per-segment score difference:** d = score(attended) − score(ignored).
  - Both readouts are `auditory_alignment.evaluate.Readouts` fitted on the training participants' single-speaker fit + es segments (400 subsampled, rng `seed + 1000`).
  - unified: the ridge bridge. native: the objective's own score; SELECTION_CE uses the NCE readout.
- **mean_score:** a window is correct if mean(d) > 0. An exact tie is scored 0.

### learned_temporal

- **Model:** sklearn `LogisticRegression(C = 1.0, lbfgs, max_iter = 1000, intercept)`.
- **Features:** the 5 summaries s(d) = [mean, sd, min, max, last − first].
- **Training data:** the training windows of the same length. Each window is presented **once**:
  - with probability 0.5 as (s(−d), label 0), otherwise as (s(d), label 1);
  - the draws come from one rng, `seed + 4242`, consumed in the loop order window length × readout × window.
- **When it is fitted:** only if there are ≥ 20 training windows.
- **Test:** every test window is presented **only in the fixed correct order** (attended first, d = attended − ignored, label 1). It is correct if `predict_proba > 0.5`.
- **No swapped presentation at test.** The training orders are random singles, not pairs.

### Consequence (algebra only; a candidate mechanism, not a measured explanation)

Write h(d) = a(d) + s_sym(d):
- antisymmetric part a = w1·mean + ½(w3 + w4)(min + max) + w5·(last − first);
- symmetric part s_sym = b0 + w2·sd + ½(w4 − w3)(max − min).

In the fixed-order test, a window with |s_sym| > |a| is decided by candidate position, not by d:
- every such window counts as correct when s_sym > 0 and as wrong when s_sym < 0;
- exactly: fixed-order accuracy − paired-order accuracy = ½[P(s_sym > |a|) − P(s_sym < −|a|)].

Random single orders balance the label only in expectation, and the symmetric features (intercept, sd, range) can still take nonzero weight. Two examples:
- finite-sample noise;
- a scale shift of d between in-sample training participants (whose readouts were fitted on them) and test participants.

This is a candidate explanation of the degenerate native column. Package docs/04 §B says it is **not yet shown to explain all of it**, and this note does not assume it does.

### 5 s windows

A 5 s window has one segment, so s(d) = [d, 0, d, d, 0]. `learned_temporal` is then the threshold rule b0 + (w1 + w3 + w4)·d > 0: a calibration or threshold question, with no temporal integration.

### What is saved per unit

**Unit record** `private/auditory_alignment_v3/units/<eid>.json` (the `mean_score` row):
- `eval.attention_windows`:
  - `per_participant`: test participant × {5, 10, 20 s} × {unified, native} → {`mean_score_accuracy`, `learned_temporal_accuracy`, `mean_margin`, `n_windows`};
  - `integrators`: per (window, readout) {`coef[5]`, `intercept`, `n_train_windows`};
  - `window_counts`.
- The standard dense-grid evaluation, including the per-segment `attention_2afc` per participant (accuracy, mean margin, n).
- The `learned_temporal` row is a derived copy of these fields.

**Checkpoints** `private/auditory_alignment_v3/ckpt/` (state dicts {enc, head (+ sel)}, symlinks to `/projects`):
- `<eid>_best.pt` for attended_alignment and selection_only;
- `<eid>_c0_best.pt` / `<eid>_c1_best.pt` for alignment_plus_selection (selection weights 0.1 / 1.0). The record field `chosen_sel_weight` names the evaluated candidate.
- All 180 needed files resolved at 19:4x today. Two were loaded and match the rebuilt architecture: 25 lag tokens × 32 → 32; `head.P` 32 × 48 for 6 Local dims × 8 frames.

**Not saved anywhere** (unit records, logs, `d_lag/`, results):
- per-window or per-segment d;
- cached representations or features.

d lives only in an in-memory dict inside `attention_windows`.

### Answer to the audit question

- **Per-window raw d for the test windows is not on disk** for the seed-3401 units or for the panel units (3407 / 3413).
- **Path (a)**, CPU from saved scores, is impossible. Per-participant means and integrator coefficients cannot reconstruct a paired-order accuracy.
- **Path (b)** applies:
  - reload each unit's saved encoder and head (the chosen candidate for alignment_plus_selection);
  - rebuild the legacy readouts with the same seeds;
  - recompute d for that unit's training and test windows.

  It is not path (c), because all checkpoints are present.
- **Resources:** the frozen loaders build the whole cohort.
  - FAU: 81 participants, 3.4 GB float32 EEG. DTU: 44 participants, 3.5 GB.
  - Building the bank makes a transient ≈ 2× copy, which is above this session's 4 GB cap. The run therefore needs a Slurm job: a GPU pool worker, or a CPU node with ≥ 16 GB.
  - The encoder is small; loading dominates the run time.
- **Risk (reported, not acted on):** 135 of the 180 needed checkpoints are on the pending deletion list `private/ckpt_cleanup_20261015/A3c_D_ATTENTION_D_COVERAGE_nondep.tsv` (sha256 `910907e7…`, "non-dependency"):
  - 3401: 55; 3407: 40; 3413: 40.
  - The list has not been executed.
  - If A3c is deleted before this recomputation, those units can only be recovered by retraining.

## 3. What was already seen when this note was written

### Seed 3401 D_ATTENTION results, seen before this session

Sources: D_ATTENTION_RESULTS.md (`6c25414c…`), `results/auditory_alignment_v3/d_lag/d_lag.json` (`736dedf0…`), and the brief (package `sources/ALN3_BRIEF_20261016.md`, D section).

- **AT-INTEGRATOR counts (unified, simultaneous intervals):** 24/30 cells I<0, 5 contain 0, 1 I>0 (DTU attended CS 10 s, +0.005). The most negative cell is FAU selection_only 10 s at −0.034.
- **Degenerate native `learned_temporal` column:**
  - CS: per identity 0 at 20 s; 1 (DTU) / 0.5 (FAU) at 10 s; the DTU 5 s identity mean is ≈ 0.965.
  - NCE: below chance at 20 s, e.g. FAU attended NCE, identity mean 0.298.
  - Δacc native at 20 s: −0.627 … −0.852 (CS) and −0.176 … −0.362 (NCE).

### Read in this session

- The D section of the brief.
- The first rows of D_ATTENTION_RESULTS.md: FAU attended NCE / CS AT-LEVEL, AT-INTEGRATOR and AT-LENGTH.
  - Examples: FAU attended NCE AT-INTEGRATOR unified −0.005 / −0.029 / −0.016 at 5 / 10 / 20 s, all I<0; native +0.008 / +0.019 / −0.362.
- The key structure of one 3401 record.
- Training-side metadata of all 180 units:
  - status, code hash, device, run time;
  - the chosen selection weight, which is an early-stopping choice made on the training side;
  - window counts of three 3401 units per dataset.

### Not read

- Any seed-3407 / 3413 test value: per-participant accuracies, margins, integrator coefficients or aggregates. **Panel values: not read.**
- `private/auditory_alignment_v3/d_lag/per_identity.json`, in this session.
- Any paired-order value; none exists.

### Consequence for the claim type

- The **3401 part** is a post-hoc correction of an anomaly that has already been seen. It is not a blind test.
- The **panel part** is computed on values not yet read, under a design shaped by the 3401 anomaly.

## 4. What changes relative to the old analysis

**Old analysis.** ADDENDUM_12 §3 AT-INTEGRATOR: `mean_score` → `learned_temporal` with the fixed-order test.
- It stays as recorded.
- It is additionally recomputed from the new scores, as a reproduction check (family `AO-FIXED`).

**New candidates (card):**
1. `legacy_learned_paired_order`: the **saved** legacy coefficients, evaluated with both presentations of every test window.
   - (A, B): label 1, logit h(d). (B, A): label 0, logit h(−d).
   - Credit per physical window = the mean of the two order credits; a logit of exactly 0 earns 0.5.
   - The model is not refitted.
2. `antisymmetric_learned`:
   - **Model:** h(d) = b0 + w·s(d), with the same 5 summaries and the same estimator (`LogisticRegression(C = 1.0, lbfgs, max_iter = 1000)`).
   - **Fitting:** on the unit's training windows only, each presented in both orders with the label flipped. Each copy has weight 0.5, so every physical window carries one unit of weight, as in the legacy fit.
   - **Score:** l(d) = ½[h(d) − h(−d)], p = σ(l). Hence p(−d) = 1 − p(d) exactly.
   - **Credit:** 1(l > 0) + ½·1(l = 0).
   - **Windows:** the same test windows as `mean_score`.

**Split rule.** Both orders of a window always stay on the same side of the split: training windows enter only the fit, test windows only the scoring.

**Reference (`mean_score`) under the same paired evaluation.** The credit is 1(mean d > 0) + ½·1(mean d = 0). This equals the legacy `mean_score` accuracy except for exact ties (checked against the record). AT-LEVEL, AT-LENGTH and AT-TASK are therefore unaffected by this correction.

**Refit scope.** No backbone is refitted; only the integrator head (`refit: head_only_when_possible`). Refitting the legacy model from the recomputed scores is used only as a QC.

**Structural expectations, fixed now:**
- At 5 s, `antisymmetric_learned` reduces to sign((w1 + w3 + w4)·d).
  - It equals `mean_score` whenever w1 + w3 + w4 > 0, so its 5 s contrast is a check (expected 0), not evidence.
  - If the sum is ≤ 0, that is reported as such.
- With exact paired training, the symmetric part of h is already ≈ 0 before antisymmetrisation. Its size is recorded as a diagnostic.

## 5. Pairing keys and identity / content aggregation

- **Pair:** the same trained model, so the same dataset, subject fold, content fold, seed, training task, objective, readout, window length and test windows. Only the integrator differs.
- **Unit level:** per test participant, accuracy = the mean credit over that participant's test windows.
- **Identity level:** the mean over the identity's units of that configuration (its one subject fold × 2 content folds), as in ADDENDUM_12 / `d_lag_interim.py`.
- **n:**
  - FAU 67 test identities (TH 14, HA 29, CI 24); the FAU TH dev participants are never tested.
  - DTU 44 (NH 22, HI 22).
- **Seeds:**
  - every seed is analysed separately;
  - seed mean = per identity, the mean of the per-seed paired differences, over identities present in all three seeds. This exists only for the NCE attended_alignment and alignment_plus_selection cells;
  - the between-seed range of the per-seed estimates is reported, with a coverage table of units and identities per seed;
  - missing pairs are not filled with 0, and seeds and folds never add n.

## 6. Quantities, families and uncertainty

### Primary quantity

The unified readout's paired-order accuracy difference, candidate − `mean_score`, at 5 / 10 / 20 s. Positive means the learned integrator is more accurate.

### Families (declared now)

Each family has 3 members (5 / 10 / 20 s), the same shape as ADDENDUM_12 AT-INTEGRATOR, so classes compare one to one.

| family | scope | contrast |
|---|---|---|
| `AO-ANTISYM` | dataset, task, objective, seed | `mean_score` → `antisymmetric_learned` |
| `AO-PAIRED-LEGACY` | dataset, task, objective, seed | `mean_score` → `legacy_learned_paired_order` |
| `AO-FIXED` | dataset, task, objective, seed | the old fixed-order contrast, recomputed (reproduction) |

The same families are formed with seed = `mean` for the panel cells.

### Statistics (inherited unchanged)

- identity-level paired differences;
- bootstrap-t over identities, B = 4,000 (`sci_r1/stats.py` through `bc_interim.run_family`);
- simultaneous 95% intervals by max-t within each family;
- classes I>0 / I<0 / contains 0;
- no p-values;
- intervals are conditional on the fitted models and do not include training randomness.

### Secondary (pointwise intervals only)

- the native readout for the same contrasts;
- the level of each integrator (accuracy − 0.5);
- the logloss (bits) of the two learned integrators;
- per-group columns, descriptive only (n < 5 is shown as n only).

### Diagnostics (descriptive, per configuration)

- The fraction of test windows whose legacy decision is decided by position (|s_sym| ≥ |a|), split by the sign of s_sym.
- The exact identity fixed − paired = ½[P(s_sym > |a|) − P(s_sym < −|a|)], checked numerically.
- The fitted coefficients of both learned integrators.
- The size of the symmetric part of the paired-trained h.

### QC per unit (before inclusion)

A unit enters the tables only if all of the following hold:
- the checkpoint sha256 equals the offload manifest;
- the recomputed training-side target statistics equal the checkpoint head buffers;
- the window counts equal the record;
- per participant, `n_windows` is identical, and `mean_margin`, the `mean_score` accuracy and the legacy fixed-order `learned_temporal` accuracy reproduce the record within the tolerances fixed in code (`QC_TOL`).

Refitting the legacy LR from the recomputed training windows should reproduce the saved coefficients. It is recorded, with a flag if the relative difference exceeds 1e-2.

A unit that fails QC is listed with its reason and excluded, never filled.

### Interpretation rules (fixed now)

- **Symmetric reporting:** favourable and unfavourable classes are reported in full and counted per cell.
- **Scope:** statements are limited to this recipe (5 fixed summaries, a linear logistic model, C = 1, these models). There is no "simple averaging suffices" generalisation in either direction.
- **Window length:** 5 s is a threshold / calibration case only. Window length means evidence integration, not latency or a recording budget.
- **Unexplained anomaly:** say plainly that the anomaly is not explained by order alone if either of these holds:
  - the paired-order legacy accuracy stays below chance;
  - the position-decided fraction does not account for the old native anomaly.
- **No pooling:** datasets, objectives and seeds are not pooled. The panel supports conclusions only for the NCE attended_alignment / alignment_plus_selection cells; CS and selection_only cells have seed 3401 only.
- **Groups:** no method selection by group; groups are descriptive only.

## 7. Exploratory / planned / correction status

- This is a correction of an already reported secondary family (AT-INTEGRATOR) together with its native column. The new antisymmetric scorer is exploratory.
- The corrected rows carry `evaluation_version aln34_attention_order_v1`. The old rows keep their original version.

## 8. Reusable products and the computation actually needed

**Reused:**
- 180 unit records (legacy per-participant values, integrator coefficients, chosen candidate);
- 180 checkpoints;
- the frozen loaders, batcher, encoder / head builders, readouts and window functions, imported unchanged.

**New:**
- one forward pass per unit over its competing-speech segments plus the 400-segment single-speaker readout subsample, giving per-segment d (unified and native), saved per unit;
- then a CPU-only analysis.

**Execution:** the GPU (or high-memory CPU) Slurm job is specified in `attention_order_units.txt` and the task summary. This agent submits nothing.

## 9. Output files

- **Code:**
  - `auditory_alignment_v3/aln34/attention_order.py`, with two entry points:
    - `--unit` / `--unit-list`: score extraction;
    - `--analyze`: aggregation;
  - tests: `tests/auditory_alignment_v3/aln34/test_attention_order.py`.
- **Unit list:** `private/auditory_alignment_v3/aln34/attention_order_units.txt`.
- **Scores:** `results/auditory_alignment_v3/aln34/attention_order/scores/<eid>.npz` + `<eid>.json` (meta and QC).
- **Results:**
  - `results/auditory_alignment_v3/aln34/attention_order/attention_order.json`;
  - `results/auditory_alignment_v3/aln34/attention_order/per_identity.json`;
  - `docs/auditory_alignment_v3/ATTENTION_ORDER_CORRECTION.md` (EXPERIMENT_UPDATE template), written only after the scores exist.

All new docs and results are mode 600.

## 10. Addendum: implementation details fixed after §1–9

Written 2026-10-16 20:12 CEST. Still no value has been computed: no score file exists and no paired-order number has been produced. §1–9 are unchanged.

### QC tolerances (`attention_order.QC_TOL`)

| check | tolerance |
|---|---|
| `mean_margin` | |Δ| ≤ 1e-6 + 1e-5·|margin| |
| `mean_score` / legacy `learned_temporal` accuracy | ≤ 1 window per participant × window × readout cell |
| target statistics | max(|Δmu| / sd, |Δsd| / sd) ≤ 1e-4 |
| legacy-refit coefficients | flagged above a relative difference of 1e-2; not an exclusion |

### Exact reproduction of the old classes

For seed 3401, the old AT-INTEGRATOR families are recomputed from the new scores under their original labels (`AT-INTEGRATOR|dataset|task|objective`, members 5s / 10s / 20s, metric `acc`). This gives the same bootstrap draws, which are then compared field by field with `results/auditory_alignment_v3/d_lag/d_lag.json`.

The new families use their own labels, so their bootstrap draws differ from ADDENDUM_12.

### Checkpoint check (20:06)

- 180 / 180 checkpoints exist, and their sha256 equals the offload manifest (`--check-ckpt`).
- 135 / 180 are on the pending A3c deletion list.
- The unit list, with the commands, is in `attention_order_units.txt`.

### Engineering tests, synthetic only (no EEG)

`tests/auditory_alignment_v3/aln34/test_attention_order.py`, 18 tests, all passing on CPU. They show:
- the frozen `run_attention.attention_windows` output is reproduced bit-exactly: windows, margins, accuracies, flip stream and LR coefficients;
- the real `lag_local_tokens` encoder, fixed-feature head, frozen `GridBatcher` and readouts run end to end on a tiny synthetic cohort with zero reproduction error;
- the results agree with the package reference `attention.py`.

These are engineering checks, not a performance gate.

## 11. Correction and v2 design (2026-10-16, from 21:04 CEST) — after an independent verification

Written from 21:04 CEST, after an independent verification of §1–10 and of the v1 code. **No paired-order value exists:** stage 1 has never run, no score file has been written, and the `--analyze` path has only run on synthetic or empty inputs (the verifier's scratch run had no score files). §1–10 above are kept exactly as written; this section corrects them where they are wrong or incomplete and declares the v2 design before any value is computed.

- v1 code, tests, unit list and this note as of 20:11:20 are archived unchanged in `private/auditory_alignment_v3/aln34/attention_order_v1_20261016T2011/` (`SHA256SUMS` inside; note `318c172e…`, code `1e52b32c…`).
- New rows carry `evaluation_version = aln34_attention_order_v2`. v1 never produced a value, so nothing is superseded in any result file.

### 11.1 Provenance correction (§3)

- §3 says "Panel values: not read" and that the panel part "is computed on values not yet read". That described only what the author of §1–10 had read, and it was incomplete. The R34_D_PANEL lane of the same session had already computed and written the panel's **legacy fixed-order** AT-INTEGRATOR values (unified primary; native and margin secondaries) for 3407, 3413 and the seed mean:
  - `results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json` (first written 20:01);
  - `docs/auditory_alignment_v3/D_MULTI_SEED_RESULTS.md` §1.6 (20:03).
  §1–10 were finalised at 20:11 without mentioning this.
- **Consequence for the claim type:** for the session, the panel's legacy fixed-order contrast is not blind. In this track it is a reproduction target, not new evidence (11.6). The panel's paired-order values (`AO-PAIRED-LEGACY`, `AO-ANTISYM`) remain uncomputed.
- The author of this correction has looked only at the key structure of `d_multiseed.json` (family labels, member names, field names; no number was displayed) and at the section headings of `D_MULTI_SEED_RESULTS.md`. No panel number has been read in this lane.
- The results document no longer hard-codes "Panel (3407/3413) values were not read before this run". Its provenance sentence is generated from this section (`PROVENANCE` in the code).

### 11.2 Scope correction: the policy arms (§1, §2, unit list)

§1, §2 and the v1 unit list covered only the 180 `lag_local_tokens` models. They omitted the D_ATTENTION policy arms.

- **Completed:** 113 trained models, all seed 3401: `dense_fm_policy` 58 and `complement_policy` 55. DTU has 99 of them (10 per task/objective cell, except dense_fm_policy alignment_plus_selection NCE with 9); FAU has 14 (1–2 per cell). Counting the learned_temporal twins there are 220 complete records (107 twins complete). The 6 missing twins do not matter, because the mean_score record holds both integrators.
- **Held:** the incomplete policy rows (87 mean_score, 93 twins) are held executions (`governance/held_executions.json`) and stay held.
- **Same flaw:** they were evaluated by `run_attention_policy._windows`, which calls the same frozen `run_attention.attention_windows` on FM representations (`fm_dense.DenseReps` / `fm_complement.CompReps`). Their records therefore hold the same fixed-order learned_temporal values and saved integrators.
- **Saved per unit:**
  - the record, with the same `attention_windows` fields;
  - `<eid>_best.pt` or `<eid>_c{k}_best.pt`, holding `model` (+ `sel`): the whole FM model including backbone weights.
  - The dense arm saves no audio head. Its head is the deterministic fixed-feature head of the training-side target statistics; v2 rebuilds it and checks the statistics against the lag twin's head buffers.
  - The complement arm's head and frozen base come from the lag twin's checkpoint (`dependency.lag_base_checkpoint`).
  - No per-window d and no features are saved, so path (b) applies, as for the lag arm.
- **Record devices:** V100-PCIE-16GB 38, V100S-PCIE-32GB 45, A30 16, A40 14.
- **Checkpoints:** all 113 policy checkpoints and the 55 complement base checkpoints (lag 3401 units) exist and match the offload manifest. All are on the pending A3c deletion list.
- **In scope:** the card names datasets fau/dtu and objectives NCE/CS_SINGLE, with no architecture restriction, and A04 asks for completed old-policy records to be summarised.
- **Reporting limits:**
  - one seed (3401);
  - FAU policy cells cover 1–2 of 10 folds and are reported with that coverage;
  - no policy arm is pooled with the lag arm or with another arm.
- **Seen:** no aggregate of the policy-arm attention values exists anywhere (C_COMPLEMENT_RESULTS.md lists unit counts only). None of their test values was read in this lane. The record fields accessed were status, device, timings, chosen configuration, checkpoint names, dependency, window counts and the key structure.
- **AO-FIXED for the policy arms:** with no old aggregate to reproduce, their AO-FIXED family is the first summary of completed old-policy records, under its own label.

### 11.3 Mechanism correction (§2, "Consequence")

- **Correction:** §2's second example is wrong. A scale shift of d between training and test participants does not create symmetric weights. It only changes how often symmetric terms that already exist dominate at test.
- **Candidate mechanism, stated concretely** (checked on training-side quantities in 11.8):
  1. Each training window gets an independent coin for its presented order. The share of label-1 presentations therefore differs from 0.5 by sampling.
  2. When the summary features carry little weight, the unpenalised intercept fits logit(share). For native CS, |d| is about 1e-4, so with C = 1 on unscaled summaries and lbfgs tol 1e-4 the feature weights stay near the zero start.
  3. `default_rng(seed + 4242)` is the same stream for every unit of a seed. It is consumed in the same order (window length × readout × window), and the units of one dataset have similar window counts. The share, and with it the sign of the intercept, is therefore shared across units.
  4. In the fixed-order test, every window then receives the intercept's decision. Identity accuracy becomes 0 or 1, or 0.5 when an identity's two content-fold units fall on different sides.
- **Paired orders:** the paired-order evaluation removes this by construction, because a position-only logit scores exactly 0.5.
- **Status:** this remains a candidate explanation, and the caution of package docs/04 §B stands. Whether it also accounts for the NCE native cells (below chance but not 0) can be answered only by the paired-order evaluation. The §6 interpretation rule is unchanged.

### 11.4 Antisymmetric fit: scaling, convergence and a zero-fit status

**Problem in v1.** With paired training, the gradients in the intercept, sd and (max − min) directions are exactly 0 at the zero start. v1 used the legacy LogisticRegression(C = 1, lbfgs, tol 1e-4) on unscaled summaries.
- For |mean d| below about 2e-4, lbfgs stops at iteration 0 with coef = 0. Then l = 0, and every window scores the 0.5 tie credit.
- The native CS readouts are on that scale.
- v1 stored `n_iter` but never flagged it, and counted such fits as "weight sum ≤ 0".

**v2 rule, declared before any value:**
1. **Scale.** σ = sqrt(mean d²) over all segments of the cell's training windows: training participants only, and swap-invariant. The model is h(d) = b0 + w·s(d/σ), with the same five summaries. s is positively homogeneous, so this is a reparametrisation of the same linear model in which the C = 1 penalty acts on standardised weights. Package docs/04 §B allows swap-invariant reweighting.
2. **Estimator.** LogisticRegression(C = 1.0, lbfgs, tol = 1e-10, max_iter = 10,000). Paired training with weight 0.5 per copy is unchanged.
3. **Status per (unit, window length, readout):**
   - `ok`;
   - `zero_fit`: n_iter = 0, or every antisymmetric weight is exactly 0;
   - `not_converged`: n_iter reaches max_iter;
   - `zero_scale`: σ = 0 or non-finite;
   - `no_fit`: fewer than 20 training windows, as in the legacy.

   Only `ok` fits are scored. The others are counted per cell and listed. They are never scored as a 0.5-credit integrator, and never counted as "weight sum ≤ 0".
4. **Pairing at the unit level.** Within each contrast, the reference and the candidate are averaged over the same units of an identity. A unit-cell without the candidate (status ≠ `ok`, or no saved legacy integrator) leaves that contrast for both sides, and the exclusion is listed. v1 averaged each integrator over its own available units.
5. **Unchanged:**
   - the 5 s reduction, now sign((w1 + w3 + w4)·d/σ), so the 5 s AO-ANTISYM contrast remains a check; the `coef_sum_5s` count now covers `ok` fits only;
   - the legacy-refit QC keeps the legacy settings, because it reproduces the old fit;
   - `legacy_learned_paired_order` uses the saved coefficients.

### 11.5 Device and QC tolerance

**Background.**
- All 180 lag units were evaluated on NVIDIA A40. The policy units ran on V100-PCIE-16GB, V100S-PCIE-32GB, A30 and A40.
- `cudnn.allow_tf32` is True by default in this environment (torch 2.6.0+cu124, cuDNN 9.1), and no project code changes it. Ampere-class cards therefore run the convolutions in TF32; V100 and the CPU run them in FP32.
- A recomputation on another device type moves per-participant margins by more than the v1 tolerance. The verifier measured up to 4.05e-6 against 1.03e-6, using TF32 emulation on CPU.

**v2 rule.**
- **Device pinning.** Stage 1 runs each unit on the **same GPU model as its record** (`rec["device"]`), with the default TF32 settings and the same software stack (the eeg2025 environment).
- **Recorded per unit:** torch, CUDA and cuDNN versions, and both TF32 flags.
- **Mismatch handling.** The script refuses a unit whose recorded device differs from the current GPU, unless `--allow-device-mismatch` is given. A score file written that way is marked `device_mismatch` and never enters the primary tables.
- **Tier 1, primary inclusion:** unchanged from §10.
  - margin: 1e-6 + 1e-5·|m|;
  - accuracies: ≤ 1 window per participant × window × readout cell;
  - target statistics: 1e-4.
- **Tier 2, sensitivity only, declared now.** A unit that fails tier 1 **only** on margin or accuracy reproduction is re-checked with:
  - margin: |Δm| ≤ 1e-6 + 1e-5·|m| + κ·rms_s, where rms_s is the RMS of the recomputed attended and ignored scores over that participant-cell's test segments;
  - accuracies: ≤ max(1, ⌈0.02·n⌉) windows.
- **Choosing κ.** κ is fixed in 11.8 before any extraction, by TF32 emulation on CPU on a synthetic cohort with real checkpoints:
  - κ = 10 × the largest observed max |Δm| / rms_s, rounded up to the next power of ten;
  - κ is accepted only if it is at least 10 times below the smallest such ratio produced, in the same experiment, by each of three configuration errors: the other selection-weight candidate, a readout rng offset, and another subject fold's checkpoint;
  - otherwise tier 2 is not used.
- **Reporting.** Units that pass only tier 2 appear in a separate sensitivity table, never in the primary families.

### 11.6 Reproduction and reconciliation

- **Empty reproduction.** v1 rendered "max |Δ| 0.00e+00, class agreement 0/0" when nothing could be compared. v2 states "not established (no member compared)" in that case and always reports how many members were compared.
- **AO-FIXED for the lag arm** is reported only as a reproduction under the original labels and bootstrap draws:
  - seed 3401 against `results/auditory_alignment_v3/d_lag/d_lag.json` (ADDENDUM_12);
  - seeds 3407 / 3413 and the seed mean against `d_multiseed.json` (R34_D_PANEL), using d_multiseed's own construction:
    - labels unchanged;
    - per-seed identity values as in `d_lag_interim.collect`;
    - seed mean = per identity, the mean of the within-seed paired differences over the seeds that have the pair, against a reference of 0.
  - Field-by-field differences (est, CI, simultaneous interval, class) and the sha256 of both reference files are recorded.
  - No second interval set for this legacy contrast is reported. The v1 AO-FIXED families under their own labels are dropped for the lag arm.
- **AO-FIXED for the policy arms** keeps its own label (11.2).

### 11.7 Declarations aligned with the code

- **Logloss.** §6 lists logloss under "Secondary (pointwise intervals only)", but v1 reported only n / mean / min / max. v2 implements the declaration: identity-level logloss (bits) of `legacy_learned_paired_order` and of `antisymmetric_learned`, and their paired difference (antisymmetric − legacy, unit-level pairing), each with a pointwise bootstrap-t interval (B = 4,000), per cell and readout.
- **Position-decided fraction.** The inequality is strict: s_sym > |a| (pos+) and s_sym < −|a| (pos−), as in §2 and the code. §6's "|s_sym| ≥ |a|" is replaced by the strict form. The boundary has measure zero.

### 11.8 Engineering checks declared now (results appended below with their times)

- (a) **Flip stream.** On the seed-3401 records' training-side quantities:
  - regenerate the presentation draws from `default_rng(seed + 4242)` and the recorded training window counts;
  - compare logit(label-1 share) with the saved intercepts per cell (correlation, sign agreement, max |difference|);
  - report the median max |w| of the saved coefficients.

  The policy arms are excluded from this check. No test value is read.
- (b) **TF32 emulation for κ (11.5).** Done on CPU with a synthetic cohort (no EEG) and real checkpoints.
- (c) **Module checks** on synthetic d at scales 1e-4 to 1. The scaled fit must not collapse, and its decisions must not depend on the scale of d.

### 11.9 Execution plan (replaces the v1 header of the unit list)

v1 had three problems:
- it offered four concurrent processes inside one 24 GB job (about 4 × 8–9 GB peak);
- it offered "any pool GPU" or a CPU node;
- it gave an unverifiable ~80 GPU-min.

v2 plan:
- **Jobs.** One Slurm job per recorded device type, each with **one process at a time** (units sorted by dataset and content fold, so each cohort loads once per job).
- **QOS.** Each job is submitted under `--qos=runfill`, the QOS of the pool. The scheduler then counts it against the per-user `gres/gpu = 10` limit (`MaxTRESPU`), so the 10-GPU cap holds without any queue or hold edit. While 10 GPUs are in use, the job pends with `QOSMaxGRESPerUser`.
- **Estimate.** From the record timings (11.10), with the upper bound stated as such.
- **Submission.** This lane submits nothing.

### 11.10 Minor corrections

- §10 is stamped 20:12, but the file was last written at 20:11:20 (mtime).
- The test count reported by the v1 builder ("35 pass with related suites") does not reproduce. `tests/auditory_alignment_v3/test_aln31_panel.py` has 2 failures, which predate this track (`plan_ext.jsonl` unchanged since 10-14). The v2 test results, with exact commands, are appended below.

### 11.11 Result of check 11.8 (a): flip stream (run 21:05 CEST, training-side quantities only)

- **Script:** `private/auditory_alignment_v3/aln34/attention_order_flip_stream_check.py`.
- **Inputs:**
  - the 100 seed-3401 lag records: their recorded training window counts and saved integrators;
  - no test value.
- **Method:**
  - regenerate the draws of `default_rng(3401 + 4242)` in the legacy consumption order;
  - label 1 = draw ≥ 0.5.

**Native CS cells (6 cells × 20 units).** The saved intercept equals logit(label-1 share).

| cell | corr | sign agreement | median b0 / median logit(share) | share < 0.5 | median max\|w\| |
|---|---|---|---|---|---|
| FAU 5 s | +0.9998 | 20/20 | −0.0008 / −0.0006 | 60 % | 3.6e-4 |
| FAU 10 s | +0.9999 | 20/20 | +0.0100 / +0.0101 | 50 % | 7.1e-4 |
| FAU 20 s | +1.0000 | 20/20 | −0.0456 / −0.0456 | 100 % | 0.34 |
| DTU 5 s | +0.9997 | 20/20 | +0.0078 / +0.0078 | 0 % | 1.36 |
| DTU 10 s | +1.0000 | 20/20 | +0.0194 / +0.0195 | 0 % | 0.67 |
| DTU 20 s | +1.0000 | 20/20 | −0.0856 / −0.0856 | 100 % | 0.33 |

- **Across these cells:** max |b0 − logit(share)| ≤ 4.2e-4.
- **Agreement with the seen degenerate column (§3):**
  - per identity 0 at 20 s in both datasets;
  - 1 at DTU 10 s;
  - 0.5 at FAU 10 s.
- **Confirmed:** this agrees with the verifier's finding.
- **Remaining question:** whether the features' contribution at test is as negligible as the coefficient sizes suggest needs the test d, which is not on disk.

**NCE native cells.**
- The intercept tracks logit(share) less tightly: corr +0.69 to +1.00, sign agreement 10/20 to 20/20.
- The feature weights are large (median max|w| 3–13).
- The sub-chance NCE native values are therefore not explained by the intercept alone (11.3 stays a candidate).

**Unified cells.**
- corr −0.38 to +0.80;
- median max|w| 1.2–8;
- the features clearly matter.

**Selection_only (SELECTION_CE).** These cells use the NCE readout and behave like the NCE cells.

### 11.12 Result of check 11.8 (b): TF32 emulation and the tier-2 constant (run 21:16–21:21 CEST, synthetic EEG only)

**Setup**
- Script: `private/auditory_alignment_v3/aln34/attention_order_tf32_calibration.py` (sha256 `201544ba…`).
- Output: `attention_order_tf32_calibration.json` (`9210a97e…`).
- Units: four seed-3401 lag alignment_plus_selection units (FAU / DTU × NCE / CS_SINGLE, subject fold 0), with their real checkpoints.
- Cohort: a synthetic cohort of 6 training and 3 test participants, with 144 / 72 / 36 training windows at 5 / 10 / 20 s.
- Reference: the frozen `attention_windows` in FP32 on CPU, playing the unit record.

**Results** (max |Δm| / rms_s over participant-cells; tier 1 = the primary tolerance)

| variant | ratio | tier 1 passes | max \|Δm\| |
|---|---|---|---|
| identical FP32 recomputation | 0 | 4/4 | 0 |
| TF32, round to nearest | 5.7e-5 – 2.2e-4 | 2/4 | 3.1e-6 |
| TF32, truncation | 7.0e-5 – 3.2e-4 | 1/4 | 5.6e-6 |
| other selection-weight candidate | ≥ 0.086 | 0/4 | |
| other subject fold's checkpoint | ≥ 0.32 | 0/4 | |
| readout rng offset | ~2e-8 | 4/4 | |

- TF32: this confirms the verifier's finding. A device-type change makes tier 1 fail, and the window decisions agree within ≤ 1 window.
- The two genuine configuration errors sit at least 266 times above the largest TF32 ratio, and they also change up to 8 window decisions.
- The readout rng offset changes nothing. The synthetic cohort has only 48 single-speaker training segments (< 400), so the readout subsample is the whole set in both cases. This check is degenerate here, not a real configuration error.

**Decision under the rule declared in 11.5**
- The rule computes κ = 10 × 3.2e-4 → 1e-2.
- It also requires every error type to lie ≥ 10 κ above that. The degenerate readout-rng check fails this requirement.
- **Tier 2 is therefore not used in v2** (`QC_TOL2["kappa_rms_s"] = None`). The tier-2 code path stays implemented and tested, but is inactive.
- The primary design is unaffected:
  - device-matched extraction (11.5);
  - tier-1 inclusion;
  - a unit that fails tier 1 is `qc_failed`, listed and not filled.
- If a fallback is wanted later, a new version must declare it before any extraction. One option is to repeat this calibration on a cohort with > 400 single-speaker training segments. This lane does not do that.

**Bearing on the device rule (11.5)**
- The identical recomputation reproduces exactly. TF32-vs-FP32 numerics produce tier-1 failures in 5 of 8 emulated runs.
- Running every unit on its recorded GPU model is therefore necessary for tier-1 inclusion. The script enforces it.

### 11.13 v2 implementation record (21:06–21:40 CEST); still no paired-order value

**Code** (`auditory_alignment_v3/aln34/attention_order.py`, sha256 `4180bb70…`, `evaluation_version aln34_attention_order_v2`):
- **11.4:** `train_scale`, `fit_antisymmetric` (scaled, tol 1e-10, statuses), unit-level pairing (`Acc`, `contrast_vals`).
- **11.5 / 11.12:** device guard (`DeviceMismatch`, `--allow-device-mismatch`), recorded numerics, tier 1 / tier 2 QC; tier 2 inactive.
- **11.2:** policy-arm rebuild (`build_unit_model`: DenseFM + fixed-feature head; Complement on the lag twin's base and head) and extraction through the legacy `DenseReps` / `CompReps`. Per-segment attended and ignored scores are saved next to d.
- **11.6:** `reproduce_old` (d_lag.json) and `reconcile_panel` (d_multiseed.json construction); "not established" wording; no lag-arm AO-FIXED family.
- **11.7:** logloss with pointwise intervals.
- **Provenance:** sentence generated from `PROVENANCE`; coverage table per arm.

**Job script:** `auditory_alignment_v3/aln34/attention_order_extract.sbatch` (`fd1ce741…`). One process per job, runfill QOS. It is not submitted.

**Unit list v2:** `private/auditory_alignment_v3/aln34/attention_order_units.txt` (`61c261de…`), 293 completed trained models:

| partition | lag | dense | complement | recorded non-training time (sum) |
|---|---|---|---|---|
| A40 | 180 | 7 | 7 | 274.7 min |
| V100-32GB (V100S) | — | 24 | 21 | 95.5 min |
| V100-16GB (exclude node42) | — | 20 | 18 | 79.8 min |
| A30 | — | 7 | 9 | 46.1 min |

- **Total: 496 GPU-min.** This is an upper bound: the recorded figure includes the full dense-grid evaluation and, for alignment_plus_selection policy units, two cohort loads. Stage 1 loads each cohort once per job.
- **Held policy rows** (87 mean_score) are not listed and stay held.

**Checkpoint check** (`--check-ckpt`, 21:31–21:34):
- 406 / 406 files exist and match the offload manifest: 293 model checkpoints and 113 dependencies (55 complement bases, 58 dense-arm lag twins).
- 356 of the 406 are on the pending A3c deletion list.

**Tests**, run with `PYTHONPATH=$PWD python -B -m pytest -q -p no:cacheprovider …` and `nice -n 10`:

| suite | result |
|---|---|
| `tests/auditory_alignment_v3/aln34/test_attention_order.py` | 31 / 31 pass (25 fast, plus 6 CPU policy-arm extractions with real CBraMod and REVE checkpoints on a tiny synthetic cohort, 174 s) |
| that file + `test_d_lag_interim.py` + `test_bc_interim.py` + `test_policy.py` | 40 / 40 pass |
| package `AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/tests` | 37 / 37 pass |
| `tests/auditory_alignment_v3/test_aln31_panel.py` | 4 pass, 2 fail (`KeyError` at line 60; predates this track, not touched) |

**What the policy-arm tests show:**
- the real checkpoints load strictly into the rebuilt architectures;
- the recomputed scores reproduce `run_attention_policy._windows` exactly (tier 1, all errors 0);
- this covers dense CBraMod full / REVE LoRA and complement CBraMod residual / REVE concat, including two alignment_plus_selection units.

**CLI smoke test (CPU).** `--unit <A40 lag unit> --unit <V100 dense unit> --device cpu` skips both for device ("recorded on …, current cpu"), writes nothing and exits 0. It also reports `cudnn_allow_tf32 = True` and `matmul_allow_tf32 = False` in this environment.

**Dry run of `--analyze`** (scratch directories only, no score file):
- the real records are read;
- 380 D_ATTENTION trained-model rows are listed with status;
- both reproductions are rendered as "no member could be compared (0 members); reproduction not established";
- nothing was written to `results/` or `docs/`.

**Order of work, for the honesty record:**
- A first attempt at check 11.8 (a), shortly before 21:02 (before the v1 archive at 21:02:46 and before §11 was written), stopped at the first held policy row (missing record) before printing anything.
- The check was rerun at 21:05:28, after §11.1–11.10 had been written (21:05:19).
- The record metadata read for the audit (status, device, timings, chosen configuration, checkpoint names, window counts) contains no test value.

**Status:** stage 1 needs a GPU, so no score file exists and no paired-order value has been computed. `ATTENTION_ORDER_CORRECTION.md` and `attention_order.json` will be written by `--analyze` only after the score files exist.

**Family labels:**
- Lag arm: unchanged from §6 / §10 (`AO-ANTISYM|ds|task|objective|seed`, seed ∈ {3401, 3407, 3413, mean}).
- Policy arms: the arm is added to the label (`AO-…|dense_fm_policy|ds|task|objective|3401`). This gives them their own bootstrap draws. They are never pooled with each other or with the lag arm.
