# FAU/Federici breadth intervention results

Snapshot 2026-10-18T19:44:12.782757+02:00, CPU job 1045980; **interim**.

Seed3401 breadth; independent of the DTU three-seed panel. Strict identity pairing; phantom excluded. Historical baseline comparisons reuse completed records and are not new intervention results.

| Lane | Complete / registered | Failed markers |
|---|---:|---:|
| breadth_budget_v1 | 4 / 75 | 0 |
| breadth_inner_v1 | 36 / 375 | 0 |
| breadth_policy_v1 | 15 / 40 | 0 |
| breadth_fusion_v1 | 6 / 15 | 0 |
| breadth_episode_v1 | 12 / 40 | 0 |

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

## fau / episode/reve/pretrained_full/support_0.1 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0002 | [-0.0002,+0.0006] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0003 | [-0.0002,+0.0007] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0002 | [-0.0002,+0.0006] |
| episode_selected versus ordinary_selected | +0.0003 | [-0.0002,+0.0007] |
| episode_selected versus source_no_adaptation | +0.0114 | [-0.0197,+0.0425] |
| fixed_episode/0 versus source_no_adaptation | -0.0027 | [-0.0310,+0.0256] |
| fixed_episode/20 versus source_no_adaptation | +0.0114 | [-0.0197,+0.0425] |
| fixed_episode/5 versus source_no_adaptation | -0.0017 | [-0.0290,+0.0256] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0029 | [-0.0311,+0.0252] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0111 | [-0.0200,+0.0422] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0019 | [-0.0290,+0.0253] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0134 | [-0.0194,+0.0461] |
| fixed_source/5 versus source_no_adaptation | +0.0011 | [-0.0012,+0.0033] |
| ordinary_selected versus source_no_adaptation | +0.0111 | [-0.0200,+0.0422] |

## fau / episode/reve/pretrained_full/support_0.1 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001,+0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0002,+0.0003] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0001,+0.0002] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0002,+0.0003] |
| episode_selected versus source_no_adaptation | +0.0058 | [-0.0078,+0.0194] |
| fixed_episode/0 versus source_no_adaptation | -0.0010 | [-0.0076,+0.0056] |
| fixed_episode/20 versus source_no_adaptation | +0.0058 | [-0.0078,+0.0194] |
| fixed_episode/5 versus source_no_adaptation | -0.0004 | [-0.0068,+0.0059] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0010 | [-0.0075,+0.0055] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0058 | [-0.0077,+0.0193] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0005 | [-0.0067,+0.0058] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0070 | [-0.0067,+0.0206] |
| fixed_source/5 versus source_no_adaptation | +0.0006 | [-0.0003,+0.0016] |
| ordinary_selected versus source_no_adaptation | +0.0058 | [-0.0077,+0.0193] |

## fau / episode/reve/pretrained_full/support_0.3 / native

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0002 | [-0.0002,+0.0006] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0002 | [-0.0002,+0.0007] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0002 | [-0.0002,+0.0006] |
| episode_selected versus ordinary_selected | +0.0002 | [-0.0002,+0.0007] |
| episode_selected versus source_no_adaptation | +0.0177 | [-0.0291,+0.0646] |
| fixed_episode/0 versus source_no_adaptation | -0.0027 | [-0.0314,+0.0259] |
| fixed_episode/20 versus source_no_adaptation | +0.0177 | [-0.0291,+0.0646] |
| fixed_episode/5 versus source_no_adaptation | -0.0011 | [-0.0289,+0.0266] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0029 | [-0.0314,+0.0256] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0175 | [-0.0293,+0.0643] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0013 | [-0.0289,+0.0263] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0202 | [-0.0259,+0.0663] |
| fixed_source/5 versus source_no_adaptation | +0.0016 | [-0.0019,+0.0051] |
| ordinary_selected versus source_no_adaptation | +0.0175 | [-0.0293,+0.0643] |

