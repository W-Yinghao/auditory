# Analysis note — R34_FUSION_FUNCTION: what SC and RS actually change (exploratory re-evaluation)

Written 2026-10-16 20:00 CEST, **before** any value covered by this note was computed. Basis: ALN3.4 package
`AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016` docs/03 §1–2, card `R34_FUSION_FUNCTION`, reference math
`src/aln34_reference/residuals.py`; AGENTS.md ALN3.4 block items 2, 8 and 11; user instruction "按这个包执行" (2026-10-16).
Template: package `templates/ANALYSIS_NOTE.md`. Code: `auditory_alignment_v3/aln34/complement_function.py`.

## 1. 问题与分析对象 — question and estimands

1. On identical test queries, candidate pools and readout / calibration contract, how do the following compare, per test
   identity: the original direct local base (L0 = A_LOCAL `lag_local_tokens` full; L1 = ALN32_LOCAL_SUPPORT
   `local_aligned1000`), SC `local_only`, the other five SC variants, RS at its selected epoch, and RS at epoch 0?
   Unified and native readouts are reported separately.
2. For RS: does the trained residual change the normalised representation, the sound prediction and the new-listener risk,
   and how do the development-side and outer-test changes relate? Four layers (package docs/03 §2):
   - L1: ‖r‖/‖u‖; r_parallel = (r·u)/(u·u)·u and the orthogonal part;
   - L2: pre-normalisation change ‖r‖, post-normalisation change ‖n(u+r) − n(u)‖, angle between n(u) and n(u+r);
   - L3: native score / sound-prediction differences, unified prediction differences, candidate-rank changes;
   - L4: development vs outer test; epoch 0 vs the selected epoch, including the selection risk difference.

These quantities separate interpretations. There is no pass line on residual magnitude, and a network residual norm is
not a neural amplitude. Query- or anchor-level counts are diagnostic sample sizes only; inference is over identities.

**Statements fixed before computing.**

- This is an exploratory re-evaluation. It is not a blind validation, and it does not replace the frozen ADDENDUM_09 /
  ADDENDUM_10 analyses or their wording rules.
- SC `local_only` is a **ridge-remapped base, not the base itself**: û = FixedFeatureHead(ridge(u_base → A)). It is the
  base pushed through a supervised ridge to the raw 8-frame target and then through the fixed audio head.
- The SC ridge is **supervised parameter fitting**. Only the encoders are frozen (base encoder and FM backbones). "No
  training" in older text means "no gradient training", nothing more.
- RS at epoch 0 is the base L0 exactly. The residual's last layer is zero-initialised, so r = 0 and u = n(u_base) = u_base
  (u_base is already L2-normalised). The saved field `epoch0_max_abs_diff_vs_base` records this per unit. Selecting a
  non-zero epoch does not by itself mean that a functional correction was adopted.
- D34 reference math applies: if r = α·u with α > −1, the L2-normalised representation is unchanged. Only the orthogonal
  part (and α ≤ −1) changes n(u+r).
- The isotropic-ridge rotation invariance in D34 holds for the evaluator's unified bridge (plain ridge with intercept). It
  does **not** hold exactly for the SC ridges, which standardise each feature and scale α by trace/p.

**Level of held-out development actually achieved (AGENTS item 8).**

- SC: ridge-only out-of-fold over 5 groups of training participants. The base encoder was trained on all of them.
- RS: residual-only cross-person selection on inner group 0. Group 0 were training participants of the frozen base.
- This re-evaluation performs no selection and fits nothing new. It re-scores fixed models on the outer test.

## 2. 数据/结果版本 — data and result versions

- Records under `private/auditory_alignment_v3/units/` as of the asset audit, 2026-10-16 19:58. All records are
  `target_contract` dense20ms_v1.
  - SC: 100/100 complete, seed 3401, NCE, code hash ff333915faeb6b48.
  - RS: 250/250 complete at seed 3401 (NCE and CS_SINGLE), code hash e28928ee603968c7.
  - Bases: L0 A_LOCAL 50/50 complete, code 89df1dde3d7a49df; L1 25/25 complete, code 1b6595fc9ac72f77.
  - The latest SC/RS seed-3401 record was written 2026-10-15 14:12.
- RS panel seeds 3407/3413 (ADDENDUM_11, NCE only) are still running: 75 and 74 of 250 complete at audit time. They are
  **not used** here. SC has no panel. The panel belongs to the ADDENDUM_11 analysis; L4 can add it when it completes.
