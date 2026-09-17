> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# A readout core, frozen before A outcomes

All coordinates and background models are fit separately inside each outer training identity set. Training summaries use all accepted boundary-eligible trials within each condition and half, then equal-weight both halves and candidates. Test summaries use 20 fixed without-replacement draws of 20 trials per condition and half. The primary 60s alternating blocks retain the frozen 10.823s whole-epoch guard. The predefined early/late split and 40-trial supported subset are reported separately and never replace the primary result. Every half must span at least four supported 60s blocks.

The contrast axis uses training candidate PCA, capped at min(8,n_train-2,numerical_rank), followed by per-axis training standard deviation. Background adjustment regresses the standardized post contrast on independently fitted four-dimensional PCA summaries of post mean, pre contrast and pre mean, plus two class-specific mean log1p peak-to-peak QC values. Ridge alpha=10 is fixed before A outcomes; no test metric selects it. The random projection uses the same dimension and training centering/scaling with a fixed Gaussian/QR basis.

Cosine, dot-product and squared-distance matching matrices are averaged across trial draws before identity bootstrap. Comparisons stay within each encoder fold; only scalar results combine folds. A duplicated bootstrap identity cannot become a nonmatched identity. Post minus pre uses identical bootstrap draws. Zero-norm cosine remains undefined. Pair rotation is descriptive, without exchangeability p-values. Leave-one-candidate sensitivity does not remove a person.

Independent raw filter-reset and additional history/position-balanced sensitivity remain separate required controls. Core output is explicitly INTERIM and cannot claim the full route is complete.
