# M8/M10 open items for wave 3 (from workflow w9f5c7rgr, 2026-10-17)

Lead already fixed: the run_harness.sh refresher-copy sandbox guard (M10 medium item 1); see private/auditory_alignment_v3/aln34/run_harness.sh.before_guard_20261017.

## M8 (final review ok=True)

### Interface

select.py (light: stdlib json/math/os/re; hashed into prior33_bridge, prior33_target and prior33_zeroshot):
- Constants: family ids, FAMILIES, DONOR_FAMILIES, STAGE, GROUP_MEMBERS, MEMBER_TAGS, JOINT="J*", JOINT_CANDIDATES, SLOTS, SCRATCH, LAMBDA_RULE="min_dev_ce_tie1e-4_lambda1", LAMBDA_TIE_BITS, DEFAULT_LIMIT_EP_EQ=60, DECAY_EP_EQ=3, CKPT_SUFFIX.
- Error type: SelectionError(ValueError).
- Row functions: stage_of, canonical_slot, group_members(group), compute_limit(group), names_limit(group), slot_of(row), group_row(row, rows).
  - group_members now requires distinct members of the family's §2.6 set, and spec.lambda_rule equal to LAMBDA_RULE when present.
- Record and λ-rule functions: member_best_ce, lambda_choice, joint_choice(record) (new), member_of(row, group_record), check_group_record(record, group=None) (new).
- Path functions: record_path, load_record, slot_member(slot, rows, out), member_ckpt, stable_ckpt, retained_states(out, group) (new), bridge_npz.
- Pinned donor-record layout:
  - members[M]["best"]["ce_dev"] holds a JSON number for every member; NaN and Infinity count as +inf.
  - An optional joint_choice = joint_choice(record), i.e. {rule, member, ce_dev, tie_bits}. When it is in this form, it must agree with the rule.
  - The flat best_ce_dev alternative was removed.
- A guard at the top of the file returns the stdlib `select` when the file is imported as top-level `select` (prior33/ first on sys.path).

deps.py (light: stdlib json/os/re; not hashed):
- Constants: QUEUE, EXT_OFFSET, EID, ID_LIKE, WEIGHTS, STAGE_RANK, BLOCK_TIER, GROUP_BLOCKS, SLOT_BLOCKS, SCRATCH_BLOCKS, ZS_SUFFIX, ZS_COHORTS, REF_FIELDS, COUNTERS.
- Functions: index(rows), upstreams(row, rows), relation(row, up), zero_shot_mode(row), check_row(row, rows), check_plan(rows) (new), ready(row, rows, out), blocked(row, rows, out), ckpt_deps(row, rows), tier_of, order_key, weight_of, write_queue(out, rows, held=(), bound=None, ext=None).
- write_queue returns {queued, in_scope, held, done, failed, blocked, ready, waiting, remaining, families, unresolved}.
- Any function that takes `rows` accepts a list or a mapping id -> row. Nothing is cached between calls.
- Files written by write_queue:
  - queue_v3_prior.txt: lines eid|idx|up1,up2. Done, failed, ready and waiting rows are listed; blocked rows are not.
  - queue_v3_prior_weights.txt.
  - .remaining and .waiting: one integer each.
  - .blocked: the blocked eids.
  - No counter ends in .txt.

Caller contract (written in the write_queue docstring, for M10 and M9):
- make_queue calls write_queue(O, ALL, held=HELD|families_on_hold, bound=set(core.FAMILY_GROUP)).
- On an exception, make_queue writes the queue, the weights and .blocked empty, and the word "unknown" (never 0) into .remaining and .waiting.
- Only keeper_prior.sh and aln33_prior_pool.sbatch may serve the prior queue.
- M9 runs check_plan on the existing plan plus its new rows before appending.

### Remaining review items