- Context rows (already reported; levels only, no new contrasts):
  - B_ALIGNED `pretrained_frozen` (the frozen FM branch whose tokens SC and RS read);
  - ALN32_TRUE_FULL `pretrained_full` `full_onestep_v1` at both registered backbone LRs (1e-5, 3e-4).
  These are chosen by registration, not by test value.
- Evaluator contract shared by every compared record: `auditory_alignment_v2.evaluate.evaluate_continuous`.
  - Same test queries: all single-speaker test segments of the fold's test participants, on the dense grid (stride = 20 ms
    grid).
  - Same candidate pool: the unique test stimuli.
  - Readouts: the unified ridge bridge and the native score are fitted on 400 training-participant fit + early-stopping
    segments.
  - Temperature: calibrated on 300 training early-stopping queries against the early-stopping pool.
  - Sampling: rng = seed + 1000 for every model.
  - Pairing is checked per fold, participant, candidate count and query count.

## 3. 写说明时已见哪些结果 — what was already seen when writing

- In full: `COMPLEMENT_REVISED_RESULTS.md` and `COMPLEMENT_REVISED_RESIDUAL_RESULTS.md`, i.e. SC-VALUE / SC-ATTRIB and
  RS-VALUE / RS-ATTRIB with their intervals, levels and epoch-0 fractions.
  - DTU: SC variants lower risk relative to `local_only`.
  - RS-VALUE: FM residuals ≈ 0 everywhere. Small-capacity RS: DTU NCE +0.016; FAU CS −0.018; DTU CS −0.087.
- The researcher's brief (`sources/ALN3_BRIEF_20261016.md`) set cross-document levels side by side, without paired
  intervals:
  - `local_only` vs the base itself (L0 / L1): DTU 6.975 / 7.035 vs 6.869 / 6.905; FAU 6.344 / 6.358 vs 6.309 / 6.344;
    Federici 8.083 / 8.029 vs 8.056 / 7.984.
  - Every SC variant's level lies above (worse than) the corresponding base's level.
  - The direction of the new base → SC contrasts is therefore **already known descriptively**. What is new is the paired,
    same-contract version with simultaneous intervals and the native-readout counterpart.
- `ALIGNED_INTERFACE_RESULTS.md` §1 (levels of L0, L1, B_ALIGNED, TRUE_FULL; I re-read the FAU table today) and the
  B_ALIGNED results were reported earlier.
- Seen by me today while auditing (engineering inspection):
  - One SC record (FAU, fold 0 / content fold 0, cbramod, L0): partial per-participant values of its variants and its
    fit log.
  - One RS record (FAU, fold 0 / content fold 0, NCE, cbramod pretrained): first dev-curve epochs, selected epoch 20,
    readout temperatures.
  - Runtime and device fields of all RS records.
  - Selected-epoch class counts of the panel units (3407: 2 of 75 at epoch 0; 3413: 5 of 74). No panel test value.
- Not seen: any per-query quantity (none was ever saved), any L1/L2 value, any checkpoint weight norm, and any paired
  base → SC or native RS family interval.

## 4. 与旧分析相比改变了什么 — what changes relative to the old analyses

1. Reference. SC is compared with the **original direct base** (L0 / L1), not only with `local_only`. All six SC variants
   enter one max-t family per dataset × backbone × base, for each readout.
2. Native readout. It becomes a primary family of its own (max-t), next to the unified readout, for SC and RS. Before, it
   was a pointwise secondary column.
3. RS selected vs epoch 0, unified readout. It reuses the frozen labels `RS-VALUE|<ds>|<obj>`, so its replicate indices and
   intervals reproduce `COMPLEMENT_REVISED_RESIDUAL_RESULTS.md` §3 exactly. This is a regression check, not new
   information. The native family (`FN-RS-NATIVE|…`) is new.
4. New function layers (§1, L1–L4) and the contract checks:
   - epoch-0 units must reproduce their base record;
   - checkpoint: epoch-0 selection ⇔ zero last layer;
   - readout temperatures RS / base.
5. Calibration caveat, disclosed rather than corrected. SC ridges were fitted on fit **and** early-stopping rows of the
   training participants (`complement32.run`: `units = fit + es`). The evaluator's temperature is calibrated on those
   early-stopping segments, so SC's R is partly calibrated in-sample with respect to its own ridge. Base and RS used
   early-stopping rows only for selection. Rank metrics (rank_pct, top-1) do not depend on the temperature and are reported
   for both readouts.

## 5. 配对键、身份与内容汇总 — pairing keys, identity and content aggregation

