"""E34_PUBLIC_PRIOR SparrKULee builders (module M2a): C1 run table, C2 clock-validity audit, C4 64 Hz caches.

Design: private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.1-§2.3, §2.5, §3.2, §3.4, §3.5, §6.2 (C1, C2, C4), §6.6 M2a and
the Revision log (F10, F11, F21); contract aln33_env64_125ms_v1 (auditory_alignment_v3.prior33.contract). Source: the NEMAR re-host
nm000238 v1.0.0 (docs/auditory_alignment_v3/PUBLIC_AUDITORY_PRETRAINING_RECEIPT.md), read-only.

CLI (a CPU Slurm job through slurm/aln33_prior_cpu.sbatch; always run with -m, never by path):
  python -m auditory_alignment_v3.prior33.build_sparrkulee --stage C1|C2|C4 --out <cache root> [--src <dataset root>]
      C1  [--no-hash-eeg] [--expect real|none]   -> <out>/sparrkulee/runs_table.json
      C2  [--runs run_id,run_id,...]             -> <out>/sparrkulee/align_audit.jsonl (+ align_audit_meta.json)
      C4                                         -> <out>/sparrkulee/{eeg_f16_tmajor.npy, runs.json, env_f32.npy, streams.json}
  --out is required; <cache root> is the §6.2 root /projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1.
  Any other --out needs --allow-other-out (dry runs into a scratch directory; see Output location). Under the cache root C1 always
  hashes the EEG files and asserts the real-data expectations, and C2 refuses --runs. Order: C1, then C2, then C4 (C4 reads C2).
  Every stage is resumable: C2 writes one done marker per run (reused only when it was written for the same runs_table.json and
  builder sha256), C4 one per participant plus a layout file (tmp file + os.replace); a resubmitted job continues. Outputs are
  byte-deterministic (sorted JSON keys, no timestamps); progress goes to stdout.

Output location (check_out(), run by every stage before it creates, reads or writes anything; tests in the test file):
- The §6.2 cache root is written only by the CLI job. stage_c1 / stage_c2 / stage_c4 have no default output and refuse the cache
  root unless main() calls them after its production checks; the stages repeat those checks (C1: EEG hashes and the real-data
  expectations; C2: every run, no `runs` subset).
- Any other output (a dry run, a test's tmp directory) must lie outside /projects/EEG-foundation-model (DATA_VOLUME: the dataset
  trees, the read-only legacy data .../auditory, the private area .../auditory_private) and must not overlap a dataset tree (the
  given src, the C1 table's src and SRC_DEFAULT): <out>/sparrkulee may neither lie inside it nor contain it. Paths are compared
  both as given (absolute) and resolved (os.path.realpath): a symlink to the cache root is the cache root, and a symlinked subtree
  hides neither the volume nor a dataset tree.

Data-use guards (§3.2 Exclusions, F10; enforced in code, tests in tests/auditory_alignment_v3/prior33/test_build_sparrkulee.py):
- Restricted participants sub-019/020/021/022/026 (RESTRICTED), united, before the first per-run file is touched, with every
  participant that participants.tsv (exclusion_note not n/a) or the dataset_description.json Notes name. With an expectation of the
  restricted set (--expect real), the three sources are compared with it before the run loop. C1 lists their runs from file names
  and .npy headers only: _read_npy_header opens the file with os.open, switches kernel readahead off (posix_fadvise RANDOM) and
  reads the 8-byte magic, the header-length field and the header dict with unbuffered os.read calls of exactly those sizes; the
  bytes received (128 for these files) are asserted equal to the file position and parsed by numpy's header parser from memory. So
  no array byte reaches the process (a buffered open() pulls a whole st_blksize block, 1 MiB on the /projects NFS mount, into a
  user-space buffer; what the NFS client keeps in the kernel page cache never reaches the process). C2 and C4 drop restricted runs
  before any file is opened, and every array read goes through _load_array, which raises RestrictedAccess for a path that names a
  restricted participant (directory sub-XXX or file prefix sub-XXX_); a restricted run in a reference pool or in the cache layout
  raises RestrictedAccess as well (explicit checks, not assert). Their events.tsv, raw files and arrays are never opened; they
  are never decoder references; they get no cache rows.
- Nothing is unpickled and nothing from the dataset runs: .npy files are read as bytes and parsed by np.load(..., allow_pickle=
  False) (object arrays raise); *.data_dict, *.pkl, stimuli/eeg/*.npz.gz and the dataset's code/ are never opened; the duplicate
  envelope audiobook_9_2_envelope-1.npy (any *.npy of preprocessed_stimuli that is not <stim>_envelope.npy) is listed, not read.

C1 run table (minutes; §6.2 C1). Reads participants.tsv, dataset_description.json (Notes), README.md (the trigger-flagged runs),
derivatives/preprocessed_eeg/.save_metadata.json (duplicate JSON keys detected with object_pairs_hook; outputs listed under two raw
names recorded), the 666 preprocessed EEG headers, the 72 envelope headers and the non-restricted events.tsv. Per run: sub, ses,
run, stimulus, events condition / snr / noise file, T_eeg, T_env, flags, role and the sha256 of each source file read (events.tsv,
envelopes, the metadata files; the EEG .npy bytes too unless --no-hash-eeg, never for restricted runs). Roles (§3.2, policy P2, by
session block): fit = shortstories01, varyingStories01-04 and 08-10; dev = varyingStories05-06; bridge_cal = varyingStories07;
audiobook_1-family runs of dev / bridge_cal participants -> holdout_seen_content; the insert-phone run audiobook_1_artefact ->
control_artefact; restricted participants -> restricted. Structural-anomaly rule: |T_eeg - modal T_eeg of the other non-restricted
listeners of the same presentation| > 8 samples. 64 Hz consistency (every run, headers only): 0 <= T_eeg - T_env <=
min(2100, 0.05 T_env), otherwise C1 stops (an EEG or envelope array at another rate breaks it by a factor; the 666 real headers
give 74..2005 samples and T_eeg / T_env 1.0012..1.0411). With --expect real (default) it asserts 666 runs, 85 participants, 50
restricted runs, 72 envelopes, the 3 README runs absent, the 668-entry metadata with 2 outputs listed twice and one artefact run
(sub-002 shortstories01 run-01); with any expectation it asserts that content families are disjoint across fit / dev / bridge_cal.

C2 clock-validity audit (§3.2 clock-validity rule, F11; 2-3 CPU-h). Never shifts or drops a run for weak tracking. For every
non-restricted run whose stimulus has >= 2 eligible co-listeners: a backward ridge decoder (EEG and envelope band-passed 1-8 Hz,
butter(4) sosfiltfilt, z-scored per channel over the run; 64 channels x lags 0, 4, ..., 24 samples = 0-375 ms; lambda = 1e-2 tr(G)
/ p) is trained on up to 8 other listeners of the same stimulus file (non-restricted, not structurally anomalous, other
participant; the first 8 by (sub, ses, run)), then applied to the run. Per half h of the reconstruction span r_h(tau) =
Pearson(rec[t], env[t + tau]) over the overlap, tau in [-40 s, +40 s] (+-2560 samples, exact via FFT and cumulative sums);
tau_h = argmax, z_h = (r_h(tau_h) - mean) / SD over the lags with |tau - tau_h| > 1 s. Measurable: z_h >= 5. aligned: both
measurable and |tau_1|, |tau_2| <= 4; misaligned: both measurable, |tau_1 - tau_2| <= 4 and |mean tau| > 4; unverifiable: otherwise
(including < 2 co-listeners). Sign: tau > 0 means EEG sample t pairs with envelope sample t + tau (the receipt's sub-051
audiobook_12_2 is expected at about -566). align_audit.jsonl holds one record per run of the table {run, refs, tau[2], z[2],
class, ...}, every record with the same keys (AUDIT_KEYS; a field a class does not compute is None); restricted runs appear as
class not_audited with no reference and no read. z is stored as computed (not rounded), so classify(tau, z) on a stored record
reproduces its class. Each decoded record also carries `diagnostic`: the scout's +-10 s statistics on the same reconstruction
(full run and halves), descriptive only (None where no reconstruction exists).

C4 caches (§6.2 C4; about 30-45 min). Participant by participant: read float64 -> 1-20 Hz (contract.band(x, eeg_sos()[0]), padlen
min(256, T - 1), over the whole run) -> QC mask (a channel whose SD over the run exceeds 10x or falls below 0.1x the run's median
channel SD) -> statistics (per participant x channel mean and population SD over all of that participant's cached runs, guard
samples [0, 128) and [T - 128, T) and masked (run, channel) cells excluded; data._stdz semantics) -> z -> masked cells 0 -> float16,
time-major, into eeg_f16_tmajor.npy [N, 64] (np.lib.format.open_memmap). Rows are in role slabs fit, dev, bridge_cal,
holdout_seen_content, control_artefact, excluded_rule (each run inside its slab, slabs contiguous; within a slab by (sub, ses, run)).
Final roles: restricted (no rows) > excluded_rule (C2 misaligned -> flag clock_misaligned; C1 structural anomaly whose clock is not
aligned -> structural_anomaly_unverified_clock) > the C1 role. The cache is built as eeg_f16_tmajor.partial.npy and renamed after a
full NaN / Inf scan. env_f32.npy + streams.json: every envelope file, 2-8 Hz (contract.band(e, env_sos()[0]), padlen min(128,
T - 1)) and RMS-normalised (contract.rms_norm), float32, concatenated in stream order (already 64 Hz, so no resampling). runs.json
{participants, runs, presentations, families, role_slabs, cohort_info, unit, unit_evidence, ...} in the schema of
tests/.../prior33/fixtures.py. The cache unit is decided here by UNIT_RULE of build_public.py (M2b; design §2.13 asks for one fixed
rule): no unit is documented for the derivative arrays (UNIT_DOCUMENTED), so the magnitude rule decides on the 1-20 Hz pre-z SDs of
all participants x unmasked channels, and every participant's own median must give the same unit; runs.json unit holds the rule's
record, cohort_info.unit {name 'uV' | None, source_unit, factor_to_uV, basis} the result (as pieces.json of C5), and
participants[].sd_prez_uV the uV values (sd_prez stays in the source unit). The dry-run runs give medians of about 2.6-5 (uV).

Interpretations (the design names the step but not the detail; each is a deviation of the M2a summary):
- One module for C1, C2 and C4 (the task), not cache_build.py + audit_align.py of §6.6; the CLI is --stage.
- C4 needs C2 (its excluded_rule slab and the structural rule need the audit class), so the order is C1 -> C2 -> C4 rather than
  §6.2's "C2 ... C4 in parallel".
- presentation / family ids in runs.json and streams.json are cohort-local and provisional (index in the sorted keys; id_space
  'cohort_local_provisional', the convention build_public.py shares), with the cohort-prefixed strings presentation_key
  ('sparrkulee:<stim>|<events condition>|snr=<snr>|noise=<file>') and family_name ('sparrkulee:<family>') beside them; the
  manifest builder (C6) owns the global ids and the C3-measured offsets (scan_audio.py reads the envelopes itself).
  Declared family (§2.5): audiobook_1 (0) with the halves audiobook_1_1 / _2 at +1711 / +30986, the shifted-voice copies at their
  halves' offsets, and audiobook_1_artefact with family_offset None (offset_known false) until C3 measures it.
- Presentation key = (stimulus, events condition, snr, noise file); the presentation's and the run's `condition` is the task state
  'listeningActive' (as in the fixture and §2.14: one task state per stratum), the events condition is `noise_condition`.
- run_id = sub-XXX_ses-YYY_run-NN; piece_id = sparrkulee:XXX:ses-YYY_run-NN; trial = ses-YYY_run-NN.
- runs[].flags lists only exclusion rules (fixture semantics); the structural measurement is in runs[].structural.
- C2 references: same stimulus file (same envelope) in any role; halves split the reconstruction span n = min(T_env, T_eeg - 24)
  (rows whose 7 lags all lie inside the run; the decoder rows are not zero-padded).
- CAR check: max_t |sum_ch x| / median channel SD of the 1-20 Hz pre-z signal, recorded per run (car_ok below 1e-3; the real runs
  read in the dry run give about 2e-13) and listed in runs.json sanity.car_not_ok, not fatal; NaN / Inf in any source array or in
  the float16 cache is fatal.
- C4 done markers are per participant, not per run (§6.2 says per run): the z statistics span all of a participant's runs.
- C1 hashes the EEG .npy files (minutes of reading) so that C2 and C4 can assert every array they read is the one C1 listed
  (SourceChanged otherwise); C2 and C4 record the sha256 of what they read in any case.
- runs[].role_c1 keeps the C1 role of a run that C4 relabels excluded_rule; restricted runs carry presentation None (their
  events.tsv is never read, so no presentation key is formed) and raw_file = their .npy path relative to the dataset root.
- §6.2 C1's ".save_metadata.json (with its 2 duplicate keys)" is read as its 2 outputs listed under two raw names (.bdf and
  .bdf.gz: sub-075 varyingStories09 run-03, sub-079 varyingStories10 run-07). The real file has 668 entries and 0 duplicate JSON
  keys; both counts are recorded and EXPECT_REAL asserts them.
- MIN_OVERLAP (not in §3.2): a run whose half is shorter than the +-40 s search plus 10 s (2560 + 640 samples) is unverifiable
  ("run too short"); no real run is affected (the shortest half is 3821 samples).
- C2 references leave out every run that C1 flags as structurally anomalous. §3.2 says "structurally excluded runs", but that
  exclusion needs the run's own C2 class (excluded unless aligned), so the C1 flag, a superset, is used.
- env_f32.npy / streams.json hold one stream per envelope file (stimulus), not one per presentation (§6.2): presentations that
  share a stimulus file share its stream. On the real data each stimulus has one presentation key (runs.json sanity lists any
  stimulus with several).
- participants[].masked lists the channels masked in every run of the participant (no unmasked sample for its statistics; mu 0,
  sd_prez None); the per-run QC masks are runs[].masked.
- The 64 Hz consistency rule of C1 and the uniform audit-record schema are additions (sanity checks), not design steps.

Known consequences of the literal §3.2 rule (design choices, not changed here): a consistent lag of 5-8 samples (78-125 ms) in both
halves is "misaligned" and excluded; decoder references are not purged of offset runs (with 3 offset references among 6, aligned
runs still came out within tolerance in the review's test); the C1 structural rule flags 3 real runs (sub-011 audiobook_6_1 +64,
sub-014 audiobook_4 -18, sub-014 audiobook_3 -89), each excluded unless C2 classes it aligned.

Interface notes for C6 (M2e, manifest.py) and the views / sampler (M3):
- presentation, family and stream ids in runs.json and streams.json are cohort-local (id_space 'cohort_local_provisional': the
  index in the sorted presentation keys / family names / envelope files); the fixture uses global ids. C6 must remap them into
  the manifest's id space by presentation_key, family_name and stream name, and the views must never index manifest tables with
  these table ids.
- audiobook_1_artefact has family_offset None (offset_known false, family_basis declared_family_offset_by_C3), where the fixture
  has an int: C6 takes the offset from C3 (scan_audio.json) or applies the unknown-clock fallback of §2.5.
- cohort_info.unit is set by UNIT_RULE (above), so C6 can treat SparrKULee as a mode-C donor like the C5 cohorts
  (build_public.mode_c_scales: participants with role 'fit' and donor true, sd_prez['A'] x factor_to_uV).
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import hashlib
import io
import json
import os
import re
import sys

import numpy as np
from scipy import fft as sfft
from scipy import signal

from auditory_alignment_v3.prior33 import contract as C

COHORT = "sparrkulee"
SRC_DEFAULT = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0"
CACHE_ROOT = "/projects/EEG-foundation-model/auditory_public/derived/aln33_env64_125ms_v1"
DATA_VOLUME = "/projects/EEG-foundation-model"          # outside CACHE_ROOT nothing is written here (docstring, Output location)
RUNS_TABLE, AUDIT, AUDIT_META = "runs_table.json", "align_audit.jsonl", "align_audit_meta.json"
CACHE, PARTIAL, RUNS, ENV, STREAMS = C.CACHE_FILE["A"], "eeg_f16_tmajor.partial.npy", "runs.json", "env_f32.npy", "streams.json"
C2_DONE, C4_DONE = "_c2_done", "_c4_done"
SCHEMA_TABLE, SCHEMA_RUNS, SCHEMA_STREAMS, SCHEMA_AUDIT = ("prior33_sparrkulee_runs_table_v1", "prior33_sparrkulee_runs_v1",
                                                          "prior33_sparrkulee_streams_v1", "prior33_sparrkulee_align_audit_v1")

RESTRICTED = ("019", "020", "021", "022", "026")         # access-restricted upstream (dataset_description.json Notes)
README_FLAGGED = (("006", "shortstories01", "06"), ("017", "shortstories01", "03"), ("048", "varyingStories05", "04"))
SESSION_ROLE = {"shortstories01": "fit", **{f"varyingStories{i:02d}": "fit" for i in (1, 2, 3, 4, 8, 9, 10)},
                "varyingStories05": "dev", "varyingStories06": "dev", "varyingStories07": "bridge_cal"}
DONOR_ROLES = ("fit", "dev", "bridge_cal")
SLABS = ("fit", "dev", "bridge_cal", "holdout_seen_content", "control_artefact", "excluded_rule")
TASK = "listeningActive"
AB1, ARTEFACT_STIM = "audiobook_1", "audiobook_1_artefact"
DECLARED_FAMILY = {"audiobook_1": 0, "audiobook_1_1": 1711, "audiobook_1_2": 30986, "audiobook_1_1_shifted": 1711,
                   "audiobook_1_2_shifted": 30986, ARTEFACT_STIM: None}       # §2.5; None: measured by C3 only
N_CH = 64
QC_HI, QC_LO = 10.0, 0.1                                 # §2.1 SparrKULee channel QC
STRUCT_TOL = 8                                           # §3.2 structural-anomaly rule (samples)
RATE_TAIL_MAX, RATE_TAIL_FRAC = 2100, 0.05               # C1 64 Hz consistency: 0 <= T_eeg - T_env <= min(2100, 0.05 T_env)
CAR_TOL = 1e-3
# C2 clock-validity audit (§3.2)
DEC_BAND, DEC_ORDER = (1.0, 8.0), 4
DEC_LAGS = tuple(range(0, 25, 4))                        # 0..24 samples = 0..375 ms, 7 lags
DEC_RIDGE, MAX_REFS, MIN_REFS = 1e-2, 8, 2
SEARCH, BG_EXCL, Z_MEAS, TAU_TOL = 40 * C.FS, C.FS, 5.0, 4
MIN_OVERLAP = 10 * C.FS                                  # minimum overlap of a half at the extreme lags
CLASSES = ("aligned", "misaligned", "unverifiable", "not_audited")
AUDIT_KEYS = ("run", "sub", "ses", "stimulus", "refs", "n_refs", "tau", "z", "r_peak", "r_at_0", "halves", "class", "reason",
              "diagnostic", "structural_anomaly", "runs_table_sha256", "builder_sha256", "sha256")   # every align_audit record

EXPECT_REAL = {"n_runs": 666, "n_participants": 85, "n_restricted_runs": 50, "n_envelopes": 72, "restricted": RESTRICTED,
               "readme_flagged": README_FLAGGED, "ignored_stimulus_files": ("audiobook_9_2_envelope-1.npy",),
               "save_metadata_entries": 668, "outputs_listed_twice": 2, "artefact_runs": (("002", "shortstories01", "01"),)}

EEG_RE = re.compile(r"^sub-(?P<sub>\d+)_ses-(?P<ses>[A-Za-z0-9]+)_task-(?P<task>[A-Za-z0-9]+)_run-(?P<run>\d+)"
                    r"_desc-preproc-audio-(?P<stim>.+)_eeg\.npy$")
ENV_RE = re.compile(r"^(?P<stim>.+)_envelope\.npy$")
FLAG_RE = re.compile(r"sub-(\d+)/ses-([A-Za-z0-9]+)/eeg/sub-\d+_ses-[A-Za-z0-9]+_task-[A-Za-z0-9]+_run-(\d+)_eeg\.bdf(?:\.gz)?")
_SUB_DIR, _SUB_FILE = re.compile(r"^sub-(\d+)$"), re.compile(r"^sub-(\d+)_")


class RestrictedAccess(RuntimeError):
    """An array (or any file) of an access-restricted participant was about to be opened."""


class SourceChanged(RuntimeError):
    """A source file's sha256 differs from the one C1 recorded."""


