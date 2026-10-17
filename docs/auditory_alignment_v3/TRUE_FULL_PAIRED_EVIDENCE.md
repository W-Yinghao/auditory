# True-full FM vs same-access local L1, and matched initialization, across seeds — INTERIM

> **Interim.** Generated 2026-10-18 00:13:26 CEST by `python -B -m auditory_alignment_v3.aln34.tf_l1_pairs` (analysis note `private/auditory_alignment_v3/aln34/TF_L1_NOTE.md`, written before any value was computed; its Correction 1 was appended at 2026-10-16 20:36, before the corrected code ran). ALN32_TRUE_FULL panel (seeds 3407/3413, one-step): **334/400 units complete**. Every panel number below covers only the identities whose fold cells are complete and changes when the script is rerun. TF-LOCAL across seeds is a new exploratory paired summary (not an ADDENDUM_11 role). TF-INIT per seed is an interim view of ADDENDUM_11's frozen role; the official version is `aln32_panel_interim.py` after the panel completes.

日期／代码与数据版本 · Date, code and data: 2026-10-18 00:13:26 CEST; code sha256 `aln34/tf_l1_pairs.py` 6674ed303e7d, `bc_interim.py` 2840df81b608, `sci_r1/stats.py` 8bb141cf6070; unit code hashes recomputed now: A_LOCAL `89df1dde3d7a49df`, ALN32_LOCAL_SUPPORT `1b6595fc9ac72f77`, ALN32_TRUE_FULL `88aafcdbd2424299`.

本轮完成／运行／待依赖 · Live state (units by role · seed, summed over datasets): L0 · 3401 complete 25; L0 · 3407 complete 25; L0 · 3413 complete 25; L1 · 3401 complete 25; L1 · 3407 complete 25; L1 · 3413 complete 25; TF/full_onestep_v1 · 3401 complete 200; TF/full_onestep_v1 · 3407 complete 167, queued 32, running 1; TF/full_onestep_v1 · 3413 complete 167, queued 32, running 1; TF/warmup_then_all_v1 · 3401 complete 200.

已见信息与本轮新增信息 · Seen before / new here: all seed-3401 values were already reported in `ALIGNED_INTERFACE_RESULTS.md` (TF-INIT §7, TF-LOCAL §10). The 3401 point estimates here reproduce them exactly. The 3401 intervals do not: bootstrap replicates are seeded by the family label, and the families here have other labels and other members (§1.3, §1.4; §1.6 also recomputes the frozen families). New here: the seed-3407/3413 paired values, the identity mean over seeds, the between-seed range, and the pairing audit. Earlier runs of this script (the first at 2026-10-16 20:09) had been read before this run; the corrections made since then are listed in §5 and in the analysis note (Correction 1).

Sign and unit: ΔR = R(reference) − R(candidate) in bits per 5 s test query; positive = candidate lower true-query risk. Intervals: identity-level bootstrap-t (B = 4,000), conditional on the fitted models (training randomness is not in them); `[a, b]` = 95 % simultaneous (max-t within the dataset × backbone × seed × recipe family; member counts in §1.2–§1.4); n = identities used. No p-values. The 2 inits × 2 lrs × 2 backbones × 3 datasets cells share identities, references and seeds: they are not independent replications, and nothing here extends beyond the seeds, lrs, recipes and the 100 / 50-epoch budgets present.

## 1. 当前观察 · Current observations

### 1.1 Coverage

Identities (human, test): fau 67, dtu 44, federici 86; phantom entities excluded: {'fau': 0, 'dtu': 0, 'federici': 1}. Split consistency: one split fingerprint per fold cell.

| family (contrast · recipe · dataset · backbone · seed) | members | fold cells per member: complete / pending / missing | identities pair-complete per member | identities used (family common set) / cohort |
|---|---|---|---|---|
| TF-INIT · onestep · dtu · cbramod · 3401 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · dtu · cbramod · 3407 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · dtu · cbramod · 3413 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · dtu · reve · 3401 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · dtu · reve · 3407 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · dtu · reve · 3413 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · onestep · fau · cbramod · 3401 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · fau · cbramod · 3407 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · fau · cbramod · 3413 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · fau · reve · 3401 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · fau · reve · 3407 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · fau · reve · 3413 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · onestep · federici · cbramod · 3401 | 2 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-INIT · onestep · federici · cbramod · 3407 | 2 | 1 / 4 / 0 | 19 | 19 / 86 |
| TF-INIT · onestep · federici · cbramod · 3413 | 2 | 1 / 4 / 0 | 19 | 19 / 86 |
| TF-INIT · onestep · federici · reve · 3401 | 2 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-INIT · onestep · federici · reve · 3407 | 2 | 0–1 / 4–5 / 0 | 0–19 | 19 / 86 |
| TF-INIT · onestep · federici · reve · 3413 | 2 | 0–1 / 4–5 / 0 | 0–19 | 19 / 86 |
| TF-INIT · warmup · dtu · cbramod · 3401 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · warmup · dtu · reve · 3401 | 2 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-INIT · warmup · fau · cbramod · 3401 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · warmup · fau · reve · 3401 | 2 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-INIT · warmup · federici · cbramod · 3401 | 2 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-INIT · warmup · federici · reve · 3401 | 2 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-LOCAL · onestep · dtu · cbramod · 3401 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · dtu · cbramod · 3407 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · dtu · cbramod · 3413 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · dtu · reve · 3401 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · dtu · reve · 3407 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · dtu · reve · 3413 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · onestep · fau · cbramod · 3401 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · fau · cbramod · 3407 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · fau · cbramod · 3413 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · fau · reve · 3401 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · fau · reve · 3407 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · fau · reve · 3413 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · onestep · federici · cbramod · 3401 | 4 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-LOCAL · onestep · federici · cbramod · 3407 | 4 | 1 / 4 / 0 | 19 | 19 / 86 |
| TF-LOCAL · onestep · federici · cbramod · 3413 | 4 | 1 / 4 / 0 | 19 | 19 / 86 |
| TF-LOCAL · onestep · federici · reve · 3401 | 4 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-LOCAL · onestep · federici · reve · 3407 | 4 | 0–1 / 4–5 / 0 | 0–19 | 19 / 86 |
| TF-LOCAL · onestep · federici · reve · 3413 | 4 | 0–1 / 4–5 / 0 | 0–19 | 19 / 86 |
| TF-LOCAL · warmup · dtu · cbramod · 3401 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · warmup · dtu · reve · 3401 | 4 | 10 / 0 / 0 | 44 | 44 / 44 |
| TF-LOCAL · warmup · fau · cbramod · 3401 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · warmup · fau · reve · 3401 | 4 | 10 / 0 / 0 | 67 | 67 / 67 |
| TF-LOCAL · warmup · federici · cbramod · 3401 | 4 | 5 / 0 / 0 | 86 | 86 / 86 |
| TF-LOCAL · warmup · federici · reve · 3401 | 4 | 5 / 0 / 0 | 86 | 86 / 86 |

An identity is pair-complete only when every fold cell it appears in is pair-complete; identities with a pending cell are excluded, never averaged over the cells that happen to be done. Family statistics use the identities pair-complete for every member.
Not registered (listed as missing in the JSON audit; nothing is trained for them): TF-INIT warmup in seeds 3407/3413 (200 member × cell pairs); TF-LOCAL warmup in seeds 3407/3413 (400 member × cell pairs).

### 1.2 TF-LOCAL one-step: L1 → true-full FM, unified readout (primary)

Each per-seed cell: ΔR [95 % simultaneous within dataset × backbone × seed, 4 members] n. Identity mean over seeds: identities pair-complete in all three seeds, 95 % simultaneous within dataset × backbone. Between-seed range: per-seed mean paired difference on those same identities (descriptive; three seeds do not estimate a seed distribution).

**Per-seed cells use each seed's own pair-complete identities (n shown).** Seed 3401 covers every identity; the panel seeds cover only the outer folds completed so far. Per-seed values on different identity sets are not a seed comparison; compare seeds through the last two columns, which use the same identities in every seed.

