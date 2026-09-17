> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 路线 C

判定：**IMPLEMENTATION_FAIL**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | T_C_linear_calibrated | -0.000196746 [-0.000922888, 0.000208532] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| L0 | T_C_linear_raw | -9.78564e-05 [-0.00136014, 0.00066845] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_RAND | T_C_linear_calibrated | 9.349e-05 [-0.000605844, 0.000602018] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_RAND | T_C_linear_raw | -0.000473747 [-0.00147779, 0.000307219] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_SUP | T_C_linear_calibrated | -0.00805367 [-0.0113482, -0.00605344] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |
| R_SUP | T_C_linear_raw | -0.00933457 [-0.0129051, -0.00741267] | 60 | bits/trial | C_linear_L0_SUP_RAND_002 |

现象与 estimand：独立预处理及编码的左右分支联合读出是否优于任一单分支。

基线解释：LL/RR、扩展单分支容量及温度校准约束模型容量解释。

剩余替代解释：固定头置零与替换是分布外诊断；预测互补性不等于 PID synergy。

与旧工作区别：左右原始输入隔离，不能从全头表示事后切片宣称独立视角。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：C_SIM_full_001:missing；C_linear_SIM_001:missing；C_linear_SIM_001:summary.json；R_SIM:primary_estimate

失败保留：C_L0_003；C_SUP_full_001

来源：C_L0_003、C_SIM_full_001、C_SUP_full_001、C_linear_L0_SUP_RAND_002、C_linear_SIM_001
