# ALN3.5 probability-fusion attribution

CPU Slurm 1047581; 29/30 bundles; status **interim**.

Positive contrasts mean the actual local+CB mixture has lower true risk. Intervals use person-level fixed-SE max-|z*|; folds, seeds and permutations do not increase n. Original primary fusion statistics are unchanged.

| Family | Contrast | Estimate | Simultaneous interval |
|---|---|---:|---|
| S35_FUSION_native_four_three_seed_primary | cb_direct_minus_actual_mix | 0.05428283599689028 | [0.027312140065102936, 0.08125353192867762] |
| S35_FUSION_native_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.14249060273303987 | [0.07651388615468808, 0.20846731931139167] |
| S35_FUSION_native_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.0560143248952151 | [0.030720413412704664, 0.08130823637772554] |
| S35_FUSION_native_four_three_seed_primary | cb_repeated_minus_actual_mix | 0.03006040123527944 | [0.0009848449797412694, 0.05913595749081761] |
| S35_FUSION_native_three_three_seed_primary | cb_direct_minus_actual_mix | 0.05428283599689028 | [0.027737008646369864, 0.08082866334741069] |
| S35_FUSION_native_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.14249060273303987 | [0.07755321543414717, 0.20742799003193257] |
| S35_FUSION_native_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.0560143248952151 | [0.031118867657765493, 0.08090978213266471] |
| S35_FUSION_native_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.06163943797271102 | [0.03816572792958775, 0.08511314801583429] |
| S35_FUSION_unified_four_three_seed_primary | cb_direct_minus_actual_mix | 0.046693924445156326 | [0.018120222173652938, 0.07526762671665971] |
| S35_FUSION_unified_four_three_seed_primary | cb_temperature_minus_actual_mix | 0.023300085658602004 | [-0.0032197357349492348, 0.049819907052153244] |
| S35_FUSION_unified_four_three_seed_primary | cb_shrink_minus_actual_mix | 0.025998011382101716 | [0.0018256237526245757, 0.05017039901157885] |
| S35_FUSION_unified_four_three_seed_primary | cb_repeated_minus_actual_mix | -0.009147549907536466 | [-0.035731256983421326, 0.01743615716834839] |
| S35_FUSION_unified_three_three_seed_primary | cb_direct_minus_actual_mix | 0.046693924445156326 | [0.018558310839354577, 0.07482953805095807] |
| S35_FUSION_unified_three_three_seed_primary | cb_temperature_minus_actual_mix | 0.023300085658602004 | [-0.0028131369309666865, 0.049413308248170695] |
| S35_FUSION_unified_three_three_seed_primary | cb_shrink_minus_actual_mix | 0.025998011382101716 | [0.002196231976326183, 0.049799790787877246] |
| S35_FUSION_unified_permutation_three_seed_primary | local_permuted_mix_minus_actual_mix | 0.04480462664918147 | [0.022066583824229106, 0.06754266947413384] |

Incomplete cyclic seed ensembles are explicitly missing; the three-reference family was declared separately before reading its outcomes.

Detailed coverage and seed-specific interim sensitivities: `results/auditory_alignment_v3/aln35/fusion/run_1047581/contrasts.json`. Exact query metadata remains private.
