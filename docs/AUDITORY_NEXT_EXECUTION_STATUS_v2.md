> 发布副本：用户在本轮验收后明确要求将代码与聚合结果推送到GitHub。文内“未push／不自动发布”描述该授权之前的状态；个体数据、模型及详细日志仍不发布。历史进行中状态以final_002为准。见[发布范围](../PUBLICATION.md)。

# auditory_next v2 执行状态

**最终更新：本轮限定执行和修订验收已完成。** 当前入口为 [FINAL_STATUS](AUDITORY_NEXT_FINAL_STATUS_v2.md)及[研究决策](AUDITORY_NEXT_RESEARCH_DECISIONS_v2.md)；固定报告为`final_002`，`postflight_002`与`public_audit_002`均PASS，终验作业997203已COMPLETED。本轮模型作业均已结束；数值失败和缺少对照仍按原回执保留，不能理解为全部科学路线完成。

以下内容是执行过程的历史截面，保留供核对；其中“进行中”“等待”“下一步”及中途计数均已由上述最终入口替代，不应据此重提已完成作业。首版final_001不作为最终验收。

## 历史执行记录（已被最终状态替代）

状态：**进行中，尚未完成本轮**。本文件只记录已建立的执行事实，不构成论文结论。B-v1、D-v1 已关闭；E1 未启动，MFF 不能整体称为 CI。N1–N3 模块不读取临床结局，本轮不训练临床预测模型。

## 已冻结并核验

- `S0_001`：90 个旧计划任务；scope/alignment 已核验，1,893 个文件、6,041,318,912 bytes。
- `S1_support_004`：60 条记录、60 个保守身份组、59,202 个事件、44,327 个 accepted 事件，其中 43,895 个具有完整历史。
- A2 支持冻结：`Ω={run3_5_pos0, run3_5_pos1}`，即 preceding run 3–5 的两个预定位置区域，共 49 个合格身份组；>=6 区域未进入最终 Ω。未根据 EEG 结果改 Ω。
- N2 `k=8` 支持组数 57；N1 组数 59；N3 outer-test 总组数 60。已有临床自由文本设备历史线索；逐段设备电源状态和确切同期临床日期仍未知，不能笼统写成全部设备历史未知。声学事件语义仍未知。
- `G0_001`：48 个旧 metric rows 已复现，最大误差不超过 `2.22e-16`；原监督 head 的训练拟合较弱。
- `G0_metadata_002`：57 个 temporal groups、59 个 offline common records、38,480 个同时通过两种 QC 的 trials；1 项 support-insufficient。`selection_isolation=false`，因为复用了 whole-record offline QC。
- `tests_010`：128 tests `PASS`。sklearn objective parity 约 `1.11e-16`；计数器记录了 15 次 logistic、10 次 ridge 函数调用，包含预期拒绝的调用，不能全称为成功拟合。此前 tests_009 暴露 CSV 将机制名称 `null` 当作缺失值的问题，修复后通过，未重拟合真实模型。
- `integration_001`：1 个 logistic fit；首次声明的 inner scope 为 33 个训练组、14 个 validation 组，状态 `PASS`。

## 已完成结果与边界

`A2_core_001` 已完成未校正主分析：4 modes、5 outer folds、60 个 axes、49 个支持组。R_SIM 主结果为 cosine `0.0153893`，区间 `[-0.0305962, 0.0593238]`；pre 为 `0.010635`；post−pre 为 `0.004754`，区间 `[-0.048115, 0.056166]`；common response 为 `0.369722`，区间 `[0.301529, 0.435123]`。R_SUP 是 secondary：post `0.056519`，区间 `[0.015913, 0.098295]`。不得因 R_SUP 数值切换 R_SIM primary。

A2 的20个残差模型均已拟合；原运行最终写入文件重名失败，`A2_residual_recovered_001` 仅从保存的模型与矩阵恢复汇总，新增拟合0。R_SIM 预测项P的cosine重复性为0.21398，区间[0.14961,0.27362]；残差R为0.02865，区间[-0.01880,0.07350]，不替代未校正主终点。合成机制控制待完成，A2总体暂为 `NOT_EVALUABLE`。

