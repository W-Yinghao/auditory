# 核 CS-QMI 对齐轮发布回执（2026-10-06）

研究者指示"push到github上"。本次发布核 CS-QMI 声音–EEG 对齐全量轮（Kernel CS / FMCA / InfoNCE）的全部非参与者产物。

- 提交：`84c73924ad3da12181e83400f58f0f67a37af8c4`（`main`），上一提交 `3de8fc2`。`git ls-remote` 读回与本地 HEAD 一致，检出目录干净。
- 公开快照：https://github.com/W-Yinghao/auditory/commit/84c73924ad3da12181e83400f58f0f67a37af8c4
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变。
- 审计材料：`private/github_publish_016/`，包括候选清单、扣留清单、发布版改动记录、构建与检查脚本和回执。

| Slurm | 作业 | 结果 |
|---|---|---|
| 1024341 | 选择：生成候选与扣留清单，以及 1 个发布版（记录源文件与发布文件的 SHA256） | 54 个候选，21.8 MB |
| 1024343 | 第一次构建 | 发现两处问题，见下 |
| 1024345 | 修正后重新选择并构建：复制并核对 SHA256；追加 79 行有序放行块；编译、语法与扩展内容扫描；zip 成员与解压文件逐字节比对；放行与扣留探针 | 通过；1 处命中审阅为误报（见"检查"） |
| 1024346 | 对 git 实际暂存的内容做最终检查 | PASS |
| 1024347 | 回执提交的检查（第一次） | FAIL：回执里原样引用了被误判为邮箱的矩阵乘法表达式；改为文字描述后重查 |
| 1024349 及其后 | 回执提交的检查 | PASS |

第一次构建（1024343）发现两处问题：

1. 包内 `reference/NUMERICAL_TEST_RESULTS.json` 与 zip 不一致。原因：开工时在本服务器运行包内参考测试，`test_losses.py` 把结果写回了包内文件。
   - 已从 zip 恢复原件，解压目录与 zip 重新逐字节一致。
   - 本服务器的测试结果（torch 2.6.0+cu124，9/9 通过）另存为 `results/auditory_alignment_kernel_cs/reference_tests_server_torch2.6.json`，实现说明中已注明。
2. 同一包的 `test_losses.py` 命中邮箱模式。实际是两处用 Python 矩阵乘法运算符 `@` 连接的张量表达式，审阅为误报。

检出目录中第一次构建复制的文件已按候选清单逐个删除，`.gitignore` 恢复，再重新构建。

## 内容（55 个文件，21.8 MB；新增 55，编辑更新 2）

- **材料包**：`AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_PACKAGE_v1_20261005.zip`（11 个成员），以及同名的解压目录 `AUDITORY_KERNEL_CS_FULL_EXPERIMENTS_SERVER_v1_20261005/`。两者逐字节一致。
- **代码**：`auditory_alignment/`，包括：
  - 数据接入与训练侧目标准备；
  - 时间受限编码器；
  - 包内参考损失的逐字副本；
  - 训练、评价（原生与统一读出）与单元运行；
  - 扩展运行器、线性参照；
  - 事后 R1 个体重复性；
  - 两个诊断探针；
  - 汇总与报告。
  
  另有 GPU 池入口 `slurm/auditory_kcs_gpu_pool.sbatch` 与编排脚本 `scripts/auditory_alignment_kernel_cs/`。
- **文档**：`docs/auditory_alignment_kernel_cs/` 下 6 份，以及 3 张组层面的图：
  - 实现说明：数据接入、偏离规格之处、追加实验登记、运行记录；
  - 核心与对照结果；
  - 优化与容量；
  - 时间结构；
  - 组别、发育与功能；
  - 解读草稿（框架待研究者决定）。
- **结果**：`results/auditory_alignment_kernel_cs/` 下 9 个文件：
  - 组层面汇总、对比、发育与功能；
  - 划分清单；
  - 6,210 个单元的运行清单及其状态汇总；
  - 扩展计划；
  - 有效代码哈希；
  - 本服务器的参考测试结果。
- **编辑更新**：
  - `README.md` 增加本轮一节和阅读入口，C3 一节去掉"最新"；
  - `.gitignore` 追加本轮放行块。

## 发布版（只在发布副本中改动；源文件不变，SHA256 记录在 `private/github_publish_016/changes.json`）

| 文件 | 改动 |
|---|---|
| `results/auditory_alignment_kernel_cs/DATA_AND_SPLIT_MANIFEST.json` | 私有任务按外折的儿童计数合并为按组总数 |

## 扣留

以下内容全部留在服务器上：
- 逐单元记录：含各队列的逐人指标与私有任务的逐儿童结果；
- 全部 checkpoint；
- R1 的逐人分半值；
- 逐配置的逐人均值；
- 参与者到外折的映射；
- 诊断探针的输出；
- 已被取代的评价副本与作废的预跑单元；
- 日志、队列与认领目录；
- 改动前的源文件副本与 diff；
- Federici 内容分组表：由数据集文件派生，可由 `auditory_alignment/federici_content.py` 确定性地重新生成；
- `private/` 下的其余内容。

## 检查

- 57 个暂存路径 = 55 个候选 + `.gitignore` + `README.md`。没有 `private/` 或扣留路径被暂存，工作区没有未暂存的改动。
- 扫描沿用 015 的全部规则，包括已知姓名串、全拼形式、已知标识、不透明 id、32 位十六进制、`M####`、事件哈希、2026 年以前的日期、邮箱与凭据模式、`child\d+` 形式，以及更严格的路径规则。另补充本轮私有逐人表中 203 个非纯数字的参与者标识。
- 结果文件中出现的 3 位数字键是学习曲线的 epoch 编号，不是参与者编号。纯数字编号无法按文本扫描，已按结构核对：结果文件中没有逐人条目。
- 扫描结果：除 `test_losses.py` 中的矩阵乘法表达式（见上）外，零命中。
- Python 文件全部编译通过；Slurm 与编排脚本 `bash -n` 通过。
- `.gitignore` 仍是 fail-closed：55 个候选全部放行。以下探针仍被忽略：
  - 逐单元记录、checkpoint、逐人均值、R1 逐人值、发布审计材料；
  - `__pycache__`；
  - 结果、图与脚本目录中额外出现的文件。

## 说明

- 结论以 `docs/auditory_alignment_kernel_cs/` 下的结果文档为准。`NEXT_INTERPRETATION.md` 是解读草稿，论文框架尚待研究者决定。
- 代码与文档中的服务器路径描述本服务器的布局，在别处使用需要改写。完整复现需要：
  - 公开数据集本身；
  - 按申请获得的 DTU 音频；
  - 留在服务器上的私有儿童数据；
  - C3 轮的预处理产物。
- 公开数据集没有在本仓库中再分发。
- 只发布了这一显式快照；这次许可不延伸到将来的参与者数据上传。
