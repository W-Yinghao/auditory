# DEP12 private children: results (Agent P)

Generated 2026-10-23T11:44:50.633845+02:00 (job 1059697); binding d1eab492546d; encoders with results: 32.

G = mean log2 p_E(y) − log2 p_B1(y) on the outer-test children (bits/trial); B1 = history-only single intercept on the same source-ES rows. Intervals: person bootstrap-t, B = 10,000, simultaneous = family max-|T*|.

## F_PRIVATE[3401] — U0 all-trials G, bits/trial

status complete, n = 64/64, critical +2.448

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00368 | [+0.00165, +0.00571] | [+0.00119, +0.00617] |
| cs_pair-info_nce | 64 | +0.00048 | [-0.00038, +0.00135] | [-0.00057, +0.00154] |
| cs_pair-sigmoid | 64 | -0.00012 | [-0.00099, +0.00075] | [-0.00119, +0.00095] |

## F_PRIVATE[3407] — U0 all-trials G, bits/trial

status complete, n = 64/64, critical +2.331

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00332 | [+0.00141, +0.00524] | [+0.00114, +0.00550] |
| cs_pair-info_nce | 64 | -0.00001 | [-0.00122, +0.00119] | [-0.00142, +0.00139] |
| cs_pair-sigmoid | 64 | -0.00004 | [-0.00125, +0.00117] | [-0.00145, +0.00137] |

## F_PRIVATE[3413] — U0 all-trials G, bits/trial

status complete, n = 64/64, critical +2.395

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00303 | [+0.00089, +0.00517] | [+0.00044, +0.00562] |
| cs_pair-info_nce | 64 | +0.00020 | [-0.00074, +0.00113] | [-0.00093, +0.00132] |
| cs_pair-sigmoid | 64 | -0.00059 | [-0.00161, +0.00044] | [-0.00181, +0.00064] |

## F_PRIVATE[merged] — U0 all-trials G, bits/trial, child mean over seeds

status complete, n = 64/64, critical +2.369

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00335 | [+0.00142, +0.00527] | [+0.00105, +0.00564] |
| cs_pair-info_nce | 64 | +0.00022 | [-0.00058, +0.00102] | [-0.00072, +0.00117] |
| cs_pair-sigmoid | 64 | -0.00025 | [-0.00103, +0.00054] | [-0.00117, +0.00067] |

## F_SELECTION[3401] — U10 query log2-score, bits/trial

status complete, n = 64/64, critical +2.475

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | +0.00038 | [-0.00072, +0.00149] | [-0.00094, +0.00170] |
| delta_cs-support_cv | 64 | -0.00043 | [-0.00128, +0.00042] | [-0.00146, +0.00060] |
| delta_cs-uniform | 64 | -0.00243 | [-0.00301, -0.00184] | [-0.00314, -0.00171] |

## F_SELECTION[3407] — U10 query log2-score, bits/trial

status complete, n = 64/64, critical +2.452

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | -0.00018 | [-0.00119, +0.00083] | [-0.00143, +0.00106] |
| delta_cs-support_cv | 64 | -0.00034 | [-0.00109, +0.00041] | [-0.00124, +0.00056] |
| delta_cs-uniform | 64 | -0.00242 | [-0.00294, -0.00191] | [-0.00306, -0.00178] |

## F_SELECTION[3413] — U10 query log2-score, bits/trial

status complete, n = 64/64, critical +2.439

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | +0.00038 | [-0.00096, +0.00172] | [-0.00124, +0.00200] |
| delta_cs-support_cv | 64 | -0.00055 | [-0.00127, +0.00018] | [-0.00142, +0.00033] |
| delta_cs-uniform | 64 | -0.00256 | [-0.00304, -0.00208] | [-0.00314, -0.00198] |

## F_SELECTION[merged] — U10 query log2-score, child mean over seeds

status complete, n = 64/64, critical +2.415

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | +0.00019 | [-0.00073, +0.00111] | [-0.00092, +0.00131] |
| delta_cs-support_cv | 64 | -0.00044 | [-0.00105, +0.00017] | [-0.00117, +0.00029] |
| delta_cs-uniform | 64 | -0.00247 | [-0.00293, -0.00201] | [-0.00302, -0.00192] |

## F_SELECTION_EXT[3401] — U10 query log2-score; added policies (DECISIONS P17-P19)

status complete, n = 64/64, critical +2.508

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_train_profile-fixed | 64 | +0.00094 | [-0.00031, +0.00220] | [-0.00056, +0.00244] |
| delta_cs_pca64-support_cv | 64 | -0.00067 | [-0.00147, +0.00013] | [-0.00167, +0.00033] |
| delta_cs_pca64-delta_cs | 64 | -0.00024 | [-0.00075, +0.00027] | [-0.00088, +0.00040] |

## F_SELECTION_EXT[3407] — U10 query log2-score; added policies (DECISIONS P17-P19)

