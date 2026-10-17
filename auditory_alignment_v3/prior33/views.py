"""E34_PUBLIC_PRIOR views (module M3; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.1, §2.2, §2.5, §2.12, §2.13,
§3.2, §3.3, §6.1 `views.py`, §6.2, §6.6 M3; contract aln33_env64_125ms_v1 in contract.py): the frozen manifest, the donor banks,
the target-cohort views, the target-stage batcher and representations on the contract ticks, and the private 64 Hz input.

Schema: the C6 manifest "prior33_manifest_v2" and the cohort caches of tests/auditory_alignment_v3/prior33/fixtures.py (module
docstring there), which is the manifest-schema interface of M3 (§6.6). Every list and pool size is read from the manifest, never
taken from the design's counts.

Public interface
  open_manifest(path, sha, root=None) -> Manifest     the manifest dict, verified against sha (full sha256 or a >= 16-hex prefix);
                                                      .path, .sha256, .root (the cache root that the relative cohort dirs use)
  DonorBank(manifest, cohort, roles, device, rich=False, root=None, pieces=None, segments=None)
                                                      one donor cohort's time-major fp16 cache on `device`: the role slabs `roles`
                                                      (mode "slabs"), or only some of their pieces (pieces=: an iterable of table
                                                      positions, or {role: iterable} restricting those roles; mode "pieces"), or
                                                      only the EEG spans [s, s + 357) of some segment-table rows (segments=; mode
                                                      "segments": validation, bridge and temperature sets); plus the cohort's
                                                      segment table and its envelope (and rich) streams.
      .gather(piece, start, offs) -> float16 [B, C, 38]      x = eeg[piece][start + offs : start + offs + 38], all channels; in
                                                             mode "segments" start must be a loaded segment start, 0 <= offs <= 319
      .targets(pres, start, offs) -> float32 [B, 8]          y = env_n[stream(pres)][start + offs : ... + 8]
      .rich_targets(pres, start, offs) -> (ss [B, 32], sc [B, 8], present [B])     (rich=True only)
      .all_ticks(piece, start, pres) -> (x [n*250, C, 38], y [n*250, 8])           every tick of n segments (validation, bridge)
      .iter_ticks(piece, start, pres, chunk=64) -> (i0, i1, x, y) per chunk of segments  (all_ticks without the whole output)
      .loaded(piece), .nbytes, .describe()
  target_view(cohort, cf, manifest, mode="A") -> TargetCohort (an auditory_alignment.data.Cohort)
  pool_of(coh, role, kind), test_queries(coh, subject_fold, kind)    ev1.evaluate_continuous's candidate pool and query set
  load_private64(kids=None) -> kids with x64          data.load_private() plus x64 [n, 20, 90] (private_to64, then z64_per_child)
  TickBatcher(coh, spec, row, dev, manifest, train_p=None)   (auditory_alignment_v2.train.Batcher); .train_p, .query_p (the
                                                      participant indices ev1 queries, bound to the manifest cell's test side),
                                                      .query_coverage {cell_test_participants, queried, cell_test_not_queried
                                                      (cell test / test_only ids without a test segment in the view)}
  TickReps(enc, aud, bt)                              (auditory_alignment.evaluate.Reps) with offs = TICK_OFFS
  PrivateBatcher64(kids, spec, row, dev)              (auditory_alignment_v2.train.PrivateBatcher) on window [32, 70) of x64
  check_piece_streams(cohort, items, pres_of, idx, streams)   the table-vs-manifest audio check of every cached piece
  condition_key(presentation)                         the XM same-condition key (sampler.py)
  contract_constants()                                the manifest constants block that open_manifest requires
  check_path(path), RestrictedAccess                  the restricted-participant file guard used by every read of this module
  IdSpaceError                                        a table whose presentation ids cannot be mapped to the manifest's

Memory (design §8 budgets; measured on the real C4 / C5 headers by the M3 review): whole fit slabs are SparrKULee 3.6 GB, FAU
0.86 GB (0.50 GB of it competing-talker trials, which only CSX samples), DTU about 0.14 GB and Federici about 0.2 GB. The sampler
therefore loads only the fit pieces its strata can draw (pieces=, sampler.py), and a bridge or validation unit should load its fixed
segments only (segments=: 2,000 x 357 x 64 x 2 bytes = 91 MB instead of the 3.6 GB slab). gather() fills a preallocated output in
chunks of GATHER_CHUNK rows, so its peak is the output plus about 20 MB (no 2x transient). all_ticks() returns n x 250 windows
(1.2 MB per 64-channel segment: 400 dev segments 0.49 GB, 2,000 bridge segments 2.4 GB); iterate large sets with iter_ticks().

Data-use guards (enforced in code, tests in tests/auditory_alignment_v3/prior33/test_views_sampler.py)
- Restricted SparrKULee participants (sub-019/020/021/022/026, RESTRICTED): this module opens only cohort-level files (the
  manifest, runs.json / pieces.json, streams.json, rich_streams.json, env_f32.npy, rich_f32.npy and the eeg_*_f16_tmajor.npy
  caches). Every path goes through check_path(), which raises RestrictedAccess for a path that names a restricted participant
  under a sparrkulee directory, given and symlink-resolved: 'sub-0XX' inside any path component, at its start or after a
  non-alphanumeric character and not followed by a digit, in any case (sub-019, sub-019_ses-1_eeg.npy, sub-019.npy,
  sub-019-eeg.npy, train_-_sub-019_-_eeg.npy; not sub-0190 or sub-023). A loaded SparrKULee
  piece or segment-table row of a restricted participant raises RestrictedAccess as well, and every loaded slab must be covered
  exactly by its listed pieces (contiguous, no unlisted rows), so no cache row of unknown origin is ever moved to a device.
  Table entries of restricted runs (raw_file) are never opened.
- Nothing is unpickled: .npy files are read with np.load(..., allow_pickle=False) (a memory map for the caches), JSON with json.
  No dataset code runs.
- DonorBank loads only donor role slabs (BANK_ROLES: fit, dev, bridge_cal, and SparrKULee's control_artefact for the artefact-run
  probe of §2.11); excluded_rule, holdout_seen_content, target_only (DTU HI / two-talker, the Federici phantom) are refused. Its
  layout and guards must be the contract's (MONTAGES, GUARDS), and every manifest segment row must name a cached piece of the same
  participant at one of its segment_starts; a row whose role is one of BANK_ROLES must lie on a piece of that slab (a role outside
  BANK_ROLES, such as C6's excluded_declared on a dev-slab run, is never read by role), and its family and kind must be those of
  its presentation. Presentation keys must be unique (one key, one presentation), and targets() / rich_targets() refuse a
  presentation id outside the manifest or one without an attended stream (no index wraps to the last stream).
- Table vs manifest (DonorBank and target_view, check_piece_streams): every cached piece must map to a manifest presentation of
  its cohort (IdSpaceError when the table's ids cannot be mapped, for donors as for targets: nothing is keyed unchecked), that
  presentation must be the one of every manifest segment row of the piece, and its kind, attended stream, ignored stream,
  ignored lead, attended side and acoustic condition (condition, noise_condition, snr, noise_file) must equal the piece's own
  table fields (the fields the table carries), with the stream's length equal to the piece's T_env. EEG can therefore never be
  paired with another presentation's envelope or keys through a manifest / table mismatch, also between presentations that
  share a stream (FAU competing talker left / right; DTU HI equalised / NH original; the Federici phantom / the human item).
- target_view is for the target cohorts fau / dtu / federici only. TickBatcher binds both sides of ev1 to the manifest cell: its
  training participants are cell.train (no cell.test participant and no test_only session can train), and the participants
  that ev1.evaluate_continuous queries (test segments, fold == row subject fold or test_only) are exactly the cell's test and
  test_only participants with test segments, none of them in cell.train. A zero-shot batcher (train_p = set()) has no training or
  early-stopping segment at all.

Interpretations (the design names the object but not every detail; each is listed as a deviation of the M3 summary)
- open_manifest(path, sha) requires a sha (no unverified open); it also checks schema, contract and the constants against
  contract.py: the manifest's constants block must hold exactly contract_constants() (fs, l_in, n_tgt, seg_ticks, seg_step,
  env_edge, neighbor, tau, onset64, key_bits, tick_offs_sha256: the block C6 and the fixture write), each equal to contract.py; a
  missing block, a missing or unknown key or a different value raises (before, only the keys present were compared, so a
  manifest without constants opened). The cohort dirs are relative to `root`: the argument, else manifest["cache_root"], else
  the manifest's directory (§6.2 writes a copy into private/...; open that copy with root=CACHE_ROOT). Functions taking
  `manifest` accept a Manifest or a plain dict plus root=.
- Global ids: the manifest's presentation / family ids are the only ids used for keys. A piece's presentation comes from
  manifest.cohorts[c].piece_presentation when C6 provides it, else from the table when the table is in the manifest id space
  (the fixture; no id_space field, or "global"), cross-checked against every segment-table row of the piece, else (id_space
  "cohort_local_provisional", the C1/C4/C5 builders) by presentation_key against manifest presentations[].key; otherwise
  IdSpaceError, in DonorBank as in target_view (the M3 review: SparrKULee never gets a target_view, so a bank that went on
  "not checked" would skip its only table-vs-manifest check). Families, family offsets and streams come from the manifest
  presentation; presentation.stream indexes the cohort's streams.json (as in the fixture and the builders, whose stream ids are
  the positions in their own streams.json in either id space) and must equal the table's piece stream (check_piece_streams).
- XM condition (condition_key): the manifest presentation's condition plus the acoustic condition fields that a C6 presentation
  may carry beside it (noise_condition, snr: build_sparrkulee.py keeps the task state 'listeningActive' in condition and the events
  condition / SNR there; §2.5 "condition (SNR, noise file)"); numbers compare as floats. The noise file is left out: on the real
  C4 table it is stimulus-specific (noise_<stimulus>.npz.gz; 63 files for 72 presentations), so with it every presentation would
  be its own condition and the preference would be empty. The real fit presentations then form 4 classes (in_noise SNR 100: 47,
  no_noise: 4, in_noise -4 dB: 1, in_noise 2.5 dB: 1); in_noise at 100 dB SNR and no_noise stay separate classes. Without those
  fields (the fixture, FAU, DTU, Federici) the key is the condition string alone. To be confirmed with C6 / the lead.
- Family offsets: a presentation of an unknown-clock family (clock "unknown") packs its own clock (offset as stored, None -> 0):
  the NCE mask covers every other presentation of such a family at any time (losses.py), so its offset never matters. A
  presentation of a known-clock family without an offset cannot be packed: using it in a key raises.
- DonorBank.gather returns float16 (the cache precision; the model casts); the windows are checked to lie inside the piece's
  guards [g0, T_eeg - g1), and targets inside the stream's 41-sample edges. The modes "pieces" and "segments" are additions of
  this module (the design's bank holds whole role slabs); they change which cache rows are copied, never a gathered value: a
  window of a loaded piece or segment equals the slab bank's window (tested).
- target_view: segments are built from every cached piece of every participant (all role slabs, the phantom included) at the
  target-stage starts: piece.segment_starts_target_stage when the builder records it (build_public.py), else the contract rule
  re-derived and checked: segment_starts (with the competing-talker onset rule for DTU two-talker trials, §2.2 "DTU target-stage
  evaluation"), and for FAU competing-talker pieces the guard-only starts (§2.2 applies the onset rule to FAU "in CSX only"; ALN3
  load_fau does the same). Roles come from the cell content split of the content fold (FAU {ss, cs}: {fit, es, test}: codes; DTU
  and Federici {fit, es, test}: stimulus ids); a cached piece with no role, or with two, raises. The donor shared-audio mask is
  not applied at the target stage (ALN3 cells are bound unchanged, §3.3); the number of target segments that meet a manifest
  shared-audio span is recorded in meta.
- Segment fields: p, e0 (= row_offset + s; eeg columns are the cache rows), s0 (= stream offset + s), s0_ign (ignored stream at
  s - ignored_lead, or None), role, kind, uid, hard_key, part, feat, code, plus presentation, family, fs0 (the family-clock sample
  of the segment start: family_offset + s), piece, s, stream. uid = "<cohort>:s<stream>@<s>": the attended envelope stream and
  start, i.e. the audio of the candidate (two listeners of one stream at one start share it, so a DTU HI listener's
  individually equalised presentation, whose target is the original's envelope, shares the original's candidate, and the
  candidate pool has no duplicate audio). hard_key / part as ALN3 (FAU code[1] / code[2]; DTU "dtu" / content group; Federici
  "fed" / "g<content group>"); feat = [mean, SD, mean |diff|] of the 2-8 Hz envelope over [s0, s0 + 320) for every cohort (the
  ALN3 Federici summary; the ALN3 'Ac' features do not exist under this contract).
- Mode inputs: A eeg_f16_tmajor.npy (z per participant x channel), B FAU eeg_noica_z_f16_tmajor.npy, C / C_partial
  eeg_raw_f16_tmajor.npy divided per channel by manifest.mode_c[cohort].scale (refused unless supported for that mode). coh.eeg is
  float16 [C, N] (the cache precision, halving host memory; the batcher moves it to the device as float16 like the ALN Batcher).
  meta.pool_sha256 hashes the stimulus-defined part (participants and segments without the EEG), identical for every mode and for
  adapted and zero-shot rows of a cell; meta.view_sha256 adds the mode, the cache file and the mode-C scale.
- TickBatcher does not call Batcher.__init__ (which would build the 128 Hz window ranges and Python-hash keys): it sets every
  attribute the inherited patches / audio / epoch_batches and the A_LOCAL fit loop read. W = [(0, 38)]; rows() draws one phase
  phi ~ U{0..30} per segment (rng.integers(0, 31, size=n), the ALN call pattern), ticks j = phi + 31 a, offsets TICK_OFFS[j],
  packed keys pack_key(family, presentation, fs0 + TICK_OFFS[j]); with roll=True the audio and the keys are those of the rolled
  segment at the same ticks. Only paired_alignment (kind ss) is supported; pairing "declared_wrong_pair" raises (no target-stage
  wrong pairing in this contract).
- TickReps raises for any stride (the contract evaluates on the 250 ticks).
- PrivateBatcher64 does not call PrivateBatcher.__init__ (which crops the 250 Hz epochs); it rebuilds the same attributes from
  x64[:, :, 32:70] with W = [(0, 38)], lo = 32, hi = 70 (so fit_private logs windows_samples_from_epoch_start [[32, 70]]).
  load_private64(kids=None) takes already-loaded children for tests; by default it calls auditory_alignment.data.load_private().
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re

import numpy as np
import torch

from auditory_alignment import evaluate as ev1
from auditory_alignment.data import Cohort
from auditory_alignment_v2.train import Batcher, PrivateBatcher, train_participants

from . import contract as C

SCHEMA = "prior33_manifest_v2"
RICH_SCHEMA = "prior33_manifest_rich_v1"
MANIFEST = "manifest.json"
MANIFEST_RICH = "manifest_rich.json"
RICH_DONOR_FAMILY = "ALN32_PUBLIC_AUDIO_PRIOR_RICH_DONOR"
PRIVATE_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                           "private", "auditory_alignment_v3", "aln34", "prior33")
CACHE_ROOT = "/projects/EEG-foundation-model/auditory_public/derived/" + C.CONTRACT     # §6.2
RESTRICTED = ("019", "020", "021", "022", "026")       # access-restricted SparrKULee participants (§3.2): never opened
TARGET_COHORTS = ("fau", "dtu", "federici")
DONOR_COHORTS = ("sparrkulee", "fau", "dtu", "federici")
BANK_ROLES = ("fit", "dev", "bridge_cal", "control_artefact")
COHORT_CODE = {"sparrkulee": 1, "fau": 2, "dtu": 3, "federici": 4}      # participant ids: code * 10**6 + table index
SEG_LEN = C.SEG_STEP                                   # 320 samples: the 5 s segment step (meta.seg_len)
PRIVATE_INPUT = "p64_lp20_z64_v1"                      # §4.3 private_input
GATHER_CHUNK = 4096                                    # gather rows per chunk: transient 4096 x 38 x C x 2 bytes (20 MB at C = 64)
SEG_KEY = 1 << 32                                      # (piece, segment start) lookup key of a "segments" bank
BANK_MODES = ("slabs", "pieces", "segments")
COND_FIELDS = ("condition", "noise_condition", "snr")   # condition_key(): the XM same-condition key (not noise_file: per stimulus)
PIECE_COND_FIELDS = COND_FIELDS + ("noise_file",)       # check_piece_streams: the acoustic condition of a piece vs its presentation


class RestrictedAccess(PermissionError):
    """A file or a cache row of an access-restricted SparrKULee participant was about to be read."""


class IdSpaceError(ValueError):
    """A cohort table's presentation ids cannot be mapped to the manifest's global ids."""


# ---------------------------------------------------------------------------------------------------------- file guards
# a participant id inside a path component: at its start or after a non-alphanumeric character, and not followed by a digit
# (sub-019, sub-019_ses-1_eeg.npy, sub-019.npy, sub-019-eeg.npy, train_-_sub-019_-_eeg.npy; not sub-0190); any case
_SUB = re.compile(r"(?:^|[^0-9a-z])sub-(\d{3})(?!\d)", re.IGNORECASE)


def _restricted_in(path):
    parts = [p for p in re.split(r"[\\/]+", str(path)) if p]
    if not any("sparrkulee" in p.lower() for p in parts):
        return None
    for p in parts:
        for m in _SUB.finditer(p):
            if m.group(1) in RESTRICTED:
                return m.group(1)
    return None


def check_path(path):
    """Raise RestrictedAccess when `path` (as given or symlink-resolved) names a restricted SparrKULee participant."""
    for q in (os.path.abspath(path), os.path.realpath(path)):
        sub = _restricted_in(q)
        if sub is not None:
            raise RestrictedAccess(f"refused: {path!r} names restricted SparrKULee participant sub-{sub}")
    return path


_VERIFIED_FILES = set()


def verify_file(manifest, path, root=None):
    """Verify only a consumed file, once per unchanged inode/stat and expected digest in this process.

    Production manifests bind every cache byte. Tiny synthetic manifests may omit files.
    Lazy checks preserve leave-target-out access: opening a donor manifest reads no target cache.
    """
    check_path(path)
    files = (manifest or {}).get("files")
    if not files:
        return
    rel = os.path.relpath(path, manifest_root(manifest, root))
    entry = files.get(rel)
    if not entry or not entry.get("sha256") or entry.get("bytes") is None:
        raise ValueError(f"cache integrity: {rel} has no sha256/bytes in the frozen manifest")
    st = os.stat(path)
    key = (os.path.realpath(path), st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, entry["sha256"])
    if key in _VERIFIED_FILES:
        return
    if st.st_size != int(entry["bytes"]):
        raise ValueError(f"cache integrity: {rel} bytes {st.st_size} != frozen {entry['bytes']}")
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            digest.update(chunk)
    after = os.stat(path)
    if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (st.st_size, st.st_mtime_ns, st.st_ctime_ns):
        raise ValueError(f"cache integrity: {rel} changed while being verified")
    if digest.hexdigest() != entry["sha256"]:
        raise ValueError(f"cache integrity: {rel} sha256 differs from the frozen manifest")
    _VERIFIED_FILES.add(key)


def _read_json(path, manifest=None, root=None):
    check_path(path)
    verify_file(manifest, path, root)
    with open(path) as f:
        return json.load(f)


def _load_npy(path, mmap=False, manifest=None, root=None):
    check_path(path)
    verify_file(manifest, path, root)
    return np.load(path, mmap_mode="r" if mmap else None, allow_pickle=False)


def _canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), default=lambda x: x.tolist() if hasattr(x, "tolist") else str(x))


def _sha_json(o):
    return hashlib.sha256(_canon(o).encode()).hexdigest()


def _cond_value(v):
    """A COND_FIELDS value as condition_key compares it: numbers (not booleans) as floats, anything else unchanged."""
    if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, (bool, np.bool_)):
        return float(v)
    return v


def condition_key(p):
    """The XM same-condition key of a manifest presentation (§2.5, §2.6, §2.14): canonical JSON of its COND_FIELDS (condition,
    noise_condition, snr; absent fields None, numbers as floats), so SparrKULee presentations that share the task state
    'listeningActive' still differ by noise condition and SNR (module docstring, Interpretations)."""
    return _canon([_cond_value(p.get(f)) for f in COND_FIELDS])


# ---------------------------------------------------------------------------------------------------------- manifest
class Manifest(dict):
    """The frozen C6 manifest (a dict) with .path, .sha256 (verified) and .root (the cache root of its relative cohort dirs)."""

    def __init__(self, data, path=None, sha256=None, root=None):
        super().__init__(data)
        self.path, self.sha256, self.root = path, sha256, root
        self._index = None


def _match_sha(got, want):
    w = str(want or "").lower()
    if len(w) < 16 or not re.fullmatch(r"[0-9a-f]+", w):
        raise ValueError(f"open_manifest: a sha256 (full, or a prefix of >= 16 hex digits) is required, got {want!r}")
    return got.startswith(w)


def contract_constants():
    """The manifest `constants` block as contract.py defines it: the keys C6 (manifest.py) and the fixture write."""
    return {"fs": C.FS, "l_in": C.L_IN, "n_tgt": C.N_TGT, "seg_ticks": C.SEG_TICKS, "seg_step": C.SEG_STEP, "env_edge": C.ENV_EDGE,
            "neighbor": C.NEIGHBOR, "tau": C.TAU, "onset64": C.ONSET64, "key_bits": [C.FAMILY_BITS, C.PRES_BITS, C.S_BITS],
            "tick_offs_sha256": hashlib.sha256(np.ascontiguousarray(C.TICK_OFFS, dtype=np.int64).tobytes()).hexdigest()}


def _same_constant(got, want):
    """JSON value `got` equals the contract value `want` (lists element-wise; true / false are not the numbers 1 / 0)."""
    if isinstance(want, (list, tuple)):
        return isinstance(got, (list, tuple)) and len(got) == len(want) and all(_same_constant(a, b) for a, b in zip(got, want))
    if isinstance(want, str):
        return isinstance(got, str) and got == want
    return isinstance(got, (int, float)) and not isinstance(got, bool) and got == want


def _check_constants(man):
    """The manifest's constants block holds exactly contract_constants(), each equal to contract.py: a missing block, a missing or
    unknown key and a different value raise (fail closed; module docstring, Interpretations)."""
    want, cst = contract_constants(), man.get("constants")
    if not isinstance(cst, dict):
        raise ValueError(f"manifest constants: no constants block (C6 writes {sorted(want)}), so nothing ties the manifest to "
                         "contract.py")
    missing, unknown = sorted(set(want) - set(cst)), sorted(set(cst) - set(want))
    bad = {k: (cst[k], v) for k, v in want.items() if k in cst and not _same_constant(cst[k], v)}
    if missing or unknown or bad:
        raise ValueError(f"manifest constants differ from contract.py: missing {missing}, unknown {unknown}, different "
                         f"{bad} (manifest, contract)")


def open_manifest(path, sha, root=None):
    """Read the manifest, verify its sha256 (full or >= 16-hex prefix), schema, contract and constants -> Manifest."""
    with open(check_path(path), "rb") as f:
        raw = f.read()
    got = hashlib.sha256(raw).hexdigest()
    if not _match_sha(got, sha):
        raise ValueError(f"open_manifest: {path} has sha256 {got[:16]}..., expected {str(sha)[:16]}...")
    data = json.loads(raw)
    if data.get("schema") != SCHEMA or data.get("contract") != C.CONTRACT:
        raise ValueError(f"open_manifest: schema {data.get('schema')!r} / contract {data.get('contract')!r}; expected {SCHEMA} / {C.CONTRACT}")
    _check_constants(data)
    r = root or data.get("cache_root") or os.path.dirname(os.path.abspath(path))
    return Manifest(data, os.path.abspath(path), got, os.path.abspath(r))


def manifest_root(manifest, root=None):
    r = root or getattr(manifest, "root", None) or manifest.get("cache_root")
    if not r:
        raise ValueError("the cache root is unknown: open the manifest with open_manifest(path, sha, root=...) or pass root=")
    return r


def manifest_sha(manifest):
    return getattr(manifest, "sha256", None)


def cohort_dir(manifest, cohort, root=None):
    d = os.path.join(manifest_root(manifest, root), manifest["cohorts"][cohort]["dir"])
    if not os.path.isdir(d):
        raise FileNotFoundError(f"cohort directory {d} not found (cache root {manifest_root(manifest, root)!r}; a private copy of the "
                                f"manifest needs root={CACHE_ROOT!r})")
    return d


def cohort_table(manifest, cohort, root=None):
    """(table, items): the cohort's runs.json / pieces.json and its item list (`piece` of the segment table indexes it)."""
    info = manifest["cohorts"][cohort]
    t = _read_json(os.path.join(cohort_dir(manifest, cohort, root), info["table"]), manifest, root)
    return t, t[info["items"]]


