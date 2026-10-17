# Adversarial review of `PUBLIC_PRIOR_DESIGN.md` (E34_PUBLIC_PRIOR, `aln33_env64_125ms_v1`)

Written 2026-10-16 (about 21:30–22:30 CEST) by a read-only review workflow under ALN3.4. No existing file was changed, nothing was submitted, nothing was deleted. This file is the workflow's only output.

**Reviewed:** `private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md` (1,027 lines, 21:28).

**Against:**
- `inherited/PUBLIC_PRIOR_EXECUTION_v3_3.md` (8a4217a8), `inherited/OBJECTIVES_v3_3.md` (b85b9d27), `inherited/public_prior_v3_3.yaml` (e8ecded1). All three match the package `SHA256SUMS`.
- Package docs/02 §C, docs/06 and `configs/seed_and_reporting.yaml`, `configs/execution.yaml`.
- The ALN3.4 block of `AGENTS.md`, the intake note, the ADDENDUM_13 draft (00d8d65b) and the SparrKULee receipt (fb5524f9).

**Method:**
- I read the live code that the design patches or edits.
- I re-derived the data claims from `.npy` headers, JSON and TSV only, using `allow_pickle=False`.
- No `*.data_dict`, `*.pkl`, BDF or HDF5 payload was opened, no dataset code was run, and no private EEG was read. Private files were inspected for counts only.
- Scratch scripts: `/tmp/claude-34987/-home-infres-yinwang/e9de8994-9c52-494a-8342-34e8ecdbe1ba/scratchpad/critique/sk_roles.py` and `.../critique/sk_segments.py`. The other checks were inline `python -I -B` one-liners, all run under `nice -n 10` with less than 1 GB RAM.

**Overall:**
- The design is careful, and most of its numbers reproduce exactly (§B).
- One finding changes the primary comparison object (F1).
- Five findings leave out things the contract requires or asks for (F2–F4, F6, F7).
- One finding makes zero-shot rows hard to compare with adapted rows (F5).
- The rest are lower-risk engineering, data-use and provenance issues.
- None of the planned edits touches a hashed file.
- The infrastructure edits (registry, run.py, make_queue, offload, watcher) are safe as specified, provided the ordering in F27 is kept.

---

## A. Findings (most severe first)

Severity:
- **HIGH**: changes what the primary rows estimate.
- **MED**: a contract requirement is missing, or comparability is lost.
- **LOW**: hygiene, efficiency or wording.

### F1 · HIGH · contract (budget) — per-arm continuation breaks the equal-update rule for the primary rows

**What the design does**
- §2.10: each donor extends its own horizon by 10 ep-eq when *its own* best stable-phase score is among its last 3 stable validations, up to 60 ep-eq.
- `<eid>_best.pt` is the maximum over all validations.
- §4: the target and zero-shot rows depend on "the slot donor", which is `_best.pt`.
- The equal-update `_h30_best.pt` exists only "for sensitivity checks".
- Risk 8 concedes that the arms "can get unequal step counts".

**Why this conflicts with the contract**
- yaml `budget.rule: equal_updates_and_eligible_anchor_exposure`.
- PUBLIC_PRIOR_EXECUTION §7: 供体预训练版本按相同优化步数和相同合格锚点暴露量比较 (donor pretraining versions are compared at equal optimisation steps and equal eligible-anchor exposure).
- docs/02 §B: 相同优化步数、batch暴露与读出预算 (equal optimisation steps, batch exposure and readout budget).
- Continuation is allowed (按统一规则续训, continue training under one uniform rule). But with a per-arm trigger, the 240 target rows and 150 zero-shot rows compare audio_pair, cross_person and joint at different update counts.
- The joint λ choice also compares λ = 1 and λ = 0.25 at possibly different horizons.

**Fix**
- Make the horizon slot-synchronous. Group the 3 variants and both λ candidates by (target, objective). If any member's trigger fires (or a pre-declared majority), all members extend together and all decay at the same H.
- Alternatively, feed the primary 240 + 150 rows from equal-update donors (`_h30_best.pt`, or the synchronised horizon), and register per-arm continuation as a separate, declared "development-selected recipe" comparison with its own downstream rows.
- In either case, compare the λ candidates at equal updates.

### F2 · MED-HIGH · contract (controls) — the retained controls are missing from the core matrix

