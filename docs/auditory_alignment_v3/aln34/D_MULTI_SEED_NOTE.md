# 透明分析记录 — R34_D_PANEL: D multi-seed panel (seeds 3401 / 3407 / 3413)

Written 2026-10-16 19:45–19:48 CEST, **before any value of a seed-3407 or seed-3413 D unit was read or computed**.
Template: `AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/templates/ANALYSIS_NOTE.md` (sha256 `a632cffe…`). Basis: card
`R34_D_PANEL` (package `plans/comparison_cards.json`), package docs/04 §A, docs/06, `configs/seed_and_reporting.yaml`,
AGENTS.md ALN3.4 item 5, intake `INTAKE_20261016.md` action A01. User instruction: "按这个包执行".

## 问题与分析对象 (question and object)

Do the method differences of the completed D panel keep their size and direction across training seeds 3401, 3407 and 3413?

- Arm: `lag_local_tokens` (local), objective NCE, datasets FAU and DTU.
- Panel registered in ADDENDUM_03 §1.1 (2026-10-11), roles `P4_ATTENTION_ADAPT/{attention, no_adaptation, spatial_adaptation}`:
  - D_ADAPT adapters `none` / `input_spatial`, NCE: 40 rows per seed (2 datasets × 2 adapters × 10 fold cells);
  - D_ATTENTION `attended_alignment` and `alignment_plus_selection`, NCE, integrators `mean_score` and `learned_temporal`:
    80 rows per seed (2 × 2 × 2 × 10).
- Fold cells: 5 subject folds × 2 content folds per configuration.
- Card contrasts: `attended_vs_alignment_selection` (AT-TASK) and `none_vs_input_spatial` (AD-GAIN). The other ADDENDUM_12
  families that the panel rows fully determine (AT-LEVEL, AT-LENGTH, AT-INTEGRATOR, AD-SUPPORT) are reported as well.

## 数据/结果版本 (data and result versions)

- Plan rows: seed 3401 from `AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010/plans/units.jsonl` (`core.PLAN`, sha256 `0aefb27a…`);
  seeds 3407/3413 from `private/auditory_alignment_v3/plan_ext.jsonl` (sha256 `85b44d8d…`), each with `reference_3401_id`.
- Live completion, read from the records' `status` field at 19:4x:
  - panel: 240/240 complete (D_ADAPT 80, D_ATTENTION 160 incl. 80 `learned_temporal` rows);
  - seed-3401 counterparts: 240/240 complete, spec identical apart from the seed.
- Record code hashes, identical for all three seeds: adapt `f029aabd1ea656c1`, attention `988bda85c8d8e404`.
  Target contract `dense20ms_v1`, target `local`.
- D_ADAPT bases: same-seed, same-fold A_LOCAL `lag_local_tokens` units (all 120 links checked).
- Each `learned_temporal` record names its same-fold, same-seed `mean_score` twin in `shared_model_with`.
- Reused analysis code, unchanged and imported (sha256 equal to the values in the published `results/auditory_alignment_v3/d_lag/d_lag.json`):
  `d_lag_interim.py` `0c192214…`, `bc_interim.py` `2840df81…`, `sci_r1/stats.py` `8bb141cf…`.

## 写说明时已见哪些结果 (what had been seen when this note was written)

1. **Seed 3401, all D results**, published 2026-10-14 (Slurm 1040261):
   - files: `D_ATTENTION_RESULTS.md`, `D_ADAPT_RESULTS.md`, `D_COVERAGE_MATRIX.md`;
   - seen by the researcher through the brief (B01) and read by this agent today.
   - Numbers already known that bear on this panel:
     - AD-GAIN NCE input_spatial: FAU +0.084 (10 %) / +0.246 (30 %); DTU −0.154 (10 %) / +0.237 (30 %);
     - AT-TASK NCE attended → align+sel: FAU +0.002 / +0.005 / −0.001 and DTU −0.001 / −0.005 / −0.000 at 5 / 10 / 20 s,
       all with intervals that contain 0;
     - AT-INTEGRATOR: mostly I<0 (24/30 cells over all tasks);
     - AT-LEVEL and AT-LENGTH: all I>0.
   - So the question was formed with seed 3401 known.
2. **The degenerate native `learned_temporal` column.** An earlier session made a read-only check of summaries in
   `private/auditory_alignment_v3/d_lag/per_identity.json` (recorded in B01; this agent did not reopen the file). It found:
   - CS: native learned_temporal is 0 for every identity at 20 s; at 10 s it is 1 (DTU) or 0.5 (FAU); the DTU 5 s identity
     mean is about 0.965;
   - NCE: also below chance at 20 s (FAU attended NCE identity mean 0.298).
