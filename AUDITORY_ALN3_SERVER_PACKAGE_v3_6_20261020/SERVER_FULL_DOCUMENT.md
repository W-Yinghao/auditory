# ALN3.6 — 三轮收束：完整研究方案与 Server 执行交接

日期：2026-10-20。研究项目：W-Yinghao/auditory。

**这一版执行用户最新的“三轮内结束”指令。主问题固定，具体结论随证据变化；不以新故事、新模型或新数据矩阵延长研究。**

本文件完整汇集论文问题、既有证据、本轮科学定义、数值合同、真实源码接入、三轮边界、统计与存储范围。可单独阅读；配套ZIP含数值参考源码、9项合成/计划测试和完整性核对工具。单文件文档不是已完成生产训练的声明。

执行优先级：用户最新明确指令优先；本包科学范围优先于旧版探索扩展。参数化细节见03，服务器真实数据/来源接入见04，范围与数量见plans/round1.json。若现场绑定揭示不一致，修正受影响绑定并说明，不自动增加新科学分支。历史结果和旧执行身份均保留。

GitHub核验基准：3da8cf5758214c0cf87a1f1c8d67fb84b574000e。恢复依据为ALN3.4/3.5交接材料及当前公开仓库；没有宣称已取得逐字完整的旧聊天档案。服务器实时队列、权重路径和清理候选清单须由server接包后重新读取。

## 全文目录

- `README.md` — ALN3.6 · 三轮收束的第一轮
- `SERVER_START_PROMPT.md` — 给 server agent：执行 ALN3.6，第一轮／总共三轮
- `AGENTS_APPEND.md` — ACTIVE RESEARCH INSTRUCTIONS — ALN3.6 (2026-10-20)
- `docs/00_PAPER_QUESTION.md` — 论文问题与判断
- `docs/01_EXISTING_EVIDENCE.md` — 已有证据：哪些支撑主线，哪些还不够
- `docs/02_ROUND1_DESIGN.md` — 第一轮：两种直接干预，一套嵌套读出
- `docs/03_READOUT_CONTRACT.md` — ALN3.6：共享声音证据、个人标定与时间读出的最小合同
- `docs/04_SERVER_BINDING.md` — 04 — Server 接入、源人群排除与执行身份
- `docs/05_THREE_ROUND_CLOSURE.md` — 三轮合同与分支结束
- `docs/06_REPORTING_AND_RETENTION.md` — 输出、统计与保留
- `src/aln36_readout/README.md` — ALN3.6 CPU readout reference
- `SOURCE_INDEX.md` — 证据与接入源码索引
- 附录：完整机器计划、包元数据、当前发布快照与本地验证回执


---

## 原文件：README.md

# ALN3.6 · 三轮收束的第一轮

**主问题：听觉 EEG 中，哪些声音证据可以跨听者／听觉组直接读取，哪些需要个人的时间读出调整？**

这是 `W-Yinghao/auditory` 的继续。用户于 2026-10-20 将目标明确改为三轮内完成研究所需证据。本包以 GitHub `3da8cf5758214c0cf87a1f1c8d67fb84b574000e` 为可核验基准；制作时远端 main 与该提交一致。服务器接包后仍须读取现场状态，不能把快照当作实时队列。

本轮补两个直接实验：FAU 整个目标听觉组排除后的迁移，以及相同表征、支持、query 上的嵌套个人时间读出。私有儿童负责区分当前声音证据、序列历史和个人概率校准。已有 FM／先验／episode／融合结果保留；不继续扩展它们的搜索空间。

## 阅读顺序

1. `SERVER_START_PROMPT.md`：给 server agent 的任务。
2. `SERVER_FULL_DOCUMENT.md`：单文件完整规格。
3. `plans/round1.json`：本轮范围、种子和数量。
4. `docs/03_READOUT_CONTRACT.md`、`docs/04_SERVER_BINDING.md`：读出算法和真实数据接入。

## 本轮工作量

- FAU：2 个工具 × 3 个排除组 × 2 个内容划分 = **12 次唯一 encoder 训练**。5 个原评估人折只是记录切片，共 60 个评估 cell；不得为这 5 个切片重复训练相同模型。
- DTU 既有 pooled 权重：20 个冻结评估 bundle。
- FAU 既有 pooled 权重：20 个冻结评估 bundle，仅作为已有分布背景和个人读出参照。
- 私有 matched AP/APwrong：10 个冻结评估 bundle。兼容的既有 S 可以另作 5 个补充参照。
- 共 **110 个核心评估 bundle，只有 12 次新的 backbone 训练**；不是 110 个新模型。五种读出和控制在 bundle 内拟合。

实际训练去重键还须包含合法 source 人／内容／预处理／代码哈希。若这些不相同，不能假装复用；先解释具体差异，不自动扩大成 60 次训练。

## 本地可执行部分