| dataset · backbone | member | seed 3401 | seed 3407 | seed 3413 | identity mean over seeds | between-seed range (same identities) |
|---|---|---|---|---|---|---|
| fau · cbramod | L1->random_full/lr1e-05 | -0.005 [-0.046, +0.036] n 67 | +0.042 [-0.005, +0.089] n 67 | -0.007 [-0.051, +0.038] n 67 | +0.010 [-0.028, +0.049] n 67 | -0.007 … +0.042 (3401: -0.005, 3407: +0.042, 3413: -0.007; n 67) |
| fau · cbramod | L1->random_full/lr0.0003 | +0.025 [-0.018, +0.067] n 67 | +0.071 [+0.035, +0.108] n 67 | +0.056 [+0.021, +0.091] n 67 | +0.051 [+0.019, +0.082] n 67 | +0.025 … +0.071 (3401: +0.025, 3407: +0.071, 3413: +0.056; n 67) |
| fau · cbramod | L1->pretrained_full/lr1e-05 | +0.127 [+0.069, +0.185] n 67 | +0.136 [+0.091, +0.181] n 67 | +0.113 [+0.070, +0.156] n 67 | +0.125 [+0.081, +0.169] n 67 | +0.113 … +0.136 (3401: +0.127, 3407: +0.136, 3413: +0.113; n 67) |
| fau · cbramod | L1->pretrained_full/lr0.0003 | +0.144 [+0.090, +0.199] n 67 | +0.157 [+0.112, +0.201] n 67 | +0.123 [+0.079, +0.168] n 67 | +0.141 [+0.099, +0.184] n 67 | +0.123 … +0.157 (3401: +0.144, 3407: +0.157, 3413: +0.123; n 67) |
| fau · reve | L1->random_full/lr1e-05 | +0.099 [+0.047, +0.152] n 67 | +0.092 [+0.055, +0.129] n 67 | +0.058 [+0.025, +0.091] n 67 | +0.083 [+0.049, +0.117] n 67 | +0.058 … +0.099 (3401: +0.099, 3407: +0.092, 3413: +0.058; n 67) |
| fau · reve | L1->random_full/lr0.0003 | +0.081 [+0.041, +0.120] n 67 | +0.046 [+0.005, +0.086] n 67 | +0.015 [-0.018, +0.048] n 67 | +0.047 [+0.018, +0.076] n 67 | +0.015 … +0.081 (3401: +0.081, 3407: +0.046, 3413: +0.015; n 67) |
| fau · reve | L1->pretrained_full/lr1e-05 | +0.109 [+0.048, +0.171] n 67 | +0.127 [+0.073, +0.181] n 67 | +0.082 [+0.033, +0.132] n 67 | +0.106 [+0.061, +0.152] n 67 | +0.082 … +0.127 (3401: +0.109, 3407: +0.127, 3413: +0.082; n 67) |
| fau · reve | L1->pretrained_full/lr0.0003 | +0.057 [-0.003, +0.118] n 67 | -0.019 [-0.066, +0.028] n 67 | +0.031 [-0.019, +0.080] n 67 | +0.023 [-0.016, +0.062] n 67 | -0.019 … +0.057 (3401: +0.057, 3407: -0.019, 3413: +0.031; n 67) |
| dtu · cbramod | L1->random_full/lr1e-05 | -0.373 [-0.482, -0.264] n 44 | -0.223 [-0.322, -0.123] n 44 | -0.339 [-0.447, -0.231] n 44 | -0.312 [-0.411, -0.213] n 44 | -0.373 … -0.223 (3401: -0.373, 3407: -0.223, 3413: -0.339; n 44) |
| dtu · cbramod | L1->random_full/lr0.0003 | -0.018 [-0.100, +0.064] n 44 | +0.057 [-0.031, +0.145] n 44 | +0.001 [-0.080, +0.081] n 44 | +0.013 [-0.064, +0.090] n 44 | -0.018 … +0.057 (3401: -0.018, 3407: +0.057, 3413: +0.001; n 44) |
| dtu · cbramod | L1->pretrained_full/lr1e-05 | +0.162 [+0.070, +0.254] n 44 | +0.192 [+0.090, +0.294] n 44 | +0.148 [+0.044, +0.252] n 44 | +0.167 [+0.071, +0.264] n 44 | +0.148 … +0.192 (3401: +0.162, 3407: +0.192, 3413: +0.148; n 44) |
| dtu · cbramod | L1->pretrained_full/lr0.0003 | +0.213 [+0.135, +0.292] n 44 | +0.229 [+0.137, +0.322] n 44 | +0.196 [+0.105, +0.288] n 44 | +0.213 [+0.129, +0.297] n 44 | +0.196 … +0.229 (3401: +0.213, 3407: +0.229, 3413: +0.196; n 44) |
| dtu · reve | L1->random_full/lr1e-05 | -0.021 [-0.089, +0.047] n 44 | -0.021 [-0.098, +0.057] n 44 | -0.003 [-0.075, +0.069] n 44 | -0.015 [-0.082, +0.053] n 44 | -0.021 … -0.003 (3401: -0.021, 3407: -0.021, 3413: -0.003; n 44) |
| dtu · reve | L1->random_full/lr0.0003 | -0.059 [-0.132, +0.014] n 44 | -0.001 [-0.082, +0.080] n 44 | -0.077 [-0.148, -0.005] n 44 | -0.046 [-0.114, +0.023] n 44 | -0.077 … -0.001 (3401: -0.059, 3407: -0.001, 3413: -0.077; n 44) |
| dtu · reve | L1->pretrained_full/lr1e-05 | -0.006 [-0.110, +0.098] n 44 | +0.052 [-0.038, +0.143] n 44 | +0.037 [-0.055, +0.128] n 44 | +0.028 [-0.061, +0.116] n 44 | -0.006 … +0.052 (3401: -0.006, 3407: +0.052, 3413: +0.037; n 44) |
| dtu · reve | L1->pretrained_full/lr0.0003 | +0.003 [-0.094, +0.100] n 44 | +0.114 [-0.016, +0.244] n 44 | +0.130 [+0.035, +0.224] n 44 | +0.082 [-0.015, +0.180] n 44 | +0.003 … +0.130 (3401: +0.003, 3407: +0.114, 3413: +0.130; n 44) |
| federici · cbramod | L1->random_full/lr1e-05 | +0.063 [+0.018, +0.108] n 86 | +0.006 [-0.094, +0.106] n 19 | +0.084 [-0.013, +0.180] n 19 | +0.048 [-0.027, +0.122] n 19 | +0.006 … +0.084 (3401: +0.054, 3407: +0.006, 3413: +0.084; n 19) |
| federici · cbramod | L1->random_full/lr0.0003 | +0.141 [+0.073, +0.209] n 86 | +0.081 [-0.062, +0.224] n 19 | +0.159 [+0.011, +0.307] n 19 | +0.144 [+0.002, +0.286] n 19 | +0.081 … +0.192 (3401: +0.192, 3407: +0.081, 3413: +0.159; n 19) |
| federici · cbramod | L1->pretrained_full/lr1e-05 | +0.180 [+0.103, +0.258] n 86 | +0.139 [-0.025, +0.303] n 19 | +0.135 [-0.024, +0.294] n 19 | +0.147 [-0.008, +0.303] n 19 | +0.135 … +0.168 (3401: +0.168, 3407: +0.139, 3413: +0.135; n 19) |
| federici · cbramod | L1->pretrained_full/lr0.0003 | +0.196 [+0.118, +0.275] n 86 | +0.142 [-0.054, +0.338] n 19 | +0.193 [+0.029, +0.356] n 19 | +0.176 [-0.001, +0.354] n 19 | +0.142 … +0.194 (3401: +0.194, 3407: +0.142, 3413: +0.193; n 19) |
| federici · reve | L1->random_full/lr1e-05 | +0.175 [+0.093, +0.256] n 86 | +0.159 [-0.018, +0.335] n 19 | +0.160 [-0.002, +0.322] n 19 | +0.163 [-0.001, +0.326] n 19 | +0.159 … +0.170 (3401: +0.170, 3407: +0.159, 3413: +0.160; n 19) |
| federici · reve | L1->random_full/lr0.0003 | +0.183 [+0.105, +0.261] n 86 | +0.126 [-0.063, +0.316] n 19 | +0.110 [-0.071, +0.292] n 19 | +0.135 [-0.041, +0.311] n 19 | +0.110 … +0.169 (3401: +0.169, 3407: +0.126, 3413: +0.110; n 19) |
| federici · reve | L1->pretrained_full/lr1e-05 | +0.087 [+0.024, +0.151] n 86 | +0.014 [-0.083, +0.112] n 19 | +0.060 [-0.024, +0.145] n 19 | +0.024 [-0.054, +0.102] n 19 | -0.002 … +0.060 (3401: -0.002, 3407: +0.014, 3413: +0.060; n 19) |
| federici · reve | L1->pretrained_full/lr0.0003 | +0.167 [+0.096, +0.238] n 86 | not available (n 0/86) | not available (n 0/86) | not available (n 0/86) | not available |

### 1.3 TF-LOCAL warm-up recipe (seed 3401 only; not registered in the panel)

ΔR [95 % simultaneous within dataset × backbone, 4 warm-up members] n. Already reported in `ALIGNED_INTERFACE_RESULTS.md` §10, where the family is `TF-LOCAL|<dataset>|<backbone>` with 16 members ({L0, L1} × init × recipe × lr). The point estimates are identical. The intervals are not, for two reasons. Bootstrap replicate indices are seeded by the family label (`sci_r1.stats.group_seed(label, metric)`), and the labels here differ from the frozen ones, so even the pointwise intervals differ by bootstrap Monte Carlo error. The simultaneous intervals differ by that error and also by the family's members. Over the seed-3401 unified members, the largest bound difference from the frozen intervals is 0.0038 bits pointwise and 0.0205 bits simultaneous. Recomputed with the frozen labels and members, this script's identity values reproduce the frozen intervals exactly (§1.6).

| dataset · backbone | member | seed 3401 |
|---|---|---|
| fau · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.010 [-0.052, +0.032] n 67 |
| fau · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.042 [+0.003, +0.082] n 67 |
| fau · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.132 [+0.074, +0.189] n 67 |
| fau · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.142 [+0.083, +0.200] n 67 |
| fau · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.092 [+0.043, +0.141] n 67 |
| fau · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.083 [+0.035, +0.131] n 67 |
| fau · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.082 [+0.024, +0.141] n 67 |
| fau · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | -0.043 [-0.107, +0.022] n 67 |
| dtu · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.372 [-0.482, -0.261] n 44 |
| dtu · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | -0.008 [-0.085, +0.069] n 44 |
| dtu · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.164 [+0.070, +0.258] n 44 |
| dtu · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.232 [+0.145, +0.319] n 44 |
| dtu · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.045 [-0.112, +0.022] n 44 |
| dtu · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.011 [-0.053, +0.075] n 44 |
| dtu · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | -0.026 [-0.119, +0.067] n 44 |
| dtu · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | -0.068 [-0.188, +0.053] n 44 |
| federici · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.059 [+0.006, +0.112] n 86 |
| federici · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.125 [+0.066, +0.183] n 86 |
| federici · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.183 [+0.105, +0.261] n 86 |
| federici · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.192 [+0.116, +0.269] n 86 |
| federici · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.172 [+0.092, +0.251] n 86 |
| federici · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.186 [+0.108, +0.265] n 86 |
| federici · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.090 [+0.028, +0.152] n 86 |
| federici · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.083 [+0.019, +0.146] n 86 |

### 1.4 TF-INIT: random → pretrained at the same recipe and numeric lr — INTERIM

One-step, per seed: ΔR [95 % simultaneous within dataset × backbone × seed, 2 members] n. **Every one-step row is interim.** It is an interim look at ADDENDUM_11's frozen role `initialization_true_full`. That role's official family is dataset × seed with 4 members (backbone × lr), computed by `aln32_panel_interim.py` once the panel is complete. The family used here (dataset × backbone × seed, recipe split off, 2 members over lr) is neither that family nor ADDENDUM_07's. No seed mean and no between-seed summary is formed for TF-INIT. Seed 3401 covers every identity and the panel seeds only the outer folds completed so far, so the per-seed values rest on different identity sets (n shown) and are not a seed comparison. Seed 3401 is also in `ALIGNED_INTERFACE_RESULTS.md` §7, where the family is `TF-INIT|<dataset>|<backbone>` with 4 members (recipe × lr). The point estimates are identical. The intervals are not, for two reasons. Bootstrap replicate indices are seeded by the family label (`sci_r1.stats.group_seed(label, metric)`), and the labels here differ from the frozen ones, so even the pointwise intervals differ by bootstrap Monte Carlo error. The simultaneous intervals differ by that error and also by the family's members. Over the seed-3401 unified members, the largest bound difference from the frozen intervals is 0.0038 bits pointwise and 0.0205 bits simultaneous. Recomputed with the frozen labels and members, this script's identity values reproduce the frozen intervals exactly (§1.6).

