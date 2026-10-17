# ALN3.4 public auditory prior: execution status

Updated 2026-10-17 18:10 CEST, after actual production launch. This is an execution report; no production transfer benefit is claimed yet.

At18:09, **4/1,154 new production units** are complete, all donor groups. Four workers1044083/1044089/1044091/1044101 run under keeper1044079. The official analysis also includes30 reused private references: a count of31completed in its earlier16:55 snapshot meant1new donor+30references, not31new prior experiments. Current donor trajectories are available in `private/auditory_alignment_v3/aln34/prior_diagnostics/`; the first blank plot caused by reading the wrong validation nesting is retained and superseded by corrected1044240/1044258 outputs. All members, including unfavorable curves, are retained. Best source-development cross-entropy is neither a target effect nor a reason to gate unrelated lanes.

All six requested prerequisites are completed: FIXC implementation and affected regression tests, eligible-window rich PCA/sigma refit, production core/rich manifests, the M12 GPU probe script, its successful GPU execution, and the frozen M13 execution record.

| Item | Evidence |
|---|---|
| FIXC regression | 1043898: 418 passed and one obsolete assertion failed; after correction, affected suite1043916:42 passed. Historical failed logs retained. |
| Core/refit/rich build | 1043917 completed at11:31:28. Rich basis uses1,899,000 eligible windows; pass-1 recomputed0. Original rich cache retained. |
| Core manifest | b751976b9238590026f26a6fbe6c84177b69802ef9e55e687425af210b627426 |
| Public core manifest | 3ffa6e6d013283368d1f7eb09bf6c9e7573c0ae4009304cf3bc1d9836c197046 |
| Rich supplement | c8f11c28b4014aec3f06f52e3c058640409d8fa9d0d8a91c95f2f05505eabcfd |
| Rich PCA array | 39ae5ee387c56ba624871db49d535c7af78edd1a5a8d158b788e9aa7d6bbfa07 |
| M12 | GPU1043922, V100S32GB, all phases passed12:20:50. Integrity63.16s; tiny59.36s; complete short chain1536.68s. Short-chain peak5.096GiB. |
| M13 | Frozen by1044059 at14:26:25; SHA07466ebce053d1886baf093510aa8e4990818067d1193f5628152fc46b28af03. Earlier1043965 formatting failure retained; no final record was written by that failed attempt. |
| Production integration | Checked registry/dispatch/offload1044063; graceful offload handoff1044070; plan apply1044074; queue/watcher deployment1044077. All21 historical code groups remained unchanged. |
| Production plan | 1,154 registered rows: core540, access210, panel120, rich126, CSX158. Initially92ready and1,062waiting for real dependencies; zero failed. |
| GPU execution | Prior keeper1044079; first worker1044083 started14:33:15 and claimed a real production unit14:33:20. Further workers1044089/1044091, with up to4 prior workers inside the aggregate10-GPU runfill cap. |

The M12 short chain covers NCE and kernel CS donor groups, leave-target-out DTU/private donors, rich and CSX paths, bridges, zero-shot A/B/C access and matched scratch/AP target interfaces including private [32,70) samples. These are explicitly truncated engineering executions, excluded from production analysis. Production wrappers reject truncated donors and epoch overrides. A successful probe is not evidence of successful pretraining or transfer.

The frozen M13 record is `private/auditory_alignment_v3/aln34/E34_PUBLIC_PRIOR_EXECUTION_RECORD.md`. Its80-file provenance table and `probe_out_prior33/20261017T115309/receipt.json` retain the complete checks, actual measurements and deviations. Cache storage remains `/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1`; checkpoint offload remains in the established private /projects location. No private raw EEG cache was added.

Important limits remain explicit: only part of the donor clock alignment is verifiable; the declared sub-051 exclusion is retained with its corrected rationale; private-test-audio overlap is unverified; historical generic-pretraining identity overlap is uncertified; FAU unplayed-code exclusions, clipping in raw-uV mode C and Federici's restricted original frequency support remain recorded. Rich availability is partial in target cohorts. These are not reasons to fabricate independence or universal auditory coverage.

Two frozen-target follow-ups now have independent plans, tests and aggregation code:90privateCS leave-self-out calibration evaluations (GPU probe1044337) and300representative-seed core science evaluations (probe1044347). Both await actual target sources and their successful engineering receipts;0production evaluations are complete. No old training/selection identity is rewritten. The first science version retains its64Hz timing and available envelope/onset/history targets; spectral/contextual features are not yet mapped into that contract.

Next execution steps are to finish the registered donor/bridge/target/access units, apply the declared donor-continuation rule if its training-side trigger is reached, and aggregate matched identity-level native/unified results with actual coverage. No outcome threshold gates the independent learning-curve, adaptation or science lanes. Queueing and completion are tracked separately in the mutable completion ledger and fleet status; the immutable execution record is not retroactively rewritten.
