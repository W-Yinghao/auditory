"""Read-only random-sample alignment audit (seed 20261016): 8 stimuli with >= 11 listeners in the non-restricted set; per stimulus a
backward ridge decoder (1-8 Hz, 64 ch x lags 0..24 step 4) is trained on 8 listeners and tested on 3 other listeners, scoring the whole
run and each half: tau in [-10, +10] s maximising corr(rec(t), env(t + tau)); null = max |r| over |tau| > 1 s."""
import json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives"
HERE = os.path.dirname(os.path.abspath(__file__))
RT = json.load(open(os.path.join(HERE, "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos"); LAGS = np.arange(0, 25, 4)
RES = set("019 020 021 022 026".split()); TESTED = {("026", "audiobook_1"), ("014", "audiobook_3"), ("014", "audiobook_4"), ("011", "audiobook_6_1"), ("051", "audiobook_12_2"), ("030", "audiobook_1"), ("002", "audiobook_3"), ("052", "audiobook_12_2")}
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
def scan(rec, e, a0, b0, L=640):
    n = len(e); cc = []
    for tau in range(-L, L + 1):
        a, b = max(a0, -tau), min(b0, n - tau); cc.append(float(np.corrcoef(rec[a:b], e[a + tau:b + tau])[0, 1]))
    cc = np.array(cc); taus = np.arange(-L, L + 1); k = int(cc.argmax())
    return int(taus[k]), float(cc[k]), float(cc[L]), float(np.abs(cc[np.abs(taus) > 64]).max())
rng = np.random.default_rng(20261016)
by = {}
for r in RT["runs"]:
    if r["sub"] not in RES and r["stim"] != "audiobook_1_artefact": by.setdefault(r["stim"], []).append(r)
stims = sorted(s for s, v in by.items() if len(v) >= 11)
pick = [stims[i] for i in rng.choice(len(stims), 8, replace=False)]
out = []
for stim in pick:
    rr = [r for r in by[stim] if (r["sub"], stim) not in TESTED]; idx = rng.permutation(len(rr)); refs = [rr[i] for i in idx[:8]]; tests = [rr[i] for i in idx[8:11]]
    e = envl(stim); n = len(e); G = c = None
    for r in refs:
        Xd = design(eeg(r), n); G = Xd.T @ Xd if G is None else G + Xd.T @ Xd; c = Xd.T @ e if c is None else c + Xd.T @ e
    w = np.linalg.solve(G.astype(np.float64) + 1e-2 * np.trace(G) / G.shape[0] * np.eye(G.shape[0]), c.astype(np.float64)).astype(np.float32)
    for r in tests:
        rec = design(eeg(r), n) @ w
        full = scan(rec, e, 0, n); h1 = scan(rec, e, 0, n // 2); h2 = scan(rec, e, n // 2, n)
        row = {"sub": r["sub"], "stim": stim, "diff": r["shape"][1] - n, "full": full, "half1": h1, "half2": h2}
        out.append(row)
        print(f"sub-{r['sub']} {stim:15s} full tau={full[0]:+4d} r={full[1]:.3f} null={full[3]:.3f} | h1 tau={h1[0]:+4d} r={h1[1]:.3f} null={h1[3]:.3f} | h2 tau={h2[0]:+4d} r={h2[1]:.3f} null={h2[3]:.3f}", flush=True)
json.dump(out, open(os.path.join(HERE, "decoder_sample.json"), "w"), indent=1)
ok = sum(1 for o in out if abs(o["full"][0]) <= 4 and o["full"][1] > o["full"][3])
print(f"aligned (|tau|<=4 samples and peak above off-peak max): {ok}/{len(out)}")