- Pairing key: dataset, subject_fold, content_fold, seed 3401, objective, evaluator version and target contract.
  - SC vs base: also base ∈ {L0, L1}.
  - RS vs base: always L0 of the same objective.
  - Candidate and query counts must match per participant and fold (`pair_ok`); otherwise the pair is excluded and listed.
- Identity: FAU / DTU participant id. Federici: entity-manifest `subject_uid`, so HC and HC-v of one child are one
  identity. The phantom is excluded.
- Identity value: mean over that identity's units (content folds). Seeds and folds never add n.

## 6. 主要量、辅助量、不确定性处理 — primary and secondary quantities, uncertainty

- **Primary (per readout).** ΔR = R(reference) − R(candidate), with R = `{unified,native}/regular/logloss_bits`. Positive
  means the candidate has lower true-query risk.
  - Families:
    - `FN-DIRECT-SC|<ds>|<backbone>|<L0|L1>|<readout>`: 6 members, original base → each SC variant; 24 families;
    - `RS-VALUE|<ds>|<obj>` (unified) and `FN-RS-NATIVE|<ds>|<obj>`: 5 members, epoch 0 = L0 → RS selected; 12 families.
  - Inference: identity bootstrap-t, B = 4,000, family max-t with shared replicate indices (`sci_r1.stats`; the
    ADDENDUM_05 machinery). Classes: I>0 / I<0 / contains 0 on the simultaneous interval.
  - An interval that contains 0 is not a zero effect, and one side being better is not general superiority.
  - L0 gains are labelled context-assisted (the candidates read the aligned window); L1 is access-matched.
  - Every member is reported whatever its sign.
- **Secondary (pointwise, no max-t).** Δrank_pct, Δtop-1 and Δgain_bits per readout. Levels per configuration, with
  identity bootstrap intervals for R.
- **L4 (from saved records).** Unit-level descriptives:
  - Δdev = dev risk(epoch 0) − dev risk(selected) from the saved curve (≥ 0 by construction);
  - the outer-test change of the same unit (RS record vs its base record);
  - selected-epoch distribution, number of epochs below epoch 0, and Spearman Δdev ~ Δtest over units whose selected
    epoch is > 0;
  - readout temperature ratios.

  Dev risk uses a dot-product score on a ≤ 300-segment group-0 pool. Its absolute bits are not on the outer-test scale, and
  for CS_SINGLE the test native readout is a ridge, not a dot product. Only directions and relative sizes are compared.
  Units share training participants, so no interval is placed on unit-level statistics.
- **L1–L3 per query (forward passes).**
  - The per-unit evaluator rebuilds each RS unit without training: base encoder and head from the base checkpoint;
    context branch with the random backbone regenerated by `torch.manual_seed(seed)` + `Backbone(random_full)`;
    selected-epoch weights from the unit checkpoint.
  - It splits u_base and r per anchor. It scores the base and RS views under one readout contract (identical rng streams).
  - Reproduction tolerance: the per-participant top1 / top5 / mrr / rank_pct / logloss and the saved dev risks (selected
    epoch and epoch 0) must match within 1e-3. This is an engineering tolerance for float order, not a performance gate.
    Units outside it are listed as flagged and their values are kept apart.
  - Per identity: means of the L1/L2 quantities over all test anchors, and the L3 rank / score / prediction differences
    over its queries. Summaries over identities use pointwise bootstrap-t intervals (descriptive diagnostics, no
    families).
  - Units that selected epoch 0 enter as exact zeros, after the checkpoint check that their last layer is zero.
  - The reference `residual_diagnostics` is evaluated on the same arrays and stored next to the per-row implementation.

## 7. 探索性/原计划/勘误的身份 — status

Exploratory re-evaluation (ALN3.4 "数据启发的探索分析"). Not a correction: no frozen number is changed. Old documents stay
as they are. If an error in an earlier document is found, it gets a versioned correction note.

## 8. 可复用产物与实际需要的新计算 — reusable assets and the new computation actually needed