status complete, n = 64/64, critical +2.440

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_train_profile-fixed | 64 | -0.00003 | [-0.00123, +0.00116] | [-0.00150, +0.00143] |
| delta_cs_pca64-support_cv | 64 | -0.00041 | [-0.00110, +0.00028] | [-0.00126, +0.00043] |
| delta_cs_pca64-delta_cs | 64 | -0.00007 | [-0.00051, +0.00037] | [-0.00061, +0.00046] |

## F_SELECTION_EXT[3413] — U10 query log2-score; added policies (DECISIONS P17-P19)

status complete, n = 64/64, critical +2.515

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_train_profile-fixed | 64 | +0.00053 | [-0.00076, +0.00183] | [-0.00104, +0.00210] |
| delta_cs_pca64-support_cv | 64 | -0.00055 | [-0.00135, +0.00025] | [-0.00155, +0.00045] |
| delta_cs_pca64-delta_cs | 64 | -0.00001 | [-0.00054, +0.00053] | [-0.00066, +0.00065] |

## F_SELECTION_EXT[merged] — U10 query log2-score, child mean over seeds; added policies

status complete, n = 64/64, critical +2.467

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_train_profile-fixed | 64 | +0.00048 | [-0.00047, +0.00143] | [-0.00069, +0.00165] |
| delta_cs_pca64-support_cv | 64 | -0.00054 | [-0.00117, +0.00008] | [-0.00130, +0.00021] |
| delta_cs_pca64-delta_cs | 64 | -0.00011 | [-0.00048, +0.00027] | [-0.00057, +0.00035] |

## EXPLORATORY_REUSED_VS_B0:G — U0 all-trials G difference vs B0, bits/trial (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.939

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| aln41_TCS[3 seeds]-B0 | 64 | +0.00123 | [-0.00016, +0.00261] | [-0.00080, +0.00326] |
| aln41_TNCE[3 seeds]-B0 | 64 | +0.00167 | [-0.00060, +0.00394] | [-0.00146, +0.00480] |
| aln41_GCS[3 seeds]-B0 | 64 | -0.00030 | [-0.00161, +0.00102] | [-0.00220, +0.00161] |
| aln41_WRONG[3 seeds]-B0 | 64 | +0.00088 | [-0.00071, +0.00246] | [-0.00147, +0.00323] |
| REVE0-B0 | 64 | +0.00031 | [-0.00292, +0.00353] | [-0.00337, +0.00398] |
| MINDMIX_branch-B0 | 64 | +0.00084 | [-0.00099, +0.00266] | [-0.00187, +0.00354] |

## EXPLORATORY_REUSED_VS_B0:AUC — U0 AUC of the readout EEG part, difference vs B0 (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.564

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| aln41_TCS[3 seeds]-B0 | 64 | +0.00950 | [+0.00248, +0.01653] | [+0.00037, +0.01864] |
| aln41_TNCE[3 seeds]-B0 | 64 | +0.01480 | [+0.00589, +0.02372] | [+0.00349, +0.02612] |
| aln41_GCS[3 seeds]-B0 | 64 | +0.00434 | [-0.00114, +0.00981] | [-0.00276, +0.01143] |
| aln41_WRONG[3 seeds]-B0 | 64 | +0.01226 | [+0.00384, +0.02069] | [+0.00153, +0.02300] |
| REVE0-B0 | 64 | -0.00091 | [-0.00969, +0.00786] | [-0.01203, +0.01021] |
| MINDMIX_branch-B0 | 64 | +0.01001 | [+0.00063, +0.01939] | [-0.00196, +0.02198] |

## EXPLORATORY_REUSED_VS_B0:delta_profile — n128 δ excess CS difference vs B0, nats (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.692

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| aln41_TCS[3 seeds]-B0 | 64 | +0.00009 | [-0.00002, +0.00021] | [-0.00006, +0.00025] |
| aln41_TNCE[3 seeds]-B0 | 64 | -0.00001 | [-0.00014, +0.00012] | [-0.00019, +0.00017] |
| aln41_GCS[3 seeds]-B0 | 64 | -0.00006 | [-0.00017, +0.00005] | [-0.00021, +0.00009] |
| aln41_WRONG[3 seeds]-B0 | 64 | +0.00013 | [+0.00001, +0.00024] | [-0.00003, +0.00028] |
| REVE0-B0 | 64 | +0.00001 | [-0.00005, +0.00007] | [-0.00007, +0.00009] |
| MINDMIX_branch-B0 | 64 | +0.00003 | [-0.00004, +0.00010] | [-0.00007, +0.00013] |

## EXPLORATORY_REUSED_VS_B0:delta_profile_pca64 — n128 δ excess CS on the PCA64 kernel variant vs B0, nats (exploratory; reused encoders carry input-support / access flags)

