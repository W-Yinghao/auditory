# Effective update coverage of the legacy progressive-prefix recipe (B_DENSE, B_ALIGNED; seed 3401)

Generated 2026-10-14 17:11 CEST by `private/auditory_alignment_v3/effective_update_legacy.py` (Slurm 1040183); see CORRECTION_01_FULL_UPDATE_LABEL.md. Part A uses each record's `open_groups` per epoch intersected with the adaptation's allowed parameters; Part B measures the best checkpoint against θ_0 rebuilt with the training construction order. B_ALIGNED rows cover the units complete at generation time.

## Part A — trainable backbone blocks (all complete units)

| family · readout · backbone · adaptation | units | blocks | trainable blocks, last epoch | median at best epoch | non-block ever open | nominal initial lr of the deepest opened group (lr × 0.75^depth) |
|---|---|---|---|---|---|---|
| B_ALIGNED · aligned_patch_linear · cbramod · pretrained_frozen | 9 | 12 | [0] | 0 | 0.00 | – |
| B_ALIGNED · aligned_patch_linear · cbramod · pretrained_full | 9 | 12 | [12] | 12 | 1.00 | 3.17e-07 |
| B_ALIGNED · aligned_patch_linear · cbramod · pretrained_partial | 9 | 12 | [3] | 3 | 0.00 | 5.63e-06 |
| B_ALIGNED · aligned_patch_linear · cbramod · pretrained_peft | 9 | 12 | [12] | 12 | 0.00 | 4.22e-06 |
| B_ALIGNED · aligned_patch_linear · cbramod · random_full | 9 | 12 | [12] | 12 | 1.00 | 9.50e-06 |
| B_ALIGNED · aligned_patch_linear · reve · pretrained_frozen | 8 | 22 | [0] | 0 | 0.00 | – |
| B_ALIGNED · aligned_patch_linear · reve · pretrained_full | 8 | 22 | [9] | 8 | 0.00 | 1.00e-06 |
| B_ALIGNED · aligned_patch_linear · reve · pretrained_partial | 8 | 22 | [6] | 6 | 0.00 | 2.37e-06 |
| B_ALIGNED · aligned_patch_linear · reve · pretrained_peft | 8 | 22 | [22] | 22 | 0.00 | 2.38e-07 |
| B_ALIGNED · aligned_patch_linear · reve · random_full | 8 | 22 | [9] | 8 | 0.00 | 3.00e-05 |
| B_DENSE · channel_phase_linear · cbramod · pretrained_frozen | 50 | 12 | [0] | 0 | 0.00 | – |
| B_DENSE · channel_phase_linear · cbramod · pretrained_full | 50 | 12 | [12] | 4 | 1.00 | 3.17e-07 |
| B_DENSE · channel_phase_linear · cbramod · pretrained_partial | 50 | 12 | [3] | 3 | 0.00 | 5.63e-06 |
| B_DENSE · channel_phase_linear · cbramod · pretrained_peft | 50 | 12 | [12] | 12 | 0.00 | 4.22e-06 |
| B_DENSE · channel_phase_linear · cbramod · random_full | 50 | 12 | [12] | 7 | 1.00 | 9.50e-06 |
| B_DENSE · channel_phase_linear · reve · pretrained_frozen | 50 | 22 | [0] | 0 | 0.00 | – |
| B_DENSE · channel_phase_linear · reve · pretrained_full | 50 | 22 | [9] | 4 | 0.00 | 1.00e-06 |
| B_DENSE · channel_phase_linear · reve · pretrained_partial | 50 | 22 | [6] | 4 | 0.00 | 2.37e-06 |
| B_DENSE · channel_phase_linear · reve · pretrained_peft | 50 | 22 | [22] | 22 | 0.00 | 2.38e-07 |
| B_DENSE · channel_phase_linear · reve · random_full | 50 | 22 | [9] | 4 | 0.00 | 3.00e-05 |
| B_DENSE · dense_query · cbramod · pretrained_frozen | 50 | 12 | [0] | 0 | 0.00 | – |
| B_DENSE · dense_query · cbramod · pretrained_full | 50 | 12 | [12] | 7 | 1.00 | 3.17e-07 |
| B_DENSE · dense_query · cbramod · pretrained_partial | 50 | 12 | [3] | 3 | 0.00 | 5.63e-06 |
| B_DENSE · dense_query · cbramod · pretrained_peft | 50 | 12 | [12] | 12 | 0.00 | 4.22e-06 |
| B_DENSE · dense_query · cbramod · random_full | 50 | 12 | [12] | 8 | 1.00 | 9.50e-06 |
| B_DENSE · dense_query · reve · pretrained_frozen | 50 | 22 | [0] | 0 | 0.00 | – |
| B_DENSE · dense_query · reve · pretrained_full | 50 | 22 | [9] | 4 | 0.00 | 1.00e-06 |
| B_DENSE · dense_query · reve · pretrained_partial | 50 | 22 | [6] | 3 | 0.00 | 2.37e-06 |
| B_DENSE · dense_query · reve · pretrained_peft | 50 | 22 | [22] | 22 | 0.00 | 2.38e-07 |
| B_DENSE · dense_query · reve · random_full | 50 | 22 | [9] | 3 | 0.00 | 3.00e-05 |