**Contract:** OBJECTIVES §4: 保留no-cross-person、错配训练和任务状态匹配对照 (keep the no-cross-person, mismatched-training and task-state-matched controls).

**What the design does**
- The no-cross-person control exists: it is audio_pair.
- The mismatched-training control and the task-state-matched control are deferred as "possible follow-up registrations" (§8 risk 3).
- Yet risk 3 itself names the confound these controls exist for: "shared stimulus-locked non-neural components could be learned instead". Inter-listener r has a median of 0.0055.

**Fix**
- Register a cross_person **mismatched-partner donor**: the same sampler and exposure, with the partner taken at a deranged tick or presentation within the stratum. Run it through the same bridge, zero-shot and target pipeline.
- Do this per objective, either for all four targets (+8 donors, 8 bridges, 60 target rows and 50 zero-shot rows) or for one declared target.
- Define the task-state-matched control explicitly: the same task and condition but a different content or time. Or record why it reduces to the mismatched control for single-task donors (all 666 SparrKULee runs are `listeningActive`).

### F3 · MED · contract (rich track) — the spectral track is absent, and one design rule blocks its main source

**Contract**
- yaml `rich_target_track: parallel_nonblocking` (spectral_structure, spectral_change, masked missing labels).
- PUBLIC_PRIOR_EXECUTION §4.
- docs/02 §C: 谱结构/谱变化用真实存在的声音标签并行增加 (add spectral-structure and spectral-change targets in parallel, using sound labels that really exist).

**What the design does**
- It never mentions the rich track.
- §5.2 states that "`*.data_dict` and `*.npz.gz` files are never opened". But the only SparrKULee waveforms are `stimuli/eeg/*.npz.gz` (204 files).
- The receipt says: "Mel / spectral stimulus features are not shipped as arrays; they would be computed from the raw stimuli by our code."

**Fix:** add a short, non-blocking rich-track section covering:
- sources with real waveforms: SparrKULee via `gzip` + `np.load(..., allow_pickle=False)` on the members, and the DTU 16 kHz originals;
- FAU and Federici masked, never fabricated;
- separate IDs;
- per-head averaging over legal samples;
- extractor and version hashes.

Replace the blanket `.npz.gz` ban with "never unpickle; `allow_pickle=False` only".

### F4 · MED · contract (zero-shot normalisation) — the source-statistics-only variant is supported but not registered

**Contract:** yaml `modes.zero_shot_normalization: …; source_statistics_only_variant_if_supported`.

**What the design does:** §2.13 says this variant is feasible for DTU, and for FAU via `eeg_1_20_noica`, but leaves it "not in this matrix". It has no plan or ID.

**Why it matters more for FAU**
- FAU's main zero-shot input is stimulus-informed. `auditory_c3/stageb.py` (docstring, lines 8–10) removes an ICA component when its 1–8 Hz cross-correlation with the *presented envelope* peaks within ±3 samples at an SNR above 15 dB.
- The rule is pooled over all 20 trials of the participant, test content included.
- The design does declare this. But it uses the test audio, which is more than "unlabelled statistics".

**Fix**
- Register a non-blocking source-statistics-only zero-shot family that reuses the same donors and bridges: DTU, and FAU from `eeg_1_20_noica`; for Federici, declare it partial.
- At minimum, add FAU zero-shot rows on the noica input.

### F5 · MED · comparability — zero-shot candidate pools differ from the adapted rows of the same cell

**What the design does:** §2.13 loads "only the held-out fold's participants".

**Why the pools differ**
- `ev1.evaluate_continuous` builds the test pool with `pool_of("test", kind)` over **all loaded segments**.
- Target-supervised rows load the whole cohort, so their pool is the union of test content over every participant.
- Zero-shot pools are therefore smaller wherever listeners heard different subsets of the content.
- Pool size moves top-1, MRR, log-loss and the hard sets.

**Measured for DTU single-talker trials** (from `inventory.json` and `content_groups.json`):

| content fold | test content groups, all subjects | test content groups, fold subjects only (folds 0–4) |
|---|---|---|
| cf0 | 23 | 22 / 21 / 21 / 22 / 22 |
| cf1 | 23 | 22 / 20 / 21 / 20 / 22 |

