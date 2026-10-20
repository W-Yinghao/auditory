# 01 — 制作基线、已见证据与 server 接入

## 1.1 证据边界

- 制作时已联网重新核对 `https://github.com/W-Yinghao/auditory.git`：HEAD/main 均为 `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`，提交时间 2026-10-18 20:25:25 +02:00。
- 本包承接研究者提供的 ALN3.4 主文与 ZIP，及本轮对最新报告、结果 JSON 和关键实现的独立核查。
- 历史检索只有相关摘要，没有完整旧对话；不把未恢复内容当作已确认指令。研究者本次明确指令和有效最新 AGENTS 优先。
- 未读取实时 Slurm、真实 EEG、全部 checkpoint 或全部 unit 压缩包。对真实生产的兼容性、资产和执行状态由 server 现场确认。
- 根 README 当前说明数据快照为 20:08–20:11 CEST。各报告自己的生成时间必须保留。10 月 17 日旧执行报告不能覆盖 10 月 18 日已完成面板。

## 1.2 制作时的完成与进行中状态

| 任务 | 最新已读快照 | 对下一轮的动作 |
|---|---|---|
| TRUE_FULL | 800/800，包含新增 one-step seed 面板 400/400 | 复用，不重跑完整矩阵 |
| local 公共先验生产 | 新 1154/1154；加 30 历史参考共 1184 | 复用 donor/target/结果，按 lineage 新增最小 APwrong |
| 公共内容/时间 | 180/180 | 直接重分析与成对对比 |
| 私有当前声音/时间 v2 | 130/130，含26个兼容v1复用 | 定点 pre 勘误；有效后刺激重分析 |
| prior science | 300/300，代表 seed3401 | 从 unit 取配对值，新增明确小family |
| 历史 private LOO 校准 | 120/120 | 保留，不能当儿童新科学结论 |
| CB auditory continuation | 19/144，donor9/9；当前目标共同10/44人 | 按已登记计划补齐 |
| 新 D | 31/120 | 补齐并分析真实风险、0-step、support覆盖 |
| 强融合 | 20/30，DTU种子3401/3407各44/44人 | 补第三种子/实际依赖，保留固定强单支 |
| private episode / CB factorial | 19:59时42/50、39/60 | 延续版本化已登记任务 |
| attention / inner sources | 19:59时50/160、103/150 | 依赖优先补齐，不转回旧顺序错误结果 |
| DTU数据曲线 / doubled budget | 19:59时94/440、26/150 | 延续；不把中途结果称完整剂量曲线 |
| 新 prior-private LOO | 20:06恢复到65/90 | 恢复回执已通过；旧失败留档，继续未完成项 |

