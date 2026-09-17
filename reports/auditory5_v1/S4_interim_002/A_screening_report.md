> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 路线 A

判定：**NEED_CONTROLS**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | post_T | 0.0184137 [-0.0231942, 0.0599399] | 55 | cosine_difference | A_L0_core_001 |
| R_SUP | post_T | 0.0418133 [-0.00163692, 0.0889623] | 55 | cosine_difference | A_SUP_RAND_core_001 |
| R_RAND | post_T | 0.023167 [-0.0122139, 0.062219] | 55 | cosine_difference | A_SUP_RAND_core_001 |

现象与 estimand：刺激差值表征的同候选跨时间块匹配是否超过异候选匹配。

基线解释：背景、刺激前、随机投影、配对时序与训练内白化可解释重复性。

剩余替代解释：共享滤波历史、序列位置及一般个体状态仍需重置/平衡敏感性约束。

与旧工作区别：终点是固定表征的候选级重复性，不复用旧波形相关作为临床证据。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：A_SIM_core_001:missing；A_controls_L0_SUP_RAND_001:L0:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:L0:continuous_balanced；A_controls_L0_SUP_RAND_001:L0:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:L0:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:L0:reset_balanced；A_controls_L0_SUP_RAND_001:L0:reset_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_balanced；A_controls_L0_SUP_RAND_001:R_RAND:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_balanced；A_controls_L0_SUP_RAND_001:R_RAND:reset_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_balanced；A_controls_L0_SUP_RAND_001:R_SUP:continuous_unbalanced_on_balanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_balance_minus_unbalanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_balanced；A_controls_L0_SUP_RAND_001:R_SUP:reset_unbalanced_on_balanced；A_controls_SIM_001:missing；R_SIM:primary_estimate；A:frozen_history_position_balance_support

失败保留：无记录到的实现失败

来源：A_L0_core_001、A_SUP_RAND_core_001、A_SIM_core_001、A_controls_L0_SUP_RAND_001、A_controls_SIM_001

固定六格历史×位置平衡支持：55 候选中，满足所有 24 个 half/class/cell 固定配额的候选为 0。
该序列支持限制不是代码失败，不调小配额补成阳性。字面码 2 的 H0 单元几乎结构为空；各半份/位置单元的零计数见 history_position_support.csv。有效的独立 reset 项仍单独保留。
