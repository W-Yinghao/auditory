# ST1 结果（中性报告）：做法一第一轮，刺激×时间解码画像

**运行：** `ST1_report_001`；预注册 `docs/auditory_st/ST1_PREREGISTRATION_FROZEN.md`（含附录 A/B）；配置 `configs/auditory_st_v1.yaml`。  
**性质：** 表格、区间、QC 与哈希。解释只到预注册第 6 节的机械判定；措辞另议。  
**单位：** 儿童 = 保守身份组；每个儿童等权；区间 = 以儿童为单位的 bootstrap（n=2000，seed 20260920）。  

## 1. 进入读出的数据

| lane | 儿童 | 记录 | 试次 | 类别 1 试次 | 窗口数 | post (s) | 保留记录（原因） |
|---|---|---|---|---|---|---|---|
| `mff_puretone` | 33 | 35 | 27121 | 4080 | 42 | 0.70 | M0088(record_support_below_minimum); M0348(record_support_below_minimum); M0379(record_support_below_minimum); M0445(record_support_below_minimum); M0467(record_support_below_minimum); M0508(record_support_below_minimum) |
| `mff_bapa` | 24 | 25 | 18807 | 2850 | 47 | 0.80 | M0539(record_support_below_minimum); M0589(record_support_below_minimum); M0593(record_support_below_minimum); M0617(record_support_below_minimum) |
| `bdf_puretone` | 73 | 83 | 74514 | 14866 | 39 | 0.64 | B4a77825e7c06(record_support_below_minimum) |
| `mff_unknown_event` | 38 | 58 | 30763 | 5745 | 43 | 0.72 | M0220(record_support_below_minimum); M0661(record_support_below_minimum); M0669(record_support_below_minimum); M0717(record_support_below_minimum); M0733(record_support_below_minimum); M0749(record_support_below_minimum); M0757(record_support_below_minimum); M0765(record_support_below_minimum); M0781(record_support_below_minimum); M0845(record_support_below_minimum); M0893(record_support_below_minimum); M1059(record_support_below_minimum); M1075(record_support_below_minimum); M1147(record_support_below_minimum); M1148(record_support_below_minimum); M0030(layout_channels_64_ne_majority_128); M0046(layout_channels_64_ne_majority_128) |

范围表（`results/auditory_st/ST1_scope_001`）：MFF 203 条记录 / 111 身份组，HA 93 条 / 78 身份组；事件读取 295/295。特征阶段每记录支持见 `results/auditory_st/ST1_features_001/record_support.csv`。

| lane | 记录 | 提取成功 | 满足支持（两类 ≥40 且 ≥4 块） |
|---|---|---|---|
| `bdf_puretone` | 84 | 84 | 83 |
| `mff_bapa` | 29 | 29 | 25 |
| `mff_puretone` | 41 | 41 | 35 |
| `mff_unknown_event` | 75 | 75 | 60 |

## 2. 参照

| lane | 类别先验 p(1) | 先验对数损失 (bits) | 历史模型对数损失 (bits) | 历史 bAcc | 历史 AUC |
|---|---|---|---|---|---|
| `mff_puretone` | 0.150 | 0.611 | 0.611 | 0.499 | 0.499 |
| `mff_bapa` | 0.152 | 0.617 | 0.618 | 0.489 | 0.492 |
| `bdf_puretone` | 0.199 | 0.719 | 0.518 | 0.755 | 0.837 |
| `mff_unknown_event` | 0.187 | 0.694 | 0.694 | 0.501 | 0.506 |

## 3. 固定时间带结果与预注册规则的机械判定（第 6 节 E1/E2）

判定规则：某带 AUC 区间下界 > 0.5 且 G_hist 区间下界 > 0 → 可读。G_prior 为校准后验相对类别先验的增益（附录 B1）。

