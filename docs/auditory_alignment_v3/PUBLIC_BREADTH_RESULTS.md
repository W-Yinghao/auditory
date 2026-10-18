# FAU/Federici breadth intervention results

Snapshot 2026-10-18T16:04:13.067949+02:00, CPU job 1045980; **interim**.

Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| breadth_budget_v1 | 0 / 75 | 0 |
| breadth_inner_v1 | 20 / 375 | 0 |
| breadth_policy_v1 | 9 / 40 | 0 |
| breadth_fusion_v1 | 3 / 15 | 0 |
| breadth_episode_v1 | 7 / 40 | 0 |

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

## fau / episode/cbramod/pretrained_full/support_0.1 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0241 | [-0.0135,+0.0617] |
| fixed_episode/0 versus source_no_adaptation | +0.0075 | [-0.0219,+0.0370] |
| fixed_episode/20 versus source_no_adaptation | +0.0241 | [-0.0135,+0.0617] |
| fixed_episode/5 versus source_no_adaptation | +0.0087 | [-0.0207,+0.0382] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0076 | [-0.0219,+0.0370] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0241 | [-0.0135,+0.0617] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0087 | [-0.0207,+0.0382] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0161 | [-0.0075,+0.0397] |
| fixed_source/5 versus source_no_adaptation | +0.0012 | [-0.0004,+0.0028] |
| ordinary_selected versus source_no_adaptation | +0.0241 | [-0.0135,+0.0617] |

## fau / episode/cbramod/pretrained_full/support_0.1 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | -0.0208 | [-0.0676,+0.0259] |
| fixed_episode/0 versus source_no_adaptation | -0.0340 | [-0.0878,+0.0197] |
| fixed_episode/20 versus source_no_adaptation | -0.0208 | [-0.0676,+0.0259] |
| fixed_episode/5 versus source_no_adaptation | -0.0331 | [-0.0861,+0.0199] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0340 | [-0.0878,+0.0198] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0208 | [-0.0676,+0.0259] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0331 | [-0.0861,+0.0200] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0119 | [-0.0099,+0.0337] |
| fixed_source/5 versus source_no_adaptation | +0.0009 | [-0.0005,+0.0023] |
| ordinary_selected versus source_no_adaptation | -0.0208 | [-0.0676,+0.0259] |

## fau / episode/cbramod/pretrained_full/support_0.3 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0313 | [-0.0185,+0.0811] |
| fixed_episode/0 versus source_no_adaptation | +0.0075 | [-0.0275,+0.0426] |
| fixed_episode/20 versus source_no_adaptation | +0.0313 | [-0.0185,+0.0811] |
| fixed_episode/5 versus source_no_adaptation | +0.0091 | [-0.0259,+0.0442] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0076 | [-0.0275,+0.0426] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0313 | [-0.0185,+0.0811] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0091 | [-0.0259,+0.0442] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0236 | [-0.0135,+0.0608] |
| fixed_source/5 versus source_no_adaptation | +0.0016 | [-0.0010,+0.0042] |
| ordinary_selected versus source_no_adaptation | +0.0313 | [-0.0185,+0.0811] |

## fau / episode/cbramod/pretrained_full/support_0.3 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | -0.0126 | [-0.0624,+0.0372] |
| fixed_episode/0 versus source_no_adaptation | -0.0340 | [-0.0872,+0.0192] |
| fixed_episode/20 versus source_no_adaptation | -0.0126 | [-0.0624,+0.0372] |
| fixed_episode/5 versus source_no_adaptation | -0.0326 | [-0.0851,+0.0199] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0340 | [-0.0872,+0.0192] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0126 | [-0.0624,+0.0372] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0326 | [-0.0851,+0.0199] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0204 | [-0.0086,+0.0494] |
| fixed_source/5 versus source_no_adaptation | +0.0013 | [-0.0005,+0.0032] |
| ordinary_selected versus source_no_adaptation | -0.0126 | [-0.0624,+0.0372] |

