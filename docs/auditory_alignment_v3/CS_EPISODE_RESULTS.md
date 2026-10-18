# Public local CS episode continuation

2026-10-18T16:04:50.099707+02:00; CPU job 1045980; **12/40 complete**.

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

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00004 | [-0.00040, +0.00033] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.00005 | [-0.00034, +0.00044] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00003 | [-0.00040, +0.00034] |
| episode_selected versus ordinary_selected | +0.03714 | [-0.07814, +0.15242] |
| episode_selected versus source_no_adaptation | +0.08010 | [-0.09599, +0.25619] |
| fixed_episode/0 versus source_no_adaptation | +0.04134 | [-0.15637, +0.23904] |
| fixed_episode/20 versus source_no_adaptation | +0.04337 | [-0.18940, +0.27615] |
| fixed_episode/5 versus source_no_adaptation | +0.04267 | [-0.15553, +0.24086] |
| fixed_ordinary/0 versus source_no_adaptation | +0.04137 | [-0.15634, +0.23908] |
| fixed_ordinary/20 versus source_no_adaptation | +0.04332 | [-0.18935, +0.27600] |
| fixed_ordinary/5 versus source_no_adaptation | +0.04270 | [-0.15547, +0.24087] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.08958 | [-0.03984, +0.21901] |
| fixed_source/5 versus source_no_adaptation | +0.00793 | [-0.00225, +0.01810] |
| ordinary_selected versus source_no_adaptation | +0.04296 | [-0.07487, +0.16079] |

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

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00017 | [-0.00056, +0.00021] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00011 | [-0.00046, +0.00024] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00016 | [-0.00055, +0.00023] |
| episode_selected versus ordinary_selected | +0.01219 | [-0.09569, +0.12008] |
| episode_selected versus source_no_adaptation | +0.00105 | [-0.14922, +0.15131] |
| fixed_episode/0 versus source_no_adaptation | -0.05540 | [-0.22418, +0.11339] |
| fixed_episode/20 versus source_no_adaptation | -0.05526 | [-0.23712, +0.12660] |
| fixed_episode/5 versus source_no_adaptation | -0.05438 | [-0.22398, +0.11523] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05522 | [-0.22418, +0.11374] |
| fixed_ordinary/20 versus source_no_adaptation | -0.05515 | [-0.23710, +0.12679] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05422 | [-0.22400, +0.11557] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.01520 | [-0.12683, +0.15723] |
| fixed_source/5 versus source_no_adaptation | +0.00500 | [-0.00452, +0.01452] |
| ordinary_selected versus source_no_adaptation | -0.01114 | [-0.10331, +0.08102] |

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

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00004 | [-0.00039, +0.00032] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.00011 | [-0.00052, +0.00075] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00002 | [-0.00039, +0.00034] |
| episode_selected versus ordinary_selected | +0.00000 | [+0.00000, +0.00000] |
| episode_selected versus source_no_adaptation | +0.00797 | [-0.00179, +0.01773] |
| fixed_episode/0 versus source_no_adaptation | +0.04134 | [-0.14822, +0.23089] |
| fixed_episode/20 versus source_no_adaptation | +0.07534 | [-0.14391, +0.29458] |
| fixed_episode/5 versus source_no_adaptation | +0.04392 | [-0.14640, +0.23424] |
| fixed_ordinary/0 versus source_no_adaptation | +0.04137 | [-0.14819, +0.23093] |
| fixed_ordinary/20 versus source_no_adaptation | +0.07523 | [-0.14392, +0.29437] |
| fixed_ordinary/5 versus source_no_adaptation | +0.04394 | [-0.14639, +0.23428] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.10357 | [-0.03153, +0.23867] |
| fixed_source/5 versus source_no_adaptation | +0.00797 | [-0.00179, +0.01773] |
| ordinary_selected versus source_no_adaptation | +0.00797 | [-0.00179, +0.01773] |

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

Paired n=10/44. positive = candidate minus reference mismatch gain, bits/query; not true-risk benefit.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00017 | [-0.00066, +0.00031] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00002 | [-0.00073, +0.00070] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00016 | [-0.00067, +0.00035] |
| episode_selected versus ordinary_selected | +0.00000 | [+0.00000, +0.00000] |
| episode_selected versus source_no_adaptation | +0.00466 | [-0.00654, +0.01586] |
| fixed_episode/0 versus source_no_adaptation | -0.05540 | [-0.27137, +0.16058] |
| fixed_episode/20 versus source_no_adaptation | -0.02537 | [-0.24251, +0.19177] |
| fixed_episode/5 versus source_no_adaptation | -0.05313 | [-0.26932, +0.16306] |
| fixed_ordinary/0 versus source_no_adaptation | -0.05522 | [-0.27142, +0.16097] |
| fixed_ordinary/20 versus source_no_adaptation | -0.02535 | [-0.24271, +0.19200] |
| fixed_ordinary/5 versus source_no_adaptation | -0.05297 | [-0.26941, +0.16346] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.02307 | [-0.14919, +0.19534] |
| fixed_source/5 versus source_no_adaptation | +0.00466 | [-0.00654, +0.01586] |
| ordinary_selected versus source_no_adaptation | +0.00466 | [-0.00654, +0.01586] |

## dtu / episode/cs_vs_nce_package/support_0.1 / unified / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.04013 | [-0.10916, +0.02890] |
| CS/ordinary versus NCE/ordinary | -0.03995 | [-0.10891, +0.02901] |

