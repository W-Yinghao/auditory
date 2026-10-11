# ALN3服务器材料包 v3.0

**2026-10-10 · 基准 `d5b2315` · 研究/执行扩展，非新结果报告**

主线：保留局部时空结构的声音–EEG对齐；通过细时间读出与预训练互补发展有效方法，再研究听觉设备人群、注意选择、儿童年龄和私有HA验配阶段。

**入口**：[SERVER_START_PROMPT.md](SERVER_START_PROMPT.md)  
**完整执行文档**：[SERVER_FULL_DOCUMENT.md](SERVER_FULL_DOCUMENT.md)  
**研究纪律**：[docs/00_RESEARCH_DISCIPLINE.md](docs/00_RESEARCH_DISCIPLINE.md)  
**来源与证据等级**：[SOURCE_INDEX.md](SOURCE_INDEX.md)

## 工作包

| 工作包 | 内容 | 起点 |
|---|---|---|
| R | Federici身份/实体重汇总；私有概率重评价 | 现有预测，不需重跑所有训练 |
| A | 局部时空主通路及目标/容量比较 | ALN2 lag-local阳性 |
| B | 基础模型通道保留、相位线性、dense query读出 | 修复后FM、probe线索 |
| C | 局部+预训练残差与必要容量/随机对照 | 新候选方法，不预设互补 |
| D | 更强主干的注意时间整合、群体覆盖与个人适配 | 完整任务实验 |
| E/F | 私有公共先验迁移、教师、时间/发育与听觉分析 | 私有独立问题持续推进 |

## 文件定位

- `docs/00`–`11`：完整规格；`AGENTS_APPEND.md`：置于server规则文件最前。
- `configs/`：工程起点与实验族；`schemas/`：计划/结果记录结构。
- `plans/units.jsonl`：**5,996条逻辑比较**，包含4,486条广覆盖与1,510条额外seed面板。不是等成本拟合次数，不是独立样本量。
- `src/aln3_reference/`与`tests/`：张量读出、身份聚合、校准与风险参考；不含真实backbone权重或完整训练runner。
- `scripts/`：计划生成、规范长表Federici重汇总、包校验；`slurm/`仅模板，运行前需真实绑定。
- `reports/`：本地接口测试、计划摘要、报告模板；不是新EEG结果。

## 本地验证

```bash
PYTHONPATH=src python -m pytest -q tests
python scripts/expand_plan.py --config configs/experiment_families.yaml --out plans
python scripts/validate_package.py
```

依赖见requirements-reference.txt；优先使用server现有受控环境，不为本包无条件升级模型库。`reports/LOCAL_VALIDATION.md`记录实际本地验证覆盖。

## 交接边界

本包没有修改GitHub、传输到server或提交作业。新行均为planned_needs_binding。真实数据/物理时间、模型层hooks、跨fold教师与迁移、Slurm调度由server接入。正确性检查不等于科学绩效门槛；完整训练不由单个probe/AUC/p值决定。

当前纪律不以负结果为导向，同时保留所有有效弱值与反向值。历史v3自动地图稿、早期必正常、禁止新模型等规则不覆盖本包。
