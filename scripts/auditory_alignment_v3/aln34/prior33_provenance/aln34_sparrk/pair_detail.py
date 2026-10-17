"""Targeted read-only check of envelope pairs flagged by content_scan: sliding 5 s windows (2-8 Hz, 64 Hz) of A against B at the
best global lag; reports the matched span (r >= 0.9) in A and B coordinates."""
import numpy as np, sys
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
sos = butter(4, [2, 8], btype="band", fs=64, output="sos")
def env(k): return sosfiltfilt(sos, np.load(f"{D}/{k}_envelope.npy", allow_pickle=False)[:, 0].astype(np.float64))
def best_lag(a, b, max_lag):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)  # c[k] = sum a(t) b(t+k)
    lags = np.r_[np.arange(0, max_lag + 1), np.arange(-max_lag, 0)]
    return lags[int(np.argmax(c[lags % n]))]
pairs = [("audiobook_1", "audiobook_1_1"), ("audiobook_1", "audiobook_1_2"), ("audiobook_1", "audiobook_1_1_shifted"), ("audiobook_1", "audiobook_1_2_shifted"),
         ("audiobook_1", "audiobook_1_artefact"), ("audiobook_1_1", "audiobook_1_1_shifted"), ("audiobook_1_2", "audiobook_1_2_shifted"),
         ("audiobook_12_1", "audiobook_1"), ("audiobook_13_1", "audiobook_1"), ("audiobook_4", "audiobook_1_artefact"), ("audiobook_8_1", "audiobook_4"),
         ("audiobook_14_1", "audiobook_4"), ("audiobook_9_1", "audiobook_4"), ("audiobook_8_2", "audiobook_4"), ("audiobook_1", "audiobook_12_2")]
W = 5 * 64
for A, B in pairs:
    a, b = env(A), env(B)
    # local windows of A every 2.5 s; for each, best lag within +-1000 s in B by direct normalised correlation via FFT on B
    n = 1 << int(np.ceil(np.log2(len(b) + W)))
    Fb = np.fft.rfft(b, n); c1 = np.r_[0, np.cumsum(b)]; c2 = np.r_[0, np.cumsum(b * b)]
    S1 = c1[W:] - c1[:-W]; S2 = c2[W:] - c2[:-W]; var = np.maximum(S2 - S1 ** 2 / W, 1e-12)
    hits = []
    for st in range(0, len(a) - W + 1, W // 2):
        w = a[st:st + W]; w = (w - w.mean()) / (w.std() + 1e-12)
        num = np.fft.irfft(Fb * np.conj(np.fft.rfft(w, n)), n)[: len(var)]
        r = num / np.sqrt(W * var); j = int(np.argmax(r))
        if r[j] >= 0.9: hits.append((st, j, r[j]))
    if not hits:
        print(f"{A:22s} vs {B:22s}: no 5-s window r>=0.9"); continue
    offs = np.array([j - st for st, j, _ in hits]); vals, cnt = np.unique(offs, return_counts=True)
    top = vals[np.argsort(-cnt)][:3]
    for o in top:
        h = [(st, j, r) for st, j, r in hits if j - st == o]
        print(f"{A:22s} vs {B:22s}: offset B-A {o:+7d} samples ({o/64:+8.3f} s), {len(h):4d} windows r>=0.9 (median r {np.median([x[2] for x in h]):.3f}); A span [{h[0][0]/64:.1f}, {(h[-1][0]+W)/64:.1f}] s of {len(a)/64:.1f} s; B span [{h[0][1]/64:.1f}, {(h[-1][1]+W)/64:.1f}] s of {len(b)/64:.1f} s")
