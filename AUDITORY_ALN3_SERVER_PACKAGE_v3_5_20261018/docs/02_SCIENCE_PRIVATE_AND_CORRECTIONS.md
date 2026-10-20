# ALN3.5：声音内容、时间组织、私有儿童与定点勘误

版本：2026-10-18。审阅基准：`W-Yinghao/auditory`，commit `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`。这是 ALN3.4 的执行增补；现场先记录实际 HEAD、注册表和队列，不能把本文列出的发布快照当作实时作业状态。

本节的研究问题是：**群体听觉学习让哪些当前声音证据更容易从新听者 EEG 中读取；哪些读取关系可以跨时间位置共享；个人支持在什么条件下改善或扰乱这些关系？** 私有儿童继续回答其中的任务迁移、当前声音与历史、支持需求问题。概率校准修复只是其中一个接口工作。

本节不启动服务器作业。Server 接入后按既有授权执行可用分析、必要的推断和已注册依赖；不需要另行批准科学措辞。所有 GPU 工作共同遵守现有 10-GPU 上限。

## 1. 本轮明确执行的事项

1. 为 native 私有 local/旧 public-transfer 的 `pre` 建立**解释勘误记录**，保留原始值、单位 ID、缓存与历史报告；从真实刺激前分析中排除这些全零条件。后刺激结果照常使用。
2. 从生产 unit 的 `per_participant` 读取真实成对结果，执行 `../plans/science_contrasts.json` 中的小规模新增对比。不能从 aggregate 的均值、SE 或单独区间倒推出配对区间。
3. 固定 seed3401 的 public-prior 科学比较；native DTU 内容/时间使用已经齐全的 3401/3407/3413，FAU/Federici 使用既定 3401。先复用现成数据，不为新的文字结论重训模型。
4. 内容报告保留 env、history-residual、onset、spec、flux、Ac、Lz 的已有有效结果；新增推断集中在指定内容和少量时间差，不扩成全部模型×全部时间×所有人群矩阵。
5. 在现有表征上补一个同等 source 校准的 history-only 接口，以及严格异 block 的 history-matched twin 分析，明确共同支持范围和缺失原因。
6. 保留正在完成的 private factorial、prior LOO、private episode 及实际存在的科学依赖。先对账、复用、补真缺项，不恢复旧失配执行，也不把本节的勘误变成全项目暂停理由。

## 2. 已知证据：用来提出问题，不用来选择有利儿童或窗口

以下是审阅快照的已有结果，**不是 ALN3.5 新跑出的结果**。统计单位为独立听者/儿童；seed、content fold、session 都在人内处理。

### 2.1 公开声音内容已经有实质可读性

`results/auditory_alignment_v3/aln34/science_v2/science.json` 的 DTU、真全量 CBraMod pretrained、NCE、三 seed、44 人，在预先存在的 `0/0` 单元：

| 目标 | 平均 r | 该 25 格时间矩阵的同时 95% 区间 |
|---|---:|---:|
| env/direct | 0.15581 | [0.13158, 0.18004] |
| env/history_conditional | 0.11059 | [0.09322, 0.12795] |
| onset/conditional | 0.10782 | [0.09294, 0.12270] |
| spec/conditional | 0.05299 | [0.04415, 0.06182] |
| flux/conditional | 0.09362 | [0.07714, 0.11010] |
| Ac/conditional | 0.05061 | [0.04104, 0.06018] |
| Lz/conditional | 0.02209 | [0.01571, 0.02846] |

FAU 相应模型的 history residual r=0.07479、spec residual r=0.03257、flux residual r=0.04845，均有正向同时区间；覆盖 67 人、seed3401。Federici 只有包络合同：CB env/direct r=0.12271、history residual r=0.04710，86 人、seed3401。不能为 Federici 的 2–8 Hz 缓存补写不存在的谱、Ac 或 Lz 结果。

这些结果支持继续问“哪类内容的读出受先验/适配影响”。它们不证明独立语言源，也不与 SCI_R2 原来的逐步 predictor 增量互相替代：**从 EEG 预测残差化声音目标**，与**在一个预测模型中增加 predictor 后的真实风险变化**，是两个不同对象。

