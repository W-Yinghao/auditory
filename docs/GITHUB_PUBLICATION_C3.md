# C3 发布回执（2026-10-05）

研究者指示"push到github上"。本次发布 C3 轮（信息分解与深度条件解码）的全部非参与者产物。

- 提交：`421f554a02bfbcec6d693e7fc6555cd387841451`（`main`），上一提交 `dfb154f`；`git ls-remote` 读回与本地 HEAD 一致，检出目录干净
- 公开快照：https://github.com/W-Yinghao/auditory/commit/421f554a02bfbcec6d693e7fc6555cd387841451
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变
- 审计材料：`private/github_publish_015/`（候选清单、扣留清单、发布版改动记录、构建与检查脚本、回执）

| Slurm | 作业 | 结果 |
|---|---|---|
| 1022882 | 选择：生成候选与扣留清单、6 个发布版（记录源文件与发布文件的 SHA256） | 149 个候选，3.07 MB |
| 1022883 | 第一次构建 | 选择脚本与标准库 `select` 重名，导入时出错；检出没有被改动。改名后重跑 |
| 1022884 | 构建：复制并核对 SHA256；追加 189 行有序放行块；编译、语法与扩展内容扫描；3 个 zip 的成员与解压文件逐字节比对；放行与扣留探针 | 通过；扫描有 3 个文件命中，审阅为误报（见下） |
| 1022885 | 对 git 实际暂存的内容做最终检查 | PASS |
| 1022886 | 回执提交的检查（第一次） | FAIL：回执里原样写了私有数据根、上游日期与站点路径；`AGENTS.md` 中命中的私有数据根是 2e79f77（2026-09-19）起已公开的旧内容。改写回执后重查 |

## 内容（149 个文件，3.07 MB；新增 149，编辑更新 2）

- **材料包**：
  - `AUDITORY_C3_SERVER_PACKAGE_v1_20261003.zip`（17 个成员）、`AUDITORY_C3_REVIEW_ADDENDUM_20261005.zip`（8 个）、`AUDITORY_C3_DL_MATH_CHECKS_v1_20261005.zip`（4 个），以及各自同名的解压目录。zip 成员与解压文件逐字节一致。
  - `AUDITORY_C3_DEEP_CONDITIONAL_DECODING_PLAN_v1_20261005.md`
- **代码**：
  - `auditory_c3/`：测量、预处理、公开端与私有端分析、汇总；
  - `auditory_c3/c3dl/`：C3-DL 试跑与全量矩阵；
  - `auditory_c3/wordlevel/`：词层级条件对比；
  - `auditory_c3/ci_edg*.py`：CI 电极图背景；
  - `auditory_c3/vendor/`：引入的 gcmi 与 partial-info-decomp 代码，GPL-3.0，附许可证文件与 numpy 2 补丁。
  - 另有：`tests/auditory_c3/`、`configs/auditory_c3_v1_frozen.json`、`slurm/auditory_c3_*.sbatch`。
- **文档**：`docs/auditory_c3/` 下 22 份，包括：
  - 落地方案、测量修正案 001、G2 之后的决定、冻结后变更记录；
  - 各项登记（C3-DL 试跑与冻结方案、H7、扩展、词层级、电极图）；
  - 结果（C3 v2、C3-DL 试跑与全量、扩展）。
- **结果**：`results/auditory_c3/` 下 26 个聚合汇总，以及 3 张组层面的图。
- **编辑更新**：
  - `README.md` 增加 C3 一节和阅读入口，STORY 一节去掉"最新"；
  - `.gitignore` 追加本轮放行块。

## 发布版（只在发布副本中改动；源文件不变，SHA256 记录在 `private/github_publish_015/changes.json`）

| 文件 | 改动 |
|---|---|
| `results/auditory_c3/C3DL_full.json` | 去掉逐被试的 G_EEG（67 人） |
| `results/auditory_c3/H7_function.json` | 连接回执中的被试编号列表改为计数 |
| `results/auditory_c3/P3_public.json` | 覆盖率中缺失被试的编号列表改为计数 |
| `results/auditory_c3/null_calibration.json` | 设计说明中的 4 个被试编号改为计数 |
| `docs/auditory_c3/POST_G1_CHANGELOG.md` | 删去数据提供者给出的受限下载地址 |
| `docs/auditory_c3/C3_LANDING_PLAN_v1.md` | 删去联系邮箱（该邮箱公开于数据集说明中） |

## 扣留

- `docs/auditory_c3/EMAIL_REQUESTS_v1.md`：发给数据提供者的邮件草稿，含个人联系地址。
- `docs/auditory_c3/REPLIES_AND_FOLLOWUPS.md`：私人往来的摘要与未发出的后续邮件草稿。其他文档中对回复的提及只保留事实（例如 CI 的逐人数据已公开于论文附录）。
- `neuroimage.pdf`：受版权保护的论文 PDF。
- `private/` 全部留在服务器上，包括：
  - 私有儿童数据的逐人输出与身份；
  - 公开数据集的逐被试结果与模型；
  - DTU 音频的访问凭据与受限音频；
  - 解析出的逐人临床表；
  - 没有许可证的第三方代码副本；
  - 日志、发布审计材料。

## 检查

- 151 个暂存路径 = 149 个候选 + `.gitignore` + `README.md`。没有 `private/` 或扣留路径被暂存，工作区没有未暂存的改动。
- 扫描沿用 014 的全部规则（321 个已知姓名串、158 个全拼形式、9,133 + 4,827 个已知标识、不透明 id、32 位十六进制、`M####`、事件哈希、2026 年以前的日期、邮箱与凭据模式），并补充：
  - C3 私有输出中的 72 个儿童或记录标识，以及 `child\d+` 形式；
  - **更严格的路径规则**：凡出现私有数据根目录（站点根下不带 `_public` 后缀的 auditory 目录）一律判失败；公开数据集与派生特征所在的 `auditory_public` 目录，以及 014 的站点路径视为站点配置；其他绝对路径都算命中。
- 扫描结果：除下面 3 处审阅为误报的命中外，零命中。
  1. 方案文献表中 NeurIPS 公开论文链接里的 32 位论文哈希；
  2. `auditory_c3/vendor/SOURCE.txt` 中上游 gcmi 提交的日期；
  3. `docs/auditory_c3/C3_LANDING_PLAN_v1.md` 中 bioRxiv DOI 里的日期形式，以及站点根目录（研究者指定的存放位置，不是参与者路径）。
- zip 本身无法做文本扫描；它们的成员与已扫描的解压文件逐字节一致。
- Python 文件全部编译通过；Slurm 脚本 `bash -n` 通过。
- `.gitignore` 仍是 fail-closed：149 个候选全部放行。以下探针仍被忽略：
  - 私有逐儿童输出、DTU 凭据、逐被试均值、逐人临床表、发布审计材料；
  - 论文 PDF 与两份通信文档；
  - `__pycache__`，以及结果目录中额外出现的文件。

## 说明

- 结论以 `docs/auditory_c3/C3_RESULTS_v2.md`、`C3DL_FULL_RESULTS.md` 与 `C3_EXTENSIONS_RESULTS.md` 为准。
- 代码与文档中的服务器路径描述本服务器的布局，在别处使用需要改写。完整复现需要公开数据集本身、按申请获得的 DTU 音频，以及留在服务器上的私有儿童数据。
- 公开数据集（FAU/TUD Zenodo、DTU Zenodo、Federici Mendeley）没有在本仓库中再分发。
- 只发布了这一显式快照；这次许可不延伸到将来的参与者数据上传。
