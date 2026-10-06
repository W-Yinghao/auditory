# Kernel CS-QMI full round: groups, CI training coverage, development and function

## FAU/TUD local/full: unified/gain_bits by group

| method | ci | ha | th |
|---|---|---|---|
| NCE | +0.4252 [+0.3103, +0.5423] | +0.9099 [+0.8248, +0.9953] | +0.8218 [+0.6847, +0.9702] |
| FMCA | +0.0691 [+0.0378, +0.1020] | +0.1316 [+0.1067, +0.1565] | +0.1483 [+0.1192, +0.1809] |
| CS_SINGLE | +0.2735 [+0.1869, +0.3631] | +0.4867 [+0.4075, +0.5683] | +0.5145 [+0.4165, +0.6187] |
| CS_MULTI | +0.1041 [+0.0652, +0.1411] | +0.1864 [+0.1574, +0.2159] | +0.2019 [+0.1771, +0.2287] |

### FAU/TUD: group differences (unified/gain_bits)

| method | window | contrast | difference |
|---|---|---|---|
| NCE | full | ci-th | -0.3965 [-0.5873, -0.2101] |
| NCE | full | ha-th | +0.0881 [-0.0876, +0.2560] |
| NCE | full | ci-ha | -0.4846 [-0.6260, -0.3383] |
| NCE | early | ci-th | -0.1518 [-0.2296, -0.0728] |
| NCE | early | ha-th | -0.0422 [-0.1253, +0.0441] |
| NCE | early | ci-ha | -0.1096 [-0.1972, -0.0243] |
| NCE | late | ci-th | -0.3710 [-0.5604, -0.1786] |
| NCE | late | ha-th | +0.0803 [-0.0837, +0.2394] |
| NCE | late | ci-ha | -0.4513 [-0.6083, -0.2868] |
| NCE | joint | ci-th | -0.5347 [-0.7956, -0.2774] |
| NCE | joint | ha-th | +0.1033 [-0.1205, +0.3313] |
| NCE | joint | ci-ha | -0.6380 [-0.8399, -0.4381] |
| FMCA | full | ci-th | -0.0792 [-0.1245, -0.0344] |
| FMCA | full | ha-th | -0.0167 [-0.0564, +0.0226] |
| FMCA | full | ci-ha | -0.0624 [-0.1023, -0.0208] |
| FMCA | early | ci-th | -0.0390 [-0.0756, -0.0029] |
| FMCA | early | ha-th | -0.0009 [-0.0408, +0.0394] |
| FMCA | early | ci-ha | -0.0382 [-0.0759, -0.0031] |
| FMCA | late | ci-th | -0.0703 [-0.1084, -0.0313] |
| FMCA | late | ha-th | -0.0093 [-0.0461, +0.0293] |
| FMCA | late | ci-ha | -0.0610 [-0.1022, -0.0212] |
| FMCA | joint | ci-th | -0.0760 [-0.1208, -0.0334] |
| FMCA | joint | ha-th | -0.0040 [-0.0476, +0.0383] |
| FMCA | joint | ci-ha | -0.0720 [-0.1118, -0.0333] |
| CS_SINGLE | full | ci-th | -0.2410 [-0.3787, -0.1041] |
| CS_SINGLE | full | ha-th | -0.0278 [-0.1622, +0.1020] |
| CS_SINGLE | full | ci-ha | -0.2132 [-0.3325, -0.0961] |
| CS_SINGLE | early | ci-th | -0.1116 [-0.1784, -0.0429] |
| CS_SINGLE | early | ha-th | -0.0347 [-0.1026, +0.0374] |
| CS_SINGLE | early | ci-ha | -0.0769 [-0.1520, -0.0055] |
| CS_SINGLE | late | ci-th | -0.2641 [-0.4189, -0.1133] |
| CS_SINGLE | late | ha-th | +0.0412 [-0.0953, +0.1737] |
| CS_SINGLE | late | ci-ha | -0.3053 [-0.4307, -0.1798] |
| CS_SINGLE | joint | ci-th | -0.3312 [-0.5088, -0.1621] |
| CS_SINGLE | joint | ha-th | +0.0323 [-0.1381, +0.1937] |
| CS_SINGLE | joint | ci-ha | -0.3635 [-0.4946, -0.2330] |
| CS_MULTI | full | ci-th | -0.0978 [-0.1455, -0.0532] |
| CS_MULTI | full | ha-th | -0.0155 [-0.0542, +0.0227] |
| CS_MULTI | full | ci-ha | -0.0823 [-0.1317, -0.0349] |
| CS_MULTI | early | ci-th | -0.0558 [-0.0917, -0.0188] |
| CS_MULTI | early | ha-th | -0.0094 [-0.0455, +0.0278] |
| CS_MULTI | early | ci-ha | -0.0464 [-0.0862, -0.0086] |
| CS_MULTI | late | ci-th | -0.0818 [-0.1480, -0.0173] |
| CS_MULTI | late | ha-th | +0.0475 [-0.0132, +0.1097] |
| CS_MULTI | late | ci-ha | -0.1292 [-0.1757, -0.0814] |
| CS_MULTI | joint | ci-th | -0.1749 [-0.2694, -0.0775] |
| CS_MULTI | joint | ha-th | +0.0597 [-0.0324, +0.1487] |
| CS_MULTI | joint | ci-ha | -0.2346 [-0.3041, -0.1619] |

## DTU local/full: unified/gain_bits by group

| method | hi | nh |
|---|---|---|
| NCE | +1.6213 [+1.4575, +1.7799] | +1.1664 [+1.0326, +1.2962] |
| FMCA | +0.3964 [+0.3415, +0.4507] | +0.2996 [+0.2494, +0.3492] |
| CS_SINGLE | +0.9460 [+0.8315, +1.0640] | +0.7319 [+0.6114, +0.8576] |
| CS_MULTI | +0.2496 [+0.2205, +0.2801] | +0.2110 [+0.1710, +0.2518] |

### DTU: group differences (unified/gain_bits)

