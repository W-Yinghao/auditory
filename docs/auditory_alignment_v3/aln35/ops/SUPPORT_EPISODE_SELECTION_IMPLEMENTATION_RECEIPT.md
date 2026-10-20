# Bounded support / episode / source-selection implementation receipt

2026-10-19. This receipt records implementation and engineering checks, not
finished new scientific experiments. No GPU was submitted by the implementing
subagent; root coordinates the common runfill10-GPU fleet.

## Support coverage

- Entry: auditory_alignment_v3.aln35.support_coverage; Slurm wrapper
  slurm/aln35_support_coverage.sbatch. Read-only fleet_status lane s35_support.
- CPU1047286:11 tests passed, real metadata binding passed,30 bundles frozen.
  Plan SHA256 bd267091dab911448c6981455504f2b17f5ae782711a71ed687028a1ec832b65.
- Root GPU probe1047300 passed all four dataset/architecture interfaces:
  DTU local20.0s, DTU CB44.1s, private local4.0s, private CB6.2s.
  Each uses the full source/readout,20 target steps and one held person; these
  timings are engineering samples, not production runtime forecasts.
- U10 five fixed repeats/U30/C10/privateH10; zero/T-only/rank4-fixed20;
  common guarded Q; private trial-vs-block count separation; P-wide metadata
  budget separate from fitting rows; no query-outcome selection.
- Private uses the native-science output residual; DTU uses input spatial
  rank4. Direct context guards are valid while inherited full-record offline
  filtering/normalisation is explicitly declared, without a causal-isolation
  claim. Restricted event/sample bindings must not be newly published.

## Episode pressure

- Entry: auditory_alignment_v3.aln35.episode_pressure; wrapper
  slurm/aln35_episode_pressure.sbatch; lane s35_episode.
- CPU1047299:6 tests passed,60 pressure bundles frozen (30 sources×20/100),
 240 ordinary/episode inner/outer source continuations.
  Plan SHA256 ae2188c200d61a0616d07ad60edb53b8fb8d96df6df5454e3665d52f2919b171.
- Actual independent inner sources and whole-pipeline exclusion; DTU inner
  uses original source-ES content, not an unseen-content claim. Matched sham
  support computation,100 encoder updates and fixed target20 versus selected
  source/continuation×{0,5,20} are separately recorded.
- Per-update source-only BA/input/representation/probability/gradient
  diagnostics; undefined zero-vector cosine; fixed20/100 pressures with no
  performance gate. New shared helper preserves zero-signal single-class CS
  identity output without altering historical CS executions.
-58/60 initial dependency paths ready. Two private CB fold0 parents were
  completed through explicit legacy-compatible reuse and retain their actual
  older inner-source storage identity. A scoped successor resolves those two.

## Exact legacy-inner lineage successor

- Entry: auditory_alignment_v3.aln35.episode_lineage_v2; wrapper
  slurm/aln35_episode_lineage.sbatch; lane s35_episode_lineage.
- CPU1047320:4 tests and actual source/plan/checkpoint/exclusion checks passed.
  Plan SHA256 aa648030ccf89a27e4a52d23862fc5454e3c20da170aa88bcee0e37f1251c359.
- Explicit old-to-new two-unit mapping in supersedes_dependency_only. Old
  frozen files remain byte-identical. Reuse original
  ALN34PE_909c395faaddca63 inner source, whose checkpoint digest is
  56a864fe1aaebb52e86839237d37312f0820cd5ad2742fed3c5a58d1e1ab8171.
  No new source training or fabricated v2 record. Coverage is58+2=60.

## Matched updates and true-risk selection

- Entries: auditory_alignment_v3.aln35.matched_updates and selection_policy;
  GPU wrapper slurm/aln35_matched_updates.sbatch, lane s35_matched.
  selection_policy is a JSON-only dependent rollup, not another GPU queue;
  refresh follows completed units inside Slurm, or use the CPU wrapper
  slurm/aln35_selection_refresh.sbatch.
- CPU1047310 audited30 DTU NCE3401 local/CBpre/CBrand sources. All30 existing
  outer100% long-cosine .25/.5/1 snapshot triples are present and match actual
  update counters and immutable execution/code identity. No short1x substitute.
