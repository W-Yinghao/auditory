> 发布副本：用户在本轮验收后明确要求将代码与聚合结果推送到GitHub。文内“未push／不自动发布”描述该授权之前的状态；个体数据、模型及详细日志仍不发布。历史进行中状态以final_002为准。见[发布范围](../PUBLICATION.md)。

# A2 与 C2-S 纯函数契约 v2

依据 `AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md` §§2/6/7/12。本文件冻结首阶段实现细节；未运行真实新效应、未提交作业，不是主实验完成回执。旧 `auditory5` 源码、输出和失败记录只读。所有测试、合成计算和后续分析由 root 统一在 Slurm 执行。函数不读路径，不写文件，不调用 loader、模型训练 runner 或临床资料。

## A2：共同支持与抽样

公开接口位于 `auditory_next/a2_overlap.py`：

```python
frozen = freeze_overlap(events, folds, literal_one="1")
draws = draw_trials(frozen, seed=20260917)
summary = summarize_draws(features, trial_ids, draws,
                          feature_scope_id="one_explicit_encoder_scope",
                          candidate_subset=one_fold_groups)
```

`events` 为完整事件元数据的 records 或 DataFrame。必要字段：

```text
trial_id, split_group_id, record_id, segment_id, stimulus_local_id,
previous_event_id, previous_code, previous_run_length,
history_chain_complete, accepted, A_boundary_eligible,
A_half, A_block_id, segment_position_fraction
```

`history_chain_complete` 是调用方从 **QC 前完整链** 审计得到的可解析过去链布尔值。不是旧 B 的 `history_target` 非空指标；已知 run=2 不是未知历史，但不符合 A2 的 run>=3 新估计区域。函数不重算历史，不读取 current_run_length，不根据 accepted 删除前一声音。`previous_code` 与显式 `literal_one` 精确比较，不推断声学角色。旧字段类型转换由 root 的事件适配层负责。

当前 accepted 与 A_boundary_eligible 必须显式为布尔值；块保护已由调用方按冻结的实际滤波支持完成，模块不重定义秒数、启动保护或事件采样轴。`segment_position_fraction=.5` 进入后半位置；1.0 允许进入后半。A_half 是冻结的交替 A 块半份，不能换为记录前/后半。

cell 固定字典序：

1. `run3_5_pos0`
2. `run3_5_pos1`
3. `run6plus_pos0`
4. `run6plus_pos1`

仅枚举大小 2–4 的 11 个 Ω。每名候选的每个 Ω cell×half×当前 class 必须有至少 6 个 trial；每个 half×class 的 Ω 并集至少 3 个原块。块主键为 `(record_id, segment_id, A_block_id)`，不能把多个来源的局部块号误当同一块。候选资格在保守 split_group_id 级计数；输入必须已限于冻结身份外折允许的研究来源，不把多个记录当独立候选。

主支持要求 >=25 候选，5 个旧外折每折 >=2 测试、>=12 训练。先最大 cell 数，再最大候选数，再 cell ID 字典序；不降低配额、不换折。无主支持时，描述性“最大支持”明确采用 **最大候选数、再最大 cell 数、再字典序**；保留 `DESCRIPTIVE_ONLY`，人数为零则 `INSUFFICIENT`。11 个区域的支持及每折 train/test 数都保存在冻结对象中。

所有候选/类别/半份/表示共用 `q(c)=1/|Ω|`。冻结对象包含选中区域的 trial-ID 池，`draw_trials` 不再读取 events，因此冻结后的标签/QC 改动不会触发新 Ω 或重新定义抽样。若要改变设计，必须显式调用新的冻结步骤并生成新版本。

每次重复、每个 half×class 的抽样：均匀选择 3 个不同原块，每块均匀选择 1 个 trial 作为锚点，再在各 cell 中无放回补足 6 个。这样抽到的实际样本仍有 3 块，而不只是候选池满足 3 块；每 cell 六个独立 trial。同一重复内不复制试次，不同重复可以复用。该预定块约束抽样 **不是所有六元子集上的均匀抽样**，与无约束抽样有所区别，必须随结果披露。固定 20 次重复；seed 由总 seed、冻结定义 hash、候选/half/class/repeat 确定，输入行顺序不影响抽样。

`TrialDraws.trial_ids` 形状为 `[20,candidate,half,class,cell,6]`。汇总先 cell 内平均，再用统一 q 求和；输出 `means[20,candidate,half,class,feature]`、`delta[20,candidate,half,feature]` 和 `common_response`。不称共同响应为纯伪迹。临时特征分配按一个 repeat/cell 处理，避免展开全部抽样张量。

`feature_scope_id` 必须为一个显式字符串。每个 outer/inner 坐标分别调用，不跨 encoder 坐标拼接。此接口没有 scaler/PCA 拟合；root 的后续 runner 只在对应合格训练候选上拟合至多 8 维变换。全队列实验标签计数参与 Ω 研究设计这一点须披露；它不是部署时仅训练来源可确定的选择。

冻结对象、trial-ID 抽样表和任何实际个体向量只留 private。`metadata_hash` 校验有效元数据 trial 池；完整源文件/完整事件链的 hash 由 root registry 保存，不能把该池 hash 当作完整原始账本 hash。

## 残差审计

`auditory_next/a2_residual_audit.py` 提供：

