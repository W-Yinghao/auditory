# ATTENTION_ORDER_CORRECTION — candidate order in the D_ATTENTION learned integrator (R34_ATTENTION_ORDER)

日期／代码与数据版本：generated 2026-10-17 05:45 CEST (Slurm job 1043780) by `python -m auditory_alignment_v3.aln34.attention_order --analyze`; evaluation_version `aln34_attention_order_v2`; scores on NVIDIA A30, NVIDIA A40, Tesla V100-PCIE-16GB, Tesla V100S-PCIE-32GB; code sha256 in `results/auditory_alignment_v3/aln34/attention_order/attention_order.json`.

本轮完成／运行／待依赖：380 D_ATTENTION trained-model rows (all arms); unit status complement_policy included 55; complement_policy record_incomplete_or_held 45; dense_fm_policy included 58; dense_fm_policy record_incomplete_or_held 42; lag_local_tokens included 180. QC tier-1 failures 0, tier-2-only (sensitivity) 0; max reproduction errors {'margin': 5.320953912202331e-08, 'margin_over_rms_s': 1.1768145630791475e-06, 'ms_windows': 0.0, 'lt_windows': 0.0, 'coef_rel': 2.8009717984791097e-06}. Held policy executions stay held and are not filled.

已见信息与本轮新增信息：analysis note `private/auditory_alignment_v3/aln34/ATTENTION_ORDER_NOTE.md` (sha256 `a98fa73537ebd834…`; v2 design in its §11, written before any value here was computed). Seen before this analysis: the seed-3401 D_ATTENTION lag-arm results (D_ATTENTION_RESULTS.md, d_lag.json), including the degenerate native learned_temporal column. The panel's legacy fixed-order AT-INTEGRATOR values (3407, 3413, seed mean; unified and native) had been computed and written by the R34_D_PANEL lane of the same session (d_multiseed.json 20:01, D_MULTI_SEED_RESULTS.md §1.6 20:03) before this track's design was finalised; this lane did not read them (note §11.1), and here they are reproduction targets, not new evidence. The policy-arm attention values had never been aggregated and were not read. Every paired-order value (AO-PAIRED-LEGACY, AO-ANTISYM) and every policy-arm aggregate in this document is computed for the first time by this run. Old rows (D_ATTENTION_RESULTS.md, d_lag.json, D_MULTI_SEED outputs, unit records) are unchanged; this is a versioned correction.

## 1. 当前观察

Paired-order evaluation: every test window is presented as (attended, ignored) with label 1 and as (ignored, attended) with label 0, both on the test side; credit per physical window = mean of the two presentations (tie 0.5). `antisymmetric_learned` = 0.5[h(d) − h(−d)] with h the legacy logistic model on the five summaries of d / σ (σ = training-window RMS of d), refitted on the training participants' windows in both orders (tol 1e-10); only fits with status `ok` are scored. Within each contrast the reference and the candidate are averaged over the same units. Positive Δ = learned integrator more accurate than mean_score. Unified readout primary; native secondary (pointwise). Identity-level bootstrap-t, simultaneous = max-t within the family. Arms are never pooled; the policy arms have seed 3401 only.

### 1.0 Coverage (trained models per arm × seed × dataset × task/objective; complete = 10 = 5 subject folds × 2 content folds)

| arm | seed | dataset | task / objective | included | sensitivity only | QC failed | scores missing | held / incomplete |
|---|---|---|---|---|---|---|---|---|
| lag_local_tokens | 3401 | dtu | alignment_plus_selection CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | dtu | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | dtu | attended_alignment CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | dtu | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | dtu | selection_only SELECTION_CE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | fau | alignment_plus_selection CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | fau | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | fau | attended_alignment CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | fau | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3401 | fau | selection_only SELECTION_CE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3407 | dtu | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3407 | dtu | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3407 | fau | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3407 | fau | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3413 | dtu | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3413 | dtu | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3413 | fau | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| lag_local_tokens | 3413 | fau | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| dense_fm_policy | 3401 | dtu | alignment_plus_selection CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| dense_fm_policy | 3401 | dtu | alignment_plus_selection NCE | 9 | 0 | 0 | 0 | 1 |
| dense_fm_policy | 3401 | dtu | attended_alignment CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| dense_fm_policy | 3401 | dtu | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| dense_fm_policy | 3401 | dtu | selection_only SELECTION_CE | 10 | 0 | 0 | 0 | 0 |
| dense_fm_policy | 3401 | fau | alignment_plus_selection CS_SINGLE | 2 | 0 | 0 | 0 | 8 |
| dense_fm_policy | 3401 | fau | alignment_plus_selection NCE | 1 | 0 | 0 | 0 | 9 |
| dense_fm_policy | 3401 | fau | attended_alignment CS_SINGLE | 2 | 0 | 0 | 0 | 8 |
| dense_fm_policy | 3401 | fau | attended_alignment NCE | 2 | 0 | 0 | 0 | 8 |
| dense_fm_policy | 3401 | fau | selection_only SELECTION_CE | 2 | 0 | 0 | 0 | 8 |
| complement_policy | 3401 | dtu | alignment_plus_selection CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| complement_policy | 3401 | dtu | alignment_plus_selection NCE | 10 | 0 | 0 | 0 | 0 |
| complement_policy | 3401 | dtu | attended_alignment CS_SINGLE | 10 | 0 | 0 | 0 | 0 |
| complement_policy | 3401 | dtu | attended_alignment NCE | 10 | 0 | 0 | 0 | 0 |
| complement_policy | 3401 | dtu | selection_only SELECTION_CE | 10 | 0 | 0 | 0 | 0 |
| complement_policy | 3401 | fau | alignment_plus_selection CS_SINGLE | 0 | 0 | 0 | 0 | 10 |
| complement_policy | 3401 | fau | alignment_plus_selection NCE | 1 | 0 | 0 | 0 | 9 |
| complement_policy | 3401 | fau | attended_alignment CS_SINGLE | 1 | 0 | 0 | 0 | 9 |
| complement_policy | 3401 | fau | attended_alignment NCE | 2 | 0 | 0 | 0 | 8 |
| complement_policy | 3401 | fau | selection_only SELECTION_CE | 1 | 0 | 0 | 0 | 9 |

### 1.1 Class counts (unified, simultaneous intervals; one cell = arm × dataset × task/objective × window)

| family | arm | seed | I>0 | contains 0 | I<0 |
|---|---|---|---|---|---|
| AO-ANTISYM | complement_policy | 3401 | 0 | 26 | 1 |
| AO-ANTISYM | dense_fm_policy | 3401 | 9 | 19 | 2 |
| AO-ANTISYM | lag_local_tokens | 3401 | 0 | 29 | 1 |
| AO-ANTISYM | lag_local_tokens | 3407 | 0 | 12 | 0 |
| AO-ANTISYM | lag_local_tokens | 3413 | 0 | 12 | 0 |
| AO-ANTISYM | lag_local_tokens | mean | 0 | 12 | 0 |
| AO-FIXED | complement_policy | 3401 | 2 | 12 | 13 |
| AO-FIXED | dense_fm_policy | 3401 | 5 | 6 | 19 |
| AO-PAIRED-LEGACY | complement_policy | 3401 | 0 | 25 | 2 |
| AO-PAIRED-LEGACY | dense_fm_policy | 3401 | 9 | 19 | 2 |
| AO-PAIRED-LEGACY | lag_local_tokens | 3401 | 0 | 26 | 4 |
| AO-PAIRED-LEGACY | lag_local_tokens | 3407 | 0 | 11 | 1 |
| AO-PAIRED-LEGACY | lag_local_tokens | 3413 | 1 | 11 | 0 |
| AO-PAIRED-LEGACY | lag_local_tokens | mean | 0 | 9 | 3 |

Reproduction of the old fixed-order AT-INTEGRATOR from the new scores, original labels and bootstrap draws (lag arm; note §11.6):

- Seed 3401 against ADDENDUM_12 (`results/auditory_alignment_v3/d_lag/d_lag.json`, sha256 `736dedf02d61…`): 30 members compared, max |Δ| over est / se / CI / simultaneous 0.00e+00, class agreement 30/30, n agreement 30/30; native secondary 30 members, max |Δ| 0.00e+00.
- Seeds 3401 / 3407 / 3413 and the seed mean against R34_D_PANEL (`results/auditory_alignment_v3/aln34/d_multiseed/d_multiseed.json`, sha256 `3c88b114952d…`): 48 members compared, max |Δ| over est / se / CI / simultaneous 0.00e+00, class agreement 48/48, n agreement 48/48; native secondary 48 members, max |Δ| 0.00e+00.

### 1.2 Families (primary inclusion tier)

**AO-ANTISYM · complement_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.27)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | -0.005 [-0.010, -0.000] | hi: -0.000 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.002 | [-0.007, +0.004] | [-0.007, +0.004] | contains 0 | +0.002 [-0.005, +0.008] | hi: -0.005 (n=22); nh: +0.002 (n=22) |

**AO-ANTISYM · complement_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.37)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.004, +0.002] | [-0.005, +0.003] | contains 0 | +0.002 [-0.001, +0.004] | hi: -0.001 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.002 | [-0.008, +0.003] | [-0.008, +0.004] | contains 0 | -0.007 [-0.013, -0.001] | hi: -0.006 (n=22); nh: +0.001 (n=22) |

**AO-ANTISYM · complement_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.29)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.002, +0.001] | [-0.003, +0.001] | contains 0 | -0.001 [-0.004, +0.002] | hi: -0.001 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | +0.000 | [-0.005, +0.005] | [-0.006, +0.006] | contains 0 | -0.002 [-0.007, +0.004] | hi: +0.000 (n=22); nh: +0.000 (n=22) |

**AO-ANTISYM · complement_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.34)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.001, +0.003] | [-0.001, +0.004] | contains 0 | -0.000 [-0.002, +0.002] | hi: +0.001 (n=22); nh: +0.002 (n=22) |
| 20s | 44 | -0.002 | [-0.009, +0.005] | [-0.010, +0.006] | contains 0 | -0.003 [-0.008, +0.003] | hi: -0.003 (n=22); nh: -0.001 (n=22) |

**AO-ANTISYM · complement_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.41)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.002, +0.004] | [-0.003, +0.004] | contains 0 | -0.001 [-0.003, +0.000] | hi: -0.001 (n=22); nh: +0.003 (n=22) |
| 20s | 44 | -0.005 | [-0.009, -0.001] | [-0.010, +0.000] | contains 0 | -0.005 [-0.012, +0.002] | hi: -0.005 (n=22); nh: -0.005 (n=22) |

**AO-ANTISYM · complement_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 2.54)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | +0.011 | [+0.000, +0.021] | [-0.001, +0.023] | contains 0 | -0.003 [-0.015, +0.009] | ci: +0.003 (n=5); ha: +0.020 (n=6); th: n=3 |
| 20s | 14 | -0.010 | [-0.036, +0.015] | [-0.040, +0.020] | contains 0 | -0.010 [-0.025, +0.005] | ci: -0.017 (n=5); ha: +0.005 (n=6); th: n=3 |

**AO-ANTISYM · complement_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.68)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | -0.045 | [-0.076, -0.015] | [-0.082, -0.009] | I<0 | -0.004 [-0.015, +0.007] | ci: -0.024 (n=5); ha: -0.050 (n=6); th: n=3 |
| 20s | 14 | -0.024 | [-0.047, -0.002] | [-0.052, +0.003] | contains 0 | -0.000 [-0.011, +0.011] | ci: -0.023 (n=5); ha: -0.024 (n=6); th: n=3 |

**AO-ANTISYM · complement_policy · fau · attended_alignment · NCE · 3401** (critical value 2.59)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | -0.003 | [-0.012, +0.006] | [-0.014, +0.008] | contains 0 | -0.002 [-0.004, +0.000] | ci: -0.008 (n=5); ha: +0.003 (n=6); th: n=3 |
| 20s | 14 | +0.003 | [-0.009, +0.015] | [-0.011, +0.017] | contains 0 | +0.002 [-0.005, +0.009] | ci: -0.006 (n=5); ha: -0.002 (n=6); th: n=3 |

**AO-ANTISYM · complement_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.69)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | -0.014 | [-0.041, +0.012] | [-0.048, +0.019] | contains 0 | -0.027 [-0.033, -0.021] | ci: -0.024 (n=5); ha: +0.000 (n=6); th: n=3 |
| 20s | 14 | -0.012 | [-0.036, +0.012] | [-0.040, +0.015] | contains 0 | -0.018 [-0.031, -0.006] | ci: -0.011 (n=5); ha: -0.010 (n=6); th: n=3 |

**AO-ANTISYM · dense_fm_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.43)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.018 | [+0.001, +0.036] | [-0.002, +0.039] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.024 (n=22); nh: +0.013 (n=22) |
| 10s | 44 | +0.022 | [+0.001, +0.044] | [-0.004, +0.048] | contains 0 | -0.021 [-0.031, -0.010] | hi: +0.024 (n=22); nh: +0.021 (n=22) |
| 20s | 44 | +0.039 | [+0.009, +0.070] | [+0.003, +0.076] | I>0 | +0.015 [+0.004, +0.026] | hi: +0.032 (n=22); nh: +0.046 (n=22) |

**AO-ANTISYM · dense_fm_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.44)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.003 | [-0.005, +0.012] | [-0.007, +0.013] | contains 0 | -0.001 [-0.004, +0.002] | hi: +0.002 (n=22); nh: +0.005 (n=22) |
| 20s | 44 | -0.003 | [-0.013, +0.008] | [-0.014, +0.009] | contains 0 | -0.001 [-0.014, +0.012] | hi: -0.000 (n=22); nh: -0.005 (n=22) |

**AO-ANTISYM · dense_fm_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.49)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.022 | [+0.008, +0.037] | [+0.005, +0.040] | I>0 | +0.000 [+0.000, +0.000] | hi: +0.030 (n=22); nh: +0.015 (n=22) |
| 10s | 44 | +0.022 | [+0.001, +0.044] | [-0.004, +0.048] | contains 0 | -0.020 [-0.028, -0.012] | hi: +0.027 (n=22); nh: +0.017 (n=22) |
| 20s | 44 | +0.053 | [+0.025, +0.081] | [+0.019, +0.088] | I>0 | +0.007 [-0.005, +0.019] | hi: +0.051 (n=22); nh: +0.056 (n=22) |

**AO-ANTISYM · dense_fm_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.31)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.006, +0.003] | [-0.007, +0.004] | contains 0 | +0.001 [-0.002, +0.004] | hi: -0.002 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.001 | [-0.010, +0.008] | [-0.011, +0.009] | contains 0 | -0.008 [-0.017, +0.001] | hi: -0.014 (n=22); nh: +0.012 (n=22) |

**AO-ANTISYM · dense_fm_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.53)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.018 | [+0.007, +0.029] | [+0.005, +0.032] | I>0 | +0.000 [+0.000, +0.000] | hi: +0.024 (n=22); nh: +0.013 (n=22) |
| 10s | 44 | +0.011 | [-0.004, +0.027] | [-0.008, +0.031] | contains 0 | -0.001 [-0.004, +0.002] | hi: +0.026 (n=22); nh: -0.003 (n=22) |
| 20s | 44 | +0.031 | [+0.011, +0.051] | [+0.006, +0.056] | I>0 | -0.004 [-0.012, +0.005] | hi: +0.026 (n=22); nh: +0.036 (n=22) |

**AO-ANTISYM · dense_fm_policy · fau · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.62)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | +0.016 | [+0.005, +0.026] | [+0.003, +0.028] | I>0 | -0.025 [-0.034, -0.017] | ci: +0.022 (n=5); ha: +0.009 (n=6); th: n=3 |
| 20s | 14 | -0.075 | [-0.100, -0.051] | [-0.105, -0.046] | I<0 | -0.045 [-0.063, -0.026] | ci: -0.071 (n=5); ha: -0.091 (n=6); th: n=3 |

**AO-ANTISYM · dense_fm_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 2.62)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | -0.035 | [-0.045, -0.025] | [-0.047, -0.023] | I<0 | +0.005 [-0.017, +0.027] | ci: -0.029 (n=5); ha: -0.041 (n=6); th: n=3 |
| 20s | 14 | +0.002 | [-0.010, +0.015] | [-0.013, +0.017] | contains 0 | -0.025 [-0.051, +0.001] | ci: +0.000 (n=5); ha: +0.005 (n=6); th: n=3 |

**AO-ANTISYM · dense_fm_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 3.20)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.013 | [-0.030, +0.003] | [-0.033, +0.007] | contains 0 | +0.000 [+0.000, +0.000] | ci: -0.010 (n=5); ha: -0.018 (n=6); th: n=3 |
| 10s | 14 | -0.020 | [-0.043, +0.003] | [-0.054, +0.015] | contains 0 | -0.070 [-0.082, -0.059] | ci: +0.011 (n=5); ha: -0.045 (n=6); th: n=3 |
| 20s | 14 | -0.021 | [-0.071, +0.030] | [-0.094, +0.053] | contains 0 | -0.077 [-0.096, -0.058] | ci: -0.035 (n=5); ha: -0.029 (n=6); th: n=3 |

