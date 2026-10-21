# GitHub 发布：ALN3 / ALN3.1（进行中）与 docs/13 科学分析第 1 轮（publish_018）

**提交**：
- 内容提交：`8f505de397cd9f3cf0729484c75666e90f164abd`（`W-Yinghao/auditory` main，用 `git ls-remote` 远端核验）。
- 上一发布：`d5b2315`（ALN2）。

**指令**：用户 2026-10-11"现在push一版到github"，并说明新工作基于公开数据集、检查不必过严。

## 内容（277 个路径：266 新增，11 修改）

- **两个用户提供的包**：`AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010` 与 `AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011`。各含 zip 与逐字节一致的解压目录，zip 成员与解压文件逐一核对一致（53 / 73 个成员）。
- **`auditory_alignment_v3/`**：ALN3 各族 runner、`aln3_reference/`，以及 docs/13 科学分析模块 `sci_r1/`；测试在 `tests/auditory_alignment_v3/`；Slurm 入口为 `slurm/aln3_gpu_pool.sbatch`、`aln3_ckpt_offload.sbatch`、`sci_r1_cpu.sbatch`。
- **`scripts/auditory_alignment_v3/`**：编排脚本副本，包括 keeper、refresh、队列构建、计划扩展行 `plan_ext.jsonl`、checkpoint 迁移、ALN3.1 governance JSON。
- **`docs/auditory_alignment_v3/`**：实现回执、增补 01–03、第 3 项到 B 的映射、科学分析第 1 轮的预登记、实现说明与中性结果文档。
- **`results/auditory_alignment_v3/sci_r1/`**：FAU、DTU、Federici 的组层面聚合 JSON 与 33 张图（S1 曲线、TG 热图、S3 地形图）。
- **ALN2 后续**：
  - 代码：`analysis_item1.py`、`analysis_item3a.py`、`fm_ext.py`（附测试），以及 `aggregate.py`、`dispatch.py` 的更新。
  - 文档：ALN2 轮报告、第 3 项预登记与增补，以及 FULL_RESULTS、REPAIRED_FM_RESULTS、实现回执的更新。
  - 其他：`aggregate.json` 与 3 个编排脚本的更新。
- **README**：新增本轮入口。

## 发布副本（只在发布时修改；源文件与发布文件的 SHA256 记录在 publish_018 `changes.json`）

- **私有 checkpoint 存储路径换成占位符**：两份实现回执、`scripts/auditory_alignment_v3/ckpt_offload.py`、`slurm/aln3_ckpt_offload.sbatch`。
- **`SCI_R1_PREREG.md`**：隐去 §0 中一处私有任务汇总数值。冻结原件保存在服务器上（sha256 `aab58bc1…`）。
- **`SCI_R1_RESULTS.md`**：移除私有任务的结果数值（依据预登记 §12）。

## 未发布

- 逐单元记录、逐参与者/逐儿童输出、模型 checkpoint 与其迁移清单。
- 私有任务的组聚合（`results/.../sci_r1/private_agg/`）与私有文档（`SCI_R1_PRIVATE_RESULTS.md`、`R_PRIVATE_CALIBRATION_RESULTS.md`、`FEDERICI_REAGGREGATION_RECEIPT.md` 及对应 JSON）；需研究者批准后才发布。
- ALN2 第 1 项与第 3a 项的结果文档与 JSON（模式 0600，待研究者定框架）。
- 与数据提供方的往来（C3）。
- 2026-10-11 的工作区目录整理：只在单独指示的发布轮中用 `git mv` 镜像。

## 核验

- **构建扫描**（Slurm 作业 1034680）：
  - 词表与 017 相同：321 个已知姓名、158 个全拼形式；另加本轮 253 个非数字参与者/实体标识。
  - 7 项人工复核为良性：两个用户包中的 `/tmp` 合成示例路径、Federici 幻影头的实体标签（设备，不是人）、四处共享数据卷根路径（已在 AGENTS.md 中公开）。
- **最终 `verify_staged`**（Slurm 作业 1034681）：PASS。277 个暂存路径中，候选文件与编辑性文件之外没有其他路径，没有私有或被扣留的路径，没有发现问题。
- **按研究者要求精简检查**：额外的人工对抗审查只完成了结果与图部分（未发现问题），其余部分为提速而停止。

## 进展更新（2026-10-13，publish_019）

研究者指示“你push一版现在的到github上”。自上次发布以来，可发布的 ALN3 代码、测试、文档与聚合结果没有变化，所以本次只更新：

- README 的 ALN3 进度：约 75% 完成，0 失败；seed 3401 的 B_DENSE 与 C_COMPLEMENT 已全部完成；D 族策略臂将按只用训练侧的选择规则绑定。
- `scripts/auditory_alignment_v3/status_brief.py` 的发布副本：增加 `/projects` 剩余空间趋势。

内容提交 `1950ab44ddcb8e34c65d0f5d4a446415ca744e43`（`git ls-remote` 已核对）。构建扫描（Slurm 1037228）只有一项已知良性路径（共享数据卷根路径，同上次）；`verify_staged`（Slurm 1037229）PASS。仍未发布：ALN3 方法比较结果、逐单元记录、checkpoint、私有任务内容；2026-10-11 的目录整理仍未镜像。

## B/C 阶段性汇总与定位探针（2026-10-14，publish_020）

研究者指示“两个都按你推荐的做，先跑定位探针，push一版到github上”。本次发布：