## fau / episode/reve/pretrained_full/support_0.3 / unified

new production intervention. Paired n=14/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | +0.0000 | [-0.0001,+0.0002] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.0000 | [-0.0003,+0.0004] |
| fixed_episode/5 versus fixed_ordinary/5 | +0.0000 | [-0.0002,+0.0002] |
| episode_selected versus ordinary_selected | +0.0000 | [-0.0003,+0.0004] |
| episode_selected versus source_no_adaptation | +0.0093 | [-0.0144,+0.0329] |
| fixed_episode/0 versus source_no_adaptation | -0.0010 | [-0.0084,+0.0064] |
| fixed_episode/20 versus source_no_adaptation | +0.0093 | [-0.0144,+0.0329] |
| fixed_episode/5 versus source_no_adaptation | -0.0002 | [-0.0075,+0.0071] |
| fixed_ordinary/0 versus source_no_adaptation | -0.0010 | [-0.0084,+0.0063] |
| fixed_ordinary/20 versus source_no_adaptation | +0.0092 | [-0.0144,+0.0329] |
| fixed_ordinary/5 versus source_no_adaptation | -0.0002 | [-0.0074,+0.0070] |
| fixed_source/0 versus source_no_adaptation | +0.0000 | [+0.0000,+0.0000] |
| fixed_source/20 versus source_no_adaptation | +0.0104 | [-0.0133,+0.0342] |
| fixed_source/5 versus source_no_adaptation | +0.0008 | [-0.0008,+0.0024] |
| ordinary_selected versus source_no_adaptation | +0.0092 | [-0.0144,+0.0329] |

## fau / fusion/cb_pre / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.3015 | [-0.4112,-0.1919] |
| probability versus fm_direct | +0.0318 | [+0.0005,+0.0631] |
| residual versus fm_direct | -0.1432 | [-0.2448,-0.0415] |
| sc_local versus fm_direct | -0.3499 | [-0.5198,-0.1800] |
| common_linear versus local_direct | -0.1584 | [-0.2413,-0.0754] |
| probability versus local_direct | +0.1750 | [+0.1014,+0.2486] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2067 | [-0.3230,-0.0905] |
| common_linear versus strong_single | -0.3015 | [-0.4112,-0.1919] |
| probability versus strong_single | +0.0318 | [+0.0005,+0.0631] |
| residual versus strong_single | -0.1432 | [-0.2448,-0.0415] |
| sc_local versus strong_single | -0.3499 | [-0.5198,-0.1800] |

## fau / fusion/cb_pre / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1211 | [-0.1755,-0.0668] |
| probability versus fm_direct | +0.0361 | [+0.0016,+0.0705] |
| residual versus fm_direct | -0.1250 | [-0.2194,-0.0306] |
| sc_local versus fm_direct | -0.1468 | [-0.2550,-0.0386] |
| common_linear versus local_direct | +0.0039 | [-0.0670,+0.0748] |
| probability versus local_direct | +0.1611 | [+0.0988,+0.2234] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0218 | [-0.0672,+0.0237] |
| common_linear versus strong_single | -0.1211 | [-0.1755,-0.0668] |
| probability versus strong_single | +0.0361 | [+0.0016,+0.0705] |
| residual versus strong_single | -0.1250 | [-0.2194,-0.0306] |
| sc_local versus strong_single | -0.1468 | [-0.2550,-0.0386] |

## fau / fusion/cb_random / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2339 | [-0.3342,-0.1337] |
| probability versus fm_direct | +0.0731 | [+0.0295,+0.1168] |
| residual versus fm_direct | -0.0534 | [-0.1455,+0.0386] |
| sc_local versus fm_direct | -0.2601 | [-0.3999,-0.1204] |
| common_linear versus local_direct | -0.1805 | [-0.2772,-0.0839] |
| probability versus local_direct | +0.1265 | [+0.0755,+0.1776] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2067 | [-0.3243,-0.0891] |
| common_linear versus strong_single | -0.3237 | [-0.4592,-0.1881] |
| probability versus strong_single | -0.0166 | [-0.0917,+0.0584] |
| residual versus strong_single | -0.1432 | [-0.2460,-0.0403] |
| sc_local versus strong_single | -0.3499 | [-0.5218,-0.1780] |

