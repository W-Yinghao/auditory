"""Within-SparrKULee content identity scan (read-only): 2-8 Hz band-limited envelopes (64 Hz -> 16 Hz for the scan), 20 s windows
every 30 s from each envelope, normalised cross-correlation against all OTHER envelopes. Reports pairs with r >= 0.7."""
import collections, glob, json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt, resample_poly
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content_scan.json")
names = sorted(os.path.basename(p)[:-13] for p in glob.glob(f"{D}/*_envelope.npy"))
sos = butter(4, [2, 8], btype="band", fs=64, output="sos")
FS = 16; W = 20 * FS; STEP = 30 * FS
env = {}
for k in names:
    x = np.load(f"{D}/{k}_envelope.npy", allow_pickle=False)[:, 0].astype(np.float64)
    env[k] = resample_poly(sosfiltfilt(sos, x), 1, 4)
parts, starts, owner, pos = [], [], [], 0
for k in names:
    s = env[k]; starts.append(pos); owner.append(k); parts += [s, np.zeros(W)]; pos += len(s) + W
b = np.concatenate(parts); N = len(b); n = 1 << int(np.ceil(np.log2(N + W)))
Fb = np.fft.rfft(b, n); c1 = np.r_[0, np.cumsum(b)]; c2 = np.r_[0, np.cumsum(b * b)]
S1 = c1[W:] - c1[:-W]; S2 = c2[W:] - c2[:-W]; var = S2 - S1 ** 2 / W
starts = np.array(starts); lens = np.array([len(env[k]) for k in names])
valid = np.zeros(len(var), bool)
for st, L in zip(starts, lens): valid[st: st + L - W + 1] = True
valid &= var > 1e-6 * np.median(var[valid])
res = collections.defaultdict(list)
for ia, k in enumerate(names):
    s = env[k]
    for st in range(0, len(s) - W + 1, STEP):
        a = s[st:st + W]; a = (a - a.mean()) / (a.std() + 1e-12)
        num = np.fft.irfft(Fb * np.conj(np.fft.rfft(a, n)), n)[: len(var)]
        r = np.where(valid, num / np.sqrt(W * np.maximum(var, 1e-12)), -np.inf)
        r[starts[ia]: starts[ia] + lens[ia]] = -np.inf  # exclude itself
        j = int(r.argmax()); t = int(np.searchsorted(starts, j, side="right") - 1)
        res[k].append((round(float(r[j]), 3), owner[t], round((j - starts[t]) / FS - st / FS, 2), st // FS))
summary = {}
for k, L in res.items():
    hits = [x for x in L if x[0] >= 0.7]
    summary[k] = {"windows": len(L), "max_r_other": max(x[0] for x in L), "n_hits_ge_0.7": len(hits),
                  "hit_targets": dict(collections.Counter(h[1] for h in hits)), "hit_offsets_s": sorted({h[2] for h in hits})[:10]}
allr = [x[0] for L in res.values() for x in L]
json.dump({"summary": summary, "q": np.quantile(allr, [0.5, 0.9, 0.99, 1]).tolist(), "n_windows": len(allr)}, open(OUT, "w"), indent=1)
print("windows", len(allr), "r quantiles 50/90/99/max", np.round(np.quantile(allr, [0.5, 0.9, 0.99, 1]), 3))
for k, v in summary.items():
    if v["n_hits_ge_0.7"]: print(k, v)
