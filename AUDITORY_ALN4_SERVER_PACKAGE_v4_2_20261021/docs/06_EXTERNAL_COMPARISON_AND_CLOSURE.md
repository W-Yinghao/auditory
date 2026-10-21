# 6. 外部比较与第三轮收束

## 6.1 外部比较要回答的问题

核心的同条件方法证据来自 TCS/TNCE/GCS/B0/wrong；外部席位回答的是：**与现有独立听觉方法相比，这套学习和读出原则在共同听觉应用合同下是否有实际价值。** 外部对手使用自己的已发布架构和输入方式，因此这是系统层面的应用比较，不把架构、预训练数据及输入时长差异归因给 CS。

整个 R3 只占原来一个外部方法席位。先读取 server 在 R1 intake 已保存的 EXTERNAL_SLOT_DECISION.json，记录其 hash、时间、代码 pin、资产和准入结论。已定 fallback 时不重开 MindMix；原决定尚有未完成的工程条件时，按该条件完成一次核验。不能按刚取得的本方法或对手分数换路线。旧决定若缺失，记录 provenance 缺口，并在读取任何新外部 test score 前按下列输入/可恢复性规则冻结；不能追记为 R1 已完成的决定。

## 6.2 两个叫 DTU 的资源必须分清

| 资源 | 原始身份 | 对本次的意义 |
|---|---|---|
| MindMix 论文所引 AAD DTU | Fuglsang et al. 2017；Zenodo 1199011，18人，发布 AUDIO.zip | 论文的被试内5折、2秒任务不能直接当作本项目的44人结果 |
| 本项目 DTU | Fuglsang et al. 2020；Zenodo 3618205，22 HI+22 NH | 官方发布的是 speech envelopes，原语音需要另外取得；server是否已有合法raw audio必须查实 |

不能通过 envelope 上采样构造“16 kHz waveform”，不能因两个数据集都叫 DTU 就转用模型成绩、fold表或刺激ID。这里只核查 server 已有原始资产，不自动联系作者、申请新数据或启动新队列。[1–4]

公共读出代码已经给出本项目的训练单位：aln41/frozen.py 的 DTU content folds 为0/1；aln41/readout.py 的每个 content fold 内循环5个 pooled person folds。每个公共方法因此有 **2×5=10个下游拟合单位**，不是儿童5fold，也不是44人各自5fold。接包时必须逐个绑定原 train people、fit/es/test roles、内容排除及共同 query，不能只复制数字10。[5]

## 6.3 互斥的两条合法路线

### A. 原决定仍指向完整 MindMix，且输入与评分合同可恢复

使用官方已发布 fusion checkpoint，完整恢复 EEG、audio、projection、CALRA；不是 EEG-only 提取。记录实际文件 SHA、完整配置、加载覆盖和排除的任务头。独立 Stage1 资产曾失败，不自动推出这个 fusion checkpoint 失败。

原生输入核验包括200 Hz的2秒 EEG、16 kHz真实语音、通道映射、振幅/参考与频带。使用真实已有 EEG 重新生成所需处理，不能靠低频缓存恢复已经丢失的频带。所有输入访问必须落在允许的训练或 query 物理段内。

作者推荐的 Stage3 路线为 multimodal_real + calra，released fusion initialization；本包固定采用当前公开推荐CLI配方：batch32、50epochs、LR1e−5、wd0.01（当前README训练表/公开CLI）；论文Appendix A.3的batch64、wd0.05等差异必须记录在binding，不追加另一套配方。完整记录实际pinned code的optimizer、scheduler、checkpoint选择和其余默认值；有冲突时说明作者来源和采用值，不能用目标test选一组。[3]

**评分准入必须先于 test 指标。** 当前公开实现中需要核对 target_audio 进入融合及 batch 归一化的行为。用合成候选和训练侧无评分样本验证：

