# 来源索引与证据等级

核查HEAD：`9b9e03eb229b93c357f6d222a93ba354deb85b06`。本包中的事实、推论、合成验证和新实验分别标注；不声称读取服务器私有结果。

- **S01** [README.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/README.md)：发布时进度；B_ALIGNED已启动、尚无结果；不是实时队列。
- **S02** [docs/auditory_alignment_v3/BC_PROBE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_PROBE_RESULTS.md)：P5输入路径与P6对齐token探针；主要是训练参与者内的留出内容，不是完整泛化结果。
- **S03** [docs/auditory_alignment_v3/BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_PROBE_PLAN_03_ALIGNED_TOKENS_20261014.md)：P6定义；aligned单patch与固定网格选中token的区别；记录原先启发式判读而不继承绩效门槛。
- **S04** [docs/auditory_alignment_v3/ADDENDUM_06_B_ALIGNED.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/ADDENDUM_06_B_ALIGNED.md)：已冻结的250行、输入[-0.4,+0.6)秒、线性读出、继承训练配方。
- **S05** [auditory_alignment_v3/fm_aligned.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_aligned.py)：aligned_windows、AlignedFM、fit_aligned、实际解冻与评价路径。
- **S06** [auditory_alignment_v3/fm_dense.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_dense.py)：epoch、warm-up、逐步解冻、LLRD与学习率常量。
- **S07** [auditory_alignment_v2/foundation_adapter.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v2/foundation_adapter.py)：backbone参数分组、CBraMod 12块、REVE 22块及patch输入；之前已核查实现。
- **S08** [docs/auditory_alignment_v3/IMPLEMENTATION_RECEIPT.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/IMPLEMENTATION_RECEIPT.md)：暂停范围与B_ALIGNED放行回执；旧hash不改。
- **S09** [docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/B_DENSE_READOUT_RESULTS.md)：上一批1000个B单元的seed3401完整比较；不是B_ALIGNED结果。
- **S10** [docs/auditory_alignment_v3/C_COMPLEMENT_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/C_COMPLEMENT_RESULTS.md)：650个C/容量对照的seed3401比较。
- **S11** [docs/auditory_alignment_v3/BC_INTERIM_QC_NOTES.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/BC_INTERIM_QC_NOTES.md)：C缺epoch0、内容验证未识别跨人退化、dense时间路径等已见问题。
- **S12** [auditory_alignment_v3/fm_complement.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/fm_complement.py)：旧残差分支与选择；全部分支共用dense上下文读出，不归因单一FM。
- **S13** [auditory_alignment_v3/aln3_reference/readouts.py](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/auditory_alignment_v3/aln3_reference/readouts.py)：query显式时间路径与通道投影；不随q恒定不等于依赖正确EEG。
- **S14** [docs/auditory_alignment_v3/SCI_R1_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_R1_RESULTS.md)：已完成SCI_R1；time/group结果及限制。
- **S15** [docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md)：原有seed角色与账本继承，不全量再乘三。
- **S16** [docs/auditory_alignment_v3/SCI_FEATURE_INCREMENT.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_FEATURE_INCREMENT.md)：S2显式声音特征增量尚未完成。
- **S17** [docs/auditory_alignment_v3/SCI_R1_PREREG.md](https://github.com/W-Yinghao/auditory/blob/9b9e03eb229b93c357f6d222a93ba354deb85b06/docs/auditory_alignment_v3/SCI_R1_PREREG.md)：各队列时间支持、身份、probe/calibration范围。

## 外部原始来源

- **E01** [SparrKULee原始论文](https://www.mdpi.com/2306-5729/9/8/94)：85名参与者、168小时EEG。
- **E02** [NEMAR发布页](https://nemar.org/dataset/nm000238)：镜像列出80名，另5名受限；不能将85写成已获取样本数。
- **E03** [Défossez et al., 2023](https://www.nature.com/articles/s42256-023-00714-5)：群体共享声音解码与预训练声音表示的先例。

## 旧包

ALN3.1上传附件为兼容基准。只继承没有被本包明确更正的工作；原始zip不改写。文件hash见`reports/INPUT_PROVENANCE.json`。

这两份2026-10-10/11的候选分析是历史资源，不是当前指令：其中“私有oddball停止所有新模型”“任何gain≤log2K”“CI差距缩小才算去伪迹成功”“自动改写边界稿”不采纳。
