# Public auditory prior: E34_PUBLIC_PRIOR results (aln33_env64_125ms_v1)

Generated 2026-10-18 13:33 CEST (Slurm 1045980) by `python -m auditory_alignment_v3.prior33.analysis` under `PUBLIC_PRIOR_DESIGN.md` §5, frozen with the execution record. Units read: 1184 (1184 complete; 0 excluded by the engineering checks of §2). Code sha256: `auditory_alignment_v3/prior33/analysis.py` 221405c791be, `tests/auditory_alignment_v3/prior33/test_analysis.py` e4c4d88f616e, `auditory_alignment_v3/prior33/select.py` 09a43fe60618, `auditory_alignment_v3/prior33/contract.py` 683116992626, `auditory_alignment_v3/sci_r1/stats.py` 8bb141cf6070, `auditory_alignment/aggregate.py` bd6198da958a. Manifest sha256 seen: `b751976b92385900`. Frozen check: PASS. Privacy scan: PASS (no private child id and no child-id pattern in the public outputs).

Execution versions (derived from the donor-group rows, §2.10): `primary` (26 donor groups; units bridge 68, donor_group 26, target 540, zero_shot 520; compute limits [60]).

**Reading the tables.**

- Every contrast is a within-identity paired difference on matched cells, written so that positive = the candidate is better: for risks (log-losses, NLL, rank percentile) Δ = R(reference) − R(candidate); for AUC, accuracies, top-1, gains and kernel_cs_diff Δ = candidate − reference. Each endpoint carries its direction (ref − cand or cand − ref).
- R = `unified/regular/logloss_bits`, the candidate cross-entropy (bits per 5-s query) of the true test segment among all test candidates under the unified readout (mode T: training-side ridge and temperature; zero-shot: the frozen donor bridge and τ(n)). Private task: positive-affine calibrated natural-distribution NLL (bits, primary) and AUC (co-primary).
- Each test identity counts once: seeds, folds, content folds, cells and repeated zero-shot evaluations never add to n. One donor member model serves every cell of its target; it is a fixed upstream, so its cells are not independent samples, and every interval conditions on the fitted donors and targets (bootstrap_scope: conditional_on_available_fitted_models_not_full_training_population).
- Intervals: bootstrap-t over identities (B = 4,000; sci_r1.stats unchanged), percentile intervals as the secondary column. Pointwise intervals (n) are on each member's own paired identities. Families (cohort × objective × mode × seed × version) carry simultaneous 95 % intervals by max-t over the members that have pairs, sharing the replicate indices, on the identities common to them (family n, printed with the members in the max-t); secondary endpoints, the B_uni_cal sensitivity, ACCESS, SELECTION, levels and the native reference are pointwise.
- An identity bootstrap does not contain the training randomness, and 3 seeds do not estimate the seed distribution precisely.
- Tables outside the panel are seed 3401 only. Donor and target seeds are recorded separately (d = donor_seed, t = target_seed; S has no donor, zero-shot rows have no target seed).
- Zero-shot access modes A (primary), B, C and C-partial are separate configurations and are never pooled; mode T and zero-shot values are never contrasted with each other. Selection levels are declared per configuration: mode T = training identities with held-out early-stopping content (not new listeners); private = training children, last 20 % of blocks; zero-shot = the donor-dev selection (new listeners, new content).
- Execution versions are derived from the donor-group rows: `primary`, or `continuation_k` for a registered continuation (§2.10), reported as its own version; S rows are never re-registered, so INIT at a continuation version uses the primary S rows.
- Missing units (a plan row without a complete record) and unregistered sides (no plan row) are listed separately, with their status, and identities enter on their remaining units; nothing is zero-filled. A mismatched cell pair, and a unit failing the pool or member check, is excluded with its reason.
- No p-values are computed or reported, and there is no per-identity best-method baseline. Effects are shown with their size and scope; cells are not counted by interval sign.
- Endpoint directions (Δ): R ref − cand, gain cand − ref, R_mm ref − cand, top1 cand − ref, rank_pct ref − cand, hard_gain cand − ref, R_native ref − cand, att_acc cand − ref, kernel_cs_diff cand − ref, NLL ref − cand, AUC cand − ref, hist_gain cand − ref, twin_sens cand − ref.

## 1. Coverage

| stage | block | cohort | version | registered | complete | technical_failed | missing | other | excluded |
|---|---|---|---|---|---|---|---|---|---|
| bridge | core | dtu | primary | 8 | 8 | 0 | 0 | 0 | 0 |
| bridge | core | fau | primary | 8 | 8 | 0 | 0 | 0 | 0 |
| bridge | core | federici | primary | 8 | 8 | 0 | 0 | 0 | 0 |
| bridge | core | private_bdf | primary | 8 | 8 | 0 | 0 | 0 | 0 |
| bridge | csx | dtu | primary | 4 | 4 | 0 | 0 | 0 | 0 |
| bridge | csx | federici | primary | 4 | 4 | 0 | 0 | 0 | 0 |
| bridge | csx | private_bdf | primary | 4 | 4 | 0 | 0 | 0 | 0 |
| bridge | panel | private_bdf | primary | 16 | 16 | 0 | 0 | 0 | 0 |
| bridge | rich | dtu | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| bridge | rich | fau | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| bridge | rich | federici | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| bridge | rich | private_bdf | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | core | dtu | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | core | fau | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | core | federici | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | core | private_bdf | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | csx | dtu | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | csx | federici | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | csx | private_bdf | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | panel | private_bdf | primary | 4 | 4 | 0 | 0 | 0 | 0 |
| donor_group | rich | dtu | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | rich | fau | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | rich | federici | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| donor_group | rich | private_bdf | primary | 2 | 2 | 0 | 0 | 0 | 0 |
| reference | aln3_native | private_bdf | aln3_native | 30 | 30 | 0 | 0 | 0 | 0 |
| target | core | dtu | primary | 100 | 100 | 0 | 0 | 0 | 0 |
| target | core | fau | primary | 100 | 100 | 0 | 0 | 0 | 0 |
| target | core | federici | primary | 50 | 50 | 0 | 0 | 0 | 0 |
| target | core | private_bdf | primary | 50 | 50 | 0 | 0 | 0 | 0 |
| target | csx | dtu | primary | 40 | 40 | 0 | 0 | 0 | 0 |
| target | csx | federici | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| target | csx | private_bdf | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| target | panel | private_bdf | primary | 100 | 100 | 0 | 0 | 0 | 0 |
| target | rich | dtu | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| target | rich | fau | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| target | rich | federici | primary | 10 | 10 | 0 | 0 | 0 | 0 |
| target | rich | private_bdf | primary | 10 | 10 | 0 | 0 | 0 | 0 |
| zero_shot | access | dtu | primary | 60 | 60 | 0 | 0 | 0 | 0 |
| zero_shot | access | fau | primary | 120 | 120 | 0 | 0 | 0 | 0 |
| zero_shot | access | federici | primary | 30 | 30 | 0 | 0 | 0 | 0 |
| zero_shot | core | dtu | primary | 80 | 80 | 0 | 0 | 0 | 0 |
| zero_shot | core | fau | primary | 80 | 80 | 0 | 0 | 0 | 0 |
| zero_shot | core | federici | primary | 40 | 40 | 0 | 0 | 0 | 0 |
| zero_shot | csx | dtu | primary | 40 | 40 | 0 | 0 | 0 | 0 |
| zero_shot | csx | federici | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| zero_shot | rich | dtu | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| zero_shot | rich | fau | primary | 20 | 20 | 0 | 0 | 0 | 0 |
| zero_shot | rich | federici | primary | 10 | 10 | 0 | 0 | 0 | 0 |

Registered rows of the primary version against the §4.1 design counts (access: a maximum, mode-C rows only where the manifest supports them):

| block | stage | registered | design |
|---|---|---|---|
| core | donor_group | 8 | 8 |
| core | bridge | 32 | 32 |
| core | target | 300 | 300 |
| core | zero_shot | 200 | 200 |
| access | zero_shot | 210 | ≤ 210 |
| panel | donor_group | 4 | 4 |
| panel | bridge | 16 | 16 |
| panel | target | 100 | 100 |
| rich | donor_group | 8 | 8 |
| rich | bridge | 8 | 8 |
| rich | zero_shot | 50 | 50 |
| rich | target | 60 | 60 |
| csx | donor_group | 6 | 6 |
| csx | bridge | 12 | 12 |
| csx | zero_shot | 60 | 60 |
| csx | target | 80 | 80 |

Units not complete: 0 (each listed in the JSON, `coverage.not_complete`). Identities per configuration (primary evaluation; appendix B), against the §5.2 test identities: dtu 44–44 of 44; fau 67–67 of 67; federici 86–86 of 86; private_bdf 64–64 of 64.

Phantom entities excluded from every summary: federici 1 (record evaluations 1620). FAU always-train TH ids found among test participants (excluded): 0. Non-finite values excluded: 0 (listed in the JSON, `coverage.nonfinite_excluded`).

Selection levels declared (§1 item 8, §2.10, §2.12): donor_group: 'donor dev: SparrKULee participants and content families disjoint from donor fit (new listeners, new content)'; target: 'training identities, held-out early-stopping content (not new listeners)'; target_private: 'training children, last 20 % of each child's physical blocks'; zero_shot: 'donor dev (the donor checkpoint and the joint λ are chosen on donor dev; no target-side selection)'. Recorded by the complete units:

- L1 = 'donor dev (the donor checkpoint and the joint λ are chosen on donor dev; no target-side selection)': 520 units (zero_shot 520; as declared 520)
- L2 = 'donor dev: SparrKULee participants and content families disjoint from donor fit (new listeners, new content)': 26 units (donor_group 26; as declared 26)
- L3 = 'donor dev: the slot's donor checkpoint is its min CE_dev _best.pt (J* by the lambda rule on donor dev); the bridge alpha and tau(n) come from donor bridge_cal (SparrKULee participants and content disjoint from donor fit and dev); no target data': 68 units (bridge 68; no declared level 68)
- L4 = 'training children, last 20 % of each child's physical blocks': 180 units (target 180; as declared 180)
- L5 = 'training identities, held-out early-stopping content (not new listeners)': 360 units (target 360; as declared 360)

Selection-level status of the complete units: as declared 1086, no declared level 98. Sensitivity evaluations: gainsel evaluated 433, identical 107; uni_cal evaluated 520 (per configuration in appendix A).

## 2. Engineering checks of the analysis (§5.8)

