> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# F-series 阶段一执行记录

所有正式数据资格统计、文档重读、哈希与最终核验通过 Slurm CPU 作业完成。0 个临床模型、0 个新 EEG 特征、0 个 GPU 作业。既有临床行级表和来源被读取，不打开 EEG 数组作新的数值分析。

| 作业 | 工作 | 状态/权威版本 |
|---|---|---|
| 999252 | 两份原始 DOCX 定向重读、词项计数 | 完成；解释句由 002 更正，原输出保留 |
| 999256 | 人工审阅后的量表定义确认 | 完成；document_evidence_002 |
| 999262 | CI/MFF 第一轮资格脚本 | 辅助函数错误；原目录归档为 ci_qualification_001_failed_999262 |
| 999264 | CI/MFF 重试 | 已占用目录阻止运行 |
| 999270 | CI/MFF 修订入口 | 缩进语法失败，无有效新结果 |
| 999272 | CI/MFF 正式资格统计 | 完成；ci_qualification_001 |
| 999283 | CI 重复身份计数/数值稳定性、字面最大值说明 | 完成；同目录两个命名补充 JSON，原 summary 保留 |
| 999263、999271、999279 | HA 脚本语法检查 | 检查回执留存；语法通过不保证运行变量正确 |
| 999276 | HA 首次资格统计 | M/MAP 变量拼写导致失败，ha_qualification_001 保留 |
| 999281 | HA 修复后新运行 | 完成；ha_qualification_002 |
| 999289 | HA 计数与输出检查 | 完成；validation_ok |
| 999293 | 父任务交叉计数及路线/终点汇总 | qualification_final_001，以完成回执为准 |
| 999297 | 首次交付核验 | 数值对账/标识符检查通过；Slurm 新建的核验日志权限为 0644，权限项失败，父目录仍为 0700 |

后继 `verification_002` 使用预先创建的 0600 日志，修正调度器在进程 umask 生效前创建 stdout 文件的问题；原核验失败回执保留。未改动科学统计。最终以 `results/auditory_fseries/verification_002/verification.json` 为验收依据。

## 文档与来源修订

旧文档摘要遗漏问卷定义；重新读取的 document_evidence_001 找到了相关文字，但脚本中预置的解释句错误地否认版本证据。002 明确更正解释并保存量表定义，词项计数和旧文件未改动。HA 临床组别按原表合并单元格处理，不能把空白 NH 行算入 HA；身份沿用候选姓名规则，不把后缀当成新儿童。CI 的 8 个重复终点序列只涉及 2 个身份组；初版“declared source max”文字由命名补充明确为字面值计数，不是确证天花板。

HA 四个登记工作簿的表头/备注存入 private 供源级核对；最终人口统计沿用主临床表，未把扩展/重复表另计为新样本。CI 的原始 `Date of Assessment` 列只是日期线索，旧代码 `clinical_date` 别名不升级其临床含义。

## 执行偏离与资源解释

CI 辅助代理在调试时误在登录节点做过一次 Python 编译和一次 CSV 检查，违反“所有 CPU 任务经 Slurm”的执行要求；已记录，正式结果、成功编译、导入、哈希和统计随后经 Slurm 完成。不能声称此次每一条调试命令都符合调度要求。这两次本地辅助操作的耗时未测量，不计为零，也不混入可核对的 Slurm 申请上界。没有在本地拟合模型或读取 EEG 波形。

阶段一 CPU 申请预算为 8 core·h、GPU 为 0。最终核验采用每个作业的完整申请资源作为保守上界，包含失败和核验本身；已过期的调度记录需按保留的提交证据记账，不能当作零消耗。精确实际 CPU 消耗没有由完整 accounting 数据支持。未触碰无关的 994815 作业。

逐行证据、原始路径、日期、姓名和详细错误留在 `private/auditory_fseries/`。汇总不构成参与者数据发布。科研资格不足与软件失败分别记录；当前没有待运行的临床模型矩阵。
