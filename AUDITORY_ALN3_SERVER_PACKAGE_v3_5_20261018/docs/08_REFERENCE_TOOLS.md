# 08 — 配对对比、物理覆盖与支持量参考工具

## 定位与边界

本目录提供 ALN3.5 的**可运行参考实现**，用于检查本轮新探索性小 family 的统计定义和输入完整性。它不是实际 EEG pipeline，不发现服务器数据，不训练模型，不拟合选择器，不提交或取消作业，不调用 Git，也不删除文件。输入均只读；结果默认写到 stdout，指定 `--output` 时只创建不存在的新文件。

这些工具不改写 ALN3.4 及更早注册分析的 bootstrap-t 输出，不回算出一个更有利的旧结论。真实分析必须先由 server 端依据完整 unit records／per-participant 数据及注册预期名册，导出可追溯的规范行；本包的合成数据不能作为任何 EEG 发现的证据。

运行要求：Python 3.10 或以上，仅标准库，无需安装依赖。以下命令从本包根目录执行，所有输入路径由调用者指定；没有预设服务器根目录。

```bash
python -B -m unittest discover -s tests -v
python -B scripts/paired_contrasts.py --help
```

## 1. 一行代表什么

`schemas/normalized_rows.schema.json` 描述 JSONL 单行格式。`examples/synthetic_rows.jsonl` 含 128 个纯合成行：8 个唯一人、2 个 seeds、2 个内容评估 cell、2 个 arms、2 个时间窗口。它不含真实参与者。

| 字段 | 约定 |
|---|---|
| `dataset`, `identity` | 数据集与稳定的人 ID；不是窗口或 seed 的伪参与者 ID。 |
| `group` | 输入中的人群标签；同一个人的标签不能随 arm、fold 或 seed 改变。 |
| `stratum` | 可选预先定义的重采样层。使用 `stratified` 时，每个选中的行必须显式提供。 |
| `fold` | 同一个人实际重复的内容／session 评估 cell。**不是要求每个人都经历全部 outer subject folds。** |
| `seed` | 该行所属的单个实际 seed，非负整数。 |
| `arm`, `window` | 精确的条件和窗口名称。条件身份应含足以区分生产配置的信息，不把不同 readout 默默合并。 |
| `metric`, `unit`, `value` | 指标名、单位和有限数值。对比符号由 spec 的权重明确指定。一个 family 只使用同一 dataset、metric、unit。 |
| `query_set_id` | 同人、同 seed、同内容 cell 下，所有配对条件共同的底层评估 query 集合 ID／哈希。跨窗口对比也须有可说明的共同评估单位。 |
| `analysis_role` | `outer_test` 或 `inner_dev`；默认分析 `outer_test`。工具不做 inner 选择或重新选赢家。 |
| `provenance` | 可选来源与分割 ID；真实绑定尽量提供，并开启 `require_full_provenance`。 |
| `metadata` | 可选补充信息，工具不把它自动解释为统计变量。 |

唯一行 key 是 `(dataset, identity, fold, seed, arm, window, metric, analysis_role)`。重复 key 一律报错，不能通过平均重复记录消除问题。JSON 内部的重复字段名也报错。

`provenance` 支持：

