# M11 analysis: interface requirements for M5/M6/M7/M9 and open low items (from workflow w3gc2ial4, 2026-10-17)

## Interface (final)

Module auditory_alignment_v3/prior33/analysis.py (sha256 f2af2b86328857e7…). Tests sha256 02e951835fe0112d…. Statistics come only from sci_r1.stats, imported unchanged: summary, draws, group_seed, family_maxt, NB = 4000 (checked).

Public functions:
- load_rows(paths=None): default is the live units.jsonl plus plan_ext.jsonl; a missing file raises.
- load_records(rows, units_dir=None, loader=None): reads the live units directory only if frozen_check(rows) passes, otherwise RuntimeError. It reads donor-group records first, then normalises every row.
- normalise(row, rec, ver=None, group=None).
- execution_versions(rows) -> {eid: {version, explicit, notes}}. Versions come from the donor-group rows (P3):
  - a DONOR group is 'primary', or 'continuation_k' along its spec.continuation_of chain;
  - a RICH/CSX group takes the version of its spec.horizon_from core group;
  - bridge, target and zero-shot rows take the version of their spec.donor_group;
  - S rows are always primary;
  - spec.version / execution_version and a downstream row's continuation_of are listed as labels, never used as keys;
  - a cycle raises ValueError.
- identity_values(units, manifest=None, view='primary').
- family_stats(label, metric, Ys, simultaneous=True, declared=None) (P5, P11):
  - each member gets a pointwise summary on its own paired identities: n, est, se, ci_low/high, pct_low/high;
  - res['maxt'] = {declared_members, n_declared, members (in the max-t), n_members, n (family set), crit, note};
  - each member in the max-t gets family_set = {n, est, ci, pct, sim_low/high, sim_position}; the others get family_note;
  - one seed, group_seed(label, metric), is used throughout, so own-set and family-set intervals coincide when the sets are equal.
- run_families(units, manifest=None, out_json=None, out_md=None, out_private=None, meta=None). JSON keys:
  - meta: versions_order, versions, directions, frozen_check, dry_run;
  - coverage: by_configuration (with excluded, selection_levels, selection_level_status, sensitivity_views), design_rows (§4.1), selection_levels legend, identities with units_excluded;
  - pairing: cell_pairs_excluded, cell_pairs_missing, cell_pairs_unregistered, each tagged with view primary or uni_cal; pool_check; member_check; member_check_failures; units_excluded;
  - families: every version; INIT at a continuation pairs against the primary S rows, the only allowed version difference;
  - secondary, access, selection {target_side, donor_groups (fixed table), bridges}, panel (per version), joint_resolution, levels, notes.
- frozen_check(rows=None, record_path=None) (P13): signature changed. The execution record must list the sha256 (full, or a prefix of at least 16 hex digits) of all six code_files() — analysis.py, its test file, select.py, contract.py, sci_r1/stats.py, aggregate.py — and every manifest sha256 of the E34 rows. Returns ok and problems.
- dry_run_problems(units, plans, outputs) and live_records(rows) (P1).

CLI: --plan, --units, --entity-manifest, --res, --docs, --priv, --allow-unfrozen (P1).
- A dry run requires explicit --plan, --units, --res, --docs and --priv. It refuses the live plan files, the live units directory or anything inside it, and outputs under docs/, results/ or private/auditory_alignment_v3/ (resolved paths, os.path.commonpath). It also refuses plan rows that already have a record in the live units directory; this checks existence only and never opens the file.
- The frozen run refuses unless frozen_check passes, and the check happens before any record is read.