3. **Panel (3407/3413): only completion status and record structure.**
   - What this agent looked at: the `status` field, key names, code hashes, dependency and twin ids, fold cells.
   - No metric value of any panel record was printed, computed or plotted.
   - No evidence that anyone else saw panel values:
     - no existing script reads D rows with a seed other than 3401 (`d_lag_interim.collect` and `bc_interim.d_status`
       filter seed 3401; `aln32_panel_interim` covers other families);
     - the intake (19:31) says "Panel values not read yet";
     - B01 L763–L767 lists the rows as complete and not aggregated.
4. **Code reading (no values).**
   - `run_attention.py`, `learned_temporal`:
     - fitted on training windows whose candidate order is mirrored together with the label;
     - every test window is scored as (attended, ignored), so the correct answer is always class 1;
     - a constant-class prediction therefore scores exactly 0 or 1. This matches the degenerate native column.
   - `run_adapt3.py` stores, per participant, support fraction and readout, only `gain_bits` (mismatched − true logloss),
     `rank_pct`, `top1` and `n_query`. The true-query logloss itself is not stored.

## 与旧分析相比改变了什么 (what changes relative to the old analysis)

- **Unchanged:** endpoints, signs (positive = candidate better), per-identity aggregation, bootstrap-t (B = 4,000) and family
  max-t. All are imported, not re-implemented:
  - `d_lag_interim.collect`, `att_families`, `ad_families`, `NEW_DIR`;
  - `bc_interim.run_family`, `member_values`;
  - `sci_r1.stats`.
- **New:**
  - seeds 3407 and 3413;
  - "panel families": each ADDENDUM_12 family restricted, by design and not by data, to the members whose two
    configurations are in the registered panel, with the same member set for every seed;
  - an identity-mean-across-seeds effect;
  - the between-seed range;
  - a coverage table;
  - pairing QC.
- **Reproduction check:** seed 3401 is also run with the full ADDENDUM_12 families and compared number by number with
  `d_lag.json`.
- **Not added:**
  - a new primary endpoint;
  - D_ADAPT true-query risk R: the fields are not in the records, and R is not derived indirectly;
  - the per-segment 5 s `attention_2afc`: not aggregated at 3401 either; listed as open;
  - group contrasts.

## 配对键、身份与内容汇总 (pairing keys, identity and content aggregation)

- **Within a seed.** Reference and candidate share:
  - dataset, subject fold, content fold and seed;
  - evaluation code hash and target contract.
- Split and target hashes are not stored separately in these records. The bound spec, fold and target contract, copied from
  the 3401 row with only the seed changed, stand in for them.
- **D_ADAPT none vs input_spatial**
  - Same frozen base: the same `dependency.base_same_fold` unit.
  - Same query rule (last 70 % in recording order) and the same participants.
  - QC: equal `n_query` and `n_support` per identity.
  - Adapter `none` must be identical across support fractions (ADDENDUM_12 QC).
- **D_ATTENTION task contrast (AT-TASK)**
  - Two separately trained models (`attended_alignment`, `alignment_plus_selection`) of the same seed and fold cell.
  - QC: the same participants and the same `n_windows` per window length and readout.
- **D_ATTENTION integrator contrast (AT-INTEGRATOR)**
  - Within one model.
  - The analysis reads the `mean_score` record, which holds both integrators, as `d_lag_interim` does.
  - QC: each `learned_temporal` record's `attention_windows` must equal its twin's.
- **Identity**
  - Identity = the FAU / DTU test participant id. Per seed and configuration, the identity's value is the mean over its
    units, i.e. the two content folds of its subject fold, exactly as in `d_lag_interim.collect`.
  - Per seed: the paired difference Δ(i, s).
  - Identity mean: Δ̄(i) = mean over the seeds in which that pair exists.
  - A reference from one seed is never paired with a candidate from another seed.
  - n = number of identities (3401: FAU 67 = TH 14 / HA 29 / CI 24; DTU 44 = NH 22 / HI 22). Seeds, folds and content
    folds never add n.
- **Complete-case sensitivity:** if any identity lacks a pair in some seed, the seed-mean family is also run on the
  identities that have all three seeds (the ADDENDUM_11 rule). Missing pairs are listed and never filled with 0.

## 主要量、辅助量、不确定性处理 (primary and secondary quantities, uncertainty)

