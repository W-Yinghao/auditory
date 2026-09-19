# Auditory FN1：临床对象落实与一次记录级功能学习

**版本：** FN1 v1.0  
**日期：** 2026-09-19  
**依据仓库：** `W-Yinghao/auditory`  
**已核对基线提交：** `493a076a3848d3546a5889e2c583d0fee2ba1612`（2026-09-19 00:45，巴黎时间）  
**文件性质：** 下一轮研究判断、分阶段执行规范及服务器代理指令；不是已执行的实验报告。  
**目标：** EEG 解码、记录级表征学习与临床条件信息。暂不承诺 JBHI 方法优势或临床效度。

---

## 0. 本轮决定：不继续修补旧问题，也不立即全面重训

本轮只保留一个候选科学问题：

> **当临床目标与 EEG 的对应关系明确后，直接围绕功能目标学习记录内 EEG 片段的聚合，是否优于先把片段压成固定统计再预测功能？这种收益是否超出合理临床基线和采集过程摘要？**

这不是再做刺激分类、刺激头零空间或 ERP 峰值分析。它也不是给现有 Hjorth 特征加几个回归器。真正的新比较是：**对同一组片段、同一组局部特征、同一临床目标及近似相同参数量，改变学习与汇总的顺序。**

本轮分成两个明确阶段：

| 阶段 | 现在允许做什么 | 不允许做什么 |
|---|---|---|
| **W0：对象与资料落实** | 复用已核验结果，形成一次性临床核对包；实现小型模型接口和有限合成测试；处理实际收到的新证据 | 重扫已确认缺失的资料、重训旧 D、再跑档案特征大矩阵、自动向外发送临床资料 |
| **W1：条件化的唯一新实验** | 仅在临床对象、信号来源及本轮分析范围锁定后，执行本文规定的有限记录级模型矩阵 | 用未知日期或混合版本自动启动；按小正值扩架构、换终点、追加种子；把档案关联改称临床验证 |

**当前起始状态：`W0_READY / W1_BLOCKED_CLINICAL_LOCK`。** 最新资料仍没有充分确证逐行量表归属及 EEG—量表时间关系；因此，本文件不把 W1 写成可以立即执行的 GPU 作业。[R1–R3]

若本轮没有收到能够改变资格的新证据，正确交付是：**资料缺口已送达研究者、候选实验已准备、真实学习未启动。** 不把这种状态写成科学阴性，也不另起一个“放宽解释的档案训练”绕过它。

本轮不设置显著性或最小效应大小作为剩余实验的执行开关。W1 一旦合法启动，规定模型与对照全部完成并保留，无论早期结果正负。支持、数据完整性、数值安全和资源限制仍是执行边界。

---

## 1. 本轮依据：哪些认识已经改变

### 1.1 PTA 修正必须进入所有新来源链

旧 `C####` 关联曾把非空记录顺序与实际工作表行号混用。57 条比较中，55 条较好耳裸耳 PTA、47 条助听 PTA 改变。旧 Phase 3 的 PTA 调整结果不能继续作为当前数值依据。[R4]

本轮继承已经修正的实际源行关联和已完成回放，不重新拟合历史模型。需要区分：

- 原 50 人、原折的 Phase 3 修正回放；
- 原 51 人、原折、旧范围表征的 D 修正回放；
- 新 52 人、新划分、40 个新编码器的完整 D 重训。

三个分析对象不同，不合并成“PTA 修复后的一个结果”。37/60 个外层身份组换折，不等于发现身份泄漏；它说明支持变化会传播到平衡划分。新任务必须使用自身明确的身份划分，不能因为缓存方便而复用不合规表征。[R4–R6]

### 1.2 最新完整重训不是直接的 F1/F2 功能学习

最新重训仍以刺激监督／SimCLR 表征及刺激头可见、null 分解预测 MUSS。它修复了历史依赖，但没有检验“以儿童级功能损失学习片段集合”的新问题。[R5–R6]

主要 R_SIM null 增益约 +0.020，固定 OOF 区间跨零；完整联合模型仍比纯临床基线差约 0.094。监督可见方向的小正值没有为 null 路线提供新依据。**不再追加该路线。**[R5–R6]

### 1.3 现有 F-series 线索只允许保留，不允许直接升级

57 组档案分析中，已知听觉列 A 时预测 MUSS 的联合 EEG 增益约 +0.289，区间约 [0.010, 0.583]；技术摘要基线约有 +0.572 的改善，继续加入 EEG 则约 −0.591。它是控制敏感的探索线索，不是已分离的听觉／言语神经功能。[R7]

Hjorth 与空间统计的采集内重复性较高，不自动代表功能效度。可靠性和临床增量不能互相背书。[R7]

### 1.4 量表定义并非全部缺失

原文档确有 IT-MAIS、CAP-II、MUSS、SIR 的计分说明。问题主要是具体临床行适用哪个版本，以及问卷日期与 EEG 的关系。不能继续向采集团队笼统索取“所有量表定义”，也不能因文档有定义而替所有行自动指定版本。[R2–R3]

### 1.5 当前范围是 HA，不是 CI 的临床外部验证

混合 MFF 档案模型的大多数来源组别未知；目前不能称为 CI 验证。F3 的跨任务＋临床交集、F4 的真实问卷随访都不足。本轮不重开这些任务，也不把 NH 小样本并入 HA 回归以增加人数。[R2,R7]

---

## 2. 本轮不再研究什么

明确关闭：

