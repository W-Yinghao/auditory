"""M2d tests: the rich-target builder C7 (auditory_alignment_v3/prior33/build_rich.py; PUBLIC_PRIOR_DESIGN.md §2.15, §3.2, §6.2 C7,
§7.1 items 8 and 12) on synthetic data only: the shared fixture's C4 / C5 tables (fixtures.make_synthetic_manifest) plus synthetic
waveforms, log-mel files written the way their producers write them, producer records, an inventory and a C3 scan written to tmp,
and a stand-in log-mel extractor (no transformers).

Covered: rich_f32.npy aligned row for row with every cohort's env_f32.npy and recomputed independently from the synthetic
waveforms; the time base (planted spectral events land on their 64 Hz samples, planted clock offsets are measured with their sign);
features shorter than the stream (NaN tail from n64 - 41); missing-target masks (Federici, competing-talker and non-target streams,
rejected waveforms incl. a non-.npy archive member, a missing file, failed clock checks, the length rule, failed identity checks)
as NaN rows with the right reasons and source hashes, never zeros; the .npz.gz reader (gzip + allow_pickle=False, pickle never
called, malformed members and oversized archives rejected); the Whisper stitching of prep_targets.run_dtu_audio with every frame
written, and the repair of producer arrays (unwritten final frames recomputed, never-written trailing frames dropped); the PCA-4
basis against an independent weighted PCA over C6's core-pool windows (C3's shared-audio mask applied), sigma equal to the fixture
rule, the C3 pointer rules and the production wait for C3, determinism and resumption (byte-identical outputs), stored projections
never regenerated; the restricted-participant guard (an open-file audit hook during the build, check_path patterns and registered
trees, runs.json roles), the output-location guard and the one-build-per-root lock. CPU only; about 60-90 s and 300 MB in tmp."""
import collections
import gzip
import hashlib
import io
import json
import os
import pickle
import sys
import zipfile

import numpy as np
import pytest
from scipy import signal
from scipy.io import wavfile

from auditory_alignment_v3.prior33 import build_rich as B
from auditory_alignment_v3.prior33 import contract as C

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures as FX  # noqa: E402

# ---------------------------------------------------------------------------------------------------------- open-file audit hook
_OPENS = {"on": False, "log": []}


def _hook(event, args):
    if _OPENS["on"] and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENS["log"].append(os.fsdecode(args[0]))


sys.addaudithook(_hook)        # process-wide and permanent, inert unless _OPENS["on"]


class _Record:
    def __enter__(self):
        _OPENS["log"] = []
        _OPENS["on"] = True
        return _OPENS["log"]

    def __exit__(self, *exc):
        _OPENS["on"] = False


# ---------------------------------------------------------------------------------------------------------- synthetic sources
class FakeLogmel:
    """Stand-in for WhisperFeatureExtractor + stitching with Whisper's frame clock: Hann-400 / hop-160 frames centred at sample 160 j,
    ceil(n / 160) frames, power pooled into 128 linear bands, log10, Whisper's max - 8 clamp and (x + 4) / 4. frames(x, idx) gives the
    same values at frames idx (the production extractor computes them on the windows that keep them)."""
    info = {"name": "fake_stft_logmel128_v1", "class": "tests.FakeLogmel", "note": "synthetic stand-in, no transformers"}

    def __init__(self):
        self.calls, self.frame_calls = 0, 0

    @staticmethod
    def compute(x16):
        x = np.asarray(x16, dtype=np.float64)
        n100 = -(-len(x) // 160)
        xp = np.pad(x, (200, 400))
        P = np.abs(np.fft.rfft(xp[160 * np.arange(n100)[:, None] + np.arange(400)[None]] * np.hanning(400), axis=1)) ** 2
        edges = np.linspace(0, 201, 129).astype(int)
        Bm = np.zeros((201, 128))
        for b in range(128):
            Bm[edges[b]:max(edges[b + 1], edges[b] + 1), b] = 1.0
        m = np.log10(P @ Bm + 1e-10)
        return ((np.maximum(m, m.max() - 8.0) + 4.0) / 4.0).T.astype(np.float32)

    def __call__(self, x16):
        self.calls += 1
        return self.compute(x16)

    def frames(self, x16, idx):
        self.frame_calls += 1
        return self.compute(x16)[:, np.asarray(idx, dtype=np.int64)]


def _producer_written(n):
    """Independent copy of prep_targets.run_dtu_audio's stitching arithmetic (features.run_whisper's is the same): the producer's
    frame count and which frames its loop writes."""
    from auditory_c3.features import _windows
    n100 = int(np.ceil(n / 16000 * 100))
    w = np.zeros(n100, bool)
    for s, e, lo, hi in _windows(n):
        a, b, A = int(round((lo - s) / 160)), int(round((hi - s) / 160)), int(round(lo / 160))
        b = min(b, a + n100 - A)
        w[A:A + (b - a)] = True
    return n100, w


def _as_producer(full, n):
    """The array a producer stores for the waveform whose every frame is `full` [128, ceil(n / 160)]: its own frame count, the
    frames its loop writes, zeros elsewhere."""
    n100p, w = _producer_written(n)
    out = np.zeros((128, n100p), full.dtype)
    idx = np.flatnonzero(w)
    out[:, idx] = full[:, idx]
    return out


TONES = (700.0, 2300.0, 5100.0)
SK_DELAY = {"podcast_1": 1, "podcast_2": 3}              # planted clock offsets (64 Hz samples): lag 1 passes, lag 3 is masked
SK_BURSTS = {"audiobook_13_1": (7.0, 19.5, 31.25)}       # planted spectral events (s): the 5100 Hz weight x 8 for 1 s
SK_OBJECT, SK_MISSING, SK_STIMFILE = "audiobook_2_1", "podcast_24", "podcast_16"
SK_STEREO48 = "audiobook_1_artefact"                     # int16 stereo at 48 kHz (other SparrKULee streams: float32 mono 16 kHz)
SK_SHORT, SK_LENTOL, SK_BYTES = "audiobook_15_1", "audiobook_15_2", "audiobook_15_3"   # extra C4 streams appended to the tables
SK_EXTRA_CUT = {SK_SHORT: 32, SK_LENTOL: 128, SK_BYTES: 0}   # waveform shorter than T by this many 64 Hz samples
FAU_BAD, DTU_HI_ONLY, DTU_BADSHA = "124", "t06", "t08"
FAU_N16 = {"111": 255880, "112": 256160}                 # n mod 160 = 40 (last frame unwritten); 160 x 1601 (float n100 = 1602)
DTU_N16 = {"t01": 319880, "t02": 320160, "t07": 319960}  # mod 40 (unwritten); 160 x 2001 (float n100 = 2002); mod 120 (none)


def _wave(raw, fs_env, fs_w, seed, delay64=0, bursts=(), n=None):
    """A waveform whose |hilbert| follows the source envelope `raw` (at fs_env): three tones with slowly varying weights, the
    carrier normalised to constant power, so the weights (and a planted burst: the 5100 Hz weight x 8 for 1 s) change the spectrum
    but not the envelope. n: the number of samples (default: the envelope's duration)."""
    n = int(round(len(raw) / fs_env * fs_w)) if n is None else int(n)
    t = np.arange(n) / fs_w
    a = np.interp(t, np.arange(len(raw)) / fs_env, raw)
    rng = np.random.default_rng(seed)
    w = [1.0 + 0.6 * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) for f in (0.21, 0.37, 0.53)]
    for t0 in bursts:
        w[2][(t >= t0) & (t < t0 + 1.0)] *= 8.0
    car = sum(wi * np.sin(2 * np.pi * f * t) for wi, f in zip(w, TONES)) / np.sqrt(0.5 * sum(wi ** 2 for wi in w))
    x = 0.1 * a * car
    if delay64:
        d = int(round(delay64 * fs_w / C.FS))
        x = np.r_[np.zeros(d), x[:-d]]
    return x


def _npz_gz(path, **arrays):
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    with gzip.open(path, "wb", compresslevel=1) as f:
        f.write(buf.getvalue())


