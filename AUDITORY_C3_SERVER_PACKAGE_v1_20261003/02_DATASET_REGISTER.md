# 02 · 数据登记

信息分解需要刺激变量本身，所以音频可得性决定每个数据集能承担哪一级分析。下表人数来自原论文或数据页，不是已接入人数；不得合并成一个总 n。

| source_id | 人群 | 刺激变量可得性 | 承担的刺激对 | 角色 | P0 必须核对 |
| --- | --- | --- | --- | --- | --- |
| `fau_tud_ha` / `fau_tud_ci` / `fau_tud_th` | 成人 HA 29 / CI 24 / TH 29，同协议，戴各自临床设备 | 发布含刺激 wav → 可提取 Whisper/wav2vec2 逐层表示 | (Ac, L)；(Att, Ign) | 公开主线：H1–H3、H7 | 音频–EEG 对齐延迟；HDF5 中音频辅助通道（33 行示例的最后两行）必须剔除；`eeg`/`eeg_ica` 分支；逐人行为文件（HSM、ACALES、理解题）是否在发布包内 |
| `dtu_snhl` | 成人 HI 22 / NH 22，未戴机线性放大 | 公开只有包络；原始音频需向作者申请 | 申请前：(Att, Ign) 包络对与 TMIF；申请后：(Ac, L) | 听损程度轴；H2/H3 第二成人队列（条件性） | **D1：是否申请音频**；SRT 定义与单位；放大是否按个人听力图 |
| `federici_ci_children` | 3–18 岁 CI（先天/后天）/ HC / 声码器 HC | 只公开预处理 EEG 与包络，无故事音频 | 包络 TMIF；(包络, 包络起始) | 儿童 CI 时间信息会聚（H1 的儿科部分） | 预处理带宽与重采样率；**D2：带宽不足时只报长滞后**；题目级理解分可否连接 |
| `private_bdf_ha` | 儿童 6–186 月；HA 64 / NH 9；临床完整约 55–57 | 离散事件，变量完全已知 | (Cur, Hist) | H4、H5；私有不可替代一环 | 阶段人数按本次资格重算；配对访视规则沿用 V4（每儿童一对，最早–最晚确证采集） |
| `private_mff_ci` | CI 标签 13 名 / 39 条；非 CI 33 名 | 离散事件；无音频 | (Cur, Hist)；(δ/θ 证据, 高频证据) | H6 | 侧别字段；任务语义不恢复 |

不纳入：SparrKULee、Southampton、Etard（正常听力成人）。

## 决定点

- **D1** 是否向 DTU 作者申请原始音频。申请：语言层多一个成人听损队列，但等待回复期间 DTU 只做包络层；不申请：R1 的语言层结论只来自三联集。默认：发出申请，不阻塞 P0。
- **D2** Federici 预处理带宽若不支持早滞后（<150 ms）的 TMIF，只报长滞后部分，不插值、不上采样。

## 回执 schema（`V4_DATA_RECEIPTS/` 沿用，字段扩展）

```
source_id, version, doi_or_url, license, local_path, bytes, checksum,
signal_state, channel_table, aux_channels_removed, participant_count, trial_count,
stimulus_audio_available, stimulus_feature_cache (model, layer_ids, pca_k, sr_hz, sha),
behavior_files, linkage_status, prior_exposure, status_code
```

每个来源一份；未下载写 `METADATA_VERIFIED_NOT_DOWNLOADED`，不写任何"ready"。
