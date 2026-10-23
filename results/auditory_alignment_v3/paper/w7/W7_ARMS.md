# W7 GPU arms — frozen-readout endpoints and W7_FACT families

Person means [95% percentile bootstrap] over people with all three seeds; families: aln41.analysis.family (B = 4000), simultaneous 95%, positive = arm better. Pre-registered in W7_CS_DEPENDENCE_PREREG_FROZEN.md (frozen 2026-10-22 19:48; hypotheses proposed after Tables 2-6 were seen); PRES uses APPENDUM_04 (L2), beta = 1.0; CCS uses APPENDUM_02/03.

## Endpoint means

| endpoint (cohort) | TCS | TCS_RES | TCS_PRES | TCS_RES_PRES | TCS_CCS |
|---|---|---|---|---|---|
| content_direct_r (dtu) | 0.0793 [0.0690, 0.0896] (n44) | 0.0853 [0.0736, 0.0964] (n44) | 0.0965 [0.0819, 0.1096] (n44) | 0.0987 [0.0845, 0.1116] (n44) | 0.0526 [0.0437, 0.0611] (n44) |
| content_direct_r (fau) | 0.0502 [0.0429, 0.0577] (n67) | 0.0591 [0.0504, 0.0679] (n67) | 0.0481 [0.0409, 0.0554] (n67) | 0.0473 [0.0410, 0.0537] (n67) | 0.0355 [0.0298, 0.0413] (n67) |
| content_r (dtu) | 0.0483 [0.0406, 0.0561] (n44) | 0.0538 [0.0436, 0.0641] (n44) | 0.0273 [0.0190, 0.0358] (n44) | 0.0286 [0.0200, 0.0368] (n44) | 0.0306 [0.0236, 0.0376] (n44) |
| content_r (fau) | 0.0486 [0.0402, 0.0568] (n67) | 0.0424 [0.0344, 0.0501] (n67) | 0.0202 [0.0146, 0.0261] (n67) | 0.0219 [0.0165, 0.0276] (n67) | 0.0278 [0.0222, 0.0331] (n67) |
| time_fixed_loss (dtu) | 0.0570 [0.0485, 0.0653] (n44) | 0.0595 [0.0486, 0.0705] (n44) | 0.0142 [0.0052, 0.0231] (n44) | 0.0126 [0.0035, 0.0217] (n44) | 0.0373 [0.0293, 0.0451] (n44) |
| time_fixed_loss (fau) | 0.0323 [0.0238, 0.0409] (n67) | 0.0395 [0.0314, 0.0479] (n67) | 0.0267 [0.0184, 0.0353] (n67) | 0.0295 [0.0203, 0.0392] (n67) | 0.0220 [0.0162, 0.0278] (n67) |
| attention20_acc (dtu) | 0.6119 [0.5929, 0.6309] (n44) | 0.6165 [0.5961, 0.6369] (n44) | 0.6224 [0.6000, 0.6447] (n44) | 0.6257 [0.6036, 0.6471] (n44) | 0.5623 [0.5434, 0.5807] (n44) |
| attention20_acc (fau) | 0.5153 [0.5030, 0.5278] (n67) | 0.5195 [0.5083, 0.5315] (n67) | 0.5110 [0.4993, 0.5222] (n67) | 0.5188 [0.5081, 0.5295] (n67) | 0.5162 [0.5052, 0.5282] (n67) |
| attention20_nll_bits (dtu) | 0.9421 [0.9256, 0.9589] (n44) | 0.9417 [0.9197, 0.9639] (n44) | 0.9321 [0.9094, 0.9546] (n44) | 0.9304 [0.9077, 0.9532] (n44) | 0.9777 [0.9664, 0.9897] (n44) |
| attention20_nll_bits (fau) | 0.9995 [0.9969, 1.0021] (n67) | 0.9981 [0.9951, 1.0009] (n67) | 1.0003 [0.9977, 1.0030] (n67) | 0.9993 [0.9972, 1.0015] (n67) | 0.9995 [0.9975, 1.0014] (n67) |
| content_hist_bits (private) | -0.0008 [-0.0022, 0.0009] (n64) | -0.0006 [-0.0022, 0.0015] (n64) | -0.0026 [-0.0036, -0.0012] (n64) | -0.0023 [-0.0034, -0.0007] (n64) | -0.0009 [-0.0023, 0.0011] (n64) |
| current_auc (private) | 0.5258 [0.5173, 0.5346] (n64) | 0.5260 [0.5173, 0.5357] (n64) | 0.5067 [0.5008, 0.5127] (n64) | 0.5069 [0.5015, 0.5124] (n64) | 0.5201 [0.5127, 0.5279] (n64) |
| age_abs_err (private) | 26.8631 [22.3049, 31.8048] (n64) | 24.0278 [19.8114, 28.8840] (n64) | 28.0587 [22.3528, 34.1287] (n64) | 27.9307 [22.2812, 34.0027] (n64) | 27.6660 [22.5013, 33.4304] (n64) |

## W7_FACT families

