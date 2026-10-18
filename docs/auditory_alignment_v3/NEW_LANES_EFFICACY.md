# ALN3.4 new-lane efficacy snapshot

Generated 2026-10-18T19:44:00.471800+02:00 by CPU job 1045980. Status: **interim**.

Complete identity pairing is required; seeds and folds do not increase n. Intervals condition on fitted models. Interim snapshots are not sequential significance tests. `historical_selected` tables reuse existing baseline records; they are not new budget results and do not replace the frozen ADDENDUM_11 analysis.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| learning_budget_v2 | 26 / 150 | 0 |
| data_inner_v1 | 197 / 590 | 0 |
| adaptation_policy_v1 | 31 / 120 | 0 |
| strong_fusion_v1 | 20 / 30 | 0 |
| episode_training_v1 | 19 / 80 | 0 |

Positive values mean lower true query NLL than the named reference. Native and unified are distinct families. All group summaries and coverage are in `results/auditory_alignment_v3/aln34/new_lanes/efficacy.json`.

## budget/cbramod/pretrained_full · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1488 | [-0.2035, -0.0941] |
| fixed_0.25 versus historical_selected | -0.2962 | [-0.4018, -0.1905] |
| fixed_0.5 versus historical_selected | -0.0834 | [-0.1372, -0.0296] |
| fixed_1.0 versus historical_selected | -0.1216 | [-0.1711, -0.0721] |
| fixed_2.0 versus historical_selected | -0.2703 | [-0.3369, -0.2038] |
| new_selected versus historical_selected | -0.2242 | [-0.2840, -0.1644] |

## budget/cbramod/pretrained_full · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0771 | [-0.1224, -0.0318] |
| fixed_0.25 versus historical_selected | -0.1419 | [-0.1982, -0.0856] |
| fixed_0.5 versus historical_selected | -0.0168 | [-0.0550, +0.0213] |
| fixed_1.0 versus historical_selected | -0.0893 | [-0.1335, -0.0451] |
| fixed_2.0 versus historical_selected | -0.1664 | [-0.2037, -0.1291] |
| new_selected versus historical_selected | -0.1393 | [-0.1768, -0.1018] |

## budget/cbramod/random_full · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1754 | [-0.2330, -0.1178] |
| fixed_0.25 versus historical_selected | -0.3382 | [-0.4379, -0.2385] |
| fixed_0.5 versus historical_selected | -0.0736 | [-0.1196, -0.0276] |
| fixed_1.0 versus historical_selected | -0.1220 | [-0.1907, -0.0532] |
| fixed_2.0 versus historical_selected | -0.2974 | [-0.3904, -0.2045] |
| new_selected versus historical_selected | -0.2309 | [-0.3178, -0.1439] |

## budget/cbramod/random_full · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1701 | [-0.2098, -0.1304] |
| fixed_0.25 versus historical_selected | -0.1682 | [-0.2170, -0.1193] |
| fixed_0.5 versus historical_selected | -0.0034 | [-0.0478, +0.0409] |
| fixed_1.0 versus historical_selected | -0.0754 | [-0.1171, -0.0337] |
| fixed_2.0 versus historical_selected | -0.2455 | [-0.2980, -0.1929] |
| new_selected versus historical_selected | -0.1770 | [-0.2272, -0.1269] |

## budget/local · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0577 | [-0.0981, -0.0172] |
| fixed_0.25 versus historical_selected | -0.0779 | [-0.1471, -0.0087] |
| fixed_0.5 versus historical_selected | -0.0266 | [-0.0836, +0.0304] |
| fixed_1.0 versus historical_selected | -0.0511 | [-0.0993, -0.0029] |
| fixed_2.0 versus historical_selected | -0.1088 | [-0.1605, -0.0571] |
| new_selected versus historical_selected | -0.0773 | [-0.1273, -0.0273] |

## budget/local · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0423 | [-0.0701, -0.0144] |
| fixed_0.25 versus historical_selected | +0.0033 | [-0.0307, +0.0374] |
| fixed_0.5 versus historical_selected | +0.0023 | [-0.0264, +0.0311] |
| fixed_1.0 versus historical_selected | -0.0487 | [-0.0874, -0.0101] |
| fixed_2.0 versus historical_selected | -0.0910 | [-0.1320, -0.0500] |
| new_selected versus historical_selected | -0.0749 | [-0.1167, -0.0331] |

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

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6951 | [-0.8283, -0.5619] |
| 0.5 versus full | -0.4716 | [-0.5840, -0.3591] |

## data/content/cbramod/pretrained_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2673 | [-0.3609, -0.1737] |
| 0.5 versus full | -0.0751 | [-0.1334, -0.0168] |

## data/content/cbramod/random_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7306 | [-0.8855, -0.5757] |
| 0.5 versus full | -0.4997 | [-0.6086, -0.3909] |

## data/content/cbramod/random_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4627 | [-0.5703, -0.3551] |
| 0.5 versus full | -0.3064 | [-0.3737, -0.2390] |

## data/content/local · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6383 | [-0.8333, -0.4433] |
| 0.5 versus full | -0.3874 | [-0.5255, -0.2494] |

## data/content/local · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3260 | [-0.4062, -0.2458] |
| 0.5 versus full | -0.2627 | [-0.3177, -0.2076] |

