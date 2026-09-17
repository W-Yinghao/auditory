> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Auditory5 Slurm execution ledger

Final status update: jobs995908,995937/938/939,995950/956/966/967/968,995977 and995979 have terminated and final receipts are present. The representation matrix is90/90; S4_final_001 is S4_RECORDED_WITH_FAILURES. B/D are NEGATIVE_SCREEN; A remains unsupported for frozen history balancing; C full MLP attempts fail numerically; E retains its partial MLP failure and E1 support limitation. See [the final status note](AUDITORY5_FINAL_STATUS_v1.md). The dated orchestration entries below preserve their original submission-time descriptions.

This is an orchestration index, not a scientific verdict. Source plan, configuration, identity splits and all prior runs remain immutable. Completion JSON files and private logs are the evidence of completion; scheduler history is not assumed available.

The immutable representation plan is `private/auditory5_v1/jobs/plan_001/plan.json`: 90 tasks, including 60 learned-encoder tasks and 30 deterministic/random tasks. Two GPU workers and at most four CPU analysis jobs are permitted concurrently. Large arrays were rejected by the site submission quota, so sequential workers implement the same task list.

| Job | Purpose / run | Execution record |
|---|---|---|
| 995905, 995906 | L0 and random representation workers | Completed |
| 995907 | Supervised representation worker, including clinical inner encoders | Completed |
| 995908 | SimCLR representation worker, including clinical inner encoders | Ongoing at this ledger's creation |
| 995912 | B_L0_001 | Completed core |
| 995913 | D_L0_core_001 | Completed core |
| 995917 | A_L0_core_001 | Completed core |
| 995929 | A_SUP_RAND_core_001 | Completed core |
| 995930 | D_SUP_core_001 | Completed core |
| 995934 | B_SUP_RAND_core_001 | Completed core |
| 995918, 995928 | E0_native_001, E0_native_002 | Preserved numerical failures at 1000/5000 MLP iterations |
| 995936 | E0_native_003 | Linear completed; MLP numerical failures isolated, no successful-record-only aggregate |
| 995919 | C_L0_001 | Cancelled before results during implementation review |
| 995925, 995933 | C_L0_002, C_L0_003 | Preserved numerical failures at 1000/5000 MLP iterations |
| 995945 | C_linear_L0_SUP_RAND_001 | Original linear matrix and interventions; explicitly incomplete C |
| 995944 | B_controls_L0_SUP_001 | Prespecified windows, quality and circular-shift diagnostics |
| 995937 | A_SIM_core_001 | Depends on completed SimCLR worker and earlier CPU jobs |
| 995938 | D_SIM_core_001 | Depends on completed SimCLR worker and earlier CPU jobs |
| 995939 | B_SIM_core_001 | After A_SIM core |
| 995940 | Superseded combined C learned job | Cancelled while pending; replaced by independent mode jobs below |
| 995946 | Superseded pending C_SIM job | Cancelled before start after explicit linear-only summary API repair; replaced by995966 |
| 995947 | C_SUP_full_001 | Numerical failure: the first nested MLP32 head did not converge at 5000 iterations; no complete nonlinear OOF folds |
| 995950 | B_controls_SIM_001 | After B_SIM core |
| 995951 | Superseded pending C linear job | Cancelled before start after summary API repair; replaced by995967 |
| 995954 | D_controls_L0_SUP_001 | All-trial/count-QC sensitivity, new null probe and FP32 checks |
| 995956 | D_controls_SIM_001 | After D_SIM core |
| 995958 | A_controls_smoke_001 | Preserved pandas trial-column alignment failure; no scientific interpretation |
| 995961 | A_controls_smoke_002 | Real-data fold0 smoke after explicit trial-index name repair |
| 995964 | C_linear_L0_SUP_RAND_002 | Re-aggregate the15 completed linear model folds from001; zero refits, full nonlinear controls still missing |
| 995965 | A_controls_L0_SUP_RAND_001 | Completed; reset supports 50 candidates, history/position balancing supports zero; NEED_CONTROLS |
| 995966 | C_SIM_full_001 | Correctly gated replacement after D_SIM core |
| 995967 | C_linear_SIM_001 | Correctly gated replacement after SimCLR worker and supervised nonlinear attempt |
| 995968 | A_controls_SIM_001 | After B_SIM controls to preserve four CPU lanes |
| 995969 | A_balance_support_001 | Descriptive audit: zero of55 A candidates has the required full24-cell support; no selection-rule change |
| 995923, 995948 | execution_status_001, execution_status_002 | Aggregate snapshots, not final S4 |
| 995971 | contracts_021 | 172 tests passed, including initial S4 contract tests |
| 995973 | S4_interim_001 | Report and figures generated; 79/90 representation receipts; explicitly IN_PROGRESS |
| 995974 | contracts_022 | 173 tests passed; §16.2 primary-endpoint flags and clearer plot labels |
| 995976 | contracts_023 | 173 tests passed; final representation audit wording updated |
| 995980 | S4_interim_002 | Report and figures generated; 80/90 receipts, no aggregate schema failures; retains earlier snapshot |
| 995977 | execution_status_003 | Queued after terminal jobs 995968/995956/995966/995967; source pinned to contracts_023 |
| 995979 | S4_final_001 | Queued after995977 succeeds; explicit per-run registry, contracts_023 snapshot; report and PNG/PDF figures |

Contract gates through contracts_015 passed up to144 tests. contracts_016 captured an in-development A control API/test mismatch while the other152 tests passed; it remains a failed snapshot and is not used to authorize new D/A controls. Later gates must pass before those controls execute.

contracts_017 and contracts_018 passed155 tests. contracts_019 passed156 tests, including the regression for the real-data A smoke column-name failure. Successful module tests and real-data integration are distinct gates.

contracts_020 passed157 tests, including explicit linear-only C aggregation. C_linear_L0_SUP_RAND_001 had completed all15 fitting/OOF folds before its summary incorrectly required absent MLP capacity heads;002 repairs only that aggregation from saved predictions. The original failure and every fitted head remain intact. Full nonlinear C jobs keep their original matrix and convergence requirements.

Generic route/control runners make an immutable private source snapshot before executing. Existing model workers always re-execute the representation plan's frozen source. Partial outputs and failed runs are retained under their original names. No patient records, model features or exact source paths are published by this ledger. New analyses have not been automatically pushed to GitHub.

The final aggregation is scheduled after all four CPU lanes terminate, including numerical failures. It must retain those failures and any unsupported controls. `S4_final_001` is a reserved output name, not a claim that all scientific routes succeeded. If Slurm kills a job before it writes an expected source summary, S4 will keep that source missing and the report incomplete; inspect the private log instead of assigning a negative verdict. The fixed R_SIM worker995908 remains the prerequisite for the pending route cores. No additional seeds or architectures have been submitted.
