"""Gate 3 side check: what are the two channels of a DTU target/masker wav (RMS ratio, max |xcorr| within +-2 ms)?"""
import sys, numpy as np, soundfile as sf
for p in sys.argv[1:]:
    x, sr = sf.read(p, dtype='float64', always_2d=True)
    a, b = x[:, 0] - x[:, 0].mean(), x[:, 1] - x[:, 1].mean()
    n = len(a); best = (0, 0.0)
    for L in range(-int(0.002 * sr), int(0.002 * sr) + 1):
        r = np.dot(a[max(0, L):n + min(0, L)], b[max(0, -L):n - max(0, L)]) / np.sqrt((a * a).sum() * (b * b).sum())
        if abs(r) > abs(best[1]): best = (L, r)
    print(p.split('audio_drcmr/')[1], 'sr', sr, 'rms L/R', round(float(np.sqrt((a*a).mean()/(b*b).mean())), 3), 'max xcorr within 2ms', round(best[1], 3), 'at lag ms', round(best[0] / sr * 1000, 3))
