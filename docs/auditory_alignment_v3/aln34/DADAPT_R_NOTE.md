# 透明分析记录 — R34_DADAPT_R: true-query risk R of the completed D_ADAPT units (execution R34_DADAPT_R_v1)

Written 2026-10-16 23:58 – 2026-10-17 00:01 CEST (file mtime), **before any true-query or mismatched-query logloss of any D_ADAPT
unit was computed or read** (no such value exists on disk: the records do not store it). Template:
`AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/templates/ANALYSIS_NOTE.md` (sha256 `a632cffe9a14…`).
Basis: package docs/04 §A ("保留原D_ADAPT的gain主表，新增真实query风险作为明确的新分析"), docs/06 ("模型选择优先使用 … 真实开发任务风险 … gain作为正确配对敏感性另报"), AGENTS.md ALN3.4 items 2 and 5, the ALN3.2 line "正增量看同query真实风险",
`D_MULTI_SEED_RESULTS.md` §4 item 2. User instruction: "按这个包执行".

## 问题与分析对象 (question and object)

When personal supervised adaptation (none → `input_spatial`, none → `output_low_rank`) or more support (10 % → 30 %) changes the
recorded D_ADAPT query gain, what happens to the true-query risk itself?

- The recorded endpoint is `gain_bits = logloss(mismatched EEG) − logloss(true EEG)` on the fixed query (last 70 %). A larger
  gain can come from a lower true-query logloss R or from a higher mismatched-EEG logloss. R separates the two.
- **Object: the 200 completed lag-local D_ADAPT units** (`architecture = lag_local_tokens`, all `complete`):
  - seed 3401 (ADDENDUM_12): FAU, DTU × NCE, CS_SINGLE × none, input_spatial, output_low_rank × 5 subject folds × 2 content
    folds = 120;
  - panel seeds 3407 / 3413 (ADDENDUM_03 §1.1): FAU, DTU × NCE × none, input_spatial × 10 fold cells = 80.
- **Not covered:** the D_ADAPT policy arms `dense_fm_policy` / `complement_policy` (records: 114 + 109 complete, 17 not run and
  held). They run `run_adapt_policy.py` (code group `adapt_policy`) on FM bases chosen by the old training-only policy; their test
  values were never aggregated (ADDENDUM_12 §0) and ALN3.4 item 7 keeps them as old-policy executions. An R for them would need its
  own evaluator (that runner binds `_gain` by name at import). Not done here.

## 审计：原始运行器如何拟合适配器 (audit of `run_adapt3.py`, code group `adapt`)

Read today: `run_adapt3.py` (sha256 `0552c3796c0f…`), `run_complement.base_ready`, `core.py`, `run.py`, `local_train.GridBatcher`,
`auditory_alignment/evaluate.py` (`Reps`, `Readouts`, `_metrics`), `auditory_alignment/data.py` (loaders),
`auditory_alignment_v2/temporal.py` (encoder), `audio_targets.py` (head), `auditory_alignment/train.py` (`Objective`), and
`slurm/aln3_gpu_pool.sbatch` (how units ran).

1. **Base.** `run_complement.base_ready` over plan + `plan_ext` rows (`run.main` points `core.load_rows` at both): the A_LOCAL
   unit with the same dataset, subject fold, content fold, seed and objective, `lag_local_tokens`, window `full`; checkpoint
   `ckpt/<base>_best.pt` (`enc` + `head` state dicts, loaded strict, then frozen). The record names it in
   `dependency.base_same_fold` / `base_checkpoint`.
2. **Readouts, fitted once per unit with the frozen base** (ADDENDUM_04 §2): `Readouts` on 400 training-participant fit+es
   single-speaker segments drawn with `rng = default_rng(seed + 1000)`; per-readout temperatures calibrated on 300 training-side es
   segments (same `rng`) against the es pool. Unified = ridge bridge into the standardised target, reconstruction-correlation score;
   native = NCE dot product / CS_SINGLE ridge U→V with negative squared distance. The readouts are not refitted after adaptation.
3. **Grid:** `g = round(0.020 · fs)` = 3 samples at 128 Hz, 214 anchors per 5 s segment; EEG window [0, 600 ms).
4. **Support and query per test participant** (subject fold of the unit, ≥ 6 single-speaker test segments, recording order =
   sorted by `e0`): support = the first `max(1, round(f · n))` segments, f ∈ {0.1, 0.3}; query = the segments from `round(0.3 · n)`
   on, identical for both fractions and all adapters.
5. **Adapters:** none (no update); `input_spatial` (C × C matrix M, identity init, applied to every input window before the frozen
   encoder); `output_low_rank` (u + u Aᵀ Bᵀ, re-normalised; A 4 × d initialised `torch.randn(4, d) · 0.1`, B d × 4 zeros).
6. **Update:** Adam, lr 1e-3, adapter parameters only; full support batch each step (8 grid-phase anchors per support segment,
   phases from `default_rng(p)`, p = participant index); the unit's own objective (NCE: deduplicated InfoNCE, τ 0.1, stimulus keys
   `hash(uid)`; CS_SINGLE: the base's calibrated bandwidths).
