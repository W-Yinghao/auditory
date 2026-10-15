# ALN3.2 实现回执（2026-10-14，持续更新）

## 0. 基准与接入

- **包**：`AUDITORY_ALN3_SERVER_PACKAGE_v3_2_20261014.zip`（sha256 `6628c437…`）。解压为同名目录，44 个文件；SHA256SUMS 43/43 一致。包内代码只读，未运行。
- **基准**：包所基于的 GitHub HEAD 为 `9b9e03e`，与服务器发布副本一致。
- **规则**：`AGENTS_APPEND.md` 已置于 `AGENTS.md` 最前，旧规则作为历史保留（备份 `private/AGENTS_before_aln32_20261014.md`）。
- **用户指示**："go"。两项决定：
  - 真实全量更新的对照在两个已有学习率格子 1e-5 与 3e-4 上都跑，共 400 个单元；
  - SparrKULee 只核查许可与体量，下载前先报告。
- **包与现场的出入**：
  - 包中提到的 `configs/reuse_actions.yaml` 不存在，相应内容在 `seed_and_reuse.yaml` 的 `reuse_actions` 键下。
  - 现有 local 模型读取的样本恰为 [t, t+77)（100 Hz 时为 [t, t+60)），与 post-only FM 的 77 个后窗样本相同。因此包中的 `local_post_exact_matched_to_F2` 就是现有 L0，不另行登记。

## 1. 更正与实际更新范围

- `CORRECTION_01_FULL_UPDATE_LABEL.md`：ADDENDUM_05/06 中把 `pretrained_full − random_full` 标作“initialization (matched full update)”是错误的。两者学习率相差 30 倍，且 REVE 用的是逐步开放前缀的日程，所以这是配方比较。数值与区间不变，只更正标签与解读。
- `EFFECTIVE_UPDATE_REPORT.md`：
  - A 部分覆盖全部已完成的 B_DENSE 与 B_ALIGNED 单元：记录的开放组数与适配方式允许的参数取交，得到可训练的块数；名义学习率由算术给出。
  - B 部分是登记子集（FAU、DTU，外折 0、内容折 0）：实测每组权重相对变化。
  - REVE 的 “full” 到最后一个 epoch 只开放了 22 块中的 9 块，非 block 组从未开放；最佳 checkpoint 多来自只开了约 4 块的 epoch。
  - CBraMod 的 “full” 全部开放，但 FAU 有些 `pretrained_full` 单元的最佳 epoch 落在 warm-up 期内，backbone 实际未变。

## 2. 暂停改为按执行指定

- `governance/held_executions.json` 列出 1,602 个具体执行：B_DENSE 785、C_COMPLEMENT 585、C_CAPACITY_CONTROL 35、D_ATTENTION 180、D_ADAPT 17（均为策略臂）。
- `make_queue.py` 读取这份清单（备份 `*.before_heldexec_20261014`）。
- `families_on_hold.json` 改为 `[]`。这不是全局放行：原先按 family 暂停，现在由上面的显式清单取代，被暂停的旧执行不变。
- 唯一被放行的是 E_GENERIC 的 seed 面板（104 个）。它属于私有单 epoch patch 接口，不依赖已失败的旧 dense 接口。local 的 D 臂此前已全部完成。

## 3. 第 1 波：ADDENDUM_07（运行前冻结，0444，sha256 `2949dc6d…`）

**行**：`plan_ext.jsonl` 第 4 块共 575 行，由 `make_plan_ext_block4.py` 生成；前 1,500 行逐字节核对不变。

| 族 | 行 | 内容 |
|---|---|---|
| ALN32_LOCAL_SUPPORT | 75 | L1 `local_aligned1000`：同一 local 编码器读取 [−0.4, +0.6) s，段首之前置零，共 42 个 token；R1 `raw_aligned1000_ridge` 与 R0 `raw_post600_ridge` 两个 ridge 参照 |
| ALN32_POSTONLY_FM | 100 | F2：B_ALIGNED 的单 patch，前 0.4 s 固定为 0；2 个 backbone × frozen/peft |
| ALN32_TRUE_FULL | 400 | 对齐接口；random 对 pretrained；`full_onestep_v1` / `warmup_then_all_v1` 两种配方；backbone 学习率 {1e-5, 3e-4}；LLRD 1；记录更新账本 |

**代码**：只新增文件，既有哈希不变（B_DENSE `040d7189…`，B_ALIGNED `1add5d0f…`）。

