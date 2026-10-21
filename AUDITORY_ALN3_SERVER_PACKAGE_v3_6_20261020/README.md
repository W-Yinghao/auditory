# ALN3.6 · 三轮收束的第一轮

**主问题：听觉 EEG 中，哪些声音证据可以跨听者／听觉组直接读取，哪些需要个人的时间读出调整？**

这是 `W-Yinghao/auditory` 的继续。用户于 2026-10-20 将目标明确改为三轮内完成研究所需证据。本包以 GitHub `3da8cf5758214c0cf87a1f1c8d67fb84b574000e` 为可核验基准；制作时远端 main 与该提交一致。服务器接包后仍须读取现场状态，不能把快照当作实时队列。

本轮补两个直接实验：FAU 整个目标听觉组排除后的迁移，以及相同表征、支持、query 上的嵌套个人时间读出。私有儿童负责区分当前声音证据、序列历史和个人概率校准。已有 FM／先验／episode／融合结果保留；不继续扩展它们的搜索空间。

## 阅读顺序

1. `SERVER_START_PROMPT.md`：给 server agent 的任务。
2. `SERVER_FULL_DOCUMENT.md`：单文件完整规格。
3. `plans/round1.json`：本轮范围、种子和数量。
4. `docs/03_READOUT_CONTRACT.md`、`docs/04_SERVER_BINDING.md`：读出算法和真实数据接入。

## 本轮工作量

- FAU：2 个工具 × 3 个排除组 × 2 个内容划分 = **12 次唯一 encoder 训练**。5 个原评估人折只是记录切片，共 60 个评估 cell；不得为这 5 个切片重复训练相同模型。
- DTU 既有 pooled 权重：20 个冻结评估 bundle。
- FAU 既有 pooled 权重：20 个冻结评估 bundle，仅作为已有分布背景和个人读出参照。
- 私有 matched AP/APwrong：10 个冻结评估 bundle。兼容的既有 S 可以另作 5 个补充参照。
- 共 **110 个核心评估 bundle，只有 12 次新的 backbone 训练**；不是 110 个新模型。五种读出和控制在 bundle 内拟合。

实际训练去重键还须包含合法 source 人／内容／预处理／代码哈希。若这些不相同，不能假装复用；先解释具体差异，不自动扩大成 60 次训练。

## 本地可执行部分

```bash
python scripts/materialize_plan.py --output /tmp/aln36_round1_plan.json
python scripts/verify_package.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

包内有可运行的 CPU 嵌套读出参考实现、配对效应汇总、计划生成和完整性核对。**原始 EEG、私有 block 绑定、训练权重和 Slurm 接入不在包中；server agent 需按 docs/04 实现新 `aln36` 绑定并做一次端到端工程检查。这里没有执行新训练，也没有宣称新假设已经得到结果。**

只追加新的执行版本。不能覆盖旧输出、改写在跑代码、清空历史 holds 或重启旧全矩阵。聚合运行与排队 GPU 总上限维持 10。个体级派生结果发布沿用用户既有授权。