7. **Step count:** chosen once per unit from {20, 50, 100} by the mean **native** gain over the first 8 (by index) training
   participants of the calibration sample, each split 30 % / 70 % on its own early-stopping segments; ties go to the first
   candidate; none uses 0 steps. The record stores `steps.chosen` and `steps.scores`.
8. **Query evaluation:** per fraction and readout, scores of the (adapted) query EEG against the full test candidate pool (unique
   test single-speaker stimulus segments, K candidates), temperature from step 2. `_metrics` on the true pairing and on the query EEG
   rolled by one segment (mismatched EEG). Stored per participant × fraction × readout: `gain_bits`, `rank_pct`, `top1` (true pairing),
   `n_query`; per fraction `n_support`. **Not stored:** the true-query logloss R, the mismatched logloss, top5, MRR, K, τ. The
   adapters were not saved.
9. **Randomness and determinism:**
   - every numpy generator is seeded (readouts `seed + 1000`, support phases `p`, target statistics `seed + 5`);
   - the encoder has no dropout or batch norm (Conv1d, LayerNorm, GELU, Linear), so `train()` during adaptation changes nothing;
   - `input_spatial` starts at the identity and none has no update, so both are deterministic up to floating-point order (TF32
     cuDNN convolutions on the A40, atomic adds in backward);
   - **`output_low_rank` is not reproducible:** its A is drawn from torch's default CPU generator, which no code in the original
     process seeds. In this environment (`torch 2.6.0+cu124`) that generator is seeded non-deterministically per process: today
     `torch.initial_seed()` and `torch.randn` differed in each of five fresh processes. No seed was recorded, so the recorded
     output_low_rank fits (and their step choices) cannot be re-created;
   - all 200 records ran on `NVIDIA A40`, one fresh process per unit, with `PYTHONHASHSEED=0` (pool script).
10. **EEG access at the support/query boundary (legacy property, unchanged here):** support anchors read EEG up to 0.6 s past a
    support segment's end. At 30 % support the last support segment is adjacent to the first query segment, so up to 0.6 s of that
    query segment's EEG can enter the update (paired with support audio); at 10 % a 20 % gap separates them. This re-evaluation
    reproduces the recorded fits and does not change it; the new adaptation work (E34_ADAPT_READY) must respect the boundary.
11. **Saved assets:** 80 distinct bases (NCE 20 per seed × 3 seeds = the 60 panel bases, plus 20 CS_SINGLE bases at 3401), all
    present (per-file symlinks into `/projects/…/auditory_alignment_v3/ckpt`, 137 KB each) with complete base records.
    `core.code_hash("D_ADAPT")` recomputed today = `f029aabd1ea656c1`, the value in every one of the 200 records.

**Conclusion of the audit.** Re-fitting on the saved base with the imported runner reproduces none and input_spatial, so for them
the reproduced `gain_bits` is the QC (tier "exact"). output_low_rank can only be refitted with a declared seed (tier
"seeded_refit"); its gain will differ from the record by the initialisation draw, and that difference is reported, not hidden.

## 数据/结果版本 (data and result versions)

- Plan rows: `AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010/plans/units.jsonl` (sha256 `0aefb27a83b0…`) for 3401,
  `private/auditory_alignment_v3/plan_ext.jsonl` (`85b44d8d7a65…`) for 3407 / 3413.
- Records: `private/auditory_alignment_v3/units/<eid>.json`, 200 complete, code hash `f029aabd1ea656c1`, target contract
  `dense20ms_v1`, device NVIDIA A40. They are read, never modified.
- Imported, unchanged (sha256 prefix): `run_adapt3.py` 0552c3796c0f, `run_complement.py` d72bb402b16e, `core.py` a3851b4a601a,
  `local_train.py` dee8d0cd5829, `run.py` 7c84b692ab3d, `auditory_alignment/evaluate.py` 2393bb5cff5b, `auditory_alignment/data.py`
  abeb9d368116, `auditory_alignment_v2/run.py` cbfc22a38c50; aggregation `d_lag_interim.py` 0c192214b760, `bc_interim.py`
  2840df81b608, `sci_r1/stats.py` 8bb141cf6070.
- **New execution version `R34_DADAPT_R_v1`.** Per unit: execution id `R34DR1_` + sha256(`<eid>|R34_DADAPT_R_v1`)[:16]; output
  `results/auditory_alignment_v3/aln34/dadapt_r/units/<eid>.json`. No original record, checkpoint or hash is touched.

## 写说明时已见哪些结果 (what had been seen when this note was written)

1. **All D_ADAPT gain results.** Seed 3401: `D_ADAPT_RESULTS.md` (all 24 AD-GAIN / AD-SUPPORT members incl. CS_SINGLE and
   output_low_rank, unified gain, Δrank, Δtop1, native gain, per group). Panel: `D_MULTI_SEED_RESULTS.md` v2 (per seed, identity mean,
   spreads, secondary readouts, groups, support/query sizes, step choices). Both read by this agent today.
