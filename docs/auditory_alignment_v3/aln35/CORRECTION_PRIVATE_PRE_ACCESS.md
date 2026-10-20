# SCI35-C01：native private local pre 访问勘误

Slurm CPU 1047290：实际生产 batcher 与原 keep-mask 在真实 epoch 上核查通过。local/旧 E_PUBLIC_TRANSFER 输入为原 epoch [50,200)，pre 请求 [0,50)，交集 0；保留样本数为 0，实际输入被全部置零。FM 对照保留 50 个 pre 样本。

现有受影响记录数：{'private_current_time_v1': 8, 'private_current_time_v2': 60}。v2 的合法 v1 复用保持其来源，不增加独立观测。逐 unit/seed/fold、原值引用、哈希及受影响路径见 `results/auditory_alignment_v3/aln35/science/run_1047290/correction_manifest.json`。

更正解释标签为 `all_zero_input_control_no_pre_access`，`valid_for_pre_event_inference=false`；包括 windows.pre 全指标与 TG 任一端为 pre 的 7 个 cell，两种校准均在内。

旧源代码、计划、unit、缓存及原统计未修改。三个后刺激窗、full 后刺激、个人适配、full 发育端点、FM 真实 pre、公开科学及新 prior 科学均不在本次勘误内。全零输入产生的排序波动不是刺激前生理信息。
