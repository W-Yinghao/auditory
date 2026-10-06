# 传统核 CS-QMI：声音–EEG 全量实验材料

先读 `01_SERVER_FULL_EXPERIMENTS.md`，交接时使用 `SERVER_START_PROMPT.md`。

## 内容

- `01_SERVER_FULL_EXPERIMENTS.md`：完整研究与执行规格。
- `configs/full_experiments.json`：可调整的默认训练配置和实验范围。
- `make_plan.py`：生成完整拟合清单，不启动作业。
- `planned_jobs.jsonl`：4,410条默认计划，全部状态为planned。
- `planned_jobs.summary.json`：任务计数。
- `reference/losses.py`：传统核CS、类别核、FMCA和InfoNCE数值参考。
- `reference/test_losses.py`：短数学／梯度测试。
- `reference/NUMERICAL_TEST_RESULTS.json`：本次实际输出，9项通过。

只依赖已发表的核CS方法，不含VCS-QMI或神经critic。

## 本地可运行

```bash
python reference/test_losses.py
python make_plan.py --config configs/full_experiments.json --output planned_jobs.jsonl
```

数值参考需要Python、PyTorch、NumPy。此材料不要求服务器切换到生成环境的PyTorch版本；沿用其已验证环境，必要时适配API。

## 实施状态

已经完成的是文档、数值参考和计划生成器。真实EEG训练器、数据接入、分折实现、局部网络与Slurm调度没有在此包中实现。计划里的内容折需要映射到真实声音ID，不能仅以数字代替实际隔离。

没有小样本科学门槛。数据接口正确后，按完整数据、完整外折、多seed执行。默认规模不是GPU时间保证，亦不要求一次性提交。
