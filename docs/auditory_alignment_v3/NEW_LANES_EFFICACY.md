# ALN3.4 new-lane efficacy snapshot

Generated 2026-10-18T16:04:02.983376+02:00 by CPU job 1045980. Status: **interim**.

Complete identity pairing is required; seeds and folds do not increase n. Intervals condition on fitted models. Interim snapshots are not sequential significance tests. `historical_selected` tables reuse existing baseline records; they are not new budget results and do not replace the frozen ADDENDUM_11 analysis.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| learning_budget_v2 | 18 / 150 | 0 |
| data_inner_v1 | 167 / 590 | 0 |
| adaptation_policy_v1 | 22 / 120 | 0 |
| strong_fusion_v1 | 17 / 30 | 0 |
| episode_training_v1 | 12 / 80 | 0 |

Positive values mean lower true query NLL than the named reference. Native and unified are distinct families. All group summaries and coverage are in `results/auditory_alignment_v3/aln34/new_lanes/efficacy.json`.

## budget/cbramod/pretrained_full · native · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1523 | [-0.2177, -0.0868] |
| fixed_0.25 versus historical_selected | -0.2532 | [-0.3536, -0.1528] |
| fixed_0.5 versus historical_selected | -0.0796 | [-0.1443, -0.0149] |
| fixed_1.0 versus historical_selected | -0.1117 | [-0.1663, -0.0570] |
| fixed_2.0 versus historical_selected | -0.2640 | [-0.3410, -0.1869] |
| new_selected versus historical_selected | -0.2336 | [-0.3024, -0.1648] |

## budget/cbramod/pretrained_full · unified · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0842 | [-0.1409, -0.0275] |
| fixed_0.25 versus historical_selected | -0.1464 | [-0.2049, -0.0879] |
| fixed_0.5 versus historical_selected | -0.0221 | [-0.0634, +0.0191] |
| fixed_1.0 versus historical_selected | -0.0836 | [-0.1364, -0.0307] |
| fixed_2.0 versus historical_selected | -0.1678 | [-0.2089, -0.1267] |
| new_selected versus historical_selected | -0.1519 | [-0.1937, -0.1101] |

## budget/cbramod/random_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1220 | [-0.2029, -0.0410] |
| fixed_0.25 versus historical_selected | -0.2470 | [-0.3692, -0.1248] |
| fixed_0.5 versus historical_selected | -0.0478 | [-0.1036, +0.0080] |
| fixed_1.0 versus historical_selected | -0.0986 | [-0.2141, +0.0170] |
| fixed_2.0 versus historical_selected | -0.2205 | [-0.3519, -0.0891] |
| new_selected versus historical_selected | -0.1840 | [-0.3141, -0.0539] |

## budget/cbramod/random_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.1817 | [-0.2402, -0.1232] |
| fixed_0.25 versus historical_selected | -0.1408 | [-0.1976, -0.0841] |
| fixed_0.5 versus historical_selected | +0.0032 | [-0.0502, +0.0565] |
| fixed_1.0 versus historical_selected | -0.0506 | [-0.1022, +0.0009] |
| fixed_2.0 versus historical_selected | -0.2323 | [-0.3048, -0.1598] |
| new_selected versus historical_selected | -0.1676 | [-0.2371, -0.0980] |

## budget/local · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0841 | [-0.1285, -0.0397] |
| fixed_0.25 versus historical_selected | -0.0374 | [-0.1228, +0.0479] |
| fixed_0.5 versus historical_selected | -0.0240 | [-0.1208, +0.0728] |
| fixed_1.0 versus historical_selected | -0.0389 | [-0.0974, +0.0195] |
| fixed_2.0 versus historical_selected | -0.1231 | [-0.1845, -0.0616] |
| new_selected versus historical_selected | -0.1197 | [-0.1819, -0.0575] |

