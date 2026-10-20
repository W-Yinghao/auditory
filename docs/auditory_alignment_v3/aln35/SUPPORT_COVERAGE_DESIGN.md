# S35_SUPPORT_COVERAGE v1 — frozen source, fixed query, bounded support policies

2026-10-19. Exploratory implementation of ALN3.5 docs/04, after the published
ALN3.4 support/adaptation results were seen. No new outer results have been read.

Exactly DTU and private_bdf, NCE, seed3401, effective local and CBpre. DTU uses
all 5 person folds × 2 content folds × 2 architectures (20 bundles); private
uses 5 folds × 2 architectures (10). Parents are parsed from data_inner_v1 and
private_episode_v2, retaining exact source records/checkpoints and original
input/target/readout contracts. Original results and queues are unchanged.

DTU P is the first round(0.3N) available segments in the registered EEG bank
order; Q is the remaining segments. Every evaluation-grid anchor's complete
context is checked against the first Q segment start. Unsafe P segments are
excluded before any selector. Segment-start masking of aligned local/CB is
retained. The original available segment count defines floor(0.1N).

Private P is the first ceil(0.3B) physical blocks, Q the remaining blocks;
the old support[:-1]/query[1:] boundary exclusions precede a shared full-epoch
[-200,+600) ms guard. Onset seconds are reconstructed from the immutable GX
stage through the exact accepted/history inclusion masks and checked against
the loaded trial labels/blocks/history. P rows whose epoch end crosses the first
Q epoch start are removed. Q equals private_episode_v2, but is generally not
identical to native-science Q (which did not drop the boundary query). U10 uses
floor(0.1 × original eligible trials), capped by safe P, not 10% of blocks.

Both contracts inherit offline filtering and within-record normalisation using
the complete record. We audit and declare that preprocessing access; the guard
establishes direct sample/context separation, not causal isolation of raw
preprocessing. Source/readout identities remain separately excluded. Frozen
event/sample geometry is private binding metadata, not a newly authorized raw
event publication. Per-person public summaries use counts, spans and hashes.

U10 uses all five fixed seeds351410–351414, without replacement inside P. U30 is
all safe P. C10 has the same n10: private class-balanced quotas with shortage
redistribution; DTU content-group round robin. H10 is private only, prioritizing
uncovered history bins, then uncovered P time thirds, then lower bin/third/cell
counts. Fixed SHA256 ties never use Q labels/scores. Metadata, label and fitting
rows are separate ledgers. C10/H10's P-wide pre-existing stimulus-log access is
explicit; no equal ten-percent deployment-label budget claim is made.

Each source has zero_step, probability_only and rank4_fixed20. T in{.5,1,2}
minimizes support true NLL, exact ties T=1; no legal support risk means T=1 with
a reason. DTU support candidates are only the selected support stimuli, never
Q labels. DTU rank4 is input lowrank_spatial with NCE, private rank4 is the
native-science output residual fitted by the frozen source linear probe's BCE.
Both use Adam1e-3 and exactly20 requested steps. Empty support retains identity
outputs; missing AUC retains all other endpoints and the child. Private linear
is the primary science interface, native calibrated scores are a supplement.
DTU native and unified are separate outcomes. Private local/CB access differs
and is not an isolated pretraining effect.

Families are fixed separately by dataset/architecture/readout/metric. Terms
are U30−U10, C10−U10, H10−U10(private) for each method, and rank4−zero,
rank4−probability for each support rule. Risks use reference−candidate; AUC
candidate−reference. Average the five U10 draws within identity, then repeated
DTU content folds; folds/seeds do not increase n. Expected n is44 DTU and64
private, with group strata preserved. Complete common-person coverage and
missing reasons precede exploratory4000 whole-person stratified bootstrap,
fixed-SE max-|z*| intervals. Nonregular terms retain points/coverage and no CI.

The plan binds source code/design, source execution/checkpoint/parent-plan
hashes, candidate/readout contracts and restricted P/Q geometry. CPU tests and
geometry audit precede one GPU engineering probe with four dataset/architecture
interfaces. Probe uses full sources/readouts and20 steps, one held person per
bundle; its records are isolated from production. No performance threshold.

All computation is Slurm-only; GPU runfill and the project-wide10-GPU cap.
The root scheduler alone submits production workers. Missing checkpoints block
only their dependent units. Nothing clears historical holds or deletes assets.
