# C3 落地与执行方案 v1（2026-10-04）

依据：`AUDITORY_C3_SERVER_PACKAGE_v1_20261003.zip`（sha256 `ae4087a1…a39a22ba`），已原样解压到同名目录，不改动。
私有基准：`/home/infres/yinwang/auditory_github` HEAD = `dfb154fdb83a96040154c5f755e8f4bd78901942` = origin HEAD，工作树干净，与包登记一致。

当前状态：P0 的下载与结构审计已完成（结果见 §6，它更新了 §1 中的若干条），P1 的包内核对已复现。**没有做任何真实组比较；没有计算任何 EEG 量；没有查看任何私有分组结果；没有用 GPU。**

---

## 0. 结论

1. 包能落地，执行骨架（G0→G1→G2→P3）不需要改。三份公开数据都在、许可都是 CC-BY，计算节点能直接下载。
2. **G1 冻结前有一处必须修的度量设计问题，已用合成数据证实（S9，§2.1）**：03 §3.4 主路径是"逐滞后估计"，L 只条件于同一滞后的 Ac。深层语音模型表示的时间感受野很长，所以这样算出的 I(T;L|Ac) 会把其他滞后上的声学信息记成"语言信息"，代理校正也去不掉。按原样冻结，H3 的组差可能完全由 TRF 形状差异产生。
3. **H7 的主终点数据不在公开发布中**：FAU/TUD 的 Zenodo 记录和 Jehn 的代码仓库里都没有逐人 HSM/ACALES/理解题数据。不另外申请的话，R3（功能）在 CI 成人组上无法评估。
4. 私有端 H4b、H5、H6 的预测在 GX/PF 里已经看过（§2.5）。这部分只能写成"换成比特单位后与已知结果一致或划出边界"，不能写成验证性主张。包的 5.5 已留了这个写法，冻结时需要把"已看过"逐条写进披露。

---

## 1. 今天已核实的事实（对照 02 登记）

| 来源 | 核实结果 | 与包的出入 |
| --- | --- | --- |
| `fau_tud_ha/ci/th` | Zenodo 17927767 / 17952844 / 17952231，CC-BY-4.0，分别 22.45 / 18.96 / 21.73 GB。三份记录的 `stimuli.zip` md5 相同（`bb8a7459…`），只下载一次。HDF5 每个试次 33 行，即 31 导 EEG 加 2 条音频辅助通道；CI 每人另去掉 2–4 个磁体附近电极（`taken_out_indices`）。每人 20 个试次：8 个单说话人、12 个竞争说话人，每个约 2 分钟，干扰流晚 10 s 开始。刺激是德语有声书（Elbenwald、Polarnacht），wav 48 kHz，HDF5 内另有 1 kHz 包络 | 包写"32 导"，实际可用 31 导。**`eeg_ica` 分支只在 HA 的说明文件里出现**，CI 和 TH 的说明文件（两份相同）没有提到，下载完成后核对 |
| FAU/TUD 行为 | 每个 Zenodo 记录只有 4 个文件（hdf5、stimuli、raw 示例、info）。代码仓库 `Constantin-Jehn/aad-neuroimage` 只有代码。论文（bioRxiv 10.64898/2025.12.22.695344，NeuroImage 2026）采集了 HSM（65/60 dB）、Freiburg、ACALES，以及每个试次 2 道三选一理解题 | **行为数据未公开** → H7a/H7b 目前为 `FUNCTION_ENDPOINT_UNAVAILABLE`（除非 HDF5 属性里有，下载后核对） |
| Jehn 2026 阳性对照 | 正文：CI 24 / HA 29 / TH 29；60 s 窗准确率 TH 87.8%、HA 88.5%、CI 63.1%；后向模型 1–8 Hz、128 个滞后（−500 到 500 ms）、ridge λ 10⁻⁷–10⁷、12 折；CI 伪迹：ICA 成分 SNR > 15 dB 剔除，**只用于前向模型**，后向模型不剔除伪迹；P1_TRF 23 ms（TH）/ 31 ms（HA）；CI 理解分与解码准确率 β = 0.236 | 与包一致。代码公开，H1a 可以直接用原作者流程复现 |
| `dtu_snhl` | Zenodo 3618205，CC-BY-4.0，一个 34.9 GB 的 BIDS tar。只有包络；原始音频需按数据集说明发邮件申请（联系邮箱见 Zenodo 3618205；发布版删去），主题 "ds-eeg-snhl audio"。`participants.tsv` 里有 SRT、理解题、SSQ、听力图。语言为丹麦语 | 与包一致（D1） |
| `federici_ci_children` | Mendeley 10.17632/nzg5g2gzrd.2，CC-BY-4.0，666 个文件 sha256 **全部核对通过**。EEG 文件数：HC 37、CI 33、HC-v 16、幻影头伪迹记录 9 条（3 次 × 双侧/左/右）。另有行为和描述表（理解准确率、年龄、CD/AD 分组）。语言为意大利语，只有预处理后的数据 | 包登记 CI 32，文件里是 33。**HC-v 的 16 个 ID 与 HC 的 1001… 重合**，是被试内条件而不是独立组，不能当作独立队列计数。幻影头记录可以直接作为 CI 伪迹的纯伪迹阴性对照（加到 4.6） |
| 私有 GX 缓存 | `predictions_shared.npz` 每个 seed×fold 存 `(test_idx, logit×2)`，试次顺序能从逐记录缓存恢复，可以重建历史变量。MFF 未知任务车道有 1–4、4–8、30–45 Hz 三个频带的缓存（allqc） | H6 不需要训练新模型 |
| 环境 | eeg2025 里已有 numpy、scipy、sklearn、pandas、h5py、mne、torch、transformers、soundfile；缺 gcmi、statsmodels、librosa；torchaudio 加载失败；**集群没有 MATLAB**；HF 缓存里没有 Whisper、wav2vec2、GPT-2；计算节点能联网 | — |
| P1 包内核对 | `tests/` 8/8 通过；`synthetic_checks.py` 的 S1–S8 与包附带的 `checks_c3.json` 完全一致（Slurm 1020901；在副本上运行，未覆盖包内文件） | — |

