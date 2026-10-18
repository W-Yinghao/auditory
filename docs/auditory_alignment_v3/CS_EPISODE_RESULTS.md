# Public local CS episode continuation

2026-10-18T19:49:00.778100+02:00; CPU job 1045980; **22/40 complete**.

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

## dtu / episode/cs_vs_nce_package/support_0.1 / unified / 3401

Paired n=20/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.02825 | [-0.06515, +0.00865] |
| CS/ordinary versus NCE/ordinary | -0.02818 | [-0.06506, +0.00871] |

## dtu / episode/cs_vs_nce_package/support_0.3 / unified / 3401

Paired n=20/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.06123 | [-0.11177, -0.01069] |
| CS/ordinary versus NCE/ordinary | -0.06114 | [-0.11167, -0.01061] |

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

## fau / episode/cs/mismatch_gain/support_0.1 / native / 3401

Paired n=14/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00005 | [-0.00012, +0.00003] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00007 | [-0.00017, +0.00004] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00005 | [-0.00013, +0.00003] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00012, +0.00003] |
| episode_selected versus source_no_adaptation | +0.11663 | [+0.02011, +0.21315] |
| fixed_episode/0 versus source_no_adaptation | +0.11663 | [+0.02011, +0.21315] |
| fixed_episode/20 versus source_no_adaptation | +0.11783 | [+0.00692, +0.22875] |
| fixed_episode/5 versus source_no_adaptation | +0.11696 | [+0.01974, +0.21417] |
| fixed_ordinary/0 versus source_no_adaptation | +0.11668 | [+0.02019, +0.21317] |
| fixed_ordinary/20 versus source_no_adaptation | +0.11790 | [+0.00703, +0.22876] |
| fixed_ordinary/5 versus source_no_adaptation | +0.11701 | [+0.01983, +0.21419] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.02364 | [+0.00152, +0.04576] |
| fixed_source/5 versus source_no_adaptation | +0.00147 | [+0.00042, +0.00252] |
| ordinary_selected versus source_no_adaptation | +0.11668 | [+0.02019, +0.21317] |

## fau / episode/cs/mismatch_gain/support_0.1 / unified / 3401

Paired n=14/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00011, +0.00006] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00005 | [-0.00015, +0.00006] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00011, +0.00007] |
| episode_selected versus ordinary_selected | -0.00003 | [-0.00011, +0.00006] |
| episode_selected versus source_no_adaptation | -0.02926 | [-0.08433, +0.02581] |
| fixed_episode/0 versus source_no_adaptation | -0.02926 | [-0.08433, +0.02581] |
| fixed_episode/20 versus source_no_adaptation | -0.04977 | [-0.12541, +0.02587] |
| fixed_episode/5 versus source_no_adaptation | -0.03032 | [-0.08642, +0.02577] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02924 | [-0.08426, +0.02579] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04972 | [-0.12529, +0.02584] |
| fixed_ordinary/5 versus source_no_adaptation | -0.03030 | [-0.08634, +0.02574] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00134 | [-0.02860, +0.02593] |
| fixed_source/5 versus source_no_adaptation | +0.00001 | [-0.00136, +0.00138] |
| ordinary_selected versus source_no_adaptation | -0.02924 | [-0.08426, +0.02579] |

## fau / episode/cs/mismatch_gain/support_0.3 / native / 3401

Paired n=14/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00005 | [-0.00012, +0.00003] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00005 | [-0.00014, +0.00005] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00005 | [-0.00013, +0.00003] |
| episode_selected versus ordinary_selected | -0.00005 | [-0.00012, +0.00003] |
| episode_selected versus source_no_adaptation | +0.11663 | [+0.02495, +0.20831] |
| fixed_episode/0 versus source_no_adaptation | +0.11663 | [+0.02495, +0.20831] |
| fixed_episode/20 versus source_no_adaptation | +0.11835 | [+0.01200, +0.22470] |
| fixed_episode/5 versus source_no_adaptation | +0.11698 | [+0.02449, +0.20948] |
| fixed_ordinary/0 versus source_no_adaptation | +0.11668 | [+0.02503, +0.20833] |
| fixed_ordinary/20 versus source_no_adaptation | +0.11840 | [+0.01209, +0.22471] |
| fixed_ordinary/5 versus source_no_adaptation | +0.11703 | [+0.02457, +0.20949] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.01750 | [-0.00577, +0.04077] |
| fixed_source/5 versus source_no_adaptation | +0.00120 | [-0.00001, +0.00241] |
| ordinary_selected versus source_no_adaptation | +0.11668 | [+0.02503, +0.20833] |

## fau / episode/cs/mismatch_gain/support_0.3 / unified / 3401

Paired n=14/67. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00003 | [-0.00011, +0.00006] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00003 | [-0.00014, +0.00009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00011, +0.00007] |
| episode_selected versus ordinary_selected | -0.00003 | [-0.00011, +0.00006] |
| episode_selected versus source_no_adaptation | -0.02926 | [-0.08399, +0.02546] |
| fixed_episode/0 versus source_no_adaptation | -0.02926 | [-0.08399, +0.02546] |
| fixed_episode/20 versus source_no_adaptation | -0.04572 | [-0.12237, +0.03093] |
| fixed_episode/5 versus source_no_adaptation | -0.03004 | [-0.08587, +0.02578] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02924 | [-0.08392, +0.02544] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04570 | [-0.12227, +0.03088] |
| fixed_ordinary/5 versus source_no_adaptation | -0.03002 | [-0.08580, +0.02575] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00811 | [-0.03559, +0.01938] |
| fixed_source/5 versus source_no_adaptation | -0.00021 | [-0.00171, +0.00130] |
| ordinary_selected versus source_no_adaptation | -0.02924 | [-0.08392, +0.02544] |

