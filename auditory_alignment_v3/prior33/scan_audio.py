"""C3 audio scan for E34_PUBLIC_PRIOR (private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.5 family clocks, §3.4 overlap
exclusion and duplicate content, §6.2 C3, §6.6 M2c). Stimulus-side only: no EEG array is read, no job is submitted.

    python -m auditory_alignment_v3.prior33.scan_audio --out /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1

writes <out>/scan_audio.json (0444) after every assertion passed (exit 0), or <out>/scan_audio.FAILED.json with the diagnostics
(exit 3), and then <out>/scan_audio.latest.json (0444): the pointer to this run's result {status ok | failed, file, sha256,
created_utc, signature, builder_sha256}, which records a result of the other kind that is still present as `superseded` (an older
FAILED file after a success) or `stale` (an older scan_audio.json after a failed rerun). Nothing is moved or deleted. Without
--force an existing scan_audio.json is reused only when the pointer says ok for its sha256 and its builder sha256 is this file's
("nothing to do", exit 0); otherwise the run stops with exit 4 (--force recomputes). Work is resumable per unit:
<out>/scan_audio_work/<signature16>/<scan>__<query>__<bank>__<unit>.npz (tmp + os.replace; a unit is reused only when its stored
spec matches; the signature covers this file, contract.py, the rule parameters and the processed streams). With the real sources
--out must be the design cache root; a --sources JSON (synthetic trees, tests) may not write there.
Real sizes: SparrKULee 3.66 M samples at 64 Hz (72 files), DTU 1.92 M, FAU ~0.3 M, Federici ~0.45 M, i.e. ~28 M window-blocks:
~3.5 h with one FFT thread, ~1.5-2.5 h with --workers 4-8 (only the scipy FFTs are threaded); RSS well below 1 GB.

Streams. Every stream is the contract envelope chain of §2.3 applied to the source the existing loaders read, at its own origin:
nan_to_num (non-finite count recorded) -> contract.resample64 (h_aa) -> contract.band(env_sos, padlen 128) -> contract.rms_norm.
  sparrkulee  <root>/derivatives/preprocessed_stimuli/<stim>_envelope.npy (T, 1) 64 Hz, np.load(allow_pickle=False) on the file
              bytes; stream id = <stim>, kind "attended", keyed. audiobook_9_2_envelope-1.npy does not match *_envelope.npy and is
              listed as ignored; 72 files asserted. *.data_dict / *.pkl are never opened; nothing under preprocessed_eeg or a
              participant directory is listed or opened (restricted sub-019/020/021/022/026 refused in code, guard_path).
  fau         c3_preproc_v1/fau_tud/stimulus_env_128.h5 <code>/{attended,distractor}_env/raw (prep_targets.FAU_ENV), 128 Hz; ids
              "<code>/attended" (keyed) and "<code>/distractor" (not keyed; all-NaN distractors of single-talker codes are silent
              and skipped, listed).
  dtu         kcs_targets_v1/audio_local.h5 <sha>/env, 128 Hz, every sha of c3_features_v1/dtu/inventory.json; id = sha; kind
              "attended" (a target waveform, keyed: NH originals and HI woa files) or "masker" (not keyed); content_groups.json
              annotates targets.
              Masker key mapping: the scan holds ONE stream per masker, under its bare sha, at the masker's own origin, whatever
              its placements. C5's streams.json keys each placement '<sha>@<offset_s>' (build_public.py placed_key: the inventory
              masker offset in seconds, written as repr(float)); that stream is the same contract envelope m delayed onto the
              trial grid, y[n] = m(n - d) with d = offset_s x 64 samples (FRAC_RULE; d may be fractional). C6 maps a C5 masker
              row to the scan stream by its placement.masker_sha (= the key before '@'); a masker sample u of this scan (spans_a
              / spans_b, span) is sample u + d of that placed stream; every placement's source_sha256 equals the bare-sha
              stream's (one masker array). Maskers have no family and are never masked: they enter the cross-cohort flags
              (flagged_streams, donor_exclusions list the bare sha) and the report_only within records only.
  federici    c3_preproc_v1/federici_ci_children/{HC,CI,HC-v,Artifact}/*.h5 block `env` [blocks, 5000] at 100 Hz (only `env` is
              read); items deduplicated by federici_content.env_key, the key of kcs_targets_v1/content_groups.json (all asserted
              present); id = key, kind "item", keyed. condition = "vocoded" when every listener block is HC-v (or the phantom) and at
              least one is HC-v, else "natural".
Source hashes (meta.source_sha256; the M1 / M2b rule of tests/auditory_alignment_v3/prior33/fixtures.py 'Source hashes', which
build_public.py and build_sparrkulee.py follow): a SparrKULee envelope is a whole file, hashed as its bytes are read; a FAU / DTU h5
dataset or a Federici block row is an array inside a container, hashed by _sha_arr = fixtures.array_sha256: the sha256 of the
C-order float64 bytes of the flattened array as read, before nan_to_num (a float32 dataset is cast first, so the value depends on
the values only, not on the stored dtype, byte order or shape).
Completeness. On the real sources (main without --sources, i.e. run(require_all=True)) every cohort of COHORTS must be configured
and yield at least one keyed stream (a cohort holding only FAU distractors or DTU maskers adds no family and no donor content). A
cohort missing from the config (refused before anything is read) or without a keyed stream fails the run before any scan: exit 3,
scan_audio.FAILED.json with complete false, empty_cohorts, the failed COMPLETE_CHECK and an error naming the cohort ('not
configured' / 'yielded no keyed streams'); a complete run asserts `complete` (COMPLETE_CHECK). On either path a configured source
that cannot be read (a missing or unreadable file, a missing dataset or field: OSError, KeyError, ValueError, EOFError in a loader)
fails the run with exit 3 (the FAILED file holds complete false, source_error and an error naming the cohort); a data-use refusal
(RestrictedAccess) is never turned into a result: it propagates and nothing is written (any other exception, e.g. a code error or
an I/O error under --out, also propagates: exit 1, no FAILED file). A --sources run may scan a subset (complete false, not
asserted; cohorts_scanned names the scanned cohorts, and only those appear as donors).

Rules (64 Hz samples; design values, fixed):
  cross-cohort  every ordered pair of scanned cohorts: 10 s windows (640) on a 2 s hop (128) of every query stream against every
                position ("all lags") of every stream of the other cohort, normalised cross-correlation, flag r >= 0.7. Both
                directions are scanned. A flagged donor stream, with every member of its family, is removed from that target's
                donor set (donor_exclusions; donor_exclusions_direct lists the flags themselves).
  within        every cohort: 10 s windows on a 1 s hop (64) against every other stream of the cohort (different content ids =
                different stream ids), flag r >= 0.9. A keyed pair whose aligned overlap (union of 10 s windows with r >= 0.9 at the
                refined lag, 1 s grid) covers >= 50 % of the shorter stream is merged into one family at that lag. A shorter keyed
                overlap is masked: from the flagged windows, the span is extended over 2 s windows (128) sliding by 0.25 s (16) while
                r >= 0.8, then a 0.5 s (32) margin is added on each stream (clipped to the stream). Pairs with a non-keyed stream
                (FAU distractors, DTU maskers) are reported only.
  sparrkulee    declared audiobook_1 family: root audiobook_1, halves audiobook_1_1 / audiobook_1_2 asserted at +1711 / +30986 +- 1,
                the shifted-voice copies and the artefact excerpt measured against the root (global Pearson cross-correlation,
                peak r >= 0.9 asserted). Each shifted copy is asserted at its half's declared offset +- 1 (M2a declares it there)
                and on its half's measured clock +- 1. C6 takes the measured offsets (`families`), not the declared ones.
  federici      each content group of content_groups.json with >= 2 items is one family; the reference is its natural item with the
                most listener blocks; each partner's offset is the lag of the 2-8 Hz cross-correlation within +-2 s (128) when that
                peak r >= 0.5 and the global peak (overlap >= 50 % of the shorter item) lies within +-2 s; otherwise the family clock
                is "unknown" (the NCE mask then covers the whole partner item at any time).

Positive controls (assert; the window scan produces every §3.4 output, so it is checked on the run's own known duplicates):
  within        every relation the declared audiobook_1 structure implies (each measured member in the root at its measured
                offset; each shifted copy in its half at the difference of their measured offsets) must be a merge record of
                the within-cohort window scan (coverage >= 0.5, lag +- 1);
  cross         the declared members, as a pseudo cohort 'probe', against a bank holding only the root ('root'), in both
                directions through the production cross path (10 s windows, 2 s hop, r >= 0.7; run_units -> cross_candidates ->
                flag_overlaps): each member must be detected from both directions and flagged at its measured offset +- 1, with
                the r >= 0.7 windows covering >= 50 % of it.
  A run on the real sources fails when the controls could not run; an empty shared_audio['sparrkulee'] is a warning (the scout
  matched head / tail windows in 49 of the 72 files). Real two-stimulus dry runs (read-only, 2026-10-17): audiobook_1_1 at +1711;
  audiobook_1_1_shifted at +1712 (global r 0.968, merged at coverage 1.0, lowest 1 s-grid window r 0.913); audiobook_1_2_shifted
  at +30986 (global r 0.974, merged at coverage 1.0, lowest window r 0.940, cross control flagged from both directions).
Detection limit (design rule, unchanged): an exact shared segment of >= 11 s holds a whole 10 s window of the 1 s grid (>= 12 s on
the 2 s cross hop) and is always found; a shorter one only when a straddling window still reaches the threshold (review, exact
copies at random positions: 0/6 at <= 8.5 s, 4/6 at 9 s, 6/6 at 9.5 s). The M1 fixture's 3 s jingle is below the limit.

Sign convention. For an ordered pair (a, b), b_in_a = k means b[u] ~ a[u + k]: b's sample 0 sits at a's sample k, a's sample t is
b's sample t - k. Family offsets satisfy off_b = off_a + k; the family clock of a stream sample i is s = family_offset + i (§2.5).
Cross-cohort overlap records also carry lag = b.span[0] - a.span[0] = -b_in_a, the sign of manifest.overlap in the M1 fixture.
Spans are half-open [a, b) stream samples at 64 Hz, with *_s copies in seconds (§10: rate-independent reuse).

Output schema "prior33_scan_audio_v1" (sorted keys):
  schema, contract, created_utc, builder {module, sha256, contract_sha256, python, numpy, scipy, host, slurm_job}, signature,
  parameters, filters (contract.filter_shas()), sources {cohort: info}, cohorts_scanned, complete (every cohort of COHORTS
  yielded a keyed stream and was scanned; asserted on the real sources), ok, checks [{check, level (assert | warn), ok, detail}],
  streams {cohort: [{stream, kind, keyed, n, seconds, family, family_offset, offset_known, meta...}]},
  within {cohort: {stats, n_pairs, pairs [{a, b, a_kind, b_kind, keyed, b_in_a, b_in_a_s, k_range_detect, n_detect,
          r_detect_max, r_pooled (over the union of flagged windows), r_window_max (best 1 s-grid 10 s window at b_in_a),
          overlap_a, overlap_b, coverage, action (merge | mask | family_mask_covers | report_only | not_reproduced), edge_role
          (merges: tree | verified | check_only, + _conflict), spans_a, spans_b (+ _s), family_a, family_b, lag_drift,
          refined (false: the lag refinement found no candidate and the best hit's lag is used)}]}},
  families {cohort: [{name, root, basis, clock, members [{stream, offset, offset_s, offset_known, length}], edges [{a, b, b_in_a,
           source, weight, tree, check_only, residual}], conflicts, content_groups, crosses_content_groups, provisional_names}]}:
           name follows the C4 / C5 provisional family names ('sparrkulee:audiobook_1', 'fau:<code>', 'dtu:<sha>',
           'federici:g<content group>'; a merged family takes its root's name) and provisional_names lists every member's
           provisional name (a stream merged into the declared family keeps its own 'sparrkulee:<stim>': the declared members
           are SK_DECLARED's root and members, as build_sparrkulee.DECLARED_FAMILY), so C6 can re-map the provisional families
           onto the merged ones (PROVISIONAL_CHECK, assert level, the last check of scan(), new in the second M2c review: each
           provisional name lies in exactly one family),
  shared_audio {cohort: [{stream, span, span_s, partners [{stream, b_in_a}]}]} (per-stream unions of the mask spans),
  shared_audio_seconds {cohort: {masked_s, total_keyed_s, fraction, n_streams}},
  cross_cohort {stats [{query, bank, ...}], overlaps [{a {cohort, stream, stimulus, kind, keyed, span}, b {...}, b_in_a, lag
                (= -b_in_a), n_detect, r_detect_max, r_pooled, r_window_max, coverage, spans_a, spans_b, detected_from, refined}],
                flagged_streams {cohort: [ids]} (every record, refined or not), donor_exclusions {target: {donor: [stream ids]}}
                (family-propagated; scanned donor cohorts only, all of them on the real sources), donor_exclusions_direct (the
                directly flagged streams only), added_via_family, donor_exclusion_rule, not_scanned {private_bdf: reason}},
  sparrkulee_audiobook_1 {declared, measured {stream: {b_in_root, r, coverage}}, checks, ok},
  positive_controls {ran, ok, relations [{x, y, expected_b_in_a, basis}], within [{x, y, expected_b_in_a, basis, found, ok}],
                     cross {ran, bank, probes, windows, n_records, rows [{probe, expected_b_in_a, found, flagged, ok}]}},
  scene_pairs {fau: [{codes [X, Y], attended_X~distractor_Y, distractor_X~attended_Y, attention_swapped, same_scene}]},
  federici_natural_vocoded [{content_group, reference, partner, conditions, window {b_in_a, r}, global {b_in_a, r}, clock, offset}],
  assumptions [...], observations [...], summary {...}.
The manifest builder (C6, M2e) maps a presentation to its stream (SparrKULee stimulus file; FAU "<code>/attended", ignored stream
"<code>/distractor"; DTU target sha (HI: the woa sha), masker: the bare sha, i.e. the placement.masker_sha of C5's
'<sha>@<offset_s>' stream (Streams, dtu: masker key mapping); Federici item key), takes family / offset / clock from
`families` (the measured offsets: on the real data audiobook_1_1_shifted sits at +1712 where M2a declares 1711), removes every
listener segment whose EEG span meets a `shared_audio` span of its presentation's stream (every role), and, for target T, removes
donor presentations whose attended OR ignored stream is in donor_exclusions[T][donor] (any heard audio; stricter than the M1
fixture, which maps through the attended stream only; the two agree on the fixture because no planted overlap involves an
ignored stream). manifest.overlap takes `lag` (the fixture's sign), not b_in_a. Further C6 obligations:
  - read scan_audio.json only when scan_audio.latest.json says status ok with sha256 = sha256(scan_audio.json); refuse otherwise;
  - family_mask_covers overlaps (inside one family, on its clock) are not masked, because the family clock's NCE mask already
    covers them; this is leak-safe only while families stay role-disjoint (§3.2): a family split across roles must mask them
    (spans_a / spans_b of those within pairs);
  - a listed SparrKULee dev / bridge_cal stream makes the shared dev / bridge_cal definition (§3.2) target-specific: report it;
  - scene_pairs (FAU attention-swapped codes) are reported, not masked: a CSX decision for the lead.

Interpretations (also listed in the M2c summary): see INTERPRETATIONS below.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import hashlib
import heapq
import io
import json
import os
import platform
import re
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import scipy
import scipy.fft as sfft

from auditory_alignment_v3.prior33 import contract as C

SCHEMA = "prior33_scan_audio_v1"
COHORTS = ("sparrkulee", "fau", "dtu", "federici")
PUB = "/projects/EEG-foundation-model/auditory_public"
SK_ROOT_REAL = os.path.join(PUB, "sparrkulee_nm000238_v1.0.0")
CACHE_ROOT = os.path.join(PUB, "derived", C.CONTRACT)          # §6.2: …/derived/aln33_env64_125ms_v1
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_NAME, FAILED_NAME, WORK_NAME = "scan_audio.json", "scan_audio.FAILED.json", "scan_audio_work"
LATEST_NAME, LATEST_SCHEMA = "scan_audio.latest.json", "prior33_scan_audio_latest_v1"
EXIT_OK, EXIT_FAILED, EXIT_NOT_CURRENT = 0, 3, 4

# ------------------------------------------------------------------------------------------------ design rules (§2.5, §3.4)
WIN = 10 * C.FS                                  # 10 s windows
CROSS_HOP, CROSS_THR = 2 * C.FS, 0.7             # cross-cohort: 2 s hop, flag r >= 0.7
WITHIN_HOP, WITHIN_THR, MERGE_COVERAGE = C.FS, 0.9, 0.5      # within: 1 s hop, flag r >= 0.9, merge at >= 50 % of the shorter
EXT_WIN, EXT_STEP, EXT_THR, MARGIN = 2 * C.FS, C.FS // 4, 0.8, C.FS // 2   # mask extension 2 s / 0.25 s / r >= 0.8; 0.5 s margin
FED_MAX_LAG, FED_MIN_R = 2 * C.FS, 0.5           # Federici natural/vocoded lag within +-2 s, peak r >= 0.5
CLOCK_TOL = 1                                    # offsets asserted / family edges consistent to +-1 sample
DECLARED_MIN_R = 0.9                             # a declared audiobook_1 member must match the root at the within threshold
SK_DECLARED = {"family": "audiobook_1", "root": "audiobook_1",
               "offsets": {"audiobook_1_1": 1711, "audiobook_1_2": 30986},
               "variants": {"audiobook_1_1_shifted": "audiobook_1_1", "audiobook_1_2_shifted": "audiobook_1_2"},
               "excerpts": ("audiobook_1_artefact",)}
DONOR_SETS = {"fau": ("sparrkulee", "dtu", "federici"), "dtu": ("sparrkulee", "fau", "federici"),
              "federici": ("sparrkulee", "fau", "dtu"), "private_bdf": ("sparrkulee", "fau", "dtu", "federici")}   # §3.1
COMPLETE_CHECK = "complete: every cohort of COHORTS configured, yielding a keyed stream and scanned (real sources)"
PROVISIONAL_CHECK = "every provisional family name lies in exactly one family (C6 re-maps the C4 / C5 families by it)"
SOURCE_ERRORS = (OSError, KeyError, ValueError, EOFError)   # a loader's missing / unreadable / malformed source: exit 3, not a traceback
SK_EXPECTED_ENVELOPES = 72
RESTRICTED_SPARRKULEE = ("sub-019", "sub-020", "sub-021", "sub-022", "sub-026")
_RESTRICTED_RE = re.compile(r"^sub-(019|020|021|022|026)(?![0-9])")
NEVER_OPEN_SUFFIXES = (".data_dict", ".pkl", ".pickle")

# ------------------------------------------------------------------------------------------------ implementation constants (ours)
VAR_FLOOR = 1e-3        # a window whose variance is below 1e-3 of the stream's mean power (RMS 1) is silent: never matched
RUN_GAP = 8             # bank positions above threshold closer than this belong to one peak (one hit per peak)
LAG_GAP = 4             # hits of a pair whose lags differ by <= 4 samples form one lag cluster
REFINE_PAD = 2          # the refined lag maximises the pooled r over the cluster's windows within its lag range +- 2
REFINE_MAX_SPAN = 64    # a cluster wider than this (drift) is refined around the lag of its best hit only
MIN_OVERLAP_FRAC = 0.5  # global cross-correlations (declared / Federici) consider lags whose overlap >= 50 % of the shorter
NFFT = 16384            # overlap-save block size of the window scan
UNIT_SAMPLES = 1 << 18  # resumable unit: query streams up to ~68 min of audio

INTERPRETATIONS = (
    "Streams are the contract envelope chain (§2.3) on the sources the loaders read; RMS normalisation cannot change any r.",
    "Content id = stream id in every cohort (SparrKULee file, FAU code stream, DTU sha, Federici item): the shifted-voice copies, "
    "the artefact excerpt and the DTU HI woa copies are scanned against their counterparts like any other stream.",
    "Cross-cohort scans run in both directions; within-cohort scans query every stream against all other streams of the cohort.",
    "Cross-cohort scans include non-keyed streams (FAU distractors, DTU maskers): any heard audio counts for leakage.",
    "Within-cohort merges and masks apply to keyed pairs only; pairs with a non-keyed stream are reported (report_only).",
    "Window r is the Pearson correlation of the two 10 s windows (local means and SDs); windows below VAR_FLOOR never match.",
    "The merge coverage is the union of 1 s-grid 10 s windows with r >= 0.9 at the refined lag over the shorter stream's length.",
    "The mask seed is the flagged 10 s windows plus the 1 s-grid windows with r >= 0.9 at the refined lag; extension steps of "
    "0.25 s stop at the first 2 s window with r < 0.8; the margin is clipped to each stream.",
    "A non-merge overlap inside one family is not masked when the family clock is unknown or the overlap lag agrees with the "
    "family offsets within the NCE neighbour mask (+-128, inclusive): the family-clock mask already removes those negatives. "
    "This departs from the literal 'shorter overlaps are masked' (e.g. where the artefact excerpt meets a half below 50 % "
    "coverage, its segments stay available to the artefact probe) and is leak-safe only while families stay role-disjoint "
    "(§3.2), which C6 must keep.",
    "Masks are seeded with the whole flagged 10 s windows, so a span can reach up to ~1.9 s past the shared audio on each side "
    "before the 0.5 s margin (conservative; the design extends, it never trims).",
    "Families: weighted union-find with a spanning tree from the root (declared / natural-vocoded edges first, then scan merges "
    "by coverage); every other edge must agree to +-1 sample, else the family clock is unknown (clock_conflict); offsets are "
    "shifted so that the smallest known offset is 0 (keys need s >= 0) and offset + length < 2**24 is asserted.",
    "SparrKULee declared family: halves asserted (design values); shifted copies and the artefact must match the root at r >= "
    "0.9 and their offsets are measured. §2.5 'asserts them to +-1 sample' is read as covering the shifted copies, which M2a "
    "declares at their halves' offsets: each copy is asserted at its half's declared offset +- 1 and on its half's measured "
    "clock +- 1. C6 takes the measured offsets.",
    "Positive controls (assert): the within-cohort window scan must merge every declared audiobook_1 relation at its measured "
    "lag +- 1 (coverage >= 0.5), and the cross path (2 s hop, r >= 0.7) must detect and flag every declared member against a "
    "bank holding only the root, from both directions; a run on the real sources fails when they could not run. Without them a "
    "broken or insensitive window scan would pass silently with 0 merges, masks and overlaps.",
    "Every cross-cohort record flags both streams, whatever its action; a detection whose lag refinement finds no candidate "
    "(not expected: the best hit's own lag always qualifies) keeps the best hit's lag (refined false, warning) and is merged, "
    "masked or flagged at it.",
    "donor_exclusions is family-propagated: every member of a donor family that holds a flagged stream ('content item' of §3.4 "
    "read as the content family; conservative); donor_exclusions_direct lists the directly flagged streams.",
    "FAU attention-swapped codes (X attended = Y distractor and X distractor = Y attended) are listed in scene_pairs and not "
    "masked: the design requires no mask (a presentation includes its attended stream; OBJECTIVES §2 allows, but does not "
    "require, masking same-content ambiguous negatives); for CSX this is a decision for the lead.",
    "Detection limit of the fixed rule: exact shared audio of >= 11 s (within, 1 s hop) or >= 12 s (cross, 2 s hop) is always "
    "found; shorter audio only when a straddling 10 s window reaches the threshold.",
    "Federici: 'lag within +-2 s' is the peak of the full-overlap Pearson cross-correlation within |k| <= 128; 'outside +-2 s' "
    "is the global peak over lags with >= 50 % overlap lying outside; the reference is the natural item.",
    "duplicate_scan edges between two members of one declared group (the SparrKULee audiobook_1 family, one Federici content "
    "group) are check-only: they verify the declared / +-2 s clock (residual) but never set it, so a natural / vocoded pair that "
    "is duplicated at a lag beyond +-2 s keeps the unknown clock of the Federici rule.",
    "Family names are the C4 / C5 provisional names ('sparrkulee:audiobook_1', 'fau:<code>', 'dtu:<sha>', 'federici:g<group>'); "
    "a merged family takes its root's name and lists every member's provisional name: only the streams SK_DECLARED names (as "
    "build_sparrkulee.DECLARED_FAMILY) carry 'sparrkulee:audiobook_1', a stream merged into that family keeps its own "
    "'sparrkulee:<stim>', and each provisional name must lie in exactly one family (PROVISIONAL_CHECK, an assert-level check new "
    "in the second M2c review, appended after every other check of scan() so the earlier checks keep their positions; under "
    "these naming rules it can fail only together with a declared-member assertion, since Federici group items are joined by "
    "natural_vocoded edges and FAU / DTU names are one per stream); stream kinds follow the same tables ('attended' for keyed "
    "SparrKULee / FAU / DTU streams, 'distractor', 'masker', 'item').",
    "source_sha256 follows the M1 / M2b rule (fixtures.py 'Source hashes'; build_public.py, build_sparrkulee.py): the file sha256 "
    "for a SparrKULee envelope file, the sha256 of the C-order float64 bytes of the array as read (before nan_to_num) for a FAU / "
    "DTU h5 dataset and a Federici block row, so that C6 compares C3, C4 and C5 hashes like with like.",
    "DTU maskers are scanned once under the bare sha at their own origin; C5 keys each placement '<sha>@<offset_s>' (the same "
    "envelope delayed by offset_s x 64 samples): C6 maps C5's masker rows to the scan by placement.masker_sha.",
    "Assertions that fail the job (exit 3, scan_audio.FAILED.json): on the real sources every cohort configured and yielding at "
    "least one keyed stream (complete; a cohort that is not configured or has no keyed stream, e.g. DTU maskers only, fails "
    "before the scan, named in the error), every configured source readable (a loader's OSError / KeyError / ValueError / "
    "EOFError fails the run naming the cohort; a RestrictedAccess refusal propagates instead), the 72 SparrKULee envelopes, "
    "DTU inventory shas present in audio_local.h5, every Federici item in content_groups.json, the declared audiobook_1 members "
    "(r >= 0.9), the two half offsets and the shifted copies' offsets, the positive controls, every non-silent query window "
    "scored, each provisional family name in exactly one family, the 2**24 key budget. Clock conflicts, families that cross "
    "content groups, unrefined detections, an empty SparrKULee shared audio and a flagged SparrKULee stream are warnings.",
    "scan_audio.latest.json names the latest run's result; superseded / stale results stay in place (nothing is moved or "
    "deleted); without --force an existing scan_audio.json is reused only when the pointer says ok for it and its builder "
    "sha256 is this file's, else exit 4.",
    "The scan work units stay under scan_audio_work/<signature16>/ after success (no deletion; a few MB).",
    "Private stimuli are not scanned: design §3.4 scans the four public cohorts, and auditory_alignment/data.py load_private "
    "yields trial epochs and class labels, no stimulus stream. donor_exclusions['private_bdf'] is therefore empty because "
    "nothing was scanned, not because no overlap was found; the inherited contract (PUBLIC_PRIOR_EXECUTION_v3_3 §2, "
    "public_prior_v3_3.yaml donor_policy) asks for that exclusion, so it is an unverified assumption (assumptions, "
    "cross_cohort.not_scanned) for the execution record.",
)
PRIVATE_NOT_SCANNED = ("not scanned: the private task stimuli are outside C3 (design §3.4 scans the four public cohorts; "
                       "auditory_alignment/data.py load_private yields trial epochs and class labels, no stimulus stream). The "
                       "inherited contract excludes donor content that overlaps the target's test stimuli (PUBLIC_PRIOR_EXECUTION_"
                       "v3_3 §2; public_prior_v3_3.yaml donor_policy): for private_bdf this is an unverified assumption (short "
                       "event-locked task sounds, not taken from the public speech corpora), to be stated in the execution record")


class ScanError(RuntimeError):
    """A source or rule assertion failed, or a configured source could not be read; the scan writes scan_audio.FAILED.json and
    exits 3. `detail` (a dict, e.g. complete / empty_cohorts / source_error) is merged into that file."""

    def __init__(self, msg, detail=None):
        super().__init__(msg)
        self.detail = dict(detail or {})


class RestrictedAccess(PermissionError):
    """A read that the data-use rules forbid (restricted SparrKULee participant, pickled file)."""


# ------------------------------------------------------------------------------------------------ guarded reads
READ_LOG: list = []                  # every path this module opened (tests inspect it; h5py opens bypass Python audit hooks)
_SK_ROOTS = {os.path.realpath(SK_ROOT_REAL)}


def register_sk_root(root):
    """Every SparrKULee root a source config names is guarded like the real one."""
    _SK_ROOTS.add(os.path.realpath(os.fspath(root)))


def guard_path(path):
    """Refuse pickled files anywhere and any path of a restricted SparrKULee participant under a SparrKULee root (a directory or
    file name starting with sub-019/020/021/022/026); returns the real path. Called before every open, listing and glob."""
    p = os.path.realpath(os.fspath(path))
    if p.lower().endswith(NEVER_OPEN_SUFFIXES):
        raise RestrictedAccess(f"scan_audio never opens pickled files: {p}")
    for root in _SK_ROOTS:
        if p == root or p.startswith(root + os.sep):
            for part in os.path.relpath(p, root).split(os.sep):
                if _RESTRICTED_RE.match(part):
                    raise RestrictedAccess(f"restricted SparrKULee participant path refused: {p}")
    return p


def read_npy(path):
    """(array, sha256 of the file bytes): np.load(allow_pickle=False) on the bytes read through the guard."""
    p = guard_path(path)
    READ_LOG.append(p)
    with open(p, "rb") as f:
        raw = f.read()
    return np.load(io.BytesIO(raw), allow_pickle=False), hashlib.sha256(raw).hexdigest()


def read_json(path):
    p = guard_path(path)
    READ_LOG.append(p)
    with open(p) as f:
        return json.load(f)


def open_h5(path):
    import h5py
    p = guard_path(path)
    READ_LOG.append(p)
    return h5py.File(p, "r")


def list_dir(path):
    return sorted(os.listdir(guard_path(path)))


def _glob(pattern):
    return sorted(guard_path(p) for p in glob.glob(pattern))


def _sha_arr(a):
    """source_sha256 of an array inside a container file (FAU / DTU h5 datasets, a Federici block row): the M1 / M2b rule
    (fixtures.array_sha256, build_public.py), the sha256 of the C-order float64 bytes of the flattened array as read, before
    nan_to_num; any stored dtype, byte order or shape is cast first, so the value depends on the values only."""
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a, dtype=np.float64).reshape(-1)).tobytes()).hexdigest()


def _file_sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ------------------------------------------------------------------------------------------------ streams
@dataclass
class Stream:
    cohort: str
    sid: str
    kind: str
    keyed: bool
    x: np.ndarray                    # 64 Hz, 2-8 Hz, RMS 1, float64, at the stream's own origin
    meta: dict = field(default_factory=dict)


def prepare(raw, fs):
    """Contract chain of §2.3 -> (env_n float64, RMS of the band-passed stream), or (None, 0.0) for a silent stream."""
    x = np.asarray(raw, dtype=np.float64).reshape(-1)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    if x.size < 2 or not np.any(x):
        return None, 0.0
    y = C.band(C.resample64(x, int(fs)), C.env_sos()[0])
    try:
        yn, rms = C.rms_norm(y, return_rms=True)
    except ValueError:
        return None, 0.0
    return yn, float(rms)


def _attr(v):
    if isinstance(v, bytes):
        return v.decode(errors="replace")
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def _chk(check, ok, detail=None, level="assert"):
    return {"check": check, "level": level, "ok": bool(ok), "detail": detail}


def load_sparrkulee(cfg):
    root = cfg["root"]
    register_sk_root(root)
    d = os.path.join(root, cfg.get("envelopes", os.path.join("derivatives", "preprocessed_stimuli")))
    names = list_dir(d)
    env = [f for f in names if f.endswith("_envelope.npy")]
    ignored = [f for f in names if f.endswith(".npy") and not f.endswith("_envelope.npy")]
    exp = cfg.get("expected_n")
    checks = [_chk("sparrkulee envelope files", exp is None or len(env) == exp, {"n": len(env), "expected": exp})]
    fs = int(cfg.get("fs", C.FS))
    streams, skipped = [], []
    for f in env:
        sid = f[:-len("_envelope.npy")]
        arr, sha = read_npy(os.path.join(d, f))
        if arr.dtype.kind != "f" or not (arr.ndim == 1 or (arr.ndim == 2 and 1 in arr.shape)):
            raise ScanError(f"sparrkulee {f}: numeric (T,) or (T, 1) envelope expected, got {arr.dtype} {arr.shape}")
        raw = arr.reshape(-1)
        nonfinite = int((~np.isfinite(raw)).sum())
        x, rms = prepare(raw, fs)
        meta = {"source": {"file": os.path.join(d, f)}, "source_sha256": sha, "fs_source": fs, "n_source": int(raw.size),
                "shape": list(arr.shape), "dtype": str(arr.dtype), "nonfinite": nonfinite, "rms_band": rms}
        if x is None:
            skipped.append({"stream": sid, "reason": "silent", **meta})
            continue
        streams.append(Stream("sparrkulee", sid, "attended", True, x, meta))
    return streams, {"root": root, "dir": d, "n_files": len(env), "ignored": ignored, "skipped": skipped, "checks": checks}


def load_fau(cfg):
    fs, path = int(cfg.get("fs", 128)), cfg["file"]
    streams, skipped, obs = [], [], []
    with open_h5(path) as f:
        attrs = {k: _attr(v) for k, v in f.attrs.items()}
        for code in sorted(f.keys()):
            for which in ("attended", "distractor"):
                key = f"{code}/{which}_env/raw"
                if key not in f:
                    continue
                raw = np.asarray(f[key][()])
                nan = int(np.isnan(raw).sum()) if raw.dtype.kind == "f" else 0
                x, rms = prepare(raw, fs)
                cond = {"1": "single", "2": "competing"}.get(code[:1], "unknown")
                meta = {"source": {"file": path, "dataset": key}, "source_sha256": _sha_arr(raw), "fs_source": fs, "n_source": int(raw.size),
                        "dtype": str(raw.dtype), "nan_count": nan, "rms_band": rms, "code": code, "condition": cond,
                        "attended_story": code[1:2], "part": code[2:3]}
                sid = f"{code}/{which}"
                if x is None:
                    skipped.append({"stream": sid, "reason": "silent (all NaN or zero)", "nan_count": nan, "n_source": int(raw.size)})
                    continue
                if which == "distractor" and cond == "single":
                    obs.append(f"fau {sid}: single-talker code with a non-silent distractor stream ({nan} NaN of {raw.size})")
                streams.append(Stream("fau", sid, which, which == "attended", x, meta))
    return streams, {"file": path, "attrs": attrs, "skipped": skipped, "observations": obs, "checks": []}


def load_dtu(cfg):
    inv = read_json(cfg["inventory"])
    cg = read_json(cfg["content_groups"]).get("content", {})
    per = {}
    for r in inv:
        sha = r.get("sha")
        if not sha:
            continue
        e = per.setdefault(sha, {"kinds": set(), "by_hearing": collections.Counter(), "trials": 0, "listeners": set()})
        e["kinds"].add(r["kind"]); e["by_hearing"]["hi" if r.get("hi") else "nh"] += 1; e["trials"] += 1; e["listeners"].add(r.get("file"))
    fs = int(cfg.get("fs", 128))
    streams, skipped, checks = [], [], []
    both = sorted(s for s, e in per.items() if len(e["kinds"]) > 1)
    with open_h5(cfg["audio"]) as f:
        missing = sorted(s for s in per if s not in f)
        checks.append(_chk("dtu inventory shas present in audio_local.h5", not missing, {"missing": missing[:20], "n_missing": len(missing)}))
        for sha in sorted(per):
            if sha in missing:
                continue
            e = per[sha]
            raw = np.asarray(f[sha]["env"][()])
            x, rms = prepare(raw, fs)
            keyed = "target" in e["kinds"]
            meta = {"source": {"file": cfg["audio"], "dataset": f"{sha}/env"}, "source_sha256": _sha_arr(raw), "fs_source": fs,
                    "n_source": int(raw.size), "dtype": str(raw.dtype), "rms_band": rms, "kinds": sorted(e["kinds"]),
                    "n_trials": e["trials"], "n_listeners": len(e["listeners"]), "trials_by_hearing": dict(sorted(e["by_hearing"].items())),
                    "content_group": cg.get(sha, {}).get("group"), "content_half": cg.get(sha, {}).get("half"),
                    "content_early_stop": cg.get(sha, {}).get("early_stop")}
            if x is None:
                skipped.append({"stream": sha, "reason": "silent", "n_source": int(raw.size)})
                continue
            streams.append(Stream("dtu", sha, "attended" if keyed else "masker", keyed, x, meta))
    return streams, {"audio": cfg["audio"], "inventory": cfg["inventory"], "content_groups": cfg["content_groups"], "n_inventory_rows": len(inv),
                     "n_shas": len(per), "shas_target_and_masker": both, "skipped": skipped, "checks": checks}


def load_federici(cfg):
    from auditory_alignment.federici_content import env_key
    cgj = read_json(cfg["content_groups"])
    items_cg = {it["key"]: it for it in cgj.get("items", [])}
    fs = int(cfg.get("fs", 100))
    items, files = {}, 0
    for grp in cfg.get("groups", ("HC", "CI", "HC-v", "Artifact")):
        for p in _glob(os.path.join(cfg["pre"], grp, "*.h5")):
            files += 1
            with open_h5(p) as f:
                env = np.atleast_2d(np.asarray(f["env"][()], dtype=np.float64))
            for b, e in enumerate(env):
                h = env_key(((e - e.mean()) / (e.std() + 1e-12)).astype(np.float32))
                it = items.get(h)
                if it is None:
                    it = items[h] = {"raw": e.copy(), "first": f"{grp}/{os.path.basename(p)}#{b}", "groups": collections.Counter(), "n": 0}
                it["groups"][grp] += 1
                it["n"] += 1
    missing = sorted(h for h in items if h not in items_cg)
    checks = [_chk("federici items present in content_groups.json", not missing, {"missing": missing[:20], "n_missing": len(missing)})]
    streams, skipped = [], []
    for h in sorted(items):
        it = items[h]
        gs = set(it["groups"])
        cond = "vocoded" if ("HC-v" in gs and gs <= {"HC-v", "Artifact"}) else "natural"
        x, rms = prepare(it["raw"], fs)
        cgi = items_cg.get(h, {})
        meta = {"source": {"first": it["first"], "dataset": "env"}, "source_sha256": _sha_arr(it["raw"]), "fs_source": fs,
                "n_source": int(it["raw"].size), "rms_band": rms, "n_listeners": it["n"], "listener_groups": dict(sorted(it["groups"].items())),
                "condition": cond, "content_group": cgi.get("group"), "content_role": cgi.get("role")}
        if x is None:
            skipped.append({"stream": h, "reason": "silent", "first": it["first"]})
            continue
        streams.append(Stream("federici", h, "item", True, x, meta))
    return streams, {"pre": cfg["pre"], "content_groups": cfg["content_groups"], "n_files": files, "n_items": len(items),
                     "n_content_group_items": len(items_cg), "skipped": skipped, "checks": checks}


LOADERS = {"sparrkulee": load_sparrkulee, "fau": load_fau, "dtu": load_dtu, "federici": load_federici}


def default_sources():
    """The real sources: where auditory_alignment/data.py, prep_targets.py and federici_content.py read them (§2.3)."""
    from auditory_alignment import data as D, prep_targets as PT
    from auditory_alignment.federici_content import OUT as FED_KCS
    return {"sparrkulee": {"root": SK_ROOT_REAL, "envelopes": os.path.join("derivatives", "preprocessed_stimuli"), "fs": C.FS,
                           "expected_n": SK_EXPECTED_ENVELOPES},
            "fau": {"file": PT.FAU_ENV, "fs": 128},
            "dtu": {"audio": os.path.join(D.DTU_KCS, "audio_local.h5"), "inventory": os.path.join(PT.DTU_FEAT, "inventory.json"),
                    "content_groups": os.path.join(D.DTU_KCS, "content_groups.json"), "fs": 128},
            "federici": {"pre": D.FED_PRE, "groups": ["HC", "CI", "HC-v", "Artifact"], "content_groups": os.path.join(FED_KCS, "content_groups.json"),
                         "fs": 100}}


def load_sources(cfg, require_all=False):
    """{cohort: [Stream]} sorted by stream id, and {cohort: info}. The config is validated and the SparrKULee root registered
    before anything is read; with require_all a cohort missing from the config is refused there as incomplete sources
    (incomplete_error: complete false, empty_cohorts, the failed COMPLETE_CHECK). A loader's SOURCE_ERRORS (a missing or unreadable
    file, a missing dataset or field) become a ScanError naming the cohort (exit 3, scan_audio.FAILED.json with source_error); a
    RestrictedAccess refusal propagates unchanged."""
    missing, unknown = [c for c in COHORTS if c not in cfg], sorted(set(cfg) - set(COHORTS))
    if unknown or (require_all and missing):
        msg = f"source config: missing cohorts {missing}, unknown keys {unknown}"
        if require_all and missing:
            raise incomplete_error({c: {"configured": False} for c in missing}, note=msg)
        raise ScanError(msg)
    if "sparrkulee" in cfg:
        register_sk_root(cfg["sparrkulee"]["root"])
    streams, info = {}, {}
    for c in COHORTS:
        if c not in cfg:
            continue
        try:
            s, i = LOADERS[c](cfg[c])
        except RestrictedAccess:
            raise                                  # a data-use refusal is never turned into a result file
        except SOURCE_ERRORS as exc:
            raise ScanError(f"source {c}: cannot read the configured source ({type(exc).__name__}: {exc})",
                            detail={"complete": False, "source_error": {"cohort": c, "type": type(exc).__name__,
                                                                        "error": str(exc)[:2000], "config": cfg[c]}}) from exc
        streams[c] = sorted(s, key=lambda z: z.sid)
        info[c] = i
    return streams, info


# ------------------------------------------------------------------------------------------------ interval helpers
def _union(iv):
    out = []
    for a, b in sorted((int(a), int(b)) for a, b in iv if b > a):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _length(iv):
    return int(sum(b - a for a, b in iv))


def _clip(iv, lo, hi):
    return [[max(int(a), lo), min(int(b), hi)] for a, b in iv if min(int(b), hi) > max(int(a), lo)]


def _cum0(v):
    out = np.empty(len(v) + 1)
    out[0] = 0.0
    np.cumsum(v, out=out[1:])
    return out


def _secs(iv):
    return [[round(a / C.FS, 4), round(b / C.FS, 4)] for a, b in iv]


# ------------------------------------------------------------------------------------------------ window scan (overlap-save)
class Bank:
    """The streams of one cohort concatenated; positions u are the starts of 10 s windows inside one stream. inv[u] = 1 / (WIN
    sd(u)) for valid windows (0 for silent or boundary-crossing ones); FB the rfft of the overlap-save blocks (float32)."""

    def __init__(self, streams, nfft=NFFT, workers=1):
        self.streams = list(streams)
        self.lens = np.array([len(s.x) for s in self.streams], np.int64)
        self.starts = np.concatenate([[0], np.cumsum(self.lens)[:-1]]).astype(np.int64) if len(self.lens) else np.zeros(0, np.int64)
        N = int(self.lens.sum())
        self.n_pos = max(0, N - WIN + 1)
        X = np.concatenate([s.x for s in self.streams]) if self.streams else np.zeros(0)
        self.sid = np.full(self.n_pos, -1, np.int32)
        for j, (st, L) in enumerate(zip(self.starts, self.lens)):
            if L >= WIN:
                self.sid[st:st + L - WIN + 1] = j
        self.inv = np.zeros(self.n_pos, np.float32)
        self.n_valid = 0
        if self.n_pos:
            c1, c2 = _cum0(X), _cum0(X * X)
            var = (c2[WIN:] - c2[:-WIN]) / WIN - ((c1[WIN:] - c1[:-WIN]) / WIN) ** 2
            ok = (self.sid >= 0) & (var > VAR_FLOOR)
            self.inv[ok] = (1.0 / (WIN * np.sqrt(var[ok]))).astype(np.float32)
            self.n_valid = int(ok.sum())
        self.nfft = int(min(int(nfft), 1 << int(np.ceil(np.log2(max(N, 2 * WIN))))))
        self.step = self.nfft - WIN + 1
        self.nb = max(1, -(-self.n_pos // self.step))
        self.inv_b = np.zeros(self.nb * self.step, np.float32)       # inv in the block layout [nb, step] (0 past n_pos)
        self.inv_b[:self.n_pos] = self.inv
        self.inv_b = self.inv_b.reshape(self.nb, self.step)
        Xp = np.zeros(self.nb * self.step + WIN - 1, np.float32)
        Xp[:N] = X
        blocks = np.lib.stride_tricks.as_strided(Xp, shape=(self.nb, self.nfft), strides=(self.step * Xp.itemsize, Xp.itemsize))
        self.FB = sfft.rfft(blocks, axis=1, workers=workers)

    def per_query_bytes(self):
        return 3 * self.nb * self.nfft * 4


_DTS = {"t": np.int64, "b": np.int32, "u": np.int64, "r": np.float32, "wt": np.int64, "wr": np.float32, "wb": np.int32, "wu": np.int64}


def _empty_hits():
    return {"q": np.zeros(0, np.int32), "wq": np.zeros(0, np.int32), **{k: np.zeros(0, dt) for k, dt in _DTS.items()}}


def detect_stream(x, bank, hop, thr, self_j=None, workers=1, nq_max=8):
    """Windows [t, t + 640) of x on a `hop` grid from sample 0 against every valid bank position: hits (one per peak: positions
    with r >= thr closer than RUN_GAP form one peak) and, per window, the best r over the bank. self_j excludes that bank stream
    (within-cohort). Returns (dict of arrays without the q column, n_windows, n_silent)."""
    out = {k: [] for k in _DTS}
    T = np.arange(0, len(x) - WIN + 1, hop, dtype=np.int64)
    n_win = len(T)
    if n_win == 0 or bank.n_pos == 0:
        return {k: np.zeros(0, dt) for k, dt in _DTS.items()}, n_win, 0
    Q = np.lib.stride_tricks.sliding_window_view(np.asarray(x, np.float64), WIN)[T]
    mu, var = Q.mean(1), Q.var(1)
    ok = var > VAR_FLOOR
    n_silent = int((~ok).sum())
    T = T[ok]
    Qz = ((Q[ok] - mu[ok, None]) / np.sqrt(var[ok])[:, None]).astype(np.float32)
    lo = hi = None
    if self_j is not None:
        lo = int(bank.starts[self_j]); hi = min(bank.n_pos, lo + int(bank.lens[self_j]))
    for b0 in range(0, len(T), nq_max):
        q = Qz[b0:b0 + nq_max]
        nq = len(q)
        FQ = np.conj(sfft.rfft(q, bank.nfft, axis=1, workers=workers))
        prod = bank.FB[None, :, :] * FQ[:, None, :]
        num = sfft.irfft(prod, bank.nfft, axis=2, workers=workers)
        del prod
        r = np.multiply(num[:, :, :bank.step], bank.inv_b[None]).reshape(nq, -1)    # contiguous [nq, nb * step]; 0 past n_pos
        del num
        if lo is not None and hi > lo:
            r[:, lo:hi] = 0.0
        jm = r.argmax(1)
        rm = r[np.arange(nq), jm]
        bm = np.where(jm < bank.n_pos, bank.sid[np.minimum(jm, bank.n_pos - 1)], -1)
        out["wt"].append(T[b0:b0 + nq]); out["wr"].append(rm.astype(np.float32)); out["wb"].append(bm.astype(np.int32))
        out["wu"].append(np.where(bm >= 0, jm - bank.starts[np.maximum(bm, 0)], -1).astype(np.int64))
        qq, uu = np.nonzero(r >= thr)
        if len(qq):
            rv = r[qq, uu]
            bb = bank.sid[uu]
            brk = np.ones(len(qq), bool)
            brk[1:] = (qq[1:] != qq[:-1]) | (uu[1:] - uu[:-1] > RUN_GAP) | (bb[1:] != bb[:-1])
            run = np.cumsum(brk) - 1
            order = np.lexsort((-rv, run))
            first = np.ones(len(order), bool)
            first[1:] = run[order][1:] != run[order][:-1]
            sel = order[first]
            out["t"].append(T[b0 + qq[sel]]); out["b"].append(bb[sel].astype(np.int32))
            out["u"].append((uu[sel] - bank.starts[bb[sel]]).astype(np.int64)); out["r"].append(rv[sel].astype(np.float32))
        del r
    return {k: (np.concatenate(v).astype(_DTS[k]) if v else np.zeros(0, _DTS[k])) for k, v in out.items()}, n_win, n_silent


def _chunks(streams, limit=UNIT_SAMPLES):
    units, cur, n = [], [], 0
    for i, s in enumerate(streams):
        if cur and n + len(s.x) > limit:
            units.append(cur); cur, n = [], 0
        cur.append(i); n += len(s.x)
    if cur:
        units.append(cur)
    return units


def _save_unit(path, spec, d):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        np.savez(f, spec=np.array(json.dumps(spec, sort_keys=True)), **d)
    os.replace(tmp, path)


def _load_unit(path, spec):
    try:
        with np.load(path, allow_pickle=False) as z:
            if json.loads(str(z["spec"])) != json.loads(json.dumps(spec, sort_keys=True)):
                return None
            return {k: z[k] for k in z.files if k != "spec"}
    except Exception:          # a truncated or foreign file is recomputed
        return None


def run_units(kind, qc, bc, qstreams, bank, hop, thr, work_dir=None, workers=1, batch_bytes=256 << 20, log=None):
    """All query streams of cohort qc against the bank of cohort bc, unit by unit (resumable). Returns concatenated arrays
    (q = query stream index) and the window counts."""
    nq_max = int(max(1, batch_bytes // max(1, bank.per_query_bytes())))
    parts, n_win, n_sil = [], 0, 0
    units = _chunks(qstreams)
    for ui, idxs in enumerate(units):
        spec = {"kind": kind, "query": qc, "bank": bc, "unit": ui, "streams": [qstreams[i].sid for i in idxs], "hop": hop, "thr": thr}
        path = os.path.join(work_dir, f"{kind}__{qc}__{bc}__{ui:04d}.npz") if work_dir else None
        d = _load_unit(path, spec) if path and os.path.exists(path) else None
        if d is None:
            t0 = time.time()
            acc = []
            counts = np.zeros(2, np.int64)
            for i in idxs:
                h, nw, ns = detect_stream(qstreams[i].x, bank, hop, thr, i if kind == "within" else None, workers, nq_max)
                h["q"] = np.full(len(h["t"]), i, np.int32); h["wq"] = np.full(len(h["wt"]), i, np.int32)
                acc.append(h); counts += (nw, ns)
            d = {k: np.concatenate([a[k] for a in acc]) for k in acc[0]}
            d["counts"] = counts
            if path:
                _save_unit(path, spec, d)
            if log:
                log(f"[scan_audio] {kind} {qc}->{bc} unit {ui + 1}/{len(units)}: {len(idxs)} streams, {int(counts[0])} windows, "
                    f"{len(d['t'])} hits, {time.time() - t0:.1f} s")
        parts.append(d)
        n_win += int(d["counts"][0]); n_sil += int(d["counts"][1])
    if not parts:
        return _empty_hits(), 0, 0
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0] if k != "counts"}, n_win, n_sil


# ------------------------------------------------------------------------------------------------ alignment and refinement
class Aligned:
    """a and b aligned at b_in_a = k (b[u] ~ a[u + k]); a-coordinates [ov0, ov1); prefix sums for window statistics."""

    def __init__(self, a, b, k):
        self.k = int(k)
        self.La, self.Lb = len(a), len(b)
        self.ov0, self.ov1 = max(0, self.k), min(self.La, self.Lb + self.k)
        self.n = max(0, self.ov1 - self.ov0)
        if self.n:
            A, B = a[self.ov0:self.ov1], b[self.ov0 - self.k:self.ov1 - self.k]
            self._c = (_cum0(A), _cum0(B), _cum0(A * A), _cum0(B * B), _cum0(A * B))

    def _stats(self, s, e):
        cA, cB, cAA, cBB, cAB = self._c
        n = (e - s).astype(np.float64)
        SA, SB = cA[e] - cA[s], cB[e] - cB[s]
        return n, SA, SB, cAA[e] - cAA[s], cBB[e] - cBB[s], cAB[e] - cAB[s]

    @staticmethod
    def _r(n, SA, SB, SAA, SBB, SAB):
        va, vb = SAA / n - (SA / n) ** 2, SBB / n - (SB / n) ** 2
        cov = SAB / n - SA * SB / n ** 2
        with np.errstate(invalid="ignore", divide="ignore"):
            r = cov / np.sqrt(va * vb)
        return np.where((va > VAR_FLOOR) & (vb > VAR_FLOOR), r, np.nan)

    def r(self, s, e):
        """Pearson r of a[s:e] and b[s - k:e - k] (a-coordinates inside the overlap); NaN for a silent window."""
        s = np.asarray(s, np.int64) - self.ov0
        e = np.asarray(e, np.int64) - self.ov0
        return self._r(*self._stats(s, e))

    def pooled(self, iv):
        """Pearson r over the union of a-intervals clipped to the overlap, and its length."""
        iv = _clip(iv, self.ov0, self.ov1)
        if not iv or not self.n:
            return np.nan, 0
        s = np.array([a for a, _ in iv], np.int64) - self.ov0
        e = np.array([b for _, b in iv], np.int64) - self.ov0
        st = [v.sum() for v in self._stats(s, e)]
        return float(self._r(*st)), int(st[0])


def _grid(ov0, ov1, n, hop):
    if ov1 - ov0 < n:
        return np.zeros(0, np.int64)
    s = np.arange(ov0, ov1 - n + 1, hop, dtype=np.int64)
    if s[-1] != ov1 - n:
        s = np.append(s, ov1 - n)
    return s


def supported(al, thr, hop=WITHIN_HOP, with_max=False):
    """Union of the hop-grid 10 s windows (anchored at the overlap start, plus the end-aligned one) with r >= thr at the lag
    (and, with_max, the best window r on that grid)."""
    s = _grid(al.ov0, al.ov1, WIN, hop)
    if not len(s):
        return ([], float("nan")) if with_max else []
    r = np.nan_to_num(al.r(s, s + WIN), nan=-2.0)
    iv = _union([(int(a), int(a) + WIN) for a in s[r >= thr]])
    return (iv, float(r.max()) if r.max() > -2 else float("nan")) if with_max else iv


def extend_spans(al, seed):
    """The mask rule: each seed component grows by 0.25 s steps while the 2 s window at the new edge has r >= 0.8."""
    out = []
    for L, R in _union(_clip(seed, al.ov0, al.ov1)):
        while L - EXT_STEP >= al.ov0 and L - EXT_STEP + EXT_WIN <= al.ov1 and al.r(L - EXT_STEP, L - EXT_STEP + EXT_WIN) >= EXT_THR:
            L -= EXT_STEP
        while R + EXT_STEP <= al.ov1 and R + EXT_STEP - EXT_WIN >= al.ov0 and al.r(R + EXT_STEP - EXT_WIN, R + EXT_STEP) >= EXT_THR:
            R += EXT_STEP
        out.append((L, R))
    return _union(out)


def refine_lag(a, b, ks, xpos, rs):
    """The lag k maximising the pooled r over the cluster's flagged windows; ties go to the lag nearest the best hit."""
    ks = np.asarray(ks, np.int64)
    kbest = int(ks[int(np.argmax(rs))])
    kmin, kmax = int(ks.min()), int(ks.max())
    cand = range(kbest - REFINE_PAD, kbest + REFINE_PAD + 1) if kmax - kmin > REFINE_MAX_SPAN else range(kmin - REFINE_PAD, kmax + REFINE_PAD + 1)
    seed = _union([(int(p), int(p) + WIN) for p in xpos])
    best = None
    for k in cand:
        al = Aligned(a, b, k)
        if al.n < WIN:
            continue
        r, n = al.pooled(seed)
        if n < WIN // 2 or not np.isfinite(r):
            continue
        key = (r, -abs(k - kbest))
        if best is None or key > best[0]:
            best = (key, k, r, al)
    return (None, seed) if best is None else ((best[1], best[2], best[3]), seed)


