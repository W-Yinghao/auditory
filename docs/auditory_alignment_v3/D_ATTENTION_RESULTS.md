# D_ATTENTION results — attended vs ignored 2AFC (lag-local arm)

Generated 2026-10-14 18:22 CEST (Slurm job 1040261) by `python -m auditory_alignment_v3.d_lag_interim` under the frozen `ADDENDUM_12_D_LAG_RESULTS.md`. Seed 3401, `lag_local_tokens`, all folds; identity-level bootstrap-t, simultaneous = max-t within the named family; positive = candidate better. Unit status: {'D_ATTENTION|complete': 100, 'D_COVERAGE|complete': 60, 'D_ADAPT|complete': 120}. QC: {'adapter_none_identical_across_support': True}. Primary: unified readout, mean_score integrator; chance 0.5.

**AT-LEVEL · fau · attended_alignment · NCE** (critical value 2.25)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 67 | +0.052 | [+0.040, +0.064] | [+0.038, +0.066] | I>0 | +0.087 | – | ci: +0.020 (n=24); ha: +0.058 (n=29); th: +0.096 (n=14) |
| 10s | above chance | 67 | +0.075 | [+0.058, +0.091] | [+0.056, +0.093] | I>0 | +0.117 | – | ci: +0.031 (n=24); ha: +0.081 (n=29); th: +0.135 (n=14) |
| 20s | above chance | 67 | +0.102 | [+0.080, +0.124] | [+0.077, +0.127] | I>0 | +0.160 | – | ci: +0.039 (n=24); ha: +0.114 (n=29); th: +0.185 (n=14) |

**AT-INTEGRATOR · fau · attended_alignment · NCE** (critical value 2.46)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 67 | -0.005 | [-0.006, -0.003] | [-0.006, -0.003] | I<0 | +0.008 | – | ci: -0.005 (n=24); ha: -0.004 (n=29); th: -0.005 (n=14) |
| 10s | mean_score -> learned_temporal | 67 | -0.029 | [-0.033, -0.025] | [-0.034, -0.024] | I<0 | +0.019 | – | ci: -0.028 (n=24); ha: -0.029 (n=29); th: -0.030 (n=14) |
| 20s | mean_score -> learned_temporal | 67 | -0.016 | [-0.024, -0.009] | [-0.026, -0.007] | I<0 | -0.362 | – | ci: -0.023 (n=24); ha: -0.015 (n=29); th: -0.009 (n=14) |

**AT-LENGTH · fau · attended_alignment · NCE** (critical value 2.25)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 67 | +0.022 | [+0.015, +0.030] | [+0.014, +0.031] | I>0 | +0.030 | +0.000 | ci: +0.011 (n=24); ha: +0.023 (n=29); th: +0.040 (n=14) |
| 5s->20s | longer window | 67 | +0.050 | [+0.036, +0.063] | [+0.035, +0.065] | I>0 | +0.073 | +0.000 | ci: +0.019 (n=24); ha: +0.056 (n=29); th: +0.089 (n=14) |

**AT-LEVEL · fau · attended_alignment · CS_SINGLE** (critical value 2.33)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 67 | +0.057 | [+0.045, +0.069] | [+0.043, +0.071] | I>0 | +0.064 | – | ci: +0.024 (n=24); ha: +0.068 (n=29); th: +0.089 (n=14) |
| 10s | above chance | 67 | +0.071 | [+0.054, +0.087] | [+0.051, +0.090] | I>0 | +0.089 | – | ci: +0.025 (n=24); ha: +0.086 (n=29); th: +0.118 (n=14) |
| 20s | above chance | 67 | +0.098 | [+0.076, +0.121] | [+0.072, +0.125] | I>0 | +0.144 | – | ci: +0.034 (n=24); ha: +0.123 (n=29); th: +0.157 (n=14) |

**AT-INTEGRATOR · fau · attended_alignment · CS_SINGLE** (critical value 2.42)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 67 | -0.003 | [-0.005, -0.002] | [-0.005, -0.002] | I<0 | -0.075 | – | ci: -0.003 (n=24); ha: -0.004 (n=29); th: -0.003 (n=14) |
| 10s | mean_score -> learned_temporal | 67 | -0.023 | [-0.027, -0.019] | [-0.028, -0.019] | I<0 | -0.089 | – | ci: -0.029 (n=24); ha: -0.021 (n=29); th: -0.020 (n=14) |
| 20s | mean_score -> learned_temporal | 67 | -0.019 | [-0.028, -0.010] | [-0.030, -0.008] | I<0 | -0.644 | – | ci: -0.021 (n=24); ha: -0.019 (n=29); th: -0.016 (n=14) |