---

## 2. G1 冻结前需要处理的问题（按严重程度）

### 2.1 【已证实】单滞后条件化会把"其他滞后的声学"记成语言信息（新增核对 S9）

构造：Ac 为 AR(1) 声学变量（64 Hz）；L0 是 Ac 的双侧 300 ms 平滑加噪声，**除 Ac 之外不含任何信息**；EEG 为 Ac 经 0–300 ms TRF 卷积后加噪声。阳性对照另加一个独立成分 W 同时进入 L 和 EEG。取滞后 94 ms，n = 60000，n_sur = 20（Slurm 1020908，`private/auditory_c3/p1_synthetic_001/s9_multilag_conditioning.{py,json}`）。

| 偏差校正后（比特） | 单滞后 I(T;L_τ\|Ac_τ)（03 §3.4 原写法） | 条件于整段 Ac 滞后窗（−200 到 600 ms） | 预测中介 I(T;L_τ\|ŷ_Ac) |
| --- | --- | --- | --- |
| 零生成器（L 无额外信息） | **0.0597**（代理均值 0.00004） | −0.00001 | −0.0001 |
| 阳性生成器 | 0.1861 | 0.1408 | 0.1122 |

单滞后版本在零生成器上给出的假信号，量级与真实信号相当。循环移位代理会把 L 和 Ac 一起平移，所以去不掉这部分。CI 的 TRF 形状与 TH/HA 不同，这个偏差在各组之间也会不同，可能凭空造出 H3 的组差。

**建议修正（冻结前）**：H3 以及所有"A 之上的 B"类 CMI 和 PID 项，主判据都要条件于整段声学滞后窗：把 Ac 在 [−200, 600] ms 内的滞后堆叠后降维，或者用 ridge 交叉验证预测 ŷ_Ac（也就是把 §3.4 的"预测中介"路径提为主路径）。单滞后版本作为敏感性照报。S9 写进 08 和 `tests/`。这一改动属于技术修正，按 3.11 留痕。

### 2.2 H7 主终点不可得（新决定点 D3）