## budget/local · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0607 | [-0.0927, -0.0288] |
| fixed_0.25 versus historical_selected | +0.0012 | [-0.0444, +0.0468] |
| fixed_0.5 versus historical_selected | -0.0170 | [-0.0611, +0.0272] |
| fixed_1.0 versus historical_selected | -0.0461 | [-0.0921, -0.0001] |
| fixed_2.0 versus historical_selected | -0.1068 | [-0.1589, -0.0548] |
| new_selected versus historical_selected | -0.1068 | [-0.1613, -0.0522] |

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

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3748 | [-0.6181, -0.1314] |
| 0.5 versus full | -0.2549 | [-0.4013, -0.1085] |

## data/content/reve/random_full · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2748 | [-0.4136, -0.1361] |
| 0.5 versus full | -0.2072 | [-0.3279, -0.0865] |

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

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3633 | [+0.1269, +0.5998] |
| cbramod/pretrained_full versus local | +0.1867 | [-0.0183, +0.3917] |
| cbramod/random_full versus local | -0.1766 | [-0.4424, +0.0892] |
| reve/pretrained_full versus local | -0.0916 | [-0.3548, +0.1716] |
| reve/random_full versus local | +0.0080 | [-0.1773, +0.1933] |
| reve/pretrained_full versus reve/random_full | -0.0996 | [-0.3750, +0.1758] |

## data_models/content/0.25 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3398 | [+0.1248, +0.5547] |
| cbramod/pretrained_full versus local | +0.2100 | [+0.0620, +0.3581] |
| cbramod/random_full versus local | -0.1297 | [-0.3415, +0.0820] |
| reve/pretrained_full versus local | -0.0079 | [-0.1416, +0.1258] |
| reve/random_full versus local | +0.0457 | [-0.1405, +0.2320] |
| reve/pretrained_full versus reve/random_full | -0.0536 | [-0.2664, +0.1592] |

## data_models/content/0.5 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.3172 | [+0.1260, +0.5085] |
| cbramod/pretrained_full versus local | +0.1855 | [-0.1128, +0.4837] |
| cbramod/random_full versus local | -0.1318 | [-0.4272, +0.1636] |
| reve/pretrained_full versus local | -0.1676 | [-0.5155, +0.1802] |
| reve/random_full versus local | -0.0844 | [-0.2575, +0.0887] |
| reve/pretrained_full versus reve/random_full | -0.0833 | [-0.4170, +0.2505] |

## data_models/content/0.5 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.2705 | [+0.0920, +0.4489] |
| cbramod/pretrained_full versus local | +0.3058 | [+0.0905, +0.5212] |
| cbramod/random_full versus local | +0.0354 | [-0.1737, +0.2445] |
| reve/pretrained_full versus local | +0.0774 | [-0.1478, +0.3026] |
| reve/random_full versus local | +0.0803 | [-0.0855, +0.2460] |
| reve/pretrained_full versus reve/random_full | -0.0029 | [-0.2432, +0.2375] |

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

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0002, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0002, +0.0001] |
| episode_selected versus ordinary_selected | -0.0001 | [-0.0002, +0.0001] |
| episode_selected versus source_no_adaptation | -0.0125 | [-0.0426, +0.0175] |
| fixed_episode/0 versus source_no_adaptation | -0.0133 | [-0.0444, +0.0178] |
| fixed_episode/20 versus source_no_adaptation | +0.0097 | [-0.0494, +0.0688] |
| fixed_episode/5 versus source_no_adaptation | -0.0100 | [-0.0399, +0.0199] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0132 | [-0.0442, +0.0178] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0097 | [-0.0492, +0.0687] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0099 | [-0.0397, +0.0199] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0170 | [-0.0440, +0.0780] |
| fixed_source/5 versus source_no_adaptation | +0.0032 | [-0.0005, +0.0068] |
| ordinary_selected versus source_no_adaptation | -0.0125 | [-0.0424, +0.0175] |

