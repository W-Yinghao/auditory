# ALN3 C_COMPLEMENT local + pretrained complement — interim results

**Interim, seed 3401 only.** Generated 2026-10-14 11:07 CEST (Slurm job 1039549) by `python -m auditory_alignment_v3.bc_interim` under the frozen `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`. Intervals are identity-level bootstrap-t (4000 replicates) conditional on the seed-3401 training; they are not training-seed uncertainty. Simultaneous intervals: max-t within the family named in each table. Sign: positive = the candidate is better (ΔR = R(reference) − R(candidate), bits per 5 s query, unified readout). Classes follow ADDENDUM_05 §7; no other interpretation is made here.

Code sha256: `bc_interim.py` 2840df81b608, `bc_interim_report.py` d0cfe6de6bcd, `sci_r1/stats.py` 8bb141cf6070.

## 0. Coverage and checks

| set | complete | other |
|---|---|---|
| C | 650 | 0 |
| L | 50 | 0 |

Identities (local reference, NCE): FAU ci 24, ha 29, th 14; DTU hi 22, nh 22; Federici CI 33, HC 37, HC-v 16. Federici phantom entities excluded: 1.
Pairing check (identical participant sets and candidate / query counts per fold): {'matched': 570}; excluded pairs: 0.

## 1. Overview: interval classes (simultaneous 95%)

| family | dataset | objective | I>0 | I<0 | contains 0 |
|---|---|---|---|---|---|
| C-LOCAL | FAU | NCE | 0 | 13 | 0 |
| C-LOCAL | FAU | CS_SINGLE | 0 | 13 | 0 |
| C-LOCAL | DTU | NCE | 0 | 13 | 0 |
| C-LOCAL | DTU | CS_SINGLE | 0 | 13 | 0 |
| C-LOCAL | Federici | NCE | 5 | 0 | 8 |
| C-LOCAL | Federici | CS_SINGLE | 0 | 0 | 13 |
| C-ATTRIB | FAU | NCE | 4 | 0 | 8 |
| C-ATTRIB | FAU | CS_SINGLE | 1 | 0 | 11 |
| C-ATTRIB | DTU | NCE | 2 | 1 | 9 |
| C-ATTRIB | DTU | CS_SINGLE | 0 | 1 | 11 |
| C-ATTRIB | Federici | NCE | 1 | 1 | 10 |
| C-ATTRIB | Federici | CS_SINGLE | 0 | 0 | 12 |
| C-FMONLY | FAU | NCE | 12 | 0 | 0 |
| C-FMONLY | FAU | CS_SINGLE | 12 | 0 | 0 |
| C-FMONLY | DTU | NCE | 12 | 0 | 0 |
| C-FMONLY | DTU | CS_SINGLE | 12 | 0 | 0 |
| C-FMONLY | Federici | NCE | 12 | 0 | 0 |
| C-FMONLY | Federici | CS_SINGLE | 12 | 0 | 0 |

## 2. Levels (unified readout)

**FAU · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 67 | 6.407 [+6.334, +6.481] | 0.046 | 0.330 | 0.636 | 6.235 | 0.532 |
| C cbramod / concat_pretrained | 67 | 6.454 [+6.395, +6.513] | 0.037 | 0.343 | 0.521 | 6.409 | 0.534 |
| C cbramod / residual_pretrained_frozen | 67 | 6.412 [+6.335, +6.489] | 0.047 | 0.330 | 0.632 | 6.251 | 0.532 |
| C cbramod / residual_pretrained_full | 67 | 6.396 [+6.322, +6.469] | 0.047 | 0.328 | 0.640 | 6.214 | 0.532 |
| C cbramod / residual_pretrained_peft | 67 | 6.397 [+6.323, +6.470] | 0.048 | 0.328 | 0.645 | 6.219 | 0.539 |
| C cbramod / residual_random_frozen | 67 | 6.398 [+6.320, +6.475] | 0.051 | 0.327 | 0.687 | 6.261 | 0.537 |
| C cbramod / residual_random_trainable | 67 | 6.389 [+6.315, +6.462] | 0.049 | 0.327 | 0.624 | 6.210 | 0.531 |
| C reve / concat_pretrained | 67 | 6.456 [+6.402, +6.511] | 0.038 | 0.346 | 0.477 | 6.407 | 0.539 |
| C reve / residual_pretrained_frozen | 67 | 6.400 [+6.313, +6.486] | 0.051 | 0.326 | 0.728 | 6.247 | 0.541 |
| C reve / residual_pretrained_full | 67 | 6.404 [+6.318, +6.491] | 0.052 | 0.329 | 0.703 | 6.196 | 0.533 |
| C reve / residual_pretrained_peft | 67 | 6.374 [+6.282, +6.466] | 0.054 | 0.321 | 0.754 | 6.209 | 0.538 |
| C reve / residual_random_frozen | 67 | 6.393 [+6.318, +6.468] | 0.051 | 0.327 | 0.685 | 6.209 | 0.535 |
| C reve / residual_random_trainable | 67 | 6.397 [+6.324, +6.470] | 0.050 | 0.327 | 0.646 | 6.238 | 0.536 |
| local `lag_local_tokens` full | 67 | 6.309 [+6.189, +6.428] | 0.066 | 0.302 | 1.044 | 6.004 | 0.547 |

**FAU · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 67 | 6.398 [+6.326, +6.470] | 0.050 | 0.327 | 0.646 | 6.374 | 0.542 |
| C cbramod / concat_pretrained | 67 | 6.423 [+6.355, +6.491] | 0.047 | 0.333 | 0.602 | 6.356 | 0.547 |
| C cbramod / residual_pretrained_frozen | 67 | 6.403 [+6.325, +6.481] | 0.048 | 0.326 | 0.676 | 6.373 | 0.541 |
| C cbramod / residual_pretrained_full | 67 | 6.405 [+6.329, +6.481] | 0.047 | 0.327 | 0.667 | 6.377 | 0.542 |
| C cbramod / residual_pretrained_peft | 67 | 6.394 [+6.315, +6.473] | 0.050 | 0.325 | 0.680 | 6.369 | 0.540 |
| C cbramod / residual_random_frozen | 67 | 6.404 [+6.334, +6.474] | 0.049 | 0.329 | 0.626 | 6.386 | 0.538 |
| C cbramod / residual_random_trainable | 67 | 6.396 [+6.323, +6.468] | 0.048 | 0.327 | 0.638 | 6.373 | 0.537 |
| C reve / concat_pretrained | 67 | 6.457 [+6.401, +6.514] | 0.041 | 0.343 | 0.524 | 6.378 | 0.543 |
| C reve / residual_pretrained_frozen | 67 | 6.398 [+6.324, +6.472] | 0.048 | 0.326 | 0.648 | 6.377 | 0.540 |
| C reve / residual_pretrained_full | 67 | 6.406 [+6.330, +6.482] | 0.049 | 0.327 | 0.674 | 6.373 | 0.545 |
| C reve / residual_pretrained_peft | 67 | 6.405 [+6.332, +6.479] | 0.048 | 0.329 | 0.645 | 6.370 | 0.538 |
| C reve / residual_random_frozen | 67 | 6.403 [+6.330, +6.476] | 0.050 | 0.327 | 0.641 | 6.368 | 0.542 |
| C reve / residual_random_trainable | 67 | 6.392 [+6.316, +6.467] | 0.049 | 0.326 | 0.634 | 6.371 | 0.539 |
| local `lag_local_tokens` full | 67 | 6.358 [+6.278, +6.438] | 0.054 | 0.317 | 0.724 | 6.340 | 0.543 |

**DTU · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 44 | 6.938 [+6.781, +7.094] | 0.064 | 0.231 | 1.914 | 6.320 | 0.666 |
| C cbramod / concat_pretrained | 44 | 7.062 [+6.911, +7.212] | 0.054 | 0.243 | 1.803 | 6.520 | 0.654 |
| C cbramod / residual_pretrained_frozen | 44 | 6.992 [+6.836, +7.147] | 0.059 | 0.236 | 1.879 | 6.431 | 0.664 |
| C cbramod / residual_pretrained_full | 44 | 6.943 [+6.779, +7.107] | 0.063 | 0.231 | 1.915 | 6.320 | 0.668 |
| C cbramod / residual_pretrained_peft | 44 | 6.936 [+6.785, +7.087] | 0.062 | 0.232 | 1.854 | 6.327 | 0.662 |
| C cbramod / residual_random_frozen | 44 | 6.983 [+6.830, +7.136] | 0.059 | 0.236 | 1.879 | 6.415 | 0.663 |
| C cbramod / residual_random_trainable | 44 | 6.978 [+6.824, +7.133] | 0.061 | 0.235 | 1.885 | 6.409 | 0.668 |
| C reve / concat_pretrained | 44 | 7.017 [+6.863, +7.170] | 0.058 | 0.241 | 1.788 | 6.542 | 0.661 |
| C reve / residual_pretrained_frozen | 44 | 6.928 [+6.771, +7.085] | 0.065 | 0.231 | 1.909 | 6.345 | 0.663 |
| C reve / residual_pretrained_full | 44 | 6.916 [+6.762, +7.070] | 0.065 | 0.229 | 1.918 | 6.352 | 0.665 |
| C reve / residual_pretrained_peft | 44 | 6.933 [+6.776, +7.091] | 0.061 | 0.231 | 1.913 | 6.396 | 0.663 |
| C reve / residual_random_frozen | 44 | 6.948 [+6.794, +7.102] | 0.063 | 0.232 | 1.893 | 6.392 | 0.664 |
| C reve / residual_random_trainable | 44 | 6.925 [+6.766, +7.083] | 0.066 | 0.229 | 1.919 | 6.295 | 0.666 |
| local `lag_local_tokens` full | 44 | 6.869 [+6.712, +7.026] | 0.066 | 0.224 | 2.009 | 6.214 | 0.668 |

**DTU · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 44 | 7.206 [+7.100, +7.312] | 0.040 | 0.272 | 1.210 | 7.273 | 0.639 |
| C cbramod / concat_pretrained | 44 | 7.152 [+7.038, +7.267] | 0.043 | 0.261 | 1.350 | 7.217 | 0.646 |
| C cbramod / residual_pretrained_frozen | 44 | 7.230 [+7.119, +7.342] | 0.039 | 0.274 | 1.232 | 7.265 | 0.642 |
| C cbramod / residual_pretrained_full | 44 | 7.215 [+7.096, +7.334] | 0.041 | 0.271 | 1.297 | 7.269 | 0.645 |
| C cbramod / residual_pretrained_peft | 44 | 7.211 [+7.091, +7.331] | 0.041 | 0.269 | 1.299 | 7.267 | 0.644 |
| C cbramod / residual_random_frozen | 44 | 7.218 [+7.109, +7.326] | 0.040 | 0.272 | 1.261 | 7.263 | 0.642 |
| C cbramod / residual_random_trainable | 44 | 7.214 [+7.103, +7.325] | 0.039 | 0.271 | 1.267 | 7.260 | 0.641 |
| C reve / concat_pretrained | 44 | 7.187 [+7.082, +7.292] | 0.038 | 0.265 | 1.280 | 7.195 | 0.641 |
| C reve / residual_pretrained_frozen | 44 | 7.215 [+7.103, +7.328] | 0.039 | 0.271 | 1.289 | 7.265 | 0.647 |
| C reve / residual_pretrained_full | 44 | 7.216 [+7.100, +7.332] | 0.039 | 0.271 | 1.291 | 7.267 | 0.644 |
| C reve / residual_pretrained_peft | 44 | 7.210 [+7.093, +7.327] | 0.041 | 0.269 | 1.294 | 7.269 | 0.643 |
| C reve / residual_random_frozen | 44 | 7.218 [+7.103, +7.334] | 0.040 | 0.271 | 1.252 | 7.270 | 0.644 |
| C reve / residual_random_trainable | 44 | 7.230 [+7.118, +7.341] | 0.041 | 0.274 | 1.212 | 7.271 | 0.640 |
| local `lag_local_tokens` full | 44 | 7.108 [+6.986, +7.230] | 0.047 | 0.255 | 1.381 | 7.205 | 0.651 |

