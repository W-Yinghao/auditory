> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 路线 B

判定：**NEED_CONTROLS**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | calibrated_main_gain | -0.00167271 [-0.00260096, -0.000745914] | 60 | bits/trial | B_L0_001 |
| R_SUP | calibrated_main_gain | -0.00133677 [-0.00228316, -0.000411545] | 60 | bits/trial | B_SUP_RAND_core_001 |
| R_RAND | calibrated_main_gain | -0.00151634 [-0.00254784, -0.000462401] | 60 | bits/trial | B_SUP_RAND_core_001 |

现象与 estimand：在当前及前一个字面码均为 1 时，历史 run-length 对当前反应是否仍有条件预测增量。

基线解释：强 gap/position 上下文、刺激前和前次反应均使用同试次对照。

剩余替代解释：残余历史、适应、质量和序列混杂不能解释为因果信息传递。

与旧工作区别：估计固定 OOF 条件 CE 增益，不以已有负结果重新选择历史或窗口。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：B:main_gain:previous_response_available；B:post_increment_over_pre:all；B:post_increment_over_previous:previous_response_available；B_SIM_core_001:missing；B_controls_SIM_001:missing；R_SIM:primary_estimate

失败保留：无记录到的实现失败

来源：B_L0_001、B_SUP_RAND_core_001、B_SIM_core_001、B_controls_L0_SUP_001、B_controls_SIM_001