## fau / episode/cs_vs_nce_package/support_0.1 / unified / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.03441 | [-0.07072, +0.00191] |
| CS/ordinary versus NCE/ordinary | -0.03439 | [-0.07067, +0.00188] |

## fau / episode/cs_vs_nce_package/support_0.3 / unified / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.04101 | [-0.07696, -0.00507] |
| CS/ordinary versus NCE/ordinary | -0.04099 | [-0.07689, -0.00508] |

## fau / episode/local/support_0.1 / native / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00001 | [-0.00009, +0.00006] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00014, +0.00006] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00009, +0.00006] |
| episode_selected versus ordinary_selected | -0.00001 | [-0.00009, +0.00006] |
| episode_selected versus source_no_adaptation | -0.02356 | [-0.13676, +0.08965] |
| fixed_episode/0 versus source_no_adaptation | -0.02356 | [-0.13676, +0.08965] |
| fixed_episode/20 versus source_no_adaptation | -0.04968 | [-0.19896, +0.09961] |
| fixed_episode/5 versus source_no_adaptation | -0.02481 | [-0.13991, +0.09030] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02354 | [-0.13669, +0.08961] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04963 | [-0.19885, +0.09958] |
| fixed_ordinary/5 versus source_no_adaptation | -0.02479 | [-0.13985, +0.09027] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00281 | [-0.02918, +0.02357] |
| fixed_source/5 versus source_no_adaptation | -0.00000 | [-0.00127, +0.00127] |
| ordinary_selected versus source_no_adaptation | -0.02354 | [-0.13669, +0.08961] |

## fau / episode/local/support_0.1 / unified / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00002 | [-0.00012, +0.00008] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00016, +0.00009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00012, +0.00008] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00012, +0.00008] |
| episode_selected versus source_no_adaptation | -0.03447 | [-0.10065, +0.03171] |
| fixed_episode/0 versus source_no_adaptation | -0.03447 | [-0.10065, +0.03171] |
| fixed_episode/20 versus source_no_adaptation | -0.05167 | [-0.14830, +0.04497] |
| fixed_episode/5 versus source_no_adaptation | -0.03526 | [-0.10296, +0.03243] |
| fixed_ordinary/0 versus source_no_adaptation | -0.03445 | [-0.10058, +0.03168] |
| fixed_ordinary/20 versus source_no_adaptation | -0.05163 | [-0.14818, +0.04492] |
| fixed_ordinary/5 versus source_no_adaptation | -0.03525 | [-0.10288, +0.03239] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.00022 | [-0.03491, +0.03535] |
| fixed_source/5 versus source_no_adaptation | +0.00016 | [-0.00155, +0.00186] |
| ordinary_selected versus source_no_adaptation | -0.03445 | [-0.10058, +0.03168] |

## fau / episode/local/support_0.3 / native / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00001 | [-0.00009, +0.00006] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00014, +0.00006] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00001 | [-0.00009, +0.00006] |
| episode_selected versus ordinary_selected | -0.00001 | [-0.00009, +0.00006] |
| episode_selected versus source_no_adaptation | -0.02356 | [-0.12928, +0.08217] |
| fixed_episode/0 versus source_no_adaptation | -0.02356 | [-0.12928, +0.08217] |
| fixed_episode/20 versus source_no_adaptation | -0.04559 | [-0.17819, +0.08702] |
| fixed_episode/5 versus source_no_adaptation | -0.02460 | [-0.13187, +0.08266] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02354 | [-0.12922, +0.08213] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04555 | [-0.17809, +0.08700] |
| fixed_ordinary/5 versus source_no_adaptation | -0.02459 | [-0.13181, +0.08263] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00814 | [-0.03716, +0.02087] |
| fixed_source/5 versus source_no_adaptation | -0.00025 | [-0.00184, +0.00135] |
| ordinary_selected versus source_no_adaptation | -0.02354 | [-0.12922, +0.08213] |

## fau / episode/local/support_0.3 / unified / 3401

Paired n=14/67. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00002 | [-0.00012, +0.00008] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00003 | [-0.00015, +0.00009] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00012, +0.00008] |
| episode_selected versus ordinary_selected | -0.00002 | [-0.00012, +0.00008] |
| episode_selected versus source_no_adaptation | -0.03447 | [-0.09615, +0.02721] |
| fixed_episode/0 versus source_no_adaptation | -0.03447 | [-0.09615, +0.02721] |
| fixed_episode/20 versus source_no_adaptation | -0.04625 | [-0.13320, +0.04070] |
| fixed_episode/5 versus source_no_adaptation | -0.03494 | [-0.09789, +0.02800] |
| fixed_ordinary/0 versus source_no_adaptation | -0.03445 | [-0.09608, +0.02718] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04621 | [-0.13308, +0.04065] |
| fixed_ordinary/5 versus source_no_adaptation | -0.03492 | [-0.09782, +0.02797] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.00505 | [-0.03583, +0.02572] |
| fixed_source/5 versus source_no_adaptation | -0.00006 | [-0.00171, +0.00160] |
| ordinary_selected versus source_no_adaptation | -0.03445 | [-0.09608, +0.02718] |