def _zip_gz(members):
    """A gzipped zip archive with the given raw members {name: bytes} (to build malformed .npz files)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return gzip.compress(buf.getvalue())


def _x16_of(x, fs):
    from fractions import Fraction
    fr = Fraction(16000, fs)
    y = x if fr == 1 else signal.resample_poly(x, fr.numerator, fr.denominator)
    return np.asarray(y, dtype=np.float64).astype(np.float32)


def _n44_for(n16k):
    n44 = (441 * n16k) // 160
    assert -(-n44 * 160 // 441) == n16k
    return n44


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_scan(d, world_or_tables, fx=None, ok=True, complete=True, status="ok", ptr_sha=None, schema=B.SCAN_SCHEMA,
               cohorts=B.COHORTS, extra_rows=(), pointer=True):
    """A synthetic C3 result at d/scan_audio.json (+ the pointer): shared_audio['sparrkulee'] from the fixture's manifest
    shared_audio, mapped presentation -> stream name (the scan_audio.py schema)."""
    tables = world_or_tables["tables"] if isinstance(world_or_tables, dict) else world_or_tables
    fx = fx or world_or_tables["fx"]
    m, names = fx["manifest"], {s["stream"]: s["name"] for s in _json(os.path.join(tables, "sparrkulee", "streams.json"))["streams"]}
    rows = [{"stream": names[m["presentations"][sh["presentation"]]["stream"]], "span": list(sh["span"]),
             "span_s": [sh["span"][0] / 64, sh["span"][1] / 64], "partners": []} for sh in m["shared_audio"] if sh["cohort"] == "sparrkulee"]
    rows += list(extra_rows)
    doc = {"schema": schema, "ok": ok, "complete": complete, "cohorts_scanned": list(cohorts), "created_utc": "synthetic",
           "builder": {"sha256": "synthetic"}, "shared_audio": {"sparrkulee": rows},
           "shared_audio_seconds": {"sparrkulee": {"masked_s": sum(r["span"][1] - r["span"][0] for r in rows) / 64}}}
    os.makedirs(d, exist_ok=True)
    raw = json.dumps(doc, sort_keys=True).encode()
    with open(os.path.join(d, B.SCAN), "wb") as f:
        f.write(raw)
    if pointer:
        ptr = {"schema": B.SCAN_PTR_SCHEMA, "status": status, "file": B.SCAN, "sha256": ptr_sha or hashlib.sha256(raw).hexdigest(),
               "created_utc": "synthetic"}
        with open(os.path.join(d, B.SCAN_PTR), "w") as f:
            json.dump(ptr, f, sort_keys=True)
    return os.path.join(d, B.SCAN)


def _append_sk_streams(tables, wav16, sk_src):
    """Extra C4 SparrKULee streams (no runs, so in no pool): features shorter than T, a length-rule rejection and an archive whose
    audio member is not a .npy array."""
    d = os.path.join(tables, "sparrkulee")
    doc, env = _json(os.path.join(d, "streams.json")), np.load(os.path.join(d, "env_f32.npy"), allow_pickle=False)
    rng, parts, off = np.random.default_rng(77), [env], len(env)
    for k, name in enumerate((SK_SHORT, SK_LENTOL, SK_BYTES)):
        raw = FX._raw_env(rng, 2880, 64)
        en = C.rms_norm(C.band(raw, C.env_sos()[0])).astype(np.float32)
        doc["streams"].append({"stream": len(doc["streams"]), "name": name, "kind": "attended", "offset": off, "length": len(en),
                               "family": None, "family_offset": None, "rms": 1.0})
        parts.append(en)
        off += len(en)
        p = os.path.join(sk_src, "stimuli", "eeg", f"{name}.npz.gz")
        if name == SK_BYTES:
            with open(p, "wb") as f:
                f.write(_zip_gz({"audio.npy": b"plain text, not a .npy array", "fs.npy": FX.npy_bytes(np.int64(16000))}))
            continue
        x = _wave(raw, 64, 16000, seed=500 + k, n=(len(raw) - SK_EXTRA_CUT[name]) * 250).astype(np.float32)
        _npz_gz(p, audio=x, fs=np.int64(16000))
        wav16[("sparrkulee", name)] = x
    np.save(os.path.join(d, "env_f32.npy"), np.concatenate(parts))
    with open(os.path.join(d, "streams.json"), "w") as f:
        json.dump(doc, f, sort_keys=True)


def make_world(root):
    """Fixture tables + synthetic sources under `root` -> dict (tables, sources, expectations, per-stream waveforms)."""
    import h5py
    from auditory_c3.features_dtu import _mono16k
    tables, src = os.path.join(root, "tables"), os.path.join(root, "src")
    fx = FX.make_synthetic_manifest(tables)
    fake = FakeLogmel()
    wav16 = {}                                                       # (cohort, name) -> the 16 kHz float32 waveform
    # SparrKULee: stimuli/eeg/<stim>.npz.gz, decoys that must never be opened, and C1's runs_table.json
    sk_src = os.path.join(src, "sparrkulee_synth")
    eeg = os.path.join(sk_src, "stimuli", "eeg")
    os.makedirs(eeg)
    for i, s in enumerate(fx["sources"]["sparrkulee"]):
        name = s["name"]
        if name == SK_MISSING:
            continue
        p = os.path.join(eeg, f"{name}.npz.gz")
        if name == SK_OBJECT:                                       # an object member: rejected without unpickling
            _npz_gz(p, audio=np.array([np.zeros(4), "x"], dtype=object), fs=np.int64(16000))
            continue
        fs_w = 48000 if name == SK_STEREO48 else 16000
        x = _wave(s["env"], 64, fs_w, seed=100 + i, delay64=SK_DELAY.get(name, 0), bursts=SK_BURSTS.get(name, ()))
        if name == SK_STEREO48:
            ch0 = np.clip(np.round(x * 0.3 * 32767), -32768, 32767).astype(np.int16)
            a = np.stack([ch0, (0.8 * ch0).astype(np.int16)], axis=1)
            mono = a.astype(np.float64).mean(1) / 32768.0
        else:
            a = x.astype(np.float32)
            mono = a.astype(np.float64)
        _npz_gz(p, audio=a, fs=np.int64(fs_w))
        wav16[("sparrkulee", name)] = _x16_of(mono, fs_w)
    for decoy in ("noise_podcast_1.npz.gz", "t_podcast_1.npz.gz"):
        _npz_gz(os.path.join(eeg, decoy), audio=np.array([None], dtype=object), fs=np.int64(1))
    os.makedirs(os.path.join(sk_src, "sub-019", "ses-x", "eeg"))
    np.save(os.path.join(sk_src, "sub-019", "ses-x", "eeg", "sub-019_ses-x_task-listeningActive_run-01_eeg.npy"), np.zeros(4))
    os.makedirs(os.path.join(sk_src, "code"))
    with open(os.path.join(sk_src, "code", "evil.py"), "w") as f:
        f.write(f"open({os.path.join(root, 'EXECUTED')!r}, 'w').write('dataset code ran')\n")
    runs = _json(os.path.join(tables, "sparrkulee", "runs.json"))["runs"]
    rt = {"runs": [{"run_id": r["run_id"], "sub": r["sub"], "stimulus": r["stimulus"], "restricted": r["role"] == "restricted",
                    "events": None if r["role"] == "restricted" else
                    {"stim_file": f"eeg/{r['stimulus']}{'_v2' if r['stimulus'] == SK_STIMFILE else ''}.npz.gz"}} for r in runs]}
    with open(os.path.join(tables, "sparrkulee", "runs_table.json"), "w") as f:
        json.dump(rt, f, sort_keys=True)
    _append_sk_streams(tables, wav16, sk_src)
    # FAU: S<code>.wav (48 kHz stereo int32, the talker on one channel) and whisper_logmel128.h5 as features.run_whisper writes it
    fau_dir = os.path.join(src, "fau")
    stim = os.path.join(fau_dir, "stimuli")
    os.makedirs(stim)
    h5p = os.path.join(fau_dir, "whisper_logmel128.h5")
    with h5py.File(h5p, "w") as f5:
        f5.attrs.update(model="openai/whisper-large-v3", revision="06f233fe06e710322aca913c1bc4249a0d71fce1", note="synthetic")
        for i, s in enumerate(fx["sources"]["fau"]):
            code, stream = s["name"].split("/")
            if stream != "attended":
                continue
            x = _wave(s["env"], 128, 48000, seed=200 + i, n=3 * FAU_N16[code] if code in FAU_N16 else None)
            att = np.clip(np.round(x * 0.3 * 2 ** 31), -2 ** 31, 2 ** 31 - 1).astype(np.int32)
            side = i % 2
            st = np.zeros((len(att), 2), np.int32)
            st[:, side] = att
            x16 = _x16_of(att.astype(np.float64) / 2 ** 31, 48000)
            g = f5.create_group(f"{code}/attended")
            g.attrs.update(silent=False, wav_sha256=hashlib.sha256(att.tobytes()).hexdigest(), n_samples_16k=len(x16),
                           seconds=len(x16) / 16000, frame_rate_hz=100.0)
            g.create_dataset("logmel", data=_as_producer(fake.compute(x16).astype(np.float16), len(x16)))
            f5.create_group(f"{code}/distractor").attrs.update(silent=True, wav_sha256=hashlib.sha256(st[:, 1 - side].copy().tobytes()).hexdigest())
            if code == FAU_BAD:                                     # the stored channel differs by one LSB: identity check fails
                st[1000, side] += 1
            wavfile.write(os.path.join(stim, f"S{code}.wav"), 48000, st)
            wav16[("fau", s["name"])] = x16
    with open(f"{h5p}.done.json", "w") as f:
        json.dump({"model": "openai/whisper-large-v3", "revision": "06f233fe06e710322aca913c1bc4249a0d71fce1", "torch": "synthetic",
                   "sha256": _sha_file(h5p), "bytes": os.path.getsize(h5p)}, f)
    # DTU: NH originals (44.1 kHz stereo int16), inventory.json, audio_local.h5 as prep_targets.run_dtu_audio writes it; streams.json
    # keys = the mono int16 sha (C5)
    dtu_dir = os.path.join(src, "dtu")
    os.makedirs(os.path.join(dtu_dir, "stimuli"))
    shas, inv = {}, []
    for i, s in enumerate(fx["sources"]["dtu"]):
        if s["name"].startswith("m"):
            continue
        x = _wave(s["env"], 128, 44100, seed=300 + i, n=_n44_for(DTU_N16[s["name"]]) if s["name"] in DTU_N16 else None)
        ch0 = np.clip(np.round(x * 0.3 * 32767), -32768, 32767).astype(np.int16)
        p = os.path.join(dtu_dir, "stimuli", f"{s['name']}.wav")
        wavfile.write(p, 44100, np.stack([ch0, (0.9 * ch0).astype(np.int16)], axis=1))
        x16, h = _mono16k(p)
        shas[s["name"]], wav16[("dtu", s["name"])] = h, x16
    dtu_h5 = os.path.join(dtu_dir, "audio_local.h5")
    with h5py.File(dtu_h5, "w") as f5:
        for name, h in shas.items():
            x16 = wav16[("dtu", name)]
            f5.create_dataset(f"{h}/logmel", data=_as_producer(fake.compute(x16), len(x16)))
            f5.create_dataset(f"{h}/env", data=np.zeros(4, np.float32))
    with open(f"{dtu_h5}.done.json", "w") as f:
        json.dump({"n": len(shas), "sha256": _sha_file(dtu_h5)}, f)
    for k, (name, h) in enumerate(sorted(shas.items())):
        path = os.path.join(dtu_dir, "stimuli", f"{'t03' if name == DTU_BADSHA else name}.wav")   # t08's row points to t03's file
        inv.append({"file": f"sub-0{21 + k}", "trial": "trial_001", "kind": "target", "path": path, "offset_s": 0.0,
                    "hi": name == DTU_HI_ONLY, "sha": h})
    inv.append({"file": "sub-021", "trial": "trial_009", "kind": "masker", "path": os.path.join(dtu_dir, "stimuli", "m01.wav"),
                "offset_s": 3.25, "hi": False, "sha": "f" * 64})
    with open(os.path.join(dtu_dir, "inventory.json"), "w") as f:
        json.dump(inv, f)
    sj = os.path.join(tables, "dtu", "streams.json")
    doc = _json(sj)
    for r in doc["streams"]:
        r["key"] = shas.get(r["name"], r["name"])
    with open(sj, "w") as f:
        json.dump(doc, f, sort_keys=True)
    write_scan(tables, tables, fx)                                  # C3's result at the table root (the production location)
    sources = B.Sources(sparrkulee=sk_src, fau_stimuli=stim, fau_logmel=h5p, dtu_inventory=os.path.join(dtu_dir, "inventory.json"),
                        dtu_audio=dtu_h5)
    fake.calls = 0
    return {"root": root, "tables": tables, "src": src, "sources": sources, "fx": fx, "fake": fake, "wav16": wav16, "shas": shas}


EXPECT = {
    "sparrkulee": {"podcast_2": "clock_lag", SK_OBJECT: "waveform_unavailable", SK_MISSING: "no_waveform",
                   SK_STIMFILE: "waveform_unavailable", SK_LENTOL: "waveform_unavailable", SK_BYTES: "waveform_unavailable"},
    "fau": {f"{FAU_BAD}/attended": "waveform_unavailable", "215/attended": "no_waveform_competing_talker",
            "227/attended": "no_waveform_competing_talker", **{f"{c}/distractor": "not_a_target_stream" for c in ("215", "227")}},
    "dtu": {DTU_HI_ONLY: "not_nh_original", DTU_BADSHA: "waveform_unavailable", "m01": "not_a_target_stream",
            "m02": "not_a_target_stream"},
}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    w = make_world(str(tmp_path_factory.mktemp("c7")))
    guarded, real_check = [], B.check_path

    def spy(path):
        guarded.append(os.fspath(path))
        return real_check(path)
    B.check_path = spy
    try:
        with _Record() as opened:
            w["meta"] = B.build(os.path.join(w["root"], "out"), tables=w["tables"], sources=w["sources"], logmel_fn=w["fake"],
                                log=lambda m: None)
    finally:
        B.check_path = real_check
    w.update(out=os.path.join(w["root"], "out"), opened=list(opened), guarded=guarded, calls=w["fake"].calls,
             frame_calls=w["fake"].frame_calls)
    return w


def _doc(w, c, out=None):
    with open(os.path.join(out or w["out"], c, B.RICH_STREAMS)) as f:
        return json.load(f)


def _rich(w, c, out=None):
    return np.load(os.path.join(out or w["out"], c, B.RICH), allow_pickle=False)


def _json(path):
    with open(path) as f:
        return json.load(f)


def _streams(w, c):
    return _json(os.path.join(w["tables"], c, "streams.json"))["streams"]


def _env(w, c):
    return np.load(os.path.join(w["tables"], c, "env_f32.npy"), allow_pickle=False)


# ---------------------------------------------------------------------------------------------------------- alignment and masks
def test_rich_rows_aligned_with_envelope_streams(world):
    for c in B.COHORTS:
        R, env, st, doc = _rich(world, c), _env(world, c), _streams(world, c), _doc(world, c)
        assert R.dtype == np.float32 and R.shape == (len(env), len(C.RICH_COLS)) and doc["columns"] == list(C.RICH_COLS)
        rows = doc["streams"]
        assert [r["stream"] for r in rows] == list(range(len(st))) and [r["name"] for r in rows] == [s["name"] for s in st]
        assert [r["length"] for r in rows] == [s["length"] for s in st]
        for s, r in zip(st, rows):
            blk = R[s["offset"]:s["offset"] + s["length"]]
            if r["available"]:
                ve = s["length"] if r["n_64"] >= s["length"] else r["n_64"] - C.ENV_EDGE          # NaN guard from the features' end
                assert r["valid_end"] == ve and np.isfinite(blk[:ve]).all() and np.isnan(blk[ve:]).all()
                if ve == s["length"]:
                    np.testing.assert_allclose(np.sqrt(np.mean(blk.astype(np.float64) ** 2, axis=0)), 1.0, atol=1e-6)   # RMS 1 per dim
            else:
                assert r["valid_end"] == 0 and np.isnan(blk).all()            # masked: NaN, never zero-filled
        assert doc["summary"]["finite_rows"] == sum(r["valid_end"] for r in rows)
    short = {r["name"]: r for r in _doc(world, "sparrkulee")["streams"]}[SK_SHORT]   # features end 32 samples before T
    assert short["available"] and short["n_64"] == 2880 - 32 and short["valid_end"] == 2880 - 32 - C.ENV_EDGE


def test_masks_reasons_and_source_hashes(world):
    for c in B.COHORTS:
        doc = _doc(world, c)
        rows = {r["name"]: r for r in doc["streams"]}
        want = {n: EXPECT.get(c, {}).get(n) for n in rows} if c != "federici" else {n: "no_waveform" for n in rows}
        assert {n: r["reason"] for n, r in rows.items()} == want
        assert doc["no_source_reasons"] == list(B.NO_SOURCE) and doc["read_masked_reasons"] == list(B.READ_MASKED)
        assert set(doc["reasons"]) == set(B.REASONS) and set(FX.NO_SOURCE) <= set(B.NO_SOURCE)   # the fixture's are a subset
        for n, r in rows.items():
            assert r["available"] == (r["reason"] is None)
            assert (r["source_sha256"] is None) == (r["reason"] in B.NO_SOURCE)
            assert r["available"] or r["reason"] in B.NO_SOURCE + B.READ_MASKED
            if r["source_sha256"] is not None:                                  # the waveform file's bytes, as read
                with open(r["source"], "rb") as f:
                    assert hashlib.sha256(f.read()).hexdigest() == r["source_sha256"]
            assert (r["extractor"] is not None) == (r["reason"] in (None, "clock_lag"))
    sk = {r["name"]: r for r in _doc(world, "sparrkulee")["streams"]}
    assert sk["podcast_1"]["available"] and sk["podcast_1"]["clock_lag"] == 1                  # within 0 +- 1: kept, never shifted
    assert sk["podcast_2"]["clock_lag"] == 3 and sk["podcast_2"]["clock"]["measurable"] and not sk["podcast_2"]["clock"]["ok"]
    assert "pickle" in sk[SK_OBJECT]["detail"] or "Object" in sk[SK_OBJECT]["detail"]
    assert "not a .npy array" in sk[SK_BYTES]["detail"] and sk[SK_BYTES]["clock"] is None      # masked, the build went on
    assert "LEN_TOL" in sk[SK_LENTOL]["detail"] and sk[SK_LENTOL]["clock"]["ok"] and sk[SK_LENTOL]["n_64"] is None
    assert sk[SK_LENTOL]["n_64_expected"] == 2880 - 128 and sk[SK_LENTOL]["feature_source"] is None
    assert "stim_file" in sk[SK_STIMFILE]["detail"] and sk["podcast_1"]["stim_file_check"] == "ok"
    assert all(r["clock_lag"] == 0 for n, r in sk.items() if r["available"] and n not in SK_DELAY)
    lc = sk["podcast_1"]["listening_conditions"]                       # from runs.json, restricted runs left out
    assert lc and all(x["role"] == "fit" for x in lc) and sum(x["n_runs"] for x in lc) == 4
    assert sk["podcast_1"]["final_frame"]["computed_by"].startswith("C7") and sk["podcast_1"]["final_frame"]["producer_unwritten"] == []
    fau = {r["name"]: r for r in _doc(world, "fau")["streams"]}
    assert "channels match" in fau[f"{FAU_BAD}/attended"]["detail"]
    assert fau["111/attended"]["audio_sha256"] == fau["111/attended"]["feature_source"]["attrs"]["wav_sha256"]
    assert fau["111/attended"]["final_frame"]["filled"] == [1599] and fau["111/attended"]["final_frame"]["stored_dtype"] == "float16"
    assert fau["112/attended"]["final_frame"]["dropped"] == [1601] and fau["112/attended"]["n_mel_100"] == 1601
    assert fau["113/attended"]["final_frame"]["producer_unwritten"] == [] and "recomputed" not in fau["113/attended"]["extractor"]
    assert "recomputed by C7" in fau["111/attended"]["extractor"] and "transformers version not recorded" in fau["111/attended"]["extractor"]
    fs_ = fau["111/attended"]["feature_source"]
    assert fs_["producer_record"]["sha256_matches_file"] and fs_["producer_record"]["content"]["torch"] == "synthetic"
    assert fau["111/attended"]["n_samples"] == 3 * 255880 and fau["111/attended"]["n_channels"] == 2
    dtu = {r["name"]: r for r in _doc(world, "dtu")["streams"]}
    assert "stream key" in dtu[DTU_BADSHA]["detail"] and dtu["t01"]["audio_sha256"] == world["shas"]["t01"] == dtu["t01"]["key"]
    assert dtu["t01"]["final_frame"]["filled"] == [1999] and dtu["t02"]["final_frame"]["dropped"] == [2001]
    assert dtu["t07"]["final_frame"]["producer_unwritten"] == [] and dtu["t01"]["n_samples"] == _n44_for(319880)
    assert dtu["t01"]["feature_source"]["extractor_version"].startswith("not recorded by the producer")
    assert "extractor version not recorded by the producer" in dtu["t01"]["extractor"]
    assert dtu["t01"]["feature_source"]["producer_record"]["content"]["n"] == len(world["shas"])
    assert dtu["t01"]["feature_source"]["producer_record"]["sha256_matches_file"] and dtu["t01"]["n_channels"] == 2
    assert _doc(world, "dtu")["summary"]["n_frames_recomputed"] == 1 and _doc(world, "dtu")["summary"]["n_frames_dropped"] == 1
    meta = world["meta"]
    assert {c: sorted(m["name"] for m in v["masked"]) for c, v in meta["cohorts"].items()} == \
        {c: sorted(n for n, r in ({r["name"]: r for r in _doc(world, c)["streams"]}).items() if not r["available"]) for c in B.COHORTS}
    assert not any(v["stale"] or v["partial"] for v in meta["cohorts"].values()) and meta["partial"] is False
    assert all(r["pca4_sha256"] == meta["pca"]["sha256"] for c in B.COHORTS for r in _doc(world, c)["streams"] if r["available"])
    ec = meta["extractor_check"]                                  # the stored log-mel recomputed with the SparrKULee extractor
    assert ec["dtu"]["max_abs_diff"] == 0.0 and ec["dtu"]["consistent"] and ec["dtu"]["stream"] == "t01"
    assert ec["dtu"]["frames_not_compared"] == [1999] and ec["dtu"]["n_frames_compared"] == 1999
    assert 0.0 < ec["fau"]["max_abs_diff"] <= 1e-3 and ec["fau"]["consistent"]                 # FAU is stored as float16
    assert world["frame_calls"] == 2                               # one recomputation each for FAU 111 and DTU t01


def _independent_rows(world, c, name, keep_producer_zero=False):
    """The documented chain recomputed from the synthetic waveform with scipy directly (not build_rich)."""
    meta, rows = world["meta"], {r["name"]: r for r in _doc(world, c)["streams"]}
    V = np.load(os.path.join(world["out"], B.PCA_FILE), allow_pickle=False)
    mu = np.asarray(meta["pca"]["mean"])
    x16 = world["wav16"][(c, name)]
    m100 = FakeLogmel.compute(x16).astype(np.float64)              # every frame, ceil(n / 160) of them
    if c == "fau":
        m100 = m100.astype(np.float16).astype(np.float64)                     # the stored FAU log-mel is float16
    if keep_producer_zero:                                                    # what the producer's array holds without the repair
        n100p, w = _producer_written(len(x16))
        m100 = m100.copy()
        m100[:, ~w[:m100.shape[1]]] = 0.0
    L = signal.resample_poly(m100.T, 16, 25, axis=0, window=C.aa_fir(100, 16))
    T = rows[name]["length"]
    L = L[:T]
    ss = (L - mu) @ V
    sc = np.r_[0.0, np.sqrt((np.diff(ss, axis=0) ** 2).sum(1))]
    sos = signal.butter(4, [2, 8], btype="band", fs=64, output="sos")
    F = signal.sosfiltfilt(sos, np.c_[ss, sc], axis=0, padtype="odd", padlen=min(128, len(L) - 1))
    return F / np.sqrt((F ** 2).mean(0)), rows[name]


def test_features_recomputed_independently(world):
    for c, name in (("sparrkulee", "podcast_1"), ("sparrkulee", SK_STEREO48), ("sparrkulee", "audiobook_11_1"),
                    ("sparrkulee", SK_SHORT), ("fau", "111/attended"), ("fau", "112/attended"), ("dtu", "t01"), ("dtu", "t02"),
                    ("dtu", "t07")):
        F, r = _independent_rows(world, c, name)
        st = {s["name"]: s for s in _streams(world, c)}[name]
        ve = r["valid_end"]
        got = _rich(world, c)[st["offset"]:st["offset"] + ve].astype(np.float64)
        assert r["available"] and len(F) == min(r["n_64"], st["length"]) and ve == (st["length"] if r["n_64"] >= st["length"] else len(F) - 41)
        np.testing.assert_allclose(got, F[:ve], rtol=0, atol=2e-5)
    for c, name in (("fau", "111/attended"), ("dtu", "t01")):     # the producer's zero frame would have changed the last rows
        Z, r = _independent_rows(world, c, name, keep_producer_zero=True)
        st = {s["name"]: s for s in _streams(world, c)}[name]
        got = _rich(world, c)[st["offset"]:st["offset"] + r["valid_end"]].astype(np.float64)
        d = np.abs(got - Z[:r["valid_end"]]).max(1)
        assert d[-100:].max() > 1e-3 and int(np.argmax(d)) >= len(d) - 100


def test_planted_spectral_events_land_on_their_samples(world):
    """Time base: rich row offset + t is 64 Hz sample t from the stream origin (as env_f32.npy): each planted 1 s burst puts a
    spectral-change peak on round(t0 * 64) and round((t0 + 1) * 64) within one sample."""
    name = "audiobook_13_1"
    st = {s["name"]: s for s in _streams(world, "sparrkulee")}[name]
    sc = _rich(world, "sparrkulee")[st["offset"]:st["offset"] + st["length"], 4].astype(np.float64)
    for t0 in SK_BURSTS[name]:
        for edge in (t0, t0 + 1.0):
            k = int(round(edge * C.FS))
            got = k - 16 + int(np.argmax(sc[k - 16:k + 17]))
            assert abs(got - k) <= 1, (edge, got, k)


def test_clock_check_measures_planted_lags():
    rng = np.random.default_rng(5)
    raw = np.abs(rng.standard_normal(4000))
    env = C.rms_norm(C.band(raw, C.env_sos()[0]))
    for d in (-5, -2, -1, 0, 1, 2, 7):
        ours = np.roll(env, d) if d else env.copy()
        r = B.clock_check(env, ours)
        assert r["tau"] == d and r["measurable"] and r["ok"] == (abs(d) <= 1) and r["r_peak"] > 0.99 and r["r_peak"] <= 1.0
    unrelated = C.rms_norm(C.band(np.abs(np.random.default_rng(6).standard_normal(4000)), C.env_sos()[0]))
    assert not B.clock_check(env, unrelated)["measurable"]                    # no peak: never passes
    taus = np.arange(-3, 4)
    a, b = rng.standard_normal(300), rng.standard_normal(310)
    ref = [np.corrcoef(a[max(0, -t):min(300, 310 - t)], b[max(0, -t) + t:min(300, 310 - t) + t])[0, 1] for t in taus]
    np.testing.assert_allclose(B.lagged_r(a, b, taus), ref, atol=1e-12)


# ---------------------------------------------------------------------------------------------------------- readers
class _FakeFE:
    """Returns, for each 30 s window, input_features whose frame f holds the window's sample 160 f (padding: -1)."""

    def __init__(self):
        self.windows = 0

    def __call__(self, x, sampling_rate, return_tensors):
        assert sampling_rate == 16000 and return_tensors == "np"
        self.windows += 1
        f = np.full((1, 128, 3000), -1.0, np.float32)
        idx = 160 * np.arange(3000)
        ok = idx < len(x)
        f[0, :, ok] = np.asarray(x)[idx[ok]][:, None]
        return type("Feat", (), {"input_features": f})()


