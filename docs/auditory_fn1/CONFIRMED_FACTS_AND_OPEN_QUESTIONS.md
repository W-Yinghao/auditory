# FN1 W0：已确认事实与尚存缺口

规则（方案 §3.1）：**已经明确的字段不再提问；只列会改变当前研究对象的缺口。** 每条事实标注其来源产物。本文件不含姓名、日期、逐人分数或身份键。

---

## A. 目标身份（哪一行用哪个量表、哪个版本）

### 已确认

| 事实 | 来源 | 范围 |
|---|---|---|
| 原始说明文档**确有**四种量表的计分规则：IT-MAIS（逐项 0–4，总分 40，百分比 = 总分/40×100）、CAP-II（0–9，10 个序级）、MUSS（10 项 × 0–4，百分比同上）、SIR（1–5） | `docs/auditory_fseries/SOURCE_DOCUMENT_AMENDMENT_001.md`；机读于 `results/auditory_fseries/document_evidence_002/summary.json` → `declared_scale_definitions` | 4/4 种量表 |
| 但每条定义都显式携带 `row_assignment: "not_established_by_this_document"` | 同上 | 4/4 |
| HA 主表四个量表列**数值完整** | `results/auditory_fseries/ha_qualification_002/qualification_summary.json` → `scale_definitions` | 84/84 行 × 4 列，缺失 0 |
| 天花板计数（按 84 行分母） | 同上 | IT-MAIS/MAIS 43/84 为 100；MUSS 27/84 为 100；CAP 25/84 为 9；SIR 26/84 为 5 |
| "跨表无量表信息"这一旧前提已被撤回 | `SOURCE_DOCUMENT_AMENDMENT_001.md`；`docs/clinical_audit_notes.md` | — |

### 尚存缺口

**Q1.1（阻断主终点）** — HA 主表的合并列 `IT-MAIS/MAIS得分（%）` 中，哪些原始行用 IT-MAIS、哪些用 MAIS，依据什么规则？
- 可关闭它的证据：施测者对**一批可指认的原始行**给出批次级说明（方案 §3.2 接受批次说明，但必须记录说明者、原始依据、适用行范围、例外与不确定性）；或逐行标注。
- 当前回退状态：unknown（`version_status: unresolved_from_registered_header`，`primary_endpoint.status: not_frozen`）。
- 影响：**84/84 HA 临床行**，并向下传播到 57/56 身份的档案队列与 52 组 D 支持。

**Q1.2（非阻断，超出本轮 HA 范围）** — CI/MFF 扩展表中百分号表头下的 0–40 值，是被误标表头的原始总分，还是恰好 ≤40 的百分比？当前状态 conflict，不做任何换算。

**Q1.3** — 同一候选身份对同一终点出现两个不同字面值时以哪个为准？当前保留为 conflict，不平均、不择优。涉及 IT-MAIS/MAIS 1 个、MUSS 2 个、CAP 1 个、SIR 1 个身份组。

### 不必再问

1. **"请提供所有量表定义/计分手册"**——方案 §1.4/§3.5 已明确关闭；四种量表的计分规则都在已交付文档中。
2. "档案里到底有没有量表数值"——84/84 行四列齐全。
3. "IT-MAIS/MUSS/CAP/SIR 的理论满分是多少"——40/40/9/5，已记载。
4. "CAP 在我们数据里的上限"——约定已固定为报告**观测**最大值而非理论上限。

---

## B. 时间关系（问卷日期与 EEG 的关系）—— 本轮唯一的阻断项

### 已确认

| 事实 | 来源 | 范围 |
|---|---|---|
| 每条 HA/BDF 记录都有厂商采集时间 | `ha_qualification_002` → `EEG_clinical_temporal_linkage` | 93/93 记录有 exam time 与 start record time |
| HA 工作表**没有**问卷评估日期列，也**没有**阈值日期列 | 同上 → `threshold_evidence.*.date_status` | HA Sheet1 全部 |
| 原始文档经人工复核**没有**评估日期、EEG–评估间隔或同次评估陈述 | `document_evidence_002/summary.json` → `assessment_time_evidence` | 2 份文档 |
| 每条候选 EEG–临床链接的日期状态都是 unknown | `ha_qualification_002` → `clinical_link_date_status_counts` | **95/95 unknown** |
| 链接证据等级 | 同上 → `clinical_link_evidence_counts` | name+label_date 81，name_only 14 |
| 不存在任何"间隔天数"字段 | 同上 → `nonmissing_EEG_clinical_gap_days` | **0** |
| 姓名后缀中形似日期/设备的字符串只是标签证据 | `docs/clinical_audit_notes.md` | 95 行中 87 个形似日期、81 个形似设备 |

