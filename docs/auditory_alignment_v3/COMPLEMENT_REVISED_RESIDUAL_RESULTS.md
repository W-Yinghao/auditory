# ALN3.2 revised complement — wave 2b: trained residual with an epoch-0 candidate (seed 3401)

Generated 2026-10-16 10:33 CEST (Slurm job 1042744) by `python -m auditory_alignment_v3.aln32_residual_interim` under the frozen `ADDENDUM_10_ALN32_RESIDUAL.md` §5. Positive = candidate lower true-query risk. Selection on a fixed inner development group of training participants (epoch 0 = the base is a legal choice); test participants are never used.

Code sha256: `aln32_residual_interim.py` 200a1ab10876, `bc_interim.py` 2840df81b608, `sci_r1/stats.py` 8bb141cf6070.

Coverage: {'L0|complete': 50, 'RS|complete': 250}. Excluded pairs: 0.

## 1. Selected epoch 0 (no correction adopted), per configuration

| configuration | units | fraction epoch 0 |
|---|---|---|
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0.00 |
| RS|dtu|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0.00 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0.00 |
| RS|dtu|CS_SINGLE|reve|residual_aligned_random | 10 | 0.10 |
| RS|dtu|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0.00 |
| RS|dtu|NCE|cbramod|residual_aligned_pretrained | 10 | 0.00 |
| RS|dtu|NCE|cbramod|residual_aligned_random | 10 | 0.00 |
| RS|dtu|NCE|reve|residual_aligned_pretrained | 10 | 0.00 |
| RS|dtu|NCE|reve|residual_aligned_random | 10 | 0.00 |
| RS|dtu|NCE|small_capacity_branch|residual_small_capacity | 10 | 0.30 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_pretrained | 10 | 0.10 |
| RS|fau|CS_SINGLE|cbramod|residual_aligned_random | 10 | 0.10 |
| RS|fau|CS_SINGLE|reve|residual_aligned_pretrained | 10 | 0.10 |
| RS|fau|CS_SINGLE|reve|residual_aligned_random | 10 | 0.10 |
| RS|fau|CS_SINGLE|small_capacity_branch|residual_small_capacity | 10 | 0.10 |
| RS|fau|NCE|cbramod|residual_aligned_pretrained | 10 | 0.00 |
| RS|fau|NCE|cbramod|residual_aligned_random | 10 | 0.00 |
| RS|fau|NCE|reve|residual_aligned_pretrained | 10 | 0.00 |
| RS|fau|NCE|reve|residual_aligned_random | 10 | 0.00 |
| RS|fau|NCE|small_capacity_branch|residual_small_capacity | 10 | 0.10 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_pretrained | 5 | 0.20 |
| RS|federici|CS_SINGLE|cbramod|residual_aligned_random | 5 | 0.20 |
| RS|federici|CS_SINGLE|reve|residual_aligned_pretrained | 5 | 0.20 |
| RS|federici|CS_SINGLE|reve|residual_aligned_random | 5 | 0.60 |
| RS|federici|CS_SINGLE|small_capacity_branch|residual_small_capacity | 5 | 0.00 |
| RS|federici|NCE|cbramod|residual_aligned_pretrained | 5 | 0.00 |
| RS|federici|NCE|cbramod|residual_aligned_random | 5 | 0.00 |
| RS|federici|NCE|reve|residual_aligned_pretrained | 5 | 0.00 |
| RS|federici|NCE|reve|residual_aligned_random | 5 | 0.00 |
| RS|federici|NCE|small_capacity_branch|residual_small_capacity | 5 | 0.00 |

## 2. Wording rule (mechanical)

| dataset · objective · backbone | RS-VALUE pretrained | vs random | vs small | wording |
|---|---|---|---|---|
| fau · NCE · cbramod | contains 0 | contains 0 | I<0 | no correction resolved |
| fau · NCE · reve | contains 0 | contains 0 | contains 0 | no correction resolved |
| fau · CS_SINGLE · cbramod | contains 0 | contains 0 | I>0 | no correction resolved |
| fau · CS_SINGLE · reve | contains 0 | contains 0 | I>0 | no correction resolved |
| dtu · NCE · cbramod | contains 0 | contains 0 | I<0 | no correction resolved |
| dtu · NCE · reve | contains 0 | contains 0 | I<0 | no correction resolved |
| dtu · CS_SINGLE · cbramod | contains 0 | contains 0 | I>0 | no correction resolved |
| dtu · CS_SINGLE · reve | contains 0 | contains 0 | I>0 | no correction resolved |
| federici · NCE · cbramod | contains 0 | contains 0 | contains 0 | no correction resolved |
| federici · NCE · reve | contains 0 | I>0 | contains 0 | no correction resolved |
| federici · CS_SINGLE · cbramod | contains 0 | contains 0 | contains 0 | no correction resolved |
| federici · CS_SINGLE · reve | contains 0 | contains 0 | contains 0 | no correction resolved |

