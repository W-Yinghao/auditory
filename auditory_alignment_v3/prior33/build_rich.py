"""E34_PUBLIC_PRIOR C7: the rich-target cache (module M2d): spectral structure (PCA-4 of the Whisper log-mel) and spectral change
(flux) at 64 Hz, aligned sample for sample with every cohort's envelope streams.

Design: private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.15 (rich-target block), §3.2 (cross-role audio), §6.2 C7,
§6.6 M2d; contract aln33_env64_125ms_v1 (auditory_alignment_v3.prior33.contract: h_aa, the 2-8 Hz SOS, rms_norm, TICK_OFFS,
SPAN_EEG, RICH_SEEDS, RICH_COLS); inherited PUBLIC_PRIOR_EXECUTION_v3_3.md §4 (spectral structure / change heads only for sources
with a waveform; missing targets masked, never zero-filled; explicit source and extractor version) and §3 (sound statistics from
donor fit only, deduplicated by content). The inherited contract and the design agree on everything used here.

CLI (a CPU Slurm job through slurm/aln33_prior_cpu.sbatch, which the lead schedules; always run with -m, never by path):
  python -m auditory_alignment_v3.prior33.build_rich --out <cache root> [--cohort all | sparrkulee,fau,dtu,federici]
  e.g. sbatch -J c3_p33c7 -c 4 --mem=16G slurm/aln33_prior_cpu.sbatch -m auditory_alignment_v3.prior33.build_rich \
       --out /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1
  <cache root> = CACHE_ROOT (§6.2). Production writes only there and only from main(): the inputs are that root's own C4 / C5 / C3
  outputs, the sources are the pinned dataset paths (SOURCES_DEFAULT) and the extractor is the pinned Whisper snapshot.
  Order and exit codes. C7 reads C4's SparrKULee tables and C5's public tables (--cohort sparrkulee needs only C4), so it runs after
  C4 and C5. Pass 1 (waveform checks, Whisper log-mel, clock checks: nearly all of the hour) needs nothing from C3 and may run
  while C3 runs. The PCA-4 basis and sigma use C3's shared-audio mask (<root>/scan_audio.json whose scan_audio.latest.json pointer
  says status ok for its sha256, ok and complete true): a production build without such a C3 result completes pass 1, writes no
  rich output and exits 5; the same command after C3 reuses every pass-1 marker and finishes in minutes. Exit 0 done, 5 waiting
  for C3, 1 error, 2 usage error. C6 runs after C7.
  Dry runs: any other --out (outside /projects/EEG-foundation-model) needs --allow-other-out and may add --tables <root>
  (read-only C4 / C5 tables, e.g. the cache root), --streams cohort:name,... (a subset; every other stream of a cohort it names is
  masked 'not_selected_dry_run', cohorts it does not name are processed whole), --scan <scan_audio.json> (default:
  <tables>/scan_audio.json when present; a present file must be current) or --no-scan (the basis without C3's mask, recorded as
  such), and source overrides (--sparrkulee, --fau-stimuli, --fau-logmel, --dtu-inventory, --dtu-audio, --whisper). SparrKULee is
  always processed (it carries the PCA-4 basis and sigma); --cohort selects the public cohorts.
  Inputs: C4 (build_sparrkulee.py) <root>/sparrkulee/{streams.json, env_f32.npy, runs.json} (+ C1 runs_table.json when present),
  C5 (build_public.py) <root>/<fau|dtu|federici>/{streams.json, env_f32.npy} (+ pieces.json, hashed only) and C3 (scan_audio.py)
  <root>/scan_audio.json shared_audio['sparrkulee']. For SparrKULee the design's "C1's stream table" is C4's streams.json (C1
  writes no stream table). Resumable per stream (done markers, tmp + os.replace); one build per output root at a time (flock on
  <out>/.c7_build.lock); byte-deterministic outputs on the same machine, libraries and thread count (sorted JSON keys, no
  timestamps). About 30-60 min; peak RSS about 2-3 GB (estimated for the longest SparrKULee stimulus, podcast_9, 19.9 min of 48 kHz
  float audio and its 16 kHz Hilbert transform; 0.98 GB measured on the dry runs).

Sources (design §2.15; real waveforms only):
  sparrkulee  stimuli/eeg/<stim>.npz.gz of every C4 stream: read as bytes, gunzipped in memory (at most MAX_NPZ_BYTES) and opened
              with np.load(..., allow_pickle=False). It must hold exactly the members 'audio' (a .npy array: numeric, finite, 1-D,
              or 2-D with <= 8 channels on the shorter axis) and 'fs' (a .npy numeric scalar, an integer >= 16000); anything else,
              including a member that is not a .npy array (numpy then returns raw bytes), -> 'waveform_unavailable'. Nothing is
              unpickled (object members raise inside np.load), no dataset code runs, noise_* / t_* files are never read, and when
              C1's runs_table.json is present every non-restricted run's events stim_file must be eeg/<stim>.npz.gz. The Whisper
              log-mel is computed here. Two fit stimuli were presented in noise (audiobook_7_5 at -4 dB, 7_6 at +2.5 dB SNR): their
              rich targets, like their envelopes, describe the clean stimulus (rows record listening_conditions from runs.json).
  fau         single-talker codes only: fau_tud/stimuli/stimuli/S<code>.wav (48 kHz) and the existing
              c3_features_v1/fau_tud/whisper_logmel128.h5 <code>/attended/logmel (128 x 100 Hz, float16; auditory_c3.features
              run_whisper). The waveform is the channel of S<code>.wav whose int32 bytes have the sha256 that the log-mel group
              records (wav_sha256; the log-mel was computed from that exact channel, the HDF5 stimulus copy) and its 16 kHz length
              must equal the group's n_samples_16k; otherwise 'waveform_unavailable'. Competing-talker attended streams:
              'no_waveform_competing_talker'; distractors: 'not_a_target_stream'.
  dtu         NH originals only (inventory.json target rows with hi false): the inventory path and the existing
              c3_features_v1/dtu/kcs_targets_v1/audio_local.h5 <sha>/logmel (prep_targets.run_dtu_audio). The waveform's mono
              int16 sha256 (features_dtu._mono16k) must equal the stream key (the C5 stream key of an attended stream is that
              sha); otherwise 'waveform_unavailable'. Streams whose sha appears only on HI (woa) rows: 'not_nh_original' (C5 makes
              them target_only); maskers: 'not_a_target_stream'; a sha without an inventory row: 'no_waveform'.
  federici    no waveform: every stream 'no_waveform' (masked, never fabricated).
  Reasons (REASONS; rich_streams.json 'reasons', 'no_source_reasons', 'read_masked_reasons'): no waveform is read for
  no_waveform, no_waveform_competing_talker, not_a_target_stream, not_nh_original and not_selected_dry_run (source_sha256 None;
  not_selected_dry_run only in dry runs, never in the cache root); a waveform is read and its stream masked for
  waveform_unavailable and clock_lag (source_sha256 set).

Chain per stream with a waveform (SCI_R2 feature definitions adapted to the shared coordinates):
  waveform -> mono (channel mean; FAU: the identified channel / 2^31) -> 16 kHz (resample_poly by Fraction(16000, fs), scipy's
  default window, as auditory_c3.features._streams / features_dtu._mono16k) -> 128-bin Whisper log-mel at 100 Hz, n100 =
  ceil(n / 160) frames, frame j centred at sample 160 j (SparrKULee: WhisperFeatureExtractor of the local offline snapshot,
  30 s windows / 20 s hop, centre-kept, stitched as prep_targets.run_dtu_audio with every frame written, see FILL_RULE; FAU / DTU:
  the stored arrays, repaired by FILL_RULE) -> 64 Hz with h_aa (contract.resample64, 727 taps; sample 0 stays the stream origin)
  -> spectral structure ss = (L - mu) V (the PCA-4 basis V, mean mu) -> spectral change sc[t] = ||ss[t] - ss[t - 1]||, sc[0] = 0
  (SCI_R2 flux of the 4-d vector) -> each of the 5 courses band-passed 2-8 Hz (contract.band with env_sos, sosfiltfilt over the
  stream) -> contract.rms_norm per stream and dimension (RMS about 0) -> float32 rows of rich_f32.npy [M, 5] (contract.RICH_COLS:
  ss0..ss3, sc), row offset + t = sample t of the stream, the same rows as env_f32.npy.
  Final frames (FILL_RULE): the producers' stitching (prep_targets.run_dtu_audio, features.run_whisper) rounds the last window's
  (hi - s) / 160, so the last frame stays 0 when n mod 160 is in 1..80 (FAU 123 and 60 of 168 DTU NH originals on the real data),
  and its float frame count int(ceil(n / 16000 * 100)) adds a never-written trailing frame for some n = 160 k. C7's own stitching
  writes every frame of [0, ceil(n / 160)). In a stored array the frames the producer never writes must hold exactly 0: one inside
  [0, ceil(n / 160)) is recomputed with the pinned extractor from the window that keeps it (cast to the stored dtype), a trailing
  one beyond it is dropped; a non-zero value there rejects the array ('waveform_unavailable'). Rows record what was done
  (final_frame). A zero frame is not data: as a value it would bias the last ~100 rows (up to 11 % of the course RMS, measured on
  audiobook_7_5 in review), and dropping it alone changes no row (resample_poly pads with zeros).
  Lengths: the stream length T is the C4 / C5 envelope length; n64 = ceil(16 n100 / 25) is known from the 16 kHz length before any
  extraction. A waveform with |n64 - T| > LEN_TOL (1 s) is not the stream's waveform ('waveform_unavailable'; clock recorded,
  no features extracted). Features longer than T are cut at T before filtering; when they end n64 < T samples in, rows
  [n64 - 41, T) stay NaN (the contract's 41-sample edge guard measured from the features' end).
Clock check (§2.15, no EEG): our envelope of the same 16 kHz waveform, |hilbert| (FFT length next_fast_len) -> 64 Hz with h_aa ->
  2-8 Hz -> rms_norm, against the stream's contract envelope (env_f32.npy): Pearson r(tau) of env[t] with ours[t + tau] over the
  overlap, tau in +-CLOCK_SEARCH (10 s); tau_hat = argmax r; z = (r(tau_hat) - mean) / SD over the lags |tau - tau_hat| > 1 s.
  Pass iff |tau_hat| <= 1 and z >= 5 (the lag is measured: C2's measurability rule); otherwise 'clock_lag' (masked and listed;
  never shifted). tau > 0: the waveform's events come tau samples after the envelope's (a lead-in of tau samples).
PCA-4 basis (SparrKULee donor fit, shared by every donor set; never refitted per cohort): FIT_RULE, i.e. C6's SparrKULee core-pool
  rule: C4 runs.json role 'fit', segments (presentation, s) with >= 2 distinct participants, minus every segment whose EEG span
  [s, s + 357) meets a C3 shared_audio span of its stream (jingles and other shared audio, §3.2: the only cross-role audio); the
  unique (stream, window start) windows w = s + TICK_OFFS[k] of those segments, on streams that passed pass 1 and inside their
  valid rows; each window contributes its 8 64 Hz log-mel frames (frame weight = number of windows that contain it); mu = weighted
  mean, covariance about mu, numpy eigh, the 4 leading eigenvectors, each sign fixed so that its largest-magnitude entry is
  positive (prep_targets._pca). Stored once (rich_pca4_f64.npy [128, 4]); reused while its marker (inputs, scan sha256 and builder
  sha) is unchanged. A dry run with --no-scan (or no scan at the table root) fits on the segments before the mask (FIT_RULE_NO_MASK,
  recorded in rich_build.json fit_mask and manifest_rich.pca4.fit).
Standardiser (contract.py docstring, "Standardiser"; design §2.15; the fixture's rule): sigma_ss [32] (8 samples x 4 dims,
  sample-major) and sigma_sc [8] = sqrt(mean_w y_w^2), the RMS about 0, over the same unique windows of the rich-available streams
  (each window once whatever its listener count); mu is 0 and the sample means are recorded only as mu_estimate_ss /
  mu_estimate_sc. With the C3 mask these are the windows of C6's core pool.
Projections: P_ss = audio_targets.semi_orthogonal(32, 32, RICH_SEEDS['ss']) and P_sc = semi_orthogonal(32, 8, RICH_SEEDS['sc']),
  float32, written once at the root under contract.RICH_P_FILE and never regenerated (an existing file is kept and its sha used).

Outputs (<out> = the cache root; JSON with sorted keys):
  <out>/<cohort>/rich_f32.npy        float32 [M, 5], M = len(<cohort>/env_f32.npy); NaN rows where a target is missing
  <out>/<cohort>/rich_streams.json   {schema, contract, cohort, builder_sha256, columns, pca4_sha256, inputs, partial, extractor,
                                      chain, clock_rule, fill_rule, len_tol, reasons, no_source_reasons, read_masked_reasons,
                                      summary, streams: [one row per stream, row i = stream i]}; a row: stream, name, key, kind,
                                      length, available, reason, detail, clock_lag, clock {tau, r_peak, r_at_0, z, measurable, ok,
                                      ...}, extractor, origin, source, source_sha256 (sha256 of the waveform file's bytes; None
                                      exactly when no waveform is read: reason in NO_SOURCE), audio_sha256 (the samples used: SK the
                                      audio member's bytes, FAU the channel's int32 bytes, DTU the mono int16 sha), fs_waveform,
                                      n_samples (at fs_waveform), n_channels, n_samples_16k, n_64_expected, feature_source
                                      (provenance of the log-mel incl. the producer's record and extractor version), final_frame,
                                      n_mel_100, n_64, valid_end (rows [offset, offset + valid_end) are finite exactly when
                                      available), rms [5], filter_sha256; SparrKULee also listening_conditions, stim_file_check
  <out>/rich_pca4_f64.npy            float64 [128, 4]
  <out>/P_ss_32x32_seed20261017_f32.npy, <out>/P_sc_32x8_seed20261018_f32.npy
  <out>/rich_build.json              {schema, ..., manifest_rich (the manifest's 'rich' block in the fixture schema: columns,
                                      y_layout, pca4, P_ss, P_sc, sigma_ss, sigma_sc, mu_estimate_ss, mu_estimate_sc, n_windows,
                                      loss_weights), fit_mask, pca, standardiser, projections, extractor, extractor_check,
                                      cohorts, ...}
  work: <out>/<cohort>/_c7_work/<stream>.npy (float32 [n_64, 128] log-mel at 64 Hz, about 2.2 GB in all, kept: this module deletes
  nothing) and <out>/<cohort>/_c7_done/<stream>.json (pass-1 markers), <out>/_c7_pca.json (the basis marker).

Data-use guards (enforced in code; tests in tests/auditory_alignment_v3/prior33/test_build_rich.py): every file is opened through
check_path(), which raises RestrictedAccess for a path that names a restricted SparrKULee participant (sub-019/020/021/022/026 as a
path component, a file prefix sub-XXX_ / sub-XXX- or a file stem sub-XXX.<ext>, under a component containing 'sparrkulee' or under
a registered SparrKULee source tree (the pinned one and any --sparrkulee override), as given and resolved); C7 opens no EEG file at
all; a restricted participant with any role other than 'restricted' in runs.json raises RestrictedAccess before any window is
formed; .npz.gz only via gzip + np.load(allow_pickle=False), .npy only with allow_pickle=False, WAV via scipy.io.wavfile /
soundfile, HDF5 via h5py, JSON via json: nothing is unpickled and nothing from a dataset's code/ runs. Outputs: check_out() (as
build_sparrkulee.check_out).

Interpretations (the design names the step, not the detail; each is listed as a deviation in the M2d summary):
- File build_rich.py (the task) instead of §6.1's rich_build.py; slurm/aln33_prior_cpu.sbatch line 23 still names rich_build and
  passes no --out (the lead's runbook; the usage line above is the working one).
- Order: C7 reads C4's SparrKULee tables and C5's public ones, so §6.2's "C7 in parallel with C4" is not possible; the basis and
  sigma use C3's shared-audio mask, so C7 finishes after C3 (pass 1 may overlap C3; exit 5 in between).
- PCA-4 fit and sigma windows: C6's core-pool rule (C3 mask applied), so the basis holds no cross-role (jingle) audio and sigma is
  the fixture's rule; the frames are weighted by the number of windows that contain them (each window contributes its 8 frames;
  |cos| >= 0.999999 against counting each frame once on the real data, review); fit and applied at 64 Hz (the log-mel is resampled
  first) and mean-centred (prep_targets._pca); the flux is taken on the unfiltered 64 Hz PCA-4 vector, then all five courses are
  band-passed (the fixture's order; SCI_R2 took the flux of band-passed 128 Hz courses); mu is immaterial after the band-pass.
- Final frames (FILL_RULE): every frame is written (C7's stitching) or recomputed (stored arrays) instead of the producers' 0;
  this departs from "exactly as prep_targets" in that one frame per affected stream (and drops a never-written trailing frame).
- Stricter than the §2.15 text, each can mask a stream the design text would keep: the archive must hold exactly the members
  {audio, fs}, both .npy arrays; fs an integer >= 16000 Hz (Whisper's 16 kHz needs no upsampling; contract §3); at most 8
  channels on the shorter axis; at most MAX_NPZ_BYTES after gunzip and per member; LEN_TOL (a 64 Hz length off by more than 1 s
  from T); the clock lag searched over +-10 s and measured (z >= 5) as well as |lag| <= 1 (reasons keep the fixture vocabulary:
  clock_lag covers both); identity checks (FAU channel sha = the log-mel's wav_sha256 and n_samples_16k; DTU mono sha = stream
  key; SparrKULee events stim_file).
- Added reasons 'not_nh_original' and 'not_selected_dry_run' (no waveform read, so NO_SOURCE grows by these two; the fixture's
  NO_SOURCE holds three): C6 must take the vocabulary from rich_streams.json, not from the fixture constant.
- Clock-masked streams have features extracted (the fixture sets their extractor) but no work file and NaN rows; a LEN_TOL
  rejection has its clock recorded but no features (extractor None, as every 'waveform_unavailable').
- An extractor consistency diagnostic: one FAU and one DTU stream's stored log-mel recomputed with the SparrKULee extractor (frames
  the producer wrote). The reused files record no transformers version (DTU: no model or revision either): rows say so and point
  at rich_build.json extractor_check.
- Hilbert with FFT length next_fast_len (a prime-length 16 kHz stream takes 14 s and 3.3 GB otherwise); edge effect only.
- sigma_ss / sigma_sc and their mean estimates are stored in rich_build.json (manifest_rich), not as separate .npy files.
- On the real C4 runs.json the pre-mask fit rule gives 1,970,250 windows, 7,881 content segments and 49 streams (design §2.3 /
  §3.2 counts); the C3 mask removes the segments that meet a jingle span (about 1.8 % of the frames, review estimate).

Interface notes for C6 (M2e), M3 and M5:
- rich_build.json manifest_rich is the manifest's 'rich' block (fixture schema). With fit_mask.applied true its sigma_* /
  mu_estimate_* / n_windows are over C6's SparrKULee core pool (C6 may recompute them with rich_standardiser(rich, streams,
  rich_rows, windows) on its pool as a check: they must agree; segment_windows() builds the windows); fit_mask records the
  scan_audio.json sha256, which C6 must find equal to the one it reads.
- Every cohort's rich_streams.json records inputs (sha256 of streams.json, env_f32.npy and the table) and pca4_sha256; C6 must
  check them against the files it reads and against manifest_rich.pca4 (a public cohort built before a basis change is stale;
  rich_build.json cohorts[c].stale says so).
- Reasons: rich_streams.json 'reasons' / 'no_source_reasons' are the vocabulary (the fixture's three no-source reasons are a
  subset); views.DonorBank reads rich_f32.npy [len(env), 5] float32 and rows' 'available'; present = available and the window
  finite (NaN rows are never zero).
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import dataclasses
import fcntl
import functools
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
import re
import sys
import warnings
import zlib
from fractions import Fraction

import numpy as np
from scipy import fft as sfft
from scipy import signal

from auditory_alignment_v3.prior33 import contract as C

COHORTS = ("sparrkulee", "fau", "dtu", "federici")
CACHE_ROOT = "/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1"
DATA_VOLUME = "/projects/EEG-foundation-model"
_PUB = "/projects/EEG-foundation-model/auditory_public"
SOURCES_DEFAULT = {
    "sparrkulee": f"{_PUB}/sparrkulee_nm000238_v1.0.0",
    "fau_stimuli": f"{_PUB}/fau_tud/stimuli/stimuli",
    "fau_logmel": f"{_PUB}/derived/c3_features_v1/fau_tud/whisper_logmel128.h5",
    "dtu_inventory": f"{_PUB}/derived/c3_features_v1/dtu/inventory.json",
    "dtu_audio": f"{_PUB}/derived/c3_features_v1/dtu/kcs_targets_v1/audio_local.h5",
    "whisper": f"{_PUB}/derived/hf_cache/hub/models--openai--whisper-large-v3/snapshots/06f233fe06e710322aca913c1bc4249a0d71fce1",
}
RESTRICTED = ("019", "020", "021", "022", "026")          # access-restricted SparrKULee participants (dataset_description Notes)

ENV, STREAMS, RUNS_TABLE = "env_f32.npy", "streams.json", "runs_table.json"
TABLE = {"sparrkulee": "runs.json", "fau": "pieces.json", "dtu": "pieces.json", "federici": "pieces.json"}
RICH, RICH_STREAMS, PCA_FILE, META, PCA_MARK = "rich_f32.npy", "rich_streams.json", "rich_pca4_f64.npy", "rich_build.json", "_c7_pca.json"
WORK, DONE, LOCK = "_c7_work", "_c7_done", ".c7_build.lock"
SCAN, SCAN_PTR, SCAN_SCHEMA, SCAN_PTR_SCHEMA = ("scan_audio.json", "scan_audio.latest.json", "prior33_scan_audio_v1",
                                                "prior33_scan_audio_latest_v1")
SCHEMA_META, SCHEMA_RICH, SCHEMA_DONE, SCHEMA_PCA = ("prior33_rich_build_v2", "prior33_rich_streams_v2", "prior33_rich_done_v2",
                                                    "prior33_rich_pca_v2")
EXIT_OK, EXIT_WAIT_C3 = 0, 5

FS_W, HOP, MEL_FS, N_MEL, PCA_K = 16000, 160, 100, 128, 4  # Whisper input rate, hop (samples), log-mel rate, bins; PCA dims
FE_FRAMES = 3000                                           # Whisper input_features frames per 30 s window
CLOCK_SEARCH, CLOCK_TOL, Z_MIN, BG_EXCL, MIN_BG = 10 * C.FS, 1, 5.0, C.FS, 32
LEN_TOL, MIN_LEN, MAX_CH = C.FS, 2 * C.FS, 8
MAX_NPZ_BYTES = 2 << 30                                    # gunzipped archive and each member (podcast_9: 0.23 GB)
NPZ_MEMBERS = ("audio", "fs")
REASONS = {   # reason -> (a waveform is read, meaning); None = available
    "no_waveform": (False, "no waveform for the stream (Federici; a missing file; a sha without an inventory row; noise_* / t_*)"),
    "no_waveform_competing_talker": (False, "FAU competing-talker attended stream: no single-talker waveform"),
    "not_a_target_stream": (False, "a distractor or masker stream (no rich target by design)"),
    "not_nh_original": (False, "DTU HI (woa) target stream: rich targets come from the NH originals only (design §2.15); "
                               "target_only in C5"),
    "not_selected_dry_run": (False, "dry runs only: a stream outside --streams (never in the cache root)"),
    "waveform_unavailable": (True, "the waveform was read and rejected: malformed, an identity / length / stored-feature check "
                                   "failed, or a silent course"),
    "clock_lag": (True, "the clock check failed (|lag| > 1 sample or the lag not measurable): masked, never shifted"),
}
NO_SOURCE = tuple(k for k, (read, _) in REASONS.items() if not read)
READ_MASKED = tuple(k for k, (read, _) in REASONS.items() if read)
TARGETS = {"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}           # design §4.3 rich_targets
LOSS_WEIGHTS = [1.0, 0.5, 0.5]                                                # design §2.15 (env, ss, sc)
Y_LAYOUT = "y_ss[k] = rich[i_k:i_k + 8, 0:4] flattened sample-major (C order) -> 32; y_sc[k] = rich[i_k:i_k + 8, 4] -> 8"
CHAIN = ("waveform -> mono -> 16 kHz (resample_poly, Fraction(16000, fs)) -> 128-bin Whisper log-mel at 100 Hz, ceil(n / 160) "
         "frames (FILL_RULE) -> 64 Hz (h_aa) -> ss = (L - mu) V (PCA-4) -> sc = ||ss[t] - ss[t-1]||, sc[0] = 0 -> 2-8 Hz (env_sos, "
         "sosfiltfilt over the stream) -> rms_norm per stream and dimension -> float32")
FILL_RULE = ("every frame j of [0, ceil(n / 160)) holds the extractor's value: C7's stitching writes all of them (the last window "
             "keeps every remaining frame); in a stored array (prep_targets.run_dtu_audio / features.run_whisper round the last "
             "window's (hi - s) / 160 and use the float frame count int(ceil(n / 16000 * 100))) the frames the producer never "
             "writes must be exactly 0: one inside [0, ceil(n / 160)) is recomputed with the pinned extractor from the window that "
             "keeps it (cast to the stored dtype), one beyond it is dropped; any non-zero value there rejects the array")
CLOCK_RULE = (f"|hilbert(x16k)| (FFT length next_fast_len) -> 64 Hz (h_aa) -> 2-8 Hz -> rms_norm vs the stream's env_f32 envelope: "
              f"Pearson r(tau) of env[t] with ours[t + tau] over the overlap, |tau| <= min({CLOCK_SEARCH}, n // 2); pass iff "
              f"|argmax| <= {CLOCK_TOL} and z >= {Z_MIN} (z over the lags more than {BG_EXCL} samples from the peak); never shifted")
_FIT_CORE = ("C4 runs.json role 'fit', segments (presentation, s) with >= 2 distinct participants{mask}; unique (stream, "
             "s + TICK_OFFS[k]) windows of the streams that passed pass 1, inside their valid rows; each window's 8 64 Hz log-mel "
             "frames")
FIT_RULE = "SparrKULee donor fit, C6's core-pool rule: " + _FIT_CORE.format(
    mask=f", minus every segment whose EEG span [s, s + {C.SPAN_EEG}) meets a C3 shared_audio span of its stream (scan_audio.json "
         "with an ok pointer)")
FIT_RULE_NO_MASK = "SparrKULee donor fit WITHOUT C3's shared-audio mask (dry run only): " + _FIT_CORE.format(mask="")
SIGMA_RULE = ("sqrt(mean over windows of y^2) per element (RMS about 0, mu fixed at 0; the sample mean recorded only as "
              "mu_estimate), each unique window once, rich-available streams only")
_DTU_VERSION = ("not recorded by the producer: audio_local.h5 has no model, revision or transformers attributes "
                "(prep_targets.run_dtu_audio loaded WhisperFeatureExtractor via auditory_c3.features._snapshot("
                "'openai/whisper-large-v3')); consistency: rich_build.json extractor_check.dtu")
_FAU_VERSION = ("model / revision as the file records them; transformers version not recorded by the producer (its .done.json "
                "records torch); consistency: rich_build.json extractor_check.fau")


class RestrictedAccess(RuntimeError):
    """A file of an access-restricted SparrKULee participant was about to be opened (or such a participant had a usable role)."""


class OutputLocationError(ValueError):
    """An output directory that the output-location rules refuse."""


class WaveformUnavailable(ValueError):
    """The stream's waveform is missing, malformed or not the stream's (it is masked, never fabricated)."""

    def __init__(self, msg, sha=None):
        super().__init__(msg)
        self.sha = sha


class ScanUnavailable(RuntimeError):
    """C3's scan_audio.json is absent or not current (scan_audio.py's pointer rule)."""


class WaitingForC3(RuntimeError):
    """Production: pass 1 is complete, but the PCA-4 basis needs a current C3 result (main() exits EXIT_WAIT_C3)."""


class _Interrupted(RuntimeError):
    pass


_CLI = object()     # main()'s token: only the CLI job, after its production checks, may write the §6.2 cache root


@dataclasses.dataclass(frozen=True)
class Sources:
    """Source locations (the defaults are the pinned dataset paths; only dry runs and tests override them)."""
    sparrkulee: str = SOURCES_DEFAULT["sparrkulee"]
    fau_stimuli: str = SOURCES_DEFAULT["fau_stimuli"]
    fau_logmel: str = SOURCES_DEFAULT["fau_logmel"]
    dtu_inventory: str = SOURCES_DEFAULT["dtu_inventory"]
    dtu_audio: str = SOURCES_DEFAULT["dtu_audio"]
    whisper: str = SOURCES_DEFAULT["whisper"]

    def trees(self):
        return (self.sparrkulee, self.fau_stimuli, os.path.dirname(self.fau_logmel), os.path.dirname(self.dtu_inventory),
                os.path.dirname(self.dtu_audio), self.whisper)


# ---------------------------------------------------------------------------------------------------------- guards
_SUB = re.compile(r"^sub-(\d+)(?:[_.\-]|$)")      # sub-XXX, sub-XXX_*, sub-XXX-*, sub-XXX.<ext>
_SK_ROOTS = set()                                 # SparrKULee source trees in use (abspath and realpath)


def _within(path, root):
    root = root.rstrip(os.sep) or os.sep
    return path == root or path.startswith(root + os.sep)


def _register_sk_root(path):
    """Mark a SparrKULee source tree, whatever its name: restricted names under it are refused (the set only grows)."""
    for p in {os.path.abspath(os.fspath(path)), os.path.realpath(os.fspath(path))}:
        _SK_ROOTS.add(p.rstrip(os.sep) or os.sep)


_register_sk_root(SOURCES_DEFAULT["sparrkulee"])


def restricted_in_path(path):
    """Restricted SparrKULee participants that `path` names (a component sub-XXX, sub-XXX_*, sub-XXX-* or sub-XXX.<ext>) under a
    component containing 'sparrkulee' or under a registered SparrKULee tree, checked as given (absolute) and resolved."""
    hits = set()
    for p in {os.path.abspath(os.fspath(path)), os.path.realpath(os.fspath(path))}:
        parts = p.split(os.sep)
        if not (any("sparrkulee" in q.lower() for q in parts) or any(_within(p, r) for r in _SK_ROOTS)):
            continue
        for q in parts:
            m = _SUB.match(q)
            if m and m.group(1) in RESTRICTED:
                hits.add(m.group(1))
    return hits


def check_path(path):
    """Every file C7 opens goes through here: a path naming a restricted SparrKULee participant raises RestrictedAccess."""
    bad = restricted_in_path(path)
    if bad:
        raise RestrictedAccess(f"{path}: names restricted SparrKULee participant(s) {sorted(bad)}; never opened")
    return os.fspath(path)


def _overlap(a, b):
    fa = {os.path.abspath(os.fspath(a)), os.path.realpath(os.fspath(a))}
    fb = {os.path.abspath(os.fspath(b)), os.path.realpath(os.fspath(b))}
    return any(_within(x, y) or _within(y, x) for x in fa for y in fb)


def check_out(out, tables=None, sources=None, _auth=None):
    """The output-location guard, run before anything is created, read or written -> (realpath(out), production). The §6.2 cache
    root is accepted only from main(); any other output must lie outside /projects/EEG-foundation-model; the output may neither
    overlap a source tree nor (unless it is the same directory) the table root."""
    if out is None or not os.fspath(out):
        raise OutputLocationError("an output root is required (no default)")
    real = os.path.realpath(os.fspath(out))
    production = real == os.path.realpath(CACHE_ROOT)
    if production and _auth is not _CLI:
        raise OutputLocationError(f"{CACHE_ROOT} (the §6.2 cache root) is written only by the CLI job: python -m "
                                  f"auditory_alignment_v3.prior33.build_rich --out {CACHE_ROOT}")
    forms = {os.path.abspath(os.fspath(out)), real}
    if not production and any(_within(f, v) for f in forms for v in {DATA_VOLUME, os.path.realpath(DATA_VOLUME)}):
        raise OutputLocationError(f"--out {out}: outside the cache root {CACHE_ROOT} nothing is written under {DATA_VOLUME}; use a "
                                  "scratch directory")
    for t in (sources or Sources()).trees():
        if _overlap(out, t):
            raise OutputLocationError(f"--out {out} overlaps the source tree {t}")
    if tables is not None and os.path.realpath(os.fspath(tables)) != real and _overlap(out, tables):
        raise OutputLocationError(f"--out {out} overlaps the table root {tables} (use the same directory or disjoint ones)")
    return real, production


# ---------------------------------------------------------------------------------------------------------- small helpers
def _log(msg):
    print(msg, flush=True)


def _code_sha():
    with open(check_path(os.path.abspath(__file__)), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _jsonable(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, bytes):
        return o.decode("utf-8", "replace")
    raise TypeError(f"not JSON serialisable: {type(o)}")


def _dumps(obj):
    return json.dumps(obj, sort_keys=True, default=_jsonable, allow_nan=False)


def _write_json(path, obj):
    check_path(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(_dumps(obj))
    os.replace(tmp, path)


def _read_json(path):
    with open(check_path(path)) as f:
        return json.load(f)


def _save_npy(path, a):
    check_path(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "wb") as f:
        np.save(f, np.ascontiguousarray(a), allow_pickle=False)
    os.replace(tmp, path)


def _load_npy(path, mmap=False):
    return np.load(check_path(path), mmap_mode="r" if mmap else None, allow_pickle=False)


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _sha_file(path, chunk=1 << 23):
    h = hashlib.sha256()
    with open(check_path(path), "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _read_bytes(path):
    with open(check_path(path), "rb") as f:
        return f.read()


def _stat(path):
    st = os.stat(check_path(path))
    return [int(st.st_size), int(st.st_mtime_ns)]


def array_sha256(a):
    """sha256 of the C-order float64 bytes of the flattened array (the fixture's rule for an array inside a container)."""
    return _sha_bytes(np.ascontiguousarray(np.asarray(a, dtype=np.float64).reshape(-1)).tobytes())


def _plain(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, np.generic):
        return v.item()
    return v


def _num(v):
    """A JSON-safe scalar (non-finite floats -> None)."""
    v = _plain(v)
    return None if isinstance(v, float) and not np.isfinite(v) else v


def _safe(i, name):
    return f"{i:05d}_" + re.sub(r"[^A-Za-z0-9_.-]", "_", str(name))[:120]


@functools.lru_cache(maxsize=1)
def _filters_cached():
    sh = C.filter_shas()
    aa16 = C.aa_fir(FS_W, 1)
    return (("aa_fir_100", sh["aa_fir_100"]), ("env_sos", sh["env_sos"]),
            ("aa_fir_16000", _sha_bytes(np.ascontiguousarray(aa16, dtype=np.float64).tobytes())))


def _filters():
    """sha256 of the filters C7 applies: h_aa 100 -> 64 Hz and the 2-8 Hz SOS (features), h_aa 16000 -> 64 Hz (clock check)."""
    return dict(_filters_cached())


# ---------------------------------------------------------------------------------------------------------- waveforms
def _scale_int(x):
    if x.dtype.kind == "i":
        return x.astype(np.float64) / float(2 ** (8 * x.dtype.itemsize - 1))
    if x.dtype.kind == "u":
        h = float(2 ** (8 * x.dtype.itemsize - 1))
        return (x.astype(np.float64) - h) / h
    return x.astype(np.float64)


def _npz_members(dec, cap):
    """The 'audio' and 'fs' members of a gunzipped .npz (np.load allow_pickle=False), each a .npy array, or WaveformUnavailable."""
    try:
        npz = np.load(io.BytesIO(dec), allow_pickle=False)
    except Exception as e:  # noqa: BLE001 - any format error (incl. pickled data, which allow_pickle=False refuses)
        raise WaveformUnavailable(f"not a .npz archive: {type(e).__name__}: {e}")
    if not isinstance(npz, np.lib.npyio.NpzFile):
        raise WaveformUnavailable(f"a single {type(npz).__name__}, not a .npz archive")
    with npz:
        names = sorted(npz.files)
        if names != sorted(NPZ_MEMBERS):
            raise WaveformUnavailable(f"members {names}, exactly {list(NPZ_MEMBERS)} expected")
        try:
            big = [i.filename for i in npz.zip.infolist() if i.file_size > cap]
        except Exception as e:  # noqa: BLE001
            raise WaveformUnavailable(f"unreadable archive directory: {type(e).__name__}: {e}")
        if big:
            raise WaveformUnavailable(f"members {big} exceed {cap} bytes")
        out = []
        for k in NPZ_MEMBERS:
            try:
                v = npz[k]
            except Exception as e:  # noqa: BLE001 - object members: np.load raises instead of unpickling
                raise WaveformUnavailable(f"member {k!r} cannot be read without pickle: {type(e).__name__}: {e}")
            if not isinstance(v, np.ndarray):   # NpzFile returns the raw bytes of a member without the .npy magic
                size = len(v) if hasattr(v, "__len__") else "?"
                raise WaveformUnavailable(f"member {k!r} is not a .npy array ({type(v).__name__} of {size})")
            out.append(v)
    return out


def read_npz_gz(raw, cap=MAX_NPZ_BYTES):
    """(audio, fs) of a SparrKULee stimuli/eeg/<stim>.npz.gz given as bytes: gunzip in memory (at most `cap` bytes), np.load(
    allow_pickle=False). The archive must hold exactly 'audio' (a .npy array: numeric, finite, 1-D or 2-D with <= MAX_CH channels on
    the shorter axis) and 'fs' (a .npy numeric scalar, an integer >= 16000). Anything else raises WaveformUnavailable; nothing is
    ever unpickled."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as g:
            dec = g.read(cap + 1)
    except (OSError, EOFError, zlib.error, ValueError) as e:
        raise WaveformUnavailable(f"not a gzip stream: {type(e).__name__}: {e}")
    if len(dec) > cap:
        raise WaveformUnavailable(f"more than {cap} bytes after gunzip")
    try:
        audio, fs = _npz_members(dec, cap)
    finally:
        del dec
    if audio.dtype.kind not in "iuf" or audio.dtype.fields is not None or audio.ndim not in (1, 2) or audio.size == 0:
        raise WaveformUnavailable(f"audio {audio.dtype} {audio.shape}: a numeric 1-D or 2-D array expected")
    if audio.ndim == 2:
        ch = int(np.argmin(audio.shape))
        if audio.shape[ch] > MAX_CH or audio.shape[ch] >= audio.shape[1 - ch]:
            raise WaveformUnavailable(f"audio {audio.shape}: no channel axis of <= {MAX_CH} channels")
    if audio.dtype.kind == "f" and not np.isfinite(audio).all():
        raise WaveformUnavailable("audio holds non-finite samples")
    if fs.dtype.kind not in "iuf" or fs.dtype.fields is not None or fs.size != 1:
        raise WaveformUnavailable(f"fs {fs.dtype} {fs.shape}: a numeric scalar expected")
    v = fs.reshape(()).item()
    if not np.isfinite(v) or v != int(v) or int(v) < FS_W:
        raise WaveformUnavailable(f"fs {v!r}: an integer sampling rate >= {FS_W} Hz expected")
    return audio, int(v)


def _mono(audio):
    a = _scale_int(np.asarray(audio))
    if a.ndim == 2:
        a = a.mean(axis=int(np.argmin(a.shape)))
    return a


def to16k(x, fs):
    """fs -> 16 kHz with resample_poly(up, down) of Fraction(16000, fs) and scipy's default window (features._streams and
    features_dtu._mono16k), float32."""
    fr = Fraction(FS_W, int(fs))
    x = np.asarray(x, dtype=np.float64)
    y = x if fr == 1 else signal.resample_poly(x, fr.numerator, fr.denominator)
    return y.astype(np.float32)


def mono16k_bytes(raw):
    """auditory_c3.features_dtu._mono16k on the file's bytes: soundfile float64, channel mean, the sha256 of the mono signal
    rounded to int16 (the DTU stream key), 44.1 -> 16 kHz (resample_poly 160 / 441) -> (float32 x16k, sha256, {n_samples (at 44.1
    kHz), n_channels})."""
    import soundfile as sf
    try:
        x, sr = sf.read(io.BytesIO(raw), dtype="float64", always_2d=True)
    except Exception as e:  # noqa: BLE001
        raise WaveformUnavailable(f"not a readable sound file: {type(e).__name__}: {e}")
    m = x.mean(1)
    h = _sha_bytes(np.round(m * 32767).astype(np.int16).tobytes())
    if sr != 44100:
        raise WaveformUnavailable(f"{sr} Hz, 44100 Hz expected (features_dtu._mono16k)")
    return signal.resample_poly(m, 160, 441).astype(np.float32), h, {"n_samples": int(x.shape[0]), "n_channels": int(x.shape[1])}


def _read_wav(raw):
    from scipy.io import wavfile
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", wavfile.WavFileWarning)
            fs, x = wavfile.read(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        raise WaveformUnavailable(f"not a readable WAV file: {type(e).__name__}: {e}")
    if x.dtype.kind not in "iuf" or x.ndim not in (1, 2) or x.size == 0:
        raise WaveformUnavailable(f"WAV data {x.dtype} {x.shape}")
    return int(fs), (x[:, None] if x.ndim == 1 else x)


def hilbert_env64(x16):
    """Our envelope of a 16 kHz waveform on the contract grid: |hilbert| (FFT length next_fast_len, cut back) -> 64 Hz (h_aa) ->
    2-8 Hz (env_sos) -> rms_norm."""
    x = np.asarray(x16, dtype=np.float64)
    e = np.abs(signal.hilbert(x, N=sfft.next_fast_len(len(x)))[:len(x)])
    try:
        return C.rms_norm(C.band(C.resample64(e, FS_W), C.env_sos()[0]))
    except ValueError as err:
        raise WaveformUnavailable(f"silent waveform: {err}")


def lagged_r(a, b, taus):
    """Pearson r(tau) of a[t] with b[t + tau] over their overlap, for each tau (exact: prefix sums and one dot product per lag)."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    na, nb = len(a), len(b)
    ca, cb = np.r_[0.0, np.cumsum(a)], np.r_[0.0, np.cumsum(b)]
    qa, qb = np.r_[0.0, np.cumsum(a * a)], np.r_[0.0, np.cumsum(b * b)]
    out = np.full(len(taus), np.nan)
    for i, tau in enumerate(np.asarray(taus, dtype=np.int64)):
        t0, t1 = max(0, -int(tau)), min(na, nb - int(tau))
        n = t1 - t0
        if n < 2:
            continue
        sa, sb = ca[t1] - ca[t0], cb[t1 + tau] - cb[t0 + tau]
        va, vb = qa[t1] - qa[t0] - sa * sa / n, qb[t1 + tau] - qb[t0 + tau] - sb * sb / n
        if va <= 0 or vb <= 0:
            continue
        out[i] = (float(np.dot(a[t0:t1], b[t0 + tau:t1 + tau])) - sa * sb / n) / np.sqrt(va * vb)
    return np.clip(out, -1.0, 1.0)


