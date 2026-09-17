> 发布副本：用户在本轮验收后明确要求将代码与聚合结果推送到GitHub。文内“未push／不自动发布”描述该授权之前的状态；个体数据、模型及详细日志仍不发布。历史进行中状态以final_002为准。见[发布范围](../PUBLICATION.md)。

# Auditory Next v2 implementation checklist

状态冻结：本轮 `auditory_next_v2` 为 `NOT_RUN`。以下是执行核对清单，不是已完成工作的清单；不得自动 push、覆盖 Auditory5 v1，或把待实现接口写成已运行。

## 启动与输入

- [ ] 读取并登记 `AGENTS.md`、`PUBLICATION.md`、v1 最终报告、执行决策、v1 reproduction navigation、v1 `S4_final_001` 报告及本 v2 plan；生成 source registry 和 snapshot delta。
- [ ] 只读复用 `private/auditory5_v1/jobs/plan_001/`、`private/auditory5_v1/splits/splits_001/`、既有 routes 与 inner/outer scope；逐项核对 outer/inner encoder、all/left/right、pre/post 和 trial IDs。
- [ ] 新输出只进入 `private/auditory_next_v2/`、`results/auditory_next_v2/`、`reports/auditory_next_v2/`；目录 0700、文件 0600、`umask 077`。
- [ ] 原始 EEG、临床、身份、v1 输入输出只读；逐人/逐试次资料、权重、路径和详细日志留在 private，禁止发布。
- [ ] 所有环境探查、测试、导出、绘图和数值计算通过 Slurm；登录节点只做文本、Git 和调度编排。

## 不可变研究约束

- [ ] B-v1、D-v1 按 `CLOSED_ROUTES.md` (server artifact: `../reports/auditory_next_v2/design_001/CLOSED_ROUTES.md`) 归档关闭；不追加旧 B seed/窗/阈值，不继续 D 的 MUSS-null 搜索，不切换临床终点。
- [ ] E1 不启动；E0-R 只使用既有请求记录、标签、布局、时间块和支持，修复完整 MLP 族并保留失败集合。
- [ ] 不重跑旧 90 个表征任务；新正式 encoder fits=0，优先复用合规 outer/inner features，inner encoder 必须核对训练范围和验证儿童排除证据。
- [ ] 仍用 P1_CAUSAL20/P2_SPATIAL_SPLIT、固定 250 Hz、既定窗口、滤波支持与事件历史前 QC 规则；不做结果驱动时窗/滤波/标签选择。
- [ ] 不跨 fold 拼 embedding 坐标；scaler、PCA、head、calibration 各按 fit scope 重建或引用带 hash 的合规工件。
- [ ] P_bal/P_nat 的训练、校准和评价不得混用；CE 增益保留 bits 单位、负值和 `fixed_oof_no_refit` 限定。
- [ ] 新 N1/N2/N3 固定使用 §13.2：`logistic_C=1.0`、`mlp_lambda=0.001`、seed 11、3 inner folds；这一固定优先于 §4 的候选范围，不能自动展开网格。
- [ ] C2-R/E0-R 仍使用旧协议的 alpha/C 语义和 objective parity；旧 `alpha` 不与新路线 `lambda` 混用、叠加或互相改名。

## 包与依赖顺序

1. **S0/G0：** 生成 registry、核对复用模型/inner scope、共享表和处理可比性；必要时只做 G0 规定诊断。
2. **A2：** 先按事件元数据冻结唯一 Ω、共同支持和 trial draw，再做未校正匹配、pre/common response 和背景残差反例；校正后单独转正不触发训练扩展。
3. **C2-R/C2-S：** 先完成 solver objective parity 与 synthetic gate，再做旧 MLP32/MLP64 完整矩阵；C2-S 先验证五部分空间可逆性，再测 cross-mean/midline 增量。
4. **N1/N2/N3：** 依赖 G0 合规 feature scopes；三条新路线各自优先获得 R_SIM 主矩阵和必要对照，不因 A2 支持不足而阻断。N1 需 H/P/B/PB/PP/noise；N2 固定 k=8 主 bag 与 k 曲线、MU/VAR/H_BAG/pre/重复列；N3 需强 H、H+post、H+pre、H+pre+post/noise。
5. **E0-R：** 与 C2-R 共享 solver 修复原则，但只做原 E0 任务内可读性，不转入 E1。
6. **S3 aggregate：** 每包写实现、支持、控制、科学四轴状态；失败/未运行/预算受限不可压成阴性，最终报告保持 `NOT_RUN` 或实际回执状态。

## 预算与停止

- [ ] 新正式 encoder：0；G0 诊断 encoder 最多 2；C2/E0 新 solver 1 个且只允许一次预定延长。
- [ ] 新神经读出首轮 seed 11；最多 2 条完整新路线可做 seed 23 固定复核，且只在主/控制达标后执行。
- [ ] 浅层 head fits ≤3000，全部 readout fits ≤8000；GPU 并发≤2、CPU 并发≤4；GPU≤32 小时、CPU≤256 小时。
- [ ] 超预算时按计划固定优先级：S0/支持/测试/G0 → A2 与 N1/N2/N3 各自 R_SIM 主矩阵及必要控制 → C2-R 主 R_SIM、C2-S L0、E0-R → N 路线 L0/敏感性 → C2 L0/R_SUP 和 seed 复核。
- [ ] 缺失输入标 `BLOCKED_INPUT`，支持不足标 `INSUFFICIENT`/`DESCRIPTIVE_ONLY`，数值失败标 `NUMERICAL_FAILURE`，预算不足标 `BUDGET_LIMITED`；不补零、不成功子集聚合、不第三次换 solver。

## 必交核对物

- [ ] `TASK_PLAN.csv` 显式列 fit 数、fold/view/mode、内存与预算上界。
- [ ] 每 fit 回执含 scope/input/feature/label/config/code/model/prediction hash、训练/评估计数、校准范围、优化状态和失败阶段。
- [ ] 每包包含支持表、主/次效应、控制、失败与限制；每个必要对照缺失即不能判 `SUPPORTED_SIGNAL`。
- [ ] 最终聚合只读明确 source registry，不搜索“最新/最好”目录；保留所有旧失败和阴性结果。本轮不自动 Git commit/push。

