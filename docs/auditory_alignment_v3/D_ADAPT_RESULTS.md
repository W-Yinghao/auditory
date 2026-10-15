# D_ADAPT results — personal supervised adaptation (lag-local arm)

Generated 2026-10-14 18:22 CEST (Slurm job 1040261) by `python -m auditory_alignment_v3.d_lag_interim` under the frozen `ADDENDUM_12_D_LAG_RESULTS.md`. Seed 3401, `lag_local_tokens`, all folds; identity-level bootstrap-t, simultaneous = max-t within the named family; positive = candidate better. Unit status: {'D_ATTENTION|complete': 100, 'D_COVERAGE|complete': 60, 'D_ADAPT|complete': 120}. QC: {'adapter_none_identical_across_support': True}. Primary: unified gain_bits on the fixed query set (last 70 %); support blocks use known-stimulus supervision (not label-free TTA); same session.

**AD-GAIN · fau · NCE · 0.1** (critical value 2.38)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 67 | +0.084 | [+0.000, +0.167] | [-0.011, +0.178] | contains 0 | +0.014 | +0.010 | +0.292 | ci: +0.245 (n=24); ha: +0.004 (n=29); th: -0.028 (n=14) |
| output_low_rank | personal supervised adaptation | 67 | +0.040 | [+0.007, +0.072] | [+0.001, +0.078] | I>0 | +0.012 | +0.003 | +0.073 | ci: +0.101 (n=24); ha: +0.011 (n=29); th: -0.006 (n=14) |

**AD-GAIN · fau · NCE · 0.3** (critical value 2.57)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 67 | +0.246 | [+0.151, +0.340] | [+0.137, +0.354] | I>0 | +0.039 | +0.027 | +0.517 | ci: +0.451 (n=24); ha: +0.149 (n=29); th: +0.095 (n=14) |
| output_low_rank | personal supervised adaptation | 67 | +0.087 | [+0.049, +0.125] | [+0.040, +0.134] | I>0 | +0.019 | +0.008 | +0.066 | ci: +0.157 (n=24); ha: +0.060 (n=29); th: +0.023 (n=14) |

**AD-SUPPORT · fau · NCE** (critical value 2.32)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | support 0.1 -> 0.3 | 67 | +0.162 | [+0.127, +0.197] | [+0.121, +0.203] | I>0 | +0.025 | +0.018 | +0.225 | ci: +0.207 (n=24); ha: +0.144 (n=29); th: +0.122 (n=14) |
| output_low_rank | support 0.1 -> 0.3 | 67 | +0.047 | [+0.026, +0.069] | [+0.023, +0.071] | I>0 | +0.007 | +0.006 | -0.007 | ci: +0.056 (n=24); ha: +0.049 (n=29); th: +0.029 (n=14) |

**AD-GAIN · fau · CS_SINGLE · 0.1** (critical value 2.26)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 67 | +0.001 | [-0.019, +0.021] | [-0.022, +0.024] | contains 0 | +0.000 | +0.002 | +0.009 | ci: +0.024 (n=24); ha: -0.016 (n=29); th: -0.001 (n=14) |
| output_low_rank | personal supervised adaptation | 67 | +0.001 | [+0.001, +0.002] | [+0.001, +0.002] | I>0 | +0.000 | -0.000 | -0.001 | ci: +0.001 (n=24); ha: +0.002 (n=29); th: +0.002 (n=14) |

**AD-GAIN · fau · CS_SINGLE · 0.3** (critical value 2.33)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 67 | +0.042 | [+0.020, +0.064] | [+0.017, +0.067] | I>0 | +0.008 | +0.007 | +0.057 | ci: +0.047 (n=24); ha: +0.026 (n=29); th: +0.065 (n=14) |
| output_low_rank | personal supervised adaptation | 67 | +0.001 | [+0.001, +0.001] | [+0.001, +0.001] | I>0 | +0.000 | +0.000 | +0.000 | ci: +0.001 (n=24); ha: +0.001 (n=29); th: +0.000 (n=14) |

