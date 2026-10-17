"""Read-only cross-listener alignment check (no envelope model): for a target run X of stimulus s, the lag tau in [-5, +5] s that
maximises the channel-summed correlation between X (1-8 Hz, per-channel z) and the mean of up to 8 OTHER listeners of s, computed on
three segments (first 180 s, middle 180 s, last 180 s of the envelope span). Expect tau = 0 if both runs start at envelope index 0."""
import glob, json, os, re, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
ENV = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_stimuli"
RT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos")
RES = "019 020 021 022 026".split()
def load(r):
    p = f"{D}/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    x = sosfiltfilt(sos, np.load(p, allow_pickle=False), axis=1)
    return (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-12)
def lagscan(x, T, a, b, L=5 * 64):
    # c(tau) = sum_ch sum_t x(t + tau) T(t) / n over t in [a, b)
    seg = T[:, a:b]; n = b - a; out = []
    for tau in range(-L, L + 1):
        if a + tau < 0 or b + tau > x.shape[1]: out.append(np.nan); continue
        out.append(float((x[:, a + tau:b + tau] * seg).sum() / n / x.shape[0]))
    c = np.array(out); k = int(np.nanargmax(c)); null = np.nanmedian(np.abs(c))
    return k - L, c[k], c[L], null
targets = [("026", "audiobook_1"), ("014", "audiobook_3"), ("014", "audiobook_4"), ("011", "audiobook_6_1"), ("051", "audiobook_12_2"),
           ("001", "audiobook_5_1"), ("054", "podcast_21")]
controls = [("030", "audiobook_1"), ("002", "audiobook_3"), ("052", "audiobook_12_2")]
runs = RT["runs"]
by = {}
for r in runs: by.setdefault(r["stim"], []).append(r)
res = {}
for sub, stim in targets + controls:
    X = next(r for r in by[stim] if r["sub"] == sub)
    refs = [r for r in by[stim] if r["sub"] != sub and r["sub"] not in RES and r["shape"][1] - r["env_len"] == max(set(q["shape"][1] - q["env_len"] for q in by[stim]), key=[q["shape"][1] - q["env_len"] for q in by[stim]].count)][:8]
    x = load(X); Tm = None
    for r in refs:
        y = load(r); m = min(y.shape[1], x.shape[1])
        Tm = y[:, :m] if Tm is None else Tm[:, :min(m, Tm.shape[1])] + y[:, :min(m, Tm.shape[1])]
    Tm = Tm / len(refs); Te = X["env_len"]; S = 180 * 64
    segs = {"first": (5 * 64 + 1, 5 * 64 + 1 + S), "middle": (Te // 2 - S // 2, Te // 2 + S // 2), "last": (Te - S - 5 * 64 - 1, Te - 5 * 64 - 1)}
    out = {}
    for name, (a, b) in segs.items():
        b = min(b, Tm.shape[1] - 5 * 64 - 1)
        tau, cpk, c0, null = lagscan(x, Tm, a, b)
        out[name] = {"tau_samples": tau, "peak": round(cpk, 4), "at_zero": round(c0, 4), "null_med_abs": round(null, 4), "seg_s": [round(a / 64, 1), round(b / 64, 1)]}
    res[f"{sub}:{stim}"] = {"T_eeg": X["shape"][1], "T_env": Te, "diff": X["shape"][1] - Te, "n_refs": len(refs), "segments": out}
    print(f"sub-{sub} {stim:15s} diff={X['shape'][1]-Te:4d} refs={len(refs)} " + " | ".join(f"{k}: tau={v['tau_samples']:+d} pk={v['peak']:.3f} @0={v['at_zero']:.3f} null={v['null_med_abs']:.3f}" for k, v in out.items()), flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "isc_lag.json"), "w"), indent=1)
