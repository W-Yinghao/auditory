# 仓库接口、已有资产与最小新增层

## 审计基准与适用范围

- 仓库：`W-Yinghao/auditory`。
- 本轮通过 `git ls-remote origin HEAD` 重新核验的远端 HEAD：`3da8cf5758214c0cf87a1f1c8d67fb84b574000e`。
- 提交时间：2026-10-20 20:03:20 +02:00；提交说明：`Publish results of the two bounded ALN3.5 lanes and lane records since publish_033`。
- 只读 checkout：`/workspace/scratch/8dbb7d920043/auditory_review_20261020`；工作树干净，与远端相同。本轮没有新的提交差异。
- 本文未访问服务器、Slurm、私有原始数据或生产权重；没有启动、取消、重启任务或删除产物。下列完成度属于 GitHub 已发布快照，不是接包时 live 状态。
- 已读根 `AGENTS.md`，未发现其他适用嵌套指令。它引用的 `CLAUDE_HANDOFF.md` / `CODEX_HANDOFF.md` 未包含于当前公开 checkout；server 接包时应自行读取。

本轮研究对象恢复为声音内容、时间组织、跨听者/范式迁移与个人适配。新包应承接现成研究接口；旧 ALN4 四臂儿童 AUC 计划不再自动代表全部研究设计。现有有效与弱/反向结果均保留。用户的新研究安排优先于历史包的研究重心，但不改变已有运行身份。

## 1. 已有训练与源声音接口

以下代码路径均相对于上述固定提交。

| 功能 | 现成入口 | 输入、关键参数与输出 | 复用边界 / 最小新增 |
|---|---|---|---|
| EEG backbone | `auditory_alignment_v2/foundation_adapter.py::Backbone(arch,dataset,adaptation,fs_native,init_state=None)` | CB/REVE；输出 `[B,C,P,E]`；初始化严格加载在 LoRA 前；`pretrained_full` / `random_full` 等全部更新 | MindMix 尚无现成 adapter，须独立 exact-load gate；不得静默部分加载 |
| 查询锚定 full 微调 | `auditory_alignment_v3/fm_aligned32.py::fit_aligned32`；`fm_aligned.py::AlignedBatcher/AlignedFM` | `d=32, grid=3, n_seg=32`；相对 query `[-400,+600) ms`；checkpoint 键 `model`；有参数更新账本 | 真 full 须显式选 `full_onestep_v1` / `warmup_then_all_v1`；默认 `aln3` 是旧渐进解冻。新初始化与新选择规则需 wrapper |
| 现成 source 训练 | `auditory_alignment_v3/aln34/cb_auditory.py::eligible/Stream.draw/run_donor` | SparrKULee 64 通道、64 Hz；旧窗 `26 before + 38 after`；至多 8 内容族 × 每族 8 anchors；输出 keys / 合法 wrong permutation；保存 `backbone`, `head`, step, stream receipt | 训练目标写死 NCE；多视图 CS、时间响应方法需新 wrapper，非一个已有 loss CLI |
| 音频固定坐标 | `auditory_alignment_v3/prior33/views.py::open_with_rich/DonorBank.rich_targets`；`prior33/model.py::fixed_heads` | env / ss / sc；必须 `rich=True`，逐批核对 present；固定标准化与投影 | rich 不是 MFCC；不能把部分数据集的 rich 可用性当作全覆盖 |
| 传统核 CS / NCE | `auditory_alignment/losses_reference.py::cs_qmi`；`auditory_alignment_v3/prior33/losses.py::nce_single_view/calibrate_sigma` | Gaussian KDE-CS；NCE 有内容族/相邻时刻负例限制；source calibration 冻结带宽 | 新 Stage2 组合目标需适配；NCE mask 不能直接解释为 CS Gram mask；不使用 VCS-QMI |
| 私有 FM 训练 | `auditory_alignment_v3/local_train.py::fit_private_fm(row,kids,dev,ckpt_prefix,log,lr_backbone,lr_head,epochs,adaptation,init_state=None,d=32)` | 20 通道、250 Hz；`EpochEncoder` 输出 `[B,32]`；checkpoint `enc` + `protos` | 现成目标是 label NCE/CS，非 CE；如需要 CE，只加 head 与训练包装 |

现成 `auditory_alignment_v2/fm_readout.py::SpatialPatchHead` 可保留通道轴与 patch 轴：常用 `K=8,e=32,d=32`，signed spatial projection，输出 `[B,P,32]`。不能将 channel mean 当作该头的等价实现。

