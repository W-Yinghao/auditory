# Private CBraMod initialization × learning-rate factorial

2026-10-18T16:04:43.913371+02:00, CPU job1045980; **interim**. 26/60 new crossed cells,60 reused original cells.

All four initialization/rate combinations are preserved. The two original rate pairs are fixed; there is no outer-test choice. Encoder training, checkpoint selection and original evaluation interfaces remain unchanged. Same64 previously studied children; no independent clinical replication. Original positive-affine and native probability interfaces remain separate.

## private_factorial/CS_SINGLE / affine_nll / 3401

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0003 | [-0.0016,+0.0009] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0005 | [-0.0017,+0.0006] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0016 | [+0.0000,+0.0032] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0002 | [-0.0011,+0.0007] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0013 | [-0.0001,+0.0027] |

## private_factorial/CS_SINGLE / affine_nll / 3407

Complete paired children26/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0013 | [-0.0035,+0.0010] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0004 | [-0.0020,+0.0013] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0001 | [-0.0021,+0.0023] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0009 | [-0.0007,+0.0025] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0012 | [-0.0034,+0.0010] |

## private_factorial/CS_SINGLE / history_gain / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0006 | [-0.0010,+0.0021] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0003 | [-0.0014,+0.0008] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0013 | [-0.0002,+0.0027] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0008 | [-0.0022,+0.0005] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0018 | [+0.0005,+0.0032] |

## private_factorial/CS_SINGLE / history_gain / 3407

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0015 | [-0.0035,+0.0005] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0019 | [-0.0043,+0.0005] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0001 | [-0.0022,+0.0024] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0004 | [-0.0025,+0.0017] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0014 | [-0.0043,+0.0014] |

## private_factorial/CS_SINGLE / native_nll / 3401

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0004 | [-0.0011,+0.0002] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0004 | [-0.0010,+0.0001] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0012 | [+0.0005,+0.0020] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0000 | [-0.0004,+0.0004] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0008 | [+0.0002,+0.0014] |

## private_factorial/CS_SINGLE / native_nll / 3407

Complete paired children26/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0008 | [-0.0021,+0.0005] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0004 | [-0.0012,+0.0005] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0004 | [-0.0006,+0.0014] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0004 | [-0.0006,+0.0014] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0004 | [-0.0018,+0.0009] |

## private_factorial/CS_SINGLE / score_auc / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0048 | [-0.0066,+0.0162] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0032 | [-0.0101,+0.0037] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0143 | [+0.0044,+0.0243] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0080 | [-0.0175,+0.0016] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0192 | [+0.0070,+0.0313] |

## private_factorial/CS_SINGLE / score_auc / 3407

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0049 | [-0.0235,+0.0137] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0007 | [-0.0114,+0.0128] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0024 | [-0.0182,+0.0134] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0056 | [-0.0100,+0.0212] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0073 | [-0.0256,+0.0111] |

## private_factorial/CS_SINGLE / twin_sensitivity / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0010 | [-0.0030,+0.0009] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0009 | [-0.0022,+0.0004] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0014 | [-0.0004,+0.0031] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0002 | [-0.0015,+0.0018] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0003 | [-0.0014,+0.0021] |

## private_factorial/CS_SINGLE / twin_sensitivity / 3407

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0006 | [-0.0040,+0.0029] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0021 | [-0.0073,+0.0030] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0008 | [-0.0046,+0.0031] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0016 | [-0.0057,+0.0026] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0014 | [-0.0061,+0.0034] |

## private_factorial/NCE / affine_nll / 3401

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0009 | [-0.0023,+0.0005] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0006 | [-0.0017,+0.0005] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0005 | [-0.0008,+0.0017] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0003 | [-0.0004,+0.0011] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0004 | [-0.0013,+0.0005] |

## private_factorial/NCE / affine_nll / 3407

Complete paired children13/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0015 | [-0.0035,+0.0004] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0002 | [-0.0018,+0.0014] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0013 | [-0.0006,+0.0032] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0013 | [-0.0002,+0.0028] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0003 | [-0.0020,+0.0015] |

## private_factorial/NCE / history_gain / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0004 | [-0.0015,+0.0023] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0000 | [-0.0016,+0.0016] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0004 | [-0.0011,+0.0020] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0004 | [-0.0020,+0.0012] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0008 | [-0.0003,+0.0020] |

## private_factorial/NCE / history_gain / 3407

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0017 | [-0.0083,+0.0050] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0009 | [-0.0045,+0.0062] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0012 | [-0.0062,+0.0086] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0025 | [-0.0004,+0.0054] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0005 | [-0.0037,+0.0028] |

## private_factorial/NCE / native_nll / 3401

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0451 | [-0.0694,-0.0209] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0284 | [-0.0496,-0.0071] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0309 | [+0.0095,+0.0523] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0168 | [+0.0103,+0.0233] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0143 | [-0.0257,-0.0028] |

## private_factorial/NCE / native_nll / 3407

Complete paired children13/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0412 | [-0.0649,-0.0175] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0059 | [-0.0279,+0.0160] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0005 | [-0.0225,+0.0236] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0353 | [+0.0136,+0.0570] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0407 | [-0.0620,-0.0194] |

## private_factorial/NCE / score_auc / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0074 | [-0.0235,+0.0088] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0076 | [-0.0201,+0.0049] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0059 | [-0.0069,+0.0187] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0002 | [-0.0091,+0.0087] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0014 | [-0.0134,+0.0105] |

## private_factorial/NCE / score_auc / 3407

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0194 | [-0.0544,+0.0156] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0039 | [-0.0311,+0.0233] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0136 | [-0.0197,+0.0469] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0155 | [-0.0098,+0.0408] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0058 | [-0.0445,+0.0329] |

## private_factorial/NCE / twin_sensitivity / 3401

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0017 | [-0.0010,+0.0044] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0003 | [-0.0013,+0.0020] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0014 | [-0.0034,+0.0006] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0014 | [-0.0038,+0.0010] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0003 | [-0.0017,+0.0022] |

## private_factorial/NCE / twin_sensitivity / 3407

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0024 | [-0.0208,+0.0160] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0011 | [-0.0154,+0.0131] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0045 | [-0.0122,+0.0212] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0012 | [-0.0055,+0.0079] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0021 | [-0.0025,+0.0067] |

