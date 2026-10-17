# 透明分析记录 — E seed panel: private task (E families), seeds 3401 / 3407 / 3413

Written 2026-10-16 23:45–23:53 CEST (file first saved 23:52:28), **before any value of a seed-3407 or seed-3413 E unit was read or
computed**.
Template: `AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016/templates/ANALYSIS_NOTE.md` (sha256 `a632cffe…`). Basis: package docs/00
("completed multi-seed records must not sit idle merely because a family lacks registered panel-summary wording"), docs/05 §5,
docs/06, `configs/seed_and_reporting.yaml`, AGENTS.md ALN3.4 items 2, 3, 5 and 10; the frozen rule `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`
§6 "Seed panel supplement" (sha256 `a7b27951…`); `ADDENDUM_03_ALN3_1_SEED_PANEL.md` §1.1; `CORRECTION_01_FULL_UPDATE_LABEL.md`.
Sister analysis imitated: `auditory_alignment_v3/aln34/d_multiseed.py` with `D_MULTI_SEED_NOTE.md` (including the corrections its
verifier asked for: one symmetric spread-versus-width rule, measured memory, a fully generated §5, Monte-Carlo class stability).

## 问题与分析对象 (question and object)

Do the private-task method contrasts of the completed E seed panel keep their size and direction across training seeds 3401,
3407 and 3413, separately for calibrated NLL, AUC and the history increment?

- Panel registered in ADDENDUM_03 (2026-10-11), ALN3.1 role panel `P5_PRIVATE` (`seed_confirmation_pairs.yaml`: native_gx,
  local_native, random_full, pretrained_full, pretrained_peft, public_task_transfer). Rows per seed (3407 = 3413):
  - in the frozen v3.0 plan (`core.PLAN` = `AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010/plans/units.jsonl`, `seed_scope = panel`):
    E_GENERIC `random_full` and `pretrained_peft`, 2 objectives × 2 backbones × 5 folds = 40; E_GX `GX_NATIVE` window full, 5;
    E_LOCAL `lag_local_tokens` window full, NCE and CS_SINGLE, 10;
  - in `private/auditory_alignment_v3/plan_ext.jsonl` block 2 (ADDENDUM_03 §1.1, each with `reference_3401_id`): E_GENERIC
    `pretrained_full`, 2 × 2 × 5 = 20; E_PUBLIC_TRANSFER source `lag_local_tokens`, `task_partial`, NCE and CS_SINGLE, 10.
  - Together 85 rows per seed, 170 panel rows. The registry `private/auditory_alignment_v3/governance/seed_panel_v31_registry.json`
    lists the 255 E requirements as 85 canonical cells × 3 seeds; every one of the 170 panel rows is in it, and each canonical cell
    has its seed-3401 counterpart (85 distinct seed-3401 rows).
- Completion, read from the records' `status` field (2026-10-16 ~23:40): 170/170 panel records complete; 85/85 seed-3401
  counterparts complete. E_GENERIC as a whole is 220/220 (100 seed-3401 breadth rows + 120 panel rows). No `.FAILED` record.
- Panel configurations (17 per seed):
  - E_GENERIC {NCE, CS_SINGLE} × {cbramod, reve} × {random_full, pretrained_peft, pretrained_full} (12);
  - E_LOCAL `lag_local_tokens` full × {NCE, CS_SINGLE} (2);
  - E_PUBLIC_TRANSFER `lag_local_tokens` `task_partial` × {NCE, CS_SINGLE} (2);
  - E_GX `GX_NATIVE` full (1).
- Contrasts present in the panel = the frozen ADDENDUM_05 §5 families (`bc_interim.private_families`) restricted, by design and not
  by data, to the members whose reference **and** candidate configurations are both panel configurations:

| Family (scope) | Panel members (of the frozen members) | Reference → candidate |
|---|---|---|
| PE-GENERIC \| objective \| backbone (4 scopes) | 2 of 4: `pretrained_peft`, `pretrained_full` | E_GENERIC `random_full` → `pretrained_peft` / `pretrained_full`; both are recipe contrasts (CORRECTION_01; the frozen code still tags `pretrained_full` "initialization (matched full update)") |
| PE-LOCAL \| objective (2 scopes) | 7 of 16: `generic/{cbramod, reve}/{random_full, pretrained_peft, pretrained_full}`, `transfer/lag_local_tokens/task_partial` | E_LOCAL `lag_local_tokens` full → that configuration |
| PE-TRANSFER \| objective (2 scopes) | 1 of 6: `transfer/lag_local_tokens/task_partial` | non-transferred twin (= E_LOCAL `lag_local_tokens` full) → E_PUBLIC_TRANSFER `lag_local_tokens` `task_partial` |

  - Each family is run for NLL and for AUC separately, as frozen: 16 primary families, 48 member cells per seed.
  - The PE-TRANSFER panel member and the PE-LOCAL member `transfer/lag_local_tokens/task_partial` have the same reference and the
    same candidate. They are the same paired difference reported in two frozen families, so only the critical value differs.
  - E_GX: no frozen contrast contains E_GX. It enters only the levels table (as at 3401: ADDENDUM_05 §5 "levels for every private
    configuration, including E_GX").
  - PE-COMPLEMENT and PE-DISTILL have no panel rows (E_COMPLEMENT and E_DISTILL are seed-3401-only).

## 数据/结果版本 (data and result versions)

- Plan files: `units.jsonl` sha256 `0aefb27a…`, `plan_ext.jsonl` `85b44d8d…`, registry `29e5756d…`.
- Record census (structure only; see the next section for what was looked at), all three seeds:
  - code groups / hashes: E_GENERIC, E_LOCAL, E_GX group `private` `51341741b9019c88`; E_PUBLIC_TRANSFER group `transfer`
    `eaef72595370515d`. Exception: 4 of the 85 seed-3401 counterparts carry `f2cf13bc441a6386` (3 of the 5 E_GX full units and
    1 of the 5 E_GENERIC NCE cbramod random_full units, written 2026-10-10 20:11–20:28). `IMPLEMENTATION_RECEIPT.md` §5 records
    `f2cf13bc441a6386` ≡ `51341741b9019c88` (the family registry moved from `core.py` to the unhashed `registry.py` at 20:20; no
    computational change). Every panel record carries the current hash.
  - target contract `current_class`; information strata E_LOCAL / E_GX `local_only`, E_GENERIC `padded_private_epoch_no_extra_EEG`,
    E_PUBLIC_TRANSFER `private_task_declared_input`; calibration set "training children's early-stopping blocks", head fit
    "training children, early-stopping blocks only" in every record.
  - folds: 5 subject folds × content fold 0; the same child sets per fold (13 / 13 / 13 / 13 / 12, 64 children, no overlap) in
    all three seeds; every panel record has the same child set and the same per-child trial counts as its seed-3401 counterpart.
  - transfer donors: every E_PUBLIC_TRANSFER record's donor is the A_LOCAL FAU `lag_local_tokens` full unit of the same objective
    and **the same seed** (subject fold 0, content fold 0, as `run_transfer.local_donor_row` fixes in advance); all 30 donor
    checkpoints are present. The seed panel therefore also varies the donor.
- Frozen analysis code, imported unchanged: `bc_interim.py` sha256 `2840df81…` (= the value at freeze in
  `private/auditory_alignment_v3/bc_interim/code_sha256_at_freeze.txt`), `sci_r1/stats.py` `8bb141cf…`. Published seed-3401
  output: `private_e.json` sha256 `e6678e40…` (identical copies in `private/auditory_alignment_v3/bc_interim/private/` and
  `results/auditory_alignment_v3/bc_interim_private/`), `PRIVATE_E_INTERIM.md` `490cdeeb…` (identical copies in the same private
  folder and `docs/auditory_alignment_v3/`).

## 写说明时已见哪些结果 (what had been seen when this note was written)

1. **Seed 3401, all private E results.**
   - `PRIVATE_E_INTERIM.md` (ADDENDUM_05, generated 2026-10-14 11:07, Slurm 1039549): read in full by this agent today
     (2026-10-16 ~23:20–23:40), every level and every PE-* table. Numbers already known that bear on this panel include:
     - PE-GENERIC CS_SINGLE reve, NLL: random_full → pretrained_peft +0.089, → pretrained_full +0.092 (both I>0); the reference
       level is the outlier NLL 0.811 of REVE CS_SINGLE random_full (all other levels 0.714–0.728). CS_SINGLE reve AUC +0.019 /
       +0.026 (I>0). CS_SINGLE cbramod: NLL +0.002 (I>0) / +0.002 (contains 0), AUC +0.022 / +0.022 (I>0). NCE cbramod: NLL +0.000 /
       +0.000, AUC +0.015 (I>0) / +0.006 (contains 0). NCE reve: NLL +0.000 / +0.000, AUC +0.011 / +0.009 (both contain 0).
     - PE-LOCAL CS_SINGLE: every reve member I<0 for NLL and AUC (e.g. AUC random_full −0.046, pretrained_peft −0.026,
       pretrained_full −0.020); cbramod random_full AUC −0.018 I<0, pretrained_peft / pretrained_full +0.004 (contain 0). PE-LOCAL
       NCE AUC: reve random_full −0.013 I<0, the other panel members contain 0. transfer/lag_local_tokens/task_partial vs local:
       NCE AUC +0.005, CS_SINGLE AUC +0.000, NLL about 0, all contain 0 (PE-LOCAL and PE-TRANSFER).
     - Levels: AUC 0.496–0.553 over 132 configurations (E_GX full the highest, 0.553); history increment −0.007 … +0.001 bits.
   - `private_e.json`: the source of that document (same values). This agent has not opened it; the code reads it only for the
     seed-3401 reproduction check.
   - `PRIVATE_RESEARCHER_SUMMARY.md` and `private_age_stage.json` (ADDENDUM_08, seed 3401; group, age, wearing-duration and stage
     associations): not opened by this agent. They were seen by the researcher (publish_025) and by earlier sessions; brief B01
     quotes their summary (145 pointwise interval cells, 1 strictly excluding 0). This analysis does not use them.
   - Brief B01 (`sources/ALN3_BRIEF_20261016.md` L1140–L1300) read today: the family counts I>0 / I<0 / contains 0 (PE-GENERIC
     15 / 1 / 16, PE-LOCAL 1 / 20 / 43, PE-TRANSFER 3 / 1 / 20, PE-COMPLEMENT 0 / 5 / 35, PE-DISTILL 0 / 1 / 47) and the remark that
     7 of the 15 PE-GENERIC I>0 cells have REVE CS_SINGLE random_full as reference.
   - So the question and this design are formed with seed 3401 known.
2. **Panel (3407 / 3413): completion status and record structure only.**
   - Looked at: the `status` field; key names; code hashes and groups; target contract; information stratum; selection rule,
     calibration-set and head-fit descriptors; row specs and folds; registry links; the child set of each record; per-child trial
     counts (`n`, compared between records, not printed); donor ids, donor seeds and checkpoint presence; whether the endpoint
     fields (`positive_affine` NLL / AUC, `hist_gain_bits`, `hist_gain_twin_bits`) are present and non-null.
   - No metric value of any panel record was printed, computed, summarised or plotted.
   - No evidence that anyone else saw panel values: `bc_interim.pcfg_of` and `aln32_private_summary` (through
     `bc_interim.load_private`) filter seed 3401; brief B01 reports no E panel value; `PUBLIC_PRIOR_DESIGN.md` names the E_LOCAL
     panel rows only as a future reference.
3. **Other families.** `D_MULTI_SEED_RESULTS.md` (D panel values) and `D_MULTI_SEED_NOTE.md` were read for format; they are a
   different family and are not used here.

## 与旧分析相比改变了什么 (what changes relative to the old analysis)

- **Unchanged and imported, not re-implemented** (`bc_interim`): the record parsing `load_private` / `child_values`, the family
  definitions `private_families`, `run_family`, `member_values`, `levels`, `aggregate_private` (reproduction), `ckey`, `cls`, `diff`,
  `jl`, `write_json`, `privacy_scan`, `unit_loader`; `sci_r1.stats` (bootstrap-t, B = 4,000; `family_maxt`; `group_seed`).
  - Per seed s the frozen loader is called with `bc_interim.SEED` switched to s for the duration of that call only (the same device
    as `d_multiseed.seed_scope`); its own seed filter then selects exactly that seed's E rows. Every loaded record's row seed is
    checked to equal s.
  - Endpoints, signs, identity values, family labels, replicate seeds `group_seed(label, metric)` and the interval classes are the
    frozen ones.
- **New (all CPU aggregation of completed records):**
  - panel families: each frozen family restricted to its panel members, the same member set for every seed, the frozen labels
    (so the replicate indices are shared across the seeds, the identity mean and the published seed-3401 tables);
  - per-seed results for 3401, 3407 and 3413;
  - identity mean over seeds and its family intervals;
  - between-seed range, spread and SD of the per-seed estimates (ADDENDUM_05 §6 asks for range and SD);
  - levels of the 17 panel configurations per seed and for the identity mean over seeds;
  - descriptive HA / NH columns;
  - coverage and pairing QC;
  - a number-by-number seed-3401 reproduction of the published `private_e.json`;
  - CORRECTION_01 label for `pretrained_full` (recipe contrast).
- **Declared exploratory additions** (decided now, before any panel value; reported whatever they show):
  - A. Simultaneous 95 % intervals for Δ history increment within the same panel families. The frozen analysis gives the history
    increment and the twin sensitivity pointwise intervals only. A uses the frozen secondary label `"<family>|<scope>|sec"` and
    metric `hist_gain`, so its pointwise intervals are identical to the frozen ones and only the max-t is added. The twin
    sensitivity stays pointwise.
  - B. A pointwise bootstrap-t interval for the history-increment **level** of each panel configuration (frozen: estimate only),
    seeded `group_seed("plevels", configuration, "hist_gain")` as the frozen NLL / AUC levels are.
  - C. Between-seed spread against the three per-seed simultaneous widths with one symmetric rule: below every width / between /
    above every width; plus the spread ÷ narrowest and ÷ widest width.
  - D. Monte-Carlo stability of every primary interval class: K = 50 alternative draw sets, set k adds 1000·k to
    `sci_r1.stats.SEED` (k = 1…50); cells: the panel families per seed and for the identity mean, and the full frozen families at
    seed 3401 (panel members only). The declared draws (k = 0) stay the reported result; no draw is chosen by its outcome and there
    is no stability threshold; every cell below 50/50 is listed.
  - E. A determinism re-computation in the same process and the measured peak resident memory.
- **Not added:** no new contrast (in particular no GX-referenced contrast, since no frozen family contains E_GX); no new endpoint;
  no group contrast; no age, wearing-duration or stage analysis; no complete-case variant unless coverage turns out incomplete
  (rule below).

## 配对键、身份与内容汇总 (pairing keys, identity and content aggregation)

- **Within a seed** (package docs/06 key list), reference and candidate share:
  - dataset `private_bdf`; subject fold and content fold (0);
  - split: no split hash is stored, so the fold's child set must be identical between reference and candidate (checked per fold
    and seed) and identical to the seed-3401 counterpart's;
  - target: `current_class`, record target contract `current_class`;
  - evaluation: the calibration set and head-fit descriptors, and the per-child test-trial counts (`n` of the per-participant
    table and of the positive-affine calibration), checked equal between reference and candidate;
  - training seed.