**Federici · NCE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 86 | 8.056 [+8.021, +8.090] | 0.012 | 0.390 | 0.264 | 8.001 | – |
| C cbramod / concat_pretrained | 86 | 8.059 [+8.027, +8.091] | 0.012 | 0.392 | 0.253 | 8.013 | – |
| C cbramod / residual_pretrained_frozen | 86 | 8.056 [+8.021, +8.091] | 0.012 | 0.390 | 0.264 | 8.001 | – |
| C cbramod / residual_pretrained_full | 86 | 8.056 [+8.022, +8.090] | 0.012 | 0.390 | 0.264 | 8.003 | – |
| C cbramod / residual_pretrained_peft | 86 | 8.056 [+8.022, +8.089] | 0.012 | 0.390 | 0.264 | 8.000 | – |
| C cbramod / residual_random_frozen | 86 | 8.056 [+8.022, +8.090] | 0.012 | 0.390 | 0.265 | 8.002 | – |
| C cbramod / residual_random_trainable | 86 | 8.053 [+8.019, +8.087] | 0.012 | 0.389 | 0.267 | 8.026 | – |
| C reve / concat_pretrained | 86 | 8.071 [+8.042, +8.101] | 0.008 | 0.397 | 0.236 | 8.060 | – |
| C reve / residual_pretrained_frozen | 86 | 8.055 [+8.021, +8.090] | 0.012 | 0.390 | 0.264 | 8.004 | – |
| C reve / residual_pretrained_full | 86 | 8.056 [+8.021, +8.090] | 0.012 | 0.390 | 0.265 | 8.003 | – |
| C reve / residual_pretrained_peft | 86 | 8.056 [+8.022, +8.089] | 0.012 | 0.390 | 0.264 | 8.005 | – |
| C reve / residual_random_frozen | 86 | 8.056 [+8.022, +8.091] | 0.011 | 0.390 | 0.264 | 8.039 | – |
| C reve / residual_random_trainable | 86 | 8.056 [+8.021, +8.090] | 0.012 | 0.390 | 0.264 | 8.002 | – |
| local `lag_local_tokens` full | 86 | 8.056 [+8.022, +8.090] | 0.012 | 0.390 | 0.264 | 7.999 | – |

**Federici · CS_SINGLE**

| configuration | n | R [95% CI] | top1 | rank% | gain | R_native | att acc |
|---|---|---|---|---|---|---|---|
| C - / residual_small_capacity | 86 | 8.082 [+8.049, +8.116] | 0.010 | 0.398 | 0.213 | 8.170 | – |
| C cbramod / concat_pretrained | 86 | 8.070 [+8.038, +8.102] | 0.012 | 0.397 | 0.209 | 8.170 | – |
| C cbramod / residual_pretrained_frozen | 86 | 8.074 [+8.040, +8.108] | 0.012 | 0.395 | 0.226 | 8.170 | – |
| C cbramod / residual_pretrained_full | 86 | 8.077 [+8.044, +8.109] | 0.012 | 0.396 | 0.225 | 8.170 | – |
| C cbramod / residual_pretrained_peft | 86 | 8.075 [+8.040, +8.109] | 0.014 | 0.394 | 0.221 | 8.170 | – |
| C cbramod / residual_random_frozen | 86 | 8.078 [+8.043, +8.112] | 0.012 | 0.397 | 0.228 | 8.170 | – |
| C cbramod / residual_random_trainable | 86 | 8.079 [+8.046, +8.112] | 0.013 | 0.397 | 0.213 | 8.170 | – |
| C reve / concat_pretrained | 86 | 8.074 [+8.040, +8.107] | 0.010 | 0.394 | 0.219 | 8.169 | – |
| C reve / residual_pretrained_frozen | 86 | 8.079 [+8.045, +8.113] | 0.011 | 0.397 | 0.225 | 8.170 | – |
| C reve / residual_pretrained_full | 86 | 8.079 [+8.045, +8.114] | 0.011 | 0.397 | 0.225 | 8.170 | – |
| C reve / residual_pretrained_peft | 86 | 8.075 [+8.041, +8.109] | 0.011 | 0.395 | 0.230 | 8.170 | – |
| C reve / residual_random_frozen | 86 | 8.075 [+8.039, +8.110] | 0.010 | 0.395 | 0.245 | 8.170 | – |
| C reve / residual_random_trainable | 86 | 8.075 [+8.041, +8.109] | 0.010 | 0.395 | 0.229 | 8.170 | – |
| local `lag_local_tokens` full | 86 | 8.077 [+8.045, +8.109] | 0.012 | 0.396 | 0.221 | 8.170 | – |

## 3. Primary increment R(local) − R(combined): local base → C variant (and → capacity control)

**FAU · NCE** (family `C-LOCAL|fau|NCE`, critical value 2.38)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 67 | -0.145 | [-0.209, -0.081] | [-0.221, -0.069] | I<0 | -0.028 | -0.041 | -0.523 | -0.404 | -0.012 |
| cbramod/residual_pretrained_frozen | primary increment | 67 | -0.103 | [-0.152, -0.054] | [-0.160, -0.046] | I<0 | -0.019 | -0.028 | -0.412 | -0.247 | -0.015 |
| cbramod/residual_pretrained_peft | primary increment | 67 | -0.088 | [-0.138, -0.038] | [-0.148, -0.028] | I<0 | -0.018 | -0.026 | -0.399 | -0.215 | -0.008 |
| cbramod/residual_pretrained_full | primary increment | 67 | -0.087 | [-0.137, -0.036] | [-0.147, -0.027] | I<0 | -0.019 | -0.026 | -0.404 | -0.210 | -0.015 |
| cbramod/residual_random_frozen | primary increment | 67 | -0.089 | [-0.136, -0.043] | [-0.144, -0.034] | I<0 | -0.015 | -0.026 | -0.357 | -0.257 | -0.010 |
| cbramod/residual_random_trainable | primary increment | 67 | -0.080 | [-0.132, -0.028] | [-0.142, -0.018] | I<0 | -0.017 | -0.026 | -0.420 | -0.205 | -0.016 |
| reve/concat_pretrained | primary increment | 67 | -0.148 | [-0.215, -0.080] | [-0.228, -0.068] | I<0 | -0.028 | -0.044 | -0.568 | -0.402 | -0.008 |
| reve/residual_pretrained_frozen | primary increment | 67 | -0.091 | [-0.128, -0.054] | [-0.135, -0.047] | I<0 | -0.015 | -0.024 | -0.316 | -0.242 | -0.006 |
| reve/residual_pretrained_peft | primary increment | 67 | -0.065 | [-0.100, -0.030] | [-0.107, -0.023] | I<0 | -0.012 | -0.019 | -0.291 | -0.205 | -0.009 |
| reve/residual_pretrained_full | primary increment | 67 | -0.096 | [-0.140, -0.052] | [-0.149, -0.043] | I<0 | -0.014 | -0.028 | -0.341 | -0.192 | -0.014 |
| reve/residual_random_frozen | primary increment | 67 | -0.084 | [-0.135, -0.033] | [-0.143, -0.025] | I<0 | -0.015 | -0.025 | -0.360 | -0.205 | -0.012 |
| reve/residual_random_trainable | primary increment | 67 | -0.088 | [-0.143, -0.034] | [-0.152, -0.025] | I<0 | -0.016 | -0.026 | -0.398 | -0.234 | -0.011 |
| -/residual_small_capacity | primary increment (capacity control) | 67 | -0.099 | [-0.150, -0.048] | [-0.160, -0.038] | I<0 | -0.020 | -0.029 | -0.408 | -0.231 | -0.015 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| cbramod/concat_pretrained | +0.052 [-0.061, +0.165] (n=24) | -0.275 [-0.340, -0.209] (n=29) | -0.215 [-0.335, -0.094] (n=14) |
| cbramod/residual_pretrained_frozen | +0.036 [-0.047, +0.119] (n=24) | -0.198 [-0.251, -0.146] (n=29) | -0.144 [-0.248, -0.040] (n=14) |
| cbramod/residual_pretrained_peft | +0.067 [-0.025, +0.160] (n=24) | -0.192 [-0.242, -0.143] (n=29) | -0.139 [-0.226, -0.052] (n=14) |
| cbramod/residual_pretrained_full | +0.073 [-0.016, +0.162] (n=24) | -0.198 [-0.251, -0.145] (n=29) | -0.131 [-0.215, -0.046] (n=14) |
| cbramod/residual_random_frozen | +0.051 [-0.033, +0.135] (n=24) | -0.177 [-0.224, -0.130] (n=29) | -0.148 [-0.243, -0.053] (n=14) |
| cbramod/residual_random_trainable | +0.083 [-0.008, +0.175] (n=24) | -0.188 [-0.245, -0.132] (n=29) | -0.137 [-0.231, -0.043] (n=14) |
| reve/concat_pretrained | +0.063 [-0.051, +0.177] (n=24) | -0.284 [-0.354, -0.214] (n=29) | -0.227 [-0.365, -0.089] (n=14) |
| reve/residual_pretrained_frozen | +0.021 [-0.041, +0.083] (n=24) | -0.162 [-0.202, -0.122] (n=29) | -0.136 [-0.219, -0.053] (n=14) |
| reve/residual_pretrained_peft | +0.048 [-0.010, +0.106] (n=24) | -0.139 [-0.177, -0.101] (n=29) | -0.107 [-0.188, -0.027] (n=14) |
| reve/residual_pretrained_full | +0.033 [-0.042, +0.109] (n=24) | -0.187 [-0.244, -0.130] (n=29) | -0.129 [-0.205, -0.053] (n=14) |
| reve/residual_random_frozen | +0.075 [-0.008, +0.158] (n=24) | -0.185 [-0.240, -0.130] (n=29) | -0.148 [-0.244, -0.052] (n=14) |
| reve/residual_random_trainable | +0.076 [-0.012, +0.163] (n=24) | -0.195 [-0.258, -0.133] (n=29) | -0.148 [-0.252, -0.043] (n=14) |
| -/residual_small_capacity | +0.059 [-0.037, +0.155] (n=24) | -0.204 [-0.254, -0.154] (n=29) | -0.151 [-0.247, -0.055] (n=14) |

**FAU · CS_SINGLE** (family `C-LOCAL|fau|CS_SINGLE`, critical value 2.78)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 67 | -0.065 | [-0.084, -0.047] | [-0.091, -0.039] | I<0 | -0.006 | -0.017 | -0.123 | -0.016 | +0.004 |
| cbramod/residual_pretrained_frozen | primary increment | 67 | -0.045 | [-0.059, -0.031] | [-0.063, -0.027] | I<0 | -0.006 | -0.009 | -0.048 | -0.032 | -0.002 |
| cbramod/residual_pretrained_peft | primary increment | 67 | -0.036 | [-0.047, -0.025] | [-0.052, -0.020] | I<0 | -0.004 | -0.008 | -0.044 | -0.028 | -0.002 |
| cbramod/residual_pretrained_full | primary increment | 67 | -0.047 | [-0.059, -0.035] | [-0.064, -0.030] | I<0 | -0.007 | -0.010 | -0.057 | -0.037 | -0.001 |
| cbramod/residual_random_frozen | primary increment | 67 | -0.046 | [-0.061, -0.031] | [-0.068, -0.024] | I<0 | -0.005 | -0.012 | -0.098 | -0.046 | -0.005 |
| cbramod/residual_random_trainable | primary increment | 67 | -0.038 | [-0.054, -0.021] | [-0.061, -0.015] | I<0 | -0.005 | -0.010 | -0.086 | -0.033 | -0.006 |
| reve/concat_pretrained | primary increment | 67 | -0.099 | [-0.125, -0.073] | [-0.136, -0.062] | I<0 | -0.013 | -0.026 | -0.200 | -0.038 | +0.000 |
| reve/residual_pretrained_frozen | primary increment | 67 | -0.040 | [-0.053, -0.027] | [-0.059, -0.021] | I<0 | -0.006 | -0.010 | -0.076 | -0.037 | -0.003 |
| reve/residual_pretrained_peft | primary increment | 67 | -0.047 | [-0.064, -0.031] | [-0.071, -0.023] | I<0 | -0.006 | -0.012 | -0.079 | -0.030 | -0.005 |
| reve/residual_pretrained_full | primary increment | 67 | -0.048 | [-0.059, -0.037] | [-0.063, -0.033] | I<0 | -0.005 | -0.010 | -0.051 | -0.033 | +0.002 |
| reve/residual_random_frozen | primary increment | 67 | -0.045 | [-0.063, -0.027] | [-0.070, -0.020] | I<0 | -0.004 | -0.010 | -0.083 | -0.027 | -0.000 |
| reve/residual_random_trainable | primary increment | 67 | -0.034 | [-0.047, -0.020] | [-0.053, -0.015] | I<0 | -0.005 | -0.009 | -0.090 | -0.030 | -0.004 |
| -/residual_small_capacity | primary increment (capacity control) | 67 | -0.040 | [-0.055, -0.025] | [-0.061, -0.019] | I<0 | -0.004 | -0.011 | -0.079 | -0.034 | -0.001 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | ci | ha | th |
|---|---|---|---|
| cbramod/concat_pretrained | -0.027 [-0.066, +0.012] (n=24) | -0.097 [-0.119, -0.075] (n=29) | -0.065 [-0.096, -0.033] (n=14) |
| cbramod/residual_pretrained_frozen | -0.026 [-0.053, +0.001] (n=24) | -0.065 [-0.086, -0.043] (n=29) | -0.037 [-0.054, -0.020] (n=14) |
| cbramod/residual_pretrained_peft | -0.019 [-0.036, -0.002] (n=24) | -0.048 [-0.070, -0.027] (n=29) | -0.040 [-0.060, -0.021] (n=14) |
| cbramod/residual_pretrained_full | -0.026 [-0.048, -0.004] (n=24) | -0.062 [-0.081, -0.043] (n=29) | -0.052 [-0.071, -0.033] (n=14) |
| cbramod/residual_random_frozen | -0.018 [-0.051, +0.015] (n=24) | -0.072 [-0.091, -0.053] (n=29) | -0.039 [-0.063, -0.015] (n=14) |
| cbramod/residual_random_trainable | -0.007 [-0.041, +0.027] (n=24) | -0.061 [-0.083, -0.040] (n=29) | -0.041 [-0.074, -0.008] (n=14) |
| reve/concat_pretrained | -0.034 [-0.085, +0.018] (n=24) | -0.144 [-0.175, -0.112] (n=29) | -0.120 [-0.171, -0.068] (n=14) |
| reve/residual_pretrained_frozen | -0.009 [-0.036, +0.018] (n=24) | -0.066 [-0.083, -0.048] (n=29) | -0.039 [-0.057, -0.022] (n=14) |
| reve/residual_pretrained_peft | -0.014 [-0.046, +0.018] (n=24) | -0.075 [-0.101, -0.049] (n=29) | -0.047 [-0.077, -0.017] (n=14) |
| reve/residual_pretrained_full | -0.035 [-0.057, -0.014] (n=24) | -0.056 [-0.072, -0.040] (n=29) | -0.053 [-0.076, -0.030] (n=14) |
| reve/residual_random_frozen | -0.008 [-0.034, +0.017] (n=24) | -0.078 [-0.112, -0.044] (n=29) | -0.040 [-0.064, -0.016] (n=14) |
| reve/residual_random_trainable | -0.014 [-0.044, +0.015] (n=24) | -0.050 [-0.068, -0.032] (n=29) | -0.033 [-0.056, -0.009] (n=14) |
| -/residual_small_capacity | -0.007 [-0.043, +0.029] (n=24) | -0.070 [-0.087, -0.052] (n=29) | -0.035 [-0.054, -0.016] (n=14) |

