# ALN3.5 APwrong results, corrected analysis v2

Analysis-only correction before any new target result: v1 incorrectly inherited the previous round's bootstrap-t and partial-cell pairing. Its seal and empty report remain intact. v2 applies package §6.5 and does not alter training.

Completed target executions: 50/50; exploratory seed3401.

| Dataset | Endpoint | Contrast | Common complete people / expected | Effect | Simultaneous 95% | Status |
|---|---|---|---:|---:|---|---|
| dtu | unified/regular/logloss_bits | AP-S | 44/44 | +0.059198 | [0.035097, 0.083299] | regular |
| dtu | unified/regular/logloss_bits | APwrong-S | 44/44 | +0.060789 | [0.032473, 0.089106] | regular |
| dtu | unified/regular/logloss_bits | AP-APwrong | 44/44 | -0.0015915 | [-0.025415, 0.022232] | regular |
| fau | unified/regular/logloss_bits | AP-S | 67/67 | -0.00031358 | [-0.020377, 0.019749] | regular |
| fau | unified/regular/logloss_bits | APwrong-S | 67/67 | +0.020597 | [-0.0014632, 0.042657] | regular |
| fau | unified/regular/logloss_bits | AP-APwrong | 67/67 | -0.02091 | [-0.043777, 0.0019562] | regular |
| private_bdf | NLL | AP-S | 64/64 | +0.00086628 | [-0.00054226, 0.0022748] | regular |
| private_bdf | NLL | APwrong-S | 64/64 | +0.00048969 | [-0.00081794, 0.0017973] | regular |
| private_bdf | NLL | AP-APwrong | 64/64 | +0.00037659 | [-0.00073618, 0.0014894] | regular |
| private_bdf | AUC | AP-S | 64/64 | +0.0093125 | [0.0015238, 0.017101] | regular |
| private_bdf | AUC | APwrong-S | 64/64 | +0.0064123 | [-0.0015742, 0.014399] | regular |
| private_bdf | AUC | AP-APwrong | 64/64 | +0.0029003 | [-0.0047884, 0.010589] | regular |

Every family uses the same people complete for S/AP/APwrong, all required content folds, and seed3401. The roster is supplied from the frozen manifest: DTU44, FAU67, private64. Subject-fold is exclusion membership, not a repeated fold. Public content folds0/1 are both required; private has one evaluation cell.

The package's unchanged reference analyzer performs 4,000 whole-person bootstrap draws within hearing-group strata, shares draws across all contrasts, and uses fixed original standard errors for max-|z*| intervals. Each metric is its own three-contrast family. Low n, zero stratum contrast variance and other nonregular cases retain point estimates and missing intervals, with reasons in JSON.

Ordered query and candidate IDs are reconstructed from the exact frozen evaluator metadata, bound to input-view/code hashes, and stored privately. This exceeds count-only matching. Historical S records did not capture runtime query IDs; reconstruction is explicitly distinguished from historical runtime evidence. Private staged-source hashes are rechecked at every analysis.

Positive risk effects mean reference minus candidate; positive AUC effects mean candidate minus reference. Intervals condition on these fitted models/content/seed. AP over wrong alone does not establish AP over S. All original public-prior endpoints remain available; no performance gate or sign-based stopping is introduced.
