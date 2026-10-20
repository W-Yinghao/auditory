# ALN3.5 APwrong paired analysis

This exploratory analysis is registered before any new target output exists.
Original public-prior conclusions and outputs remain visible. Training is fixed
by the separately sealed APwrong plan; this file cannot change a model, support
set, checkpoint, window or stopping point.

For DTU/FAU, report mode-T unified regular query NLL in bits. For private_bdf,
report the original positive-affine native NLL in bits and AUC, separately.
Every endpoint has three contrasts: AP−S, APwrong−S, AP−APwrong. The first two
reuse compatible original S cells; the last uses the new matched AP and APwrong.
Risk differences are reference minus candidate; AUC differences are candidate
minus reference. The historical original AP is retained separately because its
sampler and full candidate trajectory are not this equal-budget comparison.

Each contrast uses its own complete matching target cells. Verify the actual
input/target view, split, normalization access, identities, hearing groups,
candidate counts and per-person query counts before pairing. Average matched
cell differences within each person. Thus folds and seed never inflate n.
Missing or nonfinite endpoints remain listed, without imputation, positive-score
gates or post-result endpoint selection. Incomplete analyses disclose coverage.

Use the unchanged prior33 analysis / SCI_R1 statistics: 4,000 identity bootstrap-t
replicates; percentile intervals secondary. Each dataset × endpoint forms a
separate family of three contrasts, with simultaneous max-t on identities common
to the available contrasts and their actual n. Pointwise intervals retain each
contrast's own paired people. Intervals condition on available fitted models and
do not estimate a donor-training population or multi-seed distribution.

No new hearing-group contrast is automatically added by this script. It preserves
the inherited group labels and prevents the always-training FAU identities from
entering evaluation. Group-level research remains authorized as its own named
analysis. Report all signs; AP over wrong alone cannot establish improvement over S.
