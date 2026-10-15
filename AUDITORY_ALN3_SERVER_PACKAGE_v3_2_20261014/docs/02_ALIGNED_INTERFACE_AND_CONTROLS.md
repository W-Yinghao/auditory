# 02 · 查询锚定接口：继续现有训练，补齐可解释的比较

## 1. 继承而不改写B_ALIGNED

每个声音查询q，取`[q−0.4s,q+0.6s)`；查询位于5秒段首时，段首之前置零。128Hz下pre=51、post=77，共128点；实际边界为−398.44到+601.56ms，按代码整数样本定义而非理想小数。100Hz下为40+60点。随后重采样到200Hz、单patch、各通道token LayerNorm→展平线性头→L2。与旧B_DENSE的多patch上下文读出不是同一结构。[S04,S05]

继续现有250行、ID、代码hash与recipe。其命名增加描述性字段`effective_recipe=legacy_progressive_prefix`，不能更改旧原始记录或暗中换权重；通过sidecar补实际更新范围。后续新训练用新execution版本。

B_ALIGNED只继承整个片段允许的EEG访问上限：这不等于它与local `[q,q+0.6s)`逐query访问相同。负lag输入是连续声音中的过去EEG，不是无刺激基线。

## 2. 最小而完整的支持匹配

| 对照 | EEG输入与作用 |
|---|---|
| L0 existing_local_post600 | 现有local读取[q,q+0.6)；复用既有结果。 |
| L1 local_aligned1000 | 有效局部架构读取与B_ALIGNED完全相同的1秒窗、同段首mask；评价额外过去EEG与对齐模型的共同影响。 |
| F1 aligned1000 | 已在跑的B_ALIGNED；不再生成同一250行。 |
| F2 aligned_post600_padded | FM单patch的前0.4s固定零，后0.6s用与L0同一真实EEG；不能叫读取1秒真实EEG。先对冻结与PEFT做两主干、全部fold/content。 |
| R1 raw_aligned1000 | 同一1秒原始输入的训练侧正则化线性参照；读出预算与高维正则化单列。 |

历史local的末点可能沿用旧inclusive索引，因此先从真实batcher导出样本offset；不能只因都叫600ms就宣称匹配。若F2的77个post样本与旧local的78个样本不同，新增`local_post_exact_matched_to_F2`作为精确对照，旧L0只作历史桥接；不要暗中裁短已有checkpoint输入。比较L0↔L1时先对齐这一个端点约定，F1↔F2估计FM中额外上下文的价值；F1↔L1和F2↔精确匹配local才更接近访问匹配的方法比较。仍需说明参数量、头、监督与优化不同，不称纯神经信息量。

所有主格完成原有全部参与者外折与内容fold；不根据P6比值先筛队列。段首补零与内部完整窗口分层重评价，同时保留全部query主结果，不为抬分只删边界。真实record边界不能从文件邻接推断；不得读取下一人/下一记录。保留有效样本mask、nominal/actual support与query/candidate哈希。

## 3. 接口归因，不将一个成功点包装成唯一原因

优先复用P5/P6，不重跑相同“查错”流程。需要解释对齐收益时，用固定主干、相同LN+flatten线性头比较query-aligned单patch与固定网格选中patch。若增加单patch/多patch比较，记录总上下文与其mask，不把不同信息访问当同一输入。

`aligned_patch_linear`比旧头更好，也可能来自局部context、头的复杂度、预训练输入分布变化或参数共享。单patch会改变Transformer能使用的上下文：尤其一个时间patch时不能把它等同原多patch时序建模。P6是选择新接口的证据，不是完整机制分离。

## 4. 时间query与EEG贡献分别量化

旧dense输出随q变化，可能来自时间位置编码。本包的`query_content_diagnostic`区分跨query公共模板、固定query下的片段差异；再以同query合法交换EEG检查任务风险。不能用方差比例大或相邻余弦低证明EEG被用到。

该诊断面向旧dense或新的融合分支；B_ALIGNED没有显式query_pos通路，但段首补零和数据采样仍要记录。无须让此诊断数值“达标”才启动其他模块。

## 5. 细时间输出与早晚神经解释

查询步长不是实际EEG时间访问长度；本轮1秒窗覆盖过去和未来响应。它适合总体声音检索或支持条件下的个体适配，不直接给出早窗独有信息。

严格时间科学主线继续用原本的局部受限输入编码器和raw局部参照。0.4秒前窗、上下文FM输出不可回流到同query的早期局部分支。Teacher训练可读丰富输入，但student推理必须只读其声明窗口。