来源：[最新README](https://github.com/W-Yinghao/auditory/blob/5ef4a60/README.md)、[晚间记录](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/aln34/EVENING_PROGRESS_20261018.md)、[新线结果](https://github.com/W-Yinghao/auditory/blob/5ef4a60/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md)。不同汇总时刻的细小计数差不是失败，也不能拼成更晚的虚构快照。

## 1.3 本轮已见的关键数值（必须披露，不能再称未看结果）

本节为结果知情的设计依据，不是 ALN3.5 新实验结果。ΔR=参考真实配对NLL−候选NLL，bits/5秒检索query；正值更好。AUC差是绝对差。区间沿用相应来源 family，不跨全文统一校正。

| 观察 | 已读结果与范围 |
|---|---|
| CB 真全量对同访问 L1 | one-step LR3e-4，三seed人内平均，unified：FAU n67 +.141[.099,.184]；DTU n44 +.213[.129,.297]；Federici n86 +.180[.113,.246] |
| CB 预训练对随机 | 同配方直接差：FAU +.091[.057,.125]；DTU +.200[.135,.265]；Federici +.051[.020,.083] |
| AP 对 scratch | DTU NCE modeT seed3401 ΔR +.074[.044,.105]；儿童三seed n64 native ΔAUC +.00875[.00343,.01406] |
| 儿童 AP 对 XM | 同主面板 ΔAUC +.00253[−.00253,.00759]；XM是EEG–EEG错配，不是AP错音频 |
| D 真风险 | DTU10% input_spatial：unified −.208[−.297,−.118]，native −.595[−.750,−.439]，但native gain +.150；三seed完整 |
| 强概率融合对固定CB | DTU n44，native seed3401 +.0535[.0277,.0793]，3407 +.0487[.0109,.0864]；unified分别+.0553和+.0200，第二CI跨零 |
| 儿童先验科学 | seed3401 n64，统一线性probe full AUC S=.52835、AP=.54927；AP−S +.02092[.00831,.03354]，不是主native三seed终点 |
| 时间与内容 | DTU CB三seed，固定0/0：env r=.1558，history残差r=.1106，onset残差r=.1078，spec残差r=.0530；当前窗口是1s重叠访问 |
| episode有限诊断 | 一个bundle episode/ordinary更新方向cosine约.99998；当前干预只有3个support步骤，不能推广为所有episode算法已充分测试 |
| 预算 | DTU3401共同36/44，延长cosine内2x对1x，CBpre unified ΔR −.0771[−.1224,−.0318]；不是历史短轨迹1x对照 |

逐文件来源和SHA见 `SOURCE_INDEX.json`。主要报告：`TRUE_FULL_PAIRED_EVIDENCE.md`、`ALN32_SEED_PANEL_RESULTS.md`、`PUBLIC_PRIOR_RESULTS.md`、`D_ADAPT_TRUE_RISK_RESULTS.md`、`NEW_LANES_EFFICACY.md`、`PRIOR_SCIENCE_RESULTS.md` 及对应 JSON。

## 1.4 身份与访问合同

- DTU44；FAU67（CI24、HA29、TH14）；Federici86人类（CI33、HC37、HC-v16）；private当前有效队列64（HA55、NH9）。采用当前精确身份表，不能用此人数硬填缺失值。
- HC-v与HC不作同人配对；phantom独立于人类分析；session、content fold、seed、query不是新被试。
- 同队列/同query/同readout可比较；native与unified分别报告。不同输入长度、采样率、音频目标或候选池下的风险值不能直接跨合同相减。
- ALN32/CONTENT_TIME的1秒窗口与prior33的64Hz/38sample窗口不同。private旧local full=0–600ms，FM full=−200–600ms；新版prior采样时间为0–578.125ms，不设pre。
- 泛化到新听者是共享结构的功能证据，不自动证明各听觉组使用相同生理机制。听觉组是观察分组；队列/设备/刺激协议不被随机化。

## 1.5 必须在现场解析的资产，不是假设已存在

1. `CODEX_HANDOFF.md`：仓库未发布但服务器可能存在；读最新区块，不因它未发布暂停其他任务。
2. 当前 `private/auditory_alignment_v3/` 与 offload 指向的 checkpoint/cache：核对 record、source code、plan、checkpoint、input/target coordinate hash。删除过的旧checkpoint不可凭路径猜测可用。
3. 从当前 `auditory_alignment_v3.core.OUT` 解析生产计划目录；制作基线的活动计划通常为 `private/auditory_alignment_v3/aln34/<lane>/plan.json`。`scripts/auditory_alignment_v3/aln34/` 提供入口及部分可追溯计划副本，不能仅凭副本判断现场注册。检查实际schema和活动注册后再导出本包规范；不把比较清单直接当可提交Slurm数组。
4. 科学 unit `per_participant`：优先用服务器现有原件；必要时按公开 unit manifest 提取确切成员。aggregate只有均值/SE/区间时不能恢复配对协方差。
5. 原生/统一readout概率、candidate IDs、query IDs与inner predictions：缺失时仅对所需兼容checkpoint重做前向/读出，不为一项机制诊断重训整个旧矩阵。

已有输出的比较分成两份明确清单：`plans/science_contrasts.json` 有10个科学probe family、30项对比；`plans/main_endpoint_group_contrasts.json` 有3个原主终点family、10项组间改善差（FAU AP−S三组两两差、FAU真全量CB的两类收益各三组两两差、儿童AP−S的HA−NH差）。后者保留原5秒检索风险或native AUC，不能用科学probe结果替代。这些是CPU分析项，不是40项新模型训练，也不构成一个跨两份清单的统一显著性family；每个family的固定成员和来源必须在绑定回执中保留。

## 1.6 Intake 如何完成

填写 `templates/INTAKE.md`，把任务逐项标成 `reuse_complete / continue_registered / analyze_existing / new_bounded / blocked_by_specific_asset / retained_hold`。本包中unknown现场字段必须实际解析，不能把模板值当证据。

新remote HEAD与本包不同：列新增提交及涉及模块，更新结果覆盖，按受影响任务重新绑定。不得静默回退到制作HEAD，也不以HEAD变化为理由重审整个项目。真实scope冲突需说明最小影响；未受影响工作继续。

继承ALN3.3材料仅保留原合同供查询（见`inherited/`）；其历史审批/状态文字被ALN3.4及本轮最新规则覆盖。旧合同的算法/数据访问细节如与服务器已版本化修正冲突，使用已核实的当前实现，并显式记录差异。