### 2.2 新先验已经改变私有当前声音的线性可读性

来源：`results/auditory_alignment_v3/aln34/prior_science/science.json`；`private/windows/{arm}/NCE`；seed3401；64 儿童（HA55、NH9）；统一 source-ES 线性 probe。

| 条件 | S AUC | AP AUC | 已有 AP−S 差 | 原 4 臂×4 窗同时 95% 区间 |
|---|---:|---:|---:|---:|
| 0_200 | 0.51571 | 0.52734 | +0.011629 | [−0.002249, +0.025506] |
| 200_400 | 0.51672 | 0.52806 | +0.011337 | [−0.000447, +0.023121] |
| 400_600 | 0.50184 | 0.50665 | +0.004804 | [−0.006046, +0.015654] |
| full | 0.52835 | 0.54927 | +0.020922 | [+0.008305, +0.033539] |

实际最后 EEG 样本时间是 578.125 ms；`400_600` 是保留的逻辑标签。J* full AUC=0.54492，XM=0.54008。J*−S、XM−S 的现有同时区间也为正，故 **AP−S 不能单独识别正确声音配对的特异效应**。AP−XM 是两个特定先验训练包的比较；XM 的任务/目标几何与 AP 不完全相同。针对配对机制的新增 APwrong 对照另见本包公共先验计划，不能把 AP−XM 改名成纯配对消融。

AP 的 full history gain 绝对值为 +0.00200 bits/trial，原同时区间 [−0.00530, +0.00931]；相对 S 的改善为 +0.003792 [0.001280, 0.006304]。这意味着先验把指定历史条件读出向有利方向推动；**绝对历史基线之外的稳健收益尚未建立**。两个判断应同时保留。

### 2.3 个人支持并未自动转为收益

native 私有新科学、同一末 70% query、output-rank4 固定 20 步，三 seed、64 儿童，正值为 NLL 改善：local NCE 在 10% support 为 −0.006433 bits/trial [−0.010075, −0.002791]，30% 约为零；CB pretrained NCE 在 10% 为 −0.000979 [−0.001427, −0.000531]，30% 接近零。它们与公共少支持适配问题有关，但不能据此宣称儿童都不适合适配。

现有 10% 与 30% 使用前 10%/30% 物理 block，也同时改变了支持的时间覆盖、类别和历史覆盖。ALN3.5 的支持设计应从同一前 30% 区域取可复现的不同数量子集，保持末 70% query，再区分数量与覆盖；不直接把现有曲线命名为纯样本量效应。

## 3. 勘误 SCI35-C01：native local 的刺激前条件实际为全零

### 3.1 独立核对的代码链

| 文件与位置（基准 commit） | 实际行为 |
|---|---|
| `auditory_alignment/model.py:8–12` | private `full=(0,600)` |
| `auditory_alignment_v2/temporal.py:29–41` | 以 onset offset=50 转为 250 Hz 半开样本范围 |
| `auditory_alignment_v2/train.py:263–284` | local 缓存先裁为原 epoch 样本 `[50,200)`，实际是后刺激数据 |
| `auditory_alignment_v3/aln34/private_current_time.py:68–75` | `pre=(-200,0)` 的 mask 选择原 epoch `[0,50)`；与 local patch `[50,200)` 没有交集 |
| `auditory_alignment_v3/aln34/private_current_time_v2.py:75–84` | v2 复用原提取器与缓存，仅修复校准数值执行；输入问题保持不变 |
| `auditory_alignment_v2/train_fm.py:215–223` | FM batcher 恢复完整 epoch，因而 FM 的 pre 确实有数据 |

这是一项输入支持事实，不依赖 AUC 是否正好为 0.5。全零输入在不同 batch 大小/浮点路径下可能产生极小数值差，不能把其排序波动当生理结果。

### 3.2 受影响的精确依赖

