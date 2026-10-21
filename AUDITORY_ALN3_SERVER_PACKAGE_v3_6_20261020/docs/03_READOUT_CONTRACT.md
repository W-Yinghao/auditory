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
