# ALN3.2 revised complement — wave 2a: low-complexity fusion in the common prediction space (seed 3401, NCE)

Generated 2026-10-15 06:32 CEST (Slurm job 1040973) by `python -m auditory_alignment_v3.aln32_complement_interim` under the frozen `ADDENDUM_09_ALN32_SIMPLE_COMPLEMENT.md` §5 (ADDENDUM_05 machinery). Positive = candidate lower true-query risk. Residual ridges are fitted on out-of-fold base predictions over 5 groups of training participants; alphas by grouped CV. Base L0 reads post-only EEG (candidates read the aligned window: context-assisted); base L1 is access-matched.

Code sha256: `aln32_complement_interim.py` 22409a9237e5, `bc_interim.py` 2840df81b608, `sci_r1/stats.py` 8bb141cf6070.

Coverage: {'SC|complete': 600}. Excluded pairs: 0.

## 1. Wording rule (mechanical)

| dataset · backbone · base | SC-VALUE aligned_pretrained | vs random | vs capacity | wording |
|---|---|---|---|---|
| fau · cbramod · L0 | contains 0 | contains 0 | contains 0 | no complement resolved |
| fau · cbramod · L1 | contains 0 | contains 0 | contains 0 | no complement resolved |
| fau · reve · L0 | contains 0 | contains 0 | contains 0 | no complement resolved |
| fau · reve · L1 | contains 0 | contains 0 | contains 0 | no complement resolved |
| dtu · cbramod · L0 | I>0 | contains 0 | I>0 | added aligned features lower risk; source not separated (context-assisted: base L0 reads post-only EEG) |
| dtu · cbramod · L1 | I>0 | contains 0 | contains 0 | added aligned features lower risk; source not separated |
| dtu · reve · L0 | I>0 | contains 0 | I>0 | added aligned features lower risk; source not separated (context-assisted: base L0 reads post-only EEG) |
| dtu · reve · L1 | I>0 | contains 0 | contains 0 | added aligned features lower risk; source not separated |
| federici · cbramod · L0 | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici · cbramod · L1 | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici · reve · L0 | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici · reve · L1 | contains 0 | contains 0 | contains 0 | no complement resolved |

## 2. Value over local_only

**fau · cbramod · L0** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 67 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 | -0.000 | +0.000 |
| aligned_pretrained | vs local_only (context-assisted) | 67 | +0.007 | [-0.012, +0.026] | [-0.017, +0.031] | contains 0 | +0.005 | +0.090 | +0.002 | -0.003 |
| aligned_random | vs local_only (context-assisted) | 67 | +0.018 | [-0.000, +0.037] | [-0.005, +0.041] | contains 0 | +0.002 | +0.042 | -0.009 | +0.000 |
| small_context | vs local_only (context-assisted) | 67 | -0.001 | [-0.019, +0.017] | [-0.024, +0.022] | contains 0 | +0.004 | +0.040 | -0.015 | -0.001 |
| concat | vs local_only (context-assisted) | 67 | +0.012 | [-0.006, +0.031] | [-0.011, +0.036] | contains 0 | +0.004 | +0.097 | -0.001 | -0.002 |

**fau · cbramod · L1** (critical value 2.60)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 67 | -0.010 | [-0.020, -0.000] | [-0.022, +0.002] | contains 0 | -0.001 | +0.018 | -0.002 | -0.001 |
| aligned_pretrained | vs local_only (access-matched) | 67 | +0.008 | [-0.004, +0.019] | [-0.008, +0.023] | contains 0 | +0.002 | +0.071 | +0.005 | +0.000 |
| aligned_random | vs local_only (access-matched) | 67 | +0.003 | [-0.009, +0.015] | [-0.013, +0.019] | contains 0 | +0.001 | +0.063 | +0.003 | -0.000 |
| small_context | vs local_only (access-matched) | 67 | +0.003 | [-0.011, +0.018] | [-0.015, +0.022] | contains 0 | +0.004 | +0.089 | +0.005 | +0.003 |
| concat | vs local_only (access-matched) | 67 | +0.004 | [-0.008, +0.016] | [-0.012, +0.020] | contains 0 | +0.001 | +0.071 | +0.000 | -0.000 |