旧 FM / CBAUD 下游 recipe 的 checkpoint 选择使用 gain 型准则。若新包规定 source-side true query risk，必须在新 wrapper 实际替换选模对象并记录选择账本，不可只改文档。

### 源 pool 与 manifest

| 资产 | 路径 | SHA256 |
|---|---|---|
| 公开 core manifest | `results/auditory_alignment_v3/prior33/manifests/manifest.json` | `3ffa6e6d013283368d1f7eb09bf6c9e7573c0ae4009304cf3bc1d9836c197046` |
| rich supplement | `results/auditory_alignment_v3/prior33/manifests/manifest_rich.json` | `c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd` |
| server 完整 manifest | `private/auditory_alignment_v3/aln34/prior33/manifest.json` | `b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426` |

`cb_auditory.eligible` 排除下游重叠 `[4,5,19]` 后，SparrKULee fit 为 81,732 segments / 64 people / 48 content families；development 6,332 / 10 / 9；calibration 6,162 / 6 / 6。三部分的人与内容族分离。此处复用此前同 SHA 审计，没有在本机打开 server 私有 manifest。

缓存根为 `/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1`。rich 由 Whisper 128 维 log-mel 经 source-fit PCA 构成谱形与变化特征，ss 窗 32 维、sc 窗 8 维，再进入固定 head。SparrKULee rich 覆盖完整；DTU/FAU/Federici 不可默认同等覆盖。

源 EEG 为 64 Hz 带限缓存，原 recipe 约 1–20 Hz。FM adapter 内上采样至 200 Hz 不恢复原始高频；沿用该共同 recipe 无须重做全部 raw 预处理，但须如实记录。

## 2. 已有科学读出、迁移与个人适配

| 研究对象 | 可复用函数 | 输入 / 输出与新增边界 |
|---|---|---|
| 声音内容与时间组织 | `aln34/content_time.py::features/valid_offsets/target_views/analyse` | env/onset/spec/flux/Ac/Lz，直接与条件残差；每人 r、MSE、mismatch；5×5 时间矩阵；source-fit/ES ridge。新 checkpoint 需导出同 schema，不改旧冻结 `rebuild` |
| 新表示的科学数组 | `aln34/content_time.py::extract` 的 schema | `role/person/segment/source_segment_e0/anchor_offsets`、`target_*`、`model_<center>`、实际时窗和数组 hash。旧模型使用重叠 1 秒窗，不是新增 400 ms windowbank |
| 儿童当前声音 / 历史 / 时间迁移 | `aln34/private_current_time.py::fit_interface/history_metrics`；`private_current_time_v2.py::Probe`；`calibration_retry.py::AffineLogitCalibrator` | 每儿童/window 表示 → AUC、NLL bits、Brier、history gain、跨窗读出。必须用 v2 校准修正与实际访问标记；旧 local/E_PUBLIC_TRANSFER 的全零 pre 仍无效 |
| 注意范式迁移 | `aln34/attention_transfer.py::segments/scores/stage/evaluate_windows/select_integrator` | 冻结单说话者模型 → attended/ignored margins → 5 秒片段累计；mean 与 antisymmetric integrator；每人准确率/NLL；来源与 inner 人排除完整保存 |
| 个人支持 | `aln35/support_contract.py::private_split/dtu_split/select_support/access_budget` | 固定共同 query、完整 epoch/context guard、支持数与 metadata/label 访问账本。比旧 `private_current_time.blocks` 的划分更适合新接入 |
| 个人更新与风险 | `aln35/support_runtime.py::fit_public/fit_private_spatial/fit_private_output/public_metrics/private_metrics` | 输入 rank-4 空间或输出 rank-4 更新；true risk、mismatch gain、概率/表示变化、实际更新与梯度。public 原目标 NCE；private 按所选源 objective |
| 适配相关源训练 | `aln35/episode_pressure.py`、`episode_pressure_s3407.py`；`aln34/episode_training.py::continue_source` | 复用 matched ordinary/episode 预算与正确 lineage；旧 3-step 结果不代表充分 pressure。适配后模型优势不能自动解释为适配增量更大 |
| 人群、年龄与时长 | `aln34/science_aggregate_v2.py::public_rows/private_rows/joint_ols/summaries`；`aln35/science_export.py::public_records/main_endpoints/bind_families` | 同人 session/content/seed 先合并；直接组差；年龄/HA 时长条件关联。新增只需 endpoint/arm spec 和 exporter mapping；旧 13 families 不自动覆盖新设计 |