class OutputLocationError(ValueError):
    """An output directory that the Output-location rules of the module docstring refuse."""


_CLI = object()     # main()'s token: only the CLI job, after its production checks, may write the §6.2 cache root


def _within(path, root):
    root = root.rstrip(os.sep) or os.sep
    return path == root or path.startswith(root + os.sep)


def check_out(out, src=None, _auth=None):
    """The output-location guard (module docstring, Output location), run by every stage before it creates, reads or writes
    anything. Returns (os.path.realpath(out), whether out is the §6.2 cache root). Raises OutputLocationError."""
    if out is None or not os.fspath(out):
        raise OutputLocationError("an output cache root is required (the stages have no default)")
    real = os.path.realpath(os.fspath(out))
    production = real == os.path.realpath(CACHE_ROOT)
    if production and _auth is not _CLI:
        raise OutputLocationError(f"{CACHE_ROOT} (the §6.2 cache root) is written only by the CLI job: python -m "
                                  f"auditory_alignment_v3.prior33.build_sparrkulee --stage ... --out {CACHE_ROOT}")
    forms = {os.path.abspath(os.fspath(out)), real}                 # as given and resolved: a symlinked subtree changes neither
    if not production and any(_within(f, v) for f in forms for v in {DATA_VOLUME, os.path.realpath(DATA_VOLUME)}):
        raise OutputLocationError(f"--out {out}: outside the cache root {CACHE_ROOT} nothing is written under {DATA_VOLUME} (dataset "
                                  "trees, the read-only legacy data, the private area); use a scratch directory")
    for s in (src, SRC_DEFAULT):
        if s is None:
            continue
        for d in {os.path.join(f, COHORT) for f in forms}:
            for rs in {os.path.abspath(os.fspath(s)), os.path.realpath(os.fspath(s))}:
                if _within(d, rs) or _within(rs, d):
                    raise OutputLocationError(f"--out {out}: {d} overlaps the dataset tree {s}")
    return real, production