## fau / episode/cbramod/random_full/support_0.1 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0103 | [-0.0137,+0.0343] |
| fixed_episode/0 versus source_no_adaptation | +0.0006 | [-0.0300,+0.0312] |
| fixed_episode/20 versus source_no_adaptation | +0.0151 | [-0.0175,+0.0478] |
| fixed_episode/5 versus source_no_adaptation | +0.0015 | [-0.0286,+0.0317] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0006 | [-0.0301,+0.0312] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0152 | [-0.0175,+0.0478] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0015 | [-0.0286,+0.0317] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0141 | [-0.0087,+0.0369] |
| fixed_source/5 versus source_no_adaptation | +0.0010 | [-0.0004,+0.0024] |
| ordinary_selected versus source_no_adaptation | +0.0103 | [-0.0137,+0.0343] |

## fau / episode/cbramod/random_full/support_0.1 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | -0.0263 | [-0.0825,+0.0299] |
| fixed_episode/0 versus source_no_adaptation | -0.0398 | [-0.1039,+0.0243] |
| fixed_episode/20 versus source_no_adaptation | -0.0290 | [-0.0867,+0.0287] |
| fixed_episode/5 versus source_no_adaptation | -0.0391 | [-0.1028,+0.0246] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0398 | [-0.1039,+0.0243] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0290 | [-0.0867,+0.0287] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0391 | [-0.1028,+0.0246] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0098 | [-0.0026,+0.0223] |
| fixed_source/5 versus source_no_adaptation | +0.0007 | [+0.0000,+0.0013] |
| ordinary_selected versus source_no_adaptation | -0.0263 | [-0.0825,+0.0300] |

## fau / episode/cbramod/random_full/support_0.3 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0173 | [-0.0271,+0.0616] |
| fixed_episode/0 versus source_no_adaptation | +0.0006 | [-0.0412,+0.0423] |
| fixed_episode/20 versus source_no_adaptation | +0.0213 | [-0.0306,+0.0732] |
| fixed_episode/5 versus source_no_adaptation | +0.0020 | [-0.0391,+0.0430] |
| fixed_ordinary/0 versus source_no_adaptation | +0.0006 | [-0.0412,+0.0424] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0213 | [-0.0306,+0.0732] |
| fixed_ordinary/5 versus source_no_adaptation | +0.0020 | [-0.0391,+0.0430] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0215 | [-0.0233,+0.0662] |
| fixed_source/5 versus source_no_adaptation | +0.0014 | [-0.0015,+0.0044] |
| ordinary_selected versus source_no_adaptation | +0.0173 | [-0.0271,+0.0616] |

## fau / episode/cbramod/random_full/support_0.3 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | -0.0215 | [-0.0840,+0.0410] |
| fixed_episode/0 versus source_no_adaptation | -0.0398 | [-0.1076,+0.0279] |
| fixed_episode/20 versus source_no_adaptation | -0.0247 | [-0.0886,+0.0391] |
| fixed_episode/5 versus source_no_adaptation | -0.0388 | [-0.1061,+0.0284] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0398 | [-0.1076,+0.0279] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0247 | [-0.0886,+0.0391] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0388 | [-0.1061,+0.0285] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0153 | [-0.0081,+0.0387] |
| fixed_source/5 versus source_no_adaptation | +0.0010 | [-0.0005,+0.0025] |
| ordinary_selected versus source_no_adaptation | -0.0215 | [-0.0840,+0.0410] |

## fau / episode/local/support_0.1 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus source_no_adaptation | +0.0058 | [-0.0273,+0.0389] |
| fixed_episode/0 versus source_no_adaptation | -0.0125 | [-0.0281,+0.0030] |
| fixed_episode/20 versus source_no_adaptation | +0.0058 | [-0.0273,+0.0389] |
| fixed_episode/5 versus source_no_adaptation | -0.0111 | [-0.0258,+0.0036] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0125 | [-0.0280,+0.0030] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0058 | [-0.0273,+0.0389] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0111 | [-0.0258,+0.0036] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0176 | [-0.0169,+0.0521] |
| fixed_source/5 versus source_no_adaptation | +0.0014 | [-0.0010,+0.0038] |
| ordinary_selected versus source_no_adaptation | +0.0058 | [-0.0273,+0.0389] |

