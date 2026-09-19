# Auditory FN1-A：仅使用既有档案的记录级 EEG 学习

**版本：** FN1-A v1.1（完整修订版，替代 FN1 v1.0 的后续执行要求）  
**日期：** 2026-09-19  
**依据仓库：** `W-Yinghao/auditory`  
**研究证据基线：** `493a076a3848d3546a5889e2c583d0fee2ba1612`  
**对应旧文件：** `AUDITORY_FN1_NEXT_ROUND_PLAN_493a076.md`  
**文件性质：** 未执行的新研究方案、实现规格和服务器代理指令；不是已完成结果。  
**本次用户约束：** 医生已经提供其拥有的全部资料，后续联系困难；本轮不再要求联系医生、取得新回复、补做问卷或补充采集。只使用已交付的 EEG、工作表、说明文档、采集元数据及已经修正的关联产物。

---

## 0. 这次修改的实质

**取消“临床版本和评估日期全部确认后才能运行”的前置要求；不把未知内容改成已确认，而是明确改为既有档案数值的探索性预测。**

旧方案的目标是经过时间与版本确认的同期功能解码。本版的目标是：

> **在现有 HA 档案中，使用与候选身份可靠关联的 EEG 记录，在已有临床数字和采集摘要之外，能否更好地预测同一档案中的听觉分数？对相同片段特征，“先学习再汇总”是否优于“先汇总再学习”？**

这改变了研究对象和允许的解释，不是宣称资料缺口已被解决。结果可以作为后续论文的探索性证据，但不能称为同期临床效度、未来功能预测或设备获益证明。

| 项目 | FN1 v1.0 | 本版 FN1-A v1.1 |
|---|---|---|
| 外部联系 | 准备医生核对包并等待回复 | 不联系、不等待、不产生待发送材料 |
| 听觉目标 | 单一确证版本的听觉功能量表 | HA 原表 `IT-MAIS/MAIS得分（%）` 的档案数字，名称及不确定性原样保留 |
| 日期条件 | 要求同次访问或经确认的时间范围 | 日期存在则记录；问卷日期或关系未知可以纳入，不补零间隔 |
| 设备/PTA 元数据 | 部分字段等待确认 | 使用已有字段；单位、状态和日期未知分别标记，限定结论 |
| W0 | 资格核对和外联准备 | 复用已有资料建立档案分析清单、实现及测试 |
| W1 | 被临床确认锁阻断 | 本版已允许；仅依赖身份关联、信号、数值和执行支持检查 |
| 新方法 | 记录级学习与汇总顺序比较 | 保留，不扩大成模型搜索 |
| 缺口处理 | 可能结束于等待医生 | 进入限制表；仅真实错配、冲突、无标签或无合格信号影响对应分析 |

**初始状态：`W0_ARCHIVE_SETUP_READY`。** W0 的操作性检查通过后，执行代理直接进入 W1，不需要第二次人工确认或临床回复。

本版明确覆盖旧文档中的 `W1_BLOCKED_CLINICAL_LOCK`、`NEEDS_CLINICAL_RESPONSE`、`prepare_request`、`resolve_evidence` 以及“无临床回复不得进行档案学习”等要求。旧文件和已经执行的结果仍然保持原样；不得回写为历史上已经满足本版条件。

本轮不使用 p 值、增益大小、区间是否跨零或模型排名决定是否执行剩余规定比较。预定矩阵完整运行；支持不足、错配、数值故障和资源超限仍应真实停止相应任务并保留回执。

---

## 1. 继承什么，不重复什么

### 1.1 已经具备的资料直接使用

HA 档案已有听觉列、MUSS、CAP/SIR、年龄、助听器使用月数、左右耳裸耳/助听四频阈值及候选 EEG 关联。量表说明文档也已经找到；未确认的是其逐行适用关系和部分日期含义。它们不是“所有临床资料都缺失”。[R2–R3]

旧 PTA 的实际工作表行键修正必须保留。使用 `workbook hash + sheet + actual source row` 关联，而不是非空行顺序编号。已修正 PTA 的默认入口为：

```text
private/auditory_repair/pta_007/candidate_covariates.csv
results/auditory_repair/verification_001/pta_revalidated/
```

若活动工作区路径不同，只根据既有来源清单建立路径映射；不得复制旧错配表来补齐文件。[R4,R7]

### 1.2 现有数字是参照，不是新实验的预期效果

保留 57 组档案扩展中的小效应及控制敏感性，以及 52 组新划分重训中的弱/null 结果。后者修正了旧 D 的来源与划分，但仍是刺激表征及固定刺激头分解，不是本次直接记录级目标学习。[R5–R7]

这些旧分析不是新的独立样本。本轮也不重命名它们为同期功能解码。

### 1.3 明确不重开

不重训旧 D、可见/null 分解、P0、N2R、R3、N1/N3，不重新扫五个旧特征库和所有量表，不重跑整套历史核验，不自动追加种子、模型或数据集。F3/F4、CI 外部验证和 NH 对照扩样本不在本轮内。

