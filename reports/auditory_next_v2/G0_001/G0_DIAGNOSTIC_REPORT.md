# G0 first diagnostic stage

All existing shared metrics are recalculated, including the 58-group all-channel cohort. The original supervised CNN head is evaluated separately on its actual training groups and held-out groups; the old table describes refitted logistic probes. These training scores do not measure generalization. Encoder diagnostics and projector diagnostics remain distinct.

Temporal roles are frozen from complete original 30 s blocks (first 60%, last 40%), with effective causal-filter and three-event context dependencies removed at the boundary. No within-child readout has been fitted in this stage. The offline bridge reports actual event ordinal/sample/code matching and awaits its prespecified readouts. Float64 spatial reconstruction is checked on every stored epoch including QC rejects; this is an algebra test, not a neural-source interpretation.