## fau / episode/local/support_0.1 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001,+0.0000] |
| episode_selected versus source_no_adaptation | -0.0001 | [-0.0217,+0.0216] |
| fixed_episode/0 versus source_no_adaptation | -0.0085 | [-0.0132,-0.0038] |
| fixed_episode/20 versus source_no_adaptation | -0.0001 | [-0.0217,+0.0216] |
| fixed_episode/5 versus source_no_adaptation | -0.0079 | [-0.0126,-0.0031] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0085 | [-0.0132,-0.0038] |
| fixed_ordinary/20 versus source_no_adaptation | -0.0001 | [-0.0217,+0.0216] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0079 | [-0.0126,-0.0031] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0082 | [-0.0124,+0.0288] |
| fixed_source/5 versus source_no_adaptation | +0.0007 | [-0.0006,+0.0019] |
| ordinary_selected versus source_no_adaptation | -0.0001 | [-0.0217,+0.0216] |

## fau / episode/local/support_0.3 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.0000 | [-0.0001,+0.0001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus ordinary_selected | -0.0000 | [-0.0001,+0.0001] |
| episode_selected versus source_no_adaptation | +0.0120 | [-0.0229,+0.0468] |
| fixed_episode/0 versus source_no_adaptation | -0.0125 | [-0.0298,+0.0047] |
| fixed_episode/20 versus source_no_adaptation | +0.0120 | [-0.0229,+0.0468] |
| fixed_episode/5 versus source_no_adaptation | -0.0108 | [-0.0272,+0.0055] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0125 | [-0.0298,+0.0047] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0120 | [-0.0229,+0.0468] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0108 | [-0.0272,+0.0055] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0245 | [-0.0133,+0.0622] |
| fixed_source/5 versus source_no_adaptation | +0.0017 | [-0.0008,+0.0043] |
| ordinary_selected versus source_no_adaptation | +0.0120 | [-0.0229,+0.0468] |

## fau / episode/local/support_0.3 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0000,+0.0000] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0000,+0.0000] |
| episode_selected versus source_no_adaptation | +0.0065 | [-0.0135,+0.0266] |
| fixed_episode/0 versus source_no_adaptation | -0.0085 | [-0.0130,-0.0041] |
| fixed_episode/20 versus source_no_adaptation | +0.0065 | [-0.0135,+0.0266] |
| fixed_episode/5 versus source_no_adaptation | -0.0075 | [-0.0124,-0.0027] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0085 | [-0.0130,-0.0041] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0065 | [-0.0135,+0.0266] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0075 | [-0.0124,-0.0027] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0158 | [-0.0031,+0.0347] |
| fixed_source/5 versus source_no_adaptation | +0.0011 | [-0.0001,+0.0023] |
| ordinary_selected versus source_no_adaptation | +0.0065 | [-0.0135,+0.0266] |

## fau / fusion/cb_pre / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2785 | [-0.4583,-0.0987] |
| probability versus fm_direct | +0.0353 | [-0.0048,+0.0754] |
| residual versus fm_direct | -0.0886 | [-0.2360,+0.0588] |
| sc_local versus fm_direct | -0.2741 | [-0.5883,+0.0402] |
| common_linear versus local_direct | -0.1899 | [-0.3334,-0.0464] |
| probability versus local_direct | +0.1239 | [+0.0152,+0.2326] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1855 | [-0.4251,+0.0541] |
| common_linear versus strong_single | -0.2785 | [-0.4583,-0.0987] |
| probability versus strong_single | +0.0353 | [-0.0048,+0.0754] |
| residual versus strong_single | -0.0886 | [-0.2360,+0.0588] |
| sc_local versus strong_single | -0.2741 | [-0.5883,+0.0402] |