2. **The brief (B01), incl. risk levels of other evaluations:** all configurations' true risk near log2 K (FAU 6.69, DTU 7.72,
   Federici 8.17 bits), best small encoder 6.30 (FAU) / 6.89 (DTU). These are full-test-set R values of the B/C evaluations, not the
   D_ADAPT query R, but they make the level of the none arm roughly foreseeable.
3. **Record census for this audit (no test logloss):** status, device, wall seconds (25–502 s per unit), GPU memory (1.8–2.2 GB),
   base ids and checkpoint presence, participants per unit (FAU 11 or 14, DTU 8 or 10), `steps.chosen` and `steps.scores`
   (training-side; the smallest best-vs-second margin is 0.00011 bits, `ALN3_1f9c9632db9e9412`, DTU CS_SINGLE output_low_rank).
4. **Code reading and two environment facts:** the torch generator behaviour (audit 9) and the EEG array sizes from HDF5 shapes
   only (FAU 3.43 GB, DTU 3.53 GB as float32 with both kinds; single-speaker part 1.42 / 1.16 GB).
- No true-query logloss, mismatched logloss or any value derived from them had been computed or seen for any D_ADAPT unit.
- So this is not a blind analysis of the adaptation question: the gains are known. R is new information.

## 与旧分析相比改变了什么 (what changes relative to the old analysis)

- **Unchanged:** the gain main tables (ADDENDUM_12 for 3401, D_MULTI_SEED v2 for the panel) stay the primary gain results. Signs
  (positive = candidate better), identity aggregation, bootstrap-t (B = 4,000), max-t within families are imported, not
  re-implemented (`bc_interim.run_family` / `member_values`, `d_lag_interim.ad_families` / `run_fams`, `sci_r1.stats`).
- **New endpoint:** R (true-query logloss) with its own family results; gain is not replaced.
- **New execution:** the adapters are refitted. Tier exact (none, input_spatial): the refit is the recorded fit up to float order,
  checked unit by unit. Tier seeded_refit (output_low_rank): a new deterministic fit.
- The readout is unchanged: R measures the base-model readout applied to the adapted representation.

## 配对键、身份与内容汇总 (pairing keys, identity and content aggregation)

- **none → adapter (within seed):** the same base unit (`dependency.base_same_fold`), dataset, subject fold, content fold, seed,
  objective, participants, query segments (equal `n_query`), readout seed. Each unit refits the readouts in its own process from the
  same base and seed, so they coincide up to float order.
- **10 % → 30 %:** within one unit; same adapter, same query.
- **Identity** = FAU / DTU test participant id. Per seed and configuration the identity's value is the mean over its units (its two
  content folds), as `d_lag_interim.collect`. Per seed: Δ(i, s). Panel identity mean: Δ̄(i) = mean over the seeds in which the pair
  exists; a reference of one seed is never paired with a candidate of another. n = identities (FAU 67 = TH 14 / HA 29 / CI 24; DTU
  44 = NH 22 / HI 22). Seeds, folds and content folds never add n. Complete-case sensitivity if an identity lacks a seed.
- **Which units enter:** exact tier only when the unit passes its reproduction QC (below); seeded_refit when its structural QC
  passes. Failing or missing units are listed; their pairs are missing, never filled with 0. Coverage (units per identity) is shown.

## 主要量、辅助量、不确定性处理 (primary and secondary quantities, uncertainty)

### Endpoints

- **Primary: R = unified logloss_bits** of the true pairing against the full test candidate pool (the "regular" pool) on the fixed
  last-70 % query, bits per query, lower = better. Contrast Δ = R(reference) − R(candidate): positive = lower risk with the
  candidate (the bc_interim `lower` direction).
- **Secondary, each in its own column, pointwise only:**
  - native R (`native` logloss_bits), Δ = reference − candidate;
  - unified mismatched-EEG logloss R_mm, Δ = candidate − reference (raw);
  - refit gain (unified and native), Δ = candidate − reference, shown next to the recorded gain contrast;
  - levels: R per configuration with K and log2 K (descriptive).
- **Decomposition (exact per identity):** Δgain = ΔR (ref − cand) + ΔR_mm (cand − ref). It tells whether a gain change is a
  true-risk change or a mismatched-risk change.
- Native is never averaged with unified; rank and top1 are not merged into R.

### Families (simultaneous 95 % by max-t within each family)

| Family | Seeds | Families × members |
|---|---|---|
| AD-GAIN \| ds \| obj \| support: none → input_spatial, none → output_low_rank | 3401 | 8 × 2 |
| AD-SUPPORT \| ds \| obj: 0.1 → 0.3 for input_spatial, output_low_rank | 3401 | 4 × 2 |
| panel AD-GAIN \| ds \| NCE \| support: none → input_spatial | 3401, 3407, 3413, identity mean | 4 × 1 each |
| panel AD-SUPPORT \| ds \| NCE: input_spatial | 3401, 3407, 3413, identity mean | 2 × 1 each |

