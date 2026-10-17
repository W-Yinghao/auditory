# 透明分析记录 · R34_TF_L1_PANEL — true-full FM vs same-access local L1, across seeds (2026-10-16)

Written 2026-10-16 19:50 CEST, **before** `auditory_alignment_v3/aln34/tf_l1_pairs.py` existed or computed any value.
Template: package `templates/ANALYSIS_NOTE.md`. Basis: package `AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016` docs/02 §A,
docs/06 "配对键", `configs/pairing_example.yaml`, card `R34_TF_L1_PANEL`; AGENTS.md ALN3.4 block items 4–5; intake
`INTAKE_20261016.md` action A02. Authorisation: the user's "按这个包执行"; no further go is needed (package docs/00).

## 问题与分析对象 · Question and estimand

1. **TF-LOCAL across seeds (new, exploratory).** Does the true-full foundation model (ALN32_TRUE_FULL, aligned interface,
   one-step recipe `full_onestep_v1`) have lower true-query risk than the same-access local encoder L1
   (ALN32_LOCAL_SUPPORT `local_aligned1000`), in each training seed that exists (3401 breadth; 3407, 3413 panel)?
   Members per dataset × backbone: init ∈ {random_full, pretrained_full} × backbone lr ∈ {1e-5, 3e-4}.
   - The warm-up recipe `warmup_then_all_v1` exists only for seed 3401. It is reported separately and labelled
     "warm-up, seed 3401 only". The panel registered one-step only (ADDENDUM_11 §1). Warm-up panel pairs are listed in
     the audit as missing (not registered); nothing is trained for them.
2. **TF-INIT, interim view only.** random_full → pretrained_full at the same backbone, recipe and numeric lr, per seed.
   The one-step panel version of this contrast is ADDENDUM_11's frozen role `initialization_true_full`. The frozen
   `auditory_alignment_v3/aln32_panel_interim.py` produces the official result when the panel completes; it is not
   replaced, edited or pre-empted here. Here: coverage, plus per-seed effects labelled **interim**. No seed mean and no
   between-seed summary for TF-INIT.

Estimand: ΔR = R(reference) − R(candidate), with R = `unified/regular/logloss_bits` (bits per 5 s test query, retrieval
cross-entropy over the test candidate pool, temperature calibrated on training-side early-stopping queries). Positive =
candidate lower true-query risk. Same sign convention as ADDENDUM_05/07.

## 数据/结果版本 · Data and result versions

- Plan rows: `run.all_rows()` = package v3 `plans/units.jsonl` + `private/auditory_alignment_v3/plan_ext.jsonl`.
- Roles (NCE, d = 32, datasets fau / dtu / federici; 25 fold cells per seed: FAU 10, DTU 10, Federici 5):
  - **L0** A_LOCAL `lag_local_tokens` window `full`: 25 per seed × 3 seeds (3401 breadth; 3407/3413 ALN3.1 panel).
  - **L1** ALN32_LOCAL_SUPPORT `local_aligned1000`: 25 per seed × 3 seeds (3401 ADDENDUM_07; 3407/3413 ADDENDUM_11).
  - **TF** ALN32_TRUE_FULL: seed 3401, 2 backbones × 2 inits × 2 recipes × 2 lrs × 25 = 400 rows; seeds 3407/3413,
    one-step only, 2 × 2 × 2 × 25 × 2 seeds = 400 rows.
- Unit records: `private/auditory_alignment_v3/units/<experiment_id>.json`.
- Live state read at 19:44 (file existence and the `status` field only):
  - L0 75/75 and L1 75/75 complete; TF seed 3401 400/400 complete.
  - TF panel 70/400 complete (35 per seed). All of them are DTU subject folds 0–1, plus some subject-fold-2
    content-fold-0 cells. FAU and Federici panel units are all still queued.
  - No failure record. None of these rows is held or deferred.