def clock_check(env_contract, env_waveform, search=CLOCK_SEARCH, tol=CLOCK_TOL, z_min=Z_MIN, bg_excl=BG_EXCL):
    """The §2.15 clock check (module docstring) -> {tau, r_peak, r_at_0, z, measurable, ok, search, ...}."""
    a, b = np.asarray(env_contract, dtype=np.float64), np.asarray(env_waveform, dtype=np.float64)
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("clock_check: non-finite envelope")
    L = int(min(search, min(len(a), len(b)) // 2))
    taus = np.arange(-L, L + 1)
    r = lagged_r(a, b, taus)
    rec = {"search": L, "tol": int(tol), "z_min": float(z_min), "bg_excl": int(bg_excl), "n_contract": len(a), "n_waveform": len(b)}
    fin = np.isfinite(r)
    if not fin.any():
        return {**rec, "tau": None, "r_peak": None, "r_at_0": None, "z": None, "measurable": False, "ok": False}
    k = int(np.nanargmax(r))
    tau = int(taus[k])
    bg = r[(np.abs(taus - tau) > bg_excl) & fin]
    z = float((r[k] - bg.mean()) / bg.std()) if len(bg) >= MIN_BG and bg.std() > 0 else None
    meas = z is not None and z >= z_min
    return {**rec, "tau": tau, "r_peak": float(r[k]), "r_at_0": float(r[L]) if fin[L] else None, "z": z, "measurable": bool(meas),
            "ok": bool(meas and abs(tau) <= tol)}


# ---------------------------------------------------------------------------------------------------------- log-mel
def producer_n100(n16k):
    """The producers' frame count int(np.ceil(n / 16000 * 100)) (prep_targets.run_dtu_audio, features.run_whisper), in float
    arithmetic as they write it: n = 160 k gives k + 1 for some k (e.g. 1601, 1610)."""
    return int(np.ceil(int(n16k) / FS_W * MEL_FS))


def true_n100(n16k):
    """The frames centred inside the waveform, at samples 160 j < n: ceil(n / 160) (integer arithmetic)."""
    return -(-int(n16k) // HOP)


def n64_of(n100):
    """The 64 Hz length of an n100-frame log-mel after h_aa (resample_poly 16 / 25): ceil(16 n100 / 25)."""
    return -(-16 * int(n100) // 25)


def stitch_plan(n16k, producer=False):
    """(n100, [(s, e, a, b, A)]): the 30 s / 20 s centre-kept windows (auditory_c3.features._windows); frames f[a:b] of the window
    x[s:e] go to frames [A, A + b - a). producer=True: exactly prep_targets.run_dtu_audio's arithmetic (also features.run_whisper's)
    with n100 = producer_n100(n); otherwise C7's plan: n100 = true_n100(n) and the last window keeps every remaining frame."""
    from auditory_c3.features import _windows
    n = int(n16k)
    n100 = producer_n100(n) if producer else true_n100(n)
    plan = []
    for s, e, lo, hi in _windows(n):
        a, b, A = int(round((lo - s) / HOP)), int(round((hi - s) / HOP)), int(round(lo / HOP))
        if not producer and hi >= n:
            b = a + n100 - A
        b = min(b, a + n100 - A)
        plan.append((int(s), int(e), a, b, A))
    return n100, plan


def producer_unwritten(n16k):
    """The frames of a producer's [128, producer_n100(n)] array that its stitching never writes (left at 0): none, the last frame
    (n mod 160 in 1..80, rounding) or a trailing frame beyond ceil(n / 160) (the float frame count)."""
    n100, plan = stitch_plan(n16k, producer=True)
    w = np.zeros(n100, bool)
    for s, e, a, b, A in plan:
        w[A:A + max(b - a, 0)] = True
    return np.flatnonzero(~w)


def _input_features(fe, x):
    f = fe(x, sampling_rate=FS_W, return_tensors="np").input_features[0]
    if f.shape != (N_MEL, FE_FRAMES):
        raise RuntimeError(f"Whisper input_features {f.shape}, [{N_MEL}, {FE_FRAMES}] expected")
    return f


def stitched_logmel(x16, fe):
    """The 128-bin log-mel at 100 Hz of a 16 kHz waveform: [128, ceil(n / 160)], frame j centred at sample 160 j (time j / 100 s),
    stitched from 30 s windows (20 s hop, centre-kept) as auditory_alignment.prep_targets.run_dtu_audio, with every frame written
    (stitch_plan; FILL_RULE)."""
    x16 = np.asarray(x16, dtype=np.float32)
    n100, plan = stitch_plan(len(x16))
    mel = np.full((N_MEL, n100), np.nan, np.float32)
    for s, e, a, b, A in plan:
        mel[:, A:A + (b - a)] = _input_features(fe, x16[s:e])[:, a:b]
    if not np.isfinite(mel).all():
        raise RuntimeError("stitched_logmel: a frame was left unwritten or is non-finite (bug)")
    return mel


def stitched_frames(x16, fe, idx):
    """stitched_logmel(x16, fe)[:, idx], computed only on the windows that keep frames idx -> float32 [128, len(idx)]."""
    x16 = np.asarray(x16, dtype=np.float32)
    idx = np.asarray(idx, dtype=np.int64).reshape(-1)
    n100, plan = stitch_plan(len(x16))
    if idx.size and (idx.min() < 0 or idx.max() >= n100):
        raise ValueError(f"stitched_frames: frames {idx.tolist()} outside [0, {n100})")
    out = np.full((N_MEL, idx.size), np.nan, np.float32)
    for s, e, a, b, A in plan:
        sel = np.flatnonzero((idx >= A) & (idx < A + (b - a)))
        if sel.size:
            out[:, sel] = _input_features(fe, x16[s:e])[:, idx[sel] - A + a]
    if not np.isfinite(out).all():
        raise RuntimeError("stitched_frames: a frame is not kept by any window or is non-finite (bug)")
    return out


def reused_logmel(stored, x16, frames_fn):
    """A producer's stored log-mel [128, producer_n100(n)] of the 16 kHz waveform x16 -> (float32 [128, ceil(n / 160)], record)
    by FILL_RULE; frames_fn(x16, idx) gives the extractor's values (the pinned Whisper extractor in production)."""
    m = np.asarray(stored)
    n = len(x16)
    n100p, n100 = producer_n100(n), true_n100(n)
    if not n100 <= n100p <= n100 + 1:
        raise AssertionError(f"producer frame count {n100p} vs ceil(n / 160) = {n100}")
    if m.ndim != 2 or m.shape != (N_MEL, n100p):
        raise WaveformUnavailable(f"stored log-mel {m.shape}: [{N_MEL}, {n100p}] expected for {n} samples at 16 kHz (the producer's "
                                  "stitching)")
    if m.dtype.kind != "f" or not np.isfinite(m).all():
        raise WaveformUnavailable(f"stored log-mel {m.dtype}: finite floats expected")
    unw = producer_unwritten(n)
    if unw.size and np.any(m[:, unw] != 0):
        raise WaveformUnavailable(f"stored log-mel frames {unw.tolist()} are non-zero although the producer's stitching never writes "
                                  "them (not the producer's array)")
    fill, drop = unw[unw < n100], unw[unw >= n100]
    out = m[:, :n100].astype(np.float32)
    rec = {"rule": "FILL_RULE", "producer_n100": int(n100p), "n100": int(n100), "producer_unwritten": unw.tolist(),
           "filled": fill.tolist(), "dropped": drop.tolist(), "stored_dtype": str(m.dtype), "filled_sha256": None,
           "filled_by": None}
    if fill.size:
        v = np.asarray(frames_fn(x16, fill), dtype=np.float32)
        if v.shape != (N_MEL, fill.size) or not np.isfinite(v).all():
            raise RuntimeError(f"extractor frames {v.shape} for {fill.tolist()} (bug: not a waveform problem)")
        out[:, fill] = v.astype(m.dtype).astype(np.float32)
        rec.update(filled_sha256=array_sha256(out[:, fill]), filled_by="C7 extractor (stitched_frames), cast to the stored dtype")
    return out, rec


class WhisperLogmel:
    """The production extractor: transformers.WhisperFeatureExtractor of the local offline snapshot (preprocessor_config.json only;
    local_files_only, HF_HUB_OFFLINE), loaded on first use; `info` describes it without loading it."""

    def __init__(self, snapshot=SOURCES_DEFAULT["whisper"]):
        self.snapshot, self._fe = os.fspath(snapshot), None
        cfg = os.path.join(self.snapshot, "preprocessor_config.json")
        model = re.search(r"models--([^/]+)--([^/]+)", self.snapshot)
        self.info = {"name": "whisper_logmel128", "class": "transformers.WhisperFeatureExtractor",
                     "transformers": importlib.metadata.version("transformers"),
                     "model": f"{model.group(1)}/{model.group(2)}" if model else None, "revision": os.path.basename(self.snapshot),
                     "snapshot": self.snapshot, "preprocessor_config_sha256": _sha_file(cfg),
                     "windows": "30 s / 20 s hop, centre-kept (auditory_c3.features._windows)",
                     "stitching": "auditory_alignment.prep_targets.run_dtu_audio, every frame written (FILL_RULE)",
                     "feature_size": N_MEL, "sampling_rate": FS_W, "hop_length": HOP, "n_fft": 400, "chunk_length": 30}

    def _load(self):
        if self._fe is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            from transformers import WhisperFeatureExtractor
            check_path(self.snapshot)
            fe = WhisperFeatureExtractor.from_pretrained(self.snapshot, local_files_only=True)
            got = (type(fe).__name__, int(fe.feature_size), int(fe.sampling_rate), int(fe.hop_length), int(fe.n_fft),
                   int(fe.chunk_length))
            if got != ("WhisperFeatureExtractor", N_MEL, FS_W, HOP, 400, 30):
                raise RuntimeError(f"unexpected Whisper feature extractor {got} (info records the expected parameters)")
            self._fe = fe
        return self._fe

    def __call__(self, x16):
        return stitched_logmel(x16, self._load())

    def frames(self, x16, idx):
        return stitched_frames(x16, self._load(), idx)


def logmel64(m100):
    """[128, n100] log-mel at 100 Hz -> float32 [ceil(0.64 n100), 128] at 64 Hz (contract.resample64: h_aa, 727 taps)."""
    m = np.asarray(m100, dtype=np.float64)
    if m.ndim != 2 or m.shape[0] != N_MEL or not np.isfinite(m).all():
        raise ValueError(f"logmel64: a finite [{N_MEL}, n] log-mel expected, got {m.shape}")
    return C.resample64(m.T, MEL_FS, axis=0).astype(np.float32)


# ---------------------------------------------------------------------------------------------------------- features
def features64(L, mu, V):
    """Spectral structure ss = (L - mu) V [n, 4] and spectral change sc[t] = ||ss[t] - ss[t - 1]||, sc[0] = 0 [n], at 64 Hz."""
    ss = (np.asarray(L, dtype=np.float64) - np.asarray(mu, dtype=np.float64)) @ np.asarray(V, dtype=np.float64)
    sc = np.r_[0.0, np.linalg.norm(np.diff(ss, axis=0), axis=1)]
    return ss, sc


def valid_end(n64, T):
    """Rows [0, valid_end) of a stream of length T hold targets: T when the features cover it, else n64 - 41 (edge guard)."""
    return int(T) if n64 >= T else int(n64) - C.ENV_EDGE


def stream_features(L64, T, mu, V):
    """One stream's targets: (F float64 [n, 5] band-passed 2-8 Hz and RMS-normalised per dimension, rms [5], n, valid_end)."""
    n64 = len(L64)
    n = min(n64, int(T))
    if n < MIN_LEN or valid_end(n64, T) <= C.ENV_EDGE:
        raise WaveformUnavailable(f"features cover {n} samples, at least {MIN_LEN} expected")
    ss, sc = features64(np.asarray(L64[:n], dtype=np.float64), mu, V)
    F = C.band(np.c_[ss, sc], C.env_sos()[0], axis=0)
    try:
        F, rms = C.rms_norm(F, axis=0, return_rms=True)
    except ValueError as e:
        raise WaveformUnavailable(f"a feature course has zero RMS: {e}")
    return F, np.atleast_1d(np.asarray(rms, dtype=np.float64)), n, valid_end(n64, T)


# ---------------------------------------------------------------------------------------------------------- C3 scan
def read_scan(path, require_complete=False):
    """C3's shared-audio spans for SparrKULee -> ({stream name: sorted [[a, b), ...] 64 Hz stream samples}, record). scan_audio.py's
    rule for its readers: the pointer scan_audio.latest.json next to the file must say status ok for this file and its sha256, and
    the file must say ok (and, when required, complete); otherwise ScanUnavailable."""
    path = os.fspath(path)
    if not os.path.exists(check_path(path)):
        raise ScanUnavailable(f"no {path}")
    raw = _read_bytes(path)
    sha = _sha_bytes(raw)
    ptr_path = os.path.join(os.path.dirname(path), SCAN_PTR)
    ptr = None
    if os.path.exists(check_path(ptr_path)):
        try:
            ptr = _read_json(ptr_path)
        except ValueError:
            ptr = None
    why = []
    if not isinstance(ptr, dict):
        why.append(f"no readable {SCAN_PTR}")
    elif ptr.get("status") != "ok" or ptr.get("file") != os.path.basename(path) or ptr.get("sha256") != sha:
        why.append(f"{SCAN_PTR} says status {ptr.get('status')} for {ptr.get('file')} (sha256 {str(ptr.get('sha256'))[:16]}; "
                   f"{os.path.basename(path)} has {sha[:16]})")
    try:
        doc = json.loads(raw)
    except ValueError as e:
        raise ScanUnavailable(f"{path}: not JSON ({e})")
    doc = doc if isinstance(doc, dict) else {}
    scanned = doc.get("cohorts_scanned") or []
    if doc.get("schema") != SCAN_SCHEMA:
        why.append(f"schema {doc.get('schema')!r}, {SCAN_SCHEMA!r} expected")
    if doc.get("ok") is not True:
        why.append(f"ok = {doc.get('ok')!r}")
    if require_complete and doc.get("complete") is not True:
        why.append(f"complete = {doc.get('complete')!r} (the cache root needs C3's full run)")
    if "sparrkulee" not in scanned:
        why.append("sparrkulee was not scanned")
    if why:
        raise ScanUnavailable(f"{path}: " + "; ".join(why))
    spans = collections.defaultdict(list)
    for r in (doc.get("shared_audio") or {}).get("sparrkulee", []):
        a, b = int(r["span"][0]), int(r["span"][1])
        if not 0 <= a < b:
            raise ValueError(f"{path}: shared_audio span {r['span']} of {r['stream']} is not a half-open [a, b) with 0 <= a < b")
        spans[str(r["stream"])].append([a, b])
    spans = {k: sorted(v) for k, v in sorted(spans.items())}
    rec = {"file": path, "sha256": sha, "pointer": {k: ptr.get(k) for k in ("schema", "status", "file", "sha256", "created_utc")},
           "created_utc": doc.get("created_utc"), "builder_sha256": (doc.get("builder") or {}).get("sha256"),
           "complete": doc.get("complete"), "n_spans": int(sum(len(v) for v in spans.values())), "n_streams": len(spans),
           "shared_audio_seconds": (doc.get("shared_audio_seconds") or {}).get("sparrkulee")}
    return spans, rec


def _shared_by_stream(spans, tab):
    """{stream index: spans} of C3's per-name spans on C4's SparrKULee streams (an unknown name is a schema mismatch: raise)."""
    if spans is None:
        return None
    idx = {str(r["name"]): int(r["stream"]) for r in tab.streams}
    bad = sorted(set(spans) - set(idx))
    if bad:
        raise ValueError(f"scan_audio.json shared_audio['sparrkulee'] names streams {bad[:5]} that C4's streams.json does not hold")
    return {idx[k]: v for k, v in spans.items()}


# ---------------------------------------------------------------------------------------------------------- windows, PCA, sigma
def segment_windows(pairs):
    """{stream: sorted unique window starts s + TICK_OFFS[k]} of (stream, segment start s) pairs: each window once."""
    by = collections.defaultdict(list)
    for st, s in pairs:
        by[int(st)].append(int(s))
    return {st: np.unique(np.add.outer(np.asarray(v, dtype=np.int64), C.TICK_OFFS.astype(np.int64)).ravel()) for st, v in sorted(by.items())}


def sk_fit_segments(runs, shared=None):
    """The eligible SparrKULee donor-fit segments of C4's runs.json rows -> (sorted unique (stream, s) pairs, stats): role 'fit',
    >= 2 distinct participants per (presentation, s), and, when `shared` {stream: [[a, b), ...]} (C3's shared-audio spans) is
    given, minus every segment whose EEG span [s, s + SPAN_EEG) meets a span of its stream (FIT_RULE; C6's core pool). A
    restricted participant with any role but 'restricted' raises RestrictedAccess before anything is formed."""
    for r in runs:
        sub = str(r.get("sub") if r.get("sub") is not None else r.get("participant"))
        if sub in RESTRICTED and r.get("role") != "restricted":
            raise RestrictedAccess(f"runs.json: restricted participant sub-{sub} has role {r.get('role')!r} ({r.get('run_id')})")
    lis, stream_of = collections.defaultdict(set), {}
    for r in runs:
        if r.get("role") != "fit" or r.get("row_offset") is None or r.get("stream") is None:
            continue
        sub = str(r.get("sub") if r.get("sub") is not None else r.get("participant"))
        p, st = r["presentation"], int(r["stream"])
        if stream_of.setdefault(p, st) != st:
            raise ValueError(f"runs.json: presentation {p} on streams {stream_of[p]} and {st}")
        for s in r["segment_starts"]:
            lis[(p, int(s))].add(sub)
    pairs = sorted({(stream_of[p], s) for (p, s), subs in lis.items() if len(subs) >= 2})
    stats = {"n_single_listener_segments": int(sum(len(v) < 2 for v in lis.values())), "shared_audio_mask": shared is not None,
             "n_segments_before_mask": len(pairs), "n_segments_masked": 0}
    if shared is not None:
        keep = [(st, s) for st, s in pairs if not any(a < s + C.SPAN_EEG and s < b for a, b in shared.get(st, ()))]
        stats["n_segments_masked"] = len(pairs) - len(keep)
        pairs = keep
    stats["n_segments"] = len(pairs)
    return pairs, stats


def sk_fit_windows(runs, shared=None):
    """The C7 fit windows: {stream: unique window starts} of sk_fit_segments(runs, shared), and stats."""
    pairs, stats = sk_fit_segments(runs, shared)
    W = segment_windows(pairs)
    return W, {**stats, "n_windows": int(sum(len(v) for v in W.values())), "n_streams": len(W)}


def _frame_weights(w, n):
    """Frames [0, n): the number of 8-sample windows starting at w that contain each frame."""
    w = np.asarray(w, dtype=np.int64)
    d = np.bincount(w, minlength=n + C.N_TGT) - np.bincount(w + C.N_TGT, minlength=n + C.N_TGT)
    return np.cumsum(d)[:n].astype(np.float64)


def pca_fit(items):
    """Weighted PCA-4 of (L [n, 128], window starts w) items (each window's 8 frames) -> (V [128, 4], mu [128], record)."""
    S0, S1, S2, nu = 0.0, np.zeros(N_MEL), np.zeros((N_MEL, N_MEL)), 0
    for L, w in items:
        L = np.asarray(L, dtype=np.float64)
        c = _frame_weights(w, len(L))
        S0 += float(c.sum())
        S1 += c @ L
        S2 += (L * c[:, None]).T @ L
        nu += int((c > 0).sum())
    if S0 <= 0:
        raise ValueError("pca_fit: no fit window (a dry run must select at least one SparrKULee donor-fit stream)")
    mu = S1 / S0
    cov = S2 / S0 - np.outer(mu, mu)
    cov = 0.5 * (cov + cov.T)
    ev, vec = np.linalg.eigh(cov)
    order = np.argsort(ev)[::-1]
    V = vec[:, order[:PCA_K]].copy()
    sgn = np.sign(V[np.argmax(np.abs(V), axis=0), np.arange(PCA_K)])
    V *= np.where(sgn == 0, 1.0, sgn)
    lead = ev[order[:PCA_K]]
    return V, mu, {"eigenvalues": lead.tolist(), "total_variance": float(ev.sum()),
                   "explained_variance_ratio": (lead / ev.sum()).tolist(), "n_frames_weighted": S0, "n_unique_frames": nu,
                   "sign_rule": "each column's largest-magnitude entry positive (prep_targets._pca)"}


def rich_standardiser(rich, streams, rich_rows, windows):
    """sigma_ss [32] / sigma_sc [8] (SIGMA_RULE) over `windows` {stream: unique window starts} of a cohort's rich_f32.npy rows;
    windows of unavailable streams or with a non-finite value are left out and counted (n_windows_missing)."""
    s1, s2, n, miss = np.zeros(40), np.zeros(40), 0, 0
    for st, ws in sorted(windows.items()):
        ws = np.asarray(ws, dtype=np.int64)
        if not len(ws):
            continue
        if not rich_rows[st]["available"]:
            miss += len(ws)
            continue
        off, T = int(streams[st]["offset"]), int(streams[st]["length"])
        if ws.min() < 0 or ws.max() + C.N_TGT > T:
            raise ValueError(f"rich_standardiser: stream {st} windows leave [0, {T})")
        Y = np.asarray(rich[off + ws[:, None] + np.arange(C.N_TGT)], dtype=np.float64)          # [n_w, 8, 5]
        ok = np.isfinite(Y).all(axis=(1, 2))
        miss += int((~ok).sum())
        Y = Y[ok]
        Z = np.concatenate([Y[..., :4].reshape(len(Y), -1), Y[..., 4]], axis=1)                  # [n_w, 32 + 8], sample-major
        s1 += Z.sum(0)
        s2 += (Z ** 2).sum(0)
        n += len(Z)
    if n == 0:
        raise ValueError("rich_standardiser: no finite window")
    sig, mu = np.sqrt(s2 / n), s1 / n
    return {"sigma_ss": sig[:32].tolist(), "sigma_sc": sig[32:].tolist(), "mu_estimate_ss": mu[:32].tolist(),
            "mu_estimate_sc": mu[32:].tolist(), "abs_mu_over_sigma_max_ss": float(np.abs(mu[:32] / sig[:32]).max()),
            "abs_mu_over_sigma_max_sc": float(np.abs(mu[32:] / sig[32:]).max()), "n_windows": int(n), "n_windows_missing": int(miss),
            "rule": SIGMA_RULE}


def rich_projections(out):
    """P_ss / P_sc (module docstring): generated once with audio_targets.semi_orthogonal, never regenerated -> {k: record}."""
    from auditory_alignment_v2.audio_targets import semi_orthogonal
    rec = {}
    for k in ("ss", "sc"):
        path, shape, seed = os.path.join(out, C.RICH_P_FILE[k]), C.RICH_P_SHAPE[k], C.RICH_SEEDS[k]
        fresh = semi_orthogonal(shape[0], shape[1], seed).numpy().astype(np.float32)
        kept = os.path.exists(path)
        if kept:
            P = _load_npy(path)
            if P.dtype != np.float32 or P.shape != shape:
                raise ValueError(f"{path}: float32 {shape} expected, got {P.dtype} {P.shape}; move it away (it is never regenerated)")
        else:
            P = fresh
            _save_npy(path, P)
        rec[k] = {"file": C.RICH_P_FILE[k], "sha256": _sha_bytes(np.ascontiguousarray(P).tobytes()), "seed": seed, "shape": list(shape),
                  "kept_existing": kept, "equals_fresh_generation": bool(np.array_equal(P, fresh)),
                  "generator": "auditory_alignment_v2.audio_targets.semi_orthogonal"}
    return rec


# ---------------------------------------------------------------------------------------------------------- tables
def _tables_missing(root, cohorts):
    miss = {}
    for c in cohorts:
        need = (STREAMS, ENV) + ((TABLE["sparrkulee"],) if c == "sparrkulee" else ())
        m = [f for f in need if not os.path.exists(check_path(os.path.join(root, c, f)))]
        if m:
            miss[c] = m
    return miss


class _Tables:
    """One cohort's C4 / C5 tables (read-only): streams.json rows, env_f32.npy (memmap), the input hashes; SparrKULee also runs."""

    def __init__(self, root, cohort):
        d = os.path.join(root, cohort)
        self.cohort, self.dir = cohort, d
        self.streams = _read_json(os.path.join(d, STREAMS))["streams"]
        self.env = _load_npy(os.path.join(d, ENV), mmap=True)
        if self.env.dtype != np.float32 or self.env.ndim != 1:
            raise ValueError(f"{d}/{ENV}: float32 [M] expected, got {self.env.dtype} {self.env.shape}")
        off = 0
        for i, r in enumerate(self.streams):
            if int(r["stream"]) != i or int(r["offset"]) != off or int(r["length"]) <= 0:
                raise ValueError(f"{d}/{STREAMS}: stream {i} ({r.get('name')}) is not at offset {off} in stream order")
            off += int(r["length"])
        if off != len(self.env):
            raise ValueError(f"{d}: streams cover {off} samples, {ENV} holds {len(self.env)}")
        self.inputs = {"streams_sha256": _sha_file(os.path.join(d, STREAMS)), "env_sha256": _sha_file(os.path.join(d, ENV))}
        tab = os.path.join(d, TABLE[cohort])
        self.table = _read_json(tab) if os.path.exists(tab) else None
        self.inputs["table"] = TABLE[cohort]
        self.inputs["table_sha256"] = _sha_file(tab) if self.table is not None else None
        self.partial = bool((self.table or {}).get("partial", False))
        self.inputs["table_partial"] = self.partial
        self.runs, self.stim_files, self.conditions = None, None, {}
        if cohort == "sparrkulee":
            if self.table is None:
                raise FileNotFoundError(f"{tab}: C4's runs.json is required (the donor-fit windows)")
            self.runs = self.table["runs"]
            rt = os.path.join(d, RUNS_TABLE)
            self.inputs["runs_table_sha256"] = _sha_file(rt) if os.path.exists(rt) else None
            if os.path.exists(rt):
                self.stim_files = collections.defaultdict(set)
                for r in _read_json(rt)["runs"]:
                    if not r.get("restricted"):
                        self.stim_files[r["stimulus"]].add((r.get("events") or {}).get("stim_file"))
            cond = collections.defaultdict(collections.Counter)
            for r in self.runs:
                if r.get("role") == "restricted" or r.get("stream") is None:
                    continue
                cond[int(r["stream"])][(_num(r.get("snr")), _num(r.get("noise_condition")), r.get("role"))] += 1
            self.conditions = {st: [{"snr": s, "noise_condition": nc, "role": ro, "n_runs": n}
                                    for (s, nc, ro), n in sorted(c.items(), key=lambda kv: tuple(map(str, kv[0])))]
                               for st, c in cond.items()}

    def env_of(self, row):
        o = int(row["offset"])
        return np.asarray(self.env[o:o + int(row["length"])], dtype=np.float64)

    def env_sha(self, row):
        o = int(row["offset"])
        return _sha_bytes(np.ascontiguousarray(self.env[o:o + int(row["length"])]).tobytes())


def _key(row):
    return str(row.get("key") if row.get("key") is not None else row["name"])


class _Ctx:
    """Per-invocation state: sources, the extractor, the DTU inventory, lazily opened HDF5 files and their file hashes."""

    def __init__(self, sources, logmel_fn):
        self.src, self._logmel, self._h5, self._fsha, self._inv = sources, logmel_fn, {}, {}, None

    @property
    def logmel(self):
        if self._logmel is None:
            self._logmel = WhisperLogmel(self.src.whisper)
        return self._logmel

    def extractor_info(self):
        return dict(self.logmel.info)

    def h5(self, path):
        if path not in self._h5:
            import h5py
            self._h5[path] = h5py.File(check_path(path), "r")
        return self._h5[path]

    def file_sha(self, path):
        if path not in self._fsha:
            self._fsha[path] = _sha_file(path)
        return self._fsha[path]

    def producer_record(self, path):
        """The producer's <file>.done.json (as written; small JSON) and whether its sha256 is the file's -> dict or None."""
        p = f"{path}.done.json"
        if not os.path.exists(check_path(p)):
            return None
        try:
            d = _read_json(p)
        except ValueError:
            return {"file": os.path.basename(p), "readable": False}
        d = d if isinstance(d, dict) else {}
        return {"file": os.path.basename(p), "readable": True, "content": {k: _num(v) for k, v in sorted(d.items())},
                "sha256_matches_file": d.get("sha256") == self.file_sha(path) if d.get("sha256") else None}

    def inventory(self):
        if self._inv is None:
            nh, hi = {}, set()
            rows = _read_json(self.src.dtu_inventory)
            for r in sorted(rows, key=lambda r: (str(r.get("file")), str(r.get("trial")), str(r.get("kind")), str(r.get("path")))):
                if r.get("kind") != "target" or not r.get("sha") or not r.get("path"):
                    continue
                if r.get("hi"):
                    hi.add(r["sha"])
                else:
                    nh.setdefault(r["sha"], r["path"])
            self._inv = (nh, hi)
        return self._inv

    def close(self):
        for f in self._h5.values():
            f.close()
        self._h5 = {}


# ---------------------------------------------------------------------------------------------------------- pass 1
_SK_NAME, _FAU_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"), re.compile(r"^(\d{3})/(attended|distractor)$")


def plan_stream(cohort, row, ctx, selected=None):
    """Which waveform (if any) a stream's rich targets come from -> {reason (a NO_SOURCE reason or None), source, ...}."""
    name, kind = str(row["name"]), str(row.get("kind"))
    if selected is not None and name not in selected:
        return {"reason": "not_selected_dry_run", "source": None}
    if cohort == "sparrkulee":
        if not _SK_NAME.match(name):
            raise ValueError(f"sparrkulee streams.json: unexpected stream name {name!r}")
        if name.startswith(("noise_", "t_")):
            return {"reason": "no_waveform", "source": None, "detail": "noise_* / t_* files are never read"}
        path = os.path.join(ctx.src.sparrkulee, "stimuli", "eeg", f"{name}.npz.gz")
        return {"reason": None, "source": path} if os.path.exists(check_path(path)) else \
            {"reason": "no_waveform", "source": None, "detail": f"no {os.path.relpath(path, ctx.src.sparrkulee)}"}
    if cohort == "fau":
        m = _FAU_NAME.match(name)
        if kind != "attended":
            return {"reason": "not_a_target_stream", "source": None}
        if not m or m.group(2) != "attended":
            raise ValueError(f"fau streams.json: unexpected attended stream name {name!r}")
        code = m.group(1)
        if code[0] != "1":
            return {"reason": "no_waveform_competing_talker", "source": None}
        path = os.path.join(ctx.src.fau_stimuli, f"S{code}.wav")
        return {"reason": None, "source": path, "code": code, "feature_file": ctx.src.fau_logmel} if os.path.exists(check_path(path)) \
            else {"reason": "no_waveform", "source": None, "detail": f"no S{code}.wav"}
    if cohort == "dtu":
        if kind != "attended":
            return {"reason": "not_a_target_stream", "source": None}
        nh, hi = ctx.inventory()
        key = _key(row)
        if key in nh:
            return {"reason": None, "source": nh[key], "feature_file": ctx.src.dtu_audio}
        if key in hi:
            return {"reason": "not_nh_original", "source": None, "detail": "heard only by HI listeners (woa original)"}
        return {"reason": "no_waveform", "source": None, "detail": "no inventory target row"}
    return {"reason": "no_waveform", "source": None}                           # federici: no waveform


def _sk_waveform(plan, ctx, tab, row):
    path = check_path(plan["source"])
    raw = _read_bytes(path)
    sha = _sha_bytes(raw)
    want = f"eeg/{row['name']}.npz.gz"
    sf = (tab.stim_files or {}).get(row["name"])
    if sf is not None and sf != {want}:
        raise WaveformUnavailable(f"events stim_file {sorted(map(str, sf))} != {want}", sha)
    try:
        audio, fs = read_npz_gz(raw)
    except WaveformUnavailable as e:
        raise WaveformUnavailable(str(e), sha)
    del raw
    out = {"source_sha256": sha, "audio_sha256": _sha_bytes(np.ascontiguousarray(audio).tobytes()), "fs_waveform": fs,
           "n_samples": int(audio.shape[int(np.argmax(audio.shape))]), "n_channels": 1 if audio.ndim == 1 else int(min(audio.shape)),
           "audio_dtype": str(audio.dtype),
           "stim_file_check": "runs_table.json absent" if tab.stim_files is None else ("ok" if sf else "no non-restricted run")}
    x = _mono(audio)
    del audio
    out["x16"] = to16k(x, fs)
    return out


def _fau_waveform(plan, ctx):
    path, code = check_path(plan["source"]), plan["code"]
    raw = _read_bytes(path)
    sha = _sha_bytes(raw)
    f5 = ctx.h5(plan["feature_file"])
    grp = f"{code}/attended"
    if grp not in f5 or "logmel" not in f5[grp]:
        raise WaveformUnavailable(f"{os.path.basename(plan['feature_file'])} has no {grp}/logmel", sha)
    g = f5[grp]
    attrs = {k: _plain(v) for k, v in g.attrs.items()}
    if bool(attrs.get("silent", False)) or float(attrs.get("frame_rate_hz", MEL_FS)) != MEL_FS:
        raise WaveformUnavailable(f"{grp}: silent or not at {MEL_FS} Hz ({attrs})", sha)
    try:
        fs, x = _read_wav(raw)
    except WaveformUnavailable as e:
        raise WaveformUnavailable(str(e), sha)
    del raw
    hits = [c for c in range(x.shape[1]) if _sha_bytes(np.ascontiguousarray(x[:, c]).tobytes()) == attrs.get("wav_sha256")]
    if len(hits) != 1:
        raise WaveformUnavailable(f"S{code}.wav: {len(hits)} channels match the log-mel source sha256 (exactly 1 expected)", sha)
    ch = x[:, hits[0]]
    out = {"source_sha256": sha, "audio_sha256": attrs["wav_sha256"], "fs_waveform": fs, "n_samples": int(len(ch)),
           "n_channels": int(x.shape[1]), "channel": hits[0], "audio_dtype": str(ch.dtype)}
    out["x16"] = to16k(_scale_int(ch), fs)
    del x, ch
    if int(attrs.get("n_samples_16k", -1)) != len(out["x16"]):
        raise WaveformUnavailable(f"16 kHz length {len(out['x16'])} != the log-mel's n_samples_16k {attrs.get('n_samples_16k')}", sha)
    fa = {k: _plain(v) for k, v in f5.attrs.items()}
    out["logmel_stored"] = g["logmel"][()]
    out["feature_source"] = {"file": plan["feature_file"], "dataset": f"{grp}/logmel", "dtype": str(g["logmel"].dtype),
                             "array_sha256": array_sha256(out["logmel_stored"]), "file_sha256": ctx.file_sha(plan["feature_file"]),
                             "attrs": {"model": fa.get("model"), "revision": fa.get("revision"), "note": fa.get("note"),
                                       "wav_sha256": attrs.get("wav_sha256"), "n_samples_16k": attrs.get("n_samples_16k")},
                             "producer": "auditory_c3.features.run_whisper",
                             "producer_record": ctx.producer_record(plan["feature_file"]), "extractor_version": _FAU_VERSION}
    return out


def _dtu_waveform(plan, ctx, row):
    path = check_path(plan["source"])
    raw = _read_bytes(path)
    sha = _sha_bytes(raw)
    try:
        x16, h, info = mono16k_bytes(raw)
    except WaveformUnavailable as e:
        raise WaveformUnavailable(str(e), sha)
    del raw
    key = _key(row)
    if h != key:
        raise WaveformUnavailable(f"mono int16 sha256 {h[:16]} != stream key {key[:16]}", sha)
    f5 = ctx.h5(plan["feature_file"])
    if key not in f5 or "logmel" not in f5[key]:
        raise WaveformUnavailable(f"{os.path.basename(plan['feature_file'])} has no {key}/logmel", sha)
    m = f5[key]["logmel"][()]
    return {"source_sha256": sha, "audio_sha256": h, "fs_waveform": 44100, "n_samples": info["n_samples"],
            "n_channels": info["n_channels"], "audio_dtype": "soundfile float64", "x16": x16, "logmel_stored": m,
            "feature_source": {"file": plan["feature_file"], "dataset": f"{key}/logmel", "dtype": str(f5[key]["logmel"].dtype),
                               "array_sha256": array_sha256(m), "file_sha256": ctx.file_sha(plan["feature_file"]),
                               "attrs": {k: _num(v) for k, v in sorted(f5.attrs.items())},
                               "producer": "auditory_alignment.prep_targets.run_dtu_audio",
                               "producer_record": ctx.producer_record(plan["feature_file"]), "extractor_version": _DTU_VERSION}}


ORIGIN = {
    "sparrkulee": "C7: Whisper log-mel computed from stimuli/eeg/<stim>.npz.gz (gzip + np.load allow_pickle=False; members audio, fs), "
                  "every frame written (FILL_RULE)",
    "fau": "reused c3_features_v1/fau_tud/whisper_logmel128.h5 <code>/attended/logmel (auditory_c3.features.run_whisper, from the "
           "HDF5 stimulus copy), identical by sha256 to one channel of fau_tud/stimuli/stimuli/S<code>.wav; frames the producer "
           "never wrote recomputed or dropped (FILL_RULE)",
    "dtu": "reused c3_features_v1/dtu/kcs_targets_v1/audio_local.h5 <sha>/logmel (auditory_alignment.prep_targets.run_dtu_audio) of "
           "the NH original in inventory.json (mono int16 sha256 = stream key); frames the producer never wrote recomputed or "
           "dropped (FILL_RULE)",
    "federici": "no waveform (the authors' block envelopes only)",
}


def _extractor_text(cohort, ctx, fsrc=None, fill=None):
    tail = f" -> h_aa 100->64 Hz -> PCA-4 + flux -> 2-8 Hz -> RMS [{TARGETS['ss']}, {TARGETS['sc']}]"
    if cohort == "sparrkulee":
        i = ctx.extractor_info()
        return f"{i.get('name')} computed by C7 ({i.get('class', '')} {i.get('transformers', '')} {i.get('model', '')}@" \
               f"{str(i.get('revision', ''))[:8]}; every frame written)" + tail
    f = fsrc or {}
    a = f.get("attrs") or {}
    ver = f"{a.get('model')}@{str(a.get('revision'))[:8]}, transformers version not recorded by the producer" if a.get("model") \
        else "extractor version not recorded by the producer"
    rep = ""
    if fill and (fill.get("filled") or fill.get("dropped")):
        i = ctx.extractor_info()
        rev = str(i.get("revision", ""))[:8]
        rep = f"; frames {fill['filled']} recomputed by C7 ({i.get('name')} {rev})" if fill.get("filled") else ""
        rep += f"; never-written frames {fill['dropped']} dropped" if fill.get("dropped") else ""
    return f"whisper_logmel128 reused from {os.path.basename(f.get('file', '?'))} ({f.get('producer')}; {ver}; see rich_build.json " \
           f"extractor_check{rep})" + tail


def _marker_key(cohort, row, plan, tab, ctx, code_sha):
    ff = plan.get("feature_file")
    k = {"builder_sha256": code_sha, "cohort": cohort, "stream": int(row["stream"]), "name": row["name"], "key": _key(row),
         "kind": row.get("kind"), "offset": int(row["offset"]), "length": int(row["length"]), "env_sha256": tab.env_sha(row),
         "plan": {k2: v for k2, v in plan.items() if k2 != "detail"},
         "source_stat": _stat(plan["source"]) if plan.get("source") else None,
         "feature_stat": _stat(ff) if ff else None,
         "producer_record_stat": _stat(f"{ff}.done.json") if ff and os.path.exists(check_path(f"{ff}.done.json")) else None,
         "extractor": ctx.extractor_info(),
         "stim_files": sorted(map(str, (tab.stim_files or {}).get(row["name"], ()))) if cohort == "sparrkulee" else None}
    return _sha_bytes(_dumps(k).encode())


def _pass1_stream(cohort, row, plan, tab, ctx, out):
    """Validate the waveform, run the clock check and the length rule, extract (or repair) the log-mel at 64 Hz -> (record, L64
    or None)."""
    rec = {"schema": SCHEMA_DONE, "stream": int(row["stream"]), "name": row["name"], "key": _key(row), "kind": row.get("kind"),
           "length": int(row["length"]), "reason": plan["reason"], "detail": plan.get("detail"), "source": plan.get("source"),
           "source_sha256": None, "audio_sha256": None, "audio_dtype": None, "fs_waveform": None, "n_samples": None,
           "n_channels": None, "n_samples_16k": None, "n_64_expected": None, "clock": None, "clock_lag": None, "extractor": None,
           "feature_source": None, "final_frame": None, "n_mel_100": None, "n_64": None, "work": None, "work_sha256": None,
           "origin": ORIGIN[cohort], "channel": None, "stim_file_check": None,
           "listening_conditions": tab.conditions.get(int(row["stream"])) if cohort == "sparrkulee" else None}
    if plan["reason"] is not None:
        return rec, None
    try:
        if cohort == "sparrkulee":
            w = _sk_waveform(plan, ctx, tab, row)
        elif cohort == "fau":
            w = _fau_waveform(plan, ctx)
        else:
            w = _dtu_waveform(plan, ctx, row)
    except WaveformUnavailable as e:
        rec.update(reason="waveform_unavailable", detail=str(e), source_sha256=e.sha)
        return rec, None
    x16 = w.pop("x16")
    stored = w.pop("logmel_stored", None)
    rec.update({k: v for k, v in w.items() if k in rec})
    n = int(len(x16))
    n100 = true_n100(n)
    rec.update(n_samples_16k=n, n_64_expected=n64_of(n100))
    try:
        clock = clock_check(tab.env_of(row), hilbert_env64(x16))
    except WaveformUnavailable as e:
        rec.update(reason="waveform_unavailable", detail=str(e))
        return rec, None
    clock["filters"] = {"aa_fir_16000": _filters()["aa_fir_16000"], "env_sos": C.filter_shas()["env_sos"]}
    rec.update(clock=clock, clock_lag=clock["tau"])
    if abs(rec["n_64_expected"] - int(row["length"])) > LEN_TOL:
        rec.update(reason="waveform_unavailable", detail=f"64 Hz length {rec['n_64_expected']} differs from the stream's "
                                                         f"{row['length']} by more than {LEN_TOL} samples (LEN_TOL)")
        return rec, None
    if stored is None:
        m100 = np.asarray(ctx.logmel(x16), dtype=np.float32)
        if m100.shape != (N_MEL, n100) or not np.isfinite(m100).all():
            raise ValueError(f"extractor output {m100.shape} for {n} samples (bug: not a waveform problem)")
        rec["feature_source"] = {"computed_by": "C7", "extractor": ctx.extractor_info()}
        rec["final_frame"] = {"rule": "FILL_RULE", "n100": n100, "computed_by": "C7 (every frame written)",
                              "producer_unwritten": producer_unwritten(n).tolist(), "producer_n100": producer_n100(n)}
    else:
        try:
            m100, fill = reused_logmel(stored, x16, ctx.logmel.frames)
        except WaveformUnavailable as e:
            rec.update(reason="waveform_unavailable", detail=str(e))
            return rec, None
        rec["final_frame"] = fill
    del x16, stored
    L64 = logmel64(m100)
    if len(L64) != rec["n_64_expected"]:
        raise AssertionError(f"64 Hz length {len(L64)} != {rec['n_64_expected']} (bug)")
    rec.update(n_mel_100=int(m100.shape[1]), n_64=int(len(L64)),
               extractor=_extractor_text(cohort, ctx, rec["feature_source"], rec["final_frame"]))
    if not clock["ok"]:
        rec.update(reason="clock_lag", detail=f"tau {clock['tau']}, z {clock['z']}")
        return rec, None
    work = os.path.join(cohort, WORK, _safe(rec["stream"], row["name"]) + ".npy")
    _save_npy(os.path.join(out, work), L64)
    rec.update(work=work, work_sha256=_sha_bytes(np.ascontiguousarray(L64).tobytes()))
    return rec, L64


def _load_work(out, rec):
    L = _load_npy(os.path.join(out, rec["work"]))
    if L.dtype != np.float32 or L.shape != (rec["n_64"], N_MEL) or _sha_bytes(np.ascontiguousarray(L).tobytes()) != rec["work_sha256"]:
        raise RuntimeError(f"{rec['work']}: the work file does not match its marker; move {DONE}/ and {WORK}/ of the cohort away")
    return L


def _pass1(out, cohort, tab, ctx, selected, code_sha, log, state):
    recs, d = [], os.path.join(out, cohort, DONE)
    for row in tab.streams:
        plan = plan_stream(cohort, row, ctx, selected)
        if plan["reason"] in NO_SOURCE:
            recs.append(_pass1_stream(cohort, row, plan, tab, ctx, out)[0])
            continue
        key = _marker_key(cohort, row, plan, tab, ctx, code_sha)
        mpath = os.path.join(d, _safe(int(row["stream"]), row["name"]) + ".json")
        if os.path.exists(mpath):
            m = _read_json(mpath)
            if m.get("marker_key") == key and (m["reason"] is not None or (m.get("work") and os.path.exists(os.path.join(out, m["work"])))):
                recs.append(m)
                continue
        rec, _ = _pass1_stream(cohort, row, plan, tab, ctx, out)
        rec["marker_key"] = key
        _write_json(mpath, rec)
        recs.append(rec)
        state["computed"] += 1
        c = rec["clock"] or {}
        log(f"C7 {cohort} {int(row['stream']) + 1}/{len(tab.streams)} {row['name']}: {rec['reason'] or 'ok'}"
            + (f" lag {c.get('tau')} r {c.get('r_peak'):.3f} z {c.get('z') or float('nan'):.1f}" if c.get("r_peak") is not None else ""))
        if state["stop_after"] is not None and state["computed"] >= state["stop_after"]:
            raise _Interrupted(f"stopped after {state['computed']} streams (test hook)")
    return recs


# ---------------------------------------------------------------------------------------------------------- PCA and pass 2
def _fit_items(out, tab, recs, shared):
    W, stats = sk_fit_windows(tab.runs, shared)
    kept, n_out = {}, 0
    for st, w in W.items():
        rec = recs[st]
        if rec["reason"] is not None:
            n_out += len(w)
            continue
        ve = valid_end(rec["n_64"], rec["length"])
        k = w[(w >= 0) & (w + C.N_TGT <= ve)]
        n_out += len(w) - len(k)
        if len(k):
            kept[st] = k
    stats.update(n_windows_kept=int(sum(len(v) for v in kept.values())), n_windows_left_out=int(n_out),
                 fit_streams=[recs[st]["name"] for st in sorted(kept)])
    return kept, stats


def _pca(out, tab, recs, code_sha, selected, mask, shared, log):
    kept, stats = _fit_items(out, tab, recs, shared)
    wsha = _sha_bytes(b"".join(np.int64(st).tobytes() + np.ascontiguousarray(w, dtype=np.int64).tobytes() for st, w in sorted(kept.items())))
    key = _sha_bytes(_dumps({"builder_sha256": code_sha, "inputs": tab.inputs, "windows_sha256": wsha, "selected": selected,
                             "scan_sha256": mask.get("sha256"), "mask_applied": mask["applied"],
                             "fit": [[st, recs[st]["marker_key"], recs[st]["work_sha256"]] for st in sorted(kept)]}).encode())
    path, mpath = os.path.join(out, PCA_FILE), os.path.join(out, PCA_MARK)
    if os.path.exists(path) and os.path.exists(mpath):
        m = _read_json(mpath)
        V = _load_npy(path)
        if m.get("marker_key") == key and V.dtype == np.float64 and V.shape == (N_MEL, PCA_K) and \
                _sha_bytes(np.ascontiguousarray(V).tobytes()) == m["sha256"]:
            log(f"C7 PCA-4: reused {PCA_FILE} ({m['sha256'][:16]})")
            return {**m, "V": V, "mu": np.asarray(m["mean"], dtype=np.float64), "reused": True}
    V, mu, rec = pca_fit((_load_work(out, recs[st]), w) for st, w in sorted(kept.items()))
    _save_npy(path, V)
    m = {"schema": SCHEMA_PCA, "marker_key": key, "file": PCA_FILE, "sha256": _sha_bytes(np.ascontiguousarray(V).tobytes()),
         "shape": [N_MEL, PCA_K], "mean": mu.tolist(), "windows_sha256": wsha, "scan_sha256": mask.get("sha256"),
         "rule": FIT_RULE if mask["applied"] else FIT_RULE_NO_MASK, **stats, **rec}
    _write_json(mpath, m)
    how = "applied" if mask["applied"] else "NOT applied"
    log(f"C7 PCA-4 on {stats['n_windows_kept']} windows of {len(kept)} streams (C3 mask {how}, {stats['n_segments_masked']} segments "
        f"masked): explained {np.round(rec['explained_variance_ratio'], 4)}")
    return {**m, "V": V, "mu": mu, "reused": False}


def _rich_row(row, rec, pca_sha):
    r = {k: rec.get(k) for k in ("name", "key", "kind", "length", "reason", "detail", "clock", "clock_lag", "extractor", "origin",
                                 "source", "source_sha256", "audio_sha256", "audio_dtype", "fs_waveform", "n_samples", "n_channels",
                                 "n_samples_16k", "n_64_expected", "feature_source", "final_frame", "n_mel_100", "n_64", "channel",
                                 "stim_file_check", "listening_conditions")}
    r.update(stream=int(row["stream"]), available=False, valid_end=0, rms=None, pca4_sha256=pca_sha if rec["work"] else None,
             filter_sha256=None if rec["n_64"] is None else {k: v for k, v in _filters().items() if k != "aa_fir_16000"})
    return r


def _pass2(out, cohort, tab, recs, pca, log, extra):
    M = len(tab.env)
    R = np.full((M, len(C.RICH_COLS)), np.nan, dtype=np.float32)
    rows = []
    for row, rec in zip(tab.streams, recs):
        r = _rich_row(row, rec, pca["sha256"])
        if rec["reason"] is None:
            try:
                F, rms, n, ve = stream_features(_load_work(out, rec), int(row["length"]), pca["mu"], pca["V"])
            except WaveformUnavailable as e:
                r.update(reason="waveform_unavailable", detail=str(e))
            else:
                o = int(row["offset"])
                R[o:o + ve] = F[:ve].astype(np.float32)
                r.update(available=True, valid_end=int(ve), rms=rms.tolist(), n_features=int(n))
        if (r["source_sha256"] is None) != (r["reason"] in NO_SOURCE) or r["available"] != (r["reason"] is None) or \
                (r["reason"] is not None and r["reason"] not in REASONS):
            raise AssertionError(f"{cohort} {row['name']}: inconsistent rich row {r['reason']} / {r['source_sha256']}")
        rows.append(r)
    _save_npy(os.path.join(out, cohort, RICH), R)
    reasons = collections.Counter(str(r["reason"]) for r in rows)
    ff = [r["final_frame"] for r in rows if r["final_frame"]]
    doc = {"schema": SCHEMA_RICH, "contract": C.CONTRACT, "cohort": cohort, "builder_sha256": extra["code_sha"],
           "columns": list(C.RICH_COLS), "pca4_sha256": pca["sha256"], "inputs": tab.inputs, "partial": extra["partial"],
           "extractor": extra["extractor"] if cohort in ("sparrkulee", "fau", "dtu") else None, "chain": CHAIN,
           "clock_rule": CLOCK_RULE, "fill_rule": FILL_RULE, "len_tol": LEN_TOL,
           "reasons": {k: {"waveform_read": v[0], "meaning": v[1]} for k, v in REASONS.items()},
           "no_source_reasons": list(NO_SOURCE), "read_masked_reasons": list(READ_MASKED), "streams": rows,
           "summary": {"n_streams": len(rows), "n_available": sum(r["available"] for r in rows), "reasons": dict(sorted(reasons.items())),
                       "rows": M, "finite_rows": int(np.isfinite(R).all(axis=1).sum()),
                       "n_frames_recomputed": int(sum(len(f.get("filled") or []) for f in ff)),
                       "n_frames_dropped": int(sum(len(f.get("dropped") or []) for f in ff)),
                       "n_streams_producer_unwritten": int(sum(bool(f.get("producer_unwritten")) for f in ff))}}
    _write_json(os.path.join(out, cohort, RICH_STREAMS), doc)
    log(f"C7 {cohort}: {doc['summary']['n_available']}/{len(rows)} streams available, {doc['summary']['finite_rows']}/{M} rows; "
        f"reasons {doc['summary']['reasons']}; frames recomputed {doc['summary']['n_frames_recomputed']}, dropped "
        f"{doc['summary']['n_frames_dropped']}")
    return R, rows


def _extractor_check(ctx, cohort, tab, recs):
    """Diagnostic: one reused log-mel recomputed with the SparrKULee extractor, compared on the frames the producer wrote (stored
    FAU log-mel is float16)."""
    for row, rec in zip(tab.streams, recs):
        if rec["reason"] is not None or (rec.get("feature_source") or {}).get("file") is None:
            continue
        plan = plan_stream(cohort, row, ctx)
        w = _fau_waveform(plan, ctx) if cohort == "fau" else _dtu_waveform(plan, ctx, row)
        n = len(w["x16"])
        m = np.asarray(ctx.logmel(w["x16"]), dtype=np.float64)
        written = np.setdiff1d(np.arange(true_n100(n)), producer_unwritten(n))
        d = float(np.abs(m[:, written] - np.asarray(w["logmel_stored"], dtype=np.float64)[:, written]).max())
        tol = 2e-3 if cohort == "fau" else 1e-3
        return {"cohort": cohort, "stream": row["name"], "max_abs_diff": d, "tol": tol, "consistent": bool(d <= tol),
                "n_frames": int(m.shape[1]), "n_frames_compared": int(len(written)),
                "frames_not_compared": producer_unwritten(n).tolist(), "producer": w["feature_source"]["producer"],
                "producer_extractor_version": w["feature_source"]["extractor_version"], "extractor": ctx.extractor_info()}
    return None


# ---------------------------------------------------------------------------------------------------------- build
def _cohorts(cohorts):
    if isinstance(cohorts, str):
        cohorts = COHORTS if cohorts == "all" else tuple(c.strip() for c in cohorts.split(",") if c.strip())
    bad = sorted(set(cohorts) - set(COHORTS))
    if bad:
        raise ValueError(f"unknown cohorts {bad}; choose from {COHORTS}")
    return tuple(c for c in COHORTS if c in set(cohorts) | {"sparrkulee"})


def _selection(streams):
    if streams is None:
        return None
    if isinstance(streams, str):
        sel = collections.defaultdict(set)
        for item in (s.strip() for s in streams.split(",") if s.strip()):
            c, sep, n = item.partition(":")
            if not sep or c not in COHORTS or not n:
                raise ValueError(f"--streams item {item!r}: cohort:name expected")
            sel[c].add(n)
        streams = sel
    return {c: sorted(set(v)) for c, v in sorted(dict(streams).items())}


@contextlib.contextmanager
def _build_lock(out):
    """One C7 build per output root at a time (flock on <out>/.c7_build.lock; a second invocation fails at once)."""
    os.makedirs(out, exist_ok=True)
    with open(check_path(os.path.join(out, LOCK)), "a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f"{out}: another C7 build holds {LOCK}")
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _scan_state(scan, tables, require):
    """(spans or None, fit_mask record) for build(): scan 'auto' -> <tables>/scan_audio.json, None -> no mask (dry runs), or a path.
    A present scan must be current (ScanUnavailable); `require` (production) turns an absent or stale one into WaitingForC3."""
    if scan is None:
        if require:
            raise WaitingForC3("the cache root needs C3's shared-audio mask (no --no-scan)")
        return None, {"applied": False, "why": "dry run: --no-scan", "rule": FIT_RULE_NO_MASK}
    path = os.path.join(tables, SCAN) if scan == "auto" else os.fspath(scan)
    if scan == "auto" and not os.path.exists(check_path(path)) and not require:
        return None, {"applied": False, "why": f"dry run: no {SCAN} at the table root", "rule": FIT_RULE_NO_MASK}
    try:
        spans, rec = read_scan(path, require_complete=require)
    except ScanUnavailable as e:
        if require:
            raise WaitingForC3(f"no current C3 result ({e})")
        raise
    return spans, {**rec, "applied": True, "rule": FIT_RULE}


def build(out, tables=None, cohorts=COHORTS, sources=None, logmel_fn=None, streams=None, scan="auto", log=_log, _auth=None,
          _stop_after=None, _require_scan=None):
    """C7 (module docstring) -> the rich_build.json record. `out` has no default; the §6.2 cache root is accepted only from main()
    and only as a full production build (its own tables and C3 scan, the pinned sources and extractor, every stream). `logmel_fn`
    (tests): an object with .info (a JSON dict), __call__(x16k) -> float32 [128, ceil(n / 160)] and frames(x16k, idx) -> float32
    [128, len(idx)] (the same values at frames idx); `streams` {cohort: [names]} (dry runs: the other streams of a named cohort are
    masked 'not_selected_dry_run'; unnamed cohorts are processed whole); `scan` 'auto' (<tables>/scan_audio.json; production:
    required), None (dry runs: no C3 mask) or a path. Production (or _require_scan=True) without a current scan raises
    WaitingForC3 after pass 1."""
    src = sources or Sources()
    tables = os.fspath(out if tables is None else tables)
    out_real, production = check_out(out, tables, src, _auth)
    require = production if _require_scan is None else bool(_require_scan)
    cohorts, sel = _cohorts(cohorts), _selection(streams)
    if production:
        if os.path.realpath(tables) != out_real or sel is not None or src != Sources() or logmel_fn is not None or scan != "auto":
            raise OutputLocationError(f"{CACHE_ROOT}: only a full build from its own C4 / C5 / C3 outputs with the pinned sources and "
                                      "extractor writes the cache root")
    _register_sk_root(src.sparrkulee)
    miss = _tables_missing(tables, cohorts)
    if miss:
        raise FileNotFoundError(f"C7 input tables missing under {tables}: {miss} (C4 writes sparrkulee/, C5 fau/ dtu/ federici/; "
                                "--cohort sparrkulee needs only C4)")
    code_sha = _code_sha()
    tabs = {c: _Tables(tables, c) for c in cohorts}
    if production and any(t.partial for t in tabs.values()):
        raise RuntimeError(f"partial C5 tables {[c for c, t in tabs.items() if t.partial]} cannot feed the cache root")
    early = None if require else _scan_state(scan, tables, False)       # a dry run with a stale scan fails before any work
    ctx = _Ctx(src, logmel_fn)
    state = {"computed": 0, "stop_after": _stop_after}
    with _build_lock(out_real), contextlib.closing(ctx):
        P = rich_projections(out_real)
        recs = {c: _pass1(out_real, c, tabs[c], ctx, None if sel is None or c not in sel else sel[c], code_sha, log, state)
                for c in cohorts}
        spans, mask = early if early is not None else _scan_state(scan, tables, True)   # production: after pass 1 (C3 may run)
        shared = _shared_by_stream(spans, tabs["sparrkulee"])
        pca = _pca(out_real, tabs["sparrkulee"], recs["sparrkulee"], code_sha, sel, mask, shared, log)
        extra = {"code_sha": code_sha, "partial": sel is not None, "extractor": ctx.extractor_info()}
        rich, rows = {}, {}
        for c in cohorts:
            rich[c], rows[c] = _pass2(out_real, c, tabs[c], recs[c], pca, log, extra)
        W, wstats = _fit_items(out_real, tabs["sparrkulee"], recs["sparrkulee"], shared)
        std = rich_standardiser(rich["sparrkulee"], tabs["sparrkulee"].streams, rows["sparrkulee"], W)
        mask = {**mask, **{k: wstats[k] for k in ("n_segments_before_mask", "n_segments_masked", "n_segments", "n_windows_kept")}}
        checks = {c: _extractor_check(ctx, c, tabs[c], recs[c]) for c in cohorts if c in ("fau", "dtu")}
        meta = _meta(out_real, tabs, pca, P, std, extra, checks, src, sel, mask)
        _write_json(os.path.join(out_real, META), meta)
    log(f"C7 done: {out_real}/{META} (pca4 {pca['sha256'][:16]}, sigma over {std['n_windows']} windows, C3 mask "
        f"{'applied' if mask['applied'] else 'NOT applied'})")
    return meta


def _meta(out, tabs, pca, P, std, extra, checks, src, sel, mask):
    cohorts = {}
    for c in COHORTS:
        p = os.path.join(out, c, RICH_STREAMS)
        if not os.path.exists(p):
            continue
        doc = _read_json(p)
        cohorts[c] = {**doc["summary"], "masked": [{"name": r["name"], "reason": r["reason"]} for r in doc["streams"] if not r["available"]],
                      "pca4_sha256": doc["pca4_sha256"], "stale": doc["pca4_sha256"] != pca["sha256"], "inputs": doc["inputs"],
                      "rich_sha256": _sha_file(os.path.join(out, c, RICH)), "rich_streams_sha256": _sha_file(p),
                      "built_now": c in tabs, "partial": doc["partial"]}
    pca_pub = {k: v for k, v in pca.items() if k not in ("V", "mu", "marker_key", "schema")}
    manifest_rich = {"columns": list(C.RICH_COLS), "y_layout": Y_LAYOUT,
                     "pca4": {"file": PCA_FILE, "sha256": pca["sha256"], "shape": [N_MEL, PCA_K], "fit": mask["rule"]},
                     **{f"P_{k}": {f: P[k][f] for f in ("file", "sha256", "seed", "shape")} for k in ("ss", "sc")},
                     "sigma_ss": std["sigma_ss"], "sigma_sc": std["sigma_sc"], "mu_estimate_ss": std["mu_estimate_ss"],
                     "mu_estimate_sc": std["mu_estimate_sc"], "n_windows": std["n_windows"], "loss_weights": LOSS_WEIGHTS}
    notes = ["rows are NaN where a target is missing; a stream is usable iff its rich_streams row is available",
             "reasons: rich_streams.json 'reasons' / 'no_source_reasons' are the vocabulary (the M1 fixture's three no-source reasons "
             "are a subset: not_nh_original and not_selected_dry_run are added)"]
    notes.append("sigma_ss / sigma_sc / n_windows are over C6's SparrKULee core-pool windows (FIT_RULE, C3 mask applied; fit_mask "
                 "records the scan sha256); C6 may recompute them with build_rich.rich_standardiser as a check" if mask["applied"] else
                 "DRY RUN without C3's shared-audio mask: the basis and sigma are not the cache root's (FIT_RULE_NO_MASK)")
    return {"schema": SCHEMA_META, "contract": C.CONTRACT, "builder_sha256": extra["code_sha"], "partial": extra["partial"],
            "selected_streams": sel, "cohorts_built_now": list(tabs), "manifest_rich": manifest_rich, "targets": TARGETS,
            "fit_mask": mask, "pca": pca_pub, "standardiser": std, "extractor": extra["extractor"], "extractor_check": checks,
            "projections": {k: {f: v for f, v in P[k].items() if f != "kept_existing"} for k in P},   # resumption-invariant
            "chain": CHAIN, "clock_rule": CLOCK_RULE, "fill_rule": FILL_RULE, "filters": _filters(), "cohorts": cohorts,
            "reasons": {k: {"waveform_read": v[0], "meaning": v[1]} for k, v in REASONS.items()},
            "sources": dataclasses.asdict(src), "inputs": {c: t.inputs for c, t in tabs.items()}, "notes": notes}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m auditory_alignment_v3.prior33.build_rich",
                                 description="E34_PUBLIC_PRIOR C7: the rich-target cache (PUBLIC_PRIOR_DESIGN.md §2.15, §6.2 C7). "
                                             f"Exit {EXIT_OK} done, {EXIT_WAIT_C3} pass 1 done and waiting for C3 (rerun after C3).")
    ap.add_argument("--out", required=True, help=f"the cache root {CACHE_ROOT} (production) or a scratch directory (dry run)")
    ap.add_argument("--tables", default=None, help="dry runs: the root holding the C4 / C5 tables (default: --out)")
    ap.add_argument("--cohort", default="all", help="all, or a comma list (sparrkulee is always processed)")
    ap.add_argument("--streams", default=None, help="dry runs: cohort:name,... (the other streams of a named cohort are masked "
                                                     "'not_selected_dry_run')")
    ap.add_argument("--scan", default=None, help="dry runs: C3's scan_audio.json (default: <tables>/scan_audio.json when present)")
    ap.add_argument("--no-scan", action="store_true", help="dry runs: fit the PCA-4 basis without C3's shared-audio mask (recorded)")
    ap.add_argument("--allow-other-out", action="store_true", help="allow an --out other than the cache root (dry runs)")
    for k in SOURCES_DEFAULT:
        ap.add_argument(f"--{k.replace('_', '-')}", default=None, help=f"dry runs: override {SOURCES_DEFAULT[k]}")
    a = ap.parse_args(argv)
    production = os.path.realpath(a.out) == os.path.realpath(CACHE_ROOT)
    over = {k: getattr(a, k) for k in SOURCES_DEFAULT if getattr(a, k) is not None}
    if production:
        if a.streams is not None or over or a.scan is not None or a.no_scan or \
                (a.tables is not None and os.path.realpath(a.tables) != os.path.realpath(a.out)):
            ap.error("the cache root takes a full build only: no --streams, --scan, --no-scan, source overrides or --tables other "
                     "than --out")
    elif not a.allow_other_out:
        ap.error(f"--out {a.out} is not the §6.2 cache root {CACHE_ROOT}; pass --allow-other-out for a dry run into a scratch directory")
    if a.scan is not None and a.no_scan:
        ap.error("--scan and --no-scan exclude each other")
    scan = None if a.no_scan else ("auto" if a.scan is None else a.scan)
    try:
        meta = build(a.out, tables=a.tables, cohorts=a.cohort, sources=Sources(**over), streams=a.streams, scan=scan, _auth=_CLI)
    except WaitingForC3 as e:
        _log(f"C7: pass 1 complete; waiting for C3: {e}. Rerun the same command after C3 has written scan_audio.json with an ok "
             f"pointer (pass 1 is reused); exit {EXIT_WAIT_C3}")
        return EXIT_WAIT_C3
    _log(_dumps({c: {k: v[k] for k in ("n_streams", "n_available", "reasons", "stale")} for c, v in meta["cohorts"].items()}))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