| asset | on disk | consequence |
|---|---|---|
| SC records (6 variant evaluations, ridge α, CV curves) | yes, 100/100 | §6 primary families on CPU now |
| SC checkpoints | PCA means and bases only (tok, raw, fm_pretrained, fm_random) | ridge coefficients not saved. SC per-query predictions are recomputable only by a closed-form refit on the same training rows: base/raw/token parts are CPU-light; FM-token variants need FM forwards (GPU). Not needed for this card |
| RS records (selected-epoch evaluation, dev curve epochs 0–30, epoch-0 check) | yes, 250/250 | L4 and identity-level L3 on CPU now |
| RS selected-epoch weights | yes, 250/250 | per-query L1–L3 by forward passes |
| RS epoch-0 state | separate file only where epoch 0 was selected (16 units); elsewhere overwritten | reconstructed exactly (r = 0); no file needed |
| RS intermediate epochs | no (resume files removed at completion) | only epoch 0 and the selected epoch can be analysed |
| Base L0 / L1 checkpoints and records | yes | base view on the same queries |
| FM weights (CBraMod, REVE, positions) | yes, sha256 = fetch receipt | pretrained context recomputable |
| Random-init backbones | not saved | regenerated from the seed; checked by the reproduction tolerance |
| Per-query predictions of any SC / RS / base unit | none | L1/L2 and per-query L3 need forward passes |

- GPU need: the 234 seed-3401 RS units whose selected epoch is > 0. The FM-context units are infeasible on CPU (CBraMod /
  REVE forwards over about 10⁵–10⁶ windows per unit). The 2-CPU session can hold Federici cohorts but not DTU, within the
  4 GB limit.
- This lane runs on CPU only:
  - one full re-run of the smallest small-capacity Federici unit, as the reproduction test;
  - a development-only check of one FM unit (random-backbone regeneration against the saved dev risk);
  - tiny-subset runs.
- No checkpoint is regenerated and nothing is submitted.

## 9. 输出文件 — outputs

- `results/auditory_alignment_v3/aln34/complement_function/`, all 0600:
  - `complement_function.json`: tables, families, L4, checkpoint layer, asset audit, GPU plan;
  - `per_identity_values.json`;
  - `units/<eid>.json` and `<eid>_queries.npz`: per-unit evaluator outputs.
- `docs/auditory_alignment_v3/COMPLEMENT_FUNCTION_REPORT.md` (0600).
- `private/auditory_alignment_v3/aln34/complement_function_units.txt`: the GPU unit list, the command and the estimate.
- Tests: `tests/auditory_alignment_v3/aln34/test_complement_function.py`.

## Addendum 1 (2026-10-16 20:21 CEST) — reproduction rule narrowed; engineering reason, before any merged layer value

§6 above is kept as written. The rule actually applied is narrower:

- **Bounded within 1e-3:**
  - the per-participant log-loss and rank_pct of both readouts, against both saved records;
  - both saved development risks (selected epoch, epoch 0).
- **Reported, not bounded:** top-1, top-5 and MRR. One near-tie flip from float order (CPU vs GPU, or another GPU model) moves
  them by 1/n_queries, about 0.01–0.04, and would wrongly flag a correct re-run.

**What was seen first.** One full CPU re-run (`ALN3X_6bb801c9730ca819`, Federici, NCE, small-capacity) matched under both
the old and the new rule:

- base view: max |Δ| 4.7e-7;
- RS view: max |Δ| 5.1e-4 (MRR);
- development risks: 2.9e-6 and 4.3e-6.

No layer summary had been merged or summarised when the rule changed. The aggregator applies the rule to the stored
deviations of every output; a stored flag is not trusted.

## Addendum 2 (2026-10-16 20:37 CEST) — code provenance of the CPU evaluator outputs

**What the recorded hash means in each output.**

- The five full CPU re-runs (`results/.../units/ALN3X_*.json`) recorded `sha256(complement_function.py)` at call time. During
  that period the file was being edited, but only in its aggregation, report and unit-list functions.
- Four of the five ran in one process that had loaded the module at about 20:16. Their recorded hashes are those of the
  file on disk when each unit started, not necessarily of the code they executed.
- From now on, the hash is taken when the module is imported (`MODULE_SHA256`). The development-only check
  `ALN3X_544007987cb9cc3f.dev_only.json` (20:27) and every later output carry the hash of the code they ran.

**Evaluator-path changes between these versions.** Only one: the batch size of the development-anchor pass went from 8
to 256 anchors (float order only; the layer summary of that pass is descriptive). Otherwise:

- the pool loop gained gc/empty_cache calls;
- the per-unit CUDA peak counter is now reset per unit.

**Agreement.** All five reproduce their saved records within the rule of Addendum 1.

## Correction 1 (2026-10-16 21:34 CEST) — errors found by a verifier in this note and in the v1 outputs; plan of v2, written before any v2 value is computed

