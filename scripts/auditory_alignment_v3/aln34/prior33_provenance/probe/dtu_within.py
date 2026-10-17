"""Read-only: alignment of the several waveforms (sha) inside one DTU content group, NH only and HI only (128 Hz envelopes)."""
import json, collections
import numpy as np, h5py
F = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
inv = json.load(open(f"{F}/inventory.json")); cg = json.load(open(f"{F}/kcs_targets_v1/content_groups.json"))["content"]
hi_of = {r["sha"]: r["hi"] for r in inv if r["kind"] == "target"}
lis = collections.defaultdict(set)
for r in inv:
    if r["kind"] == "target": lis[r["sha"]].add(r["file"])
by = collections.defaultdict(lambda: {True: [], False: []})
for h, v in cg.items(): by[v["group"]][hi_of[h]].append(h)
def xc(a, b):
    n = min(len(a), len(b)); x = a - a.mean(); y = b - b.mean(); L = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(x, L) * np.conj(np.fft.rfft(y, L)), L)
    # normalise by overlap-independent norms
    c = c / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12)
    k = int(np.argmax(c)); return float(c[k]), (k if k < L // 2 else k - L) / 128
lags = collections.Counter(); rs = []
with h5py.File(f"{F}/kcs_targets_v1/audio_local.h5", "r") as A:
    for g in sorted(by):
        for hi in (False, True):
            hs = sorted(by[g][hi])
            if len(hs) < 2: continue
            E = {h: A[f"{h}/env"][()].astype(np.float64) for h in hs}
            for j in range(1, len(hs)):
                r, lag = xc(E[hs[0]], E[hs[j]]); rs.append(r); lags[round(lag, 1)] += 1
print("pairs", len(rs), "max-r quantiles", np.round(np.quantile(rs, [0, .1, .5, .9, 1]), 3).tolist())
print("best-lag histogram (s):", sorted(lags.items(), key=lambda kv: -kv[1])[:15])
print("listeners per sha (NH):", np.percentile([len(lis[h]) for h in hi_of if not hi_of[h]], [0, 50, 100]).tolist(),
      "(HI):", np.percentile([len(lis[h]) for h in hi_of if hi_of[h]], [0, 50, 100]).tolist())