- **Allowed to differ**, the declared independent variable of each frozen family:
  - PE-GENERIC: the adaptation recipe (same backbone, same stratum);
  - PE-LOCAL: model family and input access. E_LOCAL `local_only` (declared query window 0–600 ms) against E_GENERIC
    `padded_private_epoch_no_extra_EEG` (zero-padded −200…600 ms epoch) or E_PUBLIC_TRANSFER `private_task_declared_input`. These
    are access-extended comparisons, named as such, not pure architecture contrasts;
  - PE-TRANSFER: the transferred initialisation (stratum also differs, as above);
  - code group: `private` against `transfer` in PE-LOCAL / PE-TRANSFER transfer members.
- A reference from one seed is never paired with a candidate from another seed.
- **Identity** = the child pseudonym of the record's per-participant table (seed 3401: 64 children, HA 55, NH 9). Every child is
  tested in exactly one subject fold (content fold 0), so per seed and configuration a child's value is the value of its one unit.
  The frozen rule "mean over the identity's units" therefore reduces to that unit, and the frozen loader raises if a child appeared
  twice in a configuration.
  - Per seed: the paired difference Δ(i, s).
  - Identity mean: Δ̄(i) = the mean of Δ(i, s) over the seeds in which that pair exists (with complete coverage this equals the
    difference of the three-seed means, the ADDENDUM_05 §6 identity value).
  - n = number of children. Seeds and folds never add n.