**fau · reve · L0** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 67 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | -0.000 | -0.000 | -0.000 | +0.000 |
| aligned_pretrained | vs local_only (context-assisted) | 67 | +0.005 | [-0.012, +0.022] | [-0.017, +0.027] | contains 0 | +0.001 | +0.019 | -0.011 | -0.003 |
| aligned_random | vs local_only (context-assisted) | 67 | +0.004 | [-0.016, +0.024] | [-0.021, +0.029] | contains 0 | +0.004 | +0.047 | -0.015 | -0.001 |
| small_context | vs local_only (context-assisted) | 67 | -0.011 | [-0.028, +0.006] | [-0.032, +0.010] | contains 0 | +0.003 | +0.008 | -0.016 | -0.001 |
| concat | vs local_only (context-assisted) | 67 | +0.006 | [-0.011, +0.022] | [-0.015, +0.026] | contains 0 | +0.001 | +0.016 | -0.011 | -0.003 |

**fau · reve · L1** (critical value 2.58)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 67 | -0.010 | [-0.020, -0.000] | [-0.022, +0.002] | contains 0 | -0.001 | +0.018 | -0.002 | -0.001 |
| aligned_pretrained | vs local_only (access-matched) | 67 | +0.001 | [-0.010, +0.013] | [-0.013, +0.016] | contains 0 | -0.000 | +0.060 | -0.002 | -0.002 |
| aligned_random | vs local_only (access-matched) | 67 | -0.000 | [-0.014, +0.014] | [-0.018, +0.017] | contains 0 | +0.004 | +0.084 | +0.003 | +0.000 |
| small_context | vs local_only (access-matched) | 67 | +0.004 | [-0.011, +0.018] | [-0.015, +0.022] | contains 0 | +0.004 | +0.088 | +0.005 | +0.004 |
| concat | vs local_only (access-matched) | 67 | -0.001 | [-0.013, +0.011] | [-0.016, +0.014] | contains 0 | -0.001 | +0.057 | -0.006 | -0.002 |

**dtu · cbramod · L0** (critical value 2.61)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 44 | +0.003 | [-0.006, +0.012] | [-0.009, +0.015] | contains 0 | +0.001 | +0.009 | -0.009 | +0.000 |
| aligned_pretrained | vs local_only (context-assisted) | 44 | +0.048 | [+0.028, +0.069] | [+0.021, +0.075] | I>0 | +0.002 | +0.029 | -0.006 | +0.005 |
| aligned_random | vs local_only (context-assisted) | 44 | +0.041 | [+0.024, +0.058] | [+0.018, +0.064] | I>0 | -0.001 | +0.020 | -0.023 | +0.005 |
| small_context | vs local_only (context-assisted) | 44 | +0.045 | [+0.025, +0.066] | [+0.018, +0.073] | I>0 | -0.000 | +0.032 | -0.001 | +0.003 |
| concat | vs local_only (context-assisted) | 44 | +0.051 | [+0.031, +0.071] | [+0.025, +0.076] | I>0 | +0.001 | +0.029 | -0.008 | +0.005 |

**dtu · cbramod · L1** (critical value 2.62)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 44 | +0.040 | [+0.024, +0.057] | [+0.019, +0.062] | I>0 | +0.003 | +0.072 | -0.019 | +0.002 |
| aligned_pretrained | vs local_only (access-matched) | 44 | +0.049 | [+0.032, +0.066] | [+0.027, +0.071] | I>0 | +0.007 | +0.029 | +0.002 | +0.003 |
| aligned_random | vs local_only (access-matched) | 44 | +0.043 | [+0.030, +0.056] | [+0.026, +0.060] | I>0 | +0.007 | +0.017 | -0.017 | +0.003 |
| small_context | vs local_only (access-matched) | 44 | +0.061 | [+0.046, +0.075] | [+0.042, +0.080] | I>0 | +0.008 | +0.047 | +0.010 | +0.003 |
| concat | vs local_only (access-matched) | 44 | +0.036 | [+0.020, +0.053] | [+0.015, +0.057] | I>0 | +0.008 | +0.015 | -0.009 | +0.003 |

**dtu · reve · L0** (critical value 2.54)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 44 | +0.003 | [-0.006, +0.012] | [-0.008, +0.015] | contains 0 | +0.001 | +0.009 | -0.009 | +0.000 |
| aligned_pretrained | vs local_only (context-assisted) | 44 | +0.044 | [+0.020, +0.068] | [+0.014, +0.073] | I>0 | +0.005 | +0.016 | -0.014 | +0.005 |
| aligned_random | vs local_only (context-assisted) | 44 | +0.052 | [+0.029, +0.074] | [+0.023, +0.081] | I>0 | +0.005 | +0.030 | -0.001 | +0.007 |
| small_context | vs local_only (context-assisted) | 44 | +0.047 | [+0.026, +0.069] | [+0.020, +0.075] | I>0 | +0.000 | +0.033 | +0.001 | +0.003 |
| concat | vs local_only (context-assisted) | 44 | +0.033 | [+0.010, +0.056] | [+0.005, +0.061] | I>0 | +0.003 | +0.005 | -0.028 | +0.003 |