## fau / fusion/cb_random / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0427 | [-0.1554,+0.0699] |
| probability versus fm_direct | +0.0761 | [+0.0349,+0.1172] |
| residual versus fm_direct | -0.0262 | [-0.1349,+0.0825] |
| sc_local versus fm_direct | -0.0480 | [-0.1693,+0.0734] |
| common_linear versus local_direct | -0.0165 | [-0.0716,+0.0386] |
| probability versus local_direct | +0.1023 | [+0.0312,+0.1733] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0218 | [-0.0778,+0.0343] |
| common_linear versus strong_single | -0.1415 | [-0.2602,-0.0228] |
| probability versus strong_single | -0.0227 | [-0.1046,+0.0591] |
| residual versus strong_single | -0.1250 | [-0.2414,-0.0086] |
| sc_local versus strong_single | -0.1468 | [-0.2801,-0.0134] |

## fau / fusion/reve_pre / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2095 | [-0.3425,-0.0766] |
| probability versus fm_direct | +0.1123 | [+0.0240,+0.2007] |
| residual versus fm_direct | -0.1174 | [-0.3004,+0.0656] |
| sc_local versus fm_direct | -0.3241 | [-0.5594,-0.0888] |
| common_linear versus local_direct | -0.0921 | [-0.2332,+0.0489] |
| probability versus local_direct | +0.2298 | [+0.1328,+0.3267] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2067 | [-0.3304,-0.0831] |
| common_linear versus strong_single | -0.2353 | [-0.4038,-0.0667] |
| probability versus strong_single | +0.0866 | [-0.0280,+0.2012] |
| residual versus strong_single | -0.1432 | [-0.2513,-0.0351] |
| sc_local versus strong_single | -0.3499 | [-0.5306,-0.1692] |

## fau / fusion/reve_pre / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1299 | [-0.1834,-0.0764] |
| probability versus fm_direct | +0.0676 | [+0.0084,+0.1267] |
| residual versus fm_direct | -0.1262 | [-0.2622,+0.0097] |
| sc_local versus fm_direct | -0.1480 | [-0.2940,-0.0020] |
| common_linear versus local_direct | -0.0037 | [-0.1234,+0.1160] |
| probability versus local_direct | +0.1938 | [+0.1137,+0.2739] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0218 | [-0.0714,+0.0279] |
| common_linear versus strong_single | -0.1287 | [-0.2424,-0.0151] |
| probability versus strong_single | +0.0688 | [-0.0306,+0.1681] |
| residual versus strong_single | -0.1250 | [-0.2282,-0.0219] |
| sc_local versus strong_single | -0.1468 | [-0.2649,-0.0286] |

## fau / policy/cbramod/pretrained_full / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0153 | [-0.0057,+0.0363] |
| declared_window_temporal|0.3 versus base | +0.0091 | [-0.0044,+0.0226] |
| diagonal_spatial|0.1 versus base | +0.0118 | [-0.0068,+0.0305] |
| diagonal_spatial|0.3 versus base | +0.0241 | [-0.0047,+0.0529] |
| full_spatial|0.1 versus base | +0.0098 | [-0.0775,+0.0972] |
| full_spatial|0.3 versus base | +0.2755 | [-0.3487,+0.8997] |
| lowrank_spatial|0.1 versus base | +0.0099 | [-0.0380,+0.0578] |
| lowrank_spatial|0.3 versus base | +0.1338 | [-0.2634,+0.5310] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0150 | [-0.0302,+0.0602] |
| output_low_rank|0.3 versus base | +0.0600 | [-0.0401,+0.1600] |