## data/content/reve/pretrained_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6604 | [-0.8089, -0.5119] |
| 0.5 versus full | -0.5179 | [-0.6281, -0.4077] |

## data/content/reve/pretrained_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2478 | [-0.3682, -0.1274] |
| 0.5 versus full | -0.1356 | [-0.2202, -0.0510] |

## data/content/reve/random_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4922 | [-0.6488, -0.3355] |
| 0.5 versus full | -0.3108 | [-0.4368, -0.1847] |

## data/content/reve/random_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3297 | [-0.4042, -0.2552] |
| 0.5 versus full | -0.2121 | [-0.2844, -0.1399] |

## data/people/cbramod/pretrained_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7466 | [-0.9213, -0.5719] |
| 0.5 versus full | -0.3832 | [-0.4911, -0.2753] |

## data/people/cbramod/pretrained_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5800 | [-0.7413, -0.4186] |
| 0.5 versus full | -0.1952 | [-0.3090, -0.0814] |

## data/people/cbramod/random_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7473 | [-0.9060, -0.5887] |
| 0.5 versus full | -0.4040 | [-0.5047, -0.3034] |

## data/people/cbramod/random_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4875 | [-0.6016, -0.3734] |
| 0.5 versus full | -0.2982 | [-0.4121, -0.1844] |

## data/people/local · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.6931 | [-0.8619, -0.5244] |
| 0.5 versus full | -0.2901 | [-0.4091, -0.1710] |

## data/people/local · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5457 | [-0.6854, -0.4060] |
| 0.5 versus full | -0.1930 | [-0.2658, -0.1201] |

## data/people/reve/pretrained_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.7234 | [-0.8824, -0.5643] |
| 0.5 versus full | -0.4593 | [-0.5617, -0.3568] |

## data/people/reve/pretrained_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5205 | [-0.6463, -0.3946] |
| 0.5 versus full | -0.2768 | [-0.3717, -0.1818] |

## data/people/reve/random_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.4828 | [-0.6587, -0.3069] |
| 0.5 versus full | -0.2374 | [-0.3375, -0.1373] |

## data/people/reve/random_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.5235 | [-0.6866, -0.3603] |
| 0.5 versus full | -0.2388 | [-0.3277, -0.1499] |

## data_models/content/0.25 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3314 | [+0.2242, +0.4386] |
| cbramod/pretrained_full versus local | +0.2376 | [+0.0821, +0.3930] |
| cbramod/random_full versus local | -0.0939 | [-0.2553, +0.0676] |
| reve/pretrained_full versus local | -0.0043 | [-0.1718, +0.1632] |
| reve/random_full versus local | +0.0106 | [-0.1373, +0.1585] |
| reve/pretrained_full versus reve/random_full | -0.0149 | [-0.1498, +0.1200] |

## data_models/content/0.25 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.2791 | [+0.1621, +0.3960] |
| cbramod/pretrained_full versus local | +0.1435 | [+0.0351, +0.2519] |
| cbramod/random_full versus local | -0.1356 | [-0.2322, -0.0390] |
| reve/pretrained_full versus local | -0.0289 | [-0.1120, +0.0542] |
| reve/random_full versus local | -0.0169 | [-0.1241, +0.0904] |
| reve/pretrained_full versus reve/random_full | -0.0120 | [-0.1178, +0.0937] |

## data_models/content/0.5 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3241 | [+0.2112, +0.4370] |
| cbramod/pretrained_full versus local | +0.2102 | [+0.0395, +0.3809] |
| cbramod/random_full versus local | -0.1139 | [-0.2757, +0.0480] |
| reve/pretrained_full versus local | -0.1126 | [-0.2926, +0.0674] |
| reve/random_full versus local | -0.0589 | [-0.2252, +0.1075] |
| reve/pretrained_full versus reve/random_full | -0.0538 | [-0.2152, +0.1076] |

## data_models/content/0.5 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3150 | [+0.2099, +0.4200] |
| cbramod/pretrained_full versus local | +0.2724 | [+0.1402, +0.4045] |
| cbramod/random_full versus local | -0.0426 | [-0.1626, +0.0774] |
| reve/pretrained_full versus local | +0.0200 | [-0.0979, +0.1379] |
| reve/random_full versus local | +0.0374 | [-0.0787, +0.1535] |
| reve/pretrained_full versus reve/random_full | -0.0174 | [-0.1217, +0.0869] |

## data_models/people/0.25 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.2967 | [+0.1357, +0.4577] |
| cbramod/pretrained_full versus local | +0.2409 | [+0.0450, +0.4368] |
| cbramod/random_full versus local | -0.0558 | [-0.2714, +0.1598] |
| reve/pretrained_full versus local | -0.0124 | [-0.2127, +0.1879] |
| reve/random_full versus local | +0.0748 | [-0.1943, +0.3439] |
| reve/pretrained_full versus reve/random_full | -0.0872 | [-0.3332, +0.1589] |

## data_models/people/0.25 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | -0.0088 | [-0.1796, +0.1619] |
| cbramod/pretrained_full versus local | +0.0505 | [-0.0901, +0.1912] |
| cbramod/random_full versus local | +0.0594 | [-0.0970, +0.2158] |
| reve/pretrained_full versus local | -0.0818 | [-0.2346, +0.0709] |
| reve/random_full versus local | +0.0091 | [-0.1639, +0.1822] |
| reve/pretrained_full versus reve/random_full | -0.0910 | [-0.2362, +0.0543] |