医生无法进一步提供资料，不构成模型能够补出真实日期、量表版本、诊断或设备开关状态的理由。

---

## 2. 本轮具体预测什么

### 2.1 主目标：`A_archive`

- 来源：既有 HA 主工作表的 `IT-MAIS/MAIS得分（%）` 列。
- 目标定义：与本次索引 EEG 关联的、原表中实际记录的数值。
- 单位：**HA 原表分值**；依已有表头和说明采用 0–100 数值范围进行本轮建模，不将所有行命名为确证 IT-MAIS。
- 量表版本：已知则记录真实证据；未知写 `UNKNOWN_MIXED_HEADER`。不依年龄或分数猜版本。
- 日期：问卷日期及与 EEG 的关系未知时保留 `UNKNOWN`。未知不是零间隔，也不是未来评估。

本分析池是**同一个 HA 来源数值列的档案池**，并不宣称 IT-MAIS 与 MAIS 在心理测量上等价。允许估计这个原表数字，不等于已建立统一临床潜变量。若存在明确证据表明某些行采用不同计分单位，不自动做换算或跨单位合并；将受影响行列为明确单位冲突，与普通“版本未知”分开。

不能因 `A_archive` 效果不好，将主目标替换为 MUSS、CAP 或 SIR。满分记录不删除，不生成“满分以上能力”。

### 2.2 次要目标：`V_archive_given_A`

- 被预测值：同一 HA 档案行的 MUSS 原分值，记为 `V_archive`。
- 已知输入：同一行的 `A_archive`，以及相同临床变量和技术摘要。
- 解释：**已知原表听觉数字时，预测原表言语使用数字的条件关联**。
- 不要求新增问卷日期或版本证据；要求两列来自同一已关联档案行，数值有限、来源一致、没有未解决值冲突。

这个模型在测试时明确使用已观察到的 `A_archive`，所以不是“仅凭 EEG 输出全部功能画像”，不是声音分类，也不是听觉能力对言语能力的因果分解。两列可能存在未记录的测量时间差，作为限制报告。

F2 仅因共标签、身份、信号或训练支持不足而停止，不因缺少医生确认而停止。F2 不可用时不改成另一个未预定的终点，F1 可独立完成。

### 2.3 为什么不是把旧档案筛查再做一遍

旧扩展主要使用短 epoch 的固定汇总或刺激训练表征。本轮有一个具体的新比较：

> 同一批真实连续片段、同一组固定局部特征、同一目标、相同网络参数量，比较非线性映射在片段汇总之前或之后的作用。

本轮不是临床确证研究，也不只是又换一批回归器。若学习顺序不增加价值，保留结果并结束本轮，不自动扩成注意力或基础模型项目。

---

## 3. 未知、缺失与冲突必须分开处理

| 情况 | 本轮处理 | 是否阻断？ |
|---|---|---|
| 听觉列版本未知、混合标题 | 保留字面名称，预测同源档案原数字 | 否 |
| 问卷日期缺失或日期角色不明 | 保留未知；不作同期、随访或预测时间方向解释 | 否 |
| EEG 采集时间可读，问卷时间不明 | 使用真实采集时间选择索引和定位信号，不外推问卷日期 | 否 |
| PTA 单位未逐行重复，但来自同一明确裸耳/助听四频列 | 使用修正后的同源原数字；单位状态保留，不声称完整可听度控制 | 否 |
| 部分 PTA 数值缺失 | 训练折内插补＋缺失指示，不为此强制沿用旧完整病例 D 队列 | 否 |
| 设备开关状态、每日佩戴量未知 | 保留未知，后者不进入主要 C；不推断设备获益或实际暴露剂量 | 否 |
| 名称/DOB 等出现未解决的相互矛盾，可能错人 | 暂缓该身份/关联，不由预测结果决胜 | 对应记录阻断 |
| 索引行目标缺失、非数值或同证据等级的目标值冲突 | 不插补目标，不取平均或有利版本，不改用下一次访问 | 对应目标阻断 |
| 明确不同计分单位混入、无法按现有证据分开 | 不做猜测换算，单列受影响记录/来源 | 对应来源阻断 |
| 无真实连续信号或固定窗口不足 | 不拼接旧 epoch 造连续数据 | 对应记录阻断 |
| 目标总体恒定或固定验证设计支持不足 | 输出无法估计/支持不足，不能计为 EEG 阴性 | 对应任务阻断 |

**本轮的通过条件是“能够定义一个来源可信的档案预测问题”，不是“临床元数据全部完整”。**

若既有明确证据说明关联使用了错误的人、错误的值或互相矛盾的单位，不能借“档案研究”放过错误。反过来，单纯未知时间与版本也不能再次把整个队列判为零资格。

---

## 4. W0：既有资料的一次性归并与分析锁

### 4.1 不外联、不等待、不循环搜索