## fau / policy/cbramod/pretrained_full / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0110 | [-0.0036,+0.0256] |
| declared_window_temporal|0.3 versus base | +0.0067 | [-0.0019,+0.0153] |
| diagonal_spatial|0.1 versus base | +0.0039 | [-0.0114,+0.0193] |
| diagonal_spatial|0.3 versus base | +0.0178 | [-0.0072,+0.0427] |
| full_spatial|0.1 versus base | +0.0061 | [-0.0642,+0.0764] |
| full_spatial|0.3 versus base | +0.1909 | [-0.2075,+0.5894] |
| lowrank_spatial|0.1 versus base | +0.0098 | [-0.0334,+0.0530] |
| lowrank_spatial|0.3 versus base | +0.0994 | [-0.1457,+0.3446] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0077 | [-0.0312,+0.0466] |
| output_low_rank|0.3 versus base | +0.0553 | [-0.0314,+0.1419] |

## fau / policy/cbramod/random_full / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0011 | [-0.0199,+0.0221] |
| declared_window_temporal|0.3 versus base | +0.0039 | [-0.0182,+0.0261] |
| diagonal_spatial|0.1 versus base | +0.0147 | [-0.0077,+0.0370] |
| diagonal_spatial|0.3 versus base | +0.0168 | [-0.0088,+0.0424] |
| full_spatial|0.1 versus base | +0.0417 | [-0.1143,+0.1976] |
| full_spatial|0.3 versus base | +0.2647 | [-0.1532,+0.6826] |
| lowrank_spatial|0.1 versus base | +0.0103 | [-0.0525,+0.0730] |
| lowrank_spatial|0.3 versus base | +0.0989 | [-0.1031,+0.3009] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0145 | [-0.0376,+0.0665] |
| output_low_rank|0.3 versus base | +0.0573 | [-0.0188,+0.1333] |

## fau / policy/cbramod/random_full / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0026 | [-0.0120,+0.0172] |
| declared_window_temporal|0.3 versus base | +0.0065 | [-0.0120,+0.0250] |
| diagonal_spatial|0.1 versus base | +0.0085 | [-0.0099,+0.0268] |
| diagonal_spatial|0.3 versus base | +0.0113 | [-0.0094,+0.0319] |
| full_spatial|0.1 versus base | +0.0284 | [-0.1080,+0.1648] |
| full_spatial|0.3 versus base | +0.1886 | [-0.1451,+0.5224] |
| lowrank_spatial|0.1 versus base | +0.0072 | [-0.0452,+0.0596] |
| lowrank_spatial|0.3 versus base | +0.0718 | [-0.1004,+0.2440] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0185 | [-0.0349,+0.0720] |
| output_low_rank|0.3 versus base | +0.0433 | [-0.0252,+0.1119] |

## fau / policy/local / native

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0061 | [-0.0124,+0.0245] |
| declared_window_temporal|0.3 versus base | +0.0077 | [-0.0112,+0.0267] |
| diagonal_spatial|0.1 versus base | +0.0221 | [-0.0037,+0.0478] |
| diagonal_spatial|0.3 versus base | +0.0291 | [+0.0031,+0.0551] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| full_spatial|0.3 versus base | +0.0682 | [-0.1322,+0.2686] |
| lowrank_spatial|0.1 versus base | +0.0138 | [-0.0041,+0.0318] |
| lowrank_spatial|0.3 versus base | +0.0309 | [-0.1270,+0.1887] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0092 | [-0.0350,+0.0533] |
| output_low_rank|0.3 versus base | +0.0378 | [-0.0318,+0.1074] |

## fau / policy/local / unified

