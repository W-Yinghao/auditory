# ALN3.5 evening progress — 2026-10-19, 18:53–19:00 CEST

## V100 update — 23:03 CEST

The researcher has authorized V100 use. Matched production and a recovered
checkpoint have now completed on actual V10016GB; the remaining bounded
compatibility phases enable their lanes automatically as they pass. A
pre-existing CUDA RNG checkpoint-loader error was repaired in a versioned
wrapper, with exact RNG-continuation verification and preserved failure
history. Original trainers and plans remain unchanged. The new fleet runs as
step1047358.2 inside the existing evidence allocation; old fleet1047289 exited
cleanly. Read [V100_OPERATIONS_20261019.md](V100_OPERATIONS_20261019.md) for
the current authority, receipts, automatic routing and still-running probes.
The two-service allocation descriptions below are earlier snapshots.

## Later check and capacity adjustment — 21:57–21:58 CEST

CB auditory is now complete at144/144, including9/9 donors. Live completion
has advanced to D adaptation91/120, effective new episode39/60 (37 original
plus2 lineage successors), matched trajectories88/120 and true-risk selection
28/60. Doubled budgets are DTU81/150 and breadth42/75; data curves are
DTU175/440 and breadth73/300. The inner-person sources remain complete and
are excluded from those curve denominators. Automatic validated summary
1050005 at21:49 covered38/60 episode,87/120 matched and27/60 selection with
zero validation issues; the later live counts are not a new aggregate analysis.
Fleet and evidence logs/state show no new error or active failed analysis.

Completed lanes had left only seven single-worker training lanes. After a
passing Slurm `srun` check inside existing CPU allocation1047289, the episode,
breadth-budget and breadth-curve allowances were each increased from1 to2.
The check validated the existing per-unit claim exclusion/release on the real
filesystem, frozen episode plan/source, live readiness and plugin loading.
The new `episode_capacity_v1` provider only changes allowed worker count and
verifies the original episode source hash on every call. Existing runtime
configuration supports the two breadth changes. The original trainers and
plans remain byte-identical. Matched updates remain single-worker because
their shared selection refresh uses common temporary output paths; increasing
that lane requires a separate serialization change, not just a slot increase.

The installed configurations, backups and passing receipt are in
`private/auditory_alignment_v3/aln35/capacity_20261019/`. Installation was atomic
at21:57:55. The existing fleet admitted episode1050014, breadth-budget1050015
and breadth-curves1050016 at21:58. These retain runfill and
A100/L40S/A40/A30 eligibility. At that immediate check five jobs were running
and three newly submitted jobs pending, with ordinary unit turnover; the
coordinator continues filling the ten allowed slots. No running GPU was
cancelled, no new resident CPU service was added, and no hold or stored
checkpoint was changed. The dedicated CPU-check sbatch wrapper was prepared
but never submitted: the actual successful validation reused the allocated
Slurm CPU service. Fleet1047289 and evidence1047358 remain the two resident
auditory CPU services.

At21:59 the follow-up queue check confirmed all ten slots running: nineA100
and oneA30. Matched1050018 and the second breadth-budget1050019 filled the
remaining slots. The three new concurrency workers had all started, and
selection coverage had advanced to29/60. No pending auditory job remained at
that instant because the submitted work had been admitted; ready registered
work continues to feed the existing automatic replacement loop.

The complete CB result keeps the scientific distinction explicit: auditory
continuation over the generic direct baseline is uncertain (DTU three-seed
mean native gain0.0169bits/query, simultaneous95% interval[-0.0163,0.0500];
FAU native0.0060[-0.0110,0.0231]; Federici native0.0103[-0.0165,0.0371]).
Wrong-audio continuation is substantially worse on DTU/FAU, so beating that
control alone does not establish improvement over the strong direct model.
See `../CB_AUDITORY_CONTINUATION_RESULTS.md` for all modes and contrasts.
The previously registered adaptation, episode and source-side true-risk
selection comparisons continue without expanding the model grid.

## Earlier 18:53–19:00 snapshot (preserved)

Training and the two current CPU services are active. At the queue check,
three auditory runfill GPUs were running (two A100, one A30), with six jobs
pending for `Priority` or `Resources`. This is below the ten-GPU ceiling
because of cluster scheduling, not a research gate or a stopped coordinator.
All pending jobs already accept A100/L40S/A40/A30. No running job was cancelled.

