# FAU/Federici breadth intervention results

Snapshot 2026-10-20T19:29:30.442576+02:00, CPU job 1047358; **interim**.

Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| breadth_budget_v1 | 66 / 75 | 0 |
| breadth_inner_v1 | 300 / 375 | 0 |
| breadth_policy_v1 | 40 / 40 | 0 |
| breadth_fusion_v1 | 15 / 15 | 0 |
| breadth_episode_v1 | 40 / 40 | 0 |

## fau / budget/cbramod/pretrained_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0028 | [-0.0344,+0.0288] |
| fixed_0.25 versus historical_selected | -0.1449 | [-0.2034,-0.0864] |
| fixed_0.5 versus historical_selected | -0.0460 | [-0.0930,+0.0011] |
| fixed_1.0 versus historical_selected | -0.0317 | [-0.0643,+0.0010] |
| fixed_2.0 versus historical_selected | -0.0345 | [-0.0648,-0.0042] |
| new_selected versus historical_selected | -0.0364 | [-0.0650,-0.0078] |

## fau / budget/cbramod/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0412 | [-0.0583,-0.0240] |
| fixed_0.25 versus historical_selected | -0.0523 | [-0.0781,-0.0265] |
| fixed_0.5 versus historical_selected | -0.0009 | [-0.0209,+0.0191] |
| fixed_1.0 versus historical_selected | -0.0138 | [-0.0350,+0.0074] |
| fixed_2.0 versus historical_selected | -0.0549 | [-0.0776,-0.0322] |
| new_selected versus historical_selected | -0.0486 | [-0.0713,-0.0259] |

## fau / budget/cbramod/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0786 | [-0.1006,-0.0567] |
| fixed_0.25 versus historical_selected | -0.1075 | [-0.1545,-0.0604] |
| fixed_0.5 versus historical_selected | -0.0231 | [-0.0588,+0.0125] |
| fixed_1.0 versus historical_selected | -0.0326 | [-0.0626,-0.0026] |
| fixed_2.0 versus historical_selected | -0.1113 | [-0.1471,-0.0754] |
| new_selected versus historical_selected | -0.0741 | [-0.1093,-0.0390] |

## fau / budget/cbramod/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0521 | [-0.0872,-0.0169] |
| fixed_0.25 versus historical_selected | +0.0250 | [-0.0114,+0.0614] |
| fixed_0.5 versus historical_selected | +0.0329 | [+0.0026,+0.0632] |
| fixed_1.0 versus historical_selected | -0.0334 | [-0.0588,-0.0080] |
| fixed_2.0 versus historical_selected | -0.0855 | [-0.1308,-0.0402] |
| new_selected versus historical_selected | -0.0497 | [-0.0924,-0.0069] |

## fau / budget/local / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0054 | [-0.0172,+0.0063] |
| fixed_0.25 versus historical_selected | -0.0374 | [-0.0653,-0.0095] |
| fixed_0.5 versus historical_selected | -0.0183 | [-0.0350,-0.0016] |
| fixed_1.0 versus historical_selected | -0.0132 | [-0.0312,+0.0047] |
| fixed_2.0 versus historical_selected | -0.0187 | [-0.0322,-0.0052] |
| new_selected versus historical_selected | -0.0108 | [-0.0258,+0.0042] |

## fau / budget/local / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0219 | [-0.0388,-0.0050] |
| fixed_0.25 versus historical_selected | +0.0280 | [-0.0084,+0.0645] |
| fixed_0.5 versus historical_selected | +0.0107 | [-0.0052,+0.0265] |
| fixed_1.0 versus historical_selected | +0.0035 | [-0.0132,+0.0202] |
| fixed_2.0 versus historical_selected | -0.0184 | [-0.0333,-0.0035] |
| new_selected versus historical_selected | -0.0113 | [-0.0266,+0.0041] |

## fau / budget_models/fixed_0.5 / native

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0621 | [+0.0118,+0.1123] |
| cbramod/pretrained_full versus local | +0.1132 | [+0.0486,+0.1779] |
| cbramod/random_full versus local | +0.0512 | [-0.0114,+0.1137] |
| reve/pretrained_full versus local | +0.1201 | [+0.0035,+0.2368] |
| reve/random_full versus local | +0.0160 | [-0.0605,+0.0926] |
| reve/pretrained_full versus reve/random_full | +0.1041 | [-0.0168,+0.2251] |

## fau / budget_models/fixed_0.5 / unified

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0673 | [+0.0193,+0.1153] |
| cbramod/pretrained_full versus local | +0.1147 | [+0.0211,+0.2083] |
| cbramod/random_full versus local | +0.0474 | [-0.0341,+0.1288] |
| reve/pretrained_full versus local | +0.1055 | [+0.0058,+0.2052] |
| reve/random_full versus local | +0.0368 | [-0.0180,+0.0917] |
| reve/pretrained_full versus reve/random_full | +0.0686 | [-0.0270,+0.1643] |

## fau / budget_models/fixed_1.0 / native

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0966 | [+0.0100,+0.1833] |
| cbramod/pretrained_full versus local | +0.1316 | [+0.0171,+0.2460] |
| cbramod/random_full versus local | +0.0350 | [-0.0285,+0.0984] |
| reve/pretrained_full versus local | +0.0040 | [-0.1131,+0.1210] |
| reve/random_full versus local | +0.1004 | [+0.0336,+0.1673] |
| reve/pretrained_full versus reve/random_full | -0.0965 | [-0.2011,+0.0082] |

## fau / budget_models/fixed_1.0 / unified

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1461 | [+0.0866,+0.2055] |
| cbramod/pretrained_full versus local | +0.1285 | [+0.0341,+0.2230] |
| cbramod/random_full versus local | -0.0175 | [-0.0814,+0.0463] |
| reve/pretrained_full versus local | +0.0046 | [-0.0882,+0.0975] |
| reve/random_full versus local | +0.0882 | [+0.0072,+0.1692] |
| reve/pretrained_full versus reve/random_full | -0.0836 | [-0.1625,-0.0047] |

## fau / budget_models/fixed_2.0 / native

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1725 | [+0.0806,+0.2644] |
| cbramod/pretrained_full versus local | +0.1308 | [+0.0263,+0.2353] |
| cbramod/random_full versus local | -0.0417 | [-0.1095,+0.0262] |
| reve/pretrained_full versus local | -0.1067 | [-0.2350,+0.0217] |
| reve/random_full versus local | +0.1178 | [+0.0378,+0.1978] |
| reve/pretrained_full versus reve/random_full | -0.2245 | [-0.3441,-0.1048] |

## fau / budget_models/fixed_2.0 / unified

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1450 | [+0.0584,+0.2316] |
| cbramod/pretrained_full versus local | +0.1064 | [+0.0352,+0.1777] |
| cbramod/random_full versus local | -0.0386 | [-0.0880,+0.0108] |
| reve/pretrained_full versus local | -0.0566 | [-0.1465,+0.0333] |
| reve/random_full versus local | +0.0690 | [-0.0150,+0.1530] |
| reve/pretrained_full versus reve/random_full | -0.1257 | [-0.2257,-0.0257] |

## fau / budget_models/historical_selected / native

reused historical baseline; not a new training result. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1061 | [+0.0590,+0.1532] |
| cbramod/pretrained_full versus local | +0.1698 | [+0.1012,+0.2383] |
| cbramod/random_full versus local | +0.0637 | [+0.0099,+0.1174] |
| reve/pretrained_full versus local | +0.1131 | [+0.0288,+0.1974] |
| reve/random_full versus local | +0.0999 | [+0.0494,+0.1505] |
| reve/pretrained_full versus reve/random_full | +0.0132 | [-0.0670,+0.0934] |

## fau / budget_models/historical_selected / unified

reused historical baseline; not a new training result. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1197 | [+0.0776,+0.1618] |
| cbramod/pretrained_full versus local | +0.1443 | [+0.0853,+0.2033] |
| cbramod/random_full versus local | +0.0245 | [-0.0213,+0.0704] |
| reve/pretrained_full versus local | +0.1093 | [+0.0445,+0.1741] |
| reve/random_full versus local | +0.0992 | [+0.0439,+0.1545] |
| reve/pretrained_full versus reve/random_full | +0.0101 | [-0.0422,+0.0623] |

