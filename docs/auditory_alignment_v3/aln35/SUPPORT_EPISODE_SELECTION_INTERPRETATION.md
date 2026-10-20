# ALN3.5 support / episode / matched updates / true-risk selection — interpretation

Claude Code, 2026-10-20. Interpretation of the complete automatic summary **1050758**
(`results/auditory_alignment_v3/aln35/support_summary_v1/snapshots/job_1050758_20261020T015908062290Z/summary.json`,
analysis `S35_SUPPORT_SUMMARY_v1.1`, 0 validation issues). No model was trained and no statistic was recomputed;
numbers are read from that summary. All contrasts are `exploratory` and labelled as in the summary.

Conventions: true-query NLL in bits per query (DTU) or per trial (private); **positive = the first-named arm is
better** (lower NLL). Intervals are the summary's simultaneous 95% intervals (4,000 person-stratified draws, fixed
original SE, max-|z*| within family). n = people: DTU 44, private 64. Seeds, folds and draws are not extra n.
"+" interval above 0, "−" below 0, "0" includes 0. An interval that includes 0 does not show equivalence.

## 1. Matched updates: more source people at the same number of updates (DTU, seed 3401)

`EEG50_vs_EEG100_at_fixed_U`: 50% of source EEG people vs 100%, identical actual optimizer-update count U.

| Configuration | native | unified |
|---|---|---|
| local | −0.471 [−0.551, −0.392] | −0.267 [−0.313, −0.222] |
| CBpre | −0.771 [−0.857, −0.685] | −0.409 [−0.474, −0.345] |
| CBrand | −0.765 [−0.843, −0.686] | −0.463 [−0.507, −0.419] |

All six favour 100% people. The ALN3.4 data curves confounded fewer people with fewer optimizer steps
(`aln34/DATA_AND_INNER_DESIGN_20261017.md`); at matched updates the person effect remains large. Equal updates are
not equal independent samples or FLOPs (50% repeats its people more often). CBpre and CBrand lose about the same
here, so this contrast says nothing about pretraining.

## 2. True-risk vs inherited gain checkpoint selection (DTU)

`true_risk_vs_inherited_gain`: source-side inner-query true-risk rule vs the inherited mismatch-gain rule, same
trajectories and candidate states (epoch 0/.25/.5/1 U).

| Configuration | EEG 50% | EEG 100% |
|---|---|---|
| local native | +0.100 [+0.041, +0.160] | +0.010 [−0.030, +0.051] |
| local unified | +0.121 [+0.085, +0.156] | +0.040 [+0.008, +0.073] |
| CBpre native | +0.331 [+0.263, +0.399] | +0.011 [−0.020, +0.042] |
| CBpre unified | +0.255 [+0.200, +0.310] | −0.001 [−0.034, +0.033] |
| CBrand native | +0.289 [+0.212, +0.367] | −0.007 [−0.058, +0.044] |
| CBrand unified | +0.162 [+0.102, +0.221] | +0.035 [+0.005, +0.066] |

With limited source people, gain-based selection chooses states with clearly higher true risk; with full data the
two rules mostly coincide (two small favourable unified cells, none unfavourable). Neither rule picked epoch 0
except one CBrand-unified 50% decision (10%). Mismatch gain can rise because mismatched pairs get worse, so it
should not be the default selection criterion where a declared source-side true-risk query exists.

## 3. Support amount, coverage and adapter type

**DTU** (local/CBpre × native/unified; rank4 = input low-rank spatial adapter with NCE, 20 steps):

| Contrast | Range over the 4 configurations | Status |
|---|---|---|
| rank4 vs zero-step, U30 | +0.024 … +0.093 | + in 4/4 |
| rank4 vs zero-step, U10 / C10 | +0.005 … +0.028 | 0 in 8/8 |
| rank4 vs probability-only, U10 / C10 | +0.133 … +0.324 | + in 8/8 |
| rank4 vs probability-only, U30 | +0.027 … +0.108 | + in 3/4 (CBpre unified 0) |
| U30 vs U10, rank4 | +0.016 … +0.065 | + in 4/4 |
| U30 vs U10, probability-only | +0.176 … +0.261 | + in 4/4 |
| C10 vs U10 (same count, content round-robin) | −0.057 … +0.052 | 0 in 8/8 |

On DTU more support helps, the low-rank adapter beats calibration-only, and with 30% support it also beats no
update. At equal count, content-balanced composition shows no detectable change; the original 10/30 difference
therefore behaves mainly like a quantity effect here (coverage effects smaller than these intervals are not excluded).

