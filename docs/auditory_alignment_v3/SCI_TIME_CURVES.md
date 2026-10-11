# SCI_TIME_CURVES：逐 lag 可读性、模型依赖/可替代性与窗口三件套（docs/13 S1，第 1 轮）

> 预登记：`SCI_R1_PREREG.md`（冻结 v3，sha256 `aab58bc1…`）；实现说明：`SCI_R1_ADDENDUM_01_IMPLEMENTATION_NOTES.md`。
> 全部 670 个任务完成，0 失败；汇总 `results/auditory_alignment_v3/sci_r1/*.json`。本文只陈述事实与预登记解读表的适用，框架由用户决定。
> 区间记法：`估计 [95% CI] {族内同时区间} (n)`，bootstrap-t、按身份重抽、B=4000，以已拟合模型为条件。gain = 对应敏感性（错配−真实 logloss，比特/5 s 查询）；R = 真实 EEG logloss（风险，越低越好）。

## 1. 主要量（预登记 §8；每个数据集 × objective 一族，另设原始族）

**FAU · NCE**（共同身份 n=67；族内 max-t 临界值 2.74；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.311 [+0.215, +0.407] {+0.178, +0.445} (n=67) |
| triad_R_late_minus_R_joint | +0.047 [+0.005, +0.088] {-0.009, +0.102} (n=67) |
| SB_R_early | -0.002 [-0.022, +0.018] {-0.029, +0.025} (n=67) |
| SB_R_late | +0.238 [+0.153, +0.323] {+0.121, +0.355} (n=67) |
| frozen_late_minus_early_gain | +0.073 [+0.033, +0.112] {+0.017, +0.128} (n=67) |
| frozen_minus_raw_rank_gain_early | +0.022 [+0.012, +0.032] {+0.008, +0.036} (n=67) |
| frozen_minus_raw_rank_gain_late | +0.017 [+0.011, +0.023] {+0.009, +0.026} (n=67) |
| interaction_rank_gain_late_minus_early | -0.004 [-0.014, +0.005] {-0.018, +0.009} (n=67) |
| （并列，不进族）MD_R_early | +0.001 [-0.013, +0.015] (n=67) |
| （并列，不进族）MD_R_late | +0.403 [+0.329, +0.477] (n=67) |
| （并列，不进族）frozen_minus_raw_gain_early | +0.080 [+0.056, +0.105] (n=67) |
| （并列，不进族）frozen_minus_raw_gain_late | +0.072 [+0.054, +0.089] (n=67) |
| （并列，不进族）frozen_minus_raw_R_early | -0.036 [-0.058, -0.014] (n=67) |
| （并列，不进族）frozen_minus_raw_R_late | -0.038 [-0.054, -0.022] (n=67) |

**FAU · CS_SINGLE**（共同身份 n=67；族内 max-t 临界值 2.74；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.218 [+0.152, +0.285] {+0.126, +0.311} (n=67) |
| triad_R_late_minus_R_joint | +0.083 [+0.056, +0.110] {+0.046, +0.120} (n=67) |
| SB_R_early | +0.008 [-0.004, +0.019] {-0.008, +0.023} (n=67) |
| SB_R_late | +0.197 [+0.139, +0.255] {+0.116, +0.278} (n=67) |
| frozen_late_minus_early_gain | +0.074 [+0.037, +0.110] {+0.022, +0.125} (n=67) |
| frozen_minus_raw_rank_gain_early | +0.019 [+0.010, +0.027] {+0.006, +0.031} (n=67) |
| frozen_minus_raw_rank_gain_late | +0.015 [+0.009, +0.021] {+0.007, +0.023} (n=67) |
| interaction_rank_gain_late_minus_early | -0.004 [-0.012, +0.005] {-0.015, +0.008} (n=67) |
| （并列，不进族）MD_R_early | +0.006 [-0.005, +0.017] (n=67) |
| （并列，不进族）MD_R_late | +0.260 [+0.209, +0.311] (n=67) |
| （并列，不进族）frozen_minus_raw_gain_early | +0.071 [+0.048, +0.094] (n=67) |
| （并列，不进族）frozen_minus_raw_gain_late | +0.063 [+0.049, +0.078] (n=67) |
| （并列，不进族）frozen_minus_raw_R_early | -0.033 [-0.051, -0.014] (n=67) |
| （并列，不进族）frozen_minus_raw_R_late | -0.033 [-0.045, -0.021] (n=67) |

**FAU · raw_objective_free**（共同身份 n=67；族内 max-t 临界值 2.06；）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| raw_late_minus_early_gain | +0.081 [+0.051, +0.112] {+0.049, +0.113} (n=67) |
| raw_late_minus_early_rank_gain | +0.027 [+0.014, +0.041] {+0.013, +0.042} (n=67) |

**DTU · NCE**（共同身份 n=44；族内 max-t 临界值 2.81；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.627 [+0.502, +0.753] {+0.456, +0.799} (n=44) |
| triad_R_late_minus_R_joint | +0.144 [+0.098, +0.190] {+0.079, +0.210} (n=44) |
| SB_R_early | +0.063 [+0.039, +0.086] {+0.029, +0.096} (n=44) |
| SB_R_late | +0.516 [+0.418, +0.614] {+0.384, +0.648} (n=44) |
| frozen_late_minus_early_gain | +0.190 [+0.123, +0.257] {+0.099, +0.281} (n=44) |
| frozen_minus_raw_rank_gain_early | +0.028 [+0.016, +0.041] {+0.011, +0.046} (n=44) |
| frozen_minus_raw_rank_gain_late | +0.017 [+0.006, +0.028] {+0.002, +0.032} (n=44) |
| interaction_rank_gain_late_minus_early | -0.012 [-0.023, -0.000] {-0.028, +0.004} (n=44) |
| （并列，不进族）MD_R_early | +0.043 [+0.013, +0.072] (n=44) |
| （并列，不进族）MD_R_late | +0.740 [+0.643, +0.838] (n=44) |
| （并列，不进族）frozen_minus_raw_gain_early | +0.131 [+0.087, +0.174] (n=44) |
| （并列，不进族）frozen_minus_raw_gain_late | +0.107 [+0.063, +0.152] (n=44) |
| （并列，不进族）frozen_minus_raw_R_early | -0.087 [-0.113, -0.061] (n=44) |
| （并列，不进族）frozen_minus_raw_R_late | -0.078 [-0.111, -0.045] (n=44) |