- `local_support.py`。
- `fm_aligned32.py`：由 `gen_fm_aligned32.py` 对 `fit_aligned` 做 10 处声明替换生成。第一次生成时锚点误落在 docstring 内，导致语法错误，修正后重新生成。
- `run_aligned32.py`。
- `registry.py` 新增 `local_support` / `aligned32` 两个代码组，`run.py` 新增相应运行器路由（备份 `*.before_aln32_20261014`）。

**测试**：`test_aln32.py` 6/6，连同既有测试共 13/13（作业 1040153）。

**工程探针**（作业 1040154 / 1040181，V100S；第一次运行因探针脚本自身的 bug 中断，修正后续跑）：
- **L1**：窗口为 [−51, 77)，42 个 token，段首之前为 0；窗外扰动使输出变化 Δu = 0，窗内扰动 Δu = 0.0045；显存 1.9 GB。
- **R1**：完成；FAU 显存 6.7 GB。
- **F2**：前 0.4 s 为 0，其余部分与 aligned 窗口相等；冻结 backbone 时只有读出头可训练。
- **TRUE_FULL**：reve pretrained，`warmup_then_all_v1`，学习率 3e-4。
  - 22 个 block 加非 block 组都从第 6 个 epoch 起开放，全部组都有梯度步，相对权重变化 0.004–0.43；
  - θ_0 重建与起始快照完全一致；
  - FAU 显存 11.6 GB。DTU 有 64 个通道，可能超出 16 GB 卡，由现有的 OOM 重试机制处理，并持续监控。

**放行**（17:20）：
- `make_queue.py` 与 `ckpt_offload.py`（`NO_DEPS`）更新（备份 `*.before_aln32_20261014`）。
- 卸载守护重启为作业 1040189。
- ALN32_LOCAL_SUPPORT 全部放在 FM 队列：L1 权重为 2，可多个合用一张卡；ridge 独占一张卡。原因是 small 队列的 worker 会被 FM keeper 占满的 10 个槽位饿死，与 2026-10-11 的 E_DISTILL 情况相同（备份 `*.before_localfm_20261014`）。
- 为让探针在 10-GPU 上限内启动，取消过两个 pool worker（1039848、1040161），它们各自从 per-epoch checkpoint 续跑。

## 4. 私有研究者汇总：ADDENDUM_08（冻结，0444，sha256 `2490134e…`）

- 输出：`private/auditory_alignment_v3/bc_interim/private/PRIVATE_RESEARCHER_SUMMARY.md` 与 `private_age_stage.json`（0600，作业 1040190）。
- 内容：10 种预定配置 × AUC / NLL / 历史增量，共 29 个格子。每格给出 HA−NH、年龄（每年）、佩戴时长（每年，与年龄分开拟合）、阶段均值与阶段对比，以及每个终点的 n。另附 ADDENDUM_05 的私有方法比较表。
- 隐私扫描 PASS。不进入公开仓库。

## 5. 公共听觉数据

- **SparrKULee（NEMAR nm000238 v1.0.0）**：
  - 80 名参与者，源库原有 85 名，其中 5 名受限；
  - 126 GB；
  - EEG 数据为 CC BY-NC 4.0，刺激仅限非商业使用；
  - 可用 DataLad 或 HTTPS manifest 获取。
- `/projects` 当前剩余 1.7 TB，容量足够。**下载待研究者确认。**
- 在此之前，公共先验先用 FAU、DTU、Federici 做“去掉目标队列”的 donor（待登记）。

## 6. 尚待完成（按依赖顺序，不设绩效门槛）

- B_ALIGNED 250 个单元完成后运行冻结的 `aligned_interim`，随后出 ALIGNED_INTERFACE_RESULTS（含 L1 / F2 / R 对照）与 TF 结果（分析代码 `aln32_interim.py` 在出任何结果前写定）。
- SCI_R2 预登记与 CPU 分析：共同绝对 lag、显式声音特征（S2）、TG、人群与适配。
- 公共先验的数据合同与登记。
- 第 2 波：补充性（简单融合 + 带 epoch0 候选的残差训练）。
- 7 个核心角色的 seed 面板（3407 / 3413），在看到任何 ALN3.2 测试值之前登记。

## 7. 第 2 波、seed 面板、D 局部臂结果、SCI_R2、公共数据（2026-10-14 晚）

用户指示：“可以下载，go，能做的都做了”。

**第 1 波分析代码**：`aln32_interim.py` 在任何 ALN3.2 结果出来之前写定，合成数据测试 1/1；sha 记入 `aln32/code_sha256_at_freeze_add07.txt`。

