# S35 matched updates and independent-person true-risk selection v1

2026-10-19, exploratory after the ALN3.4 learning-budget and data-curve snapshots
were seen. This implements only ALN3.5 docs/03 §§3.4–3.5: DTU,NCE3401,
aligned-local/CBpre/CBrand,5person×2content folds. No extra losses, windows,
seeds, cohorts or architecture grid. Original gain results remain unchanged.

There are30 source bundles. Each has legal inner/outer training stages and
50/100% EEG-person arms,120 trajectory records. Exactly30 outer100% sources
reuse their compatible learning_budget_v2 snapshots; only90 specified source
trajectories require fitting. The reuse audit (Slurm1047310) found all30
outer trajectories' required .25/.5/1 states available, with correct immutable
execution/code hashes and optimizer step counters. The old short1x-cosine
endpoints are not used as equivalent states. Existing original-source best
checkpoints do not provide an unrecorded inner training trajectory, so the
limited inner trajectories must be trained; this does not restart old panels.

U is the actual number of optimizer updates in the compatible full-data source
budget, verified against registered source records by replaying the original
metadata sampler and anchor-phase RNG consumption on CPU. The inherited
sampler can emit partial batches: original cosine horizon2E×floor(n_fit/32)
can differ from2U. Both50/100% arms use that same exact update-level horizon,
no warmup, same initialization/optimizer/groups and the same count U. Thus we
retain the actual original long-cosine LR path rather than an approximate
epoch equivalence.50% repeats its own registered participant-balanced unique-
stimulus sampler until U, with real per-person/anchor/repetition exposure
reported. Equal updates are not equal independent samples or equal FLOPs.

50% identities use the already registered group-stratified deterministic
SHA256 prefix rule. Inner sources first exclude outer and inner people, then
apply the50% rule within the remaining source people. EEG gradient fit,
source-ES calibration and readout fitting use only the chosen EEG people.
Audio target statistics use the same full legal source-training audio in
both EEG arms; inner uses only inner-training audio, not outer statistics.
This is a change in EEG training population, not a claim that all information
or audio exposure halves. Fixed generic FM pretraining provenance is inherited;
no auditory donor/bridge is newly introduced. Current task-specific fitted
objects exclude the inner people at all stages.

The model, fixed32 audio geometry, aligned1000 window/masking, NCE objective,
AdamW weight_decay1e-4, local1e-3 / registered CB backbone/head LRs, train-mode
updates and native/unified source-side interfaces match registered recipes.
New code stops at exact updates and captures states; it never edits a trainer
used by an old running job. Nonfinite updates are failures and are not silently
skipped to change a matched budget. Evaluation preserves training RNG state.

The finite shared candidate set is epoch0 plus relative positions .25,.5,1 of
the registered baseline epoch budget along the2x-cosine trajectory. Actual
update counters at those positions are frozen separately for inner/outer;
the selected relative candidate position transfers to the corresponding
outer source. Both the inherited ES_true−ES_mismatch criterion and new true
risk selector see these same four candidates. This bounded candidate family
does not replace the older, denser original gain-selection curve.

True-risk selection minimizes equal-inner-person query NLL, separately for
native and unified. Original source-ES content is used for inner people;
this is whole task-pipeline new-person selection under source-side content,
not simultaneously new-person and held-out-content development. Personal
adaptation is explicitly0 steps in this selector diagnostic. Epoch0 is a real
candidate. Ties favor the earliest/simplest state. No outer labels/outcomes
choose a model, training state, fraction or stopping point.

The selector accepts only the inner result, writes an immutable policy with
all candidate gains/per-person true risks and code/plan/source hashes, and only
then opens the outer result to apply that frozen relative position. Outer
states may have been evaluated as fixed endpoints, but their values are not
inputs to the selection function. Policy files retain actual inner coverage,
epoch0 selection and no-common-person reasons.

Primary matched-population effects are50%-100% at fixedU; source-selected
states are separate sensitivities. True-risk-vs-gain effects are paired within
person on identical Q/candidate hashes. Folds are the person's exclusion
membership; average the two DTU content-fold measurements within identity.
Expected44 independent DTU people, with hearing strata preserved. New families
are fixed by architecture, readout and metric, with population and selection
terms declared separately. Risks reference−candidate; top1 candidate−reference.
Exploratory4000 group-stratified whole-person fixed-SE max-|z*| inference,
coverage/missing/nonregular diagnostics; never subtract separate aggregate CIs.

The new GPU worker writes trajectories; its tiny selection refresh consumes
only completed JSON on the same Slurm allocation and does no fitting. It can
also run on CPU via slurm/aln35_selection_refresh.sbatch. It is not a second
GPU training queue. Source dependency and failed-unit statuses are explicit.
Engineering smoke exercises all three architecture/initialization cases,
four-update isolated inner-half trajectories and actual reused outer-full
interfaces. Its horizon is isolated and never production input. Production
requires the matching passing probe; no metric threshold.

All caches/checkpoints are in the established/projects private root. Every
job is Slurm; GPUs runfill under the root scheduler's aggregate10-GPU cap.
No historical hold, completed result, source hash, checkpoint or queue is reset.