1. 事件码分类、run-length 解码、背景钥匙、左右互补、PCA 截断、匹配袋方差的旧迭代链。
2. 固定刺激头可见／null 分解、重复 MUSS 回归及其新种子扩展。
3. 再比较五个旧固定特征库和五个量表以寻找阳性。
4. F3/F4 的跨任务或纵向模型；没有真实关系，不以复杂模型填补。
5. 大型基础模型、Mamba/HFMCA 强制复用、全套自监督方法竞赛。
6. 为补全状态表而反复运行测试、全库哈希、失败已解释的模型或历史报告。

代码与读入器可以复用；科学任务和模型权重不自动复用。尤其不能把旧刺激编码器微调几轮后，宣称这是本轮新的直接功能目标比较。

---

## 3. W0：一次性临床核对包，不再做无边界审计

### 3.1 W0 的主要产物

研究者需要获得三个简明产物：

- **事实与问题对照表**：已经明确的字段不再提问；只列会改变当前研究对象的缺口。
- **受限的待确认记录表**：供有权限的临床团队核对，不上传 GitHub，不附 EEG、模型结果或“哪一行增益最大”。
- **临床回复导入模板**：把实际回复绑定到来源行或明确适用的批次规则；无回复仍记 unknown。

优先核对目前已审计的 HA 候选记录。57 组档案支持和 52 组 D 支持只是导航，不强制成为新队列。W0 只定向处理相关来源，不扩扫 203 个 MFF。

### 3.2 只问四类会影响决定的问题

| 问题 | 已知内容 | 真正需要补的内容 | 能否用模型替代？ |
|---|---|---|---|
| **目标身份** | HA 表有听觉列与 MUSS 数值 | 听觉列哪些行属于 IT-MAIS、哪些属于 MAIS；使用版本及该年龄范围的适用解释 | 不能 |
| **时间关系** | EEG 有采集时间；表格有标签日期 | 标签日期是否确指问卷；是否同一次临床评估；若非同次，实际评估日期或可证实区间 | 不能 |
| **身份与来源** | 候选身份及工作表行关联已审计 | 有无已知错人、重复导出或访问混淆；只处理当前未解冲突 | 不能 |
| **阈值与设备背景** | 裸耳／助听四频数据存在，PTA 行键已修正 | 单位、评估所处条件；采集是否佩戴／开启设备，是否有中途变化记录 | 不能；但部分未知可限定结论，而非一律排除 |

可以接受有范围和出处的**批次级说明**，例如“这份问卷表的某一批原始行均为同次门诊评估、均用同一版本”；不强求每人另找一张纸。但必须记录说明者、原始依据、适用行范围、例外和不确定性。不能接受由分析人员根据年龄或分数猜出的批次规则。

### 3.3 时间资格：不随意指定 30 天或 90 天窗口

本轮默认主要分析只接受以下之一：

- 有来源证据的同次访问／同次评估；
- 有明确日期或日期区间，并由临床负责人在查看新 EEG 关联前确认适用于本研究目标的时间范围及例外。

没有时间证据时不自动设为零间隔。若采用第二项，`time_window_rule`、其依据及重要临床事件处理必须写入锁文件；本稿不虚构医学上有效的时间容差。

**设备开启状态未知不自动成为 F1 关联任务的普遍排除项。** 应保留 unknown，禁止设备获益或条件因果解释；若有已知中途设备变化，则按预定规则分段或排除该次主分析，不按模型成绩选择片段。

**PTA 日期缺失与问卷日期缺失分开。** 前者可能使结论限于“超出已记录的临床变量”，不能称超出同期完整可听度；后者直接影响本次功能目标是否有明确时间意义。

### 3.4 私有确认表 schema

```text
candidate_key
source_workbook_sha256
source_sheet
source_row_number
clinical_link_key
visit_key
identity_status                 # confirmed / supported_candidate / conflict
outcome_role                    # auditory / speech
instrument_literal
instrument_resolved             # IT_MAIS / MAIS / MUSS / UNKNOWN
score_unit_resolved
version_evidence_ref
age_applicability_note
assessment_date_or_interval     # 仅 private
assessment_time_role            # questionnaire / EEG_only / UNKNOWN
eeg_visit_relation              # same_visit / dated_interval / UNKNOWN
time_evidence_ref
cohort_rule_id                   # 批次说明适用时填写
clinical_interval_event_flag
pta_unit_and_condition_status
recording_device_state          # ON / OFF / WORN_POWER_UNKNOWN / UNKNOWN
resolver_role
confirmation_evidence_ref
resolution_status
```

表中可以有 unknown，不得用空字符串在后续自动转换成 confirmed。公共报告只发布计数、排除原因和规则，不发布姓名、日期、逐人分数、身份键或原始位置。

### 3.5 给临床团队的消息草稿

> 我们已完成 EEG 与临床表的重新关联，并修正了历史 PTA 行号问题。下一步不再继续声音分类，而是评估 EEG 是否能补充儿童的日常听觉功能。现在主要需要确认：表中 IT-MAIS/MAIS 每批记录实际使用的版本及适用范围；问卷是否与 EEG 属同一次评估、表内日期具体指什么；以及听力阈值和设备条件的已知记录。原说明文档中的计分规则已经找到，不需要重新准备全部量表介绍。我们会提供一份受限的待确认表，只核对这些问题；无法确认的地方可直接标为未知。

这是草稿。服务器代理不得自动发送，不得解析联系人后自行外发受试者信息。

### 3.6 单次收束规则

W0 消费现有材料一次，生成核对包；之后只有实际新回复或新来源到达才更新。没有新证据时不重新扫描、不训练替代模型，不以自动轮询制造“仍在推进”的假象。

可输出：`NEEDS_CLINICAL_RESPONSE`、`TARGET_RESOLVED`、`TARGET_UNRESOLVABLE_FROM_CURRENT_RECORDS`。这些是资料状态，不是 EEG 阳性／阴性。

---

## 4. 科学问题与三个预定比较

### 4.1 主问题 F1-direct

