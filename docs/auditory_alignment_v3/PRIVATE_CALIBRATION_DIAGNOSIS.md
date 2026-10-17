# Private CS calibration diagnosis — exploratory, 2026-10-17

Stage 1 reads all 120 CS_SINGLE panel records (8 configurations × 3 seeds × 5 folds). All 64 children are paired, with identical trial counts. No model was retrained. Positive ΔNLL means positive-affine calibration increased test loss relative to the stored class-kernel posterior.

Child means across seeds are bootstrapped (4,000 draws); simultaneous intervals cover the eight configurations. They condition on the fitted models. Seeds do not increase n.

| Configuration | ΔNLL 3401 / 3407 / 3413 | Child-mean ΔNLL [simultaneous 95%] |
|---|---|---|
| E_GENERIC / CS_SINGLE / cbramod / random_full | -0.00019 / -0.00021 / +0.00002 | -0.00013 [-0.00070, +0.00044] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_peft | -0.00099 / -0.00072 / -0.00089 | -0.00087 [-0.00224, +0.00051] |
| E_GENERIC / CS_SINGLE / cbramod / pretrained_full | -0.00078 / -0.00057 / -0.00031 | -0.00055 [-0.00178, +0.00068] |
| E_GENERIC / CS_SINGLE / reve / random_full | +0.09233 / +0.00482 / +0.01816 | +0.03844 [+0.03572, +0.04115] |
| E_GENERIC / CS_SINGLE / reve / pretrained_peft | +0.00464 / +0.19361 / +0.20951 | +0.13592 [+0.12860, +0.14324] |
| E_GENERIC / CS_SINGLE / reve / pretrained_full | +0.00170 / +0.01538 / +0.00307 | +0.00672 [+0.00423, +0.00921] |
| E_LOCAL / CS_SINGLE / lag_local_tokens / full | -0.00026 / -0.00063 / +0.00020 | -0.00023 [-0.00105, +0.00059] |
| E_PUBLIC_TRANSFER / CS_SINGLE / lag_local_tokens / task_partial | -0.00057 / +0.00013 / -0.00042 | -0.00029 [-0.00136, +0.00078] |

The stored native-score AUC is identical between methods for every child. A loss difference diagnoses the probability mapping, but does not by itself establish the cause. Stage 2's leave-one-out self-reference intervention remains separately registered and must reproduce the original scorer. No corrected GPU result is claimed by this report.

Slurm CPU job: 1043948; analysis code SHA256: 5745e8ec418d1dd08c86b971e67c2b4c81b8479c910115824212bc091bc7432c. Full code and record hashes, per-seed NLL/Brier/AUC levels and all unit calibration parameters are in results/auditory_alignment_v3/aln34/private_calibration/record_diagnosis.json. The original E_MULTI_SEED_RESULTS.md is retained.