def cohort_streams(manifest, cohort, root=None, name="streams"):
    info = manifest["cohorts"][cohort]
    rows = _read_json(os.path.join(cohort_dir(manifest, cohort, root), info[name]), manifest, root)["streams"]
    for i, r in enumerate(rows):
        if int(r["stream"]) != i:
            raise ValueError(f"{cohort} {name}.json: stream {r['stream']} at position {i}")
    return rows


def open_with_rich(manifest, rich_sha, rich_path=None):
    """An opened core views.Manifest (full or public copy) with the rich supplement merged: manifest['rich'] (the fixture's rich
    block) and cohorts[c].rich / rich_streams file names. rich_sha: full sha256 or a >= 16-hex prefix (required); the supplement
    must name the opened manifest's sha256. The result keeps the core path / sha256 / root and adds .rich_sha256, .rich_path."""
    root = manifest_root(manifest)
    path = rich_path or os.path.join(root, MANIFEST_RICH)
    with open(check_path(path), "rb") as f:
        raw = f.read()
    got, want = hashlib.sha256(raw).hexdigest(), str(rich_sha or "").lower()
    if len(want) < 16 or not re.fullmatch(r"[0-9a-f]+", want) or not got.startswith(want):
        raise ValueError(f"open_with_rich: {path} has sha256 {got[:16]}..., expected {want[:16]!r} (>= 16 hex digits)")
    doc = json.loads(raw)
    if doc.get("schema") != RICH_SCHEMA or doc.get("contract") != C.CONTRACT:
        raise ValueError(f"open_with_rich: schema {doc.get('schema')!r} / contract {doc.get('contract')!r}")
    msha = manifest_sha(manifest)
    if msha is None or msha not in (doc.get("core_manifest_sha256"), doc.get("core_manifest_public_sha256")):
        raise ValueError(f"open_with_rich: the supplement belongs to core manifest {str(doc.get('core_manifest_sha256'))[:16]}..., "
                         f"not to the opened {str(msha)[:16]}...")
    data = copy.deepcopy(dict(manifest))
    data["rich"] = doc["rich"]
    data.setdefault("files", {}).update(doc.get("files", {}))
    for c, v in doc["cohorts"].items():
        if c in data["cohorts"]:
            data["cohorts"][c].update(rich=v["rich"], rich_streams=v["rich_streams"])
    m = Manifest(data, getattr(manifest, "path", None), msha, root)
    m.rich_sha256, m.rich_path = got, os.path.abspath(path)
    return m


