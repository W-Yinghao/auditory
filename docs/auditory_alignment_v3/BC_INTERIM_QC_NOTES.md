# B / C interim — post-hoc QC notes (2026-10-14)

These notes are **not** part of the frozen ADDENDUM_05 analysis. They were written after reading the generated
`B_DENSE_READOUT_RESULTS.md` and `C_COMPLEMENT_RESULTS.md` (job 1039549). They list training-side and readout fields that
were read afterwards to locate surprising cells. No new test-side analysis was computed.

## 1. `dense_query` (B2) is at chance in every cell

- Test side: every `dense_query` configuration has R = log2(n_candidates) with a zero-width interval, unified gain 0.000,
  rank 50 % and top1 = 1 / n_candidates. This holds for both backbones, all five adaptations, both objectives and all three
  datasets.
- Readout fields (FAU NCE, 100 units): the unified ridge selected the maximal regularisation (median α 5e7, grid maximum
  1e8). The native temperature is large (median 0.85, against 0.10 for `channel_phase_linear` and 0.005 for local). So the
  training-side calibration queries also showed no usable signal in the evaluation path.
- Training curves: the representations are not collapsed (final effective rank 17–31). But the early-stopping loss never
  goes below the chance value ln 256 = 5.545: median 5.63 at the selected epoch, against 5.52 for local. The training loss
  falls while the early-stopping loss rises. The selection score (own − mismatched) stays near 0 (median −0.005).
- `channel_phase_linear` (B1) is slightly above chance on test: FAU REVE gain ≈ 0.07 bits, DTU ≈ 0.18, Federici REVE PEFT
  0.15. For comparison, local is 1.04, 2.01 and 0.26 bits. Its early-stopping loss at the selected epoch is also above
  chance (median 5.72).
- `random_full` fails in the same way as the pretrained adaptations. On these tasks, the FM path (input, readout and
  recipe) does not learn the sound alignment that the small local encoder learns from scratch on the same data.
- Consequence for reading B-READOUT, B-INIT and B-LOCAL: the B-READOUT "I<0" cells compare a weakly learning B1 against an
  at-chance B2. They are not evidence about time interfaces until the B2 failure is located.

## 2. The C context branch uses the same `dense_query` readout

- `fm_complement.FMContext` builds `fm_dense.DenseFM(bb, "dense_query", CTX_DIM, …)`. The capacity control `SmallContext`
  (no FM) also ends in `DenseQueryReadout(1, 32, CTX_DIM)`.
- Residual variants start identical to the base: `init_max_abs_diff_vs_base` max 6e-8.
- In every FAU and DTU cell, all C variants, including random-weight branches and the no-FM capacity control, end with a
  higher true-query risk than the frozen local base. The degradation is of similar size (FAU NCE −0.07 to −0.15 bits). It
  is therefore not specific to pretrained weights.
- Checkpoint selection runs over epochs 1…E. The zero-residual initial state is never a candidate, so a branch that only
  adds noise cannot fall back to the base.
- The training-side selection score of C units (median −0.074) is close to that of local (−0.072). The selection signal
  therefore did not detect the cross-person degradation. The early-stopping content comes from the training participants.

## 3. Degenerate "I>0" cells (Federici NCE)

The five Federici NCE C-LOCAL members classed "I>0", and the two "mismatched-only" flags, have estimates below 0.0005 bits
with zero-width intervals. The residual barely moved from zero. Mechanically these are "I>0". In substance they are
identical to the local base, not a performance complement. The frozen grid set no minimal effect size; this is disclosed
here rather than reworded in the generated tables.

## 4. Link to D (training-side choices, frozen rule unchanged)

- `dense_fm_policy` chose `dense_query` configurations in all 20 CS_SINGLE cells, and REVE PEFT `channel_phase_linear` in
  18 of 20 NCE cells.
- `complement_policy` chose `concat_pretrained` in 28 of 40 cells. On test, concat is the C variant furthest below local.
- The D FM / complement arms therefore start from models whose seed-3401 test behaviour is described above. The ADDENDUM_04
  rule is training-side by design and is not changed on the basis of test results.

## 5. Checks not yet run (proposed, need compute)

1. Pipeline equivalence: evaluate a C unit with the residual forced to zero through the C evaluation path, and compare it
   per participant with its A_LOCAL record (expected: identical).
2. `dense_query` localisation, on one FAU NCE cell:
   - B2 on top of the trained local encoder's tokens (readout alone);
   - B1 vs B2 on the same frozen REVE features;
   - query-time input check (the query offsets seen in training against those seen in evaluation).
3. A C variant with a `channel_phase_linear` context branch, and an epoch-0 (zero-residual) checkpoint candidate.
   This would be a new registered variant, not a re-run.
