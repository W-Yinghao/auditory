# Auditory STORY v1：服务器执行与交付规范

**日期：2026-10-02｜基准：558e6509d64e0decb4d796ee51964f7ff6a30ee2**  
**主研究文件：[01_STORY.md](01_STORY.md)**  
**新命名空间建议：`auditory_story/`。不要覆盖`auditory_nextmap/`或任何旧结果。**

> 本轮不是继续解释谱组合、晚权重或“两个时钟”。主任务是检验：**利用已知刺激的跨块条件响应学习，是否改善低临床标签下的儿童级言语功能读出。**
>
> 默认主终点SIR有序等级，MUSS固定次终点。年龄不能取代主功能结果。主干冻结，小型新表示可以训练；不再联系医生、不下载数据、不自动发布、不重跑旧75个年龄模型。

## 0. 本包授权含义与执行边界

本包是给服务器代理的实现规格和启动材料，不表示在本对话中已经运行或已经发送到服务器。

允许实施以下固定范围：

| 阶段 | 可以做 | 不能自动做 |
|---|---|---|
| P0 | 读取指定来源、核对主访问/身份/标签、建立任务表，运行小型实现测试 | 全盘重审计、恢复未知任务、联系医生 |
| P1 | 复用每外折冻结f_o，推理所需试次；训练30个小型SRP/pooled摘要 | 新的原始EEG主干训练、跨系统池化 |
| P2 | 完成SIR标签预算矩阵、固定MUSS次矩阵和技术敏感性 | 选择新量表、删低等级、追加seed寻找显著 |
| P3 | 评价同儿童跨块响应预测、分半临床敏感性；形成报告 | 用辅助成功宣称功能成功 |
| Optional | 已知MFF车道上的独立方法验证、竞争story | 未经单独启用即训练 |

所有真实数据读取、扫描、数值计算及测试通过Slurm。源数据只读。当前已有调度配置为runfill；已查允许A100/A40/L40S/A30，禁止P100/RTX6000PRO/H100。若服务器最新明确指令与此不同，采用新指令并保存来源，不静默扩大。[R6]

## 1. 第一次阅读只需这些来源

1. 当前AGENTS.md：仅提取真实调度、隐私和写权限；历史科研判断不是不可修改定理。
2. `configs/auditory_nextmap_v1.yaml`、`configs/auditory_pf_v2.yaml`、`configs/auditory_gx_v1.yaml`。
3. `auditory_nextmap/adapters.py`、`auditory_pf/cohort.py`和对应分折/主访问接口。
4. `docs/auditory_nextmap/SIR_PREDICTIVE_HEADROOM_REPORT.md`：SIR等级、概率与既有强基线。
5. `docs/auditory_nextmap/NET_COHORT_ADDITIONS.md`和`SEMANTIC_RECOVERY_REPORT.md`：避免虚构扩样。
6. 本包01/03及配置。无需为启动而读完所有历史方案。

### 1.1 已核对的绑定

| 项目 | 来源 |
|---|---|
| PF2 cohort | `private/auditory_pf/prepare_002/`，通过现有Cohort接口读取 |
| PF2冻结模型 | `private/auditory_pf/stim_002/unit_s{seed}_k{fold}/models/M_o.pt` |
| PF2同编码器汇总 | 同单元`exports.npz`，`agg_source=single_encoder_M_o` |
| 事件数组 | `private/auditory_gx/GX_stage_001/epochs/` |
| 事件/物理位置 | `private/auditory_st/ST1_scope_001/records.csv`及`events/*.parquet` |
| 连续谱旧缓存 | `private/auditory_pf/features_001/features.npz` |
| 组合谱附加特征 | NEXTMAP H4/H8记录级缓存，从实际run receipt定位；不能猜文件名 |
| 临床主表 | `private/auditory_repair/ha_prepare_001/cohort.csv` |
| PTA修正 | `private/auditory_repair/pta_007/candidate_covariates.csv`；非主协变量 |
| NH描述来源 | `private/auditory_gx/clinical_override.csv`；不进入主SIR训练 |
| 旧C0概率 | 从NEXTMAP C0 receipt定位；只作历史参照，不混到新fold主表 |

基准仓库内容已核对，私有文件存在性、字段与权重hash仍必须由服务器确认。读取失败只影响实际依赖单元，不开启全盘搜索。

### 1.2 已有API不等于新API

已存在：`AgeSource`、`Cohort`、`load_stage`、`st_events`等。AgeSource的筛选是年龄分析逻辑，**不要不加检查地将它当成通用功能队列**。本轮可复用其55人主访问映射，但需单独核对SIR/MUSS，保持明确的功能资格表。