## data_models/people/0.5 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3168 | [+0.1888, +0.4448] |
| cbramod/pretrained_full versus local | +0.2012 | [-0.0405, +0.4429] |
| cbramod/random_full versus local | -0.1156 | [-0.3182, +0.0870] |
| reve/pretrained_full versus local | -0.1514 | [-0.3403, +0.0375] |
| reve/random_full versus local | -0.0829 | [-0.2881, +0.1223] |
| reve/pretrained_full versus reve/random_full | -0.0685 | [-0.2456, +0.1086] |

## data_models/people/0.5 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1867 | [+0.0910, +0.2825] |
| cbramod/pretrained_full versus local | +0.0826 | [-0.0861, +0.2513] |
| cbramod/random_full versus local | -0.1041 | [-0.2329, +0.0246] |
| reve/pretrained_full versus local | -0.1909 | [-0.3535, -0.0282] |
| reve/random_full versus local | -0.0589 | [-0.1805, +0.0627] |
| reve/pretrained_full versus reve/random_full | -0.1319 | [-0.2841, +0.0202] |

## episode/cbramod/pretrained_full/support_0.1 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0002, +0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0002, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0063 | [-0.0171, +0.0046] |
| fixed_episode/0 versus source_no_adaptation | -0.0132 | [-0.0318, +0.0054] |
| fixed_episode/20 versus source_no_adaptation | -0.0112 | [-0.0469, +0.0245] |
| fixed_episode/5 versus source_no_adaptation | -0.0113 | [-0.0292, +0.0066] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0131 | [-0.0317, +0.0055] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0111 | [-0.0468, +0.0245] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0112 | [-0.0291, +0.0067] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | -0.0022 | [-0.0383, +0.0340] |
| fixed_source/5 versus source_no_adaptation | +0.0018 | [-0.0001, +0.0036] |
| ordinary_selected versus source_no_adaptation | -0.0062 | [-0.0170, +0.0045] |

## episode/cbramod/pretrained_full/support_0.1 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0016 | [-0.0115, +0.0082] |
| fixed_episode/0 versus source_no_adaptation | -0.0077 | [-0.0244, +0.0090] |
| fixed_episode/20 versus source_no_adaptation | -0.0076 | [-0.0473, +0.0321] |
| fixed_episode/5 versus source_no_adaptation | -0.0065 | [-0.0231, +0.0100] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0077 | [-0.0244, +0.0090] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0076 | [-0.0473, +0.0321] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0065 | [-0.0231, +0.0100] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0004 | [-0.0360, +0.0369] |
| fixed_source/5 versus source_no_adaptation | +0.0012 | [-0.0002, +0.0026] |
| ordinary_selected versus source_no_adaptation | -0.0016 | [-0.0115, +0.0082] |

## episode/cbramod/pretrained_full/support_0.3 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0001 | [-0.0002, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0002, -0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0037 | [-0.0240, +0.0165] |
| fixed_episode/0 versus source_no_adaptation | -0.0132 | [-0.0309, +0.0045] |
| fixed_episode/20 versus source_no_adaptation | +0.0096 | [-0.0314, +0.0506] |
| fixed_episode/5 versus source_no_adaptation | -0.0099 | [-0.0276, +0.0077] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0131 | [-0.0308, +0.0046] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0097 | [-0.0313, +0.0507] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0099 | [-0.0275, +0.0077] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0203 | [-0.0154, +0.0559] |
| fixed_source/5 versus source_no_adaptation | +0.0031 | [+0.0010, +0.0052] |
| ordinary_selected versus source_no_adaptation | -0.0037 | [-0.0239, +0.0165] |

## episode/cbramod/pretrained_full/support_0.3 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0001, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0010 | [-0.0220, +0.0240] |
| fixed_episode/0 versus source_no_adaptation | -0.0077 | [-0.0250, +0.0095] |
| fixed_episode/20 versus source_no_adaptation | +0.0083 | [-0.0311, +0.0478] |
| fixed_episode/5 versus source_no_adaptation | -0.0056 | [-0.0229, +0.0117] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0077 | [-0.0250, +0.0095] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0083 | [-0.0312, +0.0478] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0056 | [-0.0229, +0.0117] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0159 | [-0.0173, +0.0491] |
| fixed_source/5 versus source_no_adaptation | +0.0021 | [+0.0005, +0.0037] |
| ordinary_selected versus source_no_adaptation | +0.0010 | [-0.0220, +0.0239] |

## episode/cbramod/random_full/support_0.1 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0099 | [-0.0364, +0.0563] |
| fixed_episode/0 versus source_no_adaptation | +0.0124 | [-0.0344, +0.0591] |
| fixed_episode/20 versus source_no_adaptation | +0.0220 | [-0.0372, +0.0811] |
| fixed_episode/5 versus source_no_adaptation | +0.0137 | [-0.0333, +0.0606] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0124 | [-0.0344, +0.0592] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0220 | [-0.0371, +0.0811] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0137 | [-0.0332, +0.0607] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0080 | [-0.0244, +0.0403] |
| fixed_source/5 versus source_no_adaptation | +0.0014 | [-0.0002, +0.0029] |
| ordinary_selected versus source_no_adaptation | +0.0099 | [-0.0364, +0.0563] |