def open_for_row(row, *, paths=None, rich_paths=None, cache_root=None):
    """The frozen manifest a plan row quotes (module docstring, Consumers): views.open_manifest with spec.manifest_sha256 from the
    first of `paths` whose sha256 matches (default: the full copy PRIVATE_OUT/manifest.json, then the public copy
    <CACHE_ROOT>/manifest.json, cache root views.CACHE_ROOT; a mismatch falls through to the next path), and, when the spec carries
    manifest_rich_sha256, the rich supplement merged by open_with_rich from the first of `rich_paths` with that sha256 (default:
    PRIVATE_OUT/manifest_rich.json, then <CACHE_ROOT>/manifest_rich.json). A RICH_DONOR row without manifest_rich_sha256 is refused
    (its runner needs the rich block, §2.15). Raises ValueError (row fields, sha256 mismatch on every path) or FileNotFoundError
    (no candidate file exists)."""
    s = row.get("spec") or {}
    sha, rsha = s.get("manifest_sha256"), s.get("manifest_rich_sha256")
    eid = row.get("experiment_id")
    if not sha:
        raise ValueError(f"{eid}: the row has no spec.manifest_sha256 (§4.3)")
    if row.get("family_id") == RICH_DONOR_FAMILY and not rsha:
        raise ValueError(f"{eid}: a {RICH_DONOR_FAMILY} row needs spec.manifest_rich_sha256 (the rich supplement it trains with)")
    default = paths is None
    paths = [os.path.join(PRIVATE_OUT, MANIFEST), os.path.join(CACHE_ROOT, MANIFEST)] if default else list(paths)
    root = cache_root or (CACHE_ROOT if default else None)
    man, tried = None, []
    for p in paths:
        if not os.path.exists(p):
            tried.append(f"{p}: absent")
            continue
        try:
            man = open_manifest(p, sha, root=root)
            break
        except ValueError as ex:
            tried.append(f"{p}: {ex}")
    if man is None:
        err = ValueError if any(not t.endswith(": absent") for t in tried) else FileNotFoundError
        raise err(f"{eid}: no manifest with the row's sha256 {str(sha)[:16]}... ({'; '.join(tried)})")
    if not rsha:
        return man
    rich_paths = [os.path.join(PRIVATE_OUT, MANIFEST_RICH), os.path.join(CACHE_ROOT, MANIFEST_RICH)] if rich_paths is None \
        else list(rich_paths)
    tried = []
    for p in rich_paths:
        if not os.path.exists(p):
            tried.append(f"{p}: absent")
            continue
        try:
            return open_with_rich(man, rsha, p)
        except ValueError as ex:
            tried.append(f"{p}: {ex}")
    err = ValueError if any(not t.endswith(": absent") for t in tried) else FileNotFoundError
    raise err(f"{eid}: no rich supplement with the row's manifest_rich_sha256 {str(rsha)[:16]}... ({'; '.join(tried)})")



