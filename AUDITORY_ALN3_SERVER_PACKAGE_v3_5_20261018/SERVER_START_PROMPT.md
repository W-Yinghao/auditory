# 复制给 server agent 的启动指令

这是 `W-Yinghao/auditory` 的 ALN3.5，延续已执行的 ALN3.4，不重新立项、不重训兼容结果。本包来自研究者阅读最新 GitHub `5ef4a60bf77eeaeab5582c2cb076077c0b15bd11` 后要求准备的下一轮工作。请按包接入和执行限定范围，保持既有 10-GPU 上限；依赖就绪且相关工程检查通过后，不再等待论文框架、措辞、显著性或第二次 go。

先读 `START_NOW.md`、`docs/00_RESEARCH_DECISIONS.md`、`docs/01_BASELINE_AND_INTAKE.md` 与当前服务器 AGENTS 的最新区块。如果 `CODEX_HANDOFF.md` 在服务器存在，读取其最新交接；GitHub 未提供的文件不能假装已经读取。将 `AGENTS_APPEND.md` 的最新规则合并到活动规则顶部，保留旧历史及既有精确 hold。不要取消全部旧作业、清空 hold、覆盖在跑源码或删除缓存/checkpoint。

先记录实际 local/remote HEAD、已登记计划、完成记录、运行/等待任务、真实 checkpoint/cache 可用性和代码 hash。旧报告计数不是服务器此刻状态；main 若更晚，以新输出更新 intake，但保持本包研究关切与已见结果记录，不能据新结果选择有利人员、窗口或模型。

本轮立即工作：

1. 给旧 private local/E_PUBLIC_TRANSFER 的 `pre` 全零输入及相关 TG 行列作版本化勘误，保存原数值；其后刺激、新 prior 三窗、同架构初始化分析继续。
2. 从真实 unit 的 per-participant 输出补规定的直接成对差、组间改善差、支持覆盖；不能从 aggregate CI 相减恢复配对区间。已有有效主分析不改写，本轮新增分析明确 exploratory。
3. 补齐已登记的 CB auditory continuation、受约束 D、强融合及其 inner sources；private factorial/episode、attention、prior LOO、数据曲线等有效在跑任务继续按其真实依赖和现场优先级执行，避免重复。
4. 按专题规格实现有限新增：local AP 的同目标错音频控制；固定 query 下支持数量与覆盖分离；有实质适配压力的 episode 对照；整条流程跨人开发的真实风险 checkpoint 选择；利用已有预测分解概率融合收益。现有 CS/REVE 竞争配置保留，不自动展开全模型×全loss×全时间矩阵。
5. 用新 execution ID 和独立输出路径绑定设计、数据、source/selection/access、种子及代码。先完成必要的源端/工程检查，再执行固定生产比较；禁止将 outer-test 风险、组别差或 p 值作为选择器或运行准入门槛。

研究者关心的是声音–EEG 对齐、不同听觉经历的共享表征、个人支持与时间组织。不要转成 ERP 主线、普通跨被试排行榜、校准修复论文或预定的负结果故事。具体方法失败可以保留为失败；弱结果不能升级为无信息、普遍天花板。所有有效阳性、阴性和不确定结果都保留。

只使用已发表传统核 CS、InfoNCE 与现有允许方法，不引入 VCS-QMI/未发表变分 critic。私有儿童是当前声音与历史条件读取、支持覆盖和适配机制的研究对象，个体级既有输出公开已经授权，不再请求相同确认。

先给 `INTAKE` 和实际任务绑定回执，随后持续执行；不要只返回计划就停止。每条任务回报观察、仍竞争的解释、实际完成覆盖和下一步能区分什么；不要求现在决定论文标题、贡献清单或结果摆放。参考工具仅经本地合成验证，真实 EEG 生产兼容性需服务器现场核验。
