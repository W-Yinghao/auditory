# FN1 / FN1-A 发布回执 — 2026-09-19

研究者明确指示发布本轮结果。提交 `5b5b662c4d7a2f7dc9dc5499ad0ad6f0add012c0`，独立 `git ls-remote` 回读与本地 HEAD 一致；发布检出干净。

- 提交：https://github.com/W-Yinghao/auditory/commit/5b5b662c4d7a2f7dc9dc5499ad0ad6f0add012c0
- 结果报告：`docs/auditory_fn1a/ARCHIVAL_RECORD_LEARNING_REPORT.md`
- 范围与限制：`docs/auditory_fn1a/ARCHIVAL_SCOPE_AND_LIMITATIONS.md`
本次为**策展快照**：代码、配置、冻结方案、聚合结果与文档进入公开仓库；参与者数据、逐记录表、身份键、逐人分数、预测、窗口与权重留在服务器。

本轮发布**不**由任何自动流程触发；FN1-A 方案 §12 禁止自动 push，且声明"旧授权发布不涵盖新增个体数据"。

## 范围

| 类别 | 数量 |
|---|---|
| 逐字发布的文件 | 102 |
| 去标识化衍生文件 | 2 |
| 明确扣留的文件 | 5 |

发布内容：`auditory_fn1/`（11 个模块）、`auditory_fn1a/`（7 个模块）、`tests/auditory_fn1/`、`tests/auditory_fn1a/`、两份冻结方案、两份配置、两个 Slurm wrapper、`docs/auditory_fn1{,a}/`、`reports/auditory_fn1/`、以及 `results/auditory_fn1{,a}/` 的聚合产物。

## 扣留的内容与原因

| 路径 | 原因 |
|---|---|
| `results/auditory_fn1a/FN1A_export_001/segment_support_summary.csv` | 逐记录表，含 `index_record_id` / `split_group_id` 与 112 个不透明记录 ID |
| `results/auditory_fn1a/FN1A_export_probe_00{1,2}/segment_support_summary.csv` | 同上 |
| `results/auditory_fn1a/FN1A_support_001/support_summary.json` | `dropped` 列表含记录 ID |
| `docs/auditory_fn1/PRIVATE_RESOLUTION_TEMPLATE.csv` | 空模板；其列清单已以 JSON 形式公开，无需再发 CSV |

替代发布的去标识化衍生文件（名称与原文件**不同**，避免同名文件在两处内容不一致）：

- `results/auditory_fn1a/FN1A_export_001/segment_support_distribution.json` — 状态计数、候选/合格窗口与时长的分位数、窗口剔除原因合计、采样率与滤波支持取值集合。无逐记录行。
- `results/auditory_fn1a/FN1A_support_001/support_summary_public.json` — 与原文件相同，但 `dropped` 归约为原因计数。

## 检查

静态检查经 Slurm 999835 执行，覆盖全部 100 个候选文件（回执文档与新测试在其后加入并同样检查）：

- 已知姓名词典 218 条 → **0 命中**
- 已知标识符词典 4,356 条 → **0 命中**
- 不透明记录 ID 正则 → **0 命中**
- 受限列 / 受限 JSON 键 → **0 命中**
- 绝对路径 → 2 处，均为两个 Slurm wrapper 中的站点解释器路径。仓库中 71 个已跟踪 slurm 文件里已有 65 个含同一路径，且 `PUBLICATION.md` 多处声明站点路径为环境设置、非参与者定位符。与既有已披露约定一致。

**本轮对检查器做了一处加强**：不透明标识符正则由 `(B|P|G|M)` 扩展为 `(B|P|G|M|R|V|D|L)`。此前的字母表遗漏了 R（临床行）、V（就诊，其取值是记录哈希替换首字母）、D 与 L——代码实际铸造这六类前缀。

## `.gitignore` 采用更严的模式

本轮新增的否定块对每一层目录采用"再包含目录 → 排除其内容 → 再包含指定文件"，而不是既有的整目录再包含。因此被扣留的逐记录产物即使将来被复制进检出目录，也**按构造**无法被 stage。已双向验证：102 个目标文件全部纳入；3 类扣留路径全部保持排除。

## 本次发布未做的事

未运行任何模型拟合，未重跑任何科学任务，未读取真实 EEG，未联系任何外部人员，未分配 GPU。发布记账与冻结的科研账本相互独立。

## 限制

这不是匿名化证明，也不是对全部历史 Git 修订的扫描；此前披露的旧脚本历史限制继续适用。发布的 `results/auditory_fn1a/` 聚合结果描述 52 个候选身份组，**不是 52 个已临床确证的独立儿童**。FN1-A 的对象是既有档案数字的离线关联，不建立同期临床效度；允许与禁止的措辞见 `docs/auditory_fn1a/ARCHIVAL_SCOPE_AND_LIMITATIONS.md`。

## 回读核验

远端 `main` = `5b5b662c4d7a2f7dc9dc5499ad0ad6f0add012c0`，与本地 HEAD 相同。已确认：3 个扣留文件在远端树中不存在；2 个去标识化衍生文件存在；整个已跟踪树中 `private/` 路径数为 0；仓库共 1,413 个已跟踪文件（本次 +105）。
