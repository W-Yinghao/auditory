# Frozen retrieval-source transfer to attention

2026-10-18T16:10:16.706621+02:00, CPU job1045980; **interim**, 27/160 units.

New aligned/true-full encoders were trained for single-speaker retrieval. Integrators and source-model policy are selected using inner listeners; outer attention is not used for selection. Paired candidate orders share one physical window.5/10/20s are evidence durations. All fixed alternatives and direct group interactions are retained in the JSON.

## dtu / policy/attention_transfer/10s / native/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0024 | [-0.0086,+0.0038] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0018 | [-0.0074,+0.0037] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0176 | [-0.0382,+0.0029] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0011 | [-0.0071,+0.0050] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0008 | [-0.0044,+0.0059] |
| local/antisymmetric versus local/mean | +0.0012 | [-0.0052,+0.0075] |
| local/selected versus local/mean | +0.0004 | [-0.0027,+0.0035] |
| cbramod/pretrained_full/selected versus local/selected | +0.0133 | [-0.0160,+0.0425] |
| cbramod/random_full/selected versus local/selected | +0.0061 | [-0.0212,+0.0334] |
| inner_selected_model versus local/selected | -0.0044 | [-0.0320,+0.0233] |
| reve/pretrained_full/selected versus local/selected | -0.0022 | [-0.0305,+0.0261] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0004 | [-0.0052,+0.0061] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0001 | [-0.0051,+0.0048] |

## dtu / policy/attention_transfer/10s / native/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0061 | [-0.0077,+0.0200] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0029 | [-0.0077,+0.0136] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0329 | [-0.0713,+0.0055] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0048 | [-0.0113,+0.0017] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0034 | [-0.0088,+0.0020] |
| local/antisymmetric versus local/mean | +0.0006 | [-0.0089,+0.0101] |
| local/selected versus local/mean | +0.0026 | [-0.0060,+0.0112] |
| cbramod/pretrained_full/selected versus local/selected | +0.0265 | [-0.0413,+0.0942] |
| cbramod/random_full/selected versus local/selected | +0.0152 | [-0.0414,+0.0719] |
| inner_selected_model versus local/selected | -0.0064 | [-0.0659,+0.0531] |
| reve/pretrained_full/selected versus local/selected | -0.0080 | [-0.0663,+0.0503] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0043 | [-0.0024,+0.0110] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0050 | [-0.0022,+0.0122] |

## dtu / policy/attention_transfer/10s / unified/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0012 | [-0.1391,+0.1415] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0004 | [-0.1058,+0.1066] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0067 | [-0.5485,+0.5351] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0001 | [-0.1215,+0.1213] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [-0.0385,+0.0386] |
| local/antisymmetric versus local/mean | -0.0010 | [-0.0970,+0.0950] |
| local/selected versus local/mean | -0.0003 | [-0.0737,+0.0731] |
| cbramod/pretrained_full/selected versus local/selected | +0.0196 | [-0.7241,+0.7633] |
| cbramod/random_full/selected versus local/selected | +0.0073 | [-0.7408,+0.7555] |
| inner_selected_model versus local/selected | +0.0129 | [-0.5829,+0.6087] |
| reve/pretrained_full/selected versus local/selected | -0.0031 | [-0.8001,+0.7938] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0006 | [-0.1685,+0.1697] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0005 | [-0.1155,+0.1145] |

## dtu / policy/attention_transfer/10s / unified/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0035 | [-0.0076,+0.0006] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0030 | [-0.0064,+0.0005] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0161 | [-0.0390,+0.0067] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0052 | [-0.0016,+0.0120] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0009 | [-0.0024,+0.0042] |
| local/antisymmetric versus local/mean | +0.0027 | [-0.0010,+0.0063] |
| local/selected versus local/mean | +0.0008 | [-0.0022,+0.0038] |
| cbramod/pretrained_full/selected versus local/selected | +0.0204 | [-0.0318,+0.0725] |
| cbramod/random_full/selected versus local/selected | -0.0169 | [-0.0596,+0.0259] |
| inner_selected_model versus local/selected | +0.0043 | [-0.0329,+0.0414] |
| reve/pretrained_full/selected versus local/selected | -0.0268 | [-0.0825,+0.0289] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0028 | [-0.0025,+0.0081] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0029 | [-0.0001,+0.0058] |

## dtu / policy/attention_transfer/20s / native/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0003 | [-0.0099,+0.0105] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0011 | [-0.0046,+0.0025] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0130 | [-0.0376,+0.0116] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0003 | [-0.0101,+0.0095] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0010 | [-0.0093,+0.0073] |
| local/antisymmetric versus local/mean | +0.0016 | [-0.0082,+0.0114] |
| local/selected versus local/mean | -0.0022 | [-0.0075,+0.0030] |
| cbramod/pretrained_full/selected versus local/selected | +0.0186 | [-0.0151,+0.0524] |
| cbramod/random_full/selected versus local/selected | +0.0134 | [-0.0210,+0.0479] |
| inner_selected_model versus local/selected | +0.0057 | [-0.0154,+0.0267] |
| reve/pretrained_full/selected versus local/selected | +0.0113 | [-0.0323,+0.0550] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0054 | [-0.0166,+0.0058] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0005 | [-0.0079,+0.0069] |

