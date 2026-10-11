# SCI_GROUP_DEVELOPMENT：人群、发育与功能（docs/13 S4，第 1 轮；连续任务数据集）

> 预登记：`SCI_R1_PREREG.md`（冻结 v3，sha256 `aab58bc1…`）；实现说明：`SCI_R1_ADDENDUM_01_IMPLEMENTATION_NOTES.md`。
> 全部 670 个任务完成，0 失败；汇总 `results/auditory_alignment_v3/sci_r1/*.json`。本文只陈述事实与预登记解读表的适用，框架由用户决定。
> 区间记法：`估计 [95% CI] {族内同时区间} (n)`，bootstrap-t、按身份重抽、B=4000，以已拟合模型为条件。gain = 对应敏感性（错配−真实 logloss，比特/5 s 查询）；R = 真实 EEG logloss（风险，越低越好）。

**族的划分**：每个数据集 × objective 一族（组间、发育、功能各成一族）；原始对象另成一族（实现说明 §1）。
**R 上的量**：R 为风险，组差为正表示该组风险更高。

**计数与内容支持**（`SCI_R1_counts.json`）：
- FAU 三组、DTU 两组：测试内容完全共享（Jaccard 1.0）。
- Federici：HC 与 CI 共享 22 个测试内容组；HC-v 只有 10 个，与 HC/CI 的 Jaccard 为 0.45。因此 HC-v−HC 的比较同时混杂了内容差异。
- 幻影（9 次会话）只单列描述。
- Federici 各年龄三分位的内容组数为 5–15，见该 JSON。

## 1. 组间（独立组差，组内重抽）