## fau / fusion/cb_pre / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1156 | [-0.2316,+0.0003] |
| probability versus fm_direct | +0.0549 | [-0.0059,+0.1157] |
| residual versus fm_direct | -0.0770 | [-0.2663,+0.1124] |
| sc_local versus fm_direct | -0.1066 | [-0.3151,+0.1019] |
| common_linear versus local_direct | -0.0387 | [-0.1740,+0.0966] |
| probability versus local_direct | +0.1319 | [+0.0018,+0.2619] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0296 | [-0.1026,+0.0434] |
| common_linear versus strong_single | -0.1156 | [-0.2316,+0.0003] |
| probability versus strong_single | +0.0549 | [-0.0059,+0.1157] |
| residual versus strong_single | -0.0770 | [-0.2663,+0.1124] |
| sc_local versus strong_single | -0.1066 | [-0.3151,+0.1019] |

## fau / fusion/cb_random / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2055 | [-0.3526,-0.0584] |
| probability versus fm_direct | +0.0869 | [+0.0147,+0.1591] |
| residual versus fm_direct | +0.0041 | [-0.1446,+0.1529] |
| sc_local versus fm_direct | -0.1813 | [-0.4478,+0.0852] |
| common_linear versus local_direct | -0.2096 | [-0.3828,-0.0364] |
| probability versus local_direct | +0.0828 | [+0.0049,+0.1606] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1855 | [-0.4516,+0.0806] |
| common_linear versus strong_single | -0.2982 | [-0.5399,-0.0565] |
| probability versus strong_single | -0.0058 | [-0.1483,+0.1367] |
| residual versus strong_single | -0.0886 | [-0.2523,+0.0752] |
| sc_local versus strong_single | -0.2741 | [-0.6231,+0.0750] |

## fau / fusion/cb_random / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0061 | [-0.2635,+0.2513] |
| probability versus fm_direct | +0.0904 | [+0.0127,+0.1682] |
| residual versus fm_direct | +0.0233 | [-0.2078,+0.2544] |
| sc_local versus fm_direct | -0.0063 | [-0.2782,+0.2655] |
| common_linear versus local_direct | -0.0294 | [-0.1336,+0.0748] |
| probability versus local_direct | +0.0672 | [-0.0878,+0.2222] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0296 | [-0.1202,+0.0610] |
| common_linear versus strong_single | -0.1064 | [-0.3557,+0.1430] |
| probability versus strong_single | -0.0098 | [-0.1482,+0.1286] |
| residual versus strong_single | -0.0770 | [-0.3120,+0.1580] |
| sc_local versus strong_single | -0.1066 | [-0.3654,+0.1522] |

## fau / fusion/reve_pre / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1463 | [-0.4163,+0.1238] |
| probability versus fm_direct | +0.1578 | [+0.0210,+0.2945] |
| residual versus fm_direct | -0.0271 | [-0.2796,+0.2254] |
| sc_local versus fm_direct | -0.2126 | [-0.6320,+0.2068] |
| common_linear versus local_direct | -0.1191 | [-0.3009,+0.0627] |
| probability versus local_direct | +0.1849 | [+0.0664,+0.3034] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1855 | [-0.4389,+0.0680] |
| common_linear versus strong_single | -0.2077 | [-0.4330,+0.0175] |
| probability versus strong_single | +0.0963 | [-0.0489,+0.2416] |
| residual versus strong_single | -0.0886 | [-0.2446,+0.0674] |
| sc_local versus strong_single | -0.2741 | [-0.6065,+0.0584] |

## fau / fusion/reve_pre / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1260 | [-0.2246,-0.0274] |
| probability versus fm_direct | +0.0846 | [+0.0148,+0.1545] |
| residual versus fm_direct | -0.0560 | [-0.2231,+0.1111] |
| sc_local versus fm_direct | -0.0856 | [-0.2946,+0.1234] |
| common_linear versus local_direct | -0.0700 | [-0.2078,+0.0678] |
| probability versus local_direct | +0.1406 | [+0.0413,+0.2400] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0296 | [-0.1063,+0.0470] |
| common_linear versus strong_single | -0.1470 | [-0.2634,-0.0306] |
| probability versus strong_single | +0.0637 | [-0.0907,+0.2181] |
| residual versus strong_single | -0.0770 | [-0.2757,+0.1218] |
| sc_local versus strong_single | -0.1066 | [-0.3254,+0.1123] |

