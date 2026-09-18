> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../../PUBLICATION.md)。

# Auditory v3 execution map

The supplied Markdown design and YAML were read before execution. The execution copy is `configs/auditory_v3_plan.yaml`, SHA256 `d777ac493cdaa223e52fda4b6e743a97dd2cea92945f5d9e73f0facce0f7d2ee`. The reference publication HEAD was `eb24106afe170b323859daa9dda597a85e548bb9`. Neither the original datasets nor historical snapshots were edited. This round does not automatically publish results.

| Role | Run / artifact |
|---|---|
| Source registry | `inspect_001` |
| Authoritative member / fold / quartet support | `support_002` |
| Bounded fit catalog | `plan_001` |
| P0 tested source | `tests_P0_002/source` |
| P0 capability / real result | `capability_P0_001`, `P0_001` |
| N2R tested source | `tests_N2R_002/source` |
| N2R independent development / evaluation | `development_N2R_001`, `capability_N2R_001` |
| N2R real result | `N2R_001` |
| R3 tested source with equivalent deterministic pooling | `tests_R3_005/source` |
| R3 common exposure plans | `exposures_R3_001` |
| R3 successful objective checks | `capability_R3_SUP_002`, `capability_R3_SIM_002`, `capability_R3_MATCH_003` |
| R3 joint capability receipt | `capability_R3_001` |
| R3 selection encoders / probes | `R3_selection_001_task000`–`task014`, `R3_probe_selection_001` |

Run directories reside below `private/auditory_v3`, with corresponding aggregate output under `results/auditory_v3` and reports under `reports/auditory_v3`. Every execution contains frozen source/config/arguments/start receipts, followed by a completion or explicit failure receipt. Exact participant paths, hashes and scope bindings remain private. Aggregate results alone are insufficient to reconstruct the EEG arrays; authorized access to the registered historical exports and original data is required.

All CPU/GPU numerical work, including tests and capability worlds, runs through Slurm. Wrapper scripts are `scripts/auditory_v3_cpu.sbatch` and `scripts/auditory_v3_gpu.sbatch`. GPU execution uses A100 and at most two concurrent tasks. Before submitting a new run, use a fresh run name; occupied run directories are rejected. Capability and real jobs set `AUDITORY_V3_CODE` to the corresponding passing test's immutable `source` directory. Do not point an existing gate at changed code.

The dependency chain is separate for P0, N2R and R3. P0's negative finding does not disable N2R or R3. N2R's three synthetic mechanisms use the exact frozen membership and identity folds, not a uniform replacement population. The 60 evaluation seeds are independent of the three development seeds. All three inner folds are required for every N2R penalty, and pooled inner OOF risk gives equal identity mass. HQQ duplication occurs after shared block standardization, with no later rescaling.

R3's 15 selection encoders exclude validation identities from channel scaling, gradients and all contrastive batches. Probe selection uses only inner-fit and validation rows. All 15 encoders and 60 explicit choices must be audited before the 15 final encoders train from seed11 on all outer-training identities. Final probes retain their complete five-fold denominator. Checkpoint state, exact exposure arrays, initial parameters and source hashes are checked again before inference.

The native PyTorch CUDA adaptive-average-pooling backward rejected strict determinism on the first update. The replacement uses the same floor/ceiling averaging bins, has no parameters or state keys, preserves initialization, and passes native forward/backward equivalence tests at the post and pre lengths. The original three failed synthetic allocations are retained. They continued only after proving the known first-backward failure and matching configuration, generator, objective, initial encoder and exposure hashes; no new seed or architecture was introduced. One accidentally submitted new MATCH allocation was rejected by the budget guard before fitting. The final accounting distinguishes initial model allocations, these continuations, and scheduler execution costs.

The global `fit_events.jsonl` reserves each optimizer/model allocation before execution under a file lock. Failed tests, failed jobs and numerical continuations are not erased. The round ceilings remain3000head optimizer attempts,30formal encoders,3synthetic model allocations,160CPU core-hours including GPU-job CPUs, and16GPU-hours. When scheduler accounting has expired, final resource reporting retains the full requested walltime as an upper bound rather than calling the cost zero.

R3 scoring amendment: `tests_R3_scoring_001` tests6stable-logit contracts with zero fits. `R3_probe_selection_002` rescored all180saved heads from `R3_probe_selection_001` without refitting and is the authoritative selection receipt. The original probability-based receipt is retained because sigmoid rounding produced exact1 at some finite logits. Exact loss is now `logaddexp(0,(1−2y)*logit)/log(2)`, with no clipping. Stable scoring has a separate algorithm hash; encoder, exposure, optimizer and base readout source hashes are unchanged. Subsequent final readout jobs use `--stable-scoring --scoring-test-run tests_R3_scoring_001`. Original probabilities and their first summaries are retained privately alongside logit-based final risks.

Final artifacts: `R3_final_001_task000`–`task014` are the15finalencoders; `R3_001` is their60-headfinalOOFpacket with stable-logit scoring. The common CLI can subsequently aggregate `P0_001`, `N2R_001`, and `R3_001` via `finalize --p0-run P0_001 --n2r-run N2R_001 --r3-run R3_001 --split-run support_002`. Finalization performs no model fitting; it writes the primary-effect table/figure, resource bounds and known-identifier scan. Only its completion receipt establishes that final aggregation succeeded.