### FAU（HA−TH、CI−TH、CI−HA）
| 族 | 对象 | 组差 | 估计 [95% CI] {族内同时区间} |
|---|---|---|---|
| NCE | frozen_gain_early | ha-th | -0.019 [-0.099, +0.060] {-0.156, +0.118} (n=29) |
| NCE | frozen_gain_early | ci-th | -0.121 [-0.196, -0.045] {-0.249, +0.007} (n=24) |
| NCE | frozen_gain_early | ci-ha | -0.102 [-0.182, -0.021] {-0.238, +0.035} (n=24) |
| NCE | frozen_gain_late | ha-th | +0.018 [-0.071, +0.106] {-0.130, +0.166} (n=29) |
| NCE | frozen_gain_late | ci-th | -0.149 [-0.252, -0.045] {-0.320, +0.023} (n=24) |
| NCE | frozen_gain_late | ci-ha | -0.166 [-0.263, -0.070] {-0.335, +0.002} (n=24) |
| NCE | frozen_gain_late_minus_early | ha-th | +0.037 [-0.040, +0.114] {-0.094, +0.168} (n=29) |
| NCE | frozen_gain_late_minus_early | ci-th | -0.028 [-0.131, +0.075] {-0.206, +0.150} (n=24) |
| NCE | frozen_gain_late_minus_early | ci-ha | -0.065 [-0.169, +0.039] {-0.242, +0.113} (n=24) |
| NCE | MD_R_early | ha-th | -0.024 [-0.048, -0.000] {-0.064, +0.016} (n=29) |
| NCE | MD_R_early | ci-th | -0.039 [-0.071, -0.006] {-0.095, +0.017} (n=24) |
| NCE | MD_R_early | ci-ha | -0.015 [-0.050, +0.021] {-0.076, +0.047} (n=24) |
| NCE | MD_R_late | ha-th | +0.161 [-0.031, +0.352] {-0.164, +0.485} (n=29) |
| NCE | MD_R_late | ci-th | -0.148 [-0.359, +0.063] {-0.497, +0.201} (n=24) |
| NCE | MD_R_late | ci-ha | -0.309 [-0.463, -0.154] {-0.575, -0.042} (n=24) |
| NCE | SB_R_early | ha-th | -0.017 [-0.050, +0.016] {-0.072, +0.038} (n=29) |
| NCE | SB_R_early | ci-th | -0.077 [-0.132, -0.022] {-0.170, +0.016} (n=24) |
| NCE | SB_R_early | ci-ha | -0.060 [-0.110, -0.009] {-0.142, +0.023} (n=24) |
| NCE | SB_R_late | ha-th | +0.130 [-0.061, +0.321] {-0.182, +0.443} (n=29) |
| NCE | SB_R_late | ci-th | -0.306 [-0.531, -0.082] {-0.685, +0.072} (n=24) |
| NCE | SB_R_late | ci-ha | -0.437 [-0.614, -0.259] {-0.729, -0.144} (n=24) |
| NCE | triad_R_early_minus_R_joint | ha-th | +0.158 [-0.063, +0.380] {-0.211, +0.528} (n=29) |
| NCE | triad_R_early_minus_R_joint | ci-th | -0.305 [-0.571, -0.039] {-0.748, +0.138} (n=24) |
| NCE | triad_R_early_minus_R_joint | ci-ha | -0.464 [-0.671, -0.256] {-0.807, -0.120} (n=24) |
| NCE | triad_R_late_minus_R_joint | ha-th | +0.003 [-0.072, +0.078] {-0.123, +0.129} (n=29) |
| NCE | triad_R_late_minus_R_joint | ci-th | -0.146 [-0.255, -0.037] {-0.336, +0.044} (n=24) |
| NCE | triad_R_late_minus_R_joint | ci-ha | -0.149 [-0.244, -0.054] {-0.311, +0.014} (n=24) |
| NCE | tg_D_E | ha-th | +0.040 [-0.025, +0.105] {-0.072, +0.151} (n=29) |
| NCE | tg_D_E | ci-th | +0.131 [+0.064, +0.198] {+0.017, +0.244} (n=24) |
| NCE | tg_D_E | ci-ha | +0.091 [+0.013, +0.169] {-0.042, +0.223} (n=24) |
| NCE | tg_D_L | ha-th | -0.017 [-0.107, +0.073] {-0.166, +0.132} (n=29) |
| NCE | tg_D_L | ci-th | +0.141 [+0.033, +0.248] {-0.040, +0.321} (n=24) |
| NCE | tg_D_L | ci-ha | +0.157 [+0.061, +0.253] {-0.007, +0.322} (n=24) |
| NCE | tg_G_EL | ha-th | +0.009 [-0.043, +0.062] {-0.081, +0.100} (n=29) |
| NCE | tg_G_EL | ci-th | +0.065 [-0.005, +0.134] {-0.052, +0.181} (n=24) |
| NCE | tg_G_EL | ci-ha | +0.055 [-0.014, +0.124] {-0.063, +0.173} (n=24) |
| NCE | tg_G_LE | ha-th | +0.030 [-0.018, +0.078] {-0.051, +0.111} (n=29) |
| NCE | tg_G_LE | ci-th | +0.114 [+0.066, +0.161] {+0.033, +0.195} (n=24) |
| NCE | tg_G_LE | ci-ha | +0.084 [+0.034, +0.133] {-0.000, +0.168} (n=24) |
| NCE | tg_D_E_minus_G_EL | ha-th | +0.031 [-0.021, +0.082] {-0.053, +0.114} (n=29) |
| NCE | tg_D_E_minus_G_EL | ci-th | +0.066 [-0.012, +0.144] {-0.067, +0.199} (n=24) |
| NCE | tg_D_E_minus_G_EL | ci-ha | +0.036 [-0.038, +0.109] {-0.090, +0.161} (n=24) |
| NCE | tg_D_L_minus_G_LE | ha-th | -0.047 [-0.122, +0.028] {-0.172, +0.078} (n=29) |
| NCE | tg_D_L_minus_G_LE | ci-th | +0.027 [-0.069, +0.123] {-0.137, +0.191} (n=24) |
| NCE | tg_D_L_minus_G_LE | ci-ha | +0.074 [-0.014, +0.161] {-0.075, +0.222} (n=24) |
| CS_SINGLE | frozen_gain_early | ha-th | -0.020 [-0.097, +0.056] {-0.149, +0.108} (n=29) |
| CS_SINGLE | frozen_gain_early | ci-th | -0.104 [-0.178, -0.030] {-0.228, +0.020} (n=24) |
| CS_SINGLE | frozen_gain_early | ci-ha | -0.084 [-0.159, -0.008] {-0.210, +0.043} (n=24) |
| CS_SINGLE | frozen_gain_late | ha-th | +0.014 [-0.062, +0.090] {-0.114, +0.141} (n=29) |
| CS_SINGLE | frozen_gain_late | ci-th | -0.136 [-0.226, -0.047] {-0.286, +0.013} (n=24) |
| CS_SINGLE | frozen_gain_late | ci-ha | -0.150 [-0.238, -0.061] {-0.302, +0.002} (n=24) |
| CS_SINGLE | frozen_gain_late_minus_early | ha-th | +0.034 [-0.052, +0.120] {-0.106, +0.174} (n=29) |
| CS_SINGLE | frozen_gain_late_minus_early | ci-th | -0.032 [-0.133, +0.068] {-0.204, +0.140} (n=24) |
| CS_SINGLE | frozen_gain_late_minus_early | ci-ha | -0.066 [-0.160, +0.028] {-0.223, +0.091} (n=24) |
| CS_SINGLE | MD_R_early | ha-th | -0.027 [-0.049, -0.004] {-0.065, +0.012} (n=29) |
| CS_SINGLE | MD_R_early | ci-th | -0.032 [-0.060, -0.005] {-0.079, +0.014} (n=24) |
| CS_SINGLE | MD_R_early | ci-ha | -0.006 [-0.034, +0.022] {-0.053, +0.041} (n=24) |
| CS_SINGLE | MD_R_late | ha-th | +0.094 [-0.040, +0.228] {-0.126, +0.315} (n=29) |
| CS_SINGLE | MD_R_late | ci-th | -0.098 [-0.240, +0.044] {-0.329, +0.134} (n=24) |
| CS_SINGLE | MD_R_late | ci-ha | -0.192 [-0.305, -0.079] {-0.379, -0.005} (n=24) |
| CS_SINGLE | SB_R_early | ha-th | -0.029 [-0.048, -0.009] {-0.062, +0.005} (n=29) |
| CS_SINGLE | SB_R_early | ci-th | -0.028 [-0.057, -0.000] {-0.076, +0.019} (n=24) |
| CS_SINGLE | SB_R_early | ci-ha | +0.000 [-0.028, +0.028] {-0.047, +0.047} (n=24) |
| CS_SINGLE | SB_R_late | ha-th | +0.088 [-0.043, +0.219] {-0.130, +0.306} (n=29) |
| CS_SINGLE | SB_R_late | ci-th | -0.189 [-0.346, -0.032] {-0.447, +0.069} (n=24) |
| CS_SINGLE | SB_R_late | ci-ha | -0.277 [-0.403, -0.150] {-0.482, -0.071} (n=24) |
| CS_SINGLE | triad_R_early_minus_R_joint | ha-th | +0.075 [-0.071, +0.221] {-0.170, +0.321} (n=29) |
| CS_SINGLE | triad_R_early_minus_R_joint | ci-th | -0.182 [-0.363, -0.002] {-0.477, +0.113} (n=24) |
| CS_SINGLE | triad_R_early_minus_R_joint | ci-ha | -0.257 [-0.413, -0.101] {-0.513, -0.001} (n=24) |
| CS_SINGLE | triad_R_late_minus_R_joint | ha-th | -0.059 [-0.123, +0.006] {-0.165, +0.048} (n=29) |
| CS_SINGLE | triad_R_late_minus_R_joint | ci-th | -0.104 [-0.170, -0.037] {-0.219, +0.012} (n=24) |
| CS_SINGLE | triad_R_late_minus_R_joint | ci-ha | -0.045 [-0.108, +0.018] {-0.149, +0.059} (n=24) |
| CS_SINGLE | tg_D_E | ha-th | +0.043 [-0.020, +0.106] {-0.061, +0.147} (n=29) |
| CS_SINGLE | tg_D_E | ci-th | +0.115 [+0.053, +0.177] {+0.009, +0.221} (n=24) |
| CS_SINGLE | tg_D_E | ci-ha | +0.072 [-0.001, +0.145] {-0.050, +0.194} (n=24) |
| CS_SINGLE | tg_D_L | ha-th | -0.012 [-0.087, +0.063] {-0.139, +0.116} (n=29) |
| CS_SINGLE | tg_D_L | ci-th | +0.131 [+0.039, +0.223] {-0.020, +0.283} (n=24) |
| CS_SINGLE | tg_D_L | ci-ha | +0.143 [+0.060, +0.226] {+0.001, +0.285} (n=24) |
| CS_SINGLE | tg_G_EL | ha-th | +0.015 [-0.034, +0.063] {-0.067, +0.096} (n=29) |
| CS_SINGLE | tg_G_EL | ci-th | +0.060 [-0.004, +0.124] {-0.045, +0.165} (n=24) |
| CS_SINGLE | tg_G_EL | ci-ha | +0.045 [-0.019, +0.109] {-0.061, +0.152} (n=24) |
| CS_SINGLE | tg_G_LE | ha-th | +0.024 [-0.019, +0.066] {-0.048, +0.096} (n=29) |
| CS_SINGLE | tg_G_LE | ci-th | +0.094 [+0.050, +0.138] {+0.020, +0.168} (n=24) |
| CS_SINGLE | tg_G_LE | ci-ha | +0.070 [+0.024, +0.117] {-0.009, +0.149} (n=24) |
| CS_SINGLE | tg_D_E_minus_G_EL | ha-th | +0.029 [-0.028, +0.085] {-0.058, +0.115} (n=29) |
| CS_SINGLE | tg_D_E_minus_G_EL | ci-th | +0.055 [-0.020, +0.130] {-0.072, +0.182} (n=24) |
| CS_SINGLE | tg_D_E_minus_G_EL | ci-ha | +0.026 [-0.041, +0.094] {-0.087, +0.140} (n=24) |
| CS_SINGLE | tg_D_L_minus_G_LE | ha-th | -0.036 [-0.103, +0.032] {-0.147, +0.075} (n=29) |
| CS_SINGLE | tg_D_L_minus_G_LE | ci-th | +0.037 [-0.051, +0.126] {-0.109, +0.183} (n=24) |
| CS_SINGLE | tg_D_L_minus_G_LE | ci-ha | +0.073 [-0.007, +0.152] {-0.059, +0.205} (n=24) |
| raw | raw_gain_early | ha-th | -0.053 [-0.106, -0.001] {-0.132, +0.025} (n=29) |
| raw | raw_gain_early | ci-th | -0.097 [-0.147, -0.046] {-0.173, -0.021} (n=24) |
| raw | raw_gain_early | ci-ha | -0.043 [-0.088, +0.002] {-0.113, +0.026} (n=24) |
| raw | raw_gain_late | ha-th | +0.019 [-0.057, +0.095] {-0.093, +0.132} (n=29) |
| raw | raw_gain_late | ci-th | -0.112 [-0.194, -0.029] {-0.233, +0.010} (n=24) |
| raw | raw_gain_late | ci-ha | -0.131 [-0.201, -0.061] {-0.239, -0.022} (n=24) |
| raw | raw_gain_late_minus_early | ha-th | +0.072 [+0.012, +0.133] {-0.018, +0.162} (n=29) |
| raw | raw_gain_late_minus_early | ci-th | -0.015 [-0.098, +0.068] {-0.138, +0.108} (n=24) |
| raw | raw_gain_late_minus_early | ci-ha | -0.087 [-0.163, -0.011] {-0.204, +0.029} (n=24) |
| raw | neg_lag_mean_gain | ha-th | -0.002 [-0.010, +0.006] {-0.014, +0.011} (n=29) |
| raw | neg_lag_mean_gain | ci-th | -0.005 [-0.013, +0.003] {-0.018, +0.007} (n=24) |
| raw | neg_lag_mean_gain | ci-ha | -0.004 [-0.012, +0.004] {-0.016, +0.008} (n=24) |
| raw | noica_raw_gain_early | ha-th | -0.075 [-0.149, -0.002] {-0.185, +0.035} (n=29) |
| raw | noica_raw_gain_early | ci-th | -0.140 [-0.299, +0.019] {-0.375, +0.095} (n=24) |
| raw | noica_raw_gain_early | ci-ha | -0.065 [-0.222, +0.092] {-0.298, +0.168} (n=24) |
### DTU（HI−NH）
| 族 | 对象 | 组差 | 估计 [95% CI] {族内同时区间} |
|---|---|---|---|
| NCE | frozen_gain_early | hi-nh | -0.027 [-0.173, +0.119] {-0.242, +0.188} (n=22) |
| NCE | frozen_gain_late | hi-nh | +0.212 [+0.054, +0.370] {-0.017, +0.441} (n=22) |
| NCE | frozen_gain_late_minus_early | hi-nh | +0.239 [+0.131, +0.347] {+0.081, +0.397} (n=22) |
| NCE | MD_R_early | hi-nh | -0.022 [-0.083, +0.039] {-0.110, +0.066} (n=22) |
| NCE | MD_R_late | hi-nh | +0.446 [+0.312, +0.581] {+0.252, +0.641} (n=22) |
| NCE | SB_R_early | hi-nh | +0.002 [-0.046, +0.051] {-0.067, +0.072} (n=22) |
| NCE | SB_R_late | hi-nh | +0.388 [+0.241, +0.534] {+0.174, +0.601} (n=22) |
| NCE | triad_R_early_minus_R_joint | hi-nh | +0.545 [+0.366, +0.725] {+0.284, +0.806} (n=22) |
| NCE | triad_R_late_minus_R_joint | hi-nh | +0.027 [-0.064, +0.119] {-0.109, +0.163} (n=22) |
| NCE | tg_D_E | hi-nh | +0.036 [-0.093, +0.165] {-0.151, +0.223} (n=22) |
| NCE | tg_D_L | hi-nh | -0.153 [-0.278, -0.028] {-0.337, +0.032} (n=22) |
| NCE | tg_G_EL | hi-nh | -0.052 [-0.162, +0.058] {-0.211, +0.107} (n=22) |
| NCE | tg_G_LE | hi-nh | +0.013 [-0.092, +0.118] {-0.139, +0.165} (n=22) |
| NCE | tg_D_E_minus_G_EL | hi-nh | +0.088 [+0.005, +0.172] {-0.032, +0.208} (n=22) |
| NCE | tg_D_L_minus_G_LE | hi-nh | -0.165 [-0.250, -0.081] {-0.286, -0.045} (n=22) |
| CS_SINGLE | frozen_gain_early | hi-nh | -0.037 [-0.167, +0.093] {-0.226, +0.153} (n=22) |
| CS_SINGLE | frozen_gain_late | hi-nh | +0.168 [+0.020, +0.316] {-0.048, +0.384} (n=22) |
| CS_SINGLE | frozen_gain_late_minus_early | hi-nh | +0.205 [+0.084, +0.325] {+0.027, +0.382} (n=22) |
| CS_SINGLE | MD_R_early | hi-nh | -0.034 [-0.077, +0.010] {-0.099, +0.032} (n=22) |
| CS_SINGLE | MD_R_late | hi-nh | +0.287 [+0.187, +0.387] {+0.140, +0.434} (n=22) |
| CS_SINGLE | SB_R_early | hi-nh | -0.026 [-0.062, +0.010] {-0.079, +0.026} (n=22) |
| CS_SINGLE | SB_R_late | hi-nh | +0.279 [+0.167, +0.392] {+0.114, +0.445} (n=22) |
| CS_SINGLE | triad_R_early_minus_R_joint | hi-nh | +0.363 [+0.211, +0.514] {+0.140, +0.585} (n=22) |
| CS_SINGLE | triad_R_late_minus_R_joint | hi-nh | +0.013 [-0.074, +0.100] {-0.113, +0.138} (n=22) |
| CS_SINGLE | tg_D_E | hi-nh | +0.039 [-0.084, +0.161] {-0.143, +0.220} (n=22) |
| CS_SINGLE | tg_D_L | hi-nh | -0.115 [-0.227, -0.004] {-0.278, +0.048} (n=22) |
| CS_SINGLE | tg_G_EL | hi-nh | -0.036 [-0.143, +0.070] {-0.188, +0.116} (n=22) |
| CS_SINGLE | tg_G_LE | hi-nh | +0.048 [-0.054, +0.149] {-0.102, +0.198} (n=22) |
| CS_SINGLE | tg_D_E_minus_G_EL | hi-nh | +0.075 [-0.008, +0.158] {-0.047, +0.197} (n=22) |
| CS_SINGLE | tg_D_L_minus_G_LE | hi-nh | -0.163 [-0.239, -0.086] {-0.274, -0.052} (n=22) |
| raw | raw_gain_early | hi-nh | -0.072 [-0.192, +0.047] {-0.223, +0.079} (n=22) |
| raw | raw_gain_late | hi-nh | +0.092 [-0.035, +0.218] {-0.069, +0.252} (n=22) |
| raw | raw_gain_late_minus_early | hi-nh | +0.164 [+0.033, +0.296] {+0.002, +0.327} (n=22) |
| raw | neg_lag_mean_gain | hi-nh | -0.043 [-0.079, -0.006] {-0.088, +0.002} (n=22) |
### Federici（CI−HC、HC-v−HC；HC-v 内容支持不同）
| 族 | 对象 | 组差 | 估计 [95% CI] {族内同时区间} |
|---|---|---|---|
| NCE | frozen_gain_early | CI-HC | +0.010 [-0.062, +0.083] {-0.110, +0.131} (n=33) |
| NCE | frozen_gain_early | HC-v-HC | -0.065 [-0.153, +0.023] {-0.201, +0.071} (n=16) |
| NCE | frozen_gain_late | CI-HC | +0.003 [-0.014, +0.020] {-0.025, +0.031} (n=33) |
| NCE | frozen_gain_late | HC-v-HC | -0.001 [-0.021, +0.018] {-0.033, +0.031} (n=16) |
| NCE | frozen_gain_late_minus_early | CI-HC | -0.007 [-0.081, +0.067] {-0.131, +0.117} (n=33) |
| NCE | frozen_gain_late_minus_early | HC-v-HC | +0.064 [-0.024, +0.151] {-0.072, +0.200} (n=16) |
| NCE | MD_R_early | CI-HC | -0.009 [-0.056, +0.039] {-0.087, +0.069} (n=33) |
| NCE | MD_R_early | HC-v-HC | -0.025 [-0.070, +0.019] {-0.097, +0.046} (n=16) |
| NCE | MD_R_late | CI-HC | +0.059 [-0.004, +0.123] {-0.043, +0.162} (n=33) |
| NCE | MD_R_late | HC-v-HC | +0.013 [-0.056, +0.083] {-0.098, +0.125} (n=16) |
| NCE | SB_R_early | CI-HC | +0.001 [-0.046, +0.048] {-0.076, +0.078} (n=33) |
| NCE | SB_R_early | HC-v-HC | -0.007 [-0.049, +0.035] {-0.074, +0.059} (n=16) |
| NCE | SB_R_late | CI-HC | +0.057 [-0.019, +0.132] {-0.066, +0.180} (n=33) |
| NCE | SB_R_late | HC-v-HC | +0.013 [-0.069, +0.095] {-0.116, +0.142} (n=16) |
| NCE | triad_R_early_minus_R_joint | CI-HC | +0.003 [-0.058, +0.064] {-0.101, +0.107} (n=33) |
| NCE | triad_R_early_minus_R_joint | HC-v-HC | +0.034 [-0.040, +0.109] {-0.083, +0.151} (n=16) |
| NCE | triad_R_late_minus_R_joint | CI-HC | -0.005 [-0.056, +0.047] {-0.089, +0.080} (n=33) |
| NCE | triad_R_late_minus_R_joint | HC-v-HC | -0.051 [-0.110, +0.009] {-0.141, +0.040} (n=16) |
| NCE | tg_D_E | CI-HC | +0.019 [-0.042, +0.081] {-0.081, +0.119} (n=33) |
| NCE | tg_D_E | HC-v-HC | +0.055 [-0.016, +0.126] {-0.056, +0.167} (n=16) |
| NCE | tg_D_L | CI-HC | -0.005 [-0.017, +0.007] {-0.025, +0.015} (n=33) |
| NCE | tg_D_L | HC-v-HC | +0.005 [-0.007, +0.017] {-0.015, +0.025} (n=16) |
| NCE | tg_G_EL | CI-HC | +0.001 [-0.002, +0.003] {-0.004, +0.005} (n=33) |
| NCE | tg_G_EL | HC-v-HC | +0.001 [-0.002, +0.004] {-0.004, +0.005} (n=16) |
| NCE | tg_G_LE | CI-HC | +0.003 [-0.004, +0.010] {-0.008, +0.015} (n=33) |
| NCE | tg_G_LE | HC-v-HC | +0.005 [-0.005, +0.014] {-0.010, +0.020} (n=16) |
| NCE | tg_D_E_minus_G_EL | CI-HC | +0.018 [-0.042, +0.079] {-0.080, +0.117} (n=33) |
| NCE | tg_D_E_minus_G_EL | HC-v-HC | +0.054 [-0.016, +0.125] {-0.055, +0.164} (n=16) |
| NCE | tg_D_L_minus_G_LE | CI-HC | -0.008 [-0.022, +0.006] {-0.031, +0.015} (n=33) |
| NCE | tg_D_L_minus_G_LE | HC-v-HC | +0.001 [-0.015, +0.017] {-0.025, +0.026} (n=16) |
| CS_SINGLE | frozen_gain_early | CI-HC | -0.019 [-0.088, +0.050] {-0.134, +0.096} (n=33) |
| CS_SINGLE | frozen_gain_early | HC-v-HC | -0.072 [-0.142, -0.001] {-0.186, +0.043} (n=16) |
| CS_SINGLE | frozen_gain_late | CI-HC | +0.003 [-0.011, +0.017] {-0.021, +0.027} (n=33) |
| CS_SINGLE | frozen_gain_late | HC-v-HC | +0.006 [-0.011, +0.023] {-0.022, +0.035} (n=16) |
| CS_SINGLE | frozen_gain_late_minus_early | CI-HC | +0.022 [-0.046, +0.090] {-0.093, +0.137} (n=33) |
| CS_SINGLE | frozen_gain_late_minus_early | HC-v-HC | +0.078 [+0.005, +0.151] {-0.038, +0.194} (n=16) |
| CS_SINGLE | MD_R_early | CI-HC | -0.026 [-0.078, +0.026] {-0.113, +0.061} (n=33) |
| CS_SINGLE | MD_R_early | HC-v-HC | -0.027 [-0.088, +0.033] {-0.125, +0.070} (n=16) |
| CS_SINGLE | MD_R_late | CI-HC | +0.022 [-0.044, +0.088] {-0.089, +0.132} (n=33) |
| CS_SINGLE | MD_R_late | HC-v-HC | -0.014 [-0.086, +0.059] {-0.134, +0.107} (n=16) |
| CS_SINGLE | SB_R_early | CI-HC | +0.003 [-0.046, +0.052] {-0.079, +0.084} (n=33) |
| CS_SINGLE | SB_R_early | HC-v-HC | -0.015 [-0.065, +0.036] {-0.096, +0.066} (n=16) |
| CS_SINGLE | SB_R_late | CI-HC | -0.003 [-0.067, +0.062] {-0.109, +0.104} (n=33) |
| CS_SINGLE | SB_R_late | HC-v-HC | -0.011 [-0.085, +0.064] {-0.131, +0.110} (n=16) |
| CS_SINGLE | triad_R_early_minus_R_joint | CI-HC | +0.063 [-0.023, +0.148] {-0.082, +0.207} (n=33) |
| CS_SINGLE | triad_R_early_minus_R_joint | HC-v-HC | +0.030 [-0.063, +0.123] {-0.119, +0.179} (n=16) |
| CS_SINGLE | triad_R_late_minus_R_joint | CI-HC | +0.053 [-0.003, +0.109] {-0.041, +0.147} (n=33) |
| CS_SINGLE | triad_R_late_minus_R_joint | HC-v-HC | -0.052 [-0.123, +0.020] {-0.165, +0.062} (n=16) |
| CS_SINGLE | tg_D_E | CI-HC | +0.017 [-0.037, +0.072] {-0.075, +0.109} (n=33) |
| CS_SINGLE | tg_D_E | HC-v-HC | +0.049 [-0.010, +0.108] {-0.047, +0.144} (n=16) |
| CS_SINGLE | tg_D_L | CI-HC | -0.002 [-0.012, +0.008] {-0.018, +0.015} (n=33) |
| CS_SINGLE | tg_D_L | HC-v-HC | -0.001 [-0.011, +0.010] {-0.018, +0.017} (n=16) |
| CS_SINGLE | tg_G_EL | CI-HC | -0.002 [-0.004, -0.000] {-0.005, +0.001} (n=33) |
| CS_SINGLE | tg_G_EL | HC-v-HC | -0.001 [-0.003, +0.002] {-0.004, +0.003} (n=16) |
| CS_SINGLE | tg_G_LE | CI-HC | +0.005 [+0.001, +0.009] {-0.002, +0.012} (n=33) |
| CS_SINGLE | tg_G_LE | HC-v-HC | +0.005 [+0.001, +0.010] {-0.002, +0.012} (n=16) |
| CS_SINGLE | tg_D_E_minus_G_EL | CI-HC | +0.019 [-0.036, +0.074] {-0.073, +0.111} (n=33) |
| CS_SINGLE | tg_D_E_minus_G_EL | HC-v-HC | +0.049 [-0.010, +0.109] {-0.047, +0.145} (n=16) |
| CS_SINGLE | tg_D_L_minus_G_LE | CI-HC | -0.007 [-0.018, +0.004] {-0.025, +0.012} (n=33) |
| CS_SINGLE | tg_D_L_minus_G_LE | HC-v-HC | -0.006 [-0.017, +0.005] {-0.024, +0.013} (n=16) |
| raw | raw_gain_early | CI-HC | +0.057 [-0.056, +0.170] {-0.102, +0.216} (n=33) |
| raw | raw_gain_early | HC-v-HC | -0.040 [-0.165, +0.085] {-0.209, +0.129} (n=16) |
| raw | raw_gain_late | CI-HC | +0.014 [-0.005, +0.033] {-0.013, +0.041} (n=33) |
| raw | raw_gain_late | HC-v-HC | +0.029 [-0.004, +0.062] {-0.014, +0.072} (n=16) |
| raw | raw_gain_late_minus_early | CI-HC | -0.043 [-0.151, +0.064] {-0.195, +0.108} (n=33) |
| raw | raw_gain_late_minus_early | HC-v-HC | +0.069 [-0.043, +0.181] {-0.083, +0.221} (n=16) |
| raw | neg_lag_mean_gain | CI-HC | +0.014 [-0.009, +0.037] {-0.017, +0.045} (n=33) |
| raw | neg_lag_mean_gain | HC-v-HC | -0.003 [-0.025, +0.020] {-0.034, +0.029} (n=16) |

