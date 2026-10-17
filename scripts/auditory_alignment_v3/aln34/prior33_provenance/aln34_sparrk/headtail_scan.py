"""Read-only: first/last 60 s of every SparrKULee envelope (2-8 Hz at 64 Hz) in 10 s windows (5 s hop) against the first/last 60 s
of every OTHER envelope at any lag (bank = heads + tails only). Reports matched spans (r >= 0.9)."""
import collections, glob, json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "headtail_scan.json")
sos = butter(4, [2, 8], btype="band", fs=64, output="sos")
names = sorted(os.path.basename(p)[:-13] for p in glob.glob(f"{D}/*_envelope.npy"))
env = {k: sosfiltfilt(sos, np.load(f"{D}/{k}_envelope.npy", allow_pickle=False)[:, 0].astype(np.float64)) for k in names}
W = 10 * 64; H = 5 * 64; EDGE = 60 * 64
segs = []  # (name, part, start_in_env, array)
for k in names:
    s = env[k]; L = len(s)
    segs.append((k, "head", 0, s[:min(EDGE, L)]))
    if L > EDGE: segs.append((k, "tail", max(EDGE, L - EDGE), s[max(EDGE, L - EDGE):]))
parts, starts, pos = [], [], 0
for _, _, _, a in segs: starts.append(pos); parts += [a, np.zeros(W)]; pos += len(a) + W
b = np.concatenate(parts); n = 1 << int(np.ceil(np.log2(len(b) + W)))
Fb = np.fft.rfft(b, n); c1 = np.r_[0, np.cumsum(b)]; c2 = np.r_[0, np.cumsum(b * b)]
S1 = c1[W:] - c1[:-W]; S2 = c2[W:] - c2[:-W]; var = S2 - S1 ** 2 / W
starts = np.array(starts); lens = np.array([len(a) for *_, a in segs])
valid = np.zeros(len(var), bool)
for st, L in zip(starts, lens): valid[st: st + L - W + 1] = True
valid &= var > 1e-3 * np.median(var[valid])
own = collections.defaultdict(list)
for i, (k, *_ ) in enumerate(segs): own[k].append(i)
out = collections.defaultdict(list)
for i, (k, part, off0, a) in enumerate(segs):
    for st in range(0, len(a) - W + 1, H):
        w = a[st:st + W]; w = (w - w.mean()) / (w.std() + 1e-12)
        num = np.fft.irfft(Fb * np.conj(np.fft.rfft(w, n)), n)[: len(var)]
        r = np.where(valid, num / np.sqrt(W * np.maximum(var, 1e-12)), -np.inf)
        for jj in own[k]: r[starts[jj]: starts[jj] + lens[jj]] = -np.inf
        j = int(r.argmax())
        if r[j] >= 0.9:
            t = int(np.searchsorted(starts, j, side="right") - 1); ko, po, offo, _ = segs[t]
            out[k].append({"a_s": (off0 + st) / 64, "other": ko, "b_s": (offo + j - starts[t]) / 64, "r": round(float(r[j]), 3), "part": part})
summ = {}
for k, L in out.items():
    g = collections.defaultdict(list)
    for h in L: g[(h["other"], round(h["b_s"] - h["a_s"], 1), h["part"])].append(h)
    summ[k] = [{"other": o, "offset_s": off, "part": p, "a_span_s": [min(x["a_s"] for x in hs), max(x["a_s"] for x in hs) + W / 64], "n": len(hs),
                "median_r": float(np.median([x["r"] for x in hs]))} for (o, off, p), hs in sorted(g.items(), key=lambda z: -len(z[1]))]
json.dump(summ, open(OUT, "w"), indent=1)
for k in names:
    if k in summ:
        print(k, f"(len {len(env[k])/64:.1f} s):", "; ".join(f"{x['part']}:{x['other']} off {x['offset_s']:+.1f}s A[{x['a_span_s'][0]:.0f},{x['a_span_s'][1]:.0f}] n={x['n']} r={x['median_r']:.3f}" for x in summ[k][:5]))
print("no head/tail match:", [k for k in names if k not in summ])
