# ALN3.4 new-lane efficacy snapshot

Generated 2026-10-18T00:49:42.072859+02:00 by CPU job 1044744. Status: **interim**.

Complete identity pairing is required; seeds and folds do not increase n. Intervals condition on fitted models. Interim snapshots are not sequential significance tests. `historical_selected` tables reuse existing baseline records; they are not new budget results and do not replace the frozen ADDENDUM_11 analysis.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| learning_budget_v2 | 6 / 150 | 0 |
| data_inner_v1 | 69 / 590 | 0 |
| adaptation_policy_v1 | 6 / 120 | 0 |
| strong_fusion_v1 | 4 / 30 | 0 |
| episode_training_v1 | 3 / 80 | 0 |

Positive values mean lower true query NLL than the named reference. Native and unified are distinct families. All group summaries and coverage are in `results/auditory_alignment_v3/aln34/new_lanes/efficacy.json`.

## budget/cbramod/pretrained_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1600 | [-0.3184, -0.0017] |
| fixed_0.25 versus historical_selected | -0.1472 | [-0.3730, +0.0787] |
| fixed_0.5 versus historical_selected | -0.0309 | [-0.1529, +0.0911] |
| fixed_1.0 versus historical_selected | -0.0961 | [-0.2182, +0.0260] |
| fixed_2.0 versus historical_selected | -0.2562 | [-0.3839, -0.1285] |
| new_selected versus historical_selected | -0.2122 | [-0.3230, -0.1013] |

## budget/cbramod/pretrained_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0495 | [-0.2311, +0.1320] |
| fixed_0.25 versus historical_selected | -0.1134 | [-0.2772, +0.0504] |
| fixed_0.5 versus historical_selected | -0.0173 | [-0.1084, +0.0738] |
| fixed_1.0 versus historical_selected | -0.1297 | [-0.2609, +0.0014] |
| fixed_2.0 versus historical_selected | -0.1793 | [-0.3037, -0.0548] |
| new_selected versus historical_selected | -0.1460 | [-0.2530, -0.0390] |

## budget_models/historical_selected · native · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.4661 | [+0.3539, +0.5782] |
| cbramod/pretrained_full versus local | +0.3774 | [+0.2757, +0.4790] |
| cbramod/random_full versus local | -0.0887 | [-0.2113, +0.0339] |
| reve/pretrained_full versus local | +0.0672 | [-0.0581, +0.1924] |
| reve/random_full versus local | -0.1987 | [-0.3175, -0.0800] |
| reve/pretrained_full versus reve/random_full | +0.2659 | [+0.1238, +0.4080] |

## budget_models/historical_selected · native · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3376 | [+0.2341, +0.4411] |
| cbramod/pretrained_full versus local | +0.4263 | [+0.2997, +0.5528] |
| cbramod/random_full versus local | +0.0887 | [-0.0425, +0.2199] |
| reve/pretrained_full versus local | +0.0666 | [-0.0519, +0.1851] |
| reve/random_full versus local | -0.0880 | [-0.2107, +0.0347] |
| reve/pretrained_full versus reve/random_full | +0.1546 | [+0.0030, +0.3063] |

## budget_models/historical_selected · native · 3413

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.4100 | [+0.3136, +0.5063] |
| cbramod/pretrained_full versus local | +0.3795 | [+0.2458, +0.5133] |
| cbramod/random_full versus local | -0.0304 | [-0.1465, +0.0856] |
| reve/pretrained_full versus local | +0.1000 | [-0.0256, +0.2255] |
| reve/random_full versus local | -0.1340 | [-0.2493, -0.0188] |
| reve/pretrained_full versus reve/random_full | +0.2340 | [+0.1054, +0.3626] |

## budget_models/historical_selected · native · complete_seed_mean

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.4045 | [+0.3052, +0.5039] |
| cbramod/pretrained_full versus local | +0.3944 | [+0.2773, +0.5115] |
| cbramod/random_full versus local | -0.0101 | [-0.1264, +0.1061] |
| reve/pretrained_full versus local | +0.0779 | [-0.0363, +0.1921] |
| reve/random_full versus local | -0.1403 | [-0.2531, -0.0274] |
| reve/pretrained_full versus reve/random_full | +0.2182 | [+0.0861, +0.3503] |

