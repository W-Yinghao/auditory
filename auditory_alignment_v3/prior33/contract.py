"""E34_PUBLIC_PRIOR execution contract aln33_env64_125ms_v1 (private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.1-§2.5,
§2.13; inherited PUBLIC_PRIOR_EXECUTION_v3_3.md §3 and public_prior_v3_3.yaml data_contract): the 64 Hz grid, ticks, segments
and windows, the fixed filters and resampling, the private 64 Hz input, cross-person keys and the electrode vocabulary.
numpy/scipy only.

Grid: tick k (20 ms) -> i_k = (64 k + 25) // 50 = round(1.28 k), counted from the piece's physical origin (EEG sample 0 =
envelope sample 0); no stride is accumulated. A 5 s segment is 250 ticks from a start s = 0 (mod 32); since i_{k+25} = i_k + 32,
every segment shares TICK_OFFS = i_0..i_249 (0..319). Windows (half-open): EEG x_k = eeg[s + i_k : s + i_k + 38] (593.75 ms),
target y_k = env[s + i_k : s + i_k + 8] (125 ms).

Interpretations where the design gives only a name (each is also listed as a deviation in the M1 summary):
- tick(k) takes integer ticks k >= 0 (the design defines ticks from the origin); negative or non-integer ticks raise.
- segment_starts(..., onset): onset in seconds from the piece origin (distractor / masker onset); the first start is the smallest
  multiple of 32 >= max(start guard, (onset + 1.7) * 64), with a 1e-9 tolerance against float noise; returns int64 starts.
- resample64(x, fs_in) requires an integer fs_in >= 64: an upsampling ratio would only add images between fs_in / 2 and 26 Hz
  (inherited contract §3: 不靠上采样生成不存在频率信息), so fs_in < 64 raises ValueError; no cohort needs it.
- resample64, band and rms_norm take an optional axis (default -1: time last). band's padlen is the contract padlen of the
  filter it is given (env 128, EEG 256, LP20 the scipy default), capped at T - 1; any other filter needs an explicit padlen.
- rms_norm(e, return_rms=True) also returns the RMS, which the manifest records per stream.
- pack_key / unpack_key are vectorised over integer arrays; unpack_key also takes torch tensors (duck-typed). Keys must be 64-bit
  integers (numpy int64 / uint64, torch.int64): a narrower dtype raises TypeError, because a key cast to int32 decodes as family 0.
  A bit-budget violation or a negative key raises AssertionError explicitly (not an assert statement: python -O cannot strip it).
- canonical(name): whitespace-stripped, case-insensitive match against VOCAB and ALIASES; any other name raises KeyError.
- private_to64 and z64_per_child compute in float64 and return float32; channels on axis -2, time last.
- env_sos(), eeg_sos() and lp20_sos() return the pair (sos, sha256), not the bare coefficients: sos is the float64 [n_sections, 6]
  array of signal.butter(..., fs=64, output='sos') and sha256 the hex digest of its float64 C-order bytes (the value filter_shas()
  and the manifest record; FILTER_SHA16 holds the prefixes). Callers take [0] for the coefficients, e.g. band(x, env_sos()[0]).
  band's padlen lookup, filter_shas(), the shared test fixture and the builders depend on this form, so it is kept as the interface.

Standardiser (§2.3; fitted once by the manifest builder C6 and applied by model.SharedFixedHead, so no function here): targets enter
as y / sigma with mu fixed at 0. sigma[d] = sqrt(mean_w y_w[d]^2) is the RMS about 0 over the unique (presentation, tick) windows
of the eligible SparrKULee donor-fit anchors (each window once, whatever its listener count); it is not the SD about the sample
mean. The sample mean is recorded only as mu_estimate (C6 asserts |mu_estimate| / sigma < 0.05 as an engineering check), and the
manifest stores mu as zeros. Because mu = 0, a stream scaled by c > 0 maps to c (y / sigma), which the head's L2 normalisation
removes: the per-stream RMS of rms_norm (also an RMS about 0) cannot change any target-side output. The rich sigma_ss [32] and
sigma_sc [8] follow the same rule on the rich windows.

Design-text corrections (measured here on the specified filters; the code follows the specified chain, the text needs a note):
- §2.3 / §7.1 3(a): the 2-8 Hz zero-phase impulse response holds 99.895 % of its energy within +-41 samples (sosfiltfilt,
  padtype 'odd', centred impulse); >= 99.9 % is first reached at +-42. ENV_EDGE stays 41 as designed (whether the guard should be
  42 is the researcher's call); test_contract asserts the measured values.
- §2.1 SparrKULee: the 1-20 Hz response holds 99.988 % (not 99.99 %) within +-64 samples; 99.99 % is first reached at +-73.
- §2.1 private epochs: with the 20 Hz low-pass added in revision F23 the synthetic 3 Hz cosine gives 1.00020 at index 32, a
  3.11 % maximum window error (at index 69) and 0.032 % over the first 24 samples. The quoted 1.0003 / 1.3 % / 0.03 % are the
  values of reflect pad + h_aa without the low-pass (1.00029 / 1.31 % / 0.029 %).
- §2.1 h_aa table: the 100 -> 64 Hz stopband from 30 Hz is -59.68 dB (stated <= -59.7 dB); 128 -> 64 -60.38 dB, 250 -> 64
  -59.80 dB. The §7.1 bound of -59 dB holds for all three.
"""
from __future__ import annotations