## episode/cbramod/random_full/support_0.1 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0149 | [-0.0330, +0.0033] |
| fixed_episode/0 versus source_no_adaptation | -0.0073 | [-0.0187, +0.0041] |
| fixed_episode/20 versus source_no_adaptation | -0.0028 | [-0.0169, +0.0112] |
| fixed_episode/5 versus source_no_adaptation | -0.0067 | [-0.0175, +0.0042] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0073 | [-0.0187, +0.0041] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0028 | [-0.0169, +0.0112] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0067 | [-0.0175, +0.0042] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0030 | [-0.0152, +0.0212] |
| fixed_source/5 versus source_no_adaptation | +0.0005 | [-0.0003, +0.0014] |
| ordinary_selected versus source_no_adaptation | -0.0149 | [-0.0330, +0.0033] |

## episode/cbramod/random_full/support_0.3 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0327 | [-0.0194, +0.0849] |
| fixed_episode/0 versus source_no_adaptation | +0.0124 | [-0.0361, +0.0608] |
| fixed_episode/20 versus source_no_adaptation | +0.0546 | [-0.0202, +0.1295] |
| fixed_episode/5 versus source_no_adaptation | +0.0159 | [-0.0337, +0.0655] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0124 | [-0.0360, +0.0608] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0547 | [-0.0202, +0.1295] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0160 | [-0.0336, +0.0656] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0430 | [+0.0039, +0.0822] |
| fixed_source/5 versus source_no_adaptation | +0.0038 | [+0.0016, +0.0059] |
| ordinary_selected versus source_no_adaptation | +0.0327 | [-0.0194, +0.0849] |

## episode/cbramod/random_full/support_0.3 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0013 | [-0.0213, +0.0238] |
| fixed_episode/0 versus source_no_adaptation | -0.0073 | [-0.0194, +0.0048] |
| fixed_episode/20 versus source_no_adaptation | +0.0156 | [-0.0072, +0.0383] |
| fixed_episode/5 versus source_no_adaptation | -0.0054 | [-0.0172, +0.0063] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0073 | [-0.0193, +0.0048] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0156 | [-0.0071, +0.0383] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0054 | [-0.0172, +0.0063] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0234 | [+0.0018, +0.0450] |
| fixed_source/5 versus source_no_adaptation | +0.0019 | [+0.0008, +0.0030] |
| ordinary_selected versus source_no_adaptation | +0.0013 | [-0.0213, +0.0238] |

## episode/local/support_0.1 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0004, +0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0005, -0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0004, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0071 | [-0.0448, +0.0305] |
| fixed_episode/0 versus source_no_adaptation | +0.0084 | [-0.0151, +0.0319] |
| fixed_episode/20 versus source_no_adaptation | +0.0062 | [-0.0834, +0.0957] |
| fixed_episode/5 versus source_no_adaptation | +0.0119 | [-0.0115, +0.0354] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0085 | [-0.0149, +0.0319] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0064 | [-0.0831, +0.0959] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0121 | [-0.0113, +0.0355] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | -0.0024 | [-0.0889, +0.0841] |
| fixed_source/5 versus source_no_adaptation | +0.0036 | [-0.0001, +0.0072] |
| ordinary_selected versus source_no_adaptation | -0.0071 | [-0.0448, +0.0305] |

## episode/local/support_0.1 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0002, +0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0004, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0002, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0038 | [-0.0252, +0.0176] |
| fixed_episode/0 versus source_no_adaptation | +0.0006 | [-0.0130, +0.0143] |
| fixed_episode/20 versus source_no_adaptation | -0.0123 | [-0.0700, +0.0454] |
| fixed_episode/5 versus source_no_adaptation | +0.0020 | [-0.0114, +0.0154] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0007 | [-0.0129, +0.0143] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0121 | [-0.0698, +0.0455] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0021 | [-0.0113, +0.0155] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | -0.0114 | [-0.0673, +0.0444] |
| fixed_source/5 versus source_no_adaptation | +0.0015 | [-0.0008, +0.0038] |
| ordinary_selected versus source_no_adaptation | -0.0038 | [-0.0252, +0.0176] |

## episode/local/support_0.3 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0004, +0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0006, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0004, +0.0002] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0517 | [-0.0145, +0.1179] |
| fixed_episode/0 versus source_no_adaptation | +0.0084 | [-0.0160, +0.0328] |
| fixed_episode/20 versus source_no_adaptation | +0.0900 | [-0.0008, +0.1809] |
| fixed_episode/5 versus source_no_adaptation | +0.0160 | [-0.0091, +0.0412] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0085 | [-0.0158, +0.0328] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0903 | [-0.0005, +0.1810] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0162 | [-0.0090, +0.0413] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0813 | [-0.0040, +0.1667] |
| fixed_source/5 versus source_no_adaptation | +0.0079 | [+0.0034, +0.0124] |
| ordinary_selected versus source_no_adaptation | +0.0517 | [-0.0145, +0.1179] |

