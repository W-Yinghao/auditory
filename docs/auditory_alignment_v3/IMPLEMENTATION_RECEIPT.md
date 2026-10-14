# ALN3 接入回执（2026-10-10 起，持续更新）

- 包：`AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010.zip`，解压为同名目录，52/52 文件 sha256 与 SHA256SUMS 一致。基准 `d5b2315`；发布检出 HEAD `d5b2315b465519fa2017ff3180fd34a090787164`（= 基准）。工作区在基准之后的改动：ALN2 第 1–3 项的分析、更正与登记（见 `docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md` §13–§15）。
- 规则：`AGENTS_APPEND.md` 已置于工作区 `AGENTS.md` 最前（历史保留，原文件备份 `private/AGENTS_before_ALN3.md`）。
- 用户授权（2026-10-10）：工程检查通过后直接启动 ALN3；旧第 2 项基础模型行降为最低优先（不占 ALN3 需要的 GPU）；3a 运行；3b/3c 并入 B（`docs/auditory_alignment_v2/ITEM3_ADDENDUM_01.md`）；Federici 身份更正（`ADDENDUM_01_FEDERICI_IDENTITY.md`）。

## 1. 代码与版本

- `auditory_alignment_v3/`：`core.py`（绑定、密集网格、每族代码哈希）、`local_train.py`（由 `private/auditory_alignment_v3/gen_local_train.py` 从 ALN2 逐字复制并做登记的替换生成）、`calib.py`（私有校准变体）、`fm_dense.py`（B 密集读出）、`run_local.py`、`run_private.py`、`run_dense.py`、`run.py`（分派，不计入哈希）、`reaggregate_federici.py`、`recalibrate_private.py`；`aln3_reference/` 为包内参考代码的逐字节副本。
- 每个族组有独立的代码哈希（族代码 + ALN2 依赖），以后绑定新族不会改变已运行单元的版本。
- ALN2 文件未改动（第 2 项的小编码器仍在运行）。

## 2. 已绑定的合同与默认值（工程选择，非门槛）

- **dense20ms_v1**：网格 = round(20 ms × fs) 个样本（FAU/DTU 128 Hz：3 = 23.4 ms；Federici 100 Hz：2 = 20 ms）。训练锚点每 5 s 片段 8 个，相位与间距都在网格上（间距向下取到网格的整数倍：FAU 78、Federici 62 个样本）。目标 = ALN2 的 8 帧窗口（local / Ac / Lz / envelope），训练侧标准化，固定半正交投影到 d（fixed_latent；默认 32，A_DIMENSION 16/64）。Federici 包络窗口只有 8 维，投影到 32 维是等距嵌入，有效秩仍为 8。评价在同一网格上，候选池、读出、风险与 ALN2 相同。
- **小编码器**：200 个 epoch（ALN2 已验证：最佳 epoch 位于 112–152/200；包的起点值 100），AdamW 1e-3（ALN2 值）。
- **私有**：ALN2 的试次、外折与窗口；表示维数 32；GX 原生网络不变。E_GENERIC 沿用 ALN2 基础模型学习率配方与训练轮数（CBraMod 100、REVE 50），整 epoch 补零输入（padded_private_epoch_no_extra_EEG）。每个私有单元同时报告校准变体：温度、正斜率仿射、类别核（CS），以及原有探针头；校准只在训练儿童的早停块上拟合。
- **B_DENSE**：主干读取从片段起点到片段结束后 0.6 s 的 EEG（= 局部模型的最大滞后访问），补零到整 patch（CBraMod 1200 样本 = 6 个 patch；REVE 6 个 patch），超出部分的 patch 掩蔽。query 只含相对时间。读出为包内参考 `DenseQueryReadout` / `ChannelPhaseLinearReadout`。训练配方按第 3 项增补 01：读出头预热 5 轮 → 每 5 轮自顶向下多解冻一组块 → 逐层学习率衰减 0.75 → 每轮在早停内容上验证。学习率事先固定（随机初始化 3e-4，PEFT 1e-4，部分/全量 1e-5，读出头 1e-3；依据 ALN2 微调严重过拟合、所选学习率多在候选上限）；学习率面板与 ALN2 一步配方对照在代表性配置上另行登记运行（见 §4）。
- **信息访问**：A 族 local_only；B 族 foundation_context；私有按各族声明。

