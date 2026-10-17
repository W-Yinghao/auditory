# ALN3.2 wave 1 — aligned interface controls and true full updates (seed 3401, NCE)

Generated 2026-10-16 08:13 CEST (Slurm job 1042577) by `python -m auditory_alignment_v3.aln32_interim` under the frozen `ADDENDUM_07_ALN32_SUPPORT_AND_TRUE_FULL.md` §5 (ADDENDUM_05 machinery). Identity-level bootstrap-t intervals conditional on the seed-3401 training; simultaneous = max-t within the named family. Positive = candidate lower true-query risk (ΔR = R(reference) − R(candidate), bits per 5 s query, unified readout). B_ALIGNED / B_DENSE `pretrained_full − random_full` are recipe contrasts (CORRECTION_01); TF-INIT is the matched initialization contrast. The aligned interface changes window, context and head together; no result here is a pure phase effect.

Code sha256: `aln32_interim.py` 15b30b0dbd26, `bc_interim.py` 2840df81b608, `sci_r1/stats.py` 8bb141cf6070.

Coverage: {'L0|complete': 25, 'A|complete': 250, 'L1|complete': 25, 'R1|complete': 25, 'R0|complete': 25, 'T|complete': 400, 'F2|complete': 100}. Excluded pairs: 0.

## 1. Levels (unified readout)

**fau**

| configuration | n | R [95% CI] | top1 | gain | R_native |
|---|---|---|---|---|---|
| A|fau|NCE|cbramod|pretrained_frozen | 67 | 6.462 [+6.404, +6.521] | 0.042 | 0.486 | 6.418 |
| A|fau|NCE|cbramod|pretrained_full | 67 | 6.349 [+6.268, +6.430] | 0.054 | 0.699 | 6.253 |
| A|fau|NCE|cbramod|pretrained_partial | 67 | 6.421 [+6.355, +6.486] | 0.044 | 0.577 | 6.359 |
| A|fau|NCE|cbramod|pretrained_peft | 67 | 6.336 [+6.253, +6.419] | 0.057 | 0.716 | 6.231 |
| A|fau|NCE|cbramod|random_full | 67 | 6.412 [+6.335, +6.489] | 0.048 | 0.671 | 6.220 |
| A|fau|NCE|reve|pretrained_frozen | 67 | 6.315 [+6.233, +6.397] | 0.057 | 0.760 | 6.135 |
| A|fau|NCE|reve|pretrained_full | 67 | 6.310 [+6.223, +6.397] | 0.056 | 0.796 | 6.124 |
| A|fau|NCE|reve|pretrained_partial | 67 | 6.310 [+6.222, +6.398] | 0.055 | 0.795 | 6.125 |
| A|fau|NCE|reve|pretrained_peft | 67 | 6.282 [+6.177, +6.388] | 0.060 | 0.942 | 6.063 |
| A|fau|NCE|reve|random_full | 67 | 6.270 [+6.151, +6.388] | 0.067 | 1.048 | 6.007 |
| F2|fau|NCE|cbramod|pretrained_frozen | 67 | 6.489 [+6.437, +6.542] | 0.040 | 0.428 | 6.464 |
| F2|fau|NCE|cbramod|pretrained_peft | 67 | 6.344 [+6.258, +6.429] | 0.057 | 0.742 | 6.178 |
| F2|fau|NCE|reve|pretrained_frozen | 67 | 6.310 [+6.222, +6.399] | 0.061 | 0.899 | 6.080 |
| F2|fau|NCE|reve|pretrained_peft | 67 | 6.261 [+6.158, +6.364] | 0.066 | 1.012 | 6.017 |
| L0|fau|NCE | 67 | 6.309 [+6.186, +6.431] | 0.066 | 1.044 | 6.004 |
| L1|fau|NCE | 67 | 6.344 [+6.248, +6.440] | 0.057 | 0.823 | 6.087 |
| R0|fau|NCE | 67 | 6.456 [+6.387, +6.524] | 0.043 | 0.538 | 6.546 |
| R1|fau|NCE | 67 | 6.501 [+6.448, +6.554] | 0.038 | 0.403 | 6.598 |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | 67 | 6.200 [+6.078, +6.321] | 0.074 | 1.136 | 5.917 |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | 67 | 6.217 [+6.091, +6.342] | 0.072 | 1.126 | 5.980 |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | 67 | 6.202 [+6.078, +6.327] | 0.074 | 1.143 | 5.905 |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | 67 | 6.212 [+6.094, +6.330] | 0.072 | 1.130 | 5.978 |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|0.0003 | 67 | 6.319 [+6.210, +6.428] | 0.061 | 0.964 | 6.023 |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|1e-05 | 67 | 6.349 [+6.265, +6.433] | 0.055 | 0.740 | 6.192 |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | 67 | 6.301 [+6.192, +6.411] | 0.064 | 0.986 | 6.010 |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | 67 | 6.354 [+6.271, +6.438] | 0.052 | 0.731 | 6.197 |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | 67 | 6.286 [+6.167, +6.405] | 0.068 | 1.071 | 5.965 |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | 67 | 6.235 [+6.118, +6.351] | 0.072 | 1.150 | 5.974 |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | 67 | 6.386 [+6.283, +6.490] | 0.053 | 0.945 | 6.103 |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | 67 | 6.261 [+6.148, +6.375] | 0.067 | 1.124 | 6.003 |
| T|fau|NCE|reve|random_full|full_onestep_v1|0.0003 | 67 | 6.263 [+6.161, +6.365] | 0.067 | 0.938 | 6.058 |
| T|fau|NCE|reve|random_full|full_onestep_v1|1e-05 | 67 | 6.245 [+6.121, +6.368] | 0.071 | 1.107 | 5.987 |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|0.0003 | 67 | 6.261 [+6.149, +6.372] | 0.067 | 1.008 | 6.032 |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|1e-05 | 67 | 6.252 [+6.129, +6.375] | 0.071 | 1.101 | 6.011 |

**dtu**

| configuration | n | R [95% CI] | top1 | gain | R_native |
|---|---|---|---|---|---|
| A|dtu|NCE|cbramod|pretrained_frozen | 44 | 7.245 [+7.149, +7.341] | 0.037 | 1.132 | 7.080 |
| A|dtu|NCE|cbramod|pretrained_full | 44 | 7.143 [+7.036, +7.250] | 0.042 | 1.352 | 6.902 |
| A|dtu|NCE|cbramod|pretrained_partial | 44 | 7.186 [+7.090, +7.282] | 0.036 | 1.210 | 6.996 |
| A|dtu|NCE|cbramod|pretrained_peft | 44 | 7.178 [+7.066, +7.290] | 0.043 | 1.317 | 6.942 |
| A|dtu|NCE|cbramod|random_full | 44 | 7.313 [+7.220, +7.406] | 0.033 | 1.084 | 7.028 |
| A|dtu|NCE|reve|pretrained_frozen | 44 | 7.145 [+7.023, +7.267] | 0.043 | 1.465 | 6.816 |
| A|dtu|NCE|reve|pretrained_full | 44 | 7.136 [+7.013, +7.259] | 0.042 | 1.475 | 6.816 |
| A|dtu|NCE|reve|pretrained_partial | 44 | 7.137 [+7.017, +7.256] | 0.042 | 1.474 | 6.816 |
| A|dtu|NCE|reve|pretrained_peft | 44 | 7.101 [+6.983, +7.218] | 0.045 | 1.469 | 6.767 |
| A|dtu|NCE|reve|random_full | 44 | 6.859 [+6.702, +7.017] | 0.061 | 1.974 | 6.401 |
| F2|dtu|NCE|cbramod|pretrained_frozen | 44 | 7.224 [+7.131, +7.318] | 0.039 | 1.170 | 7.017 |
| F2|dtu|NCE|cbramod|pretrained_peft | 44 | 7.164 [+7.051, +7.276] | 0.045 | 1.341 | 6.878 |
| F2|dtu|NCE|reve|pretrained_frozen | 44 | 7.113 [+6.994, +7.233] | 0.047 | 1.487 | 6.734 |
| F2|dtu|NCE|reve|pretrained_peft | 44 | 7.054 [+6.928, +7.180] | 0.049 | 1.600 | 6.632 |
| L0|dtu|NCE | 44 | 6.869 [+6.710, +7.028] | 0.066 | 2.009 | 6.214 |
| L1|dtu|NCE | 44 | 6.905 [+6.750, +7.061] | 0.064 | 1.978 | 6.365 |
| R0|dtu|NCE | 44 | 7.238 [+7.141, +7.335] | 0.040 | 1.142 | 7.437 |
| R1|dtu|NCE | 44 | 7.289 [+7.196, +7.382] | 0.032 | 1.088 | 7.406 |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | 44 | 6.692 [+6.525, +6.859] | 0.076 | 2.341 | 5.988 |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | 44 | 6.743 [+6.589, +6.897] | 0.072 | 2.205 | 6.234 |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | 44 | 6.674 [+6.504, +6.843] | 0.081 | 2.372 | 5.937 |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | 44 | 6.741 [+6.581, +6.902] | 0.072 | 2.204 | 6.240 |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|0.0003 | 44 | 6.924 [+6.792, +7.055] | 0.062 | 1.814 | 6.454 |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|1e-05 | 44 | 7.278 [+7.172, +7.385] | 0.034 | 1.102 | 6.982 |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | 44 | 6.914 [+6.776, +7.051] | 0.064 | 1.859 | 6.409 |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | 44 | 7.277 [+7.170, +7.384] | 0.033 | 1.105 | 6.987 |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | 44 | 6.902 [+6.754, +7.051] | 0.065 | 2.003 | 6.303 |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | 44 | 6.911 [+6.750, +7.072] | 0.067 | 2.148 | 6.298 |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | 44 | 6.973 [+6.806, +7.141] | 0.064 | 2.084 | 6.354 |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | 44 | 6.931 [+6.775, +7.087] | 0.063 | 2.135 | 6.382 |
| T|dtu|NCE|reve|random_full|full_onestep_v1|0.0003 | 44 | 6.964 [+6.836, +7.093] | 0.055 | 1.641 | 6.571 |
| T|dtu|NCE|reve|random_full|full_onestep_v1|1e-05 | 44 | 6.926 [+6.792, +7.060] | 0.058 | 1.809 | 6.564 |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|0.0003 | 44 | 6.895 [+6.746, +7.043] | 0.061 | 1.997 | 6.498 |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|1e-05 | 44 | 6.951 [+6.815, +7.087] | 0.058 | 1.784 | 6.562 |

