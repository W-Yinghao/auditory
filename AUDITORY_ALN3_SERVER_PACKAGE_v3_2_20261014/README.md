# ALN3.2 · 查询锚定接口、真实微调与听觉主线并行推进

**服务器材料包 · 2026-10-14 · 基准9b9e03e**

[即时指令](START_NOW.md) · [可直接发server的文本](SERVER_START_PROMPT.md) · [完整文档](SERVER_FULL_DOCUMENT.md) · [变更说明](CHANGELOG.md) · [来源](SOURCE_INDEX.md)

这是ALN3.1的兼容增补，不整体替代正在运行的代码。不重复已经启动的250个B_ALIGNED，不再生成几千条同质矩阵。

主改变：P5/P6之后收窄输入失败解释；保留查询锚定路径；补相同EEG访问与真正full更新；修正残差选择；并行推进声音监督群体先验、SCI_R2与私有任务。

## 内容

`docs/`包含研究纪律、证据变更、方法对照、科学主题、私有模块、排程和交付。`configs/`是待server绑定的科学比较，不是已经提交的作业。`src/aln32_reference/`提供日程、窗口与诊断参考；`scripts/queue_advice.py`只给建议，不能控制Slurm。`tests/`与`reports/`记录本地合成核对。

## 执行

先读START_NOW，按真实HEAD和现场账本合并。既有250行继续，新增版本只运行必要完整对照。已授权范围工程检查后直接启动；没有绩效门槛或新的逐项审批。公开与私有的科学分析不等待基础模型获胜。

本包不含EEG、个体元数据、checkpoint或真实集群访问。它没有修改GitHub、取消作业、下载服务器数据或提交训练。
