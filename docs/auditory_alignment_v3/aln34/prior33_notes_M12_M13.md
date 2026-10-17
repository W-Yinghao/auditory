# Notes for M12 (probe) and M13 (execution record), from wave 3a (wou8012y2, 2026-10-17)

- Lead decisions (ALN3.4: ordinary choices are not escalated):
  - The donor group trigger uses a first-minimum rule with no tolerance. State it verbatim in the execution record.
  - B_uni_cal (fitted on bridge_cal) is kept only as a labelled sensitivity (eval_uni_cal), never primary. The primary bridge is fitted on donor fit only (yaml source_sound_bridge.fit).
  - Add bridge_seconds (and n_pairs) to analysis.py BRIDGE_FIELDS before freezing.

## M5 (final review ok=True)

### Remaining review items

- [LOW; test robustness] tests/auditory_alignment_v3/prior33/test_donor_train.py:1380 (test_real_continuation_follows_the_larger_limit) asserts dep['code_hash_equal'] is True. That holds only if no hashed file changes while the module-scoped `chain` fixture runs (about 40 s). The hashed files are core.py, local_train.py, the prior33 files contract/views/model/losses/sampler/select/donor_train/run_donor, and V2_DEPS. The G30 and C40 records each call core.code_hash when their own run_donor.run starts. My first run of the file failed exactly there (35 passed, 1 failed, 123 s): another agent edited views.py (09:13:15) and sampler.py (09:13:36-09:14:18) while the fixture ran. The two records therefore got different code_hash values, and run_donor correctly wrote code_hash_equal False. A rerun with the hashed files unchanged (their sha256 matched before and after) passed 36/36 in 118 s, peak RSS 938 MB. The code is right; the test is environment-dependent, and the §6.5 step-1 Slurm run of the suite would fail spuriously under concurrent edits. Fix: in the chain fixture, monkeypatch core.code_hash to a per-family value computed once at fixture start. Or assert dep['code_hash_equal'] == (recs['C40']['code_hash'] == recs['G30']['code_hash']) with both non-null.
- [LOW; provenance of resumed trajectories] The resume file stores no code hash. Each record.resumed[] entry holds only step, ep_eq, branch, validations, time and device (donor_train.py:1339-1345 and 1380-1382). This round makes cross-version reuse a routine path. After any failure between the end of training and core.write_record, the resume stays marked done, and every retry only reruns finish() and the record (run_donor.py:13-16). The usual reason for such a retry is a code fix, which changes the prior33_donor code_hash. The retry then writes a record whose code_hash names code that trained none of the trajectory, and nothing in the record shows it. A mid-training resume across a code change is just as invisible. M5 already records this fact for continuations (dependency.continuation.code_hash_equal), so resumes are the inconsistent case (ALN3 rule: 所有改动、复用…来源可追踪). Fix: run_donor passes rec['code_hash'] to the run (meta); _save_resume stores it; _load_resume adds code_hash and code_hash_equal to the new resumed[] entry. Record the mismatch; never refuse.
- [LOW; test coverage of leave-target-out at the M5 level] test_donor_runs_never_open_restricted_or_raw_files (test_donor_train.py:1409-1419) collects every path the target-fau chain opens, but asserts only that no restricted or raw file was opened. It never asserts that no file of the target cohort is opened. The property itself holds. In my audit probe (scale-4 fixture; core groups for fau, dtu, federici and private_bdf; train_donor_group with max_steps 2; sys.addaudithook), no file under <root>/<target>/ was opened for any target. Only the donor strata's directories and the three P_*.npy files were read. M3's batch audits do not reach the validator, the bandwidth calibration, the FLOP proxy or the rich-readout paths. One assert in the chain test would pin this review item in M5's own suite: no opened path lies under <root>/fau/.
- [INFO; outside M5] EXECUTION §7 lets training continue under the same rule, but it must 记录结果已见范围 (record which results had already been seen). M5's continuation record carries the decision basis: trigger_log with best_index, best_ce and last_window_start, the curves, inherited {from, ep_eq, step, validations, files, code_hash}, and code_hash_equal. No field states which results of the primary version (bridge, target, zero-shot) had been computed or viewed when the continuation was registered. M5 cannot know this, and M9's registered text ('E34_PUBLIC_PRIOR execution record … sha256 …' plus the continuation label) does not carry it either (make_plan_ext_prior33.py:940-955). It belongs in the M9 registration or in M13's correction note.

