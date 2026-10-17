"""E34_PUBLIC_PRIOR C6: the manifest builder (module M2e) for contract aln33_env64_125ms_v1.

Design: private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §1 (fixed before the first donor result), §2.3 (standardiser,
projection), §2.5 (keys, family clocks), §2.6 (strata), §2.10 / §2.11 (selection and bridge sets, budget), §2.13 (mode C), §3
(data binding: donor sets, roles, exclusions, the 30 cells, overlap, coverage), §6.2 C6 and §6.6 M2e; inherited
PUBLIC_PRIOR_EXECUTION_v3_3.md §2-§4 (lists frozen before the first donor result; core first, the rich track non-blocking). The
schema is the M1 fixture's "prior33_manifest_v2" (tests/auditory_alignment_v3/prior33/fixtures.py), which views.open_manifest,
views.py and sampler.py read; this module only adds keys (listed below), so the views read the manifest unchanged.

CLI (a CPU Slurm job through slurm/aln33_prior_cpu.sbatch, minutes; always run with -m):
  python -m auditory_alignment_v3.prior33.manifest --part core --root <cache root> [--out-private DIR]
  python -m auditory_alignment_v3.prior33.manifest --part rich --root <cache root> [--out-private DIR]
  python -m auditory_alignment_v3.prior33.manifest --part core|rich --root <cache root> --dry-run --out <scratch dir> [--bind-private]
  <cache root> = CACHE_ROOT (/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1): production. The
  default --out-private is PRIVATE_OUT = private/auditory_alignment_v3/aln34/prior33/ (design §6.2; created 0700): the directory
  where run_donor.py, run_target.py, bridge.py (PRIVATE_MANIFEST) and make_plan_ext_prior33.py (MANIFEST, the sha256 every row
  quotes) read the full copy. Any other root is a synthetic tree (tests) and must lie outside /projects/EEG-foundation-model.
  --dry-run reads the given root read-only (the real cache root
  is allowed) and writes only into --out, which must lie outside /projects/EEG-foundation-model and outside the repo's private/,
  docs/ and results/; a dry run tolerates missing inputs (C3, C5 cohorts, ALN3 records), lists them under dry_run.missing and
  never binds or writes private child ids (unless --bind-private, which still writes none). Exit 0 written, 1 an input fails a
  check (ManifestError, RestrictedAccess; nothing written), 2 usage, 3 refused by a guard (output location, E34 results already
  present, registered rows quoting another manifest sha256).

Core first (inherited §4: the first envelope training does not wait for the rich track). --part core needs C1, C2, C4
(build_sparrkulee.py), C3 (scan_audio.py) and C5 (build_public.py) only, never C7. --part rich runs after C7 (build_rich.py) and
writes the separate supplement manifest_rich.json, which carries the sha256 of the core manifest (both copies) and of
rich_build.json; open_with_rich() merges it into an opened core manifest for the rich block (§2.15) and verifies the link. This
splits design §6.2's single manifest (C7 before C6) as the M2e task requires; the consumer side is open_for_row(row): a row whose
spec carries manifest_rich_sha256 gets the supplement merged, and a RICH_DONOR row without it is refused (donor_train.py refuses a
rich group whose manifest has no rich block). Production --part rich refuses when registered E34 rows quote another
manifest_rich_sha256, or when an E34 rich-block unit record exists and the supplement on disk would change.

Consumers (the runners; design §4.3, §6.2): open_for_row(row) opens the core manifest by the row's spec.manifest_sha256 from the
full copy PRIVATE_OUT/manifest.json, then the public copy <CACHE_ROOT>/manifest.json, falling through on a sha256 mismatch (rows
quote the full copy, so the redacted public copy never matches them), and merges the supplement when the row quotes one.
run_target.open_manifest and bridge.open_row_manifest fall through the same way; run_donor._open_manifest (2026-10-17 08:45)
returns views.open_manifest on the first existing path and so raises on the public copy (follow-up for M5).

Outputs (JSON with sorted keys, compact, allow_nan false; tmp file + os.replace, then 0444):
  <root>/manifest.json                 the core manifest, PUBLIC copy: identical to the full copy except that the private_bdf cells
                                       carry no child ids (their train / test lists are removed; counts and split hashes stay) and
                                       "copy" is "public_redacted"; it records full_manifest_sha256
  <out-private>/manifest.json          the FULL copy ("copy": "private_full"), 0444 in a 0700 directory: the private_bdf cells list
                                       their children (§3.3 / §6.2: "private IDs are stored only in the 0700 copy"). Its sha256 is
                                       the manifest sha256 every E34 row spec quotes (one sha for every row); the runners open it
                                       by that sha (open_for_row(), or views.open_manifest; cache_root is recorded, so no root= is
                                       needed)
  <root>/P_32x8_seed20261016_f32.npy   P, generated once (numpy QR of the seed, as audio_targets.semi_orthogonal; its sha256 must
                                       start with contract.P_SHA16) and never regenerated
  <root>/manifest_rich.json            (--part rich) the rich supplement, byte-identical in <out-private>/
Keys beyond the fixture schema: copy, full_manifest_sha256 (public copy), dry_run, cache_root, code, inputs, files {relpath:
{sha256, bytes}} (every file the manifest describes: tables, stream tables, env arrays, caches, their C5 done records, C1 / C2 /
C3 files, P; the rich files are in the supplement), checks [{check, ok, detail}], exclusion_rules, exclusion_summary,
declared_before_results, cell_binding, data_coverage, rich_supplement, overlap_scan (per target and donor cohort: scanned or not,
C3's listed streams and how each maps to presentations; C3's caveats), identity_overlap (§3.4.5: unverifiable, said so),
declared_choices (the C6-level choices a reader of the frozen manifest must see: alternative and effect of each),
presentations[].key (the builders' presentation_key: the views map the cohort-local table ids by it), presentations[] sid /
ignored_sid / family_name / noise_condition / snr / noise_file,
families[] root / streams / provisional_names, cohorts[c] items as given (no rich file names: open_with_rich adds them), pools
dev / bridge_cal without any presentation that a donor set excludes, selection / bridge rules, cells[] n_train / n_test /
n_test_only (+ n_test_by_group for private_bdf), shared_audio[] stream / sid.

How each C6 duty is met (design §6.2 C6, task M2e):
- Global ids (design §2.5; the C1 / C4 / C5 tables are id_space cohort_local_provisional): one id space over every cohort.
  presentation id = cohort base + rank of its presentation_key among the cohort's keys (cohorts in COHORTS order); family id =
  cohort base + rank of its C3 family name. Each presentation's family, offset and clock come from C3's families, the presentation
  mapped by its attended stream (C3 stream id: SparrKULee stimulus name, FAU '<code>/attended', DTU target sha, Federici item key;
  a C5 placed masker '<sha>@<offset>' by placement.masker_sha); the table's provisional family_name must be one of that C3
  family's provisional_names (so C4's declared offsets and C5's 'pending_C3' clocks are replaced by C3's measured ones).
  presentation.stream / ignored_stream / ignored_lead stay the cohort-local streams.json indices and table values (views
  check_piece_streams compares them with every cached piece). The tables keep their own ids: the views map pieces by
  presentation_key to presentations[].key (their third id path), independently of this module's own mapping, and cross-check
  every piece against the manifest segment table. Each cached piece is checked here too: its registry presentation, stream,
  ignored stream and lead, kind and attended side, and T_env = the stream length. Every ignored stream of a presentation (FAU
  distractor, DTU placed masker) must have a C3 stream row too, with the C5 source_sha256 and length (a placed masker: its
  placement.base_length), as the attended streams must: a spelling mismatch would otherwise silently disable an exclusion keyed
  on that stream.
- Cells (design §3.3, Option A): the 30 ALN3 A_LOCAL / E_LOCAL cells. Public cells from the C5 tables, which reproduce
  data.load_fau / load_dtu / load_federici (participants, identities, folds of data._folds seed 20261005) with the content split
  of the content fold (FAU data.FAU_CF by kind; DTU content_groups.json half / early_stop; Federici the item role), checked
  against every completed ALN3 A_LOCAL record of seed 3401 for that cell (eval.per_participant keys = test + test_only,
  n_train_participants = |train|; only keys and counts are read). private_bdf cells from the completed E_LOCAL records of seed
  3401 (per fold: the test children = eval.per_participant keys, every record of the fold agreeing; train = the children of the
  other folds; n_train_children checked; group counts kept). split_hash = sha256(json.dumps(cell[SPLIT_FIELDS], sort_keys=True))
  (the fixture's canonicalisation): train ids, test ids, always-train ids, test_only ids, the content lists, rules and seeds.
- Donor pools (design §3.1, §3.4): segments of every cached piece after the guards, the onset rule and C3's shared-audio mask
  (EEG span [s, s + 357) against the spans of the presentation's attended stream, in every role); n_partners counts the other
  listeners of (presentation, s, role) in the donor roles, never the listener's own repeats and never an HC N / HC-v N twin
  (C5 partner_exclusions). pools.core[c]: role fit, kind ss, >= 1 partner, of a donor participant (donor true, not test_only, DTU
  NH only, never the Federici phantom, never a restricted SparrKULee participant; checked, not only taken from the roles);
  pools.csx.fau_cs: FAU fit cs rows. donor_sets[target]: strata DONORS[target] (the target cohort left out; private_bdf never a
  donor), rich = core, csx = core + fau_cs (no CSX for FAU); excluded_presentations: every donor presentation whose attended OR
  ignored stream C3 lists in donor_exclusions[target][donor] (any heard audio, family-propagated by C3); weights = n / sum(n);
  every stratum must hold >= 32 distinct (presentation, s). A listed stream that no cached presentation plays as its attended or
  ignored stream (on the real scan FAU '123/distractor': code 123 is single-talker in C5, ignored_stream None, yet its stereo
  file's other channel is non-silent and the published distractor envelope is finite) is mapped, when its C3 stream row names a
  stimulus code (FAU), to every cached presentation of that code (MAP_UNPLAYED_BY_CODE: the same "any heard audio" reading C3
  already applies when FAU is the target, where this stream is the sole cause of the FAU target's cross-cohort exclusions); one
  without a code is listed (no cached piece plays it, nothing to remove); an entry that names no C3 stream refuses the build.
  overlap_scan records each (target, donor) list, its mapping and C3's caveats: private_bdf was never scanned (C3 not_scanned,
  an unverified assumption), so its empty lists mean "not scanned", not "no overlap found".
- Mode C (design §2.13): a public target is supported only when its own C5 mode-C cache is built with an established unit, every
  donor table has an established unit and build_public.mode_c_scales (band 'target': the same-band pre-z SD in uV, sd_prez_uV
  cross-checked against sd_prez x factor_to_uV) is supported; the Federici target's SparrKULee donor statistic (2-8 Hz) is derived
  with build_public.with_band_sd from the SparrKULee z-cache (C4 records 1-20 Hz only), called once per SparrKULee donor-fit
  participant (the participants mode_c_scales reads) so that each call maps the 4.3 GB cache, touches one participant's rows and
  unmaps it on return: the same values as one call over the table, with resident memory bounded by one participant (at most
  579,456 rows: about 0.3 GB of float64 pieces) instead of the whole mapped cache. cohorts[c].caches lists only the caches
  with a C5 done record (cohort_info.caches always names eeg_raw, M2b review item 2d), each sha256 checked against its record.
- Reconciliations: dtu_reconciliation (C5 checks.inventory_reconciliation, excluded_trials, unread files: every inventory trial
  absent from the cache with its status and reason, the NH single-talker ones as absent_trials, and the shas that drop below 2
  listeners), hc_hcv_excluded_pairs with partner_exclusions, and the structural exclusions (exclusions, exclusion_summary).
- Declared exclusions, fixed before any donor result (exclusions, exclusion_rules; every entry declared: true): the restricted
  participants' runs (listed from the C1 table, never opened by any job), every C2 'misaligned' run (align_audit.jsonl class
  misaligned; C4 must have put it in excluded_rule), every C1 structural anomaly whose clock is not aligned (C4 excluded_rule),
  the declared structural exclusions of DECLARED_EXCLUSIONS, the README-flagged runs (asserted absent from the re-host by C1 and
  here), and every DTU inventory trial the ALN3 loader does not load (C5 inventory_reconciliation.not_loaded: status 'excluded'
  = load_dtu's trial filter, reason per trial from excluded_trials; status 'unread_file' = a file load_dtu never opens, reason
  per file from unread_files; any other status refuses the build), each also an unused-table row.
  DECLARED_EXCLUSIONS holds sub-051 audiobook_12_2, excluded because the M2e task requires it, against §1 and §3.2 (its entry
  cites its basis and its conflicts, and the build checks the C2 numbers its reason quotes): the design scout's backward-decoder
  audit (prior33_provenance/aln34_sparrk/decoder_lag.json, sha256 checked) found tau -566 in a +-10 s search with no prominent
  peak, an output that §1 bars from any decision (that scout also audited the restricted participant 026); C2's registered
  +-40 s rule classes the run 'unverifiable' (tau-hat -1668 / -2220, z 3.40 / 3.19), which §3.2 / F11 would keep; C2's
  descriptive +-10 s diagnostic peaks at -568 / -565 (z 3.29 / 3.12, not measurable). Its segments carry role excluded_declared
  and enter no pool; its cache rows stay in C4's dev slab. C2 'unverifiable' runs are otherwise never excluded for their class
  (F11): exclusion_summary.unverifiable_kept counts those in a donor role (fit / dev / bridge_cal) that no listed exclusion
  removes, unverifiable_by_role the role of every unverifiable run, unverifiable_declared_excluded the declared ones. Production
  refuses to build when any E34 unit record already exists (declared_before_results) or when registered E34 rows quote another
  manifest sha256.
- File hashes (closes the M1 review item): files {relpath: {sha256, bytes}} for every file the manifest describes.

C5 reconciliation (the four C5 differences from the fixture schema, M2b review item 2, and two more from the M2b / M2d reviews):
  (a) FAU competing-talker pieces carry segment_starts (the onset + 1.7 s rule, CSX) and segment_starts_target_stage (guard-only):
      the manifest's donor segment table uses segment_starts (§2.2: the onset rule is "FAU in CSX only"); the target views read
      segment_starts_target_stage from the table themselves (views._target_starts), so nothing else is needed.
  (b) own_repeat_pieces (4 real DTU NH listeners): partners and n_partners count other participants only, n_listeners distinct
      participants; a listener's repeat is never its own partner (the sampler's per-listener partner CSR already expects it).
  (c) cohort-local provisional ids and Federici's 'pending_C3' clocks: replaced by the global ids and C3's families (Global ids).
  (d) cohort_info.caches always names eeg_raw: cohorts[c].caches lists only caches with a C5 done record (mode C: also
      mode_c.built and supported), each sha256 checked against its record.
  (e) sd_prez is in the source unit (FAU volts): mode-C scales come only from build_public.mode_c_scales (sd_prez_uV, checked).
  (f) C7's reason vocabulary (not_selected_dry_run beyond the fixture's four): --part rich reads it from each
      rich_streams.json (reasons / no_source_reasons), never from the fixture constant.

Interpretations (the design names the object, not the detail; each is a deviation of the M2e summary):
- Two copies differ (Design §6.2 "private IDs are stored only in the 0700 copy"): the full copy, written to
  private/auditory_alignment_v3/aln34/prior33/manifest.json as §6.2 names it, holds the private_bdf children and is the manifest
  of record (rows quote its sha256; make_plan_ext_prior33.py reads it there); the public copy is its redaction and names its
  sha256. A runner must therefore reach the full copy even when the public copy exists (Consumers above).
- The fixed sets: selection.fit_segments = 300 SparrKULee core-pool rows (uniform without replacement); selection.dev_queries =
  400 dev-pool rows and bridge.cal_queries = 300 bridge_cal-pool rows, each participant-balanced (water-filling; every listener of
  the role contributes, so cal_split covers every query participant); bridge.cal_split = the bridge_cal query participants in two
  halves by a seeded permutation; bridge.fit_rows[target] = 2,000 rows of the target's core donor set, strata drawn with the
  stratum weights, rows uniform without replacement within a stratum (with replacement only when a stratum holds fewer rows than
  it drew: synthetic trees). A pool smaller than the count is taken whole. Every draw uses its own generator
  SeedSequence([20261016, DRAW_TAGS[...]] (+ target index)), never the bare seed (sampler.bridge_rows draws its montage choices
  from SeedSequence([20261016, 0x4D4F4E54])). Every fixed set and the dev / bridge_cal pools avoid every presentation that any
  donor set excludes (sampler.selection_sets fails closed on them; §3.2 gives all four donor sets one definition); dropped rows are
  listed in checks.
- The standardiser (σ RMS about 0, μ ≡ 0, μ estimate recorded, |μ| / σ < 0.05 asserted) is fitted over the unique (presentation,
  tick) windows of pools.core.sparrkulee without any presentation a donor set excludes (one shared statistic, so it leaves out
  target-overlapping content for every target; inherited §2 / §3: source statistics from donor fit only). On the real C3 scan
  (2026-10-17) C3 flags SparrKULee audiobook_4 (fit content; excluded for the Federici target), audiobook_12_1 (dev; FAU and
  Federici) and audiobook_12_2 (dev; Federici): audiobook_4 is left out of σ and of every fixed set, and the two dev
  presentations leave the shared dev pool for every target (recorded in declared_choices with the rows dropped; the alternative,
  per-target dev / bridge_cal sets, is a design gap for the lead that sampler.selection_sets fails closed on). The rich
  supplement's σ_ss / σ_sc follow the same windows (build_rich.rich_standardiser); C7's stored σ (every C4 fit run) is
  reproduced from C7's arrays as a check and kept as manifest_rich_as_built; C7's PCA-4 basis is used as fitted (it includes
  the fit windows of the presentations the core σ leaves out; recorded in the supplement's declared_choices).
- declared_choices lists these C6-level choices with their alternative and their effect on this build: the shared dev /
  bridge_cal pools, the shared standardiser, the C3 entries mapped by code, the declared exclusions (and, in the supplement, the
  PCA-4 basis). They are fixed with the manifest; a different choice is a new manifest before any donor result.
- N_SK = |pools.core.sparrkulee| (before any per-target exclusion; S0 is the same for every group), as in the fixture.
- Families: every C3 family of a scanned cohort is listed (members may be empty: a stream no cached piece uses); a family whose
  segments fall in two SparrKULee donor roles is refused (C3's family_mask_covers overlaps are unmasked only while families stay
  role-disjoint).
- Dry runs without C3 use the tables' provisional families (a family with an unknown offset or a pending clock is 'unknown') and no
  mask or exclusion; they are flagged and cannot be mistaken for a frozen manifest (dry_run.missing; written to scratch only).

Data-use guards: every path goes through check_path() (RestrictedAccess for a path naming sub-019/020/021/022/026 under a
sparrkulee directory, given or resolved); this module opens no per-run EEG file; it reads the cohort-level caches only to hash
them (streamed) and, for the Federici target's mode-C scale, the SparrKULee z-cache through build_public.with_band_sd (rows of
non-restricted donor-fit participants only: restricted participants have no cache rows and are refused); restricted
runs must have no cache rows, no segment starts and no presentation, and no restricted participant may appear in a segment row
or pool (RestrictedAccess). Nothing is unpickled (np.load allow_pickle=False; JSON with json). Private child ids are written only
into the 0700 private copy, never into a dry run's output.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import io
import json
import math
import os
import re
import sys

import numpy as np

from auditory_alignment_v3.prior33 import contract as C

SCHEMA = "prior33_manifest_v2"                  # = views.SCHEMA (the M1 fixture schema)
RICH_SCHEMA = "prior33_manifest_rich_v1"
CACHE_ROOT = "/projects/EEG-foundation-model/auditory_public/derived/" + C.CONTRACT    # §6.2
DATA_VOLUME = "/projects/EEG-foundation-model"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIVATE_AREA = os.path.join(REPO, "private")
PRIVATE_OUT = os.path.join(REPO, "private", "auditory_alignment_v3", "aln34", "prior33")   # §6.2: the consumers' PRIVATE_MANIFEST
ALN3_PLAN = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010", "plans", "units.jsonl")
UNITS_DIR = os.path.join(REPO, "private", "auditory_alignment_v3", "units")
PLAN_EXT = os.path.join(REPO, "private", "auditory_alignment_v3", "plan_ext.jsonl")
E34_FAMILY_PREFIX = "ALN32_PUBLIC_AUDIO_PRIOR"
RICH_DONOR_FAMILY = E34_FAMILY_PREFIX + "_RICH_DONOR"          # = select.RICH_DONOR (checked by the tests)
RICH_BLOCK = "rich"                                            # spec.block of the rich block's rows (make_plan_ext_prior33.py)
MANIFEST, MANIFEST_RICH = "manifest.json", "manifest_rich.json"
SK_RUNS_TABLE, SK_AUDIT, SK_AUDIT_META, SK_TABLE = "runs_table.json", "align_audit.jsonl", "align_audit_meta.json", "runs.json"
PUB_TABLE, STREAMS, ENV = "pieces.json", "streams.json", "env_f32.npy"
SCAN, SCAN_PTR, SCAN_FAILED = "scan_audio.json", "scan_audio.latest.json", "scan_audio.FAILED.json"
RICH_BUILD, RICH_FILE, RICH_STREAMS, PCA_FILE = "rich_build.json", "rich_f32.npy", "rich_streams.json", "rich_pca4_f64.npy"
SCHEMAS = {"runs_table": "prior33_sparrkulee_runs_table_v1", "audit": "prior33_sparrkulee_align_audit_v1",
           "sk_runs": "prior33_sparrkulee_runs_v1", "sk_streams": "prior33_sparrkulee_streams_v1",
           "pieces": "prior33_public_pieces_v1", "pub_streams": "prior33_public_streams_v1", "cache_done": "prior33_public_cache_v1",
           "scan": "prior33_scan_audio_v1", "scan_ptr": "prior33_scan_audio_latest_v1", "rich_build": "prior33_rich_build_v2",
           "rich_streams": "prior33_rich_streams_v2"}
ID_SPACE = "cohort_local_provisional"

COHORTS = ("sparrkulee", "fau", "dtu", "federici")
PUBLIC = ("fau", "dtu", "federici")
PRIVATE = "private_bdf"
TARGETS = PUBLIC + (PRIVATE,)
DONORS = {"fau": ("sparrkulee", "dtu", "federici"), "dtu": ("sparrkulee", "fau", "federici"),
          "federici": ("sparrkulee", "fau", "dtu"), "private_bdf": ("sparrkulee", "fau", "dtu", "federici")}   # §3.1
DONOR_ROLES = ("fit", "dev", "bridge_cal")
SK_ROLES = ("fit", "dev", "bridge_cal", "holdout_seen_content", "control_artefact", "excluded_rule", "restricted")
PUB_ROLES = ("fit", "target_only")
DECLARED_ROLE = "excluded_declared"
RESTRICTED = ("019", "020", "021", "022", "026")       # access-restricted SparrKULee participants (§3.2): never opened
README_FLAGGED = (("006", "shortstories01", "06"), ("017", "shortstories01", "03"), ("048", "varyingStories05", "04"))
DECLARED_EXCLUSIONS = (
    # Required by the M2e task (lead); it conflicts with design §1 and §3.2, and the entry says so. `basis` names the files its
    # reason cites (sha256 checked when the file exists; required in production); `expect_c2` the C2 numbers its reason quotes
    # (checked against align_audit.jsonl: a recomputed C2 that differs refuses the build, so the reason never goes stale).
    {"cohort": "sparrkulee", "sub": "051", "stimulus": "audiobook_12_2", "rule": "declared_structural_exclusion",
     "required_by": "task M2e (lead): 'exclude it explicitly as a declared structural exclusion and say so'",
     "basis": [{"file": "private/auditory_alignment_v3/aln34/prior33_provenance/aln34_sparrk/decoder_lag.json",
                "sha256": "225bc8c422ccb5b644812ff1befd4d37ce2629e18a1e8cc0fe32b6d30f679a3f", "entry": "051:audiobook_12_2",
                "values": {"tau_samples": -566, "r_peak": 0.0517, "r_at_0": 0.028, "r_offpeak_absmax(|tau|>1s)": 0.0517,
                           "search_s": 10, "n_refs": 7},
                "produced_by": "private/auditory_alignment_v3/aln34/prior33_provenance/aln34_sparrk/decoder_lag.py (design scout)"}],
     "expect_c2": {"class": "unverifiable", "tau": [-1668, -2220], "z_2dp": [3.40, 3.19],
                   "diagnostic": {"full_tau": -566, "full_z_2dp": 4.04, "halves_tau": [-568, -565], "halves_z_2dp": [3.29, 3.12]}},
     "conflicts": ["design §1: the outputs of the scout aln34_sparrk/decoder_lag.py are 'not used for any decision' (that scout also "
                   "audited the restricted participant 026, audiobook_1); this exclusion rests on one of them",
                   "design §3.2 and F11: SparrKULee runs are excluded only by the two fixed rules, and a C2 'unverifiable' run is "
                   "kept; C2's registered rule classes this run 'unverifiable'"],
     "reason": "declared structural exclusion required by task M2e, fixed before any donor result and departing from design §3.2 / "
               "F11. Basis: the design scout's backward-decoder audit (aln34_sparrk/decoder_lag.py -> prior33_provenance/"
               "aln34_sparrk/decoder_lag.json, sha256 225bc8c4..., entry 051:audiobook_12_2) gives tau -566 samples (-8.84 s) in a "
               "+-10 s search, with r_peak 0.0517. Its off-peak maximum is defined relative to zero lag (|tau| > 1 s), so it includes this peak and does not measure its prominence; this audit is the source of "
               "design §1's 'one run misaligned by -566 samples' and of §3.2's expectation that C2 classes the run misaligned. "
               "C2's own +-10 s diagnostic (restricted-free references; descriptive only) also peaks there: -566 over the run "
               "(z 4.04), -568 / -565 in the halves (z 3.29 / 3.12, below the measurability threshold z >= 5). C2's registered "
               "+-40 s clock-validity rule classes the run 'unverifiable': tau-hat -1668 / -2220 samples, z 3.40 / 3.19 (neither "
               "half measurable; the halves disagree), which §3.2 / F11 would keep. Conflicts: §1 bars every output of "
               "decoder_lag.py from any decision; §3.2 / F11 keep unverifiable runs. The run is excluded here explicitly instead "
               "of being kept by the rule"},
)
MAP_UNPLAYED_BY_CODE = True     # C3 exclusion entries no cached presentation plays -> the presentations of their stimulus code (FAU)
PROVENANCE = os.path.join(REPO, "private", "auditory_alignment_v3", "aln34", "prior33_provenance")
N_FIT, N_DEV, N_CAL, N_BRIDGE = 300, 400, 300, 2000      # §2.10: 300 fit segments, 400 dev queries; §2.11: 300 cal queries, 2,000 rows
DRAW_TAGS = {"fit_segments": 0x43360001, "dev_queries": 0x43360002, "cal_queries": 0x43360003, "cal_split": 0x43360004,
             "bridge_fit": 0x43360005}
BATCH_SEGMENTS = 32                                      # §2.6 design batch: 32 distinct (presentation, s) per stratum
MU_RATIO_MAX = 0.05                                      # §2.3: C6 asserts |mu| / sigma < 0.05
MODE_C = {"fau": "C", "dtu": "C", "federici": "C_partial"}
CELLS = (("fau", 5, (0, 1)), ("dtu", 5, (0, 1)), ("federici", 5, (0,)), ("private_bdf", 5, (0,)))
SPLIT_FIELDS = ("dataset", "subject_fold", "content_fold", "always_train", "test_only", "train", "test", "content",
                "content_groups", "rules", "seeds")
PRIVATE_ID_FIELDS = ("train", "test")
ALN3_FAMILY = {"fau": "A_LOCAL", "dtu": "A_LOCAL", "federici": "A_LOCAL", "private_bdf": "E_LOCAL"}
CELL_RULES = {
    "fau": {"subjects": "auditory_alignment.data.fau_panel(): the TH selection half (th_split.json selection_half) always trains "
                        "(fold -1, dev); the heldout TH, HA and CI ids are folded per group by data._folds (seed 20261005, 5 folds)",
            "train": "not test_only and (dev or fold != subject_fold)", "test": "not dev and not test_only and fold == subject_fold",
            "content": "auditory_alignment.data.FAU_CF[content_fold][kind]: a code takes the role whose digits hold its part digit "
                       "code[2]; kinds ss (single talker: training) and cs (competing talker: attention 2AFC only)",
            "source": "C5 pieces.json (build_public.py reproduces data.load_fau's participants and folds)"},
    "dtu": {"subjects": "data._folds over the NH and over the HI subjects of private/auditory_c3/public/dtu_v2 (seed 20261005, 5 "
                        "folds)", "train": "fold != subject_fold", "test": "fold == subject_fold",
            "content": "kcs_targets_v1/content_groups.json per target sha: test when half == content_fold, else es when early_stop, "
                       "else fit (data.load_dtu); every trial kind of a sha takes its role",
            "source": "C5 pieces.json (build_public.py reproduces data.load_dtu's participants, trial filter and folds)"},
    "federici": {"subjects": "data._folds over the identities (HC N and HC-v N share the fold key N, Option A; CI 'CI:<id>'), seed "
                             "20261005, 5 folds; HC-v children stay separate identities; the phantom sessions are test_only",
                 "train": "not test_only and fold != subject_fold", "test": "not test_only and fold == subject_fold",
                 "content": "kcs_targets_v1 content_groups.json item role (strict unseen-content split by envelope content group, "
                            "data.load_federici); one content fold",
                 "source": "C5 pieces.json (build_public.py reproduces data.load_federici's people, identities and folds)"},
    "private_bdf": {"subjects": "auditory_c3.c3dl.hc.folds (seed 20261005, strata HA / NH, kid order), bound from the completed ALN3 "
                                "E_LOCAL unit records of seed 3401 (test children = eval.per_participant of the fold; every record of "
                                "the fold agrees)", "train": "the children of the other folds", "test": "the children of the fold",
                    "content": "no content axis; early stopping on the last 20 % of each child's physical blocks (es_mask; children "
                               "with fewer than 3 blocks contribute no es trial)",
                    "source": "ALN3 E_LOCAL unit records (keys and counts only)"},
}
SEEDS = {"folds": C.FOLD_SEED}
PRIVATE_CONTENT = {"es": "last 20 % of each child's physical blocks"}
EXCLUSION_RULES = {
    "restricted_participant": "access-restricted SparrKULee participant (dataset_description.json Notes of the re-host): listed from "
                              "file names and .npy headers only (C1); no array of theirs is opened by any job",
    "clock_misaligned": "C2 clock-validity rule (§3.2): both halves measurable (z >= 5), |tau_1 - tau_2| <= 4 and |mean tau| > 4 "
                        "samples; C4 slab excluded_rule; never shifted",
    "structural_anomaly_unverified_clock": "C1 structural-anomaly rule (|T_eeg - modal co-listener T_eeg| > 8 samples) and a C2 clock "
                                           "that is not 'aligned' (§3.2); C4 slab excluded_rule",
    "declared_structural_exclusion": "a run excluded explicitly by this manifest before any donor result (DECLARED_EXCLUSIONS; reason "
                                     "per entry); its segments carry role excluded_declared and enter no pool",
    "readme_flagged": "a run the dataset README flags; asserted absent from the re-host (C1 readme_flagged_absent and no runs.json "
                      "row)",
    "aln3_loader_filter": "a DTU inventory trial that auditory_alignment.data.load_dtu does not load, as C5 records it in "
                          "checks.inventory_reconciliation.not_loaded: status 'excluded' (load_dtu's trial filter; reason per trial, "
                          "from excluded_trials) or 'unread_file' (in a file load_dtu never opens; reason per file, from "
                          "unread_files); any other status refuses the build (design §3.3, §3.5)",
}


class ManifestError(ValueError):
    """An input fails a C6 check: nothing is written."""


class Refused(RuntimeError):
    """A guard refuses the build (results already exist, an output location, a frozen manifest would change)."""


class RestrictedAccess(PermissionError):
    """A path or a row of an access-restricted SparrKULee participant was about to be used (design §3.2)."""


_SK_RESTRICTED = re.compile(r"sub-(%s)(?![0-9])" % "|".join(RESTRICTED))


def check_path(path):
    """The path unchanged, or RestrictedAccess when it (given or resolved) lies under a sparrkulee directory and names a restricted
    participant (sub-019 / 020 / 021 / 022 / 026)."""
    raw = os.fspath(path)
    for p in (raw, os.path.realpath(raw)):
        low = p.casefold()
        if "sparrkulee" in low and _SK_RESTRICTED.search(low):
            raise RestrictedAccess(f"refusing {raw!r}: restricted SparrKULee participant (PUBLIC_PRIOR_DESIGN.md §3.2)")
    return raw


# ---------------------------------------------------------------------------------------------------------- small helpers
def _sha(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path, chunk=16 << 20):
    """(sha256, bytes) of a file, streamed through one reusable buffer (RSS stays small for the multi-GB caches)."""
    h, n = hashlib.sha256(), 0
    buf = bytearray(chunk)
    mv = memoryview(buf)
    with open(check_path(path), "rb", buffering=0) as f:
        while True:
            k = f.readinto(buf)
            if not k:
                break
            h.update(mv[:k])
            n += k
    return h.hexdigest(), n


def _plain(o):
    """JSON-ready copy: numpy scalars / arrays to Python, tuples to lists, dict keys to str."""
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, np.ndarray):
        return _plain(o.tolist())
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    return o


def dumps(obj):
    """The bytes of a manifest file: sorted keys, compact separators, no NaN / Infinity."""
    return json.dumps(_plain(obj), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def split_hash(cell):
    """sha256 of the cell's binding fields (SPLIT_FIELDS present in the cell) as json.dumps(..., sort_keys=True): the fixture's
    canonicalisation (train / test / always-train / test_only ids, content lists, rules and seeds)."""
    d = {k: cell[k] for k in SPLIT_FIELDS if k in cell}
    return _sha(json.dumps(_plain(d), sort_keys=True).encode())


def _write(path, raw, mode=0o444):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def _inside(path, base):
    p, b = os.path.realpath(path), os.path.realpath(base)
    return p == b or p.startswith(b.rstrip(os.sep) + os.sep)


def _same(a, b):
    return os.path.realpath(a) == os.path.realpath(b) or os.path.abspath(a) == os.path.abspath(b)


def coh_of(stratum):
    return "fau" if stratum == "fau_cs" else stratum


def semi_orthogonal(d, n, seed):
    """auditory_alignment_v2.audio_targets.semi_orthogonal(d, n, seed) in numpy (its body: numpy QR of the seeded normal matrix,
    then float32), so the builder needs no torch; the sha256 is checked against contract.P_SHA16."""
    g = np.random.default_rng(seed).standard_normal((max(d, n), min(d, n)))
    q, _ = np.linalg.qr(g)
    return (q.T if n >= d else q).astype(np.float32)


def _rng(*tags):
    return np.random.default_rng(np.random.SeedSequence([C.BRIDGE_SEED, *[int(t) for t in tags]]))


class _Ctx:
    """Build state: the cache root, the mode, the files read (relpath -> sha256 / bytes), the checks and the dry-run notes."""

    def __init__(self, root, mode, log):
        self.root, self.mode, self.log = os.path.abspath(root), mode, log
        self.files, self.checks, self.missing, self.notes = {}, [], [], []

    @property
    def strict(self):
        return self.mode != "dry_run"

    def path(self, *p):
        return os.path.join(self.root, *p)

    def rel(self, path):
        return os.path.relpath(os.path.abspath(path), self.root).replace(os.sep, "/")

    def fail(self, msg, missing=False):
        if self.strict:
            raise ManifestError(msg)
        (self.missing if missing else self.notes).append(msg)
        self.log(f"[manifest dry run] {msg}")

    def check(self, name, ok, detail=None, hard=True):
        self.checks.append({"check": name, "ok": bool(ok), "detail": _plain(detail)})
        if not ok and hard:
            self.fail(f"{name}: {detail}")
        return bool(ok)

    def read_bytes(self, path, describe=True):
        with open(check_path(path), "rb") as f:
            raw = f.read()
        if describe:
            self.files[self.rel(path)] = {"sha256": _sha(raw), "bytes": len(raw)}
        return raw

    def read_json(self, path, describe=True):
        raw = self.read_bytes(path, describe)
        return json.loads(raw), _sha(raw)

    def read_npy(self, path, describe=True):
        raw = self.read_bytes(path, describe)
        return np.load(io.BytesIO(raw), allow_pickle=False), _sha(raw)

    def hash_big(self, path):
        """Stream-hash a cache and read its .npy header (memory map, no data read): (sha256, shape, dtype)."""
        sha, n = sha256_file(path)
        self.files[self.rel(path)] = {"sha256": sha, "bytes": n}
        a = np.load(check_path(path), mmap_mode="r", allow_pickle=False)
        shape, dtype = tuple(int(x) for x in a.shape), a.dtype
        del a
        return sha, shape, dtype


# ---------------------------------------------------------------------------------------------------------- output locations
def resolve_mode(root, out=None, out_private=None, dry_run=False):
    """(mode, out, out_private): 'production' (root = CACHE_ROOT), 'local' (a synthetic tree outside the data volume) or
    'dry_run' (read root, write only into a scratch --out). Raises Refused for any other combination."""
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise Refused(f"--root {root} is not a directory")
    production = _same(root, CACHE_ROOT)
    forbidden = [DATA_VOLUME] + [os.path.join(REPO, x) for x in ("private", "docs", "results")]
    if dry_run:
        if out is None:
            raise Refused("--dry-run needs --out <scratch dir> (a dry run writes nothing under --root)")
        out = os.path.abspath(out)
        bad = [b for b in forbidden if _inside(out, b)]
        if bad or _inside(out, root) or _inside(root, out):
            raise Refused(f"dry-run --out {out} must lie outside {bad or [root]} (scratch only)")
        out_private = os.path.abspath(out_private) if out_private else os.path.join(out, "private")
        if not _inside(out_private, out):
            raise Refused(f"dry-run --out-private {out_private} must lie inside --out {out}")
        return "dry_run", out, out_private
    if out is not None and not _same(out, root):
        raise Refused("--out is for dry runs only: the manifest is written to <root>/manifest.json")
    if production:
        out_private = os.path.abspath(out_private) if out_private else PRIVATE_OUT
        if not _inside(out_private, PRIVATE_AREA):
            raise Refused(f"--out-private {out_private} must lie inside the 0700 area {PRIVATE_AREA}")
        return "production", root, out_private
    if _inside(root, DATA_VOLUME):
        raise Refused(f"--root {root}: only {CACHE_ROOT} (production) may lie under {DATA_VOLUME}; a synthetic tree goes elsewhere "
                      "(or use --dry-run --out <scratch>)")
    if out_private is None:
        raise Refused("a synthetic root needs an explicit out_private directory")
    out_private = os.path.abspath(out_private)
    if _inside(out_private, PRIVATE_AREA) or _inside(out_private, DATA_VOLUME):
        raise Refused(f"out_private {out_private}: a synthetic build must not write into {PRIVATE_AREA} or {DATA_VOLUME}")
    return "local", root, out_private


# ---------------------------------------------------------------------------------------------------------- inputs: C1 / C2 / C4
def _streams_ok(ctx, cohort, rows, env):
    off = 0
    for i, r in enumerate(rows):
        if int(r["stream"]) != i or int(r["offset"]) != off or int(r["length"]) <= 0:
            raise ManifestError(f"{cohort} streams.json: stream {i} ({r.get('name')}) is not at offset {off} in stream order")
        off += int(r["length"])
    if env.dtype != np.float32 or env.ndim != 1 or off != len(env):
        raise ManifestError(f"{cohort}: env_f32.npy {env.dtype} {env.shape} vs streams covering {off} samples")


def _check_cohort_info(ctx, cohort, info, cache_shape=None):
    lay = tuple(C.canonical(n) for n in info["layout"])
    bad = []
    if lay != C.MONTAGES[cohort] or int(info["n_ch"]) != len(lay):
        bad.append("layout / n_ch differ from contract.MONTAGES")
    if tuple(int(g) for g in info["guards"]) != C.GUARDS[cohort] or int(info["s_first"]) != C.S_FIRST[cohort]:
        bad.append("guards / s_first differ from the contract")
    if cache_shape is not None and tuple(cache_shape) != (int(info["n_rows"]), len(lay)):
        bad.append(f"cache shape {cache_shape} vs n_rows {info['n_rows']} x {len(lay)}")
    if bad:
        raise ManifestError(f"{cohort} cohort_info: " + "; ".join(bad))


def _check_slabs(cohort, items, slabs, n_rows):
    """Every role slab is covered exactly, contiguously and in order by its cached pieces; slabs tile [0, n_rows)."""
    spans = sorted((int(a), int(b), s) for s, (a, b) in slabs.items())
    pos = 0
    for a, b, s in spans:
        if a != pos or b < a:
            raise ManifestError(f"{cohort} role_slabs: slab {s} [{a}, {b}) does not continue at {pos}")
        mine = sorted((int(it["row_offset"]), int(it["T_eeg"])) for it in items
                      if it.get("row_offset") is not None and it.get("slab", it.get("role")) == s)
        p = a
        for off, T in mine:
            if off != p:
                raise ManifestError(f"{cohort} slab {s}: rows [{p}, {off}) are not covered by a listed piece")
            p = off + T
        if p != b:
            raise ManifestError(f"{cohort} slab {s}: listed pieces end at {p}, the slab at {b}")
        pos = b
    if pos != int(n_rows):
        raise ManifestError(f"{cohort} role_slabs end at {pos}, the cache holds {n_rows} rows")


def load_sparrkulee(ctx):
    """C1 runs_table.json, C2 align_audit.jsonl (+ meta), C4 runs.json / streams.json / env_f32.npy / eeg_f16_tmajor.npy, checked
    against each other (the sha chain C1 -> C2 -> C4) and against the data-use rules (restricted, README, C2 classes)."""
    d = ctx.path("sparrkulee")
    need = [SK_RUNS_TABLE, SK_AUDIT, SK_AUDIT_META, SK_TABLE, STREAMS, ENV, C.CACHE_FILE["A"]]
    miss = [f for f in need if not os.path.exists(os.path.join(d, f))]
    if miss:
        raise ManifestError(f"C1 / C2 / C4 outputs missing under {d}: {miss} (build_sparrkulee.py --stage C1, C2, C4)")
    rt, rt_sha = ctx.read_json(os.path.join(d, SK_RUNS_TABLE))
    araw = ctx.read_bytes(os.path.join(d, SK_AUDIT))
    a_sha = _sha(araw)
    audit = [json.loads(line) for line in araw.decode().splitlines() if line.strip()]
    meta, _ = ctx.read_json(os.path.join(d, SK_AUDIT_META))
    runs, runs_sha = ctx.read_json(os.path.join(d, SK_TABLE))
    streams_doc, _ = ctx.read_json(os.path.join(d, STREAMS))
    env, env_sha = ctx.read_npy(os.path.join(d, ENV))
    cache_sha, cache_shape, cache_dtype = ctx.hash_big(os.path.join(d, C.CACHE_FILE["A"]))
    for name, doc, want in (("runs_table.json", rt, SCHEMAS["runs_table"]), ("align_audit_meta.json", meta, SCHEMAS["audit"]),
                            ("runs.json", runs, SCHEMAS["sk_runs"]), ("streams.json", streams_doc, SCHEMAS["sk_streams"])):
        if doc.get("schema") != want or doc.get("contract", C.CONTRACT) != C.CONTRACT:
            raise ManifestError(f"sparrkulee {name}: schema {doc.get('schema')!r} / contract {doc.get('contract')!r}, {want} expected")
    if runs.get("id_space") != ID_SPACE:
        raise ManifestError(f"sparrkulee runs.json id_space {runs.get('id_space')!r}, {ID_SPACE} expected")
    ctx.check("C2 align_audit_meta records the align_audit.jsonl and runs_table.json it was built from",
              meta.get("align_audit_sha256") == a_sha and meta.get("runs_table_sha256") == rt_sha,
              {"meta": [meta.get("align_audit_sha256"), meta.get("runs_table_sha256")], "files": [a_sha, rt_sha]})
    ctx.check("C4 runs.json was built from these C1 / C2 files",
              (runs.get("inputs") or {}).get("align_audit_sha256") == a_sha and (runs.get("inputs") or {}).get("runs_table_sha256") == rt_sha,
              {"inputs": runs.get("inputs"), "files": {"align_audit_sha256": a_sha, "runs_table_sha256": rt_sha}})
    ctx.check("every C2 record was built from this runs_table.json", all(r.get("runs_table_sha256") == rt_sha for r in audit),
              sorted({str(r.get("runs_table_sha256"))[:16] for r in audit}))
    items = runs["runs"]
    streams = streams_doc["streams"]
    _streams_ok(ctx, "sparrkulee", streams, env)
    info = runs["cohort_info"]
    _check_cohort_info(ctx, "sparrkulee", info, cache_shape)
    if cache_dtype != np.float16:
        raise ManifestError(f"sparrkulee cache dtype {cache_dtype}, float16 expected")
    _check_slabs("sparrkulee", items, info["role_slabs"], info["n_rows"])
    ids = [r["run_id"] for r in items]
    if len(set(ids)) != len(ids) or set(ids) != {r["run_id"] for r in rt["runs"]} or set(ids) != {r["run"] for r in audit}:
        raise ManifestError("sparrkulee: runs.json, runs_table.json and align_audit.jsonl list different runs")
    # restricted participants: listed only (no rows, no starts, no presentation, not audited)
    rset = {str(x) for x in rt.get("restricted", [])}
    ctx.check("the restricted set is the design's five participants", rset == set(RESTRICTED), sorted(rset))
    aud = {r["run"]: r for r in audit}
    for r in items:
        sub = str(r.get("sub", r.get("participant")))
        restricted = sub in RESTRICTED
        if restricted != (r.get("role") == "restricted"):
            raise RestrictedAccess(f"sparrkulee {r['run_id']}: participant sub-{sub} has role {r.get('role')!r}")
        if restricted and (r.get("row_offset") is not None or r.get("segment_starts") or r.get("presentation") is not None):
            raise RestrictedAccess(f"sparrkulee {r['run_id']}: a restricted run with cache rows, segments or a presentation")
        if restricted and aud[r["run_id"]].get("class") != "not_audited":
            raise RestrictedAccess(f"sparrkulee {r['run_id']}: a restricted run that C2 audited")
        if r.get("role") not in SK_ROLES:
            raise ManifestError(f"sparrkulee {r['run_id']}: role {r.get('role')!r}")
        if (r.get("audit") or {}).get("clock") != aud[r["run_id"]].get("class"):
            raise ManifestError(f"sparrkulee {r['run_id']}: C4 audit {r.get('audit', {}).get('clock')!r} vs C2 class "
                                f"{aud[r['run_id']].get('class')!r}")
    # README-flagged runs: absent
    flagged = [tuple(map(str, x)) for x in rt.get("readme_flagged", [])]
    present = sorted({(str(r["sub"]), str(r["ses"]), str(r["run"])) for r in items} & set(flagged))
    ctx.check("the README-flagged runs are the design's three and are absent from the re-host",
              sorted(flagged) == sorted(README_FLAGGED) and rt.get("readme_flagged_absent") is True and not present,
              {"flagged": flagged, "readme_flagged_absent": rt.get("readme_flagged_absent"), "present": present})
    # C2 'misaligned' <-> C4 clock_misaligned <-> excluded_rule; structural anomalies
    mis = sorted(r["run"] for r in audit if r.get("class") == "misaligned")
    flag_mis = sorted(r["run_id"] for r in items if "clock_misaligned" in (r.get("flags") or []))
    ctx.check("every C2 'misaligned' run (and only those) carries C4's clock_misaligned flag", mis == flag_mis,
              {"c2": mis, "c4": flag_mis})
    c1 = {r["run_id"]: r for r in rt["runs"]}
    invalid_refs = []
    for audit_row in audit:
        for ref in audit_row.get("refs") or []:
            src = c1.get(ref)
            if src is None or str(src.get("sub")) in RESTRICTED or (src.get("structural") or {}).get("anomalous"):
                invalid_refs.append([audit_row["run"], ref])
    ctx.check("C2 references contain no restricted participants or C1 structural anomalies", not invalid_refs, invalid_refs)
    struct_bad = []
    for r in items:
        fl = set(r.get("flags") or [])
        anomalous = bool((c1[r["run_id"]].get("structural") or {}).get("anomalous"))
        cls = aud[r["run_id"]].get("class")
        if fl and r.get("role") != "excluded_rule":
            struct_bad.append([r["run_id"], "flagged but not excluded_rule"])
        if "structural_anomaly_unverified_clock" in fl and (not anomalous or cls == "aligned"):
            struct_bad.append([r["run_id"], "structural flag without a C1 anomaly or with an aligned clock"])
        if anomalous and cls not in ("aligned", "not_audited") and "structural_anomaly_unverified_clock" not in fl \
                and "clock_misaligned" not in fl:
            struct_bad.append([r["run_id"], "C1 anomaly with an unaligned clock kept"])
        if r.get("row_offset") is not None:
            rule = C.segment_starts(int(r["T_env"]), int(r["T_eeg"]), "sparrkulee").tolist()
            if [int(s) for s in r.get("segment_starts") or []] != rule:
                struct_bad.append([r["run_id"], "segment_starts differ from contract.segment_starts"])
    ctx.check("C1 structural anomalies and C2 classes agree with C4's roles and segment starts", not struct_bad, struct_bad)
    table = {k: v for k, v in runs.items()}
    return {"cohort": "sparrkulee", "table": table, "items": items, "streams": streams, "env": env, "info": info,
            "reg": runs["presentations"], "fams": runs.get("families", []), "caches": {"A": C.CACHE_FILE["A"]},
            "cache_sha": {"A": cache_sha}, "participants": {str(p["participant"]): p for p in runs["participants"]},
            "runs_table": rt, "audit": aud, "audit_meta": meta, "sha": {"runs_table": rt_sha, "align_audit": a_sha, "runs": runs_sha,
                                                                          "env": env_sha}}


# ---------------------------------------------------------------------------------------------------------- inputs: C5
def load_public(ctx, cohort):
    """C5 pieces.json / streams.json / env_f32.npy and the caches with a done record (each cache's sha256 checked against it)."""
    d = ctx.path(cohort)
    need = [PUB_TABLE, STREAMS, ENV]
    if not all(os.path.exists(os.path.join(d, f)) for f in need):
        ctx.fail(f"C5 {cohort}: {need} missing under {d} (build_public.py --cohort {cohort})", missing=True)
        return None
    t, t_sha = ctx.read_json(os.path.join(d, PUB_TABLE))
    st, _ = ctx.read_json(os.path.join(d, STREAMS))
    env, env_sha = ctx.read_npy(os.path.join(d, ENV))
    for name, doc, want in (("pieces.json", t, SCHEMAS["pieces"]), ("streams.json", st, SCHEMAS["pub_streams"])):
        if doc.get("schema") != want or doc.get("contract", C.CONTRACT) != C.CONTRACT or doc.get("cohort") != cohort:
            raise ManifestError(f"{cohort} {name}: schema {doc.get('schema')!r}, cohort {doc.get('cohort')!r}; {want} expected")
    if t.get("id_space") != ID_SPACE:
        raise ManifestError(f"{cohort} pieces.json id_space {t.get('id_space')!r}, {ID_SPACE} expected")
    if t.get("partial"):
        ctx.fail(f"C5 {cohort}: pieces.json is a partial (--participants) build", missing=True)
    streams = st["streams"]
    _streams_ok(ctx, cohort, streams, env)
    info = t["cohort_info"]
    caches, cache_sha = {}, {}
    for cm, rec in sorted((t.get("caches") or {}).items()):
        path = os.path.join(d, rec["file"])
        if rec.get("schema") != SCHEMAS["cache_done"] or rec.get("cache_mode") != cm or rec["file"] != C.CACHE_FILE[cm]:
            raise ManifestError(f"{cohort} cache record {cm}: {rec.get('schema')} {rec.get('cache_mode')} {rec.get('file')}")
        done, _ = ctx.read_json(path + ".done.json")
        sha, shape, dtype = ctx.hash_big(path)
        if done != rec or rec.get("sha256") != sha or dtype != np.float16:
            raise ManifestError(f"{cohort} {rec['file']}: sha256 {sha[:16]} / dtype {dtype} vs the done record "
                                f"{str(rec.get('sha256'))[:16]} (or the table's copy of the record differs from the file)")
        _check_cohort_info(ctx, cohort, info, shape)
        caches[cm], cache_sha[cm] = rec["file"], sha
    _check_cohort_info(ctx, cohort, info)
    if "A" not in caches:
        ctx.fail(f"C5 {cohort}: no mode-A cache with a done record yet", missing=True)
    if cohort == "fau" and "B" not in caches:
        ctx.fail("C5 fau: no mode-B (noica) cache with a done record yet", missing=True)
    items = t["pieces"]
    _check_slabs(cohort, items, info["role_slabs"], info["n_rows"])
    bad = []
    for it in items:
        if it.get("role") not in PUB_ROLES or it.get("slab", it.get("role")) != it.get("role"):
            bad.append([it.get("piece_id"), it.get("role"), it.get("slab")])
            continue
        onset = it.get("onset_s") if it.get("kind") == "cs" else None
        rule = C.segment_starts(int(it["T_env"]), int(it["T_eeg"]), cohort, onset=onset).tolist()
        if [int(s) for s in it.get("segment_starts") or []] != rule:
            bad.append([it.get("piece_id"), "segment_starts differ from contract.segment_starts"])
    ctx.check(f"{cohort}: every piece has a C5 role and the contract's segment starts", not bad, bad[:5])
    return {"cohort": cohort, "table": t, "items": items, "streams": streams, "env": env, "info": info, "reg": t["presentations"],
            "fams": t.get("families", []), "caches": caches, "cache_sha": cache_sha,
            "participants": {str(p["participant"]): p for p in t["participants"]}, "sha": {"pieces": t_sha, "env": env_sha}}


# ---------------------------------------------------------------------------------------------------------- inputs: C3
def load_scan(ctx):
    """C3 scan_audio.json, read only when scan_audio.latest.json says status ok for its sha256 (scan_audio.py's rule)."""
    p, q = ctx.path(SCAN), ctx.path(SCAN_PTR)
    if not (os.path.exists(p) and os.path.exists(q)):
        ctx.fail(f"C3 {SCAN} / {SCAN_PTR} missing under {ctx.root} (scan_audio.py)", missing=True)
        return None
    ptr, _ = ctx.read_json(q)
    raw = ctx.read_bytes(p)
    sha = _sha(raw)
    doc = json.loads(raw)
    ok_ptr = ptr.get("schema") == SCHEMAS["scan_ptr"] and ptr.get("status") == "ok" and ptr.get("file") == SCAN and \
        ptr.get("sha256") == sha
    ok_doc = doc.get("schema") == SCHEMAS["scan"] and doc.get("contract") == C.CONTRACT and doc.get("ok") is True and \
        doc.get("complete") is True and list(doc.get("cohorts_scanned") or []) == list(COHORTS)
    ctx.check("C3 pointer scan_audio.latest.json says ok for this scan_audio.json", ok_ptr,
              {k: ptr.get(k) for k in ("schema", "status", "file", "sha256")})
    ctx.check("C3 scan ok, complete, every cohort scanned", ok_doc,
              {k: doc.get(k) for k in ("schema", "ok", "complete", "cohorts_scanned")})
    if not (ok_ptr and ok_doc):
        return None
    fx = ctx.path(SCAN_FAILED)
    cc = doc.get("cross_cohort") or {}
    rec = {"file": SCAN, "sha256": sha, "pointer": {k: ptr.get(k) for k in ("status", "file", "sha256", "created_utc", "superseded",
                                                                            "stale")},
           "builder_sha256": (doc.get("builder") or {}).get("sha256"), "created_utc": doc.get("created_utc"),
           "signature": doc.get("signature"), "failed_file_present": os.path.exists(fx),
           "not_scanned": cc.get("not_scanned") or {}, "assumptions": list(doc.get("assumptions") or []),
           "donor_exclusion_rule": cc.get("donor_exclusion_rule")}
    warn = [c for c in doc.get("checks", []) if not c.get("ok")]
    ctx.check("C3 assert-level checks all passed", not [c for c in warn if c.get("level") == "assert"],
              [c.get("check") for c in warn if c.get("level") == "assert"])
    rec["warnings"] = [c.get("check") for c in warn if c.get("level") != "assert"]
    return {"doc": doc, "sha256": sha, "record": rec}


# ---------------------------------------------------------------------------------------------------------- global ids
def c3_sid(cohort, row):
    """The C3 stream id of a C4 / C5 streams.json row (scan_audio.py docstring, C6 mapping): SparrKULee the stimulus name; FAU /
    DTU / Federici the C5 key; a C5 placed DTU masker '<sha>@<offset>' its placement.masker_sha."""
    if cohort == "sparrkulee":
        return str(row["name"])
    pl = row.get("placement")
    if pl:
        return str(pl["masker_sha"])
    return str(row.get("key") if row.get("key") is not None else row["name"])


def check_registry(ctx, T):
    """Every cached piece maps to its table's registry presentation by presentation_key, with the same local id, stream, ignored
    stream and lead, kind and attended side, and T_env = the attended stream's length (the views' check, run on every cohort here)."""
    for c, X in T.items():
        reg, streams = X["reg"], X["streams"]
        if [int(p["id"]) for p in reg] != list(range(len(reg))):
            raise ManifestError(f"{c}: registry presentation ids are not positions")
        keys = [str(p["key"]) for p in reg]
        if len(set(keys)) != len(keys):
            raise ManifestError(f"{c}: duplicate presentation keys")
        by = {str(p["key"]): p for p in reg}
        bad = []
        for it in X["items"]:
            if it.get("row_offset") is None:
                continue
            p = by.get(str(it.get("presentation_key")))
            if p is None:
                bad.append([it.get("piece_id"), "presentation_key not in the registry"])
                continue
            if it.get("presentation") is not None and int(it["presentation"]) != int(p["id"]):
                bad.append([it.get("piece_id"), "local presentation id differs from the registry's"])
            for f in ("stream", "ignored_stream", "kind", "attended_side"):
                if f in it and f in p and it[f] != p[f]:
                    bad.append([it.get("piece_id"), f, it[f], p[f]])
            if int(it.get("ignored_lead") or 0) != int(p.get("ignored_lead") or 0):
                bad.append([it.get("piece_id"), "ignored_lead"])
            if int(it["T_env"]) != int(streams[int(p["stream"])]["length"]):
                bad.append([it.get("piece_id"), "T_env differs from the stream length"])
        ctx.check(f"{c}: every cached piece matches its registry presentation", not bad, bad[:5])


def assign_ids(ctx, T, scan):
    """Global presentations and families (module docstring, Global ids) -> dict with pres, fams, pid {(cohort, key): id}."""
    c3f, sid_fam, c3s = {}, {}, {}
    if scan is not None:
        for c in T:
            for f in scan["doc"]["families"].get(c, []):
                if (c, f["name"]) in c3f:
                    raise ManifestError(f"C3 {c}: family name {f['name']} twice")
                c3f[(c, f["name"])] = f
                for m in f["members"]:
                    if (c, str(m["stream"])) in sid_fam:
                        raise ManifestError(f"C3 {c}: stream {m['stream']} in two families")
                    sid_fam[(c, str(m["stream"]))] = (f["name"], m.get("offset"), bool(m.get("offset_known")))
            for r in scan["doc"]["streams"].get(c, []):
                c3s[(c, str(r["stream"]))] = r
    fams, fid = [], {}
    for c in COHORTS:
        if c not in T:
            continue
        if scan is not None:
            names = sorted(n for (cc, n) in c3f if cc == c)
        else:
            names = sorted({str(p["family_name"]) for p in T[c]["reg"]})
        for n in names:
            fid[(c, n)] = len(fams)
            if scan is not None:
                f = c3f[(c, n)]
                fams.append({"id": len(fams), "cohort": c, "name": n, "clock": f["clock"], "basis": f.get("basis", "own"),
                             "root": f.get("root"), "members": [], "provisional_names": list(f.get("provisional_names", [])),
                             "streams": [{"sid": str(m["stream"]), "offset": m.get("offset"), "offset_known": bool(m.get("offset_known")),
                                          "length": m.get("length")} for m in f["members"]]})
            else:
                regs = [p for p in T[c]["reg"] if str(p["family_name"]) == n]
                unknown = any(p.get("family_offset") is None for p in regs) or any(
                    str(f.get("clock")) not in ("known",) for f in T[c]["fams"] if str(f.get("name")) == n)
                fams.append({"id": len(fams), "cohort": c, "name": n, "clock": "unknown" if unknown else "known",
                             "basis": "provisional (no C3: dry run)", "root": None, "members": [], "provisional_names": [n],
                             "streams": []})
    pres, pid, bad_len, bad_sha, bad_prov = [], {}, [], [], []
    for c in COHORTS:
        if c not in T:
            continue
        X = T[c]
        for p in sorted(X["reg"], key=lambda q: str(q["key"])):
            st = X["streams"][int(p["stream"])]
            sid = c3_sid(c, st)
            ign = p.get("ignored_stream")
            isid = None if ign is None else c3_sid(c, X["streams"][int(ign)])
            if scan is not None:
                if (c, sid) not in sid_fam:
                    raise ManifestError(f"{c} presentation {p['key']}: attended stream {sid} is in no C3 family (not keyed or not scanned)")
                fname, off, known = sid_fam[(c, sid)]
                f = c3f[(c, fname)]
                if str(p.get("family_name")) not in f.get("provisional_names", []):
                    bad_prov.append([c, p["key"], p.get("family_name"), fname])
                row = c3s.get((c, sid))
                if row is None or int(row["n"]) != int(st["length"]):
                    bad_len.append([c, sid, None if row is None else row.get("n"), st["length"]])
                elif row.get("source_sha256") and st.get("source_sha256") and row["source_sha256"] != st["source_sha256"]:
                    bad_sha.append([c, sid])
                clock = f["clock"]
            else:
                fname, off = str(p["family_name"]), p.get("family_offset")
                known = off is not None
                clock = fams[fid[(c, fname)]]["clock"]
            g = len(pres)
            rec = {"id": g, "cohort": c, "key": str(p["key"]), "stimulus": p.get("stimulus"), "family": fid[(c, fname)],
                   "family_offset": None if off is None else int(off), "offset_known": bool(known),
                   "kind": p.get("kind", "ss"), "condition": p.get("condition"), "attended_side": p.get("attended_side"),
                   "stream": int(p["stream"]), "ignored_stream": None if ign is None else int(ign),
                   "ignored_lead": int(p.get("ignored_lead") or 0), "onset_s": p.get("onset_s"), "sid": sid, "ignored_sid": isid,
                   "family_name": p.get("family_name"), "local_id": int(p["id"])}
            for k in ("noise_condition", "snr", "noise_file"):
                if k in p:
                    rec[k] = p[k]
            if clock == "known" and rec["family_offset"] is None:
                raise ManifestError(f"{c} presentation {p['key']}: a known-clock family ({fname}) without an offset")
            pres.append(rec)
            pid[(c, str(p["key"]))] = g
            fams[rec["family"]]["members"].append(g)
    if scan is not None:
        ctx.check("every presentation's provisional family name maps into its C3 family", not bad_prov, bad_prov[:5])
        ctx.check("C3 streams have the C4 / C5 stream lengths", not bad_len, bad_len[:5])
        ctx.check("C3 scanned the sources C4 / C5 cached (stream source_sha256)", not bad_sha, bad_sha[:5])
        # ignored (non-keyed) streams: every one a presentation plays must have a C3 row (the bare masker / the distractor) with
        # the same source sha and length, as the attended streams must (an exclusion keyed on it would otherwise be lost)
        miss_ign, bad_ign, seen_ign = [], [], set()
        for p in pres:
            if p["ignored_stream"] is None or (p["cohort"], p["ignored_stream"]) in seen_ign:
                continue
            c = p["cohort"]
            seen_ign.add((c, p["ignored_stream"]))
            r = T[c]["streams"][int(p["ignored_stream"])]
            row = c3s.get((c, p["ignored_sid"]))
            if row is None:
                miss_ign.append([c, p["ignored_sid"], p["key"]])
                continue
            n_c5 = int((r.get("placement") or {}).get("base_length", r["length"]))
            if int(row["n"]) != n_c5 or (row.get("source_sha256") and r.get("source_sha256") and row["source_sha256"] != r["source_sha256"]):
                bad_ign.append([c, p["ignored_sid"], row.get("n"), n_c5])
        ctx.check("every ignored stream a presentation plays (masker / distractor) has a C3 stream row", not miss_ign, miss_ign[:5])
        ctx.check("C3 scanned the ignored streams' sources (masker / distractor source_sha256 and length)", not bad_ign, bad_ign[:5])
    if len(pres) >= 1 << C.PRES_BITS or len(fams) >= 1 << C.FAMILY_BITS:
        raise ManifestError(f"{len(pres)} presentations / {len(fams)} families exceed the key bit budget")
    return {"pres": pres, "fams": fams, "pid": pid, "c3_streams": c3s}


# ---------------------------------------------------------------------------------------------------------- segments and pools
def shared_audio(ctx, T, G, scan):
    """Manifest shared_audio rows {cohort, presentation, span, stream, sid} from C3's per-stream spans (every presentation whose
    attended stream holds the span; spans in stream samples = piece samples, the attended stream starting at the piece origin)."""
    rows = []
    if scan is None:
        return rows
    by_sid = collections.defaultdict(list)
    for p in G["pres"]:
        by_sid[(p["cohort"], p["sid"])].append(p)
    unused = []
    for c in T:
        for r in scan["doc"].get("shared_audio", {}).get(c, []):
            a, b = (int(x) for x in r["span"])
            if not 0 <= a < b:
                raise ManifestError(f"C3 shared_audio {c} {r['stream']}: span {r['span']}")
            ps = by_sid.get((c, str(r["stream"])), [])
            if not ps:
                unused.append([c, r["stream"]])
            for p in ps:
                rows.append({"cohort": c, "presentation": p["id"], "span": [a, b], "stream": p["stream"], "sid": p["sid"]})
    ctx.check("C3 shared-audio spans on streams without a cached presentation (listed only)", True, unused, hard=False)
    return sorted(rows, key=lambda d: (d["presentation"], d["span"]))


def declared_pieces(ctx, T, declared):
    """{(cohort, table position): declaration} of DECLARED_EXCLUSIONS: each must match exactly one cached piece."""
    out = {}
    for dcl in declared:
        c = dcl["cohort"]
        if c not in T:
            ctx.fail(f"declared exclusion {dcl}: cohort {c} not available", missing=True)
            continue
        who = str(dcl.get("sub", dcl.get("participant")))
        hits = [i for i, it in enumerate(T[c]["items"]) if it.get("row_offset") is not None
                and str(it.get("sub", it.get("participant"))) == who and str(it.get("stimulus")) == str(dcl["stimulus"])
                and (dcl.get("run_id") is None or it.get("run_id") == dcl["run_id"])]
        if len(hits) != 1:
            raise ManifestError(f"declared exclusion {c} {who} {dcl['stimulus']}: {len(hits)} cached pieces match (exactly 1 expected)")
        out[(c, hits[0])] = dcl
    return out


def segment_tables(ctx, T, G, shared, declared, twins):
    """The manifest segment tables (fixture semantics, module docstring) -> (segments, mask counts, hc_hcv count)."""
    spans = collections.defaultdict(list)
    for d in shared:
        spans[int(d["presentation"])].append(tuple(d["span"]))
    ex = collections.defaultdict(set)
    for c, a, b in twins:
        ex[(c, str(a))].add(str(b))
        ex[(c, str(b))].add(str(a))
    seg, masked, hc_hcv = {}, collections.Counter(), 0
    for c in COHORTS:
        if c not in T:
            continue
        rows = []
        for i, it in enumerate(T[c]["items"]):
            if it.get("row_offset") is None:
                continue
            part = str(it["participant"])
            if c == "sparrkulee" and part in RESTRICTED:
                raise RestrictedAccess(f"sparrkulee piece {i}: restricted participant sub-{part} with cache rows")
            p = G["pid"][(c, str(it["presentation_key"]))]
            role = DECLARED_ROLE if (c, i) in declared else str(it["role"])
            kind = str(it.get("kind", "ss"))
            sp = spans.get(p, ())
            for s in it["segment_starts"]:
                s = int(s)
                if any(a < s + C.SPAN_EEG and s < b for a, b in sp):
                    masked[(c, role)] += 1
                    continue
                rows.append((i, part, p, s, role, kind))
        grp = collections.defaultdict(set)
        for i, part, p, s, role, kind in rows:
            grp[(p, s, role)].add(part)
        n_l = [len(grp[(r[2], r[3], r[4])]) for r in rows]
        n_p = [len(grp[(r[2], r[3], r[4])] - {r[1]} - ex.get((c, r[1]), set())) if r[4] in DONOR_ROLES else 0 for r in rows]
        tw = [(a, b) for cc, a, b in twins if cc == c]
        hc_hcv += sum(sum(str(a) in g_ and str(b) in g_ for a, b in tw) for (_, _, role), g_ in grp.items() if role in DONOR_ROLES)
        seg[c] = {k: [r[j] for r in rows] for j, k in enumerate(("piece", "participant", "presentation", "s", "role", "kind"))}
        seg[c]["family"] = [G["pres"][r[2]]["family"] for r in rows]
        seg[c]["n_listeners"], seg[c]["n_partners"] = n_l, n_p
    return seg, masked, hc_hcv


def _donor_ok(c, q):
    """A donor-eligible participant record (§3.1): donor, not test_only, DTU NH only, never the phantom, never restricted."""
    if q is None or not q.get("donor", True) or q.get("test_only"):
        return False
    if c == "dtu" and str(q.get("group")).lower() != "nh":
        return False
    if c == "federici" and (str(q.get("group")) == "Artifact" or q.get("phantom")):
        return False
    if c == "sparrkulee" and str(q.get("participant", q.get("sub"))) in RESTRICTED:
        return False
    return True


def build_pools(ctx, T, seg):
    """pools {core, csx, dev, bridge_cal} (dev / bridge_cal before the excluded-anywhere filter, applied in build_core)."""
    def pool(c, role, kind):
        S = seg[c]
        return [r for r in range(len(S["s"])) if S["role"][r] == role and S["kind"][r] == kind and S["n_partners"][r] >= 1]
    pools = {"core": {c: pool(c, "fit", "ss") for c in seg}, "csx": {}, "dev": {}, "bridge_cal": {}}
    if "fau" in seg:
        pools["csx"]["fau_cs"] = pool("fau", "fit", "cs")
    pools["dev"]["sparrkulee"] = pool("sparrkulee", "dev", "ss")
    pools["bridge_cal"]["sparrkulee"] = pool("sparrkulee", "bridge_cal", "ss")
    bad = []
    for key, d in (("core", pools["core"]), ("csx", pools["csx"]), ("dev", pools["dev"]), ("bridge_cal", pools["bridge_cal"])):
        for s, rows in d.items():
            c = coh_of(s)
            for r in rows:
                part = str(seg[c]["participant"][r])
                if c == "sparrkulee" and part in RESTRICTED:
                    raise RestrictedAccess(f"pool {key}/{s}: restricted SparrKULee participant sub-{part}")
                if not _donor_ok(c, T[c]["participants"].get(part)):
                    bad.append([key, s, part])
    ctx.check("every pool row belongs to a donor-eligible participant (donor, not test_only, DTU NH, no phantom, not restricted)",
              not bad, sorted({tuple(b) for b in bad})[:10])
    return pools


def c3_exclusions(ctx, T, G, scan):
    """C3 donor_exclusions mapped to presentations (module docstring, Donor pools) -> ({target: {donor: sorted ids}}, overlap_scan).

    A listed stream excludes every presentation of the donor cohort that plays it as its attended or ignored stream. A listed stream
    that no cached presentation plays is mapped through its C3 stream row's stimulus code (FAU: the other channel of the code's
    stereo file) to every presentation of that code (MAP_UNPLAYED_BY_CODE), else listed as unplayed; an entry that names no C3
    stream refuses the build. C3's caveats (not_scanned, assumptions) are carried into overlap_scan."""
    cc = (scan["doc"].get("cross_cohort") or {}) if scan is not None else {}
    excl_doc = cc.get("donor_exclusions") or {}
    not_scanned = {str(k): v for k, v in (cc.get("not_scanned") or {}).items()}
    c3s = G["c3_streams"]
    play = collections.defaultdict(set)                  # (cohort, C3 stream id) -> presentations playing it (attended or ignored)
    code = collections.defaultdict(set)                  # (cohort, stimulus code) -> presentations
    for p in G["pres"]:
        play[(p["cohort"], p["sid"])].add(p["id"])
        if p["ignored_sid"] is not None:
            play[(p["cohort"], p["ignored_sid"])].add(p["id"])
        code[(p["cohort"], str(p["stimulus"]))].add(p["id"])
    key = {p["id"]: p["key"] for p in G["pres"]}
    out, rec, missing, unknown, mapped, unplayed = {}, {}, [], [], [], []
    for target in TARGETS:
        out[target], rec[target] = {}, {}
        for c in DONORS[target]:
            if c not in T:
                continue
            lst = (excl_doc.get(target) or {}).get(c)
            if scan is not None and lst is None:
                missing.append([target, c])
            ids, entries = set(), []
            for sid in sorted({str(x) for x in (lst or [])}):
                direct = sorted(play.get((c, sid), ()))
                row = c3s.get((c, sid))
                ent = {"stream": sid, "kind": None if row is None else row.get("kind"), "keyed": None if row is None else row.get("keyed")}
                if direct:
                    ent.update(mapped_by="played", presentations=[key[i] for i in direct])
                    ids |= set(direct)
                elif row is None:
                    unknown.append([target, c, sid])
                    ent.update(mapped_by="unknown_stream", presentations=[])
                elif MAP_UNPLAYED_BY_CODE and row.get("code") is not None and code.get((c, str(row["code"]))):
                    via = sorted(code[(c, str(row["code"]))])
                    ent.update(mapped_by="stimulus_code", code=str(row["code"]), presentations=[key[i] for i in via])
                    ids |= set(via)
                    mapped.append({"target": target, "donor": c, "stream": sid, "code": str(row["code"]), "presentations": ent["presentations"]})
                else:
                    ent.update(mapped_by="unplayed", presentations=[])
                    unplayed.append([target, c, sid, row.get("kind")])
                entries.append(ent)
            out[target][c] = sorted(ids)
            status = "not_scanned" if target in not_scanned else ("scanned" if scan is not None else "no_scan")
            rec[target][c] = {"status": status, "n_listed": len(lst or []), "n_presentations_excluded": len(ids), "entries": entries}
            if target in not_scanned:
                rec[target][c]["not_scanned"] = not_scanned[target]
    if scan is not None:
        ctx.check("C3 donor_exclusions lists every (target, donor cohort)", not missing,
                  {"missing": missing, "listed_but_not_scanned (empty lists mean 'not scanned', not 'no overlap')": sorted(not_scanned)})
        ctx.check("every C3 donor_exclusions entry names a stream of C3's stream table", not unknown, unknown[:10])
        ctx.check("C3 donor_exclusions entries that no cached presentation plays, mapped to the presentations of their stimulus "
                  "code (MAP_UNPLAYED_BY_CODE; listed for the record)", not mapped, mapped, hard=False)
        ctx.check("C3 donor_exclusions entries that no cached piece plays and no code maps (nothing to remove; listed)", not unplayed,
                  unplayed[:20], hard=False)
        for t in sorted(not_scanned):
            ctx.check(f"overlap of the {t} target's test stimuli with the donors is verified", False,
                      {"c3_not_scanned": not_scanned[t], "status": "unverified assumption (C3 assumptions)"}, hard=False)
    scan_rec = {"rule": cc.get("donor_exclusion_rule") if scan is not None else "C3 not available (dry run): no exclusion",
                "map_unplayed_by_code": MAP_UNPLAYED_BY_CODE,
                "mapping_rule": "a listed stream excludes every presentation of the donor cohort that plays it (attended or ignored "
                                "stream); one that no cached presentation plays is mapped through its C3 row's stimulus code to every "
                                "presentation of that code (FAU: the other channel of the code's stereo file, which the code's "
                                "listeners may have heard: the reading C3 applies when FAU is the target), else listed as unplayed "
                                "(nothing cached plays it); an entry naming no C3 stream refuses the build",
                "targets": rec, "not_scanned": not_scanned,
                "assumptions": [] if scan is None else list(scan["doc"].get("assumptions") or [])}
    return out, scan_rec


def identity_overlap(scan):
    """§3.4.5: identity overlap across cohorts is implausible and cannot be verified; records say so (C3's assumption when present)."""
    hit = [a for a in ((scan or {}).get("doc", {}).get("assumptions") or []) if "identity" in str(a.get("item", "")).lower()]
    if hit:
        return {**hit[0], "source": "C3 scan_audio.json assumptions", "design": "§3.4.5"}
    return {"item": "identity overlap across cohorts", "status": "unverifiable", "source": "design §3.4.5",
            "detail": "different sites, countries and ages, no shared identifiers; not checked"}


def donor_sets(ctx, T, G, seg, pools, scan, c3x=None):
    """donor_sets[target][core | rich | csx] (module docstring, Donor pools); c3x = c3_exclusions(...)[0]."""
    if c3x is None:
        c3x = c3_exclusions(ctx, T, G, scan)[0]
    out = {}
    for target in TARGETS:
        donors = [c for c in DONORS[target] if c in seg]
        excl = {c: list(c3x.get(target, {}).get(c, [])) for c in donors}
        blocks = {"core": list(donors), "rich": list(donors)}
        if target != "fau" and "fau" in donors and "fau_cs" in pools["csx"]:
            blocks["csx"] = list(donors) + ["fau_cs"]
        out[target] = {}
        for b, strata in blocks.items():
            ex = {s: list(excl[coh_of(s)]) for s in strata}
            n = []
            for s in strata:
                rows = pools["csx"]["fau_cs"] if s == "fau_cs" else pools["core"][s]
                S, e = seg[coh_of(s)], set(ex[s])
                n.append(int(sum(S["presentation"][r] not in e for r in rows)))
            tot = sum(n)
            out[target][b] = {"strata": list(strata), "weights": [v / tot if tot else 0.0 for v in n], "n_segments": n,
                              "excluded_presentations": ex}
    small = []
    for target, blocks in out.items():
        for b, ds in blocks.items():
            for s, n in zip(ds["strata"], ds["n_segments"]):
                rows = pools["csx"]["fau_cs"] if s == "fau_cs" else pools["core"][s]
                S, e = seg[coh_of(s)], set(ds["excluded_presentations"][s])
                n_u = len({(S["presentation"][r], S["s"][r]) for r in rows if S["presentation"][r] not in e})
                if n_u < BATCH_SEGMENTS or n <= 0:
                    small.append([target, b, s, n_u])
    ctx.check(f"every stratum of every donor set holds >= {BATCH_SEGMENTS} distinct (presentation, s) (a §2.6 design batch)",
              not small, small)
    return out


def excluded_anywhere(dsets, cohort="sparrkulee"):
    out = collections.defaultdict(set)
    for t, blocks in dsets.items():
        for b, ds in blocks.items():
            for s, ps in ds["excluded_presentations"].items():
                if coh_of(s) == cohort:
                    for p in ps:
                        out[int(p)].add(f"{t}/{b}")
    return {p: sorted(v) for p, v in sorted(out.items())}


# ---------------------------------------------------------------------------------------------------------- standardiser, P
def standardiser(ctx, T, G, seg, rows, left_out=()):
    """σ (RMS about 0), μ ≡ 0, μ estimate over the unique (presentation, tick) windows of `rows` (SparrKULee core pool without
    the presentations `left_out`, which some donor set excludes)."""
    S, X = seg["sparrkulee"], T["sparrkulee"]
    u = sorted({(int(S["presentation"][r]), int(S["s"][r])) for r in rows})
    if not u:
        ctx.fail("standardiser: no SparrKULee core-pool window")
        return None, []
    env = X["env"]
    offs = C.TICK_OFFS.astype(np.int64)[:, None] + np.arange(C.N_TGT, dtype=np.int64)[None]
    s1, s2, n = np.zeros(C.N_TGT), np.zeros(C.N_TGT), 0
    for a in range(0, len(u), 256):
        chunk = u[a:a + 256]
        base = np.asarray([int(X["streams"][G["pres"][p]["stream"]]["offset"]) + s for p, s in chunk], dtype=np.int64)
        for (p, s), b0 in zip(chunk, base):
            L = int(X["streams"][G["pres"][p]["stream"]]["length"])
            if s + int(offs.max()) + 1 > L - C.ENV_EDGE or s + int(offs.min()) < C.ENV_EDGE:
                raise ManifestError(f"standardiser: presentation {p} segment {s} touches the stream edges")
        Y = env[base[:, None, None] + offs[None]].astype(np.float64).reshape(-1, C.N_TGT)
        s1 += Y.sum(0)
        s2 += (Y ** 2).sum(0)
        n += len(Y)
    sigma, mu = np.sqrt(s2 / n), s1 / n
    ratio = float(np.abs(mu / sigma).max())
    ctx.check(f"standardiser |mu| / sigma < {MU_RATIO_MAX} (§2.3 engineering check of the 2-8 Hz band-pass)", ratio < MU_RATIO_MAX,
              ratio)
    return {"sigma": sigma.tolist(), "mu": [0.0] * C.N_TGT, "mu_estimate": mu.tolist(), "abs_mu_over_sigma_max": ratio,
            "n_windows": int(n), "n_content_segments": len(u),
            "left_out_presentations": sorted(G["pres"][int(p)]["key"] for p in left_out),
            "rule": "sigma[d] = sqrt(mean y[d]^2) (RMS about 0) over the unique (presentation, tick) windows of pools.core.sparrkulee "
                    "without any presentation a donor set excludes; each window once whatever its listener count; mu fixed at 0 "
                    "(stored as zeros), the sample mean recorded as mu_estimate"}, u


def projection(ctx):
    """P = semi_orthogonal(32, 8, 20261016) float32, stored once at the root; sha256 of its bytes must start with P_SHA16 ->
    (record, the .npy bytes to write when the root has no P yet, else None)."""
    path = os.path.join(ctx.root, C.P_FILE)
    fresh = semi_orthogonal(C.P_SHAPE[0], C.P_SHAPE[1], C.PROJ_SEED)
    if os.path.exists(path):
        P, _ = ctx.read_npy(path)
        kept = True
        if P.dtype != np.float32 or P.shape != C.P_SHAPE:
            raise ManifestError(f"{path}: float32 {C.P_SHAPE} expected, got {P.dtype} {P.shape} (never regenerated: move it away)")
    else:
        P, kept = fresh, False
    sha = _sha(np.ascontiguousarray(P).tobytes())
    eye = float(np.abs(P.astype(np.float64) @ P.astype(np.float64).T - np.eye(C.P_SHAPE[0])).max()) if P.shape[0] <= P.shape[1] \
        else float(np.abs(P.astype(np.float64).T @ P.astype(np.float64) - np.eye(C.P_SHAPE[1])).max())
    ok = sha.startswith(C.P_SHA16) and np.linalg.matrix_rank(P.astype(np.float64)) == min(C.P_SHAPE) and eye < 1e-6
    ctx.check(f"P is the contract projection (sha256 prefix {C.P_SHA16}, orthonormal, rank 8)", ok,
              {"sha256": sha, "orthonormality_error": eye, "kept_existing": kept})
    raw = None
    if not kept:
        buf = io.BytesIO()
        np.save(buf, P, allow_pickle=False)
        raw = buf.getvalue()
        ctx.files[C.P_FILE] = {"sha256": _sha(raw), "bytes": len(raw)}
    return {"file": C.P_FILE, "sha256": sha, "seed": C.PROJ_SEED, "shape": list(C.P_SHAPE),
            "generator": "numpy QR of default_rng(20261016).standard_normal((32, 8)), float32 "
                         "(= auditory_alignment_v2.audio_targets.semi_orthogonal(32, 8, 20261016))",
            "equals_fresh_generation": bool(np.array_equal(P, fresh)), "kept_existing": kept}, raw


# ---------------------------------------------------------------------------------------------------------- fixed sets
def _balanced(rows, part_of, n, rng):
    """n rows participant-balanced (water-filling over the participants in sorted order, the remainder to participants drawn by
    rng), uniform without replacement within a participant; all rows when there are at most n."""
    rows = sorted(int(r) for r in rows)
    if len(rows) <= n:
        return rows
    by = collections.defaultdict(list)
    for r in rows:
        by[str(part_of[r])].append(r)
    ps = sorted(by)
    quota, left = {p: 0 for p in ps}, n
    while left > 0:
        avail = [p for p in ps if quota[p] < len(by[p])]
        share, rem = divmod(left, len(avail))
        if share == 0:
            for i in rng.permutation(len(avail))[:rem]:
                quota[avail[int(i)]] += 1
            left = 0
            break
        for p in avail:
            add = min(share, len(by[p]) - quota[p])
            quota[p] += add
            left -= add
    out = []
    for p in ps:
        out += by[p] if quota[p] == len(by[p]) else [int(x) for x in rng.choice(by[p], quota[p], replace=False)]
    return sorted(out)


def fixed_sets(ctx, seg, pools, dsets):
    """selection {fit_segments, dev_queries} and bridge {fit_rows, cal_queries, cal_split} (module docstring, Interpretations)."""
    S = seg["sparrkulee"]
    bad = excluded_anywhere(dsets, "sparrkulee")
    keep = lambda rows: [r for r in rows if int(S["presentation"][r]) not in bad]    # noqa: E731
    fit_pool = keep(pools["core"]["sparrkulee"])
    r_fit = _rng(DRAW_TAGS["fit_segments"])
    fit = sorted(int(x) for x in (fit_pool if len(fit_pool) <= N_FIT else r_fit.choice(fit_pool, N_FIT, replace=False)))
    dev = _balanced(pools["dev"]["sparrkulee"], S["participant"], N_DEV, _rng(DRAW_TAGS["dev_queries"]))
    cal = _balanced(pools["bridge_cal"]["sparrkulee"], S["participant"], N_CAL, _rng(DRAW_TAGS["cal_queries"]))
    qp = sorted({str(S["participant"][r]) for r in cal})
    perm = _rng(DRAW_TAGS["cal_split"]).permutation(len(qp))
    h = len(qp) // 2
    split = [sorted(qp[int(i)] for i in perm[:h]), sorted(qp[int(i)] for i in perm[h:])]
    fit_rows, replaced = {}, {}
    for k, target in enumerate(TARGETS):
        if target not in dsets:
            continue
        core = dsets[target]["core"]
        strata, w = core["strata"], np.asarray(core["weights"], dtype=np.float64)
        if not strata or w.sum() <= 0:
            continue
        rng = _rng(DRAW_TAGS["bridge_fit"], k)
        elig = {s: [r for r in pools["core"][s] if seg[s]["presentation"][r] not in set(core["excluded_presentations"][s])]
                for s in strata}
        picks = rng.choice(len(strata), N_BRIDGE, p=w / w.sum())
        cnt = np.bincount(picks, minlength=len(strata))
        drawn = {}
        for j, s in enumerate(strata):
            rep = int(cnt[j]) > len(elig[s])
            if rep:
                replaced.setdefault(target, []).append(s)
            drawn[s] = iter([int(x) for x in rng.choice(elig[s], int(cnt[j]), replace=rep)]) if cnt[j] else iter(())
        fit_rows[target] = [[strata[int(j)], next(drawn[strata[int(j)]])] for j in picks]
    ctx.check("bridge fit rows drawn without replacement within every stratum", not replaced, replaced, hard=False)
    sel = {"fit_segments": fit, "dev_queries": dev,
           "rules": {"fit_segments": f"{N_FIT} rows of pools.core.sparrkulee (uniform without replacement; all rows when fewer), "
                                     f"SeedSequence([{C.BRIDGE_SEED}, {DRAW_TAGS['fit_segments']:#x}])",
                     "dev_queries": f"{N_DEV} rows of pools.dev.sparrkulee, participant-balanced (all rows when fewer), "
                                    f"SeedSequence([{C.BRIDGE_SEED}, {DRAW_TAGS['dev_queries']:#x}])",
                     "candidates": "the unique (presentation, s) of the dev queries (sampler.selection_sets)",
                     "excluded_presentations": "every fixed set and the dev / bridge_cal pools avoid every presentation a donor set "
                                               "excludes (sampler.selection_sets fails closed)"}}
    bridge = {"fit_rows": fit_rows, "cal_queries": cal, "cal_split": split,
              "rules": {"fit_rows": f"{N_BRIDGE} rows per target of its core donor set: strata drawn with the stratum weights, rows "
                                    "uniform without replacement within a stratum, in draw order; "
                                    f"SeedSequence([{C.BRIDGE_SEED}, {DRAW_TAGS['bridge_fit']:#x}, target index in {list(TARGETS)}])",
                        "cal_queries": f"{N_CAL} rows of pools.bridge_cal.sparrkulee, participant-balanced (all rows when fewer), "
                                       f"SeedSequence([{C.BRIDGE_SEED}, {DRAW_TAGS['cal_queries']:#x}])",
                        "cal_split": "the bridge_cal query participants (sorted), permuted by "
                                     f"SeedSequence([{C.BRIDGE_SEED}, {DRAW_TAGS['cal_split']:#x}]); first half / second half",
                        "with_replacement": replaced}}
    return sel, bridge


# ---------------------------------------------------------------------------------------------------------- cells
def _fau_cf():
    from auditory_alignment.data import FAU_CF
    return FAU_CF


def _content(c, items, cf):
    """The content split of one cohort and content fold from its C5 pieces (module docstring, Cells) -> (content, extra)."""
    if c == "fau":
        fcf = _fau_cf()[cf]
        content = {}
        for k in ("ss", "cs"):
            content[k] = {r: [] for r in ("fit", "es", "test")}
            for code in sorted({str(it["stimulus"]) for it in items if it.get("kind") == k}):
                roles = [r for r, digits in fcf[k].items() if code[2] in digits]
                if len(roles) != 1:
                    raise ManifestError(f"fau code {code}: content roles {roles} in FAU_CF[{cf}][{k}]")
                content[k][roles[0]].append(code)
        return content, {}
    role_of, groups = {}, {}
    for it in items:
        st = str(it["stimulus"])
        r = ("test" if int(it["content_half"]) == cf else ("es" if bool(it["content_early_stop"]) else "fit")) if c == "dtu" \
            else str(it["content_role"])
        if role_of.setdefault(st, r) != r:
            raise ManifestError(f"{c} stimulus {st}: content roles {role_of[st]} and {r}")
        g = it.get("content_group")
        if groups.setdefault(st, g) != g:
            raise ManifestError(f"{c} stimulus {st}: content groups {groups[st]} and {g}")
    if set(role_of.values()) - {"fit", "es", "test"}:
        raise ManifestError(f"{c}: content roles {sorted(set(role_of.values()))}")
    return ({r: sorted(s for s, x in role_of.items() if x == r) for r in ("fit", "es", "test")},
            {"content_groups": {s: groups[s] for s in sorted(groups)}})


def public_cells(ctx, T):
    """The 25 public cells from the C5 tables (module docstring, Cells), ordered as the fixture: subject fold, then content fold."""
    out = []
    for c, n_sf, cfs in CELLS[:3]:
        if c not in T:
            ctx.fail(f"cells: {c} not available", missing=True)
            continue
        parts, items = T[c]["table"]["participants"], T[c]["items"]
        split = {cf: _content(c, items, cf) for cf in cfs}
        for sf in range(n_sf):
            for cf in cfs:
                content, extra = split[cf]
                train = sorted(str(p["participant"]) for p in parts if not p.get("test_only") and (p.get("dev") or int(p["fold"]) != sf))
                test = sorted(str(p["participant"]) for p in parts if not p.get("dev") and not p.get("test_only") and int(p["fold"]) == sf)
                cell = {"dataset": c, "subject_fold": sf, "content_fold": cf,
                        "always_train": sorted(str(p["participant"]) for p in parts if p.get("dev")),
                        "test_only": sorted(str(p["participant"]) for p in parts if p.get("test_only")),
                        "train": train, "test": test, "content": copy.deepcopy(content), **copy.deepcopy(extra),
                        "rules": CELL_RULES[c], "seeds": dict(SEEDS)}
                if not test:
                    raise ManifestError(f"cell {c} sf{sf} cf{cf}: no test participant")
                cell["split_hash"] = split_hash(cell)
                cell.update(n_train=len(train), n_test=len(test), n_test_only=len(cell["test_only"]))
                out.append(cell)
    return out


def aln3_records(ctx, plan=ALN3_PLAN, units=UNITS_DIR, seed=C.BREADTH_SEED):
    """{(dataset, sf, cf): [{eid, file_sha256, test: sorted keys, groups {key: group}, n_train}]} of the completed ALN3 A_LOCAL
    (public) and E_LOCAL (private) records of `seed`; only eval.per_participant keys / groups and the train counts are kept."""
    if plan is None and ctx.mode == "local":
        ctx.notes.append("ALN3 records not checked (synthetic tree without an ALN3 plan)")
        return None, None
    if plan is None or not os.path.exists(plan) or units is None or not os.path.isdir(units):
        ctx.fail(f"ALN3 plan {plan} / units {units} not available: the cells cannot be checked against the ALN3 records", missing=True)
        return None, None
    raw = ctx.read_bytes(plan, describe=False)
    out, n_rows, shas = collections.defaultdict(list), 0, []
    for line in raw.decode().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("family_id") not in ("A_LOCAL", "E_LOCAL") or int(r.get("seed", -1)) != int(seed):
            continue
        n_rows += 1
        p = os.path.join(units, f"{r['experiment_id']}.json")
        if not os.path.exists(p):
            continue
        rb = ctx.read_bytes(p, describe=False)
        d = json.loads(rb)
        if d.get("status") != "complete":
            continue
        pp = (d.get("eval") or {}).get("per_participant") or {}
        n_train = d.get("n_train_children") if r["dataset"] == PRIVATE else d.get("n_train_participants")
        out[(r["dataset"], int(r["subject_fold"]), int(r.get("content_fold") or 0))].append(
            {"eid": r["experiment_id"], "family": r["family_id"], "test": sorted(map(str, pp)), "n_train": n_train,
             "groups": {str(k): (v or {}).get("group") for k, v in pp.items()}})
        shas.append([r["experiment_id"], _sha(rb)])
        del d
    rec = {"plan": os.path.relpath(plan, REPO) if _inside(plan, REPO) else plan, "plan_sha256": _sha(raw), "seed": int(seed),
           "n_plan_rows": n_rows, "n_complete_records": len(shas), "records_sha256": _sha(json.dumps(sorted(shas)).encode()),
           "read": "eval.per_participant keys and groups, n_train_participants / n_train_children only"}
    return dict(out), rec


def check_cells(ctx, cells, recs):
    """Every public cell agrees with every completed A_LOCAL record of its (dataset, sf, cf) -> per-cell summary (no ids)."""
    rows = []
    for cell in cells:
        if cell["dataset"] == PRIVATE:
            continue
        key = (cell["dataset"], int(cell["subject_fold"]), int(cell["content_fold"]))
        rs = (recs or {}).get(key, [])
        want = sorted(set(cell["test"]) | set(cell["test_only"]))
        agree = [r for r in rs if r["test"] == want and r["n_train"] == len(cell["train"])]
        rows.append({"dataset": key[0], "subject_fold": key[1], "content_fold": key[2], "n_records": len(rs),
                     "n_agree": len(agree), "split_hash": cell["split_hash"]})
    if recs is not None:
        bad = [r for r in rows if r["n_records"] == 0 or r["n_agree"] != r["n_records"]]
        ctx.check("every public cell equals every completed ALN3 A_LOCAL record of its cell (test + test_only, |train|)", not bad, bad)
    return rows


def private_cells(ctx, recs, kids=None):
    """The 5 private_bdf cells (with ids; module docstring, Cells): from the E_LOCAL records, or from `kids` [{id, group, fold}]
    (synthetic trees). Returns (cells, summary rows)."""
    folds, groups, summary = {}, {}, []
    if kids is not None:
        for k in kids:
            folds.setdefault(int(k["fold"]), set()).add(str(k["id"]))
            groups[str(k["id"])] = k.get("group")
        n_train = {sf: None for sf in folds}
        src = "children given to the builder (synthetic)"
    elif recs is not None:
        n_train = {}
        for sf in range(CELLS[3][1]):
            rs = recs.get((PRIVATE, sf, 0), [])
            if not rs:
                ctx.fail(f"private_bdf sf{sf}: no completed ALN3 E_LOCAL record", missing=True)
                return [], summary
            tests = {tuple(r["test"]) for r in rs}
            nts = {r["n_train"] for r in rs}
            ctx.check(f"private_bdf sf{sf}: every E_LOCAL record of the fold has the same children", len(tests) == 1 and len(nts) == 1,
                      {"n_records": len(rs), "n_distinct_test_sets": len(tests), "n_train": sorted(map(str, nts))})
            folds[sf] = set(rs[0]["test"])
            n_train[sf] = rs[0]["n_train"]
            for r in rs:
                groups.update(r["groups"])
            summary.append({"subject_fold": sf, "n_records": len(rs)})
        src = "ALN3 E_LOCAL records (seed 3401)"
    else:
        return [], summary
    every = set().union(*folds.values()) if folds else set()
    if sum(len(v) for v in folds.values()) != len(every):
        raise ManifestError("private_bdf: a child is a test child of two folds")
    out = []
    for sf in range(CELLS[3][1]):
        test = sorted(folds.get(sf, ()))
        train = sorted(every - set(test))
        if not test or (n_train.get(sf) is not None and int(n_train[sf]) != len(train)):
            raise ManifestError(f"private_bdf sf{sf}: {len(test)} test children, {len(train)} train vs the record's {n_train.get(sf)}")
        cell = {"dataset": PRIVATE, "subject_fold": sf, "content_fold": 0, "always_train": [], "test_only": [], "train": train,
                "test": test, "content": dict(PRIVATE_CONTENT), "rules": CELL_RULES[PRIVATE], "seeds": dict(SEEDS)}
        cell["split_hash"] = split_hash(cell)
        cell.update(n_train=len(train), n_test=len(test), n_test_only=0,
                    n_test_by_group=dict(sorted(collections.Counter(str(groups.get(k)) for k in test).items())), binding_source=src)
        out.append(cell)
    return out, summary


# ---------------------------------------------------------------------------------------------------------- mode C
def _mode_c_donor(p):
    """The participants build_public.mode_c_scales reads (donor true, role 'fit' when given)."""
    return bool(p.get("donor")) and p.get("role", "fit") == "fit"


def band_sd_by_participant(table, cohort_dir, log=print):
    """build_public.with_band_sd(table, cohort_dir) for the participants mode_c_scales reads, one participant per call: each call
    maps the z-cache, touches that participant's rows only and unmaps it on return, so resident memory stays one participant's
    pieces (in float64) instead of the whole mapped cache. Every value equals the one-call result for those participants (each
    participant's statistic depends on its own pieces only); the other participants are left as given (mode_c_scales skips them).
    Restricted SparrKULee participants never have cache rows (refused here too). -> {"participants", "cohort_info"}."""
    from auditory_alignment_v3.prior33 import build_public as BP
    ik = "pieces" if "pieces" in table else "runs"
    by = collections.defaultdict(list)
    for q in table[ik]:
        if q.get("row_offset") is not None:
            by[str(q["participant"])].append(q)
    base = {k: v for k, v in table.items() if k not in ("participants", ik)}
    ci = BP.with_band_sd({**base, "participants": [], ik: []}, cohort_dir)["cohort_info"]     # stats_band only (no row is read)
    parts, n = [], 0
    for p in table["participants"]:
        pid = str(p["participant"])
        if not _mode_c_donor(p) or not by.get(pid):
            parts.append(p)
            continue
        if (table.get("cohort") == "sparrkulee" or "runs" in table) and pid in RESTRICTED:
            raise RestrictedAccess(f"band_sd_by_participant: restricted SparrKULee participant sub-{pid} with cache rows")
        d = BP.with_band_sd({**base, "participants": [p], ik: by[pid]}, cohort_dir)
        parts.append(d["participants"][0])
        n += 1
    log(f"mode C: 2-8 Hz pre-z SD derived for {n} participants (one with_band_sd call each)")
    return {"participants": parts, "cohort_info": ci, "n_derived": n}


def mode_c(ctx, T):
    """mode_c {cohort: record} (module docstring, Mode C)."""
    from auditory_alignment_v3.prior33 import build_public as BP
    out = {"sparrkulee": {"supported": False, "reason": "donor only (never a target)"}}
    units = {c: (X["info"].get("unit") or {}).get("factor_to_uV") for c, X in T.items()}
    tables = {c: {"layout": list(X["info"]["layout"]), "participants": X["table"]["participants"], "cohort_info": X["info"],
                  "cohort": c} for c, X in T.items()}
    sk_2_8 = None
    for target in PUBLIC:
        mode = MODE_C[target]
        rec = {"supported": False, "mode": mode}
        if target not in T:
            out[target] = {**rec, "reason": "C5 table not available (dry run)"}
            continue
        own, why = T[target]["table"].get("mode_c") or {}, []
        if not own.get("supported"):
            why.append(f"C5: mode {mode} unsupported ({own.get('reason')})")
        if not own.get("built") or mode not in T[target]["caches"]:
            why.append(f"C5: no mode-{mode} cache with a done record")
        miss = [c for c in DONORS[target] if c not in T]
        if miss:
            why.append(f"donor tables missing: {miss}")
        sc = None
        if not why:
            tabs = dict(tables)
            if tuple(BP.TARGET_BAND[target]) == (2.0, 8.0) and not (T["sparrkulee"]["info"].get("stats_band") or {}).get("A_2_8"):
                if sk_2_8 is None:
                    ctx.log("mode C: deriving the SparrKULee 2-8 Hz pre-z SD from the z-cache (build_public.with_band_sd, one "
                            "donor-fit participant per call)")
                    sk_2_8 = band_sd_by_participant(T["sparrkulee"]["table"], ctx.path("sparrkulee"), ctx.log)
                tabs["sparrkulee"] = {"layout": list(sk_2_8["cohort_info"]["layout"]), "participants": sk_2_8["participants"],
                                      "cohort_info": sk_2_8["cohort_info"], "cohort": "sparrkulee"}
            sc = BP.mode_c_scales(target, tabs, units, donors=DONORS[target], band="target")
            if not sc.get("supported"):
                why.append(sc.get("reason"))
        if why:
            out[target] = {**rec, "reason": "; ".join(str(w) for w in why)}
            continue
        sc = {k: v for k, v in sc.items() if k != "supported"}
        out[target] = {**rec, "supported": True, "unit": "uV", "basis": (T[target]["info"].get("unit") or {}).get("basis"),
                       "cache": T[target]["caches"][mode], "cache_sha256": T[target]["cache_sha"][mode],
                       "sparrkulee_2_8_derived": sk_2_8 is not None and target == "federici", **sc}
        bad = [n for n in C.MONTAGES[target] if not (math.isfinite(out[target]["scale"][n]) and out[target]["scale"][n] > 0)]
        ctx.check(f"mode {mode} scale of {target} finite and positive on every channel", not bad, bad)
    return out


# ---------------------------------------------------------------------------------------------------------- reports
def _stem(path):
    b = os.path.basename(str(path))
    return b[:-3] if b.endswith(".h5") else b


def dtu_not_loaded(ctx, T):
    """Every DTU inventory trial absent from the C5 cache, with its reason (module docstring, Declared exclusions): C5
    checks.inventory_reconciliation.not_loaded, status 'excluded' (reason per trial, cross-checked with excluded_trials) or
    'unread_file' (reason per file, from unread_files, whose inventory trial count must match); any other status refuses."""
    if "dtu" not in T:
        return []
    t = T["dtu"]["table"]
    rc = (t.get("checks") or {}).get("inventory_reconciliation")
    if rc is None:
        ctx.fail("C5 dtu pieces.json: no checks.inventory_reconciliation (the DTU trial reconciliation of §3.5 cannot be declared)")
        return []
    unread = {_stem(u.get("file")): u for u in t.get("unread_files", [])}
    excl = {(str(e.get("participant")), str(e.get("trial"))): e for e in t.get("excluded_trials", [])}
    rows, bad, seen_ex, n_unread = [], [], set(), collections.Counter()
    for r in rc.get("not_loaded", []):
        f, tr, st = str(r.get("file")), str(r.get("trial")), r.get("status")
        if st == "excluded":
            e = excl.get((f, tr))
            if e is None:
                bad.append([f, tr, st, "not in excluded_trials"])
                continue
            seen_ex.add((f, tr))
            reason, source = r.get("reason") or e.get("reason"), "excluded_trials (load_dtu's trial filter)"
        elif st == "unread_file":
            u = unread.get(f)
            if u is None:
                bad.append([f, tr, st, "file not in unread_files"])
                continue
            n_unread[f] += 1
            reason, source = u.get("reason"), "unread_files (a file load_dtu never opens)"
        else:
            bad.append([f, tr, st, "status neither 'excluded' nor 'unread_file'"])
            continue
        if not reason:
            bad.append([f, tr, st, "no reason"])
        rows.append({"file": f, "trial": tr, "subject": r.get("subject"), "hearing": r.get("hearing"), "kind": r.get("kind"),
                     "target_sha": r.get("target_sha"), "status": st, "reason": reason, "source": source})
    bad += [[f, tr, "excluded_trials entry", "not in not_loaded"] for (f, tr) in sorted(set(excl) - seen_ex)]
    bad += [[f, "unread file", u.get("n_inventory_trials"), n_unread.get(f, 0)] for f, u in sorted(unread.items())
            if u.get("n_inventory_trials") is not None and int(u["n_inventory_trials"]) != n_unread.get(f, 0)]
    ctx.check("DTU: every inventory trial absent from the C5 cache is declared with its reason (inventory_reconciliation.not_loaded "
              "= excluded_trials + the trials of unread_files)", not bad, bad[:10])
    return rows


def exclusions(ctx, T, declared, dtu_rows=(), anywhere=None, G=None, seg=None):
    """The declared exclusion list (module docstring, Declared exclusions) and its summary."""
    X = T["sparrkulee"]
    out = []
    for r in X["items"]:
        a = X["audit"][r["run_id"]]
        base = {"cohort": "sparrkulee", "run_id": r["run_id"], "sub": str(r["sub"]), "stimulus": r.get("stimulus"), "declared": True}
        if r.get("role") == "restricted":
            out.append({**base, "rule": "restricted_participant", "detail": "never opened: listed from file names and .npy headers (C1)"})
        for fl in r.get("flags") or []:
            out.append({**base, "rule": fl, "role": r.get("role"),
                        "detail": {"c2_class": a.get("class"), "tau": a.get("tau"), "z": a.get("z"), "n_refs": a.get("n_refs"),
                                   "structural": r.get("structural")}})
    declared_runs = set()
    for (c, i), dcl in sorted(declared.items()):
        it = T[c]["items"][i]
        a = X["audit"].get(it.get("run_id"), {}) if c == "sparrkulee" else {}
        if c == "sparrkulee":
            declared_runs.add(it.get("run_id"))
        d = {"reason": dcl["reason"], "c2_class": a.get("class"), "tau": a.get("tau"), "z": a.get("z"),
             "c2_diagnostic": a.get("diagnostic"), "role_in_manifest": DECLARED_ROLE}
        for k in ("required_by", "basis", "conflicts", "expect_c2"):
            if k in dcl:
                d[k] = copy.deepcopy(dcl[k])
        if G is not None and seg is not None and c in seg:
            S = seg[c]
            rows = [r for r in range(len(S["s"])) if S["piece"][r] == i]
            p = G["pid"][(c, str(it["presentation_key"]))]
            d["n_segments"] = len(rows)
            d["presentation_excluded_for"] = (anywhere or {}).get(p, []) if c == "sparrkulee" else None
        out.append({"cohort": c, "run_id": it.get("run_id", it.get("piece_id")), "sub": str(it.get("sub", it.get("participant"))),
                    "stimulus": it.get("stimulus"), "declared": True, "rule": dcl["rule"], "role": it.get("role"), "detail": d})
    for sub, ses, run in README_FLAGGED:
        out.append({"cohort": "sparrkulee", "run_id": f"sub-{sub}_ses-{ses}_run-{run}", "sub": sub, "stimulus": None, "declared": True,
                    "rule": "readme_flagged", "detail": "absent from the re-host (C1 readme_flagged_absent; no runs.json row)"})
    for e in dtu_rows:
        out.append({"cohort": "dtu", "run_id": f"{e['file']}:{e['trial']}", "sub": e.get("subject"), "stimulus": e.get("target_sha"),
                    "declared": True, "rule": "aln3_loader_filter",
                    "detail": {k: e.get(k) for k in ("file", "trial", "hearing", "kind", "status", "reason", "source")}})
    classes = collections.Counter(a.get("class") for a in X["audit"].values())
    unv = [r for r in X["items"] if X["audit"][r["run_id"]].get("class") == "unverifiable"]
    kept = [r for r in unv if r.get("role") in DONOR_ROLES and r["run_id"] not in declared_runs and not r.get("flags")]
    summary = {"c2_classes": dict(sorted(classes.items())),
               "unverifiable_kept": len(kept),
               "unverifiable_by_role": dict(sorted(collections.Counter(str(r.get("role")) for r in unv).items())),
               "unverifiable_declared_excluded": sorted(r["run_id"] for r in unv if r["run_id"] in declared_runs),
               "rule": "C2 'unverifiable' runs are never excluded for their class (F11: never excluded for weak tracking). "
                       "unverifiable_kept counts the unverifiable runs in a donor role (fit / dev / bridge_cal) that no listed "
                       "exclusion removes; unverifiable_by_role gives the C4 role of every unverifiable run (holdout_seen_content and "
                       "control_artefact runs enter no pool by their role, excluded_rule ones by C1's structural rule); "
                       "unverifiable_declared_excluded lists those a declared structural exclusion removes",
               "n_by_rule": dict(sorted(collections.Counter(e["rule"] for e in out).items()))}
    return out, summary


def _r2(v):
    return None if v is None else [None if x is None else round(float(x), 2) for x in v]


def c2_numbers(a):
    """The C2 numbers a declaration may quote: class, tau-hat and z per half (z to 2 decimals) and C2's descriptive diagnostic."""
    dg = a.get("diagnostic") or {}
    full, halves = dg.get("full") or {}, dg.get("halves") or []
    return {"class": a.get("class"), "tau": None if a.get("tau") is None else [int(x) for x in a["tau"]], "z_2dp": _r2(a.get("z")),
            "diagnostic": {"full_tau": full.get("tau"), "full_z_2dp": None if full.get("z") is None else round(float(full["z"]), 2),
                           "halves_tau": [h.get("tau") for h in halves], "halves_z_2dp": _r2([h.get("z") for h in halves])}}


def _expected_c2(want):
    out = {"class": want.get("class"), "tau": None if want.get("tau") is None else [int(x) for x in want["tau"]],
           "z_2dp": _r2(want.get("z_2dp"))}
    if "diagnostic" in want:
        w = want["diagnostic"]
        out["diagnostic"] = {"full_tau": w.get("full_tau"), "full_z_2dp": None if w.get("full_z_2dp") is None else round(float(w["full_z_2dp"]), 2),
                             "halves_tau": list(w.get("halves_tau") or []), "halves_z_2dp": _r2(w.get("halves_z_2dp") or [])}
    return out


def check_declared_basis(ctx, T, declared):
    """Each declaration's cited files (sha256; required in production) and the C2 numbers its reason quotes (hard checks)."""
    X = T["sparrkulee"]
    for (c, i), dcl in sorted(declared.items()):
        it = T[c]["items"][i]
        name = f"declared exclusion {c} {it.get('sub', it.get('participant'))} {it.get('stimulus')}"
        for b in dcl.get("basis", ()):
            p = os.path.join(REPO, b["file"])
            if not os.path.exists(p):
                if ctx.mode == "production":
                    ctx.check(f"{name}: the file its reason cites exists ({b['file']})", False, b["file"])
                else:
                    ctx.notes.append(f"{name}: {b['file']} not available here (checked in production)")
                continue
            got = sha256_file(p)[0]
            ctx.check(f"{name}: the file its reason cites has the cited sha256 ({os.path.basename(b['file'])})", got == b["sha256"],
                      {"file": b["file"], "sha256": got, "cited": b["sha256"]})
        want = dcl.get("expect_c2")
        if want is None or c != "sparrkulee":
            continue
        exp = _expected_c2(want)
        got = c2_numbers(X["audit"].get(it.get("run_id"), {}))
        got = {k: got[k] for k in exp}
        ctx.check(f"{name}: C2 gives the class and lags its reason quotes", got == exp, {"c2": got, "declared": exp})


def guard_results(ctx, plan_ext=PLAN_EXT, units=UNITS_DIR):
    """No E34 unit record exists yet (the manifest is frozen before the first donor result) -> record; registered E34 rows'
    manifest shas are returned for the frozen-manifest guard."""
    rec = {"checked": False}
    if plan_ext is None and ctx.mode == "local":
        ctx.notes.append("the before-any-result guard did not run (synthetic tree without a plan)")
        return rec, set()
    if plan_ext is None or not os.path.exists(plan_ext):
        ctx.fail(f"plan {plan_ext} not available: the before-any-result guard cannot run", missing=True)
        return rec, set()
    rows = []
    for line in ctx.read_bytes(plan_ext, describe=False).decode().splitlines():
        if line.strip():
            r = json.loads(line)
            if str(r.get("family_id", "")).startswith(E34_FAMILY_PREFIX):
                rows.append(r)
    have = sorted(r["experiment_id"] for r in rows if units and os.path.exists(os.path.join(units, f"{r['experiment_id']}.json")))
    shas = {str((r.get("spec") or {}).get("manifest_sha256")) for r in rows if (r.get("spec") or {}).get("manifest_sha256")}
    rec = {"checked": True, "plan_ext": os.path.relpath(plan_ext, REPO) if _inside(plan_ext, REPO) else plan_ext,
           "n_e34_rows": len(rows), "n_e34_records": len(have), "registered_manifest_sha256": sorted(shas),
           "rule": "production refuses when any E34 (ALN32_PUBLIC_AUDIO_PRIOR_*) unit record exists, or when registered E34 rows quote "
                   "another manifest sha256"}
    if have:
        if ctx.mode == "production":
            raise Refused(f"{len(have)} E34 unit records already exist (e.g. {have[:3]}): the manifest is frozen before any result "
                          "(design §1); a new manifest needs a new execution id")
        ctx.notes.append(f"{len(have)} E34 unit records exist (dry run / synthetic: not refused)")
    return rec, shas


def _is_rich_row(r):
    return r.get("family_id") == RICH_DONOR_FAMILY or (r.get("spec") or {}).get("block") == RICH_BLOCK


def rich_results(ctx, plan_ext=PLAN_EXT, units=UNITS_DIR):
    """The E34 rows' rich state before the supplement is written -> (record, the manifest_rich_sha256 values registered rows quote,
    the rich-block rows that already have a unit record). Recorded in the supplement as declared_before_results."""
    if plan_ext is None and ctx.mode == "local":
        ctx.notes.append("the rich before-any-result guard did not run (synthetic tree without a plan)")
        return {"checked": False}, set(), []
    if plan_ext is None or not os.path.exists(plan_ext):
        ctx.fail(f"plan {plan_ext} not available: the rich before-any-result guard cannot run", missing=True)
        return {"checked": False}, set(), []
    rows = [r for r in (json.loads(x) for x in ctx.read_bytes(plan_ext, describe=False).decode().splitlines() if x.strip())
            if str(r.get("family_id", "")).startswith(E34_FAMILY_PREFIX)]
    quoted = {str((r.get("spec") or {}).get("manifest_rich_sha256")) for r in rows if (r.get("spec") or {}).get("manifest_rich_sha256")}
    have = sorted(r["experiment_id"] for r in rows if _is_rich_row(r) and units
                  and os.path.exists(os.path.join(units, f"{r['experiment_id']}.json")))
    rec = {"checked": True, "plan_ext": os.path.relpath(plan_ext, REPO) if _inside(plan_ext, REPO) else plan_ext,
           "n_rich_rows": int(sum(_is_rich_row(r) for r in rows)), "n_rich_records": len(have),
           "registered_manifest_rich_sha256": sorted(quoted),
           "rule": "production refuses when registered E34 rows quote another manifest_rich_sha256, or when an E34 rich-block unit "
                   "record exists and the supplement on disk would change"}
    return rec, quoted, have


def guard_rich(ctx, sha_new, old_sha, plan_ext=PLAN_EXT, units=UNITS_DIR, found=None):
    """The rich supplement is frozen before any rich result: production refuses when registered E34 rows quote another
    manifest_rich_sha256, or when an E34 rich-block unit record exists and the supplement on disk (old_sha) would change; a local or
    dry-run build only notes it. found = rich_results(...) when already read -> its record."""
    rec, quoted, have = found if found is not None else rich_results(ctx, plan_ext, units)
    bad = []
    if quoted and quoted != {sha_new}:
        bad.append(f"registered E34 rows quote manifest_rich_sha256 {sorted(quoted)} but this build gives {sha_new}")
    if have and old_sha is not None and old_sha != sha_new:
        bad.append(f"{len(have)} E34 rich-block unit records exist (e.g. {have[:3]}) and the supplement {old_sha[:16]} would change")
    if bad:
        if ctx.mode == "production":
            raise Refused("; ".join(bad) + ": the rich supplement is frozen before any rich result (a new one needs a new execution id)")
        ctx.notes.extend(bad)
    return rec


def unused_records(ctx, T, G, seg, masked, pools, declared, dtu_rows=()):
    """The unused-record table (§3.5) and data coverage per cohort and role."""
    out = []
    X = T["sparrkulee"]
    for r in X["items"]:
        if r.get("role") not in DONOR_ROLES:
            out.append({"cohort": "sparrkulee", "what": r["run_id"], "n": 1, "reason": r.get("role")})
    for (c, i), dcl in sorted(declared.items()):
        it = T[c]["items"][i]
        out.append({"cohort": c, "what": it.get("run_id", it.get("piece_id")), "n": 1, "reason": f"{DECLARED_ROLE} ({dcl['rule']})"})
    for (c, role), n in sorted(masked.items()):
        out.append({"cohort": c, "what": f"{role} segments meeting a C3 shared-audio span", "n": int(n),
                    "reason": "shared audio (jingles / duplicates) masked in every role"})
    for c, S in seg.items():
        lone = collections.Counter()
        for r in range(len(S["s"])):
            if S["role"][r] in DONOR_ROLES and S["n_partners"][r] == 0:
                lone[(S["role"][r], G["pres"][S["presentation"][r]]["key"])] += 1
        for (role, key), n in sorted(lone.items()):
            out.append({"cohort": c, "what": f"{role} segments of {key} without a partner", "n": int(n),
                        "reason": "single-listener presentation (or partners excluded): no cross-person anchor"})
    if "fau" in T:
        out.append({"cohort": "fau", "what": "competing-talker pieces", "n": int(sum(q.get("kind") == "cs" for q in T["fau"]["items"])),
                    "reason": "CSX only (fau_cs stratum); never core donors"})
    if "dtu" in T:
        it = T["dtu"]["items"]
        out += [{"cohort": "dtu", "what": "HI single-talker trials", "n": int(sum(str(q.get("group")).lower() == "hi" and q.get("kind") == "ss"
                                                                                  for q in it)),
                 "reason": "individually equalised audio: no shared presentation (target_only)"},
                {"cohort": "dtu", "what": "two-talker trials", "n": int(sum(q.get("kind") == "cs" for q in it)),
                 "reason": "individually timed maskers: not donors (target_only)"}]
    for (hear, kind, st, reason), n in sorted(collections.Counter(
            (str(r.get("hearing")), str(r.get("kind")), str(r.get("status")), str(r.get("reason"))) for r in dtu_rows).items()):
        out.append({"cohort": "dtu", "what": f"{hear.upper()} {'single' if kind == 'ss' else 'two'}-talker inventory trials not in the "
                                             f"C5 cache ({st})", "n": int(n), "reason": f"aln3_loader_filter: {reason}"})
    if "federici" in T:
        parts = T["federici"]["table"]["participants"]
        out.append({"cohort": "federici", "what": "phantom sessions", "n": int(sum(bool(p.get("test_only")) for p in parts)),
                    "reason": "never donors, outside human inference (test_only)"})
    cov = {}
    for c, S in seg.items():
        d = collections.defaultdict(lambda: {"n_segments": 0, "participants": set(), "pieces": set()})
        for r in range(len(S["s"])):
            v = d[(S["role"][r], S["kind"][r])]
            v["n_segments"] += 1
            v["participants"].add(S["participant"][r])
            v["pieces"].add(S["piece"][r])
        items = T[c]["items"]
        cached = [it for it in items if it.get("row_offset") is not None]
        loss = int(sum(int(it["T_eeg"]) for it in cached) - C.SEG_STEP * len(S["s"]))
        cov[c] = {"by_role_kind": {f"{role}/{kind}": {"n_segments": v["n_segments"], "n_participants": len(v["participants"]),
                                                      "n_pieces": len(v["pieces"]), "hours": round(v["n_segments"] * C.SEG_STEP / C.FS / 3600, 3)}
                                   for (role, kind), v in sorted(d.items())},
                  "n_cached_pieces": len(cached), "n_listed_not_cached": len(items) - len(cached),
                  "samples_outside_segments": loss,
                  "pool_core_rows": len(pools["core"].get(c, []))}
    return out, cov


def dtu_reconciliation(T, rows=()):
    """design §3.5: the DTU trials absent from the cache, each with its status and reason (rows = dtu_not_loaded())."""
    if "dtu" not in T:
        return {"absent_trials": [], "rule": "DTU C5 table not available (dry run)"}
    t = T["dtu"]["table"]
    rc = (t.get("checks") or {}).get("inventory_reconciliation") or {}
    keys = ("file", "trial", "subject", "hearing", "kind", "target_sha", "status", "reason")
    absent = [{k: r.get(k) for k in keys} for r in rows if r.get("hearing") == "nh" and r.get("kind") == "ss"]
    return {"absent_trials": absent, "not_loaded": [{k: r.get(k) for k in keys} for r in rows],
            "not_loaded_by_status": dict(sorted(collections.Counter(f"{r.get('hearing')}/{r.get('kind')}/{r.get('status')}"
                                                                    for r in rows).items())),
            "shas_below_2_listeners_in_cache": rc.get("shas_below_2_listeners_in_cache", []),
            "nh_single_talker": rc.get("nh_single_talker"), "trials": rc.get("trials"),
            "excluded_trials": t.get("excluded_trials", []),
            "unread_files": [{"file": os.path.basename(str(u.get("file"))), "reason": u.get("reason"),
                              "n_inventory_trials": u.get("n_inventory_trials")} for u in t.get("unread_files", [])],
            "rule": "C6 lists every inventory trial absent from the C5 cache with its status and reason (a trial of an unread file "
                    "takes the file's reason), the NH single-talker ones as absent_trials (design §3.5: 352 - 3 = 349), and the NH "
                    "single-talker shas that drop below 2 NH listeners in the cache (C5 checks.inventory_reconciliation); every one "
                    "is a declared aln3_loader_filter exclusion"}


def seen_coverage(cohorts):
    seen, cov = {}, {}
    for target, strata in DONORS.items():
        names = {n for c in strata if c in cohorts for n in C.MONTAGES[c]}
        lay = C.MONTAGES[target]
        seen[target] = [n for n in C.VOCAB if n in names]
        cov[target] = {"n_seen": sum(n in names for n in lay), "n_total": len(lay), "unseen": [n for n in lay if n not in names]}
    return seen, cov


def _code_shas(files=("manifest.py", "contract.py", "build_public.py")):
    """sha256 of the code a part runs (core: this module, contract.py, build_public.py's mode_c_scales / with_band_sd; rich: + build_rich.py)."""
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    for f in files:
        p = os.path.join(here, f)
        if os.path.exists(p):
            out[f"auditory_alignment_v3/prior33/{f}"] = sha256_file(p)[0]
    return out


def builder_sha():
    return sha256_file(os.path.abspath(__file__))[0]


def redact(full):
    """The public copy: the full manifest without the private_bdf children (PRIVATE_ID_FIELDS removed), copy 'public_redacted'."""
    pub = copy.deepcopy(full)
    pub["copy"] = "public_redacted"
    for cell in pub["cells"]:
        if cell["dataset"] == PRIVATE:
            for k in PRIVATE_ID_FIELDS:
                cell.pop(k, None)
            cell["ids"] = "redacted: the children are listed only in the 0700 private copy (manifest.py PRIVATE_ID_FIELDS)"
    pub["redaction"] = {"removed": [f"cells[dataset={PRIVATE}].{k}" for k in PRIVATE_ID_FIELDS],
                        "rule": "the public copy equals the full copy except these fields, 'copy' and this record"}
    return pub


def declared_choices(G, seg, pools, dsets, anywhere, dropped, std, scan_rec, excl):
    """The C6-level choices a reader of the frozen manifest must see (module docstring, Interpretations): rule, alternative and the
    effect on this build of each."""
    S = seg["sparrkulee"]
    key = {p["id"]: p["key"] for p in G["pres"]}
    devcal = {int(S["presentation"][r]): S["role"][r] for r in range(len(S["s"])) if S["role"][r] in ("dev", "bridge_cal")}
    kept = {k: {"rows": len(pools[k]["sparrkulee"]), "participants": len({S["participant"][r] for r in pools[k]["sparrkulee"]}),
                "presentations": sorted({key[int(S["presentation"][r])] for r in pools[k]["sparrkulee"]})} for k in ("dev", "bridge_cal")}
    removed = {key[p]: {"role": devcal[p], "excluded_for_targets": sorted({x.split("/")[0] for x in v})}
               for p, v in sorted(anywhere.items()) if p in devcal}
    mapped = []
    for t, d in sorted((scan_rec.get("targets") or {}).items()):
        for c, v in sorted(d.items()):
            for e in v.get("entries", []):
                if e.get("mapped_by") == "stimulus_code":
                    ids = {p["id"] for p in G["pres"] if p["cohort"] == c and p["key"] in set(e["presentations"])}
                    rows = pools["core"].get(c, [])
                    mapped.append({"target": t, "donor": c, "stream": e["stream"], "code": e.get("code"), "presentations": e["presentations"],
                                   "core_pool_rows_removed": int(sum(int(seg[c]["presentation"][r]) in ids for r in rows)),
                                   "core_pool_rows": len(rows)})
    dec = [e for e in excl if e["rule"] == "declared_structural_exclusion"]
    return [
        {"choice": "shared_dev_bridge_cal",
         "rule": "one SparrKULee dev / bridge_cal definition for every donor set (§3.2), without every presentation that any donor set "
                 "excludes (sampler.selection_sets fails closed on such a presentation)",
         "alternative": "per-target dev / bridge_cal sets (the §3.2 definition becomes target-specific; the fixed selection and bridge "
                        "sets and sampler.selection_sets would need one set per target)",
         "effect": {"presentations_removed": removed, "rows_dropped": dict(dropped), "kept": kept}},
        {"choice": "shared_standardiser",
         "rule": "one sigma over pools.core.sparrkulee without every presentation that any donor set excludes (§2.3; the same for every "
                 "target)",
         "alternative": "sigma over every SparrKULee donor-fit presentation (content that overlaps one target's stimuli would enter that "
                        "target's sigma), or one sigma per target (the target contract would then differ between targets)",
         "effect": None if std is None else {"left_out_presentations": std["left_out_presentations"], "n_windows": std["n_windows"]}},
        {"choice": "c3_unplayed_by_code", "enabled": scan_rec.get("map_unplayed_by_code"), "rule": scan_rec.get("mapping_rule"),
         "alternative": "C3's literal rule: a listed stream that no cached presentation plays removes nothing (the presentations below "
                        "would stay in those donor sets)",
         "effect": mapped},
        {"choice": "declared_exclusions", "rule": EXCLUSION_RULES["declared_structural_exclusion"],
         "alternative": "keep the run, as C2's registered rule and §3.2 / F11 would",
         "effect": [{"run_id": e["run_id"], "required_by": e["detail"].get("required_by"), "conflicts": e["detail"].get("conflicts"),
                     "n_segments": e["detail"].get("n_segments"),
                     "presentation_excluded_for": e["detail"].get("presentation_excluded_for")} for e in dec]},
    ]


# ---------------------------------------------------------------------------------------------------------- core build
def build_core(root, *, out=None, out_private=None, dry_run=False, aln3_plan=ALN3_PLAN, units_dir=UNITS_DIR, plan_ext=PLAN_EXT,
               declared=DECLARED_EXCLUSIONS, bind_private=None, private_kids=None, log=print):
    """Build the core manifest (C6, module docstring) -> summary {mode, manifest, full, sha256 ...}."""
    mode, out, out_private = resolve_mode(root, out, out_private, dry_run)
    ctx = _Ctx(root, mode, log)
    log(f"C6 core manifest: mode {mode}, root {ctx.root}")
    guard, registered = guard_results(ctx, plan_ext, units_dir)
    T = {"sparrkulee": load_sparrkulee(ctx)}
    for c in PUBLIC:
        X = load_public(ctx, c)
        if X is not None:
            T[c] = X
    scan = load_scan(ctx)
    check_registry(ctx, T)
    G = assign_ids(ctx, T, scan)
    shared = shared_audio(ctx, T, G, scan)
    dec = declared_pieces(ctx, T, declared)
    check_declared_basis(ctx, T, dec)
    twins = [list(x) for x in T["federici"]["table"].get("partner_exclusions", [])] if "federici" in T else []
    seg, masked, hc_hcv = segment_tables(ctx, T, G, shared, dec, twins)
    # families must stay role-disjoint across the SparrKULee donor roles (C3 family_mask_covers overlaps are not masked)
    S = seg["sparrkulee"]
    fam_roles = collections.defaultdict(set)
    for r in range(len(S["s"])):
        if S["role"][r] in DONOR_ROLES:
            fam_roles[S["family"][r]].add(S["role"][r])
    split_fams = sorted([G["fams"][f]["name"], sorted(v)] for f, v in fam_roles.items() if len(v) > 1)
    ctx.check("SparrKULee families are role-disjoint across fit / dev / bridge_cal", not split_fams, split_fams)
    pools = build_pools(ctx, T, seg)
    c3x, scan_rec = c3_exclusions(ctx, T, G, scan)
    dsets = donor_sets(ctx, T, G, seg, pools, scan, c3x)
    anywhere = excluded_anywhere(dsets, "sparrkulee")
    dropped = {}
    for k in ("dev", "bridge_cal"):
        rows = pools[k]["sparrkulee"]
        pools[k]["sparrkulee"] = [r for r in rows if int(S["presentation"][r]) not in anywhere]
        dropped[k] = len(rows) - len(pools[k]["sparrkulee"])
    devcal = {int(S["presentation"][r]) for r in range(len(S["s"])) if S["role"][r] in ("dev", "bridge_cal")}
    flagged = sorted(G["pres"][p]["key"] for p in anywhere if p in devcal)
    ctx.check("no SparrKULee dev / bridge_cal presentation is excluded for a target (else the shared §3.2 definition becomes "
              "target-specific: reported, rows dropped from the shared sets)", not flagged, {"presentations": flagged,
                                                                                            "rows_dropped": dropped}, hard=False)
    std_rows = [r for r in pools["core"]["sparrkulee"] if int(S["presentation"][r]) not in anywhere]
    core_sk = {int(S["presentation"][r]) for r in pools["core"]["sparrkulee"]}
    std, _u = standardiser(ctx, T, G, seg, std_rows, left_out=sorted(core_sk & set(anywhere)))
    proj, p_raw = projection(ctx)
    filters = C.filter_shas()
    target_contract = None if std is None else _sha(json.dumps({"sigma": std["sigma"], "mu": [0.0] * C.N_TGT, "P": proj["sha256"],
                                                               "filters": filters}, sort_keys=True).encode())
    sel, bridge = fixed_sets(ctx, seg, pools, dsets)
    n_sk = len(pools["core"]["sparrkulee"])
    budget = {"N_SK": n_sk, "anchors_per_ep_eq": C.N_ANCHORS * n_sk, "steps_per_ep_eq": C.N_ANCHORS * n_sk / 256,
              "steps_per_ep_eq_ceil": math.ceil(C.N_ANCHORS * n_sk / 256), "ep_eq0": 30, "ep_eq_limit": 60,
              "S0": math.ceil(30 * C.N_ANCHORS * n_sk / 256),
              "rule": "1 ep-eq = 8 anchors x N_SK (eligible SparrKULee donor-fit listener segments = |pools.core.sparrkulee|, after "
                      "C3's shared-audio mask); 256 anchors per step; S0 = ceil(30 x 8 x N_SK / 256)"}
    seen, coverage = seen_coverage(set(T))
    cells = public_cells(ctx, T)
    recs, recs_info = aln3_records(ctx, aln3_plan, units_dir)
    cell_rows = check_cells(ctx, cells, recs)
    bind = (mode != "dry_run") if bind_private is None else bool(bind_private)
    pcells, psummary = ([], [])
    if private_kids is not None:
        pcells, psummary = private_cells(ctx, None, kids=private_kids)
    elif bind:
        pcells, psummary = private_cells(ctx, recs)
    else:
        ctx.fail("private_bdf cells not bound (dry run without --bind-private)", missing=True)
    cells += pcells
    counts = collections.Counter(c["dataset"] for c in cells)
    ctx.check("30 target cells: FAU 10, DTU 10, Federici 5, private_bdf 5",
              dict(counts) == {"fau": 10, "dtu": 10, "federici": 5, "private_bdf": 5}, dict(counts))
    mc = mode_c(ctx, T)
    dtu_rows = dtu_not_loaded(ctx, T)
    excl, excl_summary = exclusions(ctx, T, dec, dtu_rows, anywhere, G, seg)
    unused, data_cov = unused_records(ctx, T, G, seg, masked, pools, dec, dtu_rows)
    choices = declared_choices(G, seg, pools, dsets, anywhere, dropped, std, scan_rec, excl)
    cohorts = {}
    for c, X in T.items():
        info = X["info"]
        cohorts[c] = {**{k: info[k] for k in ("dir", "fs_native", "n_ch", "layout", "reference", "band", "guards", "s_first", "n_rows",
                                              "table", "items", "env", "streams", "role_slabs") if k in info},
                      "caches": dict(X["caches"]), "unit": info.get("unit"),
                      "masked_cells": int(sum(len(it.get("masked") or []) for it in X["items"] if it.get("row_offset") is not None)),
                      "id_space": ID_SPACE}
    for c, X in T.items():
        for f in (X["info"]["table"], X["info"]["streams"], X["info"]["env"]):
            if f"{c}/{f}" not in ctx.files:
                raise ManifestError(f"{c}/{f}: described but not read")
    inputs = {"sparrkulee": {"runs_table_sha256": T["sparrkulee"]["sha"]["runs_table"],
                             "align_audit_sha256": T["sparrkulee"]["sha"]["align_audit"], "runs_sha256": T["sparrkulee"]["sha"]["runs"],
                             "builder_sha256": T["sparrkulee"]["table"].get("builder_sha256"),
                             "audit_meta": {k: T["sparrkulee"]["audit_meta"].get(k) for k in ("classes", "misaligned", "rule")}},
              "c3": None if scan is None else scan["record"], "aln3_records": recs_info,
              "c5": {c: {"pieces_sha256": T[c]["sha"]["pieces"], "builder_sha256": T[c]["table"].get("builder_sha256"),
                         "layout_sha256": T[c]["table"].get("layout_sha256"), "partial": T[c]["table"].get("partial"),
                         "mode_c": T[c]["table"].get("mode_c"), "unit": T[c]["table"].get("unit") and
                         {k: T[c]["table"]["unit"].get(k) for k in ("supported", "name", "source_unit", "factor_to_uV", "basis", "reason")}}
                     for c in PUBLIC if c in T}}
    full = {"schema": SCHEMA, "contract": C.CONTRACT, "synthetic": False, "copy": "private_full", "builder_sha256": builder_sha(),
            "code": _code_shas(), "cache_root": ctx.root,
            "constants": {"fs": C.FS, "l_in": C.L_IN, "n_tgt": C.N_TGT, "seg_ticks": C.SEG_TICKS, "seg_step": C.SEG_STEP,
                          "env_edge": C.ENV_EDGE, "neighbor": C.NEIGHBOR, "tau": C.TAU, "onset64": C.ONSET64,
                          "key_bits": [C.FAMILY_BITS, C.PRES_BITS, C.S_BITS],
                          "tick_offs_sha256": _sha(np.ascontiguousarray(C.TICK_OFFS, dtype=np.int64).tobytes())},
            "filters": filters, "target_contract": target_contract, "projection": proj, "standardiser": std,
            "vocab": list(C.VOCAB), "aliases": dict(C.ALIASES), "montages": {k: list(v) for k, v in C.MONTAGES.items()},
            "cohorts": cohorts, "families": G["fams"], "presentations": [{k: v for k, v in p.items() if k != "local_id"} for p in G["pres"]],
            "shared_audio": shared, "overlap": overlap_records(T, G, scan), "partner_exclusions": twins,
            "hc_hcv_excluded_pairs": int(hc_hcv), "segments": seg, "pools": pools, "donor_sets": dsets, "budget": budget,
            "selection": sel, "bridge": bridge, "seen": seen, "coverage": coverage, "cells": cells,
            "cell_binding": {"public": cell_rows, "private": psummary,
                             "rule": "public cells from the C5 tables checked against every completed ALN3 A_LOCAL record (seed 3401) "
                                     "of the cell; private_bdf cells bound from the completed E_LOCAL records (seed 3401)"},
            "mode_c": mc, "exclusions": excl, "exclusion_rules": dict(EXCLUSION_RULES), "exclusion_summary": excl_summary,
            "unused": unused, "data_coverage": data_cov, "dtu_reconciliation": dtu_reconciliation(T, dtu_rows),
            "declared_before_results": guard, "inputs": inputs, "overlap_scan": scan_rec, "identity_overlap": identity_overlap(scan),
            "declared_choices": choices,
            "rich_supplement": {"file": MANIFEST_RICH, "schema": RICH_SCHEMA,
                                "rule": "core first (inherited §4): this manifest needs no C7 output; the rich block (§2.15) is the "
                                        "supplement manifest_rich.json, built by manifest.py --part rich after C7, carrying this "
                                        "manifest's sha256 and rich_build.json's. A row that needs it (every RICH_DONOR group) quotes "
                                        "its sha256 as spec.manifest_rich_sha256 beside spec.manifest_sha256; manifest.open_for_row() "
                                        "opens both (manifest.open_with_rich() merges the supplement into an opened core manifest)"}}
    if mode == "dry_run":
        full["dry_run"] = {"missing": ctx.missing, "notes": ctx.notes, "private_ids_written": False,
                           "warning": "a dry run: never a frozen manifest"}
        for cell in full["cells"]:
            if cell["dataset"] == PRIVATE:
                for k in PRIVATE_ID_FIELDS:
                    cell.pop(k, None)
                cell["ids"] = "not written (dry run)"
    full["checks"] = ctx.checks
    full["files"] = dict(sorted(ctx.files.items()))
    raw_full = dumps(full)
    sha_full = _sha(raw_full)
    pub = redact(full)
    pub["full_manifest_sha256"] = sha_full
    raw_pub = dumps(pub)
    sha_pub = _sha(raw_pub)
    if mode == "production" and registered and registered != {sha_full}:
        raise Refused(f"registered E34 rows quote manifest sha256 {sorted(registered)} but this build gives {sha_full}: a frozen manifest "
                      "would change (a new manifest needs a new execution id)")
    dst = ctx.root if mode != "dry_run" else out
    pub_path, full_path = os.path.join(dst, MANIFEST), os.path.join(out_private, MANIFEST)
    old = None
    if os.path.exists(pub_path):
        with open(pub_path, "rb") as f:
            old = _sha(f.read())
    os.makedirs(out_private, mode=0o700, exist_ok=True)
    os.chmod(out_private, 0o700)
    if p_raw is not None:                     # P is generated once and never regenerated (written only after every check passed)
        _write(os.path.join(dst, C.P_FILE), p_raw)
    _write(full_path, raw_full)
    _write(pub_path, raw_pub)
    log(f"C6 core manifest written: {pub_path} (public, sha256 {sha_pub[:16]}) and {full_path} (full, sha256 {sha_full[:16]}; "
        f"the rows' manifest_sha256){'' if old is None else ('; unchanged' if old == sha_pub else f'; replaced {old[:16]}')}")
    return {"mode": mode, "manifest": pub_path, "manifest_sha256": sha_pub, "full": full_path, "full_sha256": sha_full,
            "previous_sha256": old, "n_presentations": len(G["pres"]), "n_families": len(G["fams"]),
            "n_segments": {c: len(v["s"]) for c, v in seg.items()}, "budget": budget, "missing": ctx.missing, "notes": ctx.notes}


def overlap_records(T, G, scan):
    """manifest.overlap from C3 cross_cohort.overlaps (lag = b.span[0] - a.span[0], the fixture's sign; scan_audio.py `lag`)."""
    if scan is None:
        return []
    sid_stream = {}
    for p in G["pres"]:
        sid_stream.setdefault((p["cohort"], p["sid"]), p["stream"])
        if p["ignored_sid"] is not None:
            sid_stream.setdefault((p["cohort"], p["ignored_sid"]), p["ignored_stream"])
    out = []
    for o in scan["doc"]["cross_cohort"].get("overlaps", []):
        rec = {"lag": o.get("lag"), "r": o.get("r_pooled", o.get("r_detect_max")), "r_detect_max": o.get("r_detect_max"),
               "coverage": o.get("coverage"), "refined": o.get("refined", True), "rule": "10 s windows, 2 s hop, r >= 0.7 (C3)"}
        for side in ("a", "b"):
            s = o[side]
            rec[side] = {"cohort": s["cohort"], "stimulus": s.get("stimulus"), "sid": str(s["stream"]), "kind": s.get("kind"),
                         "keyed": s.get("keyed"), "span": s.get("span"), "stream": sid_stream.get((s["cohort"], str(s["stream"])))}
        out.append(rec)
    return out


# ---------------------------------------------------------------------------------------------------------- rich supplement
def _read_core(root, out_private, ctx):
    pub_path, full_path = os.path.join(root, MANIFEST), os.path.join(out_private, MANIFEST)
    for p in (pub_path, full_path):
        if not os.path.exists(p):
            raise ManifestError(f"--part rich: {p} missing (build --part core first)")
    raw_pub, raw_full = ctx.read_bytes(pub_path, describe=False), ctx.read_bytes(full_path, describe=False)
    full = json.loads(raw_full)
    want = redact(full)
    want["full_manifest_sha256"] = _sha(raw_full)
    if dumps(want) != raw_pub:
        raise ManifestError(f"{pub_path} is not the redaction of {full_path} (the two copies come from different builds)")
    if full.get("schema") != SCHEMA or full.get("contract") != C.CONTRACT:
        raise ManifestError(f"{full_path}: schema {full.get('schema')} / contract {full.get('contract')}")
    return full, _sha(raw_full), _sha(raw_pub)


def build_rich(root, *, out=None, out_private=None, dry_run=False, plan_ext=PLAN_EXT, units_dir=UNITS_DIR, log=print):
    """The rich supplement manifest_rich.json after C7 (module docstring, Core first)."""
    from auditory_alignment_v3.prior33 import build_rich as BR
    mode, out, out_private = resolve_mode(root, out, out_private, dry_run)
    ctx = _Ctx(root, mode, log)
    core_dir = ctx.root if mode != "dry_run" else out
    full, sha_full, sha_pub = _read_core(core_dir, out_private, ctx)
    if mode != "dry_run" and full.get("dry_run"):
        raise ManifestError("--part rich: the core manifest is a dry run")
    if not os.path.exists(ctx.path(RICH_BUILD)):
        raise ManifestError(f"--part rich: {ctx.path(RICH_BUILD)} missing (C7 build_rich.py has not finished; the core does not wait for it)")
    rb, rb_sha = ctx.read_json(ctx.path(RICH_BUILD))
    if rb.get("schema") != SCHEMAS["rich_build"] or rb.get("contract") != C.CONTRACT:
        raise ManifestError(f"rich_build.json schema {rb.get('schema')!r}, {SCHEMAS['rich_build']} expected")
    scan_sha = ((full.get("inputs") or {}).get("c3") or {}).get("sha256")
    fm = rb.get("fit_mask") or {}
    ctx.check("C7 is a full build (not partial) with C3's shared-audio mask applied, from the scan the core manifest froze",
              rb.get("partial") is False and fm.get("applied") is True and fm.get("sha256") == scan_sha,
              {"partial": rb.get("partial"), "fit_mask": {k: fm.get(k) for k in ("applied", "sha256")}, "core_scan_sha256": scan_sha})
    mr = rb["manifest_rich"]
    refit = rb.get("refit")
    if mode == "production" or refit is not None:
        ctx.check("FIXC rich PCA refit uses this core manifest and excludes every donor-set-barred presentation",
                  bool(refit) and refit.get("rule") == "core_fit_unique_windows_exclude_any_donor_set_presentation_v1"
                  and refit.get("core_manifest_sha256") == sha_full,
                  {"refit": refit, "core_manifest_sha256": sha_full})
    cohorts, files_core = {}, full["files"]
    rich_sk, rows_sk = None, None
    for c in COHORTS:
        cc = (rb.get("cohorts") or {}).get(c)
        if c not in full["cohorts"]:
            ctx.fail(f"--part rich: cohort {c} is not in the core manifest", missing=True)
            continue
        if cc is None or cc.get("stale") or cc.get("partial"):
            ctx.fail(f"rich_build.json cohort {c}: {'absent' if cc is None else 'stale or partial'}")
            continue
        d = ctx.path(c)
        rs, rs_sha = ctx.read_json(os.path.join(d, RICH_STREAMS))
        if rs.get("schema") != SCHEMAS["rich_streams"] or rs.get("cohort") != c:
            raise ManifestError(f"{c} rich_streams.json schema {rs.get('schema')!r}")
        info = full["cohorts"][c]
        want = {"streams_sha256": files_core.get(f"{c}/{info['streams']}", {}).get("sha256"),
                "env_sha256": files_core.get(f"{c}/{info['env']}", {}).get("sha256"),
                "table_sha256": files_core.get(f"{c}/{info['table']}", {}).get("sha256")}
        got = {k: (rs.get("inputs") or {}).get(k) for k in want}
        ctx.check(f"{c}: C7 read the stream table, envelope and table the core manifest froze", got == want, {"got": got, "core": want})
        ctx.check(f"{c}: rich_streams.json uses the PCA-4 basis of rich_build.json",
                  rs.get("pca4_sha256") == mr["pca4"]["sha256"] == cc.get("pca4_sha256"),
                  [rs.get("pca4_sha256"), mr["pca4"]["sha256"], cc.get("pca4_sha256")])
        sha_r, shape_r, dtype_r = ctx.hash_big(os.path.join(d, RICH_FILE))
        sraw = ctx.read_bytes(os.path.join(d, info["streams"]), describe=False)
        ctx.check(f"{c}: streams.json is unchanged since the core manifest", _sha(sraw) == want["streams_sha256"],
                  [_sha(sraw)[:16], str(want["streams_sha256"])[:16]])
        streams_doc = json.loads(sraw)["streams"]
        n_env = sum(int(r["length"]) for r in streams_doc)
        if dtype_r != np.float32 or shape_r != (n_env, len(C.RICH_COLS)):
            raise ManifestError(f"{c} rich_f32.npy {dtype_r} {shape_r}, float32 ({n_env}, {len(C.RICH_COLS)}) expected")
        ctx.check(f"{c}: rich_f32.npy is the file rich_build.json describes", sha_r == cc.get("rich_sha256") and
                  rs_sha == cc.get("rich_streams_sha256"), [sha_r[:16], str(cc.get("rich_sha256"))[:16]])
        no_src = set(rs.get("no_source_reasons") or [])
        bad = []
        for i, (r, s) in enumerate(zip(rs["streams"], streams_doc)):
            if int(r["stream"]) != i or int(r["length"]) != int(s["length"]):
                bad.append([i, "stream / length"])
            if bool(r["available"]) != (r.get("reason") is None):
                bad.append([i, "available vs reason"])
            if r.get("reason") is not None and r.get("reason") not in (rs.get("reasons") or {}):
                bad.append([i, f"reason {r.get('reason')} outside the file's vocabulary"])
            if (r.get("source_sha256") is None) != (r.get("reason") in no_src):
                bad.append([i, "source_sha256 vs the no-source reasons"])
        if len(rs["streams"]) != len(streams_doc):
            bad.append(["n_streams", len(rs["streams"]), len(streams_doc)])
        ctx.check(f"{c}: rich_streams rows match the core streams and the file's own reason vocabulary", not bad, bad[:5])
        if c == "sparrkulee":
            rich_sk = np.load(check_path(os.path.join(d, RICH_FILE)), mmap_mode="r", allow_pickle=False)
            rows_sk, streams_sk = rs["streams"], streams_doc
        cohorts[c] = {"rich": RICH_FILE, "rich_streams": RICH_STREAMS, "n_streams": len(rs["streams"]),
                      "n_available": int(sum(bool(r["available"]) for r in rs["streams"])),
                      "masked": [{"name": r["name"], "reason": r["reason"]} for r in rs["streams"] if not r["available"]]}
    # the basis and projections
    V, _ = ctx.read_npy(ctx.path(PCA_FILE))
    ok_v = V.dtype == np.float64 and V.shape == (128, 4) and _sha(np.ascontiguousarray(V).tobytes()) == mr["pca4"]["sha256"]
    ctx.check("rich_pca4_f64.npy is the basis manifest_rich names", ok_v, {"shape": list(V.shape), "dtype": str(V.dtype)})
    for k in ("ss", "sc"):
        e = mr[f"P_{k}"]
        P, _ = ctx.read_npy(ctx.path(C.RICH_P_FILE[k]))
        fresh = semi_orthogonal(*C.RICH_P_SHAPE[k], C.RICH_SEEDS[k])
        ok = e["file"] == C.RICH_P_FILE[k] and int(e["seed"]) == C.RICH_SEEDS[k] and list(e["shape"]) == list(C.RICH_P_SHAPE[k]) and \
            P.dtype == np.float32 and _sha(np.ascontiguousarray(P).tobytes()) == e["sha256"] and np.array_equal(P, fresh)
        ctx.check(f"P_{k} is the contract projection (file, seed, shape, sha256, fresh generation)", ok, {k_: e.get(k_) for k_ in ("file", "seed")})
    # sigma: C7's arrays reproduce C7's stored sigma under C7's own fit rule (hard); the supplement uses the core standardiser's
    # windows (pools.core.sparrkulee without any presentation a donor set excludes), and records the difference
    sig, sig7 = None, None
    if rich_sk is not None:
        S = full["segments"]["sparrkulee"]
        runs = json.loads(ctx.read_bytes(ctx.path("sparrkulee", full["cohorts"]["sparrkulee"]["table"]), describe=False))["runs"]
        shared_sk = collections.defaultdict(list)
        for d_ in full["shared_audio"]:
            if d_["cohort"] == "sparrkulee":
                shared_sk[int(d_["stream"])].append(list(d_["span"]))
        if refit:
            from .refit_rich import core_fit_windows
            W7, _ = core_fit_windows(full)
        else:
            W7, _ = BR.sk_fit_windows(runs, dict(shared_sk))
        sig7 = BR.rich_standardiser(rich_sk, streams_sk, rows_sk, W7)
        rel7 = max(float(np.max(np.abs(np.asarray(sig7[k]) - np.asarray(mr[k])) / np.maximum(np.abs(np.asarray(mr[k])), 1e-300)))
                   for k in ("sigma_ss", "sigma_sc"))
        ctx.check("C7's sigma_ss / sigma_sc are reproduced from its arrays under its recorded fit rule (FIXC core windows when refitted)",
                  rel7 < 1e-9 and int(sig7["n_windows"]) == int(mr["n_windows"]),
                  {"max_rel_diff": rel7, "n_windows": [sig7["n_windows"], mr["n_windows"]]})
        anywhere = excluded_anywhere(full["donor_sets"], "sparrkulee")
        pairs = sorted({(int(full["presentations"][S["presentation"][r]]["stream"]), int(S["s"][r]))
                        for r in full["pools"]["core"]["sparrkulee"] if int(S["presentation"][r]) not in anywhere})
        sig = BR.rich_standardiser(rich_sk, streams_sk, rows_sk, BR.segment_windows(pairs))
        rel = max(float(np.max(np.abs(np.asarray(sig[k]) - np.asarray(mr[k])) / np.maximum(np.abs(np.asarray(mr[k])), 1e-300)))
                  for k in ("sigma_ss", "sigma_sc"))
        ctx.check("the supplement's sigma (core standardiser windows) vs C7's stored sigma (reported; they differ only when a donor "
                  "set excludes a SparrKULee fit presentation)", True,
                  {"max_rel_diff": rel, "n_windows": [sig["n_windows"], mr["n_windows"]],
                   "left_out_presentations": (full.get("standardiser") or {}).get("left_out_presentations")}, hard=False)
        del rich_sk
    rich = {"columns": list(C.RICH_COLS), "y_layout": mr["y_layout"], "pca4": mr["pca4"], "P_ss": mr["P_ss"], "P_sc": mr["P_sc"],
            "sigma_ss": sig["sigma_ss"] if sig else mr["sigma_ss"], "sigma_sc": sig["sigma_sc"] if sig else mr["sigma_sc"],
            "mu_estimate_ss": sig["mu_estimate_ss"] if sig else mr["mu_estimate_ss"],
            "mu_estimate_sc": sig["mu_estimate_sc"] if sig else mr["mu_estimate_sc"],
            "n_windows": int(sig["n_windows"]) if sig else int(mr["n_windows"]), "loss_weights": list(mr["loss_weights"])}
    if [float(x) for x in rich["loss_weights"]] != [1.0, 0.5, 0.5] or rich["columns"] != list(C.RICH_COLS):
        raise ManifestError(f"manifest_rich loss weights {rich['loss_weights']} / columns {rich['columns']} differ from §2.15")
    unused = [{"cohort": c, "what": f"rich targets of {m['name']}", "n": 1, "reason": m["reason"]} for c, v in cohorts.items() for m in v["masked"]]
    found = rich_results(ctx, plan_ext, units_dir)
    supp = {"schema": RICH_SCHEMA, "contract": C.CONTRACT, "builder_sha256": builder_sha(),
            "code": _code_shas(("manifest.py", "contract.py", "build_rich.py") + (("refit_rich.py",) if refit else ())),
            "core_manifest_sha256": sha_full, "core_manifest_public_sha256": sha_pub, "core_manifest": MANIFEST,
            "rich_build_sha256": rb_sha, "scan_audio_sha256": scan_sha, "rich": rich, "cohorts": cohorts, "unused": unused,
            "c7": {"builder_sha256": rb.get("builder_sha256"), "refit": refit, "fit_mask": fm, "targets": rb.get("targets"),
                   "manifest_rich_as_built": {k: mr.get(k) for k in ("sigma_ss", "sigma_sc", "n_windows")},
                   "sigma_rule": "recomputed with build_rich.rich_standardiser over the unique (stream, window) of pools.core.sparrkulee "
                                 "without any presentation a donor set excludes (the core standardiser's windows), rich-available "
                                 "streams only; C7's stored sigma (FIXC: these same windows; legacy: every C4 fit run) is kept under "
                                 "manifest_rich_as_built and reproduced from the arrays as a check",
                   "pca4_fit": ("FIXC refit on core-manifest windows excluding whole presentations barred by any donor set"
                                if refit else "synthetic/legacy C7 basis; no FIXC refit"),
                   "sigma_c7_rule_recomputed": None if sig7 is None else {k: sig7[k] for k in ("sigma_ss", "sigma_sc", "n_windows")}},
            "declared_choices": ([
                {"choice": "rich_pca4_refit_exclude_all_flagged_presentations",
                 "rule": "PCA-4 and sigma share core-manifest donor-fit windows; every presentation barred by any target donor set is excluded",
                 "alternative": "the original C7 basis included partial target-overlap content; preserved in rich_before_fixc_20261017",
                 "effect": {"basis_includes_left_out_presentations": [], "n_windows": rich["n_windows"]}}] if refit else [
                {"choice": "rich_pca4_basis_as_built",
                 "rule": "C7's PCA-4 basis (fitted on C7's fit windows: every C4 fit run, C3 mask applied) is used as fitted",
                 "alternative": "refit the basis without the SparrKULee fit presentations that the core sigma leaves out (a C7 change)",
                 "effect": {"basis_includes_left_out_presentations": (full.get("standardiser") or {}).get("left_out_presentations"),
                            "sigma": "recomputed over the core standardiser's windows (c7.sigma_rule)"}}]),
            "usage": "a row that needs the rich block (every RICH_DONOR group) quotes this file's sha256 as spec.manifest_rich_sha256 "
                     "beside spec.manifest_sha256 (the core full copy); manifest.open_for_row() opens both",
            "declared_before_results": found[0],
            "checks": ctx.checks, "files": dict(sorted(ctx.files.items()))}
    if mode == "dry_run":
        supp["dry_run"] = {"missing": ctx.missing, "notes": ctx.notes}
    raw = dumps(supp)
    sha = _sha(raw)
    dst = ctx.root if mode != "dry_run" else out
    old = None
    if os.path.exists(os.path.join(dst, MANIFEST_RICH)):
        with open(os.path.join(dst, MANIFEST_RICH), "rb") as f:
            old = _sha(f.read())
    guard = guard_rich(ctx, sha, old, found=found)
    os.makedirs(out_private, mode=0o700, exist_ok=True)
    os.chmod(out_private, 0o700)
    _write(os.path.join(dst, MANIFEST_RICH), raw)
    _write(os.path.join(out_private, MANIFEST_RICH), raw)
    log(f"C6 rich supplement written: {os.path.join(dst, MANIFEST_RICH)} (sha256 {sha[:16]}; core {sha_full[:16]})")
    return {"mode": mode, "manifest_rich": os.path.join(dst, MANIFEST_RICH), "sha256": sha, "core_manifest_sha256": sha_full,
            "previous_sha256": old, "guard": guard, "missing": ctx.missing, "notes": ctx.notes}


def open_with_rich(manifest, rich_sha, rich_path=None):
    """Consumer implementation lives in views.py, included in every prior training code hash."""
    from auditory_alignment_v3.prior33 import views as V
    return V.open_with_rich(manifest, rich_sha, rich_path)


def open_for_row(row, *, paths=None, rich_paths=None, cache_root=None):
    """Open the full core copy and optional rich supplement; retain builder defaults for callers."""
    from auditory_alignment_v3.prior33 import views as V
    default = paths is None
    return V.open_for_row(
        row, paths=([os.path.join(PRIVATE_OUT, MANIFEST), os.path.join(CACHE_ROOT, MANIFEST)] if default else paths),
        rich_paths=([os.path.join(PRIVATE_OUT, MANIFEST_RICH), os.path.join(CACHE_ROOT, MANIFEST_RICH)]
                    if rich_paths is None else rich_paths),
        cache_root=cache_root or (CACHE_ROOT if default else None))


# ---------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m auditory_alignment_v3.prior33.manifest",
                                 description="E34_PUBLIC_PRIOR C6: the manifest (PUBLIC_PRIOR_DESIGN.md §6.2 C6). Exit 0 written, "
                                             "1 error, 2 usage, 3 refused by a guard.")
    ap.add_argument("--part", required=True, choices=("core", "rich"), help="core (needs C1-C5, never C7) or rich (after C7)")
    ap.add_argument("--root", required=True, help=f"the cache root {CACHE_ROOT} (production) or a synthetic tree")
    ap.add_argument("--out-private", default=None, help=f"the 0700 directory of the full copy (default {PRIVATE_OUT}; dry run "
                                                        "<out>/private)")
    ap.add_argument("--dry-run", action="store_true", help="read --root, write only into --out (a scratch directory)")
    ap.add_argument("--out", default=None, help="dry runs only: the scratch output directory")
    ap.add_argument("--bind-private", action="store_true", help="dry runs: also bind the private_bdf cells in memory (ids are "
                                                               "never written by a dry run)")
    a = ap.parse_args(argv)
    try:
        if a.part == "core":
            res = build_core(a.root, out=a.out, out_private=a.out_private, dry_run=a.dry_run,
                             bind_private=True if a.bind_private else None)
        else:
            res = build_rich(a.root, out=a.out, out_private=a.out_private, dry_run=a.dry_run)
    except Refused as e:
        print(f"C6 refused: {e}", file=sys.stderr)
        return 3
    except (ManifestError, RestrictedAccess, FileNotFoundError) as e:
        print(f"C6 error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(_plain(res), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
