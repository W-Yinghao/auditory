# GX 结果汇总（数值；解释见 GX_ANALYSIS.md）

## GX1 跨儿童 vs 儿童内（儿童均值 AUC；seed 范围）

| lane | model | children | AUC mean | median | IQR | >0.5 | seed range | J bits | pitch AUC |
|---|---|---|---|---|---|---|---|---|---|
| bdf_puretone | adapt_finetuned | 67 | 0.559 | 0.561 | [0.517, 0.606] | 55/67 | 0.556–0.562 | +0.0068 |  |
| bdf_puretone | adapt_zero_shot | 67 | 0.556 | 0.553 | [0.512, 0.602] | 55/67 | 0.553–0.559 | +0.0055 |  |
| bdf_puretone | child_spatial | 70 | 0.525 | 0.521 | [0.506, 0.540] | 57/70 | 0.523–0.527 | -0.0042 |  |
| bdf_puretone | child_spatial_meanfilter | 70 | 0.533 | 0.532 | [0.507, 0.554] | 55/70 | 0.529–0.535 | +0.0015 |  |
| bdf_puretone | film_age | 57 | 0.544 | 0.540 | [0.512, 0.576] | 48/57 | 0.544–0.545 | +0.0023 |  |
| bdf_puretone | film_age_shuffled | 57 | 0.545 | 0.540 | [0.514, 0.582] | 49/57 | 0.544–0.545 | +0.0026 |  |
| bdf_puretone | per_child | 70 | 0.528 | 0.521 | [0.507, 0.532] | 61/70 | 0.528–0.529 | -0.0059 |  |
| bdf_puretone | shared | 73 | 0.556 | 0.551 | [0.521, 0.595] | 64/73 | 0.555–0.557 | +0.0057 |  |
| bdf_puretone_adabn | adabn_recalibrated | 73 | 0.556 | 0.550 | [0.522, 0.594] | 64/73 | 0.555–0.557 | +0.0060 |  |
| bdf_puretone_adabn | adabn_zero_shot | 73 | 0.556 | 0.551 | [0.521, 0.595] | 64/73 | 0.555–0.557 | +0.0057 |  |
| bdf_puretone_shared_big | shared | 73 | 0.553 | 0.549 | [0.519, 0.589] | 61/73 | 0.550–0.557 | +0.0042 |  |
| bdf_puretone_shared_postonly | shared | 73 | 0.555 | 0.551 | [0.517, 0.585] | 62/73 | 0.552–0.560 | +0.0053 |  |
| bdf_puretone_shared_preonly | shared | 73 | 0.508 | 0.508 | [0.492, 0.520] | 45/73 | 0.506–0.509 | -0.0010 |  |
| mff_bapa | adapt_finetuned | 8 | 0.522 | 0.522 | [0.517, 0.537] | 7/8 | 0.504–0.535 | -0.0024 |  |
| mff_bapa | adapt_zero_shot | 8 | 0.518 | 0.520 | [0.513, 0.536] | 7/8 | 0.504–0.530 | -0.0034 |  |
| mff_bapa | child_spatial | 20 | 0.508 | 0.508 | [0.502, 0.517] | 15/20 | 0.499–0.513 | -0.0135 |  |
| mff_bapa | child_spatial_meanfilter | 20 | 0.505 | 0.498 | [0.492, 0.514] | 8/20 | 0.496–0.511 | -0.0010 |  |
| mff_bapa | per_child | 20 | 0.506 | 0.507 | [0.491, 0.514] | 12/20 | 0.504–0.507 | -0.0227 |  |
| mff_bapa | shared | 27 | 0.510 | 0.514 | [0.494, 0.531] | 18/27 | 0.502–0.518 | -0.0096 |  |
| mff_puretone | adapt_finetuned | 12 | 0.526 | 0.526 | [0.503, 0.543] | 9/12 | 0.520–0.531 | -0.0010 |  |
| mff_puretone | adapt_zero_shot | 12 | 0.523 | 0.523 | [0.500, 0.538] | 9/12 | 0.517–0.530 | -0.0018 |  |
| mff_puretone | child_spatial | 27 | 0.508 | 0.503 | [0.493, 0.517] | 16/27 | 0.504–0.514 | -0.0112 |  |
| mff_puretone | child_spatial_meanfilter | 27 | 0.504 | 0.502 | [0.493, 0.513] | 18/27 | 0.501–0.507 | -0.0011 |  |
| mff_puretone | film_age | 27 | 0.511 | 0.510 | [0.496, 0.524] | 18/27 | 0.505–0.515 | -0.0102 |  |
| mff_puretone | film_age_shuffled | 27 | 0.511 | 0.511 | [0.496, 0.525] | 18/27 | 0.506–0.515 | -0.0104 |  |
| mff_puretone | per_child | 27 | 0.517 | 0.508 | [0.497, 0.527] | 16/27 | 0.516–0.519 | -0.0165 |  |
| mff_puretone | shared | 36 | 0.520 | 0.516 | [0.498, 0.535] | 27/36 | 0.509–0.527 | -0.0054 |  |
| mff_puretone_adabn | adabn_recalibrated | 36 | 0.521 | 0.518 | [0.497, 0.535] | 26/36 | 0.512–0.528 | -0.0039 |  |
| mff_puretone_adabn | adabn_zero_shot | 36 | 0.520 | 0.516 | [0.498, 0.535] | 27/36 | 0.509–0.527 | -0.0054 |  |
| mff_puretone_shared_big | shared | 36 | 0.525 | 0.518 | [0.497, 0.548] | 25/36 | 0.519–0.529 | -0.0076 |  |
| mff_puretone_shared_preonly | shared | 36 | 0.507 | 0.507 | [0.492, 0.520] | 22/36 | 0.502–0.510 | -0.0045 |  |
| mff_unknown_event | adapt_finetuned | 26 | 0.518 | 0.505 | [0.489, 0.549] | 14/26 | 0.513–0.521 | -0.0105 |  |
| mff_unknown_event | adapt_zero_shot | 26 | 0.516 | 0.507 | [0.487, 0.529] | 14/26 | 0.511–0.520 | -0.0131 |  |
| mff_unknown_event | child_spatial | 32 | 0.571 | 0.523 | [0.503, 0.554] | 25/32 | 0.568–0.575 | +0.0086 |  |
| mff_unknown_event | child_spatial_meanfilter | 32 | 0.531 | 0.511 | [0.502, 0.537] | 25/32 | 0.519–0.539 | -0.0012 |  |
| mff_unknown_event | film_age | 28 | 0.513 | 0.516 | [0.492, 0.534] | 18/28 | 0.510–0.518 | -0.0228 |  |
| mff_unknown_event | film_age_shuffled | 28 | 0.513 | 0.515 | [0.491, 0.534] | 17/28 | 0.506–0.521 | -0.0270 |  |
| mff_unknown_event | per_child | 32 | 0.548 | 0.513 | [0.501, 0.546] | 25/32 | 0.544–0.552 | +0.0196 |  |
| mff_unknown_event | shared | 44 | 0.526 | 0.519 | [0.498, 0.540] | 32/44 | 0.519–0.531 | -0.0438 |  |
| mff_unknown_hdev_ldev | adapt_finetuned | 14 | 0.544 | 0.542 | [0.534, 0.560] | 13/14 | 0.540–0.548 | +0.0047 | 0.548 |
| mff_unknown_hdev_ldev | adapt_zero_shot | 14 | 0.542 | 0.542 | [0.531, 0.554] | 13/14 | 0.539–0.547 | -0.0007 | 0.544 |
| mff_unknown_hdev_ldev | child_spatial | 14 | 0.507 | 0.506 | [0.499, 0.514] | 10/14 | 0.506–0.507 | -0.0110 | 0.505 |
| mff_unknown_hdev_ldev | child_spatial_meanfilter | 14 | 0.508 | 0.510 | [0.507, 0.511] | 12/14 | 0.503–0.511 | -0.0015 | 0.508 |
| mff_unknown_hdev_ldev | per_child | 14 | 0.503 | 0.503 | [0.502, 0.504] | 11/14 | 0.497–0.509 | -0.0105 | 0.503 |
| mff_unknown_hdev_ldev | shared | 15 | 0.549 | 0.551 | [0.539, 0.562] | 15/15 | 0.543–0.553 | +0.0051 | 0.556 |