import functools
import hashlib
from fractions import Fraction

import numpy as np
from scipy import signal

CONTRACT = "aln33_env64_125ms_v1"
FS = 64
TICK_S = 0.020
L_IN = 38                                   # EEG window samples
N_TGT = 8                                   # target samples
SEG_TICKS, SEG_STEP, SEG_ALIGN = 250, 320, 32
ENV_EDGE = 41                               # target edge guard at both ends of every stream
NEIGHBOR = 128                              # NCE family-clock mask |ds| <= 128 samples (2.000 s, inclusive)
TAU = 0.1
CS_LEAD_S = 1.7                             # competing-talker segments start >= distractor / masker onset + 1.7 s
GUARDS = {"sparrkulee": (128, 128), "fau": (157, 157), "dtu": (41, 41), "federici": (41, 41)}   # start / end, 64 Hz samples
N_ANCHORS, ANCHOR_STEP = 8, 31              # training anchors j = phi + 31 a, a = 0..7, phi ~ U{0..30}

# private_bdf epochs (hc.load_children: [n, 20, 200] at 250 Hz, onset at index 50)
FS_PRIVATE, PRIVATE_EPOCH, PRIVATE_ONSET, PRIVATE_PAD = 250, 200, 50, 75
ONSET64, PRIVATE_N64 = 32, 90
PRIVATE_WIN = (ONSET64, ONSET64 + L_IN)     # [32, 70)

# anti-alias FIR and Butterworth filters (§2.1, §2.3)
AA_CUTOFF, AA_PASS, AA_STOP, AA_ATTEN = 26.0, 22.0, 30.0, 60.0
ENV_BAND, EEG_BAND, LP_PRIVATE, BUTTER_ORDER = (2.0, 8.0), (1.0, 20.0), 20.0, 4
ENV_PADLEN, EEG_PADLEN = 128, 256
AA_TAPS = {128: 61, 100: 727, 250: 3627}
FILTER_SHA16 = {"env_sos": "a5457201db325d21", "eeg_sos": "e014c236c041a9df", "lp20_sos": "a9f752965a43ba97",
                "aa_fir_128": "b0fb5a2b6761efa3", "aa_fir_100": "fd778051ceda90d8", "aa_fir_250": "e0d15bfab3fc284a"}

# keys (§2.5): key = (family << 40) | (presentation << 24) | s
FAMILY_BITS, PRES_BITS, S_BITS = 23, 16, 24
FAMILY_SHIFT, PRES_SHIFT = PRES_BITS + S_BITS, S_BITS
PRES_MASK, S_MASK = (1 << PRES_BITS) - 1, (1 << S_BITS) - 1