## episode/cbramod/pretrained_full/support_0.1 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0001, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000, +0.0001] |
| episode_selected versus source_no_adaptation | -0.0033 | [-0.0254, +0.0189] |
| fixed_episode/0 versus source_no_adaptation | -0.0034 | [-0.0259, +0.0191] |
| fixed_episode/20 versus source_no_adaptation | +0.0184 | [-0.0509, +0.0876] |
| fixed_episode/5 versus source_no_adaptation | -0.0012 | [-0.0239, +0.0216] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0034 | [-0.0259, +0.0191] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0183 | [-0.0508, +0.0875] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0012 | [-0.0239, +0.0216] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0206 | [-0.0388, +0.0800] |
| fixed_source/5 versus source_no_adaptation | +0.0023 | [+0.0003, +0.0042] |
| ordinary_selected versus source_no_adaptation | -0.0033 | [-0.0254, +0.0189] |

## episode/cbramod/pretrained_full/support_0.3 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0001 | [-0.0003, +0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0002, +0.0001] |
| episode_selected versus ordinary_selected | -0.0001 | [-0.0002, +0.0001] |
| episode_selected versus source_no_adaptation | -0.0089 | [-0.0627, +0.0449] |
| fixed_episode/0 versus source_no_adaptation | -0.0133 | [-0.0393, +0.0128] |
| fixed_episode/20 versus source_no_adaptation | +0.0209 | [-0.0524, +0.0942] |
| fixed_episode/5 versus source_no_adaptation | -0.0091 | [-0.0336, +0.0155] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0132 | [-0.0392, +0.0128] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0210 | [-0.0523, +0.0942] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0090 | [-0.0334, +0.0155] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0308 | [-0.0419, +0.1036] |
| fixed_source/5 versus source_no_adaptation | +0.0041 | [-0.0007, +0.0088] |
| ordinary_selected versus source_no_adaptation | -0.0089 | [-0.0626, +0.0449] |

## episode/cbramod/pretrained_full/support_0.3 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0001 | [-0.0006, +0.0008] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus source_no_adaptation | +0.0009 | [-0.1063, +0.1081] |
| fixed_episode/0 versus source_no_adaptation | -0.0034 | [-0.0513, +0.0444] |
| fixed_episode/20 versus source_no_adaptation | +0.0236 | [-0.1250, +0.1722] |
| fixed_episode/5 versus source_no_adaptation | -0.0006 | [-0.0490, +0.0478] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0034 | [-0.0513, +0.0444] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0236 | [-0.1250, +0.1721] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0006 | [-0.0489, +0.0478] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0265 | [-0.0965, +0.1496] |
| fixed_source/5 versus source_no_adaptation | +0.0029 | [-0.0027, +0.0084] |
| ordinary_selected versus source_no_adaptation | +0.0009 | [-0.1062, +0.1080] |

## episode/cbramod/random_full/support_0.1 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0001 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0001, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0001] |
| episode_selected versus source_no_adaptation | +0.0310 | [-0.0780, +0.1401] |
| fixed_episode/0 versus source_no_adaptation | +0.0290 | [-0.0872, +0.1453] |
| fixed_episode/20 versus source_no_adaptation | +0.0513 | [-0.0892, +0.1917] |
| fixed_episode/5 versus source_no_adaptation | +0.0313 | [-0.0854, +0.1480] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0291 | [-0.0871, +0.1453] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0513 | [-0.0891, +0.1917] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0313 | [-0.0853, +0.1480] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0205 | [-0.0438, +0.0847] |
| fixed_source/5 versus source_no_adaptation | +0.0023 | [-0.0007, +0.0054] |
| ordinary_selected versus source_no_adaptation | +0.0311 | [-0.0780, +0.1401] |

## episode/cbramod/random_full/support_0.1 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0201 | [-0.0491, +0.0089] |
| fixed_episode/0 versus source_no_adaptation | -0.0150 | [-0.0297, -0.0002] |
| fixed_episode/20 versus source_no_adaptation | -0.0006 | [-0.0218, +0.0206] |
| fixed_episode/5 versus source_no_adaptation | -0.0139 | [-0.0282, +0.0003] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0150 | [-0.0297, -0.0002] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0006 | [-0.0217, +0.0206] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0139 | [-0.0282, +0.0003] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0130 | [-0.0092, +0.0353] |
| fixed_source/5 versus source_no_adaptation | +0.0010 | [-0.0000, +0.0020] |
| ordinary_selected versus source_no_adaptation | -0.0201 | [-0.0491, +0.0089] |