| dataset · backbone | member | seed 3401 | seed 3407 | seed 3413 |
|---|---|---|---|---|
| fau · cbramod | full_onestep_v1/lr1e-05 · interim | +0.132 [+0.074, +0.190] n 67 | +0.094 [+0.046, +0.142] n 67 | +0.120 [+0.071, +0.168] n 67 |
| fau · cbramod | full_onestep_v1/lr0.0003 · interim | +0.120 [+0.085, +0.155] n 67 | +0.085 [+0.052, +0.119] n 67 | +0.067 [+0.033, +0.102] n 67 |
| fau · reve | full_onestep_v1/lr1e-05 · interim | +0.010 [-0.035, +0.055] n 67 | +0.035 [-0.019, +0.090] n 67 | +0.024 [-0.021, +0.070] n 67 |
| fau · reve | full_onestep_v1/lr0.0003 · interim | -0.023 [-0.073, +0.026] n 67 | -0.065 [-0.109, -0.020] n 67 | +0.015 [-0.036, +0.066] n 67 |
| dtu · cbramod | full_onestep_v1/lr1e-05 · interim | +0.535 [+0.441, +0.629] n 44 | +0.414 [+0.334, +0.494] n 44 | +0.487 [+0.408, +0.567] n 44 |
| dtu · cbramod | full_onestep_v1/lr0.0003 · interim | +0.231 [+0.162, +0.301] n 44 | +0.172 [+0.114, +0.230] n 44 | +0.196 [+0.130, +0.261] n 44 |
| dtu · reve | full_onestep_v1/lr1e-05 · interim | +0.015 [-0.076, +0.106] n 44 | +0.073 [-0.017, +0.162] n 44 | +0.040 [-0.042, +0.122] n 44 |
| dtu · reve | full_onestep_v1/lr0.0003 · interim | +0.062 [-0.018, +0.142] n 44 | +0.115 [+0.024, +0.205] n 44 | +0.206 [+0.120, +0.293] n 44 |
| federici · cbramod | full_onestep_v1/lr1e-05 · interim | +0.117 [+0.064, +0.170] n 86 | +0.133 [-0.015, +0.281] n 19 | +0.051 [-0.065, +0.167] n 19 |
| federici · cbramod | full_onestep_v1/lr0.0003 · interim | +0.055 [+0.018, +0.091] n 86 | +0.061 [-0.026, +0.149] n 19 | +0.034 [-0.028, +0.095] n 19 |
| federici · reve | full_onestep_v1/lr1e-05 · interim | -0.087 [-0.148, -0.027] n 86 | -0.144 [-0.252, -0.036] n 19 | -0.099 [-0.213, +0.014] n 19 |
| federici · reve | full_onestep_v1/lr0.0003 · interim | -0.016 [-0.057, +0.026] n 86 | not available (n 0/86) | not available (n 0/86) |

Warm-up recipe (seed 3401 only):

| dataset · backbone | member | seed 3401 |
|---|---|---|
| fau · cbramod | warmup_then_all_v1/lr1e-05 | +0.142 [+0.083, +0.201] n 67 |
| fau · cbramod | warmup_then_all_v1/lr0.0003 | +0.099 [+0.066, +0.133] n 67 |
| fau · reve | warmup_then_all_v1/lr1e-05 | -0.009 [-0.056, +0.038] n 67 |
| fau · reve | warmup_then_all_v1/lr0.0003 | -0.126 [-0.189, -0.063] n 67 |
| dtu · cbramod | warmup_then_all_v1/lr1e-05 | +0.536 [+0.442, +0.629] n 44 |
| dtu · cbramod | warmup_then_all_v1/lr0.0003 | +0.240 [+0.168, +0.311] n 44 |
| dtu · reve | warmup_then_all_v1/lr1e-05 | +0.019 [-0.055, +0.094] n 44 |
| dtu · reve | warmup_then_all_v1/lr0.0003 | -0.079 [-0.180, +0.023] n 44 |
| federici · cbramod | warmup_then_all_v1/lr1e-05 | +0.124 [+0.070, +0.178] n 86 |
| federici · cbramod | warmup_then_all_v1/lr0.0003 | +0.068 [+0.026, +0.109] n 86 |
| federici · reve | warmup_then_all_v1/lr1e-05 | -0.082 [-0.138, -0.026] n 86 |
| federici · reve | warmup_then_all_v1/lr0.0003 | -0.104 [-0.164, -0.043] n 86 |

### 1.5 Native readout (separate families; never pooled with the unified readout)

TF-LOCAL one-step:

| dataset · backbone | member | seed 3401 | seed 3407 | seed 3413 | identity mean over seeds | between-seed range (same identities) |
|---|---|---|---|---|---|---|
| fau · cbramod | L1->random_full/lr1e-05 | -0.105 [-0.168, -0.042] n 67 | -0.031 [-0.090, +0.028] n 67 | -0.109 [-0.180, -0.039] n 67 | -0.082 [-0.142, -0.022] n 67 | -0.109 … -0.031 (3401: -0.105, 3407: -0.031, 3413: -0.109; n 67) |
| fau · cbramod | L1->random_full/lr0.0003 | +0.064 [+0.014, +0.113] n 67 | +0.074 [+0.021, +0.127] n 67 | +0.081 [+0.032, +0.131] n 67 | +0.073 [+0.025, +0.121] n 67 | +0.064 … +0.081 (3401: +0.064, 3407: +0.074, 3413: +0.081; n 67) |
| fau · cbramod | L1->pretrained_full/lr1e-05 | +0.106 [+0.053, +0.160] n 67 | +0.090 [+0.028, +0.151] n 67 | +0.103 [+0.052, +0.154] n 67 | +0.100 [+0.048, +0.152] n 67 | +0.090 … +0.106 (3401: +0.106, 3407: +0.090, 3413: +0.103; n 67) |
| fau · cbramod | L1->pretrained_full/lr0.0003 | +0.170 [+0.106, +0.233] n 67 | +0.151 [+0.082, +0.221] n 67 | +0.161 [+0.094, +0.229] n 67 | +0.161 [+0.098, +0.224] n 67 | +0.151 … +0.170 (3401: +0.170, 3407: +0.151, 3413: +0.161; n 67) |
| fau · reve | L1->random_full/lr1e-05 | +0.100 [+0.053, +0.147] n 67 | +0.066 [+0.008, +0.123] n 67 | +0.077 [+0.029, +0.126] n 67 | +0.081 [+0.033, +0.129] n 67 | +0.066 … +0.100 (3401: +0.100, 3407: +0.066, 3413: +0.077; n 67) |
| fau · reve | L1->random_full/lr0.0003 | +0.029 [-0.023, +0.081] n 67 | -0.022 [-0.084, +0.041] n 67 | -0.020 [-0.077, +0.037] n 67 | -0.004 [-0.058, +0.049] n 67 | -0.022 … +0.029 (3401: +0.029, 3407: -0.022, 3413: -0.020; n 67) |
| fau · reve | L1->pretrained_full/lr1e-05 | +0.113 [+0.035, +0.192] n 67 | +0.111 [+0.031, +0.191] n 67 | +0.111 [+0.039, +0.183] n 67 | +0.112 [+0.039, +0.184] n 67 | +0.111 … +0.113 (3401: +0.113, 3407: +0.111, 3413: +0.111; n 67) |
| fau · reve | L1->pretrained_full/lr0.0003 | +0.122 [+0.055, +0.188] n 67 | +0.013 [-0.055, +0.080] n 67 | +0.086 [+0.010, +0.162] n 67 | +0.073 [+0.013, +0.134] n 67 | +0.013 … +0.122 (3401: +0.122, 3407: +0.013, 3413: +0.086; n 67) |
| dtu · cbramod | L1->random_full/lr1e-05 | -0.617 [-0.784, -0.449] n 44 | -0.341 [-0.502, -0.180] n 44 | -0.584 [-0.739, -0.430] n 44 | -0.514 [-0.667, -0.361] n 44 | -0.617 … -0.341 (3401: -0.617, 3407: -0.341, 3413: -0.584; n 44) |
| dtu · cbramod | L1->random_full/lr0.0003 | -0.089 [-0.203, +0.026] n 44 | +0.089 [-0.033, +0.210] n 44 | -0.030 [-0.143, +0.082] n 44 | -0.010 [-0.115, +0.095] n 44 | -0.089 … +0.089 (3401: -0.089, 3407: +0.089, 3413: -0.030; n 44) |
| dtu · cbramod | L1->pretrained_full/lr1e-05 | +0.131 [-0.003, +0.265] n 44 | +0.156 [+0.010, +0.303] n 44 | +0.130 [-0.018, +0.277] n 44 | +0.139 [+0.004, +0.275] n 44 | +0.130 … +0.156 (3401: +0.131, 3407: +0.156, 3413: +0.130; n 44) |
| dtu · cbramod | L1->pretrained_full/lr0.0003 | +0.377 [+0.282, +0.472] n 44 | +0.426 [+0.309, +0.543] n 44 | +0.380 [+0.250, +0.509] n 44 | +0.394 [+0.289, +0.500] n 44 | +0.377 … +0.426 (3401: +0.377, 3407: +0.426, 3413: +0.380; n 44) |
| dtu · reve | L1->random_full/lr1e-05 | -0.199 [-0.310, -0.087] n 44 | -0.088 [-0.204, +0.028] n 44 | -0.134 [-0.241, -0.027] n 44 | -0.140 [-0.242, -0.038] n 44 | -0.199 … -0.088 (3401: -0.199, 3407: -0.088, 3413: -0.134; n 44) |
| dtu · reve | L1->random_full/lr0.0003 | -0.206 [-0.323, -0.089] n 44 | -0.083 [-0.199, +0.033] n 44 | -0.251 [-0.373, -0.128] n 44 | -0.180 [-0.289, -0.071] n 44 | -0.251 … -0.083 (3401: -0.206, 3407: -0.083, 3413: -0.251; n 44) |
| dtu · reve | L1->pretrained_full/lr1e-05 | +0.067 [-0.050, +0.185] n 44 | +0.067 [-0.045, +0.178] n 44 | +0.100 [-0.017, +0.217] n 44 | +0.078 [-0.025, +0.181] n 44 | +0.067 … +0.100 (3401: +0.067, 3407: +0.067, 3413: +0.100; n 44) |
| dtu · reve | L1->pretrained_full/lr0.0003 | +0.062 [-0.055, +0.179] n 44 | +0.260 [+0.115, +0.405] n 44 | +0.186 [+0.040, +0.332] n 44 | +0.169 [+0.052, +0.287] n 44 | +0.062 … +0.260 (3401: +0.062, 3407: +0.260, 3413: +0.186; n 44) |
| federici · cbramod | L1->random_full/lr1e-05 | +0.065 [+0.003, +0.127] n 86 | -0.023 [-0.147, +0.102] n 19 | +0.071 [-0.052, +0.194] n 19 | +0.027 [-0.079, +0.133] n 19 | -0.023 … +0.071 (3401: +0.032, 3407: -0.023, 3413: +0.071; n 19) |
| federici · cbramod | L1->random_full/lr0.0003 | +0.176 [+0.108, +0.244] n 86 | +0.072 [-0.080, +0.225] n 19 | +0.123 [+0.005, +0.241] n 19 | +0.107 [-0.020, +0.235] n 19 | +0.072 … +0.126 (3401: +0.126, 3407: +0.072, 3413: +0.123; n 19) |
| federici · cbramod | L1->pretrained_full/lr1e-05 | +0.211 [+0.129, +0.293] n 86 | +0.136 [-0.010, +0.282] n 19 | +0.150 [+0.029, +0.271] n 19 | +0.143 [+0.005, +0.280] n 19 | +0.136 … +0.150 (3401: +0.142, 3407: +0.136, 3413: +0.150; n 19) |
| federici · cbramod | L1->pretrained_full/lr0.0003 | +0.220 [+0.126, +0.313] n 86 | +0.138 [-0.117, +0.393] n 19 | +0.194 [+0.038, +0.349] n 19 | +0.164 [-0.055, +0.382] n 19 | +0.138 … +0.194 (3401: +0.159, 3407: +0.138, 3413: +0.194; n 19) |
| federici · reve | L1->random_full/lr1e-05 | +0.170 [+0.093, +0.247] n 86 | +0.155 [+0.001, +0.310] n 19 | +0.158 [+0.036, +0.279] n 19 | +0.154 [+0.021, +0.286] n 19 | +0.149 … +0.158 (3401: +0.149, 3407: +0.155, 3413: +0.158; n 19) |
| federici · reve | L1->random_full/lr0.0003 | +0.208 [+0.128, +0.289] n 86 | +0.131 [-0.042, +0.305] n 19 | +0.154 [+0.011, +0.296] n 19 | +0.147 [-0.004, +0.299] n 19 | +0.131 … +0.157 (3401: +0.157, 3407: +0.131, 3413: +0.154; n 19) |
| federici · reve | L1->pretrained_full/lr1e-05 | +0.109 [+0.038, +0.180] n 86 | -0.013 [-0.141, +0.116] n 19 | +0.029 [-0.094, +0.151] n 19 | -0.012 [-0.114, +0.091] n 19 | -0.051 … +0.029 (3401: -0.051, 3407: -0.013, 3413: +0.029; n 19) |
| federici · reve | L1->pretrained_full/lr0.0003 | +0.208 [+0.116, +0.299] n 86 | not available (n 0/86) | not available (n 0/86) | not available (n 0/86) | not available |