**AO-ANTISYM · dense_fm_policy · fau · attended_alignment · NCE · 3401** (critical value 2.76)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | +0.005 | [-0.009, +0.018] | [-0.012, +0.022] | contains 0 | -0.004 [-0.016, +0.008] | ci: -0.004 (n=5); ha: +0.000 (n=6); th: n=3 |
| 20s | 14 | +0.027 | [+0.015, +0.039] | [+0.014, +0.040] | I>0 | -0.014 [-0.029, +0.001] | ci: +0.029 (n=5); ha: +0.029 (n=6); th: n=3 |

**AO-ANTISYM · dense_fm_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.86)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.017 | [+0.006, +0.028] | [+0.002, +0.032] | I>0 | +0.000 [+0.000, +0.000] | ci: +0.016 (n=5); ha: +0.021 (n=6); th: n=3 |
| 10s | 14 | +0.017 | [-0.004, +0.038] | [-0.008, +0.042] | contains 0 | +0.002 [-0.007, +0.010] | ci: +0.018 (n=5); ha: +0.015 (n=6); th: n=3 |
| 20s | 14 | +0.040 | [+0.013, +0.067] | [+0.005, +0.076] | I>0 | +0.013 [-0.002, +0.028] | ci: +0.026 (n=5); ha: +0.044 (n=6); th: n=3 |

**AO-ANTISYM · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.38)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | -0.003 [-0.007, +0.000] | hi: +0.001 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.005 | [-0.012, +0.003] | [-0.013, +0.004] | contains 0 | -0.004 [-0.010, +0.001] | hi: +0.002 (n=22); nh: -0.011 (n=22) |

**AO-ANTISYM · dtu · alignment_plus_selection · NCE · mean** (critical value 2.30)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | hi: -0.001 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.004 | [-0.007, -0.000] | [-0.007, +0.000] | contains 0 | -0.005 [-0.008, -0.001] | hi: -0.002 (n=22); nh: -0.005 (n=22) |

**AO-ANTISYM · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.35)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | +0.000 [-0.002, +0.002] | hi: -0.001 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.003 | [-0.010, +0.004] | [-0.011, +0.005] | contains 0 | -0.002 [-0.008, +0.004] | hi: +0.000 (n=22); nh: -0.007 (n=22) |

**AO-ANTISYM · dtu · alignment_plus_selection · NCE · 3407** (critical value 2.36)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.002 | [-0.004, +0.000] | [-0.004, +0.001] | contains 0 | -0.000 [-0.004, +0.003] | hi: -0.003 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.004 | [-0.009, +0.001] | [-0.010, +0.002] | contains 0 | -0.005 [-0.013, +0.002] | hi: -0.001 (n=22); nh: -0.007 (n=22) |

**AO-ANTISYM · dtu · alignment_plus_selection · NCE · 3413** (critical value 2.28)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.000 | [-0.002, +0.002] | [-0.003, +0.002] | contains 0 | +0.001 [-0.001, +0.002] | hi: -0.000 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.004 | [-0.009, +0.001] | [-0.009, +0.002] | contains 0 | -0.006 [-0.013, +0.000] | hi: -0.006 (n=22); nh: -0.002 (n=22) |

**AO-ANTISYM · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.34)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.002 | [-0.004, +0.000] | [-0.005, +0.001] | contains 0 | +0.000 [-0.005, +0.005] | hi: -0.001 (n=22); nh: -0.003 (n=22) |
| 20s | 44 | +0.001 | [-0.005, +0.006] | [-0.006, +0.007] | contains 0 | +0.004 [-0.001, +0.008] | hi: -0.003 (n=22); nh: +0.004 (n=22) |

**AO-ANTISYM · dtu · attended_alignment · NCE · mean** (critical value 2.32)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.001 [-0.002, +0.001] | hi: -0.000 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.000 | [-0.004, +0.003] | [-0.004, +0.004] | contains 0 | -0.003 [-0.007, +0.001] | hi: -0.001 (n=22); nh: +0.000 (n=22) |

**AO-ANTISYM · dtu · attended_alignment · NCE · 3401** (critical value 2.29)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.003, +0.002] | [-0.004, +0.002] | contains 0 | +0.000 [-0.002, +0.002] | hi: +0.001 (n=22); nh: -0.002 (n=22) |
| 20s | 44 | -0.003 | [-0.010, +0.003] | [-0.011, +0.005] | contains 0 | -0.003 [-0.010, +0.004] | hi: -0.005 (n=22); nh: -0.001 (n=22) |

**AO-ANTISYM · dtu · attended_alignment · NCE · 3407** (critical value 2.31)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.000 | [-0.001, +0.002] | [-0.002, +0.002] | contains 0 | -0.001 [-0.002, +0.001] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 20s | 44 | -0.001 | [-0.004, +0.003] | [-0.005, +0.003] | contains 0 | -0.005 [-0.010, -0.000] | hi: -0.001 (n=22); nh: -0.001 (n=22) |

**AO-ANTISYM · dtu · attended_alignment · NCE · 3413** (critical value 2.34)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.002 | [-0.004, +0.000] | [-0.004, +0.001] | contains 0 | -0.002 [-0.004, +0.001] | hi: -0.001 (n=22); nh: -0.002 (n=22) |
| 20s | 44 | +0.003 | [-0.003, +0.009] | [-0.004, +0.010] | contains 0 | -0.001 [-0.006, +0.005] | hi: +0.003 (n=22); nh: +0.003 (n=22) |

**AO-ANTISYM · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.29)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.001, +0.003] | [-0.001, +0.003] | contains 0 | +0.000 [-0.002, +0.003] | hi: -0.001 (n=22); nh: +0.002 (n=22) |
| 20s | 44 | -0.004 | [-0.010, +0.002] | [-0.011, +0.002] | contains 0 | -0.003 [-0.007, +0.002] | hi: -0.001 (n=22); nh: -0.008 (n=22) |

**AO-ANTISYM · fau · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.25)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.001 | [-0.002, +0.004] | [-0.002, +0.004] | contains 0 | -0.011 [-0.018, -0.004] | ci: +0.001 (n=24); ha: +0.000 (n=29); th: +0.004 (n=14) |
| 20s | 67 | -0.001 | [-0.005, +0.003] | [-0.005, +0.004] | contains 0 | -0.009 [-0.020, +0.002] | ci: +0.000 (n=24); ha: -0.003 (n=29); th: +0.001 (n=14) |

**AO-ANTISYM · fau · alignment_plus_selection · NCE · mean** (critical value 2.32)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.001 | [-0.001, +0.002] | [-0.002, +0.003] | contains 0 | +0.000 [-0.001, +0.002] | ci: +0.001 (n=24); ha: -0.000 (n=29); th: +0.002 (n=14) |
| 20s | 67 | -0.001 | [-0.003, +0.002] | [-0.004, +0.002] | contains 0 | +0.002 [-0.001, +0.004] | ci: -0.001 (n=24); ha: -0.000 (n=29); th: -0.001 (n=14) |

**AO-ANTISYM · fau · alignment_plus_selection · NCE · 3401** (critical value 2.29)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.000 | [-0.002, +0.003] | [-0.003, +0.004] | contains 0 | +0.001 [-0.001, +0.004] | ci: +0.003 (n=24); ha: -0.003 (n=29); th: +0.003 (n=14) |
| 20s | 67 | -0.001 | [-0.005, +0.004] | [-0.006, +0.005] | contains 0 | -0.001 [-0.006, +0.005] | ci: -0.005 (n=24); ha: +0.002 (n=29); th: +0.002 (n=14) |

**AO-ANTISYM · fau · alignment_plus_selection · NCE · 3407** (critical value 2.25)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.002 | [-0.001, +0.005] | [-0.002, +0.005] | contains 0 | +0.001 [-0.002, +0.003] | ci: +0.001 (n=24); ha: +0.002 (n=29); th: +0.004 (n=14) |
| 20s | 67 | +0.000 | [-0.005, +0.005] | [-0.005, +0.006] | contains 0 | +0.006 [+0.003, +0.010] | ci: +0.004 (n=24); ha: -0.004 (n=29); th: +0.001 (n=14) |

**AO-ANTISYM · fau · alignment_plus_selection · NCE · 3413** (critical value 2.27)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.001 | [-0.004, +0.003] | [-0.005, +0.003] | contains 0 | -0.001 [-0.004, +0.003] | ci: -0.001 (n=24); ha: +0.001 (n=29); th: -0.002 (n=14) |
| 20s | 67 | -0.002 | [-0.006, +0.002] | [-0.006, +0.003] | contains 0 | -0.001 [-0.005, +0.003] | ci: -0.003 (n=24); ha: +0.001 (n=29); th: -0.006 (n=14) |

**AO-ANTISYM · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.30)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.001 | [-0.001, +0.004] | [-0.002, +0.004] | contains 0 | -0.008 [-0.014, -0.001] | ci: -0.000 (n=24); ha: +0.004 (n=29); th: -0.001 (n=14) |
| 20s | 67 | +0.001 | [-0.004, +0.005] | [-0.005, +0.006] | contains 0 | -0.003 [-0.012, +0.006] | ci: +0.005 (n=24); ha: -0.003 (n=29); th: +0.002 (n=14) |

**AO-ANTISYM · fau · attended_alignment · NCE · mean** (critical value 2.32)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | -0.001 [-0.002, +0.000] | ci: +0.002 (n=24); ha: -0.002 (n=29); th: -0.000 (n=14) |
| 20s | 67 | -0.001 | [-0.004, +0.001] | [-0.004, +0.001] | contains 0 | +0.000 [-0.001, +0.002] | ci: -0.001 (n=24); ha: -0.003 (n=29); th: +0.001 (n=14) |

**AO-ANTISYM · fau · attended_alignment · NCE · 3401** (critical value 2.33)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.004 | [-0.006, -0.001] | [-0.007, -0.000] | I<0 | -0.001 [-0.004, +0.001] | ci: -0.001 (n=24); ha: -0.005 (n=29); th: -0.005 (n=14) |
| 20s | 67 | -0.003 | [-0.007, +0.001] | [-0.008, +0.002] | contains 0 | +0.003 [-0.000, +0.006] | ci: -0.001 (n=24); ha: -0.004 (n=29); th: -0.002 (n=14) |

**AO-ANTISYM · fau · attended_alignment · NCE · 3407** (critical value 2.25)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.001 | [-0.004, +0.003] | [-0.005, +0.003] | contains 0 | -0.002 [-0.004, +0.000] | ci: -0.002 (n=24); ha: -0.003 (n=29); th: +0.005 (n=14) |
| 20s | 67 | -0.000 | [-0.004, +0.004] | [-0.005, +0.005] | contains 0 | -0.002 [-0.005, +0.001] | ci: +0.003 (n=24); ha: -0.000 (n=29); th: -0.005 (n=14) |

**AO-ANTISYM · fau · attended_alignment · NCE · 3413** (critical value 2.28)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.004 | [+0.000, +0.007] | [-0.000, +0.008] | contains 0 | +0.000 [-0.002, +0.003] | ci: +0.009 (n=24); ha: +0.002 (n=29); th: -0.000 (n=14) |
| 20s | 67 | -0.002 | [-0.006, +0.003] | [-0.007, +0.004] | contains 0 | -0.001 [-0.004, +0.002] | ci: -0.004 (n=24); ha: -0.005 (n=29); th: +0.010 (n=14) |

**AO-ANTISYM · fau · selection_only · SELECTION_CE · 3401** (critical value 2.22)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [+0.000, +0.000] | [+0.000, +0.000] | contains 0 | +0.000 [+0.000, +0.000] | ci: +0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.000 | [-0.003, +0.003] | [-0.004, +0.004] | contains 0 | -0.001 [-0.005, +0.003] | ci: +0.004 (n=24); ha: -0.002 (n=29); th: -0.003 (n=14) |
| 20s | 67 | -0.001 | [-0.006, +0.003] | [-0.007, +0.004] | contains 0 | -0.001 [-0.007, +0.005] | ci: +0.001 (n=24); ha: -0.003 (n=29); th: -0.000 (n=14) |

**AO-FIXED · complement_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.50)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.005 | [-0.006, -0.003] | [-0.007, -0.002] | I<0 | +0.271 [+0.253, +0.289] | hi: -0.005 (n=22); nh: -0.004 (n=22) |
| 10s | 44 | +0.005 | [+0.002, +0.009] | [+0.001, +0.010] | I>0 | +0.229 [+0.210, +0.248] | hi: +0.008 (n=22); nh: +0.003 (n=22) |
| 20s | 44 | -0.010 | [-0.019, -0.001] | [-0.021, +0.002] | contains 0 | -0.844 [-0.868, -0.820] | hi: -0.009 (n=22); nh: -0.010 (n=22) |

**AO-FIXED · complement_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.59)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.006 | [-0.008, -0.004] | [-0.008, -0.003] | I<0 | +0.003 [+0.001, +0.005] | hi: -0.006 (n=22); nh: -0.006 (n=22) |
| 10s | 44 | +0.002 | [-0.002, +0.007] | [-0.003, +0.008] | contains 0 | +0.032 [+0.023, +0.041] | hi: +0.005 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.022 | [-0.031, -0.013] | [-0.033, -0.011] | I<0 | -0.205 [-0.227, -0.183] | hi: -0.026 (n=22); nh: -0.018 (n=22) |

**AO-FIXED · complement_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.53)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.007 | [-0.009, -0.005] | [-0.010, -0.005] | I<0 | +0.269 [+0.251, +0.288] | hi: -0.006 (n=22); nh: -0.008 (n=22) |
| 10s | 44 | +0.002 | [-0.001, +0.005] | [-0.002, +0.006] | contains 0 | +0.239 [+0.218, +0.261] | hi: +0.003 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.011 | [-0.020, -0.002] | [-0.021, -0.000] | I<0 | -0.833 [-0.855, -0.811] | hi: -0.016 (n=22); nh: -0.006 (n=22) |

**AO-FIXED · complement_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.57)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.005 | [-0.007, -0.003] | [-0.007, -0.003] | I<0 | +0.002 [+0.001, +0.004] | hi: -0.004 (n=22); nh: -0.006 (n=22) |
| 10s | 44 | +0.004 | [+0.001, +0.007] | [-0.000, +0.008] | contains 0 | +0.044 [+0.032, +0.056] | hi: +0.003 (n=22); nh: +0.005 (n=22) |
| 20s | 44 | -0.013 | [-0.022, -0.004] | [-0.024, -0.001] | I<0 | -0.339 [-0.365, -0.312] | hi: -0.009 (n=22); nh: -0.016 (n=22) |

**AO-FIXED · complement_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.47)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.007 | [-0.008, -0.005] | [-0.008, -0.005] | I<0 | -0.000 [-0.002, +0.001] | hi: -0.006 (n=22); nh: -0.008 (n=22) |
| 10s | 44 | +0.007 | [+0.003, +0.011] | [+0.002, +0.011] | I>0 | +0.010 [+0.006, +0.014] | hi: +0.005 (n=22); nh: +0.009 (n=22) |
| 20s | 44 | -0.014 | [-0.022, -0.005] | [-0.024, -0.004] | I<0 | -0.025 [-0.032, -0.017] | hi: -0.014 (n=22); nh: -0.014 (n=22) |

**AO-FIXED · complement_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 1000.00)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.000 | [-0.470, +0.469] | [-0.470, +0.469] | contains 0 | +0.013 [+0.006, +0.020] | ci: +0.000 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | -0.006 | [-0.017, +0.006] | [-5.057, +5.045] | contains 0 | -0.007 [-0.019, +0.006] | ci: -0.008 (n=5); ha: +0.002 (n=6); th: n=3 |
| 20s | 14 | -0.002 | [-0.031, +0.027] | [-11.393, +11.389] | contains 0 | -0.047 [-0.081, -0.013] | ci: -0.006 (n=5); ha: +0.000 (n=6); th: n=3 |

**AO-FIXED · complement_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 3.46)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.002 | [-0.005, +0.001] | [-0.006, +0.002] | contains 0 | -0.299 [-0.318, -0.279] | ci: -0.004 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | -0.092 | [-0.125, -0.059] | [-0.143, -0.040] | I<0 | -0.654 [-0.705, -0.604] | ci: -0.078 (n=5); ha: -0.090 (n=6); th: n=3 |
| 20s | 14 | +0.014 | [-0.020, +0.049] | [-0.039, +0.068] | contains 0 | -0.741 [-0.803, -0.678] | ci: +0.046 (n=5); ha: -0.014 (n=6); th: n=3 |

**AO-FIXED · complement_policy · fau · attended_alignment · NCE · 3401** (critical value 2.81)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.005 | [-0.007, -0.003] | [-0.007, -0.003] | I<0 | +0.013 [+0.008, +0.017] | ci: -0.006 (n=5); ha: -0.003 (n=6); th: n=3 |
| 10s | 14 | -0.022 | [-0.032, -0.013] | [-0.034, -0.011] | I<0 | +0.041 [+0.030, +0.053] | ci: -0.029 (n=5); ha: -0.019 (n=6); th: n=3 |
| 20s | 14 | -0.008 | [-0.031, +0.016] | [-0.038, +0.023] | contains 0 | -0.051 [-0.068, -0.033] | ci: -0.009 (n=5); ha: -0.017 (n=6); th: n=3 |