**federici**

| configuration | n | R [95% CI] | top1 | gain | R_native |
|---|---|---|---|---|---|
| A|federici|NCE|cbramod|pretrained_frozen | 86 | 8.103 [+8.072, +8.134] | 0.007 | 0.167 | 8.091 |
| A|federici|NCE|cbramod|pretrained_full | 86 | 8.111 [+8.070, +8.152] | 0.008 | 0.160 | 8.100 |
| A|federici|NCE|cbramod|pretrained_partial | 86 | 8.122 [+8.094, +8.150] | 0.007 | 0.109 | 8.118 |
| A|federici|NCE|cbramod|pretrained_peft | 86 | 8.082 [+8.037, +8.127] | 0.007 | 0.223 | 8.051 |
| A|federici|NCE|cbramod|random_full | 86 | 8.013 [+7.963, +8.063] | 0.013 | 0.391 | 8.008 |
| A|federici|NCE|reve|pretrained_frozen | 86 | 7.915 [+7.855, +7.975] | 0.017 | 0.526 | 7.872 |
| A|federici|NCE|reve|pretrained_full | 86 | 7.901 [+7.832, +7.969] | 0.019 | 0.594 | 7.852 |
| A|federici|NCE|reve|pretrained_partial | 86 | 7.901 [+7.833, +7.969] | 0.019 | 0.594 | 7.852 |
| A|federici|NCE|reve|pretrained_peft | 86 | 7.867 [+7.796, +7.937] | 0.023 | 0.619 | 7.815 |
| A|federici|NCE|reve|random_full | 86 | 7.830 [+7.750, +7.910] | 0.025 | 0.737 | 7.800 |
| F2|federici|NCE|cbramod|pretrained_frozen | 86 | 8.127 [+8.103, +8.152] | 0.008 | 0.096 | 8.122 |
| F2|federici|NCE|cbramod|pretrained_peft | 86 | 8.116 [+8.089, +8.144] | 0.009 | 0.134 | 8.117 |
| F2|federici|NCE|reve|pretrained_frozen | 86 | 7.989 [+7.939, +8.038] | 0.011 | 0.421 | 7.957 |
| F2|federici|NCE|reve|pretrained_peft | 86 | 7.987 [+7.939, +8.035] | 0.013 | 0.403 | 7.950 |
| L0|federici|NCE | 86 | 8.056 [+8.022, +8.090] | 0.012 | 0.264 | 7.999 |
| L1|federici|NCE | 86 | 7.984 [+7.940, +8.028] | 0.011 | 0.382 | 7.952 |
| R0|federici|NCE | 86 | 8.109 [+8.074, +8.143] | 0.007 | 0.142 | 8.171 |
| R1|federici|NCE | 86 | 8.052 [+8.008, +8.095] | 0.008 | 0.288 | 8.168 |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | 86 | 7.788 [+7.689, +7.886] | 0.027 | 0.829 | 7.732 |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | 86 | 7.803 [+7.708, +7.899] | 0.024 | 0.825 | 7.741 |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | 86 | 7.791 [+7.699, +7.884] | 0.027 | 0.826 | 7.735 |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | 86 | 7.801 [+7.708, +7.894] | 0.025 | 0.829 | 7.745 |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|0.0003 | 86 | 7.842 [+7.760, +7.925] | 0.021 | 0.743 | 7.776 |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|1e-05 | 86 | 7.921 [+7.859, +7.982] | 0.018 | 0.536 | 7.887 |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | 86 | 7.859 [+7.785, +7.933] | 0.018 | 0.655 | 7.795 |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | 86 | 7.925 [+7.856, +7.993] | 0.016 | 0.567 | 7.892 |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | 86 | 7.817 [+7.732, +7.901] | 0.026 | 0.776 | 7.744 |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | 86 | 7.896 [+7.826, +7.967] | 0.022 | 0.605 | 7.842 |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | 86 | 7.901 [+7.830, +7.972] | 0.021 | 0.587 | 7.855 |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | 86 | 7.894 [+7.821, +7.967] | 0.022 | 0.610 | 7.831 |
| T|federici|NCE|reve|random_full|full_onestep_v1|0.0003 | 86 | 7.801 [+7.706, +7.896] | 0.031 | 0.837 | 7.743 |
| T|federici|NCE|reve|random_full|full_onestep_v1|1e-05 | 86 | 7.809 [+7.713, +7.905] | 0.025 | 0.824 | 7.782 |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|0.0003 | 86 | 7.797 [+7.705, +7.890] | 0.031 | 0.836 | 7.729 |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|1e-05 | 86 | 7.812 [+7.717, +7.906] | 0.027 | 0.828 | 7.790 |

## 2. FM vs local under the same EEG access: L1 → B_ALIGNED

**fau · cbramod** (critical value 2.42)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 67 | -0.068 | [-0.107, -0.028] | [-0.115, -0.021] | I<0 | -0.010 | -0.152 | -0.133 | -0.026 |
| pretrained_frozen | FM vs local, same EEG access | 67 | -0.119 | [-0.180, -0.058] | [-0.193, -0.044] | I<0 | -0.016 | -0.337 | -0.331 | -0.001 |
| pretrained_peft | FM vs local, same EEG access | 67 | +0.008 | [-0.036, +0.052] | [-0.045, +0.061] | contains 0 | -0.001 | -0.107 | -0.144 | -0.004 |
| pretrained_partial | FM vs local, same EEG access | 67 | -0.077 | [-0.130, -0.024] | [-0.141, -0.013] | I<0 | -0.014 | -0.246 | -0.272 | -0.005 |
| pretrained_full | FM vs local, same EEG access | 67 | -0.005 | [-0.050, +0.039] | [-0.058, +0.048] | contains 0 | -0.004 | -0.124 | -0.166 | -0.003 |

**fau · reve** (critical value 2.46)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 67 | +0.074 | [+0.035, +0.114] | [+0.027, +0.121] | I>0 | +0.010 | +0.225 | +0.079 | -0.003 |
| pretrained_frozen | FM vs local, same EEG access | 67 | +0.029 | [-0.009, +0.066] | [-0.016, +0.074] | contains 0 | -0.001 | -0.063 | -0.048 | -0.012 |
| pretrained_peft | FM vs local, same EEG access | 67 | +0.061 | [+0.025, +0.097] | [+0.018, +0.105] | I>0 | +0.003 | +0.119 | +0.024 | -0.011 |
| pretrained_partial | FM vs local, same EEG access | 67 | +0.034 | [-0.002, +0.070] | [-0.010, +0.077] | contains 0 | -0.002 | -0.028 | -0.038 | -0.012 |
| pretrained_full | FM vs local, same EEG access | 67 | +0.034 | [-0.002, +0.070] | [-0.009, +0.077] | contains 0 | -0.002 | -0.028 | -0.038 | -0.012 |

**dtu · cbramod** (critical value 2.23)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 44 | -0.408 | [-0.496, -0.320] | [-0.507, -0.308] | I<0 | -0.031 | -0.894 | -0.662 | -0.054 |
| pretrained_frozen | FM vs local, same EEG access | 44 | -0.339 | [-0.440, -0.238] | [-0.454, -0.225] | I<0 | -0.027 | -0.846 | -0.715 | -0.043 |
| pretrained_peft | FM vs local, same EEG access | 44 | -0.273 | [-0.363, -0.183] | [-0.377, -0.168] | I<0 | -0.021 | -0.661 | -0.577 | -0.028 |
| pretrained_partial | FM vs local, same EEG access | 44 | -0.280 | [-0.377, -0.183] | [-0.391, -0.169] | I<0 | -0.028 | -0.768 | -0.631 | -0.034 |
| pretrained_full | FM vs local, same EEG access | 44 | -0.238 | [-0.329, -0.147] | [-0.342, -0.133] | I<0 | -0.022 | -0.626 | -0.537 | -0.024 |

**dtu · reve** (critical value 2.38)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 44 | +0.046 | [-0.006, +0.098] | [-0.013, +0.106] | contains 0 | -0.003 | -0.004 | -0.036 | +0.001 |
| pretrained_frozen | FM vs local, same EEG access | 44 | -0.239 | [-0.314, -0.165] | [-0.327, -0.152] | I<0 | -0.021 | -0.513 | -0.450 | -0.023 |
| pretrained_peft | FM vs local, same EEG access | 44 | -0.195 | [-0.269, -0.121] | [-0.281, -0.109] | I<0 | -0.019 | -0.509 | -0.402 | -0.014 |
| pretrained_partial | FM vs local, same EEG access | 44 | -0.231 | [-0.306, -0.157] | [-0.318, -0.144] | I<0 | -0.022 | -0.504 | -0.451 | -0.021 |
| pretrained_full | FM vs local, same EEG access | 44 | -0.231 | [-0.305, -0.157] | [-0.318, -0.144] | I<0 | -0.022 | -0.503 | -0.451 | -0.021 |

**federici · cbramod** (critical value 2.45)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 86 | -0.029 | [-0.068, +0.009] | [-0.077, +0.018] | contains 0 | +0.002 | +0.009 | -0.056 | – |
| pretrained_frozen | FM vs local, same EEG access | 86 | -0.119 | [-0.160, -0.079] | [-0.169, -0.070] | I<0 | -0.004 | -0.215 | -0.139 | – |
| pretrained_peft | FM vs local, same EEG access | 86 | -0.099 | [-0.141, -0.056] | [-0.152, -0.045] | I<0 | -0.004 | -0.159 | -0.099 | – |
| pretrained_partial | FM vs local, same EEG access | 86 | -0.138 | [-0.179, -0.098] | [-0.188, -0.088] | I<0 | -0.004 | -0.273 | -0.166 | – |
| pretrained_full | FM vs local, same EEG access | 86 | -0.127 | [-0.169, -0.085] | [-0.179, -0.075] | I<0 | -0.003 | -0.222 | -0.148 | – |