- 数据集：`private_bdf`。
- families：`E_LOCAL`、旧 `E_PUBLIC_TRANSFER`；architecture/source_architecture=`lag_local_tokens`；objectives=`NCE`、`CS_SINGLE`；full/task_partial 的所有已注册 seed/fold。
- 单窗口：`per_participant[id].windows.pre` 的全部指标。
- TG：`temporal_generalization` 中 source 或 destination 为 `pre` 的全部单元，两种校准都受影响。
- 衍生物：以上条件的整体/HA/NH汇总、组差、图例、使用这些条件作为“刺激前信息”或真实 pre 对照的叙述。
- **不在本次勘误内**：同模型的三个后刺激窗口、full 后刺激读取、private support/query 适配、full-window 年龄/佩戴时长端点；FM 的真实 pre；public CONTENT_TIME；新 prior 科学的三窗口与 full。

### 3.3 执行顺序与输出

1. 解析现场旧计划、unit 与缓存 metadata；以 `bt.lo`、`bt.W` 和实际 mask 的样本交集核对每个受影响配置。只做输入支持/元数据核对，不重训。
2. 写新记录到 `results/auditory_alignment_v3/aln35/science/correction_manifest.json`，保留旧 source path、SHA256、unit ID、原窗口名和原数值引用。
3. 将新报告中的解释标签改为 `all_zero_input_control_no_pre_access`，`valid_for_pre_event_inference=false`。旧输出仍能作为数值/接口对照查阅，不当作真实 pre 证据。
4. 图表若保留该单元，必须直接标“无刺激前输入”；若图表只呈现生理时间条件，则不绘制该单元，并列出排除原因。不能用补零替代 missing/unsupported。
5. 不修改旧 `plan.json`、旧 hash、旧 unit。必要的源码更正使用新版本和新执行 ID。原 registered family 的历史区间保留；ALN3.5 的后刺激新增 family 单独标 exploratory。

每个 correction item 至少包含：`correction_id, source_commit, source_unit_id, source_record_sha256, dataset, upstream_family_id, objective, architecture, seed, subject_fold, condition, original_label, resolved_input_samples, requested_mask_samples, retained_sample_count, effective_access_ms, affected_metric_paths, valid_for_pre_event_inference, unaffected_conditions, action, checked_at`。

### 3.4 同 access 的比较规则

native private full：local/旧 transfer 约 0–600 ms；FM 完整 −200–600 ms。比较 CB pretrained 与 CB random 是同架构、同访问；直接把 CB full−local full 归为架构/预训练收益不成立。已有共同后刺激 mask，或在既有 FM checkpoint 上增加 `post_only` forward，只匹配**评价时**的 EEG 访问，可用于评价访问敏感性；FM 在 target 训练中已见过刺激前数据，这一步不会消除训练访问的差异。必须保留原 full，并将新推断明确标为 `evaluation_post_only_training_access_unchanged`。

若研究问题要求将跨架构差异归于模型/训练包，必须同时匹配 target 训练、选择与评价的 EEG 访问，并记录各阶段合同。先查找已合法完成且 target 训练本身为 post-only 的来源；如没有，只在这个归因问题确实需要时登记限定的新训练条件，沿用现有授权与 10-GPU 上限，不展开全模型矩阵。不能用补一次 post-only forward 代替训练访问匹配，也不能把评价敏感性结果重新命名为全流程访问匹配。

新 private prior 的 S/AP/XP/J*/XM 是同一 64 Hz、38 样本后刺激合同，可直接配对。native private 的数值不能与该新 prior 的数值拼成同一个控制表；FS、输入长度、训练阶段、读出均不同。

## 4. 科学输入与主方法输入必须区分