`N1_core_001`、`N2_core_001`、`N3_core_001` 的主比较均已完成。N3 的 R_SIM/P_nat、训练 OOF 选族、温度校准的 H−HP 为 -0.05063 bits/trial，区间 [-0.05776,-0.04119]；HB−HBP 为 0.0001004，区间 [-0.001904,0.002187]；H−Hnoise 为 -0.05191。N3 全部600个头（含200个神经头）通过数值门限。负增益不能直接解释为负信息或 EEG 没有信息，须区分读出估计代价。N2 的固定 `k=8` 主线性结果见下；次要240个MLP32全族未解决，不产生次要测试结果。

`G0_readouts_001` 全部1,158个线性拟合完成。57个同儿童时间测试组中，SIM温度校准bacc=0.51572、CE=0.99938 bits；59个共同预处理比较组中，因果与离线处理bacc分别0.52791、0.52491，未显示明显改善。

`C2S_core_001` 全部390个线性拟合完成：60组、44,283共同试次，19维重建最大误差1.14e-13；温度校准跨组均值增益-0.000238 bits/trial，中线增益0.000194，区间均跨0。MLP空间敏感性仍为预算未运行，不能据此称整个C2-R修复完成。

E0-R 暴露的 input-scope mismatch 已修复：直接读取冻结的旧 OOF/model/split，不重新生成有排序平局的分组。`E0_inputs_002` 的 64 个记录×外折单元通过，覆盖预定 1,024 个神经读出；`C2R_inputs_001` 的 5 个外折单元也通过，覆盖预定 560 个神经读出。两者均未在输入检查中拟合模型；C2R正式GPU作业正在运行。E0与C2R没有数据依赖，E0调度依赖现改为synthetic终态，以便接替空出的并发名额；最终汇总显式等待三项作业全部终态。

N2 已完成固定 k=8 主线性矩阵及10次测试重组。480 个 logistic 拟合数值完成；240 个次要 MLP32 在统一2000步后仍未过稳定性门限，整族不产生测试结果，也不追加第三次优化。R_SIM 主均值→均值+方差增益为 -0.0014935 bits/bag，95% CI [-0.0030173,-0.0002580]；10次重组平均为 -0.0015237，CI [-0.0031560,-0.0001977]。不含EEG的 H_BAG 已有 bacc=0.982883、CE=0.131678；当前结果不支持把高准确率归于EEG分布或据此开发集合网络。

A40队列满载后，两个零拟合 P100 兼容性探针纳入预算。首个探针额外开启deterministic-only模式却未设置CuBLAS workspace，因探针配置失败；第二个按现有读出运行方式检查float64矩阵乘与梯度，通过，误差为0。synthetic/C2R随后在P100启动。用户新指示后续不使用P100：尚未启动的E0已转至A100，站点及GPU脚本默认也改为A100；优先A100/L40S/H100，最低V100或RTX6000PRO。已运行的synthetic/C2R保留本次进度与硬预算。始终最多2 GPU并发；实际调度覆盖在私有controller ledger登记。seed23不启动。

`synthetic_001`已在1:59:52内正常结束，科研回执NUMERICAL_INCOMPLETE：300个A2 ridge和1620个分类头，150个分类头数值未解决，90个分类世界不可评价。A2 null固定非零W残差100/100呈重复性，而未校正Delta为5/100；N2强方差恢复30/30、均值充分/时间漂移各0/30。N1 background-key及N3关键正/零信息世界全部保留未知。完整解释见`AUDITORY_NEXT_SYNTHETIC_INTERPRETATION_v2.md`；超时恢复工具未调用。E0已接替并发名额在A100运行，C2R仍在原P100作业中。

N1 已完成 760 个头、含 280 个神经头，所有表示/分布/模型族均通过数值门限。R_SIM/P_nat/MLP32/temperature 的 HP−HPB = -0.0249567 bits/trial，CI [-0.0279888,-0.0221692]；HB−HPB = -0.0241528；HPP−HPB = -0.0119874。三项 donor 诊断已输出，不能以其中某项替换负的主比较。N1/N2/N3 均未满足预定主门槛，seed23 复核不启动，见 `AUDITORY_NEXT_SEED_DECISION_v2.md`。