- D 族策略臂绑定：`ADDENDUM_04_D_POLICY_BINDING.md` 与对应代码（`policy.py`、`policy_models.py`、三个策略臂运行器、`fm_attention.py`、`complement_coverage_train.py`，以及 `registry.py` / `run.py` 的路由）、测试与探针副本。
- B/C 阶段性汇总（只有 seed 3401）：
  - 看结果前冻结的 `ADDENDUM_05_BC_INTERIM_AGGREGATION.md`；
  - `bc_interim` 代码与测试；
  - `B_DENSE_READOUT_RESULTS.md`、`C_COMPLEMENT_RESULTS.md`、聚合 JSON，以及事后 `BC_INTERIM_QC_NOTES.md`。
- 定位探针：冻结计划 `BC_PROBE_PLAN_20261014.md` 与 `BC_PROBE_RESULTS.md`。
- 编排副本：
  - `make_queue.py`、`ckpt_offload.py`；
  - `families_on_hold.json`：暂停剩余的 seed 3407/3413 重复与 D 族基础模型/互补策略臂；
  - `aln3_gpu_pool.sbatch`：加入 V100。
- 发布专用派生（未改变逻辑）：
  - 实现回执与 `ckpt_offload.py` 中的私有存储根路径换成占位符；
  - `test_bc_interim.py` 的合成儿童编号改名，派生副本在 Slurm 1039596 中 5/5 通过。

内容提交 `e4d6f3af72f8141f1e7974e8dfbacb4c81c41ff6`（`git ls-remote` 已核对）。

- 第一次构建（Slurm 1039591）发现两个问题，已修正并清回干净的 HEAD：新 `.gitignore` 块会把已跟踪文件重新忽略；测试中的合成编号与私有化名同形。
- 重建（Slurm 1039597）只剩两项已知良性路径，即共享数据卷根路径，与 publish_018 相同。
- `verify_staged`（Slurm 1039610）PASS。

仍未发布：逐单元记录、checkpoint、逐人表、私有任务内容（含 E 族阶段性汇总）。2026-10-11 的目录整理仍未镜像。

## 输入路径与查询对齐探针（2026-10-14，publish_021）

研究者指示“做你觉得所有该做的，并push”。本次发布：

- P5（基础模型输入路径）与 P6（与查询对齐的 patch token）的冻结计划与结果；
- 两个探针脚本副本；
- 实现回执 §10（暂停、探针、publish_020），发布副本中私有存储根路径换成占位符；
- README 进度条目。

内容提交 `8962b5c458c46e2561539c28155232b9801d85c4`（`git ls-remote` 已核对）。构建扫描（Slurm 1039805）只有已知良性的共享数据卷根路径；`verify_staged` PASS。仍未发布的内容同 publish_020。

## B_ALIGNED 登记与启动（2026-10-14，publish_022）

研究者指示“做你觉得所有该做的，并push”。本次发布：

- `ADDENDUM_06_B_ALIGNED.md`：运行前冻结。
- B_ALIGNED 代码：`fm_aligned.py`、`run_aligned.py`，以及出结果前写好的分析代码 `aligned_interim.py`。
- 合成数据测试、生成器与工程探针脚本副本。
- `registry.py` / `run.py` 的绑定（既有代码哈希不变）。
- 队列、卸载与 `plan_ext.jsonl` 的副本（第 3 块共 250 行）。
- 实现回执 §11（发布副本中私有存储根路径换成占位符），以及 README 进度条目。

内容提交 `6326b9b38256236d9801800077c9ef26cb11c6d8`（`git ls-remote` 已核对）。构建扫描（Slurm 1039851）只有已知良性的共享数据卷根路径；`verify_staged` PASS。B_ALIGNED 结果尚未产生。仍未发布的内容同 publish_020。

## ALN3.2 登记、代码与工程回执（2026-10-15，publish_023）

研究者指示“push一版到github”。本次发布：

- ALN3.2 包（zip 与逐字节一致的解压副本，44 个文件）。
- `CORRECTION_01_FULL_UPDATE_LABEL.md`：`pretrained_full − random_full` 改称配方比较，数值不变。
- 运行前冻结的 ADDENDUM_07、09、10、11、12 与 `SCI_R2_PREREG.md`，以及对应的运行器、分析代码（均在出结果前写定）和合成数据测试。
- `PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md`（SparrKULee 下载与数据合同探针）。
- `ALN32_IMPLEMENTATION_RECEIPT.md`：发布副本把一份未发布结果文档的结论摘要换成指向说明。
- `registry.py` / `run.py` 的新代码组路由（既有代码哈希不变）；`scripts/auditory_alignment_v3/` 副本刷新：按执行指定的暂停清单、队列（未完成行优先）、卸载、状态与监控脚本、`plan_ext.jsonl` 第 4–7 块、生成器与工程探针。
- `slurm/aln3_gpu_pool.sbatch`：显存小于 20 GB 的卡跳过已知会显存不足的单元。
- README 进度条目。

内容提交 `862295f16a88b01dec908a3dd0e70b52fb34e7ae`（`git ls-remote` 已核对）。构建扫描（Slurm 1041322）只有已复核的良性命中：ALN3.2 包与脚本中的共享数据卷根路径，以及 SparrKULee 回执中引用其公开 README 的 BIDS 编号（与公开数据集编号同名）。`verify_staged`（Slurm 1041325）PASS。

未发布：ALN3.2 结果文档与聚合（低复杂度互补、D 族局部臂、SCI_R2、实际更新范围核算；待研究者定框架）、私有研究者汇总 ADDENDUM_08 及其代码、公共先验增补草稿 ADDENDUM_13、checkpoint 清理工具与清单；其余同 publish_020。

## ALN3.2 结果文档与草稿（2026-10-15，publish_024）

研究者在 publish_023 之后批准发布其中暂缓的三组内容（“这三个全可以发布”）：

