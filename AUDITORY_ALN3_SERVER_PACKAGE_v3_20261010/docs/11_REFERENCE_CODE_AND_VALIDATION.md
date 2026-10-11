# 11 · 附带参考代码能做什么、不能做什么

`src/aln3_reference/`与当前仓库训练器解耦，避免发布未经真实数据验证的“万能runner”。

| 文件 | 可直接使用的能力 | 不包含的部分 |
|---|---|---|
| aggregation.py | 规范长表的身份/条件等权聚合、HC/HC-v配对、人类与phantom分离 | 私有JSON导出、真实身份核实、复杂年龄模型 |
| calibration.py | 正斜率仿射logit校准，截距与稳定NLL | 自动选择临床标签、query校准 |
| readouts.py | 通道保留的相位线性/dense query decoder；零初始化残差输出 | CBraMod/REVE加载、物理时间和实际层hook |
| metrics.py | 对数损失、配对真实风险增量、候选评分 | 实际候选生成、历史条件分布估计 |
| scripts/expand_plan.py | 确定性配置展开、主seed面板、逻辑依赖登记 | Slurm自动提交、checkpoint自动择优 |
| scripts/reaggregate_federici.py | 对规范CSV执行分组/配对重汇总 | 用字符串猜儿童身份 |

参考代码的显式shape/finite/身份检查是数学和工程正确性检查，不是AUC/显著性门槛。测试样本全部人工合成，名称带SYNTHETIC前缀，不能被误作真实队列结果。

运行：
```bash
python -m pip install -r requirements-reference.txt
PYTHONPATH=src python -m pytest -q tests
python scripts/expand_plan.py --config configs/experiment_families.yaml --out plans
python scripts/validate_package.py
```

输出在reports/中记录实际测试状态。测试只覆盖这里提供的模块，不证明已修复server数据集、FM接口或统计结果；真实集成后应运行小规模工程端到端检查，不设置科学绩效准入线。