| lane | 带 | 区间 (s) | 儿童 | AUC 均值 [95% CI] | 儿童 AUC>0.5 | bAcc 均值 [CI] | G_hist 均值 [CI] (bits) | 儿童 G_hist>0 | G_prior 均值 (CI 下界) | 规则判定 |
|---|---|---|---|---|---|---|---|---|---|---|
| `mff_puretone` | pre | [-0.20, 0.00) | 33 | 0.503 [0.495, 0.512] | 16/33 | 0.502 [0.495, 0.508] | +0.0000 [-0.0001, +0.0001] | 20/33 | 0.0000 (-0.0001) | 不满足 |
| `mff_puretone` | early | [0.05, 0.25) | 33 | 0.496 [0.487, 0.505] | 13/33 | 0.497 [0.490, 0.504] | -0.0001 [-0.0003, +0.0000] | 14/33 | -0.0001 (-0.0003) | 不满足 |
| `mff_puretone` | mid | [0.25, 0.45) | 33 | 0.506 [0.497, 0.515] | 19/33 | 0.505 [0.498, 0.511] | -0.0001 [-0.0002, -0.0000] | 8/33 | -0.0001 (-0.0002) | 不满足 |
| `mff_puretone` | late | [0.45, 0.70) | 33 | 0.496 [0.486, 0.505] | 18/33 | 0.498 [0.491, 0.504] | -0.0000 [-0.0001, +0.0000] | 10/33 | -0.0000 (-0.0000) | 不满足 |
| `mff_bapa` | pre | [-0.20, 0.00) | 24 | 0.493 [0.485, 0.502] | 8/24 | 0.493 [0.487, 0.500] | -0.0002 [-0.0006, -0.0000] | 7/24 | -0.0002 (-0.0006) | 不满足 |
| `mff_bapa` | early | [0.05, 0.25) | 24 | 0.502 [0.494, 0.510] | 13/24 | 0.504 [0.497, 0.511] | -0.0001 [-0.0003, -0.0000] | 8/24 | -0.0001 (-0.0004) | 不满足 |
| `mff_bapa` | mid | [0.25, 0.45) | 24 | 0.496 [0.489, 0.504] | 9/24 | 0.497 [0.491, 0.503] | -0.0001 [-0.0003, +0.0000] | 12/24 | -0.0001 (-0.0003) | 不满足 |
| `mff_bapa` | late | [0.45, 0.80) | 24 | 0.498 [0.489, 0.507] | 13/24 | 0.501 [0.494, 0.507] | -0.0003 [-0.0010, -0.0000] | 9/24 | -0.0004 (-0.0010) | 不满足 |
| `bdf_puretone` | pre | [-0.20, 0.00) | 73 | 0.509 [0.503, 0.514] | 43/73 | 0.506 [0.502, 0.510] | +0.0003 [+0.0000, +0.0007] | 39/73 | -0.0000 (-0.0001) | 可读 |
| `bdf_puretone` | early | [0.05, 0.25) | 73 | 0.512 [0.507, 0.517] | 51/73 | 0.510 [0.506, 0.514] | +0.0003 [+0.0000, +0.0007] | 41/73 | 0.0000 (-0.0000) | 可读 |
| `bdf_puretone` | mid | [0.25, 0.45) | 73 | 0.514 [0.509, 0.519] | 57/73 | 0.511 [0.507, 0.515] | +0.0005 [+0.0001, +0.0010] | 48/73 | 0.0002 (0.0001) | 可读 |
| `bdf_puretone` | late | [0.45, 0.64) | 73 | 0.513 [0.506, 0.520] | 52/73 | 0.510 [0.505, 0.515] | +0.0003 [+0.0000, +0.0006] | 44/73 | 0.0001 (-0.0001) | 可读 |
| `mff_unknown_event` | pre | [-0.20, 0.00) | 38 | 0.511 [0.498, 0.527] | 21/38 | 0.503 [0.496, 0.510] | +0.0001 [-0.0002, +0.0004] | 23/38 | 0.0001 (-0.0002) | 不满足 |
| `mff_unknown_event` | early | [0.05, 0.25) | 38 | 0.517 [0.505, 0.529] | 24/38 | 0.509 [0.502, 0.516] | -0.0005 [-0.0017, +0.0001] | 21/38 | -0.0006 (-0.0018) | 不满足 |
| `mff_unknown_event` | mid | [0.25, 0.45) | 38 | 0.522 [0.508, 0.536] | 28/38 | 0.508 [0.499, 0.517] | -0.0012 [-0.0031, -0.0001] | 13/38 | -0.0012 (-0.0031) | 不满足 |
| `mff_unknown_event` | late | [0.45, 0.72) | 38 | 0.504 [0.492, 0.516] | 21/38 | 0.499 [0.493, 0.505] | -0.0001 [-0.0002, +0.0000] | 18/38 | -0.0001 (-0.0002) | 不满足 |

## 4. 时间分辨曲线的峰值描述（描述性，不作为判定）

| lane | 刺激后 AUC 均值最大值 (窗口中心 s) | 该窗 95% CI | 刺激后 G_hist 均值最大值 (s) | 该窗 CI | 预刺激带 AUC 均值最大值 |
|---|---|---|---|---|---|
| `mff_puretone` | 0.511 (0.28) | [0.501, 0.522] | +0.0000 (0.08) | [-0.0001, +0.0002] | 0.507 |
| `mff_bapa` | 0.511 (0.24) | [0.498, 0.524] | +0.0001 (0.30) | [-0.0000, +0.0004] | 0.496 |
| `bdf_puretone` | 0.529 (0.28) | [0.520, 0.538] | +0.0009 (0.28) | [+0.0003, +0.0017] | 0.514 |
| `mff_unknown_event` | 0.550 (0.22) | [0.520, 0.584] | +0.0030 (0.22) | [-0.0001, +0.0088] | 0.519 |

