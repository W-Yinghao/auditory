# ALN3.5 probability-fusion attribution

CPU Slurm 1047619; 30/30 bundles; status **complete**.

Positive contrasts mean the actual local+CB mixture has lower true risk. Intervals use person-level fixed-SE max-|z*|; folds, seeds and permutations do not increase n. Original primary fusion statistics are unchanged.

| Family | Contrast | Estimate | Simultaneous interval |
|---|---|---:|---|
| S35_FUSION_native_four_three_seed_primary | cb_direct_minus_actual_mix | 0.05144353452536977 | [0.026395382551039865, 0.07649168649969967] |
| S35_FUSION_native_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.12361352549131036 | [0.06561568086731885, 0.18161137011530187] |
| S35_FUSION_native_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.054455467618059215 | [0.03254753903771491, 0.07636339619840352] |
| S35_FUSION_native_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.025494104029270794 | [-0.0013734096011929035, 0.05236161765973449] |
| S35_FUSION_native_three_three_seed_primary | cb_direct_minus_actual_mix | 0.05144353452536977 | [0.02663451455619485, 0.07625255449454468] |
| S35_FUSION_native_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.12361352549131036 | [0.06616938003418017, 0.18105767094844055] |
| S35_FUSION_native_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.054455467618059215 | [0.03275669166883831, 0.07615424356728012] |
| S35_FUSION_native_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.057462572505586756 | [0.03650671905301531, 0.0784184259581582] |
| S35_FUSION_unified_four_three_seed_primary | cb_direct_minus_actual_mix | 0.04534409136365106 | [0.020785439934221474, 0.06990274279308065] |
| S35_FUSION_unified_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.03606464719402771 | [0.011778511153234299, 0.06035078323482112] |
| S35_FUSION_unified_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.02820423150510268 | [0.007218222512740079, 0.04919024049746529] |
| S35_FUSION_unified_four_three_seed_primary | cb_repeated_minus_actual_mix | -0.008752167895507116 | [-0.03226975535699064, 0.014765419565976412] |
| S35_FUSION_unified_three_three_seed_primary | cb_direct_minus_actual_mix | 0.04534409136365106 | [0.021296603492732383, 0.06939157923456973] |
| S35_FUSION_unified_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.03606464719402771 | [0.01228400257880238, 0.059845291809253034] |
| S35_FUSION_unified_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.02820423150510268 | [0.007655025122455982, 0.048753437887749385] |
| S35_FUSION_unified_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.04695367906075128 | [0.028139489556589327, 0.06576786856491323] |

Incomplete cyclic seed ensembles are explicitly missing; the three-reference family was declared separately before reading its outcomes.

Detailed coverage and seed-specific interim sensitivities: `results/auditory_alignment_v3/aln35/fusion/run_1047619/contrasts.json`. Exact query metadata remains private.