## Inner scope 限制

零重拟合补充 `metrics_integration_002` 已验证 N3 所有模型视图与校准版本使用同一测试池：run_2 为 7,054/1,666 两类试次，run_3_5 为 10,547/5,260；每层 60 个候选身份组均各有两类。`fit_accounting_integration_001` 对已完成包核出 2,169 次明确完成的头拟合，历史测试另有 161 次函数调用，A2 60 个变换拟合另列；此为运行中截面，非最终数量。

`metrics_integration_004`已完成全六来源的零拟合补充；`reporting_tests_006`为19项PASS，`reporting_integration_003`含5个包的图及N3五折选族计数。N3的R_SIM主H五折均选MLP，而HP/HB/HBP/Hnoise均选logistic，须解释模型容量差异。最终资源核算、完整性验收和独立发布扫描尚未完成。最终流水线996890尚未验收，不得据此写round complete。接口说明见`AUDITORY_NEXT_REPRODUCTION_v2.md`。

`reporting_integration_004`已成功读取合成终态与机制解释，汇总接口无错误。最终流水线996890已解除hold，但仍通过afterany依赖等待C2R/E0终态；排队不等于完成验收。

后续终态更新：`C2R_core_001`已完成，Slurm 996791为COMPLETED（2:14:36）；560个神经头全部在统一2000步下通过稳定性门限，325个线性头完成。60个身份组的R_SIM/MLP32/calibrated主T_C=-0.000333856 bits/trial，CI[-0.001046687,0.000300950]；重复列margin=-0.000329163、容量margin=-0.000340898，区间均跨0。主矩阵数值修复成功，未触发联合优势推进条件；完整L0/R_SUP平行修复和继承raw-isolation控制仍缺失。该终态替代上文C2R运行中描述，E0仍在A100运行。`reporting_tests_007`为19项PASS（零拟合）；报告表增加分析对象与校准列，避免混淆同值不同定义的指标。

现有三个 D-inner 验证集合合计覆盖每个 outer-train 的 40–41/48 个组，另有 7–8 个组没有已声明的 inner 验证位置。新 N 路线只使用实际已声明、且由对应 encoder 排除的验证组产生校准 OOF；其余合格 outer-train 组可以参与头部训练，但不能被补写成 unseen validation。该方案明确标注为部分覆盖的、编码器隔离的校准 OOF，不能称为全队列完整嵌套验证。

## 预算与保密边界

`plan_004` 已预留 7,778 fits：2,934 neural fits、0 个新 encoder、600 个 synthetic worlds；其中 300 个非神经拟合名额用于包含 ridge 的测试核算。各 plan 是同一轮的修订，不累加其预留数量。上限为 32 GPU·hours、256 CPU·hours，最多并发 2 GPU / 4 CPU。合成输入检查通过，合成拟合预算为2 GPU小时，排在N2之后。历史sacct服务不可用；实际用量将结合scontrol与保守请求上界核算，缺失不记0。

所有新的 private 输出目录为 0700、文件为 0600；公共输出仅可含聚合结果。逐人/逐 trial 数据、clinical records、paths、models、weights 和详细日志不得发布。没有自动 Git commit/push。

## 下一步核对清单

在 round completion 前，逐包留下回执、scope/hash、支持、控制、失败和资源状态：

1. C2-R、E0-R：等待已提交的唯一修复方案到达终态，核对完整族门限，不从成功子集生成主结果。
2. 合成审计已到终态：最终报告保留固定100/30世界分母及未知世界，不把失败世界改写为阴性。
3. 完整性与预算：复核旧文件哈希、private权限、实际拟合及资源上界，未知不填0。
4. 最终交付：汇总已完成的G0/A2/C2-S/N1/N2/N3和剩余终态，完成主报告、T01–T26覆盖与聚合产物扫描。不得重复拟合已完成矩阵。

随后才可生成完整聚合报告；当前不应称为 v2 round complete，也不应把活动作业、partial support、未解决的 N2 MLP32 或待完成 controls 写成最终 verdict。
