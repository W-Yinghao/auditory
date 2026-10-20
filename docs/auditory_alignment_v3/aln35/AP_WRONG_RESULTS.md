# ALN3.5 matched AP wrong-audio results

Exploratory common-sampler, fixed-h30 comparison; seed3401 only.

Completed target executions: 0/50.

| Dataset | Endpoint | Contrast | Paired people | Effect | Pointwise 95% | Family simultaneous 95% |
|---|---|---|---:|---:|---|---|
| dtu | unified/regular/logloss_bits | AP-S | 0 | pending | pending | pending |
| dtu | unified/regular/logloss_bits | APwrong-S | 0 | pending | pending | pending |
| dtu | unified/regular/logloss_bits | AP-APwrong | 0 | pending | pending | pending |
| fau | unified/regular/logloss_bits | AP-S | 0 | pending | pending | pending |
| fau | unified/regular/logloss_bits | APwrong-S | 0 | pending | pending | pending |
| fau | unified/regular/logloss_bits | AP-APwrong | 0 | pending | pending | pending |
| private_bdf | NLL | AP-S | 0 | pending | pending | pending |
| private_bdf | NLL | APwrong-S | 0 | pending | pending | pending |
| private_bdf | NLL | AP-APwrong | 0 | pending | pending | pending |
| private_bdf | AUC | AP-S | 0 | pending | pending | pending |
| private_bdf | AUC | APwrong-S | 0 | pending | pending | pending |
| private_bdf | AUC | AP-APwrong | 0 | pending | pending | pending |

Positive effects favour the named candidate: risk is reference minus candidate; AUC is candidate minus reference. Each endpoint is a separate three-contrast family. Cell differences are averaged within people before inference; content folds and this single seed never increase n. Max-t uses the identities common to available contrasts; its n and membership are recorded in JSON.

Intervals use 4,000 identity bootstrap replicates, conditional on these fitted donors and targets. Missing and technically invalid pairs are listed; nothing is zero-filled. Original AP/S/XP/J*/XM and their historical full-trajectory results remain unchanged and are not silently substituted for the new equal-budget AP comparator.

Beating wrong-audio alone is insufficient evidence of benefit over scratch; read AP−S, APwrong−S and AP−APwrong jointly. Weak or reversed results remain valid within this configuration and do not close the shared sound–EEG research question.
