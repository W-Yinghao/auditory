# ALN3 Addendum 08 — private researcher summary: group, age and hearing-aid stage of the completed E units, 2026-10-14

**Status**: written before any age / stage / group association of an ALN3 E unit was computed. Frozen (0444); sha256 in
`ALN32_IMPLEMENTATION_RECEIPT.md`. Basis: ALN3.2 package docs/07 (deliver the completed private E findings privately, with
age / HA-stage analyses and n per endpoint). User instruction 2026-10-14: "go". This document contains no child-level
value; the output is private (0600) and not a publication candidate.

## 0. What has been seen

- The ADDENDUM_05 private E interim (levels and method contrasts, `PRIVATE_E_INTERIM.md`).
- The SCI_R1 private results: S4 group / age / stage associations of the E_LOCAL `lag_local_tokens` representation curves
  and of raw curves.
- The earlier rounds listed in SCI_R1_PREREG §0 (NEXTMAP age signal at 160–200 / 440–560 ms, null SIR / MUSS, kernel CS
  private task ≈ 0).
- **Not computed before**: any association of an ALN3 E unit's task scores with age, wearing duration, HA stage or group.

## 1. Configurations (fixed; not chosen on any result)

| Family | Configuration | Objective |
|---|---|---|
| E_LOCAL | `lag_local_tokens`, window full | NCE; CS_SINGLE |
| E_GX | GX native, window full | GX_NATIVE |
| E_GENERIC | reve and cbramod × {`pretrained_full`, `random_full`} (recipe contrasts, CORRECTION_01) | NCE |
| E_PUBLIC_TRANSFER | source `lag_local_tokens`, `task_full` | NCE |
| E_COMPLEMENT | reve `residual_pretrained_frozen`, combined | NCE |
| E_DISTILL | `local_teacher`, window full, chosen λ | NCE |

## 2. Endpoints and covariates (per child, from the unit records)

- **Endpoints**:
  - AUC: positive-affine `auc_score` (= native ranking);
  - NLL: positive-affine natural-distribution NLL, bits;
  - history increment `hist_gain_bits`, where the record has it.
- **Covariates**: `age_months` (calendar age); `duration_months` (HA wearing duration; not applicable for NH, never filled
  with 0); HA stage bins fixed earlier (0–2, 2 < m < 13, ≥ 13 months of wearing).
- **Collinearity**: age = fitting age + duration. Age and duration models are therefore fitted **separately**, never as
  three independent axes.

## 3. Analyses (each configuration × endpoint)

1. **Group**: HA − NH, independent-group bootstrap-t (`sci_r1.stats.contrast`). Descriptive; NH n = 9.
2. **Age** (HA): OLS endpoint ~ age in years, coefficient with bootstrap-t interval (`sci_r1.stats.ols`).
3. **Duration** (HA): OLS endpoint ~ duration in years, the same.
4. **Stage** (HA): mean per stage bin; contrasts against 0–2 months (independent groups). A bin with n < 5 reports n only.

The intervals are pointwise. The number of configuration × endpoint × analysis cells is reported with the tables, and no
cell is singled out as a finding. n is reported for every cell. Children without the covariate are excluded from that
analysis only, with a count.

**Interpretation**:
- An interval excluding 0 is an observation for that configuration and endpoint, not a developmental mechanism.
- Absence of a resolved association is not evidence of no effect. With n ≈ 55 HA children and weak task signal, the
  precision is limited, and this is stated with the tables.
- No method is chosen by these associations.

## 4. Output

`private/auditory_alignment_v3/bc_interim/private/PRIVATE_RESEARCHER_SUMMARY.md` and `private_age_stage.json`, both 0600.
The summary contains:
- the ADDENDUM_05 private interim tables (unchanged);
- the §3 tables;
- n per endpoint;
- pointers to SCI_R1_PRIVATE_RESULTS and R_PRIVATE_CALIBRATION_RESULTS.

No child id, name, date or per-child value appears in any output. A privacy scan runs on every written file.