**dtu · reve · L1** (critical value 2.57)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 44 | +0.040 | [+0.024, +0.057] | [+0.019, +0.062] | I>0 | +0.003 | +0.072 | -0.019 | +0.003 |
| aligned_pretrained | vs local_only (access-matched) | 44 | +0.049 | [+0.028, +0.070] | [+0.021, +0.076] | I>0 | +0.008 | +0.079 | -0.009 | +0.001 |
| aligned_random | vs local_only (access-matched) | 44 | +0.062 | [+0.047, +0.077] | [+0.043, +0.081] | I>0 | +0.007 | +0.044 | +0.010 | +0.002 |
| small_context | vs local_only (access-matched) | 44 | +0.060 | [+0.045, +0.074] | [+0.041, +0.079] | I>0 | +0.009 | +0.046 | +0.011 | +0.004 |
| concat | vs local_only (access-matched) | 44 | +0.015 | [-0.007, +0.037] | [-0.013, +0.043] | contains 0 | +0.006 | +0.048 | -0.022 | +0.001 |

**federici · cbramod · L0** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 86 | +0.007 | [-0.002, +0.016] | [-0.005, +0.018] | contains 0 | +0.001 | +0.006 | +0.008 | – |
| aligned_pretrained | vs local_only (context-assisted) | 86 | -0.003 | [-0.014, +0.007] | [-0.017, +0.010] | contains 0 | -0.002 | -0.007 | -0.003 | – |
| aligned_random | vs local_only (context-assisted) | 86 | -0.002 | [-0.010, +0.007] | [-0.012, +0.009] | contains 0 | -0.001 | -0.015 | +0.005 | – |
| small_context | vs local_only (context-assisted) | 86 | -0.004 | [-0.012, +0.005] | [-0.015, +0.008] | contains 0 | +0.000 | -0.016 | +0.004 | – |
| concat | vs local_only (context-assisted) | 86 | -0.002 | [-0.009, +0.005] | [-0.011, +0.007] | contains 0 | +0.000 | -0.003 | -0.002 | – |

**federici · cbramod · L1** (critical value 2.58)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 86 | +0.009 | [-0.001, +0.019] | [-0.003, +0.021] | contains 0 | +0.000 | +0.006 | +0.013 | – |
| aligned_pretrained | vs local_only (access-matched) | 86 | +0.006 | [-0.005, +0.018] | [-0.008, +0.021] | contains 0 | +0.005 | +0.008 | +0.007 | – |
| aligned_random | vs local_only (access-matched) | 86 | +0.003 | [-0.003, +0.010] | [-0.005, +0.011] | contains 0 | +0.000 | -0.002 | +0.009 | – |
| small_context | vs local_only (access-matched) | 86 | +0.008 | [-0.002, +0.017] | [-0.004, +0.020] | contains 0 | -0.002 | -0.010 | +0.008 | – |
| concat | vs local_only (access-matched) | 86 | +0.001 | [-0.005, +0.008] | [-0.007, +0.010] | contains 0 | +0.001 | +0.004 | +0.002 | – |

**federici · reve · L0** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (context-assisted) | 86 | +0.007 | [-0.002, +0.016] | [-0.005, +0.018] | contains 0 | +0.001 | +0.006 | +0.008 | – |
| aligned_pretrained | vs local_only (context-assisted) | 86 | -0.002 | [-0.010, +0.007] | [-0.013, +0.010] | contains 0 | -0.001 | -0.009 | +0.006 | – |
| aligned_random | vs local_only (context-assisted) | 86 | -0.005 | [-0.015, +0.004] | [-0.017, +0.006] | contains 0 | +0.000 | -0.019 | +0.003 | – |
| small_context | vs local_only (context-assisted) | 86 | -0.004 | [-0.013, +0.005] | [-0.015, +0.008] | contains 0 | +0.001 | -0.016 | +0.004 | – |
| concat | vs local_only (context-assisted) | 86 | +0.001 | [-0.006, +0.007] | [-0.008, +0.009] | contains 0 | -0.000 | -0.011 | +0.001 | – |

