# Frozen retrieval-source transfer to attention

2026-10-18T19:49:10.274803+02:00, CPU job1045980; **interim**, 48/160 units.

New aligned/true-full encoders were trained for single-speaker retrieval. Integrators and source-model policy are selected using inner listeners; outer attention is not used for selection. Paired candidate orders share one physical window.5/10/20s are evidence durations. All fixed alternatives and direct group interactions are retained in the JSON.

## dtu / policy/attention_transfer/10s / native/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0021 | [-0.0063,+0.0021] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0021 | [-0.0058,+0.0016] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0163 | [-0.0296,-0.0030] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0014 | [-0.0054,+0.0025] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0001 | [-0.0033,+0.0035] |
| local/antisymmetric versus local/mean | +0.0002 | [-0.0041,+0.0046] |
| local/selected versus local/mean | -0.0003 | [-0.0031,+0.0025] |
| cbramod/pretrained_full/selected versus local/selected | +0.0228 | [+0.0025,+0.0431] |
| cbramod/random_full/selected versus local/selected | +0.0069 | [-0.0133,+0.0271] |
| inner_selected_model versus local/selected | +0.0065 | [-0.0142,+0.0271] |
| reve/pretrained_full/selected versus local/selected | +0.0052 | [-0.0169,+0.0273] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0004 | [-0.0044,+0.0035] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0008 | [-0.0040,+0.0025] |

## dtu / policy/attention_transfer/10s / native/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0023 | [-0.0116,+0.0069] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [-0.0053,+0.0053] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0124 | [-0.0514,+0.0265] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0051 | [-0.0065,+0.0168] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0030 | [-0.0077,+0.0136] |
| local/antisymmetric versus local/mean | +0.0006 | [-0.0164,+0.0175] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | -0.0038 | [-0.0657,+0.0580] |
| cbramod/random_full/selected versus local/selected | -0.0162 | [-0.0765,+0.0440] |
| inner_selected_model versus local/selected | -0.0162 | [-0.0765,+0.0440] |
| reve/pretrained_full/selected versus local/selected | -0.0271 | [-0.0829,+0.0287] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0023 | [-0.0123,+0.0169] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0029 | [-0.0110,+0.0168] |

## dtu / policy/attention_transfer/10s / native/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0059 | [-0.0018,+0.0136] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0038 | [-0.0023,+0.0099] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0378 | [-0.0602,-0.0154] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0043 | [-0.0084,-0.0002] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0038 | [-0.0069,-0.0006] |
| local/antisymmetric versus local/mean | -0.0010 | [-0.0066,+0.0047] |
| local/selected versus local/mean | +0.0003 | [-0.0050,+0.0056] |
| cbramod/pretrained_full/selected versus local/selected | +0.0449 | [+0.0023,+0.0875] |
| cbramod/random_full/selected versus local/selected | +0.0093 | [-0.0295,+0.0482] |
| inner_selected_model versus local/selected | +0.0071 | [-0.0329,+0.0471] |
| reve/pretrained_full/selected versus local/selected | +0.0054 | [-0.0377,+0.0484] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0028 | [-0.0024,+0.0080] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0026 | [-0.0021,+0.0072] |

## dtu / policy/attention_transfer/10s / native/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0084 | [-0.0279,+0.0446] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0010 | [-0.0117,+0.0096] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0075 | [-0.1131,+0.1281] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0049 | [-0.0481,+0.0383] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0001 | [-0.0128,+0.0126] |
| local/antisymmetric versus local/mean | -0.0030 | [-0.0130,+0.0069] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0125 | [-0.1570,+0.1821] |
| cbramod/random_full/selected versus local/selected | +0.0200 | [-0.1343,+0.1742] |
| inner_selected_model versus local/selected | +0.0200 | [-0.1343,+0.1742] |
| reve/pretrained_full/selected versus local/selected | -0.0111 | [-0.1454,+0.1232] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0060 | [-0.0335,+0.0215] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0028 | [-0.0136,+0.0080] |