class _Index:
    """Arrays of the manifest's global presentation / family tables, the segment tables and the participant ids (cached on a
    Manifest; rebuilt for a plain dict)."""

    def __init__(self, man):
        P = man["presentations"]
        if [int(p["id"]) for p in P] != list(range(len(P))):
            raise ValueError("manifest presentations: ids must equal positions")
        F = man["families"]
        if [int(f["id"]) for f in F] != list(range(len(F))):
            raise ValueError("manifest families: ids must equal positions")
        self.n_pres = len(P)
        self.fam = np.array([int(p["family"]) for p in P], dtype=np.int64)
        self.cohort = np.array([p["cohort"] for p in P], dtype=object)
        self.stream = np.array([-1 if p.get("stream") is None else int(p["stream"]) for p in P], dtype=np.int64)
        self.ign = np.array([-1 if p.get("ignored_stream") is None else int(p["ignored_stream"]) for p in P], dtype=np.int64)
        self.ign_lead = np.array([int(p.get("ignored_lead") or 0) for p in P], dtype=np.int64)
        self.kind = np.array([p.get("kind", "ss") for p in P], dtype=object)
        self.side = [p.get("attended_side") for p in P]                                  # check_piece_streams
        self.cond_fields = {f: [_canon(_cond_value(p.get(f))) for p in P] for f in PIECE_COND_FIELDS}
        clock = {int(f["id"]): f.get("clock", "known") for f in F}
        self.unknown_clock = np.array([clock[int(f)] == "unknown" for f in self.fam], dtype=bool)
        off = []
        for p, unk in zip(P, self.unknown_clock):
            o = p.get("family_offset")
            known = p.get("offset_known", o is not None)
            off.append(int(o or 0) if unk else (int(o) if (o is not None and known) else -1))
        self.famoff = np.array(off, dtype=np.int64)          # -1: known-clock family, offset unknown (cannot be packed)
        ck = [condition_key(p) for p in P]
        self.cond_names = sorted(set(ck))
        pos = {c: i for i, c in enumerate(self.cond_names)}
        self.cond = np.array([pos[c] for c in ck], dtype=np.int64)      # XM same-condition classes (condition_key)
        self.key = {}
        for p in P:
            k = p.get("key", p.get("presentation_key"))
            if k is not None:
                k = str(k)
                if k in self.key:      # the builders' keys are cohort-prefixed and C6 refuses duplicates: a repeat is ambiguous
                    raise ValueError(f"manifest presentations {self.key[k]} and {int(p['id'])} share the key {k!r}: pieces are "
                                     "mapped to presentations by key, so every key must name one presentation")
                self.key[k] = int(p["id"])
        self.seg = {c: _seg_arrays(man["segments"][c]) for c in man.get("segments", {})}
        self.shared = {}
        for d in man.get("shared_audio", ()):
            self.shared.setdefault(int(d["presentation"]), []).append(tuple(int(v) for v in d["span"]))

    def fs0(self, pres, s):
        """Family-clock sample of piece sample s of presentation pres (vectorised); raises for an unknown offset."""
        pres = np.asarray(pres, dtype=np.int64)
        o = self.famoff[pres]
        if (o < 0).any():
            bad = sorted(set(pres[o < 0].tolist()))[:5]
            raise ValueError(f"presentations {bad} of known-clock families have no family offset: their keys cannot be packed (§2.5)")
        return o + np.asarray(s, dtype=np.int64)

    def keys(self, pres, s):
        """Packed contract keys of (presentation, piece sample) rows: (family << 40) | (presentation << 24) | fs0."""
        pres = np.asarray(pres, dtype=np.int64)
        return C.pack_key(self.fam[pres], pres, self.fs0(pres, s))


def _seg_arrays(S):
    out = {k: np.asarray(S[k], dtype=np.int64) for k in ("piece", "presentation", "family", "s", "n_listeners", "n_partners")}
    out.update({k: np.asarray(S[k], dtype=object) for k in ("participant", "role", "kind")})
    n = len(out["s"])
    if any(len(v) != n for v in out.values()):
        raise ValueError("manifest segment table: columns of different lengths")
    return out


def manifest_index(manifest):
    if isinstance(manifest, Manifest):
        if manifest._index is None:
            manifest._index = _Index(manifest)
        return manifest._index
    return _Index(manifest)


def participant_ids(table, cohort):
    """{participant: int id} = COHORT_CODE[cohort] * 10**6 + position in the table's participants (global, stable)."""
    return {str(p["participant"]): COHORT_CODE[cohort] * 10 ** 6 + i for i, p in enumerate(table["participants"])}


def piece_presentations(manifest, cohort, table, items):
    """Global presentation id of every cached piece (None for pieces without cache rows); docstring, Interpretations."""
    idx = manifest_index(manifest)
    given = manifest["cohorts"][cohort].get("piece_presentation")
    if given is not None:
        if len(given) != len(items):
            raise ValueError(f"manifest cohorts.{cohort}.piece_presentation has {len(given)} entries for {len(items)} pieces")
        out = [None if g is None else int(g) for g in given]
    elif table.get("id_space") in (None, "global", "manifest"):
        out = [None if it.get("presentation") is None else int(it["presentation"]) for it in items]
    else:
        if not idx.key:
            raise IdSpaceError(f"{cohort} table ids are {table.get('id_space')!r} and the manifest presentations carry no key: the "
                               "views cannot map pieces to global presentation ids (C6 must rewrite the table ids, give "
                               "cohorts.<c>.piece_presentation, or key its presentations)")
        miss = sorted({str(it["presentation_key"]) for it in items if it.get("row_offset") is not None and it.get("presentation_key")
                       is not None and str(it["presentation_key"]) not in idx.key})
        if miss:
            raise ValueError(f"{cohort}: presentation keys {miss[:3]} of cached pieces are not in the manifest")
        out = [None if it.get("presentation_key") is None or str(it["presentation_key"]) not in idx.key else idx.key[str(it["presentation_key"])]
               for it in items]
    S = idx.seg.get(cohort)
    if S is not None and len(S["s"]):
        got = np.array([-1 if out[i] is None else out[i] for i in S["piece"]], dtype=np.int64)
        bad = np.flatnonzero(got != S["presentation"])
        if len(bad):
            r = int(bad[0])
            raise ValueError(f"{cohort}: piece {int(S['piece'][r])} has presentation {int(got[r])} in the table but "
                             f"{int(S['presentation'][r])} in the manifest segment table (table ids not in the manifest id space)")
    for i, (it, p) in enumerate(zip(items, out)):
        if p is not None and it.get("row_offset") is not None and idx.cohort[p] != cohort:
            raise ValueError(f"{cohort}: piece {i} maps to presentation {p} of cohort {idx.cohort[p]}")
    return out


def check_piece_streams(cohort, items, pres_of, idx, streams):
    """Every cached piece (row_offset set) maps to a manifest presentation whose kind, attended stream, ignored stream, ignored
    lead, attended side and acoustic condition (PIECE_COND_FIELDS: condition, noise_condition, snr, noise_file; numbers as
    floats) equal the piece's own table fields, and the attended stream's length equals the piece's T_env (the builders and the
    fixture set T_env to it).
    A field the table does not carry is not compared (the fixture's pieces carry no condition); one the manifest presentation
    lacks counts as None. The manifest presentation decides every key and envelope window, the table decides the EEG rows: a
    mismatch would pair a piece's EEG with another presentation's envelope or keys, so it raises (M3 review). Side and condition
    tell apart the presentations that share a stream (FAU competing talker (code, left) / (code, right); a DTU HI listener's
    individually equalised presentation and the NH original). Returns the number of pieces checked."""
    n_st, n = len(streams), 0
    for i, (it, p) in enumerate(zip(items, pres_of)):
        if it.get("row_offset") is None:
            continue
        name = f"{cohort} piece {i} ({it.get('piece_id')})"
        if p is None:
            raise IdSpaceError(f"{name}: a cached piece without a manifest presentation")
        st, ign, lead = int(idx.stream[p]), int(idx.ign[p]), int(idx.ign_lead[p])
        bad = []
        if "kind" in it and str(it["kind"]) != str(idx.kind[p]):
            bad.append(f"kind {it['kind']!r} vs manifest {idx.kind[p]!r}")
        if not 0 <= st < n_st:
            bad.append(f"manifest stream {st} outside streams.json ({n_st} streams)")
        elif it.get("stream") is None or int(it["stream"]) != st:
            bad.append(f"stream {it.get('stream')} vs manifest {st}")
        elif int(it["T_env"]) != int(streams[st]["length"]):
            bad.append(f"T_env {it['T_env']} vs the length {streams[st]['length']} of manifest stream {st}")
        if ign >= n_st:
            bad.append(f"manifest ignored stream {ign} outside streams.json")
        if "ignored_stream" in it and (-1 if it["ignored_stream"] is None else int(it["ignored_stream"])) != ign:
            bad.append(f"ignored stream {it['ignored_stream']} vs manifest {None if ign < 0 else ign}")
        if "ignored_lead" in it and int(it["ignored_lead"] or 0) != lead:
            bad.append(f"ignored lead {it['ignored_lead']} vs manifest {lead}")
        if "attended_side" in it and it["attended_side"] != idx.side[p]:
            bad.append(f"attended side {it['attended_side']!r} vs manifest {idx.side[p]!r}")
        for f in PIECE_COND_FIELDS:
            if f in it and _canon(_cond_value(it[f])) != idx.cond_fields[f][p]:
                bad.append(f"condition field {f} {it[f]!r} vs manifest {idx.cond_fields[f][p]}")
        if bad:
            raise ValueError(f"{name} -> manifest presentation {p}: " + "; ".join(bad) + " (the table and the manifest describe "
                             "different audio for this EEG piece)")
        n += 1
    return n


def _guard_restricted(cohort, items, S=None):
    if cohort != "sparrkulee":
        return
    for it in items:
        sub = str(it.get("sub", it.get("participant")))
        if sub in RESTRICTED and (it.get("row_offset") is not None or it.get("segment_starts")):
            raise RestrictedAccess(f"sparrkulee table lists cache rows or segments for restricted participant sub-{sub}")
    if S is not None and len(S["participant"]):
        bad = sorted(set(map(str, S["participant"])) & set(RESTRICTED))
        if bad:
            raise RestrictedAccess(f"sparrkulee segment table has rows of restricted participants {bad}")


