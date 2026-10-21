# AUDITORY ALN4.1 — 声音关系、时间组织与可适配共享表征

**交付日期：2026-10-21（Europe/Paris）。这是 ALN3.4/3.5 的延续，也是 ALN4.0 服务器包的设计修订。**

研究问题：听觉 EEG 中，哪些与刺激有关的关系可以跨听者、听觉经验和任务迁移；响应的时间组织怎样影响共享读出与个人适配？

本包将新的 Stage2 方法接入已经完成的声音成分、时间迁移、history/twin、人群和支持适配证据。私有儿童同时承担未见儿童的当前声音读出、历史条件控制、时间组织、冻结表示年龄预测及后续有限跨刺激检验，不只是一个 accuracy 外部测试。

## 从这里开始

1. 给服务器代理读 `SERVER_START_PROMPT.md`；完整合同见 `SERVER_FULL_DOCUMENT.md`。
2. 首先对照当前 GitHub、服务器 `AGENTS.md`、`CLAUDE_HANDOFF.md`、`CODEX_HANDOFF.md` 和实际队列，完成 intake。此包复核的 GitHub HEAD 是 `3da8cf5758214c0cf87a1f1c8d67fb84b574000e`，不是服务器实时队列状态。
3. `plans/round1.json` 是固定设计；`templates/BINDING.template.json` 必须用真实资产、划分和代码 hash 填写。模板中的空值有意保留，不能生成伪 receipt。
4. `reference/` 包含可执行数学、时间访问和年龄读出参考；`scripts/` 包含计划展开、绑定检查、配对统计及校验。**尚未提供已在私有数据上运行的生产 trainer。**服务器需要用仓库现有接口完成薄封装和受影响的模块实现，然后通过工程检查进入生产。

本轮固定 6 个源短校准、4 个源生产训练、15 个儿童 CE 全量微调；五臂均做冻结内容/时间分析。冻结年龄读出只用 B0/TCS/TNCE 与两个基线；实际 CPU head 数及公共目标 fold 数在 binding 后展开，不能把逻辑分析包误报成一个 fit。

R2 复现并回答一个小规模个人适配问题；R3 完成一个忠实外部比较和必要的最终消融。三轮结束，不滚动增加模型网格。主线不要求 CS 胜过 InfoNCE，也不预设 MindMix 胜过有效 local 或真正全量微调 CBraMod。

## 包内验证

```bash
python3 scripts/verify_package.py
python3 scripts/verify_handoff.py
python3 reference/verify_temporal_cs_numpy.py --out reports/VERIFY_TEMPORAL_CS_NUMPY.server.json
python3 reference/verify_temporal_torch.py --out reports/VERIFY_TEMPORAL_TORCH.server.json
python3 reference/verify_time_access.py
python3 reference/verify_age_probe.py
python3 scripts/materialize_plan.py --out /tmp/aln41_logical_units.json
```

服务器上的 CPU/GPU 计算、环境探针和测试仍按项目既定规则通过 Slurm 运行；以上是作业内命令，不是登录节点计算许可。只有 `materialize_plan.py` 是不提交作业的计划工具。Torch 缺失返回明确的未完成状态；不能将纯 NumPy 校验写成 Torch/backbone/私有数据集成通过。

历史完成结果、旧作业身份和 scoped holds 均保留。包不含数据删除脚本、不接管既有队列、不自动 GitHub push。A3d/A3c/A3b/ALN2 D_FM 的容量信息不足以判断可删，本轮先复用登记，另作逐资产依赖审计。