- [cross-module M5/M9, medium-low] Donor units would run select.py code that their code hash does not cover. The select.py docstring (select.py:25-28 and 37-41) tells run_donor.py / donor_train.py (M5) to use select.py at run time: build the record's joint_choice with select.joint_choice(), and name <gid>_m<M>_best/_gainsel/_h30 and _stable<L-3>.pt with member_ckpt / stable_ckpt / retained_states / compute_limit. But select.py says it is hashed only into prior33_bridge, prior33_target and prior33_zeroshot (select.py:3-4), as in design §6.3: FAMILY_CODE prior33_donor and prior33_rich_donor (design lines 1087-1088) have no select.py. The core, panel and CSX donor groups (prior33_donor) and the rich groups (prior33_rich_donor) would therefore execute unhashed code. A later edit of select.py (λ rule, file names, limit parse) would change donor behaviour and the recorded joint_choice without changing the donor code_hash. Fix before registration: add select.py to both donor code groups in M9's registry snippet and record this as a deviation from §6.3, or have M5 not import select. Related: names_limit is used only by deps._check_donor but lives in the hashed file, so a later queue-side fix would re-hash three families; move it into deps.py before registration.
- [M8 API, low-medium] check_plan and write_queue silently validate and queue nothing when rows is a one-shot iterable. Both build the index from rows (_Ctx -> index() consumes the iterator) and then iterate rows again (_seq(rows); deps.py:364 and 519-520). Reproduced: D.check_plan(itertools.chain(P.rows, [rich group without horizon_from])) returns [] without error, while the same rows as a list are refused. D.write_queue(out, generator) writes an empty queue_v3_prior.txt and '0' into .remaining, so the keeper would stop. M9 is the caller most at risk, since it runs check_plan on 'the plan plus its new rows'. Fix: at entry, rows = rows if isinstance(rows, dict) else list(rows); or raise TypeError when rows is not a list, tuple or dict.
- [M8 validation, low-medium] A horizon source can belong to another execution version. _check_donor (deps.py:244-247) checks only that spec.horizon_from is a DONOR group with the same (dataset, objective, seed). check_row accepts each of these (reproduced): (1) a primary RICH_DONOR group (limit 60) with horizon_from = the core continuation C (limit 90); (2) a rich continuation (limit 90, continuation_of R) with horizon_from = the primary core group Gf (limit 60); (3) a primary CSX group with horizon_from = a DTU core continuation. Such a group adopts an H* that the core members it is paired with in its own version did not train to. This breaks §2.15/§2.16 'APR-AP / APC-AP at equal updates', and nothing detects it at run time, because the stream hashes still match. Case 2 is exactly what a --continuation builder that copies the rich row's fields would produce. Fix: require compute_limit(row) == compute_limit(horizon source). For a continuation, also require that its horizon source is the continuation (continuation_of) of the horizon group of its own source.
- [M8 validation / M9-M11 contract, low-medium] The version labels of continuation slot rows are not tied to their group. deps treats spec.version and spec.continuation_of on bridge, target and zero-shot rows as labels only (deps.py docstring, lines 16-17), and _check_slot_row never compares them with the group's. check_row accepts (reproduced): a bridge or target of continuation group C with neither label; a C target labelled version 7 while C is version 2; a primary Gf target labelled version 2 with continuation_of. analysis._version (analysis.py:321-327) keys configurations on exactly these fields. An unlabelled continuation row therefore becomes 'primary' and collides with the primary row of the same cell: analysis.py:1009-1011 raises 'ambiguous duplicate units' once both are complete, and until then one of the two is set aside with a note. A mislabelled row forms a phantom version. Fix: pin one field (spec.version), require it on every continuation group and on each of its slot rows with the group's value, and refuse it on rows of primary groups.
- [M8 validation, low] check_row and check_plan still accept these plan inconsistencies (each reproduced on the test plan): (a) an access-block (mode B) zero-shot row for slot XM, although §4.1 access covers only AP, XP and J*; (b) bridge, target or zero-shot rows on the concrete members J1 or J025: select._NAMES (select.py:97) accepts them as slot names, so such a row bypasses the λ rule; (c) a second bridge row for the same slot (Gf, AP); (d) a CSX group for target fau, which §2.16 excludes; (e) a panel-block donor group and a panel from-scratch target for fau (§4.1 panel is private_bdf only); (f) seed fields: a donor group with row seed 3401 but spec.donor_seed and sampler_seed 3407, sampler_seed != donor_seed, and a target whose spec.target_seed differs from the row seed (§4.3); (g) a continuation registered in another block than its source; (h) a target with member AP but variant XP, where member silently wins; (i) spec.members = [] silently becomes the family default (select.py:143, and likewise in _recorded_group). Only M9's count assertions would catch some of these.
- [residual of round-1 #1, low] Unresolved J* rows are still admitted. When a complete group record cannot resolve J* (SelectionError), deps lists the J* rows under 'unresolved' and counts them as waiting (deps.py:541-544), but they stay listed with their upstreams (deps.py:549). The §6.5 worker and keeper test admits a row as soon as its upstream records exist. With an M5 layout drift, every J* bridge, target and zero-shot row of the group would still start, raise SelectionError, end technical_failed three times, get .failed, and block its dependents. The pinned interface and check_group_record reduce this to an M5-bug-only path. To prevent the cascade, also write unresolved eids to .blocked while still counting them as waiting; the trade-off is that the keeper then never stops until the record is fixed. Either way, the write_queue docstring should state the chosen behaviour; it currently describes only the counting.
- [M10 integration notes, low] (a) ckpt_deps(row, rows) re-indexes a list on every call (deps.py:413). Measured on a synthetic plan with the exact §4.1 block of 1,154 rows plus 9,327 other rows: 1.3 s per offload pass for 1,154 pending prior rows, against 0.00 s with a mapping. The planned deps_of patch should pass deps.index(rows) built once per pass. ckpt_offload's own `by` is last-wins while deps.index is first-wins; they are equivalent because check_plan refuses duplicate prior ids. (b) The pinned make_queue fallback (deps.py:513-517: empty queue, 'unknown' in .remaining and .waiting) keeps the keeper alive while the lane idles silently. unclaimed() is 0 and the keeper heartbeats, so watch_anyhost.sh never raises an EVENT; the error appears only in refresh.log. The prior watcher spec should raise an EVENT when .remaining has read 'unknown' for more than about 20 min.

### Open issues (implementer)

For M5 (donor_train.py / run_donor.py, which do not exist yet):
- Write members[M]["best"]["ce_dev"] as a number for every member, and record joint_choice = select.joint_choice(record).
- Name the stable states with select.stable_ckpt / retained_states, using L = select.compute_limit(row).
- Add a synthetic test asserting select.check_group_record(rec, row) and select.member_of on a record written by train_donor_group / run_donor. That test is the real protection against item 1's cascade, because the worker admits J* rows as soon as the group record exists, faster than a 10-minute refresh can intervene.
- At run time, log a check_group_record error; do not fail a finished group, because its resume files are deleted at the end.
- If run_donor imports select, M9 should add select.py to the prior33_donor and prior33_rich_donor entries in FAMILY_CODE.

For M9:
- Run deps.check_plan on the existing plan plus the new rows before appending, and follow the pinned fields:
  - a group's `dataset` is its target cohort;
  - continuations use spec.continuation_of with a larger "_limit<L>_";
  - rich and CSX groups use spec.horizon_from, pointing at the matching core group or core continuation;
  - zero-shot rows carry spec.bridge and spec.mode;
  - downstream continuation rows may carry continuation_of or version only as labels and must list only their own group (and bridge) as upstreams.
- Optionally assert, as in §6.4, that each target cohort is absent from its donor set; M8 does not check that.

For M10:
- In make_queue, pass bound=set(core.FAMILY_GROUP). On the error path, write "unknown" (never 0) into .remaining and .waiting, and print summary['unresolved'] into the refresh log.
- The keeper must treat a missing or non-integer .remaining as unknown and keep running.
- Never point keeper.sh or aln3_gpu_pool.sbatch at queue_v3_prior.txt.
- With blocked rows no longer listed, the watcher patch only needs the spec "queue_v3_prior c3_aln3pr 4"; subtracting .blocked is optional.
- The ckpt_offload patch can pass deps_of's `by` mapping to ckpt_deps.
- M10's bash tests should run the real worker and keeper against write_queue output.

Other:
- M4's rich.py will shadow the installed third-party `rich` package when a prior33 file is run by path. Use -m, or add a similar guard.
- Tests ran locally under nice inside the session allocation, as the task instructed. The §6.5 Slurm CPU-job run of the suite is still to do.
- contract.py and fixtures.py changed concurrently, from another agent; the M1 and M11 tests still pass with them.

## M10 (final review ok=False)

### Interface

Revision 2 of M10. These files are unchanged this round: slurm/aln33_prior_gpu_probe.sbatch and tests/auditory_alignment_v3/prior33/test_infra_harness.py (the pytest wrapper of the harness). No live file was edited, no patch was applied, and no job was submitted. sbatch --test-only was used for syntax only. The live sha256 values still match the patch headers: ckpt_offload 2850f647..., make_queue 78dea053..., watch_anyhost 0f7d6344..., aln3_gpu_pool ee96fa7e....

PATCHES (unapplied; each header carries live-sha256, patched-sha256 and an apply recipe that the harness now runs verbatim):
- ckpt_offload.prior33.patch (live 2850f647ae22e8d5e64896f941c4163eadeab2ef6da3dfc0bea29d4516b4bdc7 -> patched 7d4c1f4142452e402d77698047d5aed0860ddc96c292ac270b259a23bc1483a9):
  - NO_DEPS |= {..._DONOR, ..._CSX_DONOR}; HANDLED |= {..._RICH_DONOR, _BRIDGE, _TARGET, _ZEROSHOT}; new P33_FAMILIES (the six families).
  - deps_of: `elif f in P33_FAMILIES: out |= set(P33.ckpt_deps(r, by))`, with the import inside the existing try.
  - one_pass: `pending |= {not-done rows of P33_FAMILIES in the plan}`.
  - The header recipe's import test now uses importlib.machinery.SourceFileLoader.
  - The header runbook for the daemon restart now says: check sbatch --test-only first; send TERM; wait until the old job has left squeue AND `flock -n .ckpt_offload.lock true` succeeds; then sbatch, and check that a new 'start' line appears and that the job log has no 'another ckpt_offload instance' line.
- make_queue.prior33.patch (live 78dea053... -> patched f1e0ccc653d67fa7384f3ee1a27e7a5edc6dcf3d68e50a055886a418340305e6):
  - QUEUES["prior"] plus prior_queue(fams) inside a try. On error the queue files are empty and the counters read 'unknown'.
  - New: when write_queue leaves .remaining at 0 while an open prior row (no record, no .failed) is held or unbound, .remaining is rewritten as 'held'. The summary line gains paused=N.
- watch_anyhost.prior33.patch (live 0f7d6344... -> patched e2fe8b4e189eea291ffb06ce79d0cefabb188eac3ae2c5250586871934e07c23):
  - Spec "queue_v3_prior c3_aln3pr 4 120 9". Optional spec fields 4-5 give the stale seconds and the strike count, default 180/10, so fm/small behave as before. The prior EVENT comes about 10 min after the last heartbeat.
  - New EVENT 'keeper for queue_v3_prior cannot act': the log is under 5 min old, its last line is a bad heartbeat, and its last 10 heartbeats all say 'sbatch refused' or 'squeue failed'.
  - New EVENT "prior queue in make_queue.py's error state for 20 min": .remaining is a non-integer other than 'held', or the file is missing, for 20 ticks. The event prints refresh.log's 'prior queue error' line.
  - A spec without a queue file is skipped.

.remaining VALUES: an integer (deps.write_queue); 'held' (make_queue: lane paused); 'unknown' (make_queue error).

KEEPER (private/auditory_alignment_v3/keeper_prior.sh [MAXG<=4 [PAR]]; job wrapper slurm/aln33_prior_keeper.sbatch):
- Single instance: flock on private/auditory_alignment_v3/.keeper_prior.lock, opened with `exec 9>>`. A second instance logs 'another instance holds ...' and exits 0. sleep and sbatch run with 9>&-.
- Submits only for rows that were ready and unclaimed on two consecutive passes, while there are fewer than 4 c3_aln3pr jobs and fewer than 2 pending.
- When only OOM-marked rows are ready, it submits with --partition=A30,A40,L40S, and only if no such restricted worker is already pending. squeue is read as %j|%T|%P.
- Stops on STOP_queue_v3_prior, or when .remaining reads 0 on two consecutive loops.
- Every submission goes through `env -u` for ALN33_ROOT, ALN33_KEEPER_POLL and ALN33_POOL_{PY,POLL,IDLE,STAGGER}. The wrapper unsets the same variables.
- Heartbeat format: `<ts> heartbeat ready=N (no oom mark: K; also ready last pass: NP) workers=G pending=P remaining=R[ submitted worker J | sbatch refused (rc=X) | squeue failed: nothing submitted | (only out-of-memory rows ... already pending ...)]`.

POOL: same interface as revision 1, plus:
- Test hooks are validated as numbers (fallback 30/1200/20 s).
- The log prints 'test hooks in effect: ...' whenever an ALN33_POOL_* variable is set.
- The header now lists the changes beyond §6.5 and the claim recovery for dead workers (refresh.sh).
- The source's GPU check, claim sweep, run_unit, _last.pt cleanup, PAR clamp and CAP formula are byte-identical; verified with diff against source lines 46-82, 22-23 and 29-34.

### Remaining review items

- MEDIUM (latent; harness isolation). Where: tests/auditory_alignment_v3/prior33/infra/run_harness.sh:376-383. The harness builds its refresher test copy with sed from the live, unhashed private/auditory_alignment_v3/refresh.sh and always runs it (line 383). The 'differs in exactly 3 lines' check at line 378 only records a FAIL; it does not stop the run. Failure case: refresh.sh's cd line stops matching '^cd /home/infres/yinwang/EEG_auditory$', for example after someone adds the '|| exit 1' guard that every new M10 file uses. The copy then keeps the live cd. Its claim loop runs on the live pool/*/*.claim with the fake squeue, which lists only job 77, so it rm -rf's every live claim older than 2 min. Live FM/small units can then be claimed and run twice. Demonstrated without executing the copy: on a modified refresh.sh the harness sed leaves 'cd /home/infres/yinwang/EEG_auditory || exit 1' and changes only 2 lines (/tmp/claude-34987/-home-infres-yinwang/e9de8994-9c52-494a-8342-34e8ecdbe1ba/scratchpad/rf/refresh_test.sh). test_infra_harness.py runs this in every 'pytest tests/auditory_alignment_v3/prior33', including the step-1 Slurm job and any later rerun. Fix: pin refresh.sh by sha256 as the patches are pinned, and on a mismatch skip the test and FAIL. Alternatively, run the copy only when the 3-line check passed and grep -qx 'cd "$REFRESH_ROOT"' matches. Related hardening: recipe() (line 510) runs patch-header text with the real PATH. A future header that placed the daemon-restart lines (squeue/scancel/sbatch) above its 'mv -f' line would act on the live fleet. Run recipes with PATH=$FPATH; sha256sum, cp, patch and mv are all in /usr/bin.
- LOW-MEDIUM (runbook does not match M2a). Where: slurm/aln33_prior_cpu.sbatch lines 18, 19 and 21. The C1, C2 and C4 usage lines name modules that do not exist: '-m auditory_alignment_v3.prior33.cache_build sparrkulee-table', '-m ...prior33.audit_align' and '-m ...prior33.cache_build sparrkulee'. M2a implemented a single module, 'python -m auditory_alignment_v3.prior33.build_sparrkulee --stage C1|C2|C4' (build_sparrkulee.py:7-14; the deviation is noted at 66-68). M2a also requires C1 -> C2 -> C4: stage_c4 (line 1029ff) raises FileNotFoundError('... run C2 to completion first'). The header's two-slot plan (lines 13-15, 'C2 (2-3 h) | C5 -> C7 -> C4 -> C3') starts C4 about 1 h 45 min into C2's 2-3 h, so C4 fails immediately. It would do so after waiting for a CPU start, currently estimated at 2026-10-18T14:19, and normal QoS is at 28/30. Fix: correct the usage lines and use an order such as C1; then C2 | C5 -> C7 -> C3; then C4; then C6. Re-check C7's inputs when M2d lands: §6.2 aligns rich_f32 with each cohort's env_f32.npy, and for SparrKULee that file is written by C4.
- LOW (harness after deployment). Where: run_harness.sh. Once steps 3, 5 and 6 apply the patches live, the harness can no longer pass. test_infra_harness.py then makes any later 'pytest tests/auditory_alignment_v3/prior33' fail. Verified on a sandbox repo copy whose 'live' files are the patched versions: 107 passed, 4 failed (/tmp/claude-34987/-home-infres-yinwang/e9de8994-9c52-494a-8342-34e8ecdbe1ba/scratchpad/postdeploy/out.txt). Three failures are the recipe checks (lines 513-521), whose live-sha check refuses the patched file. The fourth is the 'replaces exactly 5 live lines' check (lines 414-415). The ckpt_offload import/deps_of/one_pass behaviour checks are also skipped without any message: apply_patch's 'already carries this patch' branch (line 403) makes no .unpatched copy, and line 496 has no else branch. Fix: when the live sha equals patched-sha, report the recipe and line-count checks as 'already applied' rather than FAIL, and still run the ckpt_offload checks that need only the patched copy.
- LOW (keeper lock on NFSv3). Where: private/auditory_alignment_v3/keeper_prior.sh:36-37 (code) and 15-18 (header). /home is mounted NFS vers=3 with local_lock=none, so this flock is an NLM lock held on the server. If the node running the Slurm keeper job crashes, the server keeps the lock until that node reboots and notifies it through statd. Every later keeper, whether a requeued job or the session fallback, then exits 0 at line 37 with 'another instance holds'. That contradicts the header's 'a keeper that is killed frees the lock at once'. The watcher's dead-keeper EVENT still fires, but no recovery is documented. Fix: write host, pid and job into the lock file and print them on refusal. Document the recovery: if that holder is gone, mv the lock file aside so the next keeper locks a new inode. Note on coverage: the harness lock test (k8, lines 348-361) ran under TMPDIR on local xfs, not NFS. I checked same-host NFS behaviour by hand (refused while held, freed on exit, an inherited fd keeps the lock, flock -n FILE works). Cross-host behaviour remains untested.
- LOW (stale QoS figures). Where: slurm/aln33_prior_keeper.sbatch:8-14 and slurm/aln33_prior_cpu.sbatch:7-12. Both assume about 27 normal-QoS jobs in use and say 'the keeper plus at most 2 CPU builders can bring the count to 30'. At 02:40 there were 28 (squeue -q normal), with MaxSubmitJobsPU=30 (scontrol show assoc_mgr). A keeper job plus 2 builders would make 31, and the third submission would be refused for every session. Separately, every new CPU-partition job currently gets a --test-only start of 2026-10-18T14:19 despite 430 idle CPUs; I tested the keeper job, aln3_ckpt_offload.sbatch and the CPU sbatch. So for now the keeper must run as the session fallback. Under step 1 of the ckpt_offload recipe, the daemon restart, and with it live-edit steps 4-6, must also wait. The documented procedure ('count first') already covers this; the figures should say to count rather than assume.
- LOW (doc). Where: the 'Beyond §6.5' deviation list in slurm/aln33_prior_pool.sbatch:18-22. It omits one benign change: lines 137-139 skip blank lines in queue_v3_prior_weights.txt and .blocked. The source pool (aln3_gpu_pool.sbatch:89) aborts the worker on such a line, because an empty associative-array key is fatal in non-interactive bash. Verified: 'bad array subscript', exit 1. Add one clause to the deviation list.

### Open issues (implementer)

1. Nothing is applied. The §6.5 live-edit steps 2-6 remain: registry and run.py, then ckpt_offload plus the daemon restart, the plan append, make_queue, the watcher plus the keeper. If a live file changes, regenerate the patches with scratchpad/m10r2_gen_patches.sh from fresh a/ and b/ copies; both the harness and the recipes refuse a mismatched sha256.
2. The daemon restart (step 3) must actually take effect before step 5. An old daemon still running fails open in the prior error state; the harness shows this (15 of G's files offloaded). The runbook now checks that the new daemon has started. On 2026-10-17, CPU-partition jobs (the offload daemon, the keeper job, the C1-C7 builders) were expected to start only on 2026-10-19 20:49.
3. The normal QOS is at about 27/30. In practice the keeper is best run through the session fallback, which the lock makes safe alongside a later Slurm keeper job, and the builders must be sequenced.
4. With the offload fix, prior rows that stay held keep their donor groups' _best.pt on home until they are done. This is expected to be small, but it is unbounded while a hold lasts.
5. deps.py (M8) still documents .remaining as one integer. Its owner may want to adopt or document the 'held' marker that make_queue writes; M8's own tests are unaffected.
6. Claims of dead workers (time-limited, not requeued) are released only by the remote refresh.sh and by new workers' start-up sweeps. If the refresher is down, the watcher's 'refresher silent' EVENT covers it.
7. The 'cannot act' EVENT needs 10 consecutive bad heartbeats, so intermittent sbatch refusals do not alarm.
8. Reviewer item 11 was truncated in the input. I addressed the two failure modes I inferred (the old daemon still holding the lock, and CPU-partition start delay); if the reviewer meant something else, that point needs another look.
9. The harness's watcher and keeper checks depend on timing, with margins of about 2.5x on tick counts and of 0.35-0.6 s on keeper passes. They passed three runs on the 2-CPU session node but could become flaky under heavy load.

