# C3 刺激特征清单（复核补充第 1 项）

所有特征都只从刺激导出，不读取任何 EEG。缓存目录：`/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud/`，每个文件旁边有一个 `.done.json`，记录 sha256 和模型 revision。代码：`auditory_c3/features.py`、`auditory_c3/pca.py`。

## 1. 来源音频

- 每个刺激码和流（attended / distractor）取自 HA 文件的 `stimulus_files/<code>/<stream>_wav`（48 kHz，int32，与 EEG 已对齐）。CI 和 TH 文件中的副本逐数组 sha256 完全相同（120/120，`stimulus_copy_check.json`）。
- 48 kHz 用 `resample_poly(1, 3)` 降到 16 kHz（多相 FIR，SciPy 默认 Kaiser 窗抗混叠）。
- 单说话人试次的 distractor 是静音（RMS < 1e-6），只标记 `silent`，不编码。
- 时间零点为 wav 的第 0 个样本，也就是 EEG 试次的第 0 个样本（发布时已对齐；49 个试次另有按辅助通道重新对齐的 EEG 副本，见修正 001 §5）。

## 2. 模型与 revision

| 模型 | HF repo | revision | 用到的部分 | 输出 |
| --- | --- | --- | --- | --- |
| Whisper large-v3 | `openai/whisper-large-v3` | `06f233fe06e710322aca913c1bc4249a0d71fce1` | **只用编码器**；`output_hidden_states` 共 33 个，即 `layer_00` = 卷积前端加位置嵌入，`layer_01`…`layer_32` = 32 个 Transformer 层。最后一个隐状态经过最终的 LayerNorm | 1280 维，50 Hz，fp16 |
| Whisper log-mel | 同上 | 同上 | `WhisperFeatureExtractor` 的输入谱（128 个 mel 带） | 100 Hz |
| wav2vec2 XLS-R 300M | `facebook/wav2vec2-xls-r-300m` | `1a640f32ac3e39899438a2931f9924c02f080a54` | `Wav2Vec2Model` 的 25 个隐状态（`layer_00` = 卷积特征投影后，`layer_01`…`layer_24`），fp32 推理，存成 fp16。输入按特征提取器做均值方差归一 | 1024 维，约 50 Hz |
| 转写 | Whisper large-v3（同一 revision） | — | transformers ASR pipeline，`language=german`，`task=transcribe`，`chunk_length_s=30`，`return_timestamps="word"`（交叉注意力 DTW 词时标） | 32 个流共 10379 个词，0 个流失败 |
| 德语 GPT-2 | `dbmdz/german-gpt2` | `ab6efd04479f70d66df40e7bfcb17ba41e9cd6d5` | 词惊讶度 = 组成该词的子词 −log2 p 之和。分词时第一个词前不加空格，其余词前加一个空格。上下文只限同一个流，用 1024 token 的滑窗、步长 512，每个位置只评分一次，且至少有 512 个前文 token | 每个词一个值（比特） |

GPT-2 的起始符：这个模型的词表里没有 `<|endoftext|>`。transformers 会把它追加到 id 50265，超出嵌入表；而 config 里 bos/eos = 50256，在这个词表中只是普通子词 "riegel"。因此用词表自带的 `<s>`（id 0）作为上下文起点，只影响每个流的第一个词。转写出的词带标点（例如 "streng,"），标点 token 计入惊讶度。

## 3. 切块、上下文与时间锚点

- **Whisper 编码器**：
  - 窗长 30 s，步长 20 s；每个窗只保留中间 20 s，两侧各舍弃 5 s 作为上下文。第一窗保留 [0, 25) s，最后一窗保留到末尾。
  - 最后一窗不足 30 s 时，由特征提取器补零到 30 s。
  - 帧 j 的中心时刻 = 窗起点 + j·20 ms + 10 ms（`frame_time_offset_s = 0.01`）。
  - **编码器在 30 s 窗内是双向的**：任一帧的表示可能包含该窗内前后各最多约 25 s 的音频信息，被保留帧两侧至少有 5 s 上下文。
- **XLS-R**：
  - 同样是 30 s/20 s 的窗，保留中心落在 [lo, hi) 内的帧。
  - 帧 i 的中心在 i·320 + 200 个 16 kHz 样本处（`frame_time_offset_s = 0.0125`）。
  - Transformer 部分同样双向（窗内）。
- **重采样到 EEG 网格（128 Hz）**：
  - PCA 的投影用 `resample_poly(64, 25)` 从 50 Hz 升到 128 Hz；log-mel 用 `resample_poly(32, 25)` 从 100 Hz 升到 128 Hz。
  - 帧中心偏移（10 ms 和 12.5 ms）**没有补偿**：特征样本 k 被当作时刻 k/128 s，即特征锚点比真实帧中心早约 10 ms（Whisper）或 12.5 ms（XLS-R）。这对 80 ms 以上的窗没有实质影响，但逐滞后曲线应理解为"相对于特征锚点"。
- **PCA**：只用刺激帧拟合（中心化协方差的特征分解），每个不同的波形只计一次（按 wav sha256 去重），取前 8 个成分（k = 3、5 为其嵌套子集）；分量符号按"载荷绝对值最大的坐标为正"固定。Ac = 第 1、2 层隐状态的逐帧平均再做 PCA（Whisper 浅层前 5 个成分解释约 16% 的方差）；log-mel 的前 5 个成分解释 90%。
- **分析前的滤波**：所有刺激侧变量都用与 EEG 相同的 1–8 Hz 零相位 FIR（MNE firwin，在 128 Hz 下）。

## 4. 解读限制（复核补充第 1、8 项）

- 深层表示的 TMIF/CMI 曲线是"相对于特征锚点的依赖曲线"，不是神经起始时间。由于编码器是双向的，负滞后上的依赖可能来自模型上下文，不一定是 EEG 泄漏。
- I(T; L | ŷ_Ac) 称为"深层表示增量"（在一份有限的声学摘要之上），不直接称为语言信息。语言解释还需要会聚证据：GPT-2 惊讶度、词起始、更丰富的声学参照（log-mel），见对照检查。


## 补记（2026-10-05）：第 27 层主成分的构成

冻结的 L27 PCA-5 解释该层 99.9% 的方差（FAU/TUD 与 DTU 相同），主要由 4 个高幅值坐标（695、1230、594、0）承载。
- PC1 占 99.85%，与窗内位置、能量、Ac 几乎无关（R² 0.04）。
- PC2 主要是声学（对 Ac 的 R² 0.93），并有 30 s 编码窗接缝处的跳变。
- 坐标标准化后的敏感性版本：`pca_k8_128hz_whisper_z27.h5`（前 5 个主成分解释 49%）。

详见 `results/auditory_c3/L27_diagnostic.json` 与 `POST_G1_CHANGELOG.md`。PCA 之后再做 copula 秩变换，所以 GCMI 对坐标幅值本身不敏感，但**主成分的方向由这些坐标决定**。

- 敏感性结果（`P3_l27z.json`）：深层增量在 Lz 版本中保持，甚至略大；主要由 PC2–5 承载，PC1 单独的贡献很小（`C3_RESULTS_v2.md` §1.3b）。