A verifier reviewed the v1 outputs (report generated 20:37; this note's sha256 at that time d3d08781…). The text above stays as written; this section corrects it. Byte copies of this note, the v1 code, test, unit list, report and JSON as they stood at 20:37 are in `private/auditory_alignment_v3/aln34/complement_function_v1_20261016T2037/` (`SHA256SUMS` inside). The v1 per-unit outputs stay where they are (`results/auditory_alignment_v3/aln34/complement_function/units/`).

### C1.1 What was already seen (§3) was understated

- §3 says the RS-VALUE table showed "FM residuals ≈ 0 everywhere". That is wrong, and I had read that table in full. `COMPLEMENT_REVISED_RESIDUAL_RESULTS.md` §3, dtu · CS_SINGLE:
  - cbramod/residual_aligned_random ΔR −0.016, simultaneous [−0.031, −0.001], class I<0;
  - cbramod/residual_aligned_pretrained ΔR −0.021, pointwise [−0.039, −0.003], simultaneous [−0.045, +0.003] (brief B01 §6 flags this cell).
  - Both are unfavourable to RS: higher test risk than the base.
- I had also read that table's secondary column ΔR_native (point estimates only, no intervals). Its FM-residual entries: fau · NCE −0.003 to −0.004; dtu · NCE +0.002 to +0.003; federici · NCE +0.002 to +0.004; dtu · CS_SINGLE cbramod −0.022 (pretrained) and −0.009 (random). So the point estimates of the native RS family `FN-RS-NATIVE` were known before v1. Only its intervals and classes were new.

### C1.2 Federici identities (§5): the description was wrong, the computation was right

- §5 says HC and HC-v of one child are one identity. They are not. In `private/auditory_alignment_v3/reaggregate/entity_manifest.csv` every HC-v record has its own subject_uid (`HCv:<n>vocod`; identity_source "… no evidence of identity with HC"). The 86 human records give 86 identities: 37 HC, 33 CI and 16 HC-v (AGENTS ALN3.1 item 4). The 9 phantom sessions form one non-human entity and are excluded.
- The code used the manifest's subject_uid as written (n = 86 in every Federici family), so no number changes.

### C1.3 Access labels (§6): local_refit_capacity under L0 is access-matched

- §6 says "L0 gains are labelled context-assisted (the candidates read the aligned window)". That holds for:
  - the SC candidates that read the aligned window [−0.4 s, post): aligned_pretrained, aligned_random, small_context and concat;
  - every RS candidate (its context branch reads that window).
- It does not hold for local_refit_capacity. complement32 builds it from the base encoder's own tokens (`enc.forward_tokens(bt.patches(e))`, base L0 batcher, post-only lag window [0, post)), so it reads no EEG beyond what L0 reads. local_only likewise reads only the base's input.
- The v1 code tagged local_refit_capacity under L0 "context-assisted" (12 rows of report §3). The tag was inherited from the frozen `aln32_complement_interim.py` (SC-VALUE tag line 52), so the frozen `COMPLEMENT_REVISED_RESULTS.md` carries the same mislabel for local_refit_capacity under L0. Brief B01 §2 already states the point. The frozen document is not edited.
- Under L1 every SC variant is access-matched: L1 reads [−0.4 s, post), the same window as the SC context features.
- v2 derives the labels from an explicit access table (input window of every configuration) and prints that table in the report.

### C1.4 Readout contract (§2): the native NCE score has no fitted parameter

§2 says "the unified ridge bridge and the native score are fitted on 400 … segments". For NCE the native score is the fixed dot product u·v and has no fitted parameter. NCE covers every SC, L1, FM and TF row, and the NCE L0 and RS rows. Only CS_SINGLE fits a native ridge (B_nat, U → V).

The exact contract (`auditory_alignment.evaluate.Readouts` and `evaluate_continuous`):

- **Readout rows:** 400 training-participant fit + es segments, sampled with rng(seed + 1000), all grid anchors of each.
- **Unified bridge:** a ridge with intercept and an isotropic penalty. Its alpha is chosen on those segments' es rows by mean per-dimension correlation, after fitting on their fit rows; it is then refitted on all their rows.
- **CS_SINGLE native ridge:** alpha chosen by MSE on the same es rows, then refitted on all rows.
- **Temperature:** one per readout, on ≤ 300 training es queries scored against the es candidate pool.

### C1.5 SC calibration caveat (§4.5): the bridge carries it too, not only the temperature

- §4.5 names only the temperature. But the unified bridge's alpha is selected on training es rows and the bridge is refitted on fit + es rows, and the SC ridges were fitted on fit + es rows (`complement32.run`: units = fit + es, 8 anchors per segment).
- Consequences for SC:
  - unified R, rank_pct and top-1 all carry the in-sample es effect;
  - native NCE (dot-product) ranks do not;
  - native R carries it through the temperature only.
- Base L0/L1 and RS used es rows for early stopping, selection or calibration only (the RS development temperature uses es segments outside group 0).
- The direction of the effect on SC's test values is not determined here.

### C1.6 Counts, files and assets (§1, §2, §8)

- **§2, RS panel counts.** These were 75/125 (3407) and 74/125 (3413) at 19:58 (plan_ext.jsonl has 125 ALN32_RESIDUAL rows per panel seed), not "of 250". At 21:30 the counts were 83/125 and 83/125. They are still not used.
- **§8, RS epoch-0 row.** No unit has a separate epoch-0 file.
  - Every one of the 250 seed-3401 RS units has exactly one checkpoint file, `<eid>_best.pt`, a symlink into /projects that resolves. There is no `_resume.pt`.
  - residual32 writes epoch 0 to `_best.pt` first and overwrites it when a later epoch has lower development risk.
  - For the 16 units that selected epoch 0, the single file is the epoch-0 state (zero last layer, 16/16).
- **§8, FM weights row.** "sha256 = fetch receipt" was never checked in v1: the audit only tested that the files exist. v2 hashes every file listed in `FETCH_RECEIPT.json` and compares.
- **§8, per-query predictions.**
  - The v1 search matched only file names containing 'ALN32', 'complement' or 'residual'. Unit ids (ALN3X_/ALN3_<hash>) never contain these, so its count of 0 came from a search that could not find unit files. v2 searches by experiment id.
  - Already seen while preparing this correction:
    - `private/auditory_alignment_v3/sci_r1/continuous/<eid>__frozen.{npz,json}` exist for all 50 L0 base units. They hold per-participant lag and temporal-generalisation arrays, e.g. s1 (participants, 25, 9) and tg (participants, 25, 25, 4).
    - `probe_out*/` holds the runners' engineering-probe records and checkpoints for 5 of these ids.
    - None of these is a per-query evaluator prediction.
- **§1, the field `epoch0_max_abs_diff_vs_base`.**
  - This field (5.96e-8 in each of the 16 epoch-0 records) is measured by residual32 on a training-side batch at epoch 0 (32 training-fit segments × 8 anchors), not on the outer test.
  - For the outer test the claim rests on the checkpoint: zero last layer ⇒ r = 0 exactly ⇒ u = normalise(u_base).
  - The v1 report's "identical representation up to 6e-8" was a literal in the code, not a computed value.
- **§8, statements not measured.**
  - The statement that the session cannot hold the DTU cohort within 4 GB was not measured.
  - Neither was "CPU-light" for a closed-form refit of the FM-free SC variants.
  - v2 records the peak RSS of every CPU run.

### C1.7 Missing from the v1 report (docs/03 §1; AGENTS ALN3.4 item 8)

- The held-out development level actually achieved was stated only here (§1), not in the report. v2 states it in the report.
- The fit budgets were not recorded (docs/03 §1: "记录桥、PCA、温度所用身份／内容及预算"):
  - SC PCA: K = 64 components per block (tok, raw, fm_pretrained, fm_random), fitted with torch.pca_lowrank (randomised, 4 power iterations) on a fixed 8,000-row subsample of the training rows (rng GROUP_SEED + 2).
  - SC ridge rows: 8 grid anchors per fit and es segment of the training participants (`n_fit_rows` per record).
  - Grouping: 5 participant groups (GROUP_SEED 20261014).
- v2 tabulates the budgets from the records, together with the RS development and calibration budgets and the evaluator's readout budgets.

### C1.8 Duplicated members in the SC tallies

I saw the following while preparing this correction, from a check of the saved SC records (cbramod vs reve unit of the same cell):

| variant | what the two units share | alpha equal | per-participant \|Δ log-loss\| |
|---|---|---|---|
| local_only | the same ridge (same features, no PCA) | 50/50 pairs | ≤ 4.0e-4 |
| local_refit_capacity | the same token block; only the randomised PCA basis differs | 45/50 | ≤ 2.4e-4 |
| small_context | the same raw window | 40/50 | up to 0.20 bits unified, 0.04 bits native |

For small_context, the randomised PCA draw of the raw-window block matters.

So the v1 tally "over all 72 members" counts 6 local_only contrasts twice per readout. v2 reports the tally both over the 72 members and over the 66 distinct contrasts, and it reports the cross-backbone differences of the three FM-free variants.

### C1.9 GPU plan statements

- "peak GPU memory of the original evaluations ≤ 5.5 GB (DTU REVE)" is not supported.
  - `gpu_peak_allocated_mb` in the RS records is one process per unit, covering training and evaluation together.
  - It reaches 9,945–9,947 MB in FAU small-capacity units and 14,390–14,391 MB in DTU small-capacity units, on A100/A30 cards.
  - No record separates the evaluation's own memory.
- The worker setup was incomplete:
  - the commands used a bare `python` and omitted HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE, which the pool sbatch sets for REVE loads;
  - the worker had no claim, lock or sharding;
  - the 1160.8 GPU-minute estimate included the 5 units that already had outputs.
- The estimate's basis (1.25 × the record's eval_seconds + 90 s) is an assumption, not a measurement.

