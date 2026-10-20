# Frozen retrieval-source transfer to attention

2026-10-19T17:34:35.110880+02:00, CPU job1047358; **complete**, 160/160 units.

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0011 | [-0.0051,+0.0030] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0011 | [-0.0049,+0.0027] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0054 | [-0.0156,+0.0048] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0005 | [-0.0041,+0.0030] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0016 | [-0.0047,+0.0016] |
| local/antisymmetric versus local/mean | -0.0024 | [-0.0066,+0.0018] |
| local/selected versus local/mean | -0.0014 | [-0.0038,+0.0011] |
| cbramod/pretrained_full/selected versus local/selected | +0.0295 | [+0.0093,+0.0498] |
| cbramod/random_full/selected versus local/selected | +0.0143 | [-0.0063,+0.0348] |
| inner_selected_model versus local/selected | +0.0241 | [+0.0043,+0.0440] |
| reve/pretrained_full/selected versus local/selected | +0.0176 | [-0.0053,+0.0405] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0014 | [-0.0042,+0.0070] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0020 | [-0.0026,+0.0065] |

## dtu / policy/attention_transfer/10s / native/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0026 | [-0.0080,+0.0028] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0020 | [-0.0069,+0.0029] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0066 | [-0.0221,+0.0090] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0019 | [-0.0059,+0.0020] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0005 | [-0.0025,+0.0016] |
| local/antisymmetric versus local/mean | -0.0009 | [-0.0050,+0.0032] |
| local/selected versus local/mean | +0.0002 | [-0.0023,+0.0028] |
| cbramod/pretrained_full/selected versus local/selected | +0.0253 | [+0.0042,+0.0465] |
| cbramod/random_full/selected versus local/selected | +0.0076 | [-0.0170,+0.0322] |
| inner_selected_model versus local/selected | +0.0188 | [-0.0039,+0.0414] |
| reve/pretrained_full/selected versus local/selected | +0.0109 | [-0.0102,+0.0320] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0001 | [-0.0043,+0.0045] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0005 | [-0.0038,+0.0027] |

