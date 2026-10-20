# FAU/Federici breadth intervention results

Snapshot 2026-10-20T10:05:28.350028+02:00, CPU job 1047358; **interim**.

Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| breadth_budget_v1 | 60 / 75 | 0 |
| breadth_inner_v1 | 277 / 375 | 0 |
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

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0721 | [-0.0048,+0.1490] |
| cbramod/pretrained_full versus local | +0.1172 | [+0.0275,+0.2069] |
| cbramod/random_full versus local | +0.0451 | [-0.0423,+0.1324] |
| reve/pretrained_full versus local | +0.1173 | [-0.0361,+0.2707] |
| reve/random_full versus local | -0.0024 | [-0.1024,+0.0977] |
| reve/pretrained_full versus reve/random_full | +0.1197 | [-0.0566,+0.2960] |

## fau / budget_models/fixed_0.5 / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0678 | [-0.0067,+0.1424] |
| cbramod/pretrained_full versus local | +0.1117 | [+0.0019,+0.2215] |
| cbramod/random_full versus local | +0.0439 | [-0.0485,+0.1362] |
| reve/pretrained_full versus local | +0.0957 | [-0.0347,+0.2262] |
| reve/random_full versus local | +0.0539 | [-0.0083,+0.1161] |
| reve/pretrained_full versus reve/random_full | +0.0419 | [-0.1008,+0.1845] |

## fau / budget_models/fixed_1.0 / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0863 | [-0.0268,+0.1994] |
| cbramod/pretrained_full versus local | +0.1248 | [-0.0230,+0.2725] |
| cbramod/random_full versus local | +0.0385 | [-0.0510,+0.1279] |
| reve/pretrained_full versus local | -0.0145 | [-0.1802,+0.1512] |
| reve/random_full versus local | +0.0899 | [-0.0006,+0.1803] |
| reve/pretrained_full versus reve/random_full | -0.1043 | [-0.2631,+0.0544] |

## fau / budget_models/fixed_1.0 / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1331 | [+0.0543,+0.2119] |
| cbramod/pretrained_full versus local | +0.1203 | [-0.0052,+0.2459] |
| cbramod/random_full versus local | -0.0127 | [-0.1041,+0.0786] |
| reve/pretrained_full versus local | -0.0003 | [-0.1341,+0.1334] |
| reve/random_full versus local | +0.0798 | [+0.0019,+0.1578] |
| reve/pretrained_full versus reve/random_full | -0.0801 | [-0.1904,+0.0301] |

## fau / budget_models/fixed_2.0 / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1794 | [+0.0661,+0.2927] |
| cbramod/pretrained_full versus local | +0.1377 | [+0.0264,+0.2490] |
| cbramod/random_full versus local | -0.0417 | [-0.1228,+0.0394] |
| reve/pretrained_full versus local | -0.1207 | [-0.2979,+0.0565] |
| reve/random_full versus local | +0.1084 | [+0.0114,+0.2053] |
| reve/pretrained_full versus reve/random_full | -0.2291 | [-0.4033,-0.0549] |

## fau / budget_models/fixed_2.0 / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1447 | [+0.0335,+0.2560] |
| cbramod/pretrained_full versus local | +0.1084 | [+0.0290,+0.1878] |
| cbramod/random_full versus local | -0.0363 | [-0.1051,+0.0324] |
| reve/pretrained_full versus local | -0.0549 | [-0.1857,+0.0758] |
| reve/random_full versus local | +0.0486 | [-0.0433,+0.1404] |
| reve/pretrained_full versus reve/random_full | -0.1035 | [-0.2416,+0.0346] |

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

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1237 | [+0.0177,+0.2297] |
| cbramod/pretrained_full versus local | +0.1301 | [+0.0209,+0.2393] |
| cbramod/random_full versus local | +0.0064 | [-0.0741,+0.0869] |
| reve/pretrained_full versus local | -0.1102 | [-0.2938,+0.0733] |
| reve/random_full versus local | +0.1047 | [+0.0035,+0.2058] |
| reve/pretrained_full versus reve/random_full | -0.2149 | [-0.3895,-0.0403] |