**AT-LENGTH · fau · attended_alignment · CS_SINGLE** (critical value 2.27)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 67 | +0.014 | [+0.005, +0.022] | [+0.004, +0.023] | I>0 | +0.025 | +0.000 | ci: +0.000 (n=24); ha: +0.017 (n=29); th: +0.029 (n=14) |
| 5s->20s | longer window | 67 | +0.041 | [+0.027, +0.056] | [+0.025, +0.058] | I>0 | +0.080 | +0.000 | ci: +0.010 (n=24); ha: +0.054 (n=29); th: +0.068 (n=14) |

**AT-LEVEL · fau · selection_only · SELECTION_CE** (critical value 2.24)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 67 | +0.051 | [+0.038, +0.063] | [+0.037, +0.064] | I>0 | +0.088 | – | ci: +0.017 (n=24); ha: +0.058 (n=29); th: +0.093 (n=14) |
| 10s | above chance | 67 | +0.064 | [+0.047, +0.082] | [+0.045, +0.084] | I>0 | +0.129 | – | ci: +0.013 (n=24); ha: +0.078 (n=29); th: +0.125 (n=14) |
| 20s | above chance | 67 | +0.091 | [+0.067, +0.114] | [+0.064, +0.117] | I>0 | +0.193 | – | ci: +0.027 (n=24); ha: +0.108 (n=29); th: +0.164 (n=14) |

**AT-INTEGRATOR · fau · selection_only · SELECTION_CE** (critical value 2.45)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 67 | -0.005 | [-0.007, -0.004] | [-0.007, -0.003] | I<0 | +0.002 | – | ci: -0.006 (n=24); ha: -0.005 (n=29); th: -0.003 (n=14) |
| 10s | mean_score -> learned_temporal | 67 | -0.034 | [-0.038, -0.030] | [-0.039, -0.029] | I<0 | -0.002 | – | ci: -0.033 (n=24); ha: -0.036 (n=29); th: -0.031 (n=14) |
| 20s | mean_score -> learned_temporal | 67 | -0.018 | [-0.025, -0.010] | [-0.027, -0.009] | I<0 | -0.037 | – | ci: -0.015 (n=24); ha: -0.021 (n=29); th: -0.017 (n=14) |

**AT-LENGTH · fau · selection_only · SELECTION_CE** (critical value 2.23)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 67 | +0.014 | [+0.005, +0.022] | [+0.004, +0.024] | I>0 | +0.041 | +0.000 | ci: -0.004 (n=24); ha: +0.019 (n=29); th: +0.032 (n=14) |
| 5s->20s | longer window | 67 | +0.040 | [+0.025, +0.055] | [+0.024, +0.056] | I>0 | +0.105 | +0.000 | ci: +0.010 (n=24); ha: +0.049 (n=29); th: +0.072 (n=14) |

**AT-LEVEL · fau · alignment_plus_selection · NCE** (critical value 2.24)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 67 | +0.054 | [+0.043, +0.065] | [+0.041, +0.067] | I>0 | +0.098 | – | ci: +0.017 (n=24); ha: +0.066 (n=29); th: +0.093 (n=14) |
| 10s | above chance | 67 | +0.080 | [+0.061, +0.098] | [+0.060, +0.100] | I>0 | +0.142 | – | ci: +0.024 (n=24); ha: +0.098 (n=29); th: +0.137 (n=14) |
| 20s | above chance | 67 | +0.101 | [+0.078, +0.124] | [+0.075, +0.127] | I>0 | +0.201 | – | ci: +0.034 (n=24); ha: +0.122 (n=29); th: +0.172 (n=14) |

**AT-INTEGRATOR · fau · alignment_plus_selection · NCE** (critical value 2.50)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 67 | -0.003 | [-0.005, -0.002] | [-0.005, -0.002] | I<0 | +0.005 | – | ci: -0.003 (n=24); ha: -0.003 (n=29); th: -0.004 (n=14) |
| 10s | mean_score -> learned_temporal | 67 | -0.025 | [-0.030, -0.021] | [-0.031, -0.020] | I<0 | +0.011 | – | ci: -0.031 (n=24); ha: -0.023 (n=29); th: -0.021 (n=14) |
| 20s | mean_score -> learned_temporal | 67 | -0.019 | [-0.026, -0.012] | [-0.028, -0.010] | I<0 | -0.227 | – | ci: -0.022 (n=24); ha: -0.018 (n=29); th: -0.015 (n=14) |