**federici · reve · L1** (critical value 2.56)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| local_refit_capacity | vs local_only (access-matched) | 86 | +0.009 | [-0.000, +0.018] | [-0.003, +0.021] | contains 0 | +0.000 | +0.006 | +0.013 | – |
| aligned_pretrained | vs local_only (access-matched) | 86 | +0.006 | [-0.004, +0.015] | [-0.007, +0.018] | contains 0 | -0.003 | +0.002 | +0.007 | – |
| aligned_random | vs local_only (access-matched) | 86 | +0.004 | [-0.005, +0.013] | [-0.007, +0.015] | contains 0 | -0.002 | -0.015 | +0.005 | – |
| small_context | vs local_only (access-matched) | 86 | +0.006 | [-0.003, +0.016] | [-0.006, +0.018] | contains 0 | -0.002 | -0.010 | +0.006 | – |
| concat | vs local_only (access-matched) | 86 | +0.002 | [-0.005, +0.009] | [-0.007, +0.011] | contains 0 | +0.002 | +0.000 | +0.000 | – |

## 3. Attribution of the aligned-pretrained gain

**fau · cbramod · L0** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | -0.011 | [-0.026, +0.004] | [-0.030, +0.007] | contains 0 | +0.003 | +0.047 | +0.011 | -0.003 |
| pretrained_vs_capacity | capacity | 67 | +0.007 | [-0.012, +0.026] | [-0.017, +0.031] | contains 0 | +0.005 | +0.090 | +0.002 | -0.003 |
| pretrained_vs_raw_window | beyond the raw window | 67 | +0.008 | [-0.008, +0.024] | [-0.013, +0.029] | contains 0 | +0.001 | +0.050 | +0.017 | -0.002 |
| residual_vs_concat | residual stacking vs joint fit | 67 | -0.005 | [-0.011, -0.000] | [-0.012, +0.001] | contains 0 | +0.001 | -0.008 | +0.003 | -0.001 |

**fau · cbramod · L1** (critical value 2.63)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | +0.005 | [-0.009, +0.019] | [-0.014, +0.023] | contains 0 | +0.001 | +0.008 | +0.003 | +0.001 |
| pretrained_vs_capacity | capacity | 67 | +0.018 | [+0.003, +0.032] | [-0.002, +0.037] | contains 0 | +0.003 | +0.054 | +0.007 | +0.001 |
| pretrained_vs_raw_window | beyond the raw window | 67 | +0.004 | [-0.007, +0.016] | [-0.010, +0.018] | contains 0 | -0.002 | -0.017 | +0.000 | -0.003 |
| residual_vs_concat | residual stacking vs joint fit | 67 | +0.004 | [+0.001, +0.006] | [+0.001, +0.006] | I>0 | +0.001 | +0.001 | +0.005 | +0.001 |

**fau · reve · L0** (critical value 2.59)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | +0.001 | [-0.012, +0.015] | [-0.016, +0.018] | contains 0 | -0.003 | -0.028 | +0.004 | -0.002 |
| pretrained_vs_capacity | capacity | 67 | +0.005 | [-0.012, +0.022] | [-0.017, +0.027] | contains 0 | +0.001 | +0.019 | -0.011 | -0.003 |
| pretrained_vs_raw_window | beyond the raw window | 67 | +0.016 | [+0.002, +0.030] | [-0.002, +0.034] | contains 0 | -0.002 | +0.011 | +0.004 | -0.002 |
| residual_vs_concat | residual stacking vs joint fit | 67 | -0.001 | [-0.004, +0.003] | [-0.005, +0.004] | contains 0 | +0.000 | +0.003 | +0.000 | +0.000 |

**fau · reve · L1** (critical value 2.50)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 67 | +0.002 | [-0.010, +0.013] | [-0.012, +0.015] | contains 0 | -0.004 | -0.025 | -0.006 | -0.003 |
| pretrained_vs_capacity | capacity | 67 | +0.011 | [-0.002, +0.025] | [-0.005, +0.028] | contains 0 | +0.000 | +0.042 | -0.000 | -0.001 |
| pretrained_vs_raw_window | beyond the raw window | 67 | -0.002 | [-0.013, +0.009] | [-0.016, +0.011] | contains 0 | -0.005 | -0.029 | -0.007 | -0.006 |
| residual_vs_concat | residual stacking vs joint fit | 67 | +0.003 | [+0.001, +0.004] | [+0.000, +0.005] | I>0 | +0.000 | +0.003 | +0.003 | -0.000 |