- Cell pairs excluded (pairing-key mismatch or an excluded unit): 0; with a missing or incomplete side (a plan row without a complete record or evaluation): 0, of which 0 lack the B_uni_cal sensitivity evaluation; with an unregistered side (no plan row): 0. All three lists are in the JSON (`pairing`).
- Pools (§2.13; reference: the cell's complete mode-T units (they must agree with each other)): 30 cells checked, 25 with mode-T and zero-shot units; zero-shot units verified 520 of 520, excluded 0, unverified (no complete mode-T unit in the cell) 0; cells whose mode-T units disagree: 0.
- Members (select.member_of; J* by the λ rule on the donor-group record): agrees 1048.
- Units excluded from every family and summary: 0.


## 3. Core block (seed 3401 only)

### core · fau · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 67 | +0.005 [-0.025, +0.035] | [-0.025, +0.032] | 67 | +0.005 [-0.032, +0.042] contains 0 | – | 10 cell pairs, 67 identities paired |
| INIT · NCE · T | S → XP | 67 | +0.011 [-0.006, +0.027] | [-0.005, +0.027] | 67 | +0.011 [-0.010, +0.032] contains 0 | – | 10 cell pairs, 67 identities paired |
| INIT · NCE · T | S → J* | 67 | +0.007 [-0.017, +0.031] | [-0.017, +0.030] | 67 | +0.007 [-0.023, +0.037] contains 0 | – | 10 cell pairs, 67 identities paired |
| INIT · NCE · T | S → XM | 67 | +0.010 [-0.006, +0.026] | [-0.006, +0.025] | 67 | +0.010 [-0.010, +0.030] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · T | AP → XP | 67 | +0.006 [-0.028, +0.039] | [-0.022, +0.038] | 67 | +0.006 [-0.034, +0.046] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · T | AP → J* | 67 | +0.002 [-0.013, +0.018] | [-0.013, +0.017] | 67 | +0.002 [-0.017, +0.021] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · T | XP → J* | 67 | -0.004 [-0.033, +0.025] | [-0.033, +0.021] | 67 | -0.004 [-0.040, +0.032] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · A | AP → XP | 67 | +0.169 [+0.127, +0.212] | [+0.128, +0.211] | 67 | +0.169 [+0.118, +0.220] above 0 | +0.112 [+0.083, +0.140] (n 67) | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · A | AP → J* | 67 | +0.005 [-0.015, +0.024] | [-0.014, +0.023] | 67 | +0.005 [-0.018, +0.027] contains 0 | -0.011 [-0.023, +0.001] (n 67) | 10 cell pairs, 67 identities paired |
| SUPERVISION · NCE · A | XP → J* | 67 | -0.165 [-0.208, -0.122] | [-0.206, -0.123] | 67 | -0.165 [-0.216, -0.114] below 0 | -0.123 [-0.154, -0.092] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · T | XM → AP | 67 | -0.005 [-0.027, +0.018] | [-0.027, +0.017] | 67 | -0.005 [-0.033, +0.023] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · T | XM → XP | 67 | +0.001 [-0.019, +0.021] | [-0.015, +0.019] | 67 | +0.001 [-0.022, +0.024] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · T | XM → J* | 67 | -0.003 [-0.023, +0.018] | [-0.023, +0.017] | 67 | -0.003 [-0.028, +0.023] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · A | XM → AP | 67 | -0.132 [-0.173, -0.090] | [-0.171, -0.091] | 67 | -0.132 [-0.180, -0.083] below 0 | -0.125 [-0.159, -0.091] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · A | XM → XP | 67 | +0.038 [+0.012, +0.064] | [+0.013, +0.062] | 67 | +0.038 [+0.008, +0.068] above 0 | -0.013 [-0.023, -0.003] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · NCE · A | XM → J* | 67 | -0.127 [-0.170, -0.084] | [-0.170, -0.086] | 67 | -0.127 [-0.178, -0.076] below 0 | -0.136 [-0.174, -0.098] (n 67) | 10 cell pairs, 67 identities paired |

- INIT · NCE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 67, crit 2.53.
- SUPERVISION · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 67, crit 2.48.
- SUPERVISION · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 67, crit 2.35.
- CONTROL · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 67, crit 2.52.
- CONTROL · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 67, crit 2.34.

Selection levels (unit records; codes in §1): mode T: L5 ×50 (as declared 50); mode A: L1 ×40 (as declared 40).

### core · fau · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · CS_SINGLE · T | S → AP | 67 | -0.005 [-0.022, +0.012] | [-0.022, +0.011] | 67 | -0.005 [-0.030, +0.019] contains 0 | – | 10 cell pairs, 67 identities paired |
| INIT · CS_SINGLE · T | S → XP | 67 | -0.015 [-0.044, +0.014] | [-0.034, +0.010] | 67 | -0.015 [-0.048, +0.018] contains 0 | – | 10 cell pairs, 67 identities paired |
| INIT · CS_SINGLE · T | S → J* | 67 | -0.030 [-0.045, -0.016] | [-0.045, -0.017] | 67 | -0.030 [-0.051, -0.010] below 0 | – | 10 cell pairs, 67 identities paired |
| INIT · CS_SINGLE · T | S → XM | 67 | -0.009 [-0.038, +0.020] | [-0.031, +0.017] | 67 | -0.009 [-0.044, +0.026] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 67 | -0.010 [-0.034, +0.014] | [-0.031, +0.013] | 67 | -0.010 [-0.039, +0.019] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 67 | -0.025 [-0.041, -0.009] | [-0.040, -0.009] | 67 | -0.025 [-0.046, -0.004] below 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 67 | -0.015 [-0.037, +0.007] | [-0.036, +0.002] | 67 | -0.015 [-0.041, +0.011] contains 0 | – | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → XP | 67 | -0.000 [-0.026, +0.025] | [-0.024, +0.024] | 67 | -0.000 [-0.031, +0.030] contains 0 | +0.039 [+0.014, +0.064] (n 67) | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → J* | 67 | +0.081 [+0.056, +0.106] | [+0.056, +0.106] | 67 | +0.081 [+0.050, +0.112] above 0 | +0.038 [+0.018, +0.057] (n 67) | 10 cell pairs, 67 identities paired |
| SUPERVISION · CS_SINGLE · A | XP → J* | 67 | +0.081 [+0.064, +0.098] | [+0.065, +0.098] | 67 | +0.081 [+0.061, +0.101] above 0 | -0.002 [-0.011, +0.008] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 67 | +0.004 [-0.019, +0.026] | [-0.018, +0.024] | 67 | +0.004 [-0.026, +0.033] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 67 | -0.006 [-0.020, +0.007] | [-0.020, +0.006] | 67 | -0.006 [-0.024, +0.011] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 67 | -0.021 [-0.044, +0.002] | [-0.043, -0.004] | 67 | -0.021 [-0.048, +0.005] contains 0 | – | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · A | XM → AP | 67 | -0.025 [-0.047, -0.003] | [-0.047, -0.004] | 67 | -0.025 [-0.053, +0.002] contains 0 | -0.023 [-0.048, +0.002] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · A | XM → XP | 67 | -0.026 [-0.041, -0.010] | [-0.041, -0.011] | 67 | -0.026 [-0.045, -0.007] below 0 | +0.016 [+0.006, +0.026] (n 67) | 10 cell pairs, 67 identities paired |
| CONTROL · CS_SINGLE · A | XM → J* | 67 | +0.056 [+0.037, +0.074] | [+0.038, +0.073] | 67 | +0.056 [+0.034, +0.078] above 0 | +0.014 [+0.004, +0.024] (n 67) | 10 cell pairs, 67 identities paired |

- INIT · CS_SINGLE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 67, crit 2.84.
- SUPERVISION · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 67, crit 2.57.
- SUPERVISION · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 67, crit 2.38.
- CONTROL · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 67, crit 2.66.
- CONTROL · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 67, crit 2.43.

Selection levels (unit records; codes in §1): mode T: L5 ×50 (as declared 50); mode A: L1 ×40 (as declared 40).

### core · dtu · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 44 | +0.074 [+0.050, +0.099] | [+0.050, +0.098] | 44 | +0.074 [+0.044, +0.105] above 0 | – | 10 cell pairs, 44 identities paired |
| INIT · NCE · T | S → XP | 44 | +0.021 [+0.001, +0.041] | [+0.002, +0.040] | 44 | +0.021 [-0.003, +0.045] contains 0 | – | 10 cell pairs, 44 identities paired |
| INIT · NCE · T | S → J* | 44 | +0.071 [+0.047, +0.094] | [+0.047, +0.093] | 44 | +0.071 [+0.041, +0.100] above 0 | – | 10 cell pairs, 44 identities paired |
| INIT · NCE · T | S → XM | 44 | +0.023 [-0.001, +0.046] | [-0.000, +0.046] | 44 | +0.023 [-0.007, +0.052] contains 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · T | AP → XP | 44 | -0.053 [-0.077, -0.030] | [-0.076, -0.032] | 44 | -0.053 [-0.080, -0.026] below 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · T | AP → J* | 44 | -0.004 [-0.009, +0.001] | [-0.009, +0.001] | 44 | -0.004 [-0.010, +0.002] contains 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · T | XP → J* | 44 | +0.049 [+0.027, +0.072] | [+0.028, +0.071] | 44 | +0.049 [+0.024, +0.075] above 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · A | AP → XP | 44 | -0.027 [-0.049, -0.004] | [-0.048, -0.005] | 44 | -0.027 [-0.053, -0.000] below 0 | -0.016 [-0.028, -0.005] (n 44) | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · A | AP → J* | 44 | -0.010 [-0.014, -0.006] | [-0.014, -0.006] | 44 | -0.010 [-0.015, -0.005] below 0 | -0.017 [-0.022, -0.013] (n 44) | 10 cell pairs, 44 identities paired |
| SUPERVISION · NCE · A | XP → J* | 44 | +0.016 [-0.005, +0.038] | [-0.004, +0.036] | 44 | +0.016 [-0.008, +0.041] contains 0 | -0.001 [-0.015, +0.013] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · T | XM → AP | 44 | +0.052 [+0.028, +0.075] | [+0.028, +0.074] | 44 | +0.052 [+0.024, +0.080] above 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · T | XM → XP | 44 | -0.002 [-0.028, +0.025] | [-0.028, +0.022] | 44 | -0.002 [-0.032, +0.029] contains 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · T | XM → J* | 44 | +0.048 [+0.023, +0.073] | [+0.024, +0.071] | 44 | +0.048 [+0.019, +0.077] above 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · A | XM → AP | 44 | +0.050 [+0.021, +0.079] | [+0.022, +0.077] | 44 | +0.050 [+0.017, +0.084] above 0 | -0.033 [-0.051, -0.016] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · A | XM → XP | 44 | +0.023 [+0.007, +0.040] | [+0.007, +0.039] | 44 | +0.023 [+0.004, +0.042] above 0 | -0.050 [-0.061, -0.038] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · NCE · A | XM → J* | 44 | +0.040 [+0.011, +0.069] | [+0.012, +0.067] | 44 | +0.040 [+0.006, +0.073] above 0 | -0.051 [-0.072, -0.030] (n 44) | 10 cell pairs, 44 identities paired |

- INIT · NCE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 44, crit 2.50.
- SUPERVISION · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 44, crit 2.37.
- SUPERVISION · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 44, crit 2.42.
- CONTROL · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 44, crit 2.36.
- CONTROL · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 44, crit 2.29.

Selection levels (unit records; codes in §1): mode T: L5 ×50 (as declared 50); mode A: L1 ×40 (as declared 40).

### core · dtu · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · CS_SINGLE · T | S → AP | 44 | +0.011 [-0.016, +0.038] | [-0.013, +0.038] | 44 | +0.011 [-0.021, +0.044] contains 0 | – | 10 cell pairs, 44 identities paired |
| INIT · CS_SINGLE · T | S → XP | 44 | -0.079 [-0.108, -0.050] | [-0.107, -0.051] | 44 | -0.079 [-0.116, -0.042] below 0 | – | 10 cell pairs, 44 identities paired |
| INIT · CS_SINGLE · T | S → J* | 44 | -0.043 [-0.066, -0.020] | [-0.065, -0.020] | 44 | -0.043 [-0.071, -0.015] below 0 | – | 10 cell pairs, 44 identities paired |
| INIT · CS_SINGLE · T | S → XM | 44 | -0.089 [-0.115, -0.064] | [-0.114, -0.065] | 44 | -0.089 [-0.121, -0.058] below 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 44 | -0.090 [-0.115, -0.066] | [-0.114, -0.067] | 44 | -0.090 [-0.120, -0.061] below 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 44 | -0.054 [-0.075, -0.034] | [-0.075, -0.034] | 44 | -0.054 [-0.080, -0.028] below 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 44 | +0.036 [+0.016, +0.057] | [+0.016, +0.055] | 44 | +0.036 [+0.011, +0.061] above 0 | – | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → XP | 44 | -0.048 [-0.075, -0.022] | [-0.073, -0.023] | 44 | -0.048 [-0.080, -0.017] below 0 | -0.025 [-0.042, -0.007] (n 44) | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → J* | 44 | -0.033 [-0.047, -0.019] | [-0.047, -0.020] | 44 | -0.033 [-0.050, -0.016] below 0 | -0.029 [-0.039, -0.019] (n 44) | 10 cell pairs, 44 identities paired |
| SUPERVISION · CS_SINGLE · A | XP → J* | 44 | +0.015 [-0.008, +0.038] | [-0.007, +0.037] | 44 | +0.015 [-0.011, +0.042] contains 0 | -0.005 [-0.018, +0.008] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 44 | +0.101 [+0.078, +0.123] | [+0.079, +0.122] | 44 | +0.101 [+0.074, +0.128] above 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 44 | +0.010 [-0.008, +0.029] | [-0.007, +0.029] | 44 | +0.010 [-0.013, +0.034] contains 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 44 | +0.047 [+0.028, +0.065] | [+0.029, +0.064] | 44 | +0.047 [+0.024, +0.069] above 0 | – | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · A | XM → AP | 44 | +0.100 [+0.077, +0.124] | [+0.077, +0.122] | 44 | +0.100 [+0.071, +0.129] above 0 | +0.039 [+0.021, +0.057] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · A | XM → XP | 44 | +0.052 [+0.034, +0.070] | [+0.035, +0.069] | 44 | +0.052 [+0.031, +0.073] above 0 | +0.015 [+0.007, +0.022] (n 44) | 10 cell pairs, 44 identities paired |
| CONTROL · CS_SINGLE · A | XM → J* | 44 | +0.067 [+0.051, +0.083] | [+0.052, +0.083] | 44 | +0.067 [+0.047, +0.087] above 0 | +0.010 [-0.003, +0.023] (n 44) | 10 cell pairs, 44 identities paired |

- INIT · CS_SINGLE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 44, crit 2.47.
- SUPERVISION · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 44, crit 2.43.
- SUPERVISION · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 44, crit 2.43.
- CONTROL · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 44, crit 2.46.
- CONTROL · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 44, crit 2.40.

Selection levels (unit records; codes in §1): mode T: L5 ×50 (as declared 50); mode A: L1 ×40 (as declared 40).

### core · federici · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 86 | +0.014 [-0.004, +0.032] | [-0.003, +0.032] | 86 | +0.014 [-0.009, +0.037] contains 0 | – | 5 cell pairs, 86 identities paired |
| INIT · NCE · T | S → XP | 86 | +0.024 [+0.008, +0.040] | [+0.008, +0.039] | 86 | +0.024 [+0.004, +0.043] above 0 | – | 5 cell pairs, 86 identities paired |
| INIT · NCE · T | S → J* | 86 | +0.008 [-0.012, +0.028] | [-0.011, +0.028] | 86 | +0.008 [-0.017, +0.033] contains 0 | – | 5 cell pairs, 86 identities paired |
| INIT · NCE · T | S → XM | 86 | +0.012 [-0.002, +0.026] | [-0.002, +0.025] | 86 | +0.012 [-0.006, +0.029] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · T | AP → XP | 86 | +0.010 [-0.007, +0.027] | [-0.007, +0.026] | 86 | +0.010 [-0.011, +0.030] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · T | AP → J* | 86 | -0.006 [-0.023, +0.011] | [-0.022, +0.011] | 86 | -0.006 [-0.026, +0.014] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · T | XP → J* | 86 | -0.016 [-0.032, +0.001] | [-0.032, +0.000] | 86 | -0.016 [-0.036, +0.004] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · A | AP → XP | 86 | +0.067 [+0.028, +0.106] | [+0.029, +0.106] | 86 | +0.067 [+0.021, +0.113] above 0 | +0.077 [+0.050, +0.104] (n 86) | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · A | AP → J* | 86 | +0.062 [+0.032, +0.093] | [+0.033, +0.093] | 86 | +0.062 [+0.028, +0.097] above 0 | +0.081 [+0.057, +0.104] (n 86) | 5 cell pairs, 86 identities paired |
| SUPERVISION · NCE · A | XP → J* | 86 | -0.005 [-0.021, +0.011] | [-0.021, +0.011] | 86 | -0.005 [-0.023, +0.014] contains 0 | +0.004 [-0.008, +0.015] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · T | XM → AP | 86 | +0.002 [-0.013, +0.018] | [-0.013, +0.018] | 86 | +0.002 [-0.017, +0.021] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · T | XM → XP | 86 | +0.012 [-0.002, +0.026] | [-0.002, +0.026] | 86 | +0.012 [-0.005, +0.029] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · T | XM → J* | 86 | -0.004 [-0.022, +0.015] | [-0.022, +0.014] | 86 | -0.004 [-0.026, +0.018] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · A | XM → AP | 86 | -0.135 [-0.181, -0.088] | [-0.179, -0.088] | 86 | -0.135 [-0.190, -0.080] below 0 | -0.048 [-0.082, -0.015] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · A | XM → XP | 86 | -0.068 [-0.101, -0.035] | [-0.101, -0.035] | 86 | -0.068 [-0.107, -0.029] below 0 | +0.029 [+0.014, +0.043] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · NCE · A | XM → J* | 86 | -0.073 [-0.107, -0.038] | [-0.106, -0.038] | 86 | -0.073 [-0.114, -0.031] below 0 | +0.033 [+0.012, +0.053] (n 86) | 5 cell pairs, 86 identities paired |

- INIT · NCE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 86, crit 2.50.
- SUPERVISION · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 86, crit 2.42.
- SUPERVISION · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 86, crit 2.30.
- CONTROL · NCE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 86, crit 2.34.
- CONTROL · NCE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 86, crit 2.32.

Selection levels (unit records; codes in §1): mode T: L5 ×25 (as declared 25); mode A: L1 ×20 (as declared 20).

### core · federici · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| INIT · CS_SINGLE · T | S → AP | 86 | +0.000 [-0.015, +0.016] | [-0.015, +0.016] | 86 | +0.000 [-0.019, +0.020] contains 0 | – | 5 cell pairs, 86 identities paired |
| INIT · CS_SINGLE · T | S → XP | 86 | +0.000 [-0.014, +0.015] | [-0.014, +0.015] | 86 | +0.000 [-0.017, +0.018] contains 0 | – | 5 cell pairs, 86 identities paired |
| INIT · CS_SINGLE · T | S → J* | 86 | -0.005 [-0.021, +0.010] | [-0.020, +0.010] | 86 | -0.005 [-0.024, +0.013] contains 0 | – | 5 cell pairs, 86 identities paired |
| INIT · CS_SINGLE · T | S → XM | 86 | -0.003 [-0.020, +0.015] | [-0.020, +0.015] | 86 | -0.003 [-0.024, +0.019] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 86 | -0.000 [-0.015, +0.015] | [-0.015, +0.014] | 86 | -0.000 [-0.018, +0.018] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 86 | -0.006 [-0.016, +0.004] | [-0.016, +0.004] | 86 | -0.006 [-0.018, +0.006] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 86 | -0.006 [-0.019, +0.008] | [-0.019, +0.008] | 86 | -0.006 [-0.022, +0.011] contains 0 | – | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → XP | 86 | +0.025 [+0.004, +0.046] | [+0.004, +0.045] | 86 | +0.025 [+0.001, +0.049] above 0 | +0.019 [-0.006, +0.044] (n 86) | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · A | AP → J* | 86 | -0.054 [-0.070, -0.037] | [-0.069, -0.038] | 86 | -0.054 [-0.072, -0.035] below 0 | +0.023 [+0.011, +0.035] (n 86) | 5 cell pairs, 86 identities paired |
| SUPERVISION · CS_SINGLE · A | XP → J* | 86 | -0.079 [-0.107, -0.050] | [-0.106, -0.049] | 86 | -0.079 [-0.112, -0.045] below 0 | +0.004 [-0.014, +0.022] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 86 | +0.003 [-0.013, +0.019] | [-0.013, +0.019] | 86 | +0.003 [-0.016, +0.022] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 86 | +0.003 [-0.009, +0.015] | [-0.009, +0.015] | 86 | +0.003 [-0.011, +0.017] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 86 | -0.003 [-0.017, +0.011] | [-0.016, +0.011] | 86 | -0.003 [-0.020, +0.014] contains 0 | – | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · A | XM → AP | 86 | -0.022 [-0.049, +0.005] | [-0.047, +0.005] | 86 | -0.022 [-0.053, +0.009] contains 0 | -0.014 [-0.041, +0.013] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · A | XM → XP | 86 | +0.003 [-0.015, +0.021] | [-0.014, +0.021] | 86 | +0.003 [-0.017, +0.024] contains 0 | +0.005 [-0.003, +0.013] (n 86) | 5 cell pairs, 86 identities paired |
| CONTROL · CS_SINGLE · A | XM → J* | 86 | -0.075 [-0.113, -0.037] | [-0.111, -0.037] | 86 | -0.075 [-0.119, -0.032] below 0 | +0.009 [-0.011, +0.029] (n 86) | 5 cell pairs, 86 identities paired |

- INIT · CS_SINGLE · T (R, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 86, crit 2.40.
- SUPERVISION · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 86, crit 2.35.
- SUPERVISION · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 86, crit 2.33.
- CONTROL · CS_SINGLE · T (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 86, crit 2.37.
- CONTROL · CS_SINGLE · A (R, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 86, crit 2.29.

Selection levels (unit records; codes in §1): mode T: L5 ×25 (as declared 25); mode A: L1 ×20 (as declared 20).

### core · private_bdf (mode T, seed 3401 only) · ΔNLL (ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.002 [+0.001, +0.003] | [+0.001, +0.003] | 64 | +0.002 [+0.000, +0.003] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.002 [+0.001, +0.003] | [+0.001, +0.003] | 64 | +0.002 [+0.000, +0.003] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.001 [-0.001, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | -0.001 [-0.002, +0.000] | [-0.002, +0.000] | 64 | -0.001 [-0.002, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [+0.000, +0.002] above 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | -0.001 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.001 [-0.002, +0.001] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.43.
- INIT · CS_SINGLE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.56.
- SUPERVISION · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.41.
- SUPERVISION · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.41.
- CONTROL · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.34.
- CONTROL · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.40.

### core · private_bdf (mode T, seed 3401 only) · ΔAUC (cand − ref)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.012 [+0.005, +0.019] | [+0.005, +0.019] | 64 | +0.012 [+0.003, +0.021] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | +0.007 [+0.001, +0.014] | [+0.001, +0.014] | 64 | +0.007 [-0.001, +0.015] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.015 [+0.008, +0.021] | [+0.008, +0.021] | 64 | +0.015 [+0.007, +0.023] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | +0.007 [+0.000, +0.013] | [+0.001, +0.013] | 64 | +0.007 [-0.001, +0.015] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.005 [-0.001, +0.011] | [-0.001, +0.011] | 64 | +0.005 [-0.002, +0.013] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | +0.005 [+0.000, +0.011] | [+0.000, +0.011] | 64 | +0.005 [-0.001, +0.012] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.005 [-0.001, +0.011] | [-0.001, +0.011] | 64 | +0.005 [-0.002, +0.013] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.006 [+0.000, +0.011] | [+0.001, +0.011] | 64 | +0.006 [-0.001, +0.013] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | -0.005 [-0.010, +0.001] | [-0.010, +0.001] | 64 | -0.005 [-0.012, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | +0.003 [-0.002, +0.007] | [-0.002, +0.007] | 64 | +0.003 [-0.003, +0.008] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | +0.007 [+0.002, +0.012] | [+0.003, +0.012] | 64 | +0.007 [+0.002, +0.013] above 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | +0.000 [-0.006, +0.006] | [-0.005, +0.006] | 64 | +0.000 [-0.007, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | +0.000 [-0.005, +0.006] | [-0.005, +0.005] | 64 | +0.000 [-0.007, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | -0.000 [-0.005, +0.005] | [-0.005, +0.005] | 64 | -0.000 [-0.006, +0.006] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | +0.005 [-0.002, +0.012] | [-0.002, +0.012] | 64 | +0.005 [-0.003, +0.013] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | +0.000 [-0.006, +0.006] | [-0.005, +0.006] | 64 | +0.000 [-0.007, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | +0.008 [+0.002, +0.013] | [+0.003, +0.013] | 64 | +0.008 [+0.001, +0.014] above 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | -0.001 [-0.007, +0.005] | [-0.007, +0.005] | 64 | -0.001 [-0.008, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | -0.001 [-0.005, +0.004] | [-0.004, +0.003] | 64 | -0.001 [-0.005, +0.004] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | -0.001 [-0.006, +0.005] | [-0.006, +0.005] | 64 | -0.001 [-0.007, +0.006] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.45.
- INIT · CS_SINGLE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.41.
- SUPERVISION · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.38.
- SUPERVISION · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.41.
- CONTROL · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.36.
- CONTROL · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.38.

Selection levels (unit records; codes in §1): mode T: L4 ×50 (as declared 50).

## 4. Access block (descriptive, pointwise; seed 3401 only)

| version | cohort · objective | modes | member | n | ΔR = R(A) − R(mode) [95 % bootstrap-t] | [95 % percentile] | coverage |
|---|---|---|---|---|---|---|---|
| primary | fau · NCE | A → B | AP | 67 | -0.024 [-0.060, +0.011] | [-0.059, +0.006] | 10 cell pairs, 67 identities paired |
| primary | fau · NCE | A → B | XP | 67 | +0.017 [-0.022, +0.055] | [+0.000, +0.039] | 10 cell pairs, 67 identities paired |
| primary | fau · NCE | A → B | J* | 67 | -0.036 [-0.089, +0.018] | [-0.087, +0.009] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → B | AP | 67 | +0.001 [-0.025, +0.026] | [-0.018, +0.024] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → B | XP | 67 | +0.030 [-0.026, +0.086] | [+0.002, +0.069] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → B | J* | 67 | +0.025 [-0.034, +0.083] | [-0.002, +0.059] | 10 cell pairs, 67 identities paired |
| primary | fau · NCE | A → C | AP | 67 | -0.148 [-0.207, -0.089] | [-0.204, -0.100] | 10 cell pairs, 67 identities paired |
| primary | fau · NCE | A → C | XP | 67 | +0.001 [-0.037, +0.039] | [-0.020, +0.028] | 10 cell pairs, 67 identities paired |
| primary | fau · NCE | A → C | J* | 67 | -0.150 [-0.229, -0.071] | [-0.221, -0.089] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → C | AP | 67 | -0.035 [-0.061, -0.009] | [-0.059, -0.010] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → C | XP | 67 | +0.019 [-0.041, +0.079] | [-0.012, +0.058] | 10 cell pairs, 67 identities paired |
| primary | fau · CS_SINGLE | A → C | J* | 67 | +0.029 [-0.014, +0.072] | [+0.006, +0.059] | 10 cell pairs, 67 identities paired |
| primary | dtu · NCE | A → C | AP | 44 | -0.018 [-0.032, -0.004] | [-0.030, -0.004] | 10 cell pairs, 44 identities paired |
| primary | dtu · NCE | A → C | XP | 44 | +0.002 [-0.003, +0.008] | [-0.003, +0.007] | 10 cell pairs, 44 identities paired |
| primary | dtu · NCE | A → C | J* | 44 | -0.017 [-0.031, -0.003] | [-0.029, -0.003] | 10 cell pairs, 44 identities paired |
| primary | dtu · CS_SINGLE | A → C | AP | 44 | -0.011 [-0.025, +0.003] | [-0.023, +0.003] | 10 cell pairs, 44 identities paired |
| primary | dtu · CS_SINGLE | A → C | XP | 44 | -0.007 [-0.010, -0.004] | [-0.010, -0.004] | 10 cell pairs, 44 identities paired |
| primary | dtu · CS_SINGLE | A → C | J* | 44 | +0.005 [-0.012, +0.021] | [-0.005, +0.018] | 10 cell pairs, 44 identities paired |
| primary | federici · NCE | A → C_partial | AP | 86 | +0.040 [+0.022, +0.058] | [+0.023, +0.058] | 5 cell pairs, 86 identities paired |
| primary | federici · NCE | A → C_partial | XP | 86 | -0.009 [-0.018, -0.000] | [-0.017, -0.000] | 5 cell pairs, 86 identities paired |
| primary | federici · NCE | A → C_partial | J* | 86 | -0.014 [-0.024, -0.003] | [-0.023, -0.003] | 5 cell pairs, 86 identities paired |
| primary | federici · CS_SINGLE | A → C_partial | AP | 86 | +0.007 [-0.005, +0.020] | [-0.005, +0.020] | 5 cell pairs, 86 identities paired |
| primary | federici · CS_SINGLE | A → C_partial | XP | 86 | -0.001 [-0.005, +0.004] | [-0.005, +0.004] | 5 cell pairs, 86 identities paired |
| primary | federici · CS_SINGLE | A → C_partial | J* | 86 | +0.002 [-0.010, +0.015] | [-0.010, +0.015] | 5 cell pairs, 86 identities paired |

fau (primary): Selection levels (unit records; codes in §1): mode A: L1 ×60 (as declared 60); mode B: L1 ×60 (as declared 60); mode C: L1 ×60 (as declared 60).
dtu (primary): Selection levels (unit records; codes in §1): mode A: L1 ×60 (as declared 60); mode C: L1 ×60 (as declared 60).
federici (primary): Selection levels (unit records; codes in §1): mode A: L1 ×30 (as declared 30); mode C_partial: L1 ×30 (as declared 30).

## 5. Panel (private_bdf, mode T; seeds 3401, 3407, 3413)

Per-seed families are computed like the core families (seed 3401 is the core table). Three-seed: the identity value is the mean over the three seeds of the within-seed paired difference; a contrast without a complete common seed set lists the available seeds. The between-seed SD of three estimates is descriptive.

### Three-seed summary

| family · objective | member | endpoint | seed 3401 | seed 3407 | seed 3413 | mean / range / SD | three-seed n | three-seed Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| INIT · NCE | S → AP | NLL | +0.002 | +0.001 | +0.001 | +0.001 / [+0.001, +0.002] / 0.001 | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [+0.000, +0.002] above 0 |
| INIT · NCE | S → XP | NLL | +0.001 | -0.000 | +0.001 | +0.000 / [-0.000, +0.001] / 0.001 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 |
| INIT · NCE | S → J* | NLL | +0.002 | +0.001 | +0.000 | +0.001 / [+0.000, +0.002] / 0.001 | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [+0.000, +0.002] above 0 |
| INIT · NCE | S → XM | NLL | +0.001 | -0.000 | +0.001 | +0.001 / [-0.000, +0.001] / 0.001 | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.001 [-0.000, +0.002] contains 0 |
| INIT · NCE | S → AP | AUC | +0.012 | +0.008 | +0.007 | +0.009 / [+0.007, +0.012] / 0.003 | 64 | +0.009 [+0.004, +0.013] | [+0.004, +0.013] | 64 | +0.009 [+0.003, +0.014] above 0 |
| INIT · NCE | S → XP | AUC | +0.007 | -0.001 | +0.009 | +0.005 / [-0.001, +0.009] / 0.006 | 64 | +0.005 [+0.001, +0.009] | [+0.001, +0.009] | 64 | +0.005 [+0.000, +0.010] above 0 |
| INIT · NCE | S → J* | AUC | +0.015 | +0.008 | +0.004 | +0.009 / [+0.004, +0.015] / 0.005 | 64 | +0.009 [+0.005, +0.013] | [+0.005, +0.013] | 64 | +0.009 [+0.004, +0.014] above 0 |
| INIT · NCE | S → XM | AUC | +0.007 | -0.000 | +0.012 | +0.006 / [-0.000, +0.012] / 0.006 | 64 | +0.006 [+0.002, +0.011] | [+0.002, +0.011] | 64 | +0.006 [+0.001, +0.012] above 0 |
| INIT · CS_SINGLE | S → AP | NLL | +0.001 | +0.000 | +0.001 | +0.001 / [+0.000, +0.001] / 0.000 | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 |
| INIT · CS_SINGLE | S → XP | NLL | +0.000 | -0.000 | +0.001 | +0.000 / [-0.000, +0.001] / 0.001 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 |
| INIT · CS_SINGLE | S → J* | NLL | +0.000 | +0.000 | +0.002 | +0.001 / [+0.000, +0.002] / 0.001 | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.001 [-0.000, +0.002] contains 0 |
| INIT · CS_SINGLE | S → XM | NLL | +0.001 | +0.000 | +0.001 | +0.000 / [+0.000, +0.001] / 0.000 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 |
| INIT · CS_SINGLE | S → AP | AUC | +0.005 | +0.005 | +0.009 | +0.007 / [+0.005, +0.009] / 0.002 | 64 | +0.007 [+0.002, +0.012] | [+0.002, +0.011] | 64 | +0.007 [+0.000, +0.013] above 0 |
| INIT · CS_SINGLE | S → XP | AUC | +0.005 | -0.000 | +0.007 | +0.004 / [-0.000, +0.007] / 0.004 | 64 | +0.004 [+0.001, +0.008] | [+0.001, +0.008] | 64 | +0.004 [-0.000, +0.009] contains 0 |
| INIT · CS_SINGLE | S → J* | AUC | +0.005 | +0.006 | +0.011 | +0.007 / [+0.005, +0.011] / 0.003 | 64 | +0.007 [+0.003, +0.012] | [+0.003, +0.011] | 64 | +0.007 [+0.002, +0.013] above 0 |
| INIT · CS_SINGLE | S → XM | AUC | +0.006 | +0.001 | +0.005 | +0.004 / [+0.001, +0.006] / 0.003 | 64 | +0.004 [-0.000, +0.008] | [-0.000, +0.008] | 64 | +0.004 [-0.001, +0.009] contains 0 |
| SUPERVISION · NCE | AP → XP | NLL | -0.001 | -0.001 | +0.000 | -0.001 / [-0.001, +0.000] / 0.001 | 64 | -0.001 [-0.001, -0.000] | [-0.001, -0.000] | 64 | -0.001 [-0.001, +0.000] contains 0 |
| SUPERVISION · NCE | AP → J* | NLL | +0.000 | +0.000 | -0.000 | -0.000 / [-0.000, +0.000] / 0.000 | 64 | -0.000 [-0.000, +0.000] | [-0.000, +0.000] | 64 | -0.000 [-0.000, +0.000] contains 0 |
| SUPERVISION · NCE | XP → J* | NLL | +0.001 | +0.001 | -0.001 | +0.001 / [-0.001, +0.001] / 0.001 | 64 | +0.001 [+0.000, +0.001] | [+0.000, +0.001] | 64 | +0.001 [+0.000, +0.001] above 0 |
| SUPERVISION · NCE | AP → XP | AUC | -0.005 | -0.009 | +0.003 | -0.004 / [-0.009, +0.003] / 0.006 | 64 | -0.004 [-0.007, -0.000] | [-0.007, -0.000] | 64 | -0.004 [-0.008, +0.000] contains 0 |
| SUPERVISION · NCE | AP → J* | AUC | +0.003 | +0.001 | -0.002 | +0.000 / [-0.002, +0.003] / 0.003 | 64 | +0.000 [-0.001, +0.002] | [-0.002, +0.002] | 64 | +0.000 [-0.002, +0.003] contains 0 |
| SUPERVISION · NCE | XP → J* | AUC | +0.007 | +0.010 | -0.005 | +0.004 / [-0.005, +0.010] / 0.008 | 64 | +0.004 [+0.001, +0.007] | [+0.001, +0.007] | 64 | +0.004 [+0.000, +0.008] above 0 |
| SUPERVISION · CS_SINGLE | AP → XP | NLL | -0.000 | -0.001 | -0.000 | -0.000 / [-0.001, -0.000] / 0.000 | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 |
| SUPERVISION · CS_SINGLE | AP → J* | NLL | -0.000 | +0.000 | +0.000 | +0.000 / [-0.000, +0.000] / 0.000 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.000] | 64 | +0.000 [-0.001, +0.001] contains 0 |
| SUPERVISION · CS_SINGLE | XP → J* | NLL | -0.000 | +0.001 | +0.001 | +0.000 / [-0.000, +0.001] / 0.001 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 |
| SUPERVISION · CS_SINGLE | AP → XP | AUC | +0.000 | -0.006 | -0.002 | -0.002 / [-0.006, +0.000] / 0.003 | 64 | -0.002 [-0.007, +0.002] | [-0.007, +0.002] | 64 | -0.002 [-0.008, +0.003] contains 0 |
| SUPERVISION · CS_SINGLE | AP → J* | AUC | +0.000 | +0.000 | +0.001 | +0.001 / [+0.000, +0.001] / 0.001 | 64 | +0.001 [-0.002, +0.003] | [-0.002, +0.003] | 64 | +0.001 [-0.003, +0.004] contains 0 |
| SUPERVISION · CS_SINGLE | XP → J* | AUC | -0.000 | +0.006 | +0.003 | +0.003 / [-0.000, +0.006] / 0.003 | 64 | +0.003 [-0.001, +0.007] | [-0.001, +0.007] | 64 | +0.003 [-0.002, +0.008] contains 0 |
| CONTROL · NCE | XM → AP | NLL | +0.001 | +0.001 | -0.001 | +0.000 / [-0.001, +0.001] / 0.001 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 |
| CONTROL · NCE | XM → XP | NLL | +0.000 | -0.000 | -0.000 | -0.000 / [-0.000, +0.000] / 0.000 | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.000] contains 0 |
| CONTROL · NCE | XM → J* | NLL | +0.001 | +0.001 | -0.001 | +0.000 / [-0.001, +0.001] / 0.001 | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 |
| CONTROL · NCE | XM → AP | AUC | +0.005 | +0.008 | -0.005 | +0.003 / [-0.005, +0.008] / 0.007 | 64 | +0.003 [-0.002, +0.007] | [-0.002, +0.007] | 64 | +0.003 [-0.003, +0.008] contains 0 |
| CONTROL · NCE | XM → XP | AUC | +0.000 | -0.001 | -0.003 | -0.001 / [-0.003, +0.000] / 0.002 | 64 | -0.001 [-0.005, +0.003] | [-0.005, +0.003] | 64 | -0.001 [-0.006, +0.004] contains 0 |
| CONTROL · NCE | XM → J* | AUC | +0.008 | +0.009 | -0.008 | +0.003 / [-0.008, +0.009] / 0.009 | 64 | +0.003 [-0.001, +0.007] | [-0.001, +0.006] | 64 | +0.003 [-0.001, +0.007] contains 0 |
| CONTROL · CS_SINGLE | XM → AP | NLL | -0.000 | +0.000 | +0.000 | +0.000 / [-0.000, +0.000] / 0.000 | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 |
| CONTROL · CS_SINGLE | XM → XP | NLL | -0.000 | -0.000 | +0.000 | -0.000 / [-0.000, +0.000] / 0.000 | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.000] contains 0 |
| CONTROL · CS_SINGLE | XM → J* | NLL | -0.001 | +0.000 | +0.001 | +0.000 / [-0.001, +0.001] / 0.001 | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 |
| CONTROL · CS_SINGLE | XM → AP | AUC | -0.001 | +0.004 | +0.005 | +0.003 / [-0.001, +0.005] / 0.003 | 64 | +0.003 [-0.003, +0.008] | [-0.003, +0.008] | 64 | +0.003 [-0.004, +0.009] contains 0 |
| CONTROL · CS_SINGLE | XM → XP | AUC | -0.001 | -0.001 | +0.003 | +0.000 / [-0.001, +0.003] / 0.002 | 64 | +0.000 [-0.003, +0.003] | [-0.003, +0.003] | 64 | +0.000 [-0.003, +0.004] contains 0 |
| CONTROL · CS_SINGLE | XM → J* | AUC | -0.001 | +0.005 | +0.006 | +0.003 / [-0.001, +0.006] / 0.004 | 64 | +0.003 [-0.001, +0.008] | [-0.001, +0.008] | 64 | +0.003 [-0.002, +0.009] contains 0 |

- PANEL3 INIT · NCE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.39.
- PANEL3 INIT · NCE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.43.
- PANEL3 INIT · CS_SINGLE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.47.
- PANEL3 INIT · CS_SINGLE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.49.
- PANEL3 SUPERVISION · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.42.
- PANEL3 SUPERVISION · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.38.
- PANEL3 SUPERVISION · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.40.
- PANEL3 SUPERVISION · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.42.
- PANEL3 CONTROL · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.31.
- PANEL3 CONTROL · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.42.
- PANEL3 CONTROL · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.32.
- PANEL3 CONTROL · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.34.

### panel · private_bdf (mode T, panel seed 3407) · ΔNLL (ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | -0.000 [-0.002, +0.001] | [-0.002, +0.001] | 64 | -0.000 [-0.002, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.000 [-0.001, +0.002] | [-0.001, +0.002] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | -0.001 [-0.002, -0.001] | [-0.002, -0.001] | 64 | -0.001 [-0.002, -0.000] below 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | +0.000 [-0.000, +0.000] | [-0.000, +0.000] | 64 | +0.000 [-0.000, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | +0.001 [+0.001, +0.002] | [+0.001, +0.002] | 64 | +0.001 [+0.001, +0.002] above 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | -0.001 [-0.002, +0.001] | [-0.002, +0.001] | 64 | -0.001 [-0.002, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.39.
- INIT · CS_SINGLE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.42.
- SUPERVISION · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.34.
- SUPERVISION · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.36.
- CONTROL · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.30.
- CONTROL · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.38.

### panel · private_bdf (mode T, panel seed 3407) · ΔAUC (cand − ref)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.008 [+0.001, +0.014] | [+0.001, +0.014] | 64 | +0.008 [-0.000, +0.015] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | -0.001 [-0.008, +0.005] | [-0.008, +0.005] | 64 | -0.001 [-0.009, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.008 [+0.001, +0.015] | [+0.002, +0.015] | 64 | +0.008 [+0.000, +0.017] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | -0.000 [-0.006, +0.005] | [-0.006, +0.005] | 64 | -0.000 [-0.008, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.005 [-0.002, +0.013] | [-0.002, +0.012] | 64 | +0.005 [-0.004, +0.014] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | -0.000 [-0.007, +0.006] | [-0.007, +0.006] | 64 | -0.000 [-0.009, +0.008] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.006 [-0.001, +0.012] | [-0.001, +0.012] | 64 | +0.006 [-0.003, +0.014] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.001 [-0.006, +0.008] | [-0.005, +0.007] | 64 | +0.001 [-0.007, +0.009] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | -0.009 [-0.014, -0.004] | [-0.014, -0.004] | 64 | -0.009 [-0.015, -0.003] below 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | +0.010 [+0.004, +0.015] | [+0.005, +0.015] | 64 | +0.010 [+0.004, +0.016] above 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | -0.006 [-0.012, +0.001] | [-0.012, +0.001] | 64 | -0.006 [-0.014, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | +0.000 [-0.004, +0.005] | [-0.004, +0.004] | 64 | +0.000 [-0.005, +0.005] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | +0.006 [-0.000, +0.012] | [-0.000, +0.012] | 64 | +0.006 [-0.002, +0.014] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | +0.008 [+0.002, +0.014] | [+0.003, +0.014] | 64 | +0.008 [+0.001, +0.015] above 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | -0.001 [-0.007, +0.006] | [-0.007, +0.005] | 64 | -0.001 [-0.008, +0.006] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | +0.009 [+0.003, +0.015] | [+0.003, +0.015] | 64 | +0.009 [+0.002, +0.016] above 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | +0.004 [-0.003, +0.012] | [-0.003, +0.012] | 64 | +0.004 [-0.005, +0.013] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | -0.001 [-0.006, +0.003] | [-0.006, +0.003] | 64 | -0.001 [-0.007, +0.004] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | +0.005 [-0.002, +0.011] | [-0.002, +0.011] | 64 | +0.005 [-0.003, +0.013] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.43.
- INIT · CS_SINGLE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.46.
- SUPERVISION · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.35.
- SUPERVISION · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.40.
- CONTROL · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.27.
- CONTROL · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.45.

### panel · private_bdf (mode T, panel seed 3413) · ΔNLL (ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | +0.001 [+0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [+0.000, +0.002] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | +0.001 [+0.001, +0.002] | [+0.001, +0.002] | 64 | +0.001 [+0.000, +0.003] above 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.001 [-0.000, +0.003] | [-0.000, +0.003] | 64 | +0.001 [-0.001, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.002 [+0.000, +0.003] | [+0.000, +0.003] | 64 | +0.002 [-0.000, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | -0.001 [-0.001, -0.000] | [-0.001, -0.000] | 64 | -0.001 [-0.002, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | -0.000 [-0.002, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.002, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.000, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | -0.001 [-0.002, +0.000] | [-0.002, +0.000] | 64 | -0.001 [-0.002, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.000 [-0.001, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | -0.001 [-0.002, -0.000] | [-0.002, -0.000] | 64 | -0.001 [-0.002, -0.000] below 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | +0.000 [-0.001, +0.002] | [-0.001, +0.002] | 64 | +0.000 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 64 | +0.001 [-0.001, +0.002] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.48.
- INIT · CS_SINGLE · T (NLL, ref − cand): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.49.
- SUPERVISION · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.46.
- SUPERVISION · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.35.
- CONTROL · NCE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.30.
- CONTROL · CS_SINGLE · T (NLL, ref − cand): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.34.

### panel · private_bdf (mode T, panel seed 3413) · ΔAUC (cand − ref)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| INIT · NCE · T | S → AP | 64 | +0.007 [+0.002, +0.012] | [+0.002, +0.012] | 64 | +0.007 [+0.001, +0.013] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XP | 64 | +0.009 [+0.004, +0.015] | [+0.004, +0.015] | 64 | +0.009 [+0.003, +0.016] above 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → J* | 64 | +0.004 [-0.001, +0.010] | [-0.001, +0.009] | 64 | +0.004 [-0.002, +0.011] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · NCE · T | S → XM | 64 | +0.012 [+0.006, +0.018] | [+0.006, +0.018] | 64 | +0.012 [+0.005, +0.020] above 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → AP | 64 | +0.009 [+0.002, +0.017] | [+0.002, +0.017] | 64 | +0.009 [-0.000, +0.019] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XP | 64 | +0.007 [+0.001, +0.014] | [+0.001, +0.014] | 64 | +0.007 [-0.001, +0.016] contains 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → J* | 64 | +0.011 [+0.004, +0.018] | [+0.004, +0.018] | 64 | +0.011 [+0.002, +0.020] above 0 | 5 cell pairs, 64 identities paired |
| INIT · CS_SINGLE · T | S → XM | 64 | +0.005 [-0.003, +0.012] | [-0.003, +0.012] | 64 | +0.005 [-0.005, +0.014] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → XP | 64 | +0.003 [-0.001, +0.006] | [-0.001, +0.006] | 64 | +0.003 [-0.002, +0.007] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | AP → J* | 64 | -0.002 [-0.006, +0.002] | [-0.006, +0.001] | 64 | -0.002 [-0.007, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · NCE · T | XP → J* | 64 | -0.005 [-0.010, +0.001] | [-0.010, +0.000] | 64 | -0.005 [-0.011, +0.002] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → XP | 64 | -0.002 [-0.009, +0.005] | [-0.009, +0.005] | 64 | -0.002 [-0.010, +0.006] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | AP → J* | 64 | +0.001 [-0.002, +0.005] | [-0.002, +0.005] | 64 | +0.001 [-0.003, +0.006] contains 0 | 5 cell pairs, 64 identities paired |
| SUPERVISION · CS_SINGLE · T | XP → J* | 64 | +0.003 [-0.003, +0.010] | [-0.003, +0.009] | 64 | +0.003 [-0.004, +0.011] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → AP | 64 | -0.005 [-0.011, +0.000] | [-0.011, +0.000] | 64 | -0.005 [-0.012, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → XP | 64 | -0.003 [-0.008, +0.002] | [-0.008, +0.002] | 64 | -0.003 [-0.009, +0.003] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · NCE · T | XM → J* | 64 | -0.008 [-0.014, -0.001] | [-0.014, -0.001] | 64 | -0.008 [-0.015, -0.000] below 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → AP | 64 | +0.005 [-0.003, +0.013] | [-0.003, +0.013] | 64 | +0.005 [-0.005, +0.015] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → XP | 64 | +0.003 [-0.004, +0.009] | [-0.003, +0.009] | 64 | +0.003 [-0.005, +0.010] contains 0 | 5 cell pairs, 64 identities paired |
| CONTROL · CS_SINGLE · T | XM → J* | 64 | +0.006 [-0.001, +0.014] | [-0.001, +0.014] | 64 | +0.006 [-0.003, +0.015] contains 0 | 5 cell pairs, 64 identities paired |

- INIT · NCE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.45.
- INIT · CS_SINGLE · T (AUC, cand − ref): simultaneous over 4 of 4 declared members (S → AP, S → XP, S → J*, S → XM), family n = 64, crit 2.48.
- SUPERVISION · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.40.
- SUPERVISION · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (AP → XP, AP → J*, XP → J*), family n = 64, crit 2.36.
- CONTROL · NCE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.29.
- CONTROL · CS_SINGLE · T (AUC, cand − ref): simultaneous over 3 of 3 declared members (XM → AP, XM → XP, XM → J*), family n = 64, crit 2.33.

### E_LOCAL native reference

Different input contract (250 Hz native, 0.5–45 Hz, ALN3 recipe); descriptive, pointwise; Δ = E_LOCAL → arm in the positive-is-better convention.

| seed | objective | endpoint | member | n | Δ [95 % bootstrap-t] | [95 % percentile] | coverage |
|---|---|---|---|---|---|---|---|
| seed 3401 only | NCE | NLL (ref − cand) | E_LOCAL → S | 64 | +0.002 [+0.000, +0.003] | [+0.001, +0.003] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | NLL (ref − cand) | E_LOCAL → AP | 64 | +0.003 [+0.002, +0.005] | [+0.002, +0.005] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | NLL (ref − cand) | E_LOCAL → XP | 64 | +0.002 [+0.001, +0.004] | [+0.001, +0.004] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.003 [+0.002, +0.005] | [+0.002, +0.005] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | NLL (ref − cand) | E_LOCAL → XM | 64 | +0.002 [+0.001, +0.004] | [+0.001, +0.004] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | NLL (ref − cand) | E_LOCAL → S | 64 | +0.002 [+0.001, +0.003] | [+0.001, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | NLL (ref − cand) | E_LOCAL → AP | 64 | +0.003 [+0.002, +0.005] | [+0.002, +0.005] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | NLL (ref − cand) | E_LOCAL → XP | 64 | +0.002 [+0.000, +0.003] | [+0.000, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.003 [+0.002, +0.005] | [+0.002, +0.005] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | NLL (ref − cand) | E_LOCAL → XM | 64 | +0.002 [+0.001, +0.003] | [+0.001, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | NLL (ref − cand) | E_LOCAL → S | 64 | +0.001 [-0.000, +0.003] | [-0.000, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | NLL (ref − cand) | E_LOCAL → AP | 64 | +0.002 [+0.000, +0.004] | [+0.000, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | NLL (ref − cand) | E_LOCAL → XP | 64 | +0.002 [+0.001, +0.004] | [+0.001, +0.004] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.002 [+0.000, +0.003] | [+0.000, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | NLL (ref − cand) | E_LOCAL → XM | 64 | +0.003 [+0.001, +0.004] | [+0.001, +0.004] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | AUC (cand − ref) | E_LOCAL → S | 64 | +0.018 [+0.010, +0.027] | [+0.010, +0.027] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.030 [+0.019, +0.041] | [+0.020, +0.041] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | AUC (cand − ref) | E_LOCAL → XP | 64 | +0.025 [+0.016, +0.035] | [+0.016, +0.035] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.033 [+0.022, +0.043] | [+0.023, +0.043] | 5 cell pairs, 64 identities paired |
| seed 3401 only | NCE | AUC (cand − ref) | E_LOCAL → XM | 64 | +0.025 [+0.015, +0.035] | [+0.016, +0.035] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | AUC (cand − ref) | E_LOCAL → S | 64 | +0.018 [+0.010, +0.026] | [+0.010, +0.026] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.025 [+0.016, +0.035] | [+0.016, +0.034] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | AUC (cand − ref) | E_LOCAL → XP | 64 | +0.017 [+0.008, +0.025] | [+0.008, +0.025] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.026 [+0.017, +0.036] | [+0.017, +0.035] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | NCE | AUC (cand − ref) | E_LOCAL → XM | 64 | +0.017 [+0.009, +0.026] | [+0.009, +0.026] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | AUC (cand − ref) | E_LOCAL → S | 64 | +0.012 [+0.004, +0.021] | [+0.004, +0.021] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.019 [+0.010, +0.029] | [+0.011, +0.028] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | AUC (cand − ref) | E_LOCAL → XP | 64 | +0.022 [+0.012, +0.032] | [+0.012, +0.031] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.017 [+0.008, +0.026] | [+0.009, +0.025] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | NCE | AUC (cand − ref) | E_LOCAL → XM | 64 | +0.025 [+0.015, +0.034] | [+0.015, +0.034] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | NLL (ref − cand) | E_LOCAL → S | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | NLL (ref − cand) | E_LOCAL → AP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XM | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → S | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → AP | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XP | 64 | -0.001 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XM | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → S | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → AP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XP | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.002] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → J* | 64 | +0.001 [+0.000, +0.003] | [+0.000, +0.002] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | NLL (ref − cand) | E_LOCAL → XM | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | AUC (cand − ref) | E_LOCAL → S | 64 | -0.002 [-0.007, +0.004] | [-0.007, +0.003] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.003 [-0.004, +0.011] | [-0.004, +0.010] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XP | 64 | +0.004 [-0.002, +0.010] | [-0.002, +0.010] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.003 [-0.003, +0.010] | [-0.003, +0.010] | 5 cell pairs, 64 identities paired |
| seed 3401 only | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XM | 64 | +0.004 [-0.003, +0.011] | [-0.003, +0.011] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → S | 64 | -0.004 [-0.010, +0.003] | [-0.010, +0.002] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.002 [-0.005, +0.008] | [-0.005, +0.007] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XP | 64 | -0.004 [-0.009, +0.001] | [-0.009, +0.001] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.002 [-0.004, +0.008] | [-0.003, +0.007] | 5 cell pairs, 64 identities paired |
| panel seed 3407 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XM | 64 | -0.003 [-0.008, +0.003] | [-0.008, +0.003] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → S | 64 | -0.001 [-0.007, +0.006] | [-0.007, +0.006] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → AP | 64 | +0.009 [+0.001, +0.017] | [+0.001, +0.017] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XP | 64 | +0.007 [+0.001, +0.013] | [+0.001, +0.013] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → J* | 64 | +0.010 [+0.003, +0.018] | [+0.003, +0.017] | 5 cell pairs, 64 identities paired |
| panel seed 3413 | CS_SINGLE | AUC (cand − ref) | E_LOCAL → XM | 64 | +0.004 [-0.002, +0.010] | [-0.002, +0.010] | 5 cell pairs, 64 identities paired |

| three-seed reference · objective · endpoint | member | status | n | Δ [95 % bootstrap-t] | [95 % percentile] |
|---|---|---|---|---|---|
| NCE · NLL | E_LOCAL → S | complete common seed set | 64 | +0.002 [+0.001, +0.003] | [+0.001, +0.003] |
| NCE · NLL | E_LOCAL → AP | complete common seed set | 64 | +0.003 [+0.001, +0.004] | [+0.001, +0.004] |
| NCE · NLL | E_LOCAL → XP | complete common seed set | 64 | +0.002 [+0.001, +0.004] | [+0.001, +0.004] |
| NCE · NLL | E_LOCAL → J* | complete common seed set | 64 | +0.003 [+0.001, +0.004] | [+0.001, +0.004] |
| NCE · NLL | E_LOCAL → XM | complete common seed set | 64 | +0.002 [+0.001, +0.004] | [+0.001, +0.004] |
| NCE · AUC | E_LOCAL → S | complete common seed set | 64 | +0.016 [+0.010, +0.022] | [+0.010, +0.022] |
| NCE · AUC | E_LOCAL → AP | complete common seed set | 64 | +0.025 [+0.017, +0.033] | [+0.017, +0.033] |
| NCE · AUC | E_LOCAL → XP | complete common seed set | 64 | +0.021 [+0.014, +0.029] | [+0.014, +0.029] |
| NCE · AUC | E_LOCAL → J* | complete common seed set | 64 | +0.025 [+0.018, +0.033] | [+0.018, +0.033] |
| NCE · AUC | E_LOCAL → XM | complete common seed set | 64 | +0.022 [+0.015, +0.030] | [+0.015, +0.030] |
| CS_SINGLE · NLL | E_LOCAL → S | complete common seed set | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] |
| CS_SINGLE · NLL | E_LOCAL → AP | complete common seed set | 64 | +0.001 [-0.000, +0.002] | [-0.000, +0.001] |
| CS_SINGLE · NLL | E_LOCAL → XP | complete common seed set | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] |
| CS_SINGLE · NLL | E_LOCAL → J* | complete common seed set | 64 | +0.001 [-0.000, +0.001] | [-0.000, +0.001] |
| CS_SINGLE · NLL | E_LOCAL → XM | complete common seed set | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] |
| CS_SINGLE · AUC | E_LOCAL → S | complete common seed set | 64 | -0.002 [-0.006, +0.002] | [-0.006, +0.002] |
| CS_SINGLE · AUC | E_LOCAL → AP | complete common seed set | 64 | +0.005 [-0.001, +0.010] | [-0.001, +0.010] |
| CS_SINGLE · AUC | E_LOCAL → XP | complete common seed set | 64 | +0.002 [-0.002, +0.006] | [-0.001, +0.006] |
| CS_SINGLE · AUC | E_LOCAL → J* | complete common seed set | 64 | +0.005 [+0.000, +0.010] | [+0.000, +0.010] |
| CS_SINGLE · AUC | E_LOCAL → XM | complete common seed set | 64 | +0.002 [-0.003, +0.006] | [-0.002, +0.006] |

Selection levels (unit records; codes in §1): mode T: L4 ×150 (as declared 150); E_LOCAL: none ×30 (no declared level 30).

## 6. Rich block (seed 3401 only)

### RICH · fau · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · NCE · T | AP → APR | 67 | +0.016 [-0.002, +0.034] | [-0.001, +0.034] | 67 | +0.016 [-0.002, +0.034] contains 0 | – | 10 cell pairs, 67 identities paired |
| RICH · NCE · A | AP → APR | 67 | -0.004 [-0.015, +0.006] | [-0.015, +0.005] | 67 | -0.004 [-0.015, +0.006] contains 0 | -0.003 [-0.011, +0.004] (n 67) | 10 cell pairs, 67 identities paired |

- RICH · NCE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 67, crit 2.02.
- RICH · NCE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 67, crit 2.07.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### RICH · fau · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · CS_SINGLE · T | AP → APR | 67 | -0.009 [-0.027, +0.009] | [-0.025, +0.005] | 67 | -0.009 [-0.027, +0.009] contains 0 | – | 10 cell pairs, 67 identities paired |
| RICH · CS_SINGLE · A | AP → APR | 67 | -0.000 [-0.007, +0.007] | [-0.007, +0.006] | 67 | -0.000 [-0.007, +0.007] contains 0 | +0.007 [-0.000, +0.015] (n 67) | 10 cell pairs, 67 identities paired |

- RICH · CS_SINGLE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 67, crit 2.28.
- RICH · CS_SINGLE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 67, crit 2.05.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### RICH · dtu · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · NCE · T | AP → APR | 44 | +0.011 [-0.014, +0.037] | [-0.012, +0.035] | 44 | +0.011 [-0.014, +0.037] contains 0 | – | 10 cell pairs, 44 identities paired |
| RICH · NCE · A | AP → APR | 44 | +0.065 [+0.050, +0.080] | [+0.054, +0.079] | 44 | +0.065 [+0.050, +0.080] above 0 | +0.043 [+0.031, +0.055] (n 44) | 10 cell pairs, 44 identities paired |

- RICH · NCE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 44, crit 2.11.
- RICH · NCE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 44, crit 2.28.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### RICH · dtu · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · CS_SINGLE · T | AP → APR | 44 | -0.034 [-0.051, -0.016] | [-0.050, -0.016] | 44 | -0.034 [-0.051, -0.016] below 0 | – | 10 cell pairs, 44 identities paired |
| RICH · CS_SINGLE · A | AP → APR | 44 | -0.017 [-0.028, -0.006] | [-0.028, -0.006] | 44 | -0.017 [-0.028, -0.006] below 0 | -0.010 [-0.018, -0.002] (n 44) | 10 cell pairs, 44 identities paired |

- RICH · CS_SINGLE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 44, crit 2.00.
- RICH · CS_SINGLE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 44, crit 2.09.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### RICH · federici · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · NCE · T | AP → APR | 86 | +0.013 [-0.001, +0.026] | [+0.000, +0.026] | 86 | +0.013 [-0.001, +0.026] contains 0 | – | 5 cell pairs, 86 identities paired |
| RICH · NCE · A | AP → APR | 86 | -0.008 [-0.014, -0.002] | [-0.014, -0.002] | 86 | -0.008 [-0.014, -0.002] below 0 | -0.011 [-0.018, -0.004] (n 86) | 5 cell pairs, 86 identities paired |

- RICH · NCE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 86, crit 2.00.
- RICH · NCE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 86, crit 1.97.

Selection levels (unit records; codes in §1): mode T: L5 ×10 (as declared 10); mode A: L1 ×10 (as declared 10).

### RICH · federici · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| RICH · CS_SINGLE · T | AP → APR | 86 | -0.005 [-0.015, +0.005] | [-0.014, +0.004] | 86 | -0.005 [-0.015, +0.005] contains 0 | – | 5 cell pairs, 86 identities paired |
| RICH · CS_SINGLE · A | AP → APR | 86 | -0.078 [-0.093, -0.063] | [-0.092, -0.063] | 86 | -0.078 [-0.093, -0.063] below 0 | -0.031 [-0.041, -0.022] (n 86) | 5 cell pairs, 86 identities paired |

- RICH · CS_SINGLE · T (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 86, crit 2.02.
- RICH · CS_SINGLE · A (R, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 86, crit 1.95.

Selection levels (unit records; codes in §1): mode T: L5 ×10 (as declared 10); mode A: L1 ×10 (as declared 10).

### RICH · private_bdf (mode T, seed 3401 only) · ΔNLL (ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| RICH · NCE · T | AP → APR | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| RICH · CS_SINGLE · T | AP → APR | 64 | +0.001 [-0.000, +0.002] | [+0.000, +0.002] | 64 | +0.001 [-0.000, +0.002] contains 0 | 5 cell pairs, 64 identities paired |

- RICH · NCE · T (NLL, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 64, crit 2.03.
- RICH · CS_SINGLE · T (NLL, ref − cand): simultaneous over 1 of 1 declared members (AP → APR), family n = 64, crit 2.03.

### RICH · private_bdf (mode T, seed 3401 only) · ΔAUC (cand − ref)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| RICH · NCE · T | AP → APR | 64 | +0.003 [-0.002, +0.008] | [-0.002, +0.008] | 64 | +0.003 [-0.002, +0.008] contains 0 | 5 cell pairs, 64 identities paired |
| RICH · CS_SINGLE · T | AP → APR | 64 | +0.005 [+0.001, +0.010] | [+0.001, +0.010] | 64 | +0.005 [+0.001, +0.010] above 0 | 5 cell pairs, 64 identities paired |

- RICH · NCE · T (AUC, cand − ref): simultaneous over 1 of 1 declared members (AP → APR), family n = 64, crit 2.04.
- RICH · CS_SINGLE · T (AUC, cand − ref): simultaneous over 1 of 1 declared members (AP → APR), family n = 64, crit 2.00.

Selection levels (unit records; codes in §1): mode T: L4 ×20 (as declared 20).

## 7. CSX block (competing-talker donor extension) (seed 3401 only)

### CSX · dtu · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| CSX · NCE · T | AP → APC | 44 | +0.012 [-0.017, +0.040] | [-0.016, +0.039] | 44 | +0.012 [-0.026, +0.049] contains 0 | – | 10 cell pairs, 44 identities paired |
| CSX · NCE · T | XP → XPC | 44 | +0.012 [-0.027, +0.051] | [-0.016, +0.046] | 44 | +0.012 [-0.030, +0.053] contains 0 | – | 10 cell pairs, 44 identities paired |
| CSX · NCE · A | AP → APC | 44 | +0.100 [+0.085, +0.115] | [+0.088, +0.115] | 44 | +0.100 [+0.083, +0.117] above 0 | +0.060 [+0.052, +0.067] (n 44) | 10 cell pairs, 44 identities paired |
| CSX · NCE · A | XP → XPC | 44 | +0.020 [+0.009, +0.032] | [+0.009, +0.031] | 44 | +0.020 [+0.007, +0.034] above 0 | +0.013 [+0.007, +0.018] (n 44) | 10 cell pairs, 44 identities paired |

- CSX · NCE · T (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 44, crit 2.58.
- CSX · NCE · A (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 44, crit 2.42.

Selection levels (unit records; codes in §1): mode T: L5 ×40 (as declared 40); mode A: L1 ×40 (as declared 40).

### CSX · dtu · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| CSX · CS_SINGLE · T | AP → APC | 44 | -0.002 [-0.021, +0.017] | [-0.020, +0.015] | 44 | -0.002 [-0.023, +0.019] contains 0 | – | 10 cell pairs, 44 identities paired |
| CSX · CS_SINGLE · T | XP → XPC | 44 | -0.008 [-0.028, +0.013] | [-0.027, +0.010] | 44 | -0.008 [-0.032, +0.016] contains 0 | – | 10 cell pairs, 44 identities paired |
| CSX · CS_SINGLE · A | AP → APC | 44 | -0.011 [-0.020, -0.002] | [-0.020, -0.002] | 44 | -0.011 [-0.022, -0.001] below 0 | +0.020 [+0.014, +0.027] (n 44) | 10 cell pairs, 44 identities paired |
| CSX · CS_SINGLE · A | XP → XPC | 44 | +0.007 [-0.006, +0.020] | [-0.005, +0.019] | 44 | +0.007 [-0.008, +0.021] contains 0 | +0.011 [+0.004, +0.018] (n 44) | 10 cell pairs, 44 identities paired |

- CSX · CS_SINGLE · T (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 44, crit 2.41.
- CSX · CS_SINGLE · A (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 44, crit 2.32.

Selection levels (unit records; codes in §1): mode T: L5 ×40 (as declared 40); mode A: L1 ×40 (as declared 40).

### CSX · federici · NCE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| CSX · NCE · T | AP → APC | 86 | +0.004 [-0.009, +0.016] | [-0.009, +0.016] | 86 | +0.004 [-0.011, +0.018] contains 0 | – | 5 cell pairs, 86 identities paired |
| CSX · NCE · T | XP → XPC | 86 | -0.014 [-0.026, -0.002] | [-0.026, -0.003] | 86 | -0.014 [-0.028, -0.001] below 0 | – | 5 cell pairs, 86 identities paired |
| CSX · NCE · A | AP → APC | 86 | -0.009 [-0.029, +0.012] | [-0.029, +0.011] | 86 | -0.009 [-0.032, +0.015] contains 0 | +0.034 [+0.020, +0.047] (n 86) | 5 cell pairs, 86 identities paired |
| CSX · NCE · A | XP → XPC | 86 | +0.003 [-0.011, +0.016] | [-0.010, +0.016] | 86 | +0.003 [-0.012, +0.018] contains 0 | +0.007 [+0.003, +0.012] (n 86) | 5 cell pairs, 86 identities paired |

- CSX · NCE · T (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 86, crit 2.25.
- CSX · NCE · A (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 86, crit 2.25.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### CSX · federici · CS_SINGLE · ΔR (bits, ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | B_uni_cal Δ [95 % bootstrap-t] (n) | coverage |
|---|---|---|---|---|---|---|---|---|
| CSX · CS_SINGLE · T | AP → APC | 86 | +0.010 [-0.002, +0.022] | [-0.002, +0.022] | 86 | +0.010 [-0.004, +0.024] contains 0 | – | 5 cell pairs, 86 identities paired |
| CSX · CS_SINGLE · T | XP → XPC | 86 | -0.004 [-0.019, +0.012] | [-0.019, +0.011] | 86 | -0.004 [-0.021, +0.014] contains 0 | – | 5 cell pairs, 86 identities paired |
| CSX · CS_SINGLE · A | AP → APC | 86 | -0.005 [-0.012, +0.003] | [-0.012, +0.003] | 86 | -0.005 [-0.013, +0.004] contains 0 | +0.005 [-0.004, +0.014] (n 86) | 5 cell pairs, 86 identities paired |
| CSX · CS_SINGLE · A | XP → XPC | 86 | +0.015 [+0.003, +0.027] | [+0.003, +0.027] | 86 | +0.015 [+0.001, +0.029] above 0 | -0.001 [-0.009, +0.007] (n 86) | 5 cell pairs, 86 identities paired |

- CSX · CS_SINGLE · T (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 86, crit 2.26.
- CSX · CS_SINGLE · A (R, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 86, crit 2.30.

Selection levels (unit records; codes in §1): mode T: L5 ×20 (as declared 20); mode A: L1 ×20 (as declared 20).

### CSX · private_bdf (mode T, seed 3401 only) · ΔNLL (ref − cand)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| CSX · NCE · T | AP → APC | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | -0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · NCE · T | XP → XPC | 64 | -0.001 [-0.001, +0.000] | [-0.001, +0.000] | 64 | -0.001 [-0.001, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · CS_SINGLE · T | AP → APC | 64 | +0.000 [-0.001, +0.001] | [-0.001, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · CS_SINGLE · T | XP → XPC | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 64 | +0.000 [-0.001, +0.001] contains 0 | 5 cell pairs, 64 identities paired |

- CSX · NCE · T (NLL, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 64, crit 2.27.
- CSX · CS_SINGLE · T (NLL, ref − cand): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 64, crit 2.30.

### CSX · private_bdf (mode T, seed 3401 only) · ΔAUC (cand − ref)

| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] | coverage |
|---|---|---|---|---|---|---|---|
| CSX · NCE · T | AP → APC | 64 | -0.000 [-0.006, +0.005] | [-0.006, +0.005] | 64 | -0.000 [-0.007, +0.006] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · NCE · T | XP → XPC | 64 | -0.005 [-0.010, -0.000] | [-0.010, -0.000] | 64 | -0.005 [-0.011, +0.000] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · CS_SINGLE · T | AP → APC | 64 | +0.003 [-0.001, +0.008] | [-0.001, +0.008] | 64 | +0.003 [-0.002, +0.008] contains 0 | 5 cell pairs, 64 identities paired |
| CSX · CS_SINGLE · T | XP → XPC | 64 | +0.002 [-0.004, +0.007] | [-0.004, +0.007] | 64 | +0.002 [-0.005, +0.008] contains 0 | 5 cell pairs, 64 identities paired |

- CSX · NCE · T (AUC, cand − ref): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 64, crit 2.31.
- CSX · CS_SINGLE · T (AUC, cand − ref): simultaneous over 2 of 2 declared members (AP → APC, XP → XPC), family n = 64, crit 2.32.

Selection levels (unit records; codes in §1): mode T: L4 ×40 (as declared 40).

## 8. Selection (descriptive, pointwise)

Target side: reference = the risk-selected checkpoint (primary), candidate = the gain-selected checkpoint, in the positive-is-better convention (positive = the gain-selected checkpoint has lower risk, or higher AUC). 'identical' = the two rules chose the same epoch (difference exactly 0).

| configuration | gain-selected evaluation | endpoint | n | Δ [95 % bootstrap-t] | [95 % percentile] | coverage |
|---|---|---|---|---|---|---|
| dtu · CS_SINGLE · T · APC · d3401 · t3401 · primary | evaluated 7, identical 3 | R (ref − cand) | 44 | -0.006 [-0.019, +0.006] | [-0.019, +0.006] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · APR · d3401 · t3401 · primary | evaluated 6, identical 4 | R (ref − cand) | 44 | -0.024 [-0.036, -0.012] | [-0.035, -0.013] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · AP · d3401 · t3401 · primary | evaluated 6, identical 4 | R (ref − cand) | 44 | +0.011 [-0.001, +0.023] | [-0.000, +0.023] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · J* · d3401 · t3401 · primary | evaluated 8, identical 2 | R (ref − cand) | 44 | -0.007 [-0.020, +0.005] | [-0.019, +0.004] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · S · d- · t3401 · primary | evaluated 9, identical 1 | R (ref − cand) | 44 | -0.057 [-0.090, -0.025] | [-0.090, -0.029] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · XM · d3401 · t3401 · primary | evaluated 5, identical 5 | R (ref − cand) | 44 | +0.000 [-0.010, +0.010] | [-0.009, +0.010] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · XPC · d3401 · t3401 · primary | evaluated 7, identical 3 | R (ref − cand) | 44 | +0.007 [-0.008, +0.022] | [-0.007, +0.021] | 10 cell pairs, 44 identities paired |
| dtu · CS_SINGLE · T · XP · d3401 · t3401 · primary | evaluated 5, identical 5 | R (ref − cand) | 44 | +0.004 [-0.002, +0.010] | [-0.001, +0.009] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · APC · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.183 [-0.244, -0.122] | [-0.244, -0.130] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · APR · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.146 [-0.193, -0.099] | [-0.192, -0.102] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · AP · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.185 [-0.230, -0.140] | [-0.229, -0.143] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · J* · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.181 [-0.222, -0.139] | [-0.221, -0.142] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · S · d- · t3401 · primary | evaluated 9, identical 1 | R (ref − cand) | 44 | -0.172 [-0.222, -0.121] | [-0.221, -0.126] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · XM · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.158 [-0.200, -0.117] | [-0.199, -0.117] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · XPC · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.165 [-0.211, -0.119] | [-0.207, -0.122] | 10 cell pairs, 44 identities paired |
| dtu · NCE · T · XP · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 44 | -0.114 [-0.150, -0.077] | [-0.149, -0.081] | 10 cell pairs, 44 identities paired |
| fau · CS_SINGLE · T · APR · d3401 · t3401 · primary | evaluated 3, identical 7 | R (ref − cand) | 67 | +0.006 [-0.004, +0.016] | [-0.003, +0.015] | 10 cell pairs, 67 identities paired |
| fau · CS_SINGLE · T · AP · d3401 · t3401 · primary | evaluated 4, identical 6 | R (ref − cand) | 67 | -0.006 [-0.011, -0.001] | [-0.011, -0.001] | 10 cell pairs, 67 identities paired |
| fau · CS_SINGLE · T · J* · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | +0.009 [-0.005, +0.024] | [-0.004, +0.024] | 10 cell pairs, 67 identities paired |
| fau · CS_SINGLE · T · S · d- · t3401 · primary | evaluated 9, identical 1 | R (ref − cand) | 67 | +0.000 [-0.014, +0.015] | [-0.014, +0.014] | 10 cell pairs, 67 identities paired |
| fau · CS_SINGLE · T · XM · d3401 · t3401 · primary | evaluated 8, identical 2 | R (ref − cand) | 67 | -0.001 [-0.004, +0.003] | [-0.004, +0.003] | 10 cell pairs, 67 identities paired |
| fau · CS_SINGLE · T · XP · d3401 · t3401 · primary | evaluated 5, identical 5 | R (ref − cand) | 67 | -0.004 [-0.011, +0.002] | [-0.011, +0.001] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · APR · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.052 [-0.073, -0.031] | [-0.073, -0.032] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · AP · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.042 [-0.066, -0.017] | [-0.065, -0.017] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · J* · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.034 [-0.060, -0.009] | [-0.058, -0.009] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · S · d- · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.065 [-0.098, -0.032] | [-0.097, -0.033] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · XM · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.017 [-0.029, -0.005] | [-0.029, -0.007] | 10 cell pairs, 67 identities paired |
| fau · NCE · T · XP · d3401 · t3401 · primary | evaluated 10 | R (ref − cand) | 67 | -0.062 [-0.093, -0.031] | [-0.092, -0.032] | 10 cell pairs, 67 identities paired |
| federici · CS_SINGLE · T · APC · d3401 · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | -0.010 [-0.021, +0.001] | [-0.021, +0.001] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · APR · d3401 · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | -0.002 [-0.014, +0.009] | [-0.014, +0.008] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · AP · d3401 · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | -0.003 [-0.009, +0.003] | [-0.009, +0.002] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · J* · d3401 · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | -0.004 [-0.012, +0.004] | [-0.012, +0.003] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · S · d- · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | -0.001 [-0.011, +0.008] | [-0.011, +0.008] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · XM · d3401 · t3401 · primary | evaluated 3, identical 2 | R (ref − cand) | 86 | +0.008 [-0.001, +0.017] | [-0.000, +0.017] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · XPC · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | +0.014 [+0.002, +0.027] | [+0.002, +0.027] | 5 cell pairs, 86 identities paired |
| federici · CS_SINGLE · T · XP · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.002 [-0.009, +0.005] | [-0.009, +0.005] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · APC · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.006 [-0.024, +0.012] | [-0.025, +0.011] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · APR · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.022 [-0.040, -0.003] | [-0.040, -0.003] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · AP · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | +0.001 [-0.017, +0.019] | [-0.016, +0.019] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · J* · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.005 [-0.023, +0.012] | [-0.022, +0.012] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · S · d- · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.007 [-0.025, +0.012] | [-0.025, +0.012] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · XM · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.033 [-0.051, -0.015] | [-0.051, -0.015] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · XPC · d3401 · t3401 · primary | evaluated 4, identical 1 | R (ref − cand) | 86 | -0.004 [-0.017, +0.008] | [-0.016, +0.007] | 5 cell pairs, 86 identities paired |
| federici · NCE · T · XP · d3401 · t3401 · primary | evaluated 5 | R (ref − cand) | 86 | -0.019 [-0.036, -0.003] | [-0.035, -0.003] | 5 cell pairs, 86 identities paired |
| private_bdf · CS_SINGLE · T · APC · d3401 · t3401 · primary | evaluated 1, identical 4 | NLL (ref − cand) | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · APC · d3401 · t3401 · primary | evaluated 1, identical 4 | AUC (cand − ref) | 64 | +0.001 [-0.001, +0.003] | [-0.000, +0.003] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · APR · d3401 · t3401 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · APR · d3401 · t3401 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.000 [-0.004, +0.004] | [-0.003, +0.004] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3401 · t3401 · primary | evaluated 4, identical 1 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3401 · t3401 · primary | evaluated 4, identical 1 | AUC (cand − ref) | 64 | +0.002 [-0.001, +0.005] | [-0.001, +0.005] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3407 · t3407 · primary | evaluated 2, identical 3 | NLL (ref − cand) | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3407 · t3407 · primary | evaluated 2, identical 3 | AUC (cand − ref) | 64 | +0.001 [-0.002, +0.005] | [-0.002, +0.005] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3413 · t3413 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · AP · d3413 · t3413 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | +0.000 [-0.002, +0.002] | [-0.002, +0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3401 · t3401 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3401 · t3401 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.002 [-0.005, +0.002] | [-0.005, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3407 · t3407 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.001] | [-0.001, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3407 · t3407 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.002 [-0.004, +0.001] | [-0.004, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3413 · t3413 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · J* · d3413 · t3413 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.000 [-0.003, +0.003] | [-0.003, +0.003] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3401 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3401 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.001 [-0.006, +0.003] | [-0.006, +0.003] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3407 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.001 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3407 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.005 [-0.010, -0.000] | [-0.010, -0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3413 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | +0.000 [-0.000, +0.001] | [-0.000, +0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · S · d- · t3413 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | +0.001 [-0.002, +0.005] | [-0.002, +0.005] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3401 · t3401 · primary | evaluated 2, identical 3 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3401 · t3401 · primary | evaluated 2, identical 3 | AUC (cand − ref) | 64 | -0.001 [-0.004, +0.002] | [-0.004, +0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3407 · t3407 · primary | evaluated 2, identical 3 | NLL (ref − cand) | 64 | -0.000 [-0.000, +0.000] | [-0.000, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3407 · t3407 · primary | evaluated 2, identical 3 | AUC (cand − ref) | 64 | +0.002 [+0.000, +0.005] | [+0.001, +0.005] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3413 · t3413 · primary | evaluated 4, identical 1 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XM · d3413 · t3413 · primary | evaluated 4, identical 1 | AUC (cand − ref) | 64 | +0.002 [-0.002, +0.006] | [-0.002, +0.006] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XPC · d3401 · t3401 · primary | evaluated 1, identical 4 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, -0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XPC · d3401 · t3401 · primary | evaluated 1, identical 4 | AUC (cand − ref) | 64 | -0.002 [-0.005, +0.001] | [-0.004, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3401 · t3401 · primary | evaluated 1, identical 4 | NLL (ref − cand) | 64 | -0.000 [-0.000, +0.000] | [-0.000, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3401 · t3401 · primary | evaluated 1, identical 4 | AUC (cand − ref) | 64 | +0.000 [-0.002, +0.002] | [-0.002, +0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3407 · t3407 · primary | evaluated 2, identical 3 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3407 · t3407 · primary | evaluated 2, identical 3 | AUC (cand − ref) | 64 | +0.000 [-0.003, +0.003] | [-0.002, +0.003] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3413 · t3413 · primary | evaluated 3, identical 2 | NLL (ref − cand) | 64 | -0.000 [-0.001, +0.000] | [-0.001, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · CS_SINGLE · T · XP · d3413 · t3413 · primary | evaluated 3, identical 2 | AUC (cand − ref) | 64 | -0.000 [-0.003, +0.002] | [-0.003, +0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · APC · d3401 · t3401 · primary | evaluated 4, identical 1 | NLL (ref − cand) | 64 | -0.003 [-0.004, -0.001] | [-0.004, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · APC · d3401 · t3401 · primary | evaluated 4, identical 1 | AUC (cand − ref) | 64 | -0.022 [-0.032, -0.011] | [-0.032, -0.012] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · APR · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.003 [-0.005, -0.001] | [-0.005, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · APR · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.028 [-0.040, -0.017] | [-0.040, -0.018] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.003 [-0.005, -0.002] | [-0.005, -0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.027 [-0.036, -0.017] | [-0.036, -0.018] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3407 · t3407 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.003 [-0.005, -0.002] | [-0.005, -0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3407 · t3407 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.032 [-0.041, -0.023] | [-0.041, -0.023] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3413 · t3413 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.004, -0.001] | [-0.004, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · AP · d3413 · t3413 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.022 [-0.032, -0.012] | [-0.032, -0.012] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.004 [-0.006, -0.002] | [-0.006, -0.002] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.037 [-0.048, -0.026] | [-0.047, -0.026] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3407 · t3407 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.003 [-0.005, -0.001] | [-0.005, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3407 · t3407 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.034 [-0.044, -0.025] | [-0.043, -0.025] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3413 · t3413 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.004, -0.001] | [-0.004, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · J* · d3413 · t3413 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.021 [-0.029, -0.013] | [-0.029, -0.013] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.001 [-0.002, -0.000] | [-0.002, -0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.014 [-0.021, -0.007] | [-0.021, -0.007] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3407 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.003, -0.001] | [-0.003, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3407 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.022 [-0.030, -0.014] | [-0.030, -0.015] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3413 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.003, -0.000] | [-0.003, -0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · S · d- · t3413 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.019 [-0.027, -0.011] | [-0.027, -0.011] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.003, -0.000] | [-0.003, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.011 [-0.017, -0.004] | [-0.017, -0.004] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3407 · t3407 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.001 [-0.003, +0.000] | [-0.002, -0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3407 · t3407 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.011 [-0.018, -0.004] | [-0.018, -0.004] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3413 · t3413 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.003, -0.001] | [-0.003, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XM · d3413 · t3413 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.016 [-0.024, -0.009] | [-0.024, -0.009] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XPC · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.003, -0.001] | [-0.003, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XPC · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.019 [-0.029, -0.010] | [-0.028, -0.011] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3401 · t3401 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.002 [-0.004, -0.001] | [-0.004, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3401 · t3401 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.021 [-0.029, -0.013] | [-0.029, -0.013] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3407 · t3407 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.001 [-0.003, +0.000] | [-0.003, +0.000] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3407 · t3407 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.015 [-0.024, -0.006] | [-0.024, -0.006] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3413 · t3413 · primary | evaluated 5 | NLL (ref − cand) | 64 | -0.003 [-0.005, -0.001] | [-0.005, -0.001] | 5 cell pairs, 64 identities paired |
| private_bdf · NCE · T · XP · d3413 · t3413 · primary | evaluated 5 | AUC (cand − ref) | 64 | -0.032 [-0.042, -0.021] | [-0.042, -0.021] | 5 cell pairs, 64 identities paired |

Donor side (26 donor-group records): per member, the `_best`, `_h30` and `_gainsel` checkpoints on CE_dev (bits, lower is better), dev gain and the bridge_cal cross-entropy, with their ep-eq positions; '–' = not recorded. Every recorded selection scalar is also in the JSON (`selection.donor_groups[].values`).

**ALN3X_88f2036076b66215** · DONOR · fau · NCE · d3401 · block core · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.323 / 8.323 / 8.334 | +0.039 / +0.039 / +0.041 | 9.909 / 9.909 / 9.905 | 13 / 13 / 9 | 78874 | 0 |
| XP | 8.388 / 8.388 / 8.396 | +0.031 / +0.031 / +0.032 | 9.962 / 9.962 / 9.963 | 5 / 5 / 4 | 78874 | 0 |
| J1 | 8.347 / 8.347 / 8.364 | +0.038 / +0.038 / +0.041 | 9.874 / 9.874 / 9.903 | 1 / 1 / 7 | 78874 | 0 |
| J025 | 8.340 / 8.340 / 8.344 | +0.038 / +0.038 / +0.042 | 9.865 / 9.865 / 9.891 | 6 / 6 / 17 | 78874 | 0 |
| XM | 8.405 / 8.405 / 8.415 | +0.009 / +0.009 / +0.013 | 10.020 / 10.020 / 10.019 | 23 / 23 / 14 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.347, J025 8.340 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J025 (_gainsel gain J1 +0.041, J025 +0.042).

**ALN3X_a7c7b5aa86be0f6f** · DONOR · fau · CS_SINGLE · d3401 · block core · version primary · complete · horizon 50 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.379 / 8.379 / 8.381 | +0.034 / +0.034 / +0.035 | 9.967 / 9.967 / 9.958 | 19 / 19 / 23 | 131457 | 0 |
| XP | 8.391 / 8.402 / 8.413 | +0.019 / +0.019 / +0.020 | 9.983 / 9.985 / 9.998 | 38 / 30 / 16 | 131457 | 0 |
| J1 | 8.377 / 8.377 / 8.378 | +0.028 / +0.028 / +0.035 | 9.995 / 9.995 / 9.978 | 1 / 1 / 6 | 131457 | 0 |
| J025 | 8.383 / 8.383 / 8.383 | +0.031 / +0.031 / +0.031 | 9.939 / 9.939 / 9.939 | 6 / 6 / 6 | 131457 | 0 |
| XM | 8.397 / 8.415 / 8.401 | +0.015 / +0.004 / +0.016 | 10.027 / 10.031 / 10.026 | 41 / 1 / 39 | 131457 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.377, J025 8.383 → J1; recorded primary choice J1 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.035, J025 +0.031).

**ALN3X_55b1fb81850d3052** · DONOR · dtu · NCE · d3401 · block core · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.338 / 8.338 / 8.342 | +0.037 / +0.037 / +0.038 | 9.885 / 9.885 / 9.909 | 3 / 3 / 9 | 105165 | 0 |
| XP | 8.395 / 8.395 / 8.395 | +0.036 / +0.036 / +0.036 | 9.952 / 9.952 / 9.952 | 5 / 5 / 5 | 105165 | 0 |
| J1 | 8.347 / 8.347 / 8.347 | +0.037 / +0.037 / +0.043 | 9.965 / 9.965 / 9.900 | 25 / 25 / 15 | 105165 | 0 |
| J025 | 8.340 / 8.340 / 8.359 | +0.038 / +0.038 / +0.041 | 9.881 / 9.881 / 9.907 | 3 / 3 / 29 | 105165 | 0 |
| XM | 8.420 / 8.420 / 8.425 | +0.010 / +0.010 / +0.010 | 10.024 / 10.024 / 10.032 | 3 / 3 / 5 | 105165 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.347, J025 8.340 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.043, J025 +0.041).

**ALN3X_b1245dcd72706d2c** · DONOR · dtu · CS_SINGLE · d3401 · block core · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.370 / 8.370 / 8.375 | +0.034 / +0.034 / +0.035 | 9.956 / 9.956 / 9.961 | 23 / 23 / 22 | 78874 | 0 |
| XP | 8.409 / 8.409 / 8.409 | +0.019 / +0.019 / +0.019 | 10.031 / 10.031 / 10.031 | 14 / 14 / 14 | 78874 | 0 |
| J1 | 8.388 / 8.388 / 8.399 | +0.026 / +0.026 / +0.028 | 9.962 / 9.962 / 9.990 | 30 / 30 / 23 | 78874 | 0 |
| J025 | 8.383 / 8.383 / 8.393 | +0.029 / +0.029 / +0.031 | 9.953 / 9.953 / 9.958 | 18 / 18 / 9 | 78874 | 0 |
| XM | 8.414 / 8.414 / 8.426 | +0.008 / +0.008 / +0.011 | 10.021 / 10.021 / 10.026 | 8 / 8 / 3 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.388, J025 8.383 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J025 (_gainsel gain J1 +0.028, J025 +0.031).

**ALN3X_d07616eea37acb73** · DONOR · federici · NCE · d3401 · block core · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.329 / 8.329 / 8.347 | +0.035 / +0.035 / +0.039 | 9.919 / 9.919 / 9.937 | 15 / 15 / 4 | 78874 | 0 |
| XP | 8.390 / 8.390 / 8.392 | +0.029 / +0.029 / +0.036 | 9.962 / 9.962 / 9.963 | 5 / 5 / 2 | 78874 | 0 |
| J1 | 8.336 / 8.336 / 8.336 | +0.050 / +0.050 / +0.050 | 9.937 / 9.937 / 9.937 | 15 / 15 / 15 | 78874 | 0 |
| J025 | 8.344 / 8.344 / 8.351 | +0.035 / +0.035 / +0.040 | 9.902 / 9.902 / 9.933 | 1 / 1 / 4 | 78874 | 0 |
| XM | 8.418 / 8.418 / 8.421 | +0.008 / +0.008 / +0.022 | 9.998 / 9.998 / 10.042 | 1 / 1 / 7 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.336, J025 8.344 → J1; recorded primary choice J1 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.050, J025 +0.040).

**ALN3X_be950eabd3b5ab77** · DONOR · federici · CS_SINGLE · d3401 · block core · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.379 / 8.379 / 8.380 | +0.030 / +0.030 / +0.034 | 9.975 / 9.975 / 9.965 | 23 / 23 / 19 | 105165 | 0 |
| XP | 8.406 / 8.406 / 8.406 | +0.022 / +0.022 / +0.022 | 9.982 / 9.982 / 9.982 | 26 / 26 / 26 | 105165 | 0 |
| J1 | 8.381 / 8.383 / 8.382 | +0.029 / +0.028 / +0.031 | 9.952 / 9.939 / 9.950 | 39 / 30 / 30 | 105165 | 0 |
| J025 | 8.375 / 8.375 / 8.384 | +0.032 / +0.032 / +0.035 | 9.942 / 9.942 / 9.951 | 8 / 8 / 11 | 105165 | 0 |
| XM | 8.409 / 8.409 / 8.421 | +0.016 / +0.016 / +0.021 | 10.025 / 10.025 / 10.015 | 25 / 25 / 9 | 105165 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.381, J025 8.375 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J025 (_gainsel gain J1 +0.031, J025 +0.035).

**ALN3X_01f0b9a2dbe53328** · DONOR · private_bdf · NCE · d3401 · block core · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.330 / 8.330 / 8.337 | +0.036 / +0.036 / +0.039 | 9.926 / 9.926 / 9.904 | 12 / 12 / 7 | 78874 | 0 |
| XP | 8.396 / 8.396 / 8.396 | +0.034 / +0.034 / +0.034 | 9.939 / 9.939 / 9.939 | 5 / 5 / 5 | 78874 | 0 |
| J1 | 8.358 / 8.358 / 8.364 | +0.037 / +0.037 / +0.046 | 9.872 / 9.872 / 9.951 | 1 / 1 / 18 | 78874 | 0 |
| J025 | 8.341 / 8.341 / 8.354 | +0.036 / +0.036 / +0.042 | 9.874 / 9.874 / 9.898 | 4 / 4 / 18 | 78874 | 0 |
| XM | 8.402 / 8.402 / 8.424 | +0.014 / +0.014 / +0.017 | 10.005 / 10.005 / 10.042 | 27 / 27 / 6 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.358, J025 8.341 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.046, J025 +0.042).

**ALN3X_94ec2e5731b76a95** · DONOR · private_bdf · CS_SINGLE · d3401 · block core · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.375 / 8.375 / 8.375 | +0.036 / +0.036 / +0.036 | 9.961 / 9.961 / 9.961 | 23 / 23 / 23 | 78874 | 0 |
| XP | 8.406 / 8.406 / 8.406 | +0.017 / +0.017 / +0.017 | 10.037 / 10.037 / 10.037 | 3 / 3 / 3 | 78874 | 0 |
| J1 | 8.381 / 8.381 / 8.386 | +0.029 / +0.029 / +0.031 | 9.968 / 9.968 / 9.963 | 7 / 7 / 22 | 78874 | 0 |
| J025 | 8.387 / 8.387 / 8.387 | +0.028 / +0.028 / +0.029 | 9.963 / 9.963 / 9.966 | 30 / 30 / 21 | 78874 | 0 |
| XM | 8.397 / 8.397 / 8.397 | +0.022 / +0.022 / +0.022 | 10.013 / 10.013 / 10.013 | 2 / 2 / 2 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.381, J025 8.387 → J1; recorded primary choice J1 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.031, J025 +0.029).

**ALN3X_89596ce9168aa591** · DONOR · private_bdf · NCE · d3407 · block panel · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.326 / 8.326 / 8.341 | +0.030 / +0.030 / +0.038 | 9.891 / 9.891 / 9.920 | 2 / 2 / 9 | 78874 | 0 |
| XP | 8.402 / 8.402 / 8.402 | +0.034 / +0.034 / +0.034 | 9.946 / 9.946 / 9.946 | 8 / 8 / 8 | 78874 | 0 |
| J1 | 8.346 / 8.346 / 8.346 | +0.049 / +0.049 / +0.049 | 9.922 / 9.922 / 9.922 | 23 / 23 / 23 | 78874 | 0 |
| J025 | 8.336 / 8.336 / 8.350 | +0.030 / +0.030 / +0.040 | 9.874 / 9.874 / 9.904 | 2 / 2 / 9 | 78874 | 0 |
| XM | 8.405 / 8.405 / 8.411 | +0.007 / +0.007 / +0.014 | 10.027 / 10.027 / 10.030 | 13 / 13 / 11 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.346, J025 8.336 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.049, J025 +0.040).

**ALN3X_6e44b06d8d0cf570** · DONOR · private_bdf · NCE · d3413 · block panel · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.325 / 8.325 / 8.349 | +0.035 / +0.035 / +0.038 | 9.893 / 9.893 / 9.939 | 1 / 1 / 15 | 78874 | 0 |
| XP | 8.398 / 8.398 / 8.398 | +0.031 / +0.031 / +0.031 | 9.958 / 9.958 / 9.958 | 2 / 2 / 2 | 78874 | 0 |
| J1 | 8.352 / 8.352 / 8.366 | +0.040 / +0.040 / +0.043 | 9.912 / 9.912 / 9.939 | 1 / 1 / 14 | 78874 | 0 |
| J025 | 8.327 / 8.327 / 8.347 | +0.036 / +0.036 / +0.039 | 9.890 / 9.890 / 9.874 | 1 / 1 / 5 | 78874 | 0 |
| XM | 8.405 / 8.405 / 8.405 | +0.016 / +0.016 / +0.016 | 10.021 / 10.021 / 10.021 | 15 / 15 / 15 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.352, J025 8.327 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.043, J025 +0.039).

**ALN3X_854f5a0d6cc5bf95** · DONOR · private_bdf · CS_SINGLE · d3407 · block panel · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.381 / 8.381 / 8.383 | +0.032 / +0.032 / +0.032 | 9.964 / 9.964 / 9.983 | 30 / 30 / 17 | 78874 | 0 |
| XP | 8.421 / 8.421 / 8.423 | +0.009 / +0.009 / +0.020 | 10.016 / 10.016 / 9.986 | 1 / 1 / 22 | 78874 | 0 |
| J1 | 8.384 / 8.384 / 8.384 | +0.034 / +0.034 / +0.034 | 9.958 / 9.958 / 9.958 | 19 / 19 / 19 | 78874 | 0 |
| J025 | 8.381 / 8.381 / 8.385 | +0.029 / +0.029 / +0.033 | 9.965 / 9.965 / 9.986 | 12 / 12 / 9 | 78874 | 0 |
| XM | 8.401 / 8.401 / 8.405 | +0.022 / +0.022 / +0.024 | 10.004 / 10.004 / 10.012 | 2 / 2 / 10 | 78874 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.384, J025 8.381 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.034, J025 +0.033).

**ALN3X_8f7d593b35d2d03e** · DONOR · private_bdf · CS_SINGLE · d3413 · block panel · version primary · complete · horizon 50 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| AP | 8.374 / 8.378 / 8.383 | +0.033 / +0.034 / +0.035 | 9.967 / 9.976 / 9.977 | 35 / 19 / 29 | 131457 | 0 |
| XP | 8.406 / 8.407 / 8.412 | +0.029 / +0.030 / +0.031 | 10.007 / 9.992 / 9.998 | 44 / 28 / 29 | 131457 | 0 |
| J1 | 8.379 / 8.379 / 8.379 | +0.037 / +0.037 / +0.037 | 9.970 / 9.970 / 9.970 | 19 / 19 / 19 | 131457 | 0 |
| J025 | 8.372 / 8.376 / 8.379 | +0.034 / +0.036 / +0.037 | 9.978 / 9.978 / 9.974 | 36 / 28 / 26 | 131457 | 0 |
| XM | 8.397 / 8.397 / 8.398 | +0.025 / +0.025 / +0.032 | 10.025 / 10.025 / 10.038 | 9 / 9 / 32 | 131457 | 0 |

λ (rule min_dev_ce_tie1e-4_lambda1, recomputed with select): CE_dev J1 8.379, J025 8.372 → J025; recorded primary choice J025 (agrees); recorded gain-rule choice J1 (_gainsel gain J1 +0.037, J025 +0.037).

**ALN3X_eea7db6b831b5fc9** · RICH_DONOR · fau · NCE · d3401 · block rich · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.325 / 8.325 / 8.337 | +0.037 / +0.037 / +0.040 | 9.893 / 9.893 / 9.900 | 13 / 13 / 9 | 78874 | 0 |

**ALN3X_6ce965c57f3a4733** · RICH_DONOR · fau · CS_SINGLE · d3401 · block rich · version primary · complete · horizon 50 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.368 / 8.368 / 8.377 | +0.032 / +0.032 / +0.033 | 9.971 / 9.964 / 9.957 | 29 / 29 / 7 | 131457 | 0 |

**ALN3X_71d01d4ba70a5061** · RICH_DONOR · dtu · NCE · d3401 · block rich · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.330 / 8.330 / 8.340 | +0.037 / +0.037 / +0.041 | 9.908 / 9.908 / 9.930 | 13 / 13 / 29 | 105165 | 0 |

**ALN3X_3acc115e95a7bcbd** · RICH_DONOR · dtu · CS_SINGLE · d3401 · block rich · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.372 / 8.372 / 8.373 | +0.030 / +0.030 / +0.034 | 9.955 / 9.955 / 9.951 | 6 / 6 / 23 | 78874 | 0 |

**ALN3X_daead7fb9f58aec2** · RICH_DONOR · federici · NCE · d3401 · block rich · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.322 / 8.322 / 8.322 | +0.037 / +0.037 / +0.041 | 9.914 / 9.914 / 9.936 | 15 / 15 / 21 | 78874 | 0 |

**ALN3X_82d99381df20ecfd** · RICH_DONOR · federici · CS_SINGLE · d3401 · block rich · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.377 / 8.377 / 8.380 | +0.032 / +0.032 / +0.033 | 9.969 / 9.969 / 9.972 | 21 / 21 / 37 | 105165 | 0 |

**ALN3X_9d2b683a00a9e211** · RICH_DONOR · private_bdf · NCE · d3401 · block rich · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.330 / 8.330 / 8.344 | +0.035 / +0.035 / +0.038 | 9.899 / 9.899 / 9.885 | 4 / 4 / 3 | 78874 | 0 |

**ALN3X_e37acffb01d551f2** · RICH_DONOR · private_bdf · CS_SINGLE · d3401 · block rich · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APR | 8.361 / 8.361 / 8.361 | +0.038 / +0.038 / +0.038 | 9.953 / 9.953 / 9.953 | 23 / 23 / 23 | 78874 | 0 |

**ALN3X_5b47b40a3e6af7dd** · CSX_DONOR · dtu · NCE · d3401 · block csx · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.318 / 8.318 / 8.347 | +0.036 / +0.036 / +0.037 | 9.907 / 9.907 / 9.932 | 12 / 12 / 14 | 105165 | 0 |
| XPC | 8.395 / 8.395 / 8.400 | +0.032 / +0.032 / +0.037 | 9.974 / 9.974 / 9.978 | 2 / 2 / 14 | 105165 | 0 |

**ALN3X_3873346b0fa9ff57** · CSX_DONOR · dtu · CS_SINGLE · d3401 · block csx · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.377 / 8.377 / 8.384 | +0.032 / +0.032 / +0.033 | 9.965 / 9.965 / 9.965 | 29 / 29 / 19 | 78874 | 0 |
| XPC | 8.386 / 8.386 / 8.391 | +0.025 / +0.025 / +0.028 | 10.026 / 10.026 / 10.032 | 1 / 1 / 2 | 78874 | 0 |

**ALN3X_92fdde954f1d8fc4** · CSX_DONOR · federici · NCE · d3401 · block csx · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.328 / 8.328 / 8.341 | +0.037 / +0.037 / +0.040 | 9.928 / 9.928 / 9.941 | 12 / 12 / 20 | 78874 | 0 |
| XPC | 8.379 / 8.379 / 8.379 | +0.042 / +0.042 / +0.042 | 9.963 / 9.963 / 9.963 | 7 / 7 / 7 | 78874 | 0 |

**ALN3X_59f5d2966ae30cb7** · CSX_DONOR · federici · CS_SINGLE · d3401 · block csx · version primary · complete · horizon 40 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.382 / 8.382 / 8.382 | +0.032 / +0.032 / +0.034 | 9.970 / 9.970 / 9.968 | 20 / 20 / 12 | 105165 | 0 |
| XPC | 8.395 / 8.395 / 8.395 | +0.032 / +0.032 / +0.032 | 10.009 / 10.009 / 10.009 | 15 / 15 / 15 | 105165 | 0 |

**ALN3X_e999119e056a012f** · CSX_DONOR · private_bdf · NCE · d3401 · block csx · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.324 / 8.324 / 8.324 | +0.038 / +0.038 / +0.038 | 9.907 / 9.907 / 9.907 | 12 / 12 / 12 | 78874 | 0 |
| XPC | 8.394 / 8.394 / 8.400 | +0.032 / +0.032 / +0.037 | 9.932 / 9.932 / 9.945 | 7 / 7 / 8 | 78874 | 0 |

**ALN3X_6f687f8d81261af7** · CSX_DONOR · private_bdf · CS_SINGLE · d3401 · block csx · version primary · complete · horizon 30 ep-eq · compute limit 60 · ceiling reached while improving: false

| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |
|---|---|---|---|---|---|---|
| APC | 8.380 / 8.380 / 8.392 | +0.032 / +0.032 / +0.032 | 9.962 / 9.962 / 9.967 | 23 / 23 / 19 | 78874 | 0 |
| XPC | 8.406 / 8.406 / 8.411 | +0.019 / +0.019 / +0.019 | 10.018 / 10.018 / 10.026 | 17 / 17 / 2 | 78874 | 0 |

Bridges (68 records; descriptive): 

| record | donor group | slot · member | cohort · objective | d seed | version | status | α_uni | α_nat | bridge_cal r | τ_cal | artefact probe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALN3X_91b6518381866d2d | ALN3X_88f2036076b66215 | AP · AP (agrees) | fau · NCE | 3401 | primary | complete | 10.000 | – | 0.048 | 0.325 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.130; r_own -0.002; r_own_minus_other -0.004; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_c0b924bf9b3ef476 | ALN3X_88f2036076b66215 | XP · XP (agrees) | fau · NCE | 3401 | primary | complete | 1000.000 | – | 0.049 | 0.833 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.135; r_own -0.014; r_own_minus_other -0.015; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_a50caa53c5f662f9 | ALN3X_88f2036076b66215 | J* · J025 (agrees) | fau · NCE | 3401 | primary | complete | 100.000 | – | 0.056 | 0.323 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.123; r_own -0.005; r_own_minus_other -0.007; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_09ff6b28b6502976 | ALN3X_88f2036076b66215 | XM · XM (agrees) | fau · NCE | 3401 | primary | complete | 0.000 | – | 0.025 | 0.880 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other -0.000; r_other_sd 0.115; r_own 0.026; r_own_minus_other 0.026; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_607cbd1c80b559ab | ALN3X_a7c7b5aa86be0f6f | AP · AP (agrees) | fau · CS_SINGLE | 3401 | primary | complete | 100000.000 | 1000.000 | 0.049 | 0.410 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.140; r_own -0.011; r_own_minus_other -0.012; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_5523f9cfde833a78 | ALN3X_a7c7b5aa86be0f6f | XP · XP (agrees) | fau · CS_SINGLE | 3401 | primary | complete | 1000.000 | 100.000 | 0.028 | 0.405 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.083; r_own -0.005; r_own_minus_other -0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_1aed264d25ea5759 | ALN3X_a7c7b5aa86be0f6f | J* · J1 (agrees) | fau · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.034 | 0.778 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.120; r_own 0.011; r_own_minus_other 0.010; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_1c945b0de417455a | ALN3X_a7c7b5aa86be0f6f | XM · XM (agrees) | fau · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.016 | 0.311 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.065; r_own 0.006; r_own_minus_other 0.006; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_c0c160fc0ca4872e | ALN3X_55b1fb81850d3052 | AP · AP (agrees) | dtu · NCE | 3401 | primary | complete | 100.000 | – | 0.052 | 0.441 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.118; r_own 0.009; r_own_minus_other 0.008; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_b13ef2c4d13996b6 | ALN3X_55b1fb81850d3052 | XP · XP (agrees) | dtu · NCE | 3401 | primary | complete | 1000.000 | – | 0.049 | 0.616 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.141; r_own -0.014; r_own_minus_other -0.014; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_b3894969992b11c8 | ALN3X_55b1fb81850d3052 | J* · J025 (agrees) | dtu · NCE | 3401 | primary | complete | 100.000 | – | 0.053 | 0.370 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.119; r_own 0.009; r_own_minus_other 0.007; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_03dbb89221c5ac18 | ALN3X_55b1fb81850d3052 | XM · XM (agrees) | dtu · NCE | 3401 | primary | complete | 1.000 | – | 0.017 | 0.608 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other -0.000; r_other_sd 0.111; r_own -0.010; r_own_minus_other -0.010; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_66275fca4ee37cdc | ALN3X_b1245dcd72706d2c | AP · AP (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 1000.000 | 1000.000 | 0.052 | 0.408 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.139; r_own 0.003; r_own_minus_other 0.002; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_6e2ac475ae52b081 | ALN3X_b1245dcd72706d2c | XP · XP (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 0.000 | 1000.000 | 0.024 | 0.646 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.106; r_own -0.002; r_own_minus_other -0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_752be573b571b353 | ALN3X_b1245dcd72706d2c | J* · J025 (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 100000000.000 | 1000.000 | 0.049 | 0.529 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.139; r_own 0.004; r_own_minus_other 0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_7598f1fc78f318fa | ALN3X_b1245dcd72706d2c | XM · XM (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 0.000 | 0.001 | 0.021 | 0.634 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other -0.000; r_other_sd 0.089; r_own 0.014; r_own_minus_other 0.014; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_be5edecb0af12ee1 | ALN3X_d07616eea37acb73 | AP · AP (agrees) | federici · NCE | 3401 | primary | complete | 0.100 | – | 0.047 | 0.305 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.129; r_own 0.000; r_own_minus_other -0.002; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_38efebdff4ac837d | ALN3X_d07616eea37acb73 | XP · XP (agrees) | federici · NCE | 3401 | primary | complete | 100.000 | – | 0.052 | 0.826 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.135; r_own -0.011; r_own_minus_other -0.011; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_280a5dcbe1f1e536 | ALN3X_d07616eea37acb73 | J* · J1 (agrees) | federici · NCE | 3401 | primary | complete | 100000000.000 | – | 0.050 | 0.505 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.121; r_own -0.007; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_57e37130bfb4cacc | ALN3X_d07616eea37acb73 | XM · XM (agrees) | federici · NCE | 3401 | primary | complete | 100.000 | – | 0.021 | 0.536 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other -0.000; r_other_sd 0.089; r_own 0.019; r_own_minus_other 0.019; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_f2a33fb017be91d0 | ALN3X_be950eabd3b5ab77 | AP · AP (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 0.000 | 1000.000 | 0.045 | 0.475 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.133; r_own -0.001; r_own_minus_other -0.002; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_25691aebb67950c1 | ALN3X_be950eabd3b5ab77 | XP · XP (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 100000.000 | 0.001 | 0.028 | 0.697 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.107; r_own -0.009; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_bf75d9bdf98b2170 | ALN3X_be950eabd3b5ab77 | J* · J025 (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.051 | 0.636 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.135; r_own 0.010; r_own_minus_other 0.008; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_26ca4857dcae5f77 | ALN3X_be950eabd3b5ab77 | XM · XM (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 1000.000 | 1000.000 | 0.022 | 1.539 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.114; r_own 0.027; r_own_minus_other 0.026; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_ef3e49207c61102c | ALN3X_01f0b9a2dbe53328 | AP · AP (agrees) | private_bdf · NCE | 3401 | primary | complete | 0.100 | – | 0.047 | 0.374 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.135; r_own 0.010; r_own_minus_other 0.008; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_8e4954e0eda63273 | ALN3X_01f0b9a2dbe53328 | XP · XP (agrees) | private_bdf · NCE | 3401 | primary | complete | 1000.000 | – | 0.050 | 0.722 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own -0.012; r_own_minus_other -0.013; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_1e5d72c06d178deb | ALN3X_01f0b9a2dbe53328 | J* · J025 (agrees) | private_bdf · NCE | 3401 | primary | complete | 100.000 | – | 0.054 | 0.305 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.118; r_own -0.001; r_own_minus_other -0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_44d01c41e88d3161 | ALN3X_01f0b9a2dbe53328 | XM · XM (agrees) | private_bdf · NCE | 3401 | primary | complete | 0.000 | – | 0.028 | 1.148 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.118; r_own 0.020; r_own_minus_other 0.020; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_e762c24d7b9c553c | ALN3X_94ec2e5731b76a95 | AP · AP (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 1000.000 | 1000.000 | 0.047 | 0.401 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own 0.007; r_own_minus_other 0.006; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_b0155feeb2a0f149 | ALN3X_94ec2e5731b76a95 | XP · XP (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 100000000.000 | 1000.000 | 0.014 | 2.033 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.098; r_own -0.005; r_own_minus_other -0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_73dd2039f55377e5 | ALN3X_94ec2e5731b76a95 | J* · J1 (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 100000000.000 | 1000.000 | 0.042 | 0.459 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.126; r_own 0.007; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_998a34728a3ebfa1 | ALN3X_94ec2e5731b76a95 | XM · XM (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 10000.000 | 0.001 | 0.026 | 0.741 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other -0.000; r_other_sd 0.092; r_own 0.010; r_own_minus_other 0.010; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_6ee4caceedad9251 | ALN3X_89596ce9168aa591 | AP · AP (agrees) | private_bdf · NCE | 3407 | primary | complete | 0.000 | – | 0.048 | 0.356 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.134; r_own 0.005; r_own_minus_other 0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_eea71594875fa59c | ALN3X_89596ce9168aa591 | XP · XP (agrees) | private_bdf · NCE | 3407 | primary | complete | 1000.000 | – | 0.049 | 0.608 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.139; r_own -0.008; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_46d3a83c360e2d7c | ALN3X_89596ce9168aa591 | J* · J025 (agrees) | private_bdf · NCE | 3407 | primary | complete | 1.000 | – | 0.049 | 0.368 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.132; r_own 0.003; r_own_minus_other 0.002; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_480202067a0e37ef | ALN3X_89596ce9168aa591 | XM · XM (agrees) | private_bdf · NCE | 3407 | primary | complete | 0.000 | – | 0.019 | 2.157 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.103; r_own 0.005; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_f010162f241cbf43 | ALN3X_6e44b06d8d0cf570 | AP · AP (agrees) | private_bdf · NCE | 3413 | primary | complete | 10.000 | – | 0.049 | 0.255 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.124; r_own 0.001; r_own_minus_other 0.000; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_0b8fc9fa75c36f6b | ALN3X_6e44b06d8d0cf570 | XP · XP (agrees) | private_bdf · NCE | 3413 | primary | complete | 100.000 | – | 0.049 | 0.697 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.135; r_own -0.010; r_own_minus_other -0.011; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_75d38e03ee25134d | ALN3X_6e44b06d8d0cf570 | J* · J025 (agrees) | private_bdf · NCE | 3413 | primary | complete | 10.000 | – | 0.050 | 0.259 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.125; r_own 0.002; r_own_minus_other 0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_ceca42dd7abe3827 | ALN3X_6e44b06d8d0cf570 | XM · XM (agrees) | private_bdf · NCE | 3413 | primary | complete | 0.000 | – | 0.027 | 1.095 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.100; r_own 0.020; r_own_minus_other 0.019; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_4ac836b6fdca8b69 | ALN3X_854f5a0d6cc5bf95 | AP · AP (agrees) | private_bdf · CS_SINGLE | 3407 | primary | complete | 1000.000 | 0.001 | 0.049 | 0.549 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.138; r_own 0.006; r_own_minus_other 0.004; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_d6e74510fc3640e8 | ALN3X_854f5a0d6cc5bf95 | XP · XP (agrees) | private_bdf · CS_SINGLE | 3407 | primary | complete | 100.000 | 1000.000 | 0.020 | 0.688 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.118; r_own 0.010; r_own_minus_other 0.008; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_c8bea2a7148b50bf | ALN3X_854f5a0d6cc5bf95 | J* · J025 (agrees) | private_bdf · CS_SINGLE | 3407 | primary | complete | 10000.000 | 1000.000 | 0.051 | 0.662 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.141; r_own 0.004; r_own_minus_other 0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_18119d2d1957c7d5 | ALN3X_854f5a0d6cc5bf95 | XM · XM (agrees) | private_bdf · CS_SINGLE | 3407 | primary | complete | 10000.000 | 1000.000 | 0.024 | 1.012 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.000; r_other_sd 0.109; r_own 0.015; r_own_minus_other 0.014; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_51310b390fd76a5d | ALN3X_8f7d593b35d2d03e | AP · AP (agrees) | private_bdf · CS_SINGLE | 3413 | primary | complete | 1000.000 | 100.000 | 0.048 | 0.473 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own 0.001; r_own_minus_other 0.000; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_16ceede8c7de9d18 | ALN3X_8f7d593b35d2d03e | XP · XP (agrees) | private_bdf · CS_SINGLE | 3413 | primary | complete | 0.000 | 0.001 | 0.038 | 0.238 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.124; r_own -0.019; r_own_minus_other -0.019; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_e3f03e5e64ce6905 | ALN3X_8f7d593b35d2d03e | J* · J025 (agrees) | private_bdf · CS_SINGLE | 3413 | primary | complete | 0.000 | 1000.000 | 0.046 | 0.469 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own 0.008; r_own_minus_other 0.007; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_3473c07b679a1c88 | ALN3X_8f7d593b35d2d03e | XM · XM (agrees) | private_bdf · CS_SINGLE | 3413 | primary | complete | 0.000 | 0.001 | 0.027 | 1.195 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.117; r_own 0.006; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_0e4127c91d91a013 | ALN3X_eea7db6b831b5fc9 | APR · APR (agrees) | fau · NCE | 3401 | primary | complete | 10.000 | – | 0.050 | 0.323 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.129; r_own -0.002; r_own_minus_other -0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_ea5964b544f53606 | ALN3X_6ce965c57f3a4733 | APR · APR (agrees) | fau · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.044 | 0.398 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.141; r_own -0.008; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_0ff2b6a083ad12e4 | ALN3X_71d01d4ba70a5061 | APR · APR (agrees) | dtu · NCE | 3401 | primary | complete | 0.100 | – | 0.049 | 0.363 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own 0.006; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_12a6abd9707c5028 | ALN3X_3acc115e95a7bcbd | APR · APR (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 100000.000 | 1000.000 | 0.052 | 0.447 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.137; r_own 0.008; r_own_minus_other 0.006; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_4528c55d52c2fbdc | ALN3X_daead7fb9f58aec2 | APR · APR (agrees) | federici · NCE | 3401 | primary | complete | 0.100 | – | 0.049 | 0.313 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.129; r_own 0.003; r_own_minus_other 0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_7e90056232478878 | ALN3X_82d99381df20ecfd | APR · APR (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 0.000 | 1000.000 | 0.046 | 0.402 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.130; r_own 0.002; r_own_minus_other 0.000; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_c52bd37f5ab031fd | ALN3X_9d2b683a00a9e211 | APR · APR (agrees) | private_bdf · NCE | 3401 | primary | complete | 0.100 | – | 0.048 | 0.430 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.135; r_own 0.004; r_own_minus_other 0.002; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_748774b206de9ebb | ALN3X_e37acffb01d551f2 | APR · APR (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 100.000 | 1000.000 | 0.052 | 0.399 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.134; r_own 0.001; r_own_minus_other -0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_2885d125c42f38f6 | ALN3X_5b47b40a3e6af7dd | APC · APC (agrees) | dtu · NCE | 3401 | primary | complete | 100.000 | – | 0.050 | 0.427 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.121; r_own 0.000; r_own_minus_other -0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_983a5989c02bdc4f | ALN3X_5b47b40a3e6af7dd | XPC · XPC (agrees) | dtu · NCE | 3401 | primary | complete | 1000.000 | – | 0.043 | 0.774 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.139; r_own -0.008; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_05331ca5c4531e20 | ALN3X_3873346b0fa9ff57 | APC · APC (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.047 | 0.474 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.140; r_own 0.004; r_own_minus_other 0.003; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_a4ef9c81d2d83278 | ALN3X_3873346b0fa9ff57 | XPC · XPC (agrees) | dtu · CS_SINGLE | 3401 | primary | complete | 0.000 | 1000.000 | 0.022 | 1.637 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.108; r_own 0.006; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_0e2de8b91e26f7df | ALN3X_92fdde954f1d8fc4 | APC · APC (agrees) | federici · NCE | 3401 | primary | complete | 0.010 | – | 0.050 | 0.387 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.131; r_own 0.002; r_own_minus_other 0.000; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_c50912adeaa1b4ee | ALN3X_92fdde954f1d8fc4 | XPC · XPC (agrees) | federici · NCE | 3401 | primary | complete | 1000.000 | – | 0.053 | 0.940 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.129; r_own -0.008; r_own_minus_other -0.009; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_69f6052878180fb9 | ALN3X_59f5d2966ae30cb7 | APC · APC (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.046 | 0.469 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.133; r_own -0.006; r_own_minus_other -0.007; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_3f740fd7530e50d0 | ALN3X_59f5d2966ae30cb7 | XPC · XPC (agrees) | federici · CS_SINGLE | 3401 | primary | complete | 0.000 | 1000.000 | 0.021 | 1.667 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.111; r_own 0.015; r_own_minus_other 0.014; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_7e9e9e6816c4dec0 | ALN3X_e999119e056a012f | APC · APC (agrees) | private_bdf · NCE | 3401 | primary | complete | 0.100 | – | 0.050 | 0.379 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.135; r_own 0.001; r_own_minus_other -0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_417e8fc71164f23a | ALN3X_e999119e056a012f | XPC · XPC (agrees) | private_bdf · NCE | 3401 | primary | complete | 1000.000 | – | 0.056 | 0.525 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.139; r_own 0.003; r_own_minus_other 0.001; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_4d7ffa5c9a0e2c75 | ALN3X_6f687f8d81261af7 | APC · APC (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 10000.000 | 1000.000 | 0.048 | 0.474 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.002; r_other_sd 0.137; r_own 0.006; r_own_minus_other 0.005; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |
| ALN3X_91412bec70ed79cd | ALN3X_6f687f8d81261af7 | XPC · XPC (agrees) | private_bdf · CS_SINGLE | 3401 | primary | complete | 100000000.000 | 0.001 | 0.031 | 0.416 | min_separation_samples 455.000; n_other_candidates 575.000; n_other_pairs 30407.000; n_segments 54.000; n_segments_with_other 54.000; r_other 0.001; r_other_sd 0.113; r_own 0.011; r_own_minus_other 0.010; readout B_uni (frozen); role control_artefact; status computed; use descriptive (risk 3); never used for any selection |

J* resolution and the member check of the downstream J* units:

| donor group | cohort · objective · d seed · version | λ rule → | recorded primary | check | downstream J* units | members used |
|---|---|---|---|---|---|---|
| ALN3X_01f0b9a2dbe53328 | private_bdf · NCE · d3401 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5 | J025 6 |
| ALN3X_55b1fb81850d3052 | dtu · NCE · d3401 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 10; zero_shot: agrees 20 | J025 31 |
| ALN3X_6e44b06d8d0cf570 | private_bdf · NCE · d3413 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5 | J025 6 |
| ALN3X_854f5a0d6cc5bf95 | private_bdf · CS_SINGLE · d3407 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5 | J025 6 |
| ALN3X_88f2036076b66215 | fau · NCE · d3401 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 10; zero_shot: agrees 30 | J025 41 |
| ALN3X_89596ce9168aa591 | private_bdf · NCE · d3407 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5 | J025 6 |
| ALN3X_8f7d593b35d2d03e | private_bdf · CS_SINGLE · d3413 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5 | J025 6 |
| ALN3X_94ec2e5731b76a95 | private_bdf · CS_SINGLE · d3401 · primary | J1 | J1 | agrees | bridge: agrees 1; target: agrees 5 | J1 6 |
| ALN3X_a7c7b5aa86be0f6f | fau · CS_SINGLE · d3401 · primary | J1 | J1 | agrees | bridge: agrees 1; target: agrees 10; zero_shot: agrees 30 | J1 41 |
| ALN3X_b1245dcd72706d2c | dtu · CS_SINGLE · d3401 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 10; zero_shot: agrees 20 | J025 31 |
| ALN3X_be950eabd3b5ab77 | federici · CS_SINGLE · d3401 · primary | J025 | J025 | agrees | bridge: agrees 1; target: agrees 5; zero_shot: agrees 10 | J025 16 |
| ALN3X_d07616eea37acb73 | federici · NCE · d3401 · primary | J1 | J1 | agrees | bridge: agrees 1; target: agrees 5; zero_shot: agrees 10 | J1 16 |

## 9. Secondary endpoints (pointwise, on each member's own paired identities)

**INIT · fau · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| S → AP | +0.102 [+0.069, +0.134] pct [+0.069, +0.132] (n 67) | -0.097 [-0.117, -0.076] pct [-0.117, -0.077] (n 67) | -0.000 [-0.004, +0.004] pct [-0.004, +0.004] (n 67) | +0.004 [-0.001, +0.008] pct [-0.001, +0.008] (n 67) | +0.003 [-0.024, +0.029] pct [-0.025, +0.026] (n 67) | +0.010 [-0.025, +0.045] pct [-0.027, +0.042] (n 67) | +0.002 [-0.003, +0.008] pct [-0.003, +0.008] (n 67) |
| S → XP | +0.022 [-0.000, +0.044] pct [+0.001, +0.045] (n 67) | -0.011 [-0.024, +0.002] pct [-0.025, +0.002] (n 67) | -0.002 [-0.007, +0.002] pct [-0.007, +0.002] (n 67) | +0.002 [-0.002, +0.006] pct [-0.002, +0.006] (n 67) | +0.011 [-0.004, +0.025] pct [-0.003, +0.025] (n 67) | +0.013 [-0.006, +0.033] pct [-0.006, +0.032] (n 67) | -0.000 [-0.006, +0.006] pct [-0.006, +0.006] (n 67) |
| S → J* | +0.084 [+0.056, +0.113] pct [+0.056, +0.112] (n 67) | -0.077 [-0.092, -0.063] pct [-0.091, -0.063] (n 67) | -0.001 [-0.004, +0.002] pct [-0.004, +0.002] (n 67) | +0.001 [-0.003, +0.006] pct [-0.003, +0.006] (n 67) | +0.006 [-0.015, +0.027] pct [-0.015, +0.026] (n 67) | -0.004 [-0.037, +0.029] pct [-0.038, +0.028] (n 67) | +0.002 [-0.005, +0.008] pct [-0.004, +0.008] (n 67) |
| S → XM | +0.034 [+0.015, +0.054] pct [+0.015, +0.053] (n 67) | -0.025 [-0.039, -0.010] pct [-0.039, -0.010] (n 67) | -0.002 [-0.005, +0.002] pct [-0.005, +0.001] (n 67) | +0.001 [-0.002, +0.004] pct [-0.002, +0.004] (n 67) | +0.010 [-0.004, +0.023] pct [-0.004, +0.023] (n 67) | +0.033 [+0.013, +0.053] pct [+0.014, +0.051] (n 67) | +0.002 [-0.004, +0.007] pct [-0.004, +0.007] (n 67) |

**INIT · fau · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| S → AP | +0.029 [+0.009, +0.049] pct [+0.010, +0.049] (n 67) | -0.034 [-0.048, -0.020] pct [-0.047, -0.021] (n 67) | -0.004 [-0.008, +0.000] pct [-0.008, -0.000] (n 67) | -0.001 [-0.006, +0.003] pct [-0.006, +0.003] (n 67) | -0.004 [-0.018, +0.011] pct [-0.017, +0.011] (n 67) | +0.008 [-0.009, +0.025] pct [-0.009, +0.024] (n 67) | -0.001 [-0.008, +0.005] pct [-0.008, +0.005] (n 67) | -0.000 [-0.001, -0.000] pct [-0.001, -0.000] (n 67) |
| S → XP | +0.012 [-0.020, +0.044] pct [-0.013, +0.043] (n 67) | -0.027 [-0.040, -0.014] pct [-0.040, -0.014] (n 67) | -0.004 [-0.008, -0.000] pct [-0.008, -0.001] (n 67) | -0.003 [-0.014, +0.008] pct [-0.009, +0.005] (n 67) | -0.009 [-0.036, +0.017] pct [-0.027, +0.014] (n 67) | -0.011 [-0.040, +0.017] pct [-0.032, +0.014] (n 67) | -0.002 [-0.008, +0.004] pct [-0.007, +0.004] (n 67) | -0.001 [-0.001, -0.000] pct [-0.001, -0.001] (n 67) |
| S → J* | -0.023 [-0.043, -0.004] pct [-0.042, -0.005] (n 67) | -0.007 [-0.019, +0.005] pct [-0.018, +0.005] (n 67) | -0.005 [-0.008, -0.002] pct [-0.009, -0.002] (n 67) | -0.008 [-0.012, -0.004] pct [-0.011, -0.004] (n 67) | -0.024 [-0.037, -0.011] pct [-0.037, -0.011] (n 67) | -0.026 [-0.042, -0.011] pct [-0.042, -0.012] (n 67) | -0.003 [-0.009, +0.003] pct [-0.009, +0.003] (n 67) | -0.001 [-0.001, -0.000] pct [-0.001, -0.000] (n 67) |
| S → XM | -0.019 [-0.050, +0.011] pct [-0.045, +0.011] (n 67) | +0.010 [-0.005, +0.025] pct [-0.004, +0.024] (n 67) | -0.004 [-0.008, -0.000] pct [-0.008, -0.000] (n 67) | -0.003 [-0.012, +0.006] pct [-0.009, +0.004] (n 67) | -0.003 [-0.030, +0.023] pct [-0.023, +0.021] (n 67) | -0.009 [-0.038, +0.020] pct [-0.030, +0.016] (n 67) | +0.003 [-0.003, +0.009] pct [-0.002, +0.008] (n 67) | -0.001 [-0.001, -0.001] pct [-0.001, -0.001] (n 67) |

**INIT · dtu · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| S → AP | +0.100 [+0.062, +0.137] pct [+0.065, +0.135] (n 44) | -0.025 [-0.050, -0.001] pct [-0.049, -0.002] (n 44) | +0.005 [+0.001, +0.009] pct [+0.001, +0.009] (n 44) | +0.011 [+0.007, +0.014] pct [+0.007, +0.014] (n 44) | +0.055 [+0.031, +0.079] pct [+0.031, +0.077] (n 44) | +0.084 [+0.056, +0.111] pct [+0.058, +0.110] (n 44) | +0.011 [+0.003, +0.020] pct [+0.004, +0.019] (n 44) |
| S → XP | +0.011 [-0.011, +0.033] pct [-0.010, +0.033] (n 44) | +0.010 [-0.005, +0.024] pct [-0.004, +0.024] (n 44) | -0.001 [-0.005, +0.003] pct [-0.005, +0.002] (n 44) | +0.003 [+0.000, +0.006] pct [+0.000, +0.006] (n 44) | +0.011 [-0.005, +0.028] pct [-0.005, +0.027] (n 44) | +0.029 [+0.004, +0.053] pct [+0.006, +0.052] (n 44) | +0.013 [+0.005, +0.021] pct [+0.006, +0.021] (n 44) |
| S → J* | +0.092 [+0.053, +0.131] pct [+0.055, +0.129] (n 44) | -0.021 [-0.047, +0.005] pct [-0.047, +0.003] (n 44) | +0.004 [+0.000, +0.008] pct [+0.001, +0.008] (n 44) | +0.010 [+0.006, +0.014] pct [+0.007, +0.014] (n 44) | +0.052 [+0.029, +0.076] pct [+0.029, +0.074] (n 44) | +0.079 [+0.053, +0.105] pct [+0.055, +0.104] (n 44) | +0.013 [+0.005, +0.020] pct [+0.005, +0.020] (n 44) |
| S → XM | +0.047 [+0.014, +0.079] pct [+0.016, +0.079] (n 44) | -0.024 [-0.048, +0.000] pct [-0.048, -0.001] (n 44) | -0.002 [-0.006, +0.002] pct [-0.006, +0.002] (n 44) | +0.004 [-0.001, +0.008] pct [-0.001, +0.008] (n 44) | +0.017 [-0.005, +0.039] pct [-0.004, +0.039] (n 44) | +0.039 [+0.009, +0.069] pct [+0.011, +0.068] (n 44) | +0.008 [+0.001, +0.015] pct [+0.001, +0.015] (n 44) |

**INIT · dtu · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| S → AP | +0.021 [-0.026, +0.068] pct [-0.024, +0.065] (n 44) | -0.010 [-0.045, +0.025] pct [-0.043, +0.023] (n 44) | +0.002 [-0.002, +0.006] pct [-0.002, +0.006] (n 44) | +0.001 [-0.003, +0.005] pct [-0.003, +0.005] (n 44) | +0.002 [-0.021, +0.025] pct [-0.020, +0.024] (n 44) | +0.049 [+0.022, +0.075] pct [+0.023, +0.074] (n 44) | -0.000 [-0.008, +0.007] pct [-0.007, +0.007] (n 44) | -0.001 [-0.001, -0.001] pct [-0.001, -0.001] (n 44) |
| S → XP | -0.174 [-0.222, -0.126] pct [-0.221, -0.131] (n 44) | +0.095 [+0.057, +0.133] pct [+0.059, +0.132] (n 44) | -0.002 [-0.005, +0.001] pct [-0.005, +0.001] (n 44) | -0.015 [-0.020, -0.010] pct [-0.020, -0.011] (n 44) | -0.083 [-0.107, -0.059] pct [-0.106, -0.060] (n 44) | -0.060 [-0.089, -0.032] pct [-0.087, -0.033] (n 44) | -0.008 [-0.016, -0.001] pct [-0.016, -0.001] (n 44) | -0.001 [-0.002, -0.001] pct [-0.002, -0.001] (n 44) |
| S → J* | -0.077 [-0.113, -0.042] pct [-0.111, -0.043] (n 44) | +0.035 [+0.007, +0.062] pct [+0.008, +0.061] (n 44) | +0.000 [-0.004, +0.004] pct [-0.004, +0.004] (n 44) | -0.007 [-0.011, -0.003] pct [-0.011, -0.003] (n 44) | -0.046 [-0.065, -0.026] pct [-0.064, -0.025] (n 44) | -0.007 [-0.028, +0.015] pct [-0.027, +0.014] (n 44) | -0.001 [-0.009, +0.008] pct [-0.008, +0.007] (n 44) | -0.001 [-0.002, -0.001] pct [-0.002, -0.001] (n 44) |
| S → XM | -0.150 [-0.192, -0.109] pct [-0.192, -0.111] (n 44) | +0.061 [+0.023, +0.099] pct [+0.026, +0.098] (n 44) | -0.001 [-0.004, +0.003] pct [-0.004, +0.003] (n 44) | -0.016 [-0.021, -0.012] pct [-0.021, -0.012] (n 44) | -0.082 [-0.102, -0.061] pct [-0.102, -0.062] (n 44) | -0.060 [-0.083, -0.037] pct [-0.083, -0.037] (n 44) | -0.005 [-0.014, +0.003] pct [-0.013, +0.002] (n 44) | -0.001 [-0.002, -0.001] pct [-0.002, -0.001] (n 44) |

**INIT · federici · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| S → AP | +0.017 [-0.004, +0.037] pct [-0.003, +0.036] (n 86) | -0.002 [-0.014, +0.009] pct [-0.014, +0.010] (n 86) | +0.000 [-0.005, +0.006] pct [-0.005, +0.006] (n 86) | +0.007 [-0.003, +0.018] pct [-0.003, +0.018] (n 86) | +0.015 [-0.002, +0.033] pct [-0.001, +0.032] (n 86) | +0.019 [-0.005, +0.042] pct [-0.004, +0.042] (n 86) |
| S → XP | +0.027 [+0.007, +0.047] pct [+0.007, +0.047] (n 86) | -0.003 [-0.018, +0.012] pct [-0.018, +0.012] (n 86) | +0.001 [-0.006, +0.008] pct [-0.006, +0.008] (n 86) | +0.011 [+0.002, +0.020] pct [+0.002, +0.020] (n 86) | +0.024 [+0.008, +0.039] pct [+0.009, +0.039] (n 86) | +0.016 [-0.002, +0.035] pct [-0.002, +0.034] (n 86) |
| S → J* | +0.017 [-0.006, +0.040] pct [-0.006, +0.039] (n 86) | -0.009 [-0.021, +0.004] pct [-0.021, +0.004] (n 86) | -0.001 [-0.007, +0.006] pct [-0.007, +0.006] (n 86) | +0.004 [-0.008, +0.015] pct [-0.008, +0.015] (n 86) | +0.010 [-0.009, +0.029] pct [-0.008, +0.029] (n 86) | +0.019 [-0.006, +0.045] pct [-0.005, +0.044] (n 86) |
| S → XM | +0.014 [-0.003, +0.031] pct [-0.001, +0.031] (n 86) | -0.003 [-0.016, +0.011] pct [-0.016, +0.011] (n 86) | -0.004 [-0.010, +0.003] pct [-0.010, +0.002] (n 86) | +0.005 [-0.004, +0.013] pct [-0.004, +0.013] (n 86) | +0.011 [-0.003, +0.024] pct [-0.002, +0.024] (n 86) | -0.005 [-0.022, +0.013] pct [-0.022, +0.012] (n 86) |

**INIT · federici · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| S → AP | +0.018 [-0.004, +0.040] pct [-0.003, +0.040] (n 86) | -0.018 [-0.033, -0.003] pct [-0.032, -0.003] (n 86) | +0.001 [-0.004, +0.006] pct [-0.004, +0.006] (n 86) | -0.000 [-0.009, +0.009] pct [-0.009, +0.009] (n 86) | +0.002 [-0.013, +0.017] pct [-0.013, +0.017] (n 86) | +0.007 [-0.011, +0.026] pct [-0.011, +0.025] (n 86) | -0.001 [-0.001, -0.000] pct [-0.001, -0.000] (n 86) |
| S → XP | +0.016 [-0.006, +0.037] pct [-0.006, +0.036] (n 86) | -0.015 [-0.030, -0.000] pct [-0.030, -0.001] (n 86) | +0.002 [-0.003, +0.007] pct [-0.003, +0.007] (n 86) | -0.001 [-0.010, +0.009] pct [-0.010, +0.008] (n 86) | -0.001 [-0.016, +0.013] pct [-0.015, +0.013] (n 86) | -0.001 [-0.016, +0.015] pct [-0.015, +0.014] (n 86) | -0.001 [-0.001, -0.000] pct [-0.001, -0.000] (n 86) |
| S → J* | -0.003 [-0.025, +0.018] pct [-0.024, +0.018] (n 86) | -0.002 [-0.016, +0.012] pct [-0.015, +0.012] (n 86) | +0.000 [-0.004, +0.005] pct [-0.004, +0.005] (n 86) | -0.003 [-0.013, +0.007] pct [-0.012, +0.007] (n 86) | -0.004 [-0.018, +0.010] pct [-0.018, +0.010] (n 86) | -0.003 [-0.017, +0.010] pct [-0.017, +0.010] (n 86) | -0.001 [-0.001, -0.000] pct [-0.001, -0.000] (n 86) |
| S → XM | +0.005 [-0.023, +0.033] pct [-0.021, +0.032] (n 86) | -0.007 [-0.026, +0.012] pct [-0.026, +0.012] (n 86) | +0.003 [-0.003, +0.009] pct [-0.002, +0.009] (n 86) | -0.004 [-0.015, +0.007] pct [-0.015, +0.006] (n 86) | -0.003 [-0.020, +0.014] pct [-0.020, +0.013] (n 86) | +0.004 [-0.016, +0.023] pct [-0.015, +0.023] (n 86) | -0.001 [-0.001, -0.000] pct [-0.001, -0.000] (n 86) |

**INIT · private_bdf · NCE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | +0.001 [-0.000, +0.002] pct [+0.000, +0.002] (n 64) | +0.001 [-0.000, +0.002] pct [-0.000, +0.002] (n 64) |
| S → XP | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| S → J* | +0.001 [-0.000, +0.001] pct [+0.000, +0.001] (n 64) | +0.001 [-0.000, +0.002] pct [-0.000, +0.001] (n 64) |
| S → XM | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |

**INIT · private_bdf · NCE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) |
| S → XP | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| S → J* | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) |
| S → XM | -0.000 [-0.001, -0.000] pct [-0.001, -0.000] (n 64) | -0.000 [-0.001, -0.000] pct [-0.001, -0.000] (n 64) |

**INIT · private_bdf · NCE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | -0.000 [-0.001, +0.001] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |
| S → XP | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |
| S → J* | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |
| S → XM | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |

**INIT · private_bdf · CS_SINGLE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| S → XP | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| S → J* | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) | -0.002 [-0.003, -0.000] pct [-0.003, -0.000] (n 64) |
| S → XM | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) | -0.002 [-0.003, -0.000] pct [-0.003, -0.000] (n 64) |

**INIT · private_bdf · CS_SINGLE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| S → XP | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.001 [-0.001, +0.003] pct [-0.000, +0.003] (n 64) |
| S → J* | -0.001 [-0.002, +0.001] pct [-0.002, +0.000] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| S → XM | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.001 [-0.001, +0.003] pct [-0.001, +0.002] (n 64) |

**INIT · private_bdf · CS_SINGLE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| S → AP | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| S → XP | +0.001 [-0.000, +0.002] pct [-0.000, +0.002] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.001] (n 64) |
| S → J* | +0.001 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| S → XM | +0.000 [-0.001, +0.002] pct [-0.001, +0.001] (n 64) | +0.001 [-0.001, +0.002] pct [-0.001, +0.003] (n 64) |

**SUPERVISION · fau · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | -0.080 [-0.118, -0.042] pct [-0.113, -0.042] (n 67) | +0.085 [+0.062, +0.109] pct [+0.063, +0.108] (n 67) | -0.002 [-0.007, +0.003] pct [-0.007, +0.003] (n 67) | -0.002 [-0.007, +0.003] pct [-0.006, +0.003] (n 67) | +0.008 [-0.026, +0.042] pct [-0.018, +0.038] (n 67) | +0.003 [-0.031, +0.037] pct [-0.029, +0.037] (n 67) | -0.002 [-0.007, +0.003] pct [-0.007, +0.003] (n 67) |
| AP → J* | -0.017 [-0.036, +0.001] pct [-0.037, +0.000] (n 67) | +0.019 [-0.001, +0.040] pct [-0.000, +0.039] (n 67) | -0.001 [-0.004, +0.003] pct [-0.004, +0.003] (n 67) | -0.002 [-0.006, +0.001] pct [-0.006, +0.001] (n 67) | +0.004 [-0.010, +0.017] pct [-0.009, +0.017] (n 67) | -0.014 [-0.027, -0.000] pct [-0.027, -0.001] (n 67) | -0.000 [-0.006, +0.005] pct [-0.006, +0.005] (n 67) |
| XP → J* | +0.062 [+0.029, +0.096] pct [+0.029, +0.092] (n 67) | -0.066 [-0.083, -0.049] pct [-0.082, -0.050] (n 67) | +0.002 [-0.003, +0.006] pct [-0.003, +0.006] (n 67) | -0.001 [-0.006, +0.005] pct [-0.006, +0.005] (n 67) | -0.004 [-0.033, +0.024] pct [-0.032, +0.019] (n 67) | -0.017 [-0.051, +0.016] pct [-0.050, +0.016] (n 67) | +0.002 [-0.005, +0.008] pct [-0.004, +0.008] (n 67) |

**SUPERVISION · fau · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → XP | -0.017 [-0.046, +0.012] pct [-0.042, +0.012] (n 67) | +0.007 [-0.009, +0.023] pct [-0.008, +0.023] (n 67) | -0.000 [-0.004, +0.004] pct [-0.004, +0.003] (n 67) | -0.002 [-0.010, +0.006] pct [-0.008, +0.006] (n 67) | -0.006 [-0.026, +0.015] pct [-0.024, +0.015] (n 67) | -0.019 [-0.045, +0.007] pct [-0.041, +0.005] (n 67) | -0.001 [-0.006, +0.005] pct [-0.006, +0.005] (n 67) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 67) |
| AP → J* | -0.052 [-0.071, -0.033] pct [-0.071, -0.033] (n 67) | +0.027 [+0.015, +0.039] pct [+0.015, +0.039] (n 67) | -0.001 [-0.005, +0.003] pct [-0.005, +0.003] (n 67) | -0.006 [-0.011, -0.002] pct [-0.011, -0.002] (n 67) | -0.021 [-0.034, -0.007] pct [-0.034, -0.007] (n 67) | -0.034 [-0.049, -0.020] pct [-0.048, -0.020] (n 67) | -0.001 [-0.006, +0.004] pct [-0.006, +0.004] (n 67) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 67) |
| XP → J* | -0.035 [-0.060, -0.010] pct [-0.061, -0.014] (n 67) | +0.020 [+0.009, +0.031] pct [+0.009, +0.031] (n 67) | -0.001 [-0.005, +0.003] pct [-0.005, +0.003] (n 67) | -0.005 [-0.014, +0.005] pct [-0.012, +0.001] (n 67) | -0.015 [-0.035, +0.005] pct [-0.034, +0.001] (n 67) | -0.015 [-0.039, +0.009] pct [-0.038, +0.003] (n 67) | -0.001 [-0.007, +0.005] pct [-0.007, +0.005] (n 67) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 67) |

**SUPERVISION · dtu · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | -0.088 [-0.120, -0.056] pct [-0.119, -0.058] (n 44) | +0.035 [+0.013, +0.057] pct [+0.013, +0.055] (n 44) | -0.006 [-0.010, -0.002] pct [-0.010, -0.002] (n 44) | -0.007 [-0.011, -0.004] pct [-0.011, -0.004] (n 44) | -0.044 [-0.065, -0.023] pct [-0.064, -0.024] (n 44) | -0.055 [-0.081, -0.029] pct [-0.081, -0.031] (n 44) | +0.002 [-0.005, +0.009] pct [-0.005, +0.009] (n 44) |
| AP → J* | -0.008 [-0.015, -0.001] pct [-0.014, -0.001] (n 44) | +0.004 [-0.001, +0.008] pct [-0.001, +0.008] (n 44) | -0.000 [-0.003, +0.002] pct [-0.003, +0.002] (n 44) | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 44) | -0.003 [-0.008, +0.002] pct [-0.008, +0.002] (n 44) | -0.005 [-0.010, +0.001] pct [-0.010, +0.001] (n 44) | +0.001 [-0.003, +0.005] pct [-0.003, +0.005] (n 44) |
| XP → J* | +0.081 [+0.048, +0.114] pct [+0.049, +0.113] (n 44) | -0.031 [-0.054, -0.008] pct [-0.053, -0.009] (n 44) | +0.006 [+0.002, +0.009] pct [+0.002, +0.009] (n 44) | +0.007 [+0.004, +0.010] pct [+0.004, +0.010] (n 44) | +0.041 [+0.021, +0.061] pct [+0.022, +0.060] (n 44) | +0.051 [+0.026, +0.076] pct [+0.028, +0.075] (n 44) | -0.001 [-0.007, +0.006] pct [-0.007, +0.006] (n 44) |

**SUPERVISION · dtu · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → XP | -0.195 [-0.235, -0.155] pct [-0.233, -0.158] (n 44) | +0.105 [+0.073, +0.136] pct [+0.075, +0.134] (n 44) | -0.004 [-0.007, -0.001] pct [-0.007, -0.001] (n 44) | -0.016 [-0.020, -0.012] pct [-0.020, -0.012] (n 44) | -0.085 [-0.107, -0.063] pct [-0.106, -0.064] (n 44) | -0.109 [-0.136, -0.081] pct [-0.135, -0.083] (n 44) | -0.008 [-0.015, -0.002] pct [-0.014, -0.002] (n 44) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 44) |
| AP → J* | -0.099 [-0.136, -0.062] pct [-0.134, -0.064] (n 44) | +0.044 [+0.020, +0.069] pct [+0.022, +0.068] (n 44) | -0.002 [-0.004, +0.001] pct [-0.004, +0.001] (n 44) | -0.008 [-0.012, -0.004] pct [-0.012, -0.005] (n 44) | -0.048 [-0.068, -0.027] pct [-0.068, -0.028] (n 44) | -0.055 [-0.079, -0.031] pct [-0.077, -0.032] (n 44) | -0.000 [-0.007, +0.006] pct [-0.006, +0.006] (n 44) | -0.000 [-0.000, +0.000] pct [-0.000, -0.000] (n 44) |
| XP → J* | +0.097 [+0.065, +0.128] pct [+0.066, +0.127] (n 44) | -0.060 [-0.089, -0.032] pct [-0.088, -0.033] (n 44) | +0.002 [-0.001, +0.005] pct [-0.001, +0.005] (n 44) | +0.008 [+0.004, +0.011] pct [+0.005, +0.011] (n 44) | +0.037 [+0.023, +0.052] pct [+0.023, +0.052] (n 44) | +0.054 [+0.030, +0.077] pct [+0.031, +0.075] (n 44) | +0.008 [+0.001, +0.015] pct [+0.002, +0.015] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |

**SUPERVISION · federici · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → XP | +0.010 [-0.012, +0.033] pct [-0.012, +0.033] (n 86) | -0.001 [-0.014, +0.013] pct [-0.014, +0.013] (n 86) | +0.001 [-0.005, +0.006] pct [-0.005, +0.006] (n 86) | +0.003 [-0.006, +0.012] pct [-0.006, +0.012] (n 86) | +0.009 [-0.006, +0.024] pct [-0.006, +0.024] (n 86) | -0.002 [-0.023, +0.018] pct [-0.023, +0.017] (n 86) |
| AP → J* | +0.000 [-0.021, +0.021] pct [-0.020, +0.020] (n 86) | -0.006 [-0.019, +0.006] pct [-0.018, +0.006] (n 86) | -0.001 [-0.006, +0.004] pct [-0.006, +0.004] (n 86) | -0.004 [-0.014, +0.007] pct [-0.014, +0.006] (n 86) | -0.005 [-0.020, +0.011] pct [-0.020, +0.010] (n 86) | +0.001 [-0.020, +0.022] pct [-0.021, +0.021] (n 86) |
| XP → J* | -0.010 [-0.031, +0.010] pct [-0.030, +0.010] (n 86) | -0.005 [-0.021, +0.010] pct [-0.021, +0.009] (n 86) | -0.001 [-0.007, +0.004] pct [-0.007, +0.003] (n 86) | -0.007 [-0.017, +0.003] pct [-0.017, +0.003] (n 86) | -0.014 [-0.029, +0.002] pct [-0.029, +0.001] (n 86) | +0.003 [-0.014, +0.020] pct [-0.013, +0.019] (n 86) |

**SUPERVISION · federici · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | -0.002 [-0.022, +0.017] pct [-0.021, +0.017] (n 86) | +0.002 [-0.011, +0.016] pct [-0.011, +0.015] (n 86) | +0.001 [-0.004, +0.006] pct [-0.004, +0.006] (n 86) | -0.001 [-0.010, +0.008] pct [-0.009, +0.008] (n 86) | -0.004 [-0.018, +0.011] pct [-0.019, +0.011] (n 86) | -0.008 [-0.025, +0.009] pct [-0.024, +0.008] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| AP → J* | -0.022 [-0.035, -0.008] pct [-0.035, -0.008] (n 86) | +0.016 [+0.005, +0.027] pct [+0.005, +0.027] (n 86) | -0.000 [-0.005, +0.004] pct [-0.005, +0.004] (n 86) | -0.003 [-0.009, +0.003] pct [-0.009, +0.003] (n 86) | -0.006 [-0.017, +0.004] pct [-0.017, +0.003] (n 86) | -0.011 [-0.024, +0.002] pct [-0.023, +0.002] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XP → J* | -0.019 [-0.036, -0.002] pct [-0.036, -0.003] (n 86) | +0.013 [+0.001, +0.025] pct [+0.002, +0.025] (n 86) | -0.001 [-0.006, +0.003] pct [-0.006, +0.003] (n 86) | -0.002 [-0.011, +0.006] pct [-0.011, +0.006] (n 86) | -0.003 [-0.015, +0.010] pct [-0.015, +0.010] (n 86) | -0.003 [-0.016, +0.011] pct [-0.016, +0.010] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |

**SUPERVISION · private_bdf · NCE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | -0.001 [-0.002, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| AP → J* | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |
| XP → J* | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.001, +0.001] pct [-0.000, +0.001] (n 64) |

**SUPERVISION · private_bdf · NCE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | +0.000 [-0.001, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| AP → J* | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) |
| XP → J* | -0.000 [-0.001, +0.001] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |

**SUPERVISION · private_bdf · NCE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) |
| AP → J* | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) |
| XP → J* | -0.000 [-0.001, +0.000] pct [-0.000, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |

**SUPERVISION · private_bdf · CS_SINGLE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| AP → J* | -0.001 [-0.002, +0.000] pct [-0.002, +0.000] (n 64) | -0.001 [-0.003, -0.000] pct [-0.003, -0.000] (n 64) |
| XP → J* | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) | -0.001 [-0.002, +0.000] pct [-0.002, +0.000] (n 64) |

**SUPERVISION · private_bdf · CS_SINGLE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.001 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| AP → J* | -0.001 [-0.002, +0.000] pct [-0.002, -0.000] (n 64) | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) |
| XP → J* | -0.001 [-0.002, +0.000] pct [-0.002, +0.000] (n 64) | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |

**SUPERVISION · private_bdf · CS_SINGLE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → XP | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| AP → J* | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) |
| XP → J* | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) |

**SUPERVISION · fau · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | +0.163 [+0.120, +0.207] pct [+0.120, +0.206] (n 67) | +0.006 [-0.005, +0.018] pct [-0.005, +0.018] (n 67) | +0.007 [+0.003, +0.012] pct [+0.003, +0.011] (n 67) | +0.085 [+0.063, +0.106] pct [+0.064, +0.105] (n 67) | +0.150 [+0.112, +0.189] pct [+0.114, +0.188] (n 67) | not applicable: native readout of an encoder never trained against v (design §2.11) | +0.016 [+0.003, +0.029] pct [+0.004, +0.029] (n 67) |
| AP → J* | +0.013 [-0.007, +0.032] pct [-0.007, +0.031] (n 67) | -0.008 [-0.014, -0.001] pct [-0.014, -0.002] (n 67) | -0.001 [-0.004, +0.002] pct [-0.004, +0.001] (n 67) | +0.007 [-0.002, +0.016] pct [-0.002, +0.016] (n 67) | +0.003 [-0.014, +0.020] pct [-0.014, +0.019] (n 67) | +0.003 [-0.008, +0.014] pct [-0.008, +0.013] (n 67) | -0.015 [-0.022, -0.009] pct [-0.021, -0.009] (n 67) |
| XP → J* | -0.151 [-0.193, -0.108] pct [-0.193, -0.109] (n 67) | -0.014 [-0.025, -0.003] pct [-0.025, -0.003] (n 67) | -0.008 [-0.012, -0.004] pct [-0.012, -0.005] (n 67) | -0.078 [-0.099, -0.057] pct [-0.098, -0.057] (n 67) | -0.148 [-0.187, -0.109] pct [-0.186, -0.110] (n 67) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.031 [-0.043, -0.019] pct [-0.043, -0.020] (n 67) |

**SUPERVISION · fau · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → XP | +0.011 [-0.015, +0.037] pct [-0.014, +0.037] (n 67) | -0.011 [-0.020, -0.003] pct [-0.020, -0.003] (n 67) | +0.001 [-0.003, +0.004] pct [-0.003, +0.004] (n 67) | +0.004 [-0.014, +0.022] pct [-0.012, +0.023] (n 67) | -0.003 [-0.027, +0.021] pct [-0.025, +0.020] (n 67) | +0.047 [+0.016, +0.078] pct [+0.017, +0.077] (n 67) | +0.001 [-0.009, +0.010] pct [-0.009, +0.010] (n 67) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 67) |
| AP → J* | +0.095 [+0.068, +0.122] pct [+0.069, +0.121] (n 67) | -0.014 [-0.020, -0.007] pct [-0.020, -0.008] (n 67) | +0.008 [+0.003, +0.012] pct [+0.004, +0.012] (n 67) | +0.055 [+0.037, +0.073] pct [+0.038, +0.073] (n 67) | +0.070 [+0.047, +0.093] pct [+0.047, +0.093] (n 67) | +0.107 [+0.076, +0.139] pct [+0.077, +0.138] (n 67) | +0.018 [+0.006, +0.031] pct [+0.006, +0.031] (n 67) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 67) |
| XP → J* | +0.084 [+0.066, +0.101] pct [+0.067, +0.101] (n 67) | -0.003 [-0.011, +0.006] pct [-0.011, +0.006] (n 67) | +0.007 [+0.004, +0.011] pct [+0.004, +0.011] (n 67) | +0.050 [+0.040, +0.061] pct [+0.040, +0.061] (n 67) | +0.073 [+0.058, +0.088] pct [+0.059, +0.088] (n 67) | +0.061 [+0.047, +0.074] pct [+0.047, +0.074] (n 67) | +0.018 [+0.008, +0.027] pct [+0.009, +0.027] (n 67) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 67) |

**SUPERVISION · dtu · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | -0.084 [-0.110, -0.057] pct [-0.109, -0.059] (n 44) | +0.057 [+0.044, +0.070] pct [+0.045, +0.070] (n 44) | -0.002 [-0.004, +0.001] pct [-0.004, +0.000] (n 44) | -0.015 [-0.025, -0.005] pct [-0.024, -0.005] (n 44) | -0.028 [-0.046, -0.009] pct [-0.045, -0.010] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | +0.004 [-0.008, +0.015] pct [-0.008, +0.015] (n 44) |
| AP → J* | -0.013 [-0.018, -0.009] pct [-0.018, -0.009] (n 44) | +0.003 [+0.001, +0.005] pct [+0.001, +0.005] (n 44) | -0.001 [-0.003, -0.000] pct [-0.003, -0.000] (n 44) | -0.005 [-0.007, -0.003] pct [-0.006, -0.003] (n 44) | -0.009 [-0.013, -0.005] pct [-0.013, -0.006] (n 44) | -0.003 [-0.005, -0.001] pct [-0.005, -0.001] (n 44) | -0.005 [-0.008, -0.002] pct [-0.008, -0.002] (n 44) |
| XP → J* | +0.070 [+0.046, +0.095] pct [+0.047, +0.094] (n 44) | -0.054 [-0.067, -0.041] pct [-0.067, -0.042] (n 44) | +0.000 [-0.001, +0.002] pct [-0.001, +0.002] (n 44) | +0.010 [+0.000, +0.020] pct [+0.001, +0.019] (n 44) | +0.019 [+0.002, +0.035] pct [+0.002, +0.035] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.008 [-0.020, +0.003] pct [-0.019, +0.003] (n 44) |

**SUPERVISION · dtu · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → XP | -0.117 [-0.145, -0.089] pct [-0.144, -0.090] (n 44) | +0.069 [+0.053, +0.085] pct [+0.054, +0.084] (n 44) | -0.000 [-0.002, +0.002] pct [-0.002, +0.002] (n 44) | -0.027 [-0.042, -0.012] pct [-0.041, -0.012] (n 44) | -0.043 [-0.066, -0.021] pct [-0.064, -0.021] (n 44) | -0.098 [-0.127, -0.069] pct [-0.125, -0.070] (n 44) | -0.008 [-0.026, +0.009] pct [-0.025, +0.009] (n 44) | -0.000 [-0.001, -0.000] pct [-0.001, -0.000] (n 44) |
| AP → J* | -0.079 [-0.095, -0.064] pct [-0.094, -0.065] (n 44) | +0.046 [+0.040, +0.053] pct [+0.040, +0.052] (n 44) | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 44) | -0.017 [-0.024, -0.010] pct [-0.024, -0.011] (n 44) | -0.035 [-0.047, -0.023] pct [-0.047, -0.023] (n 44) | -0.035 [-0.050, -0.020] pct [-0.049, -0.022] (n 44) | -0.003 [-0.009, +0.004] pct [-0.009, +0.003] (n 44) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 44) |
| XP → J* | +0.038 [+0.013, +0.063] pct [+0.013, +0.062] (n 44) | -0.023 [-0.035, -0.011] pct [-0.034, -0.011] (n 44) | +0.000 [-0.002, +0.002] pct [-0.002, +0.002] (n 44) | +0.010 [-0.007, +0.028] pct [-0.007, +0.027] (n 44) | +0.008 [-0.012, +0.028] pct [-0.012, +0.026] (n 44) | +0.063 [+0.033, +0.093] pct [+0.033, +0.090] (n 44) | +0.006 [-0.011, +0.022] pct [-0.011, +0.021] (n 44) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 44) |

**SUPERVISION · federici · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → XP | +0.033 [-0.019, +0.085] pct [-0.017, +0.084] (n 86) | +0.034 [+0.007, +0.061] pct [+0.007, +0.060] (n 86) | -0.002 [-0.005, +0.001] pct [-0.005, +0.000] (n 86) | +0.022 [+0.005, +0.039] pct [+0.005, +0.038] (n 86) | +0.062 [+0.026, +0.098] pct [+0.027, +0.097] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |
| AP → J* | +0.037 [-0.004, +0.078] pct [-0.003, +0.076] (n 86) | +0.025 [+0.005, +0.046] pct [+0.004, +0.045] (n 86) | -0.001 [-0.004, +0.003] pct [-0.004, +0.002] (n 86) | +0.020 [+0.008, +0.033] pct [+0.008, +0.032] (n 86) | +0.057 [+0.030, +0.084] pct [+0.030, +0.084] (n 86) | +0.344 [+0.305, +0.383] pct [+0.304, +0.380] (n 86) |
| XP → J* | +0.004 [-0.019, +0.027] pct [-0.018, +0.027] (n 86) | -0.009 [-0.023, +0.005] pct [-0.022, +0.005] (n 86) | +0.002 [-0.001, +0.004] pct [-0.000, +0.004] (n 86) | -0.001 [-0.009, +0.006] pct [-0.009, +0.006] (n 86) | -0.005 [-0.020, +0.011] pct [-0.020, +0.010] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |

**SUPERVISION · federici · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → XP | -0.023 [-0.049, +0.003] pct [-0.049, +0.002] (n 86) | +0.048 [+0.032, +0.064] pct [+0.033, +0.064] (n 86) | -0.004 [-0.008, +0.000] pct [-0.007, +0.000] (n 86) | +0.001 [-0.012, +0.014] pct [-0.011, +0.014] (n 86) | +0.022 [+0.002, +0.041] pct [+0.002, +0.040] (n 86) | +0.006 [-0.023, +0.035] pct [-0.023, +0.034] (n 86) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 86) |
| AP → J* | +0.021 [+0.004, +0.039] pct [+0.004, +0.038] (n 86) | -0.075 [-0.086, -0.064] pct [-0.086, -0.064] (n 86) | +0.002 [-0.002, +0.005] pct [-0.002, +0.005] (n 86) | +0.006 [+0.001, +0.012] pct [+0.001, +0.011] (n 86) | -0.049 [-0.064, -0.035] pct [-0.063, -0.035] (n 86) | -0.035 [-0.049, -0.021] pct [-0.049, -0.021] (n 86) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XP → J* | +0.044 [+0.011, +0.078] pct [+0.012, +0.077] (n 86) | -0.123 [-0.143, -0.102] pct [-0.143, -0.103] (n 86) | +0.005 [+0.001, +0.009] pct [+0.001, +0.009] (n 86) | +0.006 [-0.006, +0.017] pct [-0.006, +0.017] (n 86) | -0.071 [-0.097, -0.045] pct [-0.096, -0.045] (n 86) | -0.041 [-0.072, -0.010] pct [-0.072, -0.010] (n 86) | +0.000 [-0.000, +0.001] pct [+0.000, +0.001] (n 86) |

**CONTROL · fau · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | +0.067 [+0.041, +0.093] pct [+0.042, +0.092] (n 67) | -0.072 [-0.089, -0.054] pct [-0.089, -0.055] (n 67) | +0.002 [-0.002, +0.006] pct [-0.002, +0.006] (n 67) | +0.003 [-0.001, +0.007] pct [-0.001, +0.007] (n 67) | -0.007 [-0.026, +0.012] pct [-0.026, +0.011] (n 67) | -0.023 [-0.062, +0.015] pct [-0.061, +0.012] (n 67) | +0.001 [-0.004, +0.006] pct [-0.004, +0.006] (n 67) |
| XM → XP | -0.013 [-0.040, +0.015] pct [-0.039, +0.014] (n 67) | +0.014 [-0.005, +0.032] pct [-0.006, +0.031] (n 67) | -0.000 [-0.005, +0.004] pct [-0.004, +0.004] (n 67) | +0.001 [-0.003, +0.006] pct [-0.002, +0.005] (n 67) | +0.001 [-0.018, +0.019] pct [-0.014, +0.018] (n 67) | -0.020 [-0.040, +0.001] pct [-0.040, +0.000] (n 67) | -0.002 [-0.007, +0.004] pct [-0.007, +0.004] (n 67) |
| XM → J* | +0.050 [+0.022, +0.077] pct [+0.023, +0.076] (n 67) | -0.053 [-0.070, -0.036] pct [-0.069, -0.036] (n 67) | +0.001 [-0.002, +0.005] pct [-0.003, +0.005] (n 67) | +0.001 [-0.004, +0.006] pct [-0.004, +0.005] (n 67) | -0.003 [-0.021, +0.014] pct [-0.021, +0.014] (n 67) | -0.037 [-0.074, +0.000] pct [-0.073, -0.001] (n 67) | +0.000 [-0.006, +0.007] pct [-0.006, +0.006] (n 67) |

**CONTROL · fau · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| XM → AP | +0.048 [+0.020, +0.076] pct [+0.020, +0.073] (n 67) | -0.044 [-0.058, -0.031] pct [-0.057, -0.031] (n 67) | +0.000 [-0.004, +0.005] pct [-0.005, +0.004] (n 67) | +0.002 [-0.005, +0.009] pct [-0.005, +0.008] (n 67) | -0.000 [-0.020, +0.020] pct [-0.020, +0.017] (n 67) | +0.017 [-0.008, +0.042] pct [-0.008, +0.038] (n 67) | -0.004 [-0.011, +0.002] pct [-0.011, +0.002] (n 67) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 67) |
| XM → XP | +0.031 [+0.014, +0.048] pct [+0.015, +0.048] (n 67) | -0.037 [-0.048, -0.026] pct [-0.048, -0.026] (n 67) | -0.000 [-0.004, +0.003] pct [-0.004, +0.003] (n 67) | +0.000 [-0.003, +0.003] pct [-0.003, +0.003] (n 67) | -0.006 [-0.018, +0.006] pct [-0.017, +0.005] (n 67) | -0.002 [-0.013, +0.008] pct [-0.012, +0.008] (n 67) | -0.005 [-0.010, -0.000] pct [-0.009, -0.001] (n 67) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 67) |
| XM → J* | -0.004 [-0.030, +0.022] pct [-0.030, +0.019] (n 67) | -0.017 [-0.028, -0.006] pct [-0.028, -0.006] (n 67) | -0.001 [-0.005, +0.003] pct [-0.005, +0.003] (n 67) | -0.005 [-0.012, +0.003] pct [-0.011, +0.000] (n 67) | -0.021 [-0.042, -0.000] pct [-0.040, -0.006] (n 67) | -0.017 [-0.041, +0.006] pct [-0.040, +0.001] (n 67) | -0.006 [-0.012, +0.000] pct [-0.011, +0.000] (n 67) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 67) |

**CONTROL · dtu · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | +0.053 [+0.021, +0.085] pct [+0.022, +0.082] (n 44) | -0.001 [-0.022, +0.019] pct [-0.021, +0.018] (n 44) | +0.007 [+0.003, +0.010] pct [+0.003, +0.010] (n 44) | +0.007 [+0.003, +0.011] pct [+0.003, +0.011] (n 44) | +0.039 [+0.015, +0.062] pct [+0.016, +0.061] (n 44) | +0.045 [+0.018, +0.071] pct [+0.019, +0.069] (n 44) | +0.004 [-0.004, +0.011] pct [-0.004, +0.010] (n 44) |
| XM → XP | -0.035 [-0.070, -0.000] pct [-0.068, -0.002] (n 44) | +0.034 [+0.009, +0.058] pct [+0.012, +0.057] (n 44) | +0.001 [-0.003, +0.004] pct [-0.003, +0.004] (n 44) | -0.000 [-0.005, +0.004] pct [-0.005, +0.004] (n 44) | -0.006 [-0.028, +0.017] pct [-0.027, +0.015] (n 44) | -0.011 [-0.035, +0.014] pct [-0.035, +0.013] (n 44) | +0.005 [-0.001, +0.012] pct [-0.001, +0.012] (n 44) |
| XM → J* | +0.045 [+0.012, +0.079] pct [+0.013, +0.077] (n 44) | +0.002 [-0.018, +0.023] pct [-0.017, +0.022] (n 44) | +0.006 [+0.003, +0.010] pct [+0.003, +0.010] (n 44) | +0.007 [+0.002, +0.012] pct [+0.002, +0.011] (n 44) | +0.036 [+0.012, +0.060] pct [+0.012, +0.058] (n 44) | +0.040 [+0.014, +0.067] pct [+0.015, +0.065] (n 44) | +0.005 [-0.002, +0.011] pct [-0.002, +0.011] (n 44) |

**CONTROL · dtu · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| XM → AP | +0.171 [+0.137, +0.206] pct [+0.139, +0.205] (n 44) | -0.071 [-0.098, -0.043] pct [-0.096, -0.044] (n 44) | +0.003 [-0.001, +0.006] pct [-0.000, +0.006] (n 44) | +0.017 [+0.013, +0.021] pct [+0.013, +0.021] (n 44) | +0.084 [+0.063, +0.104] pct [+0.063, +0.103] (n 44) | +0.109 [+0.085, +0.132] pct [+0.086, +0.131] (n 44) | +0.005 [-0.003, +0.013] pct [-0.003, +0.013] (n 44) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 44) |
| XM → XP | -0.024 [-0.052, +0.005] pct [-0.051, +0.004] (n 44) | +0.034 [+0.007, +0.062] pct [+0.010, +0.062] (n 44) | -0.001 [-0.004, +0.001] pct [-0.003, +0.001] (n 44) | +0.001 [-0.003, +0.005] pct [-0.003, +0.005] (n 44) | -0.001 [-0.016, +0.013] pct [-0.015, +0.013] (n 44) | -0.000 [-0.019, +0.018] pct [-0.018, +0.018] (n 44) | -0.003 [-0.010, +0.004] pct [-0.010, +0.004] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |
| XM → J* | +0.073 [+0.048, +0.098] pct [+0.049, +0.098] (n 44) | -0.026 [-0.048, -0.004] pct [-0.048, -0.005] (n 44) | +0.001 [-0.002, +0.004] pct [-0.002, +0.004] (n 44) | +0.009 [+0.006, +0.012] pct [+0.006, +0.012] (n 44) | +0.036 [+0.021, +0.051] pct [+0.021, +0.051] (n 44) | +0.053 [+0.031, +0.075] pct [+0.032, +0.074] (n 44) | +0.005 [-0.003, +0.012] pct [-0.002, +0.012] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |

**CONTROL · federici · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| XM → AP | +0.002 [-0.020, +0.025] pct [-0.019, +0.025] (n 86) | +0.000 [-0.014, +0.014] pct [-0.014, +0.014] (n 86) | +0.004 [-0.001, +0.009] pct [-0.001, +0.009] (n 86) | +0.003 [-0.007, +0.012] pct [-0.007, +0.012] (n 86) | +0.005 [-0.010, +0.020] pct [-0.010, +0.019] (n 86) | +0.023 [+0.003, +0.044] pct [+0.003, +0.043] (n 86) |
| XM → XP | +0.013 [-0.006, +0.031] pct [-0.006, +0.031] (n 86) | -0.001 [-0.013, +0.012] pct [-0.013, +0.011] (n 86) | +0.005 [-0.002, +0.011] pct [-0.000, +0.010] (n 86) | +0.006 [-0.003, +0.015] pct [-0.003, +0.014] (n 86) | +0.013 [-0.001, +0.028] pct [-0.001, +0.028] (n 86) | +0.021 [+0.000, +0.042] pct [+0.001, +0.042] (n 86) |
| XM → J* | +0.002 [-0.021, +0.025] pct [-0.020, +0.025] (n 86) | -0.006 [-0.022, +0.009] pct [-0.022, +0.009] (n 86) | +0.003 [-0.002, +0.008] pct [-0.002, +0.008] (n 86) | -0.001 [-0.012, +0.010] pct [-0.012, +0.010] (n 86) | -0.000 [-0.017, +0.016] pct [-0.016, +0.016] (n 86) | +0.024 [-0.000, +0.048] pct [+0.000, +0.048] (n 86) |

**CONTROL · federici · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | +0.013 [-0.008, +0.035] pct [-0.008, +0.035] (n 86) | -0.010 [-0.026, +0.006] pct [-0.027, +0.005] (n 86) | -0.002 [-0.008, +0.004] pct [-0.008, +0.003] (n 86) | +0.004 [-0.004, +0.013] pct [-0.004, +0.013] (n 86) | +0.006 [-0.009, +0.021] pct [-0.009, +0.020] (n 86) | +0.004 [-0.014, +0.022] pct [-0.014, +0.022] (n 86) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XM → XP | +0.011 [-0.009, +0.031] pct [-0.008, +0.029] (n 86) | -0.008 [-0.022, +0.006] pct [-0.022, +0.007] (n 86) | -0.001 [-0.007, +0.004] pct [-0.007, +0.004] (n 86) | +0.004 [-0.004, +0.011] pct [-0.004, +0.010] (n 86) | +0.002 [-0.009, +0.013] pct [-0.009, +0.013] (n 86) | -0.004 [-0.017, +0.008] pct [-0.017, +0.008] (n 86) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XM → J* | -0.008 [-0.028, +0.012] pct [-0.028, +0.012] (n 86) | +0.005 [-0.009, +0.020] pct [-0.009, +0.020] (n 86) | -0.003 [-0.008, +0.002] pct [-0.008, +0.002] (n 86) | +0.001 [-0.007, +0.010] pct [-0.007, +0.010] (n 86) | -0.001 [-0.013, +0.011] pct [-0.012, +0.011] (n 86) | -0.007 [-0.022, +0.008] pct [-0.022, +0.008] (n 86) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |

**CONTROL · private_bdf · NCE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.001 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.001 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| XM → XP | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| XM → J* | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |

**CONTROL · private_bdf · NCE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.000 [+0.000, +0.001] pct [+0.000, +0.001] (n 64) | +0.000 [+0.000, +0.001] pct [+0.000, +0.001] (n 64) |
| XM → XP | +0.001 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.001 [+0.000, +0.001] pct [+0.000, +0.001] (n 64) |
| XM → J* | +0.000 [+0.000, +0.001] pct [+0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |

**CONTROL · private_bdf · NCE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| XM → XP | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |
| XM → J* | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 64) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) |

**CONTROL · private_bdf · CS_SINGLE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.001 [-0.000, +0.002] pct [-0.000, +0.002] (n 64) | +0.002 [-0.000, +0.003] pct [-0.000, +0.003] (n 64) |
| XM → XP | +0.001 [-0.000, +0.002] pct [-0.000, +0.002] (n 64) | +0.001 [-0.000, +0.002] pct [-0.000, +0.002] (n 64) |
| XM → J* | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) |

**CONTROL · private_bdf · CS_SINGLE · T · panel seed 3407**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.001 [-0.001, +0.002] pct [-0.001, +0.002] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| XM → XP | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 64) | +0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) |
| XM → J* | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) | -0.000 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |

**CONTROL · private_bdf · CS_SINGLE · T · panel seed 3413**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| XM → AP | +0.000 [-0.002, +0.002] pct [-0.002, +0.001] (n 64) | -0.001 [-0.003, +0.001] pct [-0.003, +0.001] (n 64) |
| XM → XP | +0.000 [-0.001, +0.002] pct [-0.001, +0.001] (n 64) | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |
| XM → J* | +0.000 [-0.001, +0.002] pct [-0.001, +0.001] (n 64) | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 64) |

**CONTROL · fau · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | -0.057 [-0.101, -0.014] pct [-0.099, -0.014] (n 67) | -0.074 [-0.086, -0.063] pct [-0.086, -0.064] (n 67) | -0.001 [-0.005, +0.003] pct [-0.004, +0.003] (n 67) | -0.045 [-0.068, -0.023] pct [-0.067, -0.024] (n 67) | -0.114 [-0.151, -0.077] pct [-0.150, -0.078] (n 67) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.021 [-0.033, -0.010] pct [-0.032, -0.010] (n 67) |
| XM → XP | +0.106 [+0.082, +0.130] pct [+0.082, +0.129] (n 67) | -0.068 [-0.077, -0.060] pct [-0.076, -0.060] (n 67) | +0.006 [+0.002, +0.010] pct [+0.003, +0.010] (n 67) | +0.040 [+0.026, +0.053] pct [+0.026, +0.053] (n 67) | +0.036 [+0.014, +0.059] pct [+0.014, +0.058] (n 67) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.005 [-0.017, +0.006] pct [-0.017, +0.006] (n 67) |
| XM → J* | -0.045 [-0.089, +0.000] pct [-0.088, -0.001] (n 67) | -0.082 [-0.092, -0.073] pct [-0.092, -0.073] (n 67) | -0.002 [-0.005, +0.001] pct [-0.005, +0.001] (n 67) | -0.038 [-0.061, -0.016] pct [-0.060, -0.016] (n 67) | -0.111 [-0.151, -0.072] pct [-0.151, -0.073] (n 67) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.036 [-0.048, -0.025] pct [-0.047, -0.026] (n 67) |

**CONTROL · fau · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| XM → AP | -0.001 [-0.025, +0.024] pct [-0.024, +0.024] (n 67) | -0.025 [-0.033, -0.017] pct [-0.032, -0.017] (n 67) | +0.000 [-0.004, +0.004] pct [-0.003, +0.004] (n 67) | -0.010 [-0.027, +0.006] pct [-0.028, +0.005] (n 67) | -0.021 [-0.041, -0.001] pct [-0.040, -0.001] (n 67) | -0.031 [-0.060, -0.001] pct [-0.059, -0.002] (n 67) | -0.009 [-0.020, +0.002] pct [-0.019, +0.002] (n 67) | +0.000 [+0.000, +0.001] pct [+0.000, +0.001] (n 67) |
| XM → XP | +0.010 [-0.006, +0.027] pct [-0.006, +0.027] (n 67) | -0.036 [-0.043, -0.029] pct [-0.043, -0.029] (n 67) | +0.001 [-0.002, +0.004] pct [-0.002, +0.004] (n 67) | -0.006 [-0.017, +0.005] pct [-0.017, +0.005] (n 67) | -0.024 [-0.037, -0.010] pct [-0.037, -0.010] (n 67) | +0.016 [+0.002, +0.030] pct [+0.003, +0.029] (n 67) | -0.008 [-0.017, +0.002] pct [-0.017, +0.001] (n 67) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 67) |
| XM → J* | +0.094 [+0.076, +0.112] pct [+0.077, +0.112] (n 67) | -0.039 [-0.045, -0.032] pct [-0.045, -0.032] (n 67) | +0.008 [+0.004, +0.012] pct [+0.004, +0.012] (n 67) | +0.044 [+0.032, +0.056] pct [+0.033, +0.056] (n 67) | +0.049 [+0.033, +0.066] pct [+0.033, +0.066] (n 67) | +0.077 [+0.058, +0.095] pct [+0.059, +0.095] (n 67) | +0.010 [+0.000, +0.019] pct [+0.000, +0.019] (n 67) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 67) |

**CONTROL · dtu · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | +0.147 [+0.112, +0.182] pct [+0.113, +0.182] (n 44) | -0.097 [-0.114, -0.080] pct [-0.113, -0.081] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.027 [+0.010, +0.043] pct [+0.011, +0.042] (n 44) | +0.052 [+0.028, +0.077] pct [+0.028, +0.075] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | +0.019 [+0.004, +0.034] pct [+0.005, +0.033] (n 44) |
| XM → XP | +0.064 [+0.044, +0.083] pct [+0.045, +0.083] (n 44) | -0.040 [-0.050, -0.030] pct [-0.050, -0.030] (n 44) | -0.001 [-0.003, +0.002] pct [-0.003, +0.001] (n 44) | +0.012 [-0.002, +0.026] pct [-0.002, +0.025] (n 44) | +0.025 [+0.010, +0.039] pct [+0.010, +0.038] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | +0.023 [+0.007, +0.038] pct [+0.007, +0.038] (n 44) |
| XM → J* | +0.134 [+0.099, +0.169] pct [+0.100, +0.168] (n 44) | -0.094 [-0.111, -0.077] pct [-0.110, -0.078] (n 44) | -0.000 [-0.002, +0.002] pct [-0.002, +0.002] (n 44) | +0.022 [+0.005, +0.039] pct [+0.006, +0.038] (n 44) | +0.043 [+0.019, +0.068] pct [+0.019, +0.065] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | +0.014 [-0.001, +0.030] pct [-0.000, +0.029] (n 44) |

**CONTROL · dtu · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| XM → AP | +0.167 [+0.140, +0.194] pct [+0.140, +0.193] (n 44) | -0.067 [-0.081, -0.052] pct [-0.081, -0.053] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.070 [+0.058, +0.083] pct [+0.058, +0.083] (n 44) | +0.092 [+0.072, +0.112] pct [+0.073, +0.112] (n 44) | +0.139 [+0.114, +0.165] pct [+0.114, +0.164] (n 44) | +0.035 [+0.019, +0.051] pct [+0.020, +0.050] (n 44) | +0.001 [+0.000, +0.001] pct [+0.000, +0.001] (n 44) |
| XM → XP | +0.050 [+0.030, +0.070] pct [+0.031, +0.069] (n 44) | +0.002 [-0.008, +0.012] pct [-0.008, +0.011] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.044 [+0.027, +0.060] pct [+0.029, +0.059] (n 44) | +0.049 [+0.032, +0.066] pct [+0.033, +0.066] (n 44) | +0.041 [+0.030, +0.053] pct [+0.031, +0.052] (n 44) | +0.026 [+0.012, +0.041] pct [+0.012, +0.040] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |
| XM → J* | +0.088 [+0.066, +0.109] pct [+0.067, +0.108] (n 44) | -0.021 [-0.032, -0.010] pct [-0.031, -0.010] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.054 [+0.042, +0.065] pct [+0.043, +0.065] (n 44) | +0.057 [+0.043, +0.071] pct [+0.044, +0.070] (n 44) | +0.105 [+0.079, +0.130] pct [+0.080, +0.129] (n 44) | +0.032 [+0.017, +0.047] pct [+0.018, +0.046] (n 44) | +0.000 [+0.000, +0.000] pct [+0.000, +0.000] (n 44) |

**CONTROL · federici · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| XM → AP | -0.022 [-0.079, +0.036] pct [-0.079, +0.033] (n 86) | -0.113 [-0.144, -0.082] pct [-0.144, -0.084] (n 86) | +0.001 [-0.003, +0.006] pct [-0.003, +0.006] (n 86) | -0.021 [-0.043, -0.000] pct [-0.043, -0.001] (n 86) | -0.117 [-0.161, -0.074] pct [-0.161, -0.075] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |
| XM → XP | +0.011 [-0.032, +0.055] pct [-0.031, +0.054] (n 86) | -0.079 [-0.105, -0.054] pct [-0.105, -0.055] (n 86) | -0.001 [-0.005, +0.003] pct [-0.005, +0.003] (n 86) | +0.000 [-0.017, +0.017] pct [-0.016, +0.016] (n 86) | -0.055 [-0.086, -0.025] pct [-0.086, -0.026] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |
| XM → J* | +0.015 [-0.030, +0.061] pct [-0.030, +0.060] (n 86) | -0.088 [-0.115, -0.061] pct [-0.116, -0.062] (n 86) | +0.001 [-0.004, +0.005] pct [-0.004, +0.005] (n 86) | -0.001 [-0.019, +0.016] pct [-0.018, +0.016] (n 86) | -0.060 [-0.093, -0.027] pct [-0.094, -0.029] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |

**CONTROL · federici · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| XM → AP | +0.044 [+0.012, +0.076] pct [+0.014, +0.074] (n 86) | -0.066 [-0.085, -0.047] pct [-0.085, -0.048] (n 86) | +0.002 [-0.002, +0.007] pct [-0.002, +0.007] (n 86) | +0.026 [+0.009, +0.043] pct [+0.009, +0.043] (n 86) | -0.018 [-0.042, +0.006] pct [-0.042, +0.006] (n 86) | -0.022 [-0.062, +0.018] pct [-0.061, +0.017] (n 86) | +0.000 [-0.000, +0.001] pct [-0.000, +0.001] (n 86) |
| XM → XP | +0.021 [-0.004, +0.045] pct [-0.003, +0.045] (n 86) | -0.017 [-0.033, -0.002] pct [-0.033, -0.003] (n 86) | -0.001 [-0.005, +0.002] pct [-0.005, +0.002] (n 86) | +0.027 [+0.013, +0.041] pct [+0.013, +0.041] (n 86) | +0.004 [-0.015, +0.022] pct [-0.014, +0.021] (n 86) | -0.016 [-0.044, +0.012] pct [-0.042, +0.012] (n 86) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XM → J* | +0.065 [+0.023, +0.107] pct [+0.024, +0.106] (n 86) | -0.140 [-0.165, -0.116] pct [-0.164, -0.117] (n 86) | +0.004 [-0.000, +0.008] pct [-0.000, +0.008] (n 86) | +0.033 [+0.015, +0.050] pct [+0.016, +0.050] (n 86) | -0.067 [-0.101, -0.034] pct [-0.099, -0.034] (n 86) | -0.057 [-0.100, -0.014] pct [-0.097, -0.014] (n 86) | +0.000 [+0.000, +0.001] pct [+0.000, +0.001] (n 86) |

**RICH · fau · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | +0.003 [-0.019, +0.024] pct [-0.019, +0.023] (n 67) | +0.013 [-0.007, +0.033] pct [-0.005, +0.033] (n 67) | +0.001 [-0.002, +0.005] pct [-0.002, +0.005] (n 67) | +0.001 [-0.003, +0.005] pct [-0.003, +0.004] (n 67) | +0.011 [-0.005, +0.026] pct [-0.004, +0.026] (n 67) | +0.018 [-0.000, +0.036] pct [+0.001, +0.036] (n 67) | +0.001 [-0.005, +0.006] pct [-0.005, +0.006] (n 67) |

**RICH · fau · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APR | +0.010 [-0.008, +0.028] pct [-0.008, +0.027] (n 67) | -0.018 [-0.029, -0.007] pct [-0.029, -0.008] (n 67) | +0.001 [-0.002, +0.004] pct [-0.002, +0.004] (n 67) | +0.000 [-0.002, +0.003] pct [-0.002, +0.003] (n 67) | -0.007 [-0.024, +0.010] pct [-0.022, +0.006] (n 67) | -0.014 [-0.034, +0.006] pct [-0.032, +0.002] (n 67) | -0.003 [-0.008, +0.002] pct [-0.008, +0.001] (n 67) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 67) |

**RICH · dtu · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | +0.068 [+0.026, +0.109] pct [+0.030, +0.109] (n 44) | -0.056 [-0.100, -0.013] pct [-0.097, -0.018] (n 44) | -0.003 [-0.006, -0.001] pct [-0.006, -0.001] (n 44) | +0.005 [+0.002, +0.008] pct [+0.002, +0.008] (n 44) | +0.015 [-0.003, +0.033] pct [-0.002, +0.032] (n 44) | +0.034 [+0.001, +0.066] pct [+0.003, +0.065] (n 44) | -0.001 [-0.007, +0.005] pct [-0.007, +0.004] (n 44) |

**RICH · dtu · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APR | -0.063 [-0.090, -0.037] pct [-0.089, -0.037] (n 44) | +0.030 [+0.006, +0.054] pct [+0.007, +0.053] (n 44) | -0.003 [-0.005, -0.000] pct [-0.005, -0.000] (n 44) | -0.005 [-0.008, -0.001] pct [-0.008, -0.001] (n 44) | -0.026 [-0.043, -0.008] pct [-0.042, -0.009] (n 44) | -0.037 [-0.057, -0.018] pct [-0.056, -0.019] (n 44) | +0.002 [-0.005, +0.009] pct [-0.005, +0.009] (n 44) | -0.000 [-0.000, +0.000] pct [-0.000, -0.000] (n 44) |

**RICH · federici · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → APR | +0.017 [-0.002, +0.036] pct [-0.002, +0.035] (n 86) | -0.004 [-0.017, +0.009] pct [-0.017, +0.009] (n 86) | +0.001 [-0.004, +0.006] pct [-0.004, +0.006] (n 86) | +0.006 [-0.001, +0.013] pct [-0.001, +0.013] (n 86) | +0.010 [-0.002, +0.022] pct [-0.001, +0.022] (n 86) | +0.012 [-0.001, +0.026] pct [-0.001, +0.026] (n 86) |

**RICH · federici · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | -0.007 [-0.021, +0.006] pct [-0.020, +0.005] (n 86) | +0.002 [-0.009, +0.013] pct [-0.008, +0.013] (n 86) | +0.003 [-0.002, +0.008] pct [-0.001, +0.008] (n 86) | -0.004 [-0.010, +0.002] pct [-0.010, +0.002] (n 86) | -0.004 [-0.013, +0.004] pct [-0.013, +0.004] (n 86) | -0.014 [-0.027, -0.001] pct [-0.026, -0.001] (n 86) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 86) |

**RICH · private_bdf · NCE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → APR | -0.000 [-0.002, +0.001] pct [-0.001, +0.000] (n 64) | -0.000 [-0.002, +0.001] pct [-0.001, +0.000] (n 64) |

**RICH · private_bdf · CS_SINGLE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → APR | -0.001 [-0.002, +0.000] pct [-0.002, +0.000] (n 64) | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) |

**RICH · fau · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | -0.006 [-0.017, +0.006] pct [-0.017, +0.005] (n 67) | +0.001 [-0.004, +0.007] pct [-0.004, +0.007] (n 67) | -0.002 [-0.005, +0.001] pct [-0.005, +0.000] (n 67) | -0.002 [-0.007, +0.003] pct [-0.007, +0.003] (n 67) | -0.005 [-0.014, +0.004] pct [-0.014, +0.004] (n 67) | -0.012 [-0.018, -0.006] pct [-0.018, -0.007] (n 67) | -0.003 [-0.009, +0.003] pct [-0.009, +0.003] (n 67) |

**RICH · fau · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APR | -0.001 [-0.008, +0.006] pct [-0.008, +0.006] (n 67) | +0.001 [-0.002, +0.004] pct [-0.002, +0.004] (n 67) | +0.001 [-0.001, +0.004] pct [-0.001, +0.004] (n 67) | -0.000 [-0.005, +0.005] pct [-0.005, +0.004] (n 67) | -0.000 [-0.007, +0.006] pct [-0.007, +0.006] (n 67) | +0.008 [-0.002, +0.017] pct [-0.002, +0.017] (n 67) | +0.004 [-0.000, +0.009] pct [-0.000, +0.009] (n 67) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 67) |

**RICH · dtu · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | +0.051 [+0.034, +0.068] pct [+0.037, +0.067] (n 44) | +0.014 [+0.007, +0.022] pct [+0.007, +0.021] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.029 [+0.023, +0.036] pct [+0.024, +0.036] (n 44) | +0.054 [+0.041, +0.067] pct [+0.043, +0.066] (n 44) | +0.119 [+0.099, +0.138] pct [+0.101, +0.138] (n 44) | +0.020 [+0.010, +0.031] pct [+0.010, +0.030] (n 44) |

**RICH · dtu · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APR | -0.018 [-0.031, -0.004] pct [-0.031, -0.006] (n 44) | +0.001 [-0.006, +0.008] pct [-0.006, +0.008] (n 44) | -0.001 [-0.002, +0.001] pct [-0.002, +0.001] (n 44) | -0.008 [-0.013, -0.002] pct [-0.013, -0.003] (n 44) | -0.014 [-0.023, -0.005] pct [-0.023, -0.006] (n 44) | -0.024 [-0.034, -0.014] pct [-0.034, -0.014] (n 44) | -0.002 [-0.009, +0.005] pct [-0.009, +0.005] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |

**RICH · federici · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → APR | -0.012 [-0.020, -0.004] pct [-0.020, -0.004] (n 86) | +0.004 [-0.001, +0.009] pct [-0.001, +0.009] (n 86) | -0.002 [-1.724, +1.721] pct [-0.004, +0.000] (n 86) | -0.005 [-0.007, -0.002] pct [-0.007, -0.002] (n 86) | -0.006 [-0.012, -0.001] pct [-0.012, -0.001] (n 86) | -0.019 [-0.036, -0.002] pct [-0.036, -0.002] (n 86) |

**RICH · federici · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APR | -0.009 [-0.027, +0.009] pct [-0.027, +0.009] (n 86) | -0.069 [-0.080, -0.059] pct [-0.080, -0.059] (n 86) | +0.001 [-0.002, +0.003] pct [-0.002, +0.003] (n 86) | -0.003 [-0.008, +0.002] pct [-0.008, +0.002] (n 86) | -0.070 [-0.083, -0.056] pct [-0.082, -0.056] (n 86) | -0.005 [-0.015, +0.005] pct [-0.014, +0.005] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |

**CSX · dtu · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APC | +0.120 [+0.068, +0.172] pct [+0.072, +0.172] (n 44) | -0.109 [-0.157, -0.061] pct [-0.155, -0.064] (n 44) | -0.002 [-0.006, +0.001] pct [-0.006, +0.001] (n 44) | +0.003 [-0.001, +0.006] pct [-0.000, +0.006] (n 44) | +0.020 [-0.004, +0.043] pct [-0.003, +0.042] (n 44) | +0.036 [+0.006, +0.066] pct [+0.007, +0.065] (n 44) | +0.000 [-0.008, +0.008] pct [-0.007, +0.007] (n 44) |
| XP → XPC | +0.047 [+0.009, +0.084] pct [+0.013, +0.084] (n 44) | -0.035 [-0.058, -0.012] pct [-0.057, -0.013] (n 44) | +0.000 [-0.004, +0.004] pct [-0.003, +0.004] (n 44) | +0.002 [-0.003, +0.007] pct [-0.002, +0.007] (n 44) | +0.020 [-0.012, +0.051] pct [-0.006, +0.051] (n 44) | +0.004 [-0.023, +0.032] pct [-0.021, +0.032] (n 44) | -0.002 [-0.010, +0.006] pct [-0.010, +0.006] (n 44) |

**CSX · dtu · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APC | +0.051 [+0.015, +0.087] pct [+0.017, +0.086] (n 44) | -0.053 [-0.081, -0.025] pct [-0.081, -0.026] (n 44) | -0.000 [-0.003, +0.002] pct [-0.003, +0.002] (n 44) | -0.000 [-0.003, +0.003] pct [-0.003, +0.002] (n 44) | +0.002 [-0.015, +0.019] pct [-0.015, +0.018] (n 44) | -0.013 [-0.029, +0.004] pct [-0.029, +0.003] (n 44) | +0.001 [-0.005, +0.007] pct [-0.005, +0.007] (n 44) | -0.000 [-0.000, -0.000] pct [-0.000, -0.000] (n 44) |
| XP → XPC | +0.037 [+0.006, +0.068] pct [+0.009, +0.067] (n 44) | -0.045 [-0.074, -0.016] pct [-0.073, -0.019] (n 44) | +0.002 [-0.001, +0.004] pct [-0.001, +0.004] (n 44) | +0.001 [-0.004, +0.005] pct [-0.004, +0.004] (n 44) | +0.004 [-0.016, +0.025] pct [-0.016, +0.024] (n 44) | -0.025 [-0.048, -0.003] pct [-0.047, -0.005] (n 44) | +0.001 [-0.006, +0.008] pct [-0.006, +0.008] (n 44) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |

**CSX · federici · NCE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → APC | +0.013 [-0.006, +0.033] pct [-0.006, +0.033] (n 86) | -0.010 [-0.025, +0.005] pct [-0.024, +0.005] (n 86) | -0.002 [-0.007, +0.004] pct [-0.007, +0.003] (n 86) | +0.000 [-0.008, +0.009] pct [-0.008, +0.008] (n 86) | +0.007 [-0.005, +0.019] pct [-0.005, +0.019] (n 86) | +0.001 [-0.018, +0.020] pct [-0.018, +0.020] (n 86) |
| XP → XPC | -0.017 [-0.033, -0.002] pct [-0.032, -0.002] (n 86) | +0.003 [-0.008, +0.013] pct [-0.007, +0.013] (n 86) | -0.003 [-0.009, +0.002] pct [-0.009, +0.002] (n 86) | -0.008 [-0.015, -0.000] pct [-0.015, -0.000] (n 86) | -0.010 [-0.021, +0.000] pct [-0.021, +0.000] (n 86) | -0.014 [-0.032, +0.003] pct [-0.032, +0.003] (n 86) |

**CSX · federici · CS_SINGLE · T · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APC | +0.004 [-0.011, +0.019] pct [-0.011, +0.019] (n 86) | +0.006 [-0.003, +0.015] pct [-0.003, +0.015] (n 86) | +0.002 [-0.003, +0.007] pct [-0.003, +0.007] (n 86) | +0.006 [-0.002, +0.013] pct [-0.002, +0.014] (n 86) | +0.006 [-0.004, +0.017] pct [-0.004, +0.017] (n 86) | +0.003 [-0.008, +0.014] pct [-0.008, +0.014] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XP → XPC | -0.011 [-0.031, +0.009] pct [-0.030, +0.009] (n 86) | +0.007 [-0.005, +0.019] pct [-0.005, +0.019] (n 86) | -0.002 [-0.008, +0.004] pct [-0.008, +0.004] (n 86) | -0.001 [-0.012, +0.009] pct [-0.012, +0.008] (n 86) | -0.003 [-0.017, +0.012] pct [-0.018, +0.012] (n 86) | +0.002 [-0.012, +0.015] pct [-0.011, +0.015] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |

**CSX · private_bdf · NCE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → APC | -0.000 [-0.002, +0.002] pct [-0.002, +0.001] (n 64) | -0.000 [-0.002, +0.002] pct [-0.001, +0.001] (n 64) |
| XP → XPC | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) |

**CSX · private_bdf · CS_SINGLE · T · seed 3401 only**

| member | hist_gain (cand − ref) | twin_sens (cand − ref) |
|---|---|---|
| AP → APC | -0.000 [-0.001, +0.000] pct [-0.001, +0.000] (n 64) | -0.001 [-0.003, -0.000] pct [-0.003, -0.000] (n 64) |
| XP → XPC | -0.000 [-0.001, +0.001] pct [-0.001, +0.001] (n 64) | -0.001 [-0.002, +0.000] pct [-0.002, +0.000] (n 64) |

**CSX · dtu · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APC | +0.101 [+0.085, +0.117] pct [+0.086, +0.118] (n 44) | -0.001 [-0.009, +0.007] pct [-0.009, +0.006] (n 44) | +0.002 [-0.000, +0.004] pct [+0.000, +0.004] (n 44) | +0.043 [+0.037, +0.050] pct [+0.038, +0.050] (n 44) | +0.086 [+0.074, +0.099] pct [+0.075, +0.098] (n 44) | +0.062 [+0.051, +0.073] pct [+0.052, +0.072] (n 44) | +0.020 [+0.012, +0.028] pct [+0.012, +0.027] (n 44) |
| XP → XPC | +0.012 [-0.003, +0.026] pct [-0.003, +0.025] (n 44) | +0.009 [+0.001, +0.016] pct [+0.001, +0.016] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.013 [+0.005, +0.021] pct [+0.005, +0.020] (n 44) | +0.020 [+0.009, +0.030] pct [+0.010, +0.030] (n 44) | not applicable: native readout of an encoder never trained against v (design §2.11) | -0.006 [-0.017, +0.004] pct [-0.017, +0.003] (n 44) |

**CSX · dtu · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | att_acc (cand − ref) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|---|
| AP → APC | -0.058 [-0.069, -0.047] pct [-0.069, -0.047] (n 44) | +0.047 [+0.040, +0.053] pct [+0.040, +0.053] (n 44) | +0.001 [-0.001, +0.002] pct [-0.001, +0.002] (n 44) | -0.003 [-0.005, -0.000] pct [-0.005, -0.000] (n 44) | -0.016 [-0.023, -0.008] pct [-0.023, -0.009] (n 44) | -0.013 [-0.019, -0.007] pct [-0.019, -0.007] (n 44) | +0.001 [-0.005, +0.007] pct [-0.005, +0.007] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |
| XP → XPC | +0.007 [-0.008, +0.022] pct [-0.008, +0.022] (n 44) | -0.000 [-0.008, +0.008] pct [-0.008, +0.008] (n 44) | +0.001 [-0.001, +0.003] pct [-0.001, +0.003] (n 44) | +0.006 [-0.005, +0.018] pct [-0.005, +0.018] (n 44) | +0.002 [-0.010, +0.014] pct [-0.010, +0.014] (n 44) | +0.028 [+0.019, +0.037] pct [+0.020, +0.037] (n 44) | +0.012 [-0.002, +0.026] pct [-0.001, +0.025] (n 44) | +0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 44) |

**CSX · federici · NCE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) |
|---|---|---|---|---|---|---|
| AP → APC | -0.028 [-0.053, -0.003] pct [-0.053, -0.003] (n 86) | +0.019 [+0.006, +0.032] pct [+0.006, +0.033] (n 86) | -0.001 [-0.003, +0.002] pct [-0.003, +0.002] (n 86) | -0.010 [-0.019, -0.001] pct [-0.019, -0.001] (n 86) | -0.008 [-0.027, +0.010] pct [-0.026, +0.010] (n 86) | +0.122 [+0.085, +0.160] pct [+0.086, +0.159] (n 86) |
| XP → XPC | +0.027 [+0.007, +0.047] pct [+0.007, +0.047] (n 86) | -0.024 [-0.038, -0.011] pct [-0.038, -0.011] (n 86) | +0.001 [-0.002, +0.004] pct [-0.001, +0.004] (n 86) | +0.005 [-0.001, +0.010] pct [-0.001, +0.010] (n 86) | +0.005 [-0.008, +0.018] pct [-0.007, +0.018] (n 86) | not applicable: native readout of an encoder never trained against v (design §2.11) |

**CSX · federici · CS_SINGLE · A · seed 3401 only**

| member | gain (cand − ref) | R_mm (ref − cand) | top1 (cand − ref) | rank_pct (ref − cand) | hard_gain (cand − ref) | R_native (ref − cand) | kernel_cs_diff (cand − ref) |
|---|---|---|---|---|---|---|---|
| AP → APC | -0.008 [-0.018, +0.002] pct [-0.017, +0.001] (n 86) | +0.003 [-0.003, +0.010] pct [-0.003, +0.010] (n 86) | -0.000 [-0.003, +0.003] pct [-0.003, +0.003] (n 86) | -0.003 [-0.008, +0.001] pct [-0.008, +0.001] (n 86) | -0.004 [-0.011, +0.004] pct [-0.011, +0.004] (n 86) | +0.004 [-0.009, +0.017] pct [-0.008, +0.017] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |
| XP → XPC | -0.001 [-0.019, +0.016] pct [-0.019, +0.015] (n 86) | +0.016 [+0.003, +0.030] pct [+0.004, +0.030] (n 86) | +0.003 [+0.000, +0.006] pct [+0.001, +0.006] (n 86) | -0.010 [-0.020, -0.001] pct [-0.020, -0.001] (n 86) | +0.013 [+0.001, +0.025] pct [+0.002, +0.025] (n 86) | +0.056 [+0.038, +0.075] pct [+0.038, +0.074] (n 86) | -0.000 [-0.000, +0.000] pct [-0.000, +0.000] (n 86) |

## 10. Levels (pointwise; per-group levels for groups with n ≥ 5)

| configuration | n | primary endpoint: est [95 % bootstrap-t] [95 % percentile] | by group: n, est [95 % bootstrap-t] [95 % percentile] |
|---|---|---|---|
| dtu · CS_SINGLE · A · APC · d3401 · t- · primary | 44 | R 9.577 [9.556, 9.597] [9.557, 9.597] | HI: n 22, 9.581 [9.551, 9.612] [9.555, 9.609]; NH: n 22, 9.572 [9.536, 9.607] [9.543, 9.603] |
| dtu · CS_SINGLE · A · APR · d3401 · t- · primary | 44 | R 9.582 [9.554, 9.610] [9.557, 9.610] | HI: n 22, 9.595 [9.559, 9.632] [9.562, 9.631]; NH: n 22, 9.569 [9.524, 9.615] [9.532, 9.611] |
| dtu · CS_SINGLE · A · AP · d3401 · t- · primary | 44 | R 9.565 [9.536, 9.595] [9.538, 9.594] | HI: n 22, 9.575 [9.535, 9.614] [9.540, 9.612]; NH: n 22, 9.556 [9.508, 9.604] [9.518, 9.600] |
| dtu · CS_SINGLE · A · J* · d3401 · t- · primary | 44 | R 9.598 [9.577, 9.619] [9.579, 9.619] | HI: n 22, 9.610 [9.580, 9.640] [9.584, 9.638]; NH: n 22, 9.586 [9.554, 9.619] [9.560, 9.616] |
| dtu · CS_SINGLE · A · XM · d3401 · t- · primary | 44 | R 9.665 [9.653, 9.678] [9.654, 9.677] | HI: n 22, 9.675 [9.656, 9.693] [9.658, 9.692]; NH: n 22, 9.656 [9.638, 9.673] [9.641, 9.672] |
| dtu · CS_SINGLE · A · XPC · d3401 · t- · primary | 44 | R 9.607 [9.593, 9.620] [9.594, 9.620] | HI: n 22, 9.608 [9.588, 9.629] [9.590, 9.628]; NH: n 22, 9.605 [9.588, 9.623] [9.589, 9.622] |
| dtu · CS_SINGLE · A · XP · d3401 · t- · primary | 44 | R 9.614 [9.599, 9.629] [9.599, 9.628] | HI: n 22, 9.601 [9.580, 9.622] [9.582, 9.621]; NH: n 22, 9.626 [9.604, 9.648] [9.606, 9.647] |
| dtu · CS_SINGLE · C · AP · d3401 · t- · primary | 44 | R 9.576 [9.548, 9.604] [9.551, 9.603] | HI: n 22, 9.567 [9.528, 9.606] [9.533, 9.602]; NH: n 22, 9.585 [9.538, 9.632] [9.547, 9.628] |
| dtu · CS_SINGLE · C · J* · d3401 · t- · primary | 44 | R 9.594 [9.573, 9.614] [9.574, 9.614] | HI: n 22, 9.591 [9.562, 9.620] [9.565, 9.618]; NH: n 22, 9.596 [9.563, 9.628] [9.569, 9.626] |
| dtu · CS_SINGLE · C · XP · d3401 · t- · primary | 44 | R 9.620 [9.605, 9.635] [9.606, 9.635] | HI: n 22, 9.609 [9.586, 9.632] [9.588, 9.630]; NH: n 22, 9.632 [9.611, 9.652] [9.614, 9.651] |
| dtu · CS_SINGLE · T · APC · d3401 · t3401 · primary | 44 | R 9.128 [9.019, 9.237] [9.023, 9.235] | HI: n 22, 8.970 [8.810, 9.130] [8.839, 9.087]; NH: n 22, 9.286 [9.131, 9.441] [9.143, 9.425] |
| dtu · CS_SINGLE · T · APR · d3401 · t3401 · primary | 44 | R 9.160 [9.060, 9.259] [9.063, 9.255] | HI: n 22, 9.019 [8.874, 9.164] [8.891, 9.126]; NH: n 22, 9.300 [9.158, 9.443] [9.170, 9.433] |
| dtu · CS_SINGLE · T · AP · d3401 · t3401 · primary | 44 | R 9.126 [9.018, 9.234] [9.022, 9.228] | HI: n 22, 8.973 [8.821, 9.124] [8.841, 9.083]; NH: n 22, 9.280 [9.134, 9.425] [9.154, 9.418] |
| dtu · CS_SINGLE · T · J* · d3401 · t3401 · primary | 44 | R 9.180 [9.080, 9.280] [9.082, 9.277] | HI: n 22, 9.042 [8.899, 9.184] [8.920, 9.137]; NH: n 22, 9.319 [9.167, 9.472] [9.182, 9.460] |
| dtu · CS_SINGLE · T · S · d- · t3401 · primary | 44 | R 9.138 [9.039, 9.236] [9.044, 9.232] | HI: n 22, 8.999 [8.881, 9.118] [8.889, 9.097]; NH: n 22, 9.276 [9.129, 9.422] [9.142, 9.412] |
| dtu · CS_SINGLE · T · XM · d3401 · t3401 · primary | 44 | R 9.227 [9.135, 9.319] [9.137, 9.314] | HI: n 22, 9.103 [8.979, 9.227] [8.985, 9.198]; NH: n 22, 9.351 [9.214, 9.488] [9.229, 9.480] |
| dtu · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 44 | R 9.224 [9.133, 9.316] [9.135, 9.310] | HI: n 22, 9.101 [8.986, 9.217] [8.992, 9.195]; NH: n 22, 9.347 [9.212, 9.482] [9.226, 9.473] |
| dtu · CS_SINGLE · T · XP · d3401 · t3401 · primary | 44 | R 9.217 [9.123, 9.310] [9.126, 9.308] | HI: n 22, 9.090 [8.950, 9.230] [8.970, 9.188]; NH: n 22, 9.343 [9.209, 9.477] [9.226, 9.468] |
| dtu · NCE · A · APC · d3401 · t- · primary | 44 | R 9.472 [9.438, 9.507] [9.440, 9.506] | HI: n 22, 9.463 [9.410, 9.515] [9.416, 9.512]; NH: n 22, 9.482 [9.429, 9.536] [9.438, 9.529] |
| dtu · NCE · A · APR · d3401 · t- · primary | 44 | R 9.508 [9.477, 9.538] [9.479, 9.538] | HI: n 22, 9.505 [9.461, 9.550] [9.466, 9.547]; NH: n 22, 9.510 [9.463, 9.556] [9.470, 9.552] |
| dtu · NCE · A · AP · d3401 · t- · primary | 44 | R 9.573 [9.540, 9.605] [9.542, 9.604] | HI: n 22, 9.579 [9.534, 9.624] [9.541, 9.621]; NH: n 22, 9.566 [9.514, 9.618] [9.523, 9.613] |
| dtu · NCE · A · J* · d3401 · t- · primary | 44 | R 9.583 [9.550, 9.615] [9.553, 9.613] | HI: n 22, 9.594 [9.546, 9.641] [9.552, 9.636]; NH: n 22, 9.572 [9.521, 9.623] [9.530, 9.618] |
| dtu · NCE · A · XM · d3401 · t- · primary | 44 | R 9.623 [9.611, 9.634] [9.612, 9.634] | HI: n 22, 9.618 [9.600, 9.636] [9.601, 9.633]; NH: n 22, 9.628 [9.612, 9.644] [9.614, 9.643] |
| dtu · NCE · A · XPC · d3401 · t- · primary | 44 | R 9.579 [9.558, 9.600] [9.559, 9.599] | HI: n 22, 9.578 [9.543, 9.613] [9.547, 9.609]; NH: n 22, 9.580 [9.552, 9.607] [9.556, 9.606] |
| dtu · NCE · A · XP · d3401 · t- · primary | 44 | R 9.599 [9.581, 9.618] [9.582, 9.617] | HI: n 22, 9.600 [9.571, 9.628] [9.574, 9.626]; NH: n 22, 9.599 [9.568, 9.629] [9.575, 9.625] |
| dtu · NCE · C · AP · d3401 · t- · primary | 44 | R 9.590 [9.556, 9.625] [9.557, 9.622] | HI: n 22, 9.587 [9.539, 9.635] [9.546, 9.632]; NH: n 22, 9.594 [9.541, 9.647] [9.549, 9.642] |
| dtu · NCE · C · J* · d3401 · t- · primary | 44 | R 9.600 [9.566, 9.634] [9.569, 9.632] | HI: n 22, 9.601 [9.552, 9.650] [9.561, 9.646]; NH: n 22, 9.599 [9.547, 9.651] [9.555, 9.648] |
| dtu · NCE · C · XP · d3401 · t- · primary | 44 | R 9.597 [9.577, 9.617] [9.578, 9.616] | HI: n 22, 9.594 [9.567, 9.621] [9.569, 9.619]; NH: n 22, 9.600 [9.569, 9.632] [9.573, 9.630] |
| dtu · NCE · T · APC · d3401 · t3401 · primary | 44 | R 8.981 [8.841, 9.120] [8.842, 9.112] | HI: n 22, 8.786 [8.589, 8.983] [8.612, 8.929]; NH: n 22, 9.175 [8.984, 9.367] [9.003, 9.353] |
| dtu · NCE · T · APR · d3401 · t3401 · primary | 44 | R 8.981 [8.850, 9.111] [8.852, 9.108] | HI: n 22, 8.802 [8.616, 8.987] [8.635, 8.947]; NH: n 22, 9.160 [8.973, 9.347] [8.992, 9.336] |
| dtu · NCE · T · AP · d3401 · t3401 · primary | 44 | R 8.992 [8.868, 9.116] [8.871, 9.109] | HI: n 22, 8.826 [8.640, 9.012] [8.669, 8.959]; NH: n 22, 9.158 [8.982, 9.334] [8.995, 9.318] |
| dtu · NCE · T · J* · d3401 · t3401 · primary | 44 | R 8.996 [8.875, 9.117] [8.875, 9.109] | HI: n 22, 8.827 [8.652, 9.003] [8.668, 8.957]; NH: n 22, 9.165 [8.993, 9.336] [9.007, 9.322] |
| dtu · NCE · T · S · d- · t3401 · primary | 44 | R 9.067 [8.953, 9.180] [8.954, 9.174] | HI: n 22, 8.913 [8.746, 9.080] [8.758, 9.044]; NH: n 22, 9.220 [9.056, 9.383] [9.071, 9.370] |
| dtu · NCE · T · XM · d3401 · t3401 · primary | 44 | R 9.044 [8.920, 9.168] [8.924, 9.162] | HI: n 22, 8.884 [8.718, 9.049] [8.729, 9.016]; NH: n 22, 9.204 [9.034, 9.373] [9.048, 9.360] |
| dtu · NCE · T · XPC · d3401 · t3401 · primary | 44 | R 9.034 [8.911, 9.156] [8.914, 9.152] | HI: n 22, 8.859 [8.684, 9.035] [8.698, 8.998]; NH: n 22, 9.208 [9.050, 9.367] [9.057, 9.354] |
| dtu · NCE · T · XP · d3401 · t3401 · primary | 44 | R 9.045 [8.922, 9.169] [8.922, 9.161] | HI: n 22, 8.882 [8.688, 9.075] [8.717, 9.021]; NH: n 22, 9.209 [9.052, 9.366] [9.063, 9.352] |
| fau · CS_SINGLE · A · APR · d3401 · t- · primary | 67 | R 6.707 [6.686, 6.728] [6.687, 6.728] | CI: n 24, 6.716 [6.662, 6.769] [6.665, 6.762]; HA: n 29, 6.706 [6.681, 6.730] [6.684, 6.729]; TH: n 14, 6.697 [6.663, 6.731] [6.667, 6.727] |
| fau · CS_SINGLE · A · AP · d3401 · t- · primary | 67 | R 6.707 [6.685, 6.729] [6.685, 6.728] | CI: n 24, 6.704 [6.651, 6.757] [6.656, 6.752]; HA: n 29, 6.709 [6.683, 6.735] [6.685, 6.735]; TH: n 14, 6.709 [6.672, 6.745] [6.677, 6.742] |
| fau · CS_SINGLE · A · J* · d3401 · t- · primary | 67 | R 6.626 [6.604, 6.649] [6.605, 6.648] | CI: n 24, 6.662 [6.616, 6.708] [6.619, 6.701]; HA: n 29, 6.589 [6.564, 6.613] [6.565, 6.612]; TH: n 14, 6.644 [6.606, 6.681] [6.613, 6.677] |
| fau · CS_SINGLE · A · XM · d3401 · t- · primary | 67 | R 6.682 [6.671, 6.693] [6.671, 6.693] | CI: n 24, 6.710 [6.687, 6.732] [6.690, 6.730]; HA: n 29, 6.659 [6.645, 6.673] [6.646, 6.671]; TH: n 14, 6.683 [6.668, 6.697] [6.669, 6.695] |
| fau · CS_SINGLE · A · XP · d3401 · t- · primary | 67 | R 6.708 [6.688, 6.728] [6.688, 6.727] | CI: n 24, 6.726 [6.673, 6.780] [6.677, 6.774]; HA: n 29, 6.690 [6.671, 6.709] [6.672, 6.708]; TH: n 14, 6.712 [6.688, 6.735] [6.691, 6.732] |
| fau · CS_SINGLE · B · AP · d3401 · t- · primary | 67 | R 6.706 [6.676, 6.737] [6.675, 6.736] | CI: n 24, 6.702 [6.622, 6.783] [6.628, 6.774]; HA: n 29, 6.710 [6.684, 6.735] [6.687, 6.735]; TH: n 14, 6.706 [6.670, 6.742] [6.676, 6.738] |
| fau · CS_SINGLE · B · J* · d3401 · t- · primary | 67 | R 6.602 [6.564, 6.640] [6.566, 6.635] | CI: n 24, 6.599 [6.492, 6.705] [6.506, 6.679]; HA: n 29, 6.585 [6.558, 6.613] [6.559, 6.611]; TH: n 14, 6.641 [6.605, 6.677] [6.611, 6.674] |
| fau · CS_SINGLE · B · XP · d3401 · t- · primary | 67 | R 6.677 [6.633, 6.721] [6.635, 6.713] | CI: n 24, 6.644 [6.529, 6.759] [6.535, 6.737]; HA: n 29, 6.689 [6.669, 6.709] [6.670, 6.707]; TH: n 14, 6.709 [6.686, 6.732] [6.689, 6.729] |
| fau · CS_SINGLE · C · AP · d3401 · t- · primary | 67 | R 6.742 [6.712, 6.772] [6.711, 6.771] | CI: n 24, 6.720 [6.640, 6.800] [6.644, 6.794]; HA: n 29, 6.760 [6.734, 6.785] [6.735, 6.784]; TH: n 14, 6.744 [6.709, 6.778] [6.713, 6.776] |
| fau · CS_SINGLE · C · J* · d3401 · t- · primary | 67 | R 6.597 [6.566, 6.628] [6.566, 6.625] | CI: n 24, 6.590 [6.508, 6.672] [6.513, 6.658]; HA: n 29, 6.582 [6.556, 6.608] [6.559, 6.607]; TH: n 14, 6.640 [6.602, 6.678] [6.611, 6.674] |
| fau · CS_SINGLE · C · XP · d3401 · t- · primary | 67 | R 6.689 [6.642, 6.735] [6.648, 6.724] | CI: n 24, 6.642 [6.510, 6.774] [6.531, 6.739]; HA: n 29, 6.711 [6.695, 6.728] [6.695, 6.726]; TH: n 14, 6.723 [6.702, 6.745] [6.705, 6.741] |
| fau · CS_SINGLE · T · APR · d3401 · t3401 · primary | 67 | R 6.479 [6.372, 6.585] [6.376, 6.583] | CI: n 24, 6.759 [6.548, 6.969] [6.574, 6.949]; HA: n 29, 6.242 [6.130, 6.355] [6.144, 6.352]; TH: n 14, 6.489 [6.304, 6.675] [6.330, 6.641] |
| fau · CS_SINGLE · T · AP · d3401 · t3401 · primary | 67 | R 6.470 [6.373, 6.567] [6.377, 6.568] | CI: n 24, 6.723 [6.542, 6.903] [6.554, 6.897]; HA: n 29, 6.253 [6.141, 6.365] [6.152, 6.365]; TH: n 14, 6.487 [6.307, 6.667] [6.329, 6.628] |
| fau · CS_SINGLE · T · J* · d3401 · t3401 · primary | 67 | R 6.495 [6.394, 6.596] [6.401, 6.591] | CI: n 24, 6.727 [6.540, 6.915] [6.562, 6.902]; HA: n 29, 6.293 [6.179, 6.407] [6.190, 6.402]; TH: n 14, 6.515 [6.347, 6.683] [6.380, 6.654] |
| fau · CS_SINGLE · T · S · d- · t3401 · primary | 67 | R 6.465 [6.360, 6.569] [6.367, 6.568] | CI: n 24, 6.710 [6.513, 6.907] [6.533, 6.893]; HA: n 29, 6.246 [6.124, 6.367] [6.135, 6.358]; TH: n 14, 6.497 [6.330, 6.665] [6.348, 6.634] |
| fau · CS_SINGLE · T · XM · d3401 · t3401 · primary | 67 | R 6.474 [6.385, 6.563] [6.388, 6.561] | CI: n 24, 6.677 [6.517, 6.838] [6.526, 6.824]; HA: n 29, 6.279 [6.162, 6.396] [6.175, 6.389]; TH: n 14, 6.530 [6.364, 6.695] [6.382, 6.665] |
| fau · CS_SINGLE · T · XP · d3401 · t3401 · primary | 67 | R 6.480 [6.383, 6.577] [6.387, 6.574] | CI: n 24, 6.703 [6.536, 6.869] [6.551, 6.856]; HA: n 29, 6.270 [6.148, 6.392] [6.161, 6.384]; TH: n 14, 6.534 [6.356, 6.712] [6.380, 6.680] |
| fau · NCE · A · APR · d3401 · t- · primary | 67 | R 6.819 [6.781, 6.856] [6.782, 6.856] | CI: n 24, 6.790 [6.703, 6.877] [6.711, 6.872]; HA: n 29, 6.847 [6.798, 6.895] [6.802, 6.893]; TH: n 14, 6.810 [6.662, 6.958] [6.761, 6.875] |
| fau · NCE · A · AP · d3401 · t- · primary | 67 | R 6.814 [6.773, 6.856] [6.774, 6.854] | CI: n 24, 6.785 [6.692, 6.877] [6.699, 6.871]; HA: n 29, 6.843 [6.789, 6.897] [6.794, 6.893]; TH: n 14, 6.806 [6.710, 6.902] [6.757, 6.869] |
| fau · NCE · A · J* · d3401 · t- · primary | 67 | R 6.810 [6.768, 6.851] [6.769, 6.851] | CI: n 24, 6.805 [6.708, 6.902] [6.715, 6.895]; HA: n 29, 6.830 [6.771, 6.888] [6.776, 6.884]; TH: n 14, 6.776 [6.702, 6.850] [6.730, 6.835] |
| fau · NCE · A · XM · d3401 · t- · primary | 67 | R 6.683 [6.671, 6.694] [6.672, 6.694] | CI: n 24, 6.693 [6.667, 6.718] [6.668, 6.716]; HA: n 29, 6.674 [6.658, 6.690] [6.659, 6.688]; TH: n 14, 6.684 [6.661, 6.706] [6.665, 6.700] |
| fau · NCE · A · XP · d3401 · t- · primary | 67 | R 6.645 [6.617, 6.673] [6.618, 6.672] | CI: n 24, 6.715 [6.658, 6.773] [6.663, 6.769]; HA: n 29, 6.594 [6.565, 6.624] [6.567, 6.623]; TH: n 14, 6.629 [6.588, 6.671] [6.594, 6.664] |
| fau · NCE · B · AP · d3401 · t- · primary | 67 | R 6.839 [6.786, 6.891] [6.789, 6.890] | CI: n 24, 6.848 [6.717, 6.979] [6.730, 6.970]; HA: n 29, 6.847 [6.790, 6.904] [6.797, 6.901]; TH: n 14, 6.805 [6.710, 6.901] [6.755, 6.871] |
| fau · NCE · B · J* · d3401 · t- · primary | 67 | R 6.845 [6.781, 6.910] [6.787, 6.910] | CI: n 24, 6.903 [6.726, 7.080] [6.749, 7.064]; HA: n 29, 6.832 [6.775, 6.888] [6.781, 6.885]; TH: n 14, 6.774 [6.700, 6.849] [6.728, 6.831] |
| fau · NCE · B · XP · d3401 · t- · primary | 67 | R 6.628 [6.599, 6.657] [6.599, 6.658] | CI: n 24, 6.674 [6.602, 6.745] [6.606, 6.737]; HA: n 29, 6.592 [6.560, 6.624] [6.563, 6.621]; TH: n 14, 6.624 [6.583, 6.665] [6.588, 6.659] |
| fau · NCE · C · AP · d3401 · t- · primary | 67 | R 6.963 [6.895, 7.031] [6.900, 7.031] | CI: n 24, 6.958 [6.768, 7.149] [6.795, 7.132]; HA: n 29, 6.989 [6.931, 7.048] [6.936, 7.045]; TH: n 14, 6.914 [6.828, 7.001] [6.856, 6.979] |
| fau · NCE · C · J* · d3401 · t- · primary | 67 | R 6.960 [6.875, 7.044] [6.887, 7.043] | CI: n 24, 7.025 [6.795, 7.254] [6.841, 7.236]; HA: n 29, 6.951 [6.891, 7.011] [6.892, 7.007]; TH: n 14, 6.867 [6.796, 6.938] [6.814, 6.928] |
| fau · NCE · C · XP · d3401 · t- · primary | 67 | R 6.644 [6.614, 6.674] [6.614, 6.672] | CI: n 24, 6.671 [6.592, 6.750] [6.598, 6.731]; HA: n 29, 6.622 [6.590, 6.653] [6.593, 6.652]; TH: n 14, 6.644 [6.599, 6.689] [6.605, 6.680] |
| fau · NCE · T · APR · d3401 · t3401 · primary | 67 | R 6.444 [6.313, 6.575] [6.327, 6.574] | CI: n 24, 6.766 [6.493, 7.040] [6.548, 7.013]; HA: n 29, 6.167 [6.040, 6.295] [6.050, 6.289]; TH: n 14, 6.466 [6.240, 6.692] [6.274, 6.651] |
| fau · NCE · T · AP · d3401 · t3401 · primary | 67 | R 6.460 [6.330, 6.591] [6.341, 6.588] | CI: n 24, 6.786 [6.525, 7.046] [6.567, 7.034]; HA: n 29, 6.180 [6.058, 6.302] [6.064, 6.297]; TH: n 14, 6.482 [6.269, 6.696] [6.298, 6.663] |
| fau · NCE · T · J* · d3401 · t3401 · primary | 67 | R 6.458 [6.331, 6.585] [6.341, 6.582] | CI: n 24, 6.762 [6.492, 7.031] [6.549, 6.999]; HA: n 29, 6.192 [6.067, 6.318] [6.080, 6.312]; TH: n 14, 6.489 [6.271, 6.706] [6.302, 6.672] |
| fau · NCE · T · S · d- · t3401 · primary | 67 | R 6.465 [6.352, 6.579] [6.362, 6.581] | CI: n 24, 6.735 [6.511, 6.959] [6.553, 6.943]; HA: n 29, 6.228 [6.106, 6.349] [6.118, 6.346]; TH: n 14, 6.495 [6.298, 6.692] [6.317, 6.651] |
| fau · NCE · T · XM · d3401 · t3401 · primary | 67 | R 6.455 [6.336, 6.575] [6.346, 6.569] | CI: n 24, 6.755 [6.511, 7.000] [6.553, 6.983]; HA: n 29, 6.195 [6.075, 6.316] [6.089, 6.313]; TH: n 14, 6.479 [6.289, 6.670] [6.317, 6.641] |
| fau · NCE · T · XP · d3401 · t3401 · primary | 67 | R 6.454 [6.345, 6.564] [6.354, 6.567] | CI: n 24, 6.735 [6.521, 6.949] [6.549, 6.935]; HA: n 29, 6.205 [6.075, 6.334] [6.088, 6.329]; TH: n 14, 6.491 [6.294, 6.687] [6.320, 6.653] |
| federici · CS_SINGLE · A · APC · d3401 · t- · primary | 86 | R 8.262 [8.229, 8.295] [8.228, 8.292] | CI: n 33, 8.248 [8.178, 8.318] [8.181, 8.313]; HC: n 37, 8.281 [8.242, 8.320] [8.243, 8.318]; HC-v: n 16, 8.247 [8.178, 8.315] [8.185, 8.306] |
| federici · CS_SINGLE · A · APR · d3401 · t- · primary | 86 | R 8.336 [8.290, 8.381] [8.291, 8.379] | CI: n 33, 8.310 [8.213, 8.407] [8.215, 8.396]; HC: n 37, 8.362 [8.313, 8.411] [8.313, 8.408]; HC-v: n 16, 8.327 [8.236, 8.417] [8.247, 8.402] |
| federici · CS_SINGLE · A · AP · d3401 · t- · primary | 86 | R 8.257 [8.225, 8.290] [8.225, 8.289] | CI: n 33, 8.246 [8.179, 8.313] [8.180, 8.306]; HC: n 37, 8.272 [8.230, 8.314] [8.232, 8.312]; HC-v: n 16, 8.247 [8.184, 8.310] [8.190, 8.303] |
| federici · CS_SINGLE · A · J* · d3401 · t- · primary | 86 | R 8.311 [8.265, 8.357] [8.266, 8.354] | CI: n 33, 8.274 [8.179, 8.368] [8.182, 8.357]; HC: n 37, 8.344 [8.291, 8.398] [8.293, 8.395]; HC-v: n 16, 8.311 [8.217, 8.406] [8.229, 8.394] |
| federici · CS_SINGLE · A · XM · d3401 · t- · primary | 86 | R 8.236 [8.218, 8.254] [8.218, 8.254] | CI: n 33, 8.238 [8.200, 8.276] [8.202, 8.274]; HC: n 37, 8.241 [8.217, 8.266] [8.218, 8.265]; HC-v: n 16, 8.219 [8.188, 8.249] [8.193, 8.245] |
| federici · CS_SINGLE · A · XPC · d3401 · t- · primary | 86 | R 8.218 [8.198, 8.237] [8.198, 8.236] | CI: n 33, 8.205 [8.167, 8.243] [8.169, 8.239]; HC: n 37, 8.230 [8.206, 8.254] [8.207, 8.252]; HC-v: n 16, 8.215 [8.163, 8.268] [8.170, 8.262] |
| federici · CS_SINGLE · A · XP · d3401 · t- · primary | 86 | R 8.232 [8.209, 8.256] [8.210, 8.255] | CI: n 33, 8.216 [8.167, 8.264] [8.168, 8.260]; HC: n 37, 8.246 [8.217, 8.275] [8.217, 8.273]; HC-v: n 16, 8.235 [8.184, 8.286] [8.191, 8.280] |
| federici · CS_SINGLE · C_partial · AP · d3401 · t- · primary | 86 | R 8.250 [8.219, 8.281] [8.220, 8.280] | CI: n 33, 8.245 [8.182, 8.309] [8.182, 8.302]; HC: n 37, 8.257 [8.219, 8.294] [8.221, 8.292]; HC-v: n 16, 8.245 [8.174, 8.315] [8.185, 8.309] |
| federici · CS_SINGLE · C_partial · J* · d3401 · t- · primary | 86 | R 8.308 [8.267, 8.350] [8.267, 8.348] | CI: n 33, 8.286 [8.201, 8.371] [8.206, 8.363]; HC: n 37, 8.329 [8.277, 8.382] [8.279, 8.382]; HC-v: n 16, 8.307 [8.210, 8.404] [8.229, 8.392] |
| federici · CS_SINGLE · C_partial · XP · d3401 · t- · primary | 86 | R 8.233 [8.210, 8.256] [8.210, 8.256] | CI: n 33, 8.224 [8.175, 8.272] [8.177, 8.267]; HC: n 37, 8.239 [8.210, 8.268] [8.211, 8.267]; HC-v: n 16, 8.238 [8.182, 8.294] [8.190, 8.287] |
| federici · CS_SINGLE · T · APC · d3401 · t3401 · primary | 86 | R 8.088 [8.053, 8.122] [8.054, 8.122] | CI: n 33, 8.073 [8.009, 8.137] [8.013, 8.132]; HC: n 37, 8.082 [8.031, 8.133] [8.032, 8.131]; HC-v: n 16, 8.132 [8.046, 8.218] [8.063, 8.208] |
| federici · CS_SINGLE · T · APR · d3401 · t3401 · primary | 86 | R 8.103 [8.071, 8.135] [8.070, 8.134] | CI: n 33, 8.091 [8.031, 8.151] [8.037, 8.149]; HC: n 37, 8.106 [8.060, 8.153] [8.062, 8.151]; HC-v: n 16, 8.119 [8.050, 8.188] [8.058, 8.179] |
| federici · CS_SINGLE · T · AP · d3401 · t3401 · primary | 86 | R 8.098 [8.064, 8.132] [8.064, 8.132] | CI: n 33, 8.090 [8.026, 8.154] [8.030, 8.151]; HC: n 37, 8.101 [8.052, 8.150] [8.054, 8.146]; HC-v: n 16, 8.108 [8.023, 8.192] [8.038, 8.182] |
| federici · CS_SINGLE · T · J* · d3401 · t3401 · primary | 86 | R 8.104 [8.071, 8.136] [8.071, 8.135] | CI: n 33, 8.089 [8.030, 8.147] [8.033, 8.144]; HC: n 37, 8.107 [8.056, 8.158] [8.058, 8.155]; HC-v: n 16, 8.127 [8.056, 8.199] [8.069, 8.190] |
| federici · CS_SINGLE · T · S · d- · t3401 · primary | 86 | R 8.098 [8.067, 8.130] [8.066, 8.130] | CI: n 33, 8.096 [8.036, 8.156] [8.038, 8.152]; HC: n 37, 8.085 [8.038, 8.132] [8.039, 8.129]; HC-v: n 16, 8.134 [8.056, 8.212] [8.067, 8.203] |
| federici · CS_SINGLE · T · XM · d3401 · t3401 · primary | 86 | R 8.101 [8.064, 8.137] [8.064, 8.136] | CI: n 33, 8.092 [8.025, 8.159] [8.026, 8.155]; HC: n 37, 8.089 [8.034, 8.145] [8.037, 8.145]; HC-v: n 16, 8.146 [8.076, 8.217] [8.084, 8.209] |
| federici · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 86 | R 8.102 [8.068, 8.135] [8.069, 8.134] | CI: n 33, 8.101 [8.038, 8.164] [8.039, 8.161]; HC: n 37, 8.088 [8.037, 8.139] [8.039, 8.137]; HC-v: n 16, 8.135 [8.069, 8.202] [8.079, 8.196] |
| federici · CS_SINGLE · T · XP · d3401 · t3401 · primary | 86 | R 8.098 [8.064, 8.131] [8.066, 8.132] | CI: n 33, 8.095 [8.037, 8.153] [8.039, 8.148]; HC: n 37, 8.087 [8.036, 8.138] [8.039, 8.136]; HC-v: n 16, 8.129 [8.047, 8.211] [8.059, 8.198] |
| federici · NCE · A · APC · d3401 · t- · primary | 86 | R 8.379 [8.332, 8.426] [8.333, 8.426] | CI: n 33, 8.401 [8.302, 8.501] [8.308, 8.493]; HC: n 37, 8.355 [8.295, 8.415] [8.296, 8.408]; HC-v: n 16, 8.389 [8.302, 8.476] [8.310, 8.465] |
| federici · NCE · A · APR · d3401 · t- · primary | 86 | R 8.378 [8.333, 8.424] [8.333, 8.422] | CI: n 33, 8.387 [8.291, 8.483] [8.297, 8.477]; HC: n 37, 8.376 [8.313, 8.439] [8.317, 8.433]; HC-v: n 16, 8.366 [8.280, 8.452] [8.290, 8.443] |
| federici · NCE · A · AP · d3401 · t- · primary | 86 | R 8.371 [8.324, 8.417] [8.323, 8.415] | CI: n 33, 8.377 [8.279, 8.475] [8.283, 8.466]; HC: n 37, 8.374 [8.312, 8.436] [8.316, 8.429]; HC-v: n 16, 8.348 [8.261, 8.436] [8.274, 8.425] |
| federici · NCE · A · J* · d3401 · t- · primary | 86 | R 8.308 [8.266, 8.350] [8.268, 8.350] | CI: n 33, 8.287 [8.203, 8.372] [8.206, 8.361]; HC: n 37, 8.338 [8.278, 8.397] [8.282, 8.395]; HC-v: n 16, 8.283 [8.194, 8.373] [8.203, 8.365] |
| federici · NCE · A · XM · d3401 · t- · primary | 86 | R 8.236 [8.210, 8.262] [8.210, 8.261] | CI: n 33, 8.250 [8.199, 8.300] [8.203, 8.296]; HC: n 37, 8.223 [8.188, 8.259] [8.190, 8.257]; HC-v: n 16, 8.236 [8.171, 8.300] [8.179, 8.291] |
| federici · NCE · A · XPC · d3401 · t- · primary | 86 | R 8.301 [8.257, 8.345] [8.258, 8.344] | CI: n 33, 8.277 [8.192, 8.362] [8.197, 8.356]; HC: n 37, 8.334 [8.278, 8.389] [8.281, 8.387]; HC-v: n 16, 8.275 [8.171, 8.379] [8.183, 8.366] |
| federici · NCE · A · XP · d3401 · t- · primary | 86 | R 8.304 [8.262, 8.345] [8.264, 8.345] | CI: n 33, 8.285 [8.201, 8.368] [8.206, 8.360]; HC: n 37, 8.323 [8.270, 8.376] [8.272, 8.371]; HC-v: n 16, 8.298 [8.199, 8.397] [8.211, 8.385] |
| federici · NCE · C_partial · AP · d3401 · t- · primary | 86 | R 8.330 [8.285, 8.376] [8.286, 8.374] | CI: n 33, 8.328 [8.238, 8.418] [8.245, 8.411]; HC: n 37, 8.334 [8.270, 8.398] [8.272, 8.393]; HC-v: n 16, 8.328 [8.245, 8.410] [8.256, 8.402] |
| federici · NCE · C_partial · J* · d3401 · t- · primary | 86 | R 8.322 [8.279, 8.365] [8.279, 8.362] | CI: n 33, 8.295 [8.202, 8.387] [8.212, 8.374]; HC: n 37, 8.355 [8.298, 8.413] [8.304, 8.412]; HC-v: n 16, 8.299 [8.206, 8.392] [8.219, 8.380] |
| federici · NCE · C_partial · XP · d3401 · t- · primary | 86 | R 8.312 [8.270, 8.355] [8.272, 8.355] | CI: n 33, 8.294 [8.208, 8.381] [8.212, 8.375]; HC: n 37, 8.332 [8.278, 8.385] [8.281, 8.383]; HC-v: n 16, 8.305 [8.202, 8.408] [8.213, 8.392] |
| federici · NCE · T · APC · d3401 · t3401 · primary | 86 | R 8.086 [8.050, 8.123] [8.049, 8.123] | CI: n 33, 8.081 [8.010, 8.153] [8.014, 8.149]; HC: n 37, 8.072 [8.021, 8.124] [8.020, 8.120]; HC-v: n 16, 8.129 [8.052, 8.207] [8.064, 8.197] |
| federici · NCE · T · APR · d3401 · t3401 · primary | 86 | R 8.077 [8.038, 8.116] [8.040, 8.115] | CI: n 33, 8.070 [7.997, 8.142] [8.001, 8.137]; HC: n 37, 8.062 [8.007, 8.116] [8.007, 8.113]; HC-v: n 16, 8.129 [8.041, 8.217] [8.053, 8.206] |
| federici · NCE · T · AP · d3401 · t3401 · primary | 86 | R 8.090 [8.053, 8.127] [8.053, 8.126] | CI: n 33, 8.091 [8.022, 8.160] [8.027, 8.158]; HC: n 37, 8.071 [8.021, 8.121] [8.024, 8.118]; HC-v: n 16, 8.130 [8.041, 8.220] [8.058, 8.205] |
| federici · NCE · T · J* · d3401 · t3401 · primary | 86 | R 8.096 [8.061, 8.131] [8.064, 8.131] | CI: n 33, 8.099 [8.029, 8.168] [8.037, 8.167]; HC: n 37, 8.074 [8.031, 8.118] [8.034, 8.116]; HC-v: n 16, 8.140 [8.066, 8.215] [8.077, 8.210] |
| federici · NCE · T · S · d- · t3401 · primary | 86 | R 8.104 [8.068, 8.140] [8.068, 8.139] | CI: n 33, 8.106 [8.040, 8.171] [8.044, 8.170]; HC: n 37, 8.093 [8.040, 8.147] [8.042, 8.142]; HC-v: n 16, 8.126 [8.037, 8.215] [8.054, 8.202] |
| federici · NCE · T · XM · d3401 · t3401 · primary | 86 | R 8.092 [8.058, 8.126] [8.059, 8.125] | CI: n 33, 8.078 [8.015, 8.141] [8.018, 8.137]; HC: n 37, 8.092 [8.043, 8.141] [8.045, 8.138]; HC-v: n 16, 8.122 [8.041, 8.203] [8.056, 8.194] |
| federici · NCE · T · XPC · d3401 · t3401 · primary | 86 | R 8.095 [8.062, 8.127] [8.063, 8.127] | CI: n 33, 8.081 [8.017, 8.145] [8.022, 8.140]; HC: n 37, 8.088 [8.041, 8.134] [8.044, 8.133]; HC-v: n 16, 8.138 [8.063, 8.213] [8.073, 8.206] |
| federici · NCE · T · XP · d3401 · t3401 · primary | 86 | R 8.080 [8.047, 8.114] [8.048, 8.113] | CI: n 33, 8.067 [8.006, 8.128] [8.009, 8.125]; HC: n 37, 8.078 [8.029, 8.127] [8.032, 8.125]; HC-v: n 16, 8.114 [8.029, 8.199] [8.050, 8.186] |
| private_bdf · CS_SINGLE · T · APC · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.720] [0.710, 0.719]; NH: n 9, 0.716 [0.707, 0.725] [0.709, 0.724] |
| private_bdf · CS_SINGLE · T · APC · d3401 · t3401 · primary | 64 | AUC 0.551 [0.536, 0.565] [0.537, 0.565] | HA: n 55, 0.548 [0.532, 0.563] [0.533, 0.563]; NH: n 9, 0.570 [0.524, 0.616] [0.535, 0.606] |
| private_bdf · CS_SINGLE · T · APR · d3401 · t3401 · primary | 64 | NLL 0.714 [0.709, 0.719] [0.710, 0.718] | HA: n 55, 0.715 [0.709, 0.720] [0.710, 0.719]; NH: n 9, 0.713 [0.703, 0.723] [0.706, 0.721] |
| private_bdf · CS_SINGLE · T · APR · d3401 · t3401 · primary | 64 | AUC 0.553 [0.538, 0.568] [0.539, 0.568] | HA: n 55, 0.548 [0.531, 0.564] [0.533, 0.564]; NH: n 9, 0.586 [0.534, 0.637] [0.547, 0.625] |
| private_bdf · CS_SINGLE · T · AP · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.715 [0.706, 0.724] [0.709, 0.722] |
| private_bdf · CS_SINGLE · T · AP · d3401 · t3401 · primary | 64 | AUC 0.548 [0.533, 0.562] [0.533, 0.562] | HA: n 55, 0.543 [0.527, 0.559] [0.528, 0.558]; NH: n 9, 0.577 [0.527, 0.627] [0.539, 0.613] |
| private_bdf · CS_SINGLE · T · AP · d3407 · t3407 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.710, 0.719]; NH: n 9, 0.714 [0.704, 0.723] [0.706, 0.721] |
| private_bdf · CS_SINGLE · T · AP · d3407 · t3407 · primary | 64 | AUC 0.550 [0.535, 0.565] [0.535, 0.564] | HA: n 55, 0.544 [0.529, 0.559] [0.530, 0.559]; NH: n 9, 0.585 [0.528, 0.641] [0.543, 0.627] |
| private_bdf · CS_SINGLE · T · AP · d3413 · t3413 · primary | 64 | NLL 0.715 [0.711, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.720] [0.710, 0.719]; NH: n 9, 0.714 [0.703, 0.726] [0.705, 0.723] |
| private_bdf · CS_SINGLE · T · AP · d3413 · t3413 · primary | 64 | AUC 0.550 [0.534, 0.566] [0.534, 0.565] | HA: n 55, 0.545 [0.528, 0.561] [0.529, 0.561]; NH: n 9, 0.581 [0.516, 0.646] [0.531, 0.631] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | NLL 0.716 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.716 [0.709, 0.722] [0.710, 0.720]; NH: n 9, 0.715 [0.708, 0.722] [0.710, 0.721] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | AUC 0.544 [0.532, 0.557] [0.532, 0.556] | HA: n 55, 0.539 [0.526, 0.551] [0.526, 0.551]; NH: n 9, 0.578 [0.538, 0.619] [0.547, 0.610] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | NLL 0.715 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.722] [0.710, 0.719]; NH: n 9, 0.714 [0.707, 0.722] [0.709, 0.720] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | AUC 0.548 [0.535, 0.561] [0.536, 0.561] | HA: n 55, 0.542 [0.529, 0.555] [0.530, 0.556]; NH: n 9, 0.586 [0.539, 0.633] [0.550, 0.620] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | NLL 0.716 [0.711, 0.721] [0.712, 0.720] | HA: n 55, 0.716 [0.710, 0.722] [0.712, 0.720]; NH: n 9, 0.716 [0.707, 0.724] [0.710, 0.722] |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | AUC 0.541 [0.528, 0.554] [0.529, 0.554] | HA: n 55, 0.536 [0.522, 0.549] [0.523, 0.549]; NH: n 9, 0.574 [0.530, 0.618] [0.540, 0.608] |
| private_bdf · CS_SINGLE · T · J* · d3401 · t3401 · primary | 64 | NLL 0.715 [0.711, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.710, 0.719]; NH: n 9, 0.716 [0.708, 0.723] [0.711, 0.722] |
| private_bdf · CS_SINGLE · T · J* · d3401 · t3401 · primary | 64 | AUC 0.548 [0.534, 0.561] [0.534, 0.561] | HA: n 55, 0.543 [0.529, 0.557] [0.530, 0.557]; NH: n 9, 0.575 [0.534, 0.615] [0.542, 0.607] |
| private_bdf · CS_SINGLE · T · J* · d3407 · t3407 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.710, 0.719]; NH: n 9, 0.713 [0.703, 0.723] [0.706, 0.721] |
| private_bdf · CS_SINGLE · T · J* · d3407 · t3407 · primary | 64 | AUC 0.550 [0.536, 0.565] [0.536, 0.565] | HA: n 55, 0.545 [0.530, 0.560] [0.530, 0.559]; NH: n 9, 0.585 [0.528, 0.641] [0.543, 0.626] |
| private_bdf · CS_SINGLE · T · J* · d3413 · t3413 · primary | 64 | NLL 0.715 [0.710, 0.719] [0.710, 0.719] | HA: n 55, 0.715 [0.710, 0.720] [0.710, 0.719]; NH: n 9, 0.713 [0.702, 0.724] [0.704, 0.722] |
| private_bdf · CS_SINGLE · T · J* · d3413 · t3413 · primary | 64 | AUC 0.551 [0.535, 0.567] [0.535, 0.567] | HA: n 55, 0.546 [0.529, 0.563] [0.530, 0.561]; NH: n 9, 0.583 [0.515, 0.650] [0.533, 0.632] |
| private_bdf · CS_SINGLE · T · S · d- · t3401 · primary | 64 | NLL 0.716 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.716 [0.709, 0.722] [0.711, 0.720]; NH: n 9, 0.715 [0.708, 0.723] [0.710, 0.721] |
| private_bdf · CS_SINGLE · T · S · d- · t3401 · primary | 64 | AUC 0.543 [0.530, 0.555] [0.531, 0.555] | HA: n 55, 0.538 [0.525, 0.550] [0.526, 0.550]; NH: n 9, 0.573 [0.535, 0.610] [0.544, 0.602] |
| private_bdf · CS_SINGLE · T · S · d- · t3407 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.710, 0.719]; NH: n 9, 0.715 [0.709, 0.721] [0.710, 0.720] |
| private_bdf · CS_SINGLE · T · S · d- · t3407 · primary | 64 | AUC 0.545 [0.532, 0.557] [0.533, 0.557] | HA: n 55, 0.540 [0.526, 0.554] [0.527, 0.553]; NH: n 9, 0.573 [0.543, 0.603] [0.549, 0.595] |
| private_bdf · CS_SINGLE · T · S · d- · t3413 · primary | 64 | NLL 0.716 [0.711, 0.722] [0.712, 0.720] | HA: n 55, 0.716 [0.710, 0.723] [0.711, 0.720]; NH: n 9, 0.716 [0.709, 0.723] [0.711, 0.722] |
| private_bdf · CS_SINGLE · T · S · d- · t3413 · primary | 64 | AUC 0.540 [0.527, 0.553] [0.528, 0.552] | HA: n 55, 0.536 [0.522, 0.550] [0.523, 0.549]; NH: n 9, 0.567 [0.525, 0.610] [0.535, 0.598] |
| private_bdf · CS_SINGLE · T · XM · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.710, 0.718] | HA: n 55, 0.715 [0.708, 0.721] [0.710, 0.718]; NH: n 9, 0.717 [0.711, 0.723] [0.712, 0.722] |
| private_bdf · CS_SINGLE · T · XM · d3401 · t3401 · primary | 64 | AUC 0.548 [0.536, 0.561] [0.536, 0.561] | HA: n 55, 0.545 [0.531, 0.559] [0.532, 0.559]; NH: n 9, 0.568 [0.527, 0.610] [0.538, 0.602] |
| private_bdf · CS_SINGLE · T · XM · d3407 · t3407 · primary | 64 | NLL 0.715 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.722] [0.710, 0.719]; NH: n 9, 0.716 [0.709, 0.723] [0.711, 0.721] |
| private_bdf · CS_SINGLE · T · XM · d3407 · t3407 · primary | 64 | AUC 0.546 [0.533, 0.558] [0.534, 0.558] | HA: n 55, 0.542 [0.529, 0.556] [0.530, 0.556]; NH: n 9, 0.566 [0.528, 0.604] [0.539, 0.595] |
| private_bdf · CS_SINGLE · T · XM · d3413 · t3413 · primary | 64 | NLL 0.716 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.722] [0.710, 0.719]; NH: n 9, 0.716 [0.710, 0.723] [0.712, 0.722] |
| private_bdf · CS_SINGLE · T · XM · d3413 · t3413 · primary | 64 | AUC 0.545 [0.532, 0.558] [0.532, 0.557] | HA: n 55, 0.540 [0.527, 0.554] [0.527, 0.553]; NH: n 9, 0.573 [0.533, 0.612] [0.542, 0.603] |
| private_bdf · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.710, 0.718] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.714 [0.706, 0.722] [0.708, 0.720] |
| private_bdf · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 64 | AUC 0.550 [0.535, 0.564] [0.536, 0.564] | HA: n 55, 0.546 [0.531, 0.560] [0.532, 0.560]; NH: n 9, 0.575 [0.524, 0.626] [0.536, 0.613] |
| private_bdf · CS_SINGLE · T · XP · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.715 [0.707, 0.723] [0.710, 0.722] |
| private_bdf · CS_SINGLE · T · XP · d3401 · t3401 · primary | 64 | AUC 0.548 [0.536, 0.560] [0.536, 0.560] | HA: n 55, 0.544 [0.531, 0.557] [0.532, 0.556]; NH: n 9, 0.572 [0.534, 0.611] [0.544, 0.603] |
| private_bdf · CS_SINGLE · T · XP · d3407 · t3407 · primary | 64 | NLL 0.716 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.722] [0.710, 0.719]; NH: n 9, 0.717 [0.710, 0.724] [0.712, 0.723] |
| private_bdf · CS_SINGLE · T · XP · d3407 · t3407 · primary | 64 | AUC 0.544 [0.532, 0.557] [0.532, 0.556] | HA: n 55, 0.541 [0.528, 0.555] [0.529, 0.554]; NH: n 9, 0.562 [0.524, 0.600] [0.534, 0.588] |
| private_bdf · CS_SINGLE · T · XP · d3413 · t3413 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.715 [0.707, 0.724] [0.709, 0.722] |
| private_bdf · CS_SINGLE · T · XP · d3413 · t3413 · primary | 64 | AUC 0.548 [0.534, 0.562] [0.534, 0.561] | HA: n 55, 0.543 [0.528, 0.558] [0.528, 0.558]; NH: n 9, 0.577 [0.530, 0.624] [0.542, 0.613] |
| private_bdf · NCE · T · APC · d3401 · t3401 · primary | 64 | NLL 0.714 [0.710, 0.719] [0.710, 0.718] | HA: n 55, 0.714 [0.709, 0.720] [0.709, 0.718]; NH: n 9, 0.713 [0.703, 0.723] [0.706, 0.722] |
| private_bdf · NCE · T · APC · d3401 · t3401 · primary | 64 | AUC 0.552 [0.537, 0.567] [0.538, 0.567] | HA: n 55, 0.546 [0.531, 0.562] [0.531, 0.561]; NH: n 9, 0.588 [0.536, 0.640] [0.550, 0.628] |
| private_bdf · NCE · T · APR · d3401 · t3401 · primary | 64 | NLL 0.714 [0.709, 0.718] [0.709, 0.717] | HA: n 55, 0.714 [0.708, 0.720] [0.709, 0.718]; NH: n 9, 0.713 [0.704, 0.722] [0.706, 0.721] |
| private_bdf · NCE · T · APR · d3401 · t3401 · primary | 64 | AUC 0.555 [0.540, 0.571] [0.541, 0.571] | HA: n 55, 0.551 [0.535, 0.567] [0.536, 0.567]; NH: n 9, 0.585 [0.537, 0.632] [0.547, 0.621] |
| private_bdf · NCE · T · AP · d3401 · t3401 · primary | 64 | NLL 0.714 [0.709, 0.719] [0.709, 0.718] | HA: n 55, 0.714 [0.708, 0.720] [0.709, 0.718]; NH: n 9, 0.714 [0.706, 0.722] [0.707, 0.721] |
| private_bdf · NCE · T · AP · d3401 · t3401 · primary | 64 | AUC 0.553 [0.538, 0.567] [0.539, 0.567] | HA: n 55, 0.548 [0.532, 0.564] [0.533, 0.563]; NH: n 9, 0.581 [0.540, 0.622] [0.550, 0.614] |
| private_bdf · NCE · T · AP · d3407 · t3407 · primary | 64 | NLL 0.714 [0.709, 0.720] [0.710, 0.718] | HA: n 55, 0.715 [0.708, 0.721] [0.710, 0.719]; NH: n 9, 0.713 [0.705, 0.721] [0.707, 0.720] |
| private_bdf · NCE · T · AP · d3407 · t3407 · primary | 64 | AUC 0.550 [0.537, 0.562] [0.537, 0.562] | HA: n 55, 0.544 [0.530, 0.559] [0.531, 0.559]; NH: n 9, 0.581 [0.542, 0.621] [0.553, 0.612] |
| private_bdf · NCE · T · AP · d3413 · t3413 · primary | 64 | NLL 0.715 [0.710, 0.719] [0.710, 0.719] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.714 [0.704, 0.723] [0.706, 0.721] |
| private_bdf · NCE · T · AP · d3413 · t3413 · primary | 64 | AUC 0.547 [0.533, 0.561] [0.534, 0.561] | HA: n 55, 0.542 [0.528, 0.555] [0.529, 0.555]; NH: n 9, 0.580 [0.527, 0.633] [0.541, 0.621] |
| private_bdf · NCE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | NLL 0.717 [0.711, 0.723] [0.713, 0.721] | HA: n 55, 0.717 [0.710, 0.724] [0.712, 0.721]; NH: n 9, 0.719 [0.713, 0.725] [0.715, 0.724] |
| private_bdf · NCE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | AUC 0.522 [0.515, 0.530] [0.515, 0.530] | HA: n 55, 0.520 [0.512, 0.528] [0.512, 0.527]; NH: n 9, 0.539 [0.505, 0.573] [0.513, 0.565] |
| private_bdf · NCE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | NLL 0.718 [0.712, 0.723] [0.713, 0.721] | HA: n 55, 0.717 [0.710, 0.724] [0.712, 0.721]; NH: n 9, 0.720 [0.712, 0.728] [0.716, 0.725] |
| private_bdf · NCE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | AUC 0.524 [0.515, 0.533] [0.516, 0.533] | HA: n 55, 0.521 [0.512, 0.531] [0.512, 0.531]; NH: n 9, 0.541 [0.512, 0.571] [0.519, 0.564] |
| private_bdf · NCE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | NLL 0.717 [0.711, 0.723] [0.712, 0.720] | HA: n 55, 0.717 [0.710, 0.724] [0.712, 0.721]; NH: n 9, 0.719 [0.714, 0.724] [0.715, 0.723] |
| private_bdf · NCE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | AUC 0.528 [0.519, 0.537] [0.519, 0.537] | HA: n 55, 0.526 [0.516, 0.536] [0.516, 0.536]; NH: n 9, 0.539 [0.517, 0.562] [0.522, 0.557] |
| private_bdf · NCE · T · J* · d3401 · t3401 · primary | 64 | NLL 0.714 [0.709, 0.719] [0.709, 0.718] | HA: n 55, 0.714 [0.708, 0.720] [0.709, 0.718]; NH: n 9, 0.713 [0.703, 0.722] [0.706, 0.720] |
| private_bdf · NCE · T · J* · d3401 · t3401 · primary | 64 | AUC 0.555 [0.541, 0.569] [0.542, 0.569] | HA: n 55, 0.550 [0.535, 0.565] [0.537, 0.565]; NH: n 9, 0.586 [0.538, 0.635] [0.549, 0.621] |
| private_bdf · NCE · T · J* · d3407 · t3407 · primary | 64 | NLL 0.714 [0.709, 0.720] [0.710, 0.718] | HA: n 55, 0.715 [0.709, 0.721] [0.709, 0.719]; NH: n 9, 0.713 [0.705, 0.722] [0.707, 0.720] |
| private_bdf · NCE · T · J* · d3407 · t3407 · primary | 64 | AUC 0.550 [0.537, 0.564] [0.538, 0.564] | HA: n 55, 0.545 [0.530, 0.560] [0.531, 0.560]; NH: n 9, 0.581 [0.540, 0.622] [0.552, 0.613] |
| private_bdf · NCE · T · J* · d3413 · t3413 · primary | 64 | NLL 0.715 [0.711, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.710, 0.719]; NH: n 9, 0.715 [0.707, 0.723] [0.709, 0.722] |
| private_bdf · NCE · T · J* · d3413 · t3413 · primary | 64 | AUC 0.545 [0.532, 0.558] [0.533, 0.557] | HA: n 55, 0.539 [0.526, 0.553] [0.527, 0.552]; NH: n 9, 0.577 [0.530, 0.623] [0.542, 0.612] |
| private_bdf · NCE · T · S · d- · t3401 · primary | 64 | NLL 0.716 [0.711, 0.721] [0.711, 0.719] | HA: n 55, 0.716 [0.710, 0.722] [0.711, 0.720]; NH: n 9, 0.714 [0.707, 0.721] [0.709, 0.720] |
| private_bdf · NCE · T · S · d- · t3401 · primary | 64 | AUC 0.541 [0.529, 0.553] [0.529, 0.552] | HA: n 55, 0.534 [0.522, 0.547] [0.522, 0.546]; NH: n 9, 0.580 [0.544, 0.616] [0.552, 0.608] |
| private_bdf · NCE · T · S · d- · t3407 · primary | 64 | NLL 0.715 [0.710, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.708, 0.722] [0.710, 0.719]; NH: n 9, 0.716 [0.710, 0.722] [0.711, 0.721] |
| private_bdf · NCE · T · S · d- · t3407 · primary | 64 | AUC 0.542 [0.531, 0.553] [0.531, 0.553] | HA: n 55, 0.538 [0.525, 0.550] [0.526, 0.550]; NH: n 9, 0.567 [0.533, 0.601] [0.542, 0.594] |
| private_bdf · NCE · T · S · d- · t3413 · primary | 64 | NLL 0.716 [0.711, 0.721] [0.711, 0.719] | HA: n 55, 0.716 [0.710, 0.722] [0.711, 0.720]; NH: n 9, 0.714 [0.705, 0.723] [0.707, 0.721] |
| private_bdf · NCE · T · S · d- · t3413 · primary | 64 | AUC 0.540 [0.528, 0.553] [0.528, 0.553] | HA: n 55, 0.535 [0.522, 0.548] [0.523, 0.548]; NH: n 9, 0.572 [0.532, 0.612] [0.541, 0.604] |
| private_bdf · NCE · T · XM · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.719] [0.710, 0.718] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.714 [0.704, 0.723] [0.707, 0.722] |
| private_bdf · NCE · T · XM · d3401 · t3401 · primary | 64 | AUC 0.548 [0.534, 0.561] [0.535, 0.560] | HA: n 55, 0.542 [0.529, 0.555] [0.529, 0.555]; NH: n 9, 0.582 [0.536, 0.628] [0.548, 0.617] |
| private_bdf · NCE · T · XM · d3407 · t3407 · primary | 64 | NLL 0.716 [0.711, 0.721] [0.711, 0.719] | HA: n 55, 0.715 [0.710, 0.721] [0.711, 0.719]; NH: n 9, 0.716 [0.707, 0.725] [0.710, 0.723] |
| private_bdf · NCE · T · XM · d3407 · t3407 · primary | 64 | AUC 0.542 [0.529, 0.554] [0.530, 0.554] | HA: n 55, 0.537 [0.524, 0.551] [0.525, 0.550]; NH: n 9, 0.567 [0.528, 0.606] [0.537, 0.597] |
| private_bdf · NCE · T · XM · d3413 · t3413 · primary | 64 | NLL 0.714 [0.709, 0.719] [0.710, 0.718] | HA: n 55, 0.714 [0.708, 0.720] [0.709, 0.718]; NH: n 9, 0.714 [0.705, 0.722] [0.707, 0.721] |
| private_bdf · NCE · T · XM · d3413 · t3413 · primary | 64 | AUC 0.552 [0.539, 0.566] [0.539, 0.566] | HA: n 55, 0.548 [0.533, 0.563] [0.534, 0.563]; NH: n 9, 0.581 [0.536, 0.626] [0.547, 0.615] |
| private_bdf · NCE · T · XPC · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.720] [0.711, 0.719] | HA: n 55, 0.715 [0.709, 0.721] [0.710, 0.719]; NH: n 9, 0.716 [0.709, 0.723] [0.711, 0.722] |
| private_bdf · NCE · T · XPC · d3401 · t3401 · primary | 64 | AUC 0.543 [0.530, 0.555] [0.531, 0.555] | HA: n 55, 0.539 [0.526, 0.553] [0.526, 0.552]; NH: n 9, 0.565 [0.523, 0.606] [0.534, 0.596] |
| private_bdf · NCE · T · XP · d3401 · t3401 · primary | 64 | NLL 0.715 [0.710, 0.719] [0.710, 0.719] | HA: n 55, 0.715 [0.709, 0.720] [0.710, 0.719]; NH: n 9, 0.715 [0.707, 0.722] [0.709, 0.721] |
| private_bdf · NCE · T · XP · d3401 · t3401 · primary | 64 | AUC 0.548 [0.535, 0.561] [0.535, 0.561] | HA: n 55, 0.544 [0.530, 0.558] [0.530, 0.557]; NH: n 9, 0.574 [0.536, 0.612] [0.548, 0.603] |
| private_bdf · NCE · T · XP · d3407 · t3407 · primary | 64 | NLL 0.716 [0.711, 0.721] [0.711, 0.720] | HA: n 55, 0.716 [0.710, 0.721] [0.711, 0.720]; NH: n 9, 0.716 [0.707, 0.726] [0.710, 0.724] |
| private_bdf · NCE · T · XP · d3407 · t3407 · primary | 64 | AUC 0.541 [0.527, 0.554] [0.528, 0.554] | HA: n 55, 0.537 [0.522, 0.552] [0.523, 0.551]; NH: n 9, 0.565 [0.528, 0.603] [0.536, 0.593] |
| private_bdf · NCE · T · XP · d3413 · t3413 · primary | 64 | NLL 0.715 [0.710, 0.719] [0.710, 0.718] | HA: n 55, 0.715 [0.709, 0.720] [0.710, 0.719]; NH: n 9, 0.714 [0.704, 0.723] [0.707, 0.722] |
| private_bdf · NCE · T · XP · d3413 · t3413 · primary | 64 | AUC 0.550 [0.535, 0.564] [0.536, 0.564] | HA: n 55, 0.544 [0.530, 0.559] [0.530, 0.559]; NH: n 9, 0.581 [0.531, 0.632] [0.544, 0.619] |

