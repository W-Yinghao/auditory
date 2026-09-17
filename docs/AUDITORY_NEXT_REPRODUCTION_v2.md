> 发布副本：用户在本轮验收后明确要求将代码与聚合结果推送到GitHub。文内“未push／不自动发布”描述该授权之前的状态；个体数据、模型及详细日志仍不发布。历史进行中状态以final_002为准。见[发布范围](../PUBLICATION.md)。

# Auditory next v2：执行与复核入口

本轮按 `AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md` 执行。下面记录实际接口和固定来源，不是重新提交已完成任务的指令。当前进度见 `AUDITORY_NEXT_EXECUTION_STATUS_v2.md`；最终状态以各运行的完成或失败回执为准。

## 固定来源

| 用途 | 固定运行 |
| --- | --- |
| 旧输入与环境核对 | S0_001 |
| 新事件、共同支持、bag 支持 | S1_support_004 |
| 旧指标与监督原头诊断 | G0_001 |
| 时间依赖及共同 QC 桥接 | G0_metadata_002 |
| 正式头当前完整测试门限 | tests_010 |
| 最终任务目录 | plan_004 |
| 第一个真实头集成 | integration_001 |
| G0 记录内读出与处理桥接 | G0_readouts_001 |
| A2 主分析 | A2_core_001 |
| A2 原残差拟合及输出失败 | A2_residual_001 |
| A2 零重拟合输出恢复 | A2_residual_recovered_001 |
| N1、N2、N3 | N1_core_001、N2_core_001、N3_core_001 |
| C2 空间诊断、旧非线性修复 | C2S_core_001、C2R_core_001 |
| E0 修复 | E0R_core_001 |
| 固定合成机制对照 | synthetic_001 |

较早启动的包使用各自已验证的 plan_002/003 和 tests_007/008；其精确绑定保存在不可变运行快照内。plan_004 是同一轮预算修订，不能把不同计划的预留拟合次数相加。不能用后续测试覆盖早期执行源码的事实，也不能将焦点模块测试当作全矩阵验收。

所有数据、预测、模型、精确划分、详细异常与来源路径在 `private/auditory_next_v2` 下。CPU/GPU 均经 Slurm，使用既有 eeg2025 环境，BLAS/OMP 线程为 2。没有安装或升级共享依赖，没有新正式编码器拟合。受限目录权限为 0700，文件为 0600。

实际硬件调度：N1/N2/N3使用A40；A40满载后，synthetic/C2R经零拟合兼容性探针后在P100启动。`gpu_compatibility_p100_002`在torch 2.6.0+cu124下通过float64前向/梯度检查；`001`保留探针额外deterministic-only设置导致的失败。随后用户明确要求以后不用P100，尚未启动的E0已从P100转至A100，站点及GPU脚本默认也改为A100；优先A100/L40S/H100，最低V100或RTX6000PRO，见 `GPU_SCHEDULING_POLICY.md`。已运行的两项保留本次进度，不中断重算。没有据真实测试效果选择硬件，也没有改变模型、优化步数或时限；不承诺跨设备逐bit相同。实际覆盖以controller ledger及Slurm回执为准。

## 实际 CLI

以下为命令形式。`NEW_RUN` 必须是未存在的运行名；复核应先查调度器和已有回执，避免重复拟合。

```bash
umask 077
sbatch scripts/auditory_next_cpu.sbatch check-module \
  --run NEW_RUN --source-run metrics_supplement
```

焦点模块允许 `resource_accounting`、`fit_accounting`、`receipt_enrichment`、`metrics_supplement`、`postflight`、`reporting`、`public_audit`。参数名是 `--source-run`，不是 `--module`。此类测试只检查相应汇总/审计逻辑，不拟合读出器。

```bash
sbatch scripts/auditory_next_cpu.sbatch metrics --run NEW_RUN
sbatch scripts/auditory_next_cpu.sbatch fit-accounting --run NEW_RUN
sbatch scripts/auditory_next_cpu.sbatch postflight \
  --run NEW_RUN --source-run S0_001
sbatch scripts/auditory_next_cpu.sbatch resources \
  --run NEW_RUN --plan private/auditory_next_v2/plan_004/plan.json
sbatch scripts/auditory_next_cpu.sbatch report --run NEW_RUN
sbatch scripts/auditory_next_cpu.sbatch audit-public \
  --run NEW_RUN --source-run REPORT_RUN
```

报告读取源码中明确列出的运行，不搜索“最新”或效果最好的目录。最终固定来源汇总由 `scripts/auditory_next_finalize.sbatch` 顺序编排；某项失败仍继续生成失败报告。汇总、哈希、绘图和审计也在 Slurm 内执行。未完成 worker 不能靠读取部分模型生成整族效果。

## 数值与解释边界

新路线保留 logistic 与 float64 MLP32，后者使用显式平均加权 BCE 加 λ=0.001 的权重惩罚；旧 C2/E0 维护保留原 alpha 的样本权重归一化目标。1000 步后若任一神经成员不稳定，整个矩阵统一续至 2000 步一次；续跑不是新增独立 fit。无第三次优化。

旧内折编码器的验证范围仅覆盖声明的 encoder-unseen 子集。未覆盖组可参加相应头训练，不虚构其 OOF 校准预测。温度只由训练 OOF 估计；先验混合单列为诊断。自然与类平衡风险分列。N2 使用 bits/bag，其余刺激增益使用 bits/trial；不能跨单位比较数值大小。

补充 AUROC、双类平方误差之和、校准边界及逐候选删除的均值来自固定预测；不重拟合、不删除候选。区间是固定预测的候选/记录簇 bootstrap，不是整条 pipeline 重拟合。N3 分层支持会检查所有视图与校准版本具有同一测试池，单独保留结构空格与两类计数。

拟合账本区分尝试、明确完成、数值未解决、变换拟合和复用。历史测试计数包含预期拒绝的函数调用，不能将测试通过转换为成功拟合数。若 Slurm 历史会计不可用，实际资源未知；请求时限的保守上界与已知下界分列，不用零代替未知。

## 保留失败与发布边界

A2 原失败发生在所有 20 个背景 ridge 已保存之后，原因是独占创建同名输出文件。恢复运行核验保存模型、范围与配对矩阵后重建统计，新增 readout/PCA/scaler 均为零；原失败目录不改。

G0 记录内拟合回执中 `n_calibration` 曾被校准参数字典长度覆盖。训练输入与保存预测不受此计数错误影响；汇总不使用该字段，实际样本数以拟合起始回执或冻结时间角色核对。

本轮仅在本地生成聚合科研结果。公开边界扫描检查已知标识、路径与个体字段，不等于彻底匿名化证明。冻结计划不授权自动 Git commit/push；本轮没有自动发布。B-v1/D-v1 不重开，E1 保持关闭；混合 MFF 的 E0 结果不能整体称为 CI 群体或临床验证。