def _check_segment_table(cohort, items, S, idx):
    """Every manifest segment row names a cached piece of the same participant and one of that piece's segment starts; a row in a
    role that a bank loads by role (BANK_ROLES: fit, dev, bridge_cal, control_artefact) lies on a piece of that slab (a row of
    another role, e.g. C6's excluded_declared on a dev-slab run, enters no pool and no fixed set); its family and kind are those
    of the presentation it names (M3 review: a fit row relabelled dev, or a row with another family, was accepted)."""
    starts = {(i, int(s)) for i, it in enumerate(items) if it.get("row_offset") is not None for s in it.get("segment_starts") or ()}
    part = [str(it["participant"]) for it in items]
    slab = [it.get("slab", it.get("role")) for it in items]
    pres = S["presentation"]
    if len(pres) and (pres.min() < 0 or pres.max() >= idx.n_pres):
        raise ValueError(f"{cohort} segment table: presentation ids outside the manifest presentations (0..{idx.n_pres - 1})")
    for r, (i, s, p, role) in enumerate(zip(S["piece"].tolist(), S["s"].tolist(), S["participant"].tolist(), S["role"].tolist())):
        if not 0 <= i < len(items) or (i, s) not in starts or part[i] != str(p):
            raise ValueError(f"{cohort} segment row {r}: (piece {i}, s {s}, participant {p}) is not a cached piece start of that participant")
        if role in BANK_ROLES and slab[i] != role:
            raise ValueError(f"{cohort} segment row {r}: role {role!r} on piece {i} of slab {slab[i]!r} (a row a bank uses by role must "
                             "lie in that role's slab)")
    for col, want in (("family", idx.fam[pres]), ("kind", idx.kind[pres])):
        bad = np.flatnonzero(np.asarray(S[col] != want, dtype=bool))
        if len(bad):
            r = int(bad[0])
            raise ValueError(f"{cohort} segment row {r}: {col} {S[col][r]!r}, but its presentation {int(pres[r])} has {col} "
                             f"{want[r]!r} ({len(bad)} rows differ)")


def _slab_items(items, slab, rng0, rng1, cohort):
    """Pieces of one slab, checked to cover [rng0, rng1) exactly and contiguously (no unlisted cache rows)."""
    mine = sorted((int(it["row_offset"]), int(it["T_eeg"]), i) for i, it in enumerate(items)
                  if it.get("row_offset") is not None and it.get("slab", it.get("role")) == slab)
    pos = rng0
    for off, T, i in mine:
        if off != pos:
            raise ValueError(f"{cohort} slab {slab}: rows [{pos}, {off}) are not covered by a listed piece (piece {i})")
        pos = off + T
    if pos != rng1:
        raise ValueError(f"{cohort} slab {slab}: listed pieces end at {pos}, the slab at {rng1}")
    return [i for _, _, i in mine]


def _to_device(mm, ranges, n_ch, device, chunk=1 << 19):
    """Copy the cache rows of `ranges` ([a, b) row pairs, in order) into one float16 [n, C] tensor on `device`."""
    n = sum(b - a for a, b in ranges)
    E = torch.empty((n, n_ch), dtype=torch.float16, device=device)
    o = 0
    for a, b in ranges:
        for c0 in range(a, b, chunk):
            c1 = min(b, c0 + chunk)
            E[o:o + c1 - c0] = torch.from_numpy(np.array(mm[c0:c1], dtype=np.float16, copy=True)).to(device)   # writable copy
            o += c1 - c0
    return E


def _merge_ranges(ranges):
    out = []
    for a, b in ranges:
        if out and out[-1][1] == a:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def _masks(items, layout):
    """bool [n_items, C]: True = the channel is read (not a masked (piece, channel) cell)."""
    pos = {n: i for i, n in enumerate(layout)}
    m = np.ones((len(items), len(layout)), dtype=bool)
    for i, it in enumerate(items):
        for n in it.get("masked") or ():
            m[i, pos[C.canonical(n)]] = False
    return m


def _bcast(*xs):
    """1-D int64 arrays broadcast to one length (the gather / target index arguments)."""
    return [np.array(v, dtype=np.int64) for v in np.broadcast_arrays(*(np.asarray(x, dtype=np.int64).reshape(-1) for x in xs))]


def _piece_selection(pieces, roles, slab_items, cohort):
    """{role: set of table positions, or None for the whole slab} from DonorBank's pieces= argument."""
    if pieces is None:
        return {r: None for r in roles}
    if isinstance(pieces, dict):
        extra = sorted(set(pieces) - set(roles))
        if extra:
            raise ValueError(f"DonorBank({cohort}): pieces= names roles {extra} that are not loaded ({roles})")
        sel = {r: None if pieces.get(r) is None else {int(i) for i in pieces[r]} for r in roles}
        for r, s in sel.items():
            if s is not None and not s <= set(slab_items[r]):
                raise ValueError(f"DonorBank({cohort}): pieces {sorted(s - set(slab_items[r]))[:5]} are not cached pieces of slab {r}")
        return sel
    s = {int(i) for i in pieces}
    allowed = {i for r in roles for i in slab_items[r]}
    if not s <= allowed:
        raise ValueError(f"DonorBank({cohort}): pieces {sorted(s - allowed)[:5]} are not cached pieces of the slabs {roles}")
    return {r: s for r in roles}