### Endpoints

- **D_ADAPT** (main table, as before): unified `gain_bits`, in bits per query (query = last 70 %).
  Secondary, each in its own column:
  - unified `rank_pct` (Δ = reference − candidate, positive = better);
  - unified `top1`;
  - native `gain_bits`.
- **D_ATTENTION**: unified `mean_score` 2AFC accuracy (proportion; chance 0.5).
  - Secondary: native accuracy; unified mean margin.
  - In AT-INTEGRATOR the candidate is the `learned_temporal` accuracy.
- **True-query risk R for D_ADAPT:** not computed, because the records lack the true-query logloss. Listed as a next
  intervention that needs re-evaluation.
- Native is never averaged with unified, and rank is never merged with top-1 accuracy.

### Families

Each simultaneous 95 % interval uses the max-t within its family. The labels are the ADDENDUM_12 labels.

| Family (panel) | Families | Members per family |
|---|---|---|
| AT-LEVEL \| ds \| task \| NCE | 4 | 5 s, 10 s, 20 s (accuracy − 0.5) |
| AT-INTEGRATOR \| ds \| task \| NCE | 4 | 5 s, 10 s, 20 s (mean_score → learned_temporal) |
| AT-LENGTH \| ds \| task \| NCE | 4 | 5 s → 10 s, 5 s → 20 s |
| AT-TASK \| ds \| w | 6 | `align->align+sel NCE` only |
| AD-GAIN \| ds \| NCE \| support | 4 | `input_spatial` only |
| AD-SUPPORT \| ds \| NCE | 2 | `input_spatial` only |

- Here ds ∈ {fau, dtu}; task ∈ {attended_alignment, alignment_plus_selection}; w ∈ {5, 10, 20} s; support ∈ {0.1, 0.3}.
- Totals: 24 families, 44 members.
- In a one-member family the simultaneous interval equals the pointwise bootstrap-t interval.
- At 3401, the full-family simultaneous interval (which includes the non-panel members) is shown alongside for reference.

### Computation

- **Per seed:** `run_family` on that seed's identity values.
  - Replicate indices come from `group_seed(label, metric)`.
  - So when the identity sets coincide, the three seeds and the seed mean share the same identity resamples. Identity vectors
    are resampled jointly (ALN3.1 docs/12 §5).
- **Seed mean:** the same families and machinery applied to Δ̄(i).
- **Between-seed range:** the minimum and maximum of the three per-seed estimates, and their spread. Per-seed interval classes
  are descriptive only.
- **Group columns** (FAU TH/HA/CI, DTU NH/HI): descriptive and pointwise; n < 5 shows n only.

### Uncertainty

- Intervals are conditional on the fitted models.
- Three seeds are a coarse sample of training randomness. That randomness also includes seed-dependent readout and probe
  sampling: readouts use `default_rng(seed + 1000)` and the learned_temporal mirroring uses `default_rng(seed + 4242)`.
- D_ADAPT support-row sampling is seeded by participant, not by seed.
- No p-values. "I>0 / I<0 / contains 0" describes an interval.

## learned_temporal and the candidate-order correction (track R34_ATTENTION_ORDER)

- **Could change:** every AT-INTEGRATOR number (12 panel members, per seed and seed mean, unified primary and native
  secondary) and any learned_temporal accuracy level. These are reported as legacy-order values. They are provisional until
  R34_ATTENTION_ORDER re-evaluates with paired order swap or antisymmetric scoring. The old values are kept, not overwritten.
- At 5 s (one segment) learned_temporal only sets a threshold on a single score difference; it does not integrate over time.
- **Not affected:**
  - AT-LEVEL, AT-LENGTH and AT-TASK: `mean_score` is the sign of the mean score difference, which is antisymmetric under a
    candidate swap except for exact ties; the margin is that mean;
  - all D_ADAPT numbers.
- The native learned_temporal column at 3401 is degenerate. The panel's native learned_temporal values are reported, not
  interpreted.

## 探索性/原计划/勘误的身份 (exploratory, planned or erratum)

- This is an exploratory re-aggregation under ALN3.4 (card R34_D_PANEL). It is not an erratum.
- The panel rows were registered before any of them ran (ADDENDUM_03 §1.1). No frozen aggregation rule existed: ADDENDUM_05 §1
  excludes D, and ADDENDUM_12 has no panel clause.
- The 3401 per-seed contrasts reproduce ADDENDUM_12 (already seen).
- The 3407/3413 values are computed after this note. However, the design was formed with 3401 known and the participants
  are the same, so this is not a blind or independent confirmation.