本包`reference/`可运行核心运算；`auditory_story.cli`及Slurm工作控制器是**待实现接口**。不能把尚不存在的CLI当作已完成程序提交。

## 2. 数据表与身份边界

### 2.1 私有主表

每名主队列儿童一行：

```text
child_id, identity_group, primary_record_id, acquisition_id,
source_system, source_group, sir_ordinal, muss_original,
age_months, device_months, clinical_row_ref, target_status,
n_std, n_dev, record_seconds, accept_fraction, record_scale,
fold_manifest_ref, source_hash
```

- SIR仅合法1..5；MUSS按源记录单位。冲突不平均，按既有优先来源规则处理并记录。
- 未知问卷日期不阻断档案研究；身份冲突、数值冲突不是普通元数据缺失，需要解决或列明支持不足。
- 主访问沿用当前登记，不按新结果选择“最好的一次”。
- 同一儿童额外访问不增加n，不进入主临床风险；所有派生版本归同一个acquisition_id。
- 不新增MFF临床标签、不按EEG估身份、不把NH佩戴时间填0。

### 2.2 主队列冻结

默认起点是PF2/NEXTMAP的55名有标签HA主访问。P0保存预期到实际的差异表。若某标签缺失，SIR和MUSS分别报告支持，不能填标签或把一个目标预测值当另一目标真值。

不要求所有儿童在每个时间块都有足够试次；辅助训练的episode资格和临床预测资格分开。不能因查询AUC低、年龄预测差或SIR极端而排除。

## 3. 外折、标签预算与辅助池

### 3.1 外折

复用PF2种子404、505、606各5外折。其他两个旧种子不进入本轮默认矩阵。划分从Cohort读取，不按新功能分布重排。

对每个外折o，定义：

- `T_o`：全部外层训练身份。
- `E_o`：全部外层测试身份。
- `L_o,m,r`：T_o中具有SIR且被本预算揭示的m名主队列儿童。
- `U_o`：可用辅助EEG池；主稿默认使用本主队列内T_o的EEG，已有f_o的更广刺激训练范围另记入曝光表。

T_o与E_o在身份和物理采集两个层面都不相交。E_o不能进入PCA、SRP训练、人群响应拟合或任何临床选择。

### 3.2 标签集合

固定m=12、24、全部当前外层训练主队列。12/24各3个标签采样rep；每rep用同一个不读目标的随机排列，12是24前缀。全量仅1个rep。

不要为了保证低等级出现而读取隐藏SIR进行分层采样；缺少某等级是低标签情境的一部分，五级概率头必须能处理。

保存每个集合hash。所有模型共用相同集合。隐藏标签值替换为NaN或随机数后，P1表示、集合定义及非评价代码应不变。

### 3.3 内层

临床头在L内做3折儿童验证，选3个λ之一。预训练表示可看过外层训练池中内层验证儿童的**无临床标签EEG**，这是已声明的固定辅助池协议。它的临床标签、MUSS、阶段和年龄不能用于P1模型选择。

C和临床头的填补/标准化/样条只用当前内层有标签训练部分；最终用全部L重拟合。不能复用全队列拟合的临床样条或原C0概率充当低标签基线。

## 4. P0：限定检查，不再次建立庞大门控工程

必须通过：

1. 主访问与临床目标来源一一对应；重复文件不跨折。
2. 当前o的同一个f_o用于全部本折train/test表示；读取train_children/test_children与权重hash。
3. 冻结f_o不存在当前E_o；不能把每人“自己的OOF向量”拼成第二层新的任意交叉验证。
4. 32维缩放/PCA只用T_o，child×class等权。
5. 物理块映射、时间保护和支持/查询不重叠。
6. RPS、NLL、零潜变量人群基线、模型模式和儿童等权测试。

不进行880个合成世界。首轮采用包内确定性测试，加2个小型合成场景（条件个体信息存在／仅背景个体信息存在）验证方向，结果不决定真实功能必须阳性。

关于旧`train_age`：本轮不复用它训练新摘要。记录公开代码的train/eval问题，核对所复用f_o是否由该函数产生；若不是，不为修历史报告重训75项。若某必需权重来源受影响，单独标记，不能静默改用测试更好的权重。

## 5. P1：实验监督的儿童摘要训练

具体公式以03文件为准。

1. 复用已有全试次embedding缓存；若缓存坐标、试次顺序和权重一致，直接用。否则每外折一次必要推理，不训练f_o。
2. 构造前事件历史和60秒物理块，5秒边缘保护。
3. 拟合32维变换和人群q0。
4. conditional与pooled两个模型各3000固定步；每batch4名儿童，每条件32支持+32查询。
5. 每100步checkpoint与数值诊断，结束后保存μ、query预测和完整源范围；真实逐人产物全部private。

