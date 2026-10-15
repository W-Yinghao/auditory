# D_COVERAGE matrix — training population and sampling budget (FAU, lag-local arm)

Generated 2026-10-14 18:22 CEST (Slurm job 1040261) by `python -m auditory_alignment_v3.d_lag_interim` under the frozen `ADDENDUM_12_D_LAG_RESULTS.md`. Seed 3401, `lag_local_tokens`, all folds; identity-level bootstrap-t, simultaneous = max-t within the named family; positive = candidate better. Unit status: {'D_ATTENTION|complete': 100, 'D_COVERAGE|complete': 60, 'D_ADAPT|complete': 120}. QC: {'adapter_none_identical_across_support': True}. Primary: unified true-query risk R (positive Δ = lower risk); matched_exposure separates the population change from the update count.

## Levels: training population × control × test group (R, bits; lower is better)

| configuration | n | R [95% CI] | per test group (mean R) |
|---|---|---|---|
| CV|fau|CS_SINGLE|TH_HA_CI|full_available | 67 | 6.358 [6.278, 6.438] | ci: 6.595 (n=24); ha: 6.209 (n=29); th: 6.261 (n=14) |
| CV|fau|CS_SINGLE|TH_HA_CI|matched_exposure | 67 | 6.378 [6.301, 6.455] | ci: 6.609 (n=24); ha: 6.235 (n=29); th: 6.280 (n=14) |
| CV|fau|CS_SINGLE|TH_HA|full_available | 67 | 6.435 [6.327, 6.544] | ci: 6.795 (n=24); ha: 6.196 (n=29); th: 6.314 (n=14) |
| CV|fau|CS_SINGLE|TH_HA|matched_exposure | 67 | 6.434 [6.321, 6.547] | ci: 6.798 (n=24); ha: 6.205 (n=29); th: 6.282 (n=14) |
| CV|fau|CS_SINGLE|TH_ONLY|full_available | 67 | 6.495 [6.415, 6.575] | ci: 6.736 (n=24); ha: 6.374 (n=29); th: 6.333 (n=14) |
| CV|fau|CS_SINGLE|TH_ONLY|matched_exposure | 67 | 6.510 [6.435, 6.584] | ci: 6.742 (n=24); ha: 6.395 (n=29); th: 6.349 (n=14) |
| CV|fau|NCE|TH_HA_CI|full_available | 67 | 6.309 [6.187, 6.430] | ci: 6.692 (n=24); ha: 6.056 (n=29); th: 6.174 (n=14) |
| CV|fau|NCE|TH_HA_CI|matched_exposure | 67 | 6.297 [6.176, 6.419] | ci: 6.664 (n=24); ha: 6.058 (n=29); th: 6.163 (n=14) |
| CV|fau|NCE|TH_HA|full_available | 67 | 6.353 [6.217, 6.489] | ci: 6.810 (n=24); ha: 6.068 (n=29); th: 6.162 (n=14) |
| CV|fau|NCE|TH_HA|matched_exposure | 67 | 6.335 [6.201, 6.469] | ci: 6.783 (n=24); ha: 6.056 (n=29); th: 6.143 (n=14) |
| CV|fau|NCE|TH_ONLY|full_available | 67 | 6.514 [6.389, 6.639] | ci: 6.923 (n=24); ha: 6.312 (n=29); th: 6.232 (n=14) |
| CV|fau|NCE|TH_ONLY|matched_exposure | 67 | 6.524 [6.398, 6.650] | ci: 6.946 (n=24); ha: 6.316 (n=29); th: 6.232 (n=14) |

**CV-POP · NCE · full_available** (critical value 2.35)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY->TH_HA | add HA | 67 | +0.161 | [+0.109, +0.213] | [+0.099, +0.223] | I>0 | +0.192 | +0.015 | ci: +0.113 (n=24); ha: +0.244 (n=29); th: +0.070 (n=14) |
| TH_HA->TH_HA_CI | add CI | 67 | +0.045 | [+0.007, +0.082] | [-0.000, +0.090] | contains 0 | +0.025 | -0.002 | ci: +0.117 (n=24); ha: +0.012 (n=29); th: -0.012 (n=14) |
| TH_ONLY->TH_HA_CI | add HA and CI | 67 | +0.205 | [+0.140, +0.271] | [+0.127, +0.284] | I>0 | +0.217 | +0.013 | ci: +0.230 (n=24); ha: +0.256 (n=29); th: +0.058 (n=14) |