## fau / policy/cbramod/pretrained_full / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0197 | [-0.0291,+0.0686] |
| declared_window_temporal|0.3 versus base | +0.0135 | [-0.0149,+0.0418] |
| diagonal_spatial|0.1 versus base | +0.0142 | [-0.0418,+0.0702] |
| diagonal_spatial|0.3 versus base | +0.0288 | [-0.0588,+0.1165] |
| full_spatial|0.1 versus base | +0.0162 | [-0.2090,+0.2415] |
| full_spatial|0.3 versus base | +0.3992 | [-1.6396,+2.4380] |
| lowrank_spatial|0.1 versus base | +0.0078 | [-0.1532,+0.1688] |
| lowrank_spatial|0.3 versus base | +0.1890 | [-1.1114,+1.4895] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0238 | [-0.1266,+0.1741] |
| output_low_rank|0.3 versus base | +0.0818 | [-0.1741,+0.3377] |

## fau / policy/cbramod/pretrained_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0193 | [-0.0180,+0.0566] |
| declared_window_temporal|0.3 versus base | +0.0101 | [-0.0128,+0.0329] |
| diagonal_spatial|0.1 versus base | +0.0053 | [-0.0369,+0.0475] |
| diagonal_spatial|0.3 versus base | +0.0236 | [-0.0539,+0.1010] |
| full_spatial|0.1 versus base | +0.0187 | [-0.1373,+0.1748] |
| full_spatial|0.3 versus base | +0.2795 | [-0.9788,+1.5377] |
| lowrank_spatial|0.1 versus base | +0.0124 | [-0.1322,+0.1571] |
| lowrank_spatial|0.3 versus base | +0.1470 | [-0.6165,+0.9104] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0132 | [-0.1165,+0.1429] |
| output_low_rank|0.3 versus base | +0.0673 | [-0.1396,+0.2741] |

## fau / policy/cbramod/random_full / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0075 | [-0.0316,+0.0467] |
| declared_window_temporal|0.3 versus base | +0.0102 | [-0.0397,+0.0601] |
| diagonal_spatial|0.1 versus base | +0.0201 | [-0.0346,+0.0747] |
| diagonal_spatial|0.3 versus base | +0.0274 | [-0.0414,+0.0962] |
| full_spatial|0.1 versus base | +0.0773 | [-0.3483,+0.5029] |
| full_spatial|0.3 versus base | +0.3516 | [-0.6860,+1.3893] |
| lowrank_spatial|0.1 versus base | +0.0267 | [-0.1107,+0.1641] |
| lowrank_spatial|0.3 versus base | +0.1457 | [-0.4144,+0.7057] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0267 | [-0.0657,+0.1191] |
| output_low_rank|0.3 versus base | +0.0814 | [-0.0917,+0.2545] |

## fau / policy/cbramod/random_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0057 | [-0.0322,+0.0436] |
| declared_window_temporal|0.3 versus base | +0.0108 | [-0.0399,+0.0614] |
| diagonal_spatial|0.1 versus base | +0.0116 | [-0.0360,+0.0592] |
| diagonal_spatial|0.3 versus base | +0.0185 | [-0.0439,+0.0810] |
| full_spatial|0.1 versus base | +0.0545 | [-0.3633,+0.4723] |
| full_spatial|0.3 versus base | +0.2601 | [-0.6790,+1.1993] |
| lowrank_spatial|0.1 versus base | +0.0192 | [-0.1172,+0.1556] |
| lowrank_spatial|0.3 versus base | +0.1094 | [-0.4258,+0.6445] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0146 | [-0.0930,+0.1223] |
| output_low_rank|0.3 versus base | +0.0582 | [-0.0971,+0.2136] |

## fau / policy/local / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0119 | [-0.0278,+0.0516] |
| declared_window_temporal|0.3 versus base | +0.0099 | [-0.0334,+0.0533] |
| diagonal_spatial|0.1 versus base | +0.0329 | [-0.0249,+0.0907] |
| diagonal_spatial|0.3 versus base | +0.0382 | [-0.0167,+0.0931] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| full_spatial|0.3 versus base | +0.1150 | [-0.3399,+0.5699] |
| lowrank_spatial|0.1 versus base | +0.0176 | [-0.0207,+0.0558] |
| lowrank_spatial|0.3 versus base | +0.0466 | [-0.3338,+0.4269] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0013 | [-0.1017,+0.1042] |
| output_low_rank|0.3 versus base | +0.0493 | [-0.1027,+0.2013] |

