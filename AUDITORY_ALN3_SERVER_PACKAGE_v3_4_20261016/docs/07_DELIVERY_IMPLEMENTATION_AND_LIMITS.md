# 07 · 报告改为“证据 → 问题 → 实验”

## 第一批交付

1. `D_MULTI_SEED_RESULTS`：已完成面板的真实覆盖、配对结果、native/unified与缺项，说明评分更正范围。
2. `PRETRAINING_LEARNING_EVIDENCE`：CBraMod匹配初始化、TF–L1复用面板、REVE代表对照与学习轨迹；不把12格当12独立复现。
3. `COMPLEMENT_FUNCTION_REPORT`：直接base/SC-base/融合的同合同风险，RS功能四层及dev/test差；资产不可用处明示。
4. `PUBLIC_PRIOR_EXECUTION_STATUS`：实际已注册、提交和完成的训练，不再只是一份待定草稿。
5. `HEARING_CONTENT_TIME_ADAPTATION`：固定候选的内容、时间、人群与私有任务研究进展，以及仍未检验的问题。

每张结果表标真实来源版本、实际seed范围、身份数、目标和单位；不需要重复几十条“允许短语”。稳定的科学对象写清即可。

## 新报告模板

按 `templates/EXPERIMENT_UPDATE.md`：当前观察（完整差值）→工作解释→竞争解释→下一干预→实际执行。最终论文标题、正文/附录、成稿与否都可保持未决定，但不能继续把它们作为实验等待项。

方法比较与新分析分开：已有统计结果可以立刻形成带限定的工作结论；解释可以随数据更正。探索得到的候选在未来新队列/内容上验证是额外证据，不能由增加seed替代。

## 代码接入说明

`src/aln34_reference/`只包含合成可验证的：残差功能指标、交换反对称评分、身份初始化adapter与严格配对工具。它不加载EEG，不替换当前CBraMod/REVE实现，不包含Slurm控制器。`scripts/audit_seed_pairs.py`只读用户提供的标准化元数据索引，输出可配对/缺失项，不按性能筛选，不提交或取消作业。

测试覆盖数学/张量/元数据语义，不证明真实数据对齐或模型有效。生产server仍需绑定实际tensor轴、更新范围、input support、split和target hash。工程检查应短而针对真实错误，不是一个新的科学performance gate。

## 来源与版本

主输入 `sources/ALN3_BRIEF_20261016.md`原样保存，hash在`SOURCE_INDEX.json`；包含旧规则与已经看过的结果，**不是本包生效指令**。ALN3.3公共合同原样保留。未在本轮查看新GitHub提交；现场若已实施部分工作，直接复用并记映射，不回退新代码。

包内所有任务卡是执行意向，非生产作业行，没有声称某任务已经提交或完成。发布授权继承，勿再次询问。需要超出既有资源或数据权限时仍按真实范围处理；这不影响已批准模块继续。