方案 A（推荐）：向 Jehn/Vavatzanidis 申请逐人 HSM、ACALES、理解题数据，不阻塞 P0–P2。方案 B：H7 只做 DTU（SRT，组内）和 Federici（理解题，可连接），两者都是次终点。在申请有结果之前，H7a/H7b 的状态写 `FUNCTION_ENDPOINT_UNAVAILABLE`，R3 不进摘要。

### 2.3 CI 伪迹处理在各组之间必须对称

**已由 P0 审计确认（§6）：三个文件都没有 `eeg_ica` 分支。** 三组都从原始 `eeg` 出发，用同一套流程：Jehn 的 ICA–音频相关、SNR > 15 dB 规则对三组都执行，而不是只对 CI 执行；原始版本和清理后版本都报告。诊断窗 [−200, 0) 之外，再用 Federici 的幻影头记录估计纯伪迹能产生多少 TMIF。

### 2.4 H5 的发育协变量：EEGage 有测量误差

BDF 年龄模型的 MAE 约 24 个月。用带噪协变量做调整会调整不足，佩戴时长又与日历月龄相关，残余混杂会抬高 β_D。这和 D2 记录的"未校正脑龄差与佩戴时长 r = −0.509（伪相关）"是同一机制。建议主协变量用日历月龄，EEGage 作为敏感性分析，或者两者都进模型。

### 2.5 私有端预测已被看过（必须写进 5.6 披露和登记表 notes）

- **H4b "I(T;Hist|Cur) ≈ 0"**：GX R3_memory 已经发现 HA 有一步历史效应：紧接在偏差之后的偏差最难读出，按前置标准数 0 分层是 −0.004，其后约 +0.03 logit。包里"与 GX 的历史不增益一致"这句表述不准确。预测方向本身有风险，而且无论结果如何都不是盲测。
- **H5 "佩戴时长在发育之上无信息"**：PF、GX、D2 都已经得到这个结果。
- **H6 "高频证据集中在 0–80 ms"**：GX R5 §9b 已经得到。30–45 Hz 的证据集中在 0–80 ms 和约 0.36 s；与 δ/θ 读出在试次层面独立（|rho| ≤ 0.03）；CI 与非 CI 的拓扑相同。

这部分的价值是把已知结果换成与公开端同一单位、同一套偏差校正后的表达，相当于 5.5 的"边界"写法。

### 2.6 冻结时需要写明的次要问题

- **语言层选择与组比较重叠**：选层用 TH 的一半被试，这一半之后又进入 TH 对 CI/HA 的比较，会带来选择乐观。建议主比较用全部 TH，另以留出的一半 TH 做敏感性分析，并在规格里固定划分的种子。
- **H2 的 ±15% 等效界**：每组 24–29 人，追踪量的个体间变异通常很大，大概率达不到等效。需要预先写明读法："未达等效不等于有差异"，报告差异和精度。
- **I_ccs**：Ince 的参考实现是 MATLAB，集群没有 MATLAB。需要把高斯 I_ccs 移植成 Python，并用 Ince 2017 的高斯示例核对；核对不过就按包的规定，PID 层整体标 `TECHNICALLY_UNEVALUABLE`。生产用的 GCMI 用 robince/gcmi 的 Python 文件，固定 commit 后放进仓库。
- **德语词时间戳**：GPT-2 惊讶度和词起始两个基线都需要词级对齐，发布包里没有。需要用 Whisper-large-v3 转写并带词时间戳，或者做强制对齐。这一项要显式加进 P0。
- **固定模型版本**：whisper-large-v3（32 层，1280 维）、wav2vec2 用 `facebook/wav2vec2-xls-r-300m`（24 层）、德语 GPT-2 用 `dbmdz/german-gpt2`，都记录 HF revision。

---

## 3. 落地结构（沿用仓库惯例，对应包里的 `c3/` 布局）