| 证据层 | 生产来源 | 评价对象 | 不能混用的对象 |
|---|---|---|---|
| 主 TF/5 s 方法结果 | 原方法 unit 与其官方汇总 | 已注册 native/unified 任务风险或检索结果；服从各自 query 定义 | 不能用下行 probe AUC/r 代换，也不能以单位名中有 full 就认为访问一致 |
| Native public 内容/时间 | `core.OUT/aln34/content_time_v1/units/*.json` | 5 s segment 内 8 anchors；固定表征的 source-fit/ES ridge；每个单元 r/MSE | 不是另一次 5 s 检索结果；不是在线或神经潜伏期 |
| Native private 科学 v2 | `core.OUT/aln34/private_current_time_v2/units/*.json` | 冻结原 source 后重新拟合的线性/current-history读出与掩蔽/固定适配 | 不等于原模型 native class score；local pre 无访问 |
| New-prior 科学 | `core.OUT/aln34/prior_science_v1/units/*.json` + `bindings/*.json` | seed3401 core prior 的固定表征 probe，public env/onset/history 与 private三窗/full | 不等于主 prior 三seed native结果；无public spec/flux/Ac/Lz合同、无private pre |

`core.OUT` 必须从现场 `auditory_alignment_v3/core.py` 解析。不要把本文示意字符串直接当绝对路径，更不能在 public clone 中猜私有数据路径。

### 4.1 精确数值读取路径

- New-prior private：`unit.source` 绑定 upstream row；值为 `per_participant[identity].windows[window][metric]`。window=`full/0_200/200_400/400_600`；metric=`auc/history_gain_bits/history_minus_twin_bits/nll_bits`。
- New-prior public：`decoding[representation + '/' + target][train_center + '/' + test_center].per_participant[record_id][metric]`。本轮只用 `model/env/direct` 和 `model/env/history_conditional` 的 `0/0`；onset existing levels保留但不再全扫。
- Native public：相同 `decoding` 结构；source 选择由 `content_time_v1/plan.json` 的真实 rows 绑定。CB pre/random 使用 `full_onestep_v1`、backbone LR=3e-4；local=`local_aligned1000`；不重新按本轮结果选 LR。
- Native private v2：同 private `per_participant` 结构；检查 `execution_version`、`reused_from` 与 `unit.previous_id`，不能把合法 v1复用计为新独立观测。
- 组、身份、年龄/佩戴时长来自现有授权 manifest 与原 `E_LOCAL/NCE/3401` unit；不从文件名或组别猜身份。Federici 用既有 identity manifest先聚合 session；HC-v保持单独身份，phantom排除。

仅有两个 aggregate `science.json` 时，能核对点估计和旧区间，**不能计算新配对区间**。它们没有 per-child values 或联合 bootstrap draws。先读取现场现存 unit；若某 scope 的 unit 已不在，只标真实依赖并处理其余 scope，不用独立 CI 相减。

## 5. ALN3.5 的有限新增对比

所有本节新增对比标记为 `exploratory_after_2026_10_18_review`。它们未在 ALN3.4 结果产生前注册；不能回写成原 preregistered 结果。比较清单见 `../plans/science_contrasts.json`，该文件是**声明性绑定清单，不是可直接提交的生产任务或 CLI spec**。

### 5.1 Private：先验特异性与时间分布

固定 private NCE、seed3401、共同64儿童预期名册，统一线性 probe。

- 一个 AUC family，恰好4项：`AP/full−XM/full`、`J*/full−XM/full`、`AP/0_200−AP/400_600`、`AP/200_400−AP/400_600`。
- 一个 history-gain family，2项：AP−XM、J*−XM，均 full。
- 一个 history-minus-twin family，2项：AP−XM、J*−XM，均 full。此指标与绝对 history gain分别解释。
- 一个 HA−NH 改善差 family，2项：`(AP−XM)_HA−(AP−XM)_NH`、`(J*−XM)_HA−(J*−XM)_NH`，full AUC。不是先在HA和NH分别检验再比较p值。

已有 AP−S、J*−S、XM−S 及各窗 level作为上下文完整显示，不为达到阳性而选择 family 成员。CS existing levels保留；本轮不按CS某单格有利就新增同一批扩展检验。若后续需专门研究CS，另写明确问题与合同。

### 5.2 FAU：直接检验群体的改善差

固定 public-prior NCE、seed3401、`model/env/history_conditional`、`0/0`。只新增两个直接效应差：

