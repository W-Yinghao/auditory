> Publication copy: the researcher subsequently requested this curated release. Earlier no-push, not-trained and intermediate states are historical. Current completion: [corrected-cohort retraining](../../docs/auditory_retrain/STATUS.md). Participant data and weights remain private; see [publication scope](../../PUBLICATION.md).

# Corrected-cohort full retraining — completed and verified

The requested first item is complete in a new namespace. No previous encoder,
clinical projection or stimulus head is used as initialization. This execution
does not constitute independent clinical validation or prospective follow-up.

Preparation passed in Slurm999568: corrected D support52, outer universe60,
37 changed outer assignments,427 EEG files checked against frozen exports,
and43 relevant module tests passed. Plan SHA256:
`52554a0e2c4685501669da5296ef523c5bcd2bb1c6746ac957ce57816d02b5d6`.

| Slurm job | Work | Final state |
| --- | --- | --- |
| 999567 | GPU compatibility probe, actual L40S | PASS |
| 999568 | Rebuild corrected manifest/support/folds; verify inputs and tests; freeze plan | PASS |
| 999569 | GPU lane0:10 SUP and10 SIM scopes | PASS, all20 tasks, L40S |
| 999570 | GPU lane1:10 SUP and10 SIM scopes | PASS, all20 tasks, L40S |
| 999571 | Five deterministic L0 representations and new stimulus heads | PASS, all5 tasks |
| 999572 | Three modes ×27 nested clinical models | Completed;48,105 clinical predictor calls |
| 999573 | All-trial, count/QC, null stimulus probe, numerical invariance controls | COMPLETED_DIAGNOSTICS;53,865 clinical predictor calls |
| 999580 | Independent auditor preflight on15 completed tasks; deliberate invalid fit-scope rejected | PASS, zero model fits |
| 999581 | Full independent verification, saved-OOF reporting and figures | PASS;45/45 tasks,121/121 control states,60 FP32 checks |

The authoritative completed report is
`reports/auditory_retrain_v1/verification_001/REPORT.md`; aggregate verification,
all model metrics and all contrasts are under
`results/auditory_retrain_v1/verification_001/`.
`docs/auditory_retrain/INTERPRETATION.md` explains the small signals and their
controls. Final verification checked all45 representation receipts,40 encoder
checkpoints,52 candidates ×27 core models ×3 modes, and52 ×33 sensitivity models
×3 modes. All427 EEG inputs were rehashed. Report generation and verification
performed zero model fits. No failed attempts or duplicated encoder fits occurred.

Original core/control summaries retain their historical intermediate/screening
fields; they are preserved artifacts, not the completion authority for this round.
Use the final verification above. Scheduler accounting via `sacct` was unavailable
(database connection refused); job IDs, captured allocation/completion details,
private logs and per-task receipts are retained. Predictor-call counts exclude
stimulus-head fitting, neural optimization steps and module tests.

The scientific execution has no gain/significance gate. Original SUP
training-only stimulus monitoring and fixed100 SIM epochs are retained for
comparability. R_SIM remains primary. No GitHub publication is authorized by
this turn.

Private artifacts: `private/auditory_retrain_v1/`. Aggregate outputs:
`results/auditory_retrain_v1/`. Frozen protocol:
`docs/auditory_retrain/PROTOCOL_v1.md`.

Primary R_SIM null gain beyond C+V is +0.019687 source points
(fixed-OOF95% interval −0.274180 to+0.295282). Joint C+V+N is0.094234 points worse
than C alone. Small positive alternatives and sensitivity estimates remain
reported. Completion does not imply independent clinical confirmation.