Other fixes:
- P2: each cell's complete mode-T units are the reference and must agree with each other. A zero-shot unit whose pool differs, or that sits in a cell whose T units disagree, is excluded from every family, the B_uni_cal sensitivity, levels and identities, with the reason. A cell with no T unit leaves its zero-shot units unverified, listed and kept.
- P4: R_mm is now a risk, Δ = ref − cand (sign flipped from before); kernel_cs_diff is labelled cand − ref (numbers unchanged). Each endpoint's direction is printed.
- P6: selection-level counts and status (as declared / missing / unexpected / no declared level) per configuration, plus one line under each table. Report only; nothing is excluded for this.
- P7: a fixed donor-side table per group: members × _best/_h30/_gainsel on CE_dev, gain, bridge_cal CE and ep-eq, plus horizon, compute limit and ceiling flag. The λ rule is recomputed with select and shown next to the recorded joint_choice and gain-rule choice. Every slot unit's member_resolved is checked against select.member_of(row, group record); units that disagree, and J* units that cannot be resolved, are excluded.
- P8: spec.target, spec.target_contract and the record's target_contract are separate pairing keys.
- P9: a side with no plan row is 'unregistered', listed separately from 'missing'.
- P10: B_uni_cal pairing is kept and listed; view statuses are counted per configuration.
- P12: percentile intervals appear in every Markdown table, in own-identity summaries and in levels. Declared families with nothing registered on either side are collapsed to one line in the Markdown; the JSON keeps everything.

## Open issues / assumed interfaces (fix round)

- The reviewer's 13th item was cut off after "The manifest sha256 seen in rows is not chec…". I implemented a check of the row manifests against the execution record; anything else in that item is unknown.
- M13 (execution record) must list the sha256 of all six code files, including tests/auditory_alignment_v3/prior33/test_analysis.py, sci_r1/stats.py and auditory_alignment/aggregate.py, plus the manifest sha256. Otherwise the frozen run refuses, by design.
- Interfaces assumed for runners not yet written:
  - M5: members[M].{best, h30, gainsel}.{ce_dev, gain, bridge_cal_ce, ep_eq}, joint_choice as select pins it, gain_rule {member}, horizon_ep_eq, ceiling_reached_while_improving.
  - M6/M7: selection_level text (zero-shot text containing "donor dev"), member_resolved (optional), eval_gainsel or gainsel = 'identical', eval_uni_cal, and target_contract overwritten in the record. Bridge records: alpha_uni, alpha_nat, tau_cal, bridge_cal_r, artefact_probe.
  - Field names that differ will show as '–', or as level status 'unexpected'.
- M9 must put continuation_of and horizon_from on donor-group rows (as deps.py requires) and must not re-register S rows; re-registered S rows would abort the run as duplicates.
- PUBLIC_PRIOR_EXECUTION_STATUS (§5.7) is not produced by analysis.py.
- select.py, deps.py and contract.py are being edited concurrently. Every select name analysis.py uses was confirmed present at 00:44; any edit after freezing will make the frozen check refuse, as intended.
- Whether the strict pool rule (excluding all zero-shot units of a cell whose T units disagree) is preferred over reporting only is the researcher's call.
- The real-data analysis is a CPU Slurm job that can run only after the code is frozen in the execution record.

## Second review: remaining low-severity items (fix before freezing the execution record)