**AO-FIXED · complement_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.89)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.003 | [+0.000, +0.006] | [-0.000, +0.007] | contains 0 | +0.008 [-0.000, +0.016] | ci: +0.004 (n=5); ha: +0.003 (n=6); th: n=3 |
| 10s | 14 | -0.049 | [-0.072, -0.026] | [-0.080, -0.018] | I<0 | -0.084 [-0.090, -0.078] | ci: -0.054 (n=5); ha: -0.047 (n=6); th: n=3 |
| 20s | 14 | +0.008 | [-0.022, +0.038] | [-0.032, +0.048] | contains 0 | -0.208 [-0.218, -0.198] | ci: +0.040 (n=5); ha: -0.005 (n=6); th: n=3 |

**AO-FIXED · dense_fm_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.48)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.097 | [-0.122, -0.072] | [-0.127, -0.068] | I<0 | +0.432 [+0.425, +0.440] | hi: -0.094 (n=22); nh: -0.100 (n=22) |
| 10s | 44 | +0.120 | [+0.095, +0.145] | [+0.089, +0.151] | I>0 | +0.388 [+0.378, +0.397] | hi: +0.126 (n=22); nh: +0.114 (n=22) |
| 20s | 44 | -0.037 | [-0.088, +0.015] | [-0.098, +0.024] | contains 0 | -0.631 [-0.641, -0.620] | hi: -0.034 (n=22); nh: -0.039 (n=22) |

**AO-FIXED · dense_fm_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.88)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.011 | [-0.016, -0.006] | [-0.017, -0.004] | I<0 | +0.005 [+0.001, +0.009] | hi: -0.011 (n=22); nh: -0.010 (n=22) |
| 10s | 44 | +0.024 | [+0.011, +0.037] | [+0.007, +0.041] | I>0 | +0.014 [+0.005, +0.023] | hi: +0.025 (n=22); nh: +0.023 (n=22) |
| 20s | 44 | -0.012 | [-0.031, +0.007] | [-0.038, +0.015] | contains 0 | -0.092 [-0.111, -0.073] | hi: -0.015 (n=22); nh: -0.009 (n=22) |

**AO-FIXED · dense_fm_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.49)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.243 | [-0.294, -0.191] | [-0.306, -0.180] | I<0 | +0.424 [+0.418, +0.430] | hi: -0.233 (n=22); nh: -0.252 (n=22) |
| 10s | 44 | +0.173 | [+0.138, +0.208] | [+0.129, +0.217] | I>0 | +0.387 [+0.377, +0.398] | hi: +0.187 (n=22); nh: +0.159 (n=22) |
| 20s | 44 | -0.047 | [-0.091, -0.003] | [-0.102, +0.008] | contains 0 | -0.639 [-0.651, -0.626] | hi: -0.041 (n=22); nh: -0.053 (n=22) |

**AO-FIXED · dense_fm_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.58)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.015 | [-0.022, -0.007] | [-0.024, -0.006] | I<0 | +0.005 [+0.001, +0.009] | hi: -0.015 (n=22); nh: -0.014 (n=22) |
| 10s | 44 | +0.019 | [+0.010, +0.028] | [+0.007, +0.030] | I>0 | +0.022 [+0.013, +0.031] | hi: +0.023 (n=22); nh: +0.015 (n=22) |
| 20s | 44 | -0.027 | [-0.043, -0.010] | [-0.047, -0.006] | I<0 | -0.109 [-0.127, -0.090] | hi: -0.034 (n=22); nh: -0.019 (n=22) |

**AO-FIXED · dense_fm_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.38)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.177 | [-0.207, -0.147] | [-0.213, -0.142] | I<0 | +0.003 [+0.001, +0.004] | hi: -0.176 (n=22); nh: -0.178 (n=22) |
| 10s | 44 | +0.134 | [+0.093, +0.175] | [+0.086, +0.183] | I>0 | +0.011 [+0.007, +0.016] | hi: +0.145 (n=22); nh: +0.123 (n=22) |
| 20s | 44 | -0.109 | [-0.163, -0.054] | [-0.173, -0.044] | I<0 | -0.068 [-0.080, -0.056] | hi: -0.099 (n=22); nh: -0.119 (n=22) |

**AO-FIXED · dense_fm_policy · fau · alignment_plus_selection · CS_SINGLE · 3401** (critical value 3.12)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.035 | [-0.040, -0.030] | [-0.042, -0.028] | I<0 | -0.047 [-0.052, -0.041] | ci: -0.029 (n=5); ha: -0.038 (n=6); th: n=3 |
| 10s | 14 | -0.198 | [-0.211, -0.186] | [-0.216, -0.181] | I<0 | -0.041 [-0.053, -0.028] | ci: -0.184 (n=5); ha: -0.208 (n=6); th: n=3 |
| 20s | 14 | -0.141 | [-0.162, -0.119] | [-0.170, -0.112] | I<0 | -0.646 [-0.663, -0.629] | ci: -0.120 (n=5); ha: -0.156 (n=6); th: n=3 |

**AO-FIXED · dense_fm_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 3.00)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.017 | [-0.024, -0.011] | [-0.025, -0.009] | I<0 | +0.001 [-1.019, +1.021] | ci: -0.021 (n=5); ha: -0.017 (n=6); th: n=3 |
| 10s | 14 | -0.083 | [-0.091, -0.075] | [-0.092, -0.073] | I<0 | +0.034 [+0.016, +0.052] | ci: -0.078 (n=5); ha: -0.087 (n=6); th: n=3 |
| 20s | 14 | -0.019 | [-0.032, -0.006] | [-0.036, -0.001] | I<0 | -0.029 [-0.058, -0.001] | ci: -0.012 (n=5); ha: -0.025 (n=6); th: n=3 |

**AO-FIXED · dense_fm_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.81)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.074 | [-0.090, -0.058] | [-0.094, -0.053] | I<0 | -0.017 [-0.025, -0.008] | ci: -0.079 (n=5); ha: -0.076 (n=6); th: n=3 |
| 10s | 14 | -0.223 | [-0.243, -0.204] | [-0.248, -0.198] | I<0 | -0.008 [-0.019, +0.003] | ci: -0.211 (n=5); ha: -0.239 (n=6); th: n=3 |
| 20s | 14 | -0.225 | [-0.272, -0.177] | [-0.287, -0.163] | I<0 | -0.590 [-0.604, -0.577] | ci: -0.218 (n=5); ha: -0.257 (n=6); th: n=3 |

**AO-FIXED · dense_fm_policy · fau · attended_alignment · NCE · 3401** (critical value 2.96)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.010 | [-0.013, -0.007] | [-0.014, -0.006] | I<0 | +0.010 [+0.006, +0.014] | ci: -0.010 (n=5); ha: -0.011 (n=6); th: n=3 |
| 10s | 14 | -0.011 | [-0.026, +0.005] | [-0.032, +0.010] | contains 0 | +0.003 [-0.004, +0.009] | ci: -0.018 (n=5); ha: -0.020 (n=6); th: n=3 |
| 20s | 14 | +0.009 | [-0.003, +0.021] | [-0.007, +0.026] | contains 0 | -0.050 [-0.066, -0.033] | ci: +0.012 (n=5); ha: +0.007 (n=6); th: n=3 |

**AO-FIXED · dense_fm_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.96)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.067 | [-0.082, -0.052] | [-0.086, -0.048] | I<0 | +0.007 [+0.004, +0.010] | ci: -0.063 (n=5); ha: -0.065 (n=6); th: n=3 |
| 10s | 14 | -0.006 | [-0.024, +0.011] | [-0.030, +0.017] | contains 0 | +0.017 [+0.010, +0.025] | ci: -0.010 (n=5); ha: -0.005 (n=6); th: n=3 |
| 20s | 14 | -0.070 | [-0.095, -0.046] | [-0.101, -0.039] | I<0 | +0.014 [+0.001, +0.027] | ci: -0.090 (n=5); ha: -0.061 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · complement_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.51)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.001 | [-0.000, +0.002] | [-0.000, +0.002] | contains 0 | -0.143 [-0.168, -0.118] | hi: +0.001 (n=22); nh: +0.001 (n=22) |
| 10s | 44 | +0.001 | [-0.002, +0.003] | [-0.002, +0.003] | contains 0 | -0.271 [-0.290, -0.252] | hi: +0.001 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.007 | [-0.016, +0.002] | [-0.018, +0.005] | contains 0 | -0.344 [-0.368, -0.320] | hi: -0.006 (n=22); nh: -0.007 (n=22) |

**AO-PAIRED-LEGACY · complement_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.50)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.001 | [-0.001, +0.000] | [-0.002, +0.000] | contains 0 | +0.001 [-0.001, +0.002] | hi: -0.001 (n=22); nh: -0.000 (n=22) |
| 10s | 44 | -0.000 | [-0.003, +0.003] | [-0.004, +0.004] | contains 0 | -0.003 [-0.007, +0.001] | hi: -0.000 (n=22); nh: -0.000 (n=22) |
| 20s | 44 | -0.015 | [-0.023, -0.007] | [-0.024, -0.005] | I<0 | -0.061 [-0.070, -0.051] | hi: -0.018 (n=22); nh: -0.011 (n=22) |

**AO-PAIRED-LEGACY · complement_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.60)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.138 [-0.159, -0.117] | hi: -0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.002 | [-0.004, +0.000] | [-0.004, +0.001] | contains 0 | -0.261 [-0.282, -0.239] | hi: -0.001 (n=22); nh: -0.003 (n=22) |
| 20s | 44 | -0.002 | [-0.010, +0.005] | [-0.012, +0.007] | contains 0 | -0.333 [-0.355, -0.311] | hi: -0.007 (n=22); nh: +0.002 (n=22) |

**AO-PAIRED-LEGACY · complement_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.47)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 [-0.001, +0.000] | hi: -0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.002, +0.003] | [-0.002, +0.004] | contains 0 | -0.006 [-0.011, -0.001] | hi: -0.000 (n=22); nh: +0.002 (n=22) |
| 20s | 44 | -0.008 | [-0.017, +0.001] | [-0.019, +0.003] | contains 0 | -0.114 [-0.130, -0.099] | hi: -0.003 (n=22); nh: -0.013 (n=22) |

**AO-PAIRED-LEGACY · complement_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.53)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.001 [-0.001, +0.000] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.003, +0.002] | [-0.004, +0.003] | contains 0 | -0.001 [-0.003, +0.001] | hi: -0.001 (n=22); nh: +0.000 (n=22) |
| 20s | 44 | -0.009 | [-0.017, -0.001] | [-0.019, +0.001] | contains 0 | -0.006 [-0.013, +0.001] | hi: -0.008 (n=22); nh: -0.009 (n=22) |

**AO-PAIRED-LEGACY · complement_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 3.12)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 [-0.002, +0.004] | ci: +0.001 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | +0.006 | [-0.004, +0.016] | [-0.008, +0.020] | contains 0 | +0.000 [-0.004, +0.004] | ci: +0.003 (n=5); ha: +0.016 (n=6); th: n=3 |
| 20s | 14 | -0.006 | [-0.039, +0.026] | [-0.042, +0.030] | contains 0 | +0.015 [-0.014, +0.044] | ci: -0.009 (n=5); ha: -0.002 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · complement_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.94)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [-0.001, +0.002] | [-0.002, +0.002] | contains 0 | -0.024 [-0.042, -0.006] | ci: -0.001 (n=5); ha: +0.000 (n=6); th: n=3 |
| 10s | 14 | -0.050 | [-0.079, -0.021] | [-0.090, -0.011] | I<0 | -0.154 [-0.206, -0.103] | ci: -0.030 (n=5); ha: -0.053 (n=6); th: n=3 |
| 20s | 14 | -0.016 | [-0.044, +0.012] | [-0.054, +0.021] | contains 0 | -0.241 [-0.306, -0.175] | ci: +0.011 (n=5); ha: -0.038 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · complement_policy · fau · attended_alignment · NCE · 3401** (critical value 2.75)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.001 [-0.004, +0.002] | ci: -0.000 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | -0.002 | [-0.008, +0.003] | [-0.009, +0.005] | contains 0 | -0.005 [-0.015, +0.005] | ci: -0.006 (n=5); ha: +0.001 (n=6); th: n=3 |
| 20s | 14 | +0.005 | [-0.016, +0.025] | [-0.021, +0.031] | contains 0 | -0.008 [-0.026, +0.010] | ci: +0.009 (n=5); ha: -0.007 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · complement_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.90)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.001 | [-0.001, +0.002] | [-0.002, +0.003] | contains 0 | +0.001 [-0.002, +0.004] | ci: +0.001 (n=5); ha: +0.001 (n=6); th: n=3 |
| 10s | 14 | -0.012 | [-0.038, +0.015] | [-0.046, +0.023] | contains 0 | -0.060 [-0.068, -0.052] | ci: -0.022 (n=5); ha: -0.005 (n=6); th: n=3 |
| 20s | 14 | -0.005 | [-0.030, +0.019] | [-0.037, +0.027] | contains 0 | -0.091 [-0.103, -0.079] | ci: +0.017 (n=5); ha: -0.012 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dense_fm_policy · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.40)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.019 | [+0.004, +0.034] | [+0.001, +0.037] | I>0 | -0.068 [-0.075, -0.060] | hi: +0.025 (n=22); nh: +0.013 (n=22) |
| 10s | 44 | +0.030 | [+0.009, +0.050] | [+0.005, +0.054] | I>0 | -0.112 [-0.122, -0.103] | hi: +0.033 (n=22); nh: +0.026 (n=22) |
| 20s | 44 | +0.046 | [+0.018, +0.075] | [+0.012, +0.080] | I>0 | -0.131 [-0.140, -0.121] | hi: +0.044 (n=22); nh: +0.048 (n=22) |

**AO-PAIRED-LEGACY · dense_fm_policy · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.74)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [-0.002, +0.002] | [-0.002, +0.003] | contains 0 | +0.001 [-0.000, +0.003] | hi: -0.000 (n=22); nh: +0.001 (n=22) |
| 10s | 44 | +0.005 | [-0.004, +0.015] | [-0.006, +0.016] | contains 0 | -0.001 [-0.005, +0.002] | hi: +0.006 (n=22); nh: +0.005 (n=22) |
| 20s | 44 | -0.002 | [-0.013, +0.010] | [-0.018, +0.015] | contains 0 | -0.009 [-0.021, +0.004] | hi: -0.002 (n=22); nh: -0.001 (n=22) |

**AO-PAIRED-LEGACY · dense_fm_policy · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.42)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.021 | [+0.008, +0.034] | [+0.006, +0.036] | I>0 | -0.076 [-0.082, -0.070] | hi: +0.032 (n=22); nh: +0.010 (n=22) |
| 10s | 44 | +0.021 | [+0.002, +0.039] | [-0.002, +0.043] | contains 0 | -0.113 [-0.123, -0.102] | hi: +0.032 (n=22); nh: +0.009 (n=22) |
| 20s | 44 | +0.050 | [+0.026, +0.075] | [+0.020, +0.081] | I>0 | -0.139 [-0.152, -0.125] | hi: +0.056 (n=22); nh: +0.045 (n=22) |

**AO-PAIRED-LEGACY · dense_fm_policy · dtu · attended_alignment · NCE · 3401** (critical value 2.48)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.001 | [-0.001, +0.002] | [-0.001, +0.002] | contains 0 | +0.000 [-0.001, +0.002] | hi: -0.000 (n=22); nh: +0.001 (n=22) |
| 10s | 44 | -0.000 | [-0.006, +0.005] | [-0.007, +0.006] | contains 0 | -0.001 [-0.005, +0.003] | hi: +0.001 (n=22); nh: -0.002 (n=22) |
| 20s | 44 | -0.008 | [-0.018, +0.003] | [-0.021, +0.005] | contains 0 | -0.009 [-0.020, +0.002] | hi: -0.014 (n=22); nh: -0.001 (n=22) |

**AO-PAIRED-LEGACY · dense_fm_policy · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.46)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.022 | [+0.013, +0.031] | [+0.011, +0.033] | I>0 | -0.000 [-0.001, +0.000] | hi: +0.022 (n=22); nh: +0.022 (n=22) |
| 10s | 44 | +0.011 | [-0.002, +0.025] | [-0.005, +0.028] | contains 0 | -0.001 [-0.003, +0.002] | hi: +0.024 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | +0.028 | [+0.008, +0.047] | [+0.003, +0.052] | I>0 | -0.005 [-0.014, +0.003] | hi: +0.030 (n=22); nh: +0.025 (n=22) |

