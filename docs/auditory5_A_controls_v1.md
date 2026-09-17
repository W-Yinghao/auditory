> Publication copy: aggregate research evidence only; participant-level inputs and outputs remain on the server. Historical running/queued statements are superseded by S4_final_001. See [publication scope](../PUBLICATION.md).

# Route A controls v1

This module is a subsequent control run for the interim Route A result. It
does not edit `route_a.py`, the representation plan, the training runner, or
any completed primary output. It reads the frozen split and Route A feature
caches, then uses the existing outer-fold checkpoints and their stored fit
scopes. No encoder is fitted in this run. The report keeps continuous versus
raw-reset and unbalanced versus history/position-balanced controls separate.

The raw sensitivity reads one HA BDF block at a time. Each fixed A block gets
a new causal `CausalPreprocessor` state. Blocks are never concatenated before
filtering, and the original sample grid stays anchored at sample zero. The
fixed HA20 scalp order is selected explicitly; ear, status and auxiliary BDF
channels cannot enter the average reference. Startup eligibility uses the
measured support guard (at least 20 s), while the block tail uses the frozen
`A_B_embargo_seconds` value (10.823 s). The epoch grid retains the frozen
`-.2` s origin: the 50-sample pre interval ends at zero, and the `.05` s post
interval begins at its native index (62/63 at the audited grid), never at 50.
The original `accepted` and `reject_reason` fields remain unchanged; the
additional `reset_eligible` mask is recorded separately. Every stored epoch
retains its original `trial_id` and event labels.

The history/position control is outcome-blind. For each candidate, half and
stimulus class it selects exactly the configured trial budget from the six
`history_target × position_bin` cells (two history states and three thirds of
the record), with deterministic sampling. The fixed remainder quotas are the
same in every half/class, and twenty independent balanced draws supply the
summary repetition axis. Candidates lacking the frozen cell support or four A
blocks are reported as unsupported; supported candidates remain a valid
subset. This selection is made only in the test summary; training summaries,
PCA, scaling, ridge background adjustment and encoder checkpoints remain
fit-scope local and unchanged.

Private output contains reset ledgers, trial IDs, masks, fold-level control
rows, and the per-fold matrices. A record reset is cached once and reused by
all representation modes. Public output contains the five-fold bootstrap
aggregate for each continuous/reset and unbalanced/balanced control, plus
support status. The paired post-minus-pre interval is computed from the same
identity draws. Missing folds or empty balanced support are reported as
`NEED_CONTROLS`, never as a scientific pass. Each run has a new directory,
input hashes, processing-spec hash and code hash; an existing run is never
overwritten. A missing learned checkpoint is a cache-missing status, never a
request to retrain. The intended command is a Slurm job that invokes
`auditory5.routes.route_a_controls` with the frozen plan and a new run name.
CPU/GPU tests and analyses must be submitted through Slurm.

The control results are sensitivity evidence. They cannot establish cortical
origin, across-day reliability, or clinical auditory ability.