**DTU · CS_SINGLE**（共同身份 n=44；族内 max-t 临界值 2.87；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.410 [+0.313, +0.506] {+0.276, +0.543} (n=44) |
| triad_R_late_minus_R_joint | +0.078 [+0.036, +0.121] {+0.018, +0.139} (n=44) |
| SB_R_early | +0.047 [+0.029, +0.066] {+0.022, +0.073} (n=44) |
| SB_R_late | +0.330 [+0.258, +0.401] {+0.229, +0.430} (n=44) |
| frozen_late_minus_early_gain | +0.161 [+0.093, +0.229] {+0.064, +0.257} (n=44) |
| frozen_minus_raw_rank_gain_early | +0.024 [+0.012, +0.035] {+0.007, +0.040} (n=44) |
| frozen_minus_raw_rank_gain_late | +0.011 [+0.000, +0.021] {-0.003, +0.025} (n=44) |
| interaction_rank_gain_late_minus_early | -0.013 [-0.025, -0.001] {-0.030, +0.005} (n=44) |
| （并列，不进族）MD_R_early | +0.037 [+0.013, +0.060] (n=44) |
| （并列，不进族）MD_R_late | +0.455 [+0.387, +0.524] (n=44) |
| （并列，不进族）frozen_minus_raw_gain_early | +0.095 [+0.059, +0.132] (n=44) |
| （并列，不进族）frozen_minus_raw_gain_late | +0.043 [+0.004, +0.082] (n=44) |
| （并列，不进族）frozen_minus_raw_R_early | -0.076 [-0.101, -0.050] (n=44) |
| （并列，不进族）frozen_minus_raw_R_late | -0.056 [-0.082, -0.029] (n=44) |

**DTU · raw_objective_free**（共同身份 n=44；族内 max-t 临界值 2.12；）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| raw_late_minus_early_gain | +0.213 [+0.145, +0.281] {+0.140, +0.286} (n=44) |
| raw_late_minus_early_rank_gain | +0.035 [+0.016, +0.053] {+0.015, +0.054} (n=44) |

**Federici · NCE**（共同身份 n=86；族内 max-t 临界值 2.72；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.011 [-0.016, +0.037] {-0.027, +0.048} (n=86) |
| triad_R_late_minus_R_joint | +0.053 [+0.031, +0.075] {+0.022, +0.083} (n=86) |
| SB_R_early | +0.043 [+0.025, +0.062] {+0.017, +0.070} (n=86) |
| SB_R_late | -0.010 [-0.042, +0.023] {-0.054, +0.035} (n=86) |
| frozen_late_minus_early_gain | -0.111 [-0.143, -0.078] {-0.155, -0.066} (n=86) |
| frozen_minus_raw_rank_gain_early | -0.002 [-0.020, +0.015] {-0.026, +0.021} (n=86) |
| frozen_minus_raw_rank_gain_late | +0.005 [-0.008, +0.018] {-0.013, +0.023} (n=86) |
| interaction_rank_gain_late_minus_early | +0.007 [-0.014, +0.028] {-0.022, +0.036} (n=86) |
| （并列，不进族）MD_R_early | +0.075 [+0.056, +0.094] (n=86) |
| （并列，不进族）MD_R_late | +0.017 [-0.011, +0.044] (n=86) |
| （并列，不进族）frozen_minus_raw_gain_early | -0.055 [-0.089, -0.022] (n=86) |
| （并列，不进族）frozen_minus_raw_gain_late | -0.006 [-0.017, +0.004] (n=86) |
| （并列，不进族）frozen_minus_raw_R_early | +0.001 [-0.027, +0.028] (n=86) |
| （并列，不进族）frozen_minus_raw_R_late | +0.005 [-0.003, +0.014] (n=86) |

**Federici · CS_SINGLE**（共同身份 n=86；族内 max-t 临界值 2.77；triad NCE: seeds 3401/3407/3413 averaged per identity; triad CS and all P0 quantities: seed 3401）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| triad_R_early_minus_R_joint | +0.030 [-0.007, +0.067] {-0.023, +0.082} (n=86) |
| triad_R_late_minus_R_joint | +0.089 [+0.062, +0.115] {+0.052, +0.125} (n=86) |
| SB_R_early | +0.040 [+0.020, +0.061] {+0.011, +0.069} (n=86) |
| SB_R_late | +0.006 [-0.022, +0.034] {-0.033, +0.045} (n=86) |
| frozen_late_minus_early_gain | -0.108 [-0.138, -0.078] {-0.150, -0.067} (n=86) |
| frozen_minus_raw_rank_gain_early | -0.009 [-0.027, +0.010] {-0.035, +0.017} (n=86) |
| frozen_minus_raw_rank_gain_late | +0.006 [-0.006, +0.019] {-0.011, +0.024} (n=86) |
| interaction_rank_gain_late_minus_early | +0.015 [-0.004, +0.035] {-0.012, +0.043} (n=86) |
| （并列，不进族）MD_R_early | +0.065 [+0.043, +0.088] (n=86) |
| （并列，不进族）MD_R_late | +0.020 [-0.009, +0.049] (n=86) |
| （并列，不进族）frozen_minus_raw_gain_early | -0.061 [-0.095, -0.028] (n=86) |
| （并列，不进族）frozen_minus_raw_gain_late | -0.010 [-0.020, -0.000] (n=86) |
| （并列，不进族）frozen_minus_raw_R_early | +0.013 [-0.012, +0.038] (n=86) |
| （并列，不进族）frozen_minus_raw_R_late | +0.003 [-0.004, +0.011] (n=86) |

**Federici · raw_objective_free**（共同身份 n=86；族内 max-t 临界值 2.09；）

| 量 | 估计 [95% CI] {族内同时区间} (n) |
|---|---|
| raw_late_minus_early_gain | -0.160 [-0.205, -0.114] {-0.208, -0.111} (n=86) |
| raw_late_minus_early_rank_gain | -0.058 [-0.081, -0.035] {-0.082, -0.034} (n=86) |

## 2. 逐 lag 曲线（图）

- 每个数据集 × objective 一张图，四条曲线：冻结（ALN3）、原始严格局部线性、未训练、冻结（ALN2）。阴影为逐 lag 同时带。
- 文件：`results/auditory_alignment_v3/sci_r1/figures/S1_<数据集>_<objective>.png`。
- 横轴为 lag token，样本访问支持见 `results/auditory_alignment_v3/sci_r1/SCI_R1_TIME_SUPPORT.json`。目标为锚点起的 8 帧窗口，token k 对应"刺激→EEG"滞后 `[o−7, o+w−1]` 个样本。
- 所有 FAU 曲线都受 stage-B ICA 规则影响（该规则去除了包络互相关峰在 ±23 ms 内的成分）。Federici 为作者 2–8 Hz 缓存上的窗口受限读出。