- 冻结分析代码生成的结果文档及聚合 JSON：低复杂度互补（`COMPLEMENT_REVISED_RESULTS.md`）、D 族局部臂（`D_ATTENTION_RESULTS.md`、`D_ADAPT_RESULTS.md`、`D_COVERAGE_MATRIX.md`）、`SCI_R2_RESULTS.md`、实际更新范围核算（`EFFECTIVE_UPDATE_REPORT.md`）。尚未加研究者的解读框架。
- `ADDENDUM_08_PRIVATE_RESEARCHER_SUMMARY.md` 及其代码 `aln32_private_summary.py` 与合成数据测试。
- `ADDENDUM_13_ALN32_PUBLIC_AUDIO_PRIOR_DRAFT.md`：仍是草稿，未冻结。
- `ALN32_IMPLEMENTATION_RECEIPT.md` 改为逐字发布；README 链接。

内容提交 `da47d3c5a4859decfd67822e67416333a7c47595`（`git ls-remote` 已核对）。构建扫描（Slurm 1041327）无命中；`verify_staged`（Slurm 1041328）PASS。

仍未发布：ADDENDUM_08 的产物（`PRIVATE_RESEARCHER_SUMMARY.md`、`private_age_stage.json`，0600；批准范围是增补文档与代码）、checkpoint 清理工具与清单；其余同 publish_020。

## 私有研究者汇总（2026-10-15，publish_025）

研究者批准发布 ADDENDUM_08 的产物（“这个也发布”）：

- `docs/auditory_alignment_v3/PRIVATE_RESEARCHER_SUMMARY.md`：发布副本。原标题中的“not for publication”换成发布说明，并加一行指向 CORRECTION_01（§2 原样收录 ADDENDUM_05 私有中期表，其中“matched-update initialization”标签已由 CORRECTION_01 更正为配方比较）；其余内容不变。
- `results/auditory_alignment_v3/aln32_private/private_age_stage.json`：逐字发布。

两份都只含组级聚合（均值、区间、n）；n < 5 的格子只报告 n；没有逐儿童数值或编号。原件仍在私有目录（0600）。

内容提交 `257a3774afbb5241f68d1c753598c6cbdba3158c`（`git ls-remote` 已核对）。构建扫描（Slurm 1041333）无命中；`verify_staged`（Slurm 1041334）PASS。

仍未发布：`PRIVATE_E_INTERIM.md` 与 `private_e.json`（其方法比较表已随上述汇总 §2 公开）、其他私有任务文档、checkpoint 清理工具与清单。

## B_ALIGNED 结果与存储清理记录（2026-10-16，publish_026）

研究者指示“提交一版到github”，并在发布过程中指示“B_ALIGNED结果文档和聚合JSON以后改为发布”。本次发布：

- `docs/auditory_alignment_v3/B_ALIGNED_RESULTS.md`：发布副本，在标题下加发布说明，并在第 4 节开头加一行指向 CORRECTION_01。第 4 节“initialization (matched full update)”这个标签实为配方比较；数值和其余内容不变。
- `results/auditory_alignment_v3/b_aligned/b_aligned.json`：逐字发布，只含组级聚合，没有逐人字段。
- `docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md`：记录 2026-10-15 按研究者指示删除的 ALN2 legacy 与 B 族基础模型权重。发布副本把私有存储路径换成占位符，与以往相同。
- `AGENTS.md`：补记存储清理第 (4) 条，以及本次发布。
- README：进度条目。

内容提交 `3fa78818f181fea810d89987ede40448d759faf1`（`git ls-remote` 已核对）。
- 构建扫描（Slurm 1042395）无命中。
- 第一次 `verify_staged`（1042396）只因为 `.gitignore` 未暂存而 FAIL，没有内容问题；暂存后重跑（1042398）PASS。

以后公开数据集的结果文档与聚合会直接发布，不再等定框架。私有任务产物仍须逐项批准。仍未发布的内容：`PRIVATE_E_INTERIM.md`、`private_e.json`、checkpoint 清理工具与清单；其余同 publish_020。

## 私有 E 族中期汇总（2026-10-16，publish_027）

研究者批准发布（“PRIVATE_E_INTERIM 和 private_e.json 也发布”）：

- `docs/auditory_alignment_v3/PRIVATE_E_INTERIM.md`：发布副本。原标题中的“not for publication”换成发布说明；第 2 节开头加一行指向 CORRECTION_01，因为第 2 节的“matched-update initialization”标签实为配方比较。数值和其余内容不变。
- `results/auditory_alignment_v3/bc_interim_private/private_e.json`：逐字发布。

两份只含组级聚合（n = 64，其中 HA 55、NH 9）：没有 n < 5 的数值格，也没有逐儿童数值或编号。原件仍在私有目录（0600）。

内容提交 `c93318ba2fa1416b8fb8c1c1d757c37708811783`（`git ls-remote` 已核对）。构建扫描（Slurm 1042411）无命中；`verify_staged`（Slurm 1042412）PASS。

仍未发布：SCI_R1 私有结果、私有校准结果、Federici 再聚合回执、ALN2 第 1 项与第 3a 项结果文档、checkpoint 清理工具与清单。

## 其余结果文档（2026-10-16，publish_028）

研究者指示“全部都需要发布，只要不发布私有数据集本身和名字”，并补充“checkpoint 清理工具和清单也不需要”。本次发布：

- **SCI_R1**：
  - `SCI_R1_PRIVATE_RESULTS.md`：发布副本，标题里的“0600，不进发布候选”换成发布说明。
  - `results/auditory_alignment_v3/sci_r1/private_agg/`：5 个聚合 JSON、5 份报告与 2 张图。
  - `SCI_R1_RESULTS.md`：恢复私有任务数值后的完整版。
  - `SCI_R1_PREREG.md`：与冻结原件逐字相同，sha256 `aab58bc1…`。
