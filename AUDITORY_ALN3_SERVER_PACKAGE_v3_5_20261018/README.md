# AUDITORY ALN3.5 — 下一轮 server 执行包

**2026-10-18；延续 ALN3.4，保持探索阶段。** 本包基于重新读取的 GitHub `W-Yinghao/auditory`，制作基线为 `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11`。包内状态是该推送的快照；server 接入时先对账现场变化。

本轮研究问题：哪些声音相关结构能够跨听者使用；个人适配还需要哪些支持；同一声音内容的读出如何随时间位置变化。方法候选为有效 local、查询锚定且充分微调的 CBraMod，并保留代表性 REVE、传统核 CS 与 InfoNCE。没有预定最终论文框架。

## 发给 server agent

把整个目录或 ZIP 交给 agent，复制 [`SERVER_START_PROMPT.md`](SERVER_START_PROMPT.md) 中的指令。完整规格见 [`SERVER_FULL_DOCUMENT.md`](SERVER_FULL_DOCUMENT.md)。按 [`START_NOW.md`](START_NOW.md) 接入；每条任务读取相应专题文档。

## 本轮明确决定

1. 已完成结果直接分析；补科学与主终点的直接成对差、组间改善差和个体支持覆盖，不重新训练兼容基线。
2. local 的旧 `pre` 遮罩实际全零：定点勘误，原值留档，后刺激和新版先验结果继续使用。
3. 补齐已登记的 CB 听觉中间训练、受约束适配、强融合及其他有效在跑依赖；旧 hold 不批量解除。
4. 只新增有明确用途的有限对照：AP 同目标错音频、同支持池内数量/覆盖、episode 的实质适配压力、源端真实风险选择、概率融合来源。
5. 统计主分析保留；本轮新增比较标为已看历史结果后的探索性分析。低效或失败配方可以失败，所有有效方向均报告。

## 包内入口

| 内容 | 文件 |
|---|---|
| 研究关切、假设与工具 | `docs/00_RESEARCH_DECISIONS.md` |
| 最新证据、现场对账与复用 | `docs/01_BASELINE_AND_INTAKE.md` |
| 科学/儿童/时间勘误与直接对比 | `docs/02_SCIENCE_PRIVATE_AND_CORRECTIONS.md` |
| 公共先验、checkpoint 选择与数据需求 | `docs/03_PRIOR_AND_CHECKPOINT_SELECTION.md` |
| 支持覆盖与适配友好训练 | `docs/04_SUPPORT_AND_EPISODE.md` |
| 强融合、读出敏感性与注意 | `docs/05_FUSION_READOUT_ATTENTION.md` |
| 资源、身份、统计和交付 | `docs/06_EXECUTION_AND_REPORTING.md` |
| 参考工具及输入契约 | `docs/08_REFERENCE_TOOLS.md` |
| 任务清单与比较清单 | `plans/workpackages.json`；科学probe 10个family/30项：`plans/science_contrasts.json`；原主终点组差3个family/10项：`plans/main_endpoint_group_contrasts.json` |
| 回执模板 | `templates/` |
| 包校验、现场只读对账、参考分析 | `scripts/` |

`src/aln35_reference/` 是经过合成数据验证的分析参考工具。它不训练 EEG 模型，不提交或取消作业。模型训练适配到服务器现有 `aln34/` 与 `prior33/` 代码，使用新版本执行身份；不能把本包的本地验证报告写成真实实验已完成。

既有 10-GPU 项目上限继续有效。个体级已授权模型输出可继续发布，不再询问相同授权；原始 EEG、身份映射、姓名和原始私有记录不因本包增加公开范围。