## gx2_ssl

```
{
 "path": "results/auditory_gx/GX2_ssl_bdf/summary_ssl_HA_BDF_s11.json",
 "branch": "HA_BDF",
 "channels": 20,
 "final": {
  "masked_mse": 2.583648681640625,
  "r2_masked": 0.401389344002397,
  "step": 19999,
  "zero_baseline_mse": 4.316075325012207
 },
 "hours_in_bank": 15.506666666666666,
 "probes": {
  "age_ridge": {
   "baseline_mae_mean": 33.57550639884736,
   "mae_mean": 27.676105863947313,
   "per_seed": [
    {
     "baseline_mae": 33.531994236799726,
     "mae": 28.038246734485696,
     "n": 57,
     "r": 0.6218601166614195,
     "seed": 11
    },
    {
     "baseline_mae": 33.423129078735485,
     "mae": 26.65130252646797,
     "n": 57,
     "r": 0.6221082565918332,
     "seed": 22
    },
    {
     "baseline_mae": 33.77139588100686,
     "mae": 28.33876833088827,
     "n": 57,
     "r": 0.6138766035587041,
     "seed": 33
    }
   ]
  }
 },
 "records": 93,
 "run": "GX2_ssl_bdf",
 "steps": 20000,
 "window_samples": 1000,
 "windows": 13956
}
```
```
{
 "path": "results/auditory_gx/GX2_ssl_mff/summary_ssl_MFF_s11.json",
 "branch": "MFF",
 "channels": 128,
 "final": {
  "masked_mse": 5.610915660858154,
  "r2_masked": 0.4124009810709005,
  "step": 19999,
  "zero_baseline_mse": 9.548885345458984
 },
 "hours_in_bank": 31.137777777777778,
 "probes": {
  "age_ridge": {
   "baseline_mae_mean": 19.71264015601604,
   "mae_mean": 19.78526895596665,
   "per_seed": [
    {
     "baseline_mae": 19.798441479791233,
     "mae": 19.07584529553277,
     "n": 62,
     "r": 0.2463356001719765,
     "seed": 11
    },
    {
     "baseline_mae": 19.700869452371265,
     "mae": 20.57197004662869,
     "n": 62,
     "r": 0.08798896701288764,
     "seed": 22
    },
    {
     "baseline_mae": 19.638609535885625,
     "mae": 19.707991525738493,
     "n": 62,
     "r": 0.2155092826913778,
     "seed": 33
    }
   ]
  },
  "source_explicit_ci_vs_unknown": {
   "auc_child_mean": 0.35714285714285715,
   "per_seed": [
    {
     "auc_child_mean": 0.39285714285714285,
     "children": 7,
     "seed": 11
    },
    {
     "auc_child_mean": 0.32142857142857145,
     "children": 7,
     "seed": 22
    },
    {
     "auc_child_mean": 0.35714285714285715,
     "children": 7,
     "seed": 33
    }
   ]
  },
  "task_puretone_vs_bapa": {
   "auc_child_mean": 0.5740740740740741,
   "per_seed": [
    {
     "auc_child_mean": 0.6666666666666666,
     "children": 9,
     "seed": 11
    },
    {
     "auc_child_mean": 0.3333333333333333,
     "children": 9,
     "seed": 22
    },
    {
     "auc_child_mean": 0.7222222222222222,
     "children": 9,
     "seed": 33
    }
   ]
  }
 },
 "records": 336,
 "run": "GX2_ssl_mff",
 "steps": 20000,
 "window_samples": 1000,
 "windows": 28024
}
```

