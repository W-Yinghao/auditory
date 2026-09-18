> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../../PUBLICATION.md).

# HA 档案功能分数：固定 EEG 表征探索检验 v1

本轮完成 56 个候选身份组、每组最早一条记录的 5 外折×3 内折检验。3 个任务、8 种模型均有完整 OOF 预测。

**主要解释范围：预测现存 HA 档案数值。严格 F1–F4 临床资格结论不变。** 量表时点、逐行 IT-MAIS/MAIS 版本及设备采集状态仍有限制；这不是独立外部验证、同期功能解码、未来康复预测或 CI 结论。

来源流程：93 条 BDF 来源 → 61 条合格最早 HA 索引 → 57 条唯一档案链接 → 56 条满足 epoch 数量要求的记录。临床四列缺失数依次为 [0, 0, 2, 13]。

| 任务 | 均值 MAE | 临床最佳 MAE | 临床＋EEG MAE | EEG 增量（95% 区间） | 质量调整增量（95% 区间） |
|---|---:|---:|---:|---|---|
| A_given_C | 14.425 | 3.838 | 4.087 | -0.249 [-0.700, 0.217] | -0.352 [-1.206, 0.431] |
| V_given_C | 18.222 | 5.916 | 5.944 | -0.027 [-0.170, 0.107] | -0.355 [-0.934, 0.117] |
| V_given_C_and_A | 18.222 | 5.281 | 5.233 | 0.048 [-0.189, 0.289] | -0.148 [-1.342, 0.949] |

增量为基线 MAE 减 EEG 模型 MAE，正值表示误差下降。A_given_C 与 V_given_C_and_A 是预先固定的两项主要问题；V_given_C 为并行探索。V_given_C_and_A 明确使用真实听觉档案数值作为已知输入。

## 筛查结论

- A_given_C: `NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED`。
- V_given_C: `NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED`。
- V_given_C_and_A: `NO_CONTROLLED_ARCHIVAL_GAIN_ESTABLISHED`。

仅当主增量、质量调整增量的区间下界都为正，且真实 EEG 优于固定种子的训练内打乱对照，才通过本轮推进门槛。一个打乱种子不是置换检验 p 值。失败于此门槛不等于证明 EEG 与功能无关，也不能通过更换目标或增加架构改写本轮结果。

## 方法与边界

人群选择沿用全量来源的最早身份索引，先于结果和质量筛选，不以更晚记录补位。使用两列目标、年龄和设备月数完整者，PTA 允许训练内插补。身份仍为候选身份；姓名＋标签日期档案链接不证明同期评估。

固定表征是主 QC 通过的两种事件码 epoch：20 通道、250 Hz、−0.2 至 +0.5 秒，按时间均匀取至多 256 个。每通道的 log 方差、log Hjorth mobility 与 log complexity 取记录内中位数，共 60 维。没有事件语义、ERP 峰或静息态推断。

临床模型在内层选择线性/二次岭；组合模型允许完全不用 EEG，临床与 EEG 分别正则。质量摘要为有效 epoch 数、拒绝率、最大头皮峰峰值和记录时长。它们可能同时含生理信息，不能把质量调整解释成完全剔除伪迹。

全部插补、标准化、二次展开及超参数选择仅在相应训练集内完成。区间为 2,000 次固定 OOF 误差的分折内身份 bootstrap，不反映重训/换分折变异，也不是多重比较校正后的确认性结果。此前探索过该队列，本轮结果不属于未经触碰的验证。

## 验证与资源

24 组任务×模型的完整 OOF 指标已从私有预测独立重算；身份内外折无交叉，数据哈希匹配。

本轮累计岭拟合尝试 5399 / 8000（包含合成测试及失败尝试）；全部通过 Slurm，申请时限累计上界 4.250 CPU core·h，0 GPU。逐次作业见 jobs.json；sacct 记账查询状态为 UNAVAILABLE，查询输出/错误留在 private。若记账服务不可用，不能将申请上界当成实际使用量。

逐人数据、标签、分折、预测与系数仅保存在 private。此报告不自动发布 GitHub。

## 历史 PTA 对应关系更正

本轮原表复核发现旧 phase3_ha_covariates_004 的顺序编号与原表实际行号不一致：57 条旧候选记录中，55 条较好耳裸耳 PTA、47 条助听 PTA 与按原行号读取的值不同。本轮已经使用正确原行号，并逐行核对既有临床审计的姓名、年龄、设备月数及两个目标。

旧 PTA 调整结果及其下游使用需要单独更正，不能继续作为可靠的独立支持证据。本轮没有覆盖或替换任何旧结果；也没有因 v3 未直接读取此表就宣称它完全不受间接影响。详见 docs/auditory_fseries_archival/LEGACY_PTA_LINEAGE_AMENDMENT.md。
