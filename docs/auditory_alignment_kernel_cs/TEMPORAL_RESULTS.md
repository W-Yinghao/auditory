# Kernel CS-QMI full round: temporal structure

Windows per cohort as in spec §8.3. Δ_{L|E} = R(early) − R(joint), Δ_{E|L} = R(late) − R(joint), with R the query log loss (bits); positive = the other window adds to the first.

## FAU/TUD local: unified/gain_bits by window

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +0.7179 [+0.6360, +0.8030] | +0.1127 [+0.0935, +0.1312] | +0.4161 [+0.3587, +0.4725] | +0.1601 [+0.1388, +0.1818] |
| early | +0.2915 [+0.2515, +0.3316] | +0.0915 [+0.0756, +0.1083] | +0.2383 [+0.2056, +0.2718] | +0.1028 [+0.0854, +0.1199] |
| late | +0.6913 [+0.6075, +0.7747] | +0.1024 [+0.0834, +0.1217] | +0.4820 [+0.4183, +0.5440] | +0.1709 [+0.1451, +0.1961] |
| joint | +0.9119 [+0.7989, +1.0222] | +0.1148 [+0.0953, +0.1333] | +0.6173 [+0.5446, +0.6902] | +0.2908 [+0.2505, +0.3329] |
| late_equalwidth | +0.4292 [+0.3574, +0.4983] | +0.0842 [+0.0629, +0.1060] | +0.2424 [+0.1912, +0.2940] | +0.1247 [+0.1001, +0.1493] |

### FAU/TUD Ac by window (early / late / joint from extension E12)

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +1.0669 [+0.9299, +1.2019] | +0.1483 [+0.1277, +0.1685] | +0.5486 [+0.4863, +0.6140] | +0.2409 [+0.2090, +0.2746] |
| early | +0.4397 [+0.3616, +0.5114] | +0.1009 [+0.0795, +0.1228] | +0.3368 [+0.2812, +0.3914] | +0.1338 [+0.1031, +0.1618] |
| late | +1.1263 [+0.9889, +1.2639] | +0.1350 [+0.1152, +0.1561] | +0.8128 [+0.7188, +0.9054] | +0.3239 [+0.2786, +0.3689] |
| joint | +1.1721 [+1.0139, +1.3169] | +0.1660 [+0.1427, +0.1892] | +0.9510 [+0.8404, +1.0621] | +0.4467 [+0.3853, +0.5084] |

### FAU/TUD Lz by window (early / late / joint from extension E12)

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +0.8967 [+0.7943, +0.9996] | +0.2769 [+0.2338, +0.3226] | +0.5919 [+0.5122, +0.6700] | +0.2955 [+0.2554, +0.3349] |
| early | +0.3523 [+0.3023, +0.4029] | +0.0899 [+0.0708, +0.1100] | +0.3022 [+0.2599, +0.3445] | +0.1335 [+0.1128, +0.1554] |
| late | +0.8645 [+0.7547, +0.9762] | +0.1756 [+0.1446, +0.2088] | +0.6466 [+0.5598, +0.7333] | +0.2610 [+0.2269, +0.2956] |
| joint | +0.9908 [+0.8741, +1.1077] | +0.1912 [+0.1542, +0.2300] | +0.7347 [+0.6460, +0.8217] | +0.3233 [+0.2799, +0.3657] |

### FAU/TUD: Δ by group