- Federici children hear subsets of the items (1–17 listeners per item), so the gap there is likely larger.
- FAU is unaffected, because everyone hears all codes.

**Fix**
- Build the zero-shot view with all participants, so the stimulus-defined pool is identical to the adapted rows.
- Force `train_p = ∅` in `TickBatcher` (otherwise `train_participants` would return the other folds) and assert that `train_segs == []`.
- Query only the fold's participants.
- Record `n_test_candidates` in both modes.

### F6 · MED · contract (analysis and seeds) — no analysis or aggregation is frozen with the execution record

**What the design does**
- §1 freezes the design "before the first donor result", but has no analysis section.
- The ADDENDUM_13 draft's §5 ("to be frozen with the addendum") is dropped without a replacement.

**What the contract and package require**
- OBJECTIVES §4: joint − audio and joint − cross-person as **separate** paired differences, and no 逐人最优单方法 (per-child best single method) baseline. The draft's "(iv) joint − max(audio_pair, cross_person)" must not be computed per child.
- PUBLIC_PRIOR_EXECUTION §8: reused donors and zero-shot predictions must not be counted as independent samples.
- `seed_and_reporting.yaml`: `counting_unit: unique_test_identity_not_seed_fold_or_session` and `upstream_seed_scope: donor_base_adapter_and_readout_seeds_separately_recorded`.
- docs/06: the new prior runs ALN3.3 breadth **and** 既定成对面板 (the established paired panel, 3407/3413), with 供体与target随机性都记录 (both donor and target randomness recorded).

**The current spec**
- It has a single `seed` field.
- It has no panel plan.

**Fix:** add a frozen analysis section covering:
- the contrasts: each pretrained arm − scratch, joint − audio_pair and joint − cross_person, per target, objective and mode;
- the identity unit: Federici HC and HC-v kept separate, and the always-train FAU TH never tested;
- donor reuse across a cohort's cells, so it is not double-counted;
- the family-wise procedure.

Also add the spec fields `donor_seed`, `sampler_seed` and `target_seed`, plus a panel registration rule.

### F7 · MED-LOW · selection — checkpoints are chosen by a correct-pairing gain, not by development risk

**What the design does**
- Donor checkpoints and λ are chosen by r̄(own) − r̄(another dev segment of the same listener) (§2.10).
- Target-stage checkpoints are chosen by min(es_loss − es_loss_rolled), inherited from A_LOCAL.

**What ALN3.4 says:** docs/06 (整条训练链的选择, selection along the whole training chain): 模型选择优先使用定义明确的真实开发任务风险/准确率；gain作为正确配对敏感性另报 (prefer a well-defined development task risk or accuracy for model selection; report the gain separately as a correct-pairing sensitivity). For new executions, the two rules should be compared.

**Fix**
- Declare a risk-type primary: dev reconstruction r̄(own), or dev retrieval cross-entropy at a fixed τ.
- Store the gain-selected checkpoint as well. This is cheap: a second `_best` file and no retraining.
- Label the target-stage selection level truthfully: held-out content on training identities, not new listeners.

### F8 · LOW-MED · contract (sound coordinates) — per-stream RMS normalisation uses target test-stream statistics

**What the design does:** §2.3 step 3 divides every stream, target test streams included, by its own RMS.

**Contract:** 声音统计量只从供体fit估计 (sound statistics are estimated only from donor fit).

**The invariance claim is only partly true**
- "It cannot change the L2-normalised head output" holds only if μ = 0, because v = normalize(((c·y − μ)/σ)Pᵀ).
- The unified score is exactly invariant: `ev1._zt` z-scores each segment and dimension.
- The NCE native score, the CS native score and the training losses are not invariant when μ ≠ 0.

**Fix**
- Fix μ ≡ 0, which the 2–8 Hz band-pass justifies, and record the estimated |μ|/σ. Or assert that |μ|/σ is negligible in the manifest.
- List the RMS step as a declared deviation in §1, not only in the zero-shot access table.

### F9 · LOW-MED · contract (donor pool) — FAU and DTU competing-talker donor data are dropped without a rationale

**What the design does:** §1 item 2 says "FAU and DTU donor data are single-talker only" and gives no reason.

**Why it needs one**
- PUBLIC_PRIOR_EXECUTION §2: 所有非目标公开队列的合法人类训练数据 (all legal human training data of the non-target public cohorts).
- The yaml keys include `attended_stream`.
- ALN3.2 docs/05 expects competing-speech positives when the attended stream is the same.