## 11. Notes

- none

## Estimands (design §5.4 and §5.6, fixed before any result)

- **INIT.** Donor pretraining with this supervision vs scratch, at the same target budget; S → XM is donor-EEG exposure without stimulus-locked pairing. INIT > 0 shows that the pretrained initialisation lowers risk at this budget; it does not by itself separate transferable sound structure from easier optimisation (S → XM and CONTROL separate the two partly).
- **SUPERVISION.** AP → J* and XP → J* are the two separate paired differences of OBJECTIVES §4; AP → XP compares the supervision types. No max over arms, no per-identity best method. 'Both supervisions contribute' needs both AP → J* and XP → J* above 0 at the λ chosen on donor dev; a gain at one λ or in one mode only is reported with that scope.
- **CONTROL.** Stimulus-locked supervision vs exposure-matched mismatched pretraining on the same donor EEG. Without CONTROL > 0, a gain of that arm over scratch is reported as possibly an exposure or optimisation effect.
- **RICH / CSX.** Data-and-target additions at equal updates; gains that appear only with more data or more targets are reported as such, not as a loss-function advantage.
- **ACCESS.** Dependence of zero-shot values on the stimulus-informed ICA and on target statistics (descriptive), not a method comparison. Mode-A values carry the declared target-side preprocessing access; FAU CI values in modes B and C are not interpretable as neural tracking (§2.13).
- **SELECTION.** Sensitivity of the checkpoint-selection rule (risk-selected → gain-selected), and the donor-side selection quantities as recorded (descriptive).
- **PANEL.** The established private_transfer role at seeds 3401, 3407 and 3413. E_LOCAL lag_local_tokens full (250 Hz native, 0.5–45 Hz, ALN3 recipe) is a different-input-contract reference, descriptive, not an initialisation contrast.
- **All.** These statements describe estimands; they are not a list of permitted sentences, and interpretation may change with new evidence (design §5.6).