## 3. 工程检查（不设任何表现门槛）

- 单元测试：ALN3 绑定与包内参考测试共 53 项通过（`tests/auditory_alignment_v3/`，包 `tests/`）。
- GPU 探针 1033623 **发现一个错误**：训练锚点间距（640/8 = 80 个样本）不是 FAU 网格（3）的整数倍，8 个锚点中只有第一个在网格上。已改为把间距向下取到网格的整数倍，重新生成 `local_train.py`。
- GPU 探针 1033626 全部通过（11 个单元，每个 2–3 个 epoch，输出在 `private/auditory_alignment_v3/probe_out`，不计入结果）：锚点与评价网格在密集网格上；d 与声明一致；私有校准变体齐全，仿射斜率为正，各方法 AUC 与原始分数一致；B 先预热再逐步解冻，patch 时间与掩蔽正确。

## 4. 运行（见各次状态更新）

- 2026-10-10 20:08 启动：`queue_v3_small`（A_LOCAL 1000、A_TARGETS 320、A_DIMENSION 100、E_LOCAL 140、E_GX 30；共享 GPU）与 `queue_v3_fm`（E_GENERIC 180、B_DENSE 1600；一卡一个）。两个队列内都是广覆盖 seed 在前、面板在后。
- 尚未绑定：A_LOCAL_FACTORS、B_LAYER_PROBE、C_COMPLEMENT / C_CAPACITY_CONTROL（依赖同外折局部基础单元）、D 族、E_PUBLIC_TRANSFER / E_COMPLEMENT / E_DISTILL、F_SCIENCE，以及 B 的学习率面板与原配方对照。按依赖逐步接入。

## 6. ALN3.1 增补（2026-10-11）