## fau / policy/local / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0066 | [-0.0241,+0.0372] |
| declared_window_temporal|0.3 versus base | +0.0008 | [-0.0339,+0.0355] |
| diagonal_spatial|0.1 versus base | +0.0158 | [-0.0322,+0.0638] |
| diagonal_spatial|0.3 versus base | +0.0171 | [-0.0150,+0.0491] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| full_spatial|0.3 versus base | +0.0646 | [-0.1694,+0.2985] |
| lowrank_spatial|0.1 versus base | +0.0082 | [-0.0200,+0.0363] |
| lowrank_spatial|0.3 versus base | +0.0132 | [-0.2213,+0.2478] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0116 | [-0.1290,+0.1522] |
| output_low_rank|0.3 versus base | +0.0417 | [-0.1241,+0.2075] |

## fau / policy/reve/pretrained_full / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0318 | [-0.0291,+0.0926] |
| declared_window_temporal|0.3 versus base | +0.0330 | [-0.0278,+0.0938] |
| diagonal_spatial|0.1 versus base | +0.0191 | [-0.0092,+0.0474] |
| diagonal_spatial|0.3 versus base | +0.0422 | [-0.0198,+0.1043] |
| full_spatial|0.1 versus base | +0.0574 | [-0.2757,+0.3905] |
| full_spatial|0.3 versus base | +0.1798 | [-0.5042,+0.8639] |
| lowrank_spatial|0.1 versus base | +0.0205 | [-0.2382,+0.2793] |
| lowrank_spatial|0.3 versus base | +0.0691 | [-0.0950,+0.2333] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0271 | [+0.0045,+0.0498] |
| output_low_rank|0.3 versus base | +0.1270 | [-0.0771,+0.3312] |

## fau / policy/reve/pretrained_full / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0112 | [-0.0283,+0.0507] |
| declared_window_temporal|0.3 versus base | +0.0164 | [-0.0316,+0.0643] |
| diagonal_spatial|0.1 versus base | +0.0101 | [-0.0076,+0.0278] |
| diagonal_spatial|0.3 versus base | +0.0208 | [-0.0204,+0.0619] |
| full_spatial|0.1 versus base | +0.0495 | [-0.1898,+0.2888] |
| full_spatial|0.3 versus base | +0.1314 | [-0.3853,+0.6480] |
| lowrank_spatial|0.1 versus base | +0.0080 | [-0.1998,+0.2157] |
| lowrank_spatial|0.3 versus base | +0.0368 | [-0.0948,+0.1684] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0085 | [-0.0078,+0.0248] |
| output_low_rank|0.3 versus base | +0.0528 | [-0.0705,+0.1762] |

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

## federici / fusion/cb_pre / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.4154 | [-0.7652,-0.0656] |
| probability versus fm_direct | +0.0000 | [-0.0000,+0.0000] |
| residual versus fm_direct | -0.1589 | [-0.4471,+0.1292] |
| sc_local versus fm_direct | -0.4356 | [-0.8063,-0.0649] |
| common_linear versus local_direct | -0.2565 | [-0.3843,-0.1286] |
| probability versus local_direct | +0.1589 | [-0.1292,+0.4471] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2767 | [-0.4165,-0.1369] |
| common_linear versus strong_single | -0.4154 | [-0.7652,-0.0656] |
| probability versus strong_single | +0.0000 | [-0.0000,+0.0000] |
| residual versus strong_single | -0.1589 | [-0.4471,+0.1292] |
| sc_local versus strong_single | -0.4356 | [-0.8063,-0.0649] |