## dtu / episode/cs_vs_nce_package/support_0.3 / unified / 3401

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| CS/episode versus NCE/episode | -0.09827 | [-0.18410, -0.01243] |
| CS/ordinary versus NCE/ordinary | -0.09816 | [-0.18395, -0.01237] |

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

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00008 | [-0.00036, +0.00019] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00005 | [-0.00027, +0.00016] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00008 | [-0.00036, +0.00019] |
| episode_selected versus ordinary_selected | +0.00912 | [-0.04946, +0.06771] |
| episode_selected versus source_no_adaptation | -0.00829 | [-0.12251, +0.10594] |
| fixed_episode/0 versus source_no_adaptation | -0.02084 | [-0.12669, +0.08501] |
| fixed_episode/20 versus source_no_adaptation | -0.04006 | [-0.18704, +0.10692] |
| fixed_episode/5 versus source_no_adaptation | -0.02126 | [-0.12925, +0.08672] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02075 | [-0.12655, +0.08504] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04001 | [-0.18691, +0.10688] |
| fixed_ordinary/5 versus source_no_adaptation | -0.02118 | [-0.12911, +0.08675] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.01662 | [-0.12006, +0.08681] |
| fixed_source/5 versus source_no_adaptation | +0.00221 | [-0.00455, +0.00897] |
| ordinary_selected versus source_no_adaptation | -0.01741 | [-0.10630, +0.07149] |

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

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00012 | [-0.00036, +0.00012] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00010 | [-0.00032, +0.00013] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00011 | [-0.00035, +0.00012] |
| episode_selected versus ordinary_selected | -0.00357 | [-0.08898, +0.08185] |
| episode_selected versus source_no_adaptation | -0.00228 | [-0.11306, +0.10849] |
| fixed_episode/0 versus source_no_adaptation | -0.06204 | [-0.18359, +0.05951] |
| fixed_episode/20 versus source_no_adaptation | -0.07637 | [-0.19535, +0.04261] |
| fixed_episode/5 versus source_no_adaptation | -0.06234 | [-0.18328, +0.05860] |
| fixed_ordinary/0 versus source_no_adaptation | -0.06192 | [-0.18358, +0.05974] |
| fixed_ordinary/20 versus source_no_adaptation | -0.07627 | [-0.19525, +0.04271] |
| fixed_ordinary/5 versus source_no_adaptation | -0.06223 | [-0.18327, +0.05882] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.01852 | [-0.08674, +0.12378] |
| fixed_source/5 versus source_no_adaptation | +0.00486 | [-0.00214, +0.01186] |
| ordinary_selected versus source_no_adaptation | +0.00128 | [-0.06164, +0.06421] |

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

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00008 | [-0.00033, +0.00016] |
| fixed_episode/20 versus fixed_ordinary/20 | +0.00000 | [-0.00027, +0.00028] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00008 | [-0.00032, +0.00017] |
| episode_selected versus ordinary_selected | +0.00000 | [+0.00000, +0.00000] |
| episode_selected versus source_no_adaptation | +0.00181 | [-0.00360, +0.00722] |
| fixed_episode/0 versus source_no_adaptation | -0.02084 | [-0.11242, +0.07075] |
| fixed_episode/20 versus source_no_adaptation | -0.00950 | [-0.12059, +0.10159] |
| fixed_episode/5 versus source_no_adaptation | -0.02013 | [-0.11261, +0.07236] |
| fixed_ordinary/0 versus source_no_adaptation | -0.02075 | [-0.11229, +0.07079] |
| fixed_ordinary/20 versus source_no_adaptation | -0.00950 | [-0.12055, +0.10154] |
| fixed_ordinary/5 versus source_no_adaptation | -0.02005 | [-0.11249, +0.07240] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | -0.01261 | [-0.10778, +0.08256] |
| fixed_source/5 versus source_no_adaptation | +0.00181 | [-0.00360, +0.00722] |
| ordinary_selected versus source_no_adaptation | +0.00181 | [-0.00360, +0.00722] |

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

Paired n=10/44. positive = reference minus candidate true NLL, bits/query.

| Contrast | Difference | Simultaneous95% interval |
|---|---:|---:|
| fixed_episode/0 versus fixed_ordinary/0 | -0.00012 | [-0.00040, +0.00016] |
| fixed_episode/20 versus fixed_ordinary/20 | -0.00004 | [-0.00039, +0.00032] |
| fixed_episode/5 versus fixed_ordinary/5 | -0.00011 | [-0.00040, +0.00018] |
| episode_selected versus ordinary_selected | +0.00000 | [+0.00000, +0.00000] |
| episode_selected versus source_no_adaptation | +0.00434 | [-0.00378, +0.01246] |
| fixed_episode/0 versus source_no_adaptation | -0.06204 | [-0.20268, +0.07860] |
| fixed_episode/20 versus source_no_adaptation | -0.04761 | [-0.17953, +0.08431] |
| fixed_episode/5 versus source_no_adaptation | -0.06105 | [-0.20092, +0.07882] |
| fixed_ordinary/0 versus source_no_adaptation | -0.06192 | [-0.20269, +0.07884] |
| fixed_ordinary/20 versus source_no_adaptation | -0.04758 | [-0.17962, +0.08447] |
| fixed_ordinary/5 versus source_no_adaptation | -0.06093 | [-0.20094, +0.07907] |
| fixed_source/0 versus source_no_adaptation | +0.00000 | [+0.00000, +0.00000] |
| fixed_source/20 versus source_no_adaptation | +0.02252 | [-0.10083, +0.14587] |
| fixed_source/5 versus source_no_adaptation | +0.00434 | [-0.00378, +0.01246] |
| ordinary_selected versus source_no_adaptation | +0.00434 | [-0.00378, +0.01246] |