\[
\{r(AP)-r(XM)\}_{HA}-\{r(AP)-r(XM)\}_{TH},\qquad
\{r(AP)-r(XM)\}_{CI}-\{r(AP)-r(XM)\}_{TH}.
\]

FAU 预期67独立身份（ha29、ci24、th14），各人先完成两contentfold配对，再形成个体改善。两项共用TH组的 bootstrap draws；不能把它们当两套独立实验。这个比较仍是特定先验包差异，不是HA/CI治疗效应，也不是纯声音配对机制。

### 5.3 Native public：把内容收益定位到少数固定对象

固定 DTU三seed、FAU seed3401，对 `0/0` 的 `env/history_conditional`、`spec/conditional`、`flux/conditional`，各比较：CB pretrained−CB random；CB pretrained−同access local。共6项 r 差，按dataset分别一个family。CB初始化比较首先回答同架构的先验差；CB−local是同EEG访问的模型/训练包差。

Federici 只有 env/history_conditional，固定seed3401，仅保留同样两项比较。不得补写 spec/flux 或把 HC 与 HC-v 凑为同人重复。

env/direct、onset、Ac、Lz 的已有全矩阵与levels照实存档；正文式工作简报只给固定 `0/0` 的数值和原区间。本轮不再对它们追加多模型×时间×组别选择。

### 5.4 时间映射：同一模型、同一声音anchor、两项差

固定 CB pretrained/NCE、native public的包络direct，DTU三seed、FAU seed3401。按dataset各两项family：

1. `r(train0/test0)−r(train0/test600)`：固定读出离开原相对位置后发生多大变化。
2. `r(train600/test600)−r(train0/test600)`：在相同测试位置重拟合读出能恢复多少。

所有模型表示仍访问 `[center−400, center+600)` 的完整一秒窗；600不是600ms单点。其输出说明读出与相对时间位置的关系，不单独证明神经表征翻转。目标/声音anchor、参与者、contentfold与query列表必须一致。

### 5.5 与新 APwrong 的连接

当本包公共先验模块产生匹配 target-excluded lineage 的 APwrong donor、target checkpoint及测试输出后，将它绑定为新逻辑臂；不能假装旧 XM 就是 APwrong。

优先复用相同选定probe：private full及三个后刺激窗，DTU/FAU public `0/0` 的env/direct和history residual。新的推断先只覆盖full private AUC的 AP−APwrong，以及DTU/FAU history residual的 AP−APwrong；新的组/时间矩阵不自动展开。使用单独late-binding登记，记录source hashes、实际seed/folds与新family，依赖未齐的臂不阻塞上面可立即计算的比较。

## 6. 绑定为通用 paired 分析输入

### 6.1 原始行和配对键

每个导出 observation 至少含下列字段。以下是**仅用于接口验证的 synthetic 示例**，不是儿童结果，也不是可追加到研究数据的模板观测：

```json
{
  "dataset": "private_bdf",
  "identity": "SYNTHETIC_CHILD_001",
  "group": "HA",
  "fold": "evaluation",
  "seed": 3401,
  "arm": "AP",
  "window": "full",
  "metric": "auc",
  "unit": "AUC",
  "value": 0.5,
  "query_set_id": "SYNTHETIC_SCHEMA_QUERY_SET",
  "analysis_role": "outer_test",
  "provenance": {
    "query_ids": ["SYNTHETIC_CHILD_001/trial_001"],
    "support_ids": [],
    "population_fit_identities": ["SYNTHETIC_SOURCE_CHILD_001"],
    "selection_identities": ["SYNTHETIC_SOURCE_CHILD_002"],
    "outer_fold": "subject_0",
    "source_record": "SYNTHETIC_ONLY_NOT_A_REAL_UNIT.json",
    "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "aggregation_note": "Synthetic schema validation only; no aggregation across seeds.",
    "source_fold_ids": ["evaluation"],
    "source_seed_ids": [3401]
  },
  "metadata": {
    "synthetic": true,
    "source_commit": "SYNTHETIC_ONLY",
    "source_unit_id": "SYNTHETIC_UNIT_001",
    "source_plan_sha256": "SYNTHETIC_ONLY",
    "subject_fold": 0,
    "content_fold": 0,
    "representation_contract_id": "SYNTHETIC_POST_ONLY_CONTRACT",
    "readout_contract_id": "SYNTHETIC_SOURCE_ES_LINEAR_PROBE"
  }
}
```

