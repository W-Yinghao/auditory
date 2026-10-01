# NEXTMAP 轮发布回执（2026-10-02）

研究者指示"push到github上"。本次发布 NEXTMAP 轮（A0/A1、B0 的 U1–U4、C0、B1，GPU 扩展 G1/G2，H1–H11）的全部非参与者产物。

- 提交：`961edeaa4e5940449fc364db0779e3e7ca62cc96`（`main`），上一提交 `b9c0d9f`；`git ls-remote` 读回与本地 HEAD 一致，检出目录干净
- 公开快照：https://github.com/W-Yinghao/auditory/commit/961edeaa4e5940449fc364db0779e3e7ca62cc96
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变
- 审计材料：`private/github_publish_013/`（候选清单、扣留清单、构建与检查脚本、回执）

| Slurm | 作业 | 结果 |
|---|---|---|
| 1017760 | 构建：95 个候选原样复制并核对 SHA256；追加 191 行有序放行块；编译、语法与内容扫描；放行与扣留探针 | 通过；扫描有 3 处路径命中，审阅为良性（见下） |
| 1017765 | 对 git 实际暂存的内容做最终检查 | PASS |

候选清单按本轮产物逐一列出。工作区（`private/` 除外）自上次发布以来变动的文件，除本地 `README.md` 外都已与检出逐字节一致，没有遗留的非数据积压。

## 内容（95 个文件，0.74 MB；新增 95，编辑更新 2）

- 本轮依据的计划：`AUDITORY_RESEARCH_REFRESH_v1_20260927_b9c0d9f.md`、`AUDITORY_SERVER_EXECUTION_v1_20260927_b9c0d9f.md`
- 代码：`auditory_nextmap/`（20）、`tests/auditory_nextmap/`（6）、`configs/auditory_nextmap_{v1,gpu_v1,h_v1}.yaml`、`slurm/auditory_nextmap_*.sbatch`（4）
- 文档：`docs/auditory_nextmap/`（21）：
  - 三份冻结协议（主轮、GPU、H 系列）及全部带日期的附录；
  - 分报告（年龄信息来源、SIR 预测余量、MFF 语义恢复、净新增队列、G1、G2、H 系列）；
  - 下一步选项、来源状态与最终研究决策。
- 结果：`results/auditory_nextmap/` 的 39 个聚合汇总
- 编辑更新：`README.md` 增加 NEXTMAP 一节与阅读入口，原"最新"重训一节改名；`.gitignore` 追加本轮放行块

## 扣留

- `private/auditory_nextmap/` 全部留在服务器上，包括：
  - 逐儿童年龄预测、嵌入与特征；
  - B-U1–U4 的身份边、语义主张与来源扫描；
  - SIR 逐人概率、折、模型权重、日志与作业台账。
- `private/github_publish_013/`：发布审计材料。
- 本地 `README.md`：是项目索引，不发布；发布版 README 单独编辑。

## 检查

- 97 个暂存路径 = 95 个候选 + `.gitignore` + `README.md`；没有 `private/` 或扣留路径被暂存，工作区没有未暂存的改动。
- 扫描范围：
  - 321 个已知姓名串；已知汉字姓名的 158 个全拼形式（按整词匹配）；
  - 9,133 个已知标识，其中 4,827 个取自本轮私有身份表（B-U1–U4、P0、B1、H1 队列）；
  - 不透明 id、32 位十六进制 id、`M####`、U1 事件文件哈希形式；
  - 源数据根路径、站点以外的绝对路径、2026 年以前的精确日期、邮箱与凭据模式。
- 扫描结果：除下面 3 处审阅为良性的路径命中外，零命中。
  1. 执行版计划里的数据根目录路径。它早已出现在已发布的 `AGENTS.md`、`docs/PROJECT_PLAN.md` 与 `docs/AUDITORY5_REPRODUCTION_v1.md` 中。
  2. 语义恢复报告里一个以省略号代替的路径占位。
  3. 测试里的合成路径。其中的"张三"是通用占位名，不在已知姓名中。
- 26 个 Python 文件编译通过，4 个 Slurm 脚本 `bash -n` 通过。
- `.gitignore` 仍是 fail-closed：95 个候选全部放行；私有目录、逐儿童输出与 `__pycache__` 的探针仍被忽略。

## 说明

- 结论以 `docs/auditory_nextmap/FINAL_RESEARCH_DECISIONS.md` 和 `H_SERIES_REPORT.md` 为准，要点如下：
  - **A 线**：事件锁定表示读出年龄，只在 HA/BDF 系统内成立，信息在刺激后 0.16–0.20 s 与 0.44–0.56 s。它不跨到 MFF；对最强的组合谱特征只有约 3–5 月的优势，线性读出下没有确立。
  - **D2 线**：D2 谱加增强谱后，连续 EEG 的年龄解码在两个系统里都改进了：MFF 13.0 → 10.5 月，BDF 26.9 → 24.0 月（线性读出）。这是事后发现，需要独立数据确认。
  - **SIR**：经验交叉熵仍有 1.35 bit/人。
  - **MFF 语义与身份**：未知任务的语义基本无法恢复；有证据的净新增儿童只有 1 名。
  - **跨协议共享**：这条线关闭。
- 本轮自身的偏差都记录在各报告里，包括：
  - C0 复现容差的修订（附录 001）；
  - 一次登录节点上的环境探针；
  - H8–H10 的 CPU 拟合数超过 H1–H6 预算。
- 只发布了这一显式快照；这次许可不延伸到将来的参与者数据上传。
