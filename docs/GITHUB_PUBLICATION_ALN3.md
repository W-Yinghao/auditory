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
