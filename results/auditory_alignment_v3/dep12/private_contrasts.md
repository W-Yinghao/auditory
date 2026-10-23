# DEP12 private children: results (Agent P)

Generated 2026-10-23T05:41:06.407424+02:00 (job 1058973); binding d1eab492546d; encoders with results: 9.

G = mean log2 p_E(y) − log2 p_B1(y) on the outer-test children (bits/trial); B1 = history-only single intercept on the same source-ES rows. Intervals: person bootstrap-t, B = 10,000, simultaneous = family max-|T*|.

## EXPLORATORY_REUSED_VS_B0:G — U0 all-trials G difference vs B0, bits/trial (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.687

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| REVE0-B0 | 64 | +0.00031 | [-0.00292, +0.00353] | [-0.00305, +0.00366] |
| MINDMIX_branch-B0 | 64 | +0.00084 | [-0.00099, +0.00266] | [-0.00164, +0.00331] |

## EXPLORATORY_REUSED_VS_B0:AUC — U0 AUC of the readout EEG part, difference vs B0 (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.270

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| REVE0-B0 | 64 | -0.00091 | [-0.00969, +0.00786] | [-0.01075, +0.00893] |
| MINDMIX_branch-B0 | 64 | +0.01001 | [+0.00063, +0.01939] | [-0.00058, +0.02061] |

## EXPLORATORY_REUSED_VS_B0:delta_profile — n128 δ excess CS difference vs B0, nats (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.267

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| REVE0-B0 | 64 | +0.00001 | [-0.00005, +0.00007] | [-0.00005, +0.00007] |
| MINDMIX_branch-B0 | 64 | +0.00003 | [-0.00004, +0.00010] | [-0.00005, +0.00011] |

## EXPLORATORY_REUSED_VS_B0:delta_profile_pca64 — n128 δ excess CS on the PCA64 kernel variant vs B0, nats (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.310

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| REVE0-B0 | 64 | -0.00004 | [-0.00016, +0.00008] | [-0.00018, +0.00010] |
| MINDMIX_branch-B0 | 64 | +0.00000 | [-0.00015, +0.00015] | [-0.00017, +0.00018] |

## EXPLORATORY_SELECTION_ALN41[3401] — U10 query log2-score (exploratory candidate set)

status complete, n = 64/64, critical +2.999

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | -0.00040 | [-0.00208, +0.00128] | [-0.00271, +0.00192] |
| delta_cs-support_cv | 64 | -0.00017 | [-0.00114, +0.00080] | [-0.00163, +0.00129] |
| delta_cs-uniform | 64 | -0.00458 | [-0.00562, -0.00354] | [-0.00586, -0.00330] |
| delta_train_profile-fixed | 64 | -0.00018 | [-0.00226, +0.00191] | [-0.00329, +0.00293] |
| delta_cs_pca64-support_cv | 64 | +0.00021 | [-0.00074, +0.00116] | [-0.00120, +0.00162] |
| delta_cs_pca64-delta_cs | 64 | +0.00038 | [-0.00057, +0.00133] | [-0.00087, +0.00163] |

## Levels per encoder (child means; descriptive)

| encoder | n | G all (bits) | G contract | AUC EEG part | δ excess n128 U (nats) | δ excess n128 PCA64 | E−twin (bits) |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 | 64 | -0.00583 | -0.00553 | +0.5048 | +0.000015 | +0.000035 | +0.00156 |
| MINDMIX_branch | 64 | -0.00499 | -0.00467 | +0.5148 | +0.000046 | +0.000037 | +0.00121 |
| REVE0 | 64 | -0.00553 | -0.00532 | +0.5039 | +0.000026 | -0.000004 | -0.00030 |
| aln41_GCS@3401 | 64 | -0.00402 | -0.00426 | +0.5102 | -0.000053 | -0.000049 | +0.00478 |
| aln41_TCS@3401 | 64 | -0.00468 | -0.00411 | +0.5147 | +0.000140 | +0.000094 | +0.00251 |
| aln41_TCS@3407 | 64 | -0.00482 | -0.00487 | +0.5067 | -0.000012 | -0.000031 | +0.00423 |
| aln41_TNCE@3401 | 64 | -0.00392 | -0.00404 | +0.5202 | +0.000035 | +0.000074 | +0.00364 |
| aln41_TNCE@3407 | 64 | -0.00441 | -0.00493 | +0.5181 | -0.000009 | +0.000039 | +0.00318 |
| aln41_WRONG@3401 | 64 | -0.00563 | -0.00556 | +0.5138 | +0.000165 | +0.000088 | +0.00127 |

