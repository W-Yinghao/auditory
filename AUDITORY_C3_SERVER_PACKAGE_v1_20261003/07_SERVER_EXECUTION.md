# 07 · 服务器执行

## 7.1 阶段与门槛

| 阶段 | 工作 | 门槛（进入下一阶段的条件） | 不依赖 |
| --- | --- | --- | --- |
| P0 接入与特征（第 1–2 周） | 下载三联集与 Federici；发出 DTU 音频申请（D1）；核对音频–EEG 对齐、辅助通道、行为文件；提取 Whisper/wav2vec2 逐层表示并缓存（含模型版本、层号、PCA k、采样率、SHA）；私有只核对缓存可用性 | **G0**：每个来源一份回执；三联集状态 ≥ `STIMULUS_FEATURES_CACHED`；Federici 带宽核对完成（D2） | 任何阳性结果；医生回复 |
| P1 估计器验证（第 2–3 周） | `tests/` 全过；`reference/synthetic_checks.py` 的 S1–S8 复现；生产估计器（Ince gcmi）与参考实现在合成数据上差异 < 1e-6 比特；接入 I_ccs 参考代码并通过其发表示例；语言层在 TH 一半参与者上选定 | **G1**：合成核对表齐全；I_ccs 核对通过或 PID 层标 `TECHNICALLY_UNEVALUABLE`；`config/measurement_spec.json` 置 `frozen: true` 并记 SHA | 任何真实组比较 |
| P2 阳性对照（第 3–4 周） | 04 §4.1 的三项复现 | **G2**：三项通过条件全部满足；差异有解释 | — |
| P3 主分析（第 4–6 周） | 公开 H2/H3/H7 与私有 H4/H5/H6 按冻结规格一次性运行；两种 PID 度量并排；代理分布齐全 | **G3**：登记表每行有状态、估计、区间、代理均值 | 不以公开结果决定私有是否运行 |
| P4 整合（第 6–8 周） | 按 01 的形态判断定标题；图 6 进正文；复现包 | **G4**：度量、偏差、披露齐全 | — |

G2 不通过时只能修估计器或对齐，不能修改主张以迎合复现失败。

## 7.2 目录与登记

```
c3/
  receipts/            每来源一份 DATA_RECEIPT（02 的 schema）
  features/            语音模型层特征缓存（只读，带 manifest）
  synthetic/           合成核对输出（checks_c3.json、偏差曲线、I_ccs 核对）
  public/<source>/     每参与者每量：estimate, bias_corrected, surrogate_mean, n_sur, window, roi, path
  private/             逐儿童量、身份键、访视日期；不推送公开仓库
  registry/analysis_registry.tsv
  reports/             REPRODUCTION_REPORT.md、PUBLIC_RESULTS.md、PRIVATE_RESULTS.md、CLAIM_EVIDENCE_TABLE.md、RESOURCE_LEDGER.json
```

`analysis_registry.tsv` 每行一个预注册比较：`claim_id, family, source, quantity, comparison, status, estimate, ci_low, ci_high, surrogate_mean, n_sur, n_participants, frozen_sha, notes`。状态只能取 00 的状态码。

## 7.3 计算规则

- 语音模型特征提取用 GPU 一次性完成并缓存；之后全部 CPU（GCMI、PID、岭、混合模型）。
- 代理次数 ≥ 200；每任务记账；失败单元保留，不覆盖，不静默跳过。
- 不训练任何 EEG 编码器；不微调语音模型。
- 全部经既有 Slurm 规则；私有逐儿童产物留在 `private/`。
- 资源上界在 P0 之后按真实任务计数给出；不在不知道文件支持时估计总拟合数。

## 7.4 结果写法（硬规则）

- 数值格式："偏差校正后 X 比特（代理均值 Y，n_sur=200）"；摘要中不出现绝对比特数。
- 组差一律双侧区间；"相近"只在预设等效界内且区间足够窄时写。
- PID 项只在 I_ccs 与 MMI 方向一致时进入主张；否则写"度量依赖"。
- 不合并队列 n；不把不同任务的窗称为同一发生器；不从所有终点里挑最小 p。

## 7.5 不运行清单

新模型或微调；在 CI/HA 组上重选语言层；按结果调 k、滞后窗或代理方案；未经代理校正的任何数值进报告；私有量表预测；未知任务语义恢复；声调分类；HA–CI 因果比较；SparrKULee / Southampton；在 G2 之前查看任何私有分组结果；为维持"注册外观"拒绝修正已确认的技术错误。