| method target | readout | Δ | group | bits |
|---|---|---|---|---|
| NCE local | native | Delta_L_given_E | ci | +0.2012 [-0.0038, +0.4112] |
| NCE local | native | Delta_L_given_E | ha | +0.8858 [+0.7446, +1.0302] |
| NCE local | native | Delta_L_given_E | th | +0.6180 [+0.3570, +0.9093] |
| NCE local | native | Delta_L_given_E | all | +0.5846 [+0.4530, +0.7119] |
| NCE local | native | Delta_E_given_L | ci | +0.0223 [-0.0782, +0.1108] |
| NCE local | native | Delta_E_given_L | ha | +0.1259 [+0.0933, +0.1612] |
| NCE local | native | Delta_E_given_L | th | +0.1005 [+0.0525, +0.1531] |
| NCE local | native | Delta_E_given_L | all | +0.0835 [+0.0391, +0.1220] |
| NCE local | native | Delta_L_given_E ci-th | group difference | -0.4168 [-0.7677, -0.0957] |
| NCE local | native | Delta_E_given_L ci-th | group difference | -0.0782 [-0.1882, +0.0239] |
| NCE local | native | Delta_L_given_E ha-th | group difference | +0.2678 [-0.0505, +0.5682] |
| NCE local | native | Delta_E_given_L ha-th | group difference | +0.0253 [-0.0350, +0.0861] |
| NCE local | unified | Delta_L_given_E | ci | -0.0488 [-0.2045, +0.1077] |
| NCE local | unified | Delta_L_given_E | ha | +0.4395 [+0.3480, +0.5314] |
| NCE local | unified | Delta_L_given_E | th | +0.2886 [+0.1392, +0.4533] |
| NCE local | unified | Delta_L_given_E | all | +0.2330 [+0.1401, +0.3209] |
| NCE local | unified | Delta_E_given_L | ci | -0.0684 [-0.1433, +0.0008] |
| NCE local | unified | Delta_E_given_L | ha | +0.0923 [+0.0613, +0.1237] |
| NCE local | unified | Delta_E_given_L | th | +0.0826 [+0.0306, +0.1383] |
| NCE local | unified | Delta_E_given_L | all | +0.0327 [-0.0040, +0.0662] |
| NCE local | unified | Delta_L_given_E ci-th | group difference | -0.3374 [-0.5622, -0.1216] |
| NCE local | unified | Delta_E_given_L ci-th | group difference | -0.1510 [-0.2412, -0.0650] |
| NCE local | unified | Delta_L_given_E ha-th | group difference | +0.1509 [-0.0287, +0.3290] |
| NCE local | unified | Delta_E_given_L ha-th | group difference | +0.0097 [-0.0526, +0.0691] |
| FMCA local | native | Delta_L_given_E | ci | +0.0276 [+0.0046, +0.0522] |
| FMCA local | native | Delta_L_given_E | ha | +0.0872 [+0.0609, +0.1190] |
| FMCA local | native | Delta_L_given_E | th | +0.0919 [+0.0575, +0.1275] |
| FMCA local | native | Delta_L_given_E | all | +0.0669 [+0.0492, +0.0861] |
| FMCA local | native | Delta_E_given_L | ci | +0.0042 [-0.0049, +0.0125] |
| FMCA local | native | Delta_E_given_L | ha | +0.0179 [+0.0072, +0.0289] |
| FMCA local | native | Delta_E_given_L | th | +0.0146 [+0.0030, +0.0265] |
| FMCA local | native | Delta_E_given_L | all | +0.0123 [+0.0062, +0.0186] |
| FMCA local | native | Delta_L_given_E ci-th | group difference | -0.0643 [-0.1072, -0.0212] |
| FMCA local | native | Delta_E_given_L ci-th | group difference | -0.0105 [-0.0247, +0.0039] |
| FMCA local | native | Delta_L_given_E ha-th | group difference | -0.0047 [-0.0505, +0.0416] |
| FMCA local | native | Delta_E_given_L ha-th | group difference | +0.0033 [-0.0126, +0.0195] |
| FMCA local | unified | Delta_L_given_E | ci | -0.0024 [-0.0323, +0.0258] |
| FMCA local | unified | Delta_L_given_E | ha | +0.0215 [+0.0025, +0.0402] |
| FMCA local | unified | Delta_L_given_E | th | +0.0110 [-0.0108, +0.0329] |
| FMCA local | unified | Delta_L_given_E | all | +0.0107 [-0.0040, +0.0241] |
| FMCA local | unified | Delta_E_given_L | ci | -0.0036 [-0.0145, +0.0068] |
| FMCA local | unified | Delta_E_given_L | ha | +0.0047 [-0.0052, +0.0142] |
| FMCA local | unified | Delta_E_given_L | th | +0.0020 [-0.0037, +0.0080] |
| FMCA local | unified | Delta_E_given_L | all | +0.0012 [-0.0046, +0.0072] |
| FMCA local | unified | Delta_L_given_E ci-th | group difference | -0.0134 [-0.0504, +0.0213] |
| FMCA local | unified | Delta_E_given_L ci-th | group difference | -0.0056 [-0.0181, +0.0064] |
| FMCA local | unified | Delta_L_given_E ha-th | group difference | +0.0104 [-0.0187, +0.0386] |
| FMCA local | unified | Delta_E_given_L ha-th | group difference | +0.0027 [-0.0087, +0.0137] |
| CS_SINGLE local | native | Delta_L_given_E | ci | +0.0666 [-0.0106, +0.1478] |
| CS_SINGLE local | native | Delta_L_given_E | ha | +0.2171 [+0.1508, +0.2832] |
| CS_SINGLE local | native | Delta_L_given_E | th | +0.1631 [+0.0688, +0.2577] |
| CS_SINGLE local | native | Delta_L_given_E | all | +0.1519 [+0.1034, +0.1987] |
| CS_SINGLE local | native | Delta_E_given_L | ci | +0.0001 [-0.0283, +0.0258] |
| CS_SINGLE local | native | Delta_E_given_L | ha | +0.0332 [+0.0146, +0.0520] |
| CS_SINGLE local | native | Delta_E_given_L | th | +0.0211 [+0.0050, +0.0378] |
| CS_SINGLE local | native | Delta_E_given_L | all | +0.0188 [+0.0054, +0.0325] |
| CS_SINGLE local | native | Delta_L_given_E ci-th | group difference | -0.0965 [-0.2200, +0.0270] |
| CS_SINGLE local | native | Delta_E_given_L ci-th | group difference | -0.0210 [-0.0535, +0.0094] |
| CS_SINGLE local | native | Delta_L_given_E ha-th | group difference | +0.0540 [-0.0652, +0.1673] |
| CS_SINGLE local | native | Delta_E_given_L ha-th | group difference | +0.0122 [-0.0122, +0.0360] |
| CS_SINGLE local | unified | Delta_L_given_E | ci | +0.0121 [-0.0854, +0.1120] |
| CS_SINGLE local | unified | Delta_L_given_E | ha | +0.2837 [+0.2206, +0.3503] |
| CS_SINGLE local | unified | Delta_L_given_E | th | +0.2133 [+0.1096, +0.3248] |
| CS_SINGLE local | unified | Delta_L_given_E | all | +0.1717 [+0.1129, +0.2281] |
| CS_SINGLE local | unified | Delta_E_given_L | ci | -0.0141 [-0.0475, +0.0186] |
| CS_SINGLE local | unified | Delta_E_given_L | ha | +0.0592 [+0.0372, +0.0814] |
| CS_SINGLE local | unified | Delta_E_given_L | th | +0.0786 [+0.0512, +0.1082] |
| CS_SINGLE local | unified | Delta_E_given_L | all | +0.0370 [+0.0184, +0.0551] |
| CS_SINGLE local | unified | Delta_L_given_E ci-th | group difference | -0.2012 [-0.3462, -0.0594] |
| CS_SINGLE local | unified | Delta_E_given_L ci-th | group difference | -0.0928 [-0.1367, -0.0497] |
| CS_SINGLE local | unified | Delta_L_given_E ha-th | group difference | +0.0704 [-0.0584, +0.1941] |
| CS_SINGLE local | unified | Delta_E_given_L ha-th | group difference | -0.0194 [-0.0537, +0.0158] |
| CS_MULTI local | native | Delta_L_given_E | ci | +0.0089 [+0.0014, +0.0168] |
| CS_MULTI local | native | Delta_L_given_E | ha | +0.0372 [+0.0316, +0.0432] |
| CS_MULTI local | native | Delta_L_given_E | th | +0.0252 [+0.0147, +0.0365] |
| CS_MULTI local | native | Delta_L_given_E | all | +0.0246 [+0.0193, +0.0299] |
| CS_MULTI local | native | Delta_E_given_L | ci | +0.0072 [+0.0016, +0.0129] |
| CS_MULTI local | native | Delta_E_given_L | ha | +0.0245 [+0.0202, +0.0290] |
| CS_MULTI local | native | Delta_E_given_L | th | +0.0163 [+0.0101, +0.0227] |
| CS_MULTI local | native | Delta_E_given_L | all | +0.0166 [+0.0131, +0.0202] |
| CS_MULTI local | native | Delta_L_given_E ci-th | group difference | -0.0163 [-0.0297, -0.0032] |
| CS_MULTI local | native | Delta_E_given_L ci-th | group difference | -0.0090 [-0.0175, -0.0007] |
| CS_MULTI local | native | Delta_L_given_E ha-th | group difference | +0.0120 [-0.0004, +0.0243] |
| CS_MULTI local | native | Delta_E_given_L ha-th | group difference | +0.0082 [+0.0006, +0.0158] |
| CS_MULTI local | unified | Delta_L_given_E | ci | -0.0050 [-0.0573, +0.0482] |
| CS_MULTI local | unified | Delta_L_given_E | ha | +0.1641 [+0.1218, +0.2086] |
| CS_MULTI local | unified | Delta_L_given_E | th | +0.0969 [+0.0381, +0.1571] |
| CS_MULTI local | unified | Delta_L_given_E | all | +0.0895 [+0.0551, +0.1239] |
| CS_MULTI local | unified | Delta_E_given_L | ci | -0.0014 [-0.0292, +0.0266] |
| CS_MULTI local | unified | Delta_E_given_L | ha | +0.0934 [+0.0705, +0.1171] |
| CS_MULTI local | unified | Delta_E_given_L | th | +0.0850 [+0.0516, +0.1244] |
| CS_MULTI local | unified | Delta_E_given_L | all | +0.0577 [+0.0383, +0.0768] |
| CS_MULTI local | unified | Delta_L_given_E ci-th | group difference | -0.1020 [-0.1829, -0.0230] |
| CS_MULTI local | unified | Delta_E_given_L ci-th | group difference | -0.0864 [-0.1327, -0.0419] |
| CS_MULTI local | unified | Delta_L_given_E ha-th | group difference | +0.0672 [-0.0065, +0.1414] |
| CS_MULTI local | unified | Delta_E_given_L ha-th | group difference | +0.0085 [-0.0370, +0.0486] |
| NCE Ac | native | Delta_L_given_E | ci | +0.1505 [-0.0235, +0.3259] |
| NCE Ac | native | Delta_L_given_E | ha | +0.7507 [+0.6226, +0.8786] |
| NCE Ac | native | Delta_L_given_E | th | +0.4791 [+0.2501, +0.7251] |
| NCE Ac | native | Delta_L_given_E | all | +0.4790 [+0.3661, +0.5898] |
| NCE Ac | native | Delta_E_given_L | ci | -0.0382 [-0.1329, +0.0426] |
| NCE Ac | native | Delta_E_given_L | ha | +0.0924 [+0.0610, +0.1260] |
| NCE Ac | native | Delta_E_given_L | th | +0.0614 [-0.0034, +0.1246] |
| NCE Ac | native | Delta_E_given_L | all | +0.0392 [-0.0037, +0.0752] |
| NCE Ac | native | Delta_L_given_E ci-th | group difference | -0.3286 [-0.6276, -0.0458] |
| NCE Ac | native | Delta_E_given_L ci-th | group difference | -0.0995 [-0.2111, +0.0033] |
| NCE Ac | native | Delta_L_given_E ha-th | group difference | +0.2716 [-0.0096, +0.5339] |
| NCE Ac | native | Delta_E_given_L ha-th | group difference | +0.0311 [-0.0388, +0.1042] |
| NCE Ac | unified | Delta_L_given_E | ci | +0.1228 [-0.0775, +0.3254] |
| NCE Ac | unified | Delta_L_given_E | ha | +0.6153 [+0.4934, +0.7392] |
| NCE Ac | unified | Delta_L_given_E | th | +0.2828 [+0.1045, +0.4744] |
| NCE Ac | unified | Delta_L_given_E | all | +0.3694 [+0.2613, +0.4769] |
| NCE Ac | unified | Delta_E_given_L | ci | -0.0501 [-0.1504, +0.0346] |
| NCE Ac | unified | Delta_E_given_L | ha | +0.0570 [+0.0348, +0.0777] |
| NCE Ac | unified | Delta_E_given_L | th | +0.0629 [+0.0251, +0.0966] |
| NCE Ac | unified | Delta_E_given_L | all | +0.0198 [-0.0213, +0.0537] |
| NCE Ac | unified | Delta_L_given_E ci-th | group difference | -0.1599 [-0.4383, +0.1060] |
| NCE Ac | unified | Delta_E_given_L ci-th | group difference | -0.1130 [-0.2196, -0.0181] |
| NCE Ac | unified | Delta_L_given_E ha-th | group difference | +0.3325 [+0.1052, +0.5559] |
| NCE Ac | unified | Delta_E_given_L ha-th | group difference | -0.0059 [-0.0475, +0.0374] |
| FMCA Ac | native | Delta_L_given_E | ci | +0.0193 [-0.0017, +0.0411] |
| FMCA Ac | native | Delta_L_given_E | ha | +0.0726 [+0.0499, +0.0978] |
| FMCA Ac | native | Delta_L_given_E | th | +0.0605 [+0.0318, +0.0898] |
| FMCA Ac | native | Delta_L_given_E | all | +0.0510 [+0.0364, +0.0665] |
| FMCA Ac | native | Delta_E_given_L | ci | +0.0088 [-0.0067, +0.0237] |
| FMCA Ac | native | Delta_E_given_L | ha | +0.0180 [+0.0056, +0.0311] |
| FMCA Ac | native | Delta_E_given_L | th | +0.0202 [+0.0093, +0.0313] |
| FMCA Ac | native | Delta_E_given_L | all | +0.0151 [+0.0071, +0.0235] |
| FMCA Ac | native | Delta_L_given_E ci-th | group difference | -0.0412 [-0.0761, -0.0060] |
| FMCA Ac | native | Delta_E_given_L ci-th | group difference | -0.0114 [-0.0304, +0.0070] |
| FMCA Ac | native | Delta_L_given_E ha-th | group difference | +0.0121 [-0.0251, +0.0503] |
| FMCA Ac | native | Delta_E_given_L ha-th | group difference | -0.0022 [-0.0196, +0.0149] |
| FMCA Ac | unified | Delta_L_given_E | ci | +0.0372 [+0.0129, +0.0605] |
| FMCA Ac | unified | Delta_L_given_E | ha | +0.0497 [+0.0309, +0.0685] |
| FMCA Ac | unified | Delta_L_given_E | th | +0.0061 [-0.0240, +0.0368] |
| FMCA Ac | unified | Delta_L_given_E | all | +0.0361 [+0.0216, +0.0496] |
| FMCA Ac | unified | Delta_E_given_L | ci | +0.0105 [-0.0088, +0.0287] |
| FMCA Ac | unified | Delta_E_given_L | ha | +0.0266 [+0.0172, +0.0366] |
| FMCA Ac | unified | Delta_E_given_L | th | +0.0141 [+0.0028, +0.0255] |
| FMCA Ac | unified | Delta_E_given_L | all | +0.0182 [+0.0096, +0.0263] |
| FMCA Ac | unified | Delta_L_given_E ci-th | group difference | +0.0311 [-0.0088, +0.0688] |
| FMCA Ac | unified | Delta_E_given_L ci-th | group difference | -0.0036 [-0.0258, +0.0177] |
| FMCA Ac | unified | Delta_L_given_E ha-th | group difference | +0.0436 [+0.0079, +0.0789] |
| FMCA Ac | unified | Delta_E_given_L ha-th | group difference | +0.0126 [-0.0030, +0.0277] |
| CS_SINGLE Ac | native | Delta_L_given_E | ci | +0.0672 [+0.0121, +0.1222] |
| CS_SINGLE Ac | native | Delta_L_given_E | ha | +0.1467 [+0.0943, +0.2016] |
| CS_SINGLE Ac | native | Delta_L_given_E | th | +0.0666 [-0.0114, +0.1395] |
| CS_SINGLE Ac | native | Delta_L_given_E | all | +0.1015 [+0.0663, +0.1354] |
| CS_SINGLE Ac | native | Delta_E_given_L | ci | +0.0107 [-0.0211, +0.0420] |
| CS_SINGLE Ac | native | Delta_E_given_L | ha | +0.0670 [+0.0441, +0.0921] |
| CS_SINGLE Ac | native | Delta_E_given_L | th | +0.0333 [+0.0079, +0.0611] |
| CS_SINGLE Ac | native | Delta_E_given_L | all | +0.0398 [+0.0225, +0.0577] |
| CS_SINGLE Ac | native | Delta_L_given_E ci-th | group difference | +0.0006 [-0.0917, +0.0931] |
| CS_SINGLE Ac | native | Delta_E_given_L ci-th | group difference | -0.0225 [-0.0644, +0.0173] |
| CS_SINGLE Ac | native | Delta_L_given_E ha-th | group difference | +0.0801 [-0.0119, +0.1729] |
| CS_SINGLE Ac | native | Delta_E_given_L ha-th | group difference | +0.0337 [-0.0023, +0.0686] |
| CS_SINGLE Ac | unified | Delta_L_given_E | ci | +0.0930 [-0.0618, +0.2462] |
| CS_SINGLE Ac | unified | Delta_L_given_E | ha | +0.5116 [+0.3994, +0.6254] |
| CS_SINGLE Ac | unified | Delta_L_given_E | th | +0.2493 [+0.0924, +0.4181] |
| CS_SINGLE Ac | unified | Delta_L_given_E | all | +0.3068 [+0.2138, +0.3969] |
| CS_SINGLE Ac | unified | Delta_E_given_L | ci | -0.0484 [-0.0972, -0.0016] |
| CS_SINGLE Ac | unified | Delta_E_given_L | ha | +0.0934 [+0.0655, +0.1217] |
| CS_SINGLE Ac | unified | Delta_E_given_L | th | +0.0774 [+0.0474, +0.1085] |
| CS_SINGLE Ac | unified | Delta_E_given_L | all | +0.0393 [+0.0115, +0.0663] |
| CS_SINGLE Ac | unified | Delta_L_given_E ci-th | group difference | -0.1564 [-0.3924, +0.0600] |
| CS_SINGLE Ac | unified | Delta_E_given_L ci-th | group difference | -0.1258 [-0.1832, -0.0709] |
| CS_SINGLE Ac | unified | Delta_L_given_E ha-th | group difference | +0.2623 [+0.0657, +0.4590] |
| CS_SINGLE Ac | unified | Delta_E_given_L ha-th | group difference | +0.0160 [-0.0256, +0.0574] |
| CS_MULTI Ac | native | Delta_L_given_E | ci | +0.0144 [+0.0032, +0.0258] |
| CS_MULTI Ac | native | Delta_L_given_E | ha | +0.0500 [+0.0406, +0.0597] |
| CS_MULTI Ac | native | Delta_L_given_E | th | +0.0340 [+0.0202, +0.0500] |
| CS_MULTI Ac | native | Delta_L_given_E | all | +0.0339 [+0.0264, +0.0414] |
| CS_MULTI Ac | native | Delta_E_given_L | ci | +0.0086 [+0.0002, +0.0172] |
| CS_MULTI Ac | native | Delta_E_given_L | ha | +0.0240 [+0.0153, +0.0329] |
| CS_MULTI Ac | native | Delta_E_given_L | th | +0.0134 [+0.0035, +0.0235] |
| CS_MULTI Ac | native | Delta_E_given_L | all | +0.0163 [+0.0107, +0.0219] |
| CS_MULTI Ac | native | Delta_L_given_E ci-th | group difference | -0.0196 [-0.0396, -0.0009] |
| CS_MULTI Ac | native | Delta_E_given_L ci-th | group difference | -0.0048 [-0.0177, +0.0084] |
| CS_MULTI Ac | native | Delta_L_given_E ha-th | group difference | +0.0161 [-0.0026, +0.0336] |
| CS_MULTI Ac | native | Delta_E_given_L ha-th | group difference | +0.0106 [-0.0029, +0.0238] |
| CS_MULTI Ac | unified | Delta_L_given_E | ci | +0.0426 [-0.0468, +0.1294] |
| CS_MULTI Ac | unified | Delta_L_given_E | ha | +0.2892 [+0.2253, +0.3560] |
| CS_MULTI Ac | unified | Delta_L_given_E | th | +0.1163 [+0.0339, +0.2039] |
| CS_MULTI Ac | unified | Delta_L_given_E | all | +0.1647 [+0.1128, +0.2169] |
| CS_MULTI Ac | unified | Delta_E_given_L | ci | +0.0025 [-0.0359, +0.0419] |
| CS_MULTI Ac | unified | Delta_E_given_L | ha | +0.1043 [+0.0785, +0.1316] |
| CS_MULTI Ac | unified | Delta_E_given_L | th | +0.0690 [+0.0369, +0.1046] |
| CS_MULTI Ac | unified | Delta_E_given_L | all | +0.0605 [+0.0376, +0.0829] |
| CS_MULTI Ac | unified | Delta_L_given_E ci-th | group difference | -0.0736 [-0.2000, +0.0486] |
| CS_MULTI Ac | unified | Delta_E_given_L ci-th | group difference | -0.0665 [-0.1184, -0.0141] |
| CS_MULTI Ac | unified | Delta_L_given_E ha-th | group difference | +0.1729 [+0.0604, +0.2809] |
| CS_MULTI Ac | unified | Delta_E_given_L ha-th | group difference | +0.0353 [-0.0090, +0.0786] |
| NCE Lz | native | Delta_L_given_E | ci | +0.1463 [+0.0143, +0.2825] |
| NCE Lz | native | Delta_L_given_E | ha | +0.6205 [+0.5120, +0.7300] |
| NCE Lz | native | Delta_L_given_E | th | +0.4211 [+0.2638, +0.6033] |
| NCE Lz | native | Delta_L_given_E | all | +0.4089 [+0.3207, +0.4993] |
| NCE Lz | native | Delta_E_given_L | ci | +0.0678 [+0.0110, +0.1267] |
| NCE Lz | native | Delta_E_given_L | ha | +0.0736 [+0.0457, +0.1036] |
| NCE Lz | native | Delta_E_given_L | th | +0.0883 [+0.0452, +0.1325] |
| NCE Lz | native | Delta_E_given_L | all | +0.0746 [+0.0488, +0.1010] |
| NCE Lz | native | Delta_L_given_E ci-th | group difference | -0.2748 [-0.4998, -0.0713] |
| NCE Lz | native | Delta_E_given_L ci-th | group difference | -0.0205 [-0.0958, +0.0529] |
| NCE Lz | native | Delta_L_given_E ha-th | group difference | +0.1994 [-0.0053, +0.3951] |
| NCE Lz | native | Delta_E_given_L ha-th | group difference | -0.0147 [-0.0693, +0.0378] |
| NCE Lz | unified | Delta_L_given_E | ci | +0.0420 [-0.0987, +0.1894] |
| NCE Lz | unified | Delta_L_given_E | ha | +0.4176 [+0.3076, +0.5342] |
| NCE Lz | unified | Delta_L_given_E | th | +0.2851 [+0.1398, +0.4439] |
| NCE Lz | unified | Delta_L_given_E | all | +0.2554 [+0.1682, +0.3426] |
| NCE Lz | unified | Delta_E_given_L | ci | +0.0058 [-0.0363, +0.0473] |
| NCE Lz | unified | Delta_E_given_L | ha | +0.0619 [+0.0350, +0.0893] |
| NCE Lz | unified | Delta_E_given_L | th | +0.0840 [+0.0518, +0.1170] |
| NCE Lz | unified | Delta_E_given_L | all | +0.0464 [+0.0250, +0.0679] |
| NCE Lz | unified | Delta_L_given_E ci-th | group difference | -0.2431 [-0.4502, -0.0421] |
| NCE Lz | unified | Delta_E_given_L ci-th | group difference | -0.0781 [-0.1312, -0.0281] |
| NCE Lz | unified | Delta_L_given_E ha-th | group difference | +0.1325 [-0.0597, +0.3209] |
| NCE Lz | unified | Delta_E_given_L ha-th | group difference | -0.0220 [-0.0656, +0.0212] |
| FMCA Lz | native | Delta_L_given_E | ci | +0.0218 [+0.0053, +0.0401] |
| FMCA Lz | native | Delta_L_given_E | ha | +0.0073 [-0.0025, +0.0173] |
| FMCA Lz | native | Delta_L_given_E | th | +0.0016 [-0.0104, +0.0126] |
| FMCA Lz | native | Delta_L_given_E | all | +0.0113 [+0.0034, +0.0196] |
| FMCA Lz | native | Delta_E_given_L | ci | +0.0007 [-0.0099, +0.0117] |
| FMCA Lz | native | Delta_E_given_L | ha | +0.0003 [-0.0084, +0.0115] |
| FMCA Lz | native | Delta_E_given_L | th | -0.0014 [-0.0194, +0.0142] |
| FMCA Lz | native | Delta_E_given_L | all | +0.0001 [-0.0066, +0.0071] |
| FMCA Lz | native | Delta_L_given_E ci-th | group difference | +0.0202 [+0.0004, +0.0426] |
| FMCA Lz | native | Delta_E_given_L ci-th | group difference | +0.0021 [-0.0169, +0.0237] |
| FMCA Lz | native | Delta_L_given_E ha-th | group difference | +0.0057 [-0.0090, +0.0214] |
| FMCA Lz | native | Delta_E_given_L ha-th | group difference | +0.0017 [-0.0169, +0.0232] |
| FMCA Lz | unified | Delta_L_given_E | ci | +0.0384 [-0.0002, +0.0794] |
| FMCA Lz | unified | Delta_L_given_E | ha | +0.0560 [+0.0314, +0.0827] |
| FMCA Lz | unified | Delta_L_given_E | th | +0.0411 [+0.0138, +0.0715] |
| FMCA Lz | unified | Delta_L_given_E | all | +0.0466 [+0.0276, +0.0661] |
| FMCA Lz | unified | Delta_E_given_L | ci | -0.0043 [-0.0186, +0.0108] |
| FMCA Lz | unified | Delta_E_given_L | ha | +0.0006 [-0.0097, +0.0109] |
| FMCA Lz | unified | Delta_E_given_L | th | +0.0048 [-0.0119, +0.0217] |
| FMCA Lz | unified | Delta_E_given_L | all | -0.0003 [-0.0081, +0.0073] |
| FMCA Lz | unified | Delta_L_given_E ci-th | group difference | -0.0027 [-0.0518, +0.0471] |
| FMCA Lz | unified | Delta_E_given_L ci-th | group difference | -0.0092 [-0.0309, +0.0135] |
| FMCA Lz | unified | Delta_L_given_E ha-th | group difference | +0.0149 [-0.0259, +0.0531] |
| FMCA Lz | unified | Delta_E_given_L ha-th | group difference | -0.0042 [-0.0243, +0.0151] |
| CS_SINGLE Lz | native | Delta_L_given_E | ci | +0.0331 [-0.0251, +0.0926] |
| CS_SINGLE Lz | native | Delta_L_given_E | ha | +0.1114 [+0.0700, +0.1551] |
| CS_SINGLE Lz | native | Delta_L_given_E | th | +0.0831 [+0.0104, +0.1591] |
| CS_SINGLE Lz | native | Delta_L_given_E | all | +0.0775 [+0.0443, +0.1098] |
| CS_SINGLE Lz | native | Delta_E_given_L | ci | +0.0108 [-0.0128, +0.0326] |
| CS_SINGLE Lz | native | Delta_E_given_L | ha | +0.0444 [+0.0267, +0.0623] |
| CS_SINGLE Lz | native | Delta_E_given_L | th | +0.0413 [+0.0159, +0.0651] |
| CS_SINGLE Lz | native | Delta_E_given_L | all | +0.0317 [+0.0187, +0.0445] |
| CS_SINGLE Lz | native | Delta_L_given_E ci-th | group difference | -0.0501 [-0.1453, +0.0413] |
| CS_SINGLE Lz | native | Delta_E_given_L ci-th | group difference | -0.0305 [-0.0640, +0.0026] |
| CS_SINGLE Lz | native | Delta_L_given_E ha-th | group difference | +0.0283 [-0.0588, +0.1127] |
| CS_SINGLE Lz | native | Delta_E_given_L ha-th | group difference | +0.0031 [-0.0269, +0.0340] |
| CS_SINGLE Lz | unified | Delta_L_given_E | ci | +0.0775 [-0.0341, +0.1957] |
| CS_SINGLE Lz | unified | Delta_L_given_E | ha | +0.3253 [+0.2501, +0.4041] |
| CS_SINGLE Lz | unified | Delta_L_given_E | th | +0.2484 [+0.1352, +0.3736] |
| CS_SINGLE Lz | unified | Delta_L_given_E | all | +0.2205 [+0.1559, +0.2841] |
| CS_SINGLE Lz | unified | Delta_E_given_L | ci | +0.0304 [-0.0046, +0.0637] |
| CS_SINGLE Lz | unified | Delta_E_given_L | ha | +0.0895 [+0.0674, +0.1108] |
| CS_SINGLE Lz | unified | Delta_E_given_L | th | +0.0952 [+0.0612, +0.1301] |
| CS_SINGLE Lz | unified | Delta_E_given_L | all | +0.0695 [+0.0515, +0.0876] |
| CS_SINGLE Lz | unified | Delta_L_given_E ci-th | group difference | -0.1709 [-0.3354, -0.0074] |
| CS_SINGLE Lz | unified | Delta_E_given_L ci-th | group difference | -0.0647 [-0.1151, -0.0169] |
| CS_SINGLE Lz | unified | Delta_L_given_E ha-th | group difference | +0.0770 [-0.0698, +0.2148] |
| CS_SINGLE Lz | unified | Delta_E_given_L ha-th | group difference | -0.0056 [-0.0481, +0.0347] |
| CS_MULTI Lz | native | Delta_L_given_E | ci | +0.0050 [-0.0023, +0.0128] |
| CS_MULTI Lz | native | Delta_L_given_E | ha | +0.0265 [+0.0217, +0.0316] |
| CS_MULTI Lz | native | Delta_L_given_E | th | +0.0193 [+0.0105, +0.0282] |
| CS_MULTI Lz | native | Delta_L_given_E | all | +0.0173 [+0.0130, +0.0218] |
| CS_MULTI Lz | native | Delta_E_given_L | ci | +0.0045 [-0.0028, +0.0113] |
| CS_MULTI Lz | native | Delta_E_given_L | ha | +0.0019 [-0.0068, +0.0092] |
| CS_MULTI Lz | native | Delta_E_given_L | th | +0.0017 [-0.0052, +0.0087] |
| CS_MULTI Lz | native | Delta_E_given_L | all | +0.0028 [-0.0019, +0.0074] |
| CS_MULTI Lz | native | Delta_L_given_E ci-th | group difference | -0.0142 [-0.0260, -0.0029] |
| CS_MULTI Lz | native | Delta_E_given_L ci-th | group difference | +0.0028 [-0.0071, +0.0123] |
| CS_MULTI Lz | native | Delta_L_given_E ha-th | group difference | +0.0073 [-0.0033, +0.0175] |
| CS_MULTI Lz | native | Delta_E_given_L ha-th | group difference | +0.0002 [-0.0111, +0.0104] |
| CS_MULTI Lz | unified | Delta_L_given_E | ci | +0.0060 [-0.0540, +0.0644] |
| CS_MULTI Lz | unified | Delta_L_given_E | ha | +0.1687 [+0.1263, +0.2134] |
| CS_MULTI Lz | unified | Delta_L_given_E | th | +0.0915 [+0.0321, +0.1507] |
| CS_MULTI Lz | unified | Delta_L_given_E | all | +0.0943 [+0.0588, +0.1293] |
| CS_MULTI Lz | unified | Delta_E_given_L | ci | -0.0190 [-0.0562, +0.0158] |
| CS_MULTI Lz | unified | Delta_E_given_L | ha | +0.0526 [+0.0299, +0.0751] |
| CS_MULTI Lz | unified | Delta_E_given_L | th | +0.0654 [+0.0363, +0.0955] |
| CS_MULTI Lz | unified | Delta_E_given_L | all | +0.0296 [+0.0096, +0.0491] |
| CS_MULTI Lz | unified | Delta_L_given_E ci-th | group difference | -0.0855 [-0.1703, -0.0012] |
| CS_MULTI Lz | unified | Delta_E_given_L ci-th | group difference | -0.0844 [-0.1320, -0.0380] |
| CS_MULTI Lz | unified | Delta_L_given_E ha-th | group difference | +0.0772 [+0.0008, +0.1527] |
| CS_MULTI Lz | unified | Delta_E_given_L ha-th | group difference | -0.0127 [-0.0507, +0.0238] |