new production intervention. Paired n=28/67.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| declared_window_temporal|0.1 versus base | +0.0040 | [-0.0086,+0.0166] |
| declared_window_temporal|0.3 versus base | +0.0025 | [-0.0114,+0.0163] |
| diagonal_spatial|0.1 versus base | +0.0108 | [-0.0090,+0.0306] |
| diagonal_spatial|0.3 versus base | +0.0143 | [-0.0020,+0.0305] |
| full_spatial|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| full_spatial|0.3 versus base | +0.0347 | [-0.0632,+0.1327] |
| lowrank_spatial|0.1 versus base | +0.0084 | [-0.0048,+0.0215] |
| lowrank_spatial|0.3 versus base | +0.0123 | [-0.0788,+0.1034] |
| none|0.1 versus base | +0.0000 | [+0.0000,+0.0000] |
| none|0.3 versus base | +0.0000 | [+0.0000,+0.0000] |
| output_low_rank|0.1 versus base | +0.0123 | [-0.0425,+0.0671] |
| output_low_rank|0.3 versus base | +0.0217 | [-0.0513,+0.0947] |

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

## federici / budget/cbramod/pretrained_full / native

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0355 | [-0.1027,+0.0317] |
| fixed_0.25 versus historical_selected | -0.0481 | [-0.1796,+0.0834] |
| fixed_0.5 versus historical_selected | -0.0551 | [-0.1312,+0.0210] |
| fixed_1.0 versus historical_selected | -0.0133 | [-0.0799,+0.0532] |
| fixed_2.0 versus historical_selected | -0.0489 | [-0.1429,+0.0452] |
| new_selected versus historical_selected | -0.0539 | [-0.1414,+0.0335] |

## federici / budget/cbramod/pretrained_full / unified

new production intervention. Paired n=19/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| fixed_2.0 versus fixed_1.0 | -0.0293 | [-0.0968,+0.0383] |
| fixed_0.25 versus historical_selected | -0.0636 | [-0.1291,+0.0020] |
| fixed_0.5 versus historical_selected | -0.0252 | [-0.0752,+0.0249] |
| fixed_1.0 versus historical_selected | -0.0155 | [-0.0585,+0.0275] |
| fixed_2.0 versus historical_selected | -0.0448 | [-0.1149,+0.0253] |
| new_selected versus historical_selected | -0.0368 | [-0.1003,+0.0266] |

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

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.4722 | [-0.7119,-0.2324] |
| probability versus fm_direct | -0.0087 | [-0.0381,+0.0206] |
| residual versus fm_direct | -0.2379 | [-0.4198,-0.0559] |
| sc_local versus fm_direct | -0.4906 | [-0.7395,-0.2417] |
| common_linear versus local_direct | -0.2343 | [-0.3689,-0.0997] |
| probability versus local_direct | +0.2291 | [+0.0629,+0.3954] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2527 | [-0.3939,-0.1114] |
| common_linear versus strong_single | -0.4722 | [-0.7119,-0.2324] |
| probability versus strong_single | -0.0087 | [-0.0381,+0.0206] |
| residual versus strong_single | -0.2379 | [-0.4198,-0.0559] |
| sc_local versus strong_single | -0.4906 | [-0.7395,-0.2417] |

## federici / fusion/cb_pre / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2339 | [-0.3483,-0.1195] |
| probability versus fm_direct | -0.0005 | [-0.0249,+0.0239] |
| residual versus fm_direct | -0.2277 | [-0.3717,-0.0837] |
| sc_local versus fm_direct | -0.3197 | [-0.4846,-0.1549] |
| common_linear versus local_direct | -0.0062 | [-0.0613,+0.0489] |
| probability versus local_direct | +0.2271 | [+0.0969,+0.3574] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0921 | [-0.1341,-0.0501] |
| common_linear versus strong_single | -0.2339 | [-0.3483,-0.1195] |
| probability versus strong_single | -0.0005 | [-0.0249,+0.0239] |
| residual versus strong_single | -0.2277 | [-0.3717,-0.0837] |
| sc_local versus strong_single | -0.3197 | [-0.4846,-0.1549] |