**AO-PAIRED-LEGACY · dense_fm_policy · fau · alignment_plus_selection · CS_SINGLE · 3401** (critical value 3.03)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.001 | [-0.002, +0.005] | [-0.003, +0.006] | contains 0 | -0.047 [-0.053, -0.041] | ci: +0.004 (n=5); ha: -0.000 (n=6); th: n=3 |
| 10s | 14 | +0.004 | [-0.008, +0.016] | [-0.011, +0.020] | contains 0 | -0.041 [-0.053, -0.028] | ci: +0.020 (n=5); ha: -0.004 (n=6); th: n=3 |
| 20s | 14 | -0.112 | [-0.130, -0.094] | [-0.137, -0.087] | I<0 | -0.146 [-0.164, -0.129] | ci: -0.104 (n=5); ha: -0.121 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dense_fm_policy · fau · alignment_plus_selection · NCE · 3401** (critical value 2.81)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.000 | [-0.004, +0.003] | [-0.005, +0.005] | contains 0 | -0.002 [-0.003, +0.000] | ci: -0.004 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | -0.037 | [-0.042, -0.031] | [-0.044, -0.030] | I<0 | +0.004 [-0.006, +0.013] | ci: -0.032 (n=5); ha: -0.041 (n=6); th: n=3 |
| 20s | 14 | +0.019 | [+0.008, +0.030] | [+0.006, +0.032] | I>0 | -0.013 [-0.038, +0.012] | ci: +0.018 (n=5); ha: +0.015 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dense_fm_policy · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.98)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | -0.014 | [-0.030, +0.002] | [-0.034, +0.005] | contains 0 | -0.017 [-0.024, -0.009] | ci: -0.013 (n=5); ha: -0.018 (n=6); th: n=3 |
| 10s | 14 | -0.008 | [-0.029, +0.013] | [-0.037, +0.020] | contains 0 | -0.008 [-0.019, +0.003] | ci: +0.008 (n=5); ha: -0.025 (n=6); th: n=3 |
| 20s | 14 | -0.026 | [-0.067, +0.015] | [-0.083, +0.031] | contains 0 | -0.090 [-0.104, -0.076] | ci: -0.021 (n=5); ha: -0.049 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dense_fm_policy · fau · attended_alignment · NCE · 3401** (critical value 3.01)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.000 | [-0.002, +0.002] | [-0.002, +0.003] | contains 0 | -0.001 [-0.003, +0.002] | ci: +0.002 (n=5); ha: -0.001 (n=6); th: n=3 |
| 10s | 14 | +0.010 | [-0.006, +0.026] | [-0.011, +0.032] | contains 0 | -0.000 [-0.007, +0.006] | ci: +0.001 (n=5); ha: +0.003 (n=6); th: n=3 |
| 20s | 14 | +0.020 | [+0.010, +0.030] | [+0.006, +0.033] | I>0 | -0.004 [-0.021, +0.014] | ci: +0.017 (n=5); ha: +0.023 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dense_fm_policy · fau · selection_only · SELECTION_CE · 3401** (critical value 2.98)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 14 | +0.009 | [-0.005, +0.022] | [-0.010, +0.027] | contains 0 | -0.000 [-0.002, +0.001] | ci: +0.009 (n=5); ha: +0.013 (n=6); th: n=3 |
| 10s | 14 | +0.019 | [-0.001, +0.039] | [-0.007, +0.045] | contains 0 | +0.013 [+0.005, +0.022] | ci: +0.018 (n=5); ha: +0.019 (n=6); th: n=3 |
| 20s | 14 | -0.015 | [-0.037, +0.007] | [-0.044, +0.015] | contains 0 | +0.021 [+0.010, +0.032] | ci: -0.033 (n=5); ha: -0.006 (n=6); th: n=3 |

**AO-PAIRED-LEGACY · dtu · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.55)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.139 [-0.163, -0.115] | hi: -0.000 (n=22); nh: -0.001 (n=22) |
| 10s | 44 | -0.000 | [-0.002, +0.001] | [-0.002, +0.002] | contains 0 | -0.274 [-0.294, -0.253] | hi: +0.000 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.016 | [-0.024, -0.007] | [-0.026, -0.005] | I<0 | -0.352 [-0.376, -0.327] | hi: -0.011 (n=22); nh: -0.021 (n=22) |

**AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · mean** (critical value 2.47)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | hi: +0.000 (n=22); nh: -0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.002, +0.000] | [-0.002, +0.001] | contains 0 | -0.001 [-0.003, +0.001] | hi: -0.002 (n=22); nh: +0.000 (n=22) |
| 20s | 44 | -0.013 | [-0.019, -0.007] | [-0.021, -0.006] | I<0 | -0.033 [-0.040, -0.027] | hi: -0.014 (n=22); nh: -0.012 (n=22) |

**AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 3401** (critical value 2.50)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.001 | [-0.002, +0.000] | [-0.002, +0.000] | contains 0 | +0.000 [-0.000, +0.001] | hi: -0.000 (n=22); nh: -0.001 (n=22) |
| 10s | 44 | -0.001 | [-0.003, +0.001] | [-0.003, +0.001] | contains 0 | -0.002 [-0.005, +0.002] | hi: -0.003 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.016 | [-0.026, -0.007] | [-0.028, -0.005] | I<0 | -0.048 [-0.059, -0.037] | hi: -0.015 (n=22); nh: -0.018 (n=22) |

**AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 3407** (critical value 2.46)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.002] | contains 0 | +0.000 [-0.002, +0.002] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.000 | [-0.002, +0.001] | [-0.003, +0.002] | contains 0 | -0.001 [-0.004, +0.002] | hi: -0.003 (n=22); nh: +0.002 (n=22) |
| 20s | 44 | -0.012 | [-0.021, -0.004] | [-0.022, -0.002] | I<0 | -0.031 [-0.043, -0.020] | hi: -0.010 (n=22); nh: -0.015 (n=22) |

**AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 3413** (critical value 2.58)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | hi: +0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.003, +0.001] | [-0.003, +0.002] | contains 0 | -0.001 [-0.004, +0.002] | hi: +0.000 (n=22); nh: -0.002 (n=22) |
| 20s | 44 | -0.011 | [-0.020, -0.002] | [-0.022, +0.000] | contains 0 | -0.020 [-0.028, -0.012] | hi: -0.018 (n=22); nh: -0.004 (n=22) |

**AO-PAIRED-LEGACY · dtu · attended_alignment · CS_SINGLE · 3401** (critical value 2.53)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.142 [-0.164, -0.119] | hi: -0.000 (n=22); nh: -0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.003, +0.001] | [-0.003, +0.002] | contains 0 | -0.257 [-0.279, -0.235] | hi: +0.001 (n=22); nh: -0.002 (n=22) |
| 20s | 44 | -0.008 | [-0.017, +0.001] | [-0.019, +0.003] | contains 0 | -0.326 [-0.349, -0.302] | hi: -0.015 (n=22); nh: -0.001 (n=22) |

**AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · mean** (critical value 2.53)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | -0.000 [-0.001, +0.001] | hi: -0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.001 | [-0.002, +0.001] | [-0.002, +0.001] | contains 0 | -0.004 [-0.006, -0.002] | hi: -0.000 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.007 | [-0.013, -0.002] | [-0.014, -0.000] | I<0 | -0.067 [-0.075, -0.059] | hi: -0.007 (n=22); nh: -0.007 (n=22) |

**AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 3401** (critical value 2.50)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | hi: -0.000 (n=22); nh: +0.001 (n=22) |
| 10s | 44 | -0.000 | [-0.003, +0.002] | [-0.004, +0.003] | contains 0 | -0.006 [-0.011, -0.001] | hi: +0.000 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.005 | [-0.013, +0.003] | [-0.014, +0.005] | contains 0 | -0.121 [-0.137, -0.105] | hi: -0.002 (n=22); nh: -0.007 (n=22) |

**AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 3407** (critical value 2.60)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | -0.000 [-0.003, +0.003] | hi: -0.000 (n=22); nh: -0.000 (n=22) |
| 10s | 44 | +0.001 | [-0.001, +0.002] | [-0.002, +0.003] | contains 0 | -0.002 [-0.006, +0.001] | hi: +0.001 (n=22); nh: +0.001 (n=22) |
| 20s | 44 | -0.009 | [-0.016, -0.002] | [-0.018, +0.000] | contains 0 | -0.052 [-0.065, -0.039] | hi: -0.010 (n=22); nh: -0.008 (n=22) |

**AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 3413** (critical value 2.47)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 [-0.001, +0.000] | hi: -0.000 (n=22); nh: +0.000 (n=22) |
| 10s | 44 | -0.002 | [-0.004, +0.000] | [-0.005, +0.001] | contains 0 | -0.003 [-0.006, -0.000] | hi: -0.002 (n=22); nh: -0.001 (n=22) |
| 20s | 44 | -0.008 | [-0.016, +0.001] | [-0.018, +0.003] | contains 0 | -0.029 [-0.038, -0.019] | hi: -0.010 (n=22); nh: -0.006 (n=22) |

**AO-PAIRED-LEGACY · dtu · selection_only · SELECTION_CE · 3401** (critical value 2.46)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 44 | -0.000 | [-0.001, +0.001] | [-0.002, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | hi: +0.000 (n=22); nh: -0.001 (n=22) |
| 10s | 44 | +0.001 | [-0.001, +0.004] | [-0.002, +0.004] | contains 0 | +0.000 [-0.002, +0.003] | hi: -0.000 (n=22); nh: +0.002 (n=22) |
| 20s | 44 | -0.007 | [-0.015, +0.001] | [-0.017, +0.003] | contains 0 | -0.013 [-0.019, -0.007] | hi: -0.003 (n=22); nh: -0.011 (n=22) |

**AO-PAIRED-LEGACY · fau · alignment_plus_selection · CS_SINGLE · 3401** (critical value 2.45)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.000] | contains 0 | -0.045 [-0.056, -0.033] | ci: -0.000 (n=24); ha: -0.001 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.001 | [-0.004, +0.002] | [-0.005, +0.003] | contains 0 | -0.072 [-0.086, -0.057] | ci: -0.001 (n=24); ha: -0.002 (n=29); th: +0.001 (n=14) |
| 20s | 67 | -0.001 | [-0.008, +0.006] | [-0.010, +0.008] | contains 0 | -0.127 [-0.147, -0.108] | ci: -0.005 (n=24); ha: -0.000 (n=29); th: +0.002 (n=14) |

**AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · mean** (critical value 2.42)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.000] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | ci: -0.000 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.001 | [-0.002, +0.001] | [-0.003, +0.002] | contains 0 | -0.004 [-0.008, -0.000] | ci: -0.001 (n=24); ha: -0.001 (n=29); th: +0.001 (n=14) |
| 20s | 67 | -0.006 | [-0.009, -0.002] | [-0.010, -0.001] | I<0 | -0.052 [-0.061, -0.042] | ci: -0.008 (n=24); ha: -0.006 (n=29); th: -0.001 (n=14) |

**AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 3401** (critical value 2.42)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | ci: -0.000 (n=24); ha: +0.001 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.002 | [-0.005, +0.001] | [-0.005, +0.002] | contains 0 | -0.001 [-0.006, +0.003] | ci: -0.003 (n=24); ha: -0.002 (n=29); th: +0.000 (n=14) |
| 20s | 67 | -0.008 | [-0.013, -0.002] | [-0.015, -0.000] | I<0 | -0.050 [-0.063, -0.036] | ci: -0.008 (n=24); ha: -0.008 (n=29); th: -0.006 (n=14) |

**AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 3407** (critical value 2.48)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.001 [-0.001, +0.002] | ci: +0.001 (n=24); ha: -0.001 (n=29); th: -0.000 (n=14) |
| 10s | 67 | +0.001 | [-0.002, +0.004] | [-0.003, +0.004] | contains 0 | -0.009 [-0.015, -0.003] | ci: +0.002 (n=24); ha: -0.001 (n=29); th: +0.003 (n=14) |
| 20s | 67 | -0.003 | [-0.011, +0.005] | [-0.013, +0.006] | contains 0 | -0.085 [-0.101, -0.069] | ci: -0.005 (n=24); ha: -0.007 (n=29); th: +0.006 (n=14) |

**AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 3413** (critical value 2.43)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 [-0.001, +0.001] | ci: -0.001 (n=24); ha: +0.001 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.001 | [-0.004, +0.003] | [-0.005, +0.003] | contains 0 | -0.003 [-0.008, +0.003] | ci: -0.003 (n=24); ha: +0.000 (n=29); th: +0.001 (n=14) |
| 20s | 67 | -0.006 | [-0.013, +0.002] | [-0.015, +0.003] | contains 0 | -0.020 [-0.029, -0.011] | ci: -0.010 (n=24); ha: -0.003 (n=29); th: -0.004 (n=14) |

**AO-PAIRED-LEGACY · fau · attended_alignment · CS_SINGLE · 3401** (critical value 2.42)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.049 [-0.060, -0.038] | ci: +0.001 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | +0.001 | [-0.001, +0.004] | [-0.002, +0.005] | contains 0 | -0.089 [-0.105, -0.074] | ci: -0.001 (n=24); ha: +0.003 (n=29); th: +0.004 (n=14) |
| 20s | 67 | -0.007 | [-0.014, +0.001] | [-0.016, +0.002] | contains 0 | -0.144 [-0.163, -0.125] | ci: -0.001 (n=24); ha: -0.010 (n=29); th: -0.011 (n=14) |

**AO-PAIRED-LEGACY · fau · attended_alignment · NCE · mean** (critical value 2.39)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [-0.000, +0.001] | [-0.001, +0.001] | contains 0 | -0.000 [-0.001, +0.001] | ci: -0.001 (n=24); ha: +0.001 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.000 | [-0.002, +0.002] | [-0.002, +0.002] | contains 0 | -0.010 [-0.014, -0.007] | ci: +0.002 (n=24); ha: -0.002 (n=29); th: -0.000 (n=14) |
| 20s | 67 | -0.005 | [-0.009, -0.000] | [-0.010, +0.000] | contains 0 | -0.087 [-0.100, -0.074] | ci: -0.009 (n=24); ha: -0.005 (n=29); th: +0.003 (n=14) |

**AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 3401** (critical value 2.46)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.001] | ci: -0.001 (n=24); ha: +0.000 (n=29); th: +0.000 (n=14) |
| 10s | 67 | -0.004 | [-0.007, -0.001] | [-0.007, -0.000] | I<0 | -0.004 [-0.007, +0.000] | ci: -0.002 (n=24); ha: -0.005 (n=29); th: -0.004 (n=14) |
| 20s | 67 | -0.005 | [-0.013, +0.002] | [-0.014, +0.004] | contains 0 | -0.086 [-0.102, -0.070] | ci: -0.008 (n=24); ha: -0.003 (n=29); th: -0.004 (n=14) |

**AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 3407** (critical value 2.48)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | -0.001 [-0.004, +0.001] | ci: -0.000 (n=24); ha: +0.001 (n=29); th: -0.000 (n=14) |
| 10s | 67 | -0.002 | [-0.005, +0.001] | [-0.006, +0.002] | contains 0 | -0.022 [-0.030, -0.015] | ci: -0.002 (n=24); ha: -0.004 (n=29); th: +0.002 (n=14) |
| 20s | 67 | -0.002 | [-0.009, +0.006] | [-0.011, +0.008] | contains 0 | -0.147 [-0.169, -0.126] | ci: +0.000 (n=24); ha: -0.005 (n=29); th: +0.001 (n=14) |

**AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 3413** (critical value 2.50)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | +0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.001, +0.002] | ci: -0.001 (n=24); ha: +0.001 (n=29); th: +0.001 (n=14) |
| 10s | 67 | +0.005 | [+0.001, +0.009] | [+0.001, +0.010] | I>0 | -0.005 [-0.009, -0.001] | ci: +0.011 (n=24); ha: +0.002 (n=29); th: +0.002 (n=14) |
| 20s | 67 | -0.007 | [-0.014, +0.000] | [-0.016, +0.002] | contains 0 | -0.029 [-0.038, -0.019] | ci: -0.019 (n=24); ha: -0.006 (n=29); th: +0.012 (n=14) |

**AO-PAIRED-LEGACY · fau · selection_only · SELECTION_CE · 3401** (critical value 2.43)

| member | n | Δ | 95% CI | 95% simultaneous | class | Δ native [95% CI] | per group |
|---|---|---|---|---|---|---|---|
| 5s | 67 | -0.000 | [-0.001, +0.001] | [-0.001, +0.001] | contains 0 | +0.000 [-0.000, +0.001] | ci: -0.001 (n=24); ha: -0.000 (n=29); th: +0.001 (n=14) |
| 10s | 67 | -0.002 | [-0.005, +0.001] | [-0.005, +0.002] | contains 0 | -0.004 [-0.008, -0.001] | ci: +0.001 (n=24); ha: -0.004 (n=29); th: -0.003 (n=14) |
| 20s | 67 | -0.004 | [-0.010, +0.003] | [-0.012, +0.005] | contains 0 | -0.010 [-0.020, -0.001] | ci: -0.002 (n=24); ha: -0.003 (n=29); th: -0.007 (n=14) |

### 1.3 Logloss of the two learned integrators (bits; pointwise 95% bootstrap-t; Δ = antisymmetric − legacy, negative = antisymmetric better)

