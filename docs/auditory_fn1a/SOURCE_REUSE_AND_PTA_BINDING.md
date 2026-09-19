# FN1-A：本轮依赖的来源与 PTA 绑定

只列**本轮实际依赖**的输入链。不重审全库，不把已核验的 427 文件/45 任务再当作一个科研工作包。

## 1. 输入链

| 角色 | 路径 | 本轮用途 |
|---|---|---|
| 临床行（A 与 MUSS 的来源列） | `private/clinical_003/clinical_rows_clean.csv` | 按**实际工作表行号**取 `IT_MAIS_MAIS` 与 `MUSS`、年龄、使用月数 |
| 修正后 PTA | `private/auditory_repair/pta_007/candidate_covariates.csv` | 较好耳裸耳/助听 PTA |
| 冻结的最早索引队列 | `private/auditory_fseries_archival/prepare_001/cohort.csv` | 身份、索引记录、工作表行、采集时间 |
| 信号清单 | `results/phase1_sources_001/source_manifest.csv` | 记录→信号文件定位、采样率 |
| 文件路径映射（私有） | `private/inventory_001/file_path_map.csv` | file_id→绝对路径 |

每个来源的 sha256 记入 `results/auditory_fn1a/FN1A_prepare_002/source_hashes.json`，并由档案锁绑定。

## 2. PTA 行键绑定（本轮的硬约束）

配置 `archive.source_row_key: actual_worksheet_row`、`historical_pta_table_allowed: false`。`prepare_archive` 对将要继承的表逐行跑行键守卫，并在偏移非零时**直接报错终止**：

```
pta_007（修正后）        ROW_KEY_ALIGNED                 offsets={0: 57}  未解析键 0
ha_covariates_004（历史） SEQUENTIAL_ROW_KEY_MISALIGNMENT offsets={3: 55}  未解析键 2
```

另有一道独立检查：索引队列中每条记录的 `clinical_row_id` 数字部分必须等于其 `worksheet_source_row`，否则 `INDEX_ROW_KEY_MISMATCH` 终止。历史错键表在配置层被禁止，在代码层不会被读入。

## 3. 信号处理：继承与新写的分界

**继承（显式 import，未重新推导）**：`auditory5.preprocessing` 的 `HA_CHANNELS`（20 通道规范顺序）、`fixed_sos`（Butterworth SOS，HP 4 阶 @0.5 Hz + LP 8 阶 @30 Hz）、`CausalPreprocessor`（选 20 → 平均参考 → 带状态因果 `sosfilt` → 固定栅格整数抽取）、`effective_impulse_support`；`auditory5.adapters.ha` 的 vendor 数字轨饱和规则（阈值取自 BDF 头的一个量化步长）。

实测每条记录：原始 1000 Hz → 处理后 250 Hz（抽取因子 4），滤波支持 **10.823 s**，保护区 **20.0 s**，与继承回执逐位一致。

**本轮新写**：固定栅格、与事件无关的 4 秒窗口选择（含两端 20 秒保护区——仓库既有 guard 只作用于启动端）；Welch 带功率（2 秒 Hann、50% 重叠、PSD×频率间隔、左闭右开、末带含 30 Hz）；采样率作为参数的 Hjorth。

**只读强制**：原始根目录实际属主可写，因此只读由导出器自己保证——每条记录导出前后 `stat`（大小与 mtime），不一致即 `SOURCE_CHANGED_DURING_EXPORT` 终止。全部 52 条通过。

## 4. 窗口 QC 实测（新规则，不等价于旧 epoch QC）

56 条记录、候选窗 134–206（中位 189）、合格窗 22–189（中位 156.5）、合格率 0.211–1.000（中位 0.860）。

**全部剔除都来自 `processed_ptp_channels`（处理后超过 150 µV 的通道多于 2/20），共 2869 个窗。零 vendor 饱和，零平坦失效。** 4 条记录合格窗不足 32，按方案记为 `signal_support_insufficient`，不放宽阈值补救，不做 QC 阈值搜索。
