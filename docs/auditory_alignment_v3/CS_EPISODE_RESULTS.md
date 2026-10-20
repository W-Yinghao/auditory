# Public local CS episode continuation

2026-10-19T09:24:15.300042+02:00; CPU job 1047358; **40/40 complete**.

Forty bundles reuse NCE local sources: DTU30 (three seeds), FAU10 (seed3401). These are CS continuations, not from-scratch CS models. Each independent person requires all registered folds/seeds; seeds do not increase n. Engineering probes are excluded. All candidate risk and mismatch-gain families, direct group interactions and actual paired coverage are retained in the aggregate JSON.

Primary comparison: episode-CS versus ordinary-CS with matched source weights, support computation, samples and100 encoder updates. A separate unified-readout NCE-versus-CS selected-policy comparison changes continuation objective and policy selection/readout protocol; it is a package comparison. Native NCE and CS scores are not treated as the same readout.

## dtu / episode/cs/mismatch_gain/support_0.1 / native / 3401

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00009 | [-0.00019, +0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.00002 | [-0.00025, +0.00029] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00009 | [-0.00020, +0.00002] |
| episode_selected versus ordinary_selected | -0.00006 | [-0.00016, +0.00003] |
| episode_selected versus source_no_adaptation | -0.00576 | [-0.06348, +0.05195] |
| fixed_episode/0 versus source_no_adaptation | -0.15516 | [-0.26110, -0.04922] |
| fixed_episode/20 versus source_no_adaptation | -0.15394 | [-0.27086, -0.03702] |
| fixed_episode/5 versus source_no_adaptation | -0.15320 | [-0.25947, -0.04692] |
| fixed_ordinary/0 versus source_no_adaptation | -0.15507 | [-0.26102, -0.04912] |
| fixed_ordinary/20 versus source_no_adaptation | -0.15396 | [-0.27078, -0.03714] |
| fixed_ordinary/5 versus source_no_adaptation | -0.15311 | [-0.25939, -0.04683] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.12185 | [+0.04897, +0.19472] |
| fixed_source/5 versus source_no_adaptation | +0.00888 | [+0.00537, +0.01238] |
| ordinary_selected versus source_no_adaptation | -0.00570 | [-0.06341, +0.05201] |

## dtu / episode/cs/mismatch_gain/support_0.1 / native / 3407

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00013 | [-0.00027, +0.00002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00011 | [-0.00035, +0.00012] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00013 | [-0.00027, +0.00001] |
| episode_selected versus ordinary_selected | +0.00841 | [-0.00988, +0.02670] |
| episode_selected versus source_no_adaptation | -0.04536 | [-0.13720, +0.04649] |
| fixed_episode/0 versus source_no_adaptation | -0.10622 | [-0.22158, +0.00914] |
| fixed_episode/20 versus source_no_adaptation | -0.11895 | [-0.24686, +0.00896] |
| fixed_episode/5 versus source_no_adaptation | -0.10519 | [-0.22099, +0.01060] |
| fixed_ordinary/0 versus source_no_adaptation | -0.10610 | [-0.22140, +0.00920] |
| fixed_ordinary/20 versus source_no_adaptation | -0.11884 | [-0.24670, +0.00902] |
| fixed_ordinary/5 versus source_no_adaptation | -0.10507 | [-0.22081, +0.01067] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.08884 | [+0.02286, +0.15482] |
| fixed_source/5 versus source_no_adaptation | +0.00742 | [+0.00381, +0.01102] |
| ordinary_selected versus source_no_adaptation | -0.05377 | [-0.14108, +0.03355] |

## dtu / episode/cs/mismatch_gain/support_0.1 / native / 3413

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00024 | [-0.00040, -0.00007] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00026 | [-0.00045, -0.00007] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00023 | [-0.00039, -0.00006] |
| episode_selected versus ordinary_selected | -0.00014 | [-0.00025, -0.00002] |
| episode_selected versus source_no_adaptation | -0.00667 | [-0.08620, +0.07285] |
| fixed_episode/0 versus source_no_adaptation | -0.28222 | [-0.38268, -0.18175] |
| fixed_episode/20 versus source_no_adaptation | -0.28234 | [-0.39465, -0.17003] |
| fixed_episode/5 versus source_no_adaptation | -0.28055 | [-0.38152, -0.17958] |
| fixed_ordinary/0 versus source_no_adaptation | -0.28198 | [-0.38240, -0.18156] |
| fixed_ordinary/20 versus source_no_adaptation | -0.28208 | [-0.39436, -0.16981] |
| fixed_ordinary/5 versus source_no_adaptation | -0.28032 | [-0.38125, -0.17939] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.11391 | [+0.03458, +0.19325] |
| fixed_source/5 versus source_no_adaptation | +0.00909 | [+0.00428, +0.01390] |
| ordinary_selected versus source_no_adaptation | -0.00654 | [-0.08604, +0.07296] |

## dtu / episode/cs/mismatch_gain/support_0.1 / native / complete_seed_mean

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00015 | [-0.00026, -0.00004] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00012 | [-0.00025, +0.00002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00015 | [-0.00025, -0.00004] |
| episode_selected versus ordinary_selected | +0.00274 | [-0.00290, +0.00837] |
| episode_selected versus source_no_adaptation | -0.01926 | [-0.07921, +0.04068] |
| fixed_episode/0 versus source_no_adaptation | -0.18120 | [-0.26719, -0.09521] |
| fixed_episode/20 versus source_no_adaptation | -0.18508 | [-0.28474, -0.08542] |
| fixed_episode/5 versus source_no_adaptation | -0.17965 | [-0.26627, -0.09303] |
| fixed_ordinary/0 versus source_no_adaptation | -0.18105 | [-0.26701, -0.09508] |
| fixed_ordinary/20 versus source_no_adaptation | -0.18496 | [-0.28458, -0.08534] |
| fixed_ordinary/5 versus source_no_adaptation | -0.17950 | [-0.26610, -0.09290] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.10820 | [+0.04185, +0.17455] |
| fixed_source/5 versus source_no_adaptation | +0.00846 | [+0.00495, +0.01197] |
| ordinary_selected versus source_no_adaptation | -0.02200 | [-0.08085, +0.03685] |

## dtu / episode/cs/mismatch_gain/support_0.1 / unified / 3401

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00016 | [-0.00026, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00024 | [-0.00039, -0.00008] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00016 | [-0.00027, -0.00006] |
| episode_selected versus ordinary_selected | -0.00010 | [-0.00019, -0.00001] |
| episode_selected versus source_no_adaptation | -0.13387 | [-0.21468, -0.05305] |
| fixed_episode/0 versus source_no_adaptation | -0.16277 | [-0.27504, -0.05050] |
| fixed_episode/20 versus source_no_adaptation | -0.20406 | [-0.33138, -0.07673] |
| fixed_episode/5 versus source_no_adaptation | -0.16367 | [-0.27659, -0.05075] |
| fixed_ordinary/0 versus source_no_adaptation | -0.16261 | [-0.27489, -0.05034] |
| fixed_ordinary/20 versus source_no_adaptation | -0.20382 | [-0.33112, -0.07652] |
| fixed_ordinary/5 versus source_no_adaptation | -0.16350 | [-0.27643, -0.05058] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03089 | [-0.09477, +0.03298] |
| fixed_source/5 versus source_no_adaptation | +0.00118 | [-0.00200, +0.00435] |
| ordinary_selected versus source_no_adaptation | -0.13377 | [-0.21459, -0.05294] |

## dtu / episode/cs/mismatch_gain/support_0.1 / unified / 3407

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00021 | [-0.00037, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00029 | [-0.00055, -0.00004] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00021 | [-0.00037, -0.00006] |
| episode_selected versus ordinary_selected | +0.00271 | [-0.01624, +0.02166] |
| episode_selected versus source_no_adaptation | -0.03457 | [-0.08547, +0.01633] |
| fixed_episode/0 versus source_no_adaptation | -0.05646 | [-0.13681, +0.02390] |
| fixed_episode/20 versus source_no_adaptation | -0.10048 | [-0.19682, -0.00414] |
| fixed_episode/5 versus source_no_adaptation | -0.05749 | [-0.13854, +0.02356] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05625 | [-0.13658, +0.02409] |
| fixed_ordinary/20 versus source_no_adaptation | -0.10019 | [-0.19650, -0.00388] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05728 | [-0.13830, +0.02375] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03896 | [-0.09553, +0.01760] |
| fixed_source/5 versus source_no_adaptation | +0.00112 | [-0.00213, +0.00437] |
| ordinary_selected versus source_no_adaptation | -0.03728 | [-0.08341, +0.00885] |

## dtu / episode/cs/mismatch_gain/support_0.1 / unified / 3413

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00040 | [-0.00057, -0.00023] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00046 | [-0.00066, -0.00025] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00039 | [-0.00056, -0.00022] |
| episode_selected versus ordinary_selected | -0.00020 | [-0.00032, -0.00009] |
| episode_selected versus source_no_adaptation | -0.05248 | [-0.10596, +0.00099] |
| fixed_episode/0 versus source_no_adaptation | -0.04215 | [-0.11310, +0.02880] |
| fixed_episode/20 versus source_no_adaptation | -0.09203 | [-0.18528, +0.00122] |
| fixed_episode/5 versus source_no_adaptation | -0.04375 | [-0.11570, +0.02819] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04175 | [-0.11268, +0.02917] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09157 | [-0.18478, +0.00164] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04337 | [-0.11528, +0.02855] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03618 | [-0.09232, +0.01996] |
| fixed_source/5 versus source_no_adaptation | +0.00096 | [-0.00257, +0.00449] |
| ordinary_selected versus source_no_adaptation | -0.05228 | [-0.10569, +0.00113] |

## dtu / episode/cs/mismatch_gain/support_0.1 / unified / complete_seed_mean

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00025 | [-0.00037, -0.00014] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00033 | [-0.00048, -0.00018] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00026 | [-0.00037, -0.00014] |
| episode_selected versus ordinary_selected | +0.00080 | [-0.00511, +0.00671] |
| episode_selected versus source_no_adaptation | -0.07364 | [-0.12505, -0.02223] |
| fixed_episode/0 versus source_no_adaptation | -0.08713 | [-0.16491, -0.00934] |
| fixed_episode/20 versus source_no_adaptation | -0.13219 | [-0.22672, -0.03766] |
| fixed_episode/5 versus source_no_adaptation | -0.08830 | [-0.16689, -0.00972] |
| fixed_ordinary/0 versus source_no_adaptation | -0.08687 | [-0.16464, -0.00911] |
| fixed_ordinary/20 versus source_no_adaptation | -0.13186 | [-0.22636, -0.03736] |
| fixed_ordinary/5 versus source_no_adaptation | -0.08805 | [-0.16661, -0.00949] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03534 | [-0.08945, +0.01876] |
| fixed_source/5 versus source_no_adaptation | +0.00109 | [-0.00186, +0.00403] |
| ordinary_selected versus source_no_adaptation | -0.07444 | [-0.12536, -0.02352] |

## dtu / episode/cs/mismatch_gain/support_0.3 / native / 3401

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00009 | [-0.00018, -0.00000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00014 | [-0.00026, -0.00002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00010 | [-0.00019, -0.00001] |
| episode_selected versus ordinary_selected | -0.00006 | [-0.00013, +0.00001] |
| episode_selected versus source_no_adaptation | +0.00140 | [-0.05173, +0.05453] |
| fixed_episode/0 versus source_no_adaptation | -0.15516 | [-0.25050, -0.05983] |
| fixed_episode/20 versus source_no_adaptation | -0.13020 | [-0.24149, -0.01890] |
| fixed_episode/5 versus source_no_adaptation | -0.15220 | [-0.24819, -0.05622] |
| fixed_ordinary/0 versus source_no_adaptation | -0.15507 | [-0.25042, -0.05973] |
| fixed_ordinary/20 versus source_no_adaptation | -0.13006 | [-0.24135, -0.01877] |
| fixed_ordinary/5 versus source_no_adaptation | -0.15210 | [-0.24810, -0.05611] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.14149 | [+0.06737, +0.21561] |
| fixed_source/5 versus source_no_adaptation | +0.01029 | [+0.00629, +0.01428] |
| ordinary_selected versus source_no_adaptation | +0.00146 | [-0.05168, +0.05460] |

## dtu / episode/cs/mismatch_gain/support_0.3 / native / 3407

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00013 | [-0.00027, +0.00002] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00013 | [-0.00032, +0.00007] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00013 | [-0.00027, +0.00002] |
| episode_selected versus ordinary_selected | -0.00006 | [-0.00012, +0.00000] |
| episode_selected versus source_no_adaptation | -0.06242 | [-0.14502, +0.02017] |
| fixed_episode/0 versus source_no_adaptation | -0.10622 | [-0.22127, +0.00882] |
| fixed_episode/20 versus source_no_adaptation | -0.09747 | [-0.22886, +0.03391] |
| fixed_episode/5 versus source_no_adaptation | -0.10411 | [-0.21981, +0.01159] |
| fixed_ordinary/0 versus source_no_adaptation | -0.10610 | [-0.22108, +0.00889] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09735 | [-0.22867, +0.03398] |
| fixed_ordinary/5 versus source_no_adaptation | -0.10399 | [-0.21963, +0.01165] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.10907 | [+0.02058, +0.19755] |
| fixed_source/5 versus source_no_adaptation | +0.00855 | [+0.00360, +0.01350] |
| ordinary_selected versus source_no_adaptation | -0.06237 | [-0.14494, +0.02021] |

## dtu / episode/cs/mismatch_gain/support_0.3 / native / 3413

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00024 | [-0.00041, -0.00006] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00030 | [-0.00055, -0.00005] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00023 | [-0.00041, -0.00006] |
| episode_selected versus ordinary_selected | -0.00015 | [-0.00031, +0.00000] |
| episode_selected versus source_no_adaptation | +0.01717 | [-0.07354, +0.10788] |
| fixed_episode/0 versus source_no_adaptation | -0.28222 | [-0.38831, -0.17612] |
| fixed_episode/20 versus source_no_adaptation | -0.25630 | [-0.37830, -0.13430] |
| fixed_episode/5 versus source_no_adaptation | -0.27906 | [-0.38605, -0.17207] |
| fixed_ordinary/0 versus source_no_adaptation | -0.28198 | [-0.38803, -0.17593] |
| fixed_ordinary/20 versus source_no_adaptation | -0.25600 | [-0.37791, -0.13409] |
| fixed_ordinary/5 versus source_no_adaptation | -0.27883 | [-0.38577, -0.17188] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.14441 | [+0.05368, +0.23514] |
| fixed_source/5 versus source_no_adaptation | +0.01124 | [+0.00535, +0.01713] |
| ordinary_selected versus source_no_adaptation | +0.01732 | [-0.07335, +0.10800] |

## dtu / episode/cs/mismatch_gain/support_0.3 / native / complete_seed_mean

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00015 | [-0.00025, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00019 | [-0.00033, -0.00005] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00015 | [-0.00026, -0.00005] |
| episode_selected versus ordinary_selected | -0.00009 | [-0.00015, -0.00003] |
| episode_selected versus source_no_adaptation | -0.01462 | [-0.06910, +0.03986] |
| fixed_episode/0 versus source_no_adaptation | -0.18120 | [-0.26485, -0.09755] |
| fixed_episode/20 versus source_no_adaptation | -0.16132 | [-0.26180, -0.06085] |
| fixed_episode/5 versus source_no_adaptation | -0.17846 | [-0.26298, -0.09394] |
| fixed_ordinary/0 versus source_no_adaptation | -0.18105 | [-0.26468, -0.09742] |
| fixed_ordinary/20 versus source_no_adaptation | -0.16113 | [-0.26157, -0.06070] |
| fixed_ordinary/5 versus source_no_adaptation | -0.17831 | [-0.26280, -0.09381] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.13166 | [+0.05512, +0.20819] |
| fixed_source/5 versus source_no_adaptation | +0.01003 | [+0.00564, +0.01442] |
| ordinary_selected versus source_no_adaptation | -0.01453 | [-0.06898, +0.03993] |

## dtu / episode/cs/mismatch_gain/support_0.3 / unified / 3401

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00016 | [-0.00026, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00027 | [-0.00041, -0.00013] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00017 | [-0.00028, -0.00006] |
| episode_selected versus ordinary_selected | -0.00010 | [-0.00019, -0.00001] |
| episode_selected versus source_no_adaptation | -0.08092 | [-0.15488, -0.00697] |
| fixed_episode/0 versus source_no_adaptation | -0.16277 | [-0.27512, -0.05042] |
| fixed_episode/20 versus source_no_adaptation | -0.18376 | [-0.31142, -0.05609] |
| fixed_episode/5 versus source_no_adaptation | -0.16287 | [-0.27605, -0.04969] |
| fixed_ordinary/0 versus source_no_adaptation | -0.16261 | [-0.27496, -0.05026] |
| fixed_ordinary/20 versus source_no_adaptation | -0.18349 | [-0.31112, -0.05586] |
| fixed_ordinary/5 versus source_no_adaptation | -0.16270 | [-0.27588, -0.04951] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.02801 | [-0.09955, +0.04354] |
| fixed_source/5 versus source_no_adaptation | +0.00213 | [-0.00207, +0.00632] |
| ordinary_selected versus source_no_adaptation | -0.08082 | [-0.15479, -0.00686] |

## dtu / episode/cs/mismatch_gain/support_0.3 / unified / 3407

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00021 | [-0.00036, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00027 | [-0.00047, -0.00007] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00021 | [-0.00038, -0.00005] |
| episode_selected versus ordinary_selected | -0.00009 | [-0.00017, -0.00001] |
| episode_selected versus source_no_adaptation | -0.03143 | [-0.07012, +0.00726] |
| fixed_episode/0 versus source_no_adaptation | -0.05646 | [-0.13616, +0.02325] |
| fixed_episode/20 versus source_no_adaptation | -0.08254 | [-0.18227, +0.01719] |
| fixed_episode/5 versus source_no_adaptation | -0.05638 | [-0.13715, +0.02439] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05625 | [-0.13593, +0.02344] |
| fixed_ordinary/20 versus source_no_adaptation | -0.08227 | [-0.18196, +0.01742] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05617 | [-0.13691, +0.02458] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03099 | [-0.09629, +0.03431] |
| fixed_source/5 versus source_no_adaptation | +0.00175 | [-0.00188, +0.00537] |
| ordinary_selected versus source_no_adaptation | -0.03134 | [-0.06999, +0.00731] |

## dtu / episode/cs/mismatch_gain/support_0.3 / unified / 3413

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00040 | [-0.00057, -0.00023] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00055 | [-0.00080, -0.00031] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00040 | [-0.00058, -0.00023] |
| episode_selected versus ordinary_selected | -0.00022 | [-0.00037, -0.00007] |
| episode_selected versus source_no_adaptation | -0.03921 | [-0.09203, +0.01360] |
| fixed_episode/0 versus source_no_adaptation | -0.04215 | [-0.11390, +0.02960] |
| fixed_episode/20 versus source_no_adaptation | -0.06836 | [-0.16187, +0.02515] |
| fixed_episode/5 versus source_no_adaptation | -0.04257 | [-0.11561, +0.03046] |
| fixed_ordinary/0 versus source_no_adaptation | -0.04175 | [-0.11348, +0.02997] |
| fixed_ordinary/20 versus source_no_adaptation | -0.06781 | [-0.16123, +0.02561] |
| fixed_ordinary/5 versus source_no_adaptation | -0.04217 | [-0.11517, +0.03084] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.01503 | [-0.08032, +0.05025] |
| fixed_source/5 versus source_no_adaptation | +0.00288 | [-0.00144, +0.00720] |
| ordinary_selected versus source_no_adaptation | -0.03899 | [-0.09174, +0.01375] |

## dtu / episode/cs/mismatch_gain/support_0.3 / unified / complete_seed_mean

Paired n=44/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00025 | [-0.00037, -0.00014] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00036 | [-0.00051, -0.00022] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00026 | [-0.00038, -0.00014] |
| episode_selected versus ordinary_selected | -0.00014 | [-0.00021, -0.00007] |
| episode_selected versus source_no_adaptation | -0.05052 | [-0.09712, -0.00393] |
| fixed_episode/0 versus source_no_adaptation | -0.08713 | [-0.16690, -0.00735] |
| fixed_episode/20 versus source_no_adaptation | -0.11155 | [-0.21009, -0.01302] |
| fixed_episode/5 versus source_no_adaptation | -0.08727 | [-0.16813, -0.00642] |
| fixed_ordinary/0 versus source_no_adaptation | -0.08687 | [-0.16662, -0.00712] |
| fixed_ordinary/20 versus source_no_adaptation | -0.11119 | [-0.20966, -0.01272] |
| fixed_ordinary/5 versus source_no_adaptation | -0.08701 | [-0.16784, -0.00618] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.02468 | [-0.08900, +0.03965] |
| fixed_source/5 versus source_no_adaptation | +0.00225 | [-0.00147, +0.00597] |
| ordinary_selected versus source_no_adaptation | -0.05039 | [-0.09694, -0.00383] |

## dtu / episode/cs_vs_nce_package/support_0.1 / unified / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.04389 | [-0.07199, -0.01580] |
| CS/ordinary versus NCE/ordinary | -0.04382 | [-0.07190, -0.01574] |

## dtu / episode/cs_vs_nce_package/support_0.1 / unified / 3407

Paired n=36/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.01964 | [-0.05184, +0.01255] |
| CS/ordinary versus NCE/ordinary | -0.01862 | [-0.04790, +0.01066] |

## dtu / episode/cs_vs_nce_package/support_0.3 / unified / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.06266 | [-0.09520, -0.03013] |
| CS/ordinary versus NCE/ordinary | -0.06273 | [-0.09527, -0.03019] |

## dtu / episode/cs_vs_nce_package/support_0.3 / unified / 3407

Paired n=36/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.05651 | [-0.09387, -0.01914] |
| CS/ordinary versus NCE/ordinary | -0.05654 | [-0.09387, -0.01921] |

## dtu / episode/local/support_0.1 / native / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00008 | [-0.00015, +0.00000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00016 | [-0.00035, +0.00003] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00008 | [-0.00016, +0.00000] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00012, +0.00003] |
| episode_selected versus source_no_adaptation | -0.03963 | [-0.07925, -0.00002] |
| fixed_episode/0 versus source_no_adaptation | -0.05077 | [-0.11790, +0.01636] |
| fixed_episode/20 versus source_no_adaptation | -0.09359 | [-0.17871, -0.00846] |
| fixed_episode/5 versus source_no_adaptation | -0.05197 | [-0.11962, +0.01567] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05069 | [-0.11782, +0.01644] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09342 | [-0.17852, -0.00833] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05189 | [-0.11954, +0.01575] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.04546 | [-0.11533, +0.02441] |
| fixed_source/5 versus source_no_adaptation | +0.00068 | [-0.00245, +0.00382] |
| ordinary_selected versus source_no_adaptation | -0.03959 | [-0.07920, +0.00003] |

## dtu / episode/local/support_0.1 / native / 3407

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00021, +0.00000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00016 | [-0.00032, +0.00000] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00010 | [-0.00020, +0.00000] |
| episode_selected versus ordinary_selected | +0.00205 | [-0.00654, +0.01065] |
| episode_selected versus source_no_adaptation | -0.03662 | [-0.07776, +0.00452] |
| fixed_episode/0 versus source_no_adaptation | -0.05243 | [-0.11122, +0.00635] |
| fixed_episode/20 versus source_no_adaptation | -0.07798 | [-0.15692, +0.00095] |
| fixed_episode/5 versus source_no_adaptation | -0.05281 | [-0.11253, +0.00691] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05233 | [-0.11107, +0.00641] |
| fixed_ordinary/20 versus source_no_adaptation | -0.07782 | [-0.15671, +0.00107] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05271 | [-0.11239, +0.00696] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03810 | [-0.09845, +0.02226] |
| fixed_source/5 versus source_no_adaptation | +0.00103 | [-0.00180, +0.00386] |
| ordinary_selected versus source_no_adaptation | -0.03867 | [-0.07826, +0.00091] |

## dtu / episode/local/support_0.1 / native / 3413

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00024 | [-0.00036, -0.00011] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00032 | [-0.00047, -0.00017] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00024 | [-0.00037, -0.00011] |
| episode_selected versus ordinary_selected | -0.00018 | [-0.00030, -0.00006] |
| episode_selected versus source_no_adaptation | -0.05218 | [-0.11386, +0.00951] |
| fixed_episode/0 versus source_no_adaptation | -0.05203 | [-0.11443, +0.01037] |
| fixed_episode/20 versus source_no_adaptation | -0.07722 | [-0.15468, +0.00025] |
| fixed_episode/5 versus source_no_adaptation | -0.05268 | [-0.11575, +0.01039] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05179 | [-0.11416, +0.01057] |
| fixed_ordinary/20 versus source_no_adaptation | -0.07690 | [-0.15433, +0.00053] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05244 | [-0.11548, +0.01060] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.04254 | [-0.10988, +0.02479] |
| fixed_source/5 versus source_no_adaptation | +0.00059 | [-0.00320, +0.00439] |
| ordinary_selected versus source_no_adaptation | -0.05200 | [-0.11362, +0.00963] |

## dtu / episode/local/support_0.1 / native / complete_seed_mean

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00014 | [-0.00022, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00021 | [-0.00034, -0.00009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00014 | [-0.00023, -0.00005] |
| episode_selected versus ordinary_selected | +0.00061 | [-0.00224, +0.00346] |
| episode_selected versus source_no_adaptation | -0.04281 | [-0.08514, -0.00048] |
| fixed_episode/0 versus source_no_adaptation | -0.05174 | [-0.11005, +0.00656] |
| fixed_episode/20 versus source_no_adaptation | -0.08293 | [-0.15913, -0.00672] |
| fixed_episode/5 versus source_no_adaptation | -0.05249 | [-0.11160, +0.00662] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05161 | [-0.10989, +0.00667] |
| fixed_ordinary/20 versus source_no_adaptation | -0.08271 | [-0.15888, -0.00655] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05235 | [-0.11143, +0.00673] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.04203 | [-0.10606, +0.02199] |
| fixed_source/5 versus source_no_adaptation | +0.00077 | [-0.00234, +0.00387] |
| ordinary_selected versus source_no_adaptation | -0.04342 | [-0.08557, -0.00127] |

## dtu / episode/local/support_0.1 / unified / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00021, +0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00026 | [-0.00058, +0.00007] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00010 | [-0.00022, +0.00001] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00013, +0.00004] |
| episode_selected versus source_no_adaptation | -0.04548 | [-0.08578, -0.00519] |
| fixed_episode/0 versus source_no_adaptation | -0.07390 | [-0.15539, +0.00760] |
| fixed_episode/20 versus source_no_adaptation | -0.11951 | [-0.22747, -0.01155] |
| fixed_episode/5 versus source_no_adaptation | -0.07524 | [-0.15783, +0.00736] |
| fixed_ordinary/0 versus source_no_adaptation | -0.07380 | [-0.15531, +0.00771] |
| fixed_ordinary/20 versus source_no_adaptation | -0.11925 | [-0.22719, -0.01131] |
| fixed_ordinary/5 versus source_no_adaptation | -0.07513 | [-0.15774, +0.00747] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03005 | [-0.09976, +0.03965] |
| fixed_source/5 versus source_no_adaptation | +0.00111 | [-0.00236, +0.00457] |
| ordinary_selected versus source_no_adaptation | -0.04543 | [-0.08574, -0.00513] |

## dtu / episode/local/support_0.1 / unified / 3407

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00014 | [-0.00026, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00027 | [-0.00044, -0.00010] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00014 | [-0.00026, -0.00002] |
| episode_selected versus ordinary_selected | -0.00084 | [-0.01551, +0.01382] |
| episode_selected versus source_no_adaptation | -0.05138 | [-0.09937, -0.00339] |
| fixed_episode/0 versus source_no_adaptation | -0.08082 | [-0.15195, -0.00969] |
| fixed_episode/20 versus source_no_adaptation | -0.12639 | [-0.21904, -0.03374] |
| fixed_episode/5 versus source_no_adaptation | -0.08240 | [-0.15453, -0.01027] |
| fixed_ordinary/0 versus source_no_adaptation | -0.08068 | [-0.15180, -0.00956] |
| fixed_ordinary/20 versus source_no_adaptation | -0.12612 | [-0.21873, -0.03351] |
| fixed_ordinary/5 versus source_no_adaptation | -0.08226 | [-0.15438, -0.01014] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03553 | [-0.08933, +0.01828] |
| fixed_source/5 versus source_no_adaptation | +0.00129 | [-0.00163, +0.00421] |
| ordinary_selected versus source_no_adaptation | -0.05054 | [-0.09608, -0.00500] |

## dtu / episode/local/support_0.1 / unified / 3413

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00030 | [-0.00045, -0.00016] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00037 | [-0.00054, -0.00019] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00030 | [-0.00044, -0.00015] |
| episode_selected versus ordinary_selected | -0.00015 | [-0.00026, -0.00004] |
| episode_selected versus source_no_adaptation | -0.05530 | [-0.09955, -0.01106] |
| fixed_episode/0 versus source_no_adaptation | -0.06877 | [-0.13383, -0.00371] |
| fixed_episode/20 versus source_no_adaptation | -0.11312 | [-0.19852, -0.02771] |
| fixed_episode/5 versus source_no_adaptation | -0.07038 | [-0.13639, -0.00436] |
| fixed_ordinary/0 versus source_no_adaptation | -0.06847 | [-0.13351, -0.00343] |
| fixed_ordinary/20 versus source_no_adaptation | -0.11275 | [-0.19814, -0.02736] |
| fixed_ordinary/5 versus source_no_adaptation | -0.07008 | [-0.13608, -0.00408] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03202 | [-0.08246, +0.01842] |
| fixed_source/5 versus source_no_adaptation | +0.00104 | [-0.00203, +0.00410] |
| ordinary_selected versus source_no_adaptation | -0.05515 | [-0.09934, -0.01097] |

## dtu / episode/local/support_0.1 / unified / complete_seed_mean

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00018 | [-0.00028, -0.00008] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00030 | [-0.00046, -0.00014] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00018 | [-0.00028, -0.00008] |
| episode_selected versus ordinary_selected | -0.00035 | [-0.00530, +0.00460] |
| episode_selected versus source_no_adaptation | -0.05072 | [-0.08878, -0.01266] |
| fixed_episode/0 versus source_no_adaptation | -0.07449 | [-0.14152, -0.00747] |
| fixed_episode/20 versus source_no_adaptation | -0.11967 | [-0.20774, -0.03160] |
| fixed_episode/5 versus source_no_adaptation | -0.07601 | [-0.14406, -0.00795] |
| fixed_ordinary/0 versus source_no_adaptation | -0.07432 | [-0.14134, -0.00730] |
| fixed_ordinary/20 versus source_no_adaptation | -0.11937 | [-0.20742, -0.03133] |
| fixed_ordinary/5 versus source_no_adaptation | -0.07583 | [-0.14387, -0.00778] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03253 | [-0.08615, +0.02108] |
| fixed_source/5 versus source_no_adaptation | +0.00115 | [-0.00172, +0.00401] |
| ordinary_selected versus source_no_adaptation | -0.05038 | [-0.08828, -0.01247] |

## dtu / episode/local/support_0.3 / native / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00008 | [-0.00015, +0.00000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00019 | [-0.00030, -0.00008] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00008 | [-0.00016, -0.00000] |
| episode_selected versus ordinary_selected | -0.00004 | [-0.00010, +0.00002] |
| episode_selected versus source_no_adaptation | -0.03184 | [-0.07087, +0.00718] |
| fixed_episode/0 versus source_no_adaptation | -0.05077 | [-0.11621, +0.01467] |
| fixed_episode/20 versus source_no_adaptation | -0.07063 | [-0.15012, +0.00886] |
| fixed_episode/5 versus source_no_adaptation | -0.05094 | [-0.11689, +0.01500] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05069 | [-0.11614, +0.01475] |
| fixed_ordinary/20 versus source_no_adaptation | -0.07044 | [-0.14990, +0.00902] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05086 | [-0.11681, +0.01509] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.04385 | [-0.11457, +0.02686] |
| fixed_source/5 versus source_no_adaptation | +0.00133 | [-0.00228, +0.00494] |
| ordinary_selected versus source_no_adaptation | -0.03180 | [-0.07082, +0.00722] |

## dtu / episode/local/support_0.3 / native / 3407

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00021, +0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00013 | [-0.00028, +0.00002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00010 | [-0.00021, +0.00001] |
| episode_selected versus ordinary_selected | -0.00004 | [-0.00009, +0.00002] |
| episode_selected versus source_no_adaptation | -0.03255 | [-0.06885, +0.00374] |
| fixed_episode/0 versus source_no_adaptation | -0.05243 | [-0.11265, +0.00779] |
| fixed_episode/20 versus source_no_adaptation | -0.06261 | [-0.13891, +0.01368] |
| fixed_episode/5 versus source_no_adaptation | -0.05179 | [-0.11267, +0.00909] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05233 | [-0.11251, +0.00784] |
| fixed_ordinary/20 versus source_no_adaptation | -0.06248 | [-0.13877, +0.01380] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05170 | [-0.11253, +0.00914] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03916 | [-0.11493, +0.03661] |
| fixed_source/5 versus source_no_adaptation | +0.00129 | [-0.00233, +0.00491] |
| ordinary_selected versus source_no_adaptation | -0.03252 | [-0.06880, +0.00376] |

## dtu / episode/local/support_0.3 / native / 3413

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00024 | [-0.00037, -0.00011] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00038 | [-0.00056, -0.00020] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00025 | [-0.00038, -0.00011] |
| episode_selected versus ordinary_selected | -0.00016 | [-0.00029, -0.00002] |
| episode_selected versus source_no_adaptation | -0.04480 | [-0.10904, +0.01943] |
| fixed_episode/0 versus source_no_adaptation | -0.05203 | [-0.11655, +0.01249] |
| fixed_episode/20 versus source_no_adaptation | -0.05936 | [-0.13387, +0.01515] |
| fixed_episode/5 versus source_no_adaptation | -0.05142 | [-0.11649, +0.01365] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05179 | [-0.11628, +0.01269] |
| fixed_ordinary/20 versus source_no_adaptation | -0.05898 | [-0.13344, +0.01548] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05118 | [-0.11621, +0.01386] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03430 | [-0.10667, +0.03806] |
| fixed_source/5 versus source_no_adaptation | +0.00173 | [-0.00268, +0.00614] |
| ordinary_selected versus source_no_adaptation | -0.04465 | [-0.10881, +0.01951] |

## dtu / episode/local/support_0.3 / native / complete_seed_mean

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00014 | [-0.00022, -0.00005] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00023 | [-0.00034, -0.00013] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00014 | [-0.00023, -0.00006] |
| episode_selected versus ordinary_selected | -0.00008 | [-0.00013, -0.00003] |
| episode_selected versus source_no_adaptation | -0.03640 | [-0.07471, +0.00191] |
| fixed_episode/0 versus source_no_adaptation | -0.05174 | [-0.10774, +0.00425] |
| fixed_episode/20 versus source_no_adaptation | -0.06420 | [-0.13282, +0.00442] |
| fixed_episode/5 versus source_no_adaptation | -0.05139 | [-0.10797, +0.00520] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05161 | [-0.10758, +0.00436] |
| fixed_ordinary/20 versus source_no_adaptation | -0.06397 | [-0.13256, +0.00462] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05124 | [-0.10780, +0.00531] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.03910 | [-0.10682, +0.02861] |
| fixed_source/5 versus source_no_adaptation | +0.00145 | [-0.00210, +0.00500] |
| ordinary_selected versus source_no_adaptation | -0.03632 | [-0.07461, +0.00196] |

## dtu / episode/local/support_0.3 / unified / 3401

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00010 | [-0.00019, -0.00000] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00021 | [-0.00033, -0.00009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00010 | [-0.00020, -0.00001] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00011, +0.00001] |
| episode_selected versus source_no_adaptation | -0.03550 | [-0.06877, -0.00223] |
| fixed_episode/0 versus source_no_adaptation | -0.07390 | [-0.14139, -0.00640] |
| fixed_episode/20 versus source_no_adaptation | -0.09854 | [-0.18169, -0.01540] |
| fixed_episode/5 versus source_no_adaptation | -0.07436 | [-0.14268, -0.00605] |
| fixed_ordinary/0 versus source_no_adaptation | -0.07380 | [-0.14131, -0.00629] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09833 | [-0.18144, -0.01523] |
| fixed_ordinary/5 versus source_no_adaptation | -0.07426 | [-0.14258, -0.00594] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.02403 | [-0.08763, +0.03956] |
| fixed_source/5 versus source_no_adaptation | +0.00215 | [-0.00144, +0.00574] |
| ordinary_selected versus source_no_adaptation | -0.03545 | [-0.06872, -0.00217] |

## dtu / episode/local/support_0.3 / unified / 3407

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00014 | [-0.00026, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00019 | [-0.00031, -0.00006] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00014 | [-0.00026, -0.00001] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00012, +0.00003] |
| episode_selected versus source_no_adaptation | -0.04552 | [-0.08854, -0.00249] |
| fixed_episode/0 versus source_no_adaptation | -0.08082 | [-0.15342, -0.00822] |
| fixed_episode/20 versus source_no_adaptation | -0.10130 | [-0.19273, -0.00987] |
| fixed_episode/5 versus source_no_adaptation | -0.08060 | [-0.15423, -0.00697] |
| fixed_ordinary/0 versus source_no_adaptation | -0.08068 | [-0.15328, -0.00809] |
| fixed_ordinary/20 versus source_no_adaptation | -0.10112 | [-0.19255, -0.00968] |
| fixed_ordinary/5 versus source_no_adaptation | -0.08046 | [-0.15408, -0.00684] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.02962 | [-0.09524, +0.03600] |
| fixed_source/5 versus source_no_adaptation | +0.00185 | [-0.00158, +0.00528] |
| ordinary_selected versus source_no_adaptation | -0.04547 | [-0.08846, -0.00248] |

## dtu / episode/local/support_0.3 / unified / 3413

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00030 | [-0.00045, -0.00015] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00046 | [-0.00065, -0.00028] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00031 | [-0.00046, -0.00016] |
| episode_selected versus ordinary_selected | -0.00015 | [-0.00029, -0.00002] |
| episode_selected versus source_no_adaptation | -0.04147 | [-0.08705, +0.00411] |
| fixed_episode/0 versus source_no_adaptation | -0.06877 | [-0.13480, -0.00274] |
| fixed_episode/20 versus source_no_adaptation | -0.09097 | [-0.17325, -0.00870] |
| fixed_episode/5 versus source_no_adaptation | -0.06906 | [-0.13610, -0.00203] |
| fixed_ordinary/0 versus source_no_adaptation | -0.06847 | [-0.13448, -0.00245] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09051 | [-0.17274, -0.00828] |
| fixed_ordinary/5 versus source_no_adaptation | -0.06875 | [-0.13577, -0.00173] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.01818 | [-0.07634, +0.03997] |
| fixed_source/5 versus source_no_adaptation | +0.00251 | [-0.00124, +0.00626] |
| ordinary_selected versus source_no_adaptation | -0.04132 | [-0.08683, +0.00420] |

## dtu / episode/local/support_0.3 / unified / complete_seed_mean

Paired n=44/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00018 | [-0.00027, -0.00008] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00029 | [-0.00040, -0.00017] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00018 | [-0.00028, -0.00009] |
| episode_selected versus ordinary_selected | -0.00008 | [-0.00015, -0.00002] |
| episode_selected versus source_no_adaptation | -0.04083 | [-0.07569, -0.00597] |
| fixed_episode/0 versus source_no_adaptation | -0.07449 | [-0.13880, -0.01019] |
| fixed_episode/20 versus source_no_adaptation | -0.09694 | [-0.17727, -0.01661] |
| fixed_episode/5 versus source_no_adaptation | -0.07468 | [-0.13990, -0.00945] |
| fixed_ordinary/0 versus source_no_adaptation | -0.07432 | [-0.13861, -0.01002] |
| fixed_ordinary/20 versus source_no_adaptation | -0.09665 | [-0.17695, -0.01635] |
| fixed_ordinary/5 versus source_no_adaptation | -0.07449 | [-0.13971, -0.00927] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.02395 | [-0.08331, +0.03542] |
| fixed_source/5 versus source_no_adaptation | +0.00217 | [-0.00113, +0.00548] |
| ordinary_selected versus source_no_adaptation | -0.04074 | [-0.07557, -0.00592] |

## fau / episode/cs/mismatch_gain/support_0.1 / native / 3401

Paired n=67/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00003 | [-0.00005, -0.00000] |
| episode_selected versus source_no_adaptation | +0.00163 | [-0.04373, +0.04698] |
| fixed_episode/0 versus source_no_adaptation | -0.00141 | [-0.04817, +0.04536] |
| fixed_episode/20 versus source_no_adaptation | +0.00845 | [-0.03830, +0.05521] |
| fixed_episode/5 versus source_no_adaptation | -0.00061 | [-0.04736, +0.04614] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00137 | [-0.04813, +0.04538] |
| fixed_ordinary/20 versus source_no_adaptation | +0.00849 | [-0.03825, +0.05523] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00058 | [-0.04732, +0.04616] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.03212 | [+0.02301, +0.04124] |
| fixed_source/5 versus source_no_adaptation | +0.00197 | [+0.00147, +0.00248] |
| ordinary_selected versus source_no_adaptation | +0.00166 | [-0.04369, +0.04700] |

## fau / episode/cs/mismatch_gain/support_0.1 / unified / 3401

Paired n=67/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00006, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00000] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00005, +0.00000] |
| episode_selected versus source_no_adaptation | -0.00181 | [-0.01775, +0.01413] |
| fixed_episode/0 versus source_no_adaptation | +0.00227 | [-0.01579, +0.02034] |
| fixed_episode/20 versus source_no_adaptation | -0.01130 | [-0.03371, +0.01110] |
| fixed_episode/5 versus source_no_adaptation | +0.00170 | [-0.01653, +0.01992] |
| fixed_ordinary/0 versus source_no_adaptation | +0.00231 | [-0.01576, +0.02037] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01126 | [-0.03365, +0.01113] |
| fixed_ordinary/5 versus source_no_adaptation | +0.00172 | [-0.01649, +0.01994] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00157 | [-0.00859, +0.00546] |
| fixed_source/5 versus source_no_adaptation | +0.00010 | [-0.00025, +0.00045] |
| ordinary_selected versus source_no_adaptation | -0.00179 | [-0.01772, +0.01414] |

## fau / episode/cs/mismatch_gain/support_0.3 / native / 3401

Paired n=67/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00003 | [-0.00006, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus source_no_adaptation | +0.00055 | [-0.04463, +0.04574] |
| fixed_episode/0 versus source_no_adaptation | -0.00141 | [-0.04739, +0.04458] |
| fixed_episode/20 versus source_no_adaptation | +0.00977 | [-0.03607, +0.05560] |
| fixed_episode/5 versus source_no_adaptation | -0.00052 | [-0.04648, +0.04544] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00137 | [-0.04736, +0.04461] |
| fixed_ordinary/20 versus source_no_adaptation | +0.00980 | [-0.03602, +0.05563] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00049 | [-0.04644, +0.04547] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.03156 | [+0.02229, +0.04082] |
| fixed_source/5 versus source_no_adaptation | +0.00200 | [+0.00149, +0.00251] |
| ordinary_selected versus source_no_adaptation | +0.00058 | [-0.04459, +0.04576] |

## fau / episode/cs/mismatch_gain/support_0.3 / unified / 3401

Paired n=67/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00006, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00006, -0.00001] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00005, -0.00000] |
| episode_selected versus source_no_adaptation | -0.00128 | [-0.01702, +0.01445] |
| fixed_episode/0 versus source_no_adaptation | +0.00227 | [-0.01579, +0.02034] |
| fixed_episode/20 versus source_no_adaptation | -0.00932 | [-0.03116, +0.01251] |
| fixed_episode/5 versus source_no_adaptation | +0.00183 | [-0.01637, +0.02004] |
| fixed_ordinary/0 versus source_no_adaptation | +0.00231 | [-0.01575, +0.02036] |
| fixed_ordinary/20 versus source_no_adaptation | -0.00929 | [-0.03111, +0.01254] |
| fixed_ordinary/5 versus source_no_adaptation | +0.00186 | [-0.01633, +0.02006] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00185 | [-0.00849, +0.00478] |
| fixed_source/5 versus source_no_adaptation | +0.00018 | [-0.00017, +0.00052] |
| ordinary_selected versus source_no_adaptation | -0.00126 | [-0.01699, +0.01447] |

## fau / episode/cs_vs_nce_package/support_0.1 / unified / 3401

Paired n=56/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.00917 | [-0.02282, +0.00448] |
| CS/ordinary versus NCE/ordinary | -0.00914 | [-0.02278, +0.00450] |

## fau / episode/cs_vs_nce_package/support_0.3 / unified / 3401

Paired n=56/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.01249 | [-0.02554, +0.00057] |
| CS/ordinary versus NCE/ordinary | -0.01246 | [-0.02550, +0.00059] |

## fau / episode/local/support_0.1 / native / 3401

Paired n=67/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00005 | [-0.00007, -0.00002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00005, +0.00000] |
| episode_selected versus source_no_adaptation | +0.00071 | [-0.02297, +0.02439] |
| fixed_episode/0 versus source_no_adaptation | -0.00245 | [-0.02695, +0.02206] |
| fixed_episode/20 versus source_no_adaptation | -0.01867 | [-0.04886, +0.01152] |
| fixed_episode/5 versus source_no_adaptation | -0.00312 | [-0.02786, +0.02161] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00242 | [-0.02692, +0.02208] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01862 | [-0.04880, +0.01155] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00309 | [-0.02782, +0.02163] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00590 | [-0.01576, +0.00396] |
| fixed_source/5 versus source_no_adaptation | -0.00008 | [-0.00057, +0.00042] |
| ordinary_selected versus source_no_adaptation | +0.00073 | [-0.02294, +0.02440] |

## fau / episode/local/support_0.1 / unified / 3401

Paired n=67/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00003 | [-0.00005, +0.00000] |
| episode_selected versus source_no_adaptation | -0.00345 | [-0.01859, +0.01169] |
| fixed_episode/0 versus source_no_adaptation | -0.00034 | [-0.01678, +0.01610] |
| fixed_episode/20 versus source_no_adaptation | -0.01408 | [-0.03587, +0.00770] |
| fixed_episode/5 versus source_no_adaptation | -0.00091 | [-0.01758, +0.01576] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00031 | [-0.01674, +0.01612] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01404 | [-0.03581, +0.00772] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00088 | [-0.01753, +0.01578] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00256 | [-0.00971, +0.00459] |
| fixed_source/5 versus source_no_adaptation | +0.00008 | [-0.00026, +0.00042] |
| ordinary_selected versus source_no_adaptation | -0.00343 | [-0.01855, +0.01170] |

## fau / episode/local/support_0.3 / native / 3401

Paired n=67/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00002] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00004, -0.00000] |
| episode_selected versus source_no_adaptation | +0.00059 | [-0.02359, +0.02477] |
| fixed_episode/0 versus source_no_adaptation | -0.00245 | [-0.02726, +0.02236] |
| fixed_episode/20 versus source_no_adaptation | -0.01585 | [-0.04515, +0.01346] |
| fixed_episode/5 versus source_no_adaptation | -0.00296 | [-0.02796, +0.02204] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00242 | [-0.02722, +0.02238] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01580 | [-0.04509, +0.01349] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00293 | [-0.02792, +0.02206] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00595 | [-0.01665, +0.00475] |
| fixed_source/5 versus source_no_adaptation | -0.00005 | [-0.00060, +0.00051] |
| ordinary_selected versus source_no_adaptation | +0.00061 | [-0.02355, +0.02478] |

## fau / episode/local/support_0.3 / unified / 3401

Paired n=67/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00005, -0.00001] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00007, -0.00001] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00005, -0.00001] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00005, -0.00000] |
| episode_selected versus source_no_adaptation | -0.00290 | [-0.01759, +0.01179] |
| fixed_episode/0 versus source_no_adaptation | -0.00034 | [-0.01664, +0.01596] |
| fixed_episode/20 versus source_no_adaptation | -0.01088 | [-0.03128, +0.00952] |
| fixed_episode/5 versus source_no_adaptation | -0.00072 | [-0.01718, +0.01574] |
| fixed_ordinary/0 versus source_no_adaptation | -0.00031 | [-0.01660, +0.01598] |
| fixed_ordinary/20 versus source_no_adaptation | -0.01084 | [-0.03122, +0.00954] |
| fixed_ordinary/5 versus source_no_adaptation | -0.00069 | [-0.01714, +0.01576] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00190 | [-0.00847, +0.00468] |
| fixed_source/5 versus source_no_adaptation | +0.00015 | [-0.00019, +0.00050] |
| ordinary_selected versus source_no_adaptation | -0.00287 | [-0.01755, +0.01180] |