**AT-LENGTH · fau · alignment_plus_selection · NCE** (critical value 2.23)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 67 | +0.026 | [+0.017, +0.034] | [+0.016, +0.036] | I>0 | +0.045 | +0.000 | ci: +0.007 (n=24); ha: +0.032 (n=29); th: +0.044 (n=14) |
| 5s->20s | longer window | 67 | +0.047 | [+0.033, +0.061] | [+0.031, +0.063] | I>0 | +0.104 | +0.000 | ci: +0.017 (n=24); ha: +0.056 (n=29); th: +0.079 (n=14) |

**AT-LEVEL · fau · alignment_plus_selection · CS_SINGLE** (critical value 2.29)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 67 | +0.044 | [+0.033, +0.055] | [+0.032, +0.056] | I>0 | +0.051 | – | ci: +0.012 (n=24); ha: +0.052 (n=29); th: +0.081 (n=14) |
| 10s | above chance | 67 | +0.061 | [+0.046, +0.076] | [+0.043, +0.079] | I>0 | +0.072 | – | ci: +0.020 (n=24); ha: +0.071 (n=29); th: +0.110 (n=14) |
| 20s | above chance | 67 | +0.079 | [+0.059, +0.100] | [+0.056, +0.102] | I>0 | +0.127 | – | ci: +0.025 (n=24); ha: +0.094 (n=29); th: +0.141 (n=14) |

**AT-INTEGRATOR · fau · alignment_plus_selection · CS_SINGLE** (critical value 2.50)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 67 | -0.004 | [-0.005, -0.003] | [-0.005, -0.003] | I<0 | -0.107 | – | ci: -0.004 (n=24); ha: -0.004 (n=29); th: -0.004 (n=14) |
| 10s | mean_score -> learned_temporal | 67 | -0.026 | [-0.030, -0.021] | [-0.031, -0.020] | I<0 | -0.072 | – | ci: -0.027 (n=24); ha: -0.026 (n=29); th: -0.021 (n=14) |
| 20s | mean_score -> learned_temporal | 67 | -0.011 | [-0.019, -0.003] | [-0.021, -0.001] | I<0 | -0.627 | – | ci: -0.015 (n=24); ha: -0.009 (n=29); th: -0.008 (n=14) |

**AT-LENGTH · fau · alignment_plus_selection · CS_SINGLE** (critical value 2.25)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 67 | +0.017 | [+0.009, +0.025] | [+0.008, +0.026] | I>0 | +0.021 | +0.000 | ci: +0.007 (n=24); ha: +0.019 (n=29); th: +0.029 (n=14) |
| 5s->20s | longer window | 67 | +0.035 | [+0.022, +0.048] | [+0.020, +0.050] | I>0 | +0.077 | +0.000 | ci: +0.012 (n=24); ha: +0.042 (n=29); th: +0.059 (n=14) |

**AT-TASK · fau · 5s** (critical value 2.43)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 67 | +0.002 | [-0.005, +0.008] | [-0.006, +0.009] | contains 0 | +0.011 | +0.001 | ci: -0.003 (n=24); ha: +0.007 (n=29); th: -0.003 (n=14) |
| align->align+sel CS | task | 67 | -0.013 | [-0.022, -0.004] | [-0.024, -0.002] | I<0 | -0.014 | -0.003 | ci: -0.012 (n=24); ha: -0.016 (n=29); th: -0.008 (n=14) |
| align NCE->selection_only | task | 67 | -0.002 | [-0.010, +0.007] | [-0.012, +0.009] | contains 0 | +0.002 | -0.001 | ci: -0.003 (n=24); ha: -0.000 (n=29); th: -0.003 (n=14) |

**AT-TASK · fau · 10s** (critical value 2.46)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 67 | +0.005 | [-0.004, +0.014] | [-0.006, +0.016] | contains 0 | +0.026 | +0.000 | ci: -0.007 (n=24); ha: +0.017 (n=29); th: +0.002 (n=14) |
| align->align+sel CS | task | 67 | -0.010 | [-0.021, +0.002] | [-0.024, +0.005] | contains 0 | -0.018 | -0.003 | ci: -0.005 (n=24); ha: -0.015 (n=29); th: -0.008 (n=14) |
| align NCE->selection_only | task | 67 | -0.010 | [-0.022, +0.002] | [-0.025, +0.005] | contains 0 | +0.012 | -0.001 | ci: -0.018 (n=24); ha: -0.004 (n=29); th: -0.011 (n=14) |