## Part B — measured weight change (FAU and DTU, subject fold 0, content fold 0, NCE)

| family | dataset | backbone | adaptation | readout | blocks with rel. change > 1e-6 | max block rel. change | non-block rel. change |
|---|---|---|---|---|---|---|---|
| B_ALIGNED | dtu | cbramod | pretrained_frozen | aligned_patch_linear | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_ALIGNED | dtu | cbramod | pretrained_full | aligned_patch_linear | 12 / 12 | 1.23e-02 | 1.24e-04 |
| B_ALIGNED | dtu | cbramod | pretrained_partial | aligned_patch_linear | 3 / 12 | 1.24e-02 | 0.00e+00 |
| B_ALIGNED | dtu | cbramod | pretrained_peft | aligned_patch_linear | 12 / 12 | 2.50e-02 | 0.00e+00 |
| B_ALIGNED | dtu | cbramod | random_full | aligned_patch_linear | 12 / 12 | 1.47e-01 | 6.41e-04 |
| B_ALIGNED | dtu | reve | pretrained_frozen | aligned_patch_linear | 0 / 22 | 0.00e+00 | 0.00e+00 |
| B_ALIGNED | dtu | reve | pretrained_full | aligned_patch_linear | 7 / 22 | 5.91e-03 | 0.00e+00 |
| B_ALIGNED | dtu | reve | pretrained_partial | aligned_patch_linear | 6 / 22 | 5.91e-03 | 0.00e+00 |
| B_ALIGNED | dtu | reve | pretrained_peft | aligned_patch_linear | 22 / 22 | 7.40e-03 | 0.00e+00 |
| B_ALIGNED | dtu | reve | random_full | aligned_patch_linear | 8 / 22 | 2.87e-01 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_frozen | channel_phase_linear | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_frozen | dense_query | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_full | channel_phase_linear | 4 / 12 | 8.17e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_full | dense_query | 11 / 12 | 8.34e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_partial | channel_phase_linear | 3 / 12 | 8.23e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_partial | dense_query | 3 / 12 | 8.34e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_peft | channel_phase_linear | 12 / 12 | 9.88e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | pretrained_peft | dense_query | 12 / 12 | 9.63e-03 | 0.00e+00 |
| B_DENSE | dtu | cbramod | random_full | channel_phase_linear | 12 / 12 | 2.06e-01 | 0.00e+00 |
| B_DENSE | dtu | cbramod | random_full | dense_query | 9 / 12 | 1.09e-01 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_frozen | channel_phase_linear | 0 / 22 | 0.00e+00 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_frozen | dense_query | 0 / 22 | 0.00e+00 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_full | channel_phase_linear | 6 / 22 | 1.36e-02 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_full | dense_query | 4 / 22 | 3.57e-03 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_partial | channel_phase_linear | 6 / 22 | 1.36e-02 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_partial | dense_query | 4 / 22 | 3.57e-03 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_peft | channel_phase_linear | 22 / 22 | 1.99e-02 | 0.00e+00 |
| B_DENSE | dtu | reve | pretrained_peft | dense_query | 22 / 22 | 3.77e-03 | 0.00e+00 |
| B_DENSE | dtu | reve | random_full | channel_phase_linear | 8 / 22 | 3.39e-01 | 0.00e+00 |
| B_DENSE | dtu | reve | random_full | dense_query | 4 / 22 | 1.89e-01 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_frozen | channel_phase_linear | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_frozen | dense_query | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_full | channel_phase_linear | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_full | dense_query | 8 / 12 | 1.19e-02 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_partial | channel_phase_linear | 0 / 12 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_partial | dense_query | 3 / 12 | 8.97e-03 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_peft | channel_phase_linear | 12 / 12 | 3.93e-02 | 0.00e+00 |
| B_DENSE | fau | cbramod | pretrained_peft | dense_query | 12 / 12 | 1.33e-02 | 0.00e+00 |
| B_DENSE | fau | cbramod | random_full | channel_phase_linear | 12 / 12 | 3.00e-01 | 2.22e-03 |
| B_DENSE | fau | cbramod | random_full | dense_query | 12 / 12 | 2.03e-01 | 1.90e-03 |
| B_DENSE | fau | reve | pretrained_frozen | channel_phase_linear | 0 / 22 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_frozen | dense_query | 0 / 22 | 0.00e+00 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_full | channel_phase_linear | 9 / 22 | 2.33e-02 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_full | dense_query | 4 / 22 | 8.06e-03 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_partial | channel_phase_linear | 6 / 22 | 2.33e-02 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_partial | dense_query | 4 / 22 | 8.06e-03 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_peft | channel_phase_linear | 22 / 22 | 2.27e-02 | 0.00e+00 |
| B_DENSE | fau | reve | pretrained_peft | dense_query | 22 / 22 | 8.27e-03 | 0.00e+00 |
| B_DENSE | fau | reve | random_full | channel_phase_linear | 9 / 22 | 4.97e-01 | 0.00e+00 |
| B_DENSE | fau | reve | random_full | dense_query | 4 / 22 | 2.38e-01 | 0.00e+00 |
