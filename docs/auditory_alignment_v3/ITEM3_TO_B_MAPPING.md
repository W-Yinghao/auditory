# ITEM3_TO_B_MAPPING — item-3b/3c training arms carried by ALN3 workpackage B (2026-10-11)

Required by ALN3.1 (`amendments/ALN3_1_DECISIONS.md` §3). Old registration: `docs/auditory_alignment_v2/ITEM3_PREREG_FROZEN.md`
(read-only, sha256 `c7590820…`) with addendum 01 (user-approved fold-in, 2026-10-10). None of the 400 old training units was
ever trained; the user's go for them was replaced by the fold-in before any started. Exact ids: 
`private/auditory_alignment_v3/governance/item3_to_b_mapping.json` (one entry per old unit: old id, old base unit, new
comparison ids by readout/control family, changes, source checkpoint, live status; regenerate with
`private/auditory_alignment_v3/make_item3_mapping.py`).

| old arm (units) | preserved question | B rows per old unit (seed 3401, same cohort / folds / architecture / adaptation / objective) | what changed | source checkpoint | status (02:52) |
|---|---|---|---|---|---|
| X_PHASE (100: frozen / peft × 2 arch × NCE × 25) | 3b: does finer temporal phase / relative-time alignment help the foundation readout? | B_DENSE dense_query (1) + B_DENSE channel_phase_linear (1); B_LR_PANEL (2) and B_CTRL_ONESTEP (1, peft only) as recipe references | time target dense20ms_v1 (20 ms rows, relative-time query) and the phase-linear readout replace random 0.25 s phase offsets on 1 s patch rows; ALN3 recipe | public pretrained backbone (same init as the ALN2 B_FM unit); the ALN2 unit stays the legacy comparator | B rows 129 complete / 3 running / 1,418 pending over all three arms |
| X_FT_VAL (150: full / partial / peft × 2 arch × NCE × 25) | 3c-1: checkpoint-selection granularity (every epoch vs every E/20) | B_DENSE dense_query (1) + channel_phase_linear (1); B_CTRL_ONESTEP (1 for peft/full: the E/20 one-step recipe) | per-epoch development validation is the B default; dense target | as above | as above |
| X_FT_REG (150: same grid) | 3c-2: lower backbone lr with layer-wise decay 0.75 | B_DENSE dense_query (1) + channel_phase_linear (1); B_CTRL_ONESTEP (1 for peft/full); B_LR_PANEL (2 for peft/full: backbone lr × 0.3 / × 3) | layer-wise decay 0.75 and fixed lower backbone lr (partial/full 1e-5, PEFT 1e-4) fixed before results; the lr panel replaces X_FT_REG's development-side re-selection | as above | as above |

Item-3a (X_READOUT_DIAG, 500 evaluation units) is complete and stays an evaluation-only diagnostic
(`docs/auditory_alignment_v2/ITEM3A_RESULTS.md`); it is not a launch gate for A, B or the private families.

Reading rule: a B_DENSE row answers the folded-in question only in comparison with its matched rows (same cohort, folds,
architecture, adaptation, objective): phase question = channel_phase_linear vs dense_query and both vs the ALN2 1 s-row unit;
recipe questions = B_DENSE (ALN3 recipe) vs B_CTRL_ONESTEP (ALN2 one-step recipe) and B_LR_PANEL (× 0.3 / × 3). The old
`pretrained_partial` arms have B_DENSE rows but no one-step / lr-panel control (those were registered for peft and full only);
report them as such.
