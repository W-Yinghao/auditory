# ALN4.2 source-learning diagnosis (package docs/03; seed 3401; 2026-10-21)

This is a mechanism diagnosis designed after R1. It changes no production training, selection or statistics.

- **What was evaluated:** the ALN4.1 production checkpoints at updates 0 / 2500 / 5000 / 10000 of TCS, TNCE, GCS and TCS_WRONG.
- **Panel, one fixed for every arm and snapshot:**
  - fit: the first 32 production episodes;
  - dev: 32 episodes drawn from the source-dev pool with the production sampler, seed 348201. 9 of the 10 dev people meet the
    production eligibility.
  - Each episode is 2 people × S32 / Q32 × 3 crops × 3 views.
- **Mode:** eval (dropout off), which is the mode of every frozen downstream use.
- **Code:** `auditory_alignment_v3/aln42/source_diag.py` (plan `c300d2a2…`) and `source_diag_report.py`.
- **Outputs:** `results/auditory_alignment_v3/aln42/source_diag/`:
  - `SOURCE_DIAG_SUMMARY.json`;
  - `source_probe_person.jsonl.gz` (2,048 person rows, opaque person hashes);
  - `source_gradient_audit.json`;
  - `helper_crosscheck.json`.
- **Cost:** 0.18 GPU-h in total, against the 4 A100-equivalent-hour cap.
- **Zero updates:** no optimizer was constructed. The model-state digest is unchanged after every snapshot.

## A. Did the correct sound pairing become discriminable?

**No, in any arm, at any snapshot.** This is measured on the projected EEG against the fixed audio heads, with the production
packed-key masks, as a common read-only probe.

- **Retrieval at chance:** correct-pair top-1 retrieval on Q is 0.027–0.035 in every view, slot and arm. Chance is 1/32 = 0.031.
- **No margin:** positive and legal-negative score means are equal to within ±0.02.
- **TNCE reaches the uniform baseline by collapse, not by learning:**
  - Its query loss starts at 4.50 nats, above the exact uniform-score baseline of ln 32 = 3.466 (each row has one positive and
    32 allowed candidates). From update 2500 on it sits at 3.465.
  - It gets there by collapsing the projection heads: the projected effective rank falls from 18 to 3.3–3.6, and the mean
    pairwise cosine of projected anchors rises to 1.00.
  - In other words, it removed an initial below-chance alignment. It did not learn above-chance pairing.
  - This explains why the R1 log shows the TNCE loss "at chance" for 9,800 updates.
- **CS scores** (common TCS-potential probe, eval mode):

  | Arm | Update 0 | Update 10000 |
  |---|---|---|
  | GCS | 0.011 | 0.020 |
  | TCS_WRONG | 0.011 | 0.019 |
  | TCS | 0.011 | 0.005 |
  | TNCE | 0.011 | 0.000 (collapsed) |

  - TCS's train-mode objective in the R1 log rose slightly, but in eval mode its dependence on this fixed panel fell.
  - TCS_WRONG's correct-pair probe rose exactly as much as its wrong-pair training target (0.0109 → 0.0189). So the CS
    dependence these sources learned is **not specific to the correct anchor pairing**.
- **Package helper cross-check:** `tools/source_probe_metrics.py`, run on the exported fit-episode-0 bundles, reproduces this
  module's NCE values and the ln 32 baseline to 1e-15.

## B. Did the change happen in the projection heads or the backbone?

**Both changed substantially.**

- **Raw backbone tokens:**
  - Relative change from update 0 on identical inputs:

    | Arm | Change |
    |---|---|
    | TNCE | 21× |
    | GCS | 13× |
    | TCS_WRONG | 5.5× |
    | TCS | 2.9× |

  - Effective rank of the slot tokens over 32 anchors:

    | Arm | Update 0 | Update 10000 |
    |---|---|---|
    | TCS | 29 | 17 |
    | TNCE | 29 | 18 |
    | GCS | 29 | 11 |
    | TCS_WRONG | 29 | 11 |