**AD-SUPPORT · fau · CS_SINGLE** (critical value 2.22)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | support 0.1 -> 0.3 | 67 | +0.041 | [+0.021, +0.061] | [+0.018, +0.063] | I>0 | +0.008 | +0.005 | +0.048 | ci: +0.023 (n=24); ha: +0.043 (n=29); th: +0.066 (n=14) |
| output_low_rank | support 0.1 -> 0.3 | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | +0.000 | +0.000 | +0.001 | ci: +0.000 (n=24); ha: -0.000 (n=29); th: -0.001 (n=14) |

**AD-GAIN · dtu · NCE · 0.1** (critical value 2.38)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 44 | -0.154 | [-0.267, -0.040] | [-0.285, -0.023] | I<0 | -0.024 | -0.002 | +0.229 | hi: -0.151 (n=22); nh: -0.157 (n=22) |
| output_low_rank | personal supervised adaptation | 44 | +0.023 | [+0.007, +0.038] | [+0.005, +0.040] | I>0 | +0.004 | +0.003 | -0.036 | hi: +0.021 (n=22); nh: +0.025 (n=22) |

**AD-GAIN · dtu · NCE · 0.3** (critical value 2.35)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 44 | +0.237 | [+0.138, +0.336] | [+0.122, +0.352] | I>0 | +0.017 | +0.019 | +0.773 | hi: +0.298 (n=22); nh: +0.176 (n=22) |
| output_low_rank | personal supervised adaptation | 44 | +0.042 | [+0.023, +0.061] | [+0.021, +0.063] | I>0 | +0.008 | +0.009 | -0.164 | hi: +0.042 (n=22); nh: +0.042 (n=22) |

**AD-SUPPORT · dtu · NCE** (critical value 2.38)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | support 0.1 -> 0.3 | 44 | +0.391 | [+0.304, +0.478] | [+0.290, +0.492] | I>0 | +0.041 | +0.020 | +0.544 | hi: +0.449 (n=22); nh: +0.333 (n=22) |
| output_low_rank | support 0.1 -> 0.3 | 44 | +0.020 | [+0.000, +0.039] | [-0.003, +0.042] | contains 0 | +0.004 | +0.006 | -0.129 | hi: +0.022 (n=22); nh: +0.018 (n=22) |

**AD-GAIN · dtu · CS_SINGLE · 0.1** (critical value 2.51)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 44 | -0.130 | [-0.214, -0.046] | [-0.233, -0.027] | I<0 | -0.023 | -0.006 | -0.089 | hi: -0.128 (n=22); nh: -0.133 (n=22) |
| output_low_rank | personal supervised adaptation | 44 | +0.006 | [+0.002, +0.011] | [+0.001, +0.012] | I>0 | +0.001 | -0.000 | -0.005 | hi: +0.006 (n=22); nh: +0.006 (n=22) |

**AD-GAIN · dtu · CS_SINGLE · 0.3** (critical value 2.50)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | personal supervised adaptation | 44 | +0.019 | [-0.054, +0.091] | [-0.071, +0.108] | contains 0 | -0.002 | +0.003 | +0.056 | hi: +0.039 (n=22); nh: -0.002 (n=22) |
| output_low_rank | personal supervised adaptation | 44 | +0.005 | [+0.001, +0.010] | [+0.000, +0.010] | I>0 | +0.001 | -0.000 | -0.002 | hi: +0.007 (n=22); nh: +0.003 (n=22) |

**AD-SUPPORT · dtu · CS_SINGLE** (critical value 2.32)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δrank% (lower better) | Δtop1 | Δgain native | per group |
|---|---|---|---|---|---|---|---|---|---|---|
| input_spatial | support 0.1 -> 0.3 | 44 | +0.149 | [+0.086, +0.212] | [+0.077, +0.221] | I>0 | +0.021 | +0.010 | +0.144 | hi: +0.168 (n=22); nh: +0.130 (n=22) |
| output_low_rank | support 0.1 -> 0.3 | 44 | -0.001 | [-0.004, +0.002] | [-0.004, +0.002] | contains 0 | -0.000 | -0.000 | +0.003 | hi: +0.001 (n=22); nh: -0.003 (n=22) |