## fau / budget_models/new_selected / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0969 | [-0.0053,+0.1992] |
| cbramod/pretrained_full versus local | +0.1093 | [+0.0275,+0.1910] |
| cbramod/random_full versus local | +0.0123 | [-0.0577,+0.0823] |
| reve/pretrained_full versus local | -0.0522 | [-0.1924,+0.0880] |
| reve/random_full versus local | +0.0413 | [-0.0591,+0.1417] |
| reve/pretrained_full versus reve/random_full | -0.0935 | [-0.2366,+0.0497] |

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

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0028 | [-0.0469,+0.0525] |
| 0.5 versus full | +0.0028 | [-0.0469,+0.0525] |

## fau / data/content/reve/pretrained_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0054 | [-0.0368,+0.0475] |
| 0.5 versus full | +0.0054 | [-0.0368,+0.0475] |

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

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1716 | [-0.4181,+0.0749] |
| 0.5 versus full | -0.1345 | [-0.3172,+0.0482] |

## fau / data/people/reve/pretrained_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1532 | [-0.2760,-0.0305] |
| 0.5 versus full | -0.1421 | [-0.2708,-0.0133] |

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

## fau / data_models/people/0.25 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1525 | [-0.0796,+0.3846] |
| cbramod/pretrained_full versus local | +0.1705 | [-0.0315,+0.3725] |
| cbramod/random_full versus local | +0.0180 | [-0.1841,+0.2201] |
| reve/pretrained_full versus local | +0.1153 | [-0.0591,+0.2898] |
| reve/random_full versus local | +0.0122 | [-0.1560,+0.1803] |
| reve/pretrained_full versus reve/random_full | +0.1032 | [-0.1126,+0.3190] |

## fau / data_models/people/0.25 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0915 | [-0.2054,+0.3884] |
| cbramod/pretrained_full versus local | +0.0456 | [-0.3255,+0.4167] |
| cbramod/random_full versus local | -0.0459 | [-0.2494,+0.1576] |
| reve/pretrained_full versus local | +0.0137 | [-0.1702,+0.1976] |
| reve/random_full versus local | -0.0095 | [-0.1703,+0.1514] |
| reve/pretrained_full versus reve/random_full | +0.0232 | [-0.1713,+0.2177] |

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

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0518 | [-0.0432,+0.1469] |
| cbramod/pretrained_full versus local | +0.1927 | [+0.0061,+0.3793] |
| cbramod/random_full versus local | +0.1408 | [+0.0056,+0.2761] |
| reve/pretrained_full versus local | +0.1121 | [-0.0192,+0.2433] |
| reve/random_full versus local | +0.1055 | [-0.0409,+0.2518] |
| reve/pretrained_full versus reve/random_full | +0.0066 | [-0.1076,+0.1208] |

## federici / budget_models/fixed_0.5 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0478 | [-0.0270,+0.1226] |
| cbramod/pretrained_full versus local | +0.2110 | [+0.0675,+0.3545] |
| cbramod/random_full versus local | +0.1632 | [+0.0494,+0.2769] |
| reve/pretrained_full versus local | +0.1337 | [+0.0068,+0.2605] |
| reve/random_full versus local | +0.1843 | [+0.0438,+0.3248] |
| reve/pretrained_full versus reve/random_full | -0.0506 | [-0.1470,+0.0458] |

## federici / budget_models/fixed_1.0 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1145 | [+0.0081,+0.2209] |
| cbramod/pretrained_full versus local | +0.2265 | [+0.0598,+0.3932] |
| cbramod/random_full versus local | +0.1120 | [+0.0136,+0.2103] |
| reve/pretrained_full versus local | -0.0921 | [-0.2160,+0.0319] |
| reve/random_full versus local | +0.2086 | [+0.0877,+0.3295] |
| reve/pretrained_full versus reve/random_full | -0.3007 | [-0.4233,-0.1781] |

