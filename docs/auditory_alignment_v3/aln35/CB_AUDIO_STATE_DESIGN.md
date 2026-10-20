# ALN3.5 CB auditory saved-state sensitivity

Scope is DTU seed3401 generic_paired, the four existing donor states at
0/2500/5000/10000 updates, without retraining a donor. The original donor
development NCE curve and checkpoint hashes are frozen before any state-policy
target analysis. Select the minimum original correctly paired source-dev NCE,
with exact ties retaining the earlier state. All four states are required.

This is explicitly a **donor-dev selection sensitivity**. It is not an independent
inner-person selection of the complete target adaptation/readout pipeline and
does not answer that stronger question. Original source dev uses held-out
SparrKULee people/content with the inherited exclusion union. No DTU outer query
or target result participates in the rule.

The existing source curve selects10000 (5.11945/4.07993/4.07889/4.07612 nats at
the four states). Consequently the selected-state target policy is exactly the
original fixed10000 policy. Reuse its ten DTU target cells, continuing unfinished
ones in their original lane. Do not repeat target fitting or count the alias as
an additional experiment. Original direct CB and wrong controls remain intact.

The new GPU task only loads the four saved backbone/readout states. It replays
the original32 source-dev batches and records correctly paired NCE risk, original
interval training loss, relative backbone parameter change from state0, and
effective representation rank. Rank uses the first four fixed batches (256
anchors) on flattened backbone tokens and the32-dimensional donor readout;
centered singular-value entropy is computed through the smaller Gram matrix.
Use identical anchors for every state. No target label, group or score selects
the diagnostics. GPU replay differences are disclosed and cannot reselect a state.

Parameter movement alone is not evidence of catastrophic forgetting. Donor-head
development risk and representation rank are not target-transfer performance;
the donor readout is discarded by the unchanged target recipe. This bounded
sensitivity leaves full target-inner selection as a distinct, unclaimed question.

New code and plan are isolated from the original CB auditory lane. Engineering
probe first, then diagnostics through Slurm runfill under the aggregate10-GPU
cap. All original snapshots must remain available; no checkpoint deletion.