- **私有任务概率校准**：`R_PRIVATE_CALIBRATION_RESULTS.md` 与 `r_private_calibration.json`。
- **Federici 实体/身份重汇总**：回执与 `federici_reaggregate.json`。其中只有这个公开数据集的记录号，不含人名。
- **ALN2**：第 1 项分析与第 3a 项结果，连同它们的 JSON。
- **C3 数据申请通信**：`EMAIL_REQUESTS_v1.md` 与 `REPLIES_AND_FOLLOWUPS.md`。人名、邮箱、称呼，以及一个以人名命名的目录标签，都换成角色或占位符；文献引用保留。
- **ALN2 环境探针**：`fm_probe.py` 中另一用户的缓存路径换成占位符；`chan_probe.py` 逐字发布。
- **重复的包**：`configs/` 下 ALN3.1 包的重复副本，与根目录 zip 逐字节相同。

**审查**：
- 只读审查工作流 `wf_01ac6be3-2e3`：4 组文件，每组先由一名审查员查看，再由一名对抗性复核员从头复查。
  - 所有私有队列数值都是组层面，n = 64 / 55 / 9，最小格 n = 5。
  - 没有逐儿童行、人名或私有路径。
  - 遮盖处逐一核对：每处只出现一次，遮盖后重新扫描为零命中。
- 构建扫描（Slurm 1042431）只有已复核的良性命中，已列入核验白名单：
  - DOI 中的日期；
  - 探针脚本里的一个 DTU 公开受试者编号。
- 构建时发现 `/docs/*`、`/results/*`、`/scripts/*` 这类宽泛规则会挡住父目录。构建脚本现在会自动补上父目录的放行规则，同时只放行本次列出的文件。
- 核验脚本原先把 `/private_agg/` 一律视为违规，这是预登记 §12 的旧条件，按本次指示取消。`verify_staged`（Slurm 1042440）PASS。

内容提交 `6f5c2369207d6478b40339d864231780202e0240`（`git ls-remote` 已核对）。

**以后的规则**：除私有数据集本身和人名外，全部发布。私有数据集本身包括原始数据、文件与事件索引、临床元数据、身份键和逐儿童记录。

**仍不在仓库中**：
- 上述私有数据集本身；
- 逐单元记录，含私有儿童的逐人行，共 6,443 个文件、188 MB；
- 模型 checkpoint；
- 第三方论文 PDF；
- 第三方依赖库 `.deps_phase3`；
- checkpoint 清理工具与清单；
- 2026-10-11 的 archive 目录重组。这一项按 AGENTS.md 须单独指示。

## ALN3 逐单元记录（2026-10-16，publish_029）

研究者批准发布公开数据集（FAU/DTU/Federici）的逐单元记录。被问到私有队列记录的处理方式时，研究者选择“原样发布”。

发布位置是 `results/auditory_alignment_v3/unit_records/`：
- 每个数据集一个可复现的 `.tar.gz`：DTU 2,613、FAU/TUD 2,466、Federici 826、私有儿童 HA 队列 547，共 6,452 个记录，是 2026-10-16 02:15 的快照。每个包内成员与服务器上的单元记录逐字节相同。
- `MANIFEST.tsv`：每个记录的编号、数据集、族、seed、状态、大小和 sha256。
- 字段说明 `README.md`。

私有队列的记录按每个儿童给出：内部编号 `child<N>`、组别、月龄、助听器佩戴时长（月）和各项模型得分。不含姓名、日期、路径或原始 EEG，编号到人的映射不发布。

**核验**：
- 构建脚本与 `verify_staged` 都扩展为逐个检查压缩包成员，规则与文本文件相同（人名、拼音名、路径、令牌、邮箱）。
- 6,452 个成员与服务器原文件逐一比对，0 个不一致。
- 命中的只有参与者编号：DTU 公开 BIDS 编号、Federici 公开记录标签、私有内部编号，都已列入核验白名单。没有人名或路径。
- 构建（Slurm 1042448）与 `verify_staged`（1042450）PASS。

内容提交 `2c3dc583207fe6aee571dc5d5d43ba470cf6e402`（`git ls-remote` 已核对）。

**仍不在仓库中**：私有数据集本身（原始数据、文件与事件索引、临床元数据、身份键）、模型 checkpoint、第三方论文与依赖库、checkpoint 清理工具与清单、archive 目录重组（须单独指示），以及 ALN2 与 kernel CS 两轮的逐单元记录（尚未打包）。

## ALN3.4 代码、执行与阶段结果（2026-10-18，publish_030）

研究者本次指示：`push一版到github上吧`。沿用已确认的发布范围，个体模型输出不重新请求批准；私有数据集本身、人名和身份映射仍不发布。本次是持续实验中的快照，不是 ALN3.4 全部完成的声明。

内容提交 `4c4323b4c01cef6dd0cb1d99753cbf7cea0f77c9`（已推送，`git ls-remote origin refs/heads/main` 已核对）。

