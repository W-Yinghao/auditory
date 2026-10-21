# FAU/Federici breadth intervention results

Snapshot 2026-10-21T21:48:00.485695+02:00, CPU job 1047358; **complete**.

Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| breadth_budget_v1 | 75 / 75 | 0 |
| breadth_inner_v1 | 375 / 375 | 0 |
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

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0833 | [+0.0462,+0.1203] |
| cbramod/pretrained_full versus local | +0.1421 | [+0.0912,+0.1930] |
| cbramod/random_full versus local | +0.0589 | [+0.0098,+0.1079] |
| reve/pretrained_full versus local | +0.1455 | [+0.0606,+0.2305] |
| reve/random_full versus local | +0.0172 | [-0.0382,+0.0727] |
| reve/pretrained_full versus reve/random_full | +0.1283 | [+0.0359,+0.2207] |

## fau / budget_models/fixed_0.5 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0859 | [+0.0543,+0.1176] |
| cbramod/pretrained_full versus local | +0.1327 | [+0.0701,+0.1953] |
| cbramod/random_full versus local | +0.0468 | [-0.0082,+0.1017] |
| reve/pretrained_full versus local | +0.1175 | [+0.0490,+0.1861] |
| reve/random_full versus local | +0.0456 | [+0.0071,+0.0841] |
| reve/pretrained_full versus reve/random_full | +0.0720 | [+0.0071,+0.1368] |

## fau / budget_models/fixed_1.0 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1071 | [+0.0474,+0.1667] |
| cbramod/pretrained_full versus local | +0.1513 | [+0.0775,+0.2252] |
| cbramod/random_full versus local | +0.0443 | [-0.0009,+0.0895] |
| reve/pretrained_full versus local | -0.0016 | [-0.0876,+0.0845] |
| reve/random_full versus local | +0.0992 | [+0.0522,+0.1461] |
| reve/pretrained_full versus reve/random_full | -0.1008 | [-0.1860,-0.0156] |

## fau / budget_models/fixed_1.0 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1394 | [+0.0960,+0.1828] |
| cbramod/pretrained_full versus local | +0.1270 | [+0.0669,+0.1871] |
| cbramod/random_full versus local | -0.0124 | [-0.0556,+0.0309] |
| reve/pretrained_full versus local | +0.0147 | [-0.0511,+0.0806] |
| reve/random_full versus local | +0.0863 | [+0.0356,+0.1371] |
| reve/pretrained_full versus reve/random_full | -0.0716 | [-0.1292,-0.0140] |

## fau / budget_models/fixed_2.0 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1829 | [+0.1185,+0.2473] |
| cbramod/pretrained_full versus local | +0.1540 | [+0.0841,+0.2239] |
| cbramod/random_full versus local | -0.0289 | [-0.0778,+0.0200] |
| reve/pretrained_full versus local | -0.0881 | [-0.1801,+0.0039] |
| reve/random_full versus local | +0.1329 | [+0.0797,+0.1861] |
| reve/pretrained_full versus reve/random_full | -0.2210 | [-0.3087,-0.1333] |

## fau / budget_models/fixed_2.0 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1503 | [+0.0902,+0.2104] |
| cbramod/pretrained_full versus local | +0.1077 | [+0.0591,+0.1564] |
| cbramod/random_full versus local | -0.0425 | [-0.0785,-0.0066] |
| reve/pretrained_full versus local | -0.0505 | [-0.1169,+0.0159] |
| reve/random_full versus local | +0.0811 | [+0.0276,+0.1346] |
| reve/pretrained_full versus reve/random_full | -0.1316 | [-0.2038,-0.0594] |

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

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1439 | [+0.0816,+0.2062] |
| cbramod/pretrained_full versus local | +0.1442 | [+0.0757,+0.2127] |
| cbramod/random_full versus local | +0.0003 | [-0.0472,+0.0478] |
| reve/pretrained_full versus local | -0.0856 | [-0.1784,+0.0072] |
| reve/random_full versus local | +0.1259 | [+0.0726,+0.1793] |
| reve/pretrained_full versus reve/random_full | -0.2115 | [-0.2995,-0.1235] |