## Appendix A. Coverage per configuration

| stage | block | cohort | objective | mode | slot | d / t seed | version | registered | complete | technical_failed | missing | other | excluded | selection levels | sensitivity evaluations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bridge | core | dtu | CS_SINGLE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | CS_SINGLE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | CS_SINGLE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | CS_SINGLE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | NCE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | NCE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | NCE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | dtu | NCE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | CS_SINGLE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | CS_SINGLE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | CS_SINGLE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | CS_SINGLE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | NCE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | NCE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | NCE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | fau | NCE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | CS_SINGLE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | CS_SINGLE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | CS_SINGLE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | CS_SINGLE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | NCE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | NCE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | NCE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | federici | NCE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | CS_SINGLE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | CS_SINGLE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | CS_SINGLE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | CS_SINGLE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | NCE | - | AP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | NCE | - | J* | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | NCE | - | XM | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | core | private_bdf | NCE | - | XP | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | dtu | CS_SINGLE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | dtu | CS_SINGLE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | dtu | NCE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | dtu | NCE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | federici | CS_SINGLE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | federici | CS_SINGLE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | federici | NCE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | federici | NCE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | private_bdf | CS_SINGLE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | private_bdf | CS_SINGLE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | private_bdf | NCE | - | APC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | csx | private_bdf | NCE | - | XPC | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | AP | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | AP | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | J* | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | J* | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | XM | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | XM | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | XP | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | CS_SINGLE | - | XP | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | AP | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | AP | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | J* | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | J* | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | XM | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | XM | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | XP | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | panel | private_bdf | NCE | - | XP | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | dtu | CS_SINGLE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | dtu | NCE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | fau | CS_SINGLE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | fau | NCE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | federici | CS_SINGLE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | federici | NCE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | private_bdf | CS_SINGLE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| bridge | rich | private_bdf | NCE | - | APR | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L3 ×1 (no declared level 1) | – |
| donor_group | core | dtu | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | dtu | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | fau | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | fau | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | federici | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | federici | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | private_bdf | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | core | private_bdf | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | dtu | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | dtu | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | federici | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | federici | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | private_bdf | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | csx | private_bdf | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | panel | private_bdf | CS_SINGLE | - | - | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | panel | private_bdf | CS_SINGLE | - | - | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | panel | private_bdf | NCE | - | - | 3407 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | panel | private_bdf | NCE | - | - | 3413 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | dtu | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | dtu | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | fau | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | fau | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | federici | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | federici | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | private_bdf | CS_SINGLE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| donor_group | rich | private_bdf | NCE | - | - | 3401 / - | primary | 1 | 1 | 0 | 0 | 0 | 0 | L2 ×1 (as declared 1) | – |
| reference | aln3_native | private_bdf | CS_SINGLE | T | E_LOCAL | - / 3401 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| reference | aln3_native | private_bdf | CS_SINGLE | T | E_LOCAL | - / 3407 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| reference | aln3_native | private_bdf | CS_SINGLE | T | E_LOCAL | - / 3413 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| reference | aln3_native | private_bdf | NCE | T | E_LOCAL | - / 3401 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| reference | aln3_native | private_bdf | NCE | T | E_LOCAL | - / 3407 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| reference | aln3_native | private_bdf | NCE | T | E_LOCAL | - / 3413 | aln3_native | 5 | 5 | 0 | 0 | 0 | 0 | none ×5 (no declared level 5) | – |
| target | core | dtu | CS_SINGLE | T | AP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 6, identical 4 |
| target | core | dtu | CS_SINGLE | T | J* | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 8, identical 2 |
| target | core | dtu | CS_SINGLE | T | S | - / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 9, identical 1 |
| target | core | dtu | CS_SINGLE | T | XM | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 5, identical 5 |
| target | core | dtu | CS_SINGLE | T | XP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 5, identical 5 |
| target | core | dtu | NCE | T | AP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | dtu | NCE | T | J* | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | dtu | NCE | T | S | - / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 9, identical 1 |
| target | core | dtu | NCE | T | XM | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | dtu | NCE | T | XP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | CS_SINGLE | T | AP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 4, identical 6 |
| target | core | fau | CS_SINGLE | T | J* | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | CS_SINGLE | T | S | - / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 9, identical 1 |
| target | core | fau | CS_SINGLE | T | XM | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 8, identical 2 |
| target | core | fau | CS_SINGLE | T | XP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 5, identical 5 |
| target | core | fau | NCE | T | AP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | NCE | T | J* | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | NCE | T | S | - / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | NCE | T | XM | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | fau | NCE | T | XP | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | core | federici | CS_SINGLE | T | AP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | federici | CS_SINGLE | T | J* | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | federici | CS_SINGLE | T | S | - / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | federici | CS_SINGLE | T | XM | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | federici | CS_SINGLE | T | XP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | federici | NCE | T | AP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | federici | NCE | T | J* | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | federici | NCE | T | S | - / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | federici | NCE | T | XM | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | federici | NCE | T | XP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | private_bdf | CS_SINGLE | T | AP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 4, identical 1 |
| target | core | private_bdf | CS_SINGLE | T | J* | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | private_bdf | CS_SINGLE | T | S | - / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | core | private_bdf | CS_SINGLE | T | XM | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 2, identical 3 |
| target | core | private_bdf | CS_SINGLE | T | XP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 1, identical 4 |
| target | core | private_bdf | NCE | T | AP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | private_bdf | NCE | T | J* | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | private_bdf | NCE | T | S | - / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | private_bdf | NCE | T | XM | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | core | private_bdf | NCE | T | XP | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | csx | dtu | CS_SINGLE | T | APC | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 7, identical 3 |
| target | csx | dtu | CS_SINGLE | T | XPC | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 7, identical 3 |
| target | csx | dtu | NCE | T | APC | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | csx | dtu | NCE | T | XPC | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | csx | federici | CS_SINGLE | T | APC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | csx | federici | CS_SINGLE | T | XPC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | csx | federici | NCE | T | APC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | csx | federici | NCE | T | XPC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 4, identical 1 |
| target | csx | private_bdf | CS_SINGLE | T | APC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 1, identical 4 |
| target | csx | private_bdf | CS_SINGLE | T | XPC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 1, identical 4 |
| target | csx | private_bdf | NCE | T | APC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 4, identical 1 |
| target | csx | private_bdf | NCE | T | XPC | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | CS_SINGLE | T | AP | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 2, identical 3 |
| target | panel | private_bdf | CS_SINGLE | T | AP | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | CS_SINGLE | T | J* | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | CS_SINGLE | T | J* | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | CS_SINGLE | T | S | - / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | CS_SINGLE | T | S | - / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | CS_SINGLE | T | XM | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 2, identical 3 |
| target | panel | private_bdf | CS_SINGLE | T | XM | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 4, identical 1 |
| target | panel | private_bdf | CS_SINGLE | T | XP | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 2, identical 3 |
| target | panel | private_bdf | CS_SINGLE | T | XP | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | panel | private_bdf | NCE | T | AP | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | AP | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | J* | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | J* | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | S | - / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | S | - / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | XM | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | XM | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | XP | 3407 / 3407 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | panel | private_bdf | NCE | T | XP | 3413 / 3413 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | rich | dtu | CS_SINGLE | T | APR | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 6, identical 4 |
| target | rich | dtu | NCE | T | APR | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | rich | fau | CS_SINGLE | T | APR | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 3, identical 7 |
| target | rich | fau | NCE | T | APR | 3401 / 3401 | primary | 10 | 10 | 0 | 0 | 0 | 0 | L5 ×10 (as declared 10) | gainsel: evaluated 10 |
| target | rich | federici | CS_SINGLE | T | APR | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | rich | federici | NCE | T | APR | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L5 ×5 (as declared 5) | gainsel: evaluated 5 |
| target | rich | private_bdf | CS_SINGLE | T | APR | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 3, identical 2 |
| target | rich | private_bdf | NCE | T | APR | 3401 / 3401 | primary | 5 | 5 | 0 | 0 | 0 | 0 | L4 ×5 (as declared 5) | gainsel: evaluated 5 |
| zero_shot | access | dtu | CS_SINGLE | C | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | dtu | CS_SINGLE | C | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | dtu | CS_SINGLE | C | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | dtu | NCE | C | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | dtu | NCE | C | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | dtu | NCE | C | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | B | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | B | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | B | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | C | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | C | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | CS_SINGLE | C | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | B | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | B | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | B | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | C | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | C | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | fau | NCE | C | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | access | federici | CS_SINGLE | C_partial | AP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | access | federici | CS_SINGLE | C_partial | J* | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | access | federici | CS_SINGLE | C_partial | XP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | access | federici | NCE | C_partial | AP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | access | federici | NCE | C_partial | J* | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | access | federici | NCE | C_partial | XP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | dtu | CS_SINGLE | A | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | CS_SINGLE | A | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | CS_SINGLE | A | XM | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | CS_SINGLE | A | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | NCE | A | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | NCE | A | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | NCE | A | XM | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | dtu | NCE | A | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | CS_SINGLE | A | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | CS_SINGLE | A | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | CS_SINGLE | A | XM | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | CS_SINGLE | A | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | NCE | A | AP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | NCE | A | J* | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | NCE | A | XM | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | fau | NCE | A | XP | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | core | federici | CS_SINGLE | A | AP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | CS_SINGLE | A | J* | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | CS_SINGLE | A | XM | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | CS_SINGLE | A | XP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | NCE | A | AP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | NCE | A | J* | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | NCE | A | XM | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | core | federici | NCE | A | XP | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | csx | dtu | CS_SINGLE | A | APC | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | csx | dtu | CS_SINGLE | A | XPC | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | csx | dtu | NCE | A | APC | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | csx | dtu | NCE | A | XPC | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | csx | federici | CS_SINGLE | A | APC | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | csx | federici | CS_SINGLE | A | XPC | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | csx | federici | NCE | A | APC | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | csx | federici | NCE | A | XPC | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | rich | dtu | CS_SINGLE | A | APR | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | rich | dtu | NCE | A | APR | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | rich | fau | CS_SINGLE | A | APR | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | rich | fau | NCE | A | APR | 3401 / - | primary | 10 | 10 | 0 | 0 | 0 | 0 | L1 ×10 (as declared 10) | uni_cal: evaluated 10 |
| zero_shot | rich | federici | CS_SINGLE | A | APR | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |
| zero_shot | rich | federici | NCE | A | APR | 3401 / - | primary | 5 | 5 | 0 | 0 | 0 | 0 | L1 ×5 (as declared 5) | uni_cal: evaluated 5 |

