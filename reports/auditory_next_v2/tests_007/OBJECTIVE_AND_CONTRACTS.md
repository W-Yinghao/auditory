# v2 implementation gates

The installed sklearn binary MLP objective is weighted mean BCE + alpha/(2 × sum weights) times the sum of squared weight matrices; biases are unpenalized. The replacement uses explicit L2 and Adam weight_decay=0. New-route lambda=0.001 has a separate, population-normalized meaning. Objective, logits, penalty and every gradient were compared at identical float64 parameters; a finite-difference check is also recorded. Passing numerical algebra does not establish convergence of any real-data head. Full required T01–T26 route integration remains a separate gate.