- 评分函数只接收 EEG 和两个未标注候选，真 attended 标记仅在得分后用于评价。
- 交换候选次序后两个分数相应交换；整段预测对物理候选的选择不变。
- 改变 batch 排列、batch size 或加入无关样本不改变同一个样本的候选比较。
- 不把正确声音永远放在 privileged target 槽，再把其高分当盲二选一成功。

允许机械的候选双次调用、顺序对称化和合法单样本分数导出，但必须记录公式与改动；若需要新设计 fusion、损失或以真值挑分支才能满足合同，判定本席位尚不能忠实执行，按已登记 fallback 处理。不能悄悄“修好”作者方法再称原版复现。

本路线使用一个 released fusion checkpoint、下游seed3401，在本项目10个公共训练单位完成作者 Stage3 配方。没有测试人的训练标签，fit/ES数据访问与自有方法相同。每fold使用fit拟合、es按预先登记的作者合法规则选状态；作者没有可直接沿用的选择规则时固定final50，不由test挑epoch。确切选择必须在首次读取新test得分前写入binding。

名称固定为 **MindMix released full architecture, common-protocol task adaptation**。它保留完整多模态系统，但不同于论文被试内2秒协议；不能把它称为作者99.93%结果的复现，也不能用一个本地seed声称全面否定MindMix。

### B. 已登记 fallback：Transformer-CLIP 的原生回归用途

使用官方发布的单模型 EEG encoder 和对应配置，冻结 encoder，按论文的线性卷积读出族预测 envelope。原论文回归使用3秒、64 Hz EEG表征、kernel32的500ms线性读出，以及50% overlap/Hann overlap-add。此支路在目标应用不需要原语音，适合本项目真实存在的 envelope。[4]

这不是把 MindMix 换成同backbone TNCE，也不是声称重现 Transformer-CLIP 的原生20秒AAD；作者论文原任务是 match–mismatch 与 envelope regression。本包名称固定为 **Transformer-CLIP published frozen encoder + native envelope-readout family, adapted to the common AAD protocol**。

接包时完成以下绑定后运行10个读出单位：

1. 选用官方链接预先指定的一个 released model，恢复 args/config、EEG encoder与权重；不挑本项目得分最高的 checkpoint，不额外组成16模型ensemble。
2. 验证64通道名称/顺序/参考/单位，原生3秒与64 Hz处理。不能把3秒压缩成400ms，不能以零填充通道冒称完整空间对应。
3. 读出训练采用可恢复的作者回归配置和实现；若原配置没有公开到可复原程度，固定使用同一线性卷积函数族的训练侧平方误差拟合（带bias，kernel32），采用确定性最小二乘最小范数解，不加新的λ/epoch搜索。该fallback必须标为“native readout family, deterministic LS implementation”，记录与作者优化差异。可用分块QR/SVD或LSMR避免形成巨型design matrix；不以不受控normal-equation逆矩阵替代稳定求解，报告残差/condition。
4. 读出的所有中心化、输入缩放及参数只由对应fit侧估计；ES仅供原固定配置需要的选择或既有tau校准。不得使用outer test儿童/成人标签、features拟合PCA，或给外部方法额外的subject-specific适配。
5. 从3秒预测拼接到既定5秒物理segment，保持原20秒窗口与候选；边界padding与Hann零端点应有显式有效支持mask。若原query部分无法无越界地得到合法预测，先按几何可用性冻结共同有效窗口，并在这些窗口上从已有输出重算所有core3；不根据正确与否筛query。

论文原native读出比本项目三短窗可看到更长上下文，必须在表中披露；这个系统比较不替代同输入TCS/TNCE的因果归因。表征预训练数据与目标/声音内容重叠也必须查证，未知状态保持未知，不默认为无重叠。

## 6.4 共同20秒评价与具体预算

沿用原attention流程：相同5秒物理segment组成相同20秒连续窗口；各窗口的评分按两个候选顺序评价，平分记0.5；每人先在原content folds/合法窗口按原规则汇总，再人口推断。自有core3使用原q0结果，uniform只作为原有描述。

