# FN1 W0 execution report

- stage: `W0_READY / W1_BLOCKED_CLINICAL_LOCK`
- W0 status: `NEEDS_CLINICAL_RESPONSE`
- W1 allowed: `False`
- blocking reasons:
  - no clinical lock file supplied

## Sources consulted

| role | path | present | sha256 |
|---|---|---|---|
| corrected_pta | `private/auditory_repair/pta_007/candidate_covariates.csv` | True | `a9d8e4cac31614d2` |
| legacy_pta_superseded | `private/phase3_ha_covariates_004/candidate_covariates.csv` | True | `56776d3bceabb6ab` |
| fseries_prepare | `results/auditory_fseries_archival/prepare_001/summary.json` | True | `c7893a07021b288b` |
| fseries_ci_qualification | `results/auditory_fseries/ci_qualification_001/summary.json` | True | `d4ead4520fb9fdf9` |
| fseries_ha_qualification | `results/auditory_fseries/ha_qualification_002/qualification_summary.json` | True | `8dbdb84432447af6` |
| retrain_summary | `results/auditory_retrain_v1/verification_001/summary.json` | True | `0751062850fc6728` |
| repair_summary | `results/auditory_repair/verification_001/summary.json` | True | `451f9d71e65ab4ad` |

No model was fitted on real EEG, no clinical material was sent anywhere, and no EEG-to-target association was computed in this stage.