# ---------------------------------------------------------------------------------------------------------- small helpers
def _log(msg):
    print(msg, flush=True)


def _code_sha():
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _jsonable(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        v = float(o)
        return v if np.isfinite(v) else None
    if isinstance(o, np.ndarray):
        return [_jsonable(v) for v in o.tolist()] if o.dtype.kind == "f" else o.tolist()
    if isinstance(o, (set, frozenset, tuple)):
        return sorted(o) if isinstance(o, (set, frozenset)) else list(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def _clean(o):
    """Recursively replace non-finite floats by None (strict JSON) and numpy scalars by Python scalars."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        v = float(o)
        return v if np.isfinite(v) else None
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    return o


def _dumps(obj):
    return json.dumps(_clean(obj), sort_keys=True, allow_nan=False, default=_jsonable)


def _write_json(path, obj):
    tmp = f"{path}.tmp{os.getpid()}"
    with open(tmp, "w") as f:
        f.write(_dumps(obj))
    os.replace(tmp, path)


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _save_npy(path, a):
    tmp = f"{path[:-4]}.tmp{os.getpid()}.npy"
    np.save(tmp, a)
    os.replace(tmp, path)


def _sha256_file(path, chunk=1 << 23):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _cohort_dir(out, create=True):
    d = os.path.join(os.path.abspath(out), COHORT)
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def _rel(path, root):
    return os.path.relpath(path, root)


# ---------------------------------------------------------------------------------------------------------- restricted guard
def subs_in_path(path):
    """Participant ids a path names: a component 'sub-XXX' or a file name starting with 'sub-XXX_' (BIDS)."""
    out = set()
    for part in os.path.normpath(os.fspath(path)).split(os.sep):
        m = _SUB_DIR.match(part) or _SUB_FILE.match(part)
        if m:
            out.add(m.group(1))
    return out


def guard(path, restricted):
    """Raise RestrictedAccess before any open of a path that names a restricted participant."""
    hit = subs_in_path(path) & set(restricted)
    if hit:
        raise RestrictedAccess(f"refusing to open {os.path.basename(os.fspath(path))}: restricted participant(s) {sorted(hit)}")


NPY_MAGIC = b"\x93NUMPY"
NPY_LEN_FIELD = {(1, 0): 2, (2, 0): 4}                   # bytes of the little-endian header-length field per .npy version
NPY_MAX_HEADER = 10000                                   # numpy's own max_header_size; the real headers are 118 bytes


def _read_exact(fd, n, what, name):
    """Exactly n bytes from fd: unbuffered os.read calls, each asking the kernel for the bytes still missing (no read-ahead)."""
    buf = bytearray()
    while len(buf) < n:
        b = os.read(fd, n - len(buf))
        if not b:
            raise ValueError(f"{name}: end of file inside the .npy {what}")
        buf += b
    return bytes(buf)


def _read_npy_header(path):
    """The only reader that may touch a restricted participant's file (module docstring, Data-use guards): the 8-byte magic, the
    header-length field and the header dict, received with unbuffered os.read calls of exactly those sizes (kernel readahead off),
    asserted equal to the file position and parsed from memory; no array byte reaches the process. Returns shape, dtype, order,
    header and file byte counts, the bytes read, and whether the file size matches the header (an fstat, not a read)."""
    name = os.path.basename(os.fspath(path))
    fd = os.open(path, os.O_RDONLY)
    try:
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_RANDOM)
        except (AttributeError, OSError):                 # not every platform / file system takes the advice
            pass
        magic = _read_exact(fd, len(NPY_MAGIC) + 2, "magic string", name)
        if magic[:len(NPY_MAGIC)] != NPY_MAGIC:
            raise ValueError(f"{name}: not a .npy file (magic {magic[:len(NPY_MAGIC)]!r})")
        ver = (magic[-2], magic[-1])
        if ver not in NPY_LEN_FIELD:
            raise ValueError(f"{name}: unsupported .npy version {ver}")
        lf = _read_exact(fd, NPY_LEN_FIELD[ver], "header length", name)
        hlen = int.from_bytes(lf, "little")
        if hlen > NPY_MAX_HEADER:
            raise ValueError(f"{name}: .npy header of {hlen} bytes (more than {NPY_MAX_HEADER}): refused unread")
        hdr = _read_exact(fd, hlen, "header", name)
        n_read = len(magic) + len(lf) + len(hdr)
        pos = os.lseek(fd, 0, os.SEEK_CUR)
        size = os.fstat(fd).st_size
    finally:
        os.close(fd)
    if pos != n_read:
        raise RuntimeError(f"{name}: file position {pos} after the header, {n_read} bytes received")
    parse = np.lib.format.read_array_header_1_0 if ver == (1, 0) else np.lib.format.read_array_header_2_0
    shape, fortran, dtype = parse(io.BytesIO(lf + hdr))  # numpy's literal-eval header parser on the bytes already received
    nbytes = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
    return {"shape": [int(s) for s in shape], "fortran_order": bool(fortran), "dtype": dtype.str, "object": bool(dtype.hasobject),
            "version": list(ver), "header_bytes": int(n_read), "bytes_read": int(n_read), "file_bytes": int(size),
            "consistent": n_read + nbytes == size}


def _load_array(path, restricted, expect_sha=None):
    """Guarded read: bytes -> sha256 -> np.load(BytesIO, allow_pickle=False). Raises RestrictedAccess before opening a restricted
    participant's file and SourceChanged when C1 recorded a different sha256."""
    guard(path, restricted)
    with open(path, "rb") as f:
        raw = f.read()
    sha = hashlib.sha256(raw).hexdigest()
    if expect_sha is not None and sha != expect_sha:
        raise SourceChanged(f"{os.path.basename(path)}: sha256 {sha[:16]} differs from C1's {expect_sha[:16]}")
    a = np.load(io.BytesIO(raw), allow_pickle=False)
    return a, sha


def restricted_set(table=None):
    """RESTRICTED united with the participants a C1 table lists as restricted."""
    return set(RESTRICTED) | set((table or {}).get("restricted", ()))


# ---------------------------------------------------------------------------------------------------------- C1 sources
def _participants_tsv(src):
    path = os.path.join(src, "participants.tsv")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out = {}
    for r in rows:
        m = re.match(r"^sub-(\d+)$", r["participant_id"].strip())
        if not m:
            raise ValueError(f"participants.tsv: bad participant_id {r['participant_id']!r}")
        note = (r.get("exclusion_note") or "n/a").strip()
        out[m.group(1)] = {"exclusion_note": None if note in ("", "n/a") else note}
    return out, _sha256_file(path)


def _description_restricted(src):
    path = os.path.join(src, "dataset_description.json")
    d = _read_json(path)
    return sorted(set(re.findall(r"sub-(\d+)", d.get("Notes", "")))), _sha256_file(path)


def _readme_flagged(src):
    path = os.path.join(src, "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return sorted({m.groups() for m in FLAG_RE.finditer(text)}), _sha256_file(path)


def _save_metadata(src):
    path = os.path.join(src, "derivatives", "preprocessed_eeg", ".save_metadata.json")
    dup_keys = []

    def hook(pairs):
        c = collections.Counter(k for k, _ in pairs)
        dup_keys.extend(k for k, n in c.items() if n > 1)
        return dict(pairs)
    with open(path) as f:
        meta = json.load(f, object_pairs_hook=hook)
    raw_of = collections.defaultdict(list)
    for raw, outs in meta.items():
        for o in (outs if isinstance(outs, list) else [outs]):
            raw_of[o].append(raw)
    twice = {o: sorted(v) for o, v in raw_of.items() if len(v) > 1}
    return {"n_entries": len(meta), "duplicate_json_keys": sorted(set(dup_keys)), "outputs_listed_twice": twice,
            "sha256": _sha256_file(path)}, {o: sorted(v) for o, v in raw_of.items()}


def _envelopes(src):
    d = os.path.join(src, "derivatives", "preprocessed_stimuli")
    envs, ignored = {}, []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".npy"):
            continue                                         # *.data_dict (pickles) are never opened
        m = ENV_RE.match(name)
        if not m:
            ignored.append(name)                             # e.g. the duplicate audiobook_9_2_envelope-1.npy: listed, not read
            continue
        path = os.path.join(d, name)
        h = _read_npy_header(path)
        if h["object"] or not h["consistent"] or h["dtype"] not in ("<f8", "<f4") or len(h["shape"]) not in (1, 2) or \
                (len(h["shape"]) == 2 and h["shape"][1] != 1):
            raise ValueError(f"{name}: unexpected envelope array {h}")
        envs[m.group("stim")] = {"stimulus": m.group("stim"), "file": _rel(path, src), "T_env": h["shape"][0], "shape": h["shape"],
                                 "dtype": h["dtype"], "sha256": _sha256_file(path)}
    return envs, ignored


def _events(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 1:
        raise ValueError(f"{os.path.basename(path)}: {len(rows)} event rows, 1 expected")
    return rows[0]


def _na(v):
    v = (v or "").strip()
    return None if v in ("", "n/a") else v


def _snr(v):
    v = _na(v)
    return None if v is None else float(v)


def _file_na(v):
    """events.tsv file columns: 'n/a' and 'eeg/n/a' (the no_noise runs' noise_file) mean no file; else the basename."""
    v = _na(v)
    return None if v is None or v.split("/")[-2:] == ["n", "a"] else os.path.basename(v)


def family_of(stim):
    """Declared content family (§2.5) and offset: (bare name, offset or None, basis)."""
    if stim in DECLARED_FAMILY:
        return AB1, DECLARED_FAMILY[stim], "declared" if DECLARED_FAMILY[stim] is not None else "declared_family_offset_by_C3"
    return stim, 0, "own"


def family_name(stim):
    """The cohort-prefixed family name the tables carry (as build_public.py: 'fau:<code>'), e.g. 'sparrkulee:audiobook_1'."""
    return f"{COHORT}:{family_of(stim)[0]}"


def presentation_key(stim, noise_condition, snr, noise_file):
    snr_s = "none" if snr is None else f"{snr:g}"
    return f"{COHORT}:{stim}|{noise_condition or 'none'}|snr={snr_s}|noise={noise_file or 'none'}"


def _role(block_role, stim, restricted):
    if restricted:
        return "restricted"
    if stim == ARTEFACT_STIM:
        return "control_artefact"
    if family_of(stim)[0] == AB1 and block_role in ("dev", "bridge_cal"):
        return "holdout_seen_content"
    return block_role


def _mode(values):
    c = collections.Counter(values)
    top = max(c.values())
    return min(v for v, n in c.items() if n == top)


def _check(cond, msg):
    if not cond:
        raise AssertionError(f"C1 expectation failed: {msg}")


def stage_c1(src, out, *, expect=EXPECT_REAL, hash_eeg=True, log=_log, _auth=None):
    """C1: the SparrKULee run table (module docstring). Writes <out>/sparrkulee/runs_table.json and returns it. `out` has no
    default; the §6.2 cache root is accepted only from main() (check_out)."""
    src = os.path.abspath(src)
    _, production = check_out(out, src, _auth)
    if production and (not hash_eeg or expect is not EXPECT_REAL):
        raise OutputLocationError("under the cache root C1 always hashes the EEG files and asserts the real-data expectations")
    parts, sha_parts = _participants_tsv(src)
    desc_restricted, sha_desc = _description_restricted(src)
    tsv_restricted = sorted(s for s, p in parts.items() if p["exclusion_note"])
    restricted = set(RESTRICTED) | set(tsv_restricted) | set(desc_restricted)       # before any per-run file is touched
    sources = {"constant": list(RESTRICTED), "participants_tsv": tsv_restricted, "dataset_description": desc_restricted}
    _c1_expect_restricted(sorted(restricted), sources, expect)
    flagged, sha_readme = _readme_flagged(src)
    meta, raw_of = _save_metadata(src)
    envs, ignored = _envelopes(src)
    root_eeg = os.path.join(src, "derivatives", "preprocessed_eeg")
    files = sorted(glob.glob(os.path.join(root_eeg, "sub-*", "ses-*", "*_eeg.npy")))
    runs, ses_of = [], collections.defaultdict(set)
    for path in files:
        m = EEG_RE.match(os.path.basename(path))
        if not m:
            raise ValueError(f"unparsed EEG file name {os.path.basename(path)}")
        sub, ses, task, run, stim = m.group("sub", "ses", "task", "run", "stim")
        if os.path.basename(os.path.dirname(path)) != f"ses-{ses}" or os.path.basename(os.path.dirname(os.path.dirname(path))) != f"sub-{sub}":
            raise ValueError(f"{os.path.basename(path)} is not in sub-{sub}/ses-{ses}/")
        if task != TASK:
            raise ValueError(f"{os.path.basename(path)}: task {task!r}, {TASK!r} expected")
        if ses not in SESSION_ROLE:
            raise ValueError(f"{os.path.basename(path)}: session {ses!r} has no role in §3.2")
        if stim not in envs:
            raise ValueError(f"{os.path.basename(path)}: no envelope {stim}_envelope.npy")
        is_r = sub in restricted
        h = _read_npy_header(path)                          # header only, restricted participants included (§2.1, §3.2)
        if h["object"] or not h["consistent"] or h["dtype"] != "<f8" or len(h["shape"]) != 2 or h["shape"][0] != N_CH:
            raise ValueError(f"{os.path.basename(path)}: unexpected EEG array {h}")
        tail, t_env = h["shape"][1] - envs[stim]["T_env"], envs[stim]["T_env"]
        if not 0 <= tail <= min(RATE_TAIL_MAX, RATE_TAIL_FRAC * t_env):
            raise ValueError(f"{os.path.basename(path)}: T_eeg {h['shape'][1]} against T_env {t_env} of {stim}: not EEG and envelope "
                             f"at the same {C.FS} Hz (C1 rule 0 <= T_eeg - T_env <= min({RATE_TAIL_MAX}, {RATE_TAIL_FRAC} T_env))")
        ses_of[sub].add(ses)
        rel_out = _rel(path, root_eeg)
        r = {"run_id": f"sub-{sub}_ses-{ses}_run-{run}", "sub": sub, "ses": ses, "task": task, "run": run, "stimulus": stim,
             "file": _rel(path, src), "restricted": is_r, "block_role": SESSION_ROLE[ses], "T_eeg": h["shape"][1],
             "T_env": t_env, "T_tail": tail,
             "npy_header": {k: h[k] for k in ("dtype", "fortran_order", "version", "header_bytes", "bytes_read")},
             "save_metadata_raw": raw_of.get(rel_out, []), "sha256": {"eeg": None, "events": None}, "events": None,
             "noise_condition": None, "snr": None, "noise_file": None, "raw_bdf_present": None}
        _, off, basis = family_of(stim)
        r.update(family_name=family_name(stim), family_offset_declared=off, family_basis=basis)
        if not r["save_metadata_raw"]:
            raise ValueError(f"{os.path.basename(path)} is not listed in .save_metadata.json")
        if not is_r:                                        # restricted: file name and header only
            stem = f"sub-{sub}_ses-{ses}_task-{task}_run-{run}"
            ev_path = os.path.join(src, f"sub-{sub}", f"ses-{ses}", "eeg", f"{stem}_events.tsv")
            ev = _events(ev_path)
            st = os.path.basename(ev.get("stim_file", "")).replace(".npz.gz", "")
            if st != stim:
                raise ValueError(f"{stem}: events stim_file {ev.get('stim_file')!r} does not name {stim}")
            r["events"] = {k: _na(ev.get(k)) for k in ("onset", "duration", "stim_file", "trigger_file", "noise_file", "video_file",
                                                       "condition", "snr")}
            r["noise_condition"], r["snr"] = _na(ev.get("condition")), _snr(ev.get("snr"))
            r["noise_file"] = _file_na(ev.get("noise_file"))
            r["sha256"]["events"] = _sha256_file(ev_path)
            r["raw_bdf_present"] = os.path.exists(os.path.join(src, f"sub-{sub}", f"ses-{ses}", "eeg", f"{stem}_eeg.bdf.gz"))
            if hash_eeg:
                r["sha256"]["eeg"] = _sha256_file(path)
        r["presentation_key"] = None if is_r else presentation_key(stim, r["noise_condition"], r["snr"], r["noise_file"])
        r["role"] = _role(r["block_role"], stim, is_r)
        runs.append(r)
    multi = {s: sorted(v) for s, v in ses_of.items() if len(v) > 1}
    if multi:
        raise ValueError(f"participants in several session blocks (no role rule): {multi}")
    # structural-anomaly rule (§3.2): T_eeg against the modal T_eeg of the other non-restricted listeners of the presentation
    by_key = collections.defaultdict(list)
    for r in runs:
        if not r["restricted"]:
            by_key[r["presentation_key"]].append(r)
    for r in runs:
        r["flags"] = ["restricted_participant"] if r["restricted"] else []
        if r["restricted"]:
            r["structural"] = {"n_colisteners": None, "T_eeg_mode": None, "delta": None, "anomalous": False}
            continue
        co = [q["T_eeg"] for q in by_key[r["presentation_key"]] if q["sub"] != r["sub"]]
        mode = _mode(co) if co else None
        delta = None if mode is None else r["T_eeg"] - mode
        anom = delta is not None and abs(delta) > STRUCT_TOL
        r["structural"] = {"n_colisteners": len(co), "T_eeg_mode": mode, "delta": delta, "anomalous": anom}
        if anom:
            r["flags"].append("structural_anomaly")
    present = {(r["sub"], r["ses"], r["run"]) for r in runs}
    flagged_present = sorted(set(flagged) & present)
    _check(not flagged_present, f"README-flagged runs present: {flagged_present}")
    # role disjointness by content family (P2): fit, dev and bridge_cal never share a declared family
    fam_role = collections.defaultdict(set)
    for r in runs:
        if r["role"] in DONOR_ROLES:
            fam_role[r["family_name"]].add(r["role"])
    shared = {f: sorted(v) for f, v in fam_role.items() if len(v) > 1}
    _check(not shared, f"content families shared across donor roles: {shared}")
    participants = []
    for s in sorted(ses_of):
        (ses,) = ses_of[s]
        participants.append({"sub": s, "session": ses, "block_role": SESSION_ROLE[ses], "restricted": s in restricted,
                             "exclusion_note": parts.get(s, {}).get("exclusion_note"), "in_participants_tsv": s in parts,
                             "n_runs": sum(r["sub"] == s for r in runs)})
    table = {"schema": SCHEMA_TABLE, "contract": C.CONTRACT, "cohort": COHORT, "src": src, "builder_sha256": _code_sha(),
             "hash_eeg": bool(hash_eeg), "restricted": sorted(restricted), "restricted_sources": sources,
             "readme_flagged": [list(f) for f in flagged], "readme_flagged_absent": True, "save_metadata": meta,
             "sources_sha256": {"participants.tsv": sha_parts, "dataset_description.json": sha_desc, "README.md": sha_readme,
                                "derivatives/preprocessed_eeg/.save_metadata.json": meta["sha256"]},
             "participants": participants, "envelopes": [envs[k] for k in sorted(envs)], "ignored_stimulus_files": ignored,
             "runs": runs,
             "rules": {"session_role": SESSION_ROLE, "holdout": "audiobook_1-family runs of dev / bridge_cal participants",
                       "control_artefact": ARTEFACT_STIM, "structural_tolerance_samples": STRUCT_TOL,
                       "declared_family": DECLARED_FAMILY,
                       "rate_check": {"rule": f"0 <= T_eeg - T_env <= min({RATE_TAIL_MAX}, {RATE_TAIL_FRAC} T_env)",
                                      "tail_max": RATE_TAIL_MAX, "tail_frac": RATE_TAIL_FRAC}},
             "counts": _c1_counts(runs, participants, envs, restricted)}
    _c1_expect(table, expect)
    d = _cohort_dir(out)
    _write_json(os.path.join(d, RUNS_TABLE), table)
    c = table["counts"]
    log(f"C1: {c['n_runs']} runs ({c['n_restricted_runs']} restricted), {c['n_participants']} participants, {c['n_envelopes']} "
        f"envelopes; roles {c['runs_by_role']}; structural anomalies {c['structural_anomalies']}; -> {os.path.join(d, RUNS_TABLE)}")
    return table


def _c1_counts(runs, participants, envs, restricted):
    by_role = collections.Counter(r["role"] for r in runs)
    hours = collections.defaultdict(float)
    for r in runs:
        hours[r["role"]] += r["T_eeg"] / C.FS / 3600
    cov = {}
    for role in DONOR_ROLES:                                # before C2, the overlap scan and the shared-audio mask (C6 recomputes)
        rr = [r for r in runs if r["role"] == role]
        starts = {r["run_id"]: C.segment_starts(r["T_env"], r["T_eeg"], COHORT) for r in rr}
        n = collections.Counter((r["presentation_key"], int(s)) for r in rr for s in starts[r["run_id"]])
        elig = {k for k, v in n.items() if v >= 2}
        cov[role] = {"participants": len({r["sub"] for r in rr}), "runs": len(rr), "presentations": len({r["presentation_key"] for r in rr}),
                     "presentations_ge2": len({k[0] for k in elig}),
                     "listener_segments": sum((r["presentation_key"], int(s)) in elig for r in rr for s in starts[r["run_id"]]),
                     "content_segments": len(elig)}
    return {"n_runs": len(runs), "n_participants": len(participants), "n_restricted_participants": sum(p["restricted"] for p in participants),
            "n_restricted_runs": sum(r["restricted"] for r in runs), "n_envelopes": len(envs), "runs_by_role": dict(sorted(by_role.items())),
            "hours_by_role": {k: round(v, 4) for k, v in sorted(hours.items())},
            "structural_anomalies": sorted(r["run_id"] for r in runs if r["structural"]["anomalous"]),
            "artefact_runs": sorted(r["run_id"] for r in runs if r["stimulus"] == ARTEFACT_STIM),
            "T_tail_range": [min(r["T_tail"] for r in runs), max(r["T_tail"] for r in runs)] if runs else None,
            "coverage_before_audit": cov, "restricted": sorted(restricted)}


def _c1_expect_restricted(union, sources, expect):
    """The restricted-set expectation, checked before the run loop: the union and each source (constant, participants.tsv,
    dataset_description.json Notes) must equal the expected set."""
    if not expect or "restricted" not in expect:
        return
    want = sorted(expect["restricted"])
    for name, got in (("table", union), *sources.items()):
        _check(sorted(got) == want, f"restricted participants from {name}: {sorted(got)} != {want}")


def _c1_expect(t, expect):
    if not expect:
        return
    c = t["counts"]
    for k in ("n_runs", "n_participants", "n_restricted_runs", "n_envelopes"):
        if k in expect:
            _check(c[k] == expect[k], f"{k} = {c[k]}, expected {expect[k]}")
    _c1_expect_restricted(t["restricted"], t["restricted_sources"], expect)
    if "readme_flagged" in expect:
        got = sorted(tuple(f) for f in t["readme_flagged"])
        _check(got == sorted(tuple(f) for f in expect["readme_flagged"]), f"README-flagged runs {got}")
    if "ignored_stimulus_files" in expect:
        _check(sorted(t["ignored_stimulus_files"]) == sorted(expect["ignored_stimulus_files"]), f"ignored files {t['ignored_stimulus_files']}")
    if "save_metadata_entries" in expect:
        _check(t["save_metadata"]["n_entries"] == expect["save_metadata_entries"], f"metadata entries {t['save_metadata']['n_entries']}")
    if "outputs_listed_twice" in expect:
        n = len(t["save_metadata"]["outputs_listed_twice"])
        _check(n == expect["outputs_listed_twice"], f"{n} outputs listed twice in .save_metadata.json")
    if "artefact_runs" in expect:
        got = sorted((r["sub"], r["ses"], r["run"]) for r in t["runs"] if r["stimulus"] == ARTEFACT_STIM)
        _check(got == sorted(tuple(a) for a in expect["artefact_runs"]), f"artefact runs {got}")


# ---------------------------------------------------------------------------------------------------------- C2 audit
def _dec_sos():
    return signal.butter(DEC_ORDER, DEC_BAND, btype="band", fs=C.FS, output="sos")


def _zrows(y):
    mu, sd = y.mean(-1, keepdims=True), y.std(-1, keepdims=True)
    sd = np.where(sd > 0, sd, 1.0)
    return (y - mu) / sd


def _dec_eeg(x):
    return _zrows(signal.sosfiltfilt(_dec_sos(), np.ascontiguousarray(x, dtype=np.float64), axis=-1))


def _dec_env(e):
    return _zrows(signal.sosfiltfilt(_dec_sos(), np.asarray(e, dtype=np.float64)))


def _gram(xz, e, n):
    """G = X^T X and c = X^T e of the lagged design X[t, j * 64 + ch] = xz[ch, t + L_j], t in [0, n) (lag-major columns)."""
    nc, nl = xz.shape[0], len(DEC_LAGS)
    p = nc * nl
    G, c = np.empty((p, p)), np.empty(p)
    for j, lj in enumerate(DEC_LAGS):
        xj = xz[:, lj:lj + n]
        c[j * nc:(j + 1) * nc] = xj @ e[:n]
        for k in range(j, nl):
            blk = xj @ xz[:, DEC_LAGS[k]:DEC_LAGS[k] + n].T
            G[j * nc:(j + 1) * nc, k * nc:(k + 1) * nc] = blk
            G[k * nc:(k + 1) * nc, j * nc:(j + 1) * nc] = blk.T
    return G, c


def _reconstruct(xz, w, n):
    nc = xz.shape[0]
    rec = np.zeros(n)
    for j, lj in enumerate(DEC_LAGS):
        rec += w[j * nc:(j + 1) * nc] @ xz[:, lj:lj + n]
    return rec


def lagged_pearson(a, b, lo, hi, search=SEARCH):
    """r[k] = Pearson(a[t], b[t + tau]) for tau = k - search, over t in [lo, hi) with 0 <= t + tau < len(b) (exact; FFT cross
    term and cumulative sums). Returns (taus, r, n_overlap)."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    Tv = len(b)
    taus = np.arange(-search, search + 1)
    ah = np.zeros(hi)
    ah[lo:hi] = a[lo:hi]
    nfft = sfft.next_fast_len(max(hi, Tv) + search + 1, real=True)
    cc = sfft.irfft(sfft.rfft(b, nfft) * np.conj(sfft.rfft(ah, nfft)), nfft)
    sab = cc[taus % nfft]
    t0, t1 = np.maximum(lo, -taus), np.minimum(hi, Tv - taus)
    N = t1 - t0
    ok = N >= 2
    t0, t1 = np.where(ok, t0, lo), np.where(ok, t1, lo)
    ca1, ca2 = np.r_[0.0, np.cumsum(a[:hi])], np.r_[0.0, np.cumsum(a[:hi] ** 2)]
    cb1, cb2 = np.r_[0.0, np.cumsum(b)], np.r_[0.0, np.cumsum(b ** 2)]
    sa, saa = ca1[t1] - ca1[t0], ca2[t1] - ca2[t0]
    sb, sbb = cb1[t1 + taus * ok] - cb1[t0 + taus * ok], cb2[t1 + taus * ok] - cb2[t0 + taus * ok]
    Nf = np.maximum(N, 1).astype(np.float64)
    cov, va, vb = sab - sa * sb / Nf, saa - sa ** 2 / Nf, sbb - sb ** 2 / Nf
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(ok & (va > 0) & (vb > 0), cov / np.sqrt(np.maximum(va * vb, 1e-300)), np.nan)
    return taus, r, N


def peak_and_z(taus, r):
    """tau_hat = argmax r; z = (r(tau_hat) - mean) / SD over |tau - tau_hat| > 1 s (population SD)."""
    if not np.isfinite(r).any():
        return None, None, None
    k = int(np.nanargmax(r))
    bg = np.abs(taus - taus[k]) > BG_EXCL
    v = r[bg & np.isfinite(r)]
    sd = float(v.std()) if len(v) > 1 else 0.0
    z = (float(r[k]) - float(v.mean())) / sd if sd > 0 else None
    return int(taus[k]), float(r[k]), z


def classify(tau, z):
    """§3.2 clock-validity classes from the per-half lags and prominences."""
    meas = [zh is not None and zh >= Z_MEAS for zh in z]
    if all(meas) and all(abs(t) <= TAU_TOL for t in tau):
        return "aligned", None
    if all(meas) and abs(tau[0] - tau[1]) <= TAU_TOL and abs((tau[0] + tau[1]) / 2) > TAU_TOL:
        return "misaligned", None
    if not all(meas):
        return "unverifiable", "half not measurable (z < 5): " + ", ".join(str(i + 1) for i, m in enumerate(meas) if not m)
    return "unverifiable", "lags differ between halves" if abs(tau[0] - tau[1]) > TAU_TOL else "lag within tolerance in one half only"


def audit_run(xz_t, e, refs_gc, T_env):
    """Decoder from the references' (G, c), reconstruction of the run, the two halves' lag scans and the class. Returns the
    computed AUDIT_KEYS fields; z is returned as computed (the class is decided on exactly the values that are stored)."""
    G = sum(g for g, _ in refs_gc)
    c = sum(cv for _, cv in refs_gc)
    p = G.shape[0]
    w = np.linalg.solve(G + DEC_RIDGE * np.trace(G) / p * np.eye(p), c)
    n = min(T_env, xz_t.shape[1] - DEC_LAGS[-1])
    h = n // 2
    if h - SEARCH < MIN_OVERLAP:
        return {"tau": [None, None], "z": [None, None], "r_peak": [None, None], "r_at_0": [None, None], "halves": [[0, h], [h, n]],
                "class": "unverifiable", "reason": f"run too short for the +-{SEARCH // C.FS} s search (half {h} samples)",
                "diagnostic": None}
    rec = _reconstruct(xz_t, w, n)
    tau, z, rp, r0 = [], [], [], []
    for lo, hi in ((0, h), (h, n)):
        taus, r, _ = lagged_pearson(rec, e, lo, hi)
        t_, p_, z_ = peak_and_z(taus, r)
        tau.append(t_); rp.append(p_); z.append(None if z_ is None else float(z_))
        r0.append(float(r[SEARCH]) if np.isfinite(r[SEARCH]) else None)
    diag = _diagnostic(rec, e, n, h)
    out = {"tau": tau, "z": z, "r_peak": [_rnd(v) for v in rp], "r_at_0": [_rnd(v) for v in r0], "halves": [[0, h], [h, n]],
           "diagnostic": diag}
    if any(t is None for t in tau):
        return {**out, "class": "unverifiable", "reason": "no finite correlation"}
    cls, why = classify(tau, z)
    return {**out, "class": cls, "reason": why}


def _rnd(v):
    return None if v is None or not np.isfinite(v) else round(float(v), 6)


DIAG_SEARCH = 10 * C.FS                                  # the scout's window (decoder_lag.py, decoder_lag_halves.py)


def _diagnostic(rec, e, n, h):
    """Descriptive only, never used by the §3.2 classes: the scout's +-10 s statistics on the same reconstruction (full run:
    tau, r_peak, r_at_0, max |r| over |tau| > 1 s, as decoder_lag.json; per half: tau, r and the same prominence z)."""
    taus, rf, _ = lagged_pearson(rec, e, 0, n, search=DIAG_SEARCH)
    t_, p_, z_ = peak_and_z(taus, rf)
    off = (np.abs(taus) > BG_EXCL) & np.isfinite(rf)
    out = {"note": "descriptive only (the scout's +-10 s window); the class uses the +-40 s rule", "search_samples": DIAG_SEARCH,
           "full": {"tau": t_, "r": _rnd(p_), "z": _rnd(z_), "r_at_0": _rnd(rf[DIAG_SEARCH]),
                    "offpeak_absmax": _rnd(np.abs(rf[off]).max()) if off.any() else None}, "halves": []}
    for lo, hi in ((0, h), (h, n)):
        taus, r, _ = lagged_pearson(rec, e, lo, hi, search=DIAG_SEARCH)
        t_, p_, z_ = peak_and_z(taus, r)
        out["halves"].append({"tau": t_, "r": _rnd(p_), "z": _rnd(z_)})
    return out


def _refs_for(run, pool):
    return [q for q in pool if q["sub"] != run["sub"]][:MAX_REFS]


def _audit_pool(table, stim):
    """Eligible references of a stimulus: non-restricted, not structurally anomalous, sorted by (sub, ses, run)."""
    return sorted((q for q in table["runs"] if q["stimulus"] == stim and not q["restricted"] and not q["structural"]["anomalous"]),
                  key=lambda q: (q["sub"], q["ses"], q["run"]))


def _audit_record(r, table_sha, code_sha, **fields):
    """One align_audit.jsonl record in the uniform schema AUDIT_KEYS: every key present, None where a class computes nothing."""
    unknown = sorted(set(fields) - set(AUDIT_KEYS))
    if unknown:
        raise KeyError(f"audit record fields outside AUDIT_KEYS: {unknown}")
    rec = {"run": r["run_id"], "sub": r["sub"], "ses": r["ses"], "stimulus": r["stimulus"], "refs": [], "n_refs": 0,
           "tau": [None, None], "z": [None, None], "r_peak": [None, None], "r_at_0": [None, None], "halves": None, "class": None,
           "reason": None, "diagnostic": None,
           "structural_anomaly": None if r["restricted"] else bool(r["structural"]["anomalous"]),
           "runs_table_sha256": table_sha, "builder_sha256": code_sha, "sha256": {}}
    rec.update(fields)
    if rec["class"] not in CLASSES:
        raise ValueError(f"{r['run_id']}: audit class {rec['class']!r}")
    return rec


def _not_audited(r, table_sha, code_sha):
    return _audit_record(r, table_sha, code_sha, reason="restricted participant: arrays never opened", **{"class": "not_audited"})


def _audit_meta(table, records):
    by = collections.Counter(r["class"] for r in records)
    return {"schema": SCHEMA_AUDIT, "contract": C.CONTRACT, "builder_sha256": _code_sha(), "n_runs": len(records),
            "classes": dict(sorted(by.items())),
            "misaligned": [{k: r[k] for k in ("run", "tau", "z")} for r in records if r["class"] == "misaligned"],
            "rule": {"band_hz": list(DEC_BAND), "order": DEC_ORDER, "lags": list(DEC_LAGS), "ridge": DEC_RIDGE, "max_refs": MAX_REFS,
                     "min_refs": MIN_REFS, "search_samples": SEARCH, "background_exclusion_samples": BG_EXCL, "z_measurable": Z_MEAS,
                     "tau_tolerance": TAU_TOL, "sign": "tau > 0: EEG sample t pairs with envelope sample t + tau",
                     "references": "same stimulus file, non-restricted, not structurally anomalous, other participant, first 8 by (sub, ses, run)"}}


def _table_and_src(out, src, _auth):
    """The C1 table under <out> (output location checked against src first, then against the table's dataset tree)."""
    _, production = check_out(out, src, _auth)
    d = _cohort_dir(out, create=False)
    path = os.path.join(d, RUNS_TABLE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path}: run C1 first")
    table = _read_json(path)
    if table.get("schema") != SCHEMA_TABLE:
        raise ValueError(f"{path}: schema {table.get('schema')!r}")
    if src is not None and os.path.abspath(src) != table["src"]:
        raise ValueError(f"--src {src} differs from the C1 table's {table['src']}")
    check_out(out, table["src"], _auth)
    return d, table, _sha256_file(path), production


def _marker(path, table_sha, code_sha):
    """A C2 done marker, or None when it is missing or was written for another run table or builder version (then recomputed)."""
    if not os.path.exists(path):
        return None
    m = _read_json(path)
    ok = m.get("runs_table_sha256") == table_sha and m.get("builder_sha256") == code_sha and set(m) == set(AUDIT_KEYS)
    return m if ok else None


def stage_c2(src, out, *, runs=None, log=_log, _auth=None):
    """C2: the clock-validity audit (module docstring). `runs` limits the audited run ids (a dry run, refused under the cache
    root); align_audit.jsonl is written once every run of the table has a record. `out` has no default; the §6.2 cache root is
    accepted only from main() (check_out). Returns the records of this call."""
    _, production = check_out(out, src, _auth)
    if production and runs is not None:
        raise OutputLocationError("a partial audit (runs) is refused under the cache root; use a scratch out")
    d, table, table_sha, _ = _table_and_src(out, src, _auth)
    src = table["src"]
    code_sha = _code_sha()
    restricted = restricted_set(table)
    byid = {r["run_id"]: r for r in table["runs"]}
    if runs is None:
        targets = [r for r in table["runs"] if not r["restricted"]]
    else:
        unknown = sorted(set(runs) - set(byid))
        if unknown:
            raise KeyError(f"unknown run ids {unknown}")
        targets = [byid[i] for i in runs]
    for r in targets:
        if r["restricted"] or r["sub"] in restricted:
            raise RestrictedAccess(f"{r['run_id']}: restricted participant, never audited")
    done = os.path.join(d, C2_DONE)
    os.makedirs(done, exist_ok=True)
    envs = {e["stimulus"]: e for e in table["envelopes"]}
    out_recs = []
    by_stim = collections.defaultdict(list)
    for r in targets:
        by_stim[r["stimulus"]].append(r)
    for stim in sorted(by_stim):
        have = {r["run_id"]: _marker(os.path.join(done, f"{r['run_id']}.json"), table_sha, code_sha) for r in by_stim[stim]}
        todo = [r for r in by_stim[stim] if have[r["run_id"]] is None]
        out_recs += [m for m in have.values() if m is not None]
        if not todo:
            continue
        pool = _audit_pool(table, stim)
        for q in pool:                                     # explicit (not assert: python -O must not remove it)
            if q["restricted"] or q["sub"] in restricted:
                raise RestrictedAccess(f"{q['run_id']}: a restricted participant in the reference pool of {stim}")
        plan = {r["run_id"]: _refs_for(r, pool) for r in todo}
        need = {q["run_id"] for refs in plan.values() if len(refs) >= MIN_REFS for q in refs}
        e = None
        if need:
            env_raw, _ = _load_array(os.path.join(src, envs[stim]["file"]), restricted, envs[stim]["sha256"])
            e = _dec_env(env_raw.reshape(-1))
        gc, xz_keep, shas, processed = {}, {}, {}, set()    # each needed file is read once per stimulus
        todo_ids = {r["run_id"] for r in todo}
        for r in todo:
            refs = plan[r["run_id"]]
            base = {"refs": [q["run_id"] for q in refs], "n_refs": len(refs)}
            if len(refs) < MIN_REFS:
                rec = _audit_record(r, table_sha, code_sha, **base, reason=f"fewer than {MIN_REFS} eligible co-listeners",
                                    **{"class": "unverifiable"})
            else:
                for q in refs:
                    if q["run_id"] not in gc:
                        x, shas[q["run_id"]] = _load_array(os.path.join(src, q["file"]), restricted, q["sha256"]["eeg"])
                        _check_eeg(x, q)
                        xz = _dec_eeg(x)
                        del x
                        gc[q["run_id"]] = _gram(xz, e, min(len(e), xz.shape[1] - DEC_LAGS[-1]))
                        if q["run_id"] in todo_ids and q["run_id"] not in processed:
                            xz_keep[q["run_id"]] = xz
                        del xz
                if r["run_id"] in xz_keep:
                    xz_t = xz_keep.pop(r["run_id"])
                else:
                    x, shas[r["run_id"]] = _load_array(os.path.join(src, r["file"]), restricted, r["sha256"]["eeg"])
                    _check_eeg(x, r)
                    xz_t = _dec_eeg(x)
                    del x
                rec = _audit_record(r, table_sha, code_sha, **base, **audit_run(xz_t, e, [gc[q["run_id"]] for q in refs], len(e)),
                                    sha256={k: shas[k] for k in [r["run_id"]] + base["refs"]})
                if r["run_id"] in need and r["run_id"] not in gc:  # a later run's reference: keep its (G, c), not its samples
                    gc[r["run_id"]] = _gram(xz_t, e, min(len(e), xz_t.shape[1] - DEC_LAGS[-1]))
                del xz_t
            processed.add(r["run_id"])
            _write_json(os.path.join(done, f"{r['run_id']}.json"), rec)
            out_recs.append(rec)
            log(f"C2 {r['run_id']} {stim}: {rec['class']} tau={rec['tau']} z={rec['z']} refs={rec['n_refs']}"
                + (f" ({rec['reason']})" if rec.get("reason") else ""))
    records = []
    missing = []
    for r in table["runs"]:
        m = None if r["restricted"] else _marker(os.path.join(done, f"{r['run_id']}.json"), table_sha, code_sha)
        if r["restricted"]:
            records.append(_not_audited(r, table_sha, code_sha))
        elif m is not None:
            records.append(m)
        else:
            missing.append(r["run_id"])
    if missing:
        log(f"C2: {len(missing)} runs not yet audited; {AUDIT} not written")
        return out_recs
    records.sort(key=lambda q: q["run"])
    tmp = os.path.join(d, f"{AUDIT}.tmp{os.getpid()}")
    with open(tmp, "w") as f:
        for q in records:
            f.write(_dumps(q) + "\n")
    os.replace(tmp, os.path.join(d, AUDIT))
    meta = _audit_meta(table, records)
    meta["runs_table_sha256"] = table_sha
    meta["align_audit_sha256"] = _sha256_file(os.path.join(d, AUDIT))
    _write_json(os.path.join(d, AUDIT_META), meta)
    log(f"C2: {len(records)} records, classes {meta['classes']}; misaligned {[m['run'] for m in meta['misaligned']]} -> {os.path.join(d, AUDIT)}")
    return out_recs


def _check_eeg(x, r):
    if x.dtype != np.float64 or x.shape != (N_CH, r["T_eeg"]):
        raise ValueError(f"{r['run_id']}: array {x.dtype} {x.shape}, float64 {(N_CH, r['T_eeg'])} expected")
    if not np.isfinite(x).all():
        raise ValueError(f"{r['run_id']}: {int((~np.isfinite(x)).sum())} non-finite samples in the source array")


def read_audit(out, table=None):
    """align_audit.jsonl as {run_id: record}, checked to cover every run of the table."""
    d = _cohort_dir(out, create=False)
    path = os.path.join(d, AUDIT)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path}: run C2 to completion first")
    with open(path) as f:
        recs = [json.loads(line) for line in f if line.strip()]
    off = sorted({q.get("run") for q in recs if set(q) != set(AUDIT_KEYS)}, key=str)
    if off:
        raise ValueError(f"{AUDIT}: {len(off)} records outside the schema AUDIT_KEYS (an older builder?), e.g. {off[:3]}: rerun C2")
    by = {q["run"]: q for q in recs}
    if table is not None:
        missing = sorted({r["run_id"] for r in table["runs"]} - set(by))
        if missing:
            raise ValueError(f"{AUDIT} lacks {len(missing)} runs of the table, e.g. {missing[:3]}")
        for r in table["runs"]:
            if r["restricted"] != (by[r["run_id"]]["class"] == "not_audited"):
                raise ValueError(f"{r['run_id']}: audit class {by[r['run_id']]['class']} for restricted={r['restricted']}")
    return by


# ---------------------------------------------------------------------------------------------------------- C4 caches
def final_role(r, audit):
    """Role and exclusion flags of a run after C2 (precedence restricted > excluded_rule > C1 role)."""
    if r["restricted"]:
        return "restricted", []
    cls = audit["class"]
    flags = []
    if cls == "misaligned":
        flags.append("clock_misaligned")
    if r["structural"]["anomalous"] and cls != "aligned":
        flags.append("structural_anomaly_unverified_clock")
    return ("excluded_rule" if flags else r["role"]), flags


def _layout(table, audit):
    runs = []
    for r in table["runs"]:
        role, flags = final_role(r, audit[r["run_id"]])
        runs.append(dict(r, role=role, role_c1=r["role"], flags=flags, slab=None if role == "restricted" else role))
    cached = sorted((r for r in runs if r["slab"] is not None), key=lambda r: (SLABS.index(r["slab"]), r["sub"], r["ses"], r["run"]))
    off, slabs = 0, {}
    for r in cached:
        r["row_offset"] = off
        a = slabs.setdefault(r["slab"], [off, off])
        off += r["T_eeg"]
        a[1] = off
    for r in runs:
        r.setdefault("row_offset", None)
    return runs, cached, off, slabs


def _participant_stats(filt, masks):
    """Per channel mean and population SD over the guarded spans of a participant's runs, masked (run, channel) cells out."""
    g0, g1 = C.GUARDS[COHORT]
    n, s1 = np.zeros(N_CH), np.zeros(N_CH)
    for rid, y in filt.items():
        seg = y[:, g0:max(g0, y.shape[1] - g1)]
        ok = ~masks[rid]
        n += ok * seg.shape[1]
        s1 += np.where(ok, seg.sum(1), 0.0)
    mu = np.where(n > 0, s1 / np.maximum(n, 1), 0.0)
    s2 = np.zeros(N_CH)
    for rid, y in filt.items():
        seg = y[:, g0:max(g0, y.shape[1] - g1)]
        ok = ~masks[rid]
        s2 += np.where(ok, ((seg - mu[:, None]) ** 2).sum(1), 0.0)
    sd = np.where(n > 0, np.sqrt(s2 / np.maximum(n, 1)), np.nan)
    return mu, sd, n


def process_participant(src, rr, restricted, mm=None):
    """C4 chain for one participant's runs (dicts with file, T_eeg, run_id, row_offset, sha256): returns (marker dict, {run_id:
    float16 [T, 64]} when mm is None). With a memmap, writes the rows and returns the marker only."""
    filt, masks, info = {}, {}, {}
    sos = C.eeg_sos()[0]
    for r in rr:
        x, sha = _load_array(os.path.join(src, r["file"]), restricted, r["sha256"]["eeg"])
        _check_eeg(x, r)
        y = C.band(x, sos)
        del x
        sd = y.std(1)
        med = float(np.median(sd))
        m = (sd > QC_HI * med) | (sd < QC_LO * med)
        car = float(np.abs(y.sum(0)).max() / med) if med > 0 else None
        filt[r["run_id"]], masks[r["run_id"]] = y, m
        info[r["run_id"]] = {"sha256": sha, "masked": [C.BIOSEMI64[c] for c in np.flatnonzero(m)],
                             "qc": {"median_sd": med, "ratio": {C.BIOSEMI64[c]: float(sd[c] / med) for c in np.flatnonzero(m)}},
                             "car_ratio": car, "car_ok": car is not None and car < CAR_TOL}
    mu, sd, n = _participant_stats(filt, masks)
    div = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    outs = {}
    for r in rr:
        z = (filt.pop(r["run_id"]) - mu[:, None]) / div[:, None]
        z[masks[r["run_id"]]] = 0.0
        z16 = np.ascontiguousarray(z.T).astype(np.float16)
        if not np.isfinite(z16).all():
            raise ValueError(f"{r['run_id']}: non-finite float16 values (|z| > 65504?)")
        info[r["run_id"]]["max_abs_z"] = float(np.abs(z).max())
        del z
        if mm is None:
            outs[r["run_id"]] = z16
        else:
            mm[r["row_offset"]:r["row_offset"] + r["T_eeg"]] = z16
    all_masked = [C.BIOSEMI64[c] for c in range(N_CH) if n[c] == 0]
    marker = {"sub": rr[0]["sub"], "mu": mu, "sd_prez": sd, "n_samples": n, "masked_all_runs": all_masked, "runs": info}
    return (marker, outs) if mm is None else marker


ENV_ORIGIN = ("authors' pipeline: derivatives/preprocessed_stimuli/<stim>_envelope.npy (T, 1) at 64 Hz; the extractor was neither "
              "run nor verified (*.data_dict never opened)")                                         # design §2.3 Sources
ENV_ORIGINAL_BAND = "broadband: +11 dB at 0.5 Hz, -4 dB at 8 Hz, relative to 3-7 Hz"


def _streams(src, table, restricted, fam_id):
    """env_f32.npy rows and streams.json entries (fixture schema, with the §2.3 provenance: origin, original band, source rate,
    filter shas, source sha256, NaN count). The envelopes are already at 64 Hz: no h_aa step, so filter_sha256 = {env_sos}."""
    rows, parts, off = [], [], 0
    sos, sos_sha = C.env_sos()
    for i, e in enumerate(table["envelopes"]):
        raw, sha = _load_array(os.path.join(src, e["file"]), restricted, e["sha256"])
        v = np.asarray(raw, dtype=np.float64).reshape(-1)
        n_nan = int((~np.isfinite(v)).sum())
        if len(v) != e["T_env"] or n_nan:
            raise ValueError(f"{e['file']}: {len(v)} samples ({n_nan} non-finite), {e['T_env']} finite expected")
        en, rms = C.rms_norm(C.band(v, sos), return_rms=True)
        _, foff, basis = family_of(e["stimulus"])
        fam = family_name(e["stimulus"])
        rows.append({"stream": i, "name": e["stimulus"], "kind": "attended", "offset": off, "length": len(en), "family": fam_id[fam],
                     "family_offset": foff, "family_name": fam, "family_basis": basis, "rms": rms, "origin": ENV_ORIGIN,
                     "original_band": ENV_ORIGINAL_BAND, "fs_source": C.FS, "T_source": len(v), "filter_sha256": {"env_sos": sos_sha},
                     "source_sha256": sha, "source_array_sha256": hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest(),
                     "nan_count": n_nan, "file": e["file"]})
        parts.append(en.astype(np.float32))
        off += len(en)
    return rows, (np.concatenate(parts) if parts else np.zeros(0, np.float32))


def stage_c4(src, out, *, log=_log, _stop_after=None, _auth=None):
    """C4: the SparrKULee caches (module docstring). Needs C1's runs_table.json and C2's complete align_audit.jsonl. `out` has no
    default; the §6.2 cache root is accepted only from main() (check_out)."""
    d, table, table_sha, _ = _table_and_src(out, src, _auth)
    src = table["src"]
    _unit_rule_module()                                    # fail before the cache build, not after it, if M2b's rule moved
    restricted = restricted_set(table)
    audit = read_audit(out, table)
    audit_sha = _sha256_file(os.path.join(d, AUDIT))
    meta_path = os.path.join(d, AUDIT_META)
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"{meta_path}: run C2 to completion first")
    meta = _read_json(meta_path)
    if meta.get("runs_table_sha256") != table_sha or meta.get("align_audit_sha256") != audit_sha:
        raise ValueError(f"{AUDIT} / {AUDIT_META} were not built from this {RUNS_TABLE}: rerun C2")
    runs, cached, N, slabs = _layout(table, audit)
    for r in cached:                                       # hard exclusion (explicit, not assert: python -O must not remove it)
        if r["restricted"] or r["sub"] in restricted:
            raise RestrictedAccess(f"{r['run_id']}: a restricted participant in the cache layout")
    layout = {"N": N, "n_ch": N_CH, "rows": [[r["run_id"], r["row_offset"], r["T_eeg"]] for r in cached],
              "runs_table_sha256": table_sha, "align_audit_sha256": audit_sha, "builder_sha256": _code_sha()}
    done = os.path.join(d, C4_DONE)
    os.makedirs(done, exist_ok=True)
    lay_path = os.path.join(done, "layout.json")
    if os.path.exists(lay_path):
        if _dumps(_read_json(lay_path)) != _dumps(layout):
            raise RuntimeError(f"{lay_path}: a partial C4 build with another layout or code version exists; move {C4_DONE}/ and "
                               f"{PARTIAL} away before rebuilding")
    else:
        _write_json(lay_path, layout)
    final, partial = os.path.join(d, CACHE), os.path.join(d, PARTIAL)
    subs = sorted({r["sub"] for r in cached})
    markers = {s: os.path.join(done, f"sub-{s}.json") for s in subs}
    have = {s: os.path.exists(p) for s, p in markers.items()}
    if os.path.exists(final) and not os.path.exists(partial):     # the cache is complete: only the tables are (re)written
        if not all(have.values()):
            raise RuntimeError(f"{final} exists but {sum(not v for v in have.values())} participant markers are missing")
        mm = np.load(final, mmap_mode="r")
        if mm.shape != (N, N_CH) or mm.dtype != np.float16:
            raise RuntimeError(f"{final}: {mm.dtype} {mm.shape}, float16 {(N, N_CH)} expected")
        del mm
    else:
        if os.path.exists(partial):
            mm = np.lib.format.open_memmap(partial, mode="r+")
            if mm.shape != (N, N_CH) or mm.dtype != np.float16:
                raise RuntimeError(f"{partial}: {mm.dtype} {mm.shape}, float16 {(N, N_CH)} expected")
        else:
            if any(have.values()):
                raise RuntimeError(f"participant markers exist under {done} but {PARTIAL} does not: move {C4_DONE}/ away")
            mm = np.lib.format.open_memmap(partial, mode="w+", dtype=np.float16, shape=(N, N_CH))
        n_done = 0
        for s in subs:
            if os.path.exists(markers[s]):
                continue
            rr = sorted((r for r in cached if r["sub"] == s), key=lambda r: (r["ses"], r["run"]))
            marker = process_participant(src, rr, restricted, mm)
            mm.flush()
            _write_json(markers[s], marker)
            log(f"C4 sub-{s}: {len(rr)} runs, masked {sum(len(v['masked']) for v in marker['runs'].values())} cells")
            n_done += 1
            if _stop_after is not None and n_done >= _stop_after:
                del mm
                raise _Interrupted(f"stopped after {n_done} participants (test hook)")
        bad = 0
        for a in range(0, N, 1 << 20):                     # full NaN / Inf scan of the float16 cache
            bad += int((~np.isfinite(mm[a:a + (1 << 20)])).sum())
        if bad:
            raise ValueError(f"{partial}: {bad} non-finite values")
        mm.flush()
        del mm
        os.replace(partial, final)
    marks = {s: _read_json(markers[s]) for s in subs}
    fams = sorted({family_name(e["stimulus"]) for e in table["envelopes"]})
    fam_id = {f: i for i, f in enumerate(fams)}
    rows, env = _streams(src, table, restricted, fam_id)
    stream_of = {q["name"]: q["stream"] for q in rows}
    pkeys = sorted({r["presentation_key"] for r in cached})
    pres_id = {k: i for i, k in enumerate(pkeys)}
    presentations = []
    for k in pkeys:
        r0 = next(r for r in cached if r["presentation_key"] == k)
        _, foff, basis = family_of(r0["stimulus"])
        fam = family_name(r0["stimulus"])
        presentations.append({"id": pres_id[k], "key": k, "cohort": COHORT, "stimulus": r0["stimulus"], "family": fam_id[fam],
                              "family_name": fam, "family_offset": foff, "offset_known": foff is not None, "family_basis": basis,
                              "kind": "ss", "condition": TASK, "noise_condition": r0["noise_condition"], "snr": r0["snr"],
                              "noise_file": r0["noise_file"], "attended_side": None, "stream": stream_of[r0["stimulus"]],
                              "ignored_stream": None, "ignored_lead": 0, "onset_s": None,
                              "n_listeners": len({q["sub"] for q in cached if q["presentation_key"] == k})})
    families = [{"id": fam_id[f], "cohort": COHORT, "name": f, "clock": "known", "basis": "declared" if f == f"{COHORT}:{AB1}" else "own",
                 "members": [p["id"] for p in presentations if p["family_name"] == f]} for f in fams]
    out_runs = [_run_record(r, audit[r["run_id"]], marks.get(r["sub"]), pres_id, fam_id, stream_of) for r in runs]
    unit = cohort_unit({s: marks[s]["sd_prez"] for s in subs})
    fac = unit["factor_to_uV"] if unit["supported"] else None
    participants = [_participant_record(s, table, marks[s], fac) for s in subs]
    masked_cells = sum(len(r["masked"]) for r in out_runs if r["row_offset"] is not None)
    keys_of = collections.defaultdict(set)
    for r in cached:
        keys_of[r["stimulus"]].add(r["presentation_key"])
    car = [r["car_ratio"] for r in out_runs if r.get("car_ratio") is not None]
    res = {"schema": SCHEMA_RUNS, "contract": C.CONTRACT, "cohort": COHORT, "id_space": "cohort_local_provisional", "src": src,
           "builder_sha256": _code_sha(), "inputs": {"runs_table_sha256": table_sha, "align_audit_sha256": audit_sha},
           "participants": participants, "runs": out_runs, "presentations": presentations, "families": families,
           "cohort_info": {"dir": COHORT, "fs_native": C.FS, "n_ch": N_CH, "layout": list(C.BIOSEMI64), "reference": "CAR-64 (authors)",
                           "band": "authors' pipeline, then 1-20 Hz (ours)", "guards": list(C.GUARDS[COHORT]), "s_first": C.S_FIRST[COHORT],
                           "n_rows": N, "caches": {"A": CACHE}, "table": RUNS, "items": "runs", "env": ENV, "streams": STREAMS,
                           "role_slabs": slabs, "masked_cells": masked_cells, "filters": {"eeg_sos": C.eeg_sos()[1], "env_sos": C.env_sos()[1]},
                           "unit": {"name": "uV" if fac else None, "source_unit": unit.get("source_unit"), "factor_to_uV": fac,
                                    "basis": unit.get("basis") or unit.get("reason")}},
           "unit": unit,
           "unit_evidence": {"signal": "A: 1-20 Hz, before the z-score", "median_prez_sd": unit["magnitude"].get("median"),
                             "n_values": unit["magnitude"].get("n"),
                             "note": "median over participants x unmasked channels of the 1-20 Hz pre-z SD, in the source arrays' unit"},
           "sanity": {"nonfinite_cache_values": 0, "car_ratio_max": max(car) if car else None,
                      "car_not_ok": sorted(r["run_id"] for r in out_runs if r.get("car_ok") is False),
                      "restricted_rows": 0, "restricted_runs": sorted(r["run_id"] for r in out_runs if r["role"] == "restricted"),
                      "stimuli_with_several_presentations": {k: sorted(v) for k, v in sorted(keys_of.items()) if len(v) > 1}},
           "qc_rule": {"hi": QC_HI, "lo": QC_LO, "on": "SD over the whole run after 1-20 Hz vs the run's median channel SD"}}
    _save_npy(os.path.join(d, ENV), env)
    _write_json(os.path.join(d, STREAMS), {"schema": SCHEMA_STREAMS, "cohort": COHORT, "id_space": "cohort_local_provisional",
                                           "streams": rows})
    _write_json(os.path.join(d, RUNS), res)
    log(f"C4: {N} rows x {N_CH} ch float16 ({N * N_CH * 2 / 1e9:.2f} GB), slabs {slabs}, {masked_cells} masked cells, "
        f"{len(rows)} streams ({len(env)} samples) -> {d}")
    return res


class _Interrupted(RuntimeError):
    pass


def _run_record(r, audit, mark, pres_id, fam_id, stream_of):
    """One runs.json entry in the fixture schema (fixtures._piece plus the SparrKULee fields)."""
    cached = r["row_offset"] is not None
    _, foff, _ = family_of(r["stimulus"])
    fam = family_name(r["stimulus"])
    info = mark["runs"][r["run_id"]] if cached else {}
    trial = f"ses-{r['ses']}_run-{r['run']}"
    if r["restricted"]:
        aud = {"clock": "not_audited", "reason": "restricted participant"}
    else:
        aud = {"clock": audit["class"], "tau_hat": audit["tau"], "z": audit["z"], "refs": audit["refs"], "reason": audit.get("reason")}
    rec = {"piece_id": f"{COHORT}:{r['sub']}:{trial}", "participant": r["sub"], "uid": f"{COHORT}:{r['sub']}", "group": COHORT,
           "fold": -1, "dev": False, "test_only": False, "trial": trial, "kind": "ss", "stimulus": r["stimulus"],
           "ignored_stimulus": None, "content_group": None,
           "presentation": pres_id.get(r["presentation_key"]) if cached else None, "presentation_key": r["presentation_key"],
           "family": fam_id[fam], "family_name": fam, "family_offset": foff, "stream": stream_of[r["stimulus"]],
           "ignored_stream": None, "ignored_lead": 0, "attended_side": None, "onset_s": None, "role": r["role"], "slab": r["slab"],
           "row_offset": r["row_offset"], "T_eeg": r["T_eeg"], "T_env": r["T_env"],
           "masked": info.get("masked", []) if cached else [],
           "segment_starts": C.segment_starts(r["T_env"], r["T_eeg"], COHORT).tolist() if cached else [],
           "run_id": r["run_id"], "sub": r["sub"], "ses": r["ses"], "run": r["run"], "task": r["task"], "block_role": r["block_role"],
           "role_c1": r["role_c1"],
           "condition": TASK, "noise_condition": r["noise_condition"], "snr": r["snr"], "noise_file": r["noise_file"],
           "flags": r["flags"], "structural": r["structural"], "audit": aud, "source_sha256": info.get("sha256") if cached else None,
           "file": r["file"]}
    if cached:
        rec.update(qc=info["qc"], car_ratio=info["car_ratio"], car_ok=info["car_ok"], max_abs_z=info["max_abs_z"])
    else:
        rec["raw_file"] = r["file"]                          # listed from its name and .npy header only
    return rec


def _participant_record(s, table, mark, fac):
    """One runs.json participant (fixture schema plus the C5 unit fields: sd_prez in the source unit, sd_prez_uV, median_prez_sd)."""
    p = next(q for q in table["participants"] if q["sub"] == s)
    sd = mark["sd_prez"]
    own = [v for v in sd if v is not None]
    return {"sub": s, "participant": s, "uid": f"{COHORT}:{s}", "identity": s, "role": p["block_role"], "group": COHORT,
            "session": p["session"], "fold": -1, "dev": False, "test_only": False, "donor": p["block_role"] in DONOR_ROLES,
            "masked": mark["masked_all_runs"], "mu": {"A": mark["mu"]}, "sd_prez": {"A": sd},
            "sd_prez_uV": {"A": None if fac is None else [None if v is None else v * fac for v in sd]},
            "median_prez_sd": {"A": float(np.median(own)) if own else None}, "n_stat_samples": {"A": mark["n_samples"]}}


UNIT_DOCUMENTED = (None, "none: the derivative arrays derivatives/preprocessed_eeg/*.npy (the authors' pipeline output) carry no "
                         "unit metadata; the per-run BIDS folders hold no channels.tsv or eeg.json, and code/ is never opened")


def _unit_rule_module():
    """build_public.py (M2b), the owner of UNIT_RULE; raises ImportError when the rule's three names are missing."""
    from auditory_alignment_v3.prior33 import build_public as BP
    missing = [n for n in ("UNIT_RULE", "unit_from_magnitude", "decide_unit") if not hasattr(BP, n)]
    if missing:
        raise ImportError(f"build_public.py lacks {missing}: the shared unit rule (design §2.13) moved")
    return BP


def cohort_unit(sd_by_participant):
    """The cohort unit record by UNIT_RULE of build_public.py (M2b; design §2.13: one fixed rule for every cohort, recorded in the
    manifest). sd_by_participant {sub: [C] 1-20 Hz pre-z SDs, None where a channel is masked in every run}: the magnitude rule on
    all participants x unmasked channels with the documented part UNIT_DOCUMENTED (none), then every participant's own median must
    give the same unit, else the cohort gets no unit (mode C unsupported)."""
    BP = _unit_rule_module()
    vals = {s: [float(v) for v in sd if v is not None and np.isfinite(v)] for s, sd in sorted(sd_by_participant.items())}
    unit = BP.decide_unit(UNIT_DOCUMENTED, BP.unit_from_magnitude([v for vs in vals.values() for v in vs]))
    own = {s: float(np.median(vs)) for s, vs in vals.items() if vs}
    other = sorted(s for s, m in own.items() if BP.unit_from_magnitude([m])[0] != unit.get("source_unit"))
    unit["participant_medians"] = {"n": len(own), "min": min(own.values()) if own else None,
                                   "max": max(own.values()) if own else None, "other_unit": other}
    if unit["supported"] and other:
        unit.pop("basis", None)
        unit.update(supported=False, name=None, source_unit=None, factor_to_uV=None,
                    reason=f"participants whose own median pre-z SD gives another unit than the cohort's: {other}")
    unit["rule_source"] = {"file": "auditory_alignment_v3/prior33/build_public.py",
                           "names": ["UNIT_RULE", "unit_from_magnitude", "decide_unit"], "sha256": _sha256_file(BP.__file__)}
    return unit


# ---------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m auditory_alignment_v3.prior33.build_sparrkulee", description=__doc__.split("\n")[0])
    ap.add_argument("--stage", required=True, choices=("C1", "C2", "C4"))
    ap.add_argument("--out", required=True, help=f"cache root: the §6.2 contract directory {CACHE_ROOT} (or, with "
                                                 "--allow-other-out, a scratch directory); outputs go to <out>/sparrkulee/")
    ap.add_argument("--src", default=None, help=f"dataset root (C1 default {SRC_DEFAULT}; C2 / C4 use the C1 table's)")
    ap.add_argument("--allow-other-out", action="store_true", help="permit an --out other than the §6.2 cache root (dry runs; "
                                                                   f"never under {DATA_VOLUME} and never overlapping the dataset)")
    ap.add_argument("--no-hash-eeg", action="store_true", help="C1: do not read the EEG .npy bytes for their sha256")
    ap.add_argument("--expect", choices=("real", "none"), default="real", help="C1: assert the real-data counts")
    ap.add_argument("--runs", default=None, help="C2: comma-separated run ids to audit (dry run); default all")
    a = ap.parse_args(argv)
    production = os.path.realpath(a.out) == os.path.realpath(CACHE_ROOT)
    if not production and not a.allow_other_out:
        ap.error(f"--out {a.out} is not the cache root {CACHE_ROOT}; pass --allow-other-out for a dry run")
    if production and a.stage == "C2" and a.runs is not None:
        ap.error("--runs (a partial dry-run audit) is refused under the cache root; use a scratch --out with --allow-other-out")
    if production and a.stage == "C1" and (a.no_hash_eeg or a.expect != "real"):
        ap.error("under the cache root C1 always hashes the EEG files and asserts the real-data expectations")
    try:
        check_out(a.out, a.src or (SRC_DEFAULT if a.stage == "C1" else None), _CLI)
    except OutputLocationError as e:
        ap.error(str(e))
    if a.stage == "C1":
        stage_c1(a.src or SRC_DEFAULT, a.out, expect=EXPECT_REAL if a.expect == "real" else None, hash_eeg=not a.no_hash_eeg,
                 _auth=_CLI)
    elif a.stage == "C2":
        stage_c2(a.src, a.out, runs=None if a.runs is None else [s for s in a.runs.split(",") if s], _auth=_CLI)
    else:
        stage_c4(a.src, a.out, _auth=_CLI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