**Fix:** either state the reason (the attended-alignment task differs from single-talker tracking) and register competing-talker donors as a declared extension, or include them, keyed on (mixture presentation, attended stream).

### F10 · LOW-MED · data use — the restricted SparrKULee participants were already read, and C2 does not exclude them

**What the design does:** it excludes sub-019, 020, 021, 022 and 026 "as a data-use matter" (README: DUA needed).

**What already happened**
- `aln34_sparrk/decoder_lag.py` and `isc_lag.py` use `("026", "audiobook_1")` as an audit target.
- `car_scale.json` covers runs of all five participants.

**What is missing:** C2 trains each decoder on "up to 8 other listeners of the same stimulus" and does not say that restricted participants are excluded as references.

**Fix**
- Exclude the restricted participants from every computation, audits included.
- Record that the scout outputs that touched them are not used for any decision.

### F11 · LOW · record selection — the C2 exclusion depends on an EEG decoder, and its search window is too narrow

**Possible conflict with the record-selection rule**
- ALN3.2 docs/05 says 不能根据成绩决定保留哪些记录 (no keeping or dropping records by performance), and the receipt says "no run is dropped for this".
- The C2 rule judges runs with an EEG decoder.
- It is defensible as a clock-validity check, but it should be declared as one. It should use lag consistency only, not r magnitude, and it should report and list the excluded runs.

**The window**
- τ̂ is searched over ±10 s.
- Probe C saw off-peak lags from −4.4 to +37 s.
- A run misaligned by more than 10 s would be classed "unverifiable" and kept.

**Fix:** widen the search to about ±40 s, or state the limit.

### F12 · LOW · contract (budget) — the 60 ep-eq ceiling acts as a hard cap

**Conflict:** yaml `hard_cap: false`, but the design sets an "engineering ceiling" of 60 ep-eq.

**Fix:** declare it as a compute limit. When a run reaches it, register a continuation version instead of stopping silently.

### F13 · MED-LOW · engineering — the private path hard-codes 250 Hz and 20 channels

**The code:** `local_train.fit_private` calls `build_encoder(spec["architecture"], 20, d, bt.W, 250)` (`local_train.py` line 192).

**Risk**
- The shared-encoder factory must ignore `fs` and `n_ch`.
- If it honours `fs=250`, it builds the 250 Hz geometry (token step 5, window 10). The donor `proj` then does not fit.
- A non-strict `load_donor` would hide this as "new" tensors.

**Fix**
- Assert that every donor tensor loads with an identical shape, apart from the opened `seen` rows. `run_transfer.py` asserts in the same way.
- `ContractObjective` must pass the prototype and label path through unchanged.

### F14 · LOW-MED · engineering — the key spec contradicts itself, and the loss sees only `keys`

**The contradiction (§2.5)**
- It says key = (family<<40)|(presentation<<24)|"sample on the family clock".
- It also says "the family clock … is not part of the key".

**Why it matters**
- `fit_continuous` calls `obj(u, v, keys=rws[2])` (line 110).
- The rolled early-stopping batches carry the rolled audio's keys.
- So `ContractObjective` can apply the ±2 s family mask only if the family and the family-clock sample can be decoded from the key.

**Fix**
- Pin the key as (family, presentation, family-clock sample), with bit-budget asserts: the sample below 2^24 and the presentation below 2^16.
- Test the rolled path.

### F15 · MED-LOW · engineering — the copied pool loop will not pack as estimated

**Why**
- `aln3_gpu_pool.sbatch` reads the queue once per pass and then `wait`s for **all** running units (lines 90–113).
- Its capacity wait blocks on the current row instead of skipping to a lighter one (lines 97–102).
- With the prior queue sorted donors first, a V100-16GB card (CAP 13 GB) runs one weight-8 donor while weight-3 and weight-2 units wait.
- Units that depend on finished donors also wait a whole pass.
- The estimate of about 4–7 h wall time assumes packing that this loop does not deliver.

**Fix (only in the new `aln33_prior_pool.sbatch`)**
- Use `wait -n` and re-read the queue each time a slot frees.
- Skip rows that do not fit.

### F16 · MED-LOW · engineering — the persistent exit rule can leave GPUs idle