## budget_models/historical_selected · unified · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.2314 | [+0.1487, +0.3140] |
| cbramod/pretrained_full versus local | +0.2132 | [+0.1309, +0.2956] |
| cbramod/random_full versus local | -0.0181 | [-0.1044, +0.0682] |
| reve/pretrained_full versus local | -0.0057 | [-0.1158, +0.1044] |
| reve/random_full versus local | -0.0207 | [-0.0928, +0.0514] |
| reve/pretrained_full versus reve/random_full | +0.0150 | [-0.0906, +0.1206] |

## budget_models/historical_selected · unified · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1723 | [+0.1017, +0.2428] |
| cbramod/pretrained_full versus local | +0.2293 | [+0.1236, +0.3351] |
| cbramod/random_full versus local | +0.0571 | [-0.0441, +0.1582] |
| reve/pretrained_full versus local | +0.0524 | [-0.0448, +0.1495] |
| reve/random_full versus local | -0.0205 | [-0.1039, +0.0629] |
| reve/pretrained_full versus reve/random_full | +0.0729 | [-0.0370, +0.1828] |

## budget_models/historical_selected · unified · 3413

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1956 | [+0.1176, +0.2737] |
| cbramod/pretrained_full versus local | +0.1962 | [+0.1017, +0.2908] |
| cbramod/random_full versus local | +0.0006 | [-0.0828, +0.0840] |
| reve/pretrained_full versus local | +0.0368 | [-0.0597, +0.1333] |
| reve/random_full versus local | -0.0029 | [-0.0790, +0.0731] |
| reve/pretrained_full versus reve/random_full | +0.0397 | [-0.0568, +0.1363] |

## budget_models/historical_selected · unified · complete_seed_mean

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1997 | [+0.1290, +0.2705] |
| cbramod/pretrained_full versus local | +0.2129 | [+0.1228, +0.3030] |
| cbramod/random_full versus local | +0.0132 | [-0.0695, +0.0958] |
| reve/pretrained_full versus local | +0.0278 | [-0.0650, +0.1207] |
| reve/random_full versus local | -0.0147 | [-0.0858, +0.0563] |
| reve/pretrained_full versus reve/random_full | +0.0426 | [-0.0513, +0.1364] |

## data/content/cbramod/pretrained_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6914 | [-0.8641, -0.5187] |
| 0.5 versus full | -0.4804 | [-0.6589, -0.3020] |

## data/content/cbramod/pretrained_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2191 | [-0.3606, -0.0776] |
| 0.5 versus full | -0.0902 | [-0.1825, +0.0022] |

## data/content/cbramod/random_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7773 | [-1.1344, -0.4203] |
| 0.5 versus full | -0.5202 | [-0.7660, -0.2745] |

## data/content/cbramod/random_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5214 | [-0.7566, -0.2862] |
| 0.5 versus full | -0.3232 | [-0.4680, -0.1784] |

## data/content/local · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5464 | [-0.8009, -0.2920] |
| 0.5 versus full | -0.3342 | [-0.5370, -0.1313] |

## data/content/local · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2928 | [-0.4326, -0.1530] |
| 0.5 versus full | -0.2597 | [-0.3596, -0.1598] |

## data/people/cbramod/pretrained_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7268 | [-1.0730, -0.3807] |
| 0.5 versus full | -0.4206 | [-0.6215, -0.2196] |

## data/people/cbramod/pretrained_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5626 | [-0.8536, -0.2715] |
| 0.5 versus full | -0.1318 | [-0.2800, +0.0165] |

## data/people/cbramod/random_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6460 | [-0.9342, -0.3577] |
| 0.5 versus full | -0.4473 | [-0.6382, -0.2564] |

## data/people/cbramod/random_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4778 | [-0.6596, -0.2960] |
| 0.5 versus full | -0.3249 | [-0.4963, -0.1535] |

