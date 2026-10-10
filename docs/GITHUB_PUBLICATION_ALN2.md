# ALN2 轮发布回执（2026-10-10）

研究者指示"先 push 到 github 上"。本次发布 ALN2（时间保留对齐、EEG 基础模型与读出修复、注意选择、私有迁移）的全部非参与者产物。

- 提交：`d8f6d8e19a6c142561a0aab5fa6d179ccbbec0ae`（`main`），上一提交 `e993e37`。`git ls-remote` 读回与本地 HEAD 一致，检出目录干净。
- 公开快照：https://github.com/W-Yinghao/auditory/commit/d8f6d8e19a6c142561a0aab5fa6d179ccbbec0ae
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变。
- 审计材料：`private/github_publish_017/`，包括候选清单、扣留清单、发布版改动记录、构建与检查脚本和回执。

| Slurm | 作业 | 结果 |
|---|---|---|
| 1033393 / 1033394 | 第一次选择与构建 | 88 个候选；`chan_probe.py` 命中已知参与者编号（一个公开数据集的被试文件夹名出现在 glob 路径中），改为扣留 |
| 1033396 / 1033397 | 撤回第一次构建复制的文件、恢复 `.gitignore` 后重新选择并构建：复制并核对 SHA256；追加有序放行块；编译、语法与扩展内容扫描（含本轮参与者编号）；zip 成员与解压文件逐字节比对；放行与扣留探针 | 87 个候选，9.8 MB；仅剩 3 处审阅过的例外（见下） |
| 1033398 | 对 git 实际暂存的内容做最终检查 | PASS |

## 内容（87 个文件；编辑更新 2）

- **材料包**：`AUDITORY_ALIGNMENT_NEXT_SERVER_PACKAGE_v2_20261006.zip`（36 个成员）及同名解压目录，两者逐字节一致。
- **代码**：`auditory_alignment_v2/`（数据接入与时间编码器、基础模型适配与修复后的通道感知读出、训练与评价、donor/蒸馏/个体适配、汇总），`tests/auditory_alignment_v2/`。
- **Slurm 入口**：`slurm/aln2_*.sbatch`（GPU 池、学习率选择池、汇总、CPU/GPU 检查作业）。
- **脚本**：`scripts/auditory_alignment_v2/`：队列生成、keeper、队列刷新、训练轮数规则、seed 范围、读出修复补丁、冒烟检查、最终审计、诊断探针（这些是 `private/` 下运行副本的拷贝）。
- **文档**：`docs/auditory_alignment_v2/`：实现回执、全部结果表、修复后基础模型结果摘要、多 seed 面板登记（与服务器上只读登记文件逐字节一致，sha256 `b7f7c927…`）。
- **结果**：`results/auditory_alignment_v2/aggregate.json`（只含组层面汇总）。
- **编辑更新**：`README.md` 增加本轮一节，核 CS 一节去掉"最新"；`.gitignore` 追加本轮放行块。

## 发布版（只在发布副本中改动；源文件不变，SHA256 记录在 `private/github_publish_017/changes.json`）

- `docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md`：私有 checkpoint 存储路径替换为占位符。

## 检查与审阅过的例外

- 材料包中 `SERVER_START_PROMPT.md`、`SERVER_FULL_DOCUMENT.md`、`docs/08_IMPLEMENTATION_AND_RUNS.md` 提到只读数据根目录的服务器路径。材料包由研究者提供，须与 zip 逐字节一致；该路径自 `2e79f77` 起已在 `AGENTS.md` 中公开。审阅后放行。
- 扫描覆盖已知姓名、姓名拼音、已知编号与本轮参与者编号；没有其他命中。

## 扣留（留在服务器上）

- 逐单元记录（含逐参与者与逐儿童结果）、逐参与者均值表；
- 全部 checkpoint，包括通道平均变体（`legacy_chmean_v1`）的记录、日志、配方、donor 记录、清单与修复前代码副本；
- donor 权重与记录、学习率选择记录、复用指针、诊断探针输出、归档的失败记录；
- Slurm 日志、领取目录、队列与运行状态；
- `fm_probe.py`（含另一用户的缓存路径）与 `chan_probe.py`（glob 路径含参与者文件夹名）两个早期探针脚本；
- `private/` 下其余全部内容。