**federici · reve** (critical value 2.29)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full | FM vs local, same EEG access | 86 | +0.154 | [+0.106, +0.202] | [+0.097, +0.211] | I>0 | +0.014 | +0.356 | +0.152 | – |
| pretrained_frozen | FM vs local, same EEG access | 86 | +0.069 | [+0.028, +0.110] | [+0.022, +0.116] | I>0 | +0.006 | +0.144 | +0.080 | – |
| pretrained_peft | FM vs local, same EEG access | 86 | +0.117 | [+0.073, +0.161] | [+0.065, +0.169] | I>0 | +0.012 | +0.237 | +0.137 | – |
| pretrained_partial | FM vs local, same EEG access | 86 | +0.083 | [+0.038, +0.128] | [+0.031, +0.135] | I>0 | +0.008 | +0.212 | +0.099 | – |
| pretrained_full | FM vs local, same EEG access | 86 | +0.083 | [+0.038, +0.128] | [+0.031, +0.135] | I>0 | +0.008 | +0.212 | +0.100 | – |

## 3. FM vs local under post-only access: L0 → F2

**fau · cbramod** (critical value 2.18)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 67 | -0.181 | [-0.266, -0.096] | [-0.275, -0.087] | I<0 | -0.026 | -0.616 | -0.460 | +0.001 |
| pretrained_peft | FM vs local, same post-only access | 67 | -0.035 | [-0.092, +0.022] | [-0.096, +0.026] | contains 0 | -0.009 | -0.303 | -0.174 | +0.005 |

**fau · reve** (critical value 2.18)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 67 | -0.002 | [-0.047, +0.044] | [-0.050, +0.047] | contains 0 | -0.005 | -0.145 | -0.076 | -0.002 |
| pretrained_peft | FM vs local, same post-only access | 67 | +0.047 | [+0.010, +0.085] | [+0.008, +0.087] | I>0 | +0.001 | -0.032 | -0.013 | +0.000 |

**dtu · cbramod** (critical value 2.12)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 44 | -0.355 | [-0.461, -0.249] | [-0.466, -0.244] | I<0 | -0.027 | -0.838 | -0.803 | -0.033 |
| pretrained_peft | FM vs local, same post-only access | 44 | -0.294 | [-0.394, -0.194] | [-0.398, -0.191] | I<0 | -0.021 | -0.668 | -0.664 | -0.023 |

**dtu · reve** (critical value 2.12)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 44 | -0.244 | [-0.317, -0.171] | [-0.321, -0.167] | I<0 | -0.020 | -0.522 | -0.520 | -0.013 |
| pretrained_peft | FM vs local, same post-only access | 44 | -0.185 | [-0.254, -0.115] | [-0.258, -0.111] | I<0 | -0.017 | -0.409 | -0.418 | -0.009 |

**federici · cbramod** (critical value 2.21)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 86 | -0.071 | [-0.104, -0.039] | [-0.107, -0.035] | I<0 | -0.004 | -0.168 | -0.123 | – |
| pretrained_peft | FM vs local, same post-only access | 86 | -0.060 | [-0.093, -0.028] | [-0.096, -0.024] | I<0 | -0.002 | -0.131 | -0.119 | – |

**federici · reve** (critical value 2.09)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | FM vs local, same post-only access | 86 | +0.067 | [+0.029, +0.106] | [+0.027, +0.108] | I>0 | -0.000 | +0.157 | +0.042 | – |
| pretrained_peft | FM vs local, same post-only access | 86 | +0.069 | [+0.033, +0.105] | [+0.031, +0.107] | I>0 | +0.001 | +0.139 | +0.048 | – |

## 4. Value of the 0.4 s past EEG inside the FM: F2 → B_ALIGNED

**fau · cbramod** (critical value 2.32)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 67 | +0.027 | [+0.009, +0.044] | [+0.007, +0.047] | I>0 | +0.001 | +0.058 | +0.046 | +0.007 |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 67 | +0.008 | [-0.008, +0.024] | [-0.011, +0.027] | contains 0 | -0.000 | -0.025 | -0.053 | -0.001 |

**fau · reve** (critical value 2.24)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 67 | -0.005 | [-0.028, +0.018] | [-0.030, +0.020] | contains 0 | -0.004 | -0.139 | -0.055 | -0.002 |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 67 | -0.021 | [-0.045, +0.003] | [-0.048, +0.006] | contains 0 | -0.007 | -0.070 | -0.046 | -0.003 |

**dtu · cbramod** (critical value 2.31)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 44 | -0.020 | [-0.053, +0.012] | [-0.056, +0.015] | contains 0 | -0.003 | -0.038 | -0.064 | -0.006 |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 44 | -0.014 | [-0.050, +0.021] | [-0.054, +0.025] | contains 0 | -0.002 | -0.024 | -0.064 | -0.002 |

**dtu · reve** (critical value 2.16)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 44 | -0.032 | [-0.071, +0.008] | [-0.075, +0.011] | contains 0 | -0.004 | -0.022 | -0.081 | -0.006 |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 44 | -0.046 | [-0.085, -0.007] | [-0.089, -0.004] | I<0 | -0.004 | -0.131 | -0.135 | -0.002 |

**federici · cbramod** (critical value 2.31)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 86 | +0.024 | [-0.004, +0.052] | [-0.008, +0.056] | contains 0 | -0.001 | +0.070 | +0.031 | – |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 86 | +0.034 | [+0.001, +0.067] | [-0.004, +0.071] | contains 0 | -0.002 | +0.089 | +0.066 | – |

**federici · reve** (critical value 2.13)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| pretrained_frozen | value of the 0.4 s past EEG in the FM | 86 | +0.074 | [+0.038, +0.110] | [+0.035, +0.113] | I>0 | +0.006 | +0.105 | +0.085 | – |
| pretrained_peft | value of the 0.4 s past EEG in the FM | 86 | +0.120 | [+0.082, +0.159] | [+0.078, +0.163] | I>0 | +0.010 | +0.216 | +0.136 | – |

## 5. Value of the 0.4 s past EEG for the local encoder: L0 → L1

**fau** (critical value 2.05)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->L1 | past 0.4 s EEG for the local encoder | 67 | -0.035 | [-0.074, +0.003] | [-0.074, +0.003] | contains 0 | -0.009 | -0.221 | -0.083 | +0.009 |

**dtu** (critical value 2.09)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->L1 | past 0.4 s EEG for the local encoder | 44 | -0.036 | [-0.071, -0.001] | [-0.071, -0.001] | I<0 | -0.002 | -0.031 | -0.151 | +0.004 |

**federici** (critical value 1.99)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->L1 | past 0.4 s EEG for the local encoder | 86 | +0.072 | [+0.040, +0.104] | [+0.040, +0.104] | I>0 | -0.001 | +0.118 | +0.047 | – |

## 6. Encoder vs regularised linear readout on the same window

**fau** (critical value 2.49)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| R0->L0 | encoder vs ridge, post window | 67 | +0.147 | [+0.079, +0.215] | [+0.063, +0.231] | I>0 | +0.023 | +0.506 | +0.541 | +0.017 |
| R1->L1 | encoder vs ridge, aligned window | 67 | +0.157 | [+0.104, +0.211] | [+0.092, +0.223] | I>0 | +0.019 | +0.420 | +0.511 | +0.032 |
| R1->A/cbramod/frozen | frozen FM vs ridge, aligned window | 67 | +0.039 | [+0.005, +0.072] | [-0.004, +0.081] | contains 0 | +0.003 | +0.082 | +0.180 | +0.032 |
| R1->A/reve/frozen | frozen FM vs ridge, aligned window | 67 | +0.186 | [+0.146, +0.226] | [+0.134, +0.238] | I>0 | +0.018 | +0.356 | +0.462 | +0.020 |

**dtu** (critical value 2.55)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| R0->L0 | encoder vs ridge, post window | 44 | +0.368 | [+0.287, +0.450] | [+0.267, +0.470] | I>0 | +0.026 | +0.867 | +1.223 | +0.029 |
| R1->L1 | encoder vs ridge, aligned window | 44 | +0.383 | [+0.307, +0.460] | [+0.286, +0.480] | I>0 | +0.032 | +0.890 | +1.041 | +0.038 |
| R1->A/cbramod/frozen | frozen FM vs ridge, aligned window | 44 | +0.044 | [-0.013, +0.101] | [-0.027, +0.115] | contains 0 | +0.005 | +0.044 | +0.326 | -0.006 |
| R1->A/reve/frozen | frozen FM vs ridge, aligned window | 44 | +0.144 | [+0.087, +0.201] | [+0.073, +0.214] | I>0 | +0.011 | +0.378 | +0.591 | +0.015 |

**federici** (critical value 2.53)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| R0->L0 | encoder vs ridge, post window | 86 | +0.053 | [+0.021, +0.084] | [+0.012, +0.094] | I>0 | +0.005 | +0.123 | +0.172 | – |
| R1->L1 | encoder vs ridge, aligned window | 86 | +0.068 | [+0.036, +0.100] | [+0.027, +0.109] | I>0 | +0.003 | +0.094 | +0.216 | – |
| R1->A/cbramod/frozen | frozen FM vs ridge, aligned window | 86 | -0.052 | [-0.089, -0.014] | [-0.100, -0.003] | I<0 | -0.001 | -0.121 | +0.077 | – |
| R1->A/reve/frozen | frozen FM vs ridge, aligned window | 86 | +0.137 | [+0.098, +0.176] | [+0.086, +0.188] | I>0 | +0.010 | +0.238 | +0.296 | – |

## 7. True full update — initialization (random → pretrained, matched schedule and lr)

**fau · cbramod** (critical value 2.33)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 67 | +0.132 | [+0.078, +0.186] | [+0.071, +0.193] | I>0 | +0.017 | +0.386 | +0.212 | +0.017 |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 67 | +0.120 | [+0.088, +0.151] | [+0.083, +0.156] | I>0 | +0.013 | +0.172 | +0.106 | +0.005 |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 67 | +0.142 | [+0.087, +0.197] | [+0.080, +0.204] | I>0 | +0.020 | +0.399 | +0.219 | +0.016 |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 67 | +0.099 | [+0.069, +0.129] | [+0.064, +0.134] | I>0 | +0.010 | +0.156 | +0.106 | +0.007 |

