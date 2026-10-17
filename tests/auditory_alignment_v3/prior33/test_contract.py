"""M1 contract tests (PUBLIC_PRIOR_DESIGN.md §7.1 items 1-2, the contract parts of 3a-3b, 4d-4f and 7c) and the shared fixture:
tick grid from the physical origin without accumulated drift, the segment rule, the [i_k, i_k + 38) window and the 8-sample target,
h_aa and resampling on synthetic sinusoids and pulses, the private 64 Hz input, stable filter shas, key packing and bit budgets,
alias canonicalisation, constants and the inherited yaml, and every data-use case of the synthetic manifest (fixtures.py). The
M1 follow-up adds the stream provenance fields (inherited contract §3, design §2.3, §2.15), the standardiser convention (sigma is
the RMS about 0 with mu fixed at 0, §2.3) and the fixture's scale argument: scale=1 is the default build byte for byte, and at
scale=4 every donor stratum holds a §2.6 design batch while every structural check still holds. Every provenance value is
recomputed from the stand-in sources that the fixture returns, under the source-hash rule of the fixtures.py docstring ("Source
hashes"), and the scale-1 build is pinned by a fingerprint that ignores float rounding only (eeg2025: numpy 2.4.4, scipy 1.17.0).
The rich-stream reasons follow C7 (build_rich.py REASONS and its row rule; the fixture's NO_SOURCE includes not_nh_original and
leaves out the dry-run-only not_selected_dry_run). Where the design text quotes a figure that the specified filters do not
reproduce, the test asserts the measured value and says so (contract.py docstring, "Design-text corrections")."""
import hashlib
import io
import json
import math
import os
import sys
import warnings
from fractions import Fraction

import numpy as np
import pytest
from scipy import signal

from auditory_alignment_v3.prior33 import contract as C

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest, synthetic_kids  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _read(path, mode="r"):
    with open(path, mode) as f:
        return f.read()


def _table(fx, c):
    info = fx["manifest"]["cohorts"][c]
    return json.loads(_read(os.path.join(fx["root"], info["dir"], info["table"])))


def _streams(fx, c, name="streams"):
    info = fx["manifest"]["cohorts"][c]
    return json.loads(_read(os.path.join(fx["root"], info["dir"], info[name])))["streams"]


def _npy(fx, c, f, mmap=True):
    return np.load(os.path.join(fx["root"], fx["manifest"]["cohorts"][c]["dir"], f), mmap_mode="r" if mmap else None)


def _min_abs_diff(a, b):
    """min |a_i - b_j| over all pairs (exact), by a sorted search instead of the [len(a), len(b)] matrix."""
    a, b = np.asarray(a, dtype=np.int64), np.sort(np.asarray(b, dtype=np.int64))
    j = np.searchsorted(b, a)
    lo, hi = b[np.clip(j - 1, 0, len(b) - 1)], b[np.clip(j, 0, len(b) - 1)]
    return int(np.minimum(np.abs(a - lo), np.abs(a - hi)).min())


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("prior33_fixture"))


@pytest.fixture(scope="module")
def fx4(tmp_path_factory):
    """scale=4: every donor stratum holds a §2.6 design batch (about 295 MB, 4 s)."""
    return make_synthetic_manifest(tmp_path_factory.mktemp("prior33_fixture_s4"), scale=4)


# ---------------------------------------------------------------------------------------------------------- contract
def test_ticks_from_physical_origin_without_drift():
    k = np.arange(2_000_000, dtype=np.int64)
    i = C.tick(k)
    assert np.array_equal(i, np.round(1.28 * k).astype(np.int64)) and not ((64 * k) % 50 == 25).any()   # = round(1.28 k), no ties
    assert np.array_equal(C.tick(k[:-25] + 25), i[:-25] + 32)
    assert np.abs(i / C.FS - C.TICK_S * k).max() <= 0.0075 + 1e-12          # t_act - t_req within +-7.5 ms after 11 h: no drift
    assert np.array_equal(C.tick(np.arange(0, 2_000_000, 25)), 32 * np.arange(80_000))
    assert C.tick(250) == 320 and 250 * round(C.TICK_S * C.FS) == 250     # an accumulated round(20 ms x 64 Hz) stride drifts 1.09 s per 5 s
    for m in (0, 1, 7, 1000, 79_990):                                     # segment-relative offsets = origin-relative ticks
        assert np.array_equal(C.tick(25 * m + np.arange(C.SEG_TICKS)), 32 * m + C.TICK_OFFS)
    assert C.TICK_OFFS.shape == (250,) and C.TICK_OFFS.dtype == np.int64 and C.TICK_OFFS[-1] == 319 and not C.TICK_OFFS.flags.writeable
    assert C.TICK_OFFS[:10].tolist() == [0, 1, 3, 4, 5, 6, 8, 9, 10, 12] and np.bincount(np.diff(C.TICK_OFFS)).tolist() == [0, 179, 70]
    assert isinstance(C.tick(3), np.integer) and C.tick(25) == 32 and C.tick(0) == 0
    with pytest.raises(TypeError):
        C.tick(1.5)
    for bad in (-1, np.array([0, 5, -3]), np.array([1 << 63], dtype=np.uint64)):   # ticks count from the origin: k >= 0
        with pytest.raises(ValueError):
            C.tick(bad)


def test_segment_rule_window_and_target():
    assert (C.SPAN_EEG, C.SPAN_ENV) == (357, 327) == (C.TICK_OFFS[-1] + C.L_IN, C.TICK_OFFS[-1] + C.N_TGT)
    assert C.L_IN / C.FS == 0.59375 and C.N_TGT / C.FS == 0.125 and C.SEG_TICKS * C.TICK_S == 5.0 and C.SEG_STEP == C.tick(250)
    assert C.S_FIRST == {"sparrkulee": 128, "fau": 160, "dtu": 64, "federici": 64}
    rng = np.random.default_rng(0)
    for cohort, (g0, g1) in C.GUARDS.items():
        lens = [(0, 0), (500, 500), (C.S_FIRST[cohort] + 357 + g1, 10_000), (2880, 2880), (5000, 3000), (3000, 5000)]
        for T_eeg, T_stream in lens + [tuple(int(v) for v in rng.integers(300, 12_000, 2)) for _ in range(15)]:
            s = C.segment_starts(T_stream, T_eeg, cohort)

            def ok(v):
                return v >= g0 and v >= C.ENV_EDGE and v + 357 <= T_eeg - g1 and v + 327 <= T_stream - C.ENV_EDGE
            assert s.dtype == np.int64 and (s % 32 == 0).all() and (np.diff(s) == 320).all() and all(ok(v) for v in s)
            assert not ok(s[-1] + 320 if len(s) else C.S_FIRST[cohort])     # maximal: the next grid start is ineligible
            assert not len(s) or s[0] == C.S_FIRST[cohort]
            eeg, env = np.arange(T_eeg), np.arange(T_stream)                 # sample indices stand in for the signals
            for v in s:
                X = np.stack([eeg[v + i:v + i + C.L_IN] for i in C.TICK_OFFS]); Y = np.stack([env[v + i:v + i + C.N_TGT] for i in C.TICK_OFFS])
                assert X.shape == (250, 38) and Y.shape == (250, 8) and X.min() >= g0 and X.max() < T_eeg - g1
                assert Y.min() >= C.ENV_EDGE and Y.max() < T_stream - C.ENV_EDGE
                assert np.array_equal(X[:, 0], v + C.TICK_OFFS) and np.array_equal(Y[:, 0], X[:, 0])   # the window follows the query
                assert np.array_equal(X[:, -1] - X[:, 0], np.full(250, 37)) and np.array_equal(Y[:, -1] - Y[:, 0], np.full(250, 7))
    for onset, want in ((3.0, 320), (3.3, 320), (3.30001, 352), (0.0, 160)):    # competing talker: >= onset + 1.7 s, up to 32
        assert C.segment_starts(10_000, 10_000, "fau", onset=onset)[0] == want
    assert C.segment_starts(10_000, 10_000, "dtu", onset=0.0)[0] == 128
    for onset in np.round(rng.uniform(3.0, 5.0, 200), 3):                     # DTU masker onsets 3.0-5.0 s
        s0 = int(C.segment_starts(10_000, 10_000, "dtu", onset=onset)[0]); lo = (onset + C.CS_LEAD_S) * C.FS
        assert s0 % 32 == 0 and lo - 1e-6 <= s0 < lo + 32
    with pytest.raises(ValueError):
        C.segment_starts(1000, 1000, "dtu", onset=float("nan"))
    for phi in range(C.ANCHOR_STEP):                                         # training anchors j = phi + 31 a stay on the segment's ticks
        j = phi + C.ANCHOR_STEP * np.arange(C.N_ANCHORS)
        assert j.min() >= 0 and j.max() <= C.SEG_TICKS - 1
        assert np.abs(np.diff(C.TICK_OFFS[j]) / C.FS - 0.62).max() <= 1 / C.FS