## 5. 跨时间读取（E4，描述性）

- `mff_puretone`：对角线（同窗）刺激后均值 AUC 0.499，最大 0.511；非对角刺激后子矩阵均值 0.502，最大 0.518；预刺激训练→刺激后测试均值 0.495。图：`/home/infres/yinwang/EEG_auditory/figures/auditory_st/ST1_report_001/tg_mff_puretone.png`
- `mff_bapa`：对角线（同窗）刺激后均值 AUC 0.499，最大 0.511；非对角刺激后子矩阵均值 0.500，最大 0.526；预刺激训练→刺激后测试均值 0.498。图：`/home/infres/yinwang/EEG_auditory/figures/auditory_st/ST1_report_001/tg_mff_bapa.png`
- `bdf_puretone`：对角线（同窗）刺激后均值 AUC 0.513，最大 0.529；非对角刺激后子矩阵均值 0.501，最大 0.530；预刺激训练→刺激后测试均值 0.497。图：`/home/infres/yinwang/EEG_auditory/figures/auditory_st/ST1_report_001/tg_bdf_puretone.png`
- `mff_unknown_event`：对角线（同窗）刺激后均值 AUC 0.514，最大 0.550；非对角刺激后子矩阵均值 0.500，最大 0.549；预刺激训练→刺激后测试均值 0.503。图：`/home/infres/yinwang/EEG_auditory/figures/auditory_st/ST1_report_001/tg_mff_unknown_event.png`

## 6. 独立时间块重复性（E5）与儿童内次要分析

| lane | 划分 | 儿童 | early 带 Spearman(AUC) 均值 | mid 带 | late 带 | early 带 |A−B| 均值 / 儿童间 SD |
|---|---|---|---|---|---|---|
| `mff_puretone` | early_late_halves | 33 | 0.252 | 0.145 | 0.302 | 0.041 / 0.036 |
| `mff_puretone` | odd_even_blocks | 33 | 0.308 | 0.148 | 0.113 | 0.050 / 0.042 |
| `mff_bapa` | early_late_halves | 24 | 0.016 | 0.146 | 0.060 | 0.047 / 0.030 |
| `mff_bapa` | odd_even_blocks | 24 | 0.053 | -0.023 | 0.031 | 0.057 / 0.039 |
| `bdf_puretone` | early_late_halves | 73 | 0.399 | 0.217 | 0.278 | 0.036 / 0.038 |
| `bdf_puretone` | odd_even_blocks | 73 | 0.262 | 0.273 | 0.209 | 0.049 / 0.042 |
| `mff_unknown_event` | early_late_halves | 38 | 0.340 | 0.405 | 0.276 | 0.045 / 0.084 |
| `mff_unknown_event` | odd_even_blocks | 38 | 0.327 | 0.223 | 0.124 | 0.056 / 0.085 |

- `mff_puretone` 儿童内（块 A 训练→块 B 测试，early_late_halves，33 名儿童 / 66 个方向）：刺激后 AUC 均值最大 0.574 [0.551, 0.598] @ 0.18 s；刺激后各窗均值 0.532。
- `mff_puretone` 儿童内（块 A 训练→块 B 测试，odd_even_blocks，31 名儿童 / 62 个方向）：刺激后 AUC 均值最大 0.574 [0.552, 0.599] @ 0.16 s；刺激后各窗均值 0.534。
- `mff_bapa` 儿童内（块 A 训练→块 B 测试，early_late_halves，21 名儿童 / 42 个方向）：刺激后 AUC 均值最大 0.547 [0.523, 0.576] @ 0.10 s；刺激后各窗均值 0.514。
- `mff_bapa` 儿童内（块 A 训练→块 B 测试，odd_even_blocks，20 名儿童 / 40 个方向）：刺激后 AUC 均值最大 0.542 [0.518, 0.570] @ 0.10 s；刺激后各窗均值 0.514。
- `bdf_puretone` 儿童内（块 A 训练→块 B 测试，early_late_halves，73 名儿童 / 146 个方向）：刺激后 AUC 均值最大 0.545 [0.536, 0.555] @ 0.16 s；刺激后各窗均值 0.522。
- `bdf_puretone` 儿童内（块 A 训练→块 B 测试，odd_even_blocks，73 名儿童 / 146 个方向）：刺激后 AUC 均值最大 0.542 [0.532, 0.553] @ 0.16 s；刺激后各窗均值 0.520。
- `mff_unknown_event` 儿童内（块 A 训练→块 B 测试，early_late_halves，36 名儿童 / 72 个方向）：刺激后 AUC 均值最大 0.655 [0.617, 0.694] @ 0.24 s；刺激后各窗均值 0.570。
- `mff_unknown_event` 儿童内（块 A 训练→块 B 测试，odd_even_blocks，34 名儿童 / 68 个方向）：刺激后 AUC 均值最大 0.634 [0.592, 0.682] @ 0.24 s；刺激后各窗均值 0.568。