不再生成医生消息草稿、外联确认表或等待回复的任务。使用已经交付并已审计的材料，定向建立本次清单；不再反复读取同一文档寻找已确认不存在的字段。

允许为定位实际文件、验证实际行键和读取已经存在的内容做一次性处理。这不是要求医生补资料，也不要求分析人员自行猜测未记录事实。

### 4.2 数据池与索引规则

主要范围为现有 HA 来源。57 组档案扩展可作为来源导航，但本轮人数由新信号支持确定；不硬套旧 52 组 PTA 完整 D 队列或 49 组匹配袋。

每个身份最多一个主索引：

1. 优先复用已经锁定、基于真实采集时间建立的最早来源索引及其实际工作表行关联。
2. 若某身份只有后续版本资料，先按既有来源优先级解决同一记录的重复导出，不把不同访问合并。
3. 不存在可复用索引时，仅按已有采集时间、来源资格和既有身份关联确定最早记录；同时间用稳定不透明 ID 决胜。
4. 在查看新 EEG 特征与目标关系之前冻结索引。索引目标缺失或信号失败时不改挑后续记录。
5. 同一行 A/MUSS 为 F2 共标签来源；不能把不同日期的 A 和 MUSS 拼在一起，只为扩大支持。

所有冲突及损失计数保留，原始行数、候选身份数、索引数、信号合格数分别报告。现有支持的候选身份可以使用，但不称作已经临床确证的独立儿童。

### 4.3 私有分析表 schema

```text
split_group_id                       # 既有保守身份组；所有访问同组
index_record_id
source_workbook_sha256
source_sheet
source_row_number                    # 实际工作表行号，不是非空顺序
clinical_link_key
link_evidence_level                  # 已有证据层级，不伪造 confirmed
identity_conflict                    # 明确矛盾，与未知不同
A_literal_header
A_raw_value
A_instrument_status                  # DOCUMENTED / UNKNOWN_MIXED_HEADER / CONFLICT
A_score_unit_status                  # HA_SOURCE_COLUMN / DOCUMENTED / CONFLICT
MUSS_raw_value
MUSS_instrument_status
assessment_date                      # private，可缺失
assessment_date_role                 # QUESTIONNAIRE / EEG_ONLY / UNKNOWN
eeg_acquisition_time                 # private
eeg_questionnaire_relation           # DOCUMENTED_SAME_VISIT / KNOWN_INTERVAL / UNKNOWN
age_recorded_months
age_at_eeg_if_derivable               # 辅助检查，不自动替换来源年龄
HA_duration_months
better_unaided_pta_corrected
better_aided_pta_corrected
pta_unit_status
pta_date_relation
device_state_status
target_A_available
target_V_given_A_available
source_refs
exclusion_reason                     # 不因单纯未知日期/版本产生排除
```

unknown 是实际状态，不转换为 confirmed。目标不能由 EEG、其他量表或模型插补。缺失标签掩码用于资格/损失，不作为预测特征。

### 4.4 `archive_analysis_lock.json`

```yaml
analysis_lock:
  status: LOCKED_FROM_EXISTING_ARCHIVE
  estimand: HA_source_score_prediction_not_contemporaneous_clinical_validation
  external_confirmation_required: false
  primary_target: A_archive
  secondary_target: V_archive_given_A
  target_source: HA_registered_workbook_same_source_column
  unknown_instrument_version_allowed: true
  unknown_questionnaire_time_allowed: true
  unknown_device_state_allowed: true
  assumptions:
    - predict_recorded_values_without_claiming_psychometric_equivalence
    - no_imputed_questionnaire_dates_or_scale_versions
    - association_not_temporal_or_causal_prediction
  cohort_manifest: "<实际生成的私有清单>"
  corrected_pta_source: "<已修正来源的实际路径与哈希>"
  identity_registry: "<既有身份登记来源>"
  locked_before_new_outcome_modeling: true
```

这些路径由实际产物填写。`LOCKED_FROM_EXISTING_ARCHIVE` 仅证明本次对象与规则已经固定，**不是临床资料已被医生确认的声明**。不再保留 `hypothesis_and_scope_approved`、`clinical_response_received` 等等待外部人员的门控。

W0 顺序：现有清单归并 → 标签/来源锁定 → 实现与有限测试 → 连续信号支持 → 冻结人数与划分 → W1。无需研究者再批准同一套已约定矩阵。

---

## 5. 科学比较与可解释范围

记 $U_i$ 为索引记录的片段特征集合，$Z_i$ 为记录表征，$C_i$ 为档案临床变量，$Q_i$ 为技术摘要。形式上的信息对象可写为：

$$I(A_{archive};Z\mid C,Q).$$

这里的随机变量是**记录在表中的数字**，不是已经验证的同期潜在听觉能力。首轮不拟合高维 CMI、不加入 IB 正则；用原表单位的预测误差与配对差值回答问题。MAE 不是 bit。

必须分别回答：