| method | window | contrast | difference |
|---|---|---|---|
| NCE | full | hi-nh | +0.4548 [+0.2538, +0.6665] |
| NCE | early | hi-nh | +0.0089 [-0.1477, +0.1675] |
| NCE | late | hi-nh | +0.5316 [+0.3256, +0.7413] |
| NCE | joint | hi-nh | +0.5640 [+0.2668, +0.8653] |
| FMCA | full | hi-nh | +0.0968 [+0.0191, +0.1696] |
| FMCA | early | hi-nh | +0.0237 [-0.0555, +0.1028] |
| FMCA | late | hi-nh | +0.1673 [+0.0840, +0.2480] |
| FMCA | joint | hi-nh | +0.1399 [+0.0511, +0.2231] |
| CS_SINGLE | full | hi-nh | +0.2141 [+0.0429, +0.3852] |
| CS_SINGLE | early | hi-nh | -0.0240 [-0.1481, +0.1060] |
| CS_SINGLE | late | hi-nh | +0.3338 [+0.1364, +0.5297] |
| CS_SINGLE | joint | hi-nh | +0.3395 [+0.1399, +0.5550] |
| CS_MULTI | full | hi-nh | +0.0386 [-0.0137, +0.0917] |
| CS_MULTI | early | hi-nh | -0.0071 [-0.0511, +0.0357] |
| CS_MULTI | late | hi-nh | +0.1662 [+0.0554, +0.2737] |
| CS_MULTI | joint | hi-nh | +0.1735 [+0.0531, +0.2950] |

## Federici envelope/full: unified/gain_bits by group

| method | Artifact | CI | HC | HC-v |
|---|---|---|---|---|
| NCE | -0.0108 [-0.0286, +0.0094] | +0.0500 [+0.0240, +0.0779] | +0.0586 [+0.0393, +0.0777] | +0.0562 [+0.0311, +0.0829] |
| FMCA | +0.0211 [-0.0068, +0.0583] | +0.0560 [+0.0265, +0.0848] | +0.0691 [+0.0447, +0.0945] | +0.0542 [+0.0344, +0.0731] |
| CS_SINGLE | +0.0219 [-0.0016, +0.0480] | +0.1216 [+0.0781, +0.1708] | +0.0820 [+0.0568, +0.1081] | +0.0830 [+0.0431, +0.1230] |
| CS_MULTI | -0.0120 [-0.0287, +0.0036] | +0.0592 [+0.0334, +0.0864] | +0.0561 [+0.0336, +0.0786] | +0.0748 [+0.0399, +0.1096] |

### Federici: group differences (unified/gain_bits)

| method | window | contrast | difference |
|---|---|---|---|
| NCE | full | Artifact-HC | -0.0694 [-0.0957, -0.0420] |
| NCE | full | CI-HC | -0.0086 [-0.0422, +0.0248] |
| NCE | full | HC-v-HC | -0.0024 [-0.0335, +0.0308] |
| NCE | early | Artifact-HC | -0.1729 [-0.2625, -0.0828] |
| NCE | early | CI-HC | +0.0157 [-0.0710, +0.1112] |
| NCE | early | HC-v-HC | -0.0357 [-0.1338, +0.0637] |
| NCE | late | Artifact-HC | -0.0262 [-0.0442, -0.0074] |
| NCE | late | CI-HC | -0.0038 [-0.0259, +0.0175] |
| NCE | late | HC-v-HC | -0.0057 [-0.0325, +0.0225] |
| NCE | joint | Artifact-HC | -0.0838 [-0.1208, -0.0480] |
| NCE | joint | CI-HC | +0.0043 [-0.0311, +0.0380] |
| NCE | joint | HC-v-HC | +0.0025 [-0.0348, +0.0375] |
| FMCA | full | Artifact-HC | -0.0480 [-0.0867, -0.0047] |
| FMCA | full | CI-HC | -0.0132 [-0.0518, +0.0249] |
| FMCA | full | HC-v-HC | -0.0149 [-0.0470, +0.0164] |
| FMCA | early | Artifact-HC | -0.0209 [-0.0812, +0.0520] |
| FMCA | early | CI-HC | -0.0296 [-0.0768, +0.0182] |
| FMCA | early | HC-v-HC | +0.0066 [-0.0519, +0.0674] |
| FMCA | late | Artifact-HC | -0.0098 [-0.0346, +0.0124] |
| FMCA | late | CI-HC | +0.0019 [-0.0263, +0.0302] |
| FMCA | late | HC-v-HC | -0.0004 [-0.0256, +0.0248] |
| FMCA | joint | Artifact-HC | -0.0436 [-0.0762, -0.0110] |
| FMCA | joint | CI-HC | -0.0094 [-0.0435, +0.0260] |
| FMCA | joint | HC-v-HC | +0.0095 [-0.0317, +0.0498] |
| CS_SINGLE | full | Artifact-HC | -0.0601 [-0.0962, -0.0248] |
| CS_SINGLE | full | CI-HC | +0.0397 [-0.0109, +0.0937] |
| CS_SINGLE | full | HC-v-HC | +0.0010 [-0.0455, +0.0484] |
| CS_SINGLE | early | Artifact-HC | -0.0837 [-0.1494, -0.0200] |
| CS_SINGLE | early | CI-HC | -0.0080 [-0.0825, +0.0682] |
| CS_SINGLE | early | HC-v-HC | -0.0623 [-0.1286, +0.0054] |
| CS_SINGLE | late | Artifact-HC | -0.0173 [-0.0319, -0.0027] |
| CS_SINGLE | late | CI-HC | -0.0014 [-0.0185, +0.0155] |
| CS_SINGLE | late | HC-v-HC | +0.0003 [-0.0169, +0.0184] |
| CS_SINGLE | joint | Artifact-HC | -0.1820 [-0.2399, -0.1244] |
| CS_SINGLE | joint | CI-HC | +0.0247 [-0.0583, +0.1083] |
| CS_SINGLE | joint | HC-v-HC | -0.0128 [-0.0938, +0.0662] |
| CS_MULTI | full | Artifact-HC | -0.0681 [-0.0965, -0.0404] |
| CS_MULTI | full | CI-HC | +0.0030 [-0.0311, +0.0386] |
| CS_MULTI | full | HC-v-HC | +0.0187 [-0.0214, +0.0610] |
| CS_MULTI | early | Artifact-HC | -0.0599 [-0.1155, -0.0001] |
| CS_MULTI | early | CI-HC | +0.0058 [-0.0434, +0.0549] |
| CS_MULTI | early | HC-v-HC | -0.0316 [-0.0744, +0.0089] |
| CS_MULTI | late | Artifact-HC | -0.0301 [-0.0498, -0.0103] |
| CS_MULTI | late | CI-HC | +0.0168 [-0.0031, +0.0368] |
| CS_MULTI | late | HC-v-HC | +0.0221 [-0.0043, +0.0483] |
| CS_MULTI | joint | Artifact-HC | -0.0648 [-0.0918, -0.0371] |
| CS_MULTI | joint | CI-HC | +0.0215 [-0.0082, +0.0508] |
| CS_MULTI | joint | HC-v-HC | -0.0058 [-0.0394, +0.0261] |