**AT-TASK · fau · 20s** (critical value 2.44)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 67 | -0.001 | [-0.014, +0.012] | [-0.017, +0.015] | contains 0 | +0.042 | +0.001 | ci: -0.005 (n=24); ha: +0.008 (n=29); th: -0.013 (n=14) |
| align->align+sel CS | task | 67 | -0.019 | [-0.037, -0.001] | [-0.041, +0.003] | contains 0 | -0.016 | -0.003 | ci: -0.010 (n=24); ha: -0.028 (n=29); th: -0.016 (n=14) |
| align NCE->selection_only | task | 67 | -0.011 | [-0.025, +0.003] | [-0.028, +0.006] | contains 0 | +0.033 | -0.001 | ci: -0.012 (n=24); ha: -0.007 (n=29); th: -0.021 (n=14) |

**AT-LEVEL · dtu · attended_alignment · NCE** (critical value 2.33)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 44 | +0.199 | [+0.179, +0.220] | [+0.177, +0.222] | I>0 | +0.221 | – | hi: +0.197 (n=22); nh: +0.201 (n=22) |
| 10s | above chance | 44 | +0.263 | [+0.238, +0.287] | [+0.234, +0.291] | I>0 | +0.286 | – | hi: +0.262 (n=22); nh: +0.263 (n=22) |
| 20s | above chance | 44 | +0.334 | [+0.305, +0.363] | [+0.301, +0.366] | I>0 | +0.366 | – | hi: +0.327 (n=22); nh: +0.340 (n=22) |

**AT-INTEGRATOR · dtu · attended_alignment · NCE** (critical value 2.58)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 44 | -0.005 | [-0.007, -0.004] | [-0.008, -0.003] | I<0 | +0.003 | – | hi: -0.005 (n=22); nh: -0.006 (n=22) |
| 10s | mean_score -> learned_temporal | 44 | +0.004 | [+0.000, +0.008] | [-0.001, +0.009] | contains 0 | +0.044 | – | hi: +0.004 (n=22); nh: +0.004 (n=22) |
| 20s | mean_score -> learned_temporal | 44 | -0.010 | [-0.018, -0.002] | [-0.020, +0.001] | contains 0 | -0.357 | – | hi: -0.007 (n=22); nh: -0.013 (n=22) |

**AT-LENGTH · dtu · attended_alignment · NCE** (critical value 2.37)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 44 | +0.063 | [+0.053, +0.073] | [+0.051, +0.076] | I>0 | +0.065 | -0.000 | hi: +0.065 (n=22); nh: +0.062 (n=22) |
| 5s->20s | longer window | 44 | +0.135 | [+0.121, +0.149] | [+0.120, +0.150] | I>0 | +0.145 | +0.000 | hi: +0.130 (n=22); nh: +0.139 (n=22) |

**AT-LEVEL · dtu · attended_alignment · CS_SINGLE** (critical value 2.30)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 44 | +0.179 | [+0.160, +0.197] | [+0.158, +0.200] | I>0 | +0.194 | – | hi: +0.175 (n=22); nh: +0.183 (n=22) |
| 10s | above chance | 44 | +0.235 | [+0.211, +0.259] | [+0.208, +0.262] | I>0 | +0.257 | – | hi: +0.226 (n=22); nh: +0.244 (n=22) |
| 20s | above chance | 44 | +0.305 | [+0.278, +0.332] | [+0.275, +0.335] | I>0 | +0.326 | – | hi: +0.299 (n=22); nh: +0.311 (n=22) |

**AT-INTEGRATOR · dtu · attended_alignment · CS_SINGLE** (critical value 2.53)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 44 | -0.008 | [-0.010, -0.006] | [-0.010, -0.006] | I<0 | +0.270 | – | hi: -0.008 (n=22); nh: -0.009 (n=22) |
| 10s | mean_score -> learned_temporal | 44 | +0.005 | [+0.002, +0.008] | [+0.001, +0.009] | I>0 | +0.243 | – | hi: +0.006 (n=22); nh: +0.003 (n=22) |
| 20s | mean_score -> learned_temporal | 44 | -0.015 | [-0.025, -0.005] | [-0.027, -0.002] | I<0 | -0.826 | – | hi: -0.024 (n=22); nh: -0.006 (n=22) |

