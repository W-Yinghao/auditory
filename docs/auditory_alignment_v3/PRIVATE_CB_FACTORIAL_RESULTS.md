# Private CBraMod initialization × learning-rate factorial

2026-10-18T19:47:38.256252+02:00, CPU job1045980; **interim**. 38/60 new crossed cells,60 reused original cells.

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

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0004 | [-0.0018,+0.0010] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0007 | [-0.0017,+0.0004] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0008 | [-0.0004,+0.0020] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0003 | [-0.0015,+0.0010] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0004 | [-0.0008,+0.0017] |

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

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0001 | [-0.0016,+0.0014] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0010 | [-0.0023,+0.0003] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0012 | [-0.0001,+0.0026] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0009 | [-0.0024,+0.0005] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0011 | [-0.0004,+0.0027] |

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

Complete paired children64/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0002 | [-0.0009,+0.0006] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0004 | [-0.0008,+0.0001] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0006 | [-0.0001,+0.0012] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0002 | [-0.0009,+0.0004] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0004 | [-0.0003,+0.0011] |

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

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0025 | [-0.0096,+0.0145] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0039 | [-0.0112,+0.0033] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0055 | [-0.0038,+0.0147] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0064 | [-0.0180,+0.0052] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0079 | [-0.0035,+0.0194] |

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

Complete paired children64/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0005 | [-0.0026,+0.0016] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0023 | [-0.0043,-0.0002] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0013 | [-0.0007,+0.0032] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0018 | [-0.0038,+0.0003] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0008 | [-0.0012,+0.0028] |

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

Complete paired children52/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0006 | [-0.0016,+0.0004] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0001 | [-0.0007,+0.0009] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0005 | [-0.0003,+0.0013] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0007 | [+0.0001,+0.0014] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0001 | [-0.0008,+0.0006] |

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

Complete paired children52/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0014 | [-0.0037,+0.0009] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0009 | [-0.0008,+0.0027] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0012 | [-0.0010,+0.0035] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0023 | [+0.0008,+0.0038] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0001 | [-0.0013,+0.0011] |

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

Complete paired children52/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0107 | [-0.0255,+0.0042] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0019 | [-0.0132,+0.0094] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0022 | [-0.0121,+0.0077] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0088 | [-0.0026,+0.0202] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0128 | [-0.0235,-0.0021] |

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

Complete paired children52/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0103 | [-0.0263,+0.0056] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0005 | [-0.0136,+0.0127] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0084 | [-0.0046,+0.0214] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0099 | [+0.0001,+0.0197] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0019 | [-0.0137,+0.0098] |

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

Complete paired children52/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0027 | [-0.0068,+0.0014] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0012 | [-0.0045,+0.0021] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0020 | [-0.0018,+0.0059] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0015 | [-0.0009,+0.0039] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0007 | [-0.0026,+0.0013] |

