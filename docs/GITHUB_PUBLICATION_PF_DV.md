# PF + DV 与非数据积压发布回执（2026-09-27）

研究者指示"全除数据集外推送"。本次发布包括：
- 正面主张与查否实验轮（PF、PF2）；
- 发散第二轮（DV）；
- 项目总结与第二轮发散文档；
- 此前各次精选发布没有选入、但不属于参与者数据的全部积压文件。

- 提交：`ab9c340807aff8f1be7e2a173a61d565a8345101`（`main`），上一提交 `25df3e2`；`git ls-remote` 读回与本地 HEAD 一致，检出目录干净
- 公开快照：https://github.com/W-Yinghao/auditory/commit/ab9c340807aff8f1be7e2a173a61d565a8345101
- 本地检出：`/home/infres/yinwang/auditory_github`；科研工作区不变
- 审计材料：`private/github_publish_012/`（清点、候选清单、扣留清单及理由、构建与检查脚本、回执）

| Slurm | 作业 | 结果 |
|---|---|---|
| 1010890 | 清点：工作区（`private/` 除外）与检出逐文件比对，并做内容扫描 | 2,665 个新文件，196 个与检出不同 |
| 1010927 | 按规则筛选 | 848 个候选，1,819 个扣留 |
| 1010929 | 构建：原样复制；复核 011 的去标识表；编译与语法检查 | 通过（`.gitignore` 问题见下） |
| 1010933 | 对 git 实际暂存的内容做最终检查 | PASS |

## 内容（848 个文件，15.4 MB；新增 846，更新 2）

**今天的工作**
- 代码：`auditory_pf/`（15）、`auditory_dv/`（10）、`tests/auditory_{pf,dv}/`、`configs/auditory_{pf_v1,pf_v2,dv_v1}.yaml`、`slurm/auditory_{pf,dv}_*.sbatch`（8）
- 文档：`docs/auditory_pf/`（冻结协议、附录 A1、作业台账、结果、PF2 协议与结果）、`docs/auditory_dv/`（冻结协议、结果）、`docs/PROJECT_OVERALL_SUMMARY_20260927.md`、`docs/DIVERGENCE_ROUND2_20260927.md`、顶层计划 `发散_最终版_正面主张与查否实验.md`
- 结果：`results/auditory_pf/`（16）与 `results/auditory_dv/`（7）的聚合汇总；其中 `records` 字段均为计数
- 勘误（更新 2 个已发布文件）：`docs/DATASET_KNOWLEDGE.md`、`docs/auditory_gx/GX_ROUND2_RESULTS.md`。GX 第二轮"事件表示不携带年龄"的结论撤回：训练儿童与测试儿童的嵌入来自不同网络，两者不可比。

**以前没选入的积压**
- `reports/auditory_next_v2/` 的中间报告与图（230），`results/auditory_next_v2/` 的聚合结果、测试与进度回执（283）
- `reports/auditory_v21/figures_001`（8），ST1 报告图 `figures/auditory_st/`（26）
- Phase 1–3 的非参与者文件（210）：代码快照、配置、校验和、完成计数、聚合汇总
- Phase 1–3 汇总图（11）；`manifests/` 的两个计数表
- 两份以前没推送的回执：`GITHUB_PUBLICATION_FUNCTIONAL_RETRAIN.md`、`GITHUB_PUBLICATION_ST1_GX.md`
- 研究范围计划 `AUDITORY_RESEARCH_SCOPE_AND_FIVE_APPROACHES_v1_20260920.md`
- 原始重启包 `EEG_project_restart_EN_20260916_v1.zip`：24 个成员与已发布的 `server_restart_en_v1/` 逐字节相同，不增加任何新信息

**检出中与源文件不同、保持已发布版本的 194 个文件**
- 126 个带发布说明的文档副本、`README.md`、`.gitignore`、1 个去掉硬编码记录号的 Slurm 脚本：源文件自上次发布以来没有变化；
- 65 个 011 发布的去标识逐儿童表：从当前源重新派生后逐字节一致。

## 扣留（1,819 个路径，视为数据集）

| 理由 | 路径数 |
|---|---|
| 路径本身带标识（`M####` 容器目录、`file_<id>` 图、带 id 的文件名） | 1,568 |
| 内容扫描命中：已知标识 123、不透明 id 149、`M####` 容器号 82、32 位十六进制 id 70、已知姓名 10、逐记录列/键 197（有重叠） | 239 |
| 按内容判断：逐记录波形图（其中一张把记录 id 画在图像像素里，文本扫描查不到）、单记录代表性 epoch、年龄 × 佩戴时长的逐儿童散点图（3 张）、容器身份图与 EEG 二进制哈希表、身份探针摘要、带一行数据的私有模板 | 10 |
| 超过 50 MB | 2 |

另外，`private/` 下的全部内容都留在服务器上，包括：
- 原始与处理后的 EEG、事件张量、折与模型；
- PF/DV 的逐儿童表，其中有 A1 的逐人年龄预测；
- 身份键、临床行、日志。

## 检查

- 849 个暂存路径（848 个文件加 `.gitignore`）与候选清单完全一致；没有 `private/` 或扣留路径被暂存。
- 扫描范围：321 个已知姓名串、4,851 个已知标识，以及不透明 id、32 位十六进制 id、`M####`、源数据根路径、站点以外的绝对路径、2026 年以前的精确日期、邮箱与凭据模式。结果为零命中。唯一的例外是一个测试夹具日期，它与早已发布的 `tests/test_phase2.py` 逐字节相同。
- 116 个 Python 文件编译通过，15 个 Slurm 脚本 `bash -n` 通过。
- `.gitignore` 仍是 fail-closed：848 个候选全部放行；1,819 个扣留路径即使被放进检出目录也仍然被忽略。

**我在构建中的一个错误**：沿用 011 的 `.gitignore` 生成逻辑时，去重是对整个文件做的。结果，已有的放行行被后面追加的 `/<dir>/*` 覆盖，546 个候选仍被忽略。提交前已发现：从 `HEAD:.gitignore` 重写，追加 1,397 行有序放行块，去重只在块内进行。记录见 `private/github_publish_012/gitignore_fix.json`。

## 说明

- 积压中的中间报告是原样副本。文中"未推送""仅服务器""排队中"等表述，描述的是写作时的状态；指向 `private/` 的链接在 GitHub 上不可用。
- 结论以各轮的最终文档为准，要点如下：
  - **PF**：只有 H1 经晚成分模板读出成立（0.707；只用年龄是 0.696）；PF2 复现较弱（0.637）；学习型模型接近零；修正后的 H2 没有复现。
  - **DV**：只在 HA/BDF 系统里，事件锁定嵌入比持续谱多携带年龄信息（MAE 24.4 对 33.1，持续谱对照不稳）；MFF 不复现。换参考不改变 AUC，REST/CSD 能提高信度。CI 客观测量能拿到，但与读出无关。方向 F 的代码已备，未运行，等通道筛选边界的决定。
- 只发布了这一显式快照；这次许可不延伸到将来的参与者数据上传。