## dtu / policy/attention_transfer/10s / unified/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0009 | [-0.0022,+0.0041] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0003 | [-0.0019,+0.0025] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0068 | [-0.0192,+0.0057] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0002 | [-0.0029,+0.0032] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0001 | [-0.0015,+0.0013] |
| local/antisymmetric versus local/mean | -0.0001 | [-0.0025,+0.0024] |
| local/selected versus local/mean | -0.0000 | [-0.0016,+0.0016] |
| cbramod/pretrained_full/selected versus local/selected | +0.0224 | [+0.0022,+0.0426] |
| cbramod/random_full/selected versus local/selected | -0.0005 | [-0.0191,+0.0181] |
| inner_selected_model versus local/selected | +0.0156 | [-0.0028,+0.0340] |
| reve/pretrained_full/selected versus local/selected | -0.0004 | [-0.0211,+0.0204] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0009 | [-0.0031,+0.0048] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [-0.0028,+0.0028] |

## dtu / policy/attention_transfer/10s / unified/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0001 | [-1.8021,+1.8022] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0118 | [-12.8232,+12.7996] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0007 | [-2.0290,+2.0304] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0007 | [-2.0290,+2.0304] |
| local/antisymmetric versus local/mean | +0.0000 | [-2.4612,+2.4612] |
| local/selected versus local/mean | +0.0008 | [-2.0521,+2.0538] |
| cbramod/pretrained_full/selected versus local/selected | +0.0107 | [-23.8470,+23.8684] |
| cbramod/random_full/selected versus local/selected | -0.0042 | [-20.3821,+20.3737] |
| inner_selected_model versus local/selected | -0.0011 | [-23.3483,+23.3461] |
| reve/pretrained_full/selected versus local/selected | -0.0117 | [-19.8905,+19.8671] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0017 | [-1.6568,+1.6601] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0017 | [-1.6568,+1.6601] |

## dtu / policy/attention_transfer/10s / unified/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0026 | [-0.0055,+0.0004] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0018 | [-0.0044,+0.0009] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0172 | [-0.0325,-0.0020] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0022 | [-0.0029,+0.0074] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0004 | [-0.0019,+0.0027] |
| local/antisymmetric versus local/mean | +0.0023 | [-0.0005,+0.0050] |
| local/selected versus local/mean | +0.0009 | [-0.0009,+0.0028] |
| cbramod/pretrained_full/selected versus local/selected | +0.0281 | [-0.0052,+0.0613] |
| cbramod/random_full/selected versus local/selected | -0.0199 | [-0.0492,+0.0093] |
| inner_selected_model versus local/selected | +0.0109 | [-0.0145,+0.0362] |
| reve/pretrained_full/selected versus local/selected | -0.0199 | [-0.0568,+0.0170] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0037 | [-0.0003,+0.0076] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0031 | [+0.0004,+0.0058] |

## dtu / policy/attention_transfer/10s / unified/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0013 | [-0.0177,+0.0203] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0005 | [-0.0142,+0.0151] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0182 | [-0.1025,+0.0661] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0048 | [-0.0249,+0.0345] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0013 | [-0.0125,+0.0150] |
| local/antisymmetric versus local/mean | +0.0075 | [-0.0228,+0.0379] |
| local/selected versus local/mean | +0.0022 | [-0.0144,+0.0188] |
| cbramod/pretrained_full/selected versus local/selected | +0.0332 | [-0.1488,+0.2151] |
| cbramod/random_full/selected versus local/selected | +0.0209 | [-0.1467,+0.1885] |
| inner_selected_model versus local/selected | +0.0149 | [-0.1618,+0.1917] |
| reve/pretrained_full/selected versus local/selected | -0.0094 | [-0.1779,+0.1590] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0009 | [-0.0400,+0.0381] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0036 | [-0.0499,+0.0427] |

## dtu / policy/attention_transfer/20s / native/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0003 | [-0.0080,+0.0074] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0012 | [-0.0063,+0.0040] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0108 | [-0.0277,+0.0062] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0003 | [-0.0071,+0.0066] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0004 | [-0.0059,+0.0052] |
| local/antisymmetric versus local/mean | -0.0015 | [-0.0094,+0.0064] |
| local/selected versus local/mean | -0.0029 | [-0.0081,+0.0024] |
| cbramod/pretrained_full/selected versus local/selected | +0.0274 | [+0.0018,+0.0530] |
| cbramod/random_full/selected versus local/selected | +0.0088 | [-0.0176,+0.0352] |
| inner_selected_model versus local/selected | +0.0166 | [-0.0048,+0.0380] |
| reve/pretrained_full/selected versus local/selected | +0.0108 | [-0.0212,+0.0427] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0028 | [-0.0103,+0.0047] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0008 | [-0.0058,+0.0043] |

