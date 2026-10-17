"""Read-only: are DTU NH-original and HI-'woa' waveforms of one content group the same audio at the same time?
Uses the cached 128 Hz Hilbert envelopes (audio_local.h5 'env'); no EEG."""
import json, collections
import numpy as np, h5py
F = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
inv = json.load(open(f"{F}/inventory.json")); cg = json.load(open(f"{F}/kcs_targets_v1/content_groups.json"))["content"]
hi_of = {}
for r in inv:
    if r["kind"] == "target": hi_of[r["sha"]] = r["hi"]
by = collections.defaultdict(lambda: {True: set(), False: set()})
for h, v in cg.items(): by[v["group"]][hi_of[h]].add(h)
out = []
with h5py.File(f"{F}/kcs_targets_v1/audio_local.h5", "r") as A:
    for g in sorted(by)[:12]:
        nh, hi = sorted(by[g][False]), sorted(by[g][True])
        if not nh or not hi: continue
        a = A[f"{nh[0]}/env"][()].astype(np.float64); best = None
        for hh in hi:
            b = A[f"{hh}/env"][()].astype(np.float64); n = min(len(a), len(b))
            x, y = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
            r0 = float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
            L = 1 << int(np.ceil(np.log2(2 * n)))
            c = np.fft.irfft(np.fft.rfft(x, L) * np.conj(np.fft.rfft(y, L)), L) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12)
            k = int(np.argmax(c)); lag = k if k < L // 2 else k - L
            cand = (r0, float(c[k]), lag / 128, len(a) / 128, len(b) / 128)
            if best is None or cand[1] > best[1]: best = cand
        out.append({"group": g, "n_nh_sha": len(nh), "n_hi_sha": len(hi), "best_zero_lag_r": round(best[0], 3), "best_max_r": round(best[1], 3),
                    "lag_s": round(best[2], 3), "len_nh_s": round(best[3], 1), "len_hi_s": round(best[4], 1)})
# within one hearing group: do several shas of one group share timing (excerpt variants)?
print(json.dumps(out, indent=0))