## data/people/local · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6381 | [-0.9658, -0.3105] |
| 0.5 versus full | -0.2738 | [-0.5122, -0.0354] |

## data/people/local · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4554 | [-0.6982, -0.2126] |
| 0.5 versus full | -0.1774 | [-0.3130, -0.0417] |

## data/people/reve/pretrained_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7933 | [-1.1044, -0.4821] |
| 0.5 versus full | -0.5254 | [-0.7077, -0.3431] |

## data/people/reve/pretrained_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4563 | [-0.6433, -0.2692] |
| 0.5 versus full | -0.2089 | [-0.3379, -0.0798] |

## fusion/cb_pre · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.7741 | [-0.9434, -0.6048] |
| probability versus fm_direct | +0.0709 | [+0.0327, +0.1092] |
| residual versus fm_direct | -0.2944 | [-0.4456, -0.1431] |
| sc_local versus fm_direct | -0.8155 | [-0.9790, -0.6521] |
| common_linear versus local_direct | -0.4797 | [-0.6838, -0.2756] |
| probability versus local_direct | +0.3653 | [+0.2488, +0.4817] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5212 | [-0.7021, -0.3402] |
| common_linear versus strong_single | -0.6871 | [-0.8614, -0.5127] |
| probability versus strong_single | +0.1579 | [+0.0465, +0.2693] |
| residual versus strong_single | -0.2074 | [-0.3859, -0.0289] |
| sc_local versus strong_single | -0.7286 | [-0.8946, -0.5625] |

## fusion/cb_pre · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1095 | [-0.1947, -0.0244] |
| probability versus fm_direct | +0.1014 | [+0.0574, +0.1454] |
| residual versus fm_direct | -0.0848 | [-0.1882, +0.0186] |
| sc_local versus fm_direct | -0.2483 | [-0.3633, -0.1332] |
| common_linear versus local_direct | -0.0247 | [-0.0986, +0.0491] |
| probability versus local_direct | +0.1862 | [+0.1170, +0.2554] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1635 | [-0.2109, -0.1161] |
| common_linear versus strong_single | -0.0197 | [-0.1391, +0.0997] |
| probability versus strong_single | +0.1912 | [+0.0792, +0.3033] |
| residual versus strong_single | +0.0051 | [-0.1483, +0.1585] |
| sc_local versus strong_single | -0.1584 | [-0.3202, +0.0034] |

## fusion/cb_random · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.4058 | [-0.5479, -0.2637] |
| probability versus fm_direct | +0.1995 | [+0.1089, +0.2901] |
| residual versus fm_direct | +0.0016 | [-0.1350, +0.1382] |
| sc_local versus fm_direct | -0.5196 | [-0.6576, -0.3816] |
| common_linear versus local_direct | -0.4074 | [-0.5962, -0.2185] |
| probability versus local_direct | +0.1980 | [+0.1463, +0.2496] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5212 | [-0.6853, -0.3570] |
| common_linear versus strong_single | -0.6147 | [-0.7730, -0.4564] |
| probability versus strong_single | -0.0094 | [-0.1427, +0.1238] |
| residual versus strong_single | -0.2074 | [-0.3692, -0.0455] |
| sc_local versus strong_single | -0.7286 | [-0.8792, -0.5779] |

## fusion/cb_random · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0917 | [-0.1687, -0.0146] |
| probability versus fm_direct | +0.1365 | [+0.0686, +0.2045] |
| residual versus fm_direct | -0.0011 | [-0.1057, +0.1034] |
| sc_local versus fm_direct | -0.1646 | [-0.2739, -0.0553] |
| common_linear versus local_direct | -0.0906 | [-0.1801, -0.0010] |
| probability versus local_direct | +0.1377 | [+0.0965, +0.1788] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1635 | [-0.2084, -0.1186] |
| common_linear versus strong_single | -0.0855 | [-0.2238, +0.0528] |
| probability versus strong_single | +0.1427 | [+0.0215, +0.2640] |
| residual versus strong_single | +0.0051 | [-0.1402, +0.1503] |
| sc_local versus strong_single | -0.1584 | [-0.3117, -0.0052] |