## gx2_eventprobe

```
{
 "path": "results/auditory_gx/GX2_eventprobe_bdf_puretone/summary_event_probe_bdf_puretone.json",
 "children": 73,
 "lane": "bdf_puretone",
 "random_encoder_logistic": {
  "auc_child_mean": 0.5120154384272034,
  "per_seed": [
   {
    "auc_child_mean": 0.5125422804652842,
    "children": 73,
    "seed": 11
   },
   {
    "auc_child_mean": 0.511719849603001,
    "children": 73,
    "seed": 22
   },
   {
    "auc_child_mean": 0.5117841852133251,
    "children": 73,
    "seed": 33
   }
  ]
 },
 "run": "GX2_eventprobe_bdf_puretone",
 "ssl_frozen_logistic": {
  "auc_child_mean": 0.5066656464922287,
  "per_seed": [
   {
    "auc_child_mean": 0.5062034941985609,
    "children": 73,
    "seed": 11
   },
   {
    "auc_child_mean": 0.5062323728859486,
    "children": 73,
    "seed": 22
   },
   {
    "auc_child_mean": 0.5075610723921764,
    "children": 73,
    "seed": 33
   }
  ]
 },
 "trials": 74921
}
```
```
{
 "path": "results/auditory_gx/GX2_eventprobe_mff_bapa/summary_event_probe_mff_bapa.json",
 "children": 27,
 "lane": "mff_bapa",
 "random_encoder_logistic": {
  "auc_child_mean": 0.48288371020148624,
  "per_seed": [
   {
    "auc_child_mean": 0.4831072214772381,
    "children": 27,
    "seed": 11
   },
   {
    "auc_child_mean": 0.48357560645845477,
    "children": 27,
    "seed": 22
   },
   {
    "auc_child_mean": 0.4819683026687659,
    "children": 27,
    "seed": 33
   }
  ]
 },
 "run": "GX2_eventprobe_mff_bapa",
 "ssl_frozen_logistic": {
  "auc_child_mean": 0.498485462346904,
  "per_seed": [
   {
    "auc_child_mean": 0.49773900544704913,
    "children": 27,
    "seed": 11
   },
   {
    "auc_child_mean": 0.4975976102632168,
    "children": 27,
    "seed": 22
   },
   {
    "auc_child_mean": 0.5001197713304462,
    "children": 27,
    "seed": 33
   }
  ]
 },
 "trials": 19873
}
```
```
{
 "path": "results/auditory_gx/GX2_eventprobe_mff_puretone/summary_event_probe_mff_puretone.json",
 "children": 36,
 "lane": "mff_puretone",
 "random_encoder_logistic": {
  "auc_child_mean": 0.4950381335152971,
  "per_seed": [
   {
    "auc_child_mean": 0.4950381335152971,
    "children": 36,
    "seed": 11
   },
   {
    "auc_child_mean": 0.4950381335152971,
    "children": 36,
    "seed": 22
   },
   {
    "auc_child_mean": 0.4950381335152971,
    "children": 36,
    "seed": 33
   }
  ]
 },
 "run": "GX2_eventprobe_mff_puretone",
 "ssl_frozen_logistic": {
  "auc_child_mean": 0.498449463633666,
  "per_seed": [
   {
    "auc_child_mean": 0.498449463633666,
    "children": 36,
    "seed": 11
   },
   {
    "auc_child_mean": 0.498449463633666,
    "children": 36,
    "seed": 22
   },
   {
    "auc_child_mean": 0.498449463633666,
    "children": 36,
    "seed": 33
   }
  ]
 },
 "trials": 28416
}
```
```
{
 "path": "results/auditory_gx/GX2_eventprobe_mff_unknown_event/summary_event_probe_mff_unknown_event.json",
 "children": 44,
 "lane": "mff_unknown_event",
 "random_encoder_logistic": {
  "auc_child_mean": 0.5004343154262879,
  "per_seed": [
   {
    "auc_child_mean": 0.5004343154262879,
    "children": 44,
    "seed": 11
   },
   {
    "auc_child_mean": 0.5004343154262879,
    "children": 44,
    "seed": 22
   },
   {
    "auc_child_mean": 0.5004343154262879,
    "children": 44,
    "seed": 33
   }
  ]
 },
 "run": "GX2_eventprobe_mff_unknown_event",
 "ssl_frozen_logistic": {
  "auc_child_mean": 0.5087786245157935,
  "per_seed": [
   {
    "auc_child_mean": 0.5087786245157935,
    "children": 44,
    "seed": 11
   },
   {
    "auc_child_mean": 0.5087786245157935,
    "children": 44,
    "seed": 22
   },
   {
    "auc_child_mean": 0.5087786245157935,
    "children": 44,
    "seed": 33
   }
  ]
 },
 "trials": 32980
}
```