Transformer-CLIP先导出每5秒段 predicted-envelope 对两个候选的相关差，再用原mean-score积分；tau只在原fit/es窗口上拟合。MindMix先导出合法候选margin，其原生2秒子窗须在5秒段内用预先冻结的几何铺法聚合，再走同一20秒mean-score、训练侧tau与双顺序汇总；实际铺法写在结果前的binding中，不搜索窗口偏移。

输出20秒每人accuracy及NLL bits、raw候选margin、有效窗口数、Q哈希及覆盖。5/10秒若可从相同既有margin直接导出，只作描述，不新增选择任务。

比较家族为同一共同Q上的 **external−B0、external−TCS、external−TNCE**，对accuracy和NLL分别保持独立三成员family，使用原person bootstrap-t 4000与原退化处理。NLL注明越低越好，禁止与accuracy反向混读。core3在人内先平均原三个seed；外部是一个固定发布checkpoint及下游seed3401，CI条件于这些模型，不覆盖外部预训练随机性。附上自有方法各seed，不能把不对称seed数解释成外部训练稳定性结论。

| 资源 | 本版上限 |
|---|---:|
| 外部方法/路线 | 1；A/B互斥 |
| 新Stage1/Stage2 source pretraining | 0 |
| 外部下游seed | 仅3401 |
| 公共下游训练单位 | DTU44：2 content folds ×5 person folds=10 |
| A路线encoder FT | 最多10；完整Stage3，不藏在“1个method”里 |
| B路线encoder FT | 0；10个冻结表示线性读出拟合 |
| 新儿童外部FT、FAU外部任务、ensemble、外部HPO | 0 |
| 可选方法消融 | 未启用 |

这替代草案中不适合实际公共fold结构的“总3次optimizer run”计数。原R3允许一个外部席位和有限下游训练，本版明确为这10个共同公共单位；不同时运行两条路线，不占用未启用的消融预算。中途已完成合法外部路线后不得因分数弱再转另一方法。

先对一个固定fit单元测内存/耗时，登记10单位成本和队列；不以估计时间代替资源账本。若真实资产/输入不能忠实恢复，交付具体失败证据与已核定可行的fallback；两条均有实质阻塞时关闭本轮执行并明确“外部比较尚缺”，不能写成论文已满足外部验证。

## 6.5 R3 的科学结束条件

R3依次回答：公共学习是否添加刺激相关判别依据；时间读出是否可复用；个人δ是否胜过普通校准；儿童是否支持跨刺激读出与独立发展信息；外部方法比较把应用表现放在什么位置。

结束研究轮次不等于宣称PR投稿条件自动满足。如果额外方法价值仍没有成立，应明确“目前不足以支持所拟方法贡献”，保留所有有效科学结果，进入写作/选题取舍；不通过另开第四轮或换终点挽救预定结论。

## Primary sources 与本项目依据

1. MindMix正式论文，§4及Appendix A：https://proceedings.iclr.cc/paper_files/paper/2026/file/b0ae046e198a5e43141519868a959c74-Paper-Conference.pdf
2. DTU18数据：https://zenodo.org/records/1199011；DTU44数据：https://zenodo.org/records/3618205 （Audio段）。
3. MindMix官方README与原实现：https://github.com/CookieMikeLiu/MindMix；universal_eeg_finetune.py、universal_models.py、universal_trainer.py。原资产审计pin为98445f368efcb161c638172501bd16f92d09a89d；server实际采用pin必须记录，不随main变化。
4. Bollens et al. 2025，Regression/Finetuning：https://pmc.ncbi.nlm.nih.gov/articles/PMC12329020/；官方模型/代码：https://github.com/exporl/transformer-clip-eeg。
5. 本项目固定基准：https://github.com/W-Yinghao/auditory/blob/5d2960eee61a75c048f6b6ee3cef8427d945c3cd/auditory_alignment_v3/aln41/frozen.py；同目录readout.py。所有上列网站核阅于2026-10-21；这不替代server的实际完整资产加载验证。