```json
{
  "query_ids": ["participant_01:trial_07:query"],
  "support_ids": ["participant_01:trial_02:support"],
  "population_fit_identities": ["source_01", "source_02"],
  "selection_identities": ["inner_01", "inner_02"],
  "outer_fold": "subject_partition_0",
  "source_record": "a caller-supplied immutable record identifier",
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

上面的 ID 与哈希只是格式示例，不能拿来替代真实 provenance。`population_fit_identities` 指群体 encoder、bridge、source calibration 等的来源人，不包含允许用于该人的 support adapter 的个人支持样本。`selection_identities` 指用于选择配置／步数／窗口的人；outer test 人不得出现在其中。`inner_dev` 人可以用于选择，但仍不得出现在 population fit 人列表。

检查包括：有限数值、重复 key、标签改变、同名 query 集合实际 ID 不同、support/query ID 相交、目标人与 population fit／outer-test selection 人相交，以及配对条件的 outer subject fold 改变。只有提供的 ID 能被检查；缺少 provenance 时，输出明确记录检查覆盖数，**不能把“未发现交集”写成“已证明无泄漏”**。`require_full_provenance=true` 要求每个实际用于配对的行包含 query、support、population-fit、selection IDs 和 outer fold；不需要某类数据时可以提供真实空列表。

### 已聚合输入与不同的人拥有不同内容 cell

当 source 已经正确计算了单人、单 seed 的内容均值，可用 `fold="reported_identity_mean"`，但必须额外提供 `aggregation_note`、非空 `source_fold_ids` 和 `source_seed_ids=[该行seed]`。工具不替 source 审查均值是否正确；注释必须说明其内容权重和完整性来源。

**已经把多个 seeds 平均成一行的数据，不能复制成多个 seed 行，也不能伪造一个新 seed 来代替。** 需要找回单 seed 结果，或保留在其原有分析中；本工具会拒绝 `source_seed_ids` 不是单元素当前 seed 的行。

`required_folds_by_identity` 可覆盖默认的 `required_folds`，例如某个人按注册设计只有一场 session。不能根据这次恰好下载到哪些 cell 临时把缺失项从要求中删掉。私有儿童若每人只有一个 outer test 归属，通常可统一编码 `fold="evaluation"`，把真实 `subject_fold` 放入 provenance；公开数据中同人两个 content folds 应保持为两个评估 cell。

## 2. 小 family 的声明格式

分析 spec 是一个 JSON 对象，不是运行队列。科学问题清单、服务器 job plan 或生产注册表若有额外字段，需先完成明确的 binding，不能直接塞给 CLI。

必要字段为 `family_id`, `dataset`, `metric`, `unit`, `required_seeds`, `contrasts`，并声明 `required_folds` 或 `required_folds_by_identity`。一个 contrast 的 terms 按 `group × arm × window` 指定有符号权重。

```json
{
  "family_id": "example_new_exploratory_family",
  "dataset": "example_dataset",
  "metric": "true_query_nll_unified",
  "unit": "bits/query",
  "required_folds": ["content_0", "content_1"],
  "required_seeds": [3401, 3407, 3413],
  "expected_identities": {"HA": ["ha_01", "ha_02", "ha_03"], "NH": ["nh_01", "nh_02", "nh_03"]},
  "minimum_n": 3,
  "require_full_provenance": true,
  "bootstrap": {"B": 4000, "seed": 351001, "alpha": 0.05, "resampling": "independent"},
  "contrasts": [
    {"id": "HA_benefit", "terms": [
      {"group": "HA", "arm": "reference", "window": "full", "weight": 1},
      {"group": "HA", "arm": "candidate", "window": "full", "weight": -1}
    ]},
    {"id": "HA_minus_NH_benefit", "terms": [
      {"group": "HA", "arm": "reference", "window": "full", "weight": 1},
      {"group": "HA", "arm": "candidate", "window": "full", "weight": -1},
      {"group": "NH", "arm": "reference", "window": "full", "weight": -1},
      {"group": "NH", "arm": "candidate", "window": "full", "weight": 1}
    ]}
  ]
}
```

风险改善按 `reference − candidate`，正数表示 candidate 风险更低。窗口差例如 `candidate/early − candidate/late`；如果比较的是“早期干预损害减晚期干预损害”，应把各自 full/reference 项写全，并明确其符号。代码不猜测“越大越好”，也不根据结果修改 family。

`expected_identities` 来自注册名册而非当前已有输出；允许逐 group 指定。若未给某组名册，输出 `expected_status="not_supplied"`、`expected_n=null`。`common_complete_n` 只表示本次可配对的样本数。若给了名册，输出缺失整个人的 ID、缺失具体条件的 ID，以及观察到但不在预期名册中的 ID；后者不擅自加入主 panel。

默认 `group` 按文字精确匹配。需要核心全人群 family 时可以声明 `"group_sets":{"all":["HA","NH"]}`，terms 使用 `group="all"`。`all` 没有隐式通配语义。同一 family 的不同分析组不得覆盖同一个人群层级；全体与 HA/NH 交互宜分开成已解释的 family。否则把重叠的人当独立组会破坏重采样协方差。

## 3. 精确统计定义

在每个分析组内，工具先取 **family 中全部相关条件、全部所需 folds 和 seeds 都齐全的共同人集**。同组内所有对比共享这个人集，不逐对比挑不同的人。完整性是数据配对要求，不是按性能设定的继续／终止门槛。

设 `c` 为 family 成员，`g` 为不重叠分析组，`i` 为人。对于该人的每个所需 seed `s`、内容 cell `f`，先计算有符号条件和：

\[
d_{igcfs}=\sum_{t\in(c,g)} w_t y_{igfs,t},\qquad
d_{igc}=\frac{1}{|S|}\sum_{s\in S}\frac{1}{|F_i|}\sum_{f\in F_i}d_{igcfs}.
\]

每个人先对其 required folds 等权平均，再对 required seeds 等权平均。最后：

\[
\widehat\theta_c=\sum_g\frac{1}{n_g}\sum_{i\in g}d_{igc}.
\]

组差的负号已经在 terms 中。一个人仍然是一个抽样单位；content folds、seeds、query 数量都不增加 n。不同组人数不同也不默认把组效应按人数重新加权。这种区间条件于所评估的内容和已声明的 seeds 集合；它不另外估计推广到新内容总体或新训练 seeds 分布的额外不确定性。

### 本轮新探索性区间：固定原始 SE 的 max-|z*|

`B=4000` 固定；随机 seed 必須写入实际分析记录。每次 bootstrap 对整个人的完整 family 向量重采样，保持同人的条件、fold 平均与 seed 平均的依赖关系。

`independent` 模式：各不重叠组独立有放回抽取 `n_g` 人，原始估计方差为 \(\sum_g s_{gc}^2/n_g\)。

`stratified` 模式：每组内每个预先定义的 stratum 独立、有放回抽取原来的 `n_gh` 人。固定该组的样本层权重 \(w_{gh}=n_{gh}/n_g\)，方差为 \(\sum_{g,h} w_{gh}^2 s_{ghc}^2/n_{gh}\)。它保持观察到的层组成，不估计未知总体层占比的不确定性；层的选择必须有科学或抽样设计理由。

对可估计的 family 成员：

\[
z^*_{bc}=\frac{\widehat\theta^*_{bc}-\widehat\theta_c}{\widehat{SE}_{c,\mathrm{original}}},\quad
m_b=\max_c |z^*_{bc}|,\quad
CI_c=\widehat\theta_c\pm q_{.95}(m_b)\widehat{SE}_{c,\mathrm{original}}.
\]

分母是**原始样本的固定 SE**，不使用每次重采样重新估计的 SE；因此不是旧报告的 studentized bootstrap-t。分位数使用线性插值（type 7）。输出同时保存 method、B、seed、原始 SE、critical value 和适用的 family 成员名。没有 p 值，也不把跨分析文件的所有比较自动纳入同一个校正 family。

这是有限样本探索性 bootstrap 近似，合成测试证明的是实现遵守上述定义，**不证明真实小样本人群有精确 95% 覆盖率**。固定 SE 避免某次重采样 SE 近零引起的极端临界值，不消除稀疏数据的全部推断限制。区间不裁剪到指标的自然边界。

### nonregular 不能叫“等效”

默认任何必需组 `n<3`，或任意用于该 contrast 的重采样 block 少于 2 人、经验 contrast 方差为零，都会使该 contrast 标为 `nonregular`。对应 `simultaneous_ci=null`；仍保留可计算的点估计、实际人数和原因。分层模式中出现常数层也按此处理，不能用其他层的变异代替该层未知的总体变异。

nonregular 成员不参与 max statistic；输出 `simultaneous_scope` 明确剩余可估计成员。如果 family 部分成员 nonregular，family 状态为 `partially_nonregular`，不能宣称整个原 family 都有区间覆盖。全零差值仅是样本上的精确观察，不是总体等效、没有信息或达到天花板的证据。

## 4. 可直接运行的合成示例

下例在 8 个合成人中合并 HA/NH 为 `all`，得到 early risk 改善均值 **1.8 bits/query**。这只是人为设置的数值，完全没有研究意义。

```bash
python -B scripts/paired_contrasts.py contrast \
  --rows examples/synthetic_rows.jsonl \
  --spec-json '{"family_id":"SYNTHETIC_ONLY_pooled","dataset":"synthetic_demo","metric":"true_query_nll","unit":"bits/query","required_folds":["content_0","content_1"],"required_seeds":[3401,3407],"group_sets":{"all":["HA","NH"]},"expected_identities":{"all":["SYN_HA_1","SYN_HA_2","SYN_HA_3","SYN_HA_4","SYN_NH_1","SYN_NH_2","SYN_NH_3","SYN_NH_4"]},"require_full_provenance":true,"bootstrap":{"B":4000,"seed":351001,"resampling":"independent"},"contrasts":[{"id":"pooled_benefit","terms":[{"group":"all","arm":"reference","window":"early","weight":1},{"group":"all","arm":"candidate","window":"early","weight":-1}]}]}'
