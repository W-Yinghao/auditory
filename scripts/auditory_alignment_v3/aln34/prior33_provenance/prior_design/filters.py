"""Read-only synthetic checks of the proposed contract constants (no data read)."""
import hashlib, sys
import numpy as np
from scipy import signal
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
# 1. anti-alias FIR per ratio: Kaiser, 60 dB, passband 22 Hz, stopband 30 Hz, cutoff 26 Hz, designed at fs_in*up
for name, fs_in, up, down in (("fau/dtu 128->64", 128, 1, 2), ("federici 100->64", 100, 16, 25), ("private 250->64", 250, 32, 125)):
    fs_up = fs_in * up
    n, beta = signal.kaiserord(60.0, 8.0 / (fs_up / 2))
    n += (n + 1) % 2  # odd length (type I, integer delay)
    h = signal.firwin(n, 26.0, fs=fs_up, window=("kaiser", beta))
    w, H = signal.freqz(h, worN=1 << 16, fs=fs_up)
    db = 20 * np.log10(np.maximum(np.abs(H), 1e-12))
    pb = np.abs(db[w <= 22]).max(); sb = db[w >= 30].max()
    t = np.arange(int(20 * fs_in)) / fs_in
    out = {}
    for f in (10.0, 20.0, 34.0, 40.0):
        y = signal.resample_poly(np.sin(2 * np.pi * f * t), up, down, window=h)
        out[f] = float(np.sqrt(2) * y[len(y) // 4: 3 * len(y) // 4].std())
    print(f"{name}: taps {n} beta {beta:.3f} half-support {(n - 1) / 2 / fs_up * 1000:.0f} ms | max passband dev {pb:.4f} dB, stopband max {sb:.1f} dB |"
          f" sine gains {', '.join(f'{k:g} Hz {v:.4f}' for k, v in out.items())} | sha256 {hashlib.sha256(h.astype(np.float64).tobytes()).hexdigest()[:16]}")
# sample-0 alignment, 128->64 and 100->64: a band-limited pulse at input index m -> peak at the matching output index
for fs_in, up, down, m in ((128, 1, 2, 640), (100, 16, 25, 625)):
    n, beta = signal.kaiserord(60.0, 8.0 / (fs_in * up / 2)); n += (n + 1) % 2
    h = signal.firwin(n, 26.0, fs=fs_in * up, window=("kaiser", beta))
    x = np.zeros(2000); x[m] = 1.0
    x = signal.sosfiltfilt(signal.butter(4, 8, fs=fs_in, output="sos"), x)
    y = signal.resample_poly(x, up, down, window=h)
    print(f"  pulse at input {m} ({m / fs_in:.4f} s) -> output peak {int(np.argmax(y))} ({np.argmax(y) / 64:.4f} s)")
# private onset: epoch [-200, 600) ms at 250 Hz, onset index 50; reflect-pad 75 both sides -> output index 32 = onset
n, beta = signal.kaiserord(60.0, 8.0 / (8000 / 2)); n += (n + 1) % 2
h = signal.firwin(n, 26.0, fs=8000, window=("kaiser", beta))
tt = (np.arange(200) - 50) / 250.0
x = np.cos(2 * np.pi * 3.0 * tt)  # 3 Hz cosine peaking exactly at the onset
xp = np.pad(x, 75, mode="reflect")
y = signal.resample_poly(xp, 32, 125, window=h)
k = np.arange(len(y)); tk = (k - 32) / 64.0
err = np.abs(y - np.cos(2 * np.pi * 3.0 * tk))
print(f"private: padded len {len(xp)} -> out len {len(y)}; out[32] = {y[32]:.4f} (onset); max |err| in window [32,70) {err[32:70].max():.4f};"
      f" in [32,56) {err[32:56].max():.4f}; last window sample t = {(69 - 32) / 64 * 1000:.2f} ms")
# 2. envelope band-pass: Butterworth order 4, 2-8 Hz, 64 Hz, sosfiltfilt; zero-phase impulse response energy within +-41 samples
sos = signal.butter(4, [2.0, 8.0], btype="band", fs=64, output="sos")
x = np.zeros(4097); x[2048] = 1.0
ir = signal.sosfiltfilt(sos, x)
e = ir ** 2; c = 2048
frac = lambda m: e[c - m: c + m + 1].sum() / e.sum()
print(f"envelope sos sha256 {hashlib.sha256(sos.astype(np.float64).tobytes()).hexdigest()[:16]} sections {len(sos)} | energy within +-20 {frac(20):.5f} +-41 {frac(41):.6f} +-64 {frac(64):.6f}")
w, H = signal.sosfreqz(sos, worN=4096, fs=64); g = np.abs(H) ** 2  # filtfilt = |H|^2
for f in (1.0, 2.0, 4.0, 8.0, 10.0, 16.0):
    print(f"   |H|^2 at {f:g} Hz: {10 * np.log10(g[np.argmin(np.abs(w - f))]):.1f} dB")
# 3. ticks
i = lambda k: (64 * k + 25) // 50
ks = np.arange(2_000_000)
assert np.array_equal((64 * ks + 25) // 50, np.round(1.28 * ks).astype(np.int64)), "tick formula differs from np.round"
frac_part = (1.28 * ks) % 1
assert not np.any(np.isclose(frac_part, 0.5)), "rounding ties exist"
offs = np.array([i(j) for j in range(250)])
print("ticks: first 16", offs[:16].tolist(), "| i_249", offs[-1], "| steps", np.bincount(np.diff(offs)).tolist(), "| max |t_act - t_req| ms", float(np.abs(offs / 64 - 0.02 * np.arange(250)).max() * 1000))
# 4. projection
from auditory_alignment_v2.audio_targets import semi_orthogonal
P = semi_orthogonal(32, 8, 20261016).numpy()
print("P", P.shape, "max|P^T P - I|", float(np.abs(P.T @ P - np.eye(8)).max()), "rank", np.linalg.matrix_rank(P), "sha256(float32)", hashlib.sha256(P.astype(np.float32).tobytes()).hexdigest()[:16])