- 发布 ALN3.4 包（zip 与 51 个解压成员逐字节一致）、新增 prior33/aln34 代码、55 个新增测试文件、Slurm 入口、执行脚本副本和冻结计划。
- 发布 D/E 多 seed、注意修正、D_ADAPT 真实风险、true-full 同访问配对、互补功能、校准、滤波边界及新实验中期结果；保留各自时间戳、实际覆盖和不利/不确定结果。
- 发布 FIXC、rich PCA 重拟合代码、公共版 core/rich manifest、实际 M12 GPU 回执及 M13 冻结记录。公共 manifest 与 M13 原件逐字节保留，私有完整版 manifest 和信号缓存不上传。
- 刷新 8,229 份主 runner 记录，并补充 205 份 ALN3.4 lane 记录；8,434 个归档成员均与服务器原件逐字节一致。两套清单分别列成员哈希，不将单元或 seed 当独立受试者。另含 533 个公开数据集 query 得分 NPZ。
- 发布当前监控/补队策略，更新 README 与复现入口；已存在的 checkpoint offload 脚本只刷新公共先验依赖保护。未新增 checkpoint 删除工具或清理清单。
- 334 个发布副本使用既有的存储路径占位符，数值不变。逐单元归档按授权原样保留，其中少量实验哈希命名的 checkpoint 来源路径不包含人名、私有采集索引或模型权重。[逐文件源/发布哈希](../results/auditory_alignment_v3/publication_030/MANIFEST.tsv)记录对应关系。历史冻结文档保留原执行路径与来源哈希。

检查：Slurm CPU `1045420` 冻结快照；`1045425` 构建、逐成员/NPZ 扫描、Python/Slurm 脚本语法与四个 ALN3 包的一致性检查；`1045435` 核对匹配项并生成公开哈希清单；最终暂存区 `1045439` **PASS**，1,688 个路径，无意外文件、遗漏、未暂存更改或未解决匹配。扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符。匹配项仅为公开编号、已授权儿童代号、合成夹具、非识别性来源/临时路径、矩阵运算语法及音频标签的数值时间标记。最终校验对与构建字节完全相同的暂存 blob 复用已完成的扫描，对新增内容重新扫描。原件的少量行尾空白保留，以免改写冻结源码/文档哈希；没有重复训练。

仍不在仓库中：私有原始数据、文件/事件/临床源表、身份映射、人名/联系方式、公共原始数据、模型权重、运行日志和清理清单。工作区归档迁移没有同步。GPU 训练与监控在本次发布期间继续运行。

本轮采用工作区内独立发布副本 `private/github_publish_030/checkout`；原有外部发布副本保留原状态。发布 kit 与检查回执保存在 `private/github_publish_030/`。

## ALN3.4 主面板完成与数值恢复（2026-10-18，publish_031）

研究者本次指示：`push一版到github上`。本轮沿用已确认的发布范围，记录持续实验中的进展。主面板完成不代表全部扩展实验完成。

内容提交 `393d4fefafb592d21dac4a83a4258d42a997b667` 已推送；`git fetch origin main` 后核对 `origin/main` 与该提交一致。

- TRUE_FULL 已完成 800/800，额外 seed 的 one-step 子集 400/400；发布冻结 ADDENDUM_11 的正式分析结果及其执行回执，并刷新同访问配对报告。
- 公共听觉先验完成 1,154/1,154 个新单元，最终报告另列 30 个历史参考，共 1,184/1,184，无工程排除。FIXC、rich PCA、生产 manifest、M12/M13 已在 publish_030 发布，本轮补齐最终结果。
- 发布私有 current/time v2 的同目标数值修复、测试和真实 GPU 回执。生产执行 130/130，其中复用 26 个兼容 v1 结果。另发布 prior LOO 在原 GPU 型号上重放通过的回执与路由脚本；原失败、旧计划和容差保留，不按结果删端点或参与者。
- 更新独立扩展实验的阶段结果、fleet v16/evidence v11 运行入口以及运行时间审计。结果文档保留各自实际覆盖；16:02 的 science v2 汇总仍是 public 154/180、private 117/130，不能把之后的执行完成数当成该文档已经分析的覆盖。
- 主发布快照冻结于 16:28–16:30 CEST；主 runner 记录 8,719 份，补充 lane 快照（16:30:23）1,009 份，共 9,728 个本轮归档成员。记录、seed、复用项不增加独立参与者数。新 lane 快照无损拆为两个独立 tar.gz（282 与 727 个成员，各小于 40 MiB），由 `ALN34_MANIFEST_031.tsv` 映射；publish_030 的原 lane 包与清单逐字保留。

发布入口见 [RELEASE_031](auditory_alignment_v3/RELEASE_031.md)，逐文件源/发布哈希见 [publication_031/MANIFEST.tsv](../results/auditory_alignment_v3/publication_031/MANIFEST.tsv)。冻结源码与实验身份未因发布改写；沿用既有发布副本的私有存储占位符。原样授权的逐单元记录含少量实验哈希命名的 checkpoint 来源路径，不含姓名、私有采集索引、身份映射或权重文件。

**核验**：Slurm CPU `1046273` 冻结快照；`1046277` 完成构建、逐文件/压缩包成员扫描、匹配复核、Python/Slurm 语法检查及四个 ALN3 包的一致性检查；`1046286` 无损拆包并刷新清单；`1046295` 最终暂存区核验 **PASS**。267 个路径，无遗漏、意外文件、未暂存更改或未解决匹配；`git diff --cached --check` 通过。扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符。9,728 个归档成员与服务器原件逐字节一致。最终校验对 260 个与已扫描内容完全相同的 index blob 复用检查；两个重新封装的包另核对原包哈希、逐成员往返一致性及暂存包哈希，再复用已完成的成员扫描，未把压缩包字节变化误当成未变。新增说明与清单重新扫描。

本轮发布副本为 `private/github_publish_031/checkout`，publish_030 副本保持原状态。私有原始数据、文件/事件/临床源表、人名/联系方式、身份映射、模型权重、运行日志、checkpoint 清理清单及工作区 archive 迁移未纳入本次发布。GPU 训练与监控继续运行；发布未重复训练或调整实验日程。

