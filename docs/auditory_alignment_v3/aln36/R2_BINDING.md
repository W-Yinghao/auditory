# ALN3.6 R2 (package ALN3.7): fixed seed-3407 replication (2026-10-21)

Researcher instruction: "开始两个R2". The scope is package `docs/05` R2, fixed before R1. It covers every group whatever its
R1 sign, and nothing more.

- **Runner:** `auditory_alignment_v3/aln36/r2.py`. The R1 modules stay byte-identical, re-pointed for the process.
  - Changed: `common.SEED = 3407`, the FAU group parents, and the output / store roots
    (`private/auditory_alignment_v3/aln36/r2_s3407/`).
  - The package byte-check still runs under its own round-1 seed.
  - The R1 bindings are reused unchanged: source people, population scaler and risk anchor sets. Their risk-calibration draw
    used seed 3401, so only the training seed differs from R1.
- **FAU whole-group exclusion:** 12 unique fits giving 60 evaluation cells (plan `872e2a75…`).
  - Group parents: the seed-3407 pooled person-fold-0 units with the R1 parents' exact spec.
    - local_L1: `ALN3X_da6696d66809ebb3` (cf0) and `ALN3X_b4998069d1d024dd` (cf1).
    - CB true-full: `ALN3X_fa8605dc2a60565a` (cf0) and `ALN3X_792874d043389f51` (cf1).
  - Lanes: `c3_s35r2a36loc` and `c3_s35r2a36cb`.
- **Public feature banks:** 52 in total (plan `30d2aefa…`). No pooled model is retrained.
  - 40 existing seed-3407 pooled parents:
    - DTU: the 20 seed-3407 rows of content_time_v1.
    - FAU: those rows are not in that plan. Each R1 FAU pooled row is matched to the unique completed seed-3407 unit with the
      identical spec, person fold and content fold. All 20 matched uniquely, and their checkpoints are present.
  - 12 R2 group units.
  - Lane: `c3_s35r2a36feat`.
- **Children's matched AP / APwrong, seed 3407:** `auditory_alignment_v3/aln36/r2_apwrong.py`.
  - The R1 runner `aln35/ap_wrong.py` stays byte-identical. Only its two seeded constructors (encoder build and pair sampler,
    literal 3401) are swapped for seed 3407.
  - Lineage: the seed-3407 panel donor `ALN3X_89596ce9168aa591`. It matches the R1 core donor apart from seeds and block label:
    same manifest, same donor set.
  - Templates: the seed-3407 panel AP target rows. Scratch references: the panel S rows.
  - Work: 1 donor pair (2 trainings) plus 2 × 5 targets.
  - The full h30 metadata stream (78,874 steps per member) was audited on CPU. The GPU donor must reproduce its hash.
  - Nothing compatible already existed: the seed-3407 panel AP lineage used the original stream and horizon.
  - Lanes: `c3_s35r2a36apw`, then `c3_s35r2a36priv` for window features (that plan is made once the 10 targets exist).
  - Current plan: `21a4a67a…` (donor pair `ALN36R2W_60a365fd00c6e23f`).
  - The first plan (`371fd210…`) was superseded before any unit result. Its donor pair died on the faulty node51 GPU, and the
    sbatch file is hash-bound, so node51 could only be excluded by re-registering. It is kept in
    `private/auditory_alignment_v3/aln36/r2_s3407/apwrong_superseded_node51_20261021/`.
- **Readouts and analysis:** the R1 code under `r2.py`, run as `python -m auditory_alignment_v3.aln36.r2 public_readout --all-ready`,
  then `private_readout`, then `analysis`. Output goes to `results/auditory_alignment_v3/aln36/r2/`. All R1 definitions are
  unchanged: support rules, history, time bank, lambda and statistics families.
- **Fleet:** shim `aln35/aln36_r2_fleet.py`, registered after the ALN4.1 R2 shim, which keeps priority.
- **R3 (ALN3.8):** merges the two seeds per person and handles validity and writing. It has not started.