## federici / fusion/cb_pre / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2440 | [-0.4070,-0.0811] |
| probability versus fm_direct | -0.0000 | [-0.0000,+0.0000] |
| residual versus fm_direct | -0.1944 | [-0.4386,+0.0499] |
| sc_local versus fm_direct | -0.3082 | [-0.5752,-0.0413] |
| common_linear versus local_direct | -0.0497 | [-0.1534,+0.0541] |
| probability versus local_direct | +0.1944 | [-0.0499,+0.4386] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1139 | [-0.1640,-0.0637] |
| common_linear versus strong_single | -0.2440 | [-0.4070,-0.0811] |
| probability versus strong_single | -0.0000 | [-0.0000,+0.0000] |
| residual versus strong_single | -0.1944 | [-0.4386,+0.0499] |
| sc_local versus strong_single | -0.3082 | [-0.5752,-0.0413] |

## federici / fusion/cb_random / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.3816 | [-0.6138,-0.1494] |
| probability versus fm_direct | +0.0000 | [-0.0000,+0.0000] |
| residual versus fm_direct | -0.1264 | [-0.2861,+0.0332] |
| sc_local versus fm_direct | -0.4031 | [-0.6481,-0.1581] |
| common_linear versus local_direct | -0.2551 | [-0.3912,-0.1190] |
| probability versus local_direct | +0.1264 | [-0.0332,+0.2861] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2767 | [-0.4235,-0.1299] |
| common_linear versus strong_single | -0.4141 | [-0.7857,-0.0425] |
| probability versus strong_single | -0.0325 | [-0.2142,+0.1492] |
| residual versus strong_single | -0.1589 | [-0.4615,+0.1436] |
| sc_local versus strong_single | -0.4356 | [-0.8249,-0.0464] |

## federici / fusion/cb_random / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2096 | [-0.3707,-0.0486] |
| probability versus fm_direct | +0.0000 | [-0.0000,+0.0000] |
| residual versus fm_direct | -0.1919 | [-0.3873,+0.0034] |
| sc_local versus fm_direct | -0.3058 | [-0.5213,-0.0903] |
| common_linear versus local_direct | -0.0177 | [-0.0787,+0.0433] |
| probability versus local_direct | +0.1919 | [-0.0034,+0.3873] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1139 | [-0.1612,-0.0665] |
| common_linear versus strong_single | -0.2121 | [-0.4168,-0.0074] |
| probability versus strong_single | -0.0024 | [-0.0863,+0.0814] |
| residual versus strong_single | -0.1944 | [-0.4250,+0.0363] |
| sc_local versus strong_single | -0.3082 | [-0.5603,-0.0561] |

## federici / fusion/reve_pre / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1817 | [-0.3294,-0.0340] |
| probability versus fm_direct | +0.0725 | [+0.0263,+0.1188] |
| residual versus fm_direct | +0.0515 | [-0.0890,+0.1919] |
| sc_local versus fm_direct | -0.2252 | [-0.4403,-0.0101] |
| common_linear versus local_direct | -0.2332 | [-0.3894,-0.0770] |
| probability versus local_direct | +0.0211 | [-0.0751,+0.1173] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2767 | [-0.4305,-0.1228] |
| common_linear versus strong_single | -0.3921 | [-0.7734,-0.0109] |
| probability versus strong_single | -0.1379 | [-0.4113,+0.1355] |
| residual versus strong_single | -0.1589 | [-0.4761,+0.1582] |
| sc_local versus strong_single | -0.4356 | [-0.8436,-0.0276] |

## federici / fusion/reve_pre / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0618 | [-0.1496,+0.0259] |
| probability versus fm_direct | +0.0000 | [-0.0000,+0.0000] |
| residual versus fm_direct | +0.0017 | [-0.1548,+0.1582] |
| sc_local versus fm_direct | -0.1122 | [-0.2735,+0.0492] |
| common_linear versus local_direct | -0.0635 | [-0.2042,+0.0771] |
| probability versus local_direct | -0.0017 | [-0.1582,+0.1548] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.1139 | [-0.1794,-0.0483] |
| common_linear versus strong_single | -0.2579 | [-0.5468,+0.0310] |
| probability versus strong_single | -0.1960 | [-0.4527,+0.0606] |
| residual versus strong_single | -0.1944 | [-0.5134,+0.1247] |
| sc_local versus strong_single | -0.3082 | [-0.6569,+0.0405] |
