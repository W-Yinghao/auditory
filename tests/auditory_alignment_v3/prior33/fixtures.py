"""Synthetic E34_PUBLIC_PRIOR manifest, caches and private-like epochs for the prior33 tests (PUBLIC_PRIOR_DESIGN.md §2.5, §3,
§6.2, §6.6 M1). No real data, CPU only, deterministic. make_synthetic_manifest(tmp, scale=1): about 74 MB under `tmp` and about 1 s
at scale 1 (the default); about 295 MB and 4 s at scale 4.

Scale. Every piece and stream is `scale` times longer (the SparrKULee structural anomaly stays 64 samples longer than its
co-listeners), so the pools grow while every participant, presentation, family, cell, mask and data-use case below stays the same.
scale = 1 draws the same random numbers and writes the same arrays, tables and manifest bytes as before the argument existed (only
streams.json and rich_streams.json differ: their provenance fields are new and `origin` now states the design's source). At scale 1
only the SparrKULee core pool holds a design batch. With scale >= 4, every stratum of every donor set and block (sparrkulee, fau,
dtu, federici, fau_cs; after the overlap exclusion) holds at least one design batch (§2.6: 32 listener segments with distinct
(presentation, segment), each with a valid partner, x 8 anchors = 256 anchors and 512 EEG windows of [C, 38]); the build asserts
this (the smallest stratum, fau_cs, holds 44 at scale 4). scale is an integer in 1..MAX_SCALE = 8 (about 590 MB, 8 s and 0.64 GB
RSS at 8; above 10 the audiobook_1 halves +1711 / +30986 would overlap on their family clock). Only a scale other than 1 is
recorded in the manifest (fixture_scale), so the scale-1 manifest stays byte-identical. test_contract.py pins a fingerprint of the
scale-1 build (fingerprint() below, tolerant of float rounding only): a change of the scale-1 output must be deliberate and re-pinned.

Sizes that stay below the design at every scale. Only the donor strata reach design size. The lists and pools below do not, so
M3 / M5 / M6 must take every list and pool size from the manifest (or as a parameter), never the design's count:
  selection.fit_segments  12 SparrKULee donor-fit rows at every scale (design §2.10: 300)
  selection.dev_queries   every dev pool row: 30 / 138 / 282 at scale 1 / 4 / 8, on 15 / 69 / 141 content segments (§2.10: 400)
  bridge.fit_rows         24 rows per donor set at every scale (§2.11: 2,000 listener segments)
  bridge.cal_queries      every bridge_cal pool row: 32 / 140 / 284, on 16 / 70 / 142 content segments (§2.11: 300 queries)
  bridge.cal_split        1 + 1 bridge_cal participants (§2.11: 3 + 3 of 6)
  tau(n) pools            an own candidate plus n - 1 other bridge_cal content segments exist for n = 64 at scale >= 4 and for
                          n = 128 at scale 8 only, never for n = 256, 512 or 1024 (§2.11: n in {64, 128, 256, 512, 1024})
  budget                  N_SK 137 / 623 / 1,271 and S0 129 / 585 / 1,192 (§2.10 design counts: 86,285 and 80,893)

It is the manifest-schema interface of views / sampler (M3) and the test bed of M4-M7 (§7.1 4, 8-10), so each data-use rule of
§2.5 / §3 has a case (`truth` names them):
  sparrkulee  donor only. Roles fit / dev / bridge_cal / holdout_seen_content / control_artefact (audiobook_1_artefact) /
              excluded_rule (a clock-misaligned run; a structural anomaly with an unverifiable clock). The restricted participant
              019 is listed from its file name and .npy header only: no cache rows, no content hash, audit "not_audited". The
              declared audiobook_1 family (+1711 / +30986, a shifted copy, the artefact excerpt); jingles (shared audio, masked);
              QC-masked (run, channel) cells
  fau         the always-train TH half (301, 302) + 5 TH + 5 HA + 5 CI (one per group in every subject fold); 8 single-talker
              codes (core) and 2 competing-talker codes (CSX: presentation = (code, attended side), distractor onset 2.0 s); CI
              interpolated channels masked; a stimulus-locked CI artefact in the noica input (modes B, C)
  dtu         5 NH + 5 HI. NH single-talker shas heard by >= 2 NH, one heard by one (t08), a scan-merged duplicate (t07 = t01
              re-cut, family offset +400). HI audio is equalised per listener: unique presentation on the original's stream and
              family. Two-talker trials, masker onsets 3.0-5.0 s, never donors (one presentation shared by two NH listeners).
              CAR over the 64 channels; content groups with halves and early-stop flags
  federici    5 HC + 2 HC-v (separate identities in the fold of HC N) + 5 CI + 2 phantom sessions (test_only, never donors).
              Families: N1 / V1 natural / vocoded with a known lag (V1 offset +48), N2 / V2 with an unknown clock. HC-v 1001 also
              hears N1 (a would-be HC / HC-v pair beside valid partners); N5 is heard only by HC 1002 and HC-v 1002 (no valid
              partner); N6 has one listener. No waveform, so no rich targets. Mode C_partial
  overlap     FAU code 122 shares a 10 s excerpt with DTU t05: each is removed from the other cohort's donor set (§3.4)
  private     synthetic_kids(): 6 HA + 5 NH children with the auditory_alignment.data.load_private() fields

Layout (paths relative to `tmp`; every JSON is written with sorted keys and relative paths, so builds are byte-identical):
  manifest.json (0444)                  C6 manifest, schema "prior33_manifest_v2"; its sha256 is returned
  P_32x8_seed20261016_f32.npy           P = audio_targets.semi_orthogonal(32, 8, 20261016) (numpy QR of the seed)
  P_ss_32x32_seed20261017_f32.npy, P_sc_32x8_seed20261018_f32.npy   rich projections; rich_pca4_f64.npy [128, 4] (synthetic)
  <cohort>/eeg_f16_tmajor.npy           mode A [N, C] float16, time-major: z per participant x channel over all of its cached
                                        pieces (guards and masked cells excluded), masked cells 0. Rows in role slabs
                                        (SparrKULee fit, dev, bridge_cal, holdout_seen_content, control_artefact, excluded_rule;
                                        other cohorts fit = donor-usable pieces, then target_only)
           eeg_noica_z_f16_tmajor.npy   FAU mode B (noica, z)
           eeg_raw_f16_tmajor.npy       FAU mode C (noica), DTU mode C (after CAR), Federici mode C_partial; uV, masked cells 0
           runs.json | pieces.json      {"participants": [...], "runs" | "pieces": [...]}
           env_f32.npy, streams.json    every stream's 2-8 Hz RMS-normalised envelope at its own origin, concatenated [M]
           rich_f32.npy, rich_streams.json   [M, 5] (contract.RICH_COLS) aligned with env_f32.npy, NaN rows where unavailable
  raw/sparrkulee/sub-019_*_eeg.npy      the restricted decoy (never to be opened by a builder, view or sampler)

Tables:
  participants  participant, uid (cohort:participant), identity (fold key; Federici HC N and HC-v N share N), group, fold, dev
                (FAU always-train), test_only (phantom), donor, masked [names], mu {mode: [C]}, sd_prez {mode: [C]} (pre-z SD in
                uV, None where a channel has no unmasked sample); SparrKULee: sub, role; FAU: cs_side {code: side}
  runs/pieces   piece_id, participant, uid, group, fold, dev, test_only, trial, kind (ss / cs), stimulus (content id: FAU code,
                DTU target sha, Federici item, SparrKULee stimulus), ignored_stimulus, content_group, presentation, family,
                family_offset, stream, ignored_stream, ignored_lead (piece sample of the ignored stream's index 0), attended_side,
                onset_s (starts = contract.segment_starts(T_env, T_eeg, cohort, onset_s)), role, slab, row_offset (None: never
                cached), T_eeg, T_env, segment_starts, masked [names]. SparrKULee runs add run_id, sub, condition, snr, flags,
                audit (C2), source_sha256 (the run file's sha256, Source hashes below; None: never read) and, for the
                restricted run, raw_file
  streams       stream, name, kind (attended / distractor / masker / item), offset, length, family, family_offset (None for
                ignored-only streams), rms (the stream RMS about 0 that rms_norm divided by), and the envelope provenance that the
                inherited contract §3 asks for (envelopes from original audio and from author caches each record origin, original
                band and filter hash; design §2.3 "origin and band are recorded per source"):
                  origin          who extracted the envelope from what, as design §2.3 states it for the cohort (ENV_SOURCE),
                                  marked "(synthetic stand-in)"
                  original_band   the band of that envelope before our 2-8 Hz filter (ENV_SOURCE)
                  fs_source       its sampling rate (SparrKULee 64, FAU 128, DTU 128, Federici 100 Hz)
                  filter_sha256   {aa_fir_<fs_source>: full sha256 (absent at 64 Hz), env_sos: full sha256}, the filters applied in
                                  the contract order h_aa resampling -> 2-8 Hz band-pass -> rms_norm (values as manifest.filters)
                  source_sha256   the hash of the source as stored (Source hashes below; ENV_SOURCE_FORM): a SparrKULee stream
                                  is a whole file (the file's sha256), a FAU / DTU / Federici stream an array inside a
                                  container (array_sha256 of the source envelope as read)
                  nan_count       NaNs in the source before nan_to_num (design §2.3 records it for FAU; 0 here)
  rich_streams  stream, name, available, clock_lag, reason, extractor, source_sha256. source_sha256 (design §2.15, §6.2 C7: the
                source sha of the stream's waveform file, a whole file) is None exactly when no waveform is read (reason in
                NO_SOURCE: no_waveform, no_waveform_competing_talker, not_a_target_stream, not_nh_original); a file that is read
                and then rejected (waveform_unavailable) or masked by the clock check (clock_lag) keeps its sha (READ_MASKED);
                available exactly when reason is None. The reasons are C7's (build_rich.py REASONS) without its dry-run-only
                not_selected_dry_run, which never reaches a cache root. No fixture stream is not_nh_original: C7 gives it to a
                DTU stream heard only by HI listeners (a woa original), while the fixture's HI trials reuse the NH originals.
Source hashes (design §6.2 C1 "the sha256 of each source file" and C7 "source sha", beside the inherited contract §3 / design §2.3
  provenance; one rule for every table and builder, so that C6 compares like with like): source_sha256 is the sha256 of the source
  as it is stored.
  - A source that is a whole file (a SparrKULee <stim>_envelope.npy or EEG run, a waveform .wav or .npz.gz): the sha256 of the
    file's bytes as read.
  - A source that is a dataset or a row inside a container file (the FAU and DTU h5 envelope datasets, a Federici block row):
    array_sha256(raw), the sha256 of the C-order float64 bytes of the flattened array as read, before nan_to_num. A float32
    dataset is cast to float64 first, so the value depends on the values only, not on the stored dtype, byte order or shape.
  A builder may record the other kind of hash under another key (build_sparrkulee.py: source_array_sha256), never under
  source_sha256. Every value here is a synthetic stand-in whose bytes the returned `sources` holds: SparrKULee streams hash an
  in-memory .npy of the (T, 1) envelope (`file`), FAU / DTU / Federici streams their raw float64 envelope (`env`), rich rows the
  float32 bytes of the synthetic features or a stand-in string for the rejected file (`waveform`). runs.json keeps the sha256 of
  the synthetic run's float64 bytes as its stand-in for the C1 file sha.
Standardiser (design §2.3; contract.py docstring "Standardiser"): sigma[d] = sqrt(mean y[d]^2), the RMS about 0 and not the SD about
  the mean, over the unique (presentation, tick) windows of the SparrKULee core (donor-fit) pool, each window once whatever its
  listener count (n_windows = 250 x the distinct content segments). mu is fixed at 0 and stored as zeros; the sample mean is
  recorded only as mu_estimate (and abs_mu_over_sigma_max; C6 checks < 0.05). The rich sigma_ss [32] (8 samples x 4 dimensions,
  sample-major) and sigma_sc [8] follow the same rule over the windows of the rich-available SparrKULee streams.
Manifest keys: schema, contract, synthetic, fixture_scale (only when scale != 1), builder_sha256, constants, filters, target_contract,
  projection, standardiser {sigma[8] (RMS about 0), mu[8] = 0, mu_estimate, abs_mu_over_sigma_max, n_windows}, rich {columns,
  y_layout, pca4, P_ss, P_sc, sigma_ss[32], sigma_sc[8] (RMS about 0), mu_estimate_ss, mu_estimate_sc, n_windows, loss_weights},
  vocab, aliases, montages, cohorts {name: {dir,
  fs_native, n_ch, layout, reference, band, guards, s_first, n_rows, caches {mode: file}, table, items, env, streams, rich,
  rich_streams, role_slabs {slab: [row0, row1)}, unit {name, basis}, masked_cells}}, families [{id, cohort, name, clock (known |
  unknown), basis, members}], presentations [{id, cohort, stimulus, family, family_offset, offset_known, kind, condition,
  attended_side, stream, ignored_stream, ignored_lead, onset_s}], shared_audio [{cohort, presentation, span [a, b)}], overlap,
  partner_exclusions [[cohort, a, b]], hc_hcv_excluded_pairs, segments, pools, donor_sets, budget, selection, bridge, seen,
  coverage, cells, mode_c, exclusions, unused, dtu_reconciliation.
  segments {cohort: columns piece, participant, presentation, family, s, role, kind, n_listeners, n_partners}: every listener
    segment of every cached piece after the guards, the onset rule and the shared-audio mask (`piece` indexes the cohort table);
    n_listeners = participants with the same (presentation, s, role); n_partners = valid partners among them (not self, not an
    excluded HC / HC-v twin), 0 outside the donor roles fit / dev / bridge_cal
  pools {core: {cohort: rows}, csx: {fau_cs: rows}, dev: {sparrkulee}, bridge_cal: {sparrkulee}}: rows with n_partners >= 1 (the
    rich block uses the core pools); donor_sets {target: {core | rich | csx: {strata, weights, n_segments, excluded_presentations
    {stratum: [ids]}}}}: weights and counts after the overlap exclusion; no csx block for target fau
NCE semantics the fixture encodes: positive = equal keys; masked = same family, |ds| <= 128 and not positive, and for a family whose
clock is "unknown" also every pair of different presentations of that family at any time.
Returned dict: root, manifest_path, manifest_sha256, manifest, kids, P, P_rich {ss, sc}, truth (ground truth for tests), scale and
sources {cohort: [one dict per stream, in stream order: name, fs (source rate in Hz), env (the raw source envelope at fs, float64,
read-only), file (the stand-in source-file bytes, or None), waveform (the stand-in waveform bytes, or None)]}, from which the tests
recompute every provenance value.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os

import numpy as np

from auditory_alignment_v3.prior33 import contract as C

SCHEMA = "prior33_manifest_v2"
LAG = 6                                     # synthetic neural lag, 64 Hz samples
L_SK = 2880                                 # SparrKULee runs: 45 s at 64 Hz (x scale)
L_FAU, L_DTU, L_FED = 1024, 1280, 1920      # 64 Hz piece lengths: FAU 16 s and DTU 20 s at 128 Hz, Federici blocks 30 s at 100 Hz (x scale)
MAX_SCALE = 8                               # scale 1..8: size; above 10 the audiobook_1 halves would overlap on their family clock
BATCH_SEGMENTS = 32                         # §2.6 design batch: 32 listener segments x 8 anchors x 2 listeners = 256 anchors, 512 windows
ENV_SOURCE = {  # design §2.3 Sources, per cohort: (origin, original band, source rate in Hz); every fixture stream is a stand-in for it
    "sparrkulee": ("authors' pipeline: derivatives/preprocessed_stimuli/<stim>_envelope.npy (T, 1) at 64 Hz; the extractor was neither "
                   "run nor verified", "broadband: +11 dB at 0.5 Hz, -4 dB at 8 Hz, relative to 3-7 Hz", 64),
    "fau": ("authors' 1 kHz envelope (method undocumented), copied by us at 128 Hz: c3_preproc_v1/fau_tud/stimulus_env_128.h5 "
            "<code>/{attended,distractor}_env/raw", "about 0.3-9 Hz with a steep low-pass", 128),
    "dtu": ("ours: abs(Hilbert) of the original unequalised 16 kHz audio (HI trials point to the woa originals): "
            "c3_features_v1/dtu/kcs_targets_v1/audio_local.h5 <sha>/env", "broadband", 128),
    "federici": ("authors' cache: block env (AudioEnvSp, not normalised)", "low-pass only (-3 dB at about 6.9 Hz), not high-passed", 100),
}
ENV_SOURCE_FORM = {"sparrkulee": "file", "fau": "array", "dtu": "array", "federici": "array"}   # what streams.source_sha256 hashes:
#   a whole file (<stim>_envelope.npy) or an array inside a container (FAU / DTU h5 dataset, Federici block row); Source hashes
NO_SOURCE = ("no_waveform", "no_waveform_competing_talker", "not_a_target_stream", "not_nh_original")  # rich reasons for which no
#   waveform is read (build_rich.NO_SOURCE without the dry-run-only not_selected_dry_run; DTU HI-only streams: not_nh_original)
READ_MASKED = ("waveform_unavailable", "clock_lag")   # rich reasons for which the waveform is read, then the stream masked (C7)
JINGLE, MARGIN = 192, 32                    # shared intro (3 s) and the 0.5 s mask margin
DONOR_ROLES = ("fit", "dev", "bridge_cal")
DONORS = {"fau": ("sparrkulee", "dtu", "federici"), "dtu": ("sparrkulee", "fau", "federici"), "federici": ("sparrkulee", "fau", "dtu"),
          "private_bdf": ("sparrkulee", "fau", "dtu", "federici")}       # leave the target cohort out (§3.1)

SK_STIMS = [  # stimulus, family, family offset, listeners; roles follow the listeners' session blocks
    ("audiobook_1_1", "audiobook_1", 1711, ("001", "002", "003")),
    ("audiobook_1_2", "audiobook_1", 30986, ("001", "002", "004")),
    ("audiobook_1_shifted", "audiobook_1", 1711, ("003", "004")),
    ("audiobook_2_1", "audiobook_2_1", 0, ("001", "002", "004")),
    ("podcast_1", "podcast_1", 0, ("001", "002", "003", "004")),
    ("podcast_2", "podcast_2", 0, ("001", "003", "004")),
    ("audiobook_11_1", "audiobook_11_1", 0, ("051", "052")),
    ("podcast_16", "podcast_16", 0, ("051", "052")),
    ("audiobook_13_1", "audiobook_13_1", 0, ("061", "062")),
    ("podcast_24", "podcast_24", 0, ("061", "062")),
    ("audiobook_1_artefact", "audiobook_1", 2351, ("002",)),
]
SK_JINGLE = ("podcast_1", "podcast_2", "podcast_16")
SK_ROLE = {**{s: "fit" for s in ("001", "002", "003", "004", "005")}, "051": "dev", "052": "dev", "061": "bridge_cal",
           "062": "bridge_cal", "019": "restricted"}
SK_EXTRA = [("051", "audiobook_1_1", "holdout_seen_content", None), ("005", "audiobook_2_1", "excluded_rule", "clock_misaligned"),
            ("005", "podcast_2", "excluded_rule", "structural_anomaly_unverified_clock"), ("019", "podcast_1", "restricted", None)]
SK_PLANT = {("004", "podcast_2"): ("Iz", 0.01), ("001", "audiobook_2_1"): ("T8", 30.0)}     # QC rule: flat / loud channel
SK_RICH = {"podcast_1": (1, None), "podcast_2": (3, "clock_lag"), "audiobook_2_1": (None, "waveform_unavailable")}  # lag, reason
SK_SLABS = ("fit", "dev", "bridge_cal", "holdout_seen_content", "control_artefact", "excluded_rule")
SLABS = ("fit", "target_only")

FAU_DEV = ("301", "302")                    # always-train TH selection half
FAU_P = {"th": ("303", "305", "306", "307", "308"), "ha": ("201", "202", "203", "204", "205"), "ci": ("101", "102", "103", "104", "105")}
FAU_SS = ("111", "112", "113", "114", "121", "122", "123", "124")
FAU_CS = ("215", "227")
FAU_LEAD_S = 2.0
FAU_MASK = {"101": ("CP5", "CP6"), "102": ("P7",)}
FAU_CF = {0: {"ss": {"fit": "1", "es": "2", "test": "34"}, "cs": {"fit": "05", "es": "6", "test": "789"}},
          1: {"ss": {"fit": "3", "es": "4", "test": "12"}, "cs": {"fit": "78", "es": "9", "test": "056"}}}

DTU_NH = {"sub-021": ("t01", "t02", "t03", "t07"), "sub-022": ("t01", "t02", "t04", "t07"), "sub-023": ("t03", "t04", "t05", "t06"),
          "sub-024": ("t05", "t06", "t01", "t08"), "sub-025": ("t02", "t03", "t05", "t06")}
DTU_HI = {"sub-001": ("t01", "t02", "t03", "t04"), "sub-002": ("t03", "t04", "t05", "t06"), "sub-003": ("t01", "t05", "t06", "t02"),
          "sub-004": ("t02", "t03", "t04", "t05"), "sub-005": ("t01", "t06", "t03", "t04")}
DTU_CS = {"sub-021": ("t02", "m01", 3.25), "sub-022": ("t02", "m01", 3.25), "sub-023": ("t04", "m02", 3.625),
          "sub-024": ("t02", "m02", 4.1), "sub-025": ("t04", "m01", 4.975), "sub-001": ("t02", "m02", 3.0),
          "sub-002": ("t04", "m01", 3.8125), "sub-003": ("t02", "m01", 4.4375), "sub-004": ("t04", "m02", 3.0625),
          "sub-005": ("t02", "m02", 5.0)}   # target, masker, masker onset (s)
DTU_DUP = ("t01", "t07", 400)               # t07 = t01 re-cut 400 samples (6.25 s) later: merged by the duplicate scan
DTU_GROUP = {"t01": 0, "t07": 0, "t02": 1, "t03": 2, "t04": 3, "t05": 4, "t06": 5, "t08": 6}
DTU_SPLIT = {0: (0, False), 1: (1, False), 2: (0, True), 3: (1, True), 4: (0, False), 5: (1, False), 6: (0, False)}  # half, es

FED_HEAR = {"HC:1001": ("N1", "N3", "N4"), "HC:1002": ("N1", "N5", "N4"), "HC:1003": ("N2", "N3", "N4"), "HC:1004": ("N1", "N2", "N3"),
            "HC:1005": ("N2", "N3", "N4"), "HC-v:1001": ("V1", "V2", "N1"), "HC-v:1002": ("V1", "V2", "N5"),
            "CI:0001": ("N1", "N2", "N4"), "CI:0002": ("N2", "N3", "N6"), "CI:0003": ("N1", "N3", "N4"), "CI:0004": ("N1", "N2", "N4"),
            "CI:0005": ("N2", "N3", "N4"), "Artifact:01": ("N1", "N3", "N4"), "Artifact:02": ("N2", "N4", "N3")}
FED_ITEMS = {"N1": ("g0", "natural"), "V1": ("g0", "vocoded"), "N2": ("g1", "natural"), "V2": ("g1", "vocoded"),
             "N3": ("N3", "natural"), "N4": ("N4", "natural"), "N5": ("N5", "natural"), "N6": ("N6", "natural")}
FED_LAG100, FED_LAG = 75, 48                # V1 index 0 = N1 index 75 at 100 Hz = 48 at 64 Hz (known clock)
FED_CG = {"N1": 0, "V1": 0, "N2": 1, "V2": 1, "N3": 2, "N4": 3, "N5": 4, "N6": 5}
FED_ROLE = {0: "fit", 1: "fit", 2: "es", 3: "test", 4: "fit", 5: "test"}
OVERLAP = (("fau", "122", 256), ("dtu", "t05", 640), 1280)       # shared 10 s excerpt: (cohort, stimulus, 128 Hz start) x 2, length


def _j(o):
    return o.tolist() if hasattr(o, "tolist") else str(o)


def _dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=True, default=_j)


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def array_sha256(raw):
    """source_sha256 of a source that is a dataset or a row inside a container file (module docstring, Source hashes): sha256 of
    the C-order float64 bytes of the flattened array as read, before nan_to_num (any stored dtype is cast to float64 first)."""
    return _sha_bytes(np.ascontiguousarray(np.asarray(raw, dtype=np.float64).reshape(-1)).tobytes())


def npy_bytes(a):
    """The bytes of `a` written as a .npy file (np.save, allow_pickle=False): the fixture's stand-in for a whole source file."""
    buf = io.BytesIO()
    np.save(buf, np.asarray(a), allow_pickle=False)
    return buf.getvalue()