- **Complete-case rule:** if any child lacks a pair in some seed, the identity-mean families are also run on the children that have
  all three seeds. Missing pairs are listed (in the private per-identity file by pseudonym; in the aggregate outputs by count) and
  never filled.
- **Groups** HA / NH from the records' `group` field, checked identical across records and seeds.

## 主要量、辅助量、不确定性处理 (primary and secondary quantities, uncertainty)

### Endpoints (kept separate; never combined)

- **NLL** (co-primary): positive-affine calibrated natural-distribution NLL in bits (lower is better).
  ΔNLL = NLL(reference) − NLL(candidate).
- **AUC** (co-primary): positive-affine `auc_score`, which equals the native ranking. ΔAUC = AUC(candidate) − AUC(reference).
- **History increment** (secondary, frozen): `hist_gain_bits` (q_hist+EEG vs q_hist, bits). Δ = candidate − reference.
- **Twin sensitivity** (secondary, frozen): `hist_gain_bits − hist_gain_twin_bits`. Δ = candidate − reference.
- Positive = candidate better throughout.
- Reading rules carried over: an NLL change with unchanged AUC is a calibration / probability change (ADDENDUM_05 §7, docs/08 §5);
  an AUC above 0.5 does not by itself establish an increment over the declared history (ALN3.4 docs/05 §5); equal summary AUCs of
  two models do not show equal per-trial rankings.

### Families and computation

- Per seed: `bc_interim.run_family` on that seed's child values, label `"<family>|<scope>|<NLL or AUC>"` (frozen), max-t within the
  panel family. In a one-member family (PE-TRANSFER) the simultaneous interval equals the pointwise bootstrap-t interval.
- Identity mean: the same machinery on Δ̄(i), through pseudo-configurations (reference 0, candidate the signed mean, so that
  `bc_interim.diff` returns Δ̄ for both directions), with the same labels. Replicate indices depend only on label, metric and n, so
  the three seeds and the mean resample the same children: whole seed vectors are resampled jointly (ALN3.1 docs/12 §5).
- Secondary (history increment, twin sensitivity): `run_family` with the frozen label `"<family>|<scope>|sec"`, pointwise, per seed
  and for the identity mean; plus addition A for the history increment.
- Levels: `bc_interim.levels` (label `"plevels"`) for the 17 panel configurations per seed, and on the per-child three-seed means;
  NLL and AUC with intervals and HA / NH means as frozen; the history increment with addition B.
- Between seeds: per-seed estimates, min, max, spread (max − min), SD (ddof = 1) and the interval classes.
- At seed 3401 the published full-family simultaneous interval of each panel member is shown next to its panel-family interval.
- **Group columns** (HA, NH): per member, pointwise bootstrap-t within the group (`run_family` groups, `MIN_N` = 5), per seed and
  identity mean; descriptive only, never a group contrast, never used to choose anything. NH n = 9.

### Uncertainty

- Every interval is conditional on the fitted models. No p-values. "I>0 / I<0 / contains 0" describes a simultaneous interval of
  the declared draws.
- Three seeds are a coarse sample of the training randomness. Here that randomness includes: initialisation and batch order
  (`torch.manual_seed(seed)`, `default_rng(seed)`); the training-side target statistics and calibration batches (`seed + 5`,
  `seed + 98`, `seed + 99`); for E_GENERIC the head and adaptation (the pretrained checkpoints are the same in every seed; only
  `random_full` re-draws the backbone); for E_PUBLIC_TRANSFER the donor (donor seed = target seed). The early-stopping blocks
  (`default_rng(12345)`) and the fold assignment do not change with the seed.
- The same 64 children and the same contents are reused in every seed, so agreement across seeds is not an independent replication.

## 探索性/原计划/勘误的身份 (exploratory, planned or erratum)

