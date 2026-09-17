> GitHub 发布副本：仅提供代码、报告、汇总结果和选定图表。逐人、逐记录、逐 epoch 及原始来源资料仍保存在服务器；原文的服务器内保存声明描述审计时状态。发布范围见 [PUBLICATION.md](../PUBLICATION.md)。

# Phase 3：科学探索产物与复现导航

本阶段把旧项目目标与新的实验结果对照。全部计算、安装依赖和检查使用 Slurm；原始数据与 `server_restart_en_v1/` 未改写。所有结果仍仅在本服务器；不透明候选 ID 不是匿名化证明。

## 当前版本

| 当前目录 | 内容 | 作业 |
|---|---|---|
| `results/phase3_ci_clinical_004/` | CI 档案临床表逐列、逐行审计；104 候选行、87 候选身份，不能解释为 87 名 CI 儿童 | 995525 |
| `results/phase3_ha_covariates_004/` | 显式四频双耳阈值与辅助纵向日期审计；Phase 2 的 53 个模型候选中 50 个完整 | 995515 |
| `results/phase3_ci_probe_002/` | MFF 内部 Patient ID、日期、通道与 MNE 读取探查 | 995497 |
| `results/phase3_ci_identity_probe_001/` | 271 无滤波历史连续版本中筛出 213 份事件/拓扑足够的候选 | 995506 |
| `results/phase3_ci_sources_001/` | 203 canonical 记录、10 份全信号二进制重复副本、通道几何与版本来源 | 995518 |
| `results/phase3_ci_verification_001/` | 10 对副本的增益/坐标/事件/间隔逐项一致；滤波保护区、四种布局与合成解码检查 | 995536 |
| `results/phase3_ci_linkage_005/` | 逐临床行的拼音/日期候选链接、身份歧义、同日任务配对、全部 canonical 来源标签 | 995565 |
| `results/phase3_ci_epochs_001/` | 全 203 份 MFF 的连续数据 QC、逐目标事件账本、包含拒绝试次的 ROI epochs、保留试次 evoked | 995539 数组；分片 2 恢复 995599 |
| `results/phase3_ci_stream_check_001/` | 四种布局的分块/整段 FIR 数值一致性；试次 mask 完全相同 | 995598 |
| `results/phase3_ci_measurements_001/` | 两种 QC 下的半份波形、时间分块并留 10 s 训练间隔的解码、逐折可用性 | 995601 |
| `results/phase3_ha_science_001/` | 50 个 HA 候选，三个目标、四种模型的嵌套候选人级交叉验证 | 995535 |
| `results/phase3_ha_sensitivity_001/` | 查看 v1 后预先限定的一次双惩罚敏感性实验；同一 50 人、同一折；逐条复现 v1 临床预测 | 995554 |
| `results/phase3_trial_budget_001/` | 固定 HA 幅值定义的试次数–ICC 曲线；共同 49 候选及每预算各自支持 | 995577 |
| `results/phase3_egi_coverage_001/` | 161 个 RAW 与 MFF 的名称/历史来源覆盖，不能证明数值相等 | 995547 |
| `results/phase3_raw_numeric_links_003/` | 159 连续 RAW 的 9×16×全 EEG 通道稀疏数值核对；151 对应已选 MFF 的单个存储连续区间，8 未一致 | 995566 |
| `results/phase3_synthesis_001/` | 来源标签分层、元数据先选索引、同候选同日任务配对、图表数据 | 995602 |
| `results/phase3_ci_clinical_feasibility_001/` | 最早索引后才核对临床/EEG 完整性；全部来源和明确 CI/CIHA 两种范围分别计数 | 995604 |
| `results/phase3_group_clues_001/` | 全来源路径与临床行的中英文设备/组别词汇复查；上下文另存 private | 995606、995608 |
| `results/phase3_metadata_addendum_001/` | 当前元数据补充：normal 来源字样、同日临床设备史/佩戴备注、动态设备及配合问题标记；不修改主 EEG 结果 | 995611 |
| `figures/phase3_final/` | HA 图最终标签版本：明确每个 EEG 模型使用同一三变量临床基线，数值未变 | 见对应 Slurm 日志 |
| `results/phase3_delivery_002/` | 当前交付：包含最后元数据补充的全分片、模型指标、同日配对、文档链接和哈希核验；RAW 两类来源证据合并表 | 见 verification.json |

主固定方案见 [PHASE3_SCIENTIFIC_PROTOCOL.md](PHASE3_SCIENTIFIC_PROTOCOL.md)，[配置](../configs/phase3_science_v1.json) SHA256 为 `0e64b0dc8a7cd30e4995931b735a57481fad763091d0a2143a029322d58240f6`。旧目标逐条依据见 [ORIGINAL_IDEA_EVIDENCE_MAP.md](ORIGINAL_IDEA_EVIDENCE_MAP.md)。追加规则分别见 [HA 双惩罚敏感性](PHASE3_HA_SENSITIVITY_PROTOCOL.md)、[CI 汇总规则](PHASE3_CI_SUMMARY_RULES.md)、[试次数配置](../configs/phase3_trial_budget_v1.json)。均为探索性，不是独立预注册或未触碰验证集。

## 数值语义与限制