| 包里的位置 | 落地位置 |
| --- | --- |
| 原始公开数据 | `/projects/EEG-foundation-model/auditory_public/{fau_tud,dtu_snhl,federici_ci_children}/`（组内可读；不放进只读的 `auditory/`） |
| `c3/features/` | `/projects/EEG-foundation-model/auditory_public/derived/c3_features/`（只由公开刺激导出，带 manifest） |
| `c3/receipts/`、`c3/private/`、`c3/registry/` | `private/auditory_c3/{receipts,private,registry}/`（0700） |
| `c3/synthetic/` | `private/auditory_c3/p1_synthetic_00N/` |
| `c3/public/<source>/` | `private/auditory_c3/public/<source>/`（逐人量）；聚合结果放 `results/auditory_c3/` |
| `c3/reports/` | `docs/auditory_c3/` |
| 代码与配置 | `auditory_c3/`、`tests/auditory_c3/`、`configs/auditory_c3_v1.yaml`、`slurm/auditory_c3_*.sbatch` |
| 环境 | 从 eeg2025 克隆出新环境 `auditory_c3`，再补 statsmodels 和 vendored gcmi。不改 eeg2025，避免影响已冻结轮次的复现 |

---

## 4. 执行顺序（P0 → G1 细化）

**P0（数据与特征）**
1. 下载（已完成）：Slurm 1020904 / 1020905 / 1020906，`slurm/auditory_c3_download.sbatch`，按发布方的 md5/sha256 校验后才落盘。
2. 每个来源写一份回执（02 的 schema）。FAU/TUD 的 schema 审计要列出：被试、试次、刺激码、`taken_out_indices`、各组 `eeg`/`eeg_ica` 是否存在、HDF5 属性里有没有行为字段，并用辅助通道与 wav 做互相关，得到逐试次延迟分布。
3. Federici：从 .mat 和代码里核对采样率与滤波带宽（D2），把行为表 ID 连接到 EEG 文件。
4. DTU：BIDS 审计，核对 `participants.tsv` 的字段与单位。
5. 刺激特征（一个 GPU 作业，A100/L40S，不用 P100）：所有 wav（注意流和干扰流）过 Whisper-large-v3 和 XLS-R 全部层；PCA 只在刺激上拟合，k = 3/5/8；重采样到 EEG 采样率；生成转写和词时间戳，计算德语 GPT-2 惊讶度；同时算包络、包络起始、梅尔谱基线。写 manifest（模型 revision、层号、k、采样率、sha）。
6. G0：每个来源一份回执；三联集状态 ≥ `STIMULUS_FEATURES_CACHED`；D2 核对完成。

**P1（估计器验证与冻结）**
1. vendored gcmi 与参考实现在 S1–S9 上差异 < 1e-6 比特。
2. S9 写进 08 和 `tests/`，形成修正记录 `docs/auditory_c3/MEASUREMENT_AMENDMENT_001.md`。
3. 移植 I_ccs 并核对；不通过就标 PID 层 `TECHNICALLY_UNEVALUABLE`。
4. 语言层选择：第一次接触真实 EEG，只用 TH 的一半，只做选层。前提是 §2.1 已经定下来，因为选层判据本身就是 I(T;L_ℓ|Ac)。
5. 冻结：`measurement_spec.json` 置 `frozen: true`，写修正记录，记 SHA。之后报告 G1 检查表，**等你确认后再进入 P2**。

**P2**：04 §4.1 的三项阳性对照。H1a 直接用 Jehn 的公开代码。

---

## 5. 需要你决定或动手的事

1. **发信**：三封邮件的定稿在 `docs/auditory_c3/EMAIL_REQUESTS_v1.md`（D1 发 DTU，D3 发 Jehn，另有一封可选的发 Federici/Bottari）。这些只能由你来发。
2. **冻结前修正**：§2.1 改为整段滞后窗条件化或预测中介作主路径（强烈建议）；§2.4 主协变量改用日历月龄；§2.6 选层被试的处理；§6 的逐试次对齐规则；§8 的额中央 ROI 定义。五项分别同意或否决。
3. 是否同意新建 conda 环境 `auditory_c3`。目前所有作业仍在 eeg2025 里运行，没有安装任何包；gcmi 以单文件形式放进了仓库。

2026-10-04 用户指示"现在能开始的就开始做；预处理数据存到 /projects/EEG-foundation-model；GPU 任务先用 runfill 提交"。在上面这些决定确定之前，执行范围是不依赖任何决定的 P0 与 P1 工作，见 §8。不计算任何 EEG 科学量，不接触私有分组结果。

## 6. P0 审计结果（001，2026-10-04）