## 3. 窗口值（全部人类身份；gain 与 rank_gain）

### FAU
| 曲线 · 窗口（全部人类身份） | gain_bits 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.125 [+0.104, +0.147] (n=67) |
| 原始 · late | +0.206 [+0.174, +0.239] (n=67) |
| NCE frozen · early | +0.205 [+0.169, +0.241] (n=67) |
| NCE frozen · late | +0.278 [+0.235, +0.321] (n=67) |
| NCE frozen_3seed · early | +0.207 [+0.173, +0.241] (n=67) |
| NCE frozen_3seed · late | +0.277 [+0.235, +0.319] (n=67) |
| NCE aln2 · early | +0.212 [+0.175, +0.249] (n=67) |
| NCE aln2 · late | +0.272 [+0.231, +0.313] (n=67) |
| NCE untrained_s3401 · early | +0.102 [+0.081, +0.123] (n=67) |
| NCE untrained_s3401 · late | +0.166 [+0.142, +0.189] (n=67) |
| NCE untrained_3draws · early | +0.091 [+0.074, +0.108] (n=67) |
| NCE untrained_3draws · late | +0.133 [+0.113, +0.152] (n=67) |
| CS_SINGLE frozen · early | +0.196 [+0.162, +0.229] (n=67) |
| CS_SINGLE frozen · late | +0.270 [+0.230, +0.309] (n=67) |
| CS_SINGLE frozen_3seed · early | +0.198 [+0.168, +0.228] (n=67) |
| CS_SINGLE frozen_3seed · late | +0.260 [+0.222, +0.298] (n=67) |
| CS_SINGLE aln2 · early | +0.197 [+0.161, +0.233] (n=67) |
| CS_SINGLE aln2 · late | +0.262 [+0.225, +0.300] (n=67) |
| CS_SINGLE untrained_s3401 · early | +0.102 [+0.081, +0.123] (n=67) |
| CS_SINGLE untrained_s3401 · late | +0.166 [+0.142, +0.189] (n=67) |
| CS_SINGLE untrained_3draws · early | +0.091 [+0.074, +0.108] (n=67) |
| CS_SINGLE untrained_3draws · late | +0.133 [+0.113, +0.152] (n=67) |

| 曲线 · 窗口（全部人类身份） | rank_gain 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.067 [+0.056, +0.078] (n=67) |
| 原始 · late | +0.094 [+0.080, +0.108] (n=67) |
| NCE frozen · early | +0.088 [+0.074, +0.103] (n=67) |
| NCE frozen · late | +0.111 [+0.095, +0.127] (n=67) |
| NCE frozen_3seed · early | +0.087 [+0.074, +0.101] (n=67) |
| NCE frozen_3seed · late | +0.110 [+0.094, +0.126] (n=67) |
| NCE aln2 · early | +0.089 [+0.074, +0.104] (n=67) |
| NCE aln2 · late | +0.110 [+0.094, +0.126] (n=67) |
| NCE untrained_s3401 · early | +0.062 [+0.049, +0.074] (n=67) |
| NCE untrained_s3401 · late | +0.088 [+0.075, +0.100] (n=67) |
| NCE untrained_3draws · early | +0.060 [+0.050, +0.071] (n=67) |
| NCE untrained_3draws · late | +0.080 [+0.068, +0.091] (n=67) |
| CS_SINGLE frozen · early | +0.085 [+0.072, +0.099] (n=67) |
| CS_SINGLE frozen · late | +0.109 [+0.094, +0.124] (n=67) |
| CS_SINGLE frozen_3seed · early | +0.087 [+0.075, +0.100] (n=67) |
| CS_SINGLE frozen_3seed · late | +0.107 [+0.092, +0.122] (n=67) |
| CS_SINGLE aln2 · early | +0.087 [+0.073, +0.100] (n=67) |
| CS_SINGLE aln2 · late | +0.109 [+0.093, +0.124] (n=67) |
| CS_SINGLE untrained_s3401 · early | +0.062 [+0.049, +0.074] (n=67) |
| CS_SINGLE untrained_s3401 · late | +0.088 [+0.075, +0.100] (n=67) |
| CS_SINGLE untrained_3draws · early | +0.060 [+0.050, +0.071] (n=67) |
| CS_SINGLE untrained_3draws · late | +0.080 [+0.068, +0.091] (n=67) |
### DTU
| 曲线 · 窗口（全部人类身份） | gain_bits 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.349 [+0.288, +0.410] (n=44) |
| 原始 · late | +0.562 [+0.498, +0.626] (n=44) |
| NCE frozen · early | +0.480 [+0.406, +0.554] (n=44) |
| NCE frozen · late | +0.670 [+0.585, +0.754] (n=44) |
| NCE frozen_3seed · early | +0.476 [+0.400, +0.551] (n=44) |
| NCE frozen_3seed · late | +0.684 [+0.599, +0.769] (n=44) |
| NCE aln2 · early | +0.472 [+0.395, +0.548] (n=44) |
| NCE aln2 · late | +0.668 [+0.578, +0.759] (n=44) |
| NCE untrained_s3401 · early | +0.155 [+0.118, +0.191] (n=44) |
| NCE untrained_s3401 · late | +0.273 [+0.235, +0.311] (n=44) |
| NCE untrained_3draws · early | +0.187 [+0.158, +0.215] (n=44) |
| NCE untrained_3draws · late | +0.314 [+0.273, +0.355] (n=44) |
| CS_SINGLE frozen · early | +0.445 [+0.380, +0.509] (n=44) |
| CS_SINGLE frozen · late | +0.605 [+0.528, +0.683] (n=44) |
| CS_SINGLE frozen_3seed · early | +0.445 [+0.378, +0.512] (n=44) |
| CS_SINGLE frozen_3seed · late | +0.633 [+0.554, +0.712] (n=44) |
| CS_SINGLE aln2 · early | +0.451 [+0.387, +0.515] (n=44) |
| CS_SINGLE aln2 · late | +0.614 [+0.535, +0.692] (n=44) |
| CS_SINGLE untrained_s3401 · early | +0.155 [+0.118, +0.191] (n=44) |
| CS_SINGLE untrained_s3401 · late | +0.273 [+0.235, +0.311] (n=44) |
| CS_SINGLE untrained_3draws · early | +0.187 [+0.158, +0.215] (n=44) |
| CS_SINGLE untrained_3draws · late | +0.314 [+0.273, +0.355] (n=44) |