## fau / budget_models/new_selected / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1208 | [+0.0630,+0.1786] |
| cbramod/pretrained_full versus local | +0.1070 | [+0.0570,+0.1569] |
| cbramod/random_full versus local | -0.0139 | [-0.0508,+0.0231] |
| reve/pretrained_full versus local | -0.0500 | [-0.1171,+0.0171] |
| reve/random_full versus local | +0.0767 | [+0.0207,+0.1327] |
| reve/pretrained_full versus reve/random_full | -0.1267 | [-0.2001,-0.0534] |

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

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0053 | [-0.0151,+0.0258] |
| 0.5 versus full | +0.0046 | [-0.0170,+0.0262] |

## fau / data/content/reve/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0083 | [-0.0082,+0.0248] |
| 0.5 versus full | +0.0050 | [-0.0125,+0.0225] |

## fau / data/content/reve/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | +0.0000 | [-0.0000,+0.0000] |
| 0.5 versus full | +0.0000 | [-0.0000,+0.0000] |

## fau / data/content/reve/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.0000 | [-0.0000,+0.0000] |
| 0.5 versus full | -0.0000 | [-0.0000,+0.0000] |

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

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3583 | [-0.4432,-0.2734] |
| 0.5 versus full | -0.2264 | [-0.2920,-0.1609] |

## fau / data/people/reve/pretrained_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2227 | [-0.2777,-0.1678] |
| 0.5 versus full | -0.1621 | [-0.2052,-0.1190] |

## fau / data/people/reve/random_full / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.3568 | [-0.4196,-0.2941] |
| 0.5 versus full | -0.1773 | [-0.2212,-0.1334] |

## fau / data/people/reve/random_full / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1853 | [-0.2390,-0.1316] |
| 0.5 versus full | -0.1083 | [-0.1549,-0.0618] |

## fau / data_models/content/0.25 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0993 | [+0.0484,+0.1501] |
| cbramod/pretrained_full versus local | +0.1748 | [+0.1091,+0.2406] |
| cbramod/random_full versus local | +0.0756 | [+0.0272,+0.1240] |
| reve/pretrained_full versus local | +0.1184 | [+0.0341,+0.2028] |
| reve/random_full versus local | +0.0999 | [+0.0504,+0.1495] |
| reve/pretrained_full versus reve/random_full | +0.0185 | [-0.0633,+0.1003] |

## fau / data_models/content/0.25 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1100 | [+0.0693,+0.1507] |
| cbramod/pretrained_full versus local | +0.1434 | [+0.0831,+0.2038] |
| cbramod/random_full versus local | +0.0335 | [-0.0095,+0.0764] |
| reve/pretrained_full versus local | +0.1176 | [+0.0569,+0.1782] |
| reve/random_full versus local | +0.0992 | [+0.0453,+0.1531] |
| reve/pretrained_full versus reve/random_full | +0.0183 | [-0.0288,+0.0655] |

## fau / data_models/content/0.5 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0995 | [+0.0479,+0.1511] |
| cbramod/pretrained_full versus local | +0.1736 | [+0.1066,+0.2406] |
| cbramod/random_full versus local | +0.0741 | [+0.0256,+0.1225] |
| reve/pretrained_full versus local | +0.1177 | [+0.0337,+0.2016] |
| reve/random_full versus local | +0.0999 | [+0.0503,+0.1496] |
| reve/pretrained_full versus reve/random_full | +0.0177 | [-0.0641,+0.0995] |

## fau / data_models/content/0.5 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1097 | [+0.0679,+0.1515] |
| cbramod/pretrained_full versus local | +0.1428 | [+0.0808,+0.2048] |
| cbramod/random_full versus local | +0.0331 | [-0.0109,+0.0772] |
| reve/pretrained_full versus local | +0.1143 | [+0.0512,+0.1773] |
| reve/random_full versus local | +0.0992 | [+0.0442,+0.1543] |
| reve/pretrained_full versus reve/random_full | +0.0151 | [-0.0348,+0.0650] |