## ALN3.4 完成版科学分析与晚间进展（2026-10-18，publish_032）

研究者本次指示：`你来push一版最新的到github上`。沿用既有发布范围，更新完成的分析及仍在运行的扩展实验快照。内容提交：`419c5a292d014179da35fcb44b5dcc4a0783aa0a`，已推送；重新 `git fetch origin main` 后确认远端提交一致。

- 科学分析 v2 更新为完成版：公共内容/时间 180/180、私有当前声音/时间 130/130，后者含 26 个兼容 v1 复用项。公共先验科学分析完成全部 300 个冻结目标，代表 seed 3401。结果保留完整矩阵、听力组与发育模型及各自推断范围。
- 更新注意迁移、私有 episode、初始化×学习率、CBraMod 听觉续训、强融合、训练数据量与预算等扩展结果。所有中期结果保留实际覆盖和生成时间；不因单元或 seed 数量扩大独立参与者 n。
- 发布第二次原设备数值恢复：V100S 重放 1046588 通过原容差，AUC/NLL/Brier 最大差值 0/2.22e-16/5.55e-17；原失败与来源哈希保留，校准实验线随后恢复。19:59 的进展记录保留当时待运行状态，并追加通过回执，不改写历史。
- 发布晚间运行审计及工期估算。19:59 估计剩余 1,458 个登记执行单元、中心估计 495.7 GPU 小时；属于带外推假设的运行规划，不是日历完成承诺或统计置信区间。
- 结果与单元记录冻结于 20:08–20:11 CEST。8,719 份主 runner 记录与 publish_031 逐字节一致，沿用已有包。20:10:53 的 lane 快照有 1,269 份，比上一版多 260 份；本轮无损拆为四个包，分别含 208、157、531、373 个成员，每个小于 28 MiB。所有新包成员与服务器原件逐字节一致；publish_030/031 的包与清单保持原样。

入口为 [RELEASE_032](auditory_alignment_v3/RELEASE_032.md)，来源与发布哈希见 [publication_032/MANIFEST.tsv](../results/auditory_alignment_v3/publication_032/MANIFEST.tsv)。7 个 CBraMod 续训汇总副本沿用存储路径占位符；大型先验科学 JSON 使用紧凑排版，全部解析后字段、数值及数组顺序经核对相同，服务器结果原件不变。原样授权的单元记录保留非身份性的实验哈希 checkpoint 来源路径，不包含权重字节。

**核验**：Slurm CPU `1046603` 冻结快照；`1046612` 完成构建、JSON 解析、Python/Slurm 语法、四个 ALN3 包一致性、逐文件与逐压缩包成员扫描、无损拆包及清单生成；`1046635` 最终暂存区检查 **PASS**，共 102 个路径。没有遗漏、意外文件、未暂存更改或未解决匹配，`git diff --cached --check` 通过。扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符；匹配项仅为已公开编号、已授权儿童代号和非身份性模型来源路径。最终检查复用 93 个字节完全一致的已扫描 index blob；四个新包另校验原包与暂存包哈希、所有成员往返一致性，再复用已完成的成员扫描。新说明和清单重新扫描。

本轮使用 `private/github_publish_032/checkout`；publish_031 副本保持原状态。私有原始数据、文件/事件/临床源表、身份映射、人名/联系方式、公共原始数据、模型权重、运行日志、checkpoint 清理清单及工作区 archive 迁移未纳入本次发布。GPU 训练与监控继续运行；发布没有重复训练、清除旧暂停或改变实验日程。

## ALN3.5 有限比较完成、已完成汇总首次读出与 Claude Code 接手（2026-10-20，publish_033）

研究者本次指示：`push到github上`。沿用既有发布范围；本轮起由 Claude Code 操作。内容提交 `1361ba06c44d255ce21279ac0075e78e85313ccb` 已推送，`git ls-remote origin refs/heads/main` 读回一致。

- 发布 ALN3.5 包（zip 与 50 个解压成员逐字节一致）与独立的 ALN3.4 全量实验文档；`auditory_alignment_v3/aln35/` 代码、测试、`slurm/aln35_*` 入口；`scripts/auditory_alignment_v3/aln35/` 下的编排副本（fleet v2/v3、证据服务、插件登记、绑定记录、fleet v3 回执）及 `docs/auditory_alignment_v3/aln35/ops/` 下的接入回执。
- 发布 ALN3.5 已完成比较（APwrong、44 人三 seed 融合归因、注意顺序、B×T 分解、CB 状态、history 接口、成对科学与组差、私有 pre 输入勘误）和 support / episode 压力 / 同更新次数 / true-risk 选模的完整汇总（1050758 及其历史快照）。
- 发布已完成汇总的首次读出与解读：1050758 解读、science v2（内容/时间 180 + 私有当前声音/时间 130）与公共先验科学（300）的可读报告和全部格子 CSV、私有 C10/H10 温度选择核查，以及 2026-10-20 项目梳理。读出只读取冻结聚合，未重拟合、未重新 bootstrap。
- 发布两条新登记有界实验的冻结设计、代码、计划与测试（S35_CBAUD_PEOPLE 20 单元；seed-3407 episode 复核 10 单元）；两者工程探针已通过，正式结果不在本次发布中。
- 刷新 ALN3.4 扩展结果（注意迁移、breadth、预算/数据曲线中期、CB 听觉续训、CS episode、强融合、私有 episode/factorial、先验诊断），各自保留生成时间与实际覆盖。
- 逐单元记录：主 runner 8,719 份与 publish_032 相同，未重新上传。新增 `lanes_033_*.tar.gz` 四个包（157/674/337/261 个成员，各小于 35 MiB）及 `LANES_MANIFEST_033.tsv`：1,070 份此前未逐字节发布过的 ALN3.4 lane 记录（与 publish_030/031/032 清单按成员名与 SHA256 比对），以及 359 份 ALN3.5 lane 记录（前缀 `aln35/`），快照 10:29 CEST。所有成员与服务器原件逐字节一致；旧包与清单保持原样。记录、发布版本与 seed 不增加独立参与者 n。

