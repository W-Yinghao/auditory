# ALN3.5 execution plan — 2026-10-19

The researcher authorized direct execution of the supplied ALN3.5 package and GPU prioritization. Its 16 workpackages are bound to actual plans, execution IDs and assets in `private/auditory_alignment_v3/aln35/ALN35_BINDINGS.json`. Those are server bindings, not additional independent samples. The supplied standalone ALN3.4 full-experiment document is byte-identical to the package's inherited copy. No whole-project restart or new dataset acquisition is required.

| Workpackage | Actual implementation and scope | Execution/refresh |
|---|---|---|
| INTAKE | Package/source baseline, exact old and new plans, held IDs and checkpoint availability | CPU1047276/1047281/1047366 |
| PRE_CORRECTION | 68 native-private pre/TG records; actual zero-input access correction, original values retained | CPU1047290, independent1047301 |
| PAIRED_SCIENCE | 10 science families/30 contrasts plus 3 original-main-endpoint group families/10 contrasts | Complete actual paired coverage; CPU1047290 |
| CLOSE_CB_AUDIO | Continue original144-unit donor/direct/paired/wrong panel | Original lane, two rotating slots |
| CB_AUDIO_STATE | DTU3401 generic_paired0/2500/5000/10000; source-dev minimum10000 | Reuses all10 original target cells; one bounded four-state GPU diagnostic |
| CLOSE_D_FUSION | Original independent-inner sources,120 adaptation and30 strong-fusion units | Source dependencies first; no completed-unit retraining |
| CONTINUE_OTHER_VALID | Original private, attention, prior-LOO, learning-budget, episode and breadth panels | Preserve exact active work and scoped holds |
| AP_WRONG | Three target-excluded paired donors, six models,78,874 updates/model;50 target cells, NCE3401 only | Original sampler cannot guarantee legal wrong matching; use a common revised sampler for both new arms, fully CPU-audited236,622 paired steps; original AP remains separate |
| SUPPORT_COVERAGE |30 source bundles, DTU/private local/CBpre, fixed queries; U10 five draws/U30/C10/private H10 | Reuse sources; bounded calibration/rank4 adaptation. P30 metadata access is disclosed separately from fit sample counts |
| EPISODE_PRESSURE |60 scientific bundles; matched ordinary/episode100 encoder updates,20/100 inner support steps; fixed20 and lawful inner-selected target rules |58 original source lineages plus2 exact-compatible legacy-source successors; never count both parent and successor as additional experiments |
| TRUE_RISK_SELECTION |60 source-only policies, same epoch0/.25/.5/1U states, true-query risk versus inherited gain | Shares matched-updates trajectories; policy committed before opening paired outer metrics |
| MATCHED_UPDATES |DTU local/CBpre/CBrand3401;50% versus100% EEG source people at equal actual optimizer updates |120 trajectories:90 limited new fits and30 compatible original full-data snapshot replays. Original2x cosine horizon retained; source audio coordinate access held common and disclosed |
| FUSION_ATTRIBUTION |Fixed-CB temperature/shrinkage/repeated-seed controls, actual mixture and local-score permutations on identical queries |Existing inner/outer score caches; CPU refresh as missing original fusion sources complete |
| BRIDGE_FACTOR |DTU AP/XM andFAU XP/XM, two frozen B mappings×T1/source-calibrated T,40 original zero-shot units |Four bounded frozen-encoder feature replays, then CPU only. Original full B and alpha retained; no donor training |
| HISTORY_INTERFACE |S/AP/J*/XM×5 source folds; equal-calibration history control and strict other-block twin |20/20 sources complete,64 children; CPU1047305, independent1047311 |
| ATTENTION_ORDER |Fixed10/20-second trained integrators, original/reverse/permuted order and unchanged mean-score control |Existing score arrays, separate duration/readout families; refresh as original160-unit panel completes |

New comparative analyses use the supplied fixed-original-SE max-|z*| identity bootstrap with explicit expected rosters, required seeds/content cells and missingness. Historical registered bootstrap-t/max-t outputs remain unchanged. The APwrong initial analysis-only v1 accidentally inherited the old method; its zero-result seal is preserved and a separately registered v2 corrects that before new target results. Descriptive history/bridge sensitivities do not introduce an undeclared significance family.

The single GPU authority is `private/auditory_alignment_v3/aln35/maintain_fleet.py` (CPU1047289). All GPU work is runfill, aggregate cap10, no P100, with A100/L40S preference and broader fast-card eligibility when waiting would waste capacity. New tasks require matching engineering receipts, never a performance threshold. Valid running jobs finish normally. Older low-priority curve repeats remain scheduled without displacing the new dependency and mechanism comparisons.

Evidence service1047358 replaces the oldv11 service under the same singleton lock. It retains all old aggregation and adds change-triggered new CPU analyses, at most two child analyses at once and normally no more than one refresh per task per30minutes. Every CPU submission checks the shared normal queue, counting array tasks. Unchanged inputs do not trigger repeated analyses. A failed task is recorded for scoped review. Fleet, evidence and checkpoint services have bounded Slurm allocations and renewal paths; no `scontrol` is used.

APwrong analysisv2 and support/episode/matched/selection summaryv1.1 are enrolled by1047394/1047397. The latter passed19tests and an actual automatic refresh1047401 with0validation issues. Its earlier unit-label correction preserves all prior snapshots and numerical values. The finite bridge chain is GPU1047390 → afterok CPUanalysisv2 1047402 → afterok independentverification1047403. Its historical forward-replay differences and v1 failed audit are retained; the new analysis strictly verifies the original score formula and temperature-rank invariance on each common cache. These queued jobs are not reported as completed.

The next research decision follows the complete finite comparisons: distinguish correct auditory pairing from common training, support amount from coverage, useful source learning from calibration, and learned temporal integration from encoder transfer. Do not automatically multiply the matrix by more seeds, backbones, losses or windows. Existing compatible CS and REVE references continue.