**DTU · NCE** (family `C-LOCAL|dtu|NCE`, critical value 2.78)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 44 | -0.192 | [-0.231, -0.154] | [-0.245, -0.140] | I<0 | -0.013 | -0.019 | -0.206 | -0.306 | -0.014 |
| cbramod/residual_pretrained_frozen | primary increment | 44 | -0.122 | [-0.154, -0.091] | [-0.165, -0.079] | I<0 | -0.007 | -0.013 | -0.130 | -0.217 | -0.004 |
| cbramod/residual_pretrained_peft | primary increment | 44 | -0.067 | [-0.093, -0.041] | [-0.102, -0.031] | I<0 | -0.004 | -0.009 | -0.154 | -0.113 | -0.005 |
| cbramod/residual_pretrained_full | primary increment | 44 | -0.074 | [-0.100, -0.048] | [-0.110, -0.038] | I<0 | -0.003 | -0.008 | -0.094 | -0.106 | +0.000 |
| cbramod/residual_random_frozen | primary increment | 44 | -0.114 | [-0.144, -0.083] | [-0.156, -0.072] | I<0 | -0.007 | -0.012 | -0.130 | -0.201 | -0.004 |
| cbramod/residual_random_trainable | primary increment | 44 | -0.109 | [-0.140, -0.078] | [-0.151, -0.067] | I<0 | -0.005 | -0.012 | -0.124 | -0.195 | -0.000 |
| reve/concat_pretrained | primary increment | 44 | -0.147 | [-0.183, -0.111] | [-0.195, -0.099] | I<0 | -0.008 | -0.017 | -0.220 | -0.328 | -0.006 |
| reve/residual_pretrained_frozen | primary increment | 44 | -0.059 | [-0.077, -0.040] | [-0.084, -0.033] | I<0 | -0.001 | -0.007 | -0.100 | -0.131 | -0.004 |
| reve/residual_pretrained_peft | primary increment | 44 | -0.064 | [-0.086, -0.042] | [-0.094, -0.034] | I<0 | -0.005 | -0.007 | -0.096 | -0.182 | -0.004 |
| reve/residual_pretrained_full | primary increment | 44 | -0.047 | [-0.066, -0.027] | [-0.073, -0.020] | I<0 | -0.001 | -0.005 | -0.090 | -0.138 | -0.002 |
| reve/residual_random_frozen | primary increment | 44 | -0.079 | [-0.105, -0.052] | [-0.115, -0.042] | I<0 | -0.003 | -0.009 | -0.115 | -0.178 | -0.003 |
| reve/residual_random_trainable | primary increment | 44 | -0.056 | [-0.077, -0.034] | [-0.085, -0.026] | I<0 | -0.000 | -0.006 | -0.090 | -0.081 | -0.001 |
| -/residual_small_capacity | primary increment (capacity control) | 44 | -0.068 | [-0.088, -0.049] | [-0.097, -0.040] | I<0 | -0.002 | -0.007 | -0.094 | -0.106 | -0.001 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| cbramod/concat_pretrained | -0.229 [-0.294, -0.164] (n=22) | -0.156 [-0.203, -0.109] (n=22) |
| cbramod/residual_pretrained_frozen | -0.155 [-0.200, -0.109] (n=22) | -0.090 [-0.131, -0.048] (n=22) |
| cbramod/residual_pretrained_peft | -0.094 [-0.130, -0.057] (n=22) | -0.040 [-0.078, -0.001] (n=22) |
| cbramod/residual_pretrained_full | -0.104 [-0.141, -0.067] (n=22) | -0.044 [-0.082, -0.006] (n=22) |
| cbramod/residual_random_frozen | -0.148 [-0.196, -0.100] (n=22) | -0.080 [-0.117, -0.043] (n=22) |
| cbramod/residual_random_trainable | -0.145 [-0.191, -0.098] (n=22) | -0.074 [-0.110, -0.037] (n=22) |
| reve/concat_pretrained | -0.170 [-0.221, -0.119] (n=22) | -0.125 [-0.178, -0.072] (n=22) |
| reve/residual_pretrained_frozen | -0.079 [-0.104, -0.054] (n=22) | -0.038 [-0.065, -0.011] (n=22) |
| reve/residual_pretrained_peft | -0.086 [-0.116, -0.055] (n=22) | -0.042 [-0.073, -0.011] (n=22) |
| reve/residual_pretrained_full | -0.066 [-0.095, -0.037] (n=22) | -0.027 [-0.052, -0.002] (n=22) |
| reve/residual_random_frozen | -0.106 [-0.144, -0.067] (n=22) | -0.052 [-0.087, -0.016] (n=22) |
| reve/residual_random_trainable | -0.078 [-0.107, -0.049] (n=22) | -0.033 [-0.065, -0.002] (n=22) |
| -/residual_small_capacity | -0.091 [-0.121, -0.061] (n=22) | -0.046 [-0.074, -0.018] (n=22) |

**DTU · CS_SINGLE** (family `C-LOCAL|dtu|CS_SINGLE`, critical value 2.93)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 44 | -0.045 | [-0.069, -0.021] | [-0.078, -0.012] | I<0 | -0.004 | -0.006 | -0.031 | -0.012 | -0.005 |
| cbramod/residual_pretrained_frozen | primary increment | 44 | -0.122 | [-0.146, -0.099] | [-0.156, -0.088] | I<0 | -0.008 | -0.019 | -0.149 | -0.059 | -0.009 |
| cbramod/residual_pretrained_peft | primary increment | 44 | -0.103 | [-0.122, -0.085] | [-0.130, -0.076] | I<0 | -0.006 | -0.014 | -0.082 | -0.062 | -0.007 |
| cbramod/residual_pretrained_full | primary increment | 44 | -0.107 | [-0.126, -0.089] | [-0.134, -0.080] | I<0 | -0.006 | -0.016 | -0.084 | -0.064 | -0.006 |
| cbramod/residual_random_frozen | primary increment | 44 | -0.110 | [-0.131, -0.089] | [-0.140, -0.081] | I<0 | -0.007 | -0.017 | -0.119 | -0.058 | -0.009 |
| cbramod/residual_random_trainable | primary increment | 44 | -0.106 | [-0.127, -0.085] | [-0.136, -0.076] | I<0 | -0.008 | -0.016 | -0.114 | -0.055 | -0.010 |
| reve/concat_pretrained | primary increment | 44 | -0.079 | [-0.105, -0.054] | [-0.116, -0.043] | I<0 | -0.010 | -0.010 | -0.101 | +0.010 | -0.010 |
| reve/residual_pretrained_frozen | primary increment | 44 | -0.108 | [-0.127, -0.089] | [-0.135, -0.080] | I<0 | -0.009 | -0.016 | -0.091 | -0.060 | -0.004 |
| reve/residual_pretrained_peft | primary increment | 44 | -0.102 | [-0.120, -0.085] | [-0.128, -0.076] | I<0 | -0.007 | -0.014 | -0.086 | -0.063 | -0.008 |
| reve/residual_pretrained_full | primary increment | 44 | -0.108 | [-0.128, -0.089] | [-0.136, -0.080] | I<0 | -0.008 | -0.016 | -0.089 | -0.061 | -0.007 |
| reve/residual_random_frozen | primary increment | 44 | -0.111 | [-0.130, -0.091] | [-0.139, -0.083] | I<0 | -0.007 | -0.016 | -0.129 | -0.065 | -0.007 |
| reve/residual_random_trainable | primary increment | 44 | -0.122 | [-0.146, -0.098] | [-0.156, -0.088] | I<0 | -0.007 | -0.019 | -0.168 | -0.065 | -0.011 |
| -/residual_small_capacity | primary increment (capacity control) | 44 | -0.099 | [-0.124, -0.073] | [-0.136, -0.062] | I<0 | -0.007 | -0.017 | -0.171 | -0.068 | -0.012 |

Per group (descriptive, pointwise; n < 5 → n only):

| member | hi | nh |
|---|---|---|
| cbramod/concat_pretrained | -0.062 [-0.108, -0.016] (n=22) | -0.027 [-0.049, -0.006] (n=22) |
| cbramod/residual_pretrained_frozen | -0.163 [-0.194, -0.131] (n=22) | -0.082 [-0.110, -0.054] (n=22) |
| cbramod/residual_pretrained_peft | -0.122 [-0.152, -0.092] (n=22) | -0.085 [-0.107, -0.062] (n=22) |
| cbramod/residual_pretrained_full | -0.128 [-0.158, -0.097] (n=22) | -0.087 [-0.110, -0.064] (n=22) |
| cbramod/residual_random_frozen | -0.144 [-0.175, -0.113] (n=22) | -0.076 [-0.095, -0.057] (n=22) |
| cbramod/residual_random_trainable | -0.140 [-0.171, -0.108] (n=22) | -0.073 [-0.094, -0.051] (n=22) |
| reve/concat_pretrained | -0.100 [-0.145, -0.055] (n=22) | -0.059 [-0.083, -0.035] (n=22) |
| reve/residual_pretrained_frozen | -0.134 [-0.163, -0.105] (n=22) | -0.081 [-0.102, -0.061] (n=22) |
| reve/residual_pretrained_peft | -0.125 [-0.151, -0.099] (n=22) | -0.079 [-0.102, -0.057] (n=22) |
| reve/residual_pretrained_full | -0.133 [-0.163, -0.102] (n=22) | -0.084 [-0.107, -0.060] (n=22) |
| reve/residual_random_frozen | -0.135 [-0.165, -0.104] (n=22) | -0.087 [-0.109, -0.065] (n=22) |
| reve/residual_random_trainable | -0.153 [-0.189, -0.118] (n=22) | -0.090 [-0.117, -0.064] (n=22) |
| -/residual_small_capacity | -0.130 [-0.170, -0.090] (n=22) | -0.067 [-0.104, -0.030] (n=22) |