## episode/local/support_0.3 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0003, +0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0001 | [-0.0004, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0002, +0.0002] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0298 | [-0.0137, +0.0733] |
| fixed_episode/0 versus source_no_adaptation | +0.0006 | [-0.0133, +0.0145] |
| fixed_episode/20 versus source_no_adaptation | +0.0441 | [-0.0123, +0.1005] |
| fixed_episode/5 versus source_no_adaptation | +0.0047 | [-0.0104, +0.0197] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0007 | [-0.0132, +0.0145] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0442 | [-0.0121, +0.1005] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0047 | [-0.0103, +0.0197] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0427 | [-0.0110, +0.0964] |
| fixed_source/5 versus source_no_adaptation | +0.0041 | [+0.0013, +0.0070] |
| ordinary_selected versus source_no_adaptation | +0.0298 | [-0.0137, +0.0733] |

## episode/reve/pretrained_full/support_0.1 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0011, +0.0011] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0002 | [-0.0022, +0.0027] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0009, +0.0010] |
| episode_selected versus ordinary_selected | -0.0023 | [-0.0075, +0.0028] |
| episode_selected versus source_no_adaptation | -0.0047 | [-0.0237, +0.0143] |
| fixed_episode/0 versus source_no_adaptation | -0.0034 | [-0.0220, +0.0152] |
| fixed_episode/20 versus source_no_adaptation | +0.0055 | [-0.0393, +0.0503] |
| fixed_episode/5 versus source_no_adaptation | -0.0018 | [-0.0205, +0.0168] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0034 | [-0.0219, +0.0150] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0053 | [-0.0398, +0.0503] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0019 | [-0.0203, +0.0166] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0102 | [-0.0311, +0.0514] |
| fixed_source/5 versus source_no_adaptation | +0.0017 | [-0.0010, +0.0043] |
| ordinary_selected versus source_no_adaptation | -0.0024 | [-0.0196, +0.0149] |

## episode/reve/pretrained_full/support_0.1 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0002 | [-0.0009, +0.0013] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0006 | [-0.0023, +0.0034] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0002 | [-0.0008, +0.0012] |
| episode_selected versus ordinary_selected | -0.0002 | [-0.0052, +0.0048] |
| episode_selected versus source_no_adaptation | -0.0021 | [-0.0202, +0.0159] |
| fixed_episode/0 versus source_no_adaptation | +0.0001 | [-0.0149, +0.0152] |
| fixed_episode/20 versus source_no_adaptation | +0.0095 | [-0.0359, +0.0549] |
| fixed_episode/5 versus source_no_adaptation | +0.0013 | [-0.0143, +0.0168] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0000 | [-0.0149, +0.0148] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0089 | [-0.0372, +0.0550] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0011 | [-0.0142, +0.0163] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0092 | [-0.0307, +0.0491] |
| fixed_source/5 versus source_no_adaptation | +0.0012 | [-0.0018, +0.0041] |
| ordinary_selected versus source_no_adaptation | -0.0020 | [-0.0185, +0.0146] |

## episode/reve/pretrained_full/support_0.3 · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0011, +0.0011] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0003 | [-0.0052, +0.0046] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0001 | [-0.0010, +0.0011] |
| episode_selected versus ordinary_selected | +0.0026 | [-0.0010, +0.0063] |
| episode_selected versus source_no_adaptation | +0.0134 | [-0.0177, +0.0446] |
| fixed_episode/0 versus source_no_adaptation | -0.0034 | [-0.0225, +0.0157] |
| fixed_episode/20 versus source_no_adaptation | +0.0127 | [-0.0415, +0.0668] |
| fixed_episode/5 versus source_no_adaptation | -0.0008 | [-0.0209, +0.0193] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0034 | [-0.0224, +0.0155] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0130 | [-0.0400, +0.0659] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0008 | [-0.0205, +0.0188] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0177 | [-0.0284, +0.0639] |
| fixed_source/5 versus source_no_adaptation | +0.0026 | [-0.0001, +0.0054] |
| ordinary_selected versus source_no_adaptation | +0.0108 | [-0.0220, +0.0436] |

## episode/reve/pretrained_full/support_0.3 · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0002 | [-0.0010, +0.0014] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0006 | [-0.0047, +0.0034] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0002 | [-0.0010, +0.0013] |
| episode_selected versus ordinary_selected | +0.0004 | [-0.0029, +0.0037] |
| episode_selected versus source_no_adaptation | +0.0150 | [-0.0224, +0.0524] |
| fixed_episode/0 versus source_no_adaptation | +0.0001 | [-0.0159, +0.0161] |
| fixed_episode/20 versus source_no_adaptation | +0.0161 | [-0.0487, +0.0810] |
| fixed_episode/5 versus source_no_adaptation | +0.0020 | [-0.0157, +0.0198] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0000 | [-0.0158, +0.0157] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0168 | [-0.0463, +0.0799] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0018 | [-0.0154, +0.0190] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0167 | [-0.0376, +0.0709] |
| fixed_source/5 versus source_no_adaptation | +0.0018 | [-0.0015, +0.0052] |
| ordinary_selected versus source_no_adaptation | +0.0146 | [-0.0232, +0.0524] |