3种子×5折×2臂=**30个小型表示模型**。没有额外模型seed维度；不同外折seed已影响辅助池及初始化，报告为复合分析随机性。

全访问临床摘要使用全部合格试次按条件等权，不能每条件10次抽样后说只用了80试次。主分析不声称短时采集性能。

## 6. P2：固定临床矩阵

### 6.1 SIR模型

| ID | 输入 | 训练标签 | 目的 |
|---|---|---|---|
| PRIOR | 本L的平滑类频率（0.5伪计数/类） | L | 参照，无拟合搜索 |
| C | 年龄、log1p设备月数样条 | L | 临床基线 |
| C_MEAN | C＋冻结刺激条件均值 | L | 普通预训练 |
| C_MEAN8 | C＋条件均值的训练池PCA8 | L | 同输出维数的简单压缩 |
| C_SPEC | C＋D2/增强谱组合 | L | 强谱基线 |
| C_POOL | C＋pooled支持摘要μ | L | 非条件集合对照 |
| C_SRP | C＋conditional摘要μ | L | 主方法 |
| SRP_ONLY | conditional摘要μ | L | 不输入病历的描述臂 |

每外折7个标签情境（12×3、24×3、all×1）。7个需拟合臂；每个头3λ×3内折＋1最终=10次优化。最大7350次临床头拟合。

除PRIOR外使用同一五级有序模型族。记录每次的λ、阈值、优化是否收敛、概率最小值和类别支持。不允许因罕见等级使NLL变大而改主指标或删人。

### 6.2 MUSS次结果

全标签下C、C_MEAN、C_SPEC、C_SRP，15外层单元×4臂×10=600个小型拟合。与SIR是否阳性无关地完成。

### 6.3 全标签技术敏感性

固定技术项：记录尺度、接受比例、坏段摘要、log接受试次数、记录时长，来源沿现有函数。比较C_TECH、C_TECH_SRP，15×2×10=300次。主C_SPEC不自动等于技术控制；两者作用不同。

预计总临床拟合8250，**硬上限9000**。差额只用于已记录的技术重试；不能用来增加新模型。模型重复运行不得覆盖旧输出。

### 6.4 概率评分

主SIR RPS、五类NLL(bit)、Brier、期望分数MAE、P(SIR>3) AUC。全部保存原始与共同floor后的概率；不同折潜变量不直接合并AUC。

极少数等级报告分层损失和人数。该表为解释误差，不是分层挑主效果。MUSS报告原分数MAE、RMSE及满分数。

## 7. P3：解释方法与功能结果，不制造新终点

### 7.1 跨块响应预测

同一留出儿童、同一支持/查询规则，比q0、pooled、conditional查询NLL。每个方向每条件32试次，主方向A→B，B→A作固定对称复核；不足支持单列不补有放回试次。

该NLL以训练PCA坐标为测量对象，不能直接比较不同外折绝对密度，主要用同外折配对增益；跨折按儿童聚合差值。不能叫原始EEG真实互信息。

### 7.2 临床分半敏感性

在两组物理块分别生成临床摘要并用同一已冻结临床头预测，比较差异。这个分析评估记录输入敏感性；不称复测效度，不用全记录作为无误差真值。

### 7.3 结果聚合

每儿童先平均该预算下mask/seed损失，再跨儿童平均。R_low是R_12与R_24等权平均。两个主比较和全部基线同时写入总表。

2000次固定OOF儿童bootstrap。清楚写出它不包含完整训练、调参和多年研究路径的不确定性。主结果语言采用“该队列上的内部验证”，不写独立临床复现。

## 8. 结果判读和停止规则

- **FUNCTIONAL_GAIN_SUPPORTED_WITHIN_SCOPE**：功能主对比方向及不确定性有支持，普通均值／强谱比较足以支持提出方法的用途。仍非临床部署验证。
- **METHOD_GAIN_WITHOUT_CLINICAL_INCREMENT**：超过普通表示但没有超过C；功能辅助价值未成立。
- **AUXILIARY_ONLY**：查询响应或年龄等辅助任务改善，SIR/MUSS无改善。不得宣布主story成功。
- **LOW_PRECISION**：效应区间容许明显正负，不把单一p>0.05写成不存在。
- **NO_ESTABLISHED_GAIN**：固定设计未建立收益，结束本实例；不自动换终点、latent维数或主干。
- **TECHNICAL_FAILURE/SUPPORT_LIMITED**：实际比较未合法完成，与科学阴性分开。

不要把状态机包装成文章贡献；它只是防止执行和解释混淆。完成主矩阵后再决定下一轮，不能一边看到新结果一边扩矩阵。

