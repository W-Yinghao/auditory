# ALN4.2：围绕既定 story 的 R2 接续与 R3 收束

日期：2026-10-21（UTC）  
项目：W-Yinghao/auditory  
设计基准：5d2960eee61a75c048f6b6ee3cef8427d945c3cd

## 这次要回答什么

**学习对响应时间组织保有分辨能力、又可用少量个体数据适配的声音–EEG统计依赖，以支持跨听者和跨听觉任务的共享读出。**

这是 ALN4.1 已确定的问题和候选方法解释。ALN4.2 用正在执行的复现、个人支持和跨刺激实验判断它能成立到哪一步，并安排一个忠实的外部方法比较和最终证据整合。CS 保留主要候选地位，TNCE 的已有效果完整保留；方法优越性、时间适配价值、儿童用途分别接受直接检验。

## 版本和研究轮次

4.2 是交付包版本，**不是第四轮实验**。ALN3.6 R1、ALN4.1 R1 已发布；两个 R2 已启动。接包时先读取当前 server 状态与冻结计划，匹配依赖与已完成产物，再执行缺失工作。本包不要求重新提交两个 R2。

- 保留 ALN4.1 R2 的 8 个 source、30 个儿童 CE fits 和既定 frozen/readout 单元。
- 保留 F_SUPPORT 的 20 项、F_CROSS_STIM 的 13 项及原主端点。
- 新增有界源任务诊断、事件定义核验、个人更新净收益汇总，默认新增主模型训练为 0。
- R3 运行原已登记的一个外部方法席位；默认仅共同公共听觉任务。没有新的儿童外部 FT 请求。
- 唯一可选消融槽本版保持未启用，不自动启动去 KL、换 backbone 或扩大训练。
- 之后完成结果、图表和方法主张判定；不进入 R4 搜索。

## 阅读顺序

1. SERVER_START_PROMPT.md：交给服务器助手的完整执行指令。
2. docs/00_STORY_AND_DECISIONS.md：问题、方法、证据和五张科学主图。
3. docs/01_EVIDENCE_BASELINE.md：当前证据及不能沿用的解释。
4. docs/02_EXECUTION_AND_BUDGET.md：已有任务接续、优先级、训练预算。
5. docs/03_SOURCE_LEARNING_DIAGNOSIS.md：固定 checkpoint 的源任务诊断。
6. docs/04_PRIVATE_SUPPORT_AND_CROSS_STIM.md：儿童、支持与跨刺激合同。
7. docs/05_PAIRED_RISK_AND_INFERENCE.md：净收益与统计参考。
8. docs/06_EXTERNAL_COMPARISON_AND_CLOSURE.md：外部方法与第三轮收束。
9. docs/07_REPORTING_AND_HANDOFF.md：交付物和判断规则。

SERVER_FULL_DOCUMENT.md 合并上述正文，便于一次完整读取。精确原合同保存在 inherited/AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021.zip，SHA256 为 eb9b343beb81994bf564a81b65577f0160547005a162db7894766e36e7971b2c；新包没有修改它。

## 可运行部分与服务器需要实现的部分

本地可运行：包校验、只读仓库接包检查、规范化源诊断数组的统计、规范化逐人风险的汇总，以及合成数学检查。统计工具需要Python与NumPy；只读仓库接包工具另需本机Git。

服务器需要实现或绑定：从实际 checkpoint/episode 导出诊断数组；从实际逐人结果适配风险 CSV；私有原始事件追溯；外部方法的忠实任务 wrapper。它们依赖未提供的服务器数据与权重，本包不把它们冒称已完成生产 runner。

~~~bash
python3 tools/verify_package.py
python3 tools/inspect_existing_state.py --repo /absolute/path/to/auditory --output /absolute/new/path/intake.json
python3 tools/check_source_probe_metrics.py
python3 tools/check_paired_risk_summary.py
~~~

不要直接运行旧包的 materialize_plan 来重新生成 R1。不要自动删除 A3b/A3c/A3d/ALN2 D_FM。本包也不包含自动推送或发送消息命令。

