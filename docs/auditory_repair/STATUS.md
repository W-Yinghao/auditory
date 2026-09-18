> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Extended archival repair round: complete

Final verification: **PASS**, Slurm **999510**, zero model refits. All declared
analyses for this round completed; no significance, interval or minimum-gain
threshold caused scientific early stopping. No repair-round jobs remain queued
or running. The unrelated existing no-shell allocation was not modified.

- [Full Chinese research report](../../reports/auditory_repair/verification_001/REPORT.md)
- [Machine-readable verification](../../results/auditory_repair/verification_001/verification.json)
- [All fitted-call accounting](../../results/auditory_repair/verification_001/fit_accounting.json)
- [Execution ledger](JOBS.json)
- [Reproduction and authoritative versions](REPRODUCTION.md)
- [Evidence map and limits](EVIDENCE_MAP.md)

Independent final checks covered 138 metric rows, 104 effect rows, 4,131 legacy D
prediction rows, the nine F3 task pairs and 15 HA repeated-acquisition pairs,
and 285 source bindings. Known-identity/raw-path scanning covered 87 public text
files; 943 private paths were checked and 29 permissions tightened. This is a
bounded privacy audit, not a proof against all possible re-identification.

The final numeric source-row comparison still finds **57/57 source rows
changed**. It preserves the pta_007 corrected values and confirms **55/57
unaided PTA values and 47/57 aided PTA values changed**. The frozen original
folds were reproduced exactly. Corrected D support is 52 instead of 51, with
three gains and two losses; the corrected counterfactual fold balance moves
37/60 groups. Historical replay retains the original cohorts/folds and does
not reuse old encoder projections under new fold memberships.

The most useful retained leads are the small V-given-A conditional archival
gain, its sensitivity to technical controls, the stronger split-half
consistency of Hjorth/spatial summaries, and the small paired-task measurement
set. Mixed-MFF regression is complete for 38 A/V and 36 CAP/SIR candidates,
all with usable derived age; each target has only one literal CI source.
Its current fixed EEG bank does not stably improve the baseline.

Operational accounting totals **298,686 head-call attempts**, including tests,
mean heads, repeated historical replay and supplemental previously unlogged
calls. It is not a count of independent models or statistical tests. There were
43 registered Slurm CPU jobs; the full requested-time reservation bound is
23.8 core-hours, not measured CPU consumption. GPU use is zero. The unnecessary
duplicate D replay is explicitly disclosed in the report and fully charged.

Remaining scientific scope is explicit: no new-support/new-fold encoder
retraining, full-pipeline resampling, independent validation, or confirmed
clinical follow-up study has been completed. This round's completion does not
claim every historical project result is repaired or every possible analysis
exhausted. Future rounds should preserve informative small effects and complete
their declared comparisons, with new finite hypotheses and versioned protocols.

All original data and historical results are preserved. Participant-level
artifacts remain private. This round has **not** been pushed to GitHub.
