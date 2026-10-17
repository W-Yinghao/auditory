"""Decoder alignment test (as decoder_lag.py) scored on the first and second half of two structurally anomalous runs plus a control."""
import json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives"
HERE = os.path.dirname(os.path.abspath(__file__))
RT = json.load(open(os.path.join(HERE, "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos"); LAGS = np.arange(0, 25, 4); RES = set("019 020 021 022 026".split())
def eeg(r):
    p = f"{D}/preprocessed_eeg/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    x = sosfiltfilt(sos, np.load(p, allow_pickle=False), axis=1); return ((x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-12)).astype(np.float32)
def envl(stim):
    e = sosfiltfilt(sos, np.load(f"{D}/preprocessed_stimuli/{stim}_envelope.npy", allow_pickle=False)[:, 0]); return ((e - e.mean()) / e.std()).astype(np.float32)
def design(x, n):
    T = x.shape[1]; Xd = np.zeros((n, x.shape[0] * len(LAGS)), np.float32)
    for j, L in enumerate(LAGS):
        m = min(n, T - L); Xd[:m, j * x.shape[0]:(j + 1) * x.shape[0]] = x[:, L:L + m].T
    return Xd
by = {}
for r in RT["runs"]: by.setdefault(r["stim"], []).append(r)
for sub, stim in [("051", "audiobook_12_2"), ("011", "audiobook_6_1"), ("052", "audiobook_12_2")]:
    e = envl(stim); n = len(e); X = next(r for r in by[stim] if r["sub"] == sub)
    refs = [r for r in by[stim] if r["sub"] not in RES and r["sub"] not in (sub, "051", "011")][:8]
    G = c = None
    for r in refs:
        Xd = design(eeg(r), n); G = Xd.T @ Xd if G is None else G + Xd.T @ Xd; c = Xd.T @ e if c is None else c + Xd.T @ e
    w = np.linalg.solve(G.astype(np.float64) + 1e-2 * np.trace(G) / G.shape[0] * np.eye(G.shape[0]), c.astype(np.float64)).astype(np.float32)
    rec = design(eeg(X), n) @ w; L = 10 * 64
    for name, (a0, b0) in {"first_half": (0, n // 2), "second_half": (n // 2, n), "first_380s": (0, 380 * 64)}.items():
        cc = []
        for tau in range(-L, L + 1):
            a, b = max(a0, -tau), min(b0, n - tau)
            cc.append(float(np.corrcoef(rec[a:b], e[a + tau:b + tau])[0, 1]))
        cc = np.array(cc); k = int(cc.argmax()); taus = np.arange(-L, L + 1)
        print(f"sub-{sub} {stim} {name:12s} [{a0/64:.0f},{b0/64:.0f}] s: tau={taus[k]:+5d} r_peak={cc[k]:.4f} r@0={cc[L]:.4f} null(|tau|>1s)={np.abs(cc[np.abs(taus) > 64]).max():.4f} refs={len(refs)}", flush=True)