## episode/cbramod/random_full/support_0.3 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0002, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0002, +0.0001] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0001] |
| episode_selected versus source_no_adaptation | +0.0357 | [-0.1012, +0.1726] |
| fixed_episode/0 versus source_no_adaptation | +0.0290 | [-0.0957, +0.1538] |
| fixed_episode/20 versus source_no_adaptation | +0.0827 | [-0.1103, +0.2758] |
| fixed_episode/5 versus source_no_adaptation | +0.0334 | [-0.0945, +0.1613] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0291 | [-0.0956, +0.1538] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0828 | [-0.1102, +0.2758] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0334 | [-0.0944, +0.1613] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0563 | [-0.0388, +0.1514] |
| fixed_source/5 versus source_no_adaptation | +0.0046 | [-0.0006, +0.0098] |
| ordinary_selected versus source_no_adaptation | +0.0357 | [-0.1012, +0.1725] |

## episode/cbramod/random_full/support_0.3 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000, +0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000, +0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000, +0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0139 | [-0.0606, +0.0329] |
| fixed_episode/0 versus source_no_adaptation | -0.0150 | [-0.0312, +0.0013] |
| fixed_episode/20 versus source_no_adaptation | +0.0140 | [-0.0449, +0.0729] |
| fixed_episode/5 versus source_no_adaptation | -0.0128 | [-0.0294, +0.0038] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0150 | [-0.0313, +0.0013] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0140 | [-0.0449, +0.0729] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0128 | [-0.0294, +0.0038] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0304 | [-0.0204, +0.0813] |
| fixed_source/5 versus source_no_adaptation | +0.0023 | [-0.0002, +0.0047] |
| ordinary_selected versus source_no_adaptation | -0.0139 | [-0.0606, +0.0329] |

## episode/local/support_0.1 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0004, +0.0003] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0005, +0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0004, +0.0003] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0165 | [-0.1080, +0.0749] |
| fixed_episode/0 versus source_no_adaptation | +0.0079 | [-0.0374, +0.0532] |
| fixed_episode/20 versus source_no_adaptation | +0.0197 | [-0.1458, +0.1852] |
| fixed_episode/5 versus source_no_adaptation | +0.0128 | [-0.0322, +0.0578] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0079 | [-0.0375, +0.0533] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0200 | [-0.1454, +0.1853] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0129 | [-0.0323, +0.0580] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | -0.0019 | [-0.1733, +0.1695] |
| fixed_source/5 versus source_no_adaptation | +0.0043 | [-0.0032, +0.0119] |
| ordinary_selected versus source_no_adaptation | -0.0165 | [-0.1080, +0.0749] |

## episode/local/support_0.1 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0004, +0.0003] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0007, +0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0004, +0.0003] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | -0.0083 | [-0.0739, +0.0573] |
| fixed_episode/0 versus source_no_adaptation | -0.0030 | [-0.0385, +0.0325] |
| fixed_episode/20 versus source_no_adaptation | +0.0036 | [-0.1323, +0.1395] |
| fixed_episode/5 versus source_no_adaptation | -0.0005 | [-0.0360, +0.0350] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0029 | [-0.0385, +0.0326] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0038 | [-0.1318, +0.1395] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0005 | [-0.0360, +0.0351] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | -0.0012 | [-0.1440, +0.1416] |
| fixed_source/5 versus source_no_adaptation | +0.0022 | [-0.0036, +0.0080] |
| ordinary_selected versus source_no_adaptation | -0.0083 | [-0.0739, +0.0573] |