## fau / data_models/people/0.25 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1440 | [+0.0823,+0.2057] |
| cbramod/pretrained_full versus local | +0.1774 | [+0.1114,+0.2433] |
| cbramod/random_full versus local | +0.0334 | [-0.0190,+0.0857] |
| reve/pretrained_full versus local | +0.0715 | [+0.0100,+0.1329] |
| reve/random_full versus local | +0.0597 | [+0.0027,+0.1168] |
| reve/pretrained_full versus reve/random_full | +0.0117 | [-0.0519,+0.0754] |

## fau / data_models/people/0.25 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0837 | [+0.0096,+0.1577] |
| cbramod/pretrained_full versus local | +0.0922 | [+0.0184,+0.1661] |
| cbramod/random_full versus local | +0.0085 | [-0.0406,+0.0576] |
| reve/pretrained_full versus local | +0.0201 | [-0.0310,+0.0713] |
| reve/random_full versus local | +0.0475 | [+0.0039,+0.0911] |
| reve/pretrained_full versus reve/random_full | -0.0274 | [-0.0755,+0.0208] |

## fau / data_models/people/0.5 / native

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1152 | [+0.0555,+0.1749] |
| cbramod/pretrained_full versus local | +0.1796 | [+0.1169,+0.2423] |
| cbramod/random_full versus local | +0.0644 | [+0.0105,+0.1183] |
| reve/pretrained_full versus local | +0.0534 | [-0.0271,+0.1339] |
| reve/random_full versus local | +0.0894 | [+0.0363,+0.1425] |
| reve/pretrained_full versus reve/random_full | -0.0360 | [-0.1184,+0.0464] |

## fau / data_models/people/0.5 / unified

new production intervention. Paired n=67/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0776 | [+0.0303,+0.1248] |
| cbramod/pretrained_full versus local | +0.1065 | [+0.0448,+0.1682] |
| cbramod/random_full versus local | +0.0289 | [-0.0222,+0.0800] |
| reve/pretrained_full versus local | +0.0150 | [-0.0419,+0.0719] |
| reve/random_full versus local | +0.0587 | [+0.0061,+0.1113] |
| reve/pretrained_full versus reve/random_full | -0.0437 | [-0.1049,+0.0175] |

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

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0331 | [-0.0175,+0.0837] |
| cbramod/pretrained_full versus local | +0.1785 | [+0.0748,+0.2822] |
| cbramod/random_full versus local | +0.1454 | [+0.0688,+0.2220] |
| reve/pretrained_full versus local | +0.1400 | [+0.0636,+0.2164] |
| reve/random_full versus local | +0.1201 | [+0.0352,+0.2050] |
| reve/pretrained_full versus reve/random_full | +0.0199 | [-0.0516,+0.0914] |

## federici / budget_models/fixed_0.5 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0296 | [-0.0104,+0.0695] |
| cbramod/pretrained_full versus local | +0.1784 | [+0.0966,+0.2602] |
| cbramod/random_full versus local | +0.1488 | [+0.0839,+0.2138] |
| reve/pretrained_full versus local | +0.1318 | [+0.0628,+0.2009] |
| reve/random_full versus local | +0.1535 | [+0.0752,+0.2318] |
| reve/pretrained_full versus reve/random_full | -0.0217 | [-0.0778,+0.0344] |

## federici / budget_models/fixed_1.0 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0928 | [+0.0310,+0.1547] |
| cbramod/pretrained_full versus local | +0.2228 | [+0.1228,+0.3228] |
| cbramod/random_full versus local | +0.1300 | [+0.0629,+0.1971] |
| reve/pretrained_full versus local | -0.0283 | [-0.1115,+0.0549] |
| reve/random_full versus local | +0.2087 | [+0.1292,+0.2882] |
| reve/pretrained_full versus reve/random_full | -0.2370 | [-0.3242,-0.1498] |

## federici / budget_models/fixed_1.0 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1011 | [+0.0464,+0.1558] |
| cbramod/pretrained_full versus local | +0.2123 | [+0.1285,+0.2961] |
| cbramod/random_full versus local | +0.1112 | [+0.0553,+0.1671] |
| reve/pretrained_full versus local | +0.0052 | [-0.0506,+0.0611] |
| reve/random_full versus local | +0.2133 | [+0.1289,+0.2976] |
| reve/pretrained_full versus reve/random_full | -0.2080 | [-0.2884,-0.1276] |

