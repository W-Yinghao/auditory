> 发布副本：用户在本轮验收后明确要求将代码与聚合结果推送到GitHub。文内“未push／不自动发布”描述该授权之前的状态；个体数据、模型及详细日志仍不发布。历史进行中状态以final_002为准。见[发布范围](../PUBLICATION.md)。

# Proposal: inner scope for `auditory_next_v2`

状态：**proposal only；不是执行授权**。当前 v2 仍 `NOT_RUN`。本文件不读取或计算候选 ID，不使用临床标签，也不按临床终点选择 cohort；只解释现有 fold schema 与 v2 文字的适用边界。

## 直接依据

v2 §3.1 的硬条件是：新 N1/N2/N3 优先复用对应既有 inner `all` encoder；每个 inner encoder 不得见该 inner validation 儿童；scaler、PCA、head、calibration 分别在自己的特征坐标和 fit scope 中拟合；最后只合并预测/标量。若缺少合规 inner 特征，§3.1 明确禁止把 outer-trained embedding 冒充完整 nested，允许的降级是 `FIXED_HEAD_OUTER_EVAL` 或范围明确的 `FROZEN_FEATURE_INNER_ONLY`，且不自动重训几十个 inner encoder。

§13.2 又固定 N1/N2/N3 首轮读出为 logistic `C=1.0`、MLP 显式 `lambda=0.001`、seed 11、3 inner folds；该固定值优先于 §4 的候选网格。§3.4 的校准必须只看训练内 OOF；无合规 OOF 才能标 `UNCALIBRATED_FIXED`。这些是新 N 路线约束，不能被旧 D 的临床建模语义替换。

现有 `auditory5/splitting.py`/`job_plan.py` 的 `D_inner_fold_by_group` 是按临床 D 子集建立的三折划分；D 的 encoder policy 明确排除 outer-test 与 D clinical-inner-validation groups，但允许其他 outer-train groups。该结构不是自动生成的 N1/N2/N3 inner split，也不能仅由“特征覆盖全部候选”推断 N 的 scope 已合规。

## 决策建议

仅使用声明为 unseen 的 D-inner validation candidates 做 N calibration，**在限定条件下可作为固定特征/读出诊断，但不能直接称为 N 的完整 nested OOF calibration**。允许采用的最窄表述是：

> 复用带 `encoder_scope_hash` 的 D inner `all` 特征；在其明确未见的验证 groups 上，仅按 EEG/历史输入拟合或评估 N 的固定读出；报告该临床子集 scope、覆盖损失和 `FROZEN_FEATURE_INNER_ONLY`/`FIXED_HEAD_OUTER_EVAL` 状态。

在任何实际采用前，root 需要核对并记录：

1. 对每个 fold，encoder、scaler/PCA、head 和 calibration 的 fit groups；验证 groups 不得进入任何拟合，且 inner encoder 的训练组确实排除这些 groups。
2. N 的 trial/bag 支持是否覆盖该 fold 的 N 候选，而非只满足 D 的临床完整性；不能把 D 的 51/60 子集人数当作 N 的支持人数。
3. N 的 `P_nat/P_bal`、读出族、校准和 `lambda/C` 是否按 §13.2 固定，不能借 D 的临床终点、MUSS 完整性或 D 的 penalty 选择作代理。
4. 所有 inner/outer 特征是否标注 `feature_scope_id`、`encoder_scope_hash`，并能证明测试儿童 EEG、当前标签、未来事件和临床标签没有进入 encoder、scaler、PCA、head 或 calibration。

如果上述 scope 证据不能逐 fold 对账，v2 应采用 §3.1 的固定头 fallback，或把该包标为 `BLOCKED_INPUT`/`FROZEN_FEATURE_INNER_ONLY`；不能为了得到 calibration 而把 D-inner folds 重命名为 N-inner folds，也不能在本轮新增几十个 encoder fits。

## 不可混淆的正则语义

N1/N2/N3 的固定 `lambda=0.001` 是显式平均加权 loss 的新 objective。C2-R 与 E0-R 的修复继续使用各自旧协议的 alpha/C、objective parity 和一次 solver 延长。即使共享输入特征或 numerical code，也不得共享数值语义、网格选择或 fit receipt 的 `objective_id`。

## 结论边界

本 proposal 不决定 D-inner 特征一定可用于新 N calibration；它只决定审查路径：先检查 inner encoder 的真实排除范围和 N 的独立 fit scope，再选择合规复用或固定头 fallback。任何新 N 结果仍必须拥有自己的 trial/候选支持、校准范围、四轴状态和 source hash。v2 未运行，不应生成 N 的科学效应或把该 scope 诊断写成完成。

