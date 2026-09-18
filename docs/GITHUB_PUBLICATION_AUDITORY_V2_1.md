> GitHub 发布副本：本轮执行完成后，用户明确要求发布代码与聚合结果。文内“未 push”和早期运行状态是历史记录；V3 以 final_002 为准。个体数据、预测、模型和详细日志留在服务器。见[发布范围](../PUBLICATION.md)。

# v2.1 GitHub publication receipt — 2026-09-18

The researcher explicitly requested this push after completion of the v2.1 conditional plan. The curated snapshot was pushed to `W-Yinghao/auditory` main as `eb24106afe170b323859daa9dda597a85e548bb9`; the remote reference was independently read back to the same commit. The publication checkout is clean.

- [Commit](https://github.com/W-Yinghao/auditory/commit/eb24106afe170b323859daa9dda597a85e548bb9)
- [Scientific results](https://github.com/W-Yinghao/auditory/blob/main/docs/auditory_v21/SCIENTIFIC_RESULTS_v2_1.md)
- [Publication scope and caveats](https://github.com/W-Yinghao/auditory/blob/main/PUBLICATION.md)
- [Release verification](https://github.com/W-Yinghao/auditory/blob/main/release/verification.json)

This update changes 185 files and contains 175 selected source/artifact copies, editorial navigation and release records. The complete repository now contains 888 tracked files with 886 payload hashes (12,876,179 payload bytes). The exact committed tree is `ac2add1c2986805c87097cb8de3f850c7cce2755`, matching the private index receipt.

Slurm jobs: 997577 built the whitelist export; 997580 performed the first broader scan; 997582 passed the corrected release verification; 997583 passed exact staged-file/blob/hash verification. CPU packaging requests were respectively 1 core/5 min, 2 cores/10 min, 2 cores/10 min, and 1 core/5 min; scheduler allocation rounds single-core requests to two CPUs on this partition. This publication work is separate from the immutable scientific 32 CPU core-hour upper bound. No new encoder/head/model fits or GPU jobs were run. sacct was unavailable; scontrol receipts/logs remain private.

Checks covered 249 Python files, 68 Slurm scripts, 251 local links, 16 PDF texts, 21 PNG structures, 161 known names and 59,382 known identifiers. All 163 non-documentation source copies matched exactly. The existing tests_009 receipt records 59 passed tests and its 120 Python/contract source files match this release; this is source-bound historical test evidence, not a fresh test execution. Ten figure input hashes match. 703 previous payload files are unchanged; navigation and the disclosed legacy script correction are exceptions.

The first scan found hardcoded pseudonymous record IDs in the previously published `slurm/13_phase1_smoke.sbatch`. Its publication copy now requires runtime arguments. Original server code and scientific outputs remain immutable. Existing Git history was not rewritten and still contains the old script; the correction and this limitation are disclosed in PUBLICATION.md and the change record. The failed scan receipt remains private.

N2 denominator reconciliation checked saved metadata: 57 original candidates, 54 with at least one matched half, 49 with both halves, five with one half and three with none (103 eligible candidate×halves). Thus 49/57 remains the full-cohort support fraction; the later receipt's 54 is conditional on any matched bag. No frozen result file was edited.

The release includes 880 synthetic-world records, four full N1/N3 real comparisons, A2 paired summaries, N2 metadata/support evidence, final closure_003, final_001 acceptance, figures_002 and earlier failure/superseded audit records. N1/N3 have no established controlled increment; N2 is conditionally stopped because frozen role support fails four folds. Unsupported and negative findings remain explicit.

Raw and processed EEG, individual clinical data, exact identity/event/bag manifests and splits, individual predictions, models, private source snapshots and detailed logs remain on the server. This is a curated aggregate publication, not a participant-data release or anonymization certificate. Packing scripts, prior manifest, failed/passed audit receipts, exact index allowlist, commit message and logs are retained in `private/github_publish_004/`. CSV CRLF endings and one harmless source whitespace line were retained to preserve exact executed source/result hashes; no scientific artifacts were normalized for Git styling.