## federici / budget_models/fixed_2.0 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1278 | [+0.0414,+0.2142] |
| cbramod/pretrained_full versus local | +0.2106 | [+0.0952,+0.3259] |
| cbramod/random_full versus local | +0.0828 | [+0.0168,+0.1487] |
| reve/pretrained_full versus local | -0.0410 | [-0.1063,+0.0244] |
| reve/random_full versus local | +0.2565 | [+0.1676,+0.3454] |
| reve/pretrained_full versus reve/random_full | -0.2975 | [-0.3903,-0.2046] |

## federici / budget_models/fixed_2.0 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1294 | [+0.0602,+0.1985] |
| cbramod/pretrained_full versus local | +0.1983 | [+0.1108,+0.2858] |
| cbramod/random_full versus local | +0.0689 | [+0.0171,+0.1207] |
| reve/pretrained_full versus local | -0.0358 | [-0.0899,+0.0182] |
| reve/random_full versus local | +0.2188 | [+0.1382,+0.2993] |
| reve/pretrained_full versus reve/random_full | -0.2546 | [-0.3387,-0.1705] |

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

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0778 | [-0.0056,+0.1612] |
| cbramod/pretrained_full versus local | +0.2056 | [+0.0914,+0.3198] |
| cbramod/random_full versus local | +0.1278 | [+0.0565,+0.1991] |
| reve/pretrained_full versus local | -0.0141 | [-0.0829,+0.0546] |
| reve/random_full versus local | +0.2522 | [+0.1634,+0.3410] |
| reve/pretrained_full versus reve/random_full | -0.2663 | [-0.3549,-0.1778] |

## federici / budget_models/new_selected / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0889 | [+0.0270,+0.1507] |
| cbramod/pretrained_full versus local | +0.1958 | [+0.1129,+0.2787] |
| cbramod/random_full versus local | +0.1069 | [+0.0527,+0.1611] |
| reve/pretrained_full versus local | -0.0207 | [-0.0725,+0.0312] |
| reve/random_full versus local | +0.2202 | [+0.1425,+0.2980] |
| reve/pretrained_full versus reve/random_full | -0.2409 | [-0.3197,-0.1621] |

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

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1661 | [-0.2300,-0.1022] |
| 0.5 versus full | -0.0636 | [-0.1137,-0.0135] |

## federici / data/content/reve/pretrained_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1377 | [-0.1893,-0.0861] |
| 0.5 versus full | -0.0450 | [-0.0822,-0.0078] |

## federici / data/content/reve/random_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1979 | [-0.2674,-0.1285] |
| 0.5 versus full | -0.0516 | [-0.0914,-0.0119] |

## federici / data/content/reve/random_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1802 | [-0.2566,-0.1039] |
| 0.5 versus full | -0.0384 | [-0.0777,+0.0010] |

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

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1484 | [-0.2234,-0.0734] |
| 0.5 versus full | -0.1079 | [-0.1712,-0.0447] |

## federici / data/people/reve/pretrained_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1074 | [-0.1632,-0.0516] |
| 0.5 versus full | -0.0765 | [-0.1226,-0.0304] |

## federici / data/people/reve/random_full / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.2167 | [-0.2850,-0.1485] |
| 0.5 versus full | -0.0683 | [-0.1007,-0.0358] |

## federici / data/people/reve/random_full / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| 0.25 versus full | -0.1864 | [-0.2599,-0.1128] |
| 0.5 versus full | -0.0717 | [-0.1128,-0.0306] |

## federici / data_models/content/0.25 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1541 | [+0.0958,+0.2123] |
| cbramod/pretrained_full versus local | +0.2705 | [+0.1784,+0.3627] |
| cbramod/random_full versus local | +0.1165 | [+0.0587,+0.1743] |
| reve/pretrained_full versus local | +0.1045 | [+0.0371,+0.1720] |
| reve/random_full versus local | +0.1336 | [+0.0670,+0.2001] |
| reve/pretrained_full versus reve/random_full | -0.0290 | [-0.0921,+0.0340] |