TF-INIT one-step (interim):

| dataset · backbone | member | seed 3401 | seed 3407 | seed 3413 |
|---|---|---|---|---|
| fau · cbramod | full_onestep_v1/lr1e-05 · interim | +0.212 [+0.155, +0.268] n 67 | +0.121 [+0.081, +0.160] n 67 | +0.212 [+0.160, +0.265] n 67 |
| fau · cbramod | full_onestep_v1/lr0.0003 · interim | +0.106 [+0.067, +0.146] n 67 | +0.078 [+0.030, +0.125] n 67 | +0.080 [+0.028, +0.131] n 67 |
| fau · reve | full_onestep_v1/lr1e-05 · interim | +0.013 [-0.053, +0.079] n 67 | +0.045 [-0.029, +0.120] n 67 | +0.034 [-0.036, +0.103] n 67 |
| fau · reve | full_onestep_v1/lr0.0003 · interim | +0.093 [+0.032, +0.154] n 67 | +0.034 [-0.043, +0.112] n 67 | +0.106 [+0.021, +0.191] n 67 |
| dtu · cbramod | full_onestep_v1/lr1e-05 · interim | +0.748 [+0.612, +0.884] n 44 | +0.498 [+0.377, +0.618] n 44 | +0.714 [+0.592, +0.837] n 44 |
| dtu · cbramod | full_onestep_v1/lr0.0003 · interim | +0.466 [+0.371, +0.561] n 44 | +0.338 [+0.250, +0.425] n 44 | +0.410 [+0.331, +0.489] n 44 |
| dtu · reve | full_onestep_v1/lr1e-05 · interim | +0.266 [+0.145, +0.386] n 44 | +0.155 [+0.030, +0.279] n 44 | +0.234 [+0.127, +0.341] n 44 |
| dtu · reve | full_onestep_v1/lr0.0003 · interim | +0.268 [+0.141, +0.394] n 44 | +0.344 [+0.212, +0.475] n 44 | +0.436 [+0.268, +0.605] n 44 |
| federici · cbramod | full_onestep_v1/lr1e-05 · interim | +0.146 [+0.094, +0.198] n 86 | +0.159 [+0.021, +0.297] n 19 | +0.078 [-0.015, +0.171] n 19 |
| federici · cbramod | full_onestep_v1/lr0.0003 · interim | +0.044 [-0.004, +0.092] n 86 | +0.066 [-0.074, +0.206] n 19 | +0.071 [-0.024, +0.165] n 19 |
| federici · reve | full_onestep_v1/lr1e-05 · interim | -0.061 [-0.129, +0.007] n 86 | -0.168 [-0.267, -0.068] n 19 | -0.129 [-0.215, -0.043] n 19 |
| federici · reve | full_onestep_v1/lr0.0003 · interim | -0.001 [-0.051, +0.049] n 86 | not available (n 0/86) | not available (n 0/86) |

TF-LOCAL warm-up (seed 3401 only):

| dataset · backbone | member | seed 3401 |
|---|---|---|
| fau · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.110 [-0.175, -0.046] n 67 |
| fau · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.076 [+0.030, +0.122] n 67 |
| fau · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.109 [+0.055, +0.162] n 67 |
| fau · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.182 [+0.117, +0.247] n 67 |
| fau · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.076 [+0.029, +0.123] n 67 |
| fau · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.055 [+0.006, +0.104] n 67 |
| fau · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.084 [-0.002, +0.170] n 67 |
| fau · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | -0.016 [-0.104, +0.071] n 67 |
| dtu · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.622 [-0.791, -0.452] n 44 |
| dtu · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | -0.044 [-0.152, +0.064] n 44 |
| dtu · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.125 [-0.011, +0.262] n 44 |
| dtu · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.428 [+0.315, +0.540] n 44 |
| dtu · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | -0.197 [-0.320, -0.074] n 44 |
| dtu · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | -0.133 [-0.256, -0.009] n 44 |
| dtu · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | -0.017 [-0.144, +0.111] n 44 |
| dtu · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.011 [-0.143, +0.164] n 44 |
| federici · cbramod | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.060 [-0.002, +0.122] n 86 |
| federici · cbramod | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.157 [+0.090, +0.224] n 86 |
| federici · cbramod | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.207 [+0.120, +0.294] n 86 |
| federici · cbramod | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.217 [+0.127, +0.307] n 86 |
| federici · reve | L1->random_full/warmup_then_all_v1/lr1e-05 | +0.162 [+0.083, +0.241] n 86 |
| federici · reve | L1->random_full/warmup_then_all_v1/lr0.0003 | +0.223 [+0.142, +0.304] n 86 |
| federici · reve | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | +0.121 [+0.058, +0.183] n 86 |
| federici · reve | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | +0.097 [+0.019, +0.174] n 86 |

TF-INIT warm-up (seed 3401 only):

| dataset · backbone | member | seed 3401 |
|---|---|---|
| fau · cbramod | warmup_then_all_v1/lr1e-05 | +0.219 [+0.162, +0.276] n 67 |
| fau · cbramod | warmup_then_all_v1/lr0.0003 | +0.106 [+0.058, +0.154] n 67 |
| fau · reve | warmup_then_all_v1/lr1e-05 | +0.008 [-0.067, +0.083] n 67 |
| fau · reve | warmup_then_all_v1/lr0.0003 | -0.071 [-0.158, +0.016] n 67 |
| dtu · cbramod | warmup_then_all_v1/lr1e-05 | +0.747 [+0.604, +0.890] n 44 |
| dtu · cbramod | warmup_then_all_v1/lr0.0003 | +0.471 [+0.372, +0.571] n 44 |
| dtu · reve | warmup_then_all_v1/lr1e-05 | +0.180 [+0.071, +0.289] n 44 |
| dtu · reve | warmup_then_all_v1/lr0.0003 | +0.144 [-0.027, +0.314] n 44 |
| federici · cbramod | warmup_then_all_v1/lr1e-05 | +0.147 [+0.089, +0.205] n 86 |
| federici · cbramod | warmup_then_all_v1/lr0.0003 | +0.060 [+0.016, +0.103] n 86 |
| federici · reve | warmup_then_all_v1/lr1e-05 | -0.041 [-0.100, +0.017] n 86 |
| federici · reve | warmup_then_all_v1/lr0.0003 | -0.127 [-0.187, -0.066] n 86 |

### 1.6 Pairing audit

The unit records carry no split hash, target hash or evaluation-version field (the ALN3 result schema asked for them; the runners never wrote them). The closest verifiable equivalents used for every complete pair:

| field | derivation |
|---|---|
| dataset, subject_fold, content_fold, seed | record row and bound_row against the plan row (content_fold None -> 0 as core.bind); all three must agree |
| split_fingerprint | closest verifiable equivalent of split_hash (not written by the runners): sha256 of dataset, subject_fold, content_fold, n_train_participants, n_fit_segments, n_es_segments, eval.readout.n_test_candidates and the sorted (test record id, n_candidates, n_queries) of unified/regular. Code: the split is train_participants(subject_fold) + data.load_*(content_fold) roles and does not depend on the seed; must be identical for every complete record of a fold cell |
| target_fingerprint | closest verifiable equivalent of target_hash: sha256 of spec.target, record target_contract, resolved d, grid_samples, fs and the audio head (bound_row.spec.audio_head; fixed_features is also hard-coded in fm_aligned32.fit_aligned32), plus objective_calibration sigma_v / ridge_v compared with relative tolerance 1e-6 (deterministic training-side statistics of the target head on the seed's calibration rows: projection seeded per cohort, standardisation rng(seed + 5), calibration batch rng(seed + 99 / 98) in both trainers); seed-specific by design |
| access_contract | normalised (support, window [a, b) in native samples relative to the query, mask). L1: resolved_config.support, windows_samples, resolved_config.mask; TF: resolved_config.input_support, window_s x fs (b - a = window_native_samples), mask from code (fm_aligned.aligned_windows: zero before the segment start); L0: windows_samples [0, post) = post600. Both model types read every cohort channel (code: Backbone uses CHANNELS[dataset], the local encoder coh.n_ch) |
| evaluation_version | evaluator ev2.evaluate_continuous -> ev1.evaluate_continuous (unified ridge bridge + native score, rng(seed + 1000)) on the dense grid (grid_samples), sha256 of auditory_alignment/evaluate.py + auditory_alignment_v2/evaluate.py; valid only if the record's code_hash equals core.code_hash(family) recomputed now (hashed files incl. both evaluate.py byte-identical) |
| initialization (declared difference of TF-INIT) | record backbone_contract.arch and backbone_contract.adaptation (random_full / pretrained_full) must equal the configuration, and backbone_contract.init_state_loaded must be null: that field records only donor init_state weights (auditory_alignment_v2/foundation_adapter.py Backbone.__init__); public pretrained weights load through the adaptation flag (CBraMod strict load_state_dict of the published weights, REVE AutoModel.from_pretrained; random init from_config). Local sides (L0/L1) must have an encoder record and no backbone_contract. Added in Correction 1 of the note |

Derived fields per role and dataset (complete units only; every unit's values are in the JSON `units` table):

| role · dataset | complete units | plan/record rows consistent | code_hash (reproduced now) | access: support, window [a, b) samples, mask | initialization: backbone_contract arch/adaptation (consistent with the configuration, no donor init_state) | information_stratum (plan label) |
|---|---|---|---|---|---|---|
| L0 · dtu | 30 | 30 | `89df1dde3d7a49df` (True: 30) | post600, [0, 77], not_applicable_window_starts_at_query | local encoder 30 (30) | local_only |
| L0 · fau | 30 | 30 | `89df1dde3d7a49df` (True: 30) | post600, [0, 77], not_applicable_window_starts_at_query | local encoder 30 (30) | local_only |
| L0 · federici | 15 | 15 | `89df1dde3d7a49df` (True: 15) | post600, [0, 60], not_applicable_window_starts_at_query | local encoder 15 (15) | local_only |
| L1 · dtu | 30 | 30 | `1b6595fc9ac72f77` (True: 30) | aligned1000, [-51, 77], zero_before_segment_start | local encoder 30 (30) | local_only |
| L1 · fau | 30 | 30 | `1b6595fc9ac72f77` (True: 30) | aligned1000, [-51, 77], zero_before_segment_start | local encoder 30 (30) | local_only |
| L1 · federici | 15 | 15 | `1b6595fc9ac72f77` (True: 15) | aligned1000, [-40, 60], zero_before_segment_start | local encoder 15 (15) | local_only |
| TF · dtu | 320 | 320 | `88aafcdbd2424299` (True: 320) | aligned1000, [-51, 77], zero_before_segment_start | cbramod/pretrained_full 80, cbramod/random_full 80, reve/pretrained_full 80, reve/random_full 80 (320) | foundation_context |
| TF · fau | 320 | 320 | `88aafcdbd2424299` (True: 320) | aligned1000, [-51, 77], zero_before_segment_start | cbramod/pretrained_full 80, cbramod/random_full 80, reve/pretrained_full 80, reve/random_full 80 (320) | foundation_context |
| TF · federici | 94 | 94 | `88aafcdbd2424299` (True: 94) | aligned1000, [-40, 60], zero_before_segment_start | cbramod/pretrained_full 24, cbramod/random_full 24, reve/pretrained_full 22, reve/random_full 24 (94) | foundation_context |

Pair statuses (fold cell × seed × member; L0 rows are audit-only access extensions):

| contrast | status | reason | pairs |
|---|---|---|---|
| L0-L1 (audit only) | complete | – | 75 |
| L0-TF (audit only) | complete | – | 734 |
| L0-TF (audit only) | missing | candidate not registered | 400 |
| L0-TF (audit only) | pending | candidate queued | 64 |
| L0-TF (audit only) | pending | candidate running | 2 |
| TF-INIT | complete | – | 366 |
| TF-INIT | missing | reference and candidate not registered | 200 |
| TF-INIT | pending | candidate running | 2 |
| TF-INIT | pending | reference queued; candidate queued | 32 |
| TF-LOCAL | complete | – | 734 |
| TF-LOCAL | missing | candidate not registered | 400 |
| TF-LOCAL | pending | candidate queued | 64 |
| TF-LOCAL | pending | candidate running | 2 |

Match-field mismatches among complete units: **0** (checked per complete pair: record rows, split, target, evaluation, access and initialization). Largest relative deviation of the target calibration statistics (sigma_v, ridge_v) within complete pairs: 3.3e-16.

Seed-3401 reproduction of the frozen ADDENDUM_07 analysis (`results/auditory_alignment_v3/aln32_wave1/aln32_wave1.json`):

- Point estimates and n of the declared families: **pass** (144 member × readout values, max |Δ| 0.0e+00; n mismatches 0).
- Intervals of the declared families against the frozen ones (descriptive): pointwise bounds differ in 72 of 72 unified members, by up to 0.0038 bits (native: 72 of 72, up to 0.0035); simultaneous bounds by up to 0.0205 bits (unified; the frozen native readout has no simultaneous intervals). Cause: bootstrap replicate indices are drawn with `sci_r1.stats.group_seed(label, metric)` and the family labels here (`TFL1|contrast|recipe|dataset|backbone|seed`) differ from the frozen ones (`TF-INIT|dataset|backbone`, `TF-LOCAL|dataset|backbone`, and `<label>|sec` for the native readout), so the pointwise intervals differ by bootstrap Monte Carlo error; the simultaneous intervals differ by that and by the family composition (frozen TF-INIT: 4 members, recipe x lr; frozen TF-LOCAL: 16 members, {L0, L1} x init x recipe x lr; frozen native readout: pointwise only). Point estimates are unaffected.
- Frozen labels, member names and compositions recomputed from this script's identity values (per dataset × backbone: TF-INIT 4 members, TF-LOCAL 16 members; unified with max-t, native `<label>|sec` pointwise): **pass** (240 member × readout values in 24 families; largest |Δ| over est, se, pointwise CI, simultaneous bounds and crit: 0.0e+00; n mismatches 0).

## 2. 当前工作判断 · Current working judgement

TF-LOCAL one-step only. Per member, the seeds whose 95 % simultaneous interval lies above zero, contains zero or lies below zero (unified readout; seeds not yet available are listed separately). This is a description of each member across seeds, not a count of independent replications.

TF-INIT is not judged across seeds here: the analysis note declares no seed mean and no between-seed summary for it. Its per-seed values are in §1.4 and §1.5, every one-step row tagged interim; the frozen `aln32_panel_interim.py` gives the official ADDENDUM_11 version once the panel is complete.

| dataset · backbone | contrast · member | above 0 | contains 0 | below 0 | not available | identity mean over seeds |
|---|---|---|---|---|---|---|
| fau · cbramod | TF-LOCAL · L1->random_full/lr1e-05 | – | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | +0.010 [-0.028, +0.049] n 67 (contains 0) |
| fau · cbramod | TF-LOCAL · L1->random_full/lr0.0003 | 3407 (n 67), 3413 (n 67) | 3401 (n 67) | – | – | +0.051 [+0.019, +0.082] n 67 (I>0) |
| fau · cbramod | TF-LOCAL · L1->pretrained_full/lr1e-05 | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | – | +0.125 [+0.081, +0.169] n 67 (I>0) |
| fau · cbramod | TF-LOCAL · L1->pretrained_full/lr0.0003 | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | – | +0.141 [+0.099, +0.184] n 67 (I>0) |
| fau · reve | TF-LOCAL · L1->random_full/lr1e-05 | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | – | +0.083 [+0.049, +0.117] n 67 (I>0) |
| fau · reve | TF-LOCAL · L1->random_full/lr0.0003 | 3401 (n 67), 3407 (n 67) | 3413 (n 67) | – | – | +0.047 [+0.018, +0.076] n 67 (I>0) |
| fau · reve | TF-LOCAL · L1->pretrained_full/lr1e-05 | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | – | +0.106 [+0.061, +0.152] n 67 (I>0) |
| fau · reve | TF-LOCAL · L1->pretrained_full/lr0.0003 | – | 3401 (n 67), 3407 (n 67), 3413 (n 67) | – | – | +0.023 [-0.016, +0.062] n 67 (contains 0) |
| dtu · cbramod | TF-LOCAL · L1->random_full/lr1e-05 | – | – | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | -0.312 [-0.411, -0.213] n 44 (I<0) |
| dtu · cbramod | TF-LOCAL · L1->random_full/lr0.0003 | – | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | – | +0.013 [-0.064, +0.090] n 44 (contains 0) |
| dtu · cbramod | TF-LOCAL · L1->pretrained_full/lr1e-05 | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | – | – | +0.167 [+0.071, +0.264] n 44 (I>0) |
| dtu · cbramod | TF-LOCAL · L1->pretrained_full/lr0.0003 | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | – | – | +0.213 [+0.129, +0.297] n 44 (I>0) |
| dtu · reve | TF-LOCAL · L1->random_full/lr1e-05 | – | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | – | -0.015 [-0.082, +0.053] n 44 (contains 0) |
| dtu · reve | TF-LOCAL · L1->random_full/lr0.0003 | – | 3401 (n 44), 3407 (n 44) | 3413 (n 44) | – | -0.046 [-0.114, +0.023] n 44 (contains 0) |
| dtu · reve | TF-LOCAL · L1->pretrained_full/lr1e-05 | – | 3401 (n 44), 3407 (n 44), 3413 (n 44) | – | – | +0.028 [-0.061, +0.116] n 44 (contains 0) |
| dtu · reve | TF-LOCAL · L1->pretrained_full/lr0.0003 | 3413 (n 44) | 3401 (n 44), 3407 (n 44) | – | – | +0.082 [-0.015, +0.180] n 44 (contains 0) |
| federici · cbramod | TF-LOCAL · L1->random_full/lr1e-05 | 3401 (n 86) | 3407 (n 19), 3413 (n 19) | – | – | +0.048 [-0.027, +0.122] n 19 (contains 0) |
| federici · cbramod | TF-LOCAL · L1->random_full/lr0.0003 | 3401 (n 86), 3413 (n 19) | 3407 (n 19) | – | – | +0.144 [+0.002, +0.286] n 19 (I>0) |
| federici · cbramod | TF-LOCAL · L1->pretrained_full/lr1e-05 | 3401 (n 86) | 3407 (n 19), 3413 (n 19) | – | – | +0.147 [-0.008, +0.303] n 19 (contains 0) |
| federici · cbramod | TF-LOCAL · L1->pretrained_full/lr0.0003 | 3401 (n 86), 3413 (n 19) | 3407 (n 19) | – | – | +0.176 [-0.001, +0.354] n 19 (contains 0) |
| federici · reve | TF-LOCAL · L1->random_full/lr1e-05 | 3401 (n 86) | 3407 (n 19), 3413 (n 19) | – | – | +0.163 [-0.001, +0.326] n 19 (contains 0) |
| federici · reve | TF-LOCAL · L1->random_full/lr0.0003 | 3401 (n 86) | 3407 (n 19), 3413 (n 19) | – | – | +0.135 [-0.041, +0.311] n 19 (contains 0) |
| federici · reve | TF-LOCAL · L1->pretrained_full/lr1e-05 | 3401 (n 86) | 3407 (n 19), 3413 (n 19) | – | – | +0.024 [-0.054, +0.102] n 19 (contains 0) |
| federici · reve | TF-LOCAL · L1->pretrained_full/lr0.0003 | 3401 (n 86) | – | – | 3407, 3413 | not available |

Identity-subset check (TF-LOCAL one-step, unified; descriptive means, no intervals). Where the panel covers only part of a cohort, seed 3401 restricted to the same identities shows how much of the gap between the 3401 column and the panel columns of §1.2 comes from the identity subset rather than from the seed:

| dataset · backbone | member | seed 3401, all identities | seed 3401, seed-mean identities | panel seeds, same identities |
|---|---|---|---|---|
| federici · cbramod | L1->random_full/lr1e-05 | +0.063 (n 86) | +0.054 (n 19) | 3407: +0.006, 3413: +0.084 |
| federici · cbramod | L1->random_full/lr0.0003 | +0.141 (n 86) | +0.192 (n 19) | 3407: +0.081, 3413: +0.159 |
| federici · cbramod | L1->pretrained_full/lr1e-05 | +0.180 (n 86) | +0.168 (n 19) | 3407: +0.139, 3413: +0.135 |
| federici · cbramod | L1->pretrained_full/lr0.0003 | +0.196 (n 86) | +0.194 (n 19) | 3407: +0.142, 3413: +0.193 |
| federici · reve | L1->random_full/lr1e-05 | +0.175 (n 86) | +0.170 (n 19) | 3407: +0.159, 3413: +0.160 |
| federici · reve | L1->random_full/lr0.0003 | +0.183 (n 86) | +0.169 (n 19) | 3407: +0.126, 3413: +0.110 |
| federici · reve | L1->pretrained_full/lr1e-05 | +0.087 (n 86) | -0.002 (n 19) | 3407: +0.014, 3413: +0.060 |

On the same identities the seeds still differ: over the 23 TF-LOCAL one-step members with all three seeds, the between-seed range of the per-seed means runs from 0.011 to 0.150 bits (largest: dtu · cbramod L1->random_full/lr1e-05, 3401: -0.373, 3407: -0.223, 3413: -0.339; n 44). These are descriptive means of three seeds, not an estimate of a seed distribution.

Scope of these judgements:
- Seeds 3407/3413 currently contribute only in: dtu, fau, federici; the panel-seed entries cover the identities counted in §1.1 (the outer folds completed so far), not the whole cohort. Datasets without a complete panel pair rest on seed 3401 alone.
- What is compared is this registered recipe: aligned [−0.4, +0.6) s interface, one-step full update with backbone lr 1e-5 or 3e-4 (head 1e-3, LLRD 1), 100 (CBraMod) / 50 (REVE) epochs, checkpoint by the training-side early-stopping rule. It is not a statement about other optimizers, budgets, data amounts or backbones.
- TF-LOCAL is an FM-versus-local contrast under the same EEG access, target and evaluation. It is not a pure pretraining or pure architecture effect (§3). Only TF-INIT is an initialization contrast, and it remains interim until the panel is complete.

## 3. 仍竞争的解释 · Competing explanations

- **L1 → pretrained TF** mixes the pretraining prior with architecture (12-block CBraMod / 22-block REVE transformer vs the lag-local encoder), parameter count, input resampling to one 200 Hz patch, the readout head and the optimizer/schedule (the local encoder: AdamW 1e-3, 200 epochs). The same-access match removes only the EEG-window difference. Parameter counts read from the records: L1 encoder dtu 50,800, fau 50,272, federici 58,128; CBraMod backbone dtu 4,883,800, fau 4,883,800, federici 4,883,800; REVE backbone dtu 69,189,632, fau 69,189,632, federici 69,189,632; aligned readout head dtu 410,032, fau 198,832, federici 205,232 (CBraMod) and dtu 1,049,632, fau 508,960, federici 525,344 (REVE).
- **L1 → random TF** carries the same architecture/optimizer differences without the prior. Comparing it with L1 → pretrained TF in the same seed is TF-INIT, the matched initialization contrast.
- **TF-INIT at a fixed budget** does not separate faster optimization from transferable content (package docs/01, question 1). Whether the initialization effect shrinks or grows from lr 1e-5 to 3e-4 does not by itself distinguish the two.
- **Unified vs native readout.** The unified readout fits a ridge bridge into the standardized target space on training participants; the native readout is the model's own NCE score. They can rank models differently; a difference between them is about the bridge, not the EEG access.
- **Seed variation.** A panel seed changes the whole pipeline (initialization of random parts, data order, readout subsample, calibration rows). Identity-level intervals condition on the fitted models; three seeds can show whether results are stable across these draws; they are not a seed distribution, and §2 shows large spreads on the same identities.
- **Interim coverage.** The panel queue runs DTU first and outer folds in order; the current panel identities are the earliest folds and need not represent the cohort. This is availability, not selection by performance, but it limits what the panel entries say now.

## 4. 下一轮干预 · Next interventions

- Let the registered panel finish (no new registration needed: every missing one-step pair is registered and queued; L0/L1 are complete). Rerun this script after each batch; it is idempotent. When 400/400 are complete, run the frozen `aln32_panel_interim.py` for the official ADDENDUM_11 roles (including TF-INIT); this script does not replace it.
- Warm-up is not registered for 3407/3413 and is not needed for this card (package docs/02 §A: one-step 3e-4 is the explicit starting point for the deeper CBraMod panel).
- Package docs/02 §B (learning process, target-population size, content amount, ~2× budget) is the next intervention for separating optimization speed from transferable content; it needs its own registration with matched updates. Not started here.
- REVE keeps its representative random/pretrained comparison and both readouts (package docs/02 §A).

## 5. 复用与运行 · Reuse and running

- Reused unit records: L0 75, L1 75, TF 734. No training, no GPU job, no queue or hold change. CPU aggregation run locally (4 s).
- Outputs: `results/auditory_alignment_v3/aln34/tf_l1/tf_l1_pairs.json` (pairing audit with every pair's status and checks, coverage, all families with pointwise and simultaneous intervals, seed means, ranges, native readout) and this document. Both mode 600.
- Blocking: none. Missing panel pairs are pending in the queue, not failed.
- Implementation details relative to the analysis note. Decided while coding, before the first real run: the target calibration statistics (sigma_v, ridge_v) are compared with relative tolerance 1e-6 next to the hash of the exact target fields rather than inside the hash (largest deviation observed 3.3e-16, so both readings agree here); the evaluation key also lists the readout set (unified, native). Added after the first real run had been seen: the parameter counts in §3, the per-role table of derived fields in §1.6, and the identity-subset check in §2 (prompted by the DTU panel identities showing smaller seed-3401 effects than the full cohort). These are descriptive and change no estimate, family or interval.
- Corrections after an independent verification of the 20:09 run (analysis note, Correction 1, written 2026-10-16 20:36 before the corrected code ran). No estimate, family or interval changed.
  1. The seed-3401 interval differences from `ALIGNED_INTERFACE_RESULTS.md` were explained by family composition alone. The pointwise intervals differ too, because bootstrap replicates are seeded by the family label. §1.3 and §1.4 now say so, and §1.6 recomputes the frozen families with their own labels and members.
  2. The TF-INIT difference is evidenced by `backbone_contract.adaptation` (random_full / pretrained_full) and `.arch`, not by `init_state_loaded`. That field records only donor weights and is null in every TF record. A pair check `initialization` was added (§1.6).
  3. The code and test files were mode 644 while the note said 600. They are 600 now.
  4. The note misnamed the TF-INIT family scope. It is dataset × backbone × seed × recipe (2 members over lr), which is neither ADDENDUM_07's family (dataset × backbone, recipe × lr) nor ADDENDUM_11's (dataset × seed, backbone × lr). The package card specifies none.
  5. TF-INIT left the §2 cross-seed table. Every TF-INIT one-step row carries an interim tag.
  6. §2 adds the between-seed spread on the same identities.
  7. The script was rerun on the live state, and outputs give the generation time to the second.

## 6. 暂不决定 · Not decided here

- Nothing here needs a researcher decision. Paper organisation, wording and contribution order stay open and do not block the interventions above.

## Appendix A. Per-member detail (unified readout)

| family | status | member | n (own) | ΔR | 95 % CI | 95 % simultaneous | class |
|---|---|---|---|---|---|---|---|
| TF-LOCAL · onestep · fau · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | -0.005 | [-0.038, +0.028] | [-0.046, +0.036] | contains 0 |
| TF-LOCAL · onestep · fau · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.025 | [-0.011, +0.060] | [-0.018, +0.067] | contains 0 |
| TF-LOCAL · onestep · fau · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.127 | [+0.079, +0.175] | [+0.069, +0.185] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.144 | [+0.100, +0.189] | [+0.090, +0.199] | I>0 |
| TF-LOCAL · warmup · fau · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 67 (67) | -0.010 | [-0.044, +0.023] | [-0.052, +0.032] | contains 0 |
| TF-LOCAL · warmup · fau · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 67 (67) | +0.042 | [+0.011, +0.074] | [+0.003, +0.082] | I>0 |
| TF-LOCAL · warmup · fau · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 67 (67) | +0.132 | [+0.086, +0.177] | [+0.074, +0.189] | I>0 |
| TF-LOCAL · warmup · fau · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 67 (67) | +0.142 | [+0.094, +0.189] | [+0.083, +0.200] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.132 | [+0.080, +0.184] | [+0.074, +0.190] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | +0.120 | [+0.089, +0.150] | [+0.085, +0.155] | I>0 |
| TF-INIT · warmup · fau · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 67 (67) | +0.142 | [+0.090, +0.194] | [+0.083, +0.201] | I>0 |
| TF-INIT · warmup · fau · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 67 (67) | +0.099 | [+0.069, +0.129] | [+0.066, +0.133] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3407 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.042 | [+0.004, +0.080] | [-0.005, +0.089] | contains 0 |
| TF-LOCAL · onestep · fau · cbramod · 3407 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.071 | [+0.041, +0.102] | [+0.035, +0.108] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.136 | [+0.099, +0.173] | [+0.091, +0.181] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.157 | [+0.121, +0.193] | [+0.112, +0.201] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.094 | [+0.053, +0.135] | [+0.046, +0.142] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | +0.085 | [+0.056, +0.115] | [+0.052, +0.119] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3413 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | -0.007 | [-0.043, +0.030] | [-0.051, +0.038] | contains 0 |
| TF-LOCAL · onestep · fau · cbramod · 3413 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.056 | [+0.027, +0.084] | [+0.021, +0.091] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.113 | [+0.078, +0.148] | [+0.070, +0.156] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.123 | [+0.086, +0.160] | [+0.079, +0.168] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.120 | [+0.076, +0.163] | [+0.071, +0.168] | I>0 |
| TF-INIT · onestep · fau · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | +0.067 | [+0.036, +0.099] | [+0.033, +0.102] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · seedmean | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.010 | [-0.021, +0.041] | [-0.028, +0.049] | contains 0 |
| TF-LOCAL · onestep · fau · cbramod · seedmean | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.051 | [+0.025, +0.076] | [+0.019, +0.082] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.125 | [+0.089, +0.161] | [+0.081, +0.169] | I>0 |
| TF-LOCAL · onestep · fau · cbramod · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.141 | [+0.107, +0.176] | [+0.099, +0.184] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.099 | [+0.058, +0.141] | [+0.047, +0.152] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.081 | [+0.050, +0.112] | [+0.041, +0.120] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.109 | [+0.061, +0.157] | [+0.048, +0.171] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.057 | [+0.010, +0.105] | [-0.003, +0.118] | contains 0 |
| TF-LOCAL · warmup · fau · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 67 (67) | +0.092 | [+0.051, +0.133] | [+0.043, +0.141] | I>0 |
| TF-LOCAL · warmup · fau · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 67 (67) | +0.083 | [+0.044, +0.123] | [+0.035, +0.131] | I>0 |
| TF-LOCAL · warmup · fau · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 67 (67) | +0.082 | [+0.035, +0.129] | [+0.024, +0.141] | I>0 |
| TF-LOCAL · warmup · fau · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 67 (67) | -0.043 | [-0.094, +0.009] | [-0.107, +0.022] | contains 0 |
| TF-INIT · onestep · fau · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.010 | [-0.029, +0.049] | [-0.035, +0.055] | contains 0 |
| TF-INIT · onestep · fau · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | -0.023 | [-0.066, +0.019] | [-0.073, +0.026] | contains 0 |
| TF-INIT · warmup · fau · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 67 (67) | -0.009 | [-0.052, +0.033] | [-0.056, +0.038] | contains 0 |
| TF-INIT · warmup · fau · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 67 (67) | -0.126 | [-0.181, -0.071] | [-0.189, -0.063] | I<0 |
| TF-LOCAL · onestep · fau · reve · 3407 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.092 | [+0.062, +0.122] | [+0.055, +0.129] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3407 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.046 | [+0.013, +0.078] | [+0.005, +0.086] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.127 | [+0.082, +0.172] | [+0.073, +0.181] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | -0.019 | [-0.057, +0.019] | [-0.066, +0.028] | contains 0 |
| TF-INIT · onestep · fau · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.035 | [-0.014, +0.084] | [-0.019, +0.090] | contains 0 |
| TF-INIT · onestep · fau · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | -0.065 | [-0.103, -0.027] | [-0.109, -0.020] | I<0 |
| TF-LOCAL · onestep · fau · reve · 3413 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.058 | [+0.032, +0.084] | [+0.025, +0.091] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3413 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.015 | [-0.011, +0.042] | [-0.018, +0.048] | contains 0 |
| TF-LOCAL · onestep · fau · reve · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.082 | [+0.044, +0.121] | [+0.033, +0.132] | I>0 |
| TF-LOCAL · onestep · fau · reve · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.031 | [-0.009, +0.071] | [-0.019, +0.080] | contains 0 |
| TF-INIT · onestep · fau · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 67 (67) | +0.024 | [-0.016, +0.065] | [-0.021, +0.070] | contains 0 |
| TF-INIT · onestep · fau · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 67 (67) | +0.015 | [-0.030, +0.060] | [-0.036, +0.066] | contains 0 |
| TF-LOCAL · onestep · fau · reve · seedmean | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.083 | [+0.056, +0.110] | [+0.049, +0.117] | I>0 |
| TF-LOCAL · onestep · fau · reve · seedmean | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.047 | [+0.024, +0.071] | [+0.018, +0.076] | I>0 |
| TF-LOCAL · onestep · fau · reve · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 67 (67) | +0.106 | [+0.070, +0.143] | [+0.061, +0.152] | I>0 |
| TF-LOCAL · onestep · fau · reve · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 67 (67) | +0.023 | [-0.008, +0.054] | [-0.016, +0.062] | contains 0 |
| TF-LOCAL · onestep · dtu · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.373 | [-0.457, -0.289] | [-0.482, -0.264] | I<0 |
| TF-LOCAL · onestep · dtu · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | -0.018 | [-0.082, +0.046] | [-0.100, +0.064] | contains 0 |
| TF-LOCAL · onestep · dtu · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.162 | [+0.089, +0.235] | [+0.070, +0.254] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.213 | [+0.151, +0.275] | [+0.135, +0.292] | I>0 |
| TF-LOCAL · warmup · dtu · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 44 (44) | -0.372 | [-0.457, -0.286] | [-0.482, -0.261] | I<0 |
| TF-LOCAL · warmup · dtu · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 44 (44) | -0.008 | [-0.069, +0.053] | [-0.085, +0.069] | contains 0 |
| TF-LOCAL · warmup · dtu · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 44 (44) | +0.164 | [+0.089, +0.239] | [+0.070, +0.258] | I>0 |
| TF-LOCAL · warmup · dtu · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 44 (44) | +0.232 | [+0.163, +0.301] | [+0.145, +0.319] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.535 | [+0.452, +0.618] | [+0.441, +0.629] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.231 | [+0.168, +0.294] | [+0.162, +0.301] | I>0 |
| TF-INIT · warmup · dtu · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 44 (44) | +0.536 | [+0.450, +0.621] | [+0.442, +0.629] | I>0 |
| TF-INIT · warmup · dtu · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 44 (44) | +0.240 | [+0.175, +0.305] | [+0.168, +0.311] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · 3407 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.223 | [-0.304, -0.142] | [-0.322, -0.123] | I<0 |
| TF-LOCAL · onestep · dtu · cbramod · 3407 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.057 | [-0.015, +0.129] | [-0.031, +0.145] | contains 0 |
| TF-LOCAL · onestep · dtu · cbramod · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.192 | [+0.106, +0.278] | [+0.090, +0.294] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.229 | [+0.154, +0.305] | [+0.137, +0.322] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.414 | [+0.344, +0.484] | [+0.334, +0.494] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.172 | [+0.121, +0.224] | [+0.114, +0.230] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · 3413 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.339 | [-0.424, -0.255] | [-0.447, -0.231] | I<0 |
| TF-LOCAL · onestep · dtu · cbramod · 3413 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.001 | [-0.062, +0.063] | [-0.080, +0.081] | contains 0 |
| TF-LOCAL · onestep · dtu · cbramod · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.148 | [+0.066, +0.230] | [+0.044, +0.252] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.196 | [+0.123, +0.270] | [+0.105, +0.288] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.487 | [+0.417, +0.558] | [+0.408, +0.567] | I>0 |
| TF-INIT · onestep · dtu · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.196 | [+0.138, +0.254] | [+0.130, +0.261] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · seedmean | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.312 | [-0.391, -0.232] | [-0.411, -0.213] | I<0 |
| TF-LOCAL · onestep · dtu · cbramod · seedmean | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.013 | [-0.049, +0.076] | [-0.064, +0.090] | contains 0 |
| TF-LOCAL · onestep · dtu · cbramod · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.167 | [+0.089, +0.246] | [+0.071, +0.264] | I>0 |
| TF-LOCAL · onestep · dtu · cbramod · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.213 | [+0.145, +0.281] | [+0.129, +0.297] | I>0 |
| TF-LOCAL · onestep · dtu · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.021 | [-0.077, +0.035] | [-0.089, +0.047] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | -0.059 | [-0.117, -0.001] | [-0.132, +0.014] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.006 | [-0.086, +0.074] | [-0.110, +0.098] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.003 | [-0.076, +0.082] | [-0.094, +0.100] | contains 0 |
| TF-LOCAL · warmup · dtu · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 44 (44) | -0.045 | [-0.100, +0.009] | [-0.112, +0.022] | contains 0 |
| TF-LOCAL · warmup · dtu · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 44 (44) | +0.011 | [-0.041, +0.062] | [-0.053, +0.075] | contains 0 |
| TF-LOCAL · warmup · dtu · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 44 (44) | -0.026 | [-0.101, +0.049] | [-0.119, +0.067] | contains 0 |
| TF-LOCAL · warmup · dtu · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 44 (44) | -0.068 | [-0.163, +0.027] | [-0.188, +0.053] | contains 0 |
| TF-INIT · onestep · dtu · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.015 | [-0.066, +0.096] | [-0.076, +0.106] | contains 0 |
| TF-INIT · onestep · dtu · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.062 | [-0.008, +0.132] | [-0.018, +0.142] | contains 0 |
| TF-INIT · warmup · dtu · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 44 (44) | +0.019 | [-0.047, +0.086] | [-0.055, +0.094] | contains 0 |
| TF-INIT · warmup · dtu · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 44 (44) | -0.079 | [-0.168, +0.010] | [-0.180, +0.023] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3407 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.021 | [-0.084, +0.043] | [-0.098, +0.057] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3407 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | -0.001 | [-0.068, +0.066] | [-0.082, +0.080] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.052 | [-0.017, +0.121] | [-0.038, +0.143] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3407 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.114 | [+0.014, +0.214] | [-0.016, +0.244] | contains 0 |
| TF-INIT · onestep · dtu · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.073 | [-0.007, +0.153] | [-0.017, +0.162] | contains 0 |
| TF-INIT · onestep · dtu · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.115 | [+0.036, +0.194] | [+0.024, +0.205] | I>0 |
| TF-LOCAL · onestep · dtu · reve · 3413 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.003 | [-0.061, +0.055] | [-0.075, +0.069] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3413 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | -0.077 | [-0.134, -0.019] | [-0.148, -0.005] | I<0 |
| TF-LOCAL · onestep · dtu · reve · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.037 | [-0.036, +0.110] | [-0.055, +0.128] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · 3413 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.130 | [+0.055, +0.205] | [+0.035, +0.224] | I>0 |
| TF-INIT · onestep · dtu · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 44 (44) | +0.040 | [-0.032, +0.111] | [-0.042, +0.122] | contains 0 |
| TF-INIT · onestep · dtu · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 44 (44) | +0.206 | [+0.132, +0.281] | [+0.120, +0.293] | I>0 |
| TF-LOCAL · onestep · dtu · reve · seedmean | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 44 (44) | -0.015 | [-0.070, +0.040] | [-0.082, +0.053] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · seedmean | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 44 (44) | -0.046 | [-0.102, +0.011] | [-0.114, +0.023] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 44 (44) | +0.028 | [-0.041, +0.097] | [-0.061, +0.116] | contains 0 |
| TF-LOCAL · onestep · dtu · reve · seedmean | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 44 (44) | +0.082 | [+0.007, +0.158] | [-0.015, +0.180] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 86 (86) | +0.063 | [+0.025, +0.101] | [+0.018, +0.108] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 86 (86) | +0.141 | [+0.082, +0.200] | [+0.073, +0.209] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 86 (86) | +0.180 | [+0.115, +0.246] | [+0.103, +0.258] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 86 (86) | +0.196 | [+0.129, +0.263] | [+0.118, +0.275] | I>0 |
| TF-LOCAL · warmup · federici · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 86 (86) | +0.059 | [+0.015, +0.103] | [+0.006, +0.112] | I>0 |
| TF-LOCAL · warmup · federici · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 86 (86) | +0.125 | [+0.076, +0.173] | [+0.066, +0.183] | I>0 |
| TF-LOCAL · warmup · federici · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 86 (86) | +0.183 | [+0.119, +0.247] | [+0.105, +0.261] | I>0 |
| TF-LOCAL · warmup · federici · cbramod · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 86 (86) | +0.192 | [+0.129, +0.255] | [+0.116, +0.269] | I>0 |
| TF-INIT · onestep · federici · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 86 (86) | +0.117 | [+0.069, +0.165] | [+0.064, +0.170] | I>0 |
| TF-INIT · onestep · federici · cbramod · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 86 (86) | +0.055 | [+0.023, +0.087] | [+0.018, +0.091] | I>0 |
| TF-INIT · warmup · federici · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 86 (86) | +0.124 | [+0.077, +0.171] | [+0.070, +0.178] | I>0 |
| TF-INIT · warmup · federici · cbramod · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 86 (86) | +0.068 | [+0.031, +0.104] | [+0.026, +0.109] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · 3407 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.006 | [-0.075, +0.087] | [-0.094, +0.106] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3407 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.081 | [-0.034, +0.196] | [-0.062, +0.224] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3407 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.139 | [+0.010, +0.268] | [-0.025, +0.303] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3407 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.142 | [-0.014, +0.298] | [-0.054, +0.338] | contains 0 |
| TF-INIT · onestep · federici · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 19 (19) | +0.133 | [+0.002, +0.264] | [-0.015, +0.281] | contains 0 |
| TF-INIT · onestep · federici · cbramod · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 19 (19) | +0.061 | [-0.016, +0.138] | [-0.026, +0.149] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3413 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.084 | [+0.004, +0.163] | [-0.013, +0.180] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3413 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.159 | [+0.036, +0.282] | [+0.011, +0.307] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · 3413 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.135 | [+0.006, +0.263] | [-0.024, +0.294] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · 3413 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.193 | [+0.061, +0.325] | [+0.029, +0.356] | I>0 |
| TF-INIT · onestep · federici · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 19 (19) | +0.051 | [-0.050, +0.152] | [-0.065, +0.167] | contains 0 |
| TF-INIT · onestep · federici · cbramod · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 19 (19) | +0.034 | [-0.020, +0.088] | [-0.028, +0.095] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · seedmean | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.048 | [-0.013, +0.108] | [-0.027, +0.122] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · seedmean | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.144 | [+0.025, +0.262] | [+0.002, +0.286] | I>0 |
| TF-LOCAL · onestep · federici · cbramod · seedmean | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.147 | [+0.020, +0.275] | [-0.008, +0.303] | contains 0 |
| TF-LOCAL · onestep · federici · cbramod · seedmean | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.176 | [+0.030, +0.323] | [-0.001, +0.354] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr1e-05 | 86 (86) | +0.175 | [+0.106, +0.243] | [+0.093, +0.256] | I>0 |
| TF-LOCAL · onestep · federici · reve · 3401 | exploratory | L1->random_full/full_onestep_v1/lr0.0003 | 86 (86) | +0.183 | [+0.118, +0.247] | [+0.105, +0.261] | I>0 |
| TF-LOCAL · onestep · federici · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr1e-05 | 86 (86) | +0.087 | [+0.036, +0.139] | [+0.024, +0.151] | I>0 |
| TF-LOCAL · onestep · federici · reve · 3401 | exploratory | L1->pretrained_full/full_onestep_v1/lr0.0003 | 86 (86) | +0.167 | [+0.109, +0.225] | [+0.096, +0.238] | I>0 |
| TF-LOCAL · warmup · federici · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr1e-05 | 86 (86) | +0.172 | [+0.106, +0.238] | [+0.092, +0.251] | I>0 |
| TF-LOCAL · warmup · federici · reve · 3401 | exploratory; warm-up, 3401 only | L1->random_full/warmup_then_all_v1/lr0.0003 | 86 (86) | +0.186 | [+0.120, +0.252] | [+0.108, +0.265] | I>0 |
| TF-LOCAL · warmup · federici · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr1e-05 | 86 (86) | +0.090 | [+0.039, +0.141] | [+0.028, +0.152] | I>0 |
| TF-LOCAL · warmup · federici · reve · 3401 | exploratory; warm-up, 3401 only | L1->pretrained_full/warmup_then_all_v1/lr0.0003 | 86 (86) | +0.083 | [+0.030, +0.135] | [+0.019, +0.146] | I>0 |
| TF-INIT · onestep · federici · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 86 (86) | -0.087 | [-0.138, -0.036] | [-0.148, -0.027] | I<0 |
| TF-INIT · onestep · federici · reve · 3401 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 86 (86) | -0.016 | [-0.051, +0.020] | [-0.057, +0.026] | contains 0 |
| TF-INIT · warmup · federici · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr1e-05 | 86 (86) | -0.082 | [-0.131, -0.034] | [-0.138, -0.026] | I<0 |
| TF-INIT · warmup · federici · reve · 3401 | warm-up, 3401 only | warmup_then_all_v1/lr0.0003 | 86 (86) | -0.104 | [-0.158, -0.049] | [-0.164, -0.043] | I<0 |
| TF-LOCAL · onestep · federici · reve · 3407 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.159 | [+0.007, +0.310] | [-0.018, +0.335] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3407 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.126 | [-0.037, +0.289] | [-0.063, +0.316] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3407 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.014 | [-0.069, +0.098] | [-0.083, +0.112] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3407 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 0 (0) | – | – | – | – |
| TF-INIT · onestep · federici · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 19 (19) | -0.144 | [-0.252, -0.036] | [-0.252, -0.036] | I<0 |
| TF-INIT · onestep · federici · reve · 3407 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 0 (0) | – | – | – | – |
| TF-LOCAL · onestep · federici · reve · 3413 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.160 | [+0.023, +0.296] | [-0.002, +0.322] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3413 | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.110 | [-0.041, +0.262] | [-0.071, +0.292] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3413 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.060 | [-0.010, +0.131] | [-0.024, +0.145] | contains 0 |
| TF-LOCAL · onestep · federici · reve · 3413 | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 0 (0) | – | – | – | – |
| TF-INIT · onestep · federici · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr1e-05 | 19 (19) | -0.099 | [-0.213, +0.014] | [-0.213, +0.014] | contains 0 |
| TF-INIT · onestep · federici · reve · 3413 | interim (ADDENDUM_11 role); partial coverage | full_onestep_v1/lr0.0003 | 0 (0) | – | – | – | – |
| TF-LOCAL · onestep · federici · reve · seedmean | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.163 | [+0.024, +0.302] | [-0.001, +0.326] | contains 0 |
| TF-LOCAL · onestep · federici · reve · seedmean | exploratory; partial coverage | L1->random_full/full_onestep_v1/lr0.0003 | 19 (19) | +0.135 | [-0.014, +0.284] | [-0.041, +0.311] | contains 0 |
| TF-LOCAL · onestep · federici · reve · seedmean | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr1e-05 | 19 (19) | +0.024 | [-0.044, +0.093] | [-0.054, +0.102] | contains 0 |
| TF-LOCAL · onestep · federici · reve · seedmean | exploratory; partial coverage | L1->pretrained_full/full_onestep_v1/lr0.0003 | 0 (0) | – | – | – | – |

## Appendix B. Notes

- none
