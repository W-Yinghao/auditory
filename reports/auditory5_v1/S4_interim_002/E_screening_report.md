> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../../../PUBLICATION.md).

# 路线 E

判定：**IMPLEMENTATION_FAIL**。主表征：E1:puretone_to_bapa。

| mode | statistic | estimate [95% CI] | n candidates | units | run |
|---|---|---|---:|---|---|
| E0_native | linear_calibrated_J_puretone | -0.00193664 [-0.00822001, 0.0036278] | 7 | bits/trial | E0_native_003 |
| E0_native | linear_calibrated_J_bapa | -0.0119 [-0.0173736, -0.00666896] | 7 | bits/trial | E0_native_003 |

现象与 estimand：E0 描述记录内独立时间块的任务可读性；E1 才检验纯音到 bapa 迁移。

基线解释：E0 的 linear 与 MLP32 分族核对完整记录，失败族不在成功子集聚合。

剩余替代解释：任务、布局及来源设备差异仍可能解释迁移；E0 不估计迁移信息瓶颈。

与旧工作区别：MFF 包含混合及未知来源，不能整体称 CI；现有 E1 bapa 16 候选不足 20。

下一有限步骤：完成列出的预设控制与失败复核；只有完整支持的首轮筛查才考虑预设种子复现。独立儿童验证仍未完成。

待完成：无列出的输入缺项

失败保留：E0_native_003

来源：E0_native_003

E0 请求记录 18；具有块支持 16；两族均成功记录 11。
族状态：{"linear": "COMPLETE", "MLP32": "NUMERICAL_FAILURE"}；数值失败 record-head 数：5。