## federici / data_models/content/0.25 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1317 | [+0.0859,+0.1775] |
| cbramod/pretrained_full versus local | +0.2173 | [+0.1381,+0.2964] |
| cbramod/random_full versus local | +0.0856 | [+0.0247,+0.1464] |
| reve/pretrained_full versus local | +0.0754 | [+0.0128,+0.1381] |
| reve/random_full versus local | +0.1200 | [+0.0681,+0.1719] |
| reve/pretrained_full versus reve/random_full | -0.0446 | [-0.0994,+0.0103] |

## federici / data_models/content/0.5 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0924 | [+0.0408,+0.1440] |
| cbramod/pretrained_full versus local | +0.2585 | [+0.1577,+0.3593] |
| cbramod/random_full versus local | +0.1661 | [+0.0860,+0.2462] |
| reve/pretrained_full versus local | +0.1270 | [+0.0571,+0.1968] |
| reve/random_full versus local | +0.1998 | [+0.1263,+0.2734] |
| reve/pretrained_full versus reve/random_full | -0.0729 | [-0.1439,-0.0018] |

## federici / data_models/content/0.5 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0831 | [+0.0328,+0.1335] |
| cbramod/pretrained_full versus local | +0.2257 | [+0.1339,+0.3175] |
| cbramod/random_full versus local | +0.1426 | [+0.0781,+0.2070] |
| reve/pretrained_full versus local | +0.1160 | [+0.0471,+0.1850] |
| reve/random_full versus local | +0.2097 | [+0.1268,+0.2926] |
| reve/pretrained_full versus reve/random_full | -0.0937 | [-0.1534,-0.0340] |

## federici / data_models/people/0.25 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1759 | [+0.1169,+0.2349] |
| cbramod/pretrained_full versus local | +0.2651 | [+0.1656,+0.3646] |
| cbramod/random_full versus local | +0.0892 | [+0.0163,+0.1621] |
| reve/pretrained_full versus local | +0.1081 | [+0.0298,+0.1864] |
| reve/random_full versus local | +0.1006 | [+0.0273,+0.1739] |
| reve/pretrained_full versus reve/random_full | +0.0075 | [-0.0593,+0.0743] |

## federici / data_models/people/0.25 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.1113 | [+0.0535,+0.1691] |
| cbramod/pretrained_full versus local | +0.2010 | [+0.1078,+0.2942] |
| cbramod/random_full versus local | +0.0897 | [+0.0258,+0.1536] |
| reve/pretrained_full versus local | +0.0973 | [+0.0350,+0.1597] |
| reve/random_full versus local | +0.1054 | [+0.0473,+0.1635] |
| reve/pretrained_full versus reve/random_full | -0.0081 | [-0.0684,+0.0523] |

## federici / data_models/people/0.5 / native

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0915 | [+0.0282,+0.1547] |
| cbramod/pretrained_full versus local | +0.2508 | [+0.1408,+0.3608] |
| cbramod/random_full versus local | +0.1594 | [+0.0834,+0.2354] |
| reve/pretrained_full versus local | +0.0888 | [+0.0227,+0.1549] |
| reve/random_full versus local | +0.1894 | [+0.0992,+0.2795] |
| reve/pretrained_full versus reve/random_full | -0.1006 | [-0.1769,-0.0243] |

## federici / data_models/people/0.5 / unified

new production intervention. Paired n=86/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full versus cbramod/random_full | +0.0952 | [+0.0436,+0.1467] |
| cbramod/pretrained_full versus local | +0.2216 | [+0.1307,+0.3124] |
| cbramod/random_full versus local | +0.1264 | [+0.0567,+0.1961] |
| reve/pretrained_full versus local | +0.0913 | [+0.0328,+0.1497] |
| reve/random_full versus local | +0.1831 | [+0.0981,+0.2682] |
| reve/pretrained_full versus reve/random_full | -0.0919 | [-0.1650,-0.0187] |

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