| 对比 | 意义 |
|---|---|
| M0：C vs M4：C+Q+记录学习 | 完整方法是否超出原始临床数字基线？ |
| M1：C+Q vs M4 | 是否存在采集摘要之外的 EEG 增量？这是主要档案增量。 |
| M3：先汇总后学习 vs M4：先学习后汇总 | 相同输入与容量下，改变学习位置是否有价值？这是主要方法比较。 |

“比 M3 好”不能替代“比 M0/M1 好”。对技术调整后的风险变化，不能仅凭一次增益消失断言伪迹因果作用。

允许的报告措辞示例：

> 在既有 HA 档案的候选身份关联中，使用记录级 EEG 特征预测原表听觉数字；评估时间及部分量表版本未确证，因此结果属于离线档案关联，不建立同期临床效度。

禁止写成“已验证康复水平”“预测未来恢复”“脑电分离出听觉与语言机制”“设备开启的收益”“独立临床验证”。

---

## 6. 连续 EEG 输入与窗口规则

### 6.1 来源与处理

使用已经提供的 HA 连续 BDF 或可追溯、处理定义相同的连续导出。**不把约 0.7 s、已基线校正 epoch 拼成 4 s。** 如果只有短 epoch，输出对应信号支持不足，不回退成旧档案模型矩阵。

| 项目 | 冻结设置 |
|---|---|
| 通道 | 既有可追溯 20 通道，顺序固定；不按模型选择脑区 |
| 参考 | 固定 20 通道平均参考 |
| 滤波 | 复用已经核验的因果 0.5–30 Hz 实现，记录实际阶数与依赖支持 |
| 采样率 | 250 Hz，复用已有抗混叠和时间对齐规则 |
| 缺口 | 按真实连续存储区间分别处理，不跨缺口填零滤波 |
| 保护 | 每段首尾至少20 s，且不短于已测有效支持 |
| 窗口 | 4 s、不重叠、固定网格；起点不依事件标签或量表 |
| 归一化 | 不逐窗口除方差；特征尺度仅在训练身份拟合 |

这些是方法设置，不是最优生理窗口；实验中的连续 EEG 不称作静息态。只验证本轮实际使用的来源和新窗口，不重做全库滤波审计。[R8]

### 6.2 窗口资格与设备备注

硬排除：非有限信号、源量程饱和、物理缺口；原始窗口某必需通道峰峰值 <0.5 µV 的平坦失效；处理后超过150 µV的通道多于2/20。

饱和判据使用实际 vendor 量程规则；没有相应证据时记为“未核实此类饱和”，不发明阈值。窗口 QC 是新的固定4 s规则，不等价于旧 epoch QC，不证明已完成眼动/设备伪迹消除。

一般设备状态未知不排除记录。已有明确且可对齐的中途设备/任务改变时，按已有时间证据切开物理分析区段，不让窗口跨变更；没有准确时刻的备注保留为记录级异质性限制，不能猜一个剪切时间，也不能据其模型效果决定是否删人。

每记录至少32个合格窗口；按时间顺序均匀无放回取32个，得到128 s直接信号支持。所有模型使用同一组窗口。不能解释成“实际只需采集128 s”，也不通过复制窗口补支持。

### 6.3 每窗口140维固定特征

每通道四个对数绝对带功率：1–4、4–8、8–13、13–30 Hz，共80维；每通道对数 Hjorth 活动度、mobility、complexity，共60维。

Welch：2 s Hann、50%重叠，PSD乘频率间隔求和；频段左闭右开，最后一带包含30 Hz。使用与 µV 输入相符的单位。数值 floor 固定 `1e-12`，记录触发比例。Hjorth 的采样率因子与公式复用已测试版本，仅改为真实4 s窗口。

每记录形成 $U_i\in\mathbb R^{32\times140}$。不自动加入连接组、熵、额外频段或原始波形神经编码器。

---

## 7. 临床与技术参照

### 7.1 临床变量 C

主 C 固定为原表实际月龄、`log1p(HA使用月数)`、修正后的较好耳裸耳 PTA、修正后的较好耳助听 PTA；次要任务再加同源 `A_archive`。

使用原表同列数字，不猜单位转换。PTA 日期未知不剔除其原值，但报告只称“已记录的听力变量”，不称同期完整可听度。单位未知与明确矛盾分开；确证冲突不得自动混用。

PTA 计算沿用修正后口径：各耳四频齐全才得该耳均值，较好耳依旧有双耳资格定义，不改成一耳缺失仍取最小值。

协变量缺失在每个训练折中位数插补并加指示；训练折全缺失的列置固定常量及缺失指示，不从测试集合取得数值。不插补目标，不强制所有 PTA 齐全再入组。

临床候选仅为线性与逐连续变量平方项，正则 `0.01,0.1,1.0`，不增加交叉项或新的临床变量搜索。未知问卷日期、量表版本不得由年龄或 EEG 学出后加入 C。

### 7.2 技术 Q 与振幅分开