记 $X_i=\{x_{i1},\ldots,x_{iK}\}$ 为同一次访问的有效片段集合，$A_i$ 为经确认的听觉功能目标，$C_i$ 为临床变量，$Q_i$ 为技术摘要。

研究目标是 EEG 在 $C_i$、$Q_i$ 之外对 $A_i$ 的预测价值。信息论对象可写为：

$$I(A;Z\mid C,Q).$$

实际首轮只报告原量表单位的预测损失及其配对差值；**不把 MAE 改善称为 bit，不估计高维 CMI，不加新的 IB 正则。**

预定三个比较：

| 比较 | 回答的问题 | 是否主要 |
|---|---|---|
| 临床 C vs C+Q+记录学习 | 完整系统是否比临床基线有用，而非仅修复一个变差的中间基线？ | 必报 |
| C+Q vs C+Q+记录学习 | 是否有技术摘要之外的 EEG 预测价值？ | **主临床增量** |
| C+Q+先汇总后学习 vs C+Q+先学习后汇总 | 记录级学习的操作顺序是否有实际价值？ | **主方法比较** |

另报固定 EEG 均值的正则模型。三种比较不能互相替代，也不因其中一项正向而取消其他项。

### 4.2 次要 F2 条件问题

仅在同一分析子集上，听觉目标 A 和 MUSS 均有版本与时间支持时，另做：

$$I(Y_{\mathrm{MUSS}};Z\mid C,Q,A).$$

该任务明确使用**已观测听觉分数 A**作为测试输入，属于已有听觉评估后的条件预测，不是“仅凭 EEG 输出完整功能画像”。

不训练共享／特有多任务网络，不把 A 与 MUSS 相减，不将条件预测解释为临床或神经机制分离。A 若无有效资格，不能用未知 A 执行 F2；也不能把 F2 自动改成单独 MUSS 以继续计算。

### 4.3 什么是本轮的新内容

新内容只有：临床对象落实；真实连续片段输入；功能目标直接监督；汇总前后非线性的位置对照。

集合函数架构本身已有 Deep Sets 等工作 [R9]，不是本项目的新理论。只有真实功能信息和适当对照成立后，才讨论论文方法贡献。首轮是一项有限的可行性实验，而不是已经设计完成的 JBHI 故事。

---

## 5. W1 临床锁与队列规则

### 5.1 锁文件的必要字段

```yaml
clinical_lock:
  status: PENDING
  resolver_evidence_file: null
  target_id: null
  instrument: null
  unit: null
  applicable_age_scope: null
  time_relation_rule: null
  cohort_manifest: null
  corrected_pta_source: null
  identity_registry: null
  hypothesis_and_scope_approved: false
  locked_before_new_eeg_outcome_analysis: false
```

这些 null 是待落实字段，不是可直接使用的默认值。实际回执必须能追溯至来源／临床确认，不能由执行代理把布尔值改成 true 取得运行许可。

### 5.2 队列选择

主要范围：HA 来源、可解释的身份与访问、单一可比听觉量表版本、符合临床锁的时间关系。

每个身份主分析取**最早满足临床资格的 EEG 访问**；此决定在新片段质量与预测结果之前完成。索引访问信号不合格时不换成下一次更容易建模的访问。全部访问仍随身份绑定，但本轮不把重复访问当新增人数。

不要求沿用旧 49／52／57 组完整列表；每个分母明确是原始行、身份组、索引访问还是最后可分析记录。保留因新确认排除／增加的数量与原因。

主目标按 F1 语义锁定，不能比较 IT-MAIS 与 MAIS 的模型结果后选更好的版本。不自动混合两者、重标满分、删除天花板或把有序 CAP-II/SIR 换成主目标。

### 5.3 支持规模是设计可执行性，不是功效证明

该小型五折／三内折设计预设至少 30 个可分析身份组；各外层测试至少 4 组、外层训练至少 24 组、各内层训练至少 16 组。用身份及资格元数据一次分折，不试不同随机种子直到通过。

30 不是临床验证所需的“足够样本量”，也不是效应门槛；它只是本次固定复杂度设计的最低训练支持。未达时输出 `DESIGN_SUPPORT_INSUFFICIENT`，不削小校准组到 1 人，也不自动改成 LOOCV 或重新命名任务。

F2 子集单独检查；F2 不足不阻断已经合格的 F1。若任一训练划分的目标为常数，允许基线预测并明确记录 `CONSTANT_TARGET_FIT`，不得据测试标签删折。若整个目标常数则不做预测实验。

---

## 6. 信号入口：连续片段，而不是拼接旧 epoch

### 6.1 允许的来源

优先使用已验证可追溯到 HA 连续 BDF 的采样流；若已有同样 DSP 定义的连续导出，可按来源回执复用。只读源数据。

**不得把约 0.7 秒、已基线校正的 epoch 首尾拼起来，伪造 4 秒连续片段。** 不把实验中的连续 EEG 称为静息态，不把文件切段数当成新增记录。

在临床锁生效前，只检查已有元数据能否定位真实连续来源；不得先批量提取临床特征再决定标签。

### 6.2 默认处理规范

以下是本轮方法默认值，不是已验证的最佳设置；实现前按已记录采样和通道表检查一次，若物理上不适用则停止并报告，不在查看预测之后更换。

| 项目 | 规范 |
|---|---|
| 通道 | 现有可追溯 20 通道顺序；不动态选择脑区、不插值缺失通道 |
| 参考 | 固定 20 通道平均参考；不用全队列学习参考权重 |
| 频带 | 0.5–30 Hz；复用已测试因果滤波实现和明确阶数，不混用零相位旧 epoch |
| 采样率 | 250 Hz；复用已核验抗混叠重采样与时间对齐规则 |
| 物理边界 | 按真实连续存储区间分别处理；不跨缺口滤波 |
| 保护区 | 每段首尾至少 20 秒，且不短于已测有效滤波支持；记录实际值 |
| 片段 | 4 秒、不重叠、固定采样网格；不依据事件码或临床目标选起点 |
| 基线与尺度 | 不做逐片段方差归一化；仅去直流用于局部特征计算，训练尺度只用训练身份拟合 |