## gx3_age

```
{
 "path": "results/auditory_gx/GX3_age_bdf/summary_age_HA_BDF.json",
 "branch": "HA_BDF",
 "pretrained": {
  "baseline_mae_mean": 33.57550639884736,
  "mae_mean": 32.44984582337548,
  "r_mean": 0.3737784224325548
 },
 "records_in_bank": 93,
 "run": "GX3_age_bdf",
 "scratch": {
  "baseline_mae_mean": 33.57550639884736,
  "mae_mean": 31.834736790153997,
  "r_mean": 0.3864347253106706
 }
}
```
```
{
 "path": "results/auditory_gx/GX3_age_mff/summary_age_MFF.json",
 "branch": "MFF",
 "pretrained": {
  "baseline_mae_mean": 19.83193422669459,
  "mae_mean": 16.84802607954294,
  "r_mean": 0.47266511058889904
 },
 "records_in_bank": 336,
 "run": "GX3_age_mff",
 "scratch": {
  "baseline_mae_mean": 19.83193422669459,
  "mae_mean": 16.51476814647327,
  "r_mean": 0.4648465299726763
 }
}
```

## gx4

```
{
 "path": "results/auditory_gx/GX4_crosstask/summary_gx4.json",
 "by_direction": {
  "bapa_to_puretone": 0.5095457344764747,
  "puretone_to_bapa": 0.4969821680932925
 },
 "children_with_both_tasks": 9,
 "multitask": {
  "multitask/bp": 0.5048955769210992,
  "multitask/pt": 0.5150371361862506,
  "single_bapa/bp": 0.5049637248941534,
  "single_puretone/pt": 0.5109345223376518
 },
 "run": "GX4_crosstask",
 "within_child_cross_task_auc_mean": 0.5036334679432125,
 "within_child_same_task_val_auc_mean": 0.5368368794202968
}
```

