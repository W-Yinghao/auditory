# 项目阶段性研究评估 — 2026-10-17，18:54更新

**主线值得继续，ALN3.4尚未全部完成。** 当前最充分的依据是有效CBraMod/local的匹配结果，以及个人适配随支持量改变的真实风险。应继续区分优化预算、数据量、可迁移结构和适配参数量；原样重复旧fixed-grid/prefix配置和旧融合配方，新增信息很有限。这里不把已提交、工程探针通过或donor开发曲线当作完整实验结果。

本更新取代[之前的阶段评估](PROJECT_PROGRESS_REVIEW_20261017.md)中的执行状态；早期快照保留。训练计数依据18:51证据汇总；首个强融合和episode单元的描述性检查、CS episode补充登记已加入。旧Claude已由研究者确认停止；本轮使用Slurm，所有GPU任务使用runfill，运行上限10。没有用seed、fold或job扩大独立人数。

## 整个项目已经走到哪里

| 阶段 | 已有进展与更正 | 当前含义 |
|---|---|---|
| 私有审计、临床增量和目标修复 | 身份/事件/临床键核查、PTA行键和正则尺度修复完成；修正后尚未建立已有临床量表上的稳定EEG增量。 | 早期错误比较不能作生理证据；当前声音、历史和发育问题仍开放。 |
| D1/D2连续EEG | 稳定个体信息、年龄读出及通道/时长预算有跨划分结果；单划分“饱和”曾被纠正。 | 约2分钟、16个嵌套选择电极的发现限于对应设计；年龄可读性不等于听觉治疗效果。 |
| ST/GX/PF/DV/NEXTMAP/STORY | 小幅跨儿童声音读出、部分同队列年龄信息；跨系统迁移及历史/临床增量仍有限。GX“无年龄”旧说法已撤回。 | 反复使用同一批儿童必须披露，新seed不能成为外部验证。 |
| C3、传统核CS、ALN2 | 公共数据、声音属性参照、NCE/核CS/FMCA及注意/迁移比较已建立；FM通道均值读出修正完成。 | 条件预测增量不能换算成语言信息比例或因果机制。 |
| ALN3–ALN3.2 | 空间身份/实际时间访问、固定patch接口定位、aligned、同访问local、真全量更新和融合对照。 | 旧接口的弱结果不能推广到新接口；初始化、优化配方和访问范围必须分开。 |
| ALN3.4已完成分析 | D多seed、293个注意模型顺序修正、200个D_ADAPT真风险、64儿童E面板；234个非零epoch融合功能评估及16个零点检查；120个私有校准干预；44听者原始滤波对照。 | 已将评分顺序、真实风险、概率校准、滤波时间组织分成可核验的问题。 |
| ALN3.4仍在执行 | TRUE_FULL709/800；公共先验4/1,154个新单元完成，均在donor阶段；19个GPU实验/评估计划进入21条调度队列，另有已完成的滤波CPU计划。 | 多数新比较还没有完整配对结果，登记数不是科学完成数。 |

详细历史和证据路径见[交接文档](../CODEX_HANDOFF.md)§1、[full-update更正](auditory_alignment_v3/CORRECTION_01_FULL_UPDATE_LABEL.md)和[私有配方更正](auditory_alignment_v3/CORRECTION_02_PRIVATE_RECIPE_SCOPE.md)。

## 证据、解释和下一干预

**CBraMod有效配方值得继续，但优势来源还需区分。** DTU44名听者完成3seed配对后，真全量3e-4预训练CB相对同访问L1的统一真实风险改善为+0.213bits/5s查询，同时区间[+0.129,+0.297]；随机CB相对L1为+0.013，区间跨零。另一预先说明的六对比预算参照族，直接预训练对随机差为+0.1997[+0.1290,+0.2705]。后者复用了原训练，不是新增长预算效果。FAU共同配对仍为56/67；Federici追加seed尚无完整共同覆盖。REVE随队列和native/unified读出而变化，因此继续保留代表对照。见[配对证据](auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md)、[学习证据](auditory_alignment_v3/PRETRAINING_LEARNING_EVIDENCE.md)。