下载：三个来源全部完成，每个文件都按发布方给的 md5/sha256 核对通过后才落盘。HA、CI、TH、DTU 按 md5，Federici 按逐文件 sha256。回执在 `private/auditory_c3/receipts/DATA_RECEIPT_<source>_001.json`，使用 02 的 schema。结构审计由 Slurm 1020994/1020995/1020996 运行，代码 `auditory_c3/p0_audit.py`。只读取了结构、属性和 FAU/TUD 的两条音频辅助通道，没有计算任何 EEG 量。

| 项 | 结果 | 对方案的影响 |
| --- | --- | --- |
| `eeg_ica` | **三个文件都只有 `eeg` 分支**，HA 也没有，HA 说明文件里的描述与实际文件不符 | §2.3 不再需要决定：三组只能从原始 `eeg` 出发，用同一套伪迹流程 |
| 行为数据 | HDF5 里只有试次属性 `stimulus` 和 `taken_out_indices`，没有任何行为字段 | H7a/H7b 确认为 `FUNCTION_ENDPOINT_UNAVAILABLE`，D3 是唯一途径 |
| 人数 | HA 29、CI 24、**TH 28**（论文写的是 29）；每人 20 个试次，每个 102–198 s；总时长 HA 21.5 h、CI 17.8 h、TH 20.7 h | 回执同时记录文件人数和论文人数；不合并 n；H1a 的复现按 28 名 TH 进行，并写明差异 |
| CI 去除电极 | 每人去除 0/1/2/3/4 个电极的人数分别为 1/7/13/2/1 | ROI 插值规则冻结时要覆盖去除 4 个电极的情况 |
| 音频–EEG 对齐 | 用辅助通道包络与 HDF5 包络做互相关，峰值滞后中位数为 0 ms。滞后在 ±5 ms 以内的试次：HA 575/580、CI 454/480、TH 518/560。超出的试次中，r ≥ 0.3 的多数偏移 6–23 ms，集中在少数被试（CI 一人 14 个试次，TH 一人 16 个试次）；其余是 r 很低、辅助通道本身失败的试次 | 窗 1 是 [0, 80) ms，10–20 ms 的偏移会影响早滞后。**需要在 G1 前冻结逐试次对齐规则**，建议：r ≥ 0.3 且 \|lag\| > 5 ms 的试次按辅助通道重新对齐；r < 0.3 的保留发布时的对齐并标记；两种版本都报 |
| 刺激 | 20 个刺激码，各有一个双声道 48 kHz wav，合计 2665 s；HDF5 里另有注意流和干扰流的 wav、包络和起始包络 | 特征提取的音频总量约 2 × 44 分钟，GPU 时间很小 |
| DTU | 44 人（HI 22 / NH 22），BDF 512 Hz，64 导；目标起始 2102 个（单说话人 701、双说话人 1401）；SRT 44/44 不缺失；**HI 组的刺激按 CamEQ（剑桥公式，依个人听力图）线性放大**，包络同时提供放大版和未放大版（`woa`） | 回答了 02 中"放大是否按个人听力图"的问题：是。没有原始音频，D1 仍然需要 |
| Federici | 100 Hz（作者编码代码中 Fs = 100）；每人 12 段 × 50 s × 32 导；HC 37、CI 33、HC-v 16（全部是 HC 的被试）、幻影头 9 条（3 个 ID）；行为表包含理解准确率、年龄、剥夺期、植入经验；**CI 的 EEG 有 33 人，变量表只有 32 行** | 100 Hz 的采样足以支持早滞后。预处理用的滤波带宽不在发布代码中，D2 还需要从论文或数据频谱确认。H7d 基本可以连接，缺的那一人按 ID 核对 |

## 7. 资源

- 存储：原始数据约 100 GB；DTU 的 tar 在解包核对后再决定是否保留（35 GB）。项目盘还剩 3.8 TB。
- GPU：特征提取预计不到 1 GPU 小时，准确数字等刺激解压后按音频总时长给出。
- CPU：GCMI 本身很便宜。copnorm 是按边缘分布排秩，对循环移位不变，所以代理只需要重算协方差。P3 的总量按 07 §7.3 在 P0 之后按真实任务数给出。

## 8. P0/P1 进度 002（2026-10-04 晚）

**已完成**