## federici / budget_models/fixed_1.0 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1221 | [+0.0256,+0.2186] |
| cbramod/pretrained_full versus local | +0.2185 | [+0.0794,+0.3575] |
| cbramod/random_full versus local | +0.0964 | [+0.0103,+0.1825] |
| reve/pretrained_full versus local | -0.0205 | [-0.1025,+0.0616] |
| reve/random_full versus local | +0.2271 | [+0.0937,+0.3604] |
| reve/pretrained_full versus reve/random_full | -0.2475 | [-0.3768,-0.1182] |

## federici / budget_models/fixed_2.0 / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1678 | [+0.0144,+0.3211] |
| cbramod/pretrained_full versus local | +0.2233 | [+0.0359,+0.4107] |
| cbramod/random_full versus local | +0.0555 | [-0.0516,+0.1626] |
| reve/pretrained_full versus local | -0.1023 | [-0.2077,+0.0031] |
| reve/random_full versus local | +0.2475 | [+0.0908,+0.4041] |
| reve/pretrained_full versus reve/random_full | -0.3498 | [-0.5035,-0.1961] |

## federici / budget_models/fixed_2.0 / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1635 | [+0.0429,+0.2842] |
| cbramod/pretrained_full versus local | +0.2092 | [+0.0736,+0.3448] |
| cbramod/random_full versus local | +0.0457 | [-0.0373,+0.1287] |
| reve/pretrained_full versus local | -0.0693 | [-0.1455,+0.0069] |
| reve/random_full versus local | +0.2213 | [+0.0972,+0.3455] |
| reve/pretrained_full versus reve/random_full | -0.2907 | [-0.4214,-0.1599] |

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

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1676 | [+0.0133,+0.3219] |
| cbramod/pretrained_full versus local | +0.2228 | [+0.0308,+0.4147] |
| cbramod/random_full versus local | +0.0552 | [-0.0511,+0.1615] |
| reve/pretrained_full versus local | -0.1036 | [-0.2114,+0.0042] |
| reve/random_full versus local | +0.2550 | [+0.0975,+0.4126] |
| reve/pretrained_full versus reve/random_full | -0.3586 | [-0.5139,-0.2033] |

## federici / budget_models/new_selected / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1594 | [+0.0485,+0.2703] |
| cbramod/pretrained_full versus local | +0.2159 | [+0.0809,+0.3510] |
| cbramod/random_full versus local | +0.0565 | [-0.0252,+0.1381] |
| reve/pretrained_full versus local | -0.0682 | [-0.1468,+0.0103] |
| reve/random_full versus local | +0.2284 | [+0.1017,+0.3550] |
| reve/pretrained_full versus reve/random_full | -0.2966 | [-0.4296,-0.1636] |

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

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0856 | [-0.1672,-0.0041] |
| 0.5 versus full | -0.0023 | [-0.1185,+0.1139] |

## federici / data/content/reve/pretrained_full / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0581 | [-0.1540,+0.0378] |
| 0.5 versus full | +0.0029 | [-0.0840,+0.0898] |

## federici / data/content/reve/random_full / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2136 | [-0.3646,-0.0626] |
| 0.5 versus full | -0.0564 | [-0.1123,-0.0005] |

## federici / data/content/reve/random_full / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1506 | [-0.3338,+0.0327] |
| 0.5 versus full | -0.0288 | [-0.0896,+0.0321] |

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

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0104 | [-0.1252,+0.1043] |
| 0.5 versus full | -0.0024 | [-0.1005,+0.0957] |

## federici / data/people/reve/pretrained_full / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0230 | [-0.0951,+0.1410] |
| 0.5 versus full | +0.0142 | [-0.0880,+0.1164] |

## federici / data/people/reve/random_full / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2018 | [-0.3743,-0.0294] |
| 0.5 versus full | -0.0841 | [-0.1581,-0.0101] |

## federici / data/people/reve/random_full / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1420 | [-0.3235,+0.0395] |
| 0.5 versus full | -0.0806 | [-0.1554,-0.0059] |

## federici / data_models/content/0.25 / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1178 | [-0.0131,+0.2486] |
| cbramod/pretrained_full versus local | +0.2393 | [+0.0124,+0.4662] |
| cbramod/random_full versus local | +0.1215 | [-0.0214,+0.2644] |
| reve/pretrained_full versus local | +0.0703 | [-0.1615,+0.3021] |
| reve/random_full versus local | +0.1423 | [-0.0035,+0.2880] |
| reve/pretrained_full versus reve/random_full | -0.0720 | [-0.2892,+0.1452] |