The legacy watcher and checkpoint offloader retired at 04:43 remain stopped.
Fleet1047289 and evidence1047358 have current heartbeats. Their logs contain
no ERROR/PLUGIN_ERROR/Traceback; the current evidence state has no errors and
all four active new-analysis tasks have no failure receipt. The failure files
found in the older directories belong to preserved superseded probes or
previously resolved replay attempts. No new production failure was found.

## Actual execution coverage

| Panel | Complete / registered | Interpretation |
|---|---:|---|
| AP/APwrong | 3/3 paired donors and 50/50 target cells | Complete; analysis v2 refreshed in CPU1048224 |
| Support count/coverage | 30/30 | Complete; full person-level summary available |
| Strong fusion | 30/30 | Complete; attribution analysis CPU1047619, all44 DTU people and3seeds |
| Attention transfer | 160/160 | Complete; fixed-order analysis CPU1049394 |
| Original episode / kernel-CS episode | 80/80 and40/40 | Complete |
| Broad adaptation / fusion / episode | 40/40,15/15,40/40 | Complete |
| Inner-person sources | DTU150/150, breadth75/75 | Downstream source dependencies now complete |
| CB auditory | 141/144 | Three target units remain at this snapshot |
| D adaptation | 83/120 | 37 remain |
| New episode-pressure comparisons | 24/60 | 22 original plus2 lineage successors; never count old superseded parents twice |
| Matched-update trajectories | 62/120 | 58 remain |
| True-risk versus gain policies | 2/60 | Requires both matching inner and outer trajectories; no separate training grid |
| Doubled budgets | DTU76/150, breadth36/75 | Continuing |
| Data curves | DTU160/440, breadth61/300 | Continuing; distinct from the completed inner-person sources |

Support/episode/matched/selection coverage comes from automatic summary
CPU1049708, 18:54:46 CEST, with zero validation issues. These are execution
counts, not independent participant counts. Previously completed TRUE_FULL,
public priors and public/private time-science panels remain complete.

## What the newly complete comparisons show

APwrong is now interpretable on common complete DTU44/FAU67/private64 people,
seed3401. DTU AP and APwrong both improve true risk versus scratch by about
0.0592 and0.0608 bits/query. Their direct difference is−0.00159,
simultaneous95%CI[−0.02542,0.02223]. In private BDF, AP improves AUC versus
scratch by0.00931[0.00152,0.01710], while AP−APwrong is0.00290
[−0.00479,0.01059]. FAU AP−APwrong is−0.02091bits/query
[−0.04378,0.00196]. The correct-pairing advantage is not established in
these comparisons; this is not evidence of equivalence or absence of auditory
information. The matched revised sampler and all old AP results remain explicit.
See `AP_WRONG_RESULTS_V2.md` for all risk/AUC contrasts.

Full fusion attribution now includes44 people, replacing the earlier20-person
interim coverage. Local+CB improves native true risk over direct CB by0.05144
bits/query[0.02640,0.07649], and unified risk by0.04534
[0.02079,0.06990]. Its additional advantage over repeated-CB-seed mixing is
uncertain: native0.02549[−0.00137,0.05236], unified−0.00875
[−0.03227,0.01477]. The earlier native20-person interval should not be used
as the complete result. Local-score permutation controls also remain in the
full report, `FUSION_ATTRIBUTION_RESULTS_1047619.md`. These comparisons do not
by themselves identify a neuroscience mechanism.

The next priority remains the already registered matched-update/whole-pipeline
selection and episode-pressure comparisons. They distinguish general training,
support and selection explanations without enlarging the backbone/loss grid.

## Operational evidence and scheduling decision

CPU1049714 saved a read-only snapshot and compact full-coverage fusion/attention
results under `private/auditory_alignment_v3/aln35/runtime_20261019_evening/`.
The matched lane has62 recorded runtimes, maximum815.96seconds; the new episode
lane has22, maximum2878.23seconds. Those observations are not guarantees for
remaining workloads. The long A30 allocation recently completed another unit
in2714.8seconds and started the next, so its multi-day allocation age is not a
single stalled training run.

Two `sbatch --test-only` checks compared2h and24h matched allocations with
otherwise identical resources. Both returned the same speculative start
2026-10-20T20:34:50. Their reported numbers1049718/1049717 are dry-run identifiers,
not submitted production jobs. There was no observed backfill advantage to
discarding an existing job's queue age, so existing pending jobs were retained.
The estimate is not a completion promise or a reliable bound on actual wait.

Shared `/projects` available space was733.74GiB in CPU1049714. This status check
deleted no files, changed no training sources or holds, and submitted no new
scientific experiments. The one-shot CPU audit has completed; background
services remain limited to the two current auditory services plus temporary
change-triggered analyses.
