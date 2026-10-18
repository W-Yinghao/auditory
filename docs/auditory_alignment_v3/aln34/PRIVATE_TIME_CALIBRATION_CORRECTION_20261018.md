# Private current/time calibration execution v2

Recorded after inspecting v1 failure 1045418 and training-side diagnostic 1045968.
No child-level test outcome was used to choose this numerical correction. Existing
v1 aggregate results and the 26 completed units were already available. The v1
plan, code, caches, failed marker and log remain unchanged.

The failed unit ALN34P_5551c74e7a9b79f8 (local CS) reaches the positive-slope lower
bound in the pre-stimulus window. The registered L-BFGS-B fit reports ABNORMAL
after its default 20 line-search steps. Training-only replay gives projected
gradient 1.7351e-8. Allowing 100 line-search steps converges with objective change
below 6e-15. This is a numerical termination issue, not a missing scientific
outcome or a justification to drop the window, child or model.

Execution v2 first calls the identical historical fit. Successful fits are
returned unchanged. Only its explicit optimizer-failure exception enables a
retry from the same initialization, using the same objective, weights, l2,
positive-slope bound, ftol, gtol and maxiter, with maxls=100. A fallback must report
success, finite values, a feasible slope and projected-gradient infinity norm
at most 1e-7. Otherwise the new execution also fails. No test-data fallback and
no efficacy threshold is introduced. Every fallback is recorded with input hashes.

Register all 130 original units with new IDs derived from the original unit and
this correction hash. Reuse the 26 successful v1 records with exact source hashes
and explicit reuse provenance. For outstanding units reuse the original frozen
embedding extraction and compatible cache; training, targets, folds, support,
queries, windows, candidate steps and endpoints remain unchanged. New results
and aggregate reports live under v2 paths. The first full v2 GPU validation uses
the exact failed unit and must actually exercise the numerical fallback.
