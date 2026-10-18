# ALN3.2 paired seed panel (seeds 3401, 3407, 3413)

Generated 2026-10-18 13:27 CEST (Slurm 1045980) by `python -m auditory_alignment_v3.aln32_panel_interim` under the frozen `ADDENDUM_11_ALN32_SEED_PANEL.md`. ΔR = R(reference) − R(candidate), positive = candidate lower true-query risk; per-seed families and the three-seed family (identity values averaged over seeds) each with max-t simultaneous intervals. Seed SD mixes training and readout-sampling variation.

Code sha256: `aln32_panel_interim.py` b95c78a41176, `bc_interim.py` 2840df81b608, `sci_r1/stats.py` 8bb141cf6070.

| role · dataset · member | seed 3401 | seed 3407 | seed 3413 | per-seed mean / range | three-seed ΔR [simultaneous] |
|---|---|---|---|---|---|
| adaptation · dtu · cbramod | +0.067 | +0.069 | +0.077 | +0.071 / [+0.067, +0.077] | +0.071 [+0.042, +0.100] I>0 |
| adaptation · dtu · reve | +0.044 | +0.048 | +0.039 | +0.044 / [+0.039, +0.048] | +0.044 [+0.032, +0.056] I>0 |
| adaptation · fau · cbramod | +0.127 | +0.156 | +0.139 | +0.141 / [+0.127, +0.156] | +0.141 [+0.100, +0.181] I>0 |
| adaptation · fau · reve | +0.033 | +0.027 | +0.037 | +0.032 / [+0.027, +0.037] | +0.032 [+0.012, +0.052] I>0 |
| adaptation · federici · cbramod | +0.021 | +0.004 | +0.028 | +0.018 / [+0.004, +0.028] | +0.018 [-0.001, +0.037] contains 0 |
| adaptation · federici · reve | +0.048 | +0.052 | +0.018 | +0.039 / [+0.018, +0.052] | +0.039 [+0.017, +0.062] I>0 |
| aligned_access_matched · dtu · cbramod | -0.339 | -0.328 | -0.368 | -0.345 / [-0.368, -0.328] | -0.345 [-0.459, -0.231] I<0 |
| aligned_access_matched · dtu · reve | -0.239 | -0.196 | -0.229 | -0.221 / [-0.239, -0.196] | -0.221 [-0.305, -0.138] I<0 |
| aligned_access_matched · fau · cbramod | -0.119 | -0.136 | -0.136 | -0.130 / [-0.136, -0.119] | -0.130 [-0.207, -0.054] I<0 |
| aligned_access_matched · fau · reve | +0.029 | +0.036 | +0.001 | +0.022 / [+0.001, +0.036] | +0.022 [-0.020, +0.064] contains 0 |
| aligned_access_matched · federici · cbramod | -0.119 | -0.169 | -0.165 | -0.151 / [-0.169, -0.119] | -0.151 [-0.195, -0.108] I<0 |
| aligned_access_matched · federici · reve | +0.069 | +0.049 | +0.080 | +0.066 / [+0.049, +0.080] | +0.066 [+0.029, +0.104] I>0 |
| capacity · dtu · cbramod | -0.015 | -0.016 | -0.013 | -0.015 / [-0.016, -0.013] | -0.015 [-0.023, -0.007] I<0 |
| capacity · dtu · reve | -0.016 | -0.016 | -0.013 | -0.015 / [-0.016, -0.013] | -0.015 [-0.023, -0.007] I<0 |
| capacity · fau · cbramod | -0.007 | -0.007 | -0.006 | -0.006 / [-0.007, -0.006] | -0.006 [-0.009, -0.004] I<0 |
| capacity · fau · reve | -0.006 | -0.007 | -0.005 | -0.006 / [-0.007, -0.005] | -0.006 [-0.008, -0.004] I<0 |
| capacity · federici · cbramod | -0.001 | +0.000 | -0.000 | -0.000 / [-0.001, +0.000] | -0.000 [-0.001, +0.001] contains 0 |
| capacity · federici · reve | -0.001 | +0.001 | -0.001 | -0.000 / [-0.001, +0.001] | -0.000 [-0.001, +0.001] contains 0 |
| complement_source · dtu · cbramod | +0.000 | +0.000 | -0.000 | +0.000 / [-0.000, +0.000] | +0.000 [-0.000, +0.000] contains 0 |
| complement_source · dtu · reve | +0.000 | +0.000 | +0.000 | +0.000 / [+0.000, +0.000] | +0.000 [-0.000, +0.001] contains 0 |
| complement_source · fau · cbramod | -0.000 | +0.000 | -0.000 | -0.000 / [-0.000, +0.000] | -0.000 [-0.000, +0.000] contains 0 |
| complement_source · fau · reve | +0.001 | -0.000 | +0.000 | +0.000 / [-0.000, +0.001] | +0.000 [-0.000, +0.000] contains 0 |
| complement_source · federici · cbramod | +0.001 | -0.000 | +0.001 | +0.001 / [-0.000, +0.001] | +0.001 [+0.000, +0.001] I>0 |
| complement_source · federici · reve | +0.001 | +0.000 | -0.000 | +0.000 / [-0.000, +0.001] | +0.000 [+0.000, +0.001] I>0 |
| complement_value · dtu · cbramod | +0.000 | -0.000 | -0.001 | -0.000 / [-0.001, +0.000] | -0.000 [-0.001, +0.000] contains 0 |
| complement_value · dtu · reve | +0.000 | -0.000 | -0.001 | -0.000 / [-0.001, +0.000] | -0.000 [-0.001, +0.000] contains 0 |
| complement_value · fau · cbramod | -0.000 | -0.003 | +0.000 | -0.001 / [-0.003, +0.000] | -0.001 [-0.003, +0.001] contains 0 |
| complement_value · fau · reve | +0.000 | -0.003 | +0.001 | -0.001 / [-0.003, +0.001] | -0.001 [-0.003, +0.001] contains 0 |
| complement_value · federici · cbramod | +0.001 | -0.000 | +0.001 | +0.000 / [-0.000, +0.001] | +0.000 [-0.000, +0.001] contains 0 |
| complement_value · federici · reve | +0.001 | +0.000 | -0.000 | +0.000 / [-0.000, +0.001] | +0.000 [+0.000, +0.001] I>0 |
| initialization_true_full · dtu · cbramod/lr0.0003 | +0.231 | +0.172 | +0.196 | +0.200 / [+0.172, +0.231] | +0.200 [+0.135, +0.265] I>0 |
| initialization_true_full · dtu · cbramod/lr1e-05 | +0.535 | +0.414 | +0.487 | +0.479 / [+0.414, +0.535] | +0.479 [+0.390, +0.568] I>0 |
| initialization_true_full · dtu · reve/lr0.0003 | +0.062 | +0.115 | +0.206 | +0.128 / [+0.062, +0.206] | +0.128 [+0.044, +0.211] I>0 |
| initialization_true_full · dtu · reve/lr1e-05 | +0.015 | +0.073 | +0.040 | +0.043 / [+0.015, +0.073] | +0.043 [-0.044, +0.129] contains 0 |
| initialization_true_full · fau · cbramod/lr0.0003 | +0.120 | +0.085 | +0.067 | +0.091 / [+0.067, +0.120] | +0.091 [+0.057, +0.125] I>0 |
| initialization_true_full · fau · cbramod/lr1e-05 | +0.132 | +0.094 | +0.120 | +0.115 / [+0.094, +0.132] | +0.115 [+0.061, +0.170] I>0 |
| initialization_true_full · fau · reve/lr0.0003 | -0.023 | -0.065 | +0.015 | -0.024 / [-0.065, +0.015] | -0.024 [-0.068, +0.019] contains 0 |
| initialization_true_full · fau · reve/lr1e-05 | +0.010 | +0.035 | +0.024 | +0.023 / [+0.010, +0.035] | +0.023 [-0.021, +0.068] contains 0 |
| initialization_true_full · federici · cbramod/lr0.0003 | +0.055 | +0.049 | +0.050 | +0.051 / [+0.049, +0.055] | +0.051 [+0.020, +0.083] I>0 |
| initialization_true_full · federici · cbramod/lr1e-05 | +0.117 | +0.144 | +0.077 | +0.113 / [+0.077, +0.144] | +0.113 [+0.060, +0.166] I>0 |
| initialization_true_full · federici · reve/lr0.0003 | -0.016 | -0.043 | -0.007 | -0.022 / [-0.043, -0.007] | -0.022 [-0.053, +0.010] contains 0 |
| initialization_true_full · federici · reve/lr1e-05 | -0.087 | -0.122 | -0.089 | -0.099 / [-0.122, -0.087] | -0.099 [-0.156, -0.043] I<0 |
