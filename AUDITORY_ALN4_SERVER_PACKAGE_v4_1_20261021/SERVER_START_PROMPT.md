# 发给 server 的启动指令

请接续 W-Yinghao/auditory，按 AUDITORY_ALN4_SERVER_PACKAGE_v4_1_20261021 实施下一轮。不要重新立项，不要重复已经完成且合同兼容的计算。

先读本包 `SERVER_FULL_DOCUMENT.md`、`plans/round1.json`、`docs/08_IMPLEMENTATION_AND_HANDOFF.md`，再读服务器现行 `AGENTS.md`、`CLAUDE_HANDOFF.md`、`CODEX_HANDOFF.md`。查当前 GitHub HEAD、工作树和真实 squeue，记录与包基线的差异；任何旧日进度数字都只是快照。

研究目标是“哪些声音相关关系能够跨听者/听觉经验/任务迁移，时间组织如何影响共享读出和个人适配”。不要把工作缩成五臂 AUC 排行榜。已经完成的内容成分、时间迁移、history/twin、年龄/组别、支持实验是本轮的依据和复用对象。

## 固定执行顺序

1. 保留原始结果、hold、执行身份；为 ALN4.1 创建隔离代码/结果命名空间。若 ALN4.0 已开始，登记为旧设计，保留其输出；不得静默改名成新 TCS/GCS。
2. 完成 D2/GX/NEXTMAP 旧证据 intake、私有数据 roster 与公共源/目标 overlap 核验。旧报告缺本地 blob 时，从服务器原文读取并登记；不用重新训练来“恢复历史”。
3. 选定一个可精确加载的 EEG Stage1：有界恢复 MindMix 释放的 EEG-only 资产；就绪失败则固定可信 CBraMod。不是按儿童分数选 backbone。完整 MindMix 外部方法是另一身份。
4. 建立三个原生采样时间窗、两人 × 每人 S32/Q32 episode、同一音频三视图、五臂接口。填写 BINDING，冻结数据/访问/代码/计划 hash。运行参考数学、真实模型梯度/保存重载、split/access 和 rich 三视图检查。
5. R1：TCS/TNCE/GCS 各两档 LR ×1000 updates，共 6 个短校准；共同源 dev ridge 选 LR；从同一初始化重新训练 TCS/TNCE/GCS/TCS_WRONG 各10000 updates。B0 不做 Stage2。
6. 五臂输出同一公共和私有冻结表示及内容/时间结果；B0/TCS/TNCE 做 5fold 私有 CE 全量微调（15fits）和冻结年龄回归；公共 attention 用同一 margin 的 mean-score 20s 主窗口，不开 integrator 网格。
7. 先报告科学端点、配对覆盖与身份清楚的对照，再报告 AUC/准确率、算力和优化诊断。输出完整个人级授权字段、失败/缺失原因和下一轮判断。有限值的弱/负结果不是重新调参的工程理由。

保留既定全项目 running+pending GPU 合计不超过10的约束；不使用 scontrol，不批量取消或释放旧 holds。工程和计算按 Slurm 规则执行。开发/冻结/实施按已经授权范围继续，不为一般 framing 或每个作业再请求 go；遇到真实无法解决的数据访问、正确性或资源冲突才升级。不要自动发布新的原始私有数据或身份映射；已授权去标识个人结果不需要再次询问。

先提交 `INTAKE.md`、`BINDING.json`、`IMPLEMENTATION_RECEIPT.json` 和 readiness 结果；它们是执行记录，不是等待研究者逐项批准的门槛。准备好即执行已授权 R1，期间按任务完成更新 `ROUND1_REPORT.md`。后两轮按固定闭合范围收束，保留所有有效结果，不把弱结果升级为无信息或天花板。