入口为 [RELEASE_033](auditory_alignment_v3/RELEASE_033.md)，来源与发布哈希见 [publication_033/MANIFEST.tsv](../results/auditory_alignment_v3/publication_033/MANIFEST.tsv)。63 个发布副本沿用私有 checkpoint 存储占位符，数值不变。原样授权的单元记录保留 540 条按实验哈希命名的 checkpoint/缓存/ledger 来源路径，不含姓名、记录编号或权重字节。

**核验**：CPU normal 作业数高于 27 的提交线，因此快照、构建与门禁均以 `srun --overlap` 步骤在证据作业分配 1047358 内运行，未新开 CPU 批作业（日志 `private/github_publish_033/{prepare,build,verify}-step.log`）。构建完成 JSON 解析、Python/Slurm 语法、五个 ALN3 包 zip/解压一致性、逐文件与逐压缩包成员扫描、无损拆包及清单生成；扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符，未批准标识符 0。人工复核 6 项为良性：ALN3.5 包与一个运行检查脚本中的裸共享盘根路径、两份代码中的矩阵乘法写法、上述归档来源路径。最终暂存区检查 **PASS**：918 个路径，无遗漏、意外文件、私有/扣留路径、未暂存更改或未解决匹配；909 个与构建字节相同的 index blob 复用已完成扫描，四个新包复用逐成员往返校验。`git diff --cached --check` 仅报告 3 个读出 CSV 的 CRLF 换行（RFC 4180）和 2 个读出 Markdown 末尾空行，保留与服务器输出逐字节一致。

本轮未发布：私有原始数据、文件/事件/临床源表、身份映射、人名/联系方式、仅限服务器的支持集几何绑定、模型权重、运行日志、存储清理工具/清单与入口、交接记录及其核查脚本。本轮使用 `private/github_publish_033/checkout`；publish_032 副本保持原状态。GPU 训练与监控继续运行，发布未重复训练或改变实验日程。

## 两条 ALN3.5 有界实验线的结果（2026-10-20 晚间，publish_034）

研究者本次指示：`你来push一版到github`。沿用既有发布范围。内容提交 `3da8cf5758214c0cf87a1f1c8d67fb84b574000e` 已推送，`git ls-remote` 读回一致；本记录随 publish_035 补交（当时记录提交未完成）。

- 发布 S35_CBAUD_PEOPLE（DTU 44 人）与 seed-3407 episode 复核（10/10）的结果、分析脚本与汇总；fleet v3 回执与 2026-10-20 ECC 失败标记存档脚本。
- 逐单元记录：`lanes_034_001.tar.gz`（8.4 MiB，269 个成员）及 `LANES_MANIFEST_034.tsv`，为 publish_030–033 未逐字节发布的 lane 记录；成员与服务器原件逐字节一致。

入口为 [RELEASE_034](auditory_alignment_v3/RELEASE_034.md)，来源与发布哈希见 [publication_034/MANIFEST.tsv](../results/auditory_alignment_v3/publication_034/MANIFEST.tsv)。

**核验**：快照、构建与门禁以 `srun --overlap` 步骤在证据作业分配 1047358 内运行。扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符，未批准标识符 0；人工/自动复核 19 项（公开队列标识符与授权儿童假名）。导出步骤会重新复制交接核查脚本与存储清理入口，已按扣留清单逐路径剔除（`withheld_dropped.json`）。最终暂存区检查 **PASS**：82 个路径，76 个 index blob 复用构建扫描。

## ALN3.6 与 ALN4.1 第一轮、两个第二轮计划与跨刺激决定（2026-10-21，publish_035）

研究者本次指示：`先push到github上`。沿用既有发布范围。内容提交 `20592b0bd6213fb6b0e2ef667f8d225dcff2a778` 已推送，`git ls-remote origin refs/heads/main` 读回一致。

- 发布 ALN3.6 包与 ALN4.1 包（zip 与解压成员逐字节一致）；`auditory_alignment_v3/aln36/`、`aln41/` 代码；ALN3.6 第一轮科学判断、绑定说明、family 表与逐人结果；ALN4.1 第一轮报告、接入记录与门槛（`scripts/auditory_alignment_v3/aln41/intake/`、`docs/auditory_alignment_v3/aln41/ops/`）、BINDING 与 family 表。
- 发布两个第二轮的 runner、冻结计划（ALN3.6 seed 3407；ALN4.1 seed 3407/3413）、F_SUPPORT 计划、第二轮分析代码，以及跨刺激问题的决定记录（在任何跨刺激结果前按资产语义选定：MFF 纯音→bapa 的偏差关系迁移与 bapa 重拟合）。跨刺激计划列出 MFF 记录编号与身份键，不发布；决定记录的 SHA256 绑定在该计划内。
- 发布 fleet 就绪 shim、2026-10-21 node51 ECC 失败释放脚本与回执，以及 ALN3.4 尾巴的新完成。
- 逐单元记录：`lanes_035_001.tar.gz`（7.3 MiB，398 个成员）及 `LANES_MANIFEST_035.tsv`：publish_030–034 未发布过的 ALN3.4 lane 记录与 ALN3.6/ALN4.1 lane 记录（前缀 `aln36/`、`aln41/`；第二轮为已完成部分）。本轮成员中的私有 checkpoint 存储根路径替换为既定占位符，逐成员来源/发布 SHA256 见 `publication_035/LANE_MEMBER_DERIVATIONS.json`；已发布过的原始记录不因占位符替换重复上传。年龄结果文件（含真实年龄）不发布。

