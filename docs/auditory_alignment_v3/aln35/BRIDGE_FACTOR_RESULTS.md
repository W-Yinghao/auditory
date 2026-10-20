# ALN3.5 bridge 映射与概率温度分解

CPU Slurm 1047402；4 个冻结 donor，40 个原 zero-shot unit，16 个 arm×B×T 条件。

完整结果显示，两个数据集的相对 NLL 优势在固定 T=1 时已经随 B 改变符号：DTU AP−XM 从 B_donor 的 +0.016683 bits 变为 B_bridgecal 的 −0.004425；FAU XP−XM 从 +0.023605 变为 −0.009471。源端温度校准进一步放大两种 B 的分离，校准后分别为 +0.051619/−0.033394 和 +0.040563/−0.013071。这里的正值表示 candidate 比 XM 风险低。这是完整身份覆盖下的描述性比较，没有新增显著性检验或区间。

因此，已见符号变化不能全部归于温度：映射改变在 T=1 时已经产生方向差异，温度再改变概率风险的幅度。B_donor→B_bridgecal 也实际改变候选排序；DTU AP 的平均真候选名次变差 84.312 位，XM 变差 61.780 位；FAU XP 变差 9.382 位，XM 变差 4.361 位。平均名次与 top1 是不同摘要，不能概括为所有排序指标均反向（例如 DTU 的 AP−XM top1 差在两种 B 下都仍为正）。同一 B 内改变正温度时，所有逐 query 排序及 top1 严格不变。

NCE seed3401，DTU AP/XM、FAU XP/XM，原 mode A。B_donor 与 B_bridgecal 原完整矩阵和 alpha 不变；两者各 2,000 个 source 拟合 segment。前者保留原 donor-fit 的 montage 混合，后者为 bridge-cal 全 montage；B 差异包含映射拟合人群/采样变化。

T=1 与同 source listener 两折的温度规则比较。两 B 共用 query、候选、poolsize、分折；B_bridgecal 的该折 query 只由另一 listener 折拟合的矩阵产生分数，T 取两折几何均值。原 alpha 与 donor 选择未嵌套在 T 折内、source presentations 跨折共享，因此这是固定超参数的 source-side 读出交叉拟合。目标 EEG/标签没有参与参数拟合或选择。

每人先平均两个 content fold，再等人求描述均值；没有将 fold 当作新参与者。原已发布两端点及原温度全部保留在 entries JSON，重放误差逐项记录。v1 的跨执行 rank 完全相等断言失败保留（CPU1047360）；v2 对每个真实分数矩阵验证同一新缓存上的原 BR 公式，历史冻结 encoder 重放误差单列，绝不以旧分数替代新四格。

| Dataset | Arm | B | T rule | n | NLL bits | top1 | mean true rank | entropy bits | score SD |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| dtu | AP | B_bridgecal | fixed_one | 44 | 9.678072 | 0.001397 | 407.903 | 9.659198 | 0.109901 |
| dtu | AP | B_bridgecal | source_fold_calibrated | 44 | 9.716011 | 0.001397 | 407.903 | 9.623175 | 0.109901 |
| dtu | AP | B_donor | fixed_one | 44 | 9.619592 | 0.004283 | 323.592 | 9.659586 | 0.107396 |
| dtu | AP | B_donor | source_fold_calibrated | 44 | 9.578896 | 0.004283 | 323.592 | 9.510233 | 0.107396 |
| dtu | XM | B_bridgecal | fixed_one | 44 | 9.673647 | 0.001329 | 406.897 | 9.662939 | 0.082799 |
| dtu | XM | B_bridgecal | source_fold_calibrated | 44 | 9.682617 | 0.001329 | 406.897 | 9.654479 | 0.082799 |
| dtu | XM | B_donor | fixed_one | 44 | 9.636276 | 0.003036 | 345.117 | 9.661240 | 0.095999 |
| dtu | XM | B_donor | source_fold_calibrated | 44 | 9.630516 | 0.003036 | 345.117 | 9.657546 | 0.095999 |
| fau | XM | B_bridgecal | fixed_one | 67 | 6.698024 | 0.011460 | 53.032 | 6.685741 | 0.083766 |
| fau | XM | B_bridgecal | source_fold_calibrated | 67 | 6.699812 | 0.011460 | 53.032 | 6.684260 | 0.083766 |
| fau | XM | B_donor | fixed_one | 67 | 6.679179 | 0.012828 | 48.671 | 6.683688 | 0.099504 |
| fau | XM | B_donor | source_fold_calibrated | 67 | 6.680192 | 0.012828 | 48.671 | 6.667509 | 0.099504 |
| fau | XP | B_bridgecal | fixed_one | 67 | 6.707494 | 0.010347 | 53.955 | 6.682289 | 0.108836 |
| fau | XP | B_bridgecal | source_fold_calibrated | 67 | 6.712883 | 0.010347 | 53.955 | 6.678553 | 0.108836 |
| fau | XP | B_donor | fixed_one | 67 | 6.655574 | 0.019297 | 44.574 | 6.681356 | 0.114688 |
| fau | XP | B_donor | source_fold_calibrated | 67 | 6.639628 | 0.019297 | 44.574 | 6.617109 | 0.114688 |