## fusion/cb_pre · native · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.9030 | [-1.0557, -0.7502] |
| probability versus fm_direct | +0.0535 | [+0.0277, +0.0793] |
| residual versus fm_direct | -0.3774 | [-0.4823, -0.2724] |
| sc_local versus fm_direct | -1.0710 | [-1.2539, -0.8880] |
| common_linear versus local_direct | -0.5256 | [-0.6663, -0.3850] |
| probability versus local_direct | +0.4309 | [+0.3471, +0.5147] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6936 | [-0.8392, -0.5480] |
| common_linear versus strong_single | -0.8238 | [-0.9768, -0.6709] |
| probability versus strong_single | +0.1327 | [+0.0729, +0.1924] |
| residual versus strong_single | -0.2982 | [-0.4151, -0.1814] |
| sc_local versus strong_single | -0.9918 | [-1.1778, -0.8058] |

## fusion/cb_pre · native · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.8846 | [-1.0379, -0.7314] |
| probability versus fm_direct | +0.0487 | [+0.0109, +0.0864] |
| residual versus fm_direct | -0.4263 | [-0.5559, -0.2966] |
| sc_local versus fm_direct | -1.0594 | [-1.2653, -0.8534] |
| common_linear versus local_direct | -0.4583 | [-0.5935, -0.3232] |
| probability versus local_direct | +0.4749 | [+0.3740, +0.5758] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6331 | [-0.7848, -0.4814] |
| common_linear versus strong_single | -0.7771 | [-0.9270, -0.6271] |
| probability versus strong_single | +0.1562 | [+0.1107, +0.2017] |
| residual versus strong_single | -0.3187 | [-0.4423, -0.1952] |
| sc_local versus strong_single | -0.9518 | [-1.1509, -0.7527] |

## fusion/cb_pre · unified · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1895 | [-0.2565, -0.1224] |
| probability versus fm_direct | +0.0553 | [+0.0262, +0.0845] |
| residual versus fm_direct | -0.2132 | [-0.3009, -0.1256] |
| sc_local versus fm_direct | -0.3649 | [-0.4591, -0.2707] |
| common_linear versus local_direct | +0.0238 | [-0.0455, +0.0930] |
| probability versus local_direct | +0.2685 | [+0.2058, +0.3313] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1517 | [-0.2040, -0.0994] |
| common_linear versus strong_single | -0.1119 | [-0.1982, -0.0256] |
| probability versus strong_single | +0.1329 | [+0.0684, +0.1973] |
| residual versus strong_single | -0.1357 | [-0.2469, -0.0244] |
| sc_local versus strong_single | -0.2873 | [-0.4043, -0.1704] |

## fusion/cb_pre · unified · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2054 | [-0.2704, -0.1404] |
| probability versus fm_direct | +0.0200 | [-0.0188, +0.0588] |
| residual versus fm_direct | -0.2293 | [-0.3354, -0.1233] |
| sc_local versus fm_direct | -0.3749 | [-0.4930, -0.2567] |
| common_linear versus local_direct | +0.0239 | [-0.0456, +0.0935] |
| probability versus local_direct | +0.2493 | [+0.1724, +0.3262] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1455 | [-0.1966, -0.0944] |
| common_linear versus strong_single | -0.1604 | [-0.2188, -0.1020] |
| probability versus strong_single | +0.0650 | [+0.0314, +0.0985] |
| residual versus strong_single | -0.1843 | [-0.2784, -0.0903] |
| sc_local versus strong_single | -0.3299 | [-0.4331, -0.2266] |

## fusion/cb_random · native · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.4909 | [-0.6006, -0.3812] |
| probability versus fm_direct | +0.2174 | [+0.1174, +0.3175] |
| residual versus fm_direct | +0.0887 | [-0.0360, +0.2133] |
| sc_local versus fm_direct | -0.6049 | [-0.7295, -0.4803] |
| common_linear versus local_direct | -0.5796 | [-0.7397, -0.4195] |
| probability versus local_direct | +0.1287 | [+0.0884, +0.1691] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6936 | [-0.8369, -0.5503] |
| common_linear versus strong_single | -0.8778 | [-1.0605, -0.6952] |
| probability versus strong_single | -0.1695 | [-0.2867, -0.0523] |
| residual versus strong_single | -0.2982 | [-0.4133, -0.1832] |
| sc_local versus strong_single | -0.9918 | [-1.1749, -0.8087] |

## fusion/cb_random · native · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.6132 | [-0.7434, -0.4831] |
| probability versus fm_direct | +0.1605 | [+0.0820, +0.2390] |
| residual versus fm_direct | -0.0887 | [-0.2240, +0.0466] |
| sc_local versus fm_direct | -0.7218 | [-0.8980, -0.5455] |
| common_linear versus local_direct | -0.5246 | [-0.6560, -0.3931] |
| probability versus local_direct | +0.2492 | [+0.1861, +0.3122] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6331 | [-0.7857, -0.4804] |
| common_linear versus strong_single | -0.8433 | [-1.0050, -0.6816] |
| probability versus strong_single | -0.0696 | [-0.1654, +0.0263] |
| residual versus strong_single | -0.3187 | [-0.4430, -0.1944] |
| sc_local versus strong_single | -0.9518 | [-1.1521, -0.7515] |