- **Planned.** ADDENDUM_05 §6 (frozen 2026-10-14, before any E value was seen) registers this seed-panel supplement: contrasts,
  families and endpoints unchanged; the identity value is the mean over the three seeds once every unit of both reference and
  candidate is complete (true here); each table lists the per-seed estimates, the mean, the range and the SD; contrasts without a
  complete common seed set report the seed-3401 value and the missing status; no per-method best seed; the per-seed loop is
  registered with its sha256 in a short note before it runs. This note is that short note; the sha256 of the code is appended in
  the section "Code registration" below before the first real-data run.
- **Deviation from the literal §6 wording, declared now:** the families are restricted to their panel members. Non-panel members
  have no seed-3407/3413 records, so a family at those seeds can only hold panel members, and the same restricted member set is used
  at 3401 and for the identity mean. The published full-family seed-3401 intervals are shown alongside; the non-panel members keep
  their published seed-3401 values with the status "no seed panel". This is the convention of `d_multiseed`.
- Additions A–E: exploratory.
- CORRECTION_01 relabelling of `pretrained_full`: an existing correction of record, applied to the labels only.
- Not blind and not independent: seed 3401 was known, and the panel reuses the same children.

## 可复用产物与实际需要的新计算 (reuse and new computation)

- Reused: the 170 panel records, their 85 seed-3401 counterparts, and for the reproduction check the other 395 seed-3401 E records
  (480 seed-3401 E records in all).
- No training, no GPU job, no new evaluation, no queue or hold change.
- New: CPU aggregation only, inside the session allocation (Slurm 1039458), `nice -n 10`, the eeg2025 interpreter with `-B`,
  under 3 GB RAM.

## 输出文件 (outputs)

- Code: `auditory_alignment_v3/aln34/e_multiseed.py`.
- Synthetic tests: `tests/auditory_alignment_v3/aln34/test_e_multiseed.py`.
- `results/auditory_alignment_v3/aln34/e_multiseed/e_multiseed.json` (0600; aggregates only, no child pseudonym, passes the frozen
  privacy scan).
- `docs/auditory_alignment_v3/E_MULTI_SEED_RESULTS.md` (0600; `templates/EXPERIMENT_UPDATE.md`; states the seed scope, the child
  counts, and that non-panel E configurations keep seed-3401-only statements).
- `private/auditory_alignment_v3/aln34/e_multiseed/per_identity.json` (0600): per child pseudonym, group and trial counts; per seed
  and panel configuration NLL, AUC, history increment and twin sensitivity; per contrast the within-seed paired differences and
  the identity mean; any missing pair. Within the confirmed individual-level scope; no name, no identity map.

## Not in the panel (seed-3401-only statements)

- PE-GENERIC members `pretrained_frozen` and `pretrained_partial`;
- PE-LOCAL members `generic/*/pretrained_frozen`, `generic/*/pretrained_partial`, `transfer/lag_local_tokens/task_full`,
  `transfer/cbramod/*` and `transfer/reve/*`;
- PE-TRANSFER: the other 5 members;
- PE-COMPLEMENT and PE-DISTILL (whole families);
- the levels of every non-panel configuration (E_LOCAL density_tokens / legacy_pool4 and the early / late / joint windows, E_GX
  early / late / joint, E_GENERIC pretrained_frozen / pretrained_partial, E_PUBLIC_TRANSFER task_full and the cbramod / reve
  sources, E_COMPLEMENT, E_DISTILL);
- the ADDENDUM_08 group / age / stage associations and the SCI_R1 private results.

## Reporting rules

- Every member is reported whatever its direction; I<0 and contains-0 cells appear in the same tables as I>0. No count-only summary.
- No member, seed or child is dropped because of its result. Missing pairs are listed.
- Per-child values only in the private per-identity file.

## Code registration (appended 2026-10-17 00:07 CEST, before the first real-data run; ADDENDUM_05 §6)

Nothing above was changed. No panel value had been read or computed when this section was appended: the code had run only on the
synthetic design of the tests.

- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `f6ce4809d71372dbebe8e527ce507d7f467d2b7e2562fcb9b2de804ec06c19e4`
- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `d85eb264431c956d06eb84a8b341e6824330ea52d5dfd422b17e66c54d1348cd`
  (15/15 passed; together with the frozen `tests/auditory_alignment_v3/test_bc_interim.py` 20/20, 2026-10-17 00:06 CEST)
- imported unchanged: `bc_interim.py` `2840df81…`, `sci_r1/stats.py` `8bb141cf…`
- Run: `python -B -m auditory_alignment_v3.aln34.e_multiseed --update-doc` (MC_K = 50), eeg2025 interpreter, `nice -n 10`, inside the
  session allocation 1039458. The generator records whether the sha256 it runs with is one registered here.

### Code registration, second entry (appended 2026-10-17 00:09 CEST, still before the first real-data run)

The registered version above was never run on real records. On self-review its provenance helper `registered_shas` would also have
picked up the test file's sha256 (`test_e_multiseed.py` contains the string `e_multiseed.py`). Fixed with a word-boundary guard, and
the test now checks that case. No statistic, family, endpoint or output changed. This is the version used for the first real-data run:

- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `66b36d8b71a558d4e9bee8f0fc17dbc8ab83572ad8d579ecb7317330b04e23ae`
- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `0bea3f31d32432e6ee3c9dd88910b9afb7d9f89ba9d37fb4dd19ffa6a3d44435` (15/15 passed)