## federici / data_models/content/0.25 / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1096 | [+0.0091,+0.2100] |
| cbramod/pretrained_full versus local | +0.2111 | [+0.0376,+0.3845] |
| cbramod/random_full versus local | +0.1015 | [-0.0637,+0.2667] |
| reve/pretrained_full versus local | +0.0551 | [-0.1072,+0.2174] |
| reve/random_full versus local | +0.1340 | [+0.0043,+0.2636] |
| reve/pretrained_full versus reve/random_full | -0.0789 | [-0.2498,+0.0920] |

## federici / data_models/content/0.5 / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0434 | [-0.1189,+0.2058] |
| cbramod/pretrained_full versus local | +0.1913 | [-0.0842,+0.4668] |
| cbramod/random_full versus local | +0.1478 | [-0.0560,+0.3517] |
| reve/pretrained_full versus local | +0.0713 | [-0.1480,+0.2905] |
| reve/random_full versus local | +0.2172 | [+0.0190,+0.4153] |
| reve/pretrained_full versus reve/random_full | -0.1459 | [-0.2818,-0.0101] |

## federici / data_models/content/0.5 / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0592 | [-0.0306,+0.1490] |
| cbramod/pretrained_full versus local | +0.2097 | [-0.0283,+0.4478] |
| cbramod/random_full versus local | +0.1505 | [-0.0558,+0.3569] |
| reve/pretrained_full versus local | +0.0860 | [-0.0788,+0.2507] |
| reve/random_full versus local | +0.2257 | [-0.0082,+0.4596] |
| reve/pretrained_full versus reve/random_full | -0.1397 | [-0.2795,+0.0001] |

## federici / data_models/people/0.25 / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1720 | [+0.0609,+0.2830] |
| cbramod/pretrained_full versus local | +0.2685 | [+0.0630,+0.4739] |
| cbramod/random_full versus local | +0.0965 | [-0.0814,+0.2743] |
| reve/pretrained_full versus local | +0.1427 | [-0.0586,+0.3440] |
| reve/random_full versus local | +0.1513 | [+0.0077,+0.2950] |
| reve/pretrained_full versus reve/random_full | -0.0086 | [-0.1661,+0.1489] |

## federici / data_models/people/0.25 / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1283 | [-0.0136,+0.2703] |
| cbramod/pretrained_full versus local | +0.2294 | [+0.0255,+0.4333] |
| cbramod/random_full versus local | +0.1011 | [-0.0461,+0.2482] |
| reve/pretrained_full versus local | +0.1297 | [-0.0436,+0.3029] |
| reve/random_full versus local | +0.1361 | [+0.0054,+0.2667] |
| reve/pretrained_full versus reve/random_full | -0.0064 | [-0.1898,+0.1770] |

## federici / data_models/people/0.5 / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0652 | [-0.1303,+0.2606] |
| cbramod/pretrained_full versus local | +0.1533 | [-0.1498,+0.4565] |
| cbramod/random_full versus local | +0.0882 | [-0.1192,+0.2955] |
| reve/pretrained_full versus local | +0.0402 | [-0.1722,+0.2526] |
| reve/random_full versus local | +0.1585 | [-0.0122,+0.3292] |
| reve/pretrained_full versus reve/random_full | -0.1183 | [-0.2576,+0.0210] |

## federici / data_models/people/0.5 / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0630 | [-0.0593,+0.1852] |
| cbramod/pretrained_full versus local | +0.1931 | [-0.0329,+0.4191] |
| cbramod/random_full versus local | +0.1301 | [-0.0352,+0.2955] |
| reve/pretrained_full versus local | +0.0759 | [-0.0776,+0.2293] |
| reve/random_full versus local | +0.1524 | [-0.0688,+0.3736] |
| reve/pretrained_full versus reve/random_full | -0.0765 | [-0.2390,+0.0860] |

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