## DTU local: unified/gain_bits by window

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +1.3938 [+1.2723, +1.5211] | +0.3480 [+0.3074, +0.3879] | +0.8389 [+0.7484, +0.9305] | +0.2303 [+0.2045, +0.2566] |
| early | +0.5775 [+0.4977, +0.6542] | +0.2505 [+0.2115, +0.2900] | +0.4628 [+0.3992, +0.5258] | +0.1263 [+0.1060, +0.1482] |
| late | +1.4526 [+1.3214, +1.5852] | +0.4069 [+0.3600, +0.4531] | +1.0223 [+0.9102, +1.1349] | +0.4600 [+0.4000, +0.5206] |
| joint | +1.8834 [+1.7115, +2.0554] | +0.3870 [+0.3396, +0.4345] | +1.3098 [+1.1968, +1.4281] | +0.5566 [+0.4934, +0.6225] |
| late_equalwidth | – | – | – | – |

### DTU Ac by window (early / late / joint from extension E12)

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +2.1079 [+1.9441, +2.2796] | +0.4128 [+0.3636, +0.4653] | +1.0368 [+0.9416, +1.1372] | +0.2788 [+0.2457, +0.3105] |
| early | +0.7405 [+0.6474, +0.8288] | +0.2629 [+0.2273, +0.2995] | +0.5660 [+0.4810, +0.6489] | +0.1348 [+0.1137, +0.1574] |
| late | +2.0606 [+1.8947, +2.2306] | +0.4708 [+0.4224, +0.5214] | +1.3904 [+1.2784, +1.5109] | +0.6037 [+0.5380, +0.6729] |
| joint | +2.3933 [+2.2105, +2.5739] | +0.5029 [+0.4496, +0.5574] | +1.5752 [+1.4535, +1.7000] | +0.6814 [+0.6080, +0.7604] |