def test_aa_fir_and_resampling_round_trips():
    stop_db = {128: -60.38, 100: -59.68, 250: -59.80}        # measured; §2.1 states <= -59.7 dB, which 100 -> 64 misses by 0.02 dB
    for fs_in, up in ((128, 1), (100, 16), (250, 32)):
        h = C.aa_fir(fs_in, up)
        assert len(h) == C.AA_TAPS[fs_in] and len(h) % 2 == 1 and np.array_equal(h, h[::-1])
        assert C._sha(h).startswith(C.FILTER_SHA16[f"aa_fir_{fs_in}"])
        w, H = signal.freqz(h, worN=1 << 18, fs=fs_in * up)
        db = 20 * np.log10(np.maximum(np.abs(H), 1e-12))
        assert np.abs(db[w <= C.AA_PASS]).max() <= 0.02 and db[w >= C.AA_STOP].max() <= -59        # §7.1 2 bounds
        assert abs(db[w >= C.AA_STOP].max() - stop_db[fs_in]) < 0.01
        assert abs(np.abs(signal.freqz(h, worN=[C.AA_CUTOFF], fs=fs_in * up)[1][0]) - 0.5) < 0.01   # -6 dB at 26 Hz
        t = np.arange(20 * fs_in) / fs_in; n_out = math.ceil(len(t) * C.FS / fs_in)
        for f in (3.0, 7.0, 10.0, 15.0, 20.0):       # a sinusoid on the fs_in grid comes out as the same sinusoid on the 64 Hz grid
            y = C.resample64(np.sin(2 * np.pi * f * t + 0.3), fs_in)
            assert y.shape == (n_out,) and np.abs(y - np.sin(2 * np.pi * f * np.arange(n_out) / C.FS + 0.3))[64:-64].max() < 2e-3
        for f, lo, hi in ((10.0, 0.99, 1.01), (20.0, 0.99, 1.01), (34.0, 0, 1e-3), (40.0, 0, 1e-3)):
            y = C.resample64(np.sin(2 * np.pi * f * t), fs_in)
            assert lo <= np.sqrt(2) * y[len(y) // 4:3 * len(y) // 4].std() < hi
        x = np.zeros(40 * fs_in); x[5 * fs_in] = 1.0                       # band-limited pulse at 5.000 s stays at 5.000 s
        y = C.resample64(signal.sosfiltfilt(signal.butter(4, 8, fs=fs_in, output="sos"), x), fs_in)
        assert int(np.argmax(y)) == 5 * C.FS
    y = C.resample64(np.sin(2 * np.pi * 45.0 * np.arange(5000) / 250), 250)   # private 32-45 Hz content does not alias
    assert np.sqrt(2) * y[300:1000].std() < 1e-3
    X = np.random.default_rng(1).standard_normal((3, 5, 1000))
    Y = C.resample64(X, 100)
    assert Y.shape == (3, 5, 640) and np.allclose(Y[1, 2], C.resample64(X[1, 2], 100))
    assert np.allclose(C.resample64(X.transpose(2, 0, 1), 100, axis=0), Y.transpose(2, 0, 1))
    z = np.arange(10.0); y = C.resample64(z, 64)
    assert np.array_equal(y, z) and y is not z
    for bad in (127.5, 0, -64, 32, 50, 63):         # non-integer rates, and upsampling (inherited contract §3: no created content)
        with pytest.raises(ValueError):
            C.resample64(z, bad)


def test_private_input_onset_lowpass_and_z():
    tt = (np.arange(C.PRIVATE_EPOCH) - C.PRIVATE_ONSET) / C.FS_PRIVATE
    rng = np.random.default_rng(2)
    ep = rng.standard_normal((7, 20, 200)).astype(np.float32)
    x64 = C.private_to64(x=ep)                                          # §6.1 names the argument x
    assert x64.shape == (7, 20, 90) and x64.dtype == np.float32 and C.PRIVATE_WIN == (32, 70) and C.PRIVATE_WIN[1] - 32 == C.L_IN
    a, b = ep[:3], ep[3:6]                                              # fixed linear preprocessing (no data-dependent step)
    assert np.allclose(C.private_to64(2 * a - b), 2 * C.private_to64(a) - C.private_to64(b), atol=1e-4)
    cos = np.cos(2 * np.pi * 3.0 * tt); ref = np.cos(2 * np.pi * 3.0 * (np.arange(90) - C.ONSET64) / C.FS)
    cos3 = C.private_to64(cos).astype(np.float64)                       # a 3 Hz cosine peaking at the onset -> peak at index 32
    assert 20 + int(np.argmax(cos3[20:45])) == C.ONSET64
    err = np.abs(cos3 - ref)                                            # measured with the LP20 of F23: 1.00020, 0.032 %, 3.11 % at 69
    assert abs(cos3[32] - 1) < 3e-4 and err[32:56].max() < 4e-4 and 0.030 < err[32:70].max() < 0.032 and 32 + int(np.argmax(err[32:70])) == 69
    y0 = C.resample64(np.pad(cos, C.PRIVATE_PAD, mode="reflect"), C.FS_PRIVATE); e0 = np.abs(y0 - ref)   # §2.1's quoted 1.0003 /
    assert abs(y0[32] - 1.00029) < 1e-5 and abs(e0[32:70].max() - 0.0131) < 2e-4 and e0[32:56].max() < 3e-4   # 1.3 % / 0.03 %: no LP20
    pulse = np.zeros(200); pulse[C.PRIVATE_ONSET] = 1.0
    assert int(np.argmax(C.private_to64(signal.sosfiltfilt(signal.butter(4, 8, fs=250, output="sos"), pulse)))) == C.ONSET64
    lp = C.lp20_sos()[0]                                                 # LP20: 25 Hz down by > 10 dB
    assert np.abs(C.band(np.cos(2 * np.pi * 25 * np.arange(4000) / C.FS), lp)[1000:3000]).max() < 10 ** (-10 / 20)
    assert np.abs(C.private_to64(np.cos(2 * np.pi * 25 * tt))[32:70]).max() < 10 ** (-10 / 20)
    z = rng.standard_normal(6000); full = C.band(z, lp)                   # edge transient of the 90-sample filtering inside [32, 70)
    assert max(np.abs(C.band(z[s:s + 90], lp) - full[s:s + 90])[32:70].max() for s in range(200, 5700, 11)) < 1e-3
    zc = C.z64_per_child(x64); w = zc[..., 32:70].astype(np.float64)
    assert zc.shape == x64.shape and zc.dtype == np.float32
    assert np.allclose(w.std(axis=(0, 2)), 1, atol=1e-5) and np.allclose(w.mean(axis=(0, 2)), 0, atol=1e-5)
    flat = x64.copy(); flat[:, 3] = 2.0
    assert np.isfinite(C.z64_per_child(flat)).all()
    with pytest.raises(ValueError):
        C.private_to64(np.zeros((2, 20, 199)))


def test_filter_shas_stable_and_band():
    for name, fn, shape in (("env_sos", C.env_sos, (4, 6)), ("eeg_sos", C.eeg_sos, (4, 6)), ("lp20_sos", C.lp20_sos, (2, 6))):
        (s1, h1), (s2, h2) = fn(), fn()
        assert s1.shape == shape and np.array_equal(s1, s2) and h1 == h2 == hashlib.sha256(s1.astype(np.float64).tobytes()).hexdigest()
        assert h1.startswith(C.FILTER_SHA16[name])
    assert C.env_sos()[1] == C._sha(signal.butter(4, [2, 8], "band", fs=64, output="sos"))    # the design's literal calls
    assert C.eeg_sos()[1] == C._sha(signal.butter(4, [1, 20], "band", fs=64, output="sos"))
    assert C.lp20_sos()[1] == C._sha(signal.butter(4, 20, "low", fs=64, output="sos"))
    shas = C.filter_shas()
    assert set(shas) == set(C.FILTER_SHA16) and len(set(shas.values())) == 6 and all(shas[k].startswith(v) for k, v in C.FILTER_SHA16.items())
    imp = np.zeros(4097); imp[2048] = 1.0
    frac = {}
    for name, sos in (("env", C.env_sos()[0]), ("eeg", C.eeg_sos()[0])):   # zero phase; impulse energy within +-m samples
        ir = C.band(imp, sos); e = ir ** 2
        assert np.abs(ir - ir[::-1]).max() < 1e-12
        frac[name] = lambda m, e=e: e[2048 - m:2048 + m + 1].sum() / e.sum()
    # Measured, not the design's figures: 2-8 Hz holds 99.895 % within +-41 (ENV_EDGE, as designed) and reaches 99.9 % at +-42;
    # 1-20 Hz holds 99.988 % within +-64 and reaches 99.99 % at +-73 (contract.py "Design-text corrections").
    assert 0.99894 <= frac["env"](C.ENV_EDGE) < 0.999 <= frac["env"](C.ENV_EDGE + 1) and C.ENV_EDGE == 41
    assert 0.99988 <= frac["eeg"](64) < 0.9999 and frac["eeg"](72) < 0.9999 <= frac["eeg"](73)
    gain = lambda sos, f: 20 * np.log10(np.abs(signal.sosfreqz(sos, worN=[float(f)], fs=64)[1][0]) ** 2)   # filtfilt = |H|^2
    for f, want in ((2, -6.02), (8, -6.02), (10, -26.3), (1, -63.0)):
        assert abs(gain(C.env_sos()[0], f) - want) < 0.5
    assert abs(gain(C.eeg_sos()[0], 1) + 6.02) < 0.05 and abs(gain(C.eeg_sos()[0], 20) + 6.02) < 0.05
    x = np.random.default_rng(3).standard_normal((3, 2000))
    env, eeg, lp = C.env_sos()[0], C.eeg_sos()[0], C.lp20_sos()[0]
    assert np.array_equal(C.band(x[0], env), signal.sosfiltfilt(env, x[0], padtype="odd", padlen=128))
    assert np.array_equal(C.band(x[0, :60], env), signal.sosfiltfilt(env, x[0, :60], padtype="odd", padlen=59))
    assert np.array_equal(C.band(x, eeg), signal.sosfiltfilt(eeg, x, axis=-1, padtype="odd", padlen=256))
    assert np.array_equal(C.band(x.T, eeg, axis=0), C.band(x, eeg).T)
    assert np.array_equal(C.band(x[0, :90], lp), signal.sosfiltfilt(lp, x[0, :90], padtype="odd"))
    other = signal.butter(4, [1, 8], "band", fs=64, output="sos")
    with pytest.raises(ValueError):
        C.band(x[0], other)
    assert np.array_equal(C.band(x[0], other, padlen=64), signal.sosfiltfilt(other, x[0], padtype="odd", padlen=64))
    e = x * np.array([[1.0], [10.0], [0.1]])
    n, r = C.rms_norm(e, return_rms=True)
    assert np.allclose(np.sqrt((n ** 2).mean(-1)), 1) and np.allclose(r, np.sqrt((e ** 2).mean(-1))) and np.allclose(C.rms_norm(e.T, axis=0), n.T)
    n1, r1 = C.rms_norm(e[1], return_rms=True)
    assert isinstance(r1, float) and np.allclose(n1, n[1])
    assert np.allclose(C.rms_norm(C.band(7.0 * e[0], env)), C.rms_norm(C.band(e[0], env)))    # stream scale drops out
    with pytest.raises(ValueError):
        C.rms_norm(np.zeros(10))


def test_pack_key_round_trip_and_bit_budgets():
    rng = np.random.default_rng(5); n = 100_000
    f = np.r_[0, (1 << 23) - 1, rng.integers(0, 1 << 23, n)]
    p = np.r_[0, (1 << 16) - 1, rng.integers(0, 1 << 16, n)]
    s = np.r_[0, (1 << 24) - 1, rng.integers(0, 1 << 24, n)]
    k = C.pack_key(f, p, s)
    assert k.dtype == np.int64 and (k >= 0).all() and k[0] == 0 and k[1] == np.iinfo(np.int64).max
    assert all(np.array_equal(a, b) for a, b in zip(C.unpack_key(k), (f, p, s)))
    o = np.lexsort((s, p, f))
    assert (np.diff(k[o]) >= 0).all() and len(np.unique(k)) == len(np.unique(np.stack([f, p, s], 1), axis=0))   # injective, ordered
    k0 = C.pack_key(3, 2, 1)
    assert isinstance(k0, np.integer) and int(k0) == (3 << 40) | (2 << 24) | 1 and tuple(map(int, C.unpack_key(k0))) == (3, 2, 1)
    assert C.pack_key(np.array([], dtype=np.int64), [], []).shape == (0,)
    for bad in ((1 << 23, 0, 0), (0, 1 << 16, 0), (0, 0, 1 << 24), (-1, 0, 0), (0, -1, 0), (0, 0, -1), (np.array([0, 1 << 23]), 0, 0),
                (0, np.uint64(1 << 16), 0)):
        with pytest.raises(AssertionError):
            C.pack_key(*bad)
    with pytest.raises(TypeError):
        C.pack_key(0, 0, 1.0)
    for bad in (np.array([1.0]), np.array([1], dtype=np.int32), k.astype(np.int32)):     # a key cast to int32 would decode as family 0
        with pytest.raises(TypeError):
            C.unpack_key(bad)
    for neg in (-1, np.int64(-1), np.array([3, -5], dtype=np.int64), np.array([np.iinfo(np.uint64).max], dtype=np.uint64)):
        with pytest.raises(AssertionError):
            C.unpack_key(neg)
    i = C.tick(np.arange(250))                     # s = family_offset + i_k: equal keys <=> same presentation and tick
    kk = C.pack_key(7, 9, 1711 + 320 * 3 + i)
    assert (np.diff(i) > 0).all() and len(np.unique(kk)) == 250 and np.array_equal(C.unpack_key(kk)[2] - 1711 - 960, i)
    torch = pytest.importorskip("torch")
    kt = torch.tensor(k[:1000])
    assert all(np.array_equal(a.numpy(), b) for a, b in zip(C.unpack_key(kt), C.unpack_key(k[:1000])))
    for bad in (kt.to(torch.int32), kt.double(), kt.to(torch.int16)):
        with pytest.raises(TypeError):
            C.unpack_key(bad)
    with pytest.raises(AssertionError):
        C.unpack_key(torch.tensor([5, -1]))
    assert all(v.numel() == 0 for v in C.unpack_key(torch.zeros(0, dtype=torch.int64)))


def test_alias_canonicalisation_vocab_and_layouts():
    assert len(C.VOCAB) == 70 == len(set(C.VOCAB)) == len({v.casefold() for v in C.VOCAB}) and C.VOCAB[:64] == C.BIOSEMI64
    assert C.VOCAB[0] == "Fp1" and C.VOCAB[63] == "O2" and C.VOCAB[64:] == ("F9", "F10", "TP9", "TP10", "FT9", "FT10")
    assert C.VOCAB_INDEX["Fp1"] == 0 and C.VOCAB_INDEX["FT10"] == 69
    for a, c in {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8", "P07": "PO7", "P03": "PO3"}.items():
        assert C.ALIASES[a] == c and C.canonical(a) == C.canonical(a.lower()) == C.canonical(f" {a} ") == C.canonical(a.encode()) == c
    assert all(C.canonical(v) == v == C.canonical(v.upper()) for v in C.VOCAB)
    for bad in ("EXG1", "A1", "M2", "Status", "", "T9", "PO07", "Fp3"):
        with pytest.raises(KeyError):
            C.canonical(bad)
    from auditory5.preprocessing import HA_CHANNELS                   # numpy / scipy only
    assert C.MONTAGES["dtu"] == C.MONTAGES["sparrkulee"] == C.BIOSEMI64
    assert C.PRIVATE_LAYOUT == tuple(C.canonical(c) for c in HA_CHANNELS)
    assert {c: len(v) for c, v in C.MONTAGES.items()} == {"sparrkulee": 64, "dtu": 64, "fau": 31, "federici": 32, "private_bdf": 20}
    assert all(C.canonical(v) == v for lay in C.MONTAGES.values() for v in lay) and all(len(set(lay)) == len(lay) for lay in C.MONTAGES.values())
    assert {c: len(v) for c, v in C.AUG_SUBSETS.items()} == {"fau": 27, "federici": 28, "private_bdf": 20}
    assert all(set(v) <= set(C.BIOSEMI64) for v in C.AUG_SUBSETS.values()) and C.AUG_P == 0.5
    donors = {"fau": ("sparrkulee", "dtu", "federici"), "federici": ("sparrkulee", "fau", "dtu"), "dtu": ("sparrkulee", "fau", "federici"),
              "private_bdf": ("sparrkulee", "fau", "dtu", "federici")}           # leave-target-out zero-shot coverage (§2.4 table)
    unseen = {t: [v for v in C.MONTAGES[t] if v not in {m for d in ds for m in C.MONTAGES[d]}] for t, ds in donors.items()}
    assert unseen == {"fau": ["F9", "F10"], "federici": ["FT9", "FT10"], "dtu": [], "private_bdf": []}
    pytest.importorskip("torch")                                      # foundation_adapter imports torch; everything above does not
    from auditory_alignment_v2 import foundation_adapter as fa      # layouts recorded from the cache attributes
    assert C.MONTAGES["dtu"] == C.MONTAGES["sparrkulee"] == tuple(fa.CHANNELS["dtu"]) == C.BIOSEMI64
    assert C.MONTAGES["fau"] == tuple(fa.CHANNELS["fau"]) and C.MONTAGES["federici"] == tuple(fa.CHANNELS["federici"])
    assert C.PRIVATE_LAYOUT == tuple(fa.ALIASES.get(c, c) for c in fa.CHANNELS["private_bdf"])


def test_constants_seeds_and_projection():
    """yaml- and torch-independent: seeds, P (numpy QR of the seed, sha 706c4ff4...), zero-shot names, rich constants."""
    assert (C.PROJ_SEED, C.RICH_SEEDS, C.BRIDGE_SEED, C.TAU_POOL_SEED, C.FOLD_SEED) == (20261016, {"ss": 20261017, "sc": 20261018}, 20261016,
                                                                                          20261017, 20261005)
    assert C.BREADTH_SEED == 3401 and C.PANEL_SEEDS == (3407, 3413) and C.XM_SEED_OFFSET == 7 and C.CAL_SEED_OFFSET == 99
    assert C.READOUT_SEED_OFFSETS == (5, 98, 99, 1000) and C.TAU == 0.1 and C.NEIGHBOR == 128 and C.ENV_EDGE == 41
    assert (C.FAMILY_BITS, C.PRES_BITS, C.S_BITS) == (23, 16, 24) and C.FAMILY_BITS + C.PRES_BITS + C.S_BITS == 63
    assert C.GUARDS == {"sparrkulee": (128, 128), "fau": (157, 157), "dtu": (41, 41), "federici": (41, 41)} and C.GUARDS["fau"][0] * 2 == 314
    q, _ = np.linalg.qr(np.random.default_rng(C.PROJ_SEED).standard_normal((32, 8)))
    P = q.astype(np.float32)
    assert hashlib.sha256(P.tobytes()).hexdigest().startswith(C.P_SHA16) and np.abs(P.T @ P - np.eye(8)).max() < 1e-6
    assert np.linalg.matrix_rank(P) == 8 and P.shape == C.P_SHAPE and C.P_FILE == "P_32x8_seed20261016_f32.npy"
    assert C.ZS_MODE_NAME == {"A": "zero_shot__no_target_supervised_fit__fixed_input_preprocessing",
                              "B": "zero_shot__no_target_supervised_fit__fau_noica_target_z",
                              "C": "zero_shot__no_target_supervised_fit__source_statistics_only",
                              "C_partial": "zero_shot__no_target_supervised_fit__source_statistics_partial"}
    assert set(C.ZS_COHORTS) == set(C.CACHE_FILE) == set(C.ZS_SUFFIX)
    assert C.RICH_COLS == ("ss0", "ss1", "ss2", "ss3", "sc") and sum(C.RICH_DIMS.values()) == len(C.RICH_COLS)
    assert C.RICH_P_SHAPE == {"ss": (32, 32), "sc": (32, 8)} and all(str(C.RICH_SEEDS[k]) in C.RICH_P_FILE[k] for k in C.RICH_P_FILE)


def test_projection_matches_audio_targets():
    pytest.importorskip("torch")
    from auditory_alignment_v2.audio_targets import semi_orthogonal
    from fixtures import _semi_orthogonal
    for d, n, seed in ((32, 8, C.PROJ_SEED), (*C.RICH_P_SHAPE["ss"], C.RICH_SEEDS["ss"]), (*C.RICH_P_SHAPE["sc"], C.RICH_SEEDS["sc"])):
        assert np.array_equal(semi_orthogonal(d, n, seed).numpy(), _semi_orthogonal(d, n, seed))


def test_inherited_yaml():
    yaml = pytest.importorskip("yaml")
    y = yaml.safe_load(_read(os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016", "inherited", "public_prior_v3_3.yaml")))
    d = y["data_contract"]
    assert y["execution_contract"] == C.CONTRACT and d["eeg_hz"] == d["target_hz"] == C.FS and d["target_samples"] == C.N_TGT
    assert d["target_duration_ms"] == 1000 * C.N_TGT / C.FS and d["query_step_ms"] == 1000 * C.TICK_S and tuple(d["target_band_hz"]) == C.ENV_BAND
    assert d["query_indexing"] == "round_from_physical_origin_no_accumulated_stride_drift" and d["input_window_seconds"] == [0, 0.6]
    assert C.L_IN == int(0.6 * C.FS) and d["projection_dim"] == C.P_SHAPE[0] and d["projection_seed"] == C.PROJ_SEED
    assert y["cross_person"]["nce_neighbor_exclusion_ms"] == 1000 * C.NEIGHBOR / C.FS and y["breadth_seed"] == C.BREADTH_SEED
    assert y["channel_map"]["aliases"].items() <= C.ALIASES.items()


# ---------------------------------------------------------------------------------------------------------- fixture
def test_fixture_files_caches_and_normalisation(fx):
    m, root = fx["manifest"], fx["root"]
    assert hashlib.sha256(_read(fx["manifest_path"], "rb")).hexdigest() == fx["manifest_sha256"] and m["contract"] == C.CONTRACT
    assert m["schema"] == "prior33_manifest_v2" and oct(os.stat(fx["manifest_path"]).st_mode & 0o777) == "0o444"
    assert m["filters"] == C.filter_shas() and m["projection"]["sha256"].startswith(C.P_SHA16)
    assert np.array_equal(np.load(os.path.join(root, C.P_FILE)), fx["P"])
    for k in ("ss", "sc"):
        Pk = np.load(os.path.join(root, C.RICH_P_FILE[k]))
        assert np.array_equal(Pk, fx["P_rich"][k]) and Pk.shape == C.RICH_P_SHAPE[k] and np.abs(Pk.T @ Pk - np.eye(Pk.shape[1])).max() < 1e-5
        assert hashlib.sha256(Pk.tobytes()).hexdigest() == m["rich"][f"P_{k}"]["sha256"]
    assert m["standardiser"]["mu"] == [0.0] * 8 and m["standardiser"]["abs_mu_over_sigma_max"] < 0.05 and len(m["standardiser"]["sigma"]) == 8
    assert set(m["cohorts"]) == {"sparrkulee", "fau", "dtu", "federici"} and set(m["segments"]) == set(m["cohorts"])
    assert {c: sorted(v["caches"]) for c, v in m["cohorts"].items()} == {"sparrkulee": ["A"], "fau": ["A", "B", "C"], "dtu": ["A", "C"],
                                                                          "federici": ["A", "C_partial"]}
    pres = m["presentations"]
    for c, info in m["cohorts"].items():
        tab = _table(fx, c); items = tab[info["items"]]; streams = _streams(fx, c); env = _npy(fx, c, info["env"])
        X = {mo: _npy(fx, c, f) for mo, f in info["caches"].items()}
        assert all(a.shape == (info["n_rows"], info["n_ch"]) and a.dtype == np.float16 for a in X.values())
        assert [C.canonical(v) for v in info["layout"]] == list(C.MONTAGES[c]) and info["guards"] == list(C.GUARDS[c])
        assert sum(st["length"] for st in streams) == len(env)
        assert all(st["offset"] == sum(q["length"] for q in streams[:i]) for i, st in enumerate(streams))
        for st in streams:
            e = env[st["offset"]:st["offset"] + st["length"]].astype(np.float64)
            assert abs(np.sqrt((e ** 2).mean()) - 1) < 1e-4
        cached = sorted((it for it in items if it["row_offset"] is not None), key=lambda it: it["row_offset"])
        assert cached[0]["row_offset"] == 0 and all(a["row_offset"] + a["T_eeg"] == b["row_offset"] for a, b in zip(cached, cached[1:]))
        assert cached[-1]["row_offset"] + cached[-1]["T_eeg"] == info["n_rows"]
        for it in cached:                                               # each piece inside its role slab
            lo, hi = info["role_slabs"][it["slab"]]
            assert lo <= it["row_offset"] and it["row_offset"] + it["T_eeg"] <= hi
            p = pres[it["presentation"]]
            assert p["cohort"] == c and p["stream"] == it["stream"] and streams[it["stream"]]["length"] == it["T_env"]
            assert it["segment_starts"] == C.segment_starts(it["T_env"], it["T_eeg"], c, onset=it["onset_s"]).tolist()
        S = m["segments"][c]
        assert len({len(v) for v in S.values()}) == 1 and set(S) == {"piece", "participant", "presentation", "family", "s", "role", "kind",
                                                                       "n_listeners", "n_partners"}
        for piece, part, p, s in zip(S["piece"], S["participant"], S["presentation"], S["s"]):
            it = items[piece]
            assert it["row_offset"] is not None and it["participant"] == part and it["presentation"] == p and s in it["segment_starts"]
            assert not any(sh["presentation"] == p and sh["span"][0] < s + C.SPAN_EEG and s < sh["span"][1] for sh in m["shared_audio"])
        g = info["guards"][0]
        for part in tab["participants"][:3] + tab["participants"][-2:]:  # z per participant x channel over the guarded spans of all
            mine = [it for it in cached if it["participant"] == part["participant"]]   # its pieces, masked (piece, channel) cells out
            for mo in set(X) & {"A", "B"}:
                blocks = [(it, np.asarray(X[mo][it["row_offset"] + g:it["row_offset"] + it["T_eeg"] - g], dtype=np.float64)) for it in mine]
                for j, name in enumerate(info["layout"]):
                    v = [b[:, j] for it, b in blocks if name not in it["masked"]]
                    if v:
                        v = np.concatenate(v)
                        assert abs(v.mean()) < 0.02 and abs(v.std() - 1) < 0.02, (c, part["participant"], mo, name)
    fau = _table(fx, "fau")
    for q in fau["pieces"]:                                             # CI interpolated channels masked in every mode
        for ch in fx["truth"]["fau_masked"].get(q["participant"], ()):
            for f in m["cohorts"]["fau"]["caches"].values():
                assert not np.asarray(_npy(fx, "fau", f)[q["row_offset"]:q["row_offset"] + q["T_eeg"], C.MONTAGES["fau"].index(ch)]).any()
    runs = {r["run_id"]: r for r in _table(fx, "sparrkulee")["runs"]}
    A = _npy(fx, "sparrkulee", "eeg_f16_tmajor.npy")
    for sub, stim, ch in fx["truth"]["masked_cells"]:                     # QC rule: planted flat / loud channels are masked and zero
        r = runs[f"sub-{sub}_{stim}"]
        assert ch in r["masked"] and not np.asarray(A[r["row_offset"]:r["row_offset"] + r["T_eeg"], C.BIOSEMI64.index(ch)]).any()
    raw = np.asarray(_npy(fx, "dtu", "eeg_raw_f16_tmajor.npy")[:4000], dtype=np.float64)   # DTU: CAR over the 64 EEG channels
    assert np.abs(raw.sum(1)).max() < 1e-2 * raw.std(0).mean() * 64 and raw.std(0).min() > 1.0


def test_fixture_keys_and_family_clocks(fx):
    m, t = fx["manifest"], fx["truth"]
    pres, fams = m["presentations"], m["families"]
    assert [p["id"] for p in pres] == list(range(len(pres))) and [f["id"] for f in fams] == list(range(len(fams)))
    assert len(pres) < 1 << C.PRES_BITS and len(fams) < 1 << C.FAMILY_BITS
    assert all(p["id"] in fams[p["family"]]["members"] and fams[p["family"]]["cohort"] == p["cohort"] for p in pres)
    assert sorted(i for f in fams for i in f["members"]) == list(range(len(pres)))
    content, K = set(), []
    for block in ("core", "csx", "dev", "bridge_cal"):                    # every anchor of every pool, all cohorts at once
        for c, rows in m["pools"][block].items():
            S = m["segments"]["fau" if c == "fau_cs" else c]
            content |= {(S["presentation"][r], S["s"][r]) for r in rows}
    for p, s in sorted(content):
        K.append(C.pack_key(pres[p]["family"], p, pres[p]["family_offset"] + s + C.TICK_OFFS))
    K = np.concatenate(K)
    assert len(np.unique(K)) == len(K) == 250 * len(content)              # one key per anchor; listeners of the content share it
    fam, pid, s_ = C.unpack_key(K)
    cohorts = {pres[i]["cohort"] for i in np.unique(pid)}
    assert cohorts == {"sparrkulee", "fau", "dtu", "federici"}            # global ids: no key collides across cohorts
    assert all((fam[pid == i] == pres[i]["family"]).all() for i in np.unique(pid))
    P = t["presentation"]
    fau_ss = [P[f"fau:{c}"] for c in ("111", "122")]; fau_cs = [P["fau:215/left"], P["fau:215/right"]]
    assert all(np.isin(fau_ss + fau_cs, pid))                              # FAU single- and competing-talker keys are present
    l_, r_ = (pres[i] for i in fau_cs)                                    # (code, side): same stream and family, different keys
    assert l_["stream"] == r_["stream"] and l_["family"] == r_["family"] and l_["onset_s"] == 2.0 and l_["kind"] == "cs"
    assert not set(K[pid == fau_cs[0]]) & set(K[pid == fau_cs[1]])
    h1, h2, sh, art = (P[f"sparrkulee:{n}"] for n in ("audiobook_1_1", "audiobook_1_2", "audiobook_1_shifted", "audiobook_1_artefact"))
    assert _min_abs_diff(s_[pid == h1], s_[pid == h2]) > C.NEIGHBOR                   # halves +1711 / +30986: never neighbours
    assert _min_abs_diff(s_[pid == h1], s_[pid == sh]) == 0 and (fam[pid == sh] == t["family"]["sparrkulee:audiobook_1"]).all()
    assert pres[art]["family_offset"] == 2351 and pres[art]["family"] == pres[h1]["family"]
    for key, off in t["family_offset"].items():                          # declared, scan-merged and measured offsets
        assert pres[P[key]]["family_offset"] == off
    for c, a, b, off in (("dtu", "t01", "t07", 400), ("federici", "N1", "V1", 48)):   # the merged copy follows its family clock
        pa, pb = pres[P[f"{c}:{a}"]], pres[P[f"{c}:{b}"]]
        assert pa["family"] == pb["family"] and pb["family_offset"] == off and pb["offset_known"] and fams[pa["family"]]["clock"] == "known"
        st = _streams(fx, c); env = _npy(fx, c, m["cohorts"][c]["env"], mmap=False).astype(np.float64)
        ea, eb = (env[st[q["stream"]]["offset"]:st[q["stream"]]["offset"] + st[q["stream"]]["length"]] for q in (pa, pb))
        n = min(len(ea) - off, len(eb)) - 100
        assert np.corrcoef(ea[off + 50:off + 50 + n], eb[50:50 + n])[0, 1] > 0.9          # eb[t] ~ ea[t + off]
    assert fams[pres[P["dtu:t07"]]["family"]]["basis"] == "duplicate_scan"
    n2, v2 = pres[P["federici:N2"]], pres[P["federici:V2"]]
    assert n2["family"] == v2["family"] and fams[v2["family"]]["clock"] == "unknown" and not v2["offset_known"]
    assert t["unknown_clock_families"] == [v2["family"]] and fams[v2["family"]]["members"] == [n2["id"], v2["id"]]


def test_fixture_data_use_cases(fx):
    m, t, root = fx["manifest"], fx["truth"], fx["root"]
    pres, seg, pools = m["presentations"], m["segments"], m["pools"]
    in_pool = {c: {r for b in ("core", "csx", "dev", "bridge_cal") for cc, rows in pools[b].items() if (cc == "fau_cs" and c == "fau") or cc == c
                   for r in rows} for c in seg}
    for c, S in seg.items():                                                # pools: donor roles with a valid partner only
        for r in in_pool[c]:
            assert S["role"][r] in ("fit", "dev", "bridge_cal") and S["n_partners"][r] >= 1 and S["n_listeners"][r] >= 2
        assert all(r in in_pool[c] for r in range(len(S["s"])) if S["n_partners"][r] >= 1 and S["role"][r] in ("fit", "dev", "bridge_cal")
                   and (S["kind"][r] == "ss" or c == "fau"))
    dtu = _table(fx, "dtu")["pieces"]; S = seg["dtu"]
    hi = [q for q in dtu if q["participant"] in t["dtu_hi"]]               # 4c: HI rows are never cross-person eligible
    assert hi and all(q["role"] == "target_only" and q["slab"] == "target_only" for q in hi)
    assert not {r for r in in_pool["dtu"] if S["participant"][r] in t["dtu_hi"]}
    nh_stream = {pres[p]["stimulus"]: pres[p]["stream"] for p in range(len(pres)) if pres[p]["cohort"] == "dtu" and pres[p]["kind"] == "ss"
                 and "@eq" not in pres[p]["stimulus"]}
    for q in hi:
        if q["kind"] == "ss":
            p = pres[q["presentation"]]
            assert "@eq:" in p["stimulus"] and q["stream"] == nh_stream[q["stimulus"]] and sum(x["presentation"] == p["id"] for x in dtu) == 1
    cs = [q for q in dtu if q["kind"] == "cs"]                              # two-talker trials: masker onsets, never donors
    assert len(cs) == 10 and all(3.0 <= q["onset_s"] <= 5.0 and q["ignored_lead"] == round(q["onset_s"] * C.FS) for q in cs)
    assert all(q["segment_starts"] and min(q["segment_starts"]) >= (q["onset_s"] + C.CS_LEAD_S) * C.FS and q["role"] == "target_only" for q in cs)
    shared_cs = [r for r in range(len(S["s"])) if S["presentation"][r] == t["dtu_shared_two_talker"]]
    assert shared_cs and all(S["n_listeners"][r] == 2 and S["n_partners"][r] == 0 and r not in in_pool["dtu"] for r in shared_cs)
    single = [r for r in range(len(S["s"])) if pres[S["presentation"][r]]["stimulus"] == "t08"]
    assert single and all(S["n_listeners"][r] == 1 and r not in in_pool["dtu"] for r in single)
    fed = _table(fx, "federici"); S = seg["federici"]                      # phantom: test_only, never a donor
    ph = {p["participant"] for p in fed["participants"] if p["test_only"]}
    assert ph == set(t["phantom"]) and all(p["fold"] == -1 and not p["donor"] for p in fed["participants"] if p["test_only"])
    assert not {S["participant"][r] for r in in_pool["federici"]} & ph and {S["participant"][r] for r in range(len(S["s"]))} & ph
    parts = {p["participant"]: p for p in fed["participants"]}             # 4h: HC N / HC-v N are separate, same fold, never partners
    assert m["partner_exclusions"] == t["twins"] and len(t["twins"]) == 2
    groups, n_twin = {}, 0
    for r in range(len(S["s"])):
        groups.setdefault((S["presentation"][r], S["s"][r], S["role"][r]), set()).add(S["participant"][r])
    for _, a, b in t["twins"]:
        assert parts[a]["uid"] != parts[b]["uid"] and parts[a]["identity"] == parts[b]["identity"] and parts[a]["fold"] == parts[b]["fold"] >= 0
        for r in range(len(S["s"])):
            if S["participant"][r] in (a, b) and S["role"][r] == "fit":
                others = groups[(S["presentation"][r], S["s"][r], "fit")] - {a, b}
                assert S["n_partners"][r] == len(others)                    # the twin never counts as a partner
        n_twin += sum(a in g and b in g for (_, _, role), g in groups.items() if role == "fit")
    assert m["hc_hcv_excluded_pairs"] == n_twin > 0
    n5 = [r for r in range(len(S["s"])) if pres[S["presentation"][r]]["stimulus"] == "N5"]
    assert n5 and all(S["n_listeners"][r] == 2 and S["n_partners"][r] == 0 and r not in in_pool["federici"] for r in n5)
    n1v = [r for r in range(len(S["s"])) if S["participant"][r] == "HC-v:1001" and pres[S["presentation"][r]]["stimulus"] == "N1"]
    assert n1v and all(r in in_pool["federici"] for r in n1v)              # a would-be twin pair next to valid partners stays eligible
    runs = _table(fx, "sparrkulee"); S = seg["sparrkulee"]                  # restricted decoy: listed, never opened / hashed / audited
    (dec,) = [r for r in runs["runs"] if r["role"] == "restricted"]
    assert dec["row_offset"] is None and dec["source_sha256"] is None and dec["audit"]["clock"] == "not_audited" and not dec["segment_starts"]
    assert dec["raw_file"] == t["restricted_files"][0] and not os.path.isabs(dec["raw_file"]) and os.path.exists(os.path.join(root, dec["raw_file"]))
    with open(os.path.join(root, dec["raw_file"]), "rb") as f:             # T_eeg as the .npy header gives it (header only)
        shape = np.lib.format.read_array_header_1_0(f)[0] if np.lib.format.read_magic(f) == (1, 0) else None
    assert shape == (64, dec["T_eeg"]) and dec["sub"] not in {p["sub"] for p in runs["participants"]}
    assert dec["piece_id"] not in {runs["runs"][i]["piece_id"] for i in S["piece"]}
    assert all(runs["runs"][S["piece"][r]]["role"] in ("fit", "dev", "bridge_cal") for r in in_pool["sparrkulee"])
    bad = {r["run_id"] for r in runs["runs"] if r["flags"]}
    assert bad == set(t["excluded_runs"]) and not {runs["runs"][S["piece"][r]]["run_id"] for r in in_pool["sparrkulee"]} & bad
    assert {e["run_id"] for e in m["exclusions"]} == bad | {dec["run_id"]}
    for role_ in ("fit", "dev", "bridge_cal"):                              # roles disjoint by participant and family
        subs = {S["participant"][r] for r in pools["core" if role_ == "fit" else role_]["sparrkulee"]}
        assert all(p["role"] == role_ for p in runs["participants"] if p["sub"] in subs)
    fam_of = {b: {pres[S["presentation"][r]]["family"] for r in (pools["core"]["sparrkulee"] if b == "fit" else pools[b]["sparrkulee"])}
              for b in ("fit", "dev", "bridge_cal")}
    assert not fam_of["fit"] & fam_of["dev"] and not fam_of["fit"] & fam_of["bridge_cal"] and not fam_of["dev"] & fam_of["bridge_cal"]
    jingle = ("podcast_1", "podcast_2", "podcast_16")
    assert not any(s < t["shared_span"][1] for p, s in zip(S["presentation"], S["s"]) if pres[p]["stimulus"] in jingle)
    ds = m["donor_sets"]                                                    # leave-target-out donor sets, overlap exclusion, fau_cs in CSX
    assert set(ds) == {"fau", "dtu", "federici", "private_bdf"} and "csx" not in ds["fau"]
    for target, blocks in ds.items():
        for b, v in blocks.items():
            assert target not in v["strata"] and "private_bdf" not in v["strata"] and ("fau_cs" in v["strata"]) == (b == "csx")
            assert v["strata"][0] == "sparrkulee" and abs(sum(v["weights"]) - 1) < 1e-12
            for c, n, w in zip(v["strata"], v["n_segments"], v["weights"]):
                rows = pools["csx"]["fau_cs"] if c == "fau_cs" else pools["core"][c]; Sc = seg["fau" if c == "fau_cs" else c]
                assert n == sum(Sc["presentation"][r] not in v["excluded_presentations"][c] for r in rows) > 0
                assert abs(w - n / sum(v["n_segments"])) < 1e-12
        assert blocks["rich"] == blocks["core"]
    p122, s05 = t["presentation"]["fau:122"], pres[t["presentation"]["dtu:t05"]]["stream"]
    t05 = {p["id"] for p in pres if p["cohort"] == "dtu" and p["stream"] == s05}
    assert ds["dtu"]["core"]["excluded_presentations"]["fau"] == [p122] and set(ds["fau"]["core"]["excluded_presentations"]["dtu"]) == t05
    assert m["overlap"][0]["r"] >= 0.7 and all(not v for b in ds["federici"].values() for v in b["excluded_presentations"].values())
    assert m["coverage"] == {"fau": {"n_seen": 29, "n_total": 31, "unseen": ["F9", "F10"]},
                             "federici": {"n_seen": 30, "n_total": 32, "unseen": ["FT9", "FT10"]},
                             "dtu": {"n_seen": 64, "n_total": 64, "unseen": []}, "private_bdf": {"n_seen": 20, "n_total": 20, "unseen": []}}
    for target, rows in m["bridge"]["fit_rows"].items():
        for c, r in rows:
            core = ds[target]["core"]
            assert c in core["strata"] and r in pools["core"][c] and seg[c]["presentation"][r] not in core["excluded_presentations"][c]
    assert m["budget"]["N_SK"] == len(pools["core"]["sparrkulee"]) and m["budget"]["S0"] == math.ceil(30 * 8 * m["budget"]["N_SK"] / 256)


def test_fixture_cells(fx):
    m, kids = fx["manifest"], fx["kids"]
    cells = m["cells"]
    assert [(c["dataset"], c["subject_fold"], c["content_fold"]) for c in cells] == \
        [("fau", sf, cf) for sf in range(5) for cf in (0, 1)] + [("dtu", sf, cf) for sf in range(5) for cf in (0, 1)] + \
        [("federici", sf, 0) for sf in range(5)] + [("private_bdf", sf, 0) for sf in range(5)]
    assert len({c["split_hash"] for c in cells}) == 30
    group = {c: {p["participant"]: p["group"] for p in _table(fx, c)["participants"]} for c in ("fau", "dtu", "federici")}
    group["private_bdf"] = {k["id"]: k["group"] for k in kids}
    need = {"fau": {"th", "ha", "ci"}, "dtu": {"nh", "hi"}, "federici": {"HC", "CI"}, "private_bdf": {"HA", "NH"}}
    for c in cells:
        d = {k: v for k, v in c.items() if k != "split_hash"}
        assert c["split_hash"] == hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
        tr, te, to = set(c["train"]), set(c["test"]), set(c["test_only"])
        assert te and not tr & te and not to & (tr | te) and set(c["always_train"]) <= tr - te
        assert need[c["dataset"]] <= {group[c["dataset"]][p] for p in te}  # no degenerate cell: every group is tested in every fold
        assert tr | te | to == set(group[c["dataset"]])
        if c["dataset"] in ("dtu", "federici"):                            # content roles partition the content
            ids = sorted(c["content_groups"]); roles = c["content"]
            assert sorted(i for r in ("fit", "es", "test") for i in roles[r]) == ids and all(roles[r] for r in ("fit", "es", "test"))
            for r in roles:
                gs = {c["content_groups"][i] for i in roles[r]}
                assert not any(c["content_groups"][i] in gs for r2 in roles if r2 != r for i in roles[r2])   # a group keeps one role
        if c["dataset"] == "fau":
            assert sorted(sum(c["content"]["ss"].values(), [])) == sorted(["111", "112", "113", "114", "121", "122", "123", "124"])
        if c["dataset"] == "federici":
            assert to == set(fx["truth"]["phantom"])
    fau = [c for c in cells if c["dataset"] == "fau"]                      # each FAU participant is tested in exactly one subject fold
    tested = sorted(p for c in fau if c["content_fold"] == 0 for p in c["test"])
    assert tested == sorted(p for p in group["fau"] if p not in ("301", "302"))


def test_fixture_rich_block(fx):
    m = fx["manifest"]; r = m["rich"]
    assert r["columns"] == list(C.RICH_COLS) and len(r["sigma_ss"]) == 32 and len(r["sigma_sc"]) == 8 and r["loss_weights"] == [1.0, 0.5, 0.5]
    assert min(r["sigma_ss"] + r["sigma_sc"]) > 0 and r["n_windows"] > 0 and np.load(os.path.join(fx["root"], r["pca4"]["file"])).shape == (128, 4)
    masked = {}
    for c, info in m["cohorts"].items():
        st, rs = _streams(fx, c), _streams(fx, c, "rich_streams"); R = _npy(fx, c, info["rich"], mmap=False)
        assert R.shape == (len(_npy(fx, c, info["env"])), len(C.RICH_COLS)) and R.dtype == np.float32
        assert [q["stream"] for q in rs] == [q["stream"] for q in st]
        for a, b in zip(st, rs):
            x = R[a["offset"]:a["offset"] + a["length"]].astype(np.float64)
            if b["available"]:                                              # 2-8 Hz, RMS 1 per stream and dimension; clock lag 0 +- 1
                assert np.isfinite(x).all() and np.allclose(np.sqrt((x ** 2).mean(0)), 1, atol=1e-4)
                assert abs(b["clock_lag"]) <= 1 and b["reason"] is None
            else:                                                           # masked, never fabricated
                assert np.isnan(x).all() and b["reason"]
                masked.setdefault(c, []).append(b["name"])
    assert masked == fx["truth"]["rich_masked"] and len(masked["federici"]) == len(_streams(fx, "federici"))
    sk = {q["name"]: q for q in _streams(fx, "sparrkulee", "rich_streams")}
    assert sk["podcast_2"]["reason"] == "clock_lag" and sk["podcast_2"]["clock_lag"] == 3              # lag 3: masked
    assert sk["podcast_1"]["available"] and sk["podcast_1"]["clock_lag"] == 1                         # lag 1: the 0 +- 1 boundary passes
    assert sk["audiobook_2_1"]["reason"] == "waveform_unavailable" and sk["audiobook_2_1"]["clock_lag"] is None


def test_fixture_mode_c_determinism_and_perturbation(fx, tmp_path):
    m = fx["manifest"]
    assert not m["mode_c"]["sparrkulee"]["supported"] and {c: m["mode_c"][c]["mode"] for c in ("fau", "dtu", "federici")} == \
        {"fau": "C", "dtu": "C", "federici": "C_partial"}
    for target, mc in m["mode_c"].items():
        if not mc["supported"]:
            continue
        assert sorted(mc["scale"]) == sorted(C.MONTAGES[target]) and target not in mc["donors"] and all(v > 0 for v in mc["scale"].values())
    vals = {}
    for c in ("sparrkulee", "dtu", "federici"):                            # recompute FAU's scale at Cz and at F9 (no donor has F9)
        tab = _table(fx, c)
        for p in tab["participants"]:
            if p["donor"] and p.get("role", "fit") == "fit":
                for n, v in zip(C.MONTAGES[c], p["sd_prez"]["A"]):
                    if v is not None:
                        vals.setdefault(n, []).append(v)
    assert np.isclose(m["mode_c"]["fau"]["scale"]["Cz"], np.median(vals["Cz"]))
    assert np.isclose(m["mode_c"]["fau"]["scale"]["F9"], np.median(sum(vals.values(), [])))
    fx2 = make_synthetic_manifest(tmp_path / "again")                        # deterministic: byte-identical JSON in another directory
    assert fx2["manifest_sha256"] == fx["manifest_sha256"]
    for c, info in m["cohorts"].items():
        for f in (info["table"], info["streams"], info["rich_streams"]):
            assert _read(os.path.join(fx["root"], info["dir"], f), "rb") == _read(os.path.join(fx2["root"], info["dir"], f), "rb")
    make_synthetic_manifest(tmp_path / "again")                              # rebuild in place over the 0444 manifest
    fx3 = make_synthetic_manifest(tmp_path / "perturbed", perturb={("fau", "305"): 5.0})
    m3 = fx3["manifest"]                                                     # §7.1 9: a target participant's variance moves the
    assert m3["mode_c"]["fau"]["scale"] == m["mode_c"]["fau"]["scale"]     # mode-A input, never the target's mode-C scale
    assert m3["mode_c"]["dtu"]["scale"] != m["mode_c"]["dtu"]["scale"]     # (FAU is a donor of DTU: a donor statistic does move it)
    q = [x for x in _table(fx, "fau")["pieces"] if x["participant"] == "305"][1]   # a piece of 305 that was not scaled
    sl = slice(q["row_offset"], q["row_offset"] + q["T_eeg"])
    a1, a3 = (np.asarray(_npy(f, "fau", "eeg_f16_tmajor.npy")[sl], dtype=np.float64) for f in (fx, fx3))
    c1, c3 = (np.asarray(_npy(f, "fau", "eeg_raw_f16_tmajor.npy")[sl], dtype=np.float64) for f in (fx, fx3))
    assert np.abs(a1 - a3).max() > 0.1 and np.array_equal(c1, c3)
    o = [x for x in _table(fx, "fau")["pieces"] if x["participant"] == "306"][0]
    so = slice(o["row_offset"], o["row_offset"] + o["T_eeg"])
    assert np.array_equal(_npy(fx, "fau", "eeg_f16_tmajor.npy")[so], _npy(fx3, "fau", "eeg_f16_tmajor.npy")[so])


def test_synthetic_kids_private_structure(fx):
    kids = fx["kids"]
    assert len(kids) == 11 and {k["group"] for k in kids} == {"HA", "NH"}
    for k in kids:
        n = len(k["y"])
        assert k["x"].shape == (n, 20, 200) and k["x"].dtype == np.float32 and len(k["swap"]) == n and k["es_mask"].dtype == bool
        assert set(np.unique(k["block"][k["es_mask"]])) == {4} and {0, 1} <= set(k["y"].tolist())
    for sf in range(5):
        assert {k["group"] for k in kids if k["fold"] == sf} == {"HA", "NH"}
    rng = np.random.default_rng(C.FOLD_SEED); want = {}                       # hc.folds: kid order within each group
    for g in ("HA", "NH"):
        ids = [k["id"] for k in kids if k["group"] == g]
        for p_, i in enumerate(rng.permutation(len(ids))):
            want[ids[i]] = p_ % 5
    assert want == {k["id"]: k["fold"] for k in kids}
    try:
        from auditory_c3.c3dl import hc
    except ImportError:          # torch / pandas missing: the replica above still pins the rule
        hc = None
    if hc is not None:
        assert hc.folds(kids) == want
    x64 = C.z64_per_child(C.private_to64(kids[0]["x"]))
    assert x64.shape == (len(kids[0]["y"]), 20, 90) and np.allclose(x64[..., 32:70].std(axis=(0, 2)), 1, atol=1e-4)
    assert synthetic_kids()[3]["fold"] == kids[3]["fold"]


# ---------------------------------------------------------------------------------------------------------- provenance, standardiser, scale
def _is_sha(v):
    return isinstance(v, str) and len(v) == 64 and all(ch in "0123456789abcdef" for ch in v)


def test_fixture_stream_provenance(fx):
    """Inherited contract §3 and design §2.3: every envelope stream row records its origin, original band and filter hashes (and its
    source rate, source sha256 and NaN count). Design §2.15 / §6.2 C7: every rich_streams row records a source sha256, which is None
    exactly where no waveform is read, under build_rich.py's row rule (its reasons; source_sha256 None exactly for a no-source
    reason, available exactly when there is no reason). Every value is recomputed from the stand-in sources the fixture returns
    (fx["sources"]): the source hashes by the rule of the fixtures.py docstring ("Source hashes": a SparrKULee stream is a whole
    file, a FAU / DTU / Federici stream an array inside a container), and the envelope by the contract chain h_aa -> 2-8 Hz ->
    rms_norm over the whole stream, in this order, exactly and against an independent scipy chain."""
    from fixtures import ENV_SOURCE_FORM, NO_SOURCE, READ_MASKED, array_sha256
    m = fx["manifest"]
    want = {"sparrkulee": ("authors' pipeline", "broadband", 64), "fau": ("authors' 1 kHz envelope", "0.3-9 Hz", 128),
            "dtu": ("ours: abs(Hilbert) of the original unequalised 16 kHz audio", "broadband", 128),
            "federici": ("AudioEnvSp", "not high-passed", 100)}                    # design §2.3 Sources
    assert ENV_SOURCE_FORM == {"sparrkulee": "file", "fau": "array", "dtu": "array", "federici": "array"}
    sos = signal.butter(4, [2, 8], btype="band", fs=64, output="sos")             # independent of contract.env_sos
    env_src, rich_src = [], []
    for c, info in m["cohorts"].items():
        origin, band_, fs = want[c]
        streams, rich, src = _streams(fx, c), _streams(fx, c, "rich_streams"), fx["sources"][c]
        env, rich_arr = _npy(fx, c, info["env"], mmap=False), _npy(fx, c, info["rich"], mmap=False)
        assert [s["name"] for s in src] == [st["name"] for st in streams] == [r["name"] for r in rich]
        assert [r["stream"] for r in rich] == [st["stream"] for st in streams] == list(range(len(streams)))
        for st, r, s in zip(streams, rich, src):
            raw = s["env"]
            assert origin in st["origin"] and st["origin"].endswith("(synthetic stand-in)") and band_ in st["original_band"]
            assert st["fs_source"] == s["fs"] == fs and raw.dtype == np.float64 and raw.ndim == 1 and not raw.flags.writeable
            chain = ([f"aa_fir_{fs}"] if fs != C.FS else []) + ["env_sos"]           # h_aa (none at 64 Hz), then the 2-8 Hz band-pass
            assert st["filter_sha256"] == {k: m["filters"][k] for k in chain} and st["nan_count"] == int(np.isnan(raw).sum()) == 0
            # the source hash, recomputed from the source: a whole file -> its bytes; an array in a container -> float64 bytes
            arr_sha = hashlib.sha256(np.ascontiguousarray(raw, dtype=np.float64).tobytes()).hexdigest()
            assert _is_sha(st["source_sha256"]) and arr_sha == array_sha256(raw)
            if ENV_SOURCE_FORM[c] == "file":
                back = np.load(io.BytesIO(s["file"]), allow_pickle=False)              # the stand-in file holds exactly the source
                assert st["source_sha256"] == hashlib.sha256(s["file"]).hexdigest() != arr_sha
                assert back.shape == (len(raw), 1) and np.array_equal(back[:, 0], raw)
            else:
                assert s["file"] is None and st["source_sha256"] == arr_sha
            env_src.append(st["source_sha256"])
            # the stored envelope: h_aa -> 2-8 Hz (sosfiltfilt, odd, padlen min(128, T - 1)) -> / RMS, exactly as recorded
            en = env[st["offset"]:st["offset"] + st["length"]]
            ref, rms = C.rms_norm(C.band(C.resample64(raw, fs), C.env_sos()[0]), return_rms=True)
            assert st["length"] == len(ref) and st["rms"] == rms and np.array_equal(en, ref.astype(np.float32))
            fr = Fraction(C.FS, fs)
            x = raw if fs == C.FS else signal.resample_poly(raw, fr.numerator, fr.denominator, window=C.aa_fir(fs, fr.numerator))
            bl = signal.sosfiltfilt(sos, x, padtype="odd", padlen=min(128, len(x) - 1))
            assert np.isclose(st["rms"], np.sqrt(np.mean(bl ** 2)), rtol=1e-12, atol=0)
            np.testing.assert_allclose(en, bl / st["rms"], rtol=0, atol=2e-6)
            if st["stream"] == 0:   # the order is observable: rms_norm before the band-pass, or the band-pass before h_aa, differs
                alts = [C.band(C.rms_norm(C.resample64(raw, fs)), C.env_sos()[0])]
                if fs != C.FS:
                    alts.append(C.rms_norm(C.resample64(C.band(raw, C.env_sos()[0]), fs)))
                assert all(np.abs(a - ref).max() > 1e-3 for a in alts)
            # the rich source hash: the waveform file (a whole file), here its stand-in bytes. build_rich.py's row rule (C7): the
            # reason is None or one of its reasons, available exactly when it is None, and source_sha256 None exactly when no
            # waveform is read (NO_SOURCE, not_nh_original included); a waveform read, then rejected or masked, keeps its sha
            assert "source_sha256" in r
            assert r["reason"] is None or r["reason"] in NO_SOURCE + READ_MASKED, r["reason"]
            assert r["available"] == (r["reason"] is None) and (r["source_sha256"] is None) == (r["reason"] in NO_SOURCE)
            if r["reason"] in NO_SOURCE:                                           # no waveform read: no sha, never available
                assert s["waveform"] is None
            else:                                                                   # read: available, or read and masked / rejected
                assert r["source_sha256"] == hashlib.sha256(s["waveform"]).hexdigest()
                block = rich_arr[st["offset"]:st["offset"] + st["length"]]
                if r["reason"] == "waveform_unavailable":
                    assert s["waveform"] == f"synthetic stand-in for the rejected source file of {c}:{r['name']}".encode()
                else:                                                               # the synthetic features, stored unless masked
                    assert len(s["waveform"]) == block.nbytes
                assert (block.tobytes() == s["waveform"]) if r["available"] else np.isnan(block).all()
                rich_src.append(r["source_sha256"])
    assert len(set(env_src)) == len(env_src) and len(set(rich_src)) == len(rich_src)   # one source per stream
    sk = {r["name"]: r for r in _streams(fx, "sparrkulee", "rich_streams")}
    assert _is_sha(sk["audiobook_2_1"]["source_sha256"]) and sk["audiobook_2_1"]["reason"] == "waveform_unavailable"   # read, rejected
    assert _is_sha(sk["podcast_2"]["source_sha256"]) and sk["podcast_2"]["reason"] == "clock_lag"                   # read, clock-masked
    assert all(r["source_sha256"] is None and r["reason"] == "no_waveform" for r in _streams(fx, "federici", "rich_streams"))
    fau = {r["name"]: r for r in _streams(fx, "fau", "rich_streams")}
    assert fau["215/distractor"]["source_sha256"] is None and fau["215/attended"]["reason"] == "no_waveform_competing_talker"
    assert all(_is_sha(fau[f"{code}/attended"]["source_sha256"]) for code in ("111", "124"))


def test_fixture_rich_reasons_match_build_rich(fx):
    """Design §2.15 / §6.2 C7: the fixture's rich-reason vocabulary is C7's (prior33.build_rich REASONS) for a cache root. NO_SOURCE
    (no waveform read: source_sha256 None, never available) holds every no-source reason of build_rich except its dry-run-only
    not_selected_dry_run, which never reaches a cache root, and so includes not_nh_original (a DTU stream heard only by HI
    listeners); READ_MASKED (read, then rejected or clock-masked: source_sha256 kept) is build_rich's. Every fixture rich row obeys
    build_rich's own row rule, the fixture exercises every other reason, and its stream builder treats not_nh_original as a
    no-source reason (no fixture stream carries it, so a scratch DTU builder is used and the fixture's outputs stay unchanged).
    The builder refuses, before it records anything, a row that the rule forbids: no rich features and no reason (it would be
    unavailable without a reason), clock_lag without features (only computed features are clock-masked), a reason not C7's."""
    from auditory_alignment_v3.prior33 import build_rich as B
    from fixtures import NO_SOURCE, READ_MASKED, _Streams
    dry = {"not_selected_dry_run"}
    assert dry <= set(B.NO_SOURCE) and set(NO_SOURCE) == set(B.NO_SOURCE) - dry and set(READ_MASKED) == set(B.READ_MASKED)
    assert set(B.REASONS) == set(NO_SOURCE) | set(READ_MASKED) | dry and not set(NO_SOURCE) & set(READ_MASKED)
    assert not any(B.REASONS[k][0] for k in NO_SOURCE) and all(B.REASONS[k][0] for k in READ_MASKED)   # (waveform read, meaning)
    seen = set()
    for c in fx["manifest"]["cohorts"]:
        for r in _streams(fx, c, "rich_streams"):                                  # build_rich raises on a row that breaks this
            assert r["reason"] is None or (r["reason"] in B.REASONS and r["reason"] not in dry), r
            assert (r["source_sha256"] is None) == (r["reason"] in B.NO_SOURCE) and r["available"] == (r["reason"] is None), r
            seen.add(r["reason"])
    assert seen == {None} | set(READ_MASKED) | (set(NO_SOURCE) - {"not_nh_original"})
    st = _Streams("dtu", fx["manifest"]["filters"])
    raw = np.random.default_rng(0).standard_normal(512)                           # 4 s at the DTU source rate (128 Hz)
    sid = st.add("woa_only", raw, "attended", None, 0, reason="not_nh_original")
    r = st.rich_rows[sid]
    assert r["source_sha256"] is None and not r["available"] and r["extractor"] is None and st.sources[sid]["waveform"] is None
    assert np.isnan(st.rich[sid]).all() and _is_sha(st.rows[sid]["source_sha256"])   # the envelope itself is still read
    for bad in ({}, {"reason": "clock_lag"}, {"reason": "not_a_c7_reason"}, {"rich": np.zeros((4, 5), np.float32), "reason": "x"}):
        with pytest.raises(AssertionError):
            st.add("refused", raw, "attended", None, 0, **bad)
    assert len(st.rows) == len(st.rich_rows) == len(st.rich) == len(st.sources) == sid + 1   # nothing recorded for them


def test_fixture_standardiser_rms_about_zero(fx):
    """Design §2.3 (contract.py docstring, "Standardiser"): sigma is the RMS about 0, not the SD about the mean, over the unique
    (presentation, tick) windows of the SparrKULee donor-fit pool, each window once whatever its listener count; mu is fixed at 0
    (stored as zeros) and the sample mean is recorded only as mu_estimate. The rich sigma_ss / sigma_sc follow the same rule."""
    m = fx["manifest"]; pres = m["presentations"]; S = m["segments"]["sparrkulee"]; pool = m["pools"]["core"]["sparrkulee"]
    st, rs = _streams(fx, "sparrkulee"), _streams(fx, "sparrkulee", "rich_streams")
    env = _npy(fx, "sparrkulee", "env_f32.npy", mmap=False).astype(np.float64)
    rich = _npy(fx, "sparrkulee", "rich_f32.npy", mmap=False).astype(np.float64)
    u = sorted({(S["presentation"][r], S["s"][r]) for r in pool})
    win = {(p, s): st[pres[p]["stream"]]["offset"] + s + C.TICK_OFFS[:, None] + np.arange(C.N_TGT) for p, s in u}
    Y = np.concatenate([env[win[k]] for k in u])                                     # [n_windows, 8]
    sd = m["standardiser"]; sigma, mu = np.asarray(sd["sigma"]), Y.mean(0)
    assert sd["n_windows"] == len(Y) == C.SEG_TICKS * len(u) < C.SEG_TICKS * len(pool)      # each window once, not once per listener
    assert np.allclose(sigma, np.sqrt((Y ** 2).mean(0)), rtol=1e-12, atol=0) and sd["mu"] == [0.0] * C.N_TGT
    assert np.allclose(sd["mu_estimate"], mu, rtol=1e-9, atol=1e-15) and np.allclose(sigma ** 2, Y.var(0) + mu ** 2, rtol=1e-9)
    assert (sigma > Y.std(0)).all() and np.isclose(sd["abs_mu_over_sigma_max"], np.abs(mu / sigma).max())   # RMS about 0, not the SD
    ur = [k for k in u if rs[pres[k[0]]["stream"]]["available"]]
    R = np.stack([rich[win[k]] for k in ur]).reshape(-1, C.N_TGT, len(C.RICH_COLS))   # [n, 8, 5]
    Rss, Rsc = R[..., :4].reshape(len(R), -1), R[..., 4]                               # y_ss sample-major [n, 32]; y_sc [n, 8]
    r = m["rich"]
    assert r["n_windows"] == len(R) < len(Y) and np.isfinite(R).all()
    for name, A in (("ss", Rss), ("sc", Rsc)):
        s_ = np.asarray(r[f"sigma_{name}"])
        assert np.allclose(s_, np.sqrt((A ** 2).mean(0)), rtol=1e-12, atol=0) and (s_ > A.std(0)).all()
        assert np.allclose(r[f"mu_estimate_{name}"], A.mean(0), rtol=1e-9, atol=1e-15)


def test_fixture_scale_argument(fx, tmp_path):
    """make_synthetic_manifest(tmp, scale=1) is the default build, byte for byte; scale must be an integer in 1..MAX_SCALE, checked
    before anything is written."""
    from fixtures import MAX_SCALE
    fx1 = make_synthetic_manifest(tmp_path / "s1", scale=1)
    assert fx1["manifest_sha256"] == fx["manifest_sha256"] and fx1["scale"] == fx["scale"] == 1 and "fixture_scale" not in fx1["manifest"]
    for c, info in fx["manifest"]["cohorts"].items():
        for f in (info["table"], info["streams"], info["rich_streams"], info["env"], info["rich"], *info["caches"].values()):
            assert _read(os.path.join(fx["root"], info["dir"], f), "rb") == _read(os.path.join(fx1["root"], info["dir"], f), "rb"), (c, f)
    for bad, err in ((0, ValueError), (MAX_SCALE + 1, ValueError), (-1, ValueError), (2.5, TypeError), ("4", TypeError), (True, TypeError),
                     (None, TypeError)):
        with pytest.raises(err):
            make_synthetic_manifest(tmp_path / f"bad_{bad}", scale=bad)
        assert not os.path.exists(tmp_path / f"bad_{bad}")


def _design_batch(m, stratum, excluded, index, rng):
    """A reference §2.6 draw from one stratum (not the M3 sampler): participant-balanced (a uniform participant, then a uniform
    segment of it) with no repeated (presentation, s); a uniform valid partner per segment (never self, never an HC / HC-v twin);
    8 anchors j = phi + 31 a shared by both listeners. Returns [(row, partner row, j)] for 32 segments."""
    c = "fau" if stratum == "fau_cs" else stratum
    S = m["segments"][c]; groups, twins = index[c]
    rows = m["pools"]["csx"]["fau_cs"] if stratum == "fau_cs" else m["pools"]["core"][stratum]
    by_part = {}
    for r in rows:
        if S["presentation"][r] not in excluded:
            by_part.setdefault(S["participant"][r], []).append(r)
    parts, picked, used = sorted(by_part), [], set()
    for _ in range(200_000):
        p = parts[int(rng.integers(len(parts)))]; r = by_part[p][int(rng.integers(len(by_part[p])))]
        if (S["presentation"][r], S["s"][r]) not in used:
            used.add((S["presentation"][r], S["s"][r])); picked.append(r)
            if len(picked) == 32:
                break
    assert len(picked) == 32, (stratum, len(picked))
    out = []
    for r in picked:
        cand = [q for q in groups[(S["presentation"][r], S["s"][r], S["role"][r])]
                if S["participant"][q] != S["participant"][r] and (S["participant"][r], S["participant"][q]) not in twins]
        assert len({S["participant"][q] for q in cand}) == S["n_partners"][r] >= 1
        out.append((r, cand[int(rng.integers(len(cand)))], int(rng.integers(C.ANCHOR_STEP)) + C.ANCHOR_STEP * np.arange(C.N_ANCHORS)))
    return out


def test_fixture_scale4_design_batches(fx4):
    """scale=4: every stratum of every donor set and block holds a §2.6 design batch: 32 listener segments with distinct
    (presentation, s), each with a valid partner, x 8 anchors -> 256 anchors and 512 EEG windows [C, 38] inside the guards, 256
    targets [8] inside the 41-sample edges, and one positive (equal key) per anchor across the two listeners."""
    m = fx4["manifest"]; pres = m["presentations"]; rng = np.random.default_rng(0)
    assert fx4["scale"] == 4 and m["fixture_scale"] == 4
    index = {}
    for c in m["cohorts"]:
        S, groups = m["segments"][c], {}
        for r in range(len(S["s"])):
            groups.setdefault((S["presentation"][r], S["s"][r], S["role"][r]), []).append(r)
        index[c] = (groups, {(a, b) for co, a, b in m["partner_exclusions"] if co == c} |
                    {(b, a) for co, a, b in m["partner_exclusions"] if co == c})
    tabs = {c: _table(fx4, c)[m["cohorts"][c]["items"]] for c in m["cohorts"]}
    caches = {c: _npy(fx4, c, m["cohorts"][c]["caches"]["A"]) for c in m["cohorts"]}
    envs, streams = {c: _npy(fx4, c, m["cohorts"][c]["env"]) for c in m["cohorts"]}, {c: _streams(fx4, c) for c in m["cohorts"]}
    seen, n_draws = set(), 0
    for target, blocks in m["donor_sets"].items():
        for b, v in blocks.items():
            for stratum in v["strata"]:
                c = "fau" if stratum == "fau_cs" else stratum; S = m["segments"][c]; g0, g1 = C.GUARDS[c]
                ex = set(v["excluded_presentations"][stratum])
                rows = m["pools"]["csx"]["fau_cs"] if stratum == "fau_cs" else m["pools"]["core"][stratum]
                assert len({(S["presentation"][r], S["s"][r]) for r in rows if S["presentation"][r] not in ex}) >= 32, (target, b, stratum)
                X1, X2, Y, K1, K2 = [], [], [], [], []
                for r, q, j in _design_batch(m, stratum, ex, index, rng):
                    p, s, i = S["presentation"][r], S["s"][r], C.TICK_OFFS[j]
                    assert p not in ex and S["role"][r] == "fit" and S["kind"][r] == ("cs" if stratum == "fau_cs" else "ss")
                    assert S["participant"][q] != S["participant"][r] and S["presentation"][q] == p and S["s"][q] == s
                    for row, X, K in ((r, X1, K1), (q, X2, K2)):
                        it = tabs[c][S["piece"][row]]
                        assert it["presentation"] == p and s in it["segment_starts"] and it["participant"] == S["participant"][row]
                        w = s + i[:, None] + np.arange(C.L_IN)                       # piece samples of the 8 windows [8, 38]
                        assert w.min() >= g0 and w.max() < it["T_eeg"] - g1
                        X.append(np.asarray(caches[c][it["row_offset"] + w], dtype=np.float32).transpose(0, 2, 1))
                        K.append(C.pack_key(pres[p]["family"], p, pres[p]["family_offset"] + s + i))
                    st = streams[c][pres[p]["stream"]]; t = s + i[:, None] + np.arange(C.N_TGT)
                    assert t.min() >= C.ENV_EDGE and t.max() < st["length"] - C.ENV_EDGE
                    Y.append(np.asarray(envs[c][st["offset"] + t], dtype=np.float32))
                X1, X2, Y, K1, K2 = (np.concatenate(a) for a in (X1, X2, Y, K1, K2))
                n_ch = m["cohorts"][c]["n_ch"]
                assert X1.shape == X2.shape == (256, n_ch, C.L_IN) and Y.shape == (256, C.N_TGT)          # 512 EEG windows, 256 targets
                assert np.array_equal(K1, K2) and len(np.unique(K1)) == 256                                # one positive per anchor
                assert np.isfinite(X1).all() and np.isfinite(X2).all() and np.isfinite(Y).all() and np.abs(X1).max() > 0
                seen.add(stratum); n_draws += 1
    assert seen == {"sparrkulee", "fau", "dtu", "federici", "fau_cs"} and n_draws == sum(len(v["strata"]) for bl in m["donor_sets"].values()
                                                                                      for v in bl.values())


def test_fixture_scale4_invariants(fx, fx4):
    """scale=4 only lengthens the pieces and streams: the structural checks above hold as at scale 1, and every participant,
    presentation, family, cell, mask, exclusion and data-use case is unchanged."""
    for check in (test_fixture_files_caches_and_normalisation, test_fixture_keys_and_family_clocks, test_fixture_data_use_cases,
                  test_fixture_cells, test_fixture_rich_block, test_fixture_stream_provenance, test_fixture_standardiser_rms_about_zero):
        check(fx4)
    m1, m4 = fx["manifest"], fx4["manifest"]
    for k in ("schema", "contract", "constants", "filters", "target_contract", "projection", "vocab", "aliases", "montages", "families",
              "presentations", "shared_audio", "partner_exclusions", "seen", "coverage", "cells", "exclusions", "unused",
              "dtu_reconciliation"):
        assert (m4[k] == m1[k]) == (k != "target_contract"), k                        # target_contract hashes sigma, which moves
    assert set(m1) <= set(m4) and set(m4) - set(m1) == {"fixture_scale"} and fx4["truth"] == fx["truth"]
    assert [{k: v for k, v in o.items() if k != "r"} for o in m4["overlap"]] == [{k: v for k, v in o.items() if k != "r"} for o in m1["overlap"]]
    vary = {"T_eeg", "T_env", "segment_starts", "row_offset", "source_sha256"}
    for c, info in m1["cohorts"].items():
        t1, t4 = _table(fx, c), _table(fx4, c)
        assert len(t1[info["items"]]) == len(t4[info["items"]]) and len(t1["participants"]) == len(t4["participants"])
        for a, b in zip(t1[info["items"]], t4[info["items"]]):
            assert {k: v for k, v in a.items() if k not in vary} == {k: v for k, v in b.items() if k not in vary}
            extra = 64 if "structural_anomaly_unverified_clock" in a.get("flags", ()) else 0
            assert b["T_eeg"] - extra == 4 * (a["T_eeg"] - extra) and b["T_env"] == 4 * a["T_env"]
            assert len(b["segment_starts"]) > len(a["segment_starts"]) or a["row_offset"] is None
        for a, b in zip(t1["participants"], t4["participants"]):
            assert {k: v for k, v in a.items() if k not in ("mu", "sd_prez")} == {k: v for k, v in b.items() if k not in ("mu", "sd_prez")}
        for a, b in zip(_streams(fx, c), _streams(fx4, c)):
            drop = ("offset", "length", "rms", "source_sha256")
            assert {k: v for k, v in a.items() if k not in drop} == {k: v for k, v in b.items() if k not in drop}
            assert b["length"] == 4 * a["length"]
        for a, b in zip(_streams(fx, c, "rich_streams"), _streams(fx4, c, "rich_streams")):
            assert {k: v for k, v in a.items() if k != "source_sha256"} == {k: v for k, v in b.items() if k != "source_sha256"}
        s1, s4 = fx["sources"][c], fx4["sources"][c]                              # the same sources, 4 times longer
        assert [(a["name"], a["fs"], a["file"] is None, a["waveform"] is None) for a in s1] == \
            [(b["name"], b["fs"], b["file"] is None, b["waveform"] is None) for b in s4]
        assert all(len(b["env"]) == 4 * len(a["env"]) for a, b in zip(s1, s4))
    for blk, pools in m1["pools"].items():
        assert all(len(m4["pools"][blk][c]) > len(rows) for c, rows in pools.items())
    for t, blocks in m1["donor_sets"].items():
        for b, v in blocks.items():
            w = m4["donor_sets"][t][b]
            assert w["strata"] == v["strata"] and w["excluded_presentations"] == v["excluded_presentations"]
            assert all(n4 > n1 for n1, n4 in zip(v["n_segments"], w["n_segments"]))
    assert m4["budget"]["N_SK"] > m1["budget"]["N_SK"] and m4["hc_hcv_excluded_pairs"] > m1["hc_hcv_excluded_pairs"] > 0
    assert {c: (v["supported"], v.get("mode"), v.get("donors")) for c, v in m4["mode_c"].items()} == \
        {c: (v["supported"], v.get("mode"), v.get("donors")) for c, v in m1["mode_c"].items()}


# ---------------------------------------------------------------------------------------------------------- source hashes, regression pin
def test_fixture_source_hash_rule_and_fingerprint():
    """The array branch of the source-hash rule (fixtures.py docstring, "Source hashes") depends on the values only: the float64
    C-order bytes of the flattened array, whatever the stored dtype, byte order, shape or memory order. The regression fingerprint
    ignores last-bit noise and the chunking of its sums, and moves with a reordering, a sign change, a value change of 1e-6, a
    non-finite value, a dtype, or any id, key or string (sha256 strings are masked: what they hash is fingerprinted itself)."""
    from fixtures import _fp_array, _fp_json, array_sha256, npy_bytes
    rng = np.random.default_rng(20261017)
    x = rng.standard_normal(1200)
    x32 = x.astype(np.float32)
    assert array_sha256(x) == hashlib.sha256(x.tobytes()).hexdigest() != array_sha256(x32)
    assert array_sha256(x32) == hashlib.sha256(x32.astype(np.float64).tobytes()).hexdigest() != hashlib.sha256(x32.tobytes()).hexdigest()
    assert array_sha256(x) == array_sha256(x.reshape(-1, 1)) == array_sha256(np.asfortranarray(x.reshape(30, 40))) == \
        array_sha256(x.astype(">f8"))
    b = npy_bytes(x[:, None])
    assert b == npy_bytes(x[:, None]) and np.array_equal(np.load(io.BytesIO(b), allow_pickle=False), x[:, None])
    a = rng.standard_normal((300, 7))
    fa = _fp_array(a)
    assert _fp_array(np.nextafter(a, np.inf)) == fa == _fp_array(a, chunk=64) == _fp_array(np.asfortranarray(a))
    nan = a.copy(); nan[3, 4] = np.nan
    for other in (a[::-1], np.roll(a, 1, axis=0), -a, a * (1 + 1e-6), nan, a.astype(np.float32)):
        assert _fp_array(other) != fa
    j = {"a": [0.1, 2, "x", None, True], "b": {"c": 1 / 3}, "sha": "ab" * 32}
    assert _fp_json(j) == _fp_json({"a": [float(np.nextafter(0.1, 1)), 2, "x", None, True], "b": {"c": 1 / 3}, "sha": "cd" * 32})
    for other in ({**j, "a": [0.1000001, 2, "x", None, True]}, {**j, "a": [0.1, 3, "x", None, True]}, {**j, "a": [0.1, 2, "y", None, True]},
                  {**j, "b": {"d": 1 / 3}}, {**j, "sha": "synthetic-fixture"}):
        assert _fp_json(other) != _fp_json(j)


SCALE1_PIN = {   # fixtures.fingerprint() of make_synthetic_manifest(tmp) (scale 1), pinned 2026-10-17 in eeg2025
    "numpy": "2.4.4", "scipy": "1.17.0",
    "manifest_sha256": "2aeeac92fde2b51550eb7738004a2c6f4124cd9c49259527836b06f4b03c12fb",   # exact bytes: checked as a warning only
    "fingerprint": {
        "P_32x8_seed20261016_f32.npy": "8010263dede50c0f",
        "P_sc_32x8_seed20261018_f32.npy": "6959849b2b4713f9",
        "P_ss_32x32_seed20261017_f32.npy": "5bb21bd1c3f825a7",
        "dtu/eeg_f16_tmajor.npy": "3f91aefe8cd78c20",
        "dtu/eeg_raw_f16_tmajor.npy": "47609cf29463d918",
        "dtu/env_f32.npy": "e858f1230cc1a0a0",
        "dtu/pieces.json": "53c30f4e211731bf",
        "dtu/rich_f32.npy": "a2867f3fdb3e31d2",
        "dtu/rich_streams.json": "1390fe93b2256592",
        "dtu/streams.json": "fb5ca58a9bb70206",
        "fau/eeg_f16_tmajor.npy": "123f5a56413528e3",
        "fau/eeg_noica_z_f16_tmajor.npy": "84c9fb1ed4af82af",
        "fau/eeg_raw_f16_tmajor.npy": "07db9e7967f9dfa2",
        "fau/env_f32.npy": "7b9a58258187cff5",
        "fau/pieces.json": "9b0c7e4b2e303f6a",
        "fau/rich_f32.npy": "a682eec042de5517",
        "fau/rich_streams.json": "8cb9e09c577c5eae",
        "fau/streams.json": "fc548deebb50ef50",
        "federici/eeg_f16_tmajor.npy": "bc073c29504644b9",
        "federici/eeg_raw_f16_tmajor.npy": "6eaf81e1b21d96d3",
        "federici/env_f32.npy": "1995f00003ba28be",
        "federici/pieces.json": "4e55caeb9d9c595f",
        "federici/rich_f32.npy": "1abcecc4786341cc",
        "federici/rich_streams.json": "82c0e91a985f36a9",
        "federici/streams.json": "c5d8f70da2ea392d",
        "manifest.json": "6660970036dadd6d",
        "raw/sparrkulee/sub-019_ses-x_task-listeningActive_run-01_desc-preproc-audio-podcast_1_eeg.npy": "508c88a08e187ef8",
        "rich_pca4_f64.npy": "999d0a3aff729926",
        "sparrkulee/eeg_f16_tmajor.npy": "6ae2d5de1d31d3b0",
        "sparrkulee/env_f32.npy": "429dc6036c187d2a",
        "sparrkulee/rich_f32.npy": "2ed23449a6def2be",
        "sparrkulee/rich_streams.json": "70bf56ed265b5eac",
        "sparrkulee/runs.json": "3b30506825b165e2",
        "sparrkulee/streams.json": "895d5454f768d836",
    },
}


def test_fixture_scale1_pinned(fx):
    """Regression pin of the default (scale-1) build in eeg2025 (numpy 2.4.4, scipy 1.17.0; skipped in another environment): the
    fixtures.fingerprint() of all 34 files. It ignores float rounding, because the build's last bits may follow the CPU's BLAS and
    SIMD kernels (np.convolve, QR), but it moves with any change of random draws, values, shapes, ids or strings, e.g. an edit that
    shifts the random draw order. The exact manifest sha256 recorded with the pin carries those last bits: a mismatch there is a
    warning, not a failure. After a deliberate change of the scale-1 output, re-pin SCALE1_PIN["fingerprint"] with the dict this
    test prints on failure (or fixtures.fingerprint(make_synthetic_manifest(tmp)["root"]))."""
    import scipy
    from fixtures import fingerprint
    if (np.__version__, scipy.__version__) != (SCALE1_PIN["numpy"], SCALE1_PIN["scipy"]):
        pytest.skip(f"pinned in numpy {SCALE1_PIN['numpy']} / scipy {SCALE1_PIN['scipy']}, here {np.__version__} / {scipy.__version__}")
    assert fx["scale"] == 1 and "fixture_scale" not in fx["manifest"]
    got, want = fingerprint(fx["root"]), SCALE1_PIN["fingerprint"]
    changed = sorted(k for k in set(got) | set(want) if got.get(k) != want.get(k))
    assert not changed, f"the scale-1 build changed in {changed}; re-pin only if the change is intended: {got}"
    if fx["manifest_sha256"] != SCALE1_PIN["manifest_sha256"]:
        warnings.warn(f"scale-1 manifest sha256 {fx['manifest_sha256'][:16]}... differs from the pinned {SCALE1_PIN['manifest_sha256'][:16]}... "
                      "while every fingerprint matches: float rounding only (another CPU's BLAS / SIMD kernels)")
