# 08｜实现、完整实验和交付

## 8.1 复用入口与新目录

已存在入口：`auditory_alignment/data.py`、`model.py`、`train.py`、`evaluate.py`、`aggregate.py`、`losses_reference.py`、`run.py`、`run_ext.py`、`linear_reference.py`。实际参数以读取的当前代码为准，本包不猜测未公开原始目录。[R8–R12]

建议新增：

```text
auditory_alignment_v2/
  temporal.py
  foundation_adapter.py
  audio_targets.py
  sampling.py
  attention.py
  transfer.py
  train.py
  evaluate.py
  aggregate.py
  run.py
configs/auditory_alignment_v2/
docs/auditory_alignment_v2/
results/auditory_alignment_v2/
private/auditory_alignment_v2/
```

这是**待实现规格**，不是宣称这些模块已经存在。包内参考函数可以作为张量定义起点，不是必须照搬的最佳架构。

## 8.2 配置与登记

`configs/study.json`给出研究纪律、默认划分、训练起点与模型入口。`configs/experiment_families.json`给出完整比较族，`scripts/make_plan.py`将其展开。每一单元的状态初始为`planned`，带`implementation_status=requires_server_integration`。

模型checkpoint、预训练版本、adapter层名、实际源数据路径和donor ID需由服务器填进`resolved_config`。未落实的字段保持null或unresolved，不用虚构值让校验通过。任何与现有结果有关的计算都应写入真实runtime版本。

计划行包括`work_type`，区分完整训练、迁移训练和每fold的个人适配bundle。一个bundle可能包含多名参与者的低维适配，不把它称为一次完整主干训练。计划总数不是所需独立样本数，也不是资源上限。

## 8.3 科学计算经Slurm

沿用仓库纪律：真实CPU/GPU训练、数值测试、环境探针与分析经Slurm；文件查看、编辑和调度属于编排。保护`/projects/EEG-foundation-model/auditory`读取来源，不在只读来源覆盖文件；使用服务器已批准的可写worktree。[R13]

本包`slurm_unit.template.sh`必须在服务器将真实runner接通后才使用。模板只给任务加载方式，不臆造partition、account、GPU数或路径。并行量按集群实际情况调整；小CNN适合的MPS并发不能机械套到大基础模型。

本地包验证是在本对话容器中完成，不是服务器作业。本包没有执行远程训练、提交Slurm或传输到服务器。

## 8.4 训练预算是起点，不是研究限制

小网络沿用约200epoch作起点；基础模型使用其合理学习率与单独backbone/head参数组。配置中的轮数、批量、学习率和权重衰减允许完整调整；所有改变用新recipe或可恢复续训记录。

真实训练必须覆盖计划的数据，不把短run当full experiment。比较不同batch时记录epoch实际更新数、抽样覆盖和日程长度；gradient accumulation不等于扩大核CS统计batch，若需要跨microbatch核矩阵，应有可微收集或明确不同估计方案。

新预训练模型以冻结、PEFT、部分层、完整微调和随机同架构并列训练。校准/早停/模型选择是训练程序的一部分，不是科研有效性的准入门槛。无法完成的任务保留技术原因和续跑计划，不输出零分占位。

## 8.5 只保留必要的技术检查

检查时间裁剪是否真正限制模型输入；语音辅助通道是否剔除；标签/历史的时间顺序；身份与内容分割；基础模型幅值、采样率和通道接口；训练/验证模式恢复；损失与输出有限；恢复点重跑一致。技术错误必须修复，影响范围明确后重算。

无需新建数十个合成世界才允许真实训练。包内短测试没有真实数据能力含义，也不证明生产估计器或临床解释已经成立。

## 8.6 结果数据结构

逐query字段建议：匿名参与者键、source split、model/checkpoint、task、target/candidate set、window/support、true/mismatch score、true/mismatch loss、prediction、label、adaptation setting、内容键。敏感键和逐人值留在`private/`。

聚合字段参考`schemas/result_record.schema.json`：方法和任务性能、相对baseline的配对差、训练波动、人数/内容覆盖、当前证据范围、竞争解释、下一步干预。结果状态不使用`NO_INFORMATION`或`NEGATIVE_PAPER_READY`。失败运行是技术状态，不是科学结论。

## 8.7 交付文件

```text
IMPLEMENTATION_RECEIPT.md
RUN_MANIFEST.jsonl
FULL_METHOD_RESULTS.md
TEMPORAL_RESULTS.md
FOUNDATION_ADAPTATION_RESULTS.md
AUDIO_TARGET_RESULTS.md
ATTENTION_AND_SHARED_MODEL_RESULTS.md
PRIVATE_TRANSFER_RESULTS.md
GROUP_DEVELOPMENT_FUNCTION_RESULTS.md
NEXT_METHOD_DECISIONS.md
```

另有机器可读aggregate、完整曲线与checkpoint清单。逐人数据、模型权重、详细身份、日期与原始日志不自动发布。此前对特定release的push授权不自动扩展到本轮。服务器可以准备本地提交，但推送/分享按用户另行指令。

## 8.8 允许研究调整，不允许选择性重写

基础模型接口/内容多样性/稳定声音目标等有新的合理设想时，登记后做完整实验。不要求在一个有限默认列表里永远转圈；也不因为发现反例就把每个技术问题写成论文贡献。

新增分析说明已看过哪些结果；旧结果不覆盖。模型选择依据训练侧任务性能，科学关联统一出表。下一轮资源建议要说明有望改善什么，不按‘哪个p值最接近0.05’排队。