Q：原始可用时长、候选窗口数、合格窗口比例、已观察到的缺失/饱和比例、既有可信来源类别。数值用预定 `log1p`/比例表达；类别编码词表从训练折拟合，未知类别进入固定 unknown 桶。

不加入模型预测的配合度、旧 OOF 成绩、目标缺失掩码或受试者ID。问卷时间/版本未知状态主要进入限制表，默认不作为预测输入。

振幅敏感性单独使用所选窗口全头皮峰峰值中位数的对数。它不是纯粹的技术干扰；其控制结果只说明条件预测对调整方式敏感。

---

## 8. 模型矩阵：只保留这一个新方法对比

| ID | 模型 | 角色 |
|---|---|---|
| M0 | C 的训练内最佳有限基线 | 原始临床数字参照 |
| M1 | C+Q 的训练内最佳有限基线 | 技术摘要参照 |
| M2 | C+Q+片段特征均值，分块正则模型 | 固定EEG参照 |
| M3 | C+Q+MLP(片段均值) | 先汇总后学习 |
| M4 | C+Q+均值(片段MLP输出) | 先学习后汇总，候选主方法 |

M3/M4 使用同样的 `140→8→8` 映射，第一层 tanh、第二层线性，EEG 输出 `8→1`；约1209个局部/输出参数，不含临床分支。两者无 attention、BatchNorm、dropout、projector 或刺激辅助损失。两者架构、初始种子、输入与预算相同，拟合参数分别学习。

$$\widehat y_{M3}=b+c(C,Q)^\top\gamma+w^\top\phi_\theta(\operatorname{mean}_k u_k),$$

$$\widehat y_{M4}=b+c(C,Q)^\top\gamma+w^\top\operatorname{mean}_k\phi_\theta(u_k).$$

这是非线性映射与均值不交换的比较，不预设 M4 更好；集合表示基础不是新理论贡献。[R9]

### 8.1 训练与尺度

A/MUSS 依 HA 原列0–100范围缩放到0–1训练，报告回到原表分值。不把 MFF 的0–40混入，也不做新量表换算。记录级均方误差训练，主评价为MAE，补充RMSE；一个身份一条主记录、一个损失。不能将同一分数复制到32个窗口作为32个监督个体。

EEG 特征的中心和尺度按训练身份等权、窗口等权拟合。M3/M4 共享相同变换定义，绝不在全队列上做标准化/PCA。

输出统一裁剪到HA原列的0–100范围，未裁剪结果作为数值诊断保留，不择优。

### 8.2 优化与选择机会

- CPU、FP32、full-batch Adam，固定400步，学习率 `1e-3`。
- 神经权重L2候选 `0.01,0.1`；使用记录平均平方损失 `+lambda/2*sum(weight²)`，bias不惩罚；临床项的正则独立记录。
- M0/M1 临床基与惩罚分别在内层选择。M1选择出的临床规格统一用于该外折 M2/M3/M4，以控制比较自由度。
- M2 的 EEG 惩罚 `0.01,0.1,1.0`，另保留关闭EEG的M1候选；不得从测试表现决定是否回退。
- M3/M4 种子固定11、23；每个正则候选先将两种子验证预测平均，再计算内层 MAE选正则，最终也平均两种子预测。不能选最好种子。
- 主矩阵没有临床测试早停、没有为“达到收敛平台”反复追加epoch；保存有限预算算法的数值与训练曲线。
- 内层 MAE 数值并列时，按预先固定的顺序选择较简单基、较强惩罚或关闭 EEG 的候选；不得用外层风险决胜。

M1规格的内层选择与 EEG 候选使用同一组内折，是一个预定的两步训练内算法；外层预测是评价对象，不把用于多步选择的内层成绩当作无偏泛化成绩。每次内折的实际数值变换仍仅拟合该内折训练身份。

---

## 9. 验证与支持规则

主要五外折、每个外层训练集三内折，固定seed `20260919`。使用身份及资格清单分折，不按标签大小或历史预测结果搜索分割。重复访问必须跟身份一起隔离，即使本次只取一条主记录。

最低支持保留原有限模型的设置：总计30个可分析身份，外层训练至少24、测试至少4，内层训练至少16。此处是模型设计可执行性，不是临床功效保证。若不足，报真实人数，不按有利seed重分折，不把unknown日期或版本计作不合格。

F2在F1索引清单中取同源共标签子集，保留相同外折归属；若子集不足只停止F2。全目标恒定时不给“零误差成功”，输出不可区分目标；某训练折恒定时使用预定常数拟合并保留。

所有临床插补、标准化、候选选择及模型训练在对应训练身份内。单记录的全程QC和窗口均匀选择允许用于本次离线档案预测，但不能据此声称在线、前缀或提前停止性能。

主要区间：固定 OOF 的身份级2000次配对bootstrap，所有对比共享抽样索引。两种子已平均，不把种子、窗口、折或重复记录当新增人。区间不覆盖完整重训练/重划分不确定性，不是新队列临床验证。[R10]

---

## 10. 必做对照与结论规则