## episode/local/support_0.3 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0004, +0.0003] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0002, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0001 | [-0.0004, +0.0003] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0996 | [-0.0574, +0.2565] |
| fixed_episode/0 versus source_no_adaptation | +0.0079 | [-0.0448, +0.0606] |
| fixed_episode/20 versus source_no_adaptation | +0.1129 | [-0.0562, +0.2819] |
| fixed_episode/5 versus source_no_adaptation | +0.0167 | [-0.0394, +0.0728] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0079 | [-0.0449, +0.0608] |
| fixed_ordinary/20 versus source_no_adaptation | +0.1129 | [-0.0562, +0.2819] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0167 | [-0.0395, +0.0730] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0996 | [-0.0574, +0.2565] |
| fixed_source/5 versus source_no_adaptation | +0.0087 | [-0.0009, +0.0183] |
| ordinary_selected versus source_no_adaptation | +0.0996 | [-0.0574, +0.2565] |

## episode/local/support_0.3 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0001 | [-0.0004, +0.0003] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0002, +0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0004, +0.0003] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0576 | [-0.0411, +0.1563] |
| fixed_episode/0 versus source_no_adaptation | -0.0030 | [-0.0327, +0.0267] |
| fixed_episode/20 versus source_no_adaptation | +0.0594 | [-0.0433, +0.1621] |
| fixed_episode/5 versus source_no_adaptation | +0.0016 | [-0.0315, +0.0347] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0029 | [-0.0327, +0.0268] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0594 | [-0.0433, +0.1620] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0016 | [-0.0315, +0.0348] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0576 | [-0.0411, +0.1563] |
| fixed_source/5 versus source_no_adaptation | +0.0045 | [-0.0017, +0.0107] |
| ordinary_selected versus source_no_adaptation | +0.0576 | [-0.0411, +0.1563] |

## episode/reve/pretrained_full/support_0.1 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0004 | [-0.0017, +0.0009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_episode/0 versus source_no_adaptation | -0.0014 | [-0.0305, +0.0276] |
| fixed_episode/20 versus source_no_adaptation | +0.0224 | [-0.0768, +0.1217] |
| fixed_episode/5 versus source_no_adaptation | +0.0016 | [-0.0270, +0.0302] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0014 | [-0.0304, +0.0275] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0228 | [-0.0764, +0.1221] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0016 | [-0.0269, +0.0301] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0253 | [-0.0692, +0.1198] |
| fixed_source/5 versus source_no_adaptation | +0.0032 | [-0.0021, +0.0085] |
| ordinary_selected versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |

## episode/reve/pretrained_full/support_0.1 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0002 | [-0.0007, +0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000, +0.0000] |
| episode_selected versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_episode/0 versus source_no_adaptation | +0.0019 | [-0.0150, +0.0188] |
| fixed_episode/20 versus source_no_adaptation | +0.0298 | [-0.0307, +0.0903] |
| fixed_episode/5 versus source_no_adaptation | +0.0046 | [-0.0127, +0.0220] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0019 | [-0.0150, +0.0188] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0300 | [-0.0306, +0.0906] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0046 | [-0.0127, +0.0220] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0263 | [-0.0253, +0.0779] |
| fixed_source/5 versus source_no_adaptation | +0.0028 | [-0.0007, +0.0062] |
| ordinary_selected versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |

## episode/reve/pretrained_full/support_0.3 · native · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0001 | [-0.0002, +0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0001, +0.0001] |
| episode_selected versus source_no_adaptation | +0.0270 | [-0.0225, +0.0766] |
| fixed_episode/0 versus source_no_adaptation | -0.0014 | [-0.0218, +0.0190] |
| fixed_episode/20 versus source_no_adaptation | +0.0479 | [-0.0165, +0.1123] |
| fixed_episode/5 versus source_no_adaptation | +0.0031 | [-0.0187, +0.0249] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0014 | [-0.0218, +0.0189] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0478 | [-0.0166, +0.1122] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0031 | [-0.0186, +0.0248] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0485 | [-0.0093, +0.1062] |
| fixed_source/5 versus source_no_adaptation | +0.0045 | [+0.0013, +0.0077] |
| ordinary_selected versus source_no_adaptation | +0.0270 | [-0.0226, +0.0766] |

