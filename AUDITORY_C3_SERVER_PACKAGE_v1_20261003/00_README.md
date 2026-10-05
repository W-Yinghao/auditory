# AUDITORY C3 SERVER PACKAGE v1（2026-10-03）

## 包的性质

- 这是 C3 路线（听觉设备使用者 EEG 的统一信息分解）的服务器执行包：候选研究方案 + 冻结前的度量规格 + 合成核对代码。**不是结果报告**，不含任何真实患者结果。
- 私有证据基准：`W-Yinghao/auditory@dfb154fdb83a96040154c5f755e8f4bd78901942`。执行前先记录服务器当前 SHA 与差异，不覆盖旧报告。
- 与旧包的关系：替换 `AUDITORY_PUBLIC_PRIVATE_SERVER_PACKAGE_v2` 的全部 story 文件；V4 的统计纪律（双侧、等效界、不自动退路、无硬信度门槛、技术错误可修正但要留痕）全部沿用；V3/V4 的"早窗归一化、晚窗分化"主张与 SRT 主线、个人参照校准均不再执行。
- 深度学习全部冻结：预训练语音模型（Whisper / wav2vec2）只做特征提取；私有端只用已有的冻结 EEGNet 逐试次证据。**不训练新的 EEG 模型，不微调。**

## 文件地图

| 文件 | 内容 | 读者 |
| --- | --- | --- |
| `01_STORY_AND_CLAIMS.md` | story、创新点、R1–R3、H1–H7 | 全体 |
| `02_DATASET_REGISTER.md` + `config/datasets.json` | 数据集、刺激变量可得性、角色、决定点 D1/D2、回执 schema | 服务器 |
| `03_MEASUREMENT_SPEC.md` + `config/measurement_spec.json` | 变量、估计器、降维、PID 度量、代理、滞后窗、ROI、冻结规则 | 服务器 |
| `04_PUBLIC_ANALYSIS.md` | 阳性对照、声学 vs 语言、注意、时间、功能 | 服务器 |
| `05_PRIVATE_ANALYSIS.md` | 当前 vs 历史、发育、阶段、CI 频带归属、披露 | 服务器 |
| `06_BENCHMARKS.md` | 五层对比基线与最小集合 | 全体 |
| `07_SERVER_EXECUTION.md` | 阶段、门槛、交付物、目录、登记表、计算与禁止项 | 服务器 |
| `08_SYNTHETIC_CHECKS.md` + `reference/`、`tests/` | 合成核对的内容、运行方式、预期输出 | 服务器 |
| `config/analysis_registry.tsv` | H1–H7 登记表模板（状态列由服务器维护） | 服务器 |
| `SERVER_START_PROMPT.md` | 可直接交给服务器代理的启动文本 | 服务器 |

## 状态码（每个数据来源、每个分析都必须带一个）

`METADATA_VERIFIED_NOT_DOWNLOADED` · `FILES_DOWNLOADED_SCHEMA_PENDING` · `STIMULUS_FEATURES_CACHED` · `SIGNAL_TASK_READY` · `BEHAVIOR_READY` · `FUNCTION_ENDPOINT_UNAVAILABLE` · `PREPROCESSED_ONLY` · `AUDIO_UNAVAILABLE` · `SOURCE_OR_ALIGNMENT_UNRESOLVED` · `FROZEN` · `RUN_COMPLETE` · `TECHNICALLY_UNEVALUABLE`

## 三条总原则

1. 先验证估计器，再做阳性对照，再做任何新分析（G1 → G2 → P3）。
2. 任何信息量只在偏差校正后、作组间或条件间比较时报告；绝对比特数不进摘要。
3. 公开与私有的定义同时冻结；不看公开结果后再选私有的变量定义。