## federici / fusion/cb_random / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.3955 | [-0.5636,-0.2275] |
| probability versus fm_direct | +0.0043 | [-0.0249,+0.0334] |
| residual versus fm_direct | -0.1710 | [-0.2986,-0.0435] |
| sc_local versus fm_direct | -0.4237 | [-0.6045,-0.2429] |
| common_linear versus local_direct | -0.2245 | [-0.3631,-0.0859] |
| probability versus local_direct | +0.1753 | [+0.0668,+0.2838] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2527 | [-0.4004,-0.1050] |
| common_linear versus strong_single | -0.4624 | [-0.7119,-0.2129] |
| probability versus strong_single | -0.0626 | [-0.1807,+0.0555] |
| residual versus strong_single | -0.2379 | [-0.4282,-0.0476] |
| sc_local versus strong_single | -0.4906 | [-0.7508,-0.2303] |

## federici / fusion/cb_random / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.1733 | [-0.2674,-0.0793] |
| probability versus fm_direct | +0.0015 | [-0.0291,+0.0320] |
| residual versus fm_direct | -0.1566 | [-0.2713,-0.0420] |
| sc_local versus fm_direct | -0.2487 | [-0.3761,-0.1213] |
| common_linear versus local_direct | -0.0167 | [-0.0621,+0.0287] |
| probability versus local_direct | +0.1581 | [+0.0557,+0.2605] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0921 | [-0.1356,-0.0486] |
| common_linear versus strong_single | -0.2444 | [-0.3878,-0.1009] |
| probability versus strong_single | -0.0696 | [-0.1668,+0.0276] |
| residual versus strong_single | -0.2277 | [-0.3768,-0.0785] |
| sc_local versus strong_single | -0.3197 | [-0.4905,-0.1489] |

## federici / fusion/reve_pre / native

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.2630 | [-0.4236,-0.1024] |
| probability versus fm_direct | +0.0349 | [-0.0265,+0.0962] |
| residual versus fm_direct | -0.0643 | [-0.2101,+0.0815] |
| sc_local versus fm_direct | -0.3170 | [-0.5009,-0.1331] |
| common_linear versus local_direct | -0.1986 | [-0.3371,-0.0602] |
| probability versus local_direct | +0.0992 | [+0.0108,+0.1876] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.2527 | [-0.3982,-0.1072] |
| common_linear versus strong_single | -0.4365 | [-0.6748,-0.1983] |
| probability versus strong_single | -0.1387 | [-0.2851,+0.0077] |
| residual versus strong_single | -0.2379 | [-0.4253,-0.0504] |
| sc_local versus strong_single | -0.4906 | [-0.7470,-0.2342] |

## federici / fusion/reve_pre / unified

new production intervention. Paired n=37/86.

| Contrast | ΔR bits/query | Simultaneous95% interval |
|---|---:|---:|
| common_linear versus fm_direct | -0.0821 | [-0.1337,-0.0304] |
| probability versus fm_direct | +0.0007 | [-0.0396,+0.0410] |
| residual versus fm_direct | -0.0660 | [-0.1695,+0.0374] |
| sc_local versus fm_direct | -0.1581 | [-0.2705,-0.0457] |
| common_linear versus local_direct | -0.0160 | [-0.0918,+0.0598] |
| probability versus local_direct | +0.0668 | [-0.0107,+0.1442] |
| residual versus local_direct | +0.0000 | [+0.0000,+0.0000] |
| sc_local versus local_direct | -0.0921 | [-0.1358,-0.0484] |
| common_linear versus strong_single | -0.2437 | [-0.3752,-0.1122] |
| probability versus strong_single | -0.1609 | [-0.2801,-0.0417] |
| residual versus strong_single | -0.2277 | [-0.3775,-0.0778] |
| sc_local versus strong_single | -0.3197 | [-0.4913,-0.1481] |