QA 不需要重做全部历史滤波研究。只测试新窗口边界、实际数组和读入单位；已有规则的继承限制照实记载。

### 6.3 窗口质量与输入预算

采用一次冻结的规则：非有限、源饱和、存储缺口、明确设备状态变化的不可解释区段为硬排除；原始 4 秒窗口任一必需通道峰峰值 <0.5 μV 视为平坦失效；处理后超过 150 μV 的通道多于 2/20 时排除。

上述 4 秒规则是**新的固定窗口 QC**，不声称与旧 epoch QC 等价，也不声称完成设备或眼动伪迹消除。原始量程饱和使用已核验 vendor 规则，不能凭一个通用数值猜测。

每个访问需要至少 32 个合格 4 秒窗口。沿合格窗口的时间顺序，按固定均匀索引选择 32 个；不放回。这样所有模型使用相同的 128 秒直接信号支持；这不是“只需采集 128 秒”的临床结论。

若该规则导致支持不足，先交付质量流量表，不以放宽阈值救模型。本轮不进行 QC 阈值搜索。合格窗口少的儿童不由数据增强冒充拥有更多独立信号。

### 6.4 每片段固定特征：140 维

这是降低临床学习自由度的输入，不是新生理指标。

- 每通道四个绝对对数带功率：1–4、4–8、8–13、13–30 Hz，共 80 维。
- 每通道 Hjorth 的对数活动度、对数 mobility、对数 complexity，共 60 维。

带功率采用 2 秒 Hann Welch 窗、50% 窗内重叠，PSD 单位和 Hz 因子固定；频率箱按左闭右开规则划分，最后一带包含 30 Hz。以 PSD×频率间隔求和，防止边界重复。数值 floor 固定为相应原单位下 `1e-12`，记录被截断比例；不得用测试分布设 floor。

Hjorth 的差分和采样率换算复用已测试公式，但必须在真实 4 秒窗口上计算。任何重复／共线特征都保留其定义，不能将它们当作独立生理来源。

得到每个访问 $U_i\in\mathbb R^{32\times140}$。本轮不加入 connectivity、熵谱、复杂度新指标、随机频段或学习型原始波形编码器。

---

## 7. 临床与技术基线：必须能够解释新增模型的收益

### 7.1 临床变量 C

按新临床锁记录实际可用变量：年龄、`log1p(设备使用月数)`、修正后的较好耳裸耳 PTA、较好耳助听 PTA。使用源单位，不自动把 dB HL、dB SPL 或未明单位互换。

PTA 沿用修正后定义：各耳四频齐全才计算该耳均值；“较好耳”采用既有双耳资格定义，不悄悄改成只有一耳可用也取最小值。缺失留给训练折内插补及指示变量，不用测试总体填补。无可靠单位的列不进入 C，并明确限制“超出何种临床背景”的表述。

若列在整个队列无来源支持，在临床锁时整体去掉；若只有某个训练折全缺失，按固定缺失列逻辑输出常量及指示，不偷看测试值。插补和标准化随每个训练范围重新拟合。

C 的候选基为线性与逐连续变量平方项；不包含交叉项，固定正则候选 `0.01, 0.1, 1.0`。这是一个有限非线性基线，不是完整临床机制模型。

### 7.2 Q 分成技术摘要和振幅摘要

主要技术摘要：原始可用时长、候选窗口数、合格窗口比例、明确缺失／饱和比例及已有可靠采集来源类别。若某字段恒定则只记录，不增加无效列。

主要 Q 不含根据整个 EEG 推测的“配合度”、预测出来的年龄、波形相似性或旧临床模型成绩。额外保留一个**振幅敏感性**变量：被选窗口的全头皮峰峰值中位数之对数。它不自动等同纯技术干扰。

技术调整和振幅调整分别报告；调整后增益消失只能说明条件预测敏感，不能单凭它证明原信号为伪迹。

### 7.3 不能复现“相对更差基线变好”的误读

所有 EEG 模型都报告相对 C 和相对 C+Q 的绝对 MAE 与增量。若加入 Q 后基线变差，再加 EEG 弥补了部分损失，不得仅报告后一步的正数。

---

## 8. 唯一新模型比较：先汇总还是先学习

### 8.1 矩阵

| ID | 模型 | 作用 |
|---|---|---|
| M0 | C 的训练内最佳有限基线 | 原始临床参照 |
| M1 | C+Q 的训练内最佳有限基线 | 技术摘要参照 |
| M2 | C+Q+140 维片段均值，分块正则线性模型 | 固定 EEG 基线 |
| M3 | C+Q+非线性映射（片段均值） | 先汇总后学习 |
| M4 | C+Q+均值（各片段的非线性映射） | **先学习后汇总，候选主方法** |

M3 与 M4 的编码映射均为 `140 → 8 → 8`，第一层 `tanh`、第二层线性；最后 EEG 读出为 `8 → 1`。局部映射与 EEG 头共约 1,209 个参数，不含临床分支。无 BatchNorm、无 dropout、无 attention、无 projector。

$$
\hat y_{M3}=b+c(C,Q)^\top\gamma+w^\top\phi_\theta\left(\frac1K\sum_k u_k\right),
$$

$$
\hat y_{M4}=b+c(C,Q)^\top\gamma+w^\top\left(\frac1K\sum_k\phi_\theta(u_k)\right).
$$