- 包：`AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011.zip`（sha256 `169b1c40…`），解压为同名目录，73/73 文件与 SHA256SUMS 一致；`plans/units.jsonl` 与 v3.0 逐字节相同（不重新生成）。`AGENTS_APPEND.md` 置于 `AGENTS.md` 最前（备份 `private/AGENTS_before_ALN3_1.md`）。用户 2026-10-11：按此包调整多 seed 优先级；新下载的数据一律放在 `/projects/EEG-foundation-model`。
- 多 seed：广覆盖 3401；3407/3413 只用于 `configs/seed_confirmation_pairs.yaml` 的角色（含对照）。包内只读登记脚本在 server 计划上的结果与包内 `governance/seed_pair_roles.json` 完全一致（2,565 项需求，1,615 项已在 v3.0 计划，950 项缺）。950 行新面板写入 `plan_ext.jsonl`（第 300–1249 行，id 按包的签名规则），750 行 v3.0 面板行（无任何角色需要：CS_SINGLE 的 dense 读出/互补变体、lag-local CS 的早/晚/联合窗）标为 `deferred_redundant`，不删除，开关文件 `PANEL_V30_RESUME` 可恢复。细节、理由与各族数量见 `ADDENDUM_03_ALN3_1_SEED_PANEL.md`；登记表 `private/auditory_alignment_v3/governance/`。
- 调度：`make_queue.py` 排除 deferred 行并在"计划 ∪ 扩展行"上解析依赖；分派器 `run.py`（不计哈希）让各族 runner 的依赖查找看到扩展行。所有族组代码哈希不变（与 ADDENDUM_02 / §5 相同）。重建后队列：small 2,289、fm 2,920 行；面板 C/D/E 行随同 seed 基础单元完成进入。
- 旧第 2 项：小编码器多 seed 已全部完成；旧粗时间 FM 补 seed 1,774 行仍为可恢复 backlog（`ITEM2_FM_RESUME`）；已完成的 ALN2 三 seed 面板（480 单元）保留并按更正实体重汇总；无角色需要 ALN2 FM 的新 seed，不补。第 3 项：3a 500/500 完成；3b/3c 400 个训练单元从未训练，映射见 `ITEM3_TO_B_MAPPING.md`（400/400 均有对应 B 行）。
- Federici：R_FEDERICI 已按 v3.1 规则（HC-v 独立身份与年龄、一个幻影九次会话）；loader 的折分组与年龄字段不进入任何训练/教师/采样路径，不重训（ADDENDUM_03 §3）。
- 未开始：docs/13 并行科学分析（先冻结预登记）；docs/14 新资源（候选，未下载；/projects 卷剩余 2.0 TB）。
- 调度修正（2026-10-11 10:05）：小队列 09:30 跑空后，基础模型 keeper 占满 10 个 runfill 名额；基础模型 worker 只有在一整轮领不到单元时才退出，于是依赖刚解除的 6 个 E_DISTILL 行排在其后无法开始（小队列 worker 因 QOSMaxGRESPerUser 一直排队）。已把 E_DISTILL 从小队列移到基础模型队列（权重仍为 12，不会与整卡单元同卡），取消 3 个排队中的小队列 worker（未领取任何单元）。只改调度，不改任何计哈希文件。核查：已完成的 260 个带依赖的面板单元（D_ADAPT 80、D_ATTENTION learned_temporal 80、E_PUBLIC_TRANSFER 20 及其他）全部使用同 seed 的基础/孪生/donor 单元；D_ATTENTION mean_score 面板单元无依赖。
- 存储（2026-10-11，用户批准）：已完成单元的 checkpoint 由 `private/auditory_alignment_v3/ckpt_offload.py`（Slurm 作业 1034196，`slurm/aln3_gpu_pool.sbatch` 之外的独立 CPU 作业）逐文件迁到 `<private checkpoint storage>/auditory_alignment_v3/ckpt`（0700）：只迁有完成记录、无领取、无 resume、15 分钟未改动、且不是任何待运行单元依赖的 `_best.pt`；复制后读回校验 sha256，再以原子方式把原路径换成指向副本的符号链接（`torch.load`/`os.path.exists` 跟随链接，单元代码与代码哈希不变）；每个文件写入 `ckpt_offload_manifest.tsv`（linking/done 两行）。迁移前经两轮对抗审查（链接兼容性、竞态与故障），按审查意见加入：依赖保护覆盖全部待运行单元、未知族失败即跳过、交换前再核对、读回绕过页缓存、临时文件清理、SIGTERM 与单实例锁。审查同时发现池脚本领取清理在 squeue 失败时会删除他人领取（可能导致重复运行），已修复（只影响新提交的 worker；备份 `private/auditory_alignment_v3/aln3_gpu_pool.sbatch.before_sweepfix_20261011`）。重跑任何已完成单元前须先删除其符号链接。
- 工程检查：`tests/auditory_alignment_v3/test_aln31_panel.py`（静态：扩展文件前 300 行不变、950 行恰为缺失的角色×seed、新行可解析同 seed 依赖、deferred = 角色补集、分派器可见扩展行），Slurm 作业 1033838：6/6 通过（nodecpu05，4.8 s）。

## 5. 代码版本等价记录

- 2026-10-10 20:20：族注册表（族 → 代码文件）从 `core.py` 移到不计入哈希的 `registry.py`，以便以后绑定新族时不改变已运行单元的版本。这一移动不改变任何计算。等价版本：local `d7e7a3b139c6dcbe` ≡ `89df1dde3d7a49df`；private `f2cf13bc441a6386` ≡ `51341741b9019c88`；dense `d0f2036ab5f5f831` ≡ `040d71894b35349f`（前者为工程探针 1033626 通过的版本，启动后最初的单元使用前者）。

## 7. docs/13 并行科学分析第 1 轮（2026-10-11）

