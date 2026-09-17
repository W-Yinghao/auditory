> GitHub发布副本：本轮验收后，用户明确要求发布代码与聚合结果。文内“未发布／未push”及早期进行中表述是历史状态；当前以v2.1最终科学报告和final_001为准。个体数据、预测、模型与详细日志仍在服务器。见[发布范围](../../PUBLICATION.md)。

# v2.1 existing-artifact closure lock

This closure pass is a read-only audit of the frozen v2 artifacts. It covers
A2, G0, and C2 only; it makes zero head or encoder fits, does not change the
existing Stage 0 review, and does not launch a new seed or expand a spatial
grid.

The audit may read saved aggregate CSV/JSON summaries, per-fold A2 matching
statistics and fit receipts. It checks the declared train/test/validation
ranges, checkpoint/scaler provenance fields, source hash chains, and completion
statuses. A file's presence alone never yields `PASS`; a check is `PASS` only
when the saved declaration and its linked hash or summary agree. Private
paths, identities and model artifacts remain private; public outputs contain
aggregate evidence and explicit `MISSING`/`LIMITED` statuses.

The provenance chain is anchored in the existing S0 feature-scope registry,
plan task/completion receipts, legacy input hashes, and saved probe metadata.
The closure job may hash checkpoint bytes under Slurm, but it never loads their
weights. Historical head-fit counts are recorded as reused artifacts; the
closure itself performs zero head or encoder fits.

A2 retains the four paired cosine review intervals and the frozen R_SIM
primary. Saved projected-inner-product and norm summaries may be described as
scale diagnostics when complete; they are not renamed as information. Missing
quality/background controls stay missing. G0 keeps original CNN-head,
post-fitted probe, same-child, and cross-child objects distinct. C2 checks
the existing spatial source and inherited-isolation evidence and records the
known isolation gap without expanding the left/right matrix.