## episode/reve/pretrained_full/support_0.3 · unified · 3401

Common paired identities: 10 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001, +0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0001 | [-0.0001, +0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000, +0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0001, +0.0002] |
| episode_selected versus source_no_adaptation | +0.0312 | [-0.0160, +0.0785] |
| fixed_episode/0 versus source_no_adaptation | +0.0019 | [-0.0138, +0.0177] |
| fixed_episode/20 versus source_no_adaptation | +0.0465 | [-0.0190, +0.1120] |
| fixed_episode/5 versus source_no_adaptation | +0.0053 | [-0.0123, +0.0229] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0019 | [-0.0138, +0.0177] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0464 | [-0.0191, +0.1120] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0053 | [-0.0123, +0.0229] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000, +0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0432 | [-0.0142, +0.1006] |
| fixed_source/5 versus source_no_adaptation | +0.0033 | [-0.0003, +0.0070] |
| ordinary_selected versus source_no_adaptation | +0.0312 | [-0.0161, +0.0784] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.8141 | [-0.9757, -0.6524] |
| probability versus fm_direct | +0.0596 | [+0.0065, +0.1126] |
| residual versus fm_direct | -0.3491 | [-0.4919, -0.2062] |
| sc_local versus fm_direct | -0.9137 | [-1.1438, -0.6837] |
| common_linear versus local_direct | -0.4650 | [-0.6330, -0.2970] |
| probability versus local_direct | +0.4086 | [+0.3055, +0.5118] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5647 | [-0.7659, -0.3634] |
| common_linear versus strong_single | -0.7103 | [-0.8669, -0.5537] |
| probability versus strong_single | +0.1633 | [+0.1254, +0.2013] |
| residual versus strong_single | -0.2453 | [-0.3641, -0.1265] |
| sc_local versus strong_single | -0.8100 | [-1.0227, -0.5972] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1761 | [-0.2531, -0.0991] |
| probability versus fm_direct | +0.0302 | [-0.0125, +0.0730] |
| residual versus fm_direct | -0.1597 | [-0.2713, -0.0481] |
| sc_local versus fm_direct | -0.2922 | [-0.4376, -0.1467] |
| common_linear versus local_direct | -0.0165 | [-0.0785, +0.0456] |
| probability versus local_direct | +0.1899 | [+0.1028, +0.2770] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1325 | [-0.2017, -0.0633] |
| common_linear versus strong_single | -0.1394 | [-0.2012, -0.0777] |
| probability versus strong_single | +0.0670 | [+0.0325, +0.1014] |
| residual versus strong_single | -0.1230 | [-0.2102, -0.0357] |
| sc_local versus strong_single | -0.2554 | [-0.3714, -0.1395] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.5639 | [-0.6877, -0.4402] |
| probability versus fm_direct | +0.1865 | [+0.1138, +0.2592] |
| residual versus fm_direct | -0.0516 | [-0.1821, +0.0790] |
| sc_local versus fm_direct | -0.6162 | [-0.7876, -0.4449] |
| common_linear versus local_direct | -0.5124 | [-0.6749, -0.3498] |
| probability versus local_direct | +0.2381 | [+0.1703, +0.3058] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5647 | [-0.7667, -0.3627] |
| common_linear versus strong_single | -0.7577 | [-0.9251, -0.5902] |
| probability versus strong_single | -0.0073 | [-0.1047, +0.0902] |
| residual versus strong_single | -0.2453 | [-0.3646, -0.1260] |
| sc_local versus strong_single | -0.8100 | [-1.0235, -0.5964] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0895 | [-0.1668, -0.0123] |
| probability versus fm_direct | +0.1255 | [+0.0740, +0.1770] |
| residual versus fm_direct | -0.0113 | [-0.1109, +0.0883] |
| sc_local versus fm_direct | -0.1438 | [-0.2580, -0.0295] |
| common_linear versus local_direct | -0.0783 | [-0.1361, -0.0204] |
| probability versus local_direct | +0.1368 | [+0.0835, +0.1900] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1325 | [-0.2000, -0.0650] |
| common_linear versus strong_single | -0.2012 | [-0.2952, -0.1072] |
| probability versus strong_single | +0.0138 | [-0.0533, +0.0810] |
| residual versus strong_single | -0.1230 | [-0.2080, -0.0379] |
| sc_local versus strong_single | -0.2554 | [-0.3686, -0.1423] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.5064 | [-0.6529, -0.3600] |
| probability versus fm_direct | +0.2676 | [+0.1943, +0.3409] |
| residual versus fm_direct | -0.0400 | [-0.1743, +0.0942] |
| sc_local versus fm_direct | -0.6047 | [-0.8280, -0.3814] |
| common_linear versus local_direct | -0.4664 | [-0.6443, -0.2885] |
| probability versus local_direct | +0.3076 | [+0.2376, +0.3777] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.5647 | [-0.7668, -0.3625] |
| common_linear versus strong_single | -0.7117 | [-0.8722, -0.5512] |
| probability versus strong_single | +0.0623 | [-0.0100, +0.1346] |
| residual versus strong_single | -0.2453 | [-0.3647, -0.1260] |
| sc_local versus strong_single | -0.8100 | [-1.0237, -0.5963] |

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

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1102 | [-0.2137, -0.0067] |
| probability versus fm_direct | +0.1403 | [+0.0609, +0.2198] |
| residual versus fm_direct | -0.0269 | [-0.1460, +0.0921] |
| sc_local versus fm_direct | -0.1594 | [-0.3142, -0.0046] |
| common_linear versus local_direct | -0.0832 | [-0.1609, -0.0056] |
| probability versus local_direct | +0.1673 | [+0.1145, +0.2200] |
| residual versus local_direct | +0.0000 | [+0.0000, +0.0000] |
| sc_local versus local_direct | -0.1325 | [-0.2009, -0.0641] |
| common_linear versus strong_single | -0.2062 | [-0.2883, -0.1241] |
| probability versus strong_single | +0.0443 | [-0.0234, +0.1120] |
| residual versus strong_single | -0.1230 | [-0.2092, -0.0368] |
| sc_local versus strong_single | -0.2554 | [-0.3700, -0.1409] |