| cell | n | legacy paired | antisymmetric | Δ |
|---|---|---|---|---|
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 10s native | 44 | 1.000 [1.000, 1.000] | 0.737 [0.681, 0.792] | -0.263 [-0.320, -0.206] |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 10s unified | 44 | 0.773 [0.726, 0.820] | 0.809 [0.750, 0.868] | +0.036 [+0.023, +0.049] |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 0.543 [0.459, 0.626] | -0.459 [-0.540, -0.377] |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 20s unified | 44 | 0.653 [0.604, 0.701] | 0.655 [0.567, 0.742] | +0.002 [-0.041, +0.045] |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 5s native | 44 | 0.999 [0.999, 0.999] | 0.859 [0.824, 0.894] | -0.140 [-0.176, -0.105] |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 5s unified | 44 | 0.891 [0.857, 0.926] | 0.900 [0.864, 0.937] | +0.009 [+0.006, +0.011] |
| complement_policy dtu alignment_plus_selection NCE 3401 10s native | 44 | 0.866 [0.850, 0.882] | 0.699 [0.619, 0.780] | -0.167 [-0.232, -0.102] |
| complement_policy dtu alignment_plus_selection NCE 3401 10s unified | 44 | 0.726 [0.671, 0.780] | 0.752 [0.684, 0.819] | +0.026 [+0.012, +0.040] |
| complement_policy dtu alignment_plus_selection NCE 3401 20s native | 44 | 0.913 [0.903, 0.924] | 0.493 [0.394, 0.591] | -0.420 [-0.511, -0.330] |
| complement_policy dtu alignment_plus_selection NCE 3401 20s unified | 44 | 0.604 [0.550, 0.659] | 0.576 [0.484, 0.668] | -0.028 [-0.066, +0.010] |
| complement_policy dtu alignment_plus_selection NCE 3401 5s native | 44 | 0.840 [0.819, 0.861] | 0.835 [0.779, 0.890] | -0.005 [-0.042, +0.032] |
| complement_policy dtu alignment_plus_selection NCE 3401 5s unified | 44 | 0.854 [0.814, 0.894] | 0.861 [0.819, 0.904] | +0.007 [+0.005, +0.009] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 10s native | 44 | 1.000 [0.999, 1.000] | 0.724 [0.675, 0.772] | -0.276 [-0.325, -0.227] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 10s unified | 44 | 0.772 [0.726, 0.817] | 0.788 [0.734, 0.843] | +0.016 [+0.007, +0.026] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 0.540 [0.471, 0.608] | -0.461 [-0.531, -0.392] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 20s unified | 44 | 0.648 [0.601, 0.696] | 0.623 [0.546, 0.700] | -0.025 [-0.057, +0.007] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 5s native | 44 | 0.999 [0.999, 0.999] | 0.849 [0.819, 0.878] | -0.150 [-0.180, -0.120] |
| complement_policy dtu attended_alignment CS_SINGLE 3401 5s unified | 44 | 0.875 [0.846, 0.904] | 0.879 [0.848, 0.910] | +0.004 [+0.002, +0.005] |
| complement_policy dtu attended_alignment NCE 3401 10s native | 44 | 0.905 [0.895, 0.914] | 0.678 [0.599, 0.757] | -0.227 [-0.294, -0.160] |
| complement_policy dtu attended_alignment NCE 3401 10s unified | 44 | 0.711 [0.657, 0.764] | 0.727 [0.661, 0.793] | +0.016 [+0.003, +0.030] |
| complement_policy dtu attended_alignment NCE 3401 20s native | 44 | 0.943 [0.937, 0.949] | 0.473 [0.376, 0.570] | -0.470 [-0.564, -0.376] |
| complement_policy dtu attended_alignment NCE 3401 20s unified | 44 | 0.591 [0.538, 0.644] | 0.545 [0.460, 0.629] | -0.047 [-0.081, -0.012] |
| complement_policy dtu attended_alignment NCE 3401 5s native | 44 | 0.870 [0.855, 0.885] | 0.809 [0.755, 0.862] | -0.061 [-0.100, -0.023] |
| complement_policy dtu attended_alignment NCE 3401 5s unified | 44 | 0.840 [0.802, 0.877] | 0.845 [0.806, 0.883] | +0.005 [+0.003, +0.007] |
| complement_policy dtu selection_only SELECTION_CE 3401 10s native | 44 | 0.704 [0.663, 0.744] | 0.780 [0.704, 0.856] | +0.076 [+0.039, +0.113] |
| complement_policy dtu selection_only SELECTION_CE 3401 10s unified | 44 | 0.772 [0.728, 0.816] | 0.788 [0.733, 0.843] | +0.016 [+0.005, +0.027] |
| complement_policy dtu selection_only SELECTION_CE 3401 20s native | 44 | 0.650 [0.613, 0.687] | 0.572 [0.480, 0.664] | -0.078 [-0.142, -0.014] |
| complement_policy dtu selection_only SELECTION_CE 3401 20s unified | 44 | 0.659 [0.613, 0.705] | 0.631 [0.552, 0.710] | -0.028 [-0.062, +0.005] |
| complement_policy dtu selection_only SELECTION_CE 3401 5s native | 44 | 0.845 [0.805, 0.884] | 0.895 [0.846, 0.945] | +0.051 [+0.039, +0.062] |
| complement_policy dtu selection_only SELECTION_CE 3401 5s unified | 44 | 0.881 [0.851, 0.910] | 0.885 [0.853, 0.916] | +0.004 [+0.002, +0.006] |
| complement_policy fau alignment_plus_selection NCE 3401 10s native | 14 | 0.935 [0.914, 0.956] | 0.953 [0.893, 1.013] | +0.018 [-0.024, +0.060] |
| complement_policy fau alignment_plus_selection NCE 3401 10s unified | 14 | 0.967 [0.920, 1.014] | 0.969 [0.918, 1.019] | +0.002 [-0.002, +0.006] |
| complement_policy fau alignment_plus_selection NCE 3401 20s native | 14 | 0.941 [0.927, 0.955] | 0.884 [0.820, 0.948] | -0.057 [-0.109, -0.005] |
| complement_policy fau alignment_plus_selection NCE 3401 20s unified | 14 | 0.941 [0.883, 0.998] | 0.941 [0.862, 1.020] | +0.000 [-0.018, +0.019] |
| complement_policy fau alignment_plus_selection NCE 3401 5s native | 14 | 0.972 [0.948, 0.996] | 1.078 [1.036, 1.121] | +0.106 [+0.086, +0.127] |
| complement_policy fau alignment_plus_selection NCE 3401 5s unified | 14 | 0.994 [0.966, 1.022] | 0.994 [0.965, 1.024] | +0.001 [+0.000, +0.002] |
| complement_policy fau attended_alignment CS_SINGLE 3401 10s native | 14 | 1.000 [1.000, 1.000] | 0.873 [0.831, 0.915] | -0.127 [-0.169, -0.084] |
| complement_policy fau attended_alignment CS_SINGLE 3401 10s unified | 14 | 0.987 [0.965, 1.008] | 0.986 [0.962, 1.010] | -0.001 [-0.003, +0.001] |
| complement_policy fau attended_alignment CS_SINGLE 3401 20s native | 14 | 1.000 [1.000, 1.000] | 0.716 [0.647, 0.786] | -0.284 [-0.354, -0.214] |
| complement_policy fau attended_alignment CS_SINGLE 3401 20s unified | 14 | 0.960 [0.935, 0.986] | 0.953 [0.914, 0.992] | -0.008 [-0.021, +0.006] |
| complement_policy fau attended_alignment CS_SINGLE 3401 5s native | 14 | 1.000 [1.000, 1.000] | 0.934 [0.910, 0.958] | -0.066 [-0.089, -0.042] |
| complement_policy fau attended_alignment CS_SINGLE 3401 5s unified | 14 | 0.988 [0.977, 0.999] | 0.988 [0.977, 0.999] | -0.000 [-0.000, +0.000] |
| complement_policy fau attended_alignment NCE 3401 10s native | 14 | 0.966 [0.954, 0.978] | 0.998 [0.942, 1.054] | +0.032 [-0.015, +0.079] |
| complement_policy fau attended_alignment NCE 3401 10s unified | 14 | 1.014 [0.981, 1.048] | 1.021 [0.984, 1.058] | +0.007 [+0.004, +0.009] |
| complement_policy fau attended_alignment NCE 3401 20s native | 14 | 0.970 [0.962, 0.978] | 0.947 [0.863, 1.030] | -0.023 [-0.105, +0.059] |
| complement_policy fau attended_alignment NCE 3401 20s unified | 14 | 0.984 [0.936, 1.031] | 1.003 [0.938, 1.067] | +0.019 [-0.001, +0.040] |
| complement_policy fau attended_alignment NCE 3401 5s native | 14 | 0.984 [0.970, 0.999] | 1.047 [1.009, 1.084] | +0.062 [+0.039, +0.085] |
| complement_policy fau attended_alignment NCE 3401 5s unified | 14 | 1.009 [0.989, 1.029] | 1.010 [0.990, 1.030] | +0.001 [+0.001, +0.001] |
| complement_policy fau selection_only SELECTION_CE 3401 10s native | 14 | 0.963 [0.962, 0.964] | 0.958 [0.957, 0.959] | -0.005 [-0.006, -0.004] |
| complement_policy fau selection_only SELECTION_CE 3401 10s unified | 14 | 0.986 [0.967, 1.005] | 0.986 [0.966, 1.005] | -0.000 [-0.002, +0.001] |
| complement_policy fau selection_only SELECTION_CE 3401 20s native | 14 | 0.916 [0.915, 0.916] | 0.882 [0.880, 0.884] | -0.034 [-0.035, -0.032] |
| complement_policy fau selection_only SELECTION_CE 3401 20s unified | 14 | 0.969 [0.940, 0.999] | 0.975 [0.930, 1.020] | +0.006 [-0.012, +0.024] |
| complement_policy fau selection_only SELECTION_CE 3401 5s native | 14 | 0.972 [0.971, 0.973] | 0.972 [0.971, 0.973] | -0.000 [-0.000, -0.000] |
| complement_policy fau selection_only SELECTION_CE 3401 5s unified | 14 | 0.993 [0.982, 1.003] | 0.993 [0.982, 1.003] | -0.000 [-0.000, +0.000] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 10s native | 44 | 1.000 [1.000, 1.000] | 1.014 [1.001, 1.028] | +0.014 [+0.001, +0.027] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 10s unified | 44 | 1.004 [1.001, 1.007] | 1.005 [1.001, 1.009] | +0.001 [+0.001, +0.002] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 1.037 [1.014, 1.059] | +0.035 [+0.012, +0.058] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 20s unified | 44 | 1.001 [0.996, 1.006] | 1.008 [0.999, 1.017] | +0.007 [+0.002, +0.012] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 5s native | 44 | 1.000 [1.000, 1.000] | 1.011 [1.006, 1.015] | +0.011 [+0.006, +0.015] |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 5s unified | 44 | 1.001 [1.000, 1.002] | 1.001 [1.000, 1.002] | +0.000 [+0.000, +0.000] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 10s native | 44 | 0.971 [0.956, 0.987] | 1.035 [1.004, 1.066] | +0.064 [+0.047, +0.081] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 10s unified | 44 | 1.113 [1.083, 1.143] | 1.234 [1.188, 1.280] | +0.121 [+0.101, +0.141] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 20s native | 44 | 0.959 [0.945, 0.972] | 0.956 [0.921, 0.991] | -0.003 [-0.025, +0.020] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 20s unified | 44 | 1.015 [0.985, 1.045] | 1.209 [1.149, 1.269] | +0.194 [+0.158, +0.230] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 5s native | 44 | 1.029 [1.012, 1.047] | 1.155 [1.127, 1.183] | +0.125 [+0.108, +0.143] |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 5s unified | 44 | 1.146 [1.119, 1.173] | 1.171 [1.141, 1.201] | +0.025 [+0.021, +0.029] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 10s native | 44 | 1.000 [1.000, 1.000] | 1.004 [0.988, 1.020] | +0.004 [-0.012, +0.020] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 10s unified | 44 | 1.001 [0.999, 1.003] | 1.001 [0.999, 1.004] | +0.000 [-0.000, +0.001] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 1.004 [0.981, 1.028] | +0.003 [-0.021, +0.026] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 20s unified | 44 | 0.995 [0.991, 0.999] | 0.995 [0.988, 1.001] | -0.000 [-0.003, +0.003] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 5s native | 44 | 1.000 [1.000, 1.000] | 1.004 [0.998, 1.009] | +0.004 [-0.002, +0.009] |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 5s unified | 44 | 0.999 [0.998, 1.000] | 0.999 [0.998, 1.000] | -0.000 [-0.000, -0.000] |
| dense_fm_policy dtu attended_alignment NCE 3401 10s native | 44 | 0.971 [0.958, 0.985] | 1.064 [1.028, 1.100] | +0.093 [+0.070, +0.116] |
| dense_fm_policy dtu attended_alignment NCE 3401 10s unified | 44 | 1.124 [1.090, 1.157] | 1.253 [1.208, 1.298] | +0.129 [+0.115, +0.143] |
| dense_fm_policy dtu attended_alignment NCE 3401 20s native | 44 | 0.960 [0.948, 0.972] | 0.975 [0.937, 1.014] | +0.015 [-0.013, +0.043] |
| dense_fm_policy dtu attended_alignment NCE 3401 20s unified | 44 | 1.022 [0.987, 1.058] | 1.254 [1.181, 1.327] | +0.231 [+0.192, +0.271] |
| dense_fm_policy dtu attended_alignment NCE 3401 5s native | 44 | 1.031 [1.015, 1.047] | 1.200 [1.165, 1.235] | +0.169 [+0.150, +0.189] |
| dense_fm_policy dtu attended_alignment NCE 3401 5s unified | 44 | 1.161 [1.137, 1.184] | 1.188 [1.162, 1.213] | +0.027 [+0.024, +0.029] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 10s native | 44 | 0.957 [0.945, 0.969] | 1.237 [1.200, 1.274] | +0.280 [+0.251, +0.310] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 10s unified | 44 | 1.004 [1.001, 1.007] | 1.005 [1.001, 1.009] | +0.001 [+0.000, +0.001] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 20s native | 44 | 0.924 [0.915, 0.933] | 1.253 [1.201, 1.305] | +0.329 [+0.282, +0.377] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 20s unified | 44 | 1.000 [0.995, 1.006] | 1.004 [0.996, 1.012] | +0.004 [+0.001, +0.007] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 5s native | 44 | 1.038 [1.027, 1.049] | 1.147 [1.128, 1.167] | +0.110 [+0.101, +0.119] |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 5s unified | 44 | 1.001 [1.000, 1.002] | 1.001 [1.000, 1.002] | +0.000 [-0.000, +0.000] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 10s native | 14 | 1.000 [1.000, 1.000] | 0.992 [0.989, 0.995] | -0.008 [-0.011, -0.005] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 10s unified | 14 | 0.994 [0.992, 0.995] | 0.993 [0.992, 0.995] | -0.001 [-0.001, -0.001] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 20s native | 14 | 1.000 [1.000, 1.000] | 0.916 [0.908, 0.924] | -0.084 [-0.092, -0.076] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 20s unified | 14 | 0.986 [0.980, 0.993] | 1.028 [1.018, 1.038] | +0.042 [+0.037, +0.047] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 5s native | 14 | 1.000 [1.000, 1.000] | 0.987 [0.985, 0.989] | -0.013 [-0.015, -0.011] |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 5s unified | 14 | 0.997 [0.997, 0.998] | 0.997 [0.997, 0.998] | -0.000 [-0.000, -0.000] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 10s native | 14 | 0.989 [0.974, 1.003] | 1.229 [1.150, 1.308] | +0.241 [+0.179, +0.302] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 10s unified | 14 | 1.012 [1.011, 1.014] | 1.014 [1.012, 1.016] | +0.002 [+0.002, +0.002] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 20s native | 14 | 0.983 [0.976, 0.990] | 1.237 [1.130, 1.344] | +0.254 [+0.152, +0.356] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 20s unified | 14 | 0.987 [0.985, 0.989] | 1.001 [0.999, 1.004] | +0.015 [+0.014, +0.015] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 5s native | 14 | 1.011 [0.992, 1.030] | 1.164 [1.114, 1.213] | +0.153 [+0.119, +0.188] |
| dense_fm_policy fau alignment_plus_selection NCE 3401 5s unified | 14 | 1.001 [1.001, 1.002] | 1.002 [1.001, 1.002] | +0.000 [+0.000, +0.000] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 10s native | 14 | 1.000 [1.000, 1.000] | 1.036 [1.033, 1.040] | +0.036 [+0.033, +0.040] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 10s unified | 14 | 0.998 [0.995, 1.001] | 0.998 [0.995, 1.001] | +0.000 [-0.000, +0.001] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 20s native | 14 | 1.000 [1.000, 1.000] | 1.042 [1.027, 1.057] | +0.042 [+0.027, +0.056] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 20s unified | 14 | 0.989 [0.984, 0.994] | 0.990 [0.983, 0.996] | +0.001 [-0.001, +0.003] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 5s native | 14 | 1.000 [1.000, 1.000] | 0.992 [0.991, 0.993] | -0.008 [-0.009, -0.007] |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 5s unified | 14 | 1.000 [1.000, 1.001] | 1.000 [1.000, 1.001] | +0.000 [-0.000, +0.000] |
| dense_fm_policy fau attended_alignment NCE 3401 10s native | 14 | 0.992 [0.981, 1.003] | 1.142 [1.097, 1.186] | +0.150 [+0.118, +0.182] |
| dense_fm_policy fau attended_alignment NCE 3401 10s unified | 14 | 1.018 [1.010, 1.026] | 1.024 [1.016, 1.033] | +0.006 [+0.005, +0.007] |
| dense_fm_policy fau attended_alignment NCE 3401 20s native | 14 | 0.978 [0.971, 0.986] | 1.117 [1.060, 1.173] | +0.138 [+0.087, +0.190] |
| dense_fm_policy fau attended_alignment NCE 3401 20s unified | 14 | 0.986 [0.976, 0.996] | 1.002 [0.987, 1.016] | +0.016 [+0.010, +0.021] |
| dense_fm_policy fau attended_alignment NCE 3401 5s native | 14 | 1.043 [1.028, 1.058] | 1.176 [1.142, 1.210] | +0.133 [+0.115, +0.151] |
| dense_fm_policy fau attended_alignment NCE 3401 5s unified | 14 | 1.009 [1.006, 1.012] | 1.010 [1.007, 1.013] | +0.001 [+0.001, +0.001] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 10s native | 14 | 1.067 [1.064, 1.071] | 1.247 [1.241, 1.252] | +0.179 [+0.177, +0.182] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 10s unified | 14 | 1.005 [1.001, 1.009] | 1.006 [1.002, 1.010] | +0.002 [+0.001, +0.002] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 20s native | 14 | 0.933 [0.928, 0.937] | 1.244 [1.236, 1.252] | +0.311 [+0.306, +0.316] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 20s unified | 14 | 0.995 [0.991, 1.000] | 1.004 [0.992, 1.016] | +0.009 [+0.001, +0.017] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 5s native | 14 | 1.176 [1.172, 1.179] | 1.226 [1.222, 1.230] | +0.051 [+0.050, +0.051] |
| dense_fm_policy fau selection_only SELECTION_CE 3401 5s unified | 14 | 0.999 [0.999, 1.000] | 0.999 [0.999, 1.000] | +0.000 [-0.000, +0.000] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 10s native | 44 | 1.000 [1.000, 1.000] | 0.728 [0.671, 0.786] | -0.271 [-0.329, -0.213] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 10s unified | 44 | 0.752 [0.705, 0.799] | 0.787 [0.727, 0.847] | +0.035 [+0.021, +0.049] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 0.532 [0.448, 0.616] | -0.469 [-0.552, -0.386] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 20s unified | 44 | 0.628 [0.579, 0.677] | 0.621 [0.533, 0.708] | -0.008 [-0.048, +0.032] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 5s native | 44 | 0.999 [0.999, 0.999] | 0.854 [0.817, 0.892] | -0.144 [-0.180, -0.109] |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 5s unified | 44 | 0.879 [0.842, 0.916] | 0.888 [0.849, 0.927] | +0.009 [+0.007, +0.012] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 10s native | 44 | 0.861 [0.845, 0.876] | 0.712 [0.627, 0.797] | -0.149 [-0.215, -0.082] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 10s unified | 44 | 0.718 [0.666, 0.770] | 0.740 [0.677, 0.803] | +0.022 [+0.009, +0.036] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 10s native | 44 | 0.866 [0.851, 0.881] | 0.714 [0.626, 0.803] | -0.152 [-0.225, -0.078] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 10s unified | 44 | 0.710 [0.655, 0.765] | 0.733 [0.663, 0.803] | +0.022 [+0.008, +0.037] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 10s native | 44 | 0.857 [0.841, 0.873] | 0.697 [0.610, 0.783] | -0.160 [-0.229, -0.092] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 10s unified | 44 | 0.716 [0.659, 0.773] | 0.741 [0.671, 0.810] | +0.024 [+0.010, +0.039] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 20s native | 44 | 0.908 [0.898, 0.918] | 0.502 [0.402, 0.602] | -0.406 [-0.499, -0.313] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 20s unified | 44 | 0.597 [0.544, 0.650] | 0.556 [0.468, 0.644] | -0.040 [-0.076, -0.005] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 20s native | 44 | 0.911 [0.901, 0.921] | 0.499 [0.395, 0.602] | -0.412 [-0.511, -0.313] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 20s unified | 44 | 0.587 [0.532, 0.642] | 0.542 [0.449, 0.634] | -0.045 [-0.084, -0.007] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 20s native | 44 | 0.905 [0.894, 0.915] | 0.483 [0.379, 0.587] | -0.422 [-0.515, -0.329] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 20s unified | 44 | 0.594 [0.535, 0.652] | 0.551 [0.456, 0.647] | -0.042 [-0.084, -0.001] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 5s native | 44 | 0.838 [0.818, 0.859] | 0.846 [0.790, 0.902] | +0.008 [-0.030, +0.046] |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 5s unified | 44 | 0.849 [0.811, 0.887] | 0.855 [0.816, 0.895] | +0.006 [+0.004, +0.008] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 5s native | 44 | 0.844 [0.823, 0.865] | 0.849 [0.791, 0.906] | +0.005 [-0.035, +0.044] |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 5s unified | 44 | 0.844 [0.804, 0.885] | 0.851 [0.807, 0.894] | +0.006 [+0.004, +0.009] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 5s native | 44 | 0.834 [0.813, 0.855] | 0.837 [0.780, 0.894] | +0.003 [-0.034, +0.039] |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 5s unified | 44 | 0.848 [0.808, 0.889] | 0.855 [0.812, 0.898] | +0.007 [+0.005, +0.009] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 10s native | 44 | 1.000 [1.000, 1.000] | 0.725 [0.676, 0.774] | -0.275 [-0.322, -0.227] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 10s unified | 44 | 0.768 [0.722, 0.815] | 0.783 [0.727, 0.840] | +0.015 [+0.005, +0.025] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 20s native | 44 | 1.001 [1.001, 1.001] | 0.548 [0.480, 0.617] | -0.453 [-0.523, -0.383] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 20s unified | 44 | 0.653 [0.607, 0.700] | 0.631 [0.552, 0.710] | -0.023 [-0.057, +0.012] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 5s native | 44 | 0.999 [0.999, 0.999] | 0.850 [0.819, 0.880] | -0.149 [-0.179, -0.119] |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 5s unified | 44 | 0.873 [0.843, 0.903] | 0.877 [0.845, 0.909] | +0.004 [+0.002, +0.005] |
| lag_local_tokens dtu attended_alignment NCE 3401 10s native | 44 | 0.907 [0.898, 0.917] | 0.692 [0.616, 0.768] | -0.216 [-0.283, -0.148] |
| lag_local_tokens dtu attended_alignment NCE 3401 10s unified | 44 | 0.709 [0.659, 0.760] | 0.724 [0.661, 0.788] | +0.015 [+0.002, +0.028] |
| lag_local_tokens dtu attended_alignment NCE 3407 10s native | 44 | 0.908 [0.898, 0.918] | 0.675 [0.595, 0.755] | -0.233 [-0.304, -0.163] |
| lag_local_tokens dtu attended_alignment NCE 3407 10s unified | 44 | 0.707 [0.655, 0.759] | 0.723 [0.660, 0.786] | +0.016 [+0.004, +0.029] |
| lag_local_tokens dtu attended_alignment NCE 3413 10s native | 44 | 0.907 [0.897, 0.917] | 0.679 [0.603, 0.754] | -0.228 [-0.297, -0.160] |
| lag_local_tokens dtu attended_alignment NCE 3413 10s unified | 44 | 0.707 [0.657, 0.757] | 0.722 [0.662, 0.782] | +0.015 [+0.003, +0.027] |
| lag_local_tokens dtu attended_alignment NCE 3401 20s native | 44 | 0.945 [0.939, 0.951] | 0.483 [0.389, 0.578] | -0.462 [-0.556, -0.368] |
| lag_local_tokens dtu attended_alignment NCE 3401 20s unified | 44 | 0.590 [0.539, 0.641] | 0.540 [0.456, 0.625] | -0.049 [-0.084, -0.015] |
| lag_local_tokens dtu attended_alignment NCE 3407 20s native | 44 | 0.945 [0.940, 0.951] | 0.472 [0.374, 0.570] | -0.473 [-0.564, -0.382] |
| lag_local_tokens dtu attended_alignment NCE 3407 20s unified | 44 | 0.584 [0.530, 0.637] | 0.534 [0.445, 0.624] | -0.049 [-0.087, -0.012] |
| lag_local_tokens dtu attended_alignment NCE 3413 20s native | 44 | 0.944 [0.938, 0.950] | 0.476 [0.380, 0.573] | -0.468 [-0.564, -0.371] |
| lag_local_tokens dtu attended_alignment NCE 3413 20s unified | 44 | 0.585 [0.535, 0.636] | 0.531 [0.447, 0.615] | -0.054 [-0.089, -0.019] |
| lag_local_tokens dtu attended_alignment NCE 3401 5s native | 44 | 0.873 [0.858, 0.888] | 0.819 [0.767, 0.871] | -0.054 [-0.092, -0.016] |
| lag_local_tokens dtu attended_alignment NCE 3401 5s unified | 44 | 0.839 [0.803, 0.875] | 0.844 [0.806, 0.881] | +0.005 [+0.003, +0.007] |
| lag_local_tokens dtu attended_alignment NCE 3407 5s native | 44 | 0.874 [0.859, 0.889] | 0.814 [0.762, 0.867] | -0.059 [-0.099, -0.019] |
| lag_local_tokens dtu attended_alignment NCE 3407 5s unified | 44 | 0.837 [0.799, 0.875] | 0.842 [0.803, 0.880] | +0.005 [+0.003, +0.007] |
| lag_local_tokens dtu attended_alignment NCE 3413 5s native | 44 | 0.872 [0.857, 0.888] | 0.813 [0.762, 0.865] | -0.059 [-0.097, -0.021] |
| lag_local_tokens dtu attended_alignment NCE 3413 5s unified | 44 | 0.840 [0.805, 0.874] | 0.844 [0.807, 0.881] | +0.005 [+0.003, +0.007] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 10s native | 44 | 0.729 [0.690, 0.769] | 0.786 [0.710, 0.862] | +0.057 [+0.020, +0.094] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 10s unified | 44 | 0.745 [0.698, 0.791] | 0.760 [0.703, 0.817] | +0.015 [+0.005, +0.026] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 20s native | 44 | 0.692 [0.656, 0.728] | 0.593 [0.499, 0.688] | -0.099 [-0.166, -0.032] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 20s unified | 44 | 0.630 [0.581, 0.680] | 0.599 [0.517, 0.682] | -0.031 [-0.063, +0.000] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 5s native | 44 | 0.852 [0.813, 0.891] | 0.898 [0.849, 0.948] | +0.046 [+0.034, +0.058] |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 5s unified | 44 | 0.862 [0.830, 0.894] | 0.866 [0.832, 0.900] | +0.004 [+0.002, +0.006] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 10s native | 67 | 1.000 [1.000, 1.000] | 1.014 [0.997, 1.030] | +0.014 [-0.002, +0.030] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 10s unified | 67 | 0.999 [0.987, 1.012] | 1.003 [0.989, 1.017] | +0.004 [+0.003, +0.005] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 20s native | 67 | 1.000 [1.000, 1.000] | 0.971 [0.942, 1.000] | -0.029 [-0.058, -0.001] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 20s unified | 67 | 0.984 [0.964, 1.004] | 1.001 [0.974, 1.027] | +0.017 [+0.009, +0.025] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 5s native | 67 | 1.000 [1.000, 1.000] | 0.998 [0.989, 1.008] | -0.002 [-0.011, +0.008] |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 5s unified | 67 | 1.003 [0.995, 1.010] | 1.003 [0.996, 1.011] | +0.001 [+0.000, +0.001] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 10s native | 67 | 0.960 [0.954, 0.965] | 0.933 [0.902, 0.964] | -0.027 [-0.054, +0.001] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 10s unified | 67 | 0.987 [0.970, 1.003] | 0.990 [0.972, 1.008] | +0.004 [+0.002, +0.005] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 10s native | 67 | 0.958 [0.953, 0.964] | 0.948 [0.916, 0.981] | -0.010 [-0.038, +0.018] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 10s unified | 67 | 0.987 [0.967, 1.006] | 0.991 [0.971, 1.011] | +0.004 [+0.003, +0.006] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 10s native | 67 | 0.961 [0.956, 0.967] | 0.934 [0.903, 0.966] | -0.027 [-0.053, +0.000] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 10s unified | 67 | 0.987 [0.971, 1.003] | 0.990 [0.974, 1.007] | +0.003 [+0.002, +0.004] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 20s native | 67 | 0.968 [0.964, 0.972] | 0.849 [0.799, 0.899] | -0.119 [-0.167, -0.071] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 20s unified | 67 | 0.962 [0.937, 0.986] | 0.976 [0.945, 1.007] | +0.014 [+0.006, +0.022] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 20s native | 67 | 0.965 [0.961, 0.969] | 0.868 [0.818, 0.918] | -0.097 [-0.145, -0.049] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 20s unified | 67 | 0.965 [0.938, 0.992] | 0.980 [0.943, 1.016] | +0.014 [+0.005, +0.024] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 20s native | 67 | 0.970 [0.966, 0.974] | 0.856 [0.806, 0.907] | -0.114 [-0.161, -0.066] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 20s unified | 67 | 0.966 [0.942, 0.990] | 0.979 [0.947, 1.010] | +0.013 [+0.005, +0.020] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 5s native | 67 | 0.956 [0.949, 0.964] | 0.973 [0.955, 0.992] | +0.017 [+0.005, +0.029] |
| lag_local_tokens fau alignment_plus_selection NCE 3401 5s unified | 67 | 0.996 [0.987, 1.005] | 0.997 [0.987, 1.006] | +0.001 [+0.000, +0.001] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 5s native | 67 | 0.957 [0.950, 0.964] | 0.985 [0.966, 1.003] | +0.028 [+0.015, +0.040] |
| lag_local_tokens fau alignment_plus_selection NCE 3407 5s unified | 67 | 0.996 [0.985, 1.007] | 0.997 [0.986, 1.008] | +0.001 [+0.001, +0.001] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 5s native | 67 | 0.958 [0.951, 0.965] | 0.975 [0.957, 0.994] | +0.017 [+0.005, +0.029] |
| lag_local_tokens fau alignment_plus_selection NCE 3413 5s unified | 67 | 0.996 [0.987, 1.005] | 0.996 [0.987, 1.006] | +0.001 [+0.000, +0.001] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 10s native | 67 | 1.000 [1.000, 1.000] | 0.975 [0.960, 0.989] | -0.025 [-0.040, -0.011] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 10s unified | 67 | 0.981 [0.968, 0.993] | 0.982 [0.968, 0.995] | +0.001 [+0.000, +0.002] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 20s native | 67 | 1.000 [1.000, 1.000] | 0.915 [0.888, 0.943] | -0.085 [-0.112, -0.058] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 20s unified | 67 | 0.963 [0.944, 0.982] | 0.967 [0.942, 0.992] | +0.004 [-0.003, +0.011] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 5s native | 67 | 1.000 [1.000, 1.000] | 0.980 [0.971, 0.988] | -0.020 [-0.028, -0.012] |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 5s unified | 67 | 0.991 [0.984, 0.998] | 0.991 [0.984, 0.998] | +0.000 [+0.000, +0.000] |
| lag_local_tokens fau attended_alignment NCE 3401 10s native | 67 | 0.985 [0.982, 0.987] | 0.972 [0.943, 1.001] | -0.013 [-0.040, +0.013] |
| lag_local_tokens fau attended_alignment NCE 3401 10s unified | 67 | 0.986 [0.971, 1.001] | 0.989 [0.973, 1.005] | +0.003 [+0.002, +0.004] |
| lag_local_tokens fau attended_alignment NCE 3407 10s native | 67 | 0.986 [0.983, 0.988] | 0.972 [0.942, 1.003] | -0.013 [-0.040, +0.014] |
| lag_local_tokens fau attended_alignment NCE 3407 10s unified | 67 | 0.985 [0.968, 1.003] | 0.989 [0.971, 1.007] | +0.004 [+0.002, +0.005] |
| lag_local_tokens fau attended_alignment NCE 3413 10s native | 67 | 0.985 [0.982, 0.987] | 0.968 [0.939, 0.997] | -0.016 [-0.043, +0.010] |
| lag_local_tokens fau attended_alignment NCE 3413 10s unified | 67 | 0.986 [0.970, 1.001] | 0.988 [0.972, 1.004] | +0.003 [+0.001, +0.004] |
| lag_local_tokens fau attended_alignment NCE 3401 20s native | 67 | 0.992 [0.991, 0.994] | 0.930 [0.882, 0.978] | -0.062 [-0.108, -0.016] |
| lag_local_tokens fau attended_alignment NCE 3401 20s unified | 67 | 0.966 [0.943, 0.989] | 0.980 [0.949, 1.011] | +0.013 [+0.005, +0.022] |
| lag_local_tokens fau attended_alignment NCE 3407 20s native | 67 | 0.993 [0.992, 0.995] | 0.936 [0.888, 0.985] | -0.057 [-0.104, -0.010] |
| lag_local_tokens fau attended_alignment NCE 3407 20s unified | 67 | 0.963 [0.938, 0.989] | 0.977 [0.943, 1.010] | +0.013 [+0.005, +0.022] |
| lag_local_tokens fau attended_alignment NCE 3413 20s native | 67 | 0.992 [0.990, 0.993] | 0.930 [0.881, 0.979] | -0.061 [-0.109, -0.013] |
| lag_local_tokens fau attended_alignment NCE 3413 20s unified | 67 | 0.967 [0.945, 0.989] | 0.977 [0.948, 1.007] | +0.010 [+0.003, +0.018] |
| lag_local_tokens fau attended_alignment NCE 3401 5s native | 67 | 0.979 [0.975, 0.983] | 0.990 [0.973, 1.007] | +0.011 [-0.002, +0.023] |
| lag_local_tokens fau attended_alignment NCE 3401 5s unified | 67 | 0.996 [0.987, 1.004] | 0.996 [0.987, 1.005] | +0.001 [+0.000, +0.001] |
| lag_local_tokens fau attended_alignment NCE 3407 5s native | 67 | 0.979 [0.975, 0.983] | 0.989 [0.973, 1.006] | +0.010 [-0.003, +0.023] |
| lag_local_tokens fau attended_alignment NCE 3407 5s unified | 67 | 0.995 [0.985, 1.005] | 0.996 [0.985, 1.007] | +0.001 [+0.001, +0.001] |
| lag_local_tokens fau attended_alignment NCE 3413 5s native | 67 | 0.978 [0.974, 0.983] | 0.987 [0.971, 1.003] | +0.009 [-0.004, +0.021] |
| lag_local_tokens fau attended_alignment NCE 3413 5s unified | 67 | 0.995 [0.987, 1.004] | 0.996 [0.987, 1.004] | +0.000 [+0.000, +0.001] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 10s native | 67 | 0.909 [0.896, 0.922] | 0.935 [0.911, 0.960] | +0.026 [+0.015, +0.038] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 10s unified | 67 | 0.985 [0.972, 0.997] | 0.986 [0.972, 0.999] | +0.001 [+0.000, +0.002] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 20s native | 67 | 0.851 [0.840, 0.863] | 0.856 [0.818, 0.894] | +0.004 [-0.024, +0.033] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 20s unified | 67 | 0.966 [0.949, 0.984] | 0.971 [0.946, 0.995] | +0.004 [-0.003, +0.011] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 5s native | 67 | 0.956 [0.945, 0.967] | 0.968 [0.953, 0.982] | +0.011 [+0.008, +0.014] |
| lag_local_tokens fau selection_only SELECTION_CE 3401 5s unified | 67 | 0.993 [0.986, 1.000] | 0.993 [0.986, 1.001] | +0.000 [+0.000, +0.000] |

