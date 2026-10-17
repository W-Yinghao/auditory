# Public local CS episode continuation

2026-10-17T22:55:54.376357+02:00; CPU job 1044744; **2/40 complete**.

Forty bundles reuse NCE local sources: DTU30 (three seeds), FAU10 (seed3401). These are CS continuations, not from-scratch CS models. Each independent person requires all registered folds/seeds; seeds do not increase n. Engineering probes are excluded. All candidate risk and mismatch-gain families, direct group interactions and actual paired coverage are retained in the aggregate JSON.

Primary comparison: episode-CS versus ordinary-CS with matched source weights, support computation, samples and100 encoder updates. A separate unified-readout NCE-versus-CS selected-policy comparison changes continuation objective and policy selection/readout protocol; it is a package comparison. Native NCE and CS scores are not treated as the same readout.

## dtu / episode/cs/mismatch_gain/support_0.1 / native / 3401

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00056, +0.00037] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00017 | [-0.00080, +0.00046] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00013 | [-0.00062, +0.00036] |
| episode_selected versus ordinary_selected | -0.00020 | [-0.00071, +0.00031] |
| episode_selected versus source_no_adaptation | -0.00544 | [-0.19580, +0.18492] |
| fixed_episode/0 versus source_no_adaptation | -0.21845 | [-0.54040, +0.10350] |
| fixed_episode/20 versus source_no_adaptation | -0.17888 | [-0.50770, +0.14994] |
| fixed_episode/5 versus source_no_adaptation | -0.21490 | [-0.53627, +0.10647] |
| fixed_ordinary/0 versus source_no_adaptation | -0.21835 | [-0.54030, +0.10360] |
| fixed_ordinary/20 versus source_no_adaptation | -0.17871 | [-0.50741, +0.14999] |
| fixed_ordinary/5 versus source_no_adaptation | -0.21477 | [-0.53615, +0.10661] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.13313 | [-0.04003, +0.30628] |
| fixed_source/5 versus source_no_adaptation | +0.00878 | [-0.00106, +0.01863] |
| ordinary_selected versus source_no_adaptation | -0.00524 | [-0.19537, +0.18489] |

## dtu / episode/cs/mismatch_gain/support_0.1 / unified / 3401

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00019 | [-0.00060, +0.00022] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00025 | [-0.00074, +0.00023] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00022 | [-0.00062, +0.00019] |
| episode_selected versus ordinary_selected | -0.00025 | [-0.00066, +0.00015] |
| episode_selected versus source_no_adaptation | -0.03848 | [-0.17163, +0.09467] |
| fixed_episode/0 versus source_no_adaptation | -0.04357 | [-0.21405, +0.12690] |
| fixed_episode/20 versus source_no_adaptation | -0.02466 | [-0.20606, +0.15675] |
| fixed_episode/5 versus source_no_adaptation | -0.04097 | [-0.21242, +0.13048] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04338 | [-0.21396, +0.12720] |
| fixed_ordinary/20 versus source_no_adaptation | -0.02440 | [-0.20569, +0.15688] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04075 | [-0.21228, +0.13077] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.01750 | [-0.16450, +0.19950] |
| fixed_source/5 versus source_no_adaptation | +0.00297 | [-0.00804, +0.01398] |
| ordinary_selected versus source_no_adaptation | -0.03823 | [-0.17125, +0.09480] |

## dtu / episode/cs/mismatch_gain/support_0.3 / native / 3401

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00059, +0.00040] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00009 | [-0.00053, +0.00035] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00011 | [-0.00061, +0.00040] |
| episode_selected versus ordinary_selected | -0.00010 | [-0.00044, +0.00023] |
| episode_selected versus source_no_adaptation | -0.02653 | [-0.19614, +0.14308] |
| fixed_episode/0 versus source_no_adaptation | -0.21845 | [-0.55975, +0.12285] |
| fixed_episode/20 versus source_no_adaptation | -0.15841 | [-0.50205, +0.18522] |
| fixed_episode/5 versus source_no_adaptation | -0.21367 | [-0.55438, +0.12704] |
| fixed_ordinary/0 versus source_no_adaptation | -0.21835 | [-0.55965, +0.12295] |
| fixed_ordinary/20 versus source_no_adaptation | -0.15832 | [-0.50199, +0.18535] |
| fixed_ordinary/5 versus source_no_adaptation | -0.21356 | [-0.55431, +0.12718] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.14753 | [-0.06857, +0.36364] |
| fixed_source/5 versus source_no_adaptation | +0.00989 | [-0.00309, +0.02287] |
| ordinary_selected versus source_no_adaptation | -0.02643 | [-0.19591, +0.14305] |

