# 来源索引与证据等级

本包依据最近一轮审阅及以下ALN2来源编写；代码和结果钉在同一提交。数值由仓库报告，不声称本地重新计算了真实EEG。

## S01 · ALN2修复后基础模型结果

类型：result_report。位置：§1–3；Federici混合总表须按S04–S07重汇总。

- [docs/auditory_alignment_v2/REPAIRED_FM_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/REPAIRED_FM_RESULTS.md)

## S02 · ALN2全部结果

类型：result_report。位置：A_TIME、目标、私有、注意、覆盖、适配、多seed；结果为已拟合模型条件汇总。

- [docs/auditory_alignment_v2/FULL_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/FULL_RESULTS.md)

## S03 · ALN2实现回执

类型：implementation_report。位置：§2–7、§11–12；实现与修复、教师、输入、配方。

- [docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/auditory_alignment_v2/IMPLEMENTATION_RECEIPT.md)

## S04 · 数据与身份加载

类型：code。位置：load_federici；人类/HC-v/Artifact、共享identity。

- [auditory_alignment/data.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/data.py)

## S05 · 基础模型评价

类型：code。位置：test_only测试、共同readout、patch评分。

- [auditory_alignment_v2/eval_fm.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/eval_fm.py)

## S06 · ALN2汇总

类型：code。位置：rows_of、table、summ；按输出键聚合而非真实儿童身份。

- [auditory_alignment_v2/aggregate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/aggregate.py)

## S07 · 旧汇总的行提取

类型：code。位置：unit_rows；gain=错配NLL−真实NLL。

- [auditory_alignment/aggregate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/aggregate.py)

## S08 · 局部时间编码器

类型：code。位置：LagLocalBranch、TokenEncoder；40ms/20ms为工程设置。

- [auditory_alignment_v2/temporal.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/temporal.py)

## S09 · 修复后空间头与probe

类型：code。位置：SpatialPatchHead、ProbeReps。

- [auditory_alignment_v2/fm_readout.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/fm_readout.py)

## S10 · 基础模型输入和patch级训练

类型：code。位置：patch范围、0.15*z工程假设、1.2s声音目标。

- [auditory_alignment_v2/foundation_adapter.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/foundation_adapter.py)
- [auditory_alignment_v2/train_fm.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/train_fm.py)

## S11 · 私有原生头评价

类型：code。位置：evaluate_private；NCE温度无截距、CS类别核后验。

- [auditory_alignment_v2/evaluate.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/evaluate.py)

## S12 · 历史窗口常量

类型：code。位置：WINDOWS_MS；legacy右端多一采样点。

- [auditory_alignment/model.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment/model.py)

## S13 · 固定声音目标

类型：code。位置：训练侧标准化、固定半正交映射。

- [auditory_alignment_v2/audio_targets.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/audio_targets.py)

## S14 · 蒸馏与公共donor

类型：code。位置：与S03共同描述旧teacher/donor路径；不复制私有权重。

- [auditory_alignment_v2/distill.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/distill.py)
- [auditory_alignment_v2/donor.py](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/auditory_alignment_v2/donor.py)

## S15 · ALN2发布回执

类型：publication_receipt。位置：公开与扣留产物范围。

- [docs/GITHUB_PUBLICATION_ALN2.md](https://github.com/W-Yinghao/auditory/blob/d5b2315b465519fa2017ff3180fd34a090787164/docs/GITHUB_PUBLICATION_ALN2.md)

## H01 · 历史附件只用于版本关系

《听觉 EEG 公开–私有联合研究方案 v3（JBHI）》2026-10-02：§2的“早期正常、差异只在晚期”、§11和§13的自动地图稿/绩效门槛，均是当时的候选方案；本包明确停用为当前命令，不篡改历史原文。其“公开主线＋私有独立问题、不做ERP主线”的偏好保留。

2026-09-24至09-27的《深挖计划》《发散_解码视角的候选方向》《新结果分析_PF_PF2_DV》《未用数据发散_标签复原与队列扩张》及附录包含早期“关闭/天花板/数据已用尽”表述，不作为ALN3的科学结论或停止规则。未在本包中复刻其过时数字。

## 等级声明

- **报告事实**：S01/S02明确列出的数字及其当时协议。Federici混合总表特标待重汇总。
- **代码审阅结论**：S04–S07给出的实体/身份汇总路径，S11的温度无截距；server核实实际产物后修正输出。
- **解释假设**：时间接口、读出能力和预训练适配可能限制对齐；不是唯一已确定原因。
- **新实施规格**：dense query、相位线性、残差互补、训练侧教师政策、概率仿射校准、实验配置和代码参考；均是ALN3拟开展内容，无真实性能承诺。