## dtu / policy/attention_transfer/20s / native/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0037 | [-7.2474,+7.2399] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0035 | [-6.3054,+6.2985] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0036 | [-11.9737,+11.9809] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0018 | [-6.6183,+6.6218] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0002 | [-3.5128,+3.5132] |
| local/antisymmetric versus local/mean | -0.0033 | [-8.1851,+8.1786] |
| local/selected versus local/mean | -0.0029 | [-2.9441,+2.9382] |
| cbramod/pretrained_full/selected versus local/selected | -0.0060 | [-30.1380,+30.1261] |
| cbramod/random_full/selected versus local/selected | -0.0023 | [-27.6941,+27.6894] |
| inner_selected_model versus local/selected | -0.0023 | [-27.6941,+27.6894] |
| reve/pretrained_full/selected versus local/selected | +0.0014 | [-22.2092,+22.2120] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0048 | [-5.4238,+5.4334] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0048 | [-5.4238,+5.4334] |

## dtu / policy/attention_transfer/20s / native/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0017 | [-0.0114,+0.0080] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0020 | [-0.0082,+0.0041] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0298 | [-0.0723,+0.0127] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0069 | [-0.0078,+0.0216] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0003 | [-0.0082,+0.0088] |
| local/antisymmetric versus local/mean | +0.0045 | [-0.0131,+0.0222] |
| local/selected versus local/mean | +0.0018 | [-0.0074,+0.0109] |
| cbramod/pretrained_full/selected versus local/selected | +0.0708 | [+0.0089,+0.1328] |
| cbramod/random_full/selected versus local/selected | +0.0217 | [-0.0421,+0.0855] |
| inner_selected_model versus local/selected | +0.0410 | [-0.0142,+0.0962] |
| reve/pretrained_full/selected versus local/selected | +0.0345 | [-0.0293,+0.0983] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0015 | [-0.0107,+0.0138] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0022 | [-0.0054,+0.0098] |

## dtu / policy/attention_transfer/20s / native/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0008 | [-0.0540,+0.0555] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0016 | [-0.0165,+0.0134] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0054 | [-0.1193,+0.1085] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0100 | [-0.0509,+0.0709] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0010 | [-0.0179,+0.0159] |
| local/antisymmetric versus local/mean | +0.0215 | [-0.0812,+0.1242] |
| local/selected versus local/mean | -0.0013 | [-0.0166,+0.0140] |
| cbramod/pretrained_full/selected versus local/selected | +0.0495 | [-0.1749,+0.2740] |
| cbramod/random_full/selected versus local/selected | +0.0441 | [-0.1695,+0.2577] |
| inner_selected_model versus local/selected | +0.0441 | [-0.1695,+0.2577] |
| reve/pretrained_full/selected versus local/selected | +0.0384 | [-0.2107,+0.2875] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0185 | [-0.0763,+0.1134] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0185 | [-0.0763,+0.1134] |

## dtu / policy/attention_transfer/20s / unified/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0021 | [-0.0098,+0.0057] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0016 | [-0.0068,+0.0036] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0051 | [-0.0167,+0.0064] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0028 | [-0.0093,+0.0038] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0024 | [-0.0081,+0.0034] |
| local/antisymmetric versus local/mean | -0.0044 | [-0.0116,+0.0028] |
| local/selected versus local/mean | -0.0007 | [-0.0039,+0.0026] |
| cbramod/pretrained_full/selected versus local/selected | +0.0224 | [-0.0012,+0.0460] |
| cbramod/random_full/selected versus local/selected | -0.0070 | [-0.0327,+0.0186] |
| inner_selected_model versus local/selected | +0.0173 | [-0.0002,+0.0347] |
| reve/pretrained_full/selected versus local/selected | -0.0027 | [-0.0336,+0.0282] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0009 | [-0.0081,+0.0063] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0016 | [-0.0074,+0.0041] |