- ds ∈ {fau, dtu}, obj ∈ {NCE, CS_SINGLE}, support ∈ {0.1, 0.3}. The 3401 families are the ADDENDUM_12 families; the panel families
  are the D_MULTI_SEED panel restriction (same labels, so the replicate indices are shared across seeds and with the 3401 family of
  the same label; the critical values differ with the member set).
- Metric keys are new (`R_bits`, …), so the draws differ from the gain draws (`sci_r1.stats.group_seed(label, metric)`).
- none 0.1 → 0.3 is zero by construction (QC, not a family).
- Per group (FAU TH / HA / CI, DTU NH / HI): descriptive, pointwise; n < 5 shows n only. Not a group contrast.
- Between-seed range and spread for the panel members; descriptive.

### Uncertainty

- Intervals condition on the fitted models; three seeds sample training randomness coarsely.
- output_low_rank adds the adapter-initialisation draw; its size is shown by the refit − record gain differences.
- No p-values. "I>0 / I<0 / contains 0" describes an interval. All members are reported whatever their direction.

## 复现QC (reproduction QC; declared before any refit, engineering tolerance, not a performance gate)

- **Structural, every tier, exact:** same participant set, groups and `n_segments`; equal `n_support` per fraction and `n_query` per
  fraction × readout; base id and checkpoint path equal to the record's `dependency`; `core.code_hash("D_ADAPT")` equal to the
  record's; none: R and gain identical across fractions (|Δ| ≤ 1e-12).
- **Tier exact (none, input_spatial):** `steps.chosen` equal to the record; max |Δ gain_bits| ≤ 1e-3 bits over every participant ×
  fraction × readout; max |Δ rank_pct| ≤ 1e-3; `steps.scores` max |Δ| reported; top1 deviations reported as query flips (a near-tie
  flip moves top1 by 1 / n_query), not bounded. A unit that fails is listed with its deviations and is not used in the R tables until
  the cause is understood.
- **Tier seeded_refit (output_low_rank):** structural checks only. Reported: per participant Δgain (refit − record), its
  distribution, and whether `steps.chosen` agrees. Its R and gain contrasts use the refit's own values.

## 执行 (execution)

- One fresh Python process per unit (as the pool ran them); `PYTHONHASHSEED=0` is required (stimulus keys use `hash`).
- Before the runner is called: `torch.manual_seed(int(sha256("<eid>|R34_DADAPT_R_v1|torch")[:8], 16))` (recorded per unit). This
  makes output_low_rank deterministic and changes nothing for none / input_spatial.
- `run_adapt3.bundle` is imported and called unchanged. Only `run_adapt3._gain` is replaced, in that process and for that call, by a
  function that returns the same four fields computed the same way plus `logloss_bits` (true pairing = R), `mismatched_logloss_bits`,
  `top5`, `mrr`, `n_candidates` and `tau`. The test-phase and step-selection code paths are otherwise the original ones.
- GPU execution: the original loader (`auditory_alignment_v2.run.load_cohort`), A40 (the device of all 200 records), runfill, no
  `--time`, requeue, atomic claims, idempotent, one output per unit (0600). Not submitted by this lane.
- **CPU engineering test (after this note, not part of the analysis):** the full-cohort loader needs about twice the 3.4 GB float32
  EEG array, above the session's 3 GB limit. The CPU test therefore uses an `ss_only` loader: the same participants, trials,
  per-participant standardisation over all trials (as the original), but only single-speaker trials are kept, stored as float16 with
  torch's conversion (the batcher stores EEG as float16 anyway). D_ADAPT reads single-speaker segments only. It is checked against the
  original loaders on synthetic HDF5 files in the tests. Units, all DTU (smallest single-speaker array), different fold cells so that no
  contrast is formed:
  - `ALN3_61e2dc7f6e88f7f0` (NCE none, subject fold 2 / content fold 1, 8 test participants: the smallest unit);
  - `ALN3_2f7f40f01150b17c` (NCE input_spatial, 4 / 1, 50 steps) if time allows;
  - `ALN3_7169a47e0c3689d7` (CS_SINGLE output_low_rank, 4 / 0, 20 steps) if time allows.
  Outputs `private/auditory_alignment_v3/aln34/dadapt_r/cpu_test/` (0600). CPU FP32 differs from the A40's TF32 convolutions, so these
  deviations are reported as an engineering check; the GPU run recomputes the same units.

## 探索性/原计划/勘误的身份 (exploratory, planned or erratum)

- Exploratory new analysis under ALN3.4 (docs/04 §A); not an erratum and not a frozen-rule result. The gain results were seen.

## 可复用产物与实际需要的新计算 (reuse and new computation)

- Reused: the 200 records, the 80 base checkpoints and base records, the frozen runner and readout code.
- New: a GPU re-fit of the 200 units (adaptation, readouts and query evaluation; no base training). The records' own wall times
  sum to 10,682 s on shared A40s (up to 8 units per card); the estimate is given with the unit list.

## 输出文件 (outputs)

- Code: `auditory_alignment_v3/aln34/dadapt_r.py` (new). Tests: `tests/auditory_alignment_v3/aln34/test_dadapt_r.py`.
- Per unit: `results/auditory_alignment_v3/aln34/dadapt_r/units/<eid>.json` (0600; per-participant values of the public FAU / DTU
  participants, as in the unit records).
