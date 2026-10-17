# Private CS calibration: leave-self-out intervention

Complete: 120 frozen checkpoints, all three seeds, 64 paired children. Slurm job 1044311.

Each encoder and test reference bank is unchanged. Only calibration scores remove the exact contribution of their own trial when that trial was selected into the reference bank. The positive-affine mapping is then refitted. This tests trial self-reference; same-child references remain.

All selected attempts passed the original numerical reproduction tolerances. Historical failures and device retries are retained in loo_execution_status.json. The selection rule prefers the original passing record, then original hardware, then lexical path; it never uses the intervention effect.

Loss changes are LOO minus reference, averaged within child over seeds. Negative means improvement. Simultaneous intervals cover all 16 configuration/reference contrasts separately for each endpoint. Seeds and folds do not increase n.

| Configuration | Reference | NLL change | Simultaneous 95% interval |
|---|---|---:|---|
| E_GENERIC / CS_SINGLE / cbramod / random_full | original_refit | +0.000011 | [-0.000243, +0.000265] |
| E_GENERIC / CS_SINGLE / cbramod / random_full | class_kernel | -0.000117 | [-0.000505, +0.000270] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_peft | original_refit | +0.000023 | [-0.000304, +0.000350] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_peft | class_kernel | -0.000844 | [-0.002035, +0.000348] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_full | original_refit | +0.000006 | [-0.000277, +0.000290] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_full | class_kernel | -0.000546 | [-0.001617, +0.000524] |
| E_GENERIC / CS_SINGLE / reve / random_full | original_refit | -0.038649 | [-0.041747, -0.035550] |
| E_GENERIC / CS_SINGLE / reve / random_full | class_kernel | -0.000212 | [-0.000445, +0.000020] |
| E_GENERIC / CS_SINGLE / reve / pretrained_peft | original_refit | -0.135854 | [-0.143959, -0.127750] |
| E_GENERIC / CS_SINGLE / reve / pretrained_peft | class_kernel | +0.000066 | [-0.000260, +0.000391] |
| E_GENERIC / CS_SINGLE / reve / pretrained_full | original_refit | -0.006742 | [-0.009266, -0.004218] |
| E_GENERIC / CS_SINGLE / reve / pretrained_full | class_kernel | -0.000022 | [-0.000457, +0.000412] |
| E_LOCAL / CS_SINGLE / lag_local_tokens / full | original_refit | -0.000031 | [-0.000280, +0.000218] |
| E_LOCAL / CS_SINGLE / lag_local_tokens / full | class_kernel | -0.000260 | [-0.000911, +0.000391] |
| E_PUBLIC_TRANSFER / CS_SINGLE / lag_local_tokens / task_partial | original_refit | -0.000036 | [-0.000304, +0.000232] |
| E_PUBLIC_TRANSFER / CS_SINGLE / lag_local_tokens / task_partial | class_kernel | -0.000324 | [-0.001236, +0.000587] |

Exact simultaneous statistics and all per-seed method levels are in `results/auditory_alignment_v3/aln34/private_calibration/leave_self_out.json`. AUC remains exactly unchanged within every rerun because the mapping is monotone on the same scores.

This intervention does not establish clinical prediction or history-adjusted EEG benefit. It informs the probability interface used by those separate research questions.