## policy/cbramod/pretrained_full · native · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0035 | [-0.0071, +0.0142] |
| declared_window_temporal|0.3 versus base | -0.0022 | [-0.0216, +0.0172] |
| diagonal_spatial|0.1 versus base | -0.0023 | [-0.0159, +0.0113] |
| diagonal_spatial|0.3 versus base | +0.0159 | [-0.0058, +0.0376] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.3 versus base | +0.0003 | [-0.0175, +0.0180] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0081 | [-0.0428, +0.0591] |
| output_low_rank|0.3 versus base | +0.0518 | [+0.0009, +0.1026] |

## policy/cbramod/pretrained_full · unified · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0016 | [-0.0033, +0.0066] |
| declared_window_temporal|0.3 versus base | +0.0014 | [-0.0074, +0.0101] |
| diagonal_spatial|0.1 versus base | +0.0005 | [-0.0079, +0.0088] |
| diagonal_spatial|0.3 versus base | +0.0144 | [-0.0002, +0.0291] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.3 versus base | +0.0013 | [-0.0102, +0.0128] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0265 | [-0.0209, +0.0740] |
| output_low_rank|0.3 versus base | +0.0615 | [+0.0130, +0.1100] |

## policy/cbramod/random_full · native · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0018 | [-0.0124, +0.0161] |
| declared_window_temporal|0.3 versus base | +0.0146 | [-0.0063, +0.0355] |
| diagonal_spatial|0.1 versus base | +0.0053 | [-0.0184, +0.0290] |
| diagonal_spatial|0.3 versus base | +0.0090 | [-0.0119, +0.0299] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0064 | [-0.0262, +0.0134] |
| lowrank_spatial|0.3 versus base | +0.0120 | [-0.0088, +0.0329] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0187 | [-0.0269, +0.0643] |
| output_low_rank|0.3 versus base | +0.0582 | [-0.0046, +0.1210] |

