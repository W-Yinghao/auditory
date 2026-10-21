# 8. 服务器实现、就绪与历史资产

本包提供已明确的研究/统计合同、数学参考、年龄小读出和只读计划工具；**实际数据封装、backbone训练与目标缓存适配仍要在server实现并核验**。不把reference代码冒称已完成生产实现，也不把缺Torch的本地检查冒称GPU成功。

## 8.1 精确复用边界

详见 `evidence/REPO_INTERFACES_AND_REUSE.md`。主要现成入口：

| 现有入口 | 可以复用 | 必须补的部分 |
|---|---|---|
| `foundation_adapter.Backbone` / `fm_aligned32` | FM构造、token与真full骨干路径 | 独立原生三crop、完整更新/位置映射；不沿用旧progressive默认 |
| `aln34.cb_auditory.Stream/run_donor` | donor解析、旧训练周边 | 原Stream只有env且NCE hardcode；新增rich三view/人内episode/CS/TNCE/GCS |
| `prior33.views.open_with_rich` / `DonorBank` / `fixed_heads` | core+rich、固定声音空间 | 物理guard、200个segment-contained ticks与多view完整性assert |
| `local_train.fit_private_fm` | 私有fold/旧FM接口部分 | 原CS/NCE prototype不是本包CE；实现共同三slot概率混合CE薄封装 |
| `aln34.content_time` / `private_current_time_v2` | 内容/历史/时间探针机制 | 旧checkpoint ID/plan不可直接接新arm；新三窗缓存与共同PCA |
| `aln35.history_interface` | 严格other-block twin、B1校准 | 核验新query与同label access、保留full与subsetcoverage |
| `aln35.support_contract/support_runtime` | U10/U30、固定query、guard | 新δ支持头与概率校准匹配，R2才运行 |
| `aln34.attention_transfer` | 修正后的候选顺序、margin/window | 同新冻结源与20smean主端点 |
| `science_aggregate_v2/science_export` | 人级配对/组别输出 | 替换旧13family硬编码；不得调用旧ALN4四臂/64人专用summary |

新模块建议隔离在 `auditory_alignment_v3/aln41/`，production配置/Slurm按项目规范生成。先复制受影响代码到隔离版本，不编辑运行中的源码。包内reference可直接导入或等价重写，但每个等价实现需比对数值与梯度；记录最终生产code commit和hash。

## 8.2 工程就绪检查

Stage1完整权重/20、31与64通道、三crop输入、全层梯度、optimizer参数组、保存重载一致；rich三view完整；人/内容split与source/target overlap；native crop与物理guard；S/Q无数据或label泄漏；wrong保持audio多view同置换；NCE与CS数学接口；低维δ只读support；source10000步transfer选择；private CE真实标签ES选择；age child内外fold；结果缓存hash均需要receipt。

先跑纯数学与一个真实小batch前后向/保存恢复，再跑生产。不设AUC/r/p-value就绪线；有限值低效模型进入结果。缺实际private数据只阻断该数据任务，不阻断已经就绪的公共工作。验证通过也不意味着方法有效。

`scripts/validate_binding.py`检查必要键、已确认字段、路径hash格式和训练/test隔离记录；它不访问server数据库，不能替代实际split/access扫描。`scripts/materialize_plan.py`仅输出有依赖的逻辑单位，不提交Slurm；实际publicfold/CPUhead/featurecache数量由binding materializer展开并登记。

## 8.3 旧结果复用与删除问题

GitHub本包基线HEAD为3da8cf5；CBAUD_PEOPLE20/20、episode seed3407 10/10等已完成。README 2026-10-20 19:55的remaining计数是旧快照，不写成现在还在运行。真正job状态由server squeue、日志和receipt确定；readme/source更新后重新绑定，不拿旧聊天状态覆盖它。

先保留 A3d 233GiB、A3c43.1GiB、A3b13.8GiB、ALN2 D_FM32.1GiB 的原始资产身份。容量不是可删证据。登记每类路径、真实bytes、checkpoint/预测/缓存性质、复用到哪些已完成/新分析、是否有不可重建权重/划分/receipt。只有某资产无后继依赖且已有验证完整的输出/来源/重建方案，才另写逐文件可删建议。本包不执行删除、不使新结果依赖已被假定删除的checkpoint。

source新资产优先保存0/2500/5000/10000四个step checkpoints、源/目标预测、可复用冻结表示索引及receipt；避免每个probe复制整个backbone。计算/磁盘成本单列，不把工程清理替代研究判断。

## 8.4 既有权限与调度

保留用户既定10-GPU running+pending总帽、Slurm计算规则、项目精确job所有权；不得scontrol或一键cancel/重置holds。`/projects/EEG-foundation-model/auditory`只读。新下载数据/模型依既有/projects约定放置，不占home重复复制。当前包准备不代表本地已连接server或提交job。

新的研究收束指令优先于旧“永远探索不定story”的表述；其余泄漏/隐私/版本边界继续。个体去标识结果在用户已授权字段范围内无需重复询问；不扩展到原始EEG、身份映射或新个人敏感字段。新GitHub发布按既有明确授权处理，本包不自动push或发送给他人。