- **Projections:**
  - TNCE collapsed, as described above.
  - TCS kept rank about 12 but became very similar across anchors (mean cosine 0.67).
  - GCS and TCS_WRONG spread out (cosine about 0.01–0.04, rank about 10).
- **The common ridge probe cannot rank readability.**
  - It refits the original 512 / 512 probe per snapshot, with λ = 1e-3·trace/n unchanged.
  - It interpolates the fit panel (fit NMSE ≈ 0.000) and stays worse than the fit mean on dev at every snapshot. Dev NMSE is
    1.28 at initialisation and 2.0–2.7 after training.
  - Kernel effective rank falls from 382 to 86–137, and the condition number is about 1e4.
  - This limits that LR criterion (which only ranked the two learning rates in R1). It is not evidence that EEG lacks sound
    information.
- **Together with R1:** TNCE gave the best frozen downstream content readout *after* its projection collapsed. The useful change
  is therefore in the backbone tokens, which the downstream PCA readouts use, not in the projected pairing space.

## C. Did the time weights and the per-person support have any effect?

**No measurable effect.**

- **Gate stays near uniform:** q_prior stays between 0.32 and 0.35 in every arm.
- **Support δ does nothing:**
  - The per-episode δ norm is 1e-4–1e-3. The exception is TNCE at update 0, at 0.03.
  - Five support steps change the support objective by less than 1e-4 nats. The exception is TNCE at update 0, at about
    −0.002 nats.
  - The query objective improves under q_support in 36–66% of episodes, around a mean change of 0.0000 (|mean| < 1e-4).
  - So the support update neither helps nor hurts the query.
- **Gradient audit** (production first-order outer objective; first 2 fit and 2 dev episodes):
  - The data gradient on the gate logits a is small: 2e-4–3e-3. The exception is TNCE at initialisation, at 4e-2, before
    the collapse.
  - The 0.01 KL gradient is smaller still: 0 at initialisation, 5e-6–2e-4 later. The data term is 10–100× larger.
  - **The uniform gate is therefore not caused by the KL term.** The data provide almost no slot preference.
  - This is a mechanism clue only. As the package specifies, it does not start the optional KL ablation.

## D. Reproduction boundary

- **Production update path, checked against `aln41/source.py` (byte-checked in the plan):**
  - the query projection keeps its gradient;
  - the support features are computed under `no_grad`;
  - the gate logits a are in their own optimizer group;
  - δ is reset to zero in every episode (`adapt_delta_fo`);
  - the sigmas come from the frozen receipt.
- **Logged loss reproduced:** a train-mode clone at update 0 reproduces the logged "update 1" loss to 2e-11–8e-15 for TNCE, GCS
  and TCS_WRONG, and to 2.4e-4 for TCS.
- **Dropout explains the train/eval gap:** the model has dropout p = 0.1 in 37 modules and no batch norm. That is why the
  logged train-mode objectives differ from the eval-mode values above.
- **No bug found:** no misalignment, mask error, double resampling, missing gradient or wrong weight. No BUG_SCOPE_RECEIPT was
  written, and no R1 result is affected.

## What this changes in the claims

- The R1 frozen improvements cannot be attributed to the source objectives having learned the registered sound–EEG pairing.
  Under every objective, the pairing in the projection space stayed at chance. TNCE's best downstream result coincides with a
  large backbone change and a collapsed projection.
- The R1 result "TCS > TCS_WRONG mostly reflects damage done by the wrong pairing" agrees with section A. The CS dependence
  learned here does not distinguish correct from wrong anchor pairs.
- The uniform time gate and the null per-episode support effect are valid findings, marked with diagnostic flags (near-uniform q,
  low projection rank). They do not justify retraining or the KL ablation in this package.
- Explanation exits that apply, per package §3.4:
  - the backbone readout improved while projected pairing stayed weak;
  - the original probe overfits;
  - low rank and near-uniform q.
