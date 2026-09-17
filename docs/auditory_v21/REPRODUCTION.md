> GitHub发布副本：本轮验收后，用户明确要求发布代码与聚合结果。文内“未发布／未push”及早期进行中表述是历史状态；当前以v2.1最终科学报告和final_001为准。个体数据、预测、模型与详细日志仍在服务器。见[发布范围](../../PUBLICATION.md)。

# v2.1 复现入口

本目录扩展 v2.1；不覆盖 `auditory_next` 的旧结果。受限输入、模型、预测和身份分割仍在 private。这里的公开代码不能替代数据访问授权。

所有执行经 `scripts/auditory_v21_cpu.sbatch`，CPU 分区、2 核、16 GB；提交前 `umask 077`。禁止登录节点运行分析、测试、哈希或环境探针。下面 run 名只适用于从未存在这些输出的新工作区；现有工作区不能重复提交已完成的 run。每次作业首先创建不可变源码/配置快照，worker 从快照执行。

```bash
umask 077
sbatch --time=00:15:00 scripts/auditory_v21_cpu.sbatch input_preflight --run input_preflight_003 --config configs/auditory_v21_continue.json
sbatch --time=00:05:00 scripts/auditory_v21_cpu.sbatch test --run tests_009 --config configs/auditory_v21_continue.json
```

预检和测试通过后，以下作业显式指定同一测试回执；改变 Python 源码后须使用新的测试版本，旧快照保持不变。作业总并发不超过4个 CPU，预算按申请核数×时限登记在 JOB_LEDGER.md。

```bash
sbatch --time=00:30:00 --export=ALL,AUDITORY_V21_TEST_RUN=tests_009 scripts/auditory_v21_cpu.sbatch n2_design --run n2_design_001 --config configs/auditory_v21_continue.json
sbatch --time=00:30:00 --export=ALL,AUDITORY_V21_TEST_RUN=tests_009 scripts/auditory_v21_cpu.sbatch closure --run closure_003 --config configs/auditory_v21_continue.json
sbatch --time=00:15:00 --export=ALL,AUDITORY_V21_TEST_RUN=tests_009 scripts/auditory_v21_cpu.sbatch n2_inputs --run n2_inputs_001 --config configs/auditory_v21_continue.json
```

四个独立能力 lane 为 N1_R_SIM、N1_L0、N3_R_SIM、N3_L0。逐 lane 指定环境和配置中的固定 run；例如：

```bash
sbatch --time=01:00:00 --export=ALL,AUDITORY_V21_TEST_RUN=tests_009,AUDITORY_V21_LANE=N1_R_SIM scripts/auditory_v21_cpu.sbatch evaluation --run evaluation_N1_R_SIM_001 --config configs/auditory_v21_evaluation.json
```

全部正/零世界及不可评价分母写入 capability_receipt。强注入通过只确认指定能力夹具，不证明真实微小效应可检出。真实入口会在读取 EEG 特征前校验该 lane 的能力、输入清单和核心算法源码；能力不通过则生成零拟合停止回执：

```bash
sbatch --time=00:30:00 --export=ALL,AUDITORY_V21_TEST_RUN=tests_009,AUDITORY_V21_LANE=N1_R_SIM scripts/auditory_v21_cpu.sbatch real --run real_N1_R_SIM_001 --config configs/auditory_v21_real.json
```

N2 先完成无放回匹配袋与五折角色支持检查。只有新设计支持完整时才冻结对应的独立分布能力和真实矩阵；其他路线的能力回执不能授权 N2。旧袋 imbalance 本身不构成新袋不可行的结论。

`start.json` 记录配置/源码哈希，`input_hashes.json` 记录受限来源，`fit_events.jsonl` 在拟合之前记调用并保留失败。测试的合成拟合另计入 `test_fit_counts.json`。旧失败目录不删除、不得用成功子集替代完整对比。各状态及计划完成结论最终由 finalize 的零拟合作业核验。