入口为 [RELEASE_035](auditory_alignment_v3/RELEASE_035.md)，来源与发布哈希见 [publication_035/MANIFEST.tsv](../results/auditory_alignment_v3/publication_035/MANIFEST.tsv)。21 个发布副本沿用私有 checkpoint 存储占位符，数值不变。

**核验**：快照、构建与门禁以 `srun --overlap` 步骤在证据作业分配 1047358 内运行。七个 ALN3/ALN4 包 zip/解压一致；扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符，未批准标识符 0；自动复核 44 项（公开队列标识符与授权儿童假名）。人工复核为良性：两个新包中的示例临时文件路径、模型目录占位路径与作者审阅沙箱路径，包规则文本中的只读共享盘根路径，以及 ICLR 论文链接中的 32 位哈希。另对新归档逐成员检查了身份键、MFF 记录编号、真实年龄字段和私有存储根路径，均为 0。最终暂存区检查 **PASS**：327 个路径，无遗漏、意外文件、私有/扣留路径或未解决匹配。`git diff --cached --check` 仅报告包内一份快照与三份 family 表末尾空行，保留与源文件逐字节一致。

本轮未发布：私有原始数据、文件/事件/临床源表、身份映射、人名/联系方式、MFF 记录与身份列表、真实年龄、仅限服务器的支持集几何绑定、模型权重、运行日志、存储清理工具/清单与入口、交接记录及其核查脚本。本轮使用 `private/github_publish_035/checkout`。GPU 训练继续运行，发布未改变实验日程。

## ALN3.6 第二轮、ALN4.2 诊断与论文主线第一批分析（2026-10-22，publish_036）

研究者本次指示：`先push，然后启动一个loop，定期监控实验进展`。沿用既有发布范围。内容提交 `4370a29ddd8ac1c46fe82dbb0c750bc6f5385287` 已推送，`git ls-remote origin refs/heads/main` 读回一致。

- 发布 ALN4.2 包（zip 与解压成员逐字节一致）。
- ALN3.6 第二轮：读出、family 表、R1/R2 复制表；私有通道参数解析缺陷用新包装器修复（`aln36/r2_inproc.py`、lanes v2），原代码未改。
- ALN4.2：
  - 接入记录与第二轮复用索引；
  - 来源学习诊断的代码、计划、结果与报告；
  - 私有儿童事件审计的公开版报告与审计脚本；
  - NET 诊断（两个 seed）；
  - MindMix 外部对照的代码、门槛记录、绑定与就绪报告。
- ALN4.1 第二轮：可续跑的儿童微调版本及其续跑一致性 smoke 回执。
- 论文主线：
  - 投稿蓝图；
  - CS 依赖图谱的代码、计划、逐人单元、汇总与 `ATLAS.md`；
  - MindMix 事后审计的代码与计划。
- 运维：fleet shim、注册表替换/登记回执，以及取消被取代作业的回执。
- 逐单元记录：`lanes_036_001.tar.gz`（3.4 MiB，194 个成员）及 `LANES_MANIFEST_036.tsv`，收录 publish_030–035 未逐字节发布过的 lane 记录，前缀 `aln36/`、`aln41/`、`aln42/`、`paper/`。私有存储根路径替换为既定占位符，逐成员哈希见 `publication_036/LANE_MEMBER_DERIVATIONS.json`。

来源与发布哈希见 [publication_036/MANIFEST.tsv](../results/auditory_alignment_v3/publication_036/MANIFEST.tsv)。9 个发布副本沿用私有存储占位符，数值不变。gzip 压缩的文本表（`.csv.gz`、`.jsonl.gz`）按解压后的文本扫描。

**核验**：快照、构建与门禁均以 `srun --overlap` 步骤在证据作业分配 1047358 内运行。

- 八个 ALN3/ALN4 包的 zip 与解压副本一致。
- 扫描覆盖 321 个已知姓名、158 个全拼形式和 9,386 个标识符，未批准标识符 0。自动复核 61 项（公开队列标识符与授权儿童假名）。
- 人工复核的良性项：
  - ALN4.2 包中的示例服务器根路径和测试夹具里的占位邮箱（保留域名 example.invalid）；
  - 就绪报告中省略形式的公开 HF 缓存路径；
  - `freeze_binding.py` 中用于剥离绝对路径的正则字面量；
  - ICLR 论文链接中的 32 位哈希。
- README 去掉了一个儿童假名，改为描述。
- 新归档逐成员检查：身份键、MFF 记录编号和私有存储根路径均为 0。10 份 ALN3.6 R2 apwrong 记录带逐人 `age_months`/`duration_months`，其 64 组（假名、年龄、时长）与 publish_033 已发布的记录完全相同，没有新增信息。
- 最终暂存区检查 **PASS**：233 个路径，无遗漏、意外文件、私有/扣留路径或未解决匹配。

本轮未发布：
- 私有原始数据，文件/事件/临床源表；
- 身份映射，人名/联系方式；
- MFF 记录与身份列表（含跨刺激计划与 fold 表），事件审计的逐行轨迹与身份对照；
- 真实年龄表；
- MindMix 论文副本；
- 仅限服务器的支持集几何绑定；
- 模型权重，运行日志；
- 存储清理工具/清单与入口，交接记录及其核查脚本。

本轮使用 `private/github_publish_036/checkout`。GPU 训练继续运行，发布未改变实验日程。