## fusion/reve_pre · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.5453 | [-0.6604, -0.4302] |
| probability versus fm_direct | +0.2729 | [+0.1596, +0.3862] |
| residual versus fm_direct | -0.0178 | [-0.2582, +0.2225] |
| sc_local versus fm_direct | -0.5390 | [-0.7108, -0.3672] |
| common_linear versus local_direct | -0.5275 | [-0.7974, -0.2576] |
| probability versus local_direct | +0.2907 | [+0.1545, +0.4269] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5212 | [-0.6934, -0.3489] |
| common_linear versus strong_single | -0.7349 | [-0.9242, -0.5455] |
| probability versus strong_single | +0.0833 | [+0.0016, +0.1651] |
| residual versus strong_single | -0.2074 | [-0.3772, -0.0375] |
| sc_local versus strong_single | -0.7286 | [-0.8866, -0.5705] |

## fusion/reve_pre · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0339 | [-0.1622, +0.0944] |
| probability versus fm_direct | +0.2413 | [+0.1569, +0.3258] |
| residual versus fm_direct | +0.1071 | [-0.0812, +0.2953] |
| sc_local versus fm_direct | -0.0564 | [-0.2617, +0.1489] |
| common_linear versus local_direct | -0.1410 | [-0.3209, +0.0390] |
| probability versus local_direct | +0.1343 | [+0.0248, +0.2438] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1635 | [-0.2111, -0.1159] |
| common_linear versus strong_single | -0.1359 | [-0.2732, +0.0015] |
| probability versus strong_single | +0.1394 | [+0.0631, +0.2156] |
| residual versus strong_single | +0.0051 | [-0.1489, +0.1591] |
| sc_local versus strong_single | -0.1584 | [-0.3209, +0.0040] |

## policy/cbramod/pretrained_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| declared_window_temporal|0.3 versus base | +0.0023 | [-0.0152, +0.0197] |
| diagonal_spatial|0.1 versus base | +0.0035 | [-0.0053, +0.0124] |
| diagonal_spatial|0.3 versus base | +0.0305 | [-0.0141, +0.0751] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.3 versus base | +0.0008 | [-0.0515, +0.0531] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0405 | [-0.0520, +0.1330] |
| output_low_rank|0.3 versus base | +0.0947 | [-0.0253, +0.2147] |

## policy/cbramod/pretrained_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| declared_window_temporal|0.3 versus base | +0.0003 | [-0.0085, +0.0091] |
| diagonal_spatial|0.1 versus base | +0.0019 | [-0.0049, +0.0088] |
| diagonal_spatial|0.3 versus base | +0.0284 | [-0.0125, +0.0693] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.3 versus base | +0.0036 | [-0.0342, +0.0414] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0745 | [-0.0230, +0.1720] |
| output_low_rank|0.3 versus base | +0.1223 | [+0.0090, +0.2356] |

## policy/cbramod/random_full · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| declared_window_temporal|0.3 versus base | +0.0376 | [-0.0108, +0.0860] |
| diagonal_spatial|0.1 versus base | +0.0205 | [-0.0438, +0.0848] |
| diagonal_spatial|0.3 versus base | +0.0073 | [-0.0436, +0.0581] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0074 | [-0.0436, +0.0288] |
| lowrank_spatial|0.3 versus base | +0.0039 | [-0.0454, +0.0532] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0472 | [-0.0581, +0.1525] |
| output_low_rank|0.3 versus base | +0.1293 | [-0.0381, +0.2967] |

## policy/cbramod/random_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| declared_window_temporal|0.3 versus base | +0.0040 | [-0.0135, +0.0215] |
| diagonal_spatial|0.1 versus base | +0.0047 | [-0.0488, +0.0583] |
| diagonal_spatial|0.3 versus base | +0.0073 | [-0.0366, +0.0512] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0055 | [-0.0315, +0.0205] |
| lowrank_spatial|0.3 versus base | +0.0038 | [-0.0330, +0.0405] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0407 | [-0.0164, +0.0977] |
| output_low_rank|0.3 versus base | +0.0660 | [-0.0493, +0.1813] |