M3/M4 的 C、Q 基、参数数、训练窗口、优化预算、超参数机会一致。它们**不使用相同拟合权重**，而是相同架构与初始化规则各自训练。

区别来自非线性映射与汇总不交换；不预设 M4 必然优于 M3，也不把 M4 的高分直接称为高阶神经信息。

### 8.2 训练目标

A 和 MUSS 在已确认是 0–100 百分分值时缩放到 0–1，用记录级平方误差训练；输出报告恢复原单位。评价主指标为 MAE，补充 RMSE。优化平方损失、评价绝对误差的区别明确保留。

每个记录等权，每个身份主分析只有一个访问。**不得在每片段上重复施加临床损失**；32 个片段先产生一个记录预测，再对该预测计算损失。

M3/M4 同时拟合临床分支和 EEG 分支；不以刺激分类或 subject-ID 作为辅助损失。无需在本轮增加 SimCLR、CMI critic 或 VIB。

### 8.3 训练预算与候选

- 训练 full-batch、CPU、FP32；400 个固定 Adam 步，学习率 `1e-3`，不调用临床测试集早停。
- 神经参数 L2 候选只取 `0.01, 0.1`；正则按记录均方损失的同一量纲明确定义，bias 不惩罚。
- 临床基和临床正则由相应外层训练集的内层 M1 比较选定，再统一用于该外折 M2/M3/M4。该选择只在外层训练内；不得把它的内层成绩当作无偏泛化成绩。
- M3/M4 均使用种子 11、23；两种子预测在原始分值尺度平均后形成预定模型预测。不能选择较好的种子。
- 主矩阵使用相同的训练内固定变换；片段标准化按训练身份等权拟合，不做全队列 PCA 或事后选择维度。
- 输出裁剪至已确认量表界限，所有模型同样处理；保留未裁剪误差作为数值诊断，不择优汇报。

有限预算完成不等于达到全局最优。最后 loss、梯度、预测范围、训练误差和数值故障均保存；不再要求所有学习曲线达到任意平台阈值才允许报告有限算法。

---

## 9. 验证：保留身份隔离，不再切成五个互斥角色

### 9.1 五外折、三内折

按新合格身份列表及固定 seed `20260919` 建立五折；只用身份和资格元数据平衡折大小，不使用量表值或旧 OOF 成绩。所有模型用同一外折。

每个外层训练集内再做三折用于基线家族、正则与模型选择。无需另设基线训练、校准、残差训练、候选选择四组固定人员；最终模型用全部外层训练身份拟合。

本轮没有单独概率校准，因为主要是有界分数回归；不要为了沿用旧 API 加一个不必要的校准组。

### 9.2 所有变换必须在相应训练范围内

临床插补、连续尺度、平方基、EEG 标准化、模型拟合均不得接触外层测试身份。内层候选的 EEG 标准化用内层训练身份；不能先在完整外层训练集拟合变换再声称内层严格隔离。

固定信号滤波和单记录窗口 QC 不是跨人拟合，但它们可能涉及该记录全程；因此本研究是**离线访问级预测**，不声称未来片段在线部署或提前停止采集。

### 9.3 不把更多分折当作更多人

两种训练种子不是两批临床样本；32 个窗口不是 32 个患者；内层折不是独立实验。

主区间采用固定 OOF 的身份级 2,000 次配对 bootstrap，所有主要比较共享身份抽样索引。明确其不包含完整重新训练／重新划分不确定性。不要写成前瞻或外部验证。[R10]

不在本轮追加多套外层划分。样本和预估不确定性不足的事实，留给研究决策，不靠重分折掩盖。

---

## 10. 对照与统计解释：只保留会改变结论的检查

### 10.1 必做对照

1. **绝对临床基线对照**：M0/M1 与 M4 都报告；不能仅报告 M4−M3。
2. **同输入、同容量对照**：M3 与 M4；固定均值模型 M2 同列，不新增五个特征库。
3. **技术与振幅分离**：主技术 Q 完成全模型；振幅敏感性仅重拟合 M1/M4，所有其他设置不变。
4. **身份错配内容对照**：仅使用外层训练身份，在训练内将完整记录特征包与临床行错配一次，保留包内32片段、尺度和关联结构；重新拟合一个预定 M4，测试 EEG 不打乱。它是破坏训练对应的诊断，**不是条件交换性成立的正式置换 p 值**。

错配模型表现差不能替代超过 M0/M1 的证据。反之，真实与错配相近是谨慎解释的理由，不证明真实 CMI 为零。

### 10.2 标准化的报告项

每个目标分别给出：身份数、时间证据层级、量表版本、满分人数、MAE/RMSE、所有外折误差、每个主要对比的点估计与固定 OOF 区间、去单个身份的固定误差范围。

满分／非满分结果只作预定描述，不在小亚组内重新调参，不根据结果更换年龄界限。主分析不删满分，也不把满分当成右删失的潜在能力去拟合未经定义的高于100的真值。

不作“一个显著、一个不显著，因此二者不同”的推断；方法差别用同一身份的直接配对比较。

### 10.3 不设置新的效应开关

不以 `gain > 0.5`、`CI_low > 0`、某个 p 值或某个表征排名决定剩余对照是否运行。所有预定比较完成后，给出“支持到哪里、仍有哪些替代解释”的文字判断。

小效应照实保留，但不因它自动新增神经分支、公开外部数据或种子。下一轮是否需要新证据由研究者决定，不由代理自动生成续跑清单。

---

## 11. 有限实现验证：不再做几千个 capability 世界

W0 可实现模型并完成有限、可复现的测试，不加载新真实 EEG 或新临床关联。

必须包含：