下一干预已经登记并运行：完整双倍预算、固定轨迹、同配方初始化对照，分别减少训练人数或声音内容量。若随机追上，解释转向优化/样本效率；若仍有配对差异，再结合数据量与迁移判断范围。长预算中途checkpoint与原短预算的学习率日程不同，不能当作完全相同的训练前缀。已有数据量曲线固定epoch，实际步数随数据量变化；它回答的是该训练预算规则下的联合变化，不能单独归因于数据量。全数据双倍预算也不能替代各缩减子集的固定步数比较；这项解释边界继续保留。

**适配有可利用作用，也有重复出现的伤害。** 三seed下，input_spatial在FAU的10%/30%支持对应统一风险改善+0.093/+0.250bits/query；DTU为−0.208/+0.150，小支持伤害也出现在native风险。完整矩阵参数量及将30%支持选择用于10%支持，是具体的竞争解释。新D分别开发各支持量，对比对角、rank4、全矩阵、输出rank4和短时滤波，保留0步；普通与episode训练按更新数配对。见[真实风险](auditory_alignment_v3/D_ADAPT_TRUE_RISK_RESULTS.md)。

首个完整episode bundle（CBpre、DTU seed3401、personfold0/contentfold0，10名外层听者）已经审查：两条路径各100次编码器更新、300次支持梯度步、6,400查询锚点。内层在10%支持选5步、30%选20步，episode相对ordinary的native真实风险改善仅−9.01×10⁻⁵/−7.64×10⁻⁵bits/query，unified为−2.95×10⁻⁶/−2.22×10⁻⁵；两种选定续训的外层风险都略差于原源模型。后续权重审查显示两条更新方向cosine约0.99998，二者差异范数仅相当于ordinary更新的0.59%（inner）/0.68%（outer）。这是这次干预接近普通续训的证据，权重范数本身不证明功能等价，也不能推广成episode方法无效。当前完成既定面板并检查功能差异，不追加同一弱干预配方的重复；不会用外层结果改选回基线。见[风险诊断](auditory_alignment_v3/FIRST_EPISODE_DIAGNOSTIC.md)及[权重诊断](auditory_alignment_v3/FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md)。

**注意整合的旧劣势部分来自候选顺序。** 293个模型按原记录设备重评分后，成对交换及反对称评分修正了此前判读。新的冻结源注意迁移比较5/10/20秒证据窗口和内层留人选择；证据累积时长不是神经潜伏期，5秒单段也不等于多段整合。见[顺序更正](auditory_alignment_v3/ATTENTION_ORDER_CORRECTION.md)。

**旧融合改变了预测，却没有因此获得风险收益。** DTU CS–CB残差归一化后的平均方向变化约17.44°，unified rank变化82.1%，真实风险增量−0.0210bits/query；“只改变幅度”不能概括其失败。新的强模型融合保留direct local、strong standalone FM和epoch0，采用整条流程的内层留人开发。原样重复旧融合不再有足够价值。见[功能解读](auditory_alignment_v3/COMPLEMENT_FUNCTION_FINAL_INTERPRETATION.md)。

首个返回的强融合单元（按完成顺序查看，10名外层听者、单一fold/content/seed）中，三个残差策略均由内层选择0步；原生共同线性融合相对内层选定强CB单模型的风险改善为−0.602/−0.632/−0.595bits/query。CB预训练概率融合有+0.0794 native、+0.0277 unified的描述性改善；REVE概率融合为+0.0196/+0.0368。全部候选已保存，这些不是完整人群/多seed推断。该返回支持继续完成既定低复杂度概率融合对照，并继续降低无收益残差配方的追加优先级；不因此停掉尚未完成的配对面板。见[首个返回诊断](auditory_alignment_v3/FIRST_STRONG_FUSION_DIAGNOSTIC.md)。18:40自动汇总随后已覆盖该外折两个内容折的10/44名听者（仅seed3401）：CB概率融合相对strong single的unified改善+0.0900[+0.0044,+0.1757]，native为+0.0574[−0.0106,+0.1255]。这是尚未齐全的人群/seed面板，区间条件于已拟合模型，不能作为全队列确认或提前选方法的依据。