**AT-LENGTH · dtu · attended_alignment · CS_SINGLE** (critical value 2.35)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 44 | +0.056 | [+0.047, +0.065] | [+0.045, +0.067] | I>0 | +0.063 | +0.000 | hi: +0.051 (n=22); nh: +0.061 (n=22) |
| 5s->20s | longer window | 44 | +0.126 | [+0.113, +0.140] | [+0.111, +0.142] | I>0 | +0.131 | +0.001 | hi: +0.124 (n=22); nh: +0.128 (n=22) |

**AT-LEVEL · dtu · selection_only · SELECTION_CE** (critical value 2.25)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 44 | +0.177 | [+0.159, +0.196] | [+0.156, +0.198] | I>0 | +0.195 | – | hi: +0.174 (n=22); nh: +0.181 (n=22) |
| 10s | above chance | 44 | +0.246 | [+0.221, +0.271] | [+0.218, +0.274] | I>0 | +0.257 | – | hi: +0.246 (n=22); nh: +0.246 (n=22) |
| 20s | above chance | 44 | +0.315 | [+0.288, +0.342] | [+0.285, +0.344] | I>0 | +0.329 | – | hi: +0.304 (n=22); nh: +0.325 (n=22) |

**AT-INTEGRATOR · dtu · selection_only · SELECTION_CE** (critical value 2.48)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 44 | -0.008 | [-0.010, -0.006] | [-0.010, -0.005] | I<0 | +0.000 | – | hi: -0.007 (n=22); nh: -0.009 (n=22) |
| 10s | mean_score -> learned_temporal | 44 | +0.005 | [+0.001, +0.009] | [-0.000, +0.010] | contains 0 | +0.012 | – | hi: +0.003 (n=22); nh: +0.007 (n=22) |
| 20s | mean_score -> learned_temporal | 44 | -0.013 | [-0.021, -0.004] | [-0.023, -0.002] | I<0 | -0.037 | – | hi: -0.010 (n=22); nh: -0.016 (n=22) |

**AT-LENGTH · dtu · selection_only · SELECTION_CE** (critical value 2.36)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 44 | +0.069 | [+0.058, +0.080] | [+0.056, +0.081] | I>0 | +0.062 | -0.000 | hi: +0.072 (n=22); nh: +0.065 (n=22) |
| 5s->20s | longer window | 44 | +0.138 | [+0.126, +0.149] | [+0.124, +0.151] | I>0 | +0.134 | +0.000 | hi: +0.131 (n=22); nh: +0.144 (n=22) |

**AT-LEVEL · dtu · alignment_plus_selection · NCE** (critical value 2.31)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 44 | +0.198 | [+0.179, +0.217] | [+0.176, +0.220] | I>0 | +0.221 | – | hi: +0.192 (n=22); nh: +0.204 (n=22) |
| 10s | above chance | 44 | +0.258 | [+0.233, +0.283] | [+0.230, +0.286] | I>0 | +0.287 | – | hi: +0.252 (n=22); nh: +0.264 (n=22) |
| 20s | above chance | 44 | +0.334 | [+0.305, +0.362] | [+0.302, +0.365] | I>0 | +0.363 | – | hi: +0.324 (n=22); nh: +0.343 (n=22) |

**AT-INTEGRATOR · dtu · alignment_plus_selection · NCE** (critical value 2.54)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 44 | -0.006 | [-0.008, -0.003] | [-0.008, -0.003] | I<0 | +0.004 | – | hi: -0.005 (n=22); nh: -0.006 (n=22) |
| 10s | mean_score -> learned_temporal | 44 | +0.001 | [-0.002, +0.004] | [-0.003, +0.005] | contains 0 | +0.028 | – | hi: -0.002 (n=22); nh: +0.003 (n=22) |
| 20s | mean_score -> learned_temporal | 44 | -0.020 | [-0.030, -0.011] | [-0.033, -0.008] | I<0 | -0.176 | – | hi: -0.018 (n=22); nh: -0.023 (n=22) |

**AT-LENGTH · dtu · alignment_plus_selection · NCE** (critical value 2.26)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 44 | +0.060 | [+0.050, +0.070] | [+0.049, +0.071] | I>0 | +0.066 | -0.000 | hi: +0.060 (n=22); nh: +0.060 (n=22) |
| 5s->20s | longer window | 44 | +0.136 | [+0.122, +0.149] | [+0.120, +0.151] | I>0 | +0.142 | +0.000 | hi: +0.132 (n=22); nh: +0.140 (n=22) |