**fau · reve** (critical value 2.54)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 67 | +0.010 | [-0.028, +0.048] | [-0.039, +0.059] | contains 0 | +0.001 | +0.043 | +0.013 | -0.004 |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 67 | -0.023 | [-0.067, +0.021] | [-0.078, +0.031] | contains 0 | +0.001 | +0.133 | +0.093 | +0.000 |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 67 | -0.009 | [-0.051, +0.032] | [-0.062, +0.043] | contains 0 | -0.004 | +0.023 | +0.008 | -0.003 |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 67 | -0.126 | [-0.183, -0.069] | [-0.196, -0.056] | I<0 | -0.014 | -0.063 | -0.071 | -0.008 |

**dtu · cbramod** (critical value 2.33)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 44 | +0.535 | [+0.453, +0.617] | [+0.439, +0.631] | I>0 | +0.038 | +1.104 | +0.748 | +0.063 |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 44 | +0.231 | [+0.171, +0.292] | [+0.160, +0.302] | I>0 | +0.014 | +0.527 | +0.466 | +0.018 |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 44 | +0.536 | [+0.453, +0.618] | [+0.440, +0.631] | I>0 | +0.039 | +1.099 | +0.747 | +0.059 |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 44 | +0.240 | [+0.177, +0.303] | [+0.166, +0.313] | I>0 | +0.017 | +0.513 | +0.471 | +0.026 |

**dtu · reve** (critical value 2.47)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 44 | +0.015 | [-0.063, +0.093] | [-0.082, +0.112] | contains 0 | +0.009 | +0.340 | +0.266 | -0.005 |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 44 | +0.062 | [-0.007, +0.131] | [-0.024, +0.147] | contains 0 | +0.010 | +0.362 | +0.268 | -0.003 |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 44 | +0.019 | [-0.046, +0.085] | [-0.062, +0.101] | contains 0 | +0.005 | +0.350 | +0.180 | -0.002 |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 44 | -0.079 | [-0.169, +0.011] | [-0.189, +0.031] | contains 0 | +0.003 | +0.087 | +0.144 | -0.014 |

**federici · cbramod** (critical value 2.48)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 86 | +0.117 | [+0.068, +0.166] | [+0.057, +0.177] | I>0 | +0.006 | +0.289 | +0.146 | – |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 86 | +0.055 | [+0.020, +0.089] | [+0.013, +0.096] | I>0 | +0.006 | +0.086 | +0.044 | – |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 86 | +0.124 | [+0.075, +0.173] | [+0.064, +0.183] | I>0 | +0.009 | +0.262 | +0.147 | – |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 86 | +0.068 | [+0.030, +0.105] | [+0.022, +0.113] | I>0 | +0.009 | +0.171 | +0.060 | – |

**federici · reve** (critical value 2.53)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| full_onestep_v1/lr1e-05 | initialization (matched schedule and lr) | 86 | -0.087 | [-0.141, -0.034] | [-0.155, -0.019] | I<0 | -0.003 | -0.219 | -0.061 | – |
| full_onestep_v1/lr0.0003 | initialization (matched schedule and lr) | 86 | -0.016 | [-0.052, +0.021] | [-0.062, +0.031] | contains 0 | -0.004 | -0.061 | -0.001 | – |
| warmup_then_all_v1/lr1e-05 | initialization (matched schedule and lr) | 86 | -0.082 | [-0.132, -0.032] | [-0.145, -0.019] | I<0 | -0.005 | -0.218 | -0.041 | – |
| warmup_then_all_v1/lr0.0003 | initialization (matched schedule and lr) | 86 | -0.104 | [-0.158, -0.049] | [-0.172, -0.036] | I<0 | -0.010 | -0.249 | -0.127 | – |

## 8. True full update — recipe (one-step → warm-up then all)

**fau · cbramod** (critical value 2.61)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 67 | -0.005 | [-0.010, -0.001] | [-0.011, +0.000] | contains 0 | -0.003 | -0.009 | -0.005 | +0.000 |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 67 | +0.018 | [+0.001, +0.035] | [-0.004, +0.039] | contains 0 | +0.003 | +0.022 | +0.013 | -0.002 |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 67 | +0.005 | [+0.000, +0.009] | [-0.001, +0.010] | contains 0 | +0.000 | +0.004 | +0.002 | -0.001 |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 67 | -0.003 | [-0.014, +0.008] | [-0.017, +0.012] | contains 0 | +0.000 | +0.007 | +0.012 | -0.001 |

**fau · reve** (critical value 2.62)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 67 | -0.008 | [-0.013, -0.002] | [-0.015, -0.000] | I<0 | -0.000 | -0.006 | -0.024 | +0.000 |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 67 | +0.003 | [-0.019, +0.024] | [-0.024, +0.029] | contains 0 | +0.000 | +0.070 | +0.026 | +0.003 |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 67 | -0.027 | [-0.052, -0.001] | [-0.060, +0.007] | contains 0 | -0.005 | -0.025 | -0.029 | +0.001 |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 67 | -0.100 | [-0.148, -0.052] | [-0.165, -0.035] | I<0 | -0.015 | -0.126 | -0.138 | -0.006 |