- Code hashes: for every complete record of the three roles, the recorded `code_hash` equals `core.code_hash(family)`
  recomputed now (L0 `89df1dde3d7a49df`, L1 `1b6595fc9ac72f77`, TF `88aafcdbd2424299`).
- Entity manifest for Federici identities: `private/auditory_alignment_v3/reaggregate/entity_manifest.csv` (record →
  subject_uid; the phantom entity is excluded).

## 写说明时已见哪些结果 · What had been seen when this note was written

- **Seen:** every seed-3401 result in `docs/auditory_alignment_v3/ALIGNED_INTERFACE_RESULTS.md` (generated 2026-10-16
  08:13), including TF-INIT (§7), TF-RECIPE, TF-VS-LEGACY and TF-LOCAL (§10, L0 and L1 references). While preparing this
  note I re-read the FAU·CBraMod tables of §7 and §10 and the identity counts of the L1 levels (FAU 67, DTU 44,
  Federici 86).
- **Seen:** the brief's seed-3401 numbers quoted in package docs/01 (B01 L257–L285). That brief is what promoted
  CBraMod true-full, so this summary is data-informed.
- **Not read:** any test value of the panel units (TF, L1 or L0, seeds 3407/3413). Of the panel records and rows I
  read only plan-row metadata (spec, folds, seed, lineage), record existence and the `status`, `code_group`,
  `code_hash` and `target_contract` fields. I also read queue positions and claim-file names.
- The A_LOCAL 3407/3413 units were used earlier by SCI_R1 science analyses (time curves etc.). Their retrieval risk is
  not used by any contrast computed here; L0 enters only the pairing audit.

## 与旧分析相比改变了什么 · What changes relative to the earlier analyses

- ADDENDUM_07 TF-LOCAL was seed 3401 only, one 16-member family per dataset × backbone (L0 and L1 × init × recipe ×
  lr). ADDENDUM_11 has no TF-LOCAL role.
- **New here:**
  - per-seed L1 → TF one-step families with 4 members per dataset × backbone × seed;
  - a seed-mean family on identities that are complete in all three seeds;
  - the between-seed range;
  - a separate 3401-only warm-up family;
  - the native readout as its own families;
  - a strict identity-completeness rule for interim coverage;
  - an explicit pairing audit.
- Because the families differ, the 3401 simultaneous intervals here are not the frozen ones. The 3401 **point
  estimates** must reproduce `results/auditory_alignment_v3/aln32_wave1/aln32_wave1.json` (same identity rule and the
  same data). The script checks this and reports the largest absolute difference.
- ADDENDUM_11's frozen family for `initialization_true_full` is dataset × seed with 4 members (backbone × lr). The
  interim TF-INIT families here are dataset × backbone × seed with 2 members (lr), the ADDENDUM_07 TF-INIT scope, as
  the package card asks. They are labelled interim and do not replace the frozen role.

## 配对键、身份与内容汇总 · Pairing keys, identity and content aggregation

Pairs are formed per (dataset, subject_fold, content_fold, seed) fold cell. The match fields of package docs/06 and
`pairing_example.yaml` are checked on every complete pair. The records carry no `split_hash`, `target_hash` or
evaluation-version field: the ALN3 v3 result schema asked for them but the runners never wrote them. The closest
verifiable equivalents are therefore used, as follows.