**ADDENDUM_09 · ALN32_SIMPLE_COMPLEMENT**（100 行，第 5 块）：
- 冻结的 local 基线（L0 / L1）与冻结的对齐 FM 特征，在共同预测空间中用低复杂度方式融合；对 5 组训练参与者做交叉拟合，残差用 base 的 OOF 预测训练。
- 共 6 个变体，分析代码 `aln32_complement_interim.py` 的合成测试通过。
- 探针 1040228（FAU）发现两处问题：
  - 一处 VariantReps 的递归 bug（已修）；
  - 显存峰值 19.6 GB，DTU 估计约需 40 GB。已改为在 8,000 行子样本上拟合 PCA，再分块降维。
- α 网格扩展到 1e-5，因为探针选中了原网格下界（只看训练侧量）。
- DTU 复探针（1040269）在排队；通过后放行并冻结 ADDENDUM_09。

**ADDENDUM_10 · ALN32_RESIDUAL**（250 行，第 6 块）：
- 设计：local 冻结，零初始化残差，epoch 0 作为合法候选，在固定的内部开发组上做跨人选择。
- 探针 1040247 通过：
  - epoch 0 与 base 差 6e-8；
  - 开发风险曲线覆盖 epoch 0–3；
  - 训练路径与评价路径差 6e-8；
  - 显存 3.5 GB。
- ADDENDUM_10 已冻结，18:30 放行（make_queue 与 ckpt_offload 的依赖已更新）；卸载守护重启为 1040276。

**ADDENDUM_11 · seed 面板**（900 行，第 7 块，seed 3407 / 3413，冻结）：
- 6 个核心角色；残差的同 seed base 全部可解析，且均已完成。
- 分析代码 `aln32_panel_interim.py` 已写定；其测试待 normal QOS 有空位再跑。

**ADDENDUM_12 · D 局部臂结果**（冻结后运行，作业 1040261）：
- 输出：`D_ATTENTION_RESULTS.md`、`D_ADAPT_RESULTS.md`、`D_COVERAGE_MATRIX.md`；280/280 个单元。
- QC：adapter none 在两种 support 比例下结果一致。
- 注意：TH_ONLY 的两种预算控制本应完全相同，实际差异在 0.015 bits 以内，说明训练不是逐位可复现。

**SCI_R2**（`SCI_R2_PREREG.md` 冻结；作业 1040271–1040275 共 25 个任务）：
- Q1：嵌套前向模型，env → onset → spec → flux → Ac → Lz。
- Q2：共同 ms 网格上的原始 EEG 读取包络。
- Q3：2–8 Hz 频带匹配。
- F0 / voicing 待做，需要先核对波形与刺激库的对齐。

**SparrKULee**：
- 用户同意下载（作业 1040219，可续传，逐文件按 checksum 校验），目标目录 `/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0`。
- 盘点脚本 `private/sparrkulee/inventory.py` 在下载完成后运行。

**资源**：normal QOS 达到约 30 个作业的共享上限（含其他项目）；新的 CPU 作业在有空位时再提交。

**ADDENDUM_09 放行（20:06）**：
- DTU 复探针 1040365（A40）通过：6 个变体全部完成，显存峰值 7.1 GB，窗口与 B_ALIGNED 一致。
- 两个数据集上，64 维对齐 / 原始特征的残差 ridge 都选中 α 网格下界 1e-5。在 ≥ 2 万行、64 维的条件下，这相当于几乎不加正则的拟合；予以保留。
- 这一说明原定在冻结前写进 ADDENDUM_09，但锚点文本没有匹配，文件已先被冻结，因此改记在本回执与 operations.log 中。记录时间在任何 complement 单元运行之前，不修改已冻结的文件。
- 修复记录：
  - DTU 探针 1040269 因变量名冲突 `parts` 失败，已修；
  - 显存问题通过“8,000 行子样本拟合 PCA + 分块降维”解决。

**SCI_R2 完成（20:52）**：
- 25/25 个任务（作业 1040271–1040275），汇总作业 1040462，隐私扫描 PASS，结果见 `SCI_R2_RESULTS.md`。
- seed 面板分析代码 `aln32_panel_interim.py` 测试 1/1，sha 已追加到 `aln32/code_sha256_at_freeze_add11.txt`，时间在任何面板单元结果之前。

**ALN32_SIMPLE_COMPLEMENT 分析（2026-10-15 06:32）**：
- 100/100 个单元完成后运行冻结的 `aln32_complement_interim.py`（运行前 sha 全部核对 OK）。作业 1040973，隐私扫描 PASS，600 对全部纳入。
- 结果见 `COMPLEMENT_REVISED_RESULTS.md`。机械措辞规则判定：
  - FAU、Federici：8 个 cell 均为 no complement resolved；
  - DTU：4 个 cell 均为“加入对齐特征降低风险，但来源未分离”，即 pretrained 不优于 random 或 small_context。
- 解读待用户定框架。
