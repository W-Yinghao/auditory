# ALN3.5 CB auditory state sensitivity

Selection scope: **donor-dev NCE sensitivity only; not whole-pipeline or target-inner selection**.

The minimum of the four original source-dev NCE values selects update10000. This sensitivity therefore equals the original fixed10000 policy exactly; it is not an additional independent result or a new target fit.

Existing DTU seed3401 generic_paired target coverage: 10/10 cells; unfinished cells remain in the original registered lane.

| Update | Original fit NCE | Original dev NCE | Flattened backbone rank | Readout rank | Relative backbone change |
|---:|---:|---:|---:|---:|---:|
| 0 | not applicable | 5.11945 | 238.881 | 31.1654 | 0 |
| 2500 | 4.08265 | 4.07993 | 140.912 | 6.33821 | 0.179465 |
| 5000 | 4.07875 | 4.07889 | 152.44 | 6.68267 | 0.231342 |
| 10000 | 4.07558 | 4.07612 | 155.259 | 6.5301 | 0.249253 |

Rank uses the same first four fixed source-dev batches (256 anchors), centered singular-value entropy, without target data. Original training-interval losses and donor-head dev losses do not establish target transferability. A large parameter change alone does not establish catastrophic forgetting.

The historical fixed10000, direct CB and generic_wrong target comparisons remain in CB_AUDITORY_CONTINUATION_RESULTS.md with their own paired coverage. A whole target adaptation/readout inner-person selector is not implemented or claimed by this finite source-dev sensitivity.