```bash
python scripts/materialize_plan.py --output /tmp/aln36_round1_plan.json
python scripts/verify_package.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

包内有可运行的 CPU 嵌套读出参考实现、配对效应汇总、计划生成和完整性核对。**原始 EEG、私有 block 绑定、训练权重和 Slurm 接入不在包中；server agent 需按 docs/04 实现新 `aln36` 绑定并做一次端到端工程检查。这里没有执行新训练，也没有宣称新假设已经得到结果。**

只追加新的执行版本。不能覆盖旧输出、改写在跑代码、清空历史 holds 或重启旧全矩阵。聚合运行与排队 GPU 总上限维持 10。个体级派生结果发布沿用用户既有授权。


---

## 原文件：SERVER_START_PROMPT.md

# 给 server agent：执行 ALN3.6，第一轮／总共三轮

用户最新指令：研究不再无限探索，三轮内结束；先确定论文问题、已有证据与缺口，按此准备并执行下一轮。此次主线为“跨听者／听觉组可迁移的声音证据与个人时间读出需求”。

先读 `AGENTS_APPEND.md` 和 `SERVER_FULL_DOCUMENT.md`，再读取现场 `AGENTS.md`、当前交接文件、git HEAD、已有 plan／完成结果和准确作业归属。将新优先指令追加到 AGENTS 顶部，保留历史。不要要求用户再次批准论文措辞、个体派生结果公开或已授权范围内的训练。

## 必须完成的工作

1. 以当前代码建立新的 `aln36` 命名空间；不得修改受旧执行哈希保护或仍在运行的源码。绑定本包源索引、实际父权重、合法 source 人／内容和代码版本。
2. 实现 FAU leave-hearing-group：HA、CI、TH 依次整组排除，包含 TH dev 人的正确排除；local 与 CBpre 两工具、两个内容划分，seed3401。**按真实 source 集去重为 12 次训练，60 个评估 cell**。不要因为原记录有五个人折而训练五遍。
3. 执行相同五状态读出 H0/E0/HP/EC/ET。关键是无个人支持的 `R(H0)-R(E0)`、个人校准后 EEG 增量 `R(HP)-R(EC)`、时间重权增量 `R(EC)-R(ET)`，不能只汇报最终 ET 排名。
4. DTU 与 FAU pooled 既有权重补足目标人的 source-fit 内容特征，个人 support 来自这些内容，query 是全部原 source-test 内容。新协议与旧同 role 前30%分段实验分开命名。
5. 私有 matched AP/APwrong 接同一 history 控制、自然 U30 block、三窗证据和 strict twin。不得把旧 AP lineage 或旧 full-query 指标替代新实验。
6. 输出全部完整逐人配对结果、查询一致性、直接交互区间与一页科学判断。没有阳性进入门槛，不挑组／人／seed／窗口。

只需一次针对真实剩余风险的工程检查：来源／分割正确、标签未进入 query 之前的拟合、两个骨干确实更新、嵌套读出退化关系正确、输出有限且能复现。通过后执行全范围，不等待另一次 go；不把 smoke 当科研性能闸门。

## 调度与收尾

维持 aggregate running+pending 10 GPU 上限。先让当前运行单元在安全边界结束；本轮主实验优先取得释放的槽位。已登记四条 budget/data tails 只收完原有有限计划，不新增扩展；只给仍有必要的尾项剩余槽位。不要批量取消已有作业，不释放旧1602类 held executions，不改变其他项目作业。

停止新增 selector/fusion、更多 donor checkpoint、episode 压力或步数、C10/H10、更多数据比例、更多模型×loss。已有有效结果全部保留。R2 固定重复本轮核心，R3 汇总和写作，见三轮合同；不得用这一轮的显著性决定是否偷偷开第四轮。

本包不包含服务器原始数据接入完成的声明。请实际完成实现、验证、训练／冻结前向和统计后，分别报告哪些已经完成。现场缺失只阻塞直接依赖的分支，其他已就绪任务继续。

当前不执行整目录删除。先保护本轮要复用的权重、特征和原始结果；A3b/A3d 的真实候选清单不在 GitHub。清理只处理现场证明无依赖的精确文件，保存小型派生结果与来源记录。不要让清理审计成为这一轮的科研任务。


---

## 原文件：AGENTS_APPEND.md

# ACTIVE RESEARCH INSTRUCTIONS — ALN3.6 (2026-10-20)

This block implements the researcher's explicit instruction to finish the necessary research in three further rounds. Place it above conflicting ALN3.5/3.4 exploration-only wording. Preserve the history, completed outputs, old IDs and scoped holds.

1. Separate the enduring concern (transferable sound-related EEG evidence and listener-specific temporal readout), the changeable hypotheses, and replaceable tools. This is now a bounded manuscript-oriented investigation; the paper's factual conclusions remain conditional on evidence.
2. R1 tests whole FAU hearing-group exclusion and nested shared/personal readouts. R2 repeats the fixed core, including all three groups and both tools, rather than only favorable cells. R3 finishes predeclared validity analyses and writing. No fourth scientific search round is implied.
3. Keep effective same-access local and query-aligned genuinely full-finetuned CBraMod. Keep representative REVE, random, published kernel-CS and InfoNCE evidence; do not multiply them into every new cell. No unpublished VCS-QMI or variational critic.
4. FAU group exclusion applies to this study's source EEG, normalization, fitting, development and readouts, including TH dev individuals. Generic CB pretraining provenance is fixed; do not claim its lifetime training never contained that hearing category. Retained offline EEG preprocessing is disclosed.
5. Count unique source fits, not result slices. With the full target group withheld, the five original person folds share the same allowed source set: 2 tools × 3 groups × 2 content folds = 12 unique fits per seed, yielding 60 evaluation cells. Hash-based reuse is required when dependencies are identical.
6. E0 has zero target support. HP/EC/ET have the same natural support and identical queries. A supported result does not establish zero-support group transfer. EC and ET share history calibration and the same EEG evidence bank; ET adds only the predefined temporal contrast coefficients.
7. Select all rules and checkpoints from allowed source data only. No outer query labels/results choose support, window, regularization, model, seed or stopping. Target support labels may fit the predefined personal parameters; they may not select target queries or new architectures.
8. Public support uses the held-out person's source-fit sound contents and evaluates on all source-test contents. Private support uses natural physical blocks and independent later blocks. Do not call private binary trial/block generalization unseen-sound-content transfer.
9. Children carry the current-sound-versus-history and personal-readout test. Keep all children and valid outcomes; no signal/clinical significance threshold. Keep stage/group/identity and human/phantom exclusions. No ERP main line, neural latency claim from broad windows, clinical treatment effect or exact conditional MI claim from decoder risk.
10. Completed ALN3.3–3.5 results remain available, including positive auditory-people, episode and fusion findings and all weak/reversed outcomes. No new general model/loss/pressure/scale/checkpoint search. Already running work finishes at safe unit boundaries; useful registered tails remain finite.
11. Individual derived publication remains authorized in the already agreed scope. No renewed permission request. Raw EEG, names, identity mappings, raw private records and model weights remain governed by existing restrictions.
12. Maintain the aggregate 10-GPU cap and exact job ownership. New versioned code only; no editing running source, blanket queue cancellation, hold reset, or unscoped deletion. Ordinary engineering readiness is sufficient to proceed with this authorized scope.


---

## 原文件：docs/00_PAPER_QUESTION.md

# 论文问题与判断

## 建议的主线

**跨听者的声音证据与个人时间读出：什么能够共享，什么需要个人数据？**

工作英文题名：**Transferable auditory evidence and listener-specific temporal readout in EEG**。题名中的个人时间读出是要检验的问题；若没有额外收益，不把它写成已发现的机制。

我们希望弄清楚：来自其他听者、甚至其他听觉组的训练，能否提供超出刺激历史的当前声音证据？得到新听者的一小段自然数据后，改善来自对背景概率的估计、对整体 EEG 证据尺度的标定，还是对不同时间证据的重新组合？

普通跨被试总分把这些来源混在一起。论文的贡献应是用直接的、同 query 的干预将它们拆开，并在 HA/CI/TH 和儿童中给出证据范围。不是发明一个名字不同的 adapter，也不是把所有历史实验各写成一个贡献。

## 三层必须分开

| 层次 | 本项目的决定 |
|---|---|
| 研究关切 | 不同听觉经历的人之间，什么声音证据可以迁移；新个体还需要什么数据和读出调整 |
| 可改变的假设 | 完全排除目标听觉组后仍有共享 EEG 增量；个人时间重权有超出 history 与尺度校准的增量；儿童的增量涉及当前声音而非仅序列背景 |
| 可替换的工具 | local、CBraMod、REVE、传统 kernel-CS、InfoNCE、线性／概率读出、自然 support 与严格错配控制 |

工具可以失败。不能由某个 adapter 的失败改写研究关切，也不能为了保住时间重权假设继续增加自由度。R1/R2 的直接比较决定主张强弱，R3 接受有界的不确定性。

## 论文可以承载的三段论证

1. **先证明有可迁移的声音对象。** 既有三数据集真正 full-tuning 和声音属性 probe 已提供基础；新 FAU 整组排除进一步检验在没有该组本研究训练信息的条件下，固定群体读出是否仍增加当前声音预测。重点是 history 之上的增量，不是组别分数排名。
2. **再问个人支持究竟改变什么。** 同一表征和 EEG 访问、同一支持和 query，用 H0/E0/HP/EC/ET 比较背景、共享声音证据、整体标定和时间重权。ET 最终分数好不够，必须直接超过 EC 才支持额外时间组合价值。
3. **儿童给出更严格的当前声音检验。** 在强序列可预测性的任务中，个人 history-only 必须公平竞争，真实当前 EEG 必须与同 history 异 block 的 EEG 区分。儿童不负责复制成人听觉检索 AUC，也不以验配阶段的显著性证明论文价值。

现有多被试对比式语音解码和 subject-specific 层已有先例（Défossez et al., 2023, https://arxiv.org/html/2208.12266v2）。本项目不以这些通用做法本身声称新颖；新意必须落实到跨听觉组排除、当前声音／历史的控制、以及个人时间读出的直接辨别结果。尚未完成系统新颖性审查，不使用“首次”等措辞。

## 主图草案：按问题组织

- 图1：问题、无个人支持／有支持访问边界，以及既有有效 local/CB/REVE 证据的简洁定位。
- 图2：FAU 整组排除后各目标组的共享 EEG 增量和错配控制；DTU/Federici 既有内容读出作为范围背景。
- 图3：同人同 query 的 history 校准、整体 EEG 标定、时间重权增量；不画新的模型排行榜。
- 图4：儿童当前声音相对 history/twin 的增量，和个人时间重权；AP/APwrong 只承担正确声音配对的限定检验。
- 补充材料：完整 FM 初始化、REVE/CS、数据规模、预算、public prior、融合、episode、年龄与阶段、所有有效弱／反向结果、已修正的输入访问问题。

## 预先承认的范围

共享是指定训练与读出下的可迁移预测关系；不是神经表征完全相同。个人参数可能反映稳定的测量、信噪比与神经差异，不能全部归为脑机制。公共五个一秒窗互相重叠，儿童三段为编码前 mask 敏感性；都不是行为反应时。预测 log-score 增量是 decoder-dependent evidence，不是脑中总信息或精确条件互信息。HA/CI/TH 间的直接效应差属于观察性人群差异，不是助听器／植入治疗因果效应。

三轮是科研范围上限，不是阳性结果上限，也不是保证某个期刊接受。结束时交付明确的证据和边界，不能再用换故事或换模型延长研究。


---

## 原文件：docs/01_EXISTING_EVIDENCE.md

# 已有证据：哪些支撑主线，哪些还不够

基准：GitHub `3da8cf5758214c0cf87a1f1c8d67fb84b574000e`，2026-10-20。下列均为既有结果；新 ALN3.6 尚未运行。区间的具体 family、单位和统计法随原报告保留，不能跨表相减。

## 可保留的实质发现

| 证据 | 已见结果 | 对论文的作用与边界 |
|---|---|---|
| 真正 full CB 对同访问 local | 三 seed 平均 unified 风险改善：DTU +0.213 [0.129,0.297]；FAU +0.141 [0.099,0.184]；Federici +0.180 [0.113,0.246] bits/5s query | 有效模型基础已成立；不用再用大量普通性能格子证明 CB 能训练 |
| 声音历史之外的包络读出 | CBpre−local：DTU +0.008995 r [0.000566,0.017424]；FAU +0.011993 [0.004213,0.019772] | 收益不限于 native 检索，但仍是混合源人群中的 held-out-person 读出 |
| 预训练初始化的声音属性贡献 | CBpre−CBrand env_history：DTU +0.015250 [0.007849,0.022651]；FAU +0.015572 [0.008167,0.022976] | 支持保留通用预训练的有效声音证据；不是所有内容属性和人群都同样支持 |
| 时间读出的位置依赖 | 固定读出0→600ms损失 DTU +0.222192 r、FAU +0.098419；source重拟合恢复 +0.136274、+0.030371，四项原同时区间均为正 | 说明读出关系对输入位置敏感；还不是个人时间补偿或神经潜伏期 |
| 个人支持有真实收益 | DTU U30 rank4−zero-step：local native +0.092691 [0.035161,0.150222]；CB native +0.040873 [0.015352,0.066394] | 不应宣布个人适配失败；但旧支持与query同role且干预非纯时间读出 |
| 儿童先验的科学读出 | AP−XM full AUC +0.009193 [0.000611,0.017774]；history log-score +0.001817 [0.000521,0.003113]，64人 | 儿童不是无信息案例；AP−XM仍是训练包比较，不是正确配对的纯效应 |
| 儿童严格history接口 | AP EEG−B1均值 +0.002314、EEG−strict twin +0.003470 bits/trial | 已有当前证据的方向；这是描述均值，不能补写尚未算出的新区间 |
| 听觉续训低人数价值 | DTU seed3401、50% source people：native +0.15609 [0.05660,0.25557]；相对100%的交互 +0.13864 [0.04979,0.22749] | 保留这一明确阳性；unified对应结果未分辨，不能称普遍替代源人数 |
| FAU人群收益差 | HA−CI 的 CBpre−local 改善差 +0.117080 [0.022389,0.211772] bits/query | 是直接效应差的证据，不是训练从未见过CI/HA，也不是共同神经编码已成立 |

## 不能继续作为主创新的分支

**Episode 的适配后优势大多在适配前已经存在。** 已发布记录的均值重算显示：seed3401 local-native 的 episode优势 zero-step 0.035129，U30/20steps 0.036488，适配增量交互仅 +0.001359；seed3407对应 0.043400、0.034325，交互 −0.009075。此处只有描述性点估计，不给不存在的交互区间。适配后模型的有效优势保留，不能写成已经学会更有效地利用个人支持。R1仅补一个CPU直接交互区间，作为补充材料关账，不开新的episode。

**正确听觉配对不是已证明的统一原因。** matched AP/APwrong V2 的 DTU主风险差 −0.00159、FAU −0.02091，私有AUC差 +0.00290，相关区间均包含0；这不抹去AP−S/旧AP−XM阳性，也不等于“配对完全没用”。新包只在儿童的同一科学接口上完成必要对照，不再扩全公共任务矩阵。

**融合、选择策略、训练预算和规模曲线有有效结果，但不再各自发散。** 例如local+CB融合相对CB direct有益；相对两CB的native差 +0.025494区间跨0。DTU 2×预算相对1×的 CB效果变差。这些结果限定现有实现和日程，不证明一般天花板，也无需继续4×/8×。

## 真正缺的证据

1. 本研究训练全过程排除整个听觉组之后，固定群体声音读出是否仍可用。
2. 同一表示／同一query上，个人时间重权是否增加超出 history 校准与整体 EEG 标定的预测价值。
3. 在儿童中，这个增量是否涉及当前声音对应的 EEG，而非仅有限历史或个人基率；正确声音配对对它是否有额外贡献。

## 精确来源

所有下列路径均位于同一固定提交的 `docs/auditory_alignment_v3/`：

- `TRUE_FULL_PAIRED_EVIDENCE.md`
- `aln35/SCIENCE_PRIVATE_RESULTS.md`
- `aln35/SCIENCE_V2_READOUT.md`
- `aln35/HISTORY_INTERFACE_RESULTS.md`
- `aln35/SUPPORT_EPISODE_SELECTION_INTERPRETATION.md`
- `aln35/EPISODE_REPLICATION_S3407_RESULTS.md`
- `aln35/AP_WRONG_RESULTS_V2.md`
- `aln35/CBAUD_PEOPLE_RESULTS.md`
- `aln35/FUSION_ATTRIBUTION_RESULTS_1047619.md`
- `NEW_LANES_EFFICACY.md`
- `RELEASE_034.md`

`SOURCE_INDEX.json` 给出固定提交、路径、字节SHA256和可点击URL。原始统计完整保留在GitHub相应results中。该提交的发布快照为 CBAUD_PEOPLE20/20、episode3407 10/10；四条旧尾巴当时还剩39/10/9/74。现场进度必须另查，不能将这些数字写成接包时实时状态。


---

## 原文件：docs/02_ROUND1_DESIGN.md

# 第一轮：两种直接干预，一套嵌套读出

版本：ALN3.6 / R1。主seed3401。所有新增科学比较登记为 `prospective_protocol_after_2026_10_20_result_informed_design`：利用既有结果形成的新方案，不冒称从未看过任何外层数据的预注册确认性发现。

## A. FAU：训练排除整个目标听觉组

将 CI、HA、TH 依次作为完全不参与本研究模型开发的目标组。其他组为source，包括合法TH dev；leave-TH时这些dev也必须排除。两种固定工具为既有有效local L1和query-anchored true-full CBpre。主训练用InfoNCE，不新增backbone×loss扫描；传统CS和REVE的现有竞争结果保留在补充。

沿用每种有效工具的实际父配方：local200 epochs、lr1e-3；CB100 epochs、backbone3e-4/head1e-3，full-onestep；详细绑定以04及真实parent resolved_config为准。不能把local缩到100后再称公平竞争，也不继承2×预算。checkpoint改为固定合法source ES的实际query NLL；适当温度／读出参数从source-fit内部独立校准，ES仅选择checkpoint。不是新的selector比较。

### 去重和范围

整个目标组排除后，source集合不随该组原五个人折变化。每seed仅2工具×3组×2content folds=12次唯一训练。目标组人仍按原5折输出60个eval cell，用于与历史身份/内容索引对齐；不是60次独立训练。每个目标人的两个内容划分先在人内平均。

训练键包含encoder、held-out group、content fold、seed、source身份／内容哈希、预处理／归一化、配置和代码哈希。所有目标组人不参与source encoder、数据尺度、history、时间probe、组合、checkpoint或正则选择。通用CB固定预训练权重可用；不接曾见FAU目标组的本项目听觉donor。CB原始预训练是否含同类听觉状态不可由本设计排除。

**主要检验是目标组内 `G0=R(H0)-R(E0)`。** 它不需要与不同source人数的pooled风险相减。旧pooled20个cell作为描述和既有个人读出背景；不得由pooled−excluded差宣称组特异性或组间共享程度，更不得宣称等效。三个组源人数/组成不同，原始风险排名不承担神经解释。

### 新FAU输入尺度

旧loader按每个人所有role一起做_std z；不能把它称source-fit normalization。新whole-group版本从既有stageB预处理EEG读取，按合法source组fit内容估计固定channel尺度，冻结应用到sourceES及目标人support/query。所有五状态共用它。记录channel顺序、均值/尺度和合法训练行哈希。既有离线滤波/ICA仍为继承预处理，不声称从原始电压开始的因果时间隔离。DTU/旧pooled/private保留既有权重的预处理范围并如实说明，不能靠改名变成新严格全链处理。

## B. 公共数据：直接区分共享声音证据、个人标定、个人时间读出

### 同一个科学目标

主声音目标固定为当前包络，history控制固定20/100/200/500ms的过去包络。目标按**唯一source-fit音频内容**估计均值/尺度，每content fold在两个工具/held-out-group之间使用同一合法音频坐标。不是按目标组人的EEG或query重新标准化，也不是将候选真实当前声音作为EEG模型输入。

主风险为source标准化当前包络的MSE；历史模型与EEG模型预测同一目标。报告 `H0→E0` 等差值及历史条件残差Pearson r作为读者熟悉的辅助端点。MSE、r、原检索bits不能相加或视为同一个信息量。历史控制只用于科学条件预测，不是宣称实际声音检索在部署时得到了隐藏query答案。

### 时间证据bank和等访问

固定既有center `[-200,0,200,400,600]` ms，每个encoder窗 `[c-400,c+600)` ms。每个窗的32维表征经source-only probe成为一个标量声音证据，K=5。用source上的OOF读出证据确定共享组合；原encoder可见过这些source人，因此OOF只保证读出层，不称whole-pipeline inner-person验证。

**E0、EC、ET全部看到同一完整五窗scorebank**。E0使用固定source组合；EC只改变组合的整体正尺度；ET额外改变相对时间权重。不允许E0只看单窗却让ET看五窗后把额外访问归因个人化。与旧单窗0ms结果的比较仅作为背景。

固定每个合法5秒段恰好8个anchor：0.8、1.2、1.6、2.0、2.4、2.8、3.2、3.6秒，实际索引为round(fs×秒)。source、support和query共用网格；输出并校验物理anchor唯一性，不重复导出加权，不改hop或用8个anchor声称8个独立听者。公共数值参考的总损失每anchor等权，λ=1对应这个固定密度；私有每trial等权。任何缺少完整8个合法anchor的段由几何规则整体标为不可用并报告，不能按表现保留部分点。

五窗联合访问约[-600,1200)ms。读出和支持/query选择的guard必须覆盖这个实际联合访问，不只沿用单窗guard。窗口高度重叠，权重不能当作神经潜伏期或反应时。

### 个人支持和query

- 目标人的source-fit内容提供support。选择固定自然U30：按该人可用fit段的物理时间顺序取前ceil(30%)的完整合法5s段；不看标签、group效果或query分数。记录实际秒数、段数、anchor数；不把它叫30%全部记录。候选source-fit与test内容独立。
- Query为该人的全部原source-test内容，所有状态同query。同人source-ES内容不作为新增个人择模集，也不能隐含用于调lambda。
- 支持与query必须验证原content group/part与物理样本访问范围；仅不同uid但重叠EEG不够。
- FAU整组模型中每个目标人都没有参与source学习。DTU及FAU pooled既有模型只使用其原outer-held-person，不能把别人的source人误作新目标人。

### 公共当前对应性控制 M0

仅增加一个不训练的固定E0评估控制：在每个目标人的Q内，按真实recording和segment起点排序，将完整5秒段的8个anchor×5窗scorebank循环错移一段；保持8个anchor相对位置、同一partner的五窗关系以及原query history/y不动。使用固定E0参数，不重训、不按损失选partner。至少2段时得到`R(M0)-R(E0)`；不足2段标不可估计，保留该人的所有真实主结果。该控制继承旧segment-roll思路，但使用本轮完整bank和稳定物理ID，不对anchor单独乱序。它是对应性敏感性，不能叫history条件随机化或纯神经因果控制。

公共H0固定为截距加四个过去包络lag的线性history模型；个人HP/EC/ET恰使用[1,同四个source标准化lag]五列，不把HP弱化为只有截距。主目标坐标在全合法source-fit音频内容上固定；每个source读出OOF行保留其对应H0 offset与窗口scores。a0用这些OOF行拟合。最后H0/window probes按全部合法source重拟合，但应用冻结的OOF score尺度和a0，不另换一个scaler、不在目标Q重标定。输出单位和坐标映射必须完全记录。

## C. 私有儿童：当前声音与历史的辨别

固定 matched AP/APwrong V2 的NCE、seed3401、相同初始化/曝光lineage，5个outer人折共10个冻结bundle。新AP需要新提取分段特征；旧AP−XM与新APwrong不可混为严格消融。兼容的S既有特征可做5个补充参照，不阻塞核心，也不扩J*/XM/loss矩阵。

保持64个儿童（HA55/NH9）；不要因信号、阶段、AUC或twin覆盖筛掉儿童。支持沿用自然U30完整物理block，query是后续独立blocks，保留边界guard；实际试次比例由block决定，旧规则平均约36.65%，不能标作精确30% trial。没有未见声音身份的声学内容轴，只能声称新儿童和独立block泛化。

source-only history基线沿用6档since-last-deviant的q0定义，儿童当前标签不进入history；实际历史标签来自实验已知的过去刺激序列。三个时间输入是编码前0–200/200–400/400–600ms masks。64Hz实际访问见03，且仍受继承离线预处理限制。三窗source-only logits形成K=3时间证据bank。

HP、EC、ET有相同的6档个人history收缩修正；EC添加固定共享EEG方向的整体正尺度；ET最多再增加两个source条件残差时间方向自由度，实际数量受source残差rank约束。使用自然support，不人为平衡类别，不做C10/H10。

### Strict twin

同儿童、同history、异block、非自身的partner由固定seed和合法索引决定，不接收当前y、预测分数或损失。三个窗口整体替换到同一partner。support partner只来自support，query partner只来自query，不跨集合，不回退到自身/同block。

real与twin共用真实source上冻结的H0、窗口probes、scaler、a0及时间基底，不重拟合一套twin source。E0仅在相同合法query交集替换scorebank。个人对照在同一twin-eligible支持行集合上分别拟合real-control和twin-control的HP/EC/ET；后者只替换完整K3 scores，当前history/y保留。两者再在同一合法Q交集比较。不能用real的全support对twin的较小support；完整自然支持/查询下的真实主分析另报。每次以替换后的scores和当前history重新调用冻结的时间投影，不只替换raw scores却保留real时间特征。

ET的real-control与twin-control差反映支持和Q两侧声音对应性的共同变化，不命名为单独query干预或纯时间机制。该对照复用本包数值拟合，不增加source训练。

无合法support twin时，该人twin-personal状态记`not_estimable_no_support_partner`，保留其所有真实数据结果；不能删出64人主分析，不能将缺失置零。twin是当前对应性敏感性，不是精确条件随机化检验：6档history不穷尽所有历史。

## 五状态和直接估计量

| 状态 | 使用的信息 |
|---|---|
| H0 | source-only历史预测，无EEG、无目标support |
| E0 | source-only历史加固定共享时间EEG组合，无目标support |
| HP | 个人自然support拟合历史修正，无EEG |
| EC | 与HP同一历史修正类＋共享EEG方向的个人正尺度 |
| ET | EC＋最多K−1个source确定的条件残差时间方向 |

`G0=R(H0)-R(E0)`：无支持共享EEG增量。`GC=R(HP)-R(EC)`：个人标定后的EEG增量。`DT=R(EC)-R(ET)`：额外时间重权收益。`GT=R(HP)-R(ET)`：时间读出后的EEG增量。`J=GT-G0`：个人化是否增加了公平history基线之上的EEG贡献。它们全部是同人同query直接计算的差／交互。

G0和DT是本轮主估计量；GC/GT/J/GH是预先指定的机制分解，分family同时区间，成员已在plans/round1.json冻结。主结论不能只用ET−E0，因为它混合history、尺度和时间。E0不成功而EC成功时，结论为“有限个人校准后可转移”，不能称无支持群体读出已经共享。

个人正则采用包内固定λ=1（标准化设计、sum loss + quadratic penalty）；一旦开始outer计算不得改。R1不新扫网格；使用凸拟合至数值收敛。不得按目标query退回E0；所有固定状态逐一报告。精确参数化见03。

## 一次必要的工程验证后完整运行

检查合法source组/THdev、fit/test内容与联合访问guard、source统计来源、真实full update、凸模型嵌套、错配partner合法性和同query对齐。正确性通过即可启动全计划，不要求r/AUC/p达到门槛。工程失败修复受影响依赖，不用表现好坏选择重跑。实际训练与缓存提取由server完成；包内合成测试不代表真实数据实验已完成。


---

## 原文件：docs/03_READOUT_CONTRACT.md

# ALN3.6：共享声音证据、个人标定与时间读出的最小合同

本文件定义可执行的 CPU 数值参考和 server adapter 必须提供的科学绑定。`src/aln36_readout/` 已实现 H0/E0/HP/EC/ET 的拟合、预测、风险与直接差分；**EEG 特征提取、source 重训、matched AP/APwrong 血缘核验和服务器数据接入不在这个模块中，不能把参考代码测试通过写成这些工作已经完成。**

## 1. 要判断的问题与固定范围

研究问题是：声音相关证据有多少能被共享读出直接使用；个人数据带来的变化中，history/概率标定和时间证据组合分别增加多少可用预测能力。当前假设允许失败，不要求个人更新或正确配对先验必然胜出。

公共连续结果采用 Gaussian 线性读出、五个时间位置的 source 声音预测 score，主要风险为按 source 目标尺度定义的 MSE。私有儿童采用 Bernoulli 读出、三个 post 分段的 source 当前刺激 logits，主要风险为 bits/trial。两种风险不跨任务相加，也不以相关系数或 AUC 的数值差替代 proper-risk 主对比。

R1 公共 source 的 whole-hearing-group 排除及其 12 次唯一训练、60 个评估 cell 由单独的 source binding/workpackage 执行：source 的 encoder、预处理统计、history 与 score 读出、a0、正则选择都必须满足那个合同。模块不自行把 person-held-out 结果升级为 group-held-out。私有仍使用本轮指定 matched AP/APwrong 的 outer-child 排除，所有 source 拟合禁止外层儿童；不新增仅用少数 NH 训练全部 HA 的组排除实验。

私有先冻结 matched **new AP/new APwrong** 的同目标、同轨迹来源；不能把旧 AP 的 science cache 与新 APwrong 拼成一对。S 仅在已有合法特征且血缘明确时作为附加参考。R1 只用自然 U30 支持及零更新共享基线，不增加 C10/H10、支持比例、梯度步数或32维个人残差矩阵。R2 按完整固定合同复制 seed3407，R3 不新增模型搜索。

## 2. source 必须先产生什么

每个 source 实例输出以下固定对象，再对每名目标听者应用；所有尺度、列顺序和常数只在允许的 source 上确定。

| 对象 | 数值形状 | 含义 |
|---|---|---|
| `offset` | `[n]` | H0 的 source history 预测。Bernoulli 为 logit q0 加 source history 截距；Gaussian 为同一 source 尺度的 history-only 均值预测 |
| `history_design` | `[n, P]` | 可由个人支持更新的小 history 基底；source 标准化，列顺序固定；需要截距时显式含常数1列 |
| `scores` | `[n, K]` | source 拟合、source 标准化的时间 scorebank；Bernoulli K=3，Gaussian K=5 |
| `a0` | `[K]` | source 固定的共享时间组合；`Eagg = scores @ a0` |
| `time_basis` | `B[K,r]`、`C[P+2,r]`、`scale[r]`，`r <= K-1` | source 系数方向、nuisance投影系数与残差白化尺度；必须作为同一变换冻结并应用 |
| 三个 `ridge_*` | 正有限标量 | source-only 先固定的 history、整体 EEG scale、时间对比收缩强度 |

上游 source 拟合必须使用同一个 H0 offset 来拟合 a0。E0 定义为 `offset + scores @ a0`，模块不会暗中另估一个 EEG 截距。若 source 读出确实需要新的截距，应在 source 合同中明确构造共享的 offset/score 定义，不能在目标 Q 上补一个截距。

公共 H0 固定为截距加20/100/200/500 ms过去包络的source线性history预测；HP/EC/ET的 `history_design` 固定为 `[1, 同四个source标准化的过去包络lags]`，P=5。private `history_design` 固定为截距加5个固定 source 标准化的 history-bin 对比，P=6，覆盖既有六档 since-last-deviant。HP、EC、ET 的 history 列、正则及支持样本完全相同。不得仅给 HP 一个弱截距，却把更丰富的个人 history 结构留给 EEG 模型利用。私有六档对象不是完整刺激历史，公共四个历史lag也不是完整听觉上下文。

公共 K=5 按 `[-200, 0, 200, 400, 600]` ms 的已注册输入窗中心顺序；private K=3 按 `[0–200, 200–400, 400–600]` 名义窗口顺序。现 private64 样本为0至578.125 ms，三个 mask 实际保留的样本时刻约为0–187.5、203.125–390.625、406.25–578.125 ms。必须保存实际 sample indices 和 mask 位置，不能仅保存窗口名称。

私有窗口 mask 在 encoder 输入之前作用，不允许先编码完整 EEG 再把输出 token 改名为“早/中/晚”。继承的离线滤波与整记录归一化仍需如实记录；这些 post 样本访问不能自动成为原始信号的因果时间隔离。公共1秒窗存在重叠，不产生行为RT或神经潜伏期估计。

窗口 probes、history offset、score 标准化和 a0 均须 source-only。本轮固定3折source-person读出交叉拟合：按稳定身份及seed分折，所有窗口probe、history及相关尺度只在该读出折的source训练人拟合，在折外source人的合法ES内容产生OOF score。公共各窗口EEG score先输出在共同的source-audio目标单位，不能各自换一个不可比目标单位；private各窗口输出同一定义的source logit证据。a0使用每行对应的OOF history offset与OOF窗口scores拟合，不能把OOF score配上看过该行的full-source history offset。

source encoder可能见过这些source人的训练内容，因此这个划分仅是读出层。保存3折roster、各拟合行、OOF offset、OOF score及参数哈希。最终H0/window probe在全部合法source上重拟合，但score标准化仍绑定冻结的OOF score mean/std，a0及时间残差投影也使用这套既定坐标；禁止另拟合一套full-source score scaler后混用旧a0。最终重拟合可能带来stacking分布偏差，按真实目标预测如实评价，不能用目标Q重标定来消去它。

源侧ridge候选如沿用content_time的既有8点网格，仅在读出训练折的source ES以本轮risk选择，不用OOF-held-source人先挑参数再称OOF。冻结 encoder 下的读出交叉拟合不能冒称整个 encoder 的独立 inner-person 验证。source 选择完毕后才打开本轮外层 Q 结果。

## 3. 五状态及真正嵌套的时间干预

令 `H` 为 history design，`m = scores @ a0`，`N = [1, H, m]`。真正进入 ET 的时间特征是 **`Z = (scores @ B - N @ C) / scale`**：`B`、`C` 和 `scale` 全部只在source拟合并冻结，support/Q都调用同一 `TemporalBasis.project(scores, history)`。不能只用残差检查rank、在拟合时却仍传原始 `scores @ B`。

| 状态 | 线性预测量（Bernoulli 再过 sigmoid） | 个人参数与收缩中心 |
|---|---|---|
| H0 | `offset` | 无 |
| E0 | `offset + m` | 无 |
| HP | `offset + H @ delta` | `delta -> 0` |
| EC | `offset + H @ delta + beta * m` | 同类 `delta -> 0`；`beta >= 0, beta -> 1` |
| ET | `offset + H @ delta + beta * m + Z @ gamma` | 同 EC；`gamma -> 0` |

HP/EC/ET 各自在同一支持上联合拟合其允许的参数，history 系数不强制数值相等，但允许的函数类、先验中心、惩罚强度与数据完全相同。EC 的正 scale 允许整体 EEG 证据强度/概率尺度变化，不允许通过一个负 scale 把所有声音证据反号。ET增加source条件残差时间方向，不是任意32维个人解码器。仅有`a0 @ B = 0`不足以解释为新增时间方向：近共线原始score可以通过gamma廉价重现history或共享m、绕过delta/beta的ridge；实际残差化与source单位白化用于消除这个源内重复通道。

初始化与惩罚均公开：HP 从 `delta=0` 开始，预测恰为 H0；EC/ET 从 `delta=0, beta=1, gamma=0` 开始，预测恰为 E0。所有个人参数以这些值为收缩中心；EC 是 ET 在 `gamma=0` 的严格子模型。**H0 与 E0 是不同的 source 基线，不要求 E0 风险优于 H0。**

拟合目标为总支持损失加

`0.5 * (ridge_history * ||delta||^2 + ridge_scale * (beta-1)^2 + ridge_time * ||gamma||^2)`。

HP 不含后两项，EC 不含 time 项。Bernoulli 拟合损失是总 NLL（nats）；评估才换成 bits/trial。Gaussian 拟合损失是半个总平方误差，评估为 MSE。公共固定每个完整合法5秒段8个anchor（0.8:0.4:3.6秒，round(fs×t)，无重复）；总损失每anchor等权，λ=1明确绑定这个密度，不能靠加密网格改变有效收缩。私有每trial等权。使用总损失意味着支持越多，固定 source 先验相对越弱；不要把 source 选择的 lambda 在不同代码中悄悄当成均值损失的 lambda。三个lambda在R1固定为1，仍显式传入且严格为正，不在个人Q上选值；R2保持不变。

Gaussian 使用带正 ridge、仅一个非负边界的精确二次求解；Bernoulli 使用带解析梯度和 beta 下界的 L-BFGS-B。保存优化终止、目标值、identity 初始目标值与每支持行归一化的投影梯度。未收敛抛出 `FitFailure`，不发布为有效的“零效应”。全部标签相同的支持仍能在正惩罚下得到有限预测，同时保存类别计数；这不是 CS 单类别适配的验证。

### 时间基底的可识别性

`build_time_basis(a0, source_scores, source_history_design)` 不接标签。先构造系数空间内与a0正交的K−1方向B0，再在source上用`N=[1,H,m]`拟合`C0`，得到`X B0 - N C0`。nuisance列先按source RMS缩放再求投影，最后还原原列单位，以免很小但非零的共享m被数值rank判断漏掉。

对这个source残差做SVD，R1固定相对rank阈值`1e-8`：保留奇异值大于`1e-8 * max(||X-source_mean(X)||_2, 1)`的方向。用同一SVD旋转B0与C0，再除以每个source残差的总体标准差（保留奇异值/√n_source）。因此source上的Z具有单位方差、相互正交，并与source的截距/history/m正交；实际传入support/Q的是这个变换后的Z，绝不在target重新回归投影系数或重估尺度。

`TemporalBasis`保存`matrix`(B)、`nuisance_coefficients`(C)、`residual_scale`、`history_dimension`、nuisance数值缩放、奇异值、rank及两个数值阈值。`project(scores, history)`检查与source相同的列维度。构造basis时省略source history表示P=0，不能在target突然传入另一组history列。原始B仍满足`a0 @ B=0`；残差化后的完整特征定义才是拟合与解释对象，不可仅公布B而省略C/scale。

`||a0|| <= 1e-12` 时不存在本合同定义的稳定共享系数方向；或所有剩余方向不可识别时，明确输出空时间基底，ET 与 EC 相同，`temporal_test_available=false`。此时数值 time_increment=0 是参数化退化，不是生物学等效或“没有时间信息”。名义K−1只有source条件残差满秩时才是实际新增自由度。两个数值阈值预先固定，不能根据支持/Q表现改变。

source条件正交不保证跨人群后仍统计正交或独立；目标分布改变时，冻结Z可能再次与目标history/m相关。可以记录目标无标签协方差作为诊断，但不能据此重拟合Q投影、改rank或挑人。`time_increment`应准确称为“source条件残差时间对比的额外收益”；仅凭它仍不能证明独立于所有目标域标定变化的纯神经时间机制。需结合公平EC、匹配history与strict twin，以及预先固定的复核范围判断。

## 4. 私有支持、query 与 strict twin

调用 `support_contract.private_split` 已有物理时间绑定：按时间顺序前 `ceil(0.3 * blocks)` 个 block 为支持池，继承 `support[:-1]`、`query[1:]` 边界删样及 full-epoch guard，剩余 block 为唯一固定 Q。U30 是这个 block 合同，不是保证30% trial；逐人输出真实支持/查询trial与block数、类别/history覆盖。固定自然发生的支持与 Q，不用标签均衡或 H10 选择改变其先验。

H0/E0先独立产生和保存，不应因个人拟合失败或无合法support而消失。无support时HP/EC/ET标不可估计，不把它们设成有效零收益；参考fit需要非空support，由server处理该边界。五状态在可拟合时均在同一个Q评价。H0/E0 不访问目标标签；HP/EC/ET 只访问该人的支持标签。fit API 没有 query 参数，query labels 仅进入独立评价器。接口分离不能证明调用者没有错传样本：server adapter 仍须检查 source fit/calibration/selection 与外层目标的合法排除、support/Q 不相交、真实时间边界及 query hash。

strict twin 按同儿童、同既定 history、不同物理 block、非自身 trial 选伙伴；三个 private 时间 score **整行替换为同一个伙伴**，不能给三个窗口各配一个 trial。映射按固定seed/稳定ID确定，不读当前标签或效果。

公共固定采用02规定的非学习M0对应性控制：在每个目标人的Q内按物理段顺序，把完整5秒段的8 anchors×5 scores整体循环错移一段，H与目标y仍留原位置，固定E0 source model且不重拟合。`R(M0)-R(E0)`是对应性敏感性，不是条件随机化检验；该控制不新建训练pipeline或训练矩阵。精确eligibility、段顺序和输出绑定以02/M0计划为准，不把它混称为private的同history异block twin。

本轮real/twin共用真实source上已经冻结的H0、窗口probes、score scaler、a0与TemporalBasis，不另拟合twin source，不把两种source训练协议混用。个人支持伙伴只在支持内；Q伙伴只在合法Q内，不能跨split借用。没有合法伙伴就明确缺项，不回退到自身/同block。

E0在同一合法Q交集只替换完整K3 score行、保留当前history/y，参数不变。个人对照的real-control与twin-control使用完全相同的twin-eligible支持行集合与Q交集：分别调用一次五状态fit，twin仅将支持scores换为partner整行，当前offset/history/y保持不变；Q同理。因此HP一致，EC/ET各自在允许的真实或错配支持上拟合。严禁real-control使用全support而twin只用较小子集。完整自然支持/Q下的真实主分析独立保留，不用对照交集替代。

替换score后始终重新调用`TemporalBasis.project(swapped_scores, current_history)`，不能换scores却沿用real Z。ET的twin−real-control风险差包含支持和Q两侧对应性变化，不称仅Q干预或纯时间机制效应。比较真实与twin的完整ET风险以及同各自EC→ET增量时，EC也按对应real/twin支持拟合。分别保存全Q主值、对照支持/Q交集、各自分母与缺项；不按效果选择交集。

## 5. 实际数值 API 与 server 记录 schema

`fit_nested_readout` 的全部数据入参是 `support_offset[n]`、`support_history[n,P]`、`support_scores[n,K]`、`support_y[n]`，以及已固定的 `a0`/`TemporalBasis`、family、三个ridge值。数组为有限 float64；binary y 仅0/1。source 配置和 target 运行数据没有隐式搜索或文件读取。

`evaluate_readout` 单独接 `query_offset`、`query_history`、`query_scores`、`query_y`，不拟合、不更新、不选择。`fit.predict` 和 `fit.predict_linear` 可在无标签下输出五状态预测。`fit.as_dict()` 输出参数、support计数、basis和拟合 receipts；不包含 raw EEG 或query labels。模块每次对应一个 source实例×目标人；禁止先把不同人的trial拼成一个“大样本”后解释为人群证据。

server adapter 需为每个调用另存以下绑定记录（这是外层适配器 schema，不是本模块声称已经实现的 JSON CLI）：

```json
{
  "analysis_origin": "prospective_protocol_after_2026_10_20_result_informed_design",
  "dataset": "private_bdf",
  "identity": "bound_identity",
  "group": "bound_group",
  "seed": 3401,
  "outer_split_id": "bound_outer_split",
  "arm": "matched_AP_or_APwrong",
  "family": "bernoulli",
  "source_record_sha256": "actual_sha256",
  "source_checkpoint_sha256": "actual_sha256",
  "source_fit_population_ids": [],
  "source_calibration_population_ids": [],
  "source_selection_population_ids": [],
  "held_out_source_groups": [],
  "history_contract_id": "bound_source_history",
  "score_contract_id": "bound_post_masks_and_source_probes",
  "source_scaling_sha256": "actual_sha256",
  "source_a0_and_basis_sha256": "actual_sha256",
  "support_set_id": "actual_support_hash",
  "query_set_id": "actual_query_hash",
  "support_counts": {"trials": 0, "blocks": 0, "class": {}, "history": {}},
  "query_counts": {"trials": 0, "blocks": 0, "class": {}, "history": {}},
  "twin_scope": "real_or_strict_same_history_other_block",
  "twin_map_sha256": "actual_sha256_or_null",
  "feature_cache_sha256": "actual_sha256",
  "fit_parameters": "fit.as_dict()",
  "evaluation": "evaluate_readout()"
}
```

示例字符串/空名册/0计数只是字段示意，真实调用必须填实值；不把它作为观测样本。公共同一 schema 换 dataset、group排除合同、K5 score contract 和 Gaussian family。适配器导出通用 paired-analysis observation 时应依其实际 schema 映射，额外血缘放metadata，不能把本记录任意字段直接塞入旧工具的受限provenance。

## 6. 输出估计量及人群统计

`evaluate_readout()` 返回五状态的平均 `risk`、`n_query`、单位和下列直接式：

| 输出字段 | 精确定义；正值表示对应收益 |
|---|---|
| `RsharedEEG` | `R(E0)`，这是风险本身 |
| `RpersonalEEG` | `R(ET)`，这是风险本身 |
| `shared_EEG_gain` | `R(H0) - R(E0)` |
| `personal_calibrated_EEG_gain` | `R(HP) - R(EC)` |
| `personal_EEG_gain` | `R(HP) - R(ET)` |
| `history_calibration_gain` | `R(H0) - R(HP)` |
| `time_increment` | `R(EC) - R(ET)` |
| `double_difference` | **`[R(E0)-R(ET)] - [R(H0)-R(HP)]`**，等于 personal_EEG_gain − shared_EEG_gain |
| `calibration_double_difference` | `[R(E0)-R(EC)] - [R(H0)-R(HP)]` |
| `total_EEG_risk_improvement` | `R(E0) - R(ET)`；不能单独命名为时间重权收益 |

先同一人、同一物理 Q 构造差值；有内容fold则按既有合同等权平均，再平均seed，最后整人统计。代码只返回逐人算术，不做bootstrap、不推断独立人群n。人口区间交给包内绑定好的 paired 工具，固定小 family、共同完整人集；不能把各状态独立CI相减，也不能把两个seed当成两个队列。

private full自然Q与 strict twin合法交集各自绑定 query_set_id。AP/APwrong需要同一目标query与合法 matched source lineage；新旧AP不能混用。退化rank、无支持、缺类、无twin与拟合失败各自留状态和覆盖，不能静默只保留有利儿童。

## 7. 推论边界与三轮收束

EC→ET若增加独立Q上的当前声音证据，且真实EEG相对同history异block twin也保留优势，才支持“固定共享时间组合尚未充分使用个人可用证据”。若只有HP/EC改善，结果属于history/整体标定；若E0已好而ET无额外收益，保留共享证据，不据此否定生物学个体时间差异。AP/APwrong相近则正确配对先验的附加贡献未得到支持，不能抹去共同有效的读出结果。

public broad-window map检验时间坐标改变和群体读出重拟合；private三窗组合检验个人相对时间重权。两者统一的是读出迁移问题，不是相同生理时延。无行为RT，不声称快/慢、潜伏期或纵向发育；权重受分段mask、共线性和固定source表示影响，主要结论使用风险与增量，系数只作辅助。

当前缓存若缺失，保存matched源checkpoint、source readout和绑定，进行一次冻结forward导出需要的窗口特征/scorebank。已有fit/evaluation unit可直接复算风险差分；重新构造窗口probe/个人时间读出需要对应窗口特征或完整scorebank，不能从已有全窗AUC或均值NLL逆推。整个模块不授权删除任何正在使用的source或唯一cache。

## 8. 实际验证

运行 `python -B -m unittest discover -s tests -p test_nested_readout.py -v`。七个合成测试覆盖：零共享方向/降秩；仅基率变化不伪造时间旋转；Gaussian K5与Bernoulli K3真实时间旋转在独立Q恢复；非负scale边界与嵌套/identity初始化；单类别支持有限且评价不改参数；fit接口不含query及直接双差代数；近共线时间score不得绕过beta ridge廉价模拟整体gain的反例回归。后一个测试还检查实际source投影后的正交与单位协方差。它们验证数值参考，不证明服务器数据绑定、source排除或EEG科学结果。


---

## 原文件：docs/04_SERVER_BINDING.md

# 04 — Server 接入、源人群排除与执行身份

## 4.1 本文件的执行地位

本包延续 ALN3.5，制作时核对的公开源码为 W-Yinghao/auditory 的 3da8cf5758214c0cf87a1f1c8d67fb84b574000e。它把接下来三轮收束到声音证据共享、个人读出可用性及时间组织的有限比较。旧结果、旧执行身份与有效不利结果全部保留。

**当前仓库没有可以直接启动本轮全部实验的现成 ALN3.6 CLI。** Server agent 须在独立的 auditory_alignment_v3/aln36/ 接入新协议，登记新的代码、设计、数据选择和来源哈希；复用下文已有组件，不修改正在运行的 ALN3.4/3.5 模块或将旧记录改名冒充新执行。包内参考工具及文档不等于生产实现，更不等于真实 EEG 训练已完成。

本轮工程检查通过后，已授权的完整单元继续执行；不再等待论文措辞、显著性、性能入场线或逐项人工 go。只有实际无法满足身份、内容、数据授权或资源约束的问题才阻塞其受影响单元。这里不授权整批取消旧作业、清空 holds、删除 checkpoint 或启动无关新实验。

## 4.2 R1/R2 的真实训练数与评估数

R1 使用 seed 3401；R2 按本包冻结的相同协议重复 seed 3407，不因 R1 的结果方向更换工具、目标组或指标。R3 不新增模型 family。

| 面板 | 唯一训练来源 | R1 评估 bundle |
|---|---|---:|
| FAU 整个目标听觉组排除 | local、CBpre；目标组 HA/CI/TH；2 个 content folds；默认每组/内容/工具只训练一次 | 2 × 3 × 5 person folds × 2 content folds = 60 |
| FAU 旧 pooled 描述参照 | 复用原 20 个相同工具的外层排人 source，不重新训练 | 20 |
| DTU 新个人支持协议 | 复用原 20 个相同工具的外层排人 source，不重新训练 | 20 |
| 私有 matched AP/APwrong | 复用同一修订 sampler、同目标合同的 2 arms × 5 outer folds；必要时补冻结特征提取 | 10 |
| 私有 S 补充参照 | 仅在已有特征、trial、outer fold、query 和历史接口兼容时复用 | 可选额外 5 |
| 合计 | FAU 默认 12 次新 source fits，其余为复用/提取/读出 | 110；兼容 S 加入时 115 |

FAU 的 5 个 person folds 继续作为原有目标人身份与结果分块。**当整个目标听觉组均已排除，目标组的哪一个 fold 正在评价不应再改变合法源训练人集。** 默认 source 使用所有合法非目标组的人及其 source-fit/source-ES 内容，因此 5 个目标 fold 共享一个 source checkpoint。每 seed 的唯一训练数为 2 工具 × 3 目标组 × 2 内容划分 = 12；R1 与 R2 总共默认 24。

Server 必须分别保存 source_training_signature 与 evaluation_signature：

- 训练签名包括 seed、工具及完整 recipe、目标组、合法源人 ID、fit/ES/cal 声音与样本 ID、输入预处理/统计来源、初始化、目标坐标、预算、checkpoint 规则及代码/设计哈希。没有改变训练输入的目标评估 fold 不进入训练签名。
- 评估签名另包括 source checkpoint 哈希、目标组、目标 person fold、content fold、support/query 绑定及读出条件。
- 按实际训练签名去重。不能为了凑 60 个数字复制同一训练、改 RNG 盐或给同一权重五个独立模型身份；同一 checkpoint 的多fold结果也不能当作额外独立 n。
- 每 seed 固定为 12 次唯一 FAU source 训练、60 个评估格。若实际绑定显示原先认为相同的 source 输入并不相同，先报告具体差别并修正绑定；不能静默增加训练，也不能将 60 个评估格解释成允许 60 次训练的额度。
- 以真实目标人作为推断单位，先汇总同人的两个内容重复，再按既定规则汇总 seed。共享 source 权重、fold、seed 和支持抽样均不增加独立人数。

## 4.3 FAU 整组排除：过滤必须贯穿整个学习链

FAU 人群元数据来自现有 cohort loader 与已冻结身份表。正式评估面板为 HA 29、CI 24、TH 14；额外 TH dev 人只可作为合法源人，不进入正式目标人 n。Server 重新绑定实际 roster/hash，不从本轮成功输出反推预期队列。

对于目标组 g ∈ {ha, ci, th}，先构造完整合法源人集合：

    source_ids = human identities whose group != g and test_only == false
    target_ids = registered evaluation identities whose group == g and dev == false

具体规则：

1. 排除目标组的全部 EEG，包括该组其他 outer folds、任何 dev/selection-half 身份和该组不在正式评估面板中的同源记录。leave-TH 时必须排除 TH dev，不能沿用“dev 一律放入训练”的默认条件。
2. 源模型的梯度、早停/选 checkpoint、音频—EEG目标映射、读出、温度、带宽、标准化、PCA/白化等所有依赖 EEG 或 EEG—声音配对的数据拟合，均不得访问目标组 EEG。
3. 合法源 fit 只取 source_ids 中、role=fit、kind=ss 的段；合法源 ES 只取同一 source_ids 中、role=es、kind=ss 的段。source-test 内容不进入梯度、统计拟合或 checkpoint 选择。
4. 听觉组筛选在产生 batch 索引与拟合任何统计量之前完成。允许底层只读文件中同时存在其他组，但所有数据消费者必须使用冻结的合法索引；不能凭“最后的 loss 只算 source 人”证明整个管线排除成立。
5. source ES 可以来自与source-fit相同的人、独立声音内容。报告为“源人内、内容分离的 checkpoint 开发”，不称 whole-pipeline inner-held-out-person 选择。新任务的目标组与目标人始终排除。
6. fit、ES、cal、target support、target query 各自保存人、组、content/part、stimulus UID、物理样本访问与角色哈希；任何 group、role 缺失或不一致必须显式报错，不默认为可训练。

现成入口及必须覆盖的默认行为：

| 组件 | 可复用内容 | 新接入必须处理 |
|---|---|---|
| auditory_alignment/data.py | FAU cohort、5人fold、2内容fold、段/刺激身份 | 74–89 行的 TH dev；109–115 行的角色与预处理；不能仅筛正式 panel |
| auditory_alignment_v2/train.py | Batcher 与按人平衡、去重刺激的训练 batch | 29–32 行默认人选择及49–53行 fit/es/train_p，必须替换为显式合法源集合 |
| auditory_alignment_v3/aln34/breadth_inner.py | metadata、训练索引、独立计划及训练 hook | 60–86 行的默认 dev 保留；不得直接复用作 leave-TH |
| auditory_alignment_v3/aln34/data_inner.py | 186–204 行 batcher/统计 hook | 非 inner axis 在194行保留 outer_fit；新group协议必须用合法 source-fit，不能继承全pooled统计 |
| auditory_alignment_v3/aln34/content_time.py | 冻结提取、声音属性、history残差、ridge与TG | 必须接入新的source签名/路径；旧混合组checkpoint不能冒充新group-excluded模型 |

新模块可以借鉴现有进程内 instrumentation，但使用独立 family/version 与上下文管理，退出后恢复 hook。禁止修改原全局默认后影响其他正在运行的 family。

### 4.3.1 输入标准化与预处理范围

现有 data.py 的 _stdz（38–41 行）按单个参与者的全部已加载 trial 计算均值/标准差；load_fau 在111行调用它，包含fit/es/test内容。它没有把不同人的EEG合并拟合，但不能称为严格 source-fit 内容统计。

新 FAU 接入须把学习型输入统计绑定到合法源fit，使用同一 source-only 通道统计冻结变换 source ES、目标人的支持和查询；不得利用目标组或 source-test EEG 估计 population 输入统计。读取现有 stageB 的预处理 EEG，在新 loader/缓存层实现此绑定，不覆盖原数据或旧cache，也不能在已经按全trial标准化的值上再套一层 scaler 就声称去掉了旧访问。

目标人的自然支持只供本包指定的个人读出干预。本轮不增加个人输入标准化：H0/E0/HP/EC/ET共用固定source尺度。不能让候选比共同基线多一个未登记的输入变换，也不能使用query统计。

保留历史滤波、ICA及记录级离线处理的真实范围。上述分离是新训练、统计、读出和选择阶段的分离，不声称追溯完成原始EEG因果滤波或在线预处理隔离。本轮不以重做全库原始预处理为前置主任务。DTU旧冻结模型的历史预处理原样保留并单列，不把它重标为新FAU预处理协议。

### 4.3.2 音频、初始化与 donor

- local 从该seed的合法新初始化开始，继承有效 local_aligned1000 结构与完整训练配方；不能从见过目标组的旧FAU local权重 warm-start。
- CBpre 仅使用已使用的原始通用 CBraMod checkpoint，记录实际文件及SHA256，并继承 query-aligned full_onestep_v1 的全量更新实现。
- 新FAU排组模型不得使用旧FAU pooled微调权重、项目内CB auditory-continued donor、AP/XP/J*/XM auditory donor，或任何见过被排除FAU组EEG的蒸馏/音频—EEG映射作为初始化或固定teacher。只过滤下游head不能消除这些来源访问。
- 纯声音、且不依赖FAU EEG的既定特征提取器可以复用；音频目标的均值/尺度/投影及声音history残差，只能依赖本任务合法source-fit声音，按既定源端规则开发，禁止使用query声音拟合统计。query的真实声音只用于规定评价目标/候选评分，不输入EEG decoder或参与适配选择。
- 原始通用CB预训练的听觉类别/受试者覆盖未由本包证明。论文与记录限定为“本研究FAU任务学习、校准和选择排除整个目标听觉组”，不能声称原始基础模型历史上从未接触这类听者。
- 此限制针对新FAU排组链。私有matched AP/APwrong是另一条已授权、目标队列排除的既有来源链，仍按其自身配对合同复用，不被误停。

## 4.4 保留有效工具的训练日程；只实施已决定的新选择规则

本轮不是再次竞争backbone/loss或降低local预算。制作基线的直接有效 parent 配方已核对：

| 工具 | 固定配方 | 代码证据 |
|---|---|---|
| local L1 | local_aligned1000，NCE，32维；200 epochs；AdamW lr=1e-3、weight_decay=1e-4；原cosine日程 | core.py:9,30,53–59；local_support.py:108–129；local_train.py:73–89 |
| CBpre | query-aligned full_onestep_v1；NCE；100 epochs；backbone lr=3e-4、head lr=1e-3；LLRD=1；从第一训练阶段全量更新 | run_aligned32.py:23–32；fm_dense.py:42；fm_aligned32.py；直接parent行 |

公开计划中的FAU直接parent例子：local ALN3X_84b5c4fd866b3b7a；CBpre ALN3X_124a413438c432c7。它们是配方来源，不是新排组模型的warm-start权重。Server绑定实际parent记录的 resolved_config、训练ledger、source/code hash并逐项比较；如实际来源不同，先据事实修正binding，不猜值、不静默换parent。

禁止把local改成100 epochs以节省收束成本；也不继承 doubled-budget 的local400/CB200，更不添加4×预算。每个模型保留实际更新次数、源人数、fit段数与训练曝光，因此不同源组之间不冒称等更新次数或等数据量。

### 4.4.1 唯一 checkpoint 选择对象：source实际true-query NLL

原local与FM训练器仍包含 es_loss − es_mismatch 的选择逻辑；新ALN3.6必须替换该选择分支，不能仅把字段改名。旧训练结果保留原定义。

本轮统一在冻结的source-ES query和候选音频池上，以实际native检索概率的true-query NLL选checkpoint：

    risk_bits = mean_queries[-log2 p(correct_candidate | EEG_query)]

要求：

1. query、合法候选集合、正确列索引、候选顺序及所有物理ID在第一次生产训练前冻结。候选池从合法source-ES内容建立、去重，不能用新batch随机负例改变每次风险的对象。
2. 用与最终评价一致的native评分/概率接口；温度及其他概率参数仅来自source-fit，或事先固定的source内部cal子集。cal不从目标组或query中产生。source-ES只负责checkpoint选择，不另扫gain/true-risk选择器。
3. 按既定评估节奏保存实际风险轨迹和epoch/update。候选包括合法初始状态及已登记训练节点；并列优先更早/更简单状态。所有训练按固定parent日程完成，不凭outer结果延长或提前中止。
4. 选择只使用上述真配对NLL。mismatch、相关系数、AUC、组差、个人适配收益可以报告，但不能进入checkpoint排序。
5. 新source的后续共同/个人读出使用这一固定选中checkpoint；不得为history、时间窗、不同目标组子集或个人查询各选一个更好的encoder。
6. 来源同人的独立ES内容用于此处选择是合法的既定层级；不要因此新造一整套inner-person训练网格。

若原score封装重建了自动pooled读出/温度，须在新封装中显式传入合法source集合。可借鉴 adaptation_policy.py:143–195 的重建和评分接口，但其自动training/ES选取不能直接不加筛选复用。

## 4.5 公共目标个人支持：自然U30来自source-fit内容，Q为全部source-test

FAU新排组source、FAU旧pooled参照和DTU旧排人source都使用新版本的同一目标支持/查询定义。旧ALN3.5支持结果保留，不改名复用。

对于每个目标人和content fold：

1. 目标支持候选只来自该人的role=fit、kind=ss内容；query固定为该人的全部合法role=test、kind=ss段/anchors。role=es不混入个人支持或query。
2. 按实验记录的实际顺序构造自然U30：在该人的source-fit内容全部合法5秒段中，取前ceil(0.30 × 段数)个完整5秒段；段内固定8个anchors。不得把整个声音part强行作为最小支持块而让名义U30变成全部fit数据。保存段数、秒数、anchor数、实际比例及所覆盖真实内容block；不看标签或query再挑段。
3. 同一个人的全局读出、概率/时间调整及低维个人读出，必须使用完全相同的U30输入权限和同一个Q。支持集合只按既定顺序/元数据产生，不按标签平衡、history覆盖、读出损失或query效果挑选。
4. block的稳定键来自真实刺激code/记录/part；支持选取的最小单位是上条完整5秒段，block仅作来源和覆盖记录。不要把数据bank拼接顺序假称临床时间。个体若不足以提供完整合法支持，保留no_legal_support状态，不从test内容借样本。
5. 由真实物理样本索引检查支持与query的EEG访问不重叠；覆盖五个一秒窗的联合[-600,1200)ms访问及segment-start规则。若需边界guard，只按冻结几何排除非法支持边界，不随结果改query。声音content/UID也必须符合既定fit/test分离。
6. 支持选择与干预拟合不读取query的标签、EEG、风险或组差。目标query的当前声音/历史只在规定最终评分中使用；它不是个人参数选择的数据。
7. 所有条件输出相同query_hash及显式support_hash、source_fit_content_hash；没有合法支持时保留该人的H0/E0，HP/EC/ET标为not_estimable_no_legal_support，不将未更新基线冒称个人拟合结果，不删除人或偷偷换支持协议。

旧 support_contract.dtu_split 在同一role内取前30%段、后70%段，见66–85行；support_coverage.py:133–146对outer直接传test role。该规则不能满足本轮跨内容支持定义。新实现保留其物理guard、ID和访问记录思想，**不能直接调用它后把结果标为本轮自然U30**。

旧content_time cache只有source fit/ES与outer test，缺outer人的fit内容特征。新公共提取器须补这部分，并复用已有兼容的目标query特征；使用新的cache identity及访问元数据，不把额外支持行塞回旧cache冒充原输出。

新FAU排组模型的60个目标fold评估可以共用12份权重和对应特征库。FAU pooled/DTU旧模型只按各自原outer fold绑定；它们的20份不同source不能因新模型可去重而随意合并。

## 4.6 私有AP/APwrong来源与history接口

本轮10个核心私有bundle只绑定 ALN3.5 matched AP/APwrong 的同修订sampler、同曝光/目标合同、同seed、同outer fold配对。不能用旧prior_science里的原AP替换matched AP，再与新APwrong构造所谓纯配对消融。

可复用入口：

- auditory_alignment_v3/aln35/ap_wrong.py：matched donor/target来源链；
- auditory_alignment_v3/aln34/prior_science.py 与 private_current_time.py：冻结特征提取、实际trial与时间访问；
- auditory_alignment_v3/aln35/history_interface.py:120–164：B0、等接口校准B1、EEG offset logistic、strict异block twin；
- auditory_alignment_v3/aln35/support_contract.py:30–63：私有物理block支持/query边界；
- auditory_alignment_v3/aln35/science_binding.py：真实query身份、roster及来源哈希。

Server须核对matched来源是否已经有兼容逐trial特征；没有则补冻结前向，不重新训练兼容模型。可选S只在接口、trial与query完全兼容时增加5个评估bundle；缺失只标明该补充参照，不阻塞AP/APwrong主比较，也不为S另开新训练族。

私有数据没有公共连续语音那样的独立声音内容合同。这里明确为“新儿童＋独立物理block/固定query＋history受控”，不称未见声音内容泛化。history表、校准、EEG与twin拟合必须遵守各自source/support权限；strict twin在支持拟合时只能从支持内的同history、异block、非自身trial建立，不能从query借partner。缺合法twin保留为显式缺项，不能用同block或self回退。

## 4.7 旧pooled、DTU、已有科学读出的用途

FAU旧pooled的20份结果是有用的描述性参照。新排组source与旧pooled在人群规模、预处理/选择版本等方面不同；不得把 pooled − excluded 的差值解释成听觉组信息的因果效应或纯粹同组数据价值。本轮主科学比较在固定新source、固定目标query内形成：真实声音与适当历史/错配参照、固定共同读出与个人干预。

DTU旧source与原FAU pooled的query/目标读出可按兼容签名复用，但新自然U30需要新输出身份。新结果来源字段同时保留parent执行、旧预处理、当前支持定义和当前统计版本。

公共 content_time.py 的共同ridge与5×5宽窗TG、SCI_R2的严格raw时间参照、私有SCI_R1的raw/latent lag都已存在。复用这些工具完成本包指定的有限时间问题；不得按outer峰值挑窗口，也不以新包为由重做全部模型×特征×窗口矩阵。宽窗中心和遮罩敏感性不命名为单点神经潜伏期。

## 4.8 实施顺序、工程完成条件与资源

建议在独立ALN3.6模块中依次完成：不可变来源binding → 合法source索引/统计与训练签名 → 新source训练/true-NLL选择 → 一次冻结支持/query特征提取 → 固定读出干预 → 逐人汇总与本包规定的成对推断。实际模块和CLI在实现完成后写入接入回执；本文件不提供虚构可运行命令。

足够的工程检查是：

1. 三种目标组均验证完整源排除，特别覆盖leave-TH的dev身份；fit/ES/query角色及内容集合与manifest一致。
2. 所有normalizer、audio head、概率参数及history/条件残差具有合法拟合ID；目标组没有进入source梯度、统计或checkpoint选择。
3. local/CB两工具各一次代表运行确认实际EEG访问、完整parent日程与trainable参数/梯度更新ledger；CB不得重现旧prefix-only更新。
4. 固定source-ES candidate索引、风险值与独立直接概率计算一致；不得将gain写成NLL。完成不依赖风险方向。
5. 12份默认source与60个评估cell映射可验证；不会重复训练同一签名，不会给一个目标人制造五个独立观测。
6. U30/Q物理访问、声音内容及所有干预的query hash一致；个人拟合不得访问Q。
7. 私有matched AP/APwrong来源与trial/history/twin限制可验证；旧local全零pre不再作为真实刺激前证据。
8. 规范逐人输出能通过现有有限数值、重复行、完整性和角色校验；缺失与nonregular显式输出，不要求统计显著。

检查覆盖上述实际风险后立即执行完整已授权单元，不追加泛化“安全审计”、论文框架批准或科学绩效门槛。失败只冻结受影响签名及真实下游，保留失败回执与其他有效结果；修复产生新版本。

全项目运行GPU总数继续最多10张，包含旧尾巴、新source、冻结提取和工程probe。CPU读出/统计独立调度；不为多个lane分别申请10张。只操作本项目精确归属的jobs，保留旧在跑源码与现有holds。

R1/R2各默认12次新source训练；60/seed是评估格数。旧时长只能作估算依据，不能写成新包完工承诺：现成FAU content/time单元约37–41秒，旧FAU倍预算训练样本CB约1786秒、local约382秒，硬件/缓存/预算不同。首个代表完整新source记录训练、true-NLL评价、特征提取、IO和CPU拟合成本后更新剩余估算；不得为节省时间削弱local parent或偷偷扩展训练预算。

## 4.9 Server必须形成的最小绑定与回执

在现有私有输出根下建立独立aln36目录，具体绝对路径由server绑定，不将公开包里的示意路径当现场路径。至少保存：

- 来源与代码binding：实际Git HEAD、parent records/checkpoints、通用CB初始化、stageB/声音特征/roster与角色manifest哈希。
- source manifest：每组/内容/工具/seed的合法源ID、fit/ES/cal样本、所有统计拟合权限、原parent日程、source_training_signature与去重映射。
- evaluation manifest：110个R1评估bundle（兼容S时115）的预期身份、content folds、source checkpoint、U30/Q/twin binding及actual access；R2单独记录seed重复，不能增加独立n。
- 实现与工程回执：真实CLI、版本、smoke与production区别、训练ledger、风险选择轨迹及实际成本。
- 科学输出：所有有效方向的逐人结果、完整/预期覆盖、失败/缺失/nonregular、直接成对差，以及旧pooled参照的限定解释。

旧records、旧统计主分析和旧研究结论保留。新包中的合成验证只验证接口与计算，不能填入以上生产结果。个体级既有授权字段继续沿用，无需重复询问；原始EEG、身份映射、逐trial原始记录及私有权重不因本包新增公开授权。


---

## 原文件：docs/05_THREE_ROUND_CLOSURE.md

# 三轮合同与分支结束

## 第一轮 ALN3.6：得到直接回答

完成FAU整组排除的12个唯一source训练、60个目标评估cell，DTU20/FAU pooled20/儿童10个冻结bundle，以及相同五状态、自然query和对应错配控制。主输出为G0、GC、DT及J；不是模型总分表。历史episode零步交互和history描述均值的区间只做CPU收尾，进入补充。

本轮结束要写一页判断：无support的共享证据在哪些预定范围得到支持？个人收益来自哪些允许改变的参数？儿童真实当前EEG是否超出history/twin？明确不确定范围，不依据显著性改下一轮任务。

## 第二轮 ALN3.7：固定复制核心

在看R1结果前就确定：FAU三组、两工具、两内容划分全部用seed3407复制，仍为12次唯一source训练／60个eval cell。即使某组反向或未分辨也要复制。DTU/local/CB与FAU pooled优先使用已有对应3407权重，只重做同一读出；不得只复制表现最好的读出。

儿童 matched AP/APwrong 固定另一个seed3407，使用相同donor exclusion、初始化、曝光流匹配与目标折。若已有兼容来源直接复用；否则最多2个匹配private-target donor训练加2×5=10个目标训练，然后同一冻结科学接口。不得复建所有公共donor和J*/XM/loss矩阵。S只在兼容已有权重时作补充。将确切unique依赖登记，不把一份donor按5fold复制。

所有R1定义包括支持规则、history、时间bank、lambda和统计family保持不变。复制训练seed不增加独立受试者n，也不是独立新队列。若R1出现确定实现错误，版本化修复同一个科学试验，先标清影响范围；不能用“修复”替换不喜欢的科学结果。

## 第三轮 ALN3.8：完成有效性说明和写作

不新增encoder、loss、support预算或时间窗口。完成预定三件事：

1. 合并两seed，先按人平均内容重复和seed，给出每seed以及人级直接配对区间；完成全部固定组和儿童覆盖。
2. 读取既有raw20/时间滤波、设备/phantom、REVE/CS敏感性和私人输入访问勘误，判断哪些结论受它们限制。若缺失关键控制，只做同一固定模型上一次限定重评；不得开展新架构训练。不能将device相关EEG证据自动称纯皮层机制。
3. 冻结图表与主张、整理完整结果和可复现索引，写论文初稿；所有有效正／负／不确定结果保留。实际无证据的机制删掉或限定，不用第四轮寻找替代阳性。

## 结果如何改变主张

| 结果模式 | 允许的结论 |
|---|---|
| G0为正，DT也有可靠增量且真实EEG优于twin | 存在可直接迁移的声音证据；有限个人时间重权进一步增加预测价值 |
| G0为正，DT未分辨 | 支持共享可读性；本时间bank／支持预算未分辨额外个人时间权重价值，不证明个体时间结构相同 |
| G0未分辨，GC/GT有增量 | 源端特征经个人校准／时间重权后可用；不宣称无支持群体读出已迁移 |
| HP改善而GC/DT不明确 | 已见个人支持收益主要体现在给定历史／概率背景的估计；不外推为个人EEG无用 |
| AP−APwrong未分辨 | 正确配对的额外贡献在当前接口未获支持，保留全部既有AP−S/AP−XM及其他预训练有效结果 |
| whole-group迁移不足，但旧mixed-group有效 | 当前整组排除方案尚未支持所检验的迁移；旧mixed-group结果不能补足这项证据，也不能据此把差异归因于是否覆盖目标听觉组；不宣称该目标组没有声音信息或所有方法达到天花板 |

区间包含0不是等效证据；不新造事后等效界。三轮结束允许有不确定性，但要求把到底测试了什么、结论有多强写清。

## 现在停止新增的方向

额外episode压力/步数/FAU推广、C10/H10、更多donor checkpoint、50%people全新selector面板、4×训练预算、全比例×seed auditory-pretraining曲线、更多ensemble、普通FM模型×loss×window扩展均退出新增任务。已有完成结果保留；正在运行的单元在安全边界完成；原有四条有限尾巴使用剩余资源收尾，不因收束重开或增补整格。

本轮只有两个模型类别，因为它们已被充分验证为有效工具；REVE和CS不被宣布失败。以后不因某工具分数较低就加入第三、第四候选来保护主假设。


---

## 原文件：docs/06_REPORTING_AND_RETENTION.md

# 输出、统计与保留

## 主结果表

每人、每content fold、每seed、每合法parent输出H0/E0/HP/EC/ET的同query风险，support预算、query集合哈希、source排除范围、模型/尺度/时间基底哈希。公共同时输出source标准化MSE、r，私有输出NLL bits/trial、AUC、Brier。r/AUC均辅助，不能替代本轮proper-risk主比较。

每个query先对所有状态使用同一索引；人内平均完整content repeats，再按预定seeds平均；最后每个独立人等权。不要把重复seed、内容折、5个人折切片、时间窗、trial数或job数当独立n。FAU使用CI24、HA29、TH14正式目标面板；TH dev不计入目标样本。DTU44；儿童64。错误/缺项透明输出，不能将缺失当0。H0/E0必须在personal fit之前独立保存；个人拟合失败或没有合法support不删除其共享基线。缺少必要成员时family标incomplete、不生成完整family区间；保留全员G0点值和每个缺项原因，不把可完成者冒称全队列。

## 预定统计families

1. `F_FAU_GROUP_SHARED_TIME`：2工具×3目标组×(G0,DT)，12个主对比；每组内人级成对bootstrap，组间独立重抽，所有成员共用相应人索引。输出该family同时95%区间及逐人值。
2. `F_DTU_SHARED_TIME`：2工具×(G0,DT)，4个主对比。
3. `F_PRIVATE_SHARED_TIME`：AP/APwrong×(G0,DT)，以及AP−APwrong的G0/DT直接差，共6个主对比。
4. `F_PRIVATE_CURRENT_CORRESPONDENCE`：AP/APwrong×真实E0对twin E0、真实ET对twin ET，共4个；在每family声明的相同合法twin-query和完整人覆盖上计算。与full natural-query主family分开，不以twin可估计性删主结果。

公共对应性family另固定为`F_FAU_ALIGNMENT`（2工具×3组=6项M0−E0风险差）和`F_DTU_ALIGNMENT`（2项）。它们仅检验固定E0对EEG—声音对应关系的敏感性；query错移不产生新样本，也不代替history主控制。

机制分解另有固定family：`F_FAU_MECHANISM`为2工具×3组×(GC,GT,J,GH)=24项；`F_DTU_MECHANISM`为2工具×4=8项；`F_PRIVATE_MECHANISM`为2 arms×4=8项。它们与上述主family分开给同时区间，不把额外成员偷偷放进或拿出主family，不凭单个漂亮差值升级为主终点。GC不是主family中遗漏的端点。所有组间调节分析使用逐人效应的直接差，不能“一个组显著另一个不显著”代替组差。私人HA/NH与年龄／阶段仅报告预定观察性估计，NH9限制明确，不追加切点。

采用B=4000的按人重抽，主实现沿用经验证的同时区间代码并标明确切统计法。包内`paired_summary.py`提供固定原始SE的max-|z*|参考，非旧bootstrap-t；旧历史结果不重命名统计法。退化方差、不完整人、缺乏可比较twin必须输出非regular状态。不同family之间不声称全局95%覆盖。区间条件于已拟合模型；两seed不是训练随机性的完整分布。

`plans/round1.json`登记范围，`evidence/`登记既有依据，`MANIFEST.json`记录本包字节。真实server额外生成：INTAKE、唯一trainplan、evalplan、binding_receipt、source-exclusion receipt、unit records、per-person contrasts、family summaries、R1_SCIENTIFIC_DECISION.md。关键stdout/失败日志按现有规则保存，不能只留汇总均值。

## 下一次给研究者的报告应先回答

无目标support时有没有可迁移的当前声音证据？整体概率/历史校准后，时间重权还增加多少？儿童当前EEG对应性是否存在？这些结果使哪条具体假设变强、变弱或仍未确定？之后才列完成度和耗时。不能再用大段调度流水账替代科学判断。

## 存储清理的范围

此前提及A3d约233GiB、A3c43.1GiB、A3b13.8GiB、ALN2 D_FM32.1GiB，合计约322GiB。容量名称不是可删除性的证据；真实候选列表未随GitHub发布。本包不执行或授权一条未核对的整目录`rm -rf`。

优先保护：local/CB直接父权重、genericCB初始权重、matched AP/APwrong donor与target权重、现有content/private缓存、sound/history目标和physical split绑定、所有unit记录/逐人预测摘要/统计/代码hash。新实验只保存best/source必要checkpoint和轻量逐人读出结果，避免无目的保留每步快照。

旧A3c attention已完成读出若预测cache足够，相关无后续消费的权重可以列为精确删除候选；D_COVERAGE分开核对。ALN2 D_FM旧teacher/校准/蒸馏相关权重在实际依赖都结束后可列候选；public donor目录不是同一批。A3b/A3d需要现场路径分类，不能按旧容量整体判废。已有episode3407完成会解除它特定旧依赖，不代表所有其他消费结束。

删除前只做一次基于本轮真实依赖的文件清单，保留派生结果、来源hash与重建方式；清理不再新增一个科研实验分支。此处未远程删除任何文件。


---

## 原文件：src/aln36_readout/README.md

# ALN3.6 CPU readout reference

This is a small, runnable NumPy/SciPy reference for H0/E0/HP/EC/ET. It is **not** an assertion that the server's EEG extraction, source-group exclusion, matched AP/APwrong lineage, or trial bindings have already been integrated. The server adapter must implement and verify those bindings before passing arrays here. No encoder, CUDA, Slurm, data loading, or filesystem write is performed by this module.

Public continuous outcomes use `family="gaussian"`, five source-window scores, and MSE. Private binary outcomes use `family="bernoulli"`, three source-window logits, and log loss in bits/trial. All score and history scaling, the history offset, `a0`, temporal basis, and ridge strengths are fixed using the permitted source population only. See `docs/03_READOUT_CONTRACT.md` for the scientific and data contract.

```python
from aln36_readout import build_time_basis, fit_nested_readout, evaluate_readout