**私有儿童任务仍是当前声音、历史和适配问题，校准诊断不能取代它。** 64儿童的完整E面板里，GX原生当前类别AUC在三seed为0.553/0.552/0.555，但其历史背景以上增量为−0.0081bits/trial，点估计及区间均不支持正增量；其他面板配置也尚无高于历史基线的正增量证据。旧公共迁移配方相对local的AUC增量NCE约+0.004、CS约0，区间都跨零。当前类别可读性与历史之外的独立预测收益是两个问题。继续完成已登记的匹配初始化、独立公共听觉先验、private episode和时间/history比较，保留GX/local原生对照；不通过增加相同配方seed把内部重复称为新儿童证据，也不据此断言所有儿童听觉建模无效。见[完整E面板](auditory_alignment_v3/E_MULTI_SEED_RESULTS.md)。

**私有校准异常已得到冻结权重干预支持。** 120/120checkpoint、64儿童、3seed完整配对后，去掉校准trial自身核参考项，相对原正仿射校准的NLL变化分别为：REVE random_full −0.038649[−0.041747,−0.035550]、pretrained_peft −0.135854[−0.143959,−0.127750]、pretrained_full −0.006742[−0.009266,−0.004218]bits/trial。区间来自每端点16对比同时族。与原class-kernel的差接近零，每次重跑内AUC完全不变。该干预解释了此前几乎全部校准损失，但同儿童其他trial参考仍在；这不是新儿童校准验证，也没有建立临床/history增量。已将同一问题延伸到90个新先验私有CS主checkpoint，训练与选模保持原样。见[完整校准干预](auditory_alignment_v3/PRIVATE_CALIBRATION_LOO_RESULTS.md)。

**时间峰对滤波敏感。** 原始DTU的44听者、5人折×2内容折已全部完成。幅频响应匹配的两种滤波，在+200ms处的因果减零相位r为−0.03832[−0.05139,−0.02526]（0.5s边界保护）和−0.03584[−0.04907,−0.02262]（2s）；−200ms差异为−0.00095和−0.00089，区间均跨零。因果滤波延迟没有补偿，整段无监督归一化仍保留，不能称整条流程在线因果。HI–NH直接干预差的同时区间均跨零，也不等于组间效应相同。该敏感性已回答当前问题，不再为寻找好看的峰追加时间网格；继续既定内容、history、完整时间矩阵和适配分析。见[滤波报告及图](auditory_alignment_v3/CAUSAL_FILTER_BOUNDARY_RESULTS.md)。

## 实际执行进度