- 用户 2026-10-11 指令"开始"（按包补 docs/13）。预登记 `docs/auditory_alignment_v3/SCI_R1_PREREG.md` **冻结 v3**（2026-10-11 17:57 CEST，sha256 `aab58bc13b27ace76d8ab312ea160fb7a3def1cb027d8672a2d04673b75a158e`，只读）。冻结前没有在真实数据上做任何分析计算：只读接口摸底（4 份报告存 `private/auditory_alignment_v3/sci_r1/design/`），以及合成数据单元测试。
- 冻结前两份独立审查：
  - 协议审查：3 个 blocker、23 个 should-fix。要点：docs/04 三件套列为主要量；FAU CI HSM；完整披露既往私有分析；固定名称；风险矩阵；跨界 token；种子政策；P4 计数；隐私输出。
  - 方法/代码审查：3 个 blocker、13 个 should-fix。要点：固定 SE 的 max-t 在小样本覆盖不足，改为逐重抽学生化的 bootstrap-t（合成模拟 n=9 时覆盖达标）；CS 参考集固定；u 含 L2 归一化；E1b 端到端复现；SB 以风险 R 为主；冻结−原始以 rank_gain 为共同主量；P2 为每个 seed 一个网络并取 3 个抽样；第一层摘要须对滤波器混合不变。
  - 全部 blocker 与 should-fix 已写入 v3；nice 项大多采纳。
- 范围：
  - 本轮实现计划中的 4 行 `F_SCIENCE`，限于已完成的局部主方法（S1 逐 lag 曲线、TG、MD/SB、S3、S4）。
  - S2 推迟到第 2 轮，核心先固定。
  - B/C 主方法列待补，选择规则已固定：dense_query NCE 3401，加同架构 random_full；C 主配方按训练侧早停选择分数选定。
- 代码：新模块 `auditory_alignment_v3/sci_r1/`，不在 FAMILY_CODE 中，不改任何计哈希文件。
  - FAU 未经 ICA 版本的加载器 `fau_noica.py` 是 `auditory_alignment.data.load_fau` 的逐字副本，只把 EEG 数据集名参数化（差异已核对为 2 行）。
  - 冻结时各文件 sha256 存 `private/auditory_alignment_v3/sci_r1/code_sha256_at_freeze.txt`；聚合代码在聚合前按冻结文本完成，届时另记哈希。
  - 单元测试 `tests/auditory_alignment_v3/test_sci_r1_core.py`、`test_sci_r1_private.py`：Slurm 作业 1034261，14/14 通过。测试含玩具队列上与 `evaluate_continuous` 的逐参与者一致性、bootstrap-t 覆盖率、第一层摘要的混合不变性。
- 任务计划 `private/auditory_alignment_v3/sci_r1/plan.json`（sha256 `fcf28997…`）：只由计划行与文件名生成，单元状态在作业内核对。共 32 个 CPU 作业、670 个任务，无缺失单元：
  - FAU、DTU 各 10 个作业，按内容折 × 外折；
  - Federici 5 个，私有 5 个；
  - FAU 未经 ICA 原始参照 2 个。
- 工程检查（E1–E7）：作业 1034262–1034265（Federici、FAU、DTU、私有），各含 2 个 P0 单元；连续任务另含 1 个 ALN2 A_TIME 单元。日志只打印差值与通过/失败；结果见 `private/auditory_alignment_v3/sci_r1/checks/`。
- **结果（2026-10-11 20:50）**：670/670 个任务完成，0 失败。
  - 汇总：作业 1034419，聚合代码的 sha256 见 `private/auditory_alignment_v3/sci_r1/code_sha256_aggregate.txt`。
  - E7：`results/` 的 JSON 0 命中（只扫描字符串；有一个队列用 3 位数字 id，会与数值重合）；SCI 文档对 253 个非数字 id 的扫描也是 0 命中。
  - 结果文档：`SCI_R1_RESULTS.md`（总览，先披露意外）、`SCI_TIME_CURVES.md`、`SCI_TEMPORAL_GENERALIZATION.md`、`SCI_SPATIAL_READOUT.md`、`SCI_GROUP_DEVELOPMENT.md`、`SCI_FEATURE_INCREMENT.md`（部分），以及私有的 `SCI_R1_PRIVATE_RESULTS.md`（0600）。
  - 表格由 `auditory_alignment_v3/sci_r1/report.py` 从汇总 JSON 直接生成。
  - 框架等待用户决定。