## 2. 每组窗口值（NCE；CS 见 JSON）

### FAU
| 组 | 冻结 NCE 早 | 冻结 NCE 晚 | 原始 早 | 原始 晚 |
|---|---|---|---|---|
| th | +0.257 [+0.199, +0.315] (n=14) | +0.323 [+0.257, +0.390] (n=14) | +0.183 [+0.139, +0.227] (n=14) | +0.238 [+0.176, +0.300] (n=14) |
| ha | +0.238 [+0.177, +0.298] (n=29) | +0.341 [+0.279, +0.403] (n=29) | +0.129 [+0.096, +0.163] (n=29) | +0.257 [+0.209, +0.305] (n=29) |
| ci | +0.136 [+0.082, +0.190] (n=24) | +0.175 [+0.091, +0.259] (n=24) | +0.086 [+0.054, +0.118] (n=24) | +0.126 [+0.069, +0.184] (n=24) |
### DTU
| 组 | 冻结 NCE 早 | 冻结 NCE 晚 | 原始 早 | 原始 晚 |
|---|---|---|---|---|
| nh | +0.494 [+0.369, +0.618] (n=22) | +0.564 [+0.431, +0.696] (n=22) | +0.385 [+0.294, +0.477] (n=22) | +0.516 [+0.425, +0.608] (n=22) |
| hi | +0.466 [+0.378, +0.555] (n=22) | +0.776 [+0.670, +0.882] (n=22) | +0.313 [+0.228, +0.398] (n=22) | +0.608 [+0.515, +0.701] (n=22) |
### Federici
| 组 | 冻结 NCE 早 | 冻结 NCE 晚 | 原始 早 | 原始 晚 |
|---|---|---|---|---|
| HC | +0.140 [+0.098, +0.182] (n=37) | +0.020 [+0.007, +0.034] (n=37) | +0.173 [+0.103, +0.242] (n=37) | +0.017 [+0.005, +0.029] (n=37) |
| CI | +0.150 [+0.089, +0.212] (n=33) | +0.023 [+0.012, +0.034] (n=33) | +0.230 [+0.136, +0.323] (n=33) | +0.031 [+0.016, +0.046] (n=33) |
| HC-v | +0.075 [-0.006, +0.156] (n=16) | +0.019 [+0.003, +0.035] (n=16) | +0.133 [+0.025, +0.240] (n=16) | +0.046 [+0.015, +0.077] (n=16) |

## 3. 发育

- Federici：组内年龄斜率。HC-v 的年龄是按文件序号推定的连接。
- DTU：成人，只作描述。