# seeds
PROJ_SEED = 20261016                        # P = audio_targets.semi_orthogonal(32, 8, PROJ_SEED), stored once by the manifest builder
P_FILE, P_SHAPE, P_SHA16 = "P_32x8_seed20261016_f32.npy", (32, 8), "706c4ff4441f4940"   # sha256 of the float32 bytes
RICH_SEEDS = {"ss": 20261017, "sc": 20261018}   # P_ss = semi_orthogonal(32, 32, .), P_sc = semi_orthogonal(32, 8, .)
RICH_P_FILE = {"ss": "P_ss_32x32_seed20261017_f32.npy", "sc": "P_sc_32x8_seed20261018_f32.npy"}
RICH_P_SHAPE = {"ss": (32, 32), "sc": (32, 8)}
RICH_COLS = ("ss0", "ss1", "ss2", "ss3", "sc")   # rich_f32.npy [M, 5]: PCA-4 spectral structure, then spectral change (flux)
RICH_DIMS = {"ss": 4, "sc": 1}                  # y_ss = rich[i_k:i_k+8, :4] (8 x 4 -> 32, sample-major); y_sc = rich[i_k:i_k+8, 4]
BRIDGE_SEED, TAU_POOL_SEED, FOLD_SEED = 20261016, 20261017, 20261005
BREADTH_SEED, PANEL_SEEDS = 3401, (3407, 3413)
XM_SEED_OFFSET, CAL_SEED_OFFSET = 7, 99     # derangement stream donor_seed + 7; CS bandwidth calibration stream donor_seed + 99
READOUT_SEED_OFFSETS = (5, 98, 99, 1000)    # target_seed + {5, 98, 99, 1000}

# zero-shot access modes (§2.13)
ZS_PREFIX = "zero_shot__no_target_supervised_fit"
ZS_SUFFIX = {"A": "__fixed_input_preprocessing", "B": "__fau_noica_target_z", "C": "__source_statistics_only",
             "C_partial": "__source_statistics_partial"}
ZS_MODE_NAME = {m: ZS_PREFIX + s for m, s in ZS_SUFFIX.items()}
ZS_COHORTS = {"A": ("fau", "dtu", "federici"), "B": ("fau",), "C": ("fau", "dtu"), "C_partial": ("federici",)}
CACHE_FILE = {"A": "eeg_f16_tmajor.npy", "B": "eeg_noica_z_f16_tmajor.npy", "C": "eeg_raw_f16_tmajor.npy",
              "C_partial": "eeg_raw_f16_tmajor.npy"}

# electrode vocabulary (§2.4): BioSemi-64 in the SparrKULee / DTU row order, then the six extra 10-10 names
BIOSEMI64 = ("Fp1", "AF7", "AF3", "F1", "F3", "F5", "F7", "FT7", "FC5", "FC3", "FC1", "C1", "C3", "C5", "T7", "TP7", "CP5", "CP3",
             "CP1", "P1", "P3", "P5", "P7", "P9", "PO7", "PO3", "O1", "Iz", "Oz", "POz", "Pz", "CPz", "Fpz", "Fp2", "AF8", "AF4", "AFz",
             "Fz", "F2", "F4", "F6", "F8", "FT8", "FC6", "FC4", "FC2", "FCz", "Cz", "C2", "C4", "C6", "T8", "TP8", "CP6", "CP4", "CP2",
             "P2", "P4", "P6", "P8", "P10", "PO8", "PO4", "O2")
VOCAB = BIOSEMI64 + ("F9", "F10", "TP9", "TP10", "FT9", "FT10")
VOCAB_INDEX = {n: i for i, n in enumerate(VOCAB)}
ALIASES = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8",     # legacy 10-20 names (private HA_CHANNELS)
           "P07": "PO7", "P03": "PO3"}                         # SparrKULee BDF label typos (sub-015..018 headers only)
_CANON = {**{n.casefold(): n for n in VOCAB}, **{a.casefold(): c for a, c in ALIASES.items()}}


