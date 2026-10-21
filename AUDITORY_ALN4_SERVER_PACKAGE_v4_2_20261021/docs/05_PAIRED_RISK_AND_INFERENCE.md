# 05 — 个人净改善与配对推断合同

## 1. 分析问题与地位

本工具解决一个具体误读：`GC = R(HP) − R(EC)` 为正，并不表示个人校准后的 EC 优于未经个人拟合的 E0。HP 可能已经偏离较好的 H0。需要在同一人的同一查询集上，直接比较 E0、EC、ET。

`tools/paired_risk_summary.py` 是独立 CPU reference helper；不提取 EEG、不拟合模型、不提交作业、不联网、不清理文件、不修改仓库，也不替代服务器 production 推断入口。它依赖 Python 3.10+ 与 NumPy 1.22+。

**这两个 NET 对比是在观察 R1 之后确定的诊断问题。** 它们在本包中固定用于后续 R2 与固定双 seed 面板，标签为 `post_R1_diagnostic_net_contrasts`；不能改写为观察 R1 前预注册的 confirmatory 终点。实际冻结时间与 source 绑定由运行收据记录，程序不能替代时间戳证明。原 R1/R2 families、原估计和原区间完整保留；新增 NET family 另列，不把更好看的新区间用于替换原区间。

## 2. 估计量：只用直接风险相减

所有量均以“风险减少为正”。每个风险是一个目标人、一个固定 tool、一个 seed 在同一物理查询集上的均风险。

| 名称 | 直接式 | 可检验的等式 |
|---|---|---|
| G0 | H0 − E0 | 固定 source EEG 相对 source history 的增量 |
| GH | H0 − HP | 个人 history 更新增量 |
| GC | HP − EC | 相对个人 history 基线的整体 EEG 尺度增量 |
| DT | EC − ET | 相对 EC 的额外时间读出增量 |
| NET_C | E0 − EC | GH + GC − G0 |
| NET_T | E0 − ET | GH + GC + DT − G0 |

表中 H0 等均指 `R(H0)` 等。代码的 NET 估计使用直接式；输出逐人代数重构误差，便于发现汇总口径问题。**不推定、重命名或计算 J。** 不从独立区间相减构造配对区间。

例如 H0=1.00、E0=0.80、HP=1.30、EC=1.20，GC=+0.10，但 NET_C=−0.40：尺度项收回部分损失，个人模型仍逊于原固定读出。这个反例包含在可运行检查中。

## 3. 输入 CSV 与共同 Q

必须字段：

```text
cohort,person_id,tool,seed,unit,risk_H0,risk_E0,risk_HP,risk_EC,risk_ET
```

`cohort` 应分到本次预定的独立分析组，例如 `FAU_HA`、`FAU_CI`、`FAU_TH`、`DTU`、`PRIVATE`。不能先把 FAU 的三个组混合为一个 cohort 再解释组差。`unit` 必须明确，例如 `mse` 或 `bits_per_trial`；一个 cohort 内所有人、tool、seed 必须一致。不同 cohort 始终分别汇总，即使 unit 名称相同也不合并。源端目标标准化、NLL 的 bits/nats 转换必须由 adapter 正确完成并保留其 receipt，本工具不猜单位、不转换。

共同 Q 可用两种明确方式声明：

1. **优先提供五个字段** `risk_H0_query_fingerprint`、`risk_E0_query_fingerprint`、`risk_HP_query_fingerprint`、`risk_EC_query_fingerprint`、`risk_ET_query_fingerprint`。每行五者必须相等；若同时给 `query_fingerprint`，它也必须相等。
2. 只给一个 `query_fingerprint` 时，执行者必须加 `--shared-query-declaration`，明确确认 adapter 已把五个风险绑定在相同 Q 上。输出会保留这个较弱的 `adapter_declared_shared_Q` 状态，不冒称工具检查过底层 trial。

所有 fingerprint 都必须是 SHA-256 的 64 位十六进制摘要。同一 cohort、同一人的全部 tools 与 seeds 也必须一致。这是本轮冻结 Q 的严格合同，不允许静默使用每个工具或 seed 各自剩余的 query 子集。摘要的 canonical payload 应包含排序后的物理 query ID、目标定义、风险权重及目标值的摘要；需要保存构造规则和相应 manifest。相等 hash 只能验证声明一致，不能证明 adapter 实际用了这些行。

若目前只能取得各模型在不同 Q 上的 aggregate 风险，**不能直接送入工具，也不能伪造相同 fingerprint**。由 adapter 从现有逐 query 输出在预定共同交集上重算风险并报告覆盖；不能仅靠人级均值恢复共同 Q。此工具不会进行这种交集筛选。

每个 `(cohort, person_id, tool, seed)` 必须唯一。每个 cohort 的所有人必须拥有全部已声明 tools 和 `--expected-seeds` 中的每一个 seed。缺一项、重复、额外 seed、空 seed、NaN/Inf、负风险都会失败；即使负数仅为 `−1e−16` 也不静默截断。上游若需处理数值误差，应记录原因并重新导出。原始 MSE/NLL 非负不意味着净改善也非负。

默认可发现观测面板中的缺项，不能发现整个人或整个 tool 完全未进入 CSV。正式运行应同时提供 `--expected-panel expected_panel.json`，格式为：

```json
{
  "SYNTHETIC_ONLY": {
    "person_ids": ["synthetic_1", "synthetic_2", "synthetic_3"],
    "tools": ["local", "cbpre"],
    "unit": "mse"
  }
}
```