## fau / budget_models/new_selected / native

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1242 | [+0.0360,+0.2124] |
| cbramod/pretrained_full versus local | +0.1219 | [+0.0178,+0.2261] |
| cbramod/random_full versus local | -0.0023 | [-0.0696,+0.0651] |
| reve/pretrained_full versus local | -0.0994 | [-0.2317,+0.0330] |
| reve/random_full versus local | +0.1138 | [+0.0313,+0.1964] |
| reve/pretrained_full versus reve/random_full | -0.2132 | [-0.3331,-0.0933] |

## fau / budget_models/new_selected / unified

new production intervention. Paired n=42/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1070 | [+0.0254,+0.1886] |
| cbramod/pretrained_full versus local | +0.1074 | [+0.0338,+0.1811] |
| cbramod/random_full versus local | +0.0004 | [-0.0480,+0.0489] |
| reve/pretrained_full versus local | -0.0549 | [-0.1464,+0.0366] |
| reve/random_full versus local | +0.0638 | [-0.0235,+0.1511] |
| reve/pretrained_full versus reve/random_full | -0.1187 | [-0.2182,-0.0192] |

## fau / data/content/cbramod/pretrained_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0051 | [-0.0022,+0.0123] |
| 0.5 versus full | +0.0038 | [-0.0038,+0.0114] |

## fau / data/content/cbramod/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0008 | [-0.0117,+0.0100] |
| 0.5 versus full | -0.0014 | [-0.0123,+0.0095] |

## fau / data/content/cbramod/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0120 | [-0.0048,+0.0287] |
| 0.5 versus full | +0.0104 | [-0.0064,+0.0273] |

## fau / data/content/cbramod/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0089 | [-0.0049,+0.0227] |
| 0.5 versus full | +0.0086 | [-0.0051,+0.0223] |

## fau / data/content/local / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0000 | [-0.0000,+0.0000] |
| 0.5 versus full | +0.0000 | [-0.0000,+0.0000] |

## fau / data/content/local / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0000 | [-0.0001,+0.0000] |
| 0.5 versus full | +0.0000 | [-0.0000,+0.0000] |

## fau / data/content/reve/pretrained_full / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0091 | [-0.0448,+0.0265] |
| 0.5 versus full | -0.0100 | [-0.0475,+0.0275] |

## fau / data/content/reve/pretrained_full / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0009 | [-0.0350,+0.0332] |
| 0.5 versus full | -0.0059 | [-0.0413,+0.0296] |

## fau / data/content/reve/random_full / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0000 | [-0.0000,+0.0000] |
| 0.5 versus full | +0.0000 | [-0.0000,+0.0000] |

## fau / data/content/reve/random_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0000 | [-0.0000,+0.0000] |
| 0.5 versus full | +0.0000 | [-0.0000,+0.0000] |

## fau / data/people/cbramod/pretrained_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3090 | [-0.3893,-0.2287] |
| 0.5 versus full | -0.1569 | [-0.2232,-0.0906] |

## fau / data/people/cbramod/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1856 | [-0.2486,-0.1226] |
| 0.5 versus full | -0.1056 | [-0.1528,-0.0584] |

## fau / data/people/cbramod/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3469 | [-0.4243,-0.2695] |
| 0.5 versus full | -0.1660 | [-0.2128,-0.1192] |

## fau / data/people/cbramod/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1496 | [-0.2016,-0.0976] |
| 0.5 versus full | -0.0635 | [-0.0963,-0.0307] |

## fau / data/people/local / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3166 | [-0.3785,-0.2547] |
| 0.5 versus full | -0.1667 | [-0.2191,-0.1143] |

## fau / data/people/local / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1336 | [-0.1788,-0.0884] |
| 0.5 versus full | -0.0678 | [-0.1086,-0.0270] |

## fau / data/people/reve/pretrained_full / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3366 | [-0.5052,-0.1680] |
| 0.5 versus full | -0.2414 | [-0.3601,-0.1227] |

## fau / data/people/reve/pretrained_full / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2236 | [-0.3056,-0.1415] |
| 0.5 versus full | -0.1630 | [-0.2365,-0.0895] |

## fau / data/people/reve/random_full / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2667 | [-0.4594,-0.0739] |
| 0.5 versus full | -0.1579 | [-0.3205,+0.0048] |

## fau / data/people/reve/random_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1233 | [-0.2806,+0.0339] |
| 0.5 versus full | -0.1249 | [-0.2926,+0.0428] |

## fau / data_models/content/0.25 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1060 | [-0.0651,+0.2771] |
| cbramod/pretrained_full versus local | +0.0981 | [-0.0577,+0.2539] |
| cbramod/random_full versus local | -0.0080 | [-0.1635,+0.1476] |
| reve/pretrained_full versus local | +0.0299 | [-0.2599,+0.3197] |
| reve/random_full versus local | +0.0190 | [-0.1035,+0.1415] |
| reve/pretrained_full versus reve/random_full | +0.0109 | [-0.2785,+0.3003] |

## fau / data_models/content/0.25 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0849 | [-0.0825,+0.2524] |
| cbramod/pretrained_full versus local | +0.0574 | [-0.1994,+0.3142] |
| cbramod/random_full versus local | -0.0275 | [-0.2141,+0.1590] |
| reve/pretrained_full versus local | +0.0614 | [-0.1368,+0.2596] |
| reve/random_full versus local | +0.0029 | [-0.2071,+0.2129] |
| reve/pretrained_full versus reve/random_full | +0.0584 | [-0.1224,+0.2393] |

## fau / data_models/content/0.5 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1087 | [-0.0721,+0.2894] |
| cbramod/pretrained_full versus local | +0.0981 | [-0.0660,+0.2622] |
| cbramod/random_full versus local | -0.0106 | [-0.1738,+0.1527] |
| reve/pretrained_full versus local | +0.0299 | [-0.2753,+0.3352] |
| reve/random_full versus local | +0.0190 | [-0.1100,+0.1481] |
| reve/pretrained_full versus reve/random_full | +0.0109 | [-0.2940,+0.3157] |

## fau / data_models/content/0.5 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0840 | [-0.0757,+0.2437] |
| cbramod/pretrained_full versus local | +0.0574 | [-0.1895,+0.3043] |
| cbramod/random_full versus local | -0.0266 | [-0.2088,+0.1556] |
| reve/pretrained_full versus local | +0.0614 | [-0.1291,+0.2518] |
| reve/random_full versus local | +0.0029 | [-0.1989,+0.2048] |
| reve/pretrained_full versus reve/random_full | +0.0584 | [-0.1154,+0.2323] |

## fau / data_models/people/0.25 / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1470 | [+0.0387,+0.2553] |
| cbramod/pretrained_full versus local | +0.1998 | [+0.0995,+0.3002] |
| cbramod/random_full versus local | +0.0529 | [-0.0402,+0.1460] |
| reve/pretrained_full versus local | +0.1124 | [+0.0021,+0.2227] |
| reve/random_full versus local | +0.0774 | [-0.0231,+0.1779] |
| reve/pretrained_full versus reve/random_full | +0.0351 | [-0.0709,+0.1410] |

## fau / data_models/people/0.25 / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0482 | [-0.1070,+0.2033] |
| cbramod/pretrained_full versus local | +0.0698 | [-0.0929,+0.2324] |
| cbramod/random_full versus local | +0.0216 | [-0.0855,+0.1286] |
| reve/pretrained_full versus local | +0.0284 | [-0.0697,+0.1265] |
| reve/random_full versus local | +0.0449 | [-0.0441,+0.1338] |
| reve/pretrained_full versus reve/random_full | -0.0165 | [-0.1123,+0.0794] |

## fau / data_models/people/0.5 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0872 | [-0.2435,+0.4179] |
| cbramod/pretrained_full versus local | +0.0983 | [-0.1607,+0.3573] |
| cbramod/random_full versus local | +0.0111 | [-0.2255,+0.2478] |
| reve/pretrained_full versus local | +0.0624 | [-0.1980,+0.3227] |
| reve/random_full versus local | +0.0309 | [-0.1195,+0.1814] |
| reve/pretrained_full versus reve/random_full | +0.0314 | [-0.2417,+0.3046] |