| 实验/评估 | 已登记范围 | 当前状态 |
|---|---|---|
| 预算与训练数据量 | DTU预算150、数据量/内层源590；FAU/Federici预算75、数据/内层375 | DTU预算3、数据/内层29完成；breadth内层/D/融合/episode探针通过，预算探针仍运行 |
| 受限适配和episode | DTU D120/episode80bundle；FAU D40/episode40；私有episode50 | D2个、DTU episode1个完成；私有episode探针通过；其余生产按依赖排队 |
| 强融合 | DTU30、FAU/Federici15bundle | DTU2个完成；首个返回单元仅作描述性诊断，breadth融合探针通过 |
| 公共local CS episode | DTU30+FAU10，复用同一NCE源，普通/episode各100步 | 5项CPU测试及汇总检查通过，计划冻结；GPU探针1044393排队 |
| 公共听觉先验 | 1,154个新单元，另有30历史私有参照被分析复用 | 4个donor组完成、4GPU worker运行；尚无目标迁移效果 |
| 通用→听觉→目标CB | 9donor+135target，generic/random/wrong-pair匹配 | GPU探针通过，生产排队 |
| Native内容/时间/私有科学 | 公共180、私有130个冻结模型评估 | GPU探针通过，生产排队；原始滤波对照已完成 |
| 新先验科学分析 | S/AP/XP/J*/XM，NCE/CS，代表seed3401，共300个冻结主checkpoint | 4项测试及汇总检查通过，GPU探针1044347排队；源模型齐备后评估 |
| 先验私有CS校准 | 90个主checkpoint，严格复现原评分后去自身参考 | CPU检查通过，GPU探针1044337排队 |
| 私有初始化×学习率 | NCE/CS各自交叉，3seed×5fold；60原单元+60新增 | GPU探针1044280通过，初始化/随机数/目标头匹配已核验；生产1044385排队 |
| 冻结源注意迁移 | DTU120+FAU40，内层开发和全部固定策略 | CPU检查通过，GPU探针1044250依赖breadth源探针 |

新先验科学首版公共分析使用已映射的env/onset/history，私有使用准确64Hz/0–578.125ms输入及3×3时间泛化，不虚构刺激前窗口。尚未映射的Ac/Lz/spec不冒充已实现；该代表seed面板也不冒称3seed科学复现。Native模型科学首版以NCE为主。私有episode已有local NCE/CS，另按任务卡补齐了公共local CS续训对照：DTU三seed、FAU seed3401，共40bundle。普通CS与episode-CS从同一NCE源起步、相同支持计算和查询样本，带宽只用源训练fit数据；这不是从头CS训练，也不扩成交叉所有主干/损失/rank。原NCE比较保留，跨目标只将统一读出比较称为续训配方对比，native接口不同不会被隐去。见[CS设计](../private/auditory_alignment_v3/aln34/CS_EPISODE_DESIGN_20261017.md)与[执行结果](auditory_alignment_v3/CS_EPISODE_RESULTS.md)。

F0/voicing是原包的可选扩展。FAU波形及DTU既有3,520条波形路径已确认可用，当前优先完成上述登记比较；没有将其写成完成或数据缺失。Federici2–8Hz缓存不能恢复缺失频带。小NH/早期验配分层、反复使用同一批儿童和缺少外部独立验证，仍限制临床与发育解释，但不构成停止当前任务研究的结论。

## 交付与剩余工作

FIXC、rich PCA重拟合、生产core/rich manifest、M12脚本及真实GPU运行、M13记录均已完成。D/E、注意修正、真实风险、公共先验实现/缓存/manifest已经进入交接。见[公共先验执行状态](auditory_alignment_v3/PUBLIC_PRIOR_EXECUTION_STATUS.md)、[内容/时间/人群报告](auditory_alignment_v3/HEARING_CONTENT_TIME_ADAPTATION.md)。

18:36队列保持10个运行、12个等待的项目GPU作业。协调器v12（1044397）和证据服务v9（1044399）独立运行，按工程回执、真实依赖和完整单位返回补队/汇总；TRUE_FULL800齐备后核验冻结文件并执行ADDENDUM_11。没有使用scontrol。

1,002个旧执行保留暂停，A3c删除仍暂缓；没有删除源数据或checkpoint，没有新增外部联系，也没有擅自push。正在训练、尚未运行的工程探针及真实源依赖仍是未完成项。后续判断依据完整身份配对、真实风险和比较的判别能力，不依据有利seed、组内显著性或最早返回的单元。最新执行状态见[完成清单](../private/auditory_alignment_v3/aln34/COMPLETION_LEDGER_20261017.md)与[交接文档](../CODEX_HANDOFF.md)。