### 10.1 必做对照

1. M0–M4的绝对误差及三项主要配对比较全部报告。
2. 振幅敏感性：在技术Q中增加一个固定振幅摘要，重拟合M1/M4；冻结原外折选择，不再开新网格。另报相对原M0的误差，避免只对更差基线宣称改善。
3. 训练对应错配：在每个外层训练范围内，用固定seed生成无自配的记录包置换；整个32窗口包一起错配，不改变包内结构。使用原M4选定设置拟合，测试包不打乱。它只是内容诊断，不是正式条件置换p值。
4. 行键回归测试、身份隔离和目标污染测试，见下一节。

错配对照差不能替代超出M0/M1的证据。若真实与错配相近，也不能宣称真实CMI恰为零。

### 10.2 不新增的敏感性

不自动新增版本/时间分层回归、删满分分析、年龄切点、片段长度、频段、QC阈值或模型搜索。可以按现有证据层级描述人数和固定OOF误差；样本太少只列支持，不重新拟合或挑最有利亚组。

### 10.3 怎样解释结果

- M4优于M3但未优于M0/M1：不能称档案目标的额外EEG效用。
- M2已经足够、M4无优势：记录简单表征可用，不支持汇总顺序的方法贡献。
- 有小效应但不稳：保留幅度和区间，不自动追加架构/种子。
- 所有结果弱：只限制当前目标、来源、输入与有限算法，不宣布EEG无信息。
- 元数据未知：始终保留，不因某模型好就改称同期/标准量表。

**运行完毕之后再进行科学判断；不用结果好坏决定要不要完成预定对照。**

---

## 11. 有限实现检查

复用已有测试，不重跑所有历史测试/合成世界。新增检查仅围绕这次变化：

- 空工作表行、重复表头和输入表重排不改变实际源行关联；非空顺序号错配能被拦截。
- unknown量表版本、unknown问卷时间、unknown设备状态的合法档案行能够通过；明确身份或目标冲突不能通过。
- 使用一份“全部问卷日期未知、全部版本状态未知，但标签和身份可用”的合成输入，必须能够建立 `ARCHIVE_ANALYSIS_LOCK`；不允许代码继续隐式要求临床确认。
- 改变外层测试目标不能影响该折训练变换、超参数或模型哈希；测试数据列不参与填补训练缺失。
- M3/M4参数量与窗口相同，片段置换不改变输出；一个记录只计算一次临床损失。
- 片段复制不增加身份；非有限输入不能默默当零；目标不能被插补。
- 原始缺口不能被窗口跨越，短epoch拼接输入被拒绝；源单位和范围检查明确。

有限合成机制沿用3种、各4个seed：临床足够且EEG独立；片段均值决定目标；均值相近但片段分布关联目标。M3/M4各拟合一次，共24次。强均值机制要求两模型各至少3/4个seed相对均值预测降低MSE至少50%；分布机制要求M4满足对应可学习性，M3结果完整保留。独立机制不要求每次增益都负。

这些是实现可学习性与数值检查，不是临床功效或真实假阳性率证明。只允许一次明确原因的实现修复；不得看真实结果调整合成设置。一次后仍未通过则阻断对应模型任务，保留失败，不计为科学阴性。

---

## 12. 资源与数据保护

默认全部CPU，无GPU、新原始波形编码器或大型自监督预训练。

- W0（含准备/实现/测试）上限12 CPU core·h。
- W0+W1总上限96 CPU core·h，最多4个CPU作业并行。
- 两目标、M3/M4、五外折、三内折、两正则、两种子，最多280次主神经拟合；振幅及错配最多40次；合成24次，小神经拟合总上限360次。
- 临床与固定特征求解器调用总上限1000次，含内层与失败；先做任务目录和缓存等价求解，不能为记账或画图重拟合。
- 原始数据只读，源码/配置/索引/窗口和折可追溯；所有数值、测试、哈希和绘图经Slurm。
- 只核对实际使用的新输入与来源链，不再次把已核验的全部427文件/45任务当作一个科研工作包。

新命名空间：

```text
private/auditory_fn1a/<run>/
results/auditory_fn1a/<run>/
reports/auditory_fn1a/<run>/
docs/auditory_fn1a/
```

身份、精确日期、原始行、逐人分数、预测、窗口、权重和详细日志只在private；默认 `umask 077`。不联系医生或其他外部人员，不发送核对资料，不自动push。旧授权发布不涵盖新增个体数据。[R8]

---

## 13. 待实现 CLI 与配置

下面是新接口合同，不是已存在或已运行的命令。原FN1的外联入口不应被保留为隐藏依赖。

