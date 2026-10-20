# 接入顺序

## 1. 只读对账，保持已有运行

从当前仓库根目录记录 `git rev-parse HEAD`、`git status --short`、远端 HEAD。记录当前 UTC 与 Europe/Paris 时间。检查活动计划和确切 job/execution 身份；读取实际完成记录，不以 README 或旧对话代替实时状态。

可先运行本包的本地分析工具（替换为真实绝对路径）：

```bash
python /absolute/path/to/package/scripts/validate_package.py --package /absolute/path/to/package
python /absolute/path/to/package/scripts/intake_snapshot.py --repo /absolute/path/to/auditory --package /absolute/path/to/package --out /absolute/path/to/new/intake.json
```

第二条只读仓库并写指定新 JSON；不联网、不读 Slurm、不改变 repo。远端 HEAD、队列和服务器私有资产由 server agent另作现场对账，不把工具输出当完整 live inventory。不要在未读源码时执行旧 `maintain_fleet`/`register` 脚本来获取状态。

## 2. 同时开展三个互不阻塞的工作

- **解释勘误和直接重分析**：执行 `docs/02` 的科学probe清单（10个family/30项），并按 `docs/01` 另行绑定 `plans/main_endpoint_group_contrasts.json` 的原主终点组差（3个family/10项）；两者保留各自终点、来源和family。已完成结果的CPU分析不等待新训练。
- **现有任务收尾**：按真实依赖补齐 CB 听觉/inner sources/受约束 D/强融合；既有其他有效任务继续，不清空旧 hold。
- **有限新增实现**：在新命名空间实现 `docs/03–05` 的新比较和输入导出，复用现有生产数据与 checkpoint。

某个特定缓存或 donor 不可用，只影响需要它的任务。现有结果的方向、缺少论文措辞或未确定最终故事都不构成阻塞。

## 3. 绑定后执行

生成 `ALN35_BINDINGS.json` 和 `ALN35_EXECUTION_PLAN.json`，记录每项比较对应的实际 source unit/hash、复用情况、新任务数、预计耗时依据和选择范围。参考 `plans/workpackages.json` 与 `templates/IMPLEMENTATION_RECEIPT.md`。包中的科学比较卡不是已经注册到服务器的生产任务数。

通过所需的输入时间、配对、独立开发人、概率候选、有限值和恢复检查后，按固定设计运行。检查针对具体风险：不用分数通过线，不重复已经充分验证的工程检查，也不在每项任务前重新询问 go。

## 4. 第一次回报应包含

1. 制作基线与现场 HEAD 的差异；已完成、仍运行、只读重分析、新增任务的区别。
2. `pre` 勘误所影响的精确 ID 与不受影响的依赖。
3. 每个新增比较的完整人/种子/内容/支持覆盖预期及实际绑定。
4. 10-GPU 总量内的真实资源安排；不承诺尚未测量的固定天数。
5. 已经产生的结果和仍竞争的解释；同时给负向、正向与不确定结果。
