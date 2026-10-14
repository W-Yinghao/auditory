# ALN3 Addendum 05 — interim aggregation of the seed-3401 B / C method comparisons (+ private E summary), 2026-10-14

**Status**: written 2026-10-14 before any aggregate of a B_DENSE, C_COMPLEMENT, C_CAPACITY_CONTROL or ALN3 E unit was
computed or viewed. Frozen (0444) together with the analysis code; sha256 values in `IMPLEMENTATION_RECEIPT.md` §9. Later
changes go into a new addendum. User instruction 2026-10-14: "可以，按这个方案开始" (approval of the interim B/C summary plan).

**Basis**: package `docs/05` §4 and §6 (the four B splits; native and unified tables), `docs/06` (the C comparison table, the
primary increment `R(local) − R(combined)`, "mismatched loss alone is not a performance complement"), `docs/08` §2 and §5
(private comparisons; positive-affine calibration does not change AUC), `docs/12` §3 and §5 (initialization vs recipe
contrasts; identity-level inference; common seed sets), `ADDENDUM_03` (seed panel), `ADDENDUM_04` (D policy binding),
`SCI_R1_PREREG.md` §2 (identities) and `auditory_alignment_v3/sci_r1/stats.py` (bootstrap-t, family max-t), reused unchanged.

No performance threshold is set. Every predeclared cell is reported, including weak, null and reversed ones.

## 0. What has been seen (disclosure)

- Fleet monitoring read only completion / failure counts, run times and device data.
- The D binding (ADDENDUM_04) read the **training-side** `best_selection_score` of every seed-3401 B/C unit. The resulting
  choice counts were reported to the user on 2026-10-13: a REVE PEFT `channel_phase_linear` configuration was chosen in 18 of
  40 dense cells; `concat_pretrained` was chosen in 28 of 40 complement cells. These are training-side choices, not test
  results.
- The ADDENDUM_04 probes ran short-epoch D units in a scratch directory (`probe_out`); their QC fields were read. They are
  not fleet units and are not used here.
- Before this addendum, a QC pass compared only participant sets and candidate / query **counts** between every seed-3401
  B/C unit and its same-fold local base: 1,650 / 1,650 complete and matched. No metric value was printed.
- Seen earlier: ALN2 results, SCI_R1 results (local lag models, private lag curves), R_PRIVATE_CALIBRATION results.
- **Not seen**: any test-side value of a B_DENSE, C_COMPLEMENT, C_CAPACITY_CONTROL, ALN3 E_GENERIC, E_PUBLIC_TRANSFER,
  E_COMPLEMENT, E_DISTILL or D unit.

## 1. Scope

**Continuous tasks** (FAU, DTU, Federici), seed 3401, all outer and content folds:

| Set | Units | Design |
|---|---|---|
| B_DENSE | 1,000 | backbone {cbramod, reve} × adaptation {random_full, pretrained_frozen, _peft, _partial, _full} × readout {channel_phase_linear (B1), dense_query (B2)} × objective {NCE, CS_SINGLE}; target local (FAU, DTU) / envelope (Federici) |
| C_COMPLEMENT | 600 | backbone × variant {concat_pretrained, residual_pretrained_frozen, _peft, _full, residual_random_frozen, residual_random_trainable} × objective |
| C_CAPACITY_CONTROL | 50 | residual_small_capacity (no FM) × objective |
| local reference | 50 | A_LOCAL `lag_local_tokens`, window full, d = 32, same dataset / folds / seed / objective / target (the C base) |

**Private task**, seed 3401: E_LOCAL (`lag_local_tokens` full as reference; all windows for levels), E_GX, E_GENERIC (100),
E_PUBLIC_TRANSFER (60), E_COMPLEMENT (60), E_DISTILL (120).

**D**: binding and progress only (training-side choice counts, completion counts). No D test values; D is not complete.

Not in this interim: B_LAYER_PROBE (layer panel), B_LR_PANEL, B_CTRL_ONESTEP, training curves, E_COMPLEMENT/C at other seeds,
the seed panel (§6), group × method interactions, age / stage / function associations (later HEARING_GROUP_TIME_RESULTS /
PRIVATE_TRANSFER_DEVELOPMENT rounds).

## 2. Identities and per-identity values

As SCI_R1_PREREG §2. FAU 67 test identities (TH-heldout 14, HA 29, CI 24; TH-heldout identities are tested in every outer
fold); DTU 44 (NH 22, HI 22); Federici: record → `subject_uid` via `reaggregate/entity_manifest.csv`, HC / CI / HC-v as
independent identities, the Artifact phantom excluded from every summary (its count is listed); private 64 children (HA 55,
NH 9). Per identity and configuration: the mean over that identity's units (content folds, outer folds, records → subject).
Seeds, folds and content folds never add to n.

## 3. Endpoints

**Continuous** (per identity; `auditory_alignment.aggregate.unit_rows` flattening):