```

真实文件的调用方式：

```bash
python -B scripts/paired_contrasts.py contrast \
  --rows /caller/chosen/normalized_rows.jsonl \
  --spec /caller/chosen/bound_small_family.json \
  --output /caller/chosen/new_reference_result.json
```

这里的 `/caller/chosen/` 是占位路径，不是服务器目录建议。省略 `--output` 就只向 stdout 输出；指定的输出文件若已存在会报错，不会覆盖输入或旧结果。

## 5. 物理 mask 覆盖：local pre 的 0 与 FM pre 的 50 samples

`mask` 子命令按生产函数的 **keep-mask** 语义核查：**保留指定时间窗内的输入样本，窗外位置全部置零**。`private_current_time.py` 的 `mask_patches`（仓库基线 `5ef4a60`，68–75 行）直接把 patches 乘以窗口指示函数。输入、mask 的样本位置必须相对于同一个 query anchor，且来自**实际进入 encoder 的数组坐标**。区间采用半开 `[start, stop)`，避免把零时刻算到 pre 区间。

下面使用当前私有任务的真实访问几何：采样率 **250 Hz**，pre 为 **[−200,0) ms**；local 访问 **[0,600) ms**，FM 访问 **[−200,600) ms**。换成相对事件零点的样本下标，分别是 mask `[−50,0)`、local `[0,150)`、FM `[−50,150)`。这组参考输入用于核查该几何和 keep 操作的含义，运行时仍须从实际批次导出坐标。

```bash
python -B scripts/paired_contrasts.py mask --spec-json \
  '{"sample_rate_hz":250,"mask_samples":[-50,0],"contexts":[{"id":"local_pre","input_samples":[0,150],"expected_overlap_samples":0},{"id":"fm_pre","input_samples":[-50,150],"expected_overlap_samples":50}]}'