上例所有 synthetic ID、0.5 和零 hash 只为检查字段兼容性，**不能生成假记录填缺项，也不能混入研究 `observations.jsonl`**。实际导出需要真实数值、来源与摘要；缺失必须进入 `coverage.json`。`provenance` 严格限于上例展示的工具支持字段；source commit、unit ID、原始 fold、合同等扩展信息进入 `metadata` 或独立 binding manifest，不能新增未知 provenance 字段。`query_set_id` 只能由真实缓存/数据元数据的试次或segment-anchor索引及身份得到；禁止对每个候选随意起名、或直接用arm相关unit hash充当query摘要。若生产unit本身不列query索引，可用其绑定的确定性extractor和已存cache metadata重建索引，记录重建方法；不读取外部未知数据来补身份。提供 `query_ids` 时必须至少有一个真实 query ID；未知名单不能用空数组伪装已核对。

private 每人只在其分配的一个 outer subject fold评价，不能要求每人齐5 outerfold。通用工具的 `fold` 表示**人内需要完整的content/session重复**：private使用 `evaluation`；DTU/FAU使用 `content_0`、`content_1`；Federici先按既有规则将sessions在人/seed内等权聚合后使用 `content_0`，并保存session溯源。原 `source.subject_fold` 保存在 `metadata.subject_fold`，并转换为工具识别的非空字符串 `provenance.outer_fold`（例如整数0转换为 `subject_0`），检查同人同seed跨臂一致。若提供 `source_seed_ids`，必须仅为当前 observation 的单个 seed；不能把已跨seed均值再复制成三条 seed 记录。

如果现场某合法source合同的重复单元不同，用 `required_folds_by_identity` 绑定真实预期，而不是删去未完成重复或把session数当独立n。组别由source manifest带入，不从新表现重分组。

### 6.2 family 与重采样

导出后，server为每个分析family生成实际CLI spec，含 `family_id,dataset,metric,unit,required_folds,required_seeds,expected_identities,group_sets,bootstrap,contrasts`。具体字段以包内通用paired工具接口为准。该工具的既定新分析口径为**整个人重采样、以原始样本SE标准化的bootstrap max-|z*|同时区间**；不要把它标为旧报告bootstrap-t，也不要用新口径替换原注册区间。

绑定时将清单中的 `bootstrap_seed` 转为 `bootstrap={"B":4000,"seed":该值,"alpha":0.05,"resampling":"independent"}`；从 CLI spec 去掉清单独有的 `source`、`interpretation` 等注释字段，其信息留在 binding manifest。实际调用为 `python -B scripts/paired_contrasts.py contrast --rows NORMALIZED.jsonl --spec BOUND_FAMILY.json`，如写结果则用新的 `--output` 路径，不覆盖旧输出。预期名册按 analysis group 绑定；没有真实名单就明确 `not_supplied`，不能称全队列。跨窗口配对保留同一组物理 query/声音anchor 的 `query_set_id`，窗口只改变 EEG 访问，不能把来自不同 trial 集的结果硬配对。

- 每个family使用其所有contrast需要的共同完整身份集。先同人同fold做差，再fold均值，再seed均值，最后对人等权。
- 不乘seed×subject扩n。private核心预期64人、FAU67人、DTU44人、Federici86人的名册都从现场manifest绑定；这些数字是快照核对，不是造出满额n的要求。
- `all` 显式映射：private `HA/NH`；FAU `ha/ci/th`；DTU `hi/nh`；Federici `CI/HC/HC-v`。同family不要同时把all及其子组当独立组。整体family与组间改善差family分开。
- 组交互在各组内整人重采样，并在同次replicate重用共享对照组，报告直接改善差；不能相减独立CI。
- 使用4000次replicates和固定、写入spec的seed。零经验方差、独立n不足、无法计算SE等情况保留点估计并标 `nonregular`/不可估区间，不能制造 `[0,0]` 的“等效证明”。
- family仅覆盖清单的成员；不宣称控制全部模型、所有旧target与全部人群的总体错误率。新增family后记录它为什么回答一个不同问题，不按结果拆并family。