## gx5

```
{
 "path": "results/auditory_gx/GX5_conditions/summary_gx5_conditions.json",
 "children": 2,
 "records": 15,
 "run": "GX5_conditions",
 "within_record_auc_by_condition": {
  "ci-noise-front": 0.4499066325973194,
  "ci-noise-left": 0.496716986036839,
  "ci-noise-right": 0.4653963058218377
 }
}
```

## gx6

```
{
 "path": "results/auditory_gx/GX6_bdf_puretone/summary_gx6_bdf_puretone.json",
 "across_other_day_auc_mean": 0.5171903114526747,
 "across_record_auc_mean": 0.5171903114526747,
 "across_same_day_auc_mean": null,
 "children_in_segment_contrast": 67,
 "children_with_multiple_records": 11,
 "lane": "bdf_puretone",
 "run": "GX6_bdf_puretone",
 "segment_auc_first_third_mean": 0.5160966014026122,
 "segment_auc_last_third_mean": 0.5043577771442957,
 "segments_rows": 2331,
 "within_record_auc_mean": 0.5312721707975774
}
```
```
{
 "path": "results/auditory_gx/GX6_mff_bapa/summary_gx6_mff_bapa.json",
 "across_other_day_auc_mean": 0.48633766653403576,
 "across_record_auc_mean": 0.49131708337782076,
 "across_same_day_auc_mean": 0.5012759170653908,
 "children_in_segment_contrast": 5,
 "children_with_multiple_records": 2,
 "lane": "mff_bapa",
 "run": "GX6_mff_bapa",
 "segment_auc_first_third_mean": 0.5410884855144579,
 "segment_auc_last_third_mean": 0.5183270988101912,
 "segments_rows": 78,
 "within_record_auc_mean": 0.47950973015429216
}
```
```
{
 "path": "results/auditory_gx/GX6_mff_puretone/summary_gx6_mff_puretone.json",
 "across_other_day_auc_mean": 0.494071356098281,
 "across_record_auc_mean": 0.5046508403693779,
 "across_same_day_auc_mean": 0.5152303246404748,
 "children_in_segment_contrast": 10,
 "children_with_multiple_records": 3,
 "lane": "mff_puretone",
 "run": "GX6_mff_puretone",
 "segment_auc_first_third_mean": 0.489589643923269,
 "segment_auc_last_third_mean": 0.5186070355795398,
 "segments_rows": 183,
 "within_record_auc_mean": 0.5557560391431849
}
```
```
{
 "path": "results/auditory_gx/GX6_mff_unknown_event/summary_gx6_mff_unknown_event.json",
 "across_other_day_auc_mean": 0.49978932226165323,
 "across_record_auc_mean": 0.5136435424522644,
 "across_same_day_auc_mean": 0.5145094312141776,
 "children_in_segment_contrast": 23,
 "children_with_multiple_records": 11,
 "lane": "mff_unknown_event",
 "run": "GX6_mff_unknown_event",
 "segment_auc_first_third_mean": 0.503934818183946,
 "segment_auc_last_third_mean": 0.47472816920855526,
 "segments_rows": 501,
 "within_record_auc_mean": 0.5077477483045713
}
```