## fusion/cb_random · unified · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0844 | [-0.1345, -0.0342] |
| probability versus fm_direct | +0.1424 | [+0.0822, +0.2026] |
| residual versus fm_direct | +0.0181 | [-0.0705, +0.1068] |
| sc_local versus fm_direct | -0.1336 | [-0.2172, -0.0499] |
| common_linear versus local_direct | -0.1025 | [-0.1787, -0.0262] |
| probability versus local_direct | +0.1243 | [+0.0933, +0.1553] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1517 | [-0.2021, -0.1012] |
| common_linear versus strong_single | -0.2381 | [-0.3462, -0.1301] |
| probability versus strong_single | -0.0114 | [-0.1092, +0.0864] |
| residual versus strong_single | -0.1357 | [-0.2430, -0.0283] |
| sc_local versus strong_single | -0.2873 | [-0.4002, -0.1745] |

## fusion/cb_random · unified · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1169 | [-0.1775, -0.0563] |
| probability versus fm_direct | +0.0993 | [+0.0390, +0.1595] |
| residual versus fm_direct | -0.0571 | [-0.1598, +0.0456] |
| sc_local versus fm_direct | -0.2026 | [-0.3033, -0.1019] |
| common_linear versus local_direct | -0.0599 | [-0.1243, +0.0046] |
| probability versus local_direct | +0.1563 | [+0.1096, +0.2030] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1455 | [-0.1972, -0.0938] |
| common_linear versus strong_single | -0.2442 | [-0.3254, -0.1630] |
| probability versus strong_single | -0.0280 | [-0.0982, +0.0422] |
| residual versus strong_single | -0.1843 | [-0.2795, -0.0892] |
| sc_local versus strong_single | -0.3299 | [-0.4343, -0.2254] |

## fusion/reve_pre · native · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.6453 | [-0.7619, -0.5288] |
| probability versus fm_direct | +0.2224 | [+0.1588, +0.2860] |
| residual versus fm_direct | -0.0671 | [-0.1991, +0.0648] |
| sc_local versus fm_direct | -0.7607 | [-0.9274, -0.5940] |
| common_linear versus local_direct | -0.5782 | [-0.7491, -0.4073] |
| probability versus local_direct | +0.2896 | [+0.2140, +0.3652] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6936 | [-0.8421, -0.5451] |
| common_linear versus strong_single | -0.8764 | [-1.0365, -0.7164] |
| probability versus strong_single | -0.0087 | [-0.0852, +0.0679] |
| residual versus strong_single | -0.2982 | [-0.4174, -0.1790] |
| sc_local versus strong_single | -0.9918 | [-1.1815, -0.8021] |

## fusion/reve_pre · native · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.5542 | [-0.6703, -0.4381] |
| probability versus fm_direct | +0.2492 | [+0.1939, +0.3045] |
| residual versus fm_direct | -0.0666 | [-0.1872, +0.0540] |
| sc_local versus fm_direct | -0.6997 | [-0.8679, -0.5315] |
| common_linear versus local_direct | -0.4876 | [-0.6398, -0.3353] |
| probability versus local_direct | +0.3158 | [+0.2433, +0.3883] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.6331 | [-0.7837, -0.4824] |
| common_linear versus strong_single | -0.8063 | [-0.9743, -0.6383] |
| probability versus strong_single | -0.0029 | [-0.0945, +0.0887] |
| residual versus strong_single | -0.3187 | [-0.4414, -0.1960] |
| sc_local versus strong_single | -0.9518 | [-1.1495, -0.7541] |

## fusion/reve_pre · unified · 3401

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0922 | [-0.1698, -0.0146] |
| probability versus fm_direct | +0.1732 | [+0.1116, +0.2347] |
| residual versus fm_direct | +0.0057 | [-0.1075, +0.1189] |
| sc_local versus fm_direct | -0.1460 | [-0.2662, -0.0257] |
| common_linear versus local_direct | -0.0979 | [-0.2071, +0.0113] |
| probability versus local_direct | +0.1675 | [+0.1093, +0.2256] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1517 | [-0.2022, -0.1012] |
| common_linear versus strong_single | -0.2335 | [-0.3259, -0.1412] |
| probability versus strong_single | +0.0318 | [-0.0383, +0.1020] |
| residual versus strong_single | -0.1357 | [-0.2431, -0.0282] |
| sc_local versus strong_single | -0.2873 | [-0.4002, -0.1744] |

## fusion/reve_pre · unified · 3407

Common paired identities: 44 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1324 | [-0.2197, -0.0451] |
| probability versus fm_direct | +0.1389 | [+0.0836, +0.1942] |
| residual versus fm_direct | -0.0524 | [-0.1531, +0.0484] |
| sc_local versus fm_direct | -0.1979 | [-0.3145, -0.0813] |
| common_linear versus local_direct | -0.0800 | [-0.1709, +0.0108] |
| probability versus local_direct | +0.1912 | [+0.1347, +0.2477] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1455 | [-0.1983, -0.0927] |
| common_linear versus strong_single | -0.2644 | [-0.3624, -0.1664] |
| probability versus strong_single | +0.0069 | [-0.0594, +0.0732] |
| residual versus strong_single | -0.1843 | [-0.2815, -0.0872] |
| sc_local versus strong_single | -0.3299 | [-0.4366, -0.2232] |

## policy/cbramod/pretrained_full · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0060 | [-0.0106, +0.0227] |
| declared_window_temporal|0.3 versus base | +0.0035 | [-0.0181, +0.0251] |
| diagonal_spatial|0.1 versus base | +0.0067 | [-0.0305, +0.0438] |
| diagonal_spatial|0.3 versus base | +0.0265 | [-0.0034, +0.0564] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0102 | [-0.0201, +0.0404] |
| lowrank_spatial|0.3 versus base | +0.0177 | [-0.0155, +0.0509] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0116 | [-0.0333, +0.0565] |
| output_low_rank|0.3 versus base | +0.0604 | [+0.0053, +0.1155] |

