# FN1 W0 execution report

- stage: `IMPLEMENTATION_UNRESOLVED`
- W0 status: `NEEDS_CLINICAL_RESPONSE`
- W1 allowed: `False`
- blocking reasons:
  - no clinical lock file supplied
  - implementation check: IMPLEMENTATION_UNRESOLVED

## Limited implementation check

- status: `IMPLEMENTATION_UNRESOLVED`
- neural fits executed: 24 (plan budget: three mechanisms x four seeds x two orders = 24)
- all predictions finite: True
- non-finite optimiser runs: 0
- parameter counts observed: [1209]

| mechanism | model | required | seeds meeting threshold | passed |
|---|---|---|---|---|
| segment_mean_drives_target | M3 | True | 4/4 | True |
| segment_mean_drives_target | M4 | True | 4/4 | True |
| distribution_shape_drives_target | M3 | False | 0/4 | None |
| distribution_shape_drives_target | M4 | True | 0/4 | False |

> Structural and learnability check of the fixed implementation. Not a false-positive-rate certificate, not a power analysis, and not evidence that a real clinical effect is detectable.

## Sources consulted

| role | path | present | sha256 |
|---|---|---|---|

No model was fitted on real EEG, no clinical material was sent anywhere, and no EEG-to-target association was computed in this stage.