## 补充 (addendum) — post hoc addition F, written 2026-10-17 00:13 CEST, after version 1 was generated and read, before F was computed

Appended, not rewritten. Nothing above changes.

### 写本节时已见哪些结果 (what had been seen when this section was written)

- **Everything in version 1** (generated 2026-10-17 00:11 CEST by `e_multiseed.py` `66b36d8b…`; archived unchanged with its JSON,
  per-identity file, code, tests, this note as of 00:09 and the run log in `private/auditory_alignment_v3/aln34/e_multiseed/v1_20261017T0011/`,
  `SHA256SUMS`). That is every per-seed and identity-mean value, range, SD, class, level, group column, coverage and QC entry, the
  spread-versus-width table and the Monte-Carlo table. Version 1 had no hand-written sections yet.
- The observation that prompted F: the calibrated-NLL levels of the REVE CS_SINGLE configurations change strongly between seeds
  (random_full 0.811 / 0.723 / 0.736; pretrained_peft 0.722 / 0.911 / 0.927; pretrained_full 0.719 / 0.732 / 0.720 at 3401 / 3407 / 3413),
  while every other panel configuration stays within 0.714–0.718 and the REVE CS_SINGLE AUC levels stay at 0.50–0.53. The five REVE
  CS_SINGLE NLL members of PE-GENERIC / PE-LOCAL are the only members whose between-seed spread exceeds every per-seed simultaneous width.
- So F is a result-informed exploratory description, not a blind analysis. It is reported whatever it shows.

### F. Unit-level description (exploratory, descriptive only)

- Unit = one trained record: configuration × seed × subject fold, with its 12–13 test children.
- For **every** one of the 255 panel units (all 17 configurations, all seeds and folds, not only the REVE CS_SINGLE ones): the number of
  test children and the mean over them of calibrated NLL, AUC and history increment (the per-child values of version 1), plus the
  unit's positive-affine calibrator parameters (slope, intercept), which were fitted on the training side (training children's
  early-stopping blocks) and are stored in the record.
- Question: is a configuration's between-seed NLL spread spread over all five units of a seed, or concentrated in some units?
- No interval (13 children per unit), no new contrast, no threshold, no unit dropped; the main tables, families, endpoints and draws
  stay exactly as in version 1. Calibrator slopes are compared only within a configuration (the native score scales differ between
  architectures and objectives).
- Output: a new JSON block `unit_levels` and a new document subsection; per-unit child values stay in the private per-identity file.
- Version 2 also compares every version-1 number with the archive (expected: unchanged, F added).

### Code registration, third entry (appended 2026-10-17 00:16 CEST, before the version-2 run; F not yet computed on real records)

Adds addition F (`unit_levels`, `unit_table`, the calibrator fields of the census) and the number-by-number comparison with the
version-1 archive. No other statistic, family or endpoint changed.

- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `fc83e8d647ebcaa0bf05aea400d44071365a548759152dd752c3a823f124dd20`
- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `ef99fd9b21602015a536042b28f880eff0ad97ec568c50dbb13b481db2993d54` (16/16 passed)

## 更正 01 (correction 01) — written 2026-10-17 00:50–00:56 CEST (first saved 00:56:04), after version 2 and an independent verification of it, before version 3

Appended; nothing above is changed. Versions 1 and 2 are archived unchanged in `private/auditory_alignment_v3/aln34/e_multiseed/v1_20261017T0011/`
and `v2_20261017T0018/` (each with `SHA256SUMS`; the version-2 archive holds this note as of 00:16:33, sha256 `0100c065…`, the version-2 code,
tests, JSON, per-identity file and results document).

### 写本节时已见哪些结果 (what had been seen when this section was written)

- Everything in versions 1 and 2: every panel value, the §1.15 unit table and the hand-written sections 2–4, 6 and 7 of version 2.
- A verification report on version 2 (2026-10-17, independent re-implementation, passed on by the workflow). It found every computed
  number equal, five errors in the text of the results document, and made two remarks on the rules. It quotes numbers that version 2
  does not print: the unit NLL excess over the median of the 14 stable configurations in the same seed and fold (random_full 3401
  +0.081 … +0.111 in every fold; pretrained_peft 3407 +0.133 … +0.266 and 3413 +0.151 … +0.239; random_full 3413 +0.058 / +0.001 /
  +0.008 / +0.024 / +0.004; pretrained_full 3407 +0.039 / +0.012 / +0.005 / +0.016 / +0.004; random_full 3407 +0.002 … +0.009; the
  stable configurations −0.005 … +0.003), and the seed-3401 critical values of the panel families and of the full frozen families.
- Read by this agent while checking the report, before this section (descriptors, code and already-generated values; nothing new
  computed from per-child values):
  - `resolved_config`, `backbone_contract`, `lr_backbone` / `lr_head` and the curve keys of the 180 E_GENERIC panel and counterpart
    records; `resolved_config` and curve keys of the 60 E_LOCAL / E_PUBLIC_TRANSFER panel records; the record keys of E_GX;
  - the 20 private recipe files `private/auditory_alignment_v2/fm_recipe/*__private_bdf__*.json` (`chosen`, `dev_cell`, the candidate
    grid with its 20-epoch selection scores) and `fm_recipe/epochs.json`;
  - code: `run_private.fm_recipe` / `run`, `local_train.fit_private_fm`, `auditory_alignment_v2.train_fm.param_groups`, the docstring and
    `lr_select` of `auditory_alignment_v2.run_fm` (and, by mistake first, `fm_ext.lr_select`, which writes `fm_recipe_ext`, not used here);
  - `docs/auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md`;
  - from the version-2 JSON: the critical values per family and seed, the PE-GENERIC per-seed estimates and classes, `meta.v1_comparison`;
    file times (`stat`).

