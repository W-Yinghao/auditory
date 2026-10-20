# S35_EPISODE_PRESSURE v1 — two matched first-order pressure levels

2026-10-19. ALN3.5 docs/04, exploratory after the old 3-step episode's very small
functional displacement and current support results were seen. The new
20/100-step outcomes have not been read. No performance gate is introduced.

Reuse exactly the30 source bundles registered in SUPPORT_COVERAGE_DESIGN:
DTU5person×2content folds×local/CBpre, private5person folds×local/CBpre, all
NCE3401. Each has two pressure units,20 and100 support optimizer steps per
source episode. Each pressure uses independent ordinary and episode
continuations from the identical frozen source in both legitimate inner and
outer stages:60 units,240 source continuations,100 encoder updates apiece.

Inner DTU models are the actual data_inner_v1 sources with inner/outer people
excluded from encoder and target-statistics training. Inner evaluation uses
the original source-ES content; it is not new-person plus new-content model
selection. Private inner models are actual private_episode_v2 inner_source
checkpoints, trained after removing the inner children, never relabelled outer
models. Missing inner checkpoints block only their own new units. Stage record,
checkpoint, parent-plan, source-code, fit/cal/evaluation IDs are preserved.

Each source episode draws one source-training person and uses guarded support P
and later fit-only Q. All full-context guards and inherited preprocessing
limitations are as in SUPPORT_COVERAGE_DESIGN. The source encoder may have
learned from these source people: this is intentional source training, not
inner evaluation. The two regimes share exactly the person/P/Q/anchor random
stream and support initialization seeds. Their stream hashes, exposure and
step counts must agree. Source P is the complete safe front30% region. Source
episode adapters are freshly initialized lowrank_spatial rank4, A~N(0,.01),
B=0, Adam1e-3. The private source and target episode adapter stays spatial;
the separate support-coverage intervention's private output-rank4 is not
silently substituted here.

Ordinary runs the same20/100 support sham steps, then queries the unadapted
encoder. Episode freezes the learned A/B and queries the adapted encoder;
this is first order. Encoder AdamW weight_decay1e-4, local1e-4 / CB3e-5,
100-update cosine, eval-with-grad are unchanged. Each regime includes identical
source-only diagnostic branches and records actual support/query exposure,
support/encoder updates, trainable parameters, wall time and peak GPU memory.
Equal update counts are not called equal FLOPs.

At each update, before taking the declared encoder step, record BA norm,
input/representation relative changes, probability TV, actual registered
query objective losses, support gradient norms and ordinary/episode encoder
gradient cosine at the same current state. Final continuation displacement
cosines are also recorded. A zero-vector cosine is null, not0 or1. All pressure
diagnostics use source-fit data, never outer outcomes. Their magnitude does
not gate evaluation and never automatically extends the budget to1000 steps.
Source CS is not added; the shared adapter helper nevertheless detects constant
CS label kernels and retains identity output with zero_signal_single_class_CS.

Target evaluation uses the identical guarded Q across source/ordinary/episode,
U30 and all five U10 draws351410–351414. Every configuration reports fixed
target steps0,5,20. Direct fixed20 episode−ordinary/source differences are
retained for each pressure level. Separately, an independent-inner-person
policy chooses among source or the corresponding continuation ×{0,5,20}, by
equal-person true NLL, separately for each support policy and readout. Five
U10 draws are averaged within identity before selection. Complete common
inner identities and full candidate-risk tables are stored. Exact ties favor
source, then fewer steps. Source fallback and selected0-step never stand in
for nonzero adaptation gain. Outer Q outcomes cannot change any choice.

Native/unified DTU and native/linear private are separate metrics. Full
cross-architecture private differences remain access-and-recipe contrasts.
Families are dataset/architecture/readout/metric/pressure, with fixed20 terms
episode−ordinary, episode−source, ordinary−source and the separately selected
episode-policy−ordinary-policy term at U10/U30. Risk signs are reference−candidate,
AUC candidate−reference. Average U10 repeats then DTU content folds within
identity; expected independent n44/64, never units×people. Use the declared
exploratory4000 whole-person group-stratified fixed-SE max-|z*| procedure with
complete coverage, missing reasons and nonregular cases retained.

CPU tests, exact plan/source binding and a GPU engineering probe precede the
registered production. The probe covers both tasks/architectures/pressures;
it uses two encoder updates but the full20/100 support pressure, full source
readouts and one inner/outer evaluation person. Probe rows/checkpoints are
separate from production,100-update scheduler horizons are never confused.
No oldsource,plan,checkpoint,queue or hold is edited. All computation uses
Slurm; runfill GPU workers are submitted only by the global root scheduler.