| 曲线 · 窗口（全部人类身份） | rank_gain 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.116 [+0.097, +0.134] (n=44) |
| 原始 · late | +0.150 [+0.134, +0.167] (n=44) |
| NCE frozen · early | +0.144 [+0.122, +0.166] (n=44) |
| NCE frozen · late | +0.167 [+0.147, +0.186] (n=44) |
| NCE frozen_3seed · early | +0.142 [+0.120, +0.163] (n=44) |
| NCE frozen_3seed · late | +0.170 [+0.150, +0.189] (n=44) |
| NCE aln2 · early | +0.142 [+0.120, +0.164] (n=44) |
| NCE aln2 · late | +0.166 [+0.146, +0.186] (n=44) |
| NCE untrained_s3401 · early | +0.076 [+0.059, +0.094] (n=44) |
| NCE untrained_s3401 · late | +0.107 [+0.092, +0.122] (n=44) |
| NCE untrained_3draws · early | +0.085 [+0.072, +0.098] (n=44) |
| NCE untrained_3draws · late | +0.116 [+0.101, +0.131] (n=44) |
| CS_SINGLE frozen · early | +0.139 [+0.119, +0.160] (n=44) |
| CS_SINGLE frozen · late | +0.161 [+0.142, +0.180] (n=44) |
| CS_SINGLE frozen_3seed · early | +0.138 [+0.118, +0.158] (n=44) |
| CS_SINGLE frozen_3seed · late | +0.165 [+0.146, +0.184] (n=44) |
| CS_SINGLE aln2 · early | +0.142 [+0.122, +0.161] (n=44) |
| CS_SINGLE aln2 · late | +0.161 [+0.142, +0.180] (n=44) |
| CS_SINGLE untrained_s3401 · early | +0.076 [+0.059, +0.094] (n=44) |
| CS_SINGLE untrained_s3401 · late | +0.107 [+0.092, +0.122] (n=44) |
| CS_SINGLE untrained_3draws · early | +0.085 [+0.072, +0.098] (n=44) |
| CS_SINGLE untrained_3draws · late | +0.116 [+0.101, +0.131] (n=44) |
### Federici
| 曲线 · 窗口（全部人类身份） | gain_bits 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.187 [+0.138, +0.236] (n=86) |
| 原始 · late | +0.028 [+0.018, +0.037] (n=86) |
| NCE frozen · early | +0.132 [+0.099, +0.164] (n=86) |
| NCE frozen · late | +0.021 [+0.014, +0.029] (n=86) |
| NCE frozen_3seed · early | +0.119 [+0.091, +0.147] (n=86) |
| NCE frozen_3seed · late | +0.020 [+0.015, +0.025] (n=86) |
| NCE aln2 · early | +0.126 [+0.096, +0.156] (n=86) |
| NCE aln2 · late | +0.024 [+0.018, +0.031] (n=86) |
| NCE untrained_s3401 · early | +0.059 [+0.042, +0.076] (n=86) |
| NCE untrained_s3401 · late | +0.008 [+0.004, +0.012] (n=86) |
| NCE untrained_3draws · early | +0.059 [+0.044, +0.074] (n=86) |
| NCE untrained_3draws · late | +0.009 [+0.005, +0.012] (n=86) |
| CS_SINGLE frozen · early | +0.126 [+0.096, +0.156] (n=86) |
| CS_SINGLE frozen · late | +0.018 [+0.011, +0.024] (n=86) |
| CS_SINGLE frozen_3seed · early | +0.107 [+0.082, +0.131] (n=86) |
| CS_SINGLE frozen_3seed · late | +0.017 [+0.013, +0.022] (n=86) |
| CS_SINGLE aln2 · early | +0.111 [+0.083, +0.139] (n=86) |
| CS_SINGLE aln2 · late | +0.012 [+0.006, +0.018] (n=86) |
| CS_SINGLE untrained_s3401 · early | +0.059 [+0.042, +0.076] (n=86) |
| CS_SINGLE untrained_s3401 · late | +0.008 [+0.004, +0.012] (n=86) |
| CS_SINGLE untrained_3draws · early | +0.059 [+0.044, +0.074] (n=86) |
| CS_SINGLE untrained_3draws · late | +0.009 [+0.005, +0.012] (n=86) |

| 曲线 · 窗口（全部人类身份） | rank_gain 估计 [95% CI] (n) |
|---|---|
| 原始 · early | +0.081 [+0.058, +0.104] (n=86) |
| 原始 · late | +0.023 [+0.013, +0.034] (n=86) |
| NCE frozen · early | +0.079 [+0.061, +0.097] (n=86) |
| NCE frozen · late | +0.028 [+0.017, +0.039] (n=86) |
| NCE frozen_3seed · early | +0.073 [+0.056, +0.090] (n=86) |
| NCE frozen_3seed · late | +0.028 [+0.021, +0.036] (n=86) |
| NCE aln2 · early | +0.072 [+0.055, +0.089] (n=86) |
| NCE aln2 · late | +0.038 [+0.028, +0.048] (n=86) |
| NCE untrained_s3401 · early | +0.049 [+0.032, +0.065] (n=86) |
| NCE untrained_s3401 · late | +0.012 [+0.004, +0.020] (n=86) |
| NCE untrained_3draws · early | +0.053 [+0.039, +0.067] (n=86) |
| NCE untrained_3draws · late | +0.016 [+0.009, +0.022] (n=86) |
| CS_SINGLE frozen · early | +0.072 [+0.054, +0.091] (n=86) |
| CS_SINGLE frozen · late | +0.030 [+0.018, +0.041] (n=86) |
| CS_SINGLE frozen_3seed · early | +0.066 [+0.050, +0.082] (n=86) |
| CS_SINGLE frozen_3seed · late | +0.028 [+0.021, +0.036] (n=86) |
| CS_SINGLE aln2 · early | +0.067 [+0.049, +0.086] (n=86) |
| CS_SINGLE aln2 · late | +0.020 [+0.009, +0.030] (n=86) |
| CS_SINGLE untrained_s3401 · early | +0.049 [+0.032, +0.065] (n=86) |
| CS_SINGLE untrained_s3401 · late | +0.012 [+0.004, +0.020] (n=86) |
| CS_SINGLE untrained_3draws · early | +0.053 [+0.039, +0.067] (n=86) |
| CS_SINGLE untrained_3draws · late | +0.016 [+0.009, +0.022] (n=86) |

## 4. 配对差（同一身份；冻结−原始 以 rank_gain 为共同主量）

