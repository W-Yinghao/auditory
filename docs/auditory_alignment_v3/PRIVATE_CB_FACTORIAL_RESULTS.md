# Private CBraMod initialization × learning-rate factorial

2026-10-18T00:59:33.686687+02:00, CPU job1044744; **interim**. 6/60 new crossed cells,60 reused original cells.

All four initialization/rate combinations are preserved. The two original rate pairs are fixed; there is no outer-test choice. Encoder training, checkpoint selection and original evaluation interfaces remain unchanged. Same64 previously studied children; no independent clinical replication. Original positive-affine and native probability interfaces remain separate.

## private_factorial/CS_SINGLE / affine_nll / 3401

Complete paired children26/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0004 | [-0.0019,+0.0027] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0003 | [-0.0017,+0.0023] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0007 | [-0.0023,+0.0037] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0001 | [-0.0018,+0.0016] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0011 | [-0.0017,+0.0039] |

## private_factorial/CS_SINGLE / history_gain / 3401

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0019 | [-0.0006,+0.0043] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0007 | [-0.0007,+0.0021] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0004 | [-0.0023,+0.0031] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0012 | [-0.0039,+0.0015] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0023 | [-0.0004,+0.0049] |

## private_factorial/CS_SINGLE / native_nll / 3401

Complete paired children26/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0002 | [-0.0010,+0.0014] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0001 | [-0.0011,+0.0009] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0006 | [-0.0007,+0.0019] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0003 | [-0.0012,+0.0005] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0008 | [-0.0003,+0.0019] |

## private_factorial/CS_SINGLE / score_auc / 3401

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0048 | [-0.0152,+0.0248] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0011 | [-0.0105,+0.0128] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0069 | [-0.0120,+0.0258] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0037 | [-0.0190,+0.0117] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0117 | [-0.0073,+0.0307] |

## private_factorial/CS_SINGLE / twin_sensitivity / 3401

Complete paired children26/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0006 | [-0.0026,+0.0038] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0002 | [-0.0018,+0.0021] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0011 | [-0.0019,+0.0040] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0004 | [-0.0037,+0.0029] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0016 | [-0.0016,+0.0049] |

## private_factorial/NCE / affine_nll / 3401

Complete paired children13/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | -0.0012 | [-0.0061,+0.0038] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0006 | [-0.0022,+0.0034] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | +0.0003 | [-0.0028,+0.0034] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0018 | [-0.0011,+0.0046] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0009 | [-0.0033,+0.0015] |

## private_factorial/NCE / history_gain / 3401

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0003 | [-0.0058,+0.0063] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0003 | [-0.0076,+0.0071] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0006 | [-0.0064,+0.0052] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0005 | [-0.0080,+0.0069] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0003 | [-0.0048,+0.0042] |

## private_factorial/NCE / native_nll / 3401

Complete paired children13/64; positive = reference minus candidate NLL, bits/trial.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0518 | [+0.0215,+0.0821] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0654 | [+0.0456,+0.0852] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0294 | [-0.0530,-0.0058] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0136 | [-0.0027,+0.0299] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0224 | [+0.0077,+0.0371] |

## private_factorial/NCE / score_auc / 3401

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0042 | [-0.0608,+0.0693] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | +0.0153 | [-0.0212,+0.0519] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0026 | [-0.0441,+0.0389] |
| random_full/random_recipe versus random_full/pre_recipe | +0.0111 | [-0.0261,+0.0483] |
| pretrained_full/random_recipe versus random_full/random_recipe | +0.0017 | [-0.0369,+0.0402] |

## private_factorial/NCE / twin_sensitivity / 3401

Complete paired children13/64; positive = candidate minus reference.

| Contrast | Benefit | Simultaneous95% interval |
|---|---:|---:|
| initialization_x_rate_interaction versus interaction_reference_zero | +0.0016 | [-0.0094,+0.0126] |
| pretrained_full/random_recipe versus pretrained_full/pre_recipe | -0.0012 | [-0.0082,+0.0057] |
| pretrained_full/pre_recipe versus random_full/pre_recipe | -0.0016 | [-0.0095,+0.0062] |
| random_full/random_recipe versus random_full/pre_recipe | -0.0028 | [-0.0170,+0.0114] |
| pretrained_full/random_recipe versus random_full/random_recipe | -0.0001 | [-0.0100,+0.0098] |

