# ALN3.5 frozen attention order

CPU1047312; 94/160 original units available. Reconstructed original windows/metrics agree with saved production results. Mean-score outputs are exactly unchanged by ordering. All incomplete identity/seed cells remain explicit in contrasts.json; this does not mark the original attention training complete.

Fixed mean and learned-integrator order effects, fixed CB-versus-local transfer and CB integrator-versus-mean gains are separate families. New fixed-SE max-|z*| intervals do not replace the old sparse max-t outputs. Five-second single-segment windows are skipped; no behavioral RT is measured.

Results: `results/auditory_alignment_v3/aln35/attention/run_1047312/contrasts.json`.