上表中的短路径均以 `auditory_alignment_v3/` 为前缀。现有公共时间解码使用 `[c−400,c+600) ms` 完整访问；`c=600` 不是 600 ms 单点神经潜伏期。注意任务累计时间也不是行为反应时。年龄和设备时长现成接口是横断面条件关联，不是已完成的年龄预测模型或纵向疗效。

### 私有 loader 范围

`auditory_alignment/data.py::load_private()` 连接 `auditory_c3/c3dl/hc.py`。64 儿童（55 HA / 9 NH，无 CI），五折儿童级划分，13/13/13/13/12 人；不是 64 次 LOOCV。原生 epoch 为 20×200，250 Hz，`[-200,+600) ms`。当前 standard/deviant、history bin、block、年龄和时长已有；没有连续音频 waveform/声谱目标。默认 source 儿童内 ES 为末尾约 20% 物理 blocks。

原预处理使用 whole-record 离线滤波和标准化；支持/query guard 控制直接样本访问重叠，不等于整个预处理因果隔离。个体级已批准字段可以沿用，原始 EEG、人名、identity map 和新原始事件行不得复制进包。

## 3. 新 windowbank 的原生整数访问审计

待采用的名义窗为 `[-200,200)`、`[0,400)`、`[200,600)` ms。以下是**原生采样时刻属于半开区间**的明确约定：若 query 锚点在整数样本 q，取 `q + [ceil(a·fs/1000), ceil(b·fs/1000))`。不能暗用 round 后仍宣称相同访问。

| 名义窗 ms | source 64 Hz 相对 q 的 Python slice | 样本数 | source 实际首 / 末 sample ms | private 250 Hz 原 epoch slice | 样本数 | private 实际首 / 末 sample ms |
|---|---|---:|---|---|---:|---|
| `[-200,200)` | `[-12:13]` | 25 | -187.5 / 187.5 | `[0:100]` | 100 | -200 / 196 |
| `[0,400)` | `[0:26]` | 26 | 0 / 390.625 | `[50:150]` | 100 | 0 / 396 |
| `[200,600)` | `[13:39]` | 26 | 203.125 / 593.75 | `[100:200]` | 100 | 200 / 596 |

64 Hz 三窗的实际索引 stop 分别为 13、26、39；它们对应的下一个格点为 203.125、406.25、609.375 ms，这些 stop 格点不被取入。25/26/26 是离散格点数，不可为凑相同长度偷偷插值或加一个真实 sample。私有三窗各 100 原生样本，恰为 400 ms。

**旧 CBAUD 64 点 x 不能无损提供第三个新窗。** `cb_auditory.Stream.draw` 拼接 `q+[-26:38]`，最后一个 sample 是 q+37（578.125 ms）；新第三窗需要 q+38（593.75 ms）。可在新 wrapper 从原生缓存读取完整新 bank `q+[-12:39]`（51 点）或更宽的显式 bank；不能把缺失点默认为零却标记为真实 600 ms 访问。

`DonorBank` 的 segments 模式缓存 `[s,s+357)`，旧 `gather` 每次固定 38 点。新完整 bank 的必要条件为 `off−12>=0` 且 `off+39<=357`，即 `12<=off<=318`；同时仍需原始 piece guard 检查。保留旧 source sampler 的 `off>=26` 时，只须从原 230 个候选 tick 中排除末尾 `off=319`，得到 229 个可完整访问的候选。原 tick 公式为 `(64*k+25)//50, k=0..249`。这允许沿用既有 segment 的尾部 halo，不等于全部样本都在名义 `[s,s+320)` 的 5 秒段内；若另要求严格 5 秒段内，则还需 `off<=281`，会改变候选集合，必须另行明示。

最小实现可增加接受 `[lo,hi)` 的原生 gather，或在合法已载 span 内组合读取后严格裁剪；保留每窗 sample index、valid-mask、实际首末时刻与父 segment 身份。不可编辑旧 `DonorBank` 的冻结行为来伪装成旧 unit。

