# Auditory：Story-first 研究与服务器材料包 v1.0

**日期：2026-10-02｜基准SHA：558e6509d64e0decb4d796ee51964f7ff6a30ee2**

## 先读什么

1. `01_STORY.md`：临床问题、方法贡献、终点、数据角色、论文骨架与失败边界。
2. `02_SERVER_EXECUTION.md`：可以实施的限定首轮及交付要求。
3. `03_METHOD_SPEC.md`：SRP公式、标签预算和概率评分的实现定义。
4. `config/story_v1.yaml`、`experiment_registry.yaml`：机器可读范围与对照。
5. `SERVER_START_PROMPT.md`：可直接交给服务器代理的启动文本。

`04_COMPETING_STORY.md`单独保存个体响应评估，不是主story失败后的自动备用论文。配置默认关闭。

## 文件状态

- 研究与执行文档：完整候选规格。
- `reference/`：可运行的核心数值原型；不含真实数据适配、不含完整临床训练器。
- `tests/`：合成张量/数组测试；验证公式与控制流，不证明研究假设成立。
- `scripts/build_task_manifest.py`：从配置生成限定任务表，不读取EEG、不训练。
- `scripts/slurm_template.sh`：调度模板；真实入口尚未实现时拒绝运行。
- `templates/`：报告与实施说明模板。
- `validation/`：本次在对话容器内的检查回执；不等于服务器通过。

## 核心范围

主SIR五级概率，MUSS固定次结果；每外折12、24及全部临床标签。已有刺激主干冻结，新增30个小型条件/pooled表示。临床头预计8250次、上限9000。MFF扩展、原始EEG新主干、年龄主任务和竞争story默认不运行。

## 安全与可追溯性

包内无原始EEG、临床逐人标签、身份边、真实模型权重或凭据。不自动安装环境、不下载数据、不联系医生、不发送邮件、不修改仓库、不提交作业、不推送产物。

服务器可把本包复制到独立工作目录，按原始仓库接口实现新`auditory_story`适配。不要覆盖旧文件或将本包当成已完成训练结果。

## 本地合成测试

```bash
python -m pytest -q tests
python scripts/build_task_manifest.py --config config/story_v1.yaml --out validation/planned_tasks.json
```

服务器环境中，即使运行这些数值测试也遵守其Slurm规则。本次对话容器执行只涉及合成张量，不访问服务器资料。