def _folds(ids_by_group, seed=C.FOLD_SEED, n=5):
    """auditory_alignment.data._folds: per group, a seeded permutation of the sorted ids, fold = rank % n (FAU, DTU, Federici)."""
    rng = np.random.default_rng(seed); out = {}
    for g in sorted(ids_by_group):
        ids = sorted(ids_by_group[g])
        for p_, i in enumerate(rng.permutation(len(ids))):
            out[ids[i]] = p_ % n
    return out


def _hc_folds(kids, seed=C.FOLD_SEED, n=5):
    """auditory_c3.c3dl.hc.folds: as _folds, but the ids of a group stay in kid order (private_bdf)."""
    rng = np.random.default_rng(seed); out = {}
    for g in sorted({k["group"] for k in kids}):
        ids = [k["id"] for k in kids if k["group"] == g]
        for p_, i in enumerate(rng.permutation(len(ids))):
            out[ids[i]] = p_ % n
    return out


def _semi_orthogonal(d, n, seed):
    """auditory_alignment_v2.audio_targets.semi_orthogonal(d, n, seed) as a float32 numpy array (numpy QR of the seed)."""
    q, _ = np.linalg.qr(np.random.default_rng(seed).standard_normal((max(d, n), min(d, n))))
    return (q.T if n >= d else q).astype(np.float32)