status complete, n = 64/64, critical +2.602

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| aln41_TCS[3 seeds]-B0 | 64 | +0.00002 | [-0.00010, +0.00015] | [-0.00014, +0.00018] |
| aln41_TNCE[3 seeds]-B0 | 64 | +0.00003 | [-0.00011, +0.00017] | [-0.00015, +0.00022] |
| aln41_GCS[3 seeds]-B0 | 64 | -0.00003 | [-0.00015, +0.00009] | [-0.00018, +0.00012] |
| aln41_WRONG[3 seeds]-B0 | 64 | +0.00007 | [-0.00005, +0.00019] | [-0.00008, +0.00023] |
| REVE0-B0 | 64 | -0.00004 | [-0.00016, +0.00008] | [-0.00020, +0.00012] |
| MINDMIX_branch-B0 | 64 | +0.00000 | [-0.00015, +0.00015] | [-0.00020, +0.00020] |

## MECHANISM_CONTROLS[3401]:G — single-seed mechanism controls (descriptive, not a stability claim)

status complete, n = 64/64, critical +2.502

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair@3401-raw_cs@3401 | 64 | +0.00148 | [-0.00026, +0.00322] | [-0.00042, +0.00337] |
| cs_pair@3401-cs_pair_wrong@3401 | 64 | -0.00012 | [-0.00092, +0.00068] | [-0.00113, +0.00088] |

## MECHANISM_CONTROLS[3401]:delta_profile — single-seed mechanism controls (descriptive, not a stability claim)

status complete, n = 64/64, critical +2.375

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair@3401-raw_cs@3401 | 64 | +0.00006 | [+0.00000, +0.00011] | [-0.00001, +0.00012] |
| cs_pair@3401-cs_pair_wrong@3401 | 64 | -0.00002 | [-0.00006, +0.00001] | [-0.00006, +0.00001] |

## MECHANISM_CONTROLS[3401]:delta_profile_pca64 — single-seed mechanism controls (descriptive, not a stability claim)

status complete, n = 64/64, critical +2.313

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair@3401-raw_cs@3401 | 64 | +0.00006 | [-0.00002, +0.00014] | [-0.00003, +0.00015] |
| cs_pair@3401-cs_pair_wrong@3401 | 64 | +0.00004 | [-0.00001, +0.00009] | [-0.00002, +0.00010] |

## DESCRIPTIVE_PRIVATE_delta_profile[3401] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.404

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00010 | [+0.00004, +0.00016] | [+0.00002, +0.00017] |
| cs_pair-info_nce | 64 | -0.00010 | [-0.00016, -0.00003] | [-0.00017, -0.00002] |
| cs_pair-sigmoid | 64 | -0.00011 | [-0.00018, -0.00004] | [-0.00019, -0.00003] |

## DESCRIPTIVE_PRIVATE_delta_profile[3407] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.315

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00013 | [+0.00005, +0.00022] | [+0.00003, +0.00024] |
| cs_pair-info_nce | 64 | -0.00006 | [-0.00012, -0.00001] | [-0.00012, -0.00000] |
| cs_pair-sigmoid | 64 | -0.00006 | [-0.00012, -0.00001] | [-0.00012, -0.00000] |

## DESCRIPTIVE_PRIVATE_delta_profile[3413] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.384

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00013 | [+0.00004, +0.00022] | [+0.00002, +0.00024] |
| cs_pair-info_nce | 64 | -0.00006 | [-0.00011, -0.00001] | [-0.00012, -0.00000] |
| cs_pair-sigmoid | 64 | -0.00005 | [-0.00010, -0.00001] | [-0.00011, +0.00000] |

## DESCRIPTIVE_PRIVATE_delta_profile_pca64[3401] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.386

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00011 | [+0.00001, +0.00020] | [-0.00001, +0.00022] |
| cs_pair-info_nce | 64 | -0.00000 | [-0.00008, +0.00008] | [-0.00010, +0.00009] |
| cs_pair-sigmoid | 64 | -0.00001 | [-0.00009, +0.00007] | [-0.00011, +0.00009] |

## DESCRIPTIVE_PRIVATE_delta_profile_pca64[3407] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.385

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00010 | [-0.00001, +0.00021] | [-0.00004, +0.00023] |
| cs_pair-info_nce | 64 | -0.00003 | [-0.00012, +0.00005] | [-0.00013, +0.00006] |
| cs_pair-sigmoid | 64 | -0.00003 | [-0.00011, +0.00006] | [-0.00013, +0.00007] |

## DESCRIPTIVE_PRIVATE_delta_profile_pca64[3413] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.426

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.00012 | [+0.00002, +0.00023] | [-0.00000, +0.00025] |
| cs_pair-info_nce | 64 | -0.00002 | [-0.00010, +0.00006] | [-0.00011, +0.00008] |
| cs_pair-sigmoid | 64 | -0.00001 | [-0.00009, +0.00007] | [-0.00010, +0.00009] |

## DESCRIPTIVE_PRIVATE_AUC[3401] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.416

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.02241 | [+0.01127, +0.03355] | [+0.00893, +0.03589] |
| cs_pair-info_nce | 64 | -0.00031 | [-0.00456, +0.00394] | [-0.00539, +0.00477] |
| cs_pair-sigmoid | 64 | -0.00310 | [-0.00768, +0.00149] | [-0.00862, +0.00243] |