## 3. Value over the base

**fau · NCE** (critical value 2.96)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.001 | -0.000 | -0.004 | -0.000 |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.001 | -0.003 | +0.000 |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | -0.003 | +0.000 |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 67 | -0.000 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 | -0.000 | -0.004 | -0.000 |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 67 | +0.007 | [+0.001, +0.012] | [-0.001, +0.014] | contains 0 | +0.001 | +0.006 | +0.004 | -0.001 |

**fau · CS_SINGLE** (critical value 2.73)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 67 | -0.002 | [-0.004, +0.001] | [-0.005, +0.001] | contains 0 | -0.000 | -0.001 | -0.001 | +0.001 |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 67 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 | -0.000 | +0.001 |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 67 | -0.001 | [-0.002, +0.001] | [-0.003, +0.002] | contains 0 | +0.000 | -0.000 | -0.001 | +0.000 |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | -0.000 | +0.001 |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 67 | -0.018 | [-0.032, -0.005] | [-0.037, -0.000] | I<0 | -0.003 | -0.068 | -0.021 | +0.004 |

**dtu · NCE** (critical value 2.67)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.000 | +0.002 | -0.000 |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | +0.003 | -0.000 |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.000 | +0.002 | +0.000 |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.000 | +0.003 | -0.000 |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 44 | +0.016 | [+0.006, +0.026] | [+0.004, +0.028] | I>0 | +0.002 | +0.015 | +0.012 | +0.001 |

**dtu · CS_SINGLE** (critical value 2.86)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 44 | -0.021 | [-0.039, -0.003] | [-0.045, +0.003] | contains 0 | -0.000 | -0.016 | -0.022 | +0.001 |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 44 | -0.003 | [-0.006, +0.001] | [-0.007, +0.002] | contains 0 | -0.000 | -0.001 | +0.001 | +0.001 |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 44 | -0.016 | [-0.027, -0.005] | [-0.031, -0.001] | I<0 | -0.001 | -0.013 | -0.009 | -0.001 |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 44 | +0.002 | [-0.000, +0.004] | [-0.001, +0.005] | contains 0 | +0.001 | +0.003 | +0.001 | +0.001 |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 44 | -0.087 | [-0.105, -0.069] | [-0.112, -0.061] | I<0 | -0.004 | -0.071 | -0.054 | -0.009 |