**Why**
- Rows whose upstream unit is `.failed` (after 3 tries) never become ready.
- If `deps.write_counters` counts them as "waiting", `.waiting` stays above 0, and the 4 workers loop idle until their time limit.
- The watcher reports only the failed marker.

**Fix:** count dependents of failed or `technical_failed` upstream units as *blocked*, and exit when only blocked rows remain.

### F17 · LOW · engineering — the time limit is inherited

**Why:** the source pool has `--time=24:00:00` and `--nice=50`. With "no keeper", the prior pool stalls at 24 h. The watcher's prior spec would raise an EVENT after 10 min.

**Fix:** state `--time` for the new pool (or none on V100/A40, per site practice) and how a worker is resubmitted.

### F18 · LOW · engineering — the CPU jobs specify "runfill, CPU partition"

**Why:** the existing CPU jobs (`bc_interim_cpu.sbatch`, `aln3_ckpt_offload.sbatch`) use `--partition=CPU` without runfill.

**Fix:** verify that runfill is accepted on the CPU partition, or copy the `bc_interim` pattern and keep the user's submitted-job count at 25 or fewer.

### F19 · LOW · engineering — the probe slot is not guaranteed

**Why**
- Draining a V100 FM worker frees a QOS slot, not a V100.
- `keeper.sh` (line 17) resubmits immediately, and its job may backfill on an A100, A40 or L40S if no V100 is free.
- The drain itself lasts as long as the worker's longest running unit. Weight-1000 FM units run for hours.

**Fix:** allow the probe on V100, A30, A40 and L40S, or accept the latency.

### F20 · LOW · engineering and disclosure — the FrozenBridge interface and bridge_cal reuse

**FrozenBridge**
- It must define everything `ev1` reads: `objective`, `B_uni`, `a_mu`, `a_sd`, `B_nat`, `alpha_uni`, and `tau` as a dict with the keys `unified` and `native`.
- `calibrate` is never reached when `q_es` is empty. "Raises if called" therefore proves nothing on its own: keep the `_ridge` monkeypatch and assert that `train_segs` is empty.

**bridge_cal reuse:** `B_uni_cal` and its τ are both fitted on bridge_cal. Disclose this, or split τ by the same 2-fold participant split.

### F21 · LOW · provenance — the fixed exclusions rest on non-persistent scratch files

**Why**
- These exclusions and several design counts come from scout scripts and outputs in the session scratchpad (`/tmp/...`), which is not persistent: sub-051 audiobook_12_2 at −566 samples, sub-011 audiobook_6_1 with τ = 0 unsupported, the jingle estimate, channel order, and the decoder r values.

**Fix:** copy them into `private/auditory_alignment_v3/aln34/` (0700) before registration, and quote their hashes in the execution record.

### F22 · LOW · specification — family clocks are undefined outside SparrKULee

**Federici:** each family is a natural/vocoded pair (51 two-item groups, cross-correlation 0.84–0.93), and the relative lag is not stated.

**DTU:** families are transcript groups with Jaccard ≥ 0.8 (336 waveforms in 46 groups). These are different recordings and are not time-aligned.

**Fix:** state the offsets (0, or the cross-correlation lag) so the ±2 s mask is well defined, and add a test.

### F23 · LOW · harmonisation — the private input differs from the donors

**Normalisation:** the private input is z-scored per child at 250 Hz (0.5–45 Hz) before resampling, and is not re-standardised at 64 Hz as the public cohorts are.

**Band:** it is 0.5 to about 26 Hz, while the donors are 1–20 Hz. A 20 Hz low-pass is possible on 800 ms epochs.

**Fix:** consider re-standardising per child and channel at 64 Hz, and matching the upper band edge. Either way, declare it.

### F24 · LOW · identity — HC/HC-v pairs in the donor cross-person keys

**Why:** the folds keep HC N with HC-v N because of the "either identity hypothesis", but the donor pairing does not.

**Fix:** count (HC N, HC-v N) cross-person pairs and exclude them for consistency. Probably there are none, since HC-v children heard the vocoded items.

### F25 · LOW · scope — the CBraMod next-stage comparison is not mentioned

**docs/02 §C asks for:** generic → target; generic → public auditory → target; random → public auditory → target.