**dtu · cbramod · L0** (critical value 2.57)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | +0.007 | [-0.012, +0.026] | [-0.016, +0.031] | contains 0 | +0.003 | +0.008 | +0.017 | -0.000 |
| pretrained_vs_capacity | capacity | 44 | +0.045 | [+0.024, +0.066] | [+0.017, +0.073] | I>0 | +0.002 | +0.020 | +0.004 | +0.004 |
| pretrained_vs_raw_window | beyond the raw window | 44 | +0.003 | [-0.018, +0.023] | [-0.024, +0.029] | contains 0 | +0.003 | -0.003 | -0.005 | +0.002 |
| residual_vs_concat | residual stacking vs joint fit | 44 | -0.003 | [-0.014, +0.009] | [-0.017, +0.012] | contains 0 | +0.001 | -0.000 | +0.002 | +0.000 |

**dtu · cbramod · L1** (critical value 2.54)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | +0.006 | [-0.011, +0.022] | [-0.015, +0.027] | contains 0 | +0.000 | +0.011 | +0.019 | -0.000 |
| pretrained_vs_capacity | capacity | 44 | +0.008 | [-0.012, +0.029] | [-0.017, +0.034] | contains 0 | +0.004 | -0.043 | +0.021 | +0.000 |
| pretrained_vs_raw_window | beyond the raw window | 44 | -0.012 | [-0.028, +0.004] | [-0.031, +0.008] | contains 0 | -0.001 | -0.018 | -0.008 | -0.000 |
| residual_vs_concat | residual stacking vs joint fit | 44 | +0.013 | [+0.005, +0.021] | [+0.003, +0.022] | I>0 | -0.000 | +0.013 | +0.011 | -0.000 |

**dtu · reve · L0** (critical value 2.51)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | -0.008 | [-0.024, +0.008] | [-0.028, +0.012] | contains 0 | -0.000 | -0.014 | -0.013 | -0.002 |
| pretrained_vs_capacity | capacity | 44 | +0.041 | [+0.015, +0.066] | [+0.009, +0.072] | I>0 | +0.004 | +0.007 | -0.005 | +0.004 |
| pretrained_vs_raw_window | beyond the raw window | 44 | -0.004 | [-0.020, +0.013] | [-0.024, +0.017] | contains 0 | +0.005 | -0.018 | -0.015 | +0.002 |
| residual_vs_concat | residual stacking vs joint fit | 44 | +0.011 | [+0.002, +0.019] | [+0.000, +0.021] | I>0 | +0.002 | +0.011 | +0.014 | +0.002 |

**dtu · reve · L1** (critical value 2.65)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 44 | -0.013 | [-0.030, +0.004] | [-0.036, +0.010] | contains 0 | +0.001 | +0.036 | -0.019 | -0.000 |
| pretrained_vs_capacity | capacity | 44 | +0.008 | [-0.013, +0.029] | [-0.019, +0.036] | contains 0 | +0.005 | +0.008 | +0.011 | -0.001 |
| pretrained_vs_raw_window | beyond the raw window | 44 | -0.011 | [-0.028, +0.005] | [-0.033, +0.011] | contains 0 | -0.001 | +0.033 | -0.019 | -0.003 |
| residual_vs_concat | residual stacking vs joint fit | 44 | +0.034 | [+0.018, +0.050] | [+0.014, +0.053] | I>0 | +0.002 | +0.031 | +0.014 | +0.001 |

**federici · cbramod · L0** (critical value 2.51)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | -0.002 | [-0.013, +0.010] | [-0.016, +0.013] | contains 0 | -0.002 | +0.007 | -0.008 | – |
| pretrained_vs_capacity | capacity | 86 | -0.010 | [-0.023, +0.003] | [-0.027, +0.007] | contains 0 | -0.003 | -0.013 | -0.012 | – |
| pretrained_vs_raw_window | beyond the raw window | 86 | +0.000 | [-0.010, +0.010] | [-0.012, +0.013] | contains 0 | -0.003 | +0.009 | -0.008 | – |
| residual_vs_concat | residual stacking vs joint fit | 86 | -0.002 | [-0.006, +0.003] | [-0.008, +0.004] | contains 0 | -0.002 | -0.004 | -0.002 | – |