## DESCRIPTIVE_PRIVATE_AUC[3407] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.268

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.02618 | [+0.01465, +0.03771] | [+0.01302, +0.03934] |
| cs_pair-info_nce | 64 | +0.00506 | [-0.00076, +0.01088] | [-0.00166, +0.01178] |
| cs_pair-sigmoid | 64 | +0.00513 | [-0.00063, +0.01089] | [-0.00157, +0.01183] |

## DESCRIPTIVE_PRIVATE_AUC[3413] — same members as F_PRIVATE on another endpoint (descriptive)

status complete, n = 64/64, critical +2.415

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| cs_pair-B0 | 64 | +0.02457 | [+0.01243, +0.03670] | [+0.00984, +0.03929] |
| cs_pair-info_nce | 64 | +0.00395 | [-0.00109, +0.00900] | [-0.00208, +0.00999] |
| cs_pair-sigmoid | 64 | +0.00116 | [-0.00394, +0.00627] | [-0.00493, +0.00726] |

## EXPLORATORY_SELECTION_ALN41[3401] — U10 query log2-score (exploratory candidate set)

status complete, n = 64/64, critical +2.999

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | -0.00040 | [-0.00208, +0.00128] | [-0.00271, +0.00192] |
| delta_cs-support_cv | 64 | -0.00017 | [-0.00114, +0.00080] | [-0.00163, +0.00129] |
| delta_cs-uniform | 64 | -0.00458 | [-0.00562, -0.00354] | [-0.00586, -0.00330] |
| delta_train_profile-fixed | 64 | -0.00018 | [-0.00226, +0.00191] | [-0.00329, +0.00293] |
| delta_cs_pca64-support_cv | 64 | +0.00021 | [-0.00074, +0.00116] | [-0.00120, +0.00162] |
| delta_cs_pca64-delta_cs | 64 | +0.00038 | [-0.00057, +0.00133] | [-0.00087, +0.00163] |

## EXPLORATORY_SELECTION_ALN41[3407] — U10 query log2-score (exploratory candidate set)

status complete, n = 64/64, critical +2.660

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | -0.00013 | [-0.00165, +0.00139] | [-0.00211, +0.00185] |
| delta_cs-support_cv | 64 | -0.00084 | [-0.00188, +0.00020] | [-0.00222, +0.00054] |
| delta_cs-uniform | 64 | -0.00485 | [-0.00548, -0.00423] | [-0.00569, -0.00401] |
| delta_train_profile-fixed | 64 | +0.00037 | [-0.00191, +0.00266] | [-0.00264, +0.00339] |
| delta_cs_pca64-support_cv | 64 | -0.00051 | [-0.00154, +0.00053] | [-0.00188, +0.00087] |
| delta_cs_pca64-delta_cs | 64 | +0.00034 | [-0.00015, +0.00082] | [-0.00032, +0.00099] |

## EXPLORATORY_SELECTION_ALN41[3413] — U10 query log2-score (exploratory candidate set)

status complete, n = 64/64, critical +2.761

| member | n | estimate | pointwise 95% | simultaneous 95% |
|---|---:|---:|---|---|
| delta_cs-fixed | 64 | -0.00011 | [-0.00154, +0.00131] | [-0.00208, +0.00185] |
| delta_cs-support_cv | 64 | -0.00118 | [-0.00222, -0.00014] | [-0.00260, +0.00023] |
| delta_cs-uniform | 64 | -0.00502 | [-0.00563, -0.00440] | [-0.00588, -0.00415] |
| delta_train_profile-fixed | 64 | +0.00062 | [-0.00057, +0.00181] | [-0.00095, +0.00219] |
| delta_cs_pca64-support_cv | 64 | -0.00098 | [-0.00171, -0.00025] | [-0.00198, +0.00002] |
| delta_cs_pca64-delta_cs | 64 | +0.00020 | [-0.00060, +0.00101] | [-0.00090, +0.00131] |

## Levels per encoder (child means; descriptive)

