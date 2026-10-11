# ALN3.1 server package

**2026-10-11 · 在ALN3上增补，不重启、不覆盖server生产代码。**

先看 [UPDATE_NOW.md](UPDATE_NOW.md)；直接交接 [SERVER_START_PROMPT.md](SERVER_START_PROMPT.md)；完整文档 [SERVER_FULL_DOCUMENT.md](SERVER_FULL_DOCUMENT.md)。

核心A–E保持：局部时空声音–EEG对齐、基础模型dense读出、局部+预训练补充、注意/个人适配、私有儿童迁移。本次重点是纠正Federici身份、明确多seed优先级和把科学读数并行启动。

## 立即决定

小编码器已登记多seed继续；旧粗时间FM全矩阵补seed暂缓且可恢复；已有核心三seed复用；3a评价继续，3b/3c合并B；新核心比较使用3401/3407/3413匹配对照，不把所有计划乘三。具体见 [docs/12_MULTISEED_AND_SCHEDULING.md](docs/12_MULTISEED_AND_SCHEDULING.md)。

HC-v不是按文件号配对的HC儿童；Artifact为一个phantom九次会话。§02、出口脚本和样例已更正。详细迁移见 [docs/15_MIGRATION_AND_REUSE.md](docs/15_MIGRATION_AND_REUSE.md)。

## 文件

- `docs/00–11`：继承并修订的完整训练规格；`docs/12–15`：多seed、科学分析、可选支线和迁移。
- `plans/units.jsonl`：保留原5996条核心logical比较与ID，仅用于对账，不是新的全部提交命令。
- `configs/seed_confirmation_pairs.yaml`：按问题登记的角色对比；`governance/`：待现场绑定的队列/配对/映射，不虚构状态。
- `src/aln3_reference`：修正的聚合、原读出/校准及参考数学接口；不含真实backbone权重或完整Slurm runner。
- `scripts/queue_advice.py`与`register_seed_pairs.py`：离线建议/登记，无提交、取消或删除动作。
- `reports/LOCAL_VALIDATION.md`：本次实际测试范围与结果；不包含真实EEG训练。

不额外要求新数据或新审批才启动ALN3。新的资源/污染研究是可并行的候选，不是把当前工作改成另一个大计划。

## 本地验证

```bash
PYTHONPATH=src python -m pytest -q tests
python scripts/validate_package.py
python scripts/queue_advice.py --input examples/SYNTHETIC_queue.jsonl --output /tmp/SYNTHETIC_queue_advice.jsonl
python scripts/register_seed_pairs.py --plan plans/units.jsonl --rules configs/seed_confirmation_pairs.yaml --output /tmp/SYNTHETIC_seed_roles.json
```

输出位置须用新路径。server按实际已完成记录去重并绑定，不把SYNTHETIC样例当现场账本。

本包只在会话工作目录创建，没有修改GitHub、停止作业或向server提交训练。