def _raw_env(rng, n, fs):
    k = np.hanning(max(3, fs // 8)); k /= k.sum()
    return np.convolve(np.abs(rng.standard_normal(n)), k, mode="same") + 0.05


def _rich(rng, n):
    """[n, 5] synthetic spectral structure (4 smooth PCA courses) and change (flux = |first difference|), 2-8 Hz, RMS 1 each."""
    k = np.hanning(8); k /= k.sum()
    pca = np.stack([np.convolve(rng.standard_normal(n), k, mode="same") for _ in range(4)], 1)
    flux = np.r_[0.0, np.linalg.norm(np.diff(pca, axis=0), axis=1)]
    return C.rms_norm(C.band(np.c_[pca, flux], C.env_sos()[0], axis=0), axis=0).astype(np.float32)


def _response(en, T, lag=LAG, lead=0):
    """r[t] = en[t - lead - lag] where defined (EEG follows the sound by `lag`; the stream starts at piece sample `lead`), else 0."""
    i = np.arange(T) - lead - lag; ok = (i >= 0) & (i < len(en)); r = np.zeros(T)
    r[ok] = en[i[ok]]
    return r


def _qc_mask(x):
    sd = x.std(1); med = np.median(sd)
    return np.flatnonzero((sd > 10 * med) | (sd < 0.1 * med))


def _zstats(arrs, masks, g):
    """Per channel mean / SD over the pieces' guarded spans [g, T - g), masked (piece, channel) cells excluded (data._stdz
    semantics); SD NaN where a channel has no unmasked sample."""
    n_ch = arrs[0].shape[0]; mu, sd = np.zeros(n_ch), np.full(n_ch, np.nan)
    for c in range(n_ch):
        v = [a[c, g:a.shape[1] - g] for a, m in zip(arrs, masks) if c not in m]
        if v:
            v = np.concatenate(v); mu[c], sd[c] = v.mean(), v.std()
    return mu, sd


def _z(a, mu, sd, masked):
    z = (a - mu[:, None]) / np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)[:, None]
    z[sorted(masked)] = 0
    return z


def _nan_none(a):
    return [float(v) if np.isfinite(v) else None for v in a]


def _unmasked(starts, spans):
    """Segment starts whose EEG span [s, s + 357) meets no masked shared-audio span [a, b)."""
    return [int(s) for s in starts if not any(a < s + C.SPAN_EEG and s < b for a, b in spans)]


class _Registry:
    """Global family and presentation ids: one id space over every cohort."""

    def __init__(self):
        self.fams, self.pres = [], []

    def family(self, cohort, name, clock="known", basis="own"):
        for f in self.fams:
            if f["cohort"] == cohort and f["name"] == name:
                return f["id"]
        self.fams.append({"id": len(self.fams), "cohort": cohort, "name": name, "clock": clock, "basis": basis, "members": []})
        return len(self.fams) - 1

    def presentation(self, cohort, stimulus, fid, off, stream, kind="ss", condition="single", side=None, ign=None, ign_lead=0,
                     onset=None, known=True):
        p = {"id": len(self.pres), "cohort": cohort, "stimulus": stimulus, "family": fid, "family_offset": int(off), "offset_known": known,
             "kind": kind, "condition": condition, "attended_side": side, "stream": stream, "ignored_stream": ign,
             "ignored_lead": int(ign_lead), "onset_s": onset}
        self.pres.append(p); self.fams[fid]["members"].append(p["id"])
        return p["id"]


class _Streams:
    """One cohort's env_f32.npy / streams.json and rich_f32.npy / rich_streams.json (provenance fields: module docstring), and
    the stand-in sources that the provenance values hash (`sources`)."""

    def __init__(self, cohort, filters):
        self.cohort, self.filters = cohort, filters
        self.rows, self.env, self.rich, self.rich_rows, self.sources, self.n = [], [], [], [], [], 0

    def add(self, name, raw, kind, family=None, family_offset=0, rich=None, clock_lag=None, reason=None):
        """`raw`: the stream's source envelope at the cohort's source rate (ENV_SOURCE) -> h_aa to 64 Hz, 2-8 Hz, RMS 1. `reason`: C7's
        rich reason (NO_SOURCE or READ_MASKED; None: available). build_rich.py's row rule (available exactly when the reason is
        None, source_sha256 None exactly for a NO_SOURCE reason) holds for every row: a stream without rich features carries a
        no-source reason or waveform_unavailable (its file read and rejected); clock_lag masks features that were computed."""
        assert reason is None or reason in NO_SOURCE + READ_MASKED, f"{self.cohort}:{name}: reason {reason!r} is not C7's"
        assert rich is not None or reason in NO_SOURCE + ("waveform_unavailable",), \
            f"{self.cohort}:{name}: a stream without rich features needs a no-source reason or waveform_unavailable, not {reason!r}"
        origin, band_, fs = ENV_SOURCE[self.cohort]
        raw = np.asarray(raw, dtype=np.float64)
        en, rms = C.rms_norm(C.band(C.resample64(raw, fs), C.env_sos()[0]), return_rms=True); en = en.astype(np.float32)
        sid = len(self.rows)
        chain = ([f"aa_fir_{fs}"] if fs != C.FS else []) + ["env_sos"]
        if ENV_SOURCE_FORM[self.cohort] == "file":     # a whole file: the sha256 of its bytes (stand-in: the .npy of the (T, 1) stream)
            file_ = npy_bytes(raw.reshape(-1, 1)); src_sha = _sha_bytes(file_)
        else:                                          # an array inside a container: the float64 array sha
            file_, src_sha = None, array_sha256(raw)
        self.rows.append({"stream": sid, "name": name, "kind": kind, "offset": self.n, "length": len(en), "family": family,
                          "family_offset": None if family is None else int(family_offset), "rms": rms,
                          "origin": f"{origin} (synthetic stand-in)", "original_band": band_, "fs_source": fs,
                          "filter_sha256": {k: self.filters[k] for k in chain}, "source_sha256": src_sha,
                          "nan_count": int(np.isnan(raw).sum())})
        ok = rich is not None and reason is None
        self.rich.append(rich if ok else np.full((len(en), len(C.RICH_COLS)), np.nan, np.float32))
        if reason in NO_SOURCE:                        # no waveform is read
            wav = None
        elif rich is not None:                         # the waveform's stand-in: the float32 bytes of its synthetic features
            wav = np.ascontiguousarray(rich, dtype=np.float32).tobytes()
        else:   # the file is read (hashed) and rejected: waveform_unavailable
            wav = f"synthetic stand-in for the rejected source file of {self.cohort}:{name}".encode()
        self.rich_rows.append({"stream": sid, "name": name, "available": ok, "clock_lag": clock_lag, "reason": reason,
                               "extractor": "synthetic whisper_logmel128 pca4 + flux (fixture)" if rich is not None else None,
                               "source_sha256": None if wav is None else _sha_bytes(wav)})
        env_src = raw.copy(); env_src.setflags(write=False)
        self.sources.append({"name": name, "fs": fs, "env": env_src, "file": file_, "waveform": wav})
        self.env.append(en); self.n += len(en)
        return sid

    def save(self, d):
        np.save(os.path.join(d, "env_f32.npy"), np.concatenate(self.env))
        np.save(os.path.join(d, "rich_f32.npy"), np.concatenate(self.rich))
        _dump({"streams": self.rows}, os.path.join(d, "streams.json"))
        _dump({"streams": self.rich_rows}, os.path.join(d, "rich_streams.json"))


def _piece(cohort, p, trial, pr, T_eeg, T_env, role, stimulus, content_group=None, ignored_stimulus=None):
    return {"piece_id": f"{cohort}:{p['participant']}:{trial}", "participant": p["participant"], "uid": p["uid"], "group": p["group"],
            "fold": p["fold"], "dev": p["dev"], "test_only": p["test_only"], "trial": trial, "kind": pr["kind"], "stimulus": stimulus,
            "ignored_stimulus": ignored_stimulus, "content_group": content_group, "presentation": pr["id"], "family": pr["family"],
            "family_offset": pr["family_offset"], "stream": pr["stream"], "ignored_stream": pr["ignored_stream"],
            "ignored_lead": pr["ignored_lead"], "attended_side": pr["attended_side"], "onset_s": pr["onset_s"], "role": role,
            "slab": role, "row_offset": None, "T_eeg": int(T_eeg), "T_env": int(T_env), "masked": list(p["masked"]),
            "segment_starts": C.segment_starts(T_env, T_eeg, cohort, onset=pr["onset_s"]).tolist()}


def _write_cache(d, pieces, arrays, slabs, modes):
    """Row offsets in slab order (then table order); writes one [N, C] float16 time-major cache per mode -> (N, role_slabs)."""
    order = sorted(range(len(pieces)), key=lambda i: (slabs.index(pieces[i]["slab"]), i))
    off, rs = 0, {}
    for i in order:
        q = pieces[i]; q["row_offset"] = off; a = rs.setdefault(q["slab"], [off, off]); off += q["T_eeg"]; a[1] = off
    for m in modes:
        np.save(os.path.join(d, C.CACHE_FILE[m]), np.concatenate([arrays[i][m] for i in order]))
    return off, rs


def synthetic_kids(seed=20261009, n_ha=6, n_nh=5, n_blocks=5, per_block=8):
    """Private-like children with the fields of auditory_alignment.data.load_private(): x [n, 20, 200] float32 at 250 Hz (onset at
    index 50, z-scored per child x channel as hc.load_children), y, bin, block, ev, swap (hc.add_swaps rule), fold (hc.folds: kid
    order within each group), es_mask (last 20 % of the physical blocks), group, ages. Deviants carry an evoked deflection
    150-300 ms after the onset. With the defaults every fold holds >= 1 HA and exactly 1 NH test child."""
    rng = np.random.default_rng(seed); kids = []
    t = (np.arange(C.PRIVATE_EPOCH) - C.PRIVATE_ONSET) / C.FS_PRIVATE
    erp = np.exp(-0.5 * ((t - 0.22) / 0.04) ** 2)
    topo = rng.standard_normal(20)
    for i in range(n_ha + n_nh):
        n = n_blocks * per_block
        y = (rng.random(n) < 0.25).astype(np.int64); y[:2] = (0, 1)
        x = rng.standard_normal((n, 20, C.PRIVATE_EPOCH)) + 1.5 * y[:, None, None] * topo[None, :, None] * erp[None, None]
        mu = x.mean(axis=(0, 2), keepdims=True); sd = x.std(axis=(0, 2), keepdims=True)
        k = {"id": f"child{i + 1}", "group": "HA" if i < n_ha else "NH", "rid": f"rec{i + 1}", "x": ((x - mu) / sd).astype(np.float32),
             "y": y, "bin": rng.integers(0, 6, n).astype(np.int64), "block": np.repeat(np.arange(n_blocks), per_block).astype(np.int64),
             "ev": rng.standard_normal(n).astype(np.float32), "age_months": float(40 + 5 * i),
             "duration_months": float(10 + i) if i < n_ha else None}
        kids.append(k)
    srng = np.random.default_rng(20261007)
    for k in kids:  # hc._mismatch_index: same bin, different physical block (fallback: same bin)
        idx, strict = np.empty(len(k["y"]), int), 0
        for i in range(len(k["y"])):
            c = np.flatnonzero((k["bin"] == k["bin"][i]) & (k["block"] != k["block"][i]))
            strict += bool(len(c))
            if not len(c):
                c = np.flatnonzero((k["bin"] == k["bin"][i]) & (np.arange(len(k["y"])) != i))
            idx[i] = srng.choice(c) if len(c) else i
        k["swap"], k["swap_strict_fraction"] = idx, strict / len(k["y"])
    folds = _hc_folds(kids)
    for k in kids:
        k["fold"] = folds[k["id"]]
        b = np.unique(k["block"])
        k["es_mask"] = np.isin(k["block"], b[int(np.floor(0.8 * len(b))):] if len(b) >= 3 else [])
    return kids


def make_synthetic_manifest(tmp, scale=1, perturb=None):
    """Build the synthetic manifest and caches under `tmp` (module docstring). `scale` (an integer in 1..MAX_SCALE) makes every
    piece and stream `scale` times longer; with scale >= 4 every donor stratum holds a §2.6 design batch (module docstring, Scale).
    `perturb` {(cohort, participant): factor} multiplies that participant's first piece by `factor` before any statistic (§7.1 9:
    target statistics vs the mode-C scale)."""
    if isinstance(scale, (bool, np.bool_)) or not isinstance(scale, (int, np.integer)):
        raise TypeError(f"make_synthetic_manifest: scale must be an integer, got {scale!r}")
    if not 1 <= scale <= MAX_SCALE:
        raise ValueError(f"make_synthetic_manifest: scale must lie in [1, {MAX_SCALE}], got {scale!r}")
    scale = int(scale)
    lsk, lfau, ldtu, lfed = L_SK * scale, L_FAU * scale, L_DTU * scale, L_FED * scale
    root = str(tmp); os.makedirs(root, exist_ok=True)
    perturb = dict(perturb or {})
    rng = np.random.default_rng(20261016)
    reg, shared, exclusions, tables, slabs_of, n_rows = _Registry(), [], [], {}, {}, {}
    stream_tab, parts_of, filters = {}, {}, C.filter_shas()

    # ------------------------------------------------------------------------------------------------ SparrKULee-like donor
    sk_dir = os.path.join(root, "sparrkulee"); os.makedirs(sk_dir, exist_ok=True)
    sk = _Streams("sparrkulee", filters); master = _raw_env(rng, 30986 + lsk + 64, C.FS); jingle = _raw_env(rng, JINGLE, C.FS); s_of = {}
    for stim, fname, off, _ in SK_STIMS:
        e = master[off:off + lsk].copy() if fname == "audiobook_1" else _raw_env(rng, lsk, C.FS)
        if stim == "audiobook_1_shifted":
            e = 0.8 * e + 0.05 * _raw_env(rng, lsk, C.FS)
        if stim in SK_JINGLE:
            e[:JINGLE] = jingle
        fid = reg.family("sparrkulee", fname, basis="declared" if fname == "audiobook_1" else "own")
        lag, why = SK_RICH.get(stim, (0, None))
        sid = sk.add(stim, e, "attended", fid, off, rich=None if why == "waveform_unavailable" else _rich(rng, lsk), clock_lag=lag,
                     reason=why)
        s_of[stim] = reg.presentation("sparrkulee", stim, fid, off, sid, condition="listeningActive")
        if stim in SK_JINGLE:
            shared.append({"cohort": "sparrkulee", "presentation": s_of[stim], "span": [0, JINGLE + MARGIN]})
    runs = [(sub, stim, "control_artefact" if stim == "audiobook_1_artefact" else SK_ROLE[sub], None)
            for stim, _, _, subs in SK_STIMS for sub in subs] + SK_EXTRA
    runs.sort(key=lambda r: (SK_SLABS.index(r[2]) if r[2] in SK_SLABS else len(SK_SLABS), r[0], r[1]))
    gain = rng.standard_normal(64); data, masks, recs = {}, {}, []
    for sub, stim, role, rule in runs:
        pr = reg.pres[s_of[stim]]; en = sk.env[pr["stream"]]
        T = lsk + (64 if rule == "structural_anomaly_unverified_clock" else 0)
        x = np.outer(gain * rng.uniform(0.5, 1.5), _response(en, T, LAG - 566 if rule == "clock_misaligned" else LAG))
        x = (x + 2.0 * rng.standard_normal((64, T))) * rng.uniform(5, 20, 64)[:, None]
        if (sub, stim) in SK_PLANT:
            ch, f = SK_PLANT[(sub, stim)]; x[C.BIOSEMI64.index(ch)] *= f
        p = {"participant": sub, "uid": f"sparrkulee:{sub}", "group": "sparrkulee", "fold": -1, "dev": False, "test_only": False, "masked": ()}
        rec = _piece("sparrkulee", p, stim, pr, T, len(en), role, stim)
        rec.update(run_id=f"sub-{sub}_{stim}", sub=sub, condition="listeningActive", snr=None, flags=[rule] if rule else [])
        if role == "restricted":  # listed from the file name and the .npy header only: never opened, hashed or audited
            rel = os.path.join("raw", "sparrkulee", f"sub-{sub}_ses-x_task-listeningActive_run-01_desc-preproc-audio-{stim}_eeg.npy")
            os.makedirs(os.path.join(root, os.path.dirname(rel)), exist_ok=True); np.save(os.path.join(root, rel), x)
            rec.update(raw_file=rel, source_sha256=None, audit={"clock": "not_audited", "reason": "restricted participant"},
                       segment_starts=[], masked=[], slab=None)
            exclusions.append({"cohort": "sparrkulee", "run_id": rec["run_id"], "rule": "restricted_participant", "detail": "never opened"})
        else:
            m = _qc_mask(x); data[rec["run_id"]] = x; masks[rec["run_id"]] = set(m.tolist())
            rec.update(masked=[C.BIOSEMI64[c] for c in m], source_sha256=_sha_bytes(x.tobytes()),
                       audit={"clock": "misaligned", "tau_hat": [-566, -566], "z": [9.0, 8.5]} if rule == "clock_misaligned" else
                       {"clock": "unverifiable" if rule else "aligned"})
            if rule:
                exclusions.append({"cohort": "sparrkulee", "run_id": rec["run_id"], "rule": rule, "detail": rec["audit"]})
        recs.append(rec)
    g0 = C.GUARDS["sparrkulee"][0]; sk_parts, arrays, cached = [], [], [r for r in recs if r["role"] != "restricted"]
    for sub in sorted({r["sub"] for r in cached}):
        mine = [r for r in cached if r["sub"] == sub]; arrs = [data[r["run_id"]] for r in mine]
        if ("sparrkulee", sub) in perturb:
            arrs[0] = arrs[0] * perturb[("sparrkulee", sub)]
        mu, sd = _zstats(arrs, [masks[r["run_id"]] for r in mine], g0)
        sk_parts.append({"sub": sub, "participant": sub, "uid": f"sparrkulee:{sub}", "role": SK_ROLE[sub], "group": "sparrkulee",
                         "donor": SK_ROLE[sub] in DONOR_ROLES, "mu": {"A": mu}, "sd_prez": {"A": _nan_none(sd)}})
        for r, a in zip(mine, arrs):
            data[r["run_id"]] = _z(a, mu, sd, masks[r["run_id"]]).T.astype(np.float16)
    n_rows["sparrkulee"], slabs_of["sparrkulee"] = _write_cache(sk_dir, cached, [{"A": data[r["run_id"]]} for r in cached], SK_SLABS, "A")
    sk.save(sk_dir); _dump({"participants": sk_parts, "runs": recs}, os.path.join(sk_dir, "runs.json"))
    tables["sparrkulee"], stream_tab["sparrkulee"], parts_of["sparrkulee"] = recs, sk, sk_parts

    # ------------------------------------------------------------------------------------------------ FAU-like donor / target
    fau_dir = os.path.join(root, "fau"); os.makedirs(fau_dir, exist_ok=True)
    fa = _Streams("fau", filters); lay = C.MONTAGES["fau"]; n_ch = len(lay); raw128, code_p = {}, {}
    folds = _folds({g: list(v) for g, v in FAU_P.items()})
    plist = [{"participant": s, "group": "th", "fold": -1, "dev": True} for s in FAU_DEV] + \
            [{"participant": s, "group": g, "fold": folds[s], "dev": False} for g, ss in FAU_P.items() for s in ss]
    for p in plist:
        p.update(uid=f"fau:{p['participant']}", identity=p["participant"], test_only=False, donor=True,
                 masked=list(FAU_MASK.get(p["participant"], ())))
    for code in FAU_SS:
        raw128[code] = _raw_env(rng, 2 * lfau, 128); fid = reg.family("fau", code)
        sid = fa.add(f"{code}/attended", raw128[code], "attended", fid, 0, rich=_rich(rng, lfau), clock_lag=0)
        code_p[code] = reg.presentation("fau", code, fid, 0, sid, condition="single-speaker")
    for code in FAU_CS:
        fid = reg.family("fau", code)
        sa = fa.add(f"{code}/attended", _raw_env(rng, 2 * lfau, 128), "attended", fid, 0, reason="no_waveform_competing_talker")
        d = _raw_env(rng, 2 * lfau, 128); d[:int(FAU_LEAD_S * 128)] = 0.0             # the distractor starts at the lead (trial grid)
        sd_ = fa.add(f"{code}/distractor", d, "distractor", None, 0, reason="not_a_target_stream")
        for side in ("left", "right"):
            code_p[(code, side)] = reg.presentation("fau", code, fid, 0, sa, kind="cs", condition="competing", side=side, ign=sd_,
                                                    onset=FAU_LEAD_S)
    fgain, art = rng.standard_normal(n_ch), np.zeros(n_ch)
    art[[lay.index("T7"), lay.index("T8")]] = 6.0       # stimulus-locked CI artefact, removed by the stage-B ICA rule (mode A)
    pieces, arrays, g0 = [], [], C.GUARDS["fau"][0]
    for pi, p in enumerate(plist):
        p["cs_side"] = {c: ("left", "right")[(pi + k) % 2] for k, c in enumerate(FAU_CS)}
        ch_scale = rng.uniform(5, 20, n_ch); g = fgain * rng.uniform(0.5, 1.5); mi = {lay.index(c) for c in p["masked"]}
        A, B, mine = [], [], []
        for t, code in enumerate(FAU_SS + FAU_CS):
            cs = code in FAU_CS; pr = reg.pres[code_p[(code, p["cs_side"][code])] if cs else code_p[code]]
            en = fa.env[pr["stream"]]; T = len(en); resp = _response(en, T)
            if cs:
                resp = resp + 0.5 * _response(fa.env[pr["ignored_stream"]], T, lead=pr["ignored_lead"])
            base = np.outer(g, resp) + 2.0 * rng.standard_normal((n_ch, T))
            A.append(base * ch_scale[:, None]); B.append((base + (np.outer(art, en) if p["group"] == "ci" else 0.0)) * ch_scale[:, None])
            mine.append(_piece("fau", p, f"trial_{t + 1:02d}", pr, T, T, "fit", code))
        if ("fau", p["participant"]) in perturb:
            A[0], B[0] = A[0] * perturb[("fau", p["participant"])], B[0] * perturb[("fau", p["participant"])]
        mua, sda = _zstats(A, [mi] * len(A), g0); mub, sdb = _zstats(B, [mi] * len(B), g0)
        p["mu"], p["sd_prez"] = {"A": mua, "B": mub}, {"A": _nan_none(sda), "B": _nan_none(sdb)}
        for a, b in zip(A, B):
            r = b.copy(); r[sorted(mi)] = 0
            arrays.append({"A": _z(a, mua, sda, mi).T.astype(np.float16), "B": _z(b, mub, sdb, mi).T.astype(np.float16),
                           "C": r.T.astype(np.float16)})
        pieces += mine
    n_rows["fau"], slabs_of["fau"] = _write_cache(fau_dir, pieces, arrays, SLABS, "ABC")
    fa.save(fau_dir); _dump({"participants": plist, "pieces": pieces}, os.path.join(fau_dir, "pieces.json"))
    tables["fau"], stream_tab["fau"], parts_of["fau"] = pieces, fa, plist

    # ------------------------------------------------------------------------------------------------ DTU-like donor (NH) / target
    dtu_dir = os.path.join(root, "dtu"); os.makedirs(dtu_dir, exist_ok=True)
    dt = _Streams("dtu", filters); lay = C.MONTAGES["dtu"]; n_ch = len(lay); h_p, h_sid, h_fid, h_off, m_sid = {}, {}, {}, {}, {}
    dmaster = _raw_env(rng, 2 * (ldtu + DTU_DUP[2]), 128)
    (_, fs_, f0), (_, ds_, d0), n_ov = OVERLAP
    for h in sorted(DTU_GROUP):
        e = dmaster[:2 * ldtu].copy() if h == DTU_DUP[0] else dmaster[2 * DTU_DUP[2]:2 * (DTU_DUP[2] + ldtu)].copy() if h == DTU_DUP[1] \
            else _raw_env(rng, 2 * ldtu, 128)
        if h == ds_:
            e[d0:d0 + n_ov] = raw128[fs_][f0:f0 + n_ov]
        h_off[h] = DTU_DUP[2] if h == DTU_DUP[1] else 0
        h_fid[h] = reg.family("dtu", DTU_DUP[0] if h == DTU_DUP[1] else h)
        if h == DTU_DUP[1]:
            reg.fams[h_fid[h]]["basis"] = "duplicate_scan"
        h_sid[h] = dt.add(h, e, "attended", h_fid[h], h_off[h], rich=_rich(rng, ldtu), clock_lag=0)   # the unequalised original
        h_p[h] = reg.presentation("dtu", h, h_fid[h], h_off[h], h_sid[h], condition="single-talker")
    for m in ("m01", "m02"):
        m_sid[m] = dt.add(m, _raw_env(rng, 2 * ldtu, 128), "masker", None, 0, reason="not_a_target_stream")
    folds = _folds({"nh": list(DTU_NH), "hi": list(DTU_HI)})
    plist = [{"participant": s, "group": g, "fold": folds[s], "dev": False, "test_only": False, "donor": g == "nh", "masked": []}
             for g, ss in (("nh", DTU_NH), ("hi", DTU_HI)) for s in sorted(ss)]
    pieces, arrays, g0, cs_p = [], [], C.GUARDS["dtu"][0], {}
    dgain, ck = rng.standard_normal(n_ch), np.hanning(16) / np.hanning(16).sum()
    for p in plist:
        p.update(uid=f"dtu:{p['participant']}", identity=p["participant"])
        ch_scale = rng.uniform(5, 20, n_ch); g = dgain * rng.uniform(0.5, 1.5); X, mine = [], []
        trials = [(h, None) for h in (DTU_NH if p["group"] == "nh" else DTU_HI)[p["participant"]]] + [DTU_CS[p["participant"]][:2]]
        for t, (h, m) in enumerate(trials):
            if m is None and p["group"] == "nh":
                pid, role = h_p[h], "fit"
            elif m is None:      # equalised per listener: a unique presentation on the original's stream and family clock
                pid, role = reg.presentation("dtu", f"{h}@eq:{p['participant']}", h_fid[h], h_off[h], h_sid[h],
                                             condition="single-talker (individually equalised)"), "target_only"
            else:
                on = DTU_CS[p["participant"]][2]
                if (h, m, on) not in cs_p:
                    cs_p[(h, m, on)] = reg.presentation("dtu", f"{h}+{m}@{on:.4f}", h_fid[h], h_off[h], h_sid[h], kind="cs",
                                                        condition="two-talker", ign=m_sid[m], ign_lead=round(on * C.FS), onset=on)
                pid, role = cs_p[(h, m, on)], "target_only"
            pr = reg.pres[pid]; en = dt.env[pr["stream"]]; T = ldtu; resp = _response(en, T)
            if m is not None:
                resp = resp + 0.5 * _response(dt.env[pr["ignored_stream"]], T, lead=pr["ignored_lead"])
            x = (np.outer(g, resp) + 2.0 * rng.standard_normal((n_ch, T))) * ch_scale[:, None]
            x = x + 7.0 * 12.0 * np.convolve(rng.standard_normal(T), ck, mode="same")[None]     # CMS common mode
            X.append(x - x.mean(0, keepdims=True))                                            # CAR over the 64 EEG channels
            mine.append(_piece("dtu", p, f"trial_{t + 1:03d}", pr, T, len(en), role, h, DTU_GROUP[h], m))
        if ("dtu", p["participant"]) in perturb:
            X[0] = X[0] * perturb[("dtu", p["participant"])]
        mu, sd = _zstats(X, [set()] * len(X), g0)
        p["mu"], p["sd_prez"] = {"A": mu}, {"A": _nan_none(sd)}
        arrays += [{"A": _z(x, mu, sd, ()).T.astype(np.float16), "C": x.T.astype(np.float16)} for x in X]
        pieces += mine
    n_rows["dtu"], slabs_of["dtu"] = _write_cache(dtu_dir, pieces, arrays, SLABS, "AC")
    dt.save(dtu_dir); _dump({"participants": plist, "pieces": pieces}, os.path.join(dtu_dir, "pieces.json"))
    tables["dtu"], stream_tab["dtu"], parts_of["dtu"] = pieces, dt, plist

    # ------------------------------------------------------------------------------------------------ Federici-like donor (humans) / target
    fed_dir = os.path.join(root, "federici"); os.makedirs(fed_dir, exist_ok=True)
    fe = _Streams("federici", filters); lay = C.MONTAGES["federici"]; n_ch = len(lay); it_p = {}
    n100 = lfed * 25 // 16; fmaster = _raw_env(rng, n100 + FED_LAG100, 100)
    for item, (fam, cond) in FED_ITEMS.items():
        e = fmaster[:n100].copy() if item == "N1" else 0.8 * fmaster[FED_LAG100:FED_LAG100 + n100] + 0.05 * _raw_env(rng, n100, 100) \
            if item == "V1" else _raw_env(rng, n100, 100)
        fid = reg.family("federici", fam, clock="unknown" if fam == "g1" else "known", basis="natural_vocoded" if fam[0] == "g" else "own")
        off = FED_LAG if item == "V1" else 0
        sid = fe.add(item, e, "item", fid, off, reason="no_waveform")                  # the block envelope of the item (AudioEnvSp)
        it_p[item] = reg.presentation("federici", item, fid, off, sid, condition=cond, known=item != "V2")
    idents = {"hc": sorted({q.split(":")[1] for q in FED_HEAR if q.split(":")[0] in ("HC", "HC-v")}),
              "ci": sorted(q for q in FED_HEAR if q.startswith("CI:"))}
    folds = _folds(idents)
    plist = []
    for q in FED_HEAR:
        grp, fid_ = q.split(":"); ident = fid_ if grp in ("HC", "HC-v") else q
        plist.append({"participant": q, "uid": f"federici:{q}", "identity": ident, "group": grp, "fold": folds.get(ident, -1), "dev": False,
                      "test_only": grp == "Artifact", "donor": grp != "Artifact", "masked": []})
    pieces, arrays, g0 = [], [], C.GUARDS["federici"][0]
    fgain, part = rng.standard_normal(n_ch), np.zeros(n_ch); part[[lay.index("Fp1"), lay.index("Fp2"), lay.index("T7")]] = 4.0
    for p in plist:
        ch_scale = rng.uniform(5, 20, n_ch); g = fgain * rng.uniform(0.5, 1.5); X, mine = [], []
        for b, item in enumerate(FED_HEAR[p["participant"]]):
            pr = reg.pres[it_p[item]]; en = fe.env[pr["stream"]]; T = len(en)
            resp = np.outer(part, en) if p["test_only"] else np.outer(g, _response(en, T))      # the phantom: stimulus-locked artefact
            X.append((resp + 2.0 * rng.standard_normal((n_ch, T))) * ch_scale[:, None])
            mine.append(_piece("federici", p, f"block_{b}", pr, T, T, "target_only" if p["test_only"] else "fit", item, FED_CG[item]))
        if ("federici", p["participant"]) in perturb:
            X[0] = X[0] * perturb[("federici", p["participant"])]
        mu, sd = _zstats(X, [set()] * len(X), g0)
        p["mu"], p["sd_prez"] = {"A": mu}, {"A": _nan_none(sd)}
        arrays += [{"A": _z(x, mu, sd, ()).T.astype(np.float16), "C_partial": x.T.astype(np.float16)} for x in X]
        pieces += mine
    n_rows["federici"], slabs_of["federici"] = _write_cache(fed_dir, pieces, arrays, SLABS, ("A", "C_partial"))
    fe.save(fed_dir); _dump({"participants": plist, "pieces": pieces}, os.path.join(fed_dir, "pieces.json"))
    tables["federici"], stream_tab["federici"], parts_of["federici"] = pieces, fe, plist
    twins = [["federici", f"HC:{n}", f"HC-v:{n}"] for n in idents["hc"] if f"HC:{n}" in FED_HEAR and f"HC-v:{n}" in FED_HEAR]
    pres, fams = reg.pres, reg.fams

    # ------------------------------------------------------------------------------------------------ overlap (C3, §3.4)
    (ca, sa_), (cb, sb_) = OVERLAP[0][:2], OVERLAP[1][:2]
    st = {c: next(r for r in stream_tab[c].rows if r["name"] == (f"{s}/attended" if c == "fau" else s)) for c, s in ((ca, sa_), (cb, sb_))}
    ea = stream_tab[ca].env[st[ca]["stream"]][OVERLAP[0][2] // 2:(OVERLAP[0][2] + OVERLAP[2]) // 2]
    eb = stream_tab[cb].env[st[cb]["stream"]][OVERLAP[1][2] // 2:(OVERLAP[1][2] + OVERLAP[2]) // 2]
    overlap = [{"a": {"cohort": ca, "stimulus": sa_, "stream": st[ca]["stream"], "span": [OVERLAP[0][2] // 2, (OVERLAP[0][2] + OVERLAP[2]) // 2]},
                "b": {"cohort": cb, "stimulus": sb_, "stream": st[cb]["stream"], "span": [OVERLAP[1][2] // 2, (OVERLAP[1][2] + OVERLAP[2]) // 2]},
                "lag": OVERLAP[1][2] // 2 - OVERLAP[0][2] // 2, "r": float(np.corrcoef(ea, eb)[0, 1]), "rule": "10 s windows, 2 s hop, r >= 0.7"}]
    excl_of = {}   # (target, donor cohort) -> presentations of the donor cohort on a stream that overlaps the target cohort
    for o in overlap:
        for d_, t_ in (("a", "b"), ("b", "a")):
            c, s = o[d_]["cohort"], o[d_]["stream"]
            excl_of.setdefault((o[t_]["cohort"], c), set()).update(q["id"] for q in pres if q["cohort"] == c and q["stream"] == s)

    # ------------------------------------------------------------------------------------------------ segment tables and pools
    spans = {}
    for d in shared:
        spans.setdefault(d["presentation"], []).append(tuple(d["span"]))
    ex = {}
    for c, a, b in twins:
        ex.setdefault((c, a), set()).add(b); ex.setdefault((c, b), set()).add(a)
    seg, hc_hcv = {}, 0
    for cohort, table in tables.items():
        rows = [(i, r["participant"], r["presentation"], s, r["role"], pres[r["presentation"]]["kind"]) for i, r in enumerate(table)
                if r["row_offset"] is not None for s in _unmasked(r["segment_starts"], spans.get(r["presentation"], []))]
        grp = {}
        for _, part_, p, s, role, _ in rows:
            grp.setdefault((p, s, role), set()).add(part_)
        n_l = [len(grp[(r[2], r[3], r[4])]) for r in rows]
        n_p = [len(grp[(r[2], r[3], r[4])] - {r[1]} - ex.get((cohort, r[1]), set())) if r[4] in DONOR_ROLES else 0 for r in rows]
        hc_hcv += sum(sum(a in g_ and b in g_ for c, a, b in twins if c == cohort) for (_, _, role), g_ in grp.items() if role in DONOR_ROLES)
        seg[cohort] = {k: [r[j] for r in rows] for j, k in enumerate(("piece", "participant", "presentation", "s", "role", "kind"))}
        seg[cohort].update(family=[pres[r[2]]["family"] for r in rows], n_listeners=n_l, n_partners=n_p)

    def pool(c, role="fit", kind="ss"):
        S = seg[c]
        return [i for i in range(len(S["s"])) if S["role"][i] == role and S["kind"][i] == kind and S["n_partners"][i] >= 1]
    pools = {"core": {c: pool(c) for c in tables}, "csx": {"fau_cs": pool("fau", kind="cs")},
             "dev": {"sparrkulee": pool("sparrkulee", "dev")}, "bridge_cal": {"sparrkulee": pool("sparrkulee", "bridge_cal")}}
    rows_of = lambda c: pools["csx"]["fau_cs"] if c == "fau_cs" else pools["core"][c]   # noqa: E731
    coh_of = lambda c: "fau" if c == "fau_cs" else c                                     # noqa: E731
    donor_sets = {}
    for target, strata in DONORS.items():
        blocks = {"core": strata, "rich": strata, **({} if target == "fau" else {"csx": strata + ("fau_cs",)})}
        donor_sets[target] = {}
        for b, ss in blocks.items():
            excl = {c: sorted(excl_of.get((target, coh_of(c)), ())) for c in ss}
            n = [sum(seg[coh_of(c)]["presentation"][r] not in excl[c] for r in rows_of(c)) for c in ss]
            donor_sets[target][b] = {"strata": list(ss), "weights": [v / sum(n) for v in n], "n_segments": n, "excluded_presentations": excl}
    if scale >= 4:   # every stratum of every donor set and block holds a design batch: 32 distinct (presentation, s) with a partner
        for target, blocks in donor_sets.items():
            for b, v in blocks.items():
                for c in v["strata"]:
                    Sc, ex = seg[coh_of(c)], set(v["excluded_presentations"][c])
                    n_u = len({(Sc["presentation"][r], Sc["s"][r]) for r in rows_of(c) if Sc["presentation"][r] not in ex})
                    if n_u < BATCH_SEGMENTS:
                        raise AssertionError(f"make_synthetic_manifest(scale={scale}): stratum {c} of {target}/{b} holds {n_u} < "
                                             f"{BATCH_SEGMENTS} distinct content segments")
    N_SK = len(pools["core"]["sparrkulee"])
    budget = {"N_SK": N_SK, "anchors_per_ep_eq": C.N_ANCHORS * N_SK, "steps_per_ep_eq": C.N_ANCHORS * N_SK / 256,
              "steps_per_ep_eq_ceil": math.ceil(C.N_ANCHORS * N_SK / 256), "ep_eq0": 30, "ep_eq_limit": 60,
              "S0": math.ceil(30 * C.N_ANCHORS * N_SK / 256)}

    # ------------------------------------------------------------------------------------------------ standardisers and projections
    S = seg["sparrkulee"]; u = sorted({(S["presentation"][i], S["s"][i]) for i in pools["core"]["sparrkulee"]})
    win = lambda p, s: sk.rows[pres[p]["stream"]]["offset"] + s + C.TICK_OFFS[:, None] + np.arange(C.N_TGT)[None]   # noqa: E731
    sk_env, sk_rich = np.concatenate(sk.env), np.concatenate(sk.rich)
    Y = np.concatenate([sk_env[win(p, s)] for p, s in u]).astype(np.float64)
    sigma, mu_est = np.sqrt((Y ** 2).mean(0)), Y.mean(0)          # RMS about 0 (mu fixed at 0, §2.3), not the SD; mean recorded only
    ur = [(p, s) for p, s in u if sk.rich_rows[pres[p]["stream"]]["available"]]
    R = np.concatenate([sk_rich[win(p, s)] for p, s in ur]).astype(np.float64)          # [n, 8, 5]
    Rss, Rsc = R[..., :4].reshape(len(R), -1), R[..., 4]
    P, P_rich = _semi_orthogonal(32, 8, C.PROJ_SEED), {k: _semi_orthogonal(*C.RICH_P_SHAPE[k], C.RICH_SEEDS[k]) for k in ("ss", "sc")}
    np.save(os.path.join(root, C.P_FILE), P)
    for k in P_rich:
        np.save(os.path.join(root, C.RICH_P_FILE[k]), P_rich[k])
    pca4 = np.linalg.qr(rng.standard_normal((128, 4)))[0]; np.save(os.path.join(root, "rich_pca4_f64.npy"), pca4)
    projection = {"file": C.P_FILE, "sha256": _sha_bytes(P.tobytes()), "seed": C.PROJ_SEED, "shape": list(C.P_SHAPE)}
    standardiser = {"sigma": sigma, "mu": np.zeros(C.N_TGT), "mu_estimate": mu_est, "abs_mu_over_sigma_max": float(np.abs(mu_est / sigma).max()),
                    "n_windows": int(len(Y))}
    rich = {"columns": list(C.RICH_COLS), "y_layout": "y_ss[k] = rich[i_k:i_k + 8, 0:4] flattened sample-major (C order) -> 32; "
                                                      "y_sc[k] = rich[i_k:i_k + 8, 4] -> 8",
            "pca4": {"file": "rich_pca4_f64.npy", "sha256": _sha_bytes(pca4.tobytes()), "shape": [128, 4], "fit": "synthetic"},
            **{f"P_{k}": {"file": C.RICH_P_FILE[k], "sha256": _sha_bytes(P_rich[k].tobytes()), "seed": C.RICH_SEEDS[k],
                          "shape": list(C.RICH_P_SHAPE[k])} for k in P_rich},
            "sigma_ss": np.sqrt((Rss ** 2).mean(0)), "sigma_sc": np.sqrt((Rsc ** 2).mean(0)), "mu_estimate_ss": Rss.mean(0),
            "mu_estimate_sc": Rsc.mean(0), "n_windows": int(len(R)), "loss_weights": [1.0, 0.5, 0.5]}
    target_contract = _sha_bytes(json.dumps({"sigma": sigma.tolist(), "mu": [0.0] * C.N_TGT, "P": projection["sha256"], "filters": filters},
                                            sort_keys=True).encode())

    # ------------------------------------------------------------------------------------------------ selection, bridge, coverage, mode C
    srng = np.random.default_rng(C.BRIDGE_SEED)
    selection = {"fit_segments": sorted(srng.choice(pools["core"]["sparrkulee"], 12, replace=False).tolist()),
                 "dev_queries": pools["dev"]["sparrkulee"]}
    fit_rows = {}
    for target, ds in donor_sets.items():
        core = ds["core"]; picks = srng.choice(len(core["strata"]), 24, p=core["weights"])
        ok = {c: [r for r in rows_of(c) if seg[coh_of(c)]["presentation"][r] not in core["excluded_presentations"][c]] for c in core["strata"]}
        fit_rows[target] = [[core["strata"][k], int(srng.choice(ok[core["strata"][k]]))] for k in picks]
    bridge = {"fit_rows": fit_rows, "cal_queries": pools["bridge_cal"]["sparrkulee"], "cal_split": [["061"], ["062"]]}
    seen, coverage = {}, {}
    for target, strata in DONORS.items():
        names = {n for c in strata for n in C.MONTAGES[c]}; lay_t = C.MONTAGES[target]
        seen[target] = [n for n in C.VOCAB if n in names]
        coverage[target] = {"n_seen": sum(n in names for n in lay_t), "n_total": len(lay_t), "unseen": [n for n in lay_t if n not in names]}
    sd_tab = {}   # donor-fit participants' pre-z SD (uV) of the donor-training input, per channel name
    for c, parts in parts_of.items():
        for p in parts:
            if p["donor"] and p.get("role", "fit") == "fit":
                sd_tab.setdefault(c, []).append(dict(zip(C.MONTAGES[c], p["sd_prez"]["A"])))
    mode_c = {"sparrkulee": {"supported": False, "reason": "donor only"}}
    for target, mode in (("fau", "C"), ("dtu", "C"), ("federici", "C_partial")):
        vals = [v for c in DONORS[target] for d in sd_tab[c] for v in d.values() if v is not None]
        sc = {}
        for n in C.MONTAGES[target]:
            v = [d[n] for c in DONORS[target] for d in sd_tab[c] if d.get(n) is not None]
            sc[n] = float(np.median(v if v else vals))
        mode_c[target] = {"supported": True, "mode": mode, "unit": "uV", "basis": "synthetic", "donors": list(DONORS[target]), "scale": sc,
                          "rule": "median over the leave-target-out donor-fit participants having the channel of their pre-z SD; "
                                  "names no donor has: median over all donor channels"}

    # ------------------------------------------------------------------------------------------------ cells
    def split_hash(d):
        return _sha_bytes(json.dumps(d, sort_keys=True, default=_j).encode())

    def cell(**d):
        return {**d, "split_hash": split_hash(d)}
    cells, fp = [], parts_of["fau"]
    for sf in range(5):
        for cf in (0, 1):
            content = {k: {r: sorted(c for c in (FAU_SS if k == "ss" else FAU_CS) if c[2] in parts_) for r, parts_ in v.items()}
                       for k, v in FAU_CF[cf].items()}
            cells.append(cell(dataset="fau", subject_fold=sf, content_fold=cf, always_train=list(FAU_DEV), test_only=[],
                              train=[p["participant"] for p in fp if p["dev"] or p["fold"] != sf],
                              test=[p["participant"] for p in fp if not p["dev"] and p["fold"] == sf], content=content, rules="fixture",
                              seeds={"folds": C.FOLD_SEED}))
    dp = parts_of["dtu"]
    for sf in range(5):
        for cf in (0, 1):
            role = {h: "test" if DTU_SPLIT[g_][0] == cf else ("es" if DTU_SPLIT[g_][1] else "fit") for h, g_ in DTU_GROUP.items()}
            cells.append(cell(dataset="dtu", subject_fold=sf, content_fold=cf, always_train=[], test_only=[],
                              train=[p["participant"] for p in dp if p["fold"] != sf], test=[p["participant"] for p in dp if p["fold"] == sf],
                              content={r: sorted(h for h in role if role[h] == r) for r in ("fit", "es", "test")},
                              content_groups={h: DTU_GROUP[h] for h in sorted(DTU_GROUP)}, rules="fixture", seeds={"folds": C.FOLD_SEED}))
    ep = parts_of["federici"]
    for sf in range(5):
        cells.append(cell(dataset="federici", subject_fold=sf, content_fold=0, always_train=[],
                          train=[p["participant"] for p in ep if not p["test_only"] and p["fold"] != sf],
                          test=[p["participant"] for p in ep if not p["test_only"] and p["fold"] == sf],
                          test_only=[p["participant"] for p in ep if p["test_only"]],
                          content={r: sorted(i for i in FED_CG if FED_ROLE[FED_CG[i]] == r) for r in ("fit", "es", "test")},
                          content_groups=dict(sorted(FED_CG.items())), rules="fixture", seeds={"folds": C.FOLD_SEED}))
    kids = synthetic_kids()
    for sf in range(5):
        cells.append(cell(dataset="private_bdf", subject_fold=sf, content_fold=0, always_train=[], test_only=[],
                          train=[k["id"] for k in kids if k["fold"] != sf], test=[k["id"] for k in kids if k["fold"] == sf],
                          content={"es": "last 20 % of each child's physical blocks"}, rules="fixture", seeds={"folds": C.FOLD_SEED}))

    # ------------------------------------------------------------------------------------------------ unused records, manifest
    unused = [{"cohort": "sparrkulee", "what": r["run_id"], "n": 1, "reason": r["role"]} for r in recs if r["role"] not in DONOR_ROLES]
    unused += [{"cohort": "fau", "what": "competing-talker pieces", "n": sum(q["kind"] == "cs" for q in tables["fau"]), "reason": "CSX only"},
               {"cohort": "dtu", "what": "HI single-talker trials", "n": sum(q["group"] == "hi" and q["kind"] == "ss" for q in tables["dtu"]),
                "reason": "individually equalised audio: no shared presentation"},
               {"cohort": "dtu", "what": "two-talker trials", "n": sum(q["kind"] == "cs" for q in tables["dtu"]), "reason": "not donors"},
               {"cohort": "dtu", "what": "NH single-listener shas", "n": 1, "reason": "one NH listener (t08)"},
               {"cohort": "federici", "what": "phantom sessions", "n": sum(p["test_only"] for p in ep), "reason": "never donors"},
               {"cohort": "federici", "what": "single-listener items", "n": 1, "reason": "one listener (N6)"}]
    unused += [{"cohort": c, "what": f"rich targets of {r['name']}", "n": 1, "reason": r["reason"]}
               for c, s in stream_tab.items() for r in s.rich_rows if not r["available"]]
    rel = lambda d: os.path.relpath(d, root)   # noqa: E731
    cohorts = {}
    for c, d, fs_n, ref, band, items in (("sparrkulee", sk_dir, 64, "CAR-64 (authors)", "authors' pipeline, then 1-20 Hz (ours)", "runs"),
                                         ("fau", fau_dir, 128, "average (31)", "1-20 Hz FIR + ICA (stage B)", "pieces"),
                                         ("dtu", dtu_dir, 128, "CAR-64 (ours)", "1-20 Hz FIR", "pieces"),
                                         ("federici", fed_dir, 100, "average (32)", "authors' 2-8 Hz + ICA", "pieces")):
        cohorts[c] = {"dir": rel(d), "fs_native": fs_n, "n_ch": len(C.MONTAGES[c]), "layout": list(C.MONTAGES[c]), "reference": ref, "band": band,
                      "guards": list(C.GUARDS[c]), "s_first": C.S_FIRST[c], "n_rows": n_rows[c],
                      "caches": {m: C.CACHE_FILE[m] for m in {"sparrkulee": "A", "fau": "ABC", "dtu": "AC", "federici": ("A", "C_partial")}[c]},
                      "table": f"{items}.json", "items": items, "env": "env_f32.npy", "streams": "streams.json", "rich": "rich_f32.npy",
                      "rich_streams": "rich_streams.json", "role_slabs": slabs_of[c], "unit": {"name": "uV", "basis": "synthetic"},
                      "masked_cells": int(sum(len(r["masked"]) for r in tables[c] if r["row_offset"] is not None))}
    man = {"schema": SCHEMA, "contract": C.CONTRACT, "synthetic": True, "builder_sha256": "synthetic-fixture",
           "constants": {"fs": C.FS, "l_in": C.L_IN, "n_tgt": C.N_TGT, "seg_ticks": C.SEG_TICKS, "seg_step": C.SEG_STEP,
                         "env_edge": C.ENV_EDGE, "neighbor": C.NEIGHBOR, "tau": C.TAU, "onset64": C.ONSET64,
                         "key_bits": [C.FAMILY_BITS, C.PRES_BITS, C.S_BITS],
                         "tick_offs_sha256": _sha_bytes(np.ascontiguousarray(C.TICK_OFFS, dtype=np.int64).tobytes())},
           "filters": filters, "target_contract": target_contract, "projection": projection, "standardiser": standardiser, "rich": rich,
           "vocab": list(C.VOCAB), "aliases": C.ALIASES, "montages": {k: list(v) for k, v in C.MONTAGES.items()}, "cohorts": cohorts,
           "families": fams, "presentations": pres, "shared_audio": shared, "overlap": overlap, "partner_exclusions": twins,
           "hc_hcv_excluded_pairs": hc_hcv, "segments": seg, "pools": pools, "donor_sets": donor_sets, "budget": budget,
           "selection": selection, "bridge": bridge, "seen": seen, "coverage": coverage, "cells": cells, "mode_c": mode_c,
           "exclusions": exclusions, "unused": unused,
           "dtu_reconciliation": {"absent_trials": [], "rule": "C6 lists NH single-talker trials absent from the cache (none here)"}}
    if scale != 1:                    # recorded only off the default, so the scale-1 manifest keeps its bytes
        man["fixture_scale"] = scale
    path = os.path.join(root, "manifest.json")
    if os.path.exists(path):          # rebuilding in place (deterministic: same bytes)
        os.chmod(path, 0o644)
    _dump(man, path); os.chmod(path, 0o444)
    with open(path, "rb") as f:
        raw = f.read()
    name = lambda c, s: f"{c}:{s}"   # noqa: E731
    truth = {"lag": LAG, "family": {name(f["cohort"], f["name"]): f["id"] for f in fams},
             "presentation": {name(q["cohort"], q["stimulus"] + (f"/{q['attended_side']}" if q["attended_side"] else "")): q["id"] for q in pres},
             "family_offset": {**{name("sparrkulee", s): o for s, _, o, _ in SK_STIMS}, name("dtu", DTU_DUP[1]): DTU_DUP[2],
                               name("federici", "V1"): FED_LAG},
             "unknown_clock_families": [f["id"] for f in fams if f["clock"] == "unknown"], "shared_span": [0, JINGLE + MARGIN],
             "masked_cells": [[s, st_, ch] for (s, st_), (ch, _) in SK_PLANT.items()], "fau_masked": FAU_MASK,
             "excluded_runs": [e["run_id"] for e in exclusions if e["rule"] != "restricted_participant"],
             "restricted_files": [r["raw_file"] for r in recs if r["role"] == "restricted"],
             "twins": twins, "twin_only_item": name("federici", "N5"), "phantom": [p["participant"] for p in ep if p["test_only"]],
             "dtu_hi": sorted(DTU_HI), "dtu_shared_two_talker": cs_p[("t02", "m01", 3.25)], "single_listener": ["dtu:t08", "federici:N6"],
             "overlap": [[ca, sa_], [cb, sb_]], "excluded_presentations": {f"{t}<-{c}": sorted(v) for (t, c), v in excl_of.items()},
             "rich_masked": {c: [r["name"] for r in s.rich_rows if not r["available"]] for c, s in stream_tab.items()},
             "fau_cs_onset_s": FAU_LEAD_S, "dtu_masker_onsets": {s: v[2] for s, v in DTU_CS.items()}}
    return {"root": root, "manifest_path": path, "manifest_sha256": _sha_bytes(raw), "manifest": json.loads(raw), "kids": kids, "P": P,
            "P_rich": P_rich, "truth": truth, "scale": scale, "sources": {c: s.sources for c, s in stream_tab.items()}}


# ---------------------------------------------------------------------------------------------------------- regression fingerprint
def _fp_json(o):
    """A JSON value with every float at 8 significant digits and every sha256 hex string replaced by a placeholder (what a hash
    covers is fingerprinted itself, and a hash of float bytes would carry the last-bit noise back in)."""
    if isinstance(o, float):
        return float(f"{o:.8g}") if math.isfinite(o) else str(o)
    if isinstance(o, str):
        return "<sha256>" if len(o) == 64 and all(ch in "0123456789abcdef" for ch in o) else o
    if isinstance(o, dict):
        return {k: _fp_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_fp_json(v) for v in o]
    return o


def _fp_array(a, chunk=1 << 16):
    """Shape, dtype, the non-finite count and four sums of non-negative terms over the finite values (|x|, x^2, w |x| with fixed
    position weights w in [1, 2), max(x, 0)), each at 8 significant digits: no cancellation, so last-bit noise stays far below the
    rounding, while a reordering, a sign change or any value change above about 1e-8 moves a sum."""
    flat, sums, n_bad = a.reshape(-1), [[], [], [], []], 0
    for i in range(0, flat.size, chunk):
        x = np.asarray(flat[i:i + chunk], dtype=np.float64)
        bad = ~np.isfinite(x); n_bad += int(bad.sum()); x = np.where(bad, 0.0, x)
        h = (np.arange(i, i + x.size, dtype=np.uint64) * np.uint64(2654435761)) % np.uint64(1 << 32)
        w, ax = 1.0 + h.astype(np.float64) / 2.0 ** 32, np.abs(x)
        for k, v in enumerate((ax, x * x, w * ax, np.maximum(x, 0.0))):
            sums[k].append(float(v.sum()))
    return {"shape": list(a.shape), "dtype": a.dtype.str, "n_nonfinite": n_bad, "sums": [float(f"{math.fsum(s):.8g}") for s in sums]}


def fingerprint(root):
    """{relative path: 16-hex digest} of every file of a build under `root`. It ignores float rounding (about 1e-8 relative; the
    build's last bits may depend on the CPU's BLAS and SIMD kernels), while any change of random draws, values, shapes, dtypes,
    ids, keys or strings changes it. JSON files: _fp_json; .npy files: _fp_array (read with allow_pickle=False); files under raw/
    (the restricted decoy) are never opened, their size stands in."""
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if rel.startswith("raw/"):
                obj = {"bytes": os.path.getsize(p)}
            elif f.endswith(".json"):
                with open(p) as h:
                    obj = _fp_json(json.load(h))
            elif f.endswith(".npy"):
                obj = _fp_array(np.load(p, mmap_mode="r", allow_pickle=False))
            else:
                with open(p, "rb") as h:
                    obj = {"sha256": _sha_bytes(h.read())}
            out[rel] = _sha_bytes(json.dumps(obj, sort_keys=True).encode())[:16]
    return dict(sorted(out.items()))
