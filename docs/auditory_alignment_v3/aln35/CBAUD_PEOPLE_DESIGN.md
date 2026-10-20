# S35_CBAUD_PEOPLE v1 — auditory-continued vs direct CBraMod start across source-people fractions

2026-10-20, Claude Code, at the researcher's instruction to start all proposed next steps ("全部开始").
Written before any unit of this design ran. Exploratory; result-informed by the facts below.

## Question

Can paired auditory continuation of CBraMod (SparrKULee donor) substitute for target-dataset source people?

Known before this design: on DTU (seed 3401) fewer source people raise true-query risk strongly, also at matched
optimizer updates (1050758: 50% vs 100% people −0.27 … −0.77 bits/query); CBraMod pretraining matters most when
people are few (25% people, CBpre − CBrand +0.345 bits/query native); with 100% people the auditory-continued
start is not distinguishable from the direct start (CB_AUDITORY_CONTINUATION_RESULTS: +0.017 [−0.016, +0.050],
three seeds). Whether the auditory start helps when people are scarce has not been measured.

## Arms and units

DTU, seed 3401, NCE, recipe full_onestep_v1, backbone lr 3e-4, head lr 1e-3, 100 epochs, aligned_patch_linear
readout, same subject/content folds (5 × 2) and the same frozen nested people subsets as ALN3.4 data curves.

| Fraction of source people | Direct CBraMod start | Auditory-continued start |
|---|---|---|
| 0.25 | existing `data_inner_v1` ALN34S cbramod/pretrained_full rows (10, complete) | **new, 10 units** |
| 0.5 | existing ALN34S rows (10, complete) | **new, 10 units** |
| 1.0 | existing ALN32_TRUE_FULL baselines ALN3X (10) | existing cb_auditory_v1 ALN34CBT generic_paired targets (10) |

New unit = a copy of the matching ALN34S row with only the starting backbone changed to the generic_paired
seed-3401 donor's final (10,000-update) backbone; readout and audio head are rebuilt fresh (no head transfer).
Same seed, split, people subset, early-stopping rule (training-identity ES), target statistics and evaluation.
Implementation composes the frozen `data_inner.instrumentation` (split/evaluation) and
`cb_auditory.target_instrumentation` (donor backbone load) around `run_aligned32.run`; no frozen module is edited.
New family `ALN35_CBAUD_PEOPLE` with its own code hash. 20 new GPU units; nothing else is retrained.

Not included (could be added later as separate versions): the generic_wrong and random_paired donors at 0.25/0.5,
other seeds, FAU/Federici.

## Analysis (declared now)

- Endpoint: per-person true-query NLL (`eval.per_participant[<readout>/regular].logloss_bits`, bits/query),
  native and unified readouts as separate families; DTU 44 outer-test people; content folds averaged within person.
- Family per readout, columns: auditory − direct advantage (reference minus candidate risk, positive = auditory
  start better) at 0.25, 0.5 and 1.0; and the change of that advantage, (0.25) − (1.0) and (0.5) − (1.0).
- Intervals: `sci_r1.stats.summary` identity bootstrap-t, B = 4000, simultaneous max-|t| across the family's
  columns; also the same per hearing group (HI, NH) descriptively.
- Also reported: absolute risks per arm and fraction, actual optimizer steps and best epochs.
- No performance gate, no outer-test selection, no person/seed selection. Single seed, single cohort: a
  favourable or unfavourable result constrains this donor and recipe, not auditory pretraining in general.

## Execution

Engineering smoke: one 2-epoch unit per fraction (truncated, excluded from production). Production requires a
passing smoke receipt bound to the plan hash. GPU work is runfill under the project's 10-GPU cap, launched by the
single fleet coordinator through a registered plugin; checkpoints go to the `/projects` private store.