### 6.3 输出清单与schema

写入新目录 `results/auditory_alignment_v3/aln35/science/`：

| 输出 | 必含字段/内容 |
|---|---|
| `correction_manifest.json` | §3的source及实际访问字段，受影响/不受影响依赖 |
| `binding_manifest.json` | 本计划hash、实际HEAD、upstream plans/units/cache hashes、expected identity名单摘要、全部resolved source selector、query摘要构造 |
| `observations.jsonl` | §6.1的真实逐人/seed/repetition数据；保持数据集及读出scope分离 |
| `coverage.json` | family的expected/bound/complete/paired人数、per-arm及per-contrast覆盖、缺fold/seed/metric原因、技术缺失与无支持分别计数 |
| `contrasts.json` | family_id、exploratory标记、scope、metric/unit、contrast有向terms、n与分组n、估计值/SE/同时区间、bootstrap方法/B/seed、nonregular状态、source hashes |
| `history_interface.json` | §7的基线、源拟合、严格twin、common-support和trial覆盖；原旧结果另列 |
| `SCIENCE_PRIVATE_RESULTS.md` | 先写有证据的工作认识、竞争解释和下一步干预；附固定比较表、访问说明、未完成实际依赖；不只列完成作业数 |

元数据中的匿名逐人结果按既有授权处理；原始 EEG、临床原始表、姓名及身份映射不属于这些派生报告。

## 7. 历史条件读出：增加一个可解释的同等基线

### 7.1 当前实现是什么

`auditory_c3/c3dl/hc.py:69–71` 的 `q0_table` 由source儿童在六个since-last-deviant bin的标签频率（含固定伪计数）得到。`private_current_time.py:137–150` 在source ES拟合：

\[
q_1(y=1\mid z,h)=\operatorname{sigmoid}\{\operatorname{logit}q_0(h)+b+w^\top z\}.
\]

现有 `history_gain_bits` 是 held-out mean log-score gain `LL(q1,y)−LL(q0,y)`。新增截距也可能修复背景概率误差；它不是精确条件互信息或唯一神经贡献。现有结果照实保留。

### 7.2 新增最小readout sensitivity

固定 private prior NCE的S/AP/J*/XM、seed3401、full；先使用已有表示缓存，不重新训练encoder。新执行版本中比较：

- `B0_original`：现有固定q0(h)。
- `B1_source_calibrated`：`sigmoid(logit(q0(h))+b0)`，只有一个无惩罚截距，在与full EEG-offset读出相同的source ES行上拟合。
- `EEG_offset`：现有 `q1`，能逐样本精确复用就复用；若只能重拟合，记录同一source行、标准化、C/惩罚、优化容差与状态。

输出 `B1−B0` 的log-score改善、`EEG_offset−B0`、`EEG_offset−B1`；NLL/Brier/AUC定义分别保留。B1的拟合不能用target query或target support标签。不能因B1更容易超过而将它选作主参照，也不能只留下改善最大的接口。

原 `_fit_offset_logistic` 直接取优化器 `.x`，没有完整终止证据。新版本应记录并检查finite objective、梯度范数和优化器终止状态；如有真实未收敛，只修复这个readout execution并保留旧结果，不能删除不利儿童或暂停其他科学。训练侧数值失败不按outer效果择重试。

### 7.3 严格异block的history-matched twin

旧 `hc.py:176–187` 会在无异block候选时回退同bin其他trial，极端可回到自身。因此需输出原twin的：`same_history_fraction,different_block_fraction,self_fraction`，以及各儿童/组/窗口的valid trials。