## dtu / policy/attention_transfer/20s / unified/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0076 | [-5.3518,+5.3671] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0001 | [-3.6101,+3.6099] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0184 | [-19.2644,+19.2275] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0017 | [-2.5004,+2.4971] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0012 | [-2.1338,+2.1362] |
| local/selected versus local/mean | +0.0029 | [-2.8566,+2.8623] |
| cbramod/pretrained_full/selected versus local/selected | +0.0040 | [-21.0866,+21.0946] |
| cbramod/random_full/selected versus local/selected | +0.0088 | [-26.0224,+26.0400] |
| inner_selected_model versus local/selected | -0.0144 | [-20.1479,+20.1191] |
| reve/pretrained_full/selected versus local/selected | -0.0251 | [-21.3705,+21.3204] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0077 | [-7.1927,+7.1774] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0028 | [-5.5774,+5.5717] |

## dtu / policy/attention_transfer/20s / unified/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0051 | [-0.0174,+0.0072] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0003 | [-0.0099,+0.0094] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0164 | [-0.0405,+0.0078] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0047 | [-0.0069,+0.0163] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0002 | [-0.0070,+0.0066] |
| local/antisymmetric versus local/mean | -0.0023 | [-0.0085,+0.0040] |
| local/selected versus local/mean | -0.0008 | [-0.0051,+0.0035] |
| cbramod/pretrained_full/selected versus local/selected | +0.0429 | [-0.0091,+0.0950] |
| cbramod/random_full/selected versus local/selected | -0.0199 | [-0.0652,+0.0253] |
| inner_selected_model versus local/selected | +0.0266 | [-0.0130,+0.0661] |
| reve/pretrained_full/selected versus local/selected | -0.0111 | [-0.0773,+0.0550] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0082 | [-0.0191,+0.0027] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0053 | [-0.0151,+0.0045] |

## dtu / policy/attention_transfer/20s / unified/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0071 | [-0.0368,+0.0227] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0064 | [-0.0269,+0.0142] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0485 | [-0.2816,+0.1845] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0055 | [-0.0687,+0.0797] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0017 | [-0.0221,+0.0256] |
| local/selected versus local/mean | +0.0012 | [-0.0121,+0.0146] |
| cbramod/pretrained_full/selected versus local/selected | +0.0347 | [-0.1918,+0.2613] |
| cbramod/random_full/selected versus local/selected | +0.0423 | [-0.1388,+0.2234] |
| inner_selected_model versus local/selected | -0.0138 | [-0.1510,+0.1234] |
| reve/pretrained_full/selected versus local/selected | -0.0167 | [-0.2026,+0.1692] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0075 | [-0.0535,+0.0685] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0001 | [-0.0090,+0.0088] |

## dtu / policy/attention_transfer/5s / native/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0103 | [-0.0176,-0.0030] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0131 | [+0.0005,+0.0256] |
| cbramod/random_full/selected versus local/selected | -0.0053 | [-0.0191,+0.0085] |
| inner_selected_model versus local/selected | +0.0028 | [-0.0082,+0.0138] |
| reve/pretrained_full/selected versus local/selected | -0.0016 | [-0.0172,+0.0140] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / native/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0016 | [-0.0183,+0.0152] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0083 | [-0.0261,+0.0427] |
| cbramod/random_full/selected versus local/selected | +0.0067 | [-0.0404,+0.0539] |
| inner_selected_model versus local/selected | +0.0067 | [-0.0404,+0.0539] |
| reve/pretrained_full/selected versus local/selected | -0.0065 | [-0.0501,+0.0372] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / native/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0028 | [-0.0079,+0.0024] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0028 | [-0.0078,+0.0021] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0226 | [-0.0377,-0.0075] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0003 | [-0.0028,+0.0023] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0004 | [-0.0030,+0.0021] |
| local/antisymmetric versus local/mean | -0.0000 | [-0.0034,+0.0034] |
| local/selected versus local/mean | +0.0002 | [-0.0013,+0.0017] |
| cbramod/pretrained_full/selected versus local/selected | +0.0327 | [+0.0023,+0.0631] |
| cbramod/random_full/selected versus local/selected | +0.0038 | [-0.0270,+0.0345] |
| inner_selected_model versus local/selected | +0.0101 | [-0.0136,+0.0337] |
| reve/pretrained_full/selected versus local/selected | +0.0058 | [-0.0274,+0.0391] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0040 | [-0.0084,+0.0003] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0019 | [-0.0048,+0.0010] |