- CPU1047316:7 tests passed and120 trajectory rows frozen:90 bounded new
  inner50/100 and outer50 trajectories plus30 outer100 snapshot reuses.
  Plan SHA256 b2442196bf98a2a321d8406ea2f829611bb10c6876cfff16849a8fb9ff46014e.
- U uses the actual inherited sampler update count. Both EEG population arms
  share exact update-level LR and the original2E×floor(n_fit/32) long horizon,
  which can differ from2U. Full legal source audio statistics remain common;
  EEG/readout/calibration identities are actually halved. Inner source audio
  and EEG exclude inner people throughout.
- Candidates0/.25/.5/1 are common to inherited gain and new true-risk
  selectors. Native/unified rules remain separate. Inner-only policy is
  written immutably before outer records are opened; outer applies the chosen
  relative candidate position. FixedU population effects and policy effects
  remain separate. All per-person candidate/query hashes are retained.

## Remaining execution

Root owns GPU probe and production submission. Support probe has passed;
episode, lineage and matched probes/results require their actual receipts.
CPU plan validation alone is not evidence of successful new training.
No old holds, queue state, archived source, checkpoint, AGENTS or shared
package initializer was changed by this implementation. No GitHub push.

## Independent stage summary and later probe evidence

2026-10-19 update: episode probe1047304 has an actual passing receipt for all
eight dataset/architecture/pressure interfaces. Matched probe1047332 has an
actual passing receipt for all six local/CBpre/CBrand inner-half/outer-reuse
interfaces. These are engineering checks, not completed production panels.
Slurm accounting was temporarily unavailable (localhost6819 connection
refused); passing receipts/logs and squeue departure are the available evidence.

The independent CPU summary is
auditory_alignment_v3.aln35.support_experiment_summary, with wrapper
slurm/aln35_support_summary.sbatch (2CPU,12GB,30minutes). It imports the
unchanged package fixed-SE max-|z*| statistics, no training modules. It can
also execute directly inside an existing Slurm CPU allocation. It never
submits jobs, fits a selector, reads EEG/checkpoints or changes frozen inputs.

Final CPU1047395 passed19 tests and created a real interim snapshot with zero
validation issues: support2/30,episode0/60,matched0/120,selection0/60. Episode
uses58 original bindings plus2 lineage successors; no double counting.
All290 dataset/configuration/readout/metric/pressure/fraction families are
declared independently of availability. Expected people remain44DTU/64private;
U10's five draws average within person before two DTU content cells. Current
support results do not yet form complete paired two-content-fold people.

Analysis version S35_SUPPORT_SUMMARY_v1.1_endpoint_units_and_diagnostics;
codeSHA95d7f97993afd531724da7ac597249f03380aaafe05e5fec34028c798daed620.
Root review corrected private NLL/wrong-NLL/mismatch-gain units to bits/trial,
with DTU remaining bits/query. The normalized-row/spec unit consistency test
passed. Earlier snapshots1047386/1047393 remain unchanged and the amendment
records that two support production units had been observed. No numerical
effect, family, subject or required cell was changed by that correction.

Discovery pointer:
private/auditory_alignment_v3/aln35/support_summary_v1/latest.json.
Snapshot:job_1047395_20261019T022558873950Z. Private snapshot contains summary,
specs, exact input hashes, inventory, per-person normalized rows, detailed
support/access budgets and source-only diagnostics. Results copy contains
summary/REPORT under results/auditory_alignment_v3/aln35/support_summary_v1.
Compact diagnostics distinguish source units/policy decisions from unique
people and retain zero-step/source-fallback rates, pressure/cost evidence and
undefined cosine. Every refresh writes a new job/timestamp snapshot.

Unfinished scientific panels are factual dependencies and remain active;
the summary is usable now and will grow with production records. Actual
selection policies are consumed only after the existing inner-only refresh
has written them. Missing policy refresh is named separately from missing
trajectories. Invalid units or query/candidate/initialization/budget pairs
produce explicit validation issues and exit2 after saving independent valid
evidence; ordinary incomplete coverage exits0 as interim. Root owns loop
integration and all GPU scheduling. No additional GPU was submitted here.