**federici · cbramod · L1** (critical value 2.50)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.003 | [-0.008, +0.015] | [-0.011, +0.017] | contains 0 | +0.004 | +0.010 | -0.002 | – |
| pretrained_vs_capacity | capacity | 86 | -0.003 | [-0.014, +0.009] | [-0.017, +0.012] | contains 0 | +0.004 | +0.002 | -0.006 | – |
| pretrained_vs_raw_window | beyond the raw window | 86 | -0.001 | [-0.013, +0.011] | [-0.016, +0.014] | contains 0 | +0.006 | +0.018 | -0.001 | – |
| residual_vs_concat | residual stacking vs joint fit | 86 | +0.005 | [-0.001, +0.012] | [-0.003, +0.013] | contains 0 | +0.004 | +0.004 | +0.005 | – |

**federici · reve · L0** (critical value 2.46)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.004 | [-0.005, +0.013] | [-0.007, +0.015] | contains 0 | -0.001 | +0.010 | +0.003 | – |
| pretrained_vs_capacity | capacity | 86 | -0.008 | [-0.020, +0.003] | [-0.023, +0.006] | contains 0 | -0.001 | -0.015 | -0.002 | – |
| pretrained_vs_raw_window | beyond the raw window | 86 | +0.002 | [-0.006, +0.011] | [-0.009, +0.013] | contains 0 | -0.002 | +0.007 | +0.002 | – |
| residual_vs_concat | residual stacking vs joint fit | 86 | -0.002 | [-0.007, +0.002] | [-0.008, +0.003] | contains 0 | -0.000 | +0.002 | +0.005 | – |

**federici · reve · L1** (critical value 2.48)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_vs_random | pretrained weights | 86 | +0.002 | [-0.009, +0.012] | [-0.011, +0.015] | contains 0 | -0.001 | +0.017 | +0.002 | – |
| pretrained_vs_capacity | capacity | 86 | -0.003 | [-0.016, +0.009] | [-0.019, +0.012] | contains 0 | -0.004 | -0.004 | -0.006 | – |
| pretrained_vs_raw_window | beyond the raw window | 86 | -0.001 | [-0.011, +0.009] | [-0.013, +0.011] | contains 0 | -0.002 | +0.012 | +0.000 | – |
| residual_vs_concat | residual stacking vs joint fit | 86 | +0.004 | [-0.001, +0.009] | [-0.003, +0.010] | contains 0 | -0.006 | +0.002 | +0.006 | – |

## 4. Levels