## Private BDF current_class/full: head_gain_vs_base_bits by group

| method | HA | NH |
|---|---|---|
| NCE | -0.0008 [-0.0014, -0.0003] | -0.0014 [-0.0028, -0.0003] |
| FMCA | -0.0003 [-0.0014, +0.0008] | +0.0025 [-0.0009, +0.0055] |
| CS_SINGLE | +0.0000 [-0.0011, +0.0011] | +0.0035 [+0.0005, +0.0064] |
| CS_MULTI | -0.0011 [-0.0020, -0.0001] | +0.0014 [-0.0013, +0.0041] |

### Private BDF: group differences (head_gain_vs_base_bits)

| method | window | contrast | difference |
|---|---|---|---|
| NCE | full | HA-NH | +0.0006 [-0.0007, +0.0021] |
| NCE | early | HA-NH | +0.0003 [-0.0007, +0.0015] |
| NCE | late | HA-NH | +0.0004 [-0.0011, +0.0018] |
| NCE | joint | HA-NH | -0.0002 [-0.0011, +0.0007] |
| FMCA | full | HA-NH | -0.0028 [-0.0061, +0.0006] |
| FMCA | early | HA-NH | -0.0002 [-0.0017, +0.0013] |
| FMCA | late | HA-NH | -0.0012 [-0.0026, +0.0001] |
| FMCA | joint | HA-NH | -0.0012 [-0.0044, +0.0023] |
| CS_SINGLE | full | HA-NH | -0.0034 [-0.0065, -0.0001] |
| CS_SINGLE | early | HA-NH | -0.0007 [-0.0019, +0.0002] |
| CS_SINGLE | late | HA-NH | -0.0005 [-0.0017, +0.0008] |
| CS_SINGLE | joint | HA-NH | -0.0008 [-0.0043, +0.0029] |
| CS_MULTI | full | HA-NH | -0.0025 [-0.0053, +0.0003] |
| CS_MULTI | early | HA-NH | +0.0007 [-0.0007, +0.0024] |
| CS_MULTI | late | HA-NH | +0.0006 [-0.0010, +0.0023] |
| CS_MULTI | joint | HA-NH | -0.0009 [-0.0035, +0.0018] |

## CI training coverage (E7): TH+HA-trained minus jointly trained (TH+HA+CI), same test panel

| method | target | test group | Δ unified gain_bits | Δ native gain_bits |
|---|---|---|---|---|
| CS_MULTI | Ac | ci | +0.0393 [+0.0037, +0.0811] | +0.0217 [+0.0066, +0.0388] |
| CS_MULTI | Ac | ha | +0.0465 [+0.0131, +0.0822] | +0.0313 [+0.0148, +0.0470] |
| CS_MULTI | Ac | th | +0.0558 [+0.0200, +0.0899] | +0.0347 [+0.0078, +0.0587] |
| CS_MULTI | Ac | all | +0.0459 [+0.0254, +0.0680] | +0.0286 [+0.0184, +0.0392] |
| CS_MULTI | Lz | ci | +0.0083 [-0.0335, +0.0530] | +0.0241 [+0.0062, +0.0429] |
| CS_MULTI | Lz | ha | +0.0516 [+0.0190, +0.0834] | +0.0381 [+0.0209, +0.0562] |
| CS_MULTI | Lz | th | +0.0763 [+0.0312, +0.1241] | +0.0581 [+0.0272, +0.0928] |
| CS_MULTI | Lz | all | +0.0413 [+0.0178, +0.0652] | +0.0372 [+0.0252, +0.0492] |
| CS_MULTI | local | ci | -0.0014 [-0.0234, +0.0232] | +0.0089 [+0.0015, +0.0165] |
| CS_MULTI | local | ha | +0.0488 [+0.0300, +0.0689] | +0.0199 [+0.0133, +0.0264] |
| CS_MULTI | local | th | +0.0714 [+0.0479, +0.0935] | +0.0290 [+0.0183, +0.0404] |
| CS_MULTI | local | all | +0.0355 [+0.0213, +0.0499] | +0.0179 [+0.0130, +0.0230] |
| CS_SINGLE | Ac | ci | +0.0167 [-0.0189, +0.0546] | -0.0045 [-0.0403, +0.0282] |
| CS_SINGLE | Ac | ha | +0.0465 [+0.0215, +0.0719] | +0.0210 [-0.0042, +0.0461] |
| CS_SINGLE | Ac | th | +0.0458 [+0.0050, +0.0840] | +0.0226 [-0.0148, +0.0568] |
| CS_SINGLE | Ac | all | +0.0357 [+0.0168, +0.0547] | +0.0122 [-0.0057, +0.0295] |
| CS_SINGLE | Lz | ci | +0.0274 [-0.0161, +0.0726] | -0.0296 [-0.0690, +0.0088] |
| CS_SINGLE | Lz | ha | +0.0295 [-0.0069, +0.0665] | -0.0171 [-0.0518, +0.0173] |
| CS_SINGLE | Lz | th | +0.0233 [-0.0122, +0.0596] | -0.0271 [-0.0875, +0.0319] |
| CS_SINGLE | Lz | all | +0.0274 [+0.0046, +0.0506] | -0.0237 [-0.0470, -0.0002] |
| CS_SINGLE | local | ci | -0.0122 [-0.0441, +0.0209] | -0.0393 [-0.0707, -0.0081] |
| CS_SINGLE | local | ha | +0.0196 [-0.0072, +0.0462] | -0.0403 [-0.0796, -0.0028] |
| CS_SINGLE | local | th | +0.0258 [-0.0151, +0.0659] | -0.0373 [-0.0945, +0.0156] |
| CS_SINGLE | local | all | +0.0095 [-0.0089, +0.0292] | -0.0393 [-0.0628, -0.0165] |
| FMCA | Ac | ci | +0.0204 [+0.0025, +0.0387] | +0.0263 [+0.0122, +0.0416] |
| FMCA | Ac | ha | +0.0467 [+0.0225, +0.0707] | +0.0119 [-0.0146, +0.0398] |
| FMCA | Ac | th | +0.0515 [+0.0216, +0.0851] | +0.0062 [-0.0145, +0.0296] |
| FMCA | Ac | all | +0.0382 [+0.0242, +0.0525] | +0.0159 [+0.0023, +0.0298] |
| FMCA | Lz | ci | +0.0395 [+0.0121, +0.0667] | +0.0175 [-0.0014, +0.0369] |
| FMCA | Lz | ha | +0.0601 [+0.0357, +0.0843] | +0.0506 [+0.0160, +0.0927] |
| FMCA | Lz | th | +0.0698 [+0.0320, +0.1094] | +0.0433 [+0.0033, +0.0974] |
| FMCA | Lz | all | +0.0547 [+0.0381, +0.0710] | +0.0372 [+0.0182, +0.0586] |
| FMCA | local | ci | +0.0177 [+0.0006, +0.0362] | +0.0151 [+0.0024, +0.0282] |
| FMCA | local | ha | +0.0249 [+0.0122, +0.0376] | +0.0122 [-0.0064, +0.0321] |
| FMCA | local | th | +0.0106 [-0.0117, +0.0321] | -0.0081 [-0.0294, +0.0118] |
| FMCA | local | all | +0.0193 [+0.0097, +0.0294] | +0.0090 [-0.0024, +0.0198] |
| NCE | Ac | ci | -0.0585 [-0.1299, +0.0130] | -0.0359 [-0.0924, +0.0178] |
| NCE | Ac | ha | +0.0859 [+0.0455, +0.1284] | +0.0321 [-0.0526, +0.1119] |
| NCE | Ac | th | +0.1077 [+0.0528, +0.1681] | +0.0425 [-0.0694, +0.1528] |
| NCE | Ac | all | +0.0388 [+0.0000, +0.0756] | +0.0099 [-0.0388, +0.0564] |
| NCE | Lz | ci | -0.0038 [-0.0583, +0.0551] | -0.1095 [-0.1544, -0.0635] |
| NCE | Lz | ha | +0.1173 [+0.0740, +0.1613] | -0.0568 [-0.1078, +0.0001] |
| NCE | Lz | th | +0.0949 [+0.0486, +0.1406] | -0.0969 [-0.1393, -0.0521] |
| NCE | Lz | all | +0.0692 [+0.0363, +0.1012] | -0.0841 [-0.1141, -0.0512] |
| NCE | local | ci | -0.0055 [-0.0518, +0.0447] | -0.0519 [-0.0998, -0.0046] |
| NCE | local | ha | +0.1589 [+0.0831, +0.2309] | -0.0722 [-0.1322, -0.0147] |
| NCE | local | th | +0.1430 [+0.0763, +0.2111] | -0.0920 [-0.1298, -0.0529] |
| NCE | local | all | +0.0967 [+0.0537, +0.1398] | -0.0691 [-0.1001, -0.0380] |

