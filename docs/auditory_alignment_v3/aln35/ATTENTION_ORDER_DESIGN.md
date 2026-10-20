# ALN3.5 frozen attention order sensitivity

This exploratory CPU analysis reuses each completed `attention_transfer_v1` record's saved segment margins, physical evaluation coordinates and fitted mean/antisymmetric integrators. No source encoder, calibration or integrator is retrained. All 160 registered units remain expected; incomplete coverage is explicit and refreshed as original work completes.

For 10-second and20-second windows, score original, reversed and one deterministic permutation (seed351620, keyed by canonical physical window ID). The same column permutation acts on both candidate presentations, preserving antisymmetry and the segment multiset. Five-second single-segment windows are not permuted. The mean-score value is explicitly reused after checking the floating-point permutation identity, so rounding cannot create an apparent mean-order effect.

Both frozen mean and learned integrators are reported, alongside the inherited inner-selected integrator. Separate families are defined by dataset, architecture, readout and duration: reverse-minus-original and permuted-minus-original true NLL, positive meaning disruption worsens risk. Separate fixed-order families report CBpre versus local under the mean readout, and learned versus mean under CBpre. No family compares different physical window sets; source folds and seeds are averaged within identity. DTU requires3401/3407/3413 and FAU3401, each with both content folds. Full roster derives from original cohort metadata, not available results.

New intervals use the supplied fixed-original-SE identity max-|z*|, B4000, seed351621. The old studentized bootstrap-t attention results remain unchanged; their sparse seed3407 numerical degeneracy remains an old-analysis limitation. A zero empirical order effect is nonregular, not population equivalence. Observation duration is neither neural latency nor a measured behavioral response time; no behavioral RT variable is introduced.

Physical five-second segment length is640 samples, from the unchanged native FAU/DTU loaders'128-Hz constants. Reconstructed original windows, NLL and accuracy must reproduce saved records before any order sensitivity is included.