该示例不是任何真实队列名册。实际文件由本轮冻结 source/target roster 导出；所有 cohort、人、tools、单位必须精确匹配，不做缺失后 complete-case 筛选。没有这个文件时，输出 `expected_panel_status=not_supplied`，不能宣称覆盖了完整队列。

若源数据尚有内容 fold 或 support draw，adapter 须先按原合同在每人、每 tool、每 seed 内聚合，保留逐 fold/draw 溯源与公共 Q manifest。不能把 fold、draw 或 seed 伪装成新的人；也不能把跨 seed 均值复制回两个 seed 行。工具能检查输入面板，但无法仅凭最终均值证明这些上游操作。

## 4. 人级均值、独立 NET family 与参考区间

每人首先等权平均固定 seed 列表的五个风险，随后直接计算各效应；这与先算逐 seed 效应再等权平均代数等价。人群均值再按人等权。`seed=3401/3407` 不使 n 翻倍，训练 seed 不是 bootstrap 的独立样本。

每个 cohort 创建一个独立 NET family，成员固定为该 cohort 的全部 tools × `[NET_C, NET_T]`。G0/GH/GC/DT 只输出逐人及描述均值，不在这里补做原终点的新显著性检验。不增加 cross-tool 或 cross-cohort contrast。各 cohort 的区间只控制各自这个 family 的名义同时覆盖，不宣称所有 cohort 的联合覆盖。

**参考方法为 fixed-original-SE max-|z*| 人级 bootstrap，不是 production bootstrap-t 的复制。** 对 family 的整个人效应向量进行有放回重采样，保留同人的 tools 与 NET 对比配对；默认 B=4000。在原始 n 人上计算每个效应的 `SE_j=sd(d_ij)/sqrt(n)`。对每次重采样取：

\[
M_b=\max_j\left|\frac{\bar d^*_{bj}-\bar d_j}{SE_j}\right|,
\quad c=Q_{0.95}^{\mathrm{higher}}(M_b),
\quad CI_j=\bar d_j\pm cSE_j.
\]

分母始终是原始人样本的 SE，**不是每次重采样的 SE**；没有复制原算法的 studentized bootstrap-t。区间只是在给定已拟合模型、固定 seed 列表、当前人群抽样假设下的参考近似，不包含重新训练模型的不确定性，也不修复高影响个体、错误事件定义或模型构造问题。它不是用来把 child60 导致的不稳定原区间“修成显著”的替代主分析。原 production 区间与状态必须并列保留；若需要一比一复现原算法，另按其实际源码实现并验证，本工具不作此声称。

退化处理固定如下：

- n<3：输出人级数据、均值与明确状态，family 区间全部为 `null`。
- 任一 family 成员原始 SE=0：不删除该成员、不把点估计伪装为确定区间；整个 family 区间为 `null`，列出退化成员。
- 重采样中 SE=0：计数并完整保留这些 draw。因为本参考方法不以重采样 SE 作分母，它们没有除零；不能用这一规则模拟 bootstrap-t 后再丢弃 bad draws。
- 非有限统计量或区间：失败，不产生 NaN/Infinity JSON；若临界值退化为0，输出不可估计状态与 `null` 区间。
- 不使用自动剔人、winsorization、改终点、换分母或只报告显著 tool。

child60 的事件/标签/history 原始记录审计与本统计 helper 是两项不同任务。若确认上游错误，按依赖修复并保留版本；若记录属实，保留该儿童。不能从一个异常均值判断其应被删除，也不能把 R2 seed 复制当作数据定义审计。

## 5. 运行、输出与检查

优先五个逐风险 fingerprint 字段：

```bash
python -B tools/paired_risk_summary.py --input normalized_person_risks.csv --expected-seeds 3401 3407 --expected-panel expected_panel.json --output paired_net_diagnostic_s3401_s3407.json
```

只有共享 fingerprint 时，命令加 `--shared-query-declaration`。R1 单 seed 描述可以用 `--expected-seeds 3401`，保留独立输出名称；不能把单 seed 输出伪装成双 seed 完成结果。可通过 `--family-id` 设置明确的版本标签，family 成员仍固定为全部 tools 的两个 NET 对比；bootstrap 参数及随机种子均写入 JSON。

输出拒绝覆盖已有文件；输出目录须已存在。无效输入退出码2，不写结果。有效但区间退化时仍写结构化报告，退出码0，必须读取 `net_family.status`，不能仅看进程成功。

主要字段：

- `analysis_scope`：观察 R1 后诊断、reference-only、条件化对象及原 families 保留声明。
- `input`：CSV SHA-256、共同 Q 声明模式、预期名册验证状态、观测面板与忽略的额外 metadata 列。
- `cohorts[].per_person`：人级 seed 均值、六个效应、每个 seed 原值与 query fingerprint。
- `descriptive_by_tool`：五状态风险与六效应人均值。
- `net_family`：明确 family 成员、n、参考方法、原始 SE、名义同时95%区间、零重采样 SE 计数、实际保留的 bootstrap 次数、退化状态。

执行有意义的合成检查：

```bash
python -B tools/check_paired_risk_summary.py
```

检查 GC 正而 NET 负的反例；固定 seed 平均不导致伪重复；同 Q 绑定；不完整/重复面板与名册缺失；负值/非有限值/混单位拒绝；单摘要必须显式声明；零原始 SE 不伪造区间、零重采样 SE 不丢 draw；CLI 不覆盖已有输出。所有记录均为合成 fixture，不是研究观测。