## 7. 探针与 QC 披露

探针 `ST1_probe_002`（记录 M0015，lane mff_puretone）：门 = PASS；两次提取逐位一致 True；窗口 42；接受试次 807/998（类别 {'0': 691, '1': 116}）。单记录类别差异统计：平均 |z| 预刺激 0.086 / 刺激后 0.070；SE 标准化每窗最大 |z| 预刺激 2.60 / 刺激后 2.36；|z|>2 通道比例预刺激 0.059 / 刺激后 0.031。这些值与纯噪声期望一致（附录 B2），单记录检查无功效，不作门。

QC 规则：epoch 峰峰值 >150 µV 的通道占比 >10% 或 <0.5 µV 占比 >10% 则拒绝；区间边缘 2 s 保护；记录尺度 = 接受 epoch |x| 中位数。各记录接受数见 `record_support.csv`。

## 8. 图

- mff_puretone_curves: `figures/auditory_st/ST1_report_001/curves_mff_puretone.png`
- mff_puretone_tg: `figures/auditory_st/ST1_report_001/tg_mff_puretone.png`
- mff_puretone_repeatability: `figures/auditory_st/ST1_report_001/repeatability_mff_puretone.png`
- mff_bapa_curves: `figures/auditory_st/ST1_report_001/curves_mff_bapa.png`
- mff_bapa_tg: `figures/auditory_st/ST1_report_001/tg_mff_bapa.png`
- mff_bapa_repeatability: `figures/auditory_st/ST1_report_001/repeatability_mff_bapa.png`
- bdf_puretone_curves: `figures/auditory_st/ST1_report_001/curves_bdf_puretone.png`
- bdf_puretone_tg: `figures/auditory_st/ST1_report_001/tg_bdf_puretone.png`
- bdf_puretone_repeatability: `figures/auditory_st/ST1_report_001/repeatability_bdf_puretone.png`
- mff_unknown_event_curves: `figures/auditory_st/ST1_report_001/curves_mff_unknown_event.png`
- mff_unknown_event_tg: `figures/auditory_st/ST1_report_001/tg_mff_unknown_event.png`
- mff_unknown_event_repeatability: `figures/auditory_st/ST1_report_001/repeatability_mff_unknown_event.png`
- overview: `figures/auditory_st/ST1_report_001/overview_lanes.png`

## 9. 哈希与运行

- `ST1_readout_mff_puretone_001`（config sha256 `07523e299f81144a…`，prereg sha256 `a0624c6bfff13897…`）：bands.csv `b311a61335f0`, curves.csv `54f3ff3b49c9`, repeatability.csv `ce1b0e32b6d6`, summary.json `883edfe2faa4`, tg_auc_mean.csv `bdc034dfec07`, within_child.csv `0fc924bf0f53`
- `ST1_readout_mff_bapa_001`（config sha256 `07523e299f81144a…`，prereg sha256 `a0624c6bfff13897…`）：bands.csv `987671867210`, curves.csv `363c1e562bfe`, repeatability.csv `afb4e47066e6`, summary.json `182f4379c362`, tg_auc_mean.csv `312b47a03ed8`, within_child.csv `414c56d6a274`
- `ST1_readout_bdf_puretone_001`（config sha256 `07523e299f81144a…`，prereg sha256 `a0624c6bfff13897…`）：bands.csv `617ffd014a49`, curves.csv `3320f0dcbc11`, repeatability.csv `9a4a197623ad`, summary.json `d4326f2d517d`, tg_auc_mean.csv `722694080a59`, within_child.csv `dcb5b0371416`
- `ST1_readout_mff_unknown_event_002`（config sha256 `07523e299f81144a…`，prereg sha256 `a0624c6bfff13897…`）：bands.csv `748b7fb13fe3`, curves.csv `9d533d682128`, repeatability.csv `60531e5e8415`, summary.json `6cc988766e4b`, tg_auc_mean.csv `7a62feead7e0`, within_child.csv `0283d5218f01`
- 范围表：data_scope_table.csv `08b9777e66e8`, record_support_table.csv `25a02bbfbf10`, task_event_table.csv `5e40fafe6433`

## 10. 本报告不包含

成分命名、任务难度排序、听觉能力解释、与年龄/设备/量表的关系（做法二/四/五另行预注册）。