| configuration | n | R [95% CI] | gain |
|---|---|---|---|
| SC|dtu|NCE|cbramod|L0|aligned_pretrained | 44 | 6.927 [+6.775, +7.079] | +1.897 |
| SC|dtu|NCE|cbramod|L0|aligned_random | 44 | 6.934 [+6.781, +7.088] | +1.889 |
| SC|dtu|NCE|cbramod|L0|concat | 44 | 6.924 [+6.772, +7.077] | +1.898 |
| SC|dtu|NCE|cbramod|L0|local_only | 44 | 6.975 [+6.819, +7.132] | +1.869 |
| SC|dtu|NCE|cbramod|L0|local_refit_capacity | 44 | 6.972 [+6.816, +7.128] | +1.877 |
| SC|dtu|NCE|cbramod|L0|small_context | 44 | 6.930 [+6.784, +7.076] | +1.900 |
| SC|dtu|NCE|cbramod|L1|aligned_pretrained | 44 | 6.986 [+6.848, +7.125] | +1.798 |
| SC|dtu|NCE|cbramod|L1|aligned_random | 44 | 6.992 [+6.859, +7.125] | +1.787 |
| SC|dtu|NCE|cbramod|L1|concat | 44 | 6.999 [+6.862, +7.136] | +1.785 |
| SC|dtu|NCE|cbramod|L1|local_only | 44 | 7.035 [+6.901, +7.170] | +1.769 |
| SC|dtu|NCE|cbramod|L1|local_refit_capacity | 44 | 6.995 [+6.859, +7.130] | +1.841 |
| SC|dtu|NCE|cbramod|L1|small_context | 44 | 6.975 [+6.840, +7.109] | +1.816 |
| SC|dtu|NCE|reve|L0|aligned_pretrained | 44 | 6.932 [+6.773, +7.090] | +1.884 |
| SC|dtu|NCE|reve|L0|aligned_random | 44 | 6.924 [+6.777, +7.070] | +1.898 |
| SC|dtu|NCE|reve|L0|concat | 44 | 6.942 [+6.783, +7.101] | +1.874 |
| SC|dtu|NCE|reve|L0|local_only | 44 | 6.975 [+6.819, +7.132] | +1.869 |
| SC|dtu|NCE|reve|L0|local_refit_capacity | 44 | 6.972 [+6.815, +7.130] | +1.877 |
| SC|dtu|NCE|reve|L0|small_context | 44 | 6.928 [+6.782, +7.074] | +1.902 |
| SC|dtu|NCE|reve|L1|aligned_pretrained | 44 | 6.986 [+6.849, +7.124] | +1.849 |
| SC|dtu|NCE|reve|L1|aligned_random | 44 | 6.973 [+6.841, +7.106] | +1.813 |
| SC|dtu|NCE|reve|L1|concat | 44 | 7.020 [+6.882, +7.158] | +1.818 |
| SC|dtu|NCE|reve|L1|local_only | 44 | 7.035 [+6.903, +7.167] | +1.769 |
| SC|dtu|NCE|reve|L1|local_refit_capacity | 44 | 6.995 [+6.859, +7.130] | +1.841 |
| SC|dtu|NCE|reve|L1|small_context | 44 | 6.975 [+6.839, +7.112] | +1.815 |
| SC|fau|NCE|cbramod|L0|aligned_pretrained | 67 | 6.337 [+6.223, +6.452] | +0.978 |
| SC|fau|NCE|cbramod|L0|aligned_random | 67 | 6.326 [+6.219, +6.434] | +0.931 |
| SC|fau|NCE|cbramod|L0|concat | 67 | 6.332 [+6.212, +6.452] | +0.986 |
| SC|fau|NCE|cbramod|L0|local_only | 67 | 6.344 [+6.241, +6.448] | +0.888 |
| SC|fau|NCE|cbramod|L0|local_refit_capacity | 67 | 6.344 [+6.242, +6.447] | +0.888 |
| SC|fau|NCE|cbramod|L0|small_context | 67 | 6.345 [+6.237, +6.453] | +0.929 |
| SC|fau|NCE|cbramod|L1|aligned_pretrained | 67 | 6.350 [+6.264, +6.436] | +0.753 |
| SC|fau|NCE|cbramod|L1|aligned_random | 67 | 6.355 [+6.264, +6.446] | +0.745 |
| SC|fau|NCE|cbramod|L1|concat | 67 | 6.354 [+6.266, +6.441] | +0.752 |
| SC|fau|NCE|cbramod|L1|local_only | 67 | 6.358 [+6.276, +6.440] | +0.682 |
| SC|fau|NCE|cbramod|L1|local_refit_capacity | 67 | 6.368 [+6.276, +6.459] | +0.699 |
| SC|fau|NCE|cbramod|L1|small_context | 67 | 6.354 [+6.263, +6.446] | +0.770 |
| SC|fau|NCE|reve|L0|aligned_pretrained | 67 | 6.339 [+6.236, +6.443] | +0.907 |
| SC|fau|NCE|reve|L0|aligned_random | 67 | 6.340 [+6.231, +6.449] | +0.935 |
| SC|fau|NCE|reve|L0|concat | 67 | 6.339 [+6.233, +6.444] | +0.904 |
| SC|fau|NCE|reve|L0|local_only | 67 | 6.344 [+6.243, +6.446] | +0.888 |
| SC|fau|NCE|reve|L0|local_refit_capacity | 67 | 6.344 [+6.240, +6.449] | +0.888 |
| SC|fau|NCE|reve|L0|small_context | 67 | 6.355 [+6.249, +6.462] | +0.896 |
| SC|fau|NCE|reve|L1|aligned_pretrained | 67 | 6.356 [+6.265, +6.447] | +0.741 |
| SC|fau|NCE|reve|L1|aligned_random | 67 | 6.358 [+6.266, +6.450] | +0.766 |
| SC|fau|NCE|reve|L1|concat | 67 | 6.359 [+6.271, +6.447] | +0.739 |
| SC|fau|NCE|reve|L1|local_only | 67 | 6.358 [+6.273, +6.443] | +0.682 |
| SC|fau|NCE|reve|L1|local_refit_capacity | 67 | 6.368 [+6.281, +6.454] | +0.699 |
| SC|fau|NCE|reve|L1|small_context | 67 | 6.354 [+6.261, +6.448] | +0.770 |
| SC|federici|NCE|cbramod|L0|aligned_pretrained | 86 | 8.086 [+8.055, +8.117] | +0.202 |
| SC|federici|NCE|cbramod|L0|aligned_random | 86 | 8.084 [+8.055, +8.113] | +0.195 |
| SC|federici|NCE|cbramod|L0|concat | 86 | 8.084 [+8.054, +8.115] | +0.207 |
| SC|federici|NCE|cbramod|L0|local_only | 86 | 8.083 [+8.053, +8.113] | +0.210 |
| SC|federici|NCE|cbramod|L0|local_refit_capacity | 86 | 8.076 [+8.045, +8.107] | +0.215 |
| SC|federici|NCE|cbramod|L0|small_context | 86 | 8.086 [+8.057, +8.115] | +0.193 |
| SC|federici|NCE|cbramod|L1|aligned_pretrained | 86 | 8.022 [+7.980, +8.065] | +0.343 |
| SC|federici|NCE|cbramod|L1|aligned_random | 86 | 8.026 [+7.982, +8.069] | +0.334 |
| SC|federici|NCE|cbramod|L1|concat | 86 | 8.027 [+7.985, +8.070] | +0.340 |
| SC|federici|NCE|cbramod|L1|local_only | 86 | 8.029 [+7.985, +8.072] | +0.335 |
| SC|federici|NCE|cbramod|L1|local_refit_capacity | 86 | 8.020 [+7.976, +8.063] | +0.341 |
| SC|federici|NCE|cbramod|L1|small_context | 86 | 8.021 [+7.980, +8.062] | +0.325 |
| SC|federici|NCE|reve|L0|aligned_pretrained | 86 | 8.084 [+8.055, +8.114] | +0.200 |
| SC|federici|NCE|reve|L0|aligned_random | 86 | 8.088 [+8.059, +8.117] | +0.190 |
| SC|federici|NCE|reve|L0|concat | 86 | 8.082 [+8.053, +8.111] | +0.199 |
| SC|federici|NCE|reve|L0|local_only | 86 | 8.083 [+8.051, +8.114] | +0.210 |
| SC|federici|NCE|reve|L0|local_refit_capacity | 86 | 8.076 [+8.046, +8.106] | +0.215 |
| SC|federici|NCE|reve|L0|small_context | 86 | 8.086 [+8.057, +8.116] | +0.193 |
| SC|federici|NCE|reve|L1|aligned_pretrained | 86 | 8.023 [+7.980, +8.066] | +0.337 |
| SC|federici|NCE|reve|L1|aligned_random | 86 | 8.025 [+7.982, +8.067] | +0.321 |
| SC|federici|NCE|reve|L1|concat | 86 | 8.027 [+7.983, +8.071] | +0.336 |
| SC|federici|NCE|reve|L1|local_only | 86 | 8.029 [+7.985, +8.072] | +0.335 |
| SC|federici|NCE|reve|L1|local_refit_capacity | 86 | 8.020 [+7.976, +8.064] | +0.341 |
| SC|federici|NCE|reve|L1|small_context | 86 | 8.022 [+7.981, +8.063] | +0.325 |