**dtu · cbramod** (critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 44 | +0.001 | [-0.010, +0.012] | [-0.012, +0.014] | contains 0 | -0.001 | +0.003 | -0.005 | +0.003 |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 44 | +0.010 | [-0.013, +0.033] | [-0.021, +0.041] | contains 0 | +0.002 | +0.045 | +0.045 | -0.003 |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 44 | +0.002 | [-0.005, +0.009] | [-0.008, +0.012] | contains 0 | +0.001 | -0.001 | -0.006 | -0.002 |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 44 | +0.019 | [+0.003, +0.034] | [-0.002, +0.039] | contains 0 | +0.005 | +0.031 | +0.050 | +0.005 |

**dtu · reve** (critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 44 | -0.025 | [-0.041, -0.009] | [-0.046, -0.003] | I<0 | +0.001 | -0.025 | +0.002 | -0.002 |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 44 | +0.070 | [+0.034, +0.105] | [+0.023, +0.117] | I>0 | +0.006 | +0.356 | +0.073 | +0.003 |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 44 | -0.020 | [-0.055, +0.014] | [-0.067, +0.026] | contains 0 | -0.004 | -0.014 | -0.084 | +0.002 |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 44 | -0.071 | [-0.123, -0.019] | [-0.137, -0.005] | I<0 | -0.001 | +0.081 | -0.051 | -0.008 |

**federici · cbramod** (critical value 2.56)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 86 | -0.004 | [-0.019, +0.010] | [-0.022, +0.014] | contains 0 | -0.002 | +0.032 | -0.005 | – |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 86 | -0.017 | [-0.042, +0.009] | [-0.050, +0.016] | contains 0 | -0.003 | -0.088 | -0.019 | – |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 86 | +0.003 | [-0.007, +0.012] | [-0.010, +0.015] | contains 0 | +0.001 | +0.004 | -0.004 | – |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 86 | -0.004 | [-0.023, +0.015] | [-0.028, +0.020] | contains 0 | +0.000 | -0.003 | -0.003 | – |

**federici · reve** (critical value 2.59)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/lr1e-05 | recipe: one-step -> warm-up then all | 86 | -0.003 | [-0.009, +0.004] | [-0.011, +0.006] | contains 0 | +0.003 | +0.004 | -0.008 | – |
| random_full/lr0.0003 | recipe: one-step -> warm-up then all | 86 | +0.004 | [-0.014, +0.021] | [-0.019, +0.026] | contains 0 | +0.001 | -0.001 | +0.015 | – |
| pretrained_full/lr1e-05 | recipe: one-step -> warm-up then all | 86 | +0.002 | [-0.037, +0.042] | [-0.050, +0.055] | contains 0 | +0.000 | +0.005 | +0.011 | – |
| pretrained_full/lr0.0003 | recipe: one-step -> warm-up then all | 86 | -0.084 | [-0.141, -0.028] | [-0.158, -0.011] | I<0 | -0.005 | -0.189 | -0.111 | – |

## 9. Legacy progressive prefix (B_ALIGNED) → true full

**fau · cbramod** (critical value 2.52)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.063 | [+0.047, +0.078] | [+0.043, +0.083] | I>0 | +0.008 | +0.069 | +0.028 | +0.008 |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.092 | [+0.047, +0.138] | [+0.036, +0.148] | I>0 | +0.013 | +0.292 | +0.197 | +0.018 |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.057 | [+0.044, +0.071] | [+0.040, +0.075] | I>0 | +0.005 | +0.060 | +0.023 | +0.008 |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.110 | [+0.065, +0.156] | [+0.054, +0.166] | I>0 | +0.016 | +0.315 | +0.209 | +0.016 |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.132 | [+0.078, +0.186] | [+0.064, +0.200] | I>0 | +0.018 | +0.427 | +0.273 | +0.002 |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.150 | [+0.093, +0.206] | [+0.078, +0.221] | I>0 | +0.020 | +0.437 | +0.336 | +0.000 |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.137 | [+0.083, +0.190] | [+0.070, +0.203] | I>0 | +0.019 | +0.431 | +0.275 | +0.000 |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.147 | [+0.087, +0.207] | [+0.072, +0.222] | I>0 | +0.021 | +0.443 | +0.348 | -0.001 |

**fau · reve** (critical value 2.84)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.025 | [+0.009, +0.041] | [+0.002, +0.048] | I>0 | +0.004 | +0.058 | +0.020 | -0.001 |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.007 | [-0.024, +0.037] | [-0.036, +0.049] | contains 0 | -0.001 | -0.111 | -0.051 | -0.005 |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.017 | [+0.003, +0.032] | [-0.003, +0.038] | contains 0 | +0.003 | +0.053 | -0.004 | -0.001 |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.009 | [-0.013, +0.031] | [-0.022, +0.040] | contains 0 | -0.000 | -0.041 | -0.025 | -0.003 |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.075 | [+0.028, +0.123] | [+0.010, +0.140] | I>0 | +0.017 | +0.354 | +0.151 | +0.003 |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | +0.023 | [-0.029, +0.075] | [-0.048, +0.095] | contains 0 | +0.012 | +0.276 | +0.159 | +0.004 |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 67 | +0.048 | [+0.005, +0.092] | [-0.012, +0.109] | contains 0 | +0.012 | +0.329 | +0.121 | +0.005 |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 67 | -0.077 | [-0.129, -0.024] | [-0.149, -0.005] | I<0 | -0.002 | +0.150 | +0.021 | -0.002 |

**dtu · cbramod** (critical value 2.59)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.035 | [+0.011, +0.059] | [+0.004, +0.066] | I>0 | +0.001 | +0.018 | +0.046 | +0.011 |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.390 | [+0.330, +0.450] | [+0.311, +0.468] | I>0 | +0.029 | +0.730 | +0.574 | +0.046 |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.036 | [+0.016, +0.057] | [+0.010, +0.062] | I>0 | +0.000 | +0.021 | +0.041 | +0.014 |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.400 | [+0.333, +0.466] | [+0.314, +0.485] | I>0 | +0.031 | +0.775 | +0.619 | +0.043 |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.400 | [+0.323, +0.477] | [+0.302, +0.497] | I>0 | +0.029 | +0.854 | +0.668 | +0.044 |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.451 | [+0.359, +0.543] | [+0.332, +0.570] | I>0 | +0.033 | +0.990 | +0.915 | +0.034 |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.402 | [+0.326, +0.478] | [+0.305, +0.498] | I>0 | +0.030 | +0.853 | +0.663 | +0.043 |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.470 | [+0.375, +0.564] | [+0.347, +0.592] | I>0 | +0.039 | +1.021 | +0.965 | +0.039 |

**dtu · reve** (critical value 2.81)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | -0.067 | [-0.098, -0.036] | [-0.110, -0.023] | I<0 | -0.003 | -0.165 | -0.163 | -0.001 |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | -0.105 | [-0.149, -0.061] | [-0.166, -0.045] | I<0 | -0.006 | -0.333 | -0.170 | -0.004 |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | -0.092 | [-0.119, -0.064] | [-0.131, -0.053] | I<0 | -0.003 | -0.190 | -0.161 | -0.003 |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | -0.035 | [-0.072, +0.002] | [-0.088, +0.017] | contains 0 | +0.000 | +0.023 | -0.097 | -0.001 |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.225 | [+0.158, +0.293] | [+0.131, +0.319] | I>0 | +0.025 | +0.674 | +0.518 | +0.015 |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.234 | [+0.165, +0.303] | [+0.136, +0.332] | I>0 | +0.024 | +0.528 | +0.513 | +0.015 |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 44 | +0.205 | [+0.144, +0.266] | [+0.121, +0.289] | I>0 | +0.021 | +0.660 | +0.434 | +0.017 |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 44 | +0.163 | [+0.071, +0.255] | [+0.034, +0.292] | I>0 | +0.023 | +0.609 | +0.462 | +0.007 |

**federici · cbramod** (critical value 2.49)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.092 | [+0.064, +0.121] | [+0.057, +0.128] | I>0 | +0.005 | +0.144 | +0.121 | – |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.171 | [+0.112, +0.229] | [+0.099, +0.242] | I>0 | +0.008 | +0.352 | +0.232 | – |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.088 | [+0.058, +0.119] | [+0.050, +0.127] | I>0 | +0.003 | +0.176 | +0.116 | – |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.154 | [+0.104, +0.204] | [+0.093, +0.215] | I>0 | +0.005 | +0.264 | +0.213 | – |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.307 | [+0.227, +0.388] | [+0.207, +0.408] | I>0 | +0.017 | +0.665 | +0.359 | – |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.323 | [+0.241, +0.406] | [+0.220, +0.426] | I>0 | +0.019 | +0.669 | +0.368 | – |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.310 | [+0.232, +0.388] | [+0.212, +0.408] | I>0 | +0.018 | +0.669 | +0.355 | – |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.320 | [+0.240, +0.399] | [+0.222, +0.418] | I>0 | +0.020 | +0.665 | +0.365 | – |

**federici · reve** (critical value 2.72)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| random_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.020 | [-0.010, +0.050] | [-0.021, +0.062] | contains 0 | +0.000 | +0.087 | +0.018 | – |
| random_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.028 | [-0.004, +0.061] | [-0.017, +0.073] | contains 0 | +0.006 | +0.099 | +0.056 | – |
| random_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.018 | [-0.011, +0.046] | [-0.021, +0.057] | contains 0 | +0.003 | +0.091 | +0.010 | – |
| random_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.032 | [-0.000, +0.064] | [-0.012, +0.077] | contains 0 | +0.007 | +0.099 | +0.071 | – |
| pretrained_full/full_onestep_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.004 | [-0.036, +0.045] | [-0.050, +0.059] | contains 0 | +0.003 | +0.011 | +0.010 | – |
| pretrained_full/full_onestep_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | +0.084 | [+0.043, +0.125] | [+0.027, +0.141] | I>0 | +0.007 | +0.182 | +0.108 | – |
| pretrained_full/warmup_then_all_v1/lr1e-05 | recipe: legacy prefix -> true full | 86 | +0.007 | [-0.027, +0.041] | [-0.039, +0.053] | contains 0 | +0.003 | +0.016 | +0.021 | – |
| pretrained_full/warmup_then_all_v1/lr0.0003 | recipe: legacy prefix -> true full | 86 | -0.000 | [-0.044, +0.043] | [-0.061, +0.060] | contains 0 | +0.002 | -0.007 | -0.003 | – |

## 10. Local (L0 / L1) → true-full FM

**fau · cbramod** (critical value 2.81)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 67 | -0.040 | [-0.096, +0.016] | [-0.118, +0.037] | contains 0 | -0.011 | -0.304 | -0.188 | -0.010 |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 67 | -0.011 | [-0.049, +0.027] | [-0.066, +0.044] | contains 0 | -0.005 | -0.080 | -0.019 | +0.000 |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 67 | -0.046 | [-0.102, +0.011] | [-0.125, +0.033] | contains 0 | -0.014 | -0.313 | -0.193 | -0.010 |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 67 | +0.007 | [-0.029, +0.043] | [-0.043, +0.058] | contains 0 | -0.002 | -0.058 | -0.006 | -0.002 |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 67 | +0.092 | [+0.057, +0.127] | [+0.041, +0.142] | I>0 | +0.006 | +0.082 | +0.024 | +0.007 |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 67 | +0.109 | [+0.080, +0.138] | [+0.068, +0.150] | I>0 | +0.008 | +0.092 | +0.087 | +0.006 |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 67 | +0.096 | [+0.061, +0.132] | [+0.046, +0.147] | I>0 | +0.006 | +0.086 | +0.026 | +0.006 |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 67 | +0.106 | [+0.077, +0.136] | [+0.065, +0.148] | I>0 | +0.008 | +0.099 | +0.099 | +0.005 |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 67 | -0.005 | [-0.039, +0.029] | [-0.051, +0.041] | contains 0 | -0.002 | -0.083 | -0.105 | -0.019 |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 67 | +0.025 | [-0.011, +0.060] | [-0.023, +0.072] | contains 0 | +0.004 | +0.141 | +0.064 | -0.008 |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 67 | -0.010 | [-0.045, +0.024] | [-0.058, +0.037] | contains 0 | -0.005 | -0.092 | -0.110 | -0.018 |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 67 | +0.042 | [+0.010, +0.074] | [-0.002, +0.087] | contains 0 | +0.007 | +0.163 | +0.076 | -0.010 |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 67 | +0.127 | [+0.080, +0.174] | [+0.061, +0.193] | I>0 | +0.014 | +0.303 | +0.106 | -0.001 |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 67 | +0.144 | [+0.100, +0.189] | [+0.083, +0.206] | I>0 | +0.017 | +0.313 | +0.170 | -0.003 |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 67 | +0.132 | [+0.085, +0.178] | [+0.067, +0.197] | I>0 | +0.015 | +0.307 | +0.109 | -0.003 |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 67 | +0.142 | [+0.094, +0.189] | [+0.075, +0.208] | I>0 | +0.017 | +0.320 | +0.182 | -0.004 |

**fau · reve** (critical value 2.94)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 67 | +0.064 | [+0.038, +0.090] | [+0.024, +0.104] | I>0 | +0.005 | +0.063 | +0.017 | +0.005 |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 67 | +0.046 | [+0.006, +0.085] | [-0.010, +0.101] | contains 0 | +0.001 | -0.106 | -0.054 | +0.001 |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 67 | +0.056 | [+0.030, +0.083] | [+0.018, +0.095] | I>0 | +0.005 | +0.057 | -0.007 | +0.005 |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 67 | +0.048 | [+0.014, +0.082] | [-0.001, +0.097] | contains 0 | +0.001 | -0.037 | -0.028 | +0.003 |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 67 | +0.074 | [+0.028, +0.121] | [+0.008, +0.141] | I>0 | +0.006 | +0.106 | +0.030 | +0.000 |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 67 | +0.022 | [-0.023, +0.068] | [-0.046, +0.090] | contains 0 | +0.002 | +0.027 | +0.039 | +0.001 |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 67 | +0.047 | [-0.003, +0.097] | [-0.024, +0.118] | contains 0 | +0.001 | +0.080 | +0.001 | +0.002 |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 67 | -0.078 | [-0.131, -0.024] | [-0.156, +0.000] | contains 0 | -0.013 | -0.099 | -0.099 | -0.005 |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 67 | +0.099 | [+0.057, +0.141] | [+0.039, +0.160] | I>0 | +0.014 | +0.284 | +0.100 | -0.004 |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 67 | +0.081 | [+0.050, +0.111] | [+0.035, +0.126] | I>0 | +0.009 | +0.115 | +0.029 | -0.008 |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 67 | +0.092 | [+0.052, +0.132] | [+0.033, +0.150] | I>0 | +0.014 | +0.278 | +0.076 | -0.004 |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 67 | +0.083 | [+0.044, +0.122] | [+0.026, +0.140] | I>0 | +0.010 | +0.185 | +0.055 | -0.005 |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 67 | +0.109 | [+0.062, +0.157] | [+0.039, +0.180] | I>0 | +0.015 | +0.327 | +0.113 | -0.008 |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 67 | +0.057 | [+0.010, +0.104] | [-0.012, +0.127] | contains 0 | +0.010 | +0.248 | +0.122 | -0.008 |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 67 | +0.082 | [+0.036, +0.129] | [+0.013, +0.152] | I>0 | +0.010 | +0.301 | +0.084 | -0.007 |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 67 | -0.043 | [-0.095, +0.010] | [-0.119, +0.034] | contains 0 | -0.004 | +0.122 | -0.016 | -0.014 |

**dtu · cbramod** (critical value 2.78)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 44 | -0.409 | [-0.507, -0.312] | [-0.543, -0.275] | I<0 | -0.033 | -0.907 | -0.768 | -0.039 |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 44 | -0.054 | [-0.127, +0.019] | [-0.153, +0.045] | contains 0 | -0.004 | -0.195 | -0.240 | -0.005 |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 44 | -0.408 | [-0.507, -0.309] | [-0.542, -0.274] | I<0 | -0.033 | -0.904 | -0.773 | -0.036 |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 44 | -0.044 | [-0.110, +0.022] | [-0.134, +0.045] | contains 0 | -0.002 | -0.150 | -0.195 | -0.007 |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 44 | +0.126 | [+0.056, +0.196] | [+0.032, +0.220] | I>0 | +0.005 | +0.196 | -0.020 | +0.024 |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 44 | +0.177 | [+0.125, +0.229] | [+0.106, +0.248] | I>0 | +0.009 | +0.333 | +0.226 | +0.013 |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 44 | +0.128 | [+0.058, +0.198] | [+0.033, +0.223] | I>0 | +0.006 | +0.195 | -0.026 | +0.022 |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 44 | +0.196 | [+0.137, +0.254] | [+0.115, +0.276] | I>0 | +0.015 | +0.363 | +0.277 | +0.019 |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 44 | -0.373 | [-0.458, -0.288] | [-0.491, -0.255] | I<0 | -0.030 | -0.876 | -0.617 | -0.043 |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 44 | -0.018 | [-0.083, +0.046] | [-0.107, +0.071] | contains 0 | -0.002 | -0.164 | -0.089 | -0.008 |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 44 | -0.372 | [-0.459, -0.285] | [-0.491, -0.253] | I<0 | -0.031 | -0.873 | -0.622 | -0.040 |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 44 | -0.008 | [-0.068, +0.052] | [-0.091, +0.075] | contains 0 | +0.000 | -0.119 | -0.044 | -0.011 |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 44 | +0.162 | [+0.088, +0.236] | [+0.063, +0.261] | I>0 | +0.008 | +0.227 | +0.131 | +0.020 |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 44 | +0.213 | [+0.151, +0.276] | [+0.129, +0.298] | I>0 | +0.012 | +0.363 | +0.377 | +0.010 |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 44 | +0.164 | [+0.089, +0.239] | [+0.063, +0.265] | I>0 | +0.008 | +0.226 | +0.125 | +0.019 |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 44 | +0.232 | [+0.162, +0.301] | [+0.138, +0.326] | I>0 | +0.017 | +0.394 | +0.428 | +0.015 |

**dtu · reve** (critical value 2.96)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 44 | -0.057 | [-0.116, +0.003] | [-0.143, +0.029] | contains 0 | -0.009 | -0.200 | -0.350 | +0.003 |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 44 | -0.095 | [-0.156, -0.034] | [-0.187, -0.003] | I<0 | -0.011 | -0.367 | -0.357 | -0.000 |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 44 | -0.081 | [-0.141, -0.022] | [-0.168, +0.005] | contains 0 | -0.008 | -0.225 | -0.348 | +0.001 |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 44 | -0.025 | [-0.077, +0.026] | [-0.103, +0.053] | contains 0 | -0.005 | -0.012 | -0.284 | +0.003 |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 44 | -0.042 | [-0.117, +0.033] | [-0.154, +0.070] | contains 0 | +0.001 | +0.140 | -0.084 | -0.002 |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 44 | -0.033 | [-0.108, +0.042] | [-0.142, +0.076] | contains 0 | -0.001 | -0.006 | -0.089 | -0.003 |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 44 | -0.062 | [-0.130, +0.006] | [-0.165, +0.041] | contains 0 | -0.003 | +0.126 | -0.168 | -0.001 |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 44 | -0.104 | [-0.189, -0.019] | [-0.228, +0.020] | contains 0 | -0.002 | +0.075 | -0.140 | -0.011 |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 44 | -0.021 | [-0.077, +0.035] | [-0.100, +0.058] | contains 0 | -0.006 | -0.169 | -0.199 | -0.001 |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 44 | -0.059 | [-0.118, +0.000] | [-0.144, +0.026] | contains 0 | -0.009 | -0.337 | -0.206 | -0.004 |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 44 | -0.045 | [-0.100, +0.009] | [-0.124, +0.033] | contains 0 | -0.006 | -0.194 | -0.197 | -0.002 |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 44 | +0.011 | [-0.041, +0.062] | [-0.064, +0.086] | contains 0 | -0.003 | +0.019 | -0.133 | -0.001 |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 44 | -0.006 | [-0.089, +0.078] | [-0.126, +0.115] | contains 0 | +0.003 | +0.170 | +0.067 | -0.006 |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 44 | +0.003 | [-0.075, +0.081] | [-0.109, +0.115] | contains 0 | +0.001 | +0.025 | +0.062 | -0.007 |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 44 | -0.026 | [-0.100, +0.048] | [-0.134, +0.083] | contains 0 | -0.001 | +0.157 | -0.017 | -0.004 |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 44 | -0.068 | [-0.166, +0.030] | [-0.209, +0.073] | contains 0 | +0.000 | +0.106 | +0.011 | -0.014 |

**federici · cbramod** (critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 86 | +0.135 | [+0.086, +0.184] | [+0.069, +0.201] | I>0 | +0.006 | +0.271 | +0.112 | – |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 86 | +0.213 | [+0.145, +0.282] | [+0.121, +0.306] | I>0 | +0.009 | +0.479 | +0.223 | – |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 86 | +0.131 | [+0.076, +0.186] | [+0.057, +0.206] | I>0 | +0.005 | +0.303 | +0.107 | – |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 86 | +0.197 | [+0.135, +0.259] | [+0.116, +0.278] | I>0 | +0.006 | +0.391 | +0.204 | – |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 86 | +0.252 | [+0.173, +0.331] | [+0.147, +0.357] | I>0 | +0.013 | +0.561 | +0.258 | – |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 86 | +0.268 | [+0.188, +0.348] | [+0.162, +0.375] | I>0 | +0.015 | +0.565 | +0.267 | – |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 86 | +0.255 | [+0.178, +0.332] | [+0.152, +0.358] | I>0 | +0.014 | +0.565 | +0.254 | – |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 86 | +0.264 | [+0.188, +0.341] | [+0.163, +0.366] | I>0 | +0.015 | +0.562 | +0.264 | – |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 86 | +0.063 | [+0.024, +0.103] | [+0.011, +0.115] | I>0 | +0.007 | +0.154 | +0.065 | – |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 86 | +0.141 | [+0.082, +0.200] | [+0.063, +0.220] | I>0 | +0.010 | +0.361 | +0.176 | – |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 86 | +0.059 | [+0.014, +0.104] | [-0.001, +0.119] | contains 0 | +0.005 | +0.185 | +0.060 | – |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 86 | +0.125 | [+0.074, +0.175] | [+0.058, +0.191] | I>0 | +0.007 | +0.273 | +0.157 | – |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 86 | +0.180 | [+0.112, +0.248] | [+0.091, +0.270] | I>0 | +0.013 | +0.443 | +0.211 | – |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 86 | +0.196 | [+0.127, +0.265] | [+0.105, +0.287] | I>0 | +0.016 | +0.447 | +0.220 | – |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 86 | +0.183 | [+0.117, +0.249] | [+0.096, +0.270] | I>0 | +0.014 | +0.447 | +0.207 | – |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 86 | +0.192 | [+0.129, +0.256] | [+0.106, +0.278] | I>0 | +0.016 | +0.444 | +0.217 | – |

**federici · reve** (critical value 2.72)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|
| L0->random_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 86 | +0.247 | [+0.167, +0.326] | [+0.139, +0.354] | I>0 | +0.013 | +0.560 | +0.217 | – |
| L0->random_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 86 | +0.255 | [+0.179, +0.331] | [+0.151, +0.358] | I>0 | +0.019 | +0.572 | +0.255 | – |
| L0->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 86 | +0.244 | [+0.166, +0.323] | [+0.137, +0.351] | I>0 | +0.016 | +0.564 | +0.209 | – |
| L0->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 86 | +0.258 | [+0.182, +0.335] | [+0.155, +0.362] | I>0 | +0.020 | +0.572 | +0.270 | – |
| L0->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L0) | 86 | +0.160 | [+0.102, +0.218] | [+0.081, +0.239] | I>0 | +0.010 | +0.341 | +0.156 | – |
| L0->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L0) | 86 | +0.239 | [+0.167, +0.312] | [+0.143, +0.336] | I>0 | +0.015 | +0.512 | +0.255 | – |
| L0->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L0) | 86 | +0.162 | [+0.103, +0.221] | [+0.082, +0.242] | I>0 | +0.010 | +0.346 | +0.168 | – |
| L0->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L0) | 86 | +0.155 | [+0.096, +0.213] | [+0.074, +0.235] | I>0 | +0.010 | +0.323 | +0.144 | – |
| L1->random_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 86 | +0.175 | [+0.107, +0.242] | [+0.083, +0.266] | I>0 | +0.014 | +0.442 | +0.170 | – |
| L1->random_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 86 | +0.183 | [+0.118, +0.247] | [+0.095, +0.270] | I>0 | +0.020 | +0.455 | +0.208 | – |
| L1->random_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 86 | +0.172 | [+0.104, +0.240] | [+0.082, +0.262] | I>0 | +0.016 | +0.447 | +0.162 | – |
| L1->random_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 86 | +0.186 | [+0.121, +0.251] | [+0.098, +0.275] | I>0 | +0.020 | +0.454 | +0.223 | – |
| L1->pretrained_full/full_onestep_v1/lr1e-05 | FM vs local (L1) | 86 | +0.087 | [+0.036, +0.139] | [+0.017, +0.158] | I>0 | +0.011 | +0.223 | +0.109 | – |
| L1->pretrained_full/full_onestep_v1/lr0.0003 | FM vs local (L1) | 86 | +0.167 | [+0.107, +0.227] | [+0.087, +0.247] | I>0 | +0.015 | +0.394 | +0.208 | – |
| L1->pretrained_full/warmup_then_all_v1/lr1e-05 | FM vs local (L1) | 86 | +0.090 | [+0.039, +0.141] | [+0.020, +0.160] | I>0 | +0.011 | +0.228 | +0.121 | – |
| L1->pretrained_full/warmup_then_all_v1/lr0.0003 | FM vs local (L1) | 86 | +0.083 | [+0.029, +0.136] | [+0.011, +0.155] | I>0 | +0.010 | +0.205 | +0.097 | – |

