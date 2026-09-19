# K0 / K1 发布回执 — 2026-09-19

研究者明确指示发布。本次发布目标函数尺度勘误（K0）与解析临床块的校正性重跑（K1），并为已发布的 FN1-A 结果报告加上勘误指引。

## 内容

- `auditory_k0/`、`auditory_k1/` 源码；`slurm/auditory_k0_cpu.sbatch`、`slurm/auditory_k1_cpu.sbatch`
- `docs/auditory_k0/`（勘误、144 算例的 parity 结果、逐拟合范围 α 与 α/n 表、临床收缩量化）
- `docs/auditory_k1/`（校正报告、窄测试、两目标的指标/配对效应/折与种子/训练诊断/拟合账本）
- `results/auditory_k0/`、`results/auditory_k1/` 的聚合产物
- 路线审阅文件 `AUDITORY_NEXT_ROUTE_REVIEW_5b5b662.md`
- 更新：`AGENTS.md`（上一轮发布状态行）、`docs/GITHUB_PUBLICATION_FN1_ARCHIVAL.md`（补最终 SHA 与回读核验）
- 更新：`docs/auditory_fn1a/ARCHIVAL_RECORD_LEARNING_REPORT.md` —— **仅在顶部加勘误指引横幅，正文一字未改**

## 扣留

本轮 K0/K1 不产生任何逐记录产物：K0 只做合成设计矩阵的代数核验与已冻结折上的临床块闭式对比；K1 复用 FN1-A 已冻结的窗口特征包，未重新读取真实 EEG。逐人预测保存在 `private/auditory_k1/*/predictions.npz`，未发布。

## 结论摘要

K0 确认：`ridge_solution` 解 `SSE+α‖γ‖²`，网络目标为 `MSE+α‖γ‖²`，等价形式相差 n 因子，故 M3/M4 临床块的有效惩罚是 M0/M1/M2 的 n 倍（内折 27/28，外折 41/42）。144 个算例在 FP64 下全部一致。

K1 校正后：A 的 M4\* MAE 6.4932（原 10.2430，恢复 +3.7498 [+1.3332, +5.9973]），V 的 M4\* 5.5286（原 8.5709，恢复 +3.0423 [+1.3082, +4.7768]）。**但仍未建立 EEG 增量**——M1→M4\* 为 +0.1618 [−0.3148, +0.6420] 与 +0.1092 [−0.2466, +0.4358]，区间跨零；学习顺序依然无优势（−0.0008、−0.0051）。

K1 同时改变了正则化尺度与临床块求解方式，按审阅 §5.4 不声称新旧差值完全来自其中某一项。

## 提交与回读

- 内容提交 `2e79f77790ad7e8c44adaa21189d494225ec7e7d`（48 个候选文件 + `.gitignore`；45 个新增路径，3 个更新：`AGENTS.md`、`docs/GITHUB_PUBLICATION_FN1_ARCHIVAL.md`、`docs/auditory_fn1a/ARCHIVAL_RECORD_LEARNING_REPORT.md`）
- 随后一次提交把本回执与 `AGENTS.md` 的发布状态行补齐到上述 SHA
- `git ls-remote origin refs/heads/main` 回读与本地 HEAD 一致

## 核验

Slurm 1000277（候选静态检查）、1000278（落盘）、1000279（对 git 实际暂存 blob 的终检）。终检扫描 49 个暂存 blob，218 个已知姓名、4356 个已知标识符，命中 0；不透明 ID 正则 `(?:B|P|G|M|R|V|D|L)[0-9a-f]{12,16}` 命中 0；`private/` 路径 0。唯一命中项为 3 处绝对路径（`AGENTS.md` 的只读数据根说明，两个 sbatch 的解释器路径），与既有已发布的 `slurm/auditory_fn1*.sbatch` 同类，不含姓名或身份。

`.gitignore` 沿用失败即拒的写法：逐级重新包含目录、立刻排除该目录内容、再按名重新包含文件；未具名的文件即便被复制进检出也不会被跟踪。本轮新增 65 行。

## 本次发布未做的事

未联系任何外部人员，未读取真实 EEG，未分配 GPU，未改动任何已冻结的 FN1-A 数值产物。