## fau / data_models/people/0.5 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1141 | [-0.1986,+0.4269] |
| cbramod/pretrained_full versus local | +0.0808 | [-0.3032,+0.4648] |
| cbramod/random_full versus local | -0.0333 | [-0.3963,+0.3297] |
| reve/pretrained_full versus local | +0.0122 | [-0.2502,+0.2747] |
| reve/random_full versus local | -0.0237 | [-0.4028,+0.3553] |
| reve/pretrained_full versus reve/random_full | +0.0360 | [-0.3131,+0.3850] |

## fau / episode/cbramod/pretrained_full/support_0.1 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0255 | [+0.0143,+0.0367] |
| fixed_episode/0 versus source_no_adaptation | +0.0130 | [+0.0048,+0.0213] |
| fixed_episode/20 versus source_no_adaptation | +0.0260 | [+0.0144,+0.0376] |
| fixed_episode/5 versus source_no_adaptation | +0.0139 | [+0.0056,+0.0223] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0130 | [+0.0048,+0.0213] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0260 | [+0.0144,+0.0376] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0139 | [+0.0056,+0.0222] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0129 | [+0.0063,+0.0196] |
| fixed_source/5 versus source_no_adaptation | +0.0009 | [+0.0005,+0.0013] |
| ordinary_selected versus source_no_adaptation | +0.0255 | [+0.0143,+0.0367] |

## fau / episode/cbramod/pretrained_full/support_0.1 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0036 | [-0.0063,+0.0135] |
| fixed_episode/0 versus source_no_adaptation | -0.0036 | [-0.0143,+0.0071] |
| fixed_episode/20 versus source_no_adaptation | +0.0039 | [-0.0062,+0.0141] |
| fixed_episode/5 versus source_no_adaptation | -0.0031 | [-0.0136,+0.0075] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0036 | [-0.0143,+0.0071] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0039 | [-0.0062,+0.0141] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0031 | [-0.0136,+0.0075] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0073 | [+0.0020,+0.0125] |
| fixed_source/5 versus source_no_adaptation | +0.0005 | [+0.0002,+0.0009] |
| ordinary_selected versus source_no_adaptation | +0.0036 | [-0.0063,+0.0135] |

## fau / episode/cbramod/pretrained_full/support_0.3 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [+0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | +0.0000 | [+0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0347 | [+0.0229,+0.0465] |
| fixed_episode/0 versus source_no_adaptation | +0.0130 | [+0.0048,+0.0213] |
| fixed_episode/20 versus source_no_adaptation | +0.0347 | [+0.0229,+0.0465] |
| fixed_episode/5 versus source_no_adaptation | +0.0144 | [+0.0061,+0.0228] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0130 | [+0.0047,+0.0213] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0347 | [+0.0229,+0.0465] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0144 | [+0.0061,+0.0228] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0219 | [+0.0143,+0.0296] |
| fixed_source/5 versus source_no_adaptation | +0.0014 | [+0.0009,+0.0019] |
| ordinary_selected versus source_no_adaptation | +0.0347 | [+0.0229,+0.0465] |

## fau / episode/cbramod/pretrained_full/support_0.3 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0106 | [-0.0001,+0.0213] |
| fixed_episode/0 versus source_no_adaptation | -0.0036 | [-0.0144,+0.0072] |
| fixed_episode/20 versus source_no_adaptation | +0.0106 | [-0.0001,+0.0213] |
| fixed_episode/5 versus source_no_adaptation | -0.0027 | [-0.0133,+0.0080] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0036 | [-0.0144,+0.0072] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0106 | [-0.0001,+0.0213] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0027 | [-0.0133,+0.0080] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0140 | [+0.0073,+0.0206] |
| fixed_source/5 versus source_no_adaptation | +0.0009 | [+0.0005,+0.0014] |
| ordinary_selected versus source_no_adaptation | +0.0106 | [-0.0001,+0.0213] |

## fau / episode/cbramod/random_full/support_0.1 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0083 | [+0.0033,+0.0132] |
| fixed_episode/0 versus source_no_adaptation | +0.0135 | [-0.0080,+0.0350] |
| fixed_episode/20 versus source_no_adaptation | +0.0211 | [-0.0003,+0.0424] |
| fixed_episode/5 versus source_no_adaptation | +0.0140 | [-0.0075,+0.0355] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0135 | [-0.0080,+0.0350] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0211 | [-0.0003,+0.0424] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0140 | [-0.0075,+0.0355] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0078 | [+0.0024,+0.0132] |
| fixed_source/5 versus source_no_adaptation | +0.0005 | [+0.0002,+0.0009] |
| ordinary_selected versus source_no_adaptation | +0.0083 | [+0.0033,+0.0132] |

## fau / episode/cbramod/random_full/support_0.1 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,-0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0017 | [-0.0090,+0.0123] |
| fixed_episode/0 versus source_no_adaptation | -0.0039 | [-0.0161,+0.0082] |
| fixed_episode/20 versus source_no_adaptation | +0.0011 | [-0.0104,+0.0125] |
| fixed_episode/5 versus source_no_adaptation | -0.0036 | [-0.0156,+0.0085] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0039 | [-0.0161,+0.0082] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0011 | [-0.0104,+0.0125] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0036 | [-0.0156,+0.0085] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0050 | [+0.0015,+0.0085] |
| fixed_source/5 versus source_no_adaptation | +0.0004 | [+0.0002,+0.0006] |
| ordinary_selected versus source_no_adaptation | +0.0017 | [-0.0090,+0.0123] |

## fau / episode/cbramod/random_full/support_0.3 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0151 | [+0.0085,+0.0217] |
| fixed_episode/0 versus source_no_adaptation | +0.0135 | [-0.0089,+0.0359] |
| fixed_episode/20 versus source_no_adaptation | +0.0269 | [+0.0043,+0.0495] |
| fixed_episode/5 versus source_no_adaptation | +0.0144 | [-0.0080,+0.0367] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0135 | [-0.0089,+0.0359] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0269 | [+0.0043,+0.0496] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0144 | [-0.0080,+0.0367] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0145 | [+0.0078,+0.0212] |
| fixed_source/5 versus source_no_adaptation | +0.0009 | [+0.0005,+0.0013] |
| ordinary_selected versus source_no_adaptation | +0.0151 | [+0.0085,+0.0217] |

## fau / episode/cbramod/random_full/support_0.3 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0058 | [-0.0062,+0.0178] |
| fixed_episode/0 versus source_no_adaptation | -0.0039 | [-0.0171,+0.0092] |
| fixed_episode/20 versus source_no_adaptation | +0.0051 | [-0.0077,+0.0179] |
| fixed_episode/5 versus source_no_adaptation | -0.0033 | [-0.0164,+0.0097] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0039 | [-0.0171,+0.0092] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0051 | [-0.0077,+0.0179] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0033 | [-0.0164,+0.0097] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0094 | [+0.0047,+0.0141] |
| fixed_source/5 versus source_no_adaptation | +0.0006 | [+0.0003,+0.0009] |
| ordinary_selected versus source_no_adaptation | +0.0058 | [-0.0062,+0.0178] |

## fau / episode/local/support_0.1 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0111 | [+0.0031,+0.0191] |
| fixed_episode/0 versus source_no_adaptation | +0.0033 | [-0.0025,+0.0091] |
| fixed_episode/20 versus source_no_adaptation | +0.0136 | [+0.0047,+0.0226] |
| fixed_episode/5 versus source_no_adaptation | +0.0041 | [-0.0016,+0.0098] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0033 | [-0.0024,+0.0091] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0136 | [+0.0047,+0.0226] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0041 | [-0.0016,+0.0098] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0106 | [+0.0028,+0.0183] |
| fixed_source/5 versus source_no_adaptation | +0.0008 | [+0.0003,+0.0013] |
| ordinary_selected versus source_no_adaptation | +0.0111 | [+0.0031,+0.0191] |

