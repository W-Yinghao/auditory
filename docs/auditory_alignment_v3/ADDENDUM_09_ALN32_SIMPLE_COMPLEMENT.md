# ALN3 Addendum 09 — ALN3.2 wave 2a: low-complexity complement in a common prediction space (ALN32_SIMPLE_COMPLEMENT), 2026-10-14

**Status**: written before any of these rows, their probe or any ALN3.2 test value. Frozen (0444) with the code; sha256 in
`ALN32_IMPLEMENTATION_RECEIPT.md`.

**Basis**:
- ALN3.2 package docs/04 ("第一组") and `configs/experiments.yaml` (ALN32_SIMPLE_COMPLEMENT).
- User instruction 2026-10-14: "可以下载，go，能做的都做了".

## 0. What has been seen

- Everything in ADDENDUM_07 §0.
- The old C results: every FAU/DTU variant, including the capacity control, was worse than local, and epoch 0 was never a
  candidate.
- P6: frozen aligned tokens keep linear readability on DTU training participants.
- No ALN3.2 test value.

## 1. Question

Given a valid local base, do frozen query-aligned FM features add predictive value for the same true-query risk? Is the
added value specific to pretrained weights (vs random weights), to new EEG access (vs the raw window), or to added capacity
(vs re-fitting the local features)?

## 2. Rows (`plan_ext.jsonl` block 5)

- One row per fold cell (25) × base {L0 = A_LOCAL `lag_local_tokens` full NCE; L1 = ALN32_LOCAL_SUPPORT `local_aligned1000`} ×
  backbone {cbramod, reve} = **100 rows**.
- Seed 3401, NCE, target as the cohort.
- Each unit computes the six variants of §3 on shared features and stores one evaluation per variant.
- Dependency: the base unit's record and checkpoint must be complete.

## 3. Model (no training; all fits closed-form, training participants only)

**Prediction space**:
- Target: the raw 8-frame target A(t) (flattened).
- Every variant predicts Â(t). The representation scored by the unchanged evaluation is u = FixedFeatureHead(Â): the
  cohort's training-standardised fixed semi-orthogonal projection, L2-normalised, which is exactly the space of the local
  and B models. Unified and native readouts and the candidate pools are unchanged (`ev2.evaluate_continuous`).

**Features per query**:
- the base model's u (32-d);
- the base model's lag tokens (flattened);
- the raw window [t − 0.4 s, t + 0.6 s) with zero before the segment start;
- frozen query-aligned backbone tokens of that window: the last layer, C × E, pretrained or random initialisation (seed 3401,
  same construction as B_ALIGNED).
- Every non-base block is reduced to k = 64 dimensions by a PCA fitted on a fixed random subsample of 8,000 training rows (seed
  20261016), then applied chunk by chunk. A probe change: the full-row PCA needed 19.6 GB on FAU and would need ~40 GB on DTU.

**Groups**: training participants are split into 5 fixed groups (sorted ids, seeded permutation 20261014). The base model was
trained on all of them; this is recorded.

**Variants**:

| Variant | Â |
|---|---|
| `local_only` | ridge(base u → A) |
| `local_refit_capacity` | `local_only` + ridge on the residual from PCA-64 of the base model's own tokens (no new EEG access) |
| `aligned_pretrained` | `local_only` + residual ridge from PCA-64 of the pretrained aligned tokens |
| `aligned_random` | the same with random-initialisation tokens |
| `small_context` | `local_only` + residual ridge from PCA-64 of the raw aligned window |
| `concat` | one ridge on [base u, PCA-64 of the pretrained aligned tokens] |

**Fitting**:
- Residual ridges are fitted on **out-of-fold** base predictions: for each group, the base ridge is fitted on the other four
  groups. The residual is thus learned from cross-person base errors.
- All ridge α are chosen by grouped cross-validation over the 5 groups (mean Pearson r over target dimensions), α grid
  {1e-5 … 1e3} × trace / p. Extended from {1e-3 …} after the probe chose the lower edge; a training-side observation, no test value read.
- The final maps are refitted on all training rows. Test participants are never used.
- Training rows: 8 grid-aligned anchors per fit and early-stopping segment of the training participants
  (rng = seed). Fit and early-stopping rows are pooled for the grouped CV; groups are participants.

## 4. Engineering probe (no performance gate)

One FAU cell, base L0, backbone reve. Checks:
- all six variants complete;
- `local_only` u reproduces the representation of a direct ridge (max |Δ| ≤ 1e-5);
- fold assignment has no participant in two groups;
- no test participant appears in any fit row;
- the aligned window equals the B_ALIGNED window;
- GPU memory and time are recorded.

## 5. Analysis (`aln32_complement_interim.py`, written and synthetically tested before any result)

Per dataset × backbone × base. Positive = candidate lower true-query risk (ADDENDUM_05 machinery):

| Family | Reference → candidate |
|---|---|
| SC-VALUE | `local_only` → each of the other five variants |
| SC-ATTRIB | `aligned_random` → `aligned_pretrained` (pretrained weights); `local_refit_capacity` → `aligned_pretrained` (capacity); `small_context` → `aligned_pretrained` (beyond the raw window); `concat` → `aligned_pretrained` (residual stacking vs joint fit) |

Reading:
- "Complement from the pretrained representation" is used only when SC-VALUE `aligned_pretrained` I > 0 **and** SC-ATTRIB
  pretrained-vs-random I > 0 **and** pretrained-vs-capacity I > 0.
- Base L0 reads post-only EEG while the candidates read the aligned window. With base L0 an improvement is therefore labelled
  "context-assisted"; base L1 is the access-matched comparison.
- I < 0 for a variant means the residual fit hurts on test people.
- No result is chosen by test performance.