### Open issues (implementer)

- M12 (§7.2 GPU probe) should check on V100/A30/A40/L40S:
  - Throughput under deterministic mode, especially the sort-based backward of the window gather, and the cost of the extra per-member synchronisation.
  - Whether warn_only emits any warnings.
  - That interrupt-then-resume on the same GPU model reproduces the curves and checkpoints exactly.
  A resume on a different GPU model will not be exact; resumed[].device records it.
- The tie-free trigger applies no tolerance, so a near-flat curve whose values differ only by float noise can still count as improving. This is the researcher's call; the execution record (M13) should state the first-minimum rule.
- A record can still hold one NaN token at members[M].best.ce_dev, but only when every validation of that member was non-finite. Removing it would need select.py (M8) to accept null there.
- M9: no new hashed files are needed. The new imports are torch library modules and numpy. The donor code groups must still hash select.py, which registry_patch already does.
- The FLOP proxy does not count the float64 elementwise NCE/CS work, which is where much of the joint members' extra time goes; use timing.member_train_s and joint_extra_compute.extra.*.train_s for that.
- The M5 test file now takes about 2 to 4.5 minutes, depending on host load.

### Record fields

Fields the M11 interface requires (prior33_interfaces_M11.md) are unchanged in name and meaning:
- members[M].{best,h30,gainsel}.{ce_dev, gain, bridge_cal_ce, ep_eq}
- joint_choice = select.joint_choice(rec)
- gain_rule.member
- horizon_ep_eq, ceiling_reached_while_improving
- members[M].steps / nonfinite_steps
The only change among them: the members[M].<kind>.bridge_cal sub-dict no longer carries gain or n_gain (they were always NaN, since bridge_cal is scored without o(q)). bridge_cal_ce == bridge_cal.ce_bits.

New or changed fields (descriptive; analysis.py does not read them):
- members[M].lambda: 1.0 / 0.25 for J1 / J025, None for the other members (also in checkpoints).
- members[M].identical {best_h30, best_gainsel, h30_gainsel}.
- timing.member_train_s[M]{stable, decay, side}: synchronised step seconds per member.
- flop_proxy: encoder_fwd_bwd_per_window{shared|rich}[stratum], loss_fwd_bwd[M][stratum], flops_per_step[M][stratum], steps_by_stratum, train_flops_proxy[M], train_flops_proxy_total, validation_flops_proxy, forward_flops_per_window.
- joint_extra_compute: member_train_s, member_train_flops_proxy, extra[J1|J025].vs_AP / vs_XP {train_s, train_flops_proxy}, member_steps.
- compute_this_run and compute_inherited (null for primary groups): steps, validations, seconds and FLOPs, split for continuations.
- determinism. resumed[].device.
- dependency.{horizon|continuation}.{code_group, code_hash_equal, same_code_group}.
- nonfinite_to_null {count, paths}. resume_cleanup.

Strict JSON: the tiny real-run record and all four chain records parse with NaN/Infinity tokens refused. The core record has nonfinite_to_null.count == 0. select.check_group_record and analysis._donor_table still accept the record.

## M6 (final review ok=True)

### Remaining review items

