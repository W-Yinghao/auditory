# ALN3.5 probability-fusion attribution

CPU Slurm 1047464; 26/30 bundles; status **interim**.

Positive contrasts mean the actual local+CB mixture has lower true risk. Intervals use person-level fixed-SE max-|z*|; folds, seeds and permutations do not increase n. Original primary fusion statistics are unchanged.

| Family | Contrast | Estimate | Simultaneous interval |
|---|---|---:|---|
| S35_FUSION_native_four_three_seed_primary | cb_direct_minus_actual_mix | 0.06630216836098388 | [0.03835234966642083, 0.09425198705554692] |
| S35_FUSION_native_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.17971215416460481 | [0.10189866569977944, 0.2575256426294302] |
| S35_FUSION_native_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.06328875591525113 | [0.03575118360764658, 0.09082632822285568] |
| S35_FUSION_native_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.046168107698811196 | [0.015174430959007803, 0.07716178443861459] |
| S35_FUSION_native_three_three_seed_primary | cb_direct_minus_actual_mix | 0.06630216836098388 | [0.03877575822423158, 0.09382857849773618] |
| S35_FUSION_native_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.17971215416460481 | [0.1030774532006631, 0.25634685512854655] |
| S35_FUSION_native_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.06328875591525113 | [0.036168347092812234, 0.09040916473769002] |
| S35_FUSION_native_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.07576065661561052 | [0.0533117779099786, 0.09820953532124244] |
| S35_FUSION_unified_four_three_seed_primary | cb_direct_minus_actual_mix | 0.06351900824925714 | [0.036039622783258785, 0.0909983937152555] |
| S35_FUSION_unified_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.033441215523687284 | [0.006518959367666534, 0.060363471679708035] |
| S35_FUSION_unified_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.03575143356273337 | [0.012828200018943945, 0.058674667106522804] |
| S35_FUSION_unified_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.004439620494987251 | [-0.021407095085975825, 0.030286336075950326] |
| S35_FUSION_unified_three_three_seed_primary | cb_direct_minus_actual_mix | 0.06351900824925714 | [0.03640982426132536, 0.09062819223718893] |
| S35_FUSION_unified_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.033441215523687284 | [0.006881655215948083, 0.06000077583142649] |
| S35_FUSION_unified_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.03575143356273337 | [0.013137021151442586, 0.05836584597402416] |
| S35_FUSION_unified_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.06108991108300378 | [0.04101252096803327, 0.0811673011979743] |

Incomplete cyclic seed ensembles are explicitly missing; the three-reference family was declared separately before reading its outcomes.

Detailed coverage and seed-specific interim sensitivities: `results/auditory_alignment_v3/aln35/fusion/run_1047464/contrasts.json`. Exact query metadata remains private.