### 1.4 Diagnostics of the legacy integrator (identity means over test windows)

pos+ / pos− = share of test windows whose legacy decision is set by the swap-invariant part s of its logit (strictly s > |a| / s < −|a|), i.e. by candidate position, not by d. Exact identity: fixed − paired = ½(pos+ − pos−).

| cell | readout | pos+ | pos− | fixed−paired | ½(pos+−pos−) |
|---|---|---|---|---|---|
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 10s | unified | 0.016 | 0.006 | 0.005 | 0.005 |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 20s | unified | 0.006 | 0.012 | -0.003 | -0.003 |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 5s | native | 0.829 | 0.000 | 0.414 | 0.414 |
| complement_policy dtu alignment_plus_selection CS_SINGLE 3401 5s | unified | 0.001 | 0.011 | -0.005 | -0.005 |
| complement_policy dtu alignment_plus_selection NCE 3401 10s | native | 0.070 | 0.000 | 0.035 | 0.035 |
| complement_policy dtu alignment_plus_selection NCE 3401 10s | unified | 0.011 | 0.006 | 0.003 | 0.003 |
| complement_policy dtu alignment_plus_selection NCE 3401 20s | native | 0.000 | 0.290 | -0.145 | -0.145 |
| complement_policy dtu alignment_plus_selection NCE 3401 20s | unified | 0.003 | 0.018 | -0.007 | -0.007 |
| complement_policy dtu alignment_plus_selection NCE 3401 5s | native | 0.008 | 0.003 | 0.003 | 0.003 |
| complement_policy dtu alignment_plus_selection NCE 3401 5s | unified | 0.000 | 0.010 | -0.005 | -0.005 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 10s | unified | 0.013 | 0.006 | 0.004 | 0.004 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 20s | unified | 0.001 | 0.018 | -0.009 | -0.009 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 5s | native | 0.815 | 0.000 | 0.407 | 0.407 |
| complement_policy dtu attended_alignment CS_SINGLE 3401 5s | unified | 0.000 | 0.015 | -0.007 | -0.007 |
| complement_policy dtu attended_alignment NCE 3401 10s | native | 0.100 | 0.000 | 0.050 | 0.050 |
| complement_policy dtu attended_alignment NCE 3401 10s | unified | 0.012 | 0.006 | 0.003 | 0.003 |
| complement_policy dtu attended_alignment NCE 3401 20s | native | 0.000 | 0.449 | -0.225 | -0.225 |
| complement_policy dtu attended_alignment NCE 3401 20s | unified | 0.006 | 0.015 | -0.005 | -0.005 |
| complement_policy dtu attended_alignment NCE 3401 5s | native | 0.008 | 0.002 | 0.003 | 0.003 |
| complement_policy dtu attended_alignment NCE 3401 5s | unified | 0.000 | 0.010 | -0.005 | -0.005 |
| complement_policy dtu selection_only SELECTION_CE 3401 10s | native | 0.023 | 0.002 | 0.011 | 0.011 |
| complement_policy dtu selection_only SELECTION_CE 3401 10s | unified | 0.021 | 0.006 | 0.007 | 0.007 |
| complement_policy dtu selection_only SELECTION_CE 3401 20s | native | 0.000 | 0.037 | -0.018 | -0.018 |
| complement_policy dtu selection_only SELECTION_CE 3401 20s | unified | 0.005 | 0.015 | -0.005 | -0.005 |
| complement_policy dtu selection_only SELECTION_CE 3401 5s | native | 0.006 | 0.005 | 0.000 | 0.000 |
| complement_policy dtu selection_only SELECTION_CE 3401 5s | unified | 0.000 | 0.013 | -0.007 | -0.007 |
| complement_policy fau alignment_plus_selection NCE 3401 10s | native | 0.000 | 0.014 | -0.007 | -0.007 |
| complement_policy fau alignment_plus_selection NCE 3401 10s | unified | 0.002 | 0.026 | -0.012 | -0.012 |
| complement_policy fau alignment_plus_selection NCE 3401 20s | native | 0.000 | 0.124 | -0.062 | -0.062 |
| complement_policy fau alignment_plus_selection NCE 3401 20s | unified | 0.008 | 0.000 | 0.004 | 0.004 |
| complement_policy fau alignment_plus_selection NCE 3401 5s | native | 0.023 | 0.000 | 0.012 | 0.012 |
| complement_policy fau alignment_plus_selection NCE 3401 5s | unified | 0.000 | 0.001 | -0.000 | -0.000 |
| complement_policy fau attended_alignment CS_SINGLE 3401 10s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| complement_policy fau attended_alignment CS_SINGLE 3401 10s | unified | 0.002 | 0.085 | -0.042 | -0.042 |
| complement_policy fau attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| complement_policy fau attended_alignment CS_SINGLE 3401 20s | unified | 0.061 | 0.000 | 0.031 | 0.031 |
| complement_policy fau attended_alignment CS_SINGLE 3401 5s | native | 0.000 | 0.549 | -0.275 | -0.275 |
| complement_policy fau attended_alignment CS_SINGLE 3401 5s | unified | 0.000 | 0.004 | -0.002 | -0.002 |
| complement_policy fau attended_alignment NCE 3401 10s | native | 0.099 | 0.006 | 0.046 | 0.046 |
| complement_policy fau attended_alignment NCE 3401 10s | unified | 0.005 | 0.045 | -0.020 | -0.020 |
| complement_policy fau attended_alignment NCE 3401 20s | native | 0.000 | 0.086 | -0.043 | -0.043 |
| complement_policy fau attended_alignment NCE 3401 20s | unified | 0.009 | 0.034 | -0.012 | -0.012 |
| complement_policy fau attended_alignment NCE 3401 5s | native | 0.027 | 0.000 | 0.014 | 0.014 |
| complement_policy fau attended_alignment NCE 3401 5s | unified | 0.001 | 0.010 | -0.005 | -0.005 |
| complement_policy fau selection_only SELECTION_CE 3401 10s | native | 0.000 | 0.047 | -0.024 | -0.024 |
| complement_policy fau selection_only SELECTION_CE 3401 10s | unified | 0.000 | 0.075 | -0.038 | -0.038 |
| complement_policy fau selection_only SELECTION_CE 3401 20s | native | 0.000 | 0.235 | -0.117 | -0.117 |
| complement_policy fau selection_only SELECTION_CE 3401 20s | unified | 0.051 | 0.024 | 0.013 | 0.013 |
| complement_policy fau selection_only SELECTION_CE 3401 5s | native | 0.014 | 0.000 | 0.007 | 0.007 |
| complement_policy fau selection_only SELECTION_CE 3401 5s | unified | 0.005 | 0.000 | 0.003 | 0.003 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 10s | unified | 0.186 | 0.005 | 0.090 | 0.090 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 20s | unified | 0.029 | 0.195 | -0.083 | -0.083 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 5s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| dense_fm_policy dtu alignment_plus_selection CS_SINGLE 3401 5s | unified | 0.000 | 0.233 | -0.116 | -0.116 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 10s | native | 0.046 | 0.015 | 0.015 | 0.015 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 10s | unified | 0.040 | 0.002 | 0.019 | 0.019 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 20s | native | 0.002 | 0.169 | -0.084 | -0.084 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 20s | unified | 0.017 | 0.038 | -0.010 | -0.010 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 5s | native | 0.016 | 0.009 | 0.004 | 0.004 |
| dense_fm_policy dtu alignment_plus_selection NCE 3401 5s | unified | 0.001 | 0.023 | -0.011 | -0.011 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 10s | unified | 0.314 | 0.009 | 0.152 | 0.152 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 20s | unified | 0.022 | 0.217 | -0.097 | -0.097 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 5s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| dense_fm_policy dtu attended_alignment CS_SINGLE 3401 5s | unified | 0.000 | 0.527 | -0.264 | -0.264 |
| dense_fm_policy dtu attended_alignment NCE 3401 10s | native | 0.056 | 0.009 | 0.023 | 0.023 |
| dense_fm_policy dtu attended_alignment NCE 3401 10s | unified | 0.042 | 0.003 | 0.019 | 0.019 |
| dense_fm_policy dtu attended_alignment NCE 3401 20s | native | 0.001 | 0.200 | -0.100 | -0.100 |
| dense_fm_policy dtu attended_alignment NCE 3401 20s | unified | 0.007 | 0.045 | -0.019 | -0.019 |
| dense_fm_policy dtu attended_alignment NCE 3401 5s | native | 0.016 | 0.007 | 0.004 | 0.004 |
| dense_fm_policy dtu attended_alignment NCE 3401 5s | unified | 0.001 | 0.031 | -0.015 | -0.015 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 10s | native | 0.025 | 0.001 | 0.012 | 0.012 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 10s | unified | 0.291 | 0.045 | 0.123 | 0.123 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 20s | native | 0.000 | 0.124 | -0.062 | -0.062 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 20s | unified | 0.027 | 0.300 | -0.136 | -0.136 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 5s | native | 0.008 | 0.002 | 0.003 | 0.003 |
| dense_fm_policy dtu selection_only SELECTION_CE 3401 5s | unified | 0.000 | 0.399 | -0.199 | -0.199 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 10s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 10s | unified | 0.000 | 0.405 | -0.203 | -0.203 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 20s | unified | 0.011 | 0.069 | -0.029 | -0.029 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 5s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| dense_fm_policy fau alignment_plus_selection CS_SINGLE 3401 5s | unified | 0.000 | 0.073 | -0.036 | -0.036 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 10s | native | 0.061 | 0.000 | 0.031 | 0.031 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 10s | unified | 0.000 | 0.092 | -0.046 | -0.046 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 20s | native | 0.000 | 0.034 | -0.017 | -0.017 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 20s | unified | 0.000 | 0.076 | -0.038 | -0.038 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 5s | native | 0.005 | 0.000 | 0.003 | 0.003 |
| dense_fm_policy fau alignment_plus_selection NCE 3401 5s | unified | 0.000 | 0.034 | -0.017 | -0.017 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 10s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 10s | unified | 0.000 | 0.430 | -0.215 | -0.215 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 20s | unified | 0.017 | 0.415 | -0.199 | -0.199 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 5s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| dense_fm_policy fau attended_alignment CS_SINGLE 3401 5s | unified | 0.000 | 0.119 | -0.059 | -0.059 |
| dense_fm_policy fau attended_alignment NCE 3401 10s | native | 0.020 | 0.014 | 0.003 | 0.003 |
| dense_fm_policy fau attended_alignment NCE 3401 10s | unified | 0.002 | 0.044 | -0.021 | -0.021 |
| dense_fm_policy fau attended_alignment NCE 3401 20s | native | 0.000 | 0.091 | -0.046 | -0.046 |
| dense_fm_policy fau attended_alignment NCE 3401 20s | unified | 0.007 | 0.028 | -0.011 | -0.011 |
| dense_fm_policy fau attended_alignment NCE 3401 5s | native | 0.022 | 0.000 | 0.011 | 0.011 |
| dense_fm_policy fau attended_alignment NCE 3401 5s | unified | 0.000 | 0.021 | -0.011 | -0.011 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 10s | native | 0.008 | 0.000 | 0.004 | 0.004 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 10s | unified | 0.000 | 0.051 | -0.025 | -0.025 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 20s | native | 0.000 | 0.014 | -0.007 | -0.007 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 20s | unified | 0.009 | 0.120 | -0.056 | -0.056 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 5s | native | 0.015 | 0.000 | 0.008 | 0.008 |
| dense_fm_policy fau selection_only SELECTION_CE 3401 5s | unified | 0.000 | 0.151 | -0.076 | -0.076 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 10s | unified | 0.010 | 0.006 | 0.002 | 0.002 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 20s | unified | 0.006 | 0.012 | -0.003 | -0.003 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 5s | native | 0.815 | 0.000 | 0.408 | 0.408 |
| lag_local_tokens dtu alignment_plus_selection CS_SINGLE 3401 5s | unified | 0.001 | 0.010 | -0.005 | -0.005 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 10s | native | 0.060 | 0.000 | 0.030 | 0.030 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 10s | unified | 0.009 | 0.005 | 0.002 | 0.002 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 20s | native | 0.000 | 0.256 | -0.128 | -0.128 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 20s | unified | 0.004 | 0.012 | -0.004 | -0.004 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 5s | native | 0.009 | 0.002 | 0.004 | 0.004 |
| lag_local_tokens dtu alignment_plus_selection NCE 3401 5s | unified | 0.001 | 0.010 | -0.005 | -0.005 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 10s | native | 0.029 | 0.001 | 0.014 | 0.014 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 10s | unified | 0.004 | 0.008 | -0.002 | -0.002 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 20s | native | 0.018 | 0.122 | -0.052 | -0.052 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 20s | unified | 0.023 | 0.001 | 0.011 | 0.011 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 5s | native | 0.043 | 0.000 | 0.021 | 0.021 |
| lag_local_tokens dtu alignment_plus_selection NCE 3407 5s | unified | 0.000 | 0.012 | -0.006 | -0.006 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 10s | native | 0.001 | 0.028 | -0.013 | -0.013 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 10s | unified | 0.008 | 0.006 | 0.001 | 0.001 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 20s | native | 0.001 | 0.087 | -0.043 | -0.043 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 20s | unified | 0.007 | 0.017 | -0.005 | -0.005 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 5s | native | 0.001 | 0.008 | -0.003 | -0.003 |
| lag_local_tokens dtu alignment_plus_selection NCE 3413 5s | unified | 0.004 | 0.002 | 0.001 | 0.001 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 10s | native | 1.000 | 0.000 | 0.500 | 0.500 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 10s | unified | 0.015 | 0.004 | 0.006 | 0.006 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 20s | unified | 0.002 | 0.015 | -0.007 | -0.007 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 5s | native | 0.824 | 0.000 | 0.412 | 0.412 |
| lag_local_tokens dtu attended_alignment CS_SINGLE 3401 5s | unified | 0.000 | 0.016 | -0.008 | -0.008 |
| lag_local_tokens dtu attended_alignment NCE 3401 10s | native | 0.100 | 0.000 | 0.050 | 0.050 |
| lag_local_tokens dtu attended_alignment NCE 3401 10s | unified | 0.014 | 0.006 | 0.004 | 0.004 |
| lag_local_tokens dtu attended_alignment NCE 3401 20s | native | 0.000 | 0.471 | -0.236 | -0.236 |
| lag_local_tokens dtu attended_alignment NCE 3401 20s | unified | 0.005 | 0.016 | -0.005 | -0.005 |
| lag_local_tokens dtu attended_alignment NCE 3401 5s | native | 0.008 | 0.002 | 0.003 | 0.003 |
| lag_local_tokens dtu attended_alignment NCE 3401 5s | unified | 0.000 | 0.011 | -0.005 | -0.005 |
| lag_local_tokens dtu attended_alignment NCE 3407 10s | native | 0.053 | 0.000 | 0.026 | 0.026 |
| lag_local_tokens dtu attended_alignment NCE 3407 10s | unified | 0.003 | 0.012 | -0.005 | -0.005 |
| lag_local_tokens dtu attended_alignment NCE 3407 20s | native | 0.039 | 0.186 | -0.073 | -0.073 |
| lag_local_tokens dtu attended_alignment NCE 3407 20s | unified | 0.020 | 0.000 | 0.010 | 0.010 |
| lag_local_tokens dtu attended_alignment NCE 3407 5s | native | 0.061 | 0.000 | 0.031 | 0.031 |
| lag_local_tokens dtu attended_alignment NCE 3407 5s | unified | 0.001 | 0.009 | -0.004 | -0.004 |
| lag_local_tokens dtu attended_alignment NCE 3413 10s | native | 0.002 | 0.053 | -0.025 | -0.025 |
| lag_local_tokens dtu attended_alignment NCE 3413 10s | unified | 0.008 | 0.006 | 0.001 | 0.001 |
| lag_local_tokens dtu attended_alignment NCE 3413 20s | native | 0.000 | 0.164 | -0.082 | -0.082 |
| lag_local_tokens dtu attended_alignment NCE 3413 20s | unified | 0.010 | 0.015 | -0.002 | -0.002 |
| lag_local_tokens dtu attended_alignment NCE 3413 5s | native | 0.001 | 0.008 | -0.004 | -0.004 |
| lag_local_tokens dtu attended_alignment NCE 3413 5s | unified | 0.006 | 0.002 | 0.002 | 0.002 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 10s | native | 0.024 | 0.001 | 0.011 | 0.011 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 10s | unified | 0.014 | 0.007 | 0.004 | 0.004 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 20s | native | 0.000 | 0.049 | -0.024 | -0.024 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 20s | unified | 0.003 | 0.014 | -0.006 | -0.006 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 5s | native | 0.005 | 0.004 | 0.000 | 0.000 |
| lag_local_tokens dtu selection_only SELECTION_CE 3401 5s | unified | 0.000 | 0.015 | -0.007 | -0.007 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 10s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 10s | unified | 0.004 | 0.053 | -0.025 | -0.025 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 20s | unified | 0.014 | 0.033 | -0.010 | -0.010 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 5s | native | 0.418 | 0.543 | -0.062 | -0.062 |
| lag_local_tokens fau alignment_plus_selection CS_SINGLE 3401 5s | unified | 0.001 | 0.008 | -0.003 | -0.003 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 10s | native | 0.058 | 0.034 | 0.012 | 0.012 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 10s | unified | 0.001 | 0.048 | -0.024 | -0.024 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 20s | native | 0.001 | 0.354 | -0.177 | -0.177 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 20s | unified | 0.011 | 0.034 | -0.012 | -0.012 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 5s | native | 0.011 | 0.000 | 0.005 | 0.005 |
| lag_local_tokens fau alignment_plus_selection NCE 3401 5s | unified | 0.001 | 0.009 | -0.004 | -0.004 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 10s | native | 0.000 | 0.292 | -0.146 | -0.146 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 10s | unified | 0.000 | 0.043 | -0.022 | -0.022 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 20s | native | 0.000 | 0.675 | -0.338 | -0.338 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 20s | unified | 0.001 | 0.086 | -0.042 | -0.042 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 5s | native | 0.070 | 0.000 | 0.035 | 0.035 |
| lag_local_tokens fau alignment_plus_selection NCE 3407 5s | unified | 0.015 | 0.000 | 0.008 | 0.008 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 10s | native | 0.071 | 0.010 | 0.030 | 0.030 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 10s | unified | 0.015 | 0.017 | -0.001 | -0.001 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 20s | native | 0.097 | 0.097 | -0.000 | -0.000 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 20s | unified | 0.019 | 0.010 | 0.005 | 0.005 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 5s | native | 0.002 | 0.021 | -0.010 | -0.010 |
| lag_local_tokens fau alignment_plus_selection NCE 3413 5s | unified | 0.002 | 0.012 | -0.005 | -0.005 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 10s | native | 0.500 | 0.500 | 0.000 | 0.000 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 10s | unified | 0.003 | 0.053 | -0.025 | -0.025 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 20s | native | 0.000 | 1.000 | -0.500 | -0.500 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 20s | unified | 0.015 | 0.040 | -0.012 | -0.012 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 5s | native | 0.418 | 0.471 | -0.026 | -0.026 |
| lag_local_tokens fau attended_alignment CS_SINGLE 3401 5s | unified | 0.001 | 0.009 | -0.004 | -0.004 |
| lag_local_tokens fau attended_alignment NCE 3401 10s | native | 0.106 | 0.060 | 0.023 | 0.023 |
| lag_local_tokens fau attended_alignment NCE 3401 10s | unified | 0.001 | 0.051 | -0.025 | -0.025 |
| lag_local_tokens fau attended_alignment NCE 3401 20s | native | 0.000 | 0.552 | -0.276 | -0.276 |
| lag_local_tokens fau attended_alignment NCE 3401 20s | unified | 0.015 | 0.037 | -0.011 | -0.011 |
| lag_local_tokens fau attended_alignment NCE 3401 5s | native | 0.016 | 0.000 | 0.008 | 0.008 |
| lag_local_tokens fau attended_alignment NCE 3401 5s | unified | 0.001 | 0.010 | -0.004 | -0.004 |
| lag_local_tokens fau attended_alignment NCE 3407 10s | native | 0.000 | 0.522 | -0.261 | -0.261 |
| lag_local_tokens fau attended_alignment NCE 3407 10s | unified | 0.000 | 0.057 | -0.029 | -0.029 |
| lag_local_tokens fau attended_alignment NCE 3407 20s | native | 0.000 | 0.963 | -0.482 | -0.482 |
| lag_local_tokens fau attended_alignment NCE 3407 20s | unified | 0.000 | 0.094 | -0.047 | -0.047 |
| lag_local_tokens fau attended_alignment NCE 3407 5s | native | 0.104 | 0.000 | 0.052 | 0.052 |
| lag_local_tokens fau attended_alignment NCE 3407 5s | unified | 0.017 | 0.000 | 0.008 | 0.008 |
| lag_local_tokens fau attended_alignment NCE 3413 10s | native | 0.115 | 0.015 | 0.050 | 0.050 |
| lag_local_tokens fau attended_alignment NCE 3413 10s | unified | 0.016 | 0.020 | -0.002 | -0.002 |
| lag_local_tokens fau attended_alignment NCE 3413 20s | native | 0.241 | 0.151 | 0.045 | 0.045 |
| lag_local_tokens fau attended_alignment NCE 3413 20s | unified | 0.017 | 0.009 | 0.004 | 0.004 |
| lag_local_tokens fau attended_alignment NCE 3413 5s | native | 0.003 | 0.034 | -0.016 | -0.016 |
| lag_local_tokens fau attended_alignment NCE 3413 5s | unified | 0.002 | 0.014 | -0.006 | -0.006 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 10s | native | 0.016 | 0.011 | 0.002 | 0.002 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 10s | unified | 0.005 | 0.070 | -0.032 | -0.032 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 20s | native | 0.010 | 0.063 | -0.027 | -0.027 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 20s | unified | 0.016 | 0.045 | -0.014 | -0.014 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 5s | native | 0.005 | 0.001 | 0.002 | 0.002 |
| lag_local_tokens fau selection_only SELECTION_CE 3401 5s | unified | 0.002 | 0.012 | -0.005 | -0.005 |

