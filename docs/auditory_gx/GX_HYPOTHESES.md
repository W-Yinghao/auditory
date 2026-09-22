# GX 假设清单（写于结果产生之前；结果出来后逐条判定"支持／不支持／不能判断"）

围绕：儿童、纯音、音节、音高偏差、CI／HA、年龄、听力与经验。判定依据是效应量与 seed 间一致性，不设先验阈值。

| 编号 | 假设 | 检验路线 | 判定所用量 |
|---|---|---|---|
| H1 | 声音条件（标准／偏差）的可读形态在儿童间**不共享**：共享网络跨儿童≈机会水平，而逐儿童或儿童适配网络在同一儿童的独立时间块上清楚高于机会 | GX1 shared vs per_child vs child_spatial | 儿童均值 AUC、J bits；三者的差距 |
| H1b | 儿童间差异主要在**空间**形态：共享时间滤波＋逐儿童空间滤波 ≈ 逐儿童完整模型；把逐儿童空间滤波换成均值滤波后性能回落 | GX1 child_spatial vs child_spatial_meanfilter vs per_child | 同上 |
| H1c | 少量目标儿童数据即可把共享网络适配到该儿童（few-shot） | GX1 adapt_zero_shot vs adapt_finetuned vs per_child | 同上 |
| H2 | **年龄条件化**（FiLM）改善跨儿童读出；打乱年龄后改善消失 | GX1 film_age vs shared vs film_age_shuffled（有年龄的儿童） | AUC/J 差 |
| H3 | 连续 EEG 的掩码重建表示携带**年龄**信息（可与 D2 谱特征岭回归比较）、**任务字面**信息（纯音 vs bapa）、**来源字面**信息（CI/CIHA vs 未知） | GX2 探测 | MAE vs 均值基线；AUC |
| H3b | 冻结的自监督编码器对事件锁定 epoch 的跨儿童声音条件读出优于随机初始化编码器 | GX2 event probe | AUC |
| H3c | 自监督预训练改善年龄回归的微调（相对从零训练） | GX3 pretrained vs scratch | MAE |
| H4 | 儿童内**纯音→音节**（及反向）迁移高于机会，但低于同任务；共享主干多任务网不劣于单任务网 | GX4 | AUC |
| H5 | **音高偏差方向**（高 vs 低偏差）在儿童内可读；三类读出跨儿童≈机会 | GX1 on hdev/ldev lane（3 类） | auc_pitch_direction、宏 AUC |
| H5b | 两名双模儿童：CI 单独 vs CI+HA、安静 vs 噪声条件下的记录内可读性与跨条件迁移不同 | GX5 | 逐记录 AUC 与迁移矩阵 |
| H6 | 记录内可读性随时间变化（前三分之一 vs 后三分之一）；同一儿童跨记录（同日／跨日）迁移低于记录内块间迁移 | GX6 | 段 AUC 均值；within vs across |
| H7 | 儿童内可读性与年龄、HA 使用时长、听阈、量表相关（探索） | GX7 | Spearman，年龄调整 |

补充问题（发散阶段再展开）：可读性个体差异与背景表示（GX2 嵌入）的关系；HA 序列高度可预测（历史 AUC 0.84）是否影响读出；MFF 纯音 vs bapa 车道在儿童内的可读性是否不同。