## fau / episode/local/support_0.1 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0047 | [-0.0008,+0.0102] |
| fixed_episode/0 versus source_no_adaptation | -0.0009 | [-0.0034,+0.0017] |
| fixed_episode/20 versus source_no_adaptation | +0.0050 | [-0.0008,+0.0107] |
| fixed_episode/5 versus source_no_adaptation | -0.0004 | [-0.0030,+0.0021] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0009 | [-0.0034,+0.0017] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0050 | [-0.0008,+0.0107] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0004 | [-0.0030,+0.0021] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0061 | [+0.0008,+0.0114] |
| fixed_source/5 versus source_no_adaptation | +0.0005 | [+0.0002,+0.0008] |
| ordinary_selected versus source_no_adaptation | +0.0047 | [-0.0008,+0.0102] |

## fau / episode/local/support_0.3 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0182 | [+0.0107,+0.0257] |
| fixed_episode/0 versus source_no_adaptation | +0.0033 | [-0.0021,+0.0087] |
| fixed_episode/20 versus source_no_adaptation | +0.0222 | [+0.0132,+0.0313] |
| fixed_episode/5 versus source_no_adaptation | +0.0046 | [-0.0008,+0.0100] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0033 | [-0.0021,+0.0088] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0222 | [+0.0132,+0.0313] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0046 | [-0.0008,+0.0100] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0192 | [+0.0115,+0.0268] |
| fixed_source/5 versus source_no_adaptation | +0.0013 | [+0.0008,+0.0018] |
| ordinary_selected versus source_no_adaptation | +0.0182 | [+0.0107,+0.0257] |

## fau / episode/local/support_0.3 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0092 | [+0.0039,+0.0146] |
| fixed_episode/0 versus source_no_adaptation | -0.0009 | [-0.0034,+0.0016] |
| fixed_episode/20 versus source_no_adaptation | +0.0097 | [+0.0040,+0.0154] |
| fixed_episode/5 versus source_no_adaptation | -0.0002 | [-0.0027,+0.0024] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0009 | [-0.0034,+0.0016] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0097 | [+0.0040,+0.0154] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0002 | [-0.0027,+0.0024] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0111 | [+0.0059,+0.0163] |
| fixed_source/5 versus source_no_adaptation | +0.0008 | [+0.0004,+0.0011] |
| ordinary_selected versus source_no_adaptation | +0.0092 | [+0.0039,+0.0146] |

## fau / episode/reve/pretrained_full/support_0.1 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0002,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0002,+0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0002,+0.0001] |
| episode_selected versus ordinary_selected | +0.0001 | [-0.0001,+0.0002] |
| episode_selected versus source_no_adaptation | +0.0126 | [-0.0049,+0.0300] |
| fixed_episode/0 versus source_no_adaptation | -0.0010 | [-0.0086,+0.0067] |
| fixed_episode/20 versus source_no_adaptation | +0.0118 | [-0.0063,+0.0299] |
| fixed_episode/5 versus source_no_adaptation | -0.0000 | [-0.0077,+0.0076] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0010 | [-0.0086,+0.0067] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0117 | [-0.0064,+0.0299] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0000 | [-0.0077,+0.0077] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0125 | [-0.0048,+0.0298] |
| fixed_source/5 versus source_no_adaptation | +0.0009 | [-0.0003,+0.0022] |
| ordinary_selected versus source_no_adaptation | +0.0125 | [-0.0049,+0.0300] |

## fau / episode/reve/pretrained_full/support_0.1 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0001 | [-0.0002,+0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0001,+0.0002] |
| episode_selected versus source_no_adaptation | +0.0070 | [-0.0063,+0.0203] |
| fixed_episode/0 versus source_no_adaptation | +0.0002 | [-0.0046,+0.0051] |
| fixed_episode/20 versus source_no_adaptation | +0.0068 | [-0.0070,+0.0206] |
| fixed_episode/5 versus source_no_adaptation | +0.0008 | [-0.0041,+0.0056] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0003 | [-0.0046,+0.0051] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0068 | [-0.0070,+0.0205] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0008 | [-0.0041,+0.0056] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0068 | [-0.0066,+0.0203] |
| fixed_source/5 versus source_no_adaptation | +0.0006 | [-0.0005,+0.0016] |
| ordinary_selected versus source_no_adaptation | +0.0069 | [-0.0063,+0.0202] |

## fau / episode/reve/pretrained_full/support_0.3 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0003,+0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0002,+0.0001] |
| episode_selected versus ordinary_selected | -0.0001 | [-0.0003,+0.0002] |
| episode_selected versus source_no_adaptation | +0.0174 | [-0.0009,+0.0357] |
| fixed_episode/0 versus source_no_adaptation | -0.0010 | [-0.0081,+0.0061] |
| fixed_episode/20 versus source_no_adaptation | +0.0168 | [-0.0021,+0.0357] |
| fixed_episode/5 versus source_no_adaptation | +0.0004 | [-0.0068,+0.0075] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0010 | [-0.0081,+0.0061] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0168 | [-0.0021,+0.0357] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0004 | [-0.0068,+0.0075] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0177 | [-0.0000,+0.0354] |
| fixed_source/5 versus source_no_adaptation | +0.0014 | [+0.0001,+0.0027] |
| ordinary_selected versus source_no_adaptation | +0.0174 | [-0.0008,+0.0357] |

## fau / episode/reve/pretrained_full/support_0.3 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0002,+0.0002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0002,+0.0001] |
| episode_selected versus source_no_adaptation | +0.0097 | [-0.0014,+0.0209] |
| fixed_episode/0 versus source_no_adaptation | +0.0002 | [-0.0032,+0.0036] |
| fixed_episode/20 versus source_no_adaptation | +0.0100 | [-0.0013,+0.0212] |
| fixed_episode/5 versus source_no_adaptation | +0.0010 | [-0.0024,+0.0044] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0003 | [-0.0031,+0.0036] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0100 | [-0.0013,+0.0212] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0010 | [-0.0024,+0.0044] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0099 | [-0.0013,+0.0210] |
| fixed_source/5 versus source_no_adaptation | +0.0008 | [-0.0001,+0.0016] |
| ordinary_selected versus source_no_adaptation | +0.0098 | [-0.0014,+0.0209] |

## fau / fusion/cb_pre / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.3359 | [-0.4205,-0.2512] |
| probability versus fm_direct | +0.0317 | [+0.0065,+0.0570] |
| residual versus fm_direct | -0.1698 | [-0.2393,-0.1002] |
| sc_local versus fm_direct | -0.4135 | [-0.5346,-0.2924] |
| common_linear versus local_direct | -0.1661 | [-0.2140,-0.1182] |
| probability versus local_direct | +0.2015 | [+0.1541,+0.2490] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2437 | [-0.3150,-0.1724] |
| common_linear versus strong_single | -0.3086 | [-0.3892,-0.2281] |
| probability versus strong_single | +0.0590 | [+0.0252,+0.0927] |
| residual versus strong_single | -0.1426 | [-0.2090,-0.0761] |
| sc_local versus strong_single | -0.3863 | [-0.5025,-0.2700] |

## fau / fusion/cb_pre / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1351 | [-0.1744,-0.0959] |
| probability versus fm_direct | +0.0302 | [+0.0100,+0.0503] |
| residual versus fm_direct | -0.1443 | [-0.2033,-0.0853] |
| sc_local versus fm_direct | -0.1715 | [-0.2377,-0.1054] |
| common_linear versus local_direct | +0.0091 | [-0.0294,+0.0477] |
| probability versus local_direct | +0.1744 | [+0.1342,+0.2147] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0272 | [-0.0556,+0.0011] |
| common_linear versus strong_single | -0.1125 | [-0.1585,-0.0664] |
| probability versus strong_single | +0.0528 | [+0.0262,+0.0794] |
| residual versus strong_single | -0.1216 | [-0.1805,-0.0628] |
| sc_local versus strong_single | -0.1489 | [-0.2190,-0.0788] |

