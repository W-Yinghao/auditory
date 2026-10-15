# ALN3 Addendum 07 — ALN3.2 wave 1: support-matched controls and true full updates, 2026-10-14

**Status**: written before any of these rows or their probe ran. Frozen (0444) with the code; sha256 values in
`ALN32_IMPLEMENTATION_RECEIPT.md`.

**Basis**:
- `AUDITORY_ALN3_SERVER_PACKAGE_v3_2_20261014`: docs/02 §2, docs/03 §2–§3, docs/08, `configs/experiments.yaml` (families
  ALN32_LOCAL_SUPPORT, ALN32_POSTONLY_FM, ALN32_TRUE_FULL), `configs/update_recipes.yaml`.
- User instruction 2026-10-14: "go". Both true-full learning-rate cells are run (the recommended option).

B_ALIGNED (ADDENDUM_06) keeps running unchanged. Nothing here edits a hashed file or an existing record.

## 0. What has been seen

- Everything in ADDENDUM_06 §0.
- 18 of the 250 B_ALIGNED units were complete when this was written. Only their run times and status were read; no metric.
- No ALN3.2 unit exists.

## 1. Support facts (from the code, not names)

- `lag_local_tokens` full reads samples [t, t + 77) at 128 Hz ([0, 601.6) ms) and [t, t + 60) at 100 Hz. This equals the
  post part of the B_ALIGNED window exactly. So `local_post_exact_matched_to_F2` (package docs/02 §2) is the existing local
  model L0 itself and is not registered separately.
- The B_ALIGNED window is [t − 51, t + 77) at 128 Hz and [t − 40, t + 60) at 100 Hz, zero before the segment start.
- Segments are contiguous and non-overlapping within a trial (`data._segments_of`). Each anchor therefore lies in exactly one
  segment, whose start defines the mask.

## 2. Rows (`plan_ext.jsonl` block 4, ids `ALN3X_<sha16>`, seed 3401, NCE, all 25 fold cells)

| Family | Variant | Rows | Base row | Definition |
|---|---|---|---|---|
| ALN32_LOCAL_SUPPORT | `local_aligned1000` (L1) | 25 | A_LOCAL `lag_local_tokens` full NCE | the same encoder and recipe on the B_ALIGNED window [−0.4, +0.6) s, zero before the segment start |
| ALN32_LOCAL_SUPPORT | `raw_aligned1000_ridge` (R1) | 25 | same | closed-form ridge from the raw masked window (C × 128 / C × 100) to the fixed d = 32 target projection, α on the training participants' early-stopping rows |
| ALN32_LOCAL_SUPPORT | `raw_post600_ridge` (R0) | 25 | same | the same ridge on L0's window [0, +0.6) s |
| ALN32_POSTONLY_FM | `post600_zero_left` (F2) | 100 | B_ALIGNED `pretrained_frozen` / `pretrained_peft` | the B_ALIGNED single patch with its first 0.4 s fixed at zero; otherwise identical to its twin (recipe, head, selection) |
| ALN32_TRUE_FULL | {`full_onestep_v1`, `warmup_then_all_v1`} × backbone lr {1e-5, 3e-4} | 400 | B_ALIGNED `random_full` / `pretrained_full` | aligned interface; all allowed parameters updated (one-step from epoch 1, or head warm-up for 5 epochs and then all from epoch 6); LLRD 1; head lr 1e-3; random and pretrained share the numeric lr cell, schedule, data and selection; epochs 100 / 50 |

Ids are sha256(family + spec + base id)[:16]. `base_plan_row` points to the base. The total is 575 rows.

## 3. Training and the update ledger

- **L1** reuses `local_train.fit_continuous` and the A_LOCAL evaluation unchanged. The only difference is its batcher: the
  window is (−pre, post) with the segment-start mask, patched per process.
- **F2** uses `fm_aligned32.fit_aligned32` with recipe `aln3`, i.e. the schedule of `fm_aligned.fit_aligned` unchanged plus the
  update ledger, and a batcher that zeroes the first `pre` samples of every window.
- **ALN32_TRUE_FULL** uses `fm_aligned32.fit_aligned32`. It is generated from `fm_aligned.fit_aligned` by declared textual
  replacements: the recipe branch, validation every epoch, and the ledger hooks.
- **Update ledger** (the new trainer). For every parameter group it records:
  - the first open epoch and the number of open epochs;
  - optimizer steps with a gradient, and the lr at first and last step and summed over steps;
  - the relative weight change ‖θ_best − θ_0‖ / ‖θ_0‖, with θ_0 rebuilt deterministically (same seed and construction
    order; checked in the probe).
- The ledger persists across preemption (sidecar `_ledger.json`).
- For the legacy B_DENSE / B_ALIGNED units, a post-hoc ledger is computed separately from the schedule arithmetic, recorded
  `open_groups` and checkpoints (EFFECTIVE_UPDATE_REPORT).

## 4. Engineering probe (no performance gate)

One FAU unit each of L1, R1, F2 (reve frozen) and TRUE_FULL (reve pretrained, `warmup_then_all_v1`, lr 3e-4). Two epochs
each (TRUE_FULL 7, so the all-open phase is reached), in the scratch directory. Checks:
- **L1**: window = slice and zero before the segment start; encoder token count 42 (128 Hz); a perturbation of EEG outside
  the declared window leaves the output unchanged.
- **F2**: first 0.4 s zero; the rest equals the B_ALIGNED window.
- **TRUE_FULL**: every block group and the non-block group open from epoch 6 with gradient steps and non-zero Δθ; θ_0
  rebuild equals a start snapshot (max |Δ| = 0).
- All units complete; peak GPU memory recorded.

## 5. Analysis (`aln32_interim.py`, written and synthetically tested before any result; ADDENDUM_05 machinery)

Per dataset × backbone; positive = candidate lower true-query risk; simultaneous max-t within each family:

| Family | Reference → candidate | Reading |
|---|---|---|
| AI-ACCESS | L1 → B_ALIGNED (5 adaptations) | FM vs local under the same EEG access |
| AI-POSTONLY | L0 → F2 (frozen, peft) | FM vs local under the same post-only access |
| AI-CONTEXT | F2 → B_ALIGNED (same adaptation) | value of the 0.4 s past EEG inside the FM |
| AI-PASTEEG | L0 → L1 | value of the 0.4 s past EEG for the local encoder |
| AI-RAW | R0 → L0, R1 → L1, R1 → B_ALIGNED frozen | encoder vs regularised linear on the same window |
| TF-INIT | random → pretrained at each recipe × lr cell | **initialization contrast** (same schedule, numeric lr, data, selection) |
| TF-RECIPE | `full_onestep_v1` → `warmup_then_all_v1`, and B_ALIGNED legacy → each true-full recipe | recipe contrasts (the legacy one differs in lr, LLRD and open groups) |
| TF-LOCAL | L0 and L1 → each true-full configuration | FM vs local |

Interpretation: as ADDENDUM_06 §5.
- The words "pretraining-prior benefit under matched full update" are reserved for TF-INIT.
- B_ALIGNED and B_DENSE `pretrained_full − random_full` are recipe contrasts (CORRECTION_01).
- The aligned interface changes window, context and head together. No result is called a pure phase effect or an isolated
  early response.

## 6. Seeds, later waves

- The seed-3407/3413 core panel (package `seed_and_reuse.yaml`, 7 roles) is registered in a later addendum, before any
  ALN3.2 test value is seen.
- Complement (ALN32_SIMPLE_COMPLEMENT, ALN32_RESIDUAL), public auditory pretraining and SCI_R2 have their own addenda.
