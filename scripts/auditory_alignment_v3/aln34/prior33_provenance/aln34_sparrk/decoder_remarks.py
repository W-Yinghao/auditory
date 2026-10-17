"""Read-only label/alignment check for runs named in the dataset remarks: sub-065 (all runs; 'order changed wrt automatic labeling
script') and sub-085 (run 02 restarted after a Biosemi error). Decoder as in decoder_sample.py, trained on up to 8 other listeners."""
import json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives"
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json")))
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
def scan(rec, e, L=640):
    n = len(e); cc = []
    for tau in range(-L, L + 1):
        a, b = max(0, -tau), min(n, n - tau); cc.append(float(np.corrcoef(rec[a:b], e[a + tau:b + tau])[0, 1]))
    cc = np.array(cc); taus = np.arange(-L, L + 1); k = int(cc.argmax())
    return int(taus[k]), round(float(cc[k]), 4), round(float(cc[L]), 4), round(float(np.abs(cc[np.abs(taus) > 64]).max()), 4)
by = {}
for r in RT["runs"]: by.setdefault(r["stim"], []).append(r)
targets = [r for r in RT["runs"] if r["sub"] == "065"] + [r for r in RT["runs"] if r["sub"] == "085" and r["run"] == "02"]
for X in targets:
    refs = [r for r in by[X["stim"]] if r["sub"] not in RES | {X["sub"], "051", "011"}][:8]
    if len(refs) < 2: print(X["sub"], X["run"], X["stim"], "too few refs"); continue
    e = envl(X["stim"]); n = len(e); G = c = None
    for r in refs:
        Xd = design(eeg(r), n); G = Xd.T @ Xd if G is None else G + Xd.T @ Xd; c = Xd.T @ e if c is None else c + Xd.T @ e
    w = np.linalg.solve(G.astype(np.float64) + 1e-2 * np.trace(G) / G.shape[0] * np.eye(G.shape[0]), c.astype(np.float64)).astype(np.float32)
    print(f"sub-{X['sub']} run-{X['run']} {X['stim']:15s} refs={len(refs)} (tau, r_peak, r@0, null) =", scan(design(eeg(X), n) @ w, e), flush=True)