## 11. Update ledger (true-full and post-only units)

| configuration | group kind | first open epoch (median) | open epochs (median) | grad steps (median) | rel. weight change median [min, max] |
|---|---|---|---|---|---|
| F2|dtu|NCE|cbramod|pretrained_frozen | readout | 1 | 100 | 6049 | 1.24e+00 [1.19e+00, 1.31e+00] |
| F2|dtu|NCE|cbramod|pretrained_peft | block | 6 | 95 | 5746 | 5.46e-02 [1.31e-02, 2.18e-01] |
| F2|dtu|NCE|cbramod|pretrained_peft | readout | 1 | 100 | 6049 | 1.19e+00 [1.13e+00, 1.28e+00] |
| F2|dtu|NCE|reve|pretrained_frozen | readout | 1 | 50 | 3023 | 1.38e+00 [1.32e+00, 1.45e+00] |
| F2|dtu|NCE|reve|pretrained_peft | block | 6 | 45 | 2863 | 3.46e-02 [6.79e-04, 2.37e-01] |
| F2|dtu|NCE|reve|pretrained_peft | readout | 1 | 50 | 3181 | 1.38e+00 [1.32e+00, 1.46e+00] |
| F2|fau|NCE|cbramod|pretrained_frozen | readout | 1 | 100 | 12782 | 1.25e+00 [3.81e-01, 1.61e+00] |
| F2|fau|NCE|cbramod|pretrained_peft | block | 6 | 95 | 12142 | 9.15e-02 [1.98e-02, 2.68e-01] |
| F2|fau|NCE|cbramod|pretrained_peft | readout | 1 | 100 | 12782 | 1.31e+00 [1.13e+00, 1.50e+00] |
| F2|fau|NCE|reve|pretrained_frozen | readout | 1 | 50 | 6388 | 1.26e+00 [1.14e+00, 1.38e+00] |
| F2|fau|NCE|reve|pretrained_peft | block | 6 | 45 | 5748 | 3.93e-02 [6.22e-04, 3.52e-01] |
| F2|fau|NCE|reve|pretrained_peft | readout | 1 | 50 | 6388 | 1.26e+00 [1.14e+00, 1.38e+00] |
| F2|federici|NCE|cbramod|pretrained_frozen | readout | 1 | 100 | 12600 | 4.37e-01 [3.47e-01, 1.10e+00] |
| F2|federici|NCE|cbramod|pretrained_peft | block | 6 | 95 | 11970 | 0.00e+00 [0.00e+00, 3.34e-01] |
| F2|federici|NCE|cbramod|pretrained_peft | readout | 1 | 100 | 12600 | 4.51e-01 [2.73e-01, 1.21e+00] |
| F2|federici|NCE|reve|pretrained_frozen | readout | 1 | 50 | 6300 | 1.02e+00 [1.00e+00, 1.08e+00] |
| F2|federici|NCE|reve|pretrained_peft | block | 6 | 45 | 5670 | 2.41e-02 [4.02e-04, 2.84e-01] |
| F2|federici|NCE|reve|pretrained_peft | readout | 1 | 50 | 6300 | 9.78e-01 [9.73e-01, 1.04e+00] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 100 | 6049 | 2.18e-01 [1.61e-01, 3.30e-01] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 6049 | 4.32e-01 [3.99e-01, 4.64e-01] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 6049 | 1.46e+00 [1.39e+00, 1.60e+00] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 100 | 6049 | 1.74e-02 [1.13e-02, 2.59e-02] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 6049 | 2.92e-02 [2.75e-02, 3.27e-02] |
| T|dtu|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 6049 | 1.43e+00 [1.33e+00, 1.50e+00] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 5746 | 2.03e-01 [1.55e-01, 2.88e-01] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 5746 | 3.86e-01 [3.70e-01, 4.15e-01] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 6049 | 1.15e+00 [1.12e+00, 1.26e+00] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 5746 | 1.62e-02 [9.61e-03, 2.70e-02] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 5746 | 2.74e-02 [2.52e-02, 3.01e-02] |
| T|dtu|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 6049 | 1.20e+00 [1.13e+00, 1.27e+00] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|0.0003 | block | 1 | 100 | 6049 | 1.14e-01 [8.88e-02, 1.88e-01] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 6049 | 1.91e-01 [1.71e-01, 2.08e-01] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 6049 | 1.36e+00 [1.25e+00, 1.48e+00] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|1e-05 | block | 1 | 100 | 6049 | 7.34e-03 [6.39e-03, 1.11e-02] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 6049 | 1.13e-02 [1.04e-02, 1.20e-02] |
| T|dtu|NCE|cbramod|random_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 6049 | 1.35e+00 [1.27e+00, 1.44e+00] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 5746 | 1.24e-01 [1.12e-01, 1.78e-01] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 5746 | 1.87e-01 [1.69e-01, 2.12e-01] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 6049 | 1.26e+00 [1.22e+00, 1.38e+00] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 5746 | 6.73e-03 [5.92e-03, 1.02e-02] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 5746 | 1.05e-02 [9.73e-03, 1.12e-02] |
| T|dtu|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 6049 | 1.31e+00 [1.24e+00, 1.41e+00] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 50 | 3023 | 1.05e-01 [5.06e-02, 1.35e-01] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 3023 | 7.02e-02 [5.30e-02, 8.05e-02] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 3023 | 1.13e+00 [8.28e-01, 1.21e+00] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 50 | 3023 | 6.17e-03 [4.66e-03, 7.45e-03] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 3023 | 3.56e-03 [2.52e-03, 3.87e-03] |
| T|dtu|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 3023 | 1.40e+00 [1.34e+00, 1.48e+00] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 2720 | 9.36e-02 [5.58e-02, 1.19e-01] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 2720 | 5.78e-02 [3.82e-02, 6.84e-02] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 3023 | 1.24e+00 [1.15e+00, 1.32e+00] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 2720 | 4.86e-03 [3.69e-03, 5.84e-03] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 2720 | 2.84e-03 [2.43e-03, 3.11e-03] |
| T|dtu|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 3023 | 1.40e+00 [1.36e+00, 1.48e+00] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|0.0003 | block | 1 | 50 | 3023 | 1.50e-01 [1.20e-01, 3.94e-01] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 3023 | 1.02e-01 [8.89e-02, 1.12e-01] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 3023 | 5.91e-01 [5.49e-01, 6.58e-01] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|1e-05 | block | 1 | 50 | 3023 | 1.73e-02 [1.56e-02, 1.97e-02] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 3023 | 4.88e-03 [4.68e-03, 5.21e-03] |
| T|dtu|NCE|reve|random_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 3023 | 9.05e-01 [8.79e-01, 9.75e-01] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 2720 | 1.40e-01 [8.35e-02, 3.21e-01] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 2720 | 9.18e-02 [6.99e-02, 9.75e-02] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 3023 | 8.43e-01 [6.40e-01, 8.92e-01] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 2720 | 1.38e-02 [1.25e-02, 1.56e-02] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 2720 | 3.39e-03 [3.28e-03, 3.60e-03] |
| T|dtu|NCE|reve|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 3023 | 9.49e-01 [9.18e-01, 1.01e+00] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 100 | 12782 | 3.12e-01 [2.30e-01, 5.07e-01] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 12782 | 6.28e-01 [5.64e-01, 7.22e-01] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 12782 | 1.52e+00 [1.33e+00, 1.72e+00] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 100 | 12782 | 2.16e-02 [1.46e-02, 3.38e-02] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 12782 | 3.77e-02 [3.19e-02, 4.36e-02] |
| T|fau|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 12782 | 1.54e+00 [1.36e+00, 1.70e+00] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 12142 | 2.96e-01 [2.17e-01, 4.51e-01] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 12142 | 5.93e-01 [5.29e-01, 6.59e-01] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 12782 | 1.26e+00 [1.07e+00, 1.46e+00] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 12142 | 2.00e-02 [1.31e-02, 3.12e-02] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 12142 | 3.51e-02 [3.04e-02, 4.02e-02] |
| T|fau|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 12782 | 1.31e+00 [1.12e+00, 1.50e+00] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|0.0003 | block | 1 | 100 | 12782 | 1.63e-01 [1.30e-01, 2.77e-01] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 12782 | 3.13e-01 [2.35e-01, 3.67e-01] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 12782 | 1.49e+00 [1.30e+00, 1.69e+00] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|1e-05 | block | 1 | 100 | 12782 | 1.02e-02 [8.22e-03, 1.68e-02] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 12782 | 1.83e-02 [1.41e-02, 2.19e-02] |
| T|fau|NCE|cbramod|random_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 12782 | 1.46e+00 [1.28e+00, 1.63e+00] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 12142 | 1.69e-01 [1.32e-01, 2.57e-01] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 12142 | 2.90e-01 [2.18e-01, 3.47e-01] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 12782 | 1.37e+00 [1.13e+00, 1.55e+00] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 12142 | 9.42e-03 [7.56e-03, 1.56e-02] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 12142 | 1.67e-02 [1.32e-02, 2.01e-02] |
| T|fau|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 12782 | 1.43e+00 [1.25e+00, 1.61e+00] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 50 | 6388 | 1.17e-01 [3.48e-02, 1.99e-01] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 6388 | 8.65e-02 [6.72e-02, 1.22e-01] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 6388 | 9.15e-01 [5.55e-01, 1.14e+00] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 50 | 6388 | 8.13e-03 [5.94e-03, 1.05e-02] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 6388 | 4.06e-03 [3.54e-03, 4.51e-03] |
| T|fau|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 6388 | 1.29e+00 [1.13e+00, 1.39e+00] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 6568 | 1.24e-01 [7.20e-02, 1.73e-01] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 6568 | 6.36e-02 [5.27e-02, 8.52e-02] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 7299 | 1.13e+00 [9.50e-01, 1.28e+00] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 5748 | 6.52e-03 [4.49e-03, 8.93e-03] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 5748 | 3.51e-03 [3.38e-03, 4.16e-03] |
| T|fau|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 6388 | 1.29e+00 [1.11e+00, 1.40e+00] |
| T|fau|NCE|reve|random_full|full_onestep_v1|0.0003 | block | 1 | 50 | 7299 | 2.01e-01 [1.47e-01, 5.26e-01] |
| T|fau|NCE|reve|random_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 7299 | 1.54e-01 [1.24e-01, 1.85e-01] |
| T|fau|NCE|reve|random_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 7299 | 6.79e-01 [5.67e-01, 8.17e-01] |
| T|fau|NCE|reve|random_full|full_onestep_v1|1e-05 | block | 1 | 50 | 6388 | 2.16e-02 [1.80e-02, 2.60e-02] |
| T|fau|NCE|reve|random_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 6388 | 6.33e-03 [5.61e-03, 7.09e-03] |
| T|fau|NCE|reve|random_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 6388 | 9.14e-01 [7.97e-01, 1.06e+00] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 5748 | 1.90e-01 [1.13e-01, 4.59e-01] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 5748 | 1.26e-01 [1.03e-01, 1.50e-01] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 6388 | 8.21e-01 [7.19e-01, 9.68e-01] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 5748 | 1.76e-02 [1.53e-02, 2.09e-02] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 5748 | 4.38e-03 [3.88e-03, 4.91e-03] |
| T|fau|NCE|reve|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 6388 | 9.41e-01 [8.14e-01, 1.08e+00] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 100 | 12600 | 2.71e-01 [1.74e-01, 4.33e-01] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 12600 | 4.83e-01 [3.35e-01, 5.04e-01] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 12600 | 1.23e+00 [7.93e-01, 1.31e+00] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 100 | 12600 | 2.03e-02 [1.44e-02, 3.00e-02] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 12600 | 2.95e-02 [2.56e-02, 3.00e-02] |
| T|federici|NCE|cbramod|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 12600 | 1.45e+00 [1.19e+00, 1.51e+00] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 11970 | 2.81e-01 [2.17e-01, 4.03e-01] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 11970 | 4.66e-01 [3.99e-01, 5.06e-01] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 12600 | 1.02e+00 [8.53e-01, 1.10e+00] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 11970 | 1.95e-02 [1.45e-02, 2.88e-02] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 11970 | 2.87e-02 [2.82e-02, 2.95e-02] |
| T|federici|NCE|cbramod|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 12600 | 1.18e+00 [1.10e+00, 1.21e+00] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|0.0003 | block | 1 | 100 | 12600 | 1.31e-01 [1.09e-01, 2.38e-01] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|0.0003 | non-block | 1 | 100 | 12600 | 2.00e-01 [1.90e-01, 2.37e-01] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|0.0003 | readout | 1 | 100 | 12600 | 1.14e+00 [1.02e+00, 1.30e+00] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|1e-05 | block | 1 | 100 | 12600 | 9.43e-03 [8.85e-03, 1.30e-02] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|1e-05 | non-block | 1 | 100 | 12600 | 1.23e-02 [1.22e-02, 1.28e-02] |
| T|federici|NCE|cbramod|random_full|full_onestep_v1|1e-05 | readout | 1 | 100 | 12600 | 1.24e+00 [1.22e+00, 1.26e+00] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | block | 6 | 95 | 11970 | 1.50e-01 [1.31e-01, 2.32e-01] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 95 | 11970 | 2.21e-01 [1.81e-01, 2.42e-01] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 100 | 12600 | 1.13e+00 [9.42e-01, 1.13e+00] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | block | 6 | 95 | 11970 | 8.94e-03 [8.30e-03, 1.34e-02] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 95 | 11970 | 1.19e-02 [1.12e-02, 1.28e-02] |
| T|federici|NCE|cbramod|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 100 | 12600 | 1.24e+00 [1.21e+00, 1.33e+00] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | block | 1 | 50 | 6300 | 8.24e-02 [2.97e-02, 1.78e-01] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 6300 | 1.02e-01 [5.95e-02, 1.14e-01] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 6300 | 6.51e-01 [4.45e-01, 7.14e-01] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | block | 1 | 50 | 6300 | 7.03e-03 [5.62e-03, 8.09e-03] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 6300 | 4.03e-03 [3.85e-03, 4.57e-03] |
| T|federici|NCE|reve|pretrained_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 6300 | 9.88e-01 [9.77e-01, 1.05e+00] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 5670 | 8.75e-02 [4.07e-02, 1.42e-01] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 5670 | 6.25e-02 [4.81e-02, 7.98e-02] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 6300 | 7.83e-01 [7.24e-01, 8.97e-01] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 5670 | 5.63e-03 [3.50e-03, 6.99e-03] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 5670 | 3.38e-03 [2.53e-03, 3.53e-03] |
| T|federici|NCE|reve|pretrained_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 6300 | 1.02e+00 [8.50e-01, 1.08e+00] |
| T|federici|NCE|reve|random_full|full_onestep_v1|0.0003 | block | 1 | 50 | 6300 | 1.66e-01 [1.20e-01, 4.59e-01] |
| T|federici|NCE|reve|random_full|full_onestep_v1|0.0003 | non-block | 1 | 50 | 6300 | 1.72e-01 [1.66e-01, 1.75e-01] |
| T|federici|NCE|reve|random_full|full_onestep_v1|0.0003 | readout | 1 | 50 | 6300 | 4.67e-01 [4.35e-01, 5.35e-01] |
| T|federici|NCE|reve|random_full|full_onestep_v1|1e-05 | block | 1 | 50 | 6300 | 1.82e-02 [1.56e-02, 2.39e-02] |
| T|federici|NCE|reve|random_full|full_onestep_v1|1e-05 | non-block | 1 | 50 | 6300 | 6.31e-03 [6.22e-03, 6.60e-03] |
| T|federici|NCE|reve|random_full|full_onestep_v1|1e-05 | readout | 1 | 50 | 6300 | 6.46e-01 [6.27e-01, 7.06e-01] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|0.0003 | block | 6 | 45 | 5670 | 1.65e-01 [1.17e-01, 4.28e-01] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|0.0003 | non-block | 6 | 45 | 5670 | 1.33e-01 [1.30e-01, 1.48e-01] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|0.0003 | readout | 1 | 50 | 6300 | 6.04e-01 [5.88e-01, 6.82e-01] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|1e-05 | block | 6 | 45 | 5670 | 1.65e-02 [1.48e-02, 2.10e-02] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|1e-05 | non-block | 6 | 45 | 5670 | 4.43e-03 [4.37e-03, 4.57e-03] |
| T|federici|NCE|reve|random_full|warmup_then_all_v1|1e-05 | readout | 1 | 50 | 6300 | 6.79e-01 [6.60e-01, 7.43e-01] |