- 更改外层测试标签不会改变训练变换、超参数或模型哈希。
- 数据行重排、空 Excel 行和重复表头不改变实际源行关联；错配身份能被核对规则拦截。
- 片段重排不改变 M4；同一身份不能跨折；非有限输入不会静默填成零。
- M3/M4 参数数与原始窗口完全一致；每访问仅一个损失；标签缺失掩码不进入特征。
- 复制片段不会被记为新增身份；越界裁剪和单位换算一致。
- 原始连续时间被打断时，窗口不能跨缺口；旧 epoch 拼接会被拒绝。

只设计三个合成机制，每机制4个固定种子，M3/M4 各拟合一次，共24次小模型训练：

| 机制 | 要检查什么 | 不得声称什么 |
|---|---|---|
| 临床基线足够、EEG 独立 | 无信号场景输出有限，预测和数据范围正确；保留可能的偶然小增益 | 12/24次结果不能证明总体误报受控 |
| 片段均值决定目标 | 两个方法都能学习简单映射；不是只有 M4 才被实现正确 | 不证明真实临床效应可检出 |
| 均值接近相同、分布形态与目标有关 | 先映射后汇总的完整计算图能工作，记录级监督不是被错误复制到片段 | 不将强玩具机制当作真实功效依据 |

机制检查标准在生成结果前写入测试：强注入例子需相对训练均值预测降低测试 MSE 至少50%，且四个种子至少3个达到；独立场景不设置“必须全负”的伪保证。能力未通过可做**一次实现或合成尺度排错**，不得看真实结果调参。一次后仍失败，记录未建立能力并停止 W1。

这只是结构与可学习性检查，不制作额外 MI/PID 理论审计项目。

---

## 12. 资源与拟合上限

### 12.1 W0

W0 只用 CPU，预算上限12 CPU core·h，GPU为0。已有材料读取、核对包、实现与有限测试包括在内。默认2个并发CPU作业；一次失败导致重新计算须记原因，不因报告格式错误重新拟合。

### 12.2 W1 条件额度

本方案使用片段固定特征上的小网络，**默认仍只用 CPU**，不训练新的原始波形编码器。

- 2个目标 × 2个小网络 × 5外折 ×（3内折×2正则×2种子 + 2种子最终）= 最多280次主要小网络拟合。
- 振幅和错配对照固定外层已有选择，不重新开内层网格：最多40次小网络拟合。
- 合成24次；含少量故障验证，本轮小网络拟合总上限360次。
- 临床／固定特征求解器总调用上限1,000次，含内层候选与失败。若实际任务目录超过，先压缩无必要候选或报告，不自动扩大。
- W0+W1 合计上限96 CPU core·h、0 GPU·h、最多4个CPU作业并发。

计数指优化调用，不是独立模型／统计实验数。导出、报告和核验不调用训练函数。

若执行环境确需 GPU，须单独记录资源变更及理由；不得用它扩模型。未来 GPU 禁用 P100，优先 A100/L40S/H100，备选 V100/PRO6000。[R8]

---

## 13. 来源与隐私：最少但足够的记录

继承旧发布范围：原始 EEG、身份、精确日期、临床原行、个体预测、权重与详细日志留在 private。

旧已核验的427文件及45任务回执不重复作为科研任务全量重跑。本轮只绑定实际使用的新临床锁、索引访问、源信号和新代码。可复用旧哈希，记录当前文件确有变化时才定向核验；不得通过复制旧 PASS 给新的未检查输入背书。

新的关联键至少包含 `workbook_hash + sheet + actual_row`，且有身份/DOB/临床已知字段交叉核对。只检查哈希无法发现语义错行；至少一个专门的“非空顺序号与实际行号错位”测试必须存在。

原结果和失败目录不可覆盖。新命名空间建议：

```text
private/auditory_fn1/<run>/
results/auditory_fn1/<run>/
reports/auditory_fn1/<run>/
docs/auditory_fn1/
```

公共文档不得包含真实候选键。批次临床确认如涉及人员或日期，仅将去标识化规则及计数写入公共结果。任何外发核对表、提交 GitHub 或联系临床团队都需要实际授权；本任务只准备文件。

---

## 14. CLI 与配置合同（待实现，不是已存在命令）

新模块建议 `auditory_fn1`。以下接口是实现规格，不可在未实现时声称命令已经运行。旧命令也不能只改包名当成兼容接口。

```text
python -m auditory_fn1.cli prepare_request --run <new_run>
python -m auditory_fn1.cli test --run <new_run>
python -m auditory_fn1.cli resolve_evidence --run <new_run> --evidence <private_file>
python -m auditory_fn1.cli freeze --run <new_run> --clinical-lock <private_lock>
python -m auditory_fn1.cli export_segments --run <new_run> --freeze <run>
python -m auditory_fn1.cli fit --run <new_run> --freeze <run> --target A
python -m auditory_fn1.cli fit --run <new_run> --freeze <run> --target MUSS_given_A
python -m auditory_fn1.cli report --run <new_run> --sources <manifest>
```

### 14.1 默认配置