## 8. D 族策略臂绑定（2026-10-13）

- 依据：用户批准选择规则（"plan I go"）。设计在任何策略臂单元或探针之前冻结为 `ADDENDUM_04_D_POLICY_BINDING.md`（0444，sha256 `5876deb4…`，记录在 `private/auditory_alignment_v3/logs/operations.log`）。
- 规则：每个（数据集、外折、内容折、seed、目标函数）格子里，取训练侧 `best_selection_score` 最低的候选，候选为 B_DENSE 20 个或 C_COMPLEMENT 12 个。不读任何测试/查询结果。
- 代码只新增文件，已完成单元的代码哈希不变：
  - 选择与模型重建：`policy.py`、`policy_models.py`。
  - 三个族的运行器：`run_adapt_policy.py`、`run_coverage_policy.py`、`run_attention_policy.py`。
  - 训练器：`fm_attention.py`；`complement_coverage_train.py` 由 `private/auditory_alignment_v3/gen_complement_coverage.py` 对 `fm_complement.fit_complement` 做 3 处声明替换生成。
  - 不进哈希的调度文件：`registry.py` 新增 `adapt_policy` / `coverage_policy` / `attention_policy` 三个代码组，`POLICY_GROUP` 控制放行；`run.py` 按行路由。
  - 测试：`tests/auditory_alignment_v3/test_policy.py` 3/3。
- 探针（`probe_out/`，全部通过）：
  - D_ADAPT（作业 1037235）：重建模型的重评与所选单元的记录一致，824 个数值全部吻合（最大差 6e-14 / 4e-7）；适配器初始恒等；两个 DTU 单元完整，显存峰值约 11 GB。
  - D_COVERAGE（作业 1037242）：两种采样对照完成；matched_exposure 的更新上限生效（2 个 epoch 106 步 vs 210 步）。
  - D_ATTENTION（作业 1037249）：dense × alignment_plus_selection（两个选择权重候选，按早停 2AFC 选出 1.0）、complement × selection_only，以及 learned_temporal 派生记录；注意窗口均已评估。
- 放行（13:50）：
  - `make_queue.py` 与 `ckpt_offload.py` 换为新版本（备份 `*.before_dpolicy_20261013`）。策略臂进 FM 队列；卸载依赖覆盖三个族，在 700 行上核对无 fail-closed。
  - 卸载守护重启为作业 1037426。
  - FM 队列最前是 500 个未完成的策略臂行；200 个 learned_temporal 行等对应的 mean_score 完成后入队。
- 所选配置（仅训练侧）：
  - dense：REVE PEFT + channel_phase_linear 占 18/40 个格子。
  - complement：concat_pretrained 占 28/40，残差变体 12/40。残差变体的初值恒等（`init_max_abs_diff_vs_base`）逐单元记录，便于事后检查。

## 9. B/C 阶段性汇总（2026-10-14）

- 依据：用户批准阶段性汇总方案（"可以，按这个方案开始"）。汇总规则在看到任何 B/C/E 汇总值之前冻结为 `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`（0444，sha256 `a7b27951…`，全文见 `private/auditory_alignment_v3/bc_interim/code_sha256_at_freeze.txt`）。
- 冻结前的唯一预检只比较人数与候选/查询数：seed 3401 的 1,650 个 B/C 单元全部完成，且与同折局部基线逐人匹配。
- 新文件（不属于任何训练代码哈希）：`auditory_alignment_v3/bc_interim.py`、`bc_interim_report.py`；复用 `sci_r1/stats.py`（未改动）；`slurm/bc_interim_cpu.sbatch`。
- 合成数据测试：`tests/auditory_alignment_v3/test_bc_interim.py` 5/5，连同 `test_sci_r1_core.py` 共 17/17（作业 1039548）。
- 输出：`docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md`、`C_COMPLEMENT_RESULTS.md`、`results/auditory_alignment_v3/bc_interim/`；私有部分在 `private/auditory_alignment_v3/bc_interim/`（0700/0600），未经用户批准不发布。