## GX7 相关（Spearman）

| lane | model | variable | n | rho | p |
|---|---|---|---|---|---|
| mff_puretone | per_child | age | 20 | +0.111 | 0.64 |
| bdf_puretone | per_child | age | 52 | +0.228 | 0.104 |
| bdf_puretone | per_child | duration | 52 | -0.050 | 0.723 |
| bdf_puretone | per_child | unaided | 52 | +0.037 | 0.797 |
| bdf_puretone | per_child | unaided|age | 50 | +0.003 | 0.982 |
| bdf_puretone | per_child | aided | 42 | -0.063 | 0.692 |
| bdf_puretone | per_child | aided|age | 40 | -0.062 | 0.706 |
| bdf_puretone | per_child | A | 54 | -0.047 | 0.735 |
| bdf_puretone | per_child | A|age | 52 | -0.233 | 0.0961 |
| bdf_puretone | per_child | V | 54 | -0.077 | 0.581 |
| bdf_puretone | per_child | V|age | 52 | -0.321 | 0.0203 |
| bdf_puretone | per_child | CAP | 54 | -0.082 | 0.553 |
| bdf_puretone | per_child | CAP|age | 52 | -0.371 | 0.00683 |
| bdf_puretone | per_child | SIR | 54 | +0.008 | 0.952 |
| bdf_puretone | per_child | SIR|age | 52 | -0.241 | 0.0848 |
| mff_unknown_event | per_child | age | 15 | +0.196 | 0.483 |

