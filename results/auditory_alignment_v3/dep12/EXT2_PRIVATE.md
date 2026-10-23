# EXT2 private read-outs (follow-up; cs_pair_noise)

Generated 2026-10-23T11:59:48.436813+02:00 (job 1059699). follow-up ext2 (DECISIONS 2026-10-23 10:55, P24); designed after the round results; beyond the package budget.

Arm cs_pair_noise = the cs_pair LoRA recipe with i.i.d. unit-Gaussian 32-d targets per view (S20-S22). Contrasts: cs_pair_noise − B0 and cs_pair − cs_pair_noise (positive = first-named higher). Person bootstrap-t, B = 10,000; simultaneous 95% intervals within each family (one family per cohort × endpoint × seed / merged). Single-seed rows are single-seed evidence; merged rows average each child over seeds 3401/3407/3413.

**Primary:** BDF U0 all-trials G: cs_pair_noise - B0 and cs_pair - cs_pair_noise, per seed and merged.

Missing encoders: {"BDF": ["cs_pair_noise@3413"], "MFF": ["cs_pair_noise@3413"]}

## Primary: BDF U0 G (bits/trial)

| family | role | member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---|---|---:|---:|---|---|
| EXT2:BDF:G[3401] | primary | cs_pair_noise-B0 | 64 | +0.003283 | [+0.001229, +0.005336] | [+0.000942, +0.005623] |
| EXT2:BDF:G[3401] | primary | cs_pair-cs_pair_noise | 64 | +0.000399 | [-0.000330, +0.001128] | [-0.000434, +0.001231] |
| EXT2:BDF:G[3407] | primary | cs_pair_noise-B0 | 64 | +0.003057 | [+0.000541, +0.005573] | [+0.000064, +0.006049] |
| EXT2:BDF:G[3407] | primary | cs_pair-cs_pair_noise | 64 | +0.000266 | [-0.001471, +0.002002] | [-0.001625, +0.002157] |

## Descriptive

| family | role | member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---|---|---:|---:|---|---|
| EXT2:BDF:delta[3401] | descriptive | cs_pair_noise-B0 | 64 | +0.000098 | [+0.000021, +0.000175] | [+0.000005, +0.000192] |
| EXT2:BDF:delta[3401] | descriptive | cs_pair-cs_pair_noise | 64 | -0.000003 | [-0.000048, +0.000042] | [-0.000052, +0.000047] |
| EXT2:BDF:delta[3407] | descriptive | cs_pair_noise-B0 | 64 | +0.000079 | [+0.000018, +0.000140] | [+0.000008, +0.000149] |
| EXT2:BDF:delta[3407] | descriptive | cs_pair-cs_pair_noise | 64 | +0.000055 | [+0.000002, +0.000109] | [-0.000006, +0.000116] |
| EXT2:BDF:delta_pca64[3401] | descriptive | cs_pair_noise-B0 | 64 | +0.000084 | [-0.000030, +0.000198] | [-0.000048, +0.000216] |
| EXT2:BDF:delta_pca64[3401] | descriptive | cs_pair-cs_pair_noise | 64 | +0.000023 | [-0.000041, +0.000087] | [-0.000050, +0.000095] |
| EXT2:BDF:delta_pca64[3407] | descriptive | cs_pair_noise-B0 | 64 | +0.000065 | [-0.000053, +0.000182] | [-0.000069, +0.000199] |
| EXT2:BDF:delta_pca64[3407] | descriptive | cs_pair-cs_pair_noise | 64 | +0.000033 | [-0.000079, +0.000145] | [-0.000094, +0.000160] |
| EXT2:BDF:auc_EEG_part[3401] | descriptive | cs_pair_noise-B0 | 64 | +0.021878 | [+0.010693, +0.033064] | [+0.009320, +0.034437] |
| EXT2:BDF:auc_EEG_part[3401] | descriptive | cs_pair-cs_pair_noise | 64 | +0.000532 | [-0.003648, +0.004712] | [-0.004241, +0.005305] |
| EXT2:BDF:auc_EEG_part[3407] | descriptive | cs_pair_noise-B0 | 64 | +0.020993 | [+0.009798, +0.032188] | [+0.008004, +0.033981] |
| EXT2:BDF:auc_EEG_part[3407] | descriptive | cs_pair-cs_pair_noise | 64 | +0.005188 | [-0.000753, +0.011130] | [-0.001559, +0.011936] |
| EXT2:MFF:within_G[3401] | descriptive | cs_pair_noise-B0 | 33 | +0.000127 | [-0.001239, +0.001493] | [-0.001424, +0.001678] |
| EXT2:MFF:within_G[3401] | descriptive | cs_pair-cs_pair_noise | 33 | -0.000414 | [-0.000920, +0.000091] | [-0.001010, +0.000181] |
| EXT2:MFF:within_G[3407] | descriptive | cs_pair_noise-B0 | 33 | +0.000163 | [-0.001109, +0.001435] | [-0.001282, +0.001608] |
| EXT2:MFF:within_G[3407] | descriptive | cs_pair-cs_pair_noise | 33 | -0.000021 | [-0.000764, +0.000722] | [-0.000843, +0.000801] |
| EXT2:MFF:transfer_AUC[3401] | descriptive | cs_pair_noise-B0 | 24 | +0.009746 | [-0.003385, +0.022877] | [-0.005348, +0.024840] |
| EXT2:MFF:transfer_AUC[3401] | descriptive | cs_pair-cs_pair_noise | 24 | -0.005628 | [-0.011523, +0.000267] | [-0.012425, +0.001170] |
| EXT2:MFF:transfer_AUC[3407] | descriptive | cs_pair_noise-B0 | 24 | +0.003749 | [-0.008116, +0.015614] | [-0.011428, +0.018926] |
| EXT2:MFF:transfer_AUC[3407] | descriptive | cs_pair-cs_pair_noise | 24 | +0.001717 | [-0.006369, +0.009802] | [-0.007587, +0.011020] |

### BDF levels (child means)

| encoder | G | delta | delta_pca64 | auc_EEG_part |
|---|---:|---:|---:|---:|
| B0 | -0.005831 | +0.000015 | +0.000035 | +0.504769 |
| cs_pair@3401 | -0.002150 | +0.000111 | +0.000142 | +0.527180 |
| cs_pair@3407 | -0.002508 | +0.000149 | +0.000133 | +0.530950 |
| cs_pair@3413 | -0.002798 | +0.000144 | +0.000160 | +0.529336 |
| cs_pair_noise@3401 | -0.002548 | +0.000113 | +0.000119 | +0.526648 |
| cs_pair_noise@3407 | -0.002774 | +0.000094 | +0.000100 | +0.525762 |

### MFF levels (child means)

| encoder | within_G | transfer_AUC |
|---|---:|---:|
| B0 | -0.001472 | +0.499106 |
| cs_pair@3401 | -0.001760 | +0.503224 |
| cs_pair@3407 | -0.001330 | +0.504572 |
| cs_pair@3413 | -0.001327 | +0.504032 |
| cs_pair_noise@3401 | -0.001345 | +0.508852 |
| cs_pair_noise@3407 | -0.001309 | +0.502855 |

Interpretation rule (coordinator, fixed at 10:55): cs_pair_noise ≈ cs_pair (> B0) → sound-independent training effect; cs_pair_noise ≈ B0 < cs_pair → the sound kernel structure contributes; otherwise partial. This file reports values only.