```yaml
project:
  name: auditory_fn1
  version: 1.0
  baseline_commit: 493a076a3848d3546a5889e2c583d0fee2ba1612
  initial_stage: W0
  real_training_enabled: false
  overwrite: false
  auto_publish: false

clinical:
  scope: verified_visit_function
  archival_fallback_allowed: false
  clinical_lock: null
  primary_target: auditory_function_single_confirmed_instrument
  secondary_target: MUSS_given_observed_A
  automatic_endpoint_substitution: false
  time_tolerance_days: null
  index_rule: earliest_clinically_eligible_visit_before_new_signal_qc

signal:
  continuous_source_required: true
  concatenate_epochs: false
  output_hz: 250
  filter_mode: inherited_tested_causal_0p5_30
  guard_seconds_min: 20
  window_seconds: 4
  overlap_seconds: 0
  windows_per_record: 32
  window_selection: chronological_uniform_without_replacement
  feature_dim: 140
  peak_to_peak_uv: 150
  maximum_channels_above_ptp: 2
  flat_ptp_uv: 0.5
  per_window_variance_normalization: false

models:
  ids: [M0_C, M1_CQ, M2_MEAN_RIDGE, M3_MEAN_THEN_MLP, M4_MLP_THEN_MEAN]
  local_mlp_dims: [140, 8, 8]
  activation: tanh
  train_unit: record
  stimulus_auxiliary_loss: false
  information_bottleneck_loss: false
  clinical_families: [linear, additive_quadratic]
  clinical_penalties: [0.01, 0.1, 1.0]
  eeg_ridge_penalties: [0.01, 0.1, 1.0]
  neural_penalties: [0.01, 0.1]
  seeds: [11, 23]
  seed_aggregation: arithmetic_mean_prediction
  optimization_steps: 400
  learning_rate: 0.001
  selection_metric: MAE_original_units
  test_early_stopping: false

validation:
  outer_folds: 5
  inner_folds: 3
  split_seed: 20260919
  min_total_groups: 30
  min_outer_train_groups: 24
  min_inner_train_groups: 16
  min_outer_test_groups: 4
  bootstrap_repetitions: 2000
  bootstrap_scope: fixed_oof_group_paired_not_pipeline_refit
  effect_or_significance_execution_gate: false
  expand_after_small_positive: false

resources:
  current_cpu_core_hours_cap: 12
  total_conditional_cpu_core_hours_cap: 96
  gpu_hours_cap: 0
  neural_fit_cap: 360
  linear_solver_call_cap: 1000
  max_concurrent_cpu_jobs: 4
  forbidden_gpu: [P100]
```

### 14.2 行为要求

`prepare_request` 只使用源资料与现有支持回执，不计算新的 EEG—目标关联。`resolve_evidence` 必须消费真实证据文件。`freeze` 不得自动创建临床确认，不得将最后一批模型目录当作资格证明。

`export_segments`、`fit` 的入口同时检查临床锁、身份支持和代码版本；任意缺失时输出零拟合停止回执。F2 不足只阻断 F2。

`fit` 应先写入完整任务目录再拟合；包含所有预定模型与对照。没有因效果大小提前停止的代码路径。正则 tie 按较简单模型／较强惩罚固定处理；不得用测试风险决胜。

`report` 只读取保存预测和训练回执，不隐式重新训练。无真实模型时输出 `W1_NOT_STARTED`，不能产生空的“零增益”主表。

### 14.3 Slurm 提交形状

新建并测试 `slurm/auditory_fn1_cpu.sbatch` 后，可使用以下形状；不得照抄已有运行名：

```bash
umask 077
# wrapper 必须进入实际活动工作区、使用已验证环境、快照源码并限制数学库线程。
sbatch --cpus-per-task=2 --mem=8G --time=00:20:00 \
  slurm/auditory_fn1_cpu.sbatch prepare_request --run FN1_request_<new_id>

sbatch --cpus-per-task=2 --mem=8G --time=00:40:00 \
  slurm/auditory_fn1_cpu.sbatch test --run FN1_tests_<new_id>

# 下面只在真实回复已导入且临床锁有效后允许提交。
sbatch --cpus-per-task=2 --mem=16G --time=01:00:00 \
  slurm/auditory_fn1_cpu.sbatch export_segments \
  --run FN1_export_<new_id> --freeze FN1_freeze_<id>
```

训练提交使用任务目录和明确依赖，不以“上一个作业大概结束了”作为启动条件。没有服务器连接的文档编写助手不得声称提交或完成这些作业。

---

## 15. 交付清单与结束状态

### 15.1 无论临床回复是否到达，W0 必须交付

```text
NEXT_ROUND_DECISION.md               # 一页决定，不重复全部历史
CONFIRMED_FACTS_AND_OPEN_QUESTIONS.md
CLINICAL_QUERY_DRAFT.md              # 可交给研究者的外联草稿
PRIVATE_RESOLUTION_TEMPLATE.csv      # 模板空表；填充版仅private
IMPLEMENTATION_TEST_REPORT.md
STAGE_STATUS.json
```

`NEXT_ROUND_DECISION.md` 必须说明：最新 PTA 修正如何继承、哪些旧任务不重开、实际还缺哪一项证据、是否存在可执行的临床对象。不给“建议再跑十种模型”的自动尾单。

### 15.2 W1 启动后另交付

```text
cohort_flow.csv
clinical_lock_summary.json
segment_support_summary.csv
model_metrics.csv
paired_effects.csv
technical_amplitude_controls.csv
fold_and_seed_summary.csv
fit_ledger_summary.json
FUNCTIONAL_RECORD_LEARNING_REPORT.md
```

逐人预测、片段列表、确认原件、权重和划分均私有。公共区间必须注明固定 OOF。报告至少同时展示 M0/M1/M2/M3/M4 的绝对误差，不只展示胜出的比较。

### 15.3 最终状态可为以下之一

| 状态 | 含义 | 下一步 |
|---|---|---|
| `NEEDS_CLINICAL_RESPONSE` | 缺的是真实资料，不是算力 | 研究者处理临床联系；计算代理结束本次执行 |
| `TARGET_UNRESOLVABLE_FROM_CURRENT_RECORDS` | 现有档案无法建立本轮问题 | 将所需资料纳入未来采集，不重命名旧回归继续跑 |
| `DESIGN_SUPPORT_INSUFFICIENT` | 目标成立但本次有限设计训练支持不足 | 提交人数、缺失结构和设计限制，不自动变换终点 |
| `SIGNAL_SOURCE_OR_WINDOW_SUPPORT_LIMITED` | 无真实连续来源或预定窗口不足 | 保留计数，不能拼接 epoch 补足 |
| `IMPLEMENTATION_UNRESOLVED` | 固定测试未通过或真实数值故障 | 最多一次有明确原因的修复，保留失败；不是科学阴性 |
| `W1_COMPLETED_EXPLORATORY` | 全部预定比较完成 | 按完整结果作研究判断，不自动扩模型 |

