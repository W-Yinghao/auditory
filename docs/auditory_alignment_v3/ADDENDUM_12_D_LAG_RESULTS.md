# ALN3 Addendum 12 — results of the completed D lag-arm families (attention, coverage, personal adaptation), 2026-10-14

**Status**: written before any aggregate of a D_ATTENTION, D_COVERAGE or D_ADAPT unit was computed or viewed. Frozen (0444)
with the code; sha256 in `ALN32_IMPLEMENTATION_RECEIPT.md`.

**Basis**:
- ALN3.1 package docs/07, with its deliverables D_ATTENTION_RESULTS, D_COVERAGE_MATRIX and D_ADAPT_RESULTS.
- ALN3.2 START_NOW item 5 ("局部模型注意与适配").
- User instruction 2026-10-14: "能做的都做了".

## 0. What has been seen

- Fleet monitoring: completion counts only.
- ADDENDUM_04 probes: short-epoch D units in a scratch directory.
- No D test aggregate.
- The FM / complement policy arms are on hold or incomplete and are **not** part of this addendum.

## 1. Units (seed 3401, `lag_local_tokens`, all folds)

| Family | Units | Design |
|---|---|---|
| D_ATTENTION | 100 `mean_score` rows (the `learned_temporal` rows are derived records of the same models) | FAU, DTU × task {`attended_alignment` (NCE, CS_SINGLE), `selection_only` (SELECTION_CE), `alignment_plus_selection` (NCE, CS_SINGLE)} |
| D_ADAPT | 120 | FAU, DTU × adapter {none, `input_spatial`, `output_low_rank`} × NCE / CS_SINGLE; support fraction 0.1 and 0.3, query = the same last 70 % of each test participant's segments |
| D_COVERAGE | 60 (FAU) | training population {TH_ONLY, TH_HA, TH_HA_CI} × NCE / CS_SINGLE; each with `full_available` and `matched_exposure` fits |

Identities are as in SCI_R1 §2. Per identity: the mean over that identity's units.

## 2. Endpoints

- **D_ATTENTION**: 2AFC accuracy for attended vs ignored on competing-speech test windows of 5, 10 and 20 s.
  - Primary: unified readout, `mean_score` integrator.
  - Secondary: `learned_temporal`, the native readout, mean margin, and the per-segment 5 s `attention_2afc`.
  - Chance is 0.5.
- **D_ADAPT** (on the fixed query set): primary unified `gain_bits` (mismatched − true logloss on the query set, bits);
  secondary `rank_pct` and top1.
- **D_COVERAGE** (FAU test participants): primary R = unified regular logloss (bits); secondary gain and top1.

## 3. Contrasts (identity-level paired; bootstrap-t; simultaneous max-t within each family)

| Family | Members | Positive means |
|---|---|---|
| AT-LEVEL (dataset × task / objective) | accuracy − 0.5 at 5 / 10 / 20 s | above chance |
| AT-TASK (dataset × window) | `attended_alignment` → `alignment_plus_selection` (NCE; CS); `attended_alignment` NCE → `selection_only` | candidate more accurate |
| AT-INTEGRATOR (dataset × task / objective) | `mean_score` → `learned_temporal` at 5 / 10 / 20 s (same model) | learned integrator more accurate |
| AT-LENGTH (dataset × task / objective) | 5 s → 10 s, 5 s → 20 s | longer windows more accurate |
| AD-GAIN (dataset × objective × support) | none → `input_spatial`, none → `output_low_rank` | adaptation raises query gain |
| AD-SUPPORT (dataset × objective × adapter) | support 0.1 → 0.3 | more support helps |
| CV-POP (objective × control) | TH_ONLY → TH_HA, TH_HA → TH_HA_CI, TH_ONLY → TH_HA_CI (all test identities) | lower risk with the larger population |
| CV-BUDGET (objective × population) | `full_available` → `matched_exposure` | lower risk with matched exposure |

- **Descriptive per-group tables** (FAU TH / HA / CI, DTU NH / HI; n < 5 → n only):
  - CV-POP members per test group (the training-population × test-group matrix);
  - AD-GAIN per group;
  - AT-LEVEL per group.
- **QC**:
  - adapter none must be identical across support fractions (same query set);
  - for TH_ONLY the two budget controls coincide by construction.

## 4. Interpretation (fixed now)

- **Attention**: accuracies are task readouts on the registered windows. Longer windows integrate more evidence; this is not
  a latency or recording-budget claim. A task contrast I > 0 is a recipe difference under these models.
- **Adaptation**: uses known-stimulus supervision on the support block, so it is "personal supervised adaptation", not
  label-free test-time adaptation. Support and query are the same session: no cross-session or monitoring claim.
- **Coverage**:
  - A CV-POP difference under `matched_exposure` separates the population change from the update count; under
    `full_available` the two are mixed.
  - "Adding CI hurts" is not written from a negative member; group-specific cells are descriptive.
- **General**: no selection of methods by group differences. Weak and null cells are reported in full.

## 5. Outputs

- `docs/auditory_alignment_v3/D_ATTENTION_RESULTS.md`, `D_COVERAGE_MATRIX.md`, `D_ADAPT_RESULTS.md`;
- JSON in `results/auditory_alignment_v3/d_lag/`;
- per-identity tables private.
- Analysis code: `auditory_alignment_v3/d_lag_interim.py`, synthetically tested before the run.
