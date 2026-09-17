# Independent capability evaluation

N3_L0: **PASS**. Fixed seeds and thresholds; no participant outcomes fitted.

| World | Rate | Evaluable | Recoveries | Meaningful FP | Raw FP | Risk preserved | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| strong_history_null | 0.15 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| strong_history_null | 0.2 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| strong_history_increment | 0.15 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| strong_history_increment | 0.2 | 20/20 | 20 | 20 | 20 | 20 | PASS |
| history_copy | 0.15 | 20/20 | 0 | 1 | 2 | 20 | PASS |
| history_copy | 0.2 | 20/20 | 0 | 1 | 2 | 20 | PASS |
| near_deterministic | 0.15 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| near_deterministic | 0.2 | 20/20 | 0 | 0 | 0 | 20 | PASS |
| strong_history_increment_weak | 0.15 | 20/20 | 0 | 0 | 4 | 20 | DESCRIPTIVE_ONLY |
| strong_history_increment_weak | 0.2 | 20/20 | 0 | 1 | 4 | 20 | DESCRIPTIVE_ONLY |

FP counts have their zero-information interpretation only on NULL rows; positive and weak rows retain the same diagnostic counters without claiming false positives. Exact binomial intervals and all denominators are in capability_receipt.json. Strong identifiability fixtures do not establish weak real-data power. No failed-world subset can authorize a real route.