## policy/cbramod/pretrained_full · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0024 | [-0.0045, +0.0093] |
| declared_window_temporal|0.3 versus base | +0.0028 | [-0.0071, +0.0128] |
| diagonal_spatial|0.1 versus base | +0.0031 | [-0.0151, +0.0214] |
| diagonal_spatial|0.3 versus base | +0.0158 | [-0.0007, +0.0323] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0032 | [-0.0100, +0.0164] |
| lowrank_spatial|0.3 versus base | +0.0067 | [-0.0107, +0.0242] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0225 | [-0.0262, +0.0711] |
| output_low_rank|0.3 versus base | +0.0593 | [+0.0048, +0.1138] |

## policy/cbramod/random_full · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0059 | [-0.0062, +0.0180] |
| declared_window_temporal|0.3 versus base | +0.0157 | [-0.0006, +0.0320] |
| diagonal_spatial|0.1 versus base | +0.0097 | [-0.0118, +0.0312] |
| diagonal_spatial|0.3 versus base | +0.0159 | [-0.0027, +0.0346] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0011 | [-0.0189, +0.0211] |
| lowrank_spatial|0.3 versus base | +0.0201 | [+0.0007, +0.0394] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0164 | [-0.0185, +0.0513] |
| output_low_rank|0.3 versus base | +0.0488 | [+0.0005, +0.0971] |

## policy/cbramod/random_full · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0013 | [-0.0085, +0.0112] |
| declared_window_temporal|0.3 versus base | -0.0001 | [-0.0088, +0.0087] |
| diagonal_spatial|0.1 versus base | -0.0002 | [-0.0174, +0.0171] |
| diagonal_spatial|0.3 versus base | +0.0077 | [-0.0043, +0.0197] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0009 | [-0.0147, +0.0130] |
| lowrank_spatial|0.3 versus base | +0.0084 | [-0.0065, +0.0234] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0202 | [+0.0005, +0.0399] |
| output_low_rank|0.3 versus base | +0.0259 | [-0.0033, +0.0552] |

## policy/local · native · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0011 | [-0.0231, +0.0252] |
| declared_window_temporal|0.3 versus base | +0.0207 | [+0.0006, +0.0408] |
| diagonal_spatial|0.1 versus base | +0.0174 | [-0.0265, +0.0613] |
| diagonal_spatial|0.3 versus base | +0.0734 | [+0.0240, +0.1229] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0054 | [-0.0442, +0.0334] |
| lowrank_spatial|0.3 versus base | +0.0563 | [-0.0060, +0.1185] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0217 | [-0.0218, +0.0652] |
| output_low_rank|0.3 versus base | +0.0619 | [-0.0071, +0.1310] |

## policy/local · unified · 3401

Common paired identities: 36 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0003 | [-0.0128, +0.0135] |
| declared_window_temporal|0.3 versus base | +0.0093 | [-0.0034, +0.0219] |
| diagonal_spatial|0.1 versus base | +0.0034 | [-0.0204, +0.0272] |
| diagonal_spatial|0.3 versus base | +0.0347 | [+0.0046, +0.0647] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0053 | [-0.0304, +0.0198] |
| lowrank_spatial|0.3 versus base | +0.0274 | [-0.0222, +0.0769] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0225 | [+0.0021, +0.0429] |
| output_low_rank|0.3 versus base | +0.0463 | [+0.0113, +0.0812] |

## policy/reve/pretrained_full · native · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0031 | [-0.0241, +0.0303] |
| declared_window_temporal|0.3 versus base | +0.0300 | [-0.0078, +0.0678] |
| diagonal_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| diagonal_spatial|0.3 versus base | +0.0271 | [-0.0128, +0.0670] |
| full_spatial|0.1 versus base | -0.0065 | [-0.0433, +0.0303] |
| full_spatial|0.3 versus base | +0.0106 | [-0.0550, +0.0762] |
| lowrank_spatial|0.1 versus base | -0.0016 | [-0.0077, +0.0045] |
| lowrank_spatial|0.3 versus base | -0.0121 | [-0.1030, +0.0788] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0254 | [-0.0269, +0.0777] |
| output_low_rank|0.3 versus base | +0.0499 | [-0.0301, +0.1299] |

## policy/reve/pretrained_full · unified · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0055 | [-0.0057, +0.0167] |
| declared_window_temporal|0.3 versus base | +0.0145 | [-0.0005, +0.0295] |
| diagonal_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| diagonal_spatial|0.3 versus base | +0.0209 | [-0.0036, +0.0453] |
| full_spatial|0.1 versus base | -0.0026 | [-0.0151, +0.0099] |
| full_spatial|0.3 versus base | +0.0179 | [-0.0305, +0.0663] |
| lowrank_spatial|0.1 versus base | -0.0010 | [-0.0070, +0.0051] |
| lowrank_spatial|0.3 versus base | +0.0151 | [-0.0408, +0.0710] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0361 | [+0.0077, +0.0646] |
| output_low_rank|0.3 versus base | +0.0442 | [+0.0155, +0.0729] |