## 可复用产物与实际需要的新计算 (reuse and new computation)

- **Reused:**
  - the 240 panel records and their 240 seed-3401 counterparts;
  - for the reproduction check, the other seed-3401 lag_local D_ATTENTION `mean_score` and D_ADAPT records (100 + 120 read
    in total).
- No training, no GPU job and no new evaluation.
- **New:** CPU aggregation only, inside the session allocation (Slurm 1039458, nice 10, under 4 GB RAM).
- **Not done here** (each needs a GPU re-evaluation):
  - D_ADAPT true-query R;
  - order-corrected learned_temporal, which belongs to R34_ATTENTION_ORDER.

## 输出文件 (outputs)

- Code: `auditory_alignment_v3/aln34/d_multiseed.py`.
- Synthetic tests: `tests/auditory_alignment_v3/aln34/test_d_multiseed.py`.
- `results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json` (0600).
- `docs/auditory_alignment_v3/D_MULTI_SEED_RESULTS.md` (0600; follows `templates/EXPERIMENT_UPDATE.md`).
- `private/auditory_alignment_v3/aln34/d_multiseed/per_identity.json` (0600): per-identity values per seed.

## Not in the panel (no three-seed statement)

- every CS_SINGLE cell (D_ATTENTION and D_ADAPT);
- `output_low_rank`;
- `selection_only`, including the DTU AT-TASK I<0 cells "align NCE → selection_only";
- AT-TASK "align → align+sel CS";
- D_COVERAGE (the whole family);
- the D policy arms (`dense_fm_policy`, `complement_policy`; on hold);
- the per-segment 5 s `attention_2afc`.

## Reporting rules

- Every member is reported whatever its direction. I<0 and contains-0 cells appear in the same tables as I>0.
- No count-only summary.
- No member, seed or identity is dropped because of its result.
- Missing pairs are listed.

## 更正与补充 (correction and addendum) — written 2026-10-16 20:34–20:36 CEST, after independent verification of v1

Appended, not rewritten: the text above is the note as it stood at 19:47:36 (sha256 `c410f643…`, the value recorded in v1 of the
results). This section was written **before** any value of the additions below (A–F) was computed.

### 写本节时已见哪些结果 (what had been seen when this section was written)

- **Everything in v1.** `D_MULTI_SEED_RESULTS.md` v1 (generated 20:01, hand-written sections finished at 20:03:46, file mtime) and
  `d_multiseed.json` v1. That is every seed-3407 and seed-3413 panel value, the identity means over seeds, the between-seed ranges
  and the interval classes. v1 is archived unchanged in `private/auditory_alignment_v3/aln34/d_multiseed/v1_20261016T2003/`
  (doc, JSON, per-identity file, code, tests and this note as of 19:47; `SHA256SUMS`).
- **The verifier's report on v1.** It reproduced every v1 number and listed the problems corrected below. It also contains values
  of some of the additions:
  - a Monte-Carlo redraw with 20 alternative RNG seeds for four cells: AD-GAIN fau 10 % at 3401 (panel family) I>0 in 4/20;
    AT-LENGTH fau attended 5→10 s at 3413 I>0 in 19/20; AT-INTEGRATOR dtu attended 5 s at 3413 I>0 in 19/20; AT-TASK fau 10 s
    identity mean I>0 in 20/20;
  - spread-versus-width counts for AT-INTEGRATOR: 8/12 above every per-seed simultaneous width, 1/12 between, 3/12 below every width.
- So none of A–F is blind. They are corrections and exploratory sensitivity analyses made after all panel values were seen. They
  are reported whatever they show.

### Corrections to v1 (no v1 number changes; labels, wording and rendering)

1. **Rank unit.** `rank_pct` is the mean over queries of rank / (n_candidates − 1) (`auditory_alignment/evaluate.py` `_metrics`,
   stored for the true query by `run_adapt3._gain`): a proportion, 0 = true candidate ranked first, about 0.5 = chance. The reported
   Δrank (reference − candidate, positive = better) is therefore a proportion; ×100 gives percentile points. v1 called it
   "rank-percentile points" and "rank %": DTU 10 % identity mean −0.024 is −2.4 percentile points, not −0.024 points.