## Appendix B. Identities per configuration (primary evaluation)

| configuration | identities | by group | expected (§5.2) | units | units excluded | units per identity |
|---|---|---|---|---|---|---|
| dtu · CS_SINGLE · A · APC · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · APR · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · AP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · J* · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · XM · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · XPC · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · A · XP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · C · AP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · C · J* · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · C · XP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · APC · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · APR · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · AP · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · J* · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · S · d- · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · XM · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · CS_SINGLE · T · XP · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · APC · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · APR · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · AP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · J* · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · XM · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · XPC · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · A · XP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · C · AP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · C · J* · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · C · XP · d3401 · t- · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · APC · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · APR · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · AP · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · J* · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · S · d- · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · XM · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · XPC · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| dtu · NCE · T · XP · d3401 · t3401 · primary | 44 | HI 22, NH 22 | NH 22, HI 22 | 10 | 0 | 2: 44 |
| fau · CS_SINGLE · A · APR · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · A · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · A · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · A · XM · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · A · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · B · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · B · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · B · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · C · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · C · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · C · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · APR · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · AP · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · J* · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · S · d- · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · XM · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · CS_SINGLE · T · XP · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · A · APR · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · A · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · A · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · A · XM · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · A · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · B · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · B · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · B · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · C · AP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · C · J* · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · C · XP · d3401 · t- · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · APR · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · AP · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · J* · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · S · d- · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · XM · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| fau · NCE · T · XP · d3401 · t3401 · primary | 67 | CI 24, HA 29, TH 14 | TH 14, HA 29, CI 24 | 10 | 0 | 2: 67 |
| federici · CS_SINGLE · A · APC · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · APR · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · AP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · J* · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · XM · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · XPC · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · A · XP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · C_partial · AP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · C_partial · J* · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · C_partial · XP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · APC · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · APR · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · AP · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · J* · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · S · d- · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · XM · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · CS_SINGLE · T · XP · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · APC · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · APR · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · AP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · J* · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · XM · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · XPC · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · A · XP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · C_partial · AP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · C_partial · J* · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · C_partial · XP · d3401 · t- · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · APC · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · APR · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · AP · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · J* · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · S · d- · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · XM · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · XPC · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| federici · NCE · T · XP · d3401 · t3401 · primary | 86 | CI 33, HC 37, HC-v 16 | HC 37, CI 33, HC-v 16 | 5 | 0 | 1: 86 |
| private_bdf · CS_SINGLE · T · APC · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · APR · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · AP · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · AP · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · AP · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · J* · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · J* · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · J* · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · S · d- · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · S · d- · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · S · d- · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XM · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XM · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XM · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XPC · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XP · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XP · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · CS_SINGLE · T · XP · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · APC · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · APR · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · AP · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · AP · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · AP · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · E_LOCAL · d- · t3401 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · E_LOCAL · d- · t3407 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · E_LOCAL · d- · t3413 · aln3_native | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · J* · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · J* · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · J* · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · S · d- · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · S · d- · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · S · d- · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XM · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XM · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XM · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XPC · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XP · d3401 · t3401 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XP · d3407 · t3407 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
| private_bdf · NCE · T · XP · d3413 · t3413 · primary | 64 | HA 55, NH 9 | HA 55, NH 9 | 5 | 0 | 1: 64 |