新增严格版本只为有合法候选的trial，在**同儿童、同history bin、不同物理block且非自身**选择配对，固定seed，不按当前标签或预测误差选twin。无合法候选记为缺失trial，不删儿童；整体和严格支持子集均报告人数/试次数。

严格版本的source拟合与测试应成对：在相同合法source ES行上分别拟合EEG-offset、strict-twin-offset和B1；在同一严格query集合上评价三者，保留训练行/测试行hash和twin映射hash。原版full-query结果保持独立scope，不能直接用不同trial集合的均值作差。继续报告 q0在(0.01,0.99)的common-support子集，交集和全样本均列，不择一报喜。

覆盖至少包括每儿童的 `n_trials,n_standard,n_deviant,n_history_bins,n_common_support,n_strict_twin,n_fallback_same_block,n_self_twin,strict_fraction,source_ES_class_counts,query_class_counts`。个人适配另记录support/block/class/history覆盖；无两类support尤其影响CS category objective，应标记实际可用的适配信号，而不是改儿童纳入标准。

### 7.4 哪些新结果会改变判断

- AP−XM为正但AP−APwrong未分辨：保留“特定先验包改善当前类别表征”，不能归为正确声音配对独有。
- AP−APwrong及同等history基线之外的增量都支持：更有理由研究声音监督怎样迁移到儿童当前声音证据；仍不等于临床改善。
- EEG−B0改善主要被B1−B0吸收：下一步重点在history概率接口，不把该部分宣称新EEG证据；AUC和strict-twin的独立表征发现照常保留。
- strict-twin差存在但EEG−B1真实风险未改善：说明某种history内可区分性，尚未转为有利概率预测。研究目标继续是如何读取/适配，而非宣布无信息。
- 同数量support在覆盖控制后仍伤害：适配强度/自由度或source-query匹配更值得检验；若伤害随类别/history覆盖改善，则优先设计支持采样与适配先验。

以上是解释分支，不是p值开跑门槛。所有固定对比先完成并对称报告。

## 8. 时间、发育和校准的持续边界

公开 residual target仅去掉指定线性声音参照；负中心可读性可能由声音自相关、预处理相位和访问共同产生。完整一秒FM窗及zero masking均不能直接给神经潜伏期。已完成DTU因果滤波敏感性显示+200 ms有明显变化，但forward滤波延迟未补偿、整记录标准化仍在；该结果作为已有敏感性证据，不重跑全部滤波网格。

私有年龄+HA、HA内年龄+佩戴时长沿用连续模型和固定分组，不增加fitting-age作第三个共线协变量；age=fitting-age+duration。当前HA阶段14/5/36人（≤2月、>2至<13月、≥13月），中间小层只描述支持，不当作纵向阶段轨迹。组别或年龄统计不参与模型选择。

LOO校准120/120的REVE修复是去精确trial-self-reference，same-child其他reference仍存在。新prior LOO及其恢复回执以本包 `01_BASELINE_AND_INTAKE.md` 的最新发布快照为准，接入后仍应按现场真实缺项继续；不假定复制REVE的大改善。它不覆盖history-only问题，也不让private研究以校准修复结束。

private factorial与private episode的未完成数量统一引用 `01_BASELINE_AND_INTAKE.md`，本文不另保留更早计数；实际启动/完成状态现场重新核对。已完成的native science180+130和prior science300无需重训或重抽样成“新完成量”。缺原per-child或cache是对应contrast的具体依赖，不是整个项目的批准问题。

## 9. Server交付给研究者的下一轮简报

简报开头回答：哪些听觉内容可共享；新先验是否改善当前声音读取；这种改善能否跨时间位置、跨听者组及个人支持条件保持。随后给本轮4项private AUC、有限history/组差和native内容/时间比较表。每个工作判断紧接实际scope、n、seed、访问与指标。

单列：SCI35-C01勘误影响；新增exploratory对比；仍待实际源checkpoint/unit的条目。不要把“数值全部出齐、只等论文框架”作为结尾；明确哪个竞争解释更值得下一次干预，哪些旧实现可以停止重复而研究问题仍继续。