# ---------------------------------------------------------------------------------------------------------- donor banks
class DonorBank:
    """One donor cohort's time-major fp16 cache on `device` (mode "slabs": the requested role slabs; "pieces": some of their
    pieces; "segments": only the EEG spans [s, s + 357) of some segment-table rows), its segment table and its streams."""

    def __init__(self, manifest, cohort, roles=("fit",), device="cpu", rich=False, root=None, pieces=None, segments=None):
        if cohort not in DONOR_COHORTS:
            raise ValueError(f"DonorBank: {cohort!r} is not a donor cohort (private_bdf is never a donor)")
        roles = tuple(roles)
        bad = [r for r in roles if r not in BANK_ROLES or (r != "fit" and cohort != "sparrkulee")]
        if bad or not roles or len(set(roles)) != len(roles):
            raise ValueError(f"DonorBank({cohort}): roles {roles} (allowed: fit; SparrKULee also dev, bridge_cal, control_artefact)")
        if pieces is not None and segments is not None:
            raise ValueError(f"DonorBank({cohort}): pieces= or segments=, not both")
        self.manifest, self.cohort, self.roles, self.device = manifest, cohort, roles, torch.device(device)
        info = manifest["cohorts"][cohort]
        self.layout = tuple(C.canonical(n) for n in info["layout"])
        self.n_ch = int(info["n_ch"])
        self.guards = tuple(int(g) for g in info.get("guards", C.GUARDS[cohort]))
        if len(self.layout) != self.n_ch or self.guards != C.GUARDS[cohort] or self.layout != C.MONTAGES[cohort]:
            raise ValueError(f"DonorBank({cohort}): layout / guards differ from the contract (contract.MONTAGES, GUARDS)")
        self.idx = manifest_index(manifest)
        self.segments = self.idx.seg[cohort]
        d = cohort_dir(manifest, cohort, root)
        self.table, self.items = cohort_table(manifest, cohort, root)
        _guard_restricted(cohort, self.items, self.segments)
        _check_segment_table(cohort, self.items, self.segments, self.idx)
        self.streams = cohort_streams(manifest, cohort, root)
        # the table's pieces must map to the manifest's presentations (IdSpaceError otherwise) and describe the same audio
        self.pres_of = piece_presentations(manifest, cohort, self.table, self.items)
        self.n_pieces_checked = check_piece_streams(cohort, self.items, self.pres_of, self.idx, self.streams)
        self.presentation_check = "checked"
        self.pid = participant_ids(self.table, cohort)
        self.participants = {str(p["participant"]): p for p in self.table["participants"]}
        slabs = info["role_slabs"]
        missing = [r for r in roles if r not in slabs]
        if missing:
            raise ValueError(f"DonorBank({cohort}): no role slab {missing} in the manifest")
        slab_items = {r: _slab_items(self.items, r, *(int(v) for v in slabs[r]), cohort) for r in roles}
        mm = _load_npy(os.path.join(d, info["caches"]["A"]), mmap=True, manifest=manifest, root=root)
        if mm.dtype != np.float16 or mm.shape != (int(info["n_rows"]), self.n_ch):
            raise ValueError(f"DonorBank({cohort}): cache {mm.dtype} {mm.shape}, manifest n_rows {info['n_rows']} x {self.n_ch}")
        self.T_eeg = np.array([int(it["T_eeg"]) for it in self.items], dtype=np.int64)
        self.base = np.full(len(self.items), -1, dtype=np.int64)
        self._seg_key = self._seg_base = None
        if segments is None:
            sel = _piece_selection(pieces, roles, slab_items, cohort)
            self.mode = "slabs" if all(v is None for v in sel.values()) else "pieces"
            ranges, o = [], 0
            for r in roles:
                for i in slab_items[r]:
                    if sel[r] is None or i in sel[r]:
                        a, T = int(self.items[i]["row_offset"]), int(self.items[i]["T_eeg"])
                        self.base[i] = o
                        ranges.append((a, a + T)); o += T
        else:
            self.mode = "segments"
            rows = np.unique(np.asarray([int(r) for r in segments], dtype=np.int64))
            S = self.segments
            if not len(rows) or rows.min() < 0 or rows.max() >= len(S["s"]):
                raise ValueError(f"DonorBank({cohort}): segments= must be rows of the {cohort} segment table")
            allowed = {i for r in roles for i in slab_items[r]}
            pc = S["piece"][rows]
            out = sorted(set(pc.tolist()) - allowed)
            if out:
                raise ValueError(f"DonorBank({cohort}): segment rows of pieces {out[:5]} lie outside the slabs {roles}")
            self._seg_key = np.unique(pc * SEG_KEY + S["s"][rows])
            self._seg_base = np.arange(len(self._seg_key), dtype=np.int64) * C.SPAN_EEG
            pk, sk = self._seg_key // SEG_KEY, self._seg_key % SEG_KEY
            a = np.array([int(self.items[i]["row_offset"]) for i in pk.tolist()], dtype=np.int64) + sk
            ranges, o = list(zip(a.tolist(), (a + C.SPAN_EEG).tolist())), len(self._seg_key) * C.SPAN_EEG
            self._seg_pieces = np.unique(pk)
        self.n_rows = o
        self.E = _to_device(mm, _merge_ranges(ranges), self.n_ch, self.device)
        del mm
        self.mask = _masks(self.items, self.layout)
        env = _load_npy(os.path.join(d, info["env"]), manifest=manifest, root=root)
        if env.dtype != np.float32 or env.ndim != 1:
            raise ValueError(f"DonorBank({cohort}): env {env.dtype} {env.shape}")
        self.env = torch.from_numpy(np.ascontiguousarray(env)).to(self.device)
        self.stream_off = np.array([int(r["offset"]) for r in self.streams], dtype=np.int64)
        self.stream_len = np.array([int(r["length"]) for r in self.streams], dtype=np.int64)
        if (self.stream_off + self.stream_len).max(initial=0) > len(env):
            raise ValueError(f"DonorBank({cohort}): streams exceed env_f32.npy")
        self.rich = None
        if rich:
            R = _load_npy(os.path.join(d, info["rich"]), manifest=manifest, root=root)
            if R.dtype != np.float32 or R.shape != (len(env), len(C.RICH_COLS)):
                raise ValueError(f"DonorBank({cohort}): rich {R.dtype} {R.shape}")
            rs = cohort_streams(manifest, cohort, root, "rich_streams")
            self.rich_available = np.array([bool(r["available"]) for r in rs], dtype=bool)
            self.rich = torch.from_numpy(np.ascontiguousarray(R)).to(self.device)
        self._ar38 = torch.arange(C.L_IN, device=self.device)
        self._ar8 = torch.arange(C.N_TGT, device=self.device)

    @property
    def nbytes(self):
        """Bytes held on the device: EEG rows, envelope and rich streams."""
        return int(self.E.numel() * self.E.element_size() + self.env.numel() * 4 + (0 if self.rich is None else self.rich.numel() * 4))

    def describe(self):
        """For the unit record: what the bank holds (resource accounting, §2.10 / §8)."""
        return {"cohort": self.cohort, "roles": list(self.roles), "mode": self.mode, "n_rows": int(self.n_rows),
                "n_pieces": int((self.base >= 0).sum()) if self.mode != "segments" else int(len(self._seg_pieces)),
                "n_segments": None if self.mode != "segments" else int(len(self._seg_key)), "eeg_bytes": int(self.E.numel() * 2),
                "nbytes": self.nbytes, "device": str(self.device), "presentation_check": self.presentation_check,
                "n_pieces_checked": int(self.n_pieces_checked)}

    def loaded(self, piece):
        """bool per piece: gather can read it (mode "segments": at its loaded segment starts only)."""
        piece = np.asarray(piece, dtype=np.int64)
        if self.mode == "segments":
            return np.isin(piece, self._seg_pieces)
        return self.base[piece] >= 0

    def gather(self, piece, start, offs):
        """EEG windows x = eeg[piece][start + offs : start + offs + 38], all channels -> float16 [B, C, 38] on the device."""
        piece, start, offs = _bcast(piece, start, offs)
        if len(piece) and (piece.min() < 0 or piece.max() >= len(self.items)):
            raise ValueError(f"DonorBank({self.cohort}): piece index outside the {self.cohort} table")
        w = start + offs
        g0, g1 = self.guards
        if (w < g0).any() or (w + C.L_IN > self.T_eeg[piece] - g1).any():
            raise ValueError(f"DonorBank({self.cohort}): a window leaves the guards [{g0}, T_eeg - {g1})")
        if self.mode == "segments":
            key = piece * SEG_KEY + start
            k = np.minimum(np.searchsorted(self._seg_key, key), len(self._seg_key) - 1)
            miss = self._seg_key[k] != key
            if miss.any():
                raise ValueError(f"DonorBank({self.cohort}): segments {sorted(set(zip(piece[miss].tolist(), start[miss].tolist())))[:3]} "
                                 f"(piece, start) are not loaded (mode segments)")
            if (offs < 0).any() or (offs + C.L_IN > C.SPAN_EEG).any():
                raise ValueError(f"DonorBank({self.cohort}): a window leaves its loaded segment span [s, s + {C.SPAN_EEG})")
            rows = self._seg_base[k] + offs
        else:
            b = self.base[piece]
            if (b < 0).any():
                raise ValueError(f"DonorBank({self.cohort}): pieces {sorted(set(piece[b < 0].tolist()))[:5]} are not in the loaded "
                                 f"slabs {self.roles} (mode {self.mode})")
            rows = b + w
        out = torch.empty((len(rows), self.n_ch, C.L_IN), dtype=torch.float16, device=self.device)
        for a in range(0, len(rows), GATHER_CHUNK):          # chunked: no transient copy of the whole output
            r = torch.as_tensor(rows[a:a + GATHER_CHUNK], device=self.device)[:, None] + self._ar38
            out[a:a + len(r)] = self.E[r].permute(0, 2, 1)
        return out

    def _target_index(self, pres, start, offs):
        pres, start, offs = _bcast(pres, start, offs)
        t = start + offs
        if len(pres) and (pres.min() < 0 or pres.max() >= self.idx.n_pres):        # a negative id would wrap to the last one
            raise ValueError(f"DonorBank({self.cohort}): presentation ids outside the manifest (0..{self.idx.n_pres - 1})")
        if (self.idx.cohort[pres] != self.cohort).any():
            raise ValueError(f"DonorBank({self.cohort}): presentations of another cohort")
        st = self.idx.stream[pres]
        nost = (st < 0) | (st >= len(self.stream_len))      # stream None (-1) would index the last stream (M3 review)
        if nost.any():
            raise ValueError(f"DonorBank({self.cohort}): presentations {sorted(set(pres[nost].tolist()))[:5]} have no attended stream "
                             f"in {self.cohort} streams.json")
        if (t < C.ENV_EDGE).any() or (t + C.N_TGT > self.stream_len[st] - C.ENV_EDGE).any():
            raise ValueError(f"DonorBank({self.cohort}): a target window touches the {C.ENV_EDGE}-sample stream edges")
        return st, torch.as_tensor(self.stream_off[st] + t, device=self.device)[:, None] + self._ar8

    def targets(self, pres, start, offs):
        """Envelope targets y = env_n[stream(pres)][start + offs : ... + 8] -> float32 [B, 8] (standardised later by the head)."""
        return self.env[self._target_index(pres, start, offs)[1]]

    def rich_targets(self, pres, start, offs):
        """Rich targets (rich=True): y_ss [B, 32] (8 samples x 4 PCA dims, sample-major), y_sc [B, 8], present [B] bool
        (stream available and the window finite); absent rows hold NaN (masked, never zero-filled)."""
        if self.rich is None:
            raise ValueError(f"DonorBank({self.cohort}): built without rich=True")
        st, idx = self._target_index(pres, start, offs)
        R = self.rich[idx]                                                    # [B, 8, 5]
        ok = torch.as_tensor(self.rich_available[st], device=self.device) & torch.isfinite(R).flatten(1).all(1)
        return R[:, :, :4].reshape(len(R), -1), R[:, :, 4], ok

    def all_ticks(self, piece, start, pres):
        """Every tick of n segments (full montage): x [n*250, C, 38] float16, y [n*250, 8] float32, segment-major.

        The output is n x 250 x C x 38 x 2 bytes (1.2 MB per 64-channel segment: 400 dev segments 0.49 GB, 2,000 bridge segments
        2.4 GB) on the bank's device; the gather adds only about 20 MB on top. Iterate a large set with iter_ticks()."""
        piece = np.repeat(np.asarray(piece, dtype=np.int64).reshape(-1), C.SEG_TICKS)
        start = np.repeat(np.asarray(start, dtype=np.int64).reshape(-1), C.SEG_TICKS)
        pres = np.repeat(np.asarray(pres, dtype=np.int64).reshape(-1), C.SEG_TICKS)
        if not len(piece) == len(start) == len(pres):
            raise ValueError("all_ticks: piece, start and pres must have one entry per segment")
        offs = np.tile(C.TICK_OFFS.astype(np.int64), len(piece) // C.SEG_TICKS)
        return self.gather(piece, start, offs), self.targets(pres, start, offs)

    def iter_ticks(self, piece, start, pres, chunk=64):
        """all_ticks() over chunks of `chunk` segments: yields (i0, i1, x, y) for segments [i0, i1) (64 segments: 78 MB at 64 ch)."""
        piece, start, pres = (np.asarray(v, dtype=np.int64).reshape(-1) for v in (piece, start, pres))
        if not len(piece) == len(start) == len(pres):
            raise ValueError("iter_ticks: piece, start and pres must have one entry per segment")
        if int(chunk) < 1:
            raise ValueError("iter_ticks: chunk >= 1 segment")
        for a in range(0, len(piece), int(chunk)):
            b = min(len(piece), a + int(chunk))
            x, y = self.all_ticks(piece[a:b], start[a:b], pres[a:b])
            yield a, b, x, y


# ---------------------------------------------------------------------------------------------------------- target views
class TargetCohort(Cohort):
    """An auditory_alignment.data.Cohort of every participant of a target cohort on the 64 Hz contract grid (+ layout)."""

    def __init__(self, fs, n_ch, participants, eeg, stim, segments, meta, layout):
        super().__init__(fs, n_ch, participants, eeg, stim, segments, meta)
        self.layout = list(layout)


def content_split(manifest, cohort, cf):
    """The cell content split of (cohort, content fold); every cell of that content fold must agree."""
    cells = [c for c in manifest["cells"] if c["dataset"] == cohort and int(c["content_fold"]) == int(cf)]
    if not cells:
        raise ValueError(f"no manifest cell for {cohort} content fold {cf}")
    ref = _canon(cells[0]["content"])
    if any(_canon(c["content"]) != ref for c in cells[1:]):
        raise ValueError(f"{cohort} cf{cf}: the cells disagree on the content split")
    return cells[0]["content"]


def manifest_cell(manifest, dataset, subject_fold, content_fold):
    cells = [c for c in manifest["cells"] if c["dataset"] == dataset and int(c["subject_fold"]) == int(subject_fold)
             and int(c["content_fold"]) == int(content_fold)]
    if len(cells) != 1:
        raise ValueError(f"{len(cells)} manifest cells for {dataset} sf{subject_fold} cf{content_fold}")
    return cells[0]


def _role_of(content, stimulus, kind):
    d = content[kind] if isinstance(content.get(kind), dict) else content
    roles = [r for r in ("fit", "es", "test") if str(stimulus) in {str(x) for x in d.get(r, ())}]
    if len(roles) != 1:
        raise ValueError(f"content split: stimulus {stimulus!r} ({kind}) has roles {roles}")
    return roles[0]


def _target_starts(cohort, it):
    """Target-stage starts of a piece by the contract rule (§2.2), checked against the builder's segment_starts and, when
    recorded, segment_starts_target_stage: the onset rule for DTU two-talker pieces, guard-only for FAU competing talker."""
    onset = it.get("onset_s") if it.get("kind") == "cs" else None
    rule = C.segment_starts(it["T_env"], it["T_eeg"], cohort, onset=onset).tolist()
    if [int(s) for s in it["segment_starts"]] != rule:
        raise ValueError(f"{cohort} piece {it.get('piece_id')}: segment_starts differ from contract.segment_starts")
    if cohort == "fau" and it.get("kind") == "cs":        # the onset rule is for DTU target-stage evaluation and FAU in CSX only
        rule = C.segment_starts(it["T_env"], it["T_eeg"], cohort).tolist()
    given = it.get("segment_starts_target_stage")
    if given is not None and [int(s) for s in given] != rule:
        raise ValueError(f"{cohort} piece {it.get('piece_id')}: segment_starts_target_stage differ from the contract rule")
    return rule


def _hard(cohort, it):
    code = str(it["stimulus"])
    if cohort == "fau":
        return code[1], code[2]
    if cohort == "dtu":
        return "dtu", str(it["content_group"])
    return "fed", f"g{it['content_group']}"


def _load_eeg_cm(path, n_rows, n_ch, scale=None, chunk=1 << 19, manifest=None, root=None):
    """A [N, C] fp16 cache -> float16 [C, N] (mode C: divided per channel by `scale` first)."""
    mm = _load_npy(path, mmap=True, manifest=manifest, root=root)
    if mm.dtype != np.float16 or mm.shape != (n_rows, n_ch):
        raise ValueError(f"{path}: {mm.dtype} {mm.shape}, expected float16 ({n_rows}, {n_ch})")
    out = np.empty((n_ch, n_rows), dtype=np.float16)
    for a in range(0, n_rows, chunk):
        b = min(n_rows, a + chunk)
        x = np.asarray(mm[a:b], dtype=np.float32)
        if scale is not None:
            x = x / scale[None]
        if not np.isfinite(x).all() or np.abs(x).max(initial=0) > np.finfo(np.float16).max:
            raise ValueError(f"{path}: non-finite values in rows [{a}, {b}) of the view")
        out[:, a:b] = x.T
    return out


PART_FIELDS = ("uid", "identity", "group", "fold", "dev", "test_only", "donor", "masked", "age", "age_years", "behav_acc", "cs_side",
               "phantom")


def target_view(cohort, cf, manifest, mode="A", root=None):
    """ALN Cohort of ALL participants of a target cohort for content fold `cf` and input-access mode (§2.12, §2.13)."""
    if cohort not in TARGET_COHORTS:
        raise ValueError(f"target_view: {cohort!r} is not a public target cohort {TARGET_COHORTS}")
    if mode not in C.ZS_COHORTS or cohort not in C.ZS_COHORTS[mode]:
        raise ValueError(f"target_view: mode {mode!r} is not defined for {cohort} (contract.ZS_COHORTS)")
    info, idx = manifest["cohorts"][cohort], manifest_index(manifest)
    d = cohort_dir(manifest, cohort, root)
    table, items = cohort_table(manifest, cohort, root)
    layout = tuple(C.canonical(n) for n in info["layout"])
    if len(layout) != int(info["n_ch"]) or tuple(C.canonical(n) for n in manifest["montages"][cohort]) != layout:
        raise ValueError(f"target_view({cohort}): layout differs from manifest.montages")
    content = content_split(manifest, cohort, cf)
    pres_of = piece_presentations(manifest, cohort, table, items)
    streams = cohort_streams(manifest, cohort, root)
    check_piece_streams(cohort, items, pres_of, idx, streams)      # the table's audio = the manifest presentation's, every piece
    env = _load_npy(os.path.join(d, info["env"]), manifest=manifest, root=root)
    if env.dtype != np.float32 or env.ndim != 1:
        raise ValueError(f"target_view({cohort}): env {env.dtype} {env.shape}")
    if mode not in info["caches"]:
        raise ValueError(f"target_view({cohort}): no mode-{mode} cache in the manifest")
    scale = None
    if mode in ("C", "C_partial"):
        mc = (manifest.get("mode_c") or {}).get(cohort) or {}
        if not mc.get("supported") or mc.get("mode") != mode:
            raise ValueError(f"target_view({cohort}): mode {mode} is not supported by the manifest ({mc.get('reason', mc.get('mode'))})")
        scale = np.array([float(mc["scale"][n]) for n in layout], dtype=np.float32)
        if not (np.isfinite(scale).all() and (scale > 0).all()):
            raise ValueError(f"target_view({cohort}): mode-C scale must be finite and > 0")
    parts = table["participants"]
    p_of = {str(p["participant"]): i for i, p in enumerate(parts)}
    participants = [{"id": str(p["participant"]), **{k: p[k] for k in PART_FIELDS if k in p}} for p in parts]
    for q in participants:
        q.setdefault("dev", False); q.setdefault("test_only", False); q.setdefault("identity", q["id"])
    g0, g1 = C.GUARDS[cohort]
    segs, n_shared = [], 0
    for i, it in enumerate(items):
        if it.get("row_offset") is None:
            continue
        p = pres_of[i]
        kind = str(it["kind"])
        if p is None or idx.kind[p] != kind:                       # also checked by check_piece_streams
            raise ValueError(f"{cohort} piece {i}: presentation {p} (kind {None if p is None else idx.kind[p]}) for a {kind} piece")
        role = _role_of(content, it["stimulus"], kind)
        st = int(idx.stream[p]); so, T_s = int(streams[st]["offset"]), int(streams[st]["length"])
        ign, lead = int(idx.ign[p]), int(idx.ign_lead[p])
        hk, part = _hard(cohort, it)
        spans = idx.shared.get(p, ())
        for s in _target_starts(cohort, it):
            if s < g0 or s + C.SPAN_EEG > int(it["T_eeg"]) - g1 or s < C.ENV_EDGE or s + C.SPAN_ENV > T_s - C.ENV_EDGE:
                raise ValueError(f"{cohort} piece {i}: start {s} leaves the EEG guards or the target edges")
            s_ign = None
            if ign >= 0:
                si = s - lead
                if si < C.ENV_EDGE or si + C.SPAN_ENV > int(streams[ign]["length"]) - C.ENV_EDGE:
                    raise ValueError(f"{cohort} piece {i}: the ignored stream does not cover start {s}")
                s_ign = int(streams[ign]["offset"]) + si
            a = env[so + s:so + s + SEG_LEN].astype(np.float64)
            n_shared += any(x < s + C.SPAN_EEG and s < y for x, y in spans)
            segs.append({"p": p_of[str(it["participant"])], "e0": int(it["row_offset"]) + s, "s0": so + s, "s0_ign": s_ign, "role": role,
                         "kind": kind, "uid": f"{cohort}:s{st}@{s}", "hard_key": hk, "part": part, "code": str(it["stimulus"]),
                         "feat": np.r_[a.mean(), a.std(), np.abs(np.diff(a)).mean()], "presentation": int(p), "family": int(idx.fam[p]),
                         "fs0": int(idx.fs0([p], [s])[0]), "piece": i, "s": int(s), "stream": st,
                         **({"block": it["block"]} if "block" in it else {})})
    eeg = _load_eeg_cm(os.path.join(d, info["caches"][mode]), int(info["n_rows"]), len(layout), scale,
                       manifest=manifest, root=root)
    cols = ("p", "e0", "s0", "s0_ign", "role", "kind", "uid", "hard_key", "part", "presentation", "family", "fs0", "piece", "s")
    struct = {"contract": C.CONTRACT, "cohort": cohort, "content_fold": int(cf), "layout": list(layout),
              "participants": [[q["id"], q.get("group"), q.get("fold"), bool(q["dev"]), bool(q["test_only"]), q["identity"]] for q in participants],
              "segments": {k: [s[k] for s in segs] for k in cols}, "content": content}
    pool_sha = _sha_json(struct)
    meta = {"dataset": cohort, "content_fold": int(cf), "seg_len": SEG_LEN, "fs": C.FS, "mode": mode, "cache": info["caches"][mode],
            "contract": C.CONTRACT, "manifest_sha256": manifest_sha(manifest), "content_sha256": _sha_json(content),
            "pool_sha256": pool_sha, "n_segments": len(segs), "n_participants": len(participants),
            "n_segments_meeting_shared_audio": int(n_shared), "target_starts": "segment_starts_target_stage | contract rule (§2.2)",
            "view_sha256": _sha_json({"pool": pool_sha, "mode": mode, "cache": info["caches"][mode],
                                      "scale": None if scale is None else [float(v) for v in scale],
                                      "manifest_sha256": manifest_sha(manifest)})}
    return TargetCohort(C.FS, len(layout), participants, eeg, {"envelope": env[None].astype(np.float32)}, segs, meta, layout)


def pool_of(coh, role, kind):
    """ev1.evaluate_continuous's stimulus-defined pool: the first segment of each uid among (role, kind) -> ({uid: index}, rows)."""
    uids, rows = {}, []
    for s in coh.segments:
        if s["role"] == role and s["kind"] == kind and s["uid"] not in uids:
            uids[s["uid"]] = len(rows); rows.append(s)
    return uids, rows


def test_queries(coh, subject_fold, kind="ss"):
    """ev1's query participants (fold == subject_fold or test_only, with test segments) -> sorted participant indices."""
    return sorted({s["p"] for s in coh.segments if s["role"] == "test" and s["kind"] == kind and
                   (coh.participants[s["p"]]["fold"] == subject_fold or coh.participants[s["p"]].get("test_only"))})


test_queries.__test__ = False      # not a pytest test


# ---------------------------------------------------------------------------------------------------------- target-stage batcher
def _check_spec(spec):
    for k, v in (("architecture", "lag_local_tokens"), ("window", "full")):
        if spec.get(k) not in (None, v):
            raise ValueError(f"spec {k} = {spec.get(k)!r}; the contract uses {v!r}")
    if spec.get("pairing") == "declared_wrong_pair":
        raise ValueError("pairing 'declared_wrong_pair' is not part of this contract (XM is the donor-stage control)")


class TickBatcher(Batcher):
    """A_LOCAL anchor rows on the contract ticks with packed keys (§2.2, §2.5, §2.12); train_p overrides the fold's training set
    (zero-shot: set())."""

    def __init__(self, coh, spec, row, dev, manifest, train_p=None):
        _check_spec(spec)
        meta = coh.meta
        if coh.fs != C.FS or meta.get("seg_len") != SEG_LEN or meta.get("contract") != C.CONTRACT:
            raise ValueError("TickBatcher needs a target_view cohort (64 Hz, seg_len 320, this contract)")
        task = spec.get("training_task", "paired_alignment")
        if task != "paired_alignment":
            raise ValueError(f"TickBatcher: training_task {task!r} (the target stage trains paired_alignment on single-talker data)")
        if coh.eeg is None:
            raise ValueError("TickBatcher: the view's EEG was already moved to a device by another batcher (build a new view)")
        if meta.get("manifest_sha256") and manifest_sha(manifest) and meta["manifest_sha256"] != manifest_sha(manifest):
            raise ValueError("TickBatcher: the view was built from another manifest")
        ds, sf = meta["dataset"], int(row["subject_fold"])
        cf = int(row.get("content_fold") if row.get("content_fold") is not None else meta["content_fold"])
        if cf != int(meta["content_fold"]) or row.get("dataset", ds) != ds:
            raise ValueError(f"TickBatcher: row {row.get('dataset')} cf{cf} does not match the view {ds} cf{meta['content_fold']}")
        self.coh_segments, self.dev = coh.segments, dev
        self.fs, self.seg_len = coh.fs, SEG_LEN
        self.W = [(0, C.L_IN)]
        self.E = torch.from_numpy(np.ascontiguousarray(coh.eeg, dtype=np.float16)).to(dev)
        self.S = torch.from_numpy(np.ascontiguousarray(coh.stim["envelope"], dtype=np.float32)).to(dev)
        coh.eeg, coh.stim = None, None      # as the ALN Batcher: host copies are not used after the device transfer
        self.kind, self.selection, self.wrong = "ss", False, False
        cell = manifest_cell(manifest, ds, sf, cf)
        ids = [q["id"] for q in coh.participants]
        derived = train_participants(coh, spec, sf)
        dset, train_ids, test_ids = {ids[i] for i in derived}, set(map(str, cell["train"])), set(map(str, cell["test"]))
        test_ids |= set(map(str, cell.get("test_only", ())))
        if (dset != train_ids if not spec.get("train_population") else not dset <= train_ids) or dset & test_ids:
            raise ValueError(f"TickBatcher: fold-derived training participants differ from manifest cell {ds} sf{sf} cf{cf}")
        if train_p is not None and any(isinstance(i, (str, bytes, bool, np.bool_)) or not isinstance(i, (int, np.integer)) for i in train_p):
            raise TypeError("TickBatcher: train_p holds participant indices of coh.participants (ints), as the ALN Batcher's train_p")
        tp = set(derived) if train_p is None else {int(i) for i in train_p}
        if not tp <= set(derived):
            raise ValueError("TickBatcher: train_p must be a subset of the fold's training participants (no test participant)")
        segs = coh.segments
        # the query side, bound to the cell as the training side is: ev1.evaluate_continuous queries (and scores attention on) the
        # participants with test segments whose fold is the row's subject fold or who are test_only; they must be exactly the
        # cell's test and test_only participants that have test segments, and none of them a training participant of the cell
        with_test = {s["p"] for s in segs if s["role"] == "test"}
        query = {p for p in with_test if coh.participants[p]["fold"] == sf or coh.participants[p].get("test_only")}
        q_ids, want = {ids[p] for p in query}, {ids[p] for p in with_test if ids[p] in test_ids}
        if q_ids != want or q_ids & train_ids:
            raise ValueError(f"TickBatcher: the fold-derived query participants differ from manifest cell {ds} sf{sf} cf{cf}'s test side "
                             f"(not in the cell's test / test_only: {sorted(q_ids - want)[:5]}; cell test participants not queried: "
                             f"{sorted(want - q_ids)[:5]}; training participants among the queries: {sorted(q_ids & train_ids)[:5]})")
        self.query_p = sorted(query)
        # coverage of the cell's test side (for the unit record; ev1 can only query participants with test segments in the view)
        self.query_coverage = {"cell_test_participants": len(test_ids), "queried": len(q_ids),
                               "cell_test_not_queried": sorted(test_ids - q_ids)}
        self.train_p = tp
        self.fit = [i for i, s in enumerate(segs) if s["p"] in tp and s["role"] == "fit" and s["kind"] == self.kind]
        self.es = [i for i, s in enumerate(segs) if s["p"] in tp and s["role"] == "es" and s["kind"] == self.kind]
        self.audio_dim = self.S.shape[0] * C.N_TGT
        self.e0 = np.array([s["e0"] for s in segs], dtype=np.int64)
        self.s0_true = np.array([s["s0"] for s in segs], dtype=np.int64)
        self.s0_ign = np.array([-1 if s.get("s0_ign") is None else s["s0_ign"] for s in segs], dtype=np.int64)
        self.s0_train = self.s0_true
        self.fam = np.array([s["family"] for s in segs], dtype=np.int64)
        self.pres = np.array([s["presentation"] for s in segs], dtype=np.int64)
        self.fs0 = np.array([s["fs0"] for s in segs], dtype=np.int64)
        self.key_true = self.key_train = C.pack_key(self.fam, self.pres, self.fs0)     # tick-0 key of each segment (record only)
        self.cell_split_hash, self.zero_shot = cell.get("split_hash"), train_p is not None and not tp

    def rows(self, batch, rng, anchors=C.N_ANCHORS, pairing="train", roll=False):
        """[e0, s0, keys] for 8 anchors per segment at ticks j = phi + 31 a (phi ~ U{0..30}); roll: the next segment's audio and
        keys at the same ticks (the A_LOCAL legal mismatch)."""
        if anchors != C.N_ANCHORS or pairing not in ("train", "true"):
            raise ValueError(f"TickBatcher.rows: anchors {anchors}, pairing {pairing!r}")
        phase = rng.integers(0, C.ANCHOR_STEP, size=len(batch))
        t = C.TICK_OFFS[phase[:, None] + C.ANCHOR_STEP * np.arange(anchors)[None]].reshape(-1).astype(np.int64)
        b = np.repeat(np.arange(len(batch)), anchors)
        bi = np.asarray(batch, dtype=np.int64)
        src = bi[np.roll(np.arange(len(batch)), 1) if roll else np.arange(len(batch))][b]
        e0 = self.e0[bi][b] + t
        s0 = self.s0_true[src] + t
        keys = C.pack_key(self.fam[src], self.pres[src], self.fs0[src] + t)
        return [torch.as_tensor(e0, device=self.dev), torch.as_tensor(s0, device=self.dev), torch.as_tensor(keys, device=self.dev)]

    def training_access(self, coh):
        """What ev1.evaluate_continuous would read from target training participants: participants, train_segs, es queries."""
        segs = coh.segments
        train_segs = [s for s in segs if s["p"] in self.train_p and s["role"] in ("fit", "es") and s["kind"] == self.kind]
        q_es = [s for s in segs if s["p"] in self.train_p and s["role"] == "es" and s["kind"] == self.kind]
        return {"train_participants": sorted(coh.participants[i]["id"] for i in self.train_p), "train_segs": len(train_segs),
                "es_queries": len(q_es), "fit_segments": len(self.fit), "es_segments": len(self.es)}


class TickReps(ev1.Reps):
    """ev1.Reps on the contract ticks: u / va of every tick i_0..i_249 of each segment (offs = TICK_OFFS)."""

    def __init__(self, enc, aud, bt, stride=None, chunk=2048):
        if stride is not None:
            raise ValueError("TickReps evaluates on the 250 contract ticks; a stride is not used")
        super().__init__(enc, aud, bt, stride=1, chunk=chunk)
        self.offs, self.stride = C.TICK_OFFS.astype(np.int64).copy(), None


# ---------------------------------------------------------------------------------------------------------- private 64 Hz input
def load_private64(kids=None):
    """data.load_private() (or the given children) plus x64 per child: private_to64 (reflect pad 75 -> 32/125 with h_aa -> LP20)
    then z64_per_child (per channel over the child's [32, 70) windows), in memory (§2.1)."""
    if kids is None:
        from auditory_alignment import data
        kids = data.load_private()
    for k in kids:
        x = np.asarray(k["x"])
        if x.ndim != 3 or x.shape[1:] != (len(C.PRIVATE_LAYOUT), C.PRIVATE_EPOCH) or len(x) != len(k["y"]):
            raise ValueError(f"load_private64: {k.get('id')}: epochs [n, {len(C.PRIVATE_LAYOUT)}, {C.PRIVATE_EPOCH}] expected, got {x.shape}")
        k["x64"] = C.z64_per_child(C.private_to64(x))
    return kids


class PrivateBatcher64(PrivateBatcher):
    """PrivateBatcher on the 64 Hz private input: window [32, 70) of x64 (§2.12 private path)."""

    def __init__(self, kids, spec, row, dev):
        _check_spec(spec)
        self.dev, self.kids = dev, kids
        lo, hi = C.PRIVATE_WIN
        self.W, self.lo, self.hi = [(0, hi - lo)], lo, hi
        self.train = [i for i, k in enumerate(kids) if k["fold"] != row["subject_fold"]]
        self.off = np.cumsum([0] + [len(k["y"]) for k in kids])
        X = []
        for k in kids:
            x = k.get("x64")
            if x is None or np.asarray(x).shape != (len(k["y"]), len(C.PRIVATE_LAYOUT), C.PRIVATE_N64):
                raise ValueError(f"PrivateBatcher64: {k.get('id')}: x64 [n, 20, 90] from load_private64() expected")
            X.append(np.asarray(x)[:, :, lo:hi])
        self.Xall = torch.from_numpy(np.concatenate(X).astype(np.float16)).to(dev)
        yall = np.concatenate([k["y"] for k in kids])
        self.wrong = spec.get("pairing") == "declared_wrong_pair"      # refused by _check_spec; kept for the base semantics
        self.yall = torch.as_tensor(yall, device=dev)
        self.ytrue = torch.as_tensor(np.concatenate([k["y"] for k in kids]), device=dev)
        self.fit_idx = {i: self.off[i] + np.flatnonzero(~kids[i]["es_mask"]) for i in self.train}
        self.es_idx = {i: self.off[i] + np.flatnonzero(kids[i]["es_mask"]) for i in self.train}
        self.input = PRIVATE_INPUT
