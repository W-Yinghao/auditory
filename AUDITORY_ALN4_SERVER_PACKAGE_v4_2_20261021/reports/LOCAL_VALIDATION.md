# 本地交付验证

2026-10-21完成下列实际检查：

| 检查 | 结果 | 验证范围 |
|---|---|---|
| source_probe_metrics | 7组PASS | masked/multipositive基准、q收益方向、有效rank、非法输入与CLI写入 |
| paired_risk_summary | 8项PASS | GC正而NET负、同Q/完整面板、人内seed、退化CI、不覆盖输出 |
| inspect_existing_state | 8项PASS | 临时Git仓库的三方hash、基准缺失、工作树/commit差异、只读与拒覆盖 |
| 真实旧local checkout intake | 正确返回NEEDS_RECONCILIATION，exit2 | 旧checkout不含新基准；没有误报当前server状态 |
| Python/JSON与合同结构 | 由包校验器检查 | 不执行生产模块；固定20/13family、R2/R3资源和继承ZIP |
| 事件schema | JSON与内部引用静态检查 | 本地无jsonschema，未做完整Draft2020-12真实实例语义校验 |

合计23组/项针对具体风险的合成检查通过，不代表真实数据复算通过。详细命令、输出和检查范围见LOCAL_VALIDATION.json。

独立复核已纠正：source S/Q收益命名、NCE诊断与native CS区分、原outer目标的梯度归因、每snapshot重解固定ridge，以及AUC先逐seed计算再在人内平均。外部比较复核了不同DTU身份、真实输入、候选盲评分、10个真实下游拟合单位和任务适配名称。

尚需server完成：现成生产代码适配、实际checkpoint加载/前向、私有完整事件语义核验、真实队列/输出覆盖、外部模型共同任务运行。本包不声称这些已经执行。

MANIFEST.json与SHA256SUMS覆盖交付内容；运行tools/verify_package.py检查实际文件完整性。该检查仍不等于模型科学有效性。