- LOW, residual of round-1 item 3, on the M11 side. The bridge's compute cost still never reaches the analysis output. M6 now writes top-level n_pairs, n_pairs_uni_cal, n_pairs_all and bridge_seconds (bridge.py:664-669, put into the record at :679), and bridge_row_info (:1075-1085) copies them into the zero-shot records. But analysis.BRIDGE_KEYS (analysis.py:198) matches 'n_pairs' and not 'seconds'. So the JSON 'values' of the bridges section gets the three n_pairs fields but no bridge_seconds. The Markdown bridges table (analysis.py:2182-2190, built from BRIDGE_FIELDS at :206-207) shows neither. Reproduced: AN._scalars(rec, AN.BRIDGE_KEYS) on a record holding both returns alpha_uni, bridge_cal_r, n_pairs, n_pairs_all, n_pairs_uni_cal and tau_cal, with no bridge_seconds. The inherited contract §6 asks for both counts and compute to be counted explicitly (供体桥接所用声音配对数和计算开销显式计入). Fix in M11, or have M13/the status report quote them: add 'seconds' to BRIDGE_KEYS, or n_pairs and bridge_seconds to BRIDGE_FIELDS and the table. analysis.py's sha is frozen, so decide before M13. Also: bridge_seconds times fit_bridge only (bridge.py:1009-1012). Building the device banks (run_bridge.py:77) and the artefact probe are excluded; only total_seconds covers the whole unit. The note names the probe but not the bank loading.
- INFO, missing from the deviation list. CSX bridges (APC, XPC) are fitted on the core donor set's rows, manifest bridge.fit_rows[target], with no fau_cs rows: sampler.bridge_rows refuses fau_cs. Only fit_bridge's docstring says this (bridge.py:840, 'CSX and rich slots use the core donor set's rows'). The module's Interpretations list (bridge.py:37-82) does not. §2.11 says the fit rows are 'drawn once per donor set ... identical for every member of that donor set', and CSX's donor set is core + fau_cs (§3.1, §2.16). The choice is the one the inherited contract §6 asks for (all pretraining versions on the same donor fit/calibration data). It also keeps APC-AP and XPC-XP bridge-matched. List it as an interpretation with that reason.
- INFO, defence in depth for modes C and C_partial. zeroshot.access_of (zeroshot.py:102-104) copies manifest.mode_c[T].donors into normalisation_access but never checks that T itself is absent from that list. That leave-T-out property is what makes mode C 'source statistics only'. The frozen manifest builder already enforces DONORS[target] (manifest.py:1361), so this is only a cheap guard: refuse when ds is in mc['donors'].
- INFO, test docstring overclaims; one readout not recomputed. (a) The docstring of test_m9_temperatures_interior_case (test_bridge_zeroshot.py:1242-1260) says the unified, native (NCE cosine) and cross-fitted temperatures leave the grid edge, but the test only asserts edges.count(None) > 0. My probe of the same setup (fau NCE group, XP and AP, noise 0, 0.35 and 1.0) found all 5 native NCE taus on the 'upper' edge every time. Native top-1 was 1/16, i.e. chance, because the synthetic M5 checkpoints are untrained, so this is expected and not a code defect. Unified taus were interior 5/5 (even at noise 0) and the fold taus 10/10 with noise. (b) recompute_bridge checks the native readout only for NCE (:418). The CS_SINGLE native ridge (B_nat, alpha_nat, tau_native(n)) is never recomputed independently. My probe did so for the dtu CS_SINGLE AP and XP bridges: all match exactly, tau_native is interior, and alpha_nat = 1000, the top of NAT_ALPHAS at fixture scale. Suggest per-kind interior assertions and adding the CS native recomputation to the frozen tests.
- INFO, design vs inherited contract, still open but now documented. public_prior_v3_3.yaml source_sound_bridge.fit = donor_fit_only, while design §2.11 fits B_uni_cal on bridge_cal, a donor-development partition. M6 keeps it as a separately labelled sensitivity (eval_uni_cal, never primary) and states this in bridge.py:55-58 and in the record's uni_cal.use. The execution record (M13) should carry the same statement.
- COSMETIC, latent. run_zeroshot.check_bridge (run_zeroshot.py:56-58) requires the npz meta's manifest_sha256 to equal spec.manifest_sha256 exactly. views.open_manifest and bridge.check_ckpt_provenance accept a prefix of at least 16 hex digits, so a row carrying a prefix would pass every other check and be refused only here. M9 writes the full sha256 (_common, ctx['sha']), so this cannot happen with the planned rows.

### Open issues (implementer)

1. M11 (analysis.py, not edited by me): BRIDGE_FIELDS does not contain n_pairs or bridge_seconds. The n_pairs* counts still show in the bridges table's values (pattern 'n_pairs'). bridge_seconds is in every bridge record but no BRIDGE_KEYS pattern matches it, so it is not shown there. M11 should add 'bridge_seconds' (and optionally 'n_pairs') to BRIDGE_FIELDS.
2. Researcher's call: B_uni_cal is fitted on bridge_cal data despite the yaml's fit = donor_fit_only. It is kept as a labelled sensitivity; dropping it would remove eval_uni_cal.
3. B_uni_cal's 2,000-row sample is drawn by M6, not by C6. It is deterministic and its sha is recorded. If preferred, M2e could list the rows in manifest.bridge, and M6 would read them from there.
4. evaluate_zero_shot itself does not check provenance. Any direct caller (e.g. the M12 probe) must check the checkpoint and npz sha as run_zeroshot does.
5. The new M9/M7 integration tests load private/auditory_alignment_v3/make_plan_ext_prior33.py by path, plus registry_patch and run_target. They break if those APIs change, and fail transiently while fit_target.py is being regenerated (M7's generator check).
6. The test file takes about 8 minutes on the loaded 2-CPU node (load average 5-7), with peak RSS 830 MB.
7. The execution record (M13) must freeze the new hashes listed above.
8. No unit has run, so changing the B_uni_cal rows, the npz keys and the view_sha256 definition affects no existing record.

### Record fields

Bridge records (analysis.normalise, stage 'bridge'):
- status complete | technical_failed.
- target_contract: the registered spec value.
- selection_level: BR.SELECTION_LEVEL, contains 'donor dev'.
- member_resolved (RESOLVED_KEYS): J* -> J1 / J025.
- BRIDGE_FIELDS: alpha_uni, alpha_nat (None for NCE), tau_cal (scalar at n=256, with tau_cal_by_pool_size), bridge_cal_r. The bridge_info artefact_probe/* fields come from artefact_probe {status, r_own, r_other, r_own_minus_other, n_other_*, ...}.
- New accounting fields: n_pairs, n_pairs_uni_cal, n_pairs_all and pairs_rule. The BRIDGE_KEYS pattern 'n_pairs' matches them, so they appear in run_families selection.bridges[].values; checked in the test.
- New: bridge_seconds at the top level. No BRIDGE_KEYS pattern matches it.
- dependency {donor_group, slot, member, donor_group_code_hash, checkpoint, checkpoint_sha256, checkpoint_kind, checkpoint_format}.
- bridge_file {npz, sha256, checkpoint_sha256}.
- rows_sha256 {fit, cal, uni_cal, tau_draws}, cal_participants, uni_cal_participants.
- coverage: adds uni_cal_segments, uni_cal_rows, uni_cal_pool_segments and n_audio_eeg_pairs[_uni_cal|_all].
- bridge.uni_cal.fit_rows {rule, segments, rows, per_participant, segments_per_fold, overlap_with_queries, rows_sha256} and uni_cal.use ('sensitivity only').
- view_sha256 (now also covers the uni_cal rows), mode 'donor_bridge', normalisation_access.

Zero-shot records:
- eval (B_uni) and eval_uni_cal (UNI_CAL_KEYS[0]).
- selection_level: ZS.SELECTION_LEVEL == analysis.SELECTION_LEVEL['zero_shot'][0], contains 'donor dev'.
- target_contract (registered spec value), member_resolved, mode / mode_name (== spec.variant), normalisation_access, coverage, view_sha256 / pool_sha256, split_hash, zero_shot (purity), temperatures_used, native_readout, kernel_dependence_sigma.
- bridge (bridge_row_info): adds n_pairs, n_pairs_uni_cal, n_pairs_all, bridge_seconds, pairs_rule, checkpoint_sha256, uni_cal_rows_sha256.
- dependency: adds bridge_npz_sha256 and bridge_checkpoint_sha256.

Both stages: a failure is a technical_failed record (FAILED.json) with error and traceback, including failures in core.bind / new_record (code_group / code_hash are None when the family is unregistered).