### DTU Lz by window (early / late / joint from extension E12)

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +1.0425 [+0.9371, +1.1575] | +0.5235 [+0.4567, +0.5951] | +0.9051 [+0.7977, +1.0134] | +0.2768 [+0.2427, +0.3114] |
| early | +0.5840 [+0.5015, +0.6689] | +0.2107 [+0.1722, +0.2504] | +0.5044 [+0.4261, +0.5811] | +0.1264 [+0.1075, +0.1461] |
| late | +1.2903 [+1.1577, +1.4271] | +0.3716 [+0.3220, +0.4194] | +0.8873 [+0.7809, +0.9952] | +0.3289 [+0.2892, +0.3684] |
| joint | +1.4262 [+1.2853, +1.5703] | +0.3183 [+0.2740, +0.3630] | +0.9885 [+0.8723, +1.1039] | +0.3553 [+0.3083, +0.4021] |

### DTU: Δ by group

| method target | readout | Δ | group | bits |
|---|---|---|---|---|
| NCE local | native | Delta_L_given_E | hi | +1.5985 [+1.3106, +1.8912] |
| NCE local | native | Delta_L_given_E | nh | +0.8337 [+0.6407, +1.0317] |
| NCE local | native | Delta_L_given_E | all | +1.2161 [+1.0173, +1.4288] |
| NCE local | native | Delta_E_given_L | hi | +0.2268 [+0.1396, +0.3139] |
| NCE local | native | Delta_E_given_L | nh | +0.2179 [+0.1529, +0.2775] |
| NCE local | native | Delta_E_given_L | all | +0.2224 [+0.1680, +0.2748] |
| NCE local | native | Delta_L_given_E hi-nh | group difference | +0.7648 [+0.4245, +1.1118] |
| NCE local | native | Delta_E_given_L hi-nh | group difference | +0.0089 [-0.0987, +0.1181] |
| NCE local | unified | Delta_L_given_E | hi | +0.7602 [+0.6237, +0.9031] |
| NCE local | unified | Delta_L_given_E | nh | +0.2285 [+0.1324, +0.3234] |
| NCE local | unified | Delta_L_given_E | all | +0.4944 [+0.3846, +0.6136] |
| NCE local | unified | Delta_E_given_L | hi | +0.1734 [+0.1003, +0.2461] |
| NCE local | unified | Delta_E_given_L | nh | +0.1134 [+0.0645, +0.1583] |
| NCE local | unified | Delta_E_given_L | all | +0.1434 [+0.0980, +0.1883] |
| NCE local | unified | Delta_L_given_E hi-nh | group difference | +0.5317 [+0.3725, +0.7018] |
| NCE local | unified | Delta_E_given_L hi-nh | group difference | +0.0600 [-0.0276, +0.1442] |
| FMCA local | native | Delta_L_given_E | hi | +0.1548 [+0.1049, +0.2011] |
| FMCA local | native | Delta_L_given_E | nh | +0.0643 [+0.0261, +0.1026] |
| FMCA local | native | Delta_L_given_E | all | +0.1095 [+0.0771, +0.1450] |
| FMCA local | native | Delta_E_given_L | hi | +0.0274 [-0.0023, +0.0569] |
| FMCA local | native | Delta_E_given_L | nh | +0.0117 [-0.0060, +0.0331] |
| FMCA local | native | Delta_E_given_L | all | +0.0196 [+0.0030, +0.0374] |
| FMCA local | native | Delta_L_given_E hi-nh | group difference | +0.0905 [+0.0274, +0.1516] |
| FMCA local | native | Delta_E_given_L hi-nh | group difference | +0.0157 [-0.0215, +0.0499] |
| FMCA local | unified | Delta_L_given_E | hi | +0.1108 [+0.0654, +0.1533] |
| FMCA local | unified | Delta_L_given_E | nh | +0.0041 [-0.0301, +0.0382] |
| FMCA local | unified | Delta_L_given_E | all | +0.0575 [+0.0249, +0.0915] |
| FMCA local | unified | Delta_E_given_L | hi | -0.0254 [-0.0520, +0.0002] |
| FMCA local | unified | Delta_E_given_L | nh | -0.0043 [-0.0197, +0.0114] |
| FMCA local | unified | Delta_E_given_L | all | -0.0148 [-0.0301, +0.0008] |
| FMCA local | unified | Delta_L_given_E hi-nh | group difference | +0.1067 [+0.0496, +0.1612] |
| FMCA local | unified | Delta_E_given_L hi-nh | group difference | -0.0211 [-0.0520, +0.0095] |
| CS_SINGLE local | native | Delta_L_given_E | hi | +0.3233 [+0.2142, +0.4305] |
| CS_SINGLE local | native | Delta_L_given_E | nh | +0.1214 [+0.0416, +0.2018] |
| CS_SINGLE local | native | Delta_L_given_E | all | +0.2223 [+0.1475, +0.2997] |
| CS_SINGLE local | native | Delta_E_given_L | hi | +0.0660 [+0.0331, +0.0990] |
| CS_SINGLE local | native | Delta_E_given_L | nh | +0.0726 [+0.0348, +0.1086] |
| CS_SINGLE local | native | Delta_E_given_L | all | +0.0693 [+0.0436, +0.0942] |
| CS_SINGLE local | native | Delta_L_given_E hi-nh | group difference | +0.2020 [+0.0727, +0.3374] |
| CS_SINGLE local | native | Delta_E_given_L hi-nh | group difference | -0.0066 [-0.0566, +0.0435] |
| CS_SINGLE local | unified | Delta_L_given_E | hi | +0.4800 [+0.3851, +0.5760] |
| CS_SINGLE local | unified | Delta_L_given_E | nh | +0.1551 [+0.0788, +0.2312] |
| CS_SINGLE local | unified | Delta_L_given_E | all | +0.3175 [+0.2403, +0.3985] |
| CS_SINGLE local | unified | Delta_E_given_L | hi | +0.1088 [+0.0694, +0.1455] |
| CS_SINGLE local | unified | Delta_E_given_L | nh | +0.0892 [+0.0399, +0.1378] |
| CS_SINGLE local | unified | Delta_E_given_L | all | +0.0990 [+0.0681, +0.1314] |
| CS_SINGLE local | unified | Delta_L_given_E hi-nh | group difference | +0.3249 [+0.2044, +0.4520] |
| CS_SINGLE local | unified | Delta_E_given_L hi-nh | group difference | +0.0196 [-0.0433, +0.0800] |
| CS_MULTI local | native | Delta_L_given_E | hi | +0.1242 [+0.0954, +0.1555] |
| CS_MULTI local | native | Delta_L_given_E | nh | +0.0449 [+0.0219, +0.0686] |
| CS_MULTI local | native | Delta_L_given_E | all | +0.0845 [+0.0626, +0.1069] |
| CS_MULTI local | native | Delta_E_given_L | hi | +0.0762 [+0.0438, +0.1119] |
| CS_MULTI local | native | Delta_E_given_L | nh | +0.0674 [+0.0349, +0.1027] |
| CS_MULTI local | native | Delta_E_given_L | all | +0.0718 [+0.0481, +0.0969] |
| CS_MULTI local | native | Delta_L_given_E hi-nh | group difference | +0.0793 [+0.0416, +0.1171] |
| CS_MULTI local | native | Delta_E_given_L hi-nh | group difference | +0.0088 [-0.0402, +0.0576] |
| CS_MULTI local | unified | Delta_L_given_E | hi | +0.2669 [+0.1956, +0.3406] |
| CS_MULTI local | unified | Delta_L_given_E | nh | +0.0862 [+0.0416, +0.1313] |
| CS_MULTI local | unified | Delta_L_given_E | all | +0.1766 [+0.1284, +0.2306] |
| CS_MULTI local | unified | Delta_E_given_L | hi | +0.0428 [+0.0027, +0.0842] |
| CS_MULTI local | unified | Delta_E_given_L | nh | +0.0481 [+0.0185, +0.0791] |
| CS_MULTI local | unified | Delta_E_given_L | all | +0.0455 [+0.0202, +0.0708] |
| CS_MULTI local | unified | Delta_L_given_E hi-nh | group difference | +0.1807 [+0.0946, +0.2667] |
| CS_MULTI local | unified | Delta_E_given_L hi-nh | group difference | -0.0054 [-0.0550, +0.0461] |
| NCE Ac | native | Delta_L_given_E | hi | +1.4839 [+1.2031, +1.7682] |
| NCE Ac | native | Delta_L_given_E | nh | +0.8023 [+0.6223, +0.9937] |
| NCE Ac | native | Delta_L_given_E | all | +1.1431 [+0.9518, +1.3397] |
| NCE Ac | native | Delta_E_given_L | hi | +0.2325 [+0.1728, +0.2963] |
| NCE Ac | native | Delta_E_given_L | nh | +0.2202 [+0.1288, +0.3119] |
| NCE Ac | native | Delta_E_given_L | all | +0.2264 [+0.1699, +0.2826] |
| NCE Ac | native | Delta_L_given_E hi-nh | group difference | +0.6817 [+0.3522, +1.0198] |
| NCE Ac | native | Delta_E_given_L hi-nh | group difference | +0.0124 [-0.0955, +0.1272] |
| NCE Ac | unified | Delta_L_given_E | hi | +1.0382 [+0.8664, +1.2203] |
| NCE Ac | unified | Delta_L_given_E | nh | +0.3647 [+0.2594, +0.4686] |
| NCE Ac | unified | Delta_L_given_E | all | +0.7014 [+0.5668, +0.8491] |
| NCE Ac | unified | Delta_E_given_L | hi | +0.1591 [+0.1081, +0.2122] |
| NCE Ac | unified | Delta_E_given_L | nh | +0.1533 [+0.0948, +0.2117] |
| NCE Ac | unified | Delta_E_given_L | all | +0.1562 [+0.1158, +0.1966] |
| NCE Ac | unified | Delta_L_given_E hi-nh | group difference | +0.6735 [+0.4707, +0.8829] |
| NCE Ac | unified | Delta_E_given_L hi-nh | group difference | +0.0059 [-0.0730, +0.0831] |
| FMCA Ac | native | Delta_L_given_E | hi | +0.1305 [+0.0787, +0.1829] |
| FMCA Ac | native | Delta_L_given_E | nh | +0.0406 [+0.0116, +0.0702] |
| FMCA Ac | native | Delta_L_given_E | all | +0.0855 [+0.0538, +0.1195] |
| FMCA Ac | native | Delta_E_given_L | hi | +0.0195 [-0.0020, +0.0415] |
| FMCA Ac | native | Delta_E_given_L | nh | -0.0069 [-0.0241, +0.0114] |
| FMCA Ac | native | Delta_E_given_L | all | +0.0063 [-0.0080, +0.0216] |
| FMCA Ac | native | Delta_L_given_E hi-nh | group difference | +0.0899 [+0.0301, +0.1499] |
| FMCA Ac | native | Delta_E_given_L hi-nh | group difference | +0.0264 [-0.0019, +0.0549] |
| FMCA Ac | unified | Delta_L_given_E | hi | +0.1994 [+0.1392, +0.2556] |
| FMCA Ac | unified | Delta_L_given_E | nh | +0.0196 [-0.0125, +0.0519] |
| FMCA Ac | unified | Delta_L_given_E | all | +0.1095 [+0.0685, +0.1542] |
| FMCA Ac | unified | Delta_E_given_L | hi | +0.0146 [-0.0030, +0.0329] |
| FMCA Ac | unified | Delta_E_given_L | nh | +0.0178 [-0.0053, +0.0395] |
| FMCA Ac | unified | Delta_E_given_L | all | +0.0162 [+0.0014, +0.0307] |
| FMCA Ac | unified | Delta_L_given_E hi-nh | group difference | +0.1798 [+0.1102, +0.2464] |
| FMCA Ac | unified | Delta_E_given_L hi-nh | group difference | -0.0032 [-0.0317, +0.0268] |
| CS_SINGLE Ac | native | Delta_L_given_E | hi | +0.2923 [+0.2132, +0.3712] |
| CS_SINGLE Ac | native | Delta_L_given_E | nh | +0.1090 [+0.0354, +0.1788] |
| CS_SINGLE Ac | native | Delta_L_given_E | all | +0.2006 [+0.1407, +0.2619] |
| CS_SINGLE Ac | native | Delta_E_given_L | hi | +0.0673 [+0.0405, +0.0945] |
| CS_SINGLE Ac | native | Delta_E_given_L | nh | +0.0759 [+0.0431, +0.1073] |
| CS_SINGLE Ac | native | Delta_E_given_L | all | +0.0716 [+0.0508, +0.0927] |
| CS_SINGLE Ac | native | Delta_L_given_E hi-nh | group difference | +0.1833 [+0.0809, +0.2910] |
| CS_SINGLE Ac | native | Delta_E_given_L hi-nh | group difference | -0.0086 [-0.0515, +0.0348] |
| CS_SINGLE Ac | unified | Delta_L_given_E | hi | +0.6337 [+0.5054, +0.7648] |
| CS_SINGLE Ac | unified | Delta_L_given_E | nh | +0.2178 [+0.1591, +0.2778] |
| CS_SINGLE Ac | unified | Delta_L_given_E | all | +0.4258 [+0.3371, +0.5250] |
| CS_SINGLE Ac | unified | Delta_E_given_L | hi | +0.1116 [+0.0768, +0.1483] |
| CS_SINGLE Ac | unified | Delta_E_given_L | nh | +0.0992 [+0.0569, +0.1404] |
| CS_SINGLE Ac | unified | Delta_E_given_L | all | +0.1054 [+0.0778, +0.1326] |
| CS_SINGLE Ac | unified | Delta_L_given_E hi-nh | group difference | +0.4160 [+0.2741, +0.5597] |
| CS_SINGLE Ac | unified | Delta_E_given_L hi-nh | group difference | +0.0124 [-0.0432, +0.0681] |
| CS_MULTI Ac | native | Delta_L_given_E | hi | +0.0683 [+0.0244, +0.1101] |
| CS_MULTI Ac | native | Delta_L_given_E | nh | +0.0142 [-0.0162, +0.0438] |
| CS_MULTI Ac | native | Delta_L_given_E | all | +0.0413 [+0.0134, +0.0681] |
| CS_MULTI Ac | native | Delta_E_given_L | hi | +0.0064 [-0.0240, +0.0360] |
| CS_MULTI Ac | native | Delta_E_given_L | nh | +0.0069 [-0.0139, +0.0275] |
| CS_MULTI Ac | native | Delta_E_given_L | all | +0.0067 [-0.0120, +0.0250] |
| CS_MULTI Ac | native | Delta_L_given_E hi-nh | group difference | +0.0541 [+0.0018, +0.1065] |
| CS_MULTI Ac | native | Delta_E_given_L hi-nh | group difference | -0.0005 [-0.0371, +0.0344] |
| CS_MULTI Ac | unified | Delta_L_given_E | hi | +0.3694 [+0.2879, +0.4546] |
| CS_MULTI Ac | unified | Delta_L_given_E | nh | +0.1170 [+0.0629, +0.1740] |
| CS_MULTI Ac | unified | Delta_L_given_E | all | +0.2432 [+0.1834, +0.3066] |
| CS_MULTI Ac | unified | Delta_E_given_L | hi | +0.0365 [-0.0014, +0.0742] |
| CS_MULTI Ac | unified | Delta_E_given_L | nh | +0.0321 [+0.0068, +0.0582] |
| CS_MULTI Ac | unified | Delta_E_given_L | all | +0.0343 [+0.0110, +0.0569] |
| CS_MULTI Ac | unified | Delta_L_given_E hi-nh | group difference | +0.2523 [+0.1524, +0.3538] |
| CS_MULTI Ac | unified | Delta_E_given_L hi-nh | group difference | +0.0044 [-0.0417, +0.0487] |
| NCE Lz | native | Delta_L_given_E | hi | +1.0157 [+0.8317, +1.1983] |
| NCE Lz | native | Delta_L_given_E | nh | +0.5512 [+0.4375, +0.6682] |
| NCE Lz | native | Delta_L_given_E | all | +0.7835 [+0.6594, +0.9183] |
| NCE Lz | native | Delta_E_given_L | hi | +0.1326 [+0.0807, +0.1857] |
| NCE Lz | native | Delta_E_given_L | nh | +0.1524 [+0.0914, +0.2144] |
| NCE Lz | native | Delta_E_given_L | all | +0.1425 [+0.1041, +0.1817] |
| NCE Lz | native | Delta_L_given_E hi-nh | group difference | +0.4645 [+0.2529, +0.6808] |
| NCE Lz | native | Delta_E_given_L hi-nh | group difference | -0.0198 [-0.1006, +0.0555] |
| NCE Lz | unified | Delta_L_given_E | hi | +0.4703 [+0.3664, +0.5711] |
| NCE Lz | unified | Delta_L_given_E | nh | +0.1884 [+0.0986, +0.2782] |
| NCE Lz | unified | Delta_L_given_E | all | +0.3293 [+0.2494, +0.4104] |
| NCE Lz | unified | Delta_E_given_L | hi | +0.0162 [-0.0295, +0.0613] |
| NCE Lz | unified | Delta_E_given_L | nh | +0.0751 [+0.0280, +0.1183] |
| NCE Lz | unified | Delta_E_given_L | all | +0.0456 [+0.0128, +0.0785] |
| NCE Lz | unified | Delta_L_given_E hi-nh | group difference | +0.2819 [+0.1490, +0.4187] |
| NCE Lz | unified | Delta_E_given_L hi-nh | group difference | -0.0589 [-0.1218, +0.0019] |
| FMCA Lz | native | Delta_L_given_E | hi | +0.0373 [+0.0049, +0.0706] |
| FMCA Lz | native | Delta_L_given_E | nh | +0.0183 [-0.0037, +0.0427] |
| FMCA Lz | native | Delta_L_given_E | all | +0.0278 [+0.0076, +0.0491] |
| FMCA Lz | native | Delta_E_given_L | hi | -0.0201 [-0.0438, +0.0030] |
| FMCA Lz | native | Delta_E_given_L | nh | -0.0036 [-0.0249, +0.0162] |
| FMCA Lz | native | Delta_E_given_L | all | -0.0119 [-0.0270, +0.0039] |
| FMCA Lz | native | Delta_L_given_E hi-nh | group difference | +0.0190 [-0.0214, +0.0591] |
| FMCA Lz | native | Delta_E_given_L hi-nh | group difference | -0.0166 [-0.0482, +0.0145] |
| FMCA Lz | unified | Delta_L_given_E | hi | +0.0719 [+0.0299, +0.1159] |
| FMCA Lz | unified | Delta_L_given_E | nh | -0.0019 [-0.0340, +0.0335] |
| FMCA Lz | unified | Delta_L_given_E | all | +0.0350 [+0.0069, +0.0656] |
| FMCA Lz | unified | Delta_E_given_L | hi | -0.0326 [-0.0596, -0.0047] |
| FMCA Lz | unified | Delta_E_given_L | nh | -0.0120 [-0.0321, +0.0072] |
| FMCA Lz | unified | Delta_E_given_L | all | -0.0223 [-0.0385, -0.0057] |
| FMCA Lz | unified | Delta_L_given_E hi-nh | group difference | +0.0738 [+0.0212, +0.1279] |
| FMCA Lz | unified | Delta_E_given_L hi-nh | group difference | -0.0205 [-0.0537, +0.0134] |
| CS_SINGLE Lz | native | Delta_L_given_E | hi | +0.1250 [+0.0644, +0.1866] |
| CS_SINGLE Lz | native | Delta_L_given_E | nh | -0.0029 [-0.0637, +0.0564] |
| CS_SINGLE Lz | native | Delta_L_given_E | all | +0.0610 [+0.0153, +0.1091] |
| CS_SINGLE Lz | native | Delta_E_given_L | hi | +0.0366 [+0.0082, +0.0642] |
| CS_SINGLE Lz | native | Delta_E_given_L | nh | +0.0649 [+0.0402, +0.0890] |
| CS_SINGLE Lz | native | Delta_E_given_L | all | +0.0508 [+0.0321, +0.0707] |
| CS_SINGLE Lz | native | Delta_L_given_E hi-nh | group difference | +0.1279 [+0.0434, +0.2129] |
| CS_SINGLE Lz | native | Delta_E_given_L hi-nh | group difference | -0.0283 [-0.0655, +0.0084] |
| CS_SINGLE Lz | unified | Delta_L_given_E | hi | +0.2725 [+0.1928, +0.3532] |
| CS_SINGLE Lz | unified | Delta_L_given_E | nh | +0.0872 [+0.0257, +0.1503] |
| CS_SINGLE Lz | unified | Delta_L_given_E | all | +0.1798 [+0.1235, +0.2396] |
| CS_SINGLE Lz | unified | Delta_E_given_L | hi | +0.0388 [+0.0078, +0.0688] |
| CS_SINGLE Lz | unified | Delta_E_given_L | nh | +0.0558 [+0.0185, +0.0910] |
| CS_SINGLE Lz | unified | Delta_E_given_L | all | +0.0473 [+0.0239, +0.0709] |
| CS_SINGLE Lz | unified | Delta_L_given_E hi-nh | group difference | +0.1853 [+0.0868, +0.2882] |
| CS_SINGLE Lz | unified | Delta_E_given_L hi-nh | group difference | -0.0170 [-0.0655, +0.0286] |
| CS_MULTI Lz | native | Delta_L_given_E | hi | +0.0424 [+0.0193, +0.0674] |
| CS_MULTI Lz | native | Delta_L_given_E | nh | +0.0236 [+0.0106, +0.0364] |
| CS_MULTI Lz | native | Delta_L_given_E | all | +0.0330 [+0.0189, +0.0477] |
| CS_MULTI Lz | native | Delta_E_given_L | hi | +0.0130 [-0.0027, +0.0296] |
| CS_MULTI Lz | native | Delta_E_given_L | nh | +0.0043 [-0.0066, +0.0148] |
| CS_MULTI Lz | native | Delta_E_given_L | all | +0.0087 [-0.0009, +0.0189] |
| CS_MULTI Lz | native | Delta_L_given_E hi-nh | group difference | +0.0188 [-0.0077, +0.0468] |
| CS_MULTI Lz | native | Delta_E_given_L hi-nh | group difference | +0.0087 [-0.0106, +0.0278] |
| CS_MULTI Lz | unified | Delta_L_given_E | hi | +0.1456 [+0.0935, +0.1943] |
| CS_MULTI Lz | unified | Delta_L_given_E | nh | +0.0669 [+0.0310, +0.1034] |
| CS_MULTI Lz | unified | Delta_L_given_E | all | +0.1062 [+0.0726, +0.1405] |
| CS_MULTI Lz | unified | Delta_E_given_L | hi | +0.0358 [+0.0088, +0.0644] |
| CS_MULTI Lz | unified | Delta_E_given_L | nh | +0.0445 [+0.0235, +0.0653] |
| CS_MULTI Lz | unified | Delta_E_given_L | all | +0.0402 [+0.0232, +0.0579] |
| CS_MULTI Lz | unified | Delta_L_given_E hi-nh | group difference | +0.0787 [+0.0167, +0.1396] |
| CS_MULTI Lz | unified | Delta_E_given_L hi-nh | group difference | -0.0087 [-0.0427, +0.0252] |

