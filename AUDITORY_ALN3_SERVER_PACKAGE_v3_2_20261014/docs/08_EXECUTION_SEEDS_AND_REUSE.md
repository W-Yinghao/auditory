# 08 · 排程、多seed与复用

## 当前状态只能按server现场读取

HEAD发布快照为ALN3约82%完成；250个B_ALIGNED已放行，尚无其结果；旧909重复和约200 D策略行暂停。[S01,S08] 这些不是新包生成时的实时数字。先读取running/pending/completed及checkpoint依赖，不请求它们“回到”发布状态。

## 条件暂停，避免整个family误伤

当前`families_on_hold`包含D_ADAPT/D_ATTENTION等较宽family名。改为按具体execution/architecture/policy/source-version匹配；旧FM/dense/complement依赖继续暂停，合法local分支不因同family名被拦。**不得简单将暂停文件清空为[]来恢复全部作业。**

`queue_advice.py`是离线建议器，不调用Slurm、不改队列，遇到依赖不明输出`needs_binding`。实际解除暂停由server在原授权范围对确定行执行。

## 执行波次：是依赖顺序，不是成绩门槛

- **立即并行**：现有B_ALIGNED；A/local-D/private有效剩余单元；私有脱敏汇总；已有onestep/LR结果提取；SCI_R2目标准备；公共数据许可与下载。
- **相同访问与实际更新对照**：工程绑定后整组完成，不等aligned必须显著。真实full-update单元单独命名。
- **补充性与下游**：在合法同fold base/checkpoint就绪后启动，不等全部模型/全部seed。C独立处理epoch0和跨人验证；D新policy保留local候选。
- **公共听觉预训练/迁移**：数据合同完成即可按版本训练，不等待FM支线。资源扩展不是先把所有库搬到盘上。

优先输出完整的成对比较结果，而不是等所有逻辑行结束。运行中发现纯技术错误可暂停其依赖，范围明确；新假设的弱结果不等于整个方向无效。

## seed政策

1. 原250行B_ALIGNED按3401完整运行，已产生什么都保留。
2. 新注册少量明确的成对稳定性面板：query-aligned与访问匹配local；CBraMod/REVE真正full更新下pretrained与random；一组冻结/PEFT适配；C local、预训练、随机、普通容量；私有GX/local/当前迁移。主对照一起用3407和3413，不只重复获胜方。
3. 选择面板来自研究问题与规定的角色，不由B_ALIGNED测试排名产生。新版本已在看过旧结果之后设计，明确是建设性后续而非原始盲验证。
4. 固定一套主要probe/calibration抽样帮助隔离训练seed变化，另外独立报告读出抽样敏感性。上游base/teacher不换seed的结果称固定上游条件稳定性；关键全链比较使用配对同seed上游。
5. 旧粗接口全矩阵不补重复；已完成的原面板保存，不当新的数据复现。身份bootstrap区间条件于拟合模型，多个seed不增加n。

## 资源与运行ID

继承10-GPU上限。query-aligned重复推理比固定grid成本不同，按实际吞吐、显存和合法缓存安排；不承诺一天跑完。生成comparison inventory而非盲目扩展所有交叉；`configs`列出必须回答的问题和主变体，server复用已有相同hash。所有外fold和内容fold覆盖，不把完整实验误解成每个超参数都乘所有新轴。

旧目录和包只读；新增版本文件/sidecar/注册表，不编辑正在运行的hash代码。原结果ID保留，新输入、优化或择模用新execution hash及parent lineage；不得把新结果覆盖到原B_ALIGNED。

源checkpoint可位于已有offload符号链接；引用真实hash并保护所需依赖，不硬编码发布时的私有路径。本包不产生实际Slurm计划/取消动作。