### 尚存缺口

**Q2.1（本轮最阻断）** — 表内那个日期（或姓名后缀里的日期）指的是问卷施测、EEG 采集，还是两者都不是？
- 可关闭它的证据：临床方说明该日期字段记录的是什么，按可指认的批次给出。
- 当前回退状态：95/95 unknown。**这一项单独使本轮停在 `W1_BLOCKED_CLINICAL_LOCK`。**

**Q2.2（同样阻断）** — 对某一批原始行而言，问卷与 EEG 是否属同一次临床评估？若否，实际评估日期或可证实的区间是什么？
- 可关闭它的证据：批次级同次评估陈述；或日期区间 + 临床负责人在**查看新 EEG 关联之前**确认适用的 `time_window_rule`（方案 §3.3）。
- 硬约束：没有时间证据时**不得**把间隔设为零，**不得**虚构 30/90 天容差。

### 不必再问

1. "有没有 EEG 采集时间戳"——93/93 有，且可解析。
2. "哪一次是某个孩子最早的记录"——最早采集规则已冻结，且在任何质量或结果门之前应用。
3. "重复文件是否意味着重复就诊"——已裁定为**未确认就诊**（70/70 行记为 `acquisition_repeat_candidate_not_confirmed_visit`）。
4. "是否存在 EEG 与问卷的间隔字段"——不存在，表和文档里都没有。

---

## C. 身份与来源

### 已确认

| 事实 | 来源 | 范围 |
|---|---|---|
| HA 档案漏斗及逐项排除原因完整可复现 | `results/auditory_fseries_archival/prepare_001/summary.json` | 93 → 61 → 57 → 56；排除 `link_not_unique_name_labeldate: 4`、`fewer_than_64_accepted_epochs: 1` |
| 当前 56 条记录每条都有**已确认的工作表行链接**，并对原始姓名加四个临床字段做过交叉核对 | `docs/auditory_fseries_archival/LEGACY_PTA_LINEAGE_AMENDMENT.md` | 56/56 |
| 仓库中**没有任何身份被标为 confirmed**；所有身份表都是候选级 | `results/linkage_001/participant_index.csv`（78 行全 `candidate_name_group`）、`results/phase1_final_001/measurement_candidate_groups.csv`（70 行全 `candidate_only`） | 按方案 §3.4 的词汇：0 confirmed，全部 ≤ supported_candidate |
| 具体的重复/合并风险已逐项计数 | `docs/phase0_report.md`；`participant_index.csv` | 91 个 PatientGUID → 78 个姓名簇；11 个簇有多个 GUID；2 个簇有不同出生日期串 |
| MFF 来源身份歧义收敛到很小的残余 | `results/phase3_metadata_addendum_001/source_metadata.csv` | 203 条中 `ambiguous_multiple_participants` 仅 **2** |

### 尚存缺口

**Q3.1** — 2 条按完整拼音精确匹配到多于一个参与者的 MFF 来源，正确的是哪一个（或是同音）？当前为 conflict，已排除在候选级索引之外。
**Q3.2** — 11 个携带多个 PatientGUID 的姓名簇（及 2 个携带两个不同出生日期串的簇），是同一个孩子重复登记，还是不同孩子？当前分别为 supported_candidate 与 conflict。这直接决定身份级外折是否真正隔离了儿童。
**Q3.3** — 是否存在我们从表本身无法察觉的已知错人、重复导出或就诊混淆？只处理当前未解冲突。
**Q3.4** — 1 个解析出两个不同出生日期、已被 `ci_prepare_004` 排除的身份，是一个孩子还是两个？

### 不必再问

1. "能否帮我们把 EEG 记录关联到工作表行"——已完成并独立验证。
2. "数据集里有多少个独立儿童"——不能作为计数问题提出，且已冻结为"无法从现有记录判定"。只问具体的未解冲突（Q3.1/Q3.2/Q3.4）。
3. "表名/文件名是不是诊断标签"——已裁定不作此推断。
4. "请重扫 203 份 MFF"——方案 §3.1 明确禁止。

---

## D. 阈值与设备背景

### 已确认