## By protocol (child60 = audited alternative sequence; regular = the other 63)

| encoder | regular G | regular δ excess | child60 G | child60 δ excess |
|---|---:|---:|---:|---:|
| B0 | -0.00617 | +0.000016 | +0.01541 | -0.000063 |
| MINDMIX_branch | -0.00578 | +0.000046 | +0.04460 | +0.000053 |
| REVE0 | -0.00486 | +0.000025 | -0.04762 | +0.000061 |
| aln41_GCS@3401 | -0.00477 | -0.000048 | +0.04291 | -0.000357 |
| aln41_TCS@3401 | -0.00479 | +0.000142 | +0.00229 | -0.000002 |
| aln41_TCS@3407 | -0.00557 | -0.000006 | +0.04248 | -0.000371 |
| aln41_TNCE@3401 | -0.00363 | +0.000029 | -0.02207 | +0.000444 |
| aln41_TNCE@3407 | -0.00380 | -0.000014 | -0.04330 | +0.000306 |
| aln41_WRONG@3401 | -0.00606 | +0.000168 | +0.02155 | -0.000028 |

## δ profile sensitivity (seed 3401 encoders and B0; child means of excess CS, nats)

| encoder | n32 ×1 | n64 ×1 | n128 ×0.5 | n128 ×1 | n128 ×2 |
|---|---:|---:|---:|---:|---:|
| B0 | -0.000122 | -0.000063 | +0.000031 | +0.000015 | +0.000004 |
| aln41_GCS@3401 | +0.000418 | +0.000081 | -0.000037 | -0.000053 | -0.000017 |
| aln41_TCS@3401 | -0.000233 | +0.000240 | +0.000457 | +0.000140 | +0.000035 |
| aln41_TNCE@3401 | -0.000038 | +0.000193 | +0.000265 | +0.000035 | +0.000007 |
| aln41_WRONG@3401 | -0.000082 | +0.000355 | +0.000787 | +0.000165 | +0.000024 |

## U10 decisions and fallbacks (counts over child × support seed)

- aln41_s3401: fixed by fold {0: 'aln41_GCS@3401', 1: 'aln41_TNCE@3401', 2: 'aln41_TCS@3401', 3: 'aln41_GCS@3401', 4: 'B0'}; decisions {'delta_cs:aln41_GCS@3401': 93, 'delta_cs_pca64:B0': 76, 'delta_train_profile:aln41_TCS@3401': 320, 'fixed:aln41_GCS@3401': 130, 'support_cv:aln41_TNCE@3401': 88, 'delta_cs_pca64:aln41_GCS@3401': 78, 'support_cv:aln41_TCS@3401': 78, 'delta_cs_pca64:aln41_TCS@3401': 88, 'support_cv:aln41_GCS@3401': 91, 'delta_cs_pca64:aln41_TNCE@3401': 78, 'delta_cs:B0': 76, 'delta_cs:aln41_TCS@3401': 88, 'delta_cs:aln41_TNCE@3401': 63, 'support_cv:B0': 63, 'fixed:aln41_TNCE@3401': 65, 'fixed:aln41_TCS@3401': 65, 'fixed:B0': 60}; fallbacks none

## Cross-stimulus (recovered ALN4.1 R2, pure tone → bapa; not re-run)

Source results/auditory_alignment_v3/aln41/r2/contrasts.json (sha256 27e68ffefb59).

### F_CROSS_STIM:BAPA