```text
python -m auditory_fn1a.cli prepare_archive --run <new_id> --config <yaml>
python -m auditory_fn1a.cli test --run <new_id> --config <yaml>
python -m auditory_fn1a.cli freeze_archive --run <new_id> --prepare <run> --tests <run>
python -m auditory_fn1a.cli export_segments --run <new_id> --freeze <run>
python -m auditory_fn1a.cli freeze_support --run <new_id> --freeze <run> --segments <run>
python -m auditory_fn1a.cli fit --run <new_id> --support <run> --target A_archive
python -m auditory_fn1a.cli fit --run <new_id> --support <run> --target V_archive_given_A
python -m auditory_fn1a.cli report --run <new_id> --sources <manifest>
```

### 13.1 默认配置

```yaml
project:
  name: auditory_fn1a
  version: "1.1"
  baseline_commit: 493a076a3848d3546a5889e2c583d0fee2ba1612
  initial_stage: W0_ARCHIVE_SETUP
  real_training_authorized: true
  auto_start_after_operational_checks: true
  external_contact_required: false
  new_clinical_data_required: false
  overwrite: false
  auto_publish: false

archive:
  scope: HA_single_source_archival_score_prediction
  analysis_lock: null  # prepare/freeze实际生成；不是等待医生的锁
  primary_target: A_archive
  primary_source_header: "IT-MAIS/MAIS得分（%）"
  secondary_target: V_archive_given_A
  secondary_source_header: "MUSS得分（%）"
  same_source_row_for_secondary: true
  target_bounds_source_units: [0.0, 100.0]
  target_imputation: false
  automatic_endpoint_substitution: false
  allow_unknown_instrument_version: true
  allow_unknown_questionnaire_date: true
  allow_unknown_eeg_questionnaire_relation: true
  allow_unknown_device_state: true
  unknown_time_imputation: false
  assume_same_visit: false
  infer_scale_from_age_or_score: false
  merge_HA_MFF_scales: false
  index_rule: reuse_frozen_earliest_supported_source_before_new_qc
  source_row_key: actual_worksheet_row
  corrected_pta_required: true
  historical_pta_table_allowed: false

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
  eeg_ridge_include_baseline: true
  neural_penalties: [0.01, 0.1]
  seeds: [11, 23]
  seed_aggregation: arithmetic_mean_prediction_before_selection_and_test
  optimization_steps: 400
  learning_rate: 0.001
  selection_metric: MAE_source_units
  test_early_stopping: false

validation:
  outer_folds: 5
  inner_folds: 3
  split_seed: 20260919
  min_total_groups: 30
  min_outer_train_groups: 24
  min_inner_train_groups: 16
  min_outer_test_groups: 4
  metadata_completeness_gate: false
  identity_label_signal_checks_required: true
  secondary_reuses_outer_assignments: true
  bootstrap_repetitions: 2000
  bootstrap_scope: fixed_oof_identity_paired_not_pipeline_refit
  effect_or_significance_execution_gate: false
  expand_after_small_positive: false

resources:
  setup_cpu_core_hours_cap: 12
  total_cpu_core_hours_cap: 96
  gpu_hours_cap: 0
  neural_fit_cap: 360
  linear_solver_call_cap: 1000
  max_concurrent_cpu_jobs: 4
  forbidden_gpu: [P100]
```

### 13.2 门控行为

`prepare_archive` 只使用已有资料和修正关联，不计算新 EEG—目标相关性以选人。`freeze_archive` 生成当前对象的来源锁，不会创建虚假的临床确认；UNKNOWN时间/版本必须被接受并进入限制表。

`fit` 检查：档案清单来源、目标数值、身份隔离、真实信号、窗口/训练支持、测试通过、预算和快照。**不检查“医生是否回复”“全部问卷日期是否存在”“所有版本是否确证”。**

不要复用旧 clinical gate 导致这些隐含条件重新出现。若旧模块要求临床确认，写新的适配层或新入口；保留旧实现不改。

### 13.3 Slurm 提交形状

新建并测试 `slurm/auditory_fn1a_cpu.sbatch` 后按下列形状提交；占用过的run名不能重复使用。

```bash
umask 077
sbatch --cpus-per-task=2 --mem=8G --time=00:20:00 \
  slurm/auditory_fn1a_cpu.sbatch prepare_archive \
  --run FN1A_prepare_<new_id> --config configs/auditory_fn1a.yaml

sbatch --cpus-per-task=2 --mem=8G --time=00:40:00 \
  slurm/auditory_fn1a_cpu.sbatch test \
  --run FN1A_tests_<new_id> --config configs/auditory_fn1a.yaml

# freeze_archive通过后直接进入信号导出，无需医生回复。
sbatch --cpus-per-task=2 --mem=16G --time=01:00:00 \
  slurm/auditory_fn1a_cpu.sbatch export_segments \
  --run FN1A_export_<new_id> --freeze FN1A_freeze_<id>
```

W1由任务清单提交，并依赖实际通过的支持回执，不把“作业已排队”当作“检查已完成”。报告入口不得调用训练。编写本文件不等于已经连接服务器或提交这些作业。

---

## 14. 交付与终止状态

### 14.1 必交付