| Dataset | 对比 | B | T rule | 配对人数 | ΔR (XM NLL − candidate NLL, bits) |
|---|---|---|---|---:|---:|
| dtu | AP−XM | B_donor | fixed_one | 44 | +0.016683 |
| dtu | AP−XM | B_donor | source_fold_calibrated | 44 | +0.051619 |
| dtu | AP−XM | B_bridgecal | fixed_one | 44 | -0.004425 |
| dtu | AP−XM | B_bridgecal | source_fold_calibrated | 44 | -0.033394 |
| fau | XP−XM | B_donor | fixed_one | 67 | +0.023605 |
| fau | XP−XM | B_donor | source_fold_calibrated | 67 | +0.040563 |
| fau | XP−XM | B_bridgecal | fixed_one | 67 | -0.009471 |
| fau | XP−XM | B_bridgecal | source_fold_calibrated | 67 | -0.013071 |

正温度下同一 B 的全部 query rank/top1 严格不变，断言已通过。NLL 与熵可以变化；因此不能以 NLL 符号变化自动推断候选排序改变，亦不选更有利 bridge 替换原主结果。16 格、直接配对差与每人 provenance 完整保留，结果为描述性的接口敏感性分析。

以下直接差在人内先平均两个 content fold，再等人平均。正 NLL 差表示表中变化使风险增加；温度两列的 rank/top1 差全部严格为零。

| Dataset | Arm | B_bridgecal−B_donor，T=1：ΔNLL bits | B_donor 内校准 T−T=1：ΔNLL bits | B_bridgecal 内校准 T−T=1：ΔNLL bits |
|---|---|---:|---:|---:|
| DTU | AP | +0.058480 | −0.040696 | +0.037939 |
| DTU | XM | +0.037371 | −0.005760 | +0.008970 |
| FAU | XP | +0.051920 | −0.015946 | +0.005389 |
| FAU | XM | +0.018844 | +0.001012 | +0.001788 |

源端拟合的温度在目标数据上并不保证降低风险：它改善 B_donor 的 DTU AP、DTU XM、FAU XP，但 FAU XM 略增；B_bridgecal 四个 donor 均增。B_bridgecal 的熵同时下降，显示本次读出更自信而目标 NLL 更差。这个结果支持把源端概率接口的迁移稳定性作为具体待检验因素，不能解释为公共听觉先验无效，亦不能根据这里的目标结果重选 B/T。后续优先结合已登记的 whole-pipeline 新人真实风险选择，保留固定端点与不同接口的直接比较；这个有限分解本身不需要再训练 donor 或扩展 backbone/loss 网格。

本轮使用重新提取的冻结 donor 特征，未实现历史逐预测字节一致。GPU 1047333 在 A100-PCIE-40GB 上提取 dtu_AP；1047390 在 A100-SXM4-40GB 上提取其余三份。独立历史审计 1047375 中，原 dtu_AP 十个 unit 分别有 2 个在 A100、6 个在 V100、2 个在 V100S 上运行。历史 query 特征与逐候选分数未保存，因此不能唯一确定历史差额的数值来源，也不能把差额全归因于设备。

下表是每个 donor 内，全部人×content fold×原 B 端点的历史重放最大绝对差。它们是诊断值，不是放宽后的通过阈值。四格的新结果全部从同一新缓存计算；原端点、原温度、逐人原值和差额均保存在 entries JSON。尤其 FAU XM 有离散 top1 变化，不能声称历史 rank/top1 完全复现。

| Donor | NLL bits 最大绝对差 | top1 最大绝对差 | MRR 最大绝对差 | normalized rank 最大绝对差 |
|---|---:|---:|---:|---:|
| dtu_AP | 8.423707e−5 | 0 | 7.719563e−5 | 9.999000e−5 |
| dtu_XM | 1.472995e−5 | 0 | 6.756757e−4 | 1.351717e−4 |
| fau_XP | 6.383390e−5 | 0 | 1.435228e−3 | 2.388915e−4 |
| fau_XM | 1.394026e−5 | 8.620690e−3 | 4.307910e−3 | 3.748126e−4 |

CPU 1047402 的 5 项测试通过；独立 CPU 1047403 于 2026-10-19 04:32 CEST 验证通过：86 个源代码/源记录/缓存路径 hash 未变，40 个原 unit 完整，DTU 44 人、FAU 67 人，各两个 content fold，共 222 个格的 8 个条件共用真实 query、candidate 与正确候选。16 个条件汇总、8 个 arm 对比和 12 个直接因素差由 entries 重新汇总一致。同一新缓存上，加速计算与未修改的原 BR 公式在全部真实目标分数矩阵上的最大绝对差为 1.332268e−15。原 v1 失败、1047375 独立审计及结果已见后的 v2 修订说明完整保留。

结果：`results/auditory_alignment_v3/aln35/bridge/run_1047402/bridge_factor.json`；独立回执：同目录 `verification_receipt.json`；原端点与逐人配对值：同目录 `entries/`。结果 SHA256：`c77662e0e3223387ee9c3e2415bef560c9f2dfe4a170f17fac6ce3f8fbe51937`。源端拟合矩阵、真实 query/candidate 列表和完整缓存 provenance 保留在 private/ 与 /projects 的受限目录。