### FAU
| 配对差 | 指标 | 早窗 | 晚窗 |
|---|---|---|---|
| NCE frozen_minus_raw | rank_gain | +0.022 [+0.012, +0.032] (n=67) | +0.017 [+0.011, +0.023] (n=67) |
| NCE frozen_minus_raw | gain_bits | +0.080 [+0.055, +0.105] (n=67) | +0.072 [+0.055, +0.089] (n=67) |
| NCE frozen_minus_raw | regular_logloss_bits | -0.036 [-0.057, -0.015] (n=67) | -0.038 [-0.054, -0.023] (n=67) |
| NCE frozen_minus_rawpca | rank_gain | +0.020 [+0.011, +0.029] (n=67) | +0.018 [+0.012, +0.024] (n=67) |
| NCE frozen_minus_rawpca | gain_bits | +0.085 [+0.062, +0.107] (n=67) | +0.080 [+0.063, +0.097] (n=67) |
| NCE frozen_minus_rawpca | regular_logloss_bits | -0.031 [-0.050, -0.012] (n=67) | -0.041 [-0.058, -0.024] (n=67) |
| NCE frozen_minus_untrained | rank_gain | +0.027 [+0.016, +0.037] (n=67) | +0.024 [+0.016, +0.031] (n=67) |
| NCE frozen_minus_untrained | gain_bits | +0.103 [+0.079, +0.128] (n=67) | +0.112 [+0.088, +0.136] (n=67) |
| NCE frozen_minus_untrained | regular_logloss_bits | -0.037 [-0.059, -0.016] (n=67) | -0.056 [-0.080, -0.032] (n=67) |
| NCE aln3_minus_aln2 | rank_gain | -0.001 [-0.004, +0.003] (n=67) | +0.001 [-0.002, +0.004] (n=67) |
| NCE aln3_minus_aln2 | gain_bits | -0.007 [-0.017, +0.003] (n=67) | +0.006 [-0.001, +0.014] (n=67) |
| NCE aln3_minus_aln2 | regular_logloss_bits | -0.003 [-0.012, +0.005] (n=67) | -0.005 [-0.011, +0.000] (n=67) |
| NCE frozen3_minus_untrained3 | rank_gain | +0.027 [+0.020, +0.034] (n=67) | +0.031 [+0.025, +0.037] (n=67) |
| NCE frozen3_minus_untrained3 | gain_bits | +0.116 [+0.095, +0.137] (n=67) | +0.144 [+0.120, +0.168] (n=67) |
| NCE frozen3_minus_untrained3 | regular_logloss_bits | -0.036 [-0.057, -0.016] (n=67) | -0.065 [-0.089, -0.041] (n=67) |
| CS_SINGLE frozen_minus_raw | rank_gain | +0.019 [+0.010, +0.028] (n=67) | +0.015 [+0.009, +0.021] (n=67) |
| CS_SINGLE frozen_minus_raw | gain_bits | +0.071 [+0.048, +0.094] (n=67) | +0.063 [+0.049, +0.078] (n=67) |
| CS_SINGLE frozen_minus_raw | regular_logloss_bits | -0.033 [-0.051, -0.014] (n=67) | -0.033 [-0.045, -0.021] (n=67) |
| CS_SINGLE frozen_minus_rawpca | rank_gain | +0.017 [+0.009, +0.025] (n=67) | +0.016 [+0.010, +0.021] (n=67) |
| CS_SINGLE frozen_minus_rawpca | gain_bits | +0.075 [+0.054, +0.096] (n=67) | +0.072 [+0.057, +0.086] (n=67) |
| CS_SINGLE frozen_minus_rawpca | regular_logloss_bits | -0.028 [-0.045, -0.011] (n=67) | -0.036 [-0.048, -0.023] (n=67) |
| CS_SINGLE frozen_minus_untrained | rank_gain | +0.024 [+0.015, +0.033] (n=67) | +0.022 [+0.015, +0.028] (n=67) |
| CS_SINGLE frozen_minus_untrained | gain_bits | +0.094 [+0.073, +0.115] (n=67) | +0.104 [+0.083, +0.124] (n=67) |
| CS_SINGLE frozen_minus_untrained | regular_logloss_bits | -0.034 [-0.053, -0.015] (n=67) | -0.051 [-0.070, -0.031] (n=67) |
| CS_SINGLE aln3_minus_aln2 | rank_gain | -0.001 [-0.006, +0.003] (n=67) | +0.001 [-0.002, +0.003] (n=67) |
| CS_SINGLE aln3_minus_aln2 | gain_bits | -0.001 [-0.014, +0.012] (n=67) | +0.007 [+0.001, +0.013] (n=67) |
| CS_SINGLE aln3_minus_aln2 | regular_logloss_bits | +0.005 [-0.004, +0.014] (n=67) | -0.002 [-0.007, +0.003] (n=67) |
| CS_SINGLE frozen3_minus_untrained3 | rank_gain | +0.027 [+0.022, +0.032] (n=67) | +0.028 [+0.022, +0.033] (n=67) |
| CS_SINGLE frozen3_minus_untrained3 | gain_bits | +0.107 [+0.090, +0.124] (n=67) | +0.127 [+0.107, +0.147] (n=67) |
| CS_SINGLE frozen3_minus_untrained3 | regular_logloss_bits | -0.038 [-0.054, -0.021] (n=67) | -0.059 [-0.079, -0.039] (n=67) |
### DTU
| 配对差 | 指标 | 早窗 | 晚窗 |
|---|---|---|---|
| NCE frozen_minus_raw | rank_gain | +0.028 [+0.016, +0.041] (n=44) | +0.017 [+0.006, +0.027] (n=44) |
| NCE frozen_minus_raw | gain_bits | +0.131 [+0.087, +0.174] (n=44) | +0.107 [+0.063, +0.152] (n=44) |
| NCE frozen_minus_raw | regular_logloss_bits | -0.087 [-0.113, -0.060] (n=44) | -0.078 [-0.111, -0.044] (n=44) |
| NCE frozen_minus_rawpca | rank_gain | +0.032 [+0.018, +0.045] (n=44) | +0.020 [+0.010, +0.030] (n=44) |
| NCE frozen_minus_rawpca | gain_bits | +0.178 [+0.134, +0.221] (n=44) | +0.169 [+0.122, +0.216] (n=44) |
| NCE frozen_minus_rawpca | regular_logloss_bits | -0.079 [-0.111, -0.047] (n=44) | -0.074 [-0.108, -0.041] (n=44) |
| NCE frozen_minus_untrained | rank_gain | +0.068 [+0.053, +0.082] (n=44) | +0.060 [+0.048, +0.071] (n=44) |
| NCE frozen_minus_untrained | gain_bits | +0.325 [+0.273, +0.378] (n=44) | +0.397 [+0.334, +0.460] (n=44) |
| NCE frozen_minus_untrained | regular_logloss_bits | -0.124 [-0.170, -0.079] (n=44) | -0.174 [-0.225, -0.124] (n=44) |
| NCE aln3_minus_aln2 | rank_gain | +0.002 [-0.003, +0.007] (n=44) | +0.001 [-0.003, +0.004] (n=44) |
| NCE aln3_minus_aln2 | gain_bits | +0.008 [-0.006, +0.023] (n=44) | +0.001 [-0.015, +0.018] (n=44) |
| NCE aln3_minus_aln2 | regular_logloss_bits | +0.001 [-0.010, +0.011] (n=44) | -0.000 [-0.011, +0.010] (n=44) |
| NCE frozen3_minus_untrained3 | rank_gain | +0.056 [+0.044, +0.068] (n=44) | +0.054 [+0.044, +0.064] (n=44) |
| NCE frozen3_minus_untrained3 | gain_bits | +0.289 [+0.236, +0.343] (n=44) | +0.370 [+0.313, +0.427] (n=44) |
| NCE frozen3_minus_untrained3 | regular_logloss_bits | -0.117 [-0.163, -0.070] (n=44) | -0.168 [-0.212, -0.124] (n=44) |
| CS_SINGLE frozen_minus_raw | rank_gain | +0.024 [+0.012, +0.036] (n=44) | +0.011 [+0.001, +0.021] (n=44) |
| CS_SINGLE frozen_minus_raw | gain_bits | +0.095 [+0.060, +0.131] (n=44) | +0.043 [+0.005, +0.081] (n=44) |
| CS_SINGLE frozen_minus_raw | regular_logloss_bits | -0.076 [-0.101, -0.050] (n=44) | -0.056 [-0.083, -0.029] (n=44) |
| CS_SINGLE frozen_minus_rawpca | rank_gain | +0.027 [+0.015, +0.039] (n=44) | +0.014 [+0.004, +0.024] (n=44) |
| CS_SINGLE frozen_minus_rawpca | gain_bits | +0.142 [+0.109, +0.176] (n=44) | +0.104 [+0.062, +0.147] (n=44) |
| CS_SINGLE frozen_minus_rawpca | regular_logloss_bits | -0.068 [-0.099, -0.038] (n=44) | -0.053 [-0.078, -0.028] (n=44) |
| CS_SINGLE frozen_minus_untrained | rank_gain | +0.063 [+0.050, +0.076] (n=44) | +0.054 [+0.043, +0.065] (n=44) |
| CS_SINGLE frozen_minus_untrained | gain_bits | +0.290 [+0.246, +0.334] (n=44) | +0.333 [+0.277, +0.388] (n=44) |
| CS_SINGLE frozen_minus_untrained | regular_logloss_bits | -0.113 [-0.156, -0.071] (n=44) | -0.153 [-0.193, -0.112] (n=44) |
| CS_SINGLE aln3_minus_aln2 | rank_gain | -0.003 [-0.007, +0.002] (n=44) | +0.000 [-0.004, +0.004] (n=44) |
| CS_SINGLE aln3_minus_aln2 | gain_bits | -0.006 [-0.025, +0.013] (n=44) | -0.009 [-0.026, +0.009] (n=44) |
| CS_SINGLE aln3_minus_aln2 | regular_logloss_bits | -0.000 [-0.011, +0.011] (n=44) | -0.004 [-0.016, +0.009] (n=44) |
| CS_SINGLE frozen3_minus_untrained3 | rank_gain | +0.053 [+0.043, +0.063] (n=44) | +0.049 [+0.040, +0.059] (n=44) |
| CS_SINGLE frozen3_minus_untrained3 | gain_bits | +0.258 [+0.213, +0.304] (n=44) | +0.319 [+0.268, +0.370] (n=44) |
| CS_SINGLE frozen3_minus_untrained3 | regular_logloss_bits | -0.106 [-0.148, -0.065] (n=44) | -0.146 [-0.183, -0.109] (n=44) |
### Federici
| 配对差 | 指标 | 早窗 | 晚窗 |
|---|---|---|---|
| NCE frozen_minus_raw | rank_gain | -0.002 [-0.020, +0.015] (n=86) | +0.005 [-0.008, +0.018] (n=86) |
| NCE frozen_minus_raw | gain_bits | -0.055 [-0.089, -0.022] (n=86) | -0.006 [-0.016, +0.004] (n=86) |
| NCE frozen_minus_raw | regular_logloss_bits | +0.001 [-0.026, +0.028] (n=86) | +0.005 [-0.003, +0.013] (n=86) |
| NCE frozen_minus_rawpca | rank_gain | +0.005 [-0.010, +0.020] (n=86) | +0.011 [-0.001, +0.023] (n=86) |
| NCE frozen_minus_rawpca | gain_bits | -0.013 [-0.038, +0.011] (n=86) | +0.008 [+0.000, +0.016] (n=86) |
| NCE frozen_minus_rawpca | regular_logloss_bits | -0.004 [-0.025, +0.016] (n=86) | -0.001 [-0.007, +0.004] (n=86) |
| NCE frozen_minus_untrained | rank_gain | +0.030 [+0.012, +0.048] (n=86) | +0.016 [+0.004, +0.028] (n=86) |
| NCE frozen_minus_untrained | gain_bits | +0.073 [+0.048, +0.098] (n=86) | +0.013 [+0.006, +0.021] (n=86) |
| NCE frozen_minus_untrained | regular_logloss_bits | -0.036 [-0.056, -0.016] (n=86) | -0.002 [-0.008, +0.003] (n=86) |
| NCE aln3_minus_aln2 | rank_gain | +0.007 [-0.003, +0.017] (n=86) | -0.010 [-0.019, -0.001] (n=86) |
| NCE aln3_minus_aln2 | gain_bits | +0.006 [-0.009, +0.020] (n=86) | -0.003 [-0.009, +0.003] (n=86) |
| NCE aln3_minus_aln2 | regular_logloss_bits | -0.007 [-0.018, +0.003] (n=86) | +0.003 [-0.002, +0.008] (n=86) |
| NCE frozen3_minus_untrained3 | rank_gain | +0.020 [+0.008, +0.032] (n=86) | +0.013 [+0.005, +0.020] (n=86) |
| NCE frozen3_minus_untrained3 | gain_bits | +0.061 [+0.042, +0.079] (n=86) | +0.011 [+0.007, +0.016] (n=86) |
| NCE frozen3_minus_untrained3 | regular_logloss_bits | -0.029 [-0.045, -0.013] (n=86) | -0.001 [-0.005, +0.002] (n=86) |
| CS_SINGLE frozen_minus_raw | rank_gain | -0.009 [-0.027, +0.010] (n=86) | +0.006 [-0.006, +0.019] (n=86) |
| CS_SINGLE frozen_minus_raw | gain_bits | -0.061 [-0.095, -0.027] (n=86) | -0.010 [-0.019, -0.001] (n=86) |
| CS_SINGLE frozen_minus_raw | regular_logloss_bits | +0.013 [-0.012, +0.038] (n=86) | +0.003 [-0.004, +0.011] (n=86) |
| CS_SINGLE frozen_minus_rawpca | rank_gain | -0.002 [-0.017, +0.014] (n=86) | +0.012 [-0.000, +0.024] (n=86) |
| CS_SINGLE frozen_minus_rawpca | gain_bits | -0.019 [-0.042, +0.004] (n=86) | +0.005 [-0.002, +0.012] (n=86) |
| CS_SINGLE frozen_minus_rawpca | regular_logloss_bits | +0.008 [-0.010, +0.025] (n=86) | -0.003 [-0.008, +0.002] (n=86) |
| CS_SINGLE frozen_minus_untrained | rank_gain | +0.024 [+0.007, +0.040] (n=86) | +0.017 [+0.006, +0.029] (n=86) |
| CS_SINGLE frozen_minus_untrained | gain_bits | +0.067 [+0.045, +0.090] (n=86) | +0.010 [+0.004, +0.016] (n=86) |
| CS_SINGLE frozen_minus_untrained | regular_logloss_bits | -0.024 [-0.042, -0.005] (n=86) | -0.004 [-0.009, +0.000] (n=86) |
| CS_SINGLE aln3_minus_aln2 | rank_gain | +0.005 [-0.007, +0.018] (n=86) | +0.010 [+0.001, +0.019] (n=86) |
| CS_SINGLE aln3_minus_aln2 | gain_bits | +0.015 [-0.008, +0.037] (n=86) | +0.005 [+0.000, +0.010] (n=86) |
| CS_SINGLE aln3_minus_aln2 | regular_logloss_bits | -0.002 [-0.018, +0.013] (n=86) | -0.005 [-0.008, -0.001] (n=86) |
| CS_SINGLE frozen3_minus_untrained3 | rank_gain | +0.013 [+0.001, +0.025] (n=86) | +0.012 [+0.005, +0.020] (n=86) |
| CS_SINGLE frozen3_minus_untrained3 | gain_bits | +0.048 [+0.032, +0.064] (n=86) | +0.009 [+0.005, +0.013] (n=86) |
| CS_SINGLE frozen3_minus_untrained3 | regular_logloss_bits | -0.020 [-0.035, -0.006] (n=86) | -0.003 [-0.006, +0.000] (n=86) |