```text
ARCHIVAL_SCOPE_AND_LIMITATIONS.md     # 字面标签、未知版本/时间、可允许结论
SOURCE_REUSE_AND_PTA_BINDING.md       # 只列本轮依赖，不重审全库
archive_analysis_lock_summary.json
cohort_flow.csv
segment_support_summary.csv
implementation_tests.json
STAGE_STATUS.json
```

不再交付医生询问草稿或等待回复清单。私有档案行清单与关联证据保持受限。

### 14.2 真实实验完成后

```text
model_metrics.csv
paired_effects.csv
technical_amplitude_controls.csv
fold_and_seed_summary.csv
fit_ledger_summary.json
ARCHIVAL_RECORD_LEARNING_REPORT.md
```

每个目标报告所有M0–M4绝对MAE/RMSE、固定OOF区间、外折误差、满分分布、身份影响范围；同时说明入组记录中时间/版本未知的计数。正文不能把档案关联重命名为同期评估。

### 14.3 允许的最终状态

| 状态 | 含义 |
|---|---|
| `ARCHIVE_ANALYSIS_LOCKED` | 现有档案问题定义完成，不表示临床元数据全确认 |
| `SOURCE_LINKAGE_CONFLICT` | 明确错人/矛盾或来源值冲突影响对应分析 |
| `TARGET_DATA_INSUFFICIENT` | 原列标签缺失、冲突、常数或单位无法构成当前数值任务 |
| `DESIGN_SUPPORT_INSUFFICIENT` | 实际身份/窗口支持不足，不是资料版本未知 |
| `CONTINUOUS_SIGNAL_SUPPORT_LIMITED` | 不能形成预定真实连续输入 |
| `IMPLEMENTATION_UNRESOLVED` | 有限排错后仍存在实现/数值问题 |
| `W1_COMPLETED_ARCHIVAL_EXPLORATORY` | 预定档案矩阵完成，不区分“显著成功/不显著失败” |

**没有 `NEEDS_CLINICAL_RESPONSE` 结束状态。** 未知日期、量表版本或设备状态只能进入限制字段，不能被单独用作本轮整体停止理由。

完成后不自动再训练旧任务或生成新模型搜索队列。当前资料的固有限制持续存在；若以后另有新数据，那是另一个研究版本，不是本轮的等待条件。

---

## 15. 可直接交给服务器代理的指令

> 执行本完整修订版 FN1-A v1.1。医生已经给出他拥有的全部材料，本轮不能再依赖联系医生、新回复、补问卷、额外设备日志或新采集。不要生成外联草稿，不要重复扫描同一材料来拖延，不能以问卷时间或量表版本未知为由将所有样本判为零资格。
>
> 保留旧FN1 v1.0和历史结果不变。本版明确将对象改为现有HA原表数字的离线档案关联：主目标为IT-MAIS/MAIS列的 `A_archive`，次要为同一档案行已知A时预测MUSS的 `V_archive_given_A`。不得声称这些数字属于已确认的同期临床评估，不能推断未来或因果效应。UNKNOWN保持UNKNOWN，不填成同日、不按年龄猜量表、不把MFF的0–40混进HA。
>
> 先复用修正后的实际工作表行键、PTA和既有身份/最早来源索引，建立 `archive_analysis_lock`。57/52/49等历史队列只作来源导航，不为了缓存方便机械沿用；不按模型成绩选人。真正错配、目标冲突和信号不足可阻断相应记录，普通元数据未知不阻断。档案锁和实现检查通过后，直接继续信号导出、支持冻结和W1，无需新的人工/临床确认。
>
> 使用真实连续HA EEG，固定4秒窗口、不重叠，每记录32个均匀无放回窗口。不能拼接旧短epoch。每窗口140维固定特征，比较同一输入下M0–M4；M3/M4相同小网络和预算，只改变非线性映射相对汇总的位置。记录级损失，五外折三内折，训练身份内拟合变换与选择；不能退回旧五角色切分。
>
> 预定模型、振幅和训练对应错配对照全部完成，不按中途增益、p值或区间取消任务，也不因小正值追加架构、seed或终点。F2共标签支持不足只停止F2。不重开旧D/null、事件分类、N1/N3、P0/N2R/R3或F3/F4。
>
> 全部计算通过Slurm，默认CPU，遵守12/96 CPU core-hour准备/总预算及拟合上限。模型、个体标签/预测、日期和来源行留private。报告/核验不重拟合，不联系外部人员、不自动push。最终交付真实支持、完整结果与永久保留的档案限制，而不是一份等待医生回复的报告。

---

## 16. 引用与证据入口

下列引用沿用原 FN1 的证据基线。历史说明与该基线的完成状态冲突时，以相应最终报告为准；本次修订没有重新检索后续提交。

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

**编写范围说明：** 本次修改依据已提供的 FN1 文档、既有仓库报告与用户新增约束；没有获取新的医生信息、假造时间/版本、读取个体 EEG、修改 GitHub 或提交服务器作业。上述引用固定于既有证据版本，不声称本次重新审阅了仓库后续提交。