# source arrays are provided by the server adapter, never by an outer target.
basis = build_time_basis(
    a0=a0, source_scores=source_scorebank,
    source_history_design=source_history_design,
)
fit = fit_nested_readout(
    family="bernoulli",
    support_offset=support_offset, support_history=support_history_design,
    support_scores=support_scorebank, support_y=support_y,
    a0=a0, time_basis=basis,
    ridge_history=source_fixed_ridge_history,
    ridge_scale=source_fixed_ridge_scale,
    ridge_time=source_fixed_ridge_time,
)
result = evaluate_readout(
    fit=fit, query_offset=query_offset, query_history=query_history_design,
    query_scores=query_scorebank, query_y=query_y,
)
```

`fit_nested_readout` has no query argument. Query labels appear only in the non-fitting evaluator. This interface separation cannot itself certify that an adapter supplied legal support or excluded the correct source groups.

The temporal transform stores and actually applies the source nuisance projection
and residual whitening: `Z = (scores @ B - [1, history, scores @ a0] @ C) / scale`.
Supply the same history columns when building and applying this transform; it is
never refitted on target support or query. Coefficient orthogonality alone is not
used as a substitute for conditional time features.

Run the seven synthetic checks from the server-package root:

```bash
python -B -m unittest discover -s tests -p test_nested_readout.py -v
```

Required dependencies: Python 3.10+, NumPy, SciPy. The tests use the standard-library `unittest`; pytest is not required. Synthetic checks establish the reference's algebra and optimization behavior, not the validity or scientific result of any EEG experiment.


---

## 原文件：SOURCE_INDEX.md

# 证据与接入源码索引

所有链接固定到 `3da8cf5758214c0cf87a1f1c8d67fb84b574000e`。SHA256针对`git show`文件内容，不代表server现场状态已经核验。

| 文件 | SHA256 |
|---|---|
| [AGENTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/AGENTS.md) | `de0d365c56d9ac29a4e596c9ee3adb9a494667296105a13188feea033d0066ef` |
| [docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/TRUE_FULL_PAIRED_EVIDENCE.md) | `3d740f45bb3abfe48c614f2d0b5a492377be5eae6b2443a4f91f282f7fd38995` |
| [docs/auditory_alignment_v3/RELEASE_034.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/RELEASE_034.md) | `b3c644781b05a1da2a05bd865873fd2acac4a95ef4ac7909673e9f5a4826cab0` |
| [docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/NEW_LANES_EFFICACY.md) | `97e3a4a37bd7664b13ba37e036ea237461697dac57f507d159a3cacf029d50bc` |
| [docs/auditory_alignment_v3/aln35/SCIENCE_PRIVATE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/SCIENCE_PRIVATE_RESULTS.md) | `eb493fe7ba63f4171d0c25446f01d8c5c39011fa9b2fd64e9a04597b83a4ff66` |
| [docs/auditory_alignment_v3/aln35/SCIENCE_V2_READOUT.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/SCIENCE_V2_READOUT.md) | `27889858ad1b2dd31baa7b8ea1ae49cfa7f05d6a13154c90195f8fff4aec4e2d` |
| [docs/auditory_alignment_v3/aln35/HISTORY_INTERFACE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/HISTORY_INTERFACE_RESULTS.md) | `bccfca24e122b4bc3df4d38448659010a8dfba46a122679e9574726a8eec294d` |
| [docs/auditory_alignment_v3/aln35/SUPPORT_EPISODE_SELECTION_INTERPRETATION.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/SUPPORT_EPISODE_SELECTION_INTERPRETATION.md) | `20c207233744b7f0686536e2d3f29798e073f6014c134f4486701e4927e62b8e` |
| [docs/auditory_alignment_v3/aln35/EPISODE_REPLICATION_S3407_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/EPISODE_REPLICATION_S3407_RESULTS.md) | `8b14f3cd09d0afd93bda97e723fe36eb100b04694924d1fb8b0ef28b993ec08b` |
| [docs/auditory_alignment_v3/aln35/AP_WRONG_RESULTS_V2.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/AP_WRONG_RESULTS_V2.md) | `50bb0415d0e8809125a2ebddbad97f2f2a39b4c219d37ecf53039ff150156a40` |
| [docs/auditory_alignment_v3/aln35/CBAUD_PEOPLE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/CBAUD_PEOPLE_RESULTS.md) | `65536bc418276a356d54f076faef5f2240ae2459a45a66e71a5e4245879b33fe` |
| [docs/auditory_alignment_v3/aln35/FUSION_ATTRIBUTION_RESULTS_1047619.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/FUSION_ATTRIBUTION_RESULTS_1047619.md) | `24efb886ce5be544e2e2ee43a3efa201fc752843526ce3da6484dc63e9ec0d7b` |
| [docs/auditory_alignment_v3/aln35/CORRECTION_PRIVATE_PRE_ACCESS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/CORRECTION_PRIVATE_PRE_ACCESS.md) | `a43739439edbd296e0ad0c8db20512beb28db9542f602e60ea18e5afb9584dbc` |
| [docs/auditory_alignment_v3/aln35/CB_AUDIO_STATE_RESULTS.md](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/docs/auditory_alignment_v3/aln35/CB_AUDIO_STATE_RESULTS.md) | `3e46e14e29493c1deb54895de1c3707e0a03c2a380c59a7e6a51b738fce13571` |
| [auditory_alignment/data.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment/data.py) | `abeb9d368116e4b1b6becace401299660248e48356fa12f72084950282ebb6b5` |
| [auditory_alignment_v2/train.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v2/train.py) | `1a00101c1514c1cb790c8927c778e3fd80d3b0505685e71ec058bb7720b6f9a4` |
| [auditory_alignment_v3/core.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/core.py) | `a3851b4a601a1bd7a6365514d408703bb8c4ecb0b615751107f56b7fc3987262` |
| [auditory_alignment_v3/local_support.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/local_support.py) | `a4af781077e1c2e2bfde35f4460bd89f977ba72e1da2d582147bf5ca62c0a5c3` |
| [auditory_alignment_v3/local_train.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/local_train.py) | `dee8d0cd58297e038b7a6e82c58a897aeb22dcc4109f1683396bce883a174c83` |
| [auditory_alignment_v3/fm_dense.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/fm_dense.py) | `d3aecdba47e8d31bd2ff3ef31fdc22f1f6390ce7ad5e7f918e71911d78f2385c` |
| [auditory_alignment_v3/fm_aligned32.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/fm_aligned32.py) | `7579f2a16368d3aeb16a2ffcc2ed4f74b6dd64c0b55be5d29cf6976df454d531` |
| [auditory_alignment_v3/run_aligned32.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/run_aligned32.py) | `e1be6d205789098bb066d40bbb71c047d476ed4a5bc4dcc6e530036a69d95a22` |
| [auditory_alignment_v3/aln34/content_time.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln34/content_time.py) | `c601c89a3198a4f196847344ff02238eecddf6aa90b8606b09833ddc918ddc42` |
| [auditory_alignment_v3/aln34/prior_science.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln34/prior_science.py) | `13dba78ae90f231aa9ca00c12c5acb44b176aff3a8e1dc6a55afe883ec8a226a` |
| [auditory_alignment_v3/aln34/private_current_time.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln34/private_current_time.py) | `85719e9ac455a9cd7bd5e86ee8a66a6fcbb04a0f88b88d5fdc1a988bef845dc3` |
| [auditory_alignment_v3/aln34/data_inner.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln34/data_inner.py) | `7146dfba65865b4227407dbfcf0f5b793d525e0ffab5efc33d1992c59053b812` |
| [auditory_alignment_v3/aln34/breadth_inner.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln34/breadth_inner.py) | `d27932b12a531f13a7758056f1c9b65701fad17934595724bd404ef758f5061c` |
| [auditory_alignment_v3/aln35/history_interface.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/history_interface.py) | `b02a0e1e73c544d0b798fb13c007f1638cb60e1d64477c1360c30fae26d2cd19` |
| [auditory_alignment_v3/aln35/support_contract.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/support_contract.py) | `c4abbda40e605718883b87d0dd4a6933a8b1065e49dbd11bf2f66f32e7a95f7c` |
| [auditory_alignment_v3/aln35/support_coverage.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/support_coverage.py) | `c003c41e080c81f13c8e89a1651971bdfb7656d6f758fade28e8bc86ea585be5` |
| [auditory_alignment_v3/aln35/ap_wrong.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/ap_wrong.py) | `b514741ee7c18135264664784a09dc0046d29d4a9c80b839a9f58d85582522e7` |
| [auditory_alignment_v3/aln35/ap_wrong_sampler.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/ap_wrong_sampler.py) | `2a7b109dc9aedf80055470aa6f47a7788e9ec69ebb14a78711cc7b5c1140743e` |
| [auditory_alignment_v3/aln35/ap_wrong_analysis_v2.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/ap_wrong_analysis_v2.py) | `529f5e7487632a5a8c82052fc9db11a70119e406197cae682f4dd7f7040299a0` |
| [auditory_alignment_v3/aln35/science_binding.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/aln35/science_binding.py) | `d5c596d2e5ab7dbfbae5ec1ba9585a2ed6cf395a857a88f8d726c1249d927e48` |
| [auditory_alignment_v3/sci_r1/private_task.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/auditory_alignment_v3/sci_r1/private_task.py) | `57d1b002a324a63e280c6fa34c12bf89c29d840f3f45122a3bf435786d68a6b7` |
| [scripts/auditory_alignment_v3/aln35/cbaud_people_analysis_v1.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/scripts/auditory_alignment_v3/aln35/cbaud_people_analysis_v1.py) | `939a14278ecc1f8f22b611dddb1535149227cd9ba242a478a66ed7ea111a4f4a` |
| [scripts/auditory_alignment_v3/aln35/episode_rep_s3407_analysis_v1.py](https://github.com/W-Yinghao/auditory/blob/3da8cf5758214c0cf87a1f1c8d67fb84b574000e/scripts/auditory_alignment_v3/aln35/episode_rep_s3407_analysis_v1.py) | `533f8ef650211bfadee08e3ac27560f9dde9df8072535079ee30b66e3782f4c4` |


---

## 附录：plans/round1.json

```json
{
  "version": "ALN3.6_R1_20261020",
  "research_question": "Transferable auditory evidence and listener-specific temporal readout",
  "baseline_commit": "3da8cf5758214c0cf87a1f1c8d67fb84b574000e",
  "design_status": "prospective_protocol_after_2026_10_20_result_informed_design",
  "production_binding_required": true,
  "current_round": 1,
  "maximum_rounds": 3,
  "seed": 3401,
  "replication_seed_round2": 3407,
  "gpu_cap_running_plus_pending": 10,
  "public_tools": [
    "local_L1",
    "CBpre_true_full"
  ],
  "public_objective": "InfoNCE",
  "heldout_groups": [
    "ci",
    "ha",
    "th"
  ],
  "person_folds": [
    0,
    1,
    2,
    3,
    4
  ],
  "content_folds": [
    0,
    1
  ],
  "public_time_centers_ms": [
    -200,
    0,
    200,
    400,
    600
  ],
  "public_window_relative_to_center_ms": [
    -400,
    600
  ],
  "public_joint_access_ms": [
    -600,
    1200
  ],
  "public_target": "source_audio_fit_standardized_current_envelope",
  "public_history_lags_ms": [
    20,
    100,
    200,
    500
  ],
  "public_primary_risk": "MSE",
  "public_support": "first_ceil_30pct_legal_5s_segments_from_target_person_source_fit_content_only",
  "public_query": "all_legal_target_person_source_test_content",
  "private_arms": [
    "matched_AP_v2",
    "matched_APwrong_v2"
  ],
  "private_optional_reference": "compatible_existing_S_only",
  "private_time_windows_ms": [
    [
      0,
      200
    ],
    [
      200,
      400
    ],
    [
      400,
      600
    ]
  ],
  "private_primary_risk": "NLL_bits_per_trial",
  "private_support": "existing_natural_U30_physical_block_rule_with_boundary_guards",
  "private_query": "independent_later_blocks_natural_class_proportions",
  "readout_states": [
    "H0",
    "E0",
    "HP",
    "EC",
    "ET"
  ],
  "default_personal_ridge": {
    "history": 1.0,
    "scale": 1.0,
    "time": 1.0
  },
  "main_estimands": {
    "G0": "R(H0)-R(E0)",
    "DT": "R(EC)-R(ET)"
  },
  "secondary_estimands": {
    "GC": "R(HP)-R(EC)",
    "GT": "R(HP)-R(ET)",
    "J": "GT-G0",
    "GH": "R(H0)-R(HP)"
  },
  "expected_counts": {
    "unique_fau_source_training": 12,
    "fau_group_evaluation_cells": 60,
    "fau_pooled_frozen_bundles": 20,
    "dtu_frozen_bundles": 20,
    "private_frozen_bundles": 10,
    "core_evaluation_bundles": 110,
    "optional_S_bundles": 5
  },
  "expected_people": {
    "fau": {
      "ci": 24,
      "ha": 29,
      "th": 14
    },
    "dtu_total": 44,
    "private": {
      "HA": 55,
      "NH": 9
    }
  },
  "checkpoint_selection": "source_only_fixed_ES_candidate_pool_actual_native_query_NLL",
  "parent_recipes": {
    "local_L1": {
      "epochs": 200,
      "lr": 0.001,
      "weight_decay": 0.0001
    },
    "CBpre_true_full": {
      "epochs": 100,
      "lr_backbone": 0.0003,
      "lr_head": 0.001,
      "recipe": "full_onestep_v1"
    }
  },
  "new_source_forbidden_inputs": [
    "heldout_group_EEG",
    "heldout_group_TH_dev",
    "source_test_content_for_fit_or_selection",
    "target_query_labels",
    "FAU_pooled_finetuned_initialization",
    "project_auditory_donor_seen_FAU_target_group"
  ],
  "bootstrap": {
    "B": 4000,
    "unit": "person",
    "seed": 361020,
    "reference_method": "fixed_original_SE_max_abs_centered_bootstrap_z",
    "group_resampling": "independent_within_groups_paired_across_contrasts"
  },
  "new_training_round3": false,
  "closed_new_searches": [
    "episode_pressure_or_steps",
    "C10_H10",
    "donor_checkpoint_grid",
    "50pct_selector_panel",
    "4x_or_8x_budget",
    "expanded_people_fraction_grid",
    "ensemble_grid",
    "architecture_loss_window_cartesian_grid"
  ],
  "public_anchor_seconds": [
    0.8,
    1.2,
    1.6,
    2.0,
    2.4,
    2.8,
    3.2,
    3.6
  ],
  "public_fit_loss_mass": "one_equal_weight_per_fixed_anchor; exactly_8_unique_anchors_per_legal_5s_segment",
  "private_fit_loss_mass": "one_equal_weight_per_natural_trial",
  "statistical_families": [
    {
      "id": "F_FAU_GROUP_SHARED_TIME",
      "members": 12,
      "definition": "2 tools x 3 target groups x [G0,DT]"
    },
    {
      "id": "F_FAU_MECHANISM",
      "members": 24,
      "definition": "2 tools x 3 target groups x [GC,GT,J,GH]"
    },
    {
      "id": "F_DTU_SHARED_TIME",
      "members": 4,
      "definition": "2 tools x [G0,DT]"
    },
    {
      "id": "F_DTU_MECHANISM",
      "members": 8,
      "definition": "2 tools x [GC,GT,J,GH]"
    },
    {
      "id": "F_PRIVATE_SHARED_TIME",
      "members": 6,
      "definition": "2 arms x [G0,DT] plus matched AP-minus-APwrong for G0 and DT"
    },
    {
      "id": "F_PRIVATE_MECHANISM",
      "members": 8,
      "definition": "2 arms x [GC,GT,J,GH]"
    },
    {
      "id": "F_PRIVATE_CURRENT_CORRESPONDENCE",
      "members": 4,
      "definition": "2 arms x [R(twin_E0)-R(real_E0),R(twin_ET)-R(real_ET)]"
    },
    {
      "id": "F_FAU_ALIGNMENT",
      "members": 6,
      "definition": "2 tools x 3 target groups x [R(M0)-R(E0)]"
    },
    {
      "id": "F_DTU_ALIGNMENT",
      "members": 2,
      "definition": "2 tools x [R(M0)-R(E0)]"
    }
  ],
  "public_alignment_control": {
    "name": "M0",
    "mapping": "within_target_person_Q_rotate_whole_ordered_5s_segments_by_one; keep_8_anchor_positions_and_all_5_window_scores_together",
    "fit": "none; fixed_E0_readout",
    "history_and_targets": "retain_original_rows",
    "estimand": "R(M0)-R(E0)",
    "interpretation": "alignment_sensitivity_not_conditional_randomization",
    "minimum_query_segments": 2
  },
  "source_head_crossfit": {
    "folds": 3,
    "unit": "source_person",
    "coordinates": "shared_audio_target_units_then_fixed_OOF_score_scaler",
    "combiner_fit": "corresponding_OOF_history_offset_and_OOF_scorebank",
    "final_predictor": "full_legal_source_refit_with_frozen_OOF_score_scaler_and_a0",
    "public_history_personal_columns": [
      "constant",
      "source_scaled_env_lag20",
      "source_scaled_env_lag100",
      "source_scaled_env_lag200",
      "source_scaled_env_lag500"
    ]
  },
  "private_strict_twin_control": {
    "source": "shared_frozen_real_source_H0_probes_scaler_a0_time_basis; no_twin_source_refit",
    "partners": "same_child_same_history_other_block_nonself; support_within_support_and_query_within_query; no_current_y_selection",
    "scores": "all_K3_windows_from_one_partner; project_swapped_scores_with_current_history",
    "E0": "fixed_parameters_same_eligible_query_intersection",
    "personal": "real_control_and_twin_control_each_fit_HP_EC_ET_on_identical_twin_eligible_support_rows_then_same_query_intersection",
    "natural_primary": "full_natural_real_support_and_query_reported_separately",
    "interpretation": "correspondence_sensitivity_in_both_support_and_query_not_pure_timing_or_query_only_effect",
    "missing": "explicit_not_estimable_no_support_partner_or_no_query_partner; no_fallback_or_zero_imputation"
  }
}
```


---

## 附录：PACKAGE_METADATA.json

```json
{
  "package": "AUDITORY_ALN3_SERVER_PACKAGE_v3_6_20261020",
  "version": "3.6",
  "created_utc_date": "2026-10-20",
  "baseline_commit": "3da8cf5758214c0cf87a1f1c8d67fb84b574000e",
  "remote_verified_utc": "2026-10-20T18:56:49Z",
  "task": "three-round scientific closure, round 1 server handoff",
  "prior_package": "ALN3.5",
  "status": "prepared_reference_and_execution_contract_not_server_executed",
  "new_server_code_integration_required": true,
  "unique_fau_training_round1": 12,
  "core_evaluation_bundles": 110,
  "rounds_remaining_including_this": 3,
  "source_index_entries": 37,
  "individual_derived_publication": "previous_user_authorization_preserved",
  "raw_private_data_included": false,
  "remote_training_launched": false,
  "remote_deletion_performed": false
}
```


---

## 附录：evidence/REVIEW_SNAPSHOT.json

```json
{
  "repository_commit": "3da8cf5758214c0cf87a1f1c8d67fb84b574000e",
  "remote_verified_utc": "2026-10-20T18:56:49Z",
  "release": "publish_034",
  "release_snapshot_local_time": "2026-10-20 19:55 CEST",
  "completed_at_publication": {
    "CBAUD_PEOPLE": 20,
    "episode_rep_s3407": 10
  },
  "remaining_at_publication_not_live_queue": {
    "DTU_budget": 39,
    "DTU_curve": 10,
    "breadth_budget": 9,
    "breadth_curve": 74
  },
  "new_ALN36_results": "not_run",
  "full_history_caveat": "Package decisions derive from recovered ALN3.4/3.5 artifacts and current repository; no claim of a complete verbatim old-chat archive."
}
```


---

## 附录：evidence/VALIDATION.json

```json
{
  "performed_utc": "2026-10-20T19:05:20.839489+00:00",
  "status": "pass_for_local_reference_and_specification",
  "unit_tests": {
    "count": 9,
    "command": "PYTHONPATH=src python -B -m unittest discover -s tests -v",
    "exit_code": 0,
    "transcript": "test_fit_has_no_query_label_api_and_contrasts_use_direct_paired_algebra (test_nested_readout.NestedReadoutTests.test_fit_has_no_query_label_api_and_contrasts_use_direct_paired_algebra) ... ok\ntest_near_collinear_time_score_cannot_cheaply_replace_global_gain (test_nested_readout.NestedReadoutTests.test_near_collinear_time_score_cannot_cheaply_replace_global_gain) ... ok\ntest_nested_models_positive_scale_bound_and_identity_initialization (test_nested_readout.NestedReadoutTests.test_nested_models_positive_scale_bound_and_identity_initialization) ... ok\ntest_one_class_support_is_finite_and_query_evaluation_does_not_refit (test_nested_readout.NestedReadoutTests.test_one_class_support_is_finite_and_query_evaluation_does_not_refit) ... ok\ntest_pure_base_rate_shift_is_not_a_temporal_rotation (test_nested_readout.NestedReadoutTests.test_pure_base_rate_shift_is_not_a_temporal_rotation) ... ok\ntest_true_temporal_rotation_recovers_on_independent_queries_in_both_families (test_nested_readout.NestedReadoutTests.test_true_temporal_rotation_recovers_on_independent_queries_in_both_families) ... ok\ntest_zero_shared_signal_and_source_rank_degeneracy_are_explicit (test_nested_readout.NestedReadoutTests.test_zero_shared_signal_and_source_rank_degeneracy_are_explicit) ... ok\ntest_person_slices_reuse_group_training (test_plan_and_summary.PlanAndSummary.test_person_slices_reuse_group_training) ... ok\ntest_repeats_do_not_inflate_n_and_missing_not_zero (test_plan_and_summary.PlanAndSummary.test_repeats_do_not_inflate_n_and_missing_not_zero) ... ok\n\n----------------------------------------------------------------------\nRan 9 tests in 0.085s\n\nOK\n"
  },
  "plan": {
    "unique_fau_source_fits": 12,
    "core_evaluation_bundles": 110,
    "with_optional_compatible_existing_S": 115,
    "production_binding_required": true
  },
  "review_repository": {
    "head": "3da8cf5758214c0cf87a1f1c8d67fb84b574000e",
    "clean": true,
    "source_files_rehashed": 37
  },
  "independent_review_fixes": [
    "Temporal contrast is actually source-nuisance-residualized and whitened in both fit and predict.",
    "The 60-evaluation-cell count does not authorize 60 encoder fits.",
    "Whole-group versus old pooled differences do not identify a group-coverage causal effect.",
    "Private twin controls share frozen real source parameters and identical eligible support/query rows."
  ],
  "not_performed": [
    "server adapter integration",
    "real EEG forward pass",
    "new encoder training",
    "Slurm job submission",
    "remote file deletion",
    "scientific confirmation of new hypotheses"
  ]
}
```