### DTU
| 模型 | 系数 | 估计 [95% CI] (n) |
|---|---|---|
| NCE|frozen_gain_early|nh|age_descriptive | age | +0.0091 [-0.0140, +0.0321] (n=22)  |
| NCE|frozen_gain_early|hi|age_descriptive | age | -0.0058 [-0.0203, +0.0086] (n=22)  |
| NCE|frozen_gain_late|nh|age_descriptive | age | +0.0071 [-0.0148, +0.0290] (n=22)  |
| NCE|frozen_gain_late|hi|age_descriptive | age | -0.0005 [-0.0182, +0.0173] (n=22)  |
| NCE|frozen_gain_late_minus_early|nh|age_descriptive | age | -0.0019 [-0.0118, +0.0079] (n=22)  |
| NCE|frozen_gain_late_minus_early|hi|age_descriptive | age | +0.0054 [-0.0107, +0.0214] (n=22)  |
| NCE|MD_R_early|nh|age_descriptive | age | -0.0012 [-0.0092, +0.0069] (n=22)  |
| NCE|MD_R_early|hi|age_descriptive | age | -0.0005 [-0.0072, +0.0062] (n=22)  |
| NCE|MD_R_late|nh|age_descriptive | age | +0.0113 [+0.0037, +0.0189] (n=22)  |
| NCE|MD_R_late|hi|age_descriptive | age | +0.0089 [-0.0044, +0.0222] (n=22)  |
| NCE|SB_R_early|nh|age_descriptive | age | +0.0010 [-0.0036, +0.0056] (n=22)  |
| NCE|SB_R_early|hi|age_descriptive | age | -0.0009 [-0.0071, +0.0053] (n=22)  |
| NCE|SB_R_late|nh|age_descriptive | age | +0.0038 [-0.0042, +0.0118] (n=22)  |
| NCE|SB_R_late|hi|age_descriptive | age | +0.0073 [-0.0135, +0.0282] (n=22)  |
| NCE|triad_R_early_minus_R_joint|nh|age_descriptive | age | +0.0068 [-0.0046, +0.0182] (n=22)  |
| NCE|triad_R_early_minus_R_joint|hi|age_descriptive | age | +0.0121 [-0.0137, +0.0378] (n=22)  |
| NCE|triad_R_late_minus_R_joint|nh|age_descriptive | age | +0.0016 [-0.0096, +0.0129] (n=22)  |
| NCE|triad_R_late_minus_R_joint|hi|age_descriptive | age | +0.0015 [-0.0097, +0.0128] (n=22)  |
| NCE|tg_D_E|nh|age_descriptive | age | -0.0006 [-0.0212, +0.0200] (n=22)  |
| NCE|tg_D_E|hi|age_descriptive | age | +0.0009 [-0.0144, +0.0162] (n=22)  |
| NCE|tg_D_L|nh|age_descriptive | age | -0.0034 [-0.0208, +0.0139] (n=22)  |
| NCE|tg_D_L|hi|age_descriptive | age | -0.0038 [-0.0215, +0.0140] (n=22)  |
| NCE|tg_G_EL|nh|age_descriptive | age | -0.0080 [-0.0236, +0.0075] (n=22)  |
| NCE|tg_G_EL|hi|age_descriptive | age | -0.0025 [-0.0145, +0.0095] (n=22)  |
| NCE|tg_G_LE|nh|age_descriptive | age | +0.0016 [-0.0161, +0.0193] (n=22)  |
| NCE|tg_G_LE|hi|age_descriptive | age | +0.0016 [-0.0146, +0.0178] (n=22)  |
| NCE|tg_D_E_minus_G_EL|nh|age_descriptive | age | +0.0074 [-0.0023, +0.0172] (n=22)  |
| NCE|tg_D_E_minus_G_EL|hi|age_descriptive | age | +0.0035 [-0.0057, +0.0126] (n=22)  |
| NCE|tg_D_L_minus_G_LE|nh|age_descriptive | age | -0.0050 [-0.0130, +0.0029] (n=22)  |
| NCE|tg_D_L_minus_G_LE|hi|age_descriptive | age | -0.0054 [-0.0141, +0.0034] (n=22)  |
| CS_SINGLE|frozen_gain_early|nh|age_descriptive | age | +0.0066 [-0.0118, +0.0251] (n=22)  |
| CS_SINGLE|frozen_gain_early|hi|age_descriptive | age | -0.0045 [-0.0199, +0.0109] (n=22)  |
| CS_SINGLE|frozen_gain_late|nh|age_descriptive | age | +0.0052 [-0.0166, +0.0269] (n=22)  |
| CS_SINGLE|frozen_gain_late|hi|age_descriptive | age | +0.0006 [-0.0138, +0.0151] (n=22)  |
| CS_SINGLE|frozen_gain_late_minus_early|nh|age_descriptive | age | -0.0015 [-0.0130, +0.0100] (n=22)  |
| CS_SINGLE|frozen_gain_late_minus_early|hi|age_descriptive | age | +0.0052 [-0.0124, +0.0228] (n=22)  |
| CS_SINGLE|MD_R_early|nh|age_descriptive | age | +0.0004 [-0.0057, +0.0065] (n=22)  |
| CS_SINGLE|MD_R_early|hi|age_descriptive | age | -0.0008 [-0.0059, +0.0043] (n=22)  |
| CS_SINGLE|MD_R_late|nh|age_descriptive | age | +0.0045 [-0.0043, +0.0133] (n=22)  |
| CS_SINGLE|MD_R_late|hi|age_descriptive | age | +0.0041 [-0.0058, +0.0139] (n=22)  |
| CS_SINGLE|SB_R_early|nh|age_descriptive | age | +0.0000 [-0.0040, +0.0041] (n=22)  |
| CS_SINGLE|SB_R_early|hi|age_descriptive | age | -0.0006 [-0.0044, +0.0032] (n=22)  |
| CS_SINGLE|SB_R_late|nh|age_descriptive | age | +0.0022 [-0.0049, +0.0092] (n=22)  |
| CS_SINGLE|SB_R_late|hi|age_descriptive | age | +0.0019 [-0.0142, +0.0180] (n=22)  |
| CS_SINGLE|triad_R_early_minus_R_joint|nh|age_descriptive | age | +0.0039 [-0.0074, +0.0152] (n=22)  |
| CS_SINGLE|triad_R_early_minus_R_joint|hi|age_descriptive | age | +0.0059 [-0.0173, +0.0290] (n=22)  |
| CS_SINGLE|triad_R_late_minus_R_joint|nh|age_descriptive | age | +0.0036 [-0.0063, +0.0134] (n=22)  |
| CS_SINGLE|triad_R_late_minus_R_joint|hi|age_descriptive | age | -0.0015 [-0.0119, +0.0090] (n=22)  |
| CS_SINGLE|tg_D_E|nh|age_descriptive | age | -0.0022 [-0.0210, +0.0166] (n=22)  |
| CS_SINGLE|tg_D_E|hi|age_descriptive | age | +0.0007 [-0.0140, +0.0155] (n=22)  |
| CS_SINGLE|tg_D_L|nh|age_descriptive | age | -0.0027 [-0.0174, +0.0121] (n=22)  |
| CS_SINGLE|tg_D_L|hi|age_descriptive | age | -0.0046 [-0.0198, +0.0107] (n=22)  |
| CS_SINGLE|tg_G_EL|nh|age_descriptive | age | -0.0079 [-0.0234, +0.0076] (n=22)  |
| CS_SINGLE|tg_G_EL|hi|age_descriptive | age | -0.0012 [-0.0110, +0.0087] (n=22)  |
| CS_SINGLE|tg_G_LE|nh|age_descriptive | age | -0.0014 [-0.0188, +0.0160] (n=22)  |
| CS_SINGLE|tg_G_LE|hi|age_descriptive | age | -0.0004 [-0.0164, +0.0157] (n=22)  |
| CS_SINGLE|tg_D_E_minus_G_EL|nh|age_descriptive | age | +0.0057 [-0.0048, +0.0162] (n=22)  |
| CS_SINGLE|tg_D_E_minus_G_EL|hi|age_descriptive | age | +0.0019 [-0.0076, +0.0114] (n=22)  |
| CS_SINGLE|tg_D_L_minus_G_LE|nh|age_descriptive | age | -0.0013 [-0.0097, +0.0071] (n=22)  |
| CS_SINGLE|tg_D_L_minus_G_LE|hi|age_descriptive | age | -0.0042 [-0.0125, +0.0041] (n=22)  |
| raw|raw_gain_early|nh|age_descriptive | age | +0.0144 [+0.0010, +0.0278] (n=22)  |
| raw|raw_gain_early|hi|age_descriptive | age | +0.0015 [-0.0142, +0.0172] (n=22)  |
| raw|raw_gain_late|nh|age_descriptive | age | +0.0039 [-0.0106, +0.0185] (n=22)  |
| raw|raw_gain_late|hi|age_descriptive | age | +0.0026 [-0.0124, +0.0176] (n=22)  |
| raw|raw_gain_late_minus_early|nh|age_descriptive | age | -0.0104 [-0.0221, +0.0012] (n=22)  |
| raw|raw_gain_late_minus_early|hi|age_descriptive | age | +0.0010 [-0.0162, +0.0183] (n=22)  |
| raw|neg_lag_mean_gain|nh|age_descriptive | age | +0.0040 [+0.0004, +0.0075] (n=22)  |
| raw|neg_lag_mean_gain|hi|age_descriptive | age | +0.0019 [-0.0012, +0.0050] (n=22)  |
### Federici
| 模型 | 系数 | 估计 [95% CI] (n) |
|---|---|---|
| NCE|frozen_gain_early|HC|age | age_years | -0.0084 [-0.0168, +0.0001] (n=37)  |
| NCE|frozen_gain_early|CI|age | age_years | -0.0121 [-0.0334, +0.0091] (n=32)  |
| NCE|frozen_gain_early|HC-v|age | age_years | -0.0363 [-0.0855, +0.0129] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|frozen_gain_late|HC|age | age_years | +0.0008 [-0.0021, +0.0037] (n=37)  |
| NCE|frozen_gain_late|CI|age | age_years | -0.0010 [-0.0044, +0.0024] (n=32)  |
| NCE|frozen_gain_late|HC-v|age | age_years | -0.0052 [-0.0166, +0.0062] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|frozen_gain_late_minus_early|HC|age | age_years | +0.0092 [-0.0004, +0.0187] (n=37)  |
| NCE|frozen_gain_late_minus_early|CI|age | age_years | +0.0111 [-0.0111, +0.0333] (n=32)  |
| NCE|frozen_gain_late_minus_early|HC-v|age | age_years | +0.0311 [-0.0131, +0.0753] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|MD_R_early|HC|age | age_years | -0.0011 [-0.0083, +0.0061] (n=37)  |
| NCE|MD_R_early|CI|age | age_years | -0.0120 [-0.0233, -0.0007] (n=32)  |
| NCE|MD_R_early|HC-v|age | age_years | +0.0026 [-0.0265, +0.0318] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|MD_R_late|HC|age | age_years | +0.0015 [-0.0113, +0.0142] (n=37)  |
| NCE|MD_R_late|CI|age | age_years | +0.0156 [+0.0017, +0.0294] (n=32)  |
| NCE|MD_R_late|HC-v|age | age_years | -0.0151 [-0.0510, +0.0209] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|SB_R_early|HC|age | age_years | +0.0002 [-0.0061, +0.0064] (n=37)  |
| NCE|SB_R_early|CI|age | age_years | -0.0035 [-0.0181, +0.0111] (n=32)  |
| NCE|SB_R_early|HC-v|age | age_years | +0.0024 [-0.0282, +0.0330] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|SB_R_late|HC|age | age_years | +0.0068 [-0.0063, +0.0199] (n=37)  |
| NCE|SB_R_late|CI|age | age_years | +0.0188 [+0.0011, +0.0365] (n=32)  |
| NCE|SB_R_late|HC-v|age | age_years | -0.0076 [-0.0463, +0.0312] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|triad_R_early_minus_R_joint|HC|age | age_years | +0.0034 [-0.0053, +0.0121] (n=37)  |
| NCE|triad_R_early_minus_R_joint|CI|age | age_years | +0.0089 [-0.0053, +0.0231] (n=32)  |
| NCE|triad_R_early_minus_R_joint|HC-v|age | age_years | -0.0133 [-0.0521, +0.0255] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|triad_R_late_minus_R_joint|HC|age | age_years | -0.0075 [-0.0148, -0.0001] (n=37)  |
| NCE|triad_R_late_minus_R_joint|CI|age | age_years | -0.0072 [-0.0190, +0.0046] (n=32)  |
| NCE|triad_R_late_minus_R_joint|HC-v|age | age_years | +0.0048 [-0.0481, +0.0576] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_D_E|HC|age | age_years | +0.0057 [-0.0026, +0.0140] (n=37)  |
| NCE|tg_D_E|CI|age | age_years | +0.0155 [-0.0000, +0.0310] (n=32)  |
| NCE|tg_D_E|HC-v|age | age_years | -0.0001 [-0.0489, +0.0487] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_D_L|HC|age | age_years | -0.0004 [-0.0028, +0.0020] (n=37)  |
| NCE|tg_D_L|CI|age | age_years | +0.0001 [-0.0024, +0.0026] (n=32)  |
| NCE|tg_D_L|HC-v|age | age_years | +0.0054 [-0.0015, +0.0124] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_G_EL|HC|age | age_years | +0.0002 [-0.0002, +0.0005] (n=37)  |
| NCE|tg_G_EL|CI|age | age_years | +0.0001 [-0.0004, +0.0006] (n=32)  |
| NCE|tg_G_EL|HC-v|age | age_years | +0.0003 [-0.0013, +0.0019] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_G_LE|HC|age | age_years | +0.0011 [-0.0000, +0.0022] (n=37)  |
| NCE|tg_G_LE|CI|age | age_years | +0.0014 [-0.0001, +0.0029] (n=32)  |
| NCE|tg_G_LE|HC-v|age | age_years | -0.0002 [-0.0069, +0.0064] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_D_E_minus_G_EL|HC|age | age_years | +0.0055 [-0.0028, +0.0138] (n=37)  |
| NCE|tg_D_E_minus_G_EL|CI|age | age_years | +0.0154 [+0.0002, +0.0306] (n=32)  |
| NCE|tg_D_E_minus_G_EL|HC-v|age | age_years | -0.0004 [-0.0483, +0.0476] (n=16) HC-v ages linked by file-number order (inferred) |
| NCE|tg_D_L_minus_G_LE|HC|age | age_years | -0.0015 [-0.0040, +0.0009] (n=37)  |
| NCE|tg_D_L_minus_G_LE|CI|age | age_years | -0.0013 [-0.0042, +0.0016] (n=32)  |
| NCE|tg_D_L_minus_G_LE|HC-v|age | age_years | +0.0057 [-0.0034, +0.0147] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|frozen_gain_early|HC|age | age_years | -0.0096 [-0.0182, -0.0010] (n=37)  |
| CS_SINGLE|frozen_gain_early|CI|age | age_years | -0.0073 [-0.0244, +0.0098] (n=32)  |
| CS_SINGLE|frozen_gain_early|HC-v|age | age_years | -0.0190 [-0.0581, +0.0202] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|frozen_gain_late|HC|age | age_years | +0.0016 [-0.0006, +0.0037] (n=37)  |
| CS_SINGLE|frozen_gain_late|CI|age | age_years | +0.0003 [-0.0025, +0.0031] (n=32)  |
| CS_SINGLE|frozen_gain_late|HC-v|age | age_years | -0.0076 [-0.0171, +0.0019] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|frozen_gain_late_minus_early|HC|age | age_years | +0.0112 [+0.0020, +0.0203] (n=37)  |
| CS_SINGLE|frozen_gain_late_minus_early|CI|age | age_years | +0.0076 [-0.0102, +0.0254] (n=32)  |
| CS_SINGLE|frozen_gain_late_minus_early|HC-v|age | age_years | +0.0114 [-0.0243, +0.0471] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|MD_R_early|HC|age | age_years | +0.0016 [-0.0051, +0.0084] (n=37)  |
| CS_SINGLE|MD_R_early|CI|age | age_years | -0.0111 [-0.0236, +0.0015] (n=32)  |
| CS_SINGLE|MD_R_early|HC-v|age | age_years | +0.0162 [-0.0179, +0.0504] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|MD_R_late|HC|age | age_years | -0.0029 [-0.0147, +0.0089] (n=37)  |
| CS_SINGLE|MD_R_late|CI|age | age_years | -0.0019 [-0.0161, +0.0124] (n=32)  |
| CS_SINGLE|MD_R_late|HC-v|age | age_years | -0.0181 [-0.0657, +0.0294] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|SB_R_early|HC|age | age_years | +0.0010 [-0.0052, +0.0072] (n=37)  |
| CS_SINGLE|SB_R_early|CI|age | age_years | -0.0066 [-0.0184, +0.0053] (n=32)  |
| CS_SINGLE|SB_R_early|HC-v|age | age_years | +0.0020 [-0.0240, +0.0279] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|SB_R_late|HC|age | age_years | +0.0010 [-0.0111, +0.0130] (n=37)  |
| CS_SINGLE|SB_R_late|CI|age | age_years | -0.0040 [-0.0152, +0.0072] (n=32)  |
| CS_SINGLE|SB_R_late|HC-v|age | age_years | -0.0226 [-0.0737, +0.0285] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|triad_R_early_minus_R_joint|HC|age | age_years | +0.0016 [-0.0132, +0.0164] (n=37)  |
| CS_SINGLE|triad_R_early_minus_R_joint|CI|age | age_years | +0.0030 [-0.0130, +0.0190] (n=32)  |
| CS_SINGLE|triad_R_early_minus_R_joint|HC-v|age | age_years | -0.0219 [-0.0694, +0.0256] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|triad_R_late_minus_R_joint|HC|age | age_years | -0.0036 [-0.0144, +0.0071] (n=37)  |
| CS_SINGLE|triad_R_late_minus_R_joint|CI|age | age_years | -0.0057 [-0.0172, +0.0059] (n=32)  |
| CS_SINGLE|triad_R_late_minus_R_joint|HC-v|age | age_years | -0.0043 [-0.0612, +0.0526] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_D_E|HC|age | age_years | +0.0055 [-0.0020, +0.0129] (n=37)  |
| CS_SINGLE|tg_D_E|CI|age | age_years | +0.0104 [-0.0033, +0.0240] (n=32)  |
| CS_SINGLE|tg_D_E|HC-v|age | age_years | -0.0043 [-0.0422, +0.0337] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_D_L|HC|age | age_years | -0.0012 [-0.0033, +0.0009] (n=37)  |
| CS_SINGLE|tg_D_L|CI|age | age_years | -0.0003 [-0.0025, +0.0020] (n=32)  |
| CS_SINGLE|tg_D_L|HC-v|age | age_years | +0.0060 [-0.0007, +0.0127] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_G_EL|HC|age | age_years | +0.0003 [+0.0000, +0.0006] (n=37)  |
| CS_SINGLE|tg_G_EL|CI|age | age_years | +0.0001 [-0.0005, +0.0007] (n=32)  |
| CS_SINGLE|tg_G_EL|HC-v|age | age_years | -0.0002 [-0.0021, +0.0017] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_G_LE|HC|age | age_years | +0.0003 [-0.0004, +0.0009] (n=37)  |
| CS_SINGLE|tg_G_LE|CI|age | age_years | +0.0009 [-0.0002, +0.0021] (n=32)  |
| CS_SINGLE|tg_G_LE|HC-v|age | age_years | +0.0009 [-0.0020, +0.0037] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_D_E_minus_G_EL|HC|age | age_years | +0.0051 [-0.0026, +0.0128] (n=37)  |
| CS_SINGLE|tg_D_E_minus_G_EL|CI|age | age_years | +0.0103 [-0.0030, +0.0236] (n=32)  |
| CS_SINGLE|tg_D_E_minus_G_EL|HC-v|age | age_years | -0.0041 [-0.0427, +0.0345] (n=16) HC-v ages linked by file-number order (inferred) |
| CS_SINGLE|tg_D_L_minus_G_LE|HC|age | age_years | -0.0014 [-0.0035, +0.0007] (n=37)  |
| CS_SINGLE|tg_D_L_minus_G_LE|CI|age | age_years | -0.0012 [-0.0038, +0.0014] (n=32)  |
| CS_SINGLE|tg_D_L_minus_G_LE|HC-v|age | age_years | +0.0051 [-0.0010, +0.0112] (n=16) HC-v ages linked by file-number order (inferred) |
| raw|raw_gain_early|HC|age | age_years | -0.0171 [-0.0321, -0.0021] (n=37)  |
| raw|raw_gain_early|CI|age | age_years | -0.0022 [-0.0284, +0.0241] (n=32)  |
| raw|raw_gain_early|HC-v|age | age_years | -0.0730 [-0.1387, -0.0074] (n=16) HC-v ages linked by file-number order (inferred) |
| raw|raw_gain_late|HC|age | age_years | -0.0008 [-0.0036, +0.0021] (n=37)  |
| raw|raw_gain_late|CI|age | age_years | +0.0001 [-0.0046, +0.0047] (n=32)  |
| raw|raw_gain_late|HC-v|age | age_years | -0.0186 [-0.0452, +0.0080] (n=16) HC-v ages linked by file-number order (inferred) |
| raw|raw_gain_late_minus_early|HC|age | age_years | +0.0163 [+0.0018, +0.0308] (n=37)  |
| raw|raw_gain_late_minus_early|CI|age | age_years | +0.0022 [-0.0226, +0.0271] (n=32)  |
| raw|raw_gain_late_minus_early|HC-v|age | age_years | +0.0544 [+0.0048, +0.1040] (n=16) HC-v ages linked by file-number order (inferred) |
| raw|neg_lag_mean_gain|HC|age | age_years | -0.0033 [-0.0062, -0.0004] (n=37)  |
| raw|neg_lag_mean_gain|CI|age | age_years | +0.0029 [-0.0037, +0.0094] (n=32)  |
| raw|neg_lag_mean_gain|HC-v|age | age_years | -0.0012 [-0.0210, +0.0187] (n=16) HC-v ages linked by file-number order (inferred) |