```

| 访问路径 | `retained_samples` | `zeroed_samples` | `has_requested_data` | `all_zero_input_after_keep_mask` |
|---|---:|---:|---|---|
| local `[0,150)` | 0 | 150 | false | true：keep 操作强制整个输入全零 |
| FM `[−50,150)` | 50 | 150 | true | null：保留区间实际值未知 |

FM 保留 **50 samples = 200 ms**，覆盖所请求 pre 区间的全部50个位置；local 没有被请求的 pre 数据，keep 操作会把已有的150个 post 样本全部置零。`zeroed_samples` 统计被操作设置为零的位置，不声称这些位置原来非零。FM 保留的值也可能恰好全零，所以工具没有读实际 EEG 时，将 `all_zero_input_after_keep_mask` 设为 null，不能猜测“真实输入一定改变”或“一定不全零”。输出还保存几何 overlap、请求区间覆盖率及 `input_values_inspected=false`。

若 expected count 不匹配，仍输出核查结果，但退出码为 3；输入格式错误为 2，正常为 0。

因此 local pre 与 FM pre 的比较同时受**可访问的物理数据不同**影响：前者的 encoder 输入被强制全零，后者保留 pre 样本。这不能直接解释为两个模型对同一 pre 信息的利用差异。该工具也不能单独证明服务器 mask 放到了正确张量位置，或证明模型有／没有 pre 信息。实际加载、重采样、归一化、padding、context 长度与 receptive field 仍须从生产实现和真实批次核对；不能仅复制这个示例的区间来通过核查。工具仍支持其他采样率及任意合法半开区间，其合成边界测试与上述真实访问几何测试分别保留。

## 6. 可选纯 ID 支持量分配

`support` 输入为 `{"segments":[{"id":"segment_000","order":0}, ...],"seed":351007}`。`order` 是外部已确定的严格时间顺序，ID 和 order 都不能重复。

算法令总数为 N，前 `floor(.30*N)` 个 ID 是共同支持来源区域；30% arm 使用该区域全部 ID，10% arm 从同一区域中按固定 seed 无放回抽取 `floor(.10*N)` 个 ID。两个 arm 使用**同一个剩余末端 query ID 列表**。报告实际整数数量，不能在 N 无法整除时声称恰好 70%；N 太小则报错而非虚构支持样本。

```bash
python -B scripts/paired_contrasts.py support \
  --spec /caller/chosen/chronological_segment_ids.json
