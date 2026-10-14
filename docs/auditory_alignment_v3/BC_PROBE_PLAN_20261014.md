# B / C localisation probes — plan (2026-10-14)

**Status**: written and frozen (0444) before any probe ran. The sha256 is in `private/auditory_alignment_v3/probe_bc/code_sha256_at_freeze.txt`.
User instruction 2026-10-14: "两个都按你推荐的做，先跑定位探针" (run the probes proposed in `BC_INTERIM_QC_NOTES.md` §5 and hold
the remaining B/C/E seed repeats and D FM/complement arms).

These are engineering / localisation probes, not new method comparisons. They:
- add no plan rows and no performance thresholds;
- use one cell, FAU NCE, subject fold 0, content fold 0, seed 3401 (the first cell of the plan; not chosen on any result);
- use training participants only, except P0 and P1;
- are reported in full, whatever the outcome.

Already seen: everything listed in ADDENDUM_05 §0, plus the generated B/C interim results and the QC notes.
`B_LAYER_PROBE` test values have **not** been seen.

## P0 · Frozen-backbone layer probes (existing B_LAYER_PROBE units; CPU)

- **Data**: the 150 complete seed-3401 units, i.e. cbramod / reve × {patch_embedding, middle, last} × all folds. Each is a
  training-side ridge with a time-frequency basis on frozen pretrained tokens.
- **Method**: ADDENDUM_05 identity-level levels (R, gain, top1, rank%), plus the pointwise contrast against the same-fold
  local model `lag_local_tokens` full (NCE and CS_SINGLE separately), using the `bc_interim` functions.
- **Reading**:
  - If some frozen layer clearly carries stimulus-locked information (gain well above the trained B readouts) → the trained
    readouts fail to extract what the backbone has.
  - If every layer, including patch_embedding, is at the trained-readout level or near chance → the FM input path or backbone
    features do not carry the stimulus at this time resolution.

## P1 · C evaluation-path equivalence (GPU)

- **Model**: the C unit (reve, `residual_pretrained_frozen`), rebuilt strictly from its checkpoint, with the residual's last
  layer set to zero, so the output is the frozen local base.
- **Method**: evaluated with `fm_complement.evaluate_complement` (unchanged), then compared per participant with the
  same-fold A_LOCAL record.
- **Reading**:
  - max |difference| ≤ 1e-4 bits in the `unified` / `native` regular, mismatched and hard metrics → the C path reproduces
    local, and the C-vs-local differences are training effects;
  - otherwise → the C-vs-local comparison is confounded by the evaluation path. The magnitude is reported.

## P2 · Train / evaluation query consistency (GPU)

For the B units reve `pretrained_frozen` × {`dense_query`, `channel_phase_linear`}, on 32 training-participant early-stopping
segments:
- the representation from the training path (`DenseBatcher.dense_rows` → `model(context, t / fs)`) against `DenseReps.u` at
  the same segment and offsets;
- the training audio start `s0_train` against the segment `s0` used by the evaluation.

**Reading**: max |Δu| ≤ 1e-4 and identical audio starts → consistent; otherwise → a train/evaluation mismatch (a bug).

## P3 · Lag scan, training side (GPU)

- **Models**: local base (`lag_local_tokens`), B reve `pretrained_frozen` × {dense_query, channel_phase_linear}, B reve
  `random_full` channel_phase_linear, B cbramod `pretrained_frozen` channel_phase_linear.
- **Data**: 300 fit and 160 early-stopping segments of the training participants (fixed rng 20261014).
- **Method**:
  - For Δ = −43 … +43 grid steps (±1 s): ridge u(t) → standardised target A(t + Δ), fitted on the fit segments.
  - α from {1e-3 … 1e3} is chosen on early-stopping half A; the mean Pearson r over target dimensions is reported on half B.
  - Noise floor: Δ = 0 with A from another segment (roll).
- **Reading**:
  - Local is the control: peak expected at |Δ| ≤ 1.
  - FM peak at |Δ| ≤ 1 and above the floor → aligned but weak.
  - Peak elsewhere and above the floor → time misalignment.
  - No Δ above the floor + 0.02 → no stimulus-locked information extracted.

## P4 · Query sensitivity of `dense_query` (GPU)

On the early-stopping segments of P3, for the same models:
- the fraction of u variance across query times within a segment;
- the mean cosine similarity of adjacent queries;
- the within-patch vs between-patch variance.

**Reading**: within-segment fraction < 0.05, or adjacent cosine > 0.99 → the readout ignores query time.

## Deferred

A C variant with a `channel_phase_linear` context branch and a zero-residual (epoch-0) checkpoint candidate. It would be a new
registered variant; whether and how to run it depends on P0–P4.

## Outputs

- `private/auditory_alignment_v3/probe_bc/` (JSON + logs);
- a neutral `docs/auditory_alignment_v3/BC_PROBE_RESULTS.md`.
