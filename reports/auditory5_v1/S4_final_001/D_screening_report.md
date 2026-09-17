> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 路线 D

判定：**NEGATIVE_SCREEN**。主表征：R_SIM。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| L0 | D2_minus_D3 | -0.32886 [-0.590976, -0.0991506] | 51 | MUSS_source_points | D_L0_core_001 |
| R_SUP | D2_minus_D3 | 0 [0, 0] | 51 | MUSS_source_points | D_SUP_core_001 |
| R_SIM | D2_minus_D3 | 0.10873 [-0.142199, 0.387963] | 51 | MUSS_source_points | D_SIM_core_001 |

现象与 estimand：刺激固定线性头的 null 空间是否在临床协变量及 visible 之外降低 MUSS 源分 MAE。

基线解释：临床单独、完整特征、刺激前、随机投影与试次数/QC 敏感性保持原终点。

剩余替代解释：固定头不变性只说明该头几何；新 null 读出可能恢复刺激信息。

与旧工作区别：outer 和 inner encoder 均独立拟合；不以旧临床阴性结果后的新终点替换主 MAE。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：无记录到的实现失败

来源：D_L0_core_001、D_SUP_core_001、D_SIM_core_001、D_controls_L0_SUP_001、D_controls_SIM_001