```

这只提供“同一前段来源区域内改变数量”的纯 ID 参考，10% 子集不固定为最早 10%。它不检查片段时长、类别平衡、滤波跨界、anchor 间距或 FM context halo；输出明确 `physical_context_leakage_checked=false`。真实适配仍需依据实际物理样本和 query 边界处理 context 交叉，不能仅凭 ID 集合不相交宣称没有泄漏。

## 7. 已执行的合成验证与真实验收的区别

`tests/test_reference.py` 对以下具体风险提供检查：手算的 arm 差、窗口差及组间改善差和 SE；先内容后 seed 的人级均值；条件／seed 不全排除整个 family 的该人；预期名册缺人；不同人内容 cell 数不同仍等权；显式全体合并；独立与分层 SE；零方差／小样本／singleton 层的 nonregular；稀疏 n=10 数据不采用近零的重采样 SE；重复、NaN、泄漏及 query mismatch 拒绝；inner/outer 角色区分；250 Hz 真实访问几何下 local 保留0、置零150与FM保留50、置零150 samples，以及保留位置不等于观测到非零值的 keep-mask 语义；另外的泛化区间边界；纯 ID 支持嵌套与固定 query。

示例的三个已知对比值分别是 HA early 改善 **2.8**、HA−NH 改善差 **2.0**、HA candidate early−late 风险差 **0.625**，人数每组仍是 **4**。测试还核对固定 seed 下输入行重排不改变输出、CLI 不改变输入文件且拒绝覆盖已有输出。交付前已运行 **28 项合成／参考几何测试，全部通过**；另以标准库解析 schema，核对其顶层字段与 runtime 契约一致，128 行示例全部通过 runtime 检查。当前环境未安装外部 JSON Schema 验证器，因此未执行该引擎验证；CLI 没有此依赖。实际运行记录应与包的交付核查记录一起保存。

这些合成检查没有读取真实 EEG、没有复现任何真实训练、没有验证 server exporter，也没有证明临床或神经机制结论。真实结果交回时仍须附源记录与哈希、所需 panel 的覆盖状态、实际物理 mask 核查及每个新 contrast 的统计说明。