def xcorr_pearson(a, b, min_overlap):
    """Pearson r(k) over the full overlap [max(0, k), min(La, Lb + k)) for every lag k (b[u] ~ a[u + k]) whose overlap is at
    least min_overlap samples -> (ks, r)."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    La, Lb = len(a), len(b)
    n = 1 << int(np.ceil(np.log2(La + Lb)))
    c = sfft.irfft(sfft.rfft(a, n) * np.conj(sfft.rfft(b, n)), n)
    ks = np.arange(-(Lb - 1), La, dtype=np.int64)
    t0, t1 = np.maximum(0, ks), np.minimum(La, Lb + ks)
    keep = (t1 - t0) >= max(2, int(np.ceil(min_overlap)))
    ks, t0, t1 = ks[keep], t0[keep], t1[keep]
    m = (t1 - t0).astype(np.float64)
    ca, caa, cb, cbb = _cum0(a), _cum0(a * a), _cum0(b), _cum0(b * b)
    Sa, Saa = ca[t1] - ca[t0], caa[t1] - caa[t0]
    Sb, Sbb = cb[t1 - ks] - cb[t0 - ks], cbb[t1 - ks] - cbb[t0 - ks]
    return ks, Aligned._r(m, Sa, Sb, Saa, Sbb, c[ks % n])


def measure_offset(ref, other, max_lag=None):
    """Global lag of `other` in `ref` (b_in_a) by full-overlap Pearson cross-correlation: the global peak over lags with overlap
    >= MIN_OVERLAP_FRAC of the shorter stream, and (max_lag given) the peak within |k| <= max_lag."""
    ks, r = xcorr_pearson(ref, other, MIN_OVERLAP_FRAC * min(len(ref), len(other)))
    rr = np.nan_to_num(r, nan=-2.0)
    out = {"global": None, "window": None}
    if len(ks) and rr.max() > -2:
        i = int(np.argmax(rr)); out["global"] = {"b_in_a": int(ks[i]), "r": float(r[i])}
    if max_lag is not None:
        w = np.abs(ks) <= max_lag
        if w.any() and rr[w].max() > -2:
            j = int(np.argmax(rr[w])); out["window"] = {"b_in_a": int(ks[w][j]), "r": float(r[w][j])}
    return out


# ------------------------------------------------------------------------------------------------ hits -> pair candidates
def _canonical(kind, qc, bc, h, cohort_order=COHORTS):
    """Hits in canonical orientation: within, x < y by stream index; cross, x in the earlier cohort. (x, y, xpos, k, r)."""
    q, t, b, u, r = h["q"].astype(np.int64), h["t"], h["b"].astype(np.int64), h["u"], h["r"]
    if kind == "within":
        sw = q > b
    else:
        sw = np.full(len(q), cohort_order.index(qc) > cohort_order.index(bc))
    x = np.where(sw, b, q); y = np.where(sw, q, b)
    xpos = np.where(sw, u, t)
    k = np.where(sw, u - t, t - u)
    return x, y, xpos, k, r


def clusters(x, y, xpos, k, r):
    """Group canonical hits by pair and lag cluster (lags within LAG_GAP of each other) -> list of (x, y, idx array)."""
    if not len(x):
        return []
    order = np.lexsort((k, y, x))
    xs, ys, ks = x[order], y[order], k[order]
    brk = np.ones(len(order), bool)
    brk[1:] = (xs[1:] != xs[:-1]) | (ys[1:] != ys[:-1]) | (ks[1:] - ks[:-1] > LAG_GAP)
    starts = np.flatnonzero(brk)
    ends = np.r_[starts[1:], len(order)]
    return [(int(xs[s]), int(ys[s]), order[s:e]) for s, e in zip(starts, ends)]


def _refine_pair(sa, sb, ks, xpos, rs, thr):
    """Refined lag, pooled r, aligned overlap and the windows with r >= thr at that lag (seed = flagged windows + those). When no
    candidate lag qualifies (not expected: the best hit's own lag always does), the best hit's lag is used unrefined (refined
    False), so that the detection is still merged, masked or flagged; not_reproduced remains only for an empty overlap."""
    best, seed = refine_lag(sa.x, sb.x, ks, xpos, rs)
    rec = {"k_range_detect": [int(np.min(ks)), int(np.max(ks))], "n_detect": int(len(ks)), "r_detect_max": round(float(np.max(rs)), 6),
           "lag_drift": bool(np.max(ks) - np.min(ks) > 2), "refined": best is not None}
    if best is None:
        kb = int(np.asarray(ks, np.int64)[int(np.argmax(rs))])
        al = Aligned(sa.x, sb.x, kb)
        if al.n == 0:
            return dict(rec, action="not_reproduced"), None, None, None
        best = (kb, al.pooled(seed)[0], al)
    k, rp, al = best
    sup, rwm = supported(al, thr, with_max=True)
    rec.update(b_in_a=int(k), b_in_a_s=round(k / C.FS, 4), r_pooled=round(float(rp), 6), r_window_max=round(rwm, 6),
               overlap_a=[al.ov0, al.ov1], overlap_b=[al.ov0 - k, al.ov1 - k])
    return rec, al, _union(_clip(seed, al.ov0, al.ov1) + sup), sup


def within_candidates(cohort, streams, h):
    """Every lag cluster of every within-cohort pair, refined; merge decided here (keyed pairs, coverage >= 50 %)."""
    x, y, xpos, k, r = _canonical("within", cohort, cohort, h)
    out = []
    for xi, yi, idx in clusters(x, y, xpos, k, r):
        sa, sb = streams[xi], streams[yi]
        rec, al, seed, sup = _refine_pair(sa, sb, k[idx], xpos[idx], r[idx], WITHIN_THR)
        rec = {"cohort": cohort, "a": sa.sid, "b": sb.sid, "a_kind": sa.kind, "b_kind": sb.kind, "keyed": bool(sa.keyed and sb.keyed), **rec}
        if al is not None:
            rec["coverage"] = round(_length(sup) / min(sa.x.size, sb.x.size), 6)
            spans = extend_spans(al, seed)
            rec["spans_a"] = _union([(max(0, L - MARGIN), min(sa.x.size, R + MARGIN)) for L, R in spans])
            rec["spans_b"] = _union([(max(0, L - al.k - MARGIN), min(sb.x.size, R - al.k + MARGIN)) for L, R in spans])
            if not rec["keyed"]:
                rec["action"] = "report_only"
            elif rec["coverage"] >= MERGE_COVERAGE:
                rec["action"] = "merge"
            else:
                rec["action"] = "mask_candidate"
        out.append(rec)
    return out


def _stimulus(cohort, sid):
    """The stimulus a stream belongs to (the manifest.overlap 'stimulus' field): FAU code, else the stream id."""
    return sid.split("/")[0] if cohort == "fau" else sid


def cross_candidates(A, B, SA, SB, hits_ab, hits_ba, order=COHORTS):
    """Cross-cohort overlaps (A before B in `order`) from both scan directions, refined; spans = windows with r >= 0.7; lag =
    b.span[0] - a.span[0] = -b_in_a (manifest.overlap sign). `order` names the two sides (COHORTS; the positive control passes its
    pseudo cohorts)."""
    parts = []
    for (qc, bc), h in (((A, B), hits_ab), ((B, A), hits_ba)):
        if h is not None and len(h["q"]):
            x, y, xpos, k, r = _canonical("cross", qc, bc, h, order)
            parts.append((x, y, xpos, k, r, np.full(len(x), order.index(qc))))
    if not parts:
        return []
    x, y, xpos, k, r, src = (np.concatenate([p[i] for p in parts]) for i in range(6))
    out = []
    for xi, yi, idx in clusters(x, y, xpos, k, r):
        sa, sb = SA[xi], SB[yi]
        rec, al, seed, sup = _refine_pair(sa, sb, k[idx], xpos[idx], r[idx], CROSS_THR)
        o = {"a": {"cohort": A, "stream": sa.sid, "stimulus": _stimulus(A, sa.sid), "kind": sa.kind, "keyed": sa.keyed},
             "b": {"cohort": B, "stream": sb.sid, "stimulus": _stimulus(B, sb.sid), "kind": sb.kind, "keyed": sb.keyed},
             "detected_from": sorted({order[int(s)] for s in src[idx]}), **rec}
        if al is not None:
            o["coverage"] = round(_length(sup) / min(sa.x.size, sb.x.size), 6)
            o["lag"] = -int(al.k)
            o["spans_a"] = seed
            o["spans_b"] = _union([(a - al.k, b - al.k) for a, b in seed])
            o["a"]["span"], o["b"]["span"] = [seed[0][0], seed[-1][1]], [seed[0][0] - al.k, seed[-1][1] - al.k]
        out.append(o)
    return out


def flag_overlaps(overlaps):
    """{(cohort, other cohort): stream ids} over every cross-cohort record, whatever its action (conservative)."""
    flagged = collections.defaultdict(set)
    for o in overlaps:
        flagged[(o["a"]["cohort"], o["b"]["cohort"])].add(o["a"]["stream"])
        flagged[(o["b"]["cohort"], o["a"]["cohort"])].add(o["b"]["stream"])
    return flagged


def family_closure(fams, sids):
    """sids plus every member of a family that holds one of them (families are disjoint; non-keyed streams have none)."""
    out = set(sids)
    for f in fams:
        mem = {m["stream"] for m in f["members"]}
        if mem & out:
            out |= mem
    return out


# ------------------------------------------------------------------------------------------------ declared structures
def sk_declared(streams, decl=SK_DECLARED):
    """Measure the declared audiobook_1 family against its root; returns (edges, report)."""
    by = {s.sid: s for s in streams}
    root = decl["root"]
    checks, measured, edges = [], {}, []
    members = list(decl["offsets"]) + list(decl["variants"]) + list(decl["excerpts"])
    if root not in by:
        checks.append(_chk(f"declared root {root} present", False))
        return edges, {"declared": decl, "measured": measured, "checks": checks, "ok": False}
    for m in members:
        if m not in by:
            checks.append(_chk(f"declared member {m} present", False))
            continue
        g = measure_offset(by[root].x, by[m].x)["global"]
        if g is None:
            checks.append(_chk(f"{m} measurable against {root}", False))
            continue
        al = Aligned(by[root].x, by[m].x, g["b_in_a"])
        cov = _length(supported(al, WITHIN_THR)) / min(by[root].x.size, by[m].x.size)
        measured[m] = {"b_in_root": g["b_in_a"], "b_in_root_s": round(g["b_in_a"] / C.FS, 4), "r": round(g["r"], 6), "coverage": round(cov, 6)}
        checks.append(_chk(f"{m} matches {root} (global peak r >= {DECLARED_MIN_R})", g["r"] >= DECLARED_MIN_R, measured[m]))
        if g["r"] >= DECLARED_MIN_R:
            edges.append({"a": root, "b": m, "k": g["b_in_a"], "source": "declared", "weight": float(cov)})
    for m, exp in decl["offsets"].items():
        if m in measured:
            got = measured[m]["b_in_root"]
            checks.append(_chk(f"{m} offset {exp} +- {CLOCK_TOL} in {root}", abs(got - exp) <= CLOCK_TOL, {"expected": exp, "measured": got}))
    for v, half in decl["variants"].items():          # §2.5 'asserts them to +-1': the copies are declared at their halves' offsets
        if v in measured and half in decl["offsets"]:
            exp, got = decl["offsets"][half], measured[v]["b_in_root"]
            checks.append(_chk(f"{v} offset {exp} +- {CLOCK_TOL} in {root} (declared at the offset of {half})", abs(got - exp) <= CLOCK_TOL,
                               {"expected": exp, "measured": got, "declared_as": half}))
        if v in measured and half in measured:
            d = measured[v]["b_in_root"] - measured[half]["b_in_root"]
            checks.append(_chk(f"{v} on the clock of {half} (+- {CLOCK_TOL})", abs(d) <= CLOCK_TOL, {"difference": int(d)}))
    ok = all(c["ok"] for c in checks if c["level"] == "assert")
    return edges, {"declared": {**decl, "excerpts": list(decl["excerpts"])}, "measured": measured, "checks": checks, "ok": ok}


def federici_lags(streams):
    """One family per content group with >= 2 items; partner offsets from the +-2 s lag rule. Returns (edges, records)."""
    groups = collections.defaultdict(list)
    for s in streams:
        g = s.meta.get("content_group")
        if g is not None:
            groups[g].append(s)
    edges, recs = [], []
    for g in sorted(groups, key=lambda v: (str(type(v)), v)):
        items = groups[g]
        if len(items) < 2:
            continue
        nat = [s for s in items if s.meta.get("condition") == "natural"]
        ref = sorted(nat or items, key=lambda s: (-int(s.meta.get("n_listeners", 0)), s.sid))[0]
        for p in sorted((s for s in items if s is not ref), key=lambda s: s.sid):
            m = measure_offset(ref.x, p.x, max_lag=FED_MAX_LAG)
            gl, wi = m["global"], m["window"]
            known = bool(wi is not None and gl is not None and wi["r"] >= FED_MIN_R and abs(gl["b_in_a"]) <= FED_MAX_LAG)
            why = []
            if wi is None or gl is None:
                why.append("no measurable overlap")
            else:
                if wi["r"] < FED_MIN_R:
                    why.append(f"peak r within +-{FED_MAX_LAG} is {wi['r']:.3f} < {FED_MIN_R}")
                if abs(gl["b_in_a"]) > FED_MAX_LAG:
                    why.append(f"global peak at {gl['b_in_a']} samples (r {gl['r']:.3f}), outside +-{FED_MAX_LAG}")
            why = "; ".join(why) or None
            edges.append({"a": ref.sid, "b": p.sid, "k": wi["b_in_a"] if known else None, "source": "natural_vocoded",
                          "weight": float(wi["r"]) if wi else 0.0})
            recs.append({"content_group": g, "reference": ref.sid, "partner": p.sid,
                         "conditions": {ref.sid: ref.meta.get("condition"), p.sid: p.meta.get("condition")},
                         "window": None if wi is None else {"b_in_a": wi["b_in_a"], "r": round(wi["r"], 6)},
                         "global": None if gl is None else {"b_in_a": gl["b_in_a"], "r": round(gl["r"], 6)},
                         "clock": "known" if known else "unknown", "offset": wi["b_in_a"] if known else None,
                         "offset_s": round(wi["b_in_a"] / C.FS, 4) if known else None, "reason": why})
    return edges, recs


# ------------------------------------------------------------------------------------------------ positive controls (assert)
def declared_relations(rep, decl=SK_DECLARED):
    """The relations (x, y, k, basis), y[u] ~ x[u + k], that the declared audiobook_1 structure implies: each measured member in the
    root at its measured offset; each shifted copy in its half at the difference of their measured offsets. Also returns the
    declared members without a measurement."""
    root, meas = decl["root"], rep["measured"]
    members = list(decl["offsets"]) + list(decl["variants"]) + list(decl["excerpts"])
    rel = [(root, m, int(meas[m]["b_in_root"]), "measured offset in the root") for m in members if m in meas]
    for v, half in decl["variants"].items():
        if v in meas and half in meas:
            rel.append((half, v, int(meas[v]["b_in_root"] - meas[half]["b_in_root"]), "shifted copy in its half"))
    return rel, [m for m in members if m not in meas]


def window_scan_control(pairs, rels, missing):
    """Positive control of the within-cohort window scan (§3.4.3): every declared relation must be a merge record (coverage >= 0.5)
    at its expected lag +- 1. Returns (rows, assert checks)."""
    rows, checks = [], []
    for x, y, k, basis in rels:
        found = [{"action": p.get("action"), "b_in_a": int(p["b_in_a"] if p["a"] == x else -p["b_in_a"]), "coverage": p.get("coverage"),
                  "n_detect": p.get("n_detect"), "r_window_max": p.get("r_window_max"), "refined": p.get("refined")}
                 for p in pairs if {p["a"], p["b"]} == {x, y} and p.get("b_in_a") is not None]
        ok = any(f["action"] == "merge" and (f["coverage"] or 0.0) >= MERGE_COVERAGE and abs(f["b_in_a"] - k) <= CLOCK_TOL for f in found)
        row = {"x": x, "y": y, "expected_b_in_a": k, "basis": basis, "found": found, "ok": bool(ok)}
        rows.append(row)
        checks.append(_chk(f"positive control (window scan): {y} merged into {x} at {k} +- {CLOCK_TOL} with coverage >= {MERGE_COVERAGE}",
                           ok, row))
    for m in missing:
        checks.append(_chk(f"positive control (window scan): {m} has a measured offset", False, {"member": m}))
    return rows, checks


def cross_rule_control(streams, rels, decl=SK_DECLARED, nfft=NFFT, workers=1, batch_bytes=256 << 20):
    """Positive control of the cross-cohort rule (§3.4.2): the declared members as a pseudo cohort 'probe' against a bank holding
    only the root ('root'), both directions through run_units -> cross_candidates -> flag_overlaps (10 s windows, 2 s hop,
    r >= 0.7). Each member must be detected from both directions and flagged at its measured offset +- 1, with the r >= 0.7
    windows covering >= 50 % of it. Returns (report, assert checks)."""
    by = {s.sid: s for s in streams}
    root = decl["root"]
    exp = {y: k for x, y, k, _ in rels if x == root and y in by}
    if root not in by or not exp:
        return {"ran": False}, [_chk("positive control (cross rule): the root and its measured members are present", False,
                                     {"root": root, "members": sorted(exp)})]
    R, P = by[root], sorted((by[y] for y in exp), key=lambda s: s.sid)
    h_pr = run_units("control", "probe", "root", P, Bank([R], nfft, workers), CROSS_HOP, CROSS_THR, None, workers, batch_bytes)
    h_rp = run_units("control", "root", "probe", [R], Bank(P, nfft, workers), CROSS_HOP, CROSS_THR, None, workers, batch_bytes)
    ov = cross_candidates("root", "probe", [R], P, h_rp[0], h_pr[0], order=("root", "probe"))
    flagged = flag_overlaps(ov)
    rows, checks = [], []
    for y, k in sorted(exp.items()):
        found = [{"b_in_a": o.get("b_in_a"), "coverage": o.get("coverage"), "r_window_max": o.get("r_window_max"), "n_detect": o["n_detect"],
                  "detected_from": o["detected_from"], "refined": o.get("refined")} for o in ov if o["b"]["stream"] == y]
        hit = any(f["b_in_a"] is not None and abs(f["b_in_a"] - k) <= CLOCK_TOL and (f["coverage"] or 0.0) >= MERGE_COVERAGE
                  and f["detected_from"] == ["probe", "root"] for f in found)
        ok = bool(hit and y in flagged.get(("probe", "root"), ()) and root in flagged.get(("root", "probe"), ()))
        row = {"probe": y, "expected_b_in_a": k, "found": found, "flagged": y in flagged.get(("probe", "root"), ()), "ok": ok}
        rows.append(row)
        checks.append(_chk(f"positive control (cross rule): {y} detected in {root} from both directions and flagged at {k} +- {CLOCK_TOL}",
                           ok, row))
    rep = {"ran": True, "bank": root, "probes": [s.sid for s in P], "windows": {"probe->root": h_pr[1], "root->probe": h_rp[1]},
           "n_records": len(ov), "rows": rows}
    return rep, checks


# ------------------------------------------------------------------------------------------------ FAU scene pairs (report only)
def scene_pairs(streams, pairs):
    """FAU codes X < Y whose streams are each other's with the roles swapped: X attended ~ Y distractor and / or X distractor ~
    Y attended, each at coverage >= 0.5 (within-cohort report_only records). attention_swapped: both relations hold; same_scene:
    both at the same lag (+- 1), i.e. the same two-talker scene with attention swapped. Reported only (CSX: decision for the lead)."""
    code = collections.defaultdict(dict)
    for s in streams:
        c, _, which = s.sid.partition("/")
        code[c][which] = s.sid
    comp = sorted(c for c, d in code.items() if "attended" in d and "distractor" in d)
    rel = collections.defaultdict(list)
    for p in pairs:
        if p.get("b_in_a") is not None and (p.get("coverage") or 0.0) >= MERGE_COVERAGE:
            rel[frozenset((p["a"], p["b"]))].append(p)

    def lags(x, y):                                # y in x
        return sorted({int(p["b_in_a"] if p["a"] == x else -p["b_in_a"]) for p in rel.get(frozenset((x, y)), ())})
    out = []
    for i, X in enumerate(comp):
        for Y in comp[i + 1:]:
            k1, k2 = lags(code[X]["attended"], code[Y]["distractor"]), lags(code[X]["distractor"], code[Y]["attended"])
            if not (k1 or k2):
                continue
            out.append({"codes": [X, Y], "attended_X~distractor_Y": k1, "distractor_X~attended_Y": k2, "attention_swapped": bool(k1 and k2),
                        "same_scene": any(abs(a - b) <= CLOCK_TOL for a in k1 for b in k2), "action": "report_only"})
    return out


# ------------------------------------------------------------------------------------------------ families
_PRIO = {"declared": 0, "natural_vocoded": 0, "duplicate_scan": 1}


def sk_declared_members(decl=SK_DECLARED):
    """The streams the declared family's spec names (root, halves, shifted copies, excerpts): those C4 gives the declared family's
    provisional name (build_sparrkulee.DECLARED_FAMILY), whether or not C3 merges further streams into that family."""
    return [decl["root"], *decl["offsets"], *decl["variants"], *decl["excerpts"]]


def default_family_name(cohort, s, declared_members=(), declared_family=None):
    """The provisional family name the C4 / C5 tables carry for a stream before C3 (build_sparrkulee.family_name,
    build_public: 'sparrkulee:<family>', 'fau:<code>', 'dtu:<sha>', 'federici:g<content group>'). Only the declared members
    (sk_declared_members) carry the declared family's name (declared_family, default SK_DECLARED's); any other SparrKULee stream
    carries its own, also when the duplicate scan merges it into the declared family."""
    if cohort == "sparrkulee":
        return f"sparrkulee:{declared_family or SK_DECLARED['family']}" if s.sid in declared_members else f"sparrkulee:{s.sid}"
    if cohort == "fau":
        return f"fau:{s.sid.split('/')[0]}"
    if cohort == "federici":
        g = s.meta.get("content_group")
        return f"federici:{s.sid}" if g is None else (f"federici:g{g}" if isinstance(g, (int, np.integer)) else f"federici:{g}")
    return f"{cohort}:{s.sid}"


def build_families(cohort, streams, edges, family_name=None, declared_members=None):
    """Families of the keyed streams of one cohort from edges {a, b, k (off_b = off_a + k; None = unknown), source, weight}.
    Declared (SparrKULee) and natural_vocoded (Federici) edges define declared groups; a duplicate_scan edge between two streams of
    one declared group is check-only (the specific rule governs that clock, e.g. the Federici +-2 s rule), every other edge may
    enter the spanning tree. declared_members: the streams whose provisional name is the declared family's (scan() passes
    sk_declared_members for SparrKULee; None = the endpoints of the declared edges); every other member keeps its own provisional
    name, so provisional_names is complete when the scan merges a non-declared stream into the declared family. Returns
    (families, member map {sid: (family index, offset or None, offset_known)})."""
    keyed = {s.sid: s for s in streams if s.keyed}
    edges = [dict(e) for e in edges if e["a"] in keyed and e["b"] in keyed and e["a"] != e["b"]]
    dmem = set(declared_members) if declared_members is not None else \
        {i for e in edges if e["source"] == "declared" for i in (e["a"], e["b"])}
    parent, dparent = {i: i for i in keyed}, {}

    def find(p_, i):
        while p_[i] != i:
            p_[i] = p_[p_[i]]
            i = p_[i]
        return i
    for e in edges:
        if e["source"] in ("declared", "natural_vocoded"):
            for i in (e["a"], e["b"]):
                dparent.setdefault(i, i)
            dparent[find(dparent, e["a"])] = find(dparent, e["b"])
    for e in edges:
        e["check_only"] = bool(e["source"] == "duplicate_scan" and e["a"] in dparent and e["b"] in dparent
                               and find(dparent, e["a"]) == find(dparent, e["b"]))
        parent[find(parent, e["a"])] = find(parent, e["b"])
    comps = collections.defaultdict(list)
    for i in keyed:
        comps[find(parent, i)].append(i)
    fams, member = [], {}
    for comp in sorted((sorted(c) for c in comps.values()), key=lambda c: c[0]):
        cs = set(comp)
        ce = [e for e in edges if e["a"] in cs]
        decl_roots = sorted({e["a"] for e in ce if e["source"] in ("declared", "natural_vocoded")},
                            key=lambda i: (-int(keyed[i].meta.get("n_listeners", 0)), -keyed[i].x.size, i))
        root = decl_roots[0] if decl_roots else sorted(comp, key=lambda i: (-keyed[i].x.size, i))[0]
        adj = collections.defaultdict(list)
        for n_, e in enumerate(ce):
            if not e["check_only"]:
                adj[e["a"]].append((n_, 1)); adj[e["b"]].append((n_, -1))
        off, known, tree, heap, seq = {root: 0}, {root: True}, set(), [], 0

        def push(node):
            nonlocal seq
            for n_, sgn in adj[node]:
                e = ce[n_]
                prio = 2 if e["k"] is None else _PRIO.get(e["source"], 1)
                heapq.heappush(heap, (prio, -float(e.get("weight", 0.0)), seq, n_, sgn, node))
                seq += 1
        push(root)
        while heap:
            _, _, _, n_, sgn, frm = heapq.heappop(heap)
            e = ce[n_]
            to = e["b"] if sgn == 1 else e["a"]
            if to in off:
                continue
            if e["k"] is None or not known[frm]:
                off[to], known[to] = None, False
            else:
                off[to], known[to] = off[frm] + sgn * int(e["k"]), True
            tree.add(n_)
            push(to)
        conflicts, out_edges = [], []
        for n_, e in enumerate(ce):
            res = None
            if e["k"] is not None and known.get(e["a"]) and known.get(e["b"]):
                res = int(off[e["b"]] - off[e["a"]] - int(e["k"]))
                if abs(res) > CLOCK_TOL:
                    conflicts.append({"a": e["a"], "b": e["b"], "b_in_a": int(e["k"]), "source": e["source"], "residual": res})
            out_edges.append({"a": e["a"], "b": e["b"], "b_in_a": None if e["k"] is None else int(e["k"]), "source": e["source"],
                              "weight": round(float(e.get("weight", 0.0)), 6), "tree": n_ in tree, "check_only": e["check_only"],
                              "residual": res})
        clock = "known" if all(known[i] for i in comp) and not conflicts else "unknown"
        shift = min(off[i] for i in comp if known[i])
        for i in comp:
            if known[i]:
                off[i] -= shift
        if conflicts:          # the tree offsets cannot be trusted: only the root keeps a known offset (0)
            known = {i: i == root for i in comp}
            off[root] = 0
        for i in comp:
            if known[i] and off[i] + keyed[i].x.size >= 1 << C.S_BITS:
                raise ScanError(f"{cohort} family of {root}: offset {off[i]} + length {keyed[i].x.size} exceeds the 2**{C.S_BITS} key budget")
        srcs = sorted({e["source"] for e in ce if not e["check_only"]})
        basis = "+".join(srcs) if srcs else "own"
        cgs = sorted({str(keyed[i].meta.get("content_group")) for i in comp if keyed[i].meta.get("content_group") is not None})
        prov = sorted({default_family_name(cohort, keyed[i], dmem, family_name) for i in comp})     # each member's own C4 / C5 name
        name = f"{cohort}:{family_name}" if ("declared" in srcs and family_name) else \
            default_family_name(cohort, keyed[root], dmem if "declared" in srcs else (), family_name)
        mem = [{"stream": i, "offset": off[i] if known[i] else None, "offset_s": round(off[i] / C.FS, 4) if known[i] else None,
                "offset_known": bool(known[i]), "length": int(keyed[i].x.size)} for i in comp]
        mem.sort(key=lambda m_: (not m_["offset_known"], m_["offset"] if m_["offset"] is not None else 0, m_["stream"]))
        fams.append({"name": name, "root": root, "basis": basis, "clock": clock, "members": mem, "edges": out_edges,
                     "conflicts": conflicts, "content_groups": cgs, "crosses_content_groups": len(cgs) > 1, "provisional_names": prov})
        for m_ in mem:
            member[m_["stream"]] = (len(fams) - 1, m_["offset"], m_["offset_known"])
    return fams, member


# ------------------------------------------------------------------------------------------------ statistics
def _winstats(h, qstreams, bstreams, thr, n_win, n_sil):
    wr = h["wr"]
    st = {"n_windows": int(n_win), "n_silent_windows": int(n_sil), "n_scored": int(len(wr)), "thr": thr, "n_ge_thr": int((wr >= thr).sum())}
    if len(wr):
        st["r_max_quantiles"] = {q: round(float(np.quantile(wr, float(q))), 6) for q in ("0.5", "0.9", "0.99", "1.0")}
        top = np.argsort(-wr, kind="stable")[:5]
        st["top5"] = [{"r": round(float(wr[i]), 6), "query": qstreams[int(h["wq"][i])].sid, "t_s": round(int(h["wt"][i]) / C.FS, 3),
                       "bank": bstreams[int(h["wb"][i])].sid if h["wb"][i] >= 0 else None,
                       "u_s": round(int(h["wu"][i]) / C.FS, 3) if h["wb"][i] >= 0 else None} for i in top]
    return st


def _stream_rows(cohort, streams, member, fams):
    rows = []
    for s in streams:
        fi = member.get(s.sid)
        rows.append({"stream": s.sid, "kind": s.kind, "keyed": s.keyed, "n": int(s.x.size), "seconds": round(s.x.size / C.FS, 4),
                     "family": fams[fi[0]]["name"] if fi else None, "family_offset": fi[1] if fi else None,
                     "offset_known": fi[2] if fi else None, **s.meta})
    return rows


# ------------------------------------------------------------------------------------------------ the scan
PARAMS = {"win": WIN, "cross_hop": CROSS_HOP, "cross_thr": CROSS_THR, "within_hop": WITHIN_HOP, "within_thr": WITHIN_THR,
          "merge_coverage": MERGE_COVERAGE, "ext_win": EXT_WIN, "ext_step": EXT_STEP, "ext_thr": EXT_THR, "margin": MARGIN,
          "fed_max_lag": FED_MAX_LAG, "fed_min_r": FED_MIN_R, "clock_tol": CLOCK_TOL, "declared_min_r": DECLARED_MIN_R,
          "var_floor": VAR_FLOOR, "run_gap": RUN_GAP, "lag_gap": LAG_GAP, "refine_pad": REFINE_PAD, "refine_max_span": REFINE_MAX_SPAN,
          "min_overlap_frac": MIN_OVERLAP_FRAC, "nfft": NFFT, "unit_samples": UNIT_SAMPLES, "neighbor": C.NEIGHBOR, "fs": C.FS,
          "sk_declared": {**SK_DECLARED, "excerpts": list(SK_DECLARED["excerpts"])}, "donor_sets": {k: list(v) for k, v in DONOR_SETS.items()}}


def signature(streams):
    """sha256 of the code, the contract, the parameters and every processed stream (id, kind, keyed, bytes)."""
    h = hashlib.sha256(json.dumps({"schema": SCHEMA, "code": builder_sha(), "contract": _file_sha(C.__file__),
                                   "params": PARAMS}, sort_keys=True).encode())
    for c in COHORTS:
        for s in streams.get(c, []):
            h.update(f"|{c}|{s.sid}|{s.kind}|{int(s.keyed)}|".encode())
            h.update(np.ascontiguousarray(s.x, np.float64).tobytes())
    return h.hexdigest()


def scan(streams, *, work_dir=None, workers=1, batch_bytes=256 << 20, nfft=NFFT, sk_declared_spec=SK_DECLARED, log=None):
    """Run every C3 scan on {cohort: [Stream]} (stream lists sorted by id) and assemble the JSON-able result (no file is written
    except the resumable units under work_dir)."""
    cohorts = [c for c in COHORTS if streams.get(c)]
    banks = {c: Bank(streams[c], nfft, workers) for c in cohorts}
    if log:
        for c in cohorts:
            b = banks[c]
            log(f"[scan_audio] bank {c}: {len(b.streams)} streams, {int(b.lens.sum())} samples ({b.lens.sum() / C.FS / 3600:.2f} h), "
                f"{b.nb} blocks of {b.nfft}, {b.n_valid} valid windows")
    if work_dir:
        os.makedirs(work_dir, exist_ok=True)
    W = {c: run_units("within", c, c, streams[c], banks[c], WITHIN_HOP, WITHIN_THR, work_dir, workers, batch_bytes, log) for c in cohorts}
    X = {(a, b): run_units("cross", a, b, streams[a], banks[b], CROSS_HOP, CROSS_THR, work_dir, workers, batch_bytes, log)
         for a in cohorts for b in cohorts if a != b}
    checks, observations = [], []

    # ---- declared structures and within-cohort candidates
    sk_rep, fed_recs = None, []
    edges = {c: [] for c in cohorts}
    if "sparrkulee" in cohorts and sk_declared_spec:
        e, sk_rep = sk_declared(streams["sparrkulee"], sk_declared_spec)
        edges["sparrkulee"] += e
        checks += sk_rep["checks"]
    if "federici" in cohorts:
        e, fed_recs = federici_lags(streams["federici"])
        edges["federici"] += e
    within, families, shared, shared_s = {}, {}, {}, {}
    stream_rows = {}
    for c in cohorts:
        S = streams[c]
        cands = within_candidates(c, S, W[c][0])
        for rec in cands:
            if rec.get("action") == "merge":
                edges[c].append({"a": rec["a"], "b": rec["b"], "k": rec["b_in_a"], "source": "duplicate_scan", "weight": rec["coverage"]})
        decl_c = sk_declared_spec if (c == "sparrkulee" and sk_declared_spec) else None
        fams, member = build_families(c, S, edges[c], family_name=decl_c["family"] if decl_c else None,
                                      declared_members=sk_declared_members(decl_c) if decl_c else ())
        per_stream = collections.defaultdict(list)
        roles = {}
        for f_ in fams:
            for e in f_["edges"]:
                if e["source"] == "duplicate_scan":
                    roles[(e["a"], e["b"], e["b_in_a"])] = ("check_only" if e["check_only"] else "tree" if e["tree"] else "verified") + \
                        ("" if e["residual"] is None or abs(e["residual"]) <= CLOCK_TOL else "_conflict")
        for rec in cands:
            fa, fb = member.get(rec["a"]), member.get(rec["b"])
            rec["family_a"] = fams[fa[0]]["name"] if fa else None
            rec["family_b"] = fams[fb[0]]["name"] if fb else None
            if rec.get("action") == "merge":
                rec["edge_role"] = roles.get((rec["a"], rec["b"], rec["b_in_a"]))
            if rec.get("action") != "mask_candidate":
                continue
            if fa and fb and fa[0] == fb[0]:
                f_ = fams[fa[0]]
                if f_["clock"] == "unknown" or (fa[2] and fb[2] and abs(fb[1] - fa[1] - rec["b_in_a"]) <= C.NEIGHBOR):
                    rec["action"] = "family_mask_covers"
                    continue
            rec["action"] = "mask"
            for side, other in (("a", "b"), ("b", "a")):
                for sp in rec[f"spans_{side}"]:
                    per_stream[rec[side]].append((sp, rec[other], rec["b_in_a"] if side == "a" else -rec["b_in_a"]))
        for rec in cands:
            for key in ("spans_a", "spans_b"):
                if key in rec:
                    rec[key + "_s"] = _secs(rec[key])
        rows = []
        for sid in sorted(per_stream):
            for u in _union([sp for sp, _, _ in per_stream[sid]]):
                partners = sorted({(o, kk) for (a, b), o, kk in per_stream[sid] if a < u[1] and u[0] < b})
                rows.append({"stream": sid, "span": u, "span_s": _secs([u])[0], "partners": [{"stream": o, "b_in_a": kk} for o, kk in partners]})
        tot = int(sum(s.x.size for s in S if s.keyed))
        masked = int(sum(r_["span"][1] - r_["span"][0] for r_ in rows))
        shared[c] = rows
        shared_s[c] = {"masked_s": round(masked / C.FS, 3), "total_keyed_s": round(tot / C.FS, 3), "fraction": round(masked / tot, 6) if tot else 0.0,
                       "n_streams": len({r_["stream"] for r_ in rows})}
        for f_ in fams:
            if f_["conflicts"]:
                checks.append(_chk(f"{c} family {f_['name']}: edges agree to +-{CLOCK_TOL}", False, f_["conflicts"], level="warn"))
            if f_["crosses_content_groups"]:
                checks.append(_chk(f"{c} family {f_['name']} inside one content group", False, f_["content_groups"], level="warn"))
        hits, n_win, n_sil = W[c]
        within[c] = {"stats": _winstats(hits, S, S, WITHIN_THR, n_win, n_sil), "pairs": cands,
                     "n_pairs": collections.Counter(r_.get("action") for r_ in cands)}
        families[c] = fams
        stream_rows[c] = _stream_rows(c, S, member, fams)
        for rec in cands:
            if rec.get("action") == "report_only":
                observations.append(f"{c}: {rec['a']} ({rec['a_kind']}) ~ {rec['b']} ({rec['b_kind']}) at b_in_a {rec.get('b_in_a')}, "
                                    f"coverage {rec.get('coverage')}, r_max {rec['r_detect_max']} (non-keyed: reported only)")

    # ---- cross-cohort overlaps
    overlaps, stats = [], []
    for i, A in enumerate(cohorts):
        for B in cohorts[i + 1:]:
            ab, ba = X[(A, B)], X[(B, A)]
            overlaps += cross_candidates(A, B, streams[A], streams[B], ab[0], ba[0])
            stats.append({"query": A, "bank": B, **_winstats(ab[0], streams[A], streams[B], CROSS_THR, ab[1], ab[2])})
            stats.append({"query": B, "bank": A, **_winstats(ba[0], streams[B], streams[A], CROSS_THR, ba[1], ba[2])})
    for o in overlaps:
        for key in ("spans_a", "spans_b"):
            if key in o:
                o[key + "_s"] = _secs(o[key])
    flagged = flag_overlaps(overlaps)              # every record, refined or not (conservative)
    direct = {t: {d: sorted(flagged.get((d, t), ())) for d in DONOR_SETS[t] if d in cohorts} for t in DONOR_SETS}
    excl = {t: {d: sorted(family_closure(families[d], v)) for d, v in dd.items()} for t, dd in direct.items()}
    cross = {"stats": stats, "overlaps": overlaps,
             "flagged_streams": {c: sorted({s for (cc, _), v in flagged.items() if cc == c for s in v}) for c in cohorts},
             "donor_exclusions": excl, "donor_exclusions_direct": direct,
             "added_via_family": {t: {d: sorted(set(excl[t][d]) - set(v)) for d, v in dd.items()} for t, dd in direct.items()},
             "donor_exclusion_rule": "for target T and donor cohort D: every D stream with a cross-cohort window r >= 0.7 against any T "
                                     "stream (any detection, refined or not, from either scan direction, non-keyed streams included), "
                                     "plus every member of a D family that holds such a stream (donor_exclusions_direct: the direct "
                                     "flags). The manifest removes from T's donor set every D presentation whose attended or ignored "
                                     "stream is listed. A listed SparrKULee dev / bridge_cal stream makes that target's dev / bridge_cal "
                                     "differ from the shared definition (§3.2); C6 reports it. Only scanned donor cohorts have an "
                                     "entry (a --sources subset: complete false; the real sources assert completeness). "
                                     "private_bdf: not scanned (not_scanned).",
             "not_scanned": {"private_bdf": PRIVATE_NOT_SCANNED}}
    unref_x = [{"a": o["a"]["stream"], "b": o["b"]["stream"], "action": o.get("action")} for o in overlaps if not o.get("refined", True)]
    unref_w = {c: [{"a": p["a"], "b": p["b"], "action": p.get("action")} for p in within[c]["pairs"] if not p.get("refined", True)]
               for c in cohorts}
    checks.append(_chk("every within-cohort detection refined", not any(unref_w.values()), {c: v for c, v in unref_w.items() if v}, level="warn"))
    checks.append(_chk("every cross-cohort detection refined (unrefined ones are flagged at the best hit's lag)", not unref_x, unref_x,
                       level="warn"))
    if "sparrkulee" in cohorts:
        sk_flag = cross["flagged_streams"]["sparrkulee"]
        checks.append(_chk("no SparrKULee stream flagged against another cohort (a flagged dev / bridge_cal stream makes the shared dev / "
                           "bridge_cal definition target-specific: C6 checks the roles)", not sk_flag, sk_flag, level="warn"))
    # ---- every non-silent query window was scored (a skipped stream or an empty bank would otherwise pass silently)
    cov = [{"scan": f"within {c}", **{k: within[c]["stats"][k] for k in ("n_windows", "n_silent_windows", "n_scored")}} for c in cohorts]
    cov += [{"scan": f"cross {s['query']}->{s['bank']}", **{k: s[k] for k in ("n_windows", "n_silent_windows", "n_scored")}} for s in stats]
    bad = [r_ for r_ in cov if r_["n_scored"] != r_["n_windows"] - r_["n_silent_windows"]]
    checks.append(_chk("every non-silent query window scored (within and cross)", not bad, bad or {"n_scans": len(cov)}))

    # ---- positive controls: the window scan must find the run's own declared duplicates (assert)
    pc = {"ran": False, "reason": "no SparrKULee declared structure in this scan"}
    if sk_rep is not None:
        rels, missing = declared_relations(sk_rep, sk_declared_spec)
        rows_w, chk_w = window_scan_control(within["sparrkulee"]["pairs"], rels, missing)
        rep_x, chk_x = cross_rule_control(streams["sparrkulee"], rels, sk_declared_spec, nfft, workers, batch_bytes)
        pc = {"ran": True, "ok": all(c_["ok"] for c_ in chk_w + chk_x),
              "relations": [{"x": x_, "y": y_, "expected_b_in_a": k_, "basis": b_} for x_, y_, k_, b_ in rels],
              "within": rows_w, "cross": rep_x}
        checks += chk_w + chk_x
        checks.append(_chk("SparrKULee shared audio found (the scout matched head / tail windows in 49 of the 72 files)",
                           bool(shared["sparrkulee"]), shared_s["sparrkulee"], level="warn"))
        if log:
            log(f"[scan_audio] positive controls: {sum(c_['ok'] for c_ in chk_w)}/{len(chk_w)} window-scan relations, "
                f"{sum(c_['ok'] for c_ in chk_x)}/{len(chk_x)} cross-rule probes")
    scenes = {"fau": scene_pairs(streams["fau"], within["fau"]["pairs"])} if "fau" in cohorts else {}
    for c, v in scenes.items():
        for sp in v:
            if sp["attention_swapped"]:
                observations.append(f"{c}: codes {sp['codes'][0]} and {sp['codes'][1]} present each other's streams with attention swapped "
                                    f"(same scene: {sp['same_scene']}); reported only, not masked (CSX: decision for the lead)")
    # ---- C6 re-maps every C4 / C5 provisional family onto the one merged family that lists its name (assert; new in the second
    #      M2c review, appended last so that every earlier check keeps its position in `checks`)
    prov_of = {c: collections.defaultdict(list) for c in cohorts}
    for c in cohorts:
        for f_ in families[c]:
            for p_ in f_["provisional_names"]:
                prov_of[c][p_].append(f_["name"])
    split = {c: {p_: v for p_, v in sorted(d.items()) if len(v) > 1} for c, d in prov_of.items()}
    split = {c: v for c, v in split.items() if v}
    checks.append(_chk(PROVISIONAL_CHECK, not split, split or {"n_provisional_names": {c: len(d) for c, d in prov_of.items()}}))

    summary = {"n_streams": {c: len(streams[c]) for c in cohorts},
               "n_families": {c: len(families[c]) for c in cohorts},
               "n_multi_member_families": {c: sum(len(f_["members"]) > 1 for f_ in families[c]) for c in cohorts},
               "n_unknown_clock_families": {c: sum(f_["clock"] == "unknown" for f_ in families[c]) for c in cohorts},
               "within_actions": {c: dict(within[c]["n_pairs"]) for c in cohorts},
               "shared_audio": shared_s, "n_cross_overlaps": len(overlaps), "n_cross_unrefined": len(unref_x),
               "n_flagged_streams": {c: len(v) for c, v in cross["flagged_streams"].items()},
               "federici_groups": dict(collections.Counter(r_["clock"] for r_ in fed_recs)),
               "sparrkulee_audiobook_1_ok": None if sk_rep is None else sk_rep["ok"],
               "positive_controls_ok": pc.get("ok") if pc["ran"] else None,
               "n_scene_pairs": {c: sum(sp["attention_swapped"] for sp in v) for c, v in scenes.items()}}
    for c in cohorts:
        within[c]["n_pairs"] = dict(within[c]["n_pairs"])
    assumptions = [{"item": "private_bdf donor overlap with the target's test stimuli", "status": "unverified", "detail": PRIVATE_NOT_SCANNED},
                   {"item": "identity overlap across cohorts", "status": "unverifiable", "detail": "§3.4.5: different sites, countries and "
                    "ages, no shared identifiers; not checked by C3"}]
    return {"cohorts_scanned": cohorts, "checks": checks, "streams": stream_rows, "within": within, "families": families,
            "shared_audio": shared, "shared_audio_seconds": shared_s, "cross_cohort": cross, "sparrkulee_audiobook_1": sk_rep,
            "positive_controls": pc, "scene_pairs": scenes, "federici_natural_vocoded": fed_recs, "assumptions": assumptions,
            "observations": observations, "summary": summary}


# ------------------------------------------------------------------------------------------------ CLI
def _jsonable(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (set, tuple)):
        return sorted(o) if isinstance(o, set) else list(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def clean(o):
    """JSON-safe copy: numpy scalars / arrays to Python, tuples to lists, sets sorted, non-finite floats to None."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, set):
        return [clean(v) for v in sorted(o)]
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, np.generic):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def _write_json(path, obj, mode=0o444):
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(clean(obj), f, sort_keys=True, indent=1, default=_jsonable, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def _log(msg):
    print(msg, flush=True)


def _check_out(out, real):
    """Real sources write only to the design cache root; a --sources config never writes there, under the public data volume, or
    under the repository's docs/, results/ or private/."""
    o = os.path.realpath(out)
    if real:
        if o != os.path.realpath(CACHE_ROOT):
            raise SystemExit(f"scan_audio: with the real sources --out must be the cache root {CACHE_ROOT} (got {out})")
        return o
    bad = [os.path.realpath(PUB)] + [os.path.realpath(os.path.join(REPO, d)) for d in ("docs", "results", "private")]
    if any(o == b or o.startswith(b + os.sep) for b in bad):
        raise SystemExit(f"scan_audio: a --sources run may not write under {out}")
    return o


def builder_sha():
    """sha256 of this file (the builder code hash every output carries)."""
    return _file_sha(os.path.abspath(__file__))


def _doc_ref(path):
    """{file, sha256, created_utc, signature, builder_sha256, ok} of an existing result file, or None."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        raw = f.read()
    try:
        d = json.loads(raw)
    except ValueError:
        d = {}
    d = d if isinstance(d, dict) else {}
    return {"file": os.path.basename(path), "sha256": hashlib.sha256(raw).hexdigest(), "created_utc": d.get("created_utc"),
            "signature": d.get("signature"), "builder_sha256": (d.get("builder") or {}).get("sha256"), "ok": d.get("ok")}


def latest(out):
    """The pointer <out>/scan_audio.latest.json (None if absent or unreadable)."""
    try:
        with open(os.path.join(out, LATEST_NAME)) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def not_current(out):
    """Why <out>/scan_audio.json may not be reused without --force ([] = it may): the pointer must say ok for its sha256 and the
    file's builder sha256 must be this file's."""
    ref, ptr, why = _doc_ref(os.path.join(out, OUT_NAME)), latest(out), []
    if ref is None:
        return [f"no {OUT_NAME}"]
    if ptr is None:
        why.append(f"no readable {LATEST_NAME}")
    elif ptr.get("status") != "ok" or ptr.get("file") != OUT_NAME or ptr.get("sha256") != ref["sha256"]:
        why.append(f"{LATEST_NAME} says status {ptr.get('status')} for {ptr.get('file')} (sha256 {str(ptr.get('sha256'))[:16]}; "
                   f"{OUT_NAME} has {ref['sha256'][:16]})")
    if ref["ok"] is not True:
        why.append(f"{OUT_NAME} has ok = {ref['ok']}")
    if ref["builder_sha256"] != builder_sha():
        why.append(f"{OUT_NAME} was written by builder {str(ref['builder_sha256'])[:16]}, this builder is {builder_sha()[:16]}")
    return why


def _finish(out, ok, doc, log):
    """Write this run's result (scan_audio.json or scan_audio.FAILED.json), then the pointer scan_audio.latest.json naming it. A
    result of the other kind that is still present is recorded as superseded (FAILED after a success) or stale (scan_audio.json
    after a failure); nothing is moved or deleted."""
    path, other = (os.path.join(out, OUT_NAME), os.path.join(out, FAILED_NAME)) if ok else \
                  (os.path.join(out, FAILED_NAME), os.path.join(out, OUT_NAME))
    _write_json(path, doc)
    ref, oref = _doc_ref(path), _doc_ref(other)
    ptr = {"schema": LATEST_SCHEMA, "status": "ok" if ok else "failed", **{k: ref[k] for k in ("file", "sha256", "created_utc", "signature",
                                                                                              "builder_sha256")},
           "superseded" if ok else "stale": oref,
           "rule": f"C6 reads {OUT_NAME} only when this pointer says status ok with sha256 = sha256({OUT_NAME}); otherwise it refuses."}
    _write_json(os.path.join(out, LATEST_NAME), ptr)
    if oref is not None:
        log(f"[scan_audio] {'superseded' if ok else 'STALE'}: {oref['file']} (created {oref['created_utc']}) stays in place; "
            f"{LATEST_NAME} names {ref['file']}")


def empty_cohorts(streams, info, required=COHORTS):
    """{cohort: why} for every required cohort that yielded no KEYED stream ({} = complete), in COHORTS order. A cohort holding only
    non-keyed streams (FAU distractors, DTU maskers) has no family and gives no donor content, so it is as empty as one without any
    stream. why summarises what the loader read (stream counts by kind, skip reasons, failed source checks and its counts), so that
    the error can name the cohort and the cause."""
    out = {}
    for c in required:
        S = streams.get(c) or []
        if any(s.keyed for s in S):
            continue
        i = info.get(c) or {}
        sk = i.get("skipped") or []
        out[c] = {"configured": c in info, "n_streams": len(S), "n_keyed": 0,
                  "stream_kinds": dict(sorted(collections.Counter(s.kind for s in S).items())), "n_skipped": len(sk),
                  "skip_reasons": dict(sorted(collections.Counter(str(s.get("reason")) for s in sk).items())),
                  "failed_source_checks": [x["check"] for x in i.get("checks", []) if not x["ok"]],
                  **{k: i[k] for k in ("n_files", "n_items", "n_shas", "n_inventory_rows") if k in i}}
    return out


def incomplete_error(empty, n_streams=None, n_keyed=None, sources=None, note=None):
    """The ScanError of incomplete real sources (exit 3, raised before any scan). Its message names every required cohort that is
    not configured ('not configured', empty[c] = {configured: false}) or yielded no keyed stream ('yielded no keyed streams'); its
    detail, merged into scan_audio.FAILED.json, holds complete false, empty_cohorts and the failed COMPLETE_CHECK, plus n_streams,
    n_keyed and the loaders' info when the sources were read."""
    absent = [c for c in empty if not empty[c].get("configured", True)]
    nokey = [c for c in empty if c not in absent]
    what = ([f"required cohort(s) {', '.join(absent)} not configured"] if absent else []) + \
        ([f"required cohort(s) {', '.join(nokey)} yielded no keyed streams"] if nokey else [])
    read = n_streams is not None
    counts = {"n_streams": n_streams, "n_keyed": n_keyed} if read else {}
    detail = {"complete": False, "empty_cohorts": list(empty),
              "checks": [_chk(COMPLETE_CHECK, False, {"required": list(COHORTS), "empty": empty, **counts})], **counts}
    if read:
        detail["sources"] = sources
    msg = (f"incomplete sources: {'; '.join(what)} (every cohort of {', '.join(COHORTS)} must be configured and yield at least one "
           f"keyed stream" + (f"; n_streams {json.dumps(n_streams)}; n_keyed {json.dumps(n_keyed)}" if read else "; nothing was read")
           + f"; why {json.dumps(empty, sort_keys=True, default=_jsonable)[:1500]}" + (f"; {note}" if note else "") + ")")
    return ScanError(msg, detail=detail)


def run(cfg, out, *, workers=1, batch_bytes=256 << 20, force=False, require_all=False, log=_log):
    """Load the sources, scan (resumable) and write <out>/scan_audio.json or scan_audio.FAILED.json, then scan_audio.latest.json
    -> exit code 0 (also: a current scan_audio.json exists), 3 (failed) or 4 (an existing scan_audio.json is not current).
    require_all (the real sources): every cohort of COHORTS must be configured and yield at least one keyed stream; a cohort that
    is not configured or has no keyed stream fails the run before any scan (incomplete_error), and the result asserts `complete`
    (COMPLETE_CHECK). On either path a source a loader cannot read fails the run with exit 3 (source_error); RestrictedAccess
    propagates and nothing is written."""
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, OUT_NAME)
    if os.path.exists(final) and not force:
        why = not_current(out)
        if not why:
            log(f"[scan_audio] {final} exists and is current; nothing to do (--force recomputes)")
            return EXIT_OK
        log(f"[scan_audio] {final} exists but is not current: {'; '.join(why)}. Nothing written; --force recomputes")
        return EXIT_NOT_CURRENT
    t0 = time.time()
    head = {"schema": SCHEMA, "contract": C.CONTRACT, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "builder": {"module": "auditory_alignment_v3.prior33.scan_audio", "sha256": builder_sha(),
                        "contract_sha256": _file_sha(C.__file__), "python": platform.python_version(), "numpy": np.__version__,
                        "scipy": scipy.__version__, "host": platform.node(), "slurm_job": os.environ.get("SLURM_JOB_ID")},
            "parameters": PARAMS, "filters": C.filter_shas(), "interpretations": list(INTERPRETATIONS)}
    try:
        streams, info = load_sources(cfg, require_all=require_all)
        n_streams = {c: len(streams.get(c) or []) for c in COHORTS}
        n_keyed = {c: sum(1 for s in streams.get(c) or [] if s.keyed) for c in COHORTS}
        empty = empty_cohorts(streams, info)
        if require_all and empty:          # the real sources: a cohort without a keyed stream must not pass as a smaller scan
            raise incomplete_error(empty, n_streams, n_keyed, info)
        src_checks = [c_ for i in info.values() for c_ in i.get("checks", [])]
        if not all(c_["ok"] for c_ in src_checks if c_["level"] == "assert"):
            raise ScanError("source assertion failed: " + json.dumps([c_ for c_ in src_checks if not c_["ok"]], default=_jsonable)[:2000])
        sig = signature(streams)
        work = os.path.join(out, WORK_NAME, sig[:16])
        log(f"[scan_audio] signature {sig[:16]}; work {work}; workers {workers}")
        res = scan(streams, work_dir=work, workers=workers, batch_bytes=batch_bytes, log=log)
    except ScanError as exc:
        _finish(out, False, {**head, "ok": False, "error": str(exc), **exc.detail}, log)
        log(f"[scan_audio] FAILED: {exc}")
        return EXIT_FAILED
    res["checks"] = src_checks + res["checks"]
    complete = not empty and list(res["cohorts_scanned"]) == list(COHORTS)   # every cohort has a keyed stream (scan(): any stream)
    if require_all:                    # the real sources: the positive controls and completeness are part of the result
        res["checks"].append(_chk("positive controls ran (real sources)", res["positive_controls"]["ran"], res["positive_controls"].get("reason")))
        res["checks"].append(_chk(COMPLETE_CHECK, complete, {"required": list(COHORTS), "n_streams": n_streams, "n_keyed": n_keyed,
                                                             "cohorts_scanned": list(res["cohorts_scanned"])}))
    res["observations"] = [o for i in info.values() for o in i.get("observations", [])] + res["observations"]
    ok = all(c_["ok"] for c_ in res["checks"] if c_["level"] == "assert")
    doc = {**head, "signature": sig, "sources": info, "complete": complete, "ok": ok, "elapsed_s": round(time.time() - t0, 1), **res}
    if not ok:
        _finish(out, False, doc, log)
        log("[scan_audio] FAILED assertions: " + "; ".join(c_["check"] for c_ in res["checks"] if c_["level"] == "assert" and not c_["ok"]))
        return EXIT_FAILED
    _finish(out, True, doc, log)
    warns = [c_["check"] for c_ in res["checks"] if c_["level"] == "warn" and not c_["ok"]]
    log(f"[scan_audio] wrote {final} in {time.time() - t0:.0f} s; {len(warns)} warnings{': ' + '; '.join(warns) if warns else ''}; "
        f"summary {json.dumps(clean(res['summary']), default=_jsonable)[:1500]}")
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(description="C3 audio scan (PUBLIC_PRIOR_DESIGN.md §2.5, §3.4, §6.2 C3). Exit 0: scan_audio.json "
                                             "written (or current); 3: scan_audio.FAILED.json written; 4: an existing scan_audio.json "
                                             "is not current (see scan_audio.latest.json; --force recomputes).")
    ap.add_argument("--out", required=True, help=f"cache root ({CACHE_ROOT} for the real sources)")
    ap.add_argument("--sources", default=None, help="JSON source config (synthetic trees, tests); default: the real cohorts")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")), help="FFT threads")
    ap.add_argument("--batch-mb", type=int, default=256, help="memory per FFT batch (MB)")
    ap.add_argument("--force", action="store_true", help="recompute although scan_audio.json exists (units are reused)")
    a = ap.parse_args(argv)
    real = a.sources is None
    out = _check_out(a.out, real)
    cfg = default_sources() if real else read_json(a.sources)
    return run(cfg, out, workers=max(1, a.workers), batch_bytes=max(1, a.batch_mb) << 20, force=a.force, require_all=real)


if __name__ == "__main__":
    sys.exit(main())
