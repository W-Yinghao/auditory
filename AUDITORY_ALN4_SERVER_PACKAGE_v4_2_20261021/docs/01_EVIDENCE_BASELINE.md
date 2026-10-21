# 1. 设计基准与当前证据

## 1.1 信息来源和时点

2026-10-21 本次制作时已通过 GitHub 页面重新读取 main；HEAD 仍为 5d2960eee61a75c048f6b6ee3cef8427d945c3cd。主要实验发布为其父提交 20592b0bd6213fb6b0e2ef667f8d225dcff2a778。已完整阅读两轮 R1 报告、两套 R2 计划、cross-stim 决定和两份 FAMILY_TABLES；source.py 已抽查实际音频/裁窗与更新循环。没有接入 live Slurm、私有数据和权重，没有本地复跑报告的人级统计。所有进度在 server 接包时刷新。

权威路径（相对上述 repo）：
- docs/auditory_alignment_v3/RELEASE_035.md
- docs/auditory_alignment_v3/aln36/R1_SCIENTIFIC_DECISION.md、R2_BINDING.md
- results/auditory_alignment_v3/aln36/r1/r1_final/FAMILY_TABLES.md
- docs/auditory_alignment_v3/aln41/ROUND1_REPORT.md、R2_PLAN.md、R2_CROSS_STIM_DECISION.md
- results/auditory_alignment_v3/aln41/r1/FAMILY_TABLES.md

下列数值是已经看到的 R1 结果，不能把据此选择的新问题称为未见结果的验证设计。R1 单 seed；人级区间条件于当前训练好的模型。

## 1.2 结果怎样改变假设

| 对象 | 已有证据 | 对下一轮的具体影响 |
| --- | --- | --- |
| HA 完全组外固定读出 | 本研究训练/标准化/选择/读出不含 HA；local G0 +.00173 [.00058,.00288]，CBpre +.00233 [.00139,.00327]，单位 MSE | 保留为共享关系的核心证据；R2 复制。这里不宣称 CB 通用预训练一生从未接触 HA |
| CI 与 TH | G0 不确定；CI 旧 pooled 同样 near 0 | 不把“未参与训练”作为 CI 空结果唯一解释；不推无信息，也不由各组显著性差异推出组间差异 |
| 时间个人更新 | 公共各组 DT=R(EC)−R(ET) 为负，约−.006至−.012，同时区间排0 | 固定复制并检查 support→query 泛化；不扩大 λ/窗 grid 救援 |
| 个人尺度项 | HA/DTU 的 GC=R(HP)−R(EC)>0，而 GH=R(H0)−R(HP)<0 | 新增 NET_C=R(E0)−R(EC) 的直接配对结果；GC 不代表净个人收益 |
| TCS−B0 内容 | DTU +.00288 [−.00628,.01204]；FAU +.01769 [.00874,.02664]，history-conditional r | CS 在 FAU 有局部增益；不称跨队列普遍优势 |
| TCS−TNCE 内容 | DTU −.03379 [−.04442,−.02316]；FAU −.01222 [−.02176,−.00269] | TNCE 是有实质证据的竞争者，原样复现 |
| TCS−GCS 内容 | FAU +.03427 [.02169,.04686]；DTU不确定 | 时间标记构造有部分依据；不等同已学好个人时间组织 |
| TCS−wrong | 两公共队列明确正，wrong本身低于B0 | 不能把全部差异归因正确配对训练的收益 |
| 源任务学习 | TNCE约step200后loss近ln32；群体q接近均匀；共同LR probe dev NMSE>1 | 用真实mask基准/投影与原tokens/δ/梯度做固定checkpoint诊断；不直接宣告数据无信号 |
| 儿童事件 full FT | B0 .535、TCS .537、TNCE .538；TCS−B0 .00239 [−.00517,.00994] | 未证实Stage2新增用途；保留完整预算和旧有效结果 |
| 儿童年龄 | MAE B0 25.05、TCS25.37、TNCE24.90，raw32.38，mean32.02月 | 年龄用途有效；当前新增收益不属于Stage2/CS |
| DTU attention | TCS/B0约.626；TCS−TNCE+.02884 [.00221,.05547] | 内容与候选判别不是一个终点；不能把胜TNCE写成胜B0 |
| 私有history异常 | 一名儿童的事件规律使H0极端失配，一个机制family临界值159.7 | 先核查原始定义与依赖，不靠剔除个体或换区间获得阳性 |

数值完整版本见上述固定提交原表；本表不能代替逐人 CSV。FAU/DTU MSE、r 与私有 bits/trial 分开，不拼成一个“统一信息量”。

以 FAU HA CBpre 已公布均值为例，NET_C=−.00604+.00243−.00233=−.00594；这只是均值恒等式推算，新的 CI 必须从同人同 query 风险构造，不能从旧 CI 相减。

## 1.3 有效历史证据的保留

inherited 的原包和 evidence/inherited_aln41_evidence_ledger.json 保留旧 SHA 与证据归属。历史主线包括六类声音成分及历史残差、固定跨窗损失与目标窗重拟合、有效 local/真正全量 CB/代表 REVE、AP−S/AP−XM/APwrong、严格 twin、支持预算与 episode 交互。它们继续承担科学论证，不因新 wrapper 出现而降为“预实验”。

必须继承的更正：
- +.009193 是 AP−XM，不能写成 AP−S。
- 旧全零 pre 输入的 local/E_PUBLIC_TRANSFER cell 无效；真实有 pre 输入的 FM 和有效 post 不连带作废。
- “儿童信息只在0–400ms”超过已有部分 FM 400–600ms 有效读出的支持范围，不沿用该笼统表述。
- 旧1秒访问窗、严格20/40ms raw参考与新400ms窗的物理访问不同，不能作同合同差值或神经潜伏期。
- ALN3.6 给旧 ALN3.5 history描述增量补出的区间跨0：不能继续把旧描述均值称为已明确的刺激特异增益。
- 原包旧 D2/GX 未完整取回的状态已被 ALN4.1 R1 intake 更新：MFF12.50是单seed线性或4seed RBF；4seed线性12.97。G1/H的train模式bug未重跑；D1数组已删除而GX staged arrays仍在。复用时以原始来源和勘误核验为准。

这些历史结果不与新 R2 合并为更多受试者、更多独立重复，也不触发整套历史重训。