| encoder | n | G all (bits) | G contract | AUC EEG part | δ excess n128 U (nats) | δ excess n128 PCA64 | E−twin (bits) |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 | 64 | -0.00583 | -0.00553 | +0.5048 | +0.000015 | +0.000035 | +0.00156 |
| MINDMIX_branch | 64 | -0.00499 | -0.00467 | +0.5148 | +0.000046 | +0.000037 | +0.00121 |
| REVE0 | 64 | -0.00553 | -0.00532 | +0.5039 | +0.000026 | -0.000004 | -0.00030 |
| aln41_GCS@3401 | 64 | -0.00402 | -0.00426 | +0.5102 | -0.000053 | -0.000049 | +0.00478 |
| aln41_GCS@3407 | 64 | -0.00846 | -0.00744 | +0.5044 | +0.000016 | +0.000055 | -0.00161 |
| aln41_GCS@3413 | 64 | -0.00590 | -0.00674 | +0.5127 | -0.000102 | +0.000010 | +0.00326 |
| aln41_TCS@3401 | 64 | -0.00468 | -0.00411 | +0.5147 | +0.000140 | +0.000094 | +0.00251 |
| aln41_TCS@3407 | 64 | -0.00482 | -0.00487 | +0.5067 | -0.000012 | -0.000031 | +0.00423 |
| aln41_TCS@3413 | 64 | -0.00430 | -0.00463 | +0.5214 | +0.000200 | +0.000110 | +0.00334 |
| aln41_TNCE@3401 | 64 | -0.00392 | -0.00404 | +0.5202 | +0.000035 | +0.000074 | +0.00364 |
| aln41_TNCE@3407 | 64 | -0.00441 | -0.00493 | +0.5181 | -0.000009 | +0.000039 | +0.00318 |
| aln41_TNCE@3413 | 64 | -0.00416 | -0.00470 | +0.5204 | -0.000002 | +0.000088 | +0.00383 |
| aln41_WRONG@3401 | 64 | -0.00563 | -0.00556 | +0.5138 | +0.000165 | +0.000088 | +0.00127 |
| aln41_WRONG@3407 | 64 | -0.00615 | -0.00677 | +0.5154 | +0.000148 | +0.000124 | +0.00226 |
| aln41_WRONG@3413 | 64 | -0.00309 | -0.00343 | +0.5219 | +0.000108 | +0.000114 | +0.00420 |
| cs_pair@3401 | 64 | -0.00215 | -0.00288 | +0.5272 | +0.000111 | +0.000142 | +0.00554 |
| cs_pair@3407 | 64 | -0.00251 | -0.00310 | +0.5310 | +0.000149 | +0.000133 | +0.00491 |
| cs_pair@3413 | 64 | -0.00280 | -0.00332 | +0.5293 | +0.000144 | +0.000160 | +0.00686 |
| cs_pair_noise@3401 | 64 | -0.00255 | -0.00288 | +0.5266 | +0.000113 | +0.000119 | +0.00604 |
| cs_pair_noise@3407 | 64 | -0.00277 | -0.00267 | +0.5258 | +0.000094 | +0.000100 | +0.00574 |
| cs_pair_wrong@3401 | 64 | -0.00203 | -0.00258 | +0.5306 | +0.000135 | +0.000101 | +0.00685 |
| cs_pair_wrong@3407 | 64 | -0.00254 | -0.00314 | +0.5270 | +0.000102 | +0.000096 | +0.00609 |
| cs_pair_wrong@3413 | 64 | -0.00256 | -0.00281 | +0.5271 | +0.000127 | +0.000096 | +0.00497 |
| info_nce@3401 | 64 | -0.00263 | -0.00315 | +0.5275 | +0.000206 | +0.000145 | +0.00640 |
| info_nce@3407 | 64 | -0.00250 | -0.00295 | +0.5259 | +0.000213 | +0.000167 | +0.00592 |
| info_nce@3413 | 64 | -0.00299 | -0.00332 | +0.5254 | +0.000207 | +0.000179 | +0.00486 |
| raw_cs@3401 | 64 | -0.00363 | -0.00456 | +0.5287 | +0.000054 | +0.000079 | +0.00415 |
| raw_cs@3407 | 64 | -0.00422 | -0.00469 | +0.5190 | +0.000037 | +0.000099 | +0.00307 |
| raw_cs@3413 | 64 | -0.00296 | -0.00320 | +0.5259 | +0.000132 | +0.000115 | +0.00472 |
| sigmoid@3401 | 64 | -0.00203 | -0.00280 | +0.5303 | +0.000222 | +0.000150 | +0.00625 |
| sigmoid@3407 | 64 | -0.00247 | -0.00292 | +0.5258 | +0.000213 | +0.000161 | +0.00595 |
| sigmoid@3413 | 64 | -0.00221 | -0.00268 | +0.5282 | +0.000197 | +0.000167 | +0.00583 |

## By protocol (child60 = audited alternative sequence; regular = the other 63)