- **Primary: R = `unified/regular/logloss_bits`**, the candidate cross-entropy (bits per 5 s query) of the true test segment
  among all test candidates, under the unified readout (training-side ridge from the representation to the standardised
  sound target, training-side temperature). Same readout rule for every model.
- Secondary (pointwise intervals only): `unified/gain_bits` (mismatched − regular logloss), `unified/mismatched_eeg/logloss_bits`,
  `unified/regular/top1`, `unified/regular/rank_pct`, `unified/hard_gain_bits`, `native/regular/logloss_bits` (the model's own
  score), `attention/unified/accuracy` (where competing-speech segments exist), `kernel_cs_diff` (CS_SINGLE only).

**Private** (per child): **primary `NLL` = positive-affine calibrated natural-distribution NLL (bits)**, co-primary
`AUC` = positive-affine `auc_score` (equals the native ranking); secondary `hist_gain_bits` (q_hist+EEG vs q_hist) and the twin
sensitivity `hist_gain_bits − hist_gain_twin_bits`. E_COMPLEMENT: the recorded `combined` / `local_only` NLL and AUC (same
calibration procedure for both). E_DISTILL: the record's chosen-λ evaluation vs its `baseline_lambda0_eval`.

## 4. Contrasts (continuous)

Every contrast is a within-identity paired difference written so that **positive = the candidate has lower risk**:
`ΔR = R(reference) − R(candidate)`. Identical folds / seed / objective / target; pairs whose participant sets or candidate /
query counts differ are excluded with a reason (none expected, §0).

Families (simultaneous 95% intervals by max-t over members, shared replicate indices) are defined per dataset × objective
× backbone unless stated:

| Family | Members | Reference → candidate | Label |
|---|---|---|---|
| B-READOUT | 5 | B1 `channel_phase_linear` → B2 `dense_query`, at each adaptation | readout at fixed backbone and adaptation |
| B-INIT | 8 | `random_full` → `pretrained_{frozen, peft, partial, full}`, at each readout | `pretrained_full − random_full` = **initialization (matched full update)**; the other three = **recipe contrasts** (docs/12 l.45) |
| B-ADAPT | 6 | `pretrained_frozen` → `pretrained_{peft, partial, full}`, at each readout | adaptation at fixed initialization |
| B-LOCAL | 10 | A_LOCAL `lag_local_tokens` full → each B configuration | foundation dense readout vs local model, same dense task |
| C-LOCAL (dataset × objective) | 13 | local base → each C variant × backbone, and → `residual_small_capacity` | **primary increment** `R(local) − R(combined)` |
| C-ATTRIB | 6 | `residual_random_trainable` → `residual_pretrained_full` (initialization, matched update); `residual_random_frozen` → `residual_pretrained_frozen` (initialization, frozen); `residual_small_capacity` → `residual_pretrained_{frozen, peft, full}` (capacity); `concat_pretrained` → `residual_pretrained_frozen` (residual structure, same frozen backbone) | attribution |
| C-FMONLY | 6 | foundation-only B_DENSE `dense_query` with the matched adaptation (concat / residual_pretrained_frozen → pretrained_frozen; _peft → pretrained_peft; _full → pretrained_full; residual_random_frozen and _trainable → random_full, the only random B arm, which is trainable) → each C variant | combined vs foundation alone (C uses a dense_query context branch) |

Secondary endpoints are reported for the same contrasts with pointwise intervals (for logloss-type endpoints the same sign
convention; for top1 / accuracy / gain `candidate − reference`; for rank_pct `reference − candidate`).

**Mismatched-only check** (docs/06): each C-LOCAL member is listed with ΔR and Δ of the mismatched logloss side by side; a
member whose `gain_bits` rises while the ΔR interval does not lie above 0 is labelled "mismatched-only, not a performance
complement".

**Per-group estimates** (descriptive, pointwise, groups with n ≥ 5): for the B-LOCAL and C-LOCAL members. No group
contrasts and no method choice by group in this addendum.

**ALN2 coarse interface**: the ALN2 `SpatialPatchHead` results used the 1.2 s target (docs/05 l.24). They are not
differenced against ALN3 and not re-tabulated; the within-ALN3 readout question is B-READOUT.

## 5. Contrasts (private)

Per objective (NCE, CS_SINGLE), each for NLL (`NLL(reference) − NLL(candidate)`, positive = candidate better) and AUC
(`candidate − reference`); families per objective × endpoint unless stated:

| Family | Members | Reference → candidate |
|---|---|---|
| PE-GENERIC (× backbone) | 4 | E_GENERIC `random_full` → `pretrained_{frozen, peft, partial, full}` (full = initialization contrast, others recipe) |
| PE-LOCAL | 16 | E_LOCAL `lag_local_tokens` full → each E_GENERIC configuration (10) and each E_PUBLIC_TRANSFER configuration (6) |
| PE-TRANSFER | 6 | non-transferred twin → E_PUBLIC_TRANSFER: source `lag_local_tokens` → E_LOCAL `lag_local_tokens` full twin; source cbramod / reve `task_partial` → E_GENERIC same backbone `pretrained_partial`, `task_full` → `pretrained_full` (the runner's own adaptation map) |
| PE-COMPLEMENT (× backbone) | 5 | `local_only` → `combined` for the 3 variants (within record); `residual_random_trainable` combined → `residual_pretrained_{frozen, peft}` combined (recipe contrasts) |
| PE-DISTILL | 12 | λ = 0 baseline → chosen λ, per teacher policy × window (within record) |

Levels (mean and interval) for every private configuration, including E_GX per window and E_LOCAL per architecture × window.
Per-group levels for HA and NH (NH n = 9). Cells with n < 5 report n only. No age / duration / stage / function analysis here.

## 6. Statistics and seeds

- `sci_r1.stats` unchanged: bootstrap-t with per-replicate studentisation, B = 4,000; pointwise symmetric bootstrap-t
  intervals (percentile intervals as a secondary column); families: max-t over members sharing replicate b of the identity
  resampling, seeded by `group_seed(family label)`. Non-finite values are excluded upstream with a listed reason.
- All intervals condition on the seed-3401 training; they are not training-seed uncertainty. Every table is labelled
  "seed 3401 only". No p-values; "interval excludes 0" is descriptive.
- **Seed panel supplement** (later; the per-seed loop is a small code extension, registered with its sha256 in a short note
  before it runs; contrasts, families and endpoints unchanged): when every unit of a registered ADDENDUM_03 panel cell (3401, 3407, 3413) of
  both reference and candidate is complete, the identity value is the mean over the three seeds, and each table lists the
  per-seed estimates, mean, range and SD (docs/12 §5). Contrasts without a complete common seed set report the seed-3401
  value and the missing status; no per-method best seed.

## 7. Interpretation grid (fixed now)

For a contrast with simultaneous interval I:

| Contrast | I > 0 | I < 0 | I contains 0 |
|---|---|---|---|
| B-READOUT | dense_query readout lowers true-query risk vs phase-linear under this backbone / adaptation (a time-interface effect within ALN3) | phase-linear lower | no readout difference resolved |
| B-INIT `pretrained_full − random_full` | pretraining-prior benefit under matched full update | random initialization lower risk | no prior benefit resolved |
| B-INIT other members, B-ADAPT | recipe / adaptation comparison only | — | — |
| B-LOCAL | this FM configuration has lower risk than the local model | local lower | not resolved |
| C-LOCAL | combined lowers true-query risk vs the local base (**performance complement** for that variant) | combined worse than local (training made it degrade) | no complement resolved |
| C-ATTRIB initialization | gain depends on pretrained weights (vs same-structure random) | random better | pretrained vs random not resolved |
| C-ATTRIB capacity | pretrained branch beats a similar small branch | small branch better | capacity explanation not excluded |
| C-ATTRIB residual vs concat | residual structure lowers risk vs concatenation | concatenation lower | residual structure not shown necessary |

The word "complement from the pretrained representation" is used only for a variant with C-LOCAL I > 0 **and** both of its
C-ATTRIB initialization and capacity members I > 0. A C-LOCAL I > 0 without them is written as "added branch lowers risk;
source (pretraining vs added capacity / structure) not separated". Datasets, objectives and backbones are not pooled;
consistency is described by counting cells. Private NLL gains with unchanged AUC are written as calibration / probability
changes, not a stronger signal (docs/08 §5).

**Forbidden in the reports**: "FM better/worse" in general; any seed-stability claim from seed 3401; "dense better than
the ALN2 coarse interface"; complementarity from `gain_bits` or mismatched loss alone; any HA/CI, age or development claim;
attributing C gains to the "correct pretrained EEG observation" (the mismatched-FM-context and position-only controls of
docs/06 last line are **not implemented** in the C records; listed as pending).

## 8. Outputs and privacy

- `docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md`, `docs/auditory_alignment_v3/C_COMPLEMENT_RESULTS.md` (neutral
  tables; the C document ends with the D binding / progress section); aggregate JSON in `results/auditory_alignment_v3/bc_interim/`.
- Per-identity tables: `private/auditory_alignment_v3/bc_interim/agg/` (0700).
- Private E aggregates and `PRIVATE_E_INTERIM.md`: `private/auditory_alignment_v3/bc_interim/private/` (0600 files, 0700 dir).
  Not a publication candidate without the user's approval; no child id, name, date or per-child value in any output.
- Nothing is pushed to GitHub in this round.

## 9. Engineering checks (no performance thresholds)

- E1 coverage: every expected unit present and complete; identity counts per dataset / group as §2; missing → listed, the
  cell reported on the available identities with the count.
- E2 pairing: every pair has identical participant sets and candidate / query counts (continuous) or child sets (private).
- E3 synthetic tests (before any real-data run): known paired differences and signs recovered; family intervals ⊇
  pointwise intervals; record parsing for every family; privacy scan catches a planted child id.
- E4 privacy scan of every written public file.
- E5 code sha256 at freeze in `IMPLEMENTATION_RECEIPT.md` §9; one CPU Slurm job; the analysis code is not part of any
  training code hash.