### C1.10 Report bookkeeping

- §7 "incomplete: 12" counted only the configurations with some coverage. In fact 29 of the 30 RS configurations had no L1–L3 summary: 12 were partly covered by epoch-0 zeros and 17 had no coverage at all.
- §9.5 "SC|complete: 600" counted variant pseudo-units. There are 100 SC records, holding 600 variant evaluations.

### C1.11 Code provenance of the v1 per-unit outputs (Addendum 2)

- Addendum 2 says two things:
  - 4 of the 5 recorded hashes are not the code that executed;
  - the evaluator path changed only in the batch size of the development-anchor pass.
- No copy of those intermediate file versions was kept, so neither statement can be verified, and the v1 report did not say so.
- What v2 changes:
  - The evaluator path moves into its own module, `auditory_alignment_v3/aln34/complement_function_eval.py`.
  - Every per-unit output records the sha256 of the evaluator module and the CLI module as loaded, and of the frozen modules they import.
  - At run time the loaded source of both modules is written to `results/auditory_alignment_v3/aln34/complement_function/code_snapshots/<name>.<sha12>.py`.
  - The 5 v1 full outputs and the v1 development-only output stay in `…/units/`, kept but not merged. They are re-run with the v2 evaluator into `…/units_v2/`, and the v1 vs v2 differences are reported.
  - Only v2 outputs are merged.