| encoder | regular G | regular δ excess | child60 G | child60 δ excess |
|---|---:|---:|---:|---:|
| B0 | -0.00617 | +0.000016 | +0.01541 | -0.000063 |
| MINDMIX_branch | -0.00578 | +0.000046 | +0.04460 | +0.000053 |
| REVE0 | -0.00486 | +0.000025 | -0.04762 | +0.000061 |
| aln41_GCS@3401 | -0.00477 | -0.000048 | +0.04291 | -0.000357 |
| aln41_GCS@3407 | -0.00829 | +0.000025 | -0.01936 | -0.000558 |
| aln41_GCS@3413 | -0.00741 | -0.000098 | +0.08929 | -0.000387 |
| aln41_TCS@3401 | -0.00479 | +0.000142 | +0.00229 | -0.000002 |
| aln41_TCS@3407 | -0.00557 | -0.000006 | +0.04248 | -0.000371 |
| aln41_TCS@3413 | -0.00488 | +0.000203 | +0.03199 | +0.000017 |
| aln41_TNCE@3401 | -0.00363 | +0.000029 | -0.02207 | +0.000444 |
| aln41_TNCE@3407 | -0.00380 | -0.000014 | -0.04330 | +0.000306 |
| aln41_TNCE@3413 | -0.00406 | -0.000009 | -0.01095 | +0.000438 |
| aln41_WRONG@3401 | -0.00606 | +0.000168 | +0.02155 | -0.000028 |
| aln41_WRONG@3407 | -0.00537 | +0.000150 | -0.05490 | +0.000041 |
| aln41_WRONG@3413 | -0.00397 | +0.000111 | +0.05270 | -0.000048 |
| cs_pair@3401 | -0.00197 | +0.000113 | -0.01330 | -0.000014 |
| cs_pair@3407 | -0.00268 | +0.000152 | +0.00849 | -0.000062 |
| cs_pair@3413 | -0.00271 | +0.000147 | -0.00852 | -0.000061 |
| cs_pair_noise@3401 | -0.00247 | +0.000116 | -0.00746 | -0.000081 |
| cs_pair_noise@3407 | -0.00238 | +0.000096 | -0.02748 | -0.000062 |
| cs_pair_wrong@3401 | -0.00182 | +0.000137 | -0.01520 | -0.000019 |
| cs_pair_wrong@3407 | -0.00251 | +0.000105 | -0.00425 | -0.000066 |
| cs_pair_wrong@3413 | -0.00249 | +0.000129 | -0.00664 | -0.000014 |
| info_nce@3401 | -0.00233 | +0.000207 | -0.02169 | +0.000145 |
| info_nce@3407 | -0.00257 | +0.000215 | +0.00188 | +0.000110 |
| info_nce@3413 | -0.00289 | +0.000209 | -0.00974 | +0.000079 |
| raw_cs@3401 | -0.00288 | +0.000058 | -0.05049 | -0.000185 |
| raw_cs@3407 | -0.00447 | +0.000033 | +0.01133 | +0.000286 |
| raw_cs@3413 | -0.00329 | +0.000134 | +0.01802 | -0.000016 |
| sigmoid@3401 | -0.00192 | +0.000223 | -0.00867 | +0.000145 |
| sigmoid@3407 | -0.00257 | +0.000215 | +0.00363 | +0.000105 |
| sigmoid@3413 | -0.00212 | +0.000199 | -0.00831 | +0.000070 |

## δ profile sensitivity (seed 3401 encoders and B0; child means of excess CS, nats)

| encoder | n32 ×1 | n64 ×1 | n128 ×0.5 | n128 ×1 | n128 ×2 |
|---|---:|---:|---:|---:|---:|
| B0 | -0.000122 | -0.000063 | +0.000031 | +0.000015 | +0.000004 |
| aln41_GCS@3401 | +0.000418 | +0.000081 | -0.000037 | -0.000053 | -0.000017 |
| aln41_TCS@3401 | -0.000233 | +0.000240 | +0.000457 | +0.000140 | +0.000035 |
| aln41_TNCE@3401 | -0.000038 | +0.000193 | +0.000265 | +0.000035 | +0.000007 |
| aln41_WRONG@3401 | -0.000082 | +0.000355 | +0.000787 | +0.000165 | +0.000024 |
| cs_pair@3401 | -0.000064 | +0.000103 | +0.000419 | +0.000111 | +0.000028 |
| cs_pair_noise@3401 | -0.000010 | +0.000162 | +0.000401 | +0.000113 | +0.000029 |
| cs_pair_wrong@3401 | -0.000018 | +0.000188 | +0.000480 | +0.000135 | +0.000034 |
| info_nce@3401 | +0.000226 | +0.000304 | +0.000698 | +0.000206 | +0.000053 |
| raw_cs@3401 | +0.000083 | -0.000005 | +0.000162 | +0.000054 | +0.000014 |
| sigmoid@3401 | +0.000236 | +0.000315 | +0.000736 | +0.000222 | +0.000057 |

## U10 decisions and fallbacks (counts over child × support seed)

