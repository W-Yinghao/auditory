# Independent capability evaluation

N1_L0: **PASS**. Fixed seeds and thresholds; no participant outcomes fitted.

| World | Rate | Evaluable | Recoveries | Meaningful FP | Raw FP | Risk preserved | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| trial_key | 0.15 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| trial_key | 0.2 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| group_key | 0.15 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| group_key | 0.2 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| additive_background | 0.15 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| additive_background | 0.2 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| independent_background | 0.15 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| independent_background | 0.2 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| history_only | 0.15 | 20/20 | 0 | 0 | 5 | 20 | PASS |
| history_only | 0.2 | 20/20 | 0 | 0 | 3 | 20 | PASS |
| trial_key_weak | 0.15 | 20/20 | 3 | 16 | 18 | 20 | DESCRIPTIVE_ONLY |
| trial_key_weak | 0.2 | 20/20 | 6 | 18 | 18 | 20 | DESCRIPTIVE_ONLY |

FP counts have their zero-information interpretation only on NULL rows; positive and weak rows retain the same diagnostic counters without claiming false positives. Exact binomial intervals and all denominators are in capability_receipt.json. Strong identifiability fixtures do not establish weak real-data power. No failed-world subset can authorize a real route.