**Why it matters here:** the 64 Hz cache cannot serve a 200 Hz CBraMod.

**Fix:** note that the manifest's roles, exclusions, keys and overlap masks are meant to be reused for that track.

### F26 · LOW · claim — the DTU NH single-talker counts differ slightly

**Design:** 334 trials on 79 shared SHAs, plus 15 trials on single-listener SHAs.

**`inventory.json` + `content_groups.json`:** 338 + 11, with the same 90 and 79 SHAs and the same total of 349. The difference is probably the `sub-024_run-2` exclusion or an h5-level filter.

**Fix:** the manifest should print the reason.

### F27 · LOW · operations — the order of the live edits must be pinned

**Constraints from the code**
- `ckpt_offload.deps_of` fails closed fleet-wide on any queued row of an unmodelled family. It loads `NO_DEPS` and `HANDLED` once, so it needs a restart.
- `make_queue` only queues families listed in `QUEUES` and present in `core.FAMILY_GROUP`.

**Safe order**
1. Add `prior33/` files and tests.
2. Edit `registry.py` and `run.py`, with an import test of `core` and `run` in the eeg2025 interpreter. Assert there are no key collisions in `FAMILY_CODE` and `FAMILY_GROUP`, and that all existing families' `code_hash` are unchanged *before* `os.replace`.
3. Update the offload script and restart it. Restart it gracefully with SIGTERM: the sbatch traps TERM. Expect up to a 3-minute watcher window.
4. Append to `plan_ext`.
5. Edit `make_queue`, with the `prior33` import inside its `try`.
6. Edit the watcher, then submit the workers.

A broken `registry.py` or `run.py` would make every new unit fail fleet-wide, and those failures count toward the 3 tries.

---

## B. Claims checked against the real files

### Matches

**Hashes and registry**
- All design-time hashes match: core a3851b4a, local_train dee8d0cd, registry 2e451e0b, run 7c84b692, make_queue 78dea053, ckpt_offload 2850f647, pool ee96fa7e, watcher 0f7d6344, receipt fb5524f9.
- The contract files and ADDENDUM_13 also match.
- `plan_ext.jsonl` has 3,325 lines, sha 85b44d8d.

**Code-hash scope and queue isolation**
- `registry.py` and `run.py` are outside every code hash: `core.code_hash` = `FAMILY_CODE[group]` + 14 `V2_DEPS`.
- New families cannot enter the existing queues, because `make_queue` uses explicit family lists.
- Every base and donor lookup filters on `family_id`: `run_complement`, `residual32`, `complement32`, `run_e_complement`, `run_transfer`.

**Offload, keeper, watcher and pool flags**
- `ckpt_offload`:
  - its EID regex matches `_h30_best.pt` and not `_bridge.npz`;
  - `has_resume` matches `_wsd_resume.pt`;
  - `queued()` and `claims()` cover `queue_v3_prior`;
  - it fails closed on unmodelled families.
- `keeper.sh` keeps at most 10 workers, of which at most 3 pending. With 6 running and 3 pending, the watcher's fm check does not strike.
- `.infra_<jobid>` stops claims, waits for running units and then exits. It is the pool's only per-worker graceful stop.

**Patching surface**
- The `local_train` module globals the design patches all exist and are resolved at call time: `GridBatcher`, `build_encoder`, `target_stats`, `build_head`, `Objective`, `PrivateBatcher`.
- `ev1.Reps` and `ev1.Readouts` can be patched the same way.
- The in-process patch precedents exist in `run_transfer`, `local_support` and `residual32`.

**Encoder geometry and projection**
- `lag_local_tokens` at 64 Hz: step 1, window 3, 36 tokens, `proj` = LN(1152) → Linear(1152, 32).
- 44,176 parameters in total, of which `proj.1` holds 36,896.
- `semi_orthogonal(32, 8, 20261016)` has sha 706c4ff4441f4940, and PᵀP = I to 1.2e-7.
- The `FixedFeatureHead` keys are `std.mu`, `std.sd` and `P`.

**Filters and the tick rule**
- Envelope SOS sha a5457201db325d21: −63 / −6 / −6 / −26.3 dB at 1 / 2 / 8 / 10 Hz. The EEG SOS sha is e014c236.
- `h_aa` has 61, 727 and 3,627 taps, −6.02 dB at 26 Hz, and at most −60 dB from 30 Hz.
- The scipy default filter for 250 → 64 is −6 dB at 32 Hz, as the design says.
- The tick rule has no ties up to k = 2·10⁶. The maximum |i_k − 1.28k| is 0.48 samples (7.5 ms), i₂₄₉ = 319, and the steps split 179 / 70.