## 4. 功能（测量 ~ 窗口可读性 + 协变量；嵌套留一风险差为负 = 改善）

### FAU CI HSM（logit；协变量：年龄、CI 使用年限）
| 测量模型 | 可读性系数 [95% CI] (n) | 嵌套留一风险差（协变量+可读性 − 协变量；负 = 改善） |
|---|---|---|
| NCE|frozen_gain_early|hsm_logit|ci | +1.248 [-3.897, +6.393] (n=22) | +0.2000 [-0.0147, +0.4443] |
| NCE|frozen_gain_late|hsm_logit|ci | -0.698 [-5.336, +3.939] (n=22) | +0.2249 [+0.0410, +0.4402] |
| NCE|frozen_gain_late_minus_early|hsm_logit|ci | -1.220 [-4.743, +2.303] (n=22) | +0.0887 [-0.1414, +0.3704] |
| NCE|MD_R_early|hsm_logit|ci | +4.716 [-7.033, +16.465] (n=22) | +0.2098 [-0.2120, +0.7474] |
| NCE|MD_R_late|hsm_logit|ci | -2.279 [-5.528, +0.971] (n=22) | -0.1474 [-1.1383, +0.9787] |
| NCE|SB_R_early|hsm_logit|ci | -4.282 [-13.699, +5.135] (n=22) | +0.1299 [-0.5039, +0.9479] |
| NCE|SB_R_late|hsm_logit|ci | -1.649 [-4.347, +1.048] (n=22) | -0.0233 [-0.9164, +1.0613] |
| NCE|triad_R_early_minus_R_joint|hsm_logit|ci | -1.515 [-3.778, +0.749] (n=22) | -0.1351 [-1.0641, +0.9080] |
| NCE|triad_R_late_minus_R_joint|hsm_logit|ci | -1.407 [-5.597, +2.783] (n=22) | +0.2392 [-0.1872, +0.7626] |
| NCE|tg_D_E|hsm_logit|ci | -1.784 [-6.541, +2.973] (n=22) | +0.1359 [-0.1843, +0.6015] |
| NCE|tg_D_L|hsm_logit|ci | +1.259 [-2.592, +5.110] (n=22) | +0.1272 [-0.1458, +0.4617] |
| NCE|tg_G_EL|hsm_logit|ci | +0.203 [-5.522, +5.929] (n=22) | +0.2170 [+0.0750, +0.3858] |
| NCE|tg_G_LE|hsm_logit|ci | -1.429 [-9.961, +7.104] (n=22) | +0.2510 [+0.0434, +0.4956] |
| NCE|tg_D_E_minus_G_EL|hsm_logit|ci | -1.717 [-6.265, +2.832] (n=22) | +0.1194 [-0.2527, +0.6589] |
| NCE|tg_D_L_minus_G_LE|hsm_logit|ci | +2.192 [-2.295, +6.679] (n=22) | +0.0150 [-0.3556, +0.4623] |
| CS_SINGLE|frozen_gain_early|hsm_logit|ci | +3.543 [-0.640, +7.725] (n=22) | -0.1733 [-0.5856, +0.2786] |
| CS_SINGLE|frozen_gain_late|hsm_logit|ci | -0.239 [-4.240, +3.762] (n=22) | +0.1470 [+0.0648, +0.2352] |
| CS_SINGLE|frozen_gain_late_minus_early|hsm_logit|ci | -2.193 [-5.247, +0.862] (n=22) | -0.1000 [-0.4410, +0.2420] |
| CS_SINGLE|MD_R_early|hsm_logit|ci | +11.445 [-1.962, +24.851] (n=22) | -0.2379 [-0.9204, +0.4245] |
| CS_SINGLE|MD_R_late|hsm_logit|ci | -3.340 [-8.431, +1.751] (n=22) | -0.1399 [-1.1707, +0.9650] |
| CS_SINGLE|SB_R_early|hsm_logit|ci | +10.288 [-2.216, +22.793] (n=22) | -0.1795 [-0.8201, +0.4487] |
| CS_SINGLE|SB_R_late|hsm_logit|ci | -2.307 [-6.128, +1.513] (n=22) | -0.0083 [-0.8357, +0.9726] |
| CS_SINGLE|triad_R_early_minus_R_joint|hsm_logit|ci | -2.124 [-5.213, +0.964] (n=22) | -0.1441 [-1.0623, +0.9001] |
| CS_SINGLE|triad_R_late_minus_R_joint|hsm_logit|ci | -1.395 [-9.313, +6.523] (n=22) | +0.3722 [+0.1105, +0.7570] |
| CS_SINGLE|tg_D_E|hsm_logit|ci | -3.693 [-9.337, +1.951] (n=22) | -0.1101 [-0.6618, +0.5087] |
| CS_SINGLE|tg_D_L|hsm_logit|ci | +0.844 [-3.523, +5.211] (n=22) | +0.1637 [-0.0154, +0.3853] |
| CS_SINGLE|tg_G_EL|hsm_logit|ci | -1.352 [-8.098, +5.394] (n=22) | +0.2357 [+0.0551, +0.4690] |
| CS_SINGLE|tg_G_LE|hsm_logit|ci | -5.007 [-11.883, +1.870] (n=22) | -0.0608 [-0.4473, +0.3285] |
| CS_SINGLE|tg_D_E_minus_G_EL|hsm_logit|ci | -2.290 [-6.228, +1.648] (n=22) | -0.0382 [-0.3778, +0.3514] |
| CS_SINGLE|tg_D_L_minus_G_LE|hsm_logit|ci | +3.144 [-1.119, +7.407] (n=22) | -0.1190 [-0.4926, +0.2816] |
| raw|raw_gain_early|hsm_logit|ci | +5.200 [-5.647, +16.047] (n=22) | +0.0314 [-0.4862, +0.7417] |
| raw|raw_gain_late|hsm_logit|ci | -1.183 [-6.734, +4.367] (n=22) | +0.1718 [+0.0071, +0.4003] |
| raw|raw_gain_late_minus_early|hsm_logit|ci | -2.204 [-6.635, +2.226] (n=22) | -0.0080 [-0.3625, +0.4425] |
| raw|neg_lag_mean_gain|hsm_logit|ci | -28.590 [-102.662, +45.482] (n=22) | +0.4995 [+0.0323, +0.9764] |
| raw|noica_raw_gain_early|hsm_logit|ci | +0.366 [-2.290, +3.022] (n=22) | +0.3880 [-0.0130, +0.8873] |
### DTU（SRT、SSQ-speech；协变量：年龄、PTA）
| 测量模型 | 可读性系数 [95% CI] (n) | 嵌套留一风险差（协变量+可读性 − 协变量；负 = 改善） |
|---|---|---|
| NCE|frozen_gain_early|srt|all | -0.271 [-1.591, +1.050] (n=44) | +0.0474 [+0.0107, +0.0924] |
| NCE|frozen_gain_early|ssq_speech|all | -0.164 [-1.984, +1.655] (n=44) | +0.1165 [+0.0371, +0.2237] |
| NCE|frozen_gain_late|srt|all | -0.785 [-2.192, +0.621] (n=44) | +0.0324 [-0.1148, +0.1952] |
| NCE|frozen_gain_late|ssq_speech|all | -1.326 [-2.614, -0.039] (n=44) | -0.0967 [-0.3342, +0.1610] |
| NCE|frozen_gain_late_minus_early|srt|all | -1.123 [-2.999, +0.752] (n=44) | +0.0277 [-0.1262, +0.1959] |
| NCE|frozen_gain_late_minus_early|ssq_speech|all | -2.344 [-4.454, -0.233] (n=44) | -0.1909 [-0.6365, +0.2060] |
| NCE|MD_R_early|srt|all | +0.338 [-2.659, +3.335] (n=44) | +0.0459 [+0.0098, +0.0952] |
| NCE|MD_R_early|ssq_speech|all | +2.238 [-2.535, +7.011] (n=44) | +0.0568 [-0.1551, +0.2934] |
| NCE|MD_R_late|srt|all | -1.749 [-2.944, -0.553] (n=44) | -0.1622 [-0.4431, +0.0748] |
| NCE|MD_R_late|ssq_speech|all | -2.250 [-4.050, -0.451] (n=44) | -0.2487 [-0.6775, +0.1925] |
| NCE|SB_R_early|srt|all | -1.727 [-5.445, +1.991] (n=44) | +0.0205 [-0.0504, +0.0925] |
| NCE|SB_R_early|ssq_speech|all | +0.839 [-4.519, +6.198] (n=44) | +0.0878 [+0.0107, +0.1986] |
| NCE|SB_R_late|srt|all | -1.537 [-2.506, -0.568] (n=44) | -0.1614 [-0.4169, +0.0563] |
| NCE|SB_R_late|ssq_speech|all | -1.806 [-3.337, -0.275] (n=44) | -0.1971 [-0.5661, +0.1672] |
| NCE|triad_R_early_minus_R_joint|srt|all | -1.093 [-1.873, -0.313] (n=44) | -0.1199 [-0.3335, +0.0783] |
| NCE|triad_R_early_minus_R_joint|ssq_speech|all | -1.519 [-2.849, -0.189] (n=44) | -0.2095 [-0.6229, +0.2492] |
| NCE|triad_R_late_minus_R_joint|srt|all | -0.774 [-2.480, +0.931] (n=44) | +0.0190 [-0.0400, +0.0845] |
| NCE|triad_R_late_minus_R_joint|ssq_speech|all | -0.231 [-3.248, +2.785] (n=44) | +0.1225 [+0.0524, +0.2027] |
| NCE|tg_D_E|srt|all | +0.141 [-1.313, +1.596] (n=44) | +0.0467 [+0.0136, +0.1007] |
| NCE|tg_D_E|ssq_speech|all | -0.052 [-2.109, +2.004] (n=44) | +0.0964 [+0.0558, +0.1456] |
| NCE|tg_D_L|srt|all | +0.781 [-0.723, +2.284] (n=44) | +0.0263 [-0.0708, +0.1310] |
| NCE|tg_D_L|ssq_speech|all | +1.372 [-0.332, +3.075] (n=44) | -0.0363 [-0.2419, +0.1813] |
| NCE|tg_G_EL|srt|all | -0.066 [-1.734, +1.602] (n=44) | +0.0448 [+0.0183, +0.0788] |
| NCE|tg_G_EL|ssq_speech|all | +1.641 [-0.576, +3.858] (n=44) | -0.0284 [-0.2396, +0.2126] |
| NCE|tg_G_LE|srt|all | +0.265 [-1.460, +1.990] (n=44) | +0.0417 [+0.0126, +0.0791] |
| NCE|tg_G_LE|ssq_speech|all | -0.113 [-2.735, +2.509] (n=44) | +0.1015 [+0.0528, +0.1560] |
| NCE|tg_D_E_minus_G_EL|srt|all | +0.479 [-2.017, +2.974] (n=44) | +0.0473 [-0.0065, +0.1139] |
| NCE|tg_D_E_minus_G_EL|ssq_speech|all | -3.128 [-6.666, +0.410] (n=44) | -0.1075 [-0.4978, +0.2930] |
| NCE|tg_D_L_minus_G_LE|srt|all | +1.477 [-0.598, +3.552] (n=44) | -0.0029 [-0.1254, +0.1229] |
| NCE|tg_D_L_minus_G_LE|ssq_speech|all | +3.428 [+0.171, +6.685] (n=44) | -0.1797 [-0.5672, +0.2162] |
| CS_SINGLE|frozen_gain_early|srt|all | +0.013 [-1.515, +1.541] (n=44) | +0.0569 [+0.0206, +0.1044] |
| CS_SINGLE|frozen_gain_early|ssq_speech|all | +0.379 [-1.660, +2.418] (n=44) | +0.0959 [+0.0343, +0.1644] |
| CS_SINGLE|frozen_gain_late|srt|all | -0.722 [-2.401, +0.956] (n=44) | +0.0770 [-0.0780, +0.2992] |
| CS_SINGLE|frozen_gain_late|ssq_speech|all | -1.528 [-3.064, +0.007] (n=44) | -0.0931 [-0.3751, +0.2216] |
| CS_SINGLE|frozen_gain_late_minus_early|srt|all | -1.036 [-2.927, +0.856] (n=44) | +0.0470 [-0.1443, +0.2884] |
| CS_SINGLE|frozen_gain_late_minus_early|ssq_speech|all | -2.541 [-4.700, -0.383] (n=44) | -0.2576 [-0.7769, +0.2641] |
| CS_SINGLE|MD_R_early|srt|all | +0.653 [-3.327, +4.633] (n=44) | +0.0440 [+0.0074, +0.0918] |
| CS_SINGLE|MD_R_early|ssq_speech|all | +3.837 [-1.593, +9.266] (n=44) | -0.0125 [-0.2356, +0.2082] |
| CS_SINGLE|MD_R_late|srt|all | -2.241 [-4.094, -0.387] (n=44) | -0.1238 [-0.4251, +0.1509] |
| CS_SINGLE|MD_R_late|ssq_speech|all | -2.570 [-5.020, -0.119] (n=44) | -0.1743 [-0.5655, +0.2160] |
| CS_SINGLE|SB_R_early|srt|all | +0.757 [-4.748, +6.262] (n=44) | +0.0526 [+0.0158, +0.0988] |
| CS_SINGLE|SB_R_early|ssq_speech|all | +6.248 [-0.655, +13.152] (n=44) | -0.0802 [-0.3674, +0.2029] |
| CS_SINGLE|SB_R_late|srt|all | -1.662 [-3.094, -0.229] (n=44) | -0.0843 [-0.3078, +0.1168] |
| CS_SINGLE|SB_R_late|ssq_speech|all | -1.987 [-4.030, +0.056] (n=44) | -0.1195 [-0.4244, +0.1813] |
| CS_SINGLE|triad_R_early_minus_R_joint|srt|all | -1.480 [-2.584, -0.375] (n=44) | -0.1352 [-0.4171, +0.1132] |
| CS_SINGLE|triad_R_early_minus_R_joint|ssq_speech|all | -1.397 [-2.840, +0.046] (n=44) | -0.1095 [-0.4246, +0.2026] |
| CS_SINGLE|triad_R_late_minus_R_joint|srt|all | -1.007 [-2.856, +0.842] (n=44) | +0.0134 [-0.0484, +0.0727] |
| CS_SINGLE|triad_R_late_minus_R_joint|ssq_speech|all | +1.721 [-1.163, +4.604] (n=44) | +0.0068 [-0.1801, +0.1992] |
| CS_SINGLE|tg_D_E|srt|all | +0.143 [-1.374, +1.660] (n=44) | +0.0459 [+0.0162, +0.0855] |
| CS_SINGLE|tg_D_E|ssq_speech|all | -0.247 [-2.470, +1.977] (n=44) | +0.1010 [+0.0459, +0.1661] |
| CS_SINGLE|tg_D_L|srt|all | +0.855 [-1.011, +2.721] (n=44) | +0.0423 [-0.0562, +0.1648] |
| CS_SINGLE|tg_D_L|ssq_speech|all | +1.568 [-0.522, +3.657] (n=44) | -0.0215 [-0.2420, +0.2114] |
| CS_SINGLE|tg_G_EL|srt|all | -0.265 [-1.857, +1.327] (n=44) | +0.0321 [+0.0066, +0.0633] |
| CS_SINGLE|tg_G_EL|ssq_speech|all | +2.095 [-0.392, +4.583] (n=44) | -0.0572 [-0.3271, +0.2391] |
| CS_SINGLE|tg_G_LE|srt|all | +0.223 [-1.541, +1.988] (n=44) | +0.0422 [+0.0120, +0.0804] |
| CS_SINGLE|tg_G_LE|ssq_speech|all | -0.312 [-3.149, +2.526] (n=44) | +0.1096 [+0.0439, +0.1809] |
| CS_SINGLE|tg_D_E_minus_G_EL|srt|all | +0.739 [-1.626, +3.104] (n=44) | +0.0435 [-0.0392, +0.1552] |
| CS_SINGLE|tg_D_E_minus_G_EL|ssq_speech|all | -3.872 [-7.219, -0.526] (n=44) | -0.2163 [-0.7028, +0.2662] |
| CS_SINGLE|tg_D_L_minus_G_LE|srt|all | +1.408 [-1.209, +4.026] (n=44) | +0.0314 [-0.0988, +0.1920] |
| CS_SINGLE|tg_D_L_minus_G_LE|ssq_speech|all | +3.675 [+0.043, +7.306] (n=44) | -0.1851 [-0.5883, +0.2324] |
| raw|raw_gain_early|srt|all | +0.102 [-1.452, +1.657] (n=44) | +0.0439 [+0.0146, +0.0836] |
| raw|raw_gain_early|ssq_speech|all | +0.033 [-2.537, +2.604] (n=44) | +0.1792 [+0.0523, +0.3952] |
| raw|raw_gain_late|srt|all | -1.332 [-3.251, +0.588] (n=44) | +0.0139 [-0.2038, +0.2626] |
| raw|raw_gain_late|ssq_speech|all | -1.873 [-3.573, -0.172] (n=44) | -0.1190 [-0.4165, +0.1696] |
| raw|raw_gain_late_minus_early|srt|all | -1.309 [-2.911, +0.293] (n=44) | -0.0060 [-0.2073, +0.2099] |
| raw|raw_gain_late_minus_early|ssq_speech|all | -1.761 [-3.809, +0.287] (n=44) | -0.0886 [-0.4547, +0.2585] |
| raw|neg_lag_mean_gain|srt|all | +0.138 [-4.531, +4.807] (n=44) | +0.0344 [+0.0148, +0.0606] |
| raw|neg_lag_mean_gain|ssq_speech|all | +4.058 [-3.001, +11.116] (n=44) | +0.0259 [-0.1441, +0.2065] |
### Federici behav_acc（组内；协变量：年龄）
| 测量模型 | 可读性系数 [95% CI] (n) | 嵌套留一风险差（协变量+可读性 − 协变量；负 = 改善） |
|---|---|---|
| NCE|frozen_gain_early|behav_acc|HC | +2.464 [-41.946, +46.875] (n=37) | +13.5209 [+6.0364, +22.5271] |
| NCE|frozen_gain_early|behav_acc|CI | +25.258 [-7.729, +58.244] (n=32) | -6.0740 [-48.5686, +36.6795] |
| NCE|frozen_gain_early|behav_acc|HC-v | +4.484 [-151.430, +160.398] (n=16) | +182.0509 [+9.7661, +467.1694] |
| NCE|frozen_gain_late|behav_acc|HC | -86.084 [-220.561, +48.393] (n=37) | +1.8004 [-34.4287, +41.8749] |
| NCE|frozen_gain_late|behav_acc|CI | -135.531 [-305.039, +33.977] (n=32) | -7.5599 [-54.7504, +44.8568] |
| NCE|frozen_gain_late|behav_acc|HC-v | +33.562 [-262.043, +329.167] (n=16) | +30.8373 [+5.8650, +70.3668] |
| NCE|frozen_gain_late_minus_early|behav_acc|HC | -10.311 [-54.057, +33.435] (n=37) | +13.6746 [-4.5255, +37.1581] |
| NCE|frozen_gain_late_minus_early|behav_acc|CI | -29.633 [-61.836, +2.570] (n=32) | -14.3971 [-65.5189, +37.3377] |
| NCE|frozen_gain_late_minus_early|behav_acc|HC-v | -3.031 [-167.741, +161.679] (n=16) | +230.5232 [+6.3741, +616.4939] |
| NCE|MD_R_early|behav_acc|HC | +21.494 [-30.050, +73.038] (n=37) | +7.2699 [-9.4772, +27.1249] |
| NCE|MD_R_early|behav_acc|CI | +67.465 [+20.645, +114.285] (n=32) | -39.9708 [-103.2983, +23.6366] |
| NCE|MD_R_early|behav_acc|HC-v | -44.516 [-242.287, +153.255] (n=16) | +66.0380 [-15.6972, +177.8938] |
| NCE|MD_R_late|behav_acc|HC | -8.931 [-41.350, +23.488] (n=37) | +9.2765 [-1.9667, +22.7319] |
| NCE|MD_R_late|behav_acc|CI | -17.559 [-67.680, +32.561] (n=32) | +18.0394 [-9.0318, +51.6815] |
| NCE|MD_R_late|behav_acc|HC-v | +35.607 [-64.344, +135.557] (n=16) | +25.7920 [-38.6168, +105.9665] |
| NCE|SB_R_early|behav_acc|HC | +13.788 [-44.646, +72.222] (n=37) | +11.5087 [+1.1295, +24.0838] |
| NCE|SB_R_early|behav_acc|CI | +59.705 [+12.547, +106.864] (n=32) | -32.8755 [-97.5672, +29.2495] |
| NCE|SB_R_early|behav_acc|HC-v | -20.701 [-213.675, +172.274] (n=16) | +60.3239 [+15.4702, +112.3949] |
| NCE|SB_R_late|behav_acc|HC | -11.035 [-39.312, +17.241] (n=37) | +6.8284 [-6.8684, +22.7094] |
| NCE|SB_R_late|behav_acc|CI | -3.379 [-46.548, +39.789] (n=32) | +22.5719 [+8.9869, +40.4014] |
| NCE|SB_R_late|behav_acc|HC-v | +25.420 [-77.690, +128.531] (n=16) | +58.8221 [-17.9689, +166.3853] |
| NCE|triad_R_early_minus_R_joint|behav_acc|HC | +1.001 [-36.121, +38.122] (n=37) | +10.6296 [+5.0852, +17.1240] |
| NCE|triad_R_early_minus_R_joint|behav_acc|CI | +0.856 [-46.277, +47.989] (n=32) | +24.3623 [+7.4943, +48.2590] |
| NCE|triad_R_early_minus_R_joint|behav_acc|HC-v | +24.678 [-72.964, +122.319] (n=16) | +59.9752 [-5.0709, +159.0276] |
| NCE|triad_R_late_minus_R_joint|behav_acc|HC | +14.622 [-35.499, +64.743] (n=37) | +9.4013 [-4.4018, +28.0191] |
| NCE|triad_R_late_minus_R_joint|behav_acc|CI | +34.703 [-12.161, +81.567] (n=32) | -3.9176 [-42.2701, +35.8925] |
| NCE|triad_R_late_minus_R_joint|behav_acc|HC-v | -42.869 [-139.132, +53.394] (n=16) | +1.1472 [-55.3358, +72.6248] |
| NCE|tg_D_E|behav_acc|HC | -10.273 [-61.146, +40.600] (n=37) | +13.8154 [+0.0357, +32.6691] |
| NCE|tg_D_E|behav_acc|CI | -35.827 [-79.600, +7.945] (n=32) | -6.0019 [-52.6513, +44.3427] |
| NCE|tg_D_E|behav_acc|HC-v | -1.055 [-175.082, +172.971] (n=16) | +171.6321 [+11.4276, +451.9331] |
| NCE|tg_D_L|behav_acc|HC | +76.213 [-117.026, +269.451] (n=37) | +8.7185 [-6.9865, +25.1697] |
| NCE|tg_D_L|behav_acc|CI | +129.851 [-108.443, +368.145] (n=32) | +4.8435 [-29.8425, +42.8853] |
| NCE|tg_D_L|behav_acc|HC-v | -58.920 [-583.794, +465.955] (n=16) | +35.6896 [+7.1760, +78.0819] |
| NCE|tg_G_EL|behav_acc|HC | +467.983 [-394.088, +1330.054] (n=37) | +3.5841 [-14.3801, +23.8276] |
| NCE|tg_G_EL|behav_acc|CI | -491.413 [-1988.078, +1005.251] (n=32) | +18.0940 [-16.4613, +63.8193] |
| NCE|tg_G_EL|behav_acc|HC-v | -700.178 [-3213.275, +1812.918] (n=16) | +71.9423 [+2.5720, +148.9434] |
| NCE|tg_G_LE|behav_acc|HC | -139.858 [-510.491, +230.774] (n=37) | +13.2063 [-14.0356, +47.9502] |
| NCE|tg_G_LE|behav_acc|CI | -305.058 [-633.231, +23.115] (n=32) | -7.3594 [-36.9357, +23.2259] |
| NCE|tg_G_LE|behav_acc|HC-v | +34.877 [-635.349, +705.103] (n=16) | +57.3030 [+16.9088, +113.1754] |
| NCE|tg_D_E_minus_G_EL|behav_acc|HC | -11.343 [-60.907, +38.221] (n=37) | +12.8172 [-1.2146, +31.8433] |
| NCE|tg_D_E_minus_G_EL|behav_acc|CI | -36.017 [-80.272, +8.239] (n=32) | -5.7116 [-52.3209, +44.4383] |
| NCE|tg_D_E_minus_G_EL|behav_acc|HC-v | -0.064 [-179.777, +179.649] (n=16) | +165.7105 [+11.1165, +433.4965] |
| NCE|tg_D_L_minus_G_LE|behav_acc|HC | +85.251 [-95.724, +266.225] (n=37) | +9.2774 [-16.4135, +36.9737] |
| NCE|tg_D_L_minus_G_LE|behav_acc|CI | +175.203 [-22.764, +373.170] (n=32) | -11.9618 [-61.7212, +39.4752] |
| NCE|tg_D_L_minus_G_LE|behav_acc|HC-v | -46.477 [-450.650, +357.696] (n=16) | +40.6357 [+15.8481, +68.3207] |
| CS_SINGLE|frozen_gain_early|behav_acc|HC | -6.351 [-43.547, +30.844] (n=37) | +9.9717 [+3.1775, +17.6007] |
| CS_SINGLE|frozen_gain_early|behav_acc|CI | +37.089 [+3.941, +70.237] (n=32) | -21.7815 [-75.2753, +29.9656] |
| CS_SINGLE|frozen_gain_early|behav_acc|HC-v | +20.530 [-105.477, +146.538] (n=16) | +54.4612 [+9.7164, +110.8987] |
| CS_SINGLE|frozen_gain_late|behav_acc|HC | -102.334 [-295.596, +90.928] (n=37) | +8.6776 [-18.7237, +37.2937] |
| CS_SINGLE|frozen_gain_late|behav_acc|CI | +0.063 [-230.416, +230.543] (n=32) | +31.1699 [+8.1296, +61.2915] |
| CS_SINGLE|frozen_gain_late|behav_acc|HC-v | +111.474 [-194.063, +417.012] (n=16) | +14.8632 [-27.1252, +59.8113] |
| CS_SINGLE|frozen_gain_late_minus_early|behav_acc|HC | +1.106 [-37.719, +39.931] (n=37) | +12.5629 [+6.7936, +19.2680] |
| CS_SINGLE|frozen_gain_late_minus_early|behav_acc|CI | -39.449 [-75.426, -3.471] (n=32) | -22.9106 [-79.1372, +30.6815] |
| CS_SINGLE|frozen_gain_late_minus_early|behav_acc|HC-v | -13.095 [-142.717, +116.526] (n=16) | +73.8544 [+15.3389, +149.8106] |
| CS_SINGLE|MD_R_early|behav_acc|HC | +15.493 [-25.887, +56.873] (n=37) | +7.6228 [-7.4885, +24.2465] |
| CS_SINGLE|MD_R_early|behav_acc|CI | +28.086 [-22.950, +79.122] (n=32) | +6.0533 [-29.9824, +48.0973] |
| CS_SINGLE|MD_R_early|behav_acc|HC-v | -66.475 [-126.839, -6.111] (n=16) | -31.1691 [-87.1552, +25.3404] |
| CS_SINGLE|MD_R_late|behav_acc|HC | -15.700 [-53.162, +21.763] (n=37) | +9.8068 [-11.6638, +33.0825] |
| CS_SINGLE|MD_R_late|behav_acc|CI | -5.414 [-42.429, +31.601] (n=32) | +13.7968 [+2.5886, +26.9934] |
| CS_SINGLE|MD_R_late|behav_acc|HC-v | +23.833 [-79.108, +126.775] (n=16) | +67.0412 [-7.5907, +188.7038] |
| CS_SINGLE|SB_R_early|behav_acc|HC | +2.559 [-49.087, +54.205] (n=37) | +14.3234 [+7.1218, +23.5260] |
| CS_SINGLE|SB_R_early|behav_acc|CI | +32.387 [-28.432, +93.206] (n=32) | +6.4601 [-28.2487, +46.7391] |
| CS_SINGLE|SB_R_early|behav_acc|HC-v | -97.007 [-172.137, -21.878] (n=16) | -46.4195 [-97.3548, +5.1417] |
| CS_SINGLE|SB_R_late|behav_acc|HC | -16.142 [-48.830, +16.545] (n=37) | +6.8838 [-15.0474, +30.2025] |
| CS_SINGLE|SB_R_late|behav_acc|CI | -3.253 [-54.504, +47.999] (n=32) | +19.4319 [+4.2754, +39.7275] |
| CS_SINGLE|SB_R_late|behav_acc|HC-v | +23.326 [-89.930, +136.582] (n=16) | +63.4112 [+4.9179, +150.0123] |
| CS_SINGLE|triad_R_early_minus_R_joint|behav_acc|HC | -0.478 [-20.646, +19.691] (n=37) | +5.4950 [+2.6363, +8.9367] |
| CS_SINGLE|triad_R_early_minus_R_joint|behav_acc|CI | -8.277 [-39.579, +23.024] (n=32) | +17.5161 [-0.6345, +42.2901] |
| CS_SINGLE|triad_R_early_minus_R_joint|behav_acc|HC-v | -3.738 [-88.829, +81.352] (n=16) | +68.4314 [+19.0358, +133.1665] |
| CS_SINGLE|triad_R_late_minus_R_joint|behav_acc|HC | +15.784 [-17.509, +49.077] (n=37) | +3.6748 [-7.9690, +15.6882] |
| CS_SINGLE|triad_R_late_minus_R_joint|behav_acc|CI | +31.795 [-15.093, +78.683] (n=32) | +0.4899 [-36.7879, +41.0246] |
| CS_SINGLE|triad_R_late_minus_R_joint|behav_acc|HC-v | -48.252 [-116.695, +20.190] (n=16) | -1.0255 [-91.6041, +114.4602] |
| CS_SINGLE|tg_D_E|behav_acc|HC | -2.605 [-45.780, +40.571] (n=37) | +10.7980 [+3.0777, +23.2153] |
| CS_SINGLE|tg_D_E|behav_acc|CI | -46.240 [-93.555, +1.075] (n=32) | -17.5175 [-73.8593, +39.8286] |
| CS_SINGLE|tg_D_E|behav_acc|HC-v | +23.994 [-119.279, +167.267] (n=16) | +74.8182 [-15.1499, +228.9182] |
| CS_SINGLE|tg_D_L|behav_acc|HC | -28.270 [-344.791, +288.250] (n=37) | +22.4314 [+4.4476, +45.8040] |
| CS_SINGLE|tg_D_L|behav_acc|CI | +54.147 [-257.647, +365.941] (n=32) | +25.5358 [+7.2037, +48.0326] |
| CS_SINGLE|tg_D_L|behav_acc|HC-v | -423.003 [-879.554, +33.547] (n=16) | -30.5978 [-102.1320, +47.5467] |
| CS_SINGLE|tg_G_EL|behav_acc|HC | -267.091 [-1823.199, +1289.016] (n=37) | +17.2073 [+2.1402, +40.5833] |
| CS_SINGLE|tg_G_EL|behav_acc|CI | +621.022 [-811.785, +2053.828] (n=32) | +10.9316 [-19.4981, +49.1997] |
| CS_SINGLE|tg_G_EL|behav_acc|HC-v | -512.203 [-2614.127, +1589.721] (n=16) | +23.0969 [-3.4897, +55.0597] |
| CS_SINGLE|tg_G_LE|behav_acc|HC | +446.219 [-408.399, +1300.836] (n=37) | +6.8021 [-32.0524, +50.6471] |
| CS_SINGLE|tg_G_LE|behav_acc|CI | -82.626 [-613.511, +448.260] (n=32) | +12.4794 [+2.0432, +25.2220] |
| CS_SINGLE|tg_G_LE|behav_acc|HC-v | +291.337 [-1937.315, +2519.989] (n=16) | +112.3927 [+12.2882, +230.3609] |
| CS_SINGLE|tg_D_E_minus_G_EL|behav_acc|HC | -2.267 [-45.566, +41.031] (n=37) | +10.9509 [+3.2204, +23.3383] |
| CS_SINGLE|tg_D_E_minus_G_EL|behav_acc|CI | -47.216 [-94.553, +0.121] (n=32) | -19.0290 [-75.7916, +38.5659] |
| CS_SINGLE|tg_D_E_minus_G_EL|behav_acc|HC-v | +24.377 [-119.757, +168.511] (n=16) | +74.3714 [-16.9878, +230.2259] |
| CS_SINGLE|tg_D_L_minus_G_LE|behav_acc|HC | -75.341 [-386.823, +236.142] (n=37) | +22.7850 [-4.4950, +64.7313] |
| CS_SINGLE|tg_D_L_minus_G_LE|behav_acc|CI | +54.137 [-193.772, +302.046] (n=32) | +19.5867 [+0.0636, +49.1659] |
| CS_SINGLE|tg_D_L_minus_G_LE|behav_acc|HC-v | -436.253 [-940.149, +67.643] (n=16) | -28.8223 [-103.4411, +53.3368] |
| raw|raw_gain_early|behav_acc|HC | +2.522 [-20.483, +25.528] (n=37) | +10.1220 [+3.7401, +19.0928] |
| raw|raw_gain_early|behav_acc|CI | +5.819 [-13.042, +24.679] (n=32) | +9.3377 [-3.7661, +23.9622] |
| raw|raw_gain_early|behav_acc|HC-v | -8.797 [-116.185, +98.591] (n=16) | +126.4841 [+20.2979, +256.4437] |
| raw|raw_gain_late|behav_acc|HC | +63.109 [-52.228, +178.447] (n=37) | +3.2671 [-14.9204, +22.6916] |
| raw|raw_gain_late|behav_acc|CI | -15.403 [-147.652, +116.846] (n=32) | +17.8389 [+6.8098, +31.4601] |
| raw|raw_gain_late|behav_acc|HC-v | -53.483 [-282.001, +175.035] (n=16) | +84.2975 [-21.2524, +262.8047] |
| raw|raw_gain_late_minus_early|behav_acc|HC | -0.405 [-24.983, +24.173] (n=37) | +10.2556 [+5.6670, +16.4082] |
| raw|raw_gain_late_minus_early|behav_acc|CI | -6.957 [-26.423, +12.509] (n=32) | +8.4087 [-5.2482, +23.0352] |
| raw|raw_gain_late_minus_early|behav_acc|HC-v | +4.818 [-125.571, +135.207] (n=16) | +176.0951 [+8.4182, +407.3316] |
| raw|neg_lag_mean_gain|behav_acc|HC | -78.993 [-236.566, +78.580] (n=37) | +12.1273 [-15.9046, +44.2331] |
| raw|neg_lag_mean_gain|behav_acc|CI | +75.417 [-49.526, +200.361] (n=32) | +18.4224 [-7.5051, +47.6479] |
| raw|neg_lag_mean_gain|behav_acc|HC-v | +101.924 [-127.812, +331.660] (n=16) | +10.3405 [-53.6786, +88.2240] |