Antisymmetric fits per arm × window × readout over included units (status counts; among `ok` fits: 5 s weight sum ≤ 0, max |sym|/|antisym| of the paired-trained h on training windows, max lbfgs iterations): complement_policy|10s|native: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 7.3e-10, n_iter ≤ 12; complement_policy|10s|unified: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 4.0e-15, n_iter ≤ 10; complement_policy|20s|native: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 1.5e-07, n_iter ≤ 18; complement_policy|20s|unified: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 1.4e-08, n_iter ≤ 18; complement_policy|5s|native: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 2.1e-13, n_iter ≤ 9; complement_policy|5s|unified: n=55, ok 55, w-sum ≤ 0 0, sym/antisym 1.1e-16, n_iter ≤ 7; dense_fm_policy|10s|native: n=58, ok 58, w-sum ≤ 0 0, sym/antisym 8.7e-11, n_iter ≤ 15; dense_fm_policy|10s|unified: n=58, ok 58, w-sum ≤ 0 0, sym/antisym 1.6e-14, n_iter ≤ 11; dense_fm_policy|20s|native: n=58, ok 58, w-sum ≤ 0 0, sym/antisym 3.0e-07, n_iter ≤ 20; dense_fm_policy|20s|unified: n=58, ok 58, w-sum ≤ 0 0, sym/antisym 1.3e-06, n_iter ≤ 17; dense_fm_policy|5s|native: n=58, ok 58, w-sum ≤ 0 0, sym/antisym 6.1e-15, n_iter ≤ 12; dense_fm_policy|5s|unified: n=58, ok 58, w-sum ≤ 0 21, sym/antisym 7.0e-15, n_iter ≤ 8; lag_local_tokens|10s|native: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 1.3e-13, n_iter ≤ 12; lag_local_tokens|10s|unified: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 8.1e-15, n_iter ≤ 10; lag_local_tokens|20s|native: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 1.0e-07, n_iter ≤ 19; lag_local_tokens|20s|unified: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 3.6e-07, n_iter ≤ 19; lag_local_tokens|5s|native: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 2.4e-16, n_iter ≤ 9; lag_local_tokens|5s|unified: n=180, ok 180, w-sum ≤ 0 0, sym/antisym 3.9e-16, n_iter ≤ 7.