## Appendix: notes

- SC-VALUE|federici|cbramod|L0|sec/local_refit_capacity/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L0|sec/aligned_pretrained/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L0|sec/aligned_random/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L0|sec/small_context/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L0|sec/concat/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L0|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L0|sec/pretrained_vs_capacity/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L0|sec/pretrained_vs_raw_window/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L0|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L1|sec/local_refit_capacity/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L1|sec/aligned_pretrained/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L1|sec/aligned_random/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L1|sec/small_context/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|cbramod|L1|sec/concat/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L1|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L1|sec/pretrained_vs_capacity/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L1|sec/pretrained_vs_raw_window/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|cbramod|L1|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L0|sec/local_refit_capacity/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L0|sec/aligned_pretrained/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L0|sec/aligned_random/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L0|sec/small_context/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L0|sec/concat/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L0|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L0|sec/pretrained_vs_capacity/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L0|sec/pretrained_vs_raw_window/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L0|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L1|sec/local_refit_capacity/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L1|sec/aligned_pretrained/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L1|sec/aligned_random/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L1|sec/small_context/attention/unified/accuracy: no paired identities
- SC-VALUE|federici|reve|L1|sec/concat/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L1|sec/pretrained_vs_random/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L1|sec/pretrained_vs_capacity/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L1|sec/pretrained_vs_raw_window/attention/unified/accuracy: no paired identities
- SC-ATTRIB|federici|reve|L1|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