## dtu / policy/attention_transfer/20s / native/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0005 | [-0.0186,+0.0175] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0011 | [-0.0116,+0.0094] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0433 | [-0.1212,+0.0345] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0068 | [-0.0190,+0.0326] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0009 | [-0.0156,+0.0139] |
| local/antisymmetric versus local/mean | +0.0025 | [-0.0289,+0.0340] |
| local/selected versus local/mean | -0.0019 | [-0.0121,+0.0082] |
| cbramod/pretrained_full/selected versus local/selected | +0.0507 | [-0.0474,+0.1488] |
| cbramod/random_full/selected versus local/selected | +0.0374 | [-0.0492,+0.1241] |
| inner_selected_model versus local/selected | +0.0074 | [-0.0570,+0.0718] |
| reve/pretrained_full/selected versus local/selected | +0.0171 | [-0.0718,+0.1060] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0024 | [-0.0200,+0.0249] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0025 | [-0.0101,+0.0152] |

## dtu / policy/attention_transfer/20s / unified/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0029 | [-0.0137,+0.0078] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0022 | [-0.0064,+0.0021] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0055 | [-0.0228,+0.0118] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0043 | [-0.0142,+0.0056] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0032 | [-0.0121,+0.0058] |
| local/antisymmetric versus local/mean | -0.0079 | [-0.0184,+0.0027] |
| local/selected versus local/mean | -0.0016 | [-0.0068,+0.0036] |
| cbramod/pretrained_full/selected versus local/selected | +0.0209 | [-0.0097,+0.0515] |
| cbramod/random_full/selected versus local/selected | -0.0000 | [-0.0291,+0.0291] |
| inner_selected_model versus local/selected | +0.0154 | [-0.0052,+0.0359] |
| reve/pretrained_full/selected versus local/selected | -0.0143 | [-0.0596,+0.0309] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0027 | [-0.0121,+0.0067] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0031 | [-0.0116,+0.0053] |

## dtu / policy/attention_transfer/20s / unified/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0096 | [-0.0229,+0.0037] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0020 | [-0.0089,+0.0049] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0178 | [-0.0505,+0.0149] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0001 | [-0.0130,+0.0131] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0028 | [-0.0107,+0.0051] |
| local/antisymmetric versus local/mean | -0.0038 | [-0.0119,+0.0042] |
| local/selected versus local/mean | -0.0021 | [-0.0086,+0.0045] |
| cbramod/pretrained_full/selected versus local/selected | +0.0359 | [-0.0386,+0.1104] |
| cbramod/random_full/selected versus local/selected | -0.0032 | [-0.0598,+0.0535] |
| inner_selected_model versus local/selected | +0.0181 | [-0.0361,+0.0723] |
| reve/pretrained_full/selected versus local/selected | -0.0269 | [-0.1197,+0.0658] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0130 | [-0.0279,+0.0019] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0090 | [-0.0230,+0.0049] |

## dtu / policy/attention_transfer/5s / native/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0033 | [-0.0118,+0.0052] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0044 | [-0.0112,+0.0200] |
| cbramod/random_full/selected versus local/selected | -0.0044 | [-0.0225,+0.0138] |
| inner_selected_model versus local/selected | +0.0011 | [-0.0132,+0.0154] |
| reve/pretrained_full/selected versus local/selected | -0.0073 | [-0.0258,+0.0111] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / native/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0038 | [-0.0126,+0.0051] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0038 | [-0.0126,+0.0051] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0133 | [-0.0336,+0.0071] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0010 | [-0.0046,+0.0025] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0005 | [-0.0039,+0.0028] |
| local/antisymmetric versus local/mean | -0.0012 | [-0.0065,+0.0041] |
| local/selected versus local/mean | -0.0004 | [-0.0021,+0.0013] |
| cbramod/pretrained_full/selected versus local/selected | +0.0207 | [-0.0220,+0.0634] |
| cbramod/random_full/selected versus local/selected | +0.0069 | [-0.0363,+0.0501] |
| inner_selected_model versus local/selected | +0.0074 | [-0.0284,+0.0432] |
| reve/pretrained_full/selected versus local/selected | -0.0021 | [-0.0461,+0.0419] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0048 | [-0.0123,+0.0026] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0028 | [-0.0080,+0.0023] |

## dtu / policy/attention_transfer/5s / unified/accuracy / 3401

Complete paired identities28/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0017 | [-0.0100,+0.0065] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0088 | [-0.0080,+0.0256] |
| cbramod/random_full/selected versus local/selected | -0.0051 | [-0.0221,+0.0119] |
| inner_selected_model versus local/selected | +0.0071 | [-0.0056,+0.0197] |
| reve/pretrained_full/selected versus local/selected | -0.0111 | [-0.0284,+0.0063] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/nll_bits / 3401

Complete paired identities28/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0017 | [-0.0045,+0.0079] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0005 | [-0.0017,+0.0027] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0049 | [-0.0279,+0.0180] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0003 | [-0.0055,+0.0050] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0003 | [-0.0051,+0.0045] |
| local/antisymmetric versus local/mean | +0.0041 | [-0.0053,+0.0134] |
| local/selected versus local/mean | +0.0037 | [-0.0031,+0.0105] |
| cbramod/pretrained_full/selected versus local/selected | +0.0118 | [-0.0396,+0.0631] |
| cbramod/random_full/selected versus local/selected | -0.0077 | [-0.0531,+0.0378] |
| inner_selected_model versus local/selected | +0.0068 | [-0.0373,+0.0509] |
| reve/pretrained_full/selected versus local/selected | -0.0153 | [-0.0721,+0.0415] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0053 | [-0.0023,+0.0129] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0053 | [-0.0023,+0.0129] |