## Federici envelope: unified/gain_bits by window

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | +0.0486 [+0.0353, +0.0625] | +0.0575 [+0.0433, +0.0724] | +0.0902 [+0.0704, +0.1127] | +0.0539 [+0.0393, +0.0696] |
| early | +0.1687 [+0.1318, +0.2083] | +0.0658 [+0.0459, +0.0870] | +0.1084 [+0.0802, +0.1384] | +0.0638 [+0.0449, +0.0831] |
| late | +0.0206 [+0.0116, +0.0299] | +0.0287 [+0.0183, +0.0394] | +0.0162 [+0.0098, +0.0228] | +0.0168 [+0.0080, +0.0259] |
| joint | +0.0728 [+0.0587, +0.0875] | +0.0487 [+0.0348, +0.0630] | +0.1348 [+0.1022, +0.1691] | +0.0583 [+0.0454, +0.0709] |
| late_equalwidth | +0.1153 [+0.0873, +0.1439] | +0.0329 [+0.0194, +0.0459] | +0.0596 [+0.0420, +0.0784] | +0.0348 [+0.0242, +0.0455] |

### Federici: Δ by group

| method target | readout | Δ | group | bits |
|---|---|---|---|---|
| NCE envelope | native | Delta_L_given_E | Artifact | +0.0870 [-0.0919, +0.2479] |
| NCE envelope | native | Delta_L_given_E | CI | -0.1295 [-0.2593, +0.0041] |
| NCE envelope | native | Delta_L_given_E | HC | -0.1336 [-0.2653, -0.0077] |
| NCE envelope | native | Delta_L_given_E | HC-v | +0.0719 [-0.0079, +0.1510] |
| NCE envelope | native | Delta_L_given_E | all | -0.0767 [-0.1500, +0.0007] |
| NCE envelope | native | Delta_E_given_L | Artifact | -0.3480 [-0.5719, -0.1361] |
| NCE envelope | native | Delta_E_given_L | CI | -0.1503 [-0.2498, -0.0628] |
| NCE envelope | native | Delta_E_given_L | HC | +0.0147 [-0.0676, +0.0907] |
| NCE envelope | native | Delta_E_given_L | HC-v | +0.0054 [-0.0560, +0.0638] |
| NCE envelope | native | Delta_E_given_L | all | -0.0785 [-0.1345, -0.0257] |
| NCE envelope | native | Delta_L_given_E Artifact-HC | group difference | +0.2206 [+0.0003, +0.4315] |
| NCE envelope | native | Delta_E_given_L Artifact-HC | group difference | -0.3627 [-0.5977, -0.1312] |
| NCE envelope | native | Delta_L_given_E CI-HC | group difference | +0.0042 [-0.1745, +0.1913] |
| NCE envelope | native | Delta_E_given_L CI-HC | group difference | -0.1649 [-0.2904, -0.0419] |
| NCE envelope | native | Delta_L_given_E HC-v-HC | group difference | +0.2056 [+0.0559, +0.3594] |
| NCE envelope | native | Delta_E_given_L HC-v-HC | group difference | -0.0093 [-0.1091, +0.0898] |
| NCE envelope | unified | Delta_L_given_E | Artifact | +0.0700 [+0.0145, +0.1247] |
| NCE envelope | unified | Delta_L_given_E | CI | -0.0578 [-0.1185, -0.0003] |
| NCE envelope | unified | Delta_L_given_E | HC | -0.0301 [-0.0630, +0.0022] |
| NCE envelope | unified | Delta_L_given_E | HC-v | -0.0267 [-0.0789, +0.0274] |
| NCE envelope | unified | Delta_L_given_E | all | -0.0297 [-0.0566, -0.0037] |
| NCE envelope | unified | Delta_E_given_L | Artifact | -0.0265 [-0.0446, -0.0127] |
| NCE envelope | unified | Delta_E_given_L | CI | +0.0271 [+0.0067, +0.0473] |
| NCE envelope | unified | Delta_E_given_L | HC | +0.0380 [+0.0196, +0.0574] |
| NCE envelope | unified | Delta_E_given_L | HC-v | +0.0212 [+0.0015, +0.0427] |
| NCE envelope | unified | Delta_E_given_L | all | +0.0253 [+0.0139, +0.0373] |
| NCE envelope | unified | Delta_L_given_E Artifact-HC | group difference | +0.1001 [+0.0364, +0.1631] |
| NCE envelope | unified | Delta_E_given_L Artifact-HC | group difference | -0.0645 [-0.0903, -0.0409] |
| NCE envelope | unified | Delta_L_given_E CI-HC | group difference | -0.0277 [-0.0946, +0.0359] |
| NCE envelope | unified | Delta_E_given_L CI-HC | group difference | -0.0109 [-0.0381, +0.0170] |
| NCE envelope | unified | Delta_L_given_E HC-v-HC | group difference | +0.0034 [-0.0582, +0.0664] |
| NCE envelope | unified | Delta_E_given_L HC-v-HC | group difference | -0.0168 [-0.0450, +0.0120] |
| FMCA envelope | native | Delta_L_given_E | Artifact | -0.0157 [-0.0386, +0.0022] |
| FMCA envelope | native | Delta_L_given_E | CI | +0.0079 [-0.0112, +0.0265] |
| FMCA envelope | native | Delta_L_given_E | HC | -0.0236 [-0.0474, -0.0001] |
| FMCA envelope | native | Delta_L_given_E | HC-v | +0.0005 [-0.0221, +0.0228] |
| FMCA envelope | native | Delta_L_given_E | all | -0.0078 [-0.0206, +0.0049] |
| FMCA envelope | native | Delta_E_given_L | Artifact | +0.0078 [-0.0058, +0.0200] |
| FMCA envelope | native | Delta_E_given_L | CI | -0.0057 [-0.0303, +0.0185] |
| FMCA envelope | native | Delta_E_given_L | HC | -0.0383 [-0.0593, -0.0180] |
| FMCA envelope | native | Delta_E_given_L | HC-v | -0.0028 [-0.0358, +0.0278] |
| FMCA envelope | native | Delta_E_given_L | all | -0.0166 [-0.0297, -0.0032] |
| FMCA envelope | native | Delta_L_given_E Artifact-HC | group difference | +0.0079 [-0.0254, +0.0383] |
| FMCA envelope | native | Delta_E_given_L Artifact-HC | group difference | +0.0461 [+0.0213, +0.0705] |
| FMCA envelope | native | Delta_L_given_E CI-HC | group difference | +0.0315 [+0.0006, +0.0625] |
| FMCA envelope | native | Delta_E_given_L CI-HC | group difference | +0.0326 [+0.0010, +0.0644] |
| FMCA envelope | native | Delta_L_given_E HC-v-HC | group difference | +0.0240 [-0.0089, +0.0556] |
| FMCA envelope | native | Delta_E_given_L HC-v-HC | group difference | +0.0355 [-0.0022, +0.0724] |
| FMCA envelope | unified | Delta_L_given_E | Artifact | -0.0267 [-0.0689, +0.0030] |
| FMCA envelope | unified | Delta_L_given_E | CI | -0.0084 [-0.0292, +0.0115] |
| FMCA envelope | unified | Delta_L_given_E | HC | -0.0098 [-0.0265, +0.0074] |
| FMCA envelope | unified | Delta_L_given_E | HC-v | -0.0199 [-0.0456, +0.0064] |
| FMCA envelope | unified | Delta_L_given_E | all | -0.0126 [-0.0239, -0.0013] |
| FMCA envelope | unified | Delta_E_given_L | Artifact | -0.0244 [-0.0390, -0.0102] |
| FMCA envelope | unified | Delta_E_given_L | CI | -0.0082 [-0.0268, +0.0111] |
| FMCA envelope | unified | Delta_E_given_L | HC | +0.0032 [-0.0139, +0.0203] |
| FMCA envelope | unified | Delta_E_given_L | HC-v | +0.0208 [-0.0050, +0.0479] |
| FMCA envelope | unified | Delta_E_given_L | all | -0.0004 [-0.0107, +0.0106] |
| FMCA envelope | unified | Delta_L_given_E Artifact-HC | group difference | -0.0169 [-0.0625, +0.0199] |
| FMCA envelope | unified | Delta_E_given_L Artifact-HC | group difference | -0.0275 [-0.0504, -0.0056] |
| FMCA envelope | unified | Delta_L_given_E CI-HC | group difference | +0.0015 [-0.0263, +0.0282] |
| FMCA envelope | unified | Delta_E_given_L CI-HC | group difference | -0.0114 [-0.0362, +0.0145] |
| FMCA envelope | unified | Delta_L_given_E HC-v-HC | group difference | -0.0101 [-0.0412, +0.0219] |
| FMCA envelope | unified | Delta_E_given_L HC-v-HC | group difference | +0.0176 [-0.0126, +0.0486] |
| CS_SINGLE envelope | native | Delta_L_given_E | Artifact | +0.0105 [-0.0930, +0.0928] |
| CS_SINGLE envelope | native | Delta_L_given_E | CI | +0.0548 [-0.0231, +0.1361] |
| CS_SINGLE envelope | native | Delta_L_given_E | HC | +0.0429 [-0.0365, +0.1226] |
| CS_SINGLE envelope | native | Delta_L_given_E | HC-v | -0.1376 [-0.2175, -0.0643] |
| CS_SINGLE envelope | native | Delta_L_given_E | all | +0.0136 [-0.0329, +0.0611] |
| CS_SINGLE envelope | native | Delta_E_given_L | Artifact | +0.3052 [+0.0690, +0.5513] |
| CS_SINGLE envelope | native | Delta_E_given_L | CI | -0.0019 [-0.1091, +0.1104] |
| CS_SINGLE envelope | native | Delta_E_given_L | HC | +0.0148 [-0.0691, +0.1020] |
| CS_SINGLE envelope | native | Delta_E_given_L | HC-v | -0.1096 [-0.2471, +0.0064] |
| CS_SINGLE envelope | native | Delta_E_given_L | all | +0.0156 [-0.0463, +0.0818] |
| CS_SINGLE envelope | native | Delta_L_given_E Artifact-HC | group difference | -0.0324 [-0.1618, +0.0847] |
| CS_SINGLE envelope | native | Delta_E_given_L Artifact-HC | group difference | +0.2904 [+0.0390, +0.5608] |
| CS_SINGLE envelope | native | Delta_L_given_E CI-HC | group difference | +0.0119 [-0.1033, +0.1239] |
| CS_SINGLE envelope | native | Delta_E_given_L CI-HC | group difference | -0.0167 [-0.1556, +0.1220] |
| CS_SINGLE envelope | native | Delta_L_given_E HC-v-HC | group difference | -0.1806 [-0.2986, -0.0744] |
| CS_SINGLE envelope | native | Delta_E_given_L HC-v-HC | group difference | -0.1244 [-0.2896, +0.0270] |
| CS_SINGLE envelope | unified | Delta_L_given_E | Artifact | -0.0744 [-0.1087, -0.0400] |
| CS_SINGLE envelope | unified | Delta_L_given_E | CI | +0.0294 [-0.0046, +0.0647] |
| CS_SINGLE envelope | unified | Delta_L_given_E | HC | +0.0035 [-0.0172, +0.0241] |
| CS_SINGLE envelope | unified | Delta_L_given_E | HC-v | +0.0087 [-0.0254, +0.0402] |
| CS_SINGLE envelope | unified | Delta_L_given_E | all | +0.0060 [-0.0113, +0.0224] |
| CS_SINGLE envelope | unified | Delta_E_given_L | Artifact | -0.0926 [-0.1161, -0.0702] |
| CS_SINGLE envelope | unified | Delta_E_given_L | CI | +0.0740 [+0.0253, +0.1289] |
| CS_SINGLE envelope | unified | Delta_E_given_L | HC | +0.0682 [+0.0366, +0.0997] |
| CS_SINGLE envelope | unified | Delta_E_given_L | HC-v | +0.0167 [-0.0301, +0.0646] |
| CS_SINGLE envelope | unified | Delta_E_given_L | all | +0.0463 [+0.0221, +0.0712] |
| CS_SINGLE envelope | unified | Delta_L_given_E Artifact-HC | group difference | -0.0779 [-0.1189, -0.0370] |
| CS_SINGLE envelope | unified | Delta_E_given_L Artifact-HC | group difference | -0.1608 [-0.2006, -0.1211] |
| CS_SINGLE envelope | unified | Delta_L_given_E CI-HC | group difference | +0.0259 [-0.0139, +0.0670] |
| CS_SINGLE envelope | unified | Delta_E_given_L CI-HC | group difference | +0.0058 [-0.0517, +0.0676] |
| CS_SINGLE envelope | unified | Delta_L_given_E HC-v-HC | group difference | +0.0052 [-0.0329, +0.0435] |
| CS_SINGLE envelope | unified | Delta_E_given_L HC-v-HC | group difference | -0.0515 [-0.1074, +0.0065] |
| CS_MULTI envelope | native | Delta_L_given_E | Artifact | -0.0279 [-0.0672, +0.0181] |
| CS_MULTI envelope | native | Delta_L_given_E | CI | +0.0123 [-0.0177, +0.0425] |
| CS_MULTI envelope | native | Delta_L_given_E | HC | +0.0074 [-0.0226, +0.0370] |
| CS_MULTI envelope | native | Delta_L_given_E | HC-v | +0.0355 [-0.0122, +0.0926] |
| CS_MULTI envelope | native | Delta_L_given_E | all | +0.0105 [-0.0069, +0.0299] |
| CS_MULTI envelope | native | Delta_E_given_L | Artifact | -0.0211 [-0.0494, +0.0120] |
| CS_MULTI envelope | native | Delta_E_given_L | CI | +0.0131 [-0.0093, +0.0346] |
| CS_MULTI envelope | native | Delta_E_given_L | HC | +0.0018 [-0.0157, +0.0192] |
| CS_MULTI envelope | native | Delta_E_given_L | HC-v | +0.0174 [-0.0138, +0.0496] |
| CS_MULTI envelope | native | Delta_E_given_L | all | +0.0062 [-0.0057, +0.0181] |
| CS_MULTI envelope | native | Delta_L_given_E Artifact-HC | group difference | -0.0354 [-0.0875, +0.0193] |
| CS_MULTI envelope | native | Delta_E_given_L Artifact-HC | group difference | -0.0229 [-0.0569, +0.0143] |
| CS_MULTI envelope | native | Delta_L_given_E CI-HC | group difference | +0.0048 [-0.0387, +0.0483] |
| CS_MULTI envelope | native | Delta_E_given_L CI-HC | group difference | +0.0114 [-0.0168, +0.0397] |
| CS_MULTI envelope | native | Delta_L_given_E HC-v-HC | group difference | +0.0280 [-0.0290, +0.0937] |
| CS_MULTI envelope | native | Delta_E_given_L HC-v-HC | group difference | +0.0156 [-0.0204, +0.0538] |
| CS_MULTI envelope | unified | Delta_L_given_E | Artifact | +0.0197 [-0.0163, +0.0515] |
| CS_MULTI envelope | unified | Delta_L_given_E | CI | +0.0090 [-0.0127, +0.0317] |
| CS_MULTI envelope | unified | Delta_L_given_E | HC | -0.0047 [-0.0187, +0.0098] |
| CS_MULTI envelope | unified | Delta_L_given_E | HC-v | +0.0164 [-0.0110, +0.0414] |
| CS_MULTI envelope | unified | Delta_L_given_E | all | +0.0059 [-0.0049, +0.0169] |
| CS_MULTI envelope | unified | Delta_E_given_L | Artifact | -0.0016 [-0.0140, +0.0137] |
| CS_MULTI envelope | unified | Delta_E_given_L | CI | +0.0267 [+0.0068, +0.0472] |
| CS_MULTI envelope | unified | Delta_E_given_L | HC | +0.0230 [+0.0069, +0.0386] |
| CS_MULTI envelope | unified | Delta_E_given_L | HC-v | -0.0010 [-0.0179, +0.0159] |
| CS_MULTI envelope | unified | Delta_E_given_L | all | +0.0179 [+0.0081, +0.0281] |
| CS_MULTI envelope | unified | Delta_L_given_E Artifact-HC | group difference | +0.0244 [-0.0145, +0.0585] |
| CS_MULTI envelope | unified | Delta_E_given_L Artifact-HC | group difference | -0.0246 [-0.0456, -0.0031] |
| CS_MULTI envelope | unified | Delta_L_given_E CI-HC | group difference | +0.0137 [-0.0121, +0.0406] |
| CS_MULTI envelope | unified | Delta_E_given_L CI-HC | group difference | +0.0037 [-0.0221, +0.0290] |
| CS_MULTI envelope | unified | Delta_L_given_E HC-v-HC | group difference | +0.0212 [-0.0101, +0.0509] |
| CS_MULTI envelope | unified | Delta_E_given_L HC-v-HC | group difference | -0.0239 [-0.0461, -0.0007] |