先在原生输入上 crop/mask，再进入 backbone 必需的重采样与 padding；若先对完整 epoch 作全局 FFT 重采样再遮罩，窗外值可混入窗内，不能声称只有上述原生窗口访问。CB/REVE 的 200 Hz 适配、最短 200 点 padding 必须单独记录；padding 是结构输入，不是额外 EEG。这里未运行模型或重采样，仅校验整数访问几何。

## 4. 真实已有 CLI 与待实现模块

下列现有 CLI 仅服务**旧冻结计划与旧 ID**，需要服务器 Slurm、生产数据、checkpoint 和哈希一致性；列出供接口定位，不是本包的启动指令：

```text
python -m auditory_alignment_v3.aln34.content_time --unit <registered-old-ID>
python -m auditory_alignment_v3.aln34.private_current_time_v2 --unit <registered-old-ID>
python -m auditory_alignment_v3.aln34.attention_transfer --unit <registered-old-ID>
python -m auditory_alignment_v3.aln35.support_coverage --unit <registered-old-ID>
python -m auditory_alignment_v3.aln35.episode_pressure --unit <registered-old-ID>
python -m auditory_alignment_v3.aln34.science_aggregate_v2 --bootstrap 4000
python -m auditory_alignment_v3.aln35.science_run
```

旧包 `AUDITORY_ALN4_STAGE2_CS_SERVER_PACKAGE_v4_0_20261021` 中，`aln4/assets.py/source.py/objectives.py/train_source.py/train_private.py/plan.py/report.py` 是 server **待新增**的建议模块，不是仓库现成代码。没有生产 `python -m aln4.train_source` 可直接运行。

旧包真实可运行工具为 `scripts/verify_package.py`、`scripts/materialize_plan.py`、`reference/verify_cs_math.py` 和 `scripts/paired_summary.py`。前二者检查/展开本地包，不提交生产任务；CS 数学工具本机旧报告仅 NumPy 检查完成，Torch/GPU 尚需 server 核验；`paired_summary.py` 硬编码四臂+64 儿童完整 roster，不能冒作新多任务主汇总。

## 5. GitHub 已发布完成度与旧任务

完成：TRUE_FULL 800/800；公共先验 1,154 新单元 + 30 历史参照；content/time 180/180；private current/time v2 130/130（26 兼容 v1 复用）；prior science 300/300；ALN3.5 APwrong、融合归因、attention order、bridge factor、CB 状态、history、科学/组差与 pre 修正；support/episode/matched-update/true-risk 汇总 1050758；最新两条有界线 CBAUD_PEOPLE 20/20、episode seed3407 10/10。

2026-10-20 19:55 的已发布快照仍剩 DTU budget 39/150、DTU curve 10/440、breadth budget 9/75、breadth curve 74/300。README 中段的旧“新线运行中”已被顶部最新发布覆盖；四个尾巴的今日状态仍需 server live 核查。没有自动取消旧任务、释放 holds 或删除 A3b/A3c/A3d/ALN2 D_FM 的授权执行动作。新旧 GPU running+pending 合计不超过 10；排除 P100，不使用 scontrol，不修改在跑源码。

## 6. 本轮最小新增层

1. Stage2 新目标与时间表示 wrapper：复用 source pool、backbone、固定声音坐标、传统 CS/NCE；新增明确的响应 windowbank/mixture 与 source-side checkpoint 选择。
2. 新 checkpoint → 统一 Bundle / 科学数组的导出 adapter：一次接入后可复用内容、时间迁移、注意与个人适配读出；保留实际访问、query、person、condition 与 hash。
3. 新命名空间 plan、endpoint/arm spec 和汇总 mapping：旧任务身份不变，不用儿童四臂 AUC 硬约束公共研究读出。
4. 仅在新设计确实要求时补 CE 或其他目标 head；已有当前声音、历史、时间、人群/发育分析无需重建。

## 7. 证据与历史读取边界

同目录 `evidence_ledger.json` 对 8 份公开 Markdown 保存固定 repo SHA、路径、字节 SHA256、阅读范围与不超过 10 项有边界的 claim。它不含 raw EEG、私有事件行或人名，也不把实验数当独立样本。

旧 D2/GX 的原报告本轮仅核对 git tree 条目；未取得或未完整读取其 blob，不执行网络 fetch。不得写“D2/GX 原报告已全部读完”，不得凭路径存在确认其结果或接口可直接运行。ALN3 公开汇总中若引用旧 GX，只能标为该汇总的二级引用；旧项目本身的完整复核仍未完成。