### What was wrong in version 2 and what changes

Text only: no statistic, family, endpoint, draw or child set changes. Version 3 compares every number with versions 1 and 2.

1. **Recipe description (results §1 'Contrasts', §2 item 2, §3).** Version 2 described `random_full → pretrained_full` as "a 30× lower
   backbone learning rate and the progressive-prefix schedule". That is CORRECTION_01's description of `fm_dense` (public tasks); its item 3
   says the private E_GENERIC recipes inherit it, and version 2 repeated it without checking the private records. The records show:
   - learning rates per architecture × adaptation × objective from the ALN2 recipe search (`auditory_alignment_v2.run_fm.lr_select`:
     candidates trained on one development cell, subject fold 0 / content fold 0 / seed 3401, 20 epochs, scored by the checkpoint-selection
     score on the training participants' early-stopping content; the chosen pair is fixed for every fold and seed). Backbone lr
     random_full → pretrained_full: NCE cbramod 3e-4 → 1e-4 (3×), NCE reve 3e-4 → 3e-5 (10×), CS_SINGLE cbramod 1e-4 → 1e-5 (10×),
     CS_SINGLE reve 1e-3 → 1e-5 (100×); head lr 3e-4 → 1e-4, 3e-4 → 1e-4, 1e-4 → 1e-3, 1e-3 → 1e-3. pretrained_peft (LoRA r8 on all
     attention projections; 76,800 trainable backbone parameters for CBraMod, 540,672 for REVE): adapter / head lr 1e-3 / 1e-3, 1e-3 / 1e-4,
     3e-4 / 1e-3, 3e-4 / 1e-4 in the same order;
   - the same epochs for the three recipes within a backbone (CBraMod 100, REVE 50);
   - pretrained_full (like random_full) trains every backbone parameter from the start: `n_trainable_backbone` = `n_params` (4,883,800 and
     69,189,632), no curve carries `open_groups`, and `fit_private_fm` builds one backbone lr group (AdamW, weight decay 1e-4, cosine
     annealing over all steps): no progressive prefix and no layer-wise decay.
   - These are still recipe contrasts (initialisation together with a configuration-specific learning-rate cell), not a pure
     initialisation effect. The ratio and the schedule stated in version 2 were wrong for the private task.
   - CORRECTION_01 item 3 is contradicted by these records for E_GENERIC (and, for the panel's E_PUBLIC_TRANSFER `lag_local_tokens`
     configurations, the records show AdamW lr 1e-3 for 200 epochs, the same as their E_LOCAL twin). CORRECTION_01 lies outside this
     analysis' write scope and is not edited; the discrepancy is reported in results §6 and §7.
   - Version 3 adds a generated table of these descriptors, read from every panel record (results §1.16, with a check that each record's
     learning rates equal the `chosen` pair of its recipe file); the 'Contrasts' bullet refers to it.
2. **Unit-level claim (results §2 item 1, §3 (b)).** "a high NLL affects all five units of the seed concerned" and "In each affected seed all
   five units fail together" hold for the three large failures (random_full 3401, pretrained_peft 3407 and 3413), not for the moderately
   raised REVE CS_SINGLE seed cells (random_full 3407 and 3413, pretrained_full 3407). Corrected with addition G below.
3. **Cross-reference.** "§1.11 shows their Monte-Carlo stability": the Monte-Carlo table is §1.14 (§1.11 is Coverage). The reference was
   hard-coded in the generator, also in version 1. Version 3 takes the number from the section order.
4. **"0 added fields (unit_levels)".** It meant: 0 fields added inside the compared version-1 blocks, and one new top-level block
   (`unit_levels`). Version 3 says that in words and compares with both archives.
5. **Seed-3401 reproduction sentence (results §2 item 2).** "The AUC directions and the CS cbramod NLL cells do [reproduce]": for the CS
   cbramod NLL cells only the direction reproduces (all six per-seed estimates positive); the per-seed classes do not, and only the
   identity-mean classes agree. The AUC part is also made exact: the five PE-GENERIC AUC cells that are I>0 in the published seed-3401
   tables keep a positive estimate in both other seeds, but 23, not 24, of the 24 per-seed PE-GENERIC AUC estimates are positive (NCE cbramod
   pretrained_full at 3407 is −0.001).
6. **Rule remarks.**
   - (a) Restricting the frozen families to their panel members (declared above, before any panel value) lowers the seed-3401 critical values:
     PE-GENERIC 2.13–2.32 against 2.25–2.58 in the full frozen families, PE-LOCAL 2.72–2.83 against 3.00–3.12, PE-TRANSFER 2.00–2.04
     against 2.67–2.72. The PE-TRANSFER panel families have one member, so they carry no multiplicity control. Version 3 prints these ranges
     in results §1.12 and says that both seed-3401 class changes go in the favourable direction; results §2 item 2 gives the PEFT AUC count with
     the panel-family class at 3401 (8 of 12 I>0) and with the published class (7 of 12).
   - (b) The writing time of the main body (23:45–23:53) is the previous author's statement; the file system keeps no birth time, so it cannot
     be checked. What can be checked: the copy in the version-1 archive (mtime 00:09:49) predates the first result files (per-identity file
     00:11:23, JSON 00:11:24); the version-2 note is that copy with the later sections appended (byte prefix); its mtime 00:16:33 predates the
     version-2 outputs (00:18:05, 00:18:08). This section was written after all of those.

### Post hoc addition G (exploratory, descriptive; declared here, before it is computed)

- Prompted by item 2 of the verification; result-informed: the three E_GENERIC CS_SINGLE reve configurations were singled out in version 2 by
  their between-seed NLL spread.
- Reference set: the 14 panel configurations other than E_GENERIC CS_SINGLE reve random_full / pretrained_peft / pretrained_full. For each
  seed × subject fold, the median of the 14 reference unit NLLs (the addition-F unit means).
- Per unit (all 255): NLL excess = unit NLL − that median (bits per trial). Reported for every unit; with the range of the excess over the 210
  reference units and, per configuration and seed, the number of its five units whose excess lies above the largest reference excess.
- Descriptive only: no interval, nothing decided by it, no unit dropped; the main tables, families, endpoints and draws stay unchanged.

### Version 3 (planned)

- Generator: the recipe-descriptor table (results §1.16; JSON block `recipes`), addition G (a §1.15 column and summary; JSON block
  `unit_nll_excess`), the cross-reference taken from the section order, the comparison wording, the comparison with both archives (expected:
  every version-1 and version-2 number unchanged, new top-level blocks `recipes` and `unit_nll_excess`, per-identity file unchanged), the
  seed-3401 critical-value ranges in results §1.12. Nothing else.
- Results document: the hand-written sections corrected as listed (after version 3 is generated); §7 records each correction with the
  version-2 wording.

### Code registration, fourth entry (appended 2026-10-17 01:07 CEST, before the version-3 run; G not yet computed on real records)

Implements exactly the version-3 changes listed in correction 01 (recipe descriptors and their check against the recipe files, addition G,
the seed-3401 critical-value ranges, the section-order cross-reference, the comparison wording and the comparison with both archives). No
statistic, family, endpoint or draw changed. The code had run only on the synthetic design of the tests.

- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `1a94eb22cef1b4aa81d0cac650e8273e0b51854787b1f3afbfc20277df217efb`
- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `ccea31b31504bc54a5a1a3fc74372d385b6b3eacef112f26fb93eacb3174cdc7` (22/22 passed;
  run together with the frozen `tests/auditory_alignment_v3/test_bc_interim.py`, 5 tests, 27/27; 2026-10-17 01:06 CEST)
- imported unchanged: `bc_interim.py` `2840df81…`, `sci_r1/stats.py` `8bb141cf…`
- Run: `python -B -m auditory_alignment_v3.aln34.e_multiseed --update-doc` (MC_K = 50), eeg2025 interpreter, `nice -n 10`, in this session's
  CPU allocation. The results document's hand-written sections are corrected after the run; this note is not edited after the run.

### Code registration, fifth entry (appended 2026-10-17 01:12 CEST, after the first version-3 run, before its re-run)

The first version-3 run (01:09, code `1a94eb22…`) completed: every version-1 and version-2 number unchanged, privacy scan PASS. Its outputs were
viewed (all generated sections, including the new §1.12 critical-value paragraph, the addition-G table of §1.15 and the recipe table of §1.16)
and are archived unchanged in `private/auditory_alignment_v3/aln34/e_multiseed/v3_first_run_20261017T0109/` (`SHA256SUMS`, with its run log).
Two generated phrases were made exact before any hand-written section was edited: the code-registration phrase now reads "registered in the
note before the first real-data run of this code version" (the earlier wording could be read as "before version 1"), and the §1.15 heading
says which addition was declared after which version. The re-run is also compared number by number with the first version-3 run. No
statistic, family, endpoint, draw or child set changed; the tests are unchanged.

- `auditory_alignment_v3/aln34/e_multiseed.py` sha256 `9111d628f9b1201d0573e8fcc0220fd1dad6a8fe321e2db49260f3880e865e92`
- `tests/auditory_alignment_v3/aln34/test_e_multiseed.py` sha256 `ccea31b31504bc54a5a1a3fc74372d385b6b3eacef112f26fb93eacb3174cdc7` (22/22 passed; with
  the frozen `test_bc_interim.py` 27/27; 01:11 CEST)
- Run as in the fourth entry. This note is not edited after the run.

## Edit 2026-10-17 01:55 (lead agent)

After the second verification, three hand-written sentences in §2 were corrected (no number changed): the transfer reading now states that 11 of 12 per-seed cells contain 0 and CS NLL at 3407 is I<0 (−0.0012 [−0.0020, −0.0004]); the CS·REVE NLL non-reproduction now gives each arm and seed (pretrained_peft I<0 at 3407 and 3413; pretrained_full I<0 at 3407, I>0 at 3413); a cross-reference was disambiguated. Backup of the previous doc: e_multiseed/E_MULTI_SEED_RESULTS.before_wording_20261017.md.