**AT-LEVEL · dtu · alignment_plus_selection · CS_SINGLE** (critical value 2.21)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | above chance | 44 | +0.186 | [+0.169, +0.203] | [+0.168, +0.205] | I>0 | +0.197 | – | hi: +0.179 (n=22); nh: +0.194 (n=22) |
| 10s | above chance | 44 | +0.243 | [+0.221, +0.265] | [+0.218, +0.268] | I>0 | +0.274 | – | hi: +0.239 (n=22); nh: +0.247 (n=22) |
| 20s | above chance | 44 | +0.320 | [+0.293, +0.347] | [+0.290, +0.350] | I>0 | +0.352 | – | hi: +0.317 (n=22); nh: +0.323 (n=22) |

**AT-INTEGRATOR · dtu · alignment_plus_selection · CS_SINGLE** (critical value 2.63)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s | mean_score -> learned_temporal | 44 | -0.005 | [-0.008, -0.002] | [-0.008, -0.002] | I<0 | +0.268 | – | hi: -0.004 (n=22); nh: -0.006 (n=22) |
| 10s | mean_score -> learned_temporal | 44 | +0.002 | [-0.001, +0.004] | [-0.002, +0.005] | contains 0 | +0.226 | – | hi: +0.000 (n=22); nh: +0.003 (n=22) |
| 20s | mean_score -> learned_temporal | 44 | -0.018 | [-0.028, -0.009] | [-0.030, -0.006] | I<0 | -0.852 | – | hi: -0.014 (n=22); nh: -0.022 (n=22) |

**AT-LENGTH · dtu · alignment_plus_selection · CS_SINGLE** (critical value 2.26)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| 5s->10s | longer window | 44 | +0.057 | [+0.048, +0.065] | [+0.047, +0.067] | I>0 | +0.077 | -0.000 | hi: +0.060 (n=22); nh: +0.053 (n=22) |
| 5s->20s | longer window | 44 | +0.134 | [+0.120, +0.147] | [+0.119, +0.148] | I>0 | +0.155 | +0.000 | hi: +0.138 (n=22); nh: +0.129 (n=22) |

**AT-TASK · dtu · 5s** (critical value 2.52)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 44 | -0.001 | [-0.009, +0.006] | [-0.010, +0.008] | contains 0 | +0.000 | -0.000 | hi: -0.005 (n=22); nh: +0.002 (n=22) |
| align->align+sel CS | task | 44 | +0.008 | [-0.002, +0.017] | [-0.004, +0.019] | contains 0 | +0.002 | +0.001 | hi: +0.004 (n=22); nh: +0.011 (n=22) |
| align NCE->selection_only | task | 44 | -0.022 | [-0.032, -0.013] | [-0.034, -0.010] | I<0 | -0.026 | -0.004 | hi: -0.024 (n=22); nh: -0.020 (n=22) |

**AT-TASK · dtu · 10s** (critical value 2.45)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 44 | -0.005 | [-0.014, +0.005] | [-0.016, +0.006] | contains 0 | +0.001 | -0.000 | hi: -0.010 (n=22); nh: +0.001 (n=22) |
| align->align+sel CS | task | 44 | +0.008 | [-0.004, +0.021] | [-0.007, +0.024] | contains 0 | +0.016 | +0.001 | hi: +0.014 (n=22); nh: +0.003 (n=22) |
| align NCE->selection_only | task | 44 | -0.017 | [-0.029, -0.004] | [-0.032, -0.002] | I<0 | -0.029 | -0.004 | hi: -0.016 (n=22); nh: -0.017 (n=22) |

**AT-TASK · dtu · 20s** (critical value 2.48)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δacc native | Δmargin | per group |
|---|---|---|---|---|---|---|---|---|---|
| align->align+sel NCE | task | 44 | -0.000 | [-0.012, +0.011] | [-0.014, +0.013] | contains 0 | -0.002 | -0.000 | hi: -0.003 (n=22); nh: +0.003 (n=22) |
| align->align+sel CS | task | 44 | +0.015 | [-0.001, +0.031] | [-0.004, +0.034] | contains 0 | +0.026 | +0.001 | hi: +0.018 (n=22); nh: +0.012 (n=22) |
| align NCE->selection_only | task | 44 | -0.019 | [-0.034, -0.005] | [-0.037, -0.002] | I<0 | -0.036 | -0.004 | hi: -0.023 (n=22); nh: -0.016 (n=22) |