**CV-POP · NCE · matched_exposure** (critical value 2.37)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY->TH_HA | add HA | 67 | +0.189 | [+0.139, +0.240] | [+0.129, +0.250] | I>0 | +0.182 | +0.016 | ci: +0.163 (n=24); ha: +0.260 (n=29); th: +0.089 (n=14) |
| TH_HA->TH_HA_CI | add CI | 67 | +0.037 | [-0.002, +0.077] | [-0.009, +0.084] | contains 0 | +0.044 | +0.003 | ci: +0.119 (n=24); ha: -0.002 (n=29); th: -0.020 (n=14) |
| TH_ONLY->TH_HA_CI | add HA and CI | 67 | +0.227 | [+0.160, +0.293] | [+0.148, +0.306] | I>0 | +0.226 | +0.018 | ci: +0.282 (n=24); ha: +0.257 (n=29); th: +0.069 (n=14) |

**CV-BUDGET · NCE** (critical value 2.50)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY | full -> matched exposure | 67 | -0.010 | [-0.024, +0.004] | [-0.027, +0.008] | contains 0 | -0.008 | -0.002 | ci: -0.023 (n=24); ha: -0.004 (n=29); th: +0.000 (n=14) |
| TH_HA | full -> matched exposure | 67 | +0.019 | [+0.000, +0.037] | [-0.004, +0.041] | contains 0 | -0.018 | -0.001 | ci: +0.027 (n=24); ha: +0.012 (n=29); th: +0.019 (n=14) |
| TH_HA_CI | full -> matched exposure | 67 | +0.011 | [-0.008, +0.031] | [-0.013, +0.036] | contains 0 | +0.001 | +0.003 | ci: +0.029 (n=24); ha: -0.002 (n=29); th: +0.010 (n=14) |

**CV-POP · CS_SINGLE · full_available** (critical value 2.39)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY->TH_HA | add HA | 67 | +0.060 | [+0.009, +0.111] | [-0.002, +0.122] | contains 0 | +0.279 | +0.012 | ci: -0.059 (n=24); ha: +0.178 (n=29); th: +0.019 (n=14) |
| TH_HA->TH_HA_CI | add CI | 67 | +0.077 | [+0.034, +0.121] | [+0.026, +0.128] | I>0 | -0.103 | -0.001 | ci: +0.200 (n=24); ha: -0.012 (n=29); th: +0.053 (n=14) |
| TH_ONLY->TH_HA_CI | add HA and CI | 67 | +0.137 | [+0.098, +0.177] | [+0.089, +0.185] | I>0 | +0.176 | +0.010 | ci: +0.141 (n=24); ha: +0.165 (n=29); th: +0.072 (n=14) |

**CV-POP · CS_SINGLE · matched_exposure** (critical value 2.40)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY->TH_HA | add HA | 67 | +0.076 | [+0.019, +0.133] | [+0.009, +0.143] | I>0 | +0.324 | +0.015 | ci: -0.056 (n=24); ha: +0.190 (n=29); th: +0.067 (n=14) |
| TH_HA->TH_HA_CI | add CI | 67 | +0.056 | [+0.011, +0.101] | [+0.003, +0.109] | I>0 | -0.162 | -0.001 | ci: +0.189 (n=24); ha: -0.029 (n=29); th: +0.002 (n=14) |
| TH_ONLY->TH_HA_CI | add HA and CI | 67 | +0.132 | [+0.094, +0.169] | [+0.086, +0.177] | I>0 | +0.162 | +0.013 | ci: +0.133 (n=24); ha: +0.161 (n=29); th: +0.069 (n=14) |

**CV-BUDGET · CS_SINGLE** (critical value 2.44)

| member | label | n | Δ | 95% CI | 95% simultaneous | class | Δgain | Δtop1 | per group |
|---|---|---|---|---|---|---|---|---|---|
| TH_ONLY | full -> matched exposure | 67 | -0.015 | [-0.030, +0.000] | [-0.033, +0.004] | contains 0 | -0.010 | -0.005 | ci: -0.006 (n=24); ha: -0.021 (n=29); th: -0.016 (n=14) |
| TH_HA | full -> matched exposure | 67 | +0.001 | [-0.019, +0.021] | [-0.023, +0.026] | contains 0 | +0.035 | -0.002 | ci: -0.004 (n=24); ha: -0.009 (n=29); th: +0.031 (n=14) |
| TH_HA_CI | full -> matched exposure | 67 | -0.020 | [-0.035, -0.005] | [-0.039, -0.002] | I<0 | -0.023 | -0.002 | ci: -0.014 (n=24); ha: -0.026 (n=29); th: -0.020 (n=14) |