## Development (spec §11.2)

Private: per window, OLS of the child-level value on calendar age (months) and HA; HA only: age and device-use duration.

| method | outcome | window | age slope (all) | HA − NH | age slope (HA) | duration slope (HA) |
|---|---|---|---|---|---|---|
| NCE | head_gain_vs_base_bits | early | -0.00000 [-0.00001, +0.00001] | +0.0004 [-0.0008, +0.0015] | +0.00000 [-0.00001, +0.00001] | -0.00001 [-0.00002, +0.00001] |
| NCE | head_gain_vs_base_bits | full | -0.00001 [-0.00002, +0.00000] | +0.0006 [-0.0007, +0.0022] | -0.00001 [-0.00003, +0.00000] | +0.00001 [-0.00002, +0.00003] |
| NCE | head_gain_vs_base_bits | joint | +0.00000 [-0.00001, +0.00001] | -0.0002 [-0.0011, +0.0008] | +0.00000 [-0.00001, +0.00001] | -0.00001 [-0.00002, +0.00001] |
| NCE | head_gain_vs_base_bits | late | +0.00000 [-0.00001, +0.00001] | +0.0004 [-0.0013, +0.0020] | +0.00001 [-0.00001, +0.00002] | -0.00000 [-0.00002, +0.00001] |
| NCE | hist_minus_twin_bits | early | +0.00000 [-0.00001, +0.00001] | -0.0004 [-0.0018, +0.0010] | +0.00001 [-0.00001, +0.00002] | -0.00001 [-0.00003, +0.00001] |
| NCE | hist_minus_twin_bits | full | -0.00001 [-0.00002, +0.00000] | +0.0005 [-0.0006, +0.0019] | -0.00001 [-0.00003, +0.00001] | -0.00000 [-0.00003, +0.00002] |
| NCE | hist_minus_twin_bits | joint | -0.00001 [-0.00002, +0.00001] | +0.0005 [-0.0006, +0.0016] | -0.00000 [-0.00002, +0.00001] | -0.00001 [-0.00002, +0.00001] |
| NCE | hist_minus_twin_bits | late | -0.00000 [-0.00002, +0.00002] | +0.0010 [+0.0000, +0.0020] | -0.00000 [-0.00002, +0.00002] | +0.00000 [-0.00002, +0.00003] |
| NCE | head_auc | early | -0.00000 [-0.00011, +0.00012] | +0.0037 [-0.0113, +0.0179] | +0.00005 [-0.00008, +0.00016] | -0.00005 [-0.00021, +0.00013] |
| NCE | head_auc | full | -0.00007 [-0.00020, +0.00006] | +0.0050 [-0.0092, +0.0207] | -0.00007 [-0.00028, +0.00011] | +0.00005 [-0.00019, +0.00026] |
| NCE | head_auc | joint | -0.00002 [-0.00011, +0.00006] | +0.0001 [-0.0109, +0.0109] | +0.00001 [-0.00008, +0.00012] | -0.00010 [-0.00026, +0.00004] |
| NCE | head_auc | late | +0.00004 [-0.00006, +0.00013] | +0.0015 [-0.0134, +0.0165] | +0.00006 [-0.00007, +0.00019] | -0.00004 [-0.00021, +0.00014] |
| FMCA | head_gain_vs_base_bits | early | +0.00001 [-0.00000, +0.00002] | -0.0003 [-0.0018, +0.0012] | +0.00001 [-0.00001, +0.00003] | -0.00000 [-0.00002, +0.00002] |
| FMCA | head_gain_vs_base_bits | full | +0.00002 [-0.00000, +0.00005] | -0.0028 [-0.0065, +0.0007] | +0.00003 [-0.00000, +0.00005] | +0.00001 [-0.00003, +0.00004] |
| FMCA | head_gain_vs_base_bits | joint | +0.00000 [-0.00001, +0.00002] | -0.0012 [-0.0047, +0.0024] | -0.00001 [-0.00004, +0.00002] | +0.00002 [-0.00002, +0.00006] |
| FMCA | head_gain_vs_base_bits | late | +0.00001 [-0.00001, +0.00002] | -0.0013 [-0.0028, +0.0003] | +0.00000 [-0.00002, +0.00003] | +0.00002 [-0.00001, +0.00005] |
| FMCA | hist_minus_twin_bits | early | -0.00000 [-0.00003, +0.00002] | -0.0000 [-0.0019, +0.0015] | -0.00001 [-0.00003, +0.00002] | -0.00001 [-0.00003, +0.00002] |
| FMCA | hist_minus_twin_bits | full | +0.00001 [-0.00001, +0.00003] | -0.0013 [-0.0037, +0.0009] | +0.00000 [-0.00003, +0.00003] | +0.00003 [-0.00001, +0.00006] |
| FMCA | hist_minus_twin_bits | joint | -0.00000 [-0.00003, +0.00002] | -0.0009 [-0.0037, +0.0018] | -0.00002 [-0.00006, +0.00001] | +0.00003 [-0.00001, +0.00007] |
| FMCA | hist_minus_twin_bits | late | +0.00001 [-0.00001, +0.00005] | +0.0010 [-0.0008, +0.0032] | +0.00001 [-0.00003, +0.00004] | +0.00003 [+0.00000, +0.00006] |
| FMCA | head_auc | early | +0.00011 [-0.00002, +0.00023] | -0.0052 [-0.0202, +0.0104] | +0.00007 [-0.00011, +0.00026] | +0.00003 [-0.00023, +0.00026] |
| FMCA | head_auc | full | +0.00010 [-0.00011, +0.00033] | -0.0199 [-0.0486, +0.0084] | +0.00014 [-0.00010, +0.00034] | +0.00000 [-0.00027, +0.00027] |
| FMCA | head_auc | joint | +0.00003 [-0.00014, +0.00020] | -0.0184 [-0.0527, +0.0143] | +0.00000 [-0.00028, +0.00023] | +0.00002 [-0.00028, +0.00040] |
| FMCA | head_auc | late | +0.00003 [-0.00013, +0.00018] | -0.0095 [-0.0267, +0.0058] | +0.00003 [-0.00020, +0.00022] | +0.00006 [-0.00016, +0.00030] |
| CS_SINGLE | head_gain_vs_base_bits | early | -0.00000 [-0.00001, +0.00001] | -0.0007 [-0.0020, +0.0003] | -0.00000 [-0.00002, +0.00001] | +0.00001 [-0.00000, +0.00003] |
| CS_SINGLE | head_gain_vs_base_bits | full | +0.00001 [-0.00001, +0.00003] | -0.0035 [-0.0069, -0.0001] | +0.00001 [-0.00003, +0.00004] | -0.00001 [-0.00005, +0.00003] |
| CS_SINGLE | head_gain_vs_base_bits | joint | +0.00001 [-0.00001, +0.00003] | -0.0008 [-0.0046, +0.0029] | +0.00001 [-0.00002, +0.00003] | +0.00001 [-0.00002, +0.00005] |
| CS_SINGLE | head_gain_vs_base_bits | late | +0.00001 [-0.00000, +0.00003] | -0.0005 [-0.0021, +0.0009] | +0.00001 [-0.00001, +0.00003] | +0.00001 [-0.00001, +0.00004] |
| CS_SINGLE | hist_minus_twin_bits | early | -0.00000 [-0.00002, +0.00001] | -0.0003 [-0.0021, +0.0012] | -0.00001 [-0.00002, +0.00001] | +0.00001 [-0.00001, +0.00003] |
| CS_SINGLE | hist_minus_twin_bits | full | -0.00001 [-0.00003, +0.00002] | -0.0018 [-0.0047, +0.0009] | -0.00000 [-0.00004, +0.00003] | -0.00001 [-0.00004, +0.00003] |
| CS_SINGLE | hist_minus_twin_bits | joint | +0.00000 [-0.00002, +0.00002] | -0.0004 [-0.0030, +0.0019] | -0.00001 [-0.00003, +0.00001] | +0.00002 [-0.00001, +0.00005] |
| CS_SINGLE | hist_minus_twin_bits | late | +0.00001 [-0.00000, +0.00003] | -0.0010 [-0.0027, +0.0007] | +0.00001 [-0.00001, +0.00003] | +0.00001 [-0.00001, +0.00003] |
| CS_SINGLE | head_auc | early | +0.00002 [-0.00011, +0.00017] | -0.0084 [-0.0230, +0.0049] | -0.00001 [-0.00020, +0.00018] | +0.00010 [-0.00006, +0.00031] |
| CS_SINGLE | head_auc | full | +0.00007 [-0.00009, +0.00024] | -0.0294 [-0.0529, -0.0068] | +0.00012 [-0.00015, +0.00037] | -0.00010 [-0.00038, +0.00021] |
| CS_SINGLE | head_auc | joint | +0.00009 [-0.00006, +0.00023] | -0.0129 [-0.0387, +0.0137] | +0.00008 [-0.00013, +0.00024] | +0.00004 [-0.00020, +0.00034] |
| CS_SINGLE | head_auc | late | +0.00010 [-0.00003, +0.00023] | -0.0060 [-0.0173, +0.0049] | +0.00008 [-0.00013, +0.00024] | +0.00012 [-0.00007, +0.00036] |
| CS_MULTI | head_gain_vs_base_bits | early | +0.00001 [-0.00001, +0.00002] | +0.0007 [-0.0008, +0.0024] | +0.00000 [-0.00002, +0.00002] | +0.00000 [-0.00002, +0.00002] |
| CS_MULTI | head_gain_vs_base_bits | full | +0.00002 [-0.00001, +0.00004] | -0.0025 [-0.0056, +0.0004] | +0.00002 [-0.00001, +0.00005] | -0.00001 [-0.00005, +0.00003] |
| CS_MULTI | head_gain_vs_base_bits | joint | +0.00000 [-0.00001, +0.00002] | -0.0009 [-0.0038, +0.0018] | -0.00000 [-0.00003, +0.00002] | +0.00001 [-0.00002, +0.00005] |
| CS_MULTI | head_gain_vs_base_bits | late | -0.00000 [-0.00001, +0.00001] | +0.0006 [-0.0012, +0.0024] | +0.00000 [-0.00002, +0.00002] | -0.00001 [-0.00003, +0.00001] |
| CS_MULTI | hist_minus_twin_bits | early | -0.00001 [-0.00003, +0.00001] | +0.0001 [-0.0022, +0.0023] | -0.00002 [-0.00005, +0.00001] | +0.00002 [-0.00001, +0.00004] |
| CS_MULTI | hist_minus_twin_bits | full | +0.00002 [-0.00000, +0.00004] | -0.0010 [-0.0034, +0.0013] | +0.00001 [-0.00002, +0.00004] | +0.00001 [-0.00002, +0.00006] |
| CS_MULTI | hist_minus_twin_bits | joint | +0.00000 [-0.00002, +0.00002] | +0.0009 [-0.0013, +0.0030] | -0.00001 [-0.00003, +0.00002] | +0.00002 [-0.00000, +0.00004] |
| CS_MULTI | hist_minus_twin_bits | late | +0.00000 [-0.00001, +0.00002] | +0.0009 [-0.0003, +0.0020] | +0.00000 [-0.00002, +0.00002] | +0.00001 [-0.00001, +0.00003] |
| CS_MULTI | head_auc | early | +0.00004 [-0.00007, +0.00014] | +0.0066 [-0.0082, +0.0213] | +0.00001 [-0.00015, +0.00016] | -0.00004 [-0.00026, +0.00015] |
| CS_MULTI | head_auc | full | +0.00010 [-0.00007, +0.00026] | -0.0219 [-0.0430, -0.0014] | +0.00017 [-0.00005, +0.00035] | -0.00012 [-0.00038, +0.00017] |
| CS_MULTI | head_auc | joint | +0.00002 [-0.00014, +0.00019] | -0.0109 [-0.0338, +0.0109] | -0.00000 [-0.00024, +0.00022] | +0.00006 [-0.00019, +0.00036] |
| CS_MULTI | head_auc | late | -0.00005 [-0.00016, +0.00007] | +0.0041 [-0.0113, +0.0187] | -0.00000 [-0.00013, +0.00015] | -0.00009 [-0.00029, +0.00011] |