- LOW-MED, non-blocking (§5.1 freeze gate, analysis.py:517-541). frozen_check does not verify the chain that §1 defines: the execution record's sha256 is quoted in every E34 plan row's `registered` field. The function only checks that the code and manifest shas appear somewhere in whatever file sits at EXEC_RECORD. So a record rewritten after results were read, for example one that lists a modified analysis.py, still passes. Reproduced: an E34 row whose `registered` field names a different record sha256 gives ok=True. Also, E34 rows without spec.manifest_sha256 pass silently: :530-531 drop the None key, only `e34_rows_without_manifest` is counted, and no problem is raised (reproduced, ok=True). The docstring says the manifest of every E34 row must be listed. Fix: require sha256(EXEC_RECORD), full or a prefix of at least 16 hex digits, in every E34 row's `registered` field, and make a missing manifest_sha256 a problem.
- LOW (the SELECTION and B_uni_cal views are never pool-checked). _pair_check returns None as soon as `ur is uc` (:1126-1127). So the risk→gain contrast never compares the primary and gain-selected evaluations' participant sets, candidate/query counts or n_test_candidates. _pool_check reads only views['primary'] (:1161, :1189), so a zero-shot unit's uni_cal evaluation is never checked against its own primary evaluation or against the mode-T pool. Reproduced: a gain-selected evaluation missing one participant per cell, with n_test_candidates 39, gives 'SELECTION|fau|NCE|T|AP: 4 cell pairs, 11 identities paired, 2 unpaired', no exclusion and no reason. Fix: in the within-unit case compare _sig of the two views and exclude with the reason; compare uni_cal with primary in _pool_check.
- LOW (donor seed of a donor-initialised target row, analysis.py:668). donor_seed comes only from the row's own spec.donor_seed. Unlike the execution version, which is derived from the donor-group row, there is no fallback to the group's seed. A target row without the field lands in configuration fau|NCE|T|AP|d-|t3401|primary, and INIT S->AP then reports 'not registered (reference 4 units, candidate 0 units)' although 4 complete AP units exist (reproduced). Only per-unit notes explain this. Fix: take donor_seed from the spec.donor_group row and flag any disagreement, or report such units as excluded with a reason rather than as unregistered.
- LOW (undeclared cohort × mode, canon_mode :343-354). A zero-shot row in a mode not declared for its cohort is accepted (C.ZS_COHORTS allows Federici only C_partial, DTU only A and C). It forms a configuration that no family or ACCESS entry reads, and nothing lists it. Reproduced: with three Federici mode-'C' units, ACCESS federici A->C_partial says 'not registered (reference 2 units, candidate 0 units)', and the mode-C units appear only in coverage and levels. Fix: check that the cohort is in ZS_COHORTS[mode], and list (or refuse) undeclared configurations in the engineering checks.
- LOW (zero-shot selection level shown as 'declared', :178-179 and :1868). The design declares selection levels for donor records (§2.10) and for public and private target records (§2.12), but none for zero-shot records. SELECTION_LEVEL['zero_shot'] is the analysis's own wording, yet the Markdown prints it under 'Selection levels declared (§1 item 8, §2.10, §2.12)'. _level_status also marks as 'unexpected' any run_zeroshot text that lacks 'donor dev' or 'donor-dev'. Fix: label it as the analysis's assumption, or pin the zero-shot text with M6 in the record interface.
- LOW (test coverage, tests/auditory_alignment_v3/prior33/test_analysis.py:30-37). The synthetic records never cover: DTU (IDS has no 'dtu'); the CSX family (APC/XPC slots, CSX_DONOR groups and their member check); mode C_partial and ACCESS federici A->C_partial; DTU attention; and a NATIVE_REF cell exclusion (E_LOCAL count mismatch). These paths ran without error and recomputed exactly in my fleet probe, but no frozen test guards them.
- COSMETIC. (a) The dry-run banner (:1975) says 'code not frozen in the execution record' whenever --allow-unfrozen is used, even when frozen_check passes. (b) ACCESS entries of a continuation version that has no access rows render one 'not registered (reference 4 units, candidate 0 units)' row per member instead of collapsing into one line, because _nothing_registered (:1738-1740) requires 0 units on both sides.
- INFORMATIONAL (for the execution record). Replicate indices are seeded by group_seed(family label, endpoint) (:1254), not the literal group_seed(family label) of §5.5. NLL and AUC form separate max-t families, which follows the bc_interim precedent. Both are harmless and stated in the module docstring and JSON meta, but they fix the frozen crit values, so the record should quote them. Also, the FAU CI caveat for modes B/C (§2.13, §5.6) appears only in the Estimands section, not beside the pooled FAU ACCESS rows or the FAU B/C level rows.
