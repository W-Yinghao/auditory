# ALN3 Addendum 11 — ALN3.2 paired seed panel (seeds 3407, 3413), 2026-10-14

**Status**: written before any ALN3.2 test value (B_ALIGNED, ALN32_*) was read. Frozen (0444). Basis: ALN3.2 package
`configs/seed_and_reuse.yaml` (core roles; paired, not the whole matrix) and docs/08 §seed policy. User instruction 2026-10-14:
"能做的都做了".

## 1. Roles and rows (`plan_ext.jsonl` block 7; all 25 fold cells; seeds 3407 and 3413; NCE)

| Role | Reference | Candidate | Rows registered (both seeds) |
|---|---|---|---|
| aligned_access_matched | ALN32_LOCAL_SUPPORT `local_aligned1000` | B_ALIGNED `pretrained_frozen` (cbramod, reve) | L1: 50; B_ALIGNED frozen: 100 |
| adaptation | B_ALIGNED `pretrained_frozen` | B_ALIGNED `pretrained_peft` | peft: 100 |
| initialization_true_full | ALN32_TRUE_FULL `random_full`, `full_onestep_v1` | `pretrained_full`, `full_onestep_v1` | 2 inits × 2 backbones × lr {1e-5, 3e-4}: 400 |
| complement_source | ALN32_RESIDUAL `residual_aligned_random` | `residual_aligned_pretrained` | 2 × 2 backbones: 200 |
| complement_value | base L0 (A_LOCAL `lag_local_tokens` full, same seed; existing ADDENDUM_03 panel units) | `residual_aligned_pretrained` | — (the base exists) |
| capacity | `residual_small_capacity` | `residual_aligned_pretrained` | small: 50 |
| private_transfer | private local native | private public-audio prior | registered with the public-prior addendum (dependency not yet defined) |

**Total: 900 rows.**
- Each row copies its seed-3401 row: the same spec, folds and dependencies, with the seed changed and `seed_scope = panel`.
- Its id follows the block-1 rule with the seed in the hashed spec.
- Upstream bases are seed-paired: a seed-3407 residual reads the seed-3407 A_LOCAL base. Those base units are complete (ADDENDUM_03).

## 2. Policies

- Roles were chosen from the package's research questions, not from test results. No winner-only repeats; every role reports
  both seeds even if unfavourable.
- The panel runs after the seed-3401 rows of the same families (queue order: breadth first).
- Probe and calibration sampling stay as each runner defines them (`default_rng(seed + k)`). Seed SD therefore mixes training
  and readout-sampling variation, as in SCI_R1 P3; this is disclosed.

## 3. Analysis

- Per role and seed: the same contrast as the seed-3401 family (ADDENDUM_07 / 10 machinery).
- Plus the three-seed summary: identity value = mean over seeds 3401, 3407 and 3413 (docs/12 §5). Each table lists the
  per-seed estimates, mean, range and SD.
- Contrasts without a complete common seed set report the available seeds and the missing status.
- The seed-panel aggregation code is written before any panel unit completes (`aln32_panel_interim.py`).