- primary_s3401: fixed by fold {0: 'sigmoid@3401', 1: 'info_nce@3401', 2: 'cs_pair@3401', 3: 'sigmoid@3401', 4: 'B0'}; decisions {'delta_cs:cs_pair@3401': 55, 'delta_cs_pca64:B0': 80, 'delta_train_profile:sigmoid@3401': 320, 'fixed:sigmoid@3401': 130, 'support_cv:sigmoid@3401': 83, 'delta_cs_pca64:sigmoid@3401': 87, 'support_cv:cs_pair@3401': 92, 'delta_cs:sigmoid@3401': 100, 'delta_cs_pca64:info_nce@3401': 79, 'support_cv:B0': 83, 'delta_cs:B0': 87, 'delta_cs_pca64:cs_pair@3401': 74, 'support_cv:info_nce@3401': 62, 'delta_cs:info_nce@3401': 78, 'fixed:info_nce@3401': 65, 'fixed:cs_pair@3401': 65, 'fixed:B0': 60}; fallbacks none
- primary_s3407: fixed by fold {0: 'sigmoid@3407', 1: 'info_nce@3407', 2: 'cs_pair@3407', 3: 'cs_pair@3407', 4: 'cs_pair@3407'}; decisions {'delta_cs:cs_pair@3407': 87, 'delta_cs_pca64:info_nce@3407': 83, 'delta_train_profile:info_nce@3407': 130, 'fixed:sigmoid@3407': 65, 'support_cv:B0': 89, 'delta_cs:B0': 89, 'delta_cs_pca64:sigmoid@3407': 56, 'support_cv:cs_pair@3407': 114, 'delta_cs:sigmoid@3407': 73, 'delta_cs_pca64:cs_pair@3407': 91, 'delta_cs_pca64:B0': 90, 'support_cv:info_nce@3407': 57, 'delta_cs:info_nce@3407': 71, 'support_cv:sigmoid@3407': 60, 'fixed:info_nce@3407': 65, 'delta_train_profile:sigmoid@3407': 190, 'fixed:cs_pair@3407': 190}; fallbacks none
- primary_s3413: fixed by fold {0: 'sigmoid@3413', 1: 'sigmoid@3413', 2: 'cs_pair@3413', 3: 'info_nce@3413', 4: 'B0'}; decisions {'delta_cs:info_nce@3413': 88, 'delta_cs_pca64:info_nce@3413': 76, 'delta_train_profile:info_nce@3413': 320, 'fixed:sigmoid@3413': 130, 'support_cv:info_nce@3413': 70, 'delta_cs:B0': 93, 'delta_cs_pca64:cs_pair@3413': 93, 'support_cv:cs_pair@3413': 91, 'delta_cs:sigmoid@3413': 57, 'delta_cs_pca64:sigmoid@3413': 70, 'support_cv:B0': 95, 'delta_cs_pca64:B0': 81, 'delta_cs:cs_pair@3413': 82, 'support_cv:sigmoid@3413': 64, 'fixed:cs_pair@3413': 65, 'fixed:info_nce@3413': 65, 'fixed:B0': 60}; fallbacks none
- aln41_s3401: fixed by fold {0: 'aln41_GCS@3401', 1: 'aln41_TNCE@3401', 2: 'aln41_TCS@3401', 3: 'aln41_GCS@3401', 4: 'B0'}; decisions {'delta_cs:aln41_GCS@3401': 93, 'delta_cs_pca64:B0': 76, 'delta_train_profile:aln41_TCS@3401': 320, 'fixed:aln41_GCS@3401': 130, 'support_cv:aln41_TNCE@3401': 88, 'delta_cs_pca64:aln41_GCS@3401': 78, 'support_cv:aln41_TCS@3401': 78, 'delta_cs_pca64:aln41_TCS@3401': 88, 'support_cv:aln41_GCS@3401': 91, 'delta_cs_pca64:aln41_TNCE@3401': 78, 'delta_cs:B0': 76, 'delta_cs:aln41_TCS@3401': 88, 'delta_cs:aln41_TNCE@3401': 63, 'support_cv:B0': 63, 'fixed:aln41_TNCE@3401': 65, 'fixed:aln41_TCS@3401': 65, 'fixed:B0': 60}; fallbacks none
- aln41_s3407: fixed by fold {0: 'aln41_GCS@3407', 1: 'aln41_TCS@3407', 2: 'aln41_GCS@3407', 3: 'aln41_TNCE@3407', 4: 'B0'}; decisions {'delta_cs:aln41_GCS@3407': 84, 'delta_cs_pca64:aln41_GCS@3407': 82, 'delta_train_profile:aln41_TCS@3407': 65, 'fixed:aln41_GCS@3407': 130, 'support_cv:aln41_TCS@3407': 85, 'delta_cs:B0': 59, 'delta_cs_pca64:aln41_TCS@3407': 78, 'delta_cs:aln41_TCS@3407': 94, 'delta_cs_pca64:aln41_TNCE@3407': 81, 'delta_cs_pca64:B0': 79, 'delta_cs:aln41_TNCE@3407': 83, 'support_cv:aln41_GCS@3407': 62, 'support_cv:aln41_TNCE@3407': 113, 'support_cv:B0': 60, 'delta_train_profile:aln41_GCS@3407': 130, 'fixed:aln41_TCS@3407': 65, 'delta_train_profile:B0': 65, 'fixed:aln41_TNCE@3407': 65, 'delta_train_profile:aln41_TNCE@3407': 60, 'fixed:B0': 60}; fallbacks none
- aln41_s3413: fixed by fold {0: 'aln41_TCS@3413', 1: 'aln41_TCS@3413', 2: 'aln41_TCS@3413', 3: 'aln41_TNCE@3413', 4: 'B0'}; decisions {'delta_cs:B0': 61, 'delta_cs_pca64:B0': 75, 'delta_train_profile:aln41_TCS@3413': 320, 'fixed:aln41_TCS@3413': 195, 'support_cv:aln41_TNCE@3413': 99, 'delta_cs_pca64:aln41_TNCE@3413': 90, 'support_cv:B0': 61, 'delta_cs:aln41_TCS@3413': 87, 'delta_cs_pca64:aln41_TCS@3413': 81, 'support_cv:aln41_TCS@3413': 77, 'delta_cs:aln41_TNCE@3413': 79, 'support_cv:aln41_GCS@3413': 83, 'delta_cs:aln41_GCS@3413': 93, 'delta_cs_pca64:aln41_GCS@3413': 74, 'fixed:aln41_TNCE@3413': 65, 'fixed:B0': 60}; fallbacks none