**Federici · NCE** (family `C-LOCAL|federici|NCE`, critical value 3.13)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 86 | -0.003 | [-0.008, +0.002] | [-0.011, +0.005] | contains 0 | +0.001 | -0.001 | -0.011 | -0.014 | – |
| cbramod/residual_pretrained_frozen | primary increment | 86 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | I>0 | +0.000 | +0.000 | +0.000 | -0.002 | – |
| cbramod/residual_pretrained_peft | primary increment | 86 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | I>0 | +0.000 | +0.000 | +0.000 | -0.001 | – |
| cbramod/residual_pretrained_full | primary increment | 86 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | I>0 | +0.000 | +0.000 | +0.000 | -0.004 | – |
| cbramod/residual_random_frozen | primary increment | 86 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 | +0.001 | -0.003 | – |
| cbramod/residual_random_trainable | primary increment | 86 | +0.003 | [+0.001, +0.005] | [+0.000, +0.006] | I>0 | +0.000 | +0.001 | +0.003 | -0.027 | – |
| reve/concat_pretrained | primary increment | 86 | -0.016 | [-0.027, -0.004] | [-0.033, +0.002] | contains 0 | -0.004 | -0.007 | -0.028 | -0.061 | – |
| reve/residual_pretrained_frozen | primary increment | 86 | +0.001 | [+0.000, +0.002] | [-0.000, +0.002] | contains 0 | +0.000 | +0.000 | -0.000 | -0.005 | – |
| reve/residual_pretrained_peft | primary increment | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | +0.000 | -0.006 | – |
| reve/residual_pretrained_full | primary increment | 86 | +0.000 | [-0.000, +0.001] | [-0.000, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 | -0.004 | – |
| reve/residual_random_frozen | primary increment | 86 | -0.000 | [-0.003, +0.002] | [-0.004, +0.003] | contains 0 | -0.001 | +0.000 | -0.000 | -0.040 | – |
| reve/residual_random_trainable | primary increment | 86 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 | +0.000 | +0.000 | -0.003 | – |
| -/residual_small_capacity | primary increment (capacity control) | 86 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | I>0 | +0.000 | +0.000 | +0.000 | -0.002 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| cbramod/concat_pretrained | +0.000 [-0.009, +0.009] (n=33) | -0.006 [-0.014, +0.003] (n=37) | -0.003 [-0.009, +0.004] (n=16) |
| cbramod/residual_pretrained_frozen | +0.000 [+0.000, +0.000] (n=33) | +0.000 [+0.000, +0.000] (n=37) | +0.000 [-0.000, +0.000] (n=16) |
| cbramod/residual_pretrained_peft | +0.000 [+0.000, +0.000] (n=33) | +0.000 [+0.000, +0.000] (n=37) | +0.000 [-0.000, +0.000] (n=16) |
| cbramod/residual_pretrained_full | +0.000 [-0.000, +0.000] (n=33) | +0.000 [+0.000, +0.000] (n=37) | +0.000 [-0.000, +0.000] (n=16) |
| cbramod/residual_random_frozen | -0.000 [-0.001, +0.001] (n=33) | +0.001 [-0.001, +0.002] (n=37) | -0.001 [-0.002, -0.000] (n=16) |
| cbramod/residual_random_trainable | +0.002 [-0.001, +0.006] (n=33) | +0.004 [-0.001, +0.008] (n=37) | +0.003 [-0.001, +0.007] (n=16) |
| reve/concat_pretrained | -0.016 [-0.040, +0.008] (n=33) | -0.026 [-0.037, -0.016] (n=37) | +0.011 [-0.039, +0.060] (n=16) |
| reve/residual_pretrained_frozen | +0.001 [-0.001, +0.002] (n=33) | +0.000 [-0.001, +0.002] (n=37) | +0.002 [-0.000, +0.004] (n=16) |
| reve/residual_pretrained_peft | -0.000 [-0.000, +0.000] (n=33) | +0.000 [-0.000, +0.001] (n=37) | +0.000 [-0.001, +0.001] (n=16) |
| reve/residual_pretrained_full | -0.000 [-0.001, +0.001] (n=33) | +0.001 [+0.000, +0.001] (n=37) | +0.000 [-0.000, +0.001] (n=16) |
| reve/residual_random_frozen | -0.000 [-0.005, +0.004] (n=33) | +0.001 [-0.002, +0.004] (n=37) | -0.003 [-0.008, +0.001] (n=16) |
| reve/residual_random_trainable | -0.000 [-0.001, +0.001] (n=33) | +0.000 [-0.001, +0.001] (n=37) | +0.000 [-0.001, +0.001] (n=16) |
| -/residual_small_capacity | +0.000 [+0.000, +0.000] (n=33) | +0.000 [+0.000, +0.000] (n=37) | -0.000 [-0.000, +0.000] (n=16) |

**Federici · CS_SINGLE** (family `C-LOCAL|federici|CS_SINGLE`, critical value 2.83)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cbramod/concat_pretrained | primary increment | 86 | +0.006 | [-0.003, +0.016] | [-0.007, +0.020] | contains 0 | +0.001 | -0.001 | -0.012 | +0.000 | – |
| cbramod/residual_pretrained_frozen | primary increment | 86 | +0.003 | [-0.001, +0.006] | [-0.003, +0.008] | contains 0 | -0.000 | +0.001 | +0.005 | -0.000 | – |
| cbramod/residual_pretrained_peft | primary increment | 86 | +0.002 | [-0.005, +0.008] | [-0.008, +0.011] | contains 0 | +0.003 | +0.002 | -0.000 | -0.001 | – |
| cbramod/residual_pretrained_full | primary increment | 86 | +0.000 | [-0.005, +0.005] | [-0.007, +0.007] | contains 0 | -0.000 | +0.000 | +0.004 | +0.000 | – |
| cbramod/residual_random_frozen | primary increment | 86 | -0.001 | [-0.011, +0.008] | [-0.015, +0.012] | contains 0 | +0.001 | -0.001 | +0.008 | -0.000 | – |
| cbramod/residual_random_trainable | primary increment | 86 | -0.003 | [-0.010, +0.005] | [-0.013, +0.008] | contains 0 | +0.001 | -0.001 | -0.008 | -0.000 | – |
| reve/concat_pretrained | primary increment | 86 | +0.003 | [-0.003, +0.010] | [-0.006, +0.012] | contains 0 | -0.002 | +0.002 | -0.002 | +0.000 | – |
| reve/residual_pretrained_frozen | primary increment | 86 | -0.003 | [-0.010, +0.005] | [-0.013, +0.008] | contains 0 | -0.001 | -0.001 | +0.004 | -0.000 | – |
| reve/residual_pretrained_peft | primary increment | 86 | +0.002 | [-0.006, +0.009] | [-0.009, +0.012] | contains 0 | -0.001 | +0.001 | +0.009 | -0.000 | – |
| reve/residual_pretrained_full | primary increment | 86 | -0.003 | [-0.010, +0.005] | [-0.013, +0.008] | contains 0 | -0.001 | -0.001 | +0.004 | -0.000 | – |
| reve/residual_random_frozen | primary increment | 86 | +0.002 | [-0.004, +0.008] | [-0.007, +0.011] | contains 0 | -0.002 | +0.001 | +0.024 | -0.000 | – |
| reve/residual_random_trainable | primary increment | 86 | +0.002 | [-0.006, +0.009] | [-0.009, +0.012] | contains 0 | -0.001 | +0.001 | +0.008 | -0.000 | – |
| -/residual_small_capacity | primary increment (capacity control) | 86 | -0.006 | [-0.014, +0.002] | [-0.017, +0.006] | contains 0 | -0.002 | -0.002 | -0.008 | -0.001 | – |

Per group (descriptive, pointwise; n < 5 → n only):

| member | CI | HC | HC-v |
|---|---|---|---|
| cbramod/concat_pretrained | +0.021 [+0.005, +0.037] (n=33) | +0.002 [-0.013, +0.016] (n=37) | -0.012 [-0.030, +0.006] (n=16) |
| cbramod/residual_pretrained_frozen | +0.002 [-0.004, +0.009] (n=33) | +0.003 [-0.003, +0.010] (n=37) | +0.001 [-0.001, +0.004] (n=16) |
| cbramod/residual_pretrained_peft | +0.007 [-0.004, +0.019] (n=33) | +0.004 [-0.006, +0.013] (n=37) | -0.014 [-0.038, +0.010] (n=16) |
| cbramod/residual_pretrained_full | +0.002 [-0.010, +0.013] (n=33) | -0.002 [-0.008, +0.005] (n=37) | +0.001 [-0.003, +0.005] (n=16) |
| cbramod/residual_random_frozen | +0.009 [-0.006, +0.023] (n=33) | -0.007 [-0.021, +0.008] (n=37) | -0.009 [-0.037, +0.018] (n=16) |
| cbramod/residual_random_trainable | +0.001 [-0.010, +0.012] (n=33) | -0.003 [-0.014, +0.008] (n=37) | -0.009 [-0.036, +0.017] (n=16) |
| reve/concat_pretrained | +0.005 [-0.005, +0.016] (n=33) | +0.005 [-0.007, +0.017] (n=37) | -0.005 [-0.017, +0.006] (n=16) |
| reve/residual_pretrained_frozen | +0.004 [-0.006, +0.015] (n=33) | -0.005 [-0.017, +0.008] (n=37) | -0.012 [-0.033, +0.008] (n=16) |
| reve/residual_pretrained_peft | +0.009 [-0.005, +0.022] (n=33) | -0.001 [-0.012, +0.011] (n=37) | -0.008 [-0.026, +0.010] (n=16) |
| reve/residual_pretrained_full | +0.004 [-0.006, +0.015] (n=33) | -0.005 [-0.018, +0.009] (n=37) | -0.013 [-0.033, +0.008] (n=16) |
| reve/residual_random_frozen | +0.007 [-0.004, +0.017] (n=33) | +0.002 [-0.006, +0.011] (n=37) | -0.008 [-0.028, +0.011] (n=16) |
| reve/residual_random_trainable | +0.011 [+0.001, +0.022] (n=33) | -0.002 [-0.014, +0.009] (n=37) | -0.009 [-0.032, +0.013] (n=16) |
| -/residual_small_capacity | +0.005 [-0.005, +0.015] (n=33) | -0.013 [-0.026, +0.001] (n=37) | -0.012 [-0.040, +0.017] (n=16) |

### 3a. Mismatched-only check (docs/06)

Δgain = gain(candidate) − gain(local), Δ mismatched logloss = candidate − local (pointwise 95%). Flag = Δgain interval > 0 while the ΔR simultaneous interval does not lie above 0.

| cell | ΔR class | Δgain [95% CI] | Δ mismatched logloss [95% CI] | mismatched-only |
|---|---|---|---|---|
| fau|NCE|cbramod/concat_pretrained | I<0 | -0.523 [-0.587, -0.459] | -0.378 [-0.401, -0.355] | no |
| fau|NCE|cbramod/residual_pretrained_frozen | I<0 | -0.412 [-0.469, -0.354] | -0.309 [-0.336, -0.282] | no |
| fau|NCE|cbramod/residual_pretrained_peft | I<0 | -0.399 [-0.451, -0.347] | -0.311 [-0.327, -0.295] | no |
| fau|NCE|cbramod/residual_pretrained_full | I<0 | -0.404 [-0.459, -0.350] | -0.317 [-0.337, -0.298] | no |
| fau|NCE|cbramod/residual_random_frozen | I<0 | -0.357 [-0.403, -0.311] | -0.268 [-0.288, -0.247] | no |
| fau|NCE|cbramod/residual_random_trainable | I<0 | -0.420 [-0.474, -0.367] | -0.340 [-0.359, -0.322] | no |
| fau|NCE|reve/concat_pretrained | I<0 | -0.568 [-0.632, -0.503] | -0.420 [-0.441, -0.398] | no |
| fau|NCE|reve/residual_pretrained_frozen | I<0 | -0.316 [-0.357, -0.275] | -0.225 [-0.245, -0.204] | no |
| fau|NCE|reve/residual_pretrained_peft | I<0 | -0.291 [-0.331, -0.251] | -0.225 [-0.246, -0.205] | no |
| fau|NCE|reve/residual_pretrained_full | I<0 | -0.341 [-0.393, -0.289] | -0.245 [-0.273, -0.217] | no |
| fau|NCE|reve/residual_random_frozen | I<0 | -0.360 [-0.410, -0.310] | -0.276 [-0.295, -0.256] | no |
| fau|NCE|reve/residual_random_trainable | I<0 | -0.398 [-0.454, -0.342] | -0.310 [-0.334, -0.285] | no |
| fau|NCE|-/residual_small_capacity | I<0 | -0.408 [-0.460, -0.356] | -0.309 [-0.325, -0.293] | no |
| fau|CS_SINGLE|cbramod/concat_pretrained | I<0 | -0.123 [-0.148, -0.097] | -0.057 [-0.075, -0.040] | no |
| fau|CS_SINGLE|cbramod/residual_pretrained_frozen | I<0 | -0.048 [-0.066, -0.031] | -0.003 [-0.012, +0.005] | no |
| fau|CS_SINGLE|cbramod/residual_pretrained_peft | I<0 | -0.044 [-0.058, -0.030] | -0.008 [-0.016, -0.000] | no |
| fau|CS_SINGLE|cbramod/residual_pretrained_full | I<0 | -0.057 [-0.073, -0.041] | -0.010 [-0.018, -0.002] | no |
| fau|CS_SINGLE|cbramod/residual_random_frozen | I<0 | -0.098 [-0.122, -0.074] | -0.052 [-0.070, -0.034] | no |
| fau|CS_SINGLE|cbramod/residual_random_trainable | I<0 | -0.086 [-0.108, -0.064] | -0.049 [-0.066, -0.031] | no |
| fau|CS_SINGLE|reve/concat_pretrained | I<0 | -0.200 [-0.236, -0.164] | -0.101 [-0.123, -0.078] | no |
| fau|CS_SINGLE|reve/residual_pretrained_frozen | I<0 | -0.076 [-0.097, -0.055] | -0.036 [-0.052, -0.020] | no |
| fau|CS_SINGLE|reve/residual_pretrained_peft | I<0 | -0.079 [-0.103, -0.054] | -0.032 [-0.045, -0.018] | no |
| fau|CS_SINGLE|reve/residual_pretrained_full | I<0 | -0.051 [-0.064, -0.037] | -0.003 [-0.010, +0.005] | no |
| fau|CS_SINGLE|reve/residual_random_frozen | I<0 | -0.083 [-0.109, -0.057] | -0.038 [-0.051, -0.026] | no |
| fau|CS_SINGLE|reve/residual_random_trainable | I<0 | -0.090 [-0.110, -0.071] | -0.056 [-0.072, -0.040] | no |
| fau|CS_SINGLE|-/residual_small_capacity | I<0 | -0.079 [-0.099, -0.059] | -0.039 [-0.054, -0.023] | no |
| dtu|NCE|cbramod/concat_pretrained | I<0 | -0.206 [-0.248, -0.163] | -0.013 [-0.057, +0.030] | no |
| dtu|NCE|cbramod/residual_pretrained_frozen | I<0 | -0.130 [-0.181, -0.080] | -0.008 [-0.053, +0.037] | no |
| dtu|NCE|cbramod/residual_pretrained_peft | I<0 | -0.154 [-0.200, -0.108] | -0.088 [-0.125, -0.050] | no |
| dtu|NCE|cbramod/residual_pretrained_full | I<0 | -0.094 [-0.139, -0.049] | -0.020 [-0.060, +0.020] | no |
| dtu|NCE|cbramod/residual_random_frozen | I<0 | -0.130 [-0.181, -0.080] | -0.016 [-0.062, +0.029] | no |
| dtu|NCE|cbramod/residual_random_trainable | I<0 | -0.124 [-0.175, -0.072] | -0.014 [-0.059, +0.030] | no |
| dtu|NCE|reve/concat_pretrained | I<0 | -0.220 [-0.267, -0.173] | -0.073 [-0.115, -0.031] | no |
| dtu|NCE|reve/residual_pretrained_frozen | I<0 | -0.100 [-0.142, -0.058] | -0.042 [-0.075, -0.008] | no |
| dtu|NCE|reve/residual_pretrained_peft | I<0 | -0.096 [-0.140, -0.051] | -0.032 [-0.068, +0.004] | no |
| dtu|NCE|reve/residual_pretrained_full | I<0 | -0.090 [-0.139, -0.041] | -0.044 [-0.081, -0.007] | no |
| dtu|NCE|reve/residual_random_frozen | I<0 | -0.115 [-0.171, -0.059] | -0.037 [-0.079, +0.006] | no |
| dtu|NCE|reve/residual_random_trainable | I<0 | -0.090 [-0.134, -0.046] | -0.034 [-0.072, +0.003] | no |
| dtu|NCE|-/residual_small_capacity | I<0 | -0.094 [-0.141, -0.048] | -0.026 [-0.066, +0.014] | no |
| dtu|CS_SINGLE|cbramod/concat_pretrained | I<0 | -0.031 [-0.054, -0.008] | +0.014 [+0.003, +0.025] | no |
| dtu|CS_SINGLE|cbramod/residual_pretrained_frozen | I<0 | -0.149 [-0.192, -0.106] | -0.026 [-0.054, +0.001] | no |
| dtu|CS_SINGLE|cbramod/residual_pretrained_peft | I<0 | -0.082 [-0.107, -0.056] | +0.022 [+0.007, +0.037] | no |
| dtu|CS_SINGLE|cbramod/residual_pretrained_full | I<0 | -0.084 [-0.106, -0.062] | +0.023 [+0.010, +0.037] | no |
| dtu|CS_SINGLE|cbramod/residual_random_frozen | I<0 | -0.119 [-0.158, -0.081] | -0.009 [-0.035, +0.017] | no |
| dtu|CS_SINGLE|cbramod/residual_random_trainable | I<0 | -0.114 [-0.152, -0.076] | -0.008 [-0.033, +0.017] | no |
| dtu|CS_SINGLE|reve/concat_pretrained | I<0 | -0.101 [-0.125, -0.077] | -0.022 [-0.044, +0.001] | no |
| dtu|CS_SINGLE|reve/residual_pretrained_frozen | I<0 | -0.091 [-0.115, -0.067] | +0.016 [+0.003, +0.029] | no |
| dtu|CS_SINGLE|reve/residual_pretrained_peft | I<0 | -0.086 [-0.112, -0.061] | +0.016 [+0.001, +0.031] | no |
| dtu|CS_SINGLE|reve/residual_pretrained_full | I<0 | -0.089 [-0.114, -0.064] | +0.019 [+0.006, +0.032] | no |
| dtu|CS_SINGLE|reve/residual_random_frozen | I<0 | -0.129 [-0.161, -0.096] | -0.018 [-0.039, +0.004] | no |
| dtu|CS_SINGLE|reve/residual_random_trainable | I<0 | -0.168 [-0.210, -0.126] | -0.046 [-0.072, -0.021] | no |
| dtu|CS_SINGLE|-/residual_small_capacity | I<0 | -0.171 [-0.209, -0.133] | -0.072 [-0.112, -0.032] | no |
| federici|NCE|cbramod/concat_pretrained | contains 0 | -0.011 [-0.018, -0.004] | -0.008 [-0.014, -0.002] | no |
| federici|NCE|cbramod/residual_pretrained_frozen | I>0 | +0.000 [+0.000, +0.000] | +0.000 [-0.000, +0.000] | no |
| federici|NCE|cbramod/residual_pretrained_peft | I>0 | +0.000 [+0.000, +0.000] | +0.000 [-0.000, +0.000] | no |
| federici|NCE|cbramod/residual_pretrained_full | I>0 | +0.000 [+0.000, +0.000] | -0.000 [-0.000, +0.000] | no |
| federici|NCE|cbramod/residual_random_frozen | contains 0 | +0.001 [-0.000, +0.002] | +0.001 [-0.000, +0.002] | no |
| federici|NCE|cbramod/residual_random_trainable | I>0 | +0.003 [-0.002, +0.007] | -0.000 [-0.003, +0.002] | no |
| federici|NCE|reve/concat_pretrained | contains 0 | -0.028 [-0.043, -0.014] | -0.013 [-0.023, -0.003] | no |
| federici|NCE|reve/residual_pretrained_frozen | contains 0 | -0.000 [-0.001, +0.001] | -0.001 [-0.002, +0.000] | no |
| federici|NCE|reve/residual_pretrained_peft | contains 0 | +0.000 [-0.000, +0.001] | -0.000 [-0.000, +0.000] | no |
| federici|NCE|reve/residual_pretrained_full | contains 0 | +0.000 [+0.000, +0.001] | +0.000 [-0.000, +0.001] | yes |
| federici|NCE|reve/residual_random_frozen | contains 0 | -0.000 [-0.002, +0.002] | -0.000 [-0.002, +0.002] | no |
| federici|NCE|reve/residual_random_trainable | contains 0 | +0.000 [-0.001, +0.001] | -0.000 [-0.001, +0.000] | no |
| federici|NCE|-/residual_small_capacity | I>0 | +0.000 [+0.000, +0.000] | +0.000 [-0.000, +0.000] | no |
| federici|CS_SINGLE|cbramod/concat_pretrained | contains 0 | -0.012 [-0.028, +0.004] | -0.018 [-0.032, -0.005] | no |
| federici|CS_SINGLE|cbramod/residual_pretrained_frozen | contains 0 | +0.005 [-0.002, +0.011] | +0.002 [-0.002, +0.006] | no |
| federici|CS_SINGLE|cbramod/residual_pretrained_peft | contains 0 | -0.000 [-0.013, +0.013] | -0.002 [-0.013, +0.010] | no |
| federici|CS_SINGLE|cbramod/residual_pretrained_full | contains 0 | +0.004 [-0.003, +0.012] | +0.004 [-0.001, +0.010] | no |
| federici|CS_SINGLE|cbramod/residual_random_frozen | contains 0 | +0.008 [-0.009, +0.024] | +0.009 [-0.004, +0.022] | no |
| federici|CS_SINGLE|cbramod/residual_random_trainable | contains 0 | -0.008 [-0.021, +0.006] | -0.005 [-0.017, +0.007] | no |
| federici|CS_SINGLE|reve/concat_pretrained | contains 0 | -0.002 [-0.013, +0.010] | -0.005 [-0.015, +0.005] | no |
| federici|CS_SINGLE|reve/residual_pretrained_frozen | contains 0 | +0.004 [-0.010, +0.018] | +0.007 [-0.004, +0.018] | no |
| federici|CS_SINGLE|reve/residual_pretrained_peft | contains 0 | +0.009 [-0.004, +0.023] | +0.008 [-0.004, +0.019] | no |
| federici|CS_SINGLE|reve/residual_pretrained_full | contains 0 | +0.004 [-0.010, +0.018] | +0.007 [-0.004, +0.018] | no |
| federici|CS_SINGLE|reve/residual_random_frozen | contains 0 | +0.024 [+0.014, +0.033] | +0.022 [+0.014, +0.029] | yes |
| federici|CS_SINGLE|reve/residual_random_trainable | contains 0 | +0.008 [-0.006, +0.022] | +0.007 [-0.005, +0.018] | no |
| federici|CS_SINGLE|-/residual_small_capacity | contains 0 | -0.008 [-0.024, +0.008] | -0.002 [-0.015, +0.011] | no |

## 4. Attribution (per backbone): initialization, capacity, residual structure

**FAU · NCE · cbramod** (family `C-ATTRIB|fau|NCE|cbramod`, critical value 2.76)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 67 | -0.007 | [-0.018, +0.004] | [-0.021, +0.008] | contains 0 | -0.002 | -0.000 | +0.016 | -0.004 | +0.000 |
| init_frozen | initialization (frozen) | 67 | -0.014 | [-0.030, +0.002] | [-0.036, +0.008] | contains 0 | -0.003 | -0.003 | -0.055 | +0.010 | -0.005 |
| capacity_frozen | capacity | 67 | -0.004 | [-0.025, +0.016] | [-0.031, +0.022] | contains 0 | +0.001 | +0.001 | -0.004 | -0.016 | -0.001 |
| capacity_peft | capacity | 67 | +0.011 | [+0.006, +0.016] | [+0.004, +0.018] | I>0 | +0.002 | +0.002 | +0.009 | +0.016 | +0.007 |
| capacity_full | capacity | 67 | +0.012 | [+0.001, +0.023] | [-0.003, +0.027] | contains 0 | +0.000 | +0.003 | +0.004 | +0.021 | -0.001 |
| residual_vs_concat | residual structure | 67 | +0.042 | [+0.018, +0.066] | [+0.009, +0.075] | I>0 | +0.010 | +0.013 | +0.111 | +0.157 | -0.003 |

**FAU · NCE · reve** (family `C-ATTRIB|fau|NCE|reve`, critical value 2.61)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 67 | -0.007 | [-0.031, +0.016] | [-0.039, +0.024] | contains 0 | +0.002 | -0.002 | +0.057 | +0.041 | -0.003 |
| init_frozen | initialization (frozen) | 67 | -0.007 | [-0.026, +0.012] | [-0.032, +0.018] | contains 0 | +0.000 | +0.001 | +0.044 | -0.037 | +0.007 |
| capacity_frozen | capacity | 67 | +0.008 | [-0.013, +0.029] | [-0.018, +0.033] | contains 0 | +0.005 | +0.005 | +0.092 | -0.011 | +0.009 |
| capacity_peft | capacity | 67 | +0.034 | [+0.010, +0.057] | [+0.004, +0.063] | I>0 | +0.007 | +0.010 | +0.117 | +0.026 | +0.006 |
| capacity_full | capacity | 67 | +0.003 | [-0.020, +0.026] | [-0.027, +0.033] | contains 0 | +0.006 | +0.001 | +0.067 | +0.039 | +0.001 |
| residual_vs_concat | residual structure | 67 | +0.057 | [+0.024, +0.089] | [+0.013, +0.100] | I>0 | +0.013 | +0.020 | +0.252 | +0.160 | +0.002 |

**FAU · CS_SINGLE · cbramod** (family `C-ATTRIB|fau|CS_SINGLE|cbramod`, critical value 2.65)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 67 | -0.009 | [-0.022, +0.003] | [-0.025, +0.006] | contains 0 | -0.002 | +0.000 | +0.029 | -0.004 | +0.005 |
| init_frozen | initialization (frozen) | 67 | +0.001 | [-0.014, +0.016] | [-0.018, +0.020] | contains 0 | -0.001 | +0.003 | +0.050 | +0.014 | +0.003 |
| capacity_frozen | capacity | 67 | -0.005 | [-0.018, +0.008] | [-0.023, +0.013] | contains 0 | -0.003 | +0.001 | +0.030 | +0.002 | -0.001 |
| capacity_peft | capacity | 67 | +0.004 | [-0.009, +0.017] | [-0.013, +0.021] | contains 0 | -0.001 | +0.003 | +0.035 | +0.006 | -0.002 |
| capacity_full | capacity | 67 | -0.007 | [-0.019, +0.005] | [-0.022, +0.009] | contains 0 | -0.004 | +0.000 | +0.022 | -0.003 | -0.000 |
| residual_vs_concat | residual structure | 67 | +0.020 | [+0.004, +0.036] | [-0.002, +0.042] | contains 0 | +0.000 | +0.007 | +0.074 | -0.017 | -0.006 |

**FAU · CS_SINGLE · reve** (family `C-ATTRIB|fau|CS_SINGLE|reve`, critical value 2.80)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 67 | -0.014 | [-0.028, -0.001] | [-0.033, +0.004] | contains 0 | -0.000 | -0.001 | +0.040 | -0.003 | +0.006 |
| init_frozen | initialization (frozen) | 67 | +0.005 | [-0.008, +0.018] | [-0.013, +0.024] | contains 0 | -0.002 | +0.000 | +0.007 | -0.010 | -0.002 |
| capacity_frozen | capacity | 67 | -0.000 | [-0.009, +0.009] | [-0.013, +0.013] | contains 0 | -0.002 | +0.001 | +0.002 | -0.003 | -0.002 |
| capacity_peft | capacity | 67 | -0.007 | [-0.022, +0.007] | [-0.027, +0.013] | contains 0 | -0.002 | -0.001 | -0.000 | +0.004 | -0.004 |
| capacity_full | capacity | 67 | -0.008 | [-0.023, +0.007] | [-0.028, +0.012] | contains 0 | -0.001 | +0.000 | +0.028 | +0.001 | +0.003 |
| residual_vs_concat | residual structure | 67 | +0.059 | [+0.039, +0.080] | [+0.029, +0.089] | I>0 | +0.008 | +0.017 | +0.124 | +0.000 | -0.003 |

**DTU · NCE · cbramod** (family `C-ATTRIB|dtu|NCE|cbramod`, critical value 2.79)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 44 | +0.035 | [+0.009, +0.062] | [-0.002, +0.072] | contains 0 | +0.002 | +0.004 | +0.030 | +0.089 | +0.000 |
| init_frozen | initialization (frozen) | 44 | -0.008 | [-0.022, +0.005] | [-0.027, +0.010] | contains 0 | -0.001 | -0.001 | -0.000 | -0.016 | +0.000 |
| capacity_frozen | capacity | 44 | -0.054 | [-0.079, -0.029] | [-0.087, -0.020] | I<0 | -0.005 | -0.005 | -0.036 | -0.111 | -0.003 |
| capacity_peft | capacity | 44 | +0.002 | [-0.017, +0.020] | [-0.024, +0.028] | contains 0 | -0.002 | -0.001 | -0.060 | -0.007 | -0.004 |
| capacity_full | capacity | 44 | -0.006 | [-0.022, +0.011] | [-0.028, +0.017] | contains 0 | -0.000 | -0.000 | +0.000 | -0.001 | +0.002 |
| residual_vs_concat | residual structure | 44 | +0.070 | [+0.047, +0.094] | [+0.038, +0.103] | I>0 | +0.005 | +0.007 | +0.076 | +0.089 | +0.010 |

**DTU · NCE · reve** (family `C-ATTRIB|dtu|NCE|reve`, critical value 2.81)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 44 | +0.009 | [-0.009, +0.026] | [-0.015, +0.033] | contains 0 | -0.001 | +0.000 | -0.001 | -0.056 | -0.001 |
| init_frozen | initialization (frozen) | 44 | +0.020 | [+0.004, +0.036] | [-0.003, +0.043] | contains 0 | +0.002 | +0.002 | +0.015 | +0.047 | -0.001 |
| capacity_frozen | capacity | 44 | +0.010 | [-0.009, +0.029] | [-0.014, +0.034] | contains 0 | +0.001 | +0.001 | -0.006 | -0.026 | -0.003 |
| capacity_peft | capacity | 44 | +0.005 | [-0.009, +0.018] | [-0.014, +0.023] | contains 0 | -0.003 | +0.000 | -0.001 | -0.076 | -0.003 |
| capacity_full | capacity | 44 | +0.022 | [+0.003, +0.041] | [-0.003, +0.047] | contains 0 | +0.002 | +0.002 | +0.004 | -0.032 | -0.001 |
| residual_vs_concat | residual structure | 44 | +0.089 | [+0.062, +0.115] | [+0.052, +0.125] | I>0 | +0.007 | +0.010 | +0.120 | +0.197 | +0.002 |

**DTU · CS_SINGLE · cbramod** (family `C-ATTRIB|dtu|CS_SINGLE|cbramod`, critical value 2.71)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 44 | -0.001 | [-0.021, +0.019] | [-0.027, +0.025] | contains 0 | +0.002 | +0.000 | +0.030 | -0.009 | +0.004 |
| init_frozen | initialization (frozen) | 44 | -0.012 | [-0.026, +0.001] | [-0.031, +0.006] | contains 0 | -0.001 | -0.003 | -0.029 | -0.001 | -0.001 |
| capacity_frozen | capacity | 44 | -0.024 | [-0.045, -0.002] | [-0.052, +0.004] | contains 0 | -0.001 | -0.003 | +0.022 | +0.009 | +0.003 |
| capacity_peft | capacity | 44 | -0.005 | [-0.025, +0.015] | [-0.031, +0.022] | contains 0 | +0.001 | +0.003 | +0.089 | +0.006 | +0.005 |
| capacity_full | capacity | 44 | -0.009 | [-0.030, +0.013] | [-0.037, +0.020] | contains 0 | +0.000 | +0.001 | +0.087 | +0.004 | +0.006 |
| residual_vs_concat | residual structure | 44 | -0.078 | [-0.103, -0.052] | [-0.112, -0.043] | I<0 | -0.004 | -0.014 | -0.118 | -0.047 | -0.004 |

**DTU · CS_SINGLE · reve** (family `C-ATTRIB|dtu|CS_SINGLE|reve`, critical value 2.70)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 44 | +0.014 | [-0.001, +0.028] | [-0.006, +0.033] | contains 0 | -0.001 | +0.003 | +0.079 | +0.004 | +0.004 |
| init_frozen | initialization (frozen) | 44 | +0.003 | [-0.011, +0.017] | [-0.016, +0.022] | contains 0 | -0.002 | +0.001 | +0.037 | +0.005 | +0.003 |
| capacity_frozen | capacity | 44 | -0.009 | [-0.028, +0.011] | [-0.035, +0.017] | contains 0 | -0.002 | +0.001 | +0.079 | +0.008 | +0.008 |
| capacity_peft | capacity | 44 | -0.003 | [-0.023, +0.017] | [-0.031, +0.024] | contains 0 | +0.000 | +0.003 | +0.084 | +0.005 | +0.004 |
| capacity_full | capacity | 44 | -0.010 | [-0.029, +0.010] | [-0.035, +0.016] | contains 0 | -0.001 | +0.001 | +0.081 | +0.007 | +0.005 |
| residual_vs_concat | residual structure | 44 | -0.028 | [-0.054, -0.003] | [-0.062, +0.005] | contains 0 | +0.001 | -0.006 | +0.010 | -0.070 | +0.006 |

**Federici · NCE · cbramod** (family `C-ATTRIB|federici|NCE|cbramod`, critical value 2.84)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 86 | -0.003 | [-0.005, -0.001] | [-0.005, -0.000] | I<0 | -0.000 | -0.001 | -0.003 | +0.023 | – |
| init_frozen | initialization (frozen) | 86 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 | -0.001 | +0.001 | – |
| capacity_frozen | capacity | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | -0.000 | -0.000 | +0.000 | – |
| capacity_peft | capacity | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | -0.000 | -0.000 | +0.001 | – |
| capacity_full | capacity | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | -0.000 | -0.000 | -0.002 | – |
| residual_vs_concat | residual structure | 86 | +0.003 | [-0.002, +0.008] | [-0.004, +0.010] | contains 0 | -0.001 | +0.002 | +0.011 | +0.012 | – |

**Federici · NCE · reve** (family `C-ATTRIB|federici|NCE|reve`, critical value 2.74)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 86 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 | -0.001 | – |
| init_frozen | initialization (frozen) | 86 | +0.001 | [-0.001, +0.003] | [-0.002, +0.004] | contains 0 | +0.001 | +0.000 | +0.000 | +0.035 | – |
| capacity_frozen | capacity | 86 | +0.001 | [-0.000, +0.001] | [-0.000, +0.002] | contains 0 | +0.000 | +0.000 | -0.000 | -0.003 | – |
| capacity_peft | capacity | 86 | -0.000 | [-0.000, +0.000] | [-0.000, +0.000] | contains 0 | +0.000 | +0.000 | -0.000 | -0.004 | – |
| capacity_full | capacity | 86 | +0.000 | [-0.000, +0.000] | [-0.000, +0.001] | contains 0 | +0.000 | +0.000 | +0.000 | -0.002 | – |
| residual_vs_concat | residual structure | 86 | +0.016 | [+0.005, +0.027] | [+0.001, +0.032] | I>0 | +0.004 | +0.007 | +0.028 | +0.056 | – |

**Federici · CS_SINGLE · cbramod** (family `C-ATTRIB|federici|CS_SINGLE|cbramod`, critical value 2.62)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 86 | +0.003 | [-0.006, +0.011] | [-0.009, +0.014] | contains 0 | -0.001 | +0.001 | +0.012 | +0.001 | – |
| init_frozen | initialization (frozen) | 86 | +0.004 | [-0.006, +0.013] | [-0.009, +0.016] | contains 0 | -0.001 | +0.002 | -0.003 | +0.000 | – |
| capacity_frozen | capacity | 86 | +0.008 | [+0.000, +0.016] | [-0.002, +0.019] | contains 0 | +0.002 | +0.003 | +0.013 | +0.001 | – |
| capacity_peft | capacity | 86 | +0.007 | [+0.002, +0.013] | [-0.000, +0.015] | contains 0 | +0.005 | +0.004 | +0.008 | +0.000 | – |
| capacity_full | capacity | 86 | +0.006 | [-0.003, +0.014] | [-0.005, +0.017] | contains 0 | +0.002 | +0.002 | +0.012 | +0.001 | – |
| residual_vs_concat | residual structure | 86 | -0.004 | [-0.014, +0.006] | [-0.017, +0.009] | contains 0 | -0.001 | +0.002 | +0.017 | -0.000 | – |

**Federici · CS_SINGLE · reve** (family `C-ATTRIB|federici|CS_SINGLE|reve`, critical value 2.57)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| init_full | initialization (matched update) | 86 | -0.004 | [-0.010, +0.001] | [-0.011, +0.003] | contains 0 | +0.001 | -0.002 | -0.004 | +0.000 | – |
| init_frozen | initialization (frozen) | 86 | -0.005 | [-0.011, +0.002] | [-0.013, +0.004] | contains 0 | +0.001 | -0.002 | -0.019 | +0.000 | – |
| capacity_frozen | capacity | 86 | +0.003 | [-0.004, +0.011] | [-0.007, +0.013] | contains 0 | +0.001 | +0.001 | +0.012 | +0.001 | – |
| capacity_peft | capacity | 86 | +0.007 | [-0.000, +0.015] | [-0.002, +0.017] | contains 0 | +0.002 | +0.003 | +0.017 | +0.000 | – |
| capacity_full | capacity | 86 | +0.003 | [-0.005, +0.011] | [-0.007, +0.013] | contains 0 | +0.001 | +0.001 | +0.012 | +0.001 | – |
| residual_vs_concat | residual structure | 86 | -0.006 | [-0.012, +0.001] | [-0.014, +0.003] | contains 0 | +0.001 | -0.003 | +0.006 | -0.001 | – |

### 4a. Wording rule (ADDENDUM_05 §7), mechanical

| cell | C-LOCAL | init | capacity | wording |
|---|---|---|---|---|
| fau|NCE|cbramod|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| fau|NCE|cbramod|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|NCE|cbramod|residual_pretrained_peft | I<0 | n/a | I>0 | combined worse than local |
| fau|NCE|cbramod|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|NCE|cbramod|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| fau|NCE|cbramod|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| fau|NCE|reve|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| fau|NCE|reve|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|NCE|reve|residual_pretrained_peft | I<0 | n/a | I>0 | combined worse than local |
| fau|NCE|reve|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|NCE|reve|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| fau|NCE|reve|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|cbramod|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|cbramod|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|CS_SINGLE|cbramod|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| fau|CS_SINGLE|cbramod|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|CS_SINGLE|cbramod|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|cbramod|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|reve|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|reve|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|CS_SINGLE|reve|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| fau|CS_SINGLE|reve|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| fau|CS_SINGLE|reve|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| fau|CS_SINGLE|reve|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|cbramod|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|cbramod|residual_pretrained_frozen | I<0 | contains 0 | I<0 | combined worse than local |
| dtu|NCE|cbramod|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| dtu|NCE|cbramod|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|NCE|cbramod|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|cbramod|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|reve|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|reve|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|NCE|reve|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| dtu|NCE|reve|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|NCE|reve|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| dtu|NCE|reve|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|cbramod|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|cbramod|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|CS_SINGLE|cbramod|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| dtu|CS_SINGLE|cbramod|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|CS_SINGLE|cbramod|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|cbramod|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|reve|concat_pretrained | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|reve|residual_pretrained_frozen | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|CS_SINGLE|reve|residual_pretrained_peft | I<0 | n/a | contains 0 | combined worse than local |
| dtu|CS_SINGLE|reve|residual_pretrained_full | I<0 | contains 0 | contains 0 | combined worse than local |
| dtu|CS_SINGLE|reve|residual_random_frozen | I<0 | n/a | n/a | combined worse than local |
| dtu|CS_SINGLE|reve|residual_random_trainable | I<0 | n/a | n/a | combined worse than local |
| federici|NCE|cbramod|concat_pretrained | contains 0 | n/a | n/a | no complement resolved |
| federici|NCE|cbramod|residual_pretrained_frozen | I>0 | contains 0 | contains 0 | added branch lowers risk; source (pretraining vs added capacity / structure) not separated |
| federici|NCE|cbramod|residual_pretrained_peft | I>0 | n/a | contains 0 | added branch lowers risk; source (pretraining vs added capacity / structure) not separated |
| federici|NCE|cbramod|residual_pretrained_full | I>0 | I<0 | contains 0 | added branch lowers risk; source (pretraining vs added capacity / structure) not separated |
| federici|NCE|cbramod|residual_random_frozen | contains 0 | n/a | n/a | no complement resolved |
| federici|NCE|cbramod|residual_random_trainable | I>0 | n/a | n/a | added branch lowers risk; source (pretraining vs added capacity / structure) not separated |
| federici|NCE|reve|concat_pretrained | contains 0 | n/a | n/a | no complement resolved |
| federici|NCE|reve|residual_pretrained_frozen | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|NCE|reve|residual_pretrained_peft | contains 0 | n/a | contains 0 | no complement resolved |
| federici|NCE|reve|residual_pretrained_full | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|NCE|reve|residual_random_frozen | contains 0 | n/a | n/a | no complement resolved |
| federici|NCE|reve|residual_random_trainable | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|cbramod|concat_pretrained | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|cbramod|residual_pretrained_frozen | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|CS_SINGLE|cbramod|residual_pretrained_peft | contains 0 | n/a | contains 0 | no complement resolved |
| federici|CS_SINGLE|cbramod|residual_pretrained_full | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|CS_SINGLE|cbramod|residual_random_frozen | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|cbramod|residual_random_trainable | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|reve|concat_pretrained | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|reve|residual_pretrained_frozen | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|CS_SINGLE|reve|residual_pretrained_peft | contains 0 | n/a | contains 0 | no complement resolved |
| federici|CS_SINGLE|reve|residual_pretrained_full | contains 0 | contains 0 | contains 0 | no complement resolved |
| federici|CS_SINGLE|reve|residual_random_frozen | contains 0 | n/a | n/a | no complement resolved |
| federici|CS_SINGLE|reve|residual_random_trainable | contains 0 | n/a | n/a | no complement resolved |

## 5. Combined vs foundation only: B_DENSE `dense_query` (matched adaptation) → C variant

**FAU · NCE · cbramod** (family `C-FMONLY|fau|NCE|cbramod`, critical value 2.15)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 67 | +0.237 | [+0.178, +0.297] | [+0.174, +0.301] | I>0 | +0.027 | +0.157 | +0.521 | +0.282 | +0.048 |
| residual_pretrained_frozen | vs foundation only | 67 | +0.279 | [+0.202, +0.357] | [+0.195, +0.363] | I>0 | +0.037 | +0.170 | +0.632 | +0.440 | +0.045 |
| residual_pretrained_peft | vs foundation only | 67 | +0.295 | [+0.220, +0.369] | [+0.215, +0.374] | I>0 | +0.038 | +0.172 | +0.645 | +0.472 | +0.057 |
| residual_pretrained_full | vs foundation only | 67 | +0.296 | [+0.220, +0.371] | [+0.215, +0.377] | I>0 | +0.037 | +0.172 | +0.640 | +0.477 | +0.037 |
| residual_random_frozen | vs foundation only | 67 | +0.294 | [+0.217, +0.371] | [+0.211, +0.377] | I>0 | +0.041 | +0.172 | +0.687 | +0.430 | +0.044 |
| residual_random_trainable | vs foundation only | 67 | +0.303 | [+0.229, +0.377] | [+0.224, +0.383] | I>0 | +0.039 | +0.172 | +0.624 | +0.481 | +0.038 |

**FAU · NCE · reve** (family `C-FMONLY|fau|NCE|reve`, critical value 2.16)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 67 | +0.235 | [+0.180, +0.289] | [+0.174, +0.295] | I>0 | +0.028 | +0.154 | +0.477 | +0.284 | +0.054 |
| residual_pretrained_frozen | vs foundation only | 67 | +0.291 | [+0.205, +0.378] | [+0.198, +0.385] | I>0 | +0.041 | +0.174 | +0.728 | +0.444 | +0.056 |
| residual_pretrained_peft | vs foundation only | 67 | +0.318 | [+0.228, +0.407] | [+0.220, +0.415] | I>0 | +0.044 | +0.178 | +0.753 | +0.482 | +0.054 |
| residual_pretrained_full | vs foundation only | 67 | +0.287 | [+0.200, +0.373] | [+0.193, +0.380] | I>0 | +0.042 | +0.170 | +0.703 | +0.494 | +0.048 |
| residual_random_frozen | vs foundation only | 67 | +0.299 | [+0.225, +0.373] | [+0.218, +0.380] | I>0 | +0.041 | +0.173 | +0.685 | +0.482 | +0.040 |
| residual_random_trainable | vs foundation only | 67 | +0.295 | [+0.224, +0.366] | [+0.217, +0.372] | I>0 | +0.040 | +0.173 | +0.646 | +0.453 | +0.041 |

**FAU · CS_SINGLE · cbramod** (family `C-FMONLY|fau|CS_SINGLE|cbramod`, critical value 2.11)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 67 | +0.270 | [+0.202, +0.337] | [+0.198, +0.341] | I>0 | +0.037 | +0.168 | +0.602 | +0.337 | +0.024 |
| residual_pretrained_frozen | vs foundation only | 67 | +0.290 | [+0.213, +0.366] | [+0.209, +0.370] | I>0 | +0.037 | +0.175 | +0.677 | +0.321 | +0.018 |
| residual_pretrained_peft | vs foundation only | 67 | +0.301 | [+0.223, +0.378] | [+0.219, +0.382] | I>0 | +0.040 | +0.176 | +0.680 | +0.326 | +0.027 |
| residual_pretrained_full | vs foundation only | 67 | +0.288 | [+0.213, +0.363] | [+0.209, +0.367] | I>0 | +0.037 | +0.173 | +0.667 | +0.316 | +0.034 |
| residual_random_frozen | vs foundation only | 67 | +0.289 | [+0.219, +0.359] | [+0.214, +0.363] | I>0 | +0.040 | +0.172 | +0.626 | +0.307 | +0.017 |
| residual_random_trainable | vs foundation only | 67 | +0.297 | [+0.226, +0.368] | [+0.222, +0.372] | I>0 | +0.039 | +0.174 | +0.638 | +0.320 | +0.016 |

**FAU · CS_SINGLE · reve** (family `C-FMONLY|fau|CS_SINGLE|reve`, critical value 2.10)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 67 | +0.235 | [+0.178, +0.291] | [+0.173, +0.296] | I>0 | +0.031 | +0.157 | +0.524 | +0.315 | +0.014 |
| residual_pretrained_frozen | vs foundation only | 67 | +0.294 | [+0.223, +0.365] | [+0.217, +0.371] | I>0 | +0.039 | +0.174 | +0.648 | +0.315 | +0.011 |
| residual_pretrained_peft | vs foundation only | 67 | +0.286 | [+0.214, +0.358] | [+0.208, +0.365] | I>0 | +0.039 | +0.171 | +0.645 | +0.322 | +0.014 |
| residual_pretrained_full | vs foundation only | 67 | +0.285 | [+0.212, +0.358] | [+0.204, +0.366] | I>0 | +0.040 | +0.172 | +0.673 | +0.319 | +0.015 |
| residual_random_frozen | vs foundation only | 67 | +0.290 | [+0.220, +0.360] | [+0.213, +0.367] | I>0 | +0.041 | +0.172 | +0.640 | +0.325 | +0.020 |
| residual_random_trainable | vs foundation only | 67 | +0.301 | [+0.230, +0.372] | [+0.223, +0.379] | I>0 | +0.040 | +0.173 | +0.633 | +0.322 | +0.017 |

**DTU · NCE · cbramod** (family `C-FMONLY|dtu|NCE|cbramod`, critical value 2.19)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 44 | +0.676 | [+0.520, +0.832] | [+0.509, +0.843] | I>0 | +0.048 | +0.266 | +1.803 | +1.206 | +0.170 |
| residual_pretrained_frozen | vs foundation only | 44 | +0.746 | [+0.590, +0.902] | [+0.579, +0.914] | I>0 | +0.053 | +0.272 | +1.879 | +1.295 | +0.180 |
| residual_pretrained_peft | vs foundation only | 44 | +0.806 | [+0.649, +0.963] | [+0.640, +0.972] | I>0 | +0.056 | +0.276 | +1.854 | +1.400 | +0.174 |
| residual_pretrained_full | vs foundation only | 44 | +0.796 | [+0.633, +0.960] | [+0.623, +0.970] | I>0 | +0.058 | +0.279 | +1.915 | +1.405 | +0.185 |
| residual_random_frozen | vs foundation only | 44 | +0.764 | [+0.608, +0.919] | [+0.599, +0.928] | I>0 | +0.055 | +0.273 | +1.877 | +1.311 | +0.175 |
| residual_random_trainable | vs foundation only | 44 | +0.768 | [+0.615, +0.921] | [+0.606, +0.931] | I>0 | +0.057 | +0.273 | +1.884 | +1.316 | +0.180 |

**DTU · NCE · reve** (family `C-FMONLY|dtu|NCE|reve`, critical value 2.18)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 44 | +0.719 | [+0.560, +0.879] | [+0.550, +0.888] | I>0 | +0.053 | +0.264 | +1.788 | +1.185 | +0.173 |
| residual_pretrained_frozen | vs foundation only | 44 | +0.808 | [+0.652, +0.964] | [+0.643, +0.973] | I>0 | +0.061 | +0.274 | +1.908 | +1.382 | +0.175 |
| residual_pretrained_peft | vs foundation only | 44 | +0.809 | [+0.652, +0.966] | [+0.644, +0.974] | I>0 | +0.056 | +0.276 | +1.913 | +1.330 | +0.176 |
| residual_pretrained_full | vs foundation only | 44 | +0.819 | [+0.663, +0.976] | [+0.654, +0.985] | I>0 | +0.062 | +0.278 | +1.918 | +1.375 | +0.183 |
| residual_random_frozen | vs foundation only | 44 | +0.805 | [+0.650, +0.960] | [+0.641, +0.969] | I>0 | +0.058 | +0.273 | +1.893 | +1.334 | +0.181 |
| residual_random_trainable | vs foundation only | 44 | +0.828 | [+0.670, +0.986] | [+0.660, +0.996] | I>0 | +0.061 | +0.277 | +1.919 | +1.431 | +0.183 |

**DTU · CS_SINGLE · cbramod** (family `C-FMONLY|dtu|CS_SINGLE|cbramod`, critical value 2.17)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 44 | +0.600 | [+0.489, +0.710] | [+0.481, +0.718] | I>0 | +0.038 | +0.237 | +1.351 | +0.510 | +0.162 |
| residual_pretrained_frozen | vs foundation only | 44 | +0.522 | [+0.410, +0.634] | [+0.402, +0.642] | I>0 | +0.035 | +0.224 | +1.233 | +0.463 | +0.158 |
| residual_pretrained_peft | vs foundation only | 44 | +0.528 | [+0.409, +0.648] | [+0.400, +0.656] | I>0 | +0.038 | +0.228 | +1.297 | +0.459 | +0.149 |
| residual_pretrained_full | vs foundation only | 44 | +0.526 | [+0.407, +0.644] | [+0.397, +0.654] | I>0 | +0.037 | +0.230 | +1.301 | +0.459 | +0.155 |
| residual_random_frozen | vs foundation only | 44 | +0.530 | [+0.418, +0.641] | [+0.411, +0.649] | I>0 | +0.035 | +0.231 | +1.261 | +0.464 | +0.153 |
| residual_random_trainable | vs foundation only | 44 | +0.534 | [+0.422, +0.646] | [+0.413, +0.654] | I>0 | +0.034 | +0.232 | +1.267 | +0.467 | +0.152 |

**DTU · CS_SINGLE · reve** (family `C-FMONLY|dtu|CS_SINGLE|reve`, critical value 2.18)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 44 | +0.574 | [+0.465, +0.683] | [+0.457, +0.691] | I>0 | +0.031 | +0.234 | +1.280 | +0.537 | +0.159 |
| residual_pretrained_frozen | vs foundation only | 44 | +0.545 | [+0.429, +0.662] | [+0.421, +0.670] | I>0 | +0.032 | +0.228 | +1.290 | +0.467 | +0.164 |
| residual_pretrained_peft | vs foundation only | 44 | +0.545 | [+0.428, +0.663] | [+0.420, +0.671] | I>0 | +0.036 | +0.234 | +1.295 | +0.464 | +0.158 |
| residual_pretrained_full | vs foundation only | 44 | +0.540 | [+0.424, +0.656] | [+0.416, +0.664] | I>0 | +0.034 | +0.229 | +1.292 | +0.466 | +0.162 |
| residual_random_frozen | vs foundation only | 44 | +0.537 | [+0.423, +0.651] | [+0.414, +0.660] | I>0 | +0.036 | +0.229 | +1.254 | +0.457 | +0.157 |
| residual_random_trainable | vs foundation only | 44 | +0.526 | [+0.414, +0.639] | [+0.407, +0.646] | I>0 | +0.036 | +0.226 | +1.215 | +0.457 | +0.153 |

**Federici · NCE · cbramod** (family `C-FMONLY|federici|NCE|cbramod`, critical value 2.10)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 86 | +0.112 | [+0.081, +0.143] | [+0.079, +0.145] | I>0 | +0.008 | +0.113 | +0.253 | +0.157 | – |
| residual_pretrained_frozen | vs foundation only | 86 | +0.115 | [+0.081, +0.149] | [+0.079, +0.150] | I>0 | +0.007 | +0.115 | +0.264 | +0.169 | – |
| residual_pretrained_peft | vs foundation only | 86 | +0.115 | [+0.081, +0.148] | [+0.079, +0.150] | I>0 | +0.009 | +0.116 | +0.264 | +0.169 | – |
| residual_pretrained_full | vs foundation only | 86 | +0.116 | [+0.082, +0.149] | [+0.080, +0.151] | I>0 | +0.008 | +0.120 | +0.265 | +0.168 | – |
| residual_random_frozen | vs foundation only | 86 | +0.116 | [+0.082, +0.150] | [+0.080, +0.152] | I>0 | +0.007 | +0.108 | +0.265 | +0.168 | – |
| residual_random_trainable | vs foundation only | 86 | +0.119 | [+0.085, +0.153] | [+0.083, +0.155] | I>0 | +0.007 | +0.109 | +0.267 | +0.143 | – |

**Federici · NCE · reve** (family `C-FMONLY|federici|NCE|reve`, critical value 2.23)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 86 | +0.100 | [+0.069, +0.131] | [+0.066, +0.133] | I>0 | +0.006 | +0.101 | +0.236 | +0.116 | – |
| residual_pretrained_frozen | vs foundation only | 86 | +0.116 | [+0.081, +0.151] | [+0.078, +0.154] | I>0 | +0.010 | +0.108 | +0.264 | +0.172 | – |
| residual_pretrained_peft | vs foundation only | 86 | +0.122 | [+0.087, +0.157] | [+0.084, +0.160] | I>0 | +0.008 | +0.118 | +0.270 | +0.172 | – |
| residual_pretrained_full | vs foundation only | 86 | +0.115 | [+0.080, +0.150] | [+0.076, +0.153] | I>0 | +0.008 | +0.113 | +0.265 | +0.170 | – |
| residual_random_frozen | vs foundation only | 86 | +0.117 | [+0.082, +0.151] | [+0.079, +0.154] | I>0 | +0.007 | +0.114 | +0.264 | +0.131 | – |
| residual_random_trainable | vs foundation only | 86 | +0.117 | [+0.082, +0.152] | [+0.079, +0.155] | I>0 | +0.008 | +0.114 | +0.264 | +0.168 | – |

**Federici · CS_SINGLE · cbramod** (family `C-FMONLY|federici|CS_SINGLE|cbramod`, critical value 2.23)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 86 | +0.099 | [+0.069, +0.130] | [+0.065, +0.134] | I>0 | +0.006 | +0.099 | +0.206 | +0.002 | – |
| residual_pretrained_frozen | vs foundation only | 86 | +0.095 | [+0.062, +0.129] | [+0.059, +0.132] | I>0 | +0.006 | +0.100 | +0.223 | +0.001 | – |
| residual_pretrained_peft | vs foundation only | 86 | +0.096 | [+0.062, +0.130] | [+0.058, +0.134] | I>0 | +0.014 | +0.103 | +0.222 | +0.001 | – |
| residual_pretrained_full | vs foundation only | 86 | +0.096 | [+0.063, +0.130] | [+0.059, +0.133] | I>0 | +0.009 | +0.104 | +0.226 | +0.002 | – |
| residual_random_frozen | vs foundation only | 86 | +0.093 | [+0.058, +0.129] | [+0.054, +0.133] | I>0 | +0.008 | +0.103 | +0.229 | +0.001 | – |
| residual_random_trainable | vs foundation only | 86 | +0.092 | [+0.059, +0.125] | [+0.055, +0.129] | I>0 | +0.009 | +0.103 | +0.214 | +0.001 | – |

**Federici · CS_SINGLE · reve** (family `C-FMONLY|federici|CS_SINGLE|reve`, critical value 2.23)

| member | label | n | ΔR | 95% CI | 95% simultaneous | class | Δtop1 | Δrank% | Δgain | ΔR_native | Δatt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| concat_pretrained | vs foundation only | 86 | +0.098 | [+0.064, +0.132] | [+0.062, +0.135] | I>0 | +0.007 | +0.108 | +0.219 | +0.002 | – |
| residual_pretrained_frozen | vs foundation only | 86 | +0.093 | [+0.057, +0.129] | [+0.054, +0.132] | I>0 | +0.008 | +0.104 | +0.225 | +0.001 | – |
| residual_pretrained_peft | vs foundation only | 86 | +0.096 | [+0.060, +0.131] | [+0.057, +0.134] | I>0 | +0.009 | +0.106 | +0.230 | +0.001 | – |
| residual_pretrained_full | vs foundation only | 86 | +0.091 | [+0.056, +0.126] | [+0.053, +0.129] | I>0 | +0.009 | +0.103 | +0.223 | +0.001 | – |
| residual_random_frozen | vs foundation only | 86 | +0.099 | [+0.063, +0.135] | [+0.058, +0.139] | I>0 | +0.006 | +0.109 | +0.244 | +0.001 | – |
| residual_random_trainable | vs foundation only | 86 | +0.098 | [+0.063, +0.134] | [+0.059, +0.138] | I>0 | +0.006 | +0.109 | +0.228 | +0.001 | – |

## 6. D policy arms: binding and progress (training side only; no D test value read)

| family / arm | complete | not complete |
|---|---|---|
| D_ADAPT|complement_policy | 108 | 12 |
| D_ADAPT|dense_fm_policy | 113 | 7 |
| D_ADAPT|lag_local_tokens | 120 | 0 |
| D_ATTENTION|complement_policy | 106 | 94 |
| D_ATTENTION|dense_fm_policy | 107 | 93 |
| D_ATTENTION|lag_local_tokens | 200 | 0 |
| D_COVERAGE|complement_policy | 60 | 0 |
| D_COVERAGE|lag_local_tokens | 60 | 0 |

Policy cells: {'dense_fm_policy': 40, 'complement_policy': 40}; unresolved: 0. Chosen configuration counts (lowest training-side `best_selection_score`, ADDENDUM_04 §1):

| arm · dataset · objective | chosen configuration: cells |
|---|---|
| complement_policy · dtu · CS_SINGLE | reve/concat_pretrained: 6; cbramod/concat_pretrained: 4 |
| complement_policy · dtu · NCE | cbramod/concat_pretrained: 5; reve/concat_pretrained: 2; cbramod/residual_pretrained_frozen: 1; cbramod/residual_random_trainable: 1; cbramod/residual_random_frozen: 1 |
| complement_policy · fau · CS_SINGLE | reve/concat_pretrained: 8; cbramod/concat_pretrained: 2 |
| complement_policy · fau · NCE | cbramod/residual_pretrained_full: 2; reve/residual_random_frozen: 2; reve/concat_pretrained: 1; cbramod/residual_pretrained_peft: 1; cbramod/residual_random_frozen: 1; cbramod/residual_random_trainable: 1; cbramod/residual_pretrained_frozen: 1; reve/residual_random_trainable: 1 |
| dense_fm_policy · dtu · CS_SINGLE | cbramod/pretrained_peft/dense_query: 4; cbramod/pretrained_partial/dense_query: 3; reve/pretrained_peft/dense_query: 2; reve/random_full/dense_query: 1 |
| dense_fm_policy · dtu · NCE | reve/pretrained_peft/channel_phase_linear: 8; reve/random_full/channel_phase_linear: 1; cbramod/random_full/channel_phase_linear: 1 |
| dense_fm_policy · fau · CS_SINGLE | reve/random_full/dense_query: 3; cbramod/pretrained_full/dense_query: 2; cbramod/random_full/dense_query: 2; cbramod/pretrained_frozen/dense_query: 1; cbramod/pretrained_partial/dense_query: 1; reve/pretrained_peft/dense_query: 1 |
| dense_fm_policy · fau · NCE | reve/pretrained_peft/channel_phase_linear: 10 |

## 7. Not in this interim / pending

- Mismatched-FM-context and position-only controls (docs/06 last line) are not implemented in the C records; the attribution of any C gain to the correct pretrained EEG observation is therefore not tested beyond the random-initialization and capacity controls.
- Seed panel (3407 / 3413); D results; group × method interactions.

## Appendix: notes

190 notes (first 40 listed; all in the JSON):

- B-READOUT|federici|NCE|cbramod|sec/random_full/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_peft/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_partial/attention/unified/accuracy: no paired identities
- B-READOUT|federici|NCE|cbramod|sec/pretrained_full/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-INIT|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-ADAPT|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/random_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_peft/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_partial/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/channel_phase_linear/pretrained_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/random_full/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_frozen/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_peft/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_partial/attention/unified/accuracy: no paired identities
- B-LOCAL|federici|NCE|cbramod|sec/dense_query/pretrained_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/init_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/init_frozen/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_frozen/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_peft/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/capacity_full/attention/unified/accuracy: no paired identities
- C-ATTRIB|federici|NCE|cbramod|sec/residual_vs_concat/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/concat_pretrained/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_frozen/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_peft/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_pretrained_full/attention/unified/accuracy: no paired identities
- C-FMONLY|federici|NCE|cbramod|sec/residual_random_frozen/attention/unified/accuracy: no paired identities
