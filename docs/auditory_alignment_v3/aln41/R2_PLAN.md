# ALN4.1 R2: what is frozen and running (2026-10-21)

Researcher instruction: "开始两个R2，跨刺激问题你来提方案". This follows package `plans/closure.json` R2, fixed before R1.
R1 results did not change the scope.

## Core replication (seeds 3407 / 3413)

- **Runner:** `auditory_alignment_v3/aln41/r2.py`. The R1 modules `source` / `private_ft` / `frozen` stay byte-identical.
  For one seed they are re-pointed to the following, and nothing else changes:
  - `SEED`;
  - the derived episode stream seed (seed + 41000, as R1 used 3401 + 41000);
  - the output and store roots: `private/auditory_alignment_v3/aln41/r2/seed<S>/` and the matching private checkpoint store.
- **Unchanged from R1:** pool, eligible people, panels (byte-copied, hash-checked), inner settings, sigma rule, optimiser and
  snapshots.
  - LR is not re-selected: every arm uses its R1 `selection.json` choice, 1e-4.
  - Sigmas are re-fixed at each seed's initial state with the R1 rule, because the projection heads are seeded.
- **Units per seed:**
  - 4 source productions (TCS / TNCE / GCS / TCS_WRONG, 10 000 updates);
  - 15 private CE fits (B0 / TCS / TNCE × 5 folds);
  - 20 frozen extractions (the four non-B0 arms × DTU cf0/cf1, FAU cf0/cf1, private).
  - B0 frozen does not depend on the seed (generic CBraMod, PCA seed 3437), so the R1 B0 units are reused.
- **Plans (sha256):**

  | Plan | Seed 3407 | Seed 3413 |
  |---|---|---|
  | source | `0236ceef…` | `2362bd12…` |
  | private | `8efd328f…` | `678df49c…` |
  | frozen | `10798b07…` | `4792ee74…` |

- **Fleet:** shim `aln35/aln41_r2_fleet.py` with lanes `c3_s35r2a41src`, `pb0` / `ptcs` / `ptnc` and `frz`. Each seed needs
  its own smoke receipt.

## Personal support (F_SUPPORT), CPU, frozen before any support result

- **Code and plan:** `auditory_alignment_v3/aln41/support.py`; plan `private/auditory_alignment_v3/aln41/support_v1/plan.json`
  (`3ed2b6f5…`).
- **Base:** every core-3 private CE unit across seeds 3401 / 3407 / 3413, taken at its selected checkpoint.
  - θ and the slot heads are frozen.
  - Adaptation uses only the stored per-trial slot log-probabilities and the checkpoint gate logits a_target.
  - The stored mixture must be reproduced to 1e-4.
- **Support contract:** `aln35.support_contract.private_split` / `select_support` on all of the test child's trials.
  - Pool: the earliest ceil(0.3 × blocks) blocks, after the boundary and epoch guards.
  - Query: the remaining blocks.
  - U10: n10 = min(floor(0.1 × available), pool size), drawn with seeds 351410–351414.
  - U30: the whole pool.
- **The two methods:**
  - **δ:** a_target + δ; support CE + 0.1/2‖δ‖²; 5 gradient steps at lr 0.1, re-centred after each step (as the package
    `adapt_delta_fo`).
  - **Calibration:** sigmoid(e^s·logit(p) + b); support CE + 0.1/2(s² + b²); 5 steps at lr 0.1.
  - Both gradients match finite differences to 1e-10.
  - Fallback: a support with fewer than 2 trials or only one class gets no update, and the reason is recorded.
- **Endpoints:** query NLL in bits/trial (primary); Brier and AUC (supplementary). The five U10 draws are averaged within each
  child first, then the seeds.
- **F_SUPPORT family (20 members):** children are the unit (n = 64).
  - Per arm (B0 / TCS / TNCE): δU10−U0, δU30−U0, calU10−U0, calU30−U0, δU10−calU10 and δU30−calU30.
  - Arm contrasts on the δU30 gain: TCS−B0 and TCS−TNCE.
  - Inference: bootstrap-t, B = 4000, family max-|T*|.
  - AUC is not used to claim δ beats calibration, because affine calibration does not change the ranking.

## Cross-stimulus question (F_CROSS_STIM)

The decision record is `R2_CROSS_STIM_DECISION.md`, written before any result.

- **Route:** deviance-relation transfer from MFF pure-tone to MFF bapa, followed by a refit on bapa.
- **Code and plan:** `auditory_alignment_v3/aln41/cross_stim.py`; plan `private/auditory_alignment_v3/aln41/cross_stim_v1/plan.json`
  (`4c26dfbe…`, which binds the decision sha `a9998544…`).
- **Units:** 7 frozen extractions: B0, plus TCS and TNCE at each of three seeds.
- **Fleet:** shim `aln35/aln41_xs_fleet.py`, lane `c3_s35a41xs`.

## Not used

- The optional ablation slot (shared between R2 and R3) is not invoked.
- The external slot belongs to R3.

## Infrastructure note

On 2026-10-21 one L40S GPU on node51 returned "uncorrectable ECC error" on every job it received. Eight failures were
released with receipts:

- `private/auditory_alignment_v3/aln35/fleet_v3_20261020/resolve_ecc_20261021_*.json`;
- `resolve_ecc_20261021b_*.json`.

node51 was added to `--exclude` in the active sbatch files.