## fau / fusion/cb_random / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2578 | [-0.3285,-0.1871] |
| probability versus fm_direct | +0.0659 | [+0.0386,+0.0931] |
| residual versus fm_direct | -0.0636 | [-0.1171,-0.0102] |
| sc_local versus fm_direct | -0.3073 | [-0.4008,-0.2139] |
| common_linear versus local_direct | -0.1941 | [-0.2503,-0.1380] |
| probability versus local_direct | +0.1295 | [+0.1014,+0.1576] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2437 | [-0.3136,-0.1738] |
| common_linear versus strong_single | -0.3367 | [-0.4304,-0.2430] |
| probability versus strong_single | -0.0130 | [-0.0661,+0.0400] |
| residual versus strong_single | -0.1426 | [-0.2077,-0.0774] |
| sc_local versus strong_single | -0.3863 | [-0.5003,-0.2723] |

## fau / fusion/cb_random / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0454 | [-0.0933,+0.0025] |
| probability versus fm_direct | +0.0811 | [+0.0607,+0.1014] |
| residual versus fm_direct | -0.0245 | [-0.0722,+0.0232] |
| sc_local versus fm_direct | -0.0518 | [-0.1058,+0.0023] |
| common_linear versus local_direct | -0.0209 | [-0.0517,+0.0099] |
| probability versus local_direct | +0.1056 | [+0.0758,+0.1355] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0272 | [-0.0567,+0.0022] |
| common_linear versus strong_single | -0.1425 | [-0.2087,-0.0763] |
| probability versus strong_single | -0.0160 | [-0.0647,+0.0326] |
| residual versus strong_single | -0.1216 | [-0.1828,-0.0604] |
| sc_local versus strong_single | -0.1489 | [-0.2218,-0.0759] |

## fau / fusion/reve_pre / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2136 | [-0.2874,-0.1398] |
| probability versus fm_direct | +0.1131 | [+0.0721,+0.1541] |
| residual versus fm_direct | -0.1131 | [-0.1980,-0.0282] |
| sc_local versus fm_direct | -0.3568 | [-0.4803,-0.2333] |
| common_linear versus local_direct | -0.1005 | [-0.1682,-0.0328] |
| probability versus local_direct | +0.2262 | [+0.1804,+0.2720] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2437 | [-0.3145,-0.1729] |
| common_linear versus strong_single | -0.2431 | [-0.3371,-0.1490] |
| probability versus strong_single | +0.0837 | [+0.0227,+0.1446] |
| residual versus strong_single | -0.1426 | [-0.2086,-0.0765] |
| sc_local versus strong_single | -0.3863 | [-0.5018,-0.2707] |

## fau / fusion/reve_pre / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1052 | [-0.1409,-0.0695] |
| probability versus fm_direct | +0.0765 | [+0.0448,+0.1082] |
| residual versus fm_direct | -0.1093 | [-0.1763,-0.0422] |
| sc_local versus fm_direct | -0.1365 | [-0.2124,-0.0607] |
| common_linear versus local_direct | +0.0041 | [-0.0528,+0.0609] |
| probability versus local_direct | +0.1858 | [+0.1481,+0.2235] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0272 | [-0.0566,+0.0021] |
| common_linear versus strong_single | -0.1175 | [-0.1766,-0.0585] |
| probability versus strong_single | +0.0642 | [+0.0130,+0.1153] |
| residual versus strong_single | -0.1216 | [-0.1826,-0.0607] |
| sc_local versus strong_single | -0.1489 | [-0.2215,-0.0763] |

## fau / policy/cbramod/pretrained_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0159 | [+0.0034,+0.0283] |
| declared_window_temporal|0.3 versus base | +0.0163 | [+0.0005,+0.0321] |
| diagonal_spatial|0.1 versus base | +0.0147 | [-0.0017,+0.0311] |
| diagonal_spatial|0.3 versus base | +0.0294 | [+0.0115,+0.0472] |
| full_spatial|0.1 versus base | +0.0444 | [-0.0239,+0.1127] |
| full_spatial|0.3 versus base | +0.2319 | [+0.0080,+0.4557] |
| lowrank_spatial|0.1 versus base | +0.0121 | [-0.0137,+0.0379] |
| lowrank_spatial|0.3 versus base | +0.1040 | [-0.0311,+0.2392] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0236 | [-0.0167,+0.0639] |
| output_low_rank|0.3 versus base | +0.0749 | [-0.0126,+0.1624] |

## fau / policy/cbramod/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0091 | [+0.0027,+0.0154] |
| declared_window_temporal|0.3 versus base | +0.0077 | [+0.0022,+0.0131] |
| diagonal_spatial|0.1 versus base | +0.0039 | [-0.0041,+0.0119] |
| diagonal_spatial|0.3 versus base | +0.0156 | [+0.0053,+0.0259] |
| full_spatial|0.1 versus base | +0.0194 | [-0.0208,+0.0595] |
| full_spatial|0.3 versus base | +0.1481 | [+0.0034,+0.2928] |
| lowrank_spatial|0.1 versus base | +0.0027 | [-0.0174,+0.0228] |
| lowrank_spatial|0.3 versus base | +0.0644 | [-0.0194,+0.1482] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0087 | [-0.0242,+0.0416] |
| output_low_rank|0.3 versus base | +0.0432 | [-0.0100,+0.0964] |

## fau / policy/cbramod/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0102 | [-0.0023,+0.0227] |
| declared_window_temporal|0.3 versus base | +0.0108 | [-0.0038,+0.0253] |
| diagonal_spatial|0.1 versus base | +0.0090 | [-0.0003,+0.0184] |
| diagonal_spatial|0.3 versus base | +0.0159 | [+0.0052,+0.0266] |
| full_spatial|0.1 versus base | +0.0424 | [-0.0281,+0.1128] |
| full_spatial|0.3 versus base | +0.1875 | [+0.0292,+0.3458] |
| lowrank_spatial|0.1 versus base | +0.0074 | [-0.0199,+0.0347] |
| lowrank_spatial|0.3 versus base | +0.0831 | [+0.0014,+0.1648] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0133 | [-0.0188,+0.0454] |
| output_low_rank|0.3 versus base | +0.0649 | [+0.0031,+0.1267] |

## fau / policy/cbramod/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0085 | [-0.0018,+0.0188] |
| declared_window_temporal|0.3 versus base | +0.0095 | [-0.0010,+0.0200] |
| diagonal_spatial|0.1 versus base | +0.0050 | [-0.0027,+0.0127] |
| diagonal_spatial|0.3 versus base | +0.0085 | [+0.0001,+0.0169] |
| full_spatial|0.1 versus base | +0.0241 | [-0.0317,+0.0799] |
| full_spatial|0.3 versus base | +0.1254 | [+0.0074,+0.2435] |
| lowrank_spatial|0.1 versus base | +0.0038 | [-0.0158,+0.0233] |
| lowrank_spatial|0.3 versus base | +0.0535 | [-0.0102,+0.1171] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0116 | [-0.0189,+0.0422] |
| output_low_rank|0.3 versus base | +0.0501 | [-0.0021,+0.1022] |

## fau / policy/local / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0065 | [-0.0009,+0.0138] |
| declared_window_temporal|0.3 versus base | +0.0064 | [-0.0028,+0.0157] |
| diagonal_spatial|0.1 versus base | +0.0197 | [+0.0069,+0.0324] |
| diagonal_spatial|0.3 versus base | +0.0330 | [+0.0199,+0.0461] |
| full_spatial|0.1 versus base | -0.0008 | [-0.0139,+0.0123] |
| full_spatial|0.3 versus base | +0.0785 | [+0.0052,+0.1517] |
| lowrank_spatial|0.1 versus base | +0.0112 | [-0.0103,+0.0326] |
| lowrank_spatial|0.3 versus base | +0.0348 | [-0.0266,+0.0962] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0115 | [-0.0144,+0.0373] |
| output_low_rank|0.3 versus base | +0.0388 | [+0.0043,+0.0734] |