## 5. 模型依赖（MD）与可替代性（SB），风险增加 ΔR（比特）

- "早窗/晚窗"指完全落在协议窗内的 token。"含跨界"指与窗相交的全部 token（敏感性）。
- MD：读出与温度固定。SB：编码器固定，读出与温度重拟合。

### FAU
| 面板 | 早窗（完全落窗 token）ΔR | 晚窗 ΔR | 早窗（含跨界）ΔR | 晚窗（含跨界）ΔR |
|---|---|---|---|---|
| NCE md_P0 | +0.001 [-0.013, +0.015] (n=67) | +0.403 [+0.329, +0.477] (n=67) | +0.047 [+0.016, +0.077] (n=67) | +0.442 [+0.361, +0.522] (n=67) |
| NCE sb_P0 | -0.002 [-0.023, +0.018] (n=67) | +0.238 [+0.154, +0.323] (n=67) | +0.036 [-0.005, +0.077] (n=67) | +0.256 [+0.164, +0.348] (n=67) |
| NCE md_P1 | -0.005 [-0.022, +0.011] (n=67) | +0.402 [+0.329, +0.475] (n=67) | +0.036 [+0.004, +0.068] (n=67) | +0.439 [+0.362, +0.516] (n=67) |
| NCE sb_P1 | -0.001 [-0.027, +0.024] (n=67) | +0.233 [+0.145, +0.321] (n=67) | +0.030 [-0.013, +0.072] (n=67) | +0.253 [+0.160, +0.345] (n=67) |
| CS_SINGLE md_P0 | +0.006 [-0.005, +0.017] (n=67) | +0.260 [+0.208, +0.312] (n=67) | +0.041 [+0.019, +0.063] (n=67) | +0.287 [+0.230, +0.343] (n=67) |
| CS_SINGLE sb_P0 | +0.008 [-0.003, +0.018] (n=67) | +0.197 [+0.138, +0.256] (n=67) | +0.041 [+0.018, +0.065] (n=67) | +0.216 [+0.154, +0.279] (n=67) |
| CS_SINGLE md_P1 | +0.003 [-0.008, +0.014] (n=67) | +0.246 [+0.197, +0.296] (n=67) | +0.039 [+0.016, +0.062] (n=67) | +0.266 [+0.215, +0.317] (n=67) |
| CS_SINGLE sb_P1 | -0.001 [-0.015, +0.013] (n=67) | +0.180 [+0.125, +0.235] (n=67) | +0.033 [+0.008, +0.058] (n=67) | +0.196 [+0.138, +0.254] (n=67) |
### DTU
| 面板 | 早窗（完全落窗 token）ΔR | 晚窗 ΔR | 早窗（含跨界）ΔR | 晚窗（含跨界）ΔR |
|---|---|---|---|---|
| NCE md_P0 | +0.043 [+0.013, +0.072] (n=44) | +0.740 [+0.638, +0.843] (n=44) | +0.127 [+0.084, +0.170] (n=44) | +0.833 [+0.726, +0.941] (n=44) |
| NCE sb_P0 | +0.063 [+0.039, +0.086] (n=44) | +0.516 [+0.418, +0.614] (n=44) | +0.158 [+0.121, +0.195] (n=44) | +0.563 [+0.457, +0.668] (n=44) |
| NCE md_P1 | +0.041 [+0.008, +0.074] (n=44) | +0.703 [+0.611, +0.796] (n=44) | +0.124 [+0.078, +0.170] (n=44) | +0.814 [+0.714, +0.915] (n=44) |
| NCE sb_P1 | +0.069 [+0.042, +0.096] (n=44) | +0.517 [+0.418, +0.617] (n=44) | +0.136 [+0.095, +0.176] (n=44) | +0.574 [+0.464, +0.685] (n=44) |
| CS_SINGLE md_P0 | +0.037 [+0.014, +0.060] (n=44) | +0.455 [+0.386, +0.524] (n=44) | +0.091 [+0.056, +0.126] (n=44) | +0.513 [+0.439, +0.588] (n=44) |
| CS_SINGLE sb_P0 | +0.047 [+0.029, +0.066] (n=44) | +0.330 [+0.256, +0.403] (n=44) | +0.108 [+0.077, +0.139] (n=44) | +0.361 [+0.279, +0.442] (n=44) |
| CS_SINGLE md_P1 | +0.038 [+0.018, +0.058] (n=44) | +0.482 [+0.410, +0.554] (n=44) | +0.085 [+0.055, +0.114] (n=44) | +0.544 [+0.467, +0.621] (n=44) |
| CS_SINGLE sb_P1 | +0.053 [+0.036, +0.069] (n=44) | +0.339 [+0.263, +0.416] (n=44) | +0.104 [+0.078, +0.129] (n=44) | +0.374 [+0.292, +0.456] (n=44) |
### Federici
| 面板 | 早窗（完全落窗 token）ΔR | 晚窗 ΔR | 早窗（含跨界）ΔR | 晚窗（含跨界）ΔR |
|---|---|---|---|---|
| NCE md_P0 | +0.075 [+0.056, +0.095] (n=86) | +0.017 [-0.012, +0.045] (n=86) | +0.126 [+0.100, +0.152] (n=86) | +0.052 [+0.020, +0.085] (n=86) |
| NCE sb_P0 | +0.043 [+0.024, +0.062] (n=86) | -0.010 [-0.042, +0.023] (n=86) | +0.074 [+0.049, +0.098] (n=86) | +0.009 [-0.028, +0.046] (n=86) |
| NCE md_P1 | +0.078 [+0.057, +0.098] (n=86) | +0.037 [+0.009, +0.066] (n=86) | +0.130 [+0.102, +0.157] (n=86) | +0.076 [+0.041, +0.110] (n=86) |
| NCE sb_P1 | +0.057 [+0.036, +0.077] (n=86) | +0.017 [-0.012, +0.046] (n=86) | +0.099 [+0.072, +0.127] (n=86) | +0.031 [-0.001, +0.063] (n=86) |
| CS_SINGLE md_P0 | +0.065 [+0.043, +0.088] (n=86) | +0.020 [-0.010, +0.050] (n=86) | +0.109 [+0.079, +0.139] (n=86) | +0.051 [+0.016, +0.085] (n=86) |
| CS_SINGLE sb_P0 | +0.040 [+0.020, +0.061] (n=86) | +0.006 [-0.023, +0.035] (n=86) | +0.065 [+0.038, +0.093] (n=86) | +0.008 [-0.025, +0.042] (n=86) |
| CS_SINGLE md_P1 | +0.069 [+0.046, +0.093] (n=86) | +0.026 [-0.003, +0.054] (n=86) | +0.123 [+0.090, +0.156] (n=86) | +0.060 [+0.023, +0.096] (n=86) |
| CS_SINGLE sb_P1 | +0.057 [+0.034, +0.080] (n=86) | +0.025 [-0.006, +0.057] (n=86) | +0.082 [+0.052, +0.112] (n=86) | +0.027 [-0.006, +0.061] (n=86) |

