# ALN3.5 CB saved-state execution receipt

The bounded DTU/seed3401/generic_paired state sensitivity is complete. No donor
or target was retrained. CPU1047318 passed six tests and froze plan
`b39e6fc88c277743ccf90f3e7761172dbffda1bbd385d96c7305b3d934478c3a`.
Root submitted the runfill A100 engineering probe1047334 and full diagnostic1047349;
both passed. The read-only `cb_audio_state.fleet_status()` now reports completion.

Four original snapshots at0/2500/5000/10000 were loaded, with exact checkpoint,
donor, manifest and original plan provenance. All four evaluations reproduced
the original32-batch source-dev stream SHA
`8c90dd262c2bfc01fdb02a2a0047f55a7e1dfdb09ccf8c93bb0c3f710ce131a5`.
The largest replay difference from the original risk was4.18e-5 nats at state0;
the trained-state differences were at most1.53e-7 nats. Replay risks are diagnostic
and do not reselect a state.

The originally recorded source-dev NCE values select10000. This explicitly
limited donor-dev sensitivity is therefore an exact alias of the original
fixed10000 target policy. Its10/10 DTU target cells were validated against the
original row, donor, plan and selected checkpoint hashes and reused. The original
direct CB and generic_wrong comparisons remain unchanged.

On the same256 source-dev anchors, flattened backbone effective rank changed
238.88→140.91→152.44→155.26; donor-readout rank31.17→6.34→6.68→6.53. Relative
backbone parameter movement was0→0.179→0.231→0.249. Most donor-dev risk improvement
occurred before2500 updates, followed by much smaller gains. This motivates an
objective/readout specificity explanation, but rank compression alone does not
establish information loss, catastrophic forgetting or inferior target transfer.
The donor readout is discarded in target fitting. Whole-pipeline target-inner
state selection remains a distinct question and is not claimed here.

Artifacts: `results/auditory_alignment_v3/aln35/cb_audio_state/diagnostics.json`,
`docs/auditory_alignment_v3/aln35/CB_AUDIO_STATE_RESULTS.md`, and private plan,
engineering, completion and target-reuse receipts in
`private/auditory_alignment_v3/aln35/cb_audio_state_v1/`.
Preserve all four original donor snapshots under the existing project storage.