def canonical(name):
    """Contract electrode name (aliases and case normalised); a name outside the 70-name vocabulary raises KeyError."""
    s = name.decode() if isinstance(name, bytes) else str(name)
    c = _CANON.get(s.strip().casefold())
    if c is None:
        raise KeyError(f"electrode {name!r} is not in the contract vocabulary")
    return c


# cache layouts in row order (FAU / DTU / Federici: the c3_preproc_v1 cache attribute 'channels', DTU rows [:64]; private: HA_CHANNELS)
MONTAGES = {
    "sparrkulee": BIOSEMI64, "dtu": BIOSEMI64,
    "fau": ("Fp1", "Fz", "F3", "F7", "F9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2", "P4", "P8",
            "TP10", "CP6", "CP2", "C4", "T8", "F10", "FC6", "F4", "F8", "Fp2", "Cz"),
    "federici": ("Fp1", "F3", "F7", "FT9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2", "P4", "P8",
                 "TP10", "CP6", "CP2", "C4", "T8", "FT10", "FC6", "FC2", "F4", "F8", "Fp2", "Fz", "Cz"),
    "private_bdf": tuple(canonical(c) for c in ("Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4", "T3", "T4", "Pz", "P3", "P4",
                                                "T5", "T6", "Oz", "O1", "O2")),
}
PRIVATE_LAYOUT = MONTAGES["private_bdf"]
AUG_SUBSETS = {c: tuple(n for n in MONTAGES[c] if n in BIOSEMI64) for c in ("fau", "federici", "private_bdf")}   # 27 / 28 / 20
AUG_P = 0.5


# ---------------------------------------------------------------------------------------------------------- grid and segments
def tick(k):
    """i_k = (64 k + 25) // 50 (= round(1.28 k); no rounding ties): the 64 Hz sample of tick k >= 0, from the physical origin."""
    k = np.asarray(k)
    if k.dtype.kind not in "iu":
        raise TypeError(f"tick: integer ticks expected, got {k.dtype}")
    k = k.astype(np.int64)
    if k.size and k.min() < 0:
        raise ValueError("tick: ticks count from the physical origin (k >= 0)")
    return (64 * k + 25) // 50


TICK_OFFS = tick(np.arange(SEG_TICKS))
TICK_OFFS.setflags(write=False)
SPAN_EEG = int(TICK_OFFS[-1]) + L_IN        # 357
SPAN_ENV = int(TICK_OFFS[-1]) + N_TGT       # 327
S_FIRST = {c: -(-g // SEG_ALIGN) * SEG_ALIGN for c, (g, _) in GUARDS.items()}   # 128 / 160 / 64 / 64


def segment_starts(T_stream, T_eeg, cohort, onset=None):
    """Eligible 5 s segment starts of one piece: s_m = s_first + 320 m, s_first the smallest multiple of 32 >= the start guard
    (competing talker: also >= onset + 1.7 s, onset in seconds from the piece origin), kept while s_m + 357 <= T_eeg - end_guard
    and s_m + 327 <= T_stream - 41."""
    g0, g1 = GUARDS[cohort]
    lo = float(g0)
    if onset is not None:
        if not np.isfinite(onset):
            raise ValueError(f"segment_starts: non-finite onset {onset!r}")
        lo = max(lo, (float(onset) + CS_LEAD_S) * FS)
    s0 = SEG_ALIGN * int(np.ceil(lo / SEG_ALIGN - 1e-9))
    last = min(int(T_eeg) - g1 - SPAN_EEG, int(T_stream) - ENV_EDGE - SPAN_ENV)
    return np.arange(s0, last + 1, SEG_STEP, dtype=np.int64)


# ---------------------------------------------------------------------------------------------------------- resampling and filters
def _sha(a):
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64).tobytes()).hexdigest()


def aa_fir(fs_in, up):
    """h_aa: Kaiser FIR designed at fs_in * up; -6 dB at 26 Hz, passband edge 22 Hz, stopband edge 30 Hz, 60 dB, odd length."""
    fs_up = float(fs_in) * int(up)
    n, beta = signal.kaiserord(AA_ATTEN, (AA_STOP - AA_PASS) / (fs_up / 2))
    n += (n + 1) % 2
    return signal.firwin(n, AA_CUTOFF, fs=fs_up, window=("kaiser", beta))


