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