| 项 | 结果 | 位置 |
| --- | --- | --- |
| 邮件 | 三封定稿；收件人地址取自数据页或论文的通讯作者 | `docs/auditory_c3/EMAIL_REQUESTS_v1.md` |
| 刺激副本一致性 | HA、CI、TH 三个文件中的 120 个刺激数组 sha256 完全相同，特征只从 HA 文件算一次 | `derived/c3_features_v1/fau_tud/stimulus_copy_check.json`（Slurm 1021233） |
| 通道顺序 | 示例 vhdr 给出 31 导顺序：Fp1…Fp2，其中 **IO2 是眼电**；**在线参考是 Cz，数据里没有 Cz，也没有 FCz 和 FC2**。HDF5 行顺序与 vhdr 顺序一致：HA、TH 都是 31/31 行对上；CI 是 23/31，因为 CI 伪迹使各通道高度相关，最大相关落到了其他通道上。HDF5 与示例原始文件不是逐位相同（差分相关最低 0.55，幅值比 0.91），推测作者对齐时做过处理 | `derived/c3_preproc_v1/_logs/fau_tud_chanmap.json`（Slurm 1021255） |
| CI 被移除电极 | `taken_out_indices` 按 0 起算。依据：这些行没有平坦信号，但高频方差中位数是其他行的 1.39 倍（按 1 起算则为 0.99 倍），符合电极断开后只记录噪声；按 0 起算时最常见的是 P7/P8，靠近植入体。预处理把这些行置为 NaN，不插值 | `private/auditory_c3/logs/c3_tio-1021279.log` |
| Federici 带宽（D2） | 所有人类被试合并（不分组）的频谱：−3 dB 带宽 1.76–6.84 Hz，−20 dB 点在 0.39 Hz 和 9.77 Hz，12 Hz 处 −50 dB。论文写的是先 0.1–40 Hz，再 2–8 Hz、100 Hz，与此一致。**D2 结论：带宽与成人主分析的 1–8 Hz 基本相同，早滞后窗可以解释**；但 Federici 的 CI 组 P1 本身晚约 60 ms，[0,150) 与 [150,600] 的切分会跨过这个峰，冻结时要写明 | `derived/c3_preproc_v1/_logs/federici.json`（Slurm 1021256） |
| **H7d 不能按登记形式做** | Federici 没有故事音频，算不出 I(T;L\|Ac)，H7d 只能退到包络层；理解题是每个故事 2 道二选一，信息量很少 | 已写进邮件 3 |
| 生产估计器 | Ince gcmi 固定在 f14aae8（2020 年最后一个单文件版本）；唯一改动是 numpy 2 删除的 `np.float`/`np.int` 别名，补丁单独存档；与包内参考实现 **28/28 项差异都小于 1e-6 比特** | `auditory_c3/vendor/`、`tests/auditory_c3/test_gcmi_agreement.py`（Slurm 1021280） |
| S9 | 写成 pytest | `tests/auditory_c3/test_s9_multilag_conditioning.py` |

**特征与预处理（已完成）**

- 刺激特征都在 `derived/c3_features_v1/fau_tud/`，每个文件旁有一个 `.done.json`，记录模型 revision 和 sha256：
  - Whisper-large-v3：33 层隐表示（嵌入层加 32 层，1280 维，50 Hz），另有 128 维 log-mel。用时 647 s。
  - XLS-R-300m：25 层（1024 维）。用时 205 s。
  - 德语转写带词时间戳：32 条非静音流，0 条失败，共 10379 个词。
  - 德语 GPT-2 词惊讶度：中位数 6.1 比特。
  - 两个模型的逐层 PCA（k = 8，前 3 和前 5 个成分是它的嵌套子集）：只在刺激帧上拟合，按 wav 哈希去重，结果重采样到 128 Hz。**Whisper 浅层前 5 个成分只解释约 16% 的方差**（第 1–3 层为 0.158 / 0.159 / 0.173），冻结 Ac 的定义时要写明。
  - 单说话人试次的干扰流是静音，只标记、不编码。