2. **Native versus unified, DTU 10 %.** v1 §2.2 ("the disagreement … reproduces across seeds") and §3(c) ("fits the opposite native
   sign") overstate. Native gain is positive at 3401 and 3413 but about 0 (−0.009) at 3407, and no per-seed or identity-mean native
   interval excludes 0. What holds in all three seeds is unified I<0 with native unresolved.
3. **Spread versus width.** v1 compared the between-seed spread with the per-seed interval widths under two different rules: "smaller
   than every width" (32/32 non-integrator members) and, for AT-INTEGRATOR, "larger than the narrowest width" (9/12). The symmetric
   rule is used from now on: below every per-seed simultaneous width / between / above every width (addition C).
4. **Rounding.** "spreads ≤ 0.014" (AT-LEVEL, AT-LENGTH): the largest is 0.01418, so it is written ≤ 0.0142.
5. **Rendering.** The D_ATTENTION rows of the v1 coverage table had an unescaped `|` in the first cell, which shifted their columns.
6. **Provenance.** In v1 the last bullets of §5 and the paragraph under "Not in the panel" were added by hand, although the header
   said §5 was generated; the hand-written time "20:00–20:05" should have been 20:01–20:03:46; "peak memory well under 1 GB" was a
   fixed string, not a measurement. From v2 the generator writes all of §5 and that paragraph, measures peak memory, and carries the
   hand-written sections (2–4, 6, 7) over verbatim.
7. **Monte-Carlo margin.** The seed-3401 change of AD-GAIN fau 10 % from the published "contains 0" to panel-family I>0
   (sim_low +0.0005) is true for the declared draws, but sits at the Monte-Carlo margin. v1 should not have said that the class
   change is caused "only" by the smaller family without that caveat (addition A).
8. **This note, "seed-3401 counterparts: 240/240 complete".** That counts the 240 `reference_3401_id` links of the 3407/3413 rows.
   They point to 120 distinct seed-3401 records, all complete.

### Declared additions (computed after this section; all exploratory)

- **A. Monte-Carlo stability of the interval classes.**
  - Draws: K = 50 alternative draw sets. Set k adds 1000·k to `sci_r1.stats.SEED` (k = 1…50), which shifts every group seed;
    k = 0 is the declared draw.
  - Fixed: the identities, estimates, families and B = 4,000.
  - Scope: the primary readout only. Cells:
    - panel families: per seed (3401, 3407, 3413) and the identity mean;
    - the full ADDENDUM_12 families at 3401, panel members only (for the published-versus-panel class);
    - the card families of B.
  - Reported per cell: the declared class, the number of the 50 alternative draws with the same class, and the range of the
    simultaneous bounds.
  - The declared draws stay the reported result. No draw is chosen by its outcome, and there is no stability threshold: the
    results document lists every cell below 50/50 and the JSON holds all cells.
- **B. Card contrasts with max-t across windows or support levels (post hoc sensitivity).**
  - Families: `R34-CARD|AT-TASK|<ds>` (align → align+sel NCE at 5 / 10 / 20 s within a dataset) and
    `R34-CARD|AD-GAIN|<ds>|NCE` (input_spatial at 10 % and 30 % within a dataset).
  - Computed per seed and for the identity mean, on the primary readout.
  - The labels are new, so the draws are new but still shared across seeds.
  - There is no control across datasets: the datasets have different identities, and ADDENDUM_12 families are per dataset.
  - The declared one-member panel families stay the main families. B shows how much multiplicity control across windows or
    support levels changes their classes.
- **C. Between-seed spread versus per-seed simultaneous width (descriptive).**
  - For every primary member: the three widths from the declared draws.
  - Category: below every width, between, or above every width.
  - The ratios of the spread to the narrowest and to the widest width.
- **D. Secondary readouts.** The per-seed pointwise 95 % intervals, already in the v1 JSON, are shown in the document.
- **E. D_ADAPT support and query sizes.** n_support and n_query per participant-unit block, by dataset and support fraction, with a
  check that they are equal across seeds and adapters. This backs the counts quoted in the competing explanations.
- **F. Run record.** A second computation in the same process (without A) is compared number by number with the first. Peak
  resident memory is measured (ru_maxrss).

### Not changed

- The declared panel families, endpoints, signs, identity aggregation and draws.
- Every per-seed, identity-mean and between-seed number of v1.
- The main table (unified gain_bits).
- D_ADAPT true-query risk R is still not available: the records store only gain_bits, rank_pct, top1 and n_query per readout
  (plus n_support), with no true-query logloss. It needs a GPU evaluation-only rerun under a new execution version. All 60 frozen
  bases are present.
- learned_temporal stays provisional under R34_ATTENTION_ORDER. A–C cover the AT-INTEGRATOR rows as legacy-order values only.
