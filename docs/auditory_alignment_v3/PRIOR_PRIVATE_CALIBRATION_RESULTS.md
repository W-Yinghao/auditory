# Public-prior private CS calibration sensitivity

Snapshot2026-10-18T16:10:22.524175+02:00: **interim**, 50/90frozen primary checkpoints.

This exploratory readout intervention preserves training, primary checkpoint selection and test reference banks. Original-score reproduction must pass the inherited numerical tolerances; only exact calibration-trial self-reference is removed. Same-child reference dependence remains. Positive-affine AUC is unchanged. It does not replace the frozen prior analysis.

| Configuration | Planned seeds | Complete paired children | LOO minus original NLL | Simultaneous95% interval |
|---|---|---:|---:|---|
| core / AP / donor / AP / CS_SINGLE / 200 | [3401] | 64/64 | +0.000075 | [-0.000365, +0.000514] |
| core / XP / donor / XP / CS_SINGLE / 200 | [3401] | 64/64 | +0.000003 | [-0.000253, +0.000260] |
| csx / APC / donor / APC / CS_SINGLE / 200 | [3401] | 26/64 | -0.000438 | [-0.000921, +0.000045] |
| rich / APR / donor / APR / CS_SINGLE / 200 | [3401] | 39/64 | -0.000083 | [-0.000554, +0.000388] |
| core / XM / donor / XM / CS_SINGLE / 200 | [3401] | 64/64 | +0.000128 | [-0.000172, +0.000429] |
| core / S / random / S / CS_SINGLE / 200 | [3401] | 64/64 | -0.000063 | [-0.000294, +0.000167] |
| core / J* / donor / J* / CS_SINGLE / 200 | [3401] | 64/64 | +0.000096 | [-0.000239, +0.000431] |
| csx / XPC / donor / XPC / CS_SINGLE / 200 | [3401] | 39/64 | +0.000013 | [-0.000378, +0.000404] |
| panel / AP / donor / AP / CS_SINGLE / 200 | [3407, 3413] | 0/64 | pending | pending |
| panel / XM / donor / XM / CS_SINGLE / 200 | [3407, 3413] | 0/64 | pending | pending |
| panel / XP / donor / XP / CS_SINGLE / 200 | [3407, 3413] | 0/64 | pending | pending |
| panel / S / random / S / CS_SINGLE / 200 | [3407, 3413] | 0/64 | pending | pending |
| panel / J* / donor / J* / CS_SINGLE / 200 | [3407, 3413] | 0/64 | pending | pending |

Both reference contrasts and all endpoints are in the aggregate JSON;4000identity bootstrap-t, simultaneous within each configuration×endpoint two-contrast family. Only full planned-seed pairing enters a mean. The gain-selected checkpoint sensitivity is outside this first follow-up.
