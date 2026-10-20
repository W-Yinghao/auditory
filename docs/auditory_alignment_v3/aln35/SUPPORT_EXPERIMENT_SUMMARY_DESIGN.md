# ALN3.5 support, episode, matched U and true-risk evidence v1

Analysis amendment v1.1,2026-10-19: after the two completed support units were
visible in snapshots1047386/1047393, root review corrected the private NLL,
wrong-NLL and mismatch-gain labels to bits/trial; DTU remains bits/query.
Normalized rows and contrast specs now share the same dataset-aware unit
function. No numerical value, family, person or required cell changed. Both
earlier snapshots are retained byte-for-byte. There were no private production
results in those snapshots. Compact source-pressure/cost diagnostics and
epoch0/source-fallback decision rates were added with explicit unit versus
person denominators. The analysis version and code/design hashes distinguish
the corrected snapshots; this amendment is not a retroactive claim that the
exporter was written before any new result existed.

2026-10-19. This independent CPU exporter implements the already frozen terms
in SUPPORT_COVERAGE_DESIGN, EPISODE_PRESSURE_DESIGN and
MATCHED_UPDATES_SELECTION_DESIGN. The terms were registered before their new
outer results. At exporter implementation, one support production record and
engineering probes existed; no terms, participants, folds or endpoints were
chosen using those outcomes. The exporter is exploratory, with a new code and
analysis identity. Earlier registered analyses remain unchanged.

The expected scientific units are support30, episode60, matched120 and
selection60. Episode merges58 ordinary v1 bindings plus the two explicit
lineage-v2 dependency successors. The two superseded dependency-blocked v1
execution IDs remain on disk but do not add two scientific cells. The merge
checks the source and every pressure/target-step/fold field, allowing only the
declared legacy source-resolution metadata. All plans have explicit immutable
SHA256 bindings. Production unit IDs, full unit configurations and plan hashes
must match; engineering probes and incomplete/failed records never enter.

Independent expected rosters come from frozen support geometry:44 DTU and64
private people. The rosters are not reconstructed from whichever outcomes
arrive. DTU requires content_0 and content_1 per person, while private has one
evaluation cell. Outer subject fold is a person's exclusion membership and
does not create repeat observations. Every U10 cell requires all five fixed
draws351410–351414 and averages them inside the person/content cell before
content-fold averaging. Training seed remains3401; sampling draws are never
new training seeds or independent people. Missing AUC remains missing only in
its AUC family; that person is retained for available NLL/other families.

Families are fixed by dataset, configuration, readout and metric, as already
registered. Support includes U30−U10/C10−U10/(private H10−U10) for each of the
three methods and rank4−zero/rank4−probability for every support rule. Episode
also separates source pressure20/100 and fixed20 versus inner-selected
policies. Fixed20 terms are episode−ordinary, episode−source and
ordinary−source at U10/U30. Policy terms compare selected(source,episode)
with selected(source,ordinary) at U10/U30. The saved inner choice is applied;
the exporter never chooses an outer-best state or pressure. Source-fallback
and zero-step flags remain separate diagnostics.

Matched U compares EEG50 with EEG100 at the exact common U and common long
cosine horizon, separately local/CBpre/CBrand and native/unified. Available
paired trajectories must have identical budget/candidate grids and original
model/head initialization hashes; full legal source-audio access and the
evaluation people must agree, and EEG people must be nested. No short1x state
is substituted. The actual update count, training people, exposures, LR and
reuse/no-new-training ledger are retained.

True-risk versus inherited-gain is a separate family for each EEG fraction,
configuration and readout. It consumes the immutable inner-only policy and
its actual inner/outer record hashes; all four registered states include
epoch0. Applied metrics/query/candidate hashes are checked against the
specific outer trajectory state at the frozen relative candidate index. If
trajectories are ready but the existing CPU policy refresh has not run, the
summary reports that exact dependency. It does not create or change a policy.

Inferential metrics are true-query NLL, wrong-query NLL, mismatch gain,
DTUtop1/rank percentile and privateAUC/Brier. They are separate small families,
never pooled across task units. The three NLL/gain metrics use bits/query for
DTU and bits/trial for private. Risk/Brier/rank signs use reference−candidate;
AUC/top1/mismatch gain use candidate−reference. A lower wrong-query risk is
only the signed diagnostic difference and is not automatically a better
decoder. Probability TV, entropy, temperature and representation change are
retained as per-person descriptive rows, with support counts, coverage,
access-budget and source-only functional-pressure diagnostics in the server
snapshot. No threshold on any of these quantities controls inference or
execution. All favorable, unfavorable, zero and nonregular results remain.

Numerical inference directly imports the package's unchanged
aln35_reference.contrasts implementation. It uses4,000 complete-person
bootstrap draws stratified by the registered hearing group, fixed original
SE and max-|z*| across the declared family; bootstrap seed351001,alpha.05.
Every family uses its shared complete people across all required conditions
and content cells. The output records expected/observed/paired people,
missing cells, actual SE, critical value and simultaneous scope. Singleton,
constant or sparse strata remain nonregular with no CI. No aggregate-CI
subtraction, sample-size inflation, p-value gate or repeated-look stopping
rule is introduced. Repeated interim snapshots are evidence updates, not a
sequentially valid discovery test.

Query hashes, candidate-audio hashes and query counts must agree across all
paired cells, including U10 draws. Support/episode additionally match frozen
safe-query geometry. Source-fit and selection people are explicitly supplied
to the reference validator; an outer person cannot occur in either source
list. Production records store actual subset hashes, but not every explicit
support/query sample ID in the result, so require_full_provenance=false is
intentional. The exporter does not invent IDs or claim an unperformed
explicit-sample leakage audit. It retains the previously audited direct
sample/context guard and the inherited whole-record offline preprocessing
limitation. Private support's output-rank4 and episode's input-spatial-rank4
effects remain separate; private cross-architecture access also differs.

Each Slurm run writes a new job/timestamp snapshot under
private/auditory_alignment_v3/aln35/support_summary_v1/snapshots and a result
copy containing estimates/coverage under results/auditory_alignment_v3/aln35.
Normalized per-person metric rows and detailed source/support diagnostics stay
in the private snapshot. Neither contains raw EEG; no raw event indices or
identity map are exported. A latest.json pointer advances without replacing
snapshots. Actual input bytes, analysis/design/reference hashes and unit
inventory are saved. Missing work is explicitly interim. A bad unit or pair
is retained in the error inventory and excluded as a whole from its dependent
analysis while independent valid work continues. Any validation issue yields
exit code2 after writing the evidence, so monitoring can distinguish it from
ordinary incomplete coverage.

All tests and aggregation run on Slurm CPU. The summary imports no training
module, opens no EEG/checkpoint, fits no model, submits no job, changes no
frozen execution source and has no GPU dependency. Use
slurm/aln35_support_summary.sbatch for validation plus a fresh real snapshot.
