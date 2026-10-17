"""Read-only alignment check with a backward (EEG -> envelope) ridge decoder trained on up to 8 OTHER listeners of the same stimulus
(1-8 Hz; 64 channels x lags 0,4,...,24 samples = 0-375 ms), applied to the target run; reports the shift tau in [-10, +10] s maximising
corr(reconstruction(t), env(t + tau)) and the peak sharpness. tau = 0 means EEG index 0 = envelope index 0."""
import json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives"
HERE = os.path.dirname(os.path.abspath(__file__))
RT = json.load(open(os.path.join(HERE, "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos")
LAGS = np.arange(0, 25, 4); RES = set("019 020 021 022 026".split())
def eeg(r):
    p = f"{D}/preprocessed_eeg/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    x = sosfiltfilt(sos, np.load(p, allow_pickle=False), axis=1)
    return ((x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-12)).astype(np.float32)
def envl(stim):
    e = sosfiltfilt(sos, np.load(f"{D}/preprocessed_stimuli/{stim}_envelope.npy", allow_pickle=False)[:, 0])
    return ((e - e.mean()) / e.std()).astype(np.float32)
def design(x, n):  # rows t = 0..n-1, features x[:, t + lag]
    T = x.shape[1]; Xd = np.zeros((n, x.shape[0] * len(LAGS)), np.float32)
    for j, L in enumerate(LAGS):
        m = min(n, T - L); Xd[:m, j * x.shape[0]:(j + 1) * x.shape[0]] = x[:, L:L + m].T
    return Xd
by = {}
for r in RT["runs"]: by.setdefault(r["stim"], []).append(r)
targets = [("026", "audiobook_1"), ("014", "audiobook_3"), ("014", "audiobook_4"), ("011", "audiobook_6_1"), ("051", "audiobook_12_2"),
           ("030", "audiobook_1"), ("002", "audiobook_3")]
out = {}
cache = {}
for sub, stim in targets:
    e = envl(stim); n = len(e)
    X = next(r for r in by[stim] if r["sub"] == sub)
    refs = [r for r in by[stim] if r["sub"] != sub and r["sub"] not in RES and (r["sub"], stim) not in targets][:8]
    key = (stim, tuple(r["sub"] for r in refs))
    if key not in cache:
        G = None; c = None
        for r in refs:
            Xd = design(eeg(r), n); G = Xd.T @ Xd if G is None else G + Xd.T @ Xd; c = Xd.T @ e if c is None else c + Xd.T @ e
        lam = 1e-2 * np.trace(G) / G.shape[0]
        cache[key] = np.linalg.solve(G.astype(np.float64) + lam * np.eye(G.shape[0]), c.astype(np.float64)).astype(np.float32)
    w = cache[key]
    rec = design(eeg(X), n) @ w
    L = 10 * 64; taus = np.arange(-L, L + 1); cc = []
    for tau in taus:  # corr(rec(t), e(t + tau)) over the overlap
        a, b = (rec[:n - tau], e[tau:]) if tau >= 0 else (rec[-tau:], e[:n + tau])
        cc.append(float(np.corrcoef(a, b)[0, 1]))
    cc = np.array(cc); k = int(cc.argmax()); off = np.abs(taus) > 64
    out[f"{sub}:{stim}"] = {"tau_samples": int(taus[k]), "r_peak": round(cc[k], 4), "r_at_0": round(cc[L], 4), "r_offpeak_absmax(|tau|>1s)": round(float(np.abs(cc[off]).max()), 4),
                           "n_refs": len(refs), "T_eeg": X["shape"][1], "T_env": n}
    print(sub, stim, out[f"{sub}:{stim}"], flush=True)
json.dump(out, open(os.path.join(HERE, "decoder_lag.json"), "w"), indent=1)