## Cross-stimulus (recovered ALN4.1 R2, pure tone → bapa; not re-run)

Source results/auditory_alignment_v3/aln41/r2/contrasts.json (sha256 27e68ffefb59).

### F_CROSS_STIM:BAPA

| member | n | estimate | simultaneous 95% |
|---|---:|---:|---|
| B0:transfer-0.5 | 24 | +0.00657 | [-0.01248, +0.02562] |
| B0:refit-0.5 | 24 | -0.00477 | [-0.03142, +0.02188] |
| B0:refit-transfer | 24 | -0.01134 | [-0.03490, +0.01222] |
| TCS:transfer-0.5 | 24 | +0.00374 | [-0.01322, +0.02069] |
| TCS:refit-0.5 | 24 | +0.00172 | [-0.01869, +0.02212] |
| TCS:refit-transfer | 24 | -0.00202 | [-0.01881, +0.01477] |
| TNCE:transfer-0.5 | 24 | +0.01167 | [-0.01862, +0.04196] |
| TNCE:refit-0.5 | 24 | -0.00167 | [-0.02803, +0.02469] |
| TNCE:refit-transfer | 24 | -0.01334 | [-0.03486, +0.00818] |
| transfer:TCS-B0 | 24 | -0.00283 | [-0.01967, +0.01401] |
| transfer:TCS-TNCE | 24 | -0.00793 | [-0.02859, +0.01272] |
| refit:TCS-B0 | 24 | +0.00648 | [-0.00991, +0.02288] |
| refit:TCS-TNCE | 24 | +0.00338 | [-0.01134, +0.01810] |

### F_CROSS_STIM_SECONDARY:BAPA

| member | n | estimate | simultaneous 95% |
|---|---:|---:|---|
| B0:transfer-0.0 | 24 | -0.00062 | [-0.00191, +0.00066] |
| B0:refit-0.0 | 24 | -0.00202 | [-0.00455, +0.00052] |
| B0:refit-transfer | 24 | -0.00140 | [-0.00361, +0.00082] |
| TCS:transfer-0.0 | 24 | -0.00111 | [-0.00247, +0.00025] |
| TCS:refit-0.0 | 24 | -0.00181 | [-0.00358, -0.00003] |
| TCS:refit-transfer | 24 | -0.00070 | [-0.00212, +0.00073] |
| TNCE:transfer-0.0 | 24 | -0.00068 | [-0.00327, +0.00191] |
| TNCE:refit-0.0 | 24 | -0.00229 | [-0.00460, +0.00003] |
| TNCE:refit-transfer | 24 | -0.00161 | [-0.00325, +0.00003] |
| transfer:TCS-B0 | 24 | -0.00049 | [-0.00178, +0.00080] |
| transfer:TCS-TNCE | 24 | -0.00043 | [-0.00230, +0.00144] |
| refit:TCS-B0 | 24 | +0.00021 | [-0.00137, +0.00180] |
| refit:TCS-TNCE | 24 | +0.00048 | [-0.00083, +0.00180] |

### Same-day pairs (8; descriptive mean AUC [min, max])

| arm:route | n | mean AUC | range |
|---|---:|---:|---|
| B0:within | 8 | +0.5148 | [+0.453, +0.563] |
| B0:transfer | 8 | +0.5062 | [+0.466, +0.574] |
| B0:refit | 8 | +0.5019 | [+0.418, +0.564] |
| TCS:within | 8 | +0.5307 | [+0.492, +0.579] |
| TCS:transfer | 8 | +0.4992 | [+0.467, +0.529] |
| TCS:refit | 8 | +0.5041 | [+0.452, +0.543] |
| TNCE:within | 8 | +0.5538 | [+0.508, +0.598] |
| TNCE:transfer | 8 | +0.5150 | [+0.468, +0.599] |
| TNCE:refit | 8 | +0.5013 | [+0.436, +0.574] |

same-day pairs: 8 identity groups with both lanes on the same day; descriptive only. AUC within = pure-tone within-lane (person-disjoint folds), transfer = pure-tone readout on bapa, refit = bapa readout on bapa.

New frozen representations: not run: the existing formal path extracts three 400 ms crops through the ALN4.1 time bank and mixes slots with q0; applying it to the DEP12 1 s container would need a new extraction/readout definition (03 §6.2 condition not met)