def test_whisper_stitching_keeps_the_frame_clock():
    """Every frame of [0, ceil(n / 160)) is written with the frame clock j <-> j / 100 s, for lengths that are and are not multiples
    of 160 (the producers leave the last frame at 0 when n mod 160 is in 1..80, and their float frame count adds a never-written
    frame for n = 160 x 1601); stitched_frames gives the same values from only the windows that keep them."""
    lens = [int(5.0 * 16000), int(45.0 * 16000), int(70.0 * 16000), int(101.3 * 16000), 80040, 720081, 1120001, 1910432,
            160 * 1601, 1120, 480000, 480001, 1000080]
    for n in lens:
        x = (np.arange(n) / 16000).astype(np.float32)                       # sample value = its time
        m = B.stitched_logmel(x, _FakeFE())
        n100 = -(-n // 160)
        assert m.shape == (128, n100)
        assert np.array_equal(m[0], (160 * np.arange(n100) / 16000).astype(np.float32))   # j <-> j / 100 s, no gap, no overlap
        n100p, w = _producer_written(n)                                     # the producer's arithmetic, copied independently
        assert B.producer_n100(n) == n100p and B.producer_unwritten(n).tolist() == np.flatnonzero(~w).tolist()
        assert (n % 160 in range(1, 80)) <= bool((~w[:n100]).any())          # the reviewer's case: last frame unwritten
        idx = sorted({0, n100 - 1, n100 // 2})
        fe = _FakeFE()
        np.testing.assert_array_equal(B.stitched_frames(x, fe, idx), m[:, idx])
        assert fe.windows <= len(idx)
    assert B.producer_unwritten(1910432).tolist() == [11940] and B.producer_unwritten(160 * 1601).tolist() == [1601]
    assert B.producer_unwritten(1120).tolist() == [7] and B.producer_unwritten(720081).tolist() == []
    L = B.logmel64(np.tile(np.sin(2 * np.pi * 2.0 * np.arange(1000) / 100), (128, 1)))   # 2 Hz at 100 Hz -> the same at 64 Hz
    assert L.shape == (640, 128) and L.dtype == np.float32 and B.n64_of(1000) == 640       # sample i at time i / 64 s (a shift
    np.testing.assert_allclose(L[40:600, 0], np.sin(2 * np.pi * 2.0 * np.arange(40, 600) / 64), atol=3e-3)   # of one sample: 0.2)


def test_reused_logmel_repairs_only_unwritten_frames():
    rng = np.random.default_rng(3)
    calls = []

    def frames(x, idx):
        calls.append(list(idx))
        return np.full((128, len(idx)), 0.123456789, np.float32)
    for n, fill, drop in ((255880, [1599], []), (160 * 1601, [], [1601]), (256000, [], [])):
        full = rng.standard_normal((128, -(-n // 160))).astype(np.float16)
        st = _as_producer(full, n)
        out, rec = B.reused_logmel(st, np.zeros(n, np.float32), frames)
        assert out.dtype == np.float32 and out.shape == full.shape and rec["filled"] == fill and rec["dropped"] == drop
        keep = np.setdiff1d(np.arange(full.shape[1]), fill)
        np.testing.assert_array_equal(out[:, keep], full[:, keep].astype(np.float32))
        if fill:
            assert np.all(out[:, fill] == np.float32(np.float16(0.123456789)))   # the stored dtype's precision
    assert calls == [[1599]]                                                     # the extractor runs only for a fill
    st = _as_producer(rng.standard_normal((128, 1600)).astype(np.float32), 255880)
    st[5, 1599] = 0.5                                                            # a value where the producer never writes
    with pytest.raises(B.WaveformUnavailable, match="never writes"):
        B.reused_logmel(st, np.zeros(255880, np.float32), frames)
    with pytest.raises(B.WaveformUnavailable, match="expected"):
        B.reused_logmel(np.zeros((128, 1599), np.float32), np.zeros(255880, np.float32), frames)


def _gz_npz(**arrays):
    buf = io.BytesIO()
    np.savez(buf, **arrays)
    return gzip.compress(buf.getvalue())


class _Sentinel:
    """A pickle payload that would create PATH if it were ever unpickled."""
    PATH = None

    def __reduce__(self):
        return (open, (self.PATH, "w"))


def test_npz_reader_rejects_without_unpickling(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise AssertionError("pickle was called")
    monkeypatch.setattr(pickle, "load", boom)
    monkeypatch.setattr(pickle, "loads", boom)
    a, fs = B.read_npz_gz(_gz_npz(audio=np.ones(20000, np.float32), fs=np.int64(16000)))
    assert fs == 16000 and a.dtype == np.float32
    st = np.stack([np.full(32000, 16384, np.int16), np.zeros(32000, np.int16)], axis=1)
    a, fs = B.read_npz_gz(_gz_npz(audio=st, fs=np.int64(48000)))
    np.testing.assert_allclose(B._mono(a), 0.25)                            # int16 / 32768, channel mean
    np.testing.assert_allclose(B._mono(st.T.copy()), 0.25)                   # channels on the short axis, either order
    a, fs = B.read_npz_gz(_zip_gz({"audio": FX.npy_bytes(np.ones(100, np.float32)), "fs": FX.npy_bytes(np.int64(16000))}))
    assert fs == 16000 and a.shape == (100,)                                 # members without the .npy suffix: still .npy arrays
    _Sentinel.PATH = str(tmp_path / "UNPICKLED")
    npy_audio, npy_fs = FX.npy_bytes(np.zeros(100, np.float32)), FX.npy_bytes(np.int64(16000))
    cbuf = io.BytesIO()
    np.savez_compressed(cbuf, audio=np.zeros(100000, np.float32), fs=np.int64(16000))
    bad = {"object member": _gz_npz(audio=np.array([1, "x"], dtype=object), fs=np.int64(16000)),
           "structured": _gz_npz(audio=np.zeros(100, dtype=[("a", "f4"), ("b", "f4")]), fs=np.int64(16000)),
           "complex": _gz_npz(audio=np.zeros(100, np.complex64), fs=np.int64(16000)),
           "3-D": _gz_npz(audio=np.zeros((10, 10, 10), np.float32), fs=np.int64(16000)),
           "no fs": _gz_npz(audio=np.zeros(100, np.float32)),
           "extra member": _gz_npz(audio=np.zeros(100, np.float32), fs=np.int64(16000), meta=np.zeros(1)),
           "fs array": _gz_npz(audio=np.zeros(100, np.float32), fs=np.array([16000, 16000])),
           "fs fraction": _gz_npz(audio=np.zeros(100, np.float32), fs=np.float64(44100.5)),
           "fs low": _gz_npz(audio=np.zeros(100, np.float32), fs=np.int64(8000)),
           "nan": _gz_npz(audio=np.array([0.0, np.nan], np.float32), fs=np.int64(16000)),
           "many channels": _gz_npz(audio=np.zeros((100, 20), np.float32), fs=np.int64(16000)),
           "not gzip": b"PK\x03\x04 not gzip",
           "truncated gzip": _gz_npz(audio=np.zeros(100, np.float32), fs=np.int64(16000))[:-12],
           "pickled payload": gzip.compress(pickle.dumps({"audio": 1})),
           "single npy": gzip.compress(FX.npy_bytes(np.zeros(10))),
           # members without the .npy magic: numpy's NpzFile returns raw bytes (review problem 1)
           "audio.npy holds text": _zip_gz({"audio.npy": b"not an array", "fs.npy": npy_fs}),
           "audio.npy holds a pickle stream": _zip_gz({"audio.npy": pickle.dumps(_Sentinel()), "fs.npy": npy_fs}),
           "audio (no suffix) holds text": _zip_gz({"audio": b"not an array", "fs.npy": npy_fs}),
           "fs.npy holds text": _zip_gz({"audio.npy": npy_audio, "fs.npy": b"16000"}),
           "audio twice": _zip_gz({"audio": npy_audio, "audio.npy": npy_audio, "fs.npy": npy_fs})}
    for why, raw in bad.items():
        with pytest.raises(B.WaveformUnavailable):
            B.read_npz_gz(raw)
    assert not os.path.exists(_Sentinel.PATH)
    with pytest.raises(B.WaveformUnavailable, match="after gunzip"):              # size caps: the archive and each member
        B.read_npz_gz(_gz_npz(audio=np.ones(20000, np.float32), fs=np.int64(16000)), cap=1000)
    with pytest.raises(B.WaveformUnavailable, match="exceed"):
        B.read_npz_gz(gzip.compress(cbuf.getvalue()), cap=100000)


def test_mono16k_bytes_equals_features_dtu(tmp_path):
    from auditory_c3.features_dtu import _mono16k
    x = np.random.default_rng(1).integers(-20000, 20000, size=(44100 * 3, 2)).astype(np.int16)
    p = str(tmp_path / "a.wav")
    wavfile.write(p, 44100, x)
    x16, h = _mono16k(p)
    with open(p, "rb") as f:
        y16, g, info = B.mono16k_bytes(f.read())
    assert g == h and np.array_equal(x16, y16) and info == {"n_samples": 44100 * 3, "n_channels": 2}
    wavfile.write(p, 48000, x)
    with open(p, "rb") as f, pytest.raises(B.WaveformUnavailable):
        B.mono16k_bytes(f.read())


# ---------------------------------------------------------------------------------------------------------- PCA, sigma, C3 mask
def _pool_windows(world, stream_ok=None):
    """Independent fit windows: C6's SparrKULee core pool of the fixture manifest (role fit, >= 2 listeners, after the shared-audio
    mask), unique (stream, s + TICK_OFFS[k])."""
    m = world["fx"]["manifest"]
    S, pres = m["segments"]["sparrkulee"], m["presentations"]
    W = collections.defaultdict(set)
    for i in m["pools"]["core"]["sparrkulee"]:
        st = pres[S["presentation"][i]]["stream"]
        W[st].update(int(S["s"][i]) + int(o) for o in C.TICK_OFFS)
    return {st: np.array(sorted(v)) for st, v in W.items() if stream_ok is None or stream_ok(st)}


def _premask_windows(world):
    """Independent fit windows without C3's mask: C4 runs.json role fit, >= 2 distinct participants per (presentation, s)."""
    runs = _json(os.path.join(world["tables"], "sparrkulee", "runs.json"))["runs"]
    lis, sto = collections.defaultdict(set), {}
    for r in runs:
        if r["role"] == "fit" and r["row_offset"] is not None:
            sto[r["presentation"]] = r["stream"]
            for s in r["segment_starts"]:
                lis[(r["presentation"], s)].add(r["participant"])
    W = collections.defaultdict(set)
    for (p, s), subs in lis.items():
        if len(subs) >= 2:
            W[sto[p]].update(int(s) + int(o) for o in C.TICK_OFFS)
    return {st: np.array(sorted(v)) for st, v in W.items()}


def test_pca_basis_matches_an_independent_weighted_pca(world):
    st = _streams(world, "sparrkulee")
    rows = _doc(world, "sparrkulee")["streams"]
    W = _pool_windows(world, lambda k: rows[k]["available"])
    assert sorted(rows[k]["name"] for k in W) == sorted(world["meta"]["pca"]["fit_streams"]) == \
        ["audiobook_1_1", "audiobook_1_2", "audiobook_1_shifted", "podcast_1"]       # the masked podcast_2 is left out
    S0, S1, S2 = 0.0, np.zeros(128), np.zeros((128, 128))
    for k, w in W.items():
        L = signal.resample_poly(FakeLogmel.compute(world["wav16"][("sparrkulee", st[k]["name"])]).astype(np.float64).T, 16, 25, axis=0,
                                 window=C.aa_fir(100, 16))
        c = np.zeros(len(L))
        for j in range(C.N_TGT):
            np.add.at(c, w + j, 1.0)
        S0, S1, S2 = S0 + c.sum(), S1 + c @ L, S2 + (L * c[:, None]).T @ L
    mu = S1 / S0
    ev, vec = np.linalg.eigh(S2 / S0 - np.outer(mu, mu))
    V = vec[:, np.argsort(ev)[::-1][:4]]
    V = V * np.sign(V[np.argmax(np.abs(V), 0), np.arange(4)])
    got = np.load(os.path.join(world["out"], B.PCA_FILE), allow_pickle=False)
    assert got.dtype == np.float64 and got.shape == (128, 4)
    np.testing.assert_allclose(got, V, atol=1e-8)
    np.testing.assert_allclose(world["meta"]["pca"]["mean"], mu, atol=1e-10)
    np.testing.assert_allclose(got.T @ got, np.eye(4), atol=1e-12)
    assert (got[np.argmax(np.abs(got), 0), np.arange(4)] > 0).all()
    assert world["meta"]["pca"]["n_windows_kept"] == sum(len(w) for w in W.values()) == world["meta"]["manifest_rich"]["n_windows"]
    assert world["meta"]["manifest_rich"]["pca4"]["sha256"] == hashlib.sha256(got.tobytes()).hexdigest()
    fm = world["meta"]["fit_mask"]
    assert fm["applied"] and fm["rule"] == B.FIT_RULE == world["meta"]["manifest_rich"]["pca4"]["fit"]
    assert fm["sha256"] == _sha_file(os.path.join(world["tables"], B.SCAN)) and fm["n_segments_masked"] == 2   # podcast_1 / _2 at 128


def test_fit_windows_are_the_fixture_pool_after_the_shared_audio_mask(world):
    m = world["fx"]["manifest"]
    S, pool, pres = m["segments"]["sparrkulee"], m["pools"]["core"]["sparrkulee"], m["presentations"]
    fix = {(pres[S["presentation"][i]]["stream"], S["s"][i]) for i in pool}
    runs = _json(os.path.join(world["tables"], "sparrkulee", "runs.json"))["runs"]
    ours, _ = B.sk_fit_segments(runs)                                         # before the mask: a superset
    spans = collections.defaultdict(list)
    for sh in m["shared_audio"]:
        spans[pres[sh["presentation"]]["stream"]].append(sh["span"])
    hit = {(st, s) for st, s in ours if any(a < s + C.SPAN_EEG and s < b for a, b in spans[st])}
    assert fix <= set(ours) and set(ours) - fix == hit and hit                # C3's jingle mask is the only difference
    tab = B._Tables(world["tables"], "sparrkulee")
    shared = B._shared_by_stream(B.read_scan(os.path.join(world["tables"], B.SCAN))[0], tab)
    masked, stats = B.sk_fit_segments(runs, shared)
    assert set(masked) == fix and stats["n_segments_masked"] == len(hit) and stats["n_segments_before_mask"] == len(ours)
    W, stats = B.sk_fit_windows(runs, shared)
    assert stats["n_windows"] == sum(len(v) for v in W.values()) == sum(len(v) for v in _pool_windows(world).values())


def test_sigma_is_the_fixture_rule_over_the_core_pool(world):
    st, rows, R = _streams(world, "sparrkulee"), _doc(world, "sparrkulee")["streams"], _rich(world, "sparrkulee").astype(np.float64)
    Y = []
    for k, w in _pool_windows(world, lambda k: rows[k]["available"]).items():
        Y.append(R[st[k]["offset"] + w[:, None] + np.arange(8)])
    Y = np.concatenate(Y)                                                    # [n_windows, 8, 5]
    ss, sc = Y[..., :4].reshape(len(Y), 32), Y[..., 4]
    mr = world["meta"]["manifest_rich"]
    np.testing.assert_allclose(mr["sigma_ss"], np.sqrt((ss ** 2).mean(0)), rtol=1e-12)
    np.testing.assert_allclose(mr["sigma_sc"], np.sqrt((sc ** 2).mean(0)), rtol=1e-12)
    np.testing.assert_allclose(mr["mu_estimate_ss"], ss.mean(0), atol=1e-12)
    assert mr["n_windows"] == len(Y) and mr["loss_weights"] == [1.0, 0.5, 0.5] and mr["columns"] == list(C.RICH_COLS)
    assert set(mr) == set(world["fx"]["manifest"]["rich"]) and mr["y_layout"] == world["fx"]["manifest"]["rich"]["y_layout"]
    m = world["fx"]["manifest"]                                              # C6's recomputation on its pool agrees
    S, pres = m["segments"]["sparrkulee"], m["presentations"]
    Wf = B.segment_windows((pres[S["presentation"][i]]["stream"], S["s"][i]) for i in m["pools"]["core"]["sparrkulee"])
    f = B.rich_standardiser(_rich(world, "sparrkulee"), st, rows, Wf)
    assert f["n_windows"] + f["n_windows_missing"] == sum(len(v) for v in Wf.values()) and f["n_windows_missing"] > 0
    assert f["n_windows"] == mr["n_windows"]
    np.testing.assert_allclose(f["sigma_ss"], mr["sigma_ss"], rtol=1e-12)
    np.testing.assert_allclose(f["sigma_sc"], mr["sigma_sc"], rtol=1e-12)


def test_scan_pointer_rules(world, tmp_path):
    good = os.path.join(world["tables"], B.SCAN)
    spans, rec = B.read_scan(good, require_complete=True)
    assert spans == {"podcast_1": [[0, 224]], "podcast_16": [[0, 224]], "podcast_2": [[0, 224]]} and rec["sha256"] == _sha_file(good)
    cases = {"no_pointer": {"pointer": False}, "failed": {"status": "failed"}, "other_sha": {"ptr_sha": "0" * 64},
             "not_ok": {"ok": False}, "schema": {"schema": "prior33_scan_audio_v0"}, "no_sparrkulee": {"cohorts": ("fau",)}}
    for name, kw in cases.items():
        with pytest.raises(B.ScanUnavailable):
            B.read_scan(write_scan(str(tmp_path / name), world, **kw))
    inc = write_scan(str(tmp_path / "incomplete"), world, complete=False)
    assert B.read_scan(inc)[0] == spans                                       # a partial C3 run: dry runs only
    with pytest.raises(B.ScanUnavailable, match="complete"):
        B.read_scan(inc, require_complete=True)
    tab = B._Tables(world["tables"], "sparrkulee")
    odd = write_scan(str(tmp_path / "odd"), world, extra_rows=[{"stream": "no_such_stimulus", "span": [0, 10], "partners": []}])
    with pytest.raises(ValueError, match="does not hold"):
        B._shared_by_stream(B.read_scan(odd)[0], tab)
    out = str(tmp_path / "o")                                                 # a stale scan stops a dry run before any work
    with pytest.raises(B.ScanUnavailable):
        B.build(out, tables=world["tables"], cohorts="sparrkulee", sources=world["sources"], logmel_fn=FakeLogmel(),
                scan=os.path.join(str(tmp_path / "failed"), B.SCAN), log=lambda m: None)
    assert not os.path.exists(out)


def test_production_waits_for_c3_after_pass1(world, tmp_path):
    """Production (here _require_scan=True on a scratch root): without a current C3 result pass 1 completes, nothing else is
    written and WaitingForC3 is raised (main() exits 5); the rerun after C3 reuses every pass-1 marker."""
    out = os.path.join(world["root"], "out_wait")
    fake, sel = FakeLogmel(), "sparrkulee:audiobook_1_1,sparrkulee:podcast_1"
    kw = dict(tables=world["tables"], cohorts="sparrkulee", sources=world["sources"], logmel_fn=fake, streams=sel, log=lambda m: None,
              _require_scan=True)
    for scan in (str(tmp_path / "none" / B.SCAN), write_scan(str(tmp_path / "stale"), world, status="failed"),
                 write_scan(str(tmp_path / "partial"), world, complete=False), None):
        with pytest.raises(B.WaitingForC3):
            B.build(out, scan=scan, **kw)
    assert fake.calls == 2 and len(os.listdir(os.path.join(out, "sparrkulee", B.DONE))) == 2   # pass 1 ran once, then was reused
    assert not any(os.path.exists(os.path.join(out, p)) for p in (B.META, B.PCA_FILE, os.path.join("sparrkulee", B.RICH)))
    meta = B.build(out, scan=os.path.join(world["tables"], B.SCAN), **kw)
    assert fake.calls == 2 and meta["fit_mask"]["applied"]
    assert meta["fit_mask"]["n_segments_masked"] == world["meta"]["fit_mask"]["n_segments_masked"] == 2   # counted over the pool
    assert sorted(meta["pca"]["fit_streams"]) == ["audiobook_1_1", "podcast_1"]


def test_projections_are_stored_once(world, tmp_path):
    from auditory_alignment_v2.audio_targets import semi_orthogonal
    P = world["meta"]["projections"]
    for k, n in (("ss", 32), ("sc", 8)):
        arr = np.load(os.path.join(world["out"], C.RICH_P_FILE[k]), allow_pickle=False)
        assert arr.dtype == np.float32 and arr.shape == C.RICH_P_SHAPE[k] == (32, n)
        assert np.array_equal(arr, semi_orthogonal(32, n, C.RICH_SEEDS[k]).numpy())
        np.testing.assert_allclose(arr.T @ arr, np.eye(n), atol=2e-6)
        assert P[k]["sha256"] == hashlib.sha256(arr.tobytes()).hexdigest() and P[k]["seed"] == C.RICH_SEEDS[k]
        assert world["meta"]["manifest_rich"][f"P_{k}"] == {f: P[k][f] for f in ("file", "sha256", "seed", "shape")}
    other = semi_orthogonal(32, 32, 1).numpy()
    np.save(str(tmp_path / C.RICH_P_FILE["ss"]), other)
    rec = B.rich_projections(str(tmp_path))                                  # an existing file is kept, never regenerated
    assert rec["ss"]["kept_existing"] and not rec["ss"]["equals_fresh_generation"]
    assert rec["ss"]["sha256"] == hashlib.sha256(other.tobytes()).hexdigest() and not rec["sc"]["kept_existing"]
    assert np.array_equal(np.load(str(tmp_path / C.RICH_P_FILE["ss"])), other)


def _outputs(out):
    names = [B.PCA_FILE, B.META, C.RICH_P_FILE["ss"], C.RICH_P_FILE["sc"]] + [f"{c}/{f}" for c in B.COHORTS for f in (B.RICH, B.RICH_STREAMS)]
    res = {}
    for n in names:
        with open(os.path.join(out, n), "rb") as f:
            res[n] = f.read()
    return res


def test_resume_and_determinism(world):
    """An interrupted build resumed in place gives byte-identical outputs to the uninterrupted one, without re-extracting any
    stream; the rich arrays, tables, basis and projections are deterministic."""
    out2 = os.path.join(world["root"], "out_resumed")
    fake = FakeLogmel()
    with pytest.raises(B._Interrupted):
        B.build(out2, tables=world["tables"], sources=world["sources"], logmel_fn=fake, log=lambda m: None, _stop_after=3)
    first = fake.calls
    assert first == 3 and not os.path.exists(os.path.join(out2, B.META))
    B.build(out2, tables=world["tables"], sources=world["sources"], logmel_fn=fake, log=lambda m: None)
    assert fake.calls == world["calls"] and fake.frame_calls == world["frame_calls"]   # the 3 finished streams not extracted again
    a, b = _outputs(world["out"]), _outputs(out2)
    assert a.keys() == b.keys() and all(a[k] == b[k] for k in a), [k for k in a if a[k] != b[k]]
    again = FakeLogmel()
    meta = B.build(out2, tables=world["tables"], sources=world["sources"], logmel_fn=again, log=lambda m: None)
    assert meta["pca"]["reused"] and again.calls == 2 and again.frame_calls == 0   # all markers reused; only the extractor check
    c = _outputs(out2)
    assert all(c[k] == a[k] for k in a if k != B.META)


def test_dry_run_selection(world):
    out3 = os.path.join(world["root"], "out_dry")
    meta = B.build(out3, tables=world["tables"], cohorts="sparrkulee,fau,dtu", sources=world["sources"], logmel_fn=FakeLogmel(),
                   streams="sparrkulee:audiobook_1_1,sparrkulee:podcast_1,sparrkulee:audiobook_13_1,fau:111/attended", scan=None,
                   log=lambda m: None)
    assert meta["partial"] and meta["cohorts_built_now"] == ["sparrkulee", "fau", "dtu"] == sorted(meta["cohorts"], key=B.COHORTS.index)
    sk = {r["name"]: r for r in _doc(world, "sparrkulee", out3)["streams"]}
    assert {n for n, r in sk.items() if r["available"]} == {"audiobook_1_1", "podcast_1", "audiobook_13_1"}
    assert all(r["reason"] == "not_selected_dry_run" and r["source_sha256"] is None for n, r in sk.items() if not r["available"])
    assert sorted(meta["pca"]["fit_streams"]) == ["audiobook_1_1", "podcast_1"]
    fm = meta["fit_mask"]                                                    # --no-scan: the basis without C3's mask, recorded
    assert not fm["applied"] and fm["rule"] == B.FIT_RULE_NO_MASK == meta["manifest_rich"]["pca4"]["fit"] and fm["n_segments_masked"] == 0
    pre = _premask_windows(world)
    assert meta["pca"]["n_windows_kept"] == sum(len(pre[k]) for k in pre if sk[_streams(world, "sparrkulee")[k]["name"]]["available"])
    assert [r["name"] for r in _doc(world, "fau", out3)["streams"] if r["available"]] == ["111/attended"]
    dtu = {r["name"]: r["reason"] for r in _doc(world, "dtu", out3)["streams"]}                   # not named: processed whole
    assert dtu == {r["name"]: r["reason"] for r in _doc(world, "dtu")["streams"]} and set(dtu.values()) - {None} == set(EXPECT["dtu"].values())
    assert not os.path.exists(os.path.join(out3, "federici"))
    with B._build_lock(out3), pytest.raises(RuntimeError):                                       # one build per root at a time
        B.build(out3, tables=world["tables"], cohorts="sparrkulee", sources=world["sources"], logmel_fn=FakeLogmel(), log=lambda m: None)


# ---------------------------------------------------------------------------------------------------------- data-use guards
def test_restricted_participants_never_opened(world):
    bad = [p for p in world["opened"] + world["guarded"] if B.restricted_in_path(p)]
    assert not bad, bad
    for p in world["fx"]["truth"]["restricted_files"]:                       # the fixture's decoy EEG array
        full = os.path.join(world["tables"], p)
        assert os.path.exists(full) and full not in world["opened"] and B.restricted_in_path(full) == {"019"}
        with pytest.raises(B.RestrictedAccess):
            B.check_path(full)
    for p in (os.path.join(world["sources"].sparrkulee, "sub-019", "ses-x", "eeg", "x.npy"), "/data/SparrKULee_x/sub-026_eeg.npy"):
        with pytest.raises(B.RestrictedAccess):
            B.check_path(p)
    assert B.check_path("/data/dtu/sub-021/a.wav") and B.check_path("/data/sparrkulee/sub-018_eeg.npy")   # only restricted, only SK
    seen = world["opened"] + world["guarded"]
    eeg = os.path.join(world["sources"].sparrkulee, "stimuli", "eeg")
    assert not [p for p in seen if os.path.basename(p).startswith(("noise_", "t_"))]                     # never read
    assert not [p for p in seen if p.startswith(os.path.join(world["sources"].sparrkulee, "code"))]
    assert not os.path.exists(os.path.join(world["root"], "EXECUTED"))
    assert {os.path.join(eeg, f"{n}.npz.gz") for n in ("podcast_1", SK_OBJECT, SK_BYTES)} <= set(world["opened"])
    assert {world["sources"].fau_logmel, world["sources"].dtu_audio} <= set(world["guarded"])          # h5py / soundfile: guarded
    assert not [p for p in world["opened"] if p.endswith("_eeg.npy") or p.endswith("eeg_f16_tmajor.npy")]   # C7 opens no EEG
    assert os.path.realpath(world["sources"].sparrkulee) in B._SK_ROOTS                # the build registered its SparrKULee tree
    runs = _json(os.path.join(world["tables"], "sparrkulee", "runs.json"))["runs"]
    r = next(q for q in runs if q["role"] == "restricted")
    with pytest.raises(B.RestrictedAccess):
        B.sk_fit_segments(runs + [{**r, "role": "fit", "row_offset": 0, "stream": 0, "segment_starts": [128]}])


def test_restricted_path_patterns_and_registered_trees(tmp_path):
    for p in ("/data/sparrkulee/sub-019.json", "/data/sparrkulee/sub-020-extra/a.npy", "/data/sparrkulee/derivatives/sub-021/x",
              "/data/SPARRKULEE/sub-022_ses-1_eeg.npy", "/data/sparrkulee/sub-026"):
        assert B.restricted_in_path(p), p
    for p in ("/data/sparrkulee/sub-0190/a.npy", "/data/sparrkulee/sub-018.json", "/data/sparrkulee/stimuli/eeg/sub-019x.npz.gz",
              "/data/dtu/sub-019.json"):
        assert not B.restricted_in_path(p), p
    tree = str(tmp_path / "sk_tree")                                          # a dry-run --sparrkulee tree with another name
    inside, outside = os.path.join(tree, "sub-020", "x.npy"), str(tmp_path / "elsewhere" / "sub-020" / "x.npy")
    assert not B.restricted_in_path(inside)
    before = set(B._SK_ROOTS)
    B._register_sk_root(tree)
    try:
        with pytest.raises(B.RestrictedAccess):
            B.check_path(inside)
        assert B.check_path(outside) and B.check_path(os.path.join(tree, "stimuli", "eeg", "a.npz.gz"))
    finally:
        B._SK_ROOTS.intersection_update(before)


def test_output_location_guard(world, tmp_path):
    with pytest.raises(B.OutputLocationError):
        B.build(B.CACHE_ROOT, logmel_fn=FakeLogmel())                          # the cache root only from the CLI job
    with pytest.raises(B.OutputLocationError):
        B.check_out("/projects/EEG-foundation-model/auditory_public/derived/scratch_c7")
    with pytest.raises(B.OutputLocationError):
        B.check_out(os.path.join(world["sources"].sparrkulee, "x"), sources=world["sources"])
    with pytest.raises(B.OutputLocationError):
        B.check_out(os.path.join(world["tables"], "x"), tables=world["tables"])
    with pytest.raises(B.OutputLocationError):
        B.check_out(None)
    assert B.check_out(str(tmp_path / "o"), tables=world["tables"], sources=world["sources"]) == (os.path.realpath(str(tmp_path / "o")), False)
    for argv in (["--out", B.CACHE_ROOT, "--streams", "sparrkulee:x"], ["--out", B.CACHE_ROOT, "--sparrkulee", "/tmp"],
                 ["--out", B.CACHE_ROOT, "--tables", "/tmp"], ["--out", B.CACHE_ROOT, "--no-scan"],
                 ["--out", B.CACHE_ROOT, "--scan", "/tmp/scan_audio.json"], ["--out", str(tmp_path / "o2")],
                 ["--out", str(tmp_path / "o3"), "--allow-other-out", "--scan", "/tmp/x.json", "--no-scan"]):
        with pytest.raises(SystemExit):
            B.main(argv)
    assert not os.path.exists(str(tmp_path / "o2")) and not os.path.exists(str(tmp_path / "o3"))
    with pytest.raises(FileNotFoundError, match="C5"):                         # missing C5 tables: a clear error, nothing written
        B.build(str(tmp_path / "o4"), tables=str(tmp_path / "no_tables"), cohorts="sparrkulee", sources=world["sources"],
                logmel_fn=FakeLogmel())
    assert not os.path.exists(str(tmp_path / "o4"))
    from auditory_alignment_v3.prior33 import build_public, build_sparrkulee
    assert B.CACHE_ROOT == build_public.CACHE_ROOT == build_sparrkulee.CACHE_ROOT and B.RESTRICTED == build_sparrkulee.RESTRICTED


def test_main_exit_code_while_waiting_for_c3(monkeypatch, tmp_path):
    """main() turns WaitingForC3 into exit 5 (EXIT_WAIT_C3) and passes the scan choice through (build stubbed: a real production
    call would write the cache root)."""
    seen = []

    def stub(out, **kw):
        seen.append(kw["scan"])
        raise B.WaitingForC3("no current C3 result (stub)")
    monkeypatch.setattr(B, "build", stub)
    assert B.main(["--out", str(tmp_path / "o"), "--allow-other-out"]) == B.EXIT_WAIT_C3 == 5
    assert B.main(["--out", str(tmp_path / "o"), "--allow-other-out", "--no-scan"]) == 5
    assert B.main(["--out", str(tmp_path / "o"), "--allow-other-out", "--scan", "/x/scan_audio.json"]) == 5
    assert seen == ["auto", None, "/x/scan_audio.json"] and not os.path.exists(str(tmp_path / "o"))