| member | n | estimate | simultaneous 95% |
|---|---:|---:|---|
| B0:transfer-0.5 | 24 | +0.00657 | [-0.01248, +0.02562] |
| B0:refit-0.5 | 24 | -0.00477 | [-0.03142, +0.02188] |
| B0:refit-transfer | 24 | -0.01134 | [-0.03490, +0.01222] |
| TCS:transfer-0.5 | 24 | +0.00374 | [-0.01322, +0.02069] |
| TCS:refit-0.5 | 24 | +0.00172 | [-0.01869, +0.02212] |
| TCS:refit-transfer | 24 | -0.00202 | [-0.01881, +0.01477] |
| TNCE:transfer-0.5 | 24 | +0.01167 | [-0.01862, +0.04196] |
| TNCE:refit-0.5 | 24 | -0.00167 | [-0.02803, +0.02469] |
| TNCE:refit-transfer | 24 | -0.01334 | [-0.03486, +0.00818] |
| transfer:TCS-B0 | 24 | -0.00283 | [-0.01967, +0.01401] |
| transfer:TCS-TNCE | 24 | -0.00793 | [-0.02859, +0.01272] |
| refit:TCS-B0 | 24 | +0.00648 | [-0.00991, +0.02288] |
| refit:TCS-TNCE | 24 | +0.00338 | [-0.01134, +0.01810] |

### F_CROSS_STIM_SECONDARY:BAPA

| member | n | estimate | simultaneous 95% |
|---|---:|---:|---|
| B0:transfer-0.0 | 24 | -0.00062 | [-0.00191, +0.00066] |
| B0:refit-0.0 | 24 | -0.00202 | [-0.00455, +0.00052] |
| B0:refit-transfer | 24 | -0.00140 | [-0.00361, +0.00082] |
| TCS:transfer-0.0 | 24 | -0.00111 | [-0.00247, +0.00025] |
| TCS:refit-0.0 | 24 | -0.00181 | [-0.00358, -0.00003] |
| TCS:refit-transfer | 24 | -0.00070 | [-0.00212, +0.00073] |
| TNCE:transfer-0.0 | 24 | -0.00068 | [-0.00327, +0.00191] |
| TNCE:refit-0.0 | 24 | -0.00229 | [-0.00460, +0.00003] |
| TNCE:refit-transfer | 24 | -0.00161 | [-0.00325, +0.00003] |
| transfer:TCS-B0 | 24 | -0.00049 | [-0.00178, +0.00080] |
| transfer:TCS-TNCE | 24 | -0.00043 | [-0.00230, +0.00144] |
| refit:TCS-B0 | 24 | +0.00021 | [-0.00137, +0.00180] |
| refit:TCS-TNCE | 24 | +0.00048 | [-0.00083, +0.00180] |

### Same-day pairs (8; descriptive mean AUC [min, max])

| arm:route | n | mean AUC | range |
|---|---:|---:|---|
| B0:within | 8 | +0.5148 | [+0.453, +0.563] |
| B0:transfer | 8 | +0.5062 | [+0.466, +0.574] |
| B0:refit | 8 | +0.5019 | [+0.418, +0.564] |
| TCS:within | 8 | +0.5307 | [+0.492, +0.579] |
| TCS:transfer | 8 | +0.4992 | [+0.467, +0.529] |
| TCS:refit | 8 | +0.5041 | [+0.452, +0.543] |
| TNCE:within | 8 | +0.5538 | [+0.508, +0.598] |
| TNCE:transfer | 8 | +0.5150 | [+0.468, +0.599] |
| TNCE:refit | 8 | +0.5013 | [+0.436, +0.574] |

same-day pairs: 8 identity groups with both lanes on the same day; descriptive only. AUC within = pure-tone within-lane (person-disjoint folds), transfer = pure-tone readout on bapa, refit = bapa readout on bapa.

New frozen representations: not run: the existing formal path extracts three 400 ms crops through the ALN4.1 time bank and mixes slots with q0; applying it to the DEP12 1 s container would need a new extraction/readout definition (03 §6.2 condition not met)