Exclusions from a contrast (unit × participant × window × readout cells; status of the candidate's fit or a missing legacy integrator; both sides of the contrast drop the cell): none. Full list in the JSON.

### 1.5 Between-seed range (lag panel cells; per-seed estimates)

| family · cell · window | per seed | min | max |
|---|---|---|---|
| AO-ANTISYM · dtu · alignment_plus_selection · NCE · 10s | 3401: -0.000, 3407: -0.002, 3413: -0.000 | -0.002 | -0.000 |
| AO-ANTISYM · dtu · alignment_plus_selection · NCE · 20s | 3401: -0.003, 3407: -0.004, 3413: -0.004 | -0.004 | -0.003 |
| AO-ANTISYM · dtu · alignment_plus_selection · NCE · 5s | 3401: +0.000, 3407: +0.000, 3413: +0.000 | +0.000 | +0.000 |
| AO-ANTISYM · dtu · attended_alignment · NCE · 10s | 3401: -0.001, 3407: +0.000, 3413: -0.002 | -0.002 | +0.000 |
| AO-ANTISYM · dtu · attended_alignment · NCE · 20s | 3401: -0.003, 3407: -0.001, 3413: +0.003 | -0.003 | +0.003 |
| AO-ANTISYM · dtu · attended_alignment · NCE · 5s | 3401: +0.000, 3407: +0.000, 3413: +0.000 | +0.000 | +0.000 |
| AO-ANTISYM · fau · alignment_plus_selection · NCE · 10s | 3401: +0.000, 3407: +0.002, 3413: -0.001 | -0.001 | +0.002 |
| AO-ANTISYM · fau · alignment_plus_selection · NCE · 20s | 3401: -0.001, 3407: +0.000, 3413: -0.002 | -0.002 | +0.000 |
| AO-ANTISYM · fau · alignment_plus_selection · NCE · 5s | 3401: +0.000, 3407: +0.000, 3413: +0.000 | +0.000 | +0.000 |
| AO-ANTISYM · fau · attended_alignment · NCE · 10s | 3401: -0.004, 3407: -0.001, 3413: +0.004 | -0.004 | +0.004 |
| AO-ANTISYM · fau · attended_alignment · NCE · 20s | 3401: -0.003, 3407: -0.000, 3413: -0.002 | -0.003 | -0.000 |
| AO-ANTISYM · fau · attended_alignment · NCE · 5s | 3401: +0.000, 3407: +0.000, 3413: +0.000 | +0.000 | +0.000 |
| AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 10s | 3401: -0.001, 3407: -0.000, 3413: -0.001 | -0.001 | -0.000 |
| AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 20s | 3401: -0.016, 3407: -0.012, 3413: -0.011 | -0.016 | -0.011 |
| AO-PAIRED-LEGACY · dtu · alignment_plus_selection · NCE · 5s | 3401: -0.001, 3407: +0.000, 3413: +0.000 | -0.001 | +0.000 |
| AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 10s | 3401: -0.000, 3407: +0.001, 3413: -0.002 | -0.002 | +0.001 |
| AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 20s | 3401: -0.005, 3407: -0.009, 3413: -0.008 | -0.009 | -0.005 |
| AO-PAIRED-LEGACY · dtu · attended_alignment · NCE · 5s | 3401: +0.000, 3407: -0.000, 3413: -0.000 | -0.000 | +0.000 |
| AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 10s | 3401: -0.002, 3407: +0.001, 3413: -0.001 | -0.002 | +0.001 |
| AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 20s | 3401: -0.008, 3407: -0.003, 3413: -0.006 | -0.008 | -0.003 |
| AO-PAIRED-LEGACY · fau · alignment_plus_selection · NCE · 5s | 3401: +0.000, 3407: -0.000, 3413: -0.000 | -0.000 | +0.000 |
| AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 10s | 3401: -0.004, 3407: -0.002, 3413: +0.005 | -0.004 | +0.005 |
| AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 20s | 3401: -0.005, 3407: -0.002, 3413: -0.007 | -0.007 | -0.002 |
| AO-PAIRED-LEGACY · fau · attended_alignment · NCE · 5s | 3401: -0.000, 3407: +0.000, 3413: +0.000 | -0.000 | +0.000 |

Seed-mean coverage (identities present in all three seeds): {'AO-ANTISYM|lag_local_tokens|dtu|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|dtu|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|dtu|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|dtu|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|dtu|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|dtu|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-ANTISYM|lag_local_tokens|fau|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-ANTISYM|lag_local_tokens|fau|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-ANTISYM|lag_local_tokens|fau|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-ANTISYM|lag_local_tokens|fau|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-ANTISYM|lag_local_tokens|fau|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-ANTISYM|lag_local_tokens|fau|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|dtu|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-PAIRED-LEGACY|lag_local_tokens|fau|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|dtu|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|dtu|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|dtu|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|dtu|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|dtu|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|dtu|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 44, 'acc_native': 44}, '3401': 44, '3407': 44, '3413': 44}, 'AO-FIXED|lag_local_tokens|fau|alignment_plus_selection|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|fau|alignment_plus_selection|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|fau|alignment_plus_selection|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|fau|attended_alignment|NCE|5s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|fau|attended_alignment|NCE|10s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}, 'AO-FIXED|lag_local_tokens|fau|attended_alignment|NCE|20s': {'identities_all_seeds': {'acc': 67, 'acc_native': 67}, '3401': 67, '3407': 67, '3413': 67}}

## 2. 当前工作判断

- Mechanical summary only (fixed rules of the analysis note §6 and §11): the class counts above per family type, arm and seed, favourable and unfavourable alike; no generalisation beyond this recipe (5 fixed summaries, linear logistic, C = 1, these models). mean_score results (AT-LEVEL / AT-LENGTH / AT-TASK) are unaffected by the order correction.
- 5 s windows contain one segment: the learned integrators are thresholds there, and the antisymmetric one equals mean_score whenever its coefficient sum is positive (count of exceptions in §1.4); 5 s cells are a check, not evidence about temporal integration.

## 3. 仍竞争的解释

- Candidate position: the swap-invariant part of the legacy logit (intercept, sd, range terms) decides the pos± share of test windows (§1.4). For native CS the saved intercepts equal logit(label-1 share) of the shared flip stream (note §11.11).
- A weak or wrongly weighted swap-antisymmetric part of the summaries: visible in AO-ANTISYM after the position term is removed.
- If AO-PAIRED-LEGACY native cells stay below chance, the old native anomaly is not explained by candidate order alone.

## 4. 下一轮干预

- Package docs/04 §B alternatives, not run here and without a performance gate: h reweighting d by swap-invariant quantities such as |d|; same-window method comparisons at 5/10/20 s.

## 5. 复用与运行

- Reused: the unit records and saved checkpoints (no retraining, no backbone refit). New: per-unit score extraction (stage 1, device-matched) and this CPU analysis. Notes: 0 (see JSON).

## 6. 暂不决定

- Placement of the corrected integrator rows (main text / appendix) is not decided here and does not block further experiments.