## Appendix: notes

- AI-PASTEEG|federici|sec/L0->L1/attention/unified/accuracy: no paired identities
- AI-RAW|federici|sec/R0->L0/attention/unified/accuracy: no paired identities
- AI-RAW|federici|sec/R1->L1/attention/unified/accuracy: no paired identities
- AI-RAW|federici|sec/R1->A/cbramod/frozen/attention/unified/accuracy: no paired identities
- AI-RAW|federici|sec/R1->A/reve/frozen/attention/unified/accuracy: no paired identities
- AI-ACCESS|federici|cbramod|sec/random_full/attention/unified/accuracy: no paired identities
- AI-ACCESS|federici|cbramod|sec/pretrained_frozen/attention/unified/accuracy: no paired identities
- AI-ACCESS|federici|cbramod|sec/pretrained_peft/attention/unified/accuracy: no paired identities
- AI-ACCESS|federici|cbramod|sec/pretrained_partial/attention/unified/accuracy: no paired identities
- AI-ACCESS|federici|cbramod|sec/pretrained_full/attention/unified/accuracy: no paired identities
- AI-POSTONLY|federici|cbramod|sec/pretrained_frozen/attention/unified/accuracy: no paired identities
- AI-POSTONLY|federici|cbramod|sec/pretrained_peft/attention/unified/accuracy: no paired identities
- AI-CONTEXT|federici|cbramod|sec/pretrained_frozen/attention/unified/accuracy: no paired identities
- AI-CONTEXT|federici|cbramod|sec/pretrained_peft/attention/unified/accuracy: no paired identities
- TF-INIT|federici|cbramod|sec/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-INIT|federici|cbramod|sec/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-INIT|federici|cbramod|sec/warmup_then_all_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-INIT|federici|cbramod|sec/warmup_then_all_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-RECIPE|federici|cbramod|sec/random_full/lr1e-05/attention/unified/accuracy: no paired identities
- TF-RECIPE|federici|cbramod|sec/random_full/lr0.0003/attention/unified/accuracy: no paired identities
- TF-RECIPE|federici|cbramod|sec/pretrained_full/lr1e-05/attention/unified/accuracy: no paired identities
- TF-RECIPE|federici|cbramod|sec/pretrained_full/lr0.0003/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/random_full/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/random_full/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/random_full/warmup_then_all_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/random_full/warmup_then_all_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/pretrained_full/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/pretrained_full/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/pretrained_full/warmup_then_all_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-VS-LEGACY|federici|cbramod|sec/pretrained_full/warmup_then_all_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->random_full/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->random_full/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->random_full/warmup_then_all_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->random_full/warmup_then_all_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->pretrained_full/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->pretrained_full/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->pretrained_full/warmup_then_all_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L0->pretrained_full/warmup_then_all_v1/lr0.0003/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L1->random_full/full_onestep_v1/lr1e-05/attention/unified/accuracy: no paired identities
- TF-LOCAL|federici|cbramod|sec/L1->random_full/full_onestep_v1/lr0.0003/attention/unified/accuracy: no paired identities