- 预处理阶段 A（`derived/c3_preproc_v1/`）：
  - FAU/TUD：81 人、1620 个试次。另存了 49 个重新对齐的试次副本（HA 5、CI 14、TH 30）。
  - DTU：45 个文件（sub-024 有两段记录），2112 个试次；每个试次的目标和掩蔽包络都已按 128 Hz 网格对齐，没有缺失。**更正**：001 回执写的 2102 少数了 sub-024 第二段记录里的 10 个试次，已在 002 回执中更正。DTU 共有 72 个通道，即 64 导头皮电极加 EXG1–8；其中 19 人的 EXG3–8 是耳内电极。参考电极的选择留到 G1。
  - Federici：仅转换为统一格式。
- I_ccs 移植（`auditory_c3/pid_ccs.py`）的 12 项测试全部通过：
  - 一维情形与上游 Python 版用同一批样本对照，差异小于 1e-9。
  - 多维情形下，源内可逆线性变换和两源互换都不改变结果，差异小于 1e-8。
  - 格点恒等式成立；两个源近乎相同时，冗余等于单源互信息。
  - **仍缺与 MATLAB 原版在多维情形的直接对照**（需要 Octave）。这一步是否必须做，在 G1 时决定。
- 回执 002：`private/auditory_c3/receipts/DATA_RECEIPT_*_002.json`，001 保留。FAU/TUD 三组状态升为 `STIMULUS_FEATURES_CACHED`。
- **G0 已满足**：每个来源都有回执，三组 FAU/TUD 已达到 `STIMULUS_FEATURES_CACHED`，D2 已核对。D1 不阻塞 G0。

**本轮作业与故障记录**

| 作业 | 内容 | 结果 |
| --- | --- | --- |
| 1021233 | 三组刺激副本一致性 | 通过（120/120 相同） |
| 1021254 | GPU 特征：whisper / xlsr / asr / gpt2 | 前三个单元完成；**gpt2 单元失败**：CUDA device-side assert。原因是这个德语 GPT-2 的词表里没有 `<|endoftext|>`，transformers 把它追加在 id 50265，超出了嵌入表；config 里的 bos = 50256 其实是普通子词 "riegel"。改用词表自身的 `<s>`（id 0）作为起始符，并在 CPU 端加了 id 范围断言 |
| 1021335 | gpt2 重跑 | 完成，用时 18 s |
| 1021255–58、1021281–82 | 预处理：chanmap、Federici、HA、CI、TH、DTU | 全部完成 |
| 1021272 | gcmi 对齐测试 | **失败**：28 项都在运行时报错，没有比较到任何数值。原因是 2020 版 gcmi 用了 numpy 2 已删除的 `np.float`；只替换了这两个别名，补丁单独存档 |
| 1021280 | 修复后重跑 | 28/28 通过 |
| 1021277 | 被移除电极的索引约定 | **没跑起来**：脚本放在登录节点的 /tmp，计算节点看不到 |
| 1021279 | 修复后重跑 | 完成，结论是 0 起算 |
| 1021283、1021306 | C3 测试（gcmi、S9、I_ccs） | 29 项与 12 项全部通过 |
| 1021294、1021305 | PCA（Whisper、XLS-R） | 完成 |
| 1021334 | GPT-2 分词器诊断（CPU） | 复现了越界：bos id 50265，嵌入表 50265 行 |

**新增的冻结前事项（§5 第 2 条）**

- **额中央 ROI**：03 §3.7 写的是"Fz/FCz/Cz 及邻近"。FAU/TUD 没有 FCz 和 Cz（Cz 是参考），也没有 FC2。建议：改成平均参考，把 Cz 作为全零通道重建回来，ROI 定为 Fz、FC1、FC6、C3、C4、Cz（重建）、CP1、CP2；或者在冻结时另行指定。IO2 只用于伪迹处理，不进任何 ROI。
- **I_ccs**：Ince 仓库里的 `pid_mvn.py` 把 MATLAB 的块索引直接写成了 numpy 花式索引（`Cfull[sidx, sidx]`）。源变量是一维时结果正确，是多维时只取到对角元，所以不能直接用于 5 维源。需要自行移植（用 `np.ix_`），并在一维情形与 `pid_mvn.py` 对照、在多维情形与 MATLAB 参考（需要 Octave）对照。核对不过就按包的规定，PID 层标为 `TECHNICALLY_UNEVALUABLE`。