**Private children** (local/CBpre × linear/native; rank4 = output adapter): all NLL effects ≤ 0.006 bits/trial and
AUC effects ≤ 0.001.
- rank4 vs zero-step is slightly unfavourable at 10% support for the linear readout (U10 −0.0015/−0.0024,
  C10 −0.0035/−0.0061, H10 −0.0032/−0.0049, CBpre/local) and ≈0 at U30; native readouts ≈0.
- U30 vs U10 is small and favourable (probability-only +0.005 … +0.007).
- C10 and H10 vs U10 under probability-only are clearly unfavourable (−0.048 … −0.058). **Checked from the
  existing records** (`results/auditory_alignment_v3/aln35/support_prior_shift_check_v1/summary.json`, Slurm
  step in 1047358; person × condition × unit records, not independent n): support deviant fraction is C10 0.496,
  H10 0.297, U10 0.204, U30 0.201 (query ≈ 0.20). The temperature grid {0.5, 1, 2} then selects T = 2 in 100% of
  C10 and ~90% of H10 records versus T = 1 in ~90% of U10 and 100% of U30, flattening query probabilities
  (entropy 0.91 vs 0.71–0.73 bits) and raising natural-ratio query NLL (0.777 vs 0.715–0.723). The loss is a
  class-prior mismatch in temperature-only calibration, not a measured harm of coverage. Rank4 changes little
  (−0.004 … 0). A coverage comparison on the private task would need prevalence-matched calibration (e.g. a fixed
  source temperature or prior-corrected support weighting).

The private current-sound task leaves very little personal-adaptation headroom at the present representation
quality (per-child AUC ≈ 0.55).

## 4. Episode pressure (60 bundles; 58 original + 2 lineage successors)

Episode vs ordinary use matched encoder updates; pressure = 20 or 100 inner support steps per source episode.

| DTU configuration | pressure 100: episode vs ordinary (U10 / U30) | episode vs source | selected episode vs selected ordinary |
|---|---|---|---|
| local native | **+0.034 [+0.012, +0.057] / +0.036 [+0.014, +0.059]** | +0.045 / +0.047 (+) | +0.024 / +0.034 (+) |
| local unified | +0.010 / +0.013 (0) | +0.013 / +0.015 (+) | ≈0 (0) |
| CBpre native | −0.015 [−0.031, +0.000] / **−0.018 [−0.035, −0.001]** | 0 | ≈0 (0) |
| CBpre unified | +0.012 / +0.009 (0) | 0 | +0.010 / +0.012 (+, lower bound ≈0) |

- Pressure 20: every DTU contrast includes 0 (|estimates| ≤ 0.011).
- Private: all |estimates| ≤ 0.0002 bits/trial; a few intervals exclude 0 at that scale. No practical change.
- Policy diagnostics: on DTU the inner-selected rule chose zero steps in 20–40% and the source fallback in 30–48% of
  decisions; private 5–15% and 20–35%.

Earlier "episode gives nothing" came from the old 3-step version (ALN3.4). With 100 inner steps, episode training
helps the local native model and slightly hurts CBpre native at U30; the effect depends on backbone and readout.
This is one seed (3401) and one cohort (DTU).

## 5. What this changes

| Research concern (ALN3.5 docs/00) | Update from 1050758 | Not supported |
|---|---|---|
| What does a new listener need? | Support quantity matters on DTU; content composition at equal count shows no detectable effect; a constrained low-rank update beats calibration-only. | That coverage is irrelevant; that the private task benefits from adaptation. |
| Does group (episode) training make adaptation easier? | Yes for local native at pressure 100 (+0.03–0.05 bits); not for CBpre. | A general episode advantage across backbones, seeds or cohorts. |
| How should a model be chosen? | Source-side true-risk selection is never worse and much better with limited data. | That true-risk selection improves full-data models in general. |
| Shared structure across people | More source people help strongly even at equal updates. | That pretraining (CBpre vs CBrand) matters for this contrast. |

## 6. Suggested follow-ups (not started)

1. ~~Check the private C10/H10 prior-shift explanation~~ — done 2026-10-20, confirmed (see §3).
2. Replicate local-native pressure-100 episode vs ordinary on FAU (or a second DTU seed) before treating it as a
   general mechanism; no matrix expansion.
3. Make source-side true-risk selection the default rule for new limited-data trainings; keep gain as a reported
   diagnostic.
4. Read the matched-updates result together with the final ALN3.4 data curves when DTU curves (215/440) finish.
