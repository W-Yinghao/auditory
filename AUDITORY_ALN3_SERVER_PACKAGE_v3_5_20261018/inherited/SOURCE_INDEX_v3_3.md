# 来源索引与证据层级

本包基于固定仓库版本 `a3eb744411e79e780c83acf8a5d07be135e8241b` 和当前研究者指令。不是新的真实EEG实验报告。报告数值来自仓库，方法解释为作者判断，新配方为待执行设计。

**[S01] latest repository snapshot**

[README.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/README.md)

发布快照，不是实时队列；B_ALIGNED完成，公共先验仍为草稿。

**[S02] B_ALIGNED results**

[docs/auditory_alignment_v3/B_ALIGNED_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/B_ALIGNED_RESULTS.md)

seed3401；真实风险、原生风险和局部参照；旧full标签服从更正01。

**[S03] full-update correction**

[docs/auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md)

旧full对比是更新范围及学习率不同的配方对比。

**[S04] ALN3.2 implementation**

[docs/auditory_alignment_v3/ALN32_IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/ALN32_IMPLEMENTATION_RECEIPT.md)

继承已登记的访问匹配、真正全量更新、残差及seed面板。

**[S05] public auditory prior draft**

[docs/auditory_alignment_v3/ADDENDUM_13_ALN32_PUBLIC_AUDIO_PRIOR_DRAFT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/ADDENDUM_13_ALN32_PUBLIC_AUDIO_PRIOR_DRAFT.md)

本包将其待决项转为执行决定，不重启全部ALN3。

**[S06] audio target implementation**

[auditory_alignment_v2/audio_targets.py](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/auditory_alignment_v2/audio_targets.py)

旧8-frame、按cohort随机投影不是天然共用的声音坐标。

**[S07] personal adaptation**

[docs/auditory_alignment_v3/D_ADAPT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/D_ADAPT_RESULTS.md)

同会话、已知声音支持，不能叫无标签TTA或临床改善。

**[S08] attention integration implementation**

[auditory_alignment_v3/run_attention.py](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/auditory_alignment_v3/run_attention.py)

随机翻转训练、固定正确方向测试；需候选交换一致性重评价。

**[S09] private E results**

[docs/auditory_alignment_v3/PRIVATE_E_INTERIM.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/PRIVATE_E_INTERIM.md)

保留原生GX、局部CS、特定迁移及其对照；不选择测试赢家。

**[S10] private SCI_R1**

[docs/auditory_alignment_v3/SCI_R1_PRIVATE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/SCI_R1_PRIVATE_RESULTS.md)

部分跨时AUC方向反转，未训练表示也存在类似结构；不是两个独立神经源证明。

**[S11] private calibration**

[docs/auditory_alignment_v3/R_PRIVATE_CALIBRATION_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/R_PRIVATE_CALIBRATION_RESULTS.md)

ALN2 checkpoint重评；正斜率仿射不增加排序/AUC，不保证测试NLL必改善。

**[S12] readout diagnostic**

[docs/auditory_alignment_v2/ITEM3A_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v2/ITEM3A_RESULTS.md)

最终投影/投影前空间分量/全通道探针可分离；更多维度不保证更好。

**[S13] Federici identities**

[docs/auditory_alignment_v3/FEDERICI_REAGGREGATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/FEDERICI_REAGGREGATION_RECEIPT.md)

HC37、CI33、HC-v16独立；phantom一实体九会话；HC-v年龄连接来源等级保留。

**[S14] unit record snapshot**

[results/auditory_alignment_v3/unit_records/README.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/results/auditory_alignment_v3/unit_records/README.md)

6452条快照；公开结果字段和资产存在性；不声称已解包全部。

**[S15] publication receipt**

[docs/GITHUB_PUBLICATION_ALN3.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/GITHUB_PUBLICATION_ALN3.md)

个体级公开此前经研究者批准；当前用户再次确认，既定范围无须再问。

**[S16] source-data acquisition receipt**

[docs/auditory_alignment_v3/PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md)

依server已有下载清单核对SparrKULee，不重申请不重下载；本地未读取原始EEG。

**[S17] science R2**

[docs/auditory_alignment_v3/SCI_R2_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/a3eb744411e79e780c83acf8a5d07be135e8241b/docs/auditory_alignment_v3/SCI_R2_RESULTS.md)

已有共同时间和显式特征分析复用；新增只针对模型变化与适配。

**[P32] ALN3.2 author package**

继承，不以旧状态覆盖新结果；已发布字段的交付规则由当前授权更新。

**[H01] 下一阶段方向设计_2026-10-11**

历史候选文档。只吸收§E3同刺激跨人监督等已明确采纳部分；不采纳私有关闭、阈值关线、预定组差。

**[H02] 项目进展检查_2026-10-10**

历史候选评议。保留强度/内容/时间组织问题；其“只能线性机理”“私有极限案例”等不是执行纪律。

**[U01] current user instruction**

将上一轮分析转成执行包；既定个体级结果公开已确认，不重复询问。