- Aggregate (`--aggregate`, when outputs exist): `results/auditory_alignment_v3/aln34/dadapt_r/dadapt_r.json`,
  `docs/auditory_alignment_v3/D_ADAPT_TRUE_RISK_RESULTS.md`, private per-identity values
  `private/auditory_alignment_v3/aln34/dadapt_r/per_identity.json` (all 0600).
- Unit list `private/auditory_alignment_v3/aln34/dadapt_r_units.txt`; Slurm template
  `private/auditory_alignment_v3/aln34/dadapt_r_gpu.sbatch`; logs `private/auditory_alignment_v3/aln34/dadapt_r/logs/`.

写完即执行已批准范围；不用为普通措辞或正文位置再请求许可。

## 补充一 (addendum 1) — engineering record, written 2026-10-17 00:51 CEST (file mtime) after the checks below

Appended, not rewritten: everything above is the note as it stood at 00:00:23 CEST (sha256 `9a84c52e96f0…`), before the first run.
Nothing below changes a declared rule.

### What was run

1. **Synthetic tests:** `tests/auditory_alignment_v3/aln34/test_dadapt_r.py`, 25 / 25 pass (8 s). They cover:
   - the R capture: the four recorded fields bit for bit equal to `run_adapt3._gain`, the extra fields from the same two `_metrics`
     calls, the global lookup of `_gain` by the runner's nested `evaluate_query`, restoration after errors;
   - the `ss_only` loaders against the original FAU and DTU loaders on synthetic HDF5 files: identical single-speaker segment lists,
     float16 EEG windows and stimulus windows, recording order kept, standardisation over all trials;
   - ids and seeds, the scope (200 rows read from the live plan files, no record), the QC rules, the worker loop (idempotence, claims,
     failure records, retries, shards, own-claim sweep), the aggregation (signs, decomposition, seed mean equal to d_multiseed's
     helper, QC admission, missing pairs, panel families equal to d_multiseed's) and the document splice.
2. **CPU end-to-end runs** inside the session allocation (Slurm 1039458, `nodecpu10`), nice 10, 2 torch threads, `--loader ss_only`,
   RSS watchdog 2,900 MiB, one at a time. Evaluator-function sha256 `65d2d06219630ef1…` in all three outputs (the module file changed
   between runs only outside those functions).

| unit | configuration (subject / content fold) | tier | steps record → refit | max \|Δgain\| unified / native (bits) | max \|Δrank_pct\| | top1 flips | wall | peak RSS |
|---|---|---|---|---|---|---|---|---|
| `ALN3_61e2dc7f6e88f7f0` | DTU NCE none (2 / 1), 8 participants | exact | 0 → 0 | 1.4e-7 / 4.9e-7 | 7.8e-5 (native, 2 of 16 cells) | 0 | 178 s | 2,629 MiB |
| `ALN3_2f7f40f01150b17c` | DTU NCE input_spatial (4 / 1), 8 | exact | 50 → 50 (scores max \|Δ\| 1.5e-4) | 1.1e-4 / 2.0e-4 | 1.8e-4 | 0 | 260 s | 2,624 MiB |
| `ALN3_7169a47e0c3689d7` | DTU CS_SINGLE output_low_rank (4 / 0), 8 | seeded_refit | 20 → 20 (scores max \|Δ\| 0.031) | 5.6e-3 / 6.0e-3 | 1.1e-3 | 2 (unified) | 212 s | 2,611 MiB |

   - All three: structural QC pass (participants, groups, `n_segments`, `n_support`, `n_query`, base id and checkpoint path, code hash
     `f029aabd1ea656c1`); unit 1: refit values identical across support fractions.
   - Unit 3 (seeded refit): per participant × fraction × readout, mean \|Δgain\| 2.2e-3 (unified) / 1.7e-3 (native), signed means
     −1.2e-4 / +9.4e-5, 8 positive and 8 negative cells in each readout.
   - **Result of the QC question of the task:** re-fitting deterministically on the saved base reproduces the recorded `gain_bits` of
     none and input_spatial, here within 2e-4 bits even across devices (CPU FP32 against the records' A40 TF32); the declared tolerance
     1e-3 holds with a margin of five. The output_low_rank record cannot be reproduced (audit 9); a new draw moves its per-participant
     gain by about 0.002 bits on average and its step-selection scores by up to 0.031 bits (here without changing the choice).
   - This is a scale to keep in mind, not a result: the recorded CS_SINGLE output_low_rank AD-GAIN contrasts are +0.001 to +0.006 bits
     (`D_ADAPT_RESULTS.md`), the same order as one participant-cell's draw variation. The refit-versus-record columns of the aggregate
     will show how much of each output_low_rank contrast survives another draw.
3. **Worker subprocess path:** `run_child` on unit 1 (output present): the child interpreter started in 2.2 s, skipped, log 0600.
4. **Aggregation smoke test:** `--aggregate --update-doc` with `DR_RES` / `DR_PRIV` / `DR_DOCS` in the session scratchpad, on a copy of
   unit 1's output only, so that no contrast could be formed. It completed: coverage 1 / 200, 1,998 missing pairs listed, privacy scan
   PASS. The scratch outputs are not project outputs.
5. **Unit list and template** (00:50): 200 units (exact 160, seeded_refit 40), estimate in their headers; nothing submitted.

### What was seen (new information)

- Unit 1 only: unit means over its 8 participants of unified R 6.650 bits (range 5.849–7.642; K = 214, log2 K = 7.741), native R
  5.485, mismatched-EEG logloss 9.055 (unified) and 9.808 (native); in the smoke-test document the same as identity levels with
  pointwise intervals (unified 6.650 [6.068, 7.231]).
- Units 2 and 3: only the QC deviations against the records, the step choices and scores, finiteness of the R fields, K (214, 209),
  timing and memory. Their R and R_mm values were not printed or viewed.
- No R contrast (none → adapter or 10 % → 30 %) has been computed or seen for any identity.

### Precisions to the note

1. Audit 10 (support EEG past the segment end): support anchors are at grid phase 0–75 samples plus k · 78 (k = 0…7), so the last one is
   ≤ 621 samples into the 640-sample segment and its window [t, t + 77) ends ≤ 58 samples (0.45 s) past the segment. "Up to 0.6 s" in
   the note is a bound; 0.45 s is the exact one.
2. CPU memory with the `ss_only` loader was 2.61–2.63 GB for DTU, close to the 3 GB budget. A FAU unit (0.71 GB float16 bank instead of
   0.58 GB) was not attempted on CPU. The GPU run uses the original loader (about 3.4 GB float32 EEG per cohort, roughly twice that at
   the peak of loading), hence `--mem=32G` for two concurrent units.
3. Engineering edits after run 1, none in the value-producing functions: the evaluator hash is computed at import; the aggregation got
   a units-per-identity coverage column; template wording.

### GPU plan (not submitted)

- `sbatch private/auditory_alignment_v3/aln34/dadapt_r_gpu.sbatch` from the repo root: runfill, gpu:1, A40, no `--time`, requeue,
  array 0–3, two worker loops per card.
- Estimate (assumption, from the records' own wall times, 10,683 s summed over the 200 units on shared A40s): 228 unit-minutes (range
  176–367) ⇒ about 114 GPU-minutes at two units per card (88–184), 228 at one (176–367); about 30 min wall with four cards.
- It competes with the running pool for the 10-GPU cap.
- After it: `python -m auditory_alignment_v3.aln34.dadapt_r --aggregate --update-doc`, then the hand-written sections of
  `D_ADAPT_TRUE_RISK_RESULTS.md`.

## 补充二 (addendum 2) — corrections after an independent verification; part A written 2026-10-17 01:19 CEST, before the code was changed

Appended; everything above is unchanged (whole file sha256 `8078d75c259d…` at 01:18 CEST; the body before addendum 1 still hashes to
`9a84c52e96f0…`, the pre-run value stored in the CPU outputs).

**Why.** An independent verifier re-read the module, the tests, the unit list and the template, re-ran the tests and checked the three
CPU outputs with its own script, which does not import this module. It confirmed:
- the replication of `run_adapt3`: the same four fields bit for bit, the same support, query, step-choice and seed paths;
- R on the fixed query, with no test-side selection;
- code hash `f029aabd1ea656c1` in all 200 records;
- the completeness of the unit list and the CPU figures of addendum 1.

It found the problems corrected below.

**What had been seen when part A was written:** the same as at the end of addendum 1 (unit 1's R levels; for units 2 and 3 only the QC
deviations). No R contrast of any identity (none → adapter, 10 % → 30 %) has been computed or seen. No GPU unit has run (no such job in
squeue or sacct). No file exists under `results/auditory_alignment_v3/aln34/dadapt_r/`. Every correction below is therefore made before
any value it affects exists.

### C1. none → adapter is paired at content-fold level (rule correction; the earlier note and code disagreed)

- **Problem.** The note ("配对键") averages an identity's value per seed and configuration over its units (its two content folds), and
  says that failing units "are listed; their pairs are missing, never filled". The code instead took each configuration's identity mean
  over whichever of its own units were admitted, separately per configuration, and then paired identities.
  - If one content-fold unit of a none / adapter pair is not admitted (a QC failure, no output, three failed tries, an interim
    aggregate), the reference mean covers both content folds and the candidate mean only one, or the reverse. ΔR then mixes different
    query sets, and nothing was listed as missing.
  - The verifier reproduced this with the module's own synthetic fixture. Only content fold 0 of FAU 3407 subject fold 0
    input_spatial failed. 4 identities got ΔR 0.115 instead of the per-unit 0.12, the member estimate was 0.1175, and 0 missing pairs
    were listed.
  - Affected: AD-GAIN per seed and the panel identity means. Not affected: AD-SUPPORT, which is within one unit.
- **New rule** (declared now, before any contrast is computed). For every family member (reference, candidate), seed and identity, both
  sides are averaged over the same content folds: those in which both the reference unit and the candidate unit of that identity are
  admitted. Equivalently, the content-fold-level paired difference (same base unit, same query segments) is averaged over those content
  folds. A pair is:
  - **complete:** the kept content folds are all the content folds in which both records hold the identity (normally 2);
  - **partial:** at least one content fold kept and at least one dropped. It enters the families with its kept content folds. It is
    listed (identity, seed, family, member, kept and dropped content folds, which side lacked them) and counted per member;
  - **missing:** no content fold kept. It is listed and never filled.
- Every metric of a pair uses the same kept content folds (R, R_mm, refit gain, recorded gain). The decomposition Δgain = ΔR + ΔR_mm
  and the refit-versus-record comparison therefore stay on one query set.
- Levels (R per configuration) remain the identity mean over that configuration's admitted units; they are descriptive.
- When every unit is admitted, the expected case, this rule gives exactly the earlier values.

### C2. Claim sweep with Slurm job arrays (operational)

- **Problem.**
  - The claim owner stores `SLURM_JOB_ID`, which is unique per array element. `live_jobs()` listed running jobs with `squeue -o %i`,
    which prints array elements as `<base>_<index>`.
  - With the template's `--array=0-3`, the sweep took every other element's claim for dead once it was older than 2 min. A unit in
    progress could then be claimed and run twice, and the first worker's release deleted the second worker's claim.
  - Values would stay valid (atomic writes), but GPU time would be wasted.
  - Confirmed here from `man squeue` (Slurm 24.11.7): `%A` is "Job id. This will have a unique value for each element of job arrays";
    `%i` prints `<base_job_id>_<index>`.
- **Fix.**
  - `live_jobs()` lists both forms (`squeue -o "%A %i"`).
  - The owner record also stores `<SLURM_ARRAY_JOB_ID>_<SLURM_ARRAY_TASK_ID>`. A claim counts as live when either form is running.
  - A worker releases a claim only when the owner record is its own (job, worker tag, host, pid). It never deletes another worker's
    claim.

### C3. Location of per-identity outputs (rule)

- **Problem.**
  - Per-unit outputs carry participant ids, groups and per-participant R, R_mm, gain, rank, top1, top5 and MRR. They were to be written
    to `results/auditory_alignment_v3/aln34/dadapt_r/units/`.
  - The aggregate results JSON could carry identity ids (`coverage.missing_pairs[].identity`) and QC problem strings that embed
    participant ids.
  - The task puts per-identity outputs under `private/auditory_alignment_v3/aln34/<track>/`. FAU and DTU are public, and
    individual-level publication is within the confirmed scope, so this was a location and consistency deviation, not a disclosure.
    Nothing had been written there.
- **Fix.**
  - Per-unit outputs, claims and failure records now go to `private/auditory_alignment_v3/aln34/dadapt_r/units/` (files 0600,
    directories 0700).
  - The results JSON and the results document carry no identity id:
    - missing and partial pairs are counted per seed × family × member;
    - QC problems are shown as problem kinds.
  - The identity lists, the full QC problem strings and the per-identity values go to
    `private/auditory_alignment_v3/aln34/dadapt_r/per_identity.json`.
  - The aggregation refuses to write the public files when its scan finds an identity id in them.
- This supersedes the per-unit output path given under "执行" and "输出文件" above.

### C4. Safety of `--out` (minor)

- **Problem.** Nothing stopped `--out` from being the records directory (`private/auditory_alignment_v3/units`). With `--force`, an
  original record `<eid>.json` could have been replaced.
  - No record was touched. The verifier found that all 200 unit records, the 80 base records and the checkpoints have mtime
    ≤ 2026-10-11 06:54, and that the sha256 of the 3 tested records equals the value stored at run time.
- **Fix.** Every write of the module refuses targets inside:
  - the records, checkpoint and governance directories;
  - the checkpoint offload tree and the read-only source tree;
  - the plan directory and the top level of `private/auditory_alignment_v3/`.
  `--out` is checked at start.

### C5. Provenance (minor)

- **Problem.** The evaluator hash (sha256 of the value-producing functions; `65d2d06219630ef1…` in the three CPU outputs) does not cover
  `torch_seed()`, which sets the output_low_rank initialisation, or the module constants (tiers, tolerances, version).
- **Fix.** The evaluator hash keeps its definition, so that it stays comparable with the three CPU outputs. A second hash,
  `value_path_sha256`, covers those functions, `torch_seed()`, `execution_id()` and the constants. It is recorded in every new output
  and in the aggregate.

### C6. Numbers

- The records' wall times sum to 10,683.5 s. The body ("可复用产物") says 10,682 s; addendum 1 and the unit-list header say 10,683 s
  (rounded). The estimate is unchanged.

### Not changed

- Endpoints, families, signs, statistics, QC rules, tolerances and tiers.
- The evaluator functions (the refit path), so the three CPU outputs remain valid engineering checks.

### Part B — engineering record, written 2026-10-17 01:36 CEST, after the checks below

Appended after part A; nothing above is changed. No declared rule changes here.

**Code.**
- `auditory_alignment_v3/aln34/dadapt_r.py` now implements C1–C5 as declared in part A (module sha256 `6c88d7334237…`).
- The evaluator hash is unchanged (`65d2d06219630ef1…`), so the refit path is the one checked in addendum 1; a test pins it.
- New value-path hash (C5): `33d63955dfc0d8f2…`.
- Tests: `tests/auditory_alignment_v3/aln34/test_dadapt_r.py`, 34 tests (25 before), all passing. New:
  - the partial-pair case on either side;
  - array-element claims in both squeue forms, the owner and `live_jobs` forms, and owner-checked release;
  - protected write targets, the value-path hash, identity-free public outputs, and QC problem kinds.
  Three existing tests were adapted to the new structures.

**What was run** (Slurm allocation 1039458, `nodecpu10`, nice 10):
1. **Tests.**
   - `test_dadapt_r.py`: 34 / 34 pass (16 s, peak RSS 545 MiB).
   - Together with `test_d_multiseed.py`: 46 / 46 pass (25–38 s, ≤ 543 MiB).
2. **Old versus corrected pairing on the synthetic fixture** (scratch script, synthetic data only).
   - Pre-fix path, with only content fold 0 of FAU 3407 subject fold 0 not admitted:
     - candidate side (input_spatial) failing: estimate 0.1175, per-identity ΔR 0.115 / 0.12;
     - reference side (none) failing: estimate 0.1225, per-identity ΔR 0.125 / 0.12.
   - Corrected path: 0.1200 in both cases, with 12 and 8 partial pairs listed.
   - The new test therefore separates the two behaviours.
3. **CPU end-to-end re-run** of `ALN3_61e2dc7f6e88f7f0`, the smallest unit and the same as addendum 1's unit 1, with the edited module
   (`--unit`, `--loader ss_only`, 2 threads, RSS watchdog 2,900 MiB):
   - QC pass (tier exact); steps 0 → 0; against the record, max |Δgain| 4.9e-7 and max |Δrank_pct| 7.8e-5; no problem;
   - 215 s, peak RSS 2,613 MiB;
   - the `eval` and `qc` blocks are bit-identical to addendum 1's output of the same unit (0 differing fields); same record,
     checkpoint and torch-seed values;
   - output `private/auditory_alignment_v3/aln34/dadapt_r/cpu_test_c2/` (0600); the claim was released.
   - Worker loop on the same directory: `skip_done` 1, no claim released. `live_jobs()` read the real squeue in both forms. No
     array element of this user is running, so the two forms coincide today; the array case rests on the tests and the documented
     formats.
4. **`--out` set to the records directory, with `--force`:** refused before anything was written.
5. **Unit list and template regenerated** (`--write-units`, 01:34).
   - The 200 unit rows are byte-identical (sha256 of the rows `42db2f497bee…`).
   - The header now names the private output directory and states the records' wall-time sum, 10,683.5 s.
   - The template now describes the claim and output-location corrections. `bash -n` passes. Nothing was submitted.
6. **Aggregation smoke test on the real records**, with the module's `DR_*` overrides pointing at
   `private/auditory_alignment_v3/aln34/dadapt_r/smoke_c2/` (all files 0600). Input: unit 1's output only.
   - Result: 1 / 200 units; 0 complete, 0 partial and 1,998 missing pairs (counts public, rows private); 32 pairs with unequal
     admitted content folds; identity scan PASS; privacy scan PASS.
   - An independent text search of the public JSON and the document for all 111 participant ids found no quoted id and no DTU id.
     The only bare id-like token is the integer 214, which is K (the number of candidates), not an identity.

**What was seen:** nothing new.
- Unit 1's values were reproduced and compared field by field, without being printed.
- The smoke document shows unit 1's levels again (seen in addendum 1).
- No R contrast of any identity has been computed or seen.
- The three outputs in `cpu_test/` remain valid engineering checks: same evaluator hash. They have no `value_path` field because they
  were written before C5.

**Precision to part A, C6.** Part A says the unit-list header gave 10,683 s. It did not state the sum at all, only the derived estimate;
only addendum 1 gave 10,683 s (rounded). The regenerated header states 10,683.5 s.

**Outside this lane.** The verifier noted that `auditory_alignment_v3/aln34/complement_function.py` also writes its per-unit outputs to
`results/`. That module belongs to another agent and is not edited here.

**GPU plan** (unchanged, not submitted).
- From the repo root: `sbatch private/auditory_alignment_v3/aln34/dadapt_r_gpu.sbatch`. Runfill, gpu:1, A40, no `--time`, requeue,
  array 0–3, two worker loops per card.
- Estimate, from the records' wall times (an assumption, not a measurement): 228 unit-minutes (range 176–367). That is about 114
  GPU-minutes at two units per card (88–184), or 228 at one, and about 29 min wall with four cards.
- It competes with the running pool for the 10-GPU cap.
- After it: `python -m auditory_alignment_v3.aln34.dadapt_r --aggregate --update-doc`, then the hand-written sections of
  `D_ADAPT_TRUE_RISK_RESULTS.md`.