## fau / policy/local / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0031 | [-0.0022,+0.0084] |
| declared_window_temporal|0.3 versus base | +0.0029 | [-0.0032,+0.0090] |
| diagonal_spatial|0.1 versus base | +0.0088 | [-0.0006,+0.0183] |
| diagonal_spatial|0.3 versus base | +0.0160 | [+0.0080,+0.0241] |
| full_spatial|0.1 versus base | +0.0025 | [-0.0101,+0.0150] |
| full_spatial|0.3 versus base | +0.0348 | [-0.0085,+0.0782] |
| lowrank_spatial|0.1 versus base | +0.0037 | [-0.0127,+0.0201] |
| lowrank_spatial|0.3 versus base | +0.0020 | [-0.0391,+0.0431] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0113 | [-0.0155,+0.0380] |
| output_low_rank|0.3 versus base | +0.0210 | [-0.0144,+0.0565] |

## fau / policy/reve/pretrained_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0047 | [-0.0088,+0.0181] |
| declared_window_temporal|0.3 versus base | +0.0133 | [-0.0034,+0.0301] |
| diagonal_spatial|0.1 versus base | +0.0154 | [+0.0010,+0.0299] |
| diagonal_spatial|0.3 versus base | +0.0215 | [+0.0038,+0.0392] |
| full_spatial|0.1 versus base | +0.0189 | [-0.0402,+0.0781] |
| full_spatial|0.3 versus base | +0.1297 | [-0.0016,+0.2609] |
| lowrank_spatial|0.1 versus base | +0.0213 | [-0.0351,+0.0777] |
| lowrank_spatial|0.3 versus base | +0.0715 | [+0.0043,+0.1387] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0315 | [+0.0006,+0.0624] |
| output_low_rank|0.3 versus base | +0.0843 | [+0.0206,+0.1480] |

## fau / policy/reve/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | -0.0005 | [-0.0100,+0.0090] |
| declared_window_temporal|0.3 versus base | +0.0083 | [-0.0037,+0.0203] |
| diagonal_spatial|0.1 versus base | +0.0058 | [-0.0039,+0.0154] |
| diagonal_spatial|0.3 versus base | +0.0099 | [-0.0018,+0.0217] |
| full_spatial|0.1 versus base | +0.0154 | [-0.0254,+0.0562] |
| full_spatial|0.3 versus base | +0.0894 | [-0.0120,+0.1907] |
| lowrank_spatial|0.1 versus base | +0.0056 | [-0.0345,+0.0457] |
| lowrank_spatial|0.3 versus base | +0.0430 | [-0.0143,+0.1003] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0090 | [-0.0141,+0.0320] |
| output_low_rank|0.3 versus base | +0.0437 | [-0.0083,+0.0957] |

## federici / budget/cbramod/pretrained_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0260 | [-0.0653,+0.0133] |
| fixed_0.25 versus historical_selected | -0.0305 | [-0.0769,+0.0158] |
| fixed_0.5 versus historical_selected | -0.0402 | [-0.0740,-0.0064] |
| fixed_1.0 versus historical_selected | -0.0074 | [-0.0358,+0.0210] |
| fixed_2.0 versus historical_selected | -0.0334 | [-0.0799,+0.0131] |
| new_selected versus historical_selected | -0.0305 | [-0.0734,+0.0123] |

## federici / budget/cbramod/pretrained_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0212 | [-0.0501,+0.0077] |
| fixed_0.25 versus historical_selected | -0.0419 | [-0.0744,-0.0093] |
| fixed_0.5 versus historical_selected | -0.0230 | [-0.0495,+0.0036] |
| fixed_1.0 versus historical_selected | -0.0033 | [-0.0263,+0.0196] |
| fixed_2.0 versus historical_selected | -0.0246 | [-0.0587,+0.0096] |
| new_selected versus historical_selected | -0.0207 | [-0.0526,+0.0112] |

## federici / budget/cbramod/random_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0610 | [-0.0929,-0.0291] |
| fixed_0.25 versus historical_selected | -0.0216 | [-0.0571,+0.0139] |
| fixed_0.5 versus historical_selected | -0.0293 | [-0.0606,+0.0020] |
| fixed_1.0 versus historical_selected | -0.0563 | [-0.0916,-0.0210] |
| fixed_2.0 versus historical_selected | -0.1172 | [-0.1682,-0.0662] |
| new_selected versus historical_selected | -0.0643 | [-0.1092,-0.0195] |

## federici / budget/cbramod/random_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0495 | [-0.0779,-0.0210] |
| fixed_0.25 versus historical_selected | +0.0010 | [-0.0399,+0.0419] |
| fixed_0.5 versus historical_selected | +0.0022 | [-0.0295,+0.0340] |
| fixed_1.0 versus historical_selected | -0.0497 | [-0.0925,-0.0069] |
| fixed_2.0 versus historical_selected | -0.0991 | [-0.1532,-0.0451] |
| new_selected versus historical_selected | -0.0548 | [-0.1040,-0.0056] |

## federici / budget/local / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0138 | [-0.0327,+0.0051] |
| fixed_0.25 versus historical_selected | -0.0168 | [-0.0557,+0.0222] |
| fixed_0.5 versus historical_selected | +0.0011 | [-0.0244,+0.0267] |
| fixed_1.0 versus historical_selected | -0.0104 | [-0.0364,+0.0156] |
| fixed_2.0 versus historical_selected | -0.0242 | [-0.0499,+0.0016] |
| new_selected versus historical_selected | -0.0163 | [-0.0412,+0.0087] |

## federici / budget/local / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0072 | [-0.0234,+0.0090] |
| fixed_0.25 versus historical_selected | -0.0054 | [-0.0345,+0.0237] |
| fixed_0.5 versus historical_selected | -0.0053 | [-0.0241,+0.0135] |
| fixed_1.0 versus historical_selected | -0.0196 | [-0.0378,-0.0013] |
| fixed_2.0 versus historical_selected | -0.0268 | [-0.0474,-0.0061] |
| new_selected versus historical_selected | -0.0204 | [-0.0404,-0.0004] |

## federici / budget_models/fixed_0.5 / native

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0408 | [-0.0164,+0.0980] |
| cbramod/pretrained_full versus local | +0.1915 | [+0.0755,+0.3075] |
| cbramod/random_full versus local | +0.1507 | [+0.0631,+0.2382] |
| reve/pretrained_full versus local | +0.1387 | [+0.0523,+0.2251] |
| reve/random_full versus local | +0.1284 | [+0.0297,+0.2271] |
| reve/pretrained_full versus reve/random_full | +0.0103 | [-0.0732,+0.0939] |

## federici / budget_models/fixed_0.5 / unified

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0304 | [-0.0163,+0.0772] |
| cbramod/pretrained_full versus local | +0.1865 | [+0.0900,+0.2829] |
| cbramod/random_full versus local | +0.1560 | [+0.0772,+0.2348] |
| reve/pretrained_full versus local | +0.1385 | [+0.0568,+0.2202] |
| reve/random_full versus local | +0.1700 | [+0.0787,+0.2613] |
| reve/pretrained_full versus reve/random_full | -0.0315 | [-0.0941,+0.0310] |

## federici / budget_models/fixed_1.0 / native

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0948 | [+0.0209,+0.1687] |
| cbramod/pretrained_full versus local | +0.2310 | [+0.1125,+0.3495] |
| cbramod/random_full versus local | +0.1362 | [+0.0604,+0.2120] |
| reve/pretrained_full versus local | -0.0456 | [-0.1404,+0.0493] |
| reve/random_full versus local | +0.2114 | [+0.1207,+0.3020] |
| reve/pretrained_full versus reve/random_full | -0.2569 | [-0.3578,-0.1560] |

## federici / budget_models/fixed_1.0 / unified

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1067 | [+0.0413,+0.1720] |
| cbramod/pretrained_full versus local | +0.2120 | [+0.1106,+0.3135] |
| cbramod/random_full versus local | +0.1054 | [+0.0374,+0.1734] |
| reve/pretrained_full versus local | -0.0032 | [-0.0694,+0.0630] |
| reve/random_full versus local | +0.2132 | [+0.1131,+0.3132] |
| reve/pretrained_full versus reve/random_full | -0.2164 | [-0.3120,-0.1207] |