def resample64(x, fs_in, axis=-1):
    """fs_in -> 64 Hz along the time axis: scipy.signal.resample_poly(x, up, down, window=h_aa) (scipy scales h by up); sample 0
    is preserved. Returns float64 (a copy when fs_in is already 64). fs_in < 64 raises: upsampling creates no information."""
    if fs_in <= 0 or int(fs_in) != fs_in:
        raise ValueError(f"resample64: integer sampling rate expected, got {fs_in!r}")
    if fs_in < FS:
        raise ValueError(f"resample64: {fs_in} Hz < {FS} Hz would need upsampling (inherited contract §3: no upsampled content)")
    r = Fraction(FS, int(fs_in))
    x = np.asarray(x, dtype=np.float64)
    if r == 1:
        return x.copy()
    return signal.resample_poly(x, r.numerator, r.denominator, axis=axis, window=aa_fir(int(fs_in), r.numerator))


def _butter(wn, btype):
    sos = signal.butter(BUTTER_ORDER, wn, btype=btype, fs=FS, output="sos")
    return sos, _sha(sos)


def env_sos():
    """2-8 Hz envelope band-pass butter(4, [2, 8], 'band', fs=64, output='sos').

    Returns the pair (sos, sha256): sos float64 [4, 6]; sha256 the hex digest of its float64 bytes (prefix FILTER_SHA16['env_sos']).
    The tuple is the interface other modules depend on (band(x, env_sos()[0]), filter_shas, the fixture, the builders): keep it."""
    return _butter(ENV_BAND, "band")


def eeg_sos():
    """SparrKULee 1-20 Hz EEG band-pass butter(4, [1, 20], 'band', fs=64, output='sos').

    Returns the pair (sos, sha256): sos float64 [4, 6]; sha256 the hex digest of its float64 bytes (prefix FILTER_SHA16['eeg_sos']).
    The tuple is the interface other modules depend on (band(x, eeg_sos()[0]), filter_shas, the builders): keep it."""
    return _butter(EEG_BAND, "band")


def lp20_sos():
    """Private 20 Hz low-pass butter(4, 20, 'low', fs=64, output='sos').

    Returns the pair (sos, sha256): sos float64 [2, 6]; sha256 the hex digest of its float64 bytes (prefix FILTER_SHA16['lp20_sos']).
    The tuple is the interface other modules depend on (private_to64 uses lp20_sos()[0]; filter_shas): keep it."""
    return _butter(LP_PRIVATE, "low")


@functools.lru_cache(maxsize=1)
def _contract_padlen():
    return {env_sos()[1]: ENV_PADLEN, eeg_sos()[1]: EEG_PADLEN, lp20_sos()[1]: "default"}


def filter_shas():
    """Full sha256 of every contract filter (sos and h_aa float64 bytes), as the manifest records them."""
    out = {"env_sos": env_sos()[1], "eeg_sos": eeg_sos()[1], "lp20_sos": lp20_sos()[1]}
    for fs_in in sorted(AA_TAPS):
        out[f"aa_fir_{fs_in}"] = _sha(aa_fir(fs_in, Fraction(FS, fs_in).numerator))
    return out


def band(x, sos, axis=-1, padlen=None):
    """Zero-phase sosfiltfilt(sos, x, padtype='odd') over the whole stream along `axis`; padlen = the filter's contract padlen
    (env 128, EEG 256, LP20 the scipy default) capped at T - 1, unless given."""
    x = np.asarray(x, dtype=np.float64)
    if padlen is None:
        padlen = _contract_padlen().get(_sha(sos))
        if padlen is None:
            raise ValueError("band: not a contract filter; pass padlen explicitly")
    kw = {} if padlen == "default" else {"padlen": min(int(padlen), x.shape[axis] - 1)}
    return signal.sosfiltfilt(sos, x, axis=axis, padtype="odd", **kw)