| field | how it is obtained | check |
|---|---|---|
| dataset, subject_fold, content_fold, seed | record `row` and `bound_row` against the plan row (`content_fold` None → 0 as in `core.bind`) | all three agree for every unit |
| split hash → **split fingerprint** | sha256 of {dataset, subject_fold, content_fold, `n_train_participants`, `n_fit_segments`, `n_es_segments`, `eval.readout.n_test_candidates`, sorted (test record id, n_candidates, n_queries) of `unified/regular`}. Code: the split is `train_participants(subject_fold)` plus the `data.load_*(content_fold)` roles; it does not depend on the seed (`auditory_alignment_v2/train.py`, `run.load_cohort`) | identical for every complete record of a fold cell, across roles and seeds |
| target hash → **target fingerprint** | sha256 of {`spec.target`, record `target_contract`, `resolved_config.d`, `grid_samples`, `fs`, head `fixed_features` (local: `bound_row.spec.audio_head`; FM: fixed in `fit_aligned32`), `objective_calibration.sigma_v`, `ridge_v`}. The last two are deterministic training-side statistics of the target head on the seed's calibration rows. Code: projection seeded per cohort (`audio_targets.COHORT_SEED`); standardisation from `target_stats` with rng(seed + 5); calibration batch rng(seed + 99 / 98) in both trainers | identical between reference and candidate in a cell and seed; differs across seeds by design (seed-specific standardisation sample) |
| access contract → **normalised access** | (support, window [a, b) in native samples relative to the query, mask). L1: `resolved_config.support`, `windows_samples`, `resolved_config.mask`. TF: `resolved_config.input_support`, `window_s` × fs with `window_native_samples` = b − a, mask from `fm_aligned.aligned_windows` (zero before the segment start). L0: `windows_samples` [[0, post)] = `post600`. Channels: both model types read every cohort channel (code: `Backbone` uses `CHANNELS[dataset]`; the local encoder uses `coh.n_ch`) | L1 = TF required. For the audit-only L0 pairs, `access_contract` is the declared allowed difference ("access extension", docs/06) |
| evaluation version → **evaluator identity** | `ev2.evaluate_continuous` → `ev1.evaluate_continuous`: unified ridge bridge and native score, the same candidate pools, rng(seed + 1000). Representations: `core.evaluate_grid` (Reps, stride = grid) for L0/L1; `fm_aligned.evaluate_aligned` (AlignedReps on `arange(0, seg_len, grid)`) for TF. Version = sha256 of `auditory_alignment/evaluate.py` and `auditory_alignment_v2/evaluate.py` plus `grid_samples` | valid only when the record's `code_hash` equals `core.code_hash(family)` recomputed now (the hashed files, incl. both evaluate.py, are byte-identical to what produced it), and when each role has a single `code_hash` |

- **Declared differences** (the independent variable):
  - TF-INIT: `adaptation` (random vs pretrained initialisation; `init_state_loaded`).
  - TF-LOCAL: the model (local encoder vs FM, with its recipe and lr).
  - L0 pairs: access.
- `information_stratum` is a plan label (`local_only` vs `foundation_context`). It is listed but is not a match field;
  the realised EEG access is what is compared.
- **No upstream dependency.** All three roles have `logical_dependencies = []`; no unit loads another unit's weights.
  `base_plan_row` is registration lineage only (L1 3401 → the A_LOCAL row of the same cell; panel rows → their 3401
  row; TF 3401 → its B_ALIGNED twin).
- **Pair status:**
  - complete: both units complete and every match field equal, apart from the declared difference;
  - pending: the pair is registered, at least one unit has no record yet (queued or running), and nothing is failed or
    held;
  - missing: not registered (warm-up in the panel seeds), held or deferred, failed (`technical_failed` or `FAILED`
    marker), or a match-field mismatch. The reason is always given.
- **Identity aggregation.** As `bc_interim.load_continuous`: an identity's value for a configuration is the mean over
  all of its (unit, record) entries, across content folds and outer folds. Federici records map to `subject_uid`
  through the entity manifest; the phantom is excluded.
- **Interim rule.** An identity enters a contrast only if every fold cell it appears in is pair-complete. Partial-cell
  averaging is never used, and a missing pair is never filled with 0. The cells an identity appears in come from the
  seed-independent split map, built from complete records and checked for consistency.
- **Seed mean.** The identity value is the mean over the three seeds of the per-seed identity values. It uses only
  identities complete in all three seeds; the count is reported. Seeds, folds and units never add n.

## 主要量、辅助量、不确定性处理 · Quantities and uncertainty

- **Primary:** ΔR on `unified/regular/logloss_bits`.
- **Separate readout:** ΔR on `native/regular/logloss_bits`, with the same sign and its own families. It is never pooled
  with the unified readout.