## 9. 可选扩展：独立开关，不自动触发

### 9.1 MFF方法验证

纯音和bapa分开。每条车道若已有5折×3seed合法f_o，运行相同两个小摘要臂和跨块响应评价；最多60个额外小模型，无新主干、无临床Y。不能直接借用BDF编码器失败后扫迁移结构。

默认`mff_validation.enabled=false`；P0可以形成来源卡，不提交训练。执行者不得因SIR阳性自动扩大；作者明确决定启用后，将范围和预算写入附录。

### 9.2 竞争story

见04和独立配置。默认关闭。不能以主story失败作为自动运行或发表授权。

### 9.3 全标签监督微调／年龄

首轮均关闭。年龄模型修复或新临床微调需要解释其针对的问题，并单独授权；不是为了把新story强行做成阳性。

## 10. 输出与目录

```text
auditory_story/                  # 新控制器/适配代码
configs/auditory_story_v1.yaml
private/auditory_story/<run>/
  sources.json
  records.csv
  folds.json
  label_masks.json
  transforms/
  representation_models/
  clinical_models/
  predictions_sir.parquet
  predictions_muss.parquet
  query_predictions.parquet
  fit_ledger.jsonl
  checkpoints/
results/auditory_story/<run>/
  aggregate_metrics.json
  primary_contrasts.json
  completion_summary.json
docs/auditory_story/
  PROTOCOL.md
  IMPLEMENTATION_NOTES.md
  RESULTS.md
```

逐人、逐访问、精确日期、原始路径、身份边、模型权重全部留private。公开仅充分聚合的结果。写报告不等于允许push；不能把逐人概率加入公开图表或材料包。

### 10.1 必需诊断字段

```text
unit_id, arm, outer_seed, outer_fold, label_budget, label_repeat,
source_commit, code_hash, source_encoder_hash, training_scope_hash,
source_children_hash, labelled_children_hash, excluded_children_hash,
optimizer, objective_normalization, steps_or_iterations,
initial_loss, final_loss, grad_norm, model_training_mode,
selected_lambda, convergence_status, probability_floor_count,
start_time, end_time, slurm_job_id, attempt, status
```

涉及精确时间的台账只在private。缺日志不能用新训练结果冒充旧日志。

## 11. Slurm、断点和预算

- CPU最多2个并行作业，GPU最多1个；小模型优先CPU，必要推理使用允许GPU。
- QoS默认runfill，可抢占；完成单元原子落盘，恢复跳过完整同hash单元。
- 每100步保存新摘要状态、optimizer、RNG、采样位置；不要只保存最终权重。
- SIGUSR1触发保存后退出；不要在抢占后悄悄从零重复累计拟合。
- 30个HA摘要模型，最多15个新增冻结主干推理单元，0个新原始EEG主干。
- 9000个临床优化上限；达到上限报告未完成，不降低对照数量掩盖超限。
- 不为写新摘要、补表标题或补日志重复拟合。任何新预算需写附录，不能使用未消耗的旧GPU授权。

## 12. CLI合同（需要实现，不是已有功能）

```bash
python -m auditory_story.cli prepare --config configs/auditory_story_v1.yaml --run story_p0_001
python -m auditory_story.cli train-profile --config configs/auditory_story_v1.yaml --run story_p1_001
python -m auditory_story.cli clinical --config configs/auditory_story_v1.yaml --run story_p2_001
python -m auditory_story.cli evaluate --config configs/auditory_story_v1.yaml --run story_p3_001
python -m auditory_story.cli report --config configs/auditory_story_v1.yaml --run story_final_001
```

这些命令必须在Slurm里运行。本材料包提供的`slurm_template.sh`在入口不存在时拒绝运行，不会悄悄跳过实现。实际模块可不同，但必须在IMPLEMENTATION_NOTES写出一一映射。

## 13. 第一份结果报告的固定问题

不要写“做了多少模型，所以已经充分”。按以下顺序回答：

1. 临床问题和主终点有没有被保持？实际样本与每预算标签n是多少？
2. 两项主SIR比较及强谱参照如何？不同标签预算是否一致？
3. MUSS固定次结果如何？有没有目标间差异？
4. 条件摘要相比pooled是否有实际价值？
5. 改善是否超出年龄／佩戴时长和技术摘要？
6. 哪些只是辅助响应建模成果，不能支撑功能主张？
7. 是否值得推进本story；若不足，缺失的具体证据是什么？

正文不把年龄改为主终点，不给latent命名为康复程度，不以多个低p值自动选期刊故事。

## 14. 交接时必须保留的一句话

**先解决选定的低标注功能学习问题，再使用数据提供证据；不要因为某个辅助实验成功，就重新让数据替我们决定论文主题。**