## dtu / episode/cs/mismatch_gain/support_0.3 / unified / 3401

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00019 | [-0.00057, +0.00018] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00017 | [-0.00056, +0.00021] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00021 | [-0.00060, +0.00017] |
| episode_selected versus ordinary_selected | -0.00016 | [-0.00039, +0.00006] |
| episode_selected versus source_no_adaptation | -0.04050 | [-0.14052, +0.05953] |
| fixed_episode/0 versus source_no_adaptation | -0.04357 | [-0.19857, +0.11143] |
| fixed_episode/20 versus source_no_adaptation | -0.01845 | [-0.15908, +0.12218] |
| fixed_episode/5 versus source_no_adaptation | -0.04093 | [-0.19484, +0.11298] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04338 | [-0.19848, +0.11171] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01828 | [-0.15897, +0.12242] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04072 | [-0.19473, +0.11328] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.00450 | [-0.16213, +0.17113] |
| fixed_source/5 versus source_no_adaptation | +0.00245 | [-0.00809, +0.01298] |
| ordinary_selected versus source_no_adaptation | -0.04033 | [-0.14035, +0.05968] |

## dtu / episode/local/support_0.1 / native / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00032, +0.00011] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00018 | [-0.00049, +0.00014] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00012 | [-0.00035, +0.00011] |
| episode_selected versus ordinary_selected | -0.00019 | [-0.00048, +0.00010] |
| episode_selected versus source_no_adaptation | -0.07690 | [-0.19279, +0.03900] |
| fixed_episode/0 versus source_no_adaptation | -0.05177 | [-0.18620, +0.08265] |
| fixed_episode/20 versus source_no_adaptation | -0.06812 | [-0.21118, +0.07494] |
| fixed_episode/5 versus source_no_adaptation | -0.05241 | [-0.18694, +0.08211] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05167 | [-0.18611, +0.08277] |
| fixed_ordinary/20 versus source_no_adaptation | -0.06795 | [-0.21094, +0.07505] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05229 | [-0.18682, +0.08223] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.01648 | [-0.13620, +0.10324] |
| fixed_source/5 versus source_no_adaptation | +0.00113 | [-0.00508, +0.00734] |
| ordinary_selected versus source_no_adaptation | -0.07671 | [-0.19249, +0.03908] |

## dtu / episode/local/support_0.1 / unified / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00015 | [-0.00042, +0.00012] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00018 | [-0.00052, +0.00017] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00016 | [-0.00044, +0.00012] |
| episode_selected versus ordinary_selected | -0.00018 | [-0.00046, +0.00011] |
| episode_selected versus source_no_adaptation | -0.04843 | [-0.14939, +0.05253] |
| fixed_episode/0 versus source_no_adaptation | -0.04709 | [-0.19479, +0.10062] |
| fixed_episode/20 versus source_no_adaptation | -0.05164 | [-0.19349, +0.09022] |
| fixed_episode/5 versus source_no_adaptation | -0.04649 | [-0.19381, +0.10083] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04694 | [-0.19471, +0.10084] |
| fixed_ordinary/20 versus source_no_adaptation | -0.05146 | [-0.19324, +0.09032] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04633 | [-0.19370, +0.10104] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.01745 | [-0.11752, +0.15242] |
| fixed_source/5 versus source_no_adaptation | +0.00259 | [-0.00597, +0.01116] |
| ordinary_selected versus source_no_adaptation | -0.04826 | [-0.14918, +0.05267] |

## dtu / episode/local/support_0.3 / native / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00035, +0.00014] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00014 | [-0.00041, +0.00014] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00011 | [-0.00036, +0.00014] |
| episode_selected versus ordinary_selected | -0.00009 | [-0.00027, +0.00008] |
| episode_selected versus source_no_adaptation | -0.06466 | [-0.18074, +0.05141] |
| fixed_episode/0 versus source_no_adaptation | -0.05177 | [-0.20418, +0.10064] |
| fixed_episode/20 versus source_no_adaptation | -0.05042 | [-0.19825, +0.09742] |
| fixed_episode/5 versus source_no_adaptation | -0.05133 | [-0.20241, +0.09975] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05167 | [-0.20409, +0.10075] |
| fixed_ordinary/20 versus source_no_adaptation | -0.05028 | [-0.19817, +0.09761] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05122 | [-0.20230, +0.09987] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03717 | [-0.19995, +0.12560] |
| fixed_source/5 versus source_no_adaptation | +0.00050 | [-0.00800, +0.00901] |
| ordinary_selected versus source_no_adaptation | -0.06457 | [-0.18058, +0.05144] |

## dtu / episode/local/support_0.3 / unified / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00015 | [-0.00041, +0.00011] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00016 | [-0.00049, +0.00017] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00016 | [-0.00042, +0.00010] |
| episode_selected versus ordinary_selected | -0.00011 | [-0.00027, +0.00006] |
| episode_selected versus source_no_adaptation | -0.04065 | [-0.13208, +0.05077] |
| fixed_episode/0 versus source_no_adaptation | -0.04709 | [-0.18874, +0.09457] |
| fixed_episode/20 versus source_no_adaptation | -0.03892 | [-0.15488, +0.07703] |
| fixed_episode/5 versus source_no_adaptation | -0.04578 | [-0.18601, +0.09444] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04694 | [-0.18866, +0.09478] |
| fixed_ordinary/20 versus source_no_adaptation | -0.03876 | [-0.15476, +0.07723] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04563 | [-0.18593, +0.09467] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.00778 | [-0.13064, +0.14619] |
| fixed_source/5 versus source_no_adaptation | +0.00231 | [-0.00644, +0.01105] |
| ordinary_selected versus source_no_adaptation | -0.04055 | [-0.13196, +0.05087] |

