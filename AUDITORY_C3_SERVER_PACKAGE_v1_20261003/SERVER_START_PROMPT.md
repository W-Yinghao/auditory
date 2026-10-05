# 服务器启动文本（直接交给代理）

以 `AUDITORY_C3_SERVER_PACKAGE_v1_20261003` 为完整研究依据；不叠加执行 V2/V3/V4 的旧主张与判据，但沿用 V4 的统计纪律与登记格式。私有证据基准为 `dfb154f`；先记录服务器当前 SHA 与差异，不覆盖旧报告。

第一步只做 P0 与 P1：
1. 下载 FAU/TUD 三组与 Federici；向 DTU 作者发出原始音频申请（D1），不阻塞。
2. 为每个来源写回执（02 的 schema）；三联集必须核对音频–EEG 对齐延迟、HDF5 中的音频辅助通道（剔除）、`eeg`/`eeg_ica` 分支、逐人行为文件是否在包内；Federici 核对预处理带宽（D2）。
3. 提取 Whisper（多语言）与 wav2vec2 逐层表示，训练侧 PCA k=5，重采样到 EEG 采样率，缓存并写 manifest。
4. 运行 `tests/` 与 `reference/synthetic_checks.py`；把生产估计器（Ince gcmi）与参考实现在合成数据上对齐到 1e-6 比特；接入 I_ccs 参考代码并通过其发表示例，否则 PID 层标 `TECHNICALLY_UNEVALUABLE`。
5. 在三联集 TH 组随机一半参与者上按 I(T;L|Ac) 选定语言层，然后冻结；写 `config/measurement_spec.json` 的 `frozen: true` 并记 SHA。

G1 之前不做任何真实组比较；G2（阳性对照）之前不查看任何私有分组结果。主张的主判据是 MI、CMI、TMIF（不依赖 PID 定义）；PID 只做解释层，且要求 I_ccs 与 MMI 方向一致。所有信息量只在偏差校正后作组间或条件间比较；每组分别校正；绝对比特数不进摘要。

私有端只复用 GX/PF 缓存与年龄模型：不训编码器、不训 SIR/MUSS 头、不恢复未知任务、不按结果改分组或窗、不在看到公开结果后改历史变量定义。私有逐儿童量留在 `private/`，不推送公开仓库。

结果阴性不触发新模型；技术错误允许修正但必须留痕。最终分别报告：事实、有限模型推论、开放假设、不能判断的内容。