Federici: OLS slope of the participant-level gain on age (years), within group.

| method|window | outcome|group | age slope | n |
|---|---|---|---|
| NCE|full | unified/gain_bits|HC|age_slope | +0.0011 [-0.0036, +0.0059] | 37 |
| NCE|full | unified/gain_bits|CI|age_slope | +0.0096 [-0.0017, +0.0264] | 15 |
| NCE|full | unified/gain_bits|HC-v|age_slope | -0.0041 [-0.0117, +0.0036] | 16 |
| NCE|full | native/gain_bits|HC|age_slope | +0.0065 [-0.0031, +0.0157] | 37 |
| NCE|full | native/gain_bits|CI|age_slope | +0.0029 [-0.0259, +0.0344] | 15 |
| NCE|full | native/gain_bits|HC-v|age_slope | +0.0042 [-0.0136, +0.0220] | 16 |
| NCE|early | unified/gain_bits|HC|age_slope | -0.0103 [-0.0218, +0.0007] | 37 |
| NCE|early | unified/gain_bits|CI|age_slope | +0.0188 [-0.0083, +0.0598] | 15 |
| NCE|early | unified/gain_bits|HC-v|age_slope | +0.0070 [-0.0231, +0.0387] | 16 |
| NCE|early | native/gain_bits|HC|age_slope | -0.0179 [-0.0334, -0.0040] | 37 |
| NCE|early | native/gain_bits|CI|age_slope | +0.0473 [+0.0025, +0.1034] | 15 |
| NCE|early | native/gain_bits|HC-v|age_slope | +0.0081 [-0.0119, +0.0329] | 16 |
| NCE|late | unified/gain_bits|HC|age_slope | +0.0002 [-0.0029, +0.0034] | 37 |
| NCE|late | unified/gain_bits|CI|age_slope | +0.0047 [-0.0016, +0.0118] | 15 |
| NCE|late | unified/gain_bits|HC-v|age_slope | +0.0021 [-0.0065, +0.0107] | 16 |
| NCE|late | native/gain_bits|HC|age_slope | +0.0074 [-0.0000, +0.0162] | 37 |
| NCE|late | native/gain_bits|CI|age_slope | +0.0145 [-0.0226, +0.0559] | 15 |
| NCE|late | native/gain_bits|HC-v|age_slope | -0.0023 [-0.0205, +0.0167] | 16 |
| NCE|joint | unified/gain_bits|HC|age_slope | -0.0018 [-0.0077, +0.0032] | 37 |
| NCE|joint | unified/gain_bits|CI|age_slope | +0.0038 [-0.0101, +0.0164] | 15 |
| NCE|joint | unified/gain_bits|HC-v|age_slope | +0.0019 [-0.0100, +0.0123] | 16 |
| NCE|joint | native/gain_bits|HC|age_slope | -0.0014 [-0.0151, +0.0119] | 37 |
| NCE|joint | native/gain_bits|CI|age_slope | +0.0191 [-0.0146, +0.0560] | 15 |
| NCE|joint | native/gain_bits|HC-v|age_slope | +0.0021 [-0.0148, +0.0227] | 16 |
| FMCA|full | unified/gain_bits|HC|age_slope | -0.0055 [-0.0099, -0.0005] | 37 |
| FMCA|full | unified/gain_bits|CI|age_slope | +0.0043 [-0.0070, +0.0158] | 15 |
| FMCA|full | unified/gain_bits|HC-v|age_slope | -0.0051 [-0.0112, +0.0003] | 16 |
| FMCA|full | native/gain_bits|HC|age_slope | -0.0027 [-0.0074, +0.0026] | 37 |
| FMCA|full | native/gain_bits|CI|age_slope | +0.0048 [-0.0045, +0.0169] | 15 |
| FMCA|full | native/gain_bits|HC-v|age_slope | -0.0085 [-0.0193, +0.0027] | 16 |
| FMCA|early | unified/gain_bits|HC|age_slope | -0.0097 [-0.0157, -0.0016] | 37 |
| FMCA|early | unified/gain_bits|CI|age_slope | +0.0008 [-0.0130, +0.0148] | 15 |
| FMCA|early | unified/gain_bits|HC-v|age_slope | +0.0181 [+0.0008, +0.0334] | 16 |
| FMCA|early | native/gain_bits|HC|age_slope | -0.0077 [-0.0150, -0.0007] | 37 |
| FMCA|early | native/gain_bits|CI|age_slope | +0.0165 [+0.0006, +0.0393] | 15 |
| FMCA|early | native/gain_bits|HC-v|age_slope | +0.0163 [+0.0056, +0.0258] | 16 |
| FMCA|late | unified/gain_bits|HC|age_slope | -0.0025 [-0.0059, +0.0008] | 37 |
| FMCA|late | unified/gain_bits|CI|age_slope | +0.0117 [+0.0056, +0.0192] | 15 |
| FMCA|late | unified/gain_bits|HC-v|age_slope | -0.0045 [-0.0109, +0.0036] | 16 |
| FMCA|late | native/gain_bits|HC|age_slope | +0.0000 [-0.0084, +0.0074] | 37 |
| FMCA|late | native/gain_bits|CI|age_slope | +0.0132 [+0.0013, +0.0263] | 15 |
| FMCA|late | native/gain_bits|HC-v|age_slope | +0.0036 [-0.0048, +0.0125] | 16 |
| FMCA|joint | unified/gain_bits|HC|age_slope | -0.0067 [-0.0112, -0.0020] | 37 |
| FMCA|joint | unified/gain_bits|CI|age_slope | +0.0076 [-0.0022, +0.0197] | 15 |
| FMCA|joint | unified/gain_bits|HC-v|age_slope | +0.0072 [-0.0045, +0.0182] | 16 |
| FMCA|joint | native/gain_bits|HC|age_slope | -0.0048 [-0.0089, +0.0002] | 37 |
| FMCA|joint | native/gain_bits|CI|age_slope | +0.0083 [-0.0025, +0.0179] | 15 |
| FMCA|joint | native/gain_bits|HC-v|age_slope | +0.0081 [+0.0008, +0.0151] | 16 |
| CS_SINGLE|full | unified/gain_bits|HC|age_slope | +0.0022 [-0.0035, +0.0066] | 37 |
| CS_SINGLE|full | unified/gain_bits|CI|age_slope | +0.0064 [-0.0147, +0.0309] | 15 |
| CS_SINGLE|full | unified/gain_bits|HC-v|age_slope | -0.0012 [-0.0172, +0.0156] | 16 |
| CS_SINGLE|full | native/gain_bits|HC|age_slope | +0.0040 [+0.0001, +0.0083] | 37 |
| CS_SINGLE|full | native/gain_bits|CI|age_slope | -0.0032 [-0.0139, +0.0054] | 15 |
| CS_SINGLE|full | native/gain_bits|HC-v|age_slope | -0.0063 [-0.0158, +0.0052] | 16 |
| CS_SINGLE|early | unified/gain_bits|HC|age_slope | -0.0156 [-0.0247, -0.0068] | 37 |
| CS_SINGLE|early | unified/gain_bits|CI|age_slope | +0.0030 [-0.0153, +0.0331] | 15 |
| CS_SINGLE|early | unified/gain_bits|HC-v|age_slope | +0.0045 [-0.0114, +0.0230] | 16 |
| CS_SINGLE|early | native/gain_bits|HC|age_slope | -0.0045 [-0.0113, +0.0019] | 37 |
| CS_SINGLE|early | native/gain_bits|CI|age_slope | -0.0010 [-0.0065, +0.0067] | 15 |
| CS_SINGLE|early | native/gain_bits|HC-v|age_slope | +0.0038 [-0.0045, +0.0128] | 16 |
| CS_SINGLE|late | unified/gain_bits|HC|age_slope | -0.0014 [-0.0043, +0.0014] | 37 |
| CS_SINGLE|late | unified/gain_bits|CI|age_slope | +0.0047 [-0.0022, +0.0144] | 15 |
| CS_SINGLE|late | unified/gain_bits|HC-v|age_slope | -0.0001 [-0.0051, +0.0043] | 16 |
| CS_SINGLE|late | native/gain_bits|HC|age_slope | +0.0048 [-0.0035, +0.0139] | 37 |
| CS_SINGLE|late | native/gain_bits|CI|age_slope | -0.0018 [-0.0172, +0.0138] | 15 |
| CS_SINGLE|late | native/gain_bits|HC-v|age_slope | -0.0066 [-0.0266, +0.0132] | 16 |
| CS_SINGLE|joint | unified/gain_bits|HC|age_slope | -0.0142 [-0.0259, -0.0025] | 37 |
| CS_SINGLE|joint | unified/gain_bits|CI|age_slope | +0.0181 [-0.0063, +0.0514] | 15 |
| CS_SINGLE|joint | unified/gain_bits|HC-v|age_slope | +0.0017 [-0.0177, +0.0243] | 16 |
| CS_SINGLE|joint | native/gain_bits|HC|age_slope | -0.0070 [-0.0120, -0.0021] | 37 |
| CS_SINGLE|joint | native/gain_bits|CI|age_slope | -0.0006 [-0.0197, +0.0279] | 15 |
| CS_SINGLE|joint | native/gain_bits|HC-v|age_slope | -0.0022 [-0.0173, +0.0159] | 16 |
| CS_MULTI|full | unified/gain_bits|HC|age_slope | -0.0054 [-0.0113, -0.0005] | 37 |
| CS_MULTI|full | unified/gain_bits|CI|age_slope | +0.0012 [-0.0074, +0.0109] | 15 |
| CS_MULTI|full | unified/gain_bits|HC-v|age_slope | -0.0001 [-0.0149, +0.0147] | 16 |
| CS_MULTI|full | native/gain_bits|HC|age_slope | -0.0003 [-0.0011, +0.0004] | 37 |
| CS_MULTI|full | native/gain_bits|CI|age_slope | +0.0016 [-0.0015, +0.0042] | 15 |
| CS_MULTI|full | native/gain_bits|HC-v|age_slope | +0.0004 [-0.0013, +0.0020] | 16 |
| CS_MULTI|early | unified/gain_bits|HC|age_slope | -0.0075 [-0.0139, -0.0010] | 37 |
| CS_MULTI|early | unified/gain_bits|CI|age_slope | +0.0002 [-0.0158, +0.0181] | 15 |
| CS_MULTI|early | unified/gain_bits|HC-v|age_slope | +0.0027 [-0.0069, +0.0145] | 16 |
| CS_MULTI|early | native/gain_bits|HC|age_slope | -0.0002 [-0.0004, +0.0000] | 37 |
| CS_MULTI|early | native/gain_bits|CI|age_slope | +0.0005 [-0.0003, +0.0017] | 15 |
| CS_MULTI|early | native/gain_bits|HC-v|age_slope | +0.0001 [-0.0002, +0.0006] | 16 |
| CS_MULTI|late | unified/gain_bits|HC|age_slope | +0.0009 [-0.0019, +0.0036] | 37 |
| CS_MULTI|late | unified/gain_bits|CI|age_slope | +0.0031 [-0.0045, +0.0100] | 15 |
| CS_MULTI|late | unified/gain_bits|HC-v|age_slope | -0.0002 [-0.0093, +0.0094] | 16 |
| CS_MULTI|late | native/gain_bits|HC|age_slope | +0.0001 [-0.0003, +0.0007] | 37 |
| CS_MULTI|late | native/gain_bits|CI|age_slope | +0.0006 [-0.0009, +0.0022] | 15 |
| CS_MULTI|late | native/gain_bits|HC-v|age_slope | +0.0005 [-0.0003, +0.0011] | 16 |
| CS_MULTI|joint | unified/gain_bits|HC|age_slope | -0.0051 [-0.0097, -0.0001] | 37 |
| CS_MULTI|joint | unified/gain_bits|CI|age_slope | +0.0013 [-0.0073, +0.0117] | 15 |
| CS_MULTI|joint | unified/gain_bits|HC-v|age_slope | +0.0076 [-0.0014, +0.0162] | 16 |
| CS_MULTI|joint | native/gain_bits|HC|age_slope | -0.0005 [-0.0010, +0.0001] | 37 |
| CS_MULTI|joint | native/gain_bits|CI|age_slope | +0.0004 [-0.0014, +0.0028] | 15 |
| CS_MULTI|joint | native/gain_bits|HC-v|age_slope | +0.0012 [+0.0001, +0.0027] | 16 |