- **Inference:** `sci_r1.stats` through `bc_interim.run_family`.
  - Identity-level bootstrap-t, B = 4,000, with deterministic replicate indices per family label.
  - Pointwise 95 % intervals, and simultaneous 95 % intervals by max-t within a declared family (members evaluated on
    the family's common identity set, as inherited). Each member's own complete-identity count is reported as well.
  - No p-values.
  - The intervals are conditional on the fitted models: they do not include training randomness, and three seeds do
    not estimate a seed distribution.
- **Declared families** (each per readout):

| family | scope | members |
|---|---|---|
| TF-LOCAL one-step, per seed | dataset × backbone × seed (3401, 3407, 3413) | L1 → TF {random, pretrained} × lr {1e-5, 3e-4} (4) |
| TF-LOCAL one-step, seed mean | dataset × backbone | the same 4, on identities complete in all three seeds |
| TF-LOCAL warm-up (seed 3401 only) | dataset × backbone × 3401 | L1 → TF warm-up {random, pretrained} × lr (4) |
| TF-INIT one-step, per seed (**interim**) | dataset × backbone × seed | random → pretrained at lr {1e-5, 3e-4} (2) |
| TF-INIT warm-up (seed 3401 only) | dataset × backbone × 3401 | random → pretrained at lr (2) |

- **Between-seed range** (TF-LOCAL one-step): for each member, the per-seed mean paired difference on the seed-mean
  identity set, with its minimum, maximum and SD across seeds. It is descriptive only.
- **Reporting:**
  - Favourable and unfavourable members are reported the same way, with effect, intervals, n and coverage.
  - No member is selected by performance.
  - The 2 backbones × 2 inits × 2 lrs × 3 datasets cells are not counted as independent replications. They share
    identities, the L1 reference and seeds within a dataset.
  - Nothing is generalised beyond the seeds, lrs, recipes and budgets present (100 / 50 epochs).

## 探索性/原计划/勘误 · Status of each analysis

- **TF-LOCAL vs L1 across seeds** is a new **exploratory** paired summary. TF-LOCAL is not in ADDENDUM_11, and its
  seed-3401 values were seen.
- **TF-INIT per seed** is an **interim** look at a frozen planned role. The official version is
  `aln32_panel_interim.py` (ADDENDUM_11 §3) after the panel completes.
- No correction is made. CORRECTION_01 still applies: B_ALIGNED / B_DENSE `pretrained_full − random_full` is a recipe
  contrast and is not used here.

## 可复用产物与实际需要的新计算 · Reuse and new computation

- **Reused:**
  - the unit records above;
  - `bc_interim.run_family` / `member_values` / `diff` / `privacy_scan` / `write_json`;
  - `sci_r1.stats`;
  - `auditory_alignment.aggregate.unit_rows`;
  - the entity manifest;
  - `core.code_hash`.
  Frozen scripts are imported, never edited.
- **New:** CPU aggregation only, run locally with `nice -n 10` (< 4 GB RAM). No training, no GPU job, and no queue or
  hold change.
- **Missing pairs that need training:** none outside the registered panel. The missing TF panel units are registered
  and queued, and L0/L1 are complete. The warm-up panel is not registered and is not needed for this card (package
  docs/02 §A takes one-step 3e-4 as the starting point).
- **Reruns:** the script is idempotent and is rerun as the panel fills. Every output says "interim" and states its
  coverage until 400/400.

## 输出文件 · Output files

- Code: `auditory_alignment_v3/aln34/tf_l1_pairs.py`.
- Tests: `tests/auditory_alignment_v3/aln34/test_tf_l1_pairs.py` (synthetic records).
- Results: `results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json` (pairing audit, coverage, families, seed mean,
  range, native, reproduction check).
- Report: `docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md` (template `EXPERIMENT_UPDATE.md`, interim).
- All are new files, mode 600.

写完即执行已批准范围。

---

## 更正 1 · Correction 1 (2026-10-16 20:36 CEST, appended after an independent verification; the text above is unchanged)

Written after an independent verifier checked the 20:09 outputs, and **before** the corrected code was written or run.

**What had been seen when this correction was written:**

- Everything in the 20:09:37 outputs: `docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md` and
  `results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json`. That includes the panel values (seeds 3407/3413, the
  20 DTU identities of subject folds 0–1): TF-LOCAL per seed, the seed mean and the between-seed range, and TF-INIT per
  seed. They were produced by the code described above, and read by the builder at 20:09 and by the verifier.
- The verifier's own recomputations:
  - the seed-3401 pointwise CIs differ from `ALIGNED_INTERFACE_RESULTS.md` §7/§10 for 51 of 72 unified members, by up
    to 0.0038 bits;
  - FAU·CBraMod one-step lr 1e-5: [+0.080, +0.184] here vs [+0.078, +0.186] in §7;
  - critical values: 2.257 (frozen label, 2 members), 2.225 (this script's label, 2 members), 2.332 (frozen label, 4 members);
  - the same-identity DTU per-seed means, e.g. CBraMod L1 → pretrained lr 1e-5: 3401 +0.087, 3407 +0.132, 3413 +0.094.
- Record metadata read at 20:31–20:35 (counts only):
  - 474 complete TF records;
  - `backbone_contract.arch` and `.adaptation` equal the plan spec in every one;
  - `backbone_contract.init_state_loaded` is null in every one.

**Corrections:**

1. **Why the seed-3401 intervals differ from the frozen ones** (lines 72–74 above, and report §1.3/§1.4).
   - The statement that the intervals differ because the families differ is incomplete.
     - Bootstrap replicate indices are drawn with `sci_r1.stats.group_seed(label, metric)`.
     - The family labels here (`TFL1|<contrast>|<recipe>|<dataset>|<backbone>|<seed>`) differ from the frozen ones: `TF-INIT|<dataset>|<backbone>`, `TF-LOCAL|<dataset>|<backbone>`, and `<label>|sec` for the secondary readouts.
     - So even the pointwise intervals differ, by bootstrap Monte Carlo error.
     - The simultaneous intervals differ by Monte Carlo error and also by family composition.
     - Point estimates are unaffected.
   - **The declared labels stay as they are.** Changing a Monte Carlo seed after the intervals have been seen is not
     done.
   - **New check: interval reproduction.**
     - Recompute the frozen ADDENDUM_07 families from this script's seed-3401 identity values. Use the frozen labels and the frozen member names:
       - TF-INIT, 4 members (recipe × lr);
       - TF-LOCAL, 16 members ({L0, L1} × init × recipe × lr).
     - Process the readouts as `aln32_interim.aggregate` does: max-t on the unified readout; the native readout under `<label>|sec`, pointwise only.
     - Compare with `aln32_wave1.json`: est, se, pointwise CI, simultaneous bounds and crit.
     - Pass if every |Δ| < 1e-9 and every n is equal.
   - **The script also reports** the largest pointwise and simultaneous bound differences between the declared families
     and the frozen ones. These measure the Monte Carlo part (plus, for the simultaneous bounds, the composition part).
   - No estimate, family or interval in §1.2–§1.5 changes.
   - The verifier's frozen-label result (above) already suggests that the check will pass.
2. **`init_state_loaded` (line 95) is not evidence of the TF-INIT difference.**
   - The field is `backbone_contract.init_state_loaded`. It records only a donor `init_state` loaded into the backbone (`auditory_alignment_v2/foundation_adapter.py`, `Backbone.__init__`), and it is null in every TF record.
   - Public pretrained weights load through the adaptation flag:
     - CBraMod: strict `load_state_dict` of the published weights;
     - REVE: `AutoModel.from_pretrained` (random init: `from_config`).
   - The record evidence is `backbone_contract.adaptation` (random_full vs pretrained_full), together with
     `backbone_contract.arch`.
   - The code now stores these per unit and adds a pair check, `initialization`. For every TF side, the backbone_contract
     arch and adaptation must equal the configured ones, and no donor init_state may be loaded.
   - This is an audit check, not a selection rule. It was added after the values were seen, and its outcome (all pass) is
     already known from the metadata count above.
3. **"All are new files, mode 600" (line 183) was wrong** for `auditory_alignment_v3/aln34/tf_l1_pairs.py` and
   `tests/auditory_alignment_v3/aln34/test_tf_l1_pairs.py`, which were 644.
   - The results JSON, the report and this note were 600, and every parent directory was 700.
   - Both files were set to 600 at 20:36:09, immediately after this correction was written.
4. **Lines 75–77 misdescribe the TF-INIT family scope.**
   - The interim TF-INIT families are dataset × backbone × seed × recipe, with 2 members (lr).
   - That is not "the ADDENDUM_07 TF-INIT scope". ADDENDUM_07's TF-INIT family is dataset × backbone with 4 members,
     recipe × lr (`aln32_interim.families`).
   - Package card `R34_TF_L1_PANEL` specifies no family scope. It gives only the reference
     `same_lr_random_and_same_access_L1` and the candidates `cbramod/reve_pretrained_true_full`.
   - The scope here follows the task's "dataset × backbone family per seed". The recipe is split off in the same way as for the TF-LOCAL families, because warm-up exists only for 3401 and is reported separately (question item 1).
   - The family definitions are unchanged.
5. **TF-INIT in report §2.**
   - The §2 working-judgement table placed the TF-INIT one-step per-seed classes side by side across seeds. That goes
     against lines 20–21 ("no between-seed summary for TF-INIT"), even though no mean or range was formed.
   - From now on the §2 cross-seed table holds TF-LOCAL only.
   - TF-INIT stays in §1.4, §1.5 and Appendix A, with an `interim` tag on every TF-INIT one-step row.
6. **Builder hand-off summary (not the report).**
   - "The gap is an identity-subset effect, not a seed effect" overstated what §2 shows: on the same 20 DTU identities
     the seeds still differ.
   - Report §2 now adds, below the identity-subset table, the between-seed spread on those same identities. It is
     computed from the between-seed ranges already defined above and is descriptive only.
7. **Snapshot drift.** The 20:09 outputs are a snapshot, and unit `ALN3X_fa59d0d79a025f54` completed at 20:13.
   - The corrected script is rerun on the live state.
   - The outputs state the generation time to the second.

**Run record for Correction 1** (appended 2026-10-16 20:47, after the corrected run at 20:45:45; it adds nothing to the design above):

- **Declared checks.**
  - Frozen-label interval reproduction: **pass** (24 families, 240 member × readout values, largest |Δ| 0).
  - Point estimates: pass (144 values, max |Δ| 0).
  - `initialization` pair check: no mismatch among the 474 + 236 complete TF-LOCAL / TF-INIT pairs.
- **Interval differences of the declared families from the frozen ones**, seed 3401:
  - unified readout: pointwise bounds differ in 72 of 72 members at full precision (59 of them visibly at three decimals), by up to 0.0038 bits; simultaneous bounds by up to 0.0205 bits;
  - native readout: pointwise bounds differ by up to 0.0035 bits.
  - The verifier's count of 51 is not reproduced here. Its counting rule is unknown, and the maximum (0.0038) agrees.
- **Panel coverage at the run:** 74/400. The panel values equal those of the 20:09 run, because the DTU subject-fold-2 identities still lack cells.

## Edit 2026-10-16 21:21 (lead agent)

After the second independent verification, wording only: the generator header now names the declared family (dataset × backbone × seed × recipe); §3 no longer reads as a stability claim; the JSON `interim` flag is now true for every TF-INIT one-step family (an interim view of ADDENDUM_11's frozen role), not only for families with pending cells. Rerun at this time: panel 77/400, 0 mismatches, reproduction and frozen-label checks pass. No number changed.