def rms_norm(e, axis=-1, return_rms=False):
    """env_n = e / RMS(e over the whole stream) along `axis` (stimulus-only, §2.3); RMS = sqrt(mean e^2), about 0, not the SD."""
    e = np.asarray(e, dtype=np.float64)
    r = np.sqrt(np.mean(np.square(e), axis=axis, keepdims=True))
    if not (np.isfinite(r).all() and (r > 0).all()):
        raise ValueError("rms_norm: zero or non-finite stream RMS")
    out = e / r
    if not return_rms:
        return out
    r = np.squeeze(r, axis=axis)
    return out, (float(r) if r.ndim == 0 else r)


# ---------------------------------------------------------------------------------------------------------- private 64 Hz input
def private_to64(x):
    """Private epochs [..., 200] at 250 Hz (onset at index 50) -> [..., 90] at 64 Hz: reflect-pad 75 samples at both ends (onset ->
    input 125 -> output ONSET64 = 32), 32/125 with h_aa, then the 20 Hz Butterworth low-pass (sosfiltfilt, padtype 'odd')."""
    x = np.asarray(x, dtype=np.float64)
    if x.shape[-1] != PRIVATE_EPOCH:
        raise ValueError(f"private_to64: {PRIVATE_EPOCH} samples at 250 Hz expected, got {x.shape}")
    xp = np.pad(x, [(0, 0)] * (x.ndim - 1) + [(PRIVATE_PAD, PRIVATE_PAD)], mode="reflect")
    y = band(resample64(xp, FS_PRIVATE), lp20_sos()[0])
    assert y.shape[-1] == PRIVATE_N64, y.shape
    return y.astype(np.float32)


def z64_per_child(x64):
    """One child's 64 Hz epochs [n, C, 90] z-scored per channel over all of its [32, 70) windows (population SD; SD 0 -> 1)."""
    x = np.asarray(x64, dtype=np.float64)
    w = x[..., PRIVATE_WIN[0]:PRIVATE_WIN[1]]
    ax = tuple(i for i in range(x.ndim) if i != x.ndim - 2)
    mu, sd = w.mean(axis=ax, keepdims=True), w.std(axis=ax, keepdims=True)
    sd[sd == 0] = 1
    return ((x - mu) / sd).astype(np.float32)


# ---------------------------------------------------------------------------------------------------------- keys
def pack_key(family, presentation, s):
    """key = (family << 40) | (presentation << 24) | s as int64; asserts 0 <= family < 2^23, presentation < 2^16, s < 2^24."""
    out = []
    for name, v, bits in (("family", family, FAMILY_BITS), ("presentation", presentation, PRES_BITS), ("s", s, S_BITS)):
        a = np.asarray(v)
        if a.size == 0:
            a = a.astype(np.int64)
        if a.dtype.kind not in "iu":
            raise TypeError(f"pack_key: integer {name} expected, got {a.dtype}")
        if a.size and (a.min() < 0 or a.max() >= 1 << bits):
            raise AssertionError(f"pack_key: {name} outside the {bits}-bit budget [0, 2**{bits})")
        out.append(a.astype(np.int64))
    f, p, t = out
    return (f << FAMILY_SHIFT) | (p << PRES_SHIFT) | t


def unpack_key(key):
    """Inverse of pack_key -> (family, presentation, s). Keys are 64-bit integers (numpy or torch.int64) and >= 0."""
    if hasattr(key, "device") and not isinstance(key, (np.ndarray, np.generic)):   # torch tensor (numpy 2 arrays also have .device)
        if str(key.dtype) != "torch.int64":
            raise TypeError(f"unpack_key: torch.int64 keys expected, got {key.dtype}")
        if key.numel() and not bool((key >= 0).all()):
            raise AssertionError("unpack_key: negative key")
        k = key
    else:
        k = np.asarray(key)
        if k.dtype.kind not in "iu" or k.dtype.itemsize != 8:
            raise TypeError(f"unpack_key: 64-bit integer keys expected, got {k.dtype}")
        k = k.astype(np.int64)
        if k.size and k.min() < 0:
            raise AssertionError("unpack_key: negative key")
    return k >> FAMILY_SHIFT, (k >> PRES_SHIFT) & PRES_MASK, k & S_MASK
