# ALN3.5 probability-fusion attribution

CPU Slurm 1047303; 24/30 bundles; status **interim**.

The displayed three-seed families currently have **20/44 complete paired people**, not the full DTU panel. The other 24 people have missing required source/seed cells, preserved in the coverage tables. The family IDs name the planned three-seed analysis; they do not imply completed whole-panel coverage. Single-seed interim families and exact exclusions are in the linked JSON. These preliminary values should be revisited after the six remaining registered bundles finish.

Positive contrasts mean the actual local+CB mixture has lower true risk. Intervals use person-level fixed-SE max-|z*|; folds, seeds and permutations do not increase n. Original primary fusion statistics are unchanged.

| Family | Contrast | Estimate | Simultaneous interval |
|---|---|---:|---|
| S35_FUSION_native_four_three_seed_primary | cb_direct_minus_actual_mix | 0.07679770678847231 | [0.04214803889796549, 0.11144737467897912] |
| S35_FUSION_native_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.11671944861144408 | [0.08189448097317628, 0.15154441624971188] |
| S35_FUSION_native_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.07246301007032259 | [0.03765572173396594, 0.10727029840667923] |
| S35_FUSION_native_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.05906157371923957 | [0.022570668278776088, 0.09555247915970305] |
| S35_FUSION_native_three_three_seed_primary | cb_direct_minus_actual_mix | 0.07679770678847231 | [0.042710338244052654, 0.11088507533289196] |
| S35_FUSION_native_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.11671944861144408 | [0.08245962510651644, 0.15097927211637172] |
| S35_FUSION_native_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.07246301007032259 | [0.0382205789652805, 0.10670544117536468] |
| S35_FUSION_native_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.09003959034494957 | [0.062345865068394415, 0.11773331562150473] |
| S35_FUSION_unified_four_three_seed_primary | cb_direct_minus_actual_mix | 0.08500839096507008 | [0.0521256823360732, 0.11789109959406696] |
| S35_FUSION_unified_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.042899481149272285 | [0.00566820867343245, 0.08013075362511213] |
| S35_FUSION_unified_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.0461337864039368 | [0.01512932286434783, 0.07713824994352576] |
| S35_FUSION_unified_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.02239124917051715 | [-0.009591604162893223, 0.054374102503927525] |
| S35_FUSION_unified_three_three_seed_primary | cb_direct_minus_actual_mix | 0.08500839096507008 | [0.05295326436401198, 0.11706351756612818] |
| S35_FUSION_unified_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.042899481149272285 | [0.0066052340360914785, 0.07919372826245309] |
| S35_FUSION_unified_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.0461337864039368 | [0.015909633790091353, 0.07635793901778223] |
| S35_FUSION_unified_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.08160765493231534 | [0.05831334630636664, 0.10490196355826403] |

Incomplete cyclic seed ensembles are explicitly missing; the three-reference family was declared separately before reading its outcomes.

Detailed coverage and seed-specific interim sensitivities: `results/auditory_alignment_v3/aln35/fusion/run_1047303/contrasts.json`. Exact query metadata remains private.