**W7_FACT:content_direct_r:dtu** — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00598 | [-0.00184, +0.01380] |
| TCS_PRES-TCS | +0.01726 | [+0.00631, +0.02821] |
| TCS_RES_PRES-TCS | +0.01942 | [+0.00842, +0.03041] |
| TCS_CCS-TCS | -0.02669 | [-0.03746, -0.01591] |

**W7_FACT:content_direct_r:fau** — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00894 | [+0.00424, +0.01364] |
| TCS_PRES-TCS | -0.00213 | [-0.01106, +0.00681] |
| TCS_RES_PRES-TCS | -0.00289 | [-0.01174, +0.00596] |
| TCS_CCS-TCS | -0.01470 | [-0.02107, -0.00832] |

**W7_FACT:content_r:dtu** — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00551 | [-0.00210, +0.01313] |
| TCS_PRES-TCS | -0.02093 | [-0.03040, -0.01145] |
| TCS_RES_PRES-TCS | -0.01967 | [-0.02869, -0.01065] |
| TCS_CCS-TCS | -0.01762 | [-0.02502, -0.01022] |

**W7_FACT:content_r:fau** — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | -0.00616 | [-0.01115, -0.00116] |
| TCS_PRES-TCS | -0.02841 | [-0.03887, -0.01795] |
| TCS_RES_PRES-TCS | -0.02666 | [-0.03631, -0.01700] |
| TCS_CCS-TCS | -0.02080 | [-0.02722, -0.01437] |

**W7_FACT:time_fixed_loss:dtu** — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | -0.00257 | [-0.01246, +0.00732] |
| TCS_PRES-TCS | +0.04275 | [+0.02943, +0.05608] |
| TCS_RES_PRES-TCS | +0.04440 | [+0.03131, +0.05748] |
| TCS_CCS-TCS | +0.01967 | [+0.01104, +0.02831] |

**W7_FACT:time_fixed_loss:fau** — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | -0.00718 | [-0.01225, -0.00212] |
| TCS_PRES-TCS | +0.00562 | [-0.00769, +0.01894] |
| TCS_RES_PRES-TCS | +0.00279 | [-0.01233, +0.01792] |
| TCS_CCS-TCS | +0.01027 | [+0.00222, +0.01831] |

**W7_FACT:attention20_acc:dtu** — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00459 | [-0.00973, +0.01890] |
| TCS_PRES-TCS | +0.01055 | [-0.01037, +0.03146] |
| TCS_RES_PRES-TCS | +0.01385 | [-0.00671, +0.03441] |
| TCS_CCS-TCS | -0.04958 | [-0.06576, -0.03340] |

**W7_FACT:attention20_acc:fau** — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00420 | [-0.00560, +0.01399] |
| TCS_PRES-TCS | -0.00430 | [-0.02006, +0.01146] |
| TCS_RES_PRES-TCS | +0.00348 | [-0.01300, +0.01996] |
| TCS_CCS-TCS | +0.00090 | [-0.01589, +0.01769] |

**W7_FACT:attention20_nll_bits:dtu** — complete, n 44/44

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00038 | [-0.01197, +0.01273] |
| TCS_PRES-TCS | +0.00995 | [-0.00883, +0.02872] |
| TCS_RES_PRES-TCS | +0.01171 | [-0.00664, +0.03006] |
| TCS_CCS-TCS | -0.03565 | [-0.04722, -0.02408] |

**W7_FACT:attention20_nll_bits:fau** — complete, n 67/67

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00145 | [-0.00031, +0.00320] |
| TCS_PRES-TCS | -0.00081 | [-0.00376, +0.00215] |
| TCS_RES_PRES-TCS | +0.00021 | [-0.00250, +0.00292] |
| TCS_CCS-TCS | +0.00006 | [-0.00278, +0.00291] |

**W7_FACT:content_hist_bits:private** — complete, n 64/64

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00023 | [-0.00054, +0.00101] |
| TCS_PRES-TCS | -0.00173 | [-0.00298, -0.00048] |
| TCS_RES_PRES-TCS | -0.00147 | [-0.00274, -0.00019] |
| TCS_CCS-TCS | -0.00003 | [-0.00088, +0.00081] |

**W7_FACT:current_auc:private** — complete, n 64/64

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +0.00019 | [-0.00384, +0.00421] |
| TCS_PRES-TCS | -0.01907 | [-0.02924, -0.00891] |
| TCS_RES_PRES-TCS | -0.01884 | [-0.02958, -0.00810] |
| TCS_CCS-TCS | -0.00569 | [-0.01111, -0.00027] |

**W7_FACT:age_abs_err:private** — complete, n 64/64

| member | estimate | simultaneous 95% |
|---|---|---|
| TCS_RES-TCS | +2.83521 | [+1.10921, +4.56122] |
| TCS_PRES-TCS | -1.19565 | [-4.83377, +2.44247] |
| TCS_RES_PRES-TCS | -1.06765 | [-4.68623, +2.55093] |
| TCS_CCS-TCS | -0.80298 | [-3.46689, +1.86093] |