## federici / budget_models/fixed_2.0 / native

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1471 | [+0.0491,+0.2451] |
| cbramod/pretrained_full versus local | +0.2396 | [+0.1151,+0.3641] |
| cbramod/random_full versus local | +0.0925 | [+0.0212,+0.1638] |
| reve/pretrained_full versus local | -0.0527 | [-0.1228,+0.0175] |
| reve/random_full versus local | +0.2676 | [+0.1649,+0.3703] |
| reve/pretrained_full versus reve/random_full | -0.3203 | [-0.4259,-0.2147] |

## federici / budget_models/fixed_2.0 / unified

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1431 | [+0.0636,+0.2225] |
| cbramod/pretrained_full versus local | +0.2137 | [+0.1160,+0.3114] |
| cbramod/random_full versus local | +0.0706 | [+0.0120,+0.1293] |
| reve/pretrained_full versus local | -0.0420 | [-0.1021,+0.0181] |
| reve/random_full versus local | +0.2242 | [+0.1320,+0.3165] |
| reve/pretrained_full versus reve/random_full | -0.2662 | [-0.3612,-0.1713] |

## federici / budget_models/historical_selected / native

reused historical baseline; not a new training result. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0440 | [-0.0118,+0.0998] |
| cbramod/pretrained_full versus local | +0.2198 | [+0.1162,+0.3235] |
| cbramod/random_full versus local | +0.1758 | [+0.1007,+0.2510] |
| reve/pretrained_full versus local | +0.1093 | [+0.0300,+0.1887] |
| reve/random_full versus local | +0.1702 | [+0.0844,+0.2560] |
| reve/pretrained_full versus reve/random_full | -0.0609 | [-0.1392,+0.0175] |

## federici / budget_models/historical_selected / unified

reused historical baseline; not a new training result. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0548 | [+0.0114,+0.0981] |
| cbramod/pretrained_full versus local | +0.1961 | [+0.1086,+0.2836] |
| cbramod/random_full versus local | +0.1413 | [+0.0655,+0.2171] |
| reve/pretrained_full versus local | +0.0875 | [+0.0194,+0.1556] |
| reve/random_full versus local | +0.1745 | [+0.0871,+0.2620] |
| reve/pretrained_full versus reve/random_full | -0.0871 | [-0.1566,-0.0175] |

## federici / budget_models/new_selected / native

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1104 | [+0.0156,+0.2053] |
| cbramod/pretrained_full versus local | +0.2313 | [+0.1040,+0.3585] |
| cbramod/random_full versus local | +0.1209 | [+0.0398,+0.2020] |
| reve/pretrained_full versus local | -0.0381 | [-0.1115,+0.0353] |
| reve/random_full versus local | +0.2616 | [+0.1586,+0.3646] |
| reve/pretrained_full versus reve/random_full | -0.2997 | [-0.4017,-0.1978] |

## federici / budget_models/new_selected / unified

new production intervention. Paired n=69/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1176 | [+0.0453,+0.1899] |
| cbramod/pretrained_full versus local | +0.2119 | [+0.1127,+0.3111] |
| cbramod/random_full versus local | +0.0943 | [+0.0280,+0.1606] |
| reve/pretrained_full versus local | -0.0336 | [-0.0950,+0.0279] |
| reve/random_full versus local | +0.2246 | [+0.1300,+0.3192] |
| reve/pretrained_full versus reve/random_full | -0.2581 | [-0.3535,-0.1628] |

## federici / data/content/cbramod/pretrained_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1106 | [-0.1658,-0.0553] |
| 0.5 versus full | -0.0426 | [-0.0751,-0.0101] |

## federici / data/content/cbramod/pretrained_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1045 | [-0.1520,-0.0570] |
| 0.5 versus full | -0.0440 | [-0.0720,-0.0160] |

## federici / data/content/cbramod/random_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2206 | [-0.2800,-0.1612] |
| 0.5 versus full | -0.0910 | [-0.1245,-0.0575] |

## federici / data/content/cbramod/random_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1814 | [-0.2362,-0.1267] |
| 0.5 versus full | -0.0723 | [-0.1097,-0.0349] |

## federici / data/content/local / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1613 | [-0.2180,-0.1045] |
| 0.5 versus full | -0.0813 | [-0.1159,-0.0467] |

## federici / data/content/local / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1257 | [-0.1647,-0.0868] |
| 0.5 versus full | -0.0736 | [-0.1028,-0.0443] |

## federici / data/content/reve/pretrained_full / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1422 | [-0.2240,-0.0604] |
| 0.5 versus full | -0.0608 | [-0.1565,+0.0349] |

## federici / data/content/reve/pretrained_full / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0891 | [-0.1474,-0.0309] |
| 0.5 versus full | -0.0219 | [-0.0737,+0.0300] |

## federici / data/content/reve/random_full / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2474 | [-0.3763,-0.1186] |
| 0.5 versus full | -0.0594 | [-0.1380,+0.0192] |

## federici / data/content/reve/random_full / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2202 | [-0.3474,-0.0930] |
| 0.5 versus full | -0.0352 | [-0.0964,+0.0260] |

## federici / data/people/cbramod/pretrained_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1019 | [-0.1525,-0.0513] |
| 0.5 versus full | -0.0564 | [-0.0874,-0.0254] |

## federici / data/people/cbramod/pretrained_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1124 | [-0.1531,-0.0716] |
| 0.5 versus full | -0.0549 | [-0.0848,-0.0249] |

## federici / data/people/cbramod/random_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2338 | [-0.2898,-0.1777] |
| 0.5 versus full | -0.1039 | [-0.1488,-0.0589] |

## federici / data/people/cbramod/random_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1689 | [-0.2217,-0.1161] |
| 0.5 versus full | -0.0952 | [-0.1355,-0.0550] |

## federici / data/people/local / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1471 | [-0.2044,-0.0899] |
| 0.5 versus full | -0.0874 | [-0.1323,-0.0425] |

## federici / data/people/local / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1173 | [-0.1631,-0.0714] |
| 0.5 versus full | -0.0803 | [-0.1153,-0.0454] |

## federici / data/people/reve/pretrained_full / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1369 | [-0.2421,-0.0317] |
| 0.5 versus full | -0.1230 | [-0.2208,-0.0252] |

## federici / data/people/reve/pretrained_full / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0946 | [-0.1766,-0.0126] |
| 0.5 versus full | -0.0644 | [-0.1337,+0.0048] |

## federici / data/people/reve/random_full / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2172 | [-0.3252,-0.1092] |
| 0.5 versus full | -0.0857 | [-0.1396,-0.0318] |

## federici / data/people/reve/random_full / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1914 | [-0.2980,-0.0847] |
| 0.5 versus full | -0.0841 | [-0.1509,-0.0173] |

## federici / data_models/content/0.25 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1738 | [+0.0638,+0.2837] |
| cbramod/pretrained_full versus local | +0.3164 | [+0.1577,+0.4752] |
| cbramod/random_full versus local | +0.1427 | [+0.0532,+0.2321] |
| reve/pretrained_full versus local | +0.1201 | [-0.0068,+0.2470] |
| reve/random_full versus local | +0.1270 | [+0.0285,+0.2256] |
| reve/pretrained_full versus reve/random_full | -0.0069 | [-0.1276,+0.1137] |

## federici / data_models/content/0.25 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1436 | [+0.0682,+0.2189] |
| cbramod/pretrained_full versus local | +0.2631 | [+0.1430,+0.3833] |
| cbramod/random_full versus local | +0.1196 | [+0.0146,+0.2245] |
| reve/pretrained_full versus local | +0.1244 | [+0.0084,+0.2403] |
| reve/random_full versus local | +0.1395 | [+0.0599,+0.2191] |
| reve/pretrained_full versus reve/random_full | -0.0151 | [-0.1210,+0.0908] |

## federici / data_models/content/0.5 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0889 | [-0.0025,+0.1804] |
| cbramod/pretrained_full versus local | +0.2890 | [+0.1099,+0.4680] |
| cbramod/random_full versus local | +0.2000 | [+0.0612,+0.3389] |
| reve/pretrained_full versus local | +0.1056 | [-0.0168,+0.2280] |
| reve/random_full versus local | +0.2192 | [+0.1017,+0.3367] |
| reve/pretrained_full versus reve/random_full | -0.1136 | [-0.2013,-0.0258] |