## 6. docs/04 窗口三件套（单元记录；unified 读出；NCE 三 seed，CS seed 3401；P4 目标各自一套）

### FAU
| 目标|objective | seed | R(E)−R(E,L) | R(L)−R(E,L) | R(E,L)−R(full) |
|---|---|---|---|---|
| local|NCE | 3401,3407,3413 | +0.311 [+0.215, +0.407] (n=67) | +0.047 [+0.005, +0.088] (n=67) | -0.003 [-0.024, +0.018] (n=67) |
| local|CS_SINGLE | 3401 | +0.218 [+0.149, +0.287] (n=67) | +0.083 [+0.055, +0.111] (n=67) | +0.034 [+0.009, +0.059] (n=67) |
| Ac|NCE | 3401 | +0.447 [+0.303, +0.591] (n=67) | +0.015 [-0.035, +0.065] (n=67) | +0.003 [-0.024, +0.030] (n=67) |
| Ac|CS_SINGLE | 3401 | +0.420 [+0.293, +0.546] (n=67) | +0.068 [+0.031, +0.106] (n=67) | +0.005 [-0.022, +0.033] (n=67) |
| Lz|NCE | 3401 | +0.313 [+0.213, +0.413] (n=67) | +0.072 [+0.037, +0.106] (n=67) | +0.069 [+0.038, +0.099] (n=67) |
| Lz|CS_SINGLE | 3401 | +0.266 [+0.187, +0.344] (n=67) | +0.046 [+0.025, +0.067] (n=67) | +0.051 [+0.020, +0.083] (n=67) |
### DTU
| 目标|objective | seed | R(E)−R(E,L) | R(L)−R(E,L) | R(E,L)−R(full) |
|---|---|---|---|---|
| local|NCE | 3401,3407,3413 | +0.627 [+0.502, +0.752] (n=44) | +0.144 [+0.097, +0.192] (n=44) | +0.036 [+0.001, +0.071] (n=44) |
| local|CS_SINGLE | 3401 | +0.410 [+0.312, +0.507] (n=44) | +0.078 [+0.037, +0.120] (n=44) | +0.046 [+0.008, +0.085] (n=44) |
| Ac|NCE | 3401 | +0.837 [+0.673, +1.000] (n=44) | +0.160 [+0.114, +0.206] (n=44) | +0.074 [+0.035, +0.113] (n=44) |
| Ac|CS_SINGLE | 3401 | +0.575 [+0.441, +0.710] (n=44) | +0.031 [-0.011, +0.072] (n=44) | +0.077 [+0.038, +0.117] (n=44) |
| Lz|NCE | 3401 | +0.360 [+0.262, +0.459] (n=44) | +0.055 [+0.017, +0.093] (n=44) | +0.092 [+0.055, +0.128] (n=44) |
| Lz|CS_SINGLE | 3401 | +0.311 [+0.233, +0.389] (n=44) | +0.100 [+0.065, +0.134] (n=44) | +0.067 [+0.034, +0.099] (n=44) |
### Federici
| 目标|objective | seed | R(E)−R(E,L) | R(L)−R(E,L) | R(E,L)−R(full) |
|---|---|---|---|---|
| local|NCE | 3401,3407,3413 | +0.011 [-0.017, +0.039] (n=86) | +0.053 [+0.031, +0.075] (n=86) | +0.001 [-0.014, +0.017] (n=86) |
| local|CS_SINGLE | 3401 | +0.030 [-0.008, +0.067] (n=86) | +0.089 [+0.062, +0.115] (n=86) | -0.034 [-0.055, -0.014] (n=86) |