## Function (spec §11.3): C → C + overall alignment → C + overall + temporal structure

LOO-OLS squared-error risk; differences are bigger − smaller model (negative = the added block improves held-out prediction).

| endpoint | n | +overall | +temporal structure |
|---|---|---|---|
| dtu|CS_MULTI|native/gain_bits|SRT | 44 | +0.041 [-0.054, +0.167] | +0.031 [-0.148, +0.217] |
| dtu|CS_MULTI|unified/gain_bits|SRT | 44 | +0.064 [+0.002, +0.135] | +0.087 [-0.041, +0.229] |
| dtu|CS_SINGLE|native/gain_bits|SRT | 44 | +0.090 [+0.024, +0.194] | +0.077 [-0.024, +0.179] |
| dtu|CS_SINGLE|unified/gain_bits|SRT | 44 | +0.068 [+0.022, +0.130] | -0.071 [-0.279, +0.120] |
| dtu|FMCA|native/gain_bits|SRT | 44 | +0.049 [-0.046, +0.149] | +0.080 [+0.030, +0.144] |
| dtu|FMCA|unified/gain_bits|SRT | 44 | +0.073 [-0.060, +0.234] | +0.095 [+0.024, +0.179] |
| dtu|NCE|native/gain_bits|SRT | 44 | +0.063 [-0.016, +0.155] | +0.002 [-0.171, +0.186] |
| dtu|NCE|unified/gain_bits|SRT | 44 | +0.044 [-0.024, +0.115] | -0.117 [-0.311, +0.074] |
| fau_ci|CS_MULTI|native/gain_bits|HSM_logit | 22 | -0.110 [-0.717, +0.546] | +0.003 [-0.681, +0.823] |
| fau_ci|CS_MULTI|unified/gain_bits|HSM_logit | 22 | -0.079 [-0.689, +0.526] | +0.328 [-0.796, +1.721] |
| fau_ci|CS_SINGLE|native/gain_bits|HSM_logit | 22 | +0.192 [-0.011, +0.447] | -0.402 [-1.898, +1.024] |
| fau_ci|CS_SINGLE|unified/gain_bits|HSM_logit | 22 | +0.223 [-0.049, +0.590] | -0.252 [-1.562, +0.995] |
| fau_ci|FMCA|native/gain_bits|HSM_logit | 22 | +0.504 [+0.051, +1.207] | +1.715 [+0.387, +3.974] |
| fau_ci|FMCA|unified/gain_bits|HSM_logit | 22 | +0.314 [+0.105, +0.571] | +0.486 [-0.046, +1.139] |
| fau_ci|NCE|native/gain_bits|HSM_logit | 22 | +0.265 [+0.064, +0.529] | -0.422 [-1.804, +0.806] |
| fau_ci|NCE|unified/gain_bits|HSM_logit | 22 | +0.265 [-0.147, +0.852] | -0.578 [-1.651, +0.506] |
| federici|CS_MULTI|native/gain_bits|behav_acc | 52 | +9.402 [-19.956, +47.167] | +32.948 [+5.390, +70.119] |
| federici|CS_MULTI|unified/gain_bits|behav_acc | 52 | +10.166 [-2.569, +24.160] | +16.380 [+4.900, +29.295] |
| federici|CS_SINGLE|native/gain_bits|behav_acc | 52 | +12.521 [-5.624, +36.671] | +34.138 [+6.413, +82.714] |
| federici|CS_SINGLE|unified/gain_bits|behav_acc | 52 | +9.917 [+5.095, +15.896] | +24.172 [-9.925, +70.711] |
| federici|FMCA|native/gain_bits|behav_acc | 52 | +6.546 [-8.400, +23.088] | +16.007 [-16.889, +54.075] |
| federici|FMCA|unified/gain_bits|behav_acc | 52 | +7.057 [-0.372, +15.227] | +8.515 [-24.491, +42.886] |
| federici|NCE|native/gain_bits|behav_acc | 52 | +7.892 [-2.563, +22.005] | +15.212 [+1.061, +31.634] |
| federici|NCE|unified/gain_bits|behav_acc | 52 | +9.079 [+0.205, +18.442] | +14.490 [-27.620, +60.472] |