## dtu / policy/attention_transfer/5s / native/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0019 | [-0.0203,+0.0165] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0019 | [-0.0203,+0.0165] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0118 | [-0.0597,+0.0361] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0006 | [-0.0071,+0.0058] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0005 | [-0.0039,+0.0029] |
| local/antisymmetric versus local/mean | +0.0007 | [-0.0138,+0.0151] |
| local/selected versus local/mean | -0.0005 | [-0.0078,+0.0068] |
| cbramod/pretrained_full/selected versus local/selected | +0.0253 | [-0.0525,+0.1031] |
| cbramod/random_full/selected versus local/selected | +0.0135 | [-0.0774,+0.1044] |
| inner_selected_model versus local/selected | +0.0135 | [-0.0774,+0.1044] |
| reve/pretrained_full/selected versus local/selected | -0.0027 | [-0.0844,+0.0790] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0013 | [-0.0081,+0.0056] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/accuracy / 3401

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0028 | [-0.0095,+0.0040] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0098 | [-0.0031,+0.0228] |
| cbramod/random_full/selected versus local/selected | -0.0083 | [-0.0217,+0.0052] |
| inner_selected_model versus local/selected | +0.0071 | [-0.0030,+0.0171] |
| reve/pretrained_full/selected versus local/selected | -0.0058 | [-0.0195,+0.0080] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/accuracy / 3407

Complete paired identities10/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0051 | [-0.0265,+0.0164] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0290 | [+0.0079,+0.0502] |
| cbramod/random_full/selected versus local/selected | +0.0137 | [-0.0218,+0.0493] |
| inner_selected_model versus local/selected | +0.0239 | [-0.0022,+0.0501] |
| reve/pretrained_full/selected versus local/selected | +0.0096 | [-0.0408,+0.0600] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/nll_bits / 3401

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0022 | [-0.0008,+0.0051] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0014 | [-0.0008,+0.0036] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0051 | [-0.0138,+0.0037] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0001 | [-0.0020,+0.0018] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0001 | [-0.0019,+0.0016] |
| local/antisymmetric versus local/mean | +0.0017 | [-0.0024,+0.0057] |
| local/selected versus local/mean | +0.0022 | [-0.0007,+0.0051] |
| cbramod/pretrained_full/selected versus local/selected | +0.0165 | [-0.0045,+0.0376] |
| cbramod/random_full/selected versus local/selected | -0.0125 | [-0.0320,+0.0070] |
| inner_selected_model versus local/selected | +0.0115 | [-0.0076,+0.0306] |
| reve/pretrained_full/selected versus local/selected | -0.0133 | [-0.0359,+0.0092] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0037 | [+0.0001,+0.0073] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0033 | [+0.0003,+0.0063] |

## dtu / policy/attention_transfer/5s / unified/nll_bits / 3407

Complete paired identities10/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0033 | [-0.0145,+0.0212] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0033 | [-0.0145,+0.0212] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0139 | [-0.0484,+0.0205] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0002 | [-0.0097,+0.0093] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0003 | [-0.0086,+0.0080] |
| local/antisymmetric versus local/mean | -0.0008 | [-0.0143,+0.0127] |
| local/selected versus local/mean | -0.0008 | [-0.0143,+0.0127] |
| cbramod/pretrained_full/selected versus local/selected | +0.0203 | [-0.0366,+0.0773] |
| cbramod/random_full/selected versus local/selected | +0.0054 | [-0.0512,+0.0619] |
| inner_selected_model versus local/selected | +0.0064 | [-0.0494,+0.0622] |
| reve/pretrained_full/selected versus local/selected | -0.0072 | [-0.0698,+0.0554] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0019 | [-0.0193,+0.0156] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0013 | [-0.0127,+0.0101] |