## policy/cbramod/random_full · unified · 3401

Common paired identities: 28 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0001 | [-0.0102, +0.0104] |
| declared_window_temporal|0.3 versus base | -0.0014 | [-0.0111, +0.0082] |
| diagonal_spatial|0.1 versus base | -0.0017 | [-0.0191, +0.0157] |
| diagonal_spatial|0.3 versus base | +0.0065 | [-0.0085, +0.0215] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0047 | [-0.0187, +0.0094] |
| lowrank_spatial|0.3 versus base | +0.0072 | [-0.0057, +0.0201] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0188 | [-0.0054, +0.0430] |
| output_low_rank|0.3 versus base | +0.0272 | [-0.0113, +0.0658] |

## policy/local · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | -0.0001 | [-0.0326, +0.0324] |
| declared_window_temporal|0.3 versus base | +0.0185 | [-0.0146, +0.0516] |
| diagonal_spatial|0.1 versus base | -0.0055 | [-0.0685, +0.0576] |
| diagonal_spatial|0.3 versus base | +0.0663 | [-0.0063, +0.1389] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0083 | [-0.0506, +0.0341] |
| lowrank_spatial|0.3 versus base | +0.0498 | [-0.0231, +0.1227] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0112 | [-0.0506, +0.0729] |
| output_low_rank|0.3 versus base | +0.0535 | [-0.0462, +0.1532] |

## policy/local · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0003 | [-0.0211, +0.0217] |
| declared_window_temporal|0.3 versus base | +0.0106 | [-0.0124, +0.0336] |
| diagonal_spatial|0.1 versus base | -0.0089 | [-0.0437, +0.0259] |
| diagonal_spatial|0.3 versus base | +0.0360 | [-0.0078, +0.0798] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| lowrank_spatial|0.1 versus base | -0.0042 | [-0.0292, +0.0209] |
| lowrank_spatial|0.3 versus base | +0.0288 | [-0.0217, +0.0793] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0198 | [-0.0153, +0.0549] |
| output_low_rank|0.3 versus base | +0.0425 | [-0.0133, +0.0984] |

## policy/reve/pretrained_full · native · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0079 | [-0.0095, +0.0253] |
| declared_window_temporal|0.3 versus base | +0.0347 | [-0.0107, +0.0801] |
| diagonal_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| diagonal_spatial|0.3 versus base | +0.0376 | [-0.0112, +0.0863] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0149 | [-0.0749, +0.1047] |
| lowrank_spatial|0.1 versus base | -0.0022 | [-0.0105, +0.0061] |
| lowrank_spatial|0.3 versus base | -0.0170 | [-0.1415, +0.1076] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0298 | [-0.0411, +0.1006] |
| output_low_rank|0.3 versus base | +0.0764 | [-0.0158, +0.1687] |

## policy/reve/pretrained_full · unified · 3401

Common paired identities: 20 / 44.

| Contrast | ΔR bits/query | Simultaneous 95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0083 | [-0.0035, +0.0201] |
| declared_window_temporal|0.3 versus base | +0.0192 | [-0.0009, +0.0393] |
| diagonal_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| diagonal_spatial|0.3 versus base | +0.0261 | [-0.0095, +0.0616] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| full_spatial|0.3 versus base | +0.0251 | [-0.0502, +0.1004] |
| lowrank_spatial|0.1 versus base | -0.0013 | [-0.0108, +0.0081] |
| lowrank_spatial|0.3 versus base | +0.0212 | [-0.0662, +0.1086] |
| none|0.1 versus base | +0.0000 | [+0.0000, +0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000, +0.0000] |
| output_low_rank|0.1 versus base | +0.0483 | [+0.0077, +0.0889] |
| output_low_rank|0.3 versus base | +0.0589 | [+0.0198, +0.0980] |

