# ALN3 Addendum 04 — binding the D policy arms (dense_fm_policy / complement_policy), 2026-10-13

Written after every seed-3401 B_DENSE and C_COMPLEMENT unit had completed (2026-10-13 10:58) and before any D policy-arm unit
or probe ran. The selection rule in §1 was approved by the user on 2026-10-13 ("plan I go"). No test/query result of any B, C
or D unit was read to make the choices below; the rule reads only the training-side selection score that each B/C unit already
used to pick its own checkpoint.

## 1. Training-only model policy (logical dependency `training_only_model_policy`)

For a policy-arm row with dataset Δ, subject fold k, content fold c, seed s and objective o (`SELECTION_CE` maps to `NCE`, the
objective whose calibration the selection trainer uses):

- `dense_fm_policy` candidates: the B_DENSE rows with (Δ, k, c, s, o) and target `local` — 2 backbones × 5 adaptations × 2
  readouts = 20 units.
- `complement_policy` candidates: the C_COMPLEMENT rows with (Δ, k, c, s, o) and target `local` — 2 backbones × 6 variants =
  12 units. C_CAPACITY_CONTROL, B_LR_PANEL and B_CTRL_ONESTEP are controls, not candidates.
- Chosen unit = the candidate with the **lowest recorded `best_selection_score`**: the training participants' early-stopping
  loss minus its within-batch mismatched value at the unit's selected checkpoint. All candidates of one cell share the same
  early-stopping content. Ties break on the experiment id.
- A cell resolves only if every candidate has a complete record and a checkpoint. Otherwise the row stays
  `technical_pending`; no other fold, seed or test-chosen model is substituted.
- Each D record stores the candidate ids with their scores, the chosen id, the rule string and the chosen unit's checkpoint path.

## 2. Per-family bindings

Principle: the policy chooses the configuration; the family's own registered procedure (as implemented for its
`lag_local_tokens` arm) is applied to it unchanged. The complement arm stacks the chosen FM residual on the family's own
lag-local model, as C_COMPLEMENT stacks it on A_LOCAL.

**D_ADAPT** (240 rows, FAU + DTU).
- Base: the chosen unit's model, frozen and kept in eval mode during adapter updates, loaded strictly from its best
  checkpoint with the same fixed audio head.
  - `dense_fm_policy`: backbone + dense readout.
  - `complement_policy`: A_LOCAL base + FM context + residual / concat head.
- Adapters as for the lag arm:
  - `none`;
  - `input_spatial`: a C×C identity-initialised map on the EEG input; for the complement model the same map feeds the local
    patches and the FM context;
  - `output_low_rank`: rank 4 on the d = 32 output.
- Unchanged from `run_adapt3`: the support/query protocol (first 10 % / 30 %, last 70 %), the step choice from {20, 50, 100}
  on training participants' early-stopping content, readouts fitted on training participants with the base model, and the
  metrics.

**D_COVERAGE `complement_policy`** (60 rows, FAU).
- For population P (TH_ONLY / TH_HA / TH_HA_CI) and control (full_available / matched_exposure), the base is the D_COVERAGE
  `lag_local_tokens` unit with the same (P, fold, content fold, seed, objective). Its fit of the same control is loaded and
  frozen.
- The chosen C variant and backbone are trained on population P's training participants with the C recipe (`fm_complement`).
- matched_exposure caps optimizer updates per epoch at the TH_ONLY count, as in the lag arm. Evaluation is that of the lag
  arm; the primary readout is full_available.

**D_ATTENTION** (400 rows).
- The 200 `learned_temporal` rows are derived records of their `mean_score` twin, as for the lag arm.
- `dense_fm_policy`: the chosen B_DENSE configuration is trained from the same starting weights as B_DENSE on the row's
  training task (`attended_alignment`, `selection_only` or `alignment_plus_selection`). Same configuration means backbone,
  adaptation, readout, aln3 recipe, learning rates and epochs.
  - Same as the lag arm: the ALN2 selection machinery on competing-speech segments (SelectionScore, selection_loss); for
    `alignment_plus_selection`, a selection weight from {0.1, 1.0} chosen by training-side early-stopping 2AFC accuracy; the
    checkpoint rule.
- `complement_policy`: the base is the D_ATTENTION `lag_local_tokens` unit with the same (fold, content fold, seed,
  objective, training task) and integrator `mean_score`, frozen. The chosen C variant and backbone are trained on top with the
  same training task and a fresh selection head.
- Evaluation is that of the lag arm (dense-grid evaluation, attention windows of 5 / 10 / 20 s, `mean_score` and
  `learned_temporal`) on the FM model's representations.

## 3. Engineering

- **New code only;** the hashes of completed families are unchanged: `policy.py`, `run_adapt_policy.py`,
  `run_coverage_policy.py`, `run_attention_policy.py`, `fm_attention.py`.
  - `registry.py` (unhashed) adds the code groups `adapt_policy`, `coverage_policy` and `attention_policy`.
  - `run.py` (unhashed) routes policy-arm rows to them, so the record's `code_group` and `code_hash` are those of the policy
    group.
- **Queue:** policy arms enter the FM queue (whole card) once their policy resolves and, for the complement arms of D_COVERAGE
  and D_ATTENTION, their lag-local base is complete.
- **Offload:** `ckpt_offload.deps_of` protects the chosen unit (D_ADAPT), the lag-local base (complement arms) and the
  `mean_score` twin.
- **Probe gate before release**, one unit per family × arm.
  - Checks: the policy re-resolves identically; adapter `none` reproduces the base representation; the complement residual
    starts at its base; losses are finite; the record is complete.
- **Release order:** D_ADAPT first, then D_COVERAGE and D_ATTENTION as each is implemented and probed. Any later change to this
  binding is a dated erratum below, written before the affected units run.