### C1.12 New computations in v2 (fixed before computing)

1. **Reproductions.** v2 re-runs on CPU, under the full contract, of the 5 Federici NCE small-capacity units, plus the development-only check of ALN3X_544007987cb9cc3f. Their v1 values were seen.
2. **New full CPU runs** of the 5 Federici CS_SINGLE small-capacity units, all with selected epoch > 0.
   - Seen already: their record-level ΔR (v1 report §4: unified −0.002 [−0.010, +0.006]; native about 0), their L4 rows and their checkpoint rows.
   - Not seen: any L1–L3 value.
   - This completes a second configuration, and the only one with a native ridge readout (CS_SINGLE) that is feasible on CPU.
3. **Engineering checks for the GPU plan.** These run the FM forward on CPU on small inputs, and neither is merged:
   - a development-only run of one Federici REVE residual_aligned_random unit, checking that the random REVE backbone regenerated from the seed reproduces the saved development risks;
   - a `--tiny` run of the same unit through the outer-test path.
4. **Descriptive items from saved artifacts:**
   - the access table;
   - the fit budgets;
   - the cross-backbone duplicate check (C1.8);
   - the asset search by experiment id and the checkpoint file inventory;
   - the FM-weight hashes against the fetch receipt;
   - the records' GPU-memory figures per dataset × backbone;
   - regression checks of RS-VALUE against the frozen `aln32_residual.json` and of the SC level estimates against the frozen `aln32_simple_complement.json`.

Unchanged rules:

- The reproduction rule of Addendum 1 applies; top-1, top-5 and MRR tie flips are reported, not bounded.
- No selection is made.
- No interval is placed on unit-level statistics.
- The CPU runs use nice -n 10, run one at a time and are kept under 4 GB RSS (a watchdog stops a run above 3.8 GB).

## Addendum 3 (2026-10-16 23:00 CEST) — v2 execution record, written after the runs listed in C1.12

**Code.**

- The evaluator module `complement_function_eval.py`, sha256 be2107d36af9…, was not edited after the first v2 run (21:54). Every v2 per-unit output records it, and its loaded source is in `results/auditory_alignment_v3/aln34/complement_function/code_snapshots/`.
- The value-producing functions are byte-identical to the v1 file (test `test_evaluator_math_identical_to_v1`). `evaluate_unit` differs from v1 only in provenance and runtime fields.
- The CLI module `complement_function.py` was edited during the batch (report, aggregation and GPU-plan code only). The v2 outputs therefore record three CLI versions (056fdb0de95b, 6cd5e3fc51ff, fadfbf789ff7), each snapshotted.
- The final aggregation used CLI b269c232c1ce, also snapshotted.