**SparrKULee**
- 666 runs, all `listeningActive`, each 64 × T float64.
- 85 participants, each with exactly one session.
- Role participants: fit 64, dev 10, bridge_cal 6. Content families are disjoint across roles except audiobook_1. The dev and bridge_cal stimulus lists are as stated.
- Restricted participants: 50 runs, 11.64 h, all in shortstories01. The README text about them is as quoted.
- The 3 runs flagged in the README are absent.
- 72 envelopes, plus the duplicate `audiobook_9_2_envelope-1.npy`.
- audiobook_1 has 78 listeners in total, 76 non-restricted and 60 in fit. sub-011 audiobook_6_1 is 64 samples longer than its 23 co-listeners.
- Segment counts, recomputed independently, match exactly:

  | role | listener segments | content segments | presentations |
  |---|---|---|---|
  | fit (N_SK) | 86,285 (119.8 h) | 7,881 | 49 |
  | dev | 8,520 | 1,756 | 11 |
  | bridge_cal | 6,366 | 1,090 | 6 |

- 1 ep-eq = 690,280 anchors = 2,696.4 steps, so S0 = 80,892.2 steps.
- Standardiser windows: 7,881 × 250 = 1,970,250.
- Licence: CC BY-NC 4.0.

**Folds and cohorts**
- The FAU, DTU, Federici and private folds match the design tables exactly.
- The FAU always-train TH list (14) and `FAU_CF` match.
- FAU stage-B reference and ICA rule: average over 31 channels including Cz, and the ICA rule as described.
- The DTU cache is CMS, not re-referenced.
- DTU: 352 HI single-talker trials; 0 SHAs shared between NH and HI; 336 waveforms in 46 groups.
- Federici: 141 items in 90 groups, 12 of them single-listener; HC 37, CI 33, HC-v 16, plus 9 phantom sessions.
- Private: 64 children (55 HA, 9 NH); test children per fold 13 / 13 / 13 / 13 / 12; epochs −200..600 ms at 250 Hz with a per-child z-score. These were counted from metadata only.

### Not checkable under this workflow's file rules (scout-only)

- BDF-header facts: 1,024 Hz, the P07/P03 typos.
- Decoder-lag, ISC and jingle numbers.
- FAU `bads_interpolated` counts (h5 attributes).
- The DTU "common-mode ratio 7.0" value. Only "CMS, not re-referenced" was checked.

---

## C. Checklist items found compliant (apart from the findings above)

- **Matched anchor exposure:** one shared sampler, identical seeded streams, both views, and identical eligible anchors. Broken only after S0 (F1).
- **Bridge on donor data only:**
  - `B_uni` is fitted on donor-fit rows;
  - α and τ come from SparrKULee bridge_cal;
  - nothing in the bridge is refitted on target data;
  - a `_ridge` raise guard protects zero-shot.
- **Target outer test never touched by donors:**
  - the whole target cohort is out of its donor set;
  - private_bdf and the phantom are never donors;
  - the C3 overlap scan covers every pair of the four public cohorts;
  - the standardiser and P come from SparrKULee and a seed.
- **Private target gets no speech zero-shot;** only EEG parameters transfer, and the class prototypes are retrained.
- **CS without the NCE mask:** `cs_qmi` is imported unchanged, keeps the diagonal, uses uniform weights and takes no mask argument.
- **Projection shared across cohorts:** stored once and never regenerated.
- **Query indexing without drift:** `i_k = (64k + 25) // 50` from the physical origin.
- **Unseen channels contribute zero:** a `seen` buffer, zero rows and zero gradient, with coverage reported. In target-supervised mode, unseen channels are opened at W = 0.
- **No hashed file is edited.** `core.py`, `local_train.py` and `V2_DEPS` stay untouched. The edited files (`registry.py`, `run.py`, `make_queue.py`, `ckpt_offload.py`, `watch_anyhost.sh`) are outside every code hash and get backups. Running units are not killed: drains are graceful, and the offload daemon traps TERM.
