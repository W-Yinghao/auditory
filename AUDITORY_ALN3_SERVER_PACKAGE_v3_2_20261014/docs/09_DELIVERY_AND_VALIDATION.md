# 09 · Server接入、交付与本地参考工具

## 最短接入路径

先读`START_NOW.md`与`SERVER_START_PROMPT.md`，合并`AGENTS_APPEND.md`到规则最前，保留历史。记录实际HEAD，确认ADDENDUM_06现有250行和它们的运行状态。读`configs/reuse_actions.yaml`及比较清单，复用已有结果，绑定缺失的具体fold/目标/seed/checkpoint。

本包不是一个已经完成真实数据集成的新runner；不覆盖`auditory_alignment_v3`。建议在该目录新增有版本号的schedule/control/analysis文件，沿用现有batcher、身份清单、目标和原生读出。真正变化的训练用独立注册，不改已经冻结版本。

## 必交结果

| 文件（建议名） | 内容 |
|---|---|
| ALN32_IMPLEMENTATION_RECEIPT.md | 当前代码、复用与新执行、实际输入支持、暂停范围和已提交作业。不要写再次等待go。 |
| ALIGNED_INTERFACE_RESULTS.md | 250行B_ALIGNED原结果、访问匹配local/post-only、实际更新范围注释；原生与共同读出分开。 |
| EFFECTIVE_UPDATE_REPORT.json/md | 每层允许和实际更新、one-step/真实全量对照；名称与事实对应。 |
| COMPLEMENT_REVISED_RESULTS.md | epoch0/训练选择、同query真实风险差、正确与错配context、随机/容量归因。 |
| HEARING_SHARED_TIME_RESULTS.md | SCI_R2共同时间、声音特征、HA/CI/对照及适配后的结构。 |
| PRIVATE_RESEARCHER_SUMMARY.md | 私下交付儿童任务、历史、迁移、年龄/阶段及可用n；不默认公开。 |
| PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md | 已取得/缺失数据和许可、实际规模、方法训练与目标迁移。 |

每轮先说明新建立/改善的能力，再给全部主对照，再说明未支持的配置和竞争解释。解释不能只写“框架由用户决定”；本包科学问题已固定，但不固定答案。

## 核对范围

短工程测试：真实token轴和通道对应、声明窗外扰动不影响strict-local输出、采样边界、非finite、优化器实际更新、epoch0等价、fit/dev/test来源和依赖配对。无分数阈值；测试通过不是神经效度验证。

P5/P6已经做过的检查优先复用，不重复制造大量CPU基准。按当前方法真正新增的接口补检查即可。运行正确性和数据许可之外，不把额外审计当全文实验的前置条件。

## 包内代码

`src/aln32_reference/schedules.py`：旧日程覆盖与清楚的full-update参考；不自动替换生产优化器。
`geometry.py`：带record/segment边界的查询窗与mask，供server对照真实切片；不包含数据loader。
`diagnostics.py`：公共query模板与片段变化分解、风险差、phase-readability合成例子；不估计真实神经MI。
`queue_policy.py`和CLI：逐行只读排程建议，不读取成绩、不调用Slurm。
`tests/`：合成、边界与数值测试，不能作为真实EEG成功证据。

测试命令：
```bash
PYTHONPATH=src python -m pytest -q tests
PYTHONPATH=src python scripts/run_numeric_checks.py --out reports/numeric_checks.json
python scripts/validate_package.py
```

保存私有预测/checkpoint时沿用server权限；公开仅聚合与获准的研究材料。不得因“新包已生成”推断已经push或提交了任何作业。