## Private BDF current_class: head_gain_vs_base_bits by window

| window | NCE | FMCA | CS_SINGLE | CS_MULTI |
|---|---|---|---|---|
| full | -0.0009 [-0.0014, -0.0004] | +0.0001 [-0.0010, +0.0011] | +0.0005 [-0.0006, +0.0016] | -0.0007 [-0.0017, +0.0002] |
| early | -0.0010 [-0.0014, -0.0007] | -0.0013 [-0.0019, -0.0008] | -0.0009 [-0.0013, -0.0005] | -0.0017 [-0.0022, -0.0013] |
| late | -0.0012 [-0.0016, -0.0008] | -0.0007 [-0.0014, +0.0000] | -0.0008 [-0.0014, -0.0003] | -0.0018 [-0.0023, -0.0013] |
| joint | -0.0009 [-0.0012, -0.0006] | -0.0005 [-0.0013, +0.0003] | -0.0004 [-0.0013, +0.0004] | -0.0000 [-0.0008, +0.0008] |
| late_equalwidth | – | – | – | – |

### Private BDF: Δ by group

| method target | readout | Δ | group | bits |
|---|---|---|---|---|
| NCE current_class | head_logloss_bits | Delta_L_given_E | HA | +0.0000 [-0.0005, +0.0006] |
| NCE current_class | head_logloss_bits | Delta_L_given_E | NH | +0.0005 [-0.0004, +0.0016] |
| NCE current_class | head_logloss_bits | Delta_L_given_E | all | +0.0001 [-0.0004, +0.0006] |
| NCE current_class | head_logloss_bits | Delta_E_given_L | HA | +0.0002 [-0.0003, +0.0006] |
| NCE current_class | head_logloss_bits | Delta_E_given_L | NH | +0.0007 [-0.0009, +0.0020] |
| NCE current_class | head_logloss_bits | Delta_E_given_L | all | +0.0002 [-0.0002, +0.0007] |
| NCE current_class | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0005 [-0.0016, +0.0006] |
| NCE current_class | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0006 [-0.0020, +0.0011] |
| FMCA current_class | head_logloss_bits | Delta_L_given_E | HA | +0.0007 [-0.0001, +0.0015] |
| FMCA current_class | head_logloss_bits | Delta_L_given_E | NH | +0.0017 [-0.0006, +0.0040] |
| FMCA current_class | head_logloss_bits | Delta_L_given_E | all | +0.0009 [+0.0001, +0.0016] |
| FMCA current_class | head_logloss_bits | Delta_E_given_L | HA | +0.0002 [-0.0006, +0.0010] |
| FMCA current_class | head_logloss_bits | Delta_E_given_L | NH | +0.0002 [-0.0025, +0.0026] |
| FMCA current_class | head_logloss_bits | Delta_E_given_L | all | +0.0002 [-0.0006, +0.0009] |
| FMCA current_class | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0010 [-0.0035, +0.0015] |
| FMCA current_class | head_logloss_bits | Delta_E_given_L HA-NH | group difference | +0.0001 [-0.0024, +0.0028] |
| CS_SINGLE current_class | head_logloss_bits | Delta_L_given_E | HA | +0.0005 [-0.0003, +0.0013] |
| CS_SINGLE current_class | head_logloss_bits | Delta_L_given_E | NH | +0.0005 [-0.0029, +0.0035] |
| CS_SINGLE current_class | head_logloss_bits | Delta_L_given_E | all | +0.0005 [-0.0003, +0.0013] |
| CS_SINGLE current_class | head_logloss_bits | Delta_E_given_L | HA | +0.0003 [-0.0004, +0.0010] |
| CS_SINGLE current_class | head_logloss_bits | Delta_E_given_L | NH | +0.0007 [-0.0025, +0.0036] |
| CS_SINGLE current_class | head_logloss_bits | Delta_E_given_L | all | +0.0004 [-0.0004, +0.0011] |
| CS_SINGLE current_class | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0001 [-0.0032, +0.0037] |
| CS_SINGLE current_class | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0003 [-0.0032, +0.0030] |
| CS_MULTI current_class | head_logloss_bits | Delta_L_given_E | HA | +0.0015 [+0.0006, +0.0024] |
| CS_MULTI current_class | head_logloss_bits | Delta_L_given_E | NH | +0.0032 [+0.0013, +0.0050] |
| CS_MULTI current_class | head_logloss_bits | Delta_L_given_E | all | +0.0017 [+0.0009, +0.0025] |
| CS_MULTI current_class | head_logloss_bits | Delta_E_given_L | HA | +0.0016 [+0.0008, +0.0024] |
| CS_MULTI current_class | head_logloss_bits | Delta_E_given_L | NH | +0.0031 [+0.0014, +0.0048] |
| CS_MULTI current_class | head_logloss_bits | Delta_E_given_L | all | +0.0018 [+0.0011, +0.0026] |
| CS_MULTI current_class | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0017 [-0.0038, +0.0003] |
| CS_MULTI current_class | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0015 [-0.0035, +0.0003] |
| NCE current_class (balanced) | head_logloss_bits | Delta_L_given_E | HA | +0.0004 [-0.0001, +0.0010] |
| NCE current_class (balanced) | head_logloss_bits | Delta_L_given_E | NH | -0.0001 [-0.0012, +0.0009] |
| NCE current_class (balanced) | head_logloss_bits | Delta_L_given_E | all | +0.0004 [-0.0001, +0.0008] |
| NCE current_class (balanced) | head_logloss_bits | Delta_E_given_L | HA | +0.0006 [+0.0001, +0.0012] |
| NCE current_class (balanced) | head_logloss_bits | Delta_E_given_L | NH | +0.0004 [-0.0010, +0.0016] |
| NCE current_class (balanced) | head_logloss_bits | Delta_E_given_L | all | +0.0006 [+0.0001, +0.0011] |
| NCE current_class (balanced) | head_logloss_bits | Delta_L_given_E HA-NH | group difference | +0.0005 [-0.0007, +0.0018] |
| NCE current_class (balanced) | head_logloss_bits | Delta_E_given_L HA-NH | group difference | +0.0003 [-0.0011, +0.0017] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_L_given_E | HA | +0.0005 [-0.0001, +0.0011] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_L_given_E | NH | +0.0012 [-0.0001, +0.0027] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_L_given_E | all | +0.0006 [+0.0001, +0.0012] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_E_given_L | HA | +0.0004 [-0.0002, +0.0010] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_E_given_L | NH | +0.0013 [-0.0002, +0.0030] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_E_given_L | all | +0.0005 [-0.0001, +0.0011] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0006 [-0.0023, +0.0008] |
| FMCA current_class (balanced) | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0009 [-0.0028, +0.0007] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_L_given_E | HA | +0.0002 [-0.0004, +0.0009] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_L_given_E | NH | +0.0005 [-0.0012, +0.0022] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_L_given_E | all | +0.0003 [-0.0004, +0.0009] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_E_given_L | HA | +0.0008 [+0.0000, +0.0015] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_E_given_L | NH | +0.0022 [-0.0001, +0.0044] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_E_given_L | all | +0.0010 [+0.0002, +0.0017] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0003 [-0.0022, +0.0015] |
| CS_SINGLE current_class (balanced) | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0014 [-0.0038, +0.0011] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_L_given_E | HA | +0.0007 [-0.0002, +0.0014] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_L_given_E | NH | +0.0014 [-0.0011, +0.0040] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_L_given_E | all | +0.0008 [-0.0000, +0.0015] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_E_given_L | HA | +0.0004 [-0.0005, +0.0012] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_E_given_L | NH | +0.0017 [-0.0018, +0.0052] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_E_given_L | all | +0.0006 [-0.0003, +0.0015] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_L_given_E HA-NH | group difference | -0.0007 [-0.0035, +0.0020] |
| CS_MULTI current_class (balanced) | head_logloss_bits | Delta_E_given_L HA-NH | group difference | -0.0013 [-0.0047, +0.0024] |

