# ST1 + GX 发布回执（2026-09-22）

研究者明确指示推送。本次发布做法一（ST1，预注册线性读出）与 GX 探索（五轮 GPU 路线、负结果地图、数据集知识汇总）。

- 提交：`25df3e2eb161e6ea4db1822d15bb2941b0599fe1`（`main`），远端引用已读回一致
- 公开快照：https://github.com/W-Yinghao/auditory/commit/25df3e2eb161e6ea4db1822d15bb2941b0599fe1
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变
- 构建与检查：Slurm 1003854，`private/github_publish_011/`（候选清单、扣留清单、构建脚本、回执）

## 内容（360 个文件）

- 代码：`auditory_st/`（9）、`auditory_gx/`（16：runtime、stage、data、models、train、routes、occlusion、summarize、round2–5、cli）、`tests/auditory_{st,gx}/`、`configs/auditory_{st,gx}_v1*.yaml`、`slurm/auditory_{st,gx}_*.sbatch`
- 文档：`docs/auditory_st/`（预注册冻结稿、结果）、`docs/auditory_gx/`（路线计划、假设、分析、结果表、五轮发散与结果、负结果地图）、`docs/DATASET_KNOWLEDGE.md`
- 结果：`results/auditory_gx/`、`results/auditory_st/` 的聚合汇总（JSON/CSV，237 个原样文件）与 65 个去标识的逐儿童指标表（删除年龄、设备时长、阈值列）

## 扣留

- 38 个含记录标识或逐记录临床值的表（逐记录 AUC、漂移、分半、ST1 记录支持表与逐记录读出摘要）
- `private/auditory_gx/`：事件锁定 EEG 张量、折模型、逐试次 logit、记录身份、临床覆盖表；`private/auditory_st/`：事件表、特征、逐记录读出
- 检查：185 个已知姓名串、源路径、32 位十六进制 id、凭据与邮箱模式在全部 360 个文件中零命中；16 个 Python 文件编译通过，7 个 Slurm 脚本语法通过

## 结论摘要

跨儿童单试次偏差读出 HA 0.556（随儿童数仍在升），δ/θ、刺激锁定、0.12–0.32 s、外侧额颞＋额中央；不是眼动/惊跳；不携带年龄；范式特异；数据受限而非模型受限。早（0.16 s）与晚（0.28 s）是两个成分，晚成分权重与助听器佩戴时长相关（控制月龄 0.27），NH 以早成分为主。记忆痕迹只在组水平成立；EEG 对量表无增量（五轮）；听力状态分类待样本。

只发布了这一显式快照；本次许可不延伸到未来的参与者数据上传。