**federici · NCE** (critical value 2.74)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 86 | +0.001 | [-0.000, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 | +0.001 | +0.002 | – |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 86 | +0.001 | [+0.000, +0.002] | [-0.000, +0.002] | contains 0 | -0.001 | +0.001 | +0.003 | – |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | -0.000 | +0.004 | – |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.004 | – |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 86 | +0.001 | [+0.000, +0.003] | [-0.000, +0.003] | contains 0 | -0.000 | +0.001 | +0.004 | – |

**federici · CS_SINGLE** (critical value 2.40)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 86 | +0.000 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | +0.001 | +0.000 | +0.000 | – |
| reve/residual_aligned_pretrained | vs base (epoch-0 candidate allowed) | 86 | -0.001 | [-0.004, +0.003] | [-0.005, +0.004] | contains 0 | +0.001 | +0.011 | -0.000 | – |
| cbramod/residual_aligned_random | vs base (epoch-0 candidate allowed) | 86 | +0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | +0.001 | +0.011 | +0.000 | – |
| reve/residual_aligned_random | vs base (epoch-0 candidate allowed) | 86 | -0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | +0.000 | +0.011 | +0.000 | – |
| small_capacity_branch/residual_small_capacity | vs base (epoch-0 candidate allowed) | 86 | -0.002 | [-0.010, +0.006] | [-0.012, +0.007] | contains 0 | +0.002 | +0.001 | -0.000 | – |

## 4. Attribution

**fau · NCE · cbramod** (critical value 2.32)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | -0.000 | -0.000 | -0.001 | -0.000 |
| pretrained_vs_small | beyond a small branch, same access | 67 | -0.007 | [-0.012, -0.002] | [-0.013, -0.001] | I<0 | -0.002 | -0.007 | -0.008 | +0.001 |

**fau · NCE · reve** (critical value 2.69)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | +0.001 | [+0.000, +0.001] | [-0.000, +0.001] | contains 0 | -0.000 | +0.001 | +0.002 | +0.000 |
| pretrained_vs_small | beyond a small branch, same access | 67 | -0.006 | [-0.011, -0.001] | [-0.013, +0.001] | contains 0 | -0.002 | -0.006 | -0.007 | +0.001 |

**fau · CS_SINGLE · cbramod** (critical value 2.29)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | -0.001 | [-0.003, +0.001] | [-0.004, +0.001] | contains 0 | -0.000 | -0.001 | -0.000 | +0.001 |
| pretrained_vs_small | beyond a small branch, same access | 67 | +0.017 | [+0.004, +0.030] | [+0.002, +0.032] | I>0 | +0.003 | +0.067 | +0.020 | -0.003 |

**fau · CS_SINGLE · reve** (critical value 2.35)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.001 | +0.000 | +0.000 | -0.000 |
| pretrained_vs_small | beyond a small branch, same access | 67 | +0.018 | [+0.005, +0.032] | [+0.003, +0.034] | I>0 | +0.003 | +0.068 | +0.021 | -0.003 |

**dtu · NCE · cbramod** (critical value 2.87)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 | -0.000 |
| pretrained_vs_small | beyond a small branch, same access | 44 | -0.015 | [-0.025, -0.006] | [-0.028, -0.002] | I<0 | -0.002 | -0.015 | -0.010 | -0.001 |

**dtu · NCE · reve** (critical value 2.36)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | -0.000 | +0.000 | +0.000 |
| pretrained_vs_small | beyond a small branch, same access | 44 | -0.016 | [-0.025, -0.006] | [-0.026, -0.005] | I<0 | -0.002 | -0.015 | -0.010 | -0.001 |

**dtu · CS_SINGLE · cbramod** (critical value 2.47)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | -0.005 | [-0.025, +0.016] | [-0.027, +0.018] | contains 0 | +0.001 | -0.004 | -0.013 | +0.002 |
| pretrained_vs_small | beyond a small branch, same access | 44 | +0.066 | [+0.047, +0.084] | [+0.043, +0.088] | I>0 | +0.004 | +0.055 | +0.032 | +0.010 |

**dtu · CS_SINGLE · reve** (critical value 2.35)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | -0.004 | [-0.008, -0.000] | [-0.009, +0.000] | contains 0 | -0.001 | -0.003 | -0.001 | -0.001 |
| pretrained_vs_small | beyond a small branch, same access | 44 | +0.084 | [+0.067, +0.101] | [+0.064, +0.104] | I>0 | +0.004 | +0.070 | +0.055 | +0.010 |

**federici · NCE · cbramod** (critical value 2.47)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.001 | [-0.000, +0.002] | [-0.000, +0.002] | contains 0 | +0.000 | +0.001 | -0.001 | – |
| pretrained_vs_small | beyond a small branch, same access | 86 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | +0.001 | +0.000 | -0.002 | – |

**federici · NCE · reve** (critical value 2.30)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.001 | [+0.000, +0.002] | [+0.000, +0.002] | I>0 | -0.001 | +0.001 | -0.001 | – |
| pretrained_vs_small | beyond a small branch, same access | 86 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 | +0.000 | -0.002 | – |

**federici · CS_SINGLE · cbramod** (critical value 2.28)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | -0.000 | -0.011 | -0.000 | – |
| pretrained_vs_small | beyond a small branch, same access | 86 | +0.002 | [-0.006, +0.010] | [-0.007, +0.011] | contains 0 | -0.001 | -0.000 | +0.000 | – |

**federici · CS_SINGLE · reve** (critical value 2.28)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | +0.001 | -0.000 | -0.000 | – |
| pretrained_vs_small | beyond a small branch, same access | 86 | +0.002 | [-0.008, +0.011] | [-0.009, +0.012] | contains 0 | -0.001 | +0.010 | +0.000 | – |

## Appendix: notes

- RS-VALUE|federici|NCE|sec/cbramod/residual_aligned_pretrained/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|NCE|sec/reve/residual_aligned_pretrained/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|NCE|sec/cbramod/residual_aligned_random/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|NCE|sec/reve/residual_aligned_random/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|NCE|sec/small_capacity_branch/residual_small_capacity/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|NCE|cbramod|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|NCE|cbramod|sec/pretrained_vs_small/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|NCE|reve|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|NCE|reve|sec/pretrained_vs_small/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|CS_SINGLE|sec/cbramod/residual_aligned_pretrained/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|CS_SINGLE|sec/reve/residual_aligned_pretrained/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|CS_SINGLE|sec/cbramod/residual_aligned_random/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|CS_SINGLE|sec/reve/residual_aligned_random/attention/unified/accuracy: no paired identities
- RS-VALUE|federici|CS_SINGLE|sec/small_capacity_branch/residual_small_capacity/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|CS_SINGLE|cbramod|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|CS_SINGLE|cbramod|sec/pretrained_vs_small/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|CS_SINGLE|reve|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- RS-ATTRIB|federici|CS_SINGLE|reve|sec/pretrained_vs_small/attention/unified/accuracy: no paired identities
