# N2 v2.1 design lock

This run constructs metadata-only matched bags from the immutable complete event history. It uses k=8, exact previous_code×previous_run_bin common cells, half-separated pools, equal class bag budgets, no replacement, at least two physical blocks per bag with at most four members per block, at least two bags per class/half, and at least three source blocks. All common cells are assessed before any effect is available.

Candidate denominator: 57; candidate×half denominator: 114; eligible candidate×half numerator: 103; matched pair-bag denominator: 361. Support status: DESIGN_SUPPORT_PRESENT.

The original saved imbalance is recorded as a necessary-support limitation only. It does not establish that a newly constructed balanced design is impossible. If support is limited, no EEG contrast is authorized by this run.

The separate metadata diagnostic executed 25 heads (five folds × all metadata plus history, gap, position, and block-span views), lambda=0.01, maxiter=200, with raw fixed-OOF candidate-cluster CE/bAcc and no calibration or selection. H_BAG has 16 columns; required MU/VAR dimensions are 8/8.
