# Correction 01 — "initialization (matched full update)" is a recipe contrast (2026-10-14)

**What was wrong.** ADDENDUM_05 §4–§5 and ADDENDUM_06 §5, and the generated tables (`B_DENSE_READOUT_RESULTS.md` B-INIT,
`C_COMPLEMENT_RESULTS.md` C-ATTRIB `init_full`, the private PE-GENERIC tables), label the contrast
`pretrained_full − random_full` as "initialization (matched full update)". The name is not supported by the code (ALN3.2
package docs/03 §1; verified against `fm_dense.py`).

1. **The learning rates differ by 30×.** `fm_dense.LR`: `random_full` backbone 3e-4, `pretrained_full` 1e-5 (head 1e-3 for both).
2. **The "full" schedule is a progressive prefix.**
   - Warm-up is 5 epochs, then one more block group every 5 epochs, top block first, with layer-wise decay 0.75.
   - REVE (22 blocks, 50 epochs) opens only the top 9 blocks by the last epoch and never its non-block / input parameters.
   - CBraMod (12 blocks, 100 epochs) opens all blocks and the non-block group from epoch 66.
   - The nominal lr of the deepest REVE block is 0.75^21 ≈ 0.0024 × the base value.
3. The C variants `residual_pretrained_full` vs `residual_random_trainable`, and the private `E_GENERIC` / `E_PUBLIC_TRANSFER`
   recipes, inherit the same lr table and schedule.

**Corrected reading.**
- These contrasts compare two recipes: different initialization *and* a 30× different backbone lr, under the registered
  progressive-prefix schedule. They are not a pure initialization effect, and not "full" backbone training.
- The data, the intervals and their sign are unchanged. Only the label and its interpretation change. The ADDENDUM_05 §7 and
  ADDENDUM_06 §5 grid rows "pretraining-prior benefit under matched full update" do not apply to them.
- A genuine matched initialization contrast is registered as ALN32_TRUE_FULL (ADDENDUM_07 TF-INIT). There, random and
  pretrained share the schedule, the numeric lr cell, the data and the selection, and all allowed parameters are updated.

**What is not changed.** Frozen addenda and generated result files stay as they are (0444 / as generated). This note is the
correction of record. The ALN3.2 reports and the next regeneration of the tables use the corrected label. The per-unit
update coverage (open groups per epoch, nominal lr per group, measured weight change for a registered subset) is in
`EFFECTIVE_UPDATE_REPORT.md`.

Owner: the error is mine (assistant). It was caught by the ALN3.2 package review.
