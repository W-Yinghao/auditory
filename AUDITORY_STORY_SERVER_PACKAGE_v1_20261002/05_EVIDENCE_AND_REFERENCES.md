# 来源、既有证据与本版新增设计

## 1. 固定版本

本次实际读取GitHub默认分支最新提交为`558e6509d64e0decb4d796ee51964f7ff6a30ee2`，主体NEXTMAP内容为其父提交`961edeaa4e5940449fc364db0779e3e7ca62cc96`。未修改仓库，未启动真实数据训练。

所有新SRP公式、label budget、SIR主／MUSS次次序、原型代码及预算属于本版候选设计。历史结果只能说明已有资产与风险，不证明新方法有效。

## 2. 用户材料

- **S1**：《AUDITORY_PROJECT_MAP_v1_20261002_558e650.md》。主要使用§2数据对象、§5年龄边界、§7SIR概率、§9更正链。它是已有分析汇总，不是独立患者复算。
- **S2**：《发散_解码视角的候选方向.md》§1“导师约束”（原文件第39–45行）：儿童、HA、SI，解码提供不同视角，多候选按实验收敛。本版继承这些目标，不继承其全部判据。
- **S3**：《新结果分析_PF_PF2_DV.md》§5（第111–126行）提出成熟度、经验签名与病历决定结局的故事。本版明确不把这些候选解释作为既定事实；后续概率和年龄分析已要求收窄。
- **S4**：《未用数据发散_标签复原与队列扩张.md》§0、§3（第5、44–65行）提出“已用尽”“可找回新队列与声调”等预期。后续NEXTMAP未支持原扩样数量，本版不再将其作为必需数据来源。
- **S5**：《深挖计划_验配起点的两阶段偏差反应.md》第7–9行的补充确认：HA佩戴记录、NH分开。采用确认的范围，不自行推定设备输出或问卷日期。
- **S6**：上一轮用户与助手对story-first研究顺序的讨论。本包以低标注功能学习为主候选，个体响应评估为独立竞争候选。既有技术发散降为必要基线／消融，不作为论文标题。

服务器无需重读所有S2–S5，除非某个具体来源有冲突；它们记录思想演变，不应覆盖最新数据回执。

## 3. 仓库来源（固定SHA）

- **R1** [NEXTMAP年龄信息来源](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_nextmap/AGE_INFORMATION_SOURCE_REPORT.md)：冻结刺激表示与不同聚合／参照。
- **R2** [SIR预测余量](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_nextmap/SIR_PREDICTIVE_HEADROOM_REPORT.md)：55人五级分布、强临床排序、CE与概率来源。
- **R3** [PF结果](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_pf/PF_RESULTS.md)；[PF2结果](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_pf/PF2_RESULTS.md)：阶段、个体响应和临床主张的既有边界。
- **R4** [MFF语义恢复](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_nextmap/SEMANTIC_RECOVERY_REPORT.md)：未知任务、8条恢复声音对与限制。
- **R5** [净新增队列](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_nextmap/NET_COHORT_ADDITIONS.md)：身份、曝光、SET与BDF时钟。
- **R6** [NEXTMAP配置](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/configs/auditory_nextmap_v1.yaml)：本次直接读取的数据绑定、runfill与GPU约束。
- **R7** [已存在的适配函数](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/auditory_nextmap/adapters.py)：本次直接读取的Cohort、同编码器导出与私有文件入口。
- **R8** [K1校正](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_k1/CORRECTED_OBJECTIVE_REPORT.md)：不能将实现退化当作EEG无用，也不能将修复当作临床增益。
- **R9** [H系列](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/auditory_nextmap/H_SERIES_REPORT.md)：组合谱、跨系统和预算结果。
- **R10** [发布回执](https://github.com/W-Yinghao/auditory/blob/558e6509d64e0decb4d796ee51964f7ff6a30ee2/docs/GITHUB_PUBLICATION_NEXTMAP.md)：私有数据范围、已公开聚合产物。

本次新核对为版本、配置与适配代码；其他详细历史数值使用上轮Map及已提供报告，不声称本次逐项重新运行或重新核算。

## 4. 外部方法与期刊来源（本版检索）

- **L1** IEEE EMBS, [JBHI scope](https://www.embs.org/jbhi/articles/jbhi/)。仅支持信息技术与健康/生物医学交叉的期刊定位，不保证本研究可录用。
- **L2** Garnelo et al. (2018), [Conditional Neural Processes](https://proceedings.mlr.press/v80/garnelo18a.html), ICML/PMLR 80:1704–1713。支持/查询函数预测已有方法；本SRP需明确承认这个近邻。
- **L3** Garnelo et al. (2018), [Neural Processes](https://arxiv.org/abs/1807.01622)。神经潜变量分布模型不是本版原创。
- **L4** Zaheer et al. (2017), [Deep Sets](https://proceedings.neurips.cc/paper/2017/hash/f22e4747da1aa27e363d86d40ff442fe-Abstract.html)。置换不变集合编码的已有基础。
- **L5** Szabó et al. (2016), [Learning Theory for Distribution Regression](https://www.jmlr.org/beta/papers/v17/14-510.html), JMLR 17(152):1–40。两阶段采样与集合回归已有理论；不直接把其独立性假设移到相关EEG试次。
- **L6** Geirnaert, Francart & Bertrand (2022), [Time-Adaptive Unsupervised Auditory Attention Decoding Using EEG-Based Stimulus Reconstruction](https://pubmed.ncbi.nlm.nih.gov/35344501/), IEEE JBHI 26(8):3767–3778, DOI 10.1109/JBHI.2022.3162760。参考其从使用障碍到方法验证的组织方式；任务不是本项目的儿童档案功能。
- **L7** Banville et al., [Uncovering the structure of clinical EEG signals with self-supervised learning](https://arxiv.org/abs/2007.16104)。低标签EEG收益与年龄相关嵌入已有先例；不能只以发现这些现象主张首创。

本次仅检索最接近的方法族与期刊定位，未完成儿童听觉功能表示学习的穷尽新颖性综述。没有使用搜索结果替代私有队列事实，也没有把外部论文的性能或伦理许可转移到本研究。