| 事实 | 来源 | 范围 |
|---|---|---|
| HA 表有双耳裸耳与助听 500/1000/2000/4000 Hz 阈值，共 16 个已登记列 | `ha_qualification_002` → `threshold_evidence` | 16 列 × 84 行 |
| 单元格级完整度已测 | 同上 → `profiles_HA` | 裸耳右 328/336、裸耳左 328/336、助听右 280/336、助听左 276/336 |
| **PTA 行键已修正且保证明确**：`C####` 解析到实际工作表行；当前读入器重读原始工作表行并交叉核对姓名 + 四个临床字段 | `LEGACY_PTA_LINEAGE_AMENDMENT.md`；本轮 `prepare_request` 实测 `{0: 57}` 对齐 | 保障 56 条记录的筛查与 57 候选/52 组支持 |
| 历史错误规模 | 同上 | 57 条比较中 55 条较好耳裸耳 PTA、47 条助听 PTA 改变 |
| 修正后的下游后果 | `results/auditory_repair/pta_007/summary.json` | 裸耳完整 54→55、助听完整 45→44；D 支持 51→52（+3/−2）；60 个外层身份组中 **37 个换折** |
| 阈值**单位在行级未确立**，只有文档级 dB HL 背景 | `ha_qualification_002` → `unit_status`；`docs/phase3_report.md` | 84 行 |
| **采集时设备供电状态普遍未确立**，且记为类型化字段而非散文 | `results/phase3_metadata_addendum_001/source_metadata.csv` | `device_power_state = not_established` **203/203**；`wearing_evidence = unknown` 200 |
| 确实存在的少量佩戴线索已逐条枚举并限定 | `phase3_metadata_addendum_001/summary.json` | 6 条临床自由文本行、5 个同日来源、1 条"约 8 分钟后加戴 HA 并出现不适"的注意标记（时间原点未锚定到 EEG 时钟，不据此裁剪 EEG） |

### 尚存缺口

**Q4.1** — 裸耳/助听阈值列的单位是什么（dB HL？），各自在什么条件下测得（行为/自由场/插入式；助听是戴哪一台）？当前行级 unknown。**这决定结论能否写成"超出同期完整可听度评估"，还是只能退为"超出已记录的临床变量"。**
**Q4.2** — 采集期间助听器是否佩戴并开启，是否有中途变化记录？当前 203/203 未确立。按 §3.3，未知**不自动**成为 F1 的排除项，但禁止设备获益或条件因果解释；仅在**已知**中途变化处按预定规则分段或排除，绝不按模型成绩挑片段。
**Q4.3** — 阈值相对 EEG 与问卷的测量时间？无该列。与 Q2 **分开**处理：PTA 日期缺失限制措辞；问卷日期缺失决定功能目标是否有时间意义。
**Q4.4（低优先）** — 每日佩戴时长的单位？仅 **16/84** 行有值，该覆盖度下无法成为协变量。

### 不必再问

1. "你们有听力阈值吗"——有，16 列 84 行，单元格级完整度已发布。
2. "旧的 PTA 还能用吗 / 能否帮我们重算"——行键错误已发现、量化、修正并冻结。要问的是**单位与条件**，不是数值。
3. "这些记录的设备状态是不是未知"——203/203 已确立为 `not_established`；有用的问题是 Q4.2。
4. "请描述 EEG 采集装置与刺激方案"——已记载；其中真正缺的触发码映射与预处理规则按方案 §2 属本轮关闭课题，不是 W0 的临床问题。

---

## E. 两份文档之间需要注意的不一致（不隐藏，如实并列）

1. **源行改变计数 55 vs 57。** `legacy_lineage_001/mapping_summary.json` 记 `source_row_delta_nonzero: 55`、`rows_with_any_difference: 57`；`pta_007/summary.json` 记 `source_row_changed_n: 57`。定义不同（行号数值差非零 vs 任意字段有差异），两者对 **55 条裸耳 / 47 条助听 PTA 改变**的记载一致。本文件同时引用两者，不择一。
2. **两个规模接近但不同的档案队列。** 修复轮用 **57** 个候选身份（纳入标准：每个字面事件码 ≥2 个可用试次）；F 系列档案筛查用 **56** 个（纳入标准：≥64 个已接受 epoch）。不得合并或互指。
3. **天花板计数存在四个不同分母**（84 行、57 身份、53 旧队列等）。本文件统一使用 84 行分母，并注明。
4. `AGENTS.md` 中"161 个未知来源组"已被其后一条取代为 **155 未知 + 6 literal normal**。