## federici / data_models/content/0.5 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0967 | [+0.0165,+0.1769] |
| cbramod/pretrained_full versus local | +0.2632 | [+0.1100,+0.4164] |
| cbramod/random_full versus local | +0.1665 | [+0.0533,+0.2797] |
| reve/pretrained_full versus local | +0.1329 | [+0.0210,+0.2448] |
| reve/random_full versus local | +0.2657 | [+0.1067,+0.4248] |
| reve/pretrained_full versus reve/random_full | -0.1328 | [-0.2341,-0.0315] |

## federici / data_models/people/0.25 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1966 | [+0.1171,+0.2761] |
| cbramod/pretrained_full versus local | +0.2930 | [+0.1553,+0.4307] |
| cbramod/random_full versus local | +0.0964 | [-0.0257,+0.2185] |
| reve/pretrained_full versus local | +0.1011 | [-0.0108,+0.2131] |
| reve/random_full versus local | +0.1331 | [+0.0307,+0.2354] |
| reve/pretrained_full versus reve/random_full | -0.0319 | [-0.1344,+0.0705] |

## federici / data_models/people/0.25 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1311 | [+0.0445,+0.2177] |
| cbramod/pretrained_full versus local | +0.2399 | [+0.0932,+0.3865] |
| cbramod/random_full versus local | +0.1088 | [+0.0052,+0.2124] |
| reve/pretrained_full versus local | +0.1110 | [+0.0047,+0.2174] |
| reve/random_full versus local | +0.1603 | [+0.0612,+0.2594] |
| reve/pretrained_full versus reve/random_full | -0.0493 | [-0.1508,+0.0521] |

## federici / data_models/people/0.5 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0927 | [-0.0209,+0.2063] |
| cbramod/pretrained_full versus local | +0.2160 | [+0.0255,+0.4065] |
| cbramod/random_full versus local | +0.1233 | [-0.0110,+0.2576] |
| reve/pretrained_full versus local | +0.0236 | [-0.0991,+0.1462] |
| reve/random_full versus local | +0.1730 | [+0.0190,+0.3271] |
| reve/pretrained_full versus reve/random_full | -0.1494 | [-0.2592,-0.0397] |

## federici / data_models/people/0.5 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0718 | [-0.0165,+0.1600] |
| cbramod/pretrained_full versus local | +0.2227 | [+0.0764,+0.3690] |
| cbramod/random_full versus local | +0.1509 | [+0.0521,+0.2498] |
| reve/pretrained_full versus local | +0.0988 | [+0.0021,+0.1955] |
| reve/random_full versus local | +0.2252 | [+0.0728,+0.3776] |
| reve/pretrained_full versus reve/random_full | -0.1264 | [-0.2389,-0.0140] |

## federici / fusion/cb_pre / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.4275 | [-0.5720,-0.2829] |
| probability versus fm_direct | +0.0011 | [-0.0191,+0.0214] |
| residual versus fm_direct | -0.2199 | [-0.3223,-0.1175] |
| sc_local versus fm_direct | -0.4381 | [-0.5862,-0.2900] |
| common_linear versus local_direct | -0.2076 | [-0.2881,-0.1271] |
| probability versus local_direct | +0.2210 | [+0.1323,+0.3098] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2182 | [-0.3012,-0.1352] |
| common_linear versus strong_single | -0.4252 | [-0.5570,-0.2934] |
| probability versus strong_single | +0.0035 | [-0.0220,+0.0289] |
| residual versus strong_single | -0.2176 | [-0.3119,-0.1232] |
| sc_local versus strong_single | -0.4358 | [-0.5711,-0.3004] |

## federici / fusion/cb_pre / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1888 | [-0.2599,-0.1177] |
| probability versus fm_direct | +0.0062 | [-0.0133,+0.0257] |
| residual versus fm_direct | -0.1961 | [-0.2845,-0.1077] |
| sc_local versus fm_direct | -0.2825 | [-0.3882,-0.1767] |
| common_linear versus local_direct | +0.0073 | [-0.0304,+0.0450] |
| probability versus local_direct | +0.2023 | [+0.1295,+0.2751] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0864 | [-0.1171,-0.0557] |
| common_linear versus strong_single | -0.1781 | [-0.2506,-0.1055] |
| probability versus strong_single | +0.0169 | [-0.0091,+0.0429] |
| residual versus strong_single | -0.1854 | [-0.2735,-0.0973] |
| sc_local versus strong_single | -0.2718 | [-0.3763,-0.1672] |

## federici / fusion/cb_random / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.3758 | [-0.4838,-0.2678] |
| probability versus fm_direct | +0.0071 | [-0.0107,+0.0248] |
| residual versus fm_direct | -0.1759 | [-0.2503,-0.1015] |
| sc_local versus fm_direct | -0.3941 | [-0.5063,-0.2820] |
| common_linear versus local_direct | -0.1999 | [-0.2797,-0.1201] |
| probability versus local_direct | +0.1830 | [+0.1231,+0.2429] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2182 | [-0.3013,-0.1350] |
| common_linear versus strong_single | -0.4175 | [-0.5491,-0.2858] |
| probability versus strong_single | -0.0346 | [-0.0854,+0.0162] |
| residual versus strong_single | -0.2176 | [-0.3121,-0.1231] |
| sc_local versus strong_single | -0.4358 | [-0.5713,-0.3002] |

## federici / fusion/cb_random / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1283 | [-0.1881,-0.0684] |
| probability versus fm_direct | +0.0078 | [-0.0197,+0.0354] |
| residual versus fm_direct | -0.1413 | [-0.2188,-0.0638] |
| sc_local versus fm_direct | -0.2277 | [-0.3186,-0.1368] |
| common_linear versus local_direct | +0.0130 | [-0.0236,+0.0497] |
| probability versus local_direct | +0.1491 | [+0.0921,+0.2062] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0864 | [-0.1174,-0.0553] |
| common_linear versus strong_single | -0.1724 | [-0.2510,-0.0937] |
| probability versus strong_single | -0.0362 | [-0.0860,+0.0135] |
| residual versus strong_single | -0.1854 | [-0.2746,-0.0962] |
| sc_local versus strong_single | -0.2718 | [-0.3776,-0.1659] |

## federici / fusion/reve_pre / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2967 | [-0.4054,-0.1881] |
| probability versus fm_direct | +0.0293 | [-0.0081,+0.0666] |
| residual versus fm_direct | -0.1094 | [-0.1904,-0.0284] |
| sc_local versus fm_direct | -0.3276 | [-0.4489,-0.2063] |
| common_linear versus local_direct | -0.1873 | [-0.2676,-0.1071] |
| probability versus local_direct | +0.1387 | [+0.0897,+0.1877] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2182 | [-0.3040,-0.1324] |
| common_linear versus strong_single | -0.4049 | [-0.5368,-0.2730] |
| probability versus strong_single | -0.0789 | [-0.1584,+0.0007] |
| residual versus strong_single | -0.2176 | [-0.3151,-0.1200] |
| sc_local versus strong_single | -0.4358 | [-0.5756,-0.2959] |

## federici / fusion/reve_pre / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0685 | [-0.1141,-0.0228] |
| probability versus fm_direct | +0.0127 | [-0.0179,+0.0434] |
| residual versus fm_direct | -0.0875 | [-0.1575,-0.0174] |
| sc_local versus fm_direct | -0.1738 | [-0.2552,-0.0925] |
| common_linear versus local_direct | +0.0190 | [-0.0290,+0.0670] |
| probability versus local_direct | +0.1002 | [+0.0535,+0.1468] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0864 | [-0.1176,-0.0551] |
| common_linear versus strong_single | -0.1664 | [-0.2463,-0.0865] |
| probability versus strong_single | -0.0852 | [-0.1567,-0.0137] |
| residual versus strong_single | -0.1854 | [-0.2751,-0.0957] |
| sc_local versus strong_single | -0.2718 | [-0.3782,-0.1653] |