- `inner_product_decomposition(delta1,delta2,prediction1,prediction2,candidate_ids)`：单折坐标下每个配对的四项矩阵、同/异身份均值与差。形状 `[repeat,candidate,feature]`，或无重复的 `[candidate,feature]`。核对 `DD-DP-PD+PP=RR`，容差为 `1e-11 * max(1,各项矩阵尺度)`；不能把该等式用于 cosine。
- `identity_contrast`：异人均值排除所有相同身份配对，包括 bootstrap 中重复抽到的同一候选。
- `matching_statistics`：并列 inner product、cosine、范数。零向量使 cosine 明确为 `None / UNDEFINED_ZERO_NORM`，不会补成 0。
- `fit_background(background_train,delta_train,alpha=10)`：只接受训练数组；候选等权，先取半份均值，中心化 ridge，未惩罚截距。alpha=10 冻结为旧背景审计尺度，不搜索新结局。没有用评估数据拟合或选择权重。
- `make_residual_world` 与 `audit_residual_world`：一次只构造一个虚拟世界，并给出 Delta/P/R 的并列匹配及四项分解。

合成计数按 root 的 v2 解释冻结：**3 个生成机制×100 次=300 个独立 draw**。三个机制为 `null`（Delta 两份独立噪声）、`predictable_nuisance`（稳定背景产生真实可预测 nuisance）、`individual_stimulus`（稳定个体刺激向量，背景与其独立）。同一个 draw 同时计算 `zero`、`fixed`、`fitted` 三个 W 条件；W=0 是对照条件，不是第四个独立世界。null 的非零 fixed 和有限训练样本 fitted W 可以产生共享预测项驱动的残差重复结构；交叉验证不能自动赋予它神经有效性。

所有机制用虚拟 train/test 候选、独立噪声和目标，不用临床值。可通过 n_train/n_test 与正的 `[candidate,half]` noise_scale 传入冻结支持对应的规模/精度；不能把无资格候选填零，或看结果删掉困难样本。若单 trial 噪声方差为 1、两类每格 6 次且 Ω 大小为 K，独立试次近似的 Delta 噪声 SD 为 `sqrt(2/(6K))`，仅是明确的合成机制参数，不是对真实试次独立性的断言。

N1 4×30、N2 3×30、N3 3×30 加 A2 300，共 600 independent mechanism/repetition draws。代数测试、空间注入小例和同一 draw 的审计条件不扩充该随机功效研究预算。这里的单元测试仅检验性质，没有运行 300 次 A2 实验。

## C2-S：空间几何

公开接口位于 `auditory_next/c2_spatial.py`：

```python
parts = decompose20(x, channel_names)       # x: [...,20,time], 原通道顺序明确
full_average_reference = reconstruct20(parts)
z19 = coordinates19(parts)
parts_again = from_coordinates19(z19, channel_names)
forward19x20, inverse20x19 = linear_maps(channel_names)
views = l0_views(parts, sfreq=250)
```

固定 L8/R8/M4 为计划指定电极：L=`Fp1 F3 F7 C3 T3 P3 T5 O1`，R=`Fp2 F4 F8 C4 T4 P4 T6 O2`，M=`Fz Cz Pz Oz`。实际名字和顺序必须由来源证据确认；缺失、重复、用 VREF 等替代或自动别名均拒绝。不插值、不补零、不从不一致 QC/滤波状态的左右数组拼装重建等式。

五项严格使用计划公式 `u_L,u_R,u_M,m_LR,m_M`；局部项由只接受本组数组的 `local_center` 计算。右侧有限数值干预不改变左局部项；联合均值成分按定义可变。完整输入验证/QC 的选择集合仍可能依赖全头，不能把数值隔离称为选择规则隔离。共同参考漂移在浮点容差内不改变五项。

局部有效维数为 7/7/3，加两项均值差，共 19；固定 Helmert 基构造可逆独立坐标，不拟合 PCA，不读取标签。`inverse @ forward` 等于 20 通道整体平均参考矩阵；重建只恢复平均参考信号，不能恢复被移除的共同参考。float64 单元测试逐样本验证，并检查任意线性头的坐标合成保持 logits；这是可实现线性映射的代数一致性，不是有正则读出应具有相同分数的承诺。

主空间 L0 矩阵保留计划原局部坐标：S0/S1/S2 通道宽度 16/17/22，有效空间维数 14/15/19；FULL20 宽度 20、有效 19。S1 为 S0+m_LR；S2 为 S0+m_LR+u_M+m_M。重复列控制按 S0 原通道顺序循环追加，分别扩至 17/22，绝不引入标签或新数值。固定 250 Hz 下每 5 samples 均值为 20 ms；不能把原始 fs 直接当 250 Hz。时间长度须为 5 的倍数，不静默丢弃尾部。输出按 channel-major 分箱展开。

`inject_spatial_world` 提供仅 crossmean、仅 midline、仅左内部差异、共同参考漂移和右侧干预五个无调参小例。前三个以精确构造证明信息被保留/移除，不拟合分类器、不构成功效估计。增加跨组/中线项不叫“独立专家”、半球协同或解剖源分解，不能喂给旧 CNN 假装原 latent。

## 本阶段剩余工作

当前只有纯函数、合成单元测试和上述接口冻结。Slurm 测试结果、真实 Ω、合格人数、真实特征来源/Scope、空间通道证据、有限空间导出、实际读出与 bootstrap 都由 root 后续 gate/runner 给出。本实现没有宣称模块 PASS、端到端 PASS、数值稳定或真实科学效应。真实 A2 主结论仍来自未校正差异及必要对照；残差单独转正不授权继续训练。
