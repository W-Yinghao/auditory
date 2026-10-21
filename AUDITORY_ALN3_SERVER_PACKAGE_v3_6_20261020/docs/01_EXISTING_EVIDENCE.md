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