- MFF `epochs_roi.npz` 保存可落入安全连续区间的所有目标试次，包括最终拒绝者。`accepted[:,0]` 是主 QC，`[:,1]` 是所有好通道均不超过 150 μV 的严格 QC。`epoch_ledger.csv` 还覆盖边界/冲突等未存储波形的目标事件。基于元数据的主波形来源选择与基于信号的拒绝分别保留。
- MFF 的几何 Fz/Cz 近邻为 128 通道网 E11/VREF、64 通道网 E6/VREF。VREF 是原始参考位置的虚拟电极，重参考后不应再因原始零值而当作坏通道。没有套用 HA 的电极编号。
- `half_scores.csv` 的 `waveform_r` 是单记录两个 ROI 在 50–250 ms 的半份波形形状相关，不是跨儿童的幅值 ICC。每码两半取相同试次数，不将相关性称作跨日重测。
- `decoder_scores.csv` 为同一记录内 `stad` 对每个实际 deviant literal code 的分类，不是儿童分类。只有五个时间折都有足够两类试次者进入主要汇总；失败的折及记录保留可用性状态。单个记录可以贡献多个码对，码对数不是记录数。
- CIHA、CI、HA、NH 均为明确原始路径/Patient ID 中的字面标签证据，不是确认诊断或设备开启状态。v1 中 161 个 canonical 记录没有这些标签；补充核查另标出 6 个 normal 来源字样，剩余 155 个。不能全部重命名为 CI。未知刺激不能自动由两/三个事件码解释为某种语言任务。
- full-pinyin + 同日是候选链接证据，不能排除同音同名或证明量表实际同期。两个有多个候选参与者的记录排除在个体任务索引和配对分析之外。临床行重复不增加受试者数。
- HA PTA 使用原表显式 500/1000/2000/4000 Hz 列：每耳四项均为数字、双耳完整后取更好耳。原表单位不明确，不写成已验证 dB HL。
- HA 嵌套验证：5 次重复 × 5 外折，训练内 4 折选择惩罚，缩放只拟合训练数据，MUSS 预测在内外折均限制为 0–100。固定 OOF 损失的候选人 bootstrap 不能替代全工作流不确定性，也不能解释为独立外部验证。
- Trial-budget 区间只描述固定候选中随机抽取试次的变化，不是人群置信区间；每半份 n 个试次意味着两半合计 2n 个。最大预算的候选集合变小，必须同时阅读共同候选曲线。
- RAW 稀疏匹配验证的是选定位置数值一致，不能代替完整信号逐点相等证明。样本数对不上全 MFF 的主要原因是 RAW 对应其中单个存储连续区间；未匹配的 8 个保留未知，不用于增加独立受试者或临床结论。

## 私有证据、失败及中间版本

`private/phase3_ci_clinical_004/` 保存原始列、行及身份；`private/phase3_ci_linkage_005/` 保存姓名、原始路径、具体日期与所有链接替代项。`private/phase3_ha_science_001/`、`private/phase3_ha_sensitivity_001/` 保存每个候选每模型的 OOF 预测及训练/测试划分。`private/phase3_ci_measurements_001/` 保存逐试次解码预测。父目录权限 0700。

临床 004 的字段审计没有完整解释自由文本里的设备/配合信息。最终中英文交叉检查经上下文审阅，产生 metadata_addendum_001：6 个临床行、5 份同日来源链接、1 份动态条件/哭闹标记；明确 CI/CIHA 来源或同日临床 CI 设备史范围为 17 个候选，其中 2 个有唯一年龄/MUSS原始值和可测 stad。**以后必须合并使用此补充表，不能继续断言全部设备佩戴状态未知。** 原始量表构成、设备电源状态和八分钟在 EEG 上的时间原点仍未确证。交付 001/995607 在这项补充之前已通过，002 是更新文档及新增元数据后的交付版本。

临床 001–003、HA covariates 001–003、CI linkage 001–004 为逐步修正的审计中间版本；不要混用。CI probe 001 因 JSON 类型输出失败，002 替代。RAW numeric 001 作业 995553 在错误的文件/schema 入口退出，代码被审查否决，快照保存在 private；002 仅全存储样本数筛查、无候选，不是信号不一致结论；003 加入每个存储区间长度并实际核对数值。CI linkage 作业 995562 因入口参数格式退出，未产生 005；995565 为成功作业。

所有生产目录拒绝覆盖。复跑需建立新版本、修订输出路径和引用链，不能直接重提会覆盖或冲突的入口。最终核验与报告应以完整作业输出为准。

数组分片 2 在约四小时长的 M0589 记录处因内存不足中断；32 GB 的恢复 995591 也不足。改为 60 s 中央块加 10 s FIR 支持区、节点临时磁盘保存长区间后，四个已完成 smoke 布局的 epoch 最大差异约 `5.96e-8 μV`，所有接受标记完全一致（995598）。995599 保留已完成输出并恢复未完成部分，不改变滤波/QC 定义；不完整目录移到 private 留痕。分块长记录的 raw numeric hash 按“区间→时间块→通道”序列，不与整段哈希直接比较。原失败依赖的 995548/995576 与 995592/995595 在运行前取消，由后续作业替代。