最后一种状态不编码“显著即成功”。可能出现：EEG 有增量但 M4 不优于简单汇总；M4 比 M3 好却未超临床；所有模型都没有稳定增量；或线索受技术因素影响。四类结果都应明确区分。

---

## 16. 如何决定更远的一步，而不是再进入循环

本轮最多回答“是否值得继续发展直接记录级功能学习”。它不完成临床效用、机制分离或独立队列验证。

- **临床对象未成立：** 不再扩大档案预测。下一次投入必须是目标资料或可解释的新采集。
- **对象成立、模型矩阵完成，但 EEG 增量不稳：** 保留小效应及不确定性；不自动推导出“需要更大网络”。
- **EEG 有增量、学习顺序无优势：** 可使用简单模型，但不能把 M4 写成方法贡献。
- **方法与临床增量都有一致线索：** 后续优先寻找独立、同期且来源明确的验证；不是立即加 IB/CMI 损失形成“大模型”。
- **只在调弱临床或技术基线后阳性：** 明确为基线依赖，不称为不可替代的临床信息。

这些是研究判断原则，不是本轮按 p 值中途取消任务的门控。

---

## 17. 可直接交给服务器执行代理的指令

> 从 `493a076a3848d3546a5889e2c583d0fee2ba1612` 的最新来源状态开始。先读 AGENTS、PTA 勘误、F-series 资格报告、修正扩展报告和 corrected-cohort retrain 的最终状态，不把历史“未训练”字段当当前状态。
>
> 本轮执行 FN1 v1.0。立即阶段只有 W0：一次性整理已知事实与待临床确认的问题，生成私有确认模板及外联草稿，实现本文的小型记录级学习接口和有限合成测试。不要重跑旧 D、P0、N2R、R3 或档案特征矩阵。不要计算新的临床关联来挑终点。不要自动联系临床团队或外发资料。
>
> 逐行版本、问卷—EEG 时间关系及身份来源无法从现有证据确认时，保留 unknown。只有真实临床确认或可追溯原件到达并被纳入 clinical_lock 后，才评估 W1 的身份和连续片段支持。没有回复时交付 `NEEDS_CLINICAL_RESPONSE` 并结束本次运行，不进入循环扫描或默认的 archival fallback。
>
> 若临床锁及支持成立，执行本文全部预定 M0–M4、振幅与错配对照。主要目标为单一确证的听觉功能量表；MUSS_given_A 仅在自己的共标签时间资格和人数支持成立时启动。不要因中途效果小、区间跨零或模型排名而停止剩余规定比较，也不要因为小正值增加架构或种子。
>
> 使用真实连续 EEG 的4秒窗口，绝不拼接旧短 epoch。窗口级固定特征140维；同一32窗口输入比较“先汇总后MLP”与“先MLP后汇总”。所有临床损失在记录级计算。所有变换和模型选择只使用对应训练身份。五外折、三内折，不重新切成A/B/C/D/E五个互斥角色。
>
> 全部数值任务通过Slurm，默认CPU，无新增原始波形编码器、无GPU。执行前记录任务目录与预算；报告和核验不得再次调用训练。保留旧结果、失败和小效应，个人数据与权重仅private。本轮不自动push。最终交付真实执行到的阶段、剩余资料问题和完整有限比较，不能声称独立临床验证已经完成。

---

## 18. 引用与证据入口

下列仓库引用固定在本轮已读取提交，历史说明与最新完成状态冲突时，以相应最终报告为准。

[R1] 最新修正重训状态：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/docs/auditory_retrain/STATUS.md

[R2] F-series 临床资格报告：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/reports/auditory_fseries/STAGE1_QUALIFICATION_REPORT.md

[R3] 原始说明文档量表定义修订：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/docs/auditory_fseries/SOURCE_DOCUMENT_AMENDMENT_001.md

[R4] 历史 PTA 关联勘误：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/docs/auditory_fseries_archival/LEGACY_PTA_LINEAGE_AMENDMENT.md

[R5] 修正队列完整重训报告：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/reports/auditory_retrain_v1/verification_001/REPORT.md

[R6] 完整重训解读：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/docs/auditory_retrain/INTERPRETATION.md

[R7] PTA 修正、57组档案扩展、技术／振幅对照及混合MFF结果：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/reports/auditory_repair/verification_001/REPORT.md

[R8] 仓库执行与隐私规则：
https://github.com/W-Yinghao/auditory/blob/493a076a3848d3546a5889e2c583d0fee2ba1612/AGENTS.md

[R9] Zaheer et al. Deep Sets. NeurIPS 2017. 集合映射与置换不变结构的已有方法基础；不构成本项目新颖性证明。
https://papers.nips.cc/paper/2017/hash/f22e4747da1aa27e363d86d40ff442fe-Abstract.html

[R10] Collins et al. TRIPOD+AI statement. BMJ 2024;385:e078378. 临床预测开发与评价的报告框架；不是临床合格性、功效或有效性证书。
https://pubmed.ncbi.nlm.nih.gov/38626948/

**编写范围说明：** 本文件依据上述公开代码／聚合报告及既有讨论形成。没有读取新的个体 EEG、填充临床确认表、训练模型、联系临床团队或提交服务器作业。