## dtu / policy/attention_transfer/10s / native/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0019 | [-0.0047,+0.0008] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0017 | [-0.0040,+0.0006] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0094 | [-0.0157,-0.0031] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0013 | [-0.0036,+0.0010] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0006 | [-0.0024,+0.0011] |
| local/antisymmetric versus local/mean | -0.0010 | [-0.0037,+0.0016] |
| local/selected versus local/mean | -0.0005 | [-0.0022,+0.0013] |
| cbramod/pretrained_full/selected versus local/selected | +0.0259 | [+0.0095,+0.0423] |
| cbramod/random_full/selected versus local/selected | +0.0096 | [-0.0083,+0.0275] |
| inner_selected_model versus local/selected | +0.0165 | [+0.0004,+0.0325] |
| reve/pretrained_full/selected versus local/selected | +0.0112 | [-0.0057,+0.0282] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0004 | [-0.0023,+0.0030] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0002 | [-0.0018,+0.0023] |

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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0021 | [-0.0039,+0.0082] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0003 | [-0.0040,+0.0045] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0103 | [-0.0293,+0.0088] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0065 | [-0.0131,-0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0053 | [-0.0100,-0.0007] |
| local/antisymmetric versus local/mean | -0.0032 | [-0.0086,+0.0022] |
| local/selected versus local/mean | +0.0003 | [-0.0028,+0.0035] |
| cbramod/pretrained_full/selected versus local/selected | +0.0605 | [+0.0263,+0.0947] |
| cbramod/random_full/selected versus local/selected | +0.0322 | [-0.0019,+0.0662] |
| inner_selected_model versus local/selected | +0.0502 | [+0.0191,+0.0813] |
| reve/pretrained_full/selected versus local/selected | +0.0337 | [-0.0040,+0.0713] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0018 | [-0.0062,+0.0099] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0034 | [-0.0033,+0.0101] |

## dtu / policy/attention_transfer/10s / native/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0038 | [-0.0043,+0.0119] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0019 | [-0.0032,+0.0069] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0199 | [-0.0463,+0.0065] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0012 | [-0.0089,+0.0065] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0016 | [-0.0038,+0.0070] |
| local/antisymmetric versus local/mean | -0.0040 | [-0.0093,+0.0012] |
| local/selected versus local/mean | -0.0038 | [-0.0083,+0.0007] |
| cbramod/pretrained_full/selected versus local/selected | +0.0526 | [+0.0137,+0.0916] |
| cbramod/random_full/selected versus local/selected | +0.0172 | [-0.0246,+0.0590] |
| inner_selected_model versus local/selected | +0.0328 | [-0.0102,+0.0758] |
| reve/pretrained_full/selected versus local/selected | +0.0201 | [-0.0215,+0.0617] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0044 | [-0.0044,+0.0133] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0029 | [-0.0032,+0.0089] |

## dtu / policy/attention_transfer/10s / native/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0039 | [-0.0022,+0.0101] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0020 | [-0.0020,+0.0059] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0226 | [-0.0374,-0.0079] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0040 | [-0.0082,+0.0002] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0025 | [-0.0046,-0.0004] |
| local/antisymmetric versus local/mean | -0.0027 | [-0.0056,+0.0001] |
| local/selected versus local/mean | -0.0010 | [-0.0029,+0.0008] |
| cbramod/pretrained_full/selected versus local/selected | +0.0527 | [+0.0196,+0.0857] |
| cbramod/random_full/selected versus local/selected | +0.0196 | [-0.0122,+0.0513] |
| inner_selected_model versus local/selected | +0.0300 | [+0.0005,+0.0595] |
| reve/pretrained_full/selected versus local/selected | +0.0197 | [-0.0145,+0.0539] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0030 | [-0.0024,+0.0084] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0029 | [-0.0017,+0.0076] |

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0005 | [-0.0031,+0.0020] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0007 | [-0.0026,+0.0012] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0077 | [-0.0175,+0.0020] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0017 | [-0.0024,+0.0057] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0016 | [-0.0019,+0.0051] |
| local/antisymmetric versus local/mean | -0.0014 | [-0.0049,+0.0021] |
| local/selected versus local/mean | -0.0008 | [-0.0038,+0.0022] |
| cbramod/pretrained_full/selected versus local/selected | +0.0289 | [+0.0103,+0.0474] |
| cbramod/random_full/selected versus local/selected | +0.0066 | [-0.0128,+0.0261] |
| inner_selected_model versus local/selected | +0.0211 | [+0.0021,+0.0402] |
| reve/pretrained_full/selected versus local/selected | +0.0097 | [-0.0120,+0.0314] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0008 | [-0.0021,+0.0036] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0004 | [-0.0015,+0.0022] |

## dtu / policy/attention_transfer/10s / unified/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0002 | [-0.0032,+0.0036] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0005 | [-0.0033,+0.0023] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0110 | [-0.0209,-0.0011] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0007 | [-0.0041,+0.0027] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0011 | [-0.0033,+0.0012] |
| local/antisymmetric versus local/mean | -0.0008 | [-0.0037,+0.0020] |
| local/selected versus local/mean | -0.0003 | [-0.0028,+0.0021] |
| cbramod/pretrained_full/selected versus local/selected | +0.0314 | [+0.0141,+0.0486] |
| cbramod/random_full/selected versus local/selected | +0.0019 | [-0.0173,+0.0210] |
| inner_selected_model versus local/selected | +0.0204 | [+0.0050,+0.0358] |
| reve/pretrained_full/selected versus local/selected | +0.0016 | [-0.0156,+0.0189] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0018 | [-0.0063,+0.0027] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0005 | [-0.0028,+0.0018] |

## dtu / policy/attention_transfer/10s / unified/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0002 | [-0.0017,+0.0021] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0003 | [-0.0016,+0.0010] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0085 | [-0.0149,-0.0021] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0004 | [-0.0020,+0.0028] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0001 | [-0.0015,+0.0018] |
| local/antisymmetric versus local/mean | -0.0008 | [-0.0024,+0.0008] |
| local/selected versus local/mean | -0.0004 | [-0.0018,+0.0011] |
| cbramod/pretrained_full/selected versus local/selected | +0.0275 | [+0.0126,+0.0425] |
| cbramod/random_full/selected versus local/selected | +0.0027 | [-0.0113,+0.0167] |
| inner_selected_model versus local/selected | +0.0190 | [+0.0059,+0.0322] |
| reve/pretrained_full/selected versus local/selected | +0.0037 | [-0.0115,+0.0189] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0001 | [-0.0018,+0.0017] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0000 | [-0.0012,+0.0011] |

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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0024 | [-0.0064,+0.0016] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0017 | [-0.0052,+0.0018] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0162 | [-0.0322,-0.0003] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0051 | [-0.0005,+0.0107] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0027 | [-0.0011,+0.0064] |
| local/antisymmetric versus local/mean | +0.0039 | [-0.0008,+0.0086] |
| local/selected versus local/mean | +0.0030 | [-0.0010,+0.0070] |
| cbramod/pretrained_full/selected versus local/selected | +0.0518 | [+0.0213,+0.0823] |
| cbramod/random_full/selected versus local/selected | +0.0060 | [-0.0282,+0.0403] |
| inner_selected_model versus local/selected | +0.0355 | [+0.0046,+0.0665] |
| reve/pretrained_full/selected versus local/selected | +0.0053 | [-0.0325,+0.0432] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0039 | [-0.0017,+0.0095] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0005 | [-0.0045,+0.0055] |

## dtu / policy/attention_transfer/10s / unified/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0017 | [-0.0049,+0.0014] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0012 | [-0.0037,+0.0012] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0187 | [-0.0385,+0.0012] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0001 | [-0.0043,+0.0046] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0003 | [-0.0024,+0.0029] |
| local/antisymmetric versus local/mean | +0.0040 | [+0.0004,+0.0076] |
| local/selected versus local/mean | +0.0039 | [-0.0001,+0.0079] |
| cbramod/pretrained_full/selected versus local/selected | +0.0439 | [+0.0093,+0.0785] |
| cbramod/random_full/selected versus local/selected | -0.0129 | [-0.0514,+0.0257] |
| inner_selected_model versus local/selected | +0.0253 | [-0.0034,+0.0540] |
| reve/pretrained_full/selected versus local/selected | -0.0059 | [-0.0439,+0.0321] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0028 | [-0.0022,+0.0077] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0024 | [-0.0013,+0.0062] |

## dtu / policy/attention_transfer/10s / unified/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0022 | [-0.0053,+0.0008] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0016 | [-0.0040,+0.0008] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0174 | [-0.0288,-0.0060] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0025 | [-0.0007,+0.0056] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0011 | [-0.0007,+0.0029] |
| local/antisymmetric versus local/mean | +0.0034 | [+0.0004,+0.0064] |
| local/selected versus local/mean | +0.0026 | [+0.0003,+0.0049] |
| cbramod/pretrained_full/selected versus local/selected | +0.0413 | [+0.0128,+0.0697] |
| cbramod/random_full/selected versus local/selected | -0.0089 | [-0.0373,+0.0194] |
| inner_selected_model versus local/selected | +0.0239 | [+0.0008,+0.0470] |
| reve/pretrained_full/selected versus local/selected | -0.0068 | [-0.0381,+0.0244] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0034 | [+0.0000,+0.0069] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0020 | [-0.0006,+0.0046] |

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0024 | [-0.0086,+0.0038] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0020 | [-0.0064,+0.0024] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0001 | [-0.0145,+0.0146] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0002 | [-0.0085,+0.0088] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0016 | [-0.0055,+0.0088] |
| local/antisymmetric versus local/mean | -0.0040 | [-0.0099,+0.0019] |
| local/selected versus local/mean | -0.0014 | [-0.0054,+0.0025] |
| cbramod/pretrained_full/selected versus local/selected | +0.0277 | [+0.0016,+0.0539] |
| cbramod/random_full/selected versus local/selected | +0.0121 | [-0.0143,+0.0386] |
| inner_selected_model versus local/selected | +0.0278 | [+0.0042,+0.0515] |
| reve/pretrained_full/selected versus local/selected | +0.0215 | [-0.0016,+0.0446] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0009 | [-0.0065,+0.0047] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0013 | [-0.0033,+0.0059] |

## dtu / policy/attention_transfer/20s / native/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0005 | [-0.0072,+0.0062] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0007 | [-0.0052,+0.0039] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0109 | [-0.0276,+0.0058] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [-0.0083,+0.0083] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0007 | [-0.0033,+0.0047] |
| local/antisymmetric versus local/mean | +0.0003 | [-0.0050,+0.0057] |
| local/selected versus local/mean | -0.0007 | [-0.0042,+0.0027] |
| cbramod/pretrained_full/selected versus local/selected | +0.0219 | [-0.0012,+0.0449] |
| cbramod/random_full/selected versus local/selected | +0.0106 | [-0.0183,+0.0395] |
| inner_selected_model versus local/selected | +0.0110 | [-0.0116,+0.0336] |
| reve/pretrained_full/selected versus local/selected | +0.0237 | [-0.0026,+0.0500] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0031 | [-0.0114,+0.0051] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0011 | [-0.0025,+0.0048] |

## dtu / policy/attention_transfer/20s / native/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0010 | [-0.0059,+0.0038] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0013 | [-0.0043,+0.0017] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0072 | [-0.0180,+0.0037] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0000 | [-0.0052,+0.0051] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0007 | [-0.0029,+0.0043] |
| local/antisymmetric versus local/mean | -0.0017 | [-0.0061,+0.0027] |
| local/selected versus local/mean | -0.0017 | [-0.0039,+0.0005] |
| cbramod/pretrained_full/selected versus local/selected | +0.0257 | [+0.0057,+0.0456] |
| cbramod/random_full/selected versus local/selected | +0.0105 | [-0.0122,+0.0332] |
| inner_selected_model versus local/selected | +0.0185 | [+0.0018,+0.0352] |
| reve/pretrained_full/selected versus local/selected | +0.0186 | [-0.0013,+0.0386] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0023 | [-0.0069,+0.0023] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0006 | [-0.0021,+0.0032] |

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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0004 | [-0.0097,+0.0104] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0001 | [-0.0033,+0.0032] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0101 | [-0.0361,+0.0158] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0033 | [-0.0101,+0.0167] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0011 | [-0.0087,+0.0108] |
| local/antisymmetric versus local/mean | +0.0036 | [-0.0144,+0.0217] |
| local/selected versus local/mean | -0.0004 | [-0.0069,+0.0061] |
| cbramod/pretrained_full/selected versus local/selected | +0.1012 | [+0.0393,+0.1630] |
| cbramod/random_full/selected versus local/selected | +0.0648 | [-0.0012,+0.1308] |
| inner_selected_model versus local/selected | +0.0911 | [+0.0317,+0.1504] |
| reve/pretrained_full/selected versus local/selected | +0.0659 | [+0.0011,+0.1308] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0080 | [-0.0080,+0.0240] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0049 | [-0.0103,+0.0201] |

## dtu / policy/attention_transfer/20s / native/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0023 | [-0.0141,+0.0096] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0011 | [-0.0070,+0.0048] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0623 | [-0.1074,-0.0172] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0054 | [-0.0107,+0.0216] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0014 | [-0.0069,+0.0041] |
| local/antisymmetric versus local/mean | +0.0039 | [-0.0111,+0.0189] |
| local/selected versus local/mean | +0.0004 | [-0.0094,+0.0102] |
| cbramod/pretrained_full/selected versus local/selected | +0.0809 | [+0.0290,+0.1327] |
| cbramod/random_full/selected versus local/selected | +0.0255 | [-0.0395,+0.0905] |
| inner_selected_model versus local/selected | +0.0186 | [-0.0305,+0.0676] |
| reve/pretrained_full/selected versus local/selected | +0.0464 | [-0.0131,+0.1060] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0015 | [-0.0116,+0.0146] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0006 | [-0.0044,+0.0056] |

## dtu / policy/attention_transfer/20s / native/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0012 | [-0.0105,+0.0082] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0011 | [-0.0047,+0.0026] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0341 | [-0.0595,-0.0086] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0052 | [-0.0085,+0.0189] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0000 | [-0.0062,+0.0061] |
| local/antisymmetric versus local/mean | +0.0040 | [-0.0117,+0.0198] |
| local/selected versus local/mean | +0.0006 | [-0.0056,+0.0068] |
| cbramod/pretrained_full/selected versus local/selected | +0.0843 | [+0.0353,+0.1333] |
| cbramod/random_full/selected versus local/selected | +0.0373 | [-0.0183,+0.0929] |
| inner_selected_model versus local/selected | +0.0502 | [+0.0094,+0.0911] |
| reve/pretrained_full/selected versus local/selected | +0.0489 | [-0.0021,+0.1000] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0037 | [-0.0075,+0.0148] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0026 | [-0.0039,+0.0090] |

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0017 | [-0.0037,+0.0071] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0008 | [-0.0039,+0.0023] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0061 | [-0.0182,+0.0061] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0027 | [-0.0065,+0.0011] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0026 | [-0.0064,+0.0011] |
| local/antisymmetric versus local/mean | -0.0018 | [-0.0081,+0.0045] |
| local/selected versus local/mean | +0.0001 | [-0.0058,+0.0059] |
| cbramod/pretrained_full/selected versus local/selected | +0.0280 | [+0.0070,+0.0491] |
| cbramod/random_full/selected versus local/selected | +0.0143 | [-0.0083,+0.0369] |
| inner_selected_model versus local/selected | +0.0220 | [+0.0006,+0.0434] |
| reve/pretrained_full/selected versus local/selected | +0.0051 | [-0.0210,+0.0312] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0036 | [-0.0109,+0.0036] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0004 | [-0.0061,+0.0052] |

## dtu / policy/attention_transfer/20s / unified/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0031 | [-0.0043,+0.0106] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0019 | [-0.0039,+0.0077] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0091 | [-0.0215,+0.0034] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0073 | [-0.0150,+0.0004] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0021 | [-0.0069,+0.0027] |
| local/antisymmetric versus local/mean | -0.0006 | [-0.0061,+0.0048] |
| local/selected versus local/mean | +0.0002 | [-0.0049,+0.0052] |
| cbramod/pretrained_full/selected versus local/selected | +0.0226 | [+0.0050,+0.0402] |
| cbramod/random_full/selected versus local/selected | -0.0090 | [-0.0313,+0.0133] |
| inner_selected_model versus local/selected | +0.0135 | [-0.0026,+0.0296] |
| reve/pretrained_full/selected versus local/selected | +0.0074 | [-0.0152,+0.0300] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0009 | [-0.0076,+0.0094] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0009 | [-0.0047,+0.0066] |

## dtu / policy/attention_transfer/20s / unified/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0009 | [-0.0034,+0.0053] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0002 | [-0.0027,+0.0024] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0068 | [-0.0139,+0.0003] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0043 | [-0.0077,-0.0008] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0024 | [-0.0050,+0.0003] |
| local/antisymmetric versus local/mean | -0.0023 | [-0.0055,+0.0009] |
| local/selected versus local/mean | -0.0001 | [-0.0029,+0.0026] |
| cbramod/pretrained_full/selected versus local/selected | +0.0243 | [+0.0087,+0.0400] |
| cbramod/random_full/selected versus local/selected | -0.0006 | [-0.0174,+0.0162] |
| inner_selected_model versus local/selected | +0.0176 | [+0.0056,+0.0296] |
| reve/pretrained_full/selected versus local/selected | +0.0033 | [-0.0155,+0.0220] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0012 | [-0.0059,+0.0034] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0004 | [-0.0038,+0.0030] |

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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0013 | [-0.0090,+0.0064] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0022 | [-0.0054,+0.0010] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0176 | [-0.0495,+0.0143] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0012 | [-0.0123,+0.0100] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0041 | [-0.0101,+0.0018] |
| local/antisymmetric versus local/mean | -0.0017 | [-0.0102,+0.0067] |
| local/selected versus local/mean | -0.0023 | [-0.0097,+0.0052] |
| cbramod/pretrained_full/selected versus local/selected | +0.0706 | [+0.0236,+0.1177] |
| cbramod/random_full/selected versus local/selected | +0.0240 | [-0.0274,+0.0754] |
| inner_selected_model versus local/selected | +0.0530 | [+0.0090,+0.0970] |
| reve/pretrained_full/selected versus local/selected | +0.0281 | [-0.0292,+0.0855] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0034 | [-0.0065,+0.0133] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0030 | [-0.0019,+0.0080] |

## dtu / policy/attention_transfer/20s / unified/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0066 | [-0.0158,+0.0026] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0038 | [-0.0095,+0.0018] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0280 | [-0.0607,+0.0047] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0008 | [-0.0095,+0.0078] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [-0.0062,+0.0063] |
| local/antisymmetric versus local/mean | -0.0014 | [-0.0076,+0.0048] |
| local/selected versus local/mean | -0.0000 | [-0.0050,+0.0050] |
| cbramod/pretrained_full/selected versus local/selected | +0.0591 | [+0.0150,+0.1032] |
| cbramod/random_full/selected versus local/selected | -0.0142 | [-0.0635,+0.0350] |
| inner_selected_model versus local/selected | +0.0311 | [-0.0068,+0.0691] |
| reve/pretrained_full/selected versus local/selected | -0.0010 | [-0.0510,+0.0489] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0014 | [-0.0068,+0.0096] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0011 | [-0.0054,+0.0032] |

## dtu / policy/attention_transfer/20s / unified/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0043 | [-0.0110,+0.0024] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0021 | [-0.0067,+0.0025] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0207 | [-0.0386,-0.0027] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0009 | [-0.0075,+0.0093] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0014 | [-0.0062,+0.0033] |
| local/antisymmetric versus local/mean | -0.0018 | [-0.0074,+0.0037] |
| local/selected versus local/mean | -0.0010 | [-0.0057,+0.0037] |
| cbramod/pretrained_full/selected versus local/selected | +0.0576 | [+0.0203,+0.0948] |
| cbramod/random_full/selected versus local/selected | -0.0034 | [-0.0389,+0.0321] |
| inner_selected_model versus local/selected | +0.0369 | [+0.0097,+0.0641] |
| reve/pretrained_full/selected versus local/selected | +0.0053 | [-0.0369,+0.0475] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0011 | [-0.0070,+0.0048] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0011 | [-0.0051,+0.0028] |

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0024 | [-0.0065,+0.0113] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0229 | [+0.0111,+0.0346] |
| cbramod/random_full/selected versus local/selected | +0.0145 | [+0.0006,+0.0283] |
| inner_selected_model versus local/selected | +0.0253 | [+0.0117,+0.0389] |
| reve/pretrained_full/selected versus local/selected | +0.0132 | [-0.0011,+0.0276] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / native/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0069 | [-0.0165,+0.0026] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0244 | [+0.0124,+0.0364] |
| cbramod/random_full/selected versus local/selected | +0.0088 | [-0.0050,+0.0225] |
| inner_selected_model versus local/selected | +0.0175 | [+0.0032,+0.0318] |
| reve/pretrained_full/selected versus local/selected | +0.0072 | [-0.0058,+0.0201] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / native/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0049 | [-0.0108,+0.0009] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0201 | [+0.0102,+0.0300] |
| cbramod/random_full/selected versus local/selected | +0.0060 | [-0.0056,+0.0175] |
| inner_selected_model versus local/selected | +0.0152 | [+0.0049,+0.0254] |
| reve/pretrained_full/selected versus local/selected | +0.0063 | [-0.0050,+0.0175] |
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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0011 | [-0.0028,+0.0049] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0011 | [-0.0027,+0.0049] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0108 | [-0.0232,+0.0017] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0014 | [-0.0034,+0.0006] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0009 | [-0.0022,+0.0005] |
| local/antisymmetric versus local/mean | +0.0025 | [-0.0013,+0.0063] |
| local/selected versus local/mean | +0.0005 | [-0.0011,+0.0020] |
| cbramod/pretrained_full/selected versus local/selected | +0.0484 | [+0.0285,+0.0682] |
| cbramod/random_full/selected versus local/selected | +0.0247 | [+0.0035,+0.0458] |
| inner_selected_model versus local/selected | +0.0376 | [+0.0149,+0.0603] |
| reve/pretrained_full/selected versus local/selected | +0.0248 | [-0.0005,+0.0500] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0010 | [-0.0031,+0.0010] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0001 | [-0.0004,+0.0002] |

## dtu / policy/attention_transfer/5s / native/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0021 | [-0.0061,+0.0018] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0022 | [-0.0059,+0.0015] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0120 | [-0.0283,+0.0044] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0007 | [-0.0025,+0.0012] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0003 | [-0.0013,+0.0007] |
| local/antisymmetric versus local/mean | +0.0010 | [-0.0019,+0.0039] |
| local/selected versus local/mean | +0.0004 | [-0.0017,+0.0026] |
| cbramod/pretrained_full/selected versus local/selected | +0.0426 | [+0.0205,+0.0647] |
| cbramod/random_full/selected versus local/selected | +0.0128 | [-0.0112,+0.0368] |
| inner_selected_model versus local/selected | +0.0306 | [+0.0052,+0.0559] |
| reve/pretrained_full/selected versus local/selected | +0.0181 | [-0.0056,+0.0418] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0031 | [-0.0069,+0.0007] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0020 | [-0.0048,+0.0008] |

## dtu / policy/attention_transfer/5s / native/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0013 | [-0.0047,+0.0022] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0013 | [-0.0045,+0.0019] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0151 | [-0.0268,-0.0034] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0008 | [-0.0027,+0.0011] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0005 | [-0.0016,+0.0006] |
| local/antisymmetric versus local/mean | +0.0012 | [-0.0018,+0.0042] |
| local/selected versus local/mean | +0.0004 | [-0.0014,+0.0021] |
| cbramod/pretrained_full/selected versus local/selected | +0.0412 | [+0.0184,+0.0640] |
| cbramod/random_full/selected versus local/selected | +0.0137 | [-0.0103,+0.0378] |
| inner_selected_model versus local/selected | +0.0261 | [+0.0036,+0.0486] |
| reve/pretrained_full/selected versus local/selected | +0.0162 | [-0.0095,+0.0420] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0027 | [-0.0058,+0.0004] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0014 | [-0.0033,+0.0005] |

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

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0047 | [-0.0103,+0.0010] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0263 | [+0.0158,+0.0367] |
| cbramod/random_full/selected versus local/selected | +0.0063 | [-0.0059,+0.0186] |
| inner_selected_model versus local/selected | +0.0216 | [+0.0106,+0.0327] |
| reve/pretrained_full/selected versus local/selected | +0.0060 | [-0.0086,+0.0207] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/accuracy / 3413

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0096 | [-0.0159,-0.0032] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0217 | [+0.0102,+0.0333] |
| cbramod/random_full/selected versus local/selected | +0.0002 | [-0.0130,+0.0134] |
| inner_selected_model versus local/selected | +0.0122 | [+0.0022,+0.0221] |
| reve/pretrained_full/selected versus local/selected | -0.0009 | [-0.0140,+0.0121] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## dtu / policy/attention_transfer/5s / unified/accuracy / complete_seed_mean

Complete paired identities44/44; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0057 | [-0.0096,-0.0017] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | +0.0193 | [+0.0102,+0.0284] |
| cbramod/random_full/selected versus local/selected | -0.0006 | [-0.0108,+0.0097] |
| inner_selected_model versus local/selected | +0.0136 | [+0.0065,+0.0207] |
| reve/pretrained_full/selected versus local/selected | -0.0002 | [-0.0114,+0.0109] |
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

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0018 | [-0.0018,+0.0053] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0013 | [-0.0016,+0.0043] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0090 | [-0.0189,+0.0010] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0019 | [-0.0019,+0.0056] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0021 | [-0.0013,+0.0055] |
| local/antisymmetric versus local/mean | +0.0014 | [-0.0027,+0.0055] |
| local/selected versus local/mean | +0.0017 | [-0.0022,+0.0057] |
| cbramod/pretrained_full/selected versus local/selected | +0.0329 | [+0.0155,+0.0503] |
| cbramod/random_full/selected versus local/selected | +0.0044 | [-0.0150,+0.0239] |
| inner_selected_model versus local/selected | +0.0240 | [+0.0056,+0.0423] |
| reve/pretrained_full/selected versus local/selected | +0.0028 | [-0.0196,+0.0252] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0016 | [-0.0027,+0.0059] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0011 | [-0.0021,+0.0042] |

## dtu / policy/attention_transfer/5s / unified/nll_bits / 3413

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0018 | [-0.0015,+0.0051] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0012 | [-0.0007,+0.0030] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0143 | [-0.0246,-0.0039] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0016 | [-0.0022,+0.0055] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0016 | [-0.0018,+0.0050] |
| local/antisymmetric versus local/mean | +0.0020 | [-0.0012,+0.0051] |
| local/selected versus local/mean | +0.0022 | [-0.0009,+0.0053] |
| cbramod/pretrained_full/selected versus local/selected | +0.0282 | [+0.0096,+0.0468] |
| cbramod/random_full/selected versus local/selected | -0.0056 | [-0.0245,+0.0133] |
| inner_selected_model versus local/selected | +0.0139 | [-0.0022,+0.0300] |
| reve/pretrained_full/selected versus local/selected | -0.0054 | [-0.0262,+0.0154] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0046 | [+0.0013,+0.0080] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0018 | [+0.0001,+0.0034] |

## dtu / policy/attention_transfer/5s / unified/nll_bits / complete_seed_mean

Complete paired identities44/44; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0019 | [-0.0011,+0.0049] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0013 | [-0.0007,+0.0033] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0094 | [-0.0161,-0.0028] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0011 | [-0.0013,+0.0036] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0012 | [-0.0010,+0.0033] |
| local/antisymmetric versus local/mean | +0.0017 | [-0.0017,+0.0050] |
| local/selected versus local/mean | +0.0021 | [-0.0007,+0.0048] |
| cbramod/pretrained_full/selected versus local/selected | +0.0259 | [+0.0094,+0.0423] |
| cbramod/random_full/selected versus local/selected | -0.0046 | [-0.0205,+0.0113] |
| inner_selected_model versus local/selected | +0.0164 | [+0.0023,+0.0305] |
| reve/pretrained_full/selected versus local/selected | -0.0053 | [-0.0235,+0.0128] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0033 | [+0.0007,+0.0059] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0021 | [+0.0002,+0.0039] |

## fau / policy/attention_transfer/10s / native/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0042 | [-0.0011,+0.0096] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0004 | [-0.0038,+0.0029] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0046 | [-0.0163,+0.0071] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0036 | [-0.0036,+0.0108] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0021 | [-0.0042,+0.0085] |
| local/antisymmetric versus local/mean | -0.0013 | [-0.0074,+0.0047] |
| local/selected versus local/mean | -0.0018 | [-0.0055,+0.0020] |
| cbramod/pretrained_full/selected versus local/selected | -0.0072 | [-0.0225,+0.0082] |
| cbramod/random_full/selected versus local/selected | -0.0001 | [-0.0125,+0.0123] |
| inner_selected_model versus local/selected | -0.0118 | [-0.0236,+0.0001] |
| reve/pretrained_full/selected versus local/selected | -0.0016 | [-0.0179,+0.0148] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0019 | [-0.0041,+0.0080] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0013 | [-0.0044,+0.0070] |

## fau / policy/attention_transfer/10s / native/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0018 | [-0.0004,+0.0041] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0010 | [-0.0008,+0.0028] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0041 | [-0.0131,+0.0048] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0022 | [+0.0001,+0.0042] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0016 | [-0.0003,+0.0035] |
| local/antisymmetric versus local/mean | +0.0025 | [+0.0004,+0.0045] |
| local/selected versus local/mean | +0.0010 | [-0.0002,+0.0023] |
| cbramod/pretrained_full/selected versus local/selected | -0.0022 | [-0.0151,+0.0107] |
| cbramod/random_full/selected versus local/selected | -0.0016 | [-0.0120,+0.0087] |
| inner_selected_model versus local/selected | -0.0063 | [-0.0183,+0.0057] |
| reve/pretrained_full/selected versus local/selected | +0.0025 | [-0.0136,+0.0186] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0029 | [+0.0011,+0.0046] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0024 | [+0.0007,+0.0040] |

## fau / policy/attention_transfer/10s / unified/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0010 | [-0.0047,+0.0066] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0004 | [-0.0050,+0.0057] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0023 | [-0.0026,+0.0073] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0062 | [-0.0001,+0.0126] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0042 | [-0.0012,+0.0095] |
| local/antisymmetric versus local/mean | -0.0033 | [-0.0098,+0.0032] |
| local/selected versus local/mean | -0.0032 | [-0.0089,+0.0025] |
| cbramod/pretrained_full/selected versus local/selected | -0.0084 | [-0.0232,+0.0063] |
| cbramod/random_full/selected versus local/selected | -0.0117 | [-0.0260,+0.0027] |
| inner_selected_model versus local/selected | -0.0061 | [-0.0202,+0.0080] |
| reve/pretrained_full/selected versus local/selected | -0.0109 | [-0.0261,+0.0043] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0011 | [-0.0043,+0.0064] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0006 | [-0.0045,+0.0056] |

## fau / policy/attention_transfer/10s / unified/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0013 | [-0.0009,+0.0035] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0001 | [-0.0016,+0.0017] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0029 | [-0.0005,+0.0064] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0009 | [-0.0012,+0.0031] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0004 | [-0.0014,+0.0022] |
| local/antisymmetric versus local/mean | +0.0001 | [-0.0014,+0.0017] |
| local/selected versus local/mean | +0.0003 | [-0.0011,+0.0017] |
| cbramod/pretrained_full/selected versus local/selected | -0.0102 | [-0.0230,+0.0026] |
| cbramod/random_full/selected versus local/selected | -0.0115 | [-0.0203,-0.0027] |
| inner_selected_model versus local/selected | -0.0073 | [-0.0190,+0.0044] |
| reve/pretrained_full/selected versus local/selected | -0.0107 | [-0.0227,+0.0014] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0018 | [-0.0001,+0.0037] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0015 | [-0.0003,+0.0033] |

## fau / policy/attention_transfer/20s / native/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0032 | [-0.0041,+0.0105] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0002 | [-0.0040,+0.0036] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0067 | [-0.0202,+0.0068] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0019 | [-0.0068,+0.0105] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0002 | [-0.0055,+0.0059] |
| local/antisymmetric versus local/mean | +0.0021 | [-0.0091,+0.0133] |
| local/selected versus local/mean | +0.0017 | [-0.0039,+0.0073] |
| cbramod/pretrained_full/selected versus local/selected | -0.0121 | [-0.0348,+0.0106] |
| cbramod/random_full/selected versus local/selected | -0.0084 | [-0.0273,+0.0105] |
| inner_selected_model versus local/selected | -0.0188 | [-0.0395,+0.0020] |
| reve/pretrained_full/selected versus local/selected | -0.0001 | [-0.0242,+0.0240] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0007 | [-0.0086,+0.0072] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0010 | [-0.0053,+0.0074] |

## fau / policy/attention_transfer/20s / native/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0012 | [-0.0031,+0.0054] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0004 | [-0.0024,+0.0016] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0124 | [-0.0261,+0.0012] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0043 | [-0.0001,+0.0087] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0031 | [-0.0005,+0.0067] |
| local/antisymmetric versus local/mean | +0.0031 | [-0.0011,+0.0073] |
| local/selected versus local/mean | +0.0005 | [-0.0025,+0.0035] |
| cbramod/pretrained_full/selected versus local/selected | -0.0058 | [-0.0284,+0.0168] |
| cbramod/random_full/selected versus local/selected | -0.0022 | [-0.0204,+0.0159] |
| inner_selected_model versus local/selected | -0.0183 | [-0.0416,+0.0051] |
| reve/pretrained_full/selected versus local/selected | +0.0021 | [-0.0255,+0.0297] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0029 | [-0.0005,+0.0063] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0013 | [-0.0014,+0.0040] |

## fau / policy/attention_transfer/20s / unified/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [-0.0061,+0.0062] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0011 | [-0.0046,+0.0069] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0017 | [-0.0095,+0.0129] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0030 | [-0.0101,+0.0040] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0017 | [-0.0076,+0.0041] |
| local/antisymmetric versus local/mean | -0.0056 | [-0.0158,+0.0047] |
| local/selected versus local/mean | -0.0030 | [-0.0131,+0.0070] |
| cbramod/pretrained_full/selected versus local/selected | -0.0009 | [-0.0245,+0.0226] |
| cbramod/random_full/selected versus local/selected | -0.0151 | [-0.0350,+0.0048] |
| inner_selected_model versus local/selected | +0.0008 | [-0.0194,+0.0209] |
| reve/pretrained_full/selected versus local/selected | -0.0029 | [-0.0265,+0.0206] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0037 | [-0.0047,+0.0121] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0020 | [-0.0033,+0.0073] |

## fau / policy/attention_transfer/20s / unified/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | -0.0000 | [-0.0039,+0.0039] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | -0.0008 | [-0.0043,+0.0027] |
| inner_selected_model versus cbramod/pretrained_full/selected | +0.0041 | [-0.0036,+0.0117] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | -0.0030 | [-0.0060,-0.0001] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0017 | [-0.0042,+0.0009] |
| local/antisymmetric versus local/mean | -0.0029 | [-0.0062,+0.0004] |
| local/selected versus local/mean | -0.0016 | [-0.0046,+0.0014] |
| cbramod/pretrained_full/selected versus local/selected | -0.0177 | [-0.0400,+0.0045] |
| cbramod/random_full/selected versus local/selected | -0.0188 | [-0.0356,-0.0020] |
| inner_selected_model versus local/selected | -0.0136 | [-0.0340,+0.0067] |
| reve/pretrained_full/selected versus local/selected | -0.0162 | [-0.0383,+0.0060] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0006 | [-0.0024,+0.0036] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0012 | [-0.0031,+0.0008] |

## fau / policy/attention_transfer/5s / native/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0038 | [-0.0105,+0.0029] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | -0.0019 | [-0.0111,+0.0073] |
| cbramod/random_full/selected versus local/selected | +0.0007 | [-0.0079,+0.0092] |
| inner_selected_model versus local/selected | -0.0057 | [-0.0145,+0.0031] |
| reve/pretrained_full/selected versus local/selected | -0.0015 | [-0.0117,+0.0088] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## fau / policy/attention_transfer/5s / native/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [-0.0008,+0.0008] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [-0.0007,+0.0007] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0042 | [-0.0088,+0.0004] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0001 | [-0.0007,+0.0010] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0005 | [-0.0003,+0.0013] |
| local/antisymmetric versus local/mean | +0.0001 | [-0.0006,+0.0008] |
| local/selected versus local/mean | -0.0000 | [-0.0004,+0.0004] |
| cbramod/pretrained_full/selected versus local/selected | -0.0011 | [-0.0083,+0.0061] |
| cbramod/random_full/selected versus local/selected | -0.0006 | [-0.0058,+0.0047] |
| inner_selected_model versus local/selected | -0.0053 | [-0.0130,+0.0024] |
| reve/pretrained_full/selected versus local/selected | -0.0015 | [-0.0102,+0.0072] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0014 | [+0.0004,+0.0025] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0006 | [+0.0001,+0.0011] |

## fau / policy/attention_transfer/5s / unified/accuracy / 3401

Complete paired identities67/67; positive = candidate minus reference accuracy.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0016 | [-0.0052,+0.0021] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/random_full/selected versus cbramod/random_full/mean | +0.0000 | [+0.0000,+0.0000] |
| local/antisymmetric versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| local/selected versus local/mean | +0.0000 | [+0.0000,+0.0000] |
| cbramod/pretrained_full/selected versus local/selected | -0.0030 | [-0.0128,+0.0068] |
| cbramod/random_full/selected versus local/selected | -0.0084 | [-0.0173,+0.0005] |
| inner_selected_model versus local/selected | -0.0046 | [-0.0133,+0.0041] |
| reve/pretrained_full/selected versus local/selected | -0.0083 | [-0.0185,+0.0018] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | +0.0000 | [+0.0000,+0.0000] |

## fau / policy/attention_transfer/5s / unified/nll_bits / 3401

Complete paired identities67/67; positive = reference minus candidate NLL, bits/attention window.

| Comparison | Benefit | Simultaneous95% interval |
|---|---:|---:|
| cbramod/pretrained_full/antisymmetric versus cbramod/pretrained_full/mean | +0.0003 | [-0.0003,+0.0010] |
| cbramod/pretrained_full/selected versus cbramod/pretrained_full/mean | +0.0006 | [-0.0000,+0.0013] |
| inner_selected_model versus cbramod/pretrained_full/selected | -0.0007 | [-0.0027,+0.0013] |
| cbramod/random_full/antisymmetric versus cbramod/random_full/mean | +0.0000 | [-0.0005,+0.0005] |
| cbramod/random_full/selected versus cbramod/random_full/mean | -0.0002 | [-0.0006,+0.0002] |
| local/antisymmetric versus local/mean | -0.0001 | [-0.0005,+0.0002] |
| local/selected versus local/mean | +0.0001 | [-0.0002,+0.0003] |
| cbramod/pretrained_full/selected versus local/selected | -0.0038 | [-0.0102,+0.0025] |
| cbramod/random_full/selected versus local/selected | -0.0057 | [-0.0106,-0.0009] |
| inner_selected_model versus local/selected | -0.0045 | [-0.0106,+0.0016] |
| reve/pretrained_full/selected versus local/selected | -0.0053 | [-0.0119,+0.0012] |
| reve/pretrained_full/antisymmetric versus reve/pretrained_full/mean | -0.0008 | [-0.0017,+0.0002] |
| reve/pretrained_full/selected versus reve/pretrained_full/mean | -0.0003 | [-0.0011,+0.0005] |