**Runs.** All on CPU inside the session allocation 1039458 (nodecpu10), 2 torch threads, nice 10, one at a time. The node was shared with other agents (load average 3–10).

| # | run | what was checked | result | wall time |
|---|---|---|---|---|
| 1 | Re-runs of the 5 Federici NCE small-capacity units | reproduction rule; v1 vs v2 | All reproduce: bounded max \|Δ\| ≤ 3.9e-4; development risks ≤ 1.1e-5. Against v1: max \|Δ\| over every numeric result leaf 1.2e-7, only in the development-layer angle summaries (the dev-anchor batch size change of Addendum 2); per-query arrays identical. | 109–301 s |
| 2 | Development-only re-run of ALN3X_544007987cb9cc3f (CBraMod random-init) | v1 vs v2 | Identical to v1. Saved development risks reproduced within 1.4e-6 / 4.8e-7. | 88 s |
| 3 | New full runs of the 5 Federici CS_SINGLE small-capacity units | reproduction rule | All reproduce: bounded max \|Δ\| ≤ 2.6e-4; development risks ≤ 9.5e-7. | 100–141 s |
| 4 | Development-only run of ALN3X_eb9fc79c5afda51f (Federici NCE, REVE random-init) | random REVE backbone regenerated from the seed vs the saved development risks | Reproduced within 9.5e-7 (selected epoch) and 4.3e-6 (epoch 0). | 715 s |
| 5 | `--tiny` run of the same unit | outer-test path with a REVE context (2 test participants × 4 queries, 24 readout segments) | Completed. Not comparable to the records by design. | 1015 s |

**Memory.** The process peak RSS (`ru_maxrss`) was ≤ 2.2 GB for runs 1–4 and 3.37 GB for the REVE `--tiny` run, all under the 4 GB limit; the watchdog never fired.

**Deviations from C1.12.** None in what was run. The only deviation is the CLI edits during the batch, which are recorded per output.

**After the runs.**

- `--write-units` at 22:54 wrote the unit list and the sbatch template: 224 pending units, about 1,144 GPU-minutes (assumption-based).
- `--aggregate` ran at 22:55, 22:58 and 22:59. The two re-runs followed wording and formatting edits of the report code only.
- The computations are deterministic (fixed bootstrap seeds). `per_identity_values.json` is byte-identical to v1, and every family value equals v1 (`regression.v1_vs_v2`: max |Δ| 0, no class change).
- The new values first seen in v2:
  - the L1–L3 values of RS·federici·CS_SINGLE·small_capacity: ‖r‖/‖u‖ 0.62, angle 18°, ranks changed in 0.92 / 0.81 of the queries, ΔR −0.002 / −0.000;
  - the development-side layers of the two development-only runs;
  - the cross-backbone copies and the budgets.

**Note hash.** `complement_function.json` records `meta.note_sha256` = 60825a1f6e39…. That is the hash of this note up to the end of Correction 1, i.e. without this addendum, which was written after the aggregation.

**Final aggregation (23:01), superseding the "Note hash" paragraph above.** The report code was edited twice more, wording only: the full interpreter path in the report header, and the backbone label of the parameter counts. The aggregation was then re-run (CLI 82690093acd5…, snapshotted).

- Values: unchanged (deterministic).
- `meta.note_sha256` now records this note as it stood before this paragraph: c9e32a0f1bd8….

**Final aggregation (23:02), superseding the 23:01 paragraph.** One more report-code edit was made: §9 now lists the CLI versions recorded by the v2 outputs, each with its snapshot and a check that its main() equals the current one. A matching test was added. The aggregation was re-run (CLI 43c53efcc9da…, snapshotted).

- Values: unchanged.
- `meta.note_sha256` records this note as it stood before this paragraph: 902d0dc05a69….

## Edit 2026-10-16 23:39 (lead agent)

After the second review, report wording only: §12.2 no longer calls the larger |point estimate| an "at most" bound (the pointwise intervals allow larger changes); §7 prints half-integer selected-epoch medians exactly instead of rounding half to even. Correction to Addendum 3: the 14 dev-layer leaves of each re-run Federici NCE unit differ between units/ and units_v2/ (max 1.2e-7), not only the angle summaries; and the cross-backbone counts and fit budgets were first seen while preparing Correction 1 (C1.7, C1.8), not first in v2. No number changed.
